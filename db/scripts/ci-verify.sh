#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

printf 'CI_PHASE=DATABASE_BOOTSTRAP\n'
python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --public-fixture
printf 'CI_PHASE=MIGRATION_VALIDATION\n'
python3 -B "$SCRIPT_DIR/test-round3m-artifact-contract.py"
python3 -B "$SCRIPT_DIR/test-current-descriptor-data.py"
python3 -B "$SCRIPT_DIR/test-batch3-candidate-cleaning.py"
env -u POST20K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post20k-extension.py"
python3 -B "$SCRIPT_DIR/test-batch4-cleaned-30k.py"
env -u POST30K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post30k-extension.py"
printf 'CI_PHASE=CORPUS_CONTRACTS\n'
python3 -B "$SCRIPT_DIR/test-batch6-semantic-corpus.py"
python3 -B "$SCRIPT_DIR/test-batch7-pipeline.py"
env -u POST40K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post40k-extension.py"
python3 -B "$SCRIPT_DIR/test-normalization-smoke.py"
env \
  -u ROUND3M_RESTRICTED_ROOT \
  -u ROUND3L_RESTRICTED_ROOT \
  python3 -B "$SCRIPT_DIR/test-round3m-live-adapters.py"
printf 'CI_PHASE=SEMANTIC_CONTRACTS\n'
python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --public-snapshot
printf 'CI_PHASE=BENCHMARK_CONTRACTS\n'
python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --restricted-real
printf 'CI_PHASE=FINAL_RECONCILIATION\n'
python3 -B "$SCRIPT_DIR/run-with-heartbeat.py" \
  --phase postgres-corpus-verification \
  --interval 60 \
  -- bash "$SCRIPT_DIR/rebuild-twice.sh"

printf 'CI_VERIFY_DATABASE_PASS=true\n'
