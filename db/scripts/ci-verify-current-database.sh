#!/usr/bin/env bash

# One disposable current-tree database build. This is deliberately separate
# from rebuild-twice.sh: push CI proves migrations and the complete SQL contract
# once, while the historical workflow proves byte-identical two-build replay.

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ADMIN_DATABASE=${PGDATABASE:-postgres}
TARGET_DATABASE=${COFFEE_KB_CURRENT_DB:-coffee_sensory_kb_v0_ci_current}
DATABASE_CREATED=false

source "$SCRIPT_DIR/ci-stage-timing.sh"

missing_command=false
for required_command in python3 psql createdb dropdb; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'ERROR: current database verification requires command: %s\n' "$required_command" >&2
    missing_command=true
  else
    printf 'CI_CURRENT_DATABASE_COMMAND_%s=%s\n' \
      "$(printf '%s' "$required_command" | tr '[:lower:]' '[:upper:]')" \
      "$(command -v "$required_command")"
  fi
done
if [[ "$missing_command" == true ]]; then
  exit 69
fi

if [[ "${COFFEE_KB_ALLOW_DATABASE_DROP:-}" != 1 ]]; then
  printf 'ERROR: set COFFEE_KB_ALLOW_DATABASE_DROP=1 for the disposable current database.\n' >&2
  exit 77
fi
if [[ ! "$TARGET_DATABASE" =~ ^coffee_sensory_kb_v0_[a-z0-9_]+$ ]]; then
  printf 'ERROR: unsafe disposable database name: %s\n' "$TARGET_DATABASE" >&2
  exit 64
fi
if [[ "$TARGET_DATABASE" == "$ADMIN_DATABASE" ]]; then
  printf 'ERROR: disposable database must not be the admin database.\n' >&2
  exit 64
fi

cleanup() {
  local status=$?
  trap - EXIT INT TERM
  if [[ "$DATABASE_CREATED" == true ]]; then
    dropdb --if-exists --maintenance-db="$ADMIN_DATABASE" "$TARGET_DATABASE"
  fi
  printf 'CI_CURRENT_DATABASE_CLEANUP=true\n'
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

ci_timed DATABASE_STARTUP \
  psql -X --set=ON_ERROR_STOP=1 --dbname="$ADMIN_DATABASE" --command='SHOW server_version_num;'
server_version_num=$(psql -X --tuples-only --no-align --dbname="$ADMIN_DATABASE" --command='SHOW server_version_num;')
if [[ ! "$server_version_num" =~ ^[0-9]+$ ]] || (( server_version_num < 170000 )); then
  printf 'ERROR: PostgreSQL 17 or newer is required; server version number is %s.\n' "$server_version_num" >&2
  exit 65
fi
existing=$(psql -X --tuples-only --no-align --dbname="$ADMIN_DATABASE" \
  --command="SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$TARGET_DATABASE');")
if [[ "$existing" == t ]]; then
  printf 'ERROR: refusing to overwrite existing database %s.\n' "$TARGET_DATABASE" >&2
  exit 73
fi

ci_timed DATABASE_CREATE \
  createdb --maintenance-db="$ADMIN_DATABASE" --template=template0 --encoding=UTF8 "$TARGET_DATABASE"
DATABASE_CREATED=true
ci_timed MIGRATIONS \
  bash "$SCRIPT_DIR/apply.sh" "$TARGET_DATABASE"
ci_timed GENERATED_ARTIFACT_LOAD \
  bash "$SCRIPT_DIR/load-round3m-artifacts.sh" "$TARGET_DATABASE"
ci_timed SQL_ASSERTIONS_NEGATIVE_AND_QUERY_PLANS \
  bash "$SCRIPT_DIR/test.sh" "$TARGET_DATABASE"

printf 'CI_VERIFY_CURRENT_DATABASE_PASS=true\n'
