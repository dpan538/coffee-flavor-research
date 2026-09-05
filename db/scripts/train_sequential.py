"""Grouped, nested-feature fitting for shared candidate M2 models."""

from __future__ import annotations
import copy, hashlib, itertools, json, math, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp
from sklearn.decomposition import NMF
from threadpoolctl import threadpool_limits
import flavor_sequential as s
from flavor_context import CONTEXT_VERSION
from prepare_sequential_data import save, record_recovery

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-sequential-model-v2"
SEED = 20260905


def split_groups(records, k=3):
    result = {}
    for source in sorted({r["source_family"] for r in records}):
        groups = sorted(
            {r["group_id"] for r in records if r["source_family"] == source},
            key=lambda g: s.digest([SEED, g]),
        )
        result.update({g: i % k for i, g in enumerate(groups)})
    return result


def statistics(records, vocabulary=None):
    assert all(r["split"] == "DEVELOPMENT" for r in records)
    bygroup = defaultdict(set)
    for r in records:
        bygroup[r["group_id"]].update(r["targets"])
    vocab = (
        sorted(set().union(*bygroup.values()))
        if vocabulary is None
        else list(vocabulary)
    )
    counts = Counter(c for ts in bygroup.values() for c in ts)
    pairs = Counter((a, b) for ts in bygroup.values() for a in ts for b in ts if a != b)
    paircounts = Counter()
    triples = Counter()
    for ts in bygroup.values():
        for a, b in itertools.combinations(sorted(ts), 2):
            pair = "|".join([a, b])
            paircounts[pair] += 1
            for c in ts - {a, b}:
                triples[pair, c] += 1
    pc = {
        pair: {c: triples[pair, c] / n for c in vocab if triples[pair, c] >= 3}
        for pair, n in paircounts.items()
        if n >= 3
    }
    return {
        "vocabulary": vocab,
        "counts": dict(counts),
        "log_prior": {
            c: math.log((counts[c] + 1) / (len(bygroup) + len(vocab))) for c in vocab
        },
        "conditional": {
            a: {
                b: pairs[a, b] / max(counts[a], 1)
                for b in vocab
                if a != b and pairs[a, b] >= 2
            }
            for a in vocab
        },
        "pair_conditional": pc,
        "planning_records": [
            {"group_id": g, "targets": sorted(t)} for g, t in sorted(bygroup.items())
        ],
    }


def clusters(records, vocab):
    inera = [
        r
        for r in records
        if r["source_family"] == "inera"
        and all(v is not None for v in r["attribute_values"])
    ]
    if len(inera) < 3:
        raise ValueError("INSUFFICIENT_TRAINING_ATTRIBUTE_MATRIX")
    names = inera[0]["attribute_names"]
    X = np.array([r["attribute_values"] for r in inera]) / 9.0
    with threadpool_limits(limits=1):
        nmf = NMF(
            n_components=3, init="nndsvda", random_state=SEED, max_iter=1000, tol=1e-5
        )
        W = nmf.fit_transform(X)
        H = nmf.components_
    H = H / np.maximum(np.linalg.norm(H, axis=1, keepdims=True), 1e-12)
    memberships = {}
    for c in vocab:
        ix = [names.index(a) for a in s.PARENTS.get(c, []) if a in names]
        v = H[:, ix].mean(1) if ix else np.zeros(3)
        memberships[c] = (v / max(float(np.linalg.norm(v)), 1e-12)).tolist()
    return memberships, {
        "kind": "NMF_ON_COMPLETE_SOURCE_NATIVE_FREQUENCIES",
        "training_groups": sorted({r["group_id"] for r in inera}),
        "attribute_names": names,
        "components": H.tolist(),
        "reconstruction_error": float(nmf.reconstruction_err_),
        "missing_cell_rows_excluded_from_factor_fit": sum(
            r["source_family"] == "inera" for r in records
        )
        - len(inera),
        "compound_preservation": "nutty_cocoa is one source dimension; factor memberships overlap, never exclusive class labels",
    }


