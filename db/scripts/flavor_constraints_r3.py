"""R3 constraint audit, sparse semantic relations and bounded Q2 decisions.

Scores and empirical branch utilities are retrieval proxies, not sensory or
response probabilities. This research wrapper leaves all earlier models intact.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import flavor_m2_r1 as r1

VERSION = "m2-constraints.r3.v1"
AUDIT_VERSION = "r3-k1-hypotheses.audit.v1"
VARIANTS = ["E1", "E2", "E3"]
POLICIES = ["ALWAYS_ASK", "SIMPLE_RULE", "LEARNED", "TWO_STEP_EMPIRICAL"]
FEATURES = [
    "stage_q2",
    "k1_supported_count",
    "k1_empirical_count",
    "k1_revised_count",
    "independent_broad_count",
    "explicit_fine_count",
    "dimension_count",
    "log_training_support",
    "relation_top5_disagreement",
    "previous_answer_top5_change",
]
PAIR_SLOTS = [("Q0", "Q1"), ("Q0", "Q2"), ("Q1", "Q2")]
_LOOKAHEAD_CACHE = {}


def empty_relations():
    return {"pairs": [], "triples": [], "fit_status": "UNFITTED_NO_RELATION_EFFECT"}


def empty_trigger():
    return {
        "feature_names": FEATURES,
        "mean": [0.0] * len(FEATURES),
        "scale": [1.0] * len(FEATURES),
        "coefficients": [0.0] * len(FEATURES),
        "intercept": 0.0,
        "global_mean": 0.0,
        "shrinkage": 0.0,
        "labelled_groups": 0,
        "fit_status": "UNFITTED",
        "enabled": False,
    }


def make_bundle(
    expert,
    relations=None,
    trigger_a=None,
    trigger_b=None,
    contract_hash="",
    tag="",
    empirical_branches=None,
    selected_variant="E1",
    training_lineage=None,
):
    r1.check_bundle(expert)
    if not expert.get("evidence_policy", {}).get("canonical_broad_feedback"):
        raise ValueError("CANONICAL_R1_FINAL_REPAIR_REQUIRED")
    bundle = {
        "version": VERSION,
        "r1_expert": copy.deepcopy(expert),
        "relations": copy.deepcopy(relations or empty_relations()),
        "trigger_a": copy.deepcopy(trigger_a or empty_trigger()),
        "trigger_b": copy.deepcopy(trigger_b or empty_trigger()),
        "empirical_branches": copy.deepcopy(empirical_branches or []),
        "selected_variant": selected_variant,
        "fixed_candidates": sorted(
            c for c in expert["candidate_vocabulary"] if c.startswith("sensory.")
        ),
        "objective_contract_sha256": contract_hash,
        "foundation_check_enabled": False,
        "runtime_default_changed": False,
        "direct_evidence_application_count": 1,
        "hard_pruning": "CONTRACT_INVALID_ONLY_NO_EMPIRICAL_DELETIONS",
    }
    if training_lineage is not None:
        bundle["training_lineage"] = copy.deepcopy(training_lineage)
    bundle["frozen_parameters_sha256"] = r1.digest(bundle)
    bundle["bundle_id"] = "m2-r3:" + tag + ":" + bundle["frozen_parameters_sha256"][:20]
    return bundle


def check_bundle(bundle):
    if (
        bundle.get("version") != VERSION
        or bundle.get("foundation_check_enabled") is not False
    ):
        raise ValueError("R3_BUNDLE_VERSION_OR_CHECK_POLICY_MISMATCH")
    unhashed = {
        k: v
        for k, v in bundle.items()
        if k not in {"bundle_id", "frozen_parameters_sha256"}
    }
    if r1.digest(unhashed) != bundle.get("frozen_parameters_sha256"):
        raise ValueError("SESSION_FROZEN_PARAMETERS_CHANGED")
    r1.check_bundle(bundle["r1_expert"])
    if bundle["selected_variant"] not in VARIANTS:
        raise ValueError("REGISTERED_RELATION_VARIANT_REQUIRED")
    if any(bundle[t]["feature_names"] != FEATURES for t in ["trigger_a", "trigger_b"]):
        raise ValueError("EXACT_LIVE_FEATURE_WHITELIST_REQUIRED")
    return bundle


def semantic_answer(answer):
    """Question meaning excludes ephemeral instance IDs; compounds stay whole."""
    if answer["state"] != "SELECTED" or not answer["selected_option_ids"]:
        return None
    options = answer["options"]
    return {
        "slot": answer["slot"],
        "axis": answer["axis"],
        "offered": sorted([o["kind"], o["id"], o.get("attribute")] for o in options),
        "selected": sorted(set(answer["selected_option_ids"])),
    }


def available_terms(base_state, order=2):
    patterns = {
        slot: semantic_answer(answer)
        for slot, answer in base_state["answers_by_question"].items()
    }
    slots_list = PAIR_SLOTS if order == 2 else [("Q0", "Q1", "Q2")]
    terms = []
    for slots in slots_list:
        if all(patterns.get(slot) for slot in slots):
            pattern = [patterns[slot] for slot in slots]
            terms.append(
                {
                    "term_id": "relation:" + r1.digest(pattern),
                    "slots": list(slots),
                    "pattern": pattern,
                }
            )
    return terms


def active_terms(base_state, bundle, variant):
    if variant == "E1":
        return []
    possible = {
        t["term_id"] for order in [2, 3] for t in available_terms(base_state, order)
    }
    terms = bundle["relations"]["pairs"] + (
        bundle["relations"]["triples"] if variant == "E3" else []
    )
    return [term for term in terms if term["term_id"] in possible]


def rank_candidates(base_state, bundle, variant="E1"):
    if variant not in VARIANTS:
        raise ValueError("REGISTERED_RELATION_VARIANT_REQUIRED")
    return rank_from_base_rows(
        r1.rank_candidates(base_state, bundle["r1_expert"]),
        active_terms(base_state, bundle, variant),
    )


def rank_from_base_rows(base_rows, terms):
    """Shared frozen-score plus relation path for OOF training and live output."""
    rows = copy.deepcopy(base_rows)
    for row in rows:
        delta = (
            0.0
            if row["explicit"]
            else sum(
                float(term["coefficients"].get(row["candidate_id"], 0.0))
                for term in terms
            )
        )
        row["base_r1_score"] = row["score"]
        row["relation_delta"] = delta
        row["score"] += delta
        row["relation_evidence_ids"] = [
            t["term_id"] for t in terms if row["candidate_id"] in t["coefficients"]
        ]
    raw = sorted(rows, key=lambda row: (-row["score"], row["candidate_id"]))
    raw_ranks = {row["candidate_id"]: i for i, row in enumerate(raw, 1)}
    rows.sort(
        key=lambda row: (-int(row["explicit"]), -row["score"], row["candidate_id"])
    )
    for i, row in enumerate(rows, 1):
        row.update(
            rank=i,
            raw_rank=raw_ranks[row["candidate_id"]],
            postprocessing_promoted=i < raw_ranks[row["candidate_id"]],
        )
    return rows


def build_k1(base_state, bundle, variant="E1", previous=()):
    evidence = r1.evidence(base_state, bundle["r1_expert"])
    clauses = [
        {
            "id": "contract:runtime",
            "type": "HARD_CONTRACT",
            "status": "SUPPORTED_WITHIN_SCOPE",
            "scope": "VALID_C0_C1_ORDINARY_SLOTS_AND_EXPOSURE",
            "evidence_ids": ["contract:" + VERSION],
            "hard_deleted_candidates": [],
            "sensory_exclusion_claim": False,
        }
    ]
    for relation in evidence["relations"]:
        clauses.append(
            {
                "id": relation["evidence_id"],
                "type": "SEMANTIC_ENTAILMENT",
                "status": "SUPPORTED_WITHIN_SCOPE",
                "scope": relation["relation_type"],
                "evidence_ids": [relation["evidence_id"]],
                "concept_id": relation["concept_id"],
                "hard_deleted_candidates": [],
                "sensory_exclusion_claim": False,
            }
        )
    active = {t["term_id"] for t in active_terms(base_state, bundle, variant)}
    for term in bundle["relations"]["pairs"] + bundle["relations"]["triples"]:
        if term["term_id"] not in active:
            continue
        clauses.append(
            {
                "id": term["term_id"],
                "type": "EMPIRICAL_COMPATIBILITY",
                "status": "SUPPORTED_WITHIN_SCOPE",
                "scope": "TRAIN_COFFEE_GROUP_CONDITIONAL_MENTION_RETRIEVAL_ONLY",
                "evidence_ids": term.get("training_evidence_ids", []),
                "training_group_support": term["training_group_support"],
                "hard_deleted_candidates": [],
                "sensory_exclusion_claim": False,
            }
        )
    current_ids = {clause["id"] for clause in clauses}
    for old in previous:
        if old["id"] not in current_ids:
            clauses.append(
                {**copy.deepcopy(old), "status": "REVISED", "active_effect": False}
            )
    return sorted(clauses, key=lambda clause: clause["id"])


def top5(rows):
    return set(
        [
            row["candidate_id"]
            for row in rows
            if row["candidate_id"].startswith("sensory.")
        ][:5]
    )


def positive_units(evidence, expert):
    return (
        set(evidence["confirmed"])
        | {"attribute." + a for a in evidence["broad"]}
        | {
            "attribute." + a
            for c in evidence["confirmed"]
            for a in expert["candidate_attributes"].get(c, [])
        }
    )


def live_features(state, bundle):
    base = state["base_state"]
    expert = bundle["r1_expert"]
    evidence = r1.evidence(base, expert)
    units = positive_units(evidence, expert)
    dimensions = {u for u in units if u.startswith("attribute.")}
    support = [expert["statistics"]["counts"].get(unit, 0) for unit in units]
    base_top = top5(rank_candidates(base, bundle, "E1"))
    relation_top = top5(rank_candidates(base, bundle, "E2"))
    previous = copy.deepcopy(base)
    answered = sorted(previous["answers_by_question"])
    if answered:
        previous["answers_by_question"].pop(answered[-1])
    previous_top = top5(rank_candidates(previous, bundle, state["variant"]))
    current_top = top5(state["candidate_scores"])
    values = [
        float("Q2" in base["answers_by_question"]),
        float(sum(k["status"] == "SUPPORTED_WITHIN_SCOPE" for k in state["k1"])),
        float(
            sum(
                k["type"] == "EMPIRICAL_COMPATIBILITY"
                and k["status"] == "SUPPORTED_WITHIN_SCOPE"
                for k in state["k1"]
            )
        ),
        float(sum(k["status"] == "REVISED" for k in state["k1"])),
        float(len(evidence["independent_broad"])),
        float(sum(c.startswith("sensory.") for c in evidence["confirmed"])),
        float(len(dimensions)),
        float(math.log1p(float(np.mean(support)) if support else 0.0)),
        1.0 - len(base_top & relation_top) / max(1, len(base_top | relation_top)),
        1.0 - len(previous_top & current_top) / max(1, len(previous_top | current_top)),
    ]
    return dict(zip(FEATURES, values))


def trigger_prediction(features, trigger):
    if set(features) != set(FEATURES) or trigger["feature_names"] != FEATURES:
        raise ValueError("EXACT_LIVE_FEATURE_WHITELIST_REQUIRED")
    x = np.array([features[name] for name in FEATURES])
    z = (x - np.asarray(trigger["mean"])) / np.asarray(trigger["scale"])
    local = float(trigger["intercept"] + z @ np.asarray(trigger["coefficients"]))
    return float(
        trigger["shrinkage"] * local
        + (1 - trigger["shrinkage"]) * trigger["global_mean"]
    )


def wrap_state(base, bundle, variant="E1", trigger_policy="ALWAYS_ASK", previous=None):
    state = {
        "base_state": copy.deepcopy(base),
        "constraints_model_version": bundle["bundle_id"],
        "variant": variant,
        "trigger_policy": trigger_policy,
        "relation_activation": (previous or {}).get("relation_activation", "ALWAYS"),
        "candidate_scores": rank_candidates(base, bundle, variant),
        "k1": build_k1(base, bundle, variant, (previous or {}).get("k1", [])),
        "q2_decision": copy.deepcopy((previous or {}).get("q2_decision")),
    }
    state.update(k1_audit_projection(state, bundle, previous))
    return state


def k1_audit_projection(state, bundle, previous=None):
    """Additive hypothesis ledger, deliberately excluded from trigger FEATURES.

    Initial directional priorities are hypotheses about useful candidate groups.
    An observed parent is positive evidence; a child's unmentioned status never
    becomes a negative. Neither provisional nor revised hypotheses delete IDs.
    """
    base, expert = state["base_state"], bundle["r1_expert"]
    answers = base["answers_by_question"]
    evidence = r1.evidence(base, expert)
    observed = positive_units(evidence, expert)
    fixed = set(bundle["fixed_candidates"])
    by_dimension = defaultdict(list)
    for slot, answer in sorted(answers.items()):
        options = {option["id"]: option for option in answer["options"]}
        positive = (
            answer["selected_option_ids"] if answer["state"] == "SELECTED" else []
        )
        for concept in positive:
            option = options[concept]
            dimensions = (
                [option["attribute"]]
                if option["kind"] == "broad"
                else expert["candidate_attributes"].get(concept, [])
            )
            for dimension in dimensions:
                by_dimension[dimension].append(
                    {
                        "question_id": answer["question_id"],
                        "slot": slot,
                        "concept_id": concept,
                        "kind": option["kind"],
                    }
                )
    final = base.get("final_comparison")
    if final and final.get("mode") == "F2":
        for concept in final["selected_candidates"]:
            dimensions = (
                [concept.split(".", 1)[1]]
                if concept.startswith("attribute.")
                else expert["candidate_attributes"].get(concept, [])
            )
            for dimension in dimensions:
                by_dimension[dimension].append(
                    {
                        "question_id": "FINAL_COMPARISON:"
                        + final["generation_version"],
                        "slot": "FINAL_COMPARISON",
                        "concept_id": concept,
                        "kind": (
                            "broad" if concept.startswith("attribute.") else "specific"
                        ),
                    }
                )
    hypotheses = []
    old_hypotheses = {
        row["dimension"]: row for row in (previous or {}).get("k1_hypotheses", [])
    }
    if "Q1" in answers:
        dimensions = set(by_dimension) | set(old_hypotheses)
        for dimension in sorted(dimensions):
            supports = by_dimension.get(dimension, [])
            initial_concepts = {
                row["concept_id"] for row in supports if row["slot"] in {"Q0", "Q1"}
            }
            later_new = [
                row
                for row in supports
                if row["slot"] not in {"Q0", "Q1"}
                and row["concept_id"] not in initial_concepts
            ]
            rejection_ids = [
                answer["question_id"]
                for answer in answers.values()
                if answer["state"] == "NONE_OF_THESE"
                and any(
                    option.get("attribute") == dimension for option in answer["options"]
                )
            ]
            status = (
                "REVISED"
                if not supports or rejection_ids
                else "SUPPORTED_WITHIN_SCOPE" if later_new else "PROPOSED"
            )
            preferred = [
                row["candidate_id"]
                for row in state["candidate_scores"]
                if row["candidate_id"] in fixed
                and dimension
                in expert["candidate_attributes"].get(row["candidate_id"], [])
            ]
            old = old_hypotheses.get(dimension)
            priority_revision = bool(
                old
                and "Q2" in answers
                and old["preferred_legal_candidates"] != preferred
            )
            prior_revision = bool(
                old
                and old["revising_information"].get(
                    "candidate_priority_revision_observed_in_session"
                )
            )
            if priority_revision or prior_revision:
                status = "REVISED"
            hypotheses.append(
                {
                    "id": "hypothesis:direction:" + dimension,
                    "dimension": dimension,
                    "type": (
                        "EMPIRICAL_COMPATIBILITY"
                        if not supports
                        else "SEMANTIC_ENTAILMENT"
                    ),
                    "status": status,
                    "claim": "OVERLAPPING_CANDIDATE_DIRECTION_PRIORITY_NOT_CHILD_CONFIRMATION",
                    "evidence_source": (
                        "CURRENT_SESSION_CANONICAL_POSITIVES"
                        if supports
                        else "PREVIOUSLY_PROPOSED_DIRECTION_WITHDRAWN"
                    ),
                    "answer_evidence_ids": sorted(
                        {row["question_id"] for row in supports}
                    ),
                    "concept_evidence_ids": sorted(
                        {"concept:" + row["concept_id"] for row in supports}
                    ),
                    "applicability": {
                        "after_initial_Q0_Q1": True,
                        "Q2_observed": "Q2" in answers,
                        "active_positive_support": bool(supports),
                    },
                    "revising_information": {
                        "new_later_concept_answer_ids": sorted(
                            {row["question_id"] for row in later_new}
                        ),
                        "explicit_exposure_rejection_answer_ids": sorted(rejection_ids),
                        "removed_previous_positive_support": not supports,
                        "candidate_priority_revision_observed_in_session": priority_revision
                        or prior_revision,
                    },
                    "target_scope": "REGISTERED_FINE_CANDIDATES_SHARING_PARENT_WITHOUT_CHILD_ABSENCE",
                    "preferred_legal_candidates": preferred,
                    "full_legal_candidate_count": len(fixed),
                    "soft_priority_only": True,
                    "hard_deleted_candidates": [],
                    "negative_child_observation_claim": False,
                    "not_independent_sensory_corroboration": True,
                }
            )
    details = []
    for clause in state["k1"]:
        concept = clause.get("concept_id")
        matching = []
        for answer in answers.values():
            scope = (
                answer["shown_option_ids"]
                if answer["state"] == "NONE_OF_THESE"
                else answer["selected_option_ids"]
            )
            if concept in scope:
                matching.append(answer["question_id"])
        if final and concept in final["selected_candidates"]:
            matching.append("FINAL_COMPARISON:" + final["generation_version"])
        details.append(
            {
                **copy.deepcopy(clause),
                "evidence_source": (
                    "FROZEN_CONTRACT"
                    if clause["type"] == "HARD_CONTRACT"
                    else (
                        "TRAIN_GROUP_MENTION_ASSOCIATION"
                        if clause["type"] == "EMPIRICAL_COMPATIBILITY"
                        else "CURRENT_ANSWER_SEMANTICS"
                    )
                ),
                "answer_evidence_ids": sorted(matching),
                "applicability": {
                    "current_active": clause["status"] == "SUPPORTED_WITHIN_SCOPE",
                    "contract_version": VERSION,
                },
                "revising_information": (
                    "CURRENT_CANONICAL_ANSWER_REPLACEMENT_REMOVED_ANTECEDENT"
                    if clause["status"] == "REVISED"
                    else "NEW_OR_REPEATED_CANONICAL_EVIDENCE_RECOMPUTED_NO_ACCUMULATION"
                ),
                "target_scope": (
                    "FIXED_PRE_SOFT_FINE_UNIVERSE" if not concept else concept
                ),
                "full_legal_candidate_count": len(fixed),
                "soft_pruning_applied": False,
            }
        )
    old_directions = {
        row["dimension"]
        for row in old_hypotheses.values()
        if row["applicability"]["active_positive_support"]
    }
    new_directions = {
        row["dimension"]
        for row in hypotheses
        if row["applicability"]["active_positive_support"]
    }
    before = [
        row["candidate_id"] for row in (previous or {}).get("candidate_scores", [])
    ]
    after = [row["candidate_id"] for row in state["candidate_scores"]]
    return {
        "k1_audit_version": AUDIT_VERSION,
        "k1_hypotheses": hypotheses,
        "constraint_details": details,
        "k1_diagnostics": {
            "target_direction_retention_from_previous_current_evidence": (
                len(old_directions & new_directions) / len(old_directions)
                if old_directions
                else None
            ),
            "actual_candidate_order_changed_from_previous": bool(
                before and before != after
            ),
            "full_pre_soft_universe_retained": fixed <= set(after),
            "error_pruned_candidates": 0,
            "incompatible_direction_exclusion_accuracy": "NOT_ESTIMABLE_NO_INDEPENDENT_INCOMPATIBILITY_LABELS",
            "audit_projection_changes_scores_or_trigger_features": False,
        },
    }


def initial_state(
    context,
    bundle,
    variant="E1",
    trigger_policy="ALWAYS_ASK",
    relation_activation="ALWAYS",
):
    check_bundle(bundle)
    if trigger_policy not in POLICIES:
        raise ValueError("REGISTERED_TRIGGER_POLICY_REQUIRED")
    if relation_activation not in {"ALWAYS", "TRIGGER_B"} or (
        relation_activation == "TRIGGER_B" and trigger_policy != "ALWAYS_ASK"
    ):
        raise ValueError("TRIGGER_B_REQUIRES_SEPARATE_ALWAYS_ASK_PATH")
    if relation_activation == "TRIGGER_B" and variant != bundle["selected_variant"]:
        raise ValueError("TRIGGER_B_ONLY_FOR_ITS_FROZEN_SELECTED_RELATION_FAMILY")
    state = wrap_state(
        r1.initial_state(context, bundle["r1_expert"], "P1", "fixed"),
        bundle,
        variant,
        trigger_policy,
    )
    state["relation_activation"] = relation_activation
    return state


def _state_check(state, bundle):
    check_bundle(bundle)
    if state["constraints_model_version"] != bundle["bundle_id"]:
        raise ValueError("SESSION_FROZEN_PARAMETERS_CHANGED")


def apply_q2_action(state, bundle, action, decision=None):
    """Explicit R3 permission: skip Q3 without creating a fictitious answer."""
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
    result = wrap_state(base, bundle, state["variant"], state["trigger_policy"], state)
    result["q2_decision"] = {
        "action": action,
        **(decision or {}),
        "no_fabricated_Q3_answer": True,
    }
    return result


def complete_branch(state, visible, bundle, action):
    """Only supplied A produces answers; this function has no target input."""
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


def empirical_lookahead(state, bundle):
    import alignment_metrics_r3 as metric

    key = r1.digest(
        [
            bundle["bundle_id"],
            state["variant"],
            state["base_state"]["context"],
            state["base_state"]["answers_by_question"],
        ]
    )
    if key in _LOOKAHEAD_CACHE:
        return copy.deepcopy(_LOOKAHEAD_CACHE[key])

    units = positive_units(
        r1.evidence(state["base_state"], bundle["r1_expert"]), bundle["r1_expert"]
    )
    by_action = {action: defaultdict(list) for action in ["ASK", "SKIP"]}
    counts = {action: 0 for action in by_action}
    for support in bundle["empirical_branches"]:
        if not any(
            c.startswith("sensory.") and value > 0
            for c, value in support["relevance"].items()
        ):
            continue  # Undefined TRAIN utility contributes no estimate, never a zero.
        support_units = set(support["visible_units"])
        weight = 1.0 + len(units & support_units)
        for action in by_action:
            end, answers = complete_branch(state, support["visible"], bundle, action)
            loss = metric.evaluate(
                end["candidate_scores"],
                support["relevance"],
                bundle["fixed_candidates"],
                excluded_visible=support["visible"],
            )["raw_gap"]
            if loss is not None:
                by_action[action][support["group_id"]].append(
                    (loss + 0.01 * len(answers), weight)
                )
                counts[action] += 1
    utilities = {}
    for action, groups in by_action.items():
        utilities[action] = (
            float(
                np.mean(
                    [
                        np.average([v for v, _ in cells], weights=[w for _, w in cells])
                        for cells in groups.values()
                    ]
                )
            )
            if groups
            else None
        )
    if any(value is None for value in utilities.values()):
        action, status = "SKIP", "NOT_ESTIMABLE"
    else:
        action, status = (
            "ASK" if utilities["ASK"] < utilities["SKIP"] - 1e-12 else "SKIP"
        ), "TRAIN_EMPIRICAL_PROXY"
    result = action, {
        "policy": "TWO_STEP_EMPIRICAL",
        "utilities": utilities,
        "support_rows": counts,
        "support_status": status,
        "maximum_followup_questions": 2,
    }
    _LOOKAHEAD_CACHE[key] = copy.deepcopy(result)
    return result


def decide_q2(state, bundle):
    features = live_features(state, bundle)
    policy = state["trigger_policy"]
    detail = {"policy": policy, "feature_values": features}
    if state.get("relation_activation") == "TRIGGER_B":
        relation_gain = trigger_prediction(features, bundle["trigger_b"])
        active = bundle["trigger_b"]["enabled"] and relation_gain > 0.0
        state = wrap_state(
            state["base_state"],
            bundle,
            state["variant"] if active else "E1",
            policy,
            state,
        )
        detail["trigger_b"] = {
            "active": bool(active),
            "predicted_relation_gain": relation_gain,
            "fit_status": bundle["trigger_b"]["fit_status"],
        }
    if policy == "ALWAYS_ASK":
        action = "ASK"
    elif policy == "SIMPLE_RULE":
        action = (
            "ASK"
            if features["dimension_count"] <= 1 or features["explicit_fine_count"] == 0
            else "SKIP"
        )
    elif policy == "LEARNED":
        gain = trigger_prediction(features, bundle["trigger_a"])
        action = "ASK" if gain > 0.01 else "SKIP"
        detail.update(
            predicted_gain=gain,
            threshold=0.01,
            fit_status=bundle["trigger_a"]["fit_status"],
        )
    else:
        action, detail = empirical_lookahead(state, bundle)
    return apply_q2_action(state, bundle, action, detail)


def update_state(state, answer, bundle):
    _state_check(state, bundle)
    return _update_state_checked(state, answer, bundle)


def _update_state_checked(state, answer, bundle):
    """Internal generated branches use the already validated frozen bundle."""
    base = r1.update_joint_state(state["base_state"], answer, bundle["r1_expert"])
    if base == state["base_state"]:
        return copy.deepcopy(state)
    current = wrap_state(base, bundle, state["variant"], state["trigger_policy"], state)
    if answer["slot"] == "Q2" and not any(
        q in base["answers_by_question"] for q in ["Q3", "Q4"]
    ):
        current = decide_q2(current, bundle)
    return current


def select_next_question(state, bundle):
    return r1.select_next_question(state["base_state"], bundle["r1_expert"])


def finalize_result(state, bundle):
    _state_check(state, bundle)
    finalized = r1.finalize_result(state["base_state"], bundle["r1_expert"])
    current = wrap_state(
        finalized["state"], bundle, state["variant"], state["trigger_policy"], state
    )
    if state.get("frozen_final_rows") is not None:
        current["candidate_scores"] = copy.deepcopy(state["frozen_final_rows"])
        current["frozen_final_rows"] = copy.deepcopy(state["frozen_final_rows"])
    rows = [
        row
        for row in current["candidate_scores"]
        if bundle["r1_expert"]["candidate_rights"].get(row["candidate_id"])
        == "ADMITTED"
    ]
    exposure = None
    if finalized["stage"] == "PRELIMINARY_RESULT":
        ids = [row["candidate_id"] for row in rows[:8]]
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
        "stage": finalized["stage"],
        "next": finalized["next"],
        "exposure": exposure,
        "human_time": None,
        "candidate_groups": [
            {
                "id": "R3_SINGLE_JUSTIFIED_OUTPUT_GROUP",
                "main_candidate_ids": [row["candidate_id"] for row in rows[:5]],
                "secondary_candidate_ids": [row["candidate_id"] for row in rows[5:8]],
                "constraint_ids": [
                    row["id"]
                    for row in current["constraint_details"]
                    if row["status"] != "REVISED"
                ],
                "relation_ids": sorted(
                    {
                        identity
                        for row in rows[:8]
                        for identity in row.get("relation_evidence_ids", [])
                    }
                ),
                "unresolved_direction_ids": [
                    row["id"]
                    for row in current["k1_hypotheses"]
                    if row["status"] != "SUPPORTED_WITHIN_SCOPE"
                ],
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
        "relation_activation",
        "answers",
        "final_comparison",
        "final_mode",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) - allowed
        or payload.get("contract_version") != VERSION
    ):
        raise ValueError("R3_REQUEST_CONTRACT_MISMATCH")
    if not isinstance(payload.get("answers", []), list):
        raise ValueError("ANSWERS_MUST_BE_ARRAY")
    state = initial_state(
        payload["context"],
        bundle,
        payload.get("variant", bundle["selected_variant"]),
        payload.get("trigger_policy", "LEARNED"),
        payload.get("relation_activation", "ALWAYS"),
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
