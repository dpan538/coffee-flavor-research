#!/usr/bin/env python3
"""Nested source-native sparse interactions, isolated from production scoring."""

from __future__ import annotations

import copy
import argparse
import itertools
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from threadpoolctl import threadpool_limits

import profile_alignment_r2 as prior
import profile_increment_r2 as increment
from external_construct_r3 import contract_contains, digest, save, sha

VERSION = "m2-r3-source-native-sparse-interactions.v1"
SEED = 20260906
FAMILIES = ("H0_MAIN", "H1_PAIRS", "H2_PAIRS_TRIPLES")
RIDGES = {"rocchetti": [0.5, 5.0], "barahona": [0.5, 5.0], "liberica": [0.05, 0.5]}
FIT_COUNTS = {"bundles": 0, "target_models": 0, "regression_solves": 0}


def views(kind):
    if kind == "rocchetti":
        return prior.views(kind)
    if kind == "barahona":
        return copy.deepcopy(increment.BARAHONA_VIEWS)
    if kind == "liberica":
        return copy.deepcopy(increment.VIEWS)
    raise ValueError("UNREGISTERED_SOURCE")


def protocol():
    return {
        "version": VERSION,
        "tasks": {
            "rocchetti": {"source_path": "revisions/r1/rocchetti_attribute_observations.private.json", "development_products": 38, "historical_products": 9, "view_masks": views("rocchetti"), "target": "PUBLISHED_PROFESSIONAL_SOURCE_NATIVE_0_TO_9_CODES", "metric": "PRODUCT_MACRO_NATIVE_CODE_MAE", "clip": [0, 9], "outer_folds": "UNCHANGED_R1_PRODUCT_FOLDS", "prior": "RELOAD_R2_SELECTED_OUTER_AND_FINAL_MODELS"},
            "barahona": {"source_path": "revisions/r2/barahona_ordinal_means.private.json", "source_sha256": "5173db2d83620892eb4cfd1eba0f0a94e8f369a671fa3bc4c66d84414f6256e3", "development_products": 14, "historical_products": 4, "view_masks": views("barahona"), "target": "PUBLISHED_CONSUMER_1_TO_10_ORDINAL_CATEGORY_MEANS_NOT_PROFESSIONAL", "metric": "PRODUCT_MACRO_NATIVE_CODE_MAE", "clip": [1, 10], "outer_folds": "UNCHANGED_R2_PRODUCT_FOLDS", "prior": "RELOAD_R2_FIXED_RIDGE_0.5_MODELS"},
            "liberica": {"source_path": "revisions/r2/liberica_rata_records.private.json", "source_sha256": "708fe96a5ac8cefdd758bd391ad55cc325736721afdcf4f346125d77edf93b6d", "development_intersection": {"participants": 23, "conditions": 8, "records": 184}, "view_masks": views("liberica"), "target": "TEN_NOMINAL_SIX_CATEGORY_SOURCE_CODES;ZERO_NOT_ABSENCE_OR_ORDINAL_INTENSITY", "metric": "HELD_AXIS_MACRO_BRIER_SUM_SIX_CLASS_SQUARED_ERRORS_DIVIDED_BY_SIX", "outer_folds": "UNCHANGED_R2_SEPARATE_PARTICIPANT_AND_CONDITION_THREE_FOLDS", "prior": "RELOAD_R2_FIXED_RIDGE_0.05_MODELS", "cross_coffee": "NOT_ESTIMABLE_SINGLE_STUDY_COFFEE_LEAF_MATERIALS", "opposite_axis": "SHARED_WITH_TRAIN_CONDITIONAL_SCOPE_ONLY"},
        },
        "families": list(FAMILIES),
        "ridge_grids": copy.deepcopy(RIDGES),
        "input_and_mask": "ONLY_ACTUALLY_OBSERVED_OTHER_ENTIRE_VIEWS;REJECT_MISSING_OR_FALSE_MASKS;NO_IDENTITIES_SOURCE_CONTEXT_LIKING_QUALITY_OR_TARGET_BLOCK_IN_FEATURES",
        "numeric_encoding": "TRAIN_ONLY_POPULATION_MEAN_SD_MAIN_EFFECTS;PAIR_AND_TRIPLE_PRODUCTS_OF_STANDARDIZED_DIFFERENT_SOURCE_FIELDS;STANDARDIZE_EACH_INTERACTION_ON_TRAIN;TRAIN_ONLY_TARGET_STANDARDIZATION",
        "nominal_encoding": "SIX_RAW_ONE_HOT_MAIN_COLUMNS_PER_SOURCE_FIELD;PAIR_TRIPLE_INDICATOR_CONJUNCTIONS_OF_DIFFERENT_FIELDS_AND_CATEGORY_IDS;NO_NUMERIC_CODE_MULTIPLICATION;NO_IMPUTATION",
        "interaction_selection": {
            "pairs_max_per_target": 4,
            "triples_max_per_target": 2,
            "pair_screen": "RANK_TRAIN_ONLY_ABSOLUTE_RESIDUAL_ASSOCIATION_AFTER_MAIN_MODEL_FIT_AT_CANDIDATE_RIDGE;NUMERIC_PEARSON_ABS_OR_NOMINAL_L2_SIX_CLASS_RESIDUAL_COVARIANCE_WITH_STD_TERM",
            "triple_screen": "AFTER_REFITTING_SELECTED_PAIRS_RANK_SAME_RESIDUAL_ASSOCIATION;WEAK_HEREDITY_REQUIRES_AT_LEAST_ONE_SELECTED_EXACT_PAIR_SUBTERM;ALL_MAIN_EFFECTS_RETAINED",
            "support": "AT_LEAST_THREE_INDEPENDENT_TRAIN_AXIS_GROUPS_WITH_NONZERO_TERM;NOMINAL_ALSO_AT_LEAST_THREE_GROUPS_WITH_ZERO_TERM;NUMERIC_AT_LEAST_THREE_DISTINCT_TERM_VALUES_AND_NONZERO_VARIANCE;REPORT_GROUPS_TOTAL_NONZERO_AND_NUMERIC_JOINT_ABOVE_MEDIAN",
            "ties": "LEXICOGRAPHIC_SOURCE_FIELD_CATEGORY_SPECIFICATION;NO_HELD_DATA_IN_SELECTION",
        },
        "nested_selection": "THREE_INNER_GROUP_FOLDS_WITH_SHA256_VERSION_SEED_AXIS_ID_SORT_ROUND_ROBIN;ONE_SHARED_RIDGE_PER_SOURCE_AXIS_FAMILY_BY_ALL_TARGET_GROUP_MACRO_LOSS;REPEAT_EVERY_SCALER_SCREEN_AND_FIT_WITHIN_INNER_TRAIN;TIE_1E-12_STRONGEST_RIDGE",
        "multinomial_optimizer": "L_BFGS_B_SOFTMAX_SIX_CLASSES_MEAN_NLL_PLUS_RIDGE_HALF_COEFFICIENT_SQUARE_SUM;UNPENALIZED_INTERCEPT;MAXITER1000_FTOL1E-11_GTOL1E-7;REPORT_CONVERGENCE",
        "primary_contrasts": ["H1_PAIRS_MINUS_H0_MAIN", "H2_PAIRS_TRIPLES_MINUS_H1_PAIRS"],
        "secondary_contrasts": ["EACH_H_FAMILY_MINUS_RETAINED_R2_MODEL"],
        "same_budget": "IDENTICAL_HELD_CASES_TARGET_DIMENSIONS_MASKS_AND_OBSERVED_OTHER_VIEW_CELLS;NO_NEW_QUESTION_OR_REAL_TIME_CLAIM",
        "uncertainty": "2000_FIXED_OOF_PREDICTION_PAIRED_HELD_AXIS_GROUP_BOOTSTRAPS;NO_REFIT;NO_NEW_SOURCE_OR_INDIVIDUAL_UNCERTAINTY;PER_TARGET_EXPLORATORY_NO_MULTIPLICITY_CORRECTION",
        "historical": "ALL_R2_CONFIRMATION_PREVIOUSLY_VIEWED;HISTORICAL_REGRESSION_ONLY_AFTER_ALL_FINAL_MODELS_FROZEN;NO_MODEL_FAMILY_SELECTION_OR_FRESH_CONFIRMATION_CLAIM;FEWER_THAN_FIVE_GROUPS_DESCRIPTIVE_ONLY",
        "cross_source_score_average": "FORBIDDEN",
        "CATA": "NOT_IN_THIS_BOUNDED_FIT;EXISTING_COMPLETE_BINARY_CATA_ZERO_SEMANTICS_REMAIN_SEPARATE_FROM_LIBERICA",
        "deployment": "RETAIN_ALL_FAMILIES_AND_UNSELECTED_INNER_SCORES_PRIVATE;NO_MAIN_M2_SCORING_CHANGE_OR_CALIBRATED_PSYCHOLOGICAL_DISTANCE_CLAIM",
        "new_source_increment": "DEFERRED_UNTIL_ACTUAL_SOURCE_ADMISSION_AND_SEPARATE_FIXED_MODEL_CONTRACT;NO_INCOMPATIBLE_POOLING",
        "seed": SEED,
    }


