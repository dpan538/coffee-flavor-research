#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DB_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
MIGRATION_PLAN="$SCRIPT_DIR/migration-plan.sh"

ALLOW_DROP=${COFFEE_KB_ALLOW_DATABASE_DROP:-}
ADMIN_DATABASE=${PGDATABASE:-postgres}
DATABASE_ONE=${COFFEE_KB_REBUILD_DB_ONE:-coffee_sensory_kb_v0_rebuild_one}
DATABASE_TWO=${COFFEE_KB_REBUILD_DB_TWO:-coffee_sensory_kb_v0_rebuild_two}
PG_DUMP_CONTAINER=${COFFEE_KB_PG_DUMP_CONTAINER:-}

if [[ "$ALLOW_DROP" != 1 ]]; then
  printf 'ERROR: this script creates and drops databases. Set COFFEE_KB_ALLOW_DATABASE_DROP=1 to continue.\n' >&2
  exit 77
fi

validate_disposable_database_name() {
  local database_name=$1

  if [[ ! "$database_name" =~ ^coffee_sensory_kb_v0_[a-z0-9_]+$ ]]; then
    printf 'ERROR: unsafe disposable database name: %s\n' "$database_name" >&2
    printf 'Names must match ^coffee_sensory_kb_v0_[a-z0-9_]+$.\n' >&2
    exit 64
  fi

  if (( ${#database_name} > 63 )); then
    printf 'ERROR: database name exceeds PostgreSQL\047s 63-byte identifier limit: %s\n' "$database_name" >&2
    exit 64
  fi
}

validate_disposable_database_name "$DATABASE_ONE"
validate_disposable_database_name "$DATABASE_TWO"

if [[ "$DATABASE_ONE" == "$DATABASE_TWO" ]]; then
  printf 'ERROR: the two disposable database names must be distinct.\n' >&2
  exit 64
fi

if [[ "$DATABASE_ONE" == "$ADMIN_DATABASE" || "$DATABASE_TWO" == "$ADMIN_DATABASE" ]]; then
  printf 'ERROR: a disposable database name must not equal the admin database.\n' >&2
  exit 64
fi

required_commands=(psql createdb dropdb find sort sed awk cmp mktemp python3)
if [[ -n "$PG_DUMP_CONTAINER" ]]; then
  required_commands+=(docker)
else
  required_commands+=(pg_dump)
fi
for required_command in "${required_commands[@]}"; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'ERROR: required command is unavailable: %s\n' "$required_command" >&2
    exit 69
  fi
done

if [[ ! -x "$MIGRATION_PLAN" ]]; then
  printf 'ERROR: migration plan helper is missing or not executable: %s\n' \
    "$MIGRATION_PLAN" >&2
  exit 66
fi

"$MIGRATION_PLAN" verify
DISCOVERED_MIGRATION_COUNT=$("$MIGRATION_PLAN" count)

if command -v sha256sum >/dev/null 2>&1; then
  SHA256_COMMAND=sha256sum
elif command -v shasum >/dev/null 2>&1; then
  SHA256_COMMAND=shasum
else
  printf 'ERROR: sha256sum or shasum is required.\n' >&2
  exit 69
fi

sha256_file() {
  local file_path=$1

  if [[ "$SHA256_COMMAND" == sha256sum ]]; then
    sha256sum "$file_path" | awk '{print $1}'
  else
    shasum -a 256 "$file_path" | awk '{print $1}'
  fi
}

psql_admin() {
  psql -X --set=ON_ERROR_STOP=1 --dbname="$ADMIN_DATABASE" "$@"
}

psql_target() {
  local database_name=$1
  shift
  psql -X --set=ON_ERROR_STOP=1 --dbname="$database_name" "$@"
}

database_exists() {
  local database_name=$1
  local exists

  exists=$(psql_admin \
    --tuples-only \
    --no-align \
    --command="SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$database_name');")
  [[ "$exists" == t ]]
}

server_version_num=$(psql_admin --tuples-only --no-align --command='SHOW server_version_num;')
server_version=$(psql_admin --tuples-only --no-align --command='SHOW server_version;')
admin_database_name=$(psql_admin --tuples-only --no-align --command='SELECT current_database();')
if [[ ! "$server_version_num" =~ ^[0-9]+$ ]] || (( server_version_num < 170000 )); then
  printf 'ERROR: PostgreSQL 17 or newer is required; admin server reports %s.\n' "$server_version" >&2
  exit 65
fi

if [[ "$DATABASE_ONE" == "$admin_database_name" || "$DATABASE_TWO" == "$admin_database_name" ]]; then
  printf 'ERROR: a disposable database name must not equal the connected admin database.\n' >&2
  exit 64
fi

if database_exists "$DATABASE_ONE"; then
  printf 'ERROR: refusing to overwrite existing database %s. Choose another disposable name.\n' "$DATABASE_ONE" >&2
  exit 73
fi
if database_exists "$DATABASE_TWO"; then
  printf 'ERROR: refusing to overwrite existing database %s. Choose another disposable name.\n' "$DATABASE_TWO" >&2
  exit 73
fi

ARTIFACT_DIR=$(mktemp -d "${TMPDIR:-/tmp}/coffee-sensory-kb-v0-rebuild.XXXXXX")
DATABASE_ONE_CREATED=false
DATABASE_TWO_CREATED=false

cleanup() {
  local original_status=$?
  local cleanup_status=0

  trap - EXIT INT TERM
  set +e

  if [[ "$DATABASE_TWO_CREATED" == true ]]; then
    dropdb --if-exists --maintenance-db="$ADMIN_DATABASE" "$DATABASE_TWO"
    if (( $? != 0 )); then
      printf 'ERROR: cleanup could not drop %s.\n' "$DATABASE_TWO" >&2
      cleanup_status=1
    fi
  fi

  if [[ "$DATABASE_ONE_CREATED" == true ]]; then
    dropdb --if-exists --maintenance-db="$ADMIN_DATABASE" "$DATABASE_ONE"
    if (( $? != 0 )); then
      printf 'ERROR: cleanup could not drop %s.\n' "$DATABASE_ONE" >&2
      cleanup_status=1
    fi
  fi

  printf 'ARTIFACT_DIR=%s\n' "$ARTIFACT_DIR"

  if (( original_status != 0 )); then
    exit "$original_status"
  fi
  exit "$cleanup_status"
}

trap cleanup EXIT
trap 'exit 130' INT TERM

write_migration_manifest() {
  local output_file=$1
  "$MIGRATION_PLAN" hashes >"$output_file"
}

write_seed_manifest() {
  local output_file=$1
  local seed_file

  : >"$output_file"
  while IFS= read -r seed_file; do
    printf '%s  %s\n' \
      "$(sha256_file "$seed_file")" \
      "$(basename -- "$seed_file")" >>"$output_file"
  done < <(
    find "$DB_DIR" \
      -maxdepth 1 \
      -type f \
      -name '[0-9][0-9][0-9]_*seed*.sql' \
      -print |
      LC_ALL=C sort
  )

  if [[ ! -s "$output_file" ]]; then
    printf 'ERROR: no deterministic seed migrations were discovered.\n' >&2
    return 1
  fi
}

write_stable_key_inventory() {
  local database_name=$1
  local output_file=$2
  local inventory_sql
  local inventory_query_file

  # Negative tests may consume identity sequence values even when their
  # transactions roll back. Compare only stable logical candidate values.
  inventory_sql=$(psql_target "$database_name" --tuples-only --no-align <<'SQL'
SELECT
  'SELECT * FROM (' ||
  string_agg(
    format(
      'SELECT %L::text AS table_name, %L::text AS column_name, %I::text AS key_value FROM %I.%I WHERE %I IS NOT NULL',
      c.table_schema || '.' || c.table_name,
      c.column_name,
      c.column_name,
      c.table_schema,
      c.table_name,
      c.column_name
    ),
    ' UNION ALL ' ORDER BY c.table_schema, c.table_name, c.ordinal_position
  ) ||
  ') AS stable_keys ORDER BY table_name, column_name, key_value;'
FROM information_schema.columns AS c
JOIN information_schema.tables AS t
  ON t.table_schema = c.table_schema
 AND t.table_name = c.table_name
WHERE t.table_type = 'BASE TABLE'
  AND c.table_schema IN (
    'ref', 'kb', 'evidence', 'corpus', 'context', 'calibration', 'ml',
    'audit', 'competition'
  )
  AND (
    c.column_name LIKE '%\_key' ESCAPE '\'
    OR c.column_name LIKE '%\_code' ESCAPE '\'
  );
SQL
)

  if [[ -z "$inventory_sql" ]]; then
    : >"$output_file"
    return
  fi

  # Passing the generated UNION as --command eventually exceeds the platform
  # argument-size limit as governed schemas add stable key columns. Keep the
  # same deterministic query, but let psql read it from an artifact file.
  # macOS mktemp only substitutes a trailing XXXXXX run; a suffix after it
  # creates the same literal filename on each build and breaks rebuild two.
  inventory_query_file=$(mktemp "$ARTIFACT_DIR/stable-key-query.XXXXXX")
  printf '%s\n' "$inventory_sql" >"$inventory_query_file"
  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --file="$inventory_query_file" >"$output_file"
}

write_reference_row_counts() {
  local database_name=$1
  local output_file=$2
  local count_sql

  count_sql=$(psql_target "$database_name" --tuples-only --no-align <<'SQL'
SELECT
  'SELECT * FROM (' ||
  string_agg(
    format(
      'SELECT %L::text AS table_name, count(*)::bigint AS row_count FROM %I.%I',
      t.table_schema || '.' || t.table_name,
      t.table_schema,
      t.table_name
    ),
    ' UNION ALL ' ORDER BY t.table_name
  ) ||
  ') AS reference_counts ORDER BY table_name;'
FROM information_schema.tables AS t
WHERE t.table_schema = 'ref'
  AND t.table_type = 'BASE TABLE';
SQL
)

  if [[ -z "$count_sql" ]]; then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="$count_sql" >"$output_file"
}

write_source_version_inventory() {
  local database_name=$1
  local output_file=$2

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command='SELECT s.source_key, sv.source_version_key, lp.license_policy_key
               FROM evidence.source_version AS sv
               JOIN evidence.source AS s ON s.source_id = sv.source_id
               JOIN evidence.license_policy AS lp ON lp.license_policy_id = sv.license_policy_id
               ORDER BY s.source_key, sv.source_version_key, lp.license_policy_key;' >"$output_file"
}

write_validation_results() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT > 48 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 UNION ALL
                 SELECT 'round3d', check_key, violation_count, passed
                 FROM audit.run_round3d_validation_queries()
                 UNION ALL
                 SELECT 'round3e', check_key, violation_count, passed
                 FROM audit.run_round3e_validation_queries()
                 UNION ALL
                 SELECT 'round3f', check_key, violation_count, passed
                 FROM audit.run_round3f_validation_queries()
                 UNION ALL
                 SELECT 'round3g', check_key, violation_count, passed
                 FROM audit.run_round3g_validation_queries()
                 UNION ALL
                 SELECT 'round3i', freeze_gate_key,
                        CASE WHEN passed THEN 0 ELSE 1 END::BIGINT, passed
                 FROM audit.run_research_database_freeze_gate()
                 WHERE severity = 'HARD'
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 41 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 UNION ALL
                 SELECT 'round3d', check_key, violation_count, passed
                 FROM audit.run_round3d_validation_queries()
                 UNION ALL
                 SELECT 'round3e', check_key, violation_count, passed
                 FROM audit.run_round3e_validation_queries()
                 UNION ALL
                 SELECT 'round3f', check_key, violation_count, passed
                 FROM audit.run_round3f_validation_queries()
                 UNION ALL
                 SELECT 'round3g', check_key, violation_count, passed
                 FROM audit.run_round3g_validation_queries()
                 UNION ALL
                 SELECT 'round3h', check_key, violation_count, passed
                 FROM audit.run_round3h_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 38 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 UNION ALL
                 SELECT 'round3d', check_key, violation_count, passed
                 FROM audit.run_round3d_validation_queries()
                 UNION ALL
                 SELECT 'round3e', check_key, violation_count, passed
                 FROM audit.run_round3e_validation_queries()
                 UNION ALL
                 SELECT 'round3f', check_key, violation_count, passed
                 FROM audit.run_round3f_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 35 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 UNION ALL
                 SELECT 'round3d', check_key, violation_count, passed
                 FROM audit.run_round3d_validation_queries()
                 UNION ALL
                 SELECT 'round3e', check_key, violation_count, passed
                 FROM audit.run_round3e_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 32 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 UNION ALL
                 SELECT 'round3d', check_key, violation_count, passed
                 FROM audit.run_round3d_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 29 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 25 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 21 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 17 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 8 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  else
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 ORDER BY check_key;" >"$output_file"
  fi

  if (( DISCOVERED_MIGRATION_COUNT > 52 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round3k', check_key, violation_count, passed
                 FROM audit.run_round3k_validation_queries()
                 ORDER BY check_key;" >>"$output_file"
  fi

  if (( DISCOVERED_MIGRATION_COUNT > 56 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round3m', check_key, violation_count, passed
                 FROM audit.run_round3m_gate_validation_queries()
                 ORDER BY check_key;" >>"$output_file"
  fi
}

write_round3h_checkpoint_results() {
  local database_name=$1
  local output_file=$2

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command='SELECT check_key, violation_count, passed
               FROM audit.run_round3h_validation_queries()
               ORDER BY check_key;' >"$output_file"

  psql_target "$database_name" <<'SQL'
DO $round3h_checkpoint_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3h_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3h_validation_queries()
    WHERE NOT passed OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3H checkpoint validation failed before Round 3I migrations';
  END IF;
END
$round3h_checkpoint_gate$;
SQL

  local checkpoint_test
  for checkpoint_test in \
    "$DB_DIR/tests/round3h_negative.sql" \
    "$DB_DIR/tests/round3h_semantic.sql" \
    "$DB_DIR/tests/round3h_retrieval.sql" \
    "$DB_DIR/tests/round3h_query_plans.sql"; do
    psql_target "$database_name" --file="$checkpoint_test"
  done
}

write_schema_guard_counts() {
  local database_name=$1
  local output_file=$2

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='=' \
    --command="WITH governed_namespaces AS (
                 SELECT oid
                 FROM pg_namespace
                 WHERE nspname IN (
                   'audit','calibration','context','corpus',
                   'evidence','kb','ml','ref','competition'
                 )
               )
               SELECT 'CONSTRAINT_TRIGGER_CATALOG_COUNT', count(*)
               FROM pg_constraint
               WHERE connamespace IN (SELECT oid FROM governed_namespaces)
                 AND contype = 't'
               UNION ALL
               SELECT 'PG_CONSTRAINT_COUNT', count(*)
               FROM pg_constraint
               WHERE connamespace IN (SELECT oid FROM governed_namespaces)
               UNION ALL
               SELECT 'RELATIONAL_CONSTRAINT_COUNT', count(*)
               FROM pg_constraint
               WHERE connamespace IN (SELECT oid FROM governed_namespaces)
                 AND contype <> 't'
               UNION ALL
               SELECT 'USER_EVENT_TRIGGER_COUNT', count(*)
               FROM pg_event_trigger
               UNION ALL
               SELECT 'USER_TRIGGER_COUNT', count(*)
               FROM pg_trigger AS trigger_record
               JOIN pg_class AS relation
                 ON relation.oid = trigger_record.tgrelid
               WHERE relation.relnamespace IN (
                 SELECT oid FROM governed_namespaces
               )
                 AND NOT trigger_record.tgisinternal
               ORDER BY 1;" >"$output_file"
}

apply_with_round3h_checkpoint() {
  local database_name=$1
  local checkpoint_output=$2
  local checkpoint_schema_guard_output=$3
  local round3i_schema_guard_output=$4
  local round3i_freeze_output_dir=$5
  local migrations=()
  local migration
  local index

  while IFS= read -r migration; do
    migrations+=("$migration")
  done < <("$MIGRATION_PLAN" paths)

  if (( DISCOVERED_MIGRATION_COUNT <= 48 )); then
    "$SCRIPT_DIR/apply.sh" "$database_name"
    : >"$checkpoint_output"
    : >"$checkpoint_schema_guard_output"
    : >"$round3i_schema_guard_output"
    return
  fi

  printf 'Applying immutable Round 3H checkpoint (migrations 000-044).\n'
  for (( index=0; index<45; index+=1 )); do
    psql_target "$database_name" --file="${migrations[$index]}"
  done
  write_round3h_checkpoint_results "$database_name" "$checkpoint_output"
  write_schema_guard_counts "$database_name" "$checkpoint_schema_guard_output"
  printf 'ROUND3H_CHECKPOINT_VALIDATION_PASS=true\n'

  printf 'Applying immutable Round 3I freeze migrations (045-048).\n'
  for (( index=45; index<49; index+=1 )); do
    psql_target "$database_name" --file="${migrations[$index]}"
  done
  write_schema_guard_counts "$database_name" "$round3i_schema_guard_output"
  python3 "$SCRIPT_DIR/export-round3i-freeze.py" \
    --database "$database_name" \
    --output-dir "$round3i_freeze_output_dir"
  printf 'ROUND3I_CHECKPOINT_EXPORT_PASS=true\n'

  printf 'Applying forward migrations after frozen Round 3I (049+).\n'
  for (( index=49; index<DISCOVERED_MIGRATION_COUNT; index+=1 )); do
    psql_target "$database_name" --file="${migrations[$index]}"
  done
  printf 'MIGRATION_COUNT=%d\n' "$DISCOVERED_MIGRATION_COUNT"
  printf 'MIGRATION_PASS=true\n'
}

write_round3a_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 21 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT
                     'coverage', metric_key, metric_value::TEXT
                   FROM context.v_context_coverage

                   UNION ALL

                   SELECT
                     'preparation', preparation_concept_key,
                     concat_ws(',', preparation_concept_type_code,
                       lifecycle_status_code, c0_top_level, c0_second_level,
                       direct_parent_count, direct_child_count,
                       support_count, external_support_count)
                   FROM context.v_preparation_taxonomy

                   UNION ALL

                   SELECT
                     'roast_category', source_roast_category_key,
                     concat_ws(',', source_roast_scheme_key,
                       COALESCE(source_ordinal_position::TEXT, 'none'),
                       COALESCE(context_mapping_certainty_code, 'unresolved'),
                       COALESCE(normalized_roast_category_key, 'unresolved'))
                   FROM context.v_roast_normalization

                   UNION ALL

                   SELECT
                     'unresolved_label', context_domain || '.' || expression_key,
                     concat_ws(',', language_tag_code, normalized_text,
                       lifecycle_status_code)
                   FROM context.v_unresolved_context_labels

                   UNION ALL

                   SELECT
                     'measurement_method', roast_measurement_method_key,
                     concat_ws(',', roast_measurement_basis_code, unit,
                       minimum_value, maximum_value, higher_value_is_lighter)
                   FROM context.roast_measurement_method
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3b_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 25 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'coverage', metric_key, metric_value::TEXT
                   FROM context.v_round3b_context_coverage

                   UNION ALL

                   SELECT 'normalization_metric', metric_key,
                          metric_value::TEXT
                   FROM context.v_held_out_normalization_metrics

                   UNION ALL

                   SELECT 'preparation_choice', preparation_concept_key,
                          concat_ws(',', ordinal_position,
                            candidate_user_label_en,
                            candidate_user_label_zh_hans)
                   FROM context.v_current_user_preparation

                   UNION ALL

                   SELECT 'roast_choice', roast_category_key,
                          concat_ws(',', ordinal_position,
                            interaction_code, scale_semantics)
                   FROM context.v_current_user_roast

                   UNION ALL

                   SELECT 'source', context_source_review_key,
                          concat_ws(',', doi, version_label, license_spdx,
                            context_acquisition_status_code,
                            COALESCE(inspected_row_count::TEXT, 'none'),
                            frozen_file_count)
                   FROM context.v_context_source_inventory

                   UNION ALL

                   SELECT 'snapshot', snapshot_key,
                          concat_ws(',', snapshot_hash,
                            normalization_version, code_commit,
                            case_count, held_out_case_count, is_frozen)
                   FROM context.context_dataset_snapshot
                   WHERE snapshot_key = 'context.snapshot.round3b_v1'
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3c_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 29 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'study', study_key,
                          concat_ws(',', institutional_approval_status,
                            ethics_or_approval_gate, consent_material_ready,
                            public_release_rights_ready,
                            empirical_observation_count)
                   FROM calibration.study

                   UNION ALL

                   SELECT 'design', design_scale_code,
                          concat_ws(',', coffee_lot_count, roast_batch_count,
                            preparation_family_count, roast_category_count,
                            condition_cell_count, beverage_sample_count,
                            includes_milk_mode, calibration_power_status)
                   FROM calibration.study_design_target

                   UNION ALL

                   SELECT 'question', question_key,
                          concat_ws(',', logical_question_code,
                            language_tag_code, option_count,
                            interaction_position_code)
                   FROM calibration.v_question_bank

                   UNION ALL

                   SELECT 'observation_inventory', study_key,
                          concat_ws(',', real_beverage_sample_count,
                            real_sensory_observation_count,
                            dry_run_sensory_observation_count,
                            estimability_status)
                   FROM calibration.v_calibration_observation_inventory
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3d_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 32 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'pilot_inventory', pilot_matrix_snapshot_key,
                          concat_ws(',', matrix_sha256,
                            randomization_sha256,
                            question_assignment_sha256,
                            protocol_sha256, split_inventory_sha256,
                            coffee_lot_count, roast_batch_count,
                            preparation_condition_count,
                            beverage_sample_count, session_slot_count,
                            presentation_slot_count,
                            question_assignment_slot_count,
                            dry_run_fixture_count, real_observation_count,
                            is_frozen)
                   FROM calibration.v_round3d_pilot_inventory

                   UNION ALL

                   SELECT 'analysis', analysis_run_key,
                          concat_ws(',', estimability_status,
                            release_version, real_observation_count,
                            dry_run_fixture_count, analysis_status,
                            fixture_exclusion_pass,
                            deep_learning_model_run,
                            embedding_baseline_run, pgvector_required,
                            outputs::TEXT)
                   FROM calibration.v_round3d_analysis_status

                   UNION ALL

                   SELECT 'capture_batch', capture_import_batch_key,
                          concat_ws(',', source_manifest_sha256,
                            staged_row_count, real_row_count,
                            fixture_row_count, pii_scan_pass,
                            governance_gate_pass, promotion_status)
                   FROM calibration.capture_import_batch

                   UNION ALL

                   SELECT 'dry_run', dry_run_case_key,
                          concat_ws(',', c0_code, c1_code,
                            expected_stop_step, explicit_override,
                            fixture_label, mechanics_pass)
                   FROM calibration.engineering_dry_run_case

                   UNION ALL

                   SELECT 'release', release_snapshot_key,
                          concat_ws(',', version_label,
                            lifecycle_status_code, manifest_sha256,
                            checksums_sha256, license_spdx,
                            split_snapshot_sha256,
                            real_observation_count,
                            dry_run_fixture_count)
                   FROM calibration.release_snapshot
                   WHERE release_snapshot_key =
                     'release.context_calibration_v0.protocol_schema_v0_1_0'
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3e_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 35 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'snapshot', dataset_snapshot_key,
                          concat_ws(',', source_key, source_version_key,
                            dataset_key, source_version,
                            declared_row_count, verified_row_count,
                            declared_field_count, verified_field_count,
                            imported_record_count, exclusion_count,
                            import_version, import_code_sha,
                            license_expression, rights_decision,
                            privacy_decision, public_release_eligible,
                            source_file_count, matched_file_hash_count,
                            external_observation_count,
                            external_document_count)
                   FROM evidence.v_external_snapshot_inventory

                   UNION ALL

                   SELECT 'file_hash',
                          dataset_snapshot_key || ':' || source_file_path,
                          concat_ws(',', declared_sha256, observed_sha256,
                            declared_row_count, declared_field_count,
                            included_row_count, exclusion_count,
                            counts_toward_snapshot,
                            raw_public_export_allowed, pii_scan_pass)
                   FROM evidence.external_source_file

                   UNION ALL

                   SELECT 'artifact_hash', artifact_key, sha256
                   FROM audit.round3e_artifact_hash

                   UNION ALL

                   SELECT 'import_run', external_import_run_key,
                          concat_ws(',', import_version, import_code_sha,
                            raw_snapshot_row_count, imported_record_count,
                            exclusion_count, source_file_count,
                            source_file_hash_count, pii_scan_pass,
                            rights_review_pass,
                            public_export_policy_pass,
                            quality_profile::TEXT)
                   FROM audit.external_import_run

                   UNION ALL

                   SELECT 'question', question_version_key,
                          concat_ws(',', logical_question_code,
                            language_code, lifecycle_status,
                            information_gain_status,
                            ordinary_user_validation_evidence IS NULL)
                   FROM calibration.question_research_candidate

                   UNION ALL

                   SELECT 'coverage', empirical_coverage_cell_id::TEXT,
                          concat_ws(',', source_key, coffee_identity,
                            c0_preparation, c1_roast, black_milk,
                            sensory_method, participant_type,
                            language_code, observed_record_count,
                            cell_status)
                   FROM audit.empirical_coverage_cell
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3f_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 38 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="SELECT 'relationship_constraint_delta', 'round3f',
                      row_to_json(delta)::TEXT
               FROM audit.v_round3f_relationship_constraint_delta AS delta;" \
    >"$output_file"
}

write_round3g_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 41 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'expected_state', metric_key,
                          concat_ws(',',
                            COALESCE(baseline_value, 'none'),
                            COALESCE(minimum_expected_value, 'none'),
                            COALESCE(preferred_expected_value, 'none'),
                            observed_value, hard_gate, minimum_gate,
                            preferred_gate, passed, evidence_path)
                   FROM audit.run_round3g_expected_state_gate()

                   UNION ALL

                   SELECT 'expected_state_result', 'round3g',
                          audit.round3g_expected_state_result()

                   UNION ALL

                   SELECT 'relationship_constraint_delta', 'round3g',
                          row_to_json(delta)::TEXT
                   FROM audit.v_round3g_relationship_constraint_delta AS delta
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3h_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 44 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'readiness_gate', readiness_key,
                          concat_ws(',', minimum_required,
                            preferred_required, observed,
                            hard_gate, passed, evidence_path)
                   FROM audit.run_model_prebuild_readiness_gate()

                   UNION ALL

                   SELECT 'readiness_state', 'round3h',
                          audit.model_prebuild_readiness_state()

                   UNION ALL

                   SELECT 'coverage', 'round3h', row_to_json(coverage)::TEXT
                   FROM audit.v_model_prebuild_coverage AS coverage

                   UNION ALL

                   SELECT 'feature', feature_key,
                          concat_ws(',', harmonization_status,
                            data_type, unit, model_use_status)
                   FROM evidence.model_prebuild_feature_definition

                   UNION ALL

                   SELECT 'partition', partition_key,
                          concat_ws(',', source_family_key,
                            dataset_snapshot_key, participant_type,
                            sensory_method, sample_count, row_count,
                            future_training_surface_status,
                            compatible_join_group)
                   FROM evidence.model_prebuild_source_partition

                   UNION ALL

                   SELECT 'leakage', leakage_risk_key,
                          concat_ws(',', risk_type, control_status,
                            control_key, audit_pass)
                   FROM audit.model_prebuild_leakage_risk

                   UNION ALL

                   SELECT 'relationship_constraint_delta', 'round3h',
                          row_to_json(delta)::TEXT
                   FROM audit.v_model_prebuild_relationship_delta AS delta
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3k_inventories() {
  local database_name=$1
  local output_dir=$2

  mkdir -p "$output_dir"

  if (( DISCOVERED_MIGRATION_COUNT <= 52 )); then
    : >"$output_dir/competition-series-inventory.txt"
    : >"$output_dir/edition-inventory.txt"
    : >"$output_dir/effective-record-inventory.txt"
    : >"$output_dir/descriptor-assertion-inventory.txt"
    : >"$output_dir/rights-inventory.txt"
    : >"$output_dir/duplicate-repeat-inventory.txt"
    : >"$output_dir/label-disposition-inventory.txt"
    : >"$output_dir/training-corpus-manifest.txt"
    return
  fi

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT series_key, official_name, organizer_name,
                      COALESCE(official_series_identifier, ''),
                      series_scope_code, lifecycle_status_code,
                      series_metadata::TEXT
               FROM competition.series
               ORDER BY series_key;" \
    >"$output_dir/competition-series-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT series.series_key, edition.edition_key,
                      edition.series_local_edition_key,
                      COALESCE(edition.official_edition_identifier, ''),
                      edition.edition_name, edition.edition_year,
                      COALESCE(edition.starts_on::TEXT, ''),
                      COALESCE(edition.ends_on::TEXT, ''),
                      edition.lifecycle_status_code,
                      edition.edition_metadata::TEXT
               FROM competition.edition AS edition
               JOIN competition.series AS series
                 ON series.series_id = edition.series_id
               ORDER BY series.series_key, edition.edition_key;" \
    >"$output_dir/edition-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT service.preparation_service_key, series.series_key,
                      edition.edition_key, category.category_key,
                      round_record.round_key,
                      COALESCE(entry.entry_key, lot.lot_key),
                      service.entry_service_key,
                      COALESCE(parent.preparation_service_key, ''),
                      COALESCE(service.repeat_relationship_code, ''),
                      service.fresh_preparation_confirmed,
                      service.fresh_preparation_status_code,
                      service.preparation_taxonomy_code,
                      service.milk_auxiliary,
                      service.black_coffee_core_candidate,
                      service.c0_source_status_code,
                      COALESCE(preparation.preparation_concept_key, ''),
                      service.source_native_roast_status_code,
                      COALESCE(service.source_native_roast_value, ''),
                      COALESCE(service.source_native_roast_scheme, ''),
                      service.c1_mapping_status_code,
                      COALESCE(roast.roast_category_key, ''),
                      service.lifecycle_status_code
               FROM competition.preparation_service AS service
               JOIN competition.series AS series
                 ON series.series_id = service.series_id
               JOIN competition.edition AS edition
                 ON edition.edition_id = service.edition_id
               JOIN competition.category AS category
                 ON category.category_id = service.category_id
               JOIN competition.round AS round_record
                 ON round_record.round_id = service.round_id
               LEFT JOIN competition.entry AS entry
                 ON entry.entry_id = service.entry_id
               LEFT JOIN competition.lot AS lot
                 ON lot.lot_id = service.lot_id
               LEFT JOIN competition.preparation_service AS parent
                 ON parent.preparation_service_id =
                    service.repeat_of_preparation_service_id
               LEFT JOIN context.preparation_concept AS preparation
                 ON preparation.preparation_concept_id =
                    service.c0_preparation_concept_id
               LEFT JOIN context.roast_category AS roast
                 ON roast.roast_category_id =
                    service.reviewed_c1_roast_category_id
               ORDER BY service.preparation_service_key;" \
    >"$output_dir/effective-record-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT assertion.descriptor_assertion_key,
                      service.preparation_service_key,
                      assertion.assertion_type_code,
                      assertion.evidence_tier_code,
                      assertion.language_tag,
                      assertion.raw_phrase_sha256,
                      COALESCE(assertion.source_defined_descriptor_key, ''),
                      snapshot.professional_source_snapshot_key,
                      COALESCE(source_file.professional_source_file_key, ''),
                      assertion.source_locator,
                      assertion.derived_from_judge_observations,
                      assertion.semantic_inference_used
               FROM competition.descriptor_assertion AS assertion
               JOIN competition.preparation_service AS service
                 ON service.preparation_service_id =
                    assertion.preparation_service_id
               JOIN evidence.professional_source_snapshot AS snapshot
                 ON snapshot.professional_source_snapshot_id =
                    assertion.professional_source_snapshot_id
               LEFT JOIN evidence.professional_source_file AS source_file
                 ON source_file.professional_source_file_id =
                    assertion.professional_source_file_id
               ORDER BY assertion.descriptor_assertion_key;" \
    >"$output_dir/descriptor-assertion-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT decision.professional_rights_decision_key,
                      snapshot.professional_source_snapshot_key,
                      decision.public_results_use,
                      decision.public_descriptor_use,
                      decision.internal_research_use,
                      decision.public_derived_release,
                      decision.model_research_use,
                      decision.commercial_model_use,
                      decision.decision_authority_code,
                      decision.decided_on,
                      COALESCE(predecessor.professional_rights_decision_key, '')
               FROM evidence.professional_rights_decision AS decision
               JOIN evidence.professional_source_snapshot AS snapshot
                 ON snapshot.professional_source_snapshot_id =
                    decision.professional_source_snapshot_id
               LEFT JOIN evidence.professional_rights_decision AS predecessor
                 ON predecessor.professional_rights_decision_id =
                    decision.supersedes_decision_id
               ORDER BY decision.professional_rights_decision_key;" \
    >"$output_dir/rights-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT 'duplicate', duplicate_group.professional_duplicate_group_key,
                      duplicate_group.duplicate_type_code,
                      member.member_ordinal::TEXT,
                      COALESCE(service.preparation_service_key,
                               snapshot.professional_source_snapshot_key),
                      member.member_role_code
               FROM audit.professional_duplicate_group AS duplicate_group
               JOIN audit.professional_duplicate_group_member AS member
                 ON member.professional_duplicate_group_id =
                    duplicate_group.professional_duplicate_group_id
               LEFT JOIN competition.preparation_service AS service
                 ON service.preparation_service_id = member.preparation_service_id
               LEFT JOIN evidence.professional_source_snapshot AS snapshot
                 ON snapshot.professional_source_snapshot_id =
                    member.professional_source_snapshot_id
               UNION ALL
               SELECT 'repeat', service.preparation_service_key,
                      repeat_audit.repeat_relationship_code, '1',
                      parent.preparation_service_key,
                      repeat_audit.relationship_status_code
               FROM audit.professional_repeat_audit AS repeat_audit
               JOIN competition.preparation_service AS service
                 ON service.preparation_service_id =
                    repeat_audit.preparation_service_id
               JOIN competition.preparation_service AS parent
                 ON parent.preparation_service_id =
                    repeat_audit.repeats_preparation_service_id
               ORDER BY 1, 2, 4;" \
    >"$output_dir/duplicate-repeat-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT decision.professional_label_decision_key,
                      expression.professional_expression_key,
                      decision.decision_version,
                      decision.label_disposition_code,
                      decision.decision_method_code,
                      decision.decision_status_code,
                      decision.expert_review_complete,
                      decision.candidate_only,
                      decision.provenance_complete,
                      COALESCE(string_agg(
                          COALESCE(concept.concept_key, association_range.range_key),
                          ',' ORDER BY target.target_ordinal
                      ), '')
               FROM corpus.professional_label_decision AS decision
               JOIN corpus.professional_expression AS expression
                 ON expression.professional_expression_id =
                    decision.professional_expression_id
               LEFT JOIN corpus.professional_label_target AS target
                 ON target.professional_label_decision_id =
                    decision.professional_label_decision_id
               LEFT JOIN kb.concept AS concept
                 ON concept.concept_id = target.concept_id
               LEFT JOIN corpus.association_range AS association_range
                 ON association_range.association_range_id =
                    target.association_range_id
               GROUP BY decision.professional_label_decision_id,
                        expression.professional_expression_key
               ORDER BY decision.professional_label_decision_key;" \
    >"$output_dir/label-disposition-inventory.txt"

  psql_target "$database_name" \
    --tuples-only --no-align --field-separator='|' \
    --command="SELECT 'artifact', round3k_artifact_key,
                      artifact_type_code, artifact_path, artifact_sha256
               FROM audit.round3k_artifact_registry
               WHERE artifact_type_code =
                     'TRAINING_CORPUS_CANDIDATE_MANIFEST'
               UNION ALL
               SELECT 'candidate', professional_training_candidate_key,
                      task_code, candidate_status_code,
                      concat_ws(',', provenance_complete, rights_complete,
                                integrity_complete, included)
               FROM ml.professional_training_candidate
               UNION ALL
               SELECT 'split', assignment.assignment_key,
                      split_plan.professional_split_plan_key,
                      assignment.partition_code,
                      assignment.deterministic_assignment_sha256
               FROM ml.professional_split_assignment AS assignment
               JOIN ml.professional_split_plan AS split_plan
                 ON split_plan.professional_split_plan_id =
                    assignment.professional_split_plan_id
               ORDER BY 1, 2;" \
    >"$output_dir/training-corpus-manifest.txt"
}

write_round2b_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 15 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT
                     'source_policy_decision',
                     review.corpus_source_decision_code,
                     count(*)::TEXT
                   FROM corpus.source_policy_review AS review
                   GROUP BY review.corpus_source_decision_code

                   UNION ALL

                   SELECT
                     'corpus_snapshot',
                     snapshot.corpus_snapshot_key,
                     concat_ws(',',
                       snapshot.expected_document_count,
                       snapshot.expected_observation_count,
                       snapshot.expected_normalized_expression_count,
                       snapshot.source_inventory_sha256,
                       snapshot.document_inventory_sha256,
                       snapshot.code_commit_sha,
                       snapshot.frozen_at IS NOT NULL
                     )
                   FROM corpus.corpus_snapshot AS snapshot

                   UNION ALL

                   SELECT
                     'observation_retention',
                     observation.observation_retention_code,
                     count(*)::TEXT
                   FROM corpus.raw_observation AS observation
                   JOIN corpus.captured_document AS document
                     ON document.captured_document_id = observation.captured_document_id
                   JOIN corpus.corpus AS selected_corpus
                     ON selected_corpus.corpus_id = document.corpus_id
                   WHERE selected_corpus.corpus_key = 'corpus.firstbloom_a6cb002_pilot_v1'
                   GROUP BY observation.observation_retention_code

                   UNION ALL

                   SELECT
                     'normalization_run',
                     inventory.normalization_derivation_run_key,
                     concat_ws(',',
                       inventory.input_observation_count,
                       inventory.output_occurrence_count,
                       inventory.stored_occurrence_count,
                       inventory.unique_normalized_expression_count,
                       inventory.unique_surface_expression_count,
                       inventory.input_inventory_sha256,
                       inventory.output_inventory_sha256,
                       inventory.code_commit_sha,
                       inventory.frozen_at IS NOT NULL
                     )
                   FROM corpus.v_round2b_normalization_inventory AS inventory

                   UNION ALL

                   SELECT
                     'resolution_run',
                     resolution_run.observation_resolution_run_key,
                     concat_ws(',',
                       derivation.normalization_derivation_run_key,
                       resolution_run.policy_version,
                       to_char(
                         resolution_run.resolution_as_of AT TIME ZONE 'UTC',
                         'YYYY-MM-DD HH24:MI:SS.US'
                       ) || 'Z',
                       resolution_run.expected_occurrence_count,
                       resolution_run.resolved_occurrence_count,
                       resolution_run.unresolved_occurrence_count,
                       resolution_run.expected_normalized_identity_count,
                       resolution_run.resolved_only_normalized_identity_count,
                       resolution_run.unresolved_only_normalized_identity_count,
                       resolution_run.mixed_normalized_identity_count,
                       resolution_run.policy_sha256,
                       resolution_run.result_inventory_sha256,
                       resolution_run.source_baseline_sha,
                       resolution_run.frozen_at IS NOT NULL
                     )
                   FROM corpus.observation_resolution_run AS resolution_run
                   JOIN corpus.normalization_derivation_run AS derivation
                     ON derivation.normalization_derivation_run_id =
                        resolution_run.normalization_derivation_run_id

                   UNION ALL

                   SELECT
                     'statistic_run',
                     statistic_run.corpus_statistic_run_key,
                     concat_ws(',',
                       statistic_run.sample_document_count,
                       statistic_run.sample_observation_count,
                       (SELECT count(*) FROM corpus.normalized_expression_frequency AS frequency
                        WHERE frequency.corpus_statistic_run_id = statistic_run.corpus_statistic_run_id),
                       (SELECT count(*) FROM corpus.normalized_expression_pair_measurement AS pair
                        WHERE pair.corpus_statistic_run_id = statistic_run.corpus_statistic_run_id),
                       statistic_run.configuration_sha256,
                       statistic_run.result_inventory_sha256,
                       statistic_run.frozen_at IS NOT NULL
                     )
                   FROM corpus.corpus_statistic_run AS statistic_run

                   UNION ALL

                   SELECT
                     'audit_split',
                     audit_set.retrieval_audit_set_key || '.' || audit_case.audit_split_code,
                     count(*)::TEXT
                   FROM audit.retrieval_audit_set AS audit_set
                   JOIN audit.retrieval_audit_case AS audit_case
                     ON audit_case.retrieval_audit_set_id = audit_set.retrieval_audit_set_id
                   GROUP BY audit_set.retrieval_audit_set_key, audit_case.audit_split_code

                   UNION ALL

                   SELECT
                     'audit_set',
                     audit_set.retrieval_audit_set_key,
                     concat_ws(',',
                       audit_set.version_label,
                       audit_set.inventory_sha256,
                       audit_set.code_commit_sha,
                       (SELECT count(*)
                        FROM audit.retrieval_audit_case AS audit_case
                        WHERE audit_case.retrieval_audit_set_id =
                              audit_set.retrieval_audit_set_id),
                       audit_set.frozen_at IS NOT NULL
                     )
                   FROM audit.retrieval_audit_set AS audit_set

                   UNION ALL

                   SELECT
                     'retrieval_run',
                     model_run.model_run_key,
                     concat_ws(',',
                       deterministic_run.retrieval_baseline_code,
                       model_run.model_run_status_code,
                       deterministic_run.top_k,
                       deterministic_run.trigram_threshold,
                       deterministic_run.configuration_sha256,
                       (SELECT count(*) FROM ml.mapping_inference AS inference
                        WHERE inference.model_run_id = model_run.model_run_id),
                       (SELECT count(*) FROM ml.mapping_candidate AS candidate
                        JOIN ml.mapping_inference AS inference
                          ON inference.mapping_inference_id = candidate.mapping_inference_id
                        WHERE inference.model_run_id = model_run.model_run_id)
                     )
                   FROM ml.model_run AS model_run
                   JOIN ml.deterministic_retrieval_run AS deterministic_run
                     ON deterministic_run.model_run_id = model_run.model_run_id

                   UNION ALL

                   SELECT
                     'retrieval_metric',
                     evaluation.retrieval_evaluation_key || '.' ||
                       metric.retrieval_metric_code || '.' ||
                       COALESCE(metric.cutoff_k::TEXT, 'none'),
                     concat_ws(',',
                       metric.numerator,
                       metric.denominator,
                       metric.metric_value
                     )
                   FROM audit.retrieval_metric_value AS metric
                   JOIN audit.retrieval_evaluation AS evaluation
                     ON evaluation.retrieval_evaluation_id = metric.retrieval_evaluation_id
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_ontology_coverage() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT > 8 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command='SELECT metric_key, metric_value
                 FROM kb.v_ontology_coverage
                 ORDER BY metric_key;' >"$output_file"
  else
    : >"$output_file"
  fi
}

normalize_schema_dump() {
  local database_name=$1
  local output_file=$2

  if [[ -n "$PG_DUMP_CONTAINER" ]]; then
    docker exec \
      --env "PGPASSWORD=${PGPASSWORD:-}" \
      "$PG_DUMP_CONTAINER" \
      pg_dump \
      --username="${PGUSER:-postgres}" \
      --schema-only \
      --no-owner \
      --no-privileges \
      --dbname="$database_name" |
      sed \
        -e '/^\\restrict /d' \
        -e '/^\\unrestrict /d' >"$output_file"
  else
    pg_dump \
      --schema-only \
      --no-owner \
      --no-privileges \
      --dbname="$database_name" |
      sed \
        -e '/^\\restrict /d' \
        -e '/^\\unrestrict /d' >"$output_file"
  fi
}

run_build() {
  local database_name=$1
  local build_label=$2
  local build_dir="$ARTIFACT_DIR/$build_label"

  mkdir -p "$build_dir"
  write_migration_manifest "$build_dir/migration-files.txt"
  write_seed_manifest "$build_dir/seed-files.txt"

  printf 'CREATE_DATABASE=%s\n' "$database_name"
  createdb \
    --maintenance-db="$ADMIN_DATABASE" \
    --template=template0 \
    --encoding=UTF8 \
    "$database_name"

  if [[ "$build_label" == build-one ]]; then
    DATABASE_ONE_CREATED=true
  else
    DATABASE_TWO_CREATED=true
  fi

  apply_with_round3h_checkpoint \
    "$database_name" \
    "$build_dir/round3h-checkpoint-validation.txt" \
    "$build_dir/round3h-checkpoint-schema-guard-counts.txt" \
    "$build_dir/round3i-checkpoint-schema-guard-counts.txt" \
    "$build_dir/round3i-freeze"
  if (( DISCOVERED_MIGRATION_COUNT > 56 )); then
    "$SCRIPT_DIR/load-round3m-artifacts.sh" "$database_name"
    printf 'ROUND3M_ARTIFACT_LOAD_PASS=true\n'
  fi
  "$SCRIPT_DIR/test.sh" "$database_name"
  write_schema_guard_counts \
    "$database_name" "$build_dir/round3k-final-schema-guard-counts.txt"

  normalize_schema_dump "$database_name" "$build_dir/schema.sql"
  write_stable_key_inventory "$database_name" "$build_dir/stable-key-inventory.txt"
  write_reference_row_counts "$database_name" "$build_dir/reference-row-counts.txt"
  write_source_version_inventory "$database_name" "$build_dir/source-version-inventory.txt"
  write_validation_results "$database_name" "$build_dir/validation-results.txt"
  write_ontology_coverage "$database_name" "$build_dir/ontology-coverage.txt"
  write_round2b_inventory "$database_name" "$build_dir/round2b-inventory.txt"
  write_round3a_inventory "$database_name" "$build_dir/round3a-inventory.txt"
  write_round3b_inventory "$database_name" "$build_dir/round3b-inventory.txt"
  write_round3c_inventory "$database_name" "$build_dir/round3c-inventory.txt"
  write_round3d_inventory "$database_name" "$build_dir/round3d-inventory.txt"
  write_round3e_inventory "$database_name" "$build_dir/round3e-inventory.txt"
  write_round3f_inventory "$database_name" "$build_dir/round3f-inventory.txt"
  write_round3g_inventory "$database_name" "$build_dir/round3g-inventory.txt"
  write_round3h_inventory "$database_name" "$build_dir/round3h-inventory.txt"
  write_round3k_inventories "$database_name" "$build_dir/round3k-inventories"
  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --command="SELECT extversion FROM pg_extension WHERE extname = 'pg_trgm';" \
    >"$build_dir/pg-trgm-version.txt"
}

print_result_file() {
  local label=$1
  local file_path=$2

  printf '%s_BEGIN\n' "$label"
  sed 's/^/  /' "$file_path"
  printf '%s_END\n' "$label"
}

compare_artifact() {
  local label=$1
  local relative_path=$2
  local first_file="$ARTIFACT_DIR/build-one/$relative_path"
  local second_file="$ARTIFACT_DIR/build-two/$relative_path"
  local first_hash
  local second_hash

  first_hash=$(sha256_file "$first_file")
  second_hash=$(sha256_file "$second_file")
  printf '%s_BUILD_ONE_SHA256=%s\n' "$label" "$first_hash"
  printf '%s_BUILD_TWO_SHA256=%s\n' "$label" "$second_hash"

  if ! cmp -s "$first_file" "$second_file"; then
    printf 'ERROR: reproducibility mismatch for %s.\n' "$label" >&2
    if command -v diff >/dev/null 2>&1; then
      diff -u "$first_file" "$second_file" >&2 || true
    fi
    return 1
  fi
}

printf 'POSTGRES_VERSION=%s\n' "$server_version"
printf 'ADMIN_DATABASE=%s\n' "$admin_database_name"
printf 'DISPOSABLE_DATABASE_ONE=%s\n' "$DATABASE_ONE"
printf 'DISPOSABLE_DATABASE_TWO=%s\n' "$DATABASE_TWO"

run_build "$DATABASE_ONE" build-one
run_build "$DATABASE_TWO" build-two

compare_artifact MIGRATION_HASH migration-files.txt
compare_artifact SEED_FILE_HASHES seed-files.txt
compare_artifact SCHEMA_ONLY_DUMP_HASH schema.sql
compare_artifact STABLE_KEY_INVENTORY stable-key-inventory.txt
compare_artifact REFERENCE_TABLE_ROW_COUNTS reference-row-counts.txt
compare_artifact SOURCE_VERSION_INVENTORY source-version-inventory.txt
compare_artifact VALIDATION_RESULT_COUNTS validation-results.txt
compare_artifact ONTOLOGY_COVERAGE ontology-coverage.txt
compare_artifact ROUND2B_INVENTORY round2b-inventory.txt
compare_artifact ROUND3A_INVENTORY round3a-inventory.txt
compare_artifact ROUND3B_INVENTORY round3b-inventory.txt
compare_artifact ROUND3C_INVENTORY round3c-inventory.txt
compare_artifact ROUND3D_INVENTORY round3d-inventory.txt
compare_artifact ROUND3E_INVENTORY round3e-inventory.txt
compare_artifact ROUND3F_INVENTORY round3f-inventory.txt
compare_artifact ROUND3G_INVENTORY round3g-inventory.txt
compare_artifact ROUND3H_INVENTORY round3h-inventory.txt
compare_artifact ROUND3H_CHECKPOINT_VALIDATION round3h-checkpoint-validation.txt
compare_artifact ROUND3H_CHECKPOINT_SCHEMA_GUARD_COUNTS \
  round3h-checkpoint-schema-guard-counts.txt
compare_artifact ROUND3I_CHECKPOINT_SCHEMA_GUARD_COUNTS \
  round3i-checkpoint-schema-guard-counts.txt
compare_artifact ROUND3K_FINAL_SCHEMA_GUARD_COUNTS \
  round3k-final-schema-guard-counts.txt
compare_artifact PG_TRGM_VERSION pg-trgm-version.txt

round3k_inventory_files=(
  competition-series-inventory.txt
  edition-inventory.txt
  effective-record-inventory.txt
  descriptor-assertion-inventory.txt
  rights-inventory.txt
  duplicate-repeat-inventory.txt
  label-disposition-inventory.txt
  training-corpus-manifest.txt
)
for round3k_inventory_file in "${round3k_inventory_files[@]}"; do
  round3k_inventory_label="ROUND3K_${round3k_inventory_file%%.*}"
  round3k_inventory_label=${round3k_inventory_label//-/_}
  compare_artifact \
    "$round3k_inventory_label" \
    "round3k-inventories/$round3k_inventory_file"
done

round3i_freeze_files=(
  CANONICAL_INVENTORY.tsv
  SOURCE_INVENTORY.tsv
  RAW_FILE_MANIFEST.tsv
  SENSORY_INVENTORY.tsv
  CONTEXT_COVERAGE.tsv
  LANGUAGE_CORPUS.tsv
  RELATIONSHIP_EVIDENCE.tsv
  QUESTION_EVIDENCE.tsv
  FEATURE_REGISTRY.tsv
  SOURCE_PARTITION.tsv
  FREEZE_MANIFEST.json
)
for freeze_file in "${round3i_freeze_files[@]}"; do
  freeze_label="ROUND3I_FREEZE_${freeze_file%%.*}"
  freeze_label=${freeze_label//-/_}
  compare_artifact "$freeze_label" "round3i-freeze/$freeze_file"
  if ! cmp -s \
      "$ARTIFACT_DIR/build-one/round3i-freeze/$freeze_file" \
      "$DB_DIR/data/freeze/coffee-sensory-research-db-v0/$freeze_file"; then
    printf 'ERROR: committed Round 3I freeze artifact differs: %s.\n' \
      "$freeze_file" >&2
    exit 1
  fi
done

seed_hash_one=$(sha256_file "$ARTIFACT_DIR/build-one/seed-files.txt")
seed_hash_two=$(sha256_file "$ARTIFACT_DIR/build-two/seed-files.txt")
printf 'SEED_HASH_BUILD_ONE_SHA256=%s\n' "$seed_hash_one"
printf 'SEED_HASH_BUILD_TWO_SHA256=%s\n' "$seed_hash_two"
if [[ "$seed_hash_one" != "$seed_hash_two" ]]; then
  printf 'ERROR: reproducibility mismatch for SEED_HASH.\n' >&2
  exit 1
fi

print_result_file MIGRATION_FILE_HASHES "$ARTIFACT_DIR/build-one/migration-files.txt"
print_result_file SEED_FILE_HASHES "$ARTIFACT_DIR/build-one/seed-files.txt"
print_result_file STABLE_KEY_INVENTORY "$ARTIFACT_DIR/build-one/stable-key-inventory.txt"
print_result_file REFERENCE_TABLE_ROW_COUNTS "$ARTIFACT_DIR/build-one/reference-row-counts.txt"
print_result_file SOURCE_VERSION_INVENTORY "$ARTIFACT_DIR/build-one/source-version-inventory.txt"
print_result_file VALIDATION_RESULT_COUNTS "$ARTIFACT_DIR/build-one/validation-results.txt"
print_result_file ONTOLOGY_COVERAGE "$ARTIFACT_DIR/build-one/ontology-coverage.txt"
print_result_file ROUND2B_INVENTORY "$ARTIFACT_DIR/build-one/round2b-inventory.txt"
print_result_file ROUND3A_INVENTORY "$ARTIFACT_DIR/build-one/round3a-inventory.txt"
print_result_file ROUND3B_INVENTORY "$ARTIFACT_DIR/build-one/round3b-inventory.txt"
print_result_file ROUND3C_INVENTORY "$ARTIFACT_DIR/build-one/round3c-inventory.txt"
print_result_file ROUND3D_INVENTORY "$ARTIFACT_DIR/build-one/round3d-inventory.txt"
print_result_file ROUND3E_INVENTORY "$ARTIFACT_DIR/build-one/round3e-inventory.txt"
print_result_file ROUND3F_INVENTORY "$ARTIFACT_DIR/build-one/round3f-inventory.txt"
print_result_file ROUND3G_INVENTORY "$ARTIFACT_DIR/build-one/round3g-inventory.txt"
print_result_file ROUND3H_INVENTORY "$ARTIFACT_DIR/build-one/round3h-inventory.txt"
print_result_file ROUND3H_CHECKPOINT_VALIDATION \
  "$ARTIFACT_DIR/build-one/round3h-checkpoint-validation.txt"
print_result_file ROUND3H_CHECKPOINT_SCHEMA_GUARD_COUNTS \
  "$ARTIFACT_DIR/build-one/round3h-checkpoint-schema-guard-counts.txt"
print_result_file ROUND3I_CHECKPOINT_SCHEMA_GUARD_COUNTS \
  "$ARTIFACT_DIR/build-one/round3i-checkpoint-schema-guard-counts.txt"
print_result_file ROUND3K_FINAL_SCHEMA_GUARD_COUNTS \
  "$ARTIFACT_DIR/build-one/round3k-final-schema-guard-counts.txt"
for round3k_inventory_file in "${round3k_inventory_files[@]}"; do
  round3k_inventory_label="ROUND3K_${round3k_inventory_file%%.*}"
  round3k_inventory_label=${round3k_inventory_label//-/_}
  print_result_file \
    "$round3k_inventory_label" \
    "$ARTIFACT_DIR/build-one/round3k-inventories/$round3k_inventory_file"
done
printf 'PG_TRGM_VERSION=%s\n' "$(sed -n '1p' "$ARTIFACT_DIR/build-one/pg-trgm-version.txt")"

round3i_relational_constraints=$(awk -F= \
  '$1 == "RELATIONAL_CONSTRAINT_COUNT" { print $2 }' \
  "$ARTIFACT_DIR/build-one/round3i-checkpoint-schema-guard-counts.txt")
final_relational_constraints=$(awk -F= \
  '$1 == "RELATIONAL_CONSTRAINT_COUNT" { print $2 }' \
  "$ARTIFACT_DIR/build-one/round3k-final-schema-guard-counts.txt")
round3i_user_triggers=$(awk -F= \
  '$1 == "USER_TRIGGER_COUNT" { print $2 }' \
  "$ARTIFACT_DIR/build-one/round3i-checkpoint-schema-guard-counts.txt")
final_user_triggers=$(awk -F= \
  '$1 == "USER_TRIGGER_COUNT" { print $2 }' \
  "$ARTIFACT_DIR/build-one/round3k-final-schema-guard-counts.txt")
round3i_event_triggers=$(awk -F= \
  '$1 == "USER_EVENT_TRIGGER_COUNT" { print $2 }' \
  "$ARTIFACT_DIR/build-one/round3i-checkpoint-schema-guard-counts.txt")
final_event_triggers=$(awk -F= \
  '$1 == "USER_EVENT_TRIGGER_COUNT" { print $2 }' \
  "$ARTIFACT_DIR/build-one/round3k-final-schema-guard-counts.txt")
new_relational_constraint_count=$((
  final_relational_constraints - round3i_relational_constraints
))
new_user_trigger_count=$((final_user_triggers - round3i_user_triggers))
new_event_trigger_count=$((
  final_event_triggers - round3i_event_triggers
))
new_trigger_count=$((new_user_trigger_count + new_event_trigger_count))
new_constraint_and_trigger_count=$((
  new_relational_constraint_count + new_trigger_count
))

printf 'NEW_RELATIONAL_CONSTRAINT_COUNT=%d\n' \
  "$new_relational_constraint_count"
printf 'NEW_USER_TRIGGER_COUNT=%d\n' "$new_user_trigger_count"
printf 'NEW_EVENT_TRIGGER_COUNT=%d\n' "$new_event_trigger_count"
printf 'NEW_TRIGGER_COUNT=%d\n' "$new_trigger_count"
printf 'NEW_CONSTRAINT_COUNT=%d\n' "$new_relational_constraint_count"
printf 'NEW_CONSTRAINT_COUNT_SEMANTICS=round3k-net-new-relational-pg-constraints-excluding-constraint-trigger-aliases\n'
printf 'NEW_CONSTRAINT_AND_TRIGGER_COUNT=%d\n' \
  "$new_constraint_and_trigger_count"

printf 'CLEAN_REBUILD_COUNT=2\n'
printf 'ROUND3I_FREEZE_ARTIFACT_COUNT=11\n'
printf 'ROUND3I_FREEZE_REPRODUCIBILITY_PASS=true\n'
printf 'ROUND3K_REPRODUCIBLE_INVENTORY_COUNT=8\n'
printf 'REPRODUCIBILITY_PASS=true\n'
