#!/usr/bin/env bash

# Restricted real-input replay is intentionally owner-local. It is explicit and
# fail-closed when requested, rather than being represented as a public CI pass.

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/ci-stage-timing.sh"

ci_timed RESTRICTED_REAL_REPLAY \
  python3 -B "$SCRIPT_DIR/run-corpus-ci.py" --require-restricted-real
printf 'CI_VERIFY_RESTRICTED_LOCAL_PASS=true\n'
