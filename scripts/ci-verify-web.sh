#!/usr/bin/env bash

set -euo pipefail

NPM_BIN=${COFFEE_CI_NPM_BIN:-npm}
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

if [[ "$NPM_BIN" == */* ]]; then
  if [[ ! -x "$NPM_BIN" ]]; then
    printf 'ERROR: configured npm executable is unavailable: %s\n' "$NPM_BIN" >&2
    exit 69
  fi
elif ! command -v "$NPM_BIN" >/dev/null 2>&1; then
  printf 'ERROR: npm is required for web verification.\n' >&2
  exit 69
fi

printf 'CI_VERIFY_STEP=generated_artifact_drift\n'
bash "$SCRIPT_DIR/verify-generated-artifacts.sh"

printf 'CI_VERIFY_STEP=public_project_contracts\n'
"$NPM_BIN" run public:verify

printf 'CI_VERIFY_STEP=format:check\n'
"$NPM_BIN" run format:check

printf 'CI_VERIFY_STEP=ci_fail_fast_contract\n'
"$NPM_BIN" run test:ci-contract

printf 'CI_VERIFY_STEP=typecheck\n'
"$NPM_BIN" run check

printf 'CI_VERIFY_STEP=unit_tests\n'
"$NPM_BIN" run test

printf 'CI_VERIFY_STEP=production_build\n'
"$NPM_BIN" run build

printf 'CI_VERIFY_STEP=playwright_smoke\n'
"$NPM_BIN" run test:smoke

printf 'CI_VERIFY_WEB_PASS=true\n'
