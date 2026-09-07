#!/usr/bin/env python3
"""Audit R9 output mechanisms, answer evidence and overall profiles.

The three audits operate on sealed R8 actual returns and deterministic R9
adapters.  Output selection never receives T.  The mechanism audit uses T only
after outputs exist, with the same R8 returned-position metric implementation.
Raw record IDs, answers, targets and case details remain in owner storage.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

from acquire_supervision_r5 import save
import output_alignment_r8 as r8
from output_policy_r9 import (
    NAMED_DESCRIPTOR,
    PROFILE_DIRECTION,
    adapt_output,
    role_registry_from_contract,
)

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.output-quality-audit.v2"
MIDDLE_NAMED_IDS = frozenset({"broad.citrus", "broad.chocolate", "broad.nutty"})
EPSILON = 1e-12


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["candidate_id"] for row in rows]


def outcome(delta: float) -> str:
    if delta < -EPSILON:
        return "IMPROVEMENT"
    if delta > EPSILON:
        return "REGRESSION"
    return "TIE"


def metric_delta(
    left: dict[str, Any], right: dict[str, Any]
) -> dict[str, float | None]:
    return {
        metric: (
            None
            if left[metric] is None or right[metric] is None
            else right[metric] - left[metric]
        )
        for metric in ("raw_gap", "recall", "ndcg_actual_positions")
    }


def descriptor_level(candidate_id: str) -> str:
    return (
        "EVIDENCE_QUALIFIED_MIDDLE_CATEGORY"
        if candidate_id in MIDDLE_NAMED_IDS
        else "SPECIFIC_NAMED_DESCRIPTOR"
    )


def selected_user_concepts(final: dict[str, Any]) -> set[str]:
    answers = final["state"]["base_state"].get("answers_by_question", {})
    return {
        candidate_id
        for answer in answers.values()
        for candidate_id in answer.get("selected_option_ids", [])
    }


def supported_dimensions(final: dict[str, Any]) -> dict[str, dict[str, Any]]:
    dimensions = final["state"]["k1"]["dimensions"]
    return {
        dimension_id: value
        for dimension_id, value in dimensions.items()
        if float(value.get("supported", 0)) > 0
    }


def concept_from_evidence_id(value: str) -> str | None:
    return value.split(":", 1)[1] if value.startswith("concept:") else None


def named_order_preserved(
    ranking: list[str], before: list[str], after: list[str], registry: dict[str, Any]
) -> bool:
    common = set(before) & set(after)
    expected = [
        candidate_id
        for candidate_id in ranking
        if candidate_id in common and registry[candidate_id]["role"] == NAMED_DESCRIPTOR
    ]
    return [
        candidate_id for candidate_id in after if candidate_id in common
    ] == expected


def mechanism_case(source: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    final = source["actual_return"]
    mixed = adapt_output(final, registry, "OUT_MIXED")
    separated = adapt_output(final, registry, "OUT_SEPARATED")
    mixed_main = ids(mixed["main"])
    separated_main = ids(separated["main"])
    mixed_pool = mixed["comparison_pool_candidate_ids"]
    separated_pool = separated["comparison_pool_candidate_ids"]
    removed = [
        candidate_id
        for candidate_id in mixed_main
        if candidate_id not in separated_main
    ]
    added = [
        candidate_id
        for candidate_id in separated_main
        if candidate_id not in mixed_main
    ]
    removed_directions = [
        candidate_id
        for candidate_id in removed
        if registry[candidate_id]["role"] == PROFILE_DIRECTION
    ]
    added_named = [
        candidate_id
        for candidate_id in added
        if registry[candidate_id]["role"] == NAMED_DESCRIPTOR
    ]
    if mixed_main == separated_main:
        mechanism = "NO_MAIN_CHANGE"
    elif removed_directions and added_named:
        mechanism = "PROFILE_DIRECTION_REMOVED_NAMED_PROMOTED"
    elif removed_directions:
        mechanism = "PROFILE_DIRECTION_REMOVED_NO_NAMED_BACKFILL"
    elif set(mixed_main) == set(separated_main):
        mechanism = "ORDER_ONLY_CHANGE"
    elif added_named:
        mechanism = "NAMED_CONTENT_CHANGE"
    else:
        mechanism = "OTHER_CONTENT_CHANGE"

    mixed_metric = r8.measure(mixed_main, source["full_T"], 5)
    separated_metric = r8.measure(separated_main, source["full_T"], 5)
    mixed_pool_metric = r8.measure(mixed_pool, source["full_T"], 8)
    separated_pool_metric = r8.measure(separated_pool, source["full_T"], 8)
    positive_targets = {
        candidate_id for candidate_id, weight in source["full_T"].items() if weight > 0
    }
    mixed_exact = set(mixed_main) & positive_targets
    separated_exact = set(separated_main) & positive_targets
    mixed_witness = r8.witness(mixed_main, source["full_T"])
    separated_witness = r8.witness(separated_main, source["full_T"])
    positions_before = {
        candidate_id: index for index, candidate_id in enumerate(mixed_main)
    }
    positions_after = {
        candidate_id: index for index, candidate_id in enumerate(separated_main)
    }
    compacted = [
        candidate_id
        for candidate_id in separated_main
        if candidate_id in positions_before
        and positions_after[candidate_id] < positions_before[candidate_id]
    ]
    ranking = ids(final["state"]["candidate_scores"])
    if not named_order_preserved(ranking, mixed_main, separated_main, registry):
        raise ValueError("WITHIN_ROLE_ORDER_CHANGED")
    main_delta = metric_delta(mixed_metric, separated_metric)
    pool_delta = metric_delta(mixed_pool_metric, separated_pool_metric)
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "mechanism": mechanism,
        "mixed_main_ids": mixed_main,
        "separated_main_ids": separated_main,
        "mixed_pool_ids": mixed_pool,
        "separated_pool_ids": separated_pool,
        "removed_main_ids": removed,
        "added_main_ids": added,
        "removed_profile_direction_ids": removed_directions,
        "added_named_ids": added_named,
        "compacted_named_ids": compacted,
        "within_role_order_preserved": True,
        "mixed_main_metric": mixed_metric,
        "separated_main_metric": separated_metric,
        "mixed_pool_metric": mixed_pool_metric,
        "separated_pool_metric": separated_pool_metric,
        "main_metric_delta_separated_minus_mixed": main_delta,
        "pool_metric_delta_separated_minus_mixed": pool_delta,
        "main_gap_outcome": (
            "NOT_EVALUABLE"
            if main_delta["raw_gap"] is None
            else outcome(main_delta["raw_gap"])
        ),
        "added_exact_target_ids": sorted(separated_exact - mixed_exact),
        "removed_exact_target_ids": sorted(mixed_exact - separated_exact),
        "mixed_matching_witness": mixed_witness,
        "separated_matching_witness": separated_witness,
        "added_named_witness_weight": sum(
            edge["weight"]
            for edge in separated_witness
            if edge["candidate"] in set(added_named)
        ),
        "removed_direction_witness_weight": sum(
            edge["weight"]
            for edge in mixed_witness
            if edge["candidate"] in set(removed_directions)
        ),
        "middle_named_in_mixed_main": [
            candidate_id
            for candidate_id in mixed_main
            if candidate_id in MIDDLE_NAMED_IDS
        ],
        "middle_named_in_separated_main": [
            candidate_id
            for candidate_id in separated_main
            if candidate_id in MIDDLE_NAMED_IDS
        ],
        "middle_named_exact_target_ids": sorted(
            set(separated_main) & MIDDLE_NAMED_IDS & positive_targets
        ),
    }


def group_outcomes(
    cases: list[dict[str, Any]], field: str, metric: str
) -> dict[str, int]:
    all_groups = {case["group_id"] for case in cases}
    grouped: dict[str, list[float]] = defaultdict(list)
    for case in cases:
        value = case[field][metric]
        if value is not None:
            grouped[case["group_id"]].append(value)
    counts = Counter(outcome(statistics.fmean(values)) for values in grouped.values())
    counts["NOT_EVALUABLE"] = len(all_groups) - len(grouped)
    return {
        status: counts[status]
        for status in ("IMPROVEMENT", "REGRESSION", "TIE", "NOT_EVALUABLE")
    }


def group_delta_mean(cases: list[dict[str, Any]], field: str, metric: str) -> float:
    grouped: dict[str, list[float]] = defaultdict(list)
    for case in cases:
        value = case[field][metric]
        if value is not None:
            grouped[case["group_id"]].append(value)
    if not grouped:
        raise ValueError("NO_EVALUABLE_GROUP_METRIC")
    return statistics.fmean(statistics.fmean(values) for values in grouped.values())


def mechanism_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({case["group_id"] for case in rows}),
            "mechanism_counts": dict(
                sorted(Counter(case["mechanism"] for case in rows).items())
            ),
            "record_main_gap_outcomes": {
                status: sum(case["main_gap_outcome"] == status for case in rows)
                for status in (
                    "IMPROVEMENT",
                    "REGRESSION",
                    "TIE",
                    "NOT_EVALUABLE",
                )
            },
            "coffee_group_main_gap_outcomes": group_outcomes(
                rows, "main_metric_delta_separated_minus_mixed", "raw_gap"
            ),
            "coffee_group_metric_delta_separated_minus_mixed": {
                metric: group_delta_mean(
                    rows, "main_metric_delta_separated_minus_mixed", metric
                )
                for metric in ("raw_gap", "recall", "ndcg_actual_positions")
            },
            "coffee_group_pool_metric_delta_separated_minus_mixed": {
                metric: group_delta_mean(
                    rows, "pool_metric_delta_separated_minus_mixed", metric
                )
                for metric in ("raw_gap", "recall", "ndcg_actual_positions")
            },
            "cases_with_added_exact_target": sum(
                bool(case["added_exact_target_ids"]) for case in rows
            ),
            "cases_with_removed_exact_target": sum(
                bool(case["removed_exact_target_ids"]) for case in rows
            ),
            "removed_profile_direction_occurrences": sum(
                len(case["removed_profile_direction_ids"]) for case in rows
            ),
            "added_named_occurrences": sum(
                len(case["added_named_ids"]) for case in rows
            ),
            "added_named_matching_witness_weight": sum(
                case["added_named_witness_weight"] for case in rows
            ),
            "removed_direction_matching_witness_weight": sum(
                case["removed_direction_witness_weight"] for case in rows
            ),
            "within_role_reordering_cases": sum(
                not case["within_role_order_preserved"] for case in rows
            ),
            "middle_named_main_occurrences": sum(
                len(case["middle_named_in_separated_main"]) for case in rows
            ),
            "middle_named_exact_target_occurrences": sum(
                len(case["middle_named_exact_target_ids"]) for case in rows
            ),
            "interpretation": (
                "Mechanism counts are record descriptions. Metric deltas and outcomes are also "
                "reported at the coffee-group level. Matching witnesses are one deterministic "
                "optimum and are not additive causal attribution."
            ),
        }
    return result


def evidence_rows(
    source: dict[str, Any], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    final = source["actual_return"]
    output = adapt_output(final, registry, "OUT_SEPARATED")
    selected = selected_user_concepts(final)
    confirmed = set(final["state"]["k1"].get("confirmed_concepts", []))
    supported = supported_dimensions(final)
    result = []
    for panel, rows in (("main", output["main"]), ("secondary", output["secondary"])):
        for position, row in enumerate(rows, 1):
            candidate_id = row["candidate_id"]
            dimensions = set(registry[candidate_id].get("support_dimension_ids", []))
            shared = sorted(dimensions & set(supported))
            direct = candidate_id in selected or candidate_id in confirmed
            if direct:
                evidence_class = "EXPLICIT_USER_EXPRESSION"
            elif shared:
                evidence_class = "SUPPORTED_DIRECTION_ONLY"
            else:
                evidence_class = "NO_DIRECT_USER_ANSWER_TRACE"
            evidence_concepts = {
                concept
                for dimension_id in shared
                for value in supported[dimension_id].get("support_evidence_ids", [])
                if (concept := concept_from_evidence_id(value)) is not None
            }
            broader_sources = sorted(
                concept
                for concept in evidence_concepts | selected
                if concept in registry
                and (
                    registry[concept]["role"] == PROFILE_DIRECTION
                    or concept in MIDDLE_NAMED_IDS
                )
                and set(registry[concept].get("support_dimension_ids", [])) & dimensions
            )
            sibling_sources = sorted(
                concept
                for concept in evidence_concepts | selected
                if concept in registry
                and registry[concept]["role"] == NAMED_DESCRIPTOR
                and concept != candidate_id
                and set(registry[concept].get("support_dimension_ids", [])) & dimensions
            )
            level = descriptor_level(candidate_id)
            risk = None
            if not direct and shared:
                if level == "SPECIFIC_NAMED_DESCRIPTOR" and (
                    broader_sources or sibling_sources
                ):
                    risk = "SPECIFIC_FROM_BROADER_OR_SIBLING_EVIDENCE_REVIEW"
                elif level == "EVIDENCE_QUALIFIED_MIDDLE_CATEGORY" and broader_sources:
                    risk = "MIDDLE_CATEGORY_FROM_DIRECTION_EVIDENCE_REVIEW"
            result.append(
                {
                    "record_id": source["record_id"],
                    "group_id": source["group_id"],
                    "generator": source["policy"],
                    "panel": panel,
                    "position": position,
                    "descriptor_id": candidate_id,
                    "descriptor_level": level,
                    "evidence_class": evidence_class,
                    "explicit_output_flag": bool(row.get("explicit")),
                    "selected_or_confirmed_direct": direct,
                    "shared_supported_dimensions": shared,
                    "dimension_support_evidence_concepts": sorted(evidence_concepts),
                    "broader_support_sources": broader_sources,
                    "sibling_support_sources": sibling_sources,
                    "specificity_review_flag": risk,
                    "model_relation_evidence_ids": row.get("relation_evidence_ids", []),
                    "support_state": row.get("support_state"),
                    "scope_note": (
                        "A review flag is not an over-specification finding. Shared direction "
                        "support does not confirm this descriptor."
                    ),
                }
            )
    return result


def evidence_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        values = [row for row in rows if row["generator"] == generator]
        flagged = [row for row in values if row["specificity_review_flag"]]
        result[generator] = {
            "descriptor_occurrences": len(values),
            "records": len({row["record_id"] for row in values}),
            "coffee_groups": len({row["group_id"] for row in values}),
            "evidence_class_counts": dict(
                sorted(Counter(row["evidence_class"] for row in values).items())
            ),
            "panel_evidence_class_counts": {
                panel: dict(
                    sorted(
                        Counter(
                            row["evidence_class"]
                            for row in values
                            if row["panel"] == panel
                        ).items()
                    )
                )
                for panel in ("main", "secondary")
            },
            "descriptor_level_counts": dict(
                sorted(Counter(row["descriptor_level"] for row in values).items())
            ),
            "specificity_review_flag_occurrences": len(flagged),
            "records_with_specificity_review_flag": len(
                {row["record_id"] for row in flagged}
            ),
            "specificity_review_flag_rate_not_error_rate": (
                len(flagged) / len(values) if values else None
            ),
            "explicit_flag_without_selected_or_confirmed_count": sum(
                row["explicit_output_flag"] and not row["selected_or_confirmed_direct"]
                for row in values
            ),
            "target_or_T_used": False,
            "interpretation": (
                "NO_DIRECT_USER_ANSWER_TRACE means the returned word is not directly traceable "
                "to the current answers; it does not mean the frozen model has no source or "
                "relational evidence. Review flags require real descriptor-level judgments."
            ),
        }
    return result


def profile_case(source: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    final = source["actual_return"]
    output = adapt_output(final, registry, "OUT_SEPARATED")
    profile = ids(output["overall_profile"])
    pool = output["comparison_pool_candidate_ids"]
    supported = supported_dimensions(final)
    selected = selected_user_concepts(final) | set(
        final["state"]["k1"].get("confirmed_concepts", [])
    )
    named_dimensions = {
        dimension_id
        for candidate_id in pool
        for dimension_id in registry[candidate_id].get("support_dimension_ids", [])
    }
    rows = []
    for candidate_id in profile:
        dimensions = set(registry[candidate_id].get("support_dimension_ids", []))
        matched = sorted(dimensions & set(supported))
        evidence_concepts = {
            concept
            for dimension_id in matched
            for value in supported[dimension_id].get("support_evidence_ids", [])
            if (concept := concept_from_evidence_id(value)) is not None
        }
        rows.append(
            {
                "profile_id": candidate_id,
                "support_dimensions": sorted(dimensions),
                "matched_supported_dimensions": matched,
                "supported_by_k1": bool(matched),
                "support_evidence_concepts": sorted(evidence_concepts),
                "support_trace_reaches_selected_or_confirmed": bool(
                    evidence_concepts & selected
                ),
                "represented_by_named_output_dimension": bool(
                    dimensions & named_dimensions
                ),
            }
        )
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "profile_ids": profile,
        "profile_count": len(profile),
        "profile_rows": rows,
        "all_profiles_supported_by_k1": all(row["supported_by_k1"] for row in rows),
        "profile_pool_overlap_ids": sorted(set(profile) & set(pool)),
        "directions_without_named_representation": sorted(
            {
                dimension_id
                for row in rows
                if not row["represented_by_named_output_dimension"]
                for dimension_id in row["matched_supported_dimensions"]
            }
        ),
        "interpretation": (
            "A supported profile direction without a named-output counterpart is complementary "
            "coverage, not automatically a contradiction or user benefit."
        ),
    }


def profile_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        profile_rows = [row for case in rows for row in case["profile_rows"]]
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({case["group_id"] for case in rows}),
            "profile_count_distribution": dict(
                sorted(Counter(str(case["profile_count"]) for case in rows).items())
            ),
            "profile_occurrences": len(profile_rows),
            "unsupported_profile_occurrences": sum(
                not row["supported_by_k1"] for row in profile_rows
            ),
            "records_with_unsupported_profile": sum(
                not case["all_profiles_supported_by_k1"] for case in rows
            ),
            "profile_pool_overlap_records": sum(
                bool(case["profile_pool_overlap_ids"]) for case in rows
            ),
            "profile_occurrences_with_named_dimension_representation": sum(
                row["represented_by_named_output_dimension"] for row in profile_rows
            ),
            "profile_occurrences_without_named_dimension_representation": sum(
                not row["represented_by_named_output_dimension"] for row in profile_rows
            ),
            "profile_occurrences_with_selected_or_confirmed_support_trace": sum(
                row["support_trace_reaches_selected_or_confirmed"]
                for row in profile_rows
            ),
            "interpretation": (
                "Support and structural consistency are software/evidence-chain checks. They do "
                "not establish that participants find overall_profile helpful."
            ),
        }
    return result


def audit(
    actual_returns: Path,
    contract_path: Path,
    private_output_dir: Path,
    public_comparison_path: Path,
) -> dict[str, Any]:
    expected = read(R8_PUBLIC / "output_alignment_results.json")[
        "private_artifact_hashes"
    ]["actual_returns.private.json"]
    if sha256(actual_returns) != expected:
        raise ValueError("R8_ACTUAL_RETURNS_HASH_MISMATCH")
    registry = role_registry_from_contract(read(contract_path))
    if any(
        registry[candidate_id]["role"] != NAMED_DESCRIPTOR
        for candidate_id in MIDDLE_NAMED_IDS
    ):
        raise ValueError("MIDDLE_CATEGORY_ROLE_CONTRACT_CHANGED")
    sources = read(actual_returns)
    mechanisms = [mechanism_case(source, registry) for source in sources]
    evidence = [row for source in sources for row in evidence_rows(source, registry)]
    profiles = [profile_case(source, registry) for source in sources]
    summaries = {
        "mechanism_audit": mechanism_summary(mechanisms),
        "evidence_chain_audit": evidence_summary(evidence),
        "profile_quality_audit": profile_summary(profiles),
    }
    payloads = {
        "mechanism_audit.private.json": {
            "version": VERSION,
            "scope": "PRIVATE_R8_ACTUAL_RETURN_MECHANISM_AUDIT",
            "fit_count": 0,
            "source_actual_returns_sha256": expected,
            "summary": summaries["mechanism_audit"],
            "cases": mechanisms,
        },
        "evidence_audit.private.json": {
            "version": VERSION,
            "scope": "PRIVATE_CURRENT_ANSWER_TRACE_NOT_USER_EFFECT",
            "fit_count": 0,
            "source_actual_returns_sha256": expected,
            "summary": summaries["evidence_chain_audit"],
            "descriptor_occurrences": evidence,
        },
        "profile_audit.private.json": {
            "version": VERSION,
            "scope": "PRIVATE_PROFILE_SUPPORT_AND_CONSISTENCY_AUDIT",
            "fit_count": 0,
            "source_actual_returns_sha256": expected,
            "summary": summaries["profile_quality_audit"],
            "cases": profiles,
        },
    }
    artifacts = {
        name: save(private_output_dir / name, payload)
        for name, payload in payloads.items()
    }
    comparison = read(public_comparison_path)
    if comparison["source"]["actual_returns_sha256"] != expected:
        raise ValueError("PUBLIC_COMPARISON_SOURCE_MISMATCH")
    comparison["post_decision_audits"] = {
        "version": VERSION,
        "fit_count": 0,
        "scope": "AGGREGATES_ONLY_RAW_CASE_DETAILS_PRIVATE",
        **summaries,
        "private_artifacts": {
            name: {"sha256": value["sha256"], "bytes": value["bytes"]}
            for name, value in artifacts.items()
        },
    }
    public_comparison_path.write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n"
    )
    return comparison["post_decision_audits"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-returns", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=R9_PUBLIC / "output_policy_contract.json",
    )
    parser.add_argument("--private-output-dir", type=Path, required=True)
    parser.add_argument(
        "--public-comparison",
        type=Path,
        default=R9_PUBLIC / "policy_comparison.json",
    )
    args = parser.parse_args()
    result = audit(
        args.actual_returns,
        args.contract,
        args.private_output_dir,
        args.public_comparison,
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "fit_count": result["fit_count"],
                "C01_mechanism": result["mechanism_audit"]["C01"],
                "C01_evidence": result["evidence_chain_audit"]["C01"],
                "C01_profile": result["profile_quality_audit"]["C01"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
