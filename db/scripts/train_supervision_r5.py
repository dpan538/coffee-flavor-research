"""Fixed-capacity positive-mention head for isolated R5 supervision comparisons.

Softmax describes a conditional mention ranking, never sensory presence/absence.
Question generation remains in the frozen, separately isolated R4 engine.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

import alignment_metrics_r3 as metric
from flavor_m2_r1 import PARENTS, digest

VERSION = "m2-r5.positive-mention-linear.v1"
CANDIDATES = sorted(c for c in PARENTS if c.startswith("sensory."))
INPUTS = sorted(PARENTS)


def protocol():
    return {
        "version": VERSION,
        "task": "CROSS_GRADER_CORROBORATION_FULL_FIXED_REFERENCE",
        "candidate_universe": CANDIDATES,
        "inputs": INPUTS,
        "features": "Two fixed binary canonical-selection blocks, Q0/Q1 then later newly selected concepts; no coffee, grader, source, future answer or T feature",
        "capacity": [1 + 2 * len(INPUTS), len(CANDIDATES)],
        "T1": "Initial block only, later block zero; same allocated parameter capacity",
        "T2": "Initial and actually acquired later blocks; same question/option exposure as its information-ignored T1 control",
        "T3": "Same T2 family fitted with original R4 admitted training episodes versus all raw-role-admissible R5 training episodes; identical held cohorts and loss normalization",
        "loss": "Coffee-macro mean positive-mention cross entropy + 0.1/2 squared coefficient norm; unpenalized intercept, target positive frequencies normalized per record over fixed representable positives; OOV retained in evaluation",
        "ridge": 0.1,
        "optimizer": {
            "method": "L-BFGS-B",
            "maxiter": 500,
            "ftol": 1e-11,
            "gtol": 1e-7,
        },
        "scaling": "No fitted scaling: binary canonical selection; duplicate evidence once",
        "selection": "One configuration; no tuning by old five trigger cases or held losses",
        "evaluation": "Frozen R3 matching implementation with full T and no exclusion of A; fixed hidden subset full T minus source A exact reported separately",
        "learning_curve": "Deterministic hash-selected complete training groups at 50 and 100 percent, same held groups",
        "negative_control": "Rotate complete acquired-B feature bundles across training groups within source/condition/record-count strata; singleton strata unchanged and counted; no formal permutation p-value",
        "group_scope": "Original coffee dependence folds; shared graders, source and sometimes preparation categories; no participant/cross-source/general-product confirmation claim",
        "budget": "Question and exposed-option costs inherited from actual trace; T1 information-ignored matched-budget control also reported at initial-only cost; final comparison not observed, actual cost zero and NOT_EVALUATED",
        "trigger_gate": "Inspect actual new-Q3 information and independent positive groups in each outer training fold; no new fit if any has zero or support remains concentrated; diagnostics cannot authorize more complex routing",
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
    }


def features(row, variant="T2", branch="ASK"):
    a = set(row["initial_selected"])
    later = set(row["selected"][branch]) - a if variant != "T1" else set()
    return np.array(
        [1.0] + [float(c in a) for c in INPUTS] + [float(c in later) for c in INPUTS]
    )


def targets(row):
    values = np.array([float(row["full_T"].get(c, 0)) for c in CANDIDATES])
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("FINITE_POSITIVE_REFERENCE_REQUIRED")
    return values / values.sum() if values.sum() else None


def weights(rows):
    counts = Counter(r["group_id"] for r in rows)
    return np.array([1 / counts[r["group_id"]] / len(counts) for r in rows])


def fit(rows, variant, lineage):
    usable = [r for r in rows if targets(r) is not None]
    if not usable:
        raise ValueError("NO_IDENTIFIABLE_TRAINING_REFERENCE")
    x = np.stack([features(r, variant) for r in usable])
    y = np.stack([targets(r) for r in usable])
    w = weights(usable)
    shape = (x.shape[1], y.shape[1])
    initial = np.zeros(shape)
    prior = w @ y + 1e-4
    initial[0] = np.log(prior / prior.sum())

    def objective(flat):
        coef = flat.reshape(shape)
        logits = x @ coef
        logs = logits - logsumexp(logits, axis=1, keepdims=True)
        loss = -np.sum(w[:, None] * y * logs) + 0.05 * np.sum(coef[1:] ** 2)
        gradient = x.T @ (w[:, None] * (np.exp(logs) - y))
        gradient[1:] += 0.1 * coef[1:]
        return float(loss), gradient.ravel()

    result = minimize(
        objective,
        initial.ravel(),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 500, "ftol": 1e-11, "gtol": 1e-7},
    )
    if not result.success or not np.all(np.isfinite(result.x)):
        raise ValueError("R5_FIT_DID_NOT_CONVERGE:" + str(result.message))
    return {
        "version": VERSION,
        "protocol_sha256": digest(protocol()),
        "variant": variant,
        "candidates": CANDIDATES,
        "inputs": INPUTS,
        "coefficients": result.x.reshape(shape).tolist(),
        "training_groups": sorted({r["group_id"] for r in rows}),
        "usable_training_records": len(usable),
        "unidentifiable_training_records": len(rows) - len(usable),
        "lineage": lineage,
        "optimization": {
            "success": bool(result.success),
            "iterations": int(result.nit),
            "objective": float(result.fun),
        },
    }


def check_model(model):
    if (
        model["version"] != VERSION
        or model["protocol_sha256"] != digest(protocol())
        or model["candidates"] != CANDIDATES
        or model["inputs"] != INPUTS
    ):
        raise ValueError("R5_MODEL_CONTRACT_MISMATCH")
    coef = np.asarray(model["coefficients"])
    if coef.shape != (1 + 2 * len(INPUTS), len(CANDIDATES)) or not np.all(
        np.isfinite(coef)
    ):
        raise ValueError("R5_MODEL_INVALID_WEIGHTS")


def predict(row, model, branch="ASK"):
    check_model(model)
    logits = features(row, model["variant"], branch) @ np.asarray(model["coefficients"])
    return (
        sorted(CANDIDATES, key=lambda c: (-float(logits[CANDIDATES.index(c)]), c)),
        logits,
    )


def evaluate(row, ranking, logits=None, branch="ASK"):
    full = metric.evaluate(ranking, row["full_T"], CANDIDATES)
    hidden = metric.evaluate(ranking, row["hidden_T"], CANDIDATES)
    legacy = metric.evaluate(
        ranking, row["hidden_T"], CANDIDATES, excluded_visible=row.get("A", [])
    )
    initial = {c for c in row["initial_selected"] if c in CANDIDATES}
    direct = {c for c in row["selected"][branch] if c in CANDIDATES}
    target_set = {c for c, w in row["full_T"].items() if w > 0}
    top = set(ranking[:5])
    y = targets(row)
    return {
        "record_id": row["record_id"],
        "group_id": row["group_id"],
        "raw_gap": full["raw_gap"],
        "ndcg": full["ndcg"],
        "recall": full["recall"],
        "hidden_gap": hidden["raw_gap"],
        "hidden_ndcg": hidden["ndcg"],
        "legacy_R4_recovery_gap": legacy["raw_gap"],
        "direct_exact_contribution": (
            len(top & target_set & direct) / len(target_set) if target_set else None
        ),
        "initial_exact_contribution": (
            len(top & target_set & initial) / len(target_set) if target_set else None
        ),
        "later_exact_contribution": (
            len((top & target_set & direct) - initial) / len(target_set)
            if target_set
            else None
        ),
        "inferred_exact_contribution": (
            len((top & target_set) - direct) / len(target_set) if target_set else None
        ),
        "direct_retention": len(top & direct) / len(direct) if direct else None,
        "coverage": full["fine_target_exact_coverage"],
        "positive_mention_CE": (
            float(-np.dot(y, logits - logsumexp(logits)))
            if y is not None and logits is not None
            else None
        ),
    }


def aggregate(rows):
    keys = [
        "raw_gap",
        "ndcg",
        "recall",
        "hidden_gap",
        "hidden_ndcg",
        "legacy_R4_recovery_gap",
        "direct_exact_contribution",
        "initial_exact_contribution",
        "later_exact_contribution",
        "inferred_exact_contribution",
        "direct_retention",
        "coverage",
        "positive_mention_CE",
    ]
    result = {
        "records": len(rows),
        "groups": len({r["group_id"] for r in rows}),
        "identifiable_records": sum(r["raw_gap"] is not None for r in rows),
    }
    for key in keys:
        grouped = defaultdict(list)
        for row in rows:
            if row.get(key) is not None:
                grouped[row["group_id"]].append(row[key])
        result[key] = (
            float(np.mean([np.mean(v) for v in grouped.values()])) if grouped else None
        )
    return result


def paired(left, right, key="raw_gap"):
    index = {r["record_id"]: r for r in right}
    if (
        len(index) != len(right)
        or len({r["record_id"] for r in left}) != len(left)
        or set(index) != {r["record_id"] for r in left}
    ):
        raise ValueError("PAIRED_ID_ALIGNMENT_MISMATCH")
    grouped = defaultdict(list)
    for row in left:
        other = index[row["record_id"]]
        if row["group_id"] != other["group_id"]:
            raise ValueError("PAIRED_GROUP_MISMATCH")
        if row.get(key) is not None and other.get(key) is not None:
            grouped[row["group_id"]].append(other[key] - row[key])
    values = np.array([np.mean(v) for _, v in sorted(grouped.items())])
    if not len(values):
        return {"groups": 0, "delta_right_minus_left": None}
    rng = np.random.default_rng(20260906)
    boot = np.mean(rng.choice(values, (2000, len(values)), replace=True), axis=1)
    return {
        "groups": len(values),
        "delta_right_minus_left": float(values.mean()),
        "paired_coffee_bootstrap_95": np.quantile(boot, [0.025, 0.975]).tolist(),
        "scope": "Development fixed OOF descriptive uncertainty; not fresh confirmation/noninferiority",
    }


def subset(rows, fraction):
    groups = sorted(
        {r["group_id"] for r in rows},
        key=lambda g: hashlib.sha256(("R5-learning|" + g).encode()).hexdigest(),
    )
    chosen = set(groups[: max(1, int(len(groups) * fraction))])
    return [r for r in rows if r["group_id"] in chosen]


def mismatch(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["group_id"]].append(row)
    strata = defaultdict(list)
    for group, values in grouped.items():
        key = (
            tuple(
                sorted(
                    {
                        str(r.get("condition_key", "UNVERIFIED_CONDITION"))
                        for r in values
                    }
                )
            ),
            len(values),
        )
        strata[key].append(group)
    donors = {}
    for groups in strata.values():
        groups.sort()
        for i, group in enumerate(groups):
            donors[group] = groups[(i + 1) % len(groups)]
    output, changed = [], 0
    for group, values in grouped.items():
        donor = sorted(grouped[donors[group]], key=lambda r: r["record_id"])
        for row, replacement in zip(
            sorted(values, key=lambda r: r["record_id"]), donor, strict=True
        ):
            later = set(replacement["selected"]["ASK"]) - set(
                replacement["initial_selected"]
            )
            value = dict(row)
            value["selected"] = dict(
                row["selected"], ASK=sorted(set(row["initial_selected"]) | later)
            )
            output.append(value)
            changed += donors[group] != group
    return output, {
        "changed_records": changed,
        "singleton_stratum_records_unchanged": len(rows) - changed,
        "p_value": "NOT_ESTIMATED",
    }
