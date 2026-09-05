"""Retained final R1 fix: broad feedback is canonical broad evidence, once."""

from __future__ import annotations
import argparse, json, time
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


def run(owner):
    cfg = freeze(owner)
    dst = owner / "revisions/r1"
    sel = read(dst / "conditional_selection.private.json")
    plan_path = dst / "broad_feedback_plan.private.json"
    if plan_path.exists():
        plan = read(plan_path)
    else:
        plan = {
            "registered_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trigger": "Final selection of an already selected attribute was recoded as a new concrete observation; preserve earlier R1 variants as failure controls.",
            "change": "canonical_broad_feedback=true; exactly same data, bank, C and layered conditional loss",
            "source_model": sel["model"],
            "C": sel["C"],
            "loss_mode": sel["loss_mode"],
        }
        save(plan_path, plan)
        cfg["broad_feedback_followup"] = plan
        save(OUT / "experiment_config.json", cfg)
    manifest = old_s.digest([sel["manifest_hash"], plan])
    data = read(owner / "recovery_records.json")
    dev = [r for r in data if r["split"] == "DEVELOPMENT"]
    hist = [r for r in data if r["split"] == "HISTORICAL_REGRESSION"]
    folds = read(dst / "D0_folds.private.json")
    label = "M2_R1_FINAL_FIXED"
    rows = []
    log = []
    for fold in [0, 1, 2, "ALL_DEVELOPMENT"]:
        base = (
            read(dst / f"cv/{sel['model']}_fold{fold}.model.json")
            if isinstance(fold, int)
            else read(sel["model_file"])
        )
        train = (
            [r for r in dev if folds[r["group_id"]] != fold]
            if isinstance(fold, int)
            else dev
        )
        held = (
            [r for r in dev if folds[r["group_id"]] == fold]
            if isinstance(fold, int)
            else hist
        )
        path = (
            dst / f"cv/{label}_fold{fold}.model.json"
            if isinstance(fold, int)
            else dst / f"models/{label}.model.json"
        )
        if path.exists():
            b = read(path)
        else:
            b, rec = tr.fit(
                train,
                manifest,
                C=sel["C"],
                vocabulary=base["candidate_vocabulary"],
                tag=label + ":" + str(fold),
                bank_override=base["question_bank"],
                loss_mode=sel["loss_mode"],
                canonical_broad_feedback=True,
            )
            b["experiment_variant"] = label
            save(path, b)
        log.append({"fold": fold, **b["fit_receipt"]})
        rr = []
        for r in held:
            row = enrich(tr.evaluate_record(r, b), r, rt, b)
            row["model"] = label
            row["fold"] = fold
            rr.append(row)
        if isinstance(fold, int):
            rows += rr
        else:
            historical = rr
        print(
            json.dumps(
                {
                    "phase": "final_broad_feedback",
                    "fold": fold,
                    "ndcg5": compact_summary(rr)["ndcg5"],
                }
            ),
            flush=True,
        )
    save(dst / f"cv/{label}.private.json", rows)
    save(dst / f"cv/{label}_historical.private.json", historical)
    save(dst / "final_feedback_fit_log.private.json", log)
    metrics = read(OUT / "metrics.json")
    metrics["broad_feedback_repair"] = {
        "model": compact_summary(rows),
        "historical": compact_summary(historical),
        "minus_prior_conditional": comparison(
            rows, read(dst / f"cv/{sel['model']}.private.json")
        ),
        "fit_count": len(log),
        "new_flag_default_only_for_explicit_new_fit": True,
        "earlier_R1_models_retained": True,
    }
    save(OUT / "metrics.json", metrics)
    save(
        dst / "final_fixed_selection.private.json",
        {
            "model": label,
            "C": sel["C"],
            "loss_mode": sel["loss_mode"],
            "manifest_hash": manifest,
            "model_file": str(dst / f"models/{label}.model.json"),
            "canonical_broad_feedback": True,
        },
    )
    return metrics["broad_feedback_repair"]


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-dir", type=Path, required=True)
    print(json.dumps(run(p.parse_args().owner_dir)), flush=True)
