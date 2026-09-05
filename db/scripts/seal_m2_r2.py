#!/usr/bin/env python3
"""Seal aggregate R2 evidence; never export observations or fitted parameters."""

from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import subprocess

from run_m2_r1 import ROOT, read, save, sha
from run_m2_r2 import OUT, freeze_learning_curve, now, verify_frozen


def regressions(value, path=""):
    """Index all adverse target contrasts, including tiny confirmation results."""
    result = {}
    if isinstance(value, dict):
        for key, item in value.items():
            location = f"{path}.{key}".strip(".")
            if key == "by_target":
                for target, block in item.items():
                    for contrast, delta in block.items():
                        if isinstance(delta, dict) and delta.get("delta", 0) > 0:
                            result[f"{location}.{target}.{contrast}"] = delta
                        elif contrast.startswith("delta_") and delta > 0:
                            result[f"{location}.{target}"] = block
            else:
                result.update(regressions(item, location))
    return result


def seal(owner, validation_path=None):
    contract = verify_frozen(owner)
    freeze_learning_curve(owner)
    private = owner / "revisions/r2"
    native = read(private / "profiles_public_summary.private.json")
    increment = read(private / "profiles_increment_public_summary.private.json")
    coordination = read(private / "coordination_summary.private.json")
    coordination["nested_router_fits"] = coordination.pop("fitted_routers")
    original = read(private / "original_complementarity.private.json")
    parity = read(private / "residual_order_parity.private.json")
    historical = read(private / "coordination_history_summary.private.json")
    if sha(ROOT / "db/scripts/flavor_coordination_r2.py") != parity["runtime_sha256"]:
        raise ValueError("REVALIDATE_CHANGED_COORDINATION_RUNTIME")
    isolation = read(private / "expert_isolation_audit.private.json")
    for audit in isolation:
        if set(audit["training_groups"]) & set(audit["held_groups"]):
            raise ValueError("EXPERT_GROUP_OVERLAP")
        for key in [
            "internal_feature_group_isolation_verified",
            "training_bank_recomputed_identical",
            "training_statistics_recomputed_identical",
        ]:
            if not audit[key]:
                raise ValueError("EXPERT_ISOLATION_UNVERIFIED:" + key)
    data = read(OUT / "data_increment_manifest.json")

    def public_save(path, value):
        def project(item):
            if isinstance(item, dict):
                return {key: project(child) for key, child in item.items()}
            if isinstance(item, list):
                return [project(child) for child in item]
            if isinstance(item, str):
                return item.replace(str(owner.parent), "<OWNER_RESEARCH_ROOT>")
            return item

        save(path, project(value))

    alignment = read(OUT / "alignment_cost_results.json")
    alignment["new_source_profiles_and_responses"] = increment
    alignment["data_expansion_summary_scope"] = (
        "The old native summary's pending data-expansion field describes its first "
        "checkpoint only. Completed new-source tasks and the fixed training-size "
        "control are in new_source_profiles_and_responses. No cross-source average."
    )
    public_save(OUT / "alignment_cost_results.json", alignment)
    cost = alignment["coordination_alignment_and_cost"]
    oof = {
        "coordination": coordination,
        "same_budget_endpoints": cost["same_budget_endpoints"],
        "primary_dynamic_contrast": cost["primary_dynamic_contrast"],
        "original_control_complementarity": original,
        "engineering_parity": parity,
        "historical_regression": historical,
        "isolation": {
            "audited_expert_fits": len(isolation),
            "training_held_overlap": 0,
            "inner_expert_OOF_only_for_router": True,
            "outer_groups_excluded_from_experts_router_and_scaler": True,
            "private_audit_sha256": sha(
                private / "expert_isolation_audit.private.json"
            ),
        },
        "interpretation": (
            "The eligible residual components are not unchanged B2/R1. Their oracle "
            "is worse than the original controls; original controls have some "
            "retrospective complementarity whose live detectability remains untested. "
            "Neither oracle is a deployable policy. All-prefix means are diagnostic."
        ),
    }
    public_save(OUT / "oof_expert_results.json", oof)
    errors = {
        "version": "m2-r2.error-analysis.v1",
        "prior_R1_results": "UNCHANGED; old full-recovery ranking regression remains a regression",
        "historical_coordinator_regression": historical,
        "restricted_pool_competence_loss": original["P1_endpoint"],
        "dynamic_coordination": {
            "primary_contrast": cost["primary_dynamic_contrast"],
            "observed_gain": False,
            "local_subgroup_policy": "No post-result tuning or CHECK subgroup search",
            "root_cause_scope": "Shared semantic/residual restriction loses useful original-control behavior. High component error overlap limits this pool; not proof all possible models lack complementarity.",
        },
        "native_task_adverse_target_contrasts": regressions(native["tasks"]),
        "increment_adverse_target_contrasts": regressions(increment["tasks"]),
        "new_confirmation_results": {
            name: task["confirmation_once"] for name, task in increment["tasks"].items()
        },
        "data_size_control": increment["tasks"]["barahona"]["learning_curve_control"],
        "coverage_and_cost": {
            "all_cases": 211,
            "all_coffee_groups": 187,
            "fine_target_identifiable_cases": 106,
            "fine_target_identifiable_groups": 104,
            "fine_target_unidentifiable_cases_retained": 105,
            "primary_cost_cohort": "Same 106 cases / 104 groups as alignment; full 211/187 cost reported separately",
            "threshold_failures": "All unreached and unidentifiable cases retained; conditional reached-case costs never called population savings",
            "prefix_stopping": "Not allowed; only existing P1/P4 legal endpoints compared",
            "final_candidates": "Actual eight-candidate comparison cost recorded separately; no synthetic seconds",
        },
        "final_feedback": cost["final_comparison"],
        "measurement_limits": [
            "Native source ordinal-code MAE is not calibrated psychological distance.",
            "Cotter binary CATA predicts recorded selection, not attribute intensity; held participant and held condition are separate one-coffee tasks.",
            "Liberica 0..5 anchors and zero meaning are not verified: nominal six-category response prediction only.",
            "Barahona consumer means are neither individual responses nor professional panel truth; liking and price excluded.",
            "Croijmans coded mentions include negations/comparisons: not positive sensory truth. Conflicting pairs quarantined, never silently repaired.",
            "A separate panel supplied 200 sorting ratings from 20 participants over 10 pairs of five shared coffees; ratings have within-person and shared-coffee dependence. Source description times are not product question times; neither was used to evaluate system-user alignment.",
            "No new complete production C0/C1 paired groups, no new professional intensity profiles, and no verified count of independent green lots.",
        ],
        "real_user_alignment": "NOT_EVALUATED",
        "real_user_time_efficiency": "NOT_EVALUATED",
        "selection": "B2 unchanged; CHECK off; all new models research-only",
    }
    public_save(OUT / "error_analysis.json", errors)
    reports = {
        "MECHANISM_VALIDATION": {
            "status": "SUPPORTED_IN_DECLARED_SCOPE",
            "scope": "Nested OOF isolation, deterministic semantic deduplication, legal final feedback and source-native cross-view predictability; not global product efficacy",
        },
        "PROFESSIONAL_PROFILE_ALIGNMENT": {
            "status": native["tasks"]["rocchetti"]["development"]["macro"][
                "P2_minus_P1"
            ]["status"],
            "scope": "Rocchetti 38-product development OOF source-code profile MAE; historical nine-product result inconclusive",
        },
        "OBSERVED_DESCRIPTOR_RECOVERY": {
            "status": "INCONCLUSIVE",
            "scope": "Original R1 versus B2 fine-gap difference inconclusive; R2 restricted coordinator is worse than both original controls; R1 NDCG regression preserved",
        },
        "RESPONSE_MODEL_GAIN": {
            "status": "SUPPORTED_IN_DECLARED_SCOPE",
            "scope": "Cotter held-person/condition CATA and new Liberica/Barahona source-native development tasks; small new confirmation results mixed and not established",
        },
        "PROXY_INFORMATION_EFFICIENCY": {
            "status": cost["primary_efficiency_contrast"]["status"],
            "scope": "PROXY_INFORMATION_BUDGET_GAIN for G3 existing P1 versus P4 closure, frozen 0.02 margin, same labelled cohort; coordinator itself is not promoted",
        },
        "REAL_USER_ALIGNMENT": {
            "status": "NOT_EVALUATED",
            "scope": "No actual system-user independent judgments",
        },
        "REAL_USER_TIME_EFFICIENCY": {
            "status": "NOT_EVALUATED",
            "scope": "No actual product session times",
        },
        "DYNAMIC_COORDINATION_GAIN": {
            "status": cost["primary_dynamic_contrast"]["status"],
            "scope": "G3 minus G1 P1 gap is positive; no observed improvement and no promotion",
        },
        "DATA_EXPANSION_CONTRIBUTION": {
            "status": increment["tasks"]["barahona"]["learning_curve_control"][
                "development"
            ]["macro"]["status"],
            "scope": "Fixed-model within-Barahona development training-product increment only; four-product confirmation reverses direction and is inconclusive; old M2 pooled D0/D1 effect not estimable",
        },
    }
    models = sorted(private.rglob("*.model.json"))
    if len(models) != 49:
        raise ValueError("RECONCILE_NEW_RETAINED_MODEL_COUNT")
    if any(path.stat().st_mode & 0o077 for path in models):
        raise ValueError("PRIVATE_MODEL_PERMISSIONS_TOO_BROAD")
    receipt = read(OUT / "run_receipt.json")
    validation = read(validation_path) if validation_path else {"status": "PENDING"}
    if validation_path and validation["candidate_validation_status"] != "PASS":
        raise ValueError("CANDIDATE_VALIDATION_MUST_PASS_BEFORE_COMPLETION")
    receipt.update(
        {
            "status": (
                "COMPLETE_LOCAL_RESEARCH"
                if validation_path
                else "RESULTS_SEALED_VALIDATION_PENDING"
            ),
            "sealed_utc": now(),
            "code_parent_commit_at_seal": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "reporting_categories": reports,
            "default": "B2_UNCHANGED",
            "foundation_check": "OFF",
            "new_model_disposition": "RESEARCH_ONLY; NO_RUNTIME_DEFAULT_OR_PUBLIC_WEIGHT_PROMOTION",
            "prior_immutable_files_verified": contract["prior_preservation"]["files"],
            "new_retained_model_count": len(models),
            "model_inventory": [
                {"private_relative_path": str(p.relative_to(private)), "sha256": sha(p)}
                for p in models
            ],
            "actual_fit_accounting": {
                "native_profiles": native["execution"],
                "new_source_bundle_fits": sum(
                    t["actual_bundle_fits"] for t in increment["tasks"].values()
                ),
                "new_source_target_fits": sum(
                    t["actual_target_fits"] for t in increment["tasks"].values()
                ),
                "new_nested_inner_R1_expert_fits": coordination[
                    "new_inner_expert_fits"
                ],
                "reused_outer_R1_experts": coordination["reused_outer_experts"],
                "router_fits": coordination["router_fit_counts"],
                "counting_note": "Component bundle, target-head and router fit counts are different units; not summed into an inflated model total",
            },
            "data_acquired": data["actual_increment"],
            "data_trained": {
                "liberica": "184 development observations (23 people x 8 conditions); 41 once-only held observations across three declared slices",
                "barahona": "14 development product means; four once-only confirmation products; fixed half/full training-size control",
                "croijmans": "ADMITTED_REFERENCE_ONLY; no language or distance model fitted",
            },
            "source_work_block": data["source_work_block"],
            "new_search_directions": sum(
                r["new_direction_vs_R1"] for r in data["acquisition_routes"]
            ),
            "private_source_summary_hashes": {
                name: sha(private / name)
                for name in [
                    "profiles_public_summary.private.json",
                    "profiles_increment_public_summary.private.json",
                    "coordination_summary.private.json",
                    "original_complementarity.private.json",
                    "residual_order_parity.private.json",
                ]
            },
            "engineering_parity": parity,
            "historical_coordinator_regression": historical,
            "runtime_versions": {
                n: importlib.metadata.version(n)
                for n in [
                    "numpy",
                    "scipy",
                    "scikit-learn",
                    "threadpoolctl",
                    "openpyxl",
                    "lxml",
                ]
            },
            "code_sha256": {
                str(p.relative_to(ROOT)): sha(p)
                for folder in ["db/scripts", "db/tests"]
                for p in sorted((ROOT / folder).glob("*r2*.py"))
            },
            "public_artifact_sha256": {
                p.name: sha(p)
                for p in sorted(OUT.iterdir())
                if p.is_file() and p.name != "run_receipt.json"
            },
            "validation": validation,
        }
    )
    public_save(OUT / "run_receipt.json", receipt)
    print(f"R2_AGGREGATES_SEALED; MODELS={len(models)}; DEFAULT=B2_UNCHANGED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--validation", type=Path)
    args = parser.parse_args()
    seal(args.owner_dir, args.validation)
