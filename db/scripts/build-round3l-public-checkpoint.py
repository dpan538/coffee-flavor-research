#!/usr/bin/env python3
"""Build a public-safe aggregate receipt for restricted Round 3L ledgers.

The professional acquisition ledgers remain outside Git while their reuse
rights are pending or unknown.  This builder validates the restricted lane and
ingest snapshots, then emits only aggregate counts, safe acquisition metadata,
artifact URL/hash/byte receipts, blocker states, and deterministic cursors.

It deliberately cannot emit record rows, assertion rows, source-native text,
score values, participant names, or OCR output.  Expected snapshot totals are
pinned so a partial or silently changed restricted input fails closed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "db" / "data" / "round3l" / "public"

LANES = (
    "bop_historical_continuation",
    "coe_bop",
    "commercial_regional",
    "golden_bean_ocr_continuation",
    "wcc_body_continuation",
    "wcc_national",
)

NON_WCC_ARTIFACT_LANES = (
    "bop_historical_continuation",
    "coe_bop",
    "commercial_regional",
    "golden_bean_ocr_continuation",
)

EXPECTED_ARTIFACTS_BY_LANE = {
    "bop_historical_continuation": (14, 5_434_816),
    "coe_bop": (517, 140_104_288),
    "commercial_regional": (119, 674_543_488),
    "golden_bean_ocr_continuation": (57, 389_666_008),
    "wcc_body_continuation": (29, 15_284_886),
    "wcc_national": (112, 102_504_011),
}

EXPECTED = {
    "census_items": 480,
    "source_families": 131,
    "editions": 267,
    "attempts": 851,
    "attempted_sources": 296,
    "sources_with_completed_attempt": 259,
    "sources_every_attempt_completed": 252,
    "completed_attempts": 697,
    "artifacts": 848,
    "artifact_bytes": 1_327_537_497,
    "parsed_rows": 26_531,
    "ingested_rows": 26_515,
    "canonical_rows": 20_994,
    "staged_core_candidates": 6_754,
    "emitted_duplicate_publication_losses": 5_090,
    "non_emitted_duplicate_publication_losses": 7,
    "non_admitted_aggregate_components": 9,
    "repeated_service_losses": 431,
    "mirror_losses": 0,
    "staged_gate_type_descriptor_assertions": 376,
    "numeric_structured_score_assertions": 11_418,
    "auxiliary_source_term_assertions": 7,
    "total_assertions": 11_801,
    "open_blockers": 10,
    "resolved_blockers": 1,
    "staged_internal_rights_eligible_core_candidates": 0,
    "staged_model_eligible_records": 0,
    "cross_family_raw_hash_review_groups": 1,
    "cross_family_raw_hash_review_rows": 3,
    "wcc_body_unresolved_conflict_rows": 2,
}

EXPECTED_RESTRICTED_INGEST_CHECKPOINT_SHA256 = (
    "c054e364e5193558c752ce03ff5ec002b807343e00743e7af94676e17cf39e7e"
)
EXPECTED_RESTRICTED_RECEIPT_ROOT_SHA256 = (
    "62c827c0b65029fb99c039445ec88c13b4a122bc7ad001f9c9d36fdac1c33a6a"
)
EXPECTED_AUTHORITATIVE_GATE_INPUT_SHA256 = (
    "be3d7f8078dab0bba14581b74a3a68ab1ead9940be8bbf71b2944fb73fc05ddc"
)

EXPECTED_RIGHTS = {
    "public_results_use": {"PENDING": 15_915, "UNKNOWN": 10_600},
    "public_descriptor_use": {"PENDING": 15_915, "UNKNOWN": 10_600},
    "internal_research_use": {"PENDING": 15_915, "UNKNOWN": 10_600},
    "public_derived_release": {"PENDING": 15_915, "UNKNOWN": 10_600},
    "model_research_use": {"PENDING": 15_915, "UNKNOWN": 10_600},
    "commercial_model_use": {
        "PENDING": 11_969,
        "PROHIBITED": 3_946,
        "UNKNOWN": 10_600,
    },
}

CENSUS_COLUMNS = (
    "census_version",
    "census_item_key",
    "item_kind",
    "parent_key",
    "series_key",
    "source_family_key",
    "edition_label",
    "edition_year",
    "country_or_community",
    "category_or_round",
    "official_url",
    "discovery_basis",
    "source_snapshot_sha256",
    "current_corpus_state",
    "acquisition_state",
    "rights_state",
    "note",
    "discovered_at",
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

SAFE_ATTEMPT_COLUMNS = (
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
    "next_cursor",
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

BLOCKER_COLUMNS = (
    "blocker_key",
    "attempt_key",
    "external_action_type",
    "blocker_state",
    "recorded_at",
    "resolution_evidence",
    "continuation_cursor",
)

SAFE_BLOCKER_COLUMNS = (
    "blocker_key",
    "attempt_key",
    "lane_key",
    "external_action_type",
    "blocker_state",
    "recorded_at",
    "resolution_evidence_present",
    "continuation_cursor",
)

ARTIFACT_COLUMNS = (
    "artifact_receipt_key",
    "lane_key",
    "census_item_key",
    "canonical_url",
    "retrieval_url",
    "http_status",
    "media_type",
    "sha256",
    "byte_count",
    "inventory_basis",
)

WCC_NATIONAL_MANIFEST_COLUMNS = (
    "source_file_id",
    "series_id",
    "edition_year",
    "official_name",
    "canonical_item_url",
    "download_url",
    "filename",
    "sha256",
    "byte_size",
    "media_type",
    "captured_at",
    "rights_statement_uri",
    "public_results_use",
    "public_descriptor_use",
    "internal_research_use",
    "public_derived_release",
    "model_research_use",
    "commercial_model_use",
    "rights_note",
)

WCC_BODY_MANIFEST_COLUMNS = (
    "artifact_key",
    "census_item_key",
    "cache_relpath",
    "canonical_url",
    "http_status",
    "media_type",
    "sha256",
    "byte_count",
    "artifact_role",
    "rights_state",
    "record_count",
    "note",
)

RIGHTS_FIELDS = (
    "public_results_use",
    "public_descriptor_use",
    "internal_research_use",
    "public_derived_release",
    "model_research_use",
    "commercial_model_use",
)

CORE_PAYLOADS = {
    "OFFICIAL_STRUCTURED_SCORE",
    "OFFICIAL_DESCRIPTOR",
    "OFFICIAL_SCORE_AND_DESCRIPTOR",
}

GATE_DESCRIPTOR_ASSERTION_TYPES = {
    "OFFICIAL_JUDGE_DESCRIPTOR",
    "OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR",
    "OFFICIAL_AGGREGATED_DESCRIPTOR",
}

SAFE_OUTPUT_NAMES = (
    "ARTIFACT_MANIFEST.tsv",
    "AUTHORITATIVE_GATE_RECEIPT.json",
    "BLOCKER_QUEUE_PUBLIC.tsv",
    "LANE_METRICS.json",
    "RESTRICTED_LEDGER_RECEIPT.json",
    "SOURCE_ATTEMPTS_PUBLIC.tsv",
)

FORBIDDEN_PUBLIC_COLUMNS = {
    "professional_acquisition_record_key",
    "professional_acquisition_assertion_key",
    "source_record_key",
    "entry_or_lot_key",
    "coffee_identity_key",
    "official_name",
    "official_score_value",
    "official_score_text",
    "official_score_scale",
    "assertion_text",
    "source_defined_descriptor_key",
    "source_native_roast_value",
    "reviewed_c1_mapping",
    "raw_record_sha256",
    "evidence_json",
    "blocker_detail",
    "cache_relpath",
    "filename",
    "ocr_text",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

FREEZE_ID = "round3l-2026-08-28t040000z"
AUTHORITATIVE_GATE_VIEW = "audit.v_round3k_professional_corpus_metrics"
AUTHORITATIVE_GATE_COLUMNS = (
    "observed_core_professional_record_count",
    "model_eligible_core_professional_record_count",
    "professional_descriptor_assertion_count",
)


class ContractError(ValueError):
    """A public-checkpoint contract violation."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    require(path.is_file(), f"missing required ledger: {path}")
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        actual = tuple(reader.fieldnames or ())
        require(
            actual == tuple(columns),
            f"header mismatch for {path}: expected {tuple(columns)!r}, got {actual!r}",
        )
        rows = list(reader)
    for line_number, row in enumerate(rows, start=2):
        require(None not in row, f"extra field in {path}:{line_number}")
        require(
            all("\x00" not in value for value in row.values()),
            f"NUL byte in {path}:{line_number}",
        )
    return rows


