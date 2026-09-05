#!/usr/bin/env python3
"""Aggregate fixed-scope R2 trajectories and price the one final comparison."""

from __future__ import annotations

import argparse
import copy
from collections import defaultdict
from pathlib import Path

import numpy as np

import alignment_metrics_r2 as metric
import flavor_coordination_r2 as runtime
import flavor_m2_r1 as r1
import train_coordination_r2 as training
from run_m2_r1 import read, save, sha
from run_m2_r2 import OUT, verify_frozen, private_save

VARIANTS = ["G0", "G1", "G2", "G3"]


def matching_rows(experiment, baseline):
    """Matched comparisons may differ in path/model but not cases or targets."""

    def key(row):
        return row["record_id"]

    a, b = {key(r): r for r in experiment}, {key(r): r for r in baseline}
    if len(a) != len(experiment) or len(b) != len(baseline) or set(a) != set(b):
        raise ValueError("COMPARISON_REQUIRES_ONE_MATCHED_ROW_PER_RECORD")
    for name in a:
        if (
            a[name]["group_id"] != b[name]["group_id"]
            or a[name]["target_sha256"] != b[name]["target_sha256"]
            or a[name]["visible_sha256"] != b[name]["visible_sha256"]
            or a[name]["candidate_vocabulary"] != b[name]["candidate_vocabulary"]
        ):
            raise ValueError("FIXED_COFFEE_TARGET_COMPARISON_REQUIRED")
    return a, b


def summary(rows):
    return {
        "alignment": metric.grouped_summary(rows),
        "actual_top5_alignment": metric.grouped_summary(
            rows, "actual_display_top5_gap"
        ),
        "direct_retention5": metric.grouped_summary(rows, "direct_retention5"),
        "cost": {
            key: metric.grouped_summary(rows, key)
            for key in [
                "ordinary_questions",
                "ordinary_options",
                "final_comparison_candidates",
            ]
        },
        "output_coverage": (
            sum(
                r.get("full_output_available", r.get("prediction_available", False))
                for r in rows
            )
            / len(rows)
            if rows
            else None
        ),
        "candidate_target_coverage": metric.grouped_summary(
            rows, "candidate_target_coverage"
        ),
        "fine_target_count": metric.grouped_summary(rows, "target_count"),
        "human_response_seconds": None,
    }


def paired(experiment, baseline, equal_budget=True):
    a, b = matching_rows(experiment, baseline)
    if equal_budget:
        for name in a:
            if any(
                a[name][k] != b[name][k]
                for k in [
                    "ordinary_questions",
                    "ordinary_options",
                    "final_comparison_candidates",
                ]
            ):
                raise ValueError("FIXED_BUDGET_CONTRAST_HAS_DIFFERENT_ACTUAL_COST")
    return metric.paired_group_delta(experiment, baseline)


def endpoint_rows(rows, model, path):
    return [
        r
        for r in rows
        if r["model"] == model and r["path"] == path and r["ordinary_endpoint"]
    ]


