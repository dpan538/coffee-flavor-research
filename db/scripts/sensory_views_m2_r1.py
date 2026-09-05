#!/usr/bin/env python3
"""Source-specific M2 R1 auxiliary attribute heads; no default ranking changes.

Ordinal ranks remain ordered source categories, and complete CATA ballots retain
observed zeros. Descriptor associations, basic tastes and mouthfeel are separate
views. No source-native roast term establishes the mandatory production C1.
"""

from __future__ import annotations
import argparse, copy, hashlib, json, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from threadpoolctl import threadpool_limits
import flavor_m2_r1 as runtime
import train_m2_r1 as training

VERSION = "m2-r1-source-sensory-views.v1"
ORDINAL_TARGETS = ["native.acidity_intensity", "taste.sweetness", "taste.bitterness"]
STAGES = {"INITIAL_EXTRACTION": 2, "FIRST_CORRECTION": 3, "ORDINARY_COMPLETION": -1}
CATA_VIEWS = {
    "descriptor_associations": [
        "attribute.fruity",
        "attribute.roasted",
        "broad.nutty",
        "compound.tea_floral",
        "native.burnt",
        "native.rubber",
        "sensory.caramel",
        "sensory.dark_chocolate",
    ],
    "basic_tastes": ["taste.sweetness", "taste.sourness", "taste.bitterness"],
    "mouthfeel": ["mouthfeel.astringent"],
}
RIDGE = 0.05  # Fixed before auxiliary evaluation; no historical/one-coffee tuning.


def read(path):
    return json.loads(Path(path).read_text())


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    path.chmod(0o600)


def observation_value(cell, protocol):
    if cell.get("status") not in {"OBSERVED", "TRUE_ZERO"}:
        return None
    value = cell.get("value")
    if protocol == "ordinal":
        if (
            cell["scale"].get("type") != "ordinal"
            or cell["scale"].get("zero_means_absence") is not False
        ):
            raise ValueError("SOURCE_ORDINAL_SCALE_NOT_VERIFIED")
        if cell["status"] == "TRUE_ZERO" or value not in range(5):
            raise ValueError("ORDINAL_ZERO_IS_LOW_CATEGORY_NOT_ABSENCE")
    elif protocol == "binary CATA":
        if cell["scale"].get("type") != "binary CATA" or value not in (0, 1):
            raise ValueError("COMPLETE_CATA_BINARY_PROTOCOL_REQUIRED")
        if (value == 0) != (cell["status"] == "TRUE_ZERO"):
            raise ValueError("CATA_ZERO_OBSERVATION_STATUS_MISMATCH")
    else:
        raise ValueError("UNREGISTERED_SOURCE_PROTOCOL")
    return float(value)


def group_weights(records):
    counts = Counter(r["group_id"] for r in records)
    weights = np.asarray([1 / counts[r["group_id"]] for r in records])
    return weights / weights.sum()


def evidence_spec(bundle):
    return ["supported_descriptor_family:" + a for a in runtime.ATTRS] + [
        "direct_concept:" + c
        for c in bundle["candidate_vocabulary"]
        if c.startswith("sensory.")
    ]


def encode_evidence(state, bundle, feature_names):
    """Same observation-only path for fitting, evaluation and live auxiliary use."""
    encoded = runtime.encode_features(state, bundle)
    direct = set(encoded["interpreted_evidence"]["confirmed"])
    supported = set(
        encoded["sensory_attribute_state"]["observed_or_supported_attributes"]
    )
    values = []
    for name in feature_names:
        family, concept = name.split(":", 1)
        values.append(
            float(
                concept
                in (supported if family == "supported_descriptor_family" else direct)
            )
        )
    return np.asarray(values)


def prepared_states(records, bundle):
    states = {stage: [] for stage in STAGES}
    audit = []
    for record in records:
        episode, trajectory, answers = training.trajectory(record, bundle)
        for stage, index in STAGES.items():
            states[stage].append(trajectory[index])
        audit.append(
            {
                "record_id": record["record_id"],
                "group_id": record["group_id"],
                "source_evidence_unit_ids": record["evidence_unit_ids"],
                "visible_descriptor_ids": episode["visible"],
                "question_ids": [a["question_id"] for a in answers],
                "label_block_used_as_input": False,
                "proxy_status": "DERIVED_RECORD_PROXY",
            }
        )
    return states, audit


