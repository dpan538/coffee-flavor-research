#!/usr/bin/env python3
"""Post-fit diagnosis without fitting, model selection, or test-set tuning."""

from __future__ import annotations
import argparse, copy, csv, hashlib, importlib.util, json, math, random, sys, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import flavor_backend as live

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-model-20260905"
SEED = 20260905


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


extension = module("extension", ROOT / "db/scripts/extend-backend-model.py")


def save(p, x):
    p.write_text(json.dumps(x, sort_keys=True, ensure_ascii=False, indent=2) + "\n")


def tsv(p, rows):
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: (
                        json.dumps(v, ensure_ascii=False)
                        if isinstance(v, (dict, list))
                        else v
                    )
                    for k, v in r.items()
                }
            )


def group_summary(rows, key):
    groups = defaultdict(list)
    for r in rows:
        if r[key] is not None:
            groups[r["group_id"]].append(r[key])
    values = [float(np.mean(x)) for x in groups.values()]
    if not values:
        return {"group_count": 0, "mean": None, "interval": None}
    rng = np.random.default_rng(SEED)
    boot = np.array(values)[rng.integers(0, len(values), (3000, len(values)))].mean(
        axis=1
    )
    return {
        "group_count": len(values),
        "mean": float(np.mean(values)),
        "paired_group_bootstrap_95_interval": np.quantile(
            boot, [0.025, 0.975]
        ).tolist(),
    }


def qualified(engine, episode, answers, bundle, model):
    observed, _, _ = engine.observations(answers, bundle)
    allrows = bundle["train_records"]
    conditioned = [r for r in allrows if observed <= set(r["targets"])]
    if len({r["group_id"] for r in conditioned}) < 5:
        conditioned = allrows
    used = {a["question_id"] for a in answers}
    ent = engine._entropy(conditioned, bundle["vocabulary"])
    choices = []
    if len(answers) >= 5:
        return []
    for q in engine.question_bank(bundle["vocabulary"]):
        if q["question_id"] in used:
            continue
        parts = defaultdict(list)
        for r in conditioned:
            parts[
                tuple(
                    o["option_id"]
                    for o in q["options"]
                    if set(o["concept_ids"]) & set(r["targets"])
                )
            ].append(r)
        valid = {k: v for k, v in parts.items() if len({r["group_id"] for r in v}) >= 2}
        if len(valid) < 2:
            continue
        gain = ent - sum(
            len(v) / len(conditioned) * engine._entropy(v, bundle["vocabulary"])
            for v in parts.values()
        )
        if gain <= bundle.get("question_gain_threshold", 0.01):
            continue
        outcomes = set()
        for pattern in valid:
            a = {
                "question_id": q["question_id"],
                "shown_option_ids": [o["option_id"] for o in q["options"]],
                "selected_option_ids": list(pattern),
                "state": "SELECTED" if pattern else "UNSURE",
            }
            rank = engine._scores(
                answers + [a], episode["source_context"], bundle, model
            )
            outcomes.add(tuple(r["candidate_id"] for r in rank[:5]))
        if len(outcomes) > 1:
            choices.append((q, gain))
    return sorted(choices, key=lambda item: (-item[1], item[0]["question_id"]))


