"""R4 pre-score conditioning and shared semantic pair residuals.

Research retrieval components, never sensory or response probabilities.  Earlier
model implementations and their frozen artifacts are deliberately untouched.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

import numpy as np

import flavor_m2_r1 as r1
import flavor_constraints_r3 as r3

VERSION = "m2-conditioning.r4.v1"
VARIANTS = ["A0", "AK", "AR", "AKR"]
POLICIES = ["ALWAYS_ASK", "ALWAYS_SKIP", "KEY_CASE", "R3_OLD"]
ATTRS = list(r1.ATTRS)
PAIR_SLOTS = [("Q0", "Q1"), ("Q0", "Q2"), ("Q1", "Q2")]
K1_FEATURES = [
    "k1.supported_association_mean",
    "k1.supported_association_spread",
    "k1.rejected_association_mean",
    "k1.conflicting_association_mean",
]
RELATION_FEATURES = [
    "pair." + a + "." + kind for a in ATTRS for kind in ["agreement", "complement"]
]
FEATURES = K1_FEATURES + RELATION_FEATURES
LIVE_FEATURES = [
    "supported_dimension_count",
    "rejected_dimension_count",
    "explicit_fine_count",
    "unknown_dimension_count",
    "positive_pair_count",
    "relation_feature_l1",
    "conditioning_delta_l1",
    "top5_base_disagreement",
    "previous_top5_change",
    "log_training_support",
]


def protocol():
    return {
        "runtime_version": VERSION,
        "variants": {
            "A0": "FULL_ORIGINAL_R3_E1",
            "AK": "E1_PLUS_K1_RESIDUAL",
            "AR": "E1_PLUS_SHARED_PAIR_RESIDUAL",
            "AKR": "E1_PLUS_JOINT_K1_AND_GATED_PAIR_RESIDUAL",
        },
        "dag": [
            "CURRENT_VALID_ANSWERS",
            "CANONICAL_EVIDENCE",
            "K1_BEFORE_SCORING",
            "SHARED_PAIR_FEATURES_AND_GATES",
            "CANDIDATE_SCORES",
            "Q2_DECISION",
        ],
        "candidate_feature_names": FEATURES,
        "candidate_feature_count": len(FEATURES),
        "attribute_axes": ATTRS,
        "k1_formula": [
            "support_fraction*association_mean",
            "support_fraction*(association_max-association_mean)",
            "explicit_rejection_fraction*association_mean",
            "support_and_rejection_fraction*association_mean",
        ],
        "association": "TRAIN_R1_CONDITIONAL_MENTION_MEAN_AND_MAX_FROM_CANONICAL_CONFIRMED_CONCEPTS_EXCLUDING_CANDIDATE",
        "pair_slots": [list(p) for p in PAIR_SLOTS],
        "pair_formula": "For each candidate attribute a, average x_i[a]*x_j[a] and (x_i[a]*mean_other(x_j,a)+x_j[a]*mean_other(x_i,a))/2 over available distinct-positive pairs; multiply candidate parent indicator/parent_count.",
        "semantic_vector": "Per-slot clipped multi-hot fixed parent vector. Each canonical concept occurs in earliest slot only. A broad concept entailed by any confirmed fine concept is removed from pair evidence. Whole compounds are not split into leaves.",
        "exposure": "Actual question ID, axis and shown scope retained as provenance; no full shown tuple or exact answer combination as learned feature key.",
        "gates": "AR=1; AKR=0 only for candidate explicitly rejected within an actual exposure or its explicitly rejected parent; otherwise 1 including unknown. Gate changes relation component only, never legal candidate mask.",
        "ownership": "Full R1 direct/broad/rejection components retained exactly once. K1 learns residual modulation of empirical association, not a second fixed direct or broad bonus. New feature rows are all zero for every canonical confirmed candidate.",
        "normalization": "TRAIN-only RMS positive scale with mean exactly zero; explicit boolean contract-valid candidate mask; stable legal-only log-softmax; no legal candidate returns a technical diagnostic.",
        "hard_mask": "ADMITTED_CONTRACT_CANDIDATES_ONLY; no context, low score, missing direction, or empirical compatibility deletion",
        "unknown": "All unknown K1 coordinates are zero and pair gates neutral; no user C0/C1 fallback added.",
        "trigger_feature_names": LIVE_FEATURES,
        "trigger_policies": POLICIES,
        "key_case_threshold": 0.5,
        "key_case_output_meaning": "UNCALIBRATED_WEIGHTED_CLASSIFICATION_SCORE_NOT_GAIN_OR_RESPONSE_PROBABILITY",
        "r3_old_threshold": 0.01,
        "ordinary_path": "P1_FIXED; Q2 ASK_Q3 or true SKIP_Q3 then mandatory Q4; no fabricated Q3 answer",
        "final": "One actual 3-to-8 candidate comparison; main<=5 secondary<=3; F0/F1 frozen ranking or F2 same scoring chain; then terminal",
        "foundation_check_enabled": False,
        "default_changed": False,
    }


def make_bundle(
    expert,
    model_parameters=None,
    trigger=None,
    r3_reference=None,
    contract_hash="",
    tag="",
    selected_variant="A0",
    training_lineage=None,
):
    r1.check_bundle(expert)
    if not expert.get("evidence_policy", {}).get("canonical_broad_feedback"):
        raise ValueError("CANONICAL_R1_FINAL_REPAIR_REQUIRED")
    parameters = model_parameters or {
        "feature_names": FEATURES,
        "weights": [0.0] * len(FEATURES),
        "mean": [0.0] * len(FEATURES),
        "scale": [1.0] * len(FEATURES),
    }
    trigger = trigger or {
        "feature_names": LIVE_FEATURES,
        "mean": [0.0] * len(LIVE_FEATURES),
        "scale": [1.0] * len(LIVE_FEATURES),
        "coefficients": [0.0] * len(LIVE_FEATURES),
        "intercept": 0.0,
        "constant_probability": 0.0,
        "threshold": 0.5,
        "fit_status": "UNFITTED",
    }
    bundle = {
        "version": VERSION,
        "r1_expert": copy.deepcopy(expert),
        "model_parameters": copy.deepcopy(parameters),
        "trigger": copy.deepcopy(trigger),
        "r3_reference": copy.deepcopy(r3_reference),
        "selected_variant": selected_variant,
        "fixed_candidates": sorted(
            c for c in expert["candidate_vocabulary"] if c.startswith("sensory.")
        ),
        "objective_contract_sha256": contract_hash,
        "feature_protocol_sha256": r1.digest(protocol()),
        "foundation_check_enabled": False,
        "runtime_default_changed": False,
        "training_lineage": copy.deepcopy(training_lineage),
    }
    bundle["frozen_parameters_sha256"] = r1.digest(bundle)
    bundle["bundle_id"] = "m2-r4:" + tag + ":" + bundle["frozen_parameters_sha256"][:20]
    return check_bundle(bundle)


def check_bundle(bundle):
    if (
        bundle.get("version") != VERSION
        or bundle.get("foundation_check_enabled") is not False
    ):
        raise ValueError("R4_BUNDLE_VERSION_OR_CHECK_POLICY_MISMATCH")
    unhashed = {
        k: v
        for k, v in bundle.items()
        if k not in {"bundle_id", "frozen_parameters_sha256"}
    }
    if r1.digest(unhashed) != bundle.get("frozen_parameters_sha256"):
        raise ValueError("SESSION_FROZEN_PARAMETERS_CHANGED")
    if bundle.get("feature_protocol_sha256") != r1.digest(protocol()):
        raise ValueError("FEATURE_PROTOCOL_CHANGED")
    r1.check_bundle(bundle["r1_expert"])
    if bundle.get("selected_variant") not in VARIANTS:
        raise ValueError("REGISTERED_VARIANT_REQUIRED")
    p = bundle["model_parameters"]
    if p.get("feature_names") != FEATURES:
        raise ValueError("EXACT_CANDIDATE_FEATURE_WHITELIST_REQUIRED")
    for key in ["weights", "mean", "scale"]:
        value = np.asarray(p[key], dtype=float)
        if value.shape != (len(FEATURES),) or not np.isfinite(value).all():
            raise ValueError("INVALID_CANDIDATE_PARAMETERS")
        if (key == "mean" and np.any(value != 0)) or (
            key == "scale" and np.any(value <= 0)
        ):
            raise ValueError("ZERO_MEAN_POSITIVE_RMS_SCALE_REQUIRED")
    trigger = bundle["trigger"]
    if trigger.get("feature_names") != LIVE_FEATURES or trigger.get("threshold") != 0.5:
        raise ValueError("EXACT_LIVE_FEATURE_WHITELIST_AND_THRESHOLD_REQUIRED")
    for key in ["mean", "scale", "coefficients"]:
        value = np.asarray(trigger[key], dtype=float)
        if (
            value.shape != (len(LIVE_FEATURES),)
            or not np.isfinite(value).all()
            or (key == "scale" and np.any(value <= 0))
        ):
            raise ValueError("INVALID_TRIGGER_PARAMETERS")
    if not math.isfinite(float(trigger["intercept"])):
        raise ValueError("INVALID_TRIGGER_INTERCEPT")
    if (
        trigger.get("constant_probability") is not None
        and not 0 <= trigger["constant_probability"] <= 1
    ):
        raise ValueError("INVALID_CONSTANT_CLASSIFICATION_SCORE")
    if bundle.get("r3_reference") is not None:
        r3.check_bundle(bundle["r3_reference"])
        if (
            bundle["r3_reference"]["r1_expert"]["bundle_id"]
            != bundle["r1_expert"]["bundle_id"]
        ):
            raise ValueError("R3_REFERENCE_EXPERT_SCOPE_MISMATCH")
    return bundle


def _base(state):
    return state.get("base_state", state)


def normalize(state, bundle):
    """A deliberately small projection cannot read ranks, targets or truth views."""
    expert = bundle.get("r1_expert", bundle)
    base = _base(state)
    r1.validate_context(base["context"])
    projected = {
        "context": copy.deepcopy(base["context"]),
        "answers_by_question": copy.deepcopy(base["answers_by_question"]),
        "final_comparison": copy.deepcopy(base.get("final_comparison")),
    }
    ev = r1.evidence(projected, expert)
    confirmed = set(ev["confirmed"])
    entailed = {a for c in confirmed for a in expert["candidate_attributes"].get(c, [])}
    concepts, exposures, by_slot = {}, [], {}
    for slot, answer in sorted(projected["answers_by_question"].items()):
        exposures.append(
            {
                "slot": slot,
                "question_id": answer["question_id"],
                "axis": answer["axis"],
                "shown_option_ids": sorted(answer["shown_option_ids"]),
                "state": answer["state"],
                "negative_scope": (
                    sorted(answer["shown_option_ids"])
                    if answer["state"] == "NONE_OF_THESE"
                    else []
                ),
            }
        )
        by_slot[slot] = []
        options = {o["id"]: o for o in answer["options"]}
        for concept in sorted(set(answer["selected_option_ids"])):
            option = options[concept]
            broad = option["kind"] == "broad"
            canonical = "attribute." + option["attribute"] if broad else concept
            attrs = (
                [option["attribute"]]
                if broad
                else expert["candidate_attributes"].get(concept, [])
            )
            evidence_id = "concept:" + canonical
            prior = concepts.get(canonical)
            if prior is not None:
                prior["answer_evidence_ids"].append(answer["question_id"])
                continue
            derived = bool(broad and option["attribute"] in entailed)
            concepts[canonical] = {
                "concept_id": canonical,
                "evidence_id": evidence_id,
                "attributes": sorted(set(attrs)),
                "kind": "broad" if broad else "whole_specific_concept",
                "first_slot": slot,
                "answer_evidence_ids": [answer["question_id"]],
                "derived_parent_reuse": derived,
                "independence": "DISTINCT_CANONICAL_CONTENT_NOT_INDEPENDENT_SENSORY_REPLICATION",
            }
            if not derived:
                by_slot[slot].append(canonical)
    return {
        "version": VERSION,
        "evidence": ev,
        "concepts": list(concepts.values()),
        "positive_concepts_by_slot": by_slot,
        "exposure_scopes": exposures,
        "context_availability": {
            "c0_provided": True,
            "c1_provided": True,
            "context_values_used_as_sensory_labels": False,
        },
        "stage": max(projected["answers_by_question"], default="INITIAL"),
        "has_final_comparison": projected["final_comparison"] is not None,
        "allowed_input_projection": [
            "context",
            "answers_by_question",
            "final_comparison",
        ],
    }


def build_k1(normalized, bundle):
    """Pre-score evidence hypothesis; neither legal mask nor attributes use a rank."""
    expert = bundle.get("r1_expert", bundle)
    ev = normalized["evidence"]
    explicit = set(ev["confirmed"])
    supported = set(ev["broad"]) | {
        a for c in explicit for a in expert["candidate_attributes"].get(c, [])
    }
    negative = set(ev["negative_broad"])
    dimensions = {}
    for a in ATTRS:
        support_ids = sorted(
            {c["evidence_id"] for c in normalized["concepts"] if a in c["attributes"]}
        )
        if a in supported and not support_ids:
            support_ids = [
                "final-concept:" + c
                for c in sorted(explicit)
                if a in expert["candidate_attributes"].get(c, [])
            ]
            if not support_ids:
                support_ids = ["final-direction:" + a]
        negative_ids = sorted(
            x["question_id"]
            for x in normalized["exposure_scopes"]
            if x["state"] == "NONE_OF_THESE"
            and any(
                a in expert["candidate_attributes"].get(c, [])
                and c.startswith("attribute.")
                for c in x["negative_scope"]
            )
        )
        dimensions[a] = {
            "supported": float(a in supported),
            "explicit_rejected": float(a in negative),
            "unknown": a not in supported and a not in negative,
            "status": (
                "REVISED"
                if a in supported and a in negative
                else (
                    "SUPPORTED_WITHIN_SCOPE"
                    if a in supported or a in negative
                    else "PROPOSED"
                )
            ),
            "support_evidence_ids": support_ids,
            "rejection_answer_ids": negative_ids,
            "type": "SEMANTIC_ENTAILMENT",
            "priority_is_reversible": True,
            "missing_is_negative": False,
        }
    candidates = expert["candidate_vocabulary"]
    return {
        "version": VERSION,
        "computed_before_candidate_scoring": True,
        "dimensions": dimensions,
        "confirmed_concepts": sorted(explicit),
        "explicit_rejected_concepts": ev["explicit_none"],
        "limited_counterevidence_scope": copy.deepcopy(normalized["exposure_scopes"]),
        "context_availability": normalized["context_availability"],
        "preferred_legal_candidates": sorted(
            c
            for c in candidates
            if expert["candidate_rights"].get(c) == "ADMITTED"
            and set(expert["candidate_attributes"].get(c, [])) & supported
        ),
        "legal_candidates": sorted(
            c for c in candidates if expert["candidate_rights"].get(c) == "ADMITTED"
        ),
        "hard_mask_reason": "FROZEN_ADMISSION_CONTRACT_ONLY",
        "empirical_compatibility_status": "PROPOSED_UNTIL_TRAIN_FIT_WITHIN_SCOPE",
        "independent_incompatibility_accuracy": "NOT_ESTIMABLE_NO_INDEPENDENT_LABELS",
    }


buildK1 = build_k1


def _pairs(normalized):
    concepts = {c["concept_id"]: c for c in normalized["concepts"]}
    vectors = {}
    for slot, ids in normalized["positive_concepts_by_slot"].items():
        attrs = {a for c in ids for a in concepts[c]["attributes"]}
        vectors[slot] = np.asarray([float(a in attrs) for a in ATTRS])
    pairs = []
    for left, right in PAIR_SLOTS:
        x, y = vectors.get(left), vectors.get(right)
        if x is None or y is None or not x.any() or not y.any():
            continue
        values = []
        for i in range(len(ATTRS)):
            values.extend(
                [
                    float(x[i] * y[i]),
                    float(
                        (x[i] * (y.sum() - y[i]) + y[i] * (x.sum() - x[i]))
                        / (2 * (len(ATTRS) - 1))
                    ),
                ]
            )
        pairs.append(
            {
                "slots": [left, right],
                "features": values,
                "evidence_ids": sorted(
                    "concept:" + c
                    for s in [left, right]
                    for c in normalized["positive_concepts_by_slot"][s]
                ),
            }
        )
    return pairs


def features(state, bundle, variant=None, *, k1_override=None):
    """Shared fit/live candidate matrix. Override exists only for engineering interventions."""
    variant = variant or bundle.get("selected_variant", "A0")
    if variant not in VARIANTS:
        raise ValueError("REGISTERED_VARIANT_REQUIRED")
    expert = bundle["r1_expert"]
    normalized = normalize(state, bundle)
    k1 = (
        build_k1(normalized, bundle)
        if k1_override is None
        else copy.deepcopy(k1_override)
    )
    pairs = _pairs(normalized)
    shared = (
        np.mean([p["features"] for p in pairs], axis=0)
        if pairs
        else np.zeros(len(RELATION_FEATURES))
    )
    # Baseline score computation is downstream from normalization and K1.
    base_rows = r1.rank_candidates(_base(state), expert)
    base_by_id = {r["candidate_id"]: r for r in base_rows}
    confirmed = set(normalized["evidence"]["confirmed"])
    rows, ungated, gates, mask = [], [], [], []
    for candidate in expert["candidate_vocabulary"]:
        ca = set(expert["candidate_attributes"].get(candidate, []))
        dimensions = [k1["dimensions"][a] for a in sorted(ca) if a in k1["dimensions"]]
        denom = max(len(dimensions), 1)
        support = sum(d["supported"] for d in dimensions) / denom
        rejection = sum(d["explicit_rejected"] for d in dimensions) / denom
        rejection = max(rejection, float(candidate in k1["explicit_rejected_concepts"]))
        conflict = (
            sum(d["supported"] * d["explicit_rejected"] for d in dimensions) / denom
        )
        assoc = [
            expert["statistics"]["conditional"].get(c, {}).get(candidate, 0.0)
            for c in sorted(confirmed)
            if c != candidate
        ]
        mean, maximum = (float(np.mean(assoc)), max(assoc)) if assoc else (0.0, 0.0)
        kvalues = np.asarray(
            [
                support * mean,
                support * (maximum - mean),
                rejection * mean,
                conflict * mean,
            ]
        )
        modulation = np.asarray(
            [float(a in ca) / max(len(ca), 1) for a in ATTRS for _ in range(2)]
        )
        relation = shared * modulation
        gate = 0.0 if variant == "AKR" and rejection > 0 else 1.0
        # The frozen primary retrieval task trains only fine candidates. Broad
        # scores therefore retain the complete original baseline component.
        if candidate in confirmed or not candidate.startswith("sensory."):
            kvalues *= 0
            relation *= 0
        ungated.append(relation.tolist())
        values = np.concatenate(
            [
                kvalues if variant in {"AK", "AKR"} else np.zeros(len(K1_FEATURES)),
                (
                    relation * gate
                    if variant in {"AR", "AKR"}
                    else np.zeros(len(RELATION_FEATURES))
                ),
            ]
        )
        rows.append(values.tolist())
        gates.append(gate)
        mask.append(expert["candidate_rights"].get(candidate) == "ADMITTED")
    parameters = bundle["model_parameters"]
    scaled = np.asarray(rows) / np.asarray(parameters["scale"])
    return {
        "candidate_ids": list(expert["candidate_vocabulary"]),
        "feature_names": FEATURES,
        "features": scaled.tolist(),
        "raw_features": rows,
        "legal_mask": mask,
        "base_rows": [base_by_id[c] for c in expert["candidate_vocabulary"]],
        "normalized_evidence": normalized,
        "k1": k1,
        "positive_pairs": pairs,
        "ungated_relation_features": ungated,
        "relation_gates": gates,
        "variant": variant,
        "diagnostic_k1_override": k1_override is not None,
    }


def masked_normalize(scores, legal_mask):
    scores = np.asarray(scores, dtype=float)
    mask = np.asarray(legal_mask, dtype=bool)
    if scores.ndim != 1 or scores.shape != mask.shape or not np.isfinite(scores).all():
        raise ValueError("FINITE_SCORE_AND_EXPLICIT_MASK_REQUIRED")
    if not mask.any():
        return {
            "status": "NO_LEGAL_CANDIDATE_TECHNICAL_DIAGNOSTIC",
            "log_weights": [None] * len(scores),
            "weights": [0.0] * len(scores),
        }
    valid = scores[mask]
    maximum = float(valid.max())
    log_total = maximum + math.log(float(np.exp(valid - maximum).sum()))
    logs = [
        float(value - log_total) if active else None
        for value, active in zip(scores, mask)
    ]
    return {
        "status": "OK_RETRIEVAL_NORMALIZER_NOT_SENSORY_PROBABILITY",
        "log_weights": logs,
        "weights": [math.exp(value) if value is not None else 0.0 for value in logs],
    }


def score(state, bundle, variant=None, *, k1_override=None):
    encoded = features(state, bundle, variant, k1_override=k1_override)
    matrix = np.asarray(encoded["features"])
    weights = np.asarray(bundle["model_parameters"]["weights"])
    components = matrix * weights
    deltas = matrix @ weights  # Identical whole-matrix operation to fitting.
    rows = []
    for base, values, delta, mask, gate in zip(
        encoded["base_rows"],
        components,
        deltas,
        encoded["legal_mask"],
        encoded["relation_gates"],
    ):
        kdelta = float(sum(values[: len(K1_FEATURES)]))
        rdelta = float(sum(values[len(K1_FEATURES) :]))
        rows.append(
            {
                **copy.deepcopy(base),
                "base_score": base["score"],
                "score": float(base["score"] + delta),
                "k1_delta": kdelta,
                "relation_delta": rdelta,
                "conditioning_delta": float(delta),
                "conditioning_components": dict(zip(FEATURES, map(float, values))),
                "relation_gate": gate,
                "legal": mask,
                "direct_evidence_application_count": 1,
                "relation_evidence_ids": (
                    sorted(
                        {
                            eid
                            for p in encoded["positive_pairs"]
                            for eid in p["evidence_ids"]
                        }
                    )
                    if rdelta != 0
                    else []
                ),
            }
        )
    normalization = masked_normalize([r["score"] for r in rows], encoded["legal_mask"])
    for row, value in zip(rows, normalization["log_weights"]):
        row["retrieval_log_weight"] = value
    legal = [r for r in rows if r["legal"]]
    raw_ranks = {
        r["candidate_id"]: i
        for i, r in enumerate(
            sorted(legal, key=lambda r: (-r["score"], r["candidate_id"])), 1
        )
    }
    legal.sort(key=lambda r: (-int(r["explicit"]), -r["score"], r["candidate_id"]))
    for i, row in enumerate(legal, 1):
        row.update(
            rank=i,
            raw_rank=raw_ranks[row["candidate_id"]],
            postprocessing_promoted=i < raw_ranks[row["candidate_id"]],
        )
    return {
        "candidate_scores": legal,
        "encoded": encoded,
        "normalization": normalization,
    }


def wrap_state(base, bundle, variant=None, trigger_policy="ALWAYS_ASK", previous=None):
    variant = variant or bundle["selected_variant"]
    if trigger_policy not in POLICIES:
        raise ValueError("REGISTERED_TRIGGER_POLICY_REQUIRED")
    result = score(base, bundle, variant)
    previous_order = [
        r["candidate_id"] for r in (previous or {}).get("candidate_scores", [])[:5]
    ]
    return {
        "base_state": copy.deepcopy(base),
        "conditioning_model_version": bundle["bundle_id"],
        "variant": variant,
        "trigger_policy": trigger_policy,
        "candidate_scores": result["candidate_scores"],
        "k1": result["encoded"]["k1"],
        "conditioning_trace": {
            "dag": protocol()["dag"],
            "feature_names": FEATURES,
            "raw_features": result["encoded"]["raw_features"],
            "candidate_ids": result["encoded"]["candidate_ids"],
            "positive_pairs": result["encoded"]["positive_pairs"],
            "relation_gates": result["encoded"]["relation_gates"],
            "legal_mask": result["encoded"]["legal_mask"],
            "normalization_status": result["normalization"]["status"],
        },
        "q2_decision": copy.deepcopy((previous or {}).get("q2_decision")),
        "previous_top5": previous_order,
    }


wrap = wrap_state


def live_features(state, bundle):
    dimensions = state["k1"]["dimensions"]
    rows = state["candidate_scores"]
    top = {r["candidate_id"] for r in rows[:5]}
    base_top = {
        r["candidate_id"]
        for r in r1.rank_candidates(state["base_state"], bundle["r1_expert"])[:5]
    }
    # Reconstruct the preceding canonical prefix: arrival batches, repeated
    # requests and replacement history cannot become an extra router input.
    prior = copy.deepcopy(state["base_state"])
    if prior["answers_by_question"]:
        prior["answers_by_question"].pop(max(prior["answers_by_question"]))
        prior["final_comparison"] = None
        previous = {
            r["candidate_id"]
            for r in score(prior, bundle, state["variant"])["candidate_scores"][:5]
        }
    else:
        previous = set()
    raw = np.asarray(state["conditioning_trace"]["raw_features"])
    counts = bundle["r1_expert"]["statistics"]["counts"]
    explicit = state["k1"]["confirmed_concepts"]
    return {
        "supported_dimension_count": float(
            sum(d["supported"] > 0 for d in dimensions.values())
        ),
        "rejected_dimension_count": float(
            sum(d["explicit_rejected"] > 0 for d in dimensions.values())
        ),
        "explicit_fine_count": float(sum(c.startswith("sensory.") for c in explicit)),
        "unknown_dimension_count": float(
            sum(d["unknown"] for d in dimensions.values())
        ),
        "positive_pair_count": float(
            len(state["conditioning_trace"]["positive_pairs"])
        ),
        "relation_feature_l1": float(np.abs(raw[:, len(K1_FEATURES) :]).sum()),
        "conditioning_delta_l1": float(sum(abs(r["conditioning_delta"]) for r in rows)),
        "top5_base_disagreement": 1 - len(top & base_top) / max(len(top | base_top), 1),
        "previous_top5_change": (
            1 - len(top & previous) / max(len(top | previous), 1) if previous else 0.0
        ),
        "log_training_support": math.log1p(
            sum(counts.get(c, 0) for c in explicit) / max(len(explicit), 1)
        ),
    }


def initial_state(context, bundle, variant=None, trigger_policy="ALWAYS_ASK"):
    check_bundle(bundle)
    return wrap_state(
        r1.initial_state(context, bundle["r1_expert"], "P1", "fixed"),
        bundle,
        variant,
        trigger_policy,
    )


def _state_check(state, bundle):
    check_bundle(bundle)
    if state["conditioning_model_version"] != bundle["bundle_id"]:
        raise ValueError("SESSION_FROZEN_PARAMETERS_CHANGED")


def select_next_question(state, bundle):
    return r1.select_next_question(state["base_state"], bundle["r1_expert"])


def apply_q2_action(state, bundle, action, decision=None):
    if action not in {"ASK", "SKIP"}:
        raise ValueError("Q2_ASK_OR_SKIP_REQUIRED")
    base = copy.deepcopy(state["base_state"])
    if "Q2" not in base["answers_by_question"] or any(
        q in base["answers_by_question"] for q in ["Q3", "Q4"]
    ):
        raise ValueError("BRANCH_ONLY_IMMEDIATELY_AFTER_Q2")
    base["skipped_slots"] = sorted(
        (set(base["skipped_slots"]) - {"Q3"}) | ({"Q3"} if action == "SKIP" else set())
    )
    base = r1.recompute(base, bundle["r1_expert"])
    # Applying a branch is not a new answer; retain the same pre-answer feature.
    current = wrap_state(base, bundle, state["variant"], state["trigger_policy"], state)
    current["previous_top5"] = copy.deepcopy(state.get("previous_top5", []))
    current["q2_decision"] = {
        "action": action,
        **(decision or {}),
        "no_fabricated_Q3_answer": True,
    }
    return current


def trigger_prediction(values, trigger):
    if trigger.get("constant_probability") is not None:
        return float(trigger["constant_probability"])
    x = np.asarray([values[name] for name in LIVE_FEATURES])
    z = float(
        ((x - np.asarray(trigger["mean"])) / np.asarray(trigger["scale"]))
        @ np.asarray(trigger["coefficients"])
        + trigger["intercept"]
    )
    return 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))


def decide_q2(state, bundle):
    policy = state["trigger_policy"]
    detail = {"policy": policy, "feature_values": live_features(state, bundle)}
    if policy in {"ALWAYS_ASK", "ALWAYS_SKIP"}:
        action = "ASK" if policy == "ALWAYS_ASK" else "SKIP"
    elif policy == "KEY_CASE":
        probability = trigger_prediction(detail["feature_values"], bundle["trigger"])
        action = "ASK" if probability > bundle["trigger"]["threshold"] else "SKIP"
        detail.update(
            classification_score=probability,
            threshold=bundle["trigger"]["threshold"],
            score_meaning="UNCALIBRATED_WEIGHTED_CLASSIFICATION_SCORE_NOT_GAIN_OR_RESPONSE_PROBABILITY",
            fit_status=bundle["trigger"]["fit_status"],
        )
    else:
        reference = bundle.get("r3_reference")
        if reference is None:
            raise ValueError("FROZEN_R3_REFERENCE_REQUIRED")
        # Recreate K1 revisions from the same canonical prefixes, rather than
        # silently resetting the old trigger's revision-count input to zero.
        prefix = copy.deepcopy(state["base_state"])
        complete = copy.deepcopy(prefix["answers_by_question"])
        prefix["answers_by_question"] = {}
        prefix["final_comparison"] = None
        old = r3.wrap_state(prefix, reference, reference["selected_variant"], "LEARNED")
        for slot, answer in sorted(complete.items()):
            prefix["answers_by_question"][slot] = answer
            old = r3.wrap_state(
                prefix, reference, reference["selected_variant"], "LEARNED", old
            )
        old_features = r3.live_features(old, reference)
        gain = r3.trigger_prediction(old_features, reference["trigger_a"])
        action = "ASK" if gain > 0.01 else "SKIP"
        detail.update(
            r3_predicted_gain=gain, r3_feature_values=old_features, threshold=0.01
        )
    return apply_q2_action(state, bundle, action, detail)


def update_state(state, answer, bundle):
    _state_check(state, bundle)
    return _update_state_checked(state, answer, bundle)


def _update_state_checked(state, answer, bundle):
    base = r1.update_joint_state(state["base_state"], answer, bundle["r1_expert"])
    if base == state["base_state"]:
        return copy.deepcopy(state)
    current = wrap_state(base, bundle, state["variant"], state["trigger_policy"], state)
    if answer["slot"] == "Q2" and not any(
        q in base["answers_by_question"] for q in ["Q3", "Q4"]
    ):
        current = decide_q2(current, bundle)
    return current


update = update_state


def complete_branch(state, visible, bundle, action):
    """The answer generator accepts only separately frozen visible A, never T."""
    from train_m2_r1 import answer_for

    current = apply_q2_action(state, bundle, action)
    answers = []
    while True:
        nxt = select_next_question(current, bundle)
        if nxt["action"] != "ASK":
            break
        if nxt["question"]["slot"] not in {"Q3", "Q4"} or len(answers) >= 2:
            raise ValueError("TWO_FOLLOWUP_QUESTION_BOUND_EXCEEDED")
        answer = answer_for(nxt["question"], visible, bundle["r1_expert"])
        current = _update_state_checked(current, answer, bundle)
        answers.append(answer)
    return current, answers


def finalize_result(state, bundle):
    _state_check(state, bundle)
    final = r1.finalize_result(state["base_state"], bundle["r1_expert"])
    current = wrap_state(
        final["state"], bundle, state["variant"], state["trigger_policy"], state
    )
    current["previous_top5"] = copy.deepcopy(state.get("previous_top5", []))
    if state.get("frozen_final_rows") is not None:
        current["candidate_scores"] = copy.deepcopy(state["frozen_final_rows"])
        current["frozen_final_rows"] = copy.deepcopy(state["frozen_final_rows"])
    rows = current["candidate_scores"]
    exposure = None
    if final["stage"] == "PRELIMINARY_RESULT":
        ids = [r["candidate_id"] for r in rows[:8]]
        exposure = {
            "candidate_ids": ids,
            "generation_version": bundle["bundle_id"],
            "state_hash": r1.digest(
                [
                    current["base_state"]["answers_by_question"],
                    state["variant"],
                    state["q2_decision"],
                    bundle["bundle_id"],
                ]
            ),
            "eligible_for_final_comparison": 3 <= len(ids) <= 8,
        }
    return {
        "state": current,
        "main": rows[:5],
        "secondary": rows[5:8],
        "stage": final["stage"],
        "next": final["next"],
        "exposure": exposure,
        "human_time": None,
        "candidate_groups": [
            {
                "id": "R4_SINGLE_JUSTIFIED_OUTPUT_GROUP",
                "main_candidate_ids": [r["candidate_id"] for r in rows[:5]],
                "secondary_candidate_ids": [r["candidate_id"] for r in rows[5:8]],
                "supported_direction_ids": [
                    a for a, d in current["k1"]["dimensions"].items() if d["supported"]
                ],
                "unresolved_direction_ids": [
                    a for a, d in current["k1"]["dimensions"].items() if d["unknown"]
                ],
                "relation_evidence_ids": sorted(
                    {eid for row in rows[:8] for eid in row["relation_evidence_ids"]}
                ),
                "shared_global_candidate_budget": {"main": 5, "secondary": 3},
                "group_count_does_not_multiply_budget": True,
            }
        ],
    }


def apply_final_comparison(state, feedback, bundle, mode="F2"):
    _state_check(state, bundle)
    if state["base_state"]["final_comparison"]:
        raise ValueError("FINAL_COMPARISON_ALREADY_USED")
    if (
        mode not in {"F0", "F1", "F2"}
        or not isinstance(feedback, dict)
        or set(feedback)
        != {
            "exposed_candidates",
            "selected_candidates",
            "feedback_source",
            "generation_version",
        }
    ):
        raise ValueError("FINAL_COMPARISON_SCHEMA_OR_MODE_MISMATCH")
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
        or any(not isinstance(c, str) for c in selected)
        or len(selected) != len(set(selected))
        or not set(selected) <= set(exposure["candidate_ids"])
    ):
        raise ValueError("FINAL_FEEDBACK_SOURCE_OR_SUBSET_ERROR")
    base = copy.deepcopy(result["state"]["base_state"])
    base["final_comparison"] = {
        **copy.deepcopy(feedback),
        "selected_candidates": sorted(selected),
        "mode": mode,
    }
    current = wrap_state(
        r1.recompute(base, bundle["r1_expert"]),
        bundle,
        state["variant"],
        state["trigger_policy"],
        state,
    )
    if mode in {"F0", "F1"}:
        rows = copy.deepcopy(result["state"]["candidate_scores"])
        if mode == "F1":
            rows.sort(key=lambda row: -int(row["candidate_id"] in selected))
        for i, row in enumerate(rows, 1):
            row["rank"] = i
        current["candidate_scores"] = rows
        current["frozen_final_rows"] = copy.deepcopy(rows)
    return current


def run(payload, bundle):
    allowed = {
        "contract_version",
        "context",
        "variant",
        "trigger_policy",
        "answers",
        "final_comparison",
        "final_mode",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) - allowed
        or payload.get("contract_version") != VERSION
    ):
        raise ValueError("R4_REQUEST_CONTRACT_MISMATCH")
    if not isinstance(payload.get("answers", []), list):
        raise ValueError("ANSWERS_MUST_BE_ARRAY")
    state = initial_state(
        payload["context"],
        bundle,
        payload.get("variant", bundle["selected_variant"]),
        payload.get("trigger_policy", "KEY_CASE"),
    )
    for batch in payload.get("answers", []):
        for answer in batch if isinstance(batch, list) else [batch]:
            state = update_state(state, answer, bundle)
    if "final_comparison" in payload:
        state = apply_final_comparison(
            state, payload["final_comparison"], bundle, payload.get("final_mode", "F2")
        )
    return finalize_result(state, bundle)


evaluation_entry = run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--request", "--payload-file", dest="request", required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                json.loads(Path(args.request).read_text()),
                json.loads(Path(args.model).read_text()),
            ),
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
