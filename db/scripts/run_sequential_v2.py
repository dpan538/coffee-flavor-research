#!/usr/bin/env python3
"""Bounded M2 grouped development CV. All retained details remain owner-local."""

from __future__ import annotations
import argparse, copy, json, platform, subprocess, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import scipy, sklearn
import flavor_sequential as s
import train_sequential as t
from prepare_sequential_data import save

OUT = t.OUT


def group_mean(rows, key):
    groups = defaultdict(list)
    for r in rows:
        if r.get(key) is not None:
            groups[r["group_id"]].append(float(r[key]))
    return {g: float(np.mean(v)) for g, v in groups.items()}


def mean(rows, key):
    values = list(group_mean(rows, key).values())
    return float(np.mean(values)) if values else None


def paired(a, b, key="ndcg5"):
    x = group_mean(a, key)
    y = group_mean(b, key)
    groups = sorted(set(x) & set(y))
    delta = np.array([x[g] - y[g] for g in groups])
    rng = np.random.default_rng(t.SEED)
    if not len(delta):
        return {"delta": None, "groups": 0, "status": "NOT_EVALUATED"}
    interval = np.quantile(
        delta[rng.integers(0, len(delta), (5000, len(delta)))].mean(1), [0.025, 0.975]
    ).tolist()
    return {
        "delta": float(delta.mean()),
        "paired_group_95_interval": interval,
        "groups": len(groups),
        "status": (
            "INCONCLUSIVE"
            if interval[0] <= 0 <= interval[1]
            else "IMPROVEMENT_SUPPORTED" if interval[0] > 0 else "NO_IMPROVEMENT"
        ),
        "scope": "PROXY_DEVELOPMENT_CV_NOT_INDEPENDENT_PRODUCT_CONFIRMATION",
    }


def summary(rows):
    keys = [
        "ndcg5",
        "recall5",
        "recall8",
        "direct_retention8",
        "coverage",
        "candidate_target_coverage",
        "duplicate_rate",
        "latency_ms",
        "question_count",
        "option_budget",
    ]
    return {
        "records": len(rows),
        "groups": len({r["group_id"] for r in rows}),
        "labelled_records": sum(r["ndcg5"] is not None for r in rows),
        **{k: mean(rows, k) for k in keys},
        "per_source": {
            src: {
                k: mean([r for r in rows if r["source_family"] == src], k) for k in keys
            }
            for src in sorted({r["source_family"] for r in rows})
        },
        "worst_source_ndcg5": min(
            mean([r for r in rows if r["source_family"] == src], "ndcg5")
            for src in {r["source_family"] for r in rows}
        ),
    }


