#!/usr/bin/env python3
"""Freeze R2 objectives and retain R1 evidence without rewriting its conclusions."""

from __future__ import annotations

import argparse
import datetime
from pathlib import Path
import subprocess

from alignment_metrics_r2 import METRIC_VERSION, SEMANTIC_RELATION_HASH
from profile_alignment_r2 import protocol as profile_protocol
from run_m2_r1 import ROOT, read, save, sha, freeze as verify_d0

OUT = ROOT / "db/data/backend-sequential-model-v2/revisions/r2"
BASE = "8c41e89214229c56849f04efaf61162c38b757d2"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def private_save(path, value):
    save(path, value)
    path.chmod(0o600)


def verify_frozen(owner):
    verify_d0(owner)
    private = owner / "revisions/r2"
    contract = read(OUT / "objective_and_metric_contract.json")
    if sha(private / "objective_and_metric_contract.frozen.json") != sha(
        OUT / "objective_and_metric_contract.json"
    ):
        raise ValueError("R2_OBJECTIVE_CONTRACT_CHANGED_AFTER_FREEZE")
    frozen = read(private / "immutable_prior_artifacts.private.json")
    for name, expected in frozen.items():
        if sha(name) != expected:
            raise ValueError("PRIOR_ARTIFACT_CHANGED:" + name)
    if (
        sha(private / "immutable_prior_artifacts.private.json")
        != contract["prior_preservation"]["manifest_sha256"]
    ):
        raise ValueError("IMMUTABLE_MANIFEST_CHANGED")
    if contract["primary_alignment"]["relation_sha256"] != SEMANTIC_RELATION_HASH:
        raise ValueError("FROZEN_SEMANTIC_RELATIONS_CHANGED")
    return contract