def make_bank(stats, attributes):
    vocab = stats["vocabulary"]
    counts = stats["counts"]
    attrcounts = {
        a: sum(counts.get(c, 0) for c in vocab if a in attributes.get(c, []))
        for a in s.ATTRS
    }
    ordered = sorted(s.ATTRS, key=lambda a: (-attrcounts[a], a))

    def broad(axis, attrs):
        return {
            "axis": axis,
            "options": [
                {"id": "attribute." + a, "kind": "broad", "attribute": a} for a in attrs
            ],
            "priority": sum(attrcounts[a] for a in attrs),
        }

    bank = {
        "initial_0": broad("broad.initial0", ordered[:4]),
        "initial_1": broad("broad.initial1", ordered[4:8]),
        "correction": [],
    }
    for a in ordered:
        choices = sorted(
            [
                c
                for c in vocab
                if a in attributes.get(c, []) and c.startswith("sensory.")
            ],
            key=lambda c: (-counts.get(c, 0), c),
        )[:4]
        # Source-native compound attributes can remain literal broad choices.
        if not choices and "attribute." + a in vocab:
            choices = ["attribute." + a]
        opts = [
            {
                "id": c,
                "kind": "specific" if c.startswith("sensory.") else "broad",
                "attribute": a,
            }
            for c in choices
        ]
        if opts:
            patterns = Counter(
                tuple(o["id"] for o in opts if o["id"] in r["targets"])
                for r in stats["planning_records"]
            )
            if sum(n >= 2 for n in patterns.values()) >= 2:
                bank["correction"].append(
                    {"axis": "refine." + a, "options": opts, "priority": attrcounts[a]}
                )
    if len(bank["correction"]) < 4:
        raise ValueError("Insufficient train-qualified finite question axes")
    return bank


def make_bundle(records, kind, manifest_hash, vocabulary=None, tag=""):
    stats = statistics(records, vocabulary)
    vocab = stats.pop("vocabulary")
    attributes = {c: s.PARENTS.get(c, []) for c in vocab}
    membership, factor = clusters(records, vocab)
    bank = make_bank(dict(stats, vocabulary=vocab), attributes)
    bundle = {
        **s.VERSIONS,
        "bundle_id": "m2:"
        + tag
        + ":"
        + s.digest([kind, sorted({r["group_id"] for r in records})])[:16],
        "model_kind": kind,
        "candidate_vocabulary": vocab,
        "candidate_attributes": attributes,
        "candidate_clusters": membership,
        "cluster_dimension": 3,
        "cluster_model": factor,
        "scaler_parameters": {
            "mean": [0.0] * len(s.FEATURES),
            "scale": [1.0] * len(s.FEATURES),
        },
        "model_parameters": {
            "feature_names": s.FEATURES,
            "weights": [
                1.0,
                2.0,
                1.0,
                0.1,
                0.2,
                0.2,
                0.0,
                -0.25,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.2,
            ],
        },
        "statistics": stats,
        "question_bank": bank,
        "training_split_hash": s.digest(sorted({r["group_id"] for r in records})),
        "data_manifest_hash": manifest_hash,
        "candidate_rights": {c: "ADMITTED" for c in vocab},
        "seed": SEED,
        "question_cost": 0.01,
        "context_descriptor_support": {
            "C0": False,
            "C1": False,
            "reason": "No validated context paired with these descriptor trajectories. Shared encoder masks these components identically during fitting and live inference.",
        },
        "context_attribute_models": {},
    }
    return bundle


