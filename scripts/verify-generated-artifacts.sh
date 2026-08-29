#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
NPM_BIN=${COFFEE_CI_NPM_BIN:-npm}
TEMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/coffee-generated-artifacts.XXXXXX")
BASELINE_MANIFEST="$TEMP_ROOT/baseline.sha256"
FIRST_MANIFEST="$TEMP_ROOT/first.sha256"
SECOND_MANIFEST="$TEMP_ROOT/second.sha256"

cleanup() {
  rm -rf -- "$TEMP_ROOT"
}
trap cleanup EXIT INT TERM

if command -v sha256sum >/dev/null 2>&1; then
  SHA256_MODE=sha256sum
elif command -v shasum >/dev/null 2>&1; then
  SHA256_MODE=shasum
else
  printf 'ERROR: sha256sum or shasum is required.\n' >&2
  exit 69
fi

generate_active_artifacts() {
  python3 "$REPOSITORY_ROOT/db/scripts/generate-round3d-pilot.py" >/dev/null
  python3 "$REPOSITORY_ROOT/db/scripts/validate-round3d-pilot.py" >/dev/null

  if [[ -f "$REPOSITORY_ROOT/db/scripts/generate-round3e-artifacts.py" ]]; then
    python3 "$REPOSITORY_ROOT/db/scripts/generate-round3e-artifacts.py" >/dev/null
  fi

  if [[ -f "$REPOSITORY_ROOT/db/scripts/prepare-round3e-release.py" ]]; then
    python3 "$REPOSITORY_ROOT/db/scripts/prepare-round3e-release.py" >/dev/null
  fi

  "$NPM_BIN" run round4a:generate >/dev/null
}

python3 "$REPOSITORY_ROOT/db/scripts/test-round3e-artifact-contract.py"
python3 "$REPOSITORY_ROOT/db/scripts/test-round3g-artifact-contract.py"
python3 "$REPOSITORY_ROOT/db/scripts/test-round3h-artifact-contract.py"
python3 "$REPOSITORY_ROOT/db/scripts/test-round3i-freeze-artifact-contract.py"
python3 "$REPOSITORY_ROOT/scripts/generate-public-project-status.py" --check
"$NPM_BIN" run test:round3k-governance-artifacts
"$NPM_BIN" run test:round3k-adapter-contract
"$NPM_BIN" run test:round4a-artifacts

write_manifest() {
  local output_path=$1
  local relative_path
  local artifact_path

  : >"$output_path"
  while IFS= read -r -d '' artifact_path; do
    relative_path=${artifact_path#"$REPOSITORY_ROOT"/}
    if [[ "$SHA256_MODE" == sha256sum ]]; then
      printf '%s  %s\n' "$(sha256sum "$artifact_path" | awk '{print $1}')" \
        "$relative_path" >>"$output_path"
    else
      printf '%s  %s\n' "$(shasum -a 256 "$artifact_path" | awk '{print $1}')" \
        "$relative_path" >>"$output_path"
    fi
  done < <(
    find \
      "$REPOSITORY_ROOT/db/data/round3d/generated" \
      "$REPOSITORY_ROOT/db/data/round3e/generated" \
      "$REPOSITORY_ROOT/db/data/round3g" \
      "$REPOSITORY_ROOT/db/data/round3h" \
      "$REPOSITORY_ROOT/db/data/model-prebuild/v0" \
      "$REPOSITORY_ROOT/db/data/freeze/coffee-sensory-research-db-v0" \
      "$REPOSITORY_ROOT/db/data/round4a" \
      "$REPOSITORY_ROOT/public/icon-192.png" \
      "$REPOSITORY_ROOT/public/icon-512.png" \
      "$REPOSITORY_ROOT/data/calibration/releases/protocol-and-schema-v0.1.1" \
      -type f -print0 2>/dev/null | LC_ALL=C sort -z
  )
}

cd "$REPOSITORY_ROOT"

write_manifest "$BASELINE_MANIFEST"
generate_active_artifacts
write_manifest "$FIRST_MANIFEST"

if ! cmp -s "$BASELINE_MANIFEST" "$FIRST_MANIFEST"; then
  printf 'ERROR: committed generated artifacts are stale or missing.\n' >&2
  diff -u "$BASELINE_MANIFEST" "$FIRST_MANIFEST" >&2 || true
  exit 1
fi

generate_active_artifacts
write_manifest "$SECOND_MANIFEST"

if ! cmp -s "$FIRST_MANIFEST" "$SECOND_MANIFEST"; then
  printf 'ERROR: generated artifact hashes changed across identical runs.\n' >&2
  diff -u "$FIRST_MANIFEST" "$SECOND_MANIFEST" >&2 || true
  exit 1
fi

FORMAT_PATHS=(db/data/round3d/generated)
if [[ -d db/data/round3e/generated ]]; then
  FORMAT_PATHS+=(db/data/round3e/generated)
fi
if [[ -d db/data/round3g ]]; then
  FORMAT_PATHS+=(db/data/round3g)
fi
if [[ -d db/data/round3h ]]; then
  FORMAT_PATHS+=(db/data/round3h)
fi
if [[ -d db/data/model-prebuild/v0 ]]; then
  FORMAT_PATHS+=(db/data/model-prebuild/v0)
fi
if [[ -d db/data/freeze/coffee-sensory-research-db-v0 ]]; then
  FORMAT_PATHS+=(db/data/freeze/coffee-sensory-research-db-v0)
fi
if [[ -d data/calibration/releases/protocol-and-schema-v0.1.1 ]]; then
  FORMAT_PATHS+=(data/calibration/releases/protocol-and-schema-v0.1.1)
fi
if [[ -d db/data/round4a ]]; then
  FORMAT_PATHS+=(db/data/round4a)
fi

"$NPM_BIN" exec -- prettier "${FORMAT_PATHS[@]}" --check

git diff --exit-code -- \
  db/data/round3d/generated \
  data/calibration/releases/protocol-and-schema-v0.1.1 \
  db/data/round3e/generated \
  db/data/round3g \
  db/data/round3h \
  db/data/model-prebuild/v0 \
  db/data/freeze/coffee-sensory-research-db-v0 \
  db/data/round4a \
  public/icon-192.png \
  public/icon-512.png

printf 'GENERATED_ARTIFACT_DRIFT_GATE_PASS=true\n'
printf 'GENERATED_ARTIFACT_NONDETERMINISM_COUNT=0\n'
