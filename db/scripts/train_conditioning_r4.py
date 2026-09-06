"""Small joint R4 scorer, then independently fitted nested Q3 key-case routing.

Fixed positive-mention retrieval normalizers are not sensory absence labels.
All fitting and individual trajectories remain in persistent private storage.
"""

from __future__ import annotations
import copy
import json
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
import alignment_metrics_r3 as metric
import flavor_m2_r1 as r1
import flavor_constraints_r3 as old_runtime
import train_m2_r1 as base_training
from train_constraints_r3 import (
    group_weights,
    macro,
    audit_expert,
    expert_training_groups,
)
from run_m2_r4 import ROOT, OUT, read, save, sha, now

VARIANTS = ["A0", "AK", "AR", "AKR"]
POLICIES = ["ALWAYS_ASK", "ALWAYS_SKIP", "R3_OLD", "KEY_CASE"]
RUN_DESTINATION = None


def work_directory(owner):
    return RUN_DESTINATION or (owner / "revisions/r4")


def protocol():
    return {
        "version": "m2-r4-small-joint-and-key-case.v1",
        "scoring_variants": VARIANTS,
        "configurations": "One fixed explicit shared-feature configuration, ridge10; no low-rank grid, triples or trees",
        "main_data": {
            "records": 211,
            "coffee_groups": 187,
            "outer_folds": 3,
            "inner_folds": 2,
            "deepest_base_folds": 2,
            "split": "UNCHANGED_R1_D0_GROUP_FOLDS",
        },
        "base_reuse": "R1 outer, R2 inner and R3 P1_INTERNAL deepest experts only after exact train-group/statistics/scale audit; source and model SHA retained",
        "objective": "SUM_coffee MEAN_record_stage conditional positive-mention CE plus ridge10/2 norm2; group weighted; no sensory negative labels",
        "scaler": "Train-only feature RMS with zero scale replaced by1; same serialized scale at runtime",
        "support": "At least3 distinct TRAIN coffee groups with nonzero feature; not derived row count",
        "training_stages": ["Q1", "Q2", "Q3", "Q4"],
        "candidate_availability": "Only actual base OOF scored IDs in training normalizer; full fixed outer candidate universe stays in evaluation",
        "direct_evidence": "Frozen base canonical evidence once; new deltas zero for explicit candidates; K1 and relation learned residual components, not additional fixed support bonuses",
        "optimizer": {
            "method": "L-BFGS-B",
            "maxiter": 200,
            "ftol": 1e-10,
            "gtol": 1e-7,
            "ridge": 10.0,
        },
        "score_selection": "Each outer TRAIN inner-held ASK Q4 group-macro raw_gap; tie within1e-12 simplicity A0 AK AR AKR; outer held never selects",
        "gain_generation": "Only after each scoring model frozen, inner-held ASK/SKIP with identical fixed targets; main answers derived solely from frozen A",
        "trigger": {
            "policies": POLICIES,
            "target": "loss_skip_minus_loss_ask >0.01",
            "practical_gain_threshold": 0.01,
            "C": 0.1,
            "model": "L2_LOGISTIC_LBFGS",
            "maxiter": 500,
            "positive_cost_factor": "min(20,1+max(gain,0)/0.01)",
            "other_cost_factor": 1,
            "decision_threshold": 0.5,
            "single_class": "Retain labelled cases and fit intercept-only constant class; no fabricated AUC",
            "missing_gain": "Excluded from supervised fit, retained in all-case coverage/cost",
            "selection": "Exactly one learned configuration; no threshold tuning; weights do not multiply independent sample counts",
            "probability_semantics": "Uncalibrated cost-weighted classifier score, not true gain probability",
        },
        "trigger_nesting": "Train on inner-held scorer outputs; each inner scorer uses deeper-held base outputs; outer held evaluates entire chosen scorer and trigger",
        "old_trigger": "Retained original R3 outer trigger weights/features, applied to same current information; current R4 scoring supplies both action outcomes",
        "uncertainty": "2000 paired coffee-label bootstrap of fixed OOF group losses; seed20260906; development scope only",
        "cost_curve": "Fixed policies and one KEY_CASE operating point; no posthoc NI margin or threshold grid",
        "historical_NI_0_02": "Historical operational comparison only; not a user-acceptable margin or promotion gate",
        "diagnostics": [
            "NDCG",
            "Recall",
            "explicit_retention",
            "unsubstantiated_specificity_proxy_not_true_error",
            "direction_coverage",
            "output_coverage",
            "missed_gain_sum_max_quantiles",
            "unnecessary_ask_options",
            "relation_funnel",
        ],
        "final_refit": "After development selection one chosen scorer re-fit on all original outer base OOF and trigger on selected-model outer-held branch labels; not last-fold model; no new confirmation",
        "auxiliary": {
            "only_variant": "AKR_AUX",
            "control": "AKR",
            "weight": 0.25,
            "loss": "main coffee-weighted CE +0.25*(main train groups/aux train groups)*aux coffee-weighted CE +same ridge10/2",
            "scope": "Same 22 features and original three coffee folds; main and independently recorded cross-grader held targets reported separately; auxiliary identity/target contract frozen separately before its first fit",
        },
        "default": "B2_UNCHANGED_FOUNDATION_CHECK_OFF",
    }


def fingerprint(owner, files, extra):
    return r1.digest(
        {
            "files": {
                str(p.relative_to(owner)) if p.is_relative_to(owner) else p.name: sha(p)
                for p in files
            },
            "extra": extra,
        }
    )


def scalar_summary(rows):
    out = {}
    for key in [
        "raw_gap",
        "ndcg",
        "recall",
        "direct_retention",
        "available_source_mentions_retention",
        "specificity_unsupported_proxy",
        "direction_coverage",
        "output_count",
        "ordinary_questions",
        "ordinary_options",
    ]:
        out[key] = macro(rows, key)
    out.update(
        records=len(rows),
        coffee_groups=len({r["group_id"] for r in rows}),
        identifiable_records=sum(r["raw_gap"] is not None for r in rows),
        identifiable_groups=len(
            {r["group_id"] for r in rows if r["raw_gap"] is not None}
        ),
        empty_targets=sum(r["raw_gap"] is None for r in rows),
        output_failures=sum(r["output_count"] == 0 for r in rows),
    )
    return out


