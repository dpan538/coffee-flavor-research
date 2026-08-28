#!/usr/bin/env python3
"""Build the public-safe Round 3M disposition package for Round 3L's 376 candidates.

The Round 3L restricted checkpoint contains 376 ``OFFICIAL_AGGREGATED_DESCRIPTOR``
rows extracted from AVPA palmares tables.  Round 3M inspected the five governed
source PDFs and established that the extracted value is a result-table category
classification, not a filled coffee-specific sensory observation.  Category
names are ``NON_DESCRIPTOR`` under the Round 3M contract.

This builder is deliberately fail-closed and text-free.  It validates the pinned
Round 3L checkpoint, joins every candidate to its record and acquisition attempt,
verifies the five source files by SHA-256, and emits exactly one provisional
``NON_DESCRIPTOR`` disposition for every candidate.  It never publishes source
text, source-defined category values, participant/product fields, or scores.  It
does not claim human or expert review.

The descriptor-first report is methodological evidence only.  Its machine-
readable companion bundle is required to import the report's 305/303/302 audit
surfaces; when that bundle is absent this builder records an explicit blocker and
does not reconstruct rows from the PDF.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "db" / "data" / "round3m"

ROUND3L_CHECKPOINT_SHA256 = (
    "c054e364e5193558c752ce03ff5ec002b807343e00743e7af94676e17cf39e7e"
)
DESCRIPTOR_FIRST_REPORT_SHA256 = (
    "d319236311f2abc5e15baaf70923b32e0a2bdbb5dc010723feea3e4aec8069e0"
)
CHECKPOINT_AT = "2026-08-28T04:00:00Z"
DECISION_EFFECTIVE_DATE = "2026-08-28"
REVIEW_PROTOCOL_VERSION = "round3m-descriptor-review-v1"
GENERATOR_VERSION = "round3m-review-artifact-builder-v1"
EXPECTED_CAPTURE_MANIFEST_SHA256 = (
    "b36fbe8a959b099b1a3a073b045c3d6ac74e31043f090d2fd88bd78c3290e51d"
)
EXPECTED_CAPTURE_ROOT_LOCATOR = (
    "restricted://coffee-flavor-round3m/round3m-2026-08-28t043000z"
)

EXPECTED_CANDIDATE_COUNT = 376
EXPECTED_CANDIDATE_COUNTS_BY_YEAR = {
    "2021": 69,
    "2022": 50,
    "2023": 88,
    "2024": 87,
    "2025": 82,
}
EXPECTED_SOURCE_FILE_COUNT = 5
EXPECTED_SOURCE_DEFINED_VALUE_COUNT = 20

EXPECTED_FRESH_PREPARATION_STATUS = {
    "CONFIRMED": 13_157,
    "NOT_APPLICABLE": 273,
    "PENDING": 13_085,
}
EXPECTED_C0_SOURCE_STATUS = {
    "NOT_APPLICABLE": 273,
    "NOT_REPORTED": 22_071,
    "REPORTED": 495,
    "REPORTED_UNRESOLVED": 39,
    "SOURCE_UNKNOWN": 3_637,
}
EXPECTED_C1_EVIDENCE_STATUS = {
    "NOT_APPLICABLE": 270,
    "NOT_REPORTED": 14_388,
    "REPORTED_UNRESOLVED": 7_683,
    "SOURCE_UNKNOWN": 4_174,
}
EXPECTED_DIRECT_ROAST_EVIDENCE_COUNT = 7_683

MACHINE_RESEARCH_ARTIFACTS = (
    "OPEN_DESCRIPTOR_SOURCE_CENSUS.tsv",
    "DESCRIPTOR_YIELD_AUDIT.tsv",
    "DESCRIPTOR_COUNT_RECEIPT.json",
    "DESCRIPTOR_PROVENANCE_MATRIX.tsv",
    "OPEN_DESCRIPTOR_CEILING.md",
    "DESCRIPTOR_TRAINING_GATES.md",
    "SOURCE_PRIORITY_BY_DESCRIPTOR_YIELD.tsv",
    "LOW_YIELD_AND_FALSE_SCALE_REGISTER.tsv",
    "CODEX_RESUMPTION_DECISION.md",
)

RIGHTS_DIMENSIONS = (
    ("PUBLIC_DISCOVERY", "public_results_use"),
    ("INTERNAL_RESEARCH_ANALYSIS", "internal_research_use"),
    ("DERIVED_RESEARCH_DATA", "public_derived_release"),
    ("MODEL_RESEARCH", "model_research_use"),
    ("DEPLOYMENT_OR_COMMERCIAL_MODEL", "commercial_model_use"),
    ("RAW_REDISTRIBUTION", "public_descriptor_use"),
)
RIGHTS_STATES = {"AFFIRMATIVE", "PENDING", "UNKNOWN", "PROHIBITED", "NOT_APPLICABLE"}

LIVE_ASSERTION_EXPORT_COLUMNS = (
    "descriptor_assertion_id",
    "effective_record_id",
    "source_artifact_id",
    "source_route_id",
    "schema_signature_id",
    "publication_layer",
    "source_field_label",
    "source_selector_or_locator",
    "source_page_or_record_locator",
    "raw_field_text_sha256",
    "atomic_source_text_sha256",
    "source_language",
    "descriptor_class",
    "evidence_tier",
    "evidence_origin_type",
    "origin_decision_basis",
    "review_state",
    "review_actor_type",
    "rights_state",
    "within_record_repeat_group",
    "cross_observation_repeat_group",
    "count_disposition",
    "frequency_value",
    "source_retrieved_at",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
    "parser_version",
    "adapter_version",
    "model_eligible",
)

ASSERTION_COLUMNS = (
    "professional_acquisition_assertion_key",
    "professional_acquisition_record_key",
    "assertion_type",
    "source_locator",
    "source_language_code",
    "source_defined_descriptor_key",
    "assertion_text",
    "assertion_text_sha256",
    "text_storage_state",
    "semantic_inference_used",
    "created_at",
)

RECORD_COLUMNS = (
    "professional_acquisition_record_key",
    "attempt_key",
    "source_record_key",
    "source_family_key",
    "series_key",
    "edition_key",
    "edition_year",
    "category_key",
    "round_key",
    "entry_or_lot_key",
    "coffee_identity_key",
    "preparation_service_code",
    "effective_record_key",
    "evidence_tier",
    "payload_kind",
    "official_score_value",
    "official_score_text",
    "official_score_scale",
    "fresh_preparation_status",
    "fresh_preparation_evidence_locator",
    "c0_source_status",
    "c0_family",
    "source_native_roast_value",
    "source_native_roast_scheme",
    "c1_evidence_status",
    "reviewed_c1_mapping",
    "source_snapshot_sha256",
    "raw_record_sha256",
    "public_results_use",
    "public_descriptor_use",
    "internal_research_use",
    "public_derived_release",
    "model_research_use",
    "commercial_model_use",
    "deduplication_disposition",
    "canonical_record_key",
    "duplicate_group_key",
    "mirror_group_key",
    "repeat_group_key",
    "corpus_state",
    "label_review_status",
    "is_synthetic",
    "semantic_inference_used",
    "ingested_at",
    "reviewed_at",
    "model_eligible_at",
)

ATTEMPT_COLUMNS = (
    "attempt_key",
    "census_item_key",
    "lane_key",
    "attempt_sequence",
    "attempted_at",
    "acquisition_method",
    "outcome",
    "canonical_url",
    "final_url",
    "http_status",
    "source_snapshot_sha256",
    "artifact_byte_count",
    "parsed_row_count",
    "normalized_record_count",
    "descriptor_assertion_count",
    "external_action_type",
    "blocker_detail",
    "next_cursor",
    "evidence_json",
)

QUEUE_COLUMNS = (
    "review_queue_id",
    "descriptor_assertion_id",
    "professional_record_id",
    "source_family_id",
    "source_route_id",
    "edition_id",
    "edition_year",
    "source_artifact_id",
    "source_file_sha256",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
    "raw_record_sha256",
    "source_locator",
    "source_language",
    "source_text_sha256",
    "source_text_storage_state",
    "source_text_non_storage_reason",
    "source_field_contract",
    "publication_layer",
    "descriptor_class",
    "evidence_tier",
    "review_state",
    "review_actor_type",
    "current_disposition",
    "disposition_reason_code",
    "human_review_required",
    "model_eligible",
    "decision_effective_date",
)

DECISION_COLUMNS = (
    "decision_id",
    "review_queue_id",
    "descriptor_assertion_id",
    "current_disposition",
    "descriptor_class",
    "review_state",
    "review_actor_type",
    "review_protocol_version",
    "decision_reason_code",
    "decision_basis",
    "evidence_locator",
    "source_file_sha256",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
    "source_text_sha256",
    "human_confirmed",
    "expert_adjudicated",
    "counts_as_reviewed_descriptor",
    "model_eligible",
    "decision_effective_date",
)

PROVENANCE_COLUMNS = (
    "provenance_decision_id",
    "descriptor_assertion_id",
    "source_route_id",
    "source_artifact_id",
    "source_file_sha256",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
    "source_locator",
    "source_field_contract",
    "publication_layer",
    "evidence_origin_type",
    "origin_decision_basis",
    "origin_evidence_locator",
    "descriptor_class",
    "evidence_tier",
    "review_state",
    "review_actor_type",
    "provenance_complete",
)

RIGHTS_COLUMNS = (
    "rights_decision_id",
    "descriptor_assertion_id",
    "source_artifact_id",
    "purpose",
    "rights_state",
    "decision_basis",
    "rights_evidence_locator",
    "review_actor_type",
    "model_eligibility_effect",
)

PUBLICATION_LAYER_COLUMNS = (
    "publication_layer_relation_id",
    "descriptor_assertion_id",
    "professional_record_id",
    "publication_layer",
    "related_assertion_id",
    "relation_type",
    "decision_basis",
    "source_locator",
    "source_file_sha256",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
)

DUPLICATE_COLUMNS = (
    "duplicate_decision_id",
    "descriptor_assertion_id",
    "professional_record_id",
    "deduplication_disposition",
    "within_record_repeat_group",
    "cross_observation_repeat_group",
    "mirror_group",
    "decision_basis",
    "counts_as_assertion",
    "counts_as_record_unique_descriptor",
)

NORMALIZATION_COLUMNS = (
    "normalization_decision_id",
    "descriptor_assertion_id",
    "source_native_text_sha256",
    "source_native_text_storage_state",
    "normalized_candidate_form",
    "normalization_operation",
    "decision_basis",
    "source_native_lexical_form_count_effect",
    "normalized_form_count_effect",
)

COASSERTION_COLUMNS = (
    "coassertion_event_id",
    "effective_record_id",
    "left_descriptor_assertion_id",
    "right_descriptor_assertion_id",
    "left_normalized_form",
    "right_normalized_form",
    "left_normalized_form_sha256",
    "right_normalized_form_sha256",
    "left_atomic_source_text_sha256",
    "right_atomic_source_text_sha256",
    "evidence_tier",
    "publication_layer",
    "pair_support_event_count",
    "source_file_sha256",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
)

LEDGER_COLUMNS = (
    "descriptor_assertion_id",
    "effective_record_id",
    "source_artifact_id",
    "source_route_id",
    "schema_signature_id",
    "publication_layer",
    "source_field_label",
    "source_field_label_sha256",
    "source_selector_or_locator",
    "source_page_or_record_locator",
    "raw_field_text",
    "raw_field_text_sha256",
    "atomic_source_text",
    "atomic_source_text_sha256",
    "source_language",
    "descriptor_class",
    "source_native_lexical_form",
    "source_native_lexical_form_sha256",
    "normalized_candidate_form",
    "normalized_candidate_form_sha256",
    "evidence_tier",
    "evidence_origin_type",
    "origin_decision_basis",
    "origin_evidence_locator",
    "review_state",
    "review_actor_type",
    "review_receipt_id",
    "rights_decision_id",
    "within_record_repeat_group",
    "cross_observation_repeat_group",
    "mirror_group",
    "created_at",
    "source_retrieved_at",
    "source_file_sha256",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
    "parser_version",
    "adapter_version",
    "source_text_storage_state",
    "source_text_non_storage_reason",
    "counts_as_reviewed_descriptor",
    "model_eligible",
)

HUMAN_TEMPLATE_COLUMNS = (
    "review_queue_id",
    "descriptor_assertion_id",
    "source_locator",
    "source_file_sha256",
    "source_text_sha256",
    "machine_disposition",
    "reviewer_id_or_pseudonymous_code",
    "reviewer_role",
    "review_actor_type",
    "review_protocol_version",
    "decision",
    "decision_reason",
    "evidence_locator",
    "reviewed_at",
    "adjudication_status",
    "previous_decision",
)

ADJUDICATION_TEMPLATE_COLUMNS = (
    "review_queue_id",
    "descriptor_assertion_id",
    "source_locator",
    "source_file_sha256",
    "source_text_sha256",
    "provisional_decision",
    "human_review_decision",
    "reviewer_id_or_pseudonymous_code",
    "reviewer_role",
    "review_actor_type",
    "review_protocol_version",
    "adjudication_decision",
    "decision_reason",
    "evidence_locator",
    "reviewed_at",
    "adjudication_status",
    "previous_decision",
)

SOURCE_ARTIFACT_COLUMNS = (
    "source_artifact_id",
    "edition_year",
    "governed_snapshot_locator",
    "source_file_sha256",
    "byte_count",
    "canonical_url",
    "retrieved_at",
    "storage_state",
    "non_storage_reason",
    "candidate_count",
)

BLOCKER_COLUMNS = (
    "blocker_id",
    "blocker_type",
    "blocker_state",
    "required_artifact_count",
    "available_artifact_count",
    "missing_artifact_names",
    "effect",
    "continuation_action",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    """A deterministic input or output contract violation."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_id(prefix: str, *parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:24]}"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_tsv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    require(path.is_file(), f"missing required TSV: {path}")
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        actual = tuple(reader.fieldnames or ())
        require(actual == tuple(columns), f"header mismatch for {path}: {actual!r}")
        rows = list(reader)
    for line_number, row in enumerate(rows, start=2):
        require(None not in row, f"extra field in {path}:{line_number}")
        require(
            all("\x00" not in value for value in row.values()),
            f"NUL byte in {path}:{line_number}",
        )
    return rows


