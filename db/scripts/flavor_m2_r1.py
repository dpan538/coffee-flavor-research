"""Version-isolated M2 R1 runtime; frozen v2 bundles retain their original behavior."""

from __future__ import annotations
import copy, hashlib, json, math
import numpy as np
from flavor_backend import C0, C1, validate_context
from flavor_context import CONTEXT_VERSION, estimate_context_attributes

VERSIONS = {
    "contract_version": "sequential.v2.r1",
    "feature_spec_version": "shared-candidate.v2.r1",
    "context_mapping_version": CONTEXT_VERSION,
    "question_bank_version": "limited-four-options.v2.r1",
    "semantic_version": "typed-support.v2.r1",
    "cluster_version": "disabled-unless-explicit-foundation.v2.r1",
}
ATTRS = [
    "fruity",
    "floral",
    "sweet",
    "nutty_cocoa",
    "spices",
    "roasted",
    "green_vegetative",
    "sour_fermented",
    "taste",
]
LEAF_ATTRIBUTES = {
    "fruity": "apple orange lemon cherry grape strawberry bergamot raisin grapefruit peach raspberry prune blackcurrant lime pineapple pear blueberry mango blackberry plum banana pomegranate",
    "floral": "jasmine rose orange_blossom chamomile",
    "sweet": "honey caramel brown_sugar vanilla molasses",
    "nutty_cocoa": "cocoa dark_chocolate almond hazelnut walnut peanut",
    "spices": "cardamom black_pepper cinnamon nutmeg clove",
    "roasted": "tobacco malt smoky",
    "green_vegetative": "black_tea green_tea lemongrass hay woody cedar earthy",
    "sour_fermented": "alcoholic wine_like_character fermented_character",
    "taste": "bitter",
}
PARENTS = {
    "sensory." + word: [a]
    for a, words in LEAF_ATTRIBUTES.items()
    for word in words.split()
}
# Overlap is a semantic attribute hypothesis, not a new observed coffee label.
PARENTS["sensory.lemongrass"] = ["green_vegetative", "fruity"]
PARENTS["sensory.dark_chocolate"] = ["nutty_cocoa", "roasted"]
for a in ATTRS:
    PARENTS["attribute." + a] = [a]
PARENTS["broad.chocolate"] = ["nutty_cocoa"]
PARENTS["broad.nutty"] = ["nutty_cocoa"]
PARENTS["broad.citrus"] = ["fruity"]
FEATURES = [
    "log_prior",
    "specific_direct",
    "broad_candidate_direct",
    "broad_related_support",
    "cooccurrence_mean",
    "cooccurrence_max",
    "source_support_log",
    "exposed_rejection",
    "context_c0",
    "context_c1",
    "answer_pair_affinity",
    "context_answer_interaction",
    "cluster_affinity",
    "attribute_overlap",
    "feedback_direct",
    "feedback_association",
]
STATES = {"SELECTED", "UNSURE", "NONE_OF_THESE", "SKIP"}
PATHS = {"P1", "P2", "P3", "P4"}
POLICIES = {"fixed", "random", "one_step", "two_step"}