def paired(rows, left, right, key="raw_gap"):
    l = {r["record_id"]: r for r in rows if r["model"] == left}
    r = {x["record_id"]: x for x in rows if x["model"] == right}
    if set(l) != set(r):
        raise ValueError("PAIRED_IDS_DO_NOT_ALIGN")
    groups = defaultdict(list)
    diffs = []
    for identity in sorted(l):
        a, b = l[identity][key], r[identity][key]
        if a is None or b is None:
            continue
        diff = a - b
        groups[l[identity]["group_id"]].append(diff)
        diffs.append(diff)
    values = np.array([np.mean(v) for v in groups.values()])
    rng = np.random.default_rng(20260906)
    samples = (
        rng.choice(values, (2000, len(values))).mean(axis=1) if len(values) else []
    )
    return {
        "treatment": left,
        "control": right,
        "field": key,
        "difference": float(values.mean()) if len(values) else None,
        "paired_group_95_interval": (
            np.quantile(samples, [0.025, 0.975]).tolist() if len(values) else None
        ),
        "identifiable_groups": len(groups),
        "identifiable_records": len(diffs),
        "better_records": sum(x < -1e-12 for x in diffs),
        "worse_records": sum(x > 1e-12 for x in diffs),
        "tied_records": sum(abs(x) <= 1e-12 for x in diffs),
        "all_records": len(l),
        "scope": "FIXED_OOF_COFFEE_BOOTSTRAP_DEVELOPMENT_ONLY",
    }


def audit_reuse(path, fitting, validating):
    expert = read(path)
    report = audit_expert(expert, fitting, validating)
    return expert, {"model_sha256": sha(path), "role": path.name, **report}


def fit_key_case(rows, names, allowed, excluded):
    if set(allowed) & set(excluded):
        raise ValueError("TRIGGER_TRAIN_HELD_OVERLAP")
    if {r["group_id"] for r in rows} != set(allowed):
        raise ValueError("TRIGGER_ALL_TRAIN_CASES_REQUIRED")
    for row in rows:
        if row["group_id"] in row["scorer_training_groups"] or set(
            row["scorer_training_groups"]
        ) & set(excluded):
            raise ValueError("TRIGGER_SCORER_MUST_BE_OUT_OF_GROUP")
    known = [r for r in rows if r["gain"] is not None]
    X = np.array([[r["features"][n] for n in names] for r in known], float)
    y = np.array([r["gain"] > 0.01 for r in known], int)
    result = {
        "feature_names": names,
        "threshold": 0.5,
        "coefficients": [0.0] * len(names),
        "intercept": 0.0,
        "mean": [0.0] * len(names),
        "scale": [1.0] * len(names),
        "labelled_records": len(known),
        "all_records": len(rows),
        "labelled_groups": len({r["group_id"] for r in known}),
        "key_records": int(y.sum()),
        "key_groups": len({r["group_id"] for r in known if r["gain"] > 0.01}),
        "ties": sum(abs(r["gain"]) <= 1e-12 for r in known),
        "training_groups": sorted(allowed),
        "score_versions": sorted({r["scorer_bundle_id"] for r in rows}),
        "score_semantics": "UNCALIBRATED_COST_WEIGHTED_CLASSIFICATION",
    }
    if not len(known):
        result.update(
            constant_probability=0.0,
            fit_status="NO_IDENTIFIABLE_GAIN_FIXED_SKIP_NOT_LEARNED",
        )
        return result
    weights = group_weights(known)
    mean = np.average(X, axis=0, weights=weights)
    scale = np.sqrt(np.average((X - mean) ** 2, axis=0, weights=weights))
    scale[scale < 1e-12] = 1
    result.update(mean=mean.tolist(), scale=scale.tolist())
    if len(set(y)) < 2:
        result.update(
            constant_probability=float(y[0]),
            fit_status="SINGLE_CLASS_INTERCEPT_ONLY_NOT_DYNAMIC",
        )
        return result
    factors = np.array(
        [
            min(20, 1 + max(r["gain"], 0) / 0.01) if label else 1
            for r, label in zip(known, y, strict=True)
        ]
    )
    clf = LogisticRegression(C=0.1, solver="lbfgs", max_iter=500, random_state=20260906)
    clf.fit((X - mean) / scale, y, sample_weight=weights * factors)
    result.update(
        coefficients=clf.coef_[0].tolist(),
        intercept=float(clf.intercept_[0]),
        fit_status="FITTED_LOGISTIC_KEY_CASE",
        iterations=int(clf.n_iter_[0]),
        training_weight_sum=float(np.sum(weights * factors)),
    )
    return result


def runtime_module():
    import flavor_conditioning_r4

    return flavor_conditioning_r4


def model_bundle(
    expert,
    parameters=None,
    variant="A0",
    trigger=None,
    old=None,
    contract_sha="",
    tag="",
    lineage=None,
):
    return runtime_module().make_bundle(
        expert,
        model_parameters=parameters,
        trigger=trigger,
        r3_reference=old,
        contract_hash=contract_sha,
        tag=tag,
        selected_variant=variant,
        training_lineage=lineage,
    )


def source_episode(record, auxiliary=False):
    if not auxiliary:
        return base_training.visible_episode(record)
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "visible": record["A"],
        "later_visible": sorted(set(record["A"]) | set(record["B"])),
        "relevance": record["relevance"],
        "hidden": list(record["relevance"]),
        "context": {"c0": r1.C0[0], "c1": "medium"},
        "context_assignment_status": "EXPLICIT_SIMULATION_ONLY_NO_SOURCE_CONTEXT_LABEL",
        "information_origin": "INDEPENDENT_RECORDED_GRADER_REVELATION_NOT_SAME_PERSON_QA",
    }


def answer_view(episode, slot):
    return (
        episode.get("later_visible", episode["visible"])
        if slot in {"Q2", "Q3", "Q4"}
        else episode["visible"]
    )


