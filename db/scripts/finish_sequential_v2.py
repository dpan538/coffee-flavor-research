#!/usr/bin/env python3
"""Retain model delivery, provenance, uncertainty and a small unfilled review pack."""

from __future__ import annotations
import argparse, copy, csv, hashlib, json, os, platform, subprocess, time
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
import flavor_sequential as s
import train_sequential as t
from prepare_sequential_data import save, sha
from run_sequential_v2 import fit_model, paired, mean, group_mean
from evaluate_sequential_v2 import write_tsv


def cluster_diagnostic(records, bundle):
    groups = sorted({r["group_id"] for r in records if r["source_family"] == "inera"})
    rows = defaultdict(list)
    for r in records:
        if r["source_family"] == "inera":
            rows[r["group_id"]].append(r)
    H = np.array(bundle["cluster_model"]["components"])
    rng = np.random.default_rng(t.SEED)
    similarity = []
    for i in range(20):
        draw = rng.choice(groups, len(groups), replace=True)
        sample = [r for g in draw for r in rows[g]]
        _, factor = t.clusters(sample, bundle["candidate_vocabulary"])
        h = np.array(factor["components"])
        cos = H @ h.T
        ii, jj = linear_sum_assignment(-cos)
        similarity.append(float(cos[ii, jj].mean()))
    return {
        "task": "OVERLAPPING_NATIVE_ATTRIBUTE_FACTORS",
        "source": "INERA only; removal of that source leaves no comparable complete frequency matrix",
        "original_independent_training_groups": len(groups),
        "group_bootstrap_draws": 20,
        "aligned_component_cosine_mean": float(np.mean(similarity)),
        "aligned_component_cosine_range": [min(similarity), max(similarity)],
        "independent_source_stability": "NOT_EVALUATED",
        "conditional_C0_C1_stability": "NOT_ESTIMABLE: paired validated context absent",
        "source_dominance": "Complete frequency factor estimates come entirely from INERA; projected semantic memberships in other sources are hypotheses. Downstream grouped CV, not this internal cosine, decides adoption.",
        "clusters_exclusive": False,
        "nutty_cocoa_split": False,
    }


def context_robustness(owner, metrics):
    path = t.OUT / "context_robustness.tsv"
    rows = list(csv.DictReader(path.open(), delimiter="\t"))
    if "group_id" not in rows[0]:
        return
    save(owner / "context_robustness.private.json", rows)
    out = []
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["dataset"], r["stage"], r["perturbation"]].append(r)
    for (ds, stage, perturb), rr in grouped.items():
        valid = [
            dict(r, loss=float(r["loss_increase"]))
            for r in rr
            if r.get("loss_increase") not in {"", None, "NA"}
        ]
        zero = [dict(r, loss=0.0) for r in valid]
        comparison = (
            paired(valid, zero, "loss")
            if valid
            else {"delta": None, "paired_group_95_interval": None}
        )
        out.append(
            {
                "dataset": ds,
                "stage": stage,
                "perturbation": perturb,
                "independent_groups": len({r["group_id"] for r in valid}),
                "conditions": len(valid),
                "mean_standardized_error_increase": comparison["delta"],
                "paired_group_95_interval": json.dumps(
                    comparison.get("paired_group_95_interval")
                ),
                "truth_unchanged": True,
                "status": (
                    "SOURCE_NATIVE_SENSITIVITY_INCONCLUSIVE"
                    if valid
                    else "NOT_ESTIMABLE"
                ),
                "reason": rr[0]["reason"],
                "c0_replacements": json.dumps(
                    sorted({r["c0_before"] + " -> " + r["c0_after"] for r in valid})
                ),
            }
        )
    write_tsv(path, out)
    metrics["context_robustness_summary"] = out