def fit_ordinal(X, y, sample_weights, levels=5, ridge=RIDGE):
    """Shared-beta cumulative logistic thresholds, ordered by positive gaps."""
    X, y = np.asarray(X, float), np.asarray(y, int)
    sample_weights = np.asarray(sample_weights, float)
    sample_weights = sample_weights / sample_weights.sum()
    if not len(y) or np.any((y < 0) | (y >= levels)):
        raise ValueError("VALID_ORDINAL_OBSERVATIONS_REQUIRED")
    scale = np.sqrt(np.mean(X * X, axis=0))
    scale[scale < 1e-8] = 1.0
    Z = X / scale
    target = (y[:, None] > np.arange(levels - 1)).astype(float)
    baseline = np.clip(np.sum(sample_weights[:, None] * target, axis=0), 1e-5, 1 - 1e-5)
    theta = np.log((1 - baseline) / baseline)
    theta = np.maximum.accumulate(theta + np.arange(levels - 1) * 1e-3)
    params = np.zeros(X.shape[1] + levels - 1)
    params[X.shape[1]] = theta[0]
    gaps = np.maximum(np.diff(theta), 1e-4)
    params[X.shape[1] + 1 :] = np.log(np.expm1(gaps))

    def unpack(p):
        beta = p[: X.shape[1]]
        raw = p[X.shape[1] :]
        cut = raw[0] + np.r_[0.0, np.cumsum(np.logaddexp(0, raw[1:]))]
        return beta, raw, cut

    def objective(p):
        beta, raw, cut = unpack(p)
        logits = Z @ beta[:, None] - cut[None, :]
        weight = sample_weights[:, None] / (levels - 1)
        residual = weight * (expit(logits) - target)
        loss = (
            np.sum(weight * (np.logaddexp(0, logits) - target * logits))
            + ridge * beta @ beta / 2
        )
        gbeta = Z.T @ residual.sum(axis=1) + ridge * beta
        gcut = -residual.sum(axis=0)
        graw = np.r_[gcut.sum(), expit(raw[1:]) * np.cumsum(gcut[::-1])[::-1][1:]]
        return float(loss), np.r_[gbeta, graw]

    with threadpool_limits(limits=1):
        fit = minimize(
            objective,
            params,
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7},
        )
    if not fit.success:
        raise RuntimeError("ORDINAL_HEAD_FIT_FAILED:" + str(fit.message))
    beta, raw, cut = unpack(fit.x)
    return {
        "version": VERSION,
        "kind": "ORDERED_CUMULATIVE_LOGISTIC",
        "levels": levels,
        "scale": scale.tolist(),
        "coefficients": beta.tolist(),
        "thresholds": cut.tolist(),
        "baseline_exceedance": baseline.tolist(),
        "ridge": ridge,
        "fit_loss": float(fit.fun),
        "iterations": int(fit.nit),
        "label_scale": "SOURCE_ORDERED_CATEGORIES_NOT_INTERVAL_INTENSITY",
        "zero_semantics": "LOWEST_OBSERVED_ORDINAL_CATEGORY_NOT_ABSENCE",
    }


def predict_ordinal(X, model):
    if (
        model.get("version") != VERSION
        or model.get("kind") != "ORDERED_CUMULATIVE_LOGISTIC"
    ):
        raise ValueError("ORDINAL_MODEL_VERSION_REQUIRED")
    thresholds = np.asarray(model["thresholds"])
    if np.any(np.diff(thresholds) < 0):
        raise ValueError("ORDINAL_THRESHOLDS_NOT_ORDERED")
    X = np.asarray(X, float)
    score = (X / np.asarray(model["scale"])) @ np.asarray(model["coefficients"])
    exceedance = expit(score[:, None] - thresholds[None, :])
    distribution = np.column_stack(
        [1 - exceedance[:, 0], -np.diff(exceedance, axis=1), exceedance[:, -1]]
    )
    return {
        "category_distribution": distribution,
        "threshold_exceedance": exceedance,
        "median_category": (exceedance > 0.5).sum(axis=1),
    }


def ordinal_metric_rows(records, values, predictions, baseline, target, stage):
    rows = []
    for i, (record, value) in enumerate(zip(records, values)):
        if value is None:
            continue
        true = float(value) > np.arange(4)
        pred = predictions["threshold_exceedance"][i]
        rows.append(
            {
                "record_id": record["record_id"],
                "group_id": record["group_id"],
                "target": target,
                "stage": stage,
                "threshold_brier": float(np.mean((pred - true) ** 2)),
                "baseline_threshold_brier": float(
                    np.mean((np.asarray(baseline) - true) ** 2)
                ),
                "ordinal_category_steps_error": float(
                    abs(predictions["median_category"][i] - value)
                ),
                "exact_category_accuracy": float(
                    predictions["median_category"][i] == value
                ),
                "label_category": value,
                "predicted_category_distribution": predictions["category_distribution"][
                    i
                ].tolist(),
            }
        )
    return rows


def summarize_ordinal(rows):
    result = {}
    for stage in STAGES:
        result[stage] = {}
        for target in ORDINAL_TARGETS:
            subset = [r for r in rows if r["stage"] == stage and r["target"] == target]
            grouped = defaultdict(list)
            for row in subset:
                grouped[row["group_id"]].append(row)
            values = {
                g: {
                    key: float(np.mean([r[key] for r in rs]))
                    for key in [
                        "threshold_brier",
                        "baseline_threshold_brier",
                        "ordinal_category_steps_error",
                        "exact_category_accuracy",
                    ]
                }
                for g, rs in grouped.items()
            }
            deltas = np.asarray(
                [
                    v["threshold_brier"] - v["baseline_threshold_brier"]
                    for v in values.values()
                ]
            )
            rng = np.random.default_rng(training.SEED)
            interval = (
                np.quantile(
                    deltas[rng.integers(0, len(deltas), (5000, len(deltas)))].mean(
                        axis=1
                    ),
                    [0.025, 0.975],
                ).tolist()
                if len(deltas)
                else [None, None]
            )
            conclusion = (
                "PROXY_IMPROVEMENT_SUPPORTED"
                if deltas.size and interval[1] < 0
                else (
                    "NO_IMPROVEMENT"
                    if deltas.size and interval[0] > 0
                    else "INCONCLUSIVE"
                )
            )
            result[stage][target] = {
                "model_minus_baseline_brier_delta": (
                    float(deltas.mean()) if deltas.size else None
                ),
                "paired_coffee_95_interval": interval,
                "conclusion": conclusion,
                "interval_scope": "Bootstrap fixed grouped held-out predictions; does not include refitting uncertainty or new-source transfer.",
                "observations": len(subset),
                "coffee_groups": len(values),
                **{
                    key: (
                        float(np.mean([v[key] for v in values.values()]))
                        if values
                        else None
                    )
                    for key in [
                        "threshold_brier",
                        "baseline_threshold_brier",
                        "ordinal_category_steps_error",
                        "exact_category_accuracy",
                    ]
                },
                "paired_group_brier_delta_model_minus_baseline": {
                    g: v["threshold_brier"] - v["baseline_threshold_brier"]
                    for g, v in values.items()
                },
                "meaning": "Lower threshold Brier is better. Category steps are ordinal rank differences, not physical intensity error.",
            }
    return result