def collect_rows(records, expert, auxiliary=False):
    rt = runtime_module()
    fitted = expert_training_groups(expert)
    if fitted & {r["group_id"] for r in records}:
        raise ValueError("SCORER_BASE_MUST_BE_GROUP_OOF")
    bundle = model_bundle(expert)
    rows = []
    for record in records:
        episode = source_episode(record, auxiliary)
        base = r1.initial_state(episode["context"], expert, "P1", "fixed")
        while True:
            nxt = r1.select_next_question(base, expert)
            if nxt["action"] != "ASK":
                break
            question = nxt["question"]
            answer = base_training.answer_for(
                question, answer_view(episode, question["slot"]), expert
            )
            base = r1.update_joint_state(base, answer, expert)
            if question["slot"] not in protocol()["training_stages"]:
                continue
            by_variant = {v: rt.features(base, bundle, v) for v in VARIANTS[1:]}
            sample = by_variant["AKR"]
            mapped = {r["candidate_id"]: r for r in sample["base_rows"]}
            indices = [
                i
                for i, c in enumerate(sample["candidate_ids"])
                if c.startswith("sensory.")
            ]
            ids = [sample["candidate_ids"][i] for i in indices]
            rows.append(
                {
                    "record_id": record["record_id"],
                    "group_id": record["group_id"],
                    "source_family": record["source_family"],
                    "slot": question["slot"],
                    "episode": episode,
                    "candidate_ids": ids,
                    "base_logits": [mapped[c]["score"] for c in ids],
                    "legal_mask": [sample["legal_mask"][i] for i in indices],
                    "features": {
                        v: [by_variant[v]["features"][i] for i in indices]
                        for v in VARIANTS[1:]
                    },
                    "feature_names": sample["feature_names"],
                    "base_expert_training_groups": sorted(fitted),
                    "base_expert_bundle_id": expert["bundle_id"],
                    "auxiliary": auxiliary,
                    "exposure_signature": r1.digest(
                        {
                            k: [
                                a["axis"],
                                a["shown_option_ids"],
                                a["selected_option_ids"],
                            ]
                            for k, a in base["answers_by_question"].items()
                        }
                    ),
                }
            )
    return rows


def fit_scorer(
    rows, expert, variant, allowed, excluded, contract_sha, tag, auxiliary_rows=None
):
    rt = runtime_module()
    allowed, excluded = set(allowed), set(excluded)
    if allowed & excluded or {r["group_id"] for r in rows} != allowed:
        raise ValueError("SCORER_TRAIN_SCOPE_MISMATCH")
    allrows = rows + list(auxiliary_rows or [])
    for row in allrows:
        if (
            row["group_id"] in row["base_expert_training_groups"]
            or set(row["base_expert_training_groups"]) & excluded
            or not set(row["base_expert_training_groups"]) <= allowed
        ):
            raise ValueError("SCORER_FEATURE_TRAIN_SCOPE_LEAKAGE")
    names = list(rt.FEATURES)
    p = len(names)
    supported = [set() for _ in names]
    for row in allrows:
        X = np.asarray(row["features"][variant], float)
        if X.shape != (len(row["candidate_ids"]), p):
            raise ValueError("FEATURE_SHAPE_MISMATCH")
        for j in np.flatnonzero(np.any(abs(X) > 1e-12, axis=0)):
            supported[j].add(row["group_id"])
    active = np.array([len(g) >= 3 for g in supported], bool)
    known = []
    for row in allrows:
        q = np.array(
            [row["episode"]["relevance"].get(c, 0) for c in row["candidate_ids"]], float
        )
        q *= np.asarray(row["legal_mask"], bool)
        if q.sum() > 0:
            known.append((row, q / q.sum()))
    main_known = [r for r, q in known if not r["auxiliary"]]
    aux_known = [r for r, q in known if r["auxiliary"]]
    weightmap = {}
    for subset, multiplier in [
        (main_known, 1.0),
        (
            aux_known,
            0.25
            * len(allowed)
            / max(1, len({r["group_id"] for r in auxiliary_rows or []})),
        ),
    ]:
        for row, w in zip(subset, group_weights(subset), strict=True):
            weightmap[id(row)] = float(w * multiplier)
    scales = np.zeros(p)
    weight_sum = 0.0
    for row, q in known:
        X = np.array(row["features"][variant], float)
        w = weightmap[id(row)]
        scales += w * np.mean(X * X, axis=0)
        weight_sum += w
    scales = np.sqrt(scales / max(weight_sum, 1))
    scales[scales < 1e-12] = 1.0
    arrays = []
    for row, q in known:
        X = np.asarray(row["features"][variant], float) / scales
        X[:, ~active] = 0.0
        arrays.append(
            (
                np.asarray(row["base_logits"], float),
                X,
                q,
                np.asarray(row["legal_mask"], bool),
                weightmap[id(row)],
            )
        )

    def objective(theta):
        value = 5.0 * float(theta @ theta)
        gradient = 10.0 * theta
        for base, X, q, mask, w in arrays:
            z = base + X @ theta
            if not mask.any():
                raise ValueError("NO_LEGAL_TRAIN_CANDIDATE")
            norm = logsumexp(z[mask])
            prob = np.zeros(len(z))
            prob[mask] = np.exp(z[mask] - norm)
            value += w * (norm - float(q @ z))
            gradient += w * (X.T @ (prob - q))
        return value, gradient

    if arrays and active.any():
        with threadpool_limits(limits=1):
            fitted = minimize(
                objective,
                np.zeros(p),
                jac=True,
                method="L-BFGS-B",
                options={"maxiter": 200, "ftol": 1e-10, "gtol": 1e-7},
            )
        if not fitted.success or not np.isfinite(fitted.x).all():
            raise ValueError("SCORER_OPTIMIZER_NOT_CONVERGED:" + str(fitted.message))
        theta = fitted.x
        iterations = int(fitted.nit)
        loss = float(fitted.fun)
        fitstatus = "ACTUALLY_FITTED_CONDITIONAL_MENTION_RETRIEVAL"
    else:
        theta = np.zeros(p)
        iterations = 0
        loss = None
        fitstatus = "NO_SUPPORTED_SUPERVISION_PARAMETERS"
    parameters = {
        "feature_names": names,
        "weights": theta.tolist(),
        "mean": [0.0] * p,
        "scale": scales.tolist(),
    }
    lineage = {
        "training_groups": sorted(allowed),
        "excluded_groups": sorted(excluded),
        "base_expert_ids": sorted({r["base_expert_bundle_id"] for r in allrows}),
        "training_rows": len(rows),
        "auxiliary_rows": len(auxiliary_rows or []),
        "identifiable_rows": len(known),
        "active_feature_names": [n for n, a in zip(names, active, strict=True) if a],
        "feature_group_support": {
            n: len(g) for n, g in zip(names, supported, strict=True)
        },
        "fit_status": fitstatus,
        "iterations": iterations,
        "objective": loss,
        "coefficient_l2": float(np.linalg.norm(theta)),
        "model_is_retrieval_not_sensory_truth": True,
        "training_exposure_signatures": sorted(
            {r["exposure_signature"] for r in allrows}
        ),
    }
    return model_bundle(
        expert, parameters, variant, contract_sha=contract_sha, tag=tag, lineage=lineage
    )


