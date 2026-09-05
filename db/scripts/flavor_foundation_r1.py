"""Small M2 R1 sensory-profile models and one bounded corroboration role.

All numbers are uncalibrated relative support, never sensory probabilities.
The record-derived A/B/T protocol is a recovery proxy, not a user experiment.
Only this module's runtime encoder is used to fit, replay and evaluate profiles.
"""

from __future__ import annotations

import copy
from collections import Counter, defaultdict

import numpy as np
from scipy.optimize import lsq_linear
from sklearn.decomposition import NMF
from threadpoolctl import threadpool_limits

import flavor_sequential as legacy
import train_sequential as training

VERSION = "sensory-foundation.m2-r1.1"
PROXY = "DERIVED_RECORD_PROXY"
REPRESENTATIONS = (
    "explicit_attributes",
    "nmf_projection",
    "supervised_soft_profile",
)
DIMENSIONS = list(legacy.ATTRS)
_FIT_INPUT_CACHE = {}
DIMENSION_MEANING = {
    "fruity": "aroma association: fruity",
    "floral": "aroma association: floral",
    "sweet": "source-native sweet association; aroma/taste distinction unresolved",
    "nutty_cocoa": "compound aroma association; nutty and cocoa remain combined",
    "spices": "aroma association: spices",
    "roasted": "aroma association: roasted",
    "green_vegetative": "aroma association: green/vegetative",
    "sour_fermented": "compound source association; sour taste/fermentation unresolved",
    "taste": "legacy bitter association only; not a complete basic-taste profile",
}
# Fixed project-authored neutral catalogue. It is registered before held-out
# records are read. A choice is not a negation of unselected choices.
CHECK_CATALOG = [
    {
        "axis": "foundation.aroma.a",
        "prompt": "Which of these sensory associations do you notice, if any?",
        "attributes": ["fruity", "floral", "sweet", "nutty_cocoa"],
    },
    {
        "axis": "foundation.aroma.b",
        "prompt": "Which of these sensory associations do you notice, if any?",
        "attributes": ["floral", "spices", "roasted", "green_vegetative"],
    },
    {
        "axis": "foundation.aroma.c",
        "prompt": "Which of these sensory associations do you notice, if any?",
        "attributes": ["fruity", "nutty_cocoa", "roasted", "green_vegetative"],
    },
    {
        "axis": "foundation.associations.d",
        "prompt": "Which of these sensory associations do you notice, if any?",
        "attributes": ["fruity", "sweet", "sour_fermented", "taste"],
    },
    {
        "axis": "foundation.associations.e",
        "prompt": "Which of these sensory associations do you notice, if any?",
        "attributes": ["floral", "roasted", "sour_fermented", "taste"],
    },
]


