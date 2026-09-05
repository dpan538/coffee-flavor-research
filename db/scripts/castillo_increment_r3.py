#!/usr/bin/env python3
"""Tiny, separately frozen native Q-grader-score increment; no coffee claim."""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path

import numpy as np

import admit_multiview_sources_r3 as source
from external_construct_r3 import contract_contains, digest, save, sha

VERSION = "m2-r3-castillo-tiny-recorded-grader-increment.v1"
TARGETS = source.CASTILLO_TARGETS
RIDGE = 0.5
SOURCE_SHA = "33673bc90db45730a6e30484f54708b9ce6c7e9a409da09bae9d1bc5ee5815e8"


def protocol():
    return {
        "version": VERSION,
        "source_id": "MADRID_RESTREPO_CASTILLO_2025",
        "doi": "10.1128/msystems.01364-25",
        "source_owner_relative_path": "revisions/r3/castillo_grader_scores.private.json",
        "source_sha256": SOURCE_SHA,
        "role": "AUX_RECORDED_MIXED_QUALITY_GRADER_SCORES",
        "task": "RECONSTRUCTION_OF_PUBLISHED_NATIVE_GRADER_FEATURE_CODES_NOT_SENSORY_INTENSITY",
        "source_units": {"conservative_material_groups": 1, "processing_conditions": 2, "actual_graders": 3, "actual_rows": 6, "target_cells": 30},
        "target_order": list(TARGETS),
        "source_scale": "PUBLISHED_ONE_TO_TEN_SCA_STYLE_FEATURE_CODES;MIXED_QUALITY_VS_ARTICLE_INTENSITY_WORDING;NO_CALIBRATED_INTENSITY",
        "target_exclusions": ["uniformity", "balance", "clean_cup", "sweetness", "general", "totals", "quality_preference_truth"],
        "input_exclusions": "TARGET_SELF_AND_ALL_EXCLUDED_QUALITY_FIELDS;NO_IDS_CONDITION_METADATA_C0_C1_CHEMISTRY_OR_NARRATIVE_DESCRIPTORS",
        "view_budgets": {"V1": "FIRST_AVAILABLE_OTHER_TARGET_FIELD_IN_FIXED_TARGET_ORDER", "V4": "ALL_FOUR_OTHER_TARGET_FIELDS"},
        "data_budgets": {"N1": "EACH_OF_TWO_OUTER_TRAIN_GRADERS_FIT_SEPARATELY;AVERAGE_THEIR_HELD_LOSSES_NOT_PREDICTION_ENSEMBLE", "N2": "BOTH_OUTER_TRAIN_GRADERS_FIT_JOINTLY"},
        "outer_validation": "THREE_LEAVE_ONE_GRADER_OUT_FOLDS;BOTH_CONDITIONS_OF_HELD_GRADER_TRAVEL_TOGETHER;SAME_TWO_CONDITIONS_SHARED_WITH_TRAIN",
        "model": "RIDGE_LINEAR_0.5_WITH_INTERCEPT;TRAIN_ONLY_INPUT_AND_TARGET_POPULATION_MEAN_SD;CLIP_SOURCE_RANGE_1_TO_10",
        "search": "NONE_FIXED_MODEL_NO_PAIRS_OR_TRIPLES_WITH_ONLY_TWO_TRAIN_GRADERS",
        "primary_metric": "HELD_GRADER_MACRO_MAE_ACROSS_SAME_TWO_CONDITIONS_AND_ALL_FIVE_NATIVE_TARGET_CODES",
        "primary_contrasts": ["N2V1_MINUS_N1V1", "N2V4_MINUS_N1V4"],
        "view_contrasts": ["N1V4_MINUS_N1V1", "N2V4_MINUS_N2V1"],
        "direction": "LOWER_IS_BETTER",
        "uncertainty": "ALL_THREE_HELD_GRADER_LOSSES_AND_PER_TARGET_LOSSES_REPORTED;NO_FORMAL_CONFIDENCE_INTERVAL_OR_SIGNIFICANCE_WITH_THREE_PEOPLE",
        "baselines": "NATIVE_TRAIN_TARGET_MEAN_RETAINED_FOR_EACH_DATA_BUDGET",
        "final_models": "BOTH_VIEW_BUDGETS_FIT_ALL_THREE_GRADERS_FOR_RELOAD_ONLY;NO_TRAIN_LOSS_AS_VALIDATION",
        "execution": "ALL_18_OUTER_AND_TWO_FINAL_MODELS_FROZEN_BEFORE_HELD_PREDICTION_PASS;CACHE_HASH_VERIFY_RETURN_SAVED_NO_REEVALUATION",
        "scope": "WITHIN_THIS_SOURCE_AND_THESE_TWO_PROCESSING_CONDITIONS_ONLY;NOT_NEW_COFFEE_NOT_FERMENTATION_CAUSAL_EFFECT_NOT_LIVE_QUESTION_EFFICIENCY",
        "confirmation": "NO_SEPARATE_FRESH_CONFIRMATION_SET_IN_SIX_ROW_SOURCE",
        "source_contribution": "ACTUALLY_ACQUIRED_INDEPENDENT_GRADER_CODES_AND_ONE_TO_TWO_TRAIN_GRADER_INCREMENT;NOT_D0_PLUS_D1_CORE_GAIN",
        "professional_profile_alignment": "NOT_EVALUATED",
        "real_user_alignment": "NOT_EVALUATED",
        "main_M2_scoring_changed": False,
    }