def final_feedback(owner, contract):
    destination = owner / "revisions/r2"
    cache = destination / "coordination_final_feedback.private.json"
    plan_path = destination / "coordination_final_feedback_plan.private.json"
    plan = {
        "contract_sha256": sha(OUT / "objective_and_metric_contract.json"),
        "coordinator_sha256": {
            str(i): sha(destination / f"models/R2_COORDINATOR_outer{i}.model.json")
            for i in range(3)
        },
        "runtime_sha256": sha(Path(runtime.__file__)),
        "feedback_rule": "ALL_ACTUALLY_EXPOSED_FINE_CANDIDATES_INTERSECT_FIXED_VISIBLE_A; NEVER_T",
        "variants": VARIANTS,
        "paths": contract["descriptor_inputs"]["paths"],
        "comparison_cost": "Actual exposed 3-to-8 candidate count; never treated as free information",
    }
    if cache.exists():
        if read(plan_path) != plan:
            raise ValueError("FINAL_FEEDBACK_CACHE_PROTOCOL_CHANGED")
        return read(cache)
    private_save(plan_path, plan)
    result = []
    for fold in range(3):
        bundle = read(destination / f"models/R2_COORDINATOR_outer{fold}.model.json")
        rows = read(destination / f"oof/experts_outer{fold}_held.private.json")
        for row in rows:
            if not row["ordinary_endpoint"]:
                continue
            visible, hidden = set(row["episode"]["visible"]), set(
                row["episode"]["hidden"]
            )
            if visible & hidden:
                raise ValueError("VISIBLE_AND_EVALUATION_TARGET_OVERLAP")
            for variant in VARIANTS:
                state = runtime.wrap_state(row["base_state"], bundle, variant)
                before = runtime.finalize_result(state, bundle)
                exposure = before["exposure"]
                if not exposure or not exposure["eligible_for_final_comparison"]:
                    raise ValueError(
                        "FINAL_COMPARISON_COVERAGE_FAILURE_MUST_BE_RETAINED"
                    )
                selected = [c for c in exposure["candidate_ids"] if c in visible]
                old_evidence = r1.evidence(state["base_state"], bundle["r1_expert"])
                confirmed = set(old_evidence["confirmed"])
                supported = set(old_evidence["broad"]) | {
                    a for c in confirmed for a in r1.PARENTS.get(c, [])
                }
                categories = set()
                for c in selected:
                    categories.add(
                        "REPEATED_INFORMATION"
                        if c in confirmed
                        else (
                            "BROAD_TO_SPECIFIC"
                            if set(r1.PARENTS.get(c, [])) & supported
                            else "NEW_VISIBLE_A_INFORMATION"
                        )
                    )
                feedback = {
                    "exposed_candidates": exposure["candidate_ids"],
                    "selected_candidates": selected,
                    "feedback_source": "SIMULATED",
                    "generation_version": bundle["bundle_id"],
                }
                after = runtime.apply_final_comparison(
                    before["state"], feedback, bundle
                )
                final = runtime.finalize_result(after, bundle)
                if (
                    final["stage"] != "FINAL_RESULT"
                    or final["next"]["action"] != "FINAL_RESULT"
                ):
                    raise ValueError("FINAL_FEEDBACK_MUST_TERMINATE")
                newrow = copy.deepcopy(row)
                newrow["base_state"] = after["base_state"]
                newrow["predictions"] = runtime.expert_predictions(
                    after["base_state"], bundle
                )
                newrow["cost"] = metric.information_cost(after["base_state"])
                newrow["runtime_stage"] = "FINAL_RESULT"
                values = training.result_row(
                    newrow,
                    after["candidate_scores"],
                    variant,
                    bundle["candidate_vocabulary"],
                    {
                        "weights": after["routing_weights"],
                        "features": after["routing_features"],
                    },
                )
                old_scores = {
                    r["candidate_id"]: r["score"]
                    for r in before["state"]["candidate_scores"]
                }
                change = max(
                    abs(r["score"] - old_scores[r["candidate_id"]])
                    for r in after["candidate_scores"]
                )
                if categories <= {"REPEATED_INFORMATION"} and change > 1e-12:
                    raise ValueError("REPEATED_FINAL_EVIDENCE_CHANGED_SCORE")
                values.update(
                    feedback_categories=sorted(categories) or ["EMPTY_SELECTION"],
                    feedback_selected_count=len(selected),
                    score_change_max=change,
                    exposed_candidates=exposure["candidate_ids"],
                    selected_candidates=selected,
                    generation_version=bundle["bundle_id"],
                    pre_gap=metric.semantic_gap(
                        before["state"]["candidate_scores"],
                        row["episode"]["hidden"],
                        row["episode"]["visible"],
                        vocabulary=bundle["candidate_vocabulary"],
                    ),
                )
                result.append(values)
        print("R2_FINAL_FEEDBACK_FOLD=" + str(fold), flush=True)
    private_save(cache, result)
    return result


