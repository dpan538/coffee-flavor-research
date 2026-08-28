#!/usr/bin/env python3
"""Fail-closed validation for the public-safe Round 3M artifact package.

This validator deliberately checks semantic counts and cross-file identities,
not only that files parse.  It never reads the restricted Round 3L freeze or
the restricted live-capture inputs.  Source-native descriptor text must remain
redacted from this public artifact surface.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPOSITORY_ROOT / "db" / "data" / "round3m"
DEFAULT_GENERATED_DIR = REPOSITORY_ROOT / "db" / "adapters" / "round3m" / "generated"

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SCOPED_CAPTURE_SHA256_RE = re.compile(
    r"^WEB_INDEX_FIELD_CAPTURE_SHA256:([0-9a-f]{64});NOT_FULL_PAGE_BODY$"
)

EXPECTED_BASELINE = {
    "census_items": 480,
    "source_route_or_family_keys": 131,
    "editions": 267,
    "artifacts": 848,
    "parsed_rows": 26_531,
    "staged_rows": 26_515,
    "canonical_rows": 20_994,
    "staged_core_candidates": 6_754,
    "staged_assertions": 11_801,
    "staged_gate_descriptors": 376,
    "reviewed_descriptors": 0,
    "model_eligible_descriptors": 0,
}

MISSING_RESEARCH_ARTIFACTS = {
    "OPEN_DESCRIPTOR_SOURCE_CENSUS.tsv",
    "DESCRIPTOR_YIELD_AUDIT.tsv",
    "DESCRIPTOR_COUNT_RECEIPT.json",
    "DESCRIPTOR_PROVENANCE_MATRIX.tsv",
    "OPEN_DESCRIPTOR_CEILING.md",
    "DESCRIPTOR_TRAINING_GATES.md",
    "SOURCE_PRIORITY_BY_DESCRIPTOR_YIELD.tsv",
    "LOW_YIELD_AND_FALSE_SCALE_REGISTER.tsv",
    "CODEX_RESUMPTION_DECISION.md",
}

RIGHTS_PURPOSES = {
    "PUBLIC_DISCOVERY",
    "INTERNAL_RESEARCH_ANALYSIS",
    "DERIVED_RESEARCH_DATA",
    "MODEL_RESEARCH",
    "DEPLOYMENT_OR_COMMERCIAL_MODEL",
    "RAW_REDISTRIBUTION",
}

EXPECTED_SCHEMA_SIGNATURES = {
    "schema.coe.honduras-2017.explicit-top-jury.v1",
    "schema.coe.colombia-south-2008.frequency-coded.v1",
    "schema.coe.generic-sensory-field.v1",
    "schema.wcc.completed-scoresheet.v1",
}

EXPECTED_LOW_YIELD_ROUTES = {
    "BOP_RESULT_TABLES",
    "GOLDEN_BEAN_PUBLIC_RESULTS",
    "WCC_BLANK_FORMS",
    "WCC_RANKING_METADATA",
    "SCAJ_RESULTS",
    "AFCA_SCORE_TABLES",
    "ROYAL_ADELAIDE_RESULTS",
    "MELBOURNE_ROYAL_RESULTS",
    "AVPA_PALMARES",
    "IIAC_PUBLIC_MEDAL_LISTS",
    "GLOBAL_COFFEE_AWARDS_PUBLIC_AWARD_LISTS",
}

REQUIRED_MACHINE_OUTPUTS = {
    "SOURCE_CENSUS_UNIVERSE.tsv",
    "SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv",
    "SOURCE_ROUTE_DISPOSITION.tsv",
    "DESCRIPTOR_ASSERTION_LEDGER.tsv",
    "DESCRIPTOR_REVIEW_QUEUE.tsv",
    "DESCRIPTOR_PROVISIONAL_DECISIONS.tsv",
    "HUMAN_REVIEW_IMPORT_TEMPLATE.tsv",
    "ADJUDICATION_IMPORT_TEMPLATE.tsv",
    "DESCRIPTOR_PROVENANCE_DECISION.tsv",
    "DESCRIPTOR_RIGHTS_DECISION.tsv",
    "PUBLICATION_LAYER_RELATION.tsv",
    "DUPLICATE_REPEAT_DECISION.tsv",
    "DESCRIPTOR_NORMALIZATION_DECISION.tsv",
    "COASSERTION_EVENT.tsv",
    "SOURCE_ROUTE_YIELD.tsv",
    "ANALYST_TIME_LOG.tsv",
    "LOW_YIELD_EXCLUSION_REGISTER.tsv",
    "ORGANIZER_REQUEST_MATRIX.tsv",
    "DESCRIPTOR_GATE_STATUS.tsv",
    "ROUND3M_EXPECTED_STATE.tsv",
    "ROUND3M_MANIFEST.json",
    "SHA256SUMS",
}

REQUIRED_REVIEW_OUTPUTS = {
    "EXISTING_376_REVIEW_QUEUE.tsv",
    "EXISTING_376_PROVISIONAL_DECISIONS.tsv",
    "EXISTING_376_REVIEW_RECEIPT.json",
    "EXISTING_376_SOURCE_ARTIFACT_RECEIPT.tsv",
    "ROUND3M_RESEARCH_ARTIFACT_BLOCKER.tsv",
    "BASELINE_RECONCILIATION.json",
    "C0_C1_EVIDENCE_RECEIPT.json",
    "LIVE_ASSERTION_IMPORT_RECEIPT.json",
}

REQUIRED_GENERATED_OUTPUTS = {
    "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv",
    "PUBLIC_SAFE_CAPTURE_RECEIPTS.tsv",
    "PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv",
    "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv",
    "LIVE_ADAPTER_METRICS.json",
}

FORBIDDEN_TRAINING_SUFFIXES = {
    ".ckpt",
    ".joblib",
    ".mlmodel",
    ".onnx",
    ".pickle",
    ".pkl",
    ".pt",
    ".pth",
    ".safetensors",
    ".tflite",
}


class ContractError(AssertionError):
    """A deterministic artifact-contract violation."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def parse_bool(value: str, context: str) -> bool:
    require(value in {"true", "false"}, f"{context}: expected true|false, got {value!r}")
    return value == "true"