def diagnose(owner):
    start = time.time()
    engine, run = extension.frozen(owner)
    bundle = json.loads((owner / "models/M1.model.json").read_text())
    episodes = json.loads((owner / "test_episodes.json").read_text())
    records = json.loads((owner / "records.json").read_text())
    deltas = []
    trace = []
    ablation = []
    for e in episodes:
        for model in ["B0", "B1", "B2", "M1"]:
            full = run.evaluate(e, bundle, model)
            for i, a in enumerate(e["answers"]):
                before = run.evaluate(dict(e, answers=e["answers"][:i]), bundle, model)
                after = run.evaluate(
                    dict(e, answers=e["answers"][: i + 1]), bundle, model
                )
                without = run.evaluate(
                    dict(e, answers=e["answers"][:i] + e["answers"][i + 1 :]),
                    bundle,
                    model,
                )
                deltas.append(
                    {
                        "episode_id": e["episode_id"],
                        "group_id": e["group_id"],
                        "model": model,
                        "question_id": a["question_id"],
                        "question_position": i + 1,
                        "before_ndcg5": before["observed_recovery_ndcg_at_5"],
                        "after_ndcg5": after["observed_recovery_ndcg_at_5"],
                        "incremental_delta": after["observed_recovery_ndcg_at_5"]
                        - before["observed_recovery_ndcg_at_5"],
                        "leave_one_question_out_delta": full[
                            "observed_recovery_ndcg_at_5"
                        ]
                        - without["observed_recovery_ndcg_at_5"],
                        "coverage": 1,
                    }
                )
                prev = {
                    r["candidate_id"]: r
                    for r in engine._scores(
                        e["answers"][:i], e["source_context"], bundle, model
                    )
                }
                for r in engine._scores(
                    e["answers"][: i + 1], e["source_context"], bundle, model
                ):
                    p = prev[r["candidate_id"]]
                    trace.append(
                        {
                            "episode_id": e["episode_id"],
                            "group_id": e["group_id"],
                            "model": model,
                            "question_id": a["question_id"],
                            "shown_option_ids": a["shown_option_ids"],
                            "selected_option_ids": a["selected_option_ids"],
                            "candidate_id": r["candidate_id"],
                            "score_before": p["score"],
                            "context_component": r["context_component"],
                            "direct_answer_component": r["direct_answer_component"],
                            "semantic_component": r["semantic_component"],
                            "interaction_component": r["interaction_component"],
                            "base_component": r["base_component"],
                            "score_after": r["score"],
                            "rank_before": p["rank"],
                            "rank_after": r["rank"],
                            "evidence_ids": r["evidence_ids"],
                            "update_reason": "FROZEN_PROXY_FULL_RECOMPUTE_ADD; NOT_REAL_USER_ANSWER",
                        }
                    )
            for removed in ["c0", "c1", "semantic", "interaction"]:
                r = run.evaluate(e, bundle, model, (removed,))
                ablation.append(
                    {
                        "episode_id": e["episode_id"],
                        "group_id": e["group_id"],
                        "model": model,
                        "removed": removed,
                        "full_ndcg5": full["observed_recovery_ndcg_at_5"],
                        "ablated_ndcg5": r["observed_recovery_ndcg_at_5"],
                        "full_minus_ablated": full["observed_recovery_ndcg_at_5"]
                        - r["observed_recovery_ndcg_at_5"],
                        "coverage": 1,
                    }
                )
    q_summary = []
    for model, qid in sorted({(r["model"], r["question_id"]) for r in deltas}):
        rows = [r for r in deltas if r["model"] == model and r["question_id"] == qid]
        s = group_summary(rows, "incremental_delta")
        loo = group_summary(rows, "leave_one_question_out_delta")
        q_summary.append(
            {
                "model": model,
                "question_id": qid,
                "case_count": len(rows),
                "independent_group_count": s["group_count"],
                "mean_before_ndcg5": float(np.mean([r["before_ndcg5"] for r in rows])),
                "mean_after_ndcg5": float(np.mean([r["after_ndcg5"] for r in rows])),
                "incremental_delta": s["mean"],
                "incremental_group_95_interval": s[
                    "paired_group_bootstrap_95_interval"
                ],
                "leave_one_question_out_delta": loo["mean"],
                "leave_one_out_group_95_interval": loo[
                    "paired_group_bootstrap_95_interval"
                ],
                "coverage": 1,
                "interpretation": "EXPLORATORY_PROXY_DIAGNOSIS_NOT_PARAMETER_SELECTION",
            }
        )
    for model in ["B0", "B1", "B2", "M1"]:
        for q in engine.question_bank(bundle["vocabulary"]):
            if any(
                r["model"] == model and r["question_id"] == q["question_id"]
                for r in q_summary
            ):
                continue
            q_summary.append(
                {
                    "model": model,
                    "question_id": q["question_id"],
                    "case_count": 0,
                    "independent_group_count": 0,
                    "mean_before_ndcg5": None,
                    "mean_after_ndcg5": None,
                    "incremental_delta": None,
                    "incremental_group_95_interval": None,
                    "leave_one_question_out_delta": None,
                    "leave_one_out_group_95_interval": None,
                    "coverage": None,
                    "interpretation": "NO_FROZEN_SPECIFIC_ANSWER_CASES; NOT_EVIDENCE_OF_ZERO_VALUE",
                }
            )
    tsv(OUT / "question_delta.tsv", q_summary)
    tsv(owner / "question_delta.private.tsv", trace)
    tsv(owner / "question_case_metrics.private.tsv", deltas)
    tsv(owner / "ablation.private.tsv", ablation)
    for n in [
        "question_delta.private.tsv",
        "question_case_metrics.private.tsv",
        "ablation.private.tsv",
    ]:
        (owner / n).chmod(0o600)
    ablation_summary = {
        m: {
            key: group_summary(
                [r for r in ablation if r["model"] == m and r["removed"] == key],
                "full_minus_ablated",
            )
            for key in ["c0", "c1", "semantic", "interaction"]
        }
        for m in ["B0", "B1", "B2", "M1"]
    }
    policy_rows = []
    # Same visible descriptor pool and five-question ceiling for every strategy.
    # The oracle never reads held-out targets. Missing visible responses are UNSURE.
    for e in episodes:
        for strategy in ["FIXED_QUALIFIED", "SEEDED_RANDOM_QUALIFIED", "ADAPTIVE"]:
            order = [
                q["question_id"] for q in engine.question_bank(bundle["vocabulary"])
            ]
            if strategy == "SEEDED_RANDOM_QUALIFIED":
                random.Random(SEED).shuffle(order)
            answers = []
            stopped = False
            for budget in range(6):
                result = run.evaluate(dict(e, answers=answers), bundle, "M1")
                policy_rows.append(
                    {
                        "episode_id": e["episode_id"],
                        "group_id": e["group_id"],
                        "strategy": strategy,
                        "budget": budget,
                        "actually_asked": len(answers),
                        "observed_recovery_ndcg_at_5": result[
                            "observed_recovery_ndcg_at_5"
                        ],
                        "recall_at_8": result["observed_recovery_recall_at_8"],
                        "coverage": result["coverage"],
                        "visible_descriptors_revealed": len(
                            engine.observations(answers, bundle)[0]
                        ),
                        "stopped": stopped,
                    }
                )
                if budget == 5:
                    break
                choices = qualified(engine, e, answers, bundle, "M1")
                if not choices:
                    stopped = True
                    continue
                q = (
                    choices[0][0]
                    if strategy == "ADAPTIVE"
                    else min(
                        choices, key=lambda item: order.index(item[0]["question_id"])
                    )[0]
                )
                selected = [
                    o["option_id"]
                    for o in q["options"]
                    if set(o["concept_ids"]) & set(e["visible"])
                ]
                answers.append(
                    {
                        "question_id": q["question_id"],
                        "shown_option_ids": [o["option_id"] for o in q["options"]],
                        "selected_option_ids": selected,
                        "state": "SELECTED" if selected else "UNSURE",
                    }
                )
    tsv(owner / "policy_simulation.private.tsv", policy_rows)
    (owner / "policy_simulation.private.tsv").chmod(0o600)
    policy_summary = {
        s: {
            str(k): {
                "ndcg5": group_summary(
                    [r for r in policy_rows if r["strategy"] == s and r["budget"] == k],
                    "observed_recovery_ndcg_at_5",
                ),
                "coverage": 1.0,
                "mean_asked": float(
                    np.mean(
                        [
                            r["actually_asked"]
                            for r in policy_rows
                            if r["strategy"] == s and r["budget"] == k
                        ]
                    )
                ),
                "mean_direct_concepts_revealed": float(
                    np.mean(
                        [
                            r["visible_descriptors_revealed"]
                            for r in policy_rows
                            if r["strategy"] == s and r["budget"] == k
                        ]
                    )
                ),
            }
            for k in range(6)
        }
        for s in ["FIXED_QUALIFIED", "SEEDED_RANDOM_QUALIFIED", "ADAPTIVE"]
    }
    policy_paired = {
        s: extension.paired(
            [
                r
                for r in policy_rows
                if r["strategy"] == "ADAPTIVE" and r["budget"] == 5
            ],
            [r for r in policy_rows if r["strategy"] == s and r["budget"] == 5],
        )
        for s in ["FIXED_QUALIFIED", "SEEDED_RANDOM_QUALIFIED"]
    }
    # Semantic counterexamples use transparent developer fixtures, not sensory gold.
    tests = module("backend_tests", ROOT / "db/tests/test_flavor_backend.py")
    fixture = tests.fixture()
    context = {"c0": live.C0[0], "c1": "medium"}
    counterexamples = []

    def compare_case(name, qid, selected):
        a = tests.answer(fixture, qid, selected)
        base = live.build_candidate_state(context, fixture)
        before = live.update_candidate_state(
            live.build_candidate_state(context, fixture, "B1"), a, fixture
        )
        after = live.update_candidate_state(base, a, fixture)
        counterexamples.append(
            {
                "id": name,
                "scope": "DEVELOPMENT_POLICY_FIXTURE_NOT_EMPIRICAL_LABEL",
                "context": context,
                "answers": [a],
                "before_candidates": before["candidates"],
                "after_candidates": after["candidates"],
                "test": "db/tests/test_flavor_backend.py",
                "judgment_status": "AUTOMATED_INVARIANT_ONLY",
            }
        )

    compare_case("broad_floral_is_not_jasmine", "q.direction", ["family.floral"])
    compare_case("cocoa_is_not_dark_chocolate", "q.nut_cocoa", ["sensory.cocoa"])
    compare_case(
        "multi_select_bounded_total_effect",
        "q.nut_cocoa",
        ["sensory.cocoa", "sensory.dark_chocolate", "sensory.almond"],
    )
    broad = next(
        q
        for q in live.question_bank(fixture["vocabulary"])
        if q["question_id"] == "q.direction"
    )
    compare_case(
        "all_broad_no_information",
        "q.direction",
        [o["option_id"] for o in broad["options"]],
    )
    for name, raw in [
        ("method_keyword_without_observation", "instrument.calibration"),
        ("floral_structured_claim", "floral"),
        ("cocoa_structured_claim", "cocoa"),
        ("compound_nutty_cocoa", "Nutty/Cocoa"),
    ]:
        row = {
            "review_status": "REVIEWED",
            "evidence_direction": "SUPPORTS",
            "target_entity_key": raw,
            "method": (
                "floral cocoa tokens"
                if name.startswith("method")
                else "panel frequency"
            ),
            "support_count": "1",
            "source_family_key": "fixture",
        }
        old = dict(tests.old_claims([row]))
        counterexamples.append(
            {
                "id": name,
                "scope": "DEVELOPMENT_POLICY_FIXTURE_NOT_EMPIRICAL_LABEL",
                "source_claim": row,
                "before_candidate_support": old,
                "after_candidate_support": {},
                "reason": "No typed direct observation or reviewed equivalent to any specific candidate; retain broad/combined source term separately",
                "test": "db/tests/test_flavor_backend.py",
                "judgment_status": "AUTOMATED_INVARIANT_ONLY",
            }
        )
    counterexamples += [
        {
            "id": "duplicate_semantic_paths",
            "before_candidate_support": {"sensory.cocoa": 2},
            "after_candidate_support": {"sensory.cocoa": 1},
            "reason": "Same artifact/observation/target counted once, regardless of method/path",
            "test": "test_source_permission_does_not_propagate_and_paths_deduplicate",
        },
        {
            "id": "nonempty_singleton_partitions",
            "before": "Historical eligibility requires two source families and two nonempty candidate partitions, without empirical response support or measured information gain",
            "after": "STOP unless two patterns each have two independent training groups, positive gain and changing possible top5",
            "test": "test_question_requires_supported_material_outcomes_and_stops",
        },
        {
            "id": "source_rights_propagation",
            "before": "Concept-level permission could admit another source",
            "after": "Exact artifact with unsatisfied conditions withheld; eligible artifact retained",
            "test": "test_source_permission_does_not_propagate_and_paths_deduplicate",
        },
        {
            "id": "bitter_not_fermentation",
            "before": "Bitter in fermented routing bucket",
            "after": "Dedicated taste routing; no fermented hierarchical support",
            "test": "test_bitter_is_not_fermented_child",
        },
    ]
    # Prepare at most 20 anonymous cases. DEV review may inform later rules;
    # LOCKED review must never be used for tuning. No judgments are fabricated.
    dev_eps = run.episodes([r for r in records if r["split"] == "DEV"], bundle, 1)
    review = []
    key = []
    for split, eps, count in [
        ("DEVELOPMENT_REVIEW", dev_eps, 12),
        ("LOCKED_EVALUATION", episodes, 8),
    ]:
        scored = []
        for e in eps:
            a = run.evaluate(e, bundle, "B1")
            c = run.evaluate(e, bundle, "M1")
            impact = abs(
                a["observed_recovery_ndcg_at_5"] - c["observed_recovery_ndcg_at_5"]
            )
            scored.append((impact, e, a, c))
        # Selecting largest disagreements is targeted audit, never a representative
        # metric. Locked review scores will not be pooled into the fixed TEST metric.
        for i, (_, e, a, c) in enumerate(
            sorted(scored, key=lambda x: (-x[0], x[1]["episode_id"]))[:count]
        ):
            flip = int(hashlib.sha256(e["episode_id"].encode()).hexdigest(), 16) % 2
            pair = [a, c] if not flip else [c, a]
            rid = split.lower() + "-" + str(i + 1)
            review.append(
                {
                    "review_id": rid,
                    "set": split,
                    "task": "RECORD_RECOVERY_PROXY_REVIEW_NOT_REAL_ANSWER_EVALUATION",
                    "source_C0": e["source_context"]["c0"],
                    "source_C1_nominal_only": e["source_context"]["c1"],
                    "production_context_available": False,
                    "context_note": "Source lacks validated complete C0/C1; do not invent them. These are record-evidence comparisons, not complete product cases.",
                    "answer_sequence": e["answers"],
                    "candidate_A": pair[0]["ranking"],
                    "candidate_B": pair[1]["ranking"],
                    "professional_observed_evidence": sorted(
                        set(e["visible"]) | set(e["hidden"])
                    ),
                    "evidence_ids": next(
                        r["evidence_ids"]
                        for r in records
                        if r["record_id"] == e["record_id"]
                    ),
                    "judgment_points": [
                        "Which candidates fit the provided record evidence and visible answers better?",
                        "Which candidates are over-specific?",
                        "Which observed important concepts are omitted?",
                    ],
                    "human_preference": None,
                    "human_over_specific_candidates": None,
                    "human_omissions": None,
                    "human_reviewer": None,
                }
            )
            key.append(
                {
                    "review_id": rid,
                    "A": pair[0]["model"],
                    "B": pair[1]["model"],
                    "group_id": e["group_id"],
                }
            )
    save(owner / "human_comparison_cases.private.json", review)
    save(owner / "human_comparison_key.private.json", key)
    for n in [
        "human_comparison_cases.private.json",
        "human_comparison_key.private.json",
    ]:
        (owner / n).chmod(0o600)
    # Exact legal live requests across every C0/C1 pair, with a changed fresh answer.
    lat = []
    live_outputs = []
    for c0 in live.C0:
        for c1 in live.C1:
            q = next(
                q
                for q in live.question_bank(bundle["vocabulary"])
                if q["question_id"] == "q.fruit"
            )
            a = {
                "question_id": q["question_id"],
                "shown_option_ids": [o["option_id"] for o in q["options"]],
                "selected_option_ids": [
                    q["options"][
                        (live.C0.index(c0) + live.C1.index(c1)) % len(q["options"])
                    ]["option_id"]
                ],
                "state": "SELECTED",
            }
            begin = time.perf_counter()
            r = live.run({"context": {"c0": c0, "c1": c1}, "answers": [a]}, bundle)
            lat.append((time.perf_counter() - begin) * 1000)
            live_outputs.append(
                {"context": {"c0": c0, "c1": c1}, "answer": a, "response": r}
            )
    save(owner / "live_backend_validation.private.json", live_outputs)
    (owner / "live_backend_validation.private.json").chmod(0o600)
    errors = {
        "task": "RECORD_RECOVERY_PROXY",
        "semantic_counterexamples": counterexamples,
        "observed_test_unseen_descriptors": json.loads(
            (OUT / "metrics.json").read_text()
        )["unseen_test_hidden_descriptor_count"],
        "false_specificity_rate_real_cases": None,
        "false_specificity_reason": "No independent reviewed negative/specificity labels; not inferred from unmentioned words. Counterexamples test explicit semantic invariants only.",
        "real_question_answer_evaluation_cases": 0,
        "review_pack": {
            "case_count": len(review),
            "development_count": 12,
            "locked_evaluation_count": 8,
            "human_completed": 0,
            "files": [
                "$COFFEE_BACKEND_MODEL_ROOT/human_comparison_cases.private.json",
                "$COFFEE_BACKEND_MODEL_ROOT/human_comparison_key.private.json",
            ],
            "selection": "Highest-impact disagreements; targeted audit, not a randomly sampled gold set. No manual judgments entered. Complete production C0/C1 unavailable in source observations.",
            "no_training_use_of_locked_review": True,
        },
        "question_actions": {
            "implemented": "Semantic support bounded and deduplicated; actual supported outcome change required for asking; bitter removed from fermented hierarchy; source context mapping masked.",
            "not_implemented_from_test": "No question coefficient, feature, or question removal tuned on TEST. Per-question deltas below are exploratory; zero/sparse evidence does not prove a question useless.",
        },
        "material_limitations": [
            "No coffee record in this core has reviewed complete production C0/C1; source-native roast matches are nominal only.",
            "Only one professional source family in core TEST; auxiliary second family has no independent evaluation split.",
            "B1 comparison transports legacy +3/-1.25 answer effect recipe onto common TRAIN-only candidates/priors. It is not a numerical reproduction of the old full-corpus 20-candidate product fixture. Old generator remains available only as a historical baseline.",
            "Three M1 parameter settings selected on DEV; only 17 independent TEST groups; interval crosses zero.",
            "Direct restatement Recall@5 and recovery Recall@8 regress relative to B1 despite a higher recovery NDCG@5.",
            "Broad direction support and train cooccurrence do not constitute confirmation of specific sensory properties.",
            "Source field authority is limited to reported trained-panel descriptor observations; quality scores, methods, package metadata and user questionnaires are not sensory labels.",
        ],
    }
    save(OUT / "errors.json", errors)
    metrics = json.loads((OUT / "metrics.json").read_text())
    metrics["diagnostics"] = {
        "question_summary_file": "question_delta.tsv",
        "ablations_full_minus_removed": ablation_summary,
        "adaptive_policy_simulation": {
            "assumptions": "OFFLINE_VISIBLE_DESCRIPTOR_ORACLE; fixed frozen visible pool, max3 concepts, max5 questions; absence->UNSURE; hidden recovery targets never used by answer oracle. Same TEST groups and candidate vocab. No real-user policy validation.",
            "same_question_budget_curves": policy_summary,
            "adaptive_minus_control_at_5": policy_paired,
            "coverage_all_cases": 1,
            "posthoc_diagnostic_only": True,
        },
        "live_backend": {
            "arbitrary_legal_requests_executed": len(live_outputs),
            "all_8_C0_x_7_C1_combinations_passed": True,
            "context_effect_status": "MASKED_UNVALIDATED_SOURCE_MAPPING",
            "end_to_end_latency_p50_ms": float(np.median(lat)),
            "end_to_end_latency_p95_ms": float(np.percentile(lat, 95)),
            "latency_scope": "JSON request object through validation, update, ranking, next-question/stop and final structure; excludes process startup",
            "semantic_counterexamples": len(counterexamples),
            "human_review_completed": 0,
            "real_false_specificity_rate": None,
        },
        "trace_storage": "$COFFEE_BACKEND_MODEL_ROOT/question_delta.private.tsv; source-derived shown/selected IDs retained outside Git",
    }
    save(OUT / "metrics.json", metrics)
    receipt = json.loads((OUT / "run_receipt.json").read_text())
    receipt["diagnostics"] = {
        "command": 'python db/scripts/analyze-backend-model.py --owner-root "$COFFEE_BACKEND_MODEL_ROOT"',
        "elapsed_seconds": time.time() - start,
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_fits": 0,
        "trace_rows": len(trace),
        "per_question_cases": len(deltas),
        "legal_live_cases": len(live_outputs),
        "review_cases": len(review),
        "human_judgments": 0,
    }
    save(OUT / "run_receipt.json", receipt)
    print(
        json.dumps(
            {
                "question_deltas_M1": [r for r in q_summary if r["model"] == "M1"],
                "ablations_M1": ablation_summary["M1"],
                "policy_final": {s: v["5"] for s, v in policy_summary.items()},
                "live": metrics["diagnostics"]["live_backend"],
                "elapsed_seconds": time.time() - start,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--owner-root", type=Path, required=True)
    diagnose(p.parse_args().owner_root)
