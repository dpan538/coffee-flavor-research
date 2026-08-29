#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

python3 -B "$SCRIPT_DIR/test-round3m-artifact-contract.py"
python3 -B "$SCRIPT_DIR/test-current-descriptor-data.py"
python3 -B "$SCRIPT_DIR/test-batch3-candidate-cleaning.py"
env -u POST20K_RESTRICTED_ROOT python3 -B "$SCRIPT_DIR/test-post20k-extension.py"
python3 -B "$SCRIPT_DIR/test-batch4-cleaned-30k.py"
env \
  -u ROUND3M_RESTRICTED_ROOT \
  -u ROUND3L_RESTRICTED_ROOT \
  python3 -B "$SCRIPT_DIR/test-round3m-live-adapters.py"
bash "$SCRIPT_DIR/rebuild-twice.sh"

printf 'CI_VERIFY_DATABASE_PASS=true\n'