def read_json_object(path: Path) -> dict[str, object]:
    require(path.is_file(), f"missing required JSON: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def write_tsv(
    path: Path,
    columns: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> None:
    require(
        not (set(columns) & FORBIDDEN_PUBLIC_COLUMNS),
        "unsafe public TSV columns requested: "
        f"{set(columns) & FORBIDDEN_PUBLIC_COLUMNS}",
    )
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


def write_json(path: Path, value: object) -> None:
    assert_public_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validated_gate_receipt(path: Path) -> dict[str, object]:
    """Validate and sanitize a DB-verified authoritative gate receipt."""
    require(path.is_file(), f"missing authoritative gate receipt: {path}")
    input_sha256 = sha256_file(path)
    require(
        input_sha256 == EXPECTED_AUTHORITATIVE_GATE_INPUT_SHA256,
        "authoritative gate receipt hash drift",
    )
    receipt = read_json_object(path)
    expected_keys = {
        "receipt_schema",
        "freeze_id",
        "verified_at",
        "restricted_manifest_sha256",
        "source_view",
        "verification_environment",
        "query_columns",
        "observed_core_professional_records",
        "model_eligible_core_professional_records",
        "countable_professional_descriptor_assertions",
        "gate_status",
    }
    require(
        set(receipt) == expected_keys,
        f"authoritative gate receipt keys differ: {set(receipt)!r}",
    )
    require(
        receipt["receipt_schema"] == "round3l-authoritative-gate-receipt-v1",
        "invalid authoritative gate receipt schema",
    )
    require(receipt["freeze_id"] == FREEZE_ID, "gate receipt freeze ID drift")
    verified_at = receipt["verified_at"]
    require(
        isinstance(verified_at, str)
        and UTC_TIMESTAMP_RE.fullmatch(verified_at) is not None,
        "invalid authoritative gate verification timestamp",
    )
    require(
        receipt["source_view"] == AUTHORITATIVE_GATE_VIEW,
        "authoritative gate database view drift",
    )
    require(
        receipt["verification_environment"]
        == (
            "PostgreSQL 16.13 disposable integration database; clean "
            "PostgreSQL 17 migration verification is required in CI"
        ),
        "authoritative gate verification-environment drift",
    )
    require(
        receipt["query_columns"] == list(AUTHORITATIVE_GATE_COLUMNS),
        "authoritative gate query-column drift",
    )
    require(
        receipt["restricted_manifest_sha256"]
        == EXPECTED_RESTRICTED_INGEST_CHECKPOINT_SHA256,
        "authoritative gate receipt restricted-manifest hash drift",
    )
    require(
        receipt["observed_core_professional_records"] == 0
        and receipt["model_eligible_core_professional_records"] == 0
        and receipt["countable_professional_descriptor_assertions"] == 0
        and receipt["gate_status"] == "NOT_MET",
        "authoritative gate query result drift",
    )
    return {
        **receipt,
        "verification_status": "VERIFIED",
        "verified_input_sha256": input_sha256,
        "staging_metrics_used_as_authoritative_evidence": False,
        "clean_55_migration_postgresql_17_verification": "DELEGATED_TO_CI",
    }


def assert_public_json(value: object, location: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(
                key not in FORBIDDEN_PUBLIC_COLUMNS,
                f"unsafe public JSON key {key!r} at {location}",
            )
            assert_public_json(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_public_json(child, f"{location}[{index}]")


def require_unique(rows: Sequence[Mapping[str, str]], column: str) -> None:
    counts = Counter(row[column] for row in rows)
    duplicates = sorted(key for key, count in counts.items() if count > 1)
    require(not duplicates, f"duplicate {column}: {duplicates[:5]!r}")


def integer(row: Mapping[str, str], column: str, minimum: int = 0) -> int:
    try:
        value = int(row[column])
    except ValueError as error:
        raise ContractError(
            f"invalid integer {column}={row[column]!r} in {row!r}"
        ) from error
    require(value >= minimum, f"{column} must be >= {minimum}: {value}")
    return value


def receipt_key(lane: str, source_key: str, digest: str) -> str:
    seed = f"{lane}\0{source_key}\0{digest}".encode("utf-8")
    return f"artifact-{hashlib.sha256(seed).hexdigest()[:32]}"


def reconcile_lane_rows(
    ingest_rows: Sequence[dict[str, str]],
    lane_rows: Sequence[dict[str, str]],
    key: str,
    label: str,
) -> None:
    require_unique(ingest_rows, key)
    require_unique(lane_rows, key)
    ingest_by_key = {row[key]: row for row in ingest_rows}
    lane_by_key = {row[key]: row for row in lane_rows}
    require(
        ingest_by_key.keys() == lane_by_key.keys(),
        f"restricted ingest and lane {label} keys differ",
    )
    for row_key, row in lane_by_key.items():
        require(
            ingest_by_key[row_key] == row,
            f"restricted ingest and lane {label} row differ: {row_key}",
        )


def load_inputs(
    lane_root: Path,
    ingest_root: Path,
) -> tuple[
    dict[str, list[dict[str, str]]],
    dict[str, object],
    dict[str, dict[str, list[dict[str, str]]]],
    dict[str, dict[str, object]],
    dict[str, list[dict[str, str]]],
    set[Path],
]:
    input_paths: set[Path] = set()

    def tsv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
        input_paths.add(path)
        return read_tsv(path, columns)

    def json_object(path: Path) -> dict[str, object]:
        input_paths.add(path)
        return read_json_object(path)

    ingest = {
        "census": tsv(ingest_root / "SOURCE_CENSUS.tsv", CENSUS_COLUMNS),
        "attempts": tsv(ingest_root / "SOURCE_ATTEMPTS.tsv", ATTEMPT_COLUMNS),
        "records": tsv(ingest_root / "PROFESSIONAL_RECORDS.tsv", RECORD_COLUMNS),
        "assertions": tsv(
            ingest_root / "PROFESSIONAL_ASSERTIONS.tsv", ASSERTION_COLUMNS
        ),
        "blockers": tsv(ingest_root / "BLOCKER_QUEUE.tsv", BLOCKER_COLUMNS),
    }
    ingest_checkpoint = json_object(ingest_root / "INGESTION_CHECKPOINT.json")

    lane_tables: dict[str, dict[str, list[dict[str, str]]]] = {}
    lane_json: dict[str, dict[str, object]] = {}
    for lane in LANES:
        directory = lane_root / lane
        lane_tables[lane] = {
            "attempts": tsv(directory / "ATTEMPTS.tsv", ATTEMPT_COLUMNS),
            "records": tsv(directory / "RECORDS.tsv", RECORD_COLUMNS),
            "assertions": tsv(directory / "ASSERTIONS.tsv", ASSERTION_COLUMNS),
            "blockers": tsv(directory / "BLOCKERS.tsv", BLOCKER_COLUMNS),
        }
        summary_path = directory / "SUMMARY.json"
        summary = json_object(summary_path) if summary_path.is_file() else {}
        lane_json[lane] = {
            "summary": summary,
            "resume": json_object(directory / "RESUME_MANIFEST.json"),
        }

    manifests = {
        "wcc_national": tsv(
            lane_root / "wcc_national" / "SOURCE_FILE_MANIFEST.tsv",
            WCC_NATIONAL_MANIFEST_COLUMNS,
        ),
        "wcc_body_continuation": tsv(
            lane_root / "wcc_body_continuation" / "SOURCE_FILE_MANIFEST.tsv",
            WCC_BODY_MANIFEST_COLUMNS,
        ),
    }

    return ingest, ingest_checkpoint, lane_tables, lane_json, manifests, input_paths


def validate_cross_lane(
    ingest: Mapping[str, list[dict[str, str]]],
    lane_tables: Mapping[str, Mapping[str, list[dict[str, str]]]],
) -> None:
    for table_name, key in (
        ("attempts", "attempt_key"),
        ("records", "professional_acquisition_record_key"),
        ("assertions", "professional_acquisition_assertion_key"),
    ):
        lane_union = [
            row
            for lane in LANES
            for row in lane_tables[lane][table_name]
        ]
        reconcile_lane_rows(
            ingest[table_name], lane_union, key, table_name
        )

    lane_blockers = [
        row for lane in LANES for row in lane_tables[lane]["blockers"]
    ]
    require_unique(lane_blockers, "blocker_key")
    require_unique(ingest["blockers"], "blocker_key")
    lane_by_key = {row["blocker_key"]: row for row in lane_blockers}
    ingest_by_key = {row["blocker_key"]: row for row in ingest["blockers"]}
    require(
        lane_by_key.keys() == ingest_by_key.keys(),
        "restricted ingest and lane blocker keys differ",
    )
    stable_fields = (
        "blocker_key",
        "attempt_key",
        "external_action_type",
        "recorded_at",
    )
    for blocker_key, lane_row in lane_by_key.items():
        ingest_row = ingest_by_key[blocker_key]
        require(
            all(lane_row[field] == ingest_row[field] for field in stable_fields),
            f"restricted ingest changed blocker identity: {blocker_key}",
        )
        if ingest_row["blocker_state"] == lane_row["blocker_state"]:
            require(
                ingest_row == lane_row,
                f"unresolved blocker row drift: {blocker_key}",
            )
        else:
            require(
                lane_row["blocker_state"] == "OPEN"
                and ingest_row["blocker_state"] in {
                    "AUTHORIZED",
                    "DECLINED",
                    "RESOLVED",
                }
                and bool(ingest_row["resolution_evidence"]),
                f"invalid blocker state transition: {blocker_key}",
            )


def validate_and_measure(
    ingest: Mapping[str, list[dict[str, str]]],
    ingest_checkpoint: Mapping[str, object],
    lane_json: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    census = ingest["census"]
    attempts = ingest["attempts"]
    records = ingest["records"]
    assertions = ingest["assertions"]
    blockers = ingest["blockers"]

    for rows, key in (
        (census, "census_item_key"),
        (attempts, "attempt_key"),
        (records, "professional_acquisition_record_key"),
        (assertions, "professional_acquisition_assertion_key"),
        (blockers, "blocker_key"),
    ):
        require_unique(rows, key)

    census_keys = {row["census_item_key"] for row in census}
    attempts_by_key = {row["attempt_key"]: row for row in attempts}
    records_by_key = {
        row["professional_acquisition_record_key"]: row for row in records
    }
    require(
        all(row["census_item_key"] in census_keys for row in attempts),
        "attempt references a missing census item",
    )
    require(
        all(row["attempt_key"] in attempts_by_key for row in records),
        "record references a missing attempt",
    )
    require(
        all(
            row["professional_acquisition_record_key"] in records_by_key
            for row in assertions
        ),
        "assertion references a missing record",
    )
    require(
        all(row["attempt_key"] in attempts_by_key for row in blockers),
        "blocker references a missing attempt",
    )

    require(
        all(row["is_synthetic"] == "false" for row in records),
        "synthetic record present in restricted ingestion",
    )
    require(
        all(row["semantic_inference_used"] == "false" for row in records),
        "record uses semantic inference",
    )
    require(
        all(row["semantic_inference_used"] == "false" for row in assertions),
        "assertion uses semantic inference",
    )
    require(
        all(row["assertion_text"] == "" for row in assertions),
        "restricted assertion plaintext is not eligible for a public receipt",
    )
    require(
        all(row["text_storage_state"] == "HASH_ONLY" for row in assertions),
        "restricted assertion is not hash-only",
    )
    require(
        all(row["corpus_state"] == "RESEARCH_STAGED" for row in records),
        "record is outside the expected RESEARCH_STAGED state",
    )

    record_count_by_attempt = Counter(row["attempt_key"] for row in records)
    gate_assertion_count_by_attempt = Counter(
        records_by_key[row["professional_acquisition_record_key"]]["attempt_key"]
        for row in assertions
        if row["assertion_type"] in GATE_DESCRIPTOR_ASSERTION_TYPES
    )
    for attempt in attempts:
        attempt_key = attempt["attempt_key"]
        require(
            integer(attempt, "normalized_record_count")
            == record_count_by_attempt[attempt_key],
            f"normalized record count drift: {attempt_key}",
        )
        require(
            integer(attempt, "descriptor_assertion_count")
            == gate_assertion_count_by_attempt[attempt_key],
            f"descriptor assertion count drift: {attempt_key}",
        )

    staged_core = [
        row
        for row in records
        if row["evidence_tier"] in {"P1", "P2"}
        and row["payload_kind"] in CORE_PAYLOADS
        and row["fresh_preparation_status"] == "CONFIRMED"
        and bool(row["effective_record_key"])
        and row["deduplication_disposition"] == "CANONICAL"
    ]
    observed = [
        row for row in staged_core if row["internal_research_use"] == "ALLOWED"
    ]
    model_eligible = [
        row
        for row in observed
        if row["model_research_use"] == "ALLOWED"
        and row["corpus_state"] == "MODEL_ELIGIBLE"
    ]

    staged_gate_descriptors = sum(
        row["assertion_type"] in GATE_DESCRIPTOR_ASSERTION_TYPES
        for row in assertions
    )
    structured_scores = sum(
        row["assertion_type"] == "OFFICIAL_STRUCTURED_SCORE"
        for row in assertions
    )
    auxiliary_assertions = len(assertions) - staged_gate_descriptors - structured_scores
    dedup = Counter(row["deduplication_disposition"] for row in records)
    blocker_states = Counter(row["blocker_state"] for row in blockers)

    non_emitted_duplicates = lane_json["wcc_body_continuation"]["summary"]
    require(isinstance(non_emitted_duplicates, dict), "invalid WCC body summary")
    losses = non_emitted_duplicates.get("losses")
    require(isinstance(losses, dict), "missing WCC body loss metrics")
    wcc_non_emitted_duplicates = losses.get(
        "duplicate_publication_rows_not_emitted"
    )
    wcc_unresolved_conflicts = losses.get("unresolved_conflict_rows")
    national_summary = lane_json["wcc_national"]["summary"]
    require(isinstance(national_summary, dict), "invalid WCC national summary")
    non_admitted_aggregates = national_summary.get(
        "non_admitted_final_aggregate_components"
    )

    attempts_by_census: dict[str, list[dict[str, str]]] = defaultdict(list)
    for attempt in attempts:
        attempts_by_census[attempt["census_item_key"]].append(attempt)

    records_by_raw_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        records_by_raw_hash[record["raw_record_sha256"]].append(record)
    cross_family_raw_hash_review = [
        group
        for group in records_by_raw_hash.values()
        if len({row["source_family_key"] for row in group}) > 1
    ]

    metrics = {
        "census_items": len(census),
        "source_families": len({row["source_family_key"] for row in census}),
        "editions": sum(
            row["item_kind"] in {"COMPETITION_EDITION", "PILOT_EDITION"}
            for row in census
        ),
        "attempts": len(attempts),
        "attempted_sources": len({row["census_item_key"] for row in attempts}),
        "sources_with_completed_attempt": len(
            {
                row["census_item_key"]
                for row in attempts
                if row["outcome"] == "COMPLETED"
            }
        ),
        "sources_every_attempt_completed": sum(
            all(row["outcome"] == "COMPLETED" for row in source_attempts)
            for source_attempts in attempts_by_census.values()
        ),
        "completed_attempts": sum(
            row["outcome"] == "COMPLETED" for row in attempts
        ),
        "parsed_rows": sum(integer(row, "parsed_row_count") for row in attempts),
        "ingested_rows": len(records),
        "canonical_rows": dedup["CANONICAL"],
        "staged_core_candidates": len(staged_core),
        "emitted_duplicate_publication_losses": dedup["DUPLICATE_PUBLICATION"],
        "non_emitted_duplicate_publication_losses": wcc_non_emitted_duplicates,
        "non_admitted_aggregate_components": non_admitted_aggregates,
        "repeated_service_losses": dedup["REPEATED_SERVICE"],
        "mirror_losses": dedup["MIRROR"],
        "staged_gate_type_descriptor_assertions": staged_gate_descriptors,
        "numeric_structured_score_assertions": structured_scores,
        "auxiliary_source_term_assertions": auxiliary_assertions,
        "total_assertions": len(assertions),
        "open_blockers": blocker_states["OPEN"],
        "resolved_blockers": blocker_states["RESOLVED"],
        "staged_internal_rights_eligible_core_candidates": len(observed),
        "staged_model_eligible_records": len(model_eligible),
        "cross_family_raw_hash_review_groups": len(
            cross_family_raw_hash_review
        ),
        "cross_family_raw_hash_review_rows": sum(
            len(group) for group in cross_family_raw_hash_review
        ),
        "wcc_body_unresolved_conflict_rows": wcc_unresolved_conflicts,
    }
    for key, expected in EXPECTED.items():
        if key in {"artifacts", "artifact_bytes"}:
            continue
        require(
            metrics[key] == expected,
            f"snapshot metric drift for {key}: expected {expected}, got {metrics[key]}",
        )

    require(
        dedup["CANONICAL"]
        + dedup["DUPLICATE_PUBLICATION"]
        + dedup["REPEATED_SERVICE"]
        + dedup["MIRROR"]
        == len(records),
        "unrecognized deduplication disposition",
    )

    rights_by_dimension = {
        field: dict(sorted(Counter(row[field] for row in records).items()))
        for field in RIGHTS_FIELDS
    }
    require(
        rights_by_dimension == EXPECTED_RIGHTS,
        f"rights distribution drift: {rights_by_dimension!r}",
    )
    rights_joint = Counter(
        tuple(row[field] for field in RIGHTS_FIELDS) for row in records
    )

    checkpoint_metrics = ingest_checkpoint.get("metrics")
    require(
        isinstance(checkpoint_metrics, dict),
        "invalid restricted checkpoint metrics",
    )
    require(
        checkpoint_metrics.get("ingested_records") == EXPECTED["ingested_rows"],
        "restricted checkpoint ingested-record count drift",
    )
    require(
        checkpoint_metrics.get("staged_core_candidates")
        == EXPECTED["staged_core_candidates"],
        "restricted checkpoint staged-core count drift",
    )
    require(
        checkpoint_metrics.get("cross_family_raw_hash_review_groups")
        == EXPECTED["cross_family_raw_hash_review_groups"],
        "restricted checkpoint cross-family review-group count drift",
    )
    require(
        checkpoint_metrics.get("cross_family_raw_hash_review_rows")
        == EXPECTED["cross_family_raw_hash_review_rows"],
        "restricted checkpoint cross-family review-row count drift",
    )

    return {
        "metrics": metrics,
        "rights_by_dimension": rights_by_dimension,
        "rights_joint": [
            {
                **{field: values[index] for index, field in enumerate(RIGHTS_FIELDS)},
                "record_count": count,
            }
            for values, count in sorted(rights_joint.items())
        ],
        "record_payload_distribution": dict(
            sorted(Counter(row["payload_kind"] for row in records).items())
        ),
        "evidence_tier_distribution": dict(
            sorted(Counter(row["evidence_tier"] for row in records).items())
        ),
        "corpus_state_distribution": dict(
            sorted(Counter(row["corpus_state"] for row in records).items())
        ),
        "census_state_distribution": dict(
            sorted(Counter(row["current_corpus_state"] for row in census).items())
        ),
        "attempt_outcome_distribution": dict(
            sorted(Counter(row["outcome"] for row in attempts).items())
        ),
        "preparation_service_coverage": dict(
            sorted(
                Counter(
                    row["preparation_service_code"] or "UNRESOLVED"
                    for row in records
                ).items()
            )
        ),
        "fresh_preparation_status": dict(
            sorted(Counter(row["fresh_preparation_status"] for row in records).items())
        ),
        "c0_evidence_status": dict(
            sorted(Counter(row["c0_source_status"] for row in records).items())
        ),
        "c1_evidence_status": dict(
            sorted(Counter(row["c1_evidence_status"] for row in records).items())
        ),
        "checkpoint_at": max(row["attempted_at"] for row in attempts),
        "census_version": census[0]["census_version"],
    }


def build_artifact_rows(
    lane_tables: Mapping[str, Mapping[str, list[dict[str, str]]]],
    manifests: Mapping[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for lane in NON_WCC_ARTIFACT_LANES:
        for attempt in lane_tables[lane]["attempts"]:
            digest = attempt["source_snapshot_sha256"]
            byte_count = integer(attempt, "artifact_byte_count")
            require(
                bool(digest) == (byte_count > 0),
                f"artifact hash/byte mismatch: {attempt['attempt_key']}",
            )
            if not digest:
                continue
            require(SHA256_RE.fullmatch(digest) is not None, "invalid artifact SHA-256")
            rows.append(
                {
                    "artifact_receipt_key": receipt_key(
                        lane, attempt["attempt_key"], digest
                    ),
                    "lane_key": lane,
                    "census_item_key": attempt["census_item_key"],
                    "canonical_url": attempt["canonical_url"],
                    "retrieval_url": attempt["final_url"],
                    "http_status": attempt["http_status"],
                    "media_type": "",
                    "sha256": digest,
                    "byte_count": byte_count,
                    "inventory_basis": "HASHED_ATTEMPT",
                }
            )

    national_attempts_by_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for attempt in lane_tables["wcc_national"]["attempts"]:
        national_attempts_by_hash[attempt["source_snapshot_sha256"]].append(attempt)
    for source in manifests["wcc_national"]:
        digest = source["sha256"]
        require(SHA256_RE.fullmatch(digest) is not None, "invalid WCC artifact SHA-256")
        matching_attempts = national_attempts_by_hash[digest]
        require(
            len(matching_attempts) == 1,
            f"WCC national artifact does not map to one attempt: {digest}",
        )
        attempt = matching_attempts[0]
        require(
            integer(source, "byte_size", 1)
            == integer(attempt, "artifact_byte_count", 1),
            f"WCC national artifact byte drift: {digest}",
        )
        rows.append(
            {
                "artifact_receipt_key": receipt_key(
                    "wcc_national", source["source_file_id"], digest
                ),
                "lane_key": "wcc_national",
                "census_item_key": attempt["census_item_key"],
                "canonical_url": source["canonical_item_url"],
                "retrieval_url": source["download_url"],
                "http_status": attempt["http_status"],
                "media_type": source["media_type"],
                "sha256": digest,
                "byte_count": integer(source, "byte_size", 1),
                "inventory_basis": "SOURCE_FILE_MANIFEST",
            }
        )

    body_attempt_census = {
        row["census_item_key"]
        for row in lane_tables["wcc_body_continuation"]["attempts"]
    }
    for source in manifests["wcc_body_continuation"]:
        digest = source["sha256"]
        require(SHA256_RE.fullmatch(digest) is not None, "invalid WCC body SHA-256")
        require(
            source["census_item_key"] in body_attempt_census,
            f"WCC body artifact has no attempt: {source['artifact_key']}",
        )
        rows.append(
            {
                "artifact_receipt_key": receipt_key(
                    "wcc_body_continuation", source["artifact_key"], digest
                ),
                "lane_key": "wcc_body_continuation",
                "census_item_key": source["census_item_key"],
                "canonical_url": source["canonical_url"],
                "retrieval_url": source["canonical_url"],
                "http_status": source["http_status"],
                "media_type": source["media_type"],
                "sha256": digest,
                "byte_count": integer(source, "byte_count", 1),
                "inventory_basis": "SOURCE_FILE_MANIFEST",
            }
        )

    require_unique(rows, "artifact_receipt_key")
    by_lane = defaultdict(list)
    for row in rows:
        by_lane[str(row["lane_key"])].append(row)
    for lane, (expected_count, expected_bytes) in EXPECTED_ARTIFACTS_BY_LANE.items():
        actual_count = len(by_lane[lane])
        actual_bytes = sum(int(row["byte_count"]) for row in by_lane[lane])
        require(
            (actual_count, actual_bytes) == (expected_count, expected_bytes),
            f"artifact inventory drift for {lane}: "
            f"expected {(expected_count, expected_bytes)}, "
            f"got {(actual_count, actual_bytes)}",
        )

    require(len(rows) == EXPECTED["artifacts"], "total artifact count drift")
    require(
        sum(int(row["byte_count"]) for row in rows)
        == EXPECTED["artifact_bytes"],
        "total artifact byte count drift",
    )
    return sorted(
        rows,
        key=lambda row: (str(row["lane_key"]), str(row["artifact_receipt_key"])),
    )


def safe_cursors(
    lane_json: Mapping[str, Mapping[str, object]],
    lane_tables: Mapping[str, Mapping[str, list[dict[str, str]]]],
) -> dict[str, dict[str, object]]:
    selections = {
        "bop_historical_continuation": (
            "next_edition_or_cursor",
            "next_action",
        ),
        "coe_bop": ("next_edition_or_cursor", "next_action"),
        "commercial_regional": (
            "exact_next_edition",
            "exact_archive_cursor",
            "exact_next_action",
        ),
        "golden_bean_ocr_continuation": (
            "exact_next_edition",
            "exact_archive_cursor",
            "exact_next_action",
        ),
        "wcc_body_continuation": ("next_census_item_key", "next_action"),
        "wcc_national": ("next_census_item_key", "next_action"),
    }
    expected_cursors = {
        "bop_historical_continuation": "official-scap-archive-2003",
        "coe_bop": "farm-directory-page-105",
        "commercial_regional": "golden_bean/gba_2023_category_01.pdf page 1",
        "golden_bean_ocr_continuation": (
            "golden_bean/gba_2023_category_01.pdf page 4 card segmentation review"
        ),
        "wcc_body_continuation": "source:wcc_cb_recdwegkkkkomky5z",
        "wcc_national": "source:wcc_cb_rec0zgr8vngzfsqhw",
    }
    cursor_field = {
        "bop_historical_continuation": "next_edition_or_cursor",
        "coe_bop": "next_edition_or_cursor",
        "commercial_regional": "exact_archive_cursor",
        "golden_bean_ocr_continuation": "exact_archive_cursor",
        "wcc_body_continuation": "next_census_item_key",
        "wcc_national": "next_census_item_key",
    }

    result: dict[str, dict[str, object]] = {}
    for lane in LANES:
        resume = lane_json[lane]["resume"]
        require(isinstance(resume, dict), f"invalid resume manifest: {lane}")
        selected = {key: resume.get(key) for key in selections[lane]}
        require(
            all(value not in {None, ""} for value in selected.values()),
            f"incomplete continuation cursor: {lane}",
        )
        require(
            selected[cursor_field[lane]] == expected_cursors[lane],
            f"continuation cursor drift: {lane}",
        )
        selected["latest_attempt_sequence"] = max(
            integer(row, "attempt_sequence")
            for row in lane_tables[lane]["attempts"]
        )
        result[lane] = selected
    return result


def build_lane_metrics(
    ingest: Mapping[str, list[dict[str, str]]],
    lane_tables: Mapping[str, Mapping[str, list[dict[str, str]]]],
    lane_json: Mapping[str, Mapping[str, object]],
    artifact_rows: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    attempts_by_key = {
        row["attempt_key"]: row for row in ingest["attempts"]
    }
    record_lane = {
        row["professional_acquisition_record_key"]: attempts_by_key[
            row["attempt_key"]
        ]["lane_key"]
        for row in ingest["records"]
    }
    artifacts_by_lane = Counter(str(row["lane_key"]) for row in artifact_rows)
    artifact_bytes_by_lane = Counter()
    for row in artifact_rows:
        artifact_bytes_by_lane[str(row["lane_key"])] += int(row["byte_count"])

    cursors = safe_cursors(lane_json, lane_tables)
    lanes: dict[str, object] = {}
    for lane in LANES:
        attempts = lane_tables[lane]["attempts"]
        records = lane_tables[lane]["records"]
        assertions = lane_tables[lane]["assertions"]
        blockers = [
            row
            for row in ingest["blockers"]
            if attempts_by_key[row["attempt_key"]]["lane_key"] == lane
        ]
        staged_core = sum(
            row["evidence_tier"] in {"P1", "P2"}
            and row["payload_kind"] in CORE_PAYLOADS
            and row["fresh_preparation_status"] == "CONFIRMED"
            and bool(row["effective_record_key"])
            and row["deduplication_disposition"] == "CANONICAL"
            for row in records
        )
        descriptor_assertions = sum(
            row["assertion_type"] in GATE_DESCRIPTOR_ASSERTION_TYPES
            for row in assertions
        )
        structured_scores = sum(
            row["assertion_type"] == "OFFICIAL_STRUCTURED_SCORE"
            for row in assertions
        )
        non_emitted_duplicates = 0
        unresolved_conflicts = 0
        if lane == "wcc_body_continuation":
            summary = lane_json[lane]["summary"]
            require(isinstance(summary, dict), "invalid WCC body summary")
            losses = summary.get("losses")
            require(isinstance(losses, dict), "missing WCC body losses")
            value = losses.get("duplicate_publication_rows_not_emitted")
            require(isinstance(value, int), "invalid WCC body duplicate loss")
            non_emitted_duplicates = value
            conflict_value = losses.get("unresolved_conflict_rows")
            require(
                isinstance(conflict_value, int),
                "invalid WCC body conflict count",
            )
            unresolved_conflicts = conflict_value

        rights = {
            field: dict(sorted(Counter(row[field] for row in records).items()))
            for field in RIGHTS_FIELDS
        }
        lanes[lane] = {
            "artifacts": {
                "count": artifacts_by_lane[lane],
                "bytes": artifact_bytes_by_lane[lane],
            },
            "attempts": {
                "count": len(attempts),
                "sources_attempted": len(
                    {row["census_item_key"] for row in attempts}
                ),
                "sources_with_completed_attempt": len(
                    {
                        row["census_item_key"]
                        for row in attempts
                        if row["outcome"] == "COMPLETED"
                    }
                ),
                "outcomes": dict(
                    sorted(Counter(row["outcome"] for row in attempts).items())
                ),
                "parsed_rows": sum(
                    integer(row, "parsed_row_count") for row in attempts
                ),
            },
            "records": {
                "ingested": len(records),
                "canonical": sum(
                    row["deduplication_disposition"] == "CANONICAL"
                    for row in records
                ),
                "staged_core_candidates": staged_core,
                "observed_core": 0,
                "model_eligible": 0,
                "payload_distribution": dict(
                    sorted(Counter(row["payload_kind"] for row in records).items())
                ),
            },
            "assertions": {
                "staged_gate_type_descriptors": descriptor_assertions,
                "numeric_structured_scores": structured_scores,
                "auxiliary_source_terms": (
                    len(assertions) - descriptor_assertions - structured_scores
                ),
            },
            "losses": {
                "emitted_duplicate_publications": sum(
                    row["deduplication_disposition"] == "DUPLICATE_PUBLICATION"
                    for row in records
                ),
                "non_emitted_duplicate_publications": non_emitted_duplicates,
                "repeated_services": sum(
                    row["deduplication_disposition"] == "REPEATED_SERVICE"
                    for row in records
                ),
                "mirrors": sum(
                    row["deduplication_disposition"] == "MIRROR"
                    for row in records
                ),
            },
            "preparation": {
                "service_distribution": dict(
                    sorted(
                        Counter(
                            row["preparation_service_code"] or "UNRESOLVED"
                            for row in records
                        ).items()
                    )
                ),
                "fresh_status_distribution": dict(
                    sorted(
                        Counter(
                            row["fresh_preparation_status"] for row in records
                        ).items()
                    )
                ),
            },
            "c0_evidence_status": dict(
                sorted(Counter(row["c0_source_status"] for row in records).items())
            ),
            "c1_evidence_status": dict(
                sorted(Counter(row["c1_evidence_status"] for row in records).items())
            ),
            "rights_by_dimension": rights,
            "blockers": dict(
                sorted(Counter(row["blocker_state"] for row in blockers).items())
            ),
            "unresolved_review_inventory": {
                "source_conflict_rows": unresolved_conflicts,
                "automatically_collapsed_rows": 0,
            },
            "continuation": cursors[lane],
        }

    require(
        len(record_lane) == EXPECTED["ingested_rows"],
        "lane record mapping count drift",
    )
    return {
        "phase_status": "IN_PROGRESS_ACQUISITION",
        "lane_count": len(LANES),
        "lanes": lanes,
    }


def safe_attempt_rows(
    attempts: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    rows = [
        {column: row[column] for column in SAFE_ATTEMPT_COLUMNS}
        for row in attempts
    ]
    return sorted(
        rows,
        key=lambda row: (
            row["lane_key"],
            int(row["attempt_sequence"]),
            row["attempt_key"],
        ),
    )


def safe_blocker_rows(
    blockers: Sequence[Mapping[str, str]],
    attempts: Sequence[Mapping[str, str]],
) -> list[dict[str, object]]:
    attempts_by_key = {row["attempt_key"]: row for row in attempts}
    rows = []
    for blocker in blockers:
        attempt = attempts_by_key[blocker["attempt_key"]]
        rows.append(
            {
                "blocker_key": blocker["blocker_key"],
                "attempt_key": blocker["attempt_key"],
                "lane_key": attempt["lane_key"],
                "external_action_type": blocker["external_action_type"],
                "blocker_state": blocker["blocker_state"],
                "recorded_at": blocker["recorded_at"],
                "resolution_evidence_present": str(
                    bool(blocker["resolution_evidence"])
                ).lower(),
                "continuation_cursor": blocker["continuation_cursor"],
            }
        )
    return sorted(rows, key=lambda row: str(row["blocker_key"]))


def logical_input_path(path: Path, lane_root: Path, ingest_root: Path) -> str:
    try:
        return f"restricted_lanes/{path.relative_to(lane_root).as_posix()}"
    except ValueError:
        pass
    try:
        return f"restricted_ingest/{path.relative_to(ingest_root).as_posix()}"
    except ValueError as error:
        raise ContractError(
            f"input path is outside restricted roots: {path}"
        ) from error


def build_restricted_receipt(
    input_paths: Iterable[Path],
    lane_root: Path,
    ingest_root: Path,
    checkpoint_at: str,
) -> dict[str, object]:
    entries = []
    for path in sorted(
        input_paths,
        key=lambda item: logical_input_path(item, lane_root, ingest_root),
    ):
        logical_path = logical_input_path(path, lane_root, ingest_root)
        row_count: int | None = None
        if path.suffix == ".tsv":
            with path.open("r", encoding="utf-8", newline="") as stream:
                row_count = max(sum(1 for _line in stream) - 1, 0)
        entries.append(
            {
                "logical_path": logical_path,
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
                "data_row_count": row_count,
            }
        )
    root_digest = hashlib.sha256()
    for entry in entries:
        root_digest.update(
            (
                f"{entry['logical_path']}\t{entry['sha256']}\t"
                f"{entry['byte_count']}\t{entry['data_row_count']}\n"
            ).encode("utf-8")
        )
    return {
        "receipt_version": "round3l-restricted-ledger-receipt-v1",
        "checkpoint_at": checkpoint_at,
        "restricted_inputs_tracked_in_git": False,
        "file_count": len(entries),
        "receipt_root_sha256": root_digest.hexdigest(),
        "files": entries,
    }


def output_receipts(output_dir: Path) -> list[dict[str, object]]:
    receipts = []
    for name in SAFE_OUTPUT_NAMES:
        path = output_dir / name
        require(path.is_file(), f"missing generated public output: {path}")
        receipts.append(
            {
                "path": name,
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
            }
        )
    return receipts


def build_checkpoint(
    aggregate: Mapping[str, object],
    artifacts: Sequence[Mapping[str, object]],
    blockers: Sequence[Mapping[str, object]],
    lane_metrics: Mapping[str, object],
    restricted_receipt: Mapping[str, object],
    gate_receipt: Mapping[str, object],
    public_receipts: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    metrics = aggregate["metrics"]
    require(isinstance(metrics, dict), "invalid aggregate metrics")
    lanes = lane_metrics["lanes"]
    require(isinstance(lanes, dict), "invalid lane metrics")
    continuation = {}
    for lane, lane_value in lanes.items():
        require(isinstance(lane_value, dict), f"invalid lane metric: {lane}")
        cursor = lane_value.get("continuation")
        require(isinstance(cursor, dict), f"missing lane cursor: {lane}")
        continuation[lane] = cursor
    return {
        "checkpoint_schema": "round3l-public-aggregate-v1",
        "phase_status": "IN_PROGRESS_ACQUISITION",
        "checkpoint_at": aggregate["checkpoint_at"],
        "census_version": aggregate["census_version"],
        "source_universe": {
            "discovered_source_families": metrics["source_families"],
            "discovered_editions": metrics["editions"],
            "census_items": metrics["census_items"],
            "attempted_sources": metrics["attempted_sources"],
            "sources_with_completed_attempt": metrics[
                "sources_with_completed_attempt"
            ],
            "sources_every_attempt_completed": metrics[
                "sources_every_attempt_completed"
            ],
            "source_completion_note": (
                "These are attempt-state aggregates, not source-terminal or "
                "archive-exhaustion claims."
            ),
            "attempt_count": metrics["attempts"],
            "completed_attempt_count": metrics["completed_attempts"],
            "census_state_distribution": aggregate[
                "census_state_distribution"
            ],
            "attempt_outcome_distribution": aggregate[
                "attempt_outcome_distribution"
            ],
        },
        "acquisition": {
            "artifact_count": len(artifacts),
            "artifact_bytes": sum(int(row["byte_count"]) for row in artifacts),
            "parsed_rows": metrics["parsed_rows"],
            "ingested_rows": metrics["ingested_rows"],
            "canonical_rows": metrics["canonical_rows"],
            "record_payload_distribution": aggregate[
                "record_payload_distribution"
            ],
            "evidence_tier_distribution": aggregate[
                "evidence_tier_distribution"
            ],
            "corpus_state_distribution": aggregate[
                "corpus_state_distribution"
            ],
        },
        "staging_inventory": {
            "staged_core_candidates": metrics["staged_core_candidates"],
            "staged_internal_rights_eligible_core_candidates": metrics[
                "staged_internal_rights_eligible_core_candidates"
            ],
            "staged_model_eligible_records": metrics[
                "staged_model_eligible_records"
            ],
            "staged_gate_type_descriptor_assertions": metrics[
                "staged_gate_type_descriptor_assertions"
            ],
            "numeric_structured_score_assertions": metrics[
                "numeric_structured_score_assertions"
            ],
            "auxiliary_source_term_assertions": metrics[
                "auxiliary_source_term_assertions"
            ],
            "total_assertions": metrics["total_assertions"],
            "promotion_note": (
                "Restricted staging has not been promoted into the Round 3K "
                "governed source and preparation structures."
            ),
        },
        "authoritative_round3k_gate": {
            "observed_core_professional_records": gate_receipt[
                "observed_core_professional_records"
            ],
            "model_eligible_records": gate_receipt[
                "model_eligible_core_professional_records"
            ],
            "countable_descriptor_assertions": gate_receipt[
                "countable_professional_descriptor_assertions"
            ],
            "gate_status": "NOT_MET",
            "verification_status": gate_receipt["verification_status"],
            "verified_at": gate_receipt["verified_at"],
            "evidence_receipt": "AUTHORITATIVE_GATE_RECEIPT.json",
            "remaining_observed_records_to_7000": 7_000,
            "remaining_observed_records_to_10000": 10_000,
            "remaining_countable_descriptors_to_40000": 40_000,
            "remaining_countable_descriptors_to_60000": 60_000,
        },
        "rights_state_distribution": {
            "by_dimension": aggregate["rights_by_dimension"],
            "joint": aggregate["rights_joint"],
        },
        "preparation_service_coverage": aggregate[
            "preparation_service_coverage"
        ],
        "fresh_preparation_status": aggregate["fresh_preparation_status"],
        "c0_evidence_status": aggregate["c0_evidence_status"],
        "c1_evidence_status": aggregate["c1_evidence_status"],
        "losses": {
            "emitted_duplicate_publication_rows": metrics[
                "emitted_duplicate_publication_losses"
            ],
            "non_emitted_duplicate_publication_rows": metrics[
                "non_emitted_duplicate_publication_losses"
            ],
            "non_admitted_aggregate_components": metrics[
                "non_admitted_aggregate_components"
            ],
            "repeated_service_rows": metrics["repeated_service_losses"],
            "mirror_rows": metrics["mirror_losses"],
        },
        "unresolved_review_inventory": {
            "cross_family_raw_hash_review_groups": metrics[
                "cross_family_raw_hash_review_groups"
            ],
            "cross_family_raw_hash_review_rows": metrics[
                "cross_family_raw_hash_review_rows"
            ],
            "wcc_body_source_conflict_rows": metrics[
                "wcc_body_unresolved_conflict_rows"
            ],
            "review_state": "OPEN_NO_AUTOMATIC_COLLAPSE",
            "automatically_collapsed_rows": 0,
            "counted_as_losses": False,
        },
        "blockers": {
            "open": metrics["open_blockers"],
            "resolved": metrics["resolved_blockers"],
            "queue_rows": len(blockers),
        },
        "continuation_cursor": continuation,
        "restricted_ledger_receipt_root_sha256": restricted_receipt[
            "receipt_root_sha256"
        ],
        "public_output_receipts": list(public_receipts),
        "public_boundary": {
            "record_rows_emitted": 0,
            "assertion_rows_emitted": 0,
            "participant_company_product_result_fields_emitted": 0,
            "score_values_or_text_emitted": 0,
            "source_native_descriptors_emitted": 0,
            "raw_ocr_emitted": 0,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--restricted-root",
        type=Path,
        required=True,
        help="root containing restricted_lanes/ and restricted_ingest/",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="public aggregate output directory",
    )
    parser.add_argument(
        "--gate-receipt",
        type=Path,
        required=True,
        help=(
            "JSON receipt from a verified query of "
            "audit.v_round3k_professional_corpus_metrics"
        ),
    )
    args = parser.parse_args()

    lane_root = args.restricted_root / "restricted_lanes"
    ingest_root = args.restricted_root / "restricted_ingest"
    output_dir = args.output_dir
    gate_receipt = validated_gate_receipt(args.gate_receipt)

    (
        ingest,
        ingest_checkpoint,
        lane_tables,
        lane_json,
        manifests,
        input_paths,
    ) = load_inputs(lane_root, ingest_root)
    validate_cross_lane(ingest, lane_tables)
    aggregate = validate_and_measure(ingest, ingest_checkpoint, lane_json)
    artifact_rows = build_artifact_rows(lane_tables, manifests)

    metrics = aggregate["metrics"]
    require(isinstance(metrics, dict), "invalid aggregate metrics")
    metrics["artifacts"] = len(artifact_rows)
    metrics["artifact_bytes"] = sum(
        int(row["byte_count"]) for row in artifact_rows
    )
    require(metrics["artifacts"] == EXPECTED["artifacts"], "artifact count drift")
    require(
        metrics["artifact_bytes"] == EXPECTED["artifact_bytes"],
        "artifact byte count drift",
    )

    lane_metrics = build_lane_metrics(
        ingest, lane_tables, lane_json, artifact_rows
    )
    blocker_rows = safe_blocker_rows(ingest["blockers"], ingest["attempts"])
    restricted_receipt = build_restricted_receipt(
        input_paths,
        lane_root,
        ingest_root,
        str(aggregate["checkpoint_at"]),
    )
    require(
        sha256_file(ingest_root / "INGESTION_CHECKPOINT.json")
        == EXPECTED_RESTRICTED_INGEST_CHECKPOINT_SHA256,
        "restricted ingest checkpoint hash drift",
    )
    require(
        restricted_receipt["receipt_root_sha256"]
        == EXPECTED_RESTRICTED_RECEIPT_ROOT_SHA256,
        "restricted ledger receipt root hash drift",
    )

    write_tsv(
        output_dir / "SOURCE_ATTEMPTS_PUBLIC.tsv",
        SAFE_ATTEMPT_COLUMNS,
        safe_attempt_rows(ingest["attempts"]),
    )
    write_tsv(
        output_dir / "BLOCKER_QUEUE_PUBLIC.tsv",
        SAFE_BLOCKER_COLUMNS,
        blocker_rows,
    )
    write_tsv(
        output_dir / "ARTIFACT_MANIFEST.tsv",
        ARTIFACT_COLUMNS,
        artifact_rows,
    )
    write_json(output_dir / "LANE_METRICS.json", lane_metrics)
    write_json(
        output_dir / "RESTRICTED_LEDGER_RECEIPT.json", restricted_receipt
    )
    write_json(
        output_dir / "AUTHORITATIVE_GATE_RECEIPT.json", gate_receipt
    )

    public_receipts = output_receipts(output_dir)
    checkpoint = build_checkpoint(
        aggregate,
        artifact_rows,
        blocker_rows,
        lane_metrics,
        restricted_receipt,
        gate_receipt,
        public_receipts,
    )
    write_json(output_dir / "PUBLIC_CHECKPOINT.json", checkpoint)

    print(
        "ROUND3L_PUBLIC_CHECKPOINT_PASS "
        f"artifacts={metrics['artifacts']} "
        f"artifact_bytes={metrics['artifact_bytes']} "
        f"ingested={metrics['ingested_rows']} "
        f"canonical={metrics['canonical_rows']} "
        f"staged_core={metrics['staged_core_candidates']} "
        "staged_rights_eligible=0 staged_model_eligible=0"
    )


if __name__ == "__main__":
    main()
