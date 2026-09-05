#!/usr/bin/env python3
"""A separately frozen nominal-response task for Liberica coffee/leaf treatments.

Observed codes are category IDs, including zero. No ordinal distances, sensory
absences, professional expertise, or compatibility with earlier scales is assumed.
Both confirmation identity axes stay outside every development training set.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from threadpoolctl import threadpool_limits

VERSION = "m2-r2-liberica-nominal-response.v1"
BARAHONA_VERSION = "m2-r2-barahona-consumer-mean.v1"
SEED = 20260905
RIDGE = 0.05
CATEGORIES = list(range(6))
VIEWS = {
    "aroma_named_and_roasty_flavor": [
        "green_aroma",
        "jackfruit_aroma",
        "smoky_aroma",
        "roasty_flavor",
    ],
    "taste_named_and_bitter_aftertaste": [
        "sweet",
        "sour",
        "bitter",
        "bitter_aftertaste",
    ],
    "body_and_astringent_aftertaste": ["body", "astringent_aftertaste"],
}
TARGETS = [target for block in VIEWS.values() for target in block]
BARAHONA_VIEWS = {
    "aroma_fragrance_residual_flavor": ["aroma", "fragrance", "residual_flavor"],
    "taste_named": ["acidity", "bitter", "sweet"],
    "body": ["body"],
}
BARAHONA_TARGETS = [c for block in BARAHONA_VIEWS.values() for c in block]


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    tmp.chmod(0o600)
    tmp.replace(path)


def liberica_protocol():
    return {
        "version": VERSION,
        "source": "MEILINA_LIBERICA_BAGS_2025",
        "source_doi": "10.17632/m3n2gc4dv6.1",
        "role": "AUX_COFFEE_WEAK_LABEL",
        "task": "RECORDED_RESPONSE_PREDICTION",
        "target": "TEN_NOMINAL_SOURCE_RESPONSE_CODES_WHOLE_VIEW_MASKED",
        "view_masks": copy.deepcopy(VIEWS),
        "view_provenance": "RESEARCHER_REGISTERED_CONSERVATIVE_BLOCKS_NOT_VALIDATED_SENSORY_MODALITIES",
        "recorded_categories": CATEGORIES,
        "zero_semantics": "OBSERVED_CATEGORY_ZERO_NOT_ASSUMED_ABSENCE_OR_INTENSITY",
        "scale_interpretation": "NO_ORDINAL_DISTANCE_NO_PSYCHOLOGICAL_DISTANCE",
        "models": ["P0_TRAIN_CATEGORY_FREQUENCIES", "P1_FIXED_RIDGE_MULTINOMIAL"],
        "fixed_ridge": RIDGE,
        "parameter_search": "NONE",
        "input_encoding": "ONE_HOT_SIX_CATEGORIES_FOR_OTHER_ENTIRE_VIEW_FIELDS_ONLY",
        "input_exclusions": [
            "target_view",
            "identities",
            "source_condition_codes",
            "C0_C1",
            "hedonic",
            "quality",
            "chemistry",
            "Excel_derived_recodes_or_averages",
        ],
        "mask": "ALL_TEN_RECORDED_FIELDS_OBSERVED_NO_ZERO_FILL_OR_RECODE",
        "primary_metric": "IDENTITY_MACRO_MULTICLASS_BRIER_SUM_SIX_SQUARED_ERRORS_DIVIDED_BY_SIX",
        "primary_contrast": "P1_MINUS_P0_LOWER_IS_BETTER",
        "training": "INTERSECTION_OF_SOURCE_FROZEN_DEVELOPMENT_PARTICIPANTS_AND_CONDITIONS",
        "development": {
            "participants": 23,
            "conditions": 8,
            "records": 184,
            "outer_folds": 3,
            "holdout_axes": ["participant_id", "condition_id"],
        },
        "confirmation": {
            "held_participant": {"participants": 2, "conditions": 8, "records": 16},
            "held_condition": {"participants": 23, "conditions": 1, "records": 23},
            "both_axes_held": {"participants": 2, "conditions": 1, "records": 2},
            "policy": "ALL_FITS_FROZEN_FIRST_ONE_EVALUATION_RETAIN_AND_REUSE_NO_SELECTION",
            "small_n": "NO_BOOTSTRAP_FOR_FEWER_THAN_THREE_HELD_UNITS;PER_UNIT_DESCRIPTIVE_DELTAS",
        },
        "uncertainty": "5000_FIXED_OOF_PREDICTION_HELD_AXIS_BOOTSTRAPS;OPPOSITE_AXIS_SHARED;NO_REFIT_OR_CROSS_COFFEE_CLAIM",
        "per_target_results": "EXPLORATORY_NOMINAL_NOT_MULTIPLICITY_ADJUSTED",
        "same_budget": "SAME_ACTUALLY_OBSERVED_OTHER_VIEW_CODE_FIELDS;NO_PRODUCTION_QUESTION_OR_TIME_CLAIM",
        "actual_answer_time": "NOT_EVALUATED",
        "professional_profile_alignment": "NOT_EVALUATED",
        "real_user_alignment": "NOT_EVALUATED",
        "main_M2_scoring_changed": False,
        "cross_coffee_generalization": "NOT_ESTIMABLE",
        "data_increment_scope": "NEW_ADMITTED_RESPONSE_TASK_AND_PAIRED_OBSERVATIONS;NOT_POOLED_OLD_TASK_DATA_SIZE_EFFECT",
        "seed": SEED,
    }


def barahona_protocol():
    return {
        "version": BARAHONA_VERSION,
        "source_doi": "10.1002/fsn3.1404",
        "role": "AUX_COFFEE_WEAK_LABEL",
        "task": "RECORDED_RESPONSE_PREDICTION",
        "target": "PUBLISHED_CONSUMER_ORDINAL_CATEGORY_MEANS",
        "view_masks": copy.deepcopy(BARAHONA_VIEWS),
        "scale": "SOURCE_1_TO_10_CATEGORY_MEANS_NOT_PSYCHOLOGICAL_DISTANCE",
        "input": "ONLY_MEASURED_OTHER_ENTIRE_VIEWS;NO_PRICE_LIKING_QUALITY_IDS_CONTEXT",
        "mask": "ALL_SEVEN_SOURCE_SENSORY_MEANS_OBSERVED_NO_IMPUTATION",
        "models": ["P0_TRAIN_TARGET_MEAN", "P1_FIXED_RIDGE_0.5"],
        "fixed_ridge": 0.5,
        "parameter_search": "NONE",
        "standardization": "TRAIN_ONLY_INPUT_AND_TARGET_POPULATION_MEAN_SD",
        "prediction_clip": [1, 10],
        "primary_metric": "PRODUCT_MACRO_SOURCE_CODE_MAE",
        "primary_contrast": "P1_MINUS_P0_LOWER_IS_BETTER",
        "development_products": 14,
        "outer_folds": 3,
        "confirmation_products": 4,
        "confirmation_policy": "ONE_FROZEN_EVALUATION_NO_TUNING;FOUR_PRODUCT_DESCRIPTIVE_MEAN_AND_RANGE_NO_ROBUST_CONFIRMATION_CLAIM",
        "uncertainty": "DEVELOPMENT_5000_FIXED_PREDICTION_PRODUCT_BOOTSTRAPS;NO_REFIT_SOURCE_OR_INDIVIDUAL_ASSESSOR_UNCERTAINTY",
        "professional_profile": "NOT_EVALUATED",
        "independent_individual_responses": "NOT_OBTAINED_PUBLISHED_MEANS_ONLY",
        "raw_lot_identity": "NOT_VERIFIED_SOURCE_PRODUCT_IDS_ONLY",
        "same_budget": "SAME_OTHER_VIEW_PUBLISHED_CODE_CELLS;NO_REAL_QUESTION_OR_TIME_CLAIM",
        "main_M2_scoring_changed": False,
        "pooled_with_Rocchetti_or_Liberica": False,
        "seed": SEED,
    }


def increment_protocol():
    return {
        "version": "m2-r2-independent-new-response-tasks.v1",
        "liberica": liberica_protocol(),
        "barahona": barahona_protocol(),
        "cross_source_score_average": "FORBIDDEN_DIFFERENT_TARGET_SPACES_AND_UNITS",
        "main_M2_scoring_changed": False,
    }


def learning_curve_protocol():
    return {
        "version": "m2-r2-barahona-fixed-data-size-control.v1",
        "source_doi": "10.1002/fsn3.1404",
        "task": "WITHIN_SOURCE_TRAINING_PRODUCT_INCREMENT",
        "base_protocol": barahona_protocol(),
        "models": [
            "SAME_RIDGE_0.5_HALF_TRAIN_PRODUCTS",
            "SAME_RIDGE_0.5_FULL_TRAIN_PRODUCTS",
        ],
        "subset": "SORT_GROUPS_BY_SHA256_OF_VERSION_SEED_HALF_PRODUCT_ID;TAKE_CEILING_N_TRAIN_DIVIDED_BY_TWO",
        "selection_scope": "OUTER_TRAIN_ONLY_NO_HELD_LABELS_OR_SELECTION",
        "outer_folds": "SAME_THREE_PRODUCT_FOLDS_AS_FULL_SOURCE_TASK",
        "fixed_dimensions_masks_and_inputs": copy.deepcopy(BARAHONA_VIEWS),
        "primary_metric": "SAME_HELD_PRODUCT_MACRO_SOURCE_CODE_MAE",
        "primary_contrast": "FULL_MINUS_HALF_LOWER_IS_BETTER",
        "parameters": "RIDGE_0.5_REUSED_NO_PARAMETER_SEARCH;ALL_STATISTICS_FIT_WITHIN_EACH_TRAIN_SUBSET",
        "final_training_counts": {"half": 7, "full": 14},
        "confirmation": "FOUR_PRODUCTS_ONCE_AFTER_BOTH_MODELS_FROZEN;DESCRIPTIVE_NO_ROBUST_CONFIRMATION_CLAIM",
        "interpretation": "SOURCE_SPECIFIC_TRAINING_PRODUCT_COUNT_EFFECT_NOT_D0_PLUS_D1_M2_GAIN",
        "source_condition_controls": "SAME_SOURCE_SENSORY_COLUMNS_NATIVE_SCALE_TARGETS_INPUT_BUDGET_AND_HELD_PRODUCTS",
        "seed": SEED,
    }


def half_products(rows):
    if not rows or any(r["split"] != "DEVELOPMENT" for r in rows):
        raise ValueError("HALF_SUBSET_DEVELOPMENT_PRODUCTS_ONLY")
    if len({r["group_id"] for r in rows}) != len(rows):
        raise ValueError("HALF_SUBSET_DUPLICATE_PRODUCT")
    ordered = sorted(
        rows,
        key=lambda r: digest(
            [learning_curve_protocol()["version"], SEED, "half", r["group_id"]]
        ),
    )
    return ordered[: (len(ordered) + 1) // 2]


def validate(package):
    contract, records = package["contract"], package["records"]
    if (
        contract.get("source_id") != "MEILINA_LIBERICA_BAGS_2025"
        or contract.get("admitted_measurement") != "nominal_categorical_response"
        or contract.get("split_frozen_before_model_fit") is not True
        or contract.get("license") != "CC-BY-4.0"
        or {f["id"] for f in contract["fields"]} != set(TARGETS)
        or contract.get("native_observed_codes") != CATEGORIES
    ):
        raise ValueError("ADMITTED_SOURCE_RESPONSE_CONTRACT_REQUIRED")
    identities, pairs = set(), set()
    for row in records:
        if (
            row["role"] != "AUX_COFFEE_WEAK_LABEL"
            or row["source_family"] != "family.meilina_liberica_bags_2025"
            or row["source_C0"] is not None
            or row["source_C1"] is not None
            or set(row["responses"]) != set(TARGETS)
            or set(row["response_masks"]) != set(TARGETS)
            or row["participant_split"]
            != contract["participant_assignment"][row["participant_id"]]
            or row["condition_split"]
            != contract["condition_assignment"][row["condition_id"]]
        ):
            raise ValueError("NATIVE_RESPONSE_RECORD_CONTRACT_MISMATCH")
        pair = (row["participant_id"], row["condition_id"])
        if row["record_id"] in identities or pair in pairs:
            raise ValueError("DUPLICATE_SOURCE_RESPONSE")
        identities.add(row["record_id"])
        pairs.add(pair)
        for target in TARGETS:
            if observed(row, target) is None:
                raise ValueError("COMPLETE_OBSERVED_RESPONSE_BLOCK_REQUIRED")
    if len(records) != 225 or len(pairs) != 25 * 9:
        raise ValueError("SOURCE_CROSSED_25_BY_9_MATRIX_REQUIRED")
    splits = partition(records)
    if {key: len(value) for key, value in splits.items()} != {
        "development": 184,
        "held_participant": 16,
        "held_condition": 23,
        "both_axes_held": 2,
    }:
        raise ValueError("FROZEN_INTERSECTION_SPLITS_REQUIRED")
    return splits


def observed(row, target):
    if (
        row.get("response_masks", {}).get(target) is not True
        or row.get("response_states", {}).get(target) != "OBSERVED"
    ):
        return None
    code = row.get("responses", {}).get(target)
    if isinstance(code, bool) or not isinstance(code, int) or code not in CATEGORIES:
        raise ValueError("RECORDED_NOMINAL_CATEGORY_REQUIRED")
    return code


def inputs(view):
    return [target for target in TARGETS if target not in VIEWS[view]]


def encode(row, view, specification=None):
    names = inputs(view)
    if specification is not None and specification != names:
        raise ValueError("HELD_VIEW_OR_UNREGISTERED_FEATURE")
    codes = [observed(row, target) for target in names]
    if any(code is None for code in codes):
        return None
    return np.eye(6)[codes].reshape(-1)


def partition(records):
    result = {
        key: []
        for key in [
            "development",
            "held_participant",
            "held_condition",
            "both_axes_held",
        ]
    }
    for row in records:
        a, b = row["participant_split"], row["condition_split"]
        if a not in {"DEVELOPMENT", "CONFIRMATION"} or b not in {
            "DEVELOPMENT",
            "CONFIRMATION",
        }:
            raise ValueError("PREFROZEN_IDENTITY_SPLIT_REQUIRED")
        key = (
            "development"
            if (a, b) == ("DEVELOPMENT", "DEVELOPMENT")
            else (
                "held_participant"
                if b == "DEVELOPMENT"
                else "held_condition" if a == "DEVELOPMENT" else "both_axes_held"
            )
        )
        result[key].append(row)
    return result


def fit_multinomial(X, y):
    X, y = np.asarray(X, float), np.asarray(y, int)
    prior = np.bincount(y, minlength=6) / len(y)
    initial = np.zeros((6, X.shape[1] + 1))
    initial[:, 0] = np.log(np.maximum(prior, 1e-6))
    initial[:, 0] -= initial[:, 0].mean()
    augmented = np.column_stack([np.ones(len(X)), X])
    labels = np.eye(6)[y]

    def objective(flat):
        beta = flat.reshape(initial.shape)
        logits = augmented @ beta.T
        loss = (
            np.mean(logsumexp(logits, axis=1) - logits[np.arange(len(y)), y])
            + RIDGE * np.sum(beta[:, 1:] ** 2) / 2
        )
        gradient = (softmax(logits, axis=1) - labels).T @ augmented / len(y)
        gradient[:, 1:] += RIDGE * beta[:, 1:]
        return float(loss), gradient.ravel()

    with threadpool_limits(limits=1):
        fitted = minimize(
            objective,
            initial.ravel(),
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": 1000, "ftol": 1e-11, "gtol": 1e-7},
        )
    if not fitted.success:
        raise RuntimeError("FIXED_MULTINOMIAL_FIT_FAILED:" + str(fitted.message))
    beta = fitted.x.reshape(initial.shape)
    return {
        "intercepts": beta[:, 0].tolist(),
        "coefficients": beta[:, 1:].tolist(),
        "prior": prior.tolist(),
        "iterations": int(fitted.nit),
        "loss": float(fitted.fun),
    }


def fit(records):
    if not records or any(
        row["participant_split"] != "DEVELOPMENT"
        or row["condition_split"] != "DEVELOPMENT"
        for row in records
    ):
        raise ValueError("BOTH_IDENTITY_AXES_MUST_BE_DEVELOPMENT")
    if len({r["record_id"] for r in records}) != len(records):
        raise ValueError("DUPLICATE_TRAIN_OBSERVATION")
    heads = {}
    for view, block in VIEWS.items():
        vectors = [encode(row, view) for row in records]
        if any(vector is None for vector in vectors):
            raise ValueError("COMPLETE_OTHER_VIEW_INPUT_REQUIRED")
        for target in block:
            codes = [observed(row, target) for row in records]
            if any(code is None for code in codes):
                raise ValueError("COMPLETE_TARGET_VIEW_REQUIRED")
            head = fit_multinomial(vectors, codes)
            head.update(input_fields=inputs(view), target_view=view)
            heads[target] = head
    return {
        "version": VERSION,
        "views": VIEWS,
        "categories": CATEGORIES,
        "ridge": RIDGE,
        "heads": heads,
        "training_fingerprint": digest(records),
        "training_ids": {
            key: sorted({r[key] for r in records})
            for key in ["record_id", "participant_id", "condition_id"]
        },
        "source_native_nominal_only": True,
        "main_M2_input": False,
    }


def predict(row, model):
    if (
        model.get("version") != VERSION
        or model.get("views") != VIEWS
        or model.get("categories") != CATEGORIES
        or set(model.get("heads", {})) != set(TARGETS)
    ):
        raise ValueError("NOMINAL_RESPONSE_MODEL_CONTRACT_REQUIRED")
    out = {}
    for target, head in model["heads"].items():
        if target not in VIEWS[head["target_view"]]:
            raise ValueError("TARGET_VIEW_MISMATCH")
        x = encode(row, head["target_view"], head["input_fields"])
        out[target] = (
            softmax(np.asarray(head["coefficients"]) @ x + head["intercepts"]).tolist()
            if x is not None
            else None
        )
    return out


def evaluate(records, model, axis, stage):
    if axis in {"participant_id", "condition_id"} and set(
        model["training_ids"][axis]
    ) & {r[axis] for r in records}:
        raise ValueError("HELD_IDENTITY_ENTERED_TRAINING")
    if axis == "both" and any(
        set(model["training_ids"][key]) & {r[key] for r in records}
        for key in ["participant_id", "condition_id"]
    ):
        raise ValueError("DOUBLE_HOLDOUT_IDENTITY_ENTERED_TRAINING")
    result = []
    for row in records:
        predicted = predict(row, model)
        codes = [observed(row, c) for c in TARGETS]
        if any(c is None for c in codes) or any(predicted[c] is None for c in TARGETS):
            raise ValueError("CANNOT_DROP_EVALUATION_CELL")
        truth, probabilities = np.eye(6)[codes], np.asarray(
            [predicted[c] for c in TARGETS]
        )
        priors = np.asarray([model["heads"][c]["prior"] for c in TARGETS])
        result.append(
            {
                "record_id": row["record_id"],
                "participant_id": row["participant_id"],
                "condition_id": row["condition_id"],
                "unit": row[axis] if axis != "both" else row["record_id"],
                "axis": axis,
                "stage": stage,
                "codes": codes,
                "probabilities": probabilities.tolist(),
                "priors": priors.tolist(),
                "model_brier": np.mean((probabilities - truth) ** 2, axis=1).tolist(),
                "prior_brier": np.mean((priors - truth) ** 2, axis=1).tolist(),
            }
        )
    return result


def summary(rows, force_descriptive=False):
    def block(indices):
        units = defaultdict(list)
        for row in rows:
            units[row["unit"]].append(
                [
                    float(np.mean(np.asarray(row[key])[indices]))
                    for key in ["model_brier", "prior_brier"]
                ]
            )
        values = np.asarray([np.mean(units[u], axis=0) for u in sorted(units)])
        delta = values[:, 0] - values[:, 1]
        interval = None
        if len(units) >= 3 and not force_descriptive:
            rng = np.random.default_rng(SEED)
            interval = np.quantile(
                delta[rng.integers(0, len(delta), (5000, len(delta)))].mean(1),
                [0.025, 0.975],
            ).tolist()
        status = (
            "NOT_ESTIMABLE" if len(units) < 2 or force_descriptive else "INCONCLUSIVE"
        )
        if interval is not None:
            status = (
                "SUPPORTED_IN_DECLARED_SCOPE"
                if interval[1] < 0
                else "NO_IMPROVEMENT" if interval[0] > 0 else "INCONCLUSIVE"
            )
        return {
            "held_units": len(units),
            "observations": len(rows),
            "evaluated_cells": len(rows) * len(indices),
            "model_brier": float(values[:, 0].mean()),
            "prior_brier": float(values[:, 1].mean()),
            "delta_model_minus_prior": float(delta.mean()),
            "paired_unit_95_interval": interval,
            "status": status,
            "unit_delta_range": [float(delta.min()), float(delta.max())],
            "unit_deltas_private": dict(zip(sorted(units), delta.tolist())),
        }

    return {
        "macro": block(list(range(10))),
        "by_target": {t: block([i]) for i, t in enumerate(TARGETS)},
        "by_view": {
            view: block([TARGETS.index(t) for t in ts]) for view, ts in VIEWS.items()
        },
        "coverage": 1.0,
        "uncertainty_scope": liberica_protocol()["uncertainty"],
        "source_scope": "LIBERICA_COFFEE_AND_LEAF_TREATMENT_CODES;NOT_PROFESSIONAL_PROFILE_OR_CROSS_COFFEE",
    }


def folds(records, axis):
    ids = sorted(
        {row[axis] for row in records},
        key=lambda identity: digest([VERSION, SEED, axis, identity]),
    )
    if len(ids) < 3:
        raise ValueError("THREE_HELD_UNITS_REQUIRED")
    return {identity: index % 3 for index, identity in enumerate(ids)}


def public_summary(value):
    if isinstance(value, dict):
        return {
            key: public_summary(v)
            for key, v in value.items()
            if key != "unit_deltas_private"
        }
    if isinstance(value, list):
        return [public_summary(v) for v in value]
    return value


def run_liberica(owner, contract_path):
    private = Path(owner) / "revisions/r2"
    contract = read(contract_path)
    if contract.get("profiles_increment") != increment_protocol():
        raise ValueError("SEPARATELY_FROZEN_INCREMENT_CONTRACT_REQUIRED")
    source = private / "liberica_rata_records.private.json"
    if contract.get("source_sha256", {}).get(source.name) != sha(source):
        raise ValueError("FROZEN_LIBERICA_SOURCE_HASH_MISMATCH")
    package = read(source)
    splits = validate(package)
    plan = {
        "protocol": increment_protocol(),
        "source_sha256": sha(source),
        "code_sha256": sha(__file__),
        "frozen_main_increment_contract_sha256": sha(contract_path),
    }
    plan["hash"] = digest(plan)
    plan_path, result_path = (
        private / "profiles_increment_liberica_plan.private.json",
        private / "profiles_increment_liberica_summary.private.json",
    )
    if plan_path.exists() and read(plan_path) != plan:
        raise ValueError("RETAINED_INCREMENT_PLAN_CHANGED")
    if result_path.exists():
        old = read(result_path)
        if old["plan_hash"] != plan["hash"]:
            raise ValueError("RETAINED_INCREMENT_RESULT_PLAN_MISMATCH")
        for artifact in old["artifacts"]:
            if sha(private / artifact["relative_path"]) != artifact["sha256"]:
                raise ValueError("RETAINED_INCREMENT_ARTIFACT_CHANGED")
        return old
    confirmation_lock = private / "profiles_increment_confirmation_lock.private.json"
    if confirmation_lock.exists():
        raise ValueError(
            "CONFIRMATION_ALREADY_STARTED_REVIEW_RETAINED_ROWS_NO_AUTOMATIC_REEVALUATION"
        )
    save(plan_path, plan)
    started = time.monotonic()
    dev = splits["development"]
    artifacts, details, summaries, audit = [], {}, {}, []

    def persist(model, name, example):
        path = private / ("profiles_increment_" + name + ".model.json")
        save(path, model)
        loaded = read(path)
        if predict(example, loaded) != predict(example, model):
            raise AssertionError("INCREMENT_RELOAD_PARITY_FAILED")
        artifacts.append({"relative_path": path.name, "sha256": sha(path)})
        return loaded

    for axis in ["participant_id", "condition_id"]:
        assignment = folds(dev, axis)
        rows = []
        for fold in range(3):
            train = [r for r in dev if assignment[r[axis]] != fold]
            held = [r for r in dev if assignment[r[axis]] == fold]
            model = persist(fit(train), axis + "_fold" + str(fold), held[0])
            rows.extend(evaluate(held, model, axis, "DEVELOPMENT_OUTER"))
            audit.append(
                {
                    "axis": axis,
                    "fold": fold,
                    "train_units": sorted({r[axis] for r in train}),
                    "held_units": sorted({r[axis] for r in held}),
                    "train_record_ids": model["training_ids"]["record_id"],
                    "confirmation_rows_in_train": 0,
                }
            )
        details[axis] = rows
        summaries[axis] = summary(rows)
    final = persist(fit(dev), "final", dev[0])
    # The entire fit is complete before any confirmation-target evaluation.
    save(
        confirmation_lock,
        {"plan_hash": plan["hash"], "status": "STARTED", "all_parameters_frozen": True},
    )
    confirmation = {}
    for cohort, axis in [
        ("held_participant", "participant_id"),
        ("held_condition", "condition_id"),
        ("both_axes_held", "both"),
    ]:
        rows = evaluate(splits[cohort], final, axis, "CONFIRMATION_ONCE")
        details[cohort] = rows
        confirmation[cohort] = summary(rows, force_descriptive=axis == "both")
    detail_path = private / "profiles_increment_evaluation.private.json"
    save(
        detail_path,
        {
            "plan_hash": plan["hash"],
            "target_order": TARGETS,
            "rows": details,
            "fold_audit": audit,
        },
    )
    artifacts.append({"relative_path": detail_path.name, "sha256": sha(detail_path)})
    save(
        confirmation_lock,
        {
            "plan_hash": plan["hash"],
            "status": "COMPLETE",
            "all_parameters_frozen": True,
            "evaluation_sha256": sha(detail_path),
        },
    )
    artifacts.append(
        {"relative_path": confirmation_lock.name, "sha256": sha(confirmation_lock)}
    )
    result = {
        "version": VERSION,
        "plan_hash": plan["hash"],
        "protocol": increment_protocol(),
        "development": summaries,
        "confirmation_once": confirmation,
        "contribution": {
            "new_independent_collection_studies": 1,
            "source_defined_treatments": 9,
            "participants": 25,
            "observed_records": 225,
            "observed_cells": 2250,
            "traceable_raw_coffee_lots": None,
            "cohort_dependence": "ONE_STUDY_MATERIAL_WITH_SHARED_COFFEE_AND_LEAF_TREATMENTS;NOT_9_INDEPENDENT_COFFEES",
            "old_task_data_size_effect": "NOT_ESTIMABLE_INCOMPATIBLE_NATIVE_TARGETS_AND_PROTOCOL",
        },
        "other_view_observed_cell_cost_per_target": {
            t: len(inputs(v)) for v, ts in VIEWS.items() for t in ts
        },
        "source_provenance": {
            key: package["contract"][key]
            for key in [
                "source_url",
                "doi",
                "attribution",
                "license",
                "raw_sha256",
                "workbook_sha256",
                "scale_anchor_status",
                "zero_semantics",
            ]
        },
        "actual_bundle_fits": 7,
        "actual_target_fits": 70,
        "retained_models": 7,
        "elapsed_seconds": time.monotonic() - started,
        "artifacts": artifacts,
        "main_M2_scoring_changed": False,
        "real_user_time_efficiency": "NOT_EVALUATED",
        "real_user_alignment": "NOT_EVALUATED",
    }
    save(result_path, result)
    return result


def barahona_value(row, target):
    if (
        row.get("attribute_masks", {}).get(target) is not True
        or row.get("attribute_states", {}).get(target) != "OBSERVED"
    ):
        return None
    value = row.get("attribute_measurements", {}).get(target)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
        or not 1 <= value <= 10
    ):
        raise ValueError("OBSERVED_BARAHONA_NATIVE_MEAN_REQUIRED")
    return float(value)


def barahona_inputs(view):
    return [c for c in BARAHONA_TARGETS if c not in BARAHONA_VIEWS[view]]


def encode_barahona(row, view, specification=None):
    names = barahona_inputs(view)
    if specification is not None and specification != names:
        raise ValueError("BARAHONA_HELD_VIEW_OR_UNREGISTERED_FIELD")
    values = [barahona_value(row, c) for c in names]
    return np.asarray(values) if all(v is not None for v in values) else None


def validate_barahona(package):
    c, rows = package["contract"], package["records"]
    if (
        c.get("source_id") != "BARAHONA_COLOMBIAN_CONSUMERS_2020"
        or c.get("license") != "CC-BY-4.0"
        or c.get("split_frozen_before_model_fit") is not True
        or {field["id"] for field in c["fields"]} != set(BARAHONA_TARGETS)
        or c.get("scale", {}).get("minimum") != 1
        or c.get("scale", {}).get("maximum") != 10
        or c.get("task_masks", {}).get("professional_profile") is not False
    ):
        raise ValueError("ADMITTED_BARAHONA_CONSUMER_MEAN_CONTRACT_REQUIRED")
    if len(rows) != 18 or len({r["group_id"] for r in rows}) != 18:
        raise ValueError("EIGHTEEN_UNIQUE_SOURCE_PRODUCTS_REQUIRED")
    for row in rows:
        if (
            row["role"] != "AUX_COFFEE_WEAK_LABEL"
            or row["source_family"] != "family.barahona_colombian_consumers_2020"
            or row["split"] != c["product_assignment"][row["group_id"]]
            or set(row["attribute_measurements"]) != set(BARAHONA_TARGETS)
            or any(barahona_value(row, target) is None for target in BARAHONA_TARGETS)
        ):
            raise ValueError("EXACT_BARAHONA_SENSORY_MASK_AND_SPLIT_REQUIRED")
    dev = [r for r in rows if r["split"] == "DEVELOPMENT"]
    conf = [r for r in rows if r["split"] == "CONFIRMATION"]
    if (len(dev), len(conf)) != (14, 4):
        raise ValueError("PREFROZEN_FOURTEEN_FOUR_PRODUCT_SPLIT_REQUIRED")
    return dev, conf


def fit_barahona(rows):
    if not rows or any(r["split"] != "DEVELOPMENT" for r in rows):
        raise ValueError("BARAHONA_DEVELOPMENT_PRODUCTS_ONLY")
    if len({r["group_id"] for r in rows}) != len(rows):
        raise ValueError("BARAHONA_DUPLICATE_PRODUCT")
    heads = {}
    for view, block in BARAHONA_VIEWS.items():
        vectors = [encode_barahona(r, view) for r in rows]
        if any(x is None for x in vectors):
            raise ValueError("BARAHONA_COMPLETE_OTHER_VIEW_REQUIRED")
        X = np.asarray(vectors)
        mean, scale = X.mean(0), X.std(0)
        scale[scale < 1e-8] = 1
        Z = (X - mean) / scale
        for target in block:
            y = [barahona_value(r, target) for r in rows]
            if any(v is None for v in y):
                raise ValueError("BARAHONA_COMPLETE_TARGET_REQUIRED")
            y = np.asarray(y)
            ym, ys = float(y.mean()), float(y.std()) or 1.0
            with threadpool_limits(limits=1):
                beta = np.linalg.solve(
                    Z.T @ Z / len(y) + 0.5 * np.eye(Z.shape[1]),
                    Z.T @ ((y - ym) / ys) / len(y),
                )
            heads[target] = {
                "view": view,
                "input_fields": barahona_inputs(view),
                "feature_mean": mean.tolist(),
                "feature_scale": scale.tolist(),
                "target_mean": ym,
                "target_scale": ys,
                "coefficients": beta.tolist(),
                "prior": ym,
            }
    return {
        "version": BARAHONA_VERSION,
        "views": BARAHONA_VIEWS,
        "heads": heads,
        "training_groups": sorted(r["group_id"] for r in rows),
        "training_fingerprint": digest(rows),
        "ridge": 0.5,
        "professional_profile": False,
        "main_M2_input": False,
    }


def predict_barahona(row, model):
    if (
        model.get("version") != BARAHONA_VERSION
        or model.get("views") != BARAHONA_VIEWS
        or set(model.get("heads", {})) != set(BARAHONA_TARGETS)
    ):
        raise ValueError("BARAHONA_MODEL_CONTRACT_REQUIRED")
    out = {}
    for target, head in model["heads"].items():
        if target not in BARAHONA_VIEWS[head["view"]]:
            raise ValueError("BARAHONA_TARGET_VIEW_MISMATCH")
        x = encode_barahona(row, head["view"], head["input_fields"])
        out[target] = (
            float(
                np.clip(
                    head["target_mean"]
                    + head["target_scale"]
                    * (
                        (x - head["feature_mean"])
                        / head["feature_scale"]
                        @ head["coefficients"]
                    ),
                    1,
                    10,
                )
            )
            if x is not None
            else None
        )
    return out


def evaluate_barahona(rows, model, stage):
    if set(model["training_groups"]) & {r["group_id"] for r in rows}:
        raise ValueError("BARAHONA_HELD_PRODUCT_IN_TRAIN")
    output = []
    for row in rows:
        predictions = predict_barahona(row, model)
        y, p = [barahona_value(row, c) for c in BARAHONA_TARGETS], [
            predictions[c] for c in BARAHONA_TARGETS
        ]
        if any(v is None for v in y + p):
            raise ValueError("BARAHONA_NO_EVALUATION_CELL_DROPPING")
        prior = [model["heads"][c]["prior"] for c in BARAHONA_TARGETS]
        output.append(
            {
                "record_id": row["record_id"],
                "unit": row["group_id"],
                "stage": stage,
                "truth": y,
                "prediction": p,
                "prior": prior,
                "model_mae": np.abs(np.asarray(p) - y).tolist(),
                "prior_mae": np.abs(np.asarray(prior) - y).tolist(),
            }
        )
    return output


def summarize_barahona(rows, confirmation=False):
    def block(indices):
        values = np.asarray(
            [
                [
                    np.mean(np.asarray(r[key])[indices])
                    for key in ["model_mae", "prior_mae"]
                ]
                for r in rows
            ]
        )
        delta = values[:, 0] - values[:, 1]
        interval = None
        if not confirmation:
            rng = np.random.default_rng(SEED)
            interval = np.quantile(
                delta[rng.integers(0, len(delta), (5000, len(delta)))].mean(1),
                [0.025, 0.975],
            ).tolist()
        status = (
            "INCONCLUSIVE"
            if interval is None or interval[0] <= 0 <= interval[1]
            else "SUPPORTED_IN_DECLARED_SCOPE" if interval[1] < 0 else "NO_IMPROVEMENT"
        )
        return {
            "products": len(rows),
            "evaluated_cells": len(rows) * len(indices),
            "model_native_code_mae": float(values[:, 0].mean()),
            "prior_native_code_mae": float(values[:, 1].mean()),
            "delta_model_minus_prior": float(delta.mean()),
            "paired_product_95_interval": interval,
            "unit_delta_range": [float(delta.min()), float(delta.max())],
            "status": status,
            "unit_deltas_private": {r["unit"]: float(v) for r, v in zip(rows, delta)},
        }

    return {
        "macro": block(list(range(7))),
        "by_target": {c: block([i]) for i, c in enumerate(BARAHONA_TARGETS)},
        "by_view": {
            view: block([BARAHONA_TARGETS.index(c) for c in block_targets])
            for view, block_targets in BARAHONA_VIEWS.items()
        },
        "coverage": 1.0,
        "source_scope": "CONSUMER_PUBLISHED_ORDINAL_MEANS_NOT_PROFESSIONAL_OR_INDIVIDUAL_ALIGNMENT",
        "uncertainty": (
            barahona_protocol()["confirmation_policy"]
            if confirmation
            else barahona_protocol()["uncertainty"]
        ),
    }


def summarize_learning_curve(full, half, confirmation=False):
    if len(full) != len(half) or any(
        a["record_id"] != b["record_id"] or a["truth"] != b["truth"]
        for a, b in zip(full, half)
    ):
        raise ValueError("LEARNING_CURVE_REQUIRES_IDENTICAL_HELD_ROWS_AND_TARGETS")
    paired = [
        {"unit": a["unit"], "model_mae": a["model_mae"], "prior_mae": b["model_mae"]}
        for a, b in zip(full, half)
    ]
    result = summarize_barahona(paired, confirmation)
    names = {
        "model_native_code_mae": "full_training_mae",
        "prior_native_code_mae": "half_training_mae",
        "delta_model_minus_prior": "delta_full_minus_half",
    }

    def rename(value):
        if isinstance(value, dict):
            return {names.get(k, k): rename(v) for k, v in value.items()}
        return value

    return rename(result)


def run_barahona(owner, contract_path, learning_curve_contract_path):
    private = Path(owner) / "revisions/r2"
    if read(contract_path).get("profiles_increment") != increment_protocol():
        raise ValueError("SEPARATELY_FROZEN_INCREMENT_CONTRACT_REQUIRED")
    if (
        read(learning_curve_contract_path).get("profiles_learning_curve")
        != learning_curve_protocol()
    ):
        raise ValueError("FROZEN_TRAINING_DATA_SIZE_CONTROL_REQUIRED")
    source = private / "barahona_ordinal_means.private.json"
    if read(contract_path).get("source_sha256", {}).get(source.name) != sha(source):
        raise ValueError("FROZEN_BARAHONA_SOURCE_HASH_MISMATCH")
    package = read(source)
    dev, conf = validate_barahona(package)
    plan = {
        "protocol": barahona_protocol(),
        "source_sha256": sha(source),
        "code_sha256": sha(__file__),
        "main_contract_sha256": sha(contract_path),
        "learning_curve_contract_sha256": sha(learning_curve_contract_path),
    }
    plan["hash"] = digest(plan)
    prefix = private / "profiles_increment_barahona"
    plan_path, result_path = Path(str(prefix) + "_plan.private.json"), Path(
        str(prefix) + "_summary.private.json"
    )
    lock = Path(str(prefix) + "_confirmation_lock.private.json")
    if plan_path.exists() and read(plan_path) != plan:
        raise ValueError("RETAINED_BARAHONA_PLAN_CHANGED")
    if result_path.exists():
        result = read(result_path)
        if result["plan_hash"] != plan["hash"]:
            raise ValueError("BARAHONA_RESULT_PLAN_CHANGED")
        for artifact in result["artifacts"]:
            if sha(private / artifact["relative_path"]) != artifact["sha256"]:
                raise ValueError("BARAHONA_RETAINED_ARTIFACT_CHANGED")
        return result
    if lock.exists():
        raise ValueError("BARAHONA_CONFIRMATION_ALREADY_STARTED_NO_REEVALUATION")
    save(plan_path, plan)
    start = time.monotonic()
    assignments = folds(dev, "group_id")
    rows, half_rows, audit, artifacts = [], [], [], []

    def persist(model, suffix, sample):
        path = Path(str(prefix) + suffix + ".model.json")
        save(path, model)
        loaded = read(path)
        if predict_barahona(sample, model) != predict_barahona(sample, loaded):
            raise AssertionError("BARAHONA_RELOAD_MISMATCH")
        artifacts.append({"relative_path": path.name, "sha256": sha(path)})
        return loaded

    for fold in range(3):
        train = [r for r in dev if assignments[r["group_id"]] != fold]
        held = [r for r in dev if assignments[r["group_id"]] == fold]
        model = persist(fit_barahona(train), "_fold" + str(fold), held[0])
        rows.extend(evaluate_barahona(held, model, "DEVELOPMENT_OUTER"))
        half = half_products(train)
        half_model = persist(fit_barahona(half), "_half_fold" + str(fold), held[0])
        half_rows.extend(
            evaluate_barahona(held, half_model, "DEVELOPMENT_OUTER_HALF_TRAIN")
        )
        audit.append(
            {
                "fold": fold,
                "train_products": model["training_groups"],
                "held_products": sorted(r["group_id"] for r in held),
                "half_train_products": half_model["training_groups"],
            }
        )
    final = persist(fit_barahona(dev), "_final", dev[0])
    final_half = persist(fit_barahona(half_products(dev)), "_half_final", dev[0])
    save(
        lock,
        {"plan_hash": plan["hash"], "status": "STARTED", "all_parameters_frozen": True},
    )
    confirmation_rows = evaluate_barahona(conf, final, "CONFIRMATION_ONCE")
    confirmation_half_rows = evaluate_barahona(
        conf, final_half, "CONFIRMATION_ONCE_HALF_TRAIN"
    )
    detail_path = Path(str(prefix) + "_evaluation.private.json")
    save(
        detail_path,
        {
            "target_order": BARAHONA_TARGETS,
            "development_rows": rows,
            "confirmation_rows": confirmation_rows,
            "development_half_rows": half_rows,
            "confirmation_half_rows": confirmation_half_rows,
            "fold_audit": audit,
        },
    )
    artifacts.append({"relative_path": detail_path.name, "sha256": sha(detail_path)})
    save(
        lock,
        {
            "plan_hash": plan["hash"],
            "status": "COMPLETE",
            "evaluation_sha256": sha(detail_path),
        },
    )
    artifacts.append({"relative_path": lock.name, "sha256": sha(lock)})
    result = {
        "version": BARAHONA_VERSION,
        "plan_hash": plan["hash"],
        "protocol": barahona_protocol(),
        "development": summarize_barahona(rows),
        "confirmation_once": summarize_barahona(confirmation_rows, True),
        "learning_curve_control": {
            "protocol": learning_curve_protocol(),
            "development": summarize_learning_curve(rows, half_rows),
            "confirmation_once": summarize_learning_curve(
                confirmation_rows, confirmation_half_rows, True
            ),
            "outer_training_counts": [
                {
                    "full": len(a["train_products"]),
                    "half": len(a["half_train_products"]),
                    "held": len(a["held_products"]),
                }
                for a in audit
            ],
        },
        "artifacts": artifacts,
        "new_source_products": 18,
        "observed_published_cells": 126,
        "individual_records_obtained": 0,
        "raw_lots_verified": None,
        "actual_bundle_fits": 8,
        "actual_target_fits": 56,
        "retained_models": 8,
        "elapsed_seconds": time.monotonic() - start,
        "other_view_observed_cell_cost_per_target": {
            target: len(barahona_inputs(view))
            for view, ts in BARAHONA_VIEWS.items()
            for target in ts
        },
        "source_provenance": {
            key: package["contract"][key]
            for key in [
                "source_url",
                "doi",
                "attribution",
                "license",
                "raw_sha256",
                "supplement_sha256",
                "scale",
                "scale_evidence",
            ]
        },
        "main_M2_scoring_changed": False,
        "professional_profile_alignment": "NOT_EVALUATED",
        "old_task_pooled_increment_effect": "NOT_ESTIMABLE_INCOMPATIBLE_SOURCE_NATIVE_TARGETS",
    }
    save(result_path, result)
    return result


def run(owner, contract_path, learning_curve_contract_path):
    if (
        read(contract_path).get("profiles_increment") != increment_protocol()
        or read(learning_curve_contract_path).get("profiles_learning_curve")
        != learning_curve_protocol()
    ):
        raise ValueError("BOTH_NEW_SOURCE_CONTRACTS_MUST_BE_FROZEN_BEFORE_ANY_FIT")
    tasks = {
        "liberica": run_liberica(owner, contract_path),
        "barahona": run_barahona(owner, contract_path, learning_curve_contract_path),
    }
    result = {
        "protocol": increment_protocol(),
        "tasks": tasks,
        "main_M2_scoring_changed": False,
        "cross_source_score_average": "NOT_DEFINED_DIFFERENT_TARGETS",
        "real_user_alignment": "NOT_EVALUATED",
        "real_user_time_efficiency": "NOT_EVALUATED",
    }
    path = Path(owner) / "revisions/r2/profiles_increment_summary.private.json"
    save(path, result)
    save(
        Path(owner) / "revisions/r2/profiles_increment_public_summary.private.json",
        public_summary(result),
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", type=Path)
    parser.add_argument("--contract-file", type=Path)
    parser.add_argument("--learning-curve-contract-file", type=Path)
    parser.add_argument("--print-protocol", action="store_true")
    parser.add_argument("--print-learning-curve-protocol", action="store_true")
    args = parser.parse_args()
    if args.print_protocol:
        print(json.dumps(increment_protocol(), indent=2))
    elif args.print_learning_curve_protocol:
        print(json.dumps(learning_curve_protocol(), indent=2))
    elif (
        args.owner_dir is None
        or args.contract_file is None
        or args.learning_curve_contract_file is None
    ):
        parser.error(
            "--owner-dir, --contract-file and --learning-curve-contract-file required"
        )
    else:
        result = run(
            args.owner_dir, args.contract_file, args.learning_curve_contract_file
        )
        print(
            json.dumps(
                {
                    "liberica": {
                        key: value["macro"]
                        for key, value in result["tasks"]["liberica"][
                            "development"
                        ].items()
                    },
                    "barahona": result["tasks"]["barahona"]["development"]["macro"],
                },
                indent=2,
            )
        )