def visible_episode(record):
    targets = sorted(
        record["targets"], key=lambda c: s.digest([SEED, record["record_id"], c])
    )
    n = min(3, len(targets) // 2)
    visible = targets[:n]
    closure = set(visible) | {
        "attribute." + a for c in visible for a in s.PARENTS.get(c, [])
    }
    hidden = [c for c in targets if c not in closure]
    if not hidden:
        visible = []
        hidden = targets
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "visible": visible,
        "hidden": hidden,
        "relevance": {c: record["relevance"][c] for c in hidden},
        "source_context_available": False,
        "context": {"c0": s.C0[0], "c1": "medium"},
        "context_assignment_status": "EXPLICIT_SIMULATION_SETTING_ONLY_NOT_SOURCE_C0_C1_LABEL",
    }


def answer_for(q, visible, bundle):
    v = set(visible)
    attrs = {a for c in visible for a in bundle["candidate_attributes"].get(c, [])}
    chosen = [
        o["id"]
        for o in q["options"]
        if (o["kind"] == "specific" and o["id"] in v)
        or (o["kind"] == "broad" and o["attribute"] in attrs)
    ]
    return {k: q[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]} | {
        "selected_option_ids": chosen,
        "state": "SELECTED" if chosen else "UNSURE",
    }


def trajectory(record, bundle, path="P1", policy="fixed"):
    ep = visible_episode(record)
    state = s.initial_state(ep["context"], bundle, path, policy)
    states = [copy.deepcopy(state)]
    answers = []
    from flavor_planning import select_next_question

    while True:
        nxt = select_next_question(state, bundle)
        if nxt["action"] != "ASK":
            break
        a = answer_for(nxt["question"], ep["visible"], bundle)
        state = s.update_joint_state(state, a, bundle)
        answers.append(a)
        states.append(copy.deepcopy(state))
        if len(answers) > 6:
            raise AssertionError("ordinary question limit violated")
    return ep, states, answers


def training_arrays(records, outer_bundle, manifest_hash):
    # Every sample's predictive statistics/factors are built without that sample's
    # group. No true laboratory value is supplied to the shared feature entry.
    inner = split_groups(records, 2)
    Xs = []
    Ys = []
    weights = []
    audit = []
    vocab = outer_bundle["candidate_vocabulary"]
    lookup = {c: i for i, c in enumerate(vocab)}
    source_groups = Counter(
        next(r["source_family"] for r in records if r["group_id"] == g)
        for g in {r["group_id"] for r in records}
    )
    group_rows = Counter(r["group_id"] for r in records)
    for fold in range(2):
        train = [r for r in records if inner[r["group_id"]] != fold]
        held = [r for r in records if inner[r["group_id"]] == fold]
        bundle = make_bundle(
            train,
            outer_bundle["model_kind"],
            manifest_hash,
            vocab,
            tag="inner" + str(fold),
        )
        audit.append(
            {
                "feature_training_groups": sorted({r["group_id"] for r in train}),
                "feature_output_groups": sorted({r["group_id"] for r in held}),
            }
        )
        for r in held:
            ep, states, answers = trajectory(r, bundle, path="P4")
            # Q0 and Q1 prefixes are both present, even when their answer is UNSURE.
            assert all(q in states[-1]["answers_by_question"] for q in ["Q0", "Q1"])
            preliminary = s.finalize_result(states[-1], bundle)
            exposure = preliminary["exposure"]
            selected = (
                [c for c in exposure["candidate_ids"] if c in ep["visible"]]
                if exposure
                else []
            )
            if exposure and exposure["eligible_for_final_comparison"]:
                feedback = s.apply_final_comparison(
                    states[-1],
                    exposure["candidate_ids"],
                    selected,
                    bundle,
                    feedback_source="SIMULATED",
                    generation_version=bundle["bundle_id"],
                )
                states.append(feedback)
            mass = 1 / (
                group_rows[r["group_id"]]
                * source_groups[r["source_family"]]
                * len(states)
            )
            for state in states:
                enc = s.encode_features(state, bundle)
                x = np.array(enc["features"])
                y = np.zeros(len(vocab))
                hidden = [c for c in ep["hidden"] if c in lookup]
                direct = [
                    c
                    for c in s.evidence(state, bundle)["specific"]
                    + s.evidence(state, bundle)["feedback"]
                    if c in lookup
                ]
                direct = sorted(set(direct))
                if not hidden:
                    continue
                for c in hidden:
                    y[lookup[c]] += (
                        (0.7 if direct else 1.0)
                        * r["relevance"][c]
                        / sum(r["relevance"][h] for h in hidden)
                    )
                for c in direct:
                    y[lookup[c]] += 0.3 / len(direct)
                Xs.append(x)
                Ys.append(y)
                weights.append(mass)
    return np.array(Xs), np.array(Ys), np.array(weights), audit


