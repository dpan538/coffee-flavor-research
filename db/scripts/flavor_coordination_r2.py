"""Small frozen-session descriptor expert pool with one semantic constraint layer.

This is an R2 research coordinator. The existing default B2 is untouched. Expert
rank percentiles and routing weights are not calibrated sensory probabilities.
"""

from __future__ import annotations

import copy
import json
import math
import argparse
from pathlib import Path

import numpy as np
from scipy.special import expit
from scipy.stats import rankdata

import flavor_backend as b2
import flavor_m2_r1 as r1

VERSION = "m2-coordination.r2.v1"
EXPERTS = ["B2_TYPED_PRIOR_COMPONENT", "M2_R1_FINAL_FIXED_RESIDUAL"]
STAGES = ["INITIAL", "CORRECTION", "FINAL"]
FEATURES = [
    "stage_initial",
    "stage_correction",
    "stage_final",
    "known_broad_count",
    "explicit_specific_count",
    "independent_dimension_count",
    "log_mean_training_support",
    "rank_disagreement_mean",
    "top5_disagreement",
    "novel_final_feedback",
]
RESIDUAL_FEATURES = {
    "log_prior",
    "cooccurrence_mean",
    "cooccurrence_max",
    "source_support_log",
    "answer_pair_affinity",
}
SHARED = {"broad_compatibility": 0.25, "exposed_rejection": -1.0}


def check_bundle(bundle):
    if (
        bundle.get("version") != VERSION
        or bundle.get("expert_ids") != EXPERTS
        or bundle.get("feature_names") != FEATURES
        or bundle.get("shared_semantics") != SHARED
        or bundle.get("foundation_check_enabled") is not False
    ):
        raise ValueError("COORDINATOR_VERSION_OR_FROZEN_SEMANTICS_MISMATCH")
    expert = r1.check_bundle(bundle["r1_expert"])
    if not expert.get("evidence_policy", {}).get("canonical_broad_feedback"):
        raise ValueError("R1_FINAL_BROAD_REPAIR_REQUIRED")
    candidates = bundle["candidate_vocabulary"]
    expected = sorted(
        c
        for c in expert["candidate_vocabulary"]
        if c.startswith("sensory.") and c in b2.FAMILY
    )
    if candidates != expected:
        raise ValueError("FIXED_COMMON_FINE_CANDIDATE_SCOPE_REQUIRED")
    if bundle["router"]["feature_names"] != FEATURES:
        raise ValueError("ROUTER_FEATURE_WHITELIST_MISMATCH")
    if bundle.get("frozen_parameters_sha256") != r1.digest(
        [expert, bundle["router"], candidates, SHARED]
    ):
        raise ValueError("FROZEN_COORDINATOR_PARAMETERS_CHANGED")
    return bundle


def make_bundle(expert, router, contract_hash, tag=""):
    value = {
        "version": VERSION,
        "expert_ids": EXPERTS,
        "feature_names": FEATURES,
        "candidate_vocabulary": sorted(
            c
            for c in expert["candidate_vocabulary"]
            if c.startswith("sensory.") and c in b2.FAMILY
        ),
        "r1_expert": copy.deepcopy(expert),
        "router": copy.deepcopy(router),
        "shared_semantics": SHARED,
        "objective_contract_sha256": contract_hash,
        "foundation_check_enabled": False,
        "runtime_default_changed": False,
        "score_semantics": "WITHIN_EXPERT_RANK_PERCENTILE_NOT_SENSORY_PROBABILITY",
        "semantics_application_count": 1,
        "direct_effect": "ONE_CANONICAL_EXPLICIT_PRIORITY_NO_ADDITIVE_EXPERT_BONUSES",
    }
    value["frozen_parameters_sha256"] = r1.digest(
        [value["r1_expert"], value["router"], value["candidate_vocabulary"], SHARED]
    )
    value["bundle_id"] = "m2-r2:" + tag + ":" + r1.digest(value)[:20]
    return check_bundle(value)