def split_episode(record):
    """Partition concepts only after a caller has assigned complete coffee groups.

    The hash assignment never consults model predictions or performance. Related
    broad concepts are removed from T once at construction, identically in all
    variants; no case is removed when the remaining target happens to be empty.
    """
    ordered = sorted(
        set(record["targets"]),
        key=lambda c: legacy.digest([VERSION, record["group_id"], c]),
    )
    n_a = max(1, len(ordered) // 3) if ordered else 0
    n_b = max(1, len(ordered) // 3) if len(ordered) > 1 else 0
    a, b, target = ordered[:n_a], ordered[n_a : n_a + n_b], ordered[n_a + n_b :]
    closure = {
        "attribute." + dim
        for concept in a + b
        for dim in legacy.PARENTS.get(concept, [])
    }
    target = [c for c in target if c not in closure]
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "evaluation_type": PROXY,
        "A": a,
        "B": b,
        "T": target,
        "relevance": {c: record["relevance"][c] for c in target},
        "context": {"c0": legacy.C0[0], "c1": "medium"},
        "context_status": "EXPLICIT_SIMULATION_SETTING_NOT_SOURCE_CONTEXT",
        "evidence_relationship": "SAME_RECORD_CONCEPT_PARTITION_NOT_INDEPENDENT_OBSERVATIONS",
        "target_excluded_derived_parent_count": len(
            closure & set(ordered[n_a + n_b :])
        ),
        "target_hash": legacy.digest(target),
    }


def _concept_state(concepts):
    return {
        "answers_by_question": {
            "Q0": {
                "selected_option_ids": list(concepts),
                "options": [
                    {
                        "id": c,
                        "kind": "broad" if c.startswith("attribute.") else "specific",
                        "attribute": (
                            c.split(".", 1)[1] if c.startswith("attribute.") else ""
                        ),
                    }
                    for c in concepts
                ],
            }
        },
        "final_comparison": None,
    }


def encode_observed(state, attributes):
    """Deduplicate concepts before encoding; question count is never a feature."""
    direct, broad, negative, units = set(), set(), set(), {}
    for answer in state.get("answers_by_question", {}).values():
        options = {o["id"]: o for o in answer["options"]}
        for concept in answer["selected_option_ids"]:
            option = options[concept]
            dims = attributes.get(concept, legacy.PARENTS.get(concept, []))
            if option["kind"] == "broad":
                dims = [option["attribute"]]
                broad.update(dims)
            else:
                direct.update(dims)
            units[concept] = sorted(dims)
        if answer.get("state") == "NONE_OF_THESE":
            for option in options.values():
                # Rejecting one specific child does not reject its entire
                # sensory parent. Only explicitly rejected broad choices form
                # dimension-level negative evidence.
                if option["kind"] == "broad":
                    negative.add(option["attribute"])
                    units["rejection:" + option["id"]] = [option["attribute"]]
    feedback = state.get("final_comparison") or {}
    for concept in feedback.get("selected_candidates", []):
        dims = attributes.get(concept, legacy.PARENTS.get(concept, []))
        if concept.startswith("sensory."):
            direct.update(dims)
        else:
            broad.update(dims)
        units[concept] = sorted(dims)
    # A semantic parent of direct evidence is the same information, not another
    # observation. Replaying its broad paraphrase is exactly idempotent.
    total_support = broad | direct
    x = np.asarray(
        [1.0]
        + [float(d in direct) for d in DIMENSIONS]
        + [float(d in total_support) for d in DIMENSIONS]
        + [float(d in negative) for d in DIMENSIONS]
    )
    return x, units, direct | broad


def attribute_labels(record):
    """Return targets and masks without converting missing mentions into zeros."""
    y = np.zeros(len(DIMENSIONS))
    mask = np.zeros(len(DIMENSIONS), dtype=bool)
    complete = np.zeros(len(DIMENSIONS), dtype=bool)
    if record.get("source_family") == "inera":
        # Existing source protocol: frequency out of nine assessors. Zeros in a
        # measured cell are real zeros; null cells stay unmeasured.
        for name, value in zip(
            record.get("attribute_names", []), record.get("attribute_values", [])
        ):
            if name in DIMENSIONS and value is not None:
                if not 0 <= float(value) <= 9:
                    raise ValueError("INVALID_INERA_FREQUENCY")
                j = DIMENSIONS.index(name)
                y[j], mask[j], complete[j] = float(value) / 9.0, True, True
    if not complete.any():
        for concept in record.get("targets", []):
            for dim in legacy.PARENTS.get(concept, []):
                if dim in DIMENSIONS:
                    j = DIMENSIONS.index(dim)
                    y[j], mask[j] = 1.0, True
    return y, mask, complete


def _training_vectors(records, bundle):
    import flavor_m2_r1 as backend

    key = legacy.digest(
        [
            bundle["bundle_id"],
            bundle["question_bank"],
            [(r["record_id"], r["group_id"], r["targets"]) for r in records],
        ]
    )
    if key not in _FIT_INPUT_CACHE:
        vectors = {}
        for record in records:
            _, states, _ = trajectory(record, bundle, backend, "V0")
            vectors[record["record_id"]] = [
                encode_observed(st, bundle["candidate_attributes"])[0] for st in states
            ]
        if len(_FIT_INPUT_CACHE) > 16:
            _FIT_INPUT_CACHE.clear()
        _FIT_INPUT_CACHE[key] = vectors
    return _FIT_INPUT_CACHE[key]


def fit_foundation(
    records, bundle, representation="explicit_attributes", rank=3, alpha=4.0
):
    if representation not in REPRESENTATIONS:
        raise ValueError("UNKNOWN_FOUNDATION_REPRESENTATION")
    if not records or any(r["split"] != "DEVELOPMENT" for r in records):
        raise ValueError("FOUNDATION_FIT_REQUIRES_TRAIN_DEVELOPMENT_ONLY")
    group_counts = Counter(r["group_id"] for r in records)
    source_counts = Counter(
        {r["group_id"]: r["source_family"] for r in records}.values()
    )
    xs, ys, masks, weights, complete_masks = [], [], [], [], []
    observed_vectors = _training_vectors(records, bundle)
    for record in records:
        y, mask, complete = attribute_labels(record)
        # Complete source labels are supervision, never runtime features. Both
        # before/after prefixes use only choices actually exposed by the same
        # budgeted runtime trajectory. Unexposed A/B concepts never enter X.
        for vector in observed_vectors[record["record_id"]]:
            xs.append(vector)
            ys.append(y)
            masks.append(mask)
            complete_masks.append(complete)
            weights.append(
                1.0
                / (
                    group_counts[record["group_id"]]
                    * source_counts[record["source_family"]]
                    * len(observed_vectors[record["record_id"]])
                )
            )
    x, y, mask = np.asarray(xs), np.asarray(ys), np.asarray(masks)
    complete = np.asarray(complete_masks)
    weights = np.asarray(weights)
    coefficients = np.zeros((x.shape[1], len(DIMENSIONS)))
    supported = []
    positive_stop = 1 + 2 * len(DIMENSIONS)
    soft_encoder = np.zeros((2 * len(DIMENSIONS), 0))
    with threadpool_limits(limits=1):
        for j, dim in enumerate(DIMENSIONS):
            # Without any measured absence/scale, positive-only frequency cannot
            # identify prevalence. Preserve the observation but do not fit an
            # all-high predictor to that dimension.
            if not complete[:, j].any():
                continue
            valid = mask[:, j]
            w = weights[valid] * np.where(complete[valid, j], 1.0, 0.15)
            w /= max(w.sum(), 1e-12)
            ridge = (
                np.eye(x.shape[1])
                * float(alpha)
                / max(len(set(r["group_id"] for r in records)), 1)
            )
            ridge[0, 0] = 1e-8
            design = np.vstack([np.sqrt(w[:, None]) * x[valid], np.sqrt(ridge)])
            target = np.concatenate([np.sqrt(w) * y[valid, j], np.zeros(x.shape[1])])
            fitted = lsq_linear(design, target, bounds=(0, np.inf), tol=1e-9)
            if not fitted.success:
                raise RuntimeError("NONNEGATIVE_FOUNDATION_FIT_FAILED")
            coefficients[:, j] = fitted.x
            supported.append(dim)
        if representation == "supervised_soft_profile":
            # A nonnegative low-rank approximation to the supervised response
            # map. It preserves positive-evidence monotonicity and is never
            # named as a discovered real sensory trait.
            if supported:
                factor = NMF(
                    n_components=min(rank, len(supported)),
                    init="nndsvda",
                    random_state=training.SEED,
                    max_iter=2000,
                    tol=1e-5,
                )
                soft_encoder = factor.fit_transform(coefficients[1:positive_stop])
                basis = factor.components_
                coefficients[1:positive_stop] = soft_encoder @ basis
            else:
                basis = np.zeros((0, len(DIMENSIONS)))
        else:
            basis = np.empty((0, len(DIMENSIONS)))
    nmf_components = np.zeros((0, len(DIMENSIONS)))
    if representation == "nmf_projection":
        old = bundle.get("cluster_model", {})
        if "components" not in old:
            _, old = training.clusters(records, bundle["candidate_vocabulary"])
        nmf_components = np.zeros((len(old["components"]), len(DIMENSIONS)))
        for i, dim in enumerate(old["attribute_names"]):
            if dim in DIMENSIONS:
                nmf_components[:, DIMENSIONS.index(dim)] = np.asarray(
                    old["components"]
                )[:, i]
    model = {
        "version": VERSION,
        "representation": representation,
        "dimensions": DIMENSIONS,
        "dimension_meaning": DIMENSION_MEANING,
        "supported_dimensions": supported,
        "coefficients": coefficients.tolist(),
        "soft_basis": basis.tolist(),
        "soft_encoder": soft_encoder.tolist(),
        "nmf_components": nmf_components.tolist(),
        "alpha": float(alpha),
        "rank": rank,
        "fusion_strength": 0.0,
        "exposed_negative_effect": -0.5,
        "exposed_negative_basis": "FIXED_SCOPE_LIMITED_SEMANTIC_CONSTRAINT_NOT_FITTED_FROM_UNMENTIONED_TARGETS; D0_HAS_NO_REAL_NONE_ANSWERS",
        "training_groups": sorted({r["group_id"] for r in records}),
        "source_support": dict(
            Counter({r["group_id"]: r["source_family"] for r in records}.values())
        ),
        "training_supervision": {
            "complete_native_frequency_cells": sum(
                int(attribute_labels(r)[2].sum()) for r in records
            ),
            "positive_only_cells": sum(
                int((attribute_labels(r)[1] & ~attribute_labels(r)[2]).sum())
                for r in records
            ),
            "unmentioned_is_negative": False,
            "unidentified_positive_only_dimensions_not_fitted": sorted(
                set(DIMENSIONS) - set(supported)
            ),
            "native_frequency_denominator": 9,
            "input_path": "ACTUALLY_EXPOSED_RUNTIME_TRAJECTORY_PREFIXES_SAME_ENCODER",
            "positive_evidence_constraint": "NONNEGATIVE_INCREMENT; SPECIFIC_AND_TOTAL_SUPPORT_ENCODING_PRESERVES_PARENT_IDEMPOTENCE",
        },
        "model_version": "foundation:"
        + legacy.digest(
            [
                VERSION,
                representation,
                coefficients.tolist(),
                sorted({r["group_id"] for r in records}),
            ]
        )[:20],
    }
    return model


def predict_foundation(state, bundle, model):
    if model.get("version") != VERSION or model.get("dimensions") != DIMENSIONS:
        raise ValueError("FOUNDATION_MODEL_VERSION_MISMATCH")
    x, units, observed = encode_observed(state, bundle["candidate_attributes"])
    positive_stop = 1 + 2 * len(DIMENSIONS)
    values = np.clip(
        x[:positive_stop] @ np.asarray(model["coefficients"])[:positive_stop], 0, 1
    )
    latent = []
    if model["representation"] == "nmf_projection":
        h = np.asarray(model["nmf_components"])
        latent = values @ h.T
        # The fixed nonnegative projection is monotone in positive evidence.
        # Per-dimension normalization is fitted from TRAIN factors, not inputs.
        norm = np.maximum(np.sum(h.T @ h, axis=0), 1e-12)
        values = np.clip((latent @ h) / norm, 0, 1)
        latent = latent.tolist()
    elif model["representation"] == "supervised_soft_profile":
        latent = (x[1:positive_stop] @ np.asarray(model["soft_encoder"])).tolist()
    values = np.clip(
        values + float(model["exposed_negative_effect"]) * x[positive_stop:], 0, 1
    )
    rejected = {d for d, value in zip(DIMENSIONS, x[positive_stop:]) if value}
    order = sorted(
        model["supported_dimensions"], key=lambda d: (-values[DIMENSIONS.index(d)], d)
    )
    return {
        "supported_dimensions": model["supported_dimensions"],
        "dimension_values": dict(zip(DIMENSIONS, values.tolist())),
        "scale_and_meaning": "0_TO_1_RELATIVE_SUPPORT_NOT_CALIBRATED_PROBABILITY_OR_TASTE_INTENSITY",
        "dimension_meaning": DIMENSION_MEANING,
        "observed_vs_inferred": {
            d: (
                "CONFLICTING_EXPLICIT_EVIDENCE"
                if d in rejected and d in observed
                else (
                    "EXPLICITLY_REJECTED_WITHIN_EXPOSURE"
                    if d in rejected
                    else (
                        "OBSERVED_OR_SEMANTICALLY_SUPPORTED"
                        if d in observed
                        else (
                            "INFERRED"
                            if d in model["supported_dimensions"]
                            else "NOT_IDENTIFIABLE"
                        )
                    )
                )
            )
            for d in DIMENSIONS
        },
        "rejected_dimensions": sorted(rejected),
        "evidence_unit_ids": sorted(units),
        "evidence_dimension_map": units,
        "source_support": model["source_support"],
        "competing_profile_hypotheses": [
            {"dimension": d, "support": float(values[DIMENSIONS.index(d)])}
            for d in order[:3]
        ],
        "unresolved_distinctions": [
            "sweet aroma versus sweet taste",
            "sour taste versus fermented aroma",
            "mouthfeel not represented",
            "same-record dimensions are not independent observations",
        ],
        "context_contribution": {
            "status": "NOT_ESTIMABLE",
            "scoring_effect": 0.0,
            "reason": "no validated production C0/C1 pairs in these descriptor records",
        },
        "latent_coordinates": latent,
        "latent_names": "UNNAMED_LEARNED_COORDINATES" if latent else None,
        "model_version": model["model_version"],
    }


def compatibility(profile, bundle):
    values = profile["dimension_values"]
    return {
        c: (
            float(
                np.mean(
                    [
                        values[d]
                        for d in bundle["candidate_attributes"].get(c, [])
                        if d in values
                    ]
                )
            )
            if bundle["candidate_attributes"].get(c)
            else 0.0
        )
        for c in bundle["candidate_vocabulary"]
    }


def rank_with_foundation(state, bundle, model, backend):
    profile = predict_foundation(state, bundle, model)
    support = compatibility(profile, bundle)
    rows = copy.deepcopy(backend.rank_candidates(state, bundle))
    strength = float(model.get("fusion_strength", 0))
    for row in rows:
        value = strength * support[row["candidate_id"]]
        row["score"] += value
        row["foundation_score"] = value
        row["components"]["foundation_support"] = value
    raw_ranks = {
        row["candidate_id"]: i
        for i, row in enumerate(
            sorted(rows, key=lambda row: (-row["score"], row["candidate_id"])), 1
        )
    }
    rows.sort(
        key=lambda row: (
            -int(row.get("explicit", False)),
            -row["score"],
            row["candidate_id"],
        )
    )
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
        row["raw_rank"] = raw_ranks[row["candidate_id"]]
        row["postprocessing_promoted"] = rank < row["raw_rank"]
    return rows, profile


def select_check_question(state, bundle, model, slot="Q3", option_count=4):
    if slot not in {"Q3", "Q4"} or slot != bundle.get("foundation_check_slot", "Q3"):
        raise ValueError("CHECK_SLOT_MUST_BE_PREREGISTERED_Q3_OR_Q4")
    if not {"Q0", "Q1", "Q2"} <= set(state["answers_by_question"]):
        raise ValueError("CHECK_REQUIRES_INITIAL_EXTRACTION_AND_Q2")
    if state.get("foundation_check"):
        raise ValueError("FOUNDATION_CHECK_ONCE_ONLY")
    if not 2 <= option_count <= 4:
        raise ValueError("CHECK_NEEDS_TWO_HYPOTHESES_WITHIN_OPTION_BUDGET")
    before = predict_foundation(state, bundle, model)
    hypotheses = before["competing_profile_hypotheses"]
    values = before["dimension_values"]
    observed_dims = {d for ds in before["evidence_dimension_map"].values() for d in ds}

    # Choice uses the frozen prediction and registered catalogue only, never B/T.
    def utility(q):
        dims = q["attributes"]
        represented = sum(h["dimension"] in dims for h in hypotheses[:2])
        new_view = sum(d not in observed_dims for d in dims)
        return represented, new_view, sum(values[d] for d in dims), q["axis"]

    entry = max(CHECK_CATALOG, key=utility)
    preferred = sorted(
        entry["attributes"],
        key=lambda d: (
            -int(d in [h["dimension"] for h in hypotheses[:2]]),
            -int(d not in observed_dims),
            -values[d],
            d,
        ),
    )[:option_count]
    # Preserve catalogue order, with equal neutral wording for every hypothesis.
    dimensions = [d for d in entry["attributes"] if d in preferred]
    question = {
        "axis": entry["axis"],
        "prompt": entry["prompt"],
        "role": "FOUNDATION_CHECK",
        "priority": 0,
        "tested_profile_dimensions": sorted(dimensions, key=lambda d: -values[d])[:2],
        "options": [
            {
                "id": "attribute." + d,
                "kind": "broad",
                "attribute": d,
                "label": DIMENSION_MEANING[d],
            }
            for d in dimensions
        ],
    }
    return question, before


def compare_check(before, after, answer_source=PROXY):
    before_units = before["evidence_dimension_map"]
    prior_dims = {
        d
        for unit, dims in before_units.items()
        if not unit.startswith("rejection:")
        for d in dims
    }
    new_ids = sorted(set(after["evidence_unit_ids"]) - set(before["evidence_unit_ids"]))
    novel_ids = [
        i
        for i in new_ids
        if i.startswith("rejection:")
        or set(after["evidence_dimension_map"][i]) - prior_dims
    ]
    related_details = [
        i for i in new_ids if i.startswith("sensory.") and i not in novel_ids
    ]
    new_rejections = [i for i in novel_ids if i.startswith("rejection:")]
    delta = max(
        abs(after["dimension_values"][d] - before["dimension_values"][d])
        for d in DIMENSIONS
    )
    if new_rejections:
        status = "REVISION_REQUIRED"
    elif not novel_ids:
        status = "NOT_IDENTIFIABLE_FROM_OBSERVED_DATA"
    else:
        lead_before = before["competing_profile_hypotheses"][:1]
        lead_after = after["competing_profile_hypotheses"][:1]
        status = (
            "REVISION_REQUIRED"
            if lead_before
            and lead_after
            and lead_before[0]["dimension"] != lead_after[0]["dimension"]
            else "CORROBORATED"
        )
    return {
        "status": status,
        "evaluation_type": answer_source,
        "evidence_status": (
            "NEW_EXPOSED_NEGATIVE_EVIDENCE"
            if new_rejections
            else (
                "NEW_RECORD_DERIVED_INFORMATION"
                if novel_ids
                else "NEW_RELATED_DEPENDENT" if related_details else "DERIVED_REUSE"
            )
        ),
        "new_evidence_unit_ids": sorted(novel_ids + related_details),
        "new_related_dependent_evidence_ids": related_details,
        "reused_or_dependent_evidence_ids": [i for i in new_ids if i not in novel_ids],
        "max_support_change": float(delta),
        "independence_claim": False,
        "real_answer_effect": (
            "NOT_EVALUATED"
            if answer_source != "REAL_ANSWER_EVALUATION"
            else "REQUIRES_INDEPENDENT_REFERENCE"
        ),
    }


def _answer(question, concepts, bundle):
    return training.answer_for(question, concepts, bundle)


def prepare_next(state, bundle, backend):
    """Shared live/replay/experiment planner; all selection depends on history."""
    next_action = backend.select_next_question(state, bundle)
    prepared = copy.deepcopy(state)
    if next_action["action"] != "ASK":
        return prepared, next_action
    if state.get("pending_question"):
        return prepared, next_action
    question = next_action["question"]
    replaced_axis = prepared.get("foundation_replaced_ordinary_axis")
    if replaced_axis and question["axis"] == replaced_axis:
        used = {a["axis"] for a in prepared["answers_by_question"].values()} | {
            replaced_axis
        }
        remaining = [
            q for q in bundle["question_bank"]["correction"] if q["axis"] not in used
        ]
        if not remaining:
            raise ValueError("NO_MATCHED_REMAINING_ORDINARY_QUESTION")
        prepared = backend.expose_question(
            prepared, question["slot"], remaining[0], bundle
        )
        next_action = backend.select_next_question(prepared, bundle)
        question = next_action["question"]
    model = bundle.get("foundation_model")
    if (
        model
        and bundle.get("foundation_check_enabled")
        and question["slot"] == bundle.get("foundation_check_slot", "Q3")
        and not prepared.get("foundation_check")
    ):
        count = min(4, len(question["options"]))
        if count < 2:
            prepared["foundation_check"] = {
                "status": "NOT_IDENTIFIABLE_FROM_OBSERVED_DATA",
                "reason": "MATCHED_SLOT_HAS_FEWER_THAN_TWO_OPTIONS",
            }
        else:
            replacement, before = select_check_question(
                prepared, bundle, model, question["slot"], count
            )
            prepared = backend.expose_question(
                prepared, question["slot"], replacement, bundle
            )
            prepared["foundation_before_check"] = copy.deepcopy(before)
            prepared["foundation_before_check_hash"] = legacy.digest(before)
            prepared["foundation_replaced_ordinary_axis"] = question["axis"]
            next_action = backend.select_next_question(prepared, bundle)
    return prepared, next_action


def update_state(
    state, answer, bundle, backend, answer_source="REAL_ANSWER_EVALUATION"
):
    before_hash = state.get("foundation_before_check_hash")
    updated = backend.update_joint_state(state, answer, bundle)
    if updated == state:
        return updated
    model = bundle.get("foundation_model")
    if model:
        updated["candidate_scores"], updated["foundation"] = rank_with_foundation(
            updated, bundle, model, backend
        )
        before_rows = {row["candidate_id"]: row for row in state["candidate_scores"]}
        after_rows = {row["candidate_id"]: row for row in updated["candidate_scores"]}
        for change in updated.get("last_answer_update", []):
            previous, current = (
                before_rows[change["candidate_id"]],
                after_rows[change["candidate_id"]],
            )
            change.update(
                score_before=previous["score"],
                score_after=current["score"],
                rank_before=previous["rank"],
                rank_after=current["rank"],
                foundation_component=current.get("foundation_score", 0.0)
                - previous.get("foundation_score", 0.0),
            )
        if answer["slot"] == bundle.get("foundation_check_slot", "Q3") and state.get(
            "foundation_before_check"
        ):
            check_state = copy.deepcopy(updated)
            check_state["answers_by_question"] = {
                slot: value
                for slot, value in updated["answers_by_question"].items()
                if slot <= answer["slot"]
            }
            check_profile = predict_foundation(check_state, bundle, model)
            updated["foundation_check"] = compare_check(
                state["foundation_before_check"], check_profile, answer_source
            )
            updated["foundation_immediately_after_check"] = check_profile
            if legacy.digest(updated["foundation_before_check"]) != before_hash:
                raise AssertionError("FROZEN_FOUNDATION_MUTATED")
    return updated


def initial_state(context, bundle, backend, path="P1", policy="fixed"):
    if bundle.get("foundation_check_enabled") and path != "P1":
        raise ValueError("FOUNDATION_CHECK_VARIANT_REQUIRES_PREREGISTERED_P1_PATH")
    state = backend.initial_state(context, bundle, path, policy)
    if bundle.get("foundation_model"):
        state["candidate_scores"], state["foundation"] = rank_with_foundation(
            state, bundle, bundle["foundation_model"], backend
        )
    return state


def trajectory(record, bundle, backend, variant="V1", episode=None):
    if variant not in {"V0", "V1", "V2"}:
        raise ValueError("UNKNOWN_FOUNDATION_VARIANT")
    ep = split_episode(record) if episode is None else copy.deepcopy(episode)
    active = copy.deepcopy(bundle)
    if variant == "V0":
        active.pop("foundation_model", None)
    active["foundation_check_enabled"] = variant == "V2"
    state = initial_state(ep["context"], active, backend, "P1", "fixed")
    answers, states = [], [copy.deepcopy(state)]
    while True:
        state, nxt = prepare_next(state, active, backend)
        if nxt["action"] != "ASK":
            break
        q = nxt["question"]
        # T is deliberately absent from answer generation at every stage. B is
        # revealed only at Q3 and remains available for ordinary later questions.
        visible = (
            ep["A"]
            if q["slot"] in {"Q0", "Q1", "Q2"}
            else ep["B"] if q["slot"] == "Q3" else ep["A"] + ep["B"]
        )
        answer = _answer(q, visible, active)
        state = update_state(state, answer, active, backend, PROXY)
        answers.append(answer)
        states.append(copy.deepcopy(state))
        if len(answers) > 5:
            raise AssertionError("P1_FIVE_QUESTION_BUDGET")
    return ep, states, answers


def run(payload, bundle, backend=None):
    """Reloadable live entry: exactly the same planning/encoding/scoring path."""
    if backend is None:
        import flavor_m2_r1 as backend
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
        or payload.get("contract_version") != backend.VERSIONS["contract_version"]
        or "context" not in payload
    ):
        raise ValueError("REQUEST_CONTRACT_VERSION_MISMATCH")
    if not isinstance(payload.get("answers", []), list):
        raise ValueError("ANSWERS_MUST_BE_ARRAY")
    state = initial_state(
        payload["context"],
        bundle,
        backend,
        payload.get("path", "P1"),
        payload.get("policy", "fixed"),
    )
    for batch in payload.get("answers", []):
        for answer in batch if isinstance(batch, list) else [batch]:
            if not isinstance(answer, dict):
                raise ValueError("ANSWER_SCHEMA_MISMATCH")
            if answer.get("slot") not in state["answers_by_question"]:
                state, nxt = prepare_next(state, bundle, backend)
                if nxt["action"] != "ASK":
                    raise ValueError("ANSWER_AFTER_PRELIMINARY_RESULT")
            state = update_state(state, answer, bundle, backend)
    feedback = payload.get("final_comparison")
    if feedback:
        if not isinstance(feedback, dict) or set(feedback) != {
            "exposed_candidates",
            "selected_candidates",
            "feedback_source",
            "generation_version",
        }:
            raise ValueError("FINAL_COMPARISON_SCHEMA_MISMATCH")
        state = apply_final_comparison(
            state,
            feedback["exposed_candidates"],
            feedback["selected_candidates"],
            bundle,
            backend,
            feedback_source=feedback["feedback_source"],
            generation_version=feedback["generation_version"],
        )
    elif "final_comparison" in payload:
        raise ValueError("FINAL_COMPARISON_MUST_BE_OBJECT")
    return finalize_result(state, bundle, backend)


