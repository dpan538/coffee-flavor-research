#!/usr/bin/env python3
"""Rule-based R9 coffee profile assignment over frozen policy outputs."""

from __future__ import annotations

from collections import Counter
import statistics
from typing import Any

import audit_output_quality_r9 as quality
from evaluate_output_diversity_r9 import redundancy_metrics
from output_policy_r9 import NAMED_DESCRIPTOR, adapt_output


def dimension_counts(
    rows: list[dict[str, Any]], registry: dict[str, Any]
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        for dimension_id in registry[row["candidate_id"]]["support_dimension_ids"]:
            counts[dimension_id] += 1
    return counts


def profile_type(counts: Counter[str]) -> dict[str, Any]:
    if not counts:
        return {
            "profile_type": "NO_REGISTERED_NAMED_DIMENSION",
            "dominant_dimension_ids": [],
            "second_tier_dimension_ids": [],
        }
    maximum = max(counts.values())
    dominant = sorted(
        dimension_id for dimension_id, count in counts.items() if count == maximum
    )
    remaining_counts = [count for count in counts.values() if count < maximum]
    second = []
    if remaining_counts:
        second_value = max(remaining_counts)
        second = sorted(
            dimension_id
            for dimension_id, count in counts.items()
            if count == second_value
        )
    label = (
        "DOMINANT::" + dominant[0]
        if len(dominant) == 1
        else "MIXED_DOMINANT::" + "|".join(dominant)
    )
    return {
        "profile_type": label,
        "dominant_dimension_ids": dominant,
        "second_tier_dimension_ids": second,
    }


def policy_view(output: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    named = [
        row
        for row in output["main"] + output["secondary"]
        if registry[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR
    ]
    counts = dimension_counts(named, registry)
    return {
        **profile_type(counts),
        "named_descriptor_count": len(named),
        "active_dimension_count": len(counts),
        "dimension_counts": dict(sorted(counts.items())),
        "redundancy": redundancy_metrics(named, registry),
        "overall_profile_ids": [
            row["candidate_id"] for row in output.get("overall_profile", [])
        ],
    }


def profile_case(source: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    final = source["actual_return"]
    mixed = adapt_output(final, registry, "OUT_MIXED")
    separated = adapt_output(final, registry, "OUT_SEPARATED")
    mixed_view = policy_view(mixed, registry)
    separated_view = policy_view(separated, registry)
    evidence_counts = Counter(
        row["evidence_class"] for row in quality.evidence_rows(source, registry)
    )
    total_evidence_rows = sum(evidence_counts.values())
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "policies": {
            "OUT_MIXED": mixed_view,
            "OUT_SEPARATED": separated_view,
        },
        "separated_evidence_distribution": {
            evidence_class: {
                "count": evidence_counts[evidence_class],
                "fraction": (
                    evidence_counts[evidence_class] / total_evidence_rows
                    if total_evidence_rows
                    else None
                ),
            }
            for evidence_class in (
                "EXPLICIT_USER_EXPRESSION",
                "SUPPORTED_DIRECTION_ONLY",
                "NO_DIRECT_USER_ANSWER_TRACE",
            )
        },
        "delta_separated_minus_mixed": {
            "named_descriptor_count": separated_view["named_descriptor_count"]
            - mixed_view["named_descriptor_count"],
            "active_dimension_count": separated_view["active_dimension_count"]
            - mixed_view["active_dimension_count"],
            "repeated_dimension_membership_rate": separated_view["redundancy"][
                "repeated_dimension_membership_rate"
            ]
            - mixed_view["redundancy"]["repeated_dimension_membership_rate"],
        },
        "T_used": False,
        "output_changed": False,
    }


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({case["group_id"] for case in rows}),
            "profile_type_counts": {
                policy_id: dict(
                    sorted(
                        Counter(
                            case["policies"][policy_id]["profile_type"] for case in rows
                        ).items()
                    )
                )
                for policy_id in ("OUT_MIXED", "OUT_SEPARATED")
            },
            "mean_delta_separated_minus_mixed": {
                field: (
                    statistics.fmean(
                        case["delta_separated_minus_mixed"][field] for case in rows
                    )
                    if rows
                    else None
                )
                for field in (
                    "named_descriptor_count",
                    "active_dimension_count",
                    "repeated_dimension_membership_rate",
                )
            },
            "profile_type_changed_records": sum(
                case["policies"]["OUT_MIXED"]["profile_type"]
                != case["policies"]["OUT_SEPARATED"]["profile_type"]
                for case in rows
            ),
            "interpretation": (
                "Types are deterministic descriptions of registered named-output dimension "
                "counts, not learned clusters or claims about coffee kinds."
            ),
        }
    return result