def write_tsv(
    path: Path, columns: Sequence[str], rows: Iterable[Mapping[str, str]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def index_unique(rows: Sequence[Mapping[str, str]], key: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row[key]
        require(value not in result, f"duplicate {key}: {value}")
        result[value] = row
    return result


def logical_source_path(year: str) -> str:
    return f"commercial_regional/avpa/{year}_results.pdf"


def governed_snapshot_locator(year: str) -> str:
    return (
        "restricted://round3l/round3l-2026-08-28t040000z/"
        + logical_source_path(year)
    )


def locate_machine_artifacts(search_roots: Sequence[Path]) -> tuple[dict[str, Path], list[str]]:
    located: dict[str, Path] = {}
    for name in MACHINE_RESEARCH_ARTIFACTS:
        candidates = sorted(
            path
            for root in search_roots
            if root.is_dir()
            for path in root.rglob(name)
            if path.is_file()
        )
        require(len(candidates) <= 1, f"ambiguous machine artifact {name}: {candidates}")
        if candidates:
            located[name] = candidates[0]
    missing = [name for name in MACHINE_RESEARCH_ARTIFACTS if name not in located]
    return located, missing


def validate_inputs(
    restricted_root: Path,
    report_pdf: Path,
) -> tuple[
    list[dict[str, str]],
    dict[str, Mapping[str, str]],
    dict[str, Mapping[str, str]],
    list[dict[str, str]],
]:
    ingest_root = restricted_root / "restricted_ingest"
    checkpoint = ingest_root / "INGESTION_CHECKPOINT.json"
    require(checkpoint.is_file(), f"missing Round 3L checkpoint: {checkpoint}")
    require(
        sha256_file(checkpoint) == ROUND3L_CHECKPOINT_SHA256,
        "Round 3L restricted checkpoint hash drift",
    )

    require(report_pdf.is_file(), f"missing descriptor-first report: {report_pdf}")
    require(
        sha256_file(report_pdf) == DESCRIPTOR_FIRST_REPORT_SHA256,
        "descriptor-first report hash drift",
    )

    assertions = read_tsv(ingest_root / "PROFESSIONAL_ASSERTIONS.tsv", ASSERTION_COLUMNS)
    records = read_tsv(ingest_root / "PROFESSIONAL_RECORDS.tsv", RECORD_COLUMNS)
    attempts = read_tsv(ingest_root / "SOURCE_ATTEMPTS.tsv", ATTEMPT_COLUMNS)
    record_index = index_unique(records, "professional_acquisition_record_key")
    attempt_index = index_unique(attempts, "attempt_key")

    candidates = [
        row for row in assertions if row["assertion_type"] == "OFFICIAL_AGGREGATED_DESCRIPTOR"
    ]
    candidates.sort(key=lambda row: row["professional_acquisition_assertion_key"])
    require(len(candidates) == EXPECTED_CANDIDATE_COUNT, "candidate count drift")
    require(
        len({row["professional_acquisition_assertion_key"] for row in candidates})
        == EXPECTED_CANDIDATE_COUNT,
        "candidate assertion key duplication",
    )
    require(
        len({row["professional_acquisition_record_key"] for row in candidates})
        == EXPECTED_CANDIDATE_COUNT,
        "candidate-to-record relation is not one-to-one",
    )
    require(
        len({row["source_locator"] for row in candidates}) == EXPECTED_CANDIDATE_COUNT,
        "candidate source locator duplication",
    )

    candidate_records: list[Mapping[str, str]] = []
    for candidate in candidates:
        record_key = candidate["professional_acquisition_record_key"]
        require(record_key in record_index, f"candidate record missing: {record_key}")
        record = record_index[record_key]
        candidate_records.append(record)
        require(
            bool(
                re.fullmatch(
                    r"commercial-regional-avpa-coffees-roasted-at-origin-"
                    r"(2021|2022|2023|2024|2025)-avpa-\1-(?:[0-9]+|p[0-9]+-r[0-9]+)",
                    record_key,
                )
            ),
            "candidate record key is not a public-safe row locator",
        )
        require(
            record["source_family_key"] == "avpa_coffees_roasted_at_origin",
            "unexpected candidate source family",
        )
        require(record["payload_kind"] == "OFFICIAL_DESCRIPTOR", "payload-kind drift")
        require(record["corpus_state"] == "RESEARCH_STAGED", "corpus-state drift")
        require(record["label_review_status"] == "NOT_REVIEWED", "review-state drift")
        require(record["is_synthetic"] == "false", "synthetic candidate rejected")
        require(record["semantic_inference_used"] == "false", "record inference drift")
        require(candidate["semantic_inference_used"] == "false", "assertion inference drift")
        require(candidate["assertion_text"] == "", "raw candidate text must remain absent")
        require(candidate["text_storage_state"] == "HASH_ONLY", "text storage-state drift")
        require(bool(SHA256_RE.fullmatch(candidate["assertion_text_sha256"])), "bad text hash")
        require(bool(SHA256_RE.fullmatch(record["source_snapshot_sha256"])), "bad source hash")
        require(bool(SHA256_RE.fullmatch(record["raw_record_sha256"])), "bad record hash")
        require(
            "#page=" in candidate["source_locator"]
            and ";table=" in candidate["source_locator"]
            and ";row=" in candidate["source_locator"],
            "candidate lacks bounded page/table/row locator",
        )
        require(record["attempt_key"] in attempt_index, "candidate attempt missing")
        attempt = attempt_index[record["attempt_key"]]
        require(attempt["lane_key"] == "commercial_regional", "candidate lane drift")
        require(attempt["outcome"] == "COMPLETED", "candidate source not completed")
        require(attempt["http_status"] == "200", "candidate source HTTP status drift")
        require(
            attempt["source_snapshot_sha256"] == record["source_snapshot_sha256"],
            "attempt/record source hash mismatch",
        )
        for _, source_column in RIGHTS_DIMENSIONS:
            require(record[source_column] in RIGHTS_STATES, "invalid rights state")
            require(record[source_column] == "UNKNOWN", "candidate rights-state drift")

    require(
        Counter(record["edition_year"] for record in candidate_records)
        == Counter(EXPECTED_CANDIDATE_COUNTS_BY_YEAR),
        "candidate year distribution drift",
    )
    require(
        len({row["source_defined_descriptor_key"] for row in candidates})
        == EXPECTED_SOURCE_DEFINED_VALUE_COUNT,
        "source-defined classification cardinality drift",
    )

    source_receipts: list[dict[str, str]] = []
    for year, candidate_count in sorted(EXPECTED_CANDIDATE_COUNTS_BY_YEAR.items()):
        year_records = [record for record in candidate_records if record["edition_year"] == year]
        hashes = {record["source_snapshot_sha256"] for record in year_records}
        require(len(hashes) == 1, f"expected one governed source hash for AVPA {year}")
        source_sha = next(iter(hashes))
        source_path = restricted_root / logical_source_path(year)
        require(source_path.is_file(), f"missing governed AVPA source file: {source_path}")
        require(sha256_file(source_path) == source_sha, f"AVPA {year} source hash drift")
        attempt = attempt_index[year_records[0]["attempt_key"]]
        source_receipts.append(
            {
                "source_artifact_id": stable_id("artifact", "avpa", year, source_sha),
                "edition_year": year,
                "governed_snapshot_locator": governed_snapshot_locator(year),
                "source_file_sha256": source_sha,
                "byte_count": str(source_path.stat().st_size),
                "canonical_url": attempt["canonical_url"],
                "retrieved_at": attempt["attempted_at"],
                "storage_state": "GOVERNED_RESTRICTED_SNAPSHOT",
                "non_storage_reason": "",
                "candidate_count": str(candidate_count),
            }
        )
    require(len(source_receipts) == EXPECTED_SOURCE_FILE_COUNT, "source-file count drift")

    return candidates, record_index, attempt_index, source_receipts


def build_rows(
    candidates: Sequence[Mapping[str, str]],
    record_index: Mapping[str, Mapping[str, str]],
    source_receipts: Sequence[Mapping[str, str]],
) -> dict[str, list[dict[str, str]]]:
    source_by_year = {row["edition_year"]: row for row in source_receipts}
    ledger: list[dict[str, str]] = []
    queue: list[dict[str, str]] = []
    decisions: list[dict[str, str]] = []
    provenance: list[dict[str, str]] = []
    rights: list[dict[str, str]] = []
    publication_layers: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    normalization: list[dict[str, str]] = []
    human_template: list[dict[str, str]] = []
    adjudication_template: list[dict[str, str]] = []

    for candidate in candidates:
        assertion_id = candidate["professional_acquisition_assertion_key"]
        record_id = candidate["professional_acquisition_record_key"]
        record = record_index[record_id]
        source = source_by_year[record["edition_year"]]
        queue_id = stable_id("review", assertion_id)
        decision_id = stable_id("decision", assertion_id, "NON_DESCRIPTOR")
        queue.append(
            {
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "professional_record_id": record_id,
                "source_family_id": "avpa_coffees_roasted_at_origin",
                "source_route_id": "avpa_public_palmares",
                "edition_id": record["edition_key"],
                "edition_year": record["edition_year"],
                "source_artifact_id": source["source_artifact_id"],
                "source_file_sha256": source["source_file_sha256"],
                "route_index_sha256": "",
                "source_file_sha256_scope": "FULL_GOVERNED_SNAPSHOT",
                "source_file_nonstorage_reason": "",
                "raw_record_sha256": record["raw_record_sha256"],
                "source_locator": candidate["source_locator"],
                "source_language": candidate["source_language_code"],
                "source_text_sha256": candidate["assertion_text_sha256"],
                "source_text_storage_state": "HASH_ONLY",
                "source_text_non_storage_reason": (
                    "PUBLIC_REPOSITORY_EXCLUDES_SOURCE_NATIVE_RESULT_TEXT_WHILE_RIGHTS_UNKNOWN"
                ),
                "source_field_contract": "AVPA_RESULT_TABLE_CATEGORY_CLASSIFICATION",
                "publication_layer": "RESULT_METADATA",
                "descriptor_class": "NON_DESCRIPTOR",
                "evidence_tier": "UNRESOLVED",
                "review_state": "REJECTED_NON_DESCRIPTOR",
                "review_actor_type": "CODEX_SOURCE_AUDITOR",
                "current_disposition": "NON_DESCRIPTOR",
                "disposition_reason_code": "CATEGORY_CLASSIFICATION_NOT_FILLED_OBSERVATION",
                "human_review_required": "false",
                "model_eligible": "false",
                "decision_effective_date": DECISION_EFFECTIVE_DATE,
            }
        )
        ledger.append(
            {
                "descriptor_assertion_id": assertion_id,
                "effective_record_id": record["effective_record_key"],
                "source_artifact_id": source["source_artifact_id"],
                "source_route_id": "avpa_public_palmares",
                "schema_signature_id": "schema.avpa.palmares-result-category.v1",
                "publication_layer": "RESULT_METADATA",
                "source_field_label": "AVPA_RESULT_TABLE_CATEGORY_CLASSIFICATION",
                "source_field_label_sha256": sha256_text(
                    "AVPA_RESULT_TABLE_CATEGORY_CLASSIFICATION"
                ),
                "source_selector_or_locator": candidate["source_locator"],
                "source_page_or_record_locator": candidate["source_locator"],
                "raw_field_text": "",
                "raw_field_text_sha256": candidate["assertion_text_sha256"],
                "atomic_source_text": "",
                "atomic_source_text_sha256": candidate["assertion_text_sha256"],
                "source_language": candidate["source_language_code"],
                "descriptor_class": "NON_DESCRIPTOR",
                "source_native_lexical_form": "",
                "source_native_lexical_form_sha256": candidate["assertion_text_sha256"],
                "normalized_candidate_form": "",
                "normalized_candidate_form_sha256": "",
                "evidence_tier": "UNRESOLVED",
                "evidence_origin_type": "ORGANIZER_RESULT_CLASSIFICATION",
                "origin_decision_basis": (
                    "VISUAL_FIELD_AUDIT;NOT_A_FILLED_JUDGE_OR_JURY_SENSORY_PASSAGE"
                ),
                "origin_evidence_locator": candidate["source_locator"],
                "review_state": "REJECTED_NON_DESCRIPTOR",
                "review_actor_type": "CODEX_SOURCE_AUDITOR",
                "review_receipt_id": decision_id,
                "rights_decision_id": stable_id("rights-set", assertion_id),
                "within_record_repeat_group": "",
                "cross_observation_repeat_group": "",
                "mirror_group": "",
                "created_at": candidate["created_at"],
                "source_retrieved_at": CHECKPOINT_AT,
                "source_file_sha256": source["source_file_sha256"],
                "route_index_sha256": "",
                "source_file_sha256_scope": "FULL_GOVERNED_SNAPSHOT",
                "source_file_nonstorage_reason": "",
                "parser_version": "ROUND3L_PARSER_VERSION_NOT_RECORDED",
                "adapter_version": "ROUND3L_ADAPTER_VERSION_NOT_RECORDED",
                "source_text_storage_state": "HASH_ONLY",
                "source_text_non_storage_reason": (
                    "PUBLIC_REPOSITORY_EXCLUDES_SOURCE_NATIVE_RESULT_TEXT_WHILE_RIGHTS_UNKNOWN"
                ),
                "counts_as_reviewed_descriptor": "false",
                "model_eligible": "false",
            }
        )
        decisions.append(
            {
                "decision_id": decision_id,
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "current_disposition": "NON_DESCRIPTOR",
                "descriptor_class": "NON_DESCRIPTOR",
                "review_state": "REJECTED_NON_DESCRIPTOR",
                "review_actor_type": "CODEX_SOURCE_AUDITOR",
                "review_protocol_version": REVIEW_PROTOCOL_VERSION,
                "decision_reason_code": "CATEGORY_CLASSIFICATION_NOT_FILLED_OBSERVATION",
                "decision_basis": (
                    "SOURCE_PDF_VISUAL_AUDIT_IDENTIFIES_RESULT_TABLE_CATEGORY_COLUMN;"
                    "ROUND3M_CLASS_EXCLUDES_CATEGORY_NAMES"
                ),
                "evidence_locator": candidate["source_locator"],
                "source_file_sha256": source["source_file_sha256"],
                "route_index_sha256": "",
                "source_file_sha256_scope": "FULL_GOVERNED_SNAPSHOT",
                "source_file_nonstorage_reason": "",
                "source_text_sha256": candidate["assertion_text_sha256"],
                "human_confirmed": "false",
                "expert_adjudicated": "false",
                "counts_as_reviewed_descriptor": "false",
                "model_eligible": "false",
                "decision_effective_date": DECISION_EFFECTIVE_DATE,
            }
        )
        provenance.append(
            {
                "provenance_decision_id": stable_id("provenance", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "source_route_id": "avpa_public_palmares",
                "source_artifact_id": source["source_artifact_id"],
                "source_file_sha256": source["source_file_sha256"],
                "route_index_sha256": "",
                "source_file_sha256_scope": "FULL_GOVERNED_SNAPSHOT",
                "source_file_nonstorage_reason": "",
                "source_locator": candidate["source_locator"],
                "source_field_contract": "AVPA_RESULT_TABLE_CATEGORY_CLASSIFICATION",
                "publication_layer": "RESULT_METADATA",
                "evidence_origin_type": "ORGANIZER_RESULT_CLASSIFICATION",
                "origin_decision_basis": (
                    "VISUAL_FIELD_AUDIT;NOT_A_FILLED_JUDGE_OR_JURY_SENSORY_PASSAGE"
                ),
                "origin_evidence_locator": candidate["source_locator"],
                "descriptor_class": "NON_DESCRIPTOR",
                "evidence_tier": "UNRESOLVED",
                "review_state": "REJECTED_NON_DESCRIPTOR",
                "review_actor_type": "CODEX_SOURCE_AUDITOR",
                "provenance_complete": "true",
            }
        )
        for purpose, source_column in RIGHTS_DIMENSIONS:
            rights_state = record[source_column]
            rights.append(
                {
                    "rights_decision_id": stable_id("rights", assertion_id, purpose),
                    "descriptor_assertion_id": assertion_id,
                    "source_artifact_id": source["source_artifact_id"],
                    "purpose": purpose,
                    "rights_state": rights_state,
                    "decision_basis": "CARRIED_FORWARD_FROM_PINNED_ROUND3L_RECORD_RIGHTS_STATE",
                    "rights_evidence_locator": governed_snapshot_locator(record["edition_year"]),
                    "review_actor_type": "CODEX_SOURCE_AUDITOR",
                    "model_eligibility_effect": (
                        "INELIGIBLE_NON_DESCRIPTOR_AND_NO_AFFIRMATIVE_RIGHTS"
                    ),
                }
            )
        publication_layers.append(
            {
                "publication_layer_relation_id": stable_id("layer", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "professional_record_id": record_id,
                "publication_layer": "RESULT_METADATA",
                "related_assertion_id": "",
                "relation_type": "SINGLE_REJECTED_RESULT_LAYER",
                "decision_basis": "AWARD_ROW_CATEGORY_CLASSIFICATION_IS_RESULT_METADATA",
                "source_locator": candidate["source_locator"],
                "source_file_sha256": source["source_file_sha256"],
                "route_index_sha256": "",
                "source_file_sha256_scope": "FULL_GOVERNED_SNAPSHOT",
                "source_file_nonstorage_reason": "",
            }
        )
        duplicates.append(
            {
                "duplicate_decision_id": stable_id("duplicate", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "professional_record_id": record_id,
                "deduplication_disposition": "CANONICAL",
                "within_record_repeat_group": "",
                "cross_observation_repeat_group": "",
                "mirror_group": "",
                "decision_basis": (
                    "UNIQUE_ASSERTION_KEY_RECORD_AND_LOCATOR;REPEAT_COUNTING_NOT_APPLICABLE_"
                    "TO_REJECTED_NON_DESCRIPTOR"
                ),
                "counts_as_assertion": "false",
                "counts_as_record_unique_descriptor": "false",
            }
        )
        normalization.append(
            {
                "normalization_decision_id": stable_id("normalization", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "source_native_text_sha256": candidate["assertion_text_sha256"],
                "source_native_text_storage_state": "HASH_ONLY",
                "normalized_candidate_form": "",
                "normalization_operation": "NOT_APPLICABLE_NON_DESCRIPTOR",
                "decision_basis": "CATEGORY_CLASSIFICATION_REJECTED_BEFORE_NORMALIZATION",
                "source_native_lexical_form_count_effect": "0",
                "normalized_form_count_effect": "0",
            }
        )
        human_template.append(
            {
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "source_locator": candidate["source_locator"],
                "source_file_sha256": source["source_file_sha256"],
                "source_text_sha256": candidate["assertion_text_sha256"],
                "machine_disposition": "NON_DESCRIPTOR",
                "reviewer_id_or_pseudonymous_code": "",
                "reviewer_role": "",
                "review_actor_type": "",
                "review_protocol_version": REVIEW_PROTOCOL_VERSION,
                "decision": "",
                "decision_reason": "",
                "evidence_locator": candidate["source_locator"],
                "reviewed_at": "",
                "adjudication_status": "",
                "previous_decision": "NON_DESCRIPTOR",
            }
        )
        adjudication_template.append(
            {
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "source_locator": candidate["source_locator"],
                "source_file_sha256": source["source_file_sha256"],
                "source_text_sha256": candidate["assertion_text_sha256"],
                "provisional_decision": "NON_DESCRIPTOR",
                "human_review_decision": "",
                "reviewer_id_or_pseudonymous_code": "",
                "reviewer_role": "",
                "review_actor_type": "",
                "review_protocol_version": REVIEW_PROTOCOL_VERSION,
                "adjudication_decision": "",
                "decision_reason": "",
                "evidence_locator": candidate["source_locator"],
                "reviewed_at": "",
                "adjudication_status": "",
                "previous_decision": "NON_DESCRIPTOR",
            }
        )

    return {
        "ledger": ledger,
        "queue": queue,
        "decisions": decisions,
        "provenance": provenance,
        "rights": rights,
        "publication_layers": publication_layers,
        "duplicates": duplicates,
        "normalization": normalization,
        "coassertions": [],
        "human_template": human_template,
        "adjudication_template": adjudication_template,
    }


def read_live_assertions(path: Path) -> list[dict[str, str]]:
    """Read the optional adapter handoff without requiring it to exist."""

    if not path.is_file():
        return []
    rows = read_tsv(path, LIVE_ASSERTION_EXPORT_COLUMNS)
    rows.sort(key=lambda row: row["descriptor_assertion_id"])
    require(
        len({row["descriptor_assertion_id"] for row in rows}) == len(rows),
        "duplicate live descriptor_assertion_id",
    )
    publication_layers = {
        "PRIMARY_JURY_DESCRIPTION",
        "GENERIC_ORGANIZER_SENSORY_FIELD",
        "PRODUCER_OR_FARM_PROFILE",
        "SECONDARY_SENSORY_TABLE",
        "JUDGE_LEVEL_OBSERVATION",
        "RESULT_METADATA",
        "PROTOCOL_OR_BLANK_FORM",
    }
    descriptor_classes = {"STRICT_FLAVOR", "BROAD_SENSORY", "NON_DESCRIPTOR"}
    evidence_tiers = {"P0", "P1", "P2", "P3", "P4", "P5", "UNRESOLVED"}
    review_states = {"AUTO_EXTRACTED", "PROVISIONAL_MACHINE_CLASSIFIED"}
    review_actors = {"AUTOMATED_PARSER", "CODEX_SOURCE_AUDITOR"}
    for row in rows:
        require(row["descriptor_assertion_id"], "empty live assertion id")
        require(row["effective_record_id"], "live assertion lacks effective record")
        require(row["source_artifact_id"], "live assertion lacks source artifact")
        require(row["source_route_id"], "live assertion lacks source route")
        require(row["schema_signature_id"], "live assertion lacks schema signature")
        require(row["publication_layer"] in publication_layers, "bad live publication layer")
        require(row["descriptor_class"] in descriptor_classes, "bad live descriptor class")
        require(row["descriptor_class"] != "NON_DESCRIPTOR", "live positive export has non-descriptor")
        require(row["evidence_tier"] in evidence_tiers, "bad live evidence tier")
        require(row["review_state"] in review_states, "bad live review state")
        require(row["review_actor_type"] in review_actors, "bad live review actor")
        require(row["rights_state"] in RIGHTS_STATES, "bad live rights state")
        require(row["rights_state"] != "AFFIRMATIVE", "singular rights state cannot grant rights")
        require(row["model_eligible"] == "false", "live provisional row cannot be model eligible")
        require(row["count_disposition"] in {"ADMITTED", "SECONDARY_REVIEW_ONLY"}, "bad count disposition")
        require(
            (row["publication_layer"] == "SECONDARY_SENSORY_TABLE")
            == (row["count_disposition"] == "SECONDARY_REVIEW_ONLY"),
            "secondary publication layer and review-only disposition must match",
        )
        require(bool(SHA256_RE.fullmatch(row["raw_field_text_sha256"])), "bad live raw text hash")
        require(bool(SHA256_RE.fullmatch(row["atomic_source_text_sha256"])), "bad live atomic hash")
        require(bool(SHA256_RE.fullmatch(row["route_index_sha256"])), "bad route-index hash")
        require(row["source_file_sha256_scope"], "live source hash scope missing")
        require(row["source_file_nonstorage_reason"], "live source non-storage reason missing")
        require(row["source_retrieved_at"], "live retrieval timestamp missing")
        require(row["parser_version"] and row["adapter_version"], "live version missing")
        require("\t" not in row["source_field_label"], "tab in live field label")
    return rows


def read_live_adapter_metrics(path: Path) -> dict[str, object]:
    """Verify the tracked live export's governed restricted-capture receipt."""

    require(path.is_file(), "live adapter metrics receipt is missing")
    metrics = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(metrics, dict), "live adapter metrics must be a JSON object")
    require(
        metrics.get("restricted_capture_manifest_sha256")
        == EXPECTED_CAPTURE_MANIFEST_SHA256,
        "live adapter metrics manifest hash drift",
    )
    require(
        metrics.get("restricted_capture_root_locator")
        == EXPECTED_CAPTURE_ROOT_LOCATOR,
        "live adapter metrics governed locator drift",
    )
    require(
        metrics.get("restricted_capture_manifest_contract")
        == "round3m.restricted-capture-manifest.v1",
        "live adapter metrics manifest contract drift",
    )
    return metrics


def live_capture_sha256(row: Mapping[str, str]) -> str:
    """Return the bounded-capture hash encoded by the public-safe handoff."""

    prefix = "WEB_INDEX_FIELD_CAPTURE_SHA256:"
    scope = row["source_file_sha256_scope"]
    require(scope.startswith(prefix), "live source hash scope prefix drift")
    value = scope.removeprefix(prefix).split(";", 1)[0]
    require(bool(SHA256_RE.fullmatch(value)), "bad bounded-capture source hash")
    return value


def build_live_rows(live_rows: Sequence[Mapping[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Convert the hash-only live handoff into the common public-safe surfaces."""

    ledger: list[dict[str, str]] = []
    queue: list[dict[str, str]] = []
    decisions: list[dict[str, str]] = []
    provenance: list[dict[str, str]] = []
    rights: list[dict[str, str]] = []
    publication_layers: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    normalization: list[dict[str, str]] = []
    human_template: list[dict[str, str]] = []
    adjudication_template: list[dict[str, str]] = []

    counting_rows: list[Mapping[str, str]] = []
    for row in live_rows:
        secondary_layer = row["publication_layer"] == "SECONDARY_SENSORY_TABLE"
        secondary_review_only = row["count_disposition"] == "SECONDARY_REVIEW_ONLY"
        require(
            secondary_layer == secondary_review_only,
            "secondary publication layer and review-only disposition must match",
        )
        if not secondary_review_only:
            counting_rows.append(row)

    observation_groups: dict[tuple[str, ...], list[str]] = {}
    for row in counting_rows:
        key = (
            row["effective_record_id"],
            row["source_artifact_id"],
            row["publication_layer"],
            row["source_selector_or_locator"],
            row["atomic_source_text_sha256"],
        )
        observation_groups.setdefault(key, []).append(row["descriptor_assertion_id"])
    within_group_by_id: dict[str, str] = {}
    dedup_by_id: dict[str, str] = {}
    assertion_level_rows: list[Mapping[str, str]] = []
    for key, assertion_ids in sorted(observation_groups.items()):
        ordered_ids = sorted(assertion_ids)
        if len(ordered_ids) > 1:
            group_id = stable_id("repeat-field", *key)
            within_group_by_id.update({assertion_id: group_id for assertion_id in ordered_ids})
        for index, assertion_id in enumerate(ordered_ids):
            if index:
                dedup_by_id[assertion_id] = "EXACT_WITHIN_FIELD_REPEAT"
            else:
                assertion_level_rows.append(
                    next(
                        row
                        for row in counting_rows
                        if row["descriptor_assertion_id"] == assertion_id
                    )
                )

    record_groups: dict[tuple[str, str], list[str]] = {}
    for row in assertion_level_rows:
        key = (row["effective_record_id"], row["atomic_source_text_sha256"])
        record_groups.setdefault(key, []).append(row["descriptor_assertion_id"])
    cross_group_by_id: dict[str, str] = {}
    for key, assertion_ids in sorted(record_groups.items()):
        ordered_ids = sorted(assertion_ids)
        if len(ordered_ids) > 1:
            group_id = stable_id("repeat-record", *key)
            cross_group_by_id.update({assertion_id: group_id for assertion_id in ordered_ids})
        for index, assertion_id in enumerate(ordered_ids):
            if index:
                dedup_by_id[assertion_id] = "CROSS_OBSERVATION_REPEAT"
            else:
                dedup_by_id.setdefault(assertion_id, "CANONICAL")

    for row in live_rows:
        assertion_id = row["descriptor_assertion_id"]
        source_file_sha256 = live_capture_sha256(row)
        queue_id = stable_id("review", assertion_id)
        secondary_review_only = row["count_disposition"] == "SECONDARY_REVIEW_ONLY"
        current_disposition = (
            "PUBLICATION_LAYER_CONFLICT"
            if secondary_review_only
            else "HUMAN_REVIEW_REQUIRED"
        )
        disposition_reason_code = (
            "SECONDARY_LAYER_PRESERVED_WITHOUT_PRIMARY_DOUBLE_CREDIT"
            if secondary_review_only
            else "LIVE_HASH_ONLY_CANDIDATE_REQUIRES_HUMAN_REVIEW"
        )
        decision_id = stable_id("decision", assertion_id, current_disposition)
        source_locator = row["source_selector_or_locator"]
        page_locator = row["source_page_or_record_locator"]
        source_family_id = (
            "coe_ace"
            if ".coe." in row["schema_signature_id"]
            else "UNRESOLVED_FROM_LIVE_EXPORT"
        )
        queue.append(
            {
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "professional_record_id": row["effective_record_id"],
                "source_family_id": source_family_id,
                "source_route_id": row["source_route_id"],
                "edition_id": "",
                "edition_year": "",
                "source_artifact_id": row["source_artifact_id"],
                "source_file_sha256": source_file_sha256,
                "route_index_sha256": row["route_index_sha256"],
                "source_file_sha256_scope": row["source_file_sha256_scope"],
                "source_file_nonstorage_reason": row["source_file_nonstorage_reason"],
                "raw_record_sha256": "",
                "source_locator": page_locator,
                "source_language": row["source_language"],
                "source_text_sha256": row["atomic_source_text_sha256"],
                "source_text_storage_state": "HASH_ONLY",
                "source_text_non_storage_reason": row["source_file_nonstorage_reason"],
                "source_field_contract": row["schema_signature_id"],
                "publication_layer": row["publication_layer"],
                "descriptor_class": row["descriptor_class"],
                "evidence_tier": row["evidence_tier"],
                "review_state": row["review_state"],
                "review_actor_type": row["review_actor_type"],
                "current_disposition": current_disposition,
                "disposition_reason_code": disposition_reason_code,
                "human_review_required": "true",
                "model_eligible": "false",
                "decision_effective_date": DECISION_EFFECTIVE_DATE,
            }
        )
        decisions.append(
            {
                "decision_id": decision_id,
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "current_disposition": current_disposition,
                "descriptor_class": row["descriptor_class"],
                "review_state": row["review_state"],
                "review_actor_type": row["review_actor_type"],
                "review_protocol_version": REVIEW_PROTOCOL_VERSION,
                "decision_reason_code": disposition_reason_code,
                "decision_basis": row["origin_decision_basis"],
                "evidence_locator": page_locator,
                "source_file_sha256": source_file_sha256,
                "route_index_sha256": row["route_index_sha256"],
                "source_file_sha256_scope": row["source_file_sha256_scope"],
                "source_file_nonstorage_reason": row["source_file_nonstorage_reason"],
                "source_text_sha256": row["atomic_source_text_sha256"],
                "human_confirmed": "false",
                "expert_adjudicated": "false",
                "counts_as_reviewed_descriptor": "false",
                "model_eligible": "false",
                "decision_effective_date": DECISION_EFFECTIVE_DATE,
            }
        )
        ledger.append(
            {
                "descriptor_assertion_id": assertion_id,
                "effective_record_id": row["effective_record_id"],
                "source_artifact_id": row["source_artifact_id"],
                "source_route_id": row["source_route_id"],
                "schema_signature_id": row["schema_signature_id"],
                "publication_layer": row["publication_layer"],
                "source_field_label": row["source_field_label"],
                "source_field_label_sha256": sha256_text(row["source_field_label"]),
                "source_selector_or_locator": source_locator,
                "source_page_or_record_locator": page_locator,
                "raw_field_text": "",
                "raw_field_text_sha256": row["raw_field_text_sha256"],
                "atomic_source_text": "",
                "atomic_source_text_sha256": row["atomic_source_text_sha256"],
                "source_language": row["source_language"],
                "descriptor_class": row["descriptor_class"],
                "source_native_lexical_form": "",
                "source_native_lexical_form_sha256": row["atomic_source_text_sha256"],
                "normalized_candidate_form": "",
                "normalized_candidate_form_sha256": "",
                "evidence_tier": row["evidence_tier"],
                "evidence_origin_type": row["evidence_origin_type"],
                "origin_decision_basis": row["origin_decision_basis"],
                "origin_evidence_locator": source_locator,
                "review_state": row["review_state"],
                "review_actor_type": row["review_actor_type"],
                "review_receipt_id": decision_id,
                "rights_decision_id": stable_id("rights-set", assertion_id),
                "within_record_repeat_group": within_group_by_id.get(assertion_id, ""),
                "cross_observation_repeat_group": cross_group_by_id.get(
                    assertion_id, row["cross_observation_repeat_group"]
                ),
                "mirror_group": "",
                "created_at": row["source_retrieved_at"],
                "source_retrieved_at": row["source_retrieved_at"],
                "source_file_sha256": source_file_sha256,
                "route_index_sha256": row["route_index_sha256"],
                "source_file_sha256_scope": row["source_file_sha256_scope"],
                "source_file_nonstorage_reason": row["source_file_nonstorage_reason"],
                "parser_version": row["parser_version"],
                "adapter_version": row["adapter_version"],
                "source_text_storage_state": "HASH_ONLY",
                "source_text_non_storage_reason": row["source_file_nonstorage_reason"],
                "counts_as_reviewed_descriptor": "false",
                "model_eligible": "false",
            }
        )
        provenance.append(
            {
                "provenance_decision_id": stable_id("provenance", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "source_route_id": row["source_route_id"],
                "source_artifact_id": row["source_artifact_id"],
                "source_file_sha256": source_file_sha256,
                "route_index_sha256": row["route_index_sha256"],
                "source_file_sha256_scope": row["source_file_sha256_scope"],
                "source_file_nonstorage_reason": row["source_file_nonstorage_reason"],
                "source_locator": page_locator,
                "source_field_contract": row["schema_signature_id"],
                "publication_layer": row["publication_layer"],
                "evidence_origin_type": row["evidence_origin_type"],
                "origin_decision_basis": row["origin_decision_basis"],
                "origin_evidence_locator": source_locator,
                "descriptor_class": row["descriptor_class"],
                "evidence_tier": row["evidence_tier"],
                "review_state": row["review_state"],
                "review_actor_type": row["review_actor_type"],
                "provenance_complete": "false",
            }
        )
        for purpose, _ in RIGHTS_DIMENSIONS:
            rights.append(
                {
                    "rights_decision_id": stable_id("rights", assertion_id, purpose),
                    "descriptor_assertion_id": assertion_id,
                    "source_artifact_id": row["source_artifact_id"],
                    "purpose": purpose,
                    "rights_state": row["rights_state"],
                    "decision_basis": (
                        "CONSERVATIVE_SINGULAR_SOURCE_STATE_APPLIED_TO_ALL_PURPOSES;"
                        "NO_AFFIRMATIVE_GRANT"
                    ),
                    "rights_evidence_locator": page_locator,
                    "review_actor_type": row["review_actor_type"],
                    "model_eligibility_effect": "INELIGIBLE_PENDING_OR_UNKNOWN_RIGHTS_AND_NO_HUMAN_REVIEW",
                }
            )
        publication_layers.append(
            {
                "publication_layer_relation_id": stable_id("layer", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "professional_record_id": row["effective_record_id"],
                "publication_layer": row["publication_layer"],
                "related_assertion_id": "",
                "relation_type": (
                    "SECONDARY_REVIEW_ONLY"
                    if secondary_review_only
                    else "PRIMARY_PROVISIONAL_LAYER"
                ),
                "decision_basis": row["origin_decision_basis"],
                "source_locator": page_locator,
                "source_file_sha256": source_file_sha256,
                "route_index_sha256": row["route_index_sha256"],
                "source_file_sha256_scope": row["source_file_sha256_scope"],
                "source_file_nonstorage_reason": row["source_file_nonstorage_reason"],
            }
        )
        if secondary_review_only:
            dedup = "UNRESOLVED"
        else:
            dedup = dedup_by_id[assertion_id]
        counts_as_assertion = dedup not in {
            "EXACT_WITHIN_FIELD_REPEAT",
            "UNRESOLVED",
        }
        counts_as_record_unique = dedup == "CANONICAL"
        duplicates.append(
            {
                "duplicate_decision_id": stable_id("duplicate", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "professional_record_id": row["effective_record_id"],
                "deduplication_disposition": dedup,
                "within_record_repeat_group": within_group_by_id.get(assertion_id, ""),
                "cross_observation_repeat_group": cross_group_by_id.get(
                    assertion_id, row["cross_observation_repeat_group"]
                ),
                "mirror_group": "",
                "decision_basis": (
                    "DETERMINISTIC_EFFECTIVE_RECORD_LOCATOR_AND_ATOMIC_HASH_AUDIT;"
                    "PUBLICATION_LAYER_PRESERVED"
                ),
                "counts_as_assertion": "true" if counts_as_assertion else "false",
                "counts_as_record_unique_descriptor": (
                    "true" if counts_as_record_unique else "false"
                ),
            }
        )
        normalization.append(
            {
                "normalization_decision_id": stable_id("normalization", assertion_id),
                "descriptor_assertion_id": assertion_id,
                "source_native_text_sha256": row["atomic_source_text_sha256"],
                "source_native_text_storage_state": "HASH_ONLY",
                "normalized_candidate_form": "",
                "normalization_operation": "NOT_PERFORMED_HASH_ONLY_PROVISIONAL",
                "decision_basis": "SOURCE_NATIVE_TEXT_NOT_PUBLICLY_STORED;HUMAN_REVIEW_PENDING",
                "source_native_lexical_form_count_effect": "0",
                "normalized_form_count_effect": "0",
            }
        )
        human_template.append(
            {
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "source_locator": page_locator,
                "source_file_sha256": source_file_sha256,
                "source_text_sha256": row["atomic_source_text_sha256"],
                "machine_disposition": current_disposition,
                "reviewer_id_or_pseudonymous_code": "",
                "reviewer_role": "",
                "review_actor_type": "",
                "review_protocol_version": REVIEW_PROTOCOL_VERSION,
                "decision": "",
                "decision_reason": "",
                "evidence_locator": source_locator,
                "reviewed_at": "",
                "adjudication_status": "",
                "previous_decision": current_disposition,
            }
        )
        adjudication_template.append(
            {
                "review_queue_id": queue_id,
                "descriptor_assertion_id": assertion_id,
                "source_locator": page_locator,
                "source_file_sha256": source_file_sha256,
                "source_text_sha256": row["atomic_source_text_sha256"],
                "provisional_decision": current_disposition,
                "human_review_decision": "",
                "reviewer_id_or_pseudonymous_code": "",
                "reviewer_role": "",
                "review_actor_type": "",
                "review_protocol_version": REVIEW_PROTOCOL_VERSION,
                "adjudication_decision": "",
                "decision_reason": "",
                "evidence_locator": source_locator,
                "reviewed_at": "",
                "adjudication_status": "",
                "previous_decision": current_disposition,
            }
        )

    coassertions: list[dict[str, str]] = []
    p2_by_record: dict[str, dict[str, Mapping[str, str]]] = {}
    for row in live_rows:
        if (
            row["evidence_tier"] == "P2"
            and row["publication_layer"] == "PRIMARY_JURY_DESCRIPTION"
            and row["count_disposition"] == "ADMITTED"
            and not row["within_record_repeat_group"]
        ):
            p2_by_record.setdefault(row["effective_record_id"], {}).setdefault(
                row["atomic_source_text_sha256"], row
            )
    for effective_record_id, by_hash in sorted(p2_by_record.items()):
        unique = sorted(by_hash.values(), key=lambda row: row["atomic_source_text_sha256"])
        for left_index, left in enumerate(unique):
            for right in unique[left_index + 1 :]:
                left_hash = left["atomic_source_text_sha256"]
                right_hash = right["atomic_source_text_sha256"]
                coassertions.append(
                    {
                        "coassertion_event_id": stable_id(
                            "pair", effective_record_id, left_hash, right_hash
                        ),
                        "effective_record_id": effective_record_id,
                        "left_descriptor_assertion_id": left["descriptor_assertion_id"],
                        "right_descriptor_assertion_id": right["descriptor_assertion_id"],
                        "left_normalized_form": "",
                        "right_normalized_form": "",
                        "left_normalized_form_sha256": "",
                        "right_normalized_form_sha256": "",
                        "left_atomic_source_text_sha256": left_hash,
                        "right_atomic_source_text_sha256": right_hash,
                        "evidence_tier": "P2",
                        "publication_layer": "PRIMARY_JURY_DESCRIPTION",
                        "pair_support_event_count": "1",
                        "source_file_sha256": live_capture_sha256(left),
                        "route_index_sha256": left["route_index_sha256"],
                        "source_file_sha256_scope": left["source_file_sha256_scope"],
                        "source_file_nonstorage_reason": left[
                            "source_file_nonstorage_reason"
                        ],
                    }
                )

    return {
        "ledger": ledger,
        "queue": queue,
        "decisions": decisions,
        "provenance": provenance,
        "rights": rights,
        "publication_layers": publication_layers,
        "duplicates": duplicates,
        "normalization": normalization,
        "coassertions": coassertions,
        "human_template": human_template,
        "adjudication_template": adjudication_template,
    }


def build_c0_c1_receipt(
    record_index: Mapping[str, Mapping[str, str]],
) -> dict[str, object]:
    """Reconcile only public-safe context evidence aggregates.

    Source-native roast strings and record identities stay in the restricted
    checkpoint.  Presence is counted only when both the value and its source
    scheme are populated; no descriptor vocabulary or competition category is
    used to infer roast or C0/C1.
    """

    records = list(record_index.values())
    fresh_distribution = Counter(row["fresh_preparation_status"] for row in records)
    c0_distribution = Counter(row["c0_source_status"] for row in records)
    c1_distribution = Counter(row["c1_evidence_status"] for row in records)
    require(
        fresh_distribution == Counter(EXPECTED_FRESH_PREPARATION_STATUS),
        "fresh-preparation status drift",
    )
    require(c0_distribution == Counter(EXPECTED_C0_SOURCE_STATUS), "C0 status drift")
    require(c1_distribution == Counter(EXPECTED_C1_EVIDENCE_STATUS), "C1 status drift")

    roast_value_present = sum(bool(row["source_native_roast_value"]) for row in records)
    roast_scheme_present = sum(bool(row["source_native_roast_scheme"]) for row in records)
    roast_pair_present = sum(
        bool(row["source_native_roast_value"] and row["source_native_roast_scheme"])
        for row in records
    )
    roast_pair_c1_distribution = Counter(
        row["c1_evidence_status"]
        for row in records
        if row["source_native_roast_value"] and row["source_native_roast_scheme"]
    )
    reviewed_c1_mapping_count = sum(bool(row["reviewed_c1_mapping"]) for row in records)
    semantic_inference_count = sum(row["semantic_inference_used"] != "false" for row in records)

    require(
        roast_value_present == EXPECTED_DIRECT_ROAST_EVIDENCE_COUNT,
        "source-native roast value count drift",
    )
    require(
        roast_scheme_present == EXPECTED_DIRECT_ROAST_EVIDENCE_COUNT,
        "source-native roast scheme count drift",
    )
    require(
        roast_pair_present == EXPECTED_DIRECT_ROAST_EVIDENCE_COUNT,
        "paired direct roast evidence count drift",
    )
    require(
        roast_pair_c1_distribution == {"REPORTED_UNRESOLVED": EXPECTED_DIRECT_ROAST_EVIDENCE_COUNT},
        "direct roast evidence must remain C1-unresolved",
    )
    require(reviewed_c1_mapping_count == 0, "unexpected reviewed C1 mapping")
    require(semantic_inference_count == 0, "semantic inference found in Round 3L records")

    return {
        "receipt_version": "round3m-c0-c1-evidence-receipt-v1",
        "input_checkpoint_at": CHECKPOINT_AT,
        "input_checkpoint_sha256": ROUND3L_CHECKPOINT_SHA256,
        "universe": "ROUND3L_RESEARCH_STAGED_PUBLICATION_RECORDS",
        "record_count": len(records),
        "fresh_preparation_status_distribution": dict(sorted(fresh_distribution.items())),
        "c0_source_status_distribution": dict(sorted(c0_distribution.items())),
        "c1_evidence_status_distribution": dict(sorted(c1_distribution.items())),
        "direct_source_roast_value_present_count": roast_value_present,
        "direct_source_roast_scheme_present_count": roast_scheme_present,
        "direct_source_roast_value_and_scheme_present_count": roast_pair_present,
        "direct_roast_evidence_c1_status_distribution": dict(
            sorted(roast_pair_c1_distribution.items())
        ),
        "reviewed_c1_mapping_count": reviewed_c1_mapping_count,
        "semantic_inference_used_count": semantic_inference_count,
        "c1_promotion_count": 0,
        "policy": {
            "preparation_service_requires_explicit_source_evidence": True,
            "c0_mapping_requires_reviewed_mapping": True,
            "source_native_roast_retained_in_restricted_checkpoint": True,
            "tasting_descriptors_used_to_infer_roast": False,
            "competition_categories_auto_mapped_to_c1": False,
        },
        "public_boundary": {
            "source_native_roast_strings_emitted": 0,
            "source_native_roast_scheme_strings_emitted": 0,
            "record_level_context_rows_emitted": 0,
            "aggregate_presence_counts_emitted": True,
        },
    }


def validate_outputs(rows: Mapping[str, Sequence[Mapping[str, str]]]) -> None:
    candidate_sets = {
        name: {row["descriptor_assertion_id"] for row in content}
        for name, content in rows.items()
        if name not in {"rights", "coassertions"}
    }
    reference = candidate_sets["queue"]
    require(len(reference) == EXPECTED_CANDIDATE_COUNT, "output candidate count drift")
    for name, candidate_set in candidate_sets.items():
        require(candidate_set == reference, f"candidate coverage drift in {name}")
        require(len(rows[name]) == EXPECTED_CANDIDATE_COUNT, f"row-count drift in {name}")

    disposition_counts = Counter(row["current_disposition"] for row in rows["decisions"])
    require(disposition_counts == {"NON_DESCRIPTOR": EXPECTED_CANDIDATE_COUNT}, "bad dispositions")
    require(
        all(row["review_actor_type"] == "CODEX_SOURCE_AUDITOR" for row in rows["decisions"]),
        "non-Codex provisional actor found",
    )
    require(
        all(row["human_confirmed"] == "false" for row in rows["decisions"]),
        "human review impersonation",
    )
    require(
        all(row["expert_adjudicated"] == "false" for row in rows["decisions"]),
        "expert adjudication impersonation",
    )
    require(
        len(rows["rights"]) == EXPECTED_CANDIDATE_COUNT * len(RIGHTS_DIMENSIONS),
        "rights decision row-count drift",
    )
    rights_pairs = {
        (row["descriptor_assertion_id"], row["purpose"]) for row in rows["rights"]
    }
    require(len(rights_pairs) == len(rows["rights"]), "duplicate purpose-specific rights decision")
    require(
        all(row["rights_state"] in RIGHTS_STATES for row in rows["rights"]),
        "invalid output rights state",
    )
    require(not rows["coassertions"], "rejected non-descriptors cannot create coassertions")

    forbidden_columns = {
        "assertion_text",
        "source_defined_descriptor_key",
        "source_record_key",
        "entry_or_lot_key",
        "coffee_identity_key",
        "official_score_value",
        "official_score_text",
    }
    for name, content in rows.items():
        for row in content:
            require(
                not (set(row) & forbidden_columns),
                f"rights-unsafe field emitted in {name}: {set(row) & forbidden_columns}",
            )


def merge_rows(
    existing: Mapping[str, Sequence[Mapping[str, str]]],
    live: Mapping[str, Sequence[Mapping[str, str]]],
) -> dict[str, list[dict[str, str]]]:
    sort_columns = {
        "ledger": ("descriptor_assertion_id",),
        "queue": ("descriptor_assertion_id",),
        "decisions": ("descriptor_assertion_id",),
        "provenance": ("descriptor_assertion_id",),
        "rights": ("descriptor_assertion_id", "purpose"),
        "publication_layers": ("descriptor_assertion_id",),
        "duplicates": ("descriptor_assertion_id",),
        "normalization": ("descriptor_assertion_id",),
        "coassertions": ("coassertion_event_id",),
        "human_template": ("descriptor_assertion_id",),
        "adjudication_template": ("descriptor_assertion_id",),
    }
    merged: dict[str, list[dict[str, str]]] = {}
    for name, columns in sort_columns.items():
        # Rejected NON_DESCRIPTOR candidates remain in the candidate-review
        # surfaces but must never enter the descriptor assertion ledger.
        content = (
            [dict(row) for row in live[name]]
            if name == "ledger"
            else [dict(row) for row in existing[name]] + [dict(row) for row in live[name]]
        )
        content.sort(key=lambda row: tuple(row[column] for column in columns))
        merged[name] = content
    return merged


def validate_merged_outputs(
    rows: Mapping[str, Sequence[Mapping[str, str]]],
    live_count: int,
) -> None:
    expected_count = EXPECTED_CANDIDATE_COUNT + live_count
    candidate_surface_names = (
        "queue",
        "decisions",
        "provenance",
        "publication_layers",
        "duplicates",
        "normalization",
        "human_template",
        "adjudication_template",
    )
    assertion_sets = {
        name: {row["descriptor_assertion_id"] for row in rows[name]}
        for name in candidate_surface_names
    }
    reference = assertion_sets["queue"]
    require(len(reference) == expected_count, "merged review candidate count drift")
    for name, assertion_set in assertion_sets.items():
        require(assertion_set == reference, f"merged candidate coverage drift in {name}")
        require(len(rows[name]) == expected_count, f"merged row-count drift in {name}")

    ledger_ids = {row["descriptor_assertion_id"] for row in rows["ledger"]}
    require(len(ledger_ids) == live_count, "descriptor ledger live assertion count drift")
    require(ledger_ids <= reference, "descriptor ledger assertion absent from review queue")
    require(
        all(row["descriptor_class"] != "NON_DESCRIPTOR" for row in rows["ledger"]),
        "rejected non-descriptor entered descriptor assertion ledger",
    )

    require(
        len(rows["rights"]) == expected_count * len(RIGHTS_DIMENSIONS),
        "merged purpose-specific rights row-count drift",
    )
    require(
        len(
            {
                (row["descriptor_assertion_id"], row["purpose"])
                for row in rows["rights"]
            }
        )
        == len(rows["rights"]),
        "merged rights decisions are not unique by assertion and purpose",
    )
    require(
        all(row["model_eligible"] == "false" for row in rows["ledger"]),
        "merged provisional ledger contains model-eligible row",
    )
    require(
        all(row["raw_field_text"] == "" for row in rows["ledger"]),
        "raw source text leaked into public ledger",
    )
    require(
        all(row["atomic_source_text"] == "" for row in rows["ledger"]),
        "atomic source text leaked into public ledger",
    )
    require(
        all(row["source_native_lexical_form"] == "" for row in rows["ledger"]),
        "source-native lexical text leaked into public ledger",
    )
    require(
        all(row["normalized_candidate_form"] == "" for row in rows["ledger"]),
        "normalized text leaked into public ledger",
    )
    require(
        all(
            row["review_actor_type"] not in {"HUMAN_REVIEWER", "EXPERT_REVIEWER"}
            for row in rows["decisions"]
        ),
        "merged provisional decision impersonates human/expert review",
    )

    ledger_by_id = {row["descriptor_assertion_id"]: row for row in rows["ledger"]}
    for event in rows["coassertions"]:
        left = ledger_by_id[event["left_descriptor_assertion_id"]]
        right = ledger_by_id[event["right_descriptor_assertion_id"]]
        require(
            left["effective_record_id"] == event["effective_record_id"]
            and right["effective_record_id"] == event["effective_record_id"],
            "coassertion crosses effective-record boundary",
        )
        require(
            left["evidence_tier"] in {"P1", "P2"}
            and right["evidence_tier"] in {"P1", "P2"},
            "coassertion contains non-P1/P2 assertion",
        )
        require(
            event["left_descriptor_assertion_id"] != event["right_descriptor_assertion_id"],
            "self coassertion event",
        )


def build_live_import_receipt(
    live_path: Path,
    live_rows: Sequence[Mapping[str, str]],
    converted: Mapping[str, Sequence[Mapping[str, str]]],
    live_metrics: Mapping[str, object],
) -> dict[str, object]:
    if not live_rows:
        return {
            "receipt_version": "round3m-public-safe-live-assertion-import-v1",
            "input_status": "OPTIONAL_EXPORT_NOT_PRESENT",
            "input_path": "db/adapters/round3m/generated/PUBLIC_SAFE_LIVE_ASSERTIONS.tsv",
            "input_sha256": "NA_FILE_NOT_PRESENT",
            "input_row_count": 0,
            "merged_row_count": 0,
            "human_confirmed_count": 0,
            "model_eligible_count": 0,
            "coassertion_event_count": 0,
        }
    return {
        "receipt_version": "round3m-public-safe-live-assertion-import-v1",
        "input_status": "IMPORTED_PUBLIC_SAFE_HASH_ONLY",
        "input_path": "db/adapters/round3m/generated/PUBLIC_SAFE_LIVE_ASSERTIONS.tsv",
        "input_sha256": sha256_file(live_path),
        "input_row_count": len(live_rows),
        "merged_row_count": len(converted["ledger"]),
        "descriptor_class_distribution": dict(
            sorted(Counter(row["descriptor_class"] for row in live_rows).items())
        ),
        "evidence_tier_distribution": dict(
            sorted(Counter(row["evidence_tier"] for row in live_rows).items())
        ),
        "review_state_distribution": dict(
            sorted(Counter(row["review_state"] for row in live_rows).items())
        ),
        "rights_state_distribution": dict(
            sorted(Counter(row["rights_state"] for row in live_rows).items())
        ),
        "count_disposition_distribution": dict(
            sorted(Counter(row["count_disposition"] for row in live_rows).items())
        ),
        "duplicate_disposition_distribution": dict(
            sorted(
                Counter(
                    row["deduplication_disposition"]
                    for row in converted["duplicates"]
                ).items()
            )
        ),
        "assertion_level_deinflated_count": sum(
            row["counts_as_assertion"] == "true" for row in converted["duplicates"]
        ),
        "record_level_unique_count": sum(
            row["counts_as_record_unique_descriptor"] == "true"
            for row in converted["duplicates"]
        ),
        "source_route_count": len({row["source_route_id"] for row in live_rows}),
        "effective_record_count": len({row["effective_record_id"] for row in live_rows}),
        "full_source_file_hash_count": 0,
        "route_index_hash_count": len(live_rows),
        "explicit_source_file_nonstorage_reason_count": sum(
            bool(row["source_file_nonstorage_reason"]) for row in live_rows
        ),
        "source_text_storage_state": "HASH_ONLY",
        "human_confirmed_count": 0,
        "expert_adjudicated_count": 0,
        "counts_as_reviewed_descriptor_count": 0,
        "model_eligible_count": 0,
        "coassertion_event_count": len(converted["coassertions"]),
        "coassertion_scope": "P2_PRIMARY_JURY_WITHIN_EFFECTIVE_RECORD_HASH_ONLY",
        "restricted_capture_manifest_sha256": live_metrics[
            "restricted_capture_manifest_sha256"
        ],
        "restricted_capture_root_locator": live_metrics[
            "restricted_capture_root_locator"
        ],
        "restricted_capture_manifest_contract": live_metrics[
            "restricted_capture_manifest_contract"
        ],
        "independent_source_body_reproduction_status": (
            "NOT_CLAIMED_ROUTE_INDEX_HASH_ONLY_AND_MACHINE_CENSUS_BUNDLE_MISSING"
        ),
    }


def build_manifest(
    output_dir: Path, paths: Sequence[Path], *, manifest_version: str
) -> dict[str, object]:
    files = []
    for path in sorted(paths, key=lambda candidate: candidate.name):
        with path.open("r", encoding="utf-8", newline="") as stream:
            row_count = sum(1 for _ in stream) - 1 if path.suffix == ".tsv" else None
        files.append(
            {
                "path": path.name,
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
                "data_row_count": row_count,
            }
        )
    return {
        "manifest_version": manifest_version,
        "generator_version": GENERATOR_VERSION,
        "input_checkpoint_at": CHECKPOINT_AT,
        "rights_boundary": "NO_SOURCE_NATIVE_ROW_TEXT_OR_RESULT_IDENTITY_FIELDS",
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restricted-root", required=True, type=Path)
    parser.add_argument("--report-pdf", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--live-assertion-export",
        type=Path,
        default=ROOT
        / "db"
        / "adapters"
        / "round3m"
        / "generated"
        / "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv",
        help="Optional public-safe hash-only live adapter handoff.",
    )
    parser.add_argument(
        "--research-artifact-root",
        action="append",
        type=Path,
        default=[],
        help="Directory to search recursively for the exact machine-readable census bundle.",
    )
    args = parser.parse_args()

    restricted_root = args.restricted_root.resolve()
    output_dir = args.output_dir.resolve()
    require(restricted_root != output_dir, "restricted input and public output must differ")
    require(
        restricted_root not in output_dir.parents,
        "public output cannot be placed inside the restricted checkpoint",
    )

    candidates, record_index, _, source_receipts = validate_inputs(
        restricted_root, args.report_pdf.resolve()
    )
    existing_rows = build_rows(candidates, record_index, source_receipts)
    validate_outputs(existing_rows)
    live_path = args.live_assertion_export.resolve()
    live_input_rows = read_live_assertions(live_path)
    live_metrics = (
        read_live_adapter_metrics(live_path.parent / "LIVE_ADAPTER_METRICS.json")
        if live_input_rows
        else {}
    )
    live_rows = build_live_rows(live_input_rows)
    require(
        not (
            {row["descriptor_assertion_id"] for row in existing_rows["ledger"]}
            & {row["descriptor_assertion_id"] for row in live_rows["ledger"]}
        ),
        "live assertion IDs overlap the existing 376 queue",
    )
    generated_rows = merge_rows(existing_rows, live_rows)
    validate_merged_outputs(generated_rows, len(live_input_rows))
    live_import_receipt = build_live_import_receipt(
        live_path, live_input_rows, live_rows, live_metrics
    )
    c0_c1_receipt = build_c0_c1_receipt(record_index)

    search_roots = [path.resolve() for path in args.research_artifact_root]
    located_machine_artifacts, missing_machine_artifacts = locate_machine_artifacts(search_roots)
    machine_bundle_available = not missing_machine_artifacts
    if machine_bundle_available:
        import_status = "AVAILABLE_NOT_IMPORTED_BY_SCOPED_376_BUILDER"
        blocker_rows: list[dict[str, str]] = []
    else:
        import_status = "BLOCKED_MISSING_MACHINE_ARTIFACTS"
        blocker_rows = [
            {
                "blocker_id": "round3m-missing-machine-readable-descriptor-census",
                "blocker_type": "MISSING_MACHINE_READABLE_RESEARCH_ARTIFACTS",
                "blocker_state": "OPEN",
                "required_artifact_count": str(len(MACHINE_RESEARCH_ARTIFACTS)),
                "available_artifact_count": str(len(located_machine_artifacts)),
                "missing_artifact_names": ";".join(missing_machine_artifacts),
                "effect": (
                    "REPORT_METHODOLOGY_AVAILABLE;303_ASSERTION_ROWS_NOT_IMPORTED_OR_RECONSTRUCTED"
                ),
                "continuation_action": (
                    "PROVIDE_OR_LOCATE_THE_ORIGINAL_NINE_FILE_MACHINE_READABLE_BUNDLE"
                ),
            }
        ]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_specs = (
        ("EXISTING_376_REVIEW_QUEUE.tsv", QUEUE_COLUMNS, existing_rows["queue"]),
        ("DESCRIPTOR_REVIEW_QUEUE.tsv", QUEUE_COLUMNS, generated_rows["queue"]),
        (
            "EXISTING_376_PROVISIONAL_DECISIONS.tsv",
            DECISION_COLUMNS,
            existing_rows["decisions"],
        ),
        (
            "DESCRIPTOR_PROVISIONAL_DECISIONS.tsv",
            DECISION_COLUMNS,
            generated_rows["decisions"],
        ),
        (
            "DESCRIPTOR_ASSERTION_LEDGER.tsv",
            LEDGER_COLUMNS,
            generated_rows["ledger"],
        ),
        (
            "DESCRIPTOR_PROVENANCE_DECISION.tsv",
            PROVENANCE_COLUMNS,
            generated_rows["provenance"],
        ),
        (
            "DESCRIPTOR_RIGHTS_DECISION.tsv",
            RIGHTS_COLUMNS,
            generated_rows["rights"],
        ),
        (
            "PUBLICATION_LAYER_RELATION.tsv",
            PUBLICATION_LAYER_COLUMNS,
            generated_rows["publication_layers"],
        ),
        (
            "DUPLICATE_REPEAT_DECISION.tsv",
            DUPLICATE_COLUMNS,
            generated_rows["duplicates"],
        ),
        (
            "DESCRIPTOR_NORMALIZATION_DECISION.tsv",
            NORMALIZATION_COLUMNS,
            generated_rows["normalization"],
        ),
        ("COASSERTION_EVENT.tsv", COASSERTION_COLUMNS, generated_rows["coassertions"]),
        (
            "HUMAN_REVIEW_IMPORT_TEMPLATE.tsv",
            HUMAN_TEMPLATE_COLUMNS,
            generated_rows["human_template"],
        ),
        (
            "ADJUDICATION_IMPORT_TEMPLATE.tsv",
            ADJUDICATION_TEMPLATE_COLUMNS,
            generated_rows["adjudication_template"],
        ),
        ("EXISTING_376_SOURCE_ARTIFACT_RECEIPT.tsv", SOURCE_ARTIFACT_COLUMNS, source_receipts),
        ("ROUND3M_RESEARCH_ARTIFACT_BLOCKER.tsv", BLOCKER_COLUMNS, blocker_rows),
    )

    generated_paths: list[Path] = []
    for filename, columns, rows in output_specs:
        path = output_dir / filename
        write_tsv(path, columns, rows)
        generated_paths.append(path)

    receipt = {
        "receipt_version": "round3m-existing-376-review-receipt-v1",
        "generator_version": GENERATOR_VERSION,
        "input_checkpoint_at": CHECKPOINT_AT,
        "input_checkpoint_sha256": ROUND3L_CHECKPOINT_SHA256,
        "descriptor_first_report_sha256": DESCRIPTOR_FIRST_REPORT_SHA256,
        "machine_readable_research_artifacts_available": machine_bundle_available,
        "research_artifact_import_status": import_status,
        "machine_artifact_required_count": len(MACHINE_RESEARCH_ARTIFACTS),
        "machine_artifact_available_count": len(located_machine_artifacts),
        "machine_artifact_missing_names": missing_machine_artifacts,
        "report_audit_rows_imported": "NA_MISSING_MACHINE_READABLE_BUNDLE"
        if not machine_bundle_available
        else "NA_SCOPED_BUILDER_DOES_NOT_IMPORT_REPORT_AUDIT_ROWS",
        "report_counts_independently_reproduced": False,
        "existing_candidate_count": EXPECTED_CANDIDATE_COUNT,
        "existing_candidate_dispositioned_count": EXPECTED_CANDIDATE_COUNT,
        "existing_candidate_disposition_completeness_rate": 1.0,
        "source_audit_complete_count": 0,
        "human_review_required_count": 0,
        "source_unavailable_count": 0,
        "non_descriptor_count": EXPECTED_CANDIDATE_COUNT,
        "duplicate_or_repeat_count": 0,
        "publication_layer_conflict_count": 0,
        "provenance_unresolved_count": 0,
        "rights_blocked_count": 0,
        "out_of_core_tier_count": 0,
        "codex_provisional_review_count": EXPECTED_CANDIDATE_COUNT,
        "human_confirmed_review_count": 0,
        "expert_adjudicated_review_count": 0,
        "expert_review_performed": False,
        "reviewed_descriptor_count": 0,
        "model_eligible_descriptor_count": 0,
        "rights_decision_row_count": EXPECTED_CANDIDATE_COUNT * len(RIGHTS_DIMENSIONS),
        "rights_state_distribution": {
            "UNKNOWN": EXPECTED_CANDIDATE_COUNT * len(RIGHTS_DIMENSIONS)
        },
        "rights_state_completeness_rate": 1.0,
        "source_artifact_count": EXPECTED_SOURCE_FILE_COUNT,
        "source_file_hash_completeness_rate": 1.0,
        "candidate_provenance_decision_completeness_rate": 1.0,
        "admitted_label_provenance_completeness_rate": "NA_NO_ADMITTED_DESCRIPTORS",
        "source_native_lexical_form_count_effect": 0,
        "normalized_descriptor_form_count_effect": 0,
        "coassertion_event_count": 0,
        "coassertion_non_generation_reason": "NO_ADMITTED_P1_P2_DESCRIPTOR_ASSERTIONS",
        "decision": {
            "descriptor_class": "NON_DESCRIPTOR",
            "review_state": "REJECTED_NON_DESCRIPTOR",
            "review_actor_type": "CODEX_SOURCE_AUDITOR",
            "disposition": "NON_DESCRIPTOR",
            "reason_code": "CATEGORY_CLASSIFICATION_NOT_FILLED_OBSERVATION",
        },
        "rights_boundary": {
            "source_native_text_emitted": 0,
            "source_defined_category_values_emitted": 0,
            "participant_company_product_fields_emitted": 0,
            "score_fields_emitted": 0,
            "raw_pdf_files_emitted": 0,
            "hashes_and_bounded_locators_emitted": EXPECTED_CANDIDATE_COUNT,
        },
    }
    receipt_path = output_dir / "EXISTING_376_REVIEW_RECEIPT.json"
    write_json(receipt_path, receipt)
    generated_paths.append(receipt_path)

    c0_c1_receipt_path = output_dir / "C0_C1_EVIDENCE_RECEIPT.json"
    write_json(c0_c1_receipt_path, c0_c1_receipt)
    generated_paths.append(c0_c1_receipt_path)

    live_contract_path = output_dir / "LIVE_ASSERTION_EXPORT_CONTRACT.json"
    write_json(
        live_contract_path,
        {
            "contract_version": "round3m-public-safe-live-assertion-export-v1",
            "default_path": "db/adapters/round3m/generated/PUBLIC_SAFE_LIVE_ASSERTIONS.tsv",
            "columns": list(LIVE_ASSERTION_EXPORT_COLUMNS),
            "optional": True,
            "merge_target": "DESCRIPTOR_ASSERTION_LEDGER.tsv",
            "scoped_existing_376_outputs_unchanged": True,
            "constraints": {
                "raw_or_atomic_source_text_columns_allowed": False,
                "raw_and_atomic_sha256_required": True,
                "full_source_file_hash_or_explicit_nonstorage_reason_required": True,
                "human_or_expert_review_state_allowed": False,
                "model_eligible_allowed": False,
                "affirmative_singular_rights_state_allowed": False,
                "governed_restricted_capture_manifest_receipt_required": True,
                "rights_mapping": (
                    "SINGULAR_PENDING_OR_UNKNOWN_IS_CONSERVATIVELY_APPLIED_TO_ALL_SIX_"
                    "PURPOSES_WITH_NO_AFFIRMATIVE_GRANT"
                ),
            },
        },
    )
    generated_paths.append(live_contract_path)

    live_receipt_path = output_dir / "LIVE_ASSERTION_IMPORT_RECEIPT.json"
    write_json(live_receipt_path, live_import_receipt)
    generated_paths.append(live_receipt_path)

    scoped_names = {
        "EXISTING_376_PROVISIONAL_DECISIONS.tsv",
        "EXISTING_376_REVIEW_QUEUE.tsv",
        "EXISTING_376_REVIEW_RECEIPT.json",
        "EXISTING_376_SOURCE_ARTIFACT_RECEIPT.tsv",
    }
    scoped_paths = [path for path in generated_paths if path.name in scoped_names]
    manifest_path = output_dir / "EXISTING_376_REVIEW_MANIFEST.json"
    manifest = build_manifest(
        output_dir,
        scoped_paths,
        manifest_version="round3m-existing-376-public-safe-v1",
    )
    write_json(manifest_path, manifest)

    full_manifest_path = output_dir / "DESCRIPTOR_REVIEW_ARTIFACT_MANIFEST.json"
    full_manifest = build_manifest(
        output_dir,
        [*generated_paths, manifest_path],
        manifest_version="round3m-descriptor-review-artifacts-public-safe-v1",
    )
    write_json(full_manifest_path, full_manifest)

    checksum_paths = sorted(
        [*generated_paths, manifest_path, full_manifest_path], key=lambda path: path.name
    )
    checksum_path = output_dir / "EXISTING_376_SHA256SUMS"
    checksum_path.write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "existing_candidate_count": EXPECTED_CANDIDATE_COUNT,
                "non_descriptor_count": EXPECTED_CANDIDATE_COUNT,
                "reviewed_descriptor_count": 0,
                "human_confirmed_review_count": 0,
                "source_artifact_count": EXPECTED_SOURCE_FILE_COUNT,
                "live_assertion_export_count": len(live_input_rows),
                "merged_descriptor_ledger_count": len(generated_rows["ledger"]),
                "provisional_coassertion_event_count": len(generated_rows["coassertions"]),
                "machine_readable_research_artifacts_available": machine_bundle_available,
                "research_artifact_import_status": import_status,
                "output_dir": str(output_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as error:
        print(f"ROUND3M_REVIEW_ARTIFACT_CONTRACT_ERROR: {error}")
        raise SystemExit(65) from error