def fit_ordinal_bundle(records, states, backend_bundle):
    names = evidence_spec(backend_bundle)
    heads = {}
    weights = group_weights(records)
    for stage, stage_states in states.items():
        X = np.asarray(
            [encode_evidence(st, backend_bundle, names) for st in stage_states]
        )
        heads[stage] = {}
        for target in ORDINAL_TARGETS:
            y = [
                observation_value(r["attribute_measurements"][target], "ordinal")
                for r in records
            ]
            observed = np.asarray([v is not None for v in y])
            head = fit_ordinal(
                X[observed],
                np.asarray([v for v in y if v is not None]),
                weights[observed],
            )
            head["observed_label_cells"] = int(observed.sum())
            head["missing_label_cells"] = int((~observed).sum())
            heads[stage][target] = head
    return {
        "version": VERSION,
        "source_family": "zenodo",
        "role": "CORE_PROFESSIONAL",
        "feature_names": names,
        "backend_bundle_id": backend_bundle["bundle_id"],
        "training_groups": sorted({r["group_id"] for r in records}),
        "heads": heads,
        "label_blocks_never_runtime_features": True,
        "unobserved_descriptors": "No sensory absence labels; binary inputs mean explicitly observed support only.",
        "dimension_distinction": "descriptor_family.sweet predicts source taste.sweetness through learned associations; these are not synonyms.",
    }


def predict_from_state(state, backend_bundle, head_bundle, stage):
    if head_bundle.get("version") != VERSION or stage not in head_bundle["heads"]:
        raise ValueError("SENSORY_VIEW_VERSION_OR_STAGE_MISMATCH")
    if backend_bundle["bundle_id"] != head_bundle["backend_bundle_id"]:
        raise ValueError("SENSORY_VIEW_BACKEND_VERSION_MISMATCH")
    X = encode_evidence(state, backend_bundle, head_bundle["feature_names"])[None, :]
    return {
        target: {
            key: value[0].tolist() for key, value in predict_ordinal(X, model).items()
        }
        for target, model in head_bundle["heads"][stage].items()
    }


def evaluate_ordinal(records, states, backend_bundle, head_bundle):
    rows = []
    for stage, stage_states in states.items():
        X = np.asarray(
            [
                encode_evidence(st, backend_bundle, head_bundle["feature_names"])
                for st in stage_states
            ]
        )
        for target in ORDINAL_TARGETS:
            head = head_bundle["heads"][stage][target]
            y = [
                observation_value(r["attribute_measurements"][target], "ordinal")
                for r in records
            ]
            rows.extend(
                ordinal_metric_rows(
                    records,
                    y,
                    predict_ordinal(X, head),
                    head["baseline_exceedance"],
                    target,
                    stage,
                )
            )
    return rows


def fit_binary(X, y, ridge=RIDGE):
    X, y = np.asarray(X, float), np.asarray(y, float)
    prior = float(y.mean())
    intercept = float(
        np.log(np.clip(prior, 1e-5, 1 - 1e-5) / (1 - np.clip(prior, 1e-5, 1 - 1e-5)))
    )

    def objective(params):
        logits = X @ params[1:] + params[0]
        error = (expit(logits) - y) / len(y)
        loss = (
            np.mean(np.logaddexp(0, logits) - y * logits)
            + ridge * params[1:] @ params[1:] / 2
        )
        return float(loss), np.r_[error.sum(), X.T @ error + ridge * params[1:]]

    with threadpool_limits(limits=1):
        fit = minimize(
            objective,
            np.r_[intercept, np.zeros(X.shape[1])],
            jac=True,
            method="L-BFGS-B",
            options={"maxiter": 300, "gtol": 1e-7, "ftol": 1e-11},
        )
    if not fit.success:
        raise RuntimeError("CATA_HEAD_FIT_FAILED:" + str(fit.message))
    return {
        "version": VERSION,
        "kind": "CATA_COMPLETE_BALLOT_LOGISTIC",
        "intercept": float(fit.x[0]),
        "coefficients": fit.x[1:].tolist(),
        "baseline_prevalence": prior,
        "ridge": ridge,
        "iterations": int(fit.nit),
    }


def predict_cata(measurements, model):
    """Auxiliary complete-ballot interface; an unshown term is never filled as 0."""
    output = {}
    for target, head in model["heads"].items():
        values = [
            (
                observation_value(measurements[c], "binary CATA")
                if c in measurements
                else None
            )
            for c in head["input_concepts"]
        ]
        output[target] = (
            float(
                expit(
                    np.asarray(values) @ np.asarray(head["coefficients"])
                    + head["intercept"]
                )
            )
            if all(v is not None for v in values)
            else None
        )
    return output


