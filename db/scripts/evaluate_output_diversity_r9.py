#!/usr/bin/env python3
"""Evaluate R9 output coverage, registered-dimension redundancy and fit.

This is a deterministic post-output audit over the sealed R8 actual returns.
It fits no model, selects no threshold, changes no policy and does not treat T as
an output-policy input.  Positive frozen T labels are read only after all three
policy outputs have been created and are used as the existing development-data
evaluation proxy.

The registered support dimensions are authored semantic groups, not learned
clusters.  The diversity-aware fit diagnostic uses the R8 one-to-one exact/shared-
parent matcher.  Its fixed alpha values are reported as a sensitivity series and
are not learned or combined into a product score.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any, Callable

from acquire_supervision_r5 import save
import output_alignment_r8 as r8
from output_policy_r9 import (
    NAMED_DESCRIPTOR,
    POLICIES,
    adapt_output,
    role_registry_from_contract,
)
from train_supervision_r5 import CANDIDATES

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.output-coverage-redundancy-fit.v1"
VIEWS = {"main": 5, "comparison_pool": 8}
ALPHAS = (0.0, 0.25, 0.5, 0.75)
EPSILON = 1e-12


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["candidate_id"] for row in rows]


def positive_targets(target_weights: dict[str, Any]) -> list[str]:
    targets = []
    for candidate_id, weight in target_weights.items():
        if (
            not isinstance(candidate_id, str)
            or not candidate_id
            or isinstance(weight, bool)
            or not isinstance(weight, (int, float))
            or not math.isfinite(weight)
            or weight < 0
        ):
            raise ValueError("INVALID_FROZEN_TARGET")
        if weight > 0:
            targets.append(candidate_id)
    return sorted(targets)


def candidate_dimensions(candidate_id: str, registry: dict[str, Any]) -> frozenset[str]:
    if candidate_id not in registry:
        raise ValueError("UNREGISTERED_CANDIDATE:" + candidate_id)
    return frozenset(registry[candidate_id].get("support_dimension_ids", []))


def dimensions_for_rows(
    rows: list[dict[str, Any]],
    registry: dict[str, Any],
    *,
    named_only: bool,
) -> set[str]:
    result: set[str] = set()
    for row in rows:
        candidate_id = row["candidate_id"]
        if named_only and registry[candidate_id]["role"] != NAMED_DESCRIPTOR:
            continue
        result.update(candidate_dimensions(candidate_id, registry))
    return result


def safe_ratio(numerator: int | float, denominator: int | float) -> float | None:
    return float(numerator) / denominator if denominator else None


def coverage_metrics(
    rows: list[dict[str, Any]],
    targets: list[str],
    registry: dict[str, Any],
) -> dict[str, Any]:
    target_dimensions = {
        dimension_id
        for target in targets
        for dimension_id in candidate_dimensions(target, registry)
    }
    all_output_dimensions = dimensions_for_rows(rows, registry, named_only=False)
    named_output_dimensions = dimensions_for_rows(rows, registry, named_only=True)

    def measures(output_dimensions: set[str]) -> dict[str, Any]:
        overlap = output_dimensions & target_dimensions
        union = output_dimensions | target_dimensions
        if not target_dimensions:
            recall = precision = jaccard = None
        else:
            recall = safe_ratio(len(overlap), len(target_dimensions))
            precision = safe_ratio(len(overlap), len(output_dimensions))
            jaccard = safe_ratio(len(overlap), len(union))
        return {
            "target_dimension_recall": recall,
            "output_dimension_precision": precision,
            "dimension_jaccard": jaccard,
            "covered_target_dimension_count": len(overlap),
            "missing_target_dimension_count": len(
                target_dimensions - output_dimensions
            ),
            "extra_output_dimension_count": len(output_dimensions - target_dimensions),
            "output_dimension_count": len(output_dimensions),
        }

    return {
        "target_count": len(targets),
        "target_dimension_count": len(target_dimensions),
        "evaluable": bool(target_dimensions),
        "all_roles": measures(all_output_dimensions),
        "named_only": measures(named_output_dimensions),
        "scope_note": (
            "Recall is paired with precision and Jaccard so unrelated dimensions cannot "
            "improve the audit by coverage alone. T dimensions are a frozen expert-target "
            "proxy, not participant perception."
        ),
    }


def redundancy_metrics(
    rows: list[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    named = [
        row for row in rows if registry[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR
    ]
    signatures = [candidate_dimensions(row["candidate_id"], registry) for row in named]
    nonempty = [signature for signature in signatures if signature]
    active_dimensions = set().union(*nonempty) if nonempty else set()
    membership_links = sum(len(signature) for signature in nonempty)
    repeated_membership_links = max(0, membership_links - len(active_dimensions))

    pair_jaccards = []
    identical_signature_pairs = 0
    for left_index, left in enumerate(nonempty):
        for right in nonempty[left_index + 1 :]:
            union = left | right
            pair_jaccards.append(len(left & right) / len(union))
            identical_signature_pairs += left == right

    prior_dimensions: set[str] = set()
    repeated_rows = 0
    repeat_opportunities = 0
    for signature in signatures:
        if not signature:
            continue
        if prior_dimensions:
            repeat_opportunities += 1
            repeated_rows += bool(signature & prior_dimensions)
        prior_dimensions.update(signature)

    return {
        "named_descriptor_count": len(named),
        "active_named_dimension_count": len(active_dimensions),
        "named_descriptors_per_active_dimension": safe_ratio(
            len(named), len(active_dimensions)
        ),
        "dimension_membership_links": membership_links,
        "repeated_dimension_membership_rate": safe_ratio(
            repeated_membership_links, membership_links
        ),
        "mean_pairwise_dimension_jaccard": (
            statistics.fmean(pair_jaccards) if pair_jaccards else None
        ),
        "identical_dimension_signature_pair_rate": safe_ratio(
            identical_signature_pairs, len(pair_jaccards)
        ),
        "ordered_repeated_dimension_row_rate": safe_ratio(
            repeated_rows, repeat_opportunities
        ),
        "pair_count": len(pair_jaccards),
        "scope_note": (
            "These are coarse registered-dimension overlap proxies, not semantic "
            "duplicate labels or an absolute good/bad threshold. Descriptor load is "
            "reported separately from overlap rates."
        ),
    }


def diversity_adjusted_fit(
    rows: list[dict[str, Any]],
    targets: list[str],
    registry: dict[str, Any],
    *,
    alpha: float,
    declared_budget: int,
) -> dict[str, Any]:
    if not 0 <= alpha < 1:
        raise ValueError("ALPHA_OUTSIDE_FIXED_DIAGNOSTIC_RANGE")
    if declared_budget < 1:
        raise ValueError("POSITIVE_DECLARED_BUDGET_REQUIRED")
    if not targets:
        return {
            "alpha": alpha,
            "evaluable": False,
            "alpha_dcg": None,
            "optimistic_idcg": None,
            "alpha_ndcg_optimistic": None,
            "final_one_to_one_match_sum": None,
            "position_gains": [],
        }

    fine_universe = frozenset(CANDIDATES)
    eligible_prefix: list[str] = []
    seen_dimensions: dict[str, int] = defaultdict(int)
    previous_match = 0.0
    dcg = 0.0
    position_gains = []
    for position, row in enumerate(rows):
        candidate_id = row["candidate_id"]
        if candidate_id in fine_universe and candidate_id not in eligible_prefix:
            eligible_prefix.append(candidate_id)
        match = float(r8.matching(eligible_prefix, targets, position + 1))
        marginal_match = match - previous_match
        if marginal_match < -EPSILON or marginal_match > 1 + EPSILON:
            raise ValueError("ONE_CANDIDATE_MATCH_INCREMENT_OUT_OF_RANGE")
        marginal_match = min(1.0, max(0.0, marginal_match))

        dimensions = candidate_dimensions(candidate_id, registry)
        novelty_multiplier = (
            statistics.fmean(
                (1 - alpha) ** seen_dimensions[dimension_id]
                for dimension_id in sorted(dimensions)
            )
            if dimensions
            else 1.0
        )
        adjusted_gain = marginal_match * novelty_multiplier
        discounted_gain = adjusted_gain / math.log2(position + 2)
        dcg += discounted_gain
        position_gains.append(
            {
                "position": position + 1,
                "candidate_id": candidate_id,
                "one_to_one_marginal_match_gain": marginal_match,
                "dimension_novelty_multiplier": novelty_multiplier,
                "discounted_adjusted_gain": discounted_gain,
            }
        )
        for dimension_id in dimensions:
            seen_dimensions[dimension_id] += 1
        previous_match = match

    ideal_slots = min(declared_budget, len(targets))
    optimistic_idcg = sum(
        1.0 / math.log2(position + 2) for position in range(ideal_slots)
    )
    normalized = dcg / optimistic_idcg if optimistic_idcg > 0 else None
    if normalized is not None and not -EPSILON <= normalized <= 1 + EPSILON:
        raise ValueError("OPTIMISTIC_NORMALIZED_DIVERSITY_FIT_OUT_OF_RANGE")
    return {
        "alpha": alpha,
        "evaluable": True,
        "alpha_dcg": dcg,
        "optimistic_idcg": optimistic_idcg,
        "alpha_ndcg_optimistic": (
            min(1.0, max(0.0, normalized)) if normalized is not None else None
        ),
        "final_one_to_one_match_sum": previous_match,
        "position_gains": position_gains,
        "normalizer_scope": (
            "Optimistic upper bound: one new exact target with no dimension-repeat "
            "penalty per available ideal slot."
        ),
    }


def rows_for_view(output: dict[str, Any], view: str) -> list[dict[str, Any]]:
    if view == "main":
        return output["main"]
    if view == "comparison_pool":
        return output["main"] + output["secondary"]
    if view == "pool_plus_profile":
        return output["main"] + output["secondary"] + output["overall_profile"]
    raise ValueError("UNKNOWN_OUTPUT_VIEW")


def case_metrics(source: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    # Policy construction intentionally completes before positive targets are read.
    outputs = {
        policy_id: adapt_output(source["actual_return"], registry, policy_id)
        for policy_id in POLICIES
    }
    targets = positive_targets(source["full_T"])
    policies = {}
    for policy_id, output in outputs.items():
        views = {}
        for view, budget in VIEWS.items():
            rows = rows_for_view(output, view)
            r8_metrics = r8.measure(row_ids(rows), source["full_T"], budget)
            fits = {
                str(alpha): diversity_adjusted_fit(
                    rows,
                    targets,
                    registry,
                    alpha=alpha,
                    declared_budget=budget,
                )
                for alpha in ALPHAS
            }
            if (
                targets
                and abs(
                    fits["0.0"]["final_one_to_one_match_sum"] - r8_metrics["match_sum"]
                )
                > EPSILON
            ):
                raise ValueError("DIVERSITY_MATCH_AND_R8_MATCH_DISAGREE")
            views[view] = {
                "candidate_ids": row_ids(rows),
                "coverage": coverage_metrics(rows, targets, registry),
                "redundancy": redundancy_metrics(rows, registry),
                "diversity_adjusted_fit": fits,
                "r8_reference": {
                    "raw_gap": r8_metrics["raw_gap"],
                    "exact_recall": r8_metrics["recall"],
                    "ndcg_actual_positions": r8_metrics["ndcg_actual_positions"],
                },
            }
        surface_rows = rows_for_view(output, "pool_plus_profile")
        policies[policy_id] = {
            "views": views,
            "pool_plus_profile_coverage": coverage_metrics(
                surface_rows, targets, registry
            ),
            "overall_profile_candidate_ids": row_ids(output["overall_profile"]),
        }
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "target_evaluable": bool(targets),
        "policies": policies,
        "specific_first_separated_content_equivalence": {
            view: (
                policies["OUT_SPECIFIC_FIRST"]["views"][view]["candidate_ids"]
                == policies["OUT_SEPARATED"]["views"][view]["candidate_ids"]
            )
            for view in VIEWS
        },
    }


def group_macro(
    cases: list[dict[str, Any]], getter: Callable[[dict[str, Any]], float | None]
) -> float | None:
    groups: dict[str, list[float]] = defaultdict(list)
    for case in cases:
        value = getter(case)
        if value is not None:
            groups[case["group_id"]].append(float(value))
    if not groups:
        return None
    return statistics.fmean(statistics.fmean(values) for values in groups.values())


def directional_counts(
    cases: list[dict[str, Any]],
    left: Callable[[dict[str, Any]], float | None],
    right: Callable[[dict[str, Any]], float | None],
) -> dict[str, int]:
    deltas = []
    for case in cases:
        left_value, right_value = left(case), right(case)
        if left_value is not None and right_value is not None:
            deltas.append(right_value - left_value)
    return {
        "evaluable_records": len(deltas),
        "separated_higher": sum(delta > EPSILON for delta in deltas),
        "separated_lower": sum(delta < -EPSILON for delta in deltas),
        "tie": sum(abs(delta) <= EPSILON for delta in deltas),
    }


def view_metric_getter(
    policy_id: str, view: str, section: str, metric: str
) -> Callable[[dict[str, Any]], float | None]:
    return lambda case: case["policies"][policy_id]["views"][view][section][metric]


def alpha_getter(
    policy_id: str, view: str, alpha: float
) -> Callable[[dict[str, Any]], float | None]:
    return lambda case: case["policies"][policy_id]["views"][view][
        "diversity_adjusted_fit"
    ][str(alpha)]["alpha_ndcg_optimistic"]


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    coverage_metrics_to_report = (
        "target_dimension_recall",
        "output_dimension_precision",
        "dimension_jaccard",
    )
    redundancy_metrics_to_report = (
        "named_descriptors_per_active_dimension",
        "repeated_dimension_membership_rate",
        "mean_pairwise_dimension_jaccard",
        "identical_dimension_signature_pair_rate",
        "ordered_repeated_dimension_row_rate",
    )
    r8_metrics_to_report = ("raw_gap", "exact_recall", "ndcg_actual_positions")
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        generator_result = {
            "records": len(rows),
            "coffee_groups": len({case["group_id"] for case in rows}),
            "target_evaluable_records": sum(case["target_evaluable"] for case in rows),
            "target_evaluable_coffee_groups": len(
                {case["group_id"] for case in rows if case["target_evaluable"]}
            ),
            "specific_first_separated_content_equivalence": {
                view: sum(
                    case["specific_first_separated_content_equivalence"][view]
                    for case in rows
                )
                for view in VIEWS
            },
            "views": {},
        }
        for view in VIEWS:
            view_result: dict[str, Any] = {
                "policy_means": {},
                "separated_minus_mixed": {},
                "directional_counts_separated_vs_mixed": {},
            }
            for policy_id in POLICIES:
                view_result["policy_means"][policy_id] = {}
                # Coverage has one additional nesting level; populate explicitly.
                view_result["policy_means"][policy_id]["coverage_all_roles"] = {
                    metric: group_macro(
                        rows,
                        lambda case, p=policy_id, v=view, m=metric: case["policies"][p][
                            "views"
                        ][v]["coverage"]["all_roles"][m],
                    )
                    for metric in coverage_metrics_to_report
                }
                view_result["policy_means"][policy_id]["coverage_named_only"] = {
                    metric: group_macro(
                        rows,
                        lambda case, p=policy_id, v=view, m=metric: case["policies"][p][
                            "views"
                        ][v]["coverage"]["named_only"][m],
                    )
                    for metric in coverage_metrics_to_report
                }
                view_result["policy_means"][policy_id]["redundancy"] = {
                    metric: group_macro(
                        rows,
                        view_metric_getter(policy_id, view, "redundancy", metric),
                    )
                    for metric in redundancy_metrics_to_report
                }
                view_result["policy_means"][policy_id]["diversity_adjusted_fit"] = {
                    str(alpha): group_macro(rows, alpha_getter(policy_id, view, alpha))
                    for alpha in ALPHAS
                }
                view_result["policy_means"][policy_id]["r8_reference"] = {
                    metric: group_macro(
                        rows,
                        view_metric_getter(policy_id, view, "r8_reference", metric),
                    )
                    for metric in r8_metrics_to_report
                }

            paths: dict[str, tuple[str, ...]] = {}
            for scope in ("coverage_all_roles", "coverage_named_only"):
                for metric in coverage_metrics_to_report:
                    paths[f"{scope}.{metric}"] = (scope, metric)
            for metric in redundancy_metrics_to_report:
                paths[f"redundancy.{metric}"] = ("redundancy", metric)
            for alpha in ALPHAS:
                paths[f"diversity_adjusted_fit.alpha_{alpha}"] = (
                    "diversity_adjusted_fit",
                    str(alpha),
                )
            for metric in r8_metrics_to_report:
                paths[f"r8_reference.{metric}"] = ("r8_reference", metric)

            for label, path in paths.items():
                mixed_value = view_result["policy_means"]["OUT_MIXED"]
                separated_value = view_result["policy_means"]["OUT_SEPARATED"]
                for key in path:
                    mixed_value = mixed_value[key]
                    separated_value = separated_value[key]
                view_result["separated_minus_mixed"][label] = (
                    separated_value - mixed_value
                    if separated_value is not None and mixed_value is not None
                    else None
                )

                def case_value(
                    case: dict[str, Any], policy_id: str, keys: tuple[str, ...] = path
                ) -> float | None:
                    value: Any = case["policies"][policy_id]["views"][view]
                    first, *remaining = keys
                    if first.startswith("coverage_"):
                        value = value["coverage"][
                            (
                                "all_roles"
                                if first == "coverage_all_roles"
                                else "named_only"
                            )
                        ]
                    else:
                        value = value[first]
                    for key in remaining:
                        value = value[key]
                    if first == "diversity_adjusted_fit":
                        value = value["alpha_ndcg_optimistic"]
                    return value

                view_result["directional_counts_separated_vs_mixed"][label] = (
                    directional_counts(
                        rows,
                        lambda case, p="OUT_MIXED": case_value(case, p),
                        lambda case, p="OUT_SEPARATED": case_value(case, p),
                    )
                )
            generator_result["views"][view] = view_result

        generator_result["pool_plus_profile_coverage_means"] = {
            policy_id: {
                scope: {
                    metric: group_macro(
                        rows,
                        lambda case, p=policy_id, s=scope, m=metric: case["policies"][
                            p
                        ]["pool_plus_profile_coverage"][s][m],
                    )
                    for metric in coverage_metrics_to_report
                }
                for scope in ("all_roles", "named_only")
            }
            for policy_id in POLICIES
        }
        result[generator] = generator_result
    return result


def c01_deconstruction(summary: dict[str, Any]) -> dict[str, Any]:
    c01 = summary["C01"]
    result: dict[str, Any] = {
        "evaluation_scope": {
            "records": c01["records"],
            "coffee_groups": c01["coffee_groups"],
            "target_evaluable_records": c01["target_evaluable_records"],
            "target_evaluable_coffee_groups": c01["target_evaluable_coffee_groups"],
            "independent_confirmation": False,
        },
        "specific_first_separated_content_equivalence": c01[
            "specific_first_separated_content_equivalence"
        ],
        "views": {},
    }
    for view in VIEWS:
        data = c01["views"][view]
        delta = data["separated_minus_mixed"]
        result["views"][view] = {
            "all_role_target_dimension_recall_delta": delta[
                "coverage_all_roles.target_dimension_recall"
            ],
            "all_role_output_dimension_precision_delta": delta[
                "coverage_all_roles.output_dimension_precision"
            ],
            "all_role_dimension_jaccard_delta": delta[
                "coverage_all_roles.dimension_jaccard"
            ],
            "named_only_target_dimension_recall_delta": delta[
                "coverage_named_only.target_dimension_recall"
            ],
            "named_only_output_dimension_precision_delta": delta[
                "coverage_named_only.output_dimension_precision"
            ],
            "named_only_dimension_jaccard_delta": delta[
                "coverage_named_only.dimension_jaccard"
            ],
            "repeated_dimension_membership_rate_delta": delta[
                "redundancy.repeated_dimension_membership_rate"
            ],
            "mean_pairwise_dimension_jaccard_delta": delta[
                "redundancy.mean_pairwise_dimension_jaccard"
            ],
            "alpha_0_5_diversity_adjusted_fit_delta": delta[
                "diversity_adjusted_fit.alpha_0.5"
            ],
            "alpha_0_5_directional_counts": data[
                "directional_counts_separated_vs_mixed"
            ]["diversity_adjusted_fit.alpha_0.5"],
        }

    separated_pool = c01["views"]["comparison_pool"]["policy_means"]["OUT_SEPARATED"][
        "coverage_all_roles"
    ]
    separated_surface = c01["pool_plus_profile_coverage_means"]["OUT_SEPARATED"][
        "all_roles"
    ]
    result["overall_profile_increment_over_separated_pool"] = {
        metric: separated_surface[metric] - separated_pool[metric]
        for metric in (
            "target_dimension_recall",
            "output_dimension_precision",
            "dimension_jaccard",
        )
    }
    result["interpretation"] = [
        "OUT_SEPARATED improves old-target dimension recall and one-to-one diversity-adjusted fit, but it also increases registered-dimension overlap redundancy.",
        "All-role dimension precision and Jaccard do not improve consistently, so coverage gain is not a uniform dimension-fit win.",
        "The alpha sensitivity series keeps the fit delta positive, but no alpha is an owner-approved or user-derived utility weight.",
        "Current OUT_SPECIFIC_FIRST and OUT_SEPARATED main/comparison content are identical, so these metrics cannot distinguish their current comparison pools; profile remains a separate role question.",
    ]
    return result


def analyze(
    actual_returns_path: Path,
    contract_path: Path,
    private_output_path: Path,
    public_output_path: Path,
) -> dict[str, Any]:
    expected = read(R8_PUBLIC / "output_alignment_results.json")[
        "private_artifact_hashes"
    ]["actual_returns.private.json"]
    if sha256(actual_returns_path) != expected:
        raise ValueError("R8_ACTUAL_RETURNS_HASH_MISMATCH")
    sources = read(actual_returns_path)
    registry = role_registry_from_contract(read(contract_path))
    cases = [case_metrics(source, registry) for source in sources]
    summary = summarize(cases)
    private_payload = {
        "version": VERSION,
        "scope": "PRIVATE_DEVELOPMENT_TARGET_CASE_METRICS_NO_FIT",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "alpha_sensitivity_values": list(ALPHAS),
        "cases": cases,
        "summary": summary,
    }
    artifact = save(private_output_path, private_payload)
    public = {
        "version": VERSION,
        "status": "COMPLETE_ON_REBUILT_R8_ACTUAL_RETURNS",
        "fit_count": 0,
        "purpose": (
            "Deconstruct the rejected concentration-as-quality hypothesis into separately "
            "reported target-dimension coverage, registered-dimension redundancy proxies "
            "and diversity-adjusted one-to-one fit."
        ),
        "source_actual_returns_sha256": expected,
        "policies": list(POLICIES),
        "views": VIEWS,
        "alpha_sensitivity_values": list(ALPHAS),
        "metric_contract": {
            "coverage": (
                "Recall of frozen positive-T dimensions, always accompanied by output-"
                "dimension precision and Jaccard. Reported for all flavor roles and named "
                "descriptors only."
            ),
            "redundancy": (
                "Named-descriptor load, repeated dimension memberships, pairwise dimension "
                "overlap, identical dimension signatures and ordered repeated-dimension rows."
            ),
            "diversity_adjusted_fit": (
                "R8 one-to-one exact/shared-parent marginal match gain, rank discount and "
                "registered-dimension novelty multiplier; normalized by an optimistic exact-"
                "target/no-repeat upper bound."
            ),
            "fixed_alpha_policy": (
                "0.0, 0.25, 0.5 and 0.75 are sensitivity points supplied for audit. None "
                "is learned, selected or treated as a product tradeoff weight."
            ),
        },
        "c01_deconstruction": c01_deconstruction(summary),
        "summary": summary,
        "private_detail": {
            "status": "OWNER_CONTROLLED_STORAGE",
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
        },
        "guards": {
            "fit_count": 0,
            "model_or_policy_parameter_changes": 0,
            "output_policy_received_T": False,
            "T_used_only_after_all_outputs_created": True,
            "metric_weight_learned_or_selected": False,
            "composite_product_score_created": False,
            "independent_confirmation_claim": "NOT_MADE",
            "user_effect_claim": "NOT_EVALUATED",
            "concentration_used_as_quality_target": False,
        },
        "interpretation_limits": [
            "Frozen T is an old development expert-target proxy, not participant perception or independent confirmation.",
            "Registered-dimension overlap is coarser than semantic redundancy; same-dimension descriptors are not automatically synonyms.",
            "A broad or middle descriptor can be valid product language while receiving no R8 fine-reference match credit.",
            "Coverage, redundancy and fit remain separate; no owner-approved or user-derived tradeoff weights exist.",
        ],
    }
    public_output_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return public


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-returns", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=R9_PUBLIC / "output_policy_contract.json",
    )
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=R9_PUBLIC / "r9_diversity_metrics.json",
    )
    args = parser.parse_args()
    result = analyze(
        args.actual_returns, args.contract, args.private_output, args.output
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "fit_count": result["fit_count"],
                "output": str(args.output),
                "private_sha256": result["private_detail"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
