#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/ci-stage-timing.sh"

printf 'CI_PHASE=HISTORICAL_PUBLIC_ARTIFACT_AND_CURRENT_CONTRACTS\n'
ci_timed CURRENT_ARTIFACTS \
  bash "$SCRIPT_DIR/ci-verify-current-artifacts.sh"
printf 'CI_PHASE=RESTRICTED_REAL_PUBLIC_DECLARATION\n'
ci_timed RESTRICTED_REAL_PUBLIC_DECLARATION \
  python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --restricted-real
printf 'CI_PHASE=HISTORICAL_TWO_CLEAN_DATABASE_REPLAY\n'
ci_timed HISTORICAL_TWO_CLEAN_DATABASE_REPLAY \
  python3 -B "$SCRIPT_DIR/run-with-heartbeat.py" \
  --phase postgres-corpus-verification \
  --interval 60 \
  -- bash "$SCRIPT_DIR/rebuild-twice.sh"

printf 'CI_VERIFY_HISTORICAL_DATABASE_PASS=true\n'
printf 'CI_VERIFY_DATABASE_PASS=true\n'
