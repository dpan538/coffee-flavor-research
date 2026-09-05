#!/usr/bin/env python3
"""Freeze the R3 mechanism/metric contract before fits; preserve prior revisions."""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import math
from collections import defaultdict
from pathlib import Path
import subprocess

from alignment_metrics_r3 import protocol as metric_protocol
from external_construct_r3 import protocol as external_protocol
from multi_view_r3 import protocol as views_protocol
from run_m2_r1 import ROOT, read, save, sha
from run_m2_r2 import verify_frozen as verify_r2, private_save

OUT = ROOT / "db/data/backend-sequential-model-v2/revisions/r3"
BASE = "73dcea4cf59ae2d4e11d820b690fda56b8cee503"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def mechanism_protocol():
    from train_constraints_r3 import protocol

    return protocol()


def verify(owner):
    verify_r2(owner)
    private = owner / "revisions/r3"
    contract = read(OUT / "experiment_contract.json")
    if sha(OUT / "experiment_contract.json") != sha(
        private / "experiment_contract.frozen.json"
    ):
        raise ValueError("R3_CONTRACT_CHANGED_AFTER_FREEZE")
    for key, factory in [
        ("metrics", metric_protocol),
        ("mechanisms", mechanism_protocol),
        ("external_construct", external_protocol),
        ("multi_view", views_protocol),
    ]:
        if contract[key] != factory():
            raise ValueError("R3_PROTOCOL_CHANGED:" + key)
    prior = read(private / "prior_artifacts.private.json")
    for group, manifest in prior.items():
        root = ROOT if group == "repository" else owner
        for name, expected in manifest.items():
            if sha(root / name) != expected:
                raise ValueError("PRIOR_ARTIFACT_CHANGED:" + group + ":" + name)
    if (
        sha(private / "prior_artifacts.private.json")
        != contract["preservation"]["manifest_sha256"]
    ):
        raise ValueError("PRIOR_MANIFEST_CHANGED")
    return contract


