"""M2 R1 grouped fitting: explicit supervision masks and versioned live features."""

from __future__ import annotations
import copy, itertools, math, time
from collections import Counter
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, logsumexp
from threadpoolctl import threadpool_limits
import flavor_m2_r1 as s
import train_sequential as legacy

SEED = legacy.SEED
split_groups = legacy.split_groups
statistics = legacy.statistics
visible_episode = legacy.visible_episode
answer_for = legacy.answer_for
ndcg = legacy.ndcg


def entropy(patterns):
    counts = Counter(patterns)
    total = sum(counts.values())
    return (
        -sum((n / total) * math.log2(n / total) for n in counts.values())
        if total
        else 0.0
    )


def pair_diagnostics(records, left, right, attributes):
    observed = [
        {a for c in row["targets"] for a in attributes.get(c, [])} for row in records
    ]
    p0 = [tuple(a for a in left if a in attrs) for attrs in observed]
    p1 = [tuple(a for a in right if a in attrs) for attrs in observed]
    h0, h1, joint = entropy(p0), entropy(p1), entropy(list(zip(p0, p1)))
    covered = sum(len(attrs & set(left + right)) for attrs in observed)
    total = sum(len(attrs) for attrs in observed)
    return {
        "q0_attributes": list(left),
        "q1_attributes": list(right),
        "q0_response_entropy_bits": h0,
        "q1_response_entropy_bits": h1,
        "q1_conditional_entropy_given_q0_bits": max(0.0, joint - h0),
        "joint_response_entropy_bits": joint,
        "observed_attribute_coverage": covered / max(total, 1),
        "q0_effective_selection_rate": sum(bool(x) for x in p0) / max(len(p0), 1),
        "q1_effective_selection_rate": sum(bool(x) for x in p1) / max(len(p1), 1),
        "q1_patterns": {
            "|".join(k) or "UNSURE": n for k, n in sorted(Counter(p1).items())
        },
        "basis": "TRAIN_GROUP_RECORD_PROXY_NOT_ACTUAL_USER_RESPONSE_ENTROPY",
    }


def make_bank(stats, attributes):
    """Bounded train-only joint-coverage search, separately ablated from repair."""
    bank = legacy.make_bank(stats, attributes)
    old_left = [o["attribute"] for o in bank["initial_0"]["options"]]
    old_right = [o["attribute"] for o in bank["initial_1"]["options"]]
    records = stats["planning_records"]
    qualified = sorted({a for c in stats["vocabulary"] for a in attributes.get(c, [])})
    if len(qualified) < 8:
        qualified = sorted(set(qualified) | set(s.ATTRS))
    candidates = []
    for left in itertools.combinations(qualified, 4):
        for right in itertools.combinations([a for a in qualified if a not in left], 4):
            d = pair_diagnostics(records, list(left), list(right), attributes)
            objective = (
                d["joint_response_entropy_bits"]
                + 0.25
                * min(d["q0_response_entropy_bits"], d["q1_response_entropy_bits"])
                + 0.5 * d["q1_conditional_entropy_given_q0_bits"]
                + d["observed_attribute_coverage"]
            )
            candidates.append((objective, left, right, d))
    _, left, right, selected = max(candidates, key=lambda x: (x[0], x[1], x[2]))
    for key, axis, attrs in [
        ("initial_0", "broad.initial0", left),
        ("initial_1", "broad.initial1", right),
    ]:
        bank[key] = {
            "axis": axis,
            "options": [
                {"id": "attribute." + a, "kind": "broad", "attribute": a} for a in attrs
            ],
            "priority": 0,
            "classification_scope": "LOCAL_REGISTERED_ATTRIBUTE_SUBSET",
        }
    bank["initial_pair_selection"] = {
        "method": "BOUNDED_TRAIN_GROUP_COMPLEMENTARITY_SEARCH",
        "pairs_evaluated": len(candidates),
        "selected": selected,
        "legacy_frequency_partition": pair_diagnostics(
            records, old_left, old_right, attributes
        ),
        "training_groups": sorted({r["group_id"] for r in records}),
    }
    return bank


