#!/usr/bin/env python3
"""Deterministic R9 audits over registered support dimensions.

"Cluster" in this report means an existing ``support_dimension_id``.  The
script discovers no clusters, fits no weights, calibrates no probabilities and
changes no output.  T is used only after policy outputs exist for the descriptive
prefix-coverage curve.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

from acquire_supervision_r5 import save
import output_alignment_r8 as r8
from output_policy_r9 import (
    NAMED_DESCRIPTOR,
    PROFILE_DIRECTION,
    adapt_output,
    digest,
    role_registry_from_contract,
)

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.registered-dimension-structure.v1"
POLICIES = ("OUT_MIXED", "OUT_SEPARATED")
EPSILON = 1e-12


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["candidate_id"] for row in rows]


def registered_dimensions(registry: dict[str, Any]) -> list[str]:
    dimensions = {
        dimension_id
        for entry in registry.values()
        if entry["role"] == PROFILE_DIRECTION
        for dimension_id in entry.get("support_dimension_ids", [])
    }
    if len(dimensions) != 9:
        raise ValueError("NINE_REGISTERED_PROFILE_DIMENSIONS_REQUIRED")
    return sorted(dimensions)


def selected_answer_evidence(final: dict[str, Any]) -> list[dict[str, str]]:
    answers = final["state"]["base_state"].get("answers_by_question", {})
    result = []
    for slot, answer in sorted(answers.items()):
        question_id = answer.get("question_id")
        if not question_id:
            raise ValueError("QUESTION_ID_REQUIRED_FOR_SELECTED_EVIDENCE")
        for concept_id in answer.get("selected_option_ids", []):
            result.append(
                {
                    "slot": slot,
                    "question_id": question_id,
                    "concept_id": concept_id,
                }
            )
    return result


def evidence_reception_rows(
    source: dict[str, Any], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    final = source["actual_return"]
    separated = adapt_output(final, registry, "OUT_SEPARATED")
    main = row_ids(separated["main"])
    secondary = row_ids(separated["secondary"])
    profile = row_ids(separated["overall_profile"])
    rows = []
    for evidence in selected_answer_evidence(final):
        concept_id = evidence["concept_id"]
        if concept_id not in registry:
            raise ValueError("SELECTED_EVIDENCE_CONCEPT_NOT_REGISTERED:" + concept_id)
        dimensions = sorted(set(registry[concept_id].get("support_dimension_ids", [])))
        if not dimensions:
            continue
        evidence_id = (
            "answer-evidence:"
            + digest(
                {
                    "record_id": source["record_id"],
                    "question_id": evidence["question_id"],
                    "concept_id": concept_id,
                }
            )[:24]
        )
        membership_weight = 1.0 / len(dimensions)
        for dimension_id in dimensions:
            named_main = [
                candidate_id
                for candidate_id in main
                if dimension_id
                in registry[candidate_id].get("support_dimension_ids", [])
            ]
            named_secondary = [
                candidate_id
                for candidate_id in secondary
                if dimension_id
                in registry[candidate_id].get("support_dimension_ids", [])
            ]
            profile_ids = [
                candidate_id
                for candidate_id in profile
                if dimension_id
                in registry[candidate_id].get("support_dimension_ids", [])
            ]
            rows.append(
                {
                    "record_id": source["record_id"],
                    "group_id": source["group_id"],
                    "generator": source["policy"],
                    "evidence_id": evidence_id,
                    "question_id": evidence["question_id"],
                    "question_slot": evidence["slot"],
                    "source_concept_id": concept_id,
                    "dimension_id": dimension_id,
                    "uniform_membership_weight": membership_weight,
                    "source_dimension_count": len(dimensions),
                    "separated_main_named_ids_in_dimension": named_main,
                    "separated_secondary_named_ids_in_dimension": named_secondary,
                    "separated_profile_ids_in_dimension": profile_ids,
                    "dimension_participates_in_main": bool(named_main),
                    "dimension_participates_in_pool": bool(
                        named_main or named_secondary
                    ),
                    "dimension_participates_in_profile": bool(profile_ids),
                    "weight_semantics": (
                        "Uniform incidence normalization only; not learned support, belief, "
                        "confidence or Dempster-Shafer mass."
                    ),
                }
            )
    return rows


def reception_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        values = [row for row in rows if row["generator"] == generator]
        by_evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_dimension: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in values:
            by_evidence[row["evidence_id"]].append(row)
            by_dimension[row["dimension_id"]].append(row)
        weight_sum_violations = sum(
            abs(sum(row["uniform_membership_weight"] for row in links) - 1.0) > EPSILON
            for links in by_evidence.values()
        )
        result[generator] = {
            "evidence_dimension_links": len(values),
            "unique_selected_answer_evidence": len(by_evidence),
            "evidence_received_by_multiple_dimensions": sum(
                len(links) > 1 for links in by_evidence.values()
            ),
            "multi_dimension_evidence_ratio": (
                sum(len(links) > 1 for links in by_evidence.values()) / len(by_evidence)
                if by_evidence
                else None
            ),
            "dimensions_receiving_evidence": len(by_dimension),
            "mean_unique_evidence_per_receiving_dimension": (
                statistics.fmean(
                    len({row["evidence_id"] for row in links})
                    for links in by_dimension.values()
                )
                if by_dimension
                else None
            ),
            "uniform_weight_sum_violations": weight_sum_violations,
            "dimension_summary": {
                dimension_id: {
                    "links": len(links),
                    "unique_evidence": len({row["evidence_id"] for row in links}),
                    "uniform_weight_sum": sum(
                        row["uniform_membership_weight"] for row in links
                    ),
                    "links_participating_in_separated_main": sum(
                        row["dimension_participates_in_main"] for row in links
                    ),
                    "links_participating_in_separated_pool": sum(
                        row["dimension_participates_in_pool"] for row in links
                    ),
                    "links_participating_in_profile": sum(
                        row["dimension_participates_in_profile"] for row in links
                    ),
                }
                for dimension_id, links in sorted(by_dimension.items())
            },
            "interpretation": (
                "This is a multi-label incidence matrix over registered dimensions. A link "
                "count or uniform share is not evidence strength or uncertainty."
            ),
        }
    return result


def dimension_distribution(
    output: dict[str, Any], registry: dict[str, Any], dimensions: list[str]
) -> dict[str, Any]:
    weights = {dimension_id: 0.0 for dimension_id in dimensions}
    for row in output["main"] + output["secondary"]:
        candidate_dimensions = sorted(
            set(registry[row["candidate_id"]].get("support_dimension_ids", []))
        )
        if not candidate_dimensions:
            continue
        share = 1.0 / len(candidate_dimensions)
        for dimension_id in candidate_dimensions:
            weights[dimension_id] += share
    total = sum(weights.values())
    if total <= 0:
        return {
            "active_dimension_count": 0,
            "entropy": None,
            "normalized_entropy": None,
            "gini_all_registered_dimensions": None,
            "normalized_gini": None,
            "herfindahl_concentration": None,
            "raw_distribution": weights,
        }
    probabilities = {
        dimension_id: weight / total for dimension_id, weight in weights.items()
    }
    nonzero = [value for value in probabilities.values() if value > 0]
    entropy = -sum(value * math.log(value) for value in nonzero)
    ordered = sorted(probabilities.values())
    count = len(ordered)
    gini = (
        sum(
            (2 * index - count - 1) * value
            for index, value in enumerate(ordered, start=1)
        )
        / count
    )
    maximum_gini = (count - 1) / count
    return {
        "active_dimension_count": len(nonzero),
        "entropy": entropy,
        "normalized_entropy": entropy / math.log(count),
        "gini_all_registered_dimensions": gini,
        "normalized_gini": gini / maximum_gini,
        "herfindahl_concentration": sum(
            value * value for value in probabilities.values()
        ),
        "raw_distribution": weights,
        "probability_distribution": probabilities,
    }


def consensus_case(
    source: dict[str, Any], registry: dict[str, Any], dimensions: list[str]
) -> dict[str, Any]:
    outputs = {
        policy_id: adapt_output(source["actual_return"], registry, policy_id)
        for policy_id in POLICIES
    }
    metrics = {
        policy_id: dimension_distribution(output, registry, dimensions)
        for policy_id, output in outputs.items()
    }
    deltas = {
        metric: (
            metrics["OUT_SEPARATED"][metric] - metrics["OUT_MIXED"][metric]
            if metrics["OUT_SEPARATED"][metric] is not None
            and metrics["OUT_MIXED"][metric] is not None
            else None
        )
        for metric in (
            "active_dimension_count",
            "entropy",
            "normalized_entropy",
            "gini_all_registered_dimensions",
            "normalized_gini",
            "herfindahl_concentration",
        )
    }
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "policies": metrics,
        "delta_separated_minus_mixed": deltas,
        "scope_note": (
            "These are output-dimension concentration measures, not agreement among "
            "independent learned clusterings and not user-effect evidence."
        ),
    }


def group_macro(rows: list[dict[str, Any]], getter: Any) -> float | None:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = getter(row)
        if value is not None:
            groups[row["group_id"]].append(float(value))
    if not groups:
        return None
    return statistics.fmean(statistics.fmean(values) for values in groups.values())


def consensus_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    metrics = (
        "active_dimension_count",
        "normalized_entropy",
        "normalized_gini",
        "herfindahl_concentration",
    )
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({row["group_id"] for row in rows}),
            "coffee_group_macro": {
                policy_id: {
                    metric: group_macro(
                        rows, lambda row, p=policy_id, m=metric: row["policies"][p][m]
                    )
                    for metric in metrics
                }
                for policy_id in POLICIES
            },
            "coffee_group_macro_delta_separated_minus_mixed": {
                metric: group_macro(
                    rows,
                    lambda row, m=metric: row["delta_separated_minus_mixed"][m],
                )
                for metric in metrics
            },
            "record_directional_counts": {
                "separated_more_concentrated_by_HHI": sum(
                    row["delta_separated_minus_mixed"]["herfindahl_concentration"]
                    > EPSILON
                    for row in rows
                ),
                "separated_less_concentrated_by_HHI": sum(
                    row["delta_separated_minus_mixed"]["herfindahl_concentration"]
                    < -EPSILON
                    for row in rows
                ),
                "HHI_tie": sum(
                    abs(row["delta_separated_minus_mixed"]["herfindahl_concentration"])
                    <= EPSILON
                    for row in rows
                ),
            },
            "interpretation": (
                "Lower entropy and higher Gini/HHI mean concentration over the fixed nine "
                "registered dimensions. They do not demonstrate evidence-source consensus."
            ),
        }
    return result


def average_ranks(values: list[float], descending: bool = True) -> list[float]:
    order = sorted(
        range(len(values)), key=lambda index: values[index], reverse=descending
    )
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        rank = (start + 1 + end) / 2
        for index in order[start:end]:
            ranks[index] = rank
        start = end
    return ranks


def pearson(left: list[float], right: list[float]) -> float | None:
    if len(left) != len(right) or len(left) < 2:
        return None
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True)
    )
    left_scale = math.sqrt(sum((value - left_mean) ** 2 for value in left))
    right_scale = math.sqrt(sum((value - right_mean) ** 2 for value in right))
    if left_scale <= EPSILON or right_scale <= EPSILON:
        return None
    return numerator / (left_scale * right_scale)


def single_pass_case(
    source: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    final = source["actual_return"]
    supported = {
        dimension_id: float(value.get("supported", 0))
        for dimension_id, value in final["state"]["k1"]["dimensions"].items()
    }
    named_rows = [
        row
        for row in final["state"]["candidate_scores"]
        if registry[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR
    ]
    candidate_rows = []
    for row in named_rows:
        dimensions = sorted(
            set(registry[row["candidate_id"]].get("support_dimension_ids", []))
        )
        membership_weight = 1.0 / len(dimensions) if dimensions else 0.0
        static_vote = sum(
            supported.get(dimension_id, 0.0) * membership_weight
            for dimension_id in dimensions
        )
        candidate_rows.append(
            {
                "candidate_id": row["candidate_id"],
                "original_score": float(row["score"]),
                "support_dimensions": dimensions,
                "single_pass_uniform_dimension_vote": static_vote,
            }
        )
    scores = [row["original_score"] for row in candidate_rows]
    votes = [row["single_pass_uniform_dimension_vote"] for row in candidate_rows]
    rho = pearson(average_ranks(scores), average_ranks(votes))
    separated = adapt_output(final, registry, "OUT_SEPARATED")
    returned = set(separated["comparison_pool_candidate_ids"])
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "candidate_rows": candidate_rows,
        "spearman_rank_association": rho,
        "named_candidates": len(candidate_rows),
        "named_candidates_with_nonzero_vote": sum(value > 0 for value in votes),
        "separated_returned_with_nonzero_vote": sum(
            row["candidate_id"] in returned
            and row["single_pass_uniform_dimension_vote"] > 0
            for row in candidate_rows
        ),
        "separated_returned_count": len(returned),
        "factor_graph_single_pass_equals_cluster_vote_under_this_definition": True,
        "scope_note": (
            "Rank association is descriptive and tie-heavy. It cannot show that the frozen "
            "scorer learned, needs, or causally uses a factor graph."
        ),
    }


def single_pass_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({row["group_id"] for row in rows}),
            "evaluable_rank_association_records": sum(
                row["spearman_rank_association"] is not None for row in rows
            ),
            "coffee_group_macro_spearman_rank_association": group_macro(
                rows, lambda row: row["spearman_rank_association"]
            ),
            "mean_named_candidates_with_nonzero_vote": statistics.fmean(
                row["named_candidates_with_nonzero_vote"] for row in rows
            ),
            "mean_separated_returned_with_nonzero_vote": statistics.fmean(
                row["separated_returned_with_nonzero_vote"] for row in rows
            ),
            "factor_graph_and_ensemble_duplicate_computations_avoided": True,
            "interpretation": (
                "This static uniform vote is a diagnostic comparator, not a replacement score, "
                "learned ensemble, model recommendation or training result."
            ),
        }
    return result


def policy_full_order(
    final: dict[str, Any], registry: dict[str, Any], policy_id: str
) -> list[dict[str, Any]]:
    rows = final["state"]["candidate_scores"]
    if policy_id == "OUT_MIXED":
        return rows
    return [
        row for row in rows if registry[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR
    ]


def prefix_curve_case(
    source: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    final = source["actual_return"]
    result = {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "policies": {},
    }
    for policy_id in POLICIES:
        output = adapt_output(final, registry, policy_id)
        returned = output["main"] + output["secondary"]
        full_order = policy_full_order(final, registry, policy_id)
        if row_ids(returned) != row_ids(full_order[: len(returned)]):
            raise ValueError("POLICY_PREFIX_AND_FULL_ORDER_DISAGREE")
        points = []
        for k in range(1, min(8, len(returned)) + 1):
            prefix = returned[:k]
            score_values = [float(row["score"]) for row in prefix]
            metric = r8.measure(row_ids(prefix), source["full_T"], k)
            boundary_margin = (
                float(full_order[k - 1]["score"]) - float(full_order[k]["score"])
                if k < len(full_order)
                else None
            )
            points.append(
                {
                    "k": k,
                    "candidate_ids": row_ids(prefix),
                    "raw_gap": metric["raw_gap"],
                    "recall": metric["recall"],
                    "ndcg_actual_positions": metric["ndcg_actual_positions"],
                    "mean_raw_score": statistics.fmean(score_values),
                    "raw_score_boundary_margin": boundary_margin,
                }
            )
        result["policies"][policy_id] = points
    result["scope_note"] = (
        "k is the fixed returned prefix size, not a learned score threshold. Raw score means "
        "and margins are uncalibrated separations, not probabilities or user confidence."
    )
    return result


def curve_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({row["group_id"] for row in rows}),
            "policy_curves": {},
        }
        for policy_id in POLICIES:
            points = []
            for k in range(1, 9):

                def value(row: dict[str, Any], field: str) -> float | None:
                    point = next(
                        (item for item in row["policies"][policy_id] if item["k"] == k),
                        None,
                    )
                    return None if point is None else point[field]

                points.append(
                    {
                        "k": k,
                        "coffee_group_macro_recall": group_macro(
                            rows, lambda row: value(row, "recall")
                        ),
                        "coffee_group_macro_raw_gap": group_macro(
                            rows, lambda row: value(row, "raw_gap")
                        ),
                        "coffee_group_macro_ndcg": group_macro(
                            rows, lambda row: value(row, "ndcg_actual_positions")
                        ),
                        "coffee_group_macro_mean_raw_score": group_macro(
                            rows, lambda row: value(row, "mean_raw_score")
                        ),
                        "coffee_group_macro_raw_score_boundary_margin": group_macro(
                            rows,
                            lambda row: value(row, "raw_score_boundary_margin"),
                        ),
                    }
                )
            result[generator]["policy_curves"][policy_id] = points
        result[generator]["separated_minus_mixed"] = [
            {
                "k": k,
                **{
                    field: (
                        result[generator]["policy_curves"]["OUT_SEPARATED"][k - 1][
                            field
                        ]
                        - result[generator]["policy_curves"]["OUT_MIXED"][k - 1][field]
                    )
                    for field in (
                        "coffee_group_macro_recall",
                        "coffee_group_macro_raw_gap",
                        "coffee_group_macro_ndcg",
                        "coffee_group_macro_mean_raw_score",
                        "coffee_group_macro_raw_score_boundary_margin",
                    )
                },
            }
            for k in range(1, 9)
        ]
        result[generator]["interpretation"] = (
            "Recall/gap/NDCG use unchanged fine-reference metrics after output creation. Raw "
            "scores are uncalibrated and cannot establish confidence or choose a policy."
        )
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
    dimensions = registered_dimensions(registry)
    reception = [
        row for source in sources for row in evidence_reception_rows(source, registry)
    ]
    consensus = [consensus_case(source, registry, dimensions) for source in sources]
    single_pass = [single_pass_case(source, registry) for source in sources]
    curves = [prefix_curve_case(source, registry) for source in sources]
    summaries = {
        "evidence_dimension_reception": reception_summary(reception),
        "output_dimension_concentration": consensus_summary(consensus),
        "single_pass_dimension_vote_association": single_pass_summary(single_pass),
        "prefix_coverage_raw_score_curve": curve_summary(curves),
    }
    private_payload = {
        "version": VERSION,
        "scope": "PRIVATE_REGISTERED_DIMENSION_DETAILS_NO_FIT",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "registered_dimensions": dimensions,
        "evidence_dimension_matrix": reception,
        "output_dimension_concentration_cases": consensus,
        "single_pass_dimension_vote_cases": single_pass,
        "prefix_curve_cases": curves,
        "summary": summaries,
    }
    artifact = save(private_output_path, private_payload)
    public = {
        "version": VERSION,
        "status": "COMPLETE_ON_REBUILT_R8_ACTUAL_RETURNS",
        "fit_count": 0,
        "cluster_definition": (
            "Existing support_dimension_id only; no clustering, cluster fit, learned edge, "
            "message-passing iteration or new ontology."
        ),
        "source_actual_returns_sha256": expected,
        "registered_dimensions": dimensions,
        **summaries,
        "private_detail": {
            "status": "OWNER_CONTROLLED_STORAGE",
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
        },
        "guards": {
            "model_or_policy_parameter_changes": 0,
            "fit_count": 0,
            "output_policy_received_T": False,
            "T_used_only_after_outputs_for_descriptive_prefix_metrics": True,
            "new_cluster_or_edge_learning": False,
            "confidence_probability_claim": "NOT_MADE",
            "threshold_or_policy_selected": False,
            "user_effect_claim": "NOT_EVALUATED",
        },
        "interpretation_limits": [
            "Multi-dimension incidence does not imply Dempster-Shafer independence or calibrated mass.",
            "Dimension concentration is not consensus among independent clusterings or evidence sources.",
            "Static rank association cannot show that the current scorer learned or needs message passing.",
            "Fine-reference prefix coverage and uncalibrated score separation are separate diagnostics, not a composite objective.",
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
        default=R9_PUBLIC / "r9_extension_summary.json",
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