def targets(kind):
    return [c for block in views(kind).values() for c in block]


def observed(row, target, kind):
    if kind == "liberica":
        value = increment.observed(row, target)
    elif kind == "barahona":
        value = increment.barahona_value(row, target)
    else:
        value = prior.value(row.get("attribute_measurements", {}).get(target), target, kind)
        if row.get("attribute_masks", {}).get(target) is not True:
            value = None
    return value


def input_fields(kind, view):
    return [c for c in targets(kind) if c not in views(kind)[view]]


def raw_inputs(row, kind, view):
    values = [observed(row, c, kind) for c in input_fields(kind, view)]
    if any(v is None for v in values):
        raise ValueError("COMPLETE_OBSERVED_OTHER_VIEW_REQUIRED")
    return np.asarray(values, dtype=int if kind == "liberica" else float)


def validate_train(rows, kind, axis):
    if not rows or len({r["record_id"] for r in rows}) != len(rows):
        raise ValueError("NONEMPTY_UNIQUE_TRAINING_RECORDS_REQUIRED")
    for row in rows:
        if kind == "liberica":
            if row["participant_split"] != "DEVELOPMENT" or row["condition_split"] != "DEVELOPMENT":
                raise ValueError("BOTH_LIBERICA_AXES_MUST_BE_DEVELOPMENT")
        elif row.get("split") != "DEVELOPMENT":
            raise ValueError("DEVELOPMENT_PRODUCTS_ONLY")
        if any(observed(row, c, kind) is None for c in targets(kind)):
            raise ValueError("EXACT_COMPLETE_SOURCE_TARGET_AND_INPUT_MASKS_REQUIRED")
    if kind != "liberica" and len({r[axis] for r in rows}) != len(rows):
        raise ValueError("ONE_OBSERVATION_PER_SOURCE_PRODUCT_REQUIRED")