def fields(target, budget):
    if target not in TARGETS or budget not in (1, 4):
        raise ValueError("REGISTERED_TARGET_AND_BUDGET_REQUIRED")
    return [c for c in TARGETS if c != target][:budget]


def value(row, field):
    if row.get("score_masks", {}).get(field) is not True or row.get("score_states", {}).get(field) != "OBSERVED":
        raise ValueError("EXACT_OBSERVED_NATIVE_SCORE_REQUIRED")
    val = row["source_native_scores"][field]
    if isinstance(val, bool) or not isinstance(val, (int, float)) or not 1 <= val <= 10:
        raise ValueError("NATIVE_ONE_TO_TEN_SCORE_REQUIRED")
    return float(val)


def fit(rows, budget):
    if len({r["record_id"] for r in rows}) != len(rows) or not rows:
        raise ValueError("NONEMPTY_UNIQUE_TRAINING_ROWS")
    groups = sorted({r["grader_id"] for r in rows})
    for group in groups:
        if {r["condition_id"] for r in rows if r["grader_id"] == group} != {"SW", "IW"}:
            raise ValueError("BOTH_SOURCE_CONDITIONS_PER_TRAIN_GRADER_REQUIRED")
    heads = {}
    for target in TARGETS:
        inputs = fields(target, budget)
        X = np.array([[value(row, c) for c in inputs] for row in rows])
        y = np.array([value(row, target) for row in rows])
        mean, scale = X.mean(0), X.std(0)
        scale[scale < 1e-8] = 1
        ym, ys = float(y.mean()), float(y.std())
        ys = ys if ys > 1e-8 else 1.0
        Z = (X - mean) / scale
        beta = np.linalg.solve(Z.T @ Z / len(Z) + RIDGE * np.eye(len(inputs)), Z.T @ ((y - ym) / ys) / len(y))
        heads[target] = {"input_fields": inputs, "feature_mean": mean.tolist(), "feature_scale": scale.tolist(),
                         "target_mean": ym, "target_scale": ys, "coefficients": beta.tolist()}
    return {"version": VERSION, "ridge": RIDGE, "budget": budget, "heads": heads, "training_graders": groups,
            "training_record_ids": sorted(r["record_id"] for r in rows), "training_fingerprint": digest(rows),
            "source_scale": protocol()["source_scale"], "production_runtime_input": False}


def predict(row, model, target=None):
    if model["version"] != VERSION or model["ridge"] != RIDGE or set(model["heads"]) != set(TARGETS):
        raise ValueError("FROZEN_SOURCE_NATIVE_MODEL_REQUIRED")
    output = {}
    for c, h in model["heads"].items():
        if target is not None and target != c:
            continue
        if h["input_fields"] != fields(c, model["budget"]):
            raise ValueError("TARGET_LEAK_OR_UNREGISTERED_FEATURE")
        x = np.array([value(row, f) for f in h["input_fields"]])
        output[c] = float(np.clip(h["target_mean"] + h["target_scale"] * (((x - h["feature_mean"]) / h["feature_scale"]) @ h["coefficients"]), 1, 10))
    return output


