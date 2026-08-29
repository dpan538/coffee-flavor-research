#!/usr/bin/env python3
"""Fail-closed checks for the rolling public-safe descriptor data package."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "current"
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


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict[str, str]:
    return {path.name: sha(path) for path in sorted(DATA.iterdir()) if path.is_file()}


def main() -> None:
    check(EXPECTED_FILES == {path.name for path in DATA.iterdir() if path.is_file()}, "current output inventory drift")

    listed = {}
    for line in (DATA / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[name] = digest
    check(set(listed) == EXPECTED_FILES - {"SHA256SUMS"}, "SHA256SUMS inventory mismatch")
    for name, digest in listed.items():
        check(sha(DATA / name) == digest, f"SHA mismatch: {name}")

    manifest = json.loads((DATA / "CURRENT_DATA_MANIFEST.json").read_text(encoding="utf-8"))
    check(manifest["baseline_main_sha"] == "21d04f50952ac30ee13010ee26bae8a224ea9f71", "baseline SHA drift")
    check(manifest["round4a_source_sha"] == "48ff0a921db4da98b2802c60bc23ee031687175b", "Round 4A SHA drift")
    check(manifest["round4a_product_files_imported"] == 0, "Round 4A product scope imported")
    check(manifest["descriptor_census_machine_bundle_available"] is False, "missing machine bundle claimed available")
    check(manifest["schema_changed"] is False and manifest["new_migration_count"] == 0, "schema change claimed")
    check(manifest["model_training_run"] is False and manifest["model_weight_file_count"] == 0, "model training claimed")

    inventory = rows("DATASET_INVENTORY.tsv")
    check(len(inventory) == 32, "dataset inventory count drift")
    role_counts = Counter(row["data_role"] for row in inventory)
    check(role_counts == Counter(manifest["dataset_role_counts"]), "dataset-role totals do not reconcile")
    external = next(row for row in inventory if row["dataset_id"] == "round3-external-descriptor-receipt")
    check(external["data_role"] == "AGGREGATE_RECEIPT_ONLY", "external receipt promoted to row-level data")
    check(external["current_disposition"] == "COUNTS_ONLY_NO_ROW_LEVEL_IMPORT", "external report rows reconstructed")
    round4a = [row for row in inventory if row["source_round_or_batch"] == "ROUND4A_DATA_HEALTH"]
    check(len(round4a) == 15, "Round 4A inspected-file count drift")
    check(all(row["source_commit_sha"] == manifest["round4a_source_sha"] for row in round4a), "Round 4A lineage SHA missing")

    ledger = rows("CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    check(len(ledger) == 158, "raw segmented ledger count drift")
    check(sum(row["counts_as_assertion"] == "true" for row in ledger) == 157, "assertion de-inflation drift")
    check(sum(row["counts_as_record_unique_descriptor"] == "true" for row in ledger) == 155, "record-unique de-inflation drift")
    deinf = [row for row in ledger if row["counts_as_assertion"] == "true"]
    classes = Counter(row["descriptor_class"] for row in deinf)
    tiers = Counter(row["evidence_tier"] for row in deinf)
    rights = Counter(row["rights_state"] for row in deinf)
    check(classes == Counter({"STRICT_FLAVOR": 96, "BROAD_SENSORY": 61}), "descriptor-class totals drift")
    check(tiers == Counter({"P2": 73, "UNRESOLVED": 84}), "evidence-tier totals drift")
    check(rights == Counter({"PENDING": 73, "UNKNOWN": 84}), "rights totals drift")
    check(len({row["effective_record_id"] for row in deinf}) == 9, "effective-record count drift")
    check(len({row["edition_year"] for row in deinf}) == 4, "edition-year count drift")
    check(len({row["source_family_id"] for row in deinf}) == 1, "source-family count drift")
    check(not any(row["normalized_descriptor_candidate_id"] for row in ledger), "unreviewed normalization mapping entered current ledger")
    check(not any(row["model_eligible"] == "true" for row in ledger), "model-eligible assertion leaked into current ledger")
    check(all(row["raw_source_text_or_restricted_pointer"].startswith(("hash:sha256:", "restricted:")) for row in ledger), "raw descriptor text or invalid pointer in public ledger")
    check(all(row["atomic_source_text_or_restricted_pointer"].startswith("hash:sha256:") for row in ledger), "atomic source text leaked into public ledger")
    check(all(row["source_native_lexical_form_or_restricted_pointer"].startswith("hash:sha256:") for row in ledger), "source-native lexical text leaked into public ledger")

    new_rows = [row for row in ledger if row["source_dataset_id"] == "current-targeted-acquisition-hash-ledger"]
    check(len(new_rows) == 18, "targeted acquisition assertion count drift")
    check(Counter(row["descriptor_class"] for row in new_rows) == Counter({"STRICT_FLAVOR": 11, "BROAD_SENSORY": 7}), "new assertion class totals drift")
    check(all(row["evidence_stratum"] == "C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED" for row in new_rows), "new official-field row escaped quarantine")
    check(all(row["rights_state"] == "UNKNOWN" for row in new_rows), "new rights state widened")

    merge = {row["metric"]: row["observed_value"] for row in rows("DESCRIPTOR_MERGE_RECEIPT.tsv")}
    check(merge["RAW_SEGMENTED_DESCRIPTOR_ASSERTION_COUNT"] == "158", "merge raw count drift")
    check(merge["ASSERTION_LEVEL_DEINFLATED_COUNT"] == "157", "merge assertion count drift")
    check(merge["EFFECTIVE_RECORD_LEVEL_UNIQUE_DESCRIPTOR_COUNT"] == "155", "merge record-unique count drift")
    check(merge["PAIR_EDGE_EVENT_COUNT"] == "661", "pair event count drift")
    check(merge["UNIQUE_SUPPORTED_PAIR_COUNT"] == "659", "unique pair count drift")
    check(merge["REVIEWED_NORMALIZED_DESCRIPTOR_FORM_COUNT"] == "0", "normalized label inflation")

    overlap = rows("DESCRIPTOR_OVERLAP_MAP.tsv")
    check(any(row["overlap_decision"] == "EXACT_DERIVED_SUBSET" and row["right_dataset"] == "ROUND4A_DERIVED_GRAPH" for row in overlap), "Round 4A overlap decision absent")
    duplicates = {row["duplicate_type"]: row for row in rows("DESCRIPTOR_DUPLICATE_RECEIPT.tsv")}
    check(duplicates["ROUND4A_DERIVED_PAIR_VIEW"]["count"] == "508", "Round 4A pair view count drift")
    check(duplicates["ROUND4A_DERIVED_PAIR_VIEW"]["count_surface"] == "PAIR_EVENT", "pair events treated as records")

    check(len(rows("DESCRIPTOR_DISTRIBUTION.tsv")) == 0, "fabricated normalized descriptor distribution")
    support = rows("DESCRIPTOR_SUPPORT_BANDS.tsv")
    check(len(support) == 64 and all(row["descriptor_count"] == "0" for row in support), "support bands inflated")

    acquisition = rows("TARGETED_ACQUISITION_RESULT.tsv")
    check(len(acquisition) == 3, "target route count drift")
    check(sum(int(row["artifacts_inspected"]) for row in acquisition) == 4, "target artifact count drift")
    check(sum(int(row["effective_records"]) for row in acquisition) == 1, "new effective-record count drift")
    check(acquisition[-1]["stop_condition"] == "SECOND_CONSECUTIVE_ZERO_YIELD_STRATUM_STOP", "bounded stop condition absent")

    strictness = rows("STRICTNESS_IMPACT_LOG.tsv")
    check(len(strictness) == 1, "strictness impact count drift")
    check(strictness[0]["recommended_action"] == "REQUEST_ORGANIZER_PROVENANCE", "strictness recommendation widened rules")
    check(strictness[0]["user_decision_required"] == "true", "strictness decision not surfaced")

    review = rows("REVIEW_QUEUE_RECEIPT.tsv")
    check(len(review) == 157 and len(review) <= 200, "review packet size drift")
    check(all(not row["reviewer_decision"] and not row["reviewer_reason"] for row in review), "fabricated reviewer decision")

    gates = rows("TRAINING_GATE_STATUS.tsv")
    summaries = [row for row in gates if row["criterion"] == "ALL_CRITERIA"]
    check(len(summaries) == 5 and all(row["pass"] == "false" for row in summaries), "training gate passed unexpectedly")
    check(manifest["final_data_decision"] == "MERGE_COMPLETE_STRICTNESS_POLICY_REVIEW_REQUIRED", "final data decision drift")

    forbidden_suffixes = {".ckpt", ".joblib", ".onnx", ".pkl", ".pt", ".pth", ".safetensors", ".tflite"}
    check(not any(path.suffix.lower() in forbidden_suffixes for path in DATA.rglob("*")), "model weight persisted")

    before = snapshot()
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    check(before == snapshot(), "generator is not deterministic")

    print("CURRENT_DESCRIPTOR_DATA_CONTRACT_PASS=true")
    print("DATASET_INVENTORY_COUNT=32")
    print("MERGED_ASSERTION_LEVEL_DEINFLATED_COUNT=157")
    print("MERGED_DESCRIPTOR_BEARING_EFFECTIVE_RECORD_COUNT=9")
    print("TARGETED_ACQUISITION_NEW_RECORD_COUNT=1")
    print("MODEL_ELIGIBLE_ASSERTION_COUNT=0")


if __name__ == "__main__":
    main()