def make_bundle(
    records,
    kind="M2_R1_FIXED",
    manifest_hash="",
    vocabulary=None,
    tag="",
    bank_override=None,
):
    if kind not in {
        "M2_R1_FIXED",
        "M2_R1_ADD",
        "M2_R1_FOUNDATION",
        "M2_R1_FOUNDATION_CHECK",
    }:
        raise ValueError("R1_MODEL_KIND_REQUIRED")
    stats = statistics(records, vocabulary)
    vocab = stats.pop("vocabulary")
    attrs = {c: s.PARENTS.get(c, []) for c in vocab}
    bank = (
        copy.deepcopy(bank_override)
        if bank_override is not None
        else make_bank(dict(stats, vocabulary=vocab), attrs)
    )
    weights = [1, 2, 1, 0.1, 0.2, 0.2, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0]
    return {
        **s.VERSIONS,
        "bundle_id": "m2-r1:"
        + tag
        + ":"
        + s.digest([kind, sorted({r["group_id"] for r in records}), bank])[:16],
        "model_kind": kind,
        "candidate_vocabulary": vocab,
        "candidate_attributes": attrs,
        "candidate_clusters": {},
        "cluster_dimension": 0,
        "cluster_model": {
            "kind": "NOT_USED",
            "training_groups": [],
            "reason": "R1 ADD/JOINT have no NMF dependency; legacy HIER remains a frozen comparator.",
        },
        "scaler_parameters": {
            "mean": [0.0] * len(s.FEATURES),
            "scale": [1.0] * len(s.FEATURES),
        },
        "model_parameters": {"feature_names": s.FEATURES, "weights": weights},
        "statistics": stats,
        "question_bank": bank,
        "training_split_hash": s.digest(sorted({r["group_id"] for r in records})),
        "data_manifest_hash": manifest_hash,
        "candidate_rights": dict.fromkeys(vocab, "ADMITTED"),
        "seed": SEED,
        "question_cost": 0.01,
        "context_descriptor_support": {
            "C0": False,
            "C1": False,
            "reason": "D0 has no validated production C0/C1-descriptor pairing; same zero mask at train/evaluation/live.",
        },
        "context_attribute_models": {},
        "bank_scope": (
            "FROZEN_COMPARISON_BANK"
            if bank_override is not None
            else "TRAIN_ONLY_COMPLEMENTARITY_SEARCH"
        ),
        "evidence_policy": {
            "exposed_rejection_coefficient": -1.0,
            "exposed_rejection_basis": "REGISTERED_SEMANTIC_CONSTRAINT_NOT_FITTED_FROM_UNMENTIONED_TARGETS",
            "specific_confirmation": "ELIGIBILITY_METADATA_SEPARATE_FROM_NEGATIVE_EVIDENCE",
            "feedback": "CANONICAL_UNION_NO_REPEAT_BONUS",
        },
    }


def trajectory(record, bundle, path="P1", policy="fixed"):
    episode = visible_episode(record)
    state = s.initial_state(episode["context"], bundle, path, policy)
    states, answers = [copy.deepcopy(state)], []
    while True:
        nxt = s.select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        answer = answer_for(nxt["question"], episode["visible"], bundle)
        state = s.update_joint_state(state, answer, bundle)
        answers.append(answer)
        states.append(copy.deepcopy(state))
        if len(answers) > 6:
            raise AssertionError("ORDINARY_QUESTION_BUDGET")
    return episode, states, answers


