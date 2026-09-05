#!/usr/bin/env python3
"""Replay the frozen full R2 research model on already-viewed historical groups."""

import argparse
from pathlib import Path

from alignment_metrics_r2 import grouped_summary, paired_group_delta
from run_m2_r1 import read, sha
from run_m2_r2 import OUT, private_save, verify_frozen
from train_coordination_r2 import audit_expert, collect_predictions, evaluate_outer


def run(owner):
    verify_frozen(owner)
    private = owner / "revisions/r2"
    model_path = private / "models/R2_COORDINATOR_ALL_DEVELOPMENT.model.json"
    before = sha(model_path)
    bundle = read(model_path)
    records = read(owner / "recovery_records.json")
    development = [r for r in records if r["split"] == "DEVELOPMENT"]
    historical = [r for r in records if r["split"] == "HISTORICAL_REGRESSION"]
    audit = audit_expert(bundle["r1_expert"], development, historical)
    if set(bundle["router"]["training_groups"]) & {r["group_id"] for r in historical}:
        raise ValueError("HISTORICAL_GROUPS_USED_FOR_ROUTER_TRAINING")
    rows = collect_predictions(
        historical,
        bundle["r1_expert"],
        sha(OUT / "objective_and_metric_contract.json"),
        "HISTORICAL_REGRESSION",
    )
    results = evaluate_outer(rows, bundle)
    for row in results:
        row["proxy_status"] = (
            "ALREADY_VIEWED_HISTORICAL_REGRESSION_NOT_FRESH_CONFIRMATION"
        )
    endpoints = {}
    contrasts = {}
    for path in ["P1", "P4"]:
        by_model = {
            model: [
                r
                for r in results
                if r["path"] == path and r["ordinary_endpoint"] and r["model"] == model
            ]
            for model in sorted({r["model"] for r in results})
        }
        endpoints[path] = {model: grouped_summary(rr) for model, rr in by_model.items()}
        contrasts[path] = paired_group_delta(by_model["G3"], by_model["G1"])
        contrasts[path]["scope"] = "ALREADY_VIEWED_HISTORICAL_REGRESSION_ONLY"
    if sha(model_path) != before:
        raise ValueError("MODEL_CHANGED_DURING_HISTORY_REPLAY")
    private_save(private / "coordination_history_rows.private.json", results)
    private_save(private / "coordination_history_audit.private.json", audit)
    summary = {
        "scope": "ALREADY_VIEWED_HISTORICAL_REGRESSION; NOT_FRESH_CONFIRMATION; NO_FIT_OR_SELECTION",
        "records": len(historical),
        "groups": len({r["group_id"] for r in historical}),
        "model_sha256": before,
        "model_unchanged": True,
        "same_budget_endpoints": endpoints,
        "G3_minus_G1": contrasts,
        "audit_sha256": sha(private / "coordination_history_audit.private.json"),
        "private_trajectory_sha256": sha(
            private / "coordination_history_rows.private.json"
        ),
    }
    private_save(private / "coordination_history_summary.private.json", summary)
    print({"historical_groups": summary["groups"], "P1": endpoints["P1"]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    run(parser.parse_args().owner_dir)
