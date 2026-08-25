#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

bash "$SCRIPT_DIR/rebuild-twice.sh"

printf 'CI_VERIFY_DATABASE_PASS=true\n'
