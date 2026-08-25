#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DB_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
ROUND_ONE_BASELINE="$DB_DIR/migration-baselines/round1.sha256"
ROUND_TWO_A_BASELINE="$DB_DIR/migration-baselines/round2a.sha256"
ROUND_TWO_B_BASELINE="$DB_DIR/migration-baselines/round2b.sha256"
ROUND_THREE_A_BASELINE="$DB_DIR/migration-baselines/round3a.sha256"
ROUND_THREE_B_BASELINE="$DB_DIR/migration-baselines/round3b.sha256"
ROUND_THREE_C_BASELINE="$DB_DIR/migration-baselines/round3c.sha256"
MODE=${1:-verify}

if (( $# > 1 )); then
  printf 'Usage: %s [verify|paths|hashes|count]\n' "$0" >&2
  exit 64
fi

case "$MODE" in
  verify | paths | hashes | count) ;;
  *)
    printf 'ERROR: unsupported migration-plan mode: %s\n' "$MODE" >&2
    exit 64
    ;;
esac

if command -v sha256sum >/dev/null 2>&1; then
  SHA256_COMMAND=sha256sum
elif command -v shasum >/dev/null 2>&1; then
  SHA256_COMMAND=shasum
else
  printf 'ERROR: sha256sum or shasum is required to verify immutable migrations.\n' >&2
  exit 69
fi

sha256_file() {
  local file_path=$1

  if [[ "$SHA256_COMMAND" == sha256sum ]]; then
    sha256sum "$file_path" | awk '{print $1}'
  else
    shasum -a 256 "$file_path" | awk '{print $1}'
  fi
}

if [[ ! -f "$ROUND_ONE_BASELINE" ]]; then
  printf 'ERROR: missing immutable Round 1 fingerprint manifest: %s\n' \
    "$ROUND_ONE_BASELINE" >&2
  exit 66
fi

if [[ ! -f "$ROUND_TWO_A_BASELINE" ]]; then
  printf 'ERROR: missing immutable Round 2A fingerprint manifest: %s\n' \
    "$ROUND_TWO_A_BASELINE" >&2
  exit 66
fi

if [[ ! -f "$ROUND_TWO_B_BASELINE" ]]; then
  printf 'ERROR: missing immutable Round 2B fingerprint manifest: %s\n' \
    "$ROUND_TWO_B_BASELINE" >&2
  exit 66
fi

if [[ ! -f "$ROUND_THREE_A_BASELINE" ]]; then
  printf 'ERROR: missing immutable Round 3A fingerprint manifest: %s\n' \
    "$ROUND_THREE_A_BASELINE" >&2
  exit 66
fi

if [[ ! -f "$ROUND_THREE_B_BASELINE" ]]; then
  printf 'ERROR: missing immutable Round 3B fingerprint manifest: %s\n' \
    "$ROUND_THREE_B_BASELINE" >&2
  exit 66
fi

if [[ ! -f "$ROUND_THREE_C_BASELINE" ]]; then
  printf 'ERROR: missing immutable Round 3C fingerprint manifest: %s\n' \
    "$ROUND_THREE_C_BASELINE" >&2
  exit 66
fi

migrations=()
while IFS= read -r migration; do
  migrations+=("$migration")
done < <(
  find "$DB_DIR" \
    -maxdepth 1 \
    -type f \
    -name '[0-9][0-9][0-9]_*.sql' \
    -print |
    LC_ALL=C sort
)