def freeze(owner):
    if (OUT / "experiment_contract.json").exists():
        return verify(owner)
    verify_r2(owner)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if head != BASE:
        raise ValueError("R3_BASELINE_MISMATCH")
    # Resolve all protocol objects before producing any registration timestamp.
    protocols = {
        "metrics": metric_protocol(),
        "mechanisms": mechanism_protocol(),
        "external_construct": external_protocol(),
        "multi_view": views_protocol(),
    }
    private = owner / "revisions/r3"
    repo_paths = []
    for rev in ["r1", "r2"]:
        repo_paths += list(
            (ROOT / "db/data/backend-sequential-model-v2/revisions" / rev).rglob("*")
        )
    tracked = subprocess.check_output(
        ["git", "ls-files", "db/scripts/*.py", "db/tests/*.py"], cwd=ROOT, text=True
    ).splitlines()
    repo_paths += [ROOT / name for name in tracked]
    owner_paths = [
        p for rev in ["r1", "r2"] for p in (owner / "revisions" / rev).rglob("*")
    ]
    owner_paths += [
        owner / "recovery_records.json",
        owner / "human_comparison_cases.private.json",
    ]
    prior = {
        "repository": {
            str(p.relative_to(ROOT)): sha(p)
            for p in sorted(set(repo_paths))
            if p.is_file()
        },
        "owner_v2": {
            str(p.relative_to(owner)): sha(p)
            for p in sorted(set(owner_paths))
            if p.is_file()
        },
    }
    private_save(private / "prior_artifacts.private.json", prior)
    deleted = subprocess.check_output(
        ["git", "diff", "--name-only", "--diff-filter=D"], cwd=ROOT, text=True
    ).splitlines()
    private_save(private / "excluded_worktree_deletions.private.json", deleted)
    contract = {
        "experiment_id": "M2_R3_CONSTRAINT_RELATION_TRIGGER",
        "registered_utc": now(),
        "local_timezone": "Australia/Brisbane",
        "date_policy": "Actual environment time; no backdating registration to prompt date",
        "baseline_sha": head,
        "branch": "research/coffee-sensory-data-ml-readiness",
        "lineage": "M2 revision R3, not M3",
        "preservation": {
            "files": sum(len(v) for v in prior.values()),
            "manifest_sha256": sha(private / "prior_artifacts.private.json"),
            "all_R1_R2_results_unchanged": True,
            "unrelated_missing_tracked_files_excluded": len(deleted),
        },
        **protocols,
        "primary_descriptor_target": "Fixed source-record A/T positive fine descriptor recovery; no unmentioned sensory absence and no independent new human tasting claim",
        "primary_relation_contrast": "E2 minus E1 raw fine gap at5, same fixed ASK_Q3 path through Q4, all outer-held cases retained",
        "triple_contrast": "E3 minus E2 secondary; lower-order terms retained; no rename of pair-only model as triple",
        "primary_trigger_contrast": "Learned TriggerA policy minus ALWAYS_ASK_Q3 on same outer-held cases at legal Q4 endpoint",
        "primary_information_cost": "ACTUAL_ORDINARY_OFFERED_OPTIONS",
        "separate_costs": [
            "ordinary_questions",
            "ordinary_options",
            "final_comparison_candidates",
            "actual_human_response_seconds",
        ],
        "noninferiority": {
            "raw_gap_margin": 0.02,
            "basis": "R3 predeclared operational research tolerance; not established user-acceptable difference",
            "requirement": "Upper paired coffee-group gap-difference95 interval<=0.02 AND lower actual option budget on same identifiable cohort; no equivalence claim from nonsignificance",
        },
        "coverage": "Preserve all211DEVrecords/187groups, emptyT, OOVT, ties and failed outputs; report identifiable-gap cohort alongside all-case costs and missing-target coverage",
        "task_separation": {
            "constraint": "Legal-state validation plus target direction retention/pruning/correction proxy; incompatible-negative accuracy NOT_ESTIMABLE without comparable negative observations",
            "relation": "Conditional predictive increment over lower-order model, grouped OOF, not causality",
            "trigger": "Whole-policy loss/cost/coverage, wrong-trigger harm and missed gains including ties; AUC only optional diagnostic",
            "alignment": "Set matching, exact ranking, specificity and coverage separate; authored semantic proxy and external five-coffee pilot separate",
            "source_native_views": "Native professional codes, consumer aggregate codes and nominal recorded categories evaluated separately; no cross-task accuracy average",
            "real_users": "NOT_EVALUATED without actual independent system judgments/timing; reuse original20comparison cases, no generatedparticipants or new questionnaire",
        },
        "legal_path_revision": {
            "after_Q2": ["ASK_Q3_REFINE_CONSTRAINT", "SKIP_Q3_AND_CONTINUE_TO_Q4"],
            "early_Q2_end": False,
            "fake_Q3_answer": False,
            "final": "Existing Q4/Q5 closure, at most one actually exposed3–8candidate FINAL_COMPARISON, then terminate",
            "C0": "Required existing8familyIDs",
            "C1": "Required existing7roastIDs; no unknown/unsure/null/eighth class",
            "ordinary_unknown": "Existing ordinary UNSURE state for absent record information, never fabricated NONE_OF_THESE",
        },
        "constraints": {
            "types": [
                "HARD_CONTRACT",
                "SEMANTIC_ENTAILMENT",
                "EMPIRICAL_COMPATIBILITY",
            ],
            "K1_states": ["PROPOSED", "SUPPORTED_WITHIN_SCOPE", "REVISED"],
            "empirical_priority": "Reversible; legal universe retained; low score/context never hard deletes flavor",
            "provenance": "ID,type,target,source,actualanswer/evidenceIDs,applicability,status,revisinginformation",
            "groups": "One justified overlapping explanation group unless evidence supports more; unique descriptor identity and totalmain<=5/secondary<=3 budget",
        },
        "final_feedback": "F0/F1/F2 from same actual exposed pool; selection retention separate from hidden not-directly-selected recovery; nonshown nofeedback and unselected not universal sensorynegative",
        "uncertainty": "Fixed-prediction coffee/participant/condition group bootstrap in declared task; no source/population generalization; historical17 and prior-viewedconfirmation not fresh",
        "forbidden_inference_claims": [
            "CRF_OR_MEMM_IMPLEMENTED",
            "CALIBRATED_PERCEPTUAL_DISTANCE",
            "RANK_SOFTMAX_IS_FLAVOR_PROBABILITY",
            "SCORER_IS_ANSWER_WORLD_MODEL",
            "DR_OR_IPS_WITHOUT_LOGGED_PROPENSITIES",
            "REINFORCEMENT_LEARNING",
        ],
        "new_data": "Actual files/keys/scales/rights then separate frozen fixed-model increment protocol before fresh confirmation evaluation; no many-to-many synthetic joins",
        "default": "B2_UNCHANGED",
        "foundation_check": "OFF",
        "publication": "Code, allowed configuration, aggregates and hashes only; raw data, individual rows, trajectories and fitted parameters private",
    }
    save(OUT / "experiment_contract.json", contract)
    private_save(private / "experiment_contract.frozen.json", contract)
    save(
        OUT / "run_receipt.json",
        {
            "experiment_id": contract["experiment_id"],
            "baseline_sha": head,
            "registered_utc": contract["registered_utc"],
            "contract_sha256": sha(OUT / "experiment_contract.json"),
            "status": "FROZEN_BEFORE_FITS",
            "default": "B2_UNCHANGED",
            "foundation_check": "OFF",
            "old_results_reinterpreted": False,
        },
    )
    print("R3_CONTRACT_FROZEN=" + sha(OUT / "experiment_contract.json"))
    return contract