def finalize_result(state, bundle, backend):
    result = backend.finalize_result(state, bundle)
    if bundle.get("foundation_model"):
        rows, profile = rank_with_foundation(
            state, bundle, bundle["foundation_model"], backend
        )
        if state.get("mechanical_f1_rows"):
            rows = copy.deepcopy(state["mechanical_f1_rows"])
        result["state"]["candidate_scores"] = rows
        result["state"]["foundation"] = profile
        eligible = [
            r
            for r in rows
            if bundle["candidate_rights"].get(r["candidate_id"]) == "ADMITTED"
        ]
        result["main"], result["secondary"] = eligible[:5], eligible[5:8]
        if result["exposure"]:
            ids = [r["candidate_id"] for r in result["main"] + result["secondary"]]
            result["exposure"]["candidate_ids"] = ids
            result["exposure"]["eligible_for_final_comparison"] = 3 <= len(ids) <= 8
            result["state"]["exposure"] = copy.deepcopy(result["exposure"])
    prepared, nxt = prepare_next(result["state"], bundle, backend)
    result["state"], result["next"] = prepared, nxt
    return result


def apply_final_comparison(
    state,
    exposed_candidates,
    selected_candidates,
    bundle,
    backend,
    *,
    feedback_source,
    generation_version,
    mode="F2",
):
    if state.get("final_comparison"):
        raise ValueError("FINAL_COMPARISON_ALREADY_USED")
    if feedback_source not in {"REAL_HUMAN", "SIMULATED"} or mode not in {"F1", "F2"}:
        raise ValueError("INVALID_FEEDBACK_SOURCE_OR_MODE")
    result = finalize_result(state, bundle, backend)
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
    updated = result["state"]
    updated["final_comparison"] = {
        "exposed_candidates": list(exposed_candidates),
        "selected_candidates": sorted(selected_candidates),
        "feedback_source": feedback_source,
        "generation_version": generation_version,
        "mode": mode,
    }
    if mode == "F1":
        rows = copy.deepcopy(updated["candidate_scores"])
        rows.sort(key=lambda r: -int(r["candidate_id"] in selected_candidates))
        for i, row in enumerate(rows, 1):
            row["rank"] = i
        updated["mechanical_f1_rows"] = rows
        updated["candidate_scores"] = rows
        updated["current_stage"] = "FINAL_RESULT"
        return updated
    updated = backend.recompute(updated, bundle)
    if bundle.get("foundation_model"):
        updated["candidate_scores"], updated["foundation"] = rank_with_foundation(
            updated, bundle, bundle["foundation_model"], backend
        )
    return updated


