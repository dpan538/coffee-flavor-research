#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DB_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

ALLOW_DROP=${COFFEE_KB_ALLOW_DATABASE_DROP:-}
ADMIN_DATABASE=${PGDATABASE:-postgres}
DATABASE_ONE=${COFFEE_KB_REBUILD_DB_ONE:-coffee_sensory_kb_v0_rebuild_one}
DATABASE_TWO=${COFFEE_KB_REBUILD_DB_TWO:-coffee_sensory_kb_v0_rebuild_two}

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

required_commands=(psql createdb dropdb pg_dump find sort sed awk cmp mktemp)
for required_command in "${required_commands[@]}"; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'ERROR: required command is unavailable: %s\n' "$required_command" >&2
    exit 69
  fi
done

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
  local migration
  local migration_name
  local expected_prefix
  local index
  local migrations=()

  while IFS= read -r migration; do
    migrations+=("$migration")
  done < <(
    find "$DB_DIR" -maxdepth 1 -type f -name '00[0-7]_*.sql' -print |
      LC_ALL=C sort
  )

  if (( ${#migrations[@]} != 8 )); then
    printf 'ERROR: expected exactly 8 migrations while building hash manifest; found %d.\n' \
      "${#migrations[@]}" >&2
    return 1
  fi

  : >"$output_file"
  for index in "${!migrations[@]}"; do
    migration=${migrations[$index]}
    migration_name=$(basename -- "$migration")
    expected_prefix=$(printf '%03d_' "$index")
    case "$migration_name" in
      "$expected_prefix"*.sql) ;;
      *)
        printf 'ERROR: unexpected migration order while hashing: %s.\n' "$migration_name" >&2
        return 1
        ;;
    esac
    printf '%s  %s\n' "$(sha256_file "$migration")" "$migration_name" >>"$output_file"
  done
}

write_stable_key_inventory() {
  local database_name=$1
  local output_file=$2
  local inventory_sql

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
  AND c.table_schema IN ('ref', 'kb', 'evidence', 'corpus', 'ml', 'audit')
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

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="$inventory_sql" >"$output_file"
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

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command='SELECT check_key, violation_count, passed
               FROM audit.run_validation_queries()
               ORDER BY check_key;' >"$output_file"
}

normalize_schema_dump() {
  local database_name=$1
  local output_file=$2

  pg_dump \
    --schema-only \
    --no-owner \
    --no-privileges \
    --dbname="$database_name" |
    sed \
      -e '/^\\restrict /d' \
      -e '/^\\unrestrict /d' >"$output_file"
}

run_build() {
  local database_name=$1
  local build_label=$2
  local build_dir="$ARTIFACT_DIR/$build_label"

  mkdir -p "$build_dir"
  write_migration_manifest "$build_dir/migration-files.txt"
  sha256_file "$DB_DIR/006_reference_seed.sql" >"$build_dir/seed.sha256"

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

  "$SCRIPT_DIR/apply.sh" "$database_name"
  "$SCRIPT_DIR/test.sh" "$database_name"

  normalize_schema_dump "$database_name" "$build_dir/schema.sql"
  write_stable_key_inventory "$database_name" "$build_dir/stable-key-inventory.txt"
  write_reference_row_counts "$database_name" "$build_dir/reference-row-counts.txt"
  write_source_version_inventory "$database_name" "$build_dir/source-version-inventory.txt"
  write_validation_results "$database_name" "$build_dir/validation-results.txt"
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
compare_artifact SCHEMA_ONLY_DUMP_HASH schema.sql
compare_artifact STABLE_KEY_INVENTORY stable-key-inventory.txt
compare_artifact REFERENCE_TABLE_ROW_COUNTS reference-row-counts.txt
compare_artifact SOURCE_VERSION_INVENTORY source-version-inventory.txt
compare_artifact VALIDATION_RESULT_COUNTS validation-results.txt
compare_artifact PG_TRGM_VERSION pg-trgm-version.txt

seed_hash_one=$(sed -n '1p' "$ARTIFACT_DIR/build-one/seed.sha256")
seed_hash_two=$(sed -n '1p' "$ARTIFACT_DIR/build-two/seed.sha256")
printf 'SEED_HASH_BUILD_ONE_SHA256=%s\n' "$seed_hash_one"
printf 'SEED_HASH_BUILD_TWO_SHA256=%s\n' "$seed_hash_two"
if [[ "$seed_hash_one" != "$seed_hash_two" ]]; then
  printf 'ERROR: reproducibility mismatch for SEED_HASH.\n' >&2
  exit 1
fi

print_result_file MIGRATION_FILE_HASHES "$ARTIFACT_DIR/build-one/migration-files.txt"
print_result_file STABLE_KEY_INVENTORY "$ARTIFACT_DIR/build-one/stable-key-inventory.txt"
print_result_file REFERENCE_TABLE_ROW_COUNTS "$ARTIFACT_DIR/build-one/reference-row-counts.txt"
print_result_file SOURCE_VERSION_INVENTORY "$ARTIFACT_DIR/build-one/source-version-inventory.txt"
print_result_file VALIDATION_RESULT_COUNTS "$ARTIFACT_DIR/build-one/validation-results.txt"
printf 'PG_TRGM_VERSION=%s\n' "$(sed -n '1p' "$ARTIFACT_DIR/build-one/pg-trgm-version.txt")"

printf 'CLEAN_REBUILD_COUNT=2\n'
printf 'REPRODUCIBILITY_PASS=true\n'