def supervision_targets(record, episode, state, bundle):
    """Zero mask means unknown, never a manufactured sensory negative.

    Attribute values use the registered INERA 0..9 mention-frequency range.
    Positive-only descriptors supervise their observed cells with independent
    logistic recovery; their unmentioned candidate cells have zero mask.
    """
    vocab = bundle["candidate_vocabulary"]
    index = {c: i for i, c in enumerate(vocab)}
    out = {
        name: {"values": np.zeros(len(vocab)), "mask": np.zeros(len(vocab))}
        for name in ["attr", "leaf", "recovery"]
    }
    structured = (
        record.get("supervision") == "SOURCE_NATIVE_STRUCTURED_MENTION_FREQUENCIES"
    )
    if structured:
        if record["source_family"] != "inera":
            raise ValueError("STRUCTURED_SCALE_REQUIRES_REGISTERED_SOURCE_PROTOCOL")
        for attr, value in zip(
            record.get("attribute_names", []), record.get("attribute_values", [])
        ):
            if value is None or "attribute." + attr not in index:
                continue
            if not 0 <= value <= 9:
                raise ValueError("SOURCE_ATTRIBUTE_FREQUENCY_OUT_OF_RANGE")
            i = index["attribute." + attr]
            out["attr"]["values"][i], out["attr"]["mask"][i] = value / 9.0, 1.0
    else:
        for c in record["targets"]:
            if c.startswith("attribute.") and c in index:
                out["attr"]["values"][index[c]], out["attr"]["mask"][index[c]] = (
                    1.0,
                    1.0,
                )
    for c in s.evidence(state, bundle)["confirmed"]:
        if c.startswith("sensory.") and c in index:
            out["leaf"]["values"][index[c]], out["leaf"]["mask"][index[c]] = 1.0, 1.0
    for c in episode["hidden"]:
        # Complete-frequency attributes are owned by the attribute task. Broad
        # and concrete descriptions never share a mutually exclusive softmax.
        if c in index and not (structured and c.startswith("attribute.")):
            out["recovery"]["values"][index[c]], out["recovery"]["mask"][index[c]] = (
                1.0,
                1.0,
            )
    # Conditional record-completion target preserves source mention weights.
    # The Bernoulli task above deliberately retains 0..1 targets.
    out["recovery"]["mention_mass"] = np.asarray(
        [
            float(record["relevance"].get(c, 0.0)) if c in episode["hidden"] else 0.0
            for c in vocab
        ]
    )
    return out


def training_arrays(
    records, outer_bundle, manifest_hash, loss_mode="layered", bank_override=None
):
    if loss_mode not in {"legacy", "layered", "layered_conditional"}:
        raise ValueError("UNKNOWN_LOSS_MODE")
    folds = split_groups(records, 2)
    X, Y, weights, audit, task_rows = [], [], [], [], []
    vocab = outer_bundle["candidate_vocabulary"]
    index = {c: i for i, c in enumerate(vocab)}
    source_groups = Counter(
        next(r["source_family"] for r in records if r["group_id"] == g)
        for g in {r["group_id"] for r in records}
    )
    group_rows = Counter(r["group_id"] for r in records)
    for fold in range(2):
        train = [r for r in records if folds[r["group_id"]] != fold]
        held = [r for r in records if folds[r["group_id"]] == fold]
        # Vocabulary is the fixed outer-training candidate scope. All fitted
        # question priorities/response patterns are rebuilt on inner TRAIN.
        inner_stats = statistics(train, vocab)
        inner_attrs = {c: s.PARENTS.get(c, []) for c in vocab}
        inner_bank = (
            legacy.make_bank(inner_stats, inner_attrs)
            if bank_override is not None
            and "initial_pair_selection" not in bank_override
            else make_bank(inner_stats, inner_attrs)
        )
        inner = make_bundle(
            train,
            outer_bundle["model_kind"],
            manifest_hash,
            vocab,
            "inner" + str(fold),
            inner_bank,
        )
        inner["bank_scope"] = (
            "INNER_TRAIN_ONLY_LEGACY_PARTITION"
            if "initial_pair_selection" not in inner_bank
            else "INNER_TRAIN_ONLY_COMPLEMENTARITY"
        )
        audit.append(
            {
                "feature_training_groups": sorted({r["group_id"] for r in train}),
                "feature_output_groups": sorted({r["group_id"] for r in held}),
                "cluster_fit": "NOT_USED",
                "question_bank_scope": inner["bank_scope"],
                "source_truth_as_runtime_features": False,
            }
        )
        for record in held:
            ep, states, answers = trajectory(record, inner, path="P4")
            pre = s.finalize_result(states[-1], inner)
            exposure = pre["exposure"]
            if exposure and exposure["eligible_for_final_comparison"]:
                chosen = [c for c in exposure["candidate_ids"] if c in ep["visible"]]
                states.append(
                    s.apply_final_comparison(
                        states[-1],
                        exposure["candidate_ids"],
                        chosen,
                        inner,
                        feedback_source="SIMULATED",
                        generation_version=inner["bundle_id"],
                    )
                )
            mass = 1 / (
                group_rows[record["group_id"]]
                * source_groups[record["source_family"]]
                * len(states)
            )
            for state in states:
                hidden = [c for c in ep["hidden"] if c in index]
                if not hidden:
                    continue
                X.append(s.encode_features(state, inner)["raw_features"])
                task_rows.append(supervision_targets(record, ep, state, inner))
                direct = [
                    c for c in s.evidence(state, inner)["confirmed"] if c in index
                ]
                y = np.zeros(len(vocab))
                for c in hidden:
                    y[index[c]] += (
                        (0.7 if direct else 1.0)
                        * record["relevance"][c]
                        / sum(record["relevance"][h] for h in hidden)
                    )
                for c in direct:
                    y[index[c]] += 0.3 / len(direct)
                Y.append(y)
                weights.append(mass)
    tasks = {
        task: {
            key: np.asarray([row[task][key] for row in task_rows])
            for key in ["values", "mask"]
        }
        for task in ["attr", "leaf", "recovery"]
    }
    tasks["recovery"]["mention_mass"] = np.asarray(
        [row["recovery"]["mention_mass"] for row in task_rows]
    )
    tasks["recovery"]["candidate_levels"] = [
        (
            "leaf"
            if c.startswith("sensory.")
            else "broad_descriptor" if c.startswith("broad.") else "attribute"
        )
        for c in vocab
    ]
    return np.asarray(X), np.asarray(Y), np.asarray(weights), audit, tasks