def train_base(raw, kind):
    if kind == "liberica":
        return np.eye(6)[raw].reshape(len(raw), -1), {"encoding": "nominal_one_hot", "categories": list(range(6))}
    mean, scale = raw.mean(0), raw.std(0)
    scale[scale < 1e-8] = 1
    return (raw - mean) / scale, {"encoding": "numeric_standardized", "feature_mean": mean.tolist(), "feature_scale": scale.tolist()}


def transform_base(raw, kind, specification):
    if kind == "liberica":
        if specification != {"encoding": "nominal_one_hot", "categories": list(range(6))}:
            raise ValueError("NOMINAL_ENCODING_CONTRACT")
        return np.eye(6)[raw].reshape(len(raw), -1)
    return (raw - specification["feature_mean"]) / specification["feature_scale"]


def solve(X, y, kind, ridge):
    FIT_COUNTS["regression_solves"] += 1
    if kind != "liberica":
        ym, ys = float(y.mean()), float(y.std())
        ys = ys if ys > 1e-8 else 1.0
        beta = np.linalg.solve(X.T @ X / len(X) + ridge * np.eye(X.shape[1]), X.T @ ((y - ym) / ys) / len(y))
        return {"coefficients": beta.tolist(), "target_mean": ym, "target_scale": ys, "converged": True}
    prevalence = np.bincount(y, minlength=6) / len(y)
    initial = np.zeros((6, X.shape[1] + 1))
    initial[:, 0] = np.log(np.maximum(prevalence, 1e-6))
    initial[:, 0] -= initial[:, 0].mean()
    augmented, labels = np.column_stack((np.ones(len(X)), X)), np.eye(6)[y]

    def objective(flat):
        beta = flat.reshape(initial.shape)
        logits = augmented @ beta.T
        loss = np.mean(logsumexp(logits, axis=1) - logits[np.arange(len(y)), y]) + ridge * np.sum(beta[:, 1:] ** 2) / 2
        gradient = (softmax(logits, axis=1) - labels).T @ augmented / len(y)
        gradient[:, 1:] += ridge * beta[:, 1:]
        return float(loss), gradient.ravel()

    fitted = minimize(objective, initial.ravel(), jac=True, method="L-BFGS-B", options={"maxiter": 1000, "ftol": 1e-11, "gtol": 1e-7})
    if not fitted.success:
        raise RuntimeError("MULTINOMIAL_OPTIMIZER_FAILURE:" + str(fitted.message))
    beta = fitted.x.reshape(initial.shape)
    return {"coefficients": beta[:, 1:].tolist(), "intercepts": beta[:, 0].tolist(), "converged": bool(fitted.success),
            "iterations": int(fitted.nit), "objective": float(fitted.fun)}


def fitted_prediction(X, head, kind, clip=True):
    if kind == "liberica":
        return softmax(X @ np.asarray(head["coefficients"]).T + head["intercepts"], axis=1)
    predictions = head["target_mean"] + head["target_scale"] * (X @ head["coefficients"])
    return np.clip(predictions, *(protocol()["tasks"][kind]["clip"])) if clip else predictions


def term_values(raw, standardized, term, names, kind):
    index = {name: i for i, name in enumerate(names)}
    if kind == "liberica":
        return np.all(np.column_stack([raw[:, index[name]] == code for name, code in term]), axis=1).astype(float)
    return np.prod(standardized[:, [index[name] for name in term]], axis=1)