def assemble(owner):
    """Publish allowed summaries only; source rows and model parameters stay private."""
    verify(owner)
    private = owner / "revisions/r3"
    old = read(OUT.parent / "r2/oof_expert_results.json")
    metrics = {
        "status": "ACTUAL_GROUPED_TRAINING_AND_FIXED_SOURCE_INCREMENT_COMPLETED",
        "default": "B2_UNCHANGED",
        "foundation_check": "OFF",
        "validation_scope": {
            "descriptor_recovery": "Outer-held source-defined coffee groups; stable independent participant identity unavailable across these sources, so not simultaneous participant isolation",
            "Rocchetti_Barahona": "Held source product, aggregated panel/consumer attributes; individual participant holdout not identifiable from aggregate rows",
            "Liberica": "Separate held-participant/shared-condition and held-condition/shared-participant tasks; no new-coffee or crossed coffee-participant claim",
            "Castillo_increment": "Held grader, same two processing conditions and one material shared; no new coffee",
            "crossed_unseen_coffee_and_participant": "NOT_ESTIMABLE_FROM_CURRENT_LINKED_SUPERVISION; not approximated with a concatenated coffee-participant group key",
            "Croijmans": "Fixed five-coffee matrix pilot with independent sorting cohort; participant resampling is conditional on these five coffees",
        },
        "retained_R2": {
            "source_sha256": sha(OUT.parent / "r2/oof_expert_results.json"),
            "primary_dynamic_contrast": old["primary_dynamic_contrast"],
            "original_controls_P1": old["original_control_complementarity"][
                "P1_endpoint"
            ],
            "same_budget_P1": old["same_budget_endpoints"]["P1"],
            "historical_regression": old["historical_regression"],
            "interpretation": "Original numbers retained, including regressions; R3 metrics do not rewrite R2 outcomes",
        },
    }
    summaries = {
        "first_relation": "first_relation_public_summary.private.json",
        "constraints_relations_triggers": "constraints_public_summary.private.json",
        "external_construct": "external_construct_public_summary.private.json",
        "existing_multi_view": "multi_view_public_summary.private.json",
        "new_source_increment": "castillo_increment_public_summary.private.json",
    }
    for key, name in summaries.items():
        metrics[key] = read(private / name)
    # Regression summaries are public already. New individual cases are not.
    serialized = json.dumps(metrics, ensure_ascii=False)

    def contains_private_fields(value):
        if isinstance(value, dict):
            return bool(
                set(value) & {"record_id", "participant_id", "coefficients"}
            ) or any(contains_private_fields(item) for item in value.values())
        if isinstance(value, list):
            return any(contains_private_fields(item) for item in value)
        return False

    # An axis-name value such as holdout_axis="participant_id" is metadata,
    # not an individual participant identifier.
    if str(owner) in serialized or contains_private_fields(metrics):
        raise ValueError("PRIVATE_DETAIL_IN_PUBLIC_SUMMARY")
    if metrics["constraints_relations_triggers"].get("counterfactual_examples"):
        raise ValueError("PER_CASE_COUNTEREXAMPLES_MUST_REMAIN_PRIVATE")
    save(OUT / "metrics.json", metrics)
    audit = read(OUT / "metric_audit.json")
    audit["construct_status"] = "EXTERNAL_CONSTRUCT_CHECK_PILOT"
    audit["external_construct_summary_sha256"] = sha(
        private / summaries["external_construct"]
    )
    save(OUT / "metric_audit.json", audit)
    manifest = read(OUT / "data_increment_manifest.json")
    manifest["admitted_summary"] = read(
        private / "admitted_multiview_sources_public_summary.private.json"
    )
    for source_key in ["castillo", "commercial"]:
        manifest[source_key] = manifest["admitted_summary"][source_key]
    manifest["fixed_increment_contract"] = read(
        private / "castillo_increment_contract.private.json"
    )
    manifest["fixed_increment_contract_sha256"] = sha(
        private / "castillo_increment_contract.private.json"
    )
    manifest["increment_summary_sha256"] = sha(
        private / summaries["new_source_increment"]
    )
    manifest["increment_interpretation"] = (
        "Same frozen native targets/model/held graders; new training-grader and measured-view budgets separated; not D0+D1 core descriptor gain"
    )
    manifest["attribution_addendum"] = read(
        private / "native_source_attribution_addendum.private.json"
    )
    manifest["attribution_policy"] = (
        "Use addendum authors/dates; preserve frozen admission metadata defect, raw data and all model hashes"
    )
    save(OUT / "data_increment_manifest.json", manifest)
    registry = read(private / "constraint_relation_trigger_registry.private.json")
    columns = [
        "id",
        "type",
        "status",
        "condition",
        "scope",
        "action",
        "training_group_support",
        "held_Q4_active_records",
        "candidate_effect_direction",
        "training_evidence_group_hash",
        "revision_rule",
    ]
    with (OUT / "constraint_relation_trigger_registry.tsv").open("w") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in registry:
            selected = {key: row.get(key, "") for key in columns}
            selected["revision_rule"] = (
                "New legally acquired answer recomputes compatibility; contract-invalid states alone permit rejection; no low-score hard deletion"
            )
            writer.writerow(
                {
                    k: (
                        json.dumps(v, sort_keys=True, ensure_ascii=False)
                        if isinstance(v, (dict, list))
                        else v
                    )
                    for k, v in selected.items()
                }
            )
        for identifier, kind, condition, action, scope in [
            (
                "R3_DIRECT_COMPONENT",
                "DIRECT_SEMANTIC_AND_CONSTRAINT",
                "Typed exposed evidence",
                "Apply canonical evidence once",
                "Concept entailment and same-target R1 candidate score; not a calibrated probability",
            ),
            (
                "R3_NATIVE_VIEW_COMPONENT",
                "PROFESSIONAL_AND_MULTI_VIEW",
                "Source-native observed fields with target mask",
                "Predict held native attribute/code",
                "Native numeric MAE or nominal Brier only; never average these with descriptor logits; auxiliary research interface",
            ),
            (
                "R3_COMPLETION_COMPONENT",
                "CONDITIONAL_DESCRIPTOR_RETRIEVAL",
                "Eligible TRAIN-side pair patterns at acquired semantic question IDs",
                "Add regularized nonexplicit candidate score delta",
                "Same hidden positive mention-recovery target as base; not sensory absence or causality",
            ),
            (
                "R3_TRIPLE_CORE",
                "CANDIDATE_MECHANISM",
                "Q0xQ1xQ2 support rule",
                "No supported core triple fitted",
                "Insufficient support, not proof that triples are ineffective",
            ),
        ]:
            writer.writerow(
                {
                    "id": identifier,
                    "type": kind,
                    "status": "RESEARCH_ONLY_DEFAULT_UNCHANGED",
                    "condition": condition,
                    "action": action,
                    "scope": scope,
                }
            )
    receipt = read(OUT / "run_receipt.json")
    receipt["summary_artifacts"] = {
        name: sha(private / name) for name in summaries.values()
    }
    receipt["reproduction"] = {
        "command": "python db/scripts/run_m2_r3.py --phase reproduce --owner-dir OWNER_V2_DIRECTORY",
        "requires": "Persistent private source/model artifacts and original research Python dependencies; no raw rows are downloaded from the public repository",
        "behavior": "Verify original contracts and private artifact hashes, reload all completed component results, reproduce the same public aggregates; no repeated training or historical reclassification",
        "fresh_fit_commands": [
            "python db/scripts/train_constraints_r3.py --help",
            "python db/scripts/multi_view_r3.py --help",
            "python db/scripts/castillo_increment_r3.py --help",
        ],
    }
    save(OUT / "run_receipt.json", receipt)
    return metrics