def train_cata(records):
    if any(
        r["source_family"] != "cotter_2023"
        or r["role"] != "AUX_COFFEE_WEAK_LABEL"
        or r["split"] != "DEVELOPMENT"
        for r in records
    ):
        raise ValueError("CATA_AUXILIARY_DEVELOPMENT_SCOPE_REQUIRED")
    columns = [c for view in CATA_VIEWS.values() for c in view]
    heads, diagnostic = {}, {}
    for view, targets in CATA_VIEWS.items():
        inputs = [c for c in columns if c not in targets]
        X = np.asarray(
            [
                [
                    observation_value(r["attribute_measurements"][c], "binary CATA")
                    for c in inputs
                ]
                for r in records
            ]
        )
        if any(v is None for row in X for v in row):
            raise ValueError("CATA_INPUT_VIEW_MUST_BE_OBSERVED")
        for target in targets:
            y = np.asarray(
                [
                    observation_value(
                        r["attribute_measurements"][target], "binary CATA"
                    )
                    for r in records
                ]
            )
            if any(v is None for v in y):
                raise ValueError("CATA_TARGET_MUST_BE_OBSERVED")
            head = fit_binary(X, y)
            head.update(input_concepts=inputs, held_attribute_view=view)
            heads[target] = head
            pred = expit(X @ np.asarray(head["coefficients"]) + head["intercept"])
            baseline = head["baseline_prevalence"]
            diagnostic[target] = {
                "held_attribute_view": view,
                "inputs": inputs,
                "fitting_rows": len(y),
                "observed_positive_cells": int(y.sum()),
                "true_zero_cells": int((y == 0).sum()),
                "same_rows_held_view_brier": float(np.mean((pred - y) ** 2)),
                "same_rows_prevalence_baseline_brier": float(
                    np.mean((baseline - y) ** 2)
                ),
                "status": "FITTING_ROW_VIEW_COMPLETION_DIAGNOSTIC_NOT_HELDOUT_GENERALIZATION",
            }
    model = {
        "version": VERSION,
        "source_family": "cotter_2023",
        "role": "AUX_COFFEE_WEAK_LABEL",
        "training_groups": sorted({r["group_id"] for r in records}),
        "heads": heads,
        "views": CATA_VIEWS,
        "modality_note": "Descriptor association terms were not measured as pure olfaction. They remain distinct from explicit taste and mouthfeel terms; tea_floral stays compound.",
        "not_deployed_for_candidate_scoring": True,
    }
    exact = predict_cata(records[0]["attribute_measurements"], model) == predict_cata(
        records[0]["attribute_measurements"], json.loads(json.dumps(model))
    )
    return model, {
        "observations_used_for_auxiliary_training": len(records),
        "observed_cells_used": len(records) * len(columns),
        "complete_binary_attributes": len(columns),
        "independent_coffees": len(model["training_groups"]),
        "cross_coffee_generalization": "NOT_ESTIMABLE",
        "independent_panelist_and_condition_ids": "NOT_RECOVERABLE_FROM_AUTHOR_DERIVATIVE",
        "row_random_split_used": False,
        "view_diagnostics": diagnostic,
        "model_reload_identical": exact,
        "candidate_ranking_gain": "NOT_EVALUATED",
        "source_role": "AUX_COFFEE_WEAK_LABEL",
        "in_core_ranking_evaluation": False,
        "real_user_answer_evaluation": "NOT_EVALUATED",
        "dimension_separation": CATA_VIEWS,
    }


