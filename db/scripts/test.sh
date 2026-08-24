#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DB_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
MIGRATION_PLAN="$SCRIPT_DIR/migration-plan.sh"

usage() {
  printf 'Usage: %s [database]\n' "$0" >&2
  printf 'Set PGHOST, PGPORT, and PGUSER as needed. A database argument or PGDATABASE is required.\n' >&2
}

if (( $# > 1 )); then
  usage
  exit 64
fi

TARGET_DATABASE=${1:-${PGDATABASE:-}}
if [[ -z "$TARGET_DATABASE" ]]; then
  printf 'ERROR: refusing to use libpq\047s implicit database default. Pass a database or set PGDATABASE.\n' >&2
  usage
  exit 64
fi

if ! command -v psql >/dev/null 2>&1; then
  printf 'ERROR: psql is required.\n' >&2
  exit 69
fi

test_files=(
  "$DB_DIR/tests/negative.sql"
  "$DB_DIR/tests/semantic.sql"
  "$DB_DIR/tests/retrieval.sql"
  "$DB_DIR/tests/query_plans.sql"
)

if [[ ! -x "$MIGRATION_PLAN" ]]; then
  printf 'ERROR: migration plan helper is missing or not executable: %s\n' \
    "$MIGRATION_PLAN" >&2
  exit 66
fi

"$MIGRATION_PLAN" verify
migration_count=$("$MIGRATION_PLAN" count)

if (( migration_count > 8 )); then
  test_files+=(
    "$DB_DIR/tests/round2a_negative.sql"
    "$DB_DIR/tests/round2a_semantic.sql"
    "$DB_DIR/tests/round2a_retrieval.sql"
    "$DB_DIR/tests/round2a_query_plans.sql"
  )
fi

if [[ ! -f "$DB_DIR/007_validation_queries.sql" ]]; then
  printf 'ERROR: missing db/007_validation_queries.sql. Apply all migrations before testing.\n' >&2
  exit 66
fi

for test_file in "${test_files[@]}"; do
  if [[ ! -f "$test_file" ]]; then
    printf 'ERROR: missing required test file: %s\n' "$test_file" >&2
    exit 66
  fi
done

printf 'Running validation query contract on database %s.\n' "$TARGET_DATABASE"
psql \
  -X \
  --set=ON_ERROR_STOP=1 \
  --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_validation_queries()
ORDER BY check_key;

DO $validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM audit.run_validation_queries()
  ) OR EXISTS (
    SELECT 1
    FROM audit.run_validation_queries()
    WHERE passed IS NOT TRUE
       OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'database validation failed: one or more checks reported violations';
  END IF;
END
$validation_gate$;
SQL
printf 'VALIDATION_PASS=true\n'

if (( migration_count > 8 )); then
  printf 'Running Round 2A validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round2a_validation_queries()
ORDER BY check_key;

DO $round2a_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM audit.run_round2a_validation_queries()
  ) OR EXISTS (
    SELECT 1
    FROM audit.run_round2a_validation_queries()
    WHERE passed IS NOT TRUE
       OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 2A database validation failed: one or more checks reported violations';
  END IF;
END
$round2a_validation_gate$;
SQL
  printf 'ROUND2A_VALIDATION_PASS=true\n'
fi

for test_file in "${test_files[@]}"; do
  printf 'TEST %s\n' "$(basename -- "$test_file")"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" \
    --file="$test_file"
done

printf 'DATABASE_TEST_PASS=true\n'
