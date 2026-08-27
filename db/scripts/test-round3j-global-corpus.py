#!/usr/bin/env python3
"""Offline negative and artifact-contract tests for the global checkpoint."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "round3j"
GLOBAL = DATA / "global-corpus"


def read_tsv(name: str) -> list[dict[str, str]]:
    with (GLOBAL / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(name: str, condition: bool) -> None:
    if not condition:
        raise SystemExit(f"FAIL {name}")
    print(f"PASS {name}")


documents = read_tsv("ADMITTED_FLAVOR_DOCUMENT.tsv")
occurrences = read_tsv("ADMITTED_FLAVOR_EXPRESSION_OCCURRENCE.tsv")
coverage = read_tsv("SOURCE_CLASS_CANDIDATE_COVERAGE.tsv")
saturation = read_tsv("SOURCE_CLASS_SATURATION.tsv")
pilots = read_tsv("OPEN_SOURCE_YIELD_PILOT.tsv")
options = read_tsv("HIGH_YIELD_PERMISSION_AND_LICENSE_OPTION.tsv")
batches = read_tsv("GLOBAL_ACQUISITION_BATCH.tsv")
metrics = {row["metric"]: row["value"] for row in read_tsv("GLOBAL_FLAVOR_CORPUS_METRIC.tsv")}

expected = (DATA / "global_flavor_acquisition_expected_state.tsv").read_text(encoding="utf-8")
seed_text = (DATA / "global_flavor_source_candidate_register.tsv").read_text(encoding="utf-8")

check("regional_quota_does_not_block_global_acquisition", "state.regional_acquisition_blocking_gate\tfalse\tfalse\tfalse" in expected)
check("candidate_count_is_not_admitted_source_count", len(coverage) > int(metrics["NEW_ADMITTED_SOURCE_COUNT"]))
check("request_dossier_is_not_acquired_data", all("dossier" not in row["source_key"].casefold() for row in documents))
check("public_webpage_is_not_training_permission", all(row["rights_state"] == "CLEARED" for row in documents))
check("mirror_is_not_independent_family", any(row["counts_toward_coverage_gate"] == "false" for row in coverage))
check("scraper_code_license_is_not_upstream_license", "SCRAPER_CODE_LICENSE_DOES_NOT_LICENSE_UPSTREAM_CONTENT" in seed_text)
check("lightyear_scraping_is_prohibited", any(row["candidate_key"] == "lightyear-coffee-index" and row["disposition"] == "PERMISSION_REQUEST_READY" for row in options))
check("forum_content_requires_permission", not any(row["evidence_register"] == "PERMISSIONED_COMMUNITY_FLAVOR_DOCUMENT" for row in documents))
check("machine_translation_is_not_observed_data", all(row["machine_translated"] == "false" and row["project_translation"] == "false" for row in occurrences))
check("project_paraphrase_is_not_source_expression", all(row["source_authored"] == "true" for row in occurrences))
check("product_title_alone_is_not_flavor_document", all(any(item["document_key"] == row["document_key"] for item in occurrences) for row in documents))
check("marketing_slogan_is_not_sensory_description", all(row["expression_role"] != "OUT_OF_SCOPE" for row in occurrences))
check("raw_product_row_is_not_effective_unit", all(row["result"] != "ADMIT_RAW_AND_DERIVED" or int(row["qualifying_flavor_documents"]) > 0 for row in pilots))
check("snapshot_repeat_is_detected", all(row["duplicate_reason"] for row in occurrences))
check("catalog_mirror_is_not_independent", len({row["upstream_source_family_key"] for row in coverage if row["counts_toward_coverage_gate"] == "true"}) == sum(row["counts_toward_coverage_gate"] == "true" for row in coverage))
check("unreviewed_expression_is_not_gold", all(row["review_state"] == "SOURCE_REVIEWED" for row in occurrences))
check("unresolved_expression_has_no_forced_target", all(row["label_disposition"] != "UNRESOLVED" or row["candidate_target_keys"] == "[]" for row in occurrences))
check("preference_is_not_flavor_descriptor", all(row["preference_evidence"] == "false" for row in occurrences))
check("sensory_registers_are_not_silently_pooled", {row["evidence_register"] for row in documents} == {"AUTHOR_TASTING_PROSE", "CONSUMER_STRUCTURED_SENSORY"})
check("openfoodfacts_share_alike_is_recorded", "SHARE_ALIKE_PARTITION_AND_ATTRIBUTION_REQUIRED" in seed_text)
check("cc_by_nc_is_not_unrestricted_admission", all("NC" not in row["license_expression"] for row in documents))
check("commercial_purchase_requires_authorization", all(row["user_authorization_required"] == "true" for row in options))
check("evaluation_benchmark_is_not_observed_training_data", all("flavorreasonbench" not in row["source_key"].casefold() for row in documents))
check("global_acquisition_is_not_closed_with_unreviewed_class", len(saturation) == 9 and all(row["closure_state"] != "CLOSED" for row in saturation))
check("round3_exit_is_false_without_scale_gain", int(metrics["TOTAL_ADMITTED_FLAVOR_DOCUMENT_COUNT"]) < 10000)

model_suffixes = {".onnx", ".pt", ".pth", ".safetensors", ".ckpt", ".npy", ".npz"}
model_names = {"TRAINING_CORPUS_MANIFEST.json", "EMBEDDING_MANIFEST.json"}
created_paths = [path for path in DATA.rglob("*") if path.is_file() and (path.suffix.casefold() in model_suffixes or path.name in model_names)]
check("no_model_or_embedding_artifact_created", not created_paths)

with (GLOBAL / "GLOBAL_ACQUISITION_MANIFEST.json").open(encoding="utf-8") as handle:
    manifest = json.load(handle)
check("manifest_declares_partial_no_training", manifest["phase_status"] == "ROUND3J_PARTIAL_GLOBAL_SCALEUP" and not manifest["model_training_authorized"])
check("manifest_artifact_hashes_match", all(sha256(ROOT / item["path"]) == item["sha256"] for item in manifest["artifacts"]))
check("source_file_hashes_match", all(sha256(ROOT / row["source_file_path"]) == row["source_file_sha256"] for row in documents))

print("ROUND3J_GLOBAL_NEGATIVE_TEST_COUNT=29")