def run(owner_dir, summary_path=None):
    owner = Path(owner_dir)
    private = owner / "revisions/r1"
    source = private / "zenodo_attribute_observations.private.json"
    d1 = private / "d1_attribute_observations.private.json"
    ordinal = read(source)
    cata = read(d1)
    d0 = read(owner / "recovery_records.json")
    folds = training.split_groups([r for r in d0 if r["split"] == "DEVELOPMENT"], 3)
    known = [r for r in ordinal if r["lot_identity_status"] == "D0_KNOWN_GROUP"]
    dev = [r for r in known if r["split"] == "DEVELOPMENT"]
    historical = [r for r in known if r["split"] == "HISTORICAL_REGRESSION"]
    if set(r["group_id"] for r in dev) - set(folds):
        raise ValueError("ATTRIBUTE_GROUP_NOT_IN_FROZEN_D0_DEVELOPMENT")
    cv_rows, audit = [], []
    anchor = "M2_R1_FIXED_LEGACY_LOCKED"
    start = time.perf_counter()
    for fold in range(3):
        train = [r for r in dev if folds[r["group_id"]] != fold]
        held = [r for r in dev if folds[r["group_id"]] == fold]
        backend = read(private / f"cv/{anchor}_fold{fold}.model.json")
        train_states, train_audit = prepared_states(train, backend)
        held_states, held_audit = prepared_states(held, backend)
        model = fit_ordinal_bundle(train, train_states, backend)
        model["fold"] = fold
        path = private / f"models/M2_R1_ORDINAL_ATTRIBUTES_fold{fold}.model.json"
        save(path, model)
        rows = evaluate_ordinal(held, held_states, backend, read(path))
        cv_rows.extend(rows)
        audit.append(
            {
                "fold": fold,
                "training_groups": model["training_groups"],
                "evaluation_groups": sorted({r["group_id"] for r in held}),
                "feature_backend_bundle_id": backend["bundle_id"],
                "input_measurement_block_masked": True,
                "label_feature_path": "encode_evidence",
                "per_state_input_lineage": train_audit + held_audit,
            }
        )
        print(
            json.dumps(
                {
                    "phase": "ordinal_attributes",
                    "fold": fold,
                    "train_observations": len(train),
                    "held_observations": len(held),
                }
            ),
            flush=True,
        )
    backend = read(private / f"models/{anchor}.model.json")
    states, train_audit = prepared_states(dev, backend)
    model = fit_ordinal_bundle(dev, states, backend)
    model_path = private / "models/M2_R1_ORDINAL_ATTRIBUTES.model.json"
    save(model_path, model)
    historical_states, hist_audit = prepared_states(historical, backend)
    historical_rows = evaluate_ordinal(
        historical, historical_states, backend, read(model_path)
    )
    reload_equal = predict_from_state(
        states["FIRST_CORRECTION"][0], backend, model, "FIRST_CORRECTION"
    ) == predict_from_state(
        states["FIRST_CORRECTION"][0], backend, read(model_path), "FIRST_CORRECTION"
    )
    cata_model, cata_metrics = train_cata(cata)
    cata_path = private / "models/M2_R1_CATA_AUX_ATTRIBUTES.model.json"
    save(cata_path, cata_model)
    save(
        private / "sensory_view_evaluation.private.json",
        {
            "ordinal_cv": cv_rows,
            "ordinal_historical": historical_rows,
            "fold_audit": audit,
            "final_fit_input_audit": train_audit,
            "historical_input_audit": hist_audit,
        },
    )
    summary = {
        "module_version": VERSION,
        "backend_anchor": anchor,
        "scope": "AUXILIARY_SOURCE_SPECIFIC_ATTRIBUTE_COMPONENTS; NO_DEFAULT_CANDIDATE_SCORING_CHANGE",
        "ordinal": {
            "source": "zenodo",
            "observations_total": len(ordinal),
            "known_d0_observations": len(known),
            "development_observations": len(dev),
            "development_coffees": len({r["group_id"] for r in dev}),
            "historical_observations": len(historical),
            "historical_coffees": len({r["group_id"] for r in historical}),
            "quarantined_observations_excluded": len(ordinal) - len(known),
            "new_independent_coffees": 0,
            "group_cv": summarize_ordinal(cv_rows),
            "historical_regression": summarize_ordinal(historical_rows),
            "group_split": "Frozen D0 three-fold assignments. All same-coffee observations stay together.",
            "regularization": {
                "ridge": RIDGE,
                "selection": "FIXED_BEFORE_RUN_NO_HISTORICAL_TUNING",
            },
            "source_protocol": "Ordered five-category intensity labels, 0 is lowest category and never absence; no interval-scale intensity claim.",
            "input_scope": "Only descriptor evidence actually exposed by the legal R1 question trajectory; full ordinal attribute block is target-only.",
            "relationship": "Separate attribute block from same panel row/sample; DERIVED_RECORD_PROXY, not independent user answer validation.",
            "model_reload_identical": reload_equal,
            "real_user_answer_evaluation": "NOT_EVALUATED",
        },
        "cata": cata_metrics,
        "artifact_hashes": {
            "zenodo_observations": digest_file(source),
            "cata_observations": digest_file(d1),
            "ordinal_model": digest_file(model_path),
            "cata_model": digest_file(cata_path),
        },
        "private_model_paths": {"ordinal": str(model_path), "cata": str(cata_path)},
        "elapsed_seconds": time.perf_counter() - start,
        "no_frontend_changes": True,
    }
    save(private / "sensory_views_metrics.private.json", summary)
    if summary_path:
        save(summary_path, summary)
    return summary


FULL_CATA_VERSION = "m2-r1-source-sensory-views.full-cata.v1"
FULL_CATA_VIEWS = {
    "descriptor_associations": CATA_VIEWS["descriptor_associations"]
    + [
        "broad.citrus",
        "compound.green_vegetative",
        "compound.paper_wood",
        "native.cereal",
    ],
    "basic_tastes": list(CATA_VIEWS["basic_tastes"]),
    "mouthfeel": CATA_VIEWS["mouthfeel"] + ["mouthfeel.thick_viscous"],
}
FULL_CATA_AXES = {"judge": "panelist_id", "brew_condition": "condition_id"}


def validate_full_cata(records, expected_shape=None):
    columns = [c for view in FULL_CATA_VIEWS.values() for c in view]
    if not records or len(columns) != 17 or len(set(columns)) != 17:
        raise ValueError("FULL_ORIGINAL_CATA_17_COLUMNS_REQUIRED")
    pairs, identities = set(), set()
    for record in records:
        if (
            record["source_family"] != "cotter_2023"
            or record["role"] != "AUX_COFFEE_WEAK_LABEL"
            or record["split"] != "DEVELOPMENT"
            or record["supervision"] != "COMPLETE_ORIGINAL_CONSUMER_CATA_MATRIX"
        ):
            raise ValueError("FULL_CATA_SOURCE_AND_AUXILIARY_SCOPE_REQUIRED")
        if not record.get("panelist_id") or not record.get("condition_id"):
            raise ValueError("ACTUAL_JUDGE_AND_BREW_IDENTITIES_REQUIRED")
        pair = (record["panelist_id"], record["condition_id"])
        if pair in pairs or record["record_id"] in identities:
            raise ValueError("DUPLICATE_ORIGINAL_CATA_OBSERVATION")
        pairs.add(pair)
        identities.add(record["record_id"])
        if set(record["attribute_measurements"]) != set(columns):
            raise ValueError("FULL_CATA_BALLOT_SCHEMA_MISMATCH")
        for concept in columns:
            if (
                observation_value(
                    record["attribute_measurements"][concept], "binary CATA"
                )
                is None
            ):
                raise ValueError("FULL_CATA_BALLOT_MUST_BE_OBSERVED_NOT_IMPUTED")
    judges = {r["panelist_id"] for r in records}
    conditions = {r["condition_id"] for r in records}
    if len(pairs) != len(judges) * len(conditions):
        raise ValueError("FULL_CATA_CROSSED_JUDGE_CONDITION_MATRIX_REQUIRED")
    if expected_shape and (len(judges), len(conditions)) != expected_shape:
        raise ValueError("FULL_CATA_SOURCE_MATRIX_SHAPE_MISMATCH")
    return {
        "observations": len(records),
        "judges": len(judges),
        "brew_conditions": len(conditions),
        "coffee_groups": len({r["group_id"] for r in records}),
        "measured_binary_cells": len(records) * len(columns),
    }


