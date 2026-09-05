"""Shared v2 payload -> evidence -> features -> scores -> result, used in every mode."""

from __future__ import annotations
import copy, hashlib, json, math
import numpy as np
from flavor_backend import C0, C1, validate_context
from flavor_context import CONTEXT_VERSION, estimate_context_attributes

VERSIONS = {
    "contract_version": "sequential.v2",
    "feature_spec_version": "shared-candidate.v2",
    "context_mapping_version": CONTEXT_VERSION,
    "question_bank_version": "limited-four-options.v2",
    "semantic_version": "typed-support.v2",
    "cluster_version": "overlapping-attributes.v2",
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
    "unsupported_specificity",
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
    if len(bundle["candidate_vocabulary"]) != len(set(bundle["candidate_vocabulary"])):
        raise ValueError("DUPLICATE_CANDIDATE")
    return bundle


def initial_state(context, bundle, path="P1", policy="fixed"):
    check_bundle(bundle)
    validate_context(context)
    if path not in PATHS or policy not in POLICIES:
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
    direct = set()
    broad = set()
    none = set()
    shown = set()
    unique = []
    for slot, a in sorted(state["answers_by_question"].items()):
        opts = {o["id"]: o for o in a["options"]}
        chosen = a["selected_option_ids"]
        all_broad = a["axis"].startswith("broad") and set(chosen) == set(
            a["shown_option_ids"]
        )
        for option_id in chosen:
            o = opts[option_id]
            shown.add(option_id)
            if o["kind"] == "specific":
                direct.add(option_id)
                unique.append(
                    {
                        "evidence_id": slot + ":" + option_id,
                        "concept_id": option_id,
                        "relation_type": "DIRECT_OBSERVATION",
                        "strength": 1.0,
                    }
                )
            elif not all_broad:
                broad.add(o["attribute"])
                unique.append(
                    {
                        "evidence_id": slot + ":" + option_id,
                        "concept_id": option_id,
                        "relation_type": "HIERARCHICAL_SUPPORT_NOT_CHILD_CONFIRMATION",
                        "strength": 1.0,
                    }
                )
        if a["state"] == "NONE_OF_THESE":
            none.update(a["shown_option_ids"])
    feedback = (
        set(state["final_comparison"]["selected_candidates"])
        if state["final_comparison"]
        else set()
    )
    # Leaf-to-parent information is one evidence unit. A repeated broad answer
    # adds no independent copy of support already supplied by explicit children.
    parents = {a for c in direct for a in bundle["candidate_attributes"].get(c, [])}
    independent_broad = broad - parents
    return {
        "specific": sorted(direct),
        "broad": sorted(broad),
        "independent_broad": sorted(independent_broad),
        "explicit_none": sorted(none),
        "feedback": sorted(feedback),
        "relations": unique,
        "all_broad_is_nondiscriminating": True,
    }


def encode_features(payload_or_state, bundle):
    check_bundle(bundle)
    if "answers_by_question" not in payload_or_state:
        state = replay(payload_or_state, bundle, plan=False)
    else:
        state = payload_or_state
    validate_context(state["context"])
    ev = evidence(state, bundle)
    observed = set(ev["specific"])
    broad = set(ev["independent_broad"])
    feedback = set(ev["feedback"])
    stats = bundle["statistics"]
    rows = []
    attrs = {
        a for c in observed for a in bundle["candidate_attributes"].get(c, [])
    } | broad
    cluster_vectors = [
        bundle["candidate_clusters"].get(c, []) for c in observed | feedback
    ]
    dim = bundle.get("cluster_dimension", 3)
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
        cv = np.array(bundle["candidate_clusters"].get(c, [0.0] * dim))
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
            float(leaf and bool(ca & broad) and not direct),
            0.0,
            0.0,
            max(pairs, default=0.0),
            0.0,
            affinity,
            len(ca & attrs) / max(len(ca), 1),
            float(c in feedback),
            float(np.mean(fba)) if fba else 0.0,
        ]
        # Descriptor records have no validated product C0/C1. Their components
        # are unsupported in THIS bundle and identically zero during fit/replay/live.
        # Source-specific numerical C0 predictions remain separately available.
        if bundle["model_kind"] == "M2_ADD":
            for i in [10, 11, 12, 13]:
                raw[i] = 0.0
        elif bundle["model_kind"] == "M2_JOINT":
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
            "predicted_latent_memberships": latent.tolist(),
            "measured_attribute_truth_used": False,
        },
        "cluster_membership": {
            c: bundle["candidate_clusters"].get(c, [])
            for c in bundle["candidate_vocabulary"]
        },
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
    explicit = set(ev["specific"])
    feedback = set(ev["feedback"])
    rows.sort(
        key=lambda r: (
            -int(r["candidate_id"] in feedback),
            -int(r["candidate_id"] in explicit),
            -r["score"],
            r["candidate_id"],
        )
    )
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["explicit"] = r["candidate_id"] in explicit
        r["feedback_selected"] = r["candidate_id"] in feedback
    return rows


def recompute(state, bundle):
    s = copy.deepcopy(state)
    enc = encode_features(s, bundle)
    s["interpreted_evidence"] = enc["interpreted_evidence"]
    s["sensory_attribute_state"] = enc["sensory_attribute_state"]
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
        for q in ["Q" + str(i) for i in range(6)]
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
    if set(answer) != required:
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
    else:
        from flavor_planning import select_next_question

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
    if old == a:
        return copy.deepcopy(state)
    s = copy.deepcopy(state)
    s["answers_by_question"][slot] = a
    # Correcting existing evidence recomputes all active effects; it does not
    # reopen skipped slots or invent another ordinary question.
    if not old:
        if slot == "Q4" and "Q3" not in s["answers_by_question"]:
            s["skipped_slots"] = sorted(set(s["skipped_slots"]) | {"Q3"})
    return recompute(s, bundle)


def finalize_result(state, bundle):
    from flavor_planning import plan_stage

    s = (
        copy.deepcopy(state)
        if state.get("mechanical_f1_rows")
        else recompute(state, bundle)
    )
    plan = plan_stage(s, bundle)
    if plan["action"] == "PRELIMINARY_RESULT" and "Q5" not in s["answers_by_question"]:
        s["skipped_slots"] = sorted(
            set(s["skipped_slots"]) | ({"Q5"} if s["path"] == "P4" else set())
        )
        s["current_stage"] = "PRELIMINARY_RESULT"
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
        s = apply_final_comparison(
            s,
            f["exposed_candidates"],
            f["selected_candidates"],
            bundle,
            feedback_source=f["feedback_source"],
            generation_version=f["generation_version"],
        )
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
