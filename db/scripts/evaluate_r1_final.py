"""Final fixed-model scope, feedback and reload diagnostics; no target-derived feedback."""

from __future__ import annotations
import argparse, copy, json, time
from collections import defaultdict
from pathlib import Path
import numpy as np
import flavor_m2_r1 as rt
import train_m2_r1 as tr
from run_m2_r1 import (
    OUT,
    read,
    save,
    old_s,
    old_e,
    old_t,
    enrich,
    compact_summary,
    comparison,
    scope_row,
    mean,
)


def run(owner):
    dst = owner / "revisions/r1"
    sel = read(dst / "final_fixed_selection.private.json")
    name = sel["model"]
    data = read(owner / "recovery_records.json")
    lookup = {r["record_id"]: r for r in data}
    source = read(dst / f"cv/{name}.private.json")
    bases = []
    feedback = []
    checks = []
    qdiag = []
    bundles = {i: read(dst / f"cv/{name}_fold{i}.model.json") for i in range(3)}
    for fold, b in bundles.items():
        held = [r for r in source if r["fold"] == fold]
        qdiag.append(
            tr.initial_stage_diagnostics([lookup[r["record_id"]] for r in held], b)
        )
        checks.append(
            tr.mechanism_checks(read(owner / f"cv/M2_JOINT_fold{fold}.model.json"), b)
        )
        for row in held:
            record = lookup[row["record_id"]]
            for base in old_e.baselines(record, row, b):
                if base["model"] == "B2":
                    base["episode"] = row["episode"]
                    base["fold"] = fold
                    bases.append(base)
            ep, states, answers = tr.trajectory(record, b)
            full = states[-1]
            pre = rt.finalize_result(full, b)
            ex = pre["exposure"]
            if not ex or not ex["eligible_for_final_comparison"]:
                continue
            ev = rt.evidence(full, b)
            direct = set(ev["confirmed"])
            broad = set(ev["broad"])
            supported = broad | {
                d for c in direct for d in b["candidate_attributes"].get(c, [])
            }
            known = direct | {"attribute." + d for d in supported}
            chosen = [c for c in ex["candidate_ids"] if c in ep["visible"]]
            groups = {
                "REPEATED_INFORMATION": [c for c in chosen if c in known],
                "BROAD_TO_SPECIFIC": [
                    c
                    for c in chosen
                    if c not in known
                    and c.startswith(("sensory.", "broad."))
                    and set(b["candidate_attributes"].get(c, [])) & supported
                ],
                "NEW_JUDGMENT": [
                    c
                    for c in chosen
                    if c not in known
                    and not (
                        c.startswith(("sensory.", "broad."))
                        and set(b["candidate_attributes"].get(c, [])) & supported
                    )
                ],
            }
            assert sorted(sum(groups.values(), [])) == sorted(chosen)
            for category, choices in groups.items():
                for mode in ["F0", "F1", "F2"]:
                    updated = (
                        full
                        if mode == "F0"
                        else rt.apply_final_comparison(
                            full,
                            ex["candidate_ids"],
                            choices,
                            b,
                            feedback_source="SIMULATED",
                            generation_version=b["bundle_id"],
                            mode=mode,
                        )
                    )
                    result = old_e.result_row(record, updated, b, ep, mode)
                    before_scores = {
                        r["candidate_id"]: r["score"] for r in full["candidate_scores"]
                    }
                    change = max(
                        abs(r["score"] - before_scores[r["candidate_id"]])
                        for r in updated["candidate_scores"]
                    )
                    result.update(
                        category=category,
                        selected_count=len(choices),
                        score_change_max=change,
                        large_discrepancy_proxy=row["ndcg5"] is not None
                        and row["ndcg5"] < 0.5,
                        exposed_candidates=ex["candidate_ids"],
                        selected_candidates=choices,
                        generation_version=b["bundle_id"],
                    )
                    feedback.append(result)
                    if (
                        category == "REPEATED_INFORMATION"
                        and mode == "F2"
                        and change > 1e-12
                    ):
                        raise AssertionError("REPEATED_FINAL_INFORMATION_GAIN")
    save(dst / "final_feedback_diagnostics.private.json", feedback)
    save(dst / "final_initial_diagnostics.private.json", qdiag)
    save(dst / "final_mechanism_checks.private.json", checks)
    same = {
        fold: set(b["candidate_vocabulary"])
        & set(old_e.baseline_bundle(b)["vocabulary"])
        for fold, b in bundles.items()
    }
    fine = [scope_row(r, same[r["fold"]], "fine") for r in source]
    finebase = [scope_row(r, same[r["fold"]], "fine") for r in bases]
    full = read(sel["model_file"])
    oldm1 = read(owner.parent / "backend-model-20260905/models/M1.model.json")
    hist = read(dst / f"cv/{name}_historical.private.json")
    histbase = defaultdict(list)
    for r in hist:
        for base in old_e.baselines(lookup[r["record_id"]], r, full, old=oldm1):
            base["episode"] = r["episode"]
            histbase[base["model"]].append(base)
    common = set(full["candidate_vocabulary"]) & set(oldm1["vocabulary"])
    histfine = [scope_row(r, common, "fine") for r in hist]
    fsum = {}
    for category in ["REPEATED_INFORMATION", "BROAD_TO_SPECIFIC", "NEW_JUDGMENT"]:
        fsum[category] = {}
        for subset in ["ALL", "LARGE_DISCREPANCY_PROXY"]:
            rr = [
                r
                for r in feedback
                if r["category"] == category
                and r["selected_count"]
                and (subset == "ALL" or r["large_discrepancy_proxy"])
            ]
            bymode = {m: [r for r in rr if r["model"] == m] for m in ["F0", "F1", "F2"]}
            fsum[category][subset] = {
                "models": {k: compact_summary(v) for k, v in bymode.items()},
                "F2_minus_F0": comparison(bymode["F2"], bymode["F0"]),
                "F2_minus_F1": comparison(bymode["F2"], bymode["F1"]),
                "F2_max_score_change": max(
                    (r["score_change_max"] for r in bymode["F2"]), default=None
                ),
            }
    replay = tr.evaluate_record(
        lookup[source[0]["record_id"]],
        json.loads(json.dumps(bundles[source[0]["fold"]])),
    )
    expected = source[0]
    assert replay["ranking"] == expected["ranking"]
    metrics = read(OUT / "metrics.json")
    metrics["final_fixed"] = {
        "model_name": name,
        "model": compact_summary(source),
        "old_M2": compact_summary(read(dst / "cv/M2_JOINT_REPRODUCED.private.json")),
        "old_HIER_failure_control": {
            "model": compact_summary(read(owner / "cv/M2_HIER.private.json")),
            "scope": "Preserved original D0 grouped CV control, not refit",
        },
        "versus_old_M2_full": comparison(
            source, read(dst / "cv/M2_JOINT_REPRODUCED.private.json")
        ),
        "versus_B2_full": comparison(source, bases),
        "versus_B2_matched_fine": comparison(fine, finebase),
        "matched_fine": {name: compact_summary(fine), "B2": compact_summary(finebase)},
        "historical_matched_fine": {
            name: compact_summary(histfine),
            **{
                k: compact_summary([scope_row(r, common, "fine") for r in v])
                for k, v in histbase.items()
            },
        },
        "historical_comparisons": {
            k: comparison(histfine, [scope_row(r, common, "fine") for r in histbase[k]])
            for k in ["B2", "M1"]
        },
        "raw_direct_retention8": mean(source, "raw_direct_retention8"),
        "postprocessed_direct_retention8": mean(source, "direct_retention8"),
        "sensory_false_specificity_rate": "NOT_EVALUATED: unmentioned descriptions are not verified sensory negatives.",
        "all_cases_retained_in_coverage": len(source) == 211,
        "fold_negative_broad_contributions": {
            str(i): v["broad_support"]["r1_negative_child_contribution_count"]
            for i, v in enumerate(checks)
        },
        "reload_ranking_identical": True,
    }
    metrics["final_feedback"] = {
        "categories": fsum,
        "real_feedback_effect": "NOT_EVALUATED",
        "proxy_source": "Actual exposed candidates intersect fixed A visible evidence only; never frozen T.",
        "large_discrepancy": "Fixed exploratory NDCG@5 < .5 on preliminary recovery; not actual user deviation judgment.",
        "repeated_specific_and_broad_max_gain": max(
            r["score_change_max"]
            for r in feedback
            if r["category"] == "REPEATED_INFORMATION" and r["model"] == "F2"
        ),
        "empty_new_judgment_category": "NOT_EVALUATED if no actual visible-only new judgment is available; no agent answers fabricated.",
    }
    prefix_rows = defaultdict(list)
    for fold in qdiag:
        for row in fold["record_rows"]:
            for stage, values in row["stages"].items():
                prefix_rows[stage].append(
                    {k: row[k] for k in ["record_id", "group_id", "source_family"]}
                    | values
                )
    metrics["final_question_diagnostics"] = {
        "model": name,
        "scope": "D0 fixed visible/hidden recovery; Q1-only is evidence ablation, not a product path. FOUNDATION_CHECK uses its separately fixed A/B/T target protocol.",
        "stages": {k: compact_summary(v) for k, v in prefix_rows.items()},
        "Q0_PLUS_Q1_minus_Q0": comparison(prefix_rows["Q0_PLUS_Q1"], prefix_rows["Q0"]),
        "FIRST_CORRECTION_minus_Q0_PLUS_Q1": comparison(
            prefix_rows["FIRST_CORRECTION"], prefix_rows["Q0_PLUS_Q1"]
        ),
        "response_diagnostics_by_fold": [
            {k: v for k, v in item.items() if k != "record_rows"} for item in qdiag
        ],
        "real_question_value": "NOT_EVALUATED",
    }
    save(OUT / "metrics.json", metrics)
    print(json.dumps(metrics["final_fixed"]), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-dir", type=Path, required=True)
    run(p.parse_args().owner_dir)
