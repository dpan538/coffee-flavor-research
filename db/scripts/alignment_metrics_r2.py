"""Frozen R2 semantic recovery and information-budget metrics.

These are record-recovery proxies, not calibrated perceptual distances.
The R1 authored taxonomy is fixed before R2 fitting and is never re-estimated.
"""

from __future__ import annotations

from collections import defaultdict
import math

import numpy as np
from scipy.optimize import linear_sum_assignment

from flavor_m2_r1 import PARENTS, digest

METRIC_VERSION = "r2.fixed-taxonomy-one-to-one-recovery.v1"
SEMANTIC_RELATION_HASH = digest(PARENTS)


def similarity(predicted, reference):
    if not predicted.startswith("sensory.") or not reference.startswith("sensory."):
        return 0.0
    if predicted == reference:
        return 1.0
    return (
        0.25
        if set(PARENTS.get(predicted, ())) & set(PARENTS.get(reference, ()))
        else 0.0
    )


def semantic_result(ranking, hidden_targets, excluded_visible=(), k=5, vocabulary=None):
    """One prediction may support at most one distinct held-out positive target.

    The fixed visible partition is removed before taking the recovery panel.
    Out-of-vocabulary targets remain in the denominator. Empty targets are
    unidentifiable, while a failed prediction with targets has maximum gap.
    """
    if k != 5:
        raise ValueError("R2_PRIMARY_OUTPUT_BUDGET_IS_FIVE")
    if isinstance(hidden_targets, dict):
        target_ids = [c for c, value in hidden_targets.items() if value > 0]
    else:
        target_ids = list(hidden_targets)
    targets = sorted({c for c in target_ids if c.startswith("sensory.")})
    visible = set(excluded_visible)
    allowed = None if vocabulary is None else set(vocabulary)
    predicted = []
    for item in ranking:
        candidate = item["candidate_id"] if isinstance(item, dict) else item
        if (
            candidate.startswith("sensory.")
            and candidate not in visible
            and candidate not in predicted
            and (allowed is None or candidate in allowed)
        ):
            predicted.append(candidate)
        if len(predicted) == k:
            break
    result = {
        "gap": None,
        "target_count": len(targets),
        "prediction_count": len(predicted),
        "exact_matches": 0,
        "related_matches": 0,
        "weighted_matches": 0.0,
        "candidate_target_coverage": (
            sum(allowed is None or c in allowed for c in targets) / len(targets)
            if targets
            else None
        ),
        "prediction_available": bool(predicted),
        "metric_version": METRIC_VERSION,
    }
    if not targets:
        return result
    if predicted:
        values = np.array([[similarity(p, t) for t in targets] for p in predicted])
        rows, cols = linear_sum_assignment(-values)
        matched = values[rows, cols]
        result["exact_matches"] = int(np.sum(matched == 1))
        result["related_matches"] = int(np.sum(matched == 0.25))
        result["weighted_matches"] = float(matched.sum())
    result["gap"] = 1.0 - result["weighted_matches"] / len(targets)
    return result


def semantic_gap(ranking, hidden_targets, excluded_visible=(), k=5, vocabulary=None):
    return semantic_result(ranking, hidden_targets, excluded_visible, k, vocabulary)[
        "gap"
    ]


def grouped_values(rows, key="gap"):
    groups = defaultdict(list)
    for row in rows:
        if row.get(key) is not None:
            value = float(row[key])
            if not math.isfinite(value):
                raise ValueError("NONFINITE_METRIC")
            groups[row["group_id"]].append(value)
    return {group: float(np.mean(values)) for group, values in groups.items()}


def grouped_summary(rows, key="gap"):
    values = grouped_values(rows, key)
    return {
        "records": len(rows),
        "groups": len({row["group_id"] for row in rows}),
        "labelled_records": sum(row.get(key) is not None for row in rows),
        "labelled_groups": len(values),
        "group_macro_mean": float(np.mean(list(values.values()))) if values else None,
        "full_coverage_denominator_retained": True,
    }


def paired_group_delta(experiment, baseline, key="gap", seed=20260906):
    """Experiment minus baseline; negative is favorable for a gap or a cost."""
    left, right = grouped_values(experiment, key), grouped_values(baseline, key)
    if set(left) != set(right):
        raise ValueError("PAIRED_EVALUATION_GROUPS_DIFFER")
    differences = np.array([left[g] - right[g] for g in sorted(left)])
    if not len(differences):
        return {"delta": None, "groups": 0, "status": "NOT_ESTIMABLE"}
    delta = float(differences.mean())
    if len(differences) < 10:
        return {
            "delta": delta,
            "groups": len(differences),
            "status": "INCONCLUSIVE",
            "group_delta_range": [float(differences.min()), float(differences.max())],
            "paired_group_95_interval": None,
        }
    rng = np.random.default_rng(seed)
    means = rng.choice(differences, (2000, len(differences)), replace=True).mean(axis=1)
    lo, hi = (float(x) for x in np.quantile(means, [0.025, 0.975]))
    return {
        "delta": delta,
        "groups": len(differences),
        "paired_group_95_interval": [lo, hi],
        "status": (
            "SUPPORTED_IN_DECLARED_SCOPE"
            if hi < 0
            else "NO_IMPROVEMENT" if lo > 0 else "INCONCLUSIVE"
        ),
        "scope": "NESTED_DEVELOPMENT_RECORD_PROXY; NOT_REAL_USER_EFFICACY",
    }


def information_cost(state):
    answers = state["answers_by_question"].values()
    final = state.get("final_comparison")
    return {
        "ordinary_questions": len(state["answers_by_question"]),
        "ordinary_options": sum(len(a["shown_option_ids"]) for a in answers),
        "final_comparison_candidates": len(final["exposed_candidates"]) if final else 0,
        "human_response_seconds": None,
        "time_evaluation": "NOT_EVALUATED",
    }