def review_pack(owner, records, metrics):
    selected = metrics["sequential"]["selected_model"]
    C = metrics["sequential"]["selected_C"]
    label = selected if selected != "M2_ADD" else "M2_ADD_C" + str(C)
    new = json.loads((owner / f"cv/{label}.private.json").read_text())
    other = json.loads((owner / f"cv/M2_HIER.private.json").read_text())
    old = {r["record_id"]: r for r in other}
    new = sorted(
        new,
        key=lambda r: (
            -abs((r["ndcg5"] or 0) - (old[r["record_id"]]["ndcg5"] or 0)),
            s.digest(r["record_id"]),
        ),
    )[:10]
    historical = json.loads(
        (owner / "cv/historical_predictions.private.json").read_text()
    )
    history = historical[selected][:10]
    histother = {r["record_id"]: r for r in historical["M2_HIER"]}
    pack = []
    key = []
    lookup = {r["record_id"]: r for r in records}
    for split, rows, opponents in [
        ("DEVELOPMENT_REVIEW", new, old),
        (
            "FROZEN_REVIEW_HISTORICAL_REGRESSION_NOT_NEW_CONFIRMATION",
            history,
            histother,
        ),
    ]:
        for r in rows:
            cid = "review:" + s.digest([split, r["record_id"]])[:16]
            flip = int(s.digest(cid)[0], 16) % 2
            ab = [r["ranking"][:8], opponents[r["record_id"]]["ranking"][:8]]
            ab = ab[::-1] if flip else ab
            pack.append(
                {
                    "case_id": cid,
                    "review_role": split,
                    "context": r["episode"]["context"],
                    "context_status": r["episode"]["context_assignment_status"],
                    "answer_sequence": r["payload"]["answers"],
                    "candidates_A": ab[0],
                    "candidates_B": ab[1],
                    "professional_observed_evidence": lookup[r["record_id"]]["targets"],
                    "evidence_scope": lookup[r["record_id"]]["supervision"],
                    "judgment_point": "Which candidate set is better supported; identify unsupported specificity, omitted important concepts and conflict with explicit answers. Missing descriptors are not automatic negatives.",
                    "human_choice": None,
                    "human_rationale": None,
                    "expertise": None,
                }
            )
            key.append(
                {
                    "case_id": cid,
                    "A": ("M2_HIER" if flip else selected),
                    "B": (selected if flip else "M2_HIER"),
                    "record_id": r["record_id"],
                }
            )
    save(owner / "human_comparison_cases.private.json", pack)
    save(owner / "human_comparison_key.private.json", key)
    return {
        "cases": len(pack),
        "development": 10,
        "frozen_historical_regression": 10,
        "fresh_locked_confirmatory": 0,
        "human_results_entered": 0,
        "path": str(owner / "human_comparison_cases.private.json"),
        "no_page_or_questionnaire_created": True,
    }


