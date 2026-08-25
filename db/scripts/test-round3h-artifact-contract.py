#!/usr/bin/env python3
"""Verify committed Round 3H prebuild artifacts without network access."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "round3h"
MANIFEST_PATH = (
    ROOT / "db" / "data" / "model-prebuild" / "v0" / "MODEL_PREBUILD_MANIFEST.json"
)


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
    DATA / "source_candidate_register.tsv": 36,
    DATA / "model_prebuild_expected_state.tsv": 95,
    DATA / "batch1" / "iswaldi_2026_table3_sensory_aggregates.tsv": 72,
    DATA / "batch1" / "vezzulli_2022_table2_sensory_medians.tsv": 160,
    DATA / "batch1" / "bollen_2024_sensory_scores.tsv": 95,
    DATA / "batch2" / "gorman_2021_liking_aggregates.tsv": 48,
    DATA / "batch2" / "gorman_2021_cata_terms.tsv": 26,
    DATA / "batch2" / "nguyen_2026_table3_sensory_intensities.tsv": 260,
    DATA / "batch2" / "nguyen_2026_table4_consumer_outcomes.tsv": 20,
    DATA / "batch3" / "contemporary_language_decisions.tsv": 6,
    DATA / "batch4" / "zh_hans_language_decisions.tsv": 8,
    DATA / "batch5" / "instrument_constructs.tsv": 43,
    DATA / "batch5" / "membership_promotions.tsv": 10,
    DATA / "batch5" / "question_research_evidence.tsv": 12,
    DATA / "batch5" / "relationship_evidence_claims.tsv": 76,
}

for path, expected_count in expected_counts.items():
    actual_count = len(rows(path))
    if actual_count != expected_count:
        raise SystemExit(
            f"{path.relative_to(ROOT)}: expected {expected_count} records, "
            f"found {actual_count}"
        )

expected_state = rows(DATA / "model_prebuild_expected_state.tsv")
expected_sections = {
    "BASELINE",
    "MINIMUM_MODEL_PREBUILD_STATE",
    "PREFERRED_MODEL_PREBUILD_STATE",
    "OBSERVED",
    "DELTA",
    "READINESS_DECISION",
}
if {item["section"] for item in expected_state} != expected_sections:
    raise SystemExit("Round 3H expected-state sections changed")

threshold_rows = {
    item["readiness_key"]: item
    for item in expected_state
    if item["section"] == "MINIMUM_MODEL_PREBUILD_STATE"
}
frozen_thresholds = {
    "sensory.source_family_count": "5",
    "sensory.method_family_count": "3",
    "context.preparation_sensory_coverage": "3",
    "context.roast_sensory_coverage": "4",
    "context.crossed_cell_count": "12",
    "context.empirical_coverage_cell_count": "120",
    "language.contemporary_source_family_count": "3",
    "language.new_contemporary_document_count": "500",
    "language.unique_expression_count": "2500",
    "language.zh_hans_source_family_count": "2",
    "relationship.evidence_claim_count": "80",
    "relationship.source_local_membership_count": "6",
    "relationship.cross_source_membership_count": "3",
    "question.independent_research_target_count": "6",
}
for key, expected_minimum in frozen_thresholds.items():
    if threshold_rows.get(key, {}).get("minimum_required") != expected_minimum:
        raise SystemExit(f"frozen threshold changed: {key}")

claims = rows(DATA / "batch5" / "relationship_evidence_claims.tsv")
direction_counts = Counter(item["evidence_direction"] for item in claims)
if direction_counts != {
    "SUPPORTS": 46,
    "CHALLENGES": 15,
    "MIXED": 13,
    "INSUFFICIENT": 2,
}:
    raise SystemExit(f"Round 3H claim directions changed: {direction_counts}")

promotions = rows(DATA / "batch5" / "membership_promotions.tsv")
promotion_counts = Counter(item["new_lifecycle"] for item in promotions)
if promotion_counts != {"SOURCE_LOCAL_SUPPORTED": 6, "CROSS_SOURCE_SUPPORTED": 4}:
    raise SystemExit(f"Round 3H promotion inventory changed: {promotion_counts}")

questions = rows(DATA / "batch5" / "question_research_evidence.tsv")
if any(
    item["user_validation_status"] != "NOT_USER_VALIDATED"
    or item["information_gain_status"] != "NOT_ESTIMABLE"
    for item in questions
):
    raise SystemExit("Round 3H question nonvalidation boundary changed")

contemporary = rows(DATA / "batch3" / "contemporary_language_decisions.tsv")
zh_hans = rows(DATA / "batch4" / "zh_hans_language_decisions.tsv")
if any(
    int(item["countable_family_gain"]) != 0
    or int(item["countable_document_gain"]) != 0
    for item in contemporary
):
    raise SystemExit("Round 3H contemporary-language no-gain result changed")
if any(
    int(item["countable_family_gain"]) != 0
    or int(item["countable_sensory_expression_gain"]) != 0
    for item in zh_hans
):
    raise SystemExit("Round 3H zh-Hans no-gain result changed")

with (DATA / "batch3" / "batch3_result.json").open(encoding="utf-8") as handle:
    batch3 = json.load(handle)
with (DATA / "batch4" / "batch4_result.json").open(encoding="utf-8") as handle:
    batch4 = json.load(handle)
with (DATA / "batch5" / "batch5_result.json").open(encoding="utf-8") as handle:
    batch5 = json.load(handle)

if batch3["meaningful_coverage_gain"] is not False:
    raise SystemExit("Round 3H first targeted no-gain batch changed")
if (
    batch4["stopping_rule_triggered"] is not True
    or batch4["acquisition_stop_status"]
    != "STOP_TWO_CONSECUTIVE_TARGETED_NO_GAIN_BATCHES"
):
    raise SystemExit("Round 3H acquisition stop rule changed")
if (
    batch5["total_relationship_evidence_claim_count"] != 96
    or batch5["source_local_supported_membership_count_after"] != 6
    or batch5["cross_source_supported_membership_count_after"] != 4
    or batch5["question_target_with_independent_research_support_count"] != 12
):
    raise SystemExit("Round 3H relationship closure result changed")

with MANIFEST_PATH.open(encoding="utf-8") as handle:
    manifest = json.load(handle)

if sha256(MANIFEST_PATH) != "254f7b2aa1fb697372dd896a3631ff31c5b663cd9b79e3c24ba737716fe1b8ad":
    raise SystemExit("model-prebuild manifest SHA-256 changed")
if len(manifest["source_partitions"]) != 12:
    raise SystemExit("model-prebuild source partition count changed")
if len(manifest["feature_registry"]) != 20:
    raise SystemExit("model-prebuild feature count changed")
if len(manifest["file_hashes"]) != 10:
    raise SystemExit("model-prebuild file inventory count changed")
if (
    manifest["contains_model_weights"] is not False
    or manifest["contains_embeddings"] is not False
    or manifest["training_or_evaluation_executed"] is not False
    or manifest["model_use_status"] != "PREBUILD_ONLY"
    or manifest["model_prebuild_data_ready"] is not False
    or manifest["model_prebuild_readiness_state"]
    != "COMPLETE_WITH_DATA_COVERAGE_GAP"
):
    raise SystemExit("model-prebuild execution or readiness boundary changed")

file_paths = {
    "file.iswaldi.table3-derived": DATA / "batch1" / "iswaldi_2026_table3_sensory_aggregates.tsv",
    "file.vezzulli.table2-derived": DATA / "batch1" / "vezzulli_2022_table2_sensory_medians.tsv",
    "file.bollen.sensory-derived": DATA / "batch1" / "bollen_2024_sensory_scores.tsv",
    "file.gorman.liking-derived": DATA / "batch2" / "gorman_2021_liking_aggregates.tsv",
    "file.gorman.cata-derived": DATA / "batch2" / "gorman_2021_cata_terms.tsv",
    "file.nguyen.sensory-derived": DATA / "batch2" / "nguyen_2026_table3_sensory_intensities.tsv",
    "file.nguyen.consumer-derived": DATA / "batch2" / "nguyen_2026_table4_consumer_outcomes.tsv",
    "file.condelli.constructs-derived": DATA / "batch5" / "instrument_constructs.tsv",
    "file.heo.constructs-derived": DATA / "batch5" / "instrument_constructs.tsv",
    "file.coffee-cuality.constructs-derived": DATA / "batch5" / "instrument_constructs.tsv",
}
for item in manifest["file_hashes"]:
    file_key = item["file_key"]
    path = file_paths.get(file_key)
    if path is None or not path.is_file():
        raise SystemExit(f"manifest file path unresolved: {file_key}")
    if sha256(path) != item["sha256"]:
        raise SystemExit(f"manifest file SHA-256 mismatch: {file_key}")

coverage = manifest["coverage_inventory"]
expected_coverage = {
    "coffee_sensory_source_family_count": 9,
    "source_local_sensory_observation_row_count": 4344,
    "source_local_sensory_sample_count": 230,
    "source_local_participant_or_panel_count": 520,
    "empirical_coverage_cell_count": 181,
    "relationship_evidence_claim_count": 96,
    "source_local_supported_membership_count": 6,
    "cross_source_supported_membership_count": 4,
    "question_target_with_independent_research_support_count": 12,
}
for key, expected_value in expected_coverage.items():
    if coverage.get(key) != expected_value:
        raise SystemExit(f"manifest coverage changed: {key}")

print("ROUND3H_ARTIFACT_CONTRACT_PASS=true")
print("ROUND3H_SOURCE_HASH_VERIFICATION_PASS=true")
print("EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0")
print("MODEL_PREBUILD_MANIFEST_METADATA_ONLY=true")
