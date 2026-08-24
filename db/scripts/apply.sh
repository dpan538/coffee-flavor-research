#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DB_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

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

migrations=()
while IFS= read -r migration; do
  migrations+=("$migration")
done < <(
  find "$DB_DIR" -maxdepth 1 -type f -name '00[0-7]_*.sql' -print |
    LC_ALL=C sort
)

if (( ${#migrations[@]} != 8 )); then
  printf 'ERROR: expected exactly 8 migrations matching db/000_*.sql through db/007_*.sql; found %d.\n' \
    "${#migrations[@]}" >&2
  exit 65
fi

for index in "${!migrations[@]}"; do
  migration_name=$(basename -- "${migrations[$index]}")
  expected_prefix=$(printf '%03d_' "$index")
  case "$migration_name" in
    "$expected_prefix"*.sql) ;;
    *)
      printf 'ERROR: migration position %d must start with %s; found %s.\n' \
        "$index" "$expected_prefix" "$migration_name" >&2
      exit 65
      ;;
  esac
done

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