def fit_model(records, kind, C, manifest_hash, tag, arrays=None):
    bundle = t.make_bundle(records, kind, manifest_hash, tag=tag)
    X, Y, w, audit = (
        t.training_arrays(records, bundle, manifest_hash) if arrays is None else arrays
    )
    # Identity centering, TRAIN-only per-feature RMS scale. No held-out scaling.
    scales = np.sqrt(np.mean(X * X, axis=(0, 1)))
    scales[scales < 1e-8] = 1.0
    weights, receipt = t.fit_shared(X / scales, Y, w, C, kind)
    bundle["scaler_parameters"] = {
        "mean": [0.0] * len(s.FEATURES),
        "scale": scales.tolist(),
        "basis": "RMS_OF_INNER_OOF_TRAIN_CANDIDATE_FEATURES",
    }
    bundle["model_parameters"]["weights"] = weights
    bundle["fit_receipt"] = receipt
    bundle["inner_feature_isolation"] = audit
    bundle["bundle_id"] += ":" + s.digest([C, weights])[:12]
    return bundle, (X, Y, w, audit)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", type=Path, required=True)
    a = parser.parse_args()
    owner = a.owner_dir
    started = time.time()
    records = json.loads((owner / "recovery_records.json").read_text())
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    historic = [r for r in records if r["split"] == "HISTORICAL_REGRESSION"]
    folds = t.split_groups(dev)
    manifest = json.loads((OUT / "dataset_manifest.json").read_text())
    old_manifest = json.loads(
        (t.ROOT / "db/data/backend-model-20260905/dataset_manifest.json").read_text()
    )
    manifest["record_recovery"] = {
        "roles": ["CORE_PROFESSIONAL"],
        "source_families": sorted({r["source_family"] for r in records}),
        "records": len(records),
        "groups": len({r["group_id"] for r in records}),
        "development_records": len(dev),
        "development_groups": len(folds),
        "historical_regression_records": len(historic),
        "historical_regression_groups": len({r["group_id"] for r in historic}),
        "uninterpretable_target_records_retained_in_coverage": sum(
            not r["targets"] for r in dev
        ),
        "production_paired_context_records": 0,
        "missing_source_c0_count": sum(r["source_C0"] is None for r in records),
        "missing_source_c1_count": sum(r["source_C1"] is None for r in records),
        "split_hash": s.digest(folds),
        "private_input_sha256": __import__("hashlib")
        .sha256((owner / "recovery_records.json").read_bytes())
        .hexdigest(),
        "source_share": {
            src: {
                "raw_records": sum(r["source_family"] == src for r in dev),
                "independent_groups": len(
                    {r["group_id"] for r in dev if r["source_family"] == src}
                ),
                "effective_training_source_contribution": 1 / 3,
            }
            for src in sorted({r["source_family"] for r in dev})
        },
        "label_structure": "Incomplete positive descriptions and native mention frequencies. Missing descriptors are not sensory negative labels. Nutty/Cocoa is one dimension. One uninterpretable Lengupa row is retained in coverage, excluded from labelled utility.",
        "historical_rights_reference": "db/data/backend-model-20260905/dataset_manifest.json",
        "rights_unchanged": True,
        "new_confirmation": "NOT_EVALUATED",
        "coffee_group_leakage_policy": "All sample aliases and genotypes stay grouped; outer and inner features are fitted on train groups only.",
    }
    save(OUT / "dataset_manifest.json", manifest)
    manifest_hash = s.digest(manifest)
    config = json.loads((OUT / "experiment_config.json").read_text())
    config["sequential"] = {
        "seed": t.SEED,
        "task": "RECORD_RECOVERY_PROXY",
        "folds": 3,
        "inner_feature_folds": 2,
        "development_only": True,
        "primary_metric": "observed_descriptor_recovery_NDCG@5",
        "graded_relevance": "Distinct panel mention counts or native frequency, conditional on observed positive descriptors only",
        "loss": "Positive conditional token cross entropy; 0.7 hidden recovery and 0.3 explicit-retention mass when available. Unmentioned descriptors are not labelled sensory absences.",
        "ADD_C_search": [0.01, 0.1, 1.0],
        "staged_search": "Choose ADD C on development CV, reuse C for JOINT then HIER; no Cartesian search. Final model choose best CV, retain all alternatives. No tuning on historical 17 groups.",
        "source_weighting": "Equal source; equal independent coffee group; equal records/states within group.",
        "candidate_features": s.FEATURES,
        "ordinary_path_for_primary_comparison": "P1",
        "ordinary_option_budget": 4,
        "held_visible_evidence_max": 3,
        "Q0_Q1_included_in_fit": True,
        "feedback_simulation": "Only exposed candidates intersecting frozen visible evidence; hidden targets never select feedback.",
        "policy_evaluation": "Fixed, fixed-seeded random, one-step and bounded two-step on identical P1 question/option budgets. Response distributions from TRAIN only.",
        "fixed_target_through_trajectory": True,
        "recovery_excludes_visible_and_entailed_parent_restatement": True,
        "truth_measurements_in_live_features": False,
        "context_descriptor_effect": "NOT_ESTIMABLE: no validated paired context. Both training and runtime mask descriptor context identically; no seven-bin source label fabrication.",
        "cluster": "3 nonnegative factors fit only complete INERA native frequency TRAIN matrix; overlapping semantic projection.",
        "preregistered_before_fit": True,
    }
    save(OUT / "experiment_config.json", config)
    models = owner / "models"
    models.mkdir(exist_ok=True)
    (owner / "cv").mkdir(exist_ok=True)
    save(owner / "cv/splits.private.json", folds)
    all_rows = {}
    bundles = {}
    arrays = {}
    fit_log = []
    for C in config["sequential"]["ADD_C_search"]:
        label = "M2_ADD_C" + str(C)
        rows = []
        for fold in range(3):
            train = [r for r in dev if folds[r["group_id"]] != fold]
            held = [r for r in dev if folds[r["group_id"]] == fold]
            begin = time.time()
            b, ar = fit_model(
                train, "M2_ADD", C, manifest_hash, "outer" + str(fold), arrays.get(fold)
            )
            arrays[fold] = ar
            bundles[label, fold] = b
            rows.extend(t.evaluate_record(r, b) for r in held)
            save(owner / f"cv/{label}_fold{fold}.model.json", b)
            fit_log.append(
                {
                    "label": label,
                    "fold": fold,
                    "seconds": time.time() - begin,
                    **b["fit_receipt"],
                }
            )
            print(json.dumps(fit_log[-1]), flush=True)
        all_rows[label] = rows
        save(owner / f"cv/{label}.private.json", rows)
        print(label, summary(rows)["ndcg5"], flush=True)
    bestC = max(
        config["sequential"]["ADD_C_search"],
        key=lambda C: mean(all_rows["M2_ADD_C" + str(C)], "ndcg5"),
    )
    all_rows["M2_ADD"] = all_rows["M2_ADD_C" + str(bestC)]
    for fold in range(3):
        bundles["M2_ADD", fold] = bundles["M2_ADD_C" + str(bestC), fold]
    for kind in ["M2_JOINT", "M2_HIER"]:
        rows = []
        for fold in range(3):
            train = [r for r in dev if folds[r["group_id"]] != fold]
            held = [r for r in dev if folds[r["group_id"]] == fold]
            begin = time.time()
            b, _ = fit_model(train, kind, bestC, manifest_hash, "outer" + str(fold))
            bundles[kind, fold] = b
            rows.extend(t.evaluate_record(r, b) for r in held)
            save(owner / f"cv/{kind}_fold{fold}.model.json", b)
            fit_log.append(
                {
                    "label": kind,
                    "fold": fold,
                    "seconds": time.time() - begin,
                    **b["fit_receipt"],
                }
            )
            print(json.dumps(fit_log[-1]), flush=True)
        all_rows[kind] = rows
        save(owner / f"cv/{kind}.private.json", rows)
        print(kind, summary(rows)["ndcg5"], flush=True)
    kinds = ["M2_ADD", "M2_JOINT", "M2_HIER"]
    selected = max(kinds, key=lambda k: mean(all_rows[k], "ndcg5"))
    historical = {}
    for kind in kinds:
        begin = time.time()
        b, _ = fit_model(dev, kind, bestC, manifest_hash, "all-development")
        save(models / (kind + ".model.json"), b)
        historical[kind] = [t.evaluate_record(r, b) for r in historic]
        fit_log.append(
            {
                "label": kind,
                "fold": "FINAL_DEVELOPMENT_FIT",
                "seconds": time.time() - begin,
                **b["fit_receipt"],
            }
        )
        print(json.dumps(fit_log[-1]), flush=True)
    metrics = json.loads((OUT / "metrics.json").read_text())
    metrics["sequential"] = {
        "task": "RECORD_RECOVERY_PROXY",
        "evaluation_scope": "DEVELOPMENT_GROUP_CV; model and C selected here, not independent confirmation",
        "selected_C": bestC,
        "selected_model": selected,
        "C_search": {k: summary(v) for k, v in all_rows.items() if "_C" in k},
        "models": {k: summary(all_rows[k]) for k in kinds},
        "comparisons": {
            "JOINT_minus_ADD": paired(all_rows["M2_JOINT"], all_rows["M2_ADD"]),
            "HIER_minus_JOINT": paired(all_rows["M2_HIER"], all_rows["M2_JOINT"]),
        },
        "historical_regression": {k: summary(historical[k]) for k in kinds},
        "real_QA": "NOT_EVALUATED",
        "independent_product_confirmation": "NOT_EVALUATED",
        "error_specificity_sensory_truth": "NOT_EVALUATED: incomplete positive labels; no false negatives inferred from unmentioned concepts",
        "retained_models": [str(models / (k + ".model.json")) for k in kinds],
    }
    save(OUT / "metrics.json", metrics)
    save(owner / "cv/fit_log.private.json", fit_log)
    save(owner / "cv/historical_predictions.private.json", historical)
    receipt = json.loads((OUT / "run_receipt.json").read_text())
    receipt["M2"] = {
        "command": '/private/tmp/coffee-backend-model-venv/bin/python db/scripts/run_sequential_v2.py --owner-dir "'
        + str(owner)
        + '"',
        "code_base_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=t.ROOT, text=True
        ).strip(),
        "seconds": time.time() - started,
        "fit_count": len(fit_log),
        "selected_model": selected,
        "model_path": str(models / (selected + ".model.json")),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
        "status": "ACTUAL_FITTING_COMPLETED; policy and feedback diagnostic checkpoint pending",
    }
    save(OUT / "run_receipt.json", receipt)
    print(json.dumps(metrics["sequential"]["comparisons"]), flush=True)


if __name__ == "__main__":
    main()
