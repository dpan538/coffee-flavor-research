#!/usr/bin/env python3
"""Verify committed Round 3I research-database freeze artifacts offline."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FREEZE_DIR = ROOT / "db" / "data" / "freeze" / "coffee-sensory-research-db-v0"
MANIFEST_PATH = FREEZE_DIR / "FREEZE_MANIFEST.json"
MIGRATION_PATH = ROOT / "db" / "048_round3i_research_database_freeze_seed.sql"
EXPECTED_STATE_COMMIT_SHA = "602624143fef8fa4250e5e84f07478101b0846ff"
SOURCE_SHA = "ccf5769cb5e1f165209e59beaef9fe54017265f5"
EXPECTED_FILES = {
    "CANONICAL_INVENTORY.tsv",
    "SOURCE_INVENTORY.tsv",
    "RAW_FILE_MANIFEST.tsv",
    "SENSORY_INVENTORY.tsv",
    "CONTEXT_COVERAGE.tsv",
    "LANGUAGE_CORPUS.tsv",
    "RELATIONSHIP_EVIDENCE.tsv",
    "QUESTION_EVIDENCE.tsv",
    "FEATURE_REGISTRY.tsv",
    "SOURCE_PARTITION.tsv",
    "FREEZE_MANIFEST.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(message)


if not FREEZE_DIR.is_dir():
    fail("Round 3I freeze directory is missing")

actual_files = {path.name for path in FREEZE_DIR.iterdir() if path.is_file()}
if actual_files != EXPECTED_FILES:
    fail(
        "Round 3I freeze file inventory changed: "
        f"missing={sorted(EXPECTED_FILES - actual_files)}, "
        f"extra={sorted(actual_files - EXPECTED_FILES)}"
    )

with MANIFEST_PATH.open(encoding="utf-8") as handle:
    manifest = json.load(handle)

manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
if re.search(r'"manifest_sha256"\s*:', manifest_text):
    fail("FREEZE_MANIFEST.json must not contain its own SHA-256")
if manifest.get("expected_state_commit_sha") != EXPECTED_STATE_COMMIT_SHA:
    fail("Round 3I expected-state implementation checkpoint changed")
if manifest.get("implementation_expected_state_checkpoint_sha") != EXPECTED_STATE_COMMIT_SHA:
    fail("Round 3I implementation expected-state checkpoint changed")
if manifest.get("repository_sha") != SOURCE_SHA:
    fail("Round 3I verified starting SOURCE_SHA changed")
if manifest.get("repository_sha_role") != "VERIFIED_STARTING_SOURCE_SHA":
    fail("Round 3I repository SHA role is ambiguous")
if (
    manifest.get("final_repository_sha_binding")
    != "POST_COMMIT_ATTESTATION_REQUIRED_NON_SELF_REFERENTIAL"
):
    fail("Round 3I final repository SHA binding semantics changed")
if manifest.get("migration_count") != 49:
    fail("Round 3I migration count changed")
if manifest.get("freeze_version") != "coffee-sensory-research-db-v0.1.0":
    fail("Round 3I freeze version changed")
if manifest.get("release_tag") != "coffee-sensory-research-db-v0.1.0":
    fail("Round 3I release tag changed")

inventories = manifest.get("inventory_hashes")
if not isinstance(inventories, list) or len(inventories) != 10:
    fail("FREEZE_MANIFEST.json must list exactly ten inventory hashes")

manifest_paths: set[str] = set()
artifact_types: set[str] = set()
for item in inventories:
    relative_path = item.get("path")
    digest = item.get("sha256")
    artifact_type = item.get("artifact_type")
    if not isinstance(relative_path, str) or relative_path in manifest_paths:
        fail(f"duplicate or invalid manifest inventory path: {relative_path}")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        fail(f"invalid inventory digest: {relative_path}")
    if not isinstance(artifact_type, str) or artifact_type in artifact_types:
        fail(f"duplicate or invalid artifact type: {artifact_type}")
    path = ROOT / relative_path
    if not path.is_file() or path.parent != FREEZE_DIR:
        fail(f"manifest inventory path does not resolve inside freeze dir: {relative_path}")
    if sha256(path) != digest:
        fail(f"manifest inventory SHA-256 mismatch: {relative_path}")
    with path.open(encoding="utf-8", newline="") as handle:
        actual_row_count = sum(1 for _ in csv.DictReader(handle, delimiter="\t"))
    if actual_row_count != item.get("row_count"):
        fail(f"manifest row count mismatch: {relative_path}")
    manifest_paths.add(relative_path)
    artifact_types.add(artifact_type)

expected_inventory_paths = {
    "db/data/freeze/coffee-sensory-research-db-v0/" + filename
    for filename in EXPECTED_FILES
    if filename != "FREEZE_MANIFEST.json"
}
if manifest_paths != expected_inventory_paths:
    fail("manifest inventory path set changed")

required_manifest_sections = {
    "canonical_inventory",
    "source_inventory",
    "source_family_inventory",
    "file_inventory",
    "file_hashes",
    "row_inventories",
    "sensory_inventory",
    "context_inventory",
    "language_inventory",
    "relationship_inventory",
    "question_inventory",
    "feature_definitions",
    "source_partitions",
    "current_approved_views",
    "deprecated_research_views",
    "rights_states",
    "privacy_states",
    "known_gaps",
    "known_exclusions",
}
if not required_manifest_sections <= set(manifest):
    fail(
        "Round 3I manifest sections missing: "
        f"{sorted(required_manifest_sections - set(manifest))}"
    )
if len(manifest["current_approved_views"]) != 8:
    fail("Round 3I approved current-view inventory changed")
if len(manifest["deprecated_research_views"]) != 8:
    fail("Round 3I deprecated research-view inventory changed")
if not manifest["known_gaps"] or not manifest["known_exclusions"]:
    fail("Round 3I known gaps/exclusions must be explicit")

coverage = manifest.get("coverage_inventory", {})
expected_coverage = {
    "canonical_concept_count": 130,
    "active_sensory_attribute_count": 92,
    "current_canonical_view_row_count": 193,
    "current_canonical_view_distinct_concept_count": 114,
    "coffee_sensory_source_family_count": 9,
    "source_local_sensory_observation_row_count": 4344,
    "source_local_sensory_sample_count": 230,
    "empirical_coverage_cell_count": 181,
    "contemporary_language_source_family_count": 3,
    "new_contemporary_document_count": 3289,
    "governed_unique_expression_count": 2996,
    "zh_hans_source_family_count": 2,
    "zh_hans_sensory_expression_count": 249,
    "relationship_evidence_claim_count": 97,
    "source_local_supported_membership_count": 6,
    "cross_source_supported_membership_count": 4,
    "range_with_source_local_evidence_count": 6,
    "range_with_cross_source_evidence_count": 4,
    "question_target_with_independent_research_support_count": 12,
    "model_prebuild_feature_count": 20,
    "source_partition_count": 12,
    "approved_current_surface_count": 8,
    "deprecated_research_surface_count": 8,
}
for key, expected in expected_coverage.items():
    if coverage.get(key) != expected:
        fail(f"Round 3I freeze coverage changed: {key}")

rights_states = manifest.get("rights_states", {})
expected_rights_states = {
    "source_rights_raw_redistribution_allow_count": 6,
    "source_rights_raw_redistribution_deny_count": 0,
    "source_rights_derived_expression_release_allow_count": 6,
    "language_document_public_export_state_counts": {
        "PUBLIC_DERIVED_ONLY": 4129,
        "PUBLIC_RAW": 8,
    },
}
for key, expected in expected_rights_states.items():
    if rights_states.get(key) != expected:
        fail(f"Round 3I freeze rights-state inventory changed: {key}")

if (
    manifest.get("research_database_freeze_state") != "READY_TO_FREEZE"
    or manifest.get("model_prebuild_data_ready") is not True
    or manifest.get("contains_model_weights") is not False
    or manifest.get("contains_embeddings") is not False
    or manifest.get("training_or_evaluation_executed") is not False
):
    fail("Round 3I freeze/readiness or prohibited-execution boundary changed")

migration_text = MIGRATION_PATH.read_text(encoding="utf-8")
registered_digests = {item["sha256"] for item in inventories}
registered_digests.add(sha256(MANIFEST_PATH))
for digest in registered_digests:
    if digest not in migration_text:
        fail(f"migration 048 does not register artifact SHA-256: {digest}")
if EXPECTED_STATE_COMMIT_SHA not in migration_text:
    fail("migration 048 does not bind the expected-state checkpoint")
if SOURCE_SHA not in migration_text:
    fail("migration 048 does not bind the verified starting SOURCE_SHA")

print("ROUND3I_FREEZE_ARTIFACT_CONTRACT_PASS=true")
print("ROUND3I_FREEZE_NON_SELF_REFERENTIAL_MANIFEST_PASS=true")
print("ROUND3I_FREEZE_ARTIFACT_COUNT=11")
print(f"ROUND3I_FREEZE_MANIFEST_SHA256={sha256(MANIFEST_PATH)}")