def fit_inner_bundles(records, bundle, folds=3):
    import train_m2_r1 as trainer

    split = training.split_groups(records, folds)
    result = []
    for fold in range(folds):
        train = [r for r in records if split[r["group_id"]] != fold]
        held = [r for r in records if split[r["group_id"]] == fold]
        if not train or not held:
            continue
        config = bundle.get("fit_receipt", {})
        stats = trainer.statistics(train, bundle["candidate_vocabulary"])
        attributes = {
            c: legacy.PARENTS.get(c, []) for c in bundle["candidate_vocabulary"]
        }
        bank_builder = (
            trainer.make_bank
            if "initial_pair_selection" in bundle["question_bank"]
            else training.make_bank
        )
        inner_bank = bank_builder(stats, attributes)
        model, receipt = trainer.fit(
            train,
            bundle["data_manifest_hash"],
            C=config.get("C", 1.0),
            vocabulary=bundle["candidate_vocabulary"],
            tag="foundation-inner-" + str(fold),
            bank_override=inner_bank,
            loss_mode=config.get("loss_mode", "layered"),
            task_weights=(
                config.get("task_weights")
                if config.get("loss_mode", "layered") != "legacy"
                else None
            ),
            canonical_broad_feedback=bundle.get("evidence_policy", {}).get(
                "canonical_broad_feedback", False
            ),
        )
        result.append(
            {"train": train, "held": held, "bundle": model, "fit_receipt": receipt}
        )
    return result


