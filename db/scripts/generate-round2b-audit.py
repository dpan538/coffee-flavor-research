#!/usr/bin/env python3
"""Materialize a deterministic, unjudged Round 2B retrieval audit pool.

The script is deliberately read-only. It selects actual normalized expression
identities from one frozen corpus derivation, assigns development/held-out
splits with deterministic stratification, and pools the top-five results from
each A/B/C/D retrieval baseline. It does not insert audit rows, invent relevance
judgments, expose held-out labels, or freeze an audit set.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence


SELECTION_POLICY_VERSION = "round2b-audit-selection-v1"
DEFAULT_SNAPSHOT_KEY = "corpus_snapshot.firstbloom_a6cb002_pilot_v1"
DEFAULT_PIPELINE_KEY = "normalization.en_v1"
DEFAULT_TARGET_SIZE = 300
DEFAULT_DEVELOPMENT_SIZE = 75
RETRIEVAL_TOP_K = 5
DEFAULT_TRIGRAM_THRESHOLD = 0.35
DEFAULT_HARD_NEGATIVE_FLOOR = 0.20

STRATUM_ORDER = (
    "exact",
    "variant",
    "orthographic_difficulty",
    "graph_reference",
    "qualifier_polysemy",
    "non_descriptive_language",
    "hard_negative",
    "unresolved",
)

# Targets guide deterministic over-sampling. Empty or small strata are never
# padded: their shortfall is filled from real unselected identities and is
# exposed in the receipt.
DEFAULT_STRATUM_TARGETS = {
    "exact": 30,
    "variant": 5,
    "orthographic_difficulty": 55,
    "graph_reference": 45,
    "qualifier_polysemy": 15,
    "non_descriptive_language": 5,
    "hard_negative": 60,
    "unresolved": 85,
}

MODIFIER_PROBES = frozenset(
    {"bright", "clean", "juicy", "jammy", "tea-like", "winey"}
)
NON_DESCRIPTIVE_TYPES = frozenset({"process_entity", "affective_term"})

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


class GenerationError(RuntimeError):
    """Raised when a frozen, reproducible export cannot be produced."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(*parts: str) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sql_literal(value: str) -> str:
    if "\x00" in value:
        raise GenerationError("PostgreSQL text literals cannot contain NUL")
    return "'" + value.replace("'", "''") + "'"


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def run_json_query(
    *,
    psql_path: str,
    database: str,
    select_sql: str,
    timeout_seconds: int,
) -> list[dict[str, Any]]:
    """Run one SELECT in a repeatable-read, read-only psql transaction."""

    transaction_sql = f"""
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = {sql_literal(str(timeout_seconds) + 's')};
{select_sql.rstrip().rstrip(';')};
COMMIT;
"""
    command = [
        psql_path,
        "-X",
        "--quiet",
        "--tuples-only",
        "--no-align",
        "--set=ON_ERROR_STOP=1",
        f"--dbname={database}",
    ]
    try:
        completed = subprocess.run(
            command,
            input=transaction_sql,
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds + 30,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise GenerationError(
            f"read-only PostgreSQL query exceeded {timeout_seconds + 30}s"
        ) from error

    if completed.returncode != 0:
        diagnostic = completed.stderr.strip() or "psql returned no diagnostic"
        raise GenerationError(f"read-only PostgreSQL query failed: {diagnostic}")

    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(completed.stdout.splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as error:
            raise GenerationError(
                f"psql emitted non-JSON output at line {line_number}"
            ) from error
        if not isinstance(parsed, dict):
            raise GenerationError(
                f"psql JSON row {line_number} is not an object"
            )
        rows.append(parsed)
    return rows


def metadata_sql(
    snapshot_key: str,
    pipeline_key: str,
    derivation_run_key: str | None,
) -> str:
    derivation_filter = ""
    if derivation_run_key:
        derivation_filter = (
            "\n  AND derivation.normalization_derivation_run_key = "
            + sql_literal(derivation_run_key)
        )
    return f"""
SELECT jsonb_build_object(
    'server_version_num', current_setting('server_version_num')::INTEGER,
    'server_version', current_setting('server_version'),
    'pg_trgm_version', (
        SELECT extension.extversion
        FROM pg_extension AS extension
        WHERE extension.extname = 'pg_trgm'
    ),
    'corpus_snapshot_key', snapshot.corpus_snapshot_key,
    'corpus_version', snapshot.corpus_version,
    'snapshot_frozen', snapshot.frozen_at IS NOT NULL,
    'snapshot_code_commit_sha', snapshot.code_commit_sha,
    'expected_document_count', snapshot.expected_document_count,
    'expected_observation_count', snapshot.expected_observation_count,
    'expected_normalized_expression_count',
        snapshot.expected_normalized_expression_count,
    'normalization_pipeline_key', pipeline.normalization_pipeline_key,
    'language_tag_code', pipeline.language_tag_code,
    'pipeline_frozen', pipeline.frozen_at IS NOT NULL,
    'normalization_derivation_run_key',
        derivation.normalization_derivation_run_key,
    'derivation_frozen', derivation.frozen_at IS NOT NULL,
    'derivation_code_commit_sha', derivation.code_commit_sha,
    'output_occurrence_count', derivation.output_occurrence_count,
    'stored_occurrence_count', (
        SELECT count(*)::BIGINT
        FROM corpus.normalized_expression_occurrence AS occurrence
        WHERE occurrence.normalization_derivation_run_id =
              derivation.normalization_derivation_run_id
    ),
    'stored_unique_normalized_expression_count', (
        SELECT count(DISTINCT occurrence.normalized_expression_id)::BIGINT
        FROM corpus.normalized_expression_occurrence AS occurrence
        WHERE occurrence.normalization_derivation_run_id =
              derivation.normalization_derivation_run_id
    )
)::TEXT
FROM corpus.corpus_snapshot AS snapshot
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id = snapshot.normalization_pipeline_id
JOIN corpus.normalization_derivation_run AS derivation
  ON derivation.corpus_snapshot_id = snapshot.corpus_snapshot_id
 AND derivation.normalization_pipeline_id = pipeline.normalization_pipeline_id
WHERE snapshot.corpus_snapshot_key = {sql_literal(snapshot_key)}
  AND pipeline.normalization_pipeline_key = {sql_literal(pipeline_key)}
{derivation_filter}
ORDER BY derivation.normalization_derivation_run_key
"""


def universe_sql(
    derivation_run_key: str,
    pipeline_key: str,
    language_tag_code: str,
    trigram_threshold: float,
) -> str:
    return f"""
WITH occurrence_row AS (
    SELECT
        normalized.normalized_expression_id,
        normalized.normalized_expression_key,
        normalized.normalized_text,
        expression.expression_id,
        expression.expression_key,
        expression.expression_text,
        observation_expression.observation_expression_key,
        raw_observation.captured_document_id
    FROM corpus.normalized_expression_occurrence AS occurrence
    JOIN corpus.normalization_derivation_run AS derivation
      ON derivation.normalization_derivation_run_id =
         occurrence.normalization_derivation_run_id
    JOIN corpus.normalized_expression AS normalized
      ON normalized.normalized_expression_id =
         occurrence.normalized_expression_id
     AND normalized.normalization_pipeline_id =
         occurrence.normalization_pipeline_id
    JOIN corpus.observation_expression AS observation_expression
      ON observation_expression.observation_expression_id =
         occurrence.observation_expression_id
    JOIN kb.lexical_expression AS expression
      ON expression.expression_id = observation_expression.expression_id
    JOIN corpus.raw_observation AS raw_observation
      ON raw_observation.raw_observation_id =
         observation_expression.raw_observation_id
    WHERE derivation.normalization_derivation_run_key =
          {sql_literal(derivation_run_key)}
),
surface_rollup AS (
    SELECT
        row.normalized_expression_id,
        row.normalized_expression_key,
        row.normalized_text,
        row.expression_id,
        row.expression_key,
        row.expression_text,
        count(*)::BIGINT AS surface_occurrence_count
    FROM occurrence_row AS row
    GROUP BY
        row.normalized_expression_id,
        row.normalized_expression_key,
        row.normalized_text,
        row.expression_id,
        row.expression_key,
        row.expression_text
),
ranked_surface AS (
    SELECT
        surface.*,
        row_number() OVER (
            PARTITION BY surface.normalized_expression_id
            ORDER BY
                surface.surface_occurrence_count DESC,
                encode(
                    sha256(convert_to(surface.expression_key, 'UTF8')),
                    'hex'
                ),
                surface.expression_key
        ) AS surface_rank
    FROM surface_rollup AS surface
),
representative_observation AS (
    SELECT DISTINCT ON (
        row.normalized_expression_id,
        row.expression_id
    )
        row.normalized_expression_id,
        row.expression_id,
        row.observation_expression_key
    FROM occurrence_row AS row
    ORDER BY
        row.normalized_expression_id,
        row.expression_id,
        encode(
            sha256(
                convert_to(row.observation_expression_key, 'UTF8')
            ),
            'hex'
        ),
        row.observation_expression_key
),
identity_rollup AS (
    SELECT
        row.normalized_expression_id,
        count(*)::BIGINT AS occurrence_count,
        count(DISTINCT row.captured_document_id)::BIGINT AS document_count
    FROM occurrence_row AS row
    GROUP BY row.normalized_expression_id
),
universe AS (
    SELECT
        surface.normalized_expression_id,
        surface.normalized_expression_key,
        surface.normalized_text,
        surface.expression_key,
        surface.expression_text,
        representative.observation_expression_key,
        identity.occurrence_count,
        identity.document_count
    FROM ranked_surface AS surface
    JOIN identity_rollup AS identity
      ON identity.normalized_expression_id =
         surface.normalized_expression_id
    JOIN representative_observation AS representative
      ON representative.normalized_expression_id =
         surface.normalized_expression_id
     AND representative.expression_id = surface.expression_id
    WHERE surface.surface_rank = 1
),
canonical_dictionary AS (
    SELECT DISTINCT normalized.normalized_text
    FROM corpus.normalized_expression AS normalized
    JOIN corpus.normalization_pipeline AS pipeline
      ON pipeline.normalization_pipeline_id =
         normalized.normalization_pipeline_id
    JOIN corpus.lexical_expression_normalization AS normalization
      ON normalization.normalization_pipeline_id =
         pipeline.normalization_pipeline_id
     AND normalization.normalized_expression_id =
         normalized.normalized_expression_id
    JOIN kb.lexical_expression AS expression
      ON expression.expression_id = normalization.expression_id
     AND expression.lifecycle_status_code = 'active'
     AND expression.language_tag_code = pipeline.language_tag_code
    JOIN kb.lexicalization AS lexicalization
      ON lexicalization.expression_id = expression.expression_id
     AND lexicalization.lifecycle_status_code = 'active'
     AND lexicalization.valid_from <= CURRENT_TIMESTAMP
     AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
         )
    JOIN ref.mapping_type AS mapping_type
      ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
     AND (mapping_type.is_preferred OR mapping_type.is_approved_variant)
    JOIN kb.concept AS concept
      ON concept.concept_id = lexicalization.concept_id
     AND concept.lifecycle_status_code = 'active'
    WHERE pipeline.normalization_pipeline_key = {sql_literal(pipeline_key)}
)
SELECT jsonb_build_object(
    'normalized_expression_key', universe.normalized_expression_key,
    'normalized_text', universe.normalized_text,
    'representative_expression_key', universe.expression_key,
    'representative_expression_text', universe.expression_text,
    'representative_observation_expression_key',
        universe.observation_expression_key,
    'occurrence_count', universe.occurrence_count,
    'document_count', universe.document_count,
    'maximum_canonical_trigram_similarity', nearest.maximum_similarity,
    'retrieval_results', jsonb_agg(
        jsonb_build_object(
            'retrieval_status_code', retrieval.retrieval_status_code,
            'candidate_rank', retrieval.candidate_rank,
            'retrieval_tier_code', retrieval.retrieval_tier_code,
            'tier_order', retrieval.tier_order,
            'concept_key', retrieval.concept_key,
            'concept_type_code', retrieval.concept_type_code,
            'relation_type_code', retrieval.relation_type_code,
            'traversal_direction', retrieval.traversal_direction
        )
        ORDER BY retrieval.candidate_rank NULLS LAST
    )
)::TEXT
FROM universe
CROSS JOIN LATERAL ml.retrieve_deterministic_candidates(
    universe.expression_text,
    {sql_literal(language_tag_code)},
    {sql_literal(pipeline_key)},
    'D',
    {RETRIEVAL_TOP_K},
    {trigram_threshold}::REAL
) AS retrieval
CROSS JOIN LATERAL (
    SELECT max(
        similarity(dictionary.normalized_text, universe.normalized_text)
    )::REAL AS maximum_similarity
    FROM canonical_dictionary AS dictionary
) AS nearest
GROUP BY
    universe.normalized_expression_id,
    universe.normalized_expression_key,
    universe.normalized_text,
    universe.expression_key,
    universe.expression_text,
    universe.observation_expression_key,
    universe.occurrence_count,
    universe.document_count,
    nearest.maximum_similarity
ORDER BY universe.normalized_expression_key
"""


def candidate_pool_sql(
    selected_cases: Sequence[Mapping[str, Any]],
    pipeline_key: str,
    language_tag_code: str,
    trigram_threshold: float,
) -> str:
    values: list[str] = []
    for case in selected_cases:
        values.append(
            "(" + ", ".join(
                (
                    sql_literal(str(case["audit_case_key"])),
                    sql_literal(str(case["audit_split_code"])),
                    sql_literal(str(case["normalized_expression_key"])),
                    sql_literal(str(case["representative_expression_text"])),
                    str(int(case["selection_ordinal"])),
                )
            ) + ")"
        )
    values_sql = ",\n        ".join(values)
    return f"""
WITH selected_case(
    audit_case_key,
    audit_split_code,
    normalized_expression_key,
    query_text,
    selection_ordinal
) AS (
    VALUES
        {values_sql}
),
baseline(retrieval_baseline_code, baseline_order) AS (
    VALUES
        ('A'::TEXT, 1),
        ('B', 2),
        ('C', 3),
        ('D', 4)
)
SELECT jsonb_build_object(
    'audit_case_key', selected.audit_case_key,
    'audit_split_code', selected.audit_split_code,
    'normalized_expression_key', selected.normalized_expression_key,
    'selection_ordinal', selected.selection_ordinal,
    'retrieval_baseline_code', baseline.retrieval_baseline_code,
    'baseline_order', baseline.baseline_order,
    'retrieval_status_code', retrieval.retrieval_status_code,
    'candidate_rank', retrieval.candidate_rank,
    'retrieval_tier_code', retrieval.retrieval_tier_code,
    'tier_order', retrieval.tier_order,
    'matched_expression_key', retrieval.matched_expression_key,
    'concept_key', retrieval.concept_key,
    'concept_type_code', retrieval.concept_type_code,
    'seed_concept_key', retrieval.seed_concept_key,
    'relation_type_code', retrieval.relation_type_code,
    'traversal_direction', retrieval.traversal_direction,
    'signal_ledger', retrieval.signal_ledger
)::TEXT
FROM selected_case AS selected
CROSS JOIN baseline
CROSS JOIN LATERAL ml.retrieve_deterministic_candidates(
    selected.query_text,
    {sql_literal(language_tag_code)},
    {sql_literal(pipeline_key)},
    baseline.retrieval_baseline_code,
    {RETRIEVAL_TOP_K},
    {trigram_threshold}::REAL
) AS retrieval
WHERE retrieval.concept_id IS NOT NULL
ORDER BY
    selected.selection_ordinal,
    baseline.baseline_order,
    retrieval.candidate_rank,
    retrieval.concept_key
"""


def scaled_stratum_targets(target_size: int) -> dict[str, int]:
    if target_size == DEFAULT_TARGET_SIZE:
        return dict(DEFAULT_STRATUM_TARGETS)

    floors: dict[str, int] = {}
    remainders: list[tuple[int, str]] = []
    allocated = 0
    for stratum in STRATUM_ORDER:
        numerator = DEFAULT_STRATUM_TARGETS[stratum] * target_size
        floor_value, remainder = divmod(numerator, DEFAULT_TARGET_SIZE)
        floors[stratum] = floor_value
        allocated += floor_value
        remainders.append((remainder, stratum))

    remaining = target_size - allocated
    remainders.sort(
        key=lambda item: (
            -item[0],
            sha256_text(SELECTION_POLICY_VERSION, "quota", item[1]),
        )
    )
    for _, stratum in remainders[:remaining]:
        floors[stratum] += 1
    return floors


def classify_universe_row(
    row: Mapping[str, Any], hard_negative_floor: float
) -> tuple[str, list[str]]:
    results = row.get("retrieval_results")
    if not isinstance(results, list) or not results:
        raise GenerationError("universe row lacks deterministic retrieval results")

    tier_codes = {
        result.get("retrieval_tier_code")
        for result in results
        if result.get("retrieval_tier_code") is not None
    }
    direct_results = [
        result
        for result in results
        if result.get("retrieval_tier_code") in {"A", "B", "C"}
    ]
    direct_types = {
        result.get("concept_type_code")
        for result in direct_results
        if result.get("concept_type_code")
    }
    stratum_codes: set[str] = set()

    unresolved = all(
        result.get("retrieval_status_code") == "UNRESOLVED"
        for result in results
    )
    if unresolved:
        maximum_similarity = row.get("maximum_canonical_trigram_similarity")
        if (
            maximum_similarity is not None
            and float(maximum_similarity) >= hard_negative_floor
        ):
            stratum_codes.add("hard_negative")
            return "hard_negative", ["hard_negative"]
        stratum_codes.add("unresolved")
        return "unresolved", ["unresolved"]

    if "A" in tier_codes:
        stratum_codes.add("exact")
    if "B" in tier_codes:
        stratum_codes.add("variant")
    if "C" in tier_codes:
        stratum_codes.add("orthographic_difficulty")
    if "D" in tier_codes:
        stratum_codes.add("graph_reference")
    if (
        "qualifier" in direct_types
        or str(row["normalized_text"]) in MODIFIER_PROBES
        or len({result.get("concept_key") for result in direct_results}) > 1
    ):
        stratum_codes.add("qualifier_polysemy")
    if direct_types & NON_DESCRIPTIVE_TYPES:
        stratum_codes.add("non_descriptive_language")

    primary_priority = (
        "non_descriptive_language",
        "qualifier_polysemy",
        "variant",
        "orthographic_difficulty",
        "graph_reference",
        "exact",
    )
    for primary in primary_priority:
        if primary in stratum_codes:
            ordered = [code for code in STRATUM_ORDER if code in stratum_codes]
            return primary, ordered

    raise GenerationError(
        "resolved retrieval row could not be assigned a declared sampling stratum"
    )


def select_cases(
    *,
    universe_rows: Sequence[dict[str, Any]],
    metadata: Mapping[str, Any],
    target_size: int,
    development_size: int,
    hard_negative_floor: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(universe_rows) < target_size:
        raise GenerationError(
            "frozen derivation has only "
            f"{len(universe_rows)} actual normalized expressions; "
            f"target is {target_size}; synthetic padding is prohibited"
        )

    seen_keys: set[str] = set()
    classified: list[dict[str, Any]] = []
    for source_row in universe_rows:
        normalized_key = str(source_row["normalized_expression_key"])
        if normalized_key in seen_keys:
            raise GenerationError(
                f"duplicate normalized expression identity: {normalized_key}"
            )
        seen_keys.add(normalized_key)
        primary, strata = classify_universe_row(
            source_row, hard_negative_floor
        )
        row = dict(source_row)
        row["primary_stratum_code"] = primary
        row["stratum_codes"] = strata
        row["selection_sha256"] = sha256_text(
            SELECTION_POLICY_VERSION,
            str(metadata["corpus_snapshot_key"]),
            normalized_key,
        )
        classified.append(row)

    classified.sort(
        key=lambda row: (
            row["selection_sha256"],
            row["normalized_expression_key"],
        )
    )
    stratum_targets = scaled_stratum_targets(target_size)
    selected_keys: set[str] = set()
    selected: list[dict[str, Any]] = []
    availability: dict[str, int] = {}

    for stratum in STRATUM_ORDER:
        candidates = [
            row
            for row in classified
            if row["primary_stratum_code"] == stratum
        ]
        availability[stratum] = len(candidates)
        for row in candidates[: stratum_targets[stratum]]:
            selected.append(row)
            selected_keys.add(str(row["normalized_expression_key"]))

    for row in classified:
        if len(selected) >= target_size:
            break
        normalized_key = str(row["normalized_expression_key"])
        if normalized_key not in selected_keys:
            selected.append(row)
            selected_keys.add(normalized_key)

    if len(selected) != target_size:
        raise GenerationError(
            f"selected {len(selected)} rows after backfill; expected {target_size}"
        )

    selected.sort(
        key=lambda row: (
            row["selection_sha256"],
            row["normalized_expression_key"],
        )
    )
    for ordinal, row in enumerate(selected, 1):
        row["selection_ordinal"] = ordinal
        row["audit_case_key"] = "audit_case.round2b.sha256_" + sha256_text(
            SELECTION_POLICY_VERSION,
            str(metadata["corpus_snapshot_key"]),
            str(row["normalized_expression_key"]),
        )

    selected_by_stratum: dict[str, list[dict[str, Any]]] = {
        stratum: [] for stratum in STRATUM_ORDER
    }
    for row in selected:
        selected_by_stratum[str(row["primary_stratum_code"])].append(row)

    development_quota: dict[str, int] = {}
    remainders: list[tuple[int, str]] = []
    allocated_development = 0
    for stratum in STRATUM_ORDER:
        count = len(selected_by_stratum[stratum])
        floor_value, remainder = divmod(
            count * development_size, target_size
        )
        development_quota[stratum] = floor_value
        allocated_development += floor_value
        remainders.append((remainder, stratum))

    remaining_development = development_size - allocated_development
    remainders.sort(
        key=lambda item: (
            -item[0],
            sha256_text(SELECTION_POLICY_VERSION, "split-quota", item[1]),
        )
    )
    for _, stratum in remainders[:remaining_development]:
        development_quota[stratum] += 1

    for stratum in STRATUM_ORDER:
        rows = selected_by_stratum[stratum]
        rows.sort(
            key=lambda row: (
                sha256_text(
                    SELECTION_POLICY_VERSION,
                    "split",
                    str(row["audit_case_key"]),
                ),
                row["normalized_expression_key"],
            )
        )
        for position, row in enumerate(rows):
            row["audit_split_code"] = (
                "development"
                if position < development_quota[stratum]
                else "held_out"
            )

    split_ordinals = {"development": 0, "held_out": 0}
    for row in selected:
        split = str(row["audit_split_code"])
        split_ordinals[split] += 1
        row["split_ordinal"] = split_ordinals[split]

    if split_ordinals["development"] != development_size:
        raise GenerationError("stratified development allocation is not exact")
    if split_ordinals["held_out"] != target_size - development_size:
        raise GenerationError("stratified held-out allocation is not exact")

    selected_distribution = {
        stratum: len(selected_by_stratum[stratum])
        for stratum in STRATUM_ORDER
    }
    quota_shortfalls = {
        stratum: max(
            stratum_targets[stratum] - availability[stratum],
            0,
        )
        for stratum in STRATUM_ORDER
    }
    selection_receipt = {
        "available_unique_normalized_expression_count": len(universe_rows),
        "stratum_availability": availability,
        "stratum_targets": stratum_targets,
        "stratum_target_shortfalls": quota_shortfalls,
        "selected_primary_stratum_distribution": selected_distribution,
        "development_quota_by_primary_stratum": development_quota,
        "development_count": split_ordinals["development"],
        "held_out_count": split_ordinals["held_out"],
    }
    return selected, selection_receipt


def materialize_case_rows(
    selected_cases: Sequence[Mapping[str, Any]],
    metadata: Mapping[str, Any],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for case in selected_cases:
        split = str(case["audit_split_code"])
        rows.append(
            {
                "selection_policy_version": SELECTION_POLICY_VERSION,
                "audit_case_key": str(case["audit_case_key"]),
                "corpus_snapshot_key": str(metadata["corpus_snapshot_key"]),
                "normalization_derivation_run_key": str(
                    metadata["normalization_derivation_run_key"]
                ),
                "normalization_pipeline_key": str(
                    metadata["normalization_pipeline_key"]
                ),
                "language_tag_code": str(metadata["language_tag_code"]),
                "normalized_expression_key": str(
                    case["normalized_expression_key"]
                ),
                "normalized_text": str(case["normalized_text"]),
                "representative_expression_key": str(
                    case["representative_expression_key"]
                ),
                "representative_expression_text": str(
                    case["representative_expression_text"]
                ),
                "representative_observation_expression_key": str(
                    case["representative_observation_expression_key"]
                ),
                "occurrence_count": str(int(case["occurrence_count"])),
                "document_count": str(int(case["document_count"])),
                "primary_stratum_code": str(
                    case["primary_stratum_code"]
                ),
                "stratum_codes_json": canonical_json(case["stratum_codes"]),
                "audit_split_code": split,
                "selection_ordinal": str(int(case["selection_ordinal"])),
                "split_ordinal": str(int(case["split_ordinal"])),
                "selection_sha256": str(case["selection_sha256"]),
                "tuning_eligible": bool_text(split == "development"),
                "reviewer_addition_allowed": "true",
                "adjudication_state": "unreviewed",
            }
        )
    return rows


def materialize_candidate_rows(
    retrieval_rows: Sequence[Mapping[str, Any]],
    selected_cases: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    case_by_key = {
        str(case["audit_case_key"]): case for case in selected_cases
    }
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for retrieval in retrieval_rows:
        case_key = str(retrieval["audit_case_key"])
        if case_key not in case_by_key:
            raise GenerationError(
                f"candidate pool references unknown case {case_key}"
            )
        concept_key = retrieval.get("concept_key")
        if not concept_key:
            raise GenerationError("candidate query emitted a conceptless row")
        grouped.setdefault((case_key, str(concept_key)), []).append(retrieval)

    rows: list[dict[str, str]] = []
    cases_with_candidates: set[str] = set()
    for (case_key, concept_key), records in grouped.items():
        records = sorted(
            records,
            key=lambda record: (
                int(record["tier_order"]),
                int(record["candidate_rank"]),
                int(record["baseline_order"]),
                str(record["retrieval_baseline_code"]),
            ),
        )
        best = records[0]
        case = case_by_key[case_key]
        baselines = sorted(
            {str(record["retrieval_baseline_code"]) for record in records},
            key=lambda code: "ABCD".index(code),
        )
        baseline_ranks = {
            str(record["retrieval_baseline_code"]): int(
                record["candidate_rank"]
            )
            for record in sorted(
                records,
                key=lambda item: int(item["baseline_order"]),
            )
        }
        status_codes = sorted(
            {str(record["retrieval_status_code"]) for record in records}
        )
        matched_expressions = sorted(
            {
                str(record["matched_expression_key"])
                for record in records
                if record.get("matched_expression_key")
            }
        )
        ledger_by_baseline = [
            {
                "retrieval_baseline_code": str(
                    record["retrieval_baseline_code"]
                ),
                "candidate_rank": int(record["candidate_rank"]),
                "retrieval_tier_code": str(record["retrieval_tier_code"]),
                "signal_ledger": record["signal_ledger"],
                "seed_concept_key": record.get("seed_concept_key"),
                "relation_type_code": record.get("relation_type_code"),
                "traversal_direction": record.get("traversal_direction"),
            }
            for record in sorted(
                records,
                key=lambda item: (
                    int(item["baseline_order"]),
                    int(item["candidate_rank"]),
                ),
            )
        ]
        candidate_key = "audit_candidate.round2b.sha256_" + sha256_text(
            SELECTION_POLICY_VERSION,
            case_key,
            concept_key,
            "deterministic_retrieval",
        )
        rows.append(
            {
                "candidate_pool_key": candidate_key,
                "audit_case_key": case_key,
                "audit_split_code": str(case["audit_split_code"]),
                "normalized_expression_key": str(
                    case["normalized_expression_key"]
                ),
                "concept_key": concept_key,
                "concept_type_code": str(best["concept_type_code"]),
                "candidate_source_code": "deterministic_retrieval",
                "retrieved_by_baselines_json": canonical_json(baselines),
                "baseline_ranks_json": canonical_json(baseline_ranks),
                "best_retrieval_tier_code": str(
                    best["retrieval_tier_code"]
                ),
                "best_tier_order": str(int(best["tier_order"])),
                "best_candidate_rank": str(int(best["candidate_rank"])),
                "retrieval_status_codes_json": canonical_json(status_codes),
                "matched_expression_keys_json": canonical_json(
                    matched_expressions
                ),
                "signal_ledger_by_baseline_json": canonical_json(
                    ledger_by_baseline
                ),
                "reviewer_added_by": "",
                "reviewer_added_at": "",
                "reviewer_addition_rationale": "",
            }
        )
        cases_with_candidates.add(case_key)

    selection_order = {
        str(case["audit_case_key"]): int(case["selection_ordinal"])
        for case in selected_cases
    }
    rows.sort(
        key=lambda row: (
            selection_order[row["audit_case_key"]],
            int(row["best_tier_order"]),
            int(row["best_candidate_rank"]),
            row["concept_key"],
        )
    )

    expected_candidate_cases = {
        str(case["audit_case_key"])
        for case in selected_cases
        if not all(
            result.get("retrieval_status_code") == "UNRESOLVED"
            for result in case["retrieval_results"]
        )
    }
    missing_candidate_cases = expected_candidate_cases - cases_with_candidates
    if missing_candidate_cases:
        raise GenerationError(
            "pooled retrieval lost candidates for cases: "
            + ", ".join(sorted(missing_candidate_cases)[:5])
        )

    receipt = {
        "candidate_pool_row_count": len(rows),
        "cases_with_deterministic_candidates": len(cases_with_candidates),
        "cases_without_deterministic_candidates": (
            len(selected_cases) - len(cases_with_candidates)
        ),
        "retrieval_baselines": ["A", "B", "C", "D"],
        "top_k_per_baseline": RETRIEVAL_TOP_K,
        "candidate_source_codes_emitted": ["deterministic_retrieval"],
        "reviewer_added_candidate_contract": {
            "allowed": True,
            "candidate_source_code": "reviewer_added",
            "requires_existing_audit_case_key": True,
            "requires_existing_concept_key": True,
            "relevance_judgment_belongs_in_separate_review_data": True,
        },
    }
    return rows, receipt


def write_tsv_atomic(
    path: Path,
    headers: Sequence[str],
    rows: Iterable[Mapping[str, str]],
    overwrite: bool,
) -> None:
    if path.exists() and not overwrite:
        raise GenerationError(
            f"refusing to overwrite existing export without --overwrite: {path}"
        )
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise GenerationError(
            f"private audit output parent is not a real directory: {path.parent}"
        )
    os.chmod(path.parent, 0o700)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            writer = csv.DictWriter(
                handle,
                fieldnames=list(headers),
                delimiter="\t",
                lineterminator="\n",
                extrasaction="raise",
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            handle.flush()
            os.fchmod(handle.fileno(), 0o600)
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def dry_run_receipt(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": "dry_run",
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "database_queries_executed": False,
        "database_writes": False,
        "files_written": False,
        "corpus_snapshot_key": args.snapshot_key,
        "normalization_pipeline_key": args.pipeline_key,
        "target_case_count": args.target_size,
        "development_case_count": args.development_size,
        "held_out_case_count": args.target_size - args.development_size,
        "stratum_targets": scaled_stratum_targets(args.target_size),
        "case_headers": list(CASE_HEADERS),
        "candidate_pool_headers": list(CANDIDATE_HEADERS),
        "retrieval_baselines": ["A", "B", "C", "D"],
        "top_k_per_baseline": RETRIEVAL_TOP_K,
        "synthetic_padding_allowed": False,
        "judgments_emitted": False,
        "audit_set_frozen": False,
        "held_out_tuning_eligible": False,
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Select actual frozen corpus expressions and export an unjudged "
            "A-D deterministic retrieval audit pool."
        )
    )
    parser.add_argument(
        "--database",
        help=(
            "libpq database name or URI for psql. Required unless --dry-run; "
            "PGHOST/PGPORT/PGUSER/PGPASSWORD remain supported."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="directory for audit_cases.tsv and audit_candidate_pool.tsv",
    )
    parser.add_argument("--snapshot-key", default=DEFAULT_SNAPSHOT_KEY)
    parser.add_argument("--pipeline-key", default=DEFAULT_PIPELINE_KEY)
    parser.add_argument(
        "--derivation-run-key",
        help=(
            "frozen normalization run key; optional only when the snapshot "
            "has exactly one matching frozen run"
        ),
    )
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    parser.add_argument(
        "--development-size", type=int, default=DEFAULT_DEVELOPMENT_SIZE
    )
    parser.add_argument(
        "--trigram-threshold",
        type=float,
        default=DEFAULT_TRIGRAM_THRESHOLD,
    )
    parser.add_argument(
        "--hard-negative-floor",
        type=float,
        default=DEFAULT_HARD_NEGATIVE_FLOOR,
    )
    parser.add_argument(
        "--statement-timeout-seconds", type=int, default=300
    )
    parser.add_argument("--psql", help="explicit psql executable")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the static contract without querying PostgreSQL or writing files",
    )
    args = parser.parse_args(argv)

    if args.target_size <= 0:
        parser.error("--target-size must be positive")
    if args.development_size < 0 or args.development_size > args.target_size:
        parser.error("--development-size must be between zero and target size")
    if not 0 <= args.trigram_threshold <= 1:
        parser.error("--trigram-threshold must be between zero and one")
    if not 0 <= args.hard_negative_floor < args.trigram_threshold:
        parser.error(
            "--hard-negative-floor must be nonnegative and below the trigram threshold"
        )
    if args.statement_timeout_seconds <= 0:
        parser.error("--statement-timeout-seconds must be positive")
    if not args.dry_run and not args.database:
        parser.error("--database is required unless --dry-run")
    if not args.dry_run and args.output_dir is None:
        parser.error("--output-dir is required unless --dry-run")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.dry_run:
        print(json.dumps(dry_run_receipt(args), indent=2, sort_keys=True))
        return 0

    psql_path = args.psql or shutil.which("psql")
    if not psql_path:
        raise GenerationError("psql is required")

    metadata_rows = run_json_query(
        psql_path=psql_path,
        database=args.database,
        select_sql=metadata_sql(
            args.snapshot_key,
            args.pipeline_key,
            args.derivation_run_key,
        ),
        timeout_seconds=args.statement_timeout_seconds,
    )
    if not metadata_rows:
        raise GenerationError(
            "snapshot, pipeline, and frozen derivation selection returned no rows"
        )
    if len(metadata_rows) != 1:
        run_keys = sorted(
            str(row["normalization_derivation_run_key"])
            for row in metadata_rows
        )
        raise GenerationError(
            "snapshot has multiple matching derivations; pass "
            f"--derivation-run-key explicitly: {', '.join(run_keys)}"
        )
    metadata = metadata_rows[0]
    if int(metadata["server_version_num"]) < 170000:
        raise GenerationError("PostgreSQL 17 or newer is required")
    if not metadata.get("pg_trgm_version"):
        raise GenerationError("pg_trgm is required")
    if not metadata.get("snapshot_frozen"):
        raise GenerationError("corpus snapshot must be frozen")
    if not metadata.get("pipeline_frozen"):
        raise GenerationError("normalization pipeline must be frozen")
    if not metadata.get("derivation_frozen"):
        raise GenerationError("normalization derivation must be frozen")
    if int(metadata["stored_occurrence_count"]) != int(
        metadata["output_occurrence_count"]
    ):
        raise GenerationError(
            "stored occurrence count differs from the frozen derivation receipt"
        )

    universe_rows = run_json_query(
        psql_path=psql_path,
        database=args.database,
        select_sql=universe_sql(
            str(metadata["normalization_derivation_run_key"]),
            str(metadata["normalization_pipeline_key"]),
            str(metadata["language_tag_code"]),
            args.trigram_threshold,
        ),
        timeout_seconds=args.statement_timeout_seconds,
    )
    if len(universe_rows) != int(
        metadata["stored_unique_normalized_expression_count"]
    ):
        raise GenerationError(
            "audit universe does not close over the frozen normalized occurrence inventory"
        )

    selected_cases, selection_receipt = select_cases(
        universe_rows=universe_rows,
        metadata=metadata,
        target_size=args.target_size,
        development_size=args.development_size,
        hard_negative_floor=args.hard_negative_floor,
    )
    retrieval_rows = run_json_query(
        psql_path=psql_path,
        database=args.database,
        select_sql=candidate_pool_sql(
            selected_cases,
            str(metadata["normalization_pipeline_key"]),
            str(metadata["language_tag_code"]),
            args.trigram_threshold,
        ),
        timeout_seconds=args.statement_timeout_seconds,
    )

    case_rows = materialize_case_rows(selected_cases, metadata)
    candidate_rows, candidate_receipt = materialize_candidate_rows(
        retrieval_rows, selected_cases
    )
    if len(case_rows) != args.target_size:
        raise GenerationError("materialized case count differs from target")
    if any(row["adjudication_state"] != "unreviewed" for row in case_rows):
        raise GenerationError("generator attempted to emit adjudication state")
    if any(
        row["audit_split_code"] == "held_out"
        and row["tuning_eligible"] != "false"
        for row in case_rows
    ):
        raise GenerationError("held-out case was marked tuning eligible")

    output_dir = args.output_dir.resolve()
    case_path = output_dir / "audit_cases.tsv"
    candidate_path = output_dir / "audit_candidate_pool.tsv"
    write_tsv_atomic(case_path, CASE_HEADERS, case_rows, args.overwrite)
    write_tsv_atomic(
        candidate_path,
        CANDIDATE_HEADERS,
        candidate_rows,
        args.overwrite,
    )

    receipt = {
        "status": "generated",
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "database_writes": False,
        "judgments_emitted": False,
        "audit_set_frozen": False,
        "synthetic_padding_used": False,
        "corpus_snapshot_key": metadata["corpus_snapshot_key"],
        "corpus_version": metadata["corpus_version"],
        "normalization_derivation_run_key": metadata[
            "normalization_derivation_run_key"
        ],
        "normalization_pipeline_key": metadata[
            "normalization_pipeline_key"
        ],
        "server_version": metadata["server_version"],
        "pg_trgm_version": metadata["pg_trgm_version"],
        "trigram_threshold": args.trigram_threshold,
        "hard_negative_floor": args.hard_negative_floor,
        "selection": selection_receipt,
        "candidate_pool": candidate_receipt,
        "artifacts": {
            "audit_cases.tsv": {
                "row_count": len(case_rows),
                "sha256": sha256_file(case_path),
            },
            "audit_candidate_pool.tsv": {
                "row_count": len(candidate_rows),
                "sha256": sha256_file(candidate_path),
            },
        },
        "held_out_policy": {
            "case_count": args.target_size - args.development_size,
            "tuning_eligible": False,
            "labels_exported": False,
            "candidate_pool_is_not_a_judgment": True,
        },
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as error:
        print(f"audit generation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
