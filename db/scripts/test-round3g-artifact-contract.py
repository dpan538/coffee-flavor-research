#!/usr/bin/env python3
"""Verify committed Round 3G evidence artifacts without network access."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "round3g"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


expected_counts = {
    "source_families.tsv": 2,
    "source_candidate_register.tsv": 6,
    "source_files.tsv": 4,
    "relationship_evidence_claims.tsv": 20,
    "membership_reviews.tsv": 18,
    "question_target_reviews.tsv": 18,
    "range_reviews.tsv": 7,
}

for filename, expected_count in expected_counts.items():
    actual_count = len(rows(DATA / filename))
    if actual_count != expected_count:
        raise SystemExit(
            f"{filename}: expected {expected_count} records, found {actual_count}"
        )

inventory = rows(DATA / "source_files.tsv")
for item in inventory:
    if item["declared_sha256"] != item["verified_sha256"]:
        raise SystemExit(f"{item['file_key']}: declared and verified hashes differ")
    if item["hash_verified"] != "true":
        raise SystemExit(f"{item['file_key']}: hash is not marked verified")
    if item["local_path"] == "EXTERNAL_ONLY":
        if item["public_export_decision"] != "EXTERNAL_ONLY":
            raise SystemExit(f"{item['file_key']}: external file export mismatch")
        continue
    local_path = ROOT / item["local_path"]
    if not local_path.is_file():
        raise SystemExit(f"{item['file_key']}: missing local artifact {local_path}")
    if sha256(local_path) != item["verified_sha256"]:
        raise SystemExit(f"{item['file_key']}: local SHA-256 mismatch")
    if local_path.stat().st_size != int(item["file_size_bytes"]):
        raise SystemExit(f"{item['file_key']}: local file size mismatch")

with (DATA / "enwiktionary_revision_metadata.json").open(encoding="utf-8") as handle:
    en_pages = json.load(handle)["query"]["pages"]
with (DATA / "zhwiktionary_revision_metadata.json").open(encoding="utf-8") as handle:
    zh_pages = json.load(handle)["query"]["pages"]

if len(en_pages) != 6 or len(zh_pages) != 9:
    raise SystemExit("Wiktionary revision-set cardinality changed")

expected_state = rows(DATA / "expected_state.tsv")
sections = {item["section"] for item in expected_state}
if sections != {
    "BASELINE",
    "MINIMUM_EXPECTED",
    "PREFERRED_EXPECTED",
    "OBSERVED",
    "DELTA",
}:
    raise SystemExit(f"expected-state sections changed: {sorted(sections)}")

claims = rows(DATA / "relationship_evidence_claims.tsv")
direction_counts = {
    direction: sum(item["evidence_direction"] == direction for item in claims)
    for direction in ("SUPPORTS", "CHALLENGES", "MIXED", "INSUFFICIENT")
}
if direction_counts != {
    "SUPPORTS": 1,
    "CHALLENGES": 3,
    "MIXED": 1,
    "INSUFFICIENT": 15,
}:
    raise SystemExit(f"evidence direction inventory changed: {direction_counts}")

print("ROUND3G_ARTIFACT_CONTRACT_PASS=true")
print("ROUND3G_LOCAL_ARTIFACT_HASH_PASS=true")
print("EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0")
