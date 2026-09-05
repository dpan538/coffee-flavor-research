#!/usr/bin/env python3
"""Offline Rocchetti source-native view reconstruction, never a live M2 input.

The published panel aggregates retain their original 0..9 coding and compound
categories. Regression errors describe reconstruction of that coding; they do
not establish interval sensory intensity or individual assessor reliability.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from threadpoolctl import threadpool_limits

VERSION = "m2-r1-professional-source-views.rocchetti.v1"
SOURCE = "rocchetti_2020"
SCALE_TYPE = "source-native 10-position descriptive rating; published panel aggregate"
SEED = "M2_R1_ROCCHETTI_VIEWS_20260905"
RIDGE = 0.05
# A conservative research partition, not a claim that the source defined these
# blocks. The entire aroma block is hidden together, including total olfaction.
VIEWS = {
    "aroma": [
        "native.olfactory_intensity",
        "native.flowers_and_fresh_fruit",
        "native.vegetable",
        "native.dried_fruits_and_nuts",
        "native.roasted_composite",
        "native.spicy",
        "native.empyreumatic",
        "native.biochemical",
    ],
    "basic_taste": ["native.acidity_intensity", "taste.bitterness"],
    "mouthfeel": ["mouthfeel.body", "mouthfeel.astringency"],
}
TARGETS = [target for view in VIEWS.values() for target in view]


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    path.chmod(0o600)


def observation_value(cell, target):
    """Unknown cells stay masked; valid recorded zero is never dropped."""
    if not cell or cell.get("status") not in {"OBSERVED", "TRUE_ZERO"}:
        return None
    scale = cell.get("scale", {})
    body = target == "mouthfeel.body"
    if (
        scale.get("type") != SCALE_TYPE
        or scale.get("min") != 0
        or scale.get("max") != 9
        or scale.get("anchors") != ["ZERO", "MAX"]
        or scale.get("not_quality_score") is not True
        or scale.get("zero_means_absence") is not (not body)
    ):
        raise ValueError("VERIFIED_SOURCE_NATIVE_SCALE_REQUIRED")
    if body and not scale.get("body_zero_reference"):
        raise ValueError("BODY_ZERO_REFERENCE_REQUIRED")
    value = cell.get("value")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
        or not 0 <= value <= 9
    ):
        raise ValueError("OBSERVED_SOURCE_SCORE_OUTSIDE_VERIFIED_RANGE")
    # Body's zero is a viscosity reference, not an absence label.
    zero_status = "OBSERVED" if body else "TRUE_ZERO"
    expected = zero_status if value == 0 else "OBSERVED"
    if cell["status"] != expected:
        raise ValueError("SOURCE_ZERO_STATUS_MISMATCH")
    return float(value)


def validate_records(records, split_plan, expected_groups=47):
    if split_plan.get("frozen_before_model_results") is not True:
        raise ValueError("PREFROZEN_SOURCE_SPLIT_REQUIRED")
    groups = split_plan["groups"]
    if len(records) != expected_groups or len(groups) != expected_groups:
        raise ValueError("SOURCE_PRODUCT_COUNT_MISMATCH")
    if len({row["group_id"] for row in records}) != len(records):
        raise ValueError("ONE_PUBLISHED_AGGREGATE_PER_PRODUCT_REQUIRED")
    if {row["group_id"] for row in records} != set(groups):
        raise ValueError("SPLIT_GROUPS_DO_NOT_MATCH_SOURCE")
    status_counts = Counter()
    for row in records:
        if (
            row["source_family"] != SOURCE
            or row["role"] != "CORE_PROFESSIONAL"
            or row.get("targets") != []
            or row.get("relevance") != {}
            or row.get("evaluation_group") != row["group_id"]
            or row.get("source_C0") is not None
            or row.get("source_C1") is not None
            or row.get("independent_panelist_answers_available") is not False
            or row.get("split") != groups[row["group_id"]]
            or row["split"] not in {"DEVELOPMENT", "CONFIRMATION"}
            or row.get("task_masks", {}).get("leaf_recovery") is not False
            or row.get("task_masks", {}).get("source_native_attribute_profile")
            is not True
        ):
            raise ValueError("SOURCE_ROLE_OR_PRODUCT_SPLIT_CONTRACT_MISMATCH")
        cells = row["attribute_measurements"]
        if set(cells) != set(TARGETS) or set(row["attribute_masks"]) != set(TARGETS):
            raise ValueError("EXACT_ADMITTED_DESCRIPTIVE_COLUMNS_REQUIRED")
        for target, cell in cells.items():
            if row["attribute_masks"][target] is not True:
                raise ValueError("COMPLETE_PUBLISHED_ATTRIBUTE_MASK_REQUIRED")
            if observation_value(cell, target) is None:
                raise ValueError("COMPLETE_PUBLISHED_MEASUREMENTS_REQUIRED")
            status_counts[cell["status"]] += 1
    return dict(status_counts)


def fold_assignments(records):
    groups = sorted(
        {row["group_id"] for row in records},
        key=lambda group: digest([SEED, "development-product-fold", group]),
    )
    return {group: i % 3 for i, group in enumerate(groups)}


def input_concepts(view):
    return [target for target in TARGETS if target not in VIEWS[view]]


def encode_view(measurements, view, concepts=None):
    """One explicit whitelist encoder shared by fitting and prediction."""
    expected = input_concepts(view)
    if concepts is not None and concepts != expected:
        raise ValueError("HELD_VIEW_OR_UNADMITTED_FIELD_ENTERED_FEATURE_SPEC")
    values = [observation_value(measurements.get(c), c) for c in expected]
    if any(value is None for value in values):
        return None
    return np.asarray(values, dtype=float)


def fit(records):
    if not records or any(row["split"] != "DEVELOPMENT" for row in records):
        raise ValueError("TRAIN_ONLY_DEVELOPMENT_PRODUCTS_REQUIRED")
    if len({row["group_id"] for row in records}) != len(records):
        raise ValueError("REPEATED_PRODUCTS_REQUIRE_EXPLICIT_GROUP_AGGREGATION")
    heads = {}
    for view, targets in VIEWS.items():
        for target in targets:
            examples = []
            for row in records:
                cells = row["attribute_measurements"]
                x = encode_view(cells, view)
                y = observation_value(cells.get(target), target)
                if x is not None and y is not None:
                    examples.append((row, x, y))
            if len(examples) < 2:
                raise ValueError("INSUFFICIENT_OBSERVED_TRAINING_PRODUCTS")
            X = np.asarray([item[1] for item in examples])
            y = np.asarray([item[2] for item in examples])
            mean = X.mean(axis=0)
            scale = X.std(axis=0)
            scale[scale < 1e-8] = 1.0
            y_mean = float(y.mean())
            y_scale = float(y.std()) or 1.0
            Z = (X - mean) / scale
            with threadpool_limits(limits=1):
                beta = np.linalg.solve(
                    Z.T @ Z / len(y) + RIDGE * np.eye(X.shape[1]),
                    Z.T @ ((y - y_mean) / y_scale) / len(y),
                )
            heads[target] = {
                "held_view": view,
                "input_concepts": input_concepts(view),
                "feature_mean": mean.tolist(),
                "feature_scale": scale.tolist(),
                "target_mean": y_mean,
                "target_scale": y_scale,
                "coefficients": beta.tolist(),
                "mean_prior": y_mean,
                "training_groups": [item[0]["group_id"] for item in examples],
                "training_observation_mask": "TARGET_OBSERVED_AND_OTHER_VIEWS_OBSERVED",
            }
    return {
        "version": VERSION,
        "source_family": SOURCE,
        "purpose": "OFFLINE_SOURCE_NATIVE_ATTRIBUTE_VIEW_RECONSTRUCTION",
        "production_runtime_input": False,
        "fine_descriptor_recovery": False,
        "views": VIEWS,
        "view_partition_provenance": "RESEARCHER_REGISTERED_CONSERVATIVE_MODALITY_BLOCKS",
        "fixed_ridge": RIDGE,
        "prediction_clip": [0.0, 9.0],
        "source_aggregation_method": "NOT_REPORTED",
        "score_interpretation": "PUBLISHED_0_TO_9_CODING_NOT_CALIBRATED_INTERVAL_INTENSITY",
        "heads": heads,
    }


def predict(measurements, model):
    if (
        model.get("version") != VERSION
        or model.get("views") != VIEWS
        or set(model.get("heads", {})) != set(TARGETS)
        or model.get("prediction_clip") != [0.0, 9.0]
    ):
        raise ValueError("PROFESSIONAL_VIEW_MODEL_SCHEMA_MISMATCH")
    predictions = {}
    for target, head in model["heads"].items():
        view = head["held_view"]
        if target not in VIEWS[view]:
            raise ValueError("TARGET_VIEW_MISMATCH")
        x = encode_view(measurements, view, head["input_concepts"])
        if x is None:
            predictions[target] = None
            continue
        z = (x - np.asarray(head["feature_mean"])) / np.asarray(head["feature_scale"])
        value = head["target_mean"] + head["target_scale"] * (
            z @ np.asarray(head["coefficients"])
        )
        predictions[target] = float(np.clip(value, 0.0, 9.0))
    return predictions


def evaluate(records, model, split, fold=None):
    training_groups = {
        group for head in model["heads"].values() for group in head["training_groups"]
    }
    if training_groups & {row["group_id"] for row in records}:
        raise ValueError("HELD_PRODUCT_ENTERED_TRAINING")
    results = []
    for row in records:
        predictions = predict(row["attribute_measurements"], model)
        for target in TARGETS:
            y = observation_value(row["attribute_measurements"].get(target), target)
            p = predictions[target]
            if y is None or p is None:
                raise ValueError("REGISTERED_COMPLETE_EVALUATION_CANNOT_DROP_CELLS")
            baseline = model["heads"][target]["mean_prior"]
            results.append(
                {
                    "record_id": row["record_id"],
                    "group_id": row["group_id"],
                    "split": split,
                    "fold": fold,
                    "target": target,
                    "view": model["heads"][target]["held_view"],
                    "observed_native_code": y,
                    "prediction_native_code": p,
                    "training_mean_prior_native_code": baseline,
                    "absolute_error": abs(p - y),
                    "prior_absolute_error": abs(baseline - y),
                    "squared_error": (p - y) ** 2,
                    "prior_squared_error": (baseline - y) ** 2,
                }
            )
    return results


def summarize(results):
    def block(rows):
        units = defaultdict(list)
        for row in rows:
            units[row["group_id"]].append(
                row["absolute_error"] - row["prior_absolute_error"]
            )
        differences = np.asarray([np.mean(units[group]) for group in sorted(units)])
        rng = np.random.default_rng(20260905)
        sampled = rng.choice(differences, size=(2000, len(differences)), replace=True)
        interval = np.quantile(sampled.mean(axis=1), [0.025, 0.975]).tolist()
        return {
            "product_groups": len(units),
            "measured_cells": len(rows),
            "native_code_mae": float(np.mean([r["absolute_error"] for r in rows])),
            "prior_native_code_mae": float(
                np.mean([r["prior_absolute_error"] for r in rows])
            ),
            "mae_delta_model_minus_prior": float(differences.mean()),
            "product_bootstrap95_mae_delta": interval,
            "native_code_rmse": float(
                np.sqrt(np.mean([r["squared_error"] for r in rows]))
            ),
            "prior_native_code_rmse": float(
                np.sqrt(np.mean([r["prior_squared_error"] for r in rows]))
            ),
        }

    return {
        "macro_product": block(results),
        "by_target": {
            target: block([row for row in results if row["target"] == target])
            for target in TARGETS
        },
        "by_view": {
            view: block([row for row in results if row["view"] == view])
            for view in VIEWS
        },
        "uncertainty_scope": "FIXED_PREDICTIONS_PRODUCT_BOOTSTRAP_NO_REFIT_OR_SOURCE_UNCERTAINTY",
        "per_target_intervals": "EXPLORATORY_NOMINAL_NOT_MULTIPLICITY_ADJUSTED",
    }


def run(owner_dir, summary_path):
    start = time.monotonic()
    owner = Path(owner_dir)
    source_path = owner / "rocchetti_attribute_observations.private.json"
    split_path = owner / "rocchetti_split_preregistered.private.json"
    records, split_plan = read(source_path), read(split_path)
    status_counts = validate_records(records, split_plan)
    dev = [row for row in records if row["split"] == "DEVELOPMENT"]
    confirmation = [row for row in records if row["split"] == "CONFIRMATION"]
    if (len(dev), len(confirmation)) != (38, 9):
        raise ValueError("PREFROZEN_38_9_SOURCE_PRODUCT_SPLIT_REQUIRED")
    assignments = fold_assignments(dev)
    plan = {
        "version": VERSION,
        "source_sha256": digest_file(source_path),
        "source_split_sha256": digest_file(split_path),
        "source_split_created_at_utc": split_plan["created_at_utc"],
        "seed": SEED,
        "fixed_ridge": RIDGE,
        "registered_before_fitting": True,
        "views": VIEWS,
        "primary_metric": "MACRO_PRODUCT_MEAN_ABSOLUTE_ERROR_ON_NATIVE_0_TO_9_CODES",
        "feature_transform": "TRAIN_ONLY_CENTER_AND_POPULATION_STANDARD_DEVIATION",
        "target_transform": "TRAIN_ONLY_CENTER_AND_POPULATION_STANDARD_DEVIATION",
        "model": "RIDGE_NORMALIZED_MEAN_SQUARED_CODE_LOSS_WITH_CLIP_0_9",
        "baseline": "PER_TARGET_TRAIN_ONLY_ARITHMETIC_MEAN_OF_PUBLISHED_CODES",
        "fold_assignments": assignments,
        "confirmation_groups": sorted(row["group_id"] for row in confirmation),
        "confirmation_policy": "FIXED_SETTINGS_FIT_ALL_38_DEV_THEN_ONE_FROZEN_EVALUATION",
        "parameter_selection": "NONE_SINGLE_FIXED_RIDGE_NO_RESULT_BASED_SELECTION",
        "unknown_features": "NO_IMPUTATION_OR_ZERO_FILL;INCOMPLETE_OTHER_VIEW_RETURNS_UNAVAILABLE",
    }
    plan["plan_sha256"] = digest(plan)
    plan_path = owner / "professional_views_ROCCHETTI_plan.private.json"
    result_path = owner / "professional_views_ROCCHETTI_metrics.private.json"
    if plan_path.exists():
        if read(plan_path) != plan:
            raise ValueError(
                "REGISTERED_ROCCHETTI_PLAN_CHANGED_USE_EXPLICIT_NEW_VERSION"
            )
    else:
        save(plan_path, plan)
    if result_path.exists():
        old = read(result_path)
        if old["plan_sha256"] != plan["plan_sha256"]:
            raise ValueError("EXISTING_RESULT_PLAN_MISMATCH")
        for entry in old["private_artifact_audit"]:
            if digest_file(owner / entry["relative_path"]) != entry["sha256"]:
                raise ValueError("RETAINED_ROCCHETTI_MODEL_CHANGED")
        save(summary_path, old)
        return old
    artifacts, audits, details = [], [], []

    def persist_model(model, name, held):
        model["experiment_plan_sha256"] = plan["plan_sha256"]
        path = owner / "models" / name
        save(path, model)
        restored = read(path)
        for row in held:
            if predict(row["attribute_measurements"], model) != predict(
                row["attribute_measurements"], restored
            ):
                raise AssertionError("PROFESSIONAL_VIEW_RELOAD_PARITY_FAILED")
        artifacts.append(
            {"relative_path": str(path.relative_to(owner)), "sha256": digest_file(path)}
        )
        return restored

    for fold in range(3):
        train = [row for row in dev if assignments[row["group_id"]] != fold]
        held = [row for row in dev if assignments[row["group_id"]] == fold]
        model = persist_model(
            fit(train),
            f"M2_R1_PROFESSIONAL_VIEWS_ROCCHETTI_fold{fold}.model.json",
            held,
        )
        details.extend(evaluate(held, model, "DEVELOPMENT_OOF", fold))
        audits.append(
            {
                "fold": fold,
                "train_groups": len(train),
                "held_groups": len(held),
                "group_overlap": 0,
                "statistics_fit_train_only": True,
            }
        )
    final_model = persist_model(
        fit(dev), "M2_R1_PROFESSIONAL_VIEWS_ROCCHETTI.model.json", confirmation
    )
    # Settings and all parameters are now frozen before the first confirmation
    # metric is calculated. Re-running exports the retained receipt above.
    confirmation_rows = evaluate(confirmation, final_model, "CONFIRMATION")
    summary = {
        "version": VERSION,
        "plan_sha256": plan["plan_sha256"],
        "source_sha256": plan["source_sha256"],
        "source_doi": "10.1007/s11306-020-01751-6",
        "source_family": SOURCE,
        "source_native_measured_columns": len(TARGETS),
        "source_defined_product_groups": len(records),
        "development_product_groups": len(dev),
        "confirmation_product_groups": len(confirmation),
        "published_measured_cells": sum(status_counts.values()),
        "observation_status_counts": status_counts,
        "professional_panel": {"experts_total": 30, "commissions": 5},
        "independent_panelist_observations_used": 0,
        "independence_limit": "47_SOURCE_DEFINED_PRODUCTS_RAW_LOT_AND_BLEND_CONSTITUENTS_UNKNOWN",
        "source_aggregation_method": "NOT_REPORTED_DO_NOT_CALL_VALUES_MEAN_OR_MEDIAN",
        "body_zero": "VALID_FILTER_COFFEE_VISCOSITY_REFERENCE_NOT_ABSENCE",
        "compound_categories": "RETAINED_WHOLE_WITHOUT_FINE_DESCRIPTOR_CONVERSION",
        "view_partition_provenance": "RESEARCHER_REGISTERED_CONSERVATIVE_MODALITY_BLOCKS",
        "excluded_from_features_and_targets": [
            "quality_and_hedonic_fields",
            "aroma_persistence_and_overall_positive_negative_quality",
            "visual_colour_texture",
            "sample_category_country_award_metadata",
            "panelist_commission_identity",
            "chemical_or_instrumental_measurements",
            "C0_C1_unknown_context",
        ],
        "fixed_ridge": RIDGE,
        "primary_metric": plan["primary_metric"],
        "selection_used": False,
        "whole_target_view_absent_from_features": True,
        "development_folds": audits,
        "development_oof": summarize(details),
        "confirmation_once_frozen": summarize(confirmation_rows),
        "reload_predictions_identical": True,
        "same_encoder_for_fit_and_prediction": True,
        "evaluation_status": "REAL_PUBLISHED_PROFESSIONAL_ATTRIBUTE_LABELS_OFFLINE_MASKED_VIEW_PROXY",
        "product_runtime_foundation_check": "NOT_EVALUATED",
        "main_M2_ranking_changed": False,
        "production_runtime_inputs_changed": False,
        "cross_source_generalization": "NOT_EVALUATED",
        "score_error_interpretation": "RECONSTRUCTION_OF_SOURCE_NUMERIC_CODES_NOT_CALIBRATED_INTERVAL_INTENSITY",
        "scale_copyright_form": "NOT_COPIED_OR_TRAINED;ONLY_ADMITTED_NUMERIC_OBSERVATIONS_USED",
        "private_artifact_audit": artifacts,
        "elapsed_seconds": time.monotonic() - start,
    }
    save(
        owner / "professional_views_ROCCHETTI_evaluation.private.json",
        {"plan_sha256": plan["plan_sha256"], "rows": details + confirmation_rows},
    )
    save(result_path, summary)
    save(summary_path, summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    parser.add_argument(
        "--summary-path", default="/private/tmp/m2-professional-views-summary.json"
    )
    args = parser.parse_args()
    result = run(args.owner_dir, args.summary_path)
    print(
        json.dumps(
            {
                "summary_path": args.summary_path,
                "development": result["development_oof"]["macro_product"],
                "confirmation": result["confirmation_once_frozen"]["macro_product"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