def cross_fit_foundation(
    records, bundle, representation, folds=3, alpha=4.0, rank=3, inner_bundles=None
):
    """OOF foundation predictions used to select downstream fusion strength."""
    import flavor_m2_r1 as backend

    rows, audit = [], []
    inner_bundles = (
        fit_inner_bundles(records, bundle, folds)
        if inner_bundles is None
        else inner_bundles
    )
    for inner in inner_bundles:
        train, held = inner["train"], inner["held"]
        local = copy.deepcopy(inner["bundle"])
        if representation == "nmf_projection":
            # Every factor transform is refit inside this training fold.
            _, local["cluster_model"] = training.clusters(
                train, bundle["candidate_vocabulary"]
            )
        model = fit_foundation(train, local, representation, rank, alpha)
        audit.append(
            {
                "train_groups": model["training_groups"],
                "prediction_groups": sorted({r["group_id"] for r in held}),
                "all_estimators_train_only": True,
                "base_model_id": local["bundle_id"],
                "base_model_fit_loss": inner["fit_receipt"]["loss_mode"],
                "input_path": "BUDGETED_SHARED_RUNTIME_TRAJECTORY",
                "downstream_score_path": "SAME_M2_LEARNED_CANDIDATE_SCORE_PLUS_FOUNDATION_SUPPORT",
            }
        )
        for record in held:
            ep, states, _ = trajectory(record, local, backend, "V0")
            for stage, state in [("before", states[3]), ("after", states[-1])]:
                profile = predict_foundation(state, local, model)
                rows.append(
                    {
                        "record_id": record["record_id"],
                        "group_id": record["group_id"],
                        "stage": stage,
                        "profile": profile,
                        "base_candidate_scores": copy.deepcopy(
                            state["candidate_scores"]
                        ),
                        "T": ep["T"],
                        "relevance": ep["relevance"],
                    }
                )
    return rows, audit


