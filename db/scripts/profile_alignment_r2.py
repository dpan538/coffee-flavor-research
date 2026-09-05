#!/usr/bin/env python3
"""Nested source-native profile/response reconstruction; never an M2 score.

The target modality block stays hidden. R2 selects only a shared ridge strength
inside outer TRAIN. Published source codes and consumer CATA remain separate
tasks; previously inspected confirmation products are historical regression.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.special import expit
from threadpoolctl import threadpool_limits

import professional_views_m2_r1 as professional
import sensory_views_m2_r1 as response

VERSION = "m2-r2-profile-alignment.v1"
SEED = 20260905
MODELS = ("P0_TRAIN_PRIOR", "P1_FIXED_R1", "P2_NESTED_RIDGE")
RIDGES = {"rocchetti": [0.05, 0.5, 5.0], "cotter": [0.005, 0.05, 0.5]}


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
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    path.chmod(0o600)


def views(kind):
    if kind == "rocchetti":
        return copy.deepcopy(professional.VIEWS)
    if kind == "cotter":
        return copy.deepcopy(response.FULL_CATA_VIEWS)
    raise ValueError("UNREGISTERED_SOURCE_TASK")


def targets(kind):
    return [target for block in views(kind).values() for target in block]


def protocol():
    return {
        "version": VERSION,
        "rocchetti": {
            "task": "PROFESSIONAL_PROFILE_ALIGNMENT",
            "development_products": 38,
            "historical_products": 9,
            "historical_status": "PREVIOUSLY_INSPECTED_R1_CONFIRMATION_NOT_FRESH",
            "view_masks": views("rocchetti"),
            "primary_metric": "PRODUCT_MACRO_NATIVE_0_TO_9_CODE_MAE",
            "ridge_grid": RIDGES["rocchetti"],
            "outer_folds": "R1_THREE_PRODUCT_FOLDS_UNCHANGED",
            "scale_interpretation": "SOURCE_CODING_RECONSTRUCTION_NOT_PSYCHOLOGICAL_DISTANCE",
        },
        "cotter": {
            "task": "RECORDED_RESPONSE_PREDICTION",
            "participants": 118,
            "preparation_conditions": 27,
            "coffees": 1,
            "view_masks": views("cotter"),
            "primary_metric": "HELD_IDENTITY_MACRO_COMPLETE_BALLOT_BRIER",
            "ridge_grid": RIDGES["cotter"],
            "outer_folds": "R1_THREE_FOLDS_SEPARATELY_BY_PARTICIPANT_AND_CONDITION",
            "holdout_axes": ["panelist_id", "condition_id"],
            "opposite_axis": "SHARED_WITH_TRAIN_CONDITIONAL_SCOPE_ONLY",
            "cross_coffee": "NOT_ESTIMABLE",
            "overlapping_author_derivative": "NOT_CONCATENATED",
        },
        "models": list(MODELS),
        "fixed_R1_ridge": 0.05,
        "selection": "THREE_INNER_GROUP_FOLDS_GLOBAL_ALL_TARGET_MACRO_LOSS;TIES_WITHIN_1E-12_STRONGEST_RIDGE",
        "primary_contrast": "P2_NESTED_RIDGE_MINUS_P1_FIXED_R1_LOWER_IS_BETTER",
        "target_search": "NONE_NO_PER_TARGET_SELECTION",
        "input": "OBSERVED_CELLS_IN_OTHER_ENTIRE_VIEWS_ONLY_NO_IDS_OR_METADATA",
        "mask": "EXACT_SOURCE_DIMENSIONS_COMPLETE_OBSERVED_BALLOT;NO_IMPUTATION",
        "cost": {
            "fixed_budget": "SAME_OTHER_VIEW_OBSERVED_CELL_COUNT_FOR_P1_AND_P2",
            "ordinary_question_count": None,
            "offered_options": None,
            "final_candidates": None,
            "real_answer_time": "NOT_EVALUATED",
            "production_question_efficiency": "NOT_EVALUATED",
        },
        "uncertainty": "5000_FIXED_OOF_PREDICTION_PAIRED_HELD_UNIT_BOOTSTRAPS;NO_REFIT_OR_NEW_SOURCE_UNCERTAINTY",
        "per_target_results": "EXPLORATORY_NOMINAL_NO_MULTIPLICITY_CLAIM",
        "main_M2_scoring_changed": False,
        "seed": SEED,
    }


def value(cell, target, kind):
    if kind == "rocchetti":
        return professional.observation_value(cell, target)
    if kind == "cotter":
        return response.observation_value(cell or {}, "binary CATA")
    raise ValueError("UNREGISTERED_SOURCE_TASK")


def input_names(kind, view):
    return [c for c in targets(kind) if c not in views(kind)[view]]


def encode(measurements, kind, view, specification=None):
    names = input_names(kind, view)
    if specification is not None and specification != names:
        raise ValueError("HELD_VIEW_OR_UNREGISTERED_FEATURE")
    vector = [value(measurements.get(c), c, kind) for c in names]
    return np.asarray(vector, float) if all(x is not None for x in vector) else None


def fit(records, kind, ridge):
    if not records or any(r.get("split") != "DEVELOPMENT" for r in records):
        raise ValueError("ONLY_DEVELOPMENT_ROWS_ALLOWED_IN_FIT")
    if len({r["record_id"] for r in records}) != len(records):
        raise ValueError("DUPLICATE_TRAINING_OBSERVATION")
    if kind == "rocchetti" and len({r["group_id"] for r in records}) != len(records):
        raise ValueError("REPEATED_PRODUCT_WITHOUT_REGISTERED_AGGREGATION")
    if ridge not in RIDGES[kind]:
        raise ValueError("UNREGISTERED_RIDGE")
    heads = {}
    for view, block in views(kind).items():
        vectors = [encode(r["attribute_measurements"], kind, view) for r in records]
        if any(x is None for x in vectors):
            raise ValueError("COMPLETE_INPUT_VIEW_REQUIRED")
        X = np.asarray(vectors)
        for target in block:
            y = [
                value(r["attribute_measurements"].get(target), target, kind)
                for r in records
            ]
            if any(x is None for x in y):
                raise ValueError("COMPLETE_TARGET_MASK_REQUIRED")
            if any(
                r.get("attribute_masks", {}).get(target, True) is not True
                for r in records
            ):
                raise ValueError("EXPLICIT_FALSE_ATTRIBUTE_MASK")
            y = np.asarray(y)
            if kind == "rocchetti":
                mean, scale = X.mean(0), X.std(0)
                scale[scale < 1e-8] = 1.0
                y_mean, y_scale = float(y.mean()), float(y.std()) or 1.0
                Z = (X - mean) / scale
                with threadpool_limits(limits=1):
                    beta = np.linalg.solve(
                        Z.T @ Z / len(y) + ridge * np.eye(X.shape[1]),
                        Z.T @ ((y - y_mean) / y_scale) / len(y),
                    )
                head = {
                    "feature_mean": mean.tolist(),
                    "feature_scale": scale.tolist(),
                    "target_mean": y_mean,
                    "target_scale": y_scale,
                    "coefficients": beta.tolist(),
                    "prior": y_mean,
                }
            else:
                native = response.fit_binary(X, y, ridge=ridge)
                head = {
                    "coefficients": native["coefficients"],
                    "intercept": native["intercept"],
                    "prior": native["baseline_prevalence"],
                    "iterations": native["iterations"],
                }
            head.update(
                input_concepts=input_names(kind, view),
                held_view=view,
                observed_cells=len(y),
                true_zero_cells=sum(
                    r["attribute_measurements"][target]["status"] == "TRUE_ZERO"
                    for r in records
                ),
            )
            heads[target] = head
    return {
        "version": VERSION,
        "kind": kind,
        "ridge": ridge,
        "views": views(kind),
        "heads": heads,
        "training_record_ids": sorted(r["record_id"] for r in records),
        "training_identities": {
            key: sorted({r[key] for r in records})
            for key in ("group_id", "panelist_id", "condition_id")
            if key in records[0]
        },
        "training_fingerprint": digest(records),
        "runtime_M2_input": False,
    }


def predict(measurements, model):
    kind = model["kind"]
    if (
        model["version"] != VERSION
        or model["views"] != views(kind)
        or set(model["heads"]) != set(targets(kind))
    ):
        raise ValueError("PROFILE_MODEL_CONTRACT_MISMATCH")
    out = {}
    for target, head in model["heads"].items():
        if target not in views(kind)[head["held_view"]]:
            raise ValueError("TARGET_VIEW_MISMATCH")
        x = encode(measurements, kind, head["held_view"], head["input_concepts"])
        if x is None:
            out[target] = None
        elif kind == "rocchetti":
            z = (x - np.asarray(head["feature_mean"])) / np.asarray(
                head["feature_scale"]
            )
            out[target] = float(
                np.clip(
                    head["target_mean"]
                    + head["target_scale"] * (z @ head["coefficients"]),
                    0,
                    9,
                )
            )
        else:
            out[target] = float(expit(x @ head["coefficients"] + head["intercept"]))
    return out


def evaluate(records, model, axis, fold, split):
    if set(model["training_identities"][axis]) & {r[axis] for r in records}:
        raise ValueError("OUTER_OR_INNER_HELD_IDENTITY_IN_TRAIN")
    kind, columns = model["kind"], targets(model["kind"])
    output = []
    for record in records:
        predicted = predict(record["attribute_measurements"], model)
        y = [value(record["attribute_measurements"].get(c), c, kind) for c in columns]
        p = [predicted[c] for c in columns]
        if any(x is None for x in y + p):
            raise ValueError("CANNOT_DROP_REGISTERED_EVALUATION_CELLS")
        y, p = np.asarray(y), np.asarray(p)
        prior = np.asarray([model["heads"][c]["prior"] for c in columns])
        loss = np.abs if kind == "rocchetti" else np.square
        output.append(
            {
                "record_id": record["record_id"],
                "unit": record[axis],
                "axis": axis,
                "coffee_group": record["group_id"],
                "fold": fold,
                "split": split,
                "truth": y.tolist(),
                "prediction": p.tolist(),
                "prior": prior.tolist(),
                "loss": loss(p - y).tolist(),
                "prior_loss": loss(prior - y).tolist(),
            }
        )
    return output


def folds(records, axis, salt):
    identities = sorted(
        {r[axis] for r in records}, key=lambda x: digest([VERSION, SEED, salt, axis, x])
    )
    if len(identities) < 3:
        raise ValueError("THREE_DISJOINT_INNER_UNITS_REQUIRED")
    return {identity: i % 3 for i, identity in enumerate(identities)}


def mean_loss(rows):
    units = defaultdict(list)
    for row in rows:
        units[row["unit"]].append(float(np.mean(row["loss"])))
    return float(np.mean([np.mean(v) for v in units.values()]))


def select_ridge(records, kind, axis, salt):
    assignments = folds(records, axis, salt)
    audit, candidate_rows = [], {ridge: [] for ridge in RIDGES[kind]}
    for fold in range(3):
        train = [r for r in records if assignments[r[axis]] != fold]
        held = [r for r in records if assignments[r[axis]] == fold]
        for ridge in RIDGES[kind]:
            model = fit(train, kind, ridge)
            candidate_rows[ridge].extend(
                evaluate(held, model, axis, fold, "INNER_SELECTION")
            )
        audit.append(
            {
                "fold": fold,
                "train_units": sorted({r[axis] for r in train}),
                "held_units": sorted({r[axis] for r in held}),
                "training_fingerprint": digest(train),
            }
        )
    scores = {ridge: mean_loss(rows) for ridge, rows in candidate_rows.items()}
    best = min(scores.values())
    selected = max(ridge for ridge, score in scores.items() if score <= best + 1e-12)
    return selected, {
        "selected_ridge": selected,
        "scores": scores,
        "inner_folds": audit,
        "training_fingerprint": digest(records),
        "selection_metric": "ALL_TARGET_UNIT_MACRO_LOSS",
    }


def summary(rows, columns, kind):
    def block(indices):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row["unit"]].append(
                [
                    float(np.mean(np.asarray(row[name])[indices]))
                    for name in ["prior_loss", "fixed_loss", "selected_loss"]
                ]
            )
        values = np.asarray([np.mean(grouped[key], axis=0) for key in sorted(grouped)])
        comparisons = {}
        rng = np.random.default_rng(SEED)
        bootstrap = rng.integers(0, len(values), (5000, len(values)))
        for a, b, name in [
            (2, 1, "P2_minus_P1"),
            (1, 0, "P1_minus_P0"),
            (2, 0, "P2_minus_P0"),
        ]:
            delta = values[:, a] - values[:, b]
            interval = np.quantile(delta[bootstrap].mean(1), [0.025, 0.975]).tolist()
            comparisons[name] = {
                "delta": float(delta.mean()),
                "paired_unit_95_interval": interval,
                "status": (
                    "SUPPORTED_IN_DECLARED_SCOPE"
                    if interval[1] < 0
                    else "NO_IMPROVEMENT" if interval[0] > 0 else "INCONCLUSIVE"
                ),
            }
        return {
            "held_units": len(values),
            "observations": len(rows),
            "evaluated_cells": len(rows) * len(indices),
            "loss": dict(zip(MODELS, values.mean(0).tolist())),
            **comparisons,
        }

    return {
        "macro": block(list(range(len(columns)))),
        "by_target": {target: block([i]) for i, target in enumerate(columns)},
        "by_view": {
            view: block([columns.index(c) for c in block_targets])
            for view, block_targets in views(kind).items()
        },
        "coverage": 1.0,
        "uncertainty": protocol()["uncertainty"],
        "per_target_intervals": protocol()["per_target_results"],
    }


def join_predictions(fixed, selected):
    if len(fixed) != len(selected):
        raise ValueError("MATCHED_BUDGET_ROWS_REQUIRED")
    joined = []
    for a, b in zip(fixed, selected):
        if any(
            a[key] != b[key]
            for key in ["record_id", "unit", "truth", "prior", "prior_loss"]
        ):
            raise ValueError("MATCHED_ROWS_TARGETS_OR_PRIOR_MISMATCH")
        joined.append(
            {
                key: a[key]
                for key in [
                    "record_id",
                    "unit",
                    "axis",
                    "coffee_group",
                    "fold",
                    "split",
                    "truth",
                    "prior",
                    "prior_loss",
                ]
            }
            | {
                "fixed_prediction": a["prediction"],
                "selected_prediction": b["prediction"],
                "fixed_loss": a["loss"],
                "selected_loss": b["loss"],
            }
        )
    return joined


def experiment(records, kind, axis, outer, prefix, history=None):
    """Run one task; caller has already checked and frozen its outer contract."""
    rows, audits, artifacts = [], [], []
    for fold in range(3):
        train = [r for r in records if outer[r[axis]] != fold]
        held = [r for r in records if outer[r[axis]] == fold]
        ridge, audit = select_ridge(train, kind, axis, "outer:" + str(fold))
        fixed, selected = fit(train, kind, 0.05), fit(train, kind, ridge)
        for name, model in [("fixed", fixed), ("selected", selected)]:
            path = Path(str(prefix) + f"_fold{fold}_{name}.model.json")
            save(path, model)
            if predict(held[0]["attribute_measurements"], model) != predict(
                held[0]["attribute_measurements"], read(path)
            ):
                raise AssertionError("RELOAD_PREDICTION_CHANGED")
            artifacts.append({"path": str(path), "sha256": sha(path)})
        rows.extend(
            join_predictions(
                evaluate(held, fixed, axis, fold, "DEVELOPMENT_OUTER"),
                evaluate(held, selected, axis, fold, "DEVELOPMENT_OUTER"),
            )
        )
        audit.update(outer_fold=fold, outer_held_units=sorted({r[axis] for r in held}))
        audits.append(audit)
        print(
            json.dumps(
                {
                    "task": str(prefix.name),
                    "outer_fold": fold,
                    "selected_ridge": ridge,
                    "held_units": len({r[axis] for r in held}),
                }
            ),
            flush=True,
        )
    final_ridge, final_audit = select_ridge(records, kind, axis, "final-development")
    final_fixed, final_selected = fit(records, kind, 0.05), fit(
        records, kind, final_ridge
    )
    for name, model in [("fixed", final_fixed), ("selected", final_selected)]:
        path = Path(str(prefix) + f"_final_{name}.model.json")
        save(path, model)
        artifacts.append({"path": str(path), "sha256": sha(path)})
    historical_rows = (
        join_predictions(
            evaluate(history, final_fixed, axis, None, "HISTORICAL_REGRESSION"),
            evaluate(history, final_selected, axis, None, "HISTORICAL_REGRESSION"),
        )
        if history
        else []
    )
    detail_path = Path(str(prefix) + "_evaluation.private.json")
    save(
        detail_path,
        {
            "targets": targets(kind),
            "outer_rows": rows,
            "historical_rows": historical_rows,
            "fold_audit": audits,
            "final_selection": final_audit,
        },
    )
    artifacts.append({"path": str(detail_path), "sha256": sha(detail_path)})
    return {
        "kind": kind,
        "holdout_axis": axis,
        "development": summary(rows, targets(kind), kind),
        "historical_regression": (
            summary(historical_rows, targets(kind), kind) if history else None
        ),
        "historical_status": (
            "PREVIOUSLY_INSPECTED_NOT_FRESH" if history else "NOT_EVALUATED"
        ),
        "selected_ridges": [a["selected_ridge"] for a in audits],
        "final_ridge": final_ridge,
        "other_view_cell_cost_per_target": {
            c: len(input_names(kind, view))
            for view, block in views(kind).items()
            for c in block
        },
        "cost_interpretation": protocol()["cost"],
        "model_artifacts": artifacts,
        "new_independent_products": 0,
        "main_M2_scoring_changed": False,
    }


def run(owner, contract_path):
    owner, contract_path = Path(owner), Path(contract_path)
    frozen = read(contract_path)
    if frozen.get("profiles") != protocol():
        raise ValueError("MAIN_FROZEN_PROFILE_CONTRACT_REQUIRED")
    private = owner / "revisions/r2"
    sources = {
        "rocchetti": owner
        / "revisions/r1/rocchetti_attribute_observations.private.json",
        "cotter": owner
        / "revisions/r1/cotter_full_attribute_observations.private.json",
    }
    records = {key: read(path) for key, path in sources.items()}
    professional.validate_records(
        records["rocchetti"],
        read(owner / "revisions/r1/rocchetti_split_preregistered.private.json"),
    )
    response.validate_full_cata(records["cotter"], expected_shape=(118, 27))
    plan = {
        "version": VERSION,
        "protocol": protocol(),
        "source_hashes": {key: sha(path) for key, path in sources.items()},
        "code_sha256": sha(Path(__file__)),
        "dependency_code_sha256": {
            "professional_views_m2_r1": sha(professional.__file__),
            "sensory_views_m2_r1": sha(response.__file__),
        },
        "main_contract_sha256": sha(contract_path),
    }
    plan["hash"] = digest(plan)
    result_path = private / "profiles_summary.private.json"
    plan_path = private / "profiles_plan.private.json"
    if plan_path.exists() and read(plan_path) != plan:
        raise ValueError("RETAINED_PROFILE_PLAN_CHANGED_EXPLICIT_REVISION_REQUIRED")
    if result_path.exists():
        old = read(result_path)
        if old["plan_hash"] != plan["hash"]:
            raise ValueError("RETAINED_PROFILE_RESULTS_CHANGED")
        for item in old["tasks"].values():
            for entry in item["model_artifacts"]:
                if sha(entry["path"]) != entry["sha256"]:
                    raise ValueError("RETAINED_PROFILE_ARTIFACT_CHANGED")
        return old
    save(plan_path, plan)
    started = time.monotonic()
    dev = [r for r in records["rocchetti"] if r["split"] == "DEVELOPMENT"]
    hist = [r for r in records["rocchetti"] if r["split"] == "CONFIRMATION"]
    tasks = {
        "rocchetti": experiment(
            dev,
            "rocchetti",
            "group_id",
            professional.fold_assignments(dev),
            private / "profiles_rocchetti",
            hist,
        )
    }
    for name, axis in response.FULL_CATA_AXES.items():
        tasks["cotter_" + name] = experiment(
            records["cotter"],
            "cotter",
            axis,
            response.full_cata_folds(records["cotter"], name),
            private / ("profiles_cotter_" + name),
        )
    result = {
        "version": VERSION,
        "plan_hash": plan["hash"],
        "tasks": tasks,
        "protocol": protocol(),
        "elapsed_seconds": time.monotonic() - started,
        "data_expansion_contribution": "NOT_EVALUATED_PENDING_ADMITTED_COMPATIBLE_DATA",
        "real_user_alignment": "NOT_EVALUATED",
        "real_user_time_efficiency": "NOT_EVALUATED",
        "main_M2_scoring_changed": False,
    }
    save(result_path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", type=Path)
    parser.add_argument("--contract-file", type=Path)
    parser.add_argument("--print-protocol", action="store_true")
    args = parser.parse_args()
    if args.print_protocol:
        print(json.dumps(protocol(), indent=2))
    elif args.owner_dir is None or args.contract_file is None:
        parser.error("--owner-dir and --contract-file are required for fitting")
    else:
        result = run(args.owner_dir, args.contract_file)
        print(
            json.dumps(
                {
                    key: value["development"]["macro"]
                    for key, value in result["tasks"].items()
                },
                indent=2,
            )
        )