def full_cata_folds(records, axis, folds=3):
    if axis not in FULL_CATA_AXES:
        raise ValueError("REGISTERED_HOLDOUT_AXIS_REQUIRED")
    key = FULL_CATA_AXES[axis]
    identities = sorted(
        {r[key] for r in records},
        key=lambda identity: runtime.digest(
            [FULL_CATA_VERSION, training.SEED, axis, identity]
        ),
    )
    if len(identities) < folds:
        raise ValueError("INSUFFICIENT_HOLDOUT_UNITS")
    return {identity: i % folds for i, identity in enumerate(identities)}


def encode_full_cata(measurements, input_concepts):
    values = [
        observation_value(measurements[c], "binary CATA") if c in measurements else None
        for c in input_concepts
    ]
    return np.asarray(values, float) if all(v is not None for v in values) else None


def fit_full_cata(records):
    columns = [c for view in FULL_CATA_VIEWS.values() for c in view]
    heads = {}
    for view, targets in FULL_CATA_VIEWS.items():
        inputs = [c for c in columns if c not in targets]
        vectors = [
            encode_full_cata(r["attribute_measurements"], inputs) for r in records
        ]
        if any(vector is None for vector in vectors):
            raise ValueError("CATA_FIT_REQUIRES_OBSERVED_INPUT_VIEW")
        X = np.asarray(vectors)
        for target in targets:
            values = [
                observation_value(r["attribute_measurements"][target], "binary CATA")
                for r in records
            ]
            if any(value is None for value in values):
                raise ValueError("CATA_FIT_REQUIRES_OBSERVED_TARGET_CELL")
            head = fit_binary(X, np.asarray(values))
            head.update(
                input_concepts=inputs,
                held_attribute_view=view,
                true_zero_training_cells=sum(value == 0 for value in values),
                observed_positive_training_cells=sum(value == 1 for value in values),
            )
            heads[target] = head
    return {
        "version": FULL_CATA_VERSION,
        "heads": heads,
        "views": FULL_CATA_VIEWS,
        "source_family": "cotter_2023",
        "role": "AUX_COFFEE_WEAK_LABEL",
        "training_record_ids": sorted(r["record_id"] for r in records),
        "training_judge_ids": sorted({r["panelist_id"] for r in records}),
        "training_condition_ids": sorted({r["condition_id"] for r in records}),
        "training_coffee_groups": sorted({r["group_id"] for r in records}),
        "training_observations": len(records),
        "ridge": RIDGE,
        "input_path": "encode_full_cata: only actually observed cells from other attribute views",
        "excluded_runtime_features": [
            "judge ID",
            "brew ID",
            "temperature",
            "TDS",
            "PE",
            "Week",
            "Session",
            "Position",
            "liking",
            "JAR",
            "purchase intent",
            "source C1",
        ],
        "source_protocol": "Complete original 17-column consumer CATA; 0 means not detected on that explicitly exposed ballot.",
        "modality_note": "Source descriptor terms are not separate olfactory measurements; explicit basic-taste and mouthfeel targets remain distinct, compounds stay whole.",
        "not_deployed_for_candidate_scoring": True,
    }


def predict_full_cata(measurements, model):
    if (
        model.get("version") != FULL_CATA_VERSION
        or model.get("views") != FULL_CATA_VIEWS
    ):
        raise ValueError("FULL_CATA_MODEL_VERSION_MISMATCH")
    result = {}
    for target, head in model["heads"].items():
        if set(head["input_concepts"]) & set(
            FULL_CATA_VIEWS[head["held_attribute_view"]]
        ):
            raise ValueError("HELD_ATTRIBUTE_VIEW_LEAKAGE")
        vector = encode_full_cata(measurements, head["input_concepts"])
        result[target] = (
            float(expit(vector @ np.asarray(head["coefficients"]) + head["intercept"]))
            if vector is not None
            else None
        )
    return result


def evaluate_full_cata(records, model, axis, fold):
    rows = []
    key = FULL_CATA_AXES[axis]
    training_ids = set(
        model["training_judge_ids" if axis == "judge" else "training_condition_ids"]
    )
    if training_ids & {r[key] for r in records}:
        raise ValueError("FULL_CATA_HOLDOUT_ID_LEAKAGE")
    for record in records:
        pred = predict_full_cata(record["attribute_measurements"], model)
        for target, head in model["heads"].items():
            value = observation_value(
                record["attribute_measurements"][target], "binary CATA"
            )
            if value is None or pred[target] is None:
                raise ValueError("CANNOT_SILENTLY_DROP_FULL_CATA_EVALUATION_CELL")
            p = pred[target]
            prior = head["baseline_prevalence"]
            rows.append(
                {
                    "record_id": record["record_id"],
                    "coffee_group": record["group_id"],
                    "judge_id": record["panelist_id"],
                    "condition_id": record["condition_id"],
                    "holdout_unit": record[key],
                    "holdout_axis": axis,
                    "fold": fold,
                    "target": target,
                    "held_attribute_view": head["held_attribute_view"],
                    "observed_binary_value": value,
                    "predicted_detection_support": p,
                    "training_prevalence_baseline": prior,
                    "brier": float((p - value) ** 2),
                    "baseline_brier": float((prior - value) ** 2),
                    "log_loss": float(
                        -value * np.log(max(p, 1e-12))
                        - (1 - value) * np.log(max(1 - p, 1e-12))
                    ),
                }
            )
    return rows


