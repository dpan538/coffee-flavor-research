#!/usr/bin/env python3
"""Fail-closed tests for the Round 3N offline inference checkpoint."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "product-inference-v0"
GENERATOR = ROOT / "db" / "scripts" / "generate-product-inference-v0.py"
EXPECTED_FILES = {
    "PRODUCT_TASK_CONTRACT.json",
    "PRODUCT_CONCEPT_CANDIDATE.tsv",
    "PRODUCT_CONTEXT_PRIOR.tsv",
    "PRODUCT_QUESTION_AXIS.tsv",
    "PRODUCT_ANSWER_EFFECT.tsv",
    "PRODUCT_OUTPUT_POLICY.tsv",
    "PRODUCT_ABSTENTION_RULE.tsv",
    "PRODUCT_TASK_COVERAGE_MATRIX.tsv",
    "PRODUCT_INFERENCE_CASE.tsv",
    "PRODUCT_INFERENCE_RESULT.tsv",
    "PRODUCT_OUTPUT_EXPLANATION.tsv",
    "PRODUCT_OWNER_REVIEW_PACKET.tsv",
    "PRODUCT_OWNER_REVIEW_IMPORT_TEMPLATE.tsv",
    "PRODUCT_INFERENCE_MANIFEST.json",
    "SHA256SUMS",
}
ALLOWED_EFFECTS = {
    "supports", "weakly_supports", "contradicts", "weakly_contradicts",
    "neutral", "unknown", "insufficient_evidence",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict[str, str]:
    return {path.name: sha(path) for path in sorted(DATA.iterdir()) if path.is_file()}


def split_ids(value: str) -> list[str]:
    return [item for item in value.split("|") if item]


def main() -> int:
    require({path.name for path in DATA.iterdir() if path.is_file()} == EXPECTED_FILES, "product artifact inventory drift")
    checksum_rows = {}
    for line in (DATA / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        checksum_rows[name] = digest
    require(set(checksum_rows) == EXPECTED_FILES - {"SHA256SUMS"}, "checksum inventory incomplete")
    require(all(sha(DATA / name) == digest for name, digest in checksum_rows.items()), "checksum mismatch")
    for path in sorted(DATA.glob("*.tsv")):
        artifact_rows = rows(path.name)
        require("lineage_paths" in (artifact_rows[0] if artifact_rows else {}), f"lineage column missing: {path.name}")
        require(all(row["lineage_paths"] for row in artifact_rows), f"generated row lacks lineage: {path.name}")

    contract = json.loads((DATA / "PRODUCT_TASK_CONTRACT.json").read_text(encoding="utf-8"))
    manifest = json.loads((DATA / "PRODUCT_INFERENCE_MANIFEST.json").read_text(encoding="utf-8"))
    metrics = manifest["metrics"]
    require(contract["training_authorized"] is False and contract["training_run_count"] == 0, "training was authorized or recorded")
    require(manifest["training_authorized"] is False and metrics["training_run_count"] == 0, "manifest training state widened")
    require(manifest["scientifically_validated"] is False and manifest["product_deployment_authorized"] is False, "unsupported validation/deployment claim")
    require("probability" in contract["score_semantics"] and "uncalibrated" in contract["score_semantics"], "score semantics warning missing")
    require(contract["output_rules"]["force_fill"] is False, "output force-fill enabled")

    for relative, digest in manifest["input_hashes"].items():
        require((ROOT / relative).is_file(), f"missing lineage input: {relative}")
        require(sha(ROOT / relative) == digest, f"lineage input hash drift: {relative}")

    candidates = rows("PRODUCT_CONCEPT_CANDIDATE.tsv")
    candidate_ids = {row["canonical_concept_id"] for row in candidates}
    require(len(candidates) == 20 and len(candidate_ids) == len(candidates), "candidate inventory or uniqueness drift")
    require(all(row["display_label_en"] and row["language_label_zh_hans"] for row in candidates), "bilingual candidate label missing")
    require(all(row["canonical_concept_id"].startswith("sensory.") for row in candidates), "non-canonical candidate id")
    require(all(row["lineage_paths"] and row["explanation_references"] for row in candidates), "candidate provenance missing")
    require(all(row["product_deployment_rights_status"] == "UNKNOWN_NOT_AUTHORIZED" for row in candidates), "deployment rights fabricated")
    require(any(row["public_research_simulation_rights_eligible"] == "false" for row in candidates), "rights-blocked fixture missing")

    coverage = rows("PRODUCT_TASK_COVERAGE_MATRIX.tsv")
    cells = [row for row in coverage if row["row_kind"] == "C0_C1_CELL"]
    require(len(cells) == 56, "C0 x C1 matrix must contain 56 cells")
    require(len({row["preparation_family_key"] for row in cells}) == 8, "C0 family count drift")
    require(len({row["roast_code"] for row in cells}) == 7, "C1 level count drift")
    require(len({(row["preparation_family_key"], row["roast_code"]) for row in cells}) == 56, "duplicate or missing context cell")
    require(all(row["prior_status"] in {"weak", "neutral"} for row in cells), "unsupported joint prior status")
    require(any(row["row_kind"] == "DIMENSION_SUMMARY" and row["dimension_name"] == "language" for row in coverage), "language coverage summary missing")
    require(any(row["row_kind"] == "DIMENSION_SUMMARY" and row["dimension_name"] == "rights_status" for row in coverage), "rights coverage summary missing")

    priors = rows("PRODUCT_CONTEXT_PRIOR.tsv")
    require(len(priors) == len(candidates) * 56, "candidate context-prior matrix incomplete")
    require(all(float(row["c1_prior_adjustment"]) == 0 for row in priors), "unreviewed C1 mapping created a prior")
    require(all(abs(float(row["c0_prior_adjustment"])) <= 0.25 for row in priors), "C0 weak prior exceeded bound")
    require(all((row["prior_status"] == "neutral") == (float(row["combined_context_adjustment"]) == 0) for row in priors), "neutral prior semantics drift")
    require(all(row["source_family_ids"] == "family.vezzulli-trainedpanel-2022" for row in priors if row["prior_status"] == "weak"), "weak prior lacks direct source-local lineage")

    axes = rows("PRODUCT_QUESTION_AXIS.tsv")
    axis_by_id = {row["question_axis_id"]: row for row in axes}
    require(len(axes) == 8, "question-axis count drift")
    require(sum(row["offline_simulation_eligible"] == "true" for row in axes) == 7, "offline question eligibility drift")
    require(all(row["product_use_eligible"] == "false" for row in axes), "unvalidated question promoted to product use")
    require(all(row["divides_candidate_set"] == "true" for row in axes if row["offline_simulation_eligible"] == "true"), "eligible axis does not divide candidates")
    texture = next(row for row in axes if row["question_axis_id"] == "texture_character")
    require(texture["offline_simulation_eligible"] == "false" and texture["coverage_count"] == "0", "unsupported texture axis became eligible")

    effects = rows("PRODUCT_ANSWER_EFFECT.tsv")
    require(set(row["effect_type"] for row in effects) <= ALLOWED_EFFECTS, "invalid typed answer effect")
    require(all(row["nonmention_used_as_negative"] == "false" for row in effects), "non-mention treated as negative")
    require(all(row["structured_negative_evidence"] == "true" for row in effects if row["effect_type"] in {"contradicts", "weakly_contradicts"}), "negative effect lacks structured basis")
    require(all(row["effect_type"] == "unknown" for row in effects if row["option_id"] == "unsure"), "unsure fabricated evidence")

    cases = rows("PRODUCT_INFERENCE_CASE.tsv")
    results = rows("PRODUCT_INFERENCE_RESULT.tsv")
    require(len(cases) == 120 and len(results) == 120, "minimum 120 inference cases not met")
    case_counts = Counter(row["case_type"] for row in cases)
    require(case_counts["CONTEXT_ONLY"] == 56, "context-only case count drift")
    require(case_counts["ANSWER_UPDATE"] == 24, "answer-update case count drift")
    require(case_counts["USER_ANSWER_OVERRIDES_CONTEXT"] == 8, "override case count drift")
    require(case_counts["MISSING_CONTEXT"] == 8, "missing-context case count drift")
    require(case_counts["CONFLICTING_ANSWER"] == 8, "conflict case count drift")
    require(case_counts["OPEN_SET_UNKNOWN_EXPRESSION"] == 8, "open-set case count drift")
    require(case_counts["INSUFFICIENT_EVIDENCE_RIGHTS_BLOCKED"] == 8, "rights-blocked case count drift")
    require({row["inference_case_id"] for row in cases} == {row["inference_case_id"] for row in results}, "case/result mismatch")

    result_by_id = {row["inference_case_id"]: row for row in results}
    require(all(row["result_state"] == "NEEDS_MANDATORY_Q1" for row in results if row["case_type"] == "CONTEXT_ONLY"), "context alone created precise outputs")
    require(all(row["next_question_axis_id"] for row in results if row["case_type"] == "CONTEXT_ONLY"), "context-only path did not select an eligible Q1")
    require(all(json.loads(row["question_trace_json"]) for row in results if int(row["question_count"]) > 0), "answered question lacks a policy trace")
    for row in results:
        for trace in json.loads(row["question_trace_json"]):
            require(trace["candidate_partition_sizes"] and trace["evidence_coverage_count"] > 0, "question trace lacks partition or evidence coverage")
            require(trace["unanswered_or_unsure_path"] == "NO_EVIDENCE_CHANGE", "question trace fabricates unsure evidence")
        if row["next_question_axis_id"] and row["main_concept_ids"]:
            region = set(split_ids(row["main_concept_ids"]) + split_ids(row["secondary_concept_ids"]))
            partitions = json.loads(axis_by_id[row["next_question_axis_id"]]["candidate_partitions_json"])
            require(sum(bool(region & set(values)) for values in partitions.values()) >= 2, "next question has no remaining separation value")
    require(all(row["result_state"] == "ABSTAINED_CONFLICT" for row in results if row["case_type"] == "CONFLICTING_ANSWER"), "conflicting answers did not abstain")
    require(all(row["result_state"] == "ABSTAINED_OPEN_SET" for row in results if row["case_type"] == "OPEN_SET_UNKNOWN_EXPRESSION"), "open set did not abstain")
    require(all(row["result_state"] == "ABSTAINED_RIGHTS_BLOCKED" for row in results if row["case_type"] == "INSUFFICIENT_EVIDENCE_RIGHTS_BLOCKED"), "rights-blocked candidate escaped")
    require(all(int(row["main_output_count"]) <= 5 and int(row["secondary_output_count"]) <= 3 for row in results), "output limit exceeded")
    require(any(int(row["main_output_count"]) < 5 for row in results), "fewer-than-five behavior untested")
    require(any(int(row["secondary_output_count"]) == 0 for row in results), "zero-secondary behavior untested")
    require(any(row["override_observed"] == "true" for row in results if row["case_type"] == "USER_ANSWER_OVERRIDES_CONTEXT"), "explicit answer did not override a weak prior")
    require(all(row["decision_score_semantics"].endswith("NOT_PROBABILITY") for row in results), "decision score mislabeled")

    rights = {row["canonical_concept_id"]: row["public_research_simulation_rights_eligible"] == "true" for row in candidates}
    redundancy = {row["canonical_concept_id"]: row["redundancy_group"] for row in candidates}
    for result in results:
        outputs = split_ids(result["main_concept_ids"]) + split_ids(result["secondary_concept_ids"])
        require(len(outputs) == len(set(outputs)), f"exact alias duplicate in {result['inference_case_id']}")
        require(len({redundancy[concept] for concept in outputs}) == len(outputs), f"near duplicate group in {result['inference_case_id']}")
        require(all(rights[concept] for concept in outputs), f"rights leak in {result['inference_case_id']}")
        require(all(concept in candidate_ids for concept in outputs), f"unknown output concept in {result['inference_case_id']}")

    explanations = rows("PRODUCT_OUTPUT_EXPLANATION.tsv")
    expected_explanations = sum(int(row["main_output_count"]) + int(row["secondary_output_count"]) for row in results)
    require(len(explanations) == expected_explanations, "output explanation count mismatch")
    require(all(row["lineage_paths"] and row["human_readable_explanation"] for row in explanations), "explanation provenance missing")
    require(all(row["review_state"] != "REVIEW_REQUIRED_RELATION_ONLY" for row in explanations if row["output_tier"] == "main"), "review-only relation promoted to main")

    packet = rows("PRODUCT_OWNER_REVIEW_PACKET.tsv")
    imports = rows("PRODUCT_OWNER_REVIEW_IMPORT_TEMPLATE.tsv")
    require(len(packet) == 100 and len(imports) == 100, "owner review packet size drift")
    required_review_categories = {
        "MAIN_SECONDARY_BOUNDARY", "AMBIGUOUS_CROSS_FORM_MAPPING", "CONTEXT_PRIOR_DISAGREEMENT",
        "QUESTION_AXIS_PARTITION", "REDUNDANT_OUTPUT_PAIR", "CONFLICTING_EVIDENCE", "OPEN_SET_CASE",
        "RIGHTS_SENSITIVE_CASE", "SOURCE_FAMILY_DOMINANCE", "REVIEW_REQUIRED_RANKING_EFFECT",
    }
    require({row["review_category"] for row in packet} == required_review_categories, "owner review category coverage drift")
    require(all(not row["owner_decision"] and not row["owner_rationale"] and not row["reviewer"] and not row["review_date"] for row in packet), "owner decision fabricated")
    require(all(not row["decision"] and not row["output_tier"] and not row["answer_effect"] and not row["rationale"] for row in imports), "review import decision fabricated")
    require(all(row["decision_allowed_values"] == "approve|reject|revise|defer" for row in imports), "owner decision vocabulary missing")

    sensitivity = manifest["sensitivity_analysis"]
    required_variants = {
        "without_direct_evidence", "without_effective_record", "without_source_diversity",
        "without_governed_normalization", "without_governed_semantic", "without_structured_contrast",
        "without_c0_prior", "without_c1_prior", "without_review_required_exploration",
        "without_redundancy", "without_positive_answer_weights", "without_contradiction_weights",
    }
    require(set(sensitivity) == required_variants, "sensitivity variant inventory drift")
    require(all(isinstance(row["output_changed_case_count"], int) for row in sensitivity.values()), "sensitivity analysis is not computed")
    require(sensitivity["without_c1_prior"]["output_changed_case_count"] == 0, "neutral C1 ablation changed output")
    require(sensitivity["without_review_required_exploration"]["output_changed_case_count"] == 0, "exploratory relation affected primary policy")
    require(sensitivity["without_redundancy"]["duplicate_redundancy_group_pressure_count"] > 0, "redundancy ablation did not expose duplicate pressure")

    acquisition = manifest["bounded_acquisition_review"]
    require(acquisition["reviewed_candidate_count"] == 30 and len(acquisition["candidates"]) == 30, "bounded acquisition review count drift")
    require(acquisition["reviewed_candidate_count"] <= 30, "bounded acquisition candidate cap exceeded")
    require(acquisition["imported_dataset_count"] == 0 and acquisition["new_effective_structured_observation_count"] == 0, "unapproved structured evidence imported")
    require(all(row["exact_product_gap"] and row["round3n_import_decision"] and row["decision_reason"] for row in acquisition["candidates"]), "acquisition candidate lacks product-gap decision")
    require(all(not row["round3n_import_decision"].startswith("IMPORT") for row in acquisition["candidates"]), "consumer or unreviewed evidence imported")

    forbidden_suffixes = {".ckpt", ".joblib", ".onnx", ".pkl", ".pt", ".pth", ".safetensors", ".tflite"}
    require(not any(path.suffix.lower() in forbidden_suffixes for path in DATA.rglob("*")), "model artifact persisted")
    require(metrics["rights_leak_count"] == 0 and metrics["provenance_missing_count"] == 0 and metrics["explanation_missing_count"] == 0, "manifest governance metric failed")

    before = snapshot()
    completed = subprocess.run([sys.executable, "-B", str(GENERATOR)], cwd=ROOT, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        print(completed.stdout, file=sys.stderr)
        print(completed.stderr, file=sys.stderr)
        completed.check_returncode()
    require(before == snapshot(), "product artifact generation is not byte-identical")

    print("PRODUCT_INFERENCE_V0_CONTRACT_PASS=true")
    print("PRODUCT_NEGATIVE_TEST_PASS=true")
    print("PRODUCT_BYTE_REPRODUCIBILITY_PASS=true")
    print("PRODUCT_PUBLIC_SAFE_PASS=true")
    print(f"INFERENCE_CASE_COUNT={len(cases)}")
    print("TRAINING_RUN_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