def semantic_counterexamples(bundle):
    import flavor_backend as legacy
    import flavor_planning as planner
    from evaluate_sequential_v2 import legacy_payload, baseline_bundle

    context = {"c0": s.C0[0], "c1": "medium"}
    base = s.initial_state(context, bundle)
    oldbundle = baseline_bundle(bundle)
    oldbase = legacy.run({"context": context, "answers": [], "model": "B1"}, oldbundle)[
        "candidate_state"
    ]["candidates"]
    oldbefore = {r["candidate_id"]: r for r in oldbase}
    before = {r["candidate_id"]: r for r in base["candidate_scores"]}
    results = []
    for name, visible, full in [
        ("floral_is_not_jasmine", ["attribute.floral"], False),
        ("composite_is_not_two_positives", ["attribute.nutty_cocoa"], False),
        ("cocoa_is_not_dark_chocolate", ["sensory.cocoa"], True),
        (
            "specific_multiselect_not_diluted",
            ["sensory.cocoa", "sensory.dark_chocolate"],
            True,
        ),
        ("all_broad_is_nondiscriminating", [], False),
    ]:
        state = s.initial_state(context, bundle, path="P4")
        while True:
            q = planner.select_next_question(state, bundle)
            if q["action"] != "ASK" or (
                not full and len(state["answers_by_question"]) == 2
            ):
                break
            answer = t.answer_for(q["question"], visible, bundle)
            if name == "all_broad_is_nondiscriminating":
                answer.update(
                    selected_option_ids=answer["shown_option_ids"], state="SELECTED"
                )
            state = s.update_joint_state(state, answer, bundle)
        payload = legacy_payload(state, oldbundle)
        # Six v2 slots can merge into historical semantic questions; this is an
        # evidence adapter for a counterexample, not a new product question flow.
        old = legacy.run(dict(payload, model="B1"), oldbundle)["candidate_state"][
            "candidates"
        ]
        oldafter = {r["candidate_id"]: r for r in old}
        after = {r["candidate_id"]: r for r in state["candidate_scores"]}
        watch = [
            c
            for c in ["sensory.jasmine", "sensory.cocoa", "sensory.dark_chocolate"]
            if c in after and c in oldafter
        ]
        enc = s.encode_features(state, bundle)
        results.append(
            {
                "case": name,
                "basis": "Synthetic algorithm counterexample, not a cupping record or human judgment",
                "selected_concepts": visible,
                "comparisons": [
                    {
                        "candidate_id": c,
                        "B1_score_delta": oldafter[c]["score"] - oldbefore[c]["score"],
                        "B1_rank_before": oldbefore[c]["rank"],
                        "B1_rank_after": oldafter[c]["rank"],
                        "M2_score_delta": after[c]["score"] - before[c]["score"],
                        "M2_rank_before": before[c]["rank"],
                        "M2_rank_after": after[c]["rank"],
                        "M2_explicit_confirmation": after[c]["explicit"],
                        "M2_specific_feature": enc["raw_features"][
                            enc["candidate_ids"].index(c)
                        ][1],
                    }
                    for c in watch
                ],
                "all_candidates_unchanged": state["candidate_scores"]
                == base["candidate_scores"],
            }
        )
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner-dir", type=Path, required=True)
    a = ap.parse_args()
    owner = a.owner_dir
    records = json.loads((owner / "recovery_records.json").read_text())
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    metrics = json.loads((t.OUT / "metrics.json").read_text())
    manifest = json.loads((t.OUT / "dataset_manifest.json").read_text())
    selected = metrics["sequential"]["selected_model"]
    modelpath = owner / "models" / f"{selected}.model.json"
    bundle = json.loads(modelpath.read_text())
    hier = json.loads((owner / "models/M2_HIER.model.json").read_text())
    start = time.time()
    # Preserve the exact manifest referred to by fitted bundles before adding report metadata.
    if not (owner / "training_manifest.private.json").exists():
        if s.digest(manifest) != bundle["data_manifest_hash"]:
            raise ValueError("TRAINING_MANIFEST_HASH_MISMATCH")
        save(owner / "training_manifest.private.json", manifest)
    frozen = json.loads((owner / "training_manifest.private.json").read_text())
    assert s.digest(frozen) == bundle["data_manifest_hash"]
    metrics["cluster_diagnostic"] = cluster_diagnostic(dev, hier)
    context_robustness(owner, metrics)
    old = json.loads(
        (t.ROOT / "db/data/backend-model-20260905/dataset_manifest.json").read_text()
    )
    batch = json.loads(
        (t.ROOT / "db/data/round3h/batch1/batch1_source_manifest.json").read_text()
    )
    inera = next(x for x in batch["sources"] if "bollen" in x["source_key"])
    manifest["record_recovery"]["fitted_manifest_hash"] = bundle["data_manifest_hash"]
    manifest["record_recovery"]["source_provenance"] = {
        "zenodo": {
            k: old["admitted_source"][k]
            for k in [
                "source_record_id",
                "version",
                "url",
                "creators",
                "source_sha256",
                "machine_license_field",
                "author_usage_notice",
                "current_experiment_use_basis",
                "conditions_checked",
            ]
        },
        "lengupa": {
            k: old["auxiliary_source"][k]
            for k in [
                "source_record_id",
                "version",
                "url",
                "author",
                "artifact_sha256",
                "machine_license_field",
                "author_usage_notice",
                "current_experiment_use_basis",
                "conditions_satisfied",
            ]
        },
        "inera": {
            "source_record_id": "figshare:25735122",
            "version": "1",
            "author": "Bollen et al.; source article and supplemental-file metadata retained in owner storage",
            "url": inera["doi_or_url"],
            "artifact_sha256": inera["official_file"]["sha256"],
            "machine_license_field": "CC BY 4.0",
            "author_usage_notice": "CC BY 4.0 source release",
            "current_experiment_use_basis": "NONCOMMERCIAL_RESEARCH_USE",
            "conditions_satisfied": {
                "attribution": True,
                "changes_disclosed": True,
                "local_model_retention": True,
                "no_raw_or_weight_public_release": True,
            },
        },
    }
    manifest["record_recovery"][
        "new_processing"
    ] = "Whole source broad categories retained; INERA 8 interpretable native frequency dimensions, Other excluded; Lengupa source codebook broad and fine concepts; distinct panelist mentions retained, no slash splitting."
    manifest["record_recovery"][
        "full_coffee_overlap_audit"
    ] = "Old coffee/sample groups preserved; INERA genotype joins both harvests; Lengupa original sample IDs, one study family; mirrors not additional groups. No cross-study common global lot ID, so unknown commercial supply overlap cannot be ruled out."
    # Allocation includes the uninterpretable case in coverage, but it supplies no loss.
    source_all = Counter(
        r["source_family"]
        for g in {r["group_id"] for r in dev}
        for r in [next(x for x in dev if x["group_id"] == g)]
    )
    source_labelled = Counter(
        r["source_family"]
        for g in {r["group_id"] for r in dev if r["targets"]}
        for r in [next(x for x in dev if x["group_id"] == g)]
    )
    mass = {source: source_labelled[source] / n for source, n in source_all.items()}
    for source, value in mass.items():
        manifest["record_recovery"]["source_share"][source][
            "effective_training_source_contribution"
        ] = value / sum(mass.values())
    for result in metrics["historical_same_information_comparison"][
        "selected_minus"
    ].values():
        result["scope"] = "PROXY_HISTORICAL_REGRESSION_NOT_NEW_CONFIRMATION"
    metrics["selection_decision"] = {
        "broader_record_recovery_research_candidate": selected,
        "replace_historical_M1": False,
        "reason": "New model regresses on matched fine descriptor scope; keep M1 and B2. Cluster branch rejected; selected M2 is a research candidate, not a product promotion.",
    }
    manifest["record_recovery"]["supervised_development_records"] = sum(
        bool(r["targets"]) for r in dev
    )
    manifest["record_recovery"]["supervised_development_groups"] = len(
        {r["group_id"] for r in dev if r["targets"]}
    )
    metrics["legacy_baseline_development"]["fine_only_scope"] = {
        "eligible_groups": metrics["legacy_baseline_development"][
            "selected_minus_B2_fine_only"
        ]["groups"],
        "all_case_groups": metrics["sequential"]["models"][selected]["groups"],
        "exclusion_reason": "No hidden fine descriptor after frozen visible/entailed-parent exclusion; no performance-based filtering. Full-scope results and case coverage also reported.",
    }
    metrics["feedback"][
        "retention_caveat"
    ] = "Selected feedback candidates come from the original top-eight exposure; F0 retention@8 is tautological, not evidence of improvement. F2 versus F1 hidden recovery is reported separately."
    save(t.OUT / "dataset_manifest.json", manifest)
    # Deterministic refit verifies the final code without overwriting retained weights.
    refitted, _ = fit_model(
        dev,
        selected,
        metrics["sequential"]["selected_C"],
        bundle["data_manifest_hash"],
        "all-development",
    )
    parameter_match = np.allclose(
        refitted["model_parameters"]["weights"],
        bundle["model_parameters"]["weights"],
        rtol=0,
        atol=1e-12,
    )
    scaler_match = refitted["scaler_parameters"] == bundle["scaler_parameters"]
    assert parameter_match and scaler_match
    example = json.loads(
        (owner / "cv/historical_predictions.private.json").read_text()
    )[selected][0]["payload"]
    a_live = s.run(example, bundle)
    a_eval = s.evaluation_entry(example, bundle)
    assert a_live == a_eval
    features = s.encode_features(example, bundle)
    assert features["features"] == a_live["state"]["features"]
    # Add numerical predictions as a separately disclosed state output. They never
    # become unseen laboratory features in the already fitted descriptor scorer.
    numeric = json.loads((owner / "models/context_models.model.json").read_text())
    delivery = copy.deepcopy(bundle)
    delivery["context_attribute_models"] = {
        name.split(":")[0]: m for name, m in numeric.items() if name.endswith(":C_C0")
    }
    delivery["delivery_scope"] = (
        "DEVELOPMENT_RESEARCH_CANDIDATE; no independent product confirmation"
    )
    save(owner / "models/selected_bundle.model.json", delivery)
    save(owner / "example_request.private.json", example)
    save(owner / "example_result.private.json", s.run(example, delivery))
    metrics["human_review"] = review_pack(owner, records, metrics)
    errors = {
        "scope": "Observed record recovery and engineering counterexamples; no unobserved descriptor treated as false sensory label",
        "findings": [
            {
                "issue": "Seven-bin context remains unsupported",
                "records_with_validated_C0_C1": 0,
                "effect": "Numerical native-context models cannot validate descriptor ranking or recover wrong production C1 through Q stages. Both fit and live descriptor masks agree.",
                "status": "NOT_ESTIMABLE",
            },
            {
                "issue": "Factor branch harms downstream ranking",
                "comparison": metrics["sequential"]["comparisons"]["HIER_minus_JOINT"],
                "action": "Retain trained HIER for audit, do not select it.",
            },
            {
                "issue": "Small interaction point gain",
                "comparison": metrics["sequential"]["comparisons"]["JOINT_minus_ADD"],
                "action": "Retain as research candidate; no independent improvement claim.",
            },
            {
                "issue": "Hedonic liking mixed into sensory block at first numerical checkpoint",
                "action": "Excluded overall_liking; saved original checkpoint outside repo, did not overwrite historical M1.",
            },
            {
                "issue": "One uninterpretable Lengupa code set",
                "records": 1,
                "action": "Retained in case coverage, excluded from labelled utility; no invented label.",
            },
            {
                "issue": "Semantic factors depend on one structured source",
                "diagnostic": metrics["cluster_diagnostic"],
            },
            {
                "issue": "Old baselines cannot output broad concepts",
                "action": "Report full candidate-target coverage and fine-only matched comparison separately.",
            },
        ],
        "not_evaluated": [
            "Real user QA outcomes",
            "Real final comparison feedback",
            "Independent product confirmation",
            "True sensory error-specificity rate under complete expert relevance labels",
        ],
        "no_agent_critique_used_as_truth": True,
    }
    errors["semantic_counterexamples"] = semantic_counterexamples(bundle)
    errors["findings"].append(
        {
            "issue": "Q1 does not improve this proxy ranking",
            "action": "Keep mandatory Q1 in sampling and runtime; do not claim utility. A value-trained complementary axis requires a separately recorded development iteration and fresh independent confirmation; no test-driven redesign.",
        }
    )
    errors["findings"].append(
        {
            "issue": "Broad-answer feature becomes suppressive in hidden-descriptor recovery",
            "action": "Report that the proxy can learn missing-token competition rather than product sensory support. Do not promote this model to product use; retain typed direct-support guards and historical baseline.",
        }
    )
    save(t.OUT / "errors.json", errors)
    save(t.OUT / "metrics.json", metrics)
    receipt = json.loads((t.OUT / "run_receipt.json").read_text())
    receipt["delivery"] = {
        "selected_model": selected,
        "model_path": str(owner / "models/selected_bundle.model.json"),
        "model_sha256": sha(owner / "models/selected_bundle.model.json"),
        "retained_model_paths": [
            str(p) for p in sorted((owner / "models").glob("*.model.json"))
        ],
        "code_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=t.ROOT, text=True
        ).strip(),
        "source_file_hashes": {
            p.name: sha(p)
            for p in sorted(
                set((t.ROOT / "db/scripts").glob("*sequential*.py"))
                | {
                    t.ROOT / "db/scripts" / n
                    for n in [
                        "flavor_backend.py",
                        "flavor_context.py",
                        "run_context_v2.py",
                        "backend-model-requirements.txt",
                    ]
                }
            )
        },
        "reproduction_command": 'python db/scripts/finish_sequential_v2.py --owner-dir "'
        + str(owner)
        + '"',
        "live_command": 'python db/scripts/flavor_backend.py --model-file "'
        + str(owner / "models/selected_bundle.model.json")
        + '" --input "'
        + str(owner / "example_request.private.json")
        + '"',
        "refit_identical_weights": bool(parameter_match),
        "refit_identical_scaler": scaler_match,
        "same_live_evaluation_features_scores": True,
        "verification_seconds": time.time() - start,
        "weights_not_public": True,
        "real_feedback_count": 0,
        "independent_product_confirmation": "NOT_EVALUATED",
        "remote_main_not_merged": True,
    }
    receipt["M2"]["status"] = "ACTUAL_FITTING_AND_COMPARATIVE_DIAGNOSTICS_COMPLETED"
    receipt["validation"] = {
        "basis": "Observed local checkpoint; finishing script does not execute these tests",
        "backend_unit_and_retained_artifact_tests_passed": 52,
        "tests_skipped_locally": 0,
        "public_snapshot_mandatory_tests_passed": 2,
        "restricted_corpus_replay": "NOT_EXECUTED; intentionally unavailable to public CI, unrelated to local admitted model data",
        "scope_check": "PASSED; zero frontend changes since 973f814",
        "dirty_main_worktree": "INSPECTED_READ_ONLY; original user modifications retained",
        "remote_status_last_observed": {
            "sha": "de4dc3a3c4ee0959cde2594dc71f3ba886668f4a",
            "status": "IN_PROGRESS",
            "not_claimed_accepted": True,
        },
    }
    save(t.OUT / "run_receipt.json", receipt)
    for path in owner.rglob("*"):
        if path.is_file():
            path.chmod(0o600)
    print(
        json.dumps(
            {
                "selected": selected,
                "identical_refit": bool(parameter_match),
                "cluster": metrics["cluster_diagnostic"],
                "model_path": receipt["delivery"]["model_path"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