def summarize_full_cata(rows, axis):
    output = {}
    for target in sorted({r["target"] for r in rows}):
        subset = [r for r in rows if r["target"] == target]
        units = defaultdict(list)
        for row in subset:
            units[row["holdout_unit"]].append(row)
        paired = {
            unit: float(np.mean([r["brier"] - r["baseline_brier"] for r in rs]))
            for unit, rs in sorted(units.items())
        }
        deltas = np.asarray(list(paired.values()))
        rng = np.random.default_rng(training.SEED)
        interval = np.quantile(
            deltas[rng.integers(0, len(deltas), (2000, len(deltas)))].mean(axis=1),
            [0.025, 0.975],
        ).tolist()
        output[target] = {
            "evaluated_observations": len(subset),
            "held_out_units": len(units),
            "mean_brier": float(
                np.mean([np.mean([r["brier"] for r in rs]) for rs in units.values()])
            ),
            "training_prevalence_baseline_brier": float(
                np.mean(
                    [
                        np.mean([r["baseline_brier"] for r in rs])
                        for rs in units.values()
                    ]
                )
            ),
            "model_minus_baseline_brier": float(deltas.mean()),
            "paired_holdout_unit_95_interval": interval,
            "per_holdout_unit_delta": paired,
            "observed_zero_cells": sum(r["observed_binary_value"] == 0 for r in subset),
            "observed_positive_cells": sum(
                r["observed_binary_value"] == 1 for r in subset
            ),
            "mean_log_loss": float(np.mean([r["log_loss"] for r in subset])),
            "conclusion": (
                "PROXY_IMPROVEMENT_SUPPORTED"
                if interval[1] < 0
                else "NO_IMPROVEMENT" if interval[0] > 0 else "INCONCLUSIVE"
            ),
            "conclusion_scope": "Same-coffee source-native CATA view prediction on held-"
            + axis
            + " identities; not cross-coffee or product FOUNDATION_CHECK validation.",
        }
    macro_units = defaultdict(list)
    for row in rows:
        macro_units[row["holdout_unit"]].append(row["brier"] - row["baseline_brier"])
    macro_deltas = np.asarray([np.mean(v) for _, v in sorted(macro_units.items())])
    rng = np.random.default_rng(training.SEED)
    macro_interval = np.quantile(
        macro_deltas[
            rng.integers(0, len(macro_deltas), (2000, len(macro_deltas)))
        ].mean(axis=1),
        [0.025, 0.975],
    ).tolist()
    return {
        "holdout_axis": axis,
        "targets": output,
        "macro_paired_holdout_unit_95_interval": macro_interval,
        "target_intervals": "Seventeen nominal exploratory intervals; no multiplicity-adjusted claim. The macro metric averages complete target columns within each held identity.",
        "target_macro_mean_brier": float(
            np.mean([x["mean_brier"] for x in output.values()])
        ),
        "target_macro_baseline_brier": float(
            np.mean([x["training_prevalence_baseline_brier"] for x in output.values()])
        ),
        "target_macro_model_minus_baseline_brier": float(
            np.mean([x["model_minus_baseline_brier"] for x in output.values()])
        ),
        "coverage": 1.0,
        "columns": len(output),
        "uncertainty_scope": "Bootstrap fixed OOF prediction deltas by held-out axis; single-coffee and shared opposite-axis dependence remain. No refitting or cross-coffee uncertainty claim.",
        "cross_coffee_generalization": "NOT_ESTIMABLE",
    }


