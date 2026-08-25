#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

bash "$SCRIPT_DIR/ci-verify-web.sh"
bash "$REPOSITORY_ROOT/db/scripts/ci-verify.sh"

printf 'CI_VERIFY_PASS=true\n'
