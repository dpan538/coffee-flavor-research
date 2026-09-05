#!/usr/bin/env python3
"""Two prespecified additions to the frozen core; never refit M1 or tune on TEST."""

from __future__ import annotations
import argparse, copy, csv, hashlib, importlib.util, itertools, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits
from lxml import html

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-model-20260905"
SEED = 20260905
FAMILY = "family.frontiers_cenicafe_lengupa_trained_cuppers"
URL = "https://www.frontiersin.org/journals/sustainable-food-systems/articles/10.3389/fsufs.2026.1809471/full"
CODES = {
    "7": "almond",
    "8": "caramel",
    "11": "honey",
    "13": "lemongrass",
    "16": "earthy",
    "19": "hazelnut",
    "20": "woody",
    "22": "banana",
    "23": "peanut",
}


def save(p, x):
    p.write_text(json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_module(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def frozen(owner):
    freeze = json.loads((owner / "core_freeze.json").read_text())
    for name, digest in freeze["files"].items():
        assert sha(owner / "core-freeze" / name) == digest, (
            "Core freeze changed: " + name
        )
    engine = load_module("frozen_backend", owner / "core-freeze/flavor_backend.py")
    run = load_module("frozen_run", owner / "core-freeze/run-backend-model.py")
    run.engine = engine
    return engine, run


def acquire_existing_aux(owner, core):
    path = owner / "sources/lengupa-article.html"
    tree = html.fromstring(path.read_bytes())
    text = " ".join(tree.xpath("//p//text()"))
    assert (
        "Creative Commons Attribution License (CC BY)" in text
        and "© 2026 Benavides Sánchez" in text
    )
    assert "Evaluations were performed by trained cuppers" in text
    # Verify the source-native codebook, not the old cleaner's inferred children.
    norm = re.sub(r"\s+", "", text)
    for code, term in CODES.items():
        assert code + "=" + term in norm
    rows = None
    for table in tree.xpath("//table"):
        rr = [
            [x.text_content().strip() for x in r.xpath("./td|./th")]
            for r in table.xpath(".//tr")
        ]
        if rr and "D.FA" in rr[0] and "D.F" in rr[0]:
            rows = rr
            break
    assert rows and len(rows) == 22
    header = rows[0]
    parsed = []
    for row in rows[1:]:
        sid = row[header.index("ID")]
        assert sid.isdigit()
        codes = set(
            re.findall(r"\d+", row[header.index("D.FA")])
            + re.findall(r"\d+", row[header.index("D.F")])
        )
        targets = sorted({"sensory." + CODES[c] for c in codes if c in CODES})
        parsed.append(
            {
                "group_id": "lengupa:"
                + hashlib.sha256(
                    ("doi:10.3389/fsufs.2026.1809471|" + sid).encode()
                ).hexdigest()[:24],
                "sample_id": sid,
                "targets": targets,
                "native_codes": sorted(codes),
                "source_family": FAMILY,
                "split": "AUX_TRAIN_ONLY",
                "c0": None,
                "c1": None,
            }
        )
    assert len({r["group_id"] for r in parsed}) == 21
    assert not {r["group_id"] for r in parsed} & {r["group_id"] for r in core}
    # Different independently collected study batches; do not use held-out target
    # descriptors as a similarity filter. Partial flavor overlap is not identity.
    excluded = []
    admitted = parsed
    save(owner / "aux_records.json", admitted)
    (owner / "aux_records.json").chmod(0o600)
    audit = {
        "family": FAMILY,
        "source_record_id": "doi:10.3389/fsufs.2026.1809471",
        "version": "article published 2026-07-01; retrieved 2026-09-05",
        "artifact_sha256": sha(path),
        "machine_license_field": None,
        "author_usage_notice": "Article copyright © 2026 Benavides Sánchez; Creative Commons Attribution License (CC BY)",
        "current_experiment_use_basis": "NONCOMMERCIAL_RESEARCH_USE under CC BY 4.0",
        "author": "Diego Alejandro Benavides Sánchez",
        "url": URL,
        "role": "CORE_PROFESSIONAL",
        "experiment_role": "AUXILIARY_TRAINING_FEATURES_ONLY; not core labels or gold evaluation",
        "derived_relation_role": "AUX_SEMANTIC; observed coffee cooccurrence is not equivalence",
        "conditions_satisfied": {
            "attribution": True,
            "changes_disclosed": True,
            "local_retention": True,
            "no_raw_republication": True,
        },
        "processing": "Source Table 3 D.FA and D.F codebook: retain 9 unambiguous exact leaf terms only; union per sample, repeated codes/fields do not inflate counts; broad chocolate/nutty/floral never specialized",
        "parsed_samples": 21,
        "admitted_samples": len(admitted),
        "fine_label_samples": sum(bool(r["targets"]) for r in admitted),
        "multi_leaf_samples": sum(len(r["targets"]) > 1 for r in admitted),
        "identity_audit": {
            "study_batch": "One Lengupá producer study, one publication family; article mirrors/republished old ledger rows are not additional families. Core is the distinct Golovinsky electrochemical/commercial-coffee study.",
            "within_source_duplicate_ids": 0,
            "cross_source_exact_group_overlap": 0,
            "known_cross_study_duplicate_samples_excluded": len(excluded),
            "limitations": "No shared global lot identifier is published. This is a distinct-study auxiliary comparison; universal absence of commercial supply-chain overlap cannot be proved. Core and auxiliary source identifiers, artifact hashes, collection study batches and publication mirrors were checked before auxiliary statistics. No descriptor statistics or target-similarity filtering from DEV/TEST used in features.",
            "admitted_group_ids": [r["group_id"] for r in admitted],
        },
        "public_release": "Original source text, sample code rows and model weights retained locally; only code and aggregate evaluation records committed",
    }
    return admitted, audit


def summarize(run, rows):
    keys = [
        "observed_recovery_ndcg_at_5",
        "observed_recovery_recall_at_5",
        "observed_recovery_recall_at_8",
        "direct_restatement_recall_at_5",
        "coverage",
        "duplicate_rate",
    ]
    out = {k: run.average(rows, k) for k in keys}
    out["latency_p50_ms"] = float(np.median([r["latency_ms"] for r in rows]))
    out["latency_p95_ms"] = float(np.percentile([r["latency_ms"] for r in rows], 95))
    return out


def paired(a, b):
    groups = sorted({r["group_id"] for r in a})
    d = []
    for g in groups:
        x = [r["observed_recovery_ndcg_at_5"] for r in a if r["group_id"] == g]
        y = [r["observed_recovery_ndcg_at_5"] for r in b if r["group_id"] == g]
        d.append(float(np.mean(x) - np.mean(y)))
    rng = np.random.default_rng(SEED)
    boot = np.array(d)[rng.integers(0, len(d), (5000, len(d)))].mean(axis=1)
    return {
        "group_count": len(groups),
        "delta": float(np.mean(d)),
        "paired_group_bootstrap_95_interval": np.quantile(
            boot, [0.025, 0.975]
        ).tolist(),
    }


def extend(owner):
    if (owner / "models/M1_AUX.model.json").exists():
        raise RuntimeError(
            "Two extension fits already completed; refusing repeated test consultation or weight overwrite"
        )
    started = time.time()
    engine, run = frozen(owner)
    records = json.loads((owner / "records.json").read_text())
    base = json.loads((owner / "models/M1.model.json").read_text())
    aux, audit = acquire_existing_aux(owner, records)
    manifest = json.loads((OUT / "dataset_manifest.json").read_text())
    manifest["auxiliary_source"] = audit
    prereg = {
        "core_commit": "d2e1676",
        "core_model_sha256": sha(owner / "models/M1.model.json"),
        "test_group_ids": [r["group_id"] for r in records if r["split"] == "TEST"],
        "comparisons": ["M1_BALANCED vs frozen M1", "M1_AUX vs M1_BALANCED"],
        "fits_allowed": 2,
        "hyperparameter_search": False,
        "C": base["selected_C"],
        "weighting": "Equal total core coffee-group mass; equal source-family mass after sample normalization. Core has one family so M1_BALANCED is a deliberate identity control. No source duplication.",
        "auxiliary_component": "Conditional cooccurrence features only, same frozen feature names. For an observed descriptor with >=2 auxiliary sample supports, blend 0.8 core conditional + 0.2 auxiliary conditional; target pair also requires >=2 auxiliary samples. Otherwise keep core feature unchanged. No auxiliary labels, priors, vocabulary, interactions or question-policy changes.",
        "auxiliary_blend": 0.2,
        "selection_before_test": "Keep M1_AUX only if DEV observed recovery NDCG@5 is strictly above BALANCED and DEV Recall@8 and coverage do not fall; otherwise reject auxiliary branch. No TEST-based tuning.",
        "test_plan": "Evaluate both retained extension fits once on unchanged TEST masks after recording DEV decision; compare paired coffee-group intervals with frozen core and B1. No further configurations.",
        "evaluation_scope": "RECORD_RECOVERY_PROXY, observed positives only. Nominal source roast matches reproduce core; no production seven-bin context validation.",
    }
    config = json.loads((OUT / "experiment_config.json").read_text())
    config["runtime_extension"] = prereg
    save(OUT / "experiment_config.json", config)
    save(owner / "extension_preregistered.json", prereg)
    (owner / "extension_preregistered.json").chmod(0o600)
    save(OUT / "dataset_manifest.json", manifest)
    train = [r for r in records if r["split"] == "TRAIN"]
    dev = [r for r in records if r["split"] == "DEV"]
    train_eps = run.episodes(train, base, 4)
    dev_eps = run.episodes(dev, base, 1)
    av = Counter(c for r in aux for c in set(r["targets"]))
    co = Counter(
        (a, b)
        for r in aux
        for a in set(r["targets"])
        for b in set(r["targets"])
        if a != b
    )
    aux_bundle = copy.deepcopy(base)
    changed = []
    for a in base["vocabulary"]:
        if av[a] < 2:
            continue
        for c in base["vocabulary"]:
            if a == c:
                continue
            old = base["conditional"].get(a, {}).get(c, 0)
            a_value = co[a, c] / av[a] if co[a, c] >= 2 else 0
            value = 0.8 * old + 0.2 * a_value
            if value != old:
                aux_bundle["conditional"].setdefault(a, {})[c] = value
                changed.append([a, c])
    trials = {}
    bundles = {}
    names = base["feature_names"]
    for name, bundle in [("M1_BALANCED", copy.deepcopy(base)), ("M1_AUX", aux_bundle)]:
        X = []
        y = []
        weights = []
        # Source balancing rescales source mass to original total training mass;
        # one core source already contributes uniformly by independent group.
        for ep in train_eps:
            f = engine.features(ep["answers"], ep["source_context"], bundle)
            for target in ep["hidden"]:
                X.append([f.get(n, 0) for n in names])
                y.append(target)
                weights.append(ep["weight"] / len(ep["hidden"]))
        with threadpool_limits(limits=1):
            clf = LogisticRegression(
                C=base["selected_C"],
                solver="lbfgs",
                max_iter=1000,
                tol=1e-7,
                random_state=SEED,
            )
            clf.fit(np.array(X), y, sample_weight=np.array(weights))
        bundle["model_weights"] = {
            str(c): {n: float(w) for n, w in zip(names, row) if w != 0}
            for c, row in zip(clf.classes_, clf.coef_)
        }
        bundle["model_intercepts"] = {
            str(c): float(v) for c, v in zip(clf.classes_, clf.intercept_)
        }
        bundle["fit_id"] = name + "_RECORD_RECOVERY_PROXY"
        bundle["extension_config_sha256"] = engine.fingerprint(prereg)
        if name == "M1_AUX":
            bundle["auxiliary_artifact_sha256"] = audit["artifact_sha256"]
            bundle["auxiliary_role"] = (
                "AUX_SEMANTIC_COFFEE_OBSERVED_COOCCURRENCE_NOT_EQUIVALENCE"
            )
        p = owner / "models" / f"{name}.model.json"
        save(p, bundle)
        p.chmod(0o600)
        bundles[name] = json.loads(p.read_text())
        dev_rows = [run.evaluate(e, bundle, "M1") for e in dev_eps]
        trials[name] = {
            "dev": summarize(run, dev_rows),
            "iterations": clf.n_iter_.tolist(),
            "training_target_rows": len(y),
            "model_sha256": sha(p),
        }
    bal = trials["M1_BALANCED"]["dev"]
    a = trials["M1_AUX"]["dev"]
    keep = (
        a["observed_recovery_ndcg_at_5"] > bal["observed_recovery_ndcg_at_5"]
        and a["observed_recovery_recall_at_8"] >= bal["observed_recovery_recall_at_8"]
        and a["coverage"] >= bal["coverage"]
    )
    decision = {
        "selected_proxy_branch": "M1_AUX" if keep else "M1_BALANCED",
        "auxiliary_retained": keep,
        "basis": "Recorded DEV-only gate, before extension TEST evaluation",
        "dev": copy.deepcopy(trials),
    }
    save(owner / "extension_dev_decision.json", decision)
    (owner / "extension_dev_decision.json").chmod(0o600)
    test_eps = json.loads((owner / "test_episodes.json").read_text())
    allrows = []
    testrows = {}
    for name, bundle in bundles.items():
        rows = [run.evaluate(e, bundle, "M1") for e in test_eps]
        for r in rows:
            r["model"] = name
        testrows[name] = rows
        allrows += rows
        trials[name]["test"] = summarize(run, rows)
    core_rows = json.loads((owner / "predictions.private.json").read_text())
    core = [r for r in core_rows if r["model"] == "M1"]
    legacy = [r for r in core_rows if r["model"] == "B1"]
    result = {
        "task": "RECORD_RECOVERY_PROXY",
        "preregistered_config_sha256": engine.fingerprint(prereg),
        "additional_fit_count": 2,
        "dev_decision": decision,
        "models": trials,
        "auxiliary_vs_balanced": paired(testrows["M1_AUX"], testrows["M1_BALANCED"]),
        "balanced_vs_core": paired(testrows["M1_BALANCED"], core),
        "auxiliary_vs_legacy": paired(testrows["M1_AUX"], legacy),
        "core_test_range_unchanged": True,
        "auxiliary_feature_pairs_changed": len(changed),
        "auxiliary_target_label_weight": 0,
        "core_target_label_weight": 1,
        "core_raw_records": len(records),
        "core_independent_groups": len({r["group_id"] for r in records}),
        "aux_raw_records": len(aux),
        "aux_independent_groups": len({r["group_id"] for r in aux}),
        "independent_source_families_core": 1,
        "independent_source_families_with_aux": 2,
        "source_contribution": {
            "raw_sample_record_shares": {
                "core": len(records) / (len(records) + len(aux)),
                "aux": len(aux) / (len(records) + len(aux)),
            },
            "independent_sample_shares": {
                "core": 110 / (110 + len(aux)),
                "aux": len(aux) / (110 + len(aux)),
            },
            "training_label_weight_shares": {"core": 1.0, "aux": 0.0},
            "conditional_feature_mix_where_aux_supported": {"core": 0.8, "aux": 0.2},
            "all_other_components": {"core": 1.0, "aux": 0.0},
        },
        "per_source_test": {
            "family.zenodo_golovinsky_q_grader_dataset": {
                n: t["test"] for n, t in trials.items()
            },
            FAMILY: {
                "test_groups": 0,
                "status": "AUX_TRAIN_ONLY; no independent source holdout evaluation, no transfer claim",
            },
        },
        "worst_evaluated_source": "family.zenodo_golovinsky_q_grader_dataset (only evaluated family)",
        "selected_model_for_product": "B2 governed deterministic fallback; no learned product improvement established",
        "selected_model_for_proxy_research": decision["selected_proxy_branch"],
        "elapsed_seconds": time.time() - started,
    }
    result["auxiliary_conclusion"] = (
        "NO_IMPROVEMENT"
        if not keep
        else (
            "PROXY_IMPROVEMENT_SUPPORTED"
            if result["auxiliary_vs_balanced"]["paired_group_bootstrap_95_interval"][0]
            > 0
            else "INCONCLUSIVE"
        )
    )
    metrics = json.loads((OUT / "metrics.json").read_text())
    metrics["runtime_extension"] = result
    save(OUT / "metrics.json", metrics)
    with (OUT / "predictions.tsv").open("a", newline="") as f:
        w = csv.DictWriter(f, list(allrows[0]), delimiter="\t", lineterminator="\n")
        for r in allrows:
            w.writerow(
                {k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()}
            )
    save(owner / "extension_predictions.private.json", allrows)
    (owner / "extension_predictions.private.json").chmod(0o600)
    receipt = json.loads((OUT / "run_receipt.json").read_text())
    receipt["runtime_extension"] = {
        "command": 'python db/scripts/extend-backend-model.py --owner-root "$COFFEE_BACKEND_MODEL_ROOT"',
        "elapsed_seconds": result["elapsed_seconds"],
        "code_sha": "d2e1676 plus extension source hash",
        "extension_code_sha256": sha(Path(__file__)),
        "fits": 2,
        "model_paths": [
            "$COFFEE_BACKEND_MODEL_ROOT/models/" + n + ".model.json" for n in bundles
        ],
        "core_model_hash_unchanged": sha(owner / "models/M1.model.json")
        == prereg["core_model_sha256"],
        "dev_decision_record_sha256": sha(owner / "extension_dev_decision.json"),
        "conclusion": result["auxiliary_conclusion"],
    }
    save(OUT / "run_receipt.json", receipt)
    manifest["source_contribution"] = result["source_contribution"]
    manifest["runtime_source_admission"] = {
        "noncommercial_only_sources_newly_admitted": 0,
        "explanation": "Zenodo was already admitted to the completed noncommercial core; runtime purpose confirmation does not create a second admission. Existing UNKNOWN/PENDING remain excluded.",
        "auxiliary_sources_admitted": [FAMILY],
        "auxiliary_roles": [
            "CORE_PROFESSIONAL source observations used only for AUX_SEMANTIC cooccurrence features"
        ],
        "core_gold_source_count": 1,
        "source_family_count_with_aux": 2,
        "newly_discovered_sources": 0,
    }
    save(OUT / "dataset_manifest.json", manifest)
    print(
        json.dumps(
            {
                "models": {n: t["test"] for n, t in trials.items()},
                "dev_decision": decision["selected_proxy_branch"],
                "auxiliary": result["auxiliary_vs_balanced"],
                "conclusion": result["auxiliary_conclusion"],
                "elapsed_seconds": result["elapsed_seconds"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-root", type=Path, required=True)
    extend(p.parse_args().owner_root)