def fit_shared(
    X,
    Y,
    sample_weights,
    C=1.0,
    kind="M2_R1_FIXED",
    loss_mode="layered",
    tasks=None,
    task_weights=None,
):
    sample_weights = sample_weights / sample_weights.sum()
    active = np.ones(len(s.FEATURES))
    active[[8, 9, 11, 12, 13, 14, 15]] = 0
    if kind == "M2_R1_ADD":
        active[10] = 0
    X = X * active
    lambdas = {"attr": 1.0, "leaf": 1.0, "recovery": 1.0, **(task_weights or {})}
    penalty = (0.005 if loss_mode == "legacy" else 0.02) / max(C, 1e-8)
    if loss_mode in {"layered", "layered_conditional"} and tasks is None:
        raise ValueError("LAYERED_SUPERVISION_MASKS_REQUIRED")
    normalized_masks = {}
    if tasks is not None:
        for task, data in tasks.items():
            mask = data["mask"]
            weighted = (
                mask
                * sample_weights[:, None]
                / np.maximum(mask.sum(axis=1, keepdims=True), 1.0)
            )
            normalized_masks[task] = weighted / max(weighted.sum(), 1e-12)

    conditional_recovery = []
    if loss_mode == "layered_conditional":
        levels = np.asarray(tasks["recovery"]["candidate_levels"])
        mention_mass = tasks["recovery"]["mention_mass"]
        for level in ["leaf", "broad_descriptor"]:
            indices = np.flatnonzero(levels == level)
            if not len(indices):
                continue
            mass = mention_mass[:, indices]
            labelled = mass.sum(axis=1) > 0
            distribution = mass / np.maximum(mass.sum(axis=1, keepdims=True), 1e-12)
            mass_weights = sample_weights * labelled
            mass_weights /= max(mass_weights.sum(), 1e-12)
            conditional_recovery.append((indices, distribution, mass_weights))

    def objective(w):
        logits = X @ w
        if loss_mode == "legacy":
            logp = logits - logsumexp(logits, axis=1, keepdims=True)
            loss = -np.sum(sample_weights[:, None] * Y * logp)
            grad = np.einsum("nk,nkf,n->f", np.exp(logp) - Y, X, sample_weights)
        else:
            loss, grad = 0.0, np.zeros(len(s.FEATURES))
            probabilities = expit(logits)
            for task, data in tasks.items():
                if loss_mode == "layered_conditional" and task == "recovery":
                    continue
                m = normalized_masks[task] * lambdas[task]
                y = data["values"]
                # Soft-label Bernoulli loss on 0..1 mention proportions or
                # positive observations. Unobserved cells contribute exactly 0.
                loss += np.sum(m * (np.logaddexp(0, logits) - y * logits))
                grad += np.einsum("nk,nkf->f", m * (probabilities - y), X)
            for indices, distribution, conditional_weights in conditional_recovery:
                level_logits = logits[:, indices]
                logp = level_logits - logsumexp(level_logits, axis=1, keepdims=True)
                factor = lambdas["recovery"] / max(len(conditional_recovery), 1)
                loss -= factor * np.sum(
                    conditional_weights[:, None] * distribution * logp
                )
                grad += factor * np.einsum(
                    "nk,nkf,n->f",
                    np.exp(logp) - distribution,
                    X[:, indices, :],
                    conditional_weights,
                )
        loss += penalty * np.dot(w, w) / 2
        grad += penalty * w
        return float(loss), grad

    bounds = []
    for i, name in enumerate(s.FEATURES):
        if not active[i]:
            bounds.append((0.0, 0.0))
        elif name == "exposed_rejection":
            bounds.append((-1.0, -1.0))
        elif name in {
            "log_prior",
            "specific_direct",
            "broad_candidate_direct",
            "broad_related_support",
        }:
            bounds.append((0.0, None))
        else:
            bounds.append((None, None))
    with threadpool_limits(limits=1):
        result = minimize(
            objective,
            np.zeros(len(s.FEATURES)),
            jac=True,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": 300, "ftol": 1e-10, "gtol": 1e-6},
        )
    if not result.success:
        raise RuntimeError("M2_R1_FIT_FAILED:" + str(result.message))
    receipt = {
        "iterations": int(result.nit),
        "loss": float(result.fun),
        "training_states": len(X),
        "parameter_count": int(active.sum() - 1),
        "C": C,
        "success": True,
        "loss_mode": loss_mode,
        "task_weights": (
            lambdas
            if loss_mode != "legacy"
            else {"legacy_hidden": 0.7, "legacy_direct": 0.3}
        ),
        "regularization_coefficient": penalty,
        "exposed_rejection": "FIXED_NEGATIVE_SEMANTIC_COEFFICIENT; NO_UNMENTIONED_NEGATIVES",
        "mask_counts": {
            task: {
                "observed_cells": int(data["mask"].sum()),
                "observed_zero_cells": int(
                    ((data["values"] == 0) & (data["mask"] > 0)).sum()
                ),
                "excluded_cells": int((data["mask"] == 0).sum()),
            }
            for task, data in (tasks or {}).items()
        },
    }
    if loss_mode == "layered_conditional":
        receipt["recovery_statistical_object"] = (
            "GRADED_OBSERVED_MENTION_CONDITIONAL_RETRIEVAL_WITHIN_LEAF_OR_BROAD_DESCRIPTOR_LEVEL; NOT_SENSORY_PRESENCE_PROBABILITY"
        )
        receipt["recovery_missing_semantics"] = (
            "UNMENTIONED_CANDIDATES_PARTICIPATE_IN_IDENTITY_NORMALIZER_BUT_HAVE_NO_BERNOULLI_ABSENCE_LABEL; ATTRIBUTE_VALUES_ARE_EXCLUDED_FROM_THIS_NORMALIZER"
        )
        receipt["conditional_recovery_levels"] = [
            {
                "candidate_count": len(indices),
                "labelled_state_count": int((cw > 0).sum()),
            }
            for indices, distribution, cw in conditional_recovery
        ]
    if tasks is not None:
        predicted = expit(X @ result.x)
        receipt["degeneracy_diagnostics"] = {
            task: {
                "observed_mean_support": (
                    float(predicted[data["mask"] > 0].mean())
                    if data["mask"].any()
                    else None
                ),
                "unobserved_mean_support": (
                    float(predicted[data["mask"] == 0].mean())
                    if (data["mask"] == 0).any()
                    else None
                ),
                "note": "UNCALIBRATED_MODEL_SUPPORT_NOT_SENSORY_PROBABILITY; unobserved values are diagnostics, never negative labels",
            }
            for task, data in tasks.items()
        }
    return result.x.tolist(), receipt


