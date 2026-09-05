#!/usr/bin/env python3
"""Fit and evaluate the first licensed masked-descriptor recovery model."""

from __future__ import annotations
import argparse, copy, hashlib, itertools, json, math, platform, subprocess, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
import flavor_backend as engine

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-model-20260905"
SEED = 20260905


def save(path, obj):
    path.write_text(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )


def ordered(values, salt):
    return sorted(
        values,
        key=lambda x: hashlib.sha256(
            (str(SEED) + "|" + salt + "|" + x).encode()
        ).hexdigest(),
    )


def source_answers(visible, bundle):
    result = []
    for q in engine.question_bank(bundle["vocabulary"]):
        if q["question_id"] == "q.direction":
            continue
        selected = [o["option_id"] for o in q["options"] if o["option_id"] in visible]
        if selected:
            result.append(
                {
                    "question_id": q["question_id"],
                    "shown_option_ids": [o["option_id"] for o in q["options"]],
                    "selected_option_ids": selected,
                    "state": "SELECTED",
                }
            )
    return result


def episodes(records, bundle, masks):
    result = []
    group_sizes = Counter(r["group_id"] for r in records)
    for r in records:
        for i in range(masks):
            targets = ordered(r["targets"], r["record_id"] + "|mask|" + str(i))
            n = min(3, len(targets) // 2)
            visible = targets[:n]
            hidden = targets[n:]
            assert hidden and not set(hidden) & set(visible)
            answers = source_answers(visible, bundle)
            result.append(
                {
                    "episode_id": engine.fingerprint([r["record_id"], i])[:24],
                    "record_id": r["record_id"],
                    "group_id": r["group_id"],
                    "split": r["split"],
                    "visible": visible,
                    "hidden": hidden,
                    "answers": answers,
                    "source_context": {"c0": r["c0"], "c1": r["c1"]},
                    "weight": 1 / (masks * group_sizes[r["group_id"]]),
                }
            )
    return result


def make_bundle(train):
    assert all(r["split"] == "TRAIN" for r in train)
    by_group = defaultdict(set)
    evidence = defaultdict(set)
    for r in train:
        by_group[r["group_id"]].update(r["targets"])
        for c in r["targets"]:
            evidence[c].add("source-group:" + r["group_id"])
    vocab = sorted(set.union(*by_group.values()))
    counts = Counter(c for s in by_group.values() for c in s)
    co = Counter((a, b) for s in by_group.values() for a in s for b in s if a != b)
    pairs = [
        list(p)
        for p, n in sorted(
            Counter(
                tuple(sorted((a, b)))
                for s in by_group.values()
                for a, b in itertools.combinations(sorted(s), 2)
            ).items()
        )
        if n >= 3
    ]
    conditional = {
        a: {b: co[a, b] / counts[a] for b in vocab if a != b and co[a, b] >= 2}
        for a in vocab
    }
    priors = {
        c: math.log((counts[c] + 1) / (len(by_group) + len(vocab))) for c in vocab
    }
    adjustments = {}
    for key in ["c0", "c1"]:
        for value in sorted({r[key] for r in train if r[key] is not None}):
            local = {r["group_id"]: set(r["targets"]) for r in train if r[key] == value}
            if len(local) < 5:
                continue
            freq = Counter(c for s in local.values() for c in s)
            adjustments[key + ":" + value] = {
                c: max(
                    -0.25,
                    min(
                        0.25,
                        math.log((freq[c] + 1) / (len(local) + len(vocab))) - priors[c],
                    ),
                )
                for c in vocab
            }
    bundle = {
        "bundle_id": "backend-flavor-record-recovery-20260905",
        "vocabulary": vocab,
        "priors": priors,
        "conditional": conditional,
        "interaction_pairs": pairs,
        "context_adjustments": adjustments,
        "candidate_rights": {c: "ADMITTED_SOURCE_CONDITIONS_SATISFIED" for c in vocab},
        "candidate_source_artifacts": {
            c: ["artifact-b2:85df699ea18f5849ef310410"] for c in vocab
        },
        "evidence_by_candidate": {c: sorted(v) for c, v in evidence.items()},
        "train_records": [
            {"group_id": g, "targets": sorted(s)} for g, s in sorted(by_group.items())
        ],
        "question_gain_threshold": 0.01,
        "fit_id": "M1_RECORD_RECOVERY_PROXY",
        "source_scope": "CC BY-NC 4.0 restrictive scope; local noncommercial research only",
    }
    return bundle


def ndcg(ranking, relevance, k=5):
    dcg = sum(relevance.get(c, 0) / math.log2(i + 2) for i, c in enumerate(ranking[:k]))
    ideal = sum(
        x / math.log2(i + 2)
        for i, x in enumerate(sorted(relevance.values(), reverse=True)[:k])
    )
    return dcg / ideal if ideal else 0.0


def evaluate(episode, bundle, model, ablate=()):
    start = time.perf_counter()
    rows = engine._scores(
        episode["answers"], episode["source_context"], bundle, model, ablate
    )
    elapsed = (time.perf_counter() - start) * 1000
    ranking = [r["candidate_id"] for r in rows]
    visible = set(episode["visible"])
    hidden = set(episode["hidden"])
    recovery = [c for c in ranking if c not in visible]
    return {
        "episode_id": episode["episode_id"],
        "record_id": episode["record_id"],
        "group_id": episode["group_id"],
        "model": model,
        "ranking": ranking[:8],
        "recovery_ranking": recovery[:8],
        "observed_recovery_ndcg_at_5": ndcg(recovery, {c: 1 for c in hidden}),
        "observed_recovery_recall_at_5": len(set(recovery[:5]) & hidden) / len(hidden),
        "observed_recovery_recall_at_8": len(set(recovery[:8]) & hidden) / len(hidden),
        "direct_restatement_recall_at_5": (
            len(set(ranking[:5]) & visible) / len(visible) if visible else None
        ),
        "coverage": bool(ranking),
        "duplicate_rate": 1 - len(set(ranking[:8])) / max(len(ranking[:8]), 1),
        "latency_ms": elapsed,
        "unseen_hidden_count": len(hidden - set(bundle["vocabulary"])),
        "hidden_count": len(hidden),
        "visible_count": len(visible),
        "question_count": len(episode["answers"]),
    }


def average(rows, key):
    groups = defaultdict(list)
    for r in rows:
        if r[key] is not None:
            groups[r["group_id"]].append(r[key])
    return float(np.mean([np.mean(v) for v in groups.values()])) if groups else None


def fit(owner):
    if (owner / "models/M1.model.json").exists():
        raise RuntimeError(
            "Core model is frozen; do not refit or overwrite it. Reproduce the recorded commit in an isolated directory."
        )
    started = time.time()
    records = json.loads((owner / "records.json").read_text())
    train = [r for r in records if r["split"] == "TRAIN"]
    dev = [r for r in records if r["split"] == "DEV"]
    test = [r for r in records if r["split"] == "TEST"]
    assert not ({r["group_id"] for r in train} & {r["group_id"] for r in dev + test})
    assert not ({r["group_id"] for r in dev} & {r["group_id"] for r in test})
    bundle = make_bundle(train)
    train_eps = episodes(train, bundle, 4)
    dev_eps = episodes(dev, bundle, 1)
    feature_names = (
        ["observed:" + c for c in bundle["vocabulary"]]
        + ["family:" + g for g in engine.GROUPS]
        + ["cooccurrence:" + c for c in bundle["vocabulary"]]
        + ["c0:" + c for c in engine.C0]
        + ["c1:" + c for c in engine.C1]
        + ["pair:" + "|".join(p) for p in bundle["interaction_pairs"]]
    )
    config = {
        "experiment_id": bundle["bundle_id"],
        "task": "RECORD_RECOVERY_PROXY",
        "primary_metric": "coffee-group-mean observed descriptor recovery NDCG@5; not real sensory accuracy",
        "loss": "L2-regularized conditional multinomial likelihood of actually observed withheld descriptors; candidate competition is a record-token recovery task, not sensory negative labels",
        "seed": SEED,
        "model": "M1 regularized linear candidate logit scorer plus explicitly separate direct-answer reference effect",
        "parameter_candidates": {"C": [0.1, 1.0, 10.0]},
        "selection": "DEV observed-recovery NDCG@5; smallest C on tie; TEST not consulted",
        "solver": "lbfgs",
        "max_iter": 1000,
        "threads": 1,
        "train_masks_per_record": 4,
        "evaluation_masks_per_record": 1,
        "visible_budget": "at most 3 observed descriptors, withheld set disjoint and never included in answers/features",
        "group_weighting": "each coffee group total training weight 1 across records, masks and withheld targets",
        "features": feature_names,
        "cooccurrence_scope": "TRAIN coffee groups only; minimum 2 group pair support",
        "interaction_scope": "TRAIN pair support >=3 groups",
        "baselines": {
            "B0": "TRAIN group-frequency/context baseline; no answers",
            "B1": "Legacy v0.1 +3/-1.25 question effects with TRAIN-only priors/context to prevent frozen corpus-statistic leakage; same candidate scope",
            "B2": "Evidence-deduplicated bounded direct/hierarchical effects; unselected neutral, no keyword claim matching",
            "M1": "Actually fitted regularized linear conditional recovery logits",
        },
        "independent_real_answer_evaluation_cases": 0,
        "policy_simulation": "When reported, answers are generated solely from a pre-frozen visible descriptor subset; no selected unseen target, unknown outcome is UNSURE, never a fabricated negative",
        "test_lock": "Split membership frozen in dataset_manifest before graph/features/weights; no TEST-based revisions",
        "source_c0_missing": "Internal auxiliary feature mask only; external context schema still requires complete c0/c1",
        "version": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    save(OUT / "experiment_config.json", config)
    X = []
    y = []
    weights = []
    for e in train_eps:
        f = engine.features(e["answers"], e["source_context"], bundle)
        vector = [f.get(n, 0) for n in feature_names]
        for target in e["hidden"]:
            assert target not in e["visible"]
            X.append(vector)
            y.append(target)
            weights.append(e["weight"] / len(e["hidden"]))
    X = np.array(X)
    weights = np.array(weights)
    trials = []
    fitted = []
    with threadpool_limits(limits=1):
        for strength in config["parameter_candidates"]["C"]:
            clf = LogisticRegression(
                C=strength, solver="lbfgs", max_iter=1000, tol=1e-7, random_state=SEED
            )
            clf.fit(X, y, sample_weight=weights)
            trial = copy.deepcopy(bundle)
            trial["feature_names"] = feature_names
            trial["model_weights"] = {
                str(c): {n: float(w) for n, w in zip(feature_names, row) if w != 0}
                for c, row in zip(clf.classes_, clf.coef_)
            }
            trial["model_intercepts"] = {
                str(c): float(v) for c, v in zip(clf.classes_, clf.intercept_)
            }
            score = average(
                [evaluate(e, trial, "M1") for e in dev_eps],
                "observed_recovery_ndcg_at_5",
            )
            trials.append(
                {
                    "C": strength,
                    "dev_ndcg": score,
                    "iterations": clf.n_iter_.tolist(),
                    "training_rows": len(y),
                    "training_groups": len({r["group_id"] for r in train}),
                }
            )
            fitted.append(trial)
    chosen = max(
        range(len(trials)), key=lambda i: (trials[i]["dev_ndcg"], -trials[i]["C"])
    )
    bundle = fitted[chosen]
    bundle["selected_C"] = trials[chosen]["C"]
    bundle["feature_configuration_sha256"] = engine.fingerprint(config)
    models = owner / "models"
    models.mkdir(mode=0o700, exist_ok=True)
    save(models / "M1.model.json", bundle)
    (models / "M1.model.json").chmod(0o600)
    # Reload the retained artifact before consulting TEST exactly once.
    bundle = json.loads((models / "M1.model.json").read_text())
    test_eps = episodes(test, bundle, 1)
    predictions = [
        evaluate(e, bundle, m) for e in test_eps for m in ["B0", "B1", "B2", "M1"]
    ]
    metrics = {
        m: {
            key: average([r for r in predictions if r["model"] == m], key)
            for key in [
                "observed_recovery_ndcg_at_5",
                "observed_recovery_recall_at_5",
                "observed_recovery_recall_at_8",
                "direct_restatement_recall_at_5",
                "coverage",
                "duplicate_rate",
            ]
        }
        for m in ["B0", "B1", "B2", "M1"]
    }
    for m in metrics:
        latency = [r["latency_ms"] for r in predictions if r["model"] == m]
        metrics[m]["latency_p50_ms"] = float(np.median(latency))
        metrics[m]["latency_p95_ms"] = float(np.percentile(latency, 95))
    paired = {}
    for baseline in ["B0", "B1", "B2"]:
        groups = sorted({e["group_id"] for e in test_eps})
        delta = []
        for g in groups:
            a = [r for r in predictions if r["group_id"] == g and r["model"] == "M1"]
            b = [
                r for r in predictions if r["group_id"] == g and r["model"] == baseline
            ]
            delta.append(
                np.mean([r["observed_recovery_ndcg_at_5"] for r in a])
                - np.mean([r["observed_recovery_ndcg_at_5"] for r in b])
            )
        rng = np.random.default_rng(SEED)
        samples = np.array(delta)[rng.integers(0, len(delta), (5000, len(delta)))].mean(
            axis=1
        )
        paired[baseline] = {
            "group_count": len(delta),
            "delta": float(np.mean(delta)),
            "paired_group_bootstrap_95_interval": np.quantile(
                samples, [0.025, 0.975]
            ).tolist(),
            "bootstrap_resamples": 5000,
        }
    lower = paired["B1"]["paired_group_bootstrap_95_interval"][0]
    conclusion = (
        "PROXY_IMPROVEMENT_SUPPORTED"
        if lower > 0 and metrics["M1"]["coverage"] >= metrics["B1"]["coverage"]
        else "NO_IMPROVEMENT" if paired["B1"]["delta"] <= 0 else "INCONCLUSIVE"
    )
    result = {
        "task": "RECORD_RECOVERY_PROXY",
        "conclusion": conclusion,
        "real_product_conclusion": "INCONCLUSIVE",
        "real_independent_answer_cases": 0,
        "test_record_count": len(test_eps),
        "test_group_count": len({e["group_id"] for e in test_eps}),
        "candidate_count": len(bundle["vocabulary"]),
        "all_legal_test_cases_reported": True,
        "models": metrics,
        "paired_group_uncertainty": paired,
        "dev_trials": trials,
        "selected_C": trials[chosen]["C"],
        "no_test_tuning": True,
        "unseen_test_hidden_descriptor_count": sum(
            e["unseen_hidden_count"] for e in predictions if e["model"] == "M1"
        ),
        "interpretation": "Recovery of recorded positive descriptions only; unlabelled candidates are not scored as true sensory errors. No real question-answer policy validation.",
    }
    save(OUT / "metrics.json", result)
    save(owner / "test_episodes.json", test_eps)
    (owner / "test_episodes.json").chmod(0o600)
    save(owner / "predictions.private.json", predictions)
    (owner / "predictions.private.json").chmod(0o600)
    # Public predictions omit source text, panelist names and full observed label sets.
    import csv

    with (OUT / "predictions.tsv").open("w", newline="") as f:
        keys = list(predictions[0])
        w = csv.DictWriter(f, keys, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in predictions:
            w.writerow(
                {k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()}
            )
    receipt = {
        "experiment_id": bundle["bundle_id"],
        "started_at_unix": started,
        "completed_at_unix": time.time(),
        "elapsed_seconds": time.time() - started,
        "code_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "code_worktree_status": "Development code hashes are authoritative until incremental commit; no test-label-based tuning",
        "code_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                Path(__file__),
                ROOT / "db/scripts/flavor_backend.py",
                ROOT / "db/scripts/prepare-backend-model-data.py",
            ]
        },
        "command": 'python db/scripts/run-backend-model.py --owner-root "$COFFEE_BACKEND_MODEL_ROOT"',
        "model_path": "$COFFEE_BACKEND_MODEL_ROOT/models/M1.model.json",
        "model_sha256": hashlib.sha256(
            (models / "M1.model.json").read_bytes()
        ).hexdigest(),
        "model_retained_and_reloaded": True,
        "model_fits": len(trials),
        "training_record_count": len(train),
        "training_independent_group_count": len({r["group_id"] for r in train}),
        "training_episode_count": len(train_eps),
        "training_target_rows": len(y),
        "conclusion": conclusion,
        "product_evidence_status": "INCONCLUSIVE; proxy only; no independent answer labels",
        "frontend_authorized": False,
    }
    save(OUT / "run_receipt.json", receipt)
    print(
        json.dumps(
            {
                "conclusion": conclusion,
                "metrics": metrics,
                "paired": paired,
                "model_path": str(models / "M1.model.json"),
                "elapsed_seconds": receipt["elapsed_seconds"],
            },
            indent=2,
        )
    )
    return bundle, test_eps, predictions


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-root", type=Path, required=True)
    a = p.parse_args()
    fit(a.owner_root)
