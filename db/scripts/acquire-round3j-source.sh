#!/usr/bin/env bash

set -euo pipefail

export LC_ALL=C

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
REGISTER_PATH="$ROOT_DIR/db/data/round3j/source_candidate_register.tsv"
RAW_ROOT="$ROOT_DIR/db/data/round3j/raw"

usage() {
  printf 'Usage:\n' >&2
  printf '  %s plan  --candidate KEY --source-version VERSION --artifact PATH URL [--artifact PATH URL ...]\n' "$0" >&2
  printf '  %s fetch --candidate KEY --source-version VERSION --artifact PATH URL [--artifact PATH URL ...]\n' "$0" >&2
  printf '\n' >&2
  printf 'plan validates and prints deterministic metadata without network access.\n' >&2
  printf 'fetch downloads HTTPS artifacts into a new, version-addressed directory.\n' >&2
  printf 'Artifact PATH values must be unique, safe relative paths supplied in lexical order.\n' >&2
}

fail() {
  printf 'ERROR: %s\n' "$1" >&2
  exit "${2:-64}"
}

is_preauthorized_candidate() {
  case "$1" in
    candidate.r3j.liang-full-immersion-2024 | \
      candidate.r3j.golovinsky-electrochemical-v1_1 | \
      candidate.r3j.bichlmaier-mozambioside-v1 | \
      candidate.r3j.guchengf-coffee-reviews-2025 | \
      candidate.r3j.xian-zhang-zero-price-reviews-v2)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if (( $# == 0 )); then
  usage
  exit 64
fi

MODE=$1
shift
case "$MODE" in
  plan | fetch) ;;
  *)
    usage
    fail "unsupported mode: $MODE"
    ;;
esac

CANDIDATE_KEY=
SOURCE_VERSION=
ARTIFACT_ARGS=()

