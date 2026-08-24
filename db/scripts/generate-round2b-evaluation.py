#!/usr/bin/env python3
"""Compile frozen Round 2B retrieval reviews into public persistence artifacts.

This program is intentionally an offline compiler, not an evaluator that can
tune retrieval.  It consumes a frozen, unjudged audit selection/candidate pool
and three private grading ledgers, validates their closure and temporal
separation, then emits:

* phrase-free public audit inventories and review receipts;
* adjudicated graded qrels keyed only by audit case and an existing governed
  concept; qrels may retain non-active concepts to measure ontology gaps while
  retrieved model candidates remain active-only;
* a public metric contract; and
* one forward PostgreSQL seed for A/B/C/D runs, typed candidate traces/signals,
  independent reviews, adjudication, and database-calculated metrics.

No relevance grade is inferred.  Private source phrases and reviewer rationale
text are read only for validation and hashing and are never copied to an output.
The generated SQL uses SHA-256 identities to resolve observed expressions and
occurrences, so their potentially sensitive database keys are also withheld.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


COMPILER_VERSION = "round2b-evaluation-persistence-v1"
AUDIT_SELECTION_POLICY_VERSION = "round2b-audit-selection-v1"
REVIEW_LEDGER_VERSION = "round2b-graded-review-v1"
METRIC_POLICY_VERSION = "round2b-retrieval-metrics-v1"

BASELINES = ("A", "B", "C", "D")
BASELINE_MAXIMUM_TIER = {code: index for index, code in enumerate(BASELINES, 1)}
TIERS = BASELINE_MAXIMUM_TIER
GRADES = frozenset({"0", "1", "2", "3", "U"})
NUMERIC_GRADES = frozenset({"0", "1", "2", "3"})
STRATA = frozenset(
    {
        "exact",
        "variant",
        "orthographic_difficulty",
        "graph_reference",
        "qualifier_polysemy",
        "non_descriptive_language",
        "hard_negative",
        "unresolved",
    }
)
DIRECT_SIGNAL_SETS = {
    "A": (
        frozenset({"normalized_phrase_match"}),
        frozenset({"normalized_phrase_match", "raw_surface_exact"}),
    ),
    "B": (
        frozenset({"normalized_phrase_match", "approved_variant_match"}),
        frozenset(
            {
                "normalized_phrase_match",
                "approved_variant_match",
                "raw_surface_exact",
            }
        ),
    ),
    "C": (frozenset({"pg_trgm_similarity"}),),
    "D": (frozenset({"typed_graph_hop"}),),
}
METRIC_SPECS = (
    ("recall_at_k", 1),
    ("recall_at_k", 3),
    ("recall_at_k", 5),
    ("mrr", 0),
    ("ndcg_at_k", 5),
    ("coverage", 0),
    ("abstention_rate", 0),
    ("abstention_error", 0),
    ("median_candidate_set_size", 0),
    ("unsafe_nonabstention", 0),
)

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
SAFE_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
AUDIT_CASE_KEY_RE = re.compile(r"^audit_case\.round2b\.sha256_[0-9a-f]{64}$")
AUDIT_CANDIDATE_KEY_RE = re.compile(
    r"^audit_candidate\.round2b\.sha256_[0-9a-f]{64}$"
)

CASE_HEADERS = (
    "selection_policy_version",
    "audit_case_key",
    "corpus_snapshot_key",
    "normalization_derivation_run_key",
    "normalization_pipeline_key",
    "language_tag_code",
    "normalized_expression_key",
    "normalized_text",
    "representative_expression_key",
    "representative_expression_text",
    "representative_observation_expression_key",
    "occurrence_count",
    "document_count",
    "primary_stratum_code",
    "stratum_codes_json",
    "audit_split_code",
    "selection_ordinal",
    "split_ordinal",
    "selection_sha256",
    "tuning_eligible",
    "reviewer_addition_allowed",
    "adjudication_state",
)

CANDIDATE_HEADERS = (
    "candidate_pool_key",
    "audit_case_key",
    "audit_split_code",
    "normalized_expression_key",
    "concept_key",
    "concept_type_code",
    "candidate_source_code",
    "retrieved_by_baselines_json",
    "baseline_ranks_json",
    "best_retrieval_tier_code",
    "best_tier_order",
    "best_candidate_rank",
    "retrieval_status_codes_json",
    "matched_expression_keys_json",
    "signal_ledger_by_baseline_json",
    "reviewer_added_by",
    "reviewer_added_at",
    "reviewer_addition_rationale",
)

REVIEW_HEADERS = (
    "reviewer_key",
    "audit_case_key",
    "concept_key",
    "relevance_grade_code",
    "rationale",
    "reviewed_at",
    "independent_attestation",
)

ADJUDICATION_HEADERS = (
    "adjudicator_key",
    "audit_case_key",
    "concept_key",
    "relevance_grade_code",
    "rationale",
    "reviewed_at",
)

PUBLIC_CASE_HEADERS = (
    "audit_case_key",
    "corpus_snapshot_key",
    "normalization_pipeline_key",
    "normalized_expression_identity_sha256",
    "representative_expression_identity_sha256",
    "representative_observation_expression_identity_sha256",
    "occurrence_count",
    "document_count",
    "primary_stratum_code",
    "stratum_codes_json",
    "audit_split_code",
    "selection_ordinal",
    "split_ordinal",
    "selection_sha256",
    "tuning_eligible",
)

PUBLIC_CANDIDATE_HEADERS = (
    "candidate_pool_key",
    "audit_case_key",
    "audit_split_code",
    "concept_key",
    "concept_type_code",
    "retrieved_by_baselines_json",
    "baseline_ranks_json",
    "best_retrieval_tier_code",
    "best_tier_order",
    "best_candidate_rank",
    "retrieval_status_codes_json",
    "matched_expression_identity_sha256s_json",
    "signal_ledger_by_baseline_json",
    "signal_ledger_sha256",
)

PUBLIC_QREL_HEADERS = (
    "audit_case_key",
    "audit_split_code",
    "expects_unresolved",
    "concept_key",
    "relevance_grade_code",
    "adjudication_rationale_sha256",
    "adjudicated_at",
)

PUBLIC_REVIEW_RECEIPT_HEADERS = (
    "audit_case_key",
    "audit_split_code",
    "reviewer_one_decision_sha256",
    "reviewer_two_decision_sha256",
    "adjudication_decision_sha256",
    "independent_reviewers_agree",
    "reviewer_one_expects_unresolved",
    "reviewer_two_expects_unresolved",
    "adjudicated_expects_unresolved",
)

PUBLIC_METRIC_CONTRACT_HEADERS = (
    "retrieval_evaluation_key",
    "model_run_key",
    "retrieval_baseline_code",
    "audit_split_code",
    "retrieval_metric_value_key",
    "retrieval_metric_code",
    "cutoff_k",
    "calculation_source",
)

OUTPUT_NAMES = (
    "audit_cases_public.tsv",
    "audit_candidate_pool_public.tsv",
    "audit_qrels_public.tsv",
    "audit_review_receipts_public.tsv",
    "evaluation_metric_contract_public.tsv",
    "round2b_evaluation_manifest.json",
    "016_round2b_evaluation_seed.sql",
)


class GenerationError(RuntimeError):
    """Raised when private inputs cannot be compiled without guessing."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(*parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return sha256_bytes(payload)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def opaque_identity(value: str) -> str:
    return sha256_text(COMPILER_VERSION, "opaque-identity", value)