def fit_fusion(oof_rows, records, bundle, strengths=(0.0, 0.15)):
    """Select a bounded coefficient on OOF predictions, keeping zero as control.

    This positive-observation recovery objective does not claim unmentioned
    candidates are sensory negatives. Candidate vocabulary stays fixed.
    """
    lookup = {r["record_id"]: r for r in records}
    values = {}
    for strength in strengths:
        by_group = {}
        for row in oof_rows:
            record = lookup[row["record_id"]]
            ep = split_episode(record)
            visible = ep["A"] + ep["B"]
            exclude = set(visible) | {
                "attribute." + d for c in visible for d in legacy.PARENTS.get(c, [])
            }
            support = compatibility(row["profile"], bundle)
            # The base model, feature statistics and scaler were fitted without
            # this group. This is exactly rank_with_foundation's live score and
            # explicit-evidence ordering, not a surrogate frequency-prior score.
            candidate_rows = sorted(
                row["base_candidate_scores"],
                key=lambda r: (
                    -int(r.get("explicit", False)),
                    -(r["score"] + strength * support[r["candidate_id"]]),
                    r["candidate_id"],
                ),
            )
            rank = [r["candidate_id"] for r in candidate_rows]
            recovery = [c for c in rank if c not in exclude]
            score = training.ndcg(recovery, ep["relevance"])
            by_group.setdefault(record["group_id"], []).append(score)
        values[str(strength)] = (
            float(np.mean([np.mean(v) for v in by_group.values()])) if by_group else 0.0
        )
    chosen = min(strengths, key=lambda a: (-values[str(a)], a))
    return float(chosen), {
        "candidate_strengths": list(strengths),
        "group_mean_oof_record_recovery_ndcg5": values,
        "selected_strength": float(chosen),
        "training_foundation_source": "CROSS_FITTED_PREDICTIONS_AND_CROSS_FITTED_M2_SCORES_FROM_ACTUAL_QUESTION_TRAJECTORIES",
        "objective": "POSITIVE_RECORD_RECOVERY_NOT_SENSORY_NEGATIVE_CLASSIFICATION",
        "zero_included": True,
    }


