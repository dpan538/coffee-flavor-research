#!/usr/bin/env python3
"""Validate the authoritative Round 3K governance TSV package."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "db" / "data" / "round3k"

SCHEMAS: dict[str, tuple[str, ...]] = {
    "PROFESSIONAL_CORPUS_EXPECTED_STATE.tsv": (
        "section", "state_key", "required_value", "phase_a_value", "hard_gate",
        "phase_a_pass", "evidence_basis", "note",
    ),
    "PROFESSIONAL_RECORD_CONTRACT.tsv": (
        "section", "field_key", "required_for_core", "cardinality_or_type",
        "controlled_values_or_rule", "source_rule", "note",
    ),
    "PROFESSIONAL_EVIDENCE_TIER.tsv": (
        "tier", "tier_name", "role", "counts_toward_observed_core",
        "counts_toward_model_eligible_core", "allowed_ground_truth_assertions",
        "fresh_preparation_requirement", "examples", "notes",
    ),
    "SCALE_GATE.tsv": (
        "gate_key", "metric_key", "operator", "required_value", "unit",
        "hard_gate", "condition_or_note",
    ),
    "COMPETITION_SERIES.tsv": (
        "series_key", "series_name", "organizer", "competition_level",
        "evidence_priority", "fresh_preparation_scope", "official_url",
        "verification_status", "verified_on", "limitation",
    ),
    "COMPETITION_EDITION.tsv": (
        "edition_key", "series_key", "edition_label", "year", "edition_type",
        "country_or_community", "official_url", "verification_status",
        "acquired_record_count", "note",
    ),
    "COMPETITION_CATEGORY.tsv": (
        "category_key", "series_key", "category_name", "preparation_service",
        "evidence_tier_candidate", "core_eligibility", "official_url",
        "verification_status", "note",
    ),
    "COMPETITION_ROUND.tsv": (
        "round_key", "edition_key", "round_name", "round_order", "service_type",
        "official_url", "verification_status", "note",
    ),
    "SOURCE_ACCESS_MATRIX.tsv": (
        "source_key", "series_key", "official_owner", "source_family_key",
        "source_type", "access_route", "public_results_use",
        "public_descriptor_use", "internal_research_use", "public_derived_release",
        "model_research_use", "commercial_model_use", "access_state",
        "automation_permission_state", "official_url", "verified_on", "note",
    ),
    "SCORESHEET_INVENTORY.tsv": (
        "scoresheet_key", "series_key", "year", "category", "round",
        "scoresheet_type", "official_url", "version_status", "inspected",
        "access_state", "evidence_fields", "note",
    ),
    "RESULT_ARCHIVE_INVENTORY.tsv": (
        "archive_key", "series_key", "edition_range", "archive_type", "official_url",
        "verified_item_count", "planning_estimate", "access_state", "rights_state",
        "inspected_on", "note",
    ),
    "ORGANIZER_REQUEST_MATRIX.tsv": (
        "request_key", "organizer", "series_scope", "contact_route", "requested_years",
        "requested_fields", "public_results_use", "public_descriptor_use",
        "internal_research_use", "public_derived_release", "model_research_use",
        "commercial_model_use", "preparation_status", "outbound_status",
        "official_url", "note",
    ),
    "ACQUISITION_BATCH.tsv": (
        "batch_key", "sequence", "campaign", "source_family_key", "series_key",
        "adapter_kind", "lifecycle_status", "started_on", "completed_on",
        "targeted_record_floor", "raw_records_acquired", "observed_core_delta",
        "model_eligible_delta", "descriptor_assertion_delta",
        "direct_c1_or_source_roast_delta", "new_p1_source_family",
        "new_official_series", "material_data_progress", "adapter_status",
        "evidence_path", "note",
    ),
    "ACQUISITION_OUTCOME.tsv": (
        "outcome_key", "batch_key", "campaign", "official_archive_search_complete",
        "official_items_inspected", "public_yield_pilot_complete",
        "bulk_access_route_examined", "rights_state", "access_state",
        "targeted_no_material_gain_attempt_count", "saturation_state", "stop_reason",
        "observed_core_record_count", "model_eligible_record_count", "outcome_note",
    ),
    "EFFECTIVE_RECORD_METRIC.tsv": (
        "metric_key", "metric_value", "unit", "status", "population_basis",
        "measured_on", "note",
    ),
    "SOURCE_CONCENTRATION.tsv": (
        "source_family_key", "observed_core_record_count", "model_eligible_record_count",
        "observed_share", "model_eligible_share", "independent",
        "mirror_of_source_family_key", "status", "note",
    ),
    "CATEGORY_COVERAGE.tsv": (
        "coverage_key", "preparation_taxonomy_code", "population",
        "observed_record_count", "model_eligible_record_count", "gate_7000_required",
        "gate_10000_required", "status", "note",
    ),
    "C1_COVERAGE.tsv": (
        "metric_key", "metric_value", "unit", "status", "basis", "note",
    ),
    "LABEL_DISPOSITION_METRIC.tsv": (
        "label_disposition", "professional_record_count", "expression_instance_count",
        "unique_lexical_form_count", "final_governed_count", "candidate_only_count",
        "status", "note",
    ),
    "TRAINING_READINESS_METRIC.tsv": (
        "metric_key", "metric_value", "unit", "status", "required_value",
        "gate_or_boundary", "note",
    ),
}

KEY_COLUMNS: dict[str, tuple[str, ...]] = {
    name: (columns[0],) for name, columns in SCHEMAS.items()
}
KEY_COLUMNS["PROFESSIONAL_CORPUS_EXPECTED_STATE.tsv"] = ("section", "state_key")
KEY_COLUMNS["PROFESSIONAL_RECORD_CONTRACT.tsv"] = ("section", "field_key")
KEY_COLUMNS["SCALE_GATE.tsv"] = ("gate_key", "metric_key")


def fail(message: str) -> None:
    raise AssertionError(message)


def read_table(name: str) -> list[dict[str, str]]:
    path = DATA_ROOT / name
    if not path.is_file():
        fail(f"missing authoritative artifact: {name}")
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(f"UTF-8 BOM is not allowed: {name}")
    if b"\r" in raw:
        fail(f"CR line endings are not allowed: {name}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        actual = tuple(reader.fieldnames or ())
        expected = SCHEMAS[name]
        if actual != expected:
            fail(f"header mismatch for {name}: expected {expected}, got {actual}")
        rows = list(reader)
    if not rows:
        fail(f"authoritative artifact has no rows: {name}")
    key_columns = KEY_COLUMNS[name]
    keys = [tuple(row[column] for column in key_columns) for row in rows]
    if any(not all(value) for value in keys):
        fail(f"blank primary key in {name}")
    if len(keys) != len(set(keys)):
        fail(f"duplicate primary key in {name}")
    return rows


def keyed(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row[key]: row for row in rows}


def require_zero(rows: list[dict[str, str]], *columns: str) -> None:
    for row in rows:
        for column in columns:
            if row[column] != "0":
                fail(f"expected zero {column}, got {row[column]!r}: {row}")


def main() -> int:
    actual_files = {path.name for path in DATA_ROOT.glob("*.tsv")}
    expected_files = set(SCHEMAS)
    if actual_files != expected_files:
        fail(
            "Round 3K TSV set mismatch: "
            f"missing={sorted(expected_files - actual_files)}, "
            f"unexpected={sorted(actual_files - expected_files)}"
        )

    tables = {name: read_table(name) for name in SCHEMAS}
    series = {row["series_key"] for row in tables["COMPETITION_SERIES.tsv"]}
    editions = {row["edition_key"] for row in tables["COMPETITION_EDITION.tsv"]}
    batches = {row["batch_key"] for row in tables["ACQUISITION_BATCH.tsv"]}

    for name in (
        "COMPETITION_EDITION.tsv", "COMPETITION_CATEGORY.tsv",
        "SOURCE_ACCESS_MATRIX.tsv", "SCORESHEET_INVENTORY.tsv",
        "RESULT_ARCHIVE_INVENTORY.tsv",
    ):
        for row in tables[name]:
            if row["series_key"] not in series:
                fail(f"unknown series_key in {name}: {row['series_key']}")
    for row in tables["COMPETITION_ROUND.tsv"]:
        if row["edition_key"] not in editions:
            fail(f"unknown edition_key in COMPETITION_ROUND.tsv: {row['edition_key']}")
    for row in tables["ACQUISITION_OUTCOME.tsv"]:
        if row["batch_key"] not in batches:
            fail(f"unknown batch_key in ACQUISITION_OUTCOME.tsv: {row['batch_key']}")

    expected_tiers = {f"P{index}" for index in range(6)}
    tiers = {row["tier"] for row in tables["PROFESSIONAL_EVIDENCE_TIER.tsv"]}
    if tiers != expected_tiers:
        fail(f"evidence tiers must be P0-P5, got {sorted(tiers)}")

    dispositions = {
        "EXACT_CANONICAL_TARGET", "MULTI_CANONICAL_TARGET", "RANGE_LEVEL_TARGET",
        "SOURCE_LOCAL_TARGET", "AMBIGUOUS_TARGET", "CONTRADICTORY_TARGET",
        "UNRESOLVED", "ABSTAIN", "OUTSIDE_ONTOLOGY",
    }
    actual_dispositions = {
        row["label_disposition"]
        for row in tables["LABEL_DISPOSITION_METRIC.tsv"]
    }
    if actual_dispositions != dispositions:
        fail(f"label-disposition registry mismatch: {sorted(actual_dispositions)}")

    require_zero(
        tables["COMPETITION_EDITION.tsv"], "acquired_record_count"
    )
    require_zero(
        tables["ACQUISITION_BATCH.tsv"], "raw_records_acquired",
        "observed_core_delta", "model_eligible_delta", "descriptor_assertion_delta",
        "direct_c1_or_source_roast_delta",
    )
    require_zero(
        tables["ACQUISITION_OUTCOME.tsv"], "official_items_inspected",
        "observed_core_record_count", "model_eligible_record_count",
    )
    if any(row["material_data_progress"] != "false" for row in tables["ACQUISITION_BATCH.tsv"]):
        fail("inventory-only work must not claim material data progress")
    if any(row["outbound_status"] != "NOT_SENT" for row in tables["ORGANIZER_REQUEST_MATRIX.tsv"]):
        fail("Round 3K must not claim an outbound organizer request")

    effective = keyed(tables["EFFECTIVE_RECORD_METRIC.tsv"], "metric_key")
    zero_effective_metrics = {
        "COMPETITION_SERIES_COUNT", "COMPETITION_EDITION_COUNT",
        "INDEPENDENT_PROFESSIONAL_SOURCE_FAMILY_COUNT",
        "OBSERVED_CORE_PROFESSIONAL_RECORD_COUNT",
        "MODEL_ELIGIBLE_CORE_PROFESSIONAL_RECORD_COUNT",
        "AUXILIARY_PROFESSIONAL_RECORD_COUNT", "UNIQUE_COFFEE_IDENTITY_COUNT",
        "UNIQUE_ENTRY_SERVICE_COUNT", "EFFECTIVE_ROUND_SERVICE_RECORD_COUNT",
        "P1_RECORD_COUNT", "P2_RECORD_COUNT", "P3_RECORD_COUNT", "P4_RECORD_COUNT",
        "JUDGE_OBSERVATION_COUNT", "PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT",
        "STRUCTURED_SCORE_COUNT", "P1_P2_DESCRIPTOR_COASSERTION_EVENT_COUNT",
    }
    if not zero_effective_metrics.issubset(effective):
        fail("effective-record metric registry is incomplete")
    for metric in zero_effective_metrics:
        if effective[metric]["metric_value"] != "0":
            fail(f"unadmitted corpus metric must remain zero: {metric}")

    readiness = keyed(tables["TRAINING_READINESS_METRIC.tsv"], "metric_key")
    required_boundaries = {
        "EXPERT_REVIEW_PERFORMED": "false", "ML_BASELINE_RUN": "false",
        "RANKING_MODEL_TRAINED": "false", "ADAPTIVE_POLICY_TRAINED": "false",
        "DEEP_LEARNING_MODEL_RUN": "false", "EMBEDDING_BASELINE_RUN": "false",
        "CROSS_ENCODER_RUN": "false", "PGVECTOR_REQUIRED": "false",
        "MODEL_WEIGHT_FILE_COUNT": "0", "OUTBOUND_DATA_REQUEST_COUNT": "0",
        "COMMERCIAL_PURCHASE_COUNT": "0", "CONTRACT_ACCEPTANCE_COUNT": "0",
        "GATE_1000_PASS": "false", "GATE_3000_PASS": "false",
        "GATE_7000_PASS": "false", "GATE_10000_PASS": "false",
        "GATE_12000_FORENSIC_AUDIT_REQUIRED": "false",
        "GATE_12000_FORENSIC_AUDIT_PASS": "false",
    }
    for metric, expected in required_boundaries.items():
        if metric not in readiness or readiness[metric]["metric_value"] != expected:
            fail(f"boundary mismatch for {metric}: expected {expected}")

    print(f"ROUND3K_AUTHORITATIVE_TSV_COUNT={len(tables)}")
    print(f"ROUND3K_COMPETITION_PLANNING_SERIES_COUNT={len(series)}")
    print(f"ROUND3K_COMPETITION_PLANNING_EDITION_COUNT={len(editions)}")
    print("ROUND3K_GOVERNANCE_ARTIFACT_CONTRACT_PASS=true")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as error:
        print(f"ROUND3K_GOVERNANCE_ARTIFACT_CONTRACT_PASS=false: {error}", file=sys.stderr)
        raise SystemExit(1) from error