def evaluate(rows, models):
    if any(set(m["training_graders"]) & {r["grader_id"] for r in rows} for m in models):
        raise ValueError("HELD_GRADER_LEAKAGE")
    evaluated = []
    for row in rows:
        truth = np.array([value(row, c) for c in TARGETS])
        predictions = [predict(row, model) for model in models]
        losses = [np.abs(truth - np.array([p[c] for c in TARGETS])) for p in predictions]
        prior_losses = [np.abs(truth - np.array([model["heads"][c]["target_mean"] for c in TARGETS])) for model in models]
        evaluated.append({"record_id": row["record_id"], "grader_id": row["grader_id"], "condition_id": row["condition_id"],
                          "truth": truth.tolist(), "model_predictions": predictions, "losses_each_model": [v.tolist() for v in losses],
                          "losses": np.mean(losses, axis=0).tolist(), "prior_losses": np.mean(prior_losses, axis=0).tolist()})
    return evaluated


def summarize(results):
    names = ["N1V1", "N1V4", "N2V1", "N2V4"]
    record_ids = [r["record_id"] for r in results[names[0]]]
    if any([r["record_id"] for r in results[n]] != record_ids for n in names) or len(set(record_ids)) != 6:
        raise ValueError("SAME_SIX_HELD_CASES_FOR_ALL_STRATEGIES")
    graders = sorted({r["grader_id"] for r in results[names[0]]})
    grouped = {n: np.array([np.mean([r["losses"] for r in results[n] if r["grader_id"] == g], axis=0) for g in graders]) for n in names}
    priors = {n: np.array([np.mean([r["prior_losses"] for r in results[n] if r["grader_id"] == g], axis=0) for g in graders]) for n in names}

    def block(columns):
        scores = {n: x[:, columns].mean(axis=1) for n, x in grouped.items()}
        comparisons = {}
        for after, before in [("N2V1", "N1V1"), ("N2V4", "N1V4"), ("N1V4", "N1V1"), ("N2V4", "N2V1")]:
            delta = scores[after] - scores[before]
            comparisons[after + "_MINUS_" + before] = {"delta": float(delta.mean()), "held_fold_deltas": delta.tolist(),
                                                      "formal_interval": None, "status": "TINY_SOURCE_DESCRIPTIVE_ONLY", "lower_is_better": True}
        return {"scores": {n: float(x.mean()) for n, x in scores.items()}, "held_fold_scores": {n: x.tolist() for n, x in scores.items()},
                "train_mean_baseline_scores": {n: float(x[:, columns].mean()) for n, x in priors.items()}, "comparisons": comparisons}
    return {"macro": block(list(range(5))), "per_target": {c: block([i]) for i, c in enumerate(TARGETS)}, "held_graders": 3,
            "held_rows": 6, "target_cells_per_strategy": 30, "coverage": 1.0, "status": "TINY_SOURCE_DESCRIPTIVE_ONLY"}


def freeze(owner):
    owner = Path(owner)
    path = owner / protocol()["source_owner_relative_path"]
    if sha(path) != SOURCE_SHA:
        raise ValueError("ADMITTED_SOURCE_HASH_CHANGED")
    contract_path = owner / "revisions/r3/castillo_increment_contract.private.json"
    if contract_path.exists():
        if json.loads(contract_path.read_text())["protocol"] != protocol():
            raise ValueError("PRESERVE_EXISTING_FROZEN_PROTOCOL")
        return contract_path
    save(contract_path, {"protocol": protocol(), "registered_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                         "source_sha256": sha(path), "source_adapter_sha256": sha(source.__file__), "implementation_sha256": sha(__file__),
                         "no_model_fit_or_evaluation_before_freeze": True, "parent_authorization": "EXPLICIT_BOUNDED_CASTILLO_INCREMENT_WITH_FIXED_RIDGE_AND_DATA_VIEW_BUDGETS"})
    return contract_path


