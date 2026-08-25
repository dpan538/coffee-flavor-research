#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/coffee-ci-contract.XXXXXX")
STUB_NPM="$TEMP_ROOT/npm-stub"
CALL_LOG="$TEMP_ROOT/calls.log"

cleanup() {
  rm -rf -- "$TEMP_ROOT"
}
trap cleanup EXIT INT TERM

cat >"$STUB_NPM" <<'STUB'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >>"$COFFEE_CI_STUB_LOG"
if [[ "$*" == "run check" ]]; then
  exit 23
fi
STUB
chmod 700 "$STUB_NPM"

set +e
COFFEE_CI_NPM_BIN="$STUB_NPM" \
COFFEE_CI_STUB_LOG="$CALL_LOG" \
  bash "$SCRIPT_DIR/ci-verify-web.sh" >/dev/null 2>&1
status=$?
set -e

if (( status != 23 )); then
  printf 'ERROR: CI verification returned %d instead of the injected failure status 23.\n' \
    "$status" >&2
  exit 1
fi

if grep -Eq '^run (test|build|test:smoke)$' "$CALL_LOG"; then
  printf 'ERROR: CI verification continued after the injected typecheck failure.\n' >&2
  exit 1
fi

printf 'CI_FAIL_FAST_CONTRACT_PASS=true\n'