def threshold_summary(rows, threshold=0.5):
    """Attainment is descriptive: hidden references never choose a live stop."""
    if any(not row["ordinary_endpoint"] for row in rows):
        raise ValueError("THRESHOLD_COST_ONLY_LEGAL_ENDPOINTS")
    records = defaultdict(list)
    for row in rows:
        records[row["record_id"]].append(row)
    case_results = []
    for _, options in records.items():
        known = any(r["gap"] is not None for r in options)
        reached = [r for r in options if r["gap"] is not None and r["gap"] <= threshold]
        chosen = (
            min(
                reached,
                key=lambda r: (
                    r["ordinary_options"],
                    r["final_comparison_candidates"],
                    r["path"],
                ),
            )
            if reached
            else None
        )
        case_results.append(
            {
                "group_id": options[0]["group_id"],
                "reference_identifiable": int(known),
                "reached": int(bool(reached)) if known else None,
                "reached_options": chosen["ordinary_options"] if chosen else None,
                "reached_final_candidates": (
                    chosen["final_comparison_candidates"] if chosen else None
                ),
            }
        )
    return {
        "records": len(case_results),
        "unidentifiable_records_retained": sum(
            not r["reference_identifiable"] for r in case_results
        ),
        "not_reached_labelled_records": sum(r["reached"] == 0 for r in case_results),
        "attainment": metric.grouped_summary(case_results, "reached"),
        "conditional_cost_among_reached_only": metric.grouped_summary(
            case_results, "reached_options"
        ),
        "conditional_final_candidates_among_reached_only": metric.grouped_summary(
            case_results, "reached_final_candidates"
        ),
        "interpretation": "Retrospective threshold attainment only. Conditional cost is not an all-case saving; no live policy can access T or end at an illegal prefix.",
    }


def information_efficiency(shorter, longer, margin):
    a, b = matching_rows(shorter, longer)
    delta = metric.paired_group_delta(shorter, longer)
    if any((a[k]["gap"] is None) != (b[k]["gap"] is None) for k in a):
        raise ValueError("INFORMATION_COST_ALIGNMENT_MASKS_DIFFER")
    evaluable = [k for k in a if a[k]["gap"] is not None]
    costs = {
        k: metric.paired_group_delta(
            [a[j] for j in evaluable], [b[j] for j in evaluable], k
        )
        for k in [
            "ordinary_options",
            "ordinary_questions",
            "final_comparison_candidates",
        ]
    }
    same_final_cost = all(
        a[key]["final_comparison_candidates"] == b[key]["final_comparison_candidates"]
        for key in a
    )
    interval = delta.get("paired_group_95_interval")
    noninferior = bool(interval and interval[1] <= margin)
    reduced_options = all(
        a[key]["ordinary_options"] < b[key]["ordinary_options"] for key in a
    )
    supported = noninferior and reduced_options and same_final_cost
    return {
        "comparison": "Existing P1 Q4 closure minus existing P4 Q5 closure; no new stopping rule",
        "gap_difference": delta,
        "cost_difference": costs,
        "cost_scope": "Same alignment-identifiable records/groups for primary gap and cost; no-reference cases remain in full coverage and cost diagnostics",
        "full_coverage_records": len(shorter),
        "alignment_identifiable_records": len(evaluable),
        "full_coverage_cost_diagnostics": {
            key: metric.paired_group_delta(shorter, longer, key)
            for key in [
                "ordinary_options",
                "ordinary_questions",
                "final_comparison_candidates",
            ]
        },
        "predeclared_gap_margin": margin,
        "upper_interval_within_margin": noninferior,
        "strictly_fewer_ordinary_options_for_every_record": reduced_options,
        "same_final_candidate_cost": same_final_cost,
        "status": (
            "SUPPORTED_IN_DECLARED_SCOPE"
            if supported
            else (
                "INCONCLUSIVE"
                if not interval or interval[0] <= margin
                else "NO_IMPROVEMENT"
            )
        ),
        "evidence_label": (
            "PROXY_INFORMATION_BUDGET_GAIN"
            if supported
            else "RECORD_PROXY_INFORMATION_BUDGET_COMPARISON"
        ),
        "real_time_efficiency": "NOT_EVALUATED",
    }