def parse_int(value: str, context: str) -> int:
    require(re.fullmatch(r"-?[0-9]+", value) is not None, f"{context}: invalid integer {value!r}")
    return int(value)


def require_sha256(value: str, context: str) -> None:
    require(SHA256_RE.fullmatch(value) is not None, f"{context}: invalid SHA-256 {value!r}")


def read_tsv(path: Path, required_columns: Iterable[str] = ()) -> list[dict[str, str]]:
    require(path.is_file(), f"missing TSV: {path}")
    raw = path.read_bytes()
    require(raw.endswith(b"\n"), f"{path}: deterministic TSV must end with newline")
    require(b"\x00" not in raw, f"{path}: NUL byte is forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError(f"{path}: not UTF-8: {exc}") from exc
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        header = reader.fieldnames or []
        require(bool(header), f"{path}: missing header")
        require(len(header) == len(set(header)), f"{path}: duplicate header columns")
        require(all(header), f"{path}: blank header column")
        missing = set(required_columns) - set(header)
        require(not missing, f"{path}: missing columns {sorted(missing)}")
        rows = list(reader)
    for line_number, row in enumerate(rows, start=2):
        require(None not in row, f"{path}:{line_number}: too many fields")
        require(all(value is not None for value in row.values()), f"{path}:{line_number}: missing field")
    return rows


def read_json(path: Path) -> object:
    require(path.is_file(), f"missing JSON: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"{path}: invalid JSON: {exc}") from exc


def index_unique(rows: Sequence[Mapping[str, str]], key: str, context: str) -> dict[str, Mapping[str, str]]:
    result: dict[str, Mapping[str, str]] = {}
    for row in rows:
        value = row[key]
        require(value != "", f"{context}: blank {key}")
        require(value not in result, f"{context}: duplicate {key}={value!r}")
        result[value] = row
    return result


def scoped_file_hash(row: Mapping[str, str], context: str) -> str:
    direct = row.get("source_file_sha256", "")
    if direct:
        require_sha256(direct, f"{context}.source_file_sha256")
        return direct
    match = SCOPED_CAPTURE_SHA256_RE.fullmatch(row.get("source_file_sha256_scope", ""))
    require(match is not None, f"{context}: missing direct or scoped source-file SHA-256")
    require(
        row.get("source_file_nonstorage_reason", "") != "",
        f"{context}: scoped-only hash requires explicit non-storage reason",
    )
    return match.group(1)


def count_data_rows(path: Path) -> int | None:
    if path.suffix != ".tsv":
        return None
    return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)


def validate_review_manifest(data_dir: Path) -> None:
    path = data_dir / "DESCRIPTOR_REVIEW_ARTIFACT_MANIFEST.json"
    manifest = read_json(path)
    require(isinstance(manifest, dict), f"{path}: expected object")
    entries = manifest.get("files")
    require(isinstance(entries, list) and entries, f"{path}: missing files list")
    seen: set[str] = set()
    for entry in entries:
        require(isinstance(entry, dict), f"{path}: non-object file entry")
        relative = entry.get("path")
        require(isinstance(relative, str) and relative != "", f"{path}: bad entry path")
        require(relative not in seen, f"{path}: duplicate entry {relative}")
        require(Path(relative).name == relative, f"{path}: entry must be a data-dir basename: {relative}")
        seen.add(relative)
        target = data_dir / relative
        require(target.is_file(), f"{path}: listed file absent: {relative}")
        actual = target.read_bytes()
        require(entry.get("byte_count") == len(actual), f"{path}: byte count mismatch for {relative}")
        require(
            entry.get("sha256") == hashlib.sha256(actual).hexdigest(),
            f"{path}: SHA-256 mismatch for {relative}",
        )
        require(
            entry.get("data_row_count") == count_data_rows(target),
            f"{path}: row count mismatch for {relative}",
        )


def validate_final_checksums(data_dir: Path) -> None:
    checksum_path = data_dir / "SHA256SUMS"
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    require(bool(lines), f"{checksum_path}: empty")
    seen: set[str] = set()
    for line_number, line in enumerate(lines, start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\x00]+)", line)
        require(match is not None, f"{checksum_path}:{line_number}: invalid checksum line")
        expected_hash, filename = match.groups()
        require(filename not in seen, f"{checksum_path}: duplicate filename {filename}")
        require(filename != "SHA256SUMS", f"{checksum_path}: cannot self-hash")
        seen.add(filename)
        target = data_dir / filename
        require(target.is_file(), f"{checksum_path}: missing listed file {filename}")
        require(
            hashlib.sha256(target.read_bytes()).hexdigest() == expected_hash,
            f"{checksum_path}: hash mismatch for {filename}",
        )
    require(
        REQUIRED_MACHINE_OUTPUTS - {"SHA256SUMS"} <= seen,
        f"{checksum_path}: required outputs not covered: {sorted((REQUIRED_MACHINE_OUTPUTS - {'SHA256SUMS'}) - seen)}",
    )


