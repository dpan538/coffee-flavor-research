#!/usr/bin/env python3
"""Deterministic high-dimensional descriptor features for R9 semantic analysis."""

from __future__ import annotations

from collections import Counter
import statistics
from typing import Any

import audit_output_quality_r9 as quality
from output_policy_r9 import NAMED_DESCRIPTOR, PROFILE_DIRECTION

EVIDENCE_CLASSES = (
    "EXPLICIT_USER_EXPRESSION",
    "SUPPORTED_DIRECTION_ONLY",
    "NO_DIRECT_USER_ANSWER_TRACE",
)


def registered_dimensions(registry: dict[str, Any]) -> list[str]:
    return sorted(
        {
            dimension_id
            for entry in registry.values()
            if entry["role"] == PROFILE_DIRECTION
            for dimension_id in entry["support_dimension_ids"]
        }
    )


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def build_descriptor_features(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    dimensions = registered_dimensions(registry)
    named_ids = sorted(
        candidate_id
        for candidate_id, entry in registry.items()
        if entry["role"] == NAMED_DESCRIPTOR
    )
    evidence_by_descriptor: dict[str, list[dict[str, Any]]] = {
        candidate_id: [] for candidate_id in named_ids
    }
    for source in sources:
        for row in quality.evidence_rows(source, registry):
            evidence_by_descriptor[row["descriptor_id"]].append(row)

    rows = []
    for candidate_id in named_ids:
        descriptor_dimensions = set(registry[candidate_id]["support_dimension_ids"])
        evidence = evidence_by_descriptor[candidate_id]
        evidence_counts = Counter(row["evidence_class"] for row in evidence)
        other_jaccards = [
            jaccard(
                descriptor_dimensions,
                set(registry[other_id]["support_dimension_ids"]),
            )
            for other_id in named_ids
            if other_id != candidate_id
        ]
        occurrence_count = len(evidence)
        rows.append(
            {
                "descriptor_id": candidate_id,
                "role": NAMED_DESCRIPTOR,
                "registered_level": (
                    "EVIDENCE_QUALIFIED_MIDDLE_CATEGORY"
                    if candidate_id in quality.MIDDLE_NAMED_IDS
                    else "NAMED_DESCRIPTOR_LEVEL_NOT_FURTHER_INFERRED"
                ),
                "support_dimension_ids": sorted(descriptor_dimensions),
                "dimension_vector": {
                    dimension_id: int(dimension_id in descriptor_dimensions)
                    for dimension_id in dimensions
                },
                "dimension_membership_count": len(descriptor_dimensions),
                "output_occurrences": occurrence_count,
                "main_occurrences": sum(row["panel"] == "main" for row in evidence),
                "secondary_occurrences": sum(
                    row["panel"] == "secondary" for row in evidence
                ),
                "evidence_class_counts": {
                    evidence_class: evidence_counts[evidence_class]
                    for evidence_class in EVIDENCE_CLASSES
                },
                "evidence_class_fractions": {
                    evidence_class: (
                        evidence_counts[evidence_class] / occurrence_count
                        if occurrence_count
                        else None
                    )
                    for evidence_class in EVIDENCE_CLASSES
                },
                "mean_dimension_jaccard_to_other_named_descriptors": (
                    statistics.fmean(other_jaccards) if other_jaccards else 0.0
                ),
                "language_features": "NOT_AVAILABLE_NOT_INFERRED_FROM_IDENTIFIER",
            }
        )
    return {
        "dimensions": dimensions,
        "feature_definition": {
            "dimension_membership": "EXACT_REGISTERED_MULTI_HOT",
            "role_level": "EXPLICIT_MIDDLE_REGISTRY_OR_UNSPECIFIED_NAMED",
            "evidence_distribution": "CATEGORICAL_COUNTS_AND_FRACTIONS_NO_SCALAR_WEIGHT",
            "co_membership": "MEAN_REGISTERED_DIMENSION_JACCARD_DIAGNOSTIC_ONLY",
            "language_features": "NOT_AVAILABLE_NOT_INFERRED_FROM_IDENTIFIER",
            "embedding": "NOT_RUN_R9_EMBEDDING_PROHIBITED",
        },
        "descriptor_count": len(rows),
        "rows": rows,
    }


def summarize(features: dict[str, Any]) -> dict[str, Any]:
    rows = features["rows"]
    totals = Counter()
    for row in rows:
        totals.update(row["evidence_class_counts"])
    return {
        "descriptor_count": len(rows),
        "registered_dimension_count": len(features["dimensions"]),
        "multi_dimension_descriptor_count": sum(
            row["dimension_membership_count"] > 1 for row in rows
        ),
        "descriptors_never_returned": sum(
            not row["output_occurrences"] for row in rows
        ),
        "evidence_class_occurrence_totals": dict(sorted(totals.items())),
        "embedding": "NOT_RUN_R9_EMBEDDING_PROHIBITED",
    }
