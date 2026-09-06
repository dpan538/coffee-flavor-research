"""R6 parameterized version of the frozen R5 positive-mention linear head.

This module neither selects an acquisition policy nor generates questions. The
caller supplies the actual endpoint in ``selected[branch]``. Softmax is a
conditional mention retrieval normalizer, not a sensory absence model.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from numbers import Real

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from flavor_m2_r1 import digest
import train_supervision_r5 as previous

VERSION = "m2-r6.positive-mention-linear.v1"
CANDIDATES = list(previous.CANDIDATES)
INPUTS = list(previous.INPUTS)
RIDGES = (0.03, 0.1, 0.3)
VARIANTS = ("T1", "T2", "T3")
SHAPE = (1 + 2 * len(INPUTS), len(CANDIDATES))
OPTIMIZER = {"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7}


def protocol():
    return {
        "version": VERSION,
        "parent_version": previous.VERSION,
        "candidate_universe": list(CANDIDATES),
        "inputs": list(INPUTS),
        "capacity": list(SHAPE),
        "features": "Intercept and two fixed binary canonical-selection blocks: initial_selected, then selected[branch] minus initial_selected; no identities, source, raw A/B, future answers or target features",
        "endpoint": "Caller passes the actually acquired endpoint as selected[branch]; default branch ASK has no hardcoded I1 or policy interpretation",
        "T1": "Initial block only; later block zero with identical allocated capacity",
        "T2": "Initial block plus newly acquired selected concepts",
        "T3": "T2 feature family; caller alone supplies any declared training cohort",
        "target": "Positive reference frequencies normalized per usable record over fixed representable fine candidates; unmentioned candidates participate only in the retrieval normalizer, never as measured sensory absence",
        "loss": "-sum(w[:,None]*y*log_softmax(X@coef)) + ridge/2*sum(coef[1:]**2)",
        "gradient": "X.T@(w[:,None]*(softmax(X@coef)-y)); add ridge*coef[1:] to non-intercept rows only",
        "ridge_grid": list(RIDGES),
        "parameter_meaning": "Direct ridge penalty, not inverse C; intercept unpenalized",
        "weights": "Among usable training records, each coffee group has equal total mass and records within each group share its mass; total data-loss mass is one for every fit",
        "unidentifiable_reference": "Empty or all-OOV positive T has no identifiable training loss; counted separately, retained in evaluation and its full target denominator",
        "scaling": "Binary features without fitted scaler; duplicate concepts count once",
        "optimizer": {"method": "L-BFGS-B", **OPTIMIZER},
        "selection": "Caller chooses ridge on isolated inner coffee groups only; fit performs no search or policy selection",
        "evaluation": "Unchanged R5 evaluation using frozen R3 full-T matching and fixed candidate universe; initial/selected overlap remains in full T; hidden subset reported separately",
        "scope": "Development comparisons using inherited coffee-group splits, not fresh confirmation",
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
    }


def _variant(variant):
    if variant not in VARIANTS:
        raise ValueError("R6_INVALID_VARIANT")


def _ridge(ridge):
    if (
        isinstance(ridge, bool)
        or not isinstance(ridge, Real)
        or not np.isfinite(ridge)
        or float(ridge) not in RIDGES
    ):
        raise ValueError("R6_RIDGE_MUST_BE_0.03_0.1_OR_0.3")
    return float(ridge)


def _concepts(value, field):
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError("R6_CANONICAL_SEQUENCE_REQUIRED:" + field)
    if any(not isinstance(c, str) or c not in INPUTS for c in value):
        raise ValueError("R6_REGISTERED_CANONICAL_CONCEPT_REQUIRED:" + field)
    return set(value)


def _observed(row, branch):
    if not isinstance(row, Mapping):
        raise ValueError("R6_OBSERVATION_MAPPING_REQUIRED")
    if not isinstance(branch, str) or not branch:
        raise ValueError("R6_BRANCH_REQUIRED")
    selected = row.get("selected")
    if not isinstance(selected, Mapping) or branch not in selected:
        raise ValueError("R6_ACTUAL_SELECTED_BRANCH_REQUIRED:" + branch)
    return (
        _concepts(row.get("initial_selected"), "initial_selected"),
        _concepts(selected[branch], "selected[" + branch + "]"),
    )


def features(row, variant="T2", branch="ASK"):
    """The fit/live feature path deliberately never reads any target field."""
    _variant(variant)
    initial, selected = _observed(row, branch)
    later = selected - initial if variant != "T1" else set()
    return np.array(
        [1.0]
        + [float(c in initial) for c in INPUTS]
        + [float(c in later) for c in INPUTS]
    )


def _reference(row, key):
    values = row.get(key) if isinstance(row, Mapping) else None
    if not isinstance(values, Mapping):
        raise ValueError("R6_REFERENCE_MAPPING_REQUIRED:" + key)
    for concept, weight in values.items():
        if (
            not isinstance(concept, str)
            or not concept
            or isinstance(weight, bool)
            or not isinstance(weight, Real)
            or not np.isfinite(weight)
            or weight < 0
        ):
            raise ValueError("FINITE_POSITIVE_REFERENCE_REQUIRED:" + key)
    return values


def targets(row):
    reference = _reference(row, "full_T")
    values = np.array([float(reference.get(c, 0)) for c in CANDIDATES])
    # Divide by max before summing so valid large finite frequencies stay finite.
    maximum = values.max()
    if maximum == 0:
        return None
    values /= maximum
    return values / values.sum()


def _identity(row, key):
    if (
        not isinstance(row, Mapping)
        or not isinstance(row.get(key), str)
        or not row[key]
    ):
        raise ValueError("R6_NONEMPTY_ID_REQUIRED:" + key)
    return row[key]


def weights(rows):
    groups = [_identity(row, "group_id") for row in rows]
    counts = Counter(groups)
    return np.array([1.0 / counts[g] / len(counts) for g in groups], dtype=float)


def objective_and_gradient(flat, x, y, w, ridge=0.1):
    """Normalized positive-mention CE and its exact derivative, for audit/fit."""
    ridge = _ridge(ridge)
    x, y, w, flat = [np.asarray(v, dtype=float) for v in (x, y, w, flat)]
    if (
        x.ndim != 2
        or y.ndim != 2
        or not x.shape[0]
        or not x.shape[1]
        or not y.shape[1]
        or x.shape[0] != y.shape[0]
        or w.shape != (x.shape[0],)
        or flat.shape != (x.shape[1] * y.shape[1],)
        or any(not np.all(np.isfinite(v)) for v in (x, y, w, flat))
        or np.any(y < 0)
        or np.any(w <= 0)
        or not np.allclose(y.sum(axis=1), 1, rtol=0, atol=1e-12)
        or not np.isclose(w.sum(), 1, rtol=0, atol=1e-12)
        or not np.all(x[:, 0] == 1)
    ):
        raise ValueError("R6_NORMALIZED_OBJECTIVE_SCHEMA_REQUIRED")
    coef = flat.reshape(x.shape[1], y.shape[1])
    logits = x @ coef
    logp = logits - logsumexp(logits, axis=1, keepdims=True)
    loss = -np.sum(w[:, None] * y * logp) + 0.5 * ridge * np.sum(coef[1:] ** 2)
    gradient = x.T @ (w[:, None] * (np.exp(logp) - y))
    gradient[1:] += ridge * coef[1:]
    return float(loss), gradient.ravel()


def fit(rows, variant="T2", lineage=None, ridge=0.1, branch="ASK"):
    """One caller-declared ridge fit; never performs model/policy selection."""
    _variant(variant)
    ridge = _ridge(ridge)
    rows = list(rows)
    usable, target_values = [], []
    for row in rows:
        _identity(row, "group_id")
        _identity(row, "record_id")
        features(row, variant, branch)  # Validate even an unidentifiable row.
        target = targets(row)
        if target is not None:
            usable.append(row)
            target_values.append(target)
    if not usable:
        raise ValueError("NO_IDENTIFIABLE_TRAINING_REFERENCE")
    x = np.stack([features(r, variant, branch) for r in usable])
    y = np.stack(target_values)
    w = weights(usable)
    initial = np.zeros(SHAPE)
    prior = w @ y + 1e-4
    initial[0] = np.log(prior / prior.sum())
    result = minimize(
        objective_and_gradient,
        initial.ravel(),
        args=(x, y, w, ridge),
        jac=True,
        method="L-BFGS-B",
        options=dict(OPTIMIZER),
    )
    if not result.success or not np.all(np.isfinite(result.x)):
        raise ValueError("R6_FIT_DID_NOT_CONVERGE:" + str(result.message))
    model = {
        "version": VERSION,
        "protocol_sha256": digest(protocol()),
        "variant": variant,
        "ridge": ridge,
        "feature_branch_at_fit": branch,
        "candidates": list(CANDIDATES),
        "inputs": list(INPUTS),
        "coefficients": result.x.reshape(SHAPE).tolist(),
        "training_groups": sorted({r["group_id"] for r in rows}),
        "usable_training_groups": sorted({r["group_id"] for r in usable}),
        "usable_training_records": len(usable),
        "unidentifiable_training_records": len(rows) - len(usable),
        "training_data_weight_sum": float(w.sum()),
        "lineage": {} if lineage is None else lineage,
        "optimization": {
            "success": bool(result.success),
            "iterations": int(result.nit),
            "objective": float(result.fun),
        },
    }
    check_model(model)
    return model


def check_model(model):
    if not isinstance(model, Mapping) or (
        model.get("version") != VERSION
        or model.get("protocol_sha256") != digest(protocol())
        or model.get("candidates") != CANDIDATES
        or model.get("inputs") != INPUTS
    ):
        raise ValueError("R6_MODEL_CONTRACT_MISMATCH")
    _variant(model.get("variant"))
    _ridge(model.get("ridge"))
    try:
        coef = np.asarray(model.get("coefficients"), dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError("R6_MODEL_INVALID_WEIGHTS") from exc
    if coef.shape != SHAPE or not np.all(np.isfinite(coef)):
        raise ValueError("R6_MODEL_INVALID_WEIGHTS")


def predict(row, model, branch="ASK"):
    check_model(model)
    logits = features(row, model["variant"], branch) @ np.asarray(model["coefficients"])
    order = sorted(
        range(len(CANDIDATES)), key=lambda i: (-float(logits[i]), CANDIDATES[i])
    )
    return [CANDIDATES[i] for i in order], logits


def evaluate(row, ranking, logits=None, branch="ASK"):
    _observed(row, branch)
    _reference(row, "full_T")
    _reference(row, "hidden_T")
    _identity(row, "record_id")
    _identity(row, "group_id")
    if logits is not None:
        logits = np.asarray(logits, dtype=float)
        if logits.shape != (len(CANDIDATES),) or not np.all(np.isfinite(logits)):
            raise ValueError("R6_INVALID_EVALUATION_LOGITS")
    # Preserve the original metric and denominator; only the CE uses the
    # overflow-safe normalized target path above.
    result = previous.evaluate(row, ranking, None, branch)
    y = targets(row)
    result["positive_mention_CE"] = (
        float(-np.dot(y, logits - logsumexp(logits)))
        if y is not None and logits is not None
        else None
    )
    return result


aggregate = previous.aggregate
paired = previous.paired