def candidate_terms(raw, names, kind, order, selected_pairs):
    selected = [set(map(tuple, p["term"])) if kind == "liberica" else set(p["term"]) for p in selected_pairs]
    for columns in itertools.combinations(range(len(names)), order):
        if kind == "liberica":
            for codes in sorted(set(map(tuple, raw[:, columns].tolist()))):
                term = [[names[c], int(code)] for c, code in zip(columns, codes)]
                values = set(map(tuple, term))
                if order == 2 or any(pair <= values for pair in selected):
                    yield term
        else:
            term = [names[c] for c in columns]
            if order == 2 or any(pair <= set(term) for pair in selected):
                yield term


def select_terms(raw, standardized, names, groups, residual, kind, order, selected_pairs):
    candidates = []
    groups = np.asarray(groups)
    for term in candidate_terms(raw, names, kind, order, selected_pairs):
        column = term_values(raw, standardized, term, names, kind)
        nonzero = np.abs(column) > 1e-12
        support = len(set(groups[nonzero]))
        zero_support = len(set(groups[~nonzero]))
        distinct, std = len(np.unique(column)), float(column.std())
        if support < 3 or std < 1e-8 or (kind == "liberica" and zero_support < 3) or (kind != "liberica" and distinct < 3):
            continue
        normalized = (column - column.mean()) / std
        if kind == "liberica":
            score = float(np.linalg.norm(normalized @ residual / len(raw)))
        else:
            score = float(abs(normalized @ residual / len(raw)) / max(float(residual.std()), 1e-12))
        if score <= 1e-12:
            continue
        if kind != "liberica":
            ix = [names.index(name) for name in term]
            jointly_high = np.all(raw[:, ix] > np.median(raw[:, ix], axis=0), axis=1)
            joint_high_count = len(set(groups[jointly_high]))
        else:
            joint_high_count = None
        candidates.append({"term": term, "screen_score_train_only": score, "train_group_count": len(set(groups)),
                           "nonzero_support_groups": support, "zero_support_groups": zero_support,
                           "distinct_values": distinct, "joint_above_train_median_groups": joint_high_count,
                           "term_mean": float(column.mean()) if kind != "liberica" else 0.0,
                           "term_scale": std if kind != "liberica" else 1.0})
    # Rounding only defines stable ties; no held values participate.
    candidates.sort(key=lambda c: (-round(c["screen_score_train_only"], 14), json.dumps(c["term"], separators=(",", ":"))))
    return candidates[: 4 if order == 2 else 2], len(candidates)


def add_terms(base, raw, names, kind, terms):
    columns = [(term_values(raw, base, term["term"], names, kind) - term["term_mean"]) / term["term_scale"] for term in terms]
    return np.column_stack([base, *columns]) if columns else base


def fit(rows, kind, axis, family, ridge):
    if family not in FAMILIES or ridge not in RIDGES[kind]:
        raise ValueError("UNREGISTERED_MODEL_FAMILY_OR_RIDGE")
    validate_train(rows, kind, axis)
    FIT_COUNTS["bundles"] += 1
    heads = {}
    with threadpool_limits(limits=1):
        for view, block in views(kind).items():
            names = input_fields(kind, view)
            raw = np.array([raw_inputs(row, kind, view) for row in rows])
            base, specification = train_base(raw, kind)
            for target in block:
                FIT_COUNTS["target_models"] += 1
                y = np.asarray([observed(row, target, kind) for row in rows], dtype=int if kind == "liberica" else float)
                pairs, triples, candidates_pair, candidates_triple = [], [], 0, 0
                head = solve(base, y, kind, ridge)
                if family != "H0_MAIN":
                    residual = (np.eye(6)[y] if kind == "liberica" else y) - fitted_prediction(base, head, kind, clip=False)
                    pairs, candidates_pair = select_terms(raw, base, names, [r[axis] for r in rows], residual, kind, 2, [])
                    design = add_terms(base, raw, names, kind, pairs)
                    head = solve(design, y, kind, ridge)
                    if family == "H2_PAIRS_TRIPLES":
                        residual = (np.eye(6)[y] if kind == "liberica" else y) - fitted_prediction(design, head, kind, clip=False)
                        triples, candidates_triple = select_terms(raw, base, names, [r[axis] for r in rows], residual, kind, 3, pairs)
                        head = solve(add_terms(base, raw, names, kind, pairs + triples), y, kind, ridge)
                heads[target] = {**head, "view": view, "input_fields": names, "base_encoding": specification,
                                 "pairs": pairs, "triples": triples, "eligible_pair_candidates": candidates_pair,
                                 "eligible_triple_candidates": candidates_triple, "observed_target_cells": len(y)}
    return {"version": VERSION, "kind": kind, "axis": axis, "family": family, "ridge": ridge, "views": views(kind), "heads": heads,
            "training_ids": {key: sorted({r[key] for r in rows}) for key in ("record_id", "group_id", "participant_id", "condition_id") if key in rows[0]},
            "training_fingerprint": digest(rows), "protocol_sha256": digest(protocol()), "main_M2_input": False}