def evaluate_record(record, bundle, backend, variant):
    ep, states, answers = trajectory(record, bundle, backend, variant)
    final = states[-1]
    rank = [r["candidate_id"] for r in final["candidate_scores"]]
    visible = set(ep["A"] + ep["B"])
    exclude = visible | {
        "attribute." + d for c in visible for d in legacy.PARENTS.get(c, [])
    }
    recovery = [c for c in rank if c not in exclude]
    target = set(ep["T"])
    direct = set(final["interpreted_evidence"]["specific"])
    row = {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "variant": variant,
        "evaluation_type": PROXY,
        "ndcg5": training.ndcg(recovery, ep["relevance"]),
        "recall5": len(set(recovery[:5]) & target) / len(target) if target else 0.0,
        "recall8": len(set(recovery[:8]) & target) / len(target) if target else 0.0,
        "target_count": len(target),
        "empty_target_kept_in_full_denominator": not bool(target),
        "coverage": bool(rank),
        "candidate_target_coverage": (
            len(target & set(bundle["candidate_vocabulary"])) / len(target)
            if target
            else 0.0
        ),
        "direct_retention8": (
            len(direct & set(rank[:8])) / len(direct) if direct else None
        ),
        "question_count": len(answers),
        "option_budget": sum(len(a["shown_option_ids"]) for a in answers),
        "target_hash": ep["target_hash"],
        "direct_A_B_hits8": len(set(rank[:8]) & visible),
        "check": final.get("foundation_check"),
        "ranking": rank,
        "recovery_ranking": recovery,
        "episode": ep,
        "answers": answers,
    }
    model = bundle.get("foundation_model")
    if model:
        y, _, complete = attribute_labels(record)
        profile = predict_foundation(final, bundle, model)
        pred = np.array([profile["dimension_values"][d] for d in DIMENSIONS])
        row["measured_attribute_mae"] = (
            float(np.mean(abs(pred[complete] - y[complete])))
            if complete.any()
            else None
        )
        row["attribute_error_basis"] = "COMPLETE_SOURCE_NATIVE_FREQUENCY_ONLY"
        if final.get("foundation_before_check"):
            before = final["foundation_before_check"]
            initial = max(
                before["dimension_values"], key=before["dimension_values"].get
            )
            immediately_after = predict_foundation(states[4], bundle, model)
            after = max(
                immediately_after["dimension_values"],
                key=immediately_after["dimension_values"].get,
            )
            # T is inspected only now, after the trajectory is terminal. These
            # semantic target-direction checks remain same-record proxies.
            t_dims = {d for c in ep["T"] for d in legacy.PARENTS.get(c, [])}
            row["direction_reference_status"] = (
                PROXY if t_dims else "NOT_IDENTIFIABLE_FROM_OBSERVED_DATA"
            )
            row["proxy_initial_direction_in_T"] = initial in t_dims if t_dims else None
            row["proxy_final_direction_in_T"] = after in t_dims if t_dims else None
            row["proxy_direction_corrected"] = (
                (initial not in t_dims and after in t_dims) if t_dims else None
            )
            row["proxy_correct_direction_lost"] = (
                (initial in t_dims and after not in t_dims) if t_dims else None
            )
            replayed_state = update_state(final, answers[3], bundle, backend, PROXY)
            replay = predict_foundation(replayed_state, bundle, model)
            row["duplicate_evidence_max_gain"] = max(
                abs(replay["dimension_values"][d] - profile["dimension_values"][d])
                for d in DIMENSIONS
            )
    return row


