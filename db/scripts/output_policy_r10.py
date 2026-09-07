#!/usr/bin/env python3
"""R10 evidence-aware wrapper for the owner-approved OUT_SEPARATED policy.

The wrapper never reads T.  It removes named descriptors that have neither an
exact selected/confirmed concept nor a currently supported registered dimension.
It does not backfill removed positions.  Shared-dimension and ontology-review
rows remain visible but are explicitly marked non-strict.
"""

from __future__ import annotations

from typing import Any

from output_policy_r9 import adapt_output as adapt_r9


def selected_or_confirmed(final: dict[str, Any]) -> set[str]:
    answers = final["state"]["base_state"].get("answers_by_question", {})
    selected = {
        candidate_id
        for answer in answers.values()
        for candidate_id in answer.get("selected_option_ids", [])
    }
    return selected | set(final["state"]["k1"].get("confirmed_concepts", []))


def supported_dimension_ids(final: dict[str, Any]) -> set[str]:
    return {
        dimension_id
        for dimension_id, value in final["state"]["k1"]["dimensions"].items()
        if float(value.get("supported", 0)) > 0
    }


def evidence_disposition(
    candidate_id: str,
    registry: dict[str, Any],
    direct: set[str],
    supported: set[str],
) -> str:
    if candidate_id in direct:
        return "STRICT_DIRECT_ASSERTION"
    dimensions = set(registry[candidate_id].get("support_dimension_ids", []))
    if dimensions & supported:
        return "NON_STRICT_SHARED_DIMENSION_ONLY"
    return "INSUFFICIENT_EVIDENCE_ABSTAIN"


def adapt_output(
    final: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    output = adapt_r9(final, registry, "OUT_SEPARATED")
    direct = selected_or_confirmed(final)
    supported = supported_dimension_ids(final)
    abstained: list[dict[str, Any]] = []

    def filter_panel(panel: str) -> list[dict[str, Any]]:
        kept = []
        for original_position, row in enumerate(output[panel], 1):
            disposition = evidence_disposition(
                row["candidate_id"], registry, direct, supported
            )
            annotated = {
                **row,
                "source_panel": panel,
                "source_position": original_position,
                "assertion_status": disposition,
            }
            if disposition == "INSUFFICIENT_EVIDENCE_ABSTAIN":
                abstained.append(annotated)
            else:
                kept.append(annotated)
        return kept

    main = filter_panel("main")
    secondary = filter_panel("secondary")
    comparison = [row["candidate_id"] for row in main + secondary]
    if len(comparison) != len(set(comparison)):
        raise ValueError("R10_DUPLICATE_COMPARISON_ID")
    return {
        **output,
        "policy_id": "OUT_SEPARATED_R10_EVIDENCE_ABSTENTION",
        "main": main,
        "secondary": secondary,
        "comparison_pool_candidate_ids": comparison,
        "abstained": abstained,
        "comparison_executable": len(comparison) >= 3,
        "comparison_unavailable_reason": (
            None if len(comparison) >= 3 else "FEWER_THAN_3_EVIDENCE_ADMISSIBLE_CANDIDATES"
        ),
        "T_used": False,
        "backfill_count": 0,
    }