def trajectory(record, bundle, variant=None, policy="ALWAYS_ASK", auxiliary=False):
    rt = runtime_module()
    episode = source_episode(record, auxiliary)
    state = rt.initial_state(
        episode["context"], bundle, variant or bundle["selected_variant"], policy
    )
    states = [copy.deepcopy(state)]
    answers = []
    while True:
        nxt = rt.select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        q = nxt["question"]
        a = base_training.answer_for(
            q, answer_view(episode, q["slot"]), bundle["r1_expert"]
        )
        state = rt.update_state(state, a, bundle)
        answers.append(a)
        states.append(copy.deepcopy(state))
        if len(answers) > 5:
            raise ValueError("R4_FIXED_Q4_BUDGET_EXCEEDED")
    if "Q4" not in state["base_state"]["answers_by_question"]:
        raise ValueError("Q4_REQUIRED")
    return episode, states, answers


def result_row(record, episode, state, bundle, model, fold):
    ranking = state["candidate_scores"]
    fixed = bundle["fixed_candidates"]
    scores = metric.evaluate(
        ranking, episode["relevance"], fixed, excluded_visible=episode["visible"]
    )
    ids = [r["candidate_id"] for r in ranking[:5]]
    visible = set(episode.get("later_visible", episode["visible"]))
    actual_known = {c for c in visible if c.startswith("sensory.")}
    target_dirs = {a for c in episode["relevance"] for a in r1.PARENTS.get(c, [])}
    pred_dirs = {a for c in ids for a in r1.PARENTS.get(c, [])}
    base = state["base_state"]
    actual_explicit = {
        c
        for c in ids
        if next(r for r in ranking if r["candidate_id"] == c).get("explicit")
    }
    false_specific = [
        c
        for c in ids
        if c.startswith("sensory.")
        and c not in actual_known
        and c not in episode["relevance"]
    ]
    trace = state.get("conditioning_trace", {})
    raw = np.asarray(trace.get("raw_features", []))
    lineage = bundle.get("training_lineage") or {}
    supported = set(lineage.get("active_feature_names", []))
    relation_nonzero = bool(raw.size and np.any(abs(raw[:, 4:]) > 1e-12))
    supported_relation = bool(
        raw.size
        and any(
            n in supported and np.any(abs(raw[:, j]) > 1e-12)
            for j, n in enumerate(runtime_module().FEATURES)
            if j >= 4
        )
    )
    exposure = r1.digest(
        {
            k: [a["axis"], a["shown_option_ids"], a["selected_option_ids"]]
            for k, a in base["answers_by_question"].items()
        }
    )
    base_order = [r["candidate_id"] for r in base["candidate_scores"]]
    funnel = {
        "semantic_pairs_extractable": bool(trace.get("positive_pairs")),
        "raw_relation_features_nonzero": relation_nonzero,
        "train_supported_relation_applicable": supported_relation,
        "relation_score_nonzero": any(
            abs(r.get("relation_delta", r.get("relation_component", 0.0))) > 1e-12
            for r in ranking
        ),
        "any_conditioning_score_nonzero": any(
            abs(r.get("conditioning_delta", 0.0)) > 1e-12 for r in ranking
        ),
        "full_order_changed": [r["candidate_id"] for r in ranking] != base_order,
        "unseen_complete_exposure": exposure
        not in lineage.get("training_exposure_signatures", []),
    }
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "model": model,
        "fold": fold,
        **scores,
        "available_source_mentions_retention": (
            len(actual_known & set(ids)) / len(actual_known) if actual_known else None
        ),
        "direct_retention": (
            len(
                set(state["k1"]["confirmed_concepts"])
                & set(ids)
                & {
                    c
                    for c in state["k1"]["confirmed_concepts"]
                    if c.startswith("sensory.")
                }
            )
            / len(
                [
                    c
                    for c in state["k1"]["confirmed_concepts"]
                    if c.startswith("sensory.")
                ]
            )
            if any(c.startswith("sensory.") for c in state["k1"]["confirmed_concepts"])
            else None
        ),
        "explicit_selected_count": len(actual_explicit),
        "specificity_unsupported_proxy": (
            len(false_specific) / len([c for c in ids if c.startswith("sensory.")])
            if any(c.startswith("sensory.") for c in ids)
            else None
        ),
        "specificity_interpretation": "UNOBSERVED_IN_A_B_T_NOT_A_TRUE_SENSORY_FALSE_POSITIVE",
        "direction_coverage": (
            len(target_dirs & pred_dirs) / len(target_dirs) if target_dirs else None
        ),
        "output_count": len(ids),
        "ordinary_questions": len(base["answers_by_question"]),
        "ordinary_options": sum(
            len(a["shown_option_ids"]) for a in base["answers_by_question"].values()
        ),
        "context_questions": 2,
        "context_options": 15,
        "final_comparison_candidates": 0,
        "human_time": None,
        "ranking": ranking,
        "episode": episode,
        "fixed_candidates": fixed,
        "bundle_id": bundle["bundle_id"],
        "k1_before_scoring": state.get("k1_before_scoring", state.get("k1")),
        "component_trace": state.get("conditioning_trace"),
        "q2_decision": state.get("q2_decision"),
        "relation_funnel": funnel,
    }


