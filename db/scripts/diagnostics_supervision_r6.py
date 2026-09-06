"""Read-only aligned R6 information diagnostics; no fitting or selection."""

from __future__ import annotations
from collections import defaultdict
import numpy as np

CELLS = ("C00", "C10", "C01", "C11")


def macro(rows, key):
    groups = defaultdict(list)
    for r in rows:
        if r[key] is not None:
            groups[r["group_id"]].append(float(r[key]))
    return float(np.mean([np.mean(v) for v in groups.values()])) if groups else None


def aligned(cells):
    if set(cells) != set(CELLS):
        raise ValueError("EXACT_FOUR_MATRIX_CELLS_REQUIRED")
    indices = {}
    for name, rows in cells.items():
        ids = [r["record_id"] for r in rows]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_RECORD_ID:" + name)
        indices[name] = {r["record_id"]: r for r in rows}
    base = indices["C00"]
    for name, rows in indices.items():
        if set(rows) != set(base):
            raise ValueError("MATRIX_RECORD_IDS_NOT_ALIGNED:" + name)
        for identity, row in rows.items():
            ref = base[identity]
            if row["group_id"] != ref["group_id"]:
                raise ValueError("MATRIX_COFFEE_ID_MISMATCH")
            if row["full_T"] != ref["full_T"] or row["hidden_T"] != ref["hidden_T"]:
                raise ValueError("MATRIX_FIXED_TARGET_MISMATCH")
    return indices


def ranked(row):
    return [r["candidate_id"] if isinstance(r, dict) else r for r in row["ranking"]]