def run_full_cata(owner_dir, summary_path=None):
    owner = Path(owner_dir)
    private = owner / "revisions/r1"
    source = private / "cotter_full_attribute_observations.private.json"
    records = read(source)
    shape = validate_full_cata(records, expected_shape=(118, 27))
    assignments = {axis: full_cata_folds(records, axis) for axis in FULL_CATA_AXES}
    config = {
        "version": FULL_CATA_VERSION,
        "input_sha256": digest_file(source),
        "matrix": shape,
        "folds": 3,
        "seed": training.SEED,
        "holdout_assignments": assignments,
        "ridge": RIDGE,
        "view_masks": FULL_CATA_VIEWS,
        "parameter_selection": "NONE_FIXED_BEFORE_EVALUATION",
        "existing_author_derivative": "Preserved separately; never concatenated with overlapping original rows.",
        "single_coffee_scope": "Generalization across held judges or brew conditions within this coffee only; opposite identity axis shared.",
    }
    config_hash = runtime.digest(config)
    plan_path = private / "full_cata_plan.private.json"
    if plan_path.exists():
        if read(plan_path)["config_hash"] != config_hash:
            raise ValueError("FULL_CATA_PREREGISTERED_PLAN_CHANGED")
    else:
        save(
            plan_path,
            {
                "registered_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "config_hash": config_hash,
                **config,
            },
        )
    old_models = list((private / "models").glob("M2_R1_CATA_AUX_ATTRIBUTES.model.json"))
    retained_hashes = {str(path): digest_file(path) for path in old_models}
    started = time.perf_counter()
    all_rows = {}
    summaries = {}
    audit = []
    saved_models = []
    reload_equal = True
    for axis, id_field in FULL_CATA_AXES.items():
        rows = []
        for fold in range(3):
            train = [r for r in records if assignments[axis][r[id_field]] != fold]
            held = [r for r in records if assignments[axis][r[id_field]] == fold]
            path = (
                private
                / f"models/M2_R1_CATA_AUX_ATTRIBUTES_FULL_{axis}_fold{fold}.model.json"
            )
            if path.exists():
                model = read(path)
                if model.get("experiment_config_hash") != config_hash or set(
                    model["training_record_ids"]
                ) != {r["record_id"] for r in train}:
                    raise ValueError("CACHED_FULL_CATA_FIT_DOES_NOT_MATCH_PLAN")
            else:
                model = fit_full_cata(train)
                model.update(
                    experiment_config_hash=config_hash, holdout_axis=axis, fold=fold
                )
                save(path, model)
            loaded = read(path)
            reload_equal &= predict_full_cata(
                held[0]["attribute_measurements"], model
            ) == predict_full_cata(held[0]["attribute_measurements"], loaded)
            rows.extend(evaluate_full_cata(held, loaded, axis, fold))
            audit.append(
                {
                    "axis": axis,
                    "fold": fold,
                    "training_observations": len(train),
                    "held_observations": len(held),
                    "train_identity_ids": sorted({r[id_field] for r in train}),
                    "held_identity_ids": sorted({r[id_field] for r in held}),
                    "identity_overlap": False,
                    "source_labels_masked_from_input_view": True,
                    "model_sha256": digest_file(path),
                }
            )
            saved_models.append(str(path))
            print(
                json.dumps(
                    {
                        "phase": "full_cata",
                        "axis": axis,
                        "fold": fold,
                        "train": len(train),
                        "held": len(held),
                    }
                ),
                flush=True,
            )
        all_rows[axis] = rows
        summaries[axis] = summarize_full_cata(rows, axis)
    path = private / "models/M2_R1_CATA_AUX_ATTRIBUTES_FULL.model.json"
    if path.exists():
        full = read(path)
        if full.get("experiment_config_hash") != config_hash:
            raise ValueError("CACHED_FULL_CATA_FINAL_FIT_DOES_NOT_MATCH_PLAN")
    else:
        full = fit_full_cata(records)
        full["experiment_config_hash"] = config_hash
        save(path, full)
    reload_equal &= predict_full_cata(
        records[0]["attribute_measurements"], full
    ) == predict_full_cata(records[0]["attribute_measurements"], read(path))
    saved_models.append(str(path))
    if any(digest_file(path) != digest for path, digest in retained_hashes.items()):
        raise AssertionError("OLD_CATA_DERIVATIVE_MODEL_CHANGED")
    save(
        private / "full_cata_evaluation.private.json",
        {"rows": all_rows, "fold_audit": audit},
    )
    summary = {
        "version": FULL_CATA_VERSION,
        "status": "ACTUALLY_TRAINED_AND_IDENTITY_HOLDOUT_EVALUATED",
        "full_cata": {
            **shape,
            "unique_original_observations": shape["observations"],
            "effective_coffee_sample_size": shape["coffee_groups"],
            "judge_holdout": summaries["judge"],
            "brew_condition_holdout": summaries["brew_condition"],
            "ridge": RIDGE,
            "field_semantics": "Original complete 17-column CATA only. True zeros remain not-detected reports; preferences/JAR/lab values and IDs are never model inputs.",
            "proxy_status": "REAL_RECORDED_CONSUMER_CATA_WITH_OFFLINE_ATTRIBUTE_VIEW_MASKING",
            "product_FOUNDATION_CHECK_real_answer_evaluation": "NOT_EVALUATED",
            "cross_coffee_generalization": "NOT_ESTIMABLE",
            "new_independent_coffees_over_2548_derivative": 0,
            "new_independent_collection_studies_over_2548_derivative": 0,
            "old_derivative_comparison": "NOT_A_PAIRED_DATA_SIZE_COMPARISON; columns, recovered IDs and evaluation design differ.",
            "view_masks": FULL_CATA_VIEWS,
            "original_source_use": "Existing governed CC0 cache reused; no new source scraping.",
        },
        "engineering": {
            "training_evaluation_live_encoder": "encode_full_cata",
            "reload_identical": bool(reload_equal),
            "identity_disjointness_checked_each_fold": True,
            "fold_model_count": 6,
            "final_model_count": 1,
            "old_derivative_models_unchanged": True,
            "old_derivative_hashes": retained_hashes,
            "input_sha256": digest_file(source),
            "experiment_config_hash": config_hash,
            "private_model_paths": saved_models,
            "elapsed_seconds": time.perf_counter() - started,
            "no_frontend_changes": True,
        },
    }
    save(private / "full_cata_metrics.private.json", summary)
    if summary_path:
        save(summary_path, summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True, type=Path)
    parser.add_argument("--summary-path", type=Path)
    parser.add_argument("--full-cata", action="store_true")
    args = parser.parse_args()
    if args.full_cata:
        result = run_full_cata(args.owner_dir, args.summary_path)
        print(
            json.dumps(
                {
                    "status": "COMPLETED",
                    "full_cata": result["full_cata"]["unique_original_observations"],
                    "elapsed_seconds": result["engineering"]["elapsed_seconds"],
                }
            )
        )
        raise SystemExit(0)
    result = run(args.owner_dir, args.summary_path)
    print(
        json.dumps(
            {
                "status": "COMPLETED",
                "ordinal_development_coffees": result["ordinal"]["development_coffees"],
                "cata_training_observations": result["cata"][
                    "observations_used_for_auxiliary_training"
                ],
                "elapsed_seconds": result["elapsed_seconds"],
            }
        )
    )