def branches(records, bundle, fold, auxiliary=False):
    rt = runtime_module()
    rows = []
    for record in records:
        episode, states, answers = trajectory(
            record, bundle, policy="ALWAYS_ASK", auxiliary=auxiliary
        )
        q2 = next(
            s
            for s in states
            if set(s["base_state"]["answers_by_question"]) == {"Q0", "Q1", "Q2"}
        )
        ends = {}
        for action in ["ASK", "SKIP"]:
            terminal, _ = rt.complete_branch(
                q2, episode.get("later_visible", episode["visible"]), bundle, action
            )
            ends[action] = result_row(record, episode, terminal, bundle, action, fold)
        a, s = ends["ASK"]["raw_gap"], ends["SKIP"]["raw_gap"]
        rows.append(
            {
                "record_id": record["record_id"],
                "group_id": record["group_id"],
                "features": rt.live_features(q2, bundle),
                "gain": s - a if s is not None and a is not None else None,
                "outcomes": ends,
                "scorer_training_groups": (bundle.get("training_lineage") or {}).get(
                    "training_groups",
                    sorted(expert_training_groups(bundle["r1_expert"])),
                ),
                "scorer_bundle_id": bundle["bundle_id"],
            }
        )
    return rows


def cache_identity(records, expert, variant, contract_sha, auxiliary=None):
    import inspect

    code = "\n".join(
        inspect.getsource(f)
        for f in [source_episode, answer_view, collect_rows, fit_scorer, group_weights]
    )
    return r1.digest(
        {
            "data": records,
            "auxiliary_data": auxiliary or [],
            "base_expert": r1.digest(expert),
            "variant": variant,
            "contract": contract_sha,
            "runtime_sha": sha(Path(runtime_module().__file__)),
            "fit_functions_sha": r1.digest(code),
            "base_code": {
                n: sha(ROOT / "db/scripts" / n)
                for n in ["flavor_m2_r1.py", "train_m2_r1.py", "train_sequential.py"]
            },
        }
    )


def cached_rows(owner, records, expert, tag, contract_sha, auxiliary=False):
    identity = cache_identity(
        records, expert, "FEATURES_AUX" if auxiliary else "FEATURES", contract_sha
    )
    path = work_directory(owner) / "features" / f"{tag}.{identity[:16]}.private.json"
    if path.exists():
        cached = read(path)
        if cached["cache_identity"] != identity or cached["rows_sha256"] != r1.digest(
            cached["rows"]
        ):
            raise ValueError("FEATURE_CACHE_MISMATCH")
        return cached["rows"]
    rows = collect_rows(records, expert, auxiliary)
    save(
        path,
        {"cache_identity": identity, "rows_sha256": r1.digest(rows), "rows": rows},
        True,
    )
    return rows


def cached_fit(
    owner,
    rows,
    expert,
    variant,
    allowed,
    excluded,
    contract_sha,
    tag,
    auxiliary_rows=None,
):
    identity = cache_identity(rows, expert, variant, contract_sha, auxiliary_rows)
    identity = r1.digest([identity, sorted(allowed), sorted(excluded)])
    path = work_directory(owner) / "models" / f"{tag}.{identity[:16]}.model.json"
    if path.exists():
        bundle = read(path)
        runtime_module().check_bundle(bundle)
        if bundle["training_lineage"].get("cache_identity") != identity:
            raise ValueError("MODEL_CACHE_MISMATCH")
        return bundle, path
    bundle = fit_scorer(
        rows, expert, variant, allowed, excluded, contract_sha, tag, auxiliary_rows
    )
    lineage = copy.deepcopy(bundle["training_lineage"])
    lineage["cache_identity"] = identity
    bundle = model_bundle(
        expert,
        bundle["model_parameters"],
        variant,
        contract_sha=contract_sha,
        tag=tag,
        lineage=lineage,
    )
    save(path, bundle, True)
    return bundle, path


def select_variant(branch_map):
    losses = {
        v: macro([r["outcomes"]["ASK"] for r in rows], "raw_gap")
        for v, rows in branch_map.items()
    }
    available = {v: x for v, x in losses.items() if x is not None}
    best = min(available.values()) if available else None
    chosen = next(
        (v for v in VARIANTS if v in available and available[v] <= best + 1e-12), "A0"
    )
    return chosen, losses


def trigger_risk(branch_rows, decisions):
    byid = {r["record_id"]: r for r in branch_rows}
    if set(byid) != {r["record_id"] for r in decisions}:
        raise ValueError("POLICY_FULL_COHORT_REQUIRED")
    known = [r for r in branch_rows if r["gain"] is not None]
    action = {r["record_id"]: r["q2_decision"]["action"] for r in decisions}
    keys = [r for r in known if r["gain"] > 0.01]
    miss = [
        max(r["gain"], 0.0)
        for r in known
        if action[r["record_id"]] == "SKIP" and r["gain"] > 0
    ]
    unnecessary = [
        r for r in known if action[r["record_id"]] == "ASK" and r["gain"] <= 0.01
    ]
    regrets = [
        (
            max(r["gain"], 0.0)
            if action[r["record_id"]] == "SKIP"
            else max(-r["gain"], 0.0)
        )
        for r in known
    ]
    return {
        "all_records": len(branch_rows),
        "all_coffee_groups": len({r["group_id"] for r in branch_rows}),
        "identifiable_records": len(known),
        "unknown_gain_records": len(branch_rows) - len(known),
        "key_records": len(keys),
        "key_groups": len({r["group_id"] for r in keys}),
        "key_detected_records": sum(action[r["record_id"]] == "ASK" for r in keys),
        "ask_records": sum(a == "ASK" for a in action.values()),
        "skip_records": sum(a == "SKIP" for a in action.values()),
        "dynamic_policy_observed": len(set(action.values())) > 1,
        "missed_positive_gain_sum_record_units": float(sum(miss)),
        "missed_positive_gain_max": max(miss, default=0.0),
        "missed_gain_quantiles_50_90_95": (
            np.quantile(miss, [0.5, 0.9, 0.95]).tolist() if miss else [0.0, 0.0, 0.0]
        ),
        "unnecessary_ask_records_practical_threshold": len(unnecessary),
        "unnecessary_ask_options": sum(
            r["outcomes"]["ASK"]["ordinary_options"]
            - r["outcomes"]["SKIP"]["ordinary_options"]
            for r in unnecessary
        ),
        "record_regret_sum": float(sum(regrets)),
        "sum_units": "Record loss units, not additional independent coffee trials; paired group-macro primary reported separately",
    }