if (( ${#migrations[@]} < 8 )); then
  printf 'ERROR: expected at least immutable migrations 000 through 007; found %d.\n' \
    "${#migrations[@]}" >&2
  exit 65
fi

for index in "${!migrations[@]}"; do
  migration_name=$(basename -- "${migrations[$index]}")
  expected_prefix=$(printf '%03d_' "$index")
  case "$migration_name" in
    "$expected_prefix"*.sql) ;;
    *)
      printf 'ERROR: migration position %d must start with %s; found %s.\n' \
        "$index" "$expected_prefix" "$migration_name" >&2
      exit 65
      ;;
  esac
done

baseline_count=0
while read -r expected_hash expected_name extra_field; do
  if [[ -z "$expected_hash" && -z "$expected_name" ]]; then
    continue
  fi
  if [[ -n "${extra_field:-}" || ! "$expected_hash" =~ ^[0-9a-f]{64}$ || -z "$expected_name" ]]; then
    printf 'ERROR: malformed Round 1 fingerprint entry at position %d.\n' \
      "$baseline_count" >&2
    exit 65
  fi
  if (( baseline_count >= 8 )); then
    printf 'ERROR: Round 1 fingerprint manifest must contain exactly 8 entries.\n' >&2
    exit 65
  fi

  actual_path=${migrations[$baseline_count]}
  actual_name=$(basename -- "$actual_path")
  actual_hash=$(sha256_file "$actual_path")
  if [[ "$actual_name" != "$expected_name" || "$actual_hash" != "$expected_hash" ]]; then
    printf 'ERROR: immutable Round 1 migration fingerprint mismatch at %03d.\n' \
      "$baseline_count" >&2
    printf 'EXPECTED=%s  %s\n' "$expected_hash" "$expected_name" >&2
    printf 'ACTUAL=%s  %s\n' "$actual_hash" "$actual_name" >&2
    exit 65
  fi
  baseline_count=$((baseline_count + 1))
done <"$ROUND_ONE_BASELINE"

if (( baseline_count != 8 )); then
  printf 'ERROR: Round 1 fingerprint manifest must contain exactly 8 entries; found %d.\n' \
    "$baseline_count" >&2
  exit 65
fi

round_two_a_count=0
while read -r expected_hash expected_name extra_field; do
  if [[ -z "$expected_hash" && -z "$expected_name" ]]; then
    continue
  fi
  if [[ -n "${extra_field:-}" || ! "$expected_hash" =~ ^[0-9a-f]{64}$ || -z "$expected_name" ]]; then
    printf 'ERROR: malformed Round 2A fingerprint entry at position %d.\n' \
      "$round_two_a_count" >&2
    exit 65
  fi
  if (( round_two_a_count >= 12 )); then
    printf 'ERROR: Round 2A fingerprint manifest must contain exactly 12 entries.\n' >&2
    exit 65
  fi

  actual_path=${migrations[$round_two_a_count]}
  actual_name=$(basename -- "$actual_path")
  actual_hash=$(sha256_file "$actual_path")
  if [[ "$actual_name" != "$expected_name" || "$actual_hash" != "$expected_hash" ]]; then
    printf 'ERROR: immutable Round 2A migration fingerprint mismatch at %03d.\n' \
      "$round_two_a_count" >&2
    printf 'EXPECTED=%s  %s\n' "$expected_hash" "$expected_name" >&2
    printf 'ACTUAL=%s  %s\n' "$actual_hash" "$actual_name" >&2
    exit 65
  fi
  round_two_a_count=$((round_two_a_count + 1))
done <"$ROUND_TWO_A_BASELINE"

if (( round_two_a_count != 12 )); then
  printf 'ERROR: Round 2A fingerprint manifest must contain exactly 12 entries; found %d.\n' \
    "$round_two_a_count" >&2
  exit 65
fi

round_two_b_count=0
while read -r expected_hash expected_name extra_field; do
  if [[ -z "$expected_hash" && -z "$expected_name" ]]; then
    continue
  fi
  if [[ -n "${extra_field:-}" || ! "$expected_hash" =~ ^[0-9a-f]{64}$ || -z "$expected_name" ]]; then
    printf 'ERROR: malformed Round 2B fingerprint entry at position %d.\n' \
      "$round_two_b_count" >&2
    exit 65
  fi
  if (( round_two_b_count >= 18 )); then
    printf 'ERROR: Round 2B fingerprint manifest must contain exactly 18 entries.\n' >&2
    exit 65
  fi

  actual_path=${migrations[$round_two_b_count]}
  actual_name=$(basename -- "$actual_path")
  actual_hash=$(sha256_file "$actual_path")
  if [[ "$actual_name" != "$expected_name" || "$actual_hash" != "$expected_hash" ]]; then
    printf 'ERROR: immutable Round 2B migration fingerprint mismatch at %03d.\n' \
      "$round_two_b_count" >&2
    printf 'EXPECTED=%s  %s\n' "$expected_hash" "$expected_name" >&2
    printf 'ACTUAL=%s  %s\n' "$actual_hash" "$actual_name" >&2
    exit 65
  fi
  round_two_b_count=$((round_two_b_count + 1))
done <"$ROUND_TWO_B_BASELINE"

if (( round_two_b_count != 18 )); then
  printf 'ERROR: Round 2B fingerprint manifest must contain exactly 18 entries; found %d.\n' \
    "$round_two_b_count" >&2
  exit 65
fi

round_three_a_count=0
while read -r expected_hash expected_name extra_field; do
  if [[ -z "$expected_hash" && -z "$expected_name" ]]; then
    continue
  fi
  if [[ -n "${extra_field:-}" || ! "$expected_hash" =~ ^[0-9a-f]{64}$ || -z "$expected_name" ]]; then
    printf 'ERROR: malformed Round 3A fingerprint entry at position %d.\n' \
      "$round_three_a_count" >&2
    exit 65
  fi
  if (( round_three_a_count >= 22 )); then
    printf 'ERROR: Round 3A fingerprint manifest must contain exactly 22 entries.\n' >&2
    exit 65
  fi

  actual_path=${migrations[$round_three_a_count]}
  actual_name=$(basename -- "$actual_path")
  actual_hash=$(sha256_file "$actual_path")
  if [[ "$actual_name" != "$expected_name" || "$actual_hash" != "$expected_hash" ]]; then
    printf 'ERROR: immutable Round 3A migration fingerprint mismatch at %03d.\n' \
      "$round_three_a_count" >&2
    printf 'EXPECTED=%s  %s\n' "$expected_hash" "$expected_name" >&2
    printf 'ACTUAL=%s  %s\n' "$actual_hash" "$actual_name" >&2
    exit 65
  fi
  round_three_a_count=$((round_three_a_count + 1))
done <"$ROUND_THREE_A_BASELINE"

if (( round_three_a_count != 22 )); then
  printf 'ERROR: Round 3A fingerprint manifest must contain exactly 22 entries; found %d.\n' \
    "$round_three_a_count" >&2
  exit 65
fi

round_three_b_count=0
while read -r expected_hash expected_name extra_field; do
  if [[ -z "$expected_hash" && -z "$expected_name" ]]; then
    continue
  fi
  if [[ -n "${extra_field:-}" || ! "$expected_hash" =~ ^[0-9a-f]{64}$ || -z "$expected_name" ]]; then
    printf 'ERROR: malformed Round 3B fingerprint entry at position %d.\n' \
      "$round_three_b_count" >&2
    exit 65
  fi
  if (( round_three_b_count >= 26 )); then
    printf 'ERROR: Round 3B fingerprint manifest must contain exactly 26 entries.\n' >&2
    exit 65
  fi

  actual_path=${migrations[$round_three_b_count]}
  actual_name=$(basename -- "$actual_path")
  actual_hash=$(sha256_file "$actual_path")
  if [[ "$actual_name" != "$expected_name" || "$actual_hash" != "$expected_hash" ]]; then
    printf 'ERROR: immutable Round 3B migration fingerprint mismatch at %03d.\n' \
      "$round_three_b_count" >&2
    printf 'EXPECTED=%s  %s\n' "$expected_hash" "$expected_name" >&2
    printf 'ACTUAL=%s  %s\n' "$actual_hash" "$actual_name" >&2
    exit 65
  fi
  round_three_b_count=$((round_three_b_count + 1))
done <"$ROUND_THREE_B_BASELINE"

if (( round_three_b_count != 26 )); then
  printf 'ERROR: Round 3B fingerprint manifest must contain exactly 26 entries; found %d.\n' \
    "$round_three_b_count" >&2
  exit 65
fi

round_three_c_count=0
while read -r expected_hash expected_name extra_field; do
  if [[ -z "$expected_hash" && -z "$expected_name" ]]; then
    continue
  fi
  if [[ -n "${extra_field:-}" || ! "$expected_hash" =~ ^[0-9a-f]{64}$ || -z "$expected_name" ]]; then
    printf 'ERROR: malformed Round 3C fingerprint entry at position %d.\n' \
      "$round_three_c_count" >&2
    exit 65
  fi
  if (( round_three_c_count >= 30 )); then
    printf 'ERROR: Round 3C fingerprint manifest must contain exactly 30 entries.\n' >&2
    exit 65
  fi

  actual_path=${migrations[$round_three_c_count]}
  actual_name=$(basename -- "$actual_path")
  actual_hash=$(sha256_file "$actual_path")
  if [[ "$actual_name" != "$expected_name" || "$actual_hash" != "$expected_hash" ]]; then
    printf 'ERROR: immutable Round 3C migration fingerprint mismatch at %03d.\n' \
      "$round_three_c_count" >&2
    printf 'EXPECTED=%s  %s\n' "$expected_hash" "$expected_name" >&2
    printf 'ACTUAL=%s  %s\n' "$actual_hash" "$actual_name" >&2
    exit 65
  fi
  round_three_c_count=$((round_three_c_count + 1))
done <"$ROUND_THREE_C_BASELINE"

if (( round_three_c_count != 30 )); then
  printf 'ERROR: Round 3C fingerprint manifest must contain exactly 30 entries; found %d.\n' \
    "$round_three_c_count" >&2
  exit 65
fi

case "$MODE" in
  verify)
    printf 'ROUND1_MIGRATION_FINGERPRINT_PASS=true\n'
    printf 'ROUND2A_MIGRATION_FINGERPRINT_PASS=true\n'
    printf 'ROUND2B_MIGRATION_FINGERPRINT_PASS=true\n'
    printf 'ROUND3A_MIGRATION_FINGERPRINT_PASS=true\n'
    printf 'ROUND3B_MIGRATION_FINGERPRINT_PASS=true\n'
    printf 'ROUND3C_MIGRATION_FINGERPRINT_PASS=true\n'
    printf 'MIGRATION_COUNT=%d\n' "${#migrations[@]}"
    ;;
  paths)
    printf '%s\n' "${migrations[@]}"
    ;;
  hashes)
    for migration in "${migrations[@]}"; do
      printf '%s  %s\n' \
        "$(sha256_file "$migration")" \
        "$(basename -- "$migration")"
    done
    ;;
  count)
    printf '%d\n' "${#migrations[@]}"
    ;;
esac