def fit(
    records,
    manifest_hash,
    C=1.0,
    kind="M2_R1_FIXED",
    vocabulary=None,
    tag="",
    bank_override=None,
    loss_mode="layered",
    task_weights=None,
    arrays=None,
):
    bundle = make_bundle(records, kind, manifest_hash, vocabulary, tag, bank_override)
    X, Y, w, audit, tasks = (
        training_arrays(records, bundle, manifest_hash, loss_mode, bank_override)
        if arrays is None
        else arrays
    )
    scales = np.sqrt(np.mean(X * X, axis=(0, 1)))
    scales[scales < 1e-8] = 1.0
    scales[s.FEATURES.index("exposed_rejection")] = 1.0
    weights, receipt = fit_shared(
        X / scales, Y, w, C, kind, loss_mode, tasks, task_weights
    )
    bundle["scaler_parameters"] = {
        "mean": [0.0] * len(s.FEATURES),
        "scale": scales.tolist(),
        "basis": "RMS_OF_INNER_OOF_TRAIN_CANDIDATE_FEATURES",
    }
    bundle["model_parameters"]["weights"] = weights
    receipt["inner_feature_audit"] = audit
    bundle["fit_receipt"] = receipt
    bundle["bundle_id"] = (
        "m2-r1:"
        + tag
        + ":"
        + s.digest([bundle["bundle_id"], weights, scales.tolist(), loss_mode])[:20]
    )
    s.check_bundle(bundle)
    return bundle, receipt