def predict(row, model, only_target=None):
    kind = model["kind"]
    if model.get("version") != VERSION or model.get("views") != views(kind) or set(model["heads"]) != set(targets(kind)):
        raise ValueError("SOURCE_NATIVE_MODEL_CONTRACT_MISMATCH")
    predictions = {}
    for target, head in model["heads"].items():
        if only_target is not None and target != only_target:
            continue
        if head["input_fields"] != input_fields(kind, head["view"]) or target not in views(kind)[head["view"]]:
            raise ValueError("TARGET_VIEW_LEAKAGE")
        raw = raw_inputs(row, kind, head["view"])[None, :]
        base = transform_base(raw, kind, head["base_encoding"])
        names = head["input_fields"]
        for term in head["pairs"] + head["triples"]:
            fields = [x[0] for x in term["term"]] if kind == "liberica" else term["term"]
            if len(set(fields)) != len(fields) or any(c not in names for c in fields):
                raise ValueError("INVALID_INTERACTION_FIELDS")
        design = add_terms(base, raw, names, kind, head["pairs"] + head["triples"])
        prediction = fitted_prediction(design, head, kind)[0]
        predictions[target] = prediction.tolist() if kind == "liberica" else float(prediction)
    return predictions


def losses(row, predictions, kind):
    result = []
    for target in targets(kind):
        actual = observed(row, target, kind)
        if actual is None:
            raise ValueError("HELD_TARGET_MASK_INCOMPLETE_KEEP_DENOMINATOR")
        result.append(float(np.mean((np.eye(6)[actual] - predictions[target]) ** 2)) if kind == "liberica"
                      else abs(actual - predictions[target]))
    return result


def held_rows(rows, model, axis):
    if set(model["training_ids"]["record_id"]) & {r["record_id"] for r in rows}:
        raise ValueError("HELD_RECORD_LEAKAGE")
    if axis in model["training_ids"] and set(model["training_ids"][axis]) & {r[axis] for r in rows}:
        raise ValueError("HELD_IDENTITY_LEAKAGE")
    output = []
    for row in rows:
        prediction = predict(row, model)
        unit = row[axis] if axis != "both" else row["participant_id"] + "|" + row["condition_id"]
        output.append({"record_id": row["record_id"], "unit": unit, "losses": losses(row, prediction, model["kind"]), "predictions": prediction})
    return output


def inner_folds(rows, axis):
    groups = sorted({r[axis] for r in rows}, key=lambda x: digest([VERSION, SEED, axis, x]))
    if len(groups) < 3:
        raise ValueError("AT_LEAST_THREE_TRAINING_GROUPS_REQUIRED")
    return {group: i % 3 for i, group in enumerate(groups)}


def macro_loss(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["unit"]].append(np.mean(row["losses"]))
    return float(np.mean([np.mean(values) for values in grouped.values()]))


def select_ridge(rows, kind, axis, family):
    assignment, scores, audit = inner_folds(rows, axis), {}, []
    for ridge in RIDGES[kind]:
        evaluations = []
        for fold in range(3):
            train, held = [r for r in rows if assignment[r[axis]] != fold], [r for r in rows if assignment[r[axis]] == fold]
            model = fit(train, kind, axis, family, ridge)
            evaluations.extend(held_rows(held, model, axis))
            audit.append({"ridge": ridge, "fold": fold, "train_units": sorted({r[axis] for r in train}), "held_units": sorted({r[axis] for r in held}),
                          "training_fingerprint": model["training_fingerprint"], "target_selection": {c: {k: h[k] for k in ("pairs", "triples", "base_encoding", "eligible_pair_candidates", "eligible_triple_candidates")} for c, h in model["heads"].items()}})
        scores[str(ridge)] = macro_loss(evaluations)
    best = min(scores.values())
    selected = max(ridge for ridge in RIDGES[kind] if scores[str(ridge)] <= best + 1e-12)
    return selected, {"selected_ridge": selected, "all_inner_scores": scores, "fold_audit": audit}


def baseline_path(owner, kind, axis, fold=None):
    if kind == "rocchetti":
        name = f"profiles_rocchetti_fold{fold}_selected" if fold is not None else "profiles_rocchetti_final_selected"
    elif kind == "barahona":
        name = f"profiles_increment_barahona_fold{fold}" if fold is not None else "profiles_increment_barahona_final"
    else:
        name = f"profiles_increment_{axis}_fold{fold}" if fold is not None else "profiles_increment_final"
    return Path(owner) / "revisions/r2" / (name + ".model.json")