def attach_policy(bundle, trigger, old, contract_sha, tag):
    return model_bundle(
        bundle["r1_expert"],
        bundle["model_parameters"],
        bundle["selected_variant"],
        trigger,
        old,
        contract_sha,
        tag,
        bundle.get("training_lineage"),
    )


def run_outer(owner, contract_sha, outer, dev, folds, checkpoint_one=False):
    rt = runtime_module()
    dst = work_directory(owner)
    train = [r for r in dev if folds[r["group_id"]] != outer]
    held = [r for r in dev if folds[r["group_id"]] == outer]
    tg = {r["group_id"] for r in train}
    hg = {r["group_id"] for r in held}
    expert, audit = audit_reuse(
        owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json", train, held
    )
    old = read(owner / f"revisions/r3/models/R3_CONSTRAINTS_outer{outer}.model.json")
    audits = [audit]
    innerfolds = base_training.split_groups(train, 2)
    outer_rows = []
    inner_experts = []
    splits = []
    for inner in range(2):
        fitting = [r for r in train if innerfolds[r["group_id"]] != inner]
        validating = [r for r in train if innerfolds[r["group_id"]] == inner]
        ie, ia = audit_reuse(
            owner
            / f"revisions/r2/models/R2_R1_EXPERT_outer{outer}_inner{inner}.model.json",
            fitting,
            validating,
        )
        audits.append(ia)
        inner_experts.append(ie)
        splits.append((fitting, validating))
        outer_rows.extend(
            cached_rows(
                owner, validating, ie, f"outer{outer}_inner{inner}", contract_sha
            )
        )
    models = {
        "A0": model_bundle(expert, contract_sha=contract_sha, tag=f"A0_outer{outer}")
    }
    model_paths = {}
    fixed = []
    for variant in VARIANTS[1:]:
        models[variant], path = cached_fit(
            owner,
            outer_rows,
            expert,
            variant,
            tg,
            hg,
            contract_sha,
            f"{variant}_outer{outer}",
        )
        model_paths[variant] = {
            "owner_relative_path": str(path.relative_to(owner)),
            "sha256": sha(path),
        }
    for variant, bundle in models.items():
        for record in held:
            ep, states, _ = trajectory(record, bundle, variant)
            fixed.append(result_row(record, ep, states[-1], bundle, variant, outer))
    checkpoint = {
        "outer": outer,
        "fixed_summary": {
            v: scalar_summary([r for r in fixed if r["model"] == v]) for v in VARIANTS
        },
        "actual_fit_variants": list(model_paths),
        "model_paths": model_paths,
        "candidate_scope_equal": all(
            models[v]["fixed_candidates"] == models["A0"]["fixed_candidates"]
            for v in VARIANTS
        ),
        "audit_count": len(audits),
    }
    save(dst / f"checkpoint_outer{outer}.private.json", checkpoint, True)
    print(
        json.dumps(
            {
                "checkpoint": "ACTUAL_AK_AR_AKR_FITTED",
                "outer": outer,
                "fixed_summary": checkpoint["fixed_summary"],
            },
            allow_nan=False,
        ),
        flush=True,
    )
    if checkpoint_one:
        return checkpoint
    innerbranches = {v: [] for v in VARIANTS}
    for inner, (fitting, validating) in enumerate(splits):
        df = base_training.split_groups(fitting, 2)
        fitrows = []
        for deeper in range(2):
            dt = [r for r in fitting if df[r["group_id"]] != deeper]
            dh = [r for r in fitting if df[r["group_id"]] == deeper]
            de, da = audit_reuse(
                owner
                / f"revisions/r3/models/R3_R1_EXPERT_outer{outer}_inner{inner}_deeper{deeper}_P1_INTERNAL.model.json",
                dt,
                dh,
            )
            audits.append(da)
            fitrows.extend(
                cached_rows(owner, dh, de, f"o{outer}_i{inner}_d{deeper}", contract_sha)
            )
        fg = {r["group_id"] for r in fitting}
        excluded = hg | {r["group_id"] for r in validating}
        imodels = {
            "A0": model_bundle(
                inner_experts[inner],
                contract_sha=contract_sha,
                tag=f"A0_o{outer}_i{inner}",
            )
        }
        for v in VARIANTS[1:]:
            imodels[v], _ = cached_fit(
                owner,
                fitrows,
                inner_experts[inner],
                v,
                fg,
                excluded,
                contract_sha,
                f"{v}_o{outer}_i{inner}",
            )
        for v, b in imodels.items():
            innerbranches[v].extend(branches(validating, b, outer))
    chosen, innerloss = select_variant(innerbranches)
    trigger = fit_key_case(innerbranches[chosen], list(rt.LIVE_FEATURES), tg, hg)
    deployed = attach_policy(
        models[chosen], trigger, old, contract_sha, f"POLICY_outer{outer}"
    )
    path = dst / f"models/R4_POLICY_outer{outer}.model.json"
    save(path, deployed, True)
    heldbranches = branches(held, deployed, outer)
    policies = []
    for policy in POLICIES:
        for record in held:
            ep, states, _ = trajectory(record, deployed, policy=policy)
            policies.append(result_row(record, ep, states[-1], deployed, policy, outer))
    result = {
        "outer": outer,
        "checkpoint": checkpoint,
        "selected_variant": chosen,
        "inner_selection_losses": innerloss,
        "trigger_summary": {
            k: v
            for k, v in trigger.items()
            if k
            not in {
                "coefficients",
                "intercept",
                "mean",
                "scale",
                "training_groups",
                "score_versions",
            }
        },
        "fixed_rows": fixed,
        "policy_rows": policies,
        "held_branches": heldbranches,
        "inner_branches": innerbranches,
        "models": model_paths,
        "policy_model_path": str(path.relative_to(owner)),
        "policy_model_sha256": sha(path),
        "base_reuse_audits": audits,
        "scorer_model_versions_frozen_before_gain": True,
    }
    save(dst / f"outer{outer}_results.private.json", result, True)
    print(
        json.dumps(
            {
                "phase": "NESTED_KEY_CASE_COMPLETE",
                "outer": outer,
                "selected": chosen,
                "trigger": result["trigger_summary"],
            },
            allow_nan=False,
        ),
        flush=True,
    )
    return result