def default_router():
    """Only an unfitted fixture/preregistered configuration, never a fitted claim."""
    return {
        "feature_names": FEATURES,
        "fit_status": "UNFITTED_CONFIGURATION",
        "single_expert_index": 0,
        "global_alpha": 0.5,
        "stage_alpha": dict.fromkeys(STAGES, 0.5),
        "feature_mean": [0.0] * len(FEATURES),
        "feature_scale": [1.0] * len(FEATURES),
        "advantage_intercept": 0.0,
        "advantage_coefficients": [0.0] * len(FEATURES),
        "stage_shrinkage": dict.fromkeys(STAGES, 0.0),
        "advantage_temperature": 0.1,
    }


def effective_stage(state):
    """Repeated final information cannot switch the routing stage or weights."""
    answers = state["answers_by_question"]
    if "Q4" in answers or "Q5" in answers:
        return "FINAL"
    if "Q2" in answers or "Q3" in answers:
        return "CORRECTION"
    return "INITIAL"


def midrank_percentile(values):
    values = np.asarray(values, float)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("FINITE_CANDIDATE_SCORES_REQUIRED")
    return (rankdata(values, method="average") - 0.5) / len(values)


def expert_predictions(state, bundle):
    check_bundle(bundle)
    expert = bundle["r1_expert"]
    if state["model_version"] != expert["bundle_id"]:
        raise ValueError("STATE_EXPERT_VERSION_MISMATCH")
    encoded = r1.encode_features(state, expert)
    evidence = encoded["interpreted_evidence"]
    candidates = bundle["candidate_vocabulary"]
    rows = {row["candidate_id"]: row for row in r1.compute_scores(encoded, expert)}
    raw = [
        [expert["statistics"]["log_prior"][c] for c in candidates],
        [
            sum(rows[c]["components"][f] for f in sorted(RESIDUAL_FEATURES))
            for c in candidates
        ],
    ]
    scores = [midrank_percentile(values).tolist() for values in raw]
    explicit = set(evidence["confirmed"])
    broad = set(evidence["independent_broad"])
    negative = set(evidence["negative_broad"])
    rejection, compatibility = [], []
    for candidate in candidates:
        parents = set(expert["candidate_attributes"].get(candidate, []))
        rejection.append(
            candidate in evidence["explicit_none"] or bool(parents & negative)
        )
        compatibility.append(candidate not in explicit and bool(parents & broad))
    support = [
        SHARED["broad_compatibility"] * wide + SHARED["exposed_rejection"] * rejected
        for wide, rejected in zip(compatibility, rejection)
    ]
    return {
        "candidate_ids": candidates,
        "expert_ids": EXPERTS,
        "raw_residual_scores": raw,
        "rank_percentile_scores": scores,
        "shared_semantic_scores": support,
        "explicit": [c in explicit for c in candidates],
        "rejected": rejection,
        "broadly_compatible": compatibility,
        "evidence": evidence,
        "stage": effective_stage(state),
    }


def live_features(state, predictions, bundle):
    """Only whitelisted current evidence, train support and expert disagreement."""
    evidence = predictions["evidence"]
    stage = predictions["stage"]
    dimensions = set(evidence["broad"])
    for concept in evidence["confirmed"]:
        dimensions.update(bundle["r1_expert"]["candidate_attributes"].get(concept, []))
    counts = bundle["r1_expert"]["statistics"]["counts"]
    observed = set(evidence["confirmed"]) | {
        "attribute." + attribute for attribute in evidence["independent_broad"]
    }
    support = np.mean([counts.get(c, 0) for c in observed]) if observed else 0.0
    a, b = [np.asarray(s) for s in predictions["rank_percentile_scores"]]
    ids = predictions["candidate_ids"]
    tops = [
        {
            ids[i]
            for i in sorted(range(len(ids)), key=lambda i: (-scores[i], ids[i]))[:5]
        }
        for scores in [a, b]
    ]
    values = [
        float(stage == "INITIAL"),
        float(stage == "CORRECTION"),
        float(stage == "FINAL"),
        float(len(evidence["independent_broad"])),
        float(sum(c.startswith("sensory.") for c in evidence["confirmed"])),
        float(len(dimensions)),
        float(math.log1p(support)),
        float(np.mean(np.abs(a - b))),
        1 - len(tops[0] & tops[1]) / max(len(tops[0] | tops[1]), 1),
        float(bool(evidence["novel_feedback"])),
    ]
    return dict(zip(FEATURES, values))


