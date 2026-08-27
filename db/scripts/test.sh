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

if (( migration_count > 14 )); then
  test_files+=(
    "$DB_DIR/tests/round2b_negative.sql"
    "$DB_DIR/tests/round2b_semantic.sql"
    "$DB_DIR/tests/round2b_retrieval.sql"
    "$DB_DIR/tests/round2b_query_plans.sql"
  )
fi

if (( migration_count > 21 )); then
  test_files+=(
    "$DB_DIR/tests/round3a_negative.sql"
    "$DB_DIR/tests/round3a_semantic.sql"
    "$DB_DIR/tests/round3a_retrieval.sql"
    "$DB_DIR/tests/round3a_query_plans.sql"
  )
fi

if (( migration_count > 25 )); then
  test_files+=(
    "$DB_DIR/tests/round3b_negative.sql"
    "$DB_DIR/tests/round3b_semantic.sql"
    "$DB_DIR/tests/round3b_retrieval.sql"
    "$DB_DIR/tests/round3b_query_plans.sql"
  )
fi

if (( migration_count > 29 )); then
  test_files+=(
    "$DB_DIR/tests/round3c_negative.sql"
    "$DB_DIR/tests/round3c_semantic.sql"
    "$DB_DIR/tests/round3c_retrieval.sql"
    "$DB_DIR/tests/round3c_query_plans.sql"
  )
fi

if (( migration_count > 32 )); then
  test_files+=(
    "$DB_DIR/tests/round3d_negative.sql"
    "$DB_DIR/tests/round3d_semantic.sql"
    "$DB_DIR/tests/round3d_retrieval.sql"
    "$DB_DIR/tests/round3d_query_plans.sql"
  )
fi

if (( migration_count > 35 )); then
  test_files+=(
    "$DB_DIR/tests/round3e_negative.sql"
    "$DB_DIR/tests/round3e_semantic.sql"
    "$DB_DIR/tests/round3e_retrieval.sql"
    "$DB_DIR/tests/round3e_query_plans.sql"
  )
fi

if (( migration_count > 38 )); then
  test_files+=(
    "$DB_DIR/tests/round3f_negative.sql"
    "$DB_DIR/tests/round3f_semantic.sql"
    "$DB_DIR/tests/round3f_retrieval.sql"
    "$DB_DIR/tests/round3f_query_plans.sql"
  )
fi

if (( migration_count > 41 )); then
  test_files+=(
    "$DB_DIR/tests/round3g_negative.sql"
    "$DB_DIR/tests/round3g_semantic.sql"
    "$DB_DIR/tests/round3g_retrieval.sql"
    "$DB_DIR/tests/round3g_query_plans.sql"
  )
fi

if (( migration_count > 44 && migration_count <= 45 )); then
  test_files+=(
    "$DB_DIR/tests/round3h_negative.sql"
    "$DB_DIR/tests/round3h_semantic.sql"
    "$DB_DIR/tests/round3h_retrieval.sql"
    "$DB_DIR/tests/round3h_query_plans.sql"
  )
fi

if (( migration_count > 48 )); then
  test_files+=("$DB_DIR/tests/round3i_negative.sql")
fi

if (( migration_count > 49 )); then
  test_files+=("$DB_DIR/tests/round3j_global_negative.sql")
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

if (( migration_count > 17 )); then
  printf 'Running Round 2B validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round2b_validation_queries()
ORDER BY check_key;

