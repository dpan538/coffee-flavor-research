#!/usr/bin/env python3
"""Source-neutral artifact contract for Round 3K competition adapters.

The adapter boundary accepts only explicit fields and verbatim source spans. It
does not parse source semantics, assign ontology targets, or infer preparation,
roast, or descriptors. Source-specific parsers can emit this one contract for
all supported acquisition formats.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence


CONTRACT_VERSION = "round3k.source-adapter.v1"

REQUIRED_TABLE_FILES = (
    "RAW_SERIES.tsv",
    "RAW_EDITION.tsv",
    "RAW_ENTRY.tsv",
    "RAW_COFFEE_IDENTITY.tsv",
    "RAW_PREPARATION_SERVICE.tsv",
    "RAW_SCORE.tsv",
    "RAW_DESCRIPTOR_ASSERTION.tsv",
    "NORMALIZATION_REPORT.tsv",
    "DUPLICATE_REPEAT_REPORT.tsv",
    "RIGHTS_REPORT.tsv",
    "EFFECTIVE_RECORD_REPORT.tsv",
)

REQUIRED_FILES = (
    "SOURCE_MANIFEST.json",
    "SHA256SUMS",
    *REQUIRED_TABLE_FILES,
)

RIGHTS_DIMENSIONS = (
    "PUBLIC_RESULTS_USE",
    "PUBLIC_DESCRIPTOR_USE",
    "INTERNAL_RESEARCH_USE",
    "PUBLIC_DERIVED_RELEASE",
    "MODEL_RESEARCH_USE",
    "COMMERCIAL_MODEL_USE",
)

QUALITY_THRESHOLDS = {
    "ENTRY_IDENTITY_FIELD_ACCURACY": (">=", Decimal("0.99")),
    "SCORE_FIELD_ACCURACY": (">=", Decimal("0.99")),
    "DESCRIPTOR_SPAN_PRECISION": (">=", Decimal("0.97")),
    "FALSE_FLAVOR_DOCUMENT_RATE": ("<=", Decimal("0.02")),
    "DUPLICATE_LINKAGE_ACCURACY": (">=", Decimal("0.98")),
}


@dataclass(frozen=True)
class AdapterProfile:
    """A format profile; every profile emits the same table contract."""

    source_kind: str
    accepted_authorizations: frozenset[str]
    binary_source: bool = False


SOURCE_PROFILES = {
    "OFFICIAL_HTML_RESULTS": AdapterProfile(
        "OFFICIAL_HTML_RESULTS", frozenset({"PUBLIC_OFFICIAL"})
    ),
    "OFFICIAL_AUCTION_HTML": AdapterProfile(
        "OFFICIAL_AUCTION_HTML", frozenset({"PUBLIC_OFFICIAL"})
    ),
    "OFFICIAL_PDF_CATALOG": AdapterProfile(
        "OFFICIAL_PDF_CATALOG", frozenset({"PUBLIC_OFFICIAL"}), True
    ),
    "OFFICIAL_PDF_RESULTS": AdapterProfile(
        "OFFICIAL_PDF_RESULTS", frozenset({"PUBLIC_OFFICIAL"}), True
    ),
    "CSV_EXPORT": AdapterProfile(
        "CSV_EXPORT", frozenset({"PUBLIC_OFFICIAL", "AUTHORIZED_EXPORT"})
    ),
    "TSV_EXPORT": AdapterProfile(
        "TSV_EXPORT", frozenset({"PUBLIC_OFFICIAL", "AUTHORIZED_EXPORT"})
    ),
    "XLSX_SCORE_EXPORT": AdapterProfile(
        "XLSX_SCORE_EXPORT",
        frozenset({"PUBLIC_OFFICIAL", "AUTHORIZED_EXPORT"}),
        True,
    ),
    "JSON_API_PAYLOAD": AdapterProfile(
        "JSON_API_PAYLOAD",
        frozenset({"PUBLIC_OFFICIAL", "AUTHORIZED_EXPORT"}),
    ),
    "AWARD_FORCE_AUTHORIZED_EXPORT": AdapterProfile(
        "AWARD_FORCE_AUTHORIZED_EXPORT", frozenset({"AUTHORIZED_EXPORT"})
    ),
    "COMPETITION_PLATFORM_AUTHORIZED_EXPORT": AdapterProfile(
        "COMPETITION_PLATFORM_AUTHORIZED_EXPORT",
        frozenset({"AUTHORIZED_EXPORT"}),
    ),
    "PERMITTED_TRANSCRIPT": AdapterProfile(
        "PERMITTED_TRANSCRIPT", frozenset({"PERMITTED_TRANSCRIPT"})
    ),
}

SUPPORTED_SOURCE_KINDS = tuple(SOURCE_PROFILES)

TABLE_SCHEMAS: dict[str, tuple[str, ...]] = {
    "RAW_SERIES.tsv": (
        "series_id",
        "source_family_id",
        "official_name",
        "source_locator",
        "source_record_id",
        "source_text",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "RAW_EDITION.tsv": (
        "edition_id",
        "series_id",
        "official_name",
        "competition_year",
        "source_locator",
        "source_record_id",
        "source_text",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "RAW_ENTRY.tsv": (
        "entry_id",
        "edition_id",
        "source_entry_id",
        "competitor_name",
        "entry_name",
        "competition_category",
        "placement",
        "source_locator",
        "source_text",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "RAW_COFFEE_IDENTITY.tsv": (
        "coffee_identity_id",
        "entry_id",
        "source_coffee_id",
        "coffee_name",
        "country",
        "region",
        "producer",
        "farm",
        "variety",
        "process",
        "lot_name",
        "source_locator",
        "source_text",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "RAW_PREPARATION_SERVICE.tsv": (
        "preparation_service_id",
        "entry_id",
        "coffee_identity_id",
        "round_name",
        "service_sequence",
        "preparation_family_source_text",
        "preparation_family_code",
        "preparation_evidence",
        "fresh_preparation_confirmed",
        "fresh_preparation_evidence",
        "roast_source_text",
        "roast_code",
        "roast_evidence",
        "source_locator",
        "source_text",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "RAW_SCORE.tsv": (
        "score_id",
        "preparation_service_id",
        "judge_observation_id",
        "score_name",
        "score_value",
        "score_scale_min",
        "score_scale_max",
        "score_unit",
        "score_role",
        "source_locator",
        "source_text",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "RAW_DESCRIPTOR_ASSERTION.tsv": (
        "descriptor_assertion_id",
        "preparation_service_id",
        "judge_observation_id",
        "assertion_actor_role",
        "descriptor_text",
        "source_span",
        "source_span_start",
        "source_span_end",
        "assertion_type",
        "extraction_method",
        "label_disposition",
        "source_locator",
        "structural_test_fixture",
        "core_count_eligible",
    ),
    "NORMALIZATION_REPORT.tsv": (
        "normalization_id",
        "target_file",
        "target_record_id",
        "field_name",
        "raw_value",
        "normalized_value",
        "normalization_rule",
        "semantic_change",
        "review_status",
    ),
    "DUPLICATE_REPEAT_REPORT.tsv": (
        "relationship_id",
        "left_record_type",
        "left_record_id",
        "right_record_type",
        "right_record_id",
        "relationship_type",
        "decision_basis",
        "review_status",
    ),
    "RIGHTS_REPORT.tsv": (
        "rights_id",
        "source_family_id",
        "public_results_use",
        "public_descriptor_use",
        "internal_research_use",
        "public_derived_release",
        "model_research_use",
        "commercial_model_use",
        "rights_decision_status",
        "evidence_locator",
        "review_status",
    ),
    "EFFECTIVE_RECORD_REPORT.tsv": (
        "effective_record_id",
        "entry_id",
        "coffee_identity_id",
        "preparation_service_id",
        "effective_record_type",
        "observed_core_eligible",
        "model_eligible",
        "auxiliary_eligible",
        "exclusion_reason",
        "judge_observation_count",
        "descriptor_assertion_count",
        "structural_test_fixture",
    ),
}

_MANIFEST_REQUIRED_KEYS = frozenset(
    {
        "contract_version",
        "adapter_id",
        "adapter_version",
        "source_kind",
        "source_family_id",
        "snapshot_id",
        "adapter_status",
        "acquisition_authorization",
        "generated_at",
        "structural_test_fixture",
        "contains_observed_coffee_data",
        "core_count_eligible",
        "semantic_inference_permitted",
        "llm_generated_fields_permitted",
        "record_count_basis",
        "rights_dimensions",
        "source_files",
        "output_files",
        "record_counts",
        "quality_gate_policy",
        "quality_gate_results",
    }
)

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_SHA_LINE = re.compile(r"^([0-9a-f]{64})  (.+)$")
_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)
_RIGHTS_VALUES = frozenset({"true", "false", "pending"})
_BOOL_VALUES = frozenset({"true", "false"})


class ContractViolation(ValueError):
    """A stable, machine-testable adapter contract failure."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class ValidationSummary:
    bundle_path: Path
    source_kind: str
    adapter_status: str
    structural_test_fixture: bool
    table_counts: Mapping[str, int]
    verified_file_count: int