def reproduce(owner):
    """Replay sealed components without silently retraining or re-selecting models."""
    verify(owner)
    from train_constraints_r3 import verify_completed
    from external_construct_r3 import run as external_run
    from multi_view_r3 import run as views_run
    from castillo_increment_r3 import run as increment_run
    from source_attribution_r3 import run as attribution_run

    contract = OUT / "experiment_contract.json"
    amendment = owner / "revisions/r3/internal_feature_amendment.frozen.json"
    completed = verify_completed(owner, contract, sha(contract), sha(amendment))
    external_run(owner, contract)
    views_run(owner, contract)
    increment_run(
        owner, owner / "revisions/r3/castillo_increment_contract.private.json"
    )
    attribution_run(owner)
    metric_replay = recheck_metrics(owner, completed["public_summary"])
    result = assemble(owner)
    receipt = read(OUT / "run_receipt.json")
    receipt["reproduction_verified"] = {**completed["verification"], **metric_replay}
    save(OUT / "run_receipt.json", receipt)
    print("R3_REPRODUCED_WITH_RELOADED_FROZEN_COMPONENTS=true")
    return result


def recheck_metrics(owner, expected):
    """Recalculate R3 endpoint metrics from sealed rankings and fixed targets."""
    from alignment_metrics_r3 import evaluate

    compared = 0
    for filename, section in [
        ("relation_results.private.json", "fixed_relation_Q4"),
        ("policy_results.private.json", "policy_Q4"),
        ("final_feedback_results.private.json", "final_feedback"),
    ]:
        rows = [
            r
            for r in read(owner / "revisions/r3" / filename)
            if r["slot"] in {"Q4", "FINAL_COMPARISON"}
        ]
        identities = [(r["model"], r["record_id"], r["slot"]) for r in rows]
        if len(set(identities)) != len(identities):
            raise ValueError("DUPLICATE_REPLAY_MODEL_RECORD_STAGE")
        groups = defaultdict(lambda: defaultdict(list))
        for row in rows:
            result = evaluate(
                row["ranking"],
                row["episode"]["relevance"],
                row["fixed_candidates"],
                excluded_visible=row["episode"]["visible"],
            )
            for field in [
                "raw_gap",
                "ndcg",
                "recall",
                "M",
                "M_star",
                "opportunity_gap",
            ]:
                a, b = result[field], row[field]
                if (a is None) != (b is None) or (
                    a is not None and not math.isclose(a, b, abs_tol=1e-12)
                ):
                    raise ValueError("SEALED_RANKING_METRIC_REPLAY_MISMATCH:" + field)
            if result["raw_gap"] is not None:
                groups[row["model"]][row["group_id"]].append(result["raw_gap"])
            compared += 1
        for model, group_rows in groups.items():
            group_means = [sum(v) / len(v) for v in group_rows.values()]
            gap = sum(group_means) / len(group_means)
            if not math.isclose(gap, expected[section][model]["gap"], abs_tol=1e-12):
                raise ValueError("GROUP_MACRO_REPLAY_MISMATCH:" + model)
    return {
        "endpoint_rankings_recalculated": compared,
        "metrics_recalculated": [
            "raw_gap",
            "ndcg",
            "recall",
            "M",
            "M_star",
            "opportunity_gap",
        ],
        "metric_replay_matches_saved": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument(
        "--phase",
        choices=["freeze", "verify", "assemble", "reproduce"],
        default="verify",
    )
    args = parser.parse_args()
    {"freeze": freeze, "verify": verify, "assemble": assemble, "reproduce": reproduce}[
        args.phase
    ](args.owner_dir)