def run(owner, contract_path):
    owner, contract_path = Path(owner), Path(contract_path)
    frozen = json.loads(contract_path.read_text())
    if not contract_contains(frozen, protocol()) or sha(__file__) != frozen["implementation_sha256"] or sha(source.__file__) != frozen["source_adapter_sha256"]:
        raise ValueError("EXACT_FROZEN_PROTOCOL_AND_IMPLEMENTATION_REQUIRED")
    path = owner / protocol()["source_owner_relative_path"]
    if sha(path) != SOURCE_SHA:
        raise ValueError("SOURCE_HASH_MISMATCH")
    rows = json.loads(path.read_text())["records"]
    if len(rows) != 6 or len({r["grader_id"] for r in rows}) != 3:
        raise ValueError("REGISTERED_SIX_ROW_THREE_GRADER_SOURCE_REQUIRED")
    private = owner / "revisions/r3"
    receipt_path, summary_path = private / "castillo_increment_receipt.private.json", private / "castillo_increment_public_summary.private.json"
    fingerprint = {"contract_sha256": sha(contract_path), "source_sha256": SOURCE_SHA, "code_sha256": sha(__file__), "adapter_sha256": sha(source.__file__)}
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["status"] != "COMPLETE" or receipt["fingerprint"] != fingerprint:
            raise ValueError("PRESERVE_PRIOR_RUN_OR_INCOMPLETE_RECEIPT")
        for artifact in receipt["artifacts"]:
            if sha(owner / artifact["owner_relative_path"]) != artifact["sha256"]:
                raise ValueError("RETAINED_ARTIFACT_HASH_MISMATCH")
        return json.loads(summary_path.read_text())
    save(receipt_path, {"status": "RUNNING", "fingerprint": fingerprint})
    graders, model_sets, artifacts = sorted({r["grader_id"] for r in rows}), [], []

    def persist(name, payload):
        path = private / name
        save(path, payload)
        artifacts.append({"owner_relative_path": str(path.relative_to(owner)), "sha256": sha(path)})
        return json.loads(path.read_text())

    for fold, held_grader in enumerate(graders):
        train_graders = [g for g in graders if g != held_grader]
        models = {}
        for budget in (1, 4):
            models[f"N1V{budget}"] = [persist(f"castillo_increment_fold{fold}_V{budget}_singleton{i}.model.json", fit([r for r in rows if r["grader_id"] == g], budget)) for i, g in enumerate(train_graders)]
            models[f"N2V{budget}"] = [persist(f"castillo_increment_fold{fold}_V{budget}_both.model.json", fit([r for r in rows if r["grader_id"] in train_graders], budget))]
        model_sets.append((held_grader, models))
    for budget in (1, 4):
        persist(f"castillo_increment_final_V{budget}.model.json", fit(rows, budget))
    persist("castillo_increment_models_frozen.private.json", {"status": "ALL_TWENTY_MODELS_FROZEN_BEFORE_HELD_EVALUATION", "fingerprint": fingerprint, "artifacts": list(artifacts)})
    results = {n: [] for n in ("N1V1", "N1V4", "N2V1", "N2V4")}
    for held_grader, models in model_sets:
        held = [r for r in rows if r["grader_id"] == held_grader]
        for name, fitted in models.items():
            results[name].extend(evaluate(held, fitted))
    summary = {"version": VERSION, **summarize(results), "source_units": protocol()["source_units"], "scope": protocol()["scope"],
               "role": protocol()["role"], "model_fits": 20, "target_fits": 100, "new_independent_coffees": 0, "main_M2_scoring_changed": False,
               "one_grader_policy": "AVERAGE_TWO_SINGLETON_HELD_LOSSES;NO_TWO_GRADER_PREDICTION_ENSEMBLE",
               "private_details_owner_relative": "revisions/r3/castillo_increment_evaluation.private.json",
               "no_formal_uncertainty": "ONLY_THREE_INDEPENDENT_GRADERS_SAME_TWO_PROCESSING_CONDITIONS"}
    persist("castillo_increment_evaluation.private.json", {"fingerprint": fingerprint, "grader_order_private": graders, "results": results, "protocol": protocol()})
    persist(summary_path.name, summary)
    save(receipt_path, {"status": "COMPLETE", "fingerprint": fingerprint, "artifacts": artifacts, "model_fits": 20,
                        "held_evaluation_passes": 1, "cached_rerun": "VERIFY_HASHES_RETURN_SAVED_NO_RECOMPUTATION"})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    parser.add_argument("--freeze-only", action="store_true")
    parser.add_argument("--contract")
    args = parser.parse_args()
    if args.freeze_only:
        path = freeze(args.owner_dir)
        print(json.dumps({"contract_path": str(path), "sha256": sha(path)}))
    else:
        if not args.contract:
            parser.error("--contract is required for fitting")
        print(json.dumps(run(args.owner_dir, args.contract), sort_keys=True, indent=2))
