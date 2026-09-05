"""R3 fixed-universe matching, ranking and reachability diagnostics.

Authored semantic proxies, not calibrated psychological distance. R2 unchanged.
"""

from __future__ import annotations

import math
import numpy as np
from scipy.optimize import linear_sum_assignment

from flavor_m2_r1 import PARENTS, digest

VERSION = "m2-r3.fixed-universe-matching-and-ranked-recovery.v1"


def protocol():
    return {
        "version": VERSION,
        "primary": "raw_gap=1-M/number_of_distinct_positive_fine_hidden_targets",
        "primary_k": 5,
        "primary_similarity": {
            "exact_fine": 1.0,
            "registered_shared_parent": 0.25,
            "otherwise": 0.0,
        },
        "relation_hash": digest(PARENTS),
        "external_relation_partial_credit": "Separate diagnostic only; empty until independent relations are registered; training associations cannot grade themselves",
        "rank_metric": "Linear positive target relevance DCG by predicted rank / ideal sorted target DCG at same k; deduplicated predictions; all fixed targets retained in IDCG",
        "candidate_universe": "Frozen base-expert legal fine universe before any model soft priority/filter; exclude fixed visible A for all variants",
        "matching": "One-to-one maximum-weight bipartite assignment; k-cardinality assignment for fixed-universe M_star",
        "opportunity_gap": "1-M/M_star only if M_star>0; diagnostic, not a replacement denominator for primary raw_gap",
        "capacity_floor": "1-min(k,|T|)/|T|, a capacity-only ideal with hypothetical exact coverage",
        "vocabulary_relation_extra_floor": "(min(k,|T|)-M_star)/|T|",
        "wrong_pruning_extra_floor": "(M_star-M_star_after_soft_filter)/|T|; denominator always original fixed universe",
        "threshold": "Raw gap<=0.5 reachable iff M_star>=0.5*|T|; target_count>5 alone is insufficient",
        "empty_targets": "Unidentifiable: null gaps/NDCG/Recall; retained full-case coverage",
        "missing_output": "With target: gap1/Recall0/NDCG0, retained as failure",
        "duplicate_ids": "Predictions deduplicated before k; fixed candidate duplicates rejected; duplicate target list entries collapse once",
        "unknown_parents": "No partial credit, including None==None",
        "batch_alignment": "Exact unique IDs and equal lengths; explicit error instead of zip truncation or incidental row order",
    }


def _ids(values):
    result = []
    for item in values:
        identity = item.get("candidate_id") if isinstance(item, dict) else item
        if not isinstance(identity, str) or not identity:
            raise ValueError("NONEMPTY_STRING_ID_REQUIRED")
        result.append(identity)
    return result