def digest(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def check_bundle(bundle):
    if not isinstance(bundle, dict):
        raise ValueError("INVALID_MODEL_BUNDLE")
    if bundle.get("model_kind") not in {
        "M2_R1_FIXED",
        "M2_R1_ADD",
        "M2_R1_FOUNDATION",
        "M2_R1_FOUNDATION_CHECK",
    }:
        raise ValueError("UNKNOWN_MODEL_KIND")
    for k, v in VERSIONS.items():
        if bundle.get(k) != v:
            raise ValueError("MODEL_BUNDLE_VERSION_MISMATCH:" + k)
    for k in [
        "scaler_parameters",
        "model_parameters",
        "candidate_vocabulary",
        "training_split_hash",
        "data_manifest_hash",
        "statistics",
        "question_bank",
        "candidate_attributes",
        "candidate_clusters",
    ]:
        if k not in bundle:
            raise ValueError("MODEL_BUNDLE_MISSING:" + k)
    if bundle["model_parameters"]["feature_names"] != FEATURES:
        raise ValueError("FEATURE_SPEC_MISMATCH")
    for key in ["mean", "scale"]:
        values = np.asarray(bundle["scaler_parameters"][key], dtype=float)
        if (
            values.shape != (len(FEATURES),)
            or not np.isfinite(values).all()
            or (key == "scale" and (values <= 0).any())
        ):
            raise ValueError("INVALID_FEATURE_SCALER")
    if np.asarray(bundle["model_parameters"]["weights"]).shape != (len(FEATURES),):
        raise ValueError("INVALID_MODEL_PARAMETERS")
    if not np.isfinite(
        np.asarray(bundle["model_parameters"]["weights"], dtype=float)
    ).all():
        raise ValueError("INVALID_MODEL_PARAMETERS")
    if len(bundle["candidate_vocabulary"]) != len(set(bundle["candidate_vocabulary"])):
        raise ValueError("DUPLICATE_CANDIDATE")
    w = dict(zip(FEATURES, bundle["model_parameters"]["weights"]))
    if any(
        w[name] < 0
        for name in [
            "specific_direct",
            "broad_candidate_direct",
            "broad_related_support",
        ]
    ):
        raise ValueError("POSITIVE_EVIDENCE_WEIGHT_MUST_BE_NONNEGATIVE")
    if w["exposed_rejection"] >= 0:
        raise ValueError("EXPLICIT_REJECTION_REQUIRES_NEGATIVE_SEMANTIC_COEFFICIENT")
    return bundle


def initial_state(context, bundle, path="P1", policy="fixed"):
    check_bundle(bundle)
    validate_context(context)
    if (
        not isinstance(path, str)
        or not isinstance(policy, str)
        or path not in PATHS
        or policy not in POLICIES
    ):
        raise ValueError("Unknown path or policy")
    state = {
        "context": dict(context),
        "path": path,
        "policy": policy,
        "answers_by_question": {},
        "final_comparison": None,
        "current_stage": "CONTEXT",
        "model_version": bundle["bundle_id"],
        "remaining_question_slots": ["Q" + str(i) for i in range(6)],
        "skipped_slots": [],
    }
    return recompute(state, bundle)


def evidence(state, bundle):
    """Canonical sets carry support once; exposure and negative scope stay explicit."""
    direct, broad, none, negative_broad = set(), set(), set(), set()
    relations, exposure_scopes = {}, []
    for slot, answer in sorted(state["answers_by_question"].items()):
        opts = {o["id"]: o for o in answer["options"]}
        chosen = set(answer["selected_option_ids"])
        all_shown = bool(chosen) and chosen == set(answer["shown_option_ids"])
        broad_options = {o["attribute"] for o in opts.values() if o["kind"] == "broad"}
        complete = answer.get(
            "classification_scope"
        ) == "COMPLETE_REGISTERED_ATTRIBUTE_RANGE" and broad_options == set(ATTRS)
        exposure_scopes.append(
            {
                "question_id": answer["question_id"],
                "all_shown_selected": all_shown,
                "complete_registered_range": complete,
                "interpretation": (
                    "NONDISCRIMINATING_WITHIN_COMPLETE_RANGE"
                    if all_shown and complete
                    else "OBSERVED_LOCAL_OPTIONS"
                ),
            }
        )
        for option_id in chosen:
            option = opts[option_id]
            if option["kind"] == "specific":
                direct.add(option_id)
            else:
                broad.add(option["attribute"])
        if answer["state"] == "NONE_OF_THESE":
            none.update(answer["shown_option_ids"])
            negative_broad.update(
                o["attribute"] for o in opts.values() if o["kind"] == "broad"
            )
    feedback = (
        set(state["final_comparison"]["selected_candidates"])
        if state.get("final_comparison")
        else set()
    )
    confirmed = direct | feedback
    parents = {a for c in confirmed for a in bundle["candidate_attributes"].get(c, [])}
    independent_broad = broad - parents
    # A source concept, repeated question, parent inference, or repeated final
    # comparison selection cannot become a second independent observation.
    for concept in sorted(confirmed):
        relations[concept] = {
            "evidence_id": "concept:" + concept,
            "concept_id": concept,
            "relation_type": "DIRECT_OBSERVATION",
            "strength": 1.0,
            "independence": "CANONICAL_CONCEPT_SUPPORT_NOT_INDEPENDENT_PANEL_REPLICATION",
        }
    for attribute in sorted(independent_broad):
        concept = "attribute." + attribute
        relations[concept] = {
            "evidence_id": "concept:" + concept,
            "concept_id": concept,
            "relation_type": "HIERARCHICAL_SUPPORT_NOT_CHILD_CONFIRMATION",
            "strength": 1.0,
            "independence": "CANONICAL_CONCEPT_SUPPORT_NOT_INDEPENDENT_PANEL_REPLICATION",
        }
    for concept in sorted(none):
        relations["negative:" + concept] = {
            "evidence_id": "exposed-rejection:" + concept,
            "concept_id": concept,
            "relation_type": "EXPLICIT_REJECTION_OF_EXPOSED_OPTION",
            "strength": 1.0,
        }
    return {
        "specific": sorted(direct),
        "confirmed": sorted(confirmed),
        "broad": sorted(broad),
        "independent_broad": sorted(independent_broad),
        "explicit_none": sorted(none),
        "negative_broad": sorted(negative_broad),
        "feedback": sorted(feedback),
        "novel_feedback": sorted(feedback - direct),
        "relations": list(relations.values()),
        "exposure_scopes": exposure_scopes,
        "all_broad_is_nondiscriminating": False,
    }


def encode_features(payload_or_state, bundle):
    check_bundle(bundle)
    if "answers_by_question" not in payload_or_state:
        state = replay(payload_or_state, bundle, plan=False)
    else:
        state = payload_or_state
    validate_context(state["context"])
    ev = evidence(state, bundle)
    observed = set(ev["confirmed"])
    broad = set(ev["independent_broad"])
    feedback = set(ev["novel_feedback"])
    stats = bundle["statistics"]
    rows = []
    attrs = {
        a for c in observed for a in bundle["candidate_attributes"].get(c, [])
    } | broad
    cluster_vectors = []  # R1 ADD/JOINT never fit or require NMF.
    dim = 0
    latent = np.mean(cluster_vectors, axis=0) if cluster_vectors else np.zeros(dim)
    for c in bundle["candidate_vocabulary"]:
        ca = set(bundle["candidate_attributes"].get(c, []))
        association = [
            stats["conditional"].get(x, {}).get(c, 0.0) for x in observed if x != c
        ]
        fba = [stats["conditional"].get(x, {}).get(c, 0.0) for x in feedback if x != c]
        pairs = [
            stats["pair_conditional"].get("|".join(sorted([a, b])), {}).get(c, 0.0)
            for i, a in enumerate(sorted(observed))
            for b in sorted(observed)[i + 1 :]
            if c not in {a, b}
        ]
        cv = np.zeros(dim)
        affinity = (
            float(np.dot(latent, cv) / (np.linalg.norm(latent) * np.linalg.norm(cv)))
            if np.linalg.norm(latent) * np.linalg.norm(cv) > 0
            else 0.0
        )
        leaf = c.startswith("sensory.")
        direct = c in observed
        wide = not leaf and (
            c in observed
            or (c.startswith("attribute.") and c.split(".", 1)[1] in broad)
        )
        raw = [
            stats["log_prior"].get(c, -10.0),
            float(direct and leaf),
            float(wide),
            float(bool(ca & broad) and not direct),
            float(np.mean(association)) if association else 0.0,
            max(association, default=0.0),
            math.log1p(stats["counts"].get(c, 0)),
            float(c in ev["explicit_none"] or bool(ca & set(ev["negative_broad"]))),
            0.0,
            0.0,
            max(pairs, default=0.0),
            0.0,
            affinity,
            len(ca & attrs) / max(len(ca), 1),
            0.0,  # Feedback is canonical direct evidence; never added twice.
            0.0,
        ]
        # Descriptor records have no validated product C0/C1. Their components
        # are unsupported in THIS bundle and identically zero during fit/replay/live.
        # Source-specific numerical C0 predictions remain separately available.
        if bundle["model_kind"] == "M2_R1_ADD":
            for i in [10, 11, 12, 13]:
                raw[i] = 0.0
        else:
            raw[12] = raw[13] = 0.0
        rows.append(raw)
    arr = np.array(rows)
    mean = np.array(bundle["scaler_parameters"]["mean"])
    scale = np.array(bundle["scaler_parameters"]["scale"])
    features = (arr - mean) / scale
    return {
        "candidate_ids": bundle["candidate_vocabulary"],
        "feature_names": FEATURES,
        "raw_features": arr.tolist(),
        "features": features.tolist(),
        "interpreted_evidence": ev,
        "sensory_attribute_state": {
            "observed_or_supported_attributes": sorted(attrs),
            "predicted_latent_memberships": [],
            "cluster_status": "NOT_USED",
            "measured_attribute_truth_used": False,
        },
        "cluster_membership": {},
    }


def compute_scores(encoded, bundle):
    matrix = np.array(encoded["features"])
    w = np.array(bundle["model_parameters"]["weights"])
    score = matrix @ w
    return [
        {
            "candidate_id": c,
            "score": float(s),
            "components": {n: float(x * y) for n, x, y in zip(FEATURES, row, w)},
        }
        for c, s, row in zip(encoded["candidate_ids"], score, matrix)
    ]


def rank_candidates(state, bundle):
    enc = encode_features(state, bundle)
    rows = compute_scores(enc, bundle)
    ev = enc["interpreted_evidence"]
    explicit = set(ev["confirmed"])
    feedback = set(ev["feedback"])
    raw_order = sorted(rows, key=lambda r: (-r["score"], r["candidate_id"]))
    raw_ranks = {r["candidate_id"]: i for i, r in enumerate(raw_order, 1)}
    rows.sort(
        key=lambda r: (
            -int(r["candidate_id"] in explicit),
            -r["score"],
            r["candidate_id"],
        )
    )
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["raw_rank"] = raw_ranks[r["candidate_id"]]
        r["postprocessing_promoted"] = i < r["raw_rank"]
        r["explicit"] = r["candidate_id"] in explicit
        r["feedback_selected"] = r["candidate_id"] in feedback
        ca = set(bundle["candidate_attributes"].get(r["candidate_id"], []))
        rejected = r["candidate_id"] in ev["explicit_none"] or bool(
            ca & set(ev["negative_broad"])
        )
        r["support_state"] = (
            "CONFLICTING_EXPLICIT_EVIDENCE"
            if rejected and r["explicit"]
            else (
                "EXPLICITLY_REJECTED_WITHIN_EXPOSURE"
                if rejected
                else (
                    "SPECIFICALLY_OBSERVED"
                    if r["explicit"]
                    else (
                        "BROADLY_COMPATIBLE_NOT_CONFIRMED"
                        if ca & set(ev["broad"])
                        else "UNOBSERVED_CANDIDATE"
                    )
                )
            )
        )
        r["specific_confirmation_eligible"] = (
            r["candidate_id"].startswith("sensory.") and r["explicit"] and not rejected
        )
    return rows


def recompute(state, bundle):
    s = copy.deepcopy(state)
    enc = encode_features(s, bundle)
    s["interpreted_evidence"] = enc["interpreted_evidence"]
    s["sensory_attribute_state"] = enc["sensory_attribute_state"]
    s["predicted_context_attributes"] = estimate_context_attributes(
        s["context"], bundle.get("context_attribute_models", {})
    )
    s["context_attributes_used_for_descriptor_scoring"] = False
    s["cluster_membership"] = enc["cluster_membership"]
    s["features"] = enc["features"]
    s["candidate_scores"] = rank_candidates(s, bundle)
    s["candidate_support"] = {
        r["candidate_id"]: {
            "direct": r["explicit"],
            "feedback": r["feedback_selected"],
            "source_group_count": bundle["statistics"]["counts"].get(
                r["candidate_id"], 0
            ),
        }
        for r in s["candidate_scores"]
    }
    s["remaining_question_slots"] = [
        q
        for q in ["Q" + str(i) for i in range(6 if s["path"] == "P4" else 5)]
        if q not in s["answers_by_question"] and q not in s["skipped_slots"]
    ]
    if s["final_comparison"]:
        s["current_stage"] = "FINAL_RESULT"
    elif "Q4" in s["answers_by_question"]:
        s["current_stage"] = (
            "PRELIMINARY_RESULT"
            if s["path"] != "P4"
            or "Q5" in s["answers_by_question"]
            or "Q5" in s["skipped_slots"]
            else "CLOSING_STAGE"
        )
    elif "Q1" in s["answers_by_question"]:
        s["current_stage"] = (
            "INITIAL_EXTRACTION"
            if len(s["answers_by_question"]) == 2
            else "CORRECTION_STAGE"
        )
    elif "Q0" in s["answers_by_question"]:
        s["current_stage"] = "INITIAL_EXTRACTION_PENDING_Q1"
    else:
        s["current_stage"] = "CONTEXT"
    return s


def make_instance(slot, question, state, bundle):
    q = copy.deepcopy(question)
    q["slot"] = slot
    q["question_id"] = (
        "qi:" + digest([bundle["bundle_id"], slot, q["axis"], q["options"]])[:20]
    )
    q["shown_option_ids"] = [o["id"] for o in q["options"]]
    if not 1 <= len(q["options"]) <= 4:
        raise ValueError("ORDINARY_OPTION_BUDGET")
    return q


def update_joint_state(state, answer, bundle):
    check_bundle(bundle)
    if state["model_version"] != bundle["bundle_id"]:
        raise ValueError("STATE_MODEL_VERSION_MISMATCH")
    if state["final_comparison"]:
        raise ValueError("FINAL_RESULT_IS_TERMINAL")
    required = {
        "slot",
        "question_id",
        "axis",
        "shown_option_ids",
        "selected_option_ids",
        "state",
    }
    if not isinstance(answer, dict) or set(answer) != required:
        raise ValueError("ANSWER_SCHEMA_MISMATCH")
    slot = answer["slot"]
    if slot not in ["Q" + str(i) for i in range(6)]:
        raise ValueError("Q0_Q5_ONLY")
    if not isinstance(answer["state"], str) or answer["state"] not in STATES:
        raise ValueError("INVALID_ANSWER_STATE")
    for key in ["shown_option_ids", "selected_option_ids"]:
        x = answer[key]
        if (
            not isinstance(x, list)
            or any(not isinstance(v, str) for v in x)
            or len(x) != len(set(x))
        ):
            raise ValueError("OPTION_IDS_MUST_BE_UNIQUE")
    if not 1 <= len(answer["shown_option_ids"]) <= 4 or not set(
        answer["selected_option_ids"]
    ) <= set(answer["shown_option_ids"]):
        raise ValueError("OPTION_BUDGET_OR_SUBSET_ERROR")
    if (answer["state"] == "SELECTED") != bool(answer["selected_option_ids"]):
        raise ValueError("SELECTION_STATE_MISMATCH")
    old = state["answers_by_question"].get(slot)
    if old:
        question = {
            k: old[k]
            for k in ["slot", "question_id", "axis", "shown_option_ids", "options"]
        }
        if "classification_scope" in old:
            question["classification_scope"] = old["classification_scope"]
    else:
        next_q = select_next_question(state, bundle)
        if next_q["action"] != "ASK" or next_q["question"]["slot"] != slot:
            raise ValueError("QUESTION_SLOT_NOT_CURRENT")
        question = next_q["question"]
    if (
        answer["question_id"] != question["question_id"]
        or answer["axis"] != question["axis"]
        or answer["shown_option_ids"] != question["shown_option_ids"]
    ):
        raise ValueError("QUESTION_INSTANCE_NOT_ACTUALLY_EXPOSED")
    a = {
        **copy.deepcopy(answer),
        "selected_option_ids": sorted(answer["selected_option_ids"]),
        "options": question["options"],
    }
    if "classification_scope" in question:
        a["classification_scope"] = question["classification_scope"]
    if old == a:
        return copy.deepcopy(state)
    s = copy.deepcopy(state)
    s["answers_by_question"][slot] = a
    s.pop("pending_question", None)
    # Correcting existing evidence recomputes all active effects; it does not
    # reopen skipped slots or invent another ordinary question.
    if not old:
        if slot == "Q4" and "Q3" not in s["answers_by_question"]:
            s["skipped_slots"] = sorted(set(s["skipped_slots"]) | {"Q3"})
    after = recompute(s, bundle)
    before_rows = {r["candidate_id"]: r for r in state["candidate_scores"]}
    after["last_answer_update"] = []
    groups = {
        "context_component": ["context_c0", "context_c1"],
        "direct_answer_component": [
            "specific_direct",
            "broad_candidate_direct",
            "feedback_direct",
        ],
        "semantic_component": [
            "broad_related_support",
            "cooccurrence_mean",
            "cooccurrence_max",
            "source_support_log",
            "exposed_rejection",
            "cluster_affinity",
            "attribute_overlap",
            "feedback_association",
        ],
        "interaction_component": ["answer_pair_affinity", "context_answer_interaction"],
    }
    evidence_ids = sorted(
        {r["evidence_id"] for r in after["interpreted_evidence"]["relations"]}
    )
    for row in after["candidate_scores"]:
        before = before_rows[row["candidate_id"]]
        after["last_answer_update"].append(
            {
                "question_id": a["question_id"],
                "shown_option_ids": a["shown_option_ids"],
                "selected_option_ids": a["selected_option_ids"],
                "candidate_id": row["candidate_id"],
                "score_before": before["score"],
                "score_after": row["score"],
                "rank_before": before["rank"],
                "rank_after": row["rank"],
                **{
                    key: sum(
                        row["components"][n] - before["components"][n] for n in names
                    )
                    for key, names in groups.items()
                },
                "evidence_ids": evidence_ids,
                "update_reason": (
                    "REPLACE_PREVIOUS_ANSWER" if old else "ADD_NEW_ANSWER"
                )
                + "; FULL_RECOMPUTE_NO_ACCUMULATION",
                "component_semantics": "DELTA_FROM_PREVIOUS_STATE; base prior unchanged",
            }
        )
    return after


def finalize_result(state, bundle):
    s = (
        copy.deepcopy(state)
        if state.get("mechanical_f1_rows")
        else recompute(state, bundle)
    )
    plan = select_next_question(s, bundle)
    if plan["action"] == "PRELIMINARY_RESULT" and "Q5" not in s["answers_by_question"]:
        s["skipped_slots"] = sorted(
            set(s["skipped_slots"]) | ({"Q5"} if s["path"] == "P4" else set())
        )
        s["current_stage"] = "PRELIMINARY_RESULT"
        s["remaining_question_slots"] = []
    rows = s["candidate_scores"]
    eligible = [
        r
        for r in rows
        if bundle["candidate_rights"].get(r["candidate_id"]) == "ADMITTED"
    ]
    main = eligible[:5]
    secondary = eligible[5:8]
    exposure = None
    if s["current_stage"] == "PRELIMINARY_RESULT":
        ids = [r["candidate_id"] for r in main + secondary]
        exposure = {
            "candidate_ids": ids,
            "generation_version": bundle["bundle_id"],
            "state_hash": digest(
                [s["context"], s["answers_by_question"], bundle["bundle_id"]]
            ),
            "eligible_for_final_comparison": 3 <= len(ids) <= 8,
        }
        s["exposure"] = exposure
    return {
        "state": s,
        "main": main,
        "secondary": secondary,
        "stage": s["current_stage"],
        "next": plan,
        "exposure": exposure,
        "explicit_overflow": max(0, len(s["interpreted_evidence"]["specific"]) - 8),
        "evidence_scope": "PROFESSIONAL_RECORD_RECOVERY_PROXY; no independent real answer validation",
    }


def apply_final_comparison(
    state,
    exposed_candidates,
    selected_candidates,
    bundle,
    *,
    feedback_source,
    generation_version,
    mode="F2",
):
    check_bundle(bundle)
    if state["final_comparison"]:
        raise ValueError("FINAL_COMPARISON_ALREADY_USED")
    if feedback_source not in {"REAL_HUMAN", "SIMULATED"}:
        raise ValueError("FEEDBACK_SOURCE_REQUIRED")
    if mode not in {"F1", "F2"}:
        raise ValueError("FEEDBACK_MODE")
    result = finalize_result(state, bundle)
    exposure = result["exposure"]
    if not exposure or not exposure["eligible_for_final_comparison"]:
        raise ValueError("FINAL_COMPARISON_REQUIRES_PRELIMINARY_3_TO_8")
    if (
        generation_version != bundle["bundle_id"]
        or exposed_candidates != exposure["candidate_ids"]
    ):
        raise ValueError("EXPOSURE_OR_GENERATION_VERSION_MISMATCH")
    if (
        not isinstance(selected_candidates, list)
        or any(not isinstance(c, str) for c in selected_candidates)
        or len(selected_candidates) != len(set(selected_candidates))
        or not set(selected_candidates) <= set(exposed_candidates)
    ):
        raise ValueError("FEEDBACK_SUBSET_ERROR")
    s = result["state"]
    s["final_comparison"] = {
        "exposed_candidates": list(exposed_candidates),
        "selected_candidates": sorted(selected_candidates),
        "feedback_source": feedback_source,
        "generation_version": generation_version,
        "mode": mode,
    }
    if mode == "F2":
        return recompute(s, bundle)
    # F1 mechanically reorders only. Preserve all nonselected relative ranks.
    old = copy.deepcopy(s["candidate_scores"])
    chosen = set(selected_candidates)
    old.sort(key=lambda r: -int(r["candidate_id"] in chosen))
    for i, r in enumerate(old, 1):
        r["rank"] = i
        r["feedback_selected"] = r["candidate_id"] in chosen
    s["current_stage"] = "FINAL_RESULT"
    s["candidate_scores"] = old
    s["mechanical_f1_rows"] = old
    return s


def replay(payload, bundle, plan=True):
    allowed = {
        "contract_version",
        "context",
        "path",
        "policy",
        "answers",
        "final_comparison",
    }
    if (
        not isinstance(payload, dict)
        or set(payload) - allowed
        or payload.get("contract_version") != VERSIONS["contract_version"]
        or "context" not in payload
    ):
        raise ValueError("REQUEST_CONTRACT_VERSION_MISMATCH")
    if not isinstance(payload.get("answers", []), list):
        raise ValueError("ANSWERS_MUST_BE_ARRAY")
    s = initial_state(
        payload["context"],
        bundle,
        payload.get("path", "P1"),
        payload.get("policy", "fixed"),
    )
    for batch in payload.get("answers", []):
        for a in (batch if isinstance(batch, list) else [batch]):
            s = update_joint_state(s, a, bundle)
    if payload.get("final_comparison"):
        f = payload["final_comparison"]
        if not isinstance(f, dict) or set(f) != {
            "exposed_candidates",
            "selected_candidates",
            "feedback_source",
            "generation_version",
        }:
            raise ValueError("FINAL_COMPARISON_SCHEMA_MISMATCH")
        s = apply_final_comparison(
            s,
            f["exposed_candidates"],
            f["selected_candidates"],
            bundle,
            feedback_source=f["feedback_source"],
            generation_version=f["generation_version"],
        )
    elif "final_comparison" in payload:
        raise ValueError("FINAL_COMPARISON_MUST_BE_OBJECT")
    return s


def run(payload, bundle):
    s = replay(payload, bundle)
    result = finalize_result(s, bundle)
    if s.get("mechanical_f1_rows"):
        result["main"] = s["mechanical_f1_rows"][:5]
        result["secondary"] = s["mechanical_f1_rows"][5:8]
    return result


def evaluation_entry(payload, bundle):
    # Deliberately no lower-level shortcut: evaluation returns the live result.
    return run(payload, bundle)


def select_next_question(state, bundle):
    if state.get("pending_question"):
        return {
            "action": "ASK",
            "reason": "REGISTERED_FOUNDATION_CHECK",
            "question": copy.deepcopy(state["pending_question"]),
        }
    from flavor_planning import plan_stage

    return plan_stage(state, bundle)


def expose_question(state, slot, question, bundle):
    """Expose a backend-generated registered question within the current slot."""
    planned = select_next_question(state, bundle)
    if planned["action"] != "ASK" or planned["question"]["slot"] != slot:
        raise ValueError("QUESTION_SLOT_NOT_CURRENT")
    if question["axis"] in {a["axis"] for a in state["answers_by_question"].values()}:
        raise ValueError("QUESTION_AXIS_ALREADY_USED")
    instance = make_instance(slot, question, state, bundle)
    updated = copy.deepcopy(state)
    updated["pending_question"] = instance
    return updated