def load_baseline(owner, kind, axis, train, fold=None):
    path = baseline_path(owner, kind, axis, fold)
    model = json.loads(path.read_text())
    if kind == "rocchetti":
        old_ids, new_ids = model["training_record_ids"], [r["record_id"] for r in train]
    elif kind == "barahona":
        old_ids, new_ids = model["training_groups"], [r["group_id"] for r in train]
    else:
        old_ids, new_ids = model["training_ids"]["record_id"], [r["record_id"] for r in train]
    if set(old_ids) != set(new_ids) or model["training_fingerprint"] != digest(train):
        raise ValueError("EXACT_R2_TRAINING_RECORDS_AND_VALUES_MUST_MATCH:" + path.name)
    return model


def baseline_predict(row, model, kind):
    if kind == "rocchetti":
        return prior.predict(row["attribute_measurements"], model)
    if kind == "barahona":
        return increment.predict_barahona(row, model)
    return increment.predict(row, model)


def paired_evaluate(rows, models, baseline, kind, axis, stage, fold=None):
    family_rows = {name: {r["record_id"]: r for r in held_rows(rows, model, axis)} for name, model in models.items()}
    output = []
    for row in rows:
        old_prediction = baseline_predict(row, baseline, kind)
        unit = row[axis] if axis != "both" else row["participant_id"] + "|" + row["condition_id"]
        item = {"record_id": row["record_id"], "unit": unit, "stage": stage, "fold": fold,
                "truth": [observed(row, c, kind) for c in targets(kind)],
                "losses": {"R2_RETAINED": losses(row, old_prediction, kind)}, "predictions": {"R2_RETAINED": old_prediction}}
        for name, by_id in family_rows.items():
            item["losses"][name] = by_id[row["record_id"]]["losses"]
            item["predictions"][name] = by_id[row["record_id"]]["predictions"]
        output.append(item)
    if len({r["record_id"] for r in output}) != len(rows):
        raise ValueError("DUPLICATE_HELD_DENOMINATOR")
    return output


def summarize(rows, kind, historical=False):
    units = sorted({r["unit"] for r in rows})
    columns = targets(kind)
    names = ["R2_RETAINED", *FAMILIES]
    grouped = {name: np.array([np.mean([r["losses"][name] for r in rows if r["unit"] == unit], axis=0) for unit in units]) for name in names}
    rng = np.random.default_rng(SEED)
    resamples = rng.integers(len(units), size=(2000, len(units))) if len(units) >= 5 else None

    def block(indices):
        scores = {name: array[:, indices].mean(axis=1) for name, array in grouped.items()}
        comparisons = {}
        for after, before in [("H1_PAIRS", "H0_MAIN"), ("H2_PAIRS_TRIPLES", "H1_PAIRS"), *[(name, "R2_RETAINED") for name in FAMILIES]]:
            delta = scores[after] - scores[before]
            interval = np.quantile(delta[resamples].mean(axis=1), [0.025, 0.975]).tolist() if resamples is not None else None
            status = "INCONCLUSIVE" if interval is None or interval[0] <= 0 <= interval[1] else "SUPPORTED_IN_DECLARED_SCOPE" if interval[1] < 0 else "DEGRADATION_IN_DECLARED_SCOPE"
            if historical:
                status = "HISTORICAL_REGRESSION_DESCRIPTIVE"
            comparisons[after + "_MINUS_" + before] = {"delta": float(delta.mean()), "paired_group_95_interval": interval,
                                                    "range_per_unit": [float(delta.min()), float(delta.max())], "lower_is_better": True,
                                                    "status": status, "improved_units": int(np.sum(delta < -1e-12)),
                                                    "worsened_units": int(np.sum(delta > 1e-12)), "tied_units": int(np.sum(np.abs(delta) <= 1e-12))}
        return {"scores": {name: float(x.mean()) for name, x in scores.items()}, "comparisons": comparisons}

    return {"held_units": len(units), "held_records": len(rows), "target_dimensions": len(columns),
            "evaluated_cells_per_model": len(rows) * len(columns), "coverage": 1.0, "macro": block(list(range(len(columns)))),
            "per_target": {target: block([i]) for i, target in enumerate(columns)},
            "scope": protocol()["tasks"][kind]["target"], "metric": protocol()["tasks"][kind]["metric"],
            "historical": historical, "uncertainty_scope": protocol()["uncertainty"]}


def support_summary(models):
    heads = [h for m in models for h in m["heads"].values()]
    terms = {key: [t for h in heads for t in h[key]] for key in ("pairs", "triples")}
    return {"target_models": len(heads), "heads_with_pairs": sum(bool(h["pairs"]) for h in heads),
            "heads_with_triples": sum(bool(h["triples"]) for h in heads),
            "all_optimizers_converged": all(h["converged"] for h in heads),
            "terms": {key: {"count": len(values), "minimum_nonzero_support_groups": min((t["nonzero_support_groups"] for t in values), default=None),
                            "minimum_zero_support_groups": min((t["zero_support_groups"] for t in values), default=None),
                            "maximum_count_per_target": max((len(h[key]) for h in heads), default=0)} for key, values in terms.items()}}