def route_from_features(features, stage, router, variant):
    if set(features) != set(FEATURES) or router["feature_names"] != FEATURES:
        raise ValueError("EXACT_LIVE_FEATURE_WHITELIST_REQUIRED")
    if variant == "G0":
        alpha = float(router["single_expert_index"])
    elif variant == "G1":
        alpha = router["global_alpha"]
    elif variant == "G2":
        alpha = router["stage_alpha"][stage]
    elif variant == "G3":
        x = np.asarray([features[f] for f in FEATURES])
        z = (x - np.asarray(router["feature_mean"])) / np.asarray(
            router["feature_scale"]
        )
        advantage = router["advantage_intercept"] + z @ np.asarray(
            router["advantage_coefficients"]
        )
        local = expit(advantage / router["advantage_temperature"])
        shrinkage = router["stage_shrinkage"][stage]
        alpha = (1 - shrinkage) * router["global_alpha"] + shrinkage * local
    else:
        raise ValueError("REGISTERED_G0_TO_G3_VARIANT_REQUIRED")
    if not np.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("INVALID_FROZEN_ROUTER_WEIGHT")
    return [1 - float(alpha), float(alpha)]


def route_weights(state, predictions, bundle, variant="G3"):
    return route_from_features(
        live_features(state, predictions, bundle),
        predictions["stage"],
        bundle["router"],
        variant,
    )


def rank_from_predictions(predictions, weights):
    if len(weights) != 2 or min(weights) < 0 or abs(sum(weights) - 1) > 1e-10:
        raise ValueError("CONVEX_EXPERT_WEIGHTS_REQUIRED")
    scores = np.asarray(weights) @ np.asarray(predictions["rank_percentile_scores"])
    scores += np.asarray(predictions["shared_semantic_scores"])
    rows = [
        {
            "candidate_id": candidate,
            "score": float(scores[i]),
            "explicit": predictions["explicit"][i],
            "specific_confirmation_eligible": predictions["explicit"][i]
            and not predictions["rejected"][i],
            "rejected_within_exposure": predictions["rejected"][i],
            "broadly_compatible": predictions["broadly_compatible"][i],
            "shared_semantic_score": predictions["shared_semantic_scores"][i],
        }
        for i, candidate in enumerate(predictions["candidate_ids"])
    ]
    raw = sorted(rows, key=lambda row: (-row["score"], row["candidate_id"]))
    ranks = {row["candidate_id"]: i for i, row in enumerate(raw, 1)}
    rows.sort(
        key=lambda row: (-int(row["explicit"]), -row["score"], row["candidate_id"])
    )
    for i, row in enumerate(rows, 1):
        row["rank"] = i
        row["raw_rank"] = ranks[row["candidate_id"]]
    return rows


def rank_candidates(state, bundle, variant="G3"):
    predictions = expert_predictions(state, bundle)
    features = live_features(state, predictions, bundle)
    weights = route_from_features(
        features, predictions["stage"], bundle["router"], variant
    )
    return {
        "candidate_scores": rank_from_predictions(predictions, weights),
        "routing_weights": dict(zip(EXPERTS, weights)),
        "routing_features": features,
        "effective_stage": predictions["stage"],
        "expert_predictions": predictions,
    }


def wrap_state(base_state, bundle, variant):
    return {
        "base_state": copy.deepcopy(base_state),
        "coordination_model_version": bundle["bundle_id"],
        "variant": variant,
        **rank_candidates(base_state, bundle, variant),
    }


def initial_state(context, bundle, path="P1", variant="G3"):
    check_bundle(bundle)
    if path not in {"P1", "P4"}:
        raise ValueError("R2_REGISTERED_FIXED_P1_OR_P4_REQUIRED")
    return wrap_state(
        r1.initial_state(context, bundle["r1_expert"], path, "fixed"), bundle, variant
    )


def update_state(state, answer, bundle):
    if state["coordination_model_version"] != bundle["bundle_id"]:
        raise ValueError("SESSION_COORDINATOR_PARAMETERS_CHANGED")
    base = r1.update_joint_state(state["base_state"], answer, bundle["r1_expert"])
    return wrap_state(base, bundle, state["variant"])


