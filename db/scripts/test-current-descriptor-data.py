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
CLEANING_STAGING = ROOT / "db" / "data" / "candidate-cleaning-staging"
GENERATOR = ROOT / "db" / "scripts" / "generate-current-descriptor-data.py"
BATCH4_GENERATOR = ROOT / "db" / "scripts" / "generate-batch4-cleaned-30k.py"
BATCH6_GENERATOR = ROOT / "db" / "scripts" / "generate-batch6-semantic-corpus.py"
BATCH7_RUNNER = ROOT / "db" / "scripts" / "descriptor-pipeline.py"

EXPECTED_FILES = {
    "BATCH7_SEMANTIC_MANIFEST.json",
    "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv",
    "CANDIDATE_20K_SNAPSHOT_MANIFEST.json",
    "CANDIDATE_30K_SNAPSHOT_MANIFEST.json",
    "CANDIDATE_40K_SNAPSHOT_MANIFEST.json",
    "CANDIDATE_50K_SNAPSHOT_MANIFEST.json",
    "CANONICAL_NORMALIZATION_MAP.tsv",
    "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv",
    "CLEANED_30K_PAIR_EVENT_RECEIPT.tsv",
    "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv",
    "CLEANED_40K_MANIFEST.json",
    "CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv",
    "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv",
    "CLEANED_50K_MANIFEST.json",
    "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv",
    "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv",
    "CLEANED_DESCRIPTOR_ASSERTION_LEDGER.tsv",
    "CLEANED_DESCRIPTOR_DISTRIBUTION.tsv",
    "CLEANED_DESCRIPTOR_SUPPORT_BANDS.tsv",
    "CLEANED_PAIR_EVENT_RECEIPT.tsv",
    "CLEANER_V1_V2_DELTA.tsv",
    "COE_CROSS_DOMAIN_DUPLICATE_DECISION.tsv",
    "COE_ENTITY_RESOLUTION.tsv",
    "COE_ENTITY_RESOLUTION_V2.tsv",
    "CONCEPT_CLUSTER.tsv",
    "CONCEPT_CLUSTER_V2.tsv",
    "COMPOUND_COMPONENT.tsv",
    "COMPOUND_MODIFIER_BENCHMARK.tsv",
    "CURRENT_DATA_MANIFEST.json",
    "CROSS_FAMILY_SHARED_TARGET_BENCHMARK.tsv",
    "CROSS_FORM_BENCHMARK_CANDIDATE.tsv",
    "CROSS_FORM_BENCHMARK_GROUP.tsv",
    "CROSS_FORM_BENCHMARK_LEAKAGE_AUDIT.tsv",
    "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json",
    "CROSS_FORM_OWNER_REVIEW_IMPORT_TEMPLATE.tsv",
    "CROSS_FORM_OWNER_REVIEW_PACKET.tsv",
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
    "GROUPED_SPLIT_FEASIBILITY.tsv",
    "GROUPED_SPLIT_GROUPS.tsv",
    "GROUPED_SPLIT_LEAKAGE_AUDIT.tsv",
    "HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv",
    "HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv",
    "MACHINE_GOVERNED_MAPPING.tsv",
    "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json",
    "ONTOLOGY_CONSOLIDATION_MAP.tsv",
    "ONTOLOGY_CONSOLIDATION_V2.tsv",
    "ONTOLOGY_GAP_REGISTER.tsv",
    "ONTOLOGY_GAP_REGISTER_V1_20K.tsv",
    "PAIR_EVENT_CONTRIBUTION_DISTRIBUTION.tsv",
    "MODIFIER_COMPONENT.tsv",
    "OPEN_SET_UNSEEN_TARGET_BENCHMARK.tsv",
    "POST20K_EXTENSION_PROGRESS.tsv",
    "PROJECT_OWNER_REVIEW_IMPORT_TEMPLATE.tsv",
    "PROJECT_OWNER_REVIEW_PACKET.tsv",
    "PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv",
    "REVIEW_CLUSTER_QUEUE.tsv",
    "REVIEW_QUEUE_RECEIPT.tsv",
    "RIGHTS_PROPAGATION_RECEIPT.tsv",
    "SEGMENTATION_DECISION.tsv",
    "SEMANTIC_AUDIT_METRICS.json",
    "SEMANTIC_CLEANING_DECISION.tsv",
    "SEMANTIC_CLEANING_V2_DECISION.tsv",
    "SEMANTIC_CONCEPT_NODE.tsv",
    "SEMANTIC_FORM_NODE.tsv",
    "SEMANTIC_NOVELTY_DISTRIBUTION.tsv",
    "SEMANTIC_REFERENCE_SOURCE.tsv",
    "SEMANTIC_RELATION_CANDIDATE.tsv",
    "SEMANTIC_RELATION_EDGE.tsv",
    "SEMANTIC_RELATION_EVIDENCE.tsv",
    "SEMANTIC_RELATION_REJECTION.tsv",
    "SEMANTIC_RELATION_OWNER_REVIEW_IMPORT_TEMPLATE.tsv",
    "SEMANTIC_RELATION_OWNER_REVIEW_PACKET.tsv",
    "SEMANTIC_RELATION_SUPPORT.tsv",
    "SEMANTIC_RELATION_SUMMARY.tsv",
    "SEMANTIC_SOURCE_ROUTE_YIELD.tsv",
    "SHA256SUMS",
    "STRICTNESS_IMPACT_LOG.tsv",
    "SOURCE_FAMILY_BALANCE.tsv",
    "SOURCE_FAMILY_HOLDOUT_PLAN.tsv",
    "SOURCE_STRATIFIED_SEMANTIC_AUDIT.tsv",
    "SMOKE_BENCHMARK_INTERPRETATION_ADDENDUM.json",
    "SMOKE_TARGET_SUPPORT_CORRECTION.tsv",
    "TARGETED_ACQUISITION_QUEUE.tsv",
    "TARGETED_ACQUISITION_RESULT.tsv",
    "TRAINING_GATE_STATUS.tsv",
    "YEAR_HOLDOUT_PLAN.tsv",
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
    cleaning_checksum_rows = {
        name: digest
        for digest, name in (
            line.split("  ", 1)
            for line in (CLEANING_STAGING / "SHA256SUMS")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    }
    cleaning_files = {
        path.name
        for path in CLEANING_STAGING.iterdir()
        if path.is_file() and path.name != "SHA256SUMS"
    }
    check(
        set(cleaning_checksum_rows) == cleaning_files,
        "candidate-cleaning staging checksum inventory drift",
    )
    check(
        all(
            sha(CLEANING_STAGING / name) == digest
            for name, digest in cleaning_checksum_rows.items()
        ),
        "candidate-cleaning staging source hash drift",
    )
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
    check(manifest["baseline_main_sha"] == "afde62ba0e957de959fd6127fc1e8b900814cbf4", "baseline SHA drift")
    check(manifest["round4a_product_files_imported"] == 0, "Round 4A product scope imported")
    check(manifest["schema_changed"] is False and manifest["new_migration_count"] == 0, "schema change claimed")
    check(manifest["model_training_run"] is False and manifest["model_weight_file_count"] == 0, "model training claimed")
    check(manifest["phase_status"] in {
        "CLEANING_PARTIAL_SEMANTIC_REVIEW_REQUIRED",
        "CLEANING_PASS_POST20K_EXTENSION_CHECKPOINT",
        "CLEANING_PASS_30K_CANDIDATE_CHECKPOINT_REACHED",
        "CLEANING_PASS_COE_ROUTE_EXHAUSTED",
        "CLEANING_PASS_NON_COE_DIVERSIFICATION_GAPS",
        "CLEANED_30K_AND_40K_ACQUISITION_CHECKPOINT_REACHED",
        "CLEANED_40K_SEMANTIC_LAYER_REVIEW_REQUIRED",
        "BATCH7_50K_CLEANED_SEMANTIC_ENGINEERING_PASS",
        "BATCH7_50K_AND_60K_ACQUISITION_CHECKPOINT_REACHED",
    }, "current cleaning status absent")

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

    batch3 = manifest["batch3_cleaning_metrics"]
    snapshot_manifest = json.loads((DATA / "CANDIDATE_20K_SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))
    check(snapshot_manifest["snapshot_version"] == "professional-descriptor-candidate-v0-20k", "20k snapshot version drift")
    check(snapshot_manifest["immutable"] is True and snapshot_manifest["post20k_extension_included_in_snapshot"] is False, "20k snapshot not immutable/isolated")
    check(snapshot_manifest["canonical_source_ledger_sha256"] == sha(DATA / "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv"), "20k snapshot source hash drift")
    check(snapshot_manifest["frozen_mechanically_deinflated_assertion_count"] == 20003, "20k snapshot denominator drift")

    cleaning = current_rows("SEMANTIC_CLEANING_DECISION.tsv")
    check(len(cleaning) == len(ledger), "semantic-cleaning completeness drift")
    check(len({row["descriptor_assertion_id"] for row in cleaning}) == len(cleaning), "semantic-cleaning IDs not unique")
    check(all(row["human_reviewed"] == "false" and row["expert_adjudicated"] == "false" for row in cleaning), "machine cleaning promoted to human/expert")
    cleaning_by_id = {row["descriptor_assertion_id"]: row for row in cleaning}
    for source in ledger:
        decision = cleaning_by_id[source["descriptor_assertion_id"]]
        check(decision["evidence_tier"] == source["evidence_tier"], "cleaning widened evidence tier")
        check(decision["rights_state"] == source["rights_state"], "cleaning widened rights state")
        check(decision["model_eligible"] == "false", "cleaning widened model eligibility")

    segmentation = current_rows("SEGMENTATION_DECISION.tsv")
    check(all(row["segmentation_reversible"] == "true" for row in segmentation), "segmentation reversibility drift")
    normalization = current_rows("CANONICAL_NORMALIZATION_MAP.tsv")
    check(len({row["cleaned_lexical_form_sha256"] for row in normalization}) == len(normalization), "normalization form IDs not unique")
    decision_form_hashes = {
        form_hash
        for row in cleaning
        for form_hash in row["cleaned_lexical_form_sha256s"].split("|")
        if form_hash
    }
    normalization_form_hashes = {
        row["cleaned_lexical_form_sha256"] for row in normalization
    }
    check(
        decision_form_hashes == normalization_form_hashes,
        "normalization dispositions do not cover every cleaned form",
    )
    check(all(row["review_requirement"] in {"AUTOMATED_SAFE_RULE", "MACHINE_PROVISIONAL_REVIEW"} for row in normalization), "normalization review state widened")

    cleaned = current_rows("CLEANED_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    check(len(cleaned) == sum(batch3[key] for key in (
        "cleaned_strict_flavor_assertion_count", "cleaned_broad_sensory_assertion_count", "cleaned_defect_assertion_count"
    )), "cleaned class reconciliation drift")
    check(sum(row["counts_as_record_unique_cleaned_descriptor"] == "true" for row in cleaned) == batch3["record_unique_cleaned_assertion_count"], "cleaned record-unique reconciliation drift")
    check(all(row["source_native_form_or_restricted_pointer"].startswith("hash:sha256:") for row in cleaned), "cleaned ledger leaked source-native text")
    check(all(row["cleaned_lexical_form_or_restricted_pointer"].startswith("hash:sha256:") for row in cleaned), "cleaned ledger leaked lexical text")
    check(not any(row["model_eligible"] == "true" for row in cleaned), "cleaned ledger model eligibility widened")

    cleaned_distribution = current_rows("CLEANED_DESCRIPTOR_DISTRIBUTION.tsv")
    check(sum(int(row["cleaned_assertion_support"]) for row in cleaned_distribution) == len(cleaned), "cleaned distribution assertion reconciliation drift")
    cleaned_support = current_rows("CLEANED_DESCRIPTOR_SUPPORT_BANDS.tsv")
    check(sum(int(row["descriptor_count"]) for row in cleaned_support) == len(cleaned_distribution), "cleaned support-band descriptor reconciliation drift")
    check(sum(int(row["cleaned_assertion_count"]) for row in cleaned_support) == len(cleaned), "cleaned support-band assertion reconciliation drift")

    pair_receipt = current_rows("CLEANED_PAIR_EVENT_RECEIPT.tsv")
    check(sum(int(row["record_unique_pair_event_count"]) for row in pair_receipt) == batch3["pair_event_count"], "cleaned pair-event reconciliation drift")
    check(sum(int(row["zenodo_sample_consensus_pair_event_count"]) for row in pair_receipt) == batch3["sample_consensus_pair_event_count"], "sample-consensus pair reconciliation drift")
    check(all(row["maximum_single_record_contribution"] in {"0", "1"} and row["pair_counted_as_source_assertion"] == "false" for row in pair_receipt), "pair inflated source assertion or record contribution")

    entity = current_rows("COE_ENTITY_RESOLUTION.tsv")
    check(len(entity) == 7 and all(row["match_state"] in {
        "EXACT_SAME_EFFECTIVE_RECORD", "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD",
        "POSSIBLE_SAME_EFFECTIVE_RECORD_REVIEW_REQUIRED", "DISTINCT_ROUND_OR_SERVICE",
        "DISTINCT_COFFEE", "INSUFFICIENT_IDENTITY_EVIDENCE",
    } for row in entity), "CoE entity audit incomplete")
    entity_duplicates = current_rows("COE_CROSS_DOMAIN_DUPLICATE_DECISION.tsv")
    check(all(row["retain_both_source_artifacts"] == "true" for row in entity_duplicates), "CoE publication lineage discarded")

    audit = current_rows("SOURCE_STRATIFIED_SEMANTIC_AUDIT.tsv")
    check(len(audit) == batch3["semantic_audit_sample_count"], "semantic audit count drift")
    check(sum(row["audit_stratum"] in {"ZENODO_GOLD_ALL", "COE_GOLD_EXPLICIT_JURY"} for row in audit) == 5055, "not all Gold assertions audited")
    check(len({row["panelist_sample_observation_sha256"] for row in audit if row["panelist_sample_observation_sha256"]}) == 360, "Zenodo observation audit drift")
    check(Counter(row["audit_stratum"] for row in audit)["INDIA_FINE_CUP_ALL"] == 59, "India audit incomplete")
    check(Counter(row["audit_stratum"] for row in audit)["SHEBA_ALL"] == 28, "Sheba audit incomplete")
    check(Counter(row["audit_stratum"] for row in audit)["PROJECT_ORIGIN_ALL"] == 302, "Project Origin audit incomplete")
    check(Counter(row["audit_stratum"] for row in audit)["COE_GENERIC_STRATIFIED"] == 300, "CoE generic audit sample incomplete")

    review_clusters = current_rows("REVIEW_CLUSTER_QUEUE.tsv")
    check(len(review_clusters) <= 300 and len(review_clusters) == batch3["active_review_cluster_count"], "active cleaning cluster cap/reconciliation drift")
    queued_hashes = {row["cleaned_lexical_form_or_restricted_pointer"].removeprefix("hash:sha256:") for row in review_clusters}
    check(all(row["cleaned_lexical_form_sha256"] in queued_hashes for row in normalization if row["semantic_class"] in {"STRICT_FLAVOR", "BROAD_SENSORY", "DEFECT_OR_NEGATIVE_SENSORY"} and int(row["assertion_support"]) >= 20), "support>=20 cleaning cluster omitted")

    balance = current_rows("SOURCE_FAMILY_BALANCE.tsv")
    check(len(balance) == batch3["cleaned_source_family_count"], "cleaned source-family count drift")
    check(sum(int(row["cleaned_descriptor_assertion_count"]) for row in balance) == len(cleaned), "source-family cleaned assertion reconciliation drift")
    check(batch3["zenodo_panelist_sample_observation_count"] == 360 and batch3["zenodo_effective_sample_count"] == 112, "Zenodo observation/sample separation drift")

    extension_progress = {row["metric"]: row["observed_value"] for row in current_rows("POST20K_EXTENSION_PROGRESS.tsv")}
    check(extension_progress["CURSOR_START"] == snapshot_manifest["exact_post20k_continuation_cursor"], "post20k cursor continuity drift")
    check(not any(row["source_dataset_id"].startswith("post20k") for row in ledger), "post20k extension leaked into frozen ledger")

    forbidden_suffixes = {".ckpt", ".joblib", ".onnx", ".pkl", ".pt", ".pth", ".safetensors", ".tflite"}
    check(not any(path.suffix.lower() in forbidden_suffixes for path in DATA.rglob("*")), "model weight persisted")

    before = snapshot()
    subprocess.run([sys.executable, str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
    subprocess.run(
        [sys.executable, str(BATCH4_GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, "-B", str(BATCH6_GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, "-B", str(BATCH7_RUNNER), "semantic"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [sys.executable, "-B", str(BATCH7_RUNNER), "checkpoint"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    check(before == snapshot(), "generator is not deterministic")

    print("CURRENT_DESCRIPTOR_DATA_CONTRACT_PASS=true")
    print(f"MERGED_ASSERTION_LEVEL_DEINFLATED_COUNT={metrics['assertion_deinflated']}")
    print(f"MERGED_DESCRIPTOR_BEARING_EFFECTIVE_RECORD_COUNT={metrics['effective_records']}")
    print(f"PROVISIONAL_MAPPING_COVERAGE_RATE={metrics['provisional_mapping_coverage_rate']:.6f}")
    print("MODEL_ELIGIBLE_ASSERTION_COUNT=0")


if __name__ == "__main__":
    main()