def load_sources(owner):
    owner = Path(owner)
    paths = {kind: owner / task["source_path"] for kind, task in protocol()["tasks"].items()}
    packages = {kind: json.loads(path.read_text()) for kind, path in paths.items()}
    for kind in ("barahona", "liberica"):
        if sha(paths[kind]) != protocol()["tasks"][kind]["source_sha256"]:
            raise ValueError("FROZEN_SOURCE_HASH_MISMATCH:" + kind)
    prior.professional.validate_records(packages["rocchetti"], json.loads((owner / "revisions/r1/rocchetti_split_preregistered.private.json").read_text()))
    bar_dev, bar_history = increment.validate_barahona(packages["barahona"])
    lib = increment.validate(packages["liberica"])
    roc_dev = [r for r in packages["rocchetti"] if r["split"] == "DEVELOPMENT"]
    roc_history = [r for r in packages["rocchetti"] if r["split"] == "CONFIRMATION"]
    if (len(roc_dev), len(roc_history)) != (38, 9):
        raise ValueError("PRESERVED_ROCCHETTI_SPLIT_REQUIRED")
    tasks = {
        "rocchetti_product": {"kind": "rocchetti", "axis": "group_id", "dev": roc_dev, "history": {"historical_products": (roc_history, "group_id")}, "folds": prior.professional.fold_assignments(roc_dev)},
        "barahona_product": {"kind": "barahona", "axis": "group_id", "dev": bar_dev, "history": {"historical_products": (bar_history, "group_id")}, "folds": increment.folds(bar_dev, "group_id")},
    }
    for axis in ("participant_id", "condition_id"):
        cohort = "held_participant" if axis == "participant_id" else "held_condition"
        tasks["liberica_" + axis] = {"kind": "liberica", "axis": axis, "dev": lib["development"],
                                     "history": {"historical_" + cohort: (lib[cohort], axis), "historical_both_axes": (lib["both_axes_held"], "both")},
                                     "folds": increment.folds(lib["development"], axis)}
    return paths, tasks