def sql_literal(value: str) -> str:
    if "\x00" in value:
        raise GenerationError("PostgreSQL text cannot contain NUL")
    return "'" + value.replace("'", "''") + "'"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def parse_bool(value: str, field: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise GenerationError(f"{field} must be canonical true or false")


def parse_positive_int(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise GenerationError(f"{field} must be an integer") from error
    if parsed <= 0 or str(parsed) != value:
        raise GenerationError(f"{field} must be a canonical positive integer")
    return parsed


def parse_json_field(value: str, field: str, expected_type: type) -> Any:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise GenerationError(f"{field} is not valid JSON") from error
    if not isinstance(parsed, expected_type):
        raise GenerationError(
            f"{field} must decode to {expected_type.__name__}"
        )
    if canonical_json(parsed) != value:
        raise GenerationError(f"{field} must use canonical JSON encoding")
    return parsed


def parse_timestamp(value: str, field: str) -> datetime:
    if not value or value != value.strip():
        raise GenerationError(f"{field} must be a nonempty trimmed timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise GenerationError(f"{field} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise GenerationError(f"{field} must include an explicit UTC offset")
    return parsed.astimezone(timezone.utc)


def timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )


def validate_key(value: str, field: str) -> str:
    if not value or value != value.strip() or not SAFE_KEY_RE.fullmatch(value):
        raise GenerationError(f"{field} is not a safe stable key")
    return value


def read_tsv_exact(path: Path, headers: Sequence[str]) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != list(headers):
                raise GenerationError(
                    f"{path.name} headers differ from the frozen contract"
                )
            rows = list(reader)
    except UnicodeDecodeError as error:
        raise GenerationError(f"{path.name} must be strict UTF-8") from error
    if not rows:
        raise GenerationError(f"{path.name} is empty")
    for row_number, row in enumerate(rows, 2):
        if None in row or any(value is None for value in row.values()):
            raise GenerationError(
                f"{path.name}:{row_number} has a malformed field count"
            )
    return rows


def validate_expected_hash(path: Path, expected: str, label: str) -> str:
    if not HEX64_RE.fullmatch(expected):
        raise GenerationError(f"expected {label} SHA-256 is not 64 hex")
    actual = sha256_file(path)
    if actual != expected:
        raise GenerationError(
            f"{label} SHA-256 mismatch: expected {expected}, got {actual}"
        )
    return actual


def assert_unique(rows: Sequence[Mapping[str, str]], field: str, label: str) -> None:
    seen: set[str] = set()
    for row in rows:
        value = row[field]
        if value in seen:
            raise GenerationError(f"duplicate {label}: {value}")
        seen.add(value)


def validate_cases(
    rows: list[dict[str, str]],
    *,
    snapshot_key: str,
    pipeline_key: str,
    derivation_run_key: str,
    expected_count: int,
    expected_development_count: int,
) -> dict[str, dict[str, Any]]:
    if len(rows) != expected_count:
        raise GenerationError(
            f"audit case count is {len(rows)}, expected {expected_count}; "
            "synthetic padding is prohibited"
        )
    assert_unique(rows, "audit_case_key", "audit case key")
    assert_unique(rows, "normalized_expression_key", "normalized expression")
    selection_ordinals: list[int] = []
    split_ordinals: dict[str, list[int]] = defaultdict(list)
    split_counts: Counter[str] = Counter()
    result: dict[str, dict[str, Any]] = {}

    for row_number, row in enumerate(rows, 2):
        prefix = f"audit_cases.tsv:{row_number}"
        case_key = row["audit_case_key"]
        if not AUDIT_CASE_KEY_RE.fullmatch(case_key):
            raise GenerationError(f"{prefix} has a non-hash audit_case_key")
        if row["selection_policy_version"] != AUDIT_SELECTION_POLICY_VERSION:
            raise GenerationError(f"{prefix} uses an unknown selection policy")
        if row["corpus_snapshot_key"] != snapshot_key:
            raise GenerationError(f"{prefix} snapshot key differs from CLI")
        if row["normalization_pipeline_key"] != pipeline_key:
            raise GenerationError(f"{prefix} pipeline key differs from CLI")
        if row["normalization_derivation_run_key"] != derivation_run_key:
            raise GenerationError(f"{prefix} derivation key differs from CLI")
        if row["language_tag_code"] != "en":
            raise GenerationError(f"{prefix} is not an English audit case")
        for field in (
            "normalized_expression_key",
            "representative_expression_key",
            "representative_observation_expression_key",
        ):
            validate_key(row[field], f"{prefix} {field}")
        if not row["normalized_text"] or not row["representative_expression_text"]:
            raise GenerationError(f"{prefix} has an empty private expression")
        occurrence_count = parse_positive_int(
            row["occurrence_count"], f"{prefix} occurrence_count"
        )
        document_count = parse_positive_int(
            row["document_count"], f"{prefix} document_count"
        )
        if document_count > occurrence_count:
            raise GenerationError(f"{prefix} document count exceeds occurrences")
        primary = row["primary_stratum_code"]
        strata = parse_json_field(
            row["stratum_codes_json"], f"{prefix} stratum_codes_json", list
        )
        if (
            not strata
            or len(strata) != len(set(strata))
            or any(not isinstance(value, str) or value not in STRATA for value in strata)
            or primary not in strata
        ):
            raise GenerationError(f"{prefix} has invalid strata")
        split = row["audit_split_code"]
        if split not in ("development", "held_out"):
            raise GenerationError(f"{prefix} has an invalid split")
        tuning_eligible = parse_bool(
            row["tuning_eligible"], f"{prefix} tuning_eligible"
        )
        if tuning_eligible != (split == "development"):
            raise GenerationError(f"{prefix} split/tuning policy is inconsistent")
        if not parse_bool(
            row["reviewer_addition_allowed"],
            f"{prefix} reviewer_addition_allowed",
        ):
            raise GenerationError(f"{prefix} forbids reviewer additions")
        if row["adjudication_state"] != "unreviewed":
            raise GenerationError(
                f"{prefix} was not frozen before relevance review"
            )
        selection_ordinal = parse_positive_int(
            row["selection_ordinal"], f"{prefix} selection_ordinal"
        )
        split_ordinal = parse_positive_int(
            row["split_ordinal"], f"{prefix} split_ordinal"
        )
        selection_sha = sha256_text(
            AUDIT_SELECTION_POLICY_VERSION,
            snapshot_key,
            row["normalized_expression_key"],
        )
        expected_case_key = "audit_case.round2b.sha256_" + sha256_text(
            AUDIT_SELECTION_POLICY_VERSION,
            snapshot_key,
            row["normalized_expression_key"],
        )
        if row["selection_sha256"] != selection_sha:
            raise GenerationError(f"{prefix} selection hash does not verify")
        if case_key != expected_case_key:
            raise GenerationError(f"{prefix} audit case key does not verify")
        selection_ordinals.append(selection_ordinal)
        split_ordinals[split].append(split_ordinal)
        split_counts[split] += 1
        result[case_key] = {
            **row,
            "occurrence_count_int": occurrence_count,
            "document_count_int": document_count,
            "strata": strata,
            "selection_ordinal_int": selection_ordinal,
            "split_ordinal_int": split_ordinal,
            "tuning_eligible_bool": tuning_eligible,
        }

    if sorted(selection_ordinals) != list(range(1, len(rows) + 1)):
        raise GenerationError("selection ordinals are not a complete 1..N sequence")
    for split, ordinals in split_ordinals.items():
        if sorted(ordinals) != list(range(1, len(ordinals) + 1)):
            raise GenerationError(f"{split} split ordinals are not contiguous")
    if split_counts["development"] != expected_development_count:
        raise GenerationError(
            "development count differs from the frozen expected count"
        )
    if split_counts["held_out"] != expected_count - expected_development_count:
        raise GenerationError("held-out count differs from the frozen expected count")
    if not split_counts["development"] or not split_counts["held_out"]:
        raise GenerationError("both development and held-out splits are required")
    return result


def _validate_signal_ledger(
    *,
    case_key: str,
    concept_key: str,
    baseline: str,
    tier: str,
    ledger: Any,
    seed_concept_key: Any,
    relation_type_code: Any,
    traversal_direction: Any,
) -> list[dict[str, Any]]:
    label = f"{case_key}/{concept_key}/{baseline}"
    if not isinstance(ledger, list) or not ledger:
        raise GenerationError(f"{label} has no signal ledger")
    if any(not isinstance(signal, dict) for signal in ledger):
        raise GenerationError(f"{label} signal ledger must contain objects")
    codes = [signal.get("signal_code") for signal in ledger]
    if any(not isinstance(code, str) for code in codes) or len(codes) != len(
        set(codes)
    ):
        raise GenerationError(f"{label} has invalid or duplicate signal codes")
    if frozenset(codes) not in DIRECT_SIGNAL_SETS[tier]:
        raise GenerationError(f"{label} signal set does not match tier {tier}")

    normalized: list[dict[str, Any]] = []
    for ordinal, signal in enumerate(ledger, 1):
        code = signal["signal_code"]
        allowed_keys = {"signal_code", "value"}
        if code == "pg_trgm_similarity":
            allowed_keys.add("value_semantics")
        elif code == "typed_graph_hop":
            allowed_keys.update(
                {
                    "relation_type_code",
                    "traversal_direction",
                    "source_concept_key",
                }
            )
        if set(signal) != allowed_keys:
            raise GenerationError(f"{label}/{code} has unexpected signal fields")

        value = signal["value"]
        context: dict[str, Any] = {
            "retrieval_baseline_code": baseline,
            "retrieval_tier_code": tier,
        }
        if code in {
            "raw_surface_exact",
            "normalized_phrase_match",
            "approved_variant_match",
        }:
            if value is not True:
                raise GenerationError(f"{label}/{code} must be boolean true")
            numeric_value = 1.0
        elif code == "pg_trgm_similarity":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise GenerationError(f"{label}/{code} must be numeric")
            numeric_value = float(value)
            if not 0.0 <= numeric_value <= 1.0:
                raise GenerationError(f"{label}/{code} is outside [0,1]")
            if signal.get("value_semantics") != "orthographic similarity only":
                raise GenerationError(f"{label}/{code} semantics changed")
        else:
            if isinstance(value, bool) or value != 1:
                raise GenerationError(f"{label}/{code} must be one hop")
            numeric_value = 1.0
            if (
                signal.get("source_concept_key") != seed_concept_key
                or signal.get("relation_type_code") != relation_type_code
                or signal.get("traversal_direction") != traversal_direction
            ):
                raise GenerationError(f"{label}/{code} trace fields disagree")
            context.update(
                {
                    "source_concept_key": seed_concept_key,
                    "relation_type_code": relation_type_code,
                    "traversal_direction": traversal_direction,
                }
            )
        normalized.append(
            {
                "signal_ordinal": ordinal,
                "signal_code": code,
                "signal_value": numeric_value,
                "context": context,
            }
        )
    return normalized


def validate_candidate_pool(
    rows: list[dict[str, str]],
    cases: Mapping[str, Mapping[str, Any]],
    *,
    top_k: int,
) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    assert_unique(rows, "candidate_pool_key", "candidate pool key")
    seen_case_concepts: set[tuple[str, str]] = set()
    records: list[dict[str, Any]] = []
    pooled_concepts: dict[str, set[str]] = {
        case_key: set() for case_key in cases
    }

    for row_number, row in enumerate(rows, 2):
        prefix = f"audit_candidate_pool.tsv:{row_number}"
        pool_key = row["candidate_pool_key"]
        if not AUDIT_CANDIDATE_KEY_RE.fullmatch(pool_key):
            raise GenerationError(f"{prefix} has a non-hash candidate key")
        case_key = row["audit_case_key"]
        if case_key not in cases:
            raise GenerationError(f"{prefix} references an unknown case")
        case = cases[case_key]
        if row["audit_split_code"] != case["audit_split_code"]:
            raise GenerationError(f"{prefix} split differs from its case")
        if row["normalized_expression_key"] != case["normalized_expression_key"]:
            raise GenerationError(f"{prefix} normalized identity differs")
        concept_key = validate_key(row["concept_key"], f"{prefix} concept_key")
        concept_type = validate_key(
            row["concept_type_code"], f"{prefix} concept_type_code"
        )
        pair = (case_key, concept_key)
        if pair in seen_case_concepts:
            raise GenerationError(f"{prefix} duplicates a case/concept")
        seen_case_concepts.add(pair)
        pooled_concepts[case_key].add(concept_key)
        if row["candidate_source_code"] != "deterministic_retrieval":
            raise GenerationError(f"{prefix} is not a deterministic candidate")
        if any(
            row[field]
            for field in (
                "reviewer_added_by",
                "reviewer_added_at",
                "reviewer_addition_rationale",
            )
        ):
            raise GenerationError(
                f"{prefix} candidate pool was modified during review"
            )
        expected_pool_key = "audit_candidate.round2b.sha256_" + sha256_text(
            AUDIT_SELECTION_POLICY_VERSION,
            case_key,
            concept_key,
            "deterministic_retrieval",
        )
        if pool_key != expected_pool_key:
            raise GenerationError(f"{prefix} candidate pool key does not verify")

        baselines = parse_json_field(
            row["retrieved_by_baselines_json"],
            f"{prefix} retrieved_by_baselines_json",
            list,
        )
        if (
            not baselines
            or any(code not in BASELINES for code in baselines)
            or baselines != sorted(set(baselines), key=BASELINES.index)
        ):
            raise GenerationError(f"{prefix} has invalid baseline membership")
        ranks = parse_json_field(
            row["baseline_ranks_json"], f"{prefix} baseline_ranks_json", dict
        )
        if set(ranks) != set(baselines):
            raise GenerationError(f"{prefix} baseline rank coverage differs")
        for baseline, rank in ranks.items():
            if isinstance(rank, bool) or not isinstance(rank, int) or not 1 <= rank <= top_k:
                raise GenerationError(f"{prefix}/{baseline} has invalid rank")
        statuses = parse_json_field(
            row["retrieval_status_codes_json"],
            f"{prefix} retrieval_status_codes_json",
            list,
        )
        if not statuses or any(status not in ("CANDIDATE", "RESOLVED") for status in statuses):
            raise GenerationError(f"{prefix} has invalid retrieval statuses")
        matched_keys = parse_json_field(
            row["matched_expression_keys_json"],
            f"{prefix} matched_expression_keys_json",
            list,
        )
        if (
            any(not isinstance(key, str) for key in matched_keys)
            or matched_keys != sorted(set(matched_keys))
        ):
            raise GenerationError(f"{prefix} matched expression keys are invalid")
        for key in matched_keys:
            validate_key(key, f"{prefix} matched expression key")
        ledger_records = parse_json_field(
            row["signal_ledger_by_baseline_json"],
            f"{prefix} signal_ledger_by_baseline_json",
            list,
        )
        if len(ledger_records) != len(baselines):
            raise GenerationError(f"{prefix} ledger/baseline coverage differs")
        seen_baselines: set[str] = set()
        normalized_records: list[dict[str, Any]] = []
        for ledger_record in ledger_records:
            if not isinstance(ledger_record, dict) or set(ledger_record) != {
                "retrieval_baseline_code",
                "candidate_rank",
                "retrieval_tier_code",
                "signal_ledger",
                "seed_concept_key",
                "relation_type_code",
                "traversal_direction",
            }:
                raise GenerationError(f"{prefix} has malformed ledger metadata")
            baseline = ledger_record["retrieval_baseline_code"]
            tier = ledger_record["retrieval_tier_code"]
            rank = ledger_record["candidate_rank"]
            if baseline not in baselines or baseline in seen_baselines:
                raise GenerationError(f"{prefix} repeats or invents a baseline")
            seen_baselines.add(baseline)
            if tier not in TIERS or TIERS[tier] > BASELINE_MAXIMUM_TIER[baseline]:
                raise GenerationError(f"{prefix}/{baseline} exceeds its tier")
            if isinstance(rank, bool) or rank != ranks[baseline]:
                raise GenerationError(f"{prefix}/{baseline} rank disagrees")

            seed_key = ledger_record["seed_concept_key"]
            relation = ledger_record["relation_type_code"]
            direction = ledger_record["traversal_direction"]
            if tier == "D":
                if (
                    not isinstance(seed_key, str)
                    or not isinstance(relation, str)
                    or direction not in ("OUTGOING", "INCOMING", "SYMMETRIC")
                    or matched_keys
                ):
                    raise GenerationError(f"{prefix}/{baseline} has an invalid graph trace")
                validate_key(seed_key, f"{prefix}/{baseline} seed concept")
                validate_key(relation, f"{prefix}/{baseline} relation")
                matched_key_hash = None
            else:
                if seed_key is not None or relation is not None or direction is not None:
                    raise GenerationError(f"{prefix}/{baseline} direct trace has graph fields")
                if len(matched_keys) != 1:
                    raise GenerationError(
                        f"{prefix}/{baseline} cannot bind one direct matched expression; "
                        "the pooled export is ambiguous"
                    )
                matched_key_hash = sha256_text(matched_keys[0])

            signals = _validate_signal_ledger(
                case_key=case_key,
                concept_key=concept_key,
                baseline=baseline,
                tier=tier,
                ledger=ledger_record["signal_ledger"],
                seed_concept_key=seed_key,
                relation_type_code=relation,
                traversal_direction=direction,
            )
            raw_surface_exact = any(
                signal["signal_code"] == "raw_surface_exact" for signal in signals
            )
            normalized_phrase_match = any(
                signal["signal_code"] == "normalized_phrase_match"
                for signal in signals
            )
            trigram_similarity = next(
                (
                    signal["signal_value"]
                    for signal in signals
                    if signal["signal_code"] == "pg_trgm_similarity"
                ),
                None,
            )
            normalized_records.append(
                {
                    "candidate_pool_key": pool_key,
                    "audit_case_key": case_key,
                    "audit_split_code": row["audit_split_code"],
                    "concept_key": concept_key,
                    "concept_type_code": concept_type,
                    "retrieval_baseline_code": baseline,
                    "candidate_rank": rank,
                    "retrieval_tier_code": tier,
                    "tier_order": TIERS[tier],
                    "matched_expression_key_sha256": matched_key_hash,
                    "seed_concept_key": seed_key,
                    "relation_type_code": relation,
                    "traversal_direction": direction,
                    "graph_hop_count": 1 if tier == "D" else 0,
                    "raw_surface_exact": raw_surface_exact,
                    "normalized_phrase_match": normalized_phrase_match,
                    "trigram_similarity": trigram_similarity,
                    "signals": signals,
                    "signal_ledger_sha256": sha256_text(
                        canonical_json(ledger_record)
                    ),
                }
            )

        if seen_baselines != set(baselines):
            raise GenerationError(f"{prefix} ledger coverage is incomplete")
        ordered = sorted(
            normalized_records,
            key=lambda item: (
                item["tier_order"],
                item["candidate_rank"],
                BASELINES.index(item["retrieval_baseline_code"]),
            ),
        )
        best = ordered[0]
        if (
            row["best_retrieval_tier_code"] != best["retrieval_tier_code"]
            or parse_positive_int(row["best_tier_order"], f"{prefix} best_tier_order")
            != best["tier_order"]
            or parse_positive_int(
                row["best_candidate_rank"], f"{prefix} best_candidate_rank"
            )
            != best["candidate_rank"]
        ):
            raise GenerationError(f"{prefix} best-candidate summary disagrees")
        records.extend(normalized_records)

    rank_groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    concept_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in records:
        scope = (
            record["audit_case_key"],
            record["retrieval_baseline_code"],
        )
        rank_groups[scope].append(record["candidate_rank"])
        if record["concept_key"] in concept_groups[scope]:
            raise GenerationError(f"duplicate concept in baseline scope {scope}")
        concept_groups[scope].add(record["concept_key"])
    for scope, ranks in rank_groups.items():
        if sorted(ranks) != list(range(1, len(ranks) + 1)):
            raise GenerationError(f"candidate ranks are not contiguous for {scope}")
        if len(ranks) > top_k:
            raise GenerationError(f"candidate count exceeds top_k for {scope}")

    records.sort(
        key=lambda item: (
            cases[item["audit_case_key"]]["selection_ordinal_int"],
            BASELINES.index(item["retrieval_baseline_code"]),
            item["candidate_rank"],
            item["concept_key"],
        )
    )
    return records, pooled_concepts


def _review_decision_sha(
    *,
    case_key: str,
    private_actor_key: str,
    expects_unresolved: bool,
    judgments: Sequence[Mapping[str, Any]],
    unresolved_rationale_sha256: str | None,
) -> str:
    receipt = {
        "audit_case_key": case_key,
        "actor_key_sha256": opaque_identity(private_actor_key),
        "expects_unresolved": expects_unresolved,
        "unresolved_rationale_sha256": unresolved_rationale_sha256,
        "judgments": [
            {
                "concept_key": row["concept_key"],
                "relevance_grade_code": row["relevance_grade_code"],
                "rationale_sha256": row["rationale_sha256"],
            }
            for row in sorted(judgments, key=lambda item: item["concept_key"])
        ],
    }
    return sha256_text(REVIEW_LEDGER_VERSION, canonical_json(receipt))


def validate_review_ledger(
    rows: list[dict[str, str]],
    cases: Mapping[str, Mapping[str, Any]],
    pooled_concepts: Mapping[str, set[str]],
    *,
    actor_field: str,
    independent: bool,
    model_frozen_at: datetime,
) -> tuple[str, dict[str, dict[str, Any]]]:
    actor_values = {row[actor_field] for row in rows}
    if len(actor_values) != 1:
        raise GenerationError(f"{actor_field} must be constant within one ledger")
    private_actor_key = validate_key(actor_values.pop(), actor_field)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row_number, row in enumerate(rows, 2):
        prefix = f"private ledger:{row_number}"
        case_key = row["audit_case_key"]
        if case_key not in cases:
            raise GenerationError(f"{prefix} references an unknown audit case")
        grade = row["relevance_grade_code"]
        if grade not in GRADES:
            raise GenerationError(f"{prefix} grade is outside 0/1/2/3/U")
        if not row["rationale"] or row["rationale"] != row["rationale"].strip():
            raise GenerationError(f"{prefix} requires a trimmed private rationale")
        if independent and row["independent_attestation"] != "true":
            raise GenerationError(f"{prefix} lacks independent attestation")
        concept_key = row["concept_key"]
        if grade == "U":
            if concept_key:
                raise GenerationError(f"{prefix} U must be a case-level blank concept")
        else:
            validate_key(concept_key, f"{prefix} concept_key")
        parse_timestamp(row["reviewed_at"], f"{prefix} reviewed_at")
        grouped[case_key].append(row)

    if set(grouped) != set(cases):
        missing = sorted(set(cases) - set(grouped))
        extra = sorted(set(grouped) - set(cases))
        raise GenerationError(
            "private ledger case coverage is not exact; "
            f"missing={missing[:3]}, extra={extra[:3]}"
        )

    result: dict[str, dict[str, Any]] = {}
    for case_key, case_rows in grouped.items():
        times = {
            parse_timestamp(row["reviewed_at"], "reviewed_at")
            for row in case_rows
        }
        if len(times) != 1:
            raise GenerationError(
                f"{case_key} ledger rows must share one review timestamp"
            )
        reviewed_at = times.pop()
        if cases[case_key]["audit_split_code"] == "held_out" and not (
            reviewed_at > model_frozen_at
        ):
            raise GenerationError(
                f"held-out review {case_key} is not strictly post-freeze"
            )
        unresolved_rows = [
            row for row in case_rows if row["relevance_grade_code"] == "U"
        ]
        if len(unresolved_rows) > 1:
            raise GenerationError(f"{case_key} has duplicate U decisions")
        expects_unresolved = bool(unresolved_rows)
        numeric_rows = [
            row for row in case_rows if row["relevance_grade_code"] != "U"
        ]
        concepts = [row["concept_key"] for row in numeric_rows]
        if len(concepts) != len(set(concepts)):
            raise GenerationError(f"{case_key} repeats a concept judgment")
        missing_pool = pooled_concepts[case_key] - set(concepts)
        if missing_pool:
            raise GenerationError(
                f"{case_key} did not explicitly grade every pooled candidate"
            )
        grades = [int(row["relevance_grade_code"]) for row in numeric_rows]
        if expects_unresolved:
            if any(grade >= 2 for grade in grades):
                raise GenerationError(
                    f"{case_key} is U but assigns a grade-2-or-3 concept"
                )
        elif not any(grade >= 2 for grade in grades):
            raise GenerationError(
                f"{case_key} is resolvable without a grade-2-or-3 concept"
            )
        judgments = [
            {
                "concept_key": row["concept_key"],
                "relevance_grade_code": row["relevance_grade_code"],
                "rationale_sha256": sha256_text(row["rationale"]),
            }
            for row in numeric_rows
        ]
        unresolved_rationale_sha = (
            sha256_text(unresolved_rows[0]["rationale"])
            if unresolved_rows
            else None
        )
        result[case_key] = {
            "private_actor_key": private_actor_key,
            "public_actor_key": "reviewer.round2b.private_sha256_"
            + opaque_identity(private_actor_key),
            "reviewed_at": reviewed_at,
            "expects_unresolved": expects_unresolved,
            "judgments": judgments,
            "unresolved_rationale_sha256": unresolved_rationale_sha,
            "decision_sha256": _review_decision_sha(
                case_key=case_key,
                private_actor_key=private_actor_key,
                expects_unresolved=expects_unresolved,
                judgments=judgments,
                unresolved_rationale_sha256=unresolved_rationale_sha,
            ),
        }
    return private_actor_key, result


def validate_adjudication_closure(
    adjudication: Mapping[str, Mapping[str, Any]],
    review_one: Mapping[str, Mapping[str, Any]],
    review_two: Mapping[str, Mapping[str, Any]],
    pooled_concepts: Mapping[str, set[str]],
) -> None:
    for case_key, adjudicated in adjudication.items():
        required = (
            pooled_concepts[case_key]
            | {row["concept_key"] for row in review_one[case_key]["judgments"]}
            | {row["concept_key"] for row in review_two[case_key]["judgments"]}
        )
        actual = {
            row["concept_key"] for row in adjudicated["judgments"]
        }
        if not required <= actual:
            raise GenerationError(
                f"adjudication for {case_key} does not grade the pooled and "
                "reviewer-added concept union"
            )
        latest_independent = max(
            review_one[case_key]["reviewed_at"],
            review_two[case_key]["reviewed_at"],
        )
        if adjudicated["reviewed_at"] < latest_independent:
            raise GenerationError(
                f"adjudication for {case_key} predates independent review"
            )


def public_case_rows(cases: Mapping[str, Mapping[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for case in sorted(cases.values(), key=lambda row: row["selection_ordinal_int"]):
        output.append(
            {
                "audit_case_key": case["audit_case_key"],
                "corpus_snapshot_key": case["corpus_snapshot_key"],
                "normalization_pipeline_key": case["normalization_pipeline_key"],
                "normalized_expression_identity_sha256": sha256_text(
                    case["normalized_expression_key"]
                ),
                "representative_expression_identity_sha256": sha256_text(
                    case["representative_expression_key"]
                ),
                "representative_observation_expression_identity_sha256": sha256_text(
                    case["representative_observation_expression_key"]
                ),
                "occurrence_count": case["occurrence_count"],
                "document_count": case["document_count"],
                "primary_stratum_code": case["primary_stratum_code"],
                "stratum_codes_json": case["stratum_codes_json"],
                "audit_split_code": case["audit_split_code"],
                "selection_ordinal": case["selection_ordinal"],
                "split_ordinal": case["split_ordinal"],
                "selection_sha256": case["selection_sha256"],
                "tuning_eligible": case["tuning_eligible"],
            }
        )
    return output


def public_candidate_rows(
    source_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in source_rows:
        matched = json.loads(row["matched_expression_keys_json"])
        ledger = json.loads(row["signal_ledger_by_baseline_json"])
        output.append(
            {
                "candidate_pool_key": row["candidate_pool_key"],
                "audit_case_key": row["audit_case_key"],
                "audit_split_code": row["audit_split_code"],
                "concept_key": row["concept_key"],
                "concept_type_code": row["concept_type_code"],
                "retrieved_by_baselines_json": row[
                    "retrieved_by_baselines_json"
                ],
                "baseline_ranks_json": row["baseline_ranks_json"],
                "best_retrieval_tier_code": row[
                    "best_retrieval_tier_code"
                ],
                "best_tier_order": row["best_tier_order"],
                "best_candidate_rank": row["best_candidate_rank"],
                "retrieval_status_codes_json": row[
                    "retrieval_status_codes_json"
                ],
                "matched_expression_identity_sha256s_json": canonical_json(
                    [sha256_text(key) for key in matched]
                ),
                "signal_ledger_by_baseline_json": canonical_json(ledger),
                "signal_ledger_sha256": sha256_text(canonical_json(ledger)),
            }
        )
    output.sort(
        key=lambda row: (
            row["audit_case_key"],
            int(row["best_tier_order"]),
            int(row["best_candidate_rank"]),
            row["concept_key"],
        )
    )
    return output


def public_qrel_rows(
    cases: Mapping[str, Mapping[str, Any]],
    adjudication: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for case_key in sorted(
        cases, key=lambda key: cases[key]["selection_ordinal_int"]
    ):
        decision = adjudication[case_key]
        if decision["expects_unresolved"]:
            output.append(
                {
                    "audit_case_key": case_key,
                    "audit_split_code": cases[case_key]["audit_split_code"],
                    "expects_unresolved": "true",
                    "concept_key": "",
                    "relevance_grade_code": "U",
                    "adjudication_rationale_sha256": decision[
                        "unresolved_rationale_sha256"
                    ],
                    "adjudicated_at": timestamp_text(decision["reviewed_at"]),
                }
            )
        for judgment in sorted(
            decision["judgments"], key=lambda row: row["concept_key"]
        ):
            output.append(
                {
                    "audit_case_key": case_key,
                    "audit_split_code": cases[case_key]["audit_split_code"],
                    "expects_unresolved": bool_text(
                        decision["expects_unresolved"]
                    ),
                    "concept_key": judgment["concept_key"],
                    "relevance_grade_code": judgment[
                        "relevance_grade_code"
                    ],
                    "adjudication_rationale_sha256": judgment[
                        "rationale_sha256"
                    ],
                    "adjudicated_at": timestamp_text(decision["reviewed_at"]),
                }
            )
    return output


def public_review_receipt_rows(
    cases: Mapping[str, Mapping[str, Any]],
    review_one: Mapping[str, Mapping[str, Any]],
    review_two: Mapping[str, Mapping[str, Any]],
    adjudication: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for case_key in sorted(
        cases, key=lambda key: cases[key]["selection_ordinal_int"]
    ):
        first = review_one[case_key]
        second = review_two[case_key]
        gold = adjudication[case_key]
        first_map = {
            row["concept_key"]: row["relevance_grade_code"]
            for row in first["judgments"]
        }
        second_map = {
            row["concept_key"]: row["relevance_grade_code"]
            for row in second["judgments"]
        }
        output.append(
            {
                "audit_case_key": case_key,
                "audit_split_code": cases[case_key]["audit_split_code"],
                "reviewer_one_decision_sha256": first["decision_sha256"],
                "reviewer_two_decision_sha256": second["decision_sha256"],
                "adjudication_decision_sha256": gold["decision_sha256"],
                "independent_reviewers_agree": bool_text(
                    first["expects_unresolved"] == second["expects_unresolved"]
                    and first_map == second_map
                ),
                "reviewer_one_expects_unresolved": bool_text(
                    first["expects_unresolved"]
                ),
                "reviewer_two_expects_unresolved": bool_text(
                    second["expects_unresolved"]
                ),
                "adjudicated_expects_unresolved": bool_text(
                    gold["expects_unresolved"]
                ),
            }
        )
    return output


def inference_statuses(
    cases: Mapping[str, Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], str]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[
            (
                candidate["audit_case_key"],
                candidate["retrieval_baseline_code"],
            )
        ].append(candidate)
    result: dict[tuple[str, str], str] = {}
    for case_key in cases:
        for baseline in BASELINES:
            records = grouped[(case_key, baseline)]
            direct = [row for row in records if row["retrieval_tier_code"] != "D"]
            if not records:
                status = "unresolved"
            elif (
                len(direct) == 1
                and direct[0]["retrieval_tier_code"] in ("A", "B")
            ):
                status = "resolved"
            else:
                status = "pending"
            result[(case_key, baseline)] = status
    return result


def stable_keys(
    *,
    audit_set_key: str,
    model_run_keys: Mapping[str, str],
    case_key: str,
    baseline: str,
    concept_key: str | None = None,
    signal_code: str | None = None,
    signal_ordinal: int | None = None,
) -> dict[str, str]:
    inference_key = "mapping_inference.round2b.sha256_" + sha256_text(
        COMPILER_VERSION,
        audit_set_key,
        model_run_keys[baseline],
        case_key,
    )
    result = {"mapping_inference_key": inference_key}
    if concept_key is not None:
        candidate_key = "mapping_candidate.round2b.sha256_" + sha256_text(
            COMPILER_VERSION, inference_key, concept_key
        )
        result["mapping_candidate_key"] = candidate_key
        if signal_code is not None and signal_ordinal is not None:
            result["candidate_signal_key"] = (
                "candidate_signal.round2b.sha256_"
                + sha256_text(
                    COMPILER_VERSION,
                    candidate_key,
                    signal_code,
                    str(signal_ordinal),
                )
            )
    return result


def evaluation_seed_rows(
    *,
    audit_set_key: str,
    model_run_keys: Mapping[str, str],
    generated_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    evaluations: list[dict[str, Any]] = []
    metrics: list[dict[str, str]] = []
    for baseline in BASELINES:
        for split in ("development", "held_out"):
            evaluation_key = "retrieval_evaluation.round2b.sha256_" + sha256_text(
                METRIC_POLICY_VERSION,
                audit_set_key,
                model_run_keys[baseline],
                split,
            )
            configuration = {
                "calculation_function": "audit.calculate_retrieval_metrics",
                "metric_policy_version": METRIC_POLICY_VERSION,
                "relevance_threshold": 2,
                "ndcg_gains": {"0": 0, "1": 1, "2": 3, "3": 7},
                "unresolved_cases_excluded_from_ranking_metrics": True,
            }
            configuration_json = canonical_json(configuration)
            evaluations.append(
                {
                    "evaluation_key": evaluation_key,
                    "model_run_key": model_run_keys[baseline],
                    "baseline": baseline,
                    "split": split,
                    "evaluated_at": timestamp_text(generated_at),
                    "configuration_json": configuration_json,
                    "configuration_sha256": sha256_text(configuration_json),
                }
            )
            for metric_code, cutoff in METRIC_SPECS:
                metric_key = "retrieval_metric_value.round2b.sha256_" + sha256_text(
                    METRIC_POLICY_VERSION,
                    evaluation_key,
                    metric_code,
                    str(cutoff),
                )
                metrics.append(
                    {
                        "retrieval_evaluation_key": evaluation_key,
                        "model_run_key": model_run_keys[baseline],
                        "retrieval_baseline_code": baseline,
                        "audit_split_code": split,
                        "retrieval_metric_value_key": metric_key,
                        "retrieval_metric_code": metric_code,
                        "cutoff_k": str(cutoff),
                        "calculation_source": "audit.calculate_retrieval_metrics",
                    }
                )
    return evaluations, metrics


def copy_block(
    table: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.writer(
        buffer,
        delimiter="\t",
        quotechar='"',
        lineterminator="\n",
    )
    for row in rows:
        writer.writerow([r"\N" if value is None else value for value in row])
    return (
        f"COPY {table} ({', '.join(columns)}) FROM STDIN "
        "WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N');\n"
        + buffer.getvalue()
        + "\\.\n"
    )


def build_sql(
    *,
    cases: Mapping[str, Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    review_one: Mapping[str, Mapping[str, Any]],
    review_two: Mapping[str, Mapping[str, Any]],
    adjudication: Mapping[str, Mapping[str, Any]],
    reviewer_private_keys: Sequence[str],
    input_hashes: Mapping[str, str],
    snapshot_key: str,
    pipeline_key: str,
    derivation_run_key: str,
    graph_policy_key: str,
    code_commit_sha: str,
    model_key: str,
    model_version_key: str,
    model_run_keys: Mapping[str, str],
    audit_set_key: str,
    audit_set_version: str,
    model_frozen_at: datetime,
    generated_at: datetime,
    top_k: int,
    trigram_threshold: float,
    evaluations: Sequence[Mapping[str, Any]],
    metrics: Sequence[Mapping[str, str]],
) -> str:
    ordered_cases = sorted(
        cases.values(), key=lambda row: row["selection_ordinal_int"]
    )
    statuses = inference_statuses(cases, candidates)
    inventory_sha = sha256_text(
        COMPILER_VERSION,
        snapshot_key,
        input_hashes["audit_cases.tsv"],
        input_hashes["audit_candidate_pool.tsv"],
    )
    model_configuration = {
        "code_commit_sha": code_commit_sha,
        "compiler_version": COMPILER_VERSION,
        "corpus_snapshot_key": snapshot_key,
        "normalization_pipeline_key": pipeline_key,
        "normalization_derivation_run_key": derivation_run_key,
        "graph_policy_key": graph_policy_key,
        "retrieval_baselines": list(BASELINES),
        "top_k": top_k,
        "trigram_threshold": trigram_threshold,
        "weighted_composite_score": False,
        "embeddings": False,
        "llm": False,
        "audit_case_sha256": input_hashes["audit_cases.tsv"],
        "candidate_pool_sha256": input_hashes["audit_candidate_pool.tsv"],
    }
    model_configuration_json = canonical_json(model_configuration)
    reviewer_public_keys = [
        "reviewer.round2b.private_sha256_" + opaque_identity(key)
        for key in reviewer_private_keys
    ]

    sql: list[str] = [
        "\\set ON_ERROR_STOP on\n",
        "-- Generated by db/scripts/generate-round2b-evaluation.py.\n",
        "-- Hash-only observed-expression binding; no private phrase or rationale text.\n",
        "-- A/B/C/D are ordinal ablations, not weighted sensory scores.\n\n",
        "-- Retrieved candidates must be active. Qrels may reference any existing governed concept,\n",
        "-- including non-active concepts retained to measure ontology gaps; qrels are not model output.\n\n",
        "BEGIN;\nSET CONSTRAINTS ALL DEFERRED;\n\n",
        "DO $preflight$\nDECLARE checked_count BIGINT;\nBEGIN\n",
        "  IF current_setting('server_version_num')::INTEGER < 170000 THEN\n",
        "    RAISE EXCEPTION 'Round 2B evaluation seed requires PostgreSQL 17';\n",
        "  END IF;\n",
        "  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN\n",
        "    RAISE EXCEPTION 'Round 2B evaluation seed requires pg_trgm';\n",
        "  END IF;\n",
        "  SELECT count(*) INTO checked_count\n",
        "  FROM corpus.corpus_snapshot AS snapshot\n",
        "  JOIN corpus.normalization_pipeline AS pipeline\n",
        "    ON pipeline.normalization_pipeline_id = snapshot.normalization_pipeline_id\n",
        "  JOIN corpus.normalization_derivation_run AS derivation\n",
        "    ON derivation.corpus_snapshot_id = snapshot.corpus_snapshot_id\n",
        "   AND derivation.normalization_pipeline_id = pipeline.normalization_pipeline_id\n",
        "  WHERE snapshot.corpus_snapshot_key = ",
        sql_literal(snapshot_key),
        " AND snapshot.frozen_at IS NOT NULL\n",
        "    AND pipeline.normalization_pipeline_key = ",
        sql_literal(pipeline_key),
        " AND pipeline.frozen_at IS NOT NULL\n",
        "    AND derivation.normalization_derivation_run_key = ",
        sql_literal(derivation_run_key),
        " AND derivation.frozen_at IS NOT NULL;\n",
        "  IF checked_count <> 1 THEN RAISE EXCEPTION 'Frozen snapshot/pipeline/derivation contract not found exactly once'; END IF;\n",
        "  IF NOT EXISTS (SELECT 1 FROM ml.retrieval_graph_policy WHERE retrieval_graph_policy_key = ",
        sql_literal(graph_policy_key),
        " AND is_frozen) THEN RAISE EXCEPTION 'Frozen graph policy not found'; END IF;\n",
        "END;\n$preflight$;\n\n",
        "CREATE TEMP TABLE _r2b_eval_case_seed (\n",
        "  audit_case_key TEXT PRIMARY KEY, expression_key_sha256 TEXT NOT NULL,\n",
        "  observation_expression_key_sha256 TEXT NOT NULL, audit_split_code TEXT NOT NULL,\n",
        "  case_ordinal INTEGER NOT NULL, selection_sha256 TEXT NOT NULL\n",
        ") ON COMMIT DROP;\n",
    ]
    sql.append(
        copy_block(
            "_r2b_eval_case_seed",
            (
                "audit_case_key",
                "expression_key_sha256",
                "observation_expression_key_sha256",
                "audit_split_code",
                "case_ordinal",
                "selection_sha256",
            ),
            (
                (
                    case["audit_case_key"],
                    sha256_text(case["representative_expression_key"]),
                    sha256_text(case["representative_observation_expression_key"]),
                    case["audit_split_code"],
                    case["selection_ordinal_int"],
                    case["selection_sha256"],
                )
                for case in ordered_cases
            ),
        )
    )
    sql.extend(
        [
            "CREATE TEMP TABLE _r2b_eval_stratum_seed (audit_case_key TEXT NOT NULL, retrieval_audit_stratum_code TEXT NOT NULL, PRIMARY KEY (audit_case_key, retrieval_audit_stratum_code)) ON COMMIT DROP;\n",
            copy_block(
                "_r2b_eval_stratum_seed",
                ("audit_case_key", "retrieval_audit_stratum_code"),
                (
                    (case["audit_case_key"], stratum)
                    for case in ordered_cases
                    for stratum in case["strata"]
                ),
            ),
            "CREATE TEMP TABLE _r2b_eval_candidate_seed (\n",
            "  audit_case_key TEXT NOT NULL, retrieval_baseline_code TEXT NOT NULL,\n",
            "  concept_key TEXT NOT NULL, candidate_rank INTEGER NOT NULL, retrieval_tier_code TEXT NOT NULL,\n",
            "  matched_expression_key_sha256 TEXT, seed_concept_key TEXT, relation_type_code TEXT, traversal_direction TEXT,\n",
            "  graph_hop_count SMALLINT NOT NULL, raw_surface_exact BOOLEAN NOT NULL, normalized_phrase_match BOOLEAN NOT NULL,\n",
            "  signal_ledger_sha256 TEXT NOT NULL, PRIMARY KEY (audit_case_key, retrieval_baseline_code, concept_key),\n",
            "  UNIQUE (audit_case_key, retrieval_baseline_code, candidate_rank)\n",
            ") ON COMMIT DROP;\n",
            copy_block(
                "_r2b_eval_candidate_seed",
                (
                    "audit_case_key",
                    "retrieval_baseline_code",
                    "concept_key",
                    "candidate_rank",
                    "retrieval_tier_code",
                    "matched_expression_key_sha256",
                    "seed_concept_key",
                    "relation_type_code",
                    "traversal_direction",
                    "graph_hop_count",
                    "raw_surface_exact",
                    "normalized_phrase_match",
                    "signal_ledger_sha256",
                ),
                (
                    (
                        row["audit_case_key"],
                        row["retrieval_baseline_code"],
                        row["concept_key"],
                        row["candidate_rank"],
                        row["retrieval_tier_code"],
                        row["matched_expression_key_sha256"],
                        row["seed_concept_key"],
                        row["relation_type_code"],
                        row["traversal_direction"],
                        row["graph_hop_count"],
                        bool_text(row["raw_surface_exact"]),
                        bool_text(row["normalized_phrase_match"]),
                        row["signal_ledger_sha256"],
                    )
                    for row in candidates
                ),
            ),
            "CREATE TEMP TABLE _r2b_eval_signal_seed (\n",
            "  audit_case_key TEXT NOT NULL, retrieval_baseline_code TEXT NOT NULL, concept_key TEXT NOT NULL,\n",
            "  signal_ordinal SMALLINT NOT NULL, retrieval_signal_code TEXT NOT NULL, signal_value NUMERIC NOT NULL,\n",
            "  value_semantics TEXT NOT NULL, context JSONB NOT NULL, candidate_signal_key TEXT NOT NULL UNIQUE,\n",
            "  PRIMARY KEY (audit_case_key, retrieval_baseline_code, concept_key, signal_ordinal)\n",
            ") ON COMMIT DROP;\n",
        ]
    )
    signal_rows: list[tuple[Any, ...]] = []
    signal_semantics = {
        "raw_surface_exact": "Binary raw-surface identity indicator; not a sensory score.",
        "normalized_phrase_match": "Binary versioned-normalization identity indicator; not a sensory score.",
        "approved_variant_match": "Binary governed-variant indicator; not a sensory score.",
        "pg_trgm_similarity": "PostgreSQL trigram orthographic similarity only; not sensory similarity.",
        "typed_graph_hop": "One allowlisted canonical graph hop; not a sensory coefficient.",
    }
    for candidate in candidates:
        for signal in candidate["signals"]:
            keys = stable_keys(
                audit_set_key=audit_set_key,
                model_run_keys=model_run_keys,
                case_key=candidate["audit_case_key"],
                baseline=candidate["retrieval_baseline_code"],
                concept_key=candidate["concept_key"],
                signal_code=signal["signal_code"],
                signal_ordinal=signal["signal_ordinal"],
            )
            context = dict(signal["context"])
            context["signal_ledger_sha256"] = candidate["signal_ledger_sha256"]
            signal_rows.append(
                (
                    candidate["audit_case_key"],
                    candidate["retrieval_baseline_code"],
                    candidate["concept_key"],
                    signal["signal_ordinal"],
                    signal["signal_code"],
                    format(signal["signal_value"], ".17g"),
                    signal_semantics[signal["signal_code"]],
                    canonical_json(context),
                    keys["candidate_signal_key"],
                )
            )
    sql.append(
        copy_block(
            "_r2b_eval_signal_seed",
            (
                "audit_case_key",
                "retrieval_baseline_code",
                "concept_key",
                "signal_ordinal",
                "retrieval_signal_code",
                "signal_value",
                "value_semantics",
                "context",
                "candidate_signal_key",
            ),
            signal_rows,
        )
    )

    review_rows: list[tuple[Any, ...]] = []
    judgment_rows: list[tuple[Any, ...]] = []
    review_sources = (
        ("independent", review_one, input_hashes["review_one.tsv"]),
        ("independent", review_two, input_hashes["review_two.tsv"]),
        ("adjudicated", adjudication, input_hashes["adjudication.tsv"]),
    )
    for role, ledger, ledger_sha in review_sources:
        for case in ordered_cases:
            case_key = case["audit_case_key"]
            decision = ledger[case_key]
            public_actor = decision["public_actor_key"]
            review_key = "retrieval_case_review.round2b.sha256_" + sha256_text(
                COMPILER_VERSION, audit_set_key, case_key, public_actor, role
            )
            review_rows.append(
                (
                    review_key,
                    case_key,
                    public_actor,
                    role,
                    bool_text(decision["expects_unresolved"]),
                    timestamp_text(decision["reviewed_at"]),
                    ledger_sha,
                    decision["decision_sha256"],
                )
            )
            for judgment in decision["judgments"]:
                judgment_key = (
                    "retrieval_relevance_judgment.round2b.sha256_"
                    + sha256_text(
                        COMPILER_VERSION,
                        review_key,
                        judgment["concept_key"],
                    )
                )
                judgment_rows.append(
                    (
                        judgment_key,
                        review_key,
                        judgment["concept_key"],
                        judgment["relevance_grade_code"],
                        judgment["rationale_sha256"],
                    )
                )
    sql.extend(
        [
            "CREATE TEMP TABLE _r2b_eval_review_seed (\n",
            "  retrieval_case_review_key TEXT PRIMARY KEY, audit_case_key TEXT NOT NULL, reviewer_key TEXT NOT NULL,\n",
            "  audit_review_role_code TEXT NOT NULL, expects_unresolved BOOLEAN NOT NULL, reviewed_at TIMESTAMPTZ NOT NULL,\n",
            "  private_ledger_sha256 TEXT NOT NULL, decision_sha256 TEXT NOT NULL\n",
            ") ON COMMIT DROP;\n",
            copy_block(
                "_r2b_eval_review_seed",
                (
                    "retrieval_case_review_key",
                    "audit_case_key",
                    "reviewer_key",
                    "audit_review_role_code",
                    "expects_unresolved",
                    "reviewed_at",
                    "private_ledger_sha256",
                    "decision_sha256",
                ),
                review_rows,
            ),
            "CREATE TEMP TABLE _r2b_eval_judgment_seed (\n",
            "  retrieval_relevance_judgment_key TEXT PRIMARY KEY, retrieval_case_review_key TEXT NOT NULL,\n",
            "  concept_key TEXT NOT NULL, relevance_grade_code TEXT NOT NULL, private_rationale_sha256 TEXT NOT NULL\n",
            ") ON COMMIT DROP;\n",
            copy_block(
                "_r2b_eval_judgment_seed",
                (
                    "retrieval_relevance_judgment_key",
                    "retrieval_case_review_key",
                    "concept_key",
                    "relevance_grade_code",
                    "private_rationale_sha256",
                ),
                judgment_rows,
            ),
            "CREATE TEMP TABLE _r2b_eval_inference_seed (\n",
            "  mapping_inference_key TEXT PRIMARY KEY, audit_case_key TEXT NOT NULL, retrieval_baseline_code TEXT NOT NULL,\n",
            "  model_run_key TEXT NOT NULL, resolution_status_code TEXT NOT NULL, UNIQUE (audit_case_key, retrieval_baseline_code)\n",
            ") ON COMMIT DROP;\n",
        ]
    )
    inference_rows = []
    for case in ordered_cases:
        for baseline in BASELINES:
            keys = stable_keys(
                audit_set_key=audit_set_key,
                model_run_keys=model_run_keys,
                case_key=case["audit_case_key"],
                baseline=baseline,
            )
            inference_rows.append(
                (
                    keys["mapping_inference_key"],
                    case["audit_case_key"],
                    baseline,
                    model_run_keys[baseline],
                    statuses[(case["audit_case_key"], baseline)],
                )
            )
    sql.append(
        copy_block(
            "_r2b_eval_inference_seed",
            (
                "mapping_inference_key",
                "audit_case_key",
                "retrieval_baseline_code",
                "model_run_key",
                "resolution_status_code",
            ),
            inference_rows,
        )
    )
    sql.extend(
        [
            "CREATE TEMP TABLE _r2b_eval_evaluation_seed (\n",
            "  evaluation_key TEXT PRIMARY KEY, model_run_key TEXT NOT NULL, baseline_code TEXT NOT NULL, split_code TEXT NOT NULL,\n",
            "  evaluated_at TIMESTAMPTZ NOT NULL, configuration JSONB NOT NULL, configuration_sha256 TEXT NOT NULL\n",
            ") ON COMMIT DROP;\n",
            copy_block(
                "_r2b_eval_evaluation_seed",
                (
                    "evaluation_key",
                    "model_run_key",
                    "baseline_code",
                    "split_code",
                    "evaluated_at",
                    "configuration",
                    "configuration_sha256",
                ),
                (
                    (
                        row["evaluation_key"],
                        row["model_run_key"],
                        row["baseline"],
                        row["split"],
                        row["evaluated_at"],
                        row["configuration_json"],
                        row["configuration_sha256"],
                    )
                    for row in evaluations
                ),
            ),
            "CREATE TEMP TABLE _r2b_eval_metric_seed (\n",
            "  metric_value_key TEXT PRIMARY KEY, evaluation_key TEXT NOT NULL, metric_code TEXT NOT NULL, cutoff_k SMALLINT NOT NULL,\n",
            "  UNIQUE (evaluation_key, metric_code, cutoff_k)\n",
            ") ON COMMIT DROP;\n",
            copy_block(
                "_r2b_eval_metric_seed",
                ("metric_value_key", "evaluation_key", "metric_code", "cutoff_k"),
                (
                    (
                        row["retrieval_metric_value_key"],
                        row["retrieval_evaluation_key"],
                        row["retrieval_metric_code"],
                        row["cutoff_k"],
                    )
                    for row in metrics
                ),
            ),
            "\nDO $seed_closure$\nDECLARE checked_count BIGINT;\nBEGIN\n",
            "  SELECT count(*) INTO checked_count FROM _r2b_eval_case_seed AS seed JOIN kb.lexical_expression AS expression ON encode(sha256(convert_to(expression.expression_key, 'UTF8')), 'hex') = seed.expression_key_sha256 JOIN corpus.observation_expression AS occurrence ON encode(sha256(convert_to(occurrence.observation_expression_key, 'UTF8')), 'hex') = seed.observation_expression_key_sha256 AND occurrence.expression_id = expression.expression_id;\n",
            f"  IF checked_count <> {len(ordered_cases)} THEN RAISE EXCEPTION 'Hash-only audit case identities do not resolve exactly'; END IF;\n",
            "  IF EXISTS (SELECT 1 FROM _r2b_eval_candidate_seed AS seed LEFT JOIN kb.concept AS concept ON concept.concept_key = seed.concept_key AND concept.lifecycle_status_code = 'active' WHERE concept.concept_id IS NULL) THEN RAISE EXCEPTION 'Candidate concept is absent or inactive'; END IF;\n",
            "  IF EXISTS (SELECT 1 FROM _r2b_eval_judgment_seed AS seed LEFT JOIN kb.concept AS concept ON concept.concept_key = seed.concept_key WHERE concept.concept_id IS NULL) THEN RAISE EXCEPTION 'Judged concept is absent'; END IF;\n",
            "  IF EXISTS (SELECT 1 FROM _r2b_eval_candidate_seed AS seed WHERE seed.retrieval_tier_code IN ('A','B','C') AND (SELECT count(*) FROM kb.lexical_expression AS expression WHERE encode(sha256(convert_to(expression.expression_key, 'UTF8')), 'hex') = seed.matched_expression_key_sha256) <> 1) THEN RAISE EXCEPTION 'Direct matched expression hash does not resolve exactly once'; END IF;\n",
            "  IF EXISTS (SELECT 1 FROM _r2b_eval_candidate_seed AS graph WHERE graph.retrieval_tier_code = 'D' AND NOT EXISTS (SELECT 1 FROM _r2b_eval_candidate_seed AS seed WHERE seed.audit_case_key = graph.audit_case_key AND seed.retrieval_baseline_code = graph.retrieval_baseline_code AND seed.concept_key = graph.seed_concept_key AND seed.retrieval_tier_code IN ('A','B','C'))) THEN RAISE EXCEPTION 'Graph candidate lacks an in-scope direct seed'; END IF;\n",
            "END;\n$seed_closure$;\n\n",
            "INSERT INTO evidence.statistical_method (method_key, name, description) VALUES\n",
            " ('statistical_method.round2b.deterministic_indicator', 'Round 2B deterministic indicator', 'Binary deterministic retrieval signal; not a sensory measurement.'),\n",
            " ('statistical_method.round2b.pg_trgm_similarity', 'Round 2B PostgreSQL trigram similarity', 'Orthographic PostgreSQL pg_trgm similarity; not sensory similarity.'),\n",
            " ('statistical_method.round2b.typed_graph_hop', 'Round 2B typed graph hop', 'One-hop allowlisted canonical graph traversal; not a sensory coefficient.');\n",
            "INSERT INTO evidence.measurement_scale (scale_key, name, minimum_value, maximum_value, unit, value_semantics) VALUES\n",
            " ('measurement_scale.round2b.binary_indicator', 'Round 2B binary indicator', 0, 1, NULL, 'Zero/one deterministic indicator.'),\n",
            " ('measurement_scale.round2b.unit_interval', 'Round 2B unit interval', 0, 1, NULL, 'Inclusive unit interval for orthographic similarity.'),\n",
            " ('measurement_scale.round2b.one_hop', 'Round 2B one-hop count', 0, 1, 'hop', 'Exactly one allowlisted canonical graph hop for emitted graph candidates.');\n\n",
            "INSERT INTO ml.model (model_key, name, model_family, description, external_metadata) VALUES (",
            sql_literal(model_key),
            ", 'Round 2B deterministic lexical retrieval', 'deterministic_ordinal_retrieval', 'Exact, approved variant, pg_trgm, and allowlisted one-hop graph retrieval; no embeddings, LLM, or weighted aggregate.', ",
            sql_literal(canonical_json({"pgvector_required": False, "embedding_baseline_run": False})),
            "::JSONB);\n",
            "INSERT INTO ml.model_version (model_version_key, model_id, version_label, artifact_locator, configuration, created_at) SELECT ",
            sql_literal(model_version_key),
            ", model.model_id, ",
            sql_literal(audit_set_version),
            ", 'db/scripts/generate-round2b-evaluation.py', ",
            sql_literal(model_configuration_json),
            "::JSONB, ",
            sql_literal(timestamp_text(model_frozen_at)),
            "::TIMESTAMPTZ FROM ml.model AS model WHERE model.model_key = ",
            sql_literal(model_key),
            ";\n",
        ]
    )
    for baseline in BASELINES:
        run_config = {
            "retrieval_baseline_code": baseline,
            "normalization_pipeline_key": pipeline_key,
            "graph_policy_key": graph_policy_key if baseline == "D" else None,
            "top_k": top_k,
            "trigram_threshold": trigram_threshold,
            "candidate_pool_sha256": input_hashes["audit_candidate_pool.tsv"],
            "code_commit_sha": code_commit_sha,
            "weighted_composite_score": False,
        }
        run_json = canonical_json(run_config)
        config_sha = sha256_text(run_json)
        candidate_count = sum(
            row["retrieval_baseline_code"] == baseline for row in candidates
        )
        sql.extend(
            [
                "INSERT INTO ml.model_run (model_run_key, model_version_id, model_run_status_code, input_dataset_id, input_corpus_id, started_at, completed_at, random_seed, run_configuration, result_metadata) SELECT ",
                sql_literal(model_run_keys[baseline]),
                ", version.model_version_id, 'running', snapshot.manifest_dataset_id, snapshot.corpus_id, ",
                sql_literal(timestamp_text(model_frozen_at)),
                "::TIMESTAMPTZ, NULL, NULL, ",
                sql_literal(run_json),
                "::JSONB, '{}'::JSONB FROM ml.model_version AS version CROSS JOIN corpus.corpus_snapshot AS snapshot WHERE version.model_version_key = ",
                sql_literal(model_version_key),
                " AND snapshot.corpus_snapshot_key = ",
                sql_literal(snapshot_key),
                ";\n",
                "INSERT INTO ml.deterministic_retrieval_run (model_run_id, retrieval_baseline_code, normalization_pipeline_id, retrieval_graph_policy_id, top_k, trigram_threshold, configuration_sha256) SELECT run.model_run_id, ",
                sql_literal(baseline),
                ", pipeline.normalization_pipeline_id, ",
                (
                    "policy.retrieval_graph_policy_id"
                    if baseline == "D"
                    else "NULL::BIGINT"
                ),
                f", {top_k}, {format(trigram_threshold, '.17g')}::REAL, ",
                sql_literal(config_sha),
                " FROM ml.model_run AS run CROSS JOIN corpus.normalization_pipeline AS pipeline ",
                (
                    "CROSS JOIN ml.retrieval_graph_policy AS policy "
                    if baseline == "D"
                    else ""
                ),
                "WHERE run.model_run_key = ",
                sql_literal(model_run_keys[baseline]),
                " AND pipeline.normalization_pipeline_key = ",
                sql_literal(pipeline_key),
                (
                    " AND policy.retrieval_graph_policy_key = "
                    + sql_literal(graph_policy_key)
                    if baseline == "D"
                    else ""
                ),
                ";\n",
                f"-- Expected persisted candidate count for baseline {baseline}: {candidate_count}.\n",
            ]
        )
    sampling_configuration = {
        "selection_policy_version": AUDIT_SELECTION_POLICY_VERSION,
        "review_ledger_version": REVIEW_LEDGER_VERSION,
        "case_count": len(cases),
        "development_count": sum(
            case["audit_split_code"] == "development" for case in cases.values()
        ),
        "held_out_count": sum(
            case["audit_split_code"] == "held_out" for case in cases.values()
        ),
        "synthetic_padding": False,
        "held_out_tuning_eligible": False,
        "retrieved_candidates_require_active_concepts": True,
        "qrels_require_existing_concepts": True,
        "non_active_qrels_measure_ontology_gaps": True,
        "input_hashes": dict(sorted(input_hashes.items())),
    }
    sql.extend(
        [
            "\nINSERT INTO audit.retrieval_audit_set (retrieval_audit_set_key, corpus_snapshot_id, version_label, name, description, sampling_configuration, inventory_sha256, code_commit_sha, created_at, frozen_at) SELECT ",
            sql_literal(audit_set_key),
            ", snapshot.corpus_snapshot_id, ",
            sql_literal(audit_set_version),
            ", 'Round 2B held-out deterministic retrieval audit', 'Stratified actual normalized expressions with development and held-out splits; no synthetic padding.', ",
            sql_literal(canonical_json(sampling_configuration)),
            "::JSONB, ",
            sql_literal(inventory_sha),
            ", ",
            sql_literal(code_commit_sha),
            ", ",
            sql_literal(timestamp_text(model_frozen_at)),
            "::TIMESTAMPTZ, NULL FROM corpus.corpus_snapshot AS snapshot WHERE snapshot.corpus_snapshot_key = ",
            sql_literal(snapshot_key),
            ";\n",
            "INSERT INTO audit.retrieval_audit_case (retrieval_audit_case_key, retrieval_audit_set_id, expression_id, representative_observation_expression_id, audit_split_code, case_ordinal, notes) SELECT seed.audit_case_key, audit_set.retrieval_audit_set_id, expression.expression_id, occurrence.observation_expression_id, seed.audit_split_code, seed.case_ordinal, 'Frozen selection SHA-256: ' || seed.selection_sha256 FROM _r2b_eval_case_seed AS seed JOIN audit.retrieval_audit_set AS audit_set ON audit_set.retrieval_audit_set_key = ",
            sql_literal(audit_set_key),
            " JOIN kb.lexical_expression AS expression ON encode(sha256(convert_to(expression.expression_key, 'UTF8')), 'hex') = seed.expression_key_sha256 JOIN corpus.observation_expression AS occurrence ON encode(sha256(convert_to(occurrence.observation_expression_key, 'UTF8')), 'hex') = seed.observation_expression_key_sha256 AND occurrence.expression_id = expression.expression_id ORDER BY seed.case_ordinal;\n",
            "INSERT INTO audit.retrieval_audit_case_stratum (retrieval_audit_case_id, retrieval_audit_stratum_code) SELECT audit_case.retrieval_audit_case_id, seed.retrieval_audit_stratum_code FROM _r2b_eval_stratum_seed AS seed JOIN audit.retrieval_audit_case AS audit_case ON audit_case.retrieval_audit_case_key = seed.audit_case_key ORDER BY audit_case.retrieval_audit_case_id, seed.retrieval_audit_stratum_code;\n\n",
        ]
    )
    for index, public_key in enumerate(reviewer_public_keys, 1):
        role_name = (
            f"Round 2B independent reviewer {index} (pseudonymous)"
            if index <= 2
            else "Round 2B adjudicator (pseudonymous)"
        )
        sql.extend(
            [
                "INSERT INTO audit.reviewer (reviewer_key, display_name, affiliation) VALUES (",
                sql_literal(public_key),
                ", ",
                sql_literal(role_name),
                ", NULL);\n",
            ]
        )
    sql.extend(
        [
            "INSERT INTO audit.retrieval_case_review (retrieval_case_review_key, retrieval_audit_case_id, reviewer_id, audit_review_role_code, expects_unresolved, reviewed_at, notes) SELECT seed.retrieval_case_review_key, audit_case.retrieval_audit_case_id, reviewer.reviewer_id, seed.audit_review_role_code, seed.expects_unresolved, seed.reviewed_at, 'Private ledger SHA-256: ' || seed.private_ledger_sha256 || '; decision receipt SHA-256: ' || seed.decision_sha256 FROM _r2b_eval_review_seed AS seed JOIN audit.retrieval_audit_case AS audit_case ON audit_case.retrieval_audit_case_key = seed.audit_case_key JOIN audit.reviewer AS reviewer ON reviewer.reviewer_key = seed.reviewer_key ORDER BY audit_case.retrieval_audit_case_id, seed.audit_review_role_code, reviewer.reviewer_id;\n",
            "INSERT INTO audit.retrieval_relevance_judgment (retrieval_relevance_judgment_key, retrieval_case_review_id, concept_id, relevance_grade_code, rationale) SELECT seed.retrieval_relevance_judgment_key, review.retrieval_case_review_id, concept.concept_id, seed.relevance_grade_code, 'Private rationale withheld; SHA-256=' || seed.private_rationale_sha256 FROM _r2b_eval_judgment_seed AS seed JOIN audit.retrieval_case_review AS review ON review.retrieval_case_review_key = seed.retrieval_case_review_key JOIN kb.concept AS concept ON concept.concept_key = seed.concept_key ORDER BY review.retrieval_case_review_id, concept.concept_id;\n\n",
            "INSERT INTO ml.mapping_inference (mapping_inference_key, model_run_id, observation_expression_id, resolution_status_code, inferred_at, resolution_notes) SELECT seed.mapping_inference_key, run.model_run_id, audit_case.representative_observation_expression_id, seed.resolution_status_code, ",
            sql_literal(timestamp_text(model_frozen_at)),
            "::TIMESTAMPTZ, CASE seed.resolution_status_code WHEN 'unresolved' THEN 'Explicit deterministic abstention: no candidate survived.' WHEN 'resolved' THEN 'Exactly one direct approved A/B candidate resolved the expression.' ELSE 'Reviewable ordinal candidates; no forced resolution.' END FROM _r2b_eval_inference_seed AS seed JOIN ml.model_run AS run ON run.model_run_key = seed.model_run_key JOIN audit.retrieval_audit_case AS audit_case ON audit_case.retrieval_audit_case_key = seed.audit_case_key ORDER BY run.model_run_id, audit_case.case_ordinal;\n",
            "INSERT INTO ml.mapping_candidate (mapping_candidate_key, mapping_inference_id, concept_id, candidate_status_code, rank, rationale) SELECT 'mapping_candidate.round2b.sha256_' || encode(sha256(convert_to(",
            sql_literal(COMPILER_VERSION + "\x1f"),
            " || inference.mapping_inference_key || E'\\x1f' || seed.concept_key, 'UTF8')), 'hex'), inference.mapping_inference_id, concept.concept_id, 'proposed', seed.candidate_rank, 'Deterministic ordinal retrieval candidate; signals are preserved separately without a weighted aggregate.' FROM _r2b_eval_candidate_seed AS seed JOIN _r2b_eval_inference_seed AS inference_seed ON inference_seed.audit_case_key = seed.audit_case_key AND inference_seed.retrieval_baseline_code = seed.retrieval_baseline_code JOIN ml.mapping_inference AS inference ON inference.mapping_inference_key = inference_seed.mapping_inference_key JOIN kb.concept AS concept ON concept.concept_key = seed.concept_key ORDER BY inference.mapping_inference_id, seed.candidate_rank;\n",
            "INSERT INTO ml.deterministic_candidate_trace (mapping_candidate_id, retrieval_tier_code, matched_expression_id, seed_mapping_candidate_id, concept_relation_id, traversal_direction, graph_hop_count, raw_surface_exact, normalized_phrase_match) SELECT candidate.mapping_candidate_id, seed.retrieval_tier_code, expression.expression_id, NULL, NULL, NULL, 0, seed.raw_surface_exact, seed.normalized_phrase_match FROM _r2b_eval_candidate_seed AS seed JOIN _r2b_eval_inference_seed AS inference_seed ON inference_seed.audit_case_key = seed.audit_case_key AND inference_seed.retrieval_baseline_code = seed.retrieval_baseline_code JOIN ml.mapping_inference AS inference ON inference.mapping_inference_key = inference_seed.mapping_inference_key JOIN ml.mapping_candidate AS candidate ON candidate.mapping_inference_id = inference.mapping_inference_id JOIN kb.concept AS concept ON concept.concept_id = candidate.concept_id AND concept.concept_key = seed.concept_key JOIN kb.lexical_expression AS expression ON encode(sha256(convert_to(expression.expression_key, 'UTF8')), 'hex') = seed.matched_expression_key_sha256 WHERE seed.retrieval_tier_code IN ('A','B','C') ORDER BY candidate.mapping_candidate_id;\n",
            "INSERT INTO ml.deterministic_candidate_trace (mapping_candidate_id, retrieval_tier_code, matched_expression_id, seed_mapping_candidate_id, concept_relation_id, traversal_direction, graph_hop_count, raw_surface_exact, normalized_phrase_match) SELECT candidate.mapping_candidate_id, 'D', NULL, seed_candidate.mapping_candidate_id, neighbour.concept_relation_id, seed.traversal_direction, 1, FALSE, FALSE FROM _r2b_eval_candidate_seed AS seed JOIN _r2b_eval_inference_seed AS inference_seed ON inference_seed.audit_case_key = seed.audit_case_key AND inference_seed.retrieval_baseline_code = seed.retrieval_baseline_code JOIN ml.mapping_inference AS inference ON inference.mapping_inference_key = inference_seed.mapping_inference_key JOIN ml.mapping_candidate AS candidate ON candidate.mapping_inference_id = inference.mapping_inference_id JOIN kb.concept AS concept ON concept.concept_id = candidate.concept_id AND concept.concept_key = seed.concept_key JOIN kb.concept AS seed_concept ON seed_concept.concept_key = seed.seed_concept_key JOIN ml.mapping_candidate AS seed_candidate ON seed_candidate.mapping_inference_id = inference.mapping_inference_id AND seed_candidate.concept_id = seed_concept.concept_id JOIN kb.v_concept_neighbours AS neighbour ON neighbour.concept_id = seed_concept.concept_id AND neighbour.neighbour_concept_id = concept.concept_id AND neighbour.relation_type_code = seed.relation_type_code AND neighbour.traversal_direction = seed.traversal_direction WHERE seed.retrieval_tier_code = 'D' ORDER BY candidate.mapping_candidate_id;\n",
            "INSERT INTO ml.candidate_signal (candidate_signal_key, mapping_candidate_id, signal_domain_code, statistical_method_id, dataset_id, measurement_scale_id, signal_value, value_semantics, context) SELECT signal.candidate_signal_key, candidate.mapping_candidate_id, signal_type.signal_domain_code, method.statistical_method_id, snapshot.manifest_dataset_id, scale.measurement_scale_id, signal.signal_value, signal.value_semantics, signal.context FROM _r2b_eval_signal_seed AS signal JOIN _r2b_eval_inference_seed AS inference_seed ON inference_seed.audit_case_key = signal.audit_case_key AND inference_seed.retrieval_baseline_code = signal.retrieval_baseline_code JOIN ml.mapping_inference AS inference ON inference.mapping_inference_key = inference_seed.mapping_inference_key JOIN ml.mapping_candidate AS candidate ON candidate.mapping_inference_id = inference.mapping_inference_id JOIN kb.concept AS concept ON concept.concept_id = candidate.concept_id AND concept.concept_key = signal.concept_key JOIN ref.retrieval_signal AS signal_type ON signal_type.retrieval_signal_code = signal.retrieval_signal_code JOIN evidence.statistical_method AS method ON method.method_key = CASE signal.retrieval_signal_code WHEN 'pg_trgm_similarity' THEN 'statistical_method.round2b.pg_trgm_similarity' WHEN 'typed_graph_hop' THEN 'statistical_method.round2b.typed_graph_hop' ELSE 'statistical_method.round2b.deterministic_indicator' END JOIN evidence.measurement_scale AS scale ON scale.scale_key = CASE signal.retrieval_signal_code WHEN 'pg_trgm_similarity' THEN 'measurement_scale.round2b.unit_interval' WHEN 'typed_graph_hop' THEN 'measurement_scale.round2b.one_hop' ELSE 'measurement_scale.round2b.binary_indicator' END JOIN corpus.corpus_snapshot AS snapshot ON snapshot.corpus_snapshot_key = ",
            sql_literal(snapshot_key),
            " ORDER BY candidate.mapping_candidate_id, signal.signal_ordinal;\n",
            "INSERT INTO ml.deterministic_candidate_signal (candidate_signal_id, mapping_candidate_id, retrieval_signal_code, signal_ordinal) SELECT candidate_signal.candidate_signal_id, candidate_signal.mapping_candidate_id, seed.retrieval_signal_code, seed.signal_ordinal FROM _r2b_eval_signal_seed AS seed JOIN ml.candidate_signal AS candidate_signal ON candidate_signal.candidate_signal_key = seed.candidate_signal_key ORDER BY candidate_signal.mapping_candidate_id, seed.signal_ordinal;\n\n",
        ]
    )
    for baseline in BASELINES:
        candidate_count = sum(
            row["retrieval_baseline_code"] == baseline for row in candidates
        )
        unresolved_count = sum(
            statuses[(case_key, baseline)] == "unresolved" for case_key in cases
        )
        metadata = canonical_json(
            {
                "candidate_count": candidate_count,
                "case_count": len(cases),
                "unresolved_inference_count": unresolved_count,
                "automatic_ontology_promotion": False,
            }
        )
        sql.extend(
            [
                "UPDATE ml.model_run SET model_run_status_code = 'completed', completed_at = ",
                sql_literal(timestamp_text(model_frozen_at)),
                "::TIMESTAMPTZ, result_metadata = ",
                sql_literal(metadata),
                "::JSONB WHERE model_run_key = ",
                sql_literal(model_run_keys[baseline]),
                ";\n",
            ]
        )
    sql.extend(
        [
            "\nUPDATE audit.retrieval_audit_set SET frozen_at = ",
            sql_literal(timestamp_text(generated_at)),
            "::TIMESTAMPTZ WHERE retrieval_audit_set_key = ",
            sql_literal(audit_set_key),
            ";\n",
            "INSERT INTO audit.retrieval_evaluation (retrieval_evaluation_key, retrieval_audit_set_id, model_run_id, audit_split_code, evaluated_at, evaluation_configuration, configuration_sha256, notes) SELECT seed.evaluation_key, audit_set.retrieval_audit_set_id, run.model_run_id, seed.split_code, seed.evaluated_at, seed.configuration, seed.configuration_sha256, 'Language-retrieval evaluation; not coffee flavor accuracy.' FROM _r2b_eval_evaluation_seed AS seed JOIN audit.retrieval_audit_set AS audit_set ON audit_set.retrieval_audit_set_key = ",
            sql_literal(audit_set_key),
            " JOIN ml.model_run AS run ON run.model_run_key = seed.model_run_key ORDER BY seed.baseline_code, seed.split_code;\n",
            "INSERT INTO audit.retrieval_metric_value (retrieval_metric_value_key, retrieval_evaluation_id, retrieval_metric_code, cutoff_k, numerator, denominator, metric_value, value_semantics) SELECT metric_seed.metric_value_key, evaluation.retrieval_evaluation_id, calculated.retrieval_metric_code, calculated.cutoff_k, calculated.numerator, calculated.denominator, calculated.metric_value, calculated.value_semantics FROM _r2b_eval_metric_seed AS metric_seed JOIN _r2b_eval_evaluation_seed AS evaluation_seed ON evaluation_seed.evaluation_key = metric_seed.evaluation_key JOIN audit.retrieval_evaluation AS evaluation ON evaluation.retrieval_evaluation_key = evaluation_seed.evaluation_key CROSS JOIN LATERAL audit.calculate_retrieval_metrics(",
            sql_literal(audit_set_key),
            ", evaluation_seed.model_run_key, evaluation_seed.split_code) AS calculated WHERE calculated.retrieval_metric_code = metric_seed.metric_code AND calculated.cutoff_k = metric_seed.cutoff_k ORDER BY evaluation.retrieval_evaluation_id, calculated.retrieval_metric_code, calculated.cutoff_k;\n",
            "\nDO $final_closure$\nDECLARE checked_count BIGINT;\nBEGIN\n",
            f"  SELECT count(*) INTO checked_count FROM audit.retrieval_audit_case AS c JOIN audit.retrieval_audit_set AS s ON s.retrieval_audit_set_id = c.retrieval_audit_set_id WHERE s.retrieval_audit_set_key = {sql_literal(audit_set_key)}; IF checked_count <> {len(cases)} THEN RAISE EXCEPTION 'Audit case persistence count mismatch'; END IF;\n",
            f"  SELECT count(*) INTO checked_count FROM audit.retrieval_evaluation AS e JOIN audit.retrieval_audit_set AS s ON s.retrieval_audit_set_id = e.retrieval_audit_set_id WHERE s.retrieval_audit_set_key = {sql_literal(audit_set_key)}; IF checked_count <> {len(evaluations)} THEN RAISE EXCEPTION 'Evaluation persistence count mismatch'; END IF;\n",
            f"  SELECT count(*) INTO checked_count FROM audit.retrieval_metric_value AS m JOIN audit.retrieval_evaluation AS e ON e.retrieval_evaluation_id = m.retrieval_evaluation_id JOIN audit.retrieval_audit_set AS s ON s.retrieval_audit_set_id = e.retrieval_audit_set_id WHERE s.retrieval_audit_set_key = {sql_literal(audit_set_key)}; IF checked_count <> {len(metrics)} THEN RAISE EXCEPTION 'Metric persistence count mismatch'; END IF;\n",
            "END;\n$final_closure$;\n\nCOMMIT;\n",
        ]
    )
    return "".join(sql)


def tsv_bytes(headers: Sequence[str], rows: Iterable[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(headers),
        delimiter="\t",
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def write_outputs_atomic(
    output_dir: Path,
    artifacts: Mapping[str, bytes],
    *,
    overwrite: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in artifacts:
        destination = output_dir / name
        if destination.exists() and not overwrite:
            raise GenerationError(
                f"refusing to overwrite {destination} without --overwrite"
            )
    temporary: dict[str, Path] = {}
    try:
        for name, payload in artifacts.items():
            with tempfile.NamedTemporaryFile(
                "wb",
                dir=output_dir,
                prefix=name + ".",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                temporary[name] = Path(handle.name)
        for name in artifacts:
            os.replace(temporary.pop(name), output_dir / name)
        directory_fd = os.open(output_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        for path in temporary.values():
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def dry_run_contract() -> dict[str, Any]:
    return {
        "status": "dry_run",
        "compiler_version": COMPILER_VERSION,
        "files_read": False,
        "files_written": False,
        "grades_inferred": False,
        "private_phrases_exported": False,
        "private_rationales_exported": False,
        "review_headers": list(REVIEW_HEADERS),
        "adjudication_headers": list(ADJUDICATION_HEADERS),
        "required_baselines": list(BASELINES),
        "required_grade_domain": sorted(GRADES),
        "default_case_count": 300,
        "default_development_count": 75,
        "default_held_out_count": 225,
        "synthetic_padding_allowed": False,
        "retrieved_candidates_require_active_concepts": True,
        "qrels_require_existing_concepts": True,
        "non_active_qrels_measure_ontology_gaps": True,
        "database_metric_function": "audit.calculate_retrieval_metrics",
        "output_names": list(OUTPUT_NAMES),
        "held_out_tuning_eligible": False,
        "embedding_baseline_run": False,
        "pgvector_required": False,
    }


def parse_model_run_keys(values: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise GenerationError("--model-run-key must use BASELINE=stable_key")
        baseline, key = value.split("=", 1)
        baseline = baseline.strip().upper()
        if baseline not in BASELINES or baseline in result:
            raise GenerationError("model run keys must define A, B, C, and D once")
        result[baseline] = validate_key(key, f"model run key {baseline}")
    if set(result) != set(BASELINES):
        raise GenerationError("model run keys must define A, B, C, and D")
    if len(set(result.values())) != len(BASELINES):
        raise GenerationError("A/B/C/D model run keys must be distinct")
    return result


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate frozen Round 2B audit/review ledgers and emit phrase-free "
            "public artifacts plus a forward PostgreSQL evaluation seed."
        )
    )
    parser.add_argument("--audit-cases", type=Path)
    parser.add_argument("--candidate-pool", type=Path)
    parser.add_argument("--review-one", type=Path)
    parser.add_argument("--review-two", type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--audit-cases-sha256")
    parser.add_argument("--candidate-pool-sha256")
    parser.add_argument("--review-one-sha256")
    parser.add_argument("--review-two-sha256")
    parser.add_argument("--adjudication-sha256")
    parser.add_argument("--snapshot-key")
    parser.add_argument("--pipeline-key")
    parser.add_argument("--derivation-run-key")
    parser.add_argument("--graph-policy-key", default="graph_policy.round2b.v1")
    parser.add_argument("--code-commit-sha")
    parser.add_argument("--model-key")
    parser.add_argument("--model-version-key")
    parser.add_argument(
        "--model-run-key",
        action="append",
        default=[],
        metavar="BASELINE=KEY",
    )
    parser.add_argument("--audit-set-key")
    parser.add_argument("--audit-set-version")
    parser.add_argument("--model-frozen-at")
    parser.add_argument("--generated-at")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--expected-case-count", type=int, default=300)
    parser.add_argument("--expected-development-count", type=int, default=75)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--trigram-threshold", type=float, default=0.35)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the static contract without reading or writing files",
    )
    args = parser.parse_args(argv)
    if args.dry_run:
        return args
    required = (
        "audit_cases",
        "candidate_pool",
        "review_one",
        "review_two",
        "adjudication",
        "audit_cases_sha256",
        "candidate_pool_sha256",
        "review_one_sha256",
        "review_two_sha256",
        "adjudication_sha256",
        "snapshot_key",
        "pipeline_key",
        "derivation_run_key",
        "code_commit_sha",
        "model_key",
        "model_version_key",
        "audit_set_key",
        "audit_set_version",
        "model_frozen_at",
        "generated_at",
        "output_dir",
    )
    missing = [name for name in required if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join(missing))
    if args.expected_case_count <= 0:
        parser.error("--expected-case-count must be positive")
    if not 0 < args.expected_development_count < args.expected_case_count:
        parser.error("development count must be between zero and case count")
    if args.top_k != 5:
        parser.error("Round 2B frozen candidate-pool contract requires --top-k=5")
    if not 0.0 <= args.trigram_threshold <= 1.0:
        parser.error("--trigram-threshold must be in [0,1]")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.dry_run:
        print(json.dumps(dry_run_contract(), indent=2, sort_keys=True))
        return 0

    paths = {
        "audit_cases.tsv": args.audit_cases.resolve(),
        "audit_candidate_pool.tsv": args.candidate_pool.resolve(),
        "review_one.tsv": args.review_one.resolve(),
        "review_two.tsv": args.review_two.resolve(),
        "adjudication.tsv": args.adjudication.resolve(),
    }
    if len(set(paths.values())) != len(paths):
        raise GenerationError("all five input files must be distinct")
    expected_hashes = {
        "audit_cases.tsv": args.audit_cases_sha256,
        "audit_candidate_pool.tsv": args.candidate_pool_sha256,
        "review_one.tsv": args.review_one_sha256,
        "review_two.tsv": args.review_two_sha256,
        "adjudication.tsv": args.adjudication_sha256,
    }
    input_hashes = {
        label: validate_expected_hash(paths[label], expected_hashes[label], label)
        for label in paths
    }
    if len(set(input_hashes.values())) != len(input_hashes):
        raise GenerationError("input byte ledgers must be distinct")

    snapshot_key = validate_key(args.snapshot_key, "snapshot key")
    pipeline_key = validate_key(args.pipeline_key, "pipeline key")
    derivation_run_key = validate_key(args.derivation_run_key, "derivation key")
    graph_policy_key = validate_key(args.graph_policy_key, "graph policy key")
    model_key = validate_key(args.model_key, "model key")
    model_version_key = validate_key(args.model_version_key, "model version key")
    audit_set_key = validate_key(args.audit_set_key, "audit set key")
    audit_set_version = validate_key(args.audit_set_version, "audit set version")
    if not HEX40_RE.fullmatch(args.code_commit_sha):
        raise GenerationError("code commit SHA must be an exact 40-hex Git SHA")
    model_run_keys = parse_model_run_keys(args.model_run_key)
    model_frozen_at = parse_timestamp(args.model_frozen_at, "model_frozen_at")
    generated_at = parse_timestamp(args.generated_at, "generated_at")
    if generated_at <= model_frozen_at:
        raise GenerationError("generated_at must be strictly after model_frozen_at")

    case_source = read_tsv_exact(paths["audit_cases.tsv"], CASE_HEADERS)
    candidate_source = read_tsv_exact(
        paths["audit_candidate_pool.tsv"], CANDIDATE_HEADERS
    )
    review_one_source = read_tsv_exact(paths["review_one.tsv"], REVIEW_HEADERS)
    review_two_source = read_tsv_exact(paths["review_two.tsv"], REVIEW_HEADERS)
    adjudication_source = read_tsv_exact(
        paths["adjudication.tsv"], ADJUDICATION_HEADERS
    )
    cases = validate_cases(
        case_source,
        snapshot_key=snapshot_key,
        pipeline_key=pipeline_key,
        derivation_run_key=derivation_run_key,
        expected_count=args.expected_case_count,
        expected_development_count=args.expected_development_count,
    )
    candidates, pooled_concepts = validate_candidate_pool(
        candidate_source, cases, top_k=args.top_k
    )
    reviewer_one_key, review_one = validate_review_ledger(
        review_one_source,
        cases,
        pooled_concepts,
        actor_field="reviewer_key",
        independent=True,
        model_frozen_at=model_frozen_at,
    )
    reviewer_two_key, review_two = validate_review_ledger(
        review_two_source,
        cases,
        pooled_concepts,
        actor_field="reviewer_key",
        independent=True,
        model_frozen_at=model_frozen_at,
    )
    adjudicator_key, adjudication = validate_review_ledger(
        adjudication_source,
        cases,
        pooled_concepts,
        actor_field="adjudicator_key",
        independent=False,
        model_frozen_at=model_frozen_at,
    )
    if len({reviewer_one_key, reviewer_two_key, adjudicator_key}) != 3:
        raise GenerationError(
            "two independent reviewers and the adjudicator must be distinct"
        )
    validate_adjudication_closure(
        adjudication, review_one, review_two, pooled_concepts
    )
    latest_review = max(
        decision["reviewed_at"]
        for ledger in (review_one, review_two, adjudication)
        for decision in ledger.values()
    )
    if generated_at < latest_review:
        raise GenerationError("generated_at predates a private review decision")

    case_public = public_case_rows(cases)
    candidate_public = public_candidate_rows(candidate_source)
    qrels_public = public_qrel_rows(cases, adjudication)
    receipts_public = public_review_receipt_rows(
        cases, review_one, review_two, adjudication
    )
    evaluations, metrics_public = evaluation_seed_rows(
        audit_set_key=audit_set_key,
        model_run_keys=model_run_keys,
        generated_at=generated_at,
    )
    sql = build_sql(
        cases=cases,
        candidates=candidates,
        review_one=review_one,
        review_two=review_two,
        adjudication=adjudication,
        reviewer_private_keys=(
            reviewer_one_key,
            reviewer_two_key,
            adjudicator_key,
        ),
        input_hashes=input_hashes,
        snapshot_key=snapshot_key,
        pipeline_key=pipeline_key,
        derivation_run_key=derivation_run_key,
        graph_policy_key=graph_policy_key,
        code_commit_sha=args.code_commit_sha,
        model_key=model_key,
        model_version_key=model_version_key,
        model_run_keys=model_run_keys,
        audit_set_key=audit_set_key,
        audit_set_version=audit_set_version,
        model_frozen_at=model_frozen_at,
        generated_at=generated_at,
        top_k=args.top_k,
        trigram_threshold=args.trigram_threshold,
        evaluations=evaluations,
        metrics=metrics_public,
    )

    preliminary = {
        "audit_cases_public.tsv": tsv_bytes(PUBLIC_CASE_HEADERS, case_public),
        "audit_candidate_pool_public.tsv": tsv_bytes(
            PUBLIC_CANDIDATE_HEADERS, candidate_public
        ),
        "audit_qrels_public.tsv": tsv_bytes(PUBLIC_QREL_HEADERS, qrels_public),
        "audit_review_receipts_public.tsv": tsv_bytes(
            PUBLIC_REVIEW_RECEIPT_HEADERS, receipts_public
        ),
        "evaluation_metric_contract_public.tsv": tsv_bytes(
            PUBLIC_METRIC_CONTRACT_HEADERS, metrics_public
        ),
        "016_round2b_evaluation_seed.sql": sql.encode("utf-8"),
    }
    manifest = {
        "status": "generated",
        "compiler_version": COMPILER_VERSION,
        "code_commit_sha": args.code_commit_sha,
        "corpus_snapshot_key": snapshot_key,
        "normalization_pipeline_key": pipeline_key,
        "normalization_derivation_run_key": derivation_run_key,
        "graph_policy_key": graph_policy_key,
        "model_key": model_key,
        "model_version_key": model_version_key,
        "model_run_keys": dict(sorted(model_run_keys.items())),
        "audit_set_key": audit_set_key,
        "audit_set_version": audit_set_version,
        "model_frozen_at": timestamp_text(model_frozen_at),
        "generated_at": timestamp_text(generated_at),
        "case_count": len(cases),
        "development_case_count": sum(
            case["audit_split_code"] == "development" for case in cases.values()
        ),
        "held_out_case_count": sum(
            case["audit_split_code"] == "held_out" for case in cases.values()
        ),
        "pooled_candidate_count": len(candidate_source),
        "persisted_candidate_trace_count": len(candidates),
        "persisted_candidate_signal_count": sum(
            len(candidate["signals"]) for candidate in candidates
        ),
        "adjudicated_qrel_row_count": len(qrels_public),
        "evaluation_count": len(evaluations),
        "metric_value_contract_count": len(metrics_public),
        "input_artifacts": {
            label: {"sha256": digest}
            for label, digest in sorted(input_hashes.items())
        },
        "reviewer_receipts": {
            "reviewer_one_key_sha256": opaque_identity(reviewer_one_key),
            "reviewer_two_key_sha256": opaque_identity(reviewer_two_key),
            "adjudicator_key_sha256": opaque_identity(adjudicator_key),
            "distinct_actor_count": 3,
        },
        "governance": {
            "grades_inferred": False,
            "reviewer_added_concepts_can_enter_qrels_but_not_model_outputs": True,
            "retrieved_candidates_require_active_concepts": True,
            "qrels_require_existing_concepts": True,
            "non_active_qrels_measure_ontology_gaps": True,
            "private_phrases_exported": False,
            "private_rationales_exported": False,
            "held_out_tuning_eligible": False,
            "held_out_reviews_strictly_post_model_freeze": True,
            "synthetic_padding_used": False,
            "weighted_composite_score": False,
            "embedding_baseline_run": False,
            "pgvector_required": False,
        },
        "output_artifacts": {
            name: {
                "sha256": sha256_bytes(payload),
                "byte_count": len(payload),
            }
            for name, payload in sorted(preliminary.items())
        },
    }
    manifest_bytes = (
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    artifacts = dict(preliminary)
    artifacts["round2b_evaluation_manifest.json"] = manifest_bytes
    write_outputs_atomic(
        args.output_dir.resolve(), artifacts, overwrite=args.overwrite
    )
    receipt = {
        "status": "generated",
        "output_dir": str(args.output_dir.resolve()),
        "manifest_sha256": sha256_bytes(manifest_bytes),
        "case_count": len(cases),
        "development_case_count": args.expected_development_count,
        "held_out_case_count": len(cases) - args.expected_development_count,
        "persisted_candidate_trace_count": len(candidates),
        "metric_value_contract_count": len(metrics_public),
        "private_phrases_exported": False,
        "private_rationales_exported": False,
        "grades_inferred": False,
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as error:
        print(f"evaluation generation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
