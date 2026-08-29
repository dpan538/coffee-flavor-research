#!/usr/bin/env python3
"""Fail-closed public contract tests for the Batch 5 normalization smoke."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "normalization-smoke"
CURRENT = ROOT / "db" / "data" / "current"

EXPECTED_FILES = {
    "EXPERIMENTAL_BASELINE_ABLATION.tsv",
    "EXPERIMENTAL_BASELINE_CONFIGURATION.tsv",
    "EXPERIMENTAL_BASELINE_DECISION.json",
    "EXPERIMENTAL_BASELINE_LEARNING_CURVE.tsv",
    "EXPERIMENTAL_BASELINE_METRICS.tsv",
    "SHA256SUMS",
    "SMOKE_CONFIGURATION_REGISTRY.tsv",
    "SMOKE_CONFUSION_SUMMARY.tsv",
    "SMOKE_ELIGIBILITY_AUDIT.tsv",
    "SMOKE_FAMILY_HOLDOUT_METRICS.tsv",
    "SMOKE_FINAL_DECISION.json",
    "SMOKE_GROUP_ASSIGNMENT.tsv",
    "SMOKE_INPUT_MANIFEST.json",
    "SMOKE_METRICS.tsv",
    "SMOKE_MODEL_FILE_AUDIT.json",
    "SMOKE_PREDICTION_RECEIPT.tsv",
    "SMOKE_REPRODUCIBILITY_RECEIPT.json",
    "SMOKE_RIGHTS_FILTER_AUDIT.tsv",
    "SMOKE_RUNTIME_ENVIRONMENT.json",
    "SMOKE_SEEN_UNSEEN_FORM_METRICS.tsv",
    "SMOKE_SPLIT_LEAKAGE_AUDIT.tsv",
    "SMOKE_SPLIT_MANIFEST.json",
    "SMOKE_TARGET_SUPPORT.tsv",
}
MODEL_SUFFIXES = {
    ".bin", ".ckpt", ".joblib", ".onnx", ".pkl", ".pt", ".pth",
    ".safetensors", ".tflite",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def document(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> None:
    inventory = {path.name for path in DATA.iterdir() if path.is_file()}
    check(inventory == EXPECTED_FILES, "normalization smoke output inventory drift")
    listed = {}
    for line in (DATA / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[name] = digest
    check(set(listed) == EXPECTED_FILES - {"SHA256SUMS"}, "smoke checksum inventory drift")
    check(all(sha(DATA / name) == digest for name, digest in listed.items()), "smoke artifact hash drift")

    manifest = document("SMOKE_INPUT_MANIFEST.json")
    check(manifest["project_owner_authorization"] == "NORMALIZATION_ENGINEERING_SMOKE_MODEL_RUN_APPROVED", "owner authorization absent")
    check(
        all(sha(CURRENT / name) == digest for name, digest in manifest["input_file_sha256"].items()),
        "governed smoke input hash drift",
    )
    check(manifest["smoke_source_corpus_version"] == "professional-descriptor-candidate-v1-30k", "source corpus version drift")
    check(manifest["smoke_source_corpus_sha256"] == sha(CURRENT / "CANDIDATE_30K_SNAPSHOT_MANIFEST.json"), "snapshot hash drift")
    check(manifest["cleaner_contract_version"] == "batch4.semantic-cleaner.v2", "cleaner contract drift")
    check(manifest["post30k_extension_included"] is False, "post-30k extension entered smoke")
    check(manifest["frozen_corpus_checkpoints_mutated"] is False, "frozen checkpoint mutation claimed")
    check(manifest["raw_source_text_publication"] is False, "raw text publication widened")
    check(manifest["rights_permitted_strict_output_count"] == 4096, "rights strict count drift")
    check(manifest["machine_governed_strict_output_count"] == 9439, "machine strict count drift")
    check(manifest["exact_intersection_output_count"] == 1005, "exact eligible intersection drift")
    check(manifest["grouped_sample_count"] == 198, "grouped sample count drift")
    check(manifest["effective_record_count"] == 219, "effective record count drift")
    check(manifest["source_family_count"] == 3 and manifest["target_concept_count"] == 52, "source/target diversity drift")

    eligibility = rows("SMOKE_ELIGIBILITY_AUDIT.tsv")
    check(len(eligibility) == 31676, "eligibility audit does not cover every output atom")
    admitted = [row for row in eligibility if row["engineering_smoke_eligible"] == "true"]
    check(len(admitted) == manifest["exact_intersection_output_count"], "eligibility audit admission count drift")
    check(all(row["semantic_class"] == "STRICT_FLAVOR" for row in admitted), "non-strict output admitted")
    check(all(row["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE" for row in admitted), "ungoverned output admitted")
    check(all(row["target_concept_id"] for row in admitted), "admitted output lacks governed target")
    check(all(row["noncommercial_model_research_right"] in {"AFFIRMATIVE", "AFFIRMATIVE_WITH_CONDITIONS"} for row in admitted), "rights-ineligible output admitted")
    check(all(row["restricted_text_available"] == "true" for row in admitted), "admitted restricted input unavailable")
    check(all(row["model_eligible"] == "false" for row in eligibility), "deployment model eligibility widened")

    split = document("SMOKE_SPLIT_MANIFEST.json")
    groups = rows("SMOKE_GROUP_ASSIGNMENT.tsv")
    check(len(groups) == 198, "group assignment count drift")
    check(Counter(row["split"] for row in groups) == Counter({"TRAIN": 139, "DEV": 30, "TEST": 29}), "70/15/15 group allocation drift")
    check(sum(int(row["output_atom_count"]) for row in groups) == 1005, "group output reconciliation drift")
    check(split["train_output_count"] + split["dev_output_count"] + split["test_output_count"] == 1005, "split output count drift")
    check(split["lexical_form_disjoint_split"]["feasible"] is False, "lexical disjoint feasibility drift")
    leakage = rows("SMOKE_SPLIT_LEAKAGE_AUDIT.tsv")
    check(len(leakage) == 4, "leakage audit inventory drift")
    check(all(row["status"] == "PASS" and int(row["cross_split_leak_count"]) == 0 for row in leakage), "cross-split leakage detected")

    configurations = rows("SMOKE_CONFIGURATION_REGISTRY.tsv")
    check(len(configurations) == 6, "configuration cap violated")
    check(all(row["source_family_feature_used"] == "false" for row in configurations), "source family used as feature")
    check(all(row["target_label_text_feature_used"] == "false" for row in configurations), "target label text used as feature")
    check(all(row["model_weight_persisted"] == "false" for row in configurations), "model weight persistence claimed")
    metrics = rows("SMOKE_METRICS.tsv")
    check(len(metrics) == 12, "grouped DEV/TEST metrics inventory drift")
    numeric_fields = {
        "supported_target_coverage", "prediction_coverage", "abstention_rate",
        "top1_accuracy", "top3_accuracy", "macro_f1", "weighted_f1", "micro_f1",
        "mean_reciprocal_rank", "seen_form_top1", "unseen_form_top1",
        "unseen_form_top3", "unsupported_target_rate", "worst_family_macro_f1",
    }
    check(all(math.isfinite(float(row[field])) for row in metrics for field in numeric_fields), "non-finite smoke metric")
    family = rows("SMOKE_FAMILY_HOLDOUT_METRICS.tsv")
    check(len(family) == 18, "not every configuration ran all three family holdouts")
    check(len({row["held_out_source_family_id"] for row in family}) == 3, "family holdout coverage drift")

    support = rows("SMOKE_TARGET_SUPPORT.tsv")
    check(len(support) == 52, "target support inventory drift")
    check(sum(int(row["output_atom_count"]) for row in support) == 1005, "target support output reconciliation drift")
    check(all(row["support_status"] in {"SUPPORTED_TARGET", "LOW_SUPPORT_TARGET", "TRAIN_UNSUPPORTED_TARGET"} for row in support), "unknown support state")

    predictions = rows("SMOKE_PREDICTION_RECEIPT.tsv")
    expected_prediction_fields = {
        "protocol", "evaluation_id", "configuration_id", "cleaned_output_atom_id",
        "input_hash", "cleaned_form_hash", "group_id", "split", "source_family_id",
        "true_target_concept_id", "predicted_target_concept_id", "prediction_rank",
        "score", "abstention_status", "seen_form_status",
    }
    check(set(predictions[0]) == expected_prediction_fields, "prediction receipt public schema drift")
    forbidden_field_fragments = {"lexical_text", "source_native_text", "raw_text", "cleaned_text", "field_label_text"}
    check(not any(any(fragment in field.casefold() for fragment in forbidden_field_fragments) for field in predictions[0]), "text-bearing prediction column leaked")
    check(all(len(row["input_hash"]) == 64 and len(row["cleaned_form_hash"]) == 64 for row in predictions), "prediction hash contract drift")

    final = document("SMOKE_FINAL_DECISION.json")
    check(final["phase_status"] == "ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY", "scientific interpretation drift")
    check(final["engineering_smoke_pass"] is True and final["conditional_experimental_baseline_run"] is True, "authorized baseline did not complete")
    check(final["selected_configuration_id"] == "B2_CHAR_LINEAR", "selected fixed configuration drift")
    check(final["selected_test_unseen_form_top1"] == 0 and final["selected_test_unseen_form_top3"] == 0, "unexpected unseen-form signal")
    check(final["human_reviewed_normalized_form_count"] == 0 and final["model_eligible_assertion_count"] == 0, "scientific boundary widened")
    check(final["training_corpus_frozen"] is False and final["product_model_status"] == "NOT_AUTHORIZED", "product/training boundary widened")

    reproducibility = document("SMOKE_REPRODUCIBILITY_RECEIPT.json")
    check(reproducibility["byte_identical_core_rerun"] is True and reproducibility["reproducibility_pass"] is True, "offline reproducibility failed")
    model_audit = document("SMOKE_MODEL_FILE_AUDIT.json")
    check(model_audit["committed_model_weight_file_count"] == 0, "committed model weight detected")
    check(model_audit["released_model_weight_file_count"] == 0, "released model weight claimed")
    check(not any(path.is_file() and path.suffix.lower() in MODEL_SUFFIXES for path in ROOT.rglob("*")), "forbidden model suffix in repository")

    print("NORMALIZATION_ENGINEERING_SMOKE_CONTRACT_PASS=true")
    print("SMOKE_EXACT_INTERSECTION_OUTPUT_COUNT=1005")
    print("CROSS_SPLIT_LEAK_COUNT=0")
    print("CONFIGURATION_COUNT=6")
    print("COMMITTED_MODEL_WEIGHT_FILE_COUNT=0")
    print("SMOKE_FINAL_STATUS=ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY")


if __name__ == "__main__":
    main()
