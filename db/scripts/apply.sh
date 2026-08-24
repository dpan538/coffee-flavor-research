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

if [[ ! -x "$MIGRATION_PLAN" ]]; then
  printf 'ERROR: migration plan helper is missing or not executable: %s\n' \
    "$MIGRATION_PLAN" >&2
  exit 66
fi

"$MIGRATION_PLAN" verify

migrations=()
while IFS= read -r migration; do
  migrations+=("$migration")
done < <("$MIGRATION_PLAN" paths)

printf 'Applying %d migrations to database %s.\n' "${#migrations[@]}" "$TARGET_DATABASE"
for migration in "${migrations[@]}"; do
  printf 'APPLY %s\n' "$(basename -- "$migration")"
  psql \
    -X \
    --set=ON_ERROR_STOP=1 \
    --dbname="$TARGET_DATABASE" \
    --file="$migration"
done

printf 'MIGRATION_COUNT=%d\n' "${#migrations[@]}"
printf 'MIGRATION_PASS=true\n'
