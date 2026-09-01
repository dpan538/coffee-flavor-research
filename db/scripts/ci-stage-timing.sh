#!/usr/bin/env bash

# Shared, fail-closed stage timing for the database CI entrypoints. The values
# are elapsed seconds, not performance claims; each wrapped command retains its
# original exit status.

ci_timed() {
  local stage=$1
  shift
  local started
  local finished
  local status

  started=$(date +%s)
  printf 'CI_STAGE_START stage=%s epoch=%s\n' "$stage" "$started"
  if "$@"; then
    status=0
  else
    status=$?
  fi
  finished=$(date +%s)
  printf 'CI_STAGE_END stage=%s elapsed_seconds=%s exit_status=%s\n' \
    "$stage" "$((finished - started))" "$status"
  return "$status"
}
