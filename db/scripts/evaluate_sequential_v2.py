#!/usr/bin/env python3
"""Predeclared held-group stage, policy, hierarchy and feedback diagnostics."""

from __future__ import annotations
import argparse, copy, csv, json, math, time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import flavor_backend as legacy
import flavor_sequential as s
import flavor_planning as p
import train_sequential as t
from run_sequential_v2 import paired, summary, mean, group_mean
from prepare_sequential_data import save


def write_tsv(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w") as f:
        w = csv.DictWriter(f, keys, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def result_row(record, state, bundle, episode, model):
    rank = [r["candidate_id"] for r in state["candidate_scores"]]
    exclude = set(episode["visible"]) | {
        "attribute." + a for c in episode["visible"] for a in s.PARENTS.get(c, [])
    }
    recovery = [c for c in rank if c not in exclude]
    hidden = set(episode["hidden"])
    explicit = set(state["interpreted_evidence"]["specific"])
    shown = rank[:8]
    return {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
        "model": model,
        "ndcg5": t.ndcg(recovery, episode["relevance"]) if hidden else None,
        "recall5": len(set(recovery[:5]) & hidden) / len(hidden) if hidden else None,
        "recall8": len(set(recovery[:8]) & hidden) / len(hidden) if hidden else None,
        "coverage": bool(shown),
        "candidate_target_coverage": (
            len(hidden & set(bundle["candidate_vocabulary"])) / len(hidden)
            if hidden
            else None
        ),
        "direct_retention8": (
            len(set(shown) & explicit) / len(explicit) if explicit else None
        ),
        "duplicate_rate": 1 - len(set(shown)) / max(len(shown), 1),
        "ranking": rank,
        "recovery_ranking": recovery,
    }


def legacy_payload(state, bundle):
    """Transport the same actual answer information; do not generate from targets."""
    mapping = {
        "fruity": "fruit",
        "floral": "floral",
        "sweet": "sweet",
        "nutty_cocoa": "nut_cocoa",
        "spices": "spice_roasted",
        "roasted": "spice_roasted",
        "green_vegetative": "tea_green",
        "sour_fermented": "fermented",
        "taste": "taste",
    }
    grouped = defaultdict(lambda: {"shown": set(), "selected": set()})
    valid = {
        q["question_id"]: {o["option_id"] for o in q["options"]}
        for q in legacy.question_bank(bundle["vocabulary"])
    }
    for a in state["answers_by_question"].values():
        for o in a["options"]:
            if o["kind"] == "broad":
                qid = "q.direction"
                oid = "family." + mapping[o["attribute"]]
            else:
                if o["id"] not in legacy.FAMILY:
                    continue
                qid = "q." + legacy.FAMILY[o["id"]]
                oid = o["id"]
            if oid not in valid.get(qid, set()):
                continue
            grouped[qid]["shown"].add(oid)
            if o["id"] in a["selected_option_ids"]:
                grouped[qid]["selected"].add(oid)
    return {
        "context": state["context"],
        "answers": [
            {
                "question_id": qid,
                "shown_option_ids": sorted(g["shown"]),
                "selected_option_ids": sorted(g["selected"]),
                "state": "SELECTED" if g["selected"] else "UNSURE",
            }
            for qid, g in sorted(grouped.items())
        ],
    }


def baseline_bundle(bundle):
    vocab = [c for c in bundle["candidate_vocabulary"] if c in legacy.FAMILY]
    stats = bundle["statistics"]
    return {
        "vocabulary": vocab,
        "bundle_id": "v2-transported-train-only-baseline",
        "priors": {c: stats["log_prior"][c] for c in vocab},
        "conditional": stats["conditional"],
        "interaction_pairs": [],
        "context_adjustments": {},
        "candidate_rights": dict.fromkeys(
            vocab, "ADMITTED_SOURCE_CONDITIONS_SATISFIED"
        ),
        "evidence_by_candidate": {},
        "train_records": [],
    }


def baselines(record, row, bundle, old=None):
    b = old if old is not None else baseline_bundle(bundle)
    payload = legacy_payload(row["state"], b)
    out = []
    for kind in (["B0", "B1", "B2", "M1"] if old is not None else ["B0", "B1", "B2"]):
        live = legacy.run(dict(payload, model=kind), b)
        state = {
            "candidate_scores": live["candidate_state"]["candidates"],
            "interpreted_evidence": {
                "specific": sorted(legacy.observations(payload["answers"], b)[0])
            },
        }
        fake = {"candidate_vocabulary": b["vocabulary"]}
        r = result_row(record, state, fake, row["episode"], kind)
        r["question_count"] = len(row["payload"]["answers"])
        r["option_budget"] = sum(
            len(a["shown_option_ids"]) for a in row["payload"]["answers"]
        )
        r["latency_ms"] = None
        r["adapter_note"] = (
            "Same offered answer information transported to historical families; merged direction/overlapping axes. Original executable B0/B1/B2 coefficients, context mask and M1 retained weights unchanged. Candidate vocabulary coverage is reported."
        )
        out.append(r)
    return out


def policy_job(job):
    record, bundle, policy = job
    # All policies receive exactly the same TRAIN-qualified four-option pool.
    bundle = copy.deepcopy(bundle)
    bundle["question_bank"]["correction"] = [
        q for q in bundle["question_bank"]["correction"] if len(q["options"]) == 4
    ]
    bundle["bundle_id"] += ":equal20"
    start = time.perf_counter()
    r = t.evaluate_record(record, bundle, policy)
    r["full_chain_latency_ms"] = (time.perf_counter() - start) * 1000
    r["policy"] = policy
    return r


def stage_diagnostics(record, row, bundle):
    episode, states, answers = t.trajectory(record, bundle)
    out = []
    previous = None
    full = result_row(record, states[-1], bundle, episode, "full")
    key = {
        "record_id": record["record_id"],
        "group_id": record["group_id"],
        "source_family": record["source_family"],
    }
    for i, st in enumerate(states):
        r = result_row(record, st, bundle, episode, "prefix")
        slot = "CONTEXT" if i == 0 else answers[i - 1]["slot"]
        delta = (
            (r["ndcg5"] - previous["ndcg5"])
            if previous and r["ndcg5"] is not None
            else None
        )
        out.append(
            {
                **key,
                "kind": "PREFIX",
                "slot": slot,
                "ndcg5": r["ndcg5"],
                "delta": delta,
                "direct_retention8": r["direct_retention8"],
                "question_count": i,
                "option_budget": sum(len(a["shown_option_ids"]) for a in answers[:i]),
            }
        )
        previous = r
    for a in answers:
        st = copy.deepcopy(states[-1])
        del st["answers_by_question"][a["slot"]]
        st = s.recompute(st, bundle)
        r = result_row(record, st, bundle, episode, "leave-one-answer-out")
        out.append(
            {
                **key,
                "kind": "ANSWER_REMOVAL",
                "slot": a["slot"],
                "axis": a["axis"],
                "ndcg5": r["ndcg5"],
                "delta": (
                    full["ndcg5"] - r["ndcg5"] if full["ndcg5"] is not None else None
                ),
            }
        )
    for label, indices in [
        ("NO_SEMANTIC", [3, 4, 5, 7, 10, 12, 13, 15]),
        ("NO_INTERACTION", [10, 11]),
        ("NO_CLUSTER", [12, 13]),
    ]:
        b = copy.deepcopy(bundle)
        for i in indices:
            b["model_parameters"]["weights"][i] = 0.0
        st = s.recompute(states[-1], b)
        r = result_row(record, st, b, episode, label)
        out.append(
            {
                **key,
                "kind": "FEATURE_REMOVAL",
                "slot": label,
                "ndcg5": r["ndcg5"],
                "delta": (
                    full["ndcg5"] - r["ndcg5"] if full["ndcg5"] is not None else None
                ),
            }
        )
    # Context numerical efficacy is not inferred from arbitrary proxy settings.
    for label in ["NO_C0", "NO_C1"]:
        out.append(
            {
                **key,
                "kind": "FEATURE_REMOVAL",
                "slot": label,
                "ndcg5": None,
                "delta": None,
                "status": "NOT_ESTIMABLE_NO_SOURCE_PAIRED_CONTEXT",
            }
        )
    return out


def feedback_diagnostics(record, row, bundle):
    st = row["state"]
    pre = s.finalize_result(st, bundle)
    ex = pre["exposure"]
    episode = row["episode"]
    selected = [c for c in ex["candidate_ids"] if c in episode["visible"]] if ex else []
    eligible = bool(ex and ex["eligible_for_final_comparison"])
    hidden = set(episode["hidden"])
    rows = []
    for mode in ["F0", "F1", "F2"]:
        candidate = (
            st
            if mode == "F0" or not eligible
            else s.apply_final_comparison(
                st,
                ex["candidate_ids"],
                selected,
                bundle,
                feedback_source="SIMULATED",
                generation_version=bundle["bundle_id"],
                mode=mode,
            )
        )
        r = result_row(record, candidate, bundle, episode, mode)
        r.update(
            {
                "comparison_eligible": eligible,
                "selected_count": len(selected),
                "selection_retention8": (
                    len(set(r["ranking"][:8]) & set(selected)) / len(selected)
                    if selected
                    else None
                ),
                "exposure_target_coverage": (
                    len(set(ex["candidate_ids"]) & hidden) / len(hidden)
                    if ex and hidden
                    else None
                ),
                "feedback_source": "SIMULATED_VISIBLE_ONLY_NOT_HIDDEN_TARGET",
                "previous_explicit_retention8": r["direct_retention8"],
            }
        )
        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner-dir", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    owner = a.owner_dir
    start = time.time()
    metrics = json.loads((t.OUT / "metrics.json").read_text())
    config = json.loads((t.OUT / "experiment_config.json").read_text())
    config["sequential"][
        "policy_exact_budget"
    ] = "P1, exactly 5 ordinary questions and 20 shown options; shared TRAIN-qualified axes having exactly four actual options. Full-pool primary ranking result kept separately."
    config["sequential"]["diagnostics_preregistered_before_execution"] = [
        "all development records, no performance filtering",
        "F0/F1/F2 visible-only simulated selection, fixed hidden targets",
        "20 anonymous human review cases:10 development,10 historical regression; none claimed fresh locked confirmation",
        "source-native cluster bootstrap alignment, and missing-context limitation",
    ]
    save(t.OUT / "experiment_config.json", config)
    records = json.loads((owner / "recovery_records.json").read_text())
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    historical = [r for r in records if r["split"] == "HISTORICAL_REGRESSION"]
    lookup = {r["record_id"]: r for r in records}
    folds = json.loads((owner / "cv/splits.private.json").read_text())
    selected = metrics["sequential"]["selected_model"]
    C = metrics["sequential"]["selected_C"]
    label = selected if selected != "M2_ADD" else "M2_ADD_C" + str(C)
    bundles = {
        fold: json.loads((owner / f"cv/{label}_fold{fold}.model.json").read_text())
        for fold in range(3)
    }
    primary = json.loads((owner / f"cv/{label}.private.json").read_text())
    stage = []
    feedback = []
    base = []
    for row in primary:
        r = lookup[row["record_id"]]
        b = bundles[folds[r["group_id"]]]
        stage.extend(stage_diagnostics(r, row, b))
        feedback.extend(feedback_diagnostics(r, row, b))
        base.extend(baselines(r, row, b))
    save(owner / "cv/stage_effects.private.json", stage)
    save(owner / "cv/feedback_effects.private.json", feedback)
    save(owner / "cv/baselines.private.json", base)
    policies = []
    jobs = [
        (r, bundles[folds[r["group_id"]]], policy)
        for r in dev
        for policy in ["fixed", "random", "one_step", "two_step"]
    ]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i, r in enumerate(pool.map(policy_job, jobs, chunksize=1)):
            policies.append(r)
            if (i + 1) % 80 == 0:
                print(
                    "policy episodes",
                    i + 1,
                    "/",
                    len(jobs),
                    "seconds",
                    round(time.time() - start, 1),
                    flush=True,
                )
    save(owner / "cv/policy_predictions.private.json", policies)
    bypolicy = {
        policy: [r for r in policies if r["policy"] == policy]
        for policy in ["fixed", "random", "one_step", "two_step"]
    }
    assert all(r["question_count"] == 5 and r["option_budget"] == 20 for r in policies)
    public_stage = []
    for kind, slot in sorted({(r["kind"], r["slot"]) for r in stage}):
        rows = [r for r in stage if r["kind"] == kind and r["slot"] == slot]
        values = group_mean(rows, "delta")
        zero = [dict(r, delta=0.0) for r in rows if r["delta"] is not None]
        comparison = paired(rows, zero, "delta")
        public_stage.append(
            {
                "kind": kind,
                "slot_or_policy": slot,
                "records": len(rows),
                "groups": len({r["group_id"] for r in rows}),
                "observed_recovery_ndcg5": mean(rows, "ndcg5"),
                "marginal_or_removal_delta": mean(rows, "delta"),
                "interval": json.dumps(comparison.get("paired_group_95_interval")),
                "status": comparison["status"] if values else "NOT_ESTIMABLE",
                "scope": "DEVELOPMENT_RECORD_RECOVERY_PROXY",
            }
        )
    for policy, rows in bypolicy.items():
        public_stage.append(
            {
                "kind": "POLICY",
                "slot_or_policy": policy,
                "records": len(rows),
                "groups": len({r["group_id"] for r in rows}),
                "observed_recovery_ndcg5": mean(rows, "ndcg5"),
                "marginal_or_removal_delta": paired(rows, bypolicy["fixed"])["delta"],
                "interval": json.dumps(
                    paired(rows, bypolicy["fixed"]).get("paired_group_95_interval")
                ),
                "mean_full_chain_ms": mean(rows, "full_chain_latency_ms"),
                "coverage": mean(rows, "coverage"),
                "question_count": 5,
                "option_budget": 20,
                "status": paired(rows, bypolicy["fixed"])["status"],
                "scope": "PROXY_POLICY_SIMULATION",
            }
        )
    write_tsv(t.OUT / "stage_effects.tsv", public_stage)
    fb = {
        mode: [r for r in feedback if r["model"] == mode] for mode in ["F0", "F1", "F2"]
    }
    public_fb = []
    for mode, rows in fb.items():
        public_fb.append(
            {
                "mode": mode,
                "records": len(rows),
                "groups": len({r["group_id"] for r in rows}),
                "observed_recovery_ndcg5": mean(rows, "ndcg5"),
                "selected_retention8": mean(rows, "selection_retention8"),
                "previous_explicit_retention8": mean(
                    rows, "previous_explicit_retention8"
                ),
                "exposure_hidden_target_coverage": mean(
                    rows, "exposure_target_coverage"
                ),
                "eligible_case_coverage": mean(rows, "comparison_eligible"),
                "nonempty_selections": sum(r["selected_count"] > 0 for r in rows),
                "scope": "SIMULATED_VISIBLE_ONLY; real feedback NOT_EVALUATED",
            }
        )
    write_tsv(t.OUT / "feedback_effects.tsv", public_fb)
    metrics["policy"] = {
        "pool": "Identical train-qualified four-option axes; exactly five ordinary questions,20 shown options",
        "scope": "PROXY_POLICY_SIMULATION",
        "models": {
            k: summary(v) | {"full_chain_latency_ms": mean(v, "full_chain_latency_ms")}
            for k, v in bypolicy.items()
        },
        "comparisons": {
            k + "_minus_fixed": paired(v, bypolicy["fixed"])
            for k, v in bypolicy.items()
            if k != "fixed"
        }
        | {
            "two_step_minus_one_step": paired(
                bypolicy["two_step"], bypolicy["one_step"]
            )
        },
    }
    metrics["feedback"] = {
        "scope": "VISIBLE_ONLY_SIMULATION; no actual human responses",
        "models": {
            k: summary(v)
            | {
                "selected_retention8": mean(v, "selection_retention8"),
                "comparison_eligible": mean(v, "comparison_eligible"),
                "exposure_target_coverage": mean(v, "exposure_target_coverage"),
            }
            for k, v in fb.items()
        },
        "F2_minus_F1": paired(fb["F2"], fb["F1"]),
        "F1_minus_F0": paired(fb["F1"], fb["F0"]),
        "real_feedback_effect": "NOT_EVALUATED",
    }
    # Original baseline code used through its live entry, with shared answer adapter.
    bs = {kind: [r for r in base if r["model"] == kind] for kind in ["B0", "B1", "B2"]}
    metrics["legacy_baseline_development"] = {
        "scope": "Same actual evidence, historical family adapter; old models lack broad candidate outputs. Full-target coverage and common-fine-only comparison both required.",
        "models": {k: summary(v) for k, v in bs.items()},
        "selected_minus_B2_full_scope": paired(primary, bs["B2"]),
    }

    def fine(row, common=None):
        ep = row.get("episode")
        relevance = ep["relevance"] if ep else lookup[row["record_id"]]["relevance"]
        hidden = (
            set(ep["hidden"])
            if ep
            else set(t.visible_episode(lookup[row["record_id"]])["hidden"])
        )
        target = {
            c: relevance[c]
            for c in hidden
            if c.startswith("sensory.") and (common is None or c in common)
        }
        ranking = [
            c
            for c in row["recovery_ranking"]
            if c.startswith("sensory.") and (common is None or c in common)
        ]
        return dict(row, ndcg5=t.ndcg(ranking, target) if target else None)

    metrics["legacy_baseline_development"]["selected_minus_B2_fine_only"] = paired(
        [fine(r) for r in primary], [fine(r) for r in bs["B2"]]
    )
    old = json.loads(
        (owner.parent / "backend-model-20260905/models/M1.model.json").read_text()
    )
    hist_predictions = json.loads(
        (owner / "cv/historical_predictions.private.json").read_text()
    )[selected]
    histbase = []
    finalbundle = json.loads((owner / "models" / f"{selected}.model.json").read_text())
    for row in hist_predictions:
        histbase.extend(baselines(lookup[row["record_id"]], row, finalbundle, old))
    save(owner / "cv/historical_baselines.private.json", histbase)
    common = set(old["vocabulary"])
    metrics["historical_same_information_comparison"] = {
        "scope": "17 previously inspected groups; REGRESSION_ONLY, not new confirmation. Fine vocabulary intersection also reported; context masked consistently in old live code and new descriptor code.",
        "models": {
            kind: summary([r for r in histbase if r["model"] == kind])
            for kind in ["B0", "B1", "B2", "M1"]
        },
        "selected_minus": {
            kind: paired(
                [fine(r, common) for r in hist_predictions],
                [fine(r, common) for r in histbase if r["model"] == kind],
            )
            for kind in ["B0", "B1", "B2", "M1"]
        },
    }
    save(t.OUT / "metrics.json", metrics)
    receipt = json.loads((t.OUT / "run_receipt.json").read_text())
    receipt["diagnostics"] = {
        "command": 'python db/scripts/evaluate_sequential_v2.py --owner-dir "'
        + str(owner)
        + '" --workers '
        + str(a.workers),
        "seconds": time.time() - start,
        "policy_cases": len(policies),
        "feedback_cases": len(feedback),
        "truth_feedback_count": 0,
        "old_M1_not_refit": True,
    }
    save(t.OUT / "run_receipt.json", receipt)
    print(
        json.dumps(
            {
                "policy": metrics["policy"]["comparisons"],
                "feedback": metrics["feedback"]["F2_minus_F1"],
                "old": metrics["historical_same_information_comparison"][
                    "selected_minus"
                ],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