DO $round2b_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM audit.run_round2b_validation_queries()
  ) OR EXISTS (
    SELECT 1
    FROM audit.run_round2b_validation_queries()
    WHERE passed IS NOT TRUE
       OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 2B database validation failed: one or more checks reported violations';
  END IF;
END
$round2b_validation_gate$;
SQL
  printf 'ROUND2B_VALIDATION_PASS=true\n'
fi

if (( migration_count > 21 )); then
  printf 'Running Round 3A validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3a_validation_queries()
ORDER BY check_key;

DO $round3a_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM audit.run_round3a_validation_queries()
  ) OR EXISTS (
    SELECT 1
    FROM audit.run_round3a_validation_queries()
    WHERE passed IS NOT TRUE
       OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3A database validation failed: one or more checks reported violations';
  END IF;
END
$round3a_validation_gate$;
SQL
  printf 'ROUND3A_VALIDATION_PASS=true\n'
fi

if (( migration_count > 25 )); then
  printf 'Running Round 3B validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3b_validation_queries()
ORDER BY check_key;

DO $round3b_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM audit.run_round3b_validation_queries()
  ) OR EXISTS (
    SELECT 1
    FROM audit.run_round3b_validation_queries()
    WHERE passed IS NOT TRUE
       OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3B database validation failed: one or more checks reported violations';
  END IF;
END
$round3b_validation_gate$;
SQL
  printf 'ROUND3B_VALIDATION_PASS=true\n'
fi

if (( migration_count > 29 )); then
  printf 'Running Round 3C validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3c_validation_queries()
ORDER BY check_key;

DO $round3c_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3c_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3c_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3C database validation failed: one or more checks reported violations';
  END IF;
END
$round3c_validation_gate$;
SQL
  printf 'ROUND3C_VALIDATION_PASS=true\n'
fi

if (( migration_count > 32 )); then
  printf 'Running Round 3D validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3d_validation_queries()
ORDER BY check_key;

DO $round3d_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3d_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3d_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3D database validation failed: one or more checks reported violations';
  END IF;
END
$round3d_validation_gate$;
SQL
  printf 'ROUND3D_VALIDATION_PASS=true\n'
fi

if (( migration_count > 35 )); then
  printf 'Running Round 3E validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3e_validation_queries()
ORDER BY check_key;

DO $round3e_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3e_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3e_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3E database validation failed: one or more checks reported violations';
  END IF;
END
$round3e_validation_gate$;
SQL
  printf 'ROUND3E_VALIDATION_PASS=true\n'
fi

if (( migration_count > 38 )); then
  printf 'Running Round 3F validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3f_validation_queries()
ORDER BY check_key;

DO $round3f_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3f_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3f_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3F database validation failed: one or more checks reported violations';
  END IF;
END
$round3f_validation_gate$;
SQL
  printf 'ROUND3F_VALIDATION_PASS=true\n'
fi

if (( migration_count > 41 )); then
  printf 'Running Round 3G validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3g_validation_queries()
ORDER BY check_key;

DO $round3g_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3g_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3g_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3G database validation failed: one or more checks reported violations';
  END IF;
END
$round3g_validation_gate$;
SQL
  printf 'ROUND3G_VALIDATION_PASS=true\n'
fi

if (( migration_count > 44 && migration_count <= 45 )); then
  printf 'Running Round 3H validation query contract on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT check_key, violation_count, passed
FROM audit.run_round3h_validation_queries()
ORDER BY check_key;

DO $round3h_validation_gate$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM audit.run_round3h_validation_queries()
  ) OR EXISTS (
    SELECT 1 FROM audit.run_round3h_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0
  ) THEN
    RAISE EXCEPTION 'Round 3H database validation failed: one or more checks reported violations';
  END IF;
END
$round3h_validation_gate$;
SQL
  printf 'ROUND3H_VALIDATION_PASS=true\n'
fi

if (( migration_count > 48 )); then
  printf 'Running Round 3I research-database freeze gate on database %s.\n' "$TARGET_DATABASE"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" <<'SQL'
SELECT freeze_gate_key, required, observed, passed, severity, evidence_path
FROM audit.run_research_database_freeze_gate()
ORDER BY freeze_gate_key;

DO $round3i_freeze_gate$
BEGIN
  IF NOT audit.model_prebuild_data_ready()
     OR NOT EXISTS (
       SELECT 1 FROM audit.run_research_database_freeze_gate()
     )
     OR EXISTS (
       SELECT 1 FROM audit.run_research_database_freeze_gate()
       WHERE severity = 'HARD' AND NOT passed
     ) THEN
    RAISE EXCEPTION 'Round 3I database freeze validation failed';
  END IF;
END
$round3i_freeze_gate$;
SQL
  printf 'ROUND3I_FREEZE_GATE_PASS=true\n'
  printf 'MODEL_PREBUILD_DATA_READY=true\n'
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