def finalize_result(state, bundle):
    if state["coordination_model_version"] != bundle["bundle_id"]:
        raise ValueError("SESSION_COORDINATOR_PARAMETERS_CHANGED")
    base = r1.finalize_result(state["base_state"], bundle["r1_expert"])
    current = wrap_state(base["state"], bundle, state["variant"])
    rows = current["candidate_scores"]
    exposure = None
    if base["stage"] == "PRELIMINARY_RESULT":
        ids = [row["candidate_id"] for row in rows[:8]]
        exposure = {
            "candidate_ids": ids,
            "generation_version": bundle["bundle_id"],
            "state_hash": r1.digest(
                [
                    base["state"]["context"],
                    base["state"]["answers_by_question"],
                    bundle["bundle_id"],
                    state["variant"],
                ]
            ),
            "eligible_for_final_comparison": 3 <= len(ids) <= 8,
        }
    return {
        "state": current,
        "main": rows[:5],
        "secondary": rows[5:8],
        "stage": base["stage"],
        "next": base["next"],
        "exposure": exposure,
    }


def apply_final_comparison(state, feedback, bundle):
    if state["base_state"]["final_comparison"]:
        raise ValueError("FINAL_COMPARISON_ALREADY_USED")
    if not isinstance(feedback, dict) or set(feedback) != {
        "exposed_candidates",
        "selected_candidates",
        "feedback_source",
        "generation_version",
    }:
        raise ValueError("FINAL_COMPARISON_SCHEMA_MISMATCH")
    result = finalize_result(state, bundle)
    exposure = result["exposure"]
    if not exposure or not exposure["eligible_for_final_comparison"]:
        raise ValueError("FINAL_COMPARISON_REQUIRES_PRELIMINARY_3_TO_8")
    if (
        feedback["generation_version"] != bundle["bundle_id"]
        or feedback["exposed_candidates"] != exposure["candidate_ids"]
    ):
        raise ValueError("EXPOSURE_OR_GENERATION_VERSION_MISMATCH")
    selected = feedback["selected_candidates"]
    if (
        feedback["feedback_source"] not in {"REAL_HUMAN", "SIMULATED"}
        or not isinstance(selected, list)
        or any(not isinstance(value, str) for value in selected)
        or len(selected) != len(set(selected))
        or not set(selected) <= set(exposure["candidate_ids"])
    ):
        raise ValueError("FINAL_FEEDBACK_SOURCE_OR_SUBSET_ERROR")
    base = result["state"]["base_state"]
    base["final_comparison"] = {
        **copy.deepcopy(feedback),
        "selected_candidates": sorted(selected),
        "mode": "F2",
    }
    base = r1.recompute(base, bundle["r1_expert"])
    return wrap_state(base, bundle, state["variant"])


def run(payload, bundle):
    if (
        not isinstance(payload, dict)
        or set(payload)
        - {
            "contract_version",
            "context",
            "path",
            "variant",
            "answers",
            "final_comparison",
        }
        or payload.get("contract_version") != VERSION
    ):
        raise ValueError("R2_REQUEST_CONTRACT_MISMATCH")
    if not isinstance(payload.get("answers", []), list):
        raise ValueError("ANSWERS_MUST_BE_ARRAY")
    state = initial_state(
        payload["context"],
        bundle,
        payload.get("path", "P1"),
        payload.get("variant", "G3"),
    )
    for batch in payload.get("answers", []):
        for answer in batch if isinstance(batch, list) else [batch]:
            state = update_state(state, answer, bundle)
    if "final_comparison" in payload:
        state = apply_final_comparison(state, payload["final_comparison"], bundle)
    return finalize_result(state, bundle)


def evaluation_entry(payload, bundle):
    return run(payload, bundle)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--request", "--payload-file", dest="request", required=True)
    args = parser.parse_args()
    bundle = json.loads(Path(args.model).read_text())
    payload = json.loads(Path(args.request).read_text())
    print(
        json.dumps(
            run(payload, bundle), ensure_ascii=False, sort_keys=True, allow_nan=False
        )
    )


if __name__ == "__main__":
    main()