def run(owner):
    contract = verify_frozen(owner)
    destination = owner / "revisions/r2"
    rows = read(destination / "alignment_cost_trajectories.private.json")
    final = final_feedback(owner, contract)
    models = sorted({r["model"] for r in rows})
    endpoints = {
        path: {model: endpoint_rows(rows, model, path) for model in models}
        for path in ["P1", "P4"]
    }
    for path in endpoints:
        for model, subset in endpoints[path].items():
            if len(subset) != contract["data"]["development_records"]:
                raise ValueError(
                    "ENDPOINT_COVERAGE_DENOMINATOR_CHANGED:" + path + model
                )
    contrasts = {}
    for path, per_model in endpoints.items():
        contrasts[path] = {
            f"{a}_minus_{b}": paired(per_model[a], per_model[b])
            for a, b in [
                ("G3", "G1"),
                ("G2", "G1"),
                ("G1", "G0"),
                ("G3", "G0"),
                ("G3", "B2_ORIGINAL_CONTROL"),
                ("G3", "M2_R1_FINAL_FIXED_ORIGINAL_CONTROL"),
            ]
        }
    curve = []
    for path in ["P1", "P4"]:
        for model in models:
            for slot in ["CONTEXT", "Q0", "Q1", "Q2", "Q3", "Q4", "Q5"]:
                subset = [
                    r
                    for r in rows
                    if r["path"] == path and r["model"] == model and r["slot"] == slot
                ]
                if subset:
                    curve.append(
                        {
                            "path": path,
                            "model": model,
                            "slot": slot,
                            "legal_terminal_for_all": all(
                                r["ordinary_endpoint"] for r in subset
                            ),
                            **summary(subset),
                        }
                    )
    stage_changes = {}
    for model in VARIANTS:
        stage_changes[model] = {}
        for current, prior in [("Q1", "Q0"), ("Q2", "Q1"), ("Q3", "Q2"), ("Q4", "Q3")]:
            newer = [
                r
                for r in rows
                if r["model"] == model and r["path"] == "P1" and r["slot"] == current
            ]
            older = [
                r
                for r in rows
                if r["model"] == model and r["path"] == "P1" and r["slot"] == prior
            ]
            stage_changes[model][current + "_minus_" + prior] = paired(
                newer, older, equal_budget=False
            )
    feedback_report, efficiency, thresholds = {}, {}, {}
    for model in VARIANTS:
        feedback_report[model] = {}
        for path in ["P1", "P4"]:
            after = [r for r in final if r["model"] == model and r["path"] == path]
            before = endpoints[path][model]
            feedback_report[model][path] = {
                "before": summary(before),
                "after": summary(after),
                "after_minus_before": paired(after, before, equal_budget=False),
                "selected_records": sum(
                    r["feedback_selected_count"] > 0 for r in after
                ),
                "category_record_counts": {
                    c: sum(c in r["feedback_categories"] for r in after)
                    for c in [
                        "EMPTY_SELECTION",
                        "REPEATED_INFORMATION",
                        "BROAD_TO_SPECIFIC",
                        "NEW_VISIBLE_A_INFORMATION",
                    ]
                },
                "repeated_or_empty_max_score_change": max(
                    (
                        r["score_change_max"]
                        for r in after
                        if set(r["feedback_categories"])
                        <= {"REPEATED_INFORMATION", "EMPTY_SELECTION"}
                    ),
                    default=None,
                ),
                "independent_real_feedback": "NOT_EVALUATED",
            }
        efficiency[model] = {
            "before_final": information_efficiency(
                endpoints["P1"][model],
                endpoints["P4"][model],
                contract["information_efficiency"][
                    "noninferiority_absolute_gap_margin"
                ],
            ),
            "after_final": information_efficiency(
                [r for r in final if r["model"] == model and r["path"] == "P1"],
                [r for r in final if r["model"] == model and r["path"] == "P4"],
                contract["information_efficiency"][
                    "noninferiority_absolute_gap_margin"
                ],
            ),
        }
        thresholds[model] = {
            "before_final": threshold_summary(
                endpoints["P1"][model] + endpoints["P4"][model]
            ),
            "after_final": threshold_summary([r for r in final if r["model"] == model]),
        }
    report = {
        "primary_dynamic_contrast": contrasts["P1"]["G3_minus_G1"],
        "same_budget_endpoints": {
            path: {m: summary(rr) for m, rr in bymodel.items()}
            for path, bymodel in endpoints.items()
        },
        "paired_endpoint_contrasts": contrasts,
        "alignment_cost_curves": curve,
        "P1_legal_stage_changes": stage_changes,
        "threshold_attainment": thresholds,
        "proxy_information_efficiency": efficiency,
        "primary_efficiency_contrast": efficiency["G3"]["before_final"],
        "final_comparison": feedback_report,
        "interpretation": "All descriptor alignment and cost results are fixed-reference record proxies, not independent personal sensory judgments. Source-native profile/response losses are separate.",
        "actual_human_response_times": "NOT_EVALUATED",
    }
    result = read(OUT / "alignment_cost_results.json")
    result["coordination_alignment_and_cost"] = report
    save(OUT / "alignment_cost_results.json", result)
    print(
        "R2_PRIMARY_DYNAMIC_RESULT=" + str(report["primary_dynamic_contrast"]),
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    run(parser.parse_args().owner_dir)