def auxiliary_comparison(owner, contract_sha, dev, folds, episodes):
    rt = runtime_module()
    results = []
    models = []
    for outer in range(3):
        train = [r for r in dev if folds[r["group_id"]] != outer]
        held = [r for r in dev if folds[r["group_id"]] == outer]
        tg = {r["group_id"] for r in train}
        hg = {r["group_id"] for r in held}
        auxtrain = [r for r in episodes if r["group_id"] in tg]
        auxheld = [r for r in episodes if r["group_id"] in hg]
        expert = read(
            owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json"
        )
        innerfolds = base_training.split_groups(train, 2)
        mainrows = []
        auxrows = []
        for inner in range(2):
            validating = [r for r in train if innerfolds[r["group_id"]] == inner]
            av = [r for r in auxtrain if innerfolds[r["group_id"]] == inner]
            ie = read(
                owner
                / f"revisions/r2/models/R2_R1_EXPERT_outer{outer}_inner{inner}.model.json"
            )
            mainrows.extend(
                cached_rows(
                    owner, validating, ie, f"outer{outer}_inner{inner}", contract_sha
                )
            )
            auxrows.extend(
                cached_rows(owner, av, ie, f"aux_o{outer}_i{inner}", contract_sha, True)
            )
        off, pathoff = cached_fit(
            owner, mainrows, expert, "AKR", tg, hg, contract_sha, f"AKR_outer{outer}"
        )
        on, pathon = cached_fit(
            owner,
            mainrows,
            expert,
            "AKR",
            tg,
            hg,
            contract_sha,
            f"AKR_AUX_outer{outer}",
            auxrows,
        )
        models.append(
            {
                "outer": outer,
                "off_model_sha256": sha(pathoff),
                "on_model_sha256": sha(pathon),
                "on_owner_relative_path": str(pathon.relative_to(owner)),
                "aux_train_records": len(auxtrain),
                "aux_held_records": len(auxheld),
            }
        )
        for task, records, isaux in [
            ("MAIN_RECORD_DERIVED", held, False),
            ("CROSS_GRADER_REVELATION", auxheld, True),
        ]:
            for label, b in [("AKR", off), ("AKR_AUX", on)]:
                for record in records:
                    ep, states, _ = trajectory(
                        record, b, policy="ALWAYS_ASK", auxiliary=isaux
                    )
                    row = result_row(record, ep, states[-1], b, label, outer)
                    row["task"] = task
                    results.append(row)
    report = {
        "task_definition": "Independent recorded grader A/B/T, shared graders and held coffee groups; source-local auxiliary joint CE, not general sensory pretraining",
        "models": models,
        "results": {
            task: {
                v: scalar_summary(
                    [r for r in results if r["task"] == task and r["model"] == v]
                )
                for v in ["AKR", "AKR_AUX"]
            }
            for task in ["MAIN_RECORD_DERIVED", "CROSS_GRADER_REVELATION"]
        },
        "contrasts": {
            task: paired([r for r in results if r["task"] == task], "AKR_AUX", "AKR")
            for task in ["MAIN_RECORD_DERIVED", "CROSS_GRADER_REVELATION"]
        },
    }
    save(
        work_directory(owner) / "auxiliary_results.private.json",
        {"summary": report, "rows": results},
        True,
    )
    return report


