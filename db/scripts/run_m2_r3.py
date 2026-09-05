#!/usr/bin/env python3
"""Freeze the R3 mechanism/metric contract before fits; preserve prior revisions."""

from __future__ import annotations

import argparse
import datetime
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=["freeze", "verify"], default="freeze")
    args = parser.parse_args()
    {"freeze": freeze, "verify": verify}[args.phase](args.owner_dir)