def fit_shared(X, Y, weights, C, kind):
    weights = weights / weights.sum()
    active = np.ones(len(s.FEATURES))
    if kind == "M2_ADD":
        active[[10, 11, 12, 13]] = 0
    elif kind == "M2_JOINT":
        active[[12, 13]] = 0
    # Source-native context is not silently used then dropped at inference.
    active[[8, 9, 11]] = 0
    X = X * active

    def objective(w):
        logits = X @ w
        logp = logits - logsumexp(logits, axis=1, keepdims=True)
        prob = np.exp(logp)
        penalty = 0.005 / max(C, 1e-8)
        loss = -np.sum(weights[:, None] * Y * logp) + penalty * np.dot(w, w) / 2
        grad = np.einsum("nk,nkf,n->f", prob - Y, X, weights) + penalty * w
        return float(loss), grad

    bounds = [
        (
            (0, None)
            if n in {"specific_direct", "broad_candidate_direct", "feedback_direct"}
            else (None, 0) if n == "unsupported_specificity" else (None, None)
        )
        for n in s.FEATURES
    ]
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
        raise RuntimeError("SHARED_FIT_FAILED:" + str(result.message))
    return (result.x * active).tolist(), {
        "iterations": result.nit,
        "loss": float(result.fun),
        "training_states": len(X),
        "parameter_count": int(active.sum()),
        "C": C,
        "success": bool(result.success),
    }


def ndcg(ranking, relevance, k=5):
    values = sorted(relevance.values(), reverse=True)
    ideal = sum(v / math.log2(i + 2) for i, v in enumerate(values[:k]))
    return (
        sum(relevance.get(c, 0) / math.log2(i + 2) for i, c in enumerate(ranking[:k]))
        / ideal
        if ideal
        else 0.0
    )


def evaluate_record(r, bundle, policy="fixed", path="P1"):
    ep, states, answers = trajectory(r, bundle, path, policy)
    payload = {
        "contract_version": s.VERSIONS["contract_version"],
        "context": ep["context"],
        "path": path,
        "policy": policy,
        "answers": answers,
    }
    begin = time.perf_counter()
    result = s.evaluation_entry(payload, bundle)
    elapsed = (time.perf_counter() - begin) * 1000
    rank = [x["candidate_id"] for x in result["state"]["candidate_scores"]]
    exclude = set(ep["visible"]) | {
        "attribute." + a
        for c in ep["visible"]
        for a in bundle["candidate_attributes"].get(c, [])
    }
    recovery = [c for c in rank if c not in exclude]
    hidden = set(ep["hidden"])
    direct = set(result["state"]["interpreted_evidence"]["specific"])
    outputs = [x["candidate_id"] for x in result["main"] + result["secondary"]]
    return {
        "record_id": r["record_id"],
        "group_id": r["group_id"],
        "source_family": r["source_family"],
        "model": bundle["model_kind"],
        "ndcg5": ndcg(recovery, ep["relevance"]) if hidden else None,
        "recall5": len(set(recovery[:5]) & hidden) / len(hidden) if hidden else None,
        "recall8": len(set(recovery[:8]) & hidden) / len(hidden) if hidden else None,
        "direct_retention8": (
            len(set(outputs) & direct) / len(direct) if direct else None
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
        "recovery_ranking": recovery,
        "episode": ep,
        "payload": payload,
        "state": result["state"],
    }