def evaluate_record(record, bundle, policy="fixed", path="P1"):
    ep, states, answers = trajectory(record, bundle, path, policy)
    payload = {
        "contract_version": s.VERSIONS["contract_version"],
        "context": ep["context"],
        "path": path,
        "policy": policy,
        "answers": answers,
    }
    before = time.perf_counter()
    result = s.evaluation_entry(payload, bundle)
    elapsed = (time.perf_counter() - before) * 1000
    state = result["state"]
    rank = [r["candidate_id"] for r in state["candidate_scores"]]
    raw_rank = [
        r["candidate_id"]
        for r in sorted(state["candidate_scores"], key=lambda r: r["raw_rank"])
    ]
    exclude = set(ep["visible"]) | {
        "attribute." + a
        for c in ep["visible"]
        for a in bundle["candidate_attributes"].get(c, [])
    }
    recovery, raw_recovery = [c for c in rank if c not in exclude], [
        c for c in raw_rank if c not in exclude
    ]
    hidden = set(ep["hidden"])
    direct = set(state["interpreted_evidence"]["specific"])
    outputs = [r["candidate_id"] for r in result["main"] + result["secondary"]]
    row = {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "model": bundle["model_kind"],
        "ndcg5": ndcg(recovery, ep["relevance"]) if hidden else None,
        "raw_ndcg5": ndcg(raw_recovery, ep["relevance"]) if hidden else None,
        "recall5": len(set(recovery[:5]) & hidden) / len(hidden) if hidden else None,
        "recall8": len(set(recovery[:8]) & hidden) / len(hidden) if hidden else None,
        "direct_retention8": (
            len(set(outputs) & direct) / len(direct) if direct else None
        ),
        "raw_direct_retention8": (
            len(set(raw_rank[:8]) & direct) / len(direct) if direct else None
        ),
        "coverage": bool(outputs),
        "candidate_target_coverage": (
            len(hidden & set(bundle["candidate_vocabulary"])) / len(hidden)
            if hidden
            else None
        ),
        "duplicate_rate": 1 - len(set(outputs)) / max(len(outputs), 1),
        "latency_ms": elapsed,
        "question_count": len(answers),
        "option_budget": sum(len(a["shown_option_ids"]) for a in answers),
        "ranking": rank,
        "raw_ranking": raw_rank,
        "recovery_ranking": recovery,
        "episode": ep,
        "payload": payload,
        "state": state,
    }
    for label, selector in [
        ("leaf", lambda c: c.startswith("sensory.")),
        ("broad", lambda c: not c.startswith("sensory.")),
    ]:
        targets = {c: v for c, v in ep["relevance"].items() if selector(c)}
        subrank = [c for c in recovery if selector(c)]
        row[label + "_ndcg5"] = ndcg(subrank, targets) if targets else None
        row[label + "_recall8"] = (
            len(set(subrank[:8]) & set(targets)) / len(targets) if targets else None
        )
        row[label + "_target_count"] = len(targets)
    return row


