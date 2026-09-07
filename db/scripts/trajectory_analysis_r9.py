#!/usr/bin/env python3
"""Exact answer-evidence prefix trajectories for frozen R9 analysis."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any

SLOT_PATTERN = re.compile(r"^Q(\d+)$")


def ordered_answers(final: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    answers = final["state"]["base_state"].get("answers_by_question")
    if not isinstance(answers, dict) or not answers:
        raise ValueError("ORDERED_FROZEN_ANSWERS_REQUIRED")
    indexed = []
    for slot, answer in answers.items():
        match = SLOT_PATTERN.fullmatch(slot)
        if match is None or not isinstance(answer, dict):
            raise ValueError("REGISTERED_QUESTION_SLOT_REQUIRED:" + str(slot))
        indexed.append((int(match.group(1)), slot, answer))
    indexed.sort()
    expected = list(range(indexed[0][0], indexed[0][0] + len(indexed)))
    if [index for index, _, _ in indexed] != expected:
        raise ValueError("CONTIGUOUS_QUESTION_SEQUENCE_REQUIRED")
    return [(slot, answer) for _, slot, answer in indexed]


def dominant_dimensions(counts: Counter[str]) -> list[str]:
    if not counts:
        return []
    maximum = max(counts.values())
    return sorted(
        dimension_id for dimension_id, count in counts.items() if count == maximum
    )


def trajectory_class(stages: list[dict[str, Any]]) -> dict[str, str]:
    supported = [stage for stage in stages if stage["active_dimension_count"]]
    if not supported:
        return {
            "dimension_evolution": "NO_SELECTED_REGISTERED_DIMENSION_EVIDENCE",
            "dominance_evolution": "NO_DOMINANT_DIMENSION",
            "trajectory_type": "NO_SELECTED_EVIDENCE",
        }
    sizes = [stage["active_dimension_count"] for stage in supported]
    if any(right < left for left, right in zip(sizes, sizes[1:])):
        raise ValueError("CUMULATIVE_EVIDENCE_DIMENSIONS_MUST_NOT_CONTRACT")
    dimension_evolution = (
        "EXPANDS_AFTER_FIRST_SUPPORT"
        if len(set(sizes)) > 1
        else "STABLE_AFTER_FIRST_SUPPORT"
    )
    dominance = [tuple(stage["dominant_dimension_ids"]) for stage in supported]
    dominance_evolution = (
        "STABLE_AFTER_FIRST_SUPPORT"
        if len(set(dominance)) == 1
        else "DOMINANT_SET_CHANGED"
    )
    return {
        "dimension_evolution": dimension_evolution,
        "dominance_evolution": dominance_evolution,
        "trajectory_type": dimension_evolution + "__" + dominance_evolution,
    }


def extract_trajectory(
    source: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    final = source["actual_return"]
    counts: Counter[str] = Counter()
    selected_ids: set[str] = set()
    stages = []
    for slot, answer in ordered_answers(final):
        new_ids = list(answer.get("selected_option_ids", []))
        if len(new_ids) != len(set(new_ids)):
            raise ValueError("DUPLICATE_SELECTED_OPTION_ID:" + slot)
        for candidate_id in new_ids:
            if candidate_id not in registry:
                raise ValueError("UNREGISTERED_SELECTED_OPTION_ID:" + candidate_id)
            selected_ids.add(candidate_id)
            for dimension_id in registry[candidate_id]["support_dimension_ids"]:
                counts[dimension_id] += 1
        stages.append(
            {
                "slot": slot,
                "question_id": answer.get("question_id"),
                "answer_state": answer.get("state"),
                "new_selected_concept_ids": new_ids,
                "cumulative_selected_concept_count": len(selected_ids),
                "cumulative_dimension_counts": dict(sorted(counts.items())),
                "active_dimension_count": len(counts),
                "dominant_dimension_ids": dominant_dimensions(counts),
                "candidate_set_size": None,
                "candidate_evidence_distribution": None,
            }
        )
    classification = trajectory_class(stages)
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "stages": stages,
        **classification,
        "trajectory_scope": "OBSERVED_ANSWER_EVIDENCE_PREFIXES_ONLY",
        "intermediate_candidate_state": "NOT_AVAILABLE_FINAL_ENDPOINT_ONLY",
        "T_used": False,
        "output_changed": False,
    }


def summarize(trajectories: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [row for row in trajectories if row["generator"] == generator]
        question_counts = Counter(len(row["stages"]) for row in rows)
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({row["group_id"] for row in rows}),
            "question_count_distribution": {
                str(key): value for key, value in sorted(question_counts.items())
            },
            "trajectory_type_counts": dict(
                sorted(Counter(row["trajectory_type"] for row in rows).items())
            ),
            "dimension_evolution_counts": dict(
                sorted(Counter(row["dimension_evolution"] for row in rows).items())
            ),
            "dominance_evolution_counts": dict(
                sorted(Counter(row["dominance_evolution"] for row in rows).items())
            ),
            "intermediate_candidate_trajectory": "NOT_EVALUATED_NOT_SAVED",
            "interpretation": (
                "Cumulative answer evidence can expand or remain stable but cannot show "
                "candidate-set convergence. Dominance changes describe evidence prefixes "
                "only and do not validate a trigger or stopping rule."
            ),
        }
    return result
