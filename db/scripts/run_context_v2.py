"""Actual grouped numerical context fits with raw-unit and standardized errors."""

from __future__ import annotations
import csv, json, time, hashlib, platform
from pathlib import Path
import numpy as np
from flavor_context import VARIANTS, CONTEXT_VERSION, fit_context, predict_context
from prepare_sequential_data import numerical, save

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-sequential-model-v2"
SEED = 20260905


def write_tsv(p, rows):
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: (
                        json.dumps(v, ensure_ascii=False)
                        if isinstance(v, (dict, list))
                        else v
                    )
                    for k, v in r.items()
                }
            )


def interval(values):
    vals = np.array(values, float)
    rng = np.random.default_rng(SEED)
    sample = vals[rng.integers(0, len(vals), (5000, len(vals)))].mean(1)
    return np.quantile(sample, [0.025, 0.975]).tolist()


def run(owner):
    start = time.time()
    data = numerical(owner)
    effects = []
    robust = []
    pred = []
    summaries = {}
    models = {}
    fit_count = 0
    config = {
        "task": "NUMERICAL_CONTEXT_AUXILIARY",
        "context_mapping_version": CONTEXT_VERSION,
        "models": VARIANTS,
        "loss": "Multi-output squared loss; per-target TRAIN-only mean/std then Ridge alpha=1; separate datasets/scales, not pooled",
        "alpha": 1.0,
        "interaction_feature_shrinkage": 0.25,
        "evaluation": "Leave-one-coffee/sample-group-out within each study; all technical/panel repeats kept aggregate",
        "independent_confirmatory_product_status": "NOT_EVALUATED",
        "source_native_roast_not_seven_bin": True,
        "preregistered_before_fit": True,
        "seed": SEED,
        "model_features_exclude": [
            "coffee_identity",
            "study_identity",
            "lab_identity",
            "measurement_truth",
            "evaluation_targets",
        ],
    }
    save(OUT / "experiment_config.json", {"context_experiment": config})
    for ds, rows in data["datasets"].items():
        groups = sorted({r["group_id"] for r in rows})
        pred_by = {m: [] for m in VARIANTS}
        by_id = {r["condition_id"]: r for r in rows}
        c0_variation = len({r["c0"] for r in rows}) > 1
        c1_variation = len({r["source_roast"] for r in rows if r["source_roast"]}) > 1
        for held in groups:
            train = [r for r in rows if r["group_id"] != held]
            test = [r for r in rows if r["group_id"] == held]
            for variant in VARIANTS:
                model = fit_context(train, variant)
                fit_count += 1
                for r in test:
                    p = predict_context(r, model)
                    entry = {
                        "dataset": ds,
                        "model": variant,
                        "group_id": held,
                        "condition_id": r["condition_id"],
                        "prediction": p,
                        "targets": r["targets"],
                        "train_target_scale": model["scaler_parameters"]["scale"],
                    }
                    pred_by[variant].append(entry)
                    pred.append(entry)
                    if variant == "C_JOINT":
                        options = [
                            "correct",
                            "c0_other_observed",
                            "c1_native_adjacent",
                            "c1_native_far",
                            "both_native_changed",
                        ]
                        for condition in options:
                            altered = dict(r)
                            reason = None
                            if condition in {
                                "c0_other_observed",
                                "both_native_changed",
                            }:
                                altered["c0"] = next(
                                    (
                                        x
                                        for x in sorted({x["c0"] for x in train})
                                        if x != r["c0"]
                                    ),
                                    r["c0"],
                                )
                            if condition in {
                                "c1_native_adjacent",
                                "c1_native_far",
                                "both_native_changed",
                            }:
                                if not r["source_roast"]:
                                    reason = (
                                        "No source roast contrast or verified category"
                                    )
                                else:
                                    labels = ["light", "medium", "dark"]
                                    i = labels.index(r["source_roast"])
                                    j = (
                                        (i + 1 if i < 2 else i - 1)
                                        if condition == "c1_native_adjacent"
                                        else (2 if i == 0 else 0)
                                    )
                                    altered["source_roast"] = labels[j]
                            changed = (
                                predict_context(altered, model)
                                if reason is None
                                else None
                            )
                            assert altered["targets"] == r["targets"]
                            scale = np.array(model["scaler_parameters"]["scale"])
                            truth = np.array(r["targets"])
                            err = float(np.mean(np.abs((np.array(p) - truth) / scale)))
                            newerr = (
                                float(
                                    np.mean(np.abs((np.array(changed) - truth) / scale))
                                )
                                if changed is not None
                                else None
                            )
                            robust.append(
                                {
                                    "dataset": ds,
                                    "group_id": held,
                                    "condition_id": r["condition_id"],
                                    "stage": "CONTEXT_ONLY_SOURCE_NATIVE",
                                    "perturbation": condition,
                                    "c0_before": r["c0"],
                                    "c0_after": altered["c0"],
                                    "c1_source_before": r["source_roast"],
                                    "c1_source_after": altered["source_roast"],
                                    "truth_unchanged": True,
                                    "standardized_mae_correct": err,
                                    "standardized_mae_perturbed": newerr,
                                    "loss_increase": (
                                        newerr - err if newerr is not None else None
                                    ),
                                    "status": (
                                        "ESTIMATED_SOURCE_NATIVE_AGGREGATE"
                                        if reason is None
                                        else "NOT_ESTIMABLE"
                                    ),
                                    "reason": reason
                                    or "Legally encoded source-native sensitivity, not seven-bin product error distribution",
                                }
                            )
        summary = {}
        for variant in VARIANTS:
            pp = pred_by[variant]
            base = {r["condition_id"]: r for r in pred_by["C_BASE"]}
            add = {r["condition_id"]: r for r in pred_by["C_ADD"]}
            group_deltas = []
            for j, target in enumerate(rows[0]["target_names"]):
                errors = np.array([r["prediction"][j] - r["targets"][j] for r in pp])
                scales = np.array([r["train_target_scale"][j] for r in pp])
                comparison = add if variant == "C_JOINT" else base
                deltas = []
                for g in groups:
                    gr = [r for r in pp if r["group_id"] == g]
                    deltas.append(
                        float(
                            np.mean(
                                [
                                    abs(
                                        comparison[r["condition_id"]]["prediction"][j]
                                        - r["targets"][j]
                                    )
                                    - abs(r["prediction"][j] - r["targets"][j])
                                    for r in gr
                                ]
                            )
                        )
                    )
                estimable = not (
                    (variant == "C_C0" and not c0_variation)
                    or (variant in {"C_C1", "C_JOINT"} and not c1_variation)
                )
                effects.append(
                    {
                        "dataset": ds,
                        "effect_type": rows[0]["effect_type"],
                        "model": variant,
                        "comparison": "C_ADD" if variant == "C_JOINT" else "C_BASE",
                        "target": target,
                        "unit": rows[0]["units"][j],
                        "aggregate_conditions": len(rows),
                        "independent_coffee_groups": len(groups),
                        "mae": float(np.abs(errors).mean()),
                        "rmse": float(np.sqrt((errors**2).mean())),
                        "train_standardized_mae": float(np.abs(errors / scales).mean()),
                        "train_standardized_rmse": float(
                            np.sqrt(((errors / scales) ** 2).mean())
                        ),
                        "baseline_error_minus_model_error": (
                            float(np.mean(deltas)) if estimable else None
                        ),
                        "paired_group_95_interval": (
                            interval(deltas) if estimable else None
                        ),
                        "scope": "AGGREGATE_ONLY; source-native roast, not product seven bins",
                        "status": "INCONCLUSIVE" if estimable else "NOT_ESTIMABLE",
                        "reason": (
                            "Small source-specific grouped evaluation; no universal causal or descriptor inference claim"
                            if estimable
                            else "No source roast contrast; fitting a zero-feature control is not evidence of C1 efficacy"
                        ),
                    }
                )
            standardized = np.array(
                [
                    np.mean(
                        np.abs(
                            (np.array(r["prediction"]) - r["targets"])
                            / r["train_target_scale"]
                        )
                    )
                    for r in pp
                ]
            )
            summary[variant] = {
                "standardized_mae": float(standardized.mean()),
                "mae_by_target": {
                    e["target"]: e["mae"]
                    for e in effects
                    if e["dataset"] == ds and e["model"] == variant
                },
                "estimable_c0": c0_variation,
                "estimable_source_native_c1": c1_variation,
            }
            models[ds + ":" + variant] = fit_context(rows, variant)
            fit_count += 1
        comparisons = {}
        for m, b in [("C_C0", "C_BASE"), ("C_C1", "C_BASE"), ("C_JOINT", "C_ADD")]:
            lookup = {r["condition_id"]: r for r in pred_by[b]}
            dscores = []
            for g in groups:
                dif = []
                for r in pred_by[m]:
                    if r["group_id"] != g:
                        continue
                    scale = np.array(r["train_target_scale"])
                    y = np.array(r["targets"])
                    dif.append(
                        np.abs(
                            (np.array(lookup[r["condition_id"]]["prediction"]) - y)
                            / scale
                        ).mean()
                        - np.abs((np.array(r["prediction"]) - y) / scale).mean()
                    )
                dscores.append(float(np.mean(dif)))
            estimable = c0_variation if m == "C_C0" else c1_variation
            comparisons[m + "_minus_" + b] = {
                "error_reduction": float(np.mean(dscores)) if estimable else None,
                "paired_group_95_interval": interval(dscores) if estimable else None,
                "status": "INCONCLUSIVE" if estimable else "NOT_ESTIMABLE",
                "groups": len(groups),
            }
        summaries[ds] = {
            "models": summary,
            "comparisons": comparisons,
            "independent_coffee_groups": len(groups),
            "condition_count": len(rows),
            "effect_type": rows[0]["effect_type"],
            "role": rows[0]["role"],
            "observation_unit": "AGGREGATE_ONLY",
        }
    for stage in [
        "CONTEXT_ONLY",
        "AFTER_Q0_Q1",
        "AFTER_CORRECTION",
        "AFTER_FINAL_COMPARISON",
    ]:
        for condition in [
            "C1_adjacent_one_of_seven",
            "C1_multiple_of_seven",
            "correct_C0_C1",
        ]:
            robust.append(
                {k: None for k in robust[0]}
                | {
                    "dataset": "PRODUCTION_SEVEN_BIN",
                    "stage": stage,
                    "perturbation": condition,
                    "truth_unchanged": True,
                    "status": "NOT_ESTIMABLE",
                    "reason": "No verified seven-bin roast mapping or independent context+answer trajectory. Source-native and actual seven-bin perturbations are not interchangeable.",
                }
            )
    modeldir = owner / "models"
    modeldir.mkdir(mode=0o700, exist_ok=True)
    save(modeldir / "context_models.model.json", models)
    (modeldir / "context_models.model.json").chmod(0o600)
    save(owner / "context_predictions.private.json", pred)
    (owner / "context_predictions.private.json").chmod(0o600)
    write_tsv(OUT / "context_effects.tsv", effects)
    write_tsv(OUT / "context_robustness.tsv", robust)
    manifest = {
        "experiment_id": "backend-sequential-model-v2",
        "baseline_sha": "973f814afe4e592ed521bab952f98f59ca0324ed",
        "project_purpose": "PERSONAL_NONCOMMERCIAL_COFFEE_RESEARCH",
        "context_sources": data["sources"],
        "source_discovery": {
            "new_high_relevance_sources_checked": 0,
            "existing_registered_sources_rechecked": [
                "Iswaldi",
                "Vezzulli",
                "Stanek",
                "Liang",
            ],
            "closed_after_one_targeted_block": True,
            "liang_status": "NOT_ADMITTED_RAW_FILES_UNAVAILABLE",
        },
        "context_data_units": "Source aggregates kept as aggregates; groups are original coffee/sample identities, not panelist or technical repeat counts",
        "context_source_groups": {
            "iswaldi_shared_chemical_sensory": 2,
            "stanek_coffee_lots": 6,
            "vezzulli_coffee_species_samples": 2,
        },
        "numerical_record_counts": {k: len(v) for k, v in data["datasets"].items()},
        "not_estimable": data["not_estimable"],
        "data_type_A": "NUMERICAL_AGGREGATE_SUPERVISION; no reconstructed individual rows",
        "data_type_C_real_feedback": 0,
    }
    save(OUT / "dataset_manifest.json", manifest)
    save(
        OUT / "metrics.json",
        {"context": summaries, "independent_product_confirmation": "NOT_EVALUATED"},
    )
    receipt = {
        "experiment_id": "backend-sequential-model-v2",
        "first_checkpoint_has_actual_fits": True,
        "context_fit_count": fit_count,
        "context_elapsed_seconds": time.time() - start,
        "context_model_path": "$COFFEE_SEQUENTIAL_V2_ROOT/models/context_models.model.json",
        "context_model_sha256": hashlib.sha256(
            (modeldir / "context_models.model.json").read_bytes()
        ).hexdigest(),
        "command": 'python db/scripts/run_context_v2.py --owner-root "$COFFEE_SEQUENTIAL_V2_ROOT"',
        "errors": [
            "Source C1 classes are coarse native labels, not validated production bins.",
            "Only 2 coffee groups in each sensory study; grouped intervals do not establish broad generalization.",
            "Methods differ in time, temperature and extraction mechanics; effects are source-specific recipe associations.",
            "No true seven-bin context plus actual answer trajectories; stage recovery is not estimable from these aggregates.",
        ],
        "original_M1_retained": True,
    }
    save(OUT / "run_receipt.json", receipt)
    print(
        json.dumps(
            {
                "fits": fit_count,
                "elapsed": time.time() - start,
                "comparisons": {k: v["comparisons"] for k, v in summaries.items()},
            },
            indent=2,
        )
    )
    return manifest


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--owner-root", type=Path, required=True)
    run(p.parse_args().owner_root)
