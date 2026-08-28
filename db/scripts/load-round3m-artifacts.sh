#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
LOADER_SQL="$SCRIPT_DIR/load-round3m-artifacts.sql"
VALIDATOR="$SCRIPT_DIR/test-round3m-artifact-contract.py"

usage() {
  printf 'Usage: %s [database] [data-directory] [generated-directory]\n' "$0" >&2
  printf 'Set PGHOST, PGPORT, and PGUSER as needed. A database argument or PGDATABASE is required.\n' >&2
}

if (( $# > 3 )); then
  usage
  exit 64
fi

TARGET_DATABASE=${1:-${PGDATABASE:-}}
DATA_DIR=${2:-"$REPOSITORY_ROOT/db/data/round3m"}
GENERATED_DIR=${3:-"$REPOSITORY_ROOT/db/adapters/round3m/generated"}

if [[ -z "$TARGET_DATABASE" ]]; then
  printf 'ERROR: pass a database or set PGDATABASE.\n' >&2
  exit 64
fi
if [[ ! -d "$DATA_DIR" || ! -d "$GENERATED_DIR" ]]; then
  printf 'ERROR: Round 3M artifact directories are missing.\n' >&2
  exit 66
fi
if ! command -v psql >/dev/null 2>&1; then
  printf 'ERROR: psql is required.\n' >&2
  exit 69
fi
if ! command -v python3 >/dev/null 2>&1; then
  printf 'ERROR: python3 is required.\n' >&2
  exit 69
fi
if ! command -v perl >/dev/null 2>&1; then
  printf 'ERROR: perl is required to render client-side copy paths.\n' >&2
  exit 69
fi

DATA_DIR=$(CDPATH= cd -- "$DATA_DIR" && pwd -P)
GENERATED_DIR=$(CDPATH= cd -- "$GENERATED_DIR" && pwd -P)

validator_args=(--data-dir "$DATA_DIR" --generated-dir "$GENERATED_DIR")
if [[ ${ROUND3M_ALLOW_INCOMPLETE_FINALIZATION:-false} == true ]]; then
  validator_args+=(--allow-incomplete-finalization)
fi
python3 "$VALIDATOR" "${validator_args[@]}"

artifact_paths=(
  "$DATA_DIR/SOURCE_CENSUS_UNIVERSE.tsv"
  "$DATA_DIR/SOURCE_ROUTE_DISPOSITION.tsv"
  "$DATA_DIR/SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv"
  "$GENERATED_DIR/PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv"
  "$GENERATED_DIR/PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv"
  "$DATA_DIR/DESCRIPTOR_REVIEW_QUEUE.tsv"
  "$DATA_DIR/DESCRIPTOR_PROVISIONAL_DECISIONS.tsv"
  "$DATA_DIR/DESCRIPTOR_RIGHTS_DECISION.tsv"
  "$DATA_DIR/DESCRIPTOR_ASSERTION_LEDGER.tsv"
  "$DATA_DIR/DUPLICATE_REPEAT_DECISION.tsv"
  "$DATA_DIR/COASSERTION_EVENT.tsv"
  "$DATA_DIR/ANALYST_TIME_LOG.tsv"
)
for artifact_path in "${artifact_paths[@]}"; do
  if [[ "$artifact_path" == *"'"* || "$artifact_path" == *$'\n'* || "$artifact_path" == *$'\r'* ]]; then
    printf 'ERROR: artifact path cannot be safely represented for client-side copy: %s\n' "$artifact_path" >&2
    exit 65
  fi
done

ROUND3M_CENSUS_FILE="$DATA_DIR/SOURCE_CENSUS_UNIVERSE.tsv" \
ROUND3M_ROUTE_FILE="$DATA_DIR/SOURCE_ROUTE_DISPOSITION.tsv" \
ROUND3M_SCHEMA_FILE="$DATA_DIR/SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv" \
ROUND3M_SOURCE_ARTIFACT_FILE="$GENERATED_DIR/PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv" \
ROUND3M_EFFECTIVE_RECORD_FILE="$GENERATED_DIR/PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv" \
ROUND3M_QUEUE_FILE="$DATA_DIR/DESCRIPTOR_REVIEW_QUEUE.tsv" \
ROUND3M_DECISION_FILE="$DATA_DIR/DESCRIPTOR_PROVISIONAL_DECISIONS.tsv" \
ROUND3M_RIGHTS_FILE="$DATA_DIR/DESCRIPTOR_RIGHTS_DECISION.tsv" \
ROUND3M_LEDGER_FILE="$DATA_DIR/DESCRIPTOR_ASSERTION_LEDGER.tsv" \
ROUND3M_DUPLICATE_FILE="$DATA_DIR/DUPLICATE_REPEAT_DECISION.tsv" \
ROUND3M_PAIR_FILE="$DATA_DIR/COASSERTION_EVENT.tsv" \
ROUND3M_ANALYST_TIME_FILE="$DATA_DIR/ANALYST_TIME_LOG.tsv" \
perl -pe '
  s/__ROUND3M_CENSUS_FILE__/$ENV{ROUND3M_CENSUS_FILE}/ge;
  s/__ROUND3M_ROUTE_FILE__/$ENV{ROUND3M_ROUTE_FILE}/ge;
  s/__ROUND3M_SCHEMA_FILE__/$ENV{ROUND3M_SCHEMA_FILE}/ge;
  s/__ROUND3M_SOURCE_ARTIFACT_FILE__/$ENV{ROUND3M_SOURCE_ARTIFACT_FILE}/ge;
  s/__ROUND3M_EFFECTIVE_RECORD_FILE__/$ENV{ROUND3M_EFFECTIVE_RECORD_FILE}/ge;
  s/__ROUND3M_QUEUE_FILE__/$ENV{ROUND3M_QUEUE_FILE}/ge;
  s/__ROUND3M_DECISION_FILE__/$ENV{ROUND3M_DECISION_FILE}/ge;
  s/__ROUND3M_RIGHTS_FILE__/$ENV{ROUND3M_RIGHTS_FILE}/ge;
  s/__ROUND3M_LEDGER_FILE__/$ENV{ROUND3M_LEDGER_FILE}/ge;
  s/__ROUND3M_DUPLICATE_FILE__/$ENV{ROUND3M_DUPLICATE_FILE}/ge;
  s/__ROUND3M_PAIR_FILE__/$ENV{ROUND3M_PAIR_FILE}/ge;
  s/__ROUND3M_ANALYST_TIME_FILE__/$ENV{ROUND3M_ANALYST_TIME_FILE}/ge;
' "$LOADER_SQL" | psql \
  -X \
  --set=ON_ERROR_STOP=1 \
  --dbname="$TARGET_DATABASE"