def summarize(rows):
    out = {
        "evaluation_type": PROXY,
        "real_answer_evaluation": "NOT_EVALUATED",
        "records": len(rows),
        "coffee_groups": len({r["group_id"] for r in rows}),
        "no_output_or_empty_target_cases_removed": False,
    }
    for metric in [
        "ndcg5",
        "recall5",
        "recall8",
        "coverage",
        "candidate_target_coverage",
        "direct_retention8",
        "measured_attribute_mae",
        "duplicate_evidence_max_gain",
    ]:
        by_group = {}
        for row in rows:
            if row.get(metric) is not None:
                by_group.setdefault(row["group_id"], []).append(float(row[metric]))
        out[metric] = (
            float(np.mean([np.mean(v) for v in by_group.values()]))
            if by_group
            else None
        )
    wrong = [r for r in rows if r.get("proxy_initial_direction_in_T") is False]
    right = [r for r in rows if r.get("proxy_initial_direction_in_T") is True]
    out["proxy_wrong_initial_count"] = len(wrong)
    out["proxy_correct_initial_count"] = len(right)
    out["proxy_direction_not_identifiable_count"] = sum(
        r.get("direction_reference_status") == "NOT_IDENTIFIABLE_FROM_OBSERVED_DATA"
        for r in rows
    )
    out["proxy_wrong_direction_correction_rate"] = (
        float(np.mean([r["proxy_direction_corrected"] for r in wrong]))
        if wrong
        else None
    )
    out["proxy_correct_direction_loss_rate"] = (
        float(np.mean([r["proxy_correct_direction_lost"] for r in right]))
        if right
        else None
    )
    return out


def evaluate_experiment(
    train,
    held,
    bundle,
    backend,
    representations=REPRESENTATIONS,
    folds=3,
    alpha=4.0,
    rank=3,
    extra_soft_ranks=(),
):
    if {r["group_id"] for r in train} & {r["group_id"] for r in held}:
        raise ValueError("FOUNDATION_TRAIN_EVALUATION_GROUP_LEAKAGE")
    baseline = [evaluate_record(r, bundle, backend, "V0") for r in held]
    result = {
        "version": VERSION,
        "evaluation_type": PROXY,
        "real_answer_evaluation": "NOT_EVALUATED",
        "models": {},
        "rows": {"V0": baseline},
        "summary": {"V0": summarize(baseline)},
        "training_audit": {},
    }
    inner_bundles = fit_inner_bundles(train, bundle, folds)
    specs = [
        (representation, rank, representation) for representation in representations
    ]
    specs.extend(
        ("supervised_soft_profile", value, "supervised_soft_profile_rank" + str(value))
        for value in extra_soft_ranks
        if value != rank
    )
    for representation, selected_rank, model_key in specs:
        oof, audit = cross_fit_foundation(
            train, bundle, representation, folds, alpha, selected_rank, inner_bundles
        )
        model = fit_foundation(train, bundle, representation, selected_rank, alpha)
        model["fusion_strength"], fusion_audit = fit_fusion(oof, train, bundle)
        active = copy.deepcopy(bundle)
        active["foundation_model"] = model
        result["models"][model_key] = model
        result["training_audit"][model_key] = {
            "cross_fit": audit,
            "fusion": fusion_audit,
        }
        for variant in ["V1", "V2"]:
            key = model_key + ":" + variant
            rows = [evaluate_record(r, active, backend, variant) for r in held]
            for reference, row in zip(baseline, rows):
                if (
                    reference["target_hash"] != row["target_hash"]
                    or reference["question_count"] != row["question_count"]
                    or reference["option_budget"] != row["option_budget"]
                ):
                    raise AssertionError(
                        "FOUNDATION_ABLATION_BUDGET_OR_TARGET_MISMATCH"
                    )
            result["rows"][key], result["summary"][key] = rows, summarize(rows)
    return result