def run(owner, contract_path):
    owner, contract_path = Path(owner), Path(contract_path)
    if not contract_contains(json.loads(contract_path.read_text()), protocol()):
        raise ValueError("EXACT_MULTI_VIEW_PROTOCOL_NOT_IN_FROZEN_CONTRACT")
    sources, tasks = load_sources(owner)
    baseline_paths = sorted({baseline_path(owner, task["kind"], task["axis"], fold) for task in tasks.values() for fold in [0, 1, 2, None]})
    fingerprint = {"protocol_sha256": digest(protocol()), "contract_sha256": sha(contract_path), "code_sha256": sha(__file__),
                   "source_sha256": {k: sha(p) for k, p in sources.items()}, "baseline_sha256": {p.name: sha(p) for p in baseline_paths},
                   "dependency_sha256": {Path(m.__file__).name: sha(m.__file__) for m in (prior, increment, prior.professional, prior.response)}}
    directory = owner / "revisions/r3"
    receipt_path = directory / "multi_view_receipt.private.json"
    summary_path = directory / "multi_view_public_summary.private.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt["fingerprint"] != fingerprint or receipt["status"] != "COMPLETE":
            raise ValueError("PRESERVE_PRIOR_MULTI_VIEW_RUN_OR_INCOMPLETE_RECEIPT")
        for artifact in receipt["artifacts"]:
            if sha(owner / artifact["owner_relative_path"]) != artifact["sha256"]:
                raise ValueError("RETAINED_MULTI_VIEW_ARTIFACT_HASH_MISMATCH")
        return json.loads(summary_path.read_text())
    # Validate every exact prior training scope before any new fit.
    for task in tasks.values():
        for fold in range(3):
            train = [r for r in task["dev"] if task["folds"][r[task["axis"]]] != fold]
            load_baseline(owner, task["kind"], task["axis"], train, fold)
        load_baseline(owner, task["kind"], task["axis"], task["dev"])
    save(receipt_path, {"status": "RUNNING", "fingerprint": fingerprint, "historical_not_yet_evaluated": True})
    for key in FIT_COUNTS:
        FIT_COUNTS[key] = 0
    started = time.monotonic()
    artifacts, summaries, final_models, details = [], {}, {}, {}

    def persist(name, value):
        path = directory / name
        save(path, value)
        artifacts.append({"owner_relative_path": str(path.relative_to(owner)), "sha256": sha(path)})
        return json.loads(path.read_text())

    for task_name, task in tasks.items():
        kind, axis, dev, assignment = task["kind"], task["axis"], task["dev"], task["folds"]
        outer_rows, audits, retained_models, outer_ridges = [], [], [], {name: [] for name in FAMILIES}
        for fold in range(3):
            train = [r for r in dev if assignment[r[axis]] != fold]
            held = [r for r in dev if assignment[r[axis]] == fold]
            baseline = load_baseline(owner, kind, axis, train, fold)
            models = {}
            for family in FAMILIES:
                ridge, audit = select_ridge(train, kind, axis, family)
                model = fit(train, kind, axis, family, ridge)
                loaded = persist(f"multi_view_{task_name}_{family}_fold{fold}.model.json", model)
                if predict(held[0], loaded) != predict(held[0], model):
                    raise AssertionError("RELOADED_MULTI_VIEW_PREDICTION_MISMATCH")
                models[family] = loaded
                retained_models.append(loaded)
                outer_ridges[family].append(ridge)
                audits.append({"outer_fold": fold, "family": family, "outer_train_units": sorted({r[axis] for r in train}),
                               "outer_held_units": sorted({r[axis] for r in held}), **audit})
            outer_rows.extend(paired_evaluate(held, models, baseline, kind, axis, "DEVELOPMENT_OUTER", fold))
            print(json.dumps({"task": task_name, "outer_fold": fold, "held_groups": len({r[axis] for r in held}), "selected_ridges": {k: v["ridge"] for k, v in models.items()}}), flush=True)
        final_models[task_name] = {}
        final_audits = {}
        for family in FAMILIES:
            ridge, audit = select_ridge(dev, kind, axis, family)
            model = persist(f"multi_view_{task_name}_{family}_final.model.json", fit(dev, kind, axis, family, ridge))
            final_models[task_name][family] = model
            final_audits[family] = audit
        details[task_name] = {"target_order": targets(kind), "outer_rows": outer_rows, "outer_audits": audits, "final_audits": final_audits}
        summaries[task_name] = {"kind": kind, "holdout_axis": axis, "development": summarize(outer_rows, kind), "selected_outer_ridges": outer_ridges,
                                "final_ridges": {k: m["ridge"] for k, m in final_models[task_name].items()}, "outer_support": support_summary(retained_models),
                                "final_support": support_summary(list(final_models[task_name].values())),
                                "source_count": 1, "new_source_samples_added": 0, "main_M2_scoring_changed": False}
    # Every model for every task is frozen before viewing any historical targets.
    historical_receipt = persist("multi_view_historical_freeze.private.json", {"status": "ALL_MODELS_FROZEN_BEFORE_HISTORICAL_EVALUATION", "fingerprint": fingerprint,
                                                                         "model_artifacts": list(artifacts), "confirmation_grade": "HISTORICAL_ONLY"})
    for task_name, task in tasks.items():
        kind, axis, dev = task["kind"], task["axis"], task["dev"]
        baseline = load_baseline(owner, kind, axis, dev)
        summaries[task_name]["historical_regression"] = {}
        details[task_name]["historical_rows"] = {}
        for cohort, (rows, held_axis) in task["history"].items():
            evaluated = paired_evaluate(rows, final_models[task_name], baseline, kind, held_axis, "HISTORICAL_REGRESSION_ONLY")
            details[task_name]["historical_rows"][cohort] = evaluated
            summaries[task_name]["historical_regression"][cohort] = summarize(evaluated, kind, historical=True)
        filename = f"multi_view_{task_name}_evaluation.private.json"
        persist(filename, {"fingerprint": fingerprint, **details[task_name]})
        summaries[task_name]["private_details_owner_relative"] = "revisions/r3/" + filename
    summary = {"version": VERSION, "protocol_sha256": digest(protocol()), "tasks": summaries, "fit_counts": dict(FIT_COUNTS),
               "elapsed_seconds": time.monotonic() - started, "same_budget": protocol()["same_budget"],
               "main_M2_scoring_changed": False, "cross_source_average": "NOT_COMPUTED_INCOMPATIBLE_TARGETS", "historical_grade": "PREVIOUSLY_VIEWED_R2_CONFIRMATION_ONLY",
               "model_family_selection": "NONE_ALL_THREE_RETAINED", "source_manifest_owner_relative": "revisions/r3/multi_view_receipt.private.json"}
    persist(summary_path.name, summary)
    save(receipt_path, {"status": "COMPLETE", "fingerprint": fingerprint, "artifacts": artifacts, "fit_counts": dict(FIT_COUNTS),
                        "historical_evaluation_passes": 1, "cached_rerun": "VERIFY_ALL_ARTIFACTS_RETURN_SAVED_NO_FITS_OR_EVALUATIONS"})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    parser.add_argument("--contract", required=True)
    arguments = parser.parse_args()
    outcome = run(arguments.owner_dir, arguments.contract)
    print(json.dumps({"version": outcome["version"], "fit_counts": outcome["fit_counts"], "elapsed_seconds": outcome["elapsed_seconds"],
                      "tasks": {name: data["development"]["macro"] for name, data in outcome["tasks"].items()}}, indent=2, sort_keys=True))