def _fail(code: str, message: str) -> None:
    raise ContractViolation(code, message)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _safe_relative_path(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        _fail("UNSAFE_PATH", f"{field} must be a non-empty relative path")
    if "\\" in value:
        _fail("UNSAFE_PATH", f"{field} must use POSIX separators: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        _fail("UNSAFE_PATH", f"{field} is not a safe relative path: {value!r}")
    return value


def _require_string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        _fail("MANIFEST_FIELD", f"manifest {key} must be a non-empty string")
    return value


def _require_bool(mapping: Mapping[str, object], key: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        _fail("MANIFEST_FIELD", f"manifest {key} must be a JSON boolean")
    return value


def _validate_id(value: str, *, field: str) -> None:
    if not _ID_PATTERN.fullmatch(value):
        _fail("INVALID_IDENTIFIER", f"{field} has an invalid identifier: {value!r}")


def _validate_manifest(manifest: object) -> dict[str, object]:
    if not isinstance(manifest, dict):
        _fail("MANIFEST_TYPE", "SOURCE_MANIFEST.json must contain a JSON object")
    missing = sorted(_MANIFEST_REQUIRED_KEYS - manifest.keys())
    if missing:
        _fail("MANIFEST_KEYS", f"manifest is missing keys: {', '.join(missing)}")

    if manifest["contract_version"] != CONTRACT_VERSION:
        _fail("CONTRACT_VERSION", "manifest contract_version is unsupported")

    for key in ("adapter_id", "adapter_version", "source_family_id", "snapshot_id"):
        value = _require_string(manifest, key)
        if key != "adapter_version":
            _validate_id(value, field=key)

    generated_at = _require_string(manifest, "generated_at")
    if not _TIMESTAMP.fullmatch(generated_at):
        _fail("MANIFEST_TIMESTAMP", "generated_at must be an ISO-8601 timestamp with zone")

    source_kind = _require_string(manifest, "source_kind")
    if source_kind not in SOURCE_PROFILES:
        _fail("SOURCE_KIND", f"unsupported source kind: {source_kind}")

    structural = _require_bool(manifest, "structural_test_fixture")
    observed = _require_bool(manifest, "contains_observed_coffee_data")
    core_eligible = _require_bool(manifest, "core_count_eligible")
    semantic_inference = _require_bool(manifest, "semantic_inference_permitted")
    llm_fields = _require_bool(manifest, "llm_generated_fields_permitted")

    if semantic_inference:
        _fail("SEMANTIC_INFERENCE", "semantic inference must remain disabled")
    if llm_fields:
        _fail("LLM_FIELDS", "LLM-generated source fields must remain disabled")
    if manifest["record_count_basis"] != "ENTRY_PREPARATION_SERVICE":
        _fail("COUNT_BASIS", "record_count_basis must be ENTRY_PREPARATION_SERVICE")
    if manifest["rights_dimensions"] != list(RIGHTS_DIMENSIONS):
        _fail("RIGHTS_DIMENSIONS", "rights dimensions must remain separate and complete")
    if manifest["output_files"] != list(REQUIRED_TABLE_FILES):
        _fail("OUTPUT_INVENTORY", "manifest output_files must exactly match the contract")

    status = _require_string(manifest, "adapter_status")
    allowed_statuses = {
        "READY_FOR_REVIEW",
        "VALIDATED",
        "BLOCKED_QUALITY",
        "STRUCTURAL_TEST_ONLY",
    }
    if status not in allowed_statuses:
        _fail("ADAPTER_STATUS", f"unsupported adapter status: {status}")

    authorization = _require_string(manifest, "acquisition_authorization")
    if structural:
        if authorization != "FIXTURE_ONLY":
            _fail("FIXTURE_AUTHORIZATION", "structural fixtures must use FIXTURE_ONLY")
        if status != "STRUCTURAL_TEST_ONLY":
            _fail("FIXTURE_STATUS", "structural fixtures must be STRUCTURAL_TEST_ONLY")
        if observed:
            _fail("FIXTURE_OBSERVED_DATA", "structural fixtures cannot claim observed data")
        if core_eligible:
            _fail("STRUCTURAL_CORE_ELIGIBILITY", "structural fixtures cannot count as core")
    else:
        accepted = SOURCE_PROFILES[source_kind].accepted_authorizations
        if authorization not in accepted:
            _fail(
                "SOURCE_AUTHORIZATION",
                f"{source_kind} requires one of {sorted(accepted)}, got {authorization}",
            )
        if status == "STRUCTURAL_TEST_ONLY":
            _fail("FIXTURE_STATUS", "non-fixtures cannot be STRUCTURAL_TEST_ONLY")

    source_files = manifest["source_files"]
    if not isinstance(source_files, list) or not source_files:
        _fail("SOURCE_FILES", "manifest source_files must be a non-empty list")
    source_paths: set[str] = set()
    for index, item in enumerate(source_files):
        if not isinstance(item, dict):
            _fail("SOURCE_FILES", f"source_files[{index}] must be an object")
        required = {"path", "sha256", "media_type", "source_locator", "captured_at"}
        missing_source_keys = sorted(required - item.keys())
        if missing_source_keys:
            _fail(
                "SOURCE_FILES",
                f"source_files[{index}] is missing {', '.join(missing_source_keys)}",
            )
        path = _safe_relative_path(item["path"], field=f"source_files[{index}].path")
        if path in REQUIRED_FILES:
            _fail("SOURCE_FILES", f"source file collides with contract file: {path}")
        if path in source_paths:
            _fail("SOURCE_FILES", f"duplicate source file path: {path}")
        source_paths.add(path)
        sha = item["sha256"]
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            _fail("SOURCE_FILES", f"source_files[{index}].sha256 is invalid")
        for text_key in ("media_type", "source_locator"):
            value = item[text_key]
            if not isinstance(value, str) or not value.strip():
                _fail("SOURCE_FILES", f"source_files[{index}].{text_key} is empty")
        captured_at = item["captured_at"]
        if not isinstance(captured_at, str) or not _TIMESTAMP.fullmatch(captured_at):
            _fail("SOURCE_FILES", f"source_files[{index}].captured_at is invalid")

    record_counts = manifest["record_counts"]
    if not isinstance(record_counts, dict) or set(record_counts) != set(
        REQUIRED_TABLE_FILES
    ):
        _fail("RECORD_COUNTS", "record_counts must cover every contract table exactly")
    if any(type(value) is not int or value < 0 for value in record_counts.values()):
        _fail("RECORD_COUNTS", "record_counts values must be non-negative integers")

    _validate_quality(manifest, structural=structural)
    return manifest


def _metric_decimal(value: object, key: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        _fail("QUALITY_METRIC", f"{key} must be numeric")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        _fail("QUALITY_METRIC", f"{key} must be numeric")
    if not result.is_finite() or result < 0 or result > 1:
        _fail("QUALITY_METRIC", f"{key} must be within 0..1")
    return result


def _validate_quality(manifest: Mapping[str, object], *, structural: bool) -> None:
    policy = manifest["quality_gate_policy"]
    if not isinstance(policy, dict):
        _fail("QUALITY_POLICY", "quality_gate_policy must be an object")
    expected_policy = {
        "manual_audit_rule": "max(100,ceil(0.01*parsed_record_count))",
        **{
            key: f"{operator}{threshold}"
            for key, (operator, threshold) in QUALITY_THRESHOLDS.items()
        },
    }
    if policy != expected_policy:
        _fail("QUALITY_POLICY", "quality gate thresholds or audit rule changed")

    results = manifest["quality_gate_results"]
    if not isinstance(results, dict):
        _fail("QUALITY_RESULTS", "quality_gate_results must be an object")
    required_keys = {
        "parsed_record_count",
        "audited_record_count",
        "quality_gate_status",
        *QUALITY_THRESHOLDS,
    }
    if set(results) != required_keys:
        _fail("QUALITY_RESULTS", "quality_gate_results keys are incomplete or conflated")
    parsed = results["parsed_record_count"]
    audited = results["audited_record_count"]
    if type(parsed) is not int or parsed < 0 or type(audited) is not int or audited < 0:
        _fail("QUALITY_RESULTS", "quality record counts must be non-negative integers")

    if structural:
        if results["quality_gate_status"] != "NOT_APPLICABLE_STRUCTURAL_FIXTURE":
            _fail("QUALITY_STATUS", "fixture quality status must be not applicable")
        if parsed != 0 or audited != 0:
            _fail("QUALITY_RESULTS", "fixture quality counts must be zero")
        if any(results[key] is not None for key in QUALITY_THRESHOLDS):
            _fail("QUALITY_RESULTS", "fixture quality metrics must be null")
        return

    adapter_status = manifest["adapter_status"]
    if adapter_status == "READY_FOR_REVIEW":
        if results["quality_gate_status"] != "PENDING":
            _fail("QUALITY_STATUS", "review-ready adapters must have PENDING quality")
        if any(results[key] is not None for key in QUALITY_THRESHOLDS):
            _fail("QUALITY_RESULTS", "pending quality metrics must be null")
        if manifest["core_count_eligible"] is not False:
            _fail("QUALITY_CORE_ELIGIBILITY", "pending adapters cannot count as core")
        return

    metric_values = {
        key: _metric_decimal(results[key], key) for key in QUALITY_THRESHOLDS
    }
    required_sample = min(parsed, max(100, math.ceil(Decimal(parsed) * Decimal("0.01"))))
    sample_pass = audited >= required_sample
    failed_metrics = []
    for key, (operator, threshold) in QUALITY_THRESHOLDS.items():
        value = metric_values[key]
        if (operator == ">=" and value < threshold) or (
            operator == "<=" and value > threshold
        ):
            failed_metrics.append(key)
    passes = sample_pass and not failed_metrics
    expected_quality_status = "PASS" if passes else "BLOCKED_QUALITY"
    if not sample_pass and adapter_status == "VALIDATED":
        _fail("QUALITY_AUDIT_SAMPLE", "manual audit sample is below the required size")
    if results["quality_gate_status"] != expected_quality_status:
        _fail("QUALITY_STATUS", "quality gate result does not match its measurements")
    if passes and adapter_status != "VALIDATED":
        _fail("QUALITY_STATUS", "passing quality gates require VALIDATED status")
    if not passes and adapter_status != "BLOCKED_QUALITY":
        reason = "audit sample" if not sample_pass else ", ".join(failed_metrics)
        _fail("QUALITY_STATUS", f"failed {reason} requires BLOCKED_QUALITY status")
    if adapter_status == "BLOCKED_QUALITY" and manifest["core_count_eligible"] is not False:
        _fail("QUALITY_CORE_ELIGIBILITY", "blocked adapters cannot count as core")


def _load_manifest(bundle_path: Path) -> dict[str, object]:
    path = bundle_path / "SOURCE_MANIFEST.json"
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        _fail("MANIFEST_ENCODING", "SOURCE_MANIFEST.json must be UTF-8")
    try:
        return _validate_manifest(json.loads(content))
    except json.JSONDecodeError as error:
        _fail("MANIFEST_JSON", f"invalid SOURCE_MANIFEST.json: {error.msg}")


def _parse_hash_inventory(path: Path) -> dict[str, str]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        _fail("HASH_FORMAT", "SHA256SUMS must be UTF-8")
    if "\r" in content or (content and not content.endswith("\n")):
        _fail("HASH_FORMAT", "SHA256SUMS must use LF and end with a newline")
    inventory: dict[str, str] = {}
    previous = ""
    for line_number, line in enumerate(content.splitlines(), start=1):
        match = _SHA_LINE.fullmatch(line)
        if match is None:
            _fail("HASH_FORMAT", f"invalid SHA256SUMS line {line_number}")
        digest, raw_path = match.groups()
        relative_path = _safe_relative_path(raw_path, field="SHA256SUMS path")
        if relative_path in inventory:
            _fail("HASH_DUPLICATE", f"duplicate SHA256SUMS path: {relative_path}")
        if previous and relative_path <= previous:
            _fail("HASH_ORDER", "SHA256SUMS paths must be strictly sorted")
        inventory[relative_path] = digest
        previous = relative_path
    return inventory


def _validate_files(bundle_path: Path, manifest: Mapping[str, object]) -> int:
    source_files = manifest["source_files"]
    assert isinstance(source_files, list)
    source_paths = {str(item["path"]) for item in source_files}
    expected_hashed = {"SOURCE_MANIFEST.json", *REQUIRED_TABLE_FILES, *source_paths}
    inventory = _parse_hash_inventory(bundle_path / "SHA256SUMS")
    if set(inventory) != expected_hashed:
        missing = sorted(expected_hashed - inventory.keys())
        extra = sorted(inventory.keys() - expected_hashed)
        _fail("HASH_INVENTORY", f"hash inventory mismatch; missing={missing}, extra={extra}")

    expected_physical = expected_hashed | {"SHA256SUMS"}
    physical: set[str] = set()
    for path in bundle_path.rglob("*"):
        if path.is_symlink():
            _fail("SYMLINK_FILE", f"bundle files cannot be symlinks: {path}")
        if path.is_file():
            physical.add(path.relative_to(bundle_path).as_posix())
    if physical != expected_physical:
        missing = sorted(expected_physical - physical)
        extra = sorted(physical - expected_physical)
        _fail("UNDECLARED_FILE", f"physical inventory mismatch; missing={missing}, extra={extra}")

    for relative_path, expected_sha in inventory.items():
        actual_sha = _sha256(bundle_path / relative_path)
        if actual_sha != expected_sha:
            _fail("HASH_MISMATCH", f"SHA-256 mismatch for {relative_path}")

    declarations = {str(item["path"]): str(item["sha256"]) for item in source_files}
    for relative_path, declared_sha in declarations.items():
        if inventory[relative_path] != declared_sha:
            _fail("SOURCE_HASH_DECLARATION", f"source hash differs for {relative_path}")
    return len(inventory)


def read_table(path: Path, expected_columns: Sequence[str]) -> list[dict[str, str]]:
    """Read one canonical UTF-8/LF TSV and require its exact schema."""

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        _fail("TSV_ENCODING", f"{path.name} must be UTF-8")
    if "\r" in content or not content.endswith("\n"):
        _fail("TSV_FORMAT", f"{path.name} must use LF and end with a newline")
    try:
        reader = csv.DictReader(io.StringIO(content), delimiter="\t", strict=True)
        if reader.fieldnames != list(expected_columns):
            _fail(
                "TSV_SCHEMA",
                f"{path.name} columns differ: expected {list(expected_columns)}, "
                f"got {reader.fieldnames}",
            )
        rows = list(reader)
    except csv.Error as error:
        _fail("TSV_FORMAT", f"{path.name} is invalid TSV: {error}")
    for index, row in enumerate(rows, start=2):
        if None in row or any(value is None for value in row.values()):
            _fail("TSV_SCHEMA", f"{path.name}:{index} has a malformed field count")
    return rows


def _require_row_bool(row: Mapping[str, str], key: str, *, context: str) -> bool:
    value = row[key]
    if value not in _BOOL_VALUES:
        _fail("BOOLEAN_FIELD", f"{context}.{key} must be true or false")
    return value == "true"


def _require_row_id(row: Mapping[str, str], key: str, *, context: str) -> str:
    value = row[key]
    if not value:
        _fail("INVALID_IDENTIFIER", f"{context}.{key} is empty")
    _validate_id(value, field=f"{context}.{key}")
    return value


def _index_unique(
    rows: Iterable[dict[str, str]], key: str, *, table: str
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, start=2):
        value = _require_row_id(row, key, context=f"{table}:{row_number}")
        if value in result:
            _fail("DUPLICATE_IDENTIFIER", f"{table} repeats {key}={value}")
        result[value] = row
    return result


def _validate_raw_flags(
    rows_by_file: Mapping[str, list[dict[str, str]]],
    *,
    structural: bool,
    manifest_core: bool,
) -> None:
    for filename in REQUIRED_TABLE_FILES[:7]:
        for row_number, row in enumerate(rows_by_file[filename], start=2):
            row_structural = _require_row_bool(
                row, "structural_test_fixture", context=f"{filename}:{row_number}"
            )
            row_core = _require_row_bool(
                row, "core_count_eligible", context=f"{filename}:{row_number}"
            )
            if row_structural != structural:
                _fail("FIXTURE_FLAG", f"{filename}:{row_number} fixture flag differs")
            if structural and row_core:
                _fail(
                    "STRUCTURAL_CORE_ELIGIBILITY",
                    f"{filename}:{row_number} structural row cannot count as core",
                )
            if row_core and not manifest_core:
                _fail("CORE_ELIGIBILITY", f"{filename}:{row_number} exceeds manifest eligibility")


def _validate_scores(scores: Sequence[dict[str, str]]) -> None:
    allowed_roles = {
        "OFFICIAL_TOTAL",
        "OFFICIAL_COMPONENT",
        "JUDGE_COMPONENT",
        "OTHER_EXPLICIT",
    }
    for row_number, row in enumerate(scores, start=2):
        context = f"RAW_SCORE.tsv:{row_number}"
        if row["score_role"] not in allowed_roles:
            _fail("SCORE_ROLE", f"{context} has an unsupported score role")
        if row["score_role"] == "JUDGE_COMPONENT" and not row["judge_observation_id"]:
            _fail("JUDGE_LINEAGE", f"{context} judge component lacks judge observation id")
        try:
            value = Decimal(row["score_value"])
            minimum = Decimal(row["score_scale_min"])
            maximum = Decimal(row["score_scale_max"])
        except InvalidOperation:
            _fail("SCORE_VALUE", f"{context} contains a non-numeric score")
        if not all(item.is_finite() for item in (value, minimum, maximum)):
            _fail("SCORE_VALUE", f"{context} score values must be finite")
        if minimum > maximum or value < minimum or value > maximum:
            _fail("SCORE_VALUE", f"{context} score is outside its explicit scale")
        if not row["source_locator"] or not row["source_text"]:
            _fail("SCORE_LINEAGE", f"{context} lacks explicit source lineage")


def _validate_preparations(preparations: Sequence[dict[str, str]]) -> None:
    preparation_evidence = {
        "EXPLICIT_SOURCE_FIELD",
        "DOCUMENTED_FRESH_PROTOCOL",
        "UNRESOLVED",
    }
    fresh_evidence = {
        "EXPLICIT_SOURCE_FIELD",
        "DOCUMENTED_FRESH_PROTOCOL",
        "UNRESOLVED",
    }
    roast_evidence = {"EXPLICIT_SOURCE_FIELD", "UNRESOLVED", "NOT_PROVIDED"}
    for row_number, row in enumerate(preparations, start=2):
        context = f"RAW_PREPARATION_SERVICE.tsv:{row_number}"
        try:
            sequence = int(row["service_sequence"])
        except ValueError:
            _fail("SERVICE_SEQUENCE", f"{context} service_sequence must be an integer")
        if sequence < 1:
            _fail("SERVICE_SEQUENCE", f"{context} service_sequence must be positive")
        fresh = _require_row_bool(row, "fresh_preparation_confirmed", context=context)
        prep_evidence = row["preparation_evidence"]
        if prep_evidence not in preparation_evidence:
            _fail("PREPARATION_INFERENCE", f"{context} uses prohibited preparation inference")
        if row["preparation_family_code"] and (
            not row["preparation_family_source_text"] or prep_evidence == "UNRESOLVED"
        ):
            _fail("PREPARATION_LINEAGE", f"{context} preparation code lacks explicit evidence")
        if row["fresh_preparation_evidence"] not in fresh_evidence:
            _fail("FRESH_PREPARATION", f"{context} has unsupported fresh-preparation evidence")
        if fresh and row["fresh_preparation_evidence"] == "UNRESOLVED":
            _fail("FRESH_PREPARATION", f"{context} confirms freshness without evidence")

        evidence = row["roast_evidence"]
        if evidence not in roast_evidence:
            _fail("ROAST_INFERENCE", f"{context} uses a prohibited roast shortcut")
        if row["roast_code"] and (
            not row["roast_source_text"] or evidence != "EXPLICIT_SOURCE_FIELD"
        ):
            _fail("ROAST_INFERENCE", f"{context} roast code is not explicitly sourced")
        if not row["roast_code"] and evidence == "EXPLICIT_SOURCE_FIELD":
            _fail("ROAST_LINEAGE", f"{context} declares roast evidence without a roast code")
        if not row["source_locator"] or not row["source_text"]:
            _fail("PREPARATION_LINEAGE", f"{context} lacks source lineage")


def _validate_descriptors(descriptors: Sequence[dict[str, str]]) -> None:
    allowed_actor_roles = {"OFFICIAL", "JUDGE", "COMPETITOR"}
    allowed_types = {
        "OFFICIAL_TASTING_NOTE",
        "OFFICIAL_DESCRIPTOR_FIELD",
        "JUDGE_NOTE",
        "COMPETITOR_NOTE",
    }
    allowed_methods = {
        "EXPLICIT_FIELD",
        "VERBATIM_SPAN",
        "AUTHORIZED_EXPORT_FIELD",
        "PERMITTED_TRANSCRIPT_SPAN",
        "MANUAL_VERBATIM_TRANSCRIPTION",
    }
    allowed_dispositions = {
        "POSITIVE",
        "MULTI_TARGET",
        "AMBIGUOUS",
        "CONFLICTING",
        "SOURCE_LOCAL",
        "UNRESOLVED",
        "ABSTENTION",
        "OUTSIDE_ONTOLOGY",
        "CANDIDATE_NOT_TRAINING_LABEL",
    }
    type_roles = {
        "OFFICIAL_TASTING_NOTE": "OFFICIAL",
        "OFFICIAL_DESCRIPTOR_FIELD": "OFFICIAL",
        "JUDGE_NOTE": "JUDGE",
        "COMPETITOR_NOTE": "COMPETITOR",
    }
    for row_number, row in enumerate(descriptors, start=2):
        context = f"RAW_DESCRIPTOR_ASSERTION.tsv:{row_number}"
        role = row["assertion_actor_role"]
        assertion_type = row["assertion_type"]
        if role not in allowed_actor_roles:
            _fail("ASSERTION_ACTOR", f"{context} does not distinguish assertion actor")
        if assertion_type not in allowed_types or type_roles[assertion_type] != role:
            _fail("ASSERTION_ACTOR", f"{context} assertion type and actor disagree")
        if role == "JUDGE" and not row["judge_observation_id"]:
            _fail("JUDGE_LINEAGE", f"{context} judge note lacks judge observation id")
        if role != "JUDGE" and row["judge_observation_id"]:
            _fail("JUDGE_LINEAGE", f"{context} non-judge note has judge observation id")
        if row["extraction_method"] not in allowed_methods:
            _fail("DESCRIPTOR_INVENTION", f"{context} is synthetic, inferred, or LLM-made")
        descriptor = row["descriptor_text"].strip()
        span = row["source_span"].strip()
        if not descriptor or not span or descriptor.casefold() not in span.casefold():
            _fail("DESCRIPTOR_LINEAGE", f"{context} descriptor lacks a verbatim source span")
        try:
            start = int(row["source_span_start"])
            end = int(row["source_span_end"])
        except ValueError:
            _fail("DESCRIPTOR_LINEAGE", f"{context} source offsets must be integers")
        if start < 0 or end <= start:
            _fail("DESCRIPTOR_LINEAGE", f"{context} source offsets are invalid")
        if row["label_disposition"] not in allowed_dispositions:
            _fail("LABEL_DISPOSITION", f"{context} has an unsupported label disposition")
        if not row["source_locator"]:
            _fail("DESCRIPTOR_LINEAGE", f"{context} lacks a source locator")


def _validate_normalizations(rows: Sequence[dict[str, str]]) -> None:
    allowed_rules = {
        "UNICODE_NFC",
        "CASE_NORMALIZATION",
        "WHITESPACE_NORMALIZATION",
        "CONTROLLED_PUNCTUATION_NORMALIZATION",
        "SOURCE_DECLARED_IDENTIFIER_NORMALIZATION",
    }
    for row_number, row in enumerate(rows, start=2):
        context = f"NORMALIZATION_REPORT.tsv:{row_number}"
        _require_row_id(row, "normalization_id", context=context)
        if row["target_file"] not in REQUIRED_TABLE_FILES[:7]:
            _fail("NORMALIZATION_TARGET", f"{context} has an invalid target file")
        if row["normalization_rule"] not in allowed_rules:
            _fail("NORMALIZATION_RULE", f"{context} uses semantic inference")
        if _require_row_bool(row, "semantic_change", context=context):
            _fail("SEMANTIC_NORMALIZATION", f"{context} changes source semantics")
        if row["review_status"] not in {"AUTO_ALLOWED", "REVIEWED_ALLOWED"}:
            _fail("NORMALIZATION_REVIEW", f"{context} has an invalid review status")


def _validate_rights(
    rows: Sequence[dict[str, str]], source_family_id: str
) -> dict[str, str]:
    if len(rows) != 1:
        _fail("RIGHTS_CARDINALITY", "RIGHTS_REPORT.tsv must have one current source decision")
    row = rows[0]
    _require_row_id(row, "rights_id", context="RIGHTS_REPORT.tsv:2")
    if row["source_family_id"] != source_family_id:
        _fail("RIGHTS_SOURCE", "rights decision source family differs from manifest")
    dimensions = (
        "public_results_use",
        "public_descriptor_use",
        "internal_research_use",
        "public_derived_release",
        "model_research_use",
        "commercial_model_use",
    )
    for dimension in dimensions:
        if row[dimension] not in _RIGHTS_VALUES:
            _fail("RIGHTS_VALUE", f"{dimension} must be true, false, or pending")
    if row["rights_decision_status"] not in {
        "REVIEWED_ALLOWED",
        "REVIEWED_RESTRICTED",
        "PENDING",
        "DENIED",
        "FIXTURE_ONLY_NO_RIGHTS",
    }:
        _fail("RIGHTS_STATUS", "unsupported rights decision status")
    if not row["evidence_locator"]:
        _fail("RIGHTS_EVIDENCE", "rights decision lacks evidence locator")
    if row["review_status"] not in {"REVIEWED", "PENDING", "NOT_APPLICABLE"}:
        _fail("RIGHTS_STATUS", "unsupported rights review status")
    return row


def _validate_duplicate_relationships(
    rows: Sequence[dict[str, str]], known_ids: set[str]
) -> None:
    allowed_record_types = {
        "ENTRY",
        "COFFEE_IDENTITY",
        "PREPARATION_SERVICE",
        "EFFECTIVE_RECORD",
    }
    allowed_relationships = {
        "EXACT_DUPLICATE",
        "MIRROR_DUPLICATE",
        "REPEAT_ROUND",
        "REPEAT_CATEGORY",
        "SAME_COFFEE_DIFFERENT_ENTRY",
        "NOT_A_DUPLICATE",
    }
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        context = f"DUPLICATE_REPEAT_REPORT.tsv:{row_number}"
        relationship_id = _require_row_id(row, "relationship_id", context=context)
        if relationship_id in seen_ids:
            _fail("DUPLICATE_IDENTIFIER", f"duplicate relationship id {relationship_id}")
        seen_ids.add(relationship_id)
        if row["left_record_type"] not in allowed_record_types or row[
            "right_record_type"
        ] not in allowed_record_types:
            _fail("DUPLICATE_RELATIONSHIP", f"{context} has an invalid record type")
        if row["left_record_id"] not in known_ids or row["right_record_id"] not in known_ids:
            _fail("DUPLICATE_RELATIONSHIP", f"{context} references an unknown record")
        if row["left_record_id"] == row["right_record_id"]:
            _fail("DUPLICATE_RELATIONSHIP", f"{context} is a self-link")
        if row["relationship_type"] not in allowed_relationships:
            _fail("DUPLICATE_RELATIONSHIP", f"{context} has an invalid relationship type")
        if not row["decision_basis"] or row["review_status"] not in {
            "REVIEWED",
            "PENDING",
        }:
            _fail("DUPLICATE_RELATIONSHIP", f"{context} lacks review lineage")


def _validate_table_contract(
    manifest: Mapping[str, object], rows_by_file: Mapping[str, list[dict[str, str]]]
) -> None:
    structural = bool(manifest["structural_test_fixture"])
    manifest_core = bool(manifest["core_count_eligible"])
    _validate_raw_flags(rows_by_file, structural=structural, manifest_core=manifest_core)

    series = _index_unique(rows_by_file["RAW_SERIES.tsv"], "series_id", table="RAW_SERIES.tsv")
    editions = _index_unique(
        rows_by_file["RAW_EDITION.tsv"], "edition_id", table="RAW_EDITION.tsv"
    )
    entries = _index_unique(rows_by_file["RAW_ENTRY.tsv"], "entry_id", table="RAW_ENTRY.tsv")
    coffees = _index_unique(
        rows_by_file["RAW_COFFEE_IDENTITY.tsv"],
        "coffee_identity_id",
        table="RAW_COFFEE_IDENTITY.tsv",
    )
    preparations = _index_unique(
        rows_by_file["RAW_PREPARATION_SERVICE.tsv"],
        "preparation_service_id",
        table="RAW_PREPARATION_SERVICE.tsv",
    )
    scores = _index_unique(rows_by_file["RAW_SCORE.tsv"], "score_id", table="RAW_SCORE.tsv")
    descriptors = _index_unique(
        rows_by_file["RAW_DESCRIPTOR_ASSERTION.tsv"],
        "descriptor_assertion_id",
        table="RAW_DESCRIPTOR_ASSERTION.tsv",
    )
    effective = _index_unique(
        rows_by_file["EFFECTIVE_RECORD_REPORT.tsv"],
        "effective_record_id",
        table="EFFECTIVE_RECORD_REPORT.tsv",
    )

    source_family_id = str(manifest["source_family_id"])
    for row in series.values():
        if row["source_family_id"] != source_family_id:
            _fail("SOURCE_FAMILY_LINK", "series source family differs from manifest")
    for row in editions.values():
        if row["series_id"] not in series:
            _fail("ORPHAN_REFERENCE", f"edition {row['edition_id']} has no series")
    for row in entries.values():
        if row["edition_id"] not in editions:
            _fail("ORPHAN_REFERENCE", f"entry {row['entry_id']} has no edition")
    for row in coffees.values():
        if row["entry_id"] not in entries:
            _fail("ORPHAN_REFERENCE", f"coffee {row['coffee_identity_id']} has no entry")
    for row in preparations.values():
        if row["entry_id"] not in entries or row["coffee_identity_id"] not in coffees:
            _fail("ORPHAN_REFERENCE", f"service {row['preparation_service_id']} is orphaned")
        if coffees[row["coffee_identity_id"]]["entry_id"] != row["entry_id"]:
            _fail("IDENTITY_LINKAGE", "preparation entry and coffee entry disagree")
    for row in scores.values():
        if row["preparation_service_id"] not in preparations:
            _fail("ORPHAN_REFERENCE", f"score {row['score_id']} has no service")
    for row in descriptors.values():
        if row["preparation_service_id"] not in preparations:
            _fail("ORPHAN_REFERENCE", f"descriptor {row['descriptor_assertion_id']} has no service")

    _validate_preparations(list(preparations.values()))
    _validate_scores(list(scores.values()))
    _validate_descriptors(list(descriptors.values()))
    _validate_normalizations(rows_by_file["NORMALIZATION_REPORT.tsv"])
    rights = _validate_rights(rows_by_file["RIGHTS_REPORT.tsv"], source_family_id)

    known_ids = set(entries) | set(coffees) | set(preparations) | set(effective)
    _validate_duplicate_relationships(
        rows_by_file["DUPLICATE_REPEAT_REPORT.tsv"], known_ids
    )

    seen_effective_services: set[tuple[str, str]] = set()
    for row_number, row in enumerate(effective.values(), start=2):
        context = f"EFFECTIVE_RECORD_REPORT.tsv:{row_number}"
        if row["effective_record_type"] != "EFFECTIVE_ROUND_SERVICE_RECORD":
            _fail("EFFECTIVE_RECORD_TYPE", f"{context} has an invalid record type")
        entry_id = row["entry_id"]
        coffee_id = row["coffee_identity_id"]
        service_id = row["preparation_service_id"]
        if entry_id not in entries or coffee_id not in coffees or service_id not in preparations:
            _fail("ORPHAN_REFERENCE", f"{context} is orphaned")
        service = preparations[service_id]
        if service["entry_id"] != entry_id or service["coffee_identity_id"] != coffee_id:
            _fail("IDENTITY_LINKAGE", f"{context} disagrees with its service identity")
        service_key = (entry_id, service_id)
        if service_key in seen_effective_services:
            _fail(
                "JUDGE_MULTIPLICATION",
                f"{context} repeats entry x preparation_service as an effective record",
            )
        seen_effective_services.add(service_key)

        observed = _require_row_bool(row, "observed_core_eligible", context=context)
        model = _require_row_bool(row, "model_eligible", context=context)
        auxiliary = _require_row_bool(row, "auxiliary_eligible", context=context)
        row_structural = _require_row_bool(
            row, "structural_test_fixture", context=context
        )
        if row_structural != structural:
            _fail("FIXTURE_FLAG", f"{context} fixture flag differs from manifest")
        if model and not observed:
            _fail("MODEL_ELIGIBILITY", f"{context} model record is not observed core")
        if auxiliary and (observed or model):
            _fail("AUXILIARY_ELIGIBILITY", f"{context} auxiliary/core flags overlap")
        if structural and (observed or model or auxiliary):
            _fail("STRUCTURAL_CORE_ELIGIBILITY", f"{context} fixture is count-eligible")
        if (observed or auxiliary) and not manifest_core:
            _fail("CORE_ELIGIBILITY", f"{context} exceeds manifest eligibility")
        if observed:
            if manifest["adapter_status"] != "VALIDATED" or not manifest[
                "contains_observed_coffee_data"
            ]:
                _fail("OBSERVED_ELIGIBILITY", f"{context} adapter is not validated observed data")
            if rights["internal_research_use"] != "true":
                _fail("RESEARCH_RIGHTS", f"{context} lacks internal research rights")
            if service["fresh_preparation_confirmed"] != "true" or service[
                "fresh_preparation_evidence"
            ] not in {"EXPLICIT_SOURCE_FIELD", "DOCUMENTED_FRESH_PROTOCOL"}:
                _fail("FRESH_PREPARATION", f"{context} lacks fresh-preparation provenance")
            lineage = (entries[entry_id], coffees[coffee_id], service)
            if any(item["core_count_eligible"] != "true" for item in lineage):
                _fail("CORE_LINEAGE", f"{context} has a non-core identity/service parent")
        if model and rights["model_research_use"] != "true":
            _fail("MODEL_RIGHTS", f"{context} lacks MODEL_RESEARCH_USE=true")
        if not (observed or model or auxiliary) and not row["exclusion_reason"]:
            _fail("EXCLUSION_REASON", f"{context} ineligible record lacks an exclusion reason")

        judge_ids = {
            item["judge_observation_id"]
            for item in (*scores.values(), *descriptors.values())
            if item["preparation_service_id"] == service_id
            and item["judge_observation_id"]
        }
        descriptor_count = sum(
            item["preparation_service_id"] == service_id for item in descriptors.values()
        )
        try:
            declared_judges = int(row["judge_observation_count"])
            declared_descriptors = int(row["descriptor_assertion_count"])
        except ValueError:
            _fail("EFFECTIVE_COUNTS", f"{context} counts must be integers")
        if declared_judges != len(judge_ids):
            _fail("JUDGE_COUNT", f"{context} judge count multiplies or drops observations")
        if declared_descriptors != descriptor_count:
            _fail("DESCRIPTOR_COUNT", f"{context} descriptor count differs from assertions")

    if len(rows_by_file["RAW_ENTRY.tsv"]) != manifest["quality_gate_results"][
        "parsed_record_count"
    ] and not structural:
        _fail("QUALITY_PARSED_COUNT", "quality parsed count must equal raw entry count")


def validate_bundle(bundle_path: Path | str) -> ValidationSummary:
    """Validate a complete adapter output directory without network access."""

    path = Path(bundle_path)
    if not path.is_dir():
        _fail("BUNDLE_DIRECTORY", f"adapter bundle directory is missing: {path}")
    for filename in REQUIRED_FILES:
        if not (path / filename).is_file():
            _fail("MISSING_FILE", f"required adapter artifact is missing: {filename}")

    manifest = _load_manifest(path)
    verified_count = _validate_files(path, manifest)
    rows_by_file = {
        filename: read_table(path / filename, TABLE_SCHEMAS[filename])
        for filename in REQUIRED_TABLE_FILES
    }
    for filename, rows in rows_by_file.items():
        if manifest["record_counts"][filename] != len(rows):
            _fail("RECORD_COUNT_MISMATCH", f"manifest count differs for {filename}")
    _validate_table_contract(manifest, rows_by_file)
    return ValidationSummary(
        bundle_path=path,
        source_kind=str(manifest["source_kind"]),
        adapter_status=str(manifest["adapter_status"]),
        structural_test_fixture=bool(manifest["structural_test_fixture"]),
        table_counts={key: len(value) for key, value in rows_by_file.items()},
        verified_file_count=verified_count,
    )


def _encode_tsv(filename: str, rows: Iterable[Mapping[str, object]]) -> bytes:
    fieldnames = TABLE_SCHEMAS[filename]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for index, row in enumerate(rows, start=2):
        if set(row) != set(fieldnames):
            _fail("EMIT_SCHEMA", f"{filename}:{index} does not exactly match its schema")
        writer.writerow({key: row[key] for key in fieldnames})
    return output.getvalue().encode("utf-8")


def emit_bundle(
    output_path: Path | str,
    manifest: Mapping[str, object],
    tables: Mapping[str, Iterable[Mapping[str, object]]],
    source_files: Mapping[str, bytes],
) -> ValidationSummary:
    """Emit one deterministic bundle from explicit records and captured bytes.

    The destination must not exist or must be empty. This function intentionally
    performs no extraction or semantic filling; format-specific code supplies
    explicit rows and verbatim spans.
    """

    path = Path(output_path)
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        _fail("OUTPUT_NOT_EMPTY", f"refusing to overwrite non-empty output: {path}")
    if set(tables) != set(REQUIRED_TABLE_FILES):
        _fail("EMIT_INVENTORY", "tables must contain every contract table exactly")
    manifest_copy = json.loads(json.dumps(manifest))
    if not isinstance(manifest_copy, dict):
        _fail("MANIFEST_TYPE", "manifest must be a mapping")
    manifest_source_files = manifest_copy.get("source_files")
    if not isinstance(manifest_source_files, list):
        _fail("SOURCE_FILES", "manifest source_files must be a list")
    declared_source_paths = {str(item.get("path")) for item in manifest_source_files}
    if set(source_files) != declared_source_paths:
        _fail("EMIT_INVENTORY", "source file bytes differ from manifest inventory")

    table_rows = {key: list(value) for key, value in tables.items()}
    encoded_tables = {key: _encode_tsv(key, table_rows[key]) for key in tables}
    expected_counts = {key: len(table_rows[key]) for key in REQUIRED_TABLE_FILES}
    if manifest_copy.get("record_counts") != expected_counts:
        _fail("RECORD_COUNTS", "manifest counts do not match rows supplied to emitter")
    for item in manifest_source_files:
        source_path = str(item["path"])
        if item.get("sha256") != _sha256_bytes(source_files[source_path]):
            _fail("SOURCE_HASH_DECLARATION", f"source bytes differ for {source_path}")

    path.mkdir(parents=True, exist_ok=True)
    for relative_path, content in source_files.items():
        safe_path = _safe_relative_path(relative_path, field="source file output path")
        destination = path / safe_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    for filename, content in encoded_tables.items():
        (path / filename).write_bytes(content)
    manifest_bytes = (
        json.dumps(manifest_copy, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    (path / "SOURCE_MANIFEST.json").write_bytes(manifest_bytes)

    hashed_files = {
        "SOURCE_MANIFEST.json",
        *REQUIRED_TABLE_FILES,
        *source_files.keys(),
    }
    hash_lines = [
        f"{_sha256(path / relative_path)}  {relative_path}\n"
        for relative_path in sorted(hashed_files)
    ]
    (path / "SHA256SUMS").write_text("".join(hash_lines), encoding="utf-8")
    return validate_bundle(path)


class ExplicitRecordAdapter:
    """One generic emitter configured for any supported source kind."""

    def __init__(self, source_kind: str):
        if source_kind not in SOURCE_PROFILES:
            _fail("SOURCE_KIND", f"unsupported source kind: {source_kind}")
        self.profile = SOURCE_PROFILES[source_kind]

    def emit(
        self,
        output_path: Path | str,
        manifest: Mapping[str, object],
        tables: Mapping[str, Iterable[Mapping[str, object]]],
        source_files: Mapping[str, bytes],
    ) -> ValidationSummary:
        if manifest.get("source_kind") != self.profile.source_kind:
            _fail("SOURCE_KIND", "adapter profile and manifest source_kind differ")
        return emit_bundle(output_path, manifest, tables, source_files)


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    summary = validate_bundle(args.bundle)
    print("ROUND3K_ADAPTER_CONTRACT_PASS=true")
    print(f"SOURCE_KIND={summary.source_kind}")
    print(f"ADAPTER_STATUS={summary.adapter_status}")
    print(f"STRUCTURAL_TEST_FIXTURE={str(summary.structural_test_fixture).lower()}")
    print(f"VERIFIED_FILE_COUNT={summary.verified_file_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