def validate_baseline(data_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    receipt = read_json(data_dir / "BASELINE_RECONCILIATION.json")
    require(isinstance(receipt, dict), "baseline receipt must be an object")
    require(receipt.get("exact_match") is True, "baseline receipt exact_match must be true")
    require(receipt.get("expected") == EXPECTED_BASELINE, "baseline expected counts changed")
    require(receipt.get("recomputed") == EXPECTED_BASELINE, "baseline recomputed counts changed")
    require(receipt.get("independent_source_family_count") == 11, "expected 11 conservative independent families")
    require(receipt.get("machine_readable_research_artifacts_available") is False, "missing research bundle must remain explicit")
    require(
        receipt.get("research_artifact_import_status") == "BLOCKED_MISSING_MACHINE_ARTIFACTS",
        "research artifact import status must remain blocked",
    )
    require(receipt.get("report_counts_independently_reproduced") is False, "PDF counts must not be claimed as independently reproduced")
    require(set(receipt.get("missing_research_artifacts", [])) == MISSING_RESEARCH_ARTIFACTS, "baseline missing-artifact set changed")

    census = read_tsv(
        data_dir / "SOURCE_CENSUS_UNIVERSE.tsv",
        {
            "census_item_key",
            "source_route_id",
            "organizer_id",
            "edition_id",
            "publication_host",
            "independent_source_family_id",
            "rights_lineage_id",
            "mirror_lineage_id",
            "route_disposition",
            "official_url",
        },
    )
    routes = read_tsv(
        data_dir / "SOURCE_ROUTE_DISPOSITION.tsv",
        {"source_route_id", "organizer_id", "independent_source_family_id", "route_disposition"},
    )
    require(len(census) == 480, f"census row count {len(census)} != 480")
    require(len(routes) == 131, f"route row count {len(routes)} != 131")
    index_unique(census, "census_item_key", "source census")
    route_by_id = index_unique(routes, "source_route_id", "source routes")
    require(len({row["independent_source_family_id"] for row in routes}) == 11, "route census must collapse to 11 independent families")
    require(
        sum(
            row["item_kind"] in {"COMPETITION_EDITION", "PILOT_EDITION"}
            for row in census
        )
        == 267,
        "discovered edition count must be 267 (excluding the aggregate count-claim row)",
    )
    require({row["source_route_id"] for row in census} <= set(route_by_id), "census references an unknown route")
    return census, routes


def validate_schema_and_policy(data_dir: Path) -> None:
    signatures = read_tsv(
        data_dir / "SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv",
        {
            "schema_signature_id",
            "source_route_id",
            "schema_version",
            "host",
            "route_pattern",
            "field_labels_json",
            "selectors_json",
            "publication_layer_rules_json",
            "field_origin_assumptions_json",
            "positive_fixture_locator",
            "negative_fixture_locator",
            "adapter_version",
            "live_positive_fixture_present",
            "validation_status",
        },
    )
    signature_by_id = index_unique(signatures, "schema_signature_id", "schema signatures")
    require(set(signature_by_id) == EXPECTED_SCHEMA_SIGNATURES, "unexpected schema signature set")
    coe_signatures = [row for row in signatures if row["schema_signature_id"].startswith("schema.coe.")]
    require(len(coe_signatures) == 3, "exactly three CoE schema classes must be represented")
    require(
        all(parse_bool(row["live_positive_fixture_present"], "schema fixture") for row in coe_signatures),
        "a required CoE schema class lacks a real positive fixture",
    )
    require(
        all(row["validation_status"] in {"VALIDATED", "SOURCE_DRIFT"} for row in coe_signatures),
        "a required CoE schema class is neither validated nor explicitly source-drifted",
    )
    wcc = signature_by_id["schema.wcc.completed-scoresheet.v1"]
    require(not parse_bool(wcc["live_positive_fixture_present"], "WCC fixture"), "WCC must not claim a completed positive fixture")
    require(wcc["validation_status"] != "VALIDATED", "WCC cannot validate without a completed filled scoresheet")
    for row in signatures:
        for column in (
            "field_labels_json",
            "selectors_json",
            "publication_layer_rules_json",
            "field_origin_assumptions_json",
        ):
            try:
                json.loads(row[column])
            except json.JSONDecodeError as exc:
                raise ContractError(f"schema {row['schema_signature_id']}: invalid {column}: {exc}") from exc

    exclusions = read_tsv(
        data_dir / "LOW_YIELD_EXCLUSION_REGISTER.tsv",
        {"route_key", "verified_descriptor_count", "new_round3m_broad_acquisition_budget"},
    )
    require(len(exclusions) == 11, "low-yield register must contain 11 named routes")
    require({row["route_key"] for row in exclusions} == EXPECTED_LOW_YIELD_ROUTES, "low-yield route set changed")
    require(all(row["verified_descriptor_count"] == "0" for row in exclusions), "low-yield register claims descriptors")
    require(all(row["new_round3m_broad_acquisition_budget"] == "0" for row in exclusions), "low-yield route received acquisition budget")

    requests = read_tsv(
        data_dir / "ORGANIZER_REQUEST_MATRIX.tsv",
        {"request_key", "request_status", "outbound_data_request_count", "contract_acceptance_count", "commercial_purchase_count"},
    )
    require(len(requests) == 34, "organizer request matrix must contain 34 prepared rows")
    index_unique(requests, "request_key", "organizer requests")
    for row in requests:
        require(row["request_status"] == "NOT_SENT", f"request {row['request_key']} was sent")
        require(row["outbound_data_request_count"] == "0", f"request {row['request_key']} has outbound count")
        require(row["contract_acceptance_count"] == "0", f"request {row['request_key']} has contract acceptance")
        require(row["commercial_purchase_count"] == "0", f"request {row['request_key']} has purchase")


def validate_candidate_review(data_dir: Path) -> tuple[dict[str, Mapping[str, str]], dict[str, Mapping[str, str]]]:
    queue_columns = {
        "review_queue_id",
        "descriptor_assertion_id",
        "professional_record_id",
        "source_route_id",
        "source_artifact_id",
        "source_file_sha256",
        "route_index_sha256",
        "source_file_sha256_scope",
        "source_file_nonstorage_reason",
        "raw_record_sha256",
        "source_locator",
        "source_text_sha256",
        "source_text_storage_state",
        "source_text_non_storage_reason",
        "publication_layer",
        "descriptor_class",
        "evidence_tier",
        "review_state",
        "review_actor_type",
        "current_disposition",
        "human_review_required",
        "model_eligible",
    }
    existing_queue = read_tsv(data_dir / "EXISTING_376_REVIEW_QUEUE.tsv", queue_columns)
    existing_decisions = read_tsv(
        data_dir / "EXISTING_376_PROVISIONAL_DECISIONS.tsv",
        {
            "decision_id",
            "review_queue_id",
            "descriptor_assertion_id",
            "current_disposition",
            "descriptor_class",
            "review_state",
            "review_actor_type",
            "source_file_sha256",
            "source_text_sha256",
            "human_confirmed",
            "expert_adjudicated",
            "counts_as_reviewed_descriptor",
            "model_eligible",
        },
    )
    require(len(existing_queue) == 376, "existing review queue must contain 376 candidates")
    require(len(existing_decisions) == 376, "existing decisions must contain 376 candidates")
    existing_queue_by_assertion = index_unique(existing_queue, "descriptor_assertion_id", "existing queue")
    existing_decision_by_assertion = index_unique(existing_decisions, "descriptor_assertion_id", "existing decisions")
    require(set(existing_queue_by_assertion) == set(existing_decision_by_assertion), "existing queue/decision assertion sets differ")
    for assertion_id, row in existing_queue_by_assertion.items():
        require(row["current_disposition"] == "NON_DESCRIPTOR", f"{assertion_id}: expected NON_DESCRIPTOR")
        require(row["descriptor_class"] == "NON_DESCRIPTOR", f"{assertion_id}: expected NON_DESCRIPTOR class")
        require(row["review_state"] == "REJECTED_NON_DESCRIPTOR", f"{assertion_id}: wrong review state")
        require(row["review_actor_type"] == "CODEX_SOURCE_AUDITOR", f"{assertion_id}: wrong provisional actor")
        require_sha256(row["source_file_sha256"], f"{assertion_id}.source_file_sha256")
        require_sha256(row["raw_record_sha256"], f"{assertion_id}.raw_record_sha256")
        require_sha256(row["source_text_sha256"], f"{assertion_id}.source_text_sha256")
        require(row["source_text_storage_state"] == "HASH_ONLY", f"{assertion_id}: source text must be hash-only")
        require(not parse_bool(row["human_review_required"], f"{assertion_id}.human_review_required"), f"{assertion_id}: rejected metadata must not request descriptor review")
        require(not parse_bool(row["model_eligible"], f"{assertion_id}.model_eligible"), f"{assertion_id}: rejected metadata marked model eligible")
        decision = existing_decision_by_assertion[assertion_id]
        require(decision["review_queue_id"] == row["review_queue_id"], f"{assertion_id}: queue identity changed")
        require(decision["current_disposition"] == row["current_disposition"], f"{assertion_id}: decision disposition mismatch")
        require(decision["source_file_sha256"] == row["source_file_sha256"], f"{assertion_id}: decision file hash mismatch")
        require(decision["source_text_sha256"] == row["source_text_sha256"], f"{assertion_id}: decision text hash mismatch")
        for flag in ("human_confirmed", "expert_adjudicated", "counts_as_reviewed_descriptor", "model_eligible"):
            require(not parse_bool(decision[flag], f"{assertion_id}.{flag}"), f"{assertion_id}: provisional decision set {flag}")

    queue = read_tsv(data_dir / "DESCRIPTOR_REVIEW_QUEUE.tsv", queue_columns)
    decisions = read_tsv(data_dir / "DESCRIPTOR_PROVISIONAL_DECISIONS.tsv", set(existing_decisions[0]))
    require(len(queue) == 516, f"merged review queue count {len(queue)} != 516")
    require(len(decisions) == 516, f"merged decision count {len(decisions)} != 516")
    queue_by_assertion = index_unique(queue, "descriptor_assertion_id", "merged queue")
    decision_by_assertion = index_unique(decisions, "descriptor_assertion_id", "merged decisions")
    require(set(queue_by_assertion) == set(decision_by_assertion), "merged queue/decision assertion sets differ")
    require(set(existing_queue_by_assertion) <= set(queue_by_assertion), "existing 376 candidates missing from merged queue")
    require(Counter(row["descriptor_class"] for row in queue) == Counter({"NON_DESCRIPTOR": 376, "STRICT_FLAVOR": 86, "BROAD_SENSORY": 54}), "merged candidate classes changed")
    require(Counter(row["current_disposition"] for row in queue) == Counter({"NON_DESCRIPTOR": 376, "HUMAN_REVIEW_REQUIRED": 140}), "merged dispositions changed")
    require(Counter(row["review_state"] for row in queue) == Counter({"REJECTED_NON_DESCRIPTOR": 376, "PROVISIONAL_MACHINE_CLASSIFIED": 140}), "merged review states changed")
    for assertion_id, row in queue_by_assertion.items():
        require(row["source_text_storage_state"] == "HASH_ONLY", f"{assertion_id}: public queue text is not hash-only")
        require_sha256(row["source_text_sha256"], f"{assertion_id}.source_text_sha256")
        scoped_file_hash(row, f"queue {assertion_id}")
        require(not parse_bool(row["model_eligible"], f"{assertion_id}.model_eligible"), f"{assertion_id}: queue row marked model eligible")
        decision = decision_by_assertion[assertion_id]
        require(decision["review_queue_id"] == row["review_queue_id"], f"{assertion_id}: merged queue identity mismatch")
        require(decision["current_disposition"] == row["current_disposition"], f"{assertion_id}: merged disposition mismatch")
        require(decision["source_text_sha256"] == row["source_text_sha256"], f"{assertion_id}: merged source text hash mismatch")
        for flag in ("human_confirmed", "expert_adjudicated", "counts_as_reviewed_descriptor", "model_eligible"):
            require(not parse_bool(decision[flag], f"{assertion_id}.{flag}"), f"{assertion_id}: provisional decision set {flag}")
        require(decision["review_actor_type"] not in {"HUMAN_REVIEWER", "EXPERT_REVIEWER"}, f"{assertion_id}: provisional actor impersonates reviewer")
    return queue_by_assertion, decision_by_assertion


def validate_rights(data_dir: Path, queue: Mapping[str, Mapping[str, str]]) -> None:
    rights = read_tsv(
        data_dir / "DESCRIPTOR_RIGHTS_DECISION.tsv",
        {
            "rights_decision_id",
            "descriptor_assertion_id",
            "source_artifact_id",
            "purpose",
            "rights_state",
            "decision_basis",
            "rights_evidence_locator",
            "review_actor_type",
            "model_eligibility_effect",
        },
    )
    require(len(rights) == 3_096, f"rights row count {len(rights)} != 3096")
    index_unique(rights, "rights_decision_id", "rights decisions")
    grouped: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for row in rights:
        assertion_id = row["descriptor_assertion_id"]
        require(assertion_id in queue, f"rights row references unknown assertion {assertion_id}")
        require(row["source_artifact_id"] == queue[assertion_id]["source_artifact_id"], f"{assertion_id}: rights artifact mismatch")
        require(row["rights_state"] in {"AFFIRMATIVE", "PENDING", "UNKNOWN", "PROHIBITED", "NOT_APPLICABLE"}, f"{assertion_id}: invalid rights state")
        require(row["decision_basis"] != "" and row["rights_evidence_locator"] != "", f"{assertion_id}: incomplete rights evidence")
        if row["purpose"] in {"MODEL_RESEARCH", "DEPLOYMENT_OR_COMMERCIAL_MODEL"}:
            require(row["rights_state"] != "AFFIRMATIVE", f"{assertion_id}: public visibility created affirmative model/deployment rights")
            require("SUPPORTS" not in row["model_eligibility_effect"], f"{assertion_id}: nonaffirmative rights support eligibility")
        grouped[assertion_id].append(row)
    require(set(grouped) == set(queue), "rights decisions do not cover every queued candidate")
    for assertion_id, rows in grouped.items():
        require(len(rows) == 6, f"{assertion_id}: expected six purpose-specific rights rows")
        require({row["purpose"] for row in rows} == RIGHTS_PURPOSES, f"{assertion_id}: incomplete rights-purpose set")
        require(len({row["purpose"] for row in rows}) == 6, f"{assertion_id}: duplicate rights purpose")

    live_ids = {key for key in queue if key.startswith("assertion:")}
    existing_ids = set(queue) - live_ids
    require(len(live_ids) == 140 and len(existing_ids) == 376, "rights candidate universes changed")
    live_state = Counter()
    for assertion_id in live_ids:
        states = {row["rights_state"] for row in grouped[assertion_id]}
        require(len(states) == 1, f"{assertion_id}: pilot singular rights state not consistently expanded")
        live_state[next(iter(states))] += 1
    require(live_state == Counter({"PENDING": 73, "UNKNOWN": 67}), "live rights-state distribution changed")
    require(all({row["rights_state"] for row in grouped[key]} == {"UNKNOWN"} for key in existing_ids), "existing rejected candidates must retain UNKNOWN rights")


def validate_live_assertions(
    data_dir: Path,
    generated_dir: Path,
    queue: Mapping[str, Mapping[str, str]],
) -> tuple[dict[str, Mapping[str, str]], dict[str, Mapping[str, str]]]:
    ledger = read_tsv(
        data_dir / "DESCRIPTOR_ASSERTION_LEDGER.tsv",
        {
            "descriptor_assertion_id",
            "effective_record_id",
            "source_artifact_id",
            "source_route_id",
            "schema_signature_id",
            "publication_layer",
            "source_field_label",
            "source_selector_or_locator",
            "source_page_or_record_locator",
            "raw_field_text",
            "raw_field_text_sha256",
            "atomic_source_text",
            "atomic_source_text_sha256",
            "source_native_lexical_form",
            "source_native_lexical_form_sha256",
            "normalized_candidate_form",
            "evidence_tier",
            "evidence_origin_type",
            "review_state",
            "review_actor_type",
            "rights_decision_id",
            "source_file_sha256",
            "route_index_sha256",
            "source_file_sha256_scope",
            "source_file_nonstorage_reason",
            "source_text_storage_state",
            "counts_as_reviewed_descriptor",
            "model_eligible",
        },
    )
    require(len(ledger) == 140, f"live ledger row count {len(ledger)} != 140")
    assertion_by_id = index_unique(ledger, "descriptor_assertion_id", "live assertion ledger")
    require(set(assertion_by_id) == {key for key in queue if key.startswith("assertion:")}, "live ledger/queue assertion sets differ")
    require(Counter(row["descriptor_class"] for row in ledger) == Counter({"STRICT_FLAVOR": 86, "BROAD_SENSORY": 54}), "live strict/broad counts changed")
    require(Counter(row["evidence_tier"] for row in ledger) == Counter({"P2": 73, "UNRESOLVED": 67}), "live tier counts changed")
    require(Counter(row["review_state"] for row in ledger) == Counter({"PROVISIONAL_MACHINE_CLASSIFIED": 140}), "live assertions are not all provisional")
    require(len({row["effective_record_id"] for row in ledger}) == 8, "live effective-record count must be 8")
    require(len({row["source_route_id"] for row in ledger}) == 3, "live source route count must be 3")
    for assertion_id, row in assertion_by_id.items():
        require(row["raw_field_text"] == "", f"{assertion_id}: raw field text leaked into public ledger")
        require(row["atomic_source_text"] == "", f"{assertion_id}: atomic source text leaked into public ledger")
        require(row["source_native_lexical_form"] == "", f"{assertion_id}: source-native lexical text leaked into public ledger")
        require(row["normalized_candidate_form"] == "", f"{assertion_id}: unreviewed normalized form populated")
        for column in ("raw_field_text_sha256", "atomic_source_text_sha256", "source_native_lexical_form_sha256"):
            require_sha256(row[column], f"{assertion_id}.{column}")
        require(row["source_text_storage_state"] == "HASH_ONLY", f"{assertion_id}: source text must be hash-only")
        scoped_file_hash(row, f"ledger {assertion_id}")
        require(not parse_bool(row["counts_as_reviewed_descriptor"], f"{assertion_id}.counts_as_reviewed_descriptor"), f"{assertion_id}: provisional assertion counted as reviewed")
        require(not parse_bool(row["model_eligible"], f"{assertion_id}.model_eligible"), f"{assertion_id}: provisional assertion marked model eligible")
        require(row["review_actor_type"] not in {"HUMAN_REVIEWER", "EXPERT_REVIEWER"}, f"{assertion_id}: parser impersonates reviewer")
        require(row["source_route_id"] == queue[assertion_id]["source_route_id"], f"{assertion_id}: queue route mismatch")
        require(row["source_artifact_id"] == queue[assertion_id]["source_artifact_id"], f"{assertion_id}: queue artifact mismatch")

    public_live = read_tsv(generated_dir / "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv", set(read_tsv(generated_dir / "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv")[0]))
    require(len(public_live) == 140, "public-safe live export must contain 140 rows")
    require(set(index_unique(public_live, "descriptor_assertion_id", "public live export")) == set(assertion_by_id), "public live export/ledger identities differ")

    duplicate_rows = read_tsv(
        data_dir / "DUPLICATE_REPEAT_DECISION.tsv",
        {"descriptor_assertion_id", "deduplication_disposition", "within_record_repeat_group", "cross_observation_repeat_group", "counts_as_assertion", "counts_as_record_unique_descriptor"},
    )
    require(len(duplicate_rows) == 516, "duplicate ledger must cover 516 candidates")
    duplicate_by_assertion = index_unique(duplicate_rows, "descriptor_assertion_id", "duplicate decisions")
    require(set(duplicate_by_assertion) == set(queue), "duplicate decisions do not cover queue")
    live_duplicates = [duplicate_by_assertion[key] for key in assertion_by_id]
    require(Counter(row["deduplication_disposition"] for row in live_duplicates) == Counter({"CANONICAL": 137, "CROSS_OBSERVATION_REPEAT": 2, "EXACT_WITHIN_FIELD_REPEAT": 1}), "live duplicate disposition changed")
    require(sum(parse_bool(row["counts_as_assertion"], "counts_as_assertion") for row in live_duplicates) == 139, "assertion-level de-inflated count must be 139")
    require(sum(parse_bool(row["counts_as_record_unique_descriptor"], "counts_as_record_unique_descriptor") for row in live_duplicates) == 137, "record-level unique count must be 137")

    pairs = read_tsv(
        data_dir / "COASSERTION_EVENT.tsv",
        {"coassertion_event_id", "effective_record_id", "left_descriptor_assertion_id", "right_descriptor_assertion_id", "evidence_tier", "publication_layer"},
    )
    require(len(pairs) == 508, f"P1/P2 supported pair count {len(pairs)} != 508")
    index_unique(pairs, "coassertion_event_id", "coassertion events")
    unordered_pairs: set[frozenset[str]] = set()
    for row in pairs:
        left_id = row["left_descriptor_assertion_id"]
        right_id = row["right_descriptor_assertion_id"]
        require(left_id != right_id, f"pair {row['coassertion_event_id']}: self-pair")
        require(left_id in assertion_by_id and right_id in assertion_by_id, f"pair {row['coassertion_event_id']}: unknown assertion")
        pair_key = frozenset((left_id, right_id))
        require(pair_key not in unordered_pairs, f"pair {row['coassertion_event_id']}: duplicate unordered edge")
        unordered_pairs.add(pair_key)
        left = assertion_by_id[left_id]
        right = assertion_by_id[right_id]
        require(left["effective_record_id"] == right["effective_record_id"] == row["effective_record_id"], f"pair {row['coassertion_event_id']}: crosses effective-record boundary")
        require(left["source_artifact_id"] == right["source_artifact_id"], f"pair {row['coassertion_event_id']}: crosses source artifact")
        require(left["source_selector_or_locator"] == right["source_selector_or_locator"], f"pair {row['coassertion_event_id']}: crosses source observation")
        require(left["evidence_tier"] == right["evidence_tier"] == row["evidence_tier"] == "P2", f"pair {row['coassertion_event_id']}: not a supported P1/P2 event")
        require(left["publication_layer"] == right["publication_layer"] == row["publication_layer"] == "PRIMARY_JURY_DESCRIPTION", f"pair {row['coassertion_event_id']}: crosses publication layer")

    artifacts = read_tsv(
        generated_dir / "PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv",
        {"source_artifact_id", "source_route_id", "schema_signature_id", "governed_locator", "source_retrieved_at", "source_file_sha256", "file_size_bytes", "storage_state", "non_storage_reason", "parser_version", "adapter_version"},
    )
    artifact_by_id = index_unique(artifacts, "source_artifact_id", "public-safe source artifacts")
    require(len(artifact_by_id) == 8, "live source-artifact bridge must contain 8 rows")
    require(set(artifact_by_id) == {row["source_artifact_id"] for row in ledger}, "source-artifact bridge does not cover live ledger")
    for artifact_id, row in artifact_by_id.items():
        require_sha256(row["source_file_sha256"], f"{artifact_id}.source_file_sha256")
        require(row["storage_state"] == "HASH_AND_LOCATOR_ONLY", f"{artifact_id}: live artifact must be hash/locator only")
        require(row["non_storage_reason"] != "", f"{artifact_id}: missing non-storage reason")
        require(parse_int(row["file_size_bytes"], f"{artifact_id}.file_size_bytes") >= 0, f"{artifact_id}: negative byte count")
        for assertion in (item for item in ledger if item["source_artifact_id"] == artifact_id):
            require(scoped_file_hash(assertion, f"ledger {assertion['descriptor_assertion_id']}") == row["source_file_sha256"], f"{assertion['descriptor_assertion_id']}: artifact hash lineage mismatch")

    bridges = read_tsv(
        generated_dir / "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv",
        {"round3m_effective_record_id", "effective_record_key", "series_id", "edition_id", "edition_year", "category_id", "round_id", "subject_kind", "entry_or_lot_id", "preparation_service_code", "preparation_evidence_locator", "source_route_id", "source_artifact_id", "source_record_locator", "source_file_sha256", "record_identity_sha256", "identity_resolution_state", "synthetic_generated", "preparation_inferred_from_descriptor"},
    )
    bridge_by_id = index_unique(bridges, "round3m_effective_record_id", "effective-record bridge")
    require(len(bridge_by_id) == 8, "effective-record bridge must contain 8 rows")
    require(set(bridge_by_id) == {row["effective_record_id"] for row in ledger}, "effective-record bridge does not cover live ledger")
    for bridge_id, row in bridge_by_id.items():
        require(row["source_artifact_id"] in artifact_by_id, f"{bridge_id}: unknown source artifact")
        artifact = artifact_by_id[row["source_artifact_id"]]
        require(row["source_route_id"] == artifact["source_route_id"], f"{bridge_id}: artifact route mismatch")
        require(row["source_file_sha256"] == artifact["source_file_sha256"], f"{bridge_id}: artifact hash mismatch")
        require_sha256(row["record_identity_sha256"], f"{bridge_id}.record_identity_sha256")
        require(1900 <= parse_int(row["edition_year"], f"{bridge_id}.edition_year") <= 2100, f"{bridge_id}: invalid edition year")
        require(row["subject_kind"] in {"ENTRY", "LOT"}, f"{bridge_id}: invalid subject kind")
        require(row["identity_resolution_state"] == "SOURCE_NATIVE_PROVISIONAL", f"{bridge_id}: unexpected identity resolution")
        require(not parse_bool(row["synthetic_generated"], f"{bridge_id}.synthetic_generated"), f"{bridge_id}: synthetic record")
        require(not parse_bool(row["preparation_inferred_from_descriptor"], f"{bridge_id}.preparation_inferred_from_descriptor"), f"{bridge_id}: preparation inferred from descriptors")
    return assertion_by_id, bridge_by_id


def validate_auxiliary_ledgers(data_dir: Path, queue_ids: set[str]) -> None:
    for filename, key in (
        ("DESCRIPTOR_PROVENANCE_DECISION.tsv", "provenance_decision_id"),
        ("PUBLICATION_LAYER_RELATION.tsv", "publication_layer_relation_id"),
        ("DESCRIPTOR_NORMALIZATION_DECISION.tsv", "normalization_decision_id"),
    ):
        rows = read_tsv(data_dir / filename, {key, "descriptor_assertion_id"})
        require(len(rows) == 516, f"{filename}: expected 516 rows")
        index_unique(rows, key, filename)
        require({row["descriptor_assertion_id"] for row in rows} == queue_ids, f"{filename}: assertion coverage mismatch")

    normalization = read_tsv(
        data_dir / "DESCRIPTOR_NORMALIZATION_DECISION.tsv",
        {"descriptor_assertion_id", "normalized_candidate_form", "normalization_operation", "source_native_lexical_form_count_effect", "normalized_form_count_effect"},
    )
    require(all(row["normalized_candidate_form"] == "" for row in normalization), "unreviewed normalization target populated")
    require(all(row["source_native_lexical_form_count_effect"] == "0" and row["normalized_form_count_effect"] == "0" for row in normalization), "hash-only provisional rows inflated lexical counts")


def validate_gates_and_controls(data_dir: Path, generated_dir: Path) -> None:
    gates = read_tsv(
        data_dir / "DESCRIPTOR_GATE_STATUS.tsv",
        {"gate_version", "gate_name", "metric_name", "observed_value", "required_value", "pass", "not_applicable", "rights_blocker", "data_blocker", "review_blocker"},
    )
    require(len(gates) == 56, f"gate criterion count {len(gates)} != 56")
    require(len({(row["gate_version"], row["gate_name"], row["metric_name"]) for row in gates}) == 56, "duplicate gate criterion")
    require(all(not parse_bool(row["pass"], f"gate {row['gate_name']}/{row['metric_name']}") for row in gates), "a descriptor gate passed with no human-reviewed corpus")
    for row in gates:
        if row["observed_value"] == "NA":
            require(parse_bool(row["not_applicable"], f"gate {row['gate_name']}/{row['metric_name']}.not_applicable"), "NA gate metric not marked not_applicable")
            require(not parse_bool(row["pass"], f"gate {row['gate_name']}/{row['metric_name']}.pass"), "NA gate metric passed")
        require(parse_bool(row["review_blocker"], f"gate {row['gate_name']}/{row['metric_name']}.review_blocker"), "zero-human-review gate lacks review blocker")

    blocker_rows = read_tsv(
        data_dir / "ROUND3M_RESEARCH_ARTIFACT_BLOCKER.tsv",
        {"blocker_type", "blocker_state", "required_artifact_count", "available_artifact_count", "missing_artifact_names", "effect"},
    )
    require(len(blocker_rows) == 1, "expected exactly one machine-artifact blocker")
    blocker = blocker_rows[0]
    require(blocker["blocker_type"] == "MISSING_MACHINE_READABLE_RESEARCH_ARTIFACTS", "wrong machine-artifact blocker type")
    require(blocker["blocker_state"] == "OPEN", "machine-artifact blocker must remain open")
    require(blocker["required_artifact_count"] == "9" and blocker["available_artifact_count"] == "0", "machine-artifact blocker counts changed")
    require(set(blocker["missing_artifact_names"].split(";")) == MISSING_RESEARCH_ARTIFACTS, "machine-artifact blocker names changed")
    require("NOT_IMPORTED_OR_RECONSTRUCTED" in blocker["effect"], "blocker must forbid PDF row reconstruction")

    c0_c1 = read_json(data_dir / "C0_C1_EVIDENCE_RECEIPT.json")
    require(isinstance(c0_c1, dict), "C0/C1 receipt must be an object")
    require(c0_c1.get("direct_source_roast_value_present_count") == 7_683, "direct roast-value count changed")
    require(c0_c1.get("direct_source_roast_scheme_present_count") == 7_683, "direct roast-scheme count changed")
    require(c0_c1.get("reviewed_c1_mapping_count") == 0, "C1 mappings were promoted without review")
    require(c0_c1.get("c1_promotion_count") == 0, "C1 promotion must remain zero")
    policy = c0_c1.get("policy", {})
    require(policy.get("tasting_descriptors_used_to_infer_roast") is False, "descriptors were used to infer roast")
    require(policy.get("preparation_service_requires_explicit_source_evidence") is True, "preparation evidence policy weakened")

    live_metrics = read_json(generated_dir / "LIVE_ADAPTER_METRICS.json")
    require(isinstance(live_metrics, dict), "live adapter metrics must be an object")
    expected_values = {
        "segmented_atomic_candidate_count": 140,
        "assertion_level_deinflated_count": 139,
        "record_level_unique_count": 137,
        "effective_record_count": 8,
        "live_source_adapter_count": 4,
        "live_source_adapter_validated_count": 3,
        "completed_wcc_scoresheet_live_positive_count": 0,
        "model_eligible_count": 0,
    }
    for key, expected in expected_values.items():
        require(live_metrics.get(key) == expected, f"live metric {key} changed: {live_metrics.get(key)!r}")
    require(live_metrics.get("class_counts") == {"BROAD_SENSORY": 54, "STRICT_FLAVOR": 86}, "live class receipt changed")
    require(live_metrics.get("tier_counts") == {"P2": 73, "UNRESOLVED": 67}, "live tier receipt changed")
    require(live_metrics.get("rights_counts") == {"PENDING": 73, "UNKNOWN": 67}, "live rights receipt changed")
    require(live_metrics.get("raw_source_text_published") is False, "live metrics claim raw source text publication")


def validate_analyst_time(data_dir: Path) -> None:
    rows = read_tsv(
        data_dir / "ANALYST_TIME_LOG.tsv",
        {"analyst_time_log_key", "task_type", "source_route_id", "artifact_count", "candidate_count", "reviewed_count", "started_at", "ended_at", "active_minutes", "automated_runtime_seconds", "review_actor_type", "notes"},
    )
    require(bool(rows), "Round 3M analyst-equivalent time log is empty")
    index_unique(rows, "analyst_time_log_key", "analyst time log")
    total_active = 0.0
    for row in rows:
        try:
            active = float(row["active_minutes"])
            runtime_text = row["automated_runtime_seconds"]
            runtime = (
                None
                if runtime_text.startswith("NA_")
                else float(runtime_text)
            )
        except ValueError as exc:
            raise ContractError(f"analyst time {row['analyst_time_log_key']}: invalid numeric value") from exc
        require(
            active >= 0 and (runtime is None or runtime >= 0),
            f"analyst time {row['analyst_time_log_key']}: negative duration",
        )
        source_route_id = row["source_route_id"]
        require(
            source_route_id.startswith("route.")
            or (source_route_id == "" and "MULTIPLE_ROUTES" in row["notes"]),
            f"analyst time {row['analyst_time_log_key']}: invalid source route scope",
        )
        require(parse_int(row["artifact_count"], "artifact_count") >= 0, "negative artifact count")
        require(parse_int(row["candidate_count"], "candidate_count") >= 0, "negative candidate count")
        require(row["reviewed_count"] == "0", f"analyst time {row['analyst_time_log_key']}: fabricated reviewed descriptors")
        require(row["review_actor_type"] not in {"HUMAN_REVIEWER", "EXPERT_REVIEWER"}, f"analyst time {row['analyst_time_log_key']}: undocumented human actor")
        require(row["notes"] != "", f"analyst time {row['analyst_time_log_key']}: missing notes")
        total_active += active
    require(total_active > 0, "analyst-equivalent active minutes were not recorded")


def validate_no_training_artifacts(data_dir: Path, generated_dir: Path) -> None:
    for root in (data_dir, generated_dir):
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            require(path.suffix.lower() not in FORBIDDEN_TRAINING_SUFFIXES, f"forbidden model-weight artifact: {path}")
            lowered = path.name.lower()
            require(not re.search(r"(^|[-_.])(trained[-_]?model|model[-_]?weights|training[-_]?corpus)([-_.]|$)", lowered), f"forbidden training artifact name: {path}")


def validate_artifacts(data_dir: Path, generated_dir: Path, allow_incomplete_finalization: bool) -> dict[str, int]:
    require(data_dir.is_dir(), f"data directory not found: {data_dir}")
    require(generated_dir.is_dir(), f"generated directory not found: {generated_dir}")
    required_data = REQUIRED_REVIEW_OUTPUTS | (REQUIRED_MACHINE_OUTPUTS if not allow_incomplete_finalization else REQUIRED_MACHINE_OUTPUTS - {"ANALYST_TIME_LOG.tsv", "ROUND3M_EXPECTED_STATE.tsv", "ROUND3M_MANIFEST.json", "SHA256SUMS"})
    missing_data = sorted(name for name in required_data if not (data_dir / name).is_file())
    require(not missing_data, f"missing required Round 3M data outputs: {missing_data}")
    missing_generated = sorted(name for name in REQUIRED_GENERATED_OUTPUTS if not (generated_dir / name).is_file())
    require(not missing_generated, f"missing required live adapter outputs: {missing_generated}")

    validate_baseline(data_dir)
    validate_schema_and_policy(data_dir)
    queue, _ = validate_candidate_review(data_dir)
    validate_rights(data_dir, queue)
    assertions, bridges = validate_live_assertions(data_dir, generated_dir, queue)
    validate_auxiliary_ledgers(data_dir, set(queue))
    validate_gates_and_controls(data_dir, generated_dir)
    validate_review_manifest(data_dir)
    if not allow_incomplete_finalization:
        validate_analyst_time(data_dir)
        validate_final_checksums(data_dir)
        manifest = read_json(data_dir / "ROUND3M_MANIFEST.json")
        require(isinstance(manifest, dict), "Round 3M manifest must be an object")
    validate_no_training_artifacts(data_dir, generated_dir)
    return {
        "census_items": 480,
        "source_routes": 131,
        "independent_source_families": 11,
        "review_queue_items": len(queue),
        "rights_decisions": 3_096,
        "live_assertions": len(assertions),
        "live_effective_records": len(bridges),
        "assertion_level_deinflated": 139,
        "record_level_unique": 137,
        "coassertion_events": 508,
        "human_confirmed": 0,
        "expert_adjudicated": 0,
        "model_eligible": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--generated-dir", type=Path, default=DEFAULT_GENERATED_DIR)
    parser.add_argument(
        "--allow-incomplete-finalization",
        action="store_true",
        help="development-only: do not require final analyst log, manifest, expected-state, or SHA256SUMS",
    )
    args = parser.parse_args()
    try:
        metrics = validate_artifacts(
            args.data_dir.resolve(),
            args.generated_dir.resolve(),
            args.allow_incomplete_finalization,
        )
    except ContractError as exc:
        print(f"ROUND3M_ARTIFACT_CONTRACT_FAIL {exc}", file=sys.stderr)
        return 1
    print("ROUND3M_ARTIFACT_CONTRACT_PASS " + " ".join(f"{key}={value}" for key, value in metrics.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
