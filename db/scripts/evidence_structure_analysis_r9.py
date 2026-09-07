#!/usr/bin/env python3
"""Deterministic evidence, question, K1, position, and profile analyses for R9."""

from __future__ import annotations

from collections import Counter, defaultdict
import statistics
from typing import Any, Iterable

import audit_output_quality_r9 as quality
import coffee_profile_assignment_r9 as profiles
from output_policy_r9 import adapt_output
from trajectory_analysis_r9 import ordered_answers

EVIDENCE_CLASSES = (
    "EXPLICIT_USER_EXPRESSION",
    "SUPPORTED_DIRECTION_ONLY",
    "NO_DIRECT_USER_ANSWER_TRACE",
)


def categorical_summary(values: Iterable[str]) -> dict[str, Any]:
    counts = Counter(values)
    total = sum(counts.values())
    return {
        "total": total,
        "counts": {key: counts[key] for key in EVIDENCE_CLASSES},
        "fractions": {
            key: counts[key] / total if total else None for key in EVIDENCE_CLASSES
        },
    }


def evidence_stratified_rows(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for source in sources:
        profile = profiles.profile_case(source, registry)["policies"]["OUT_SEPARATED"]
        for evidence in quality.evidence_rows(source, registry):
            if evidence["evidence_class"] not in EVIDENCE_CLASSES:
                raise ValueError("UNREGISTERED_EVIDENCE_CLASS")
            rows.append(
                {
                    "record_id": source["record_id"],
                    "group_id": source["group_id"],
                    "descriptor_id": evidence["descriptor_id"],
                    "panel": evidence["panel"],
                    "position": evidence["position"],
                    "evidence_class": evidence["evidence_class"],
                    "dimension_ids": registry[evidence["descriptor_id"]][
                        "support_dimension_ids"
                    ],
                    "profile_type": profile["profile_type"],
                }
            )
    return rows


def summarize_evidence_strata(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_panel = {
        panel: categorical_summary(
            row["evidence_class"] for row in rows if row["panel"] == panel
        )
        for panel in ("main", "secondary")
    }
    dimensions = sorted(
        {dimension_id for row in rows for dimension_id in row["dimension_ids"]}
    )
    profile_types = sorted({row["profile_type"] for row in rows})
    return {
        "descriptor_occurrences": len(rows),
        "coffee_groups": len({row["group_id"] for row in rows}),
        "overall": categorical_summary(row["evidence_class"] for row in rows),
        "by_panel": by_panel,
        "by_dimension_multi_membership": {
            dimension_id: categorical_summary(
                row["evidence_class"]
                for row in rows
                if dimension_id in row["dimension_ids"]
            )
            for dimension_id in dimensions
        },
        "by_profile_type": {
            profile_type: categorical_summary(
                row["evidence_class"]
                for row in rows
                if row["profile_type"] == profile_type
            )
            for profile_type in profile_types
        },
        "interpretation": (
            "Dimension counts are multi-membership occurrence counts. Evidence classes "
            "remain categorical and are not collapsed into a scalar strength score."
        ),
    }


def first_dimension_sources(
    final: dict[str, Any], registry: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    first_by_dimension = {}
    first_direct_slot = {}
    for slot, answer in ordered_answers(final):
        selected = list(answer.get("selected_option_ids", []))
        for candidate_id in selected:
            if candidate_id not in registry:
                raise ValueError("UNREGISTERED_SELECTED_OPTION_ID:" + candidate_id)
            first_direct_slot.setdefault(candidate_id, slot)
            for dimension_id in registry[candidate_id]["support_dimension_ids"]:
                row = first_by_dimension.setdefault(
                    dimension_id,
                    {"slot": slot, "source_concept_ids": []},
                )
                if row["slot"] == slot:
                    row["source_concept_ids"].append(candidate_id)
    for row in first_by_dimension.values():
        row["source_concept_ids"] = sorted(set(row["source_concept_ids"]))
    return first_by_dimension, first_direct_slot


def question_source_rows(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for source in sources:
        final = source["actual_return"]
        output = adapt_output(final, registry, "OUT_SEPARATED")
        first_by_dimension, direct_slots = first_dimension_sources(final, registry)
        for panel, output_rows in (
            ("main", output["main"]),
            ("secondary", output["secondary"]),
        ):
            for position, output_row in enumerate(output_rows, 1):
                candidate_id = output_row["candidate_id"]
                dimension_sources = [
                    {
                        "dimension_id": dimension_id,
                        **first_by_dimension[dimension_id],
                    }
                    for dimension_id in registry[candidate_id]["support_dimension_ids"]
                    if dimension_id in first_by_dimension
                ]
                slots = sorted(
                    {row["slot"] for row in dimension_sources},
                    key=lambda value: int(value[1:]),
                )
                rows.append(
                    {
                        "record_id": source["record_id"],
                        "group_id": source["group_id"],
                        "descriptor_id": candidate_id,
                        "panel": panel,
                        "position": position,
                        "exact_descriptor_source_slot": direct_slots.get(candidate_id),
                        "first_compatible_dimension_source_slot": (
                            slots[0] if slots else None
                        ),
                        "dimension_source_rows": dimension_sources,
                        "source_interpretation": (
                            "EXACT_DESCRIPTOR_SELECTION"
                            if candidate_id in direct_slots
                            else (
                                "FIRST_DIMENSION_COMPATIBILITY_ONLY"
                                if slots
                                else "NO_SELECTED_DIMENSION_SOURCE"
                            )
                        ),
                    }
                )
    return rows


def summarize_question_sources(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "descriptor_occurrences": len(rows),
        "exact_descriptor_source_slot_counts": dict(
            sorted(
                Counter(
                    row["exact_descriptor_source_slot"] or "NONE" for row in rows
                ).items()
            )
        ),
        "first_compatible_dimension_source_slot_counts": dict(
            sorted(
                Counter(
                    row["first_compatible_dimension_source_slot"] or "NONE"
                    for row in rows
                ).items()
            )
        ),
        "source_interpretation_counts": dict(
            sorted(Counter(row["source_interpretation"] for row in rows).items())
        ),
        "by_panel": {
            panel: dict(
                sorted(
                    Counter(
                        row["source_interpretation"]
                        for row in rows
                        if row["panel"] == panel
                    ).items()
                )
            )
            for panel in ("main", "secondary")
        },
        "interpretation": (
            "First activation is dimension provenance, not causal attribution and not "
            "evidence that a broad selection entails a returned child descriptor."
        ),
    }


def k1_output_rows(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = []
    for source in sources:
        final = source["actual_return"]
        output = adapt_output(final, registry, "OUT_SEPARATED")
        direct_ids = quality.selected_user_concepts(final) | set(
            final["state"]["k1"].get("confirmed_concepts", [])
        )
        pool = output["main"] + output["secondary"]
        k1_dimensions = final["state"]["k1"]["dimensions"]
        for dimension_id, k1 in sorted(k1_dimensions.items()):
            if not isinstance(k1.get("status"), str):
                raise ValueError("K1_STATUS_REQUIRED:" + dimension_id)
            matching = [
                row
                for row in pool
                if dimension_id
                in registry[row["candidate_id"]]["support_dimension_ids"]
            ]
            dimension_evidence_classes = [
                (
                    "EXPLICIT_USER_EXPRESSION"
                    if row["candidate_id"] in direct_ids
                    else (
                        "SUPPORTED_DIRECTION_ONLY"
                        if float(k1.get("supported", 0)) > 0
                        else "NO_DIRECT_USER_ANSWER_TRACE"
                    )
                )
                for row in matching
            ]
            rows.append(
                {
                    "record_id": source["record_id"],
                    "group_id": source["group_id"],
                    "dimension_id": dimension_id,
                    "k1_status": k1["status"],
                    "k1_supported": k1["supported"],
                    "k1_unknown": k1["unknown"],
                    "descriptor_count": len(matching),
                    "middle_category_count": sum(
                        row["candidate_id"] in quality.MIDDLE_NAMED_IDS
                        for row in matching
                    ),
                    "other_named_count": sum(
                        row["candidate_id"] not in quality.MIDDLE_NAMED_IDS
                        for row in matching
                    ),
                    "dimension_local_evidence_classes": dimension_evidence_classes,
                }
            )
    return rows


def summarize_k1(rows: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = sorted({row["k1_status"] for row in rows})
    dimensions = sorted({row["dimension_id"] for row in rows})

    def aggregate(values: list[dict[str, Any]]) -> dict[str, Any]:
        descriptor_counts = [row["descriptor_count"] for row in values]
        evidence = [
            value for row in values for value in row["dimension_local_evidence_classes"]
        ]
        return {
            "dimension_instances": len(values),
            "records_with_output_descriptor_membership": len(
                {row["record_id"] for row in values if row["descriptor_count"]}
            ),
            "coffee_groups_with_output_descriptor_membership": len(
                {row["group_id"] for row in values if row["descriptor_count"]}
            ),
            "mean_output_descriptor_memberships": (
                statistics.fmean(descriptor_counts) if descriptor_counts else None
            ),
            "zero_output_descriptor_instances": sum(
                not value for value in descriptor_counts
            ),
            "middle_category_memberships": sum(
                row["middle_category_count"] for row in values
            ),
            "other_named_memberships": sum(row["other_named_count"] for row in values),
            "evidence_distribution": categorical_summary(evidence),
        }

    return {
        "observed_k1_statuses": statuses,
        "by_status": {
            status: aggregate([row for row in rows if row["k1_status"] == status])
            for status in statuses
        },
        "by_dimension_and_status": {
            dimension_id: {
                status: aggregate(
                    [
                        row
                        for row in rows
                        if row["dimension_id"] == dimension_id
                        and row["k1_status"] == status
                    ]
                )
                for status in statuses
            }
            for dimension_id in dimensions
        },
        "interpretation": (
            "All registered dimensions are retained, including zero-output rows. K1 status "
            "association uses dimension-local evidence classes, is descriptive, and does "
            "not establish causal activation or descriptor specificity."
        ),
    }


def summarize_position_evidence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_record: dict[str, dict[str, list[str]]] = defaultdict(
        lambda: {"main": [], "secondary": []}
    )
    for row in rows:
        by_record[row["record_id"]][row["panel"]].append(row["evidence_class"])
    direct_outcomes = Counter()
    no_trace_outcomes = Counter()

    def compare_shares(
        main: list[str], secondary: list[str], evidence_class: str
    ) -> str:
        if not main or not secondary:
            return "NOT_COMPARABLE_EMPTY_PANEL"
        main_share = main.count(evidence_class) / len(main)
        secondary_share = secondary.count(evidence_class) / len(secondary)
        if main_share > secondary_share:
            return "MAIN_HIGHER"
        if secondary_share > main_share:
            return "SECONDARY_HIGHER"
        return "TIE"

    for panels in by_record.values():
        direct_outcomes[
            compare_shares(
                panels["main"], panels["secondary"], "EXPLICIT_USER_EXPRESSION"
            )
        ] += 1
        no_trace_outcomes[
            compare_shares(
                panels["main"], panels["secondary"], "NO_DIRECT_USER_ANSWER_TRACE"
            )
        ] += 1
    return {
        "by_panel": {
            panel: categorical_summary(
                row["evidence_class"] for row in rows if row["panel"] == panel
            )
            for panel in ("main", "secondary")
        },
        "paired_record_direct_share_outcomes": dict(sorted(direct_outcomes.items())),
        "paired_record_no_trace_share_outcomes": dict(
            sorted(no_trace_outcomes.items())
        ),
        "evidence_scalar_score": "NOT_DEFINED",
        "interpretation": (
            "Panel distributions and within-record share comparisons are reported without "
            "mapping evidence classes to arbitrary 1/0.5/0 weights."
        ),
    }


def profile_cross_summary(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    buckets: dict[str, list[tuple[dict[str, Any], list[dict[str, Any]]]]] = defaultdict(
        list
    )
    for source in sources:
        case = profiles.profile_case(source, registry)
        profile_type = case["policies"]["OUT_SEPARATED"]["profile_type"]
        buckets[profile_type].append((case, quality.evidence_rows(source, registry)))
    result = {}
    for profile_type, values in sorted(buckets.items()):
        cases = [case for case, _ in values]
        evidence = [row for _, evidence_rows in values for row in evidence_rows]
        separated = [case["policies"]["OUT_SEPARATED"] for case in cases]
        result[profile_type] = {
            "records": len(cases),
            "coffee_groups": len({case["group_id"] for case in cases}),
            "evidence_distribution": categorical_summary(
                row["evidence_class"] for row in evidence
            ),
            "mean_active_dimension_count": statistics.fmean(
                row["active_dimension_count"] for row in separated
            ),
            "mean_repeated_dimension_membership_rate": statistics.fmean(
                row["redundancy"]["repeated_dimension_membership_rate"]
                for row in separated
            ),
            "mean_delta_separated_minus_mixed": {
                field: statistics.fmean(
                    case["delta_separated_minus_mixed"][field] for case in cases
                )
                for field in (
                    "named_descriptor_count",
                    "active_dimension_count",
                    "repeated_dimension_membership_rate",
                )
            },
            "target_or_gap_metric": "NOT_READ_NO_T",
        }
    return {
        "profile_types": result,
        "inference": "NOT_RUN_DESCRIPTIVE_DEPENDENT_RECORDS_RETAINED",
        "interpretation": (
            "Profile types are output-composition strata, not coffee classes. Evidence, "
            "coverage and redundancy remain separate; no composite benefit score is made."
        ),
    }