def _target_weights(targets):
    if isinstance(targets, dict):
        weights = {}
        for key, value in targets.items():
            _ids([key])
            if (
                not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError("FINITE_NONNEGATIVE_TARGET_RELEVANCE_REQUIRED")
            if value > 0 and key.startswith("sensory."):
                weights[key] = float(value)
        return weights
    return {key: 1.0 for key in _ids(targets) if key.startswith("sensory.")}


def similarity(a, b, mode="parent", relations=None):
    if not a.startswith("sensory.") or not b.startswith("sensory."):
        return 0.0
    if a == b:
        return 1.0
    if mode == "exact":
        return 0.0
    pa, pb = set(PARENTS.get(a) or ()), set(PARENTS.get(b) or ())
    partial = 0.25 if pa and pb and pa & pb else 0.0
    if mode == "relation":
        value = (relations or {}).get(tuple(sorted((a, b))), 0.0)
        if (
            not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0 <= value < 1
        ):
            raise ValueError("INDEPENDENT_PARTIAL_RELATION_WEIGHT_OUT_OF_RANGE")
        return max(partial, float(value))
    if mode != "parent":
        raise ValueError("UNREGISTERED_MATCHING_MODE")
    return partial


def maximum_matching(candidates, targets, k, mode="parent", relations=None):
    """Exact k-cardinality maximum weight via dummy-augmented assignment.

    Bottom dummy rows must occupy |T|-k true columns, leaving exactly k real
    candidate-to-target edges; zero edges allow fewer than k positive matches.
    """
    candidates, targets = list(dict.fromkeys(candidates)), list(dict.fromkeys(targets))
    cap = min(k, len(candidates), len(targets))
    if cap <= 0:
        return 0.0
    nc, nt = len(candidates), len(targets)
    values = np.asarray(
        [[similarity(c, t, mode, relations) for t in targets] for c in candidates]
    )
    size = nc + nt - cap
    costs = np.zeros((size, size))
    costs[:nc, :nt] = -values
    costs[nc:, nt:] = size + 1.0
    rows, cols = linear_sum_assignment(costs)
    if any(row >= nc and col >= nt for row, col in zip(rows, cols, strict=True)):
        raise AssertionError("INVALID_CARDINALITY_ASSIGNMENT")
    return float(
        sum(
            values[row, col]
            for row, col in zip(rows, cols, strict=True)
            if row < nc and col < nt
        )
    )


def ndcg(ranking, relevance, k=5):
    if k < 1:
        raise ValueError("POSITIVE_K_REQUIRED")
    weights = _target_weights(relevance)
    if not weights:
        return None
    predicted = list(dict.fromkeys(_ids(ranking)))[:k]
    ideal = sum(
        v / math.log2(i + 2)
        for i, v in enumerate(sorted(weights.values(), reverse=True)[:k])
    )
    dcg = sum(weights.get(c, 0.0) / math.log2(i + 2) for i, c in enumerate(predicted))
    return dcg / ideal


def evaluate(
    ranking,
    targets,
    fixed_candidates,
    excluded_visible=(),
    k=5,
    soft_candidates=None,
    mode="parent",
    relations=None,
):
    if not isinstance(k, int) or k < 1:
        raise ValueError("POSITIVE_INTEGER_K_REQUIRED")
    weights = _target_weights(targets)
    target_ids = sorted(weights)
    all_ids = _ids(fixed_candidates)
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("FIXED_UNIVERSE_IDS_MUST_BE_UNIQUE")
    visible = set(_ids(excluded_visible))
    universe = [c for c in all_ids if c.startswith("sensory.") and c not in visible]
    allowed = set(universe)
    predicted = list(dict.fromkeys(c for c in _ids(ranking) if c in allowed))[:k]
    soft = allowed if soft_candidates is None else set(_ids(soft_candidates))
    if not soft <= set(all_ids):
        raise ValueError("SOFT_SET_CANNOT_EXTEND_FIXED_UNIVERSE")
    soft &= allowed
    match = maximum_matching(predicted, target_ids, k, mode, relations)
    best = maximum_matching(universe, target_ids, k, mode, relations)
    after = maximum_matching(sorted(soft), target_ids, k, mode, relations)
    n = len(target_ids)
    exact = len(set(predicted) & set(target_ids))
    return {
        "metric_version": VERSION,
        "matching_mode": mode,
        "target_count": n,
        "prediction_count": len(predicted),
        "prediction_available": bool(predicted),
        "fixed_candidate_count": len(universe),
        "M": match,
        "M_star": best,
        "M_star_after_soft_filter": after,
        "raw_gap": 1 - match / n if n else None,
        "gap": 1 - match / n if n else None,
        "opportunity_gap": 1 - match / best if best > 0 else None,
        "capacity_floor": 1 - min(k, n) / n if n else None,
        "vocabulary_relation_extra_floor": (min(k, n) - best) / n if n else None,
        "fixed_universe_best_raw_gap": 1 - best / n if n else None,
        "wrong_pruning_extra_floor": (best - after) / n if n else None,
        "threshold_0_5_reachable": best >= n * 0.5 - 1e-12 if n else None,
        "exact_set_recall": exact / n if n else None,
        "recall": exact / n if n else None,
        "ndcg": ndcg(predicted, weights, k),
        "fine_target_exact_coverage": len(set(target_ids) & allowed) / n if n else None,
        "fixed_universe_sha256": digest(sorted(universe)),
    }


def align_by_id(prediction_ids, predictions, target_ids, targets):
    if len(prediction_ids) != len(predictions) or len(target_ids) != len(targets):
        raise ValueError("ID_VALUE_LENGTH_MISMATCH")
    if len(set(prediction_ids)) != len(prediction_ids) or len(set(target_ids)) != len(
        target_ids
    ):
        raise ValueError("DUPLICATE_BATCH_ID")
    if set(prediction_ids) != set(target_ids):
        raise ValueError("BATCH_ID_SETS_DIFFER")
    lookup = dict(zip(target_ids, targets, strict=True))
    return [
        (key, prediction, lookup[key])
        for key, prediction in zip(prediction_ids, predictions, strict=True)
    ]