def refit_final(owner, contract_sha, dev, folds, outer_results):
    rt = runtime_module()
    allfixed = [r for o in outer_results for r in o["fixed_rows"]]
    losses = {
        v: macro([r for r in allfixed if r["model"] == v], "raw_gap") for v in VARIANTS
    }
    minimum = min(x for x in losses.values() if x is not None)
    chosen = next(
        v for v in VARIANTS if losses[v] is not None and losses[v] <= minimum + 1e-12
    )
    old = read(owner / "revisions/r3/models/R3_CONSTRAINTS_ALL_DEVELOPMENT.model.json")
    expert = old["r1_expert"]
    rows = []
    branchrows = []
    for outer in range(3):
        held = [r for r in dev if folds[r["group_id"]] == outer]
        oe = read(owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{outer}.model.json")
        rows.extend(
            cached_rows(owner, held, oe, f"full_base_oof_{outer}", contract_sha)
        )
        if chosen == "A0":
            b = model_bundle(oe, contract_sha=contract_sha, tag=f"FINAL_A0_OOF_{outer}")
        else:
            b = read(
                owner / outer_results[outer]["models"][chosen]["owner_relative_path"]
            )
        branchrows.extend(branches(held, b, outer))
    if chosen == "A0":
        score = model_bundle(
            expert,
            contract_sha=contract_sha,
            tag="ALL_DEV_A0",
            lineage={
                "training_groups": sorted(folds),
                "fit_status": "SELECTED_FROZEN_BASE_NO_NEW_SCORER_PARAMETERS",
            },
        )
    else:
        score, _ = cached_fit(
            owner,
            rows,
            expert,
            chosen,
            set(folds),
            set(),
            contract_sha,
            "FINAL_SCORER_ALL_DEVELOPMENT",
        )
    trigger = fit_key_case(branchrows, list(rt.LIVE_FEATURES), set(folds), set())
    bundle = attach_policy(
        score, trigger, old, contract_sha, "ALL_DEVELOPMENT_RESEARCH"
    )
    path = work_directory(owner) / "models/R4_ALL_DEVELOPMENT_RESEARCH.model.json"
    save(path, bundle, True)
    save(work_directory(owner) / "final_trigger_oof.private.json", branchrows, True)
    return bundle, {
        "selected_variant": chosen,
        "selection_losses": losses,
        "selection_scope": "Previously inspected development OOF only; final refit is not new evaluation",
        "training_records": len(dev),
        "training_groups": len(folds),
        "owner_relative_model_path": str(path.relative_to(owner)),
        "sha256": sha(path),
        "not_last_fold_model": True,
        "trigger_fit_status": trigger["fit_status"],
    }


def publish(owner, outer_results, auxiliary=None, final=None, execution=None):
    fixed = [r for o in outer_results for r in o["fixed_rows"]]
    policies = [r for o in outer_results for r in o["policy_rows"]]
    br = [r for o in outer_results for r in o["held_branches"]]
    scores = {
        v: scalar_summary([r for r in fixed if r["model"] == v]) for v in VARIANTS
    }
    policy = {
        v: scalar_summary([r for r in policies if r["model"] == v]) for v in POLICIES
    }
    metrics = {
        "status": "ACTUAL_GROUPED_DEVELOPMENT_COMPARISONS",
        "proxy_only": True,
        "main_scoring": scores,
        "relation_funnel_Q4": {
            v: {
                k: sum(bool(r["relation_funnel"][k]) for r in fixed if r["model"] == v)
                for k in fixed[0]["relation_funnel"]
            }
            for v in VARIANTS
        },
        "scoring_contrasts": [
            paired(fixed, a, b)
            for a, b in [
                ("AK", "A0"),
                ("AR", "A0"),
                ("AKR", "A0"),
                ("AKR", "AK"),
                ("AKR", "AR"),
            ]
        ],
        "policy": policy,
        "policy_contrasts": [paired(policies, a, "ALWAYS_ASK") for a in POLICIES[1:]],
        "trigger_risk": {
            v: trigger_risk(br, [r for r in policies if r["model"] == v])
            for v in POLICIES
        },
        "outer_selections": [
            {
                "outer": o["outer"],
                "selected": o["selected_variant"],
                "inner_losses": o["inner_selection_losses"],
                "trigger": o["trigger_summary"],
            }
            for o in outer_results
        ],
        "auxiliary": auxiliary,
        "final_research_bundle": final,
        "real_user_alignment": "NOT_EVALUATED",
        "human_time": None,
        "B2": "UNCHANGED",
        "FOUNDATION_CHECK": False,
        "r3_results_preserved": {
            "metrics_sha256": sha(
                ROOT / "db/data/backend-sequential-model-v2/revisions/r3/metrics.json"
            ),
            "metric_code_sha256": sha(ROOT / "db/scripts/alignment_metrics_r3.py"),
        },
        "execution": execution,
    }
    save(OUT / "metrics.json", metrics)
    receipt = read(OUT / "run_receipt.json")
    receipt.update(
        status="ACTUAL_TRAINING_AND_NESTED_POLICY_COMPLETED",
        updated_utc=now(),
        final_model=final,
        execution=execution,
    )
    save(OUT / "run_receipt.json", receipt)
    return metrics


def run(owner, contract_path, replay=False, checkpoint_one=False, fresh=False):
    global OUT, RUN_DESTINATION
    if fresh:
        import shutil

        stamp = now().replace(":", "").replace("+", "_")
        RUN_DESTINATION = Path(owner) / "revisions/r4/retraining" / stamp
        RUN_DESTINATION.mkdir(parents=True, exist_ok=False)
        RUN_DESTINATION.chmod(0o700)
        original_out = OUT
        OUT = RUN_DESTINATION / "summaries"
        shutil.copytree(original_out, OUT)
        print(
            json.dumps(
                {
                    "operation": "FRESH_R4_REFIT_FROM_DATA_WITH_AUDITED_FROZEN_BASE_EXPERTS",
                    "output_owner_relative_path": str(
                        RUN_DESTINATION.relative_to(owner)
                    ),
                    "old_R4_artifacts_overwritten": False,
                }
            ),
            flush=True,
        )
    rt = runtime_module()
    owner = Path(owner)
    contract_sha = sha(contract_path)
    diagnostic = OUT / "component_trace.json"
    if not diagnostic.exists() or not read(diagnostic).get(
        "pre_fit_intervention_checks_passed"
    ):
        raise ValueError("FIRST_CHECKPOINT_INTERVENTIONS_REQUIRED_BEFORE_FITTING")
    records = read(owner / "recovery_records.json")
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    if folds != base_training.split_groups(dev, 3):
        raise ValueError("ORIGINAL_COFFEE_FOLDS_CHANGED")
    results = []
    for outer in range(1 if checkpoint_one else 3):
        if replay:
            results.append(
                read(work_directory(owner) / f"outer{outer}_results.private.json")
            )
        else:
            results.append(
                run_outer(owner, contract_sha, outer, dev, folds, checkpoint_one)
            )
    if checkpoint_one:
        save(
            OUT / "metrics.json",
            {
                "status": "FIRST_ACTUAL_OLD_DATA_FIT_CHECKPOINT",
                "outer0": results[0],
                "remaining": "Nested trigger and full grouped evaluation pending",
            },
        )
        return results
    if replay:
        summary = read(work_directory(owner) / "final_summary.private.json")
        # Replay is a numerical recomputation from saved ranking and fixed targets.
        checked = 0
        for row in [r for o in results for r in o["fixed_rows"] + o["policy_rows"]]:
            actual = metric.evaluate(
                row["ranking"],
                row["episode"]["relevance"],
                row["fixed_candidates"],
                excluded_visible=row["episode"]["visible"],
            )
            for key in ["raw_gap", "ndcg", "recall", "M", "M_star"]:
                if (actual[key] is None) != (row[key] is None) or (
                    actual[key] is not None and abs(actual[key] - row[key]) > 1e-12
                ):
                    raise ValueError("REPLAY_METRIC_MISMATCH")
            checked += 1
        return publish(
            owner,
            results,
            summary["auxiliary"],
            summary["final"],
            {
                "operation": "ARTIFACT_REPLAY_NOT_RETRAINING",
                "rankings_recomputed": checked,
                "fit_calls": 0,
            },
        )
    import data_connections_r4

    episodes = data_connections_r4.load_episodes(owner)
    auxiliary = auxiliary_comparison(owner, contract_sha, dev, folds, episodes)
    bundle, final = refit_final(owner, contract_sha, dev, folds, results)
    summary = {"auxiliary": auxiliary, "final": final}
    save(work_directory(owner) / "final_summary.private.json", summary, True)
    return publish(
        owner,
        results,
        auxiliary,
        final,
        {"operation": "ACTUAL_FITS_AND_LIVE_TRAJECTORIES", "outer_folds": 3},
    )
