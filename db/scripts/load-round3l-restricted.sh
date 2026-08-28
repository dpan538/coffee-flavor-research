#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
LOADER_SQL="$SCRIPT_DIR/load-round3l-restricted.sql"

usage() {
  printf 'Usage: %s RESTRICTED_ROOT FREEZE_ID MANIFEST_SHA256 [database]\n' "$0" >&2
  printf 'Set PGHOST, PGPORT, and PGUSER as needed. A database argument or PGDATABASE is required.\n' >&2
}

if (( $# < 3 || $# > 4 )); then
  usage
  exit 64
fi

RESTRICTED_ROOT=$1
FREEZE_ID=$2
MANIFEST_SHA256=$3
TARGET_DATABASE=${4:-${PGDATABASE:-}}

if [[ -z "$TARGET_DATABASE" ]]; then
  printf 'ERROR: pass a database or set PGDATABASE.\n' >&2
  exit 64
fi
if [[ ! "$FREEZE_ID" =~ ^[a-z0-9][a-z0-9._:/-]*$ ]]; then
  printf 'ERROR: invalid lowercase freeze ID.\n' >&2
  exit 65
fi
if [[ ! "$MANIFEST_SHA256" =~ ^[0-9a-f]{64}$ ]]; then
  printf 'ERROR: invalid manifest SHA-256.\n' >&2
  exit 65
fi
if [[ ! -d "$RESTRICTED_ROOT" ]]; then
  printf 'ERROR: restricted root is not a directory: %s\n' "$RESTRICTED_ROOT" >&2
  exit 66
fi

RESTRICTED_ROOT=$(CDPATH= cd -- "$RESTRICTED_ROOT" && pwd -P)
case "$RESTRICTED_ROOT/" in
  "$REPOSITORY_ROOT/"*)
    printf 'ERROR: row-level restricted data cannot be loaded from inside public Git.\n' >&2
    exit 73
    ;;
esac

required_files=(
  SOURCE_CENSUS.tsv
  SOURCE_ATTEMPTS.tsv
  PROFESSIONAL_RECORDS.tsv
  PROFESSIONAL_ASSERTIONS.tsv
  BLOCKER_QUEUE.tsv
  INGESTION_CHECKPOINT.json
)
for filename in "${required_files[@]}"; do
  if [[ ! -f "$RESTRICTED_ROOT/$filename" ]]; then
    printf 'ERROR: missing restricted freeze file: %s\n' "$filename" >&2
    exit 66
  fi
done

if ! command -v psql >/dev/null 2>&1; then
  printf 'ERROR: psql is required.\n' >&2
  exit 69
fi
if ! command -v shasum >/dev/null 2>&1; then
  printf 'ERROR: shasum is required.\n' >&2
  exit 69
fi

actual_manifest_sha=$(shasum -a 256 "$RESTRICTED_ROOT/INGESTION_CHECKPOINT.json")
actual_manifest_sha=${actual_manifest_sha%% *}
if [[ "$actual_manifest_sha" != "$MANIFEST_SHA256" ]]; then
  printf 'ERROR: restricted manifest hash mismatch.\n' >&2
  exit 65
fi

psql \
  -X \
  --set=ON_ERROR_STOP=1 \
  --set=round3l_ingest_root="$RESTRICTED_ROOT" \
  --set=round3l_freeze_id="$FREEZE_ID" \
  --set=round3l_manifest_sha256="$MANIFEST_SHA256" \
  --dbname="$TARGET_DATABASE" \
  --file="$LOADER_SQL"