def mechanism_checks(old_bundle, new_bundle):
    """Paired executable diagnostics on frozen weights; synthetic states are not sensory labels."""
    import flavor_sequential as old_s

    context = {"c0": s.C0[0], "c1": "medium"}
    before, after = {}, {}
    failures = {"old": 0, "r1": 0}
    cases = []
    for backend, bundle, tag in [(old_s, old_bundle, "old"), (s, new_bundle, "r1")]:
        initial = backend.initial_state(context, bundle)
        base = {
            r["candidate_id"]: r
            for r in backend.compute_scores(
                backend.encode_features(initial, bundle), bundle
            )
        }
        for attr in s.ATTRS:
            alternatives = [a for a in s.ATTRS if a != attr][:1]
            opts = [
                {"id": "attribute." + a, "kind": "broad", "attribute": a}
                for a in [attr] + alternatives
            ]
            test = copy.deepcopy(initial)
            test["answers_by_question"]["Q0"] = {
                "slot": "Q0",
                "question_id": "synthetic-mechanism:" + attr,
                "axis": "broad.diagnostic",
                "options": opts,
                "shown_option_ids": [o["id"] for o in opts],
                "selected_option_ids": ["attribute." + attr],
                "state": "SELECTED",
            }
            rows = backend.compute_scores(backend.encode_features(test, bundle), bundle)
            deltas = []
            for row in rows:
                c = row["candidate_id"]
                if c.startswith("sensory.") and attr in bundle[
                    "candidate_attributes"
                ].get(c, []):
                    semantic = sum(
                        row["components"].get(n, 0.0)
                        - base[c]["components"].get(n, 0.0)
                        for n in [
                            "broad_related_support",
                            "unsupported_specificity",
                            "exposed_rejection",
                            "attribute_overlap",
                        ]
                    )
                    deltas.append(
                        {
                            "candidate_id": c,
                            "semantic_component_delta": semantic,
                            "score_delta": row["score"] - base[c]["score"],
                        }
                    )
                    failures[tag] += semantic < -1e-10
            if tag == "old":
                before[attr] = deltas
            else:
                after[attr] = deltas
        # The actual Q0 contains a local subset (<=4 of nine); selecting every
        # exposed direction remains genuine support rather than erasing it.
        planned = (
            s.select_next_question(initial, bundle)
            if tag == "r1"
            else __import__("flavor_planning").select_next_question(initial, bundle)
        )["question"]
        answer = {
            k: planned[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
        }
        answer.update(selected_option_ids=planned["shown_option_ids"], state="SELECTED")
        all_selected = backend.update_joint_state(initial, answer, bundle)
        none_answer = dict(answer, selected_option_ids=[], state="NONE_OF_THESE")
        rejected = backend.update_joint_state(initial, none_answer, bundle)
        all_features = backend.encode_features(all_selected, bundle)
        initial_features = backend.encode_features(initial, bundle)
        negative_rows = backend.compute_scores(
            backend.encode_features(rejected, bundle), bundle
        )
        cases.append(
            {
                "model": tag,
                "local_all_shown_selected_support_count": len(
                    backend.evidence(all_selected, bundle)["broad"]
                ),
                "local_all_shown_selected_changes_features": all_features[
                    "raw_features"
                ]
                != initial_features["raw_features"],
                "explicit_none_candidates_with_negative_score_delta": sum(
                    r["score"] < base[r["candidate_id"]]["score"] - 1e-10
                    for r in negative_rows
                ),
                "unselected_choices_automatically_negative": False,
            }
        )
    return {
        "scope": "AUTOMATED_SEMANTIC_INVARIANTS_SYNTHETIC_STATES_NOT_SENSORY_EVALUATION",
        "broad_support": {
            "old_negative_child_contribution_count": int(failures["old"]),
            "r1_negative_child_contribution_count": int(failures["r1"]),
            "before": before,
            "after": after,
            "passed": failures["r1"] == 0,
        },
        "exposure_and_none": cases,
        "cluster_dependency": {
            "r1": new_bundle["cluster_model"]["kind"],
            "legacy_hier": "RETAINED_UNCHANGED",
        },
        "score_and_postprocessing_separate": True,
        "confirmation_is_not_negative_evidence": True,
        "mask_summary": new_bundle.get("fit_receipt", {}).get("mask_counts", {}),
        "q01_training_selection": new_bundle["question_bank"].get(
            "initial_pair_selection",
            {"status": "FROZEN_LEGACY_BANK_FOR_MATCHED_REPAIR"},
        ),
    }


def initial_stage_diagnostics(records, bundle):
    """Fixed T across Q0, Q1-only diagnostic, Q0+Q1 and first correction."""
    rows = []
    patterns0, patterns1 = [], []
    for record in records:
        ep, states, answers = trajectory(record, bundle)
        q0, q01 = states[1], states[2]
        q1_only = copy.deepcopy(q01)
        q1_only["answers_by_question"]["Q0"]["selected_option_ids"] = []
        q1_only["answers_by_question"]["Q0"]["state"] = "UNSURE"
        q1_only = s.recompute(q1_only, bundle)
        pattern0, pattern1 = tuple(answers[0]["selected_option_ids"]), tuple(
            answers[1]["selected_option_ids"]
        )
        patterns0.append(pattern0)
        patterns1.append(pattern1)
        exclude = set(ep["visible"]) | {
            "attribute." + a
            for c in ep["visible"]
            for a in bundle["candidate_attributes"].get(c, [])
        }
        stage_rows = {}
        for label, state in [
            ("Q0", q0),
            ("Q1_ONLY_DIAGNOSTIC_MASKED_Q0", q1_only),
            ("Q0_PLUS_Q1", q01),
            ("FIRST_CORRECTION", states[3]),
        ]:
            rank = [
                r["candidate_id"]
                for r in state["candidate_scores"]
                if r["candidate_id"] not in exclude
            ]
            stage_rows[label] = {
                "ndcg5": ndcg(rank, ep["relevance"]),
                "recall8": len(set(rank[:8]) & set(ep["hidden"]))
                / max(len(ep["hidden"]), 1),
            }
        attrs0 = set(q0["sensory_attribute_state"]["observed_or_supported_attributes"])
        attrs01 = set(
            q01["sensory_attribute_state"]["observed_or_supported_attributes"]
        )
        rows.append(
            {
                "record_id": record["record_id"],
                "group_id": record["group_id"],
                "source_family": record["source_family"],
                "q1_effective_selection": bool(pattern1),
                "q1_response_pattern": list(pattern1),
                "q1_new_supported_attributes": sorted(attrs01 - attrs0),
                "q1_changes_features": q0["features"] != q01["features"],
                "q1_feature_delta_l2": float(
                    np.linalg.norm(
                        np.asarray(q01["features"]) - np.asarray(q0["features"])
                    )
                ),
                "stages": stage_rows,
                "fixed_target_ids": ep["hidden"],
            }
        )
    return {
        "scope": "DERIVED_RECORD_PROXY; Q1_ONLY_IS_EVIDENCE_ABLATION_NOT_A_NEW_PRODUCT_PATH",
        "record_rows": rows,
        "q1_effective_selection_rate": sum(r["q1_effective_selection"] for r in rows)
        / max(len(rows), 1),
        "q1_feature_change_rate": sum(r["q1_changes_features"] for r in rows)
        / max(len(rows), 1),
        "q1_conditional_response_entropy_bits": max(
            0.0, entropy(list(zip(patterns0, patterns1))) - entropy(patterns0)
        ),
        "q1_response_patterns": {
            "|".join(k) or "UNSURE": n for k, n in sorted(Counter(patterns1).items())
        },
        "relevant_coefficient_directions": {
            name: bundle["model_parameters"]["weights"][s.FEATURES.index(name)]
            for name in [
                "broad_related_support",
                "broad_candidate_direct",
                "exposed_rejection",
            ]
        },
        "q1_option_target_scope": {
            o["id"]: {
                "in_candidate_vocabulary": o["id"] in bundle["candidate_vocabulary"],
                "records_with_direct_same_level_target": sum(
                    o["id"] in r["targets"] for r in records
                ),
            }
            for o in bundle["question_bank"]["initial_1"]["options"]
        },
    }
