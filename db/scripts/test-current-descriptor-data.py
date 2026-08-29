#!/usr/bin/env python3
"""Fail-closed checks for the rolling public-safe descriptor data package."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "current"
STAGING = ROOT / "db" / "data" / "professional-descriptor-staging"
GENERATOR = ROOT / "db" / "scripts" / "generate-current-descriptor-data.py"

EXPECTED_FILES = {
    "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv",
    "CURRENT_DATA_MANIFEST.json",
    "DATASET_INVENTORY.tsv",
    "DATASET_ROLE_AND_LINEAGE.tsv",
    "DESCRIPTOR_DISTRIBUTION.tsv",
    "DESCRIPTOR_DUPLICATE_RECEIPT.tsv",
    "DESCRIPTOR_GAP_MATRIX.tsv",
    "DESCRIPTOR_MERGE_RECEIPT.tsv",
    "DESCRIPTOR_OVERLAP_MAP.tsv",
    "DESCRIPTOR_PREPARATION_DISTRIBUTION.tsv",
    "DESCRIPTOR_REVIEW_DISTRIBUTION.tsv",
    "DESCRIPTOR_RIGHTS_DISTRIBUTION.tsv",
    "DESCRIPTOR_ROAST_EVIDENCE_DISTRIBUTION.tsv",
    "DESCRIPTOR_SOURCE_FAMILY_DISTRIBUTION.tsv",
    "DESCRIPTOR_SUPPORT_BANDS.tsv",
    "DESCRIPTOR_YEAR_DISTRIBUTION.tsv",
    "REVIEW_QUEUE_RECEIPT.tsv",
    "SHA256SUMS",
    "STRICTNESS_IMPACT_LOG.tsv",
    "TARGETED_ACQUISITION_QUEUE.tsv",
    "TARGETED_ACQUISITION_RESULT.tsv",
    "TRAINING_GATE_STATUS.tsv",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def current_rows(name: str) -> list[dict[str, str]]:
    return rows(DATA / name)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict[str, str]:
    return {path.name: sha(path) for path in sorted(DATA.iterdir()) if path.is_file()}


def bool_count(values: list[dict[str, str]], field: str) -> int:
    return sum(row[field] == "true" for row in values)


def main() -> None:
    check(
        EXPECTED_FILES == {path.name for path in DATA.iterdir() if path.is_file()},
        "current output inventory drift",
    )
    listed = {}
    for line in (DATA / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[name] = digest
    check(set(listed) == EXPECTED_FILES - {"SHA256SUMS"}, "SHA256SUMS inventory mismatch")
    for name, digest in listed.items():
        check(sha(DATA / name) == digest, f"SHA mismatch: {name}")

    manifest = json.loads((DATA / "CURRENT_DATA_MANIFEST.json").read_text(encoding="utf-8"))
    metrics = manifest["metrics"]
    check(manifest["baseline_main_sha"] == "21d04f50952ac30ee13010ee26bae8a224ea9f71", "baseline SHA drift")
    check(manifest["round4a_product_files_imported"] == 0, "Round 4A product scope imported")
    check(manifest["schema_changed"] is False and manifest["new_migration_count"] == 0, "schema change claimed")
    check(manifest["model_training_run"] is False and manifest["model_weight_file_count"] == 0, "model training claimed")
    check(manifest["phase_status"] == "CANDIDATE_CORPUS_20000_REACHED_DISTRIBUTION_GAPS", "20k hard stop absent")

    inventory = current_rows("DATASET_INVENTORY.tsv")
    check(len(inventory) == manifest["dataset_inventory_count"], "dataset inventory count drift")
    check(Counter(row["data_role"] for row in inventory) == Counter(manifest["dataset_role_counts"]), "dataset role reconciliation failed")
    external = next(row for row in inventory if row["dataset_id"] == "round3-external-descriptor-receipt")
    check(external["data_role"] == "AGGREGATE_RECEIPT_ONLY", "external report promoted to rows")
    batch2 = next(row for row in inventory if row["dataset_id"] == "professional-descriptor-scaleup-batch2-public-safe")
    check(batch2["data_role"] == "ROW_LEVEL_PRIMARY_PUBLIC_SAFE", "Batch 2 sidecar role drift")

    ledger = current_rows("CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    deinf = [row for row in ledger if row["counts_as_assertion"] == "true"]
    record_unique = [row for row in ledger if row["counts_as_record_unique_descriptor"] == "true"]
    check(len(ledger) == metrics["raw_segmented"], "raw segmented count drift")
    check(len(deinf) == metrics["assertion_deinflated"], "assertion de-inflation drift")
    check(len(record_unique) == metrics["record_unique"], "record-unique count drift")
    check(len(deinf) >= 20_000, "hard stop count not reached")
    check(len({row["descriptor_assertion_id"] for row in ledger}) == len(ledger), "assertion IDs not unique")
    check(len({row["effective_record_id"] for row in deinf}) == metrics["effective_records"], "effective record count drift")
    check(len({row["source_family_id"] for row in deinf}) == metrics["source_families"], "source family count drift")
    check(metrics["source_families"] >= 5, "positive source-family floor missed")
    check(metrics["provisional_mapping_coverage_rate"] >= 0.80, "provisional mapping coverage below 80%")
    check(metrics["model_eligible"] == 0, "model-eligible rows widened")
    check(not any(row["model_eligible"] == "true" for row in ledger), "model-eligible assertion leaked")
    check(all(row["raw_source_text_or_restricted_pointer"].startswith(("hash:sha256:", "restricted:")) for row in ledger), "raw source text leaked")
    check(all(row["atomic_source_text_or_restricted_pointer"].startswith("hash:sha256:") for row in ledger), "atomic source text leaked")
    check(all(row["source_native_lexical_form_or_restricted_pointer"].startswith("hash:sha256:") for row in ledger), "source-native text leaked")

    classes = Counter(row["descriptor_class"] for row in deinf)
    tiers = Counter(row["evidence_tier"] for row in deinf)
    rights = Counter(row["rights_state"] for row in deinf)
    check(classes["STRICT_FLAVOR"] == metrics["strict"] and classes["BROAD_SENSORY"] == metrics["broad"], "class totals drift")
    check(tiers["P1"] == metrics["p1"] and tiers["P2"] == metrics["p2"], "P1/P2 totals drift")
    check(tiers["P4"] == metrics["p4"] and tiers["UNRESOLVED"] == metrics["unresolved"], "auxiliary/unresolved totals drift")
    check(rights["AFFIRMATIVE"] == metrics["rights_affirmative"], "affirmative rights drift")
    check(rights["PENDING"] == metrics["rights_pending"] and rights["UNKNOWN"] == metrics["rights_unknown"], "blocked rights drift")

    sidecar = rows(STAGING / "PUBLIC_SAFE_ASSERTION_SIDECAR.tsv")
    batch2_rows = [row for row in ledger if row["source_dataset_id"] == "professional-descriptor-scaleup-batch2-public-safe"]
    check(len(batch2_rows) == len(sidecar), "Batch 2 ledger import row drift")
    check(all(row["provisional_normalized_form_id"] for row in sidecar), "missing provisional mapping")
    check(all(row["human_reviewed"] == "false" and row["model_eligible"] == "false" for row in sidecar), "sidecar review/model state widened")
    overlap = [row for row in sidecar if row["source_url"].endswith("2009-brazil-pulped-naturals-84-96/")]
    check(len(overlap) == 18 and not any(row["counts_as_assertion"] == "true" for row in overlap), "cross-batch publication overlap not de-inflated")

    merge = {row["metric"]: row["observed_value"] for row in current_rows("DESCRIPTOR_MERGE_RECEIPT.tsv")}
    check(int(merge["ASSERTION_LEVEL_DEINFLATED_COUNT"]) == len(deinf), "merge receipt count drift")
    check(int(merge["PROVISIONAL_NORMALIZED_DESCRIPTOR_FORM_COUNT"]) == metrics["normalized_forms"], "provisional form count drift")
    check(int(merge["MODEL_ELIGIBLE_ASSERTION_COUNT"]) == 0, "merge receipt model eligibility drift")
    check(int(merge["PROVISIONAL_NORMALIZED_PAIR_EVENT_COUNT"]) == metrics["provisional_normalized_pair_event_count"], "pair event count drift")

    distribution = current_rows("DESCRIPTOR_DISTRIBUTION.tsv")
    all_distribution = [row for row in distribution if row["corpus_view"] == "ALL_PROFESSIONAL_CANDIDATES"]
    check(len(all_distribution) == metrics["normalized_forms"], "descriptor distribution form count drift")
    support = current_rows("DESCRIPTOR_SUPPORT_BANDS.tsv")
    all_support = [row for row in support if row["corpus_view"] == "ALL_PROFESSIONAL_CANDIDATES"]
    check(sum(int(row["descriptor_count"]) for row in all_support) == metrics["normalized_forms"], "support bands do not reconcile")

    route_manifest = json.loads((STAGING / "BATCH2_PUBLIC_MANIFEST.json").read_text(encoding="utf-8"))
    acquisition = current_rows("TARGETED_ACQUISITION_RESULT.tsv")
    check(len(acquisition) == route_manifest["source_route_count_inspected"], "source route count drift")
    check(route_manifest["artifact_count"] <= 2000, "artifact cap exceeded")
    check(route_manifest["positive_source_family_count"] >= 5, "positive source family requirement missed")
    check(route_manifest["cross_batch_publication_layer_duplicate_losses"] == 18, "cross-batch duplicate receipt drift")
    check(route_manifest["automated_live_acquisition_runtime_seconds"] == 1057.548111, "observed live runtime drift")
    check(len(route_manifest["files"]) == 4, "Batch 2 manifest file inventory drift")

    review = current_rows("REVIEW_QUEUE_RECEIPT.tsv")
    check(len(review) == min(metrics["normalized_forms"], 200), "active cluster review packet size drift")
    check(all(not row["reviewer_decision"] and not row["reviewer_reason"] for row in review), "fabricated reviewer decision")
    strictness = current_rows("STRICTNESS_IMPACT_LOG.tsv")
    check(strictness[0]["recommended_action"].startswith("KEEP_AS_SILVER_CANDIDATE"), "strictness widened official-field evidence")
    check(strictness[0]["user_decision_required"] == "false", "already-authorized collection policy marked blocked")

    gates = current_rows("TRAINING_GATE_STATUS.tsv")
    summaries = [row for row in gates if row["criterion"] == "ALL_CRITERIA"]
    check(len(summaries) == 5 and all(row["pass"] == "false" for row in summaries), "training gate passed unexpectedly")
    hard_stop_volume = next(row for row in gates if row["gate_id"] == "GATE_20000_RESEARCH_RANKING" and row["criterion"] == "candidate_corpus_assertions")
    check(hard_stop_volume["pass"] == "true", "20k candidate volume gate not recorded")

    milestone = json.loads((STAGING / "CANDIDATE_MILESTONE_10000.json").read_text(encoding="utf-8"))
    check(milestone["milestone_assertion_count"] >= 10_000, "10k milestone receipt missing")
    check(milestone["stop_at_10000"] is False and milestone["continue_after_10000"] is True, "runtime amendment missing")
    reconciliation = json.loads((STAGING / "CANDIDATE_MILESTONE_10000_RECONCILIATION.json").read_text(encoding="utf-8"))
    check(reconciliation["original_milestone_receipt_sha256"] == sha(STAGING / "CANDIDATE_MILESTONE_10000.json"), "milestone lineage hash drift")
    check(reconciliation["merged_count_at_original_cursor"] == 9988, "original cursor reconciliation drift")
    check(reconciliation["corrected_first_complete_record_boundary_count"] == 10009, "corrected 10k boundary drift")
    check(reconciliation["corrected_exact_continuation_cursor"].startswith("detail-index=307;"), "corrected continuation cursor drift")

    forbidden_suffixes = {".ckpt", ".joblib", ".onnx", ".pkl", ".pt", ".pth", ".safetensors", ".tflite"}
    check(not any(path.suffix.lower() in forbidden_suffixes for path in DATA.rglob("*")), "model weight persisted")

    before = snapshot()
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    check(before == snapshot(), "generator is not deterministic")

    print("CURRENT_DESCRIPTOR_DATA_CONTRACT_PASS=true")
    print(f"MERGED_ASSERTION_LEVEL_DEINFLATED_COUNT={metrics['assertion_deinflated']}")
    print(f"MERGED_DESCRIPTOR_BEARING_EFFECTIVE_RECORD_COUNT={metrics['effective_records']}")
    print(f"PROVISIONAL_MAPPING_COVERAGE_RATE={metrics['provisional_mapping_coverage_rate']:.6f}")
    print("MODEL_ELIGIBLE_ASSERTION_COUNT=0")


if __name__ == "__main__":
    main()