while (( $# > 0 )); do
  case "$1" in
    --candidate)
      (( $# >= 2 )) || fail "--candidate requires a value"
      [[ -z "$CANDIDATE_KEY" ]] || fail "--candidate may be supplied only once"
      CANDIDATE_KEY=$2
      shift 2
      ;;
    --source-version)
      (( $# >= 2 )) || fail "--source-version requires a value"
      [[ -z "$SOURCE_VERSION" ]] || fail "--source-version may be supplied only once"
      SOURCE_VERSION=$2
      shift 2
      ;;
    --artifact)
      (( $# >= 3 )) || fail "--artifact requires PATH and URL values"
      ARTIFACT_ARGS+=("$2" "$3")
      shift 3
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      fail "unsupported argument: $1"
      ;;
  esac
done

[[ -n "$CANDIDATE_KEY" ]] || fail "--candidate is required"
[[ -n "$SOURCE_VERSION" ]] || fail "--source-version is required"
(( ${#ARTIFACT_ARGS[@]} >= 2 )) || fail "at least one --artifact PATH URL pair is required"

if ! is_preauthorized_candidate "$CANDIDATE_KEY"; then
  fail "candidate is outside the immutable Round 3J acquisition allowlist: $CANDIDATE_KEY" 77
fi

if [[ ! -f "$REGISTER_PATH" ]]; then
  fail "Round 3J source candidate register is missing: $REGISTER_PATH" 66
fi

if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 is required for registry validation and deterministic manifests" 69
fi

DESTINATION_REL="db/data/round3j/raw/$CANDIDATE_KEY/$SOURCE_VERSION"

emit_metadata() {
  local action=$1
  local staging_dir=${2:-}

  python3 - \
    "$REGISTER_PATH" \
    "$CANDIDATE_KEY" \
    "$SOURCE_VERSION" \
    "$action" \
    "$staging_dir" \
    "$DESTINATION_REL" \
    "${ARTIFACT_ARGS[@]}" <<'PY'
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


PREAUTHORIZED_KEYS = {
    "candidate.r3j.liang-full-immersion-2024",
    "candidate.r3j.golovinsky-electrochemical-v1_1",
    "candidate.r3j.bichlmaier-mozambioside-v1",
    "candidate.r3j.guchengf-coffee-reviews-2025",
    "candidate.r3j.xian-zhang-zero-price-reviews-v2",
}
ALLOWED_ARTIFACT_HOSTS = {
    "candidate.r3j.liang-full-immersion-2024": {
        "doi.org",
        "datadryad.org",
        "www.datadryad.org",
    },
    "candidate.r3j.golovinsky-electrochemical-v1_1": {
        "doi.org",
        "zenodo.org",
        "www.zenodo.org",
    },
    "candidate.r3j.bichlmaier-mozambioside-v1": {
        "doi.org",
        "data.mendeley.com",
        "www.data.mendeley.com",
    },
    "candidate.r3j.guchengf-coffee-reviews-2025": {
        "guchengf.me",
        "www.guchengf.me",
    },
    "candidate.r3j.xian-zhang-zero-price-reviews-v2": {
        "doi.org",
        "data.mendeley.com",
        "www.data.mendeley.com",
    },
}
REQUIRED_COLUMNS = {
    "candidate_key",
    "acquisition_batch",
    "targeted_training_gap",
    "title",
    "authors_or_owner",
    "year",
    "doi_or_stable_url",
    "repository",
    "expected_contribution",
    "license_or_terms",
    "rights_state",
    "access_state",
    "decision",
    "independence_basis",
    "estimated_effective_units",
    "raw_acquisition_authorized",
    "registered_on",
    "limitation",
}
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ARTIFACT_PATH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
RESERVED_ARTIFACT_PATHS = {"ACQUISITION_MANIFEST.json", "SHA256SUMS"}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if len(sys.argv) < 9 or (len(sys.argv) - 7) % 2:
    fail("internal artifact argument contract is malformed")

register_path = Path(sys.argv[1])
candidate_key = sys.argv[2]
source_version = sys.argv[3]
action = sys.argv[4]
staging_value = sys.argv[5]
destination_rel = sys.argv[6]
artifact_values = sys.argv[7:]

if candidate_key not in PREAUTHORIZED_KEYS:
    fail(f"candidate is outside the immutable allowlist: {candidate_key}")
if not VERSION_RE.fullmatch(source_version):
    fail("source version must be an immutable path token using letters, digits, '.', '_' or '-'")
if source_version.casefold() in {"current", "head", "latest", "live", "main", "master"}:
    fail(f"mutable source version label is prohibited: {source_version}")
if action not in {"plan", "finalize"}:
    fail(f"unsupported metadata action: {action}")

with register_path.open(encoding="utf-8", newline="") as handle:
    reader = csv.DictReader(handle, delimiter="\t")
    if reader.fieldnames is None or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
        missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
        fail(f"source candidate register is missing required columns: {missing}")
    rows = list(reader)

keys = [row["candidate_key"] for row in rows]
if len(keys) != len(set(keys)):
    fail("source candidate register contains duplicate candidate keys")
authorized_keys = {
    row["candidate_key"]
    for row in rows
    if row["raw_acquisition_authorized"].strip().casefold() == "true"
}
if authorized_keys != PREAUTHORIZED_KEYS:
    fail(
        "source candidate register authorization set changed: "
        f"missing={sorted(PREAUTHORIZED_KEYS - authorized_keys)}, "
        f"unexpected={sorted(authorized_keys - PREAUTHORIZED_KEYS)}"
    )

row = next((item for item in rows if item["candidate_key"] == candidate_key), None)
if row is None:
    fail(f"candidate is not registered: {candidate_key}")
if row["raw_acquisition_authorized"].strip().casefold() != "true":
    fail(f"candidate is registered but raw acquisition is not authorized: {candidate_key}")

for column in REQUIRED_COLUMNS - {"limitation"}:
    if not row[column].strip():
        fail(f"authorized candidate has empty required metadata: {candidate_key}.{column}")

registered_url = urlsplit(row["doi_or_stable_url"])
if registered_url.scheme != "https" or not registered_url.hostname:
    fail(f"registered source URL is not immutable HTTPS metadata: {row['doi_or_stable_url']}")

artifacts: list[dict[str, str]] = []
for index in range(0, len(artifact_values), 2):
    relative_path = artifact_values[index]
    source_url = artifact_values[index + 1]
    if not ARTIFACT_PATH_RE.fullmatch(relative_path):
        fail(f"unsafe artifact path: {relative_path}")
    path = PurePosixPath(relative_path)
    raw_parts = relative_path.split("/")
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        fail(f"artifact path must remain below the immutable destination: {relative_path}")
    if relative_path in RESERVED_ARTIFACT_PATHS:
        fail(f"artifact path is reserved for acquisition metadata: {relative_path}")

    parsed_url = urlsplit(source_url)
    if parsed_url.scheme != "https" or not parsed_url.hostname:
        fail(f"artifact URL must use HTTPS: {source_url}")
    if parsed_url.username or parsed_url.password or parsed_url.fragment:
        fail(f"artifact URL must not contain credentials or a fragment: {source_url}")
    try:
        port = parsed_url.port
    except ValueError:
        fail(f"artifact URL contains an invalid port: {source_url}")
    if port not in {None, 443}:
        fail(f"artifact URL must use the default HTTPS port: {source_url}")
    if parsed_url.hostname.casefold() not in ALLOWED_ARTIFACT_HOSTS[candidate_key]:
        fail(
            f"artifact host is not authorized for {candidate_key}: "
            f"{parsed_url.hostname}"
        )
    artifacts.append({"path": relative_path, "source_url": source_url})

paths = [item["path"] for item in artifacts]
if len(paths) != len(set(paths)):
    fail("artifact paths must be unique")
if paths != sorted(paths):
    fail("artifact PATH values must be supplied in lexical order")

registry_relative_path = "db/data/round3j/source_candidate_register.tsv"
metadata = {
    "artifact_requests": artifacts,
    "candidate_key": candidate_key,
    "immutable_destination_path": destination_rel,
    "manifest_schema": "coffee-flavor-round3j-acquisition-v1",
    "overwrite_policy": "REFUSE_EXISTING_DESTINATION",
    "source_candidate_register": {
        "path": registry_relative_path,
        "sha256": sha256(register_path),
    },
    "source_candidate_register_row": row,
    "source_version": source_version,
}

if action == "plan":
    metadata["acquisition_state"] = "PLANNED_NO_NETWORK"
    print(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0)

staging_dir = Path(staging_value)
if not staging_dir.is_dir():
    fail(f"staging directory is missing: {staging_dir}")

files: list[dict[str, object]] = []
staging_resolved = staging_dir.resolve()
for artifact in artifacts:
    path = staging_dir / artifact["path"]
    if not path.is_file() or path.is_symlink():
        fail(f"downloaded artifact is missing or not a regular file: {artifact['path']}")
    if not path.resolve().is_relative_to(staging_resolved):
        fail(f"downloaded artifact escaped staging root: {artifact['path']}")
    files.append(
        {
            "byte_count": path.stat().st_size,
            "path": artifact["path"],
            "sha256": sha256(path),
            "source_url": artifact["source_url"],
        }
    )

metadata.pop("artifact_requests")
metadata["acquisition_state"] = "ACQUIRED_BYTES_HASHED_NOT_IMPORTED"
metadata["files"] = files
metadata["raw_file_hash_completeness"] = 1.0

manifest_path = staging_dir / "ACQUISITION_MANIFEST.json"
manifest_path.write_text(
    json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
manifest_sha256 = sha256(manifest_path)

checksum_lines = [f"{item['sha256']}  {item['path']}" for item in files]
checksum_lines.append(f"{manifest_sha256}  ACQUISITION_MANIFEST.json")
(staging_dir / "SHA256SUMS").write_text(
    "\n".join(sorted(checksum_lines)) + "\n",
    encoding="utf-8",
)

print(f"ACQUIRED_FILE_COUNT={len(files)}")
print("SOURCE_FILE_HASH_COMPLETENESS=1.0000")
print(f"ACQUISITION_MANIFEST_SHA256={manifest_sha256}")
PY
}

if [[ "$MODE" == plan ]]; then
  emit_metadata plan
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  fail "curl is required for fetch mode" 69
fi

# Validate every registry and request constraint before creating any raw path or
# making a network request.
emit_metadata plan >/dev/null

FINAL_DIR="$RAW_ROOT/$CANDIDATE_KEY/$SOURCE_VERSION"
FINAL_PARENT=$(dirname -- "$FINAL_DIR")
LOCK_DIR="$FINAL_PARENT/.${SOURCE_VERSION}.acquisition-lock"
STAGING_DIR=
PUBLISHED=false

cleanup() {
  local original_status=$?

  trap - EXIT INT TERM
  if [[ "$PUBLISHED" != true && -n "$STAGING_DIR" && -d "$STAGING_DIR" ]]; then
    case "$STAGING_DIR" in
      "$FINAL_PARENT"/.*.partial.*)
        rm -rf -- "$STAGING_DIR"
        ;;
      *)
        printf 'ERROR: refusing unsafe staging cleanup path: %s\n' "$STAGING_DIR" >&2
        ;;
    esac
  fi
  if [[ -d "$LOCK_DIR" ]]; then
    rmdir -- "$LOCK_DIR" 2>/dev/null || true
  fi
  exit "$original_status"
}

trap cleanup EXIT
trap 'exit 130' INT TERM

mkdir -p -- "$FINAL_PARENT"
if [[ -e "$FINAL_DIR" ]]; then
  fail "immutable acquisition destination already exists: $FINAL_DIR" 73
fi
if ! mkdir -- "$LOCK_DIR" 2>/dev/null; then
  fail "another acquisition holds the version lock: $LOCK_DIR" 73
fi
if [[ -e "$FINAL_DIR" ]]; then
  fail "immutable acquisition destination appeared while locking: $FINAL_DIR" 73
fi

STAGING_DIR=$(mktemp -d "$FINAL_PARENT/.${SOURCE_VERSION}.partial.XXXXXX")
artifact_index=0
while (( artifact_index < ${#ARTIFACT_ARGS[@]} )); do
  artifact_path=${ARTIFACT_ARGS[$artifact_index]}
  artifact_url=${ARTIFACT_ARGS[$((artifact_index + 1))]}
  output_path="$STAGING_DIR/$artifact_path"
  mkdir -p -- "$(dirname -- "$output_path")"
  printf 'FETCH candidate=%s version=%s path=%s\n' \
    "$CANDIDATE_KEY" "$SOURCE_VERSION" "$artifact_path"
  curl \
    --fail \
    --location \
    --silent \
    --show-error \
    --proto '=https' \
    --proto-redir '=https' \
    --header 'Accept-Encoding: identity' \
    --user-agent 'Coffee-Flavor-Research-Round3J/1.0' \
    --output "$output_path" \
    "$artifact_url"
  artifact_index=$((artifact_index + 2))
done

emit_metadata finalize "$STAGING_DIR"

# The version directory is published once. Existing destinations are never
# merged, replaced, or updated in place.
mv -- "$STAGING_DIR" "$FINAL_DIR"
PUBLISHED=true
rmdir -- "$LOCK_DIR"

printf 'IMMUTABLE_DESTINATION=%s\n' "$FINAL_DIR"
printf 'RAW_ACQUISITION_COMPLETE=true\n'
printf 'RAW_IMPORT_PERFORMED=false\n'