def freeze(owner):
    private = owner / "revisions/r2"
    if (OUT / "objective_and_metric_contract.json").exists():
        return verify_frozen(owner)
    verify_d0(owner)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if head != BASE:
        raise ValueError("REGISTER_ACTUAL_BASELINE_BEFORE_R2_FREEZE")
    paths = list((owner / "revisions/r1").rglob("*"))
    paths += list(
        (ROOT / "db/data/backend-sequential-model-v2/revisions/r1").rglob("*")
    )
    paths += [owner / "human_comparison_cases.private.json"]
    paths += [
        ROOT / "db/scripts" / name
        for name in [
            "flavor_m2_r1.py",
            "train_m2_r1.py",
            "flavor_backend.py",
            "flavor_sequential.py",
            "flavor_planning.py",
            "train_sequential.py",
            "flavor_foundation_r1.py",
            "professional_views_m2_r1.py",
            "sensory_views_m2_r1.py",
        ]
    ]
    frozen = {str(p): sha(p) for p in sorted(paths) if p.is_file()}
    private_save(private / "immutable_prior_artifacts.private.json", frozen)
    records = read(owner / "recovery_records.json")
    development = [r for r in records if r["split"] == "DEVELOPMENT"]
    folds = read(owner / "revisions/r1/D0_folds.private.json")
    contract = {
        "experiment_id": "M2_R2_PERCEPTUAL_ALIGNMENT_INFORMATION_EFFICIENCY",
        "registered_utc": now(),
        "code_baseline_sha": head,
        "branch": "research/coffee-sensory-data-ml-readiness",
        "lineage": "M2 revision; not M3",
        "new_objective_policy": "Introduced in R2 before new fits; R1 ranking regressions remain regressions.",
        "prior_preservation": {
            "files": len(frozen),
            "private_manifest": str(private / "immutable_prior_artifacts.private.json"),
            "manifest_sha256": sha(private / "immutable_prior_artifacts.private.json"),
            "D0_additionally_verified_by_R1_freeze": True,
        },
        "primary_task": "OBSERVED_DESCRIPTOR_RECOVERY",
        "primary_alignment": {
            "name": "FIXED_TAXONOMY_ONE_TO_ONE_FINE_RECOVERY_GAP_AT_5",
            "metric_version": METRIC_VERSION,
            "relation_sha256": SEMANTIC_RELATION_HASH,
            "reference": "Fixed R1 record-derived hidden T; same positive observations throughout trajectory",
            "formula": "1 - maximum one-to-one matching weight(top5 recovery fine candidates, distinct positive fine T) / number of fine T",
            "similarity": {
                "exact_fine_identity": 1.0,
                "distinct_fine_shared_fixed_R1_parent": 0.25,
                "otherwise": 0.0,
            },
            "granularity": "sensory.* only; compound IDs stay whole; broad descriptors and attributes receive no primary credit",
            "target_mask": "No fine T => null/unidentifiable; no prediction with fine T => gap 1; vocabulary-excluded T remains in denominator",
            "explicit_repetition": "Entire fixed visible A excluded before taking five; no direct-A identity is counted as new recovery",
            "output_interpretation": "Counterfactual five-item completion panel; actual full top5/direct retention reported separately; not actual user-display accuracy",
            "aggregation": "Coffee-group macro mean after equal record/path/stage weighting within a declared contrast",
            "scale": "Authored semantic proxy; not calibrated psychological distance or flavor probability",
        },
        "primary_cost": "ACTUALLY_OFFERED_ORDINARY_OPTION_COUNT",
        "cost_fields": [
            "ordinary_questions",
            "ordinary_options",
            "final_comparison_candidates",
            "human_response_seconds",
        ],
        "human_response_seconds": "NULL_UNLESS_ACTUALLY_MEASURED; NO_INFERRED_SECONDS_FROM_COMPUTE_LATENCY",
        "information_efficiency": {
            "alignment_threshold_gap": 0.5,
            "noninferiority_absolute_gap_margin": 0.02,
            "threshold_basis": "R2 operational research thresholds fixed before results; not validated human acceptability",
            "primary_cost_claim": "Require lower ordinary option cost and upper paired gap-difference interval <=0.02 on common groups at existing legal endpoints",
            "threshold_cost": "Earliest observed legal terminal endpoint reaching gap<=0.5; failures retained as not reached, never dropped from cost denominator",
            "diagnostic_prefixes": "All existing stages, including context and Q0/Q1, are curve observations, not new permitted stops",
            "final_comparison": "Candidate count separately included; pre-final and post-final curves separate, no free final correction",
            "real_sessions_absent_label": "PROXY_INFORMATION_BUDGET_GAIN_ONLY",
            "target_driven_stopping": "FORBIDDEN; thresholds evaluated retrospectively, never control runtime",
        },
        "data": {
            "development_records": len(development),
            "development_coffee_groups": len(folds),
            "development_folds_sha256": sha(
                owner / "revisions/r1/D0_folds.private.json"
            ),
            "outer_folds": 3,
            "router_training_expert_OOF_folds": 2,
            "base_model_internal_feature_folds": 2,
            "old_17_and_all_viewed_R1_confirmation": "HISTORICAL_REGRESSION_ONLY",
            "outer_scope": "Nested development evaluation of a new frozen objective; old D0 results previously inspected, not fresh confirmation",
        },
        "descriptor_inputs": {
            "runtime": "Required C0/C1, actually answered options and previously exposed final candidates only",
            "missing_source_context": "Not fabricated; existing source masks retained; synthetic valid context is engineering only",
            "forbidden_router_fields": [
                "coffee_id",
                "source_family",
                "future_answers",
                "hidden_targets",
                "oracle_expert_id",
                "measured_lab_values",
            ],
            "candidate_scope": "Per outer-train qualified R1 vocabulary intersect legacy FAMILY fine IDs; frozen for all experts and variants; target coverage retained",
            "paths": ["P1", "P4"],
            "primary_path": "P1",
            "question_policy": "Existing fixed R1 planner; all coordination variants share each record/path's actual questions and answers",
            "feedback": "One 3–8 candidate exposure after legal preliminary endpoint; choices only from visible A; hidden T never chooses feedback",
        },
        "coordination": {
            "eligible_experts": [
                "B2_TYPED_PRIOR_COMPONENT",
                "M2_R1_FINAL_FIXED_RESIDUAL",
            ],
            "excluded_M1_reason": "Retained training overlaps development; no raw retained M1 development OOF claim",
            "historical_originals": "Unchanged B2 and R1 outputs retained as controls, not known-error components of deployed ensemble",
            "score_alignment": "Expertwise midrank percentile over identical candidate universe; not probabilities",
            "shared_semantics": "Canonical direct priority once, compatible broad support +0.25 once, actually exposed NONE -1 once; deduplicate parent/child and feedback paths",
            "G0": "Best eligible single expert selected only on inner coffee-group OOF",
            "G1": {"global_R1_weight_grid": [0.0, 0.25, 0.5, 0.75, 1.0]},
            "G2": {
                "stages": ["INITIAL", "CORRECTION", "FINAL"],
                "weight_grid": [0.0, 0.25, 0.5, 0.75, 1.0],
                "shrinkage_pseudogroups": 50,
            },
            "G3": {
                "ridge": 10.0,
                "response": "inner OOF primary gap advantage of R1 versus B2",
                "sigmoid_temperature": 0.1,
                "shrinkage_pseudogroups": 50,
                "source_or_identity_features": False,
                "parameter_search": "NONE",
            },
            "primary_dynamic_contrast": "G3 minus G1 at P1 PRELIMINARY_RESULT, fixed information and five recovery results",
            "diagnostics": [
                "G1_minus_G0",
                "G2_minus_G1",
                "G3_minus_G0",
                "oracle_gap",
                "expert_error_overlap",
                "source_stage_strata",
            ],
            "in_session_parameter_updates": False,
        },
        "profiles": profile_protocol(),
        "task_registry": {
            "PROFESSIONAL_PROFILE_ALIGNMENT": "Native source-coded profile reconstruction MAE, product unit, other-view cells only; separate from descriptor ranks",
            "OBSERVED_DESCRIPTOR_RECOVERY": "Positive-only source descriptions, fixed A/T; no unmentioned sensory negatives",
            "RECORDED_RESPONSE_PREDICTION": "Complete CATA ballots with true binary zeros, held participant and held condition separately; no cross-coffee claim from one coffee",
            "INDIVIDUAL_PERCEPTUAL_ALIGNMENT": "Requires imported actual judgments independent of corrective selections; currently NOT_EVALUATED",
            "INFORMATION_EFFICIENCY": "Actual offered information budget in fixed legal paths; user-time efficacy NOT_EVALUATED without measured sessions",
        },
        "foundation": {
            "default": "OFF",
            "simple_attributes": "SEPARATE_MAIN_PROFILE_CONTROL",
            "CHECK": "R1 retained; no initial inclusion in coordinator pool or post-hoc hunt for favorable subgroups",
        },
        "new_data_policy": "New retrieval directions allowed; actual files and rights required. Freeze task-specific incremental controls and confirmation groups before viewing results. No synthetic sample reconstruction from papers.",
        "uncertainty": "Paired independent coffee/participant/condition unit as declared; 2000 fixed-prediction bootstraps for descriptor tasks; <10 groups show range and INCONCLUSIVE, not narrow generalization CI",
        "per_source_and_subgroups": "Diagnostic and exploratory; no unregistered product-wide promotion from nominal local intervals",
        "default": "B2_UNCHANGED_UNLESS_DECLARED_COMPARISON_SUPPORTS_CHANGE",
        "allowed_conclusions": [
            "SUPPORTED_IN_DECLARED_SCOPE",
            "NO_IMPROVEMENT",
            "INCONCLUSIVE",
            "NOT_ESTIMABLE",
            "NOT_EVALUATED",
        ],
        "publication": "Code, permissible configuration, aggregate metrics and hashes only; raw data, trajectories and weights stay private",
    }
    save(OUT / "objective_and_metric_contract.json", contract)
    private_save(private / "objective_and_metric_contract.frozen.json", contract)
    private_save(private / "D0_folds.private.json", folds)
    cases = read(owner / "human_comparison_cases.private.json")
    enriched = []
    for case in cases:
        enriched.append(
            {
                **case,
                "r2_usage": (
                    "HISTORICAL_REGRESSION"
                    if "HISTORICAL" in case["review_role"].upper()
                    else "DEVELOPMENT_REVIEW"
                ),
                "actual_or_simulated": "SIMULATED_RECORD_DERIVED_INPUT; HUMAN_JUDGMENT_NOT_COLLECTED",
                "independent_reference": {
                    "kind": "SOURCE_RECORDED_DESCRIPTORS",
                    "new_independent_user_judgment": False,
                    "source_observation_relationship": "Same original case record; not an independently tasted new coffee",
                },
                "input_information": {
                    "context": case["context"],
                    "answers": case["answer_sequence"],
                },
                "exposed_comparison_sets": {
                    "A": case["candidates_A"],
                    "B": case["candidates_B"],
                },
                "feedback_before_result": {
                    "A": case["candidates_A"],
                    "B": case["candidates_B"],
                },
                "feedback_after_result": None,
                "corrective_selection": None,
                "evaluation_judgment_independent_of_corrective_selection": None,
                "actual_response_seconds": None,
                "real_answer_evaluation": "NOT_EVALUATED",
            }
        )
    private_save(private / "human_comparison_cases_r2.private.json", enriched)
    save(
        OUT / "run_receipt.json",
        {
            "experiment_id": contract["experiment_id"],
            "baseline_sha": head,
            "status": "CONTRACT_FROZEN_BEFORE_NEW_FITS",
            "registered_utc": now(),
            "contract_sha256": sha(OUT / "objective_and_metric_contract.json"),
            "private_root": str(private),
            "default": "B2_UNCHANGED",
            "human_comparison_cases": {
                "count": len(enriched),
                "originals_preserved": True,
                "path": str(private / "human_comparison_cases_r2.private.json"),
                "real_judgments": 0,
                "real_times": 0,
            },
            "real_user_alignment": "NOT_EVALUATED",
            "real_user_time_efficiency": "NOT_EVALUATED",
            "old_results_reinterpreted": False,
        },
    )
    print("R2_CONTRACT_FROZEN; PRIOR_FILES=" + str(len(frozen)))
    return contract


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=["freeze", "verify"], default="freeze")
    args = parser.parse_args()
    (freeze if args.phase == "freeze" else verify_frozen)(args.owner_dir)
