"""Reuse the native context model; new compact per-coffee sensitivity receipt."""

from __future__ import annotations
import argparse, json
from pathlib import Path
from collections import defaultdict
import numpy as np
from flavor_context import VARIANTS, fit_context, predict_context, NATIVE_ROASTS
from prepare_sequential_data import numerical
from run_m2_r1 import OUT, read, save, tsv


def perturb_context(row, train, mode):
    """A two-axis error requires two observed axes and two actual changes."""
    required = (
        {"c0"}
        if mode == "c0_other"
        else {"source_roast"} if mode == "c1_other" else {"c0", "source_roast"}
    )
    altered = dict(row)
    for field in required:
        options = sorted(
            {r[field] for r in train if r[field] and r[field] != row[field]}
        )
        if row[field] is None or not options:
            return None
        altered[field] = options[0]
    return altered


def run(owner, reuse_models=False):
    data = numerical(owner)["datasets"]
    extra = owner / "revisions/r1/context_records.private.json"
    if extra.exists():
        # Only source-native, rights-admitted complete matrices prepared by source adapter.
        for name, rows in read(extra).items():
            if name in data:
                raise ValueError("OLD_DATASET_OVERWRITE")
            data[name] = rows
    rows_out = []
    model_path = owner / "revisions/r1/models/context_native.model.json"
    models = read(model_path) if reuse_models else {}
    fits = 0
    for dataset, rows in data.items():
        groups = sorted({r["group_id"] for r in rows})
        if len(groups) < 2:
            rows_out.append(
                {
                    "dataset": dataset,
                    "groups": len(groups),
                    "status": "NOT_ESTIMABLE",
                    "reason": "No independent coffee group available to train and hold out.",
                }
            )
            continue
        for group in groups:
            train = [r for r in rows if r["group_id"] != group]
            held = [r for r in rows if r["group_id"] == group]
            baselines = {}
            for variant in VARIANTS:
                key = dataset + ":" + variant + ":" + str(groups.index(group))
                model = models[key] if reuse_models else fit_context(train, variant)
                fits += int(not reuse_models)
                models[key] = model
                losses = []
                altered_losses = defaultdict(list)
                for r in held:
                    target = np.array(r["targets"])
                    scale = np.array(model["scaler_parameters"]["scale"])
                    pred = np.array(predict_context(r, model))
                    losses.append(float(np.mean(np.abs((pred - target) / scale))))
                    for mode in ["c0_other", "c1_other", "both"]:
                        alt = perturb_context(r, train, mode)
                        if alt is not None:
                            p = np.array(predict_context(alt, model))
                            altered_losses[mode].append(
                                float(np.mean(np.abs((p - target) / scale)))
                                - losses[-1]
                            )
                loss = float(np.mean(losses))
                baselines[variant] = loss
                rows_out.append(
                    {
                        "dataset": dataset,
                        "model": variant,
                        "groups": len(groups),
                        "held_group_index": groups.index(group),
                        "held_conditions": len(held),
                        "stage": "CONTEXT_ONLY_SOURCE_NATIVE",
                        "standardized_mae": loss,
                        "delta_from_base": loss - baselines["C_BASE"],
                        **{
                            k + "_error_increase": float(np.mean(v))
                            for k, v in altered_losses.items()
                        },
                        **{
                            mode + "_applicable_conditions": len(altered_losses[mode])
                            for mode in ["c0_other", "c1_other", "both"]
                        },
                        **{
                            mode
                            + "_status": (
                                "EVALUATED_SOURCE_NATIVE"
                                if altered_losses[mode]
                                else "NOT_ESTIMABLE"
                            )
                            for mode in ["c0_other", "c1_other", "both"]
                        },
                        "status": "INCONCLUSIVE",
                        "scope": "Source-native aggregate; per-group results, no small-n confidence claim",
                    }
                )
        for stage in ["INITIAL_EXTRACTION", "FOUNDATION_CHECK", "FINAL_RESULT"]:
            rows_out.append(
                {
                    "dataset": dataset,
                    "groups": len(groups),
                    "stage": stage,
                    "status": "NOT_ESTIMABLE",
                    "reason": "No verified production seven-bin C1 + independent stage answers + common specific targets; source-native labels not substituted.",
                }
            )
    if not reuse_models:
        save(model_path, models)
    tsv(OUT / "context_effects.tsv", rows_out)
    result = {
        "actual_fits": len(models),
        "fits_this_execution": fits,
        "sensitivity_pairing": "Each perturbation subtracts its own unperturbed row loss; both requires two genuinely changed observed axes.",
        "datasets": len(data),
        "per_group_table": "context_effects.tsv",
        "production_C1_to_leaf": "NOT_ESTIMABLE",
        "source_native_small_groups": "Report group deltas/range, not robust generalization.",
        "means": {
            dataset: {
                variant: float(
                    np.mean(
                        [
                            r["standardized_mae"]
                            for r in rows_out
                            if r.get("dataset") == dataset and r.get("model") == variant
                        ]
                    )
                )
                for variant in VARIANTS
            }
            for dataset in data
            if len({r["group_id"] for r in data[dataset]}) >= 2
        },
    }
    metrics = read(OUT / "metrics.json")
    metrics["context"] = result
    save(OUT / "metrics.json", metrics)
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-dir", type=Path, required=True)
    p.add_argument("--reuse-models", action="store_true")
    args = p.parse_args()
    print(json.dumps(run(args.owner_dir, args.reuse_models)))