def summarize(cells):
    indices = aligned(cells)
    base = indices["C00"]
    result = {
        "records": len(base),
        "groups": len({r["group_id"] for r in base.values()}),
        "empty_full_T_retained": sum(
            not any(w > 0 for w in r["full_T"].values()) for r in base.values()
        ),
        "cells": {},
        "comparisons": {},
    }
    private = {"group_differences": {}, "review_cases": []}
    for name, records in indices.items():
        rows = []
        for identity, r in records.items():
            n = r.get("novelty") or {}
            known = {c for c, w in r["full_T"].items() if w > 0}
            new = set(n.get("B_new_system_canonical", []))
            specific = set(n.get("B_actual_new_specific", []))
            initial = {c for c in r["initial_selected"] if c.startswith("sensory.")}
            pred = set(ranked(r)[:5])
            ref = base[identity]
            old = r.get("old_full_A_selector_local_differences", [])
            rows.append(
                {
                    "group_id": r["group_id"],
                    "failure": bool(r.get("failure")),
                    "source_B_new_exact": len(n.get("source_B_new_exact", [])),
                    "actual_new_B_canonical": len(new),
                    "actual_new_B_specific": len(specific),
                    "actual_new_B_exact_T": len(specific & known),
                    "unacquired_B_specific": len(
                        n.get("source_B_new_specific_not_selected", [])
                    ),
                    "target_direction_coverage": r.get("target_direction_coverage"),
                    "initial_specific_expression_retention": (
                        len(initial & pred) / len(initial) if initial else None
                    ),
                    "new_B_record": bool(new),
                    "B_exact_T_record": bool(specific & known),
                    "initial_selected_changed": set(r["initial_selected"])
                    != set(ref["initial_selected"]),
                    "endpoint_selected_changed": set(r["endpoint_selected"])
                    != set(ref["endpoint_selected"]),
                    "ranking_changed": ranked(r) != ranked(ref),
                    "prediction_set_changed": set(ranked(r)[:5])
                    != set(ranked(ref)[:5]),
                    "full_A_unobserved_direction_count": len(
                        r.get("full_A_direction_not_observed", [])
                    ),
                    "old_selector_local_axis_different": any(
                        x.get("different_axis", False) for x in old
                    ),
                    "old_selector_local_option_different": any(
                        x.get("different_options", False) for x in old
                    ),
                    "ordinary_questions": r["costs"]["ordinary_questions"],
                    "ordinary_options": r["costs"]["ordinary_options"],
                    "proposed_final_candidates": r["costs"][
                        "proposed_final_candidate_count"
                    ],
                    "actual_final_exposure": r["costs"]["actual_final_exposure"],
                }
            )
        counts = [
            "failure",
            "new_B_record",
            "B_exact_T_record",
            "initial_selected_changed",
            "endpoint_selected_changed",
            "ranking_changed",
            "prediction_set_changed",
            "old_selector_local_axis_different",
            "old_selector_local_option_different",
        ]
        sums = [
            "source_B_new_exact",
            "actual_new_B_canonical",
            "actual_new_B_specific",
            "actual_new_B_exact_T",
            "unacquired_B_specific",
            "full_A_unobserved_direction_count",
        ]
        means = [
            "target_direction_coverage",
            "initial_specific_expression_retention",
            "ordinary_questions",
            "ordinary_options",
            "proposed_final_candidates",
        ]
        result["cells"][name] = {
            "record_counts": {k: sum(bool(r[k]) for r in rows) for k in counts},
            "record_concept_totals": {k: sum(r[k] for r in rows) for k in sums},
            "coffee_macro": {k: macro(rows, k) for k in means},
            "actual_final_exposure": sum(r["actual_final_exposure"] for r in rows),
            "full_A_extra_direction_records": sum(
                r["full_A_unobserved_direction_count"] > 0 for r in rows
            ),
            "old_selector_comparison_scope": "Same live prefix local full-A selector comparison, not complete historical R5 trajectory; reported only for I2_LIVE cells",
            "human_time": "NOT_EVALUATED",
        }
    candidates = []
    for name in ("C10", "C01", "C11"):
        groups = defaultdict(list)
        recordcounts = {"win": 0, "tie": 0, "loss": 0, "unknown": 0}
        for identity, ref in base.items():
            row = indices[name][identity]
            a = ref["metrics"]["raw_gap"]
            b = row["metrics"]["raw_gap"]
            delta = None if a is None or b is None else b - a
            category = (
                "unknown"
                if delta is None
                else "win" if delta < -1e-12 else "loss" if delta > 1e-12 else "tie"
            )
            recordcounts[category] += 1
            if delta is not None:
                groups[ref["group_id"]].append(delta)
            if delta is not None and abs(delta) > 1e-12:
                candidates.append(
                    {
                        "record_id": identity,
                        "comparison": name + "-C00",
                        "delta_raw_gap": delta,
                        "direction": "LOWER_IS_BETTER",
                        "reference_coverage_status": "FIXED_INDEPENDENT_CROSS_GRADER_T",
                        "cell_summaries": {
                            c: {
                                "ranking": ranked(indices[c][identity])[:5],
                                "full_T": indices[c][identity]["full_T"],
                                "initial_selected": indices[c][identity][
                                    "initial_selected"
                                ],
                                "endpoint_selected": indices[c][identity][
                                    "endpoint_selected"
                                ],
                                "novelty": indices[c][identity].get("novelty"),
                                "failure": indices[c][identity].get("failure"),
                            }
                            for c in CELLS
                        },
                    }
                )
        differences = {g: float(np.mean(ds)) for g, ds in groups.items()}
        result["comparisons"][name + "-C00"] = {
            "record_outcomes": recordcounts,
            "coffee_groups_with_T": len(differences),
            "coffee_group_wins": sum(d < -1e-12 for d in differences.values()),
            "coffee_group_ties": sum(abs(d) <= 1e-12 for d in differences.values()),
            "coffee_group_losses": sum(d > 1e-12 for d in differences.values()),
            "mean_delta_raw_gap": (
                float(np.mean(list(differences.values()))) if differences else None
            ),
            "all_group_denominator": result["groups"],
            "failure_cases_not_removed": True,
        }
        private["group_differences"][name + "-C00"] = differences
    seen = set()
    for item in sorted(
        candidates,
        key=lambda x: (-abs(x["delta_raw_gap"]), x["record_id"], x["comparison"]),
    ):
        if item["record_id"] not in seen:
            private["review_cases"].append(item)
            seen.add(item["record_id"])
        if len(seen) == 12:
            break
    result["private_review_cases"] = len(private["review_cases"])
    result["review_scope"] = (
        "Existing source cases for diagnostic mapping/information errors; no generated human judgments"
    )
    result["matched_all_cell_complete_records"] = sum(
        all(not indices[c][identity].get("failure") for c in CELLS) for identity in base
    )
    result["same_realized_option_budget_records"] = sum(
        len({indices[c][identity]["costs"]["ordinary_options"] for c in CELLS}) == 1
        for identity in base
    )
    return result, private
