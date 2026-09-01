#!/usr/bin/env bash

# Public-safe current corpus and generated-artifact verification. Historical
# two-clean-database replay remains in ci-verify.sh and is dispatched
# separately; this script does not weaken or replace it.

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/ci-stage-timing.sh"

ci_timed PUBLIC_FIXTURE_REPLAY \
  python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --public-fixture
ci_timed ROUND3M_ARTIFACT_CONTRACT \
  python3 -B "$SCRIPT_DIR/test-round3m-artifact-contract.py"
ci_timed CURRENT_DESCRIPTOR_DATA \
  python3 -B "$SCRIPT_DIR/test-current-descriptor-data.py"
ci_timed BATCH3_CANDIDATE_CLEANING \
  python3 -B "$SCRIPT_DIR/test-batch3-candidate-cleaning.py"
ci_timed POST20K_PUBLIC_EXTENSION \
  env -u POST20K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post20k-extension.py"
ci_timed BATCH4_CLEANED_30K \
  python3 -B "$SCRIPT_DIR/test-batch4-cleaned-30k.py"
ci_timed POST30K_PUBLIC_EXTENSION \
  env -u POST30K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post30k-extension.py"
ci_timed BATCH6_SEMANTIC_CORPUS \
  python3 -B "$SCRIPT_DIR/test-batch6-semantic-corpus.py"
ci_timed BATCH7_PIPELINE \
  python3 -B "$SCRIPT_DIR/test-batch7-pipeline.py"
ci_timed POST40K_PUBLIC_EXTENSION \
  env -u POST40K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post40k-extension.py"
ci_timed NORMALIZATION_SMOKE \
  python3 -B "$SCRIPT_DIR/test-normalization-smoke.py"
ci_timed ROUND3M_LIVE_ADAPTERS_PUBLIC \
  env -u ROUND3M_RESTRICTED_ROOT -u ROUND3L_RESTRICTED_ROOT \
  python3 -B "$SCRIPT_DIR/test-round3m-live-adapters.py"
ci_timed PUBLIC_SNAPSHOT_CONTRACT \
  python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --public-snapshot
ci_timed CI_WORKFLOW_CONTRACT \
  python3 -B "$SCRIPT_DIR/test-ci-workflow-contract.py"

printf 'CI_VERIFY_CURRENT_ARTIFACTS_PASS=true\n'
