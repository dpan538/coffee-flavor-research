#!/usr/bin/env python3
"""Validate and freeze restricted Round 3L lanes for database ingestion.

The lane adapters preserve source-native acquisition evidence in four common
TSV ledgers.  This builder performs the cross-lane checks that a source-local
adapter cannot: global key uniqueness, reference integrity, validation of
adapter-declared effective-record deduplication, rights/state consistency,
assertion counting, and deterministic ordering.  It emits no inferred fields
and never promotes a pending-rights row.  Cross-lane hash collisions are review
candidates, not automatic duplicate decisions.
The row-level outputs can contain source-native result facts and therefore must
remain outside the public repository while rights are pending or unknown.
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
ROUND3L = ROOT / "db" / "data" / "round3l"
BLOCKER_RESOLUTIONS = ROUND3L / "BLOCKER_RESOLUTIONS.tsv"

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

BLOCKER_RESOLUTION_COLUMNS = (
    "blocker_key",
    "blocker_state",
    "resolution_evidence",
    "continuation_cursor",
)

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

SOURCE_UNIVERSE_COLUMNS = (
    "census_item_key",
    "item_kind",
    "parent_key",
    "series_key",
    "source_family_key",
    "edition_label",
    "year",
    "country_or_community",
    "category_or_round",
    "official_url",
    "discovery_basis",
    "source_snapshot_sha256",
    "corpus_state",
    "acquisition_state",
    "rights_state",
    "attempt_status",
    "note",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LOWER_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._:/-]*$")
RIGHTS_VALUES = {"ALLOWED", "PROHIBITED", "PENDING", "UNKNOWN", "NOT_APPLICABLE"}
CORE_PAYLOADS = {
    "OFFICIAL_STRUCTURED_SCORE",
    "OFFICIAL_DESCRIPTOR",
    "OFFICIAL_SCORE_AND_DESCRIPTOR",
}
DESCRIPTOR_ASSERTION_TYPES = {
    "OFFICIAL_JUDGE_DESCRIPTOR",
    "OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR",
    "OFFICIAL_AGGREGATED_DESCRIPTOR",
}
ASSERTION_TYPES = DESCRIPTOR_ASSERTION_TYPES | {
    "OFFICIAL_STRUCTURED_SCORE",
    "COMPETITOR_DECLARED_DESCRIPTOR",
    "ROASTER_SUBMITTED_DESCRIPTOR",
    "ORGANIZER_MARKETING_DESCRIPTION",
}


class ContractError(ValueError):
    """A deterministic lane or cross-lane contract violation."""


def read_tsv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ContractError(f"missing required ledger: {path}")
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        actual = tuple(reader.fieldnames or ())
        if actual != tuple(columns):
            raise ContractError(
                f"header mismatch for {path}: expected {tuple(columns)!r}, got {actual!r}"
            )
        rows = list(reader)
    for index, row in enumerate(rows, start=2):
        if None in row:
            raise ContractError(f"extra field in {path}:{index}")
        if any("\x00" in value for value in row.values()):
            raise ContractError(f"NUL byte in {path}:{index}")
    return rows


def write_tsv(path: Path, columns: Sequence[str], rows: Iterable[Mapping[str, str]]) -> None:
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def require_unique(rows: Sequence[Mapping[str, str]], column: str) -> None:
    values = [row[column] for row in rows]
    duplicates = sorted(key for key, count in Counter(values).items() if count > 1)
    require(not duplicates, f"duplicate {column}: {duplicates[:5]!r}")


def int_field(row: Mapping[str, str], key: str, minimum: int = 0) -> int:
    try:
        value = int(row[key])
    except ValueError as error:
        raise ContractError(f"invalid integer {key}={row[key]!r}") from error
    require(value >= minimum, f"{key} must be >= {minimum}: {value}")
    return value


def validate_lower_key(value: str, label: str) -> None:
    require(bool(LOWER_KEY_RE.fullmatch(value)), f"invalid lower key {label}={value!r}")


def load_census(source_path: Path, reconciliation_path: Path) -> list[dict[str, str]]:
    source_rows = read_tsv(source_path, SOURCE_UNIVERSE_COLUMNS)
    reconciliation = json.loads(reconciliation_path.read_text(encoding="utf-8"))
    census_version = reconciliation["census_version"]
    discovered_at = reconciliation["live_official_coe_snapshot"]["retrieved_at"]
    rows: list[dict[str, str]] = []
    for row in source_rows:
        rows.append(
            {
                "census_version": census_version,
                "census_item_key": row["census_item_key"],
                "item_kind": row["item_kind"],
                "parent_key": row["parent_key"],
                "series_key": row["series_key"],
                "source_family_key": row["source_family_key"],
                "edition_label": row["edition_label"],
                "edition_year": row["year"],
                "country_or_community": row["country_or_community"],
                "category_or_round": row["category_or_round"],
                "official_url": row["official_url"],
                "discovery_basis": row["discovery_basis"],
                "source_snapshot_sha256": row["source_snapshot_sha256"],
                "current_corpus_state": row["corpus_state"],
                "acquisition_state": row["acquisition_state"],
                "rights_state": row["rights_state"],
                "note": row["note"],
                "discovered_at": discovered_at,
            }
        )
    require_unique(rows, "census_item_key")
    return sorted(rows, key=lambda row: row["census_item_key"])


def load_lanes(
    lane_root: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], set[str]]:
    lane_dirs = sorted(path for path in lane_root.iterdir() if path.is_dir())
    require(bool(lane_dirs), f"no acquisition lane directories found under {lane_root}")
    attempts: list[dict[str, str]] = []
    records: list[dict[str, str]] = []
    assertions: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []
    source_hashes: set[str] = set()
    for lane_dir in lane_dirs:
        lane_attempts = read_tsv(lane_dir / "ATTEMPTS.tsv", ATTEMPT_COLUMNS)
        for row in lane_attempts:
            require(
                row["lane_key"] == lane_dir.name,
                f"lane_key {row['lane_key']!r} does not match directory {lane_dir.name!r}",
            )
        attempts.extend(lane_attempts)
        source_hashes.update(
            row["source_snapshot_sha256"]
            for row in lane_attempts
            if row["source_snapshot_sha256"]
        )
        source_file_manifest = lane_dir / "SOURCE_FILE_MANIFEST.tsv"
        if source_file_manifest.is_file():
            with source_file_manifest.open("r", encoding="utf-8", newline="") as stream:
                manifest_reader = csv.DictReader(stream, delimiter="\t")
                require(
                    "sha256" in (manifest_reader.fieldnames or []),
                    f"source manifest lacks sha256 column: {source_file_manifest}",
                )
                for manifest_row in manifest_reader:
                    value = manifest_row["sha256"]
                    require(
                        bool(SHA256_RE.fullmatch(value)),
                        f"invalid source manifest hash: {source_file_manifest}",
                    )
                    source_hashes.add(value)
        records.extend(read_tsv(lane_dir / "RECORDS.tsv", RECORD_COLUMNS))
        assertions.extend(read_tsv(lane_dir / "ASSERTIONS.tsv", ASSERTION_COLUMNS))
        blockers.extend(read_tsv(lane_dir / "BLOCKERS.tsv", BLOCKER_COLUMNS))
    return attempts, records, assertions, blockers, source_hashes


def validate(
    census: Sequence[dict[str, str]],
    attempts: Sequence[dict[str, str]],
    records: Sequence[dict[str, str]],
    assertions: Sequence[dict[str, str]],
    blockers: Sequence[dict[str, str]],
    source_hashes: set[str],
) -> None:
    census_keys = {row["census_item_key"] for row in census}
    require_unique(attempts, "attempt_key")
    require_unique(records, "professional_acquisition_record_key")
    require_unique(assertions, "professional_acquisition_assertion_key")
    require_unique(blockers, "blocker_key")

    attempt_by_key = {row["attempt_key"]: row for row in attempts}
    record_by_key = {row["professional_acquisition_record_key"]: row for row in records}
    blocker_attempts = {row["attempt_key"] for row in blockers}
    seen_lane_sequence: set[tuple[str, str]] = set()
    for row in attempts:
        validate_lower_key(row["attempt_key"], "attempt_key")
        require(row["census_item_key"] in census_keys, f"unknown census reference: {row['census_item_key']}")
        require(row["attempted_at"].endswith("Z"), f"attempt timestamp is not UTC: {row['attempt_key']}")
        sequence = int_field(row, "attempt_sequence", 1)
        lane_sequence = (row["lane_key"], str(sequence))
        require(lane_sequence not in seen_lane_sequence, f"duplicate lane sequence: {lane_sequence!r}")
        seen_lane_sequence.add(lane_sequence)
        parsed = int_field(row, "parsed_row_count")
        normalized = int_field(row, "normalized_record_count")
        int_field(row, "artifact_byte_count")
        int_field(row, "descriptor_assertion_count")
        require(normalized <= parsed, f"normalized rows exceed parsed rows: {row['attempt_key']}")
        if row["source_snapshot_sha256"]:
            require(bool(SHA256_RE.fullmatch(row["source_snapshot_sha256"])), f"invalid attempt hash: {row['attempt_key']}")
            require(int(row["artifact_byte_count"]) > 0, f"hashed attempt has zero bytes: {row['attempt_key']}")
        try:
            evidence = json.loads(row["evidence_json"] or "{}")
        except json.JSONDecodeError as error:
            raise ContractError(f"invalid evidence_json: {row['attempt_key']}") from error
        require(isinstance(evidence, dict), f"evidence_json must be an object: {row['attempt_key']}")
        blocked = row["outcome"] == "BLOCKED_EXTERNAL_ACTION"
        require(blocked == (row["attempt_key"] in blocker_attempts), f"blocker queue mismatch: {row['attempt_key']}")

    seen_source_records: set[tuple[str, str]] = set()
    canonical_effective: dict[str, str] = {}
    for row in records:
        record_key = row["professional_acquisition_record_key"]
        validate_lower_key(record_key, "professional_acquisition_record_key")
        require(row["attempt_key"] in attempt_by_key, f"unknown attempt for record: {record_key}")
        source_record_pair = (row["attempt_key"], row["source_record_key"])
        require(source_record_pair not in seen_source_records, f"duplicate source record: {source_record_pair!r}")
        seen_source_records.add(source_record_pair)
        require(bool(SHA256_RE.fullmatch(row["source_snapshot_sha256"])), f"invalid source hash: {record_key}")
        require(
            row["source_snapshot_sha256"] in source_hashes,
            f"record hash is absent from attempt/source-file manifests: {record_key}",
        )
        require(bool(SHA256_RE.fullmatch(row["raw_record_sha256"])), f"invalid raw row hash: {record_key}")
        require(row["is_synthetic"].lower() == "false", f"synthetic record prohibited: {record_key}")
        require(row["semantic_inference_used"].lower() == "false", f"inferred record prohibited: {record_key}")
        for right in (
            "public_results_use",
            "public_descriptor_use",
            "internal_research_use",
            "public_derived_release",
            "model_research_use",
            "commercial_model_use",
        ):
            require(row[right] in RIGHTS_VALUES, f"invalid {right} on {record_key}")
        disposition = row["deduplication_disposition"]
        if disposition == "CANONICAL":
            require(not row["canonical_record_key"], f"canonical row points to another record: {record_key}")
            if row["effective_record_key"]:
                require(row["effective_record_key"] not in canonical_effective, f"duplicate effective record: {row['effective_record_key']}")
                canonical_effective[row["effective_record_key"]] = record_key
        else:
            require(not row["effective_record_key"], f"dedup loss retains effective key: {record_key}")
            require(bool(row["canonical_record_key"]), f"dedup loss lacks canonical target: {record_key}")
        if row["corpus_state"] == "MODEL_ELIGIBLE":
            require(row["internal_research_use"] == "ALLOWED", f"model row lacks internal rights: {record_key}")
            require(row["model_research_use"] == "ALLOWED", f"model row lacks model rights: {record_key}")

    for row in records:
        target = row["canonical_record_key"]
        if target:
            require(target in record_by_key, f"unknown canonical target: {target}")
            require(record_by_key[target]["deduplication_disposition"] == "CANONICAL", f"target is not canonical: {target}")

    for row in assertions:
        assertion_key = row["professional_acquisition_assertion_key"]
        validate_lower_key(assertion_key, "professional_acquisition_assertion_key")
        record_key = row["professional_acquisition_record_key"]
        require(record_key in record_by_key, f"orphan assertion: {assertion_key}")
        require(bool(SHA256_RE.fullmatch(row["assertion_text_sha256"])), f"invalid assertion hash: {assertion_key}")
        require(row["semantic_inference_used"].lower() == "false", f"inferred assertion prohibited: {assertion_key}")
        require(row["assertion_type"] in ASSERTION_TYPES, f"invalid assertion type: {assertion_key}")
        require(
            row["text_storage_state"] != "CAPTURED_RESTRICTED",
            f"restricted assertion text cannot enter the public Git freeze: {assertion_key}",
        )
        if row["assertion_text"]:
            require(
                row["text_storage_state"] == "REVIEWED_TEXT",
                f"stored assertion text is not reviewed for public freeze: {assertion_key}",
            )
            required_right = (
                "public_descriptor_use"
                if row["assertion_type"] in DESCRIPTOR_ASSERTION_TYPES
                else "public_results_use"
            )
            require(
                record_by_key[record_key][required_right] == "ALLOWED",
                f"stored assertion text lacks affirmative {required_right}: {assertion_key}",
            )
            actual_hash = hashlib.sha256(row["assertion_text"].encode("utf-8")).hexdigest()
            require(actual_hash == row["assertion_text_sha256"], f"assertion text hash mismatch: {assertion_key}")

    for row in blockers:
        require(row["attempt_key"] in attempt_by_key, f"orphan blocker: {row['blocker_key']}")
        require(attempt_by_key[row["attempt_key"]]["outcome"] == "BLOCKED_EXTERNAL_ACTION", f"non-blocked attempt queued: {row['attempt_key']}")

    record_counts = Counter(row["attempt_key"] for row in records)
    descriptor_counts = Counter(
        record_by_key[row["professional_acquisition_record_key"]]["attempt_key"]
        for row in assertions
        if row["assertion_type"] in DESCRIPTOR_ASSERTION_TYPES
    )
    for row in attempts:
        require(int(row["normalized_record_count"]) == record_counts[row["attempt_key"]], f"record count drift: {row['attempt_key']}")
        require(int(row["descriptor_assertion_count"]) == descriptor_counts[row["attempt_key"]], f"descriptor count drift: {row['attempt_key']}")


def apply_blocker_resolutions(
    blockers: Sequence[dict[str, str]], resolution_path: Path
) -> None:
    """Apply auditable cross-lane resolutions without rewriting source lanes."""
    if not resolution_path.is_file():
        return
    resolutions = read_tsv(resolution_path, BLOCKER_RESOLUTION_COLUMNS)
    require_unique(resolutions, "blocker_key")
    blocker_by_key = {row["blocker_key"]: row for row in blockers}
    for resolution in resolutions:
        blocker_key = resolution["blocker_key"]
        require(blocker_key in blocker_by_key, f"resolution references unknown blocker: {blocker_key}")
        require(
            resolution["blocker_state"] in {"AUTHORIZED", "RESOLVED", "DECLINED"},
            f"invalid terminal blocker state: {blocker_key}",
        )
        require(
            bool(resolution["resolution_evidence"]),
            f"resolved blocker lacks evidence: {blocker_key}",
        )
        blocker = blocker_by_key[blocker_key]
        blocker["blocker_state"] = resolution["blocker_state"]
        blocker["resolution_evidence"] = resolution["resolution_evidence"]
        blocker["continuation_cursor"] = resolution["continuation_cursor"]


def apply_census_progress(
    census: Sequence[dict[str, str]], attempts: Sequence[dict[str, str]]
) -> None:
    attempts_by_census: dict[str, list[dict[str, str]]] = defaultdict(list)
    for attempt in attempts:
        attempts_by_census[attempt["census_item_key"]].append(attempt)
    for row in census:
        item_attempts = attempts_by_census.get(row["census_item_key"], [])
        if not item_attempts:
            continue
        outcomes = {attempt["outcome"] for attempt in item_attempts}
        has_snapshot_or_records = any(
            attempt["source_snapshot_sha256"]
            or int(attempt["normalized_record_count"]) > 0
            for attempt in item_attempts
        )
        if has_snapshot_or_records:
            row["current_corpus_state"] = "RESEARCH_STAGED"
        if outcomes == {"COMPLETED"}:
            row["acquisition_state"] = "ACQUIRED_COMPLETE"
        elif "COMPLETED" in outcomes or "PARTIAL" in outcomes:
            row["acquisition_state"] = "ACQUIRED_PARTIAL"
        elif "BLOCKED_EXTERNAL_ACTION" in outcomes:
            row["acquisition_state"] = "BLOCKED_EXTERNAL_ACTION"
        elif "TRANSIENT_TECHNICAL_FAILURE" in outcomes:
            row["acquisition_state"] = "TRANSIENT_TECHNICAL_FAILURE"
        else:
            row["acquisition_state"] = "ATTEMPTED_NO_RECORD_PAYLOAD"


def checkpoint(
    census: Sequence[dict[str, str]],
    attempts: Sequence[dict[str, str]],
    records: Sequence[dict[str, str]],
    assertions: Sequence[dict[str, str]],
    blockers: Sequence[dict[str, str]],
    output_files: Sequence[Path],
    lane_root: Path,
) -> dict[str, object]:
    core_candidates = [
        row
        for row in records
        if row["evidence_tier"] in {"P1", "P2"}
        and row["payload_kind"] in CORE_PAYLOADS
        and row["fresh_preparation_status"] == "CONFIRMED"
        and bool(row["effective_record_key"])
        and row["deduplication_disposition"] == "CANONICAL"
    ]
    staged_rights_eligible = [
        row for row in core_candidates if row["internal_research_use"] == "ALLOWED"
    ]
    model = [
        row
        for row in staged_rights_eligible
        if row["model_research_use"] == "ALLOWED" and row["corpus_state"] == "MODEL_ELIGIBLE"
    ]
    current_by_lane: dict[str, dict[str, str]] = {}
    for row in attempts:
        current = current_by_lane.get(row["lane_key"])
        if current is None or int(row["attempt_sequence"]) > int(current["attempt_sequence"]):
            current_by_lane[row["lane_key"]] = row
    resume_manifests: dict[str, object] = {}
    for lane, latest_attempt in sorted(current_by_lane.items()):
        manifest_path = lane_root / lane / "RESUME_MANIFEST.json"
        require(manifest_path.is_file(), f"missing resume manifest for lane {lane}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        require(isinstance(manifest, dict), f"resume manifest is not an object: {lane}")
        resume_manifests[lane] = {
            "latest_attempt_sequence": int(latest_attempt["attempt_sequence"]),
            "manifest": manifest,
        }
    rights_distribution = Counter(
        (row["corpus_state"], row["internal_research_use"], row["model_research_use"])
        for row in records
    )
    rights_dimensions = {
        right: dict(sorted(Counter(row[right] for row in records).items()))
        for right in (
            "public_results_use",
            "public_descriptor_use",
            "internal_research_use",
            "public_derived_release",
            "model_research_use",
            "commercial_model_use",
        )
    }
    records_by_raw_hash: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in records:
        records_by_raw_hash[row["raw_record_sha256"]].append(row)
    cross_family_hash_candidates = [
        group
        for group in records_by_raw_hash.values()
        if len({row["source_family_key"] for row in group}) > 1
    ]
    editions = sum(row["item_kind"] in {"COMPETITION_EDITION", "PILOT_EDITION"} for row in census)
    descriptor_count = sum(row["assertion_type"] in DESCRIPTOR_ASSERTION_TYPES for row in assertions)
    return {
        "phase_status": "IN_PROGRESS_ACQUISITION",
        "census_version": census[0]["census_version"],
        "checkpoint_at": max(row["attempted_at"] for row in attempts),
        "metrics": {
            "discovered_source_families": len({row["source_family_key"] for row in census}),
            "discovered_editions": editions,
            "attempted_sources": len({row["census_item_key"] for row in attempts}),
            "sources_with_completed_attempt": len({row["census_item_key"] for row in attempts if row["outcome"] == "COMPLETED"}),
            "attempt_count": len(attempts),
            "completed_attempt_count": sum(
                row["outcome"] == "COMPLETED" for row in attempts
            ),
            "acquired_attempt_snapshots": sum(
                bool(row["source_snapshot_sha256"]) for row in attempts
            ),
            "attempt_snapshot_bytes": sum(
                int(row["artifact_byte_count"]) for row in attempts
            ),
            "parsed_rows": sum(int(row["parsed_row_count"]) for row in attempts),
            "ingested_records": len(records),
            "canonical_records_after_declared_dedup": sum(
                row["deduplication_disposition"] == "CANONICAL" for row in records
            ),
            "staged_core_candidates": len(core_candidates),
            "staged_internal_rights_eligible_core_candidates": len(staged_rights_eligible),
            "staged_model_eligible_records": len(model),
            "total_professional_assertions": len(assertions),
            "structured_score_assertions": sum(
                row["assertion_type"] == "OFFICIAL_STRUCTURED_SCORE"
                for row in assertions
            ),
            "staged_gate_type_descriptor_assertions": descriptor_count,
            "staged_remaining_descriptor_assertions_to_40000": max(40000 - descriptor_count, 0),
            "staged_remaining_descriptor_assertions_to_60000": max(60000 - descriptor_count, 0),
            "preparation_service_confirmed": sum(row["fresh_preparation_status"] == "CONFIRMED" for row in records),
            "c0_reported": sum(row["c0_source_status"] == "REPORTED" for row in records),
            "c1_reviewed": sum(row["c1_evidence_status"] == "REVIEWED" for row in records),
            "duplicate_publication_losses": sum(row["deduplication_disposition"] == "DUPLICATE_PUBLICATION" for row in records),
            "mirror_losses": sum(row["deduplication_disposition"] == "MIRROR" for row in records),
            "repeated_service_losses": sum(row["deduplication_disposition"] == "REPEATED_SERVICE" for row in records),
            "open_external_blockers": sum(row["blocker_state"] == "OPEN" for row in blockers),
            "cross_family_raw_hash_review_groups": len(cross_family_hash_candidates),
            "cross_family_raw_hash_review_rows": sum(
                len(group) for group in cross_family_hash_candidates
            ),
            "staged_rights_eligible_gap_to_7000": max(7000 - len(staged_rights_eligible), 0),
            "staged_rights_eligible_gap_to_10000": max(10000 - len(staged_rights_eligible), 0),
        },
        "rights_state_distribution": [
            {
                "corpus_state": key[0],
                "internal_research_use": key[1],
                "model_research_use": key[2],
                "record_count": value,
            }
            for key, value in sorted(rights_distribution.items())
        ],
        "rights_dimension_distribution": rights_dimensions,
        "blocker_state_distribution": dict(
            sorted(Counter(row["blocker_state"] for row in blockers).items())
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
        "record_payload_distribution": dict(
            sorted(Counter(row["payload_kind"] for row in records).items())
        ),
        "evidence_tier_distribution": dict(
            sorted(Counter(row["evidence_tier"] for row in records).items())
        ),
        "preparation_service_coverage": dict(
            sorted(
                Counter(
                    row["preparation_service_code"] or "UNRESOLVED"
                    for row in records
                ).items()
            )
        ),
        "c0_evidence_status": dict(
            sorted(Counter(row["c0_source_status"] for row in records).items())
        ),
        "c1_evidence_status": dict(
            sorted(Counter(row["c1_evidence_status"] for row in records).items())
        ),
        "continuation_cursor": resume_manifests,
        "artifacts": [
            {
                "path": (
                    path.relative_to(ROOT).as_posix()
                    if path.is_relative_to(ROOT)
                    else path.name
                ),
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
            }
            for path in output_files
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lane-root",
        type=Path,
        required=True,
        help="restricted directory containing the source-lane ledgers",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="restricted output directory; required unless --validate-only",
    )
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    lane_root = args.lane_root.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else None
    require(
        args.validate_only or output_dir is not None,
        "--output-dir is required unless --validate-only is used",
    )
    if output_dir is not None:
        require(
            not output_dir.is_relative_to(ROOT.resolve()),
            "restricted row-level ingest output cannot be written inside the public repository",
        )

    census = load_census(
        ROUND3L / "SOURCE_UNIVERSE.tsv",
        ROUND3L / "CENSUS_RECONCILIATION.json",
    )
    attempts, records, assertions, blockers, source_hashes = load_lanes(lane_root)
    validate(census, attempts, records, assertions, blockers, source_hashes)
    apply_blocker_resolutions(blockers, BLOCKER_RESOLUTIONS)
    apply_census_progress(census, attempts)
    attempts.sort(key=lambda row: (row["lane_key"], int(row["attempt_sequence"]), row["attempt_key"]))
    records.sort(key=lambda row: row["professional_acquisition_record_key"])
    assertions.sort(key=lambda row: row["professional_acquisition_assertion_key"])
    blockers.sort(key=lambda row: row["blocker_key"])

    if args.validate_only:
        print("ROUND3L_LANE_CONTRACT_PASS=true")
        return

    assert output_dir is not None
    outputs = [
        output_dir / "SOURCE_CENSUS.tsv",
        output_dir / "SOURCE_ATTEMPTS.tsv",
        output_dir / "PROFESSIONAL_RECORDS.tsv",
        output_dir / "PROFESSIONAL_ASSERTIONS.tsv",
        output_dir / "BLOCKER_QUEUE.tsv",
    ]
    write_tsv(outputs[0], CENSUS_COLUMNS, census)
    write_tsv(outputs[1], ATTEMPT_COLUMNS, attempts)
    write_tsv(outputs[2], RECORD_COLUMNS, records)
    write_tsv(outputs[3], ASSERTION_COLUMNS, assertions)
    write_tsv(outputs[4], BLOCKER_COLUMNS, blockers)
    frozen_checkpoint = checkpoint(
        census,
        attempts,
        records,
        assertions,
        blockers,
        outputs,
        lane_root,
    )
    checkpoint_path = output_dir / "INGESTION_CHECKPOINT.json"
    checkpoint_path.write_text(
        json.dumps(frozen_checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(frozen_checkpoint["metrics"], sort_keys=True))
    print("ROUND3L_INGEST_FREEZE_PASS=true")


if __name__ == "__main__":
    main()
