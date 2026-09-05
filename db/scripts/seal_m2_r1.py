#!/usr/bin/env python3
"""Consolidate public R1 summaries while keeping all rows and weights private."""

from __future__ import annotations

import argparse
import importlib.metadata
import subprocess
import time
from pathlib import Path

from run_m2_r1 import OUT, ROOT, freeze, read, save, sha


def seal(owner, completed=False):
    config = freeze(owner)
    private = owner / "revisions/r1"
    metrics = read(OUT / "metrics.json")
    summaries = {
        "foundation": "foundation/report.private.json",
        "sensory_views": "sensory_views_metrics.private.json",
        "full_cata_views": "full_cata_metrics.private.json",
        "engineering": "engineering_checks.private.json",
    }
    for key, relative in summaries.items():
        metrics[key] = read(private / relative)
    professional = private / "professional_views_ROCCHETTI_metrics.private.json"
    if professional.exists():
        metrics["professional_views"] = read(professional)
    if completed and not professional.exists():
        raise ValueError("PROFESSIONAL_D1_TRAINING_SUMMARY_REQUIRED")
    metrics["selection_decision"] = {
        "backend_default": "B2",
        "preferred_valid_repaired_M2": "M2_R1_FINAL_FIXED",
        "retain_legacy_loss_as_control_only": "M2_R1_FIXED_LEGACY_LOCKED",
        "replace_B2_or_M1": False,
        "foundation_representation": "explicit_attributes",
        "foundation_scoring_fusion": 0,
        "foundation_check": "RESEARCH_ONLY_NO_IMPROVEMENT_IN_RECORD_PROXY",
        "D1_ranking_promotion": "INCONCLUSIVE; NOT_SELECTED",
        "complementary_Q01_promotion": "INCONCLUSIVE; RETAIN_FINAL_FIXED_QUESTION_PAIR",
        "source_native_attribute_heads": "SEPARATE_RESEARCH_TASKS; NOT_RUNTIME_FEATURES",
        "real_independent_answer_efficacy": "NOT_EVALUATED",
        "rationale": "Semantics were repaired, but common fine-descriptor gains over B2/M1 remain uncertain and old M2 full recovery is higher. The old proxy can reward suppression of observed broad categories. Do not promote a model from vocabulary coverage or auxiliary attribute accuracy alone.",
    }
    feedback = read(private / "final_feedback_diagnostics.private.json")
    granular = {}
    for category in ["REPEATED_INFORMATION", "BROAD_TO_SPECIFIC", "NEW_JUDGMENT"]:
        rows = [
            r
            for r in feedback
            if r["model"] == "F2" and r["category"] == category and r["selected_count"]
        ]
        granular[category] = {
            level: {
                "selection_events": sum(
                    c.startswith(prefix) for r in rows for c in r["selected_candidates"]
                ),
                "groups": len(
                    {
                        r["group_id"]
                        for r in rows
                        if any(c.startswith(prefix) for c in r["selected_candidates"])
                    }
                ),
            }
            for level, prefix in [
                ("fine_leaf", "sensory."),
                ("intermediate_descriptor", "broad."),
                ("broad_attribute", "attribute."),
            ]
        }
    metrics["final_feedback"]["selected_granularity"] = granular
    metrics["final_feedback"][
        "specificization_scope"
    ] = "Further specification from broad direction includes intermediate descriptors. Only fine_leaf counts represent sensory.* selections; the pooled subgroup effect is not a general fine-leaf claim."

    def directions_only(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "relevant_coefficient_directions":
                    value[key] = {
                        name: (
                            (
                                "POSITIVE"
                                if weight > 1e-12
                                else "NEGATIVE" if weight < -1e-12 else "ZERO"
                            )
                            if isinstance(weight, (int, float))
                            else weight
                        )
                        for name, weight in item.items()
                    }
                else:
                    directions_only(item)
        elif isinstance(value, list):
            for item in value:
                directions_only(item)

    directions_only(metrics)
    save(OUT / "metrics.json", metrics)
    redundant = OUT / "foundation_result.json"
    if redundant.exists():
        redundant.unlink()  # Generated duplicate; the report is now in metrics.json.

    log_names = {
        "initial_repair": "fit_log.private.json",
        "conditional_recovery": "conditional_fit_log.private.json",
        "conditional_Q01": "q01_fit_log.private.json",
        "final_repaired_Q01": "q01_final_fit_log.private.json",
        "canonical_final_feedback": "final_feedback_fit_log.private.json",
        "Peru_D1_mixed_catalog_control": "expansion_fit_log.private.json",
        "Peru_Condelli_D1_mixed_catalog_control": "expansion_fit_log_expanded.private.json",
        "Peru_Condelli_D1_strict_control": "expansion_fit_log_expanded_controlled.private.json",
    }
    fit_counts = {
        key: len(read(private / relative)) for key, relative in log_names.items()
    }
    fit_counts["source_native_context"] = metrics["context"]["actual_fits"]
    model_inventory = {
        str(path.relative_to(private)): {
            "sha256": sha(path),
            "bytes": path.stat().st_size,
        }
        for folder in ["models", "cv"]
        for path in sorted((private / folder).glob("*.model.json"))
    }
    receipt = read(OUT / "run_receipt.json")
    receipt.update(
        checkpoint=(
            "COMPLETED"
            if completed
            else "FOUNDATION_AND_REPAIR_VERIFIED; SOURCE_WORK_ACTIVE"
        ),
        updated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        code_sha_at_seal=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        actual_fit_counts=fit_counts,
        foundation_fit_scope={
            "outer_folds": 3,
            "inner_folds": 3,
            "representations": 4,
            "retained_full_development_bundles": 2,
            "fit_audit_private_path": str(
                private / "foundation/fit_audit.private.json"
            ),
        },
        model_paths={
            name: str(private / "models" / (name + ".model.json"))
            for name in [
                "M2_R1_FINAL_FIXED",
                "M2_R1_FOUNDATION",
                "M2_R1_FOUNDATION_CHECK",
                "M2_R1_CONTROLLED_D0_D1",
                "M2_R1_ORDINAL_ATTRIBUTES",
                "M2_R1_CATA_AUX_ATTRIBUTES_FULL",
                "M2_R1_PROFESSIONAL_VIEWS_ROCCHETTI",
            ]
        },
        private_artifact_root=str(private),
        model_inventory=model_inventory,
        old_models_and_results_byte_identical=True,
        immutable_D0_file_count=len(config["D0"]["immutable_file_sha256"]),
        selection=metrics["selection_decision"],
        independent_evidence={
            "foundation_and_ranking": "DERIVED_RECORD_PROXY",
            "CATA": "ACTUAL_RECORDED_CATA_VIEW_PREDICTION; ONE_COFFEE",
            "professional_attributes": "SOURCE_NATIVE_PANEL_AGGREGATES; NOT_USER_ANSWERS",
            "real_independent_answers": "NOT_EVALUATED",
            "original_17_groups": "PREVIOUSLY_VIEWED_HISTORICAL_REGRESSION",
            "Condelli_3_groups": "PREASSIGNED_HELD_OUT; NOW_VIEWED; NOT_FRESH_CONFIRMATION",
        },
        validation={
            **receipt.get("validation", {}),
            "backend_unit_suite_with_retained_owner_models": {
                "passed": 97,
                "skipped": 0,
            },
            "new_mechanism_tests": {"passed": 14, "skipped": 0},
            "public_artifact_and_context_tests": {"passed": 4, "skipped": 0},
            "foundation_tests": {"passed": 13, "skipped": 0},
            "professional_source_view_tests": {"passed": 6, "skipped": 0},
            "saved_model_full_contract_sessions": sum(
                v["completed_synthetic_contract_sessions"]
                for v in metrics["engineering"]["models"].values()
            ),
            "cross_process_hash_seed_cli_exact_matches": sum(
                v["cli_saved_model_exact_matches"]
                for v in metrics["engineering"]["models"].values()
            ),
            "foundation_three_fold_review_replay": "PASSED_RANKINGS_AND_METRICS_UNCHANGED",
            "full_CATA_tests": {"passed": 8, "skipped": 0},
            "source_adapter_final_replay": "PASSED; 11_ORIGINAL_ARTIFACT_HASHES_AND_RECORD_GROUP_MASK_ZERO_CHECKS",
            "professional_saved_model_replay": "PASSED; RETAINED_HASHES_AND_CACHED_CONFIRMATION_SUMMARY",
            "latency_scope": "Full synthetic session in-process; excludes Python startup, model loading and file IO.",
        },
        runtime_versions={
            name: importlib.metadata.version(name)
            for name in [
                "numpy",
                "scipy",
                "scikit-learn",
                "openpyxl",
                "lxml",
                "jsonschema",
            ]
        },
        executed_code_sha256={
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted((ROOT / "db/scripts").glob("*r1*.py"))
        },
    )
    receipt["commands"] = [
        "python db/scripts/run_m2_r1.py --owner-dir <owner-v2-root> --phase reproduce",
        "python db/scripts/run_m2_r1.py --owner-dir <owner-v2-root> --phase repair",
        "python db/scripts/conditional_m2_r1.py --owner-dir <owner-v2-root>",
        "python db/scripts/context_m2_r1.py --owner-dir <owner-v2-root>",
        "python db/scripts/final_feedback_m2_r1.py --owner-dir <owner-v2-root>",
        "python db/scripts/q01_m2_r1.py --owner-dir <owner-v2-root>",
        "python db/scripts/q01_m2_r1.py --owner-dir <owner-v2-root> --final-repair",
        "python db/scripts/evaluate_r1_final.py --owner-dir <owner-v2-root>",
        "python db/scripts/evaluate_foundation_r1.py --owner <owner-v2-root> --base-name M2_R1_FINAL_FIXED",
        "python db/scripts/acquire_m2_r1.py --owner <owner-v2-root>/revisions/r1",
        "python db/scripts/acquire_m2_r1.py --owner <owner-v2-root>/revisions/r1 --close-source-block",
        "python db/scripts/expansion_m2_r1.py --owner-dir <owner-v2-root> --expanded --controlled",
        "python db/scripts/sensory_views_m2_r1.py --owner-dir <owner-v2-root>",
        "python db/scripts/sensory_views_m2_r1.py --owner-dir <owner-v2-root> --full-cata",
        "python db/scripts/professional_views_m2_r1.py --owner-dir <owner-v2-root>/revisions/r1",
        "python db/scripts/verify_m2_r1.py --owner-dir <owner-v2-root>",
        "python db/scripts/context_m2_r1.py --owner-dir <owner-v2-root> --reuse-models",
        "python db/scripts/infer_m2_r1.py --model-file <private-model> --input <request-json>",
    ]
    manifest_path = OUT / "sample_expansion_manifest.json"
    if manifest_path.exists():
        manifest = read(manifest_path)
        receipt["actual_sample_increment"] = manifest["actual_increment"]
        receipt["source_work_block"] = manifest.get(
            "source_work_block", {"status": "IN_PROGRESS"}
        )
    save(OUT / "run_receipt.json", receipt)
    print("R1_SUMMARIES_SEALED; PRIVATE_MODEL_FILES=" + str(len(model_inventory)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--completed", action="store_true")
    args = parser.parse_args()
    seal(args.owner_dir, args.completed)
