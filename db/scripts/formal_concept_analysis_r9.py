#!/usr/bin/env python3
"""Exact finite formal-context observations for frozen R9 descriptor outputs."""

from __future__ import annotations

from collections import Counter
from typing import Any

from output_policy_r9 import NAMED_DESCRIPTOR, adapt_output

MAX_FORMAL_INTENTS = 200_000


def build_formal_context(
    sources: list[dict[str, Any]],
    registry: dict[str, Any],
    policy_id: str = "OUT_SEPARATED",
) -> dict[str, Any]:
    attributes = sorted(
        candidate_id
        for candidate_id, entry in registry.items()
        if entry["role"] == NAMED_DESCRIPTOR
    )
    objects = []
    for source in sources:
        output = adapt_output(source["actual_return"], registry, policy_id)
        intent = sorted(
            row["candidate_id"] for row in output["main"] + output["secondary"]
        )
        objects.append(
            {
                "object_id": source["record_id"],
                "group_id": source["group_id"],
                "attributes": intent,
            }
        )
    return {
        "policy_id": policy_id,
        "attributes": attributes,
        "objects": objects,
    }


def enumerate_formal_intents(
    context: dict[str, Any], max_intents: int = MAX_FORMAL_INTENTS
) -> tuple[list[frozenset[str]], bool]:
    """Enumerate the intersection closure of object intents without a learned cutoff."""

    all_attributes = frozenset(context["attributes"])
    initial = {all_attributes} | {
        frozenset(row["attributes"]) for row in context["objects"]
    }
    intents = set(initial)
    queue = sorted(initial, key=lambda value: (len(value), tuple(sorted(value))))
    index = 0
    truncated = False
    while index < len(queue):
        current = queue[index]
        index += 1
        for other in list(queue):
            intersection = current & other
            if intersection in intents:
                continue
            if len(intents) >= max_intents:
                truncated = True
                break
            intents.add(intersection)
            queue.append(intersection)
        if truncated:
            break
    return (
        sorted(intents, key=lambda value: (len(value), tuple(sorted(value)))),
        truncated,
    )


def formal_concepts(context: dict[str, Any]) -> dict[str, Any]:
    intents, truncated = enumerate_formal_intents(context)
    objects = context["objects"]
    rows = []
    for intent in intents:
        extent = [row for row in objects if intent.issubset(set(row["attributes"]))]
        rows.append(
            {
                "intent_descriptor_ids": sorted(intent),
                "extent_record_ids": sorted(row["object_id"] for row in extent),
                "extent_group_ids": sorted({row["group_id"] for row in extent}),
                "extent_record_count": len(extent),
                "extent_group_count": len({row["group_id"] for row in extent}),
            }
        )
    return {
        "formal_intent_count": len(rows),
        "enumeration_truncated": truncated,
        "software_safety_limit": MAX_FORMAL_INTENTS,
        "concepts": rows,
    }


def exact_singleton_implications(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Return A=>B rules that have zero exceptions in this frozen context."""

    attributes = context["attributes"]
    objects = context["objects"]
    extents = {
        candidate_id: {
            index
            for index, row in enumerate(objects)
            if candidate_id in row["attributes"]
        }
        for candidate_id in attributes
    }
    rows = []
    for antecedent in attributes:
        antecedent_extent = extents[antecedent]
        if not antecedent_extent:
            continue
        for consequent in attributes:
            if antecedent == consequent or not antecedent_extent.issubset(
                extents[consequent]
            ):
                continue
            support_groups = {objects[index]["group_id"] for index in antecedent_extent}
            rows.append(
                {
                    "antecedent_descriptor_id": antecedent,
                    "consequent_descriptor_id": consequent,
                    "support_record_count": len(antecedent_extent),
                    "support_group_count": len(support_groups),
                    "exception_record_count": 0,
                    "frozen_context_confidence": 1.0,
                    "equivalent_extents": antecedent_extent == extents[consequent],
                    "semantic_status": "CO_OCCURRENCE_CANDIDATE_ONLY_NOT_RELATION_EDGE",
                }
            )
    rows.sort(
        key=lambda row: (
            -row["support_group_count"],
            -row["support_record_count"],
            row["antecedent_descriptor_id"],
            row["consequent_descriptor_id"],
        )
    )
    return rows


def analyze_formal_context(context: dict[str, Any]) -> dict[str, Any]:
    concepts = formal_concepts(context)
    implications = exact_singleton_implications(context)
    return {
        "context": context,
        "formal_concepts": concepts,
        "exact_singleton_implications": implications,
        "summary": {
            "object_records": len(context["objects"]),
            "object_groups": len({row["group_id"] for row in context["objects"]}),
            "attributes": len(context["attributes"]),
            "formal_intents": concepts["formal_intent_count"],
            "formal_intent_enumeration_truncated": concepts["enumeration_truncated"],
            "exact_singleton_implication_candidates": len(implications),
            "equivalent_extent_directed_candidates": sum(
                row["equivalent_extents"] for row in implications
            ),
            "implication_support_group_distribution": dict(
                sorted(
                    Counter(row["support_group_count"] for row in implications).items()
                )
            ),
            "semantic_relation_edges_created": 0,
            "interpretation": (
                "Formal implications are exact only inside the repeatedly viewed frozen "
                "output context. They are association-review candidates, not IS_A, "
                "SYNONYM, causal, or sensory-truth relations."
            ),
        },
    }
