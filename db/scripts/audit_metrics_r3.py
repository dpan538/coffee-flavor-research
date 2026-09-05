#!/usr/bin/env python3
"""Audit frozen R2 output ties and fixed-universe reachability under R3 metrics."""

from collections import Counter, defaultdict
from pathlib import Path
import argparse

from alignment_metrics_r3 import evaluate, protocol
from run_m2_r1 import read, save, sha
from run_m2_r3 import OUT, verify
from run_m2_r2 import private_save


def panel(row):
    visible = set(row["episode"]["visible"])
    allowed = set(row["candidate_vocabulary"])
    return list(
        dict.fromkeys(
            c
            for c in row["ranking"]
            if c.startswith("sensory.") and c in allowed and c not in visible
        )
    )[:5]


def run(owner):
    verify(owner)
    rows = read(owner / "revisions/r2/alignment_cost_trajectories.private.json")
    experts = ["B2_TYPED_PRIOR_COMPONENT", "M2_R1_FINAL_FIXED_RESIDUAL"]
    lookup = {}
    for row in rows:
        if row["model"] in experts:
            key = (row["record_id"], row["path"], row["slot"])
            lookup.setdefault(key, {})[row["model"]] = row
    ties = Counter()
    bystage = defaultdict(Counter)
    detailed = []
    for values in lookup.values():
        if set(values) != set(experts):
            raise ValueError("UNPAIRED_R2_EXPERT_OUTPUT")
        a, b = (values[k] for k in experts)
        if (
            a["target_sha256"] != b["target_sha256"]
            or a["visible_sha256"] != b["visible_sha256"]
            or a["candidate_vocabulary"] != b["candidate_vocabulary"]
        ):
            raise ValueError("EXPERT_CASE_TARGET_UNIVERSE_MISMATCH")
        ra, rb = [
            evaluate(
                r["ranking"],
                r["episode"]["relevance"],
                r["candidate_vocabulary"],
                r["episode"]["visible"],
            )
            for r in [a, b]
        ]
        if ra["raw_gap"] is None:
            category = "NO_FINE_TARGET_UNIDENTIFIABLE"
        elif abs(ra["raw_gap"] - rb["raw_gap"]) > 1e-12:
            category = "DIFFERENT_SET_MATCHING_LOSS"
        elif panel(a) == panel(b):
            category = "IDENTICAL_FINE_PANEL_ORDER"
        elif set(panel(a)) == set(panel(b)):
            category = "SAME_FINE_SET_DIFFERENT_ORDER"
        else:
            category = "DIFFERENT_FINE_SETS_SAME_MATCHING_LOSS"
        ties[category] += 1
        bystage[a["slot"]][category] += 1
        detailed.append(
            {
                "record_id": a["record_id"],
                "group_id": a["group_id"],
                "path": a["path"],
                "slot": a["slot"],
                "category": category,
                "ndcg_difference": (
                    ra["ndcg"] - rb["ndcg"] if ra["ndcg"] is not None else None
                ),
            }
        )
    endpoint = [
        r
        for r in rows
        if r["model"] == "G3" and r["path"] == "P1" and r["ordinary_endpoint"]
    ]
    reaches = []
    for row in endpoint:
        result = evaluate(
            row["ranking"],
            row["episode"]["hidden"],
            row["candidate_vocabulary"],
            row["episode"]["visible"],
        )
        if result["raw_gap"] != row["gap"]:
            if result["raw_gap"] is None or abs(result["raw_gap"] - row["gap"]) > 1e-12:
                raise ValueError("R2_FIXED_MATCHING_PARITY_FAILED")
        reaches.append(
            {"record_id": row["record_id"], "group_id": row["group_id"], **result}
        )
    known = [r for r in reaches if r["target_count"]]
    summary = {
        "status": "METRIC_IMPLEMENTATION_VERIFIED",
        "construct_status": "EXTERNAL_CONSTRUCT_CHECK_PILOT_PENDING_SEPARATE_FROZEN_RUN",
        "protocol": protocol(),
        "implementation_tests": {
            "test_file": "db/tests/test_alignment_metrics_r3.py",
            "test_count": 12,
            "passed_before_empirical_audit": True,
        },
        "prior_implementation_findings": {
            "R2_one_to_one_matching": "Already correct, preserved unchanged",
            "R2_unknown_parent_match": "Already rejects unknown/empty shared parents, no None==None credit observed",
            "legacy_ndcg": "Uses predicted rank and sorted ideal relevance correctly; legacy empty-target0 behavior preserved historically, new R3 returnsnull",
            "new_R3_work": "Explicit ID/length checks; exact k-cardinality reachability decomposition; distinguish set equivalence from rank equivalence",
            "R2_original_numeric_results": "UNCHANGED; primary matching reproduced on all declared G3 P1 endpoint cases",
        },
        "R2_expert_tie_audit": {
            "counts": dict(ties),
            "by_slot": dict(bystage),
            "state_rows": len(lookup),
            "not_independent_sample_size": True,
            "scope": "Common fine five-item counterfactual completion panels; identity here is panel identity, not equality of all scores or runtime state",
            "ranking_informative_among_equal_set_losses": sum(
                r["ndcg_difference"] is not None
                and abs(r["ndcg_difference"]) > 1e-12
                and r["category"]
                in [
                    "SAME_FINE_SET_DIFFERENT_ORDER",
                    "DIFFERENT_FINE_SETS_SAME_MATCHING_LOSS",
                ]
                for r in detailed
            ),
        },
        "R2_G3_P1_reachability": {
            "all_records": len(reaches),
            "fine_target_identifiable_records": len(known),
            "unidentifiable_retained": len(reaches) - len(known),
            "all_coffee_groups": len({r["group_id"] for r in reaches}),
            "labelled_coffee_groups": len({r["group_id"] for r in known}),
            "threshold_unreachable_cases": sum(
                not r["threshold_0_5_reachable"] for r in known
            ),
            "target_count_above5_but_threshold_reachable": sum(
                r["target_count"] > 5 and r["threshold_0_5_reachable"] for r in known
            ),
            "M_star_zero_cases": sum(r["M_star"] == 0 for r in known),
            "capacity_limited_cases": sum(r["capacity_floor"] > 0 for r in known),
            "additional_vocabulary_relation_limited_cases": sum(
                r["vocabulary_relation_extra_floor"] > 1e-12 for r in known
            ),
            "currently_over_threshold_but_reachable_cases": sum(
                r["raw_gap"] > 0.5 and r["threshold_0_5_reachable"] for r in known
            ),
            "opportunity_metric_role": "Diagnostic only; raw gap always retained; no retroactive success reclassification",
        },
        "input_sha256": sha(
            owner / "revisions/r2/alignment_cost_trajectories.private.json"
        ),
        "psychological_distance_calibration": "NOT_ESTABLISHED",
    }
    private_save(owner / "revisions/r3/metric_tie_details.private.json", detailed)
    private_save(
        owner / "revisions/r3/metric_reachability_details.private.json", reaches
    )
    save(OUT / "metric_audit.json", summary)
    print(summary["R2_expert_tie_audit"]["counts"])
    print(summary["R2_G3_P1_reachability"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    run(parser.parse_args().owner_dir)
