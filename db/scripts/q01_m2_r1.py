"""Complementary initial-question ablation on the repaired conditional objective."""

from __future__ import annotations
import argparse, copy, json, time
from pathlib import Path
import train_m2_r1 as tr
import flavor_m2_r1 as rt
from run_m2_r1 import (
    OUT,
    read,
    save,
    freeze,
    old_s,
    enrich,
    compact_summary,
    comparison,
)


def run(owner, final_repair=False):
    cfg = freeze(owner)
    dst = owner / "revisions/r1"
    sel = read(
        dst
        / (
            "final_fixed_selection.private.json"
            if final_repair
            else "conditional_selection.private.json"
        )
    )
    data = read(owner / "recovery_records.json")
    dev = [r for r in data if r["split"] == "DEVELOPMENT"]
    folds = read(dst / "D0_folds.private.json")
    label = "M2_R1_FINAL_Q01" if final_repair else "M2_R1_CONDITIONAL_Q01"
    result_key = "final_Q01" if final_repair else "conditional_Q01"
    suffix = "_final" if final_repair else ""
    if final_repair:
        plan_path = dst / "q01_final_plan.private.json"
        plan = {
            "model": label,
            "base_model": sel["model"],
            "C": sel["C"],
            "canonical_broad_feedback": True,
            "data": "FROZEN_D0_ONLY",
            "outer_folds": 3,
            "only_changed_factor": "Training-only complementary Q0/Q1 construction; fixed vocabulary, correction pool, objective, A/T and full group denominator",
            "decision": "Retain final fixed baseline unless paired development interval supports improvement; never use historical or confirmation data for this decision.",
        }
        if plan_path.exists():
            assert {
                k: v for k, v in read(plan_path).items() if k != "registered_utc"
            } == plan
        else:
            plan["registered_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            save(plan_path, plan)
            cfg["final_Q01_followup"] = plan
            save(OUT / "experiment_config.json", cfg)
    rows = []
    detail = []
    old_detail = []
    fits = []
    for fold in range(3):
        old = read(dst / f"cv/{sel['model']}_fold{fold}.model.json")
        train = [r for r in dev if folds[r["group_id"]] != fold]
        held = [r for r in dev if folds[r["group_id"]] == fold]
        path = dst / f"cv/{label}_fold{fold}.model.json"
        if path.exists():
            b = read(path)
        else:
            new = tr.make_bundle(
                train,
                manifest_hash=sel["manifest_hash"],
                vocabulary=old["candidate_vocabulary"],
            )
            bank = copy.deepcopy(old["question_bank"])
            for key in ["initial_0", "initial_1", "initial_pair_selection"]:
                bank[key] = new["question_bank"][key]
            b, rec = tr.fit(
                train,
                sel["manifest_hash"],
                C=sel["C"],
                vocabulary=old["candidate_vocabulary"],
                tag=label + ":fold" + str(fold),
                bank_override=bank,
                loss_mode=sel["loss_mode"],
                canonical_broad_feedback=sel.get("canonical_broad_feedback", False),
            )
            b["experiment_variant"] = label
            save(path, b)
        assert (
            b["fit_receipt"]["C"] == sel["C"]
            and b["fit_receipt"]["loss_mode"] == sel["loss_mode"]
        )
        assert b["data_manifest_hash"] == sel["manifest_hash"]
        assert b["evidence_policy"].get("canonical_broad_feedback", False) == sel.get(
            "canonical_broad_feedback", False
        )
        fits.append({"fold": fold, **b["fit_receipt"]})
        detail.append(tr.initial_stage_diagnostics(held, b))
        old_detail.append(tr.initial_stage_diagnostics(held, old))
        for r in held:
            row = enrich(tr.evaluate_record(r, b), r, rt, b)
            row["model"] = label
            row["fold"] = fold
            rows.append(row)
        print(
            json.dumps(
                {
                    "phase": result_key,
                    "fold": fold,
                    "ndcg5": compact_summary(rows)["ndcg5"],
                }
            ),
            flush=True,
        )
    save(dst / f"cv/{label}.private.json", rows)
    save(
        dst / ("q01" + suffix + "_diagnostics.private.json"),
        {"original": old_detail, "complementary": detail},
    )
    save(dst / ("q01" + suffix + "_fit_log.private.json"), fits)
    base = read(dst / f"cv/{sel['model']}.private.json")
    metrics = read(OUT / "metrics.json")

    def remove_private(x):
        if isinstance(x, dict):
            return {
                k: remove_private(v)
                for k, v in x.items()
                if k not in {"rows", "record_rows", "training_groups", "records"}
            }
        if isinstance(x, list):
            return [remove_private(v) for v in x]
        return x

    metrics[result_key] = {
        "same_C_same_objective_minus_original_pair": comparison(rows, base),
        "models": {
            "original_pair": compact_summary(base),
            "complementary_pair": compact_summary(rows),
        },
        "diagnostics_by_fold": {
            "original": remove_private(old_detail),
            "complementary": remove_private(detail),
        },
        "fit_count": len(fits),
        "interpretation": "Fixed A/T and correction pool; Q1 response/information effects are record-derived proxies; does not remove Q1.",
    }
    save(OUT / "metrics.json", metrics)
    print(
        json.dumps(
            {
                "phase": "Q01_complete",
                "delta": metrics[result_key][
                    "same_C_same_objective_minus_original_pair"
                ],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-dir", type=Path, required=True)
    p.add_argument("--final-repair", action="store_true")
    args = p.parse_args()
    run(args.owner_dir, args.final_repair)
