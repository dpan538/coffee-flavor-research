#!/usr/bin/env python3
"""Generate the rolling public-safe descriptor data and ML-readiness package.

The current package is a deterministic derived view over the governed Round 3M
ledger, the Round 3L public receipts, selected Round 4A data-health semantics,
and one bounded 2026-08-29 acquisition receipt. It never imports the missing
descriptor-census rows, publishes source-native descriptor strings, changes a
database schema, or promotes machine-audited evidence to human review.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db" / "data" / "current"
ROUND3M = ROOT / "db" / "data" / "round3m"
ROUND3L = ROOT / "db" / "data" / "round3l" / "public"
ADAPTER3M = ROOT / "db" / "adapters" / "round3m" / "generated"
BATCH2 = ROOT / "db" / "data" / "professional-descriptor-staging"
BATCH2_SIDECAR = BATCH2 / "PUBLIC_SAFE_ASSERTION_SIDECAR.tsv"
BATCH2_ROUTES = BATCH2 / "SOURCE_ROUTE_PROBE_AND_YIELD.tsv"
BATCH2_MANIFEST = BATCH2 / "BATCH2_PUBLIC_MANIFEST.json"

BASELINE_MAIN_SHA = "21d04f50952ac30ee13010ee26bae8a224ea9f71"
ROUND4A_SHA = "48ff0a921db4da98b2802c60bc23ee031687175b"
ROUND4A_IMPLEMENTATION_SHA = "3781afc46495ad4e6ad94e0d4dd238f6f71a293f"
ROUND3_EXTERNAL_REPORT_SHA256 = "d319236311f2abc5e15baaf70923b32e0a2bdbb5dc010723feea3e4aec8069e0"
BATCH_ID = "professional-descriptor-scaleup-batch2-20260829"
BATCH_DATE = "2026-08-29"

NEW_SOURCE_URL = (
    "https://farmdirectory.cupofexcellence.org/listing/"
    "2009-brazil-pulped-naturals-84-96/"
)
NEW_BODY_TEXT_SHA256 = "0716d43dedbfcb99393e7f81e8d89f919ab8358e717fcb0a0f633ab091447839"
NEW_BODY_TEXT_BYTES = 4498
NEW_RECORD_IDENTITY_SHA256 = "1cf75637c208a1513d29c617d48474ff192f94ffb3314c82033bc79128b0a288"

# Hash-only bounded source atoms. Source-native strings were used transiently
# to calculate these hashes and are intentionally absent from the repository.
NEW_ATOMS = (
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "6815f3c300383519de8e437497e2c3e97852fe8d717a5419d5aafb00cb43c494", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "26138f2ac4b2c2bb71aee05f2a671fe9b23262b69a3154320cfa21479334a906", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "b1123b42a6d1bb3e5e45c40353a2bbe668e240933f735d4d48dbc2563e3c9310", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "abe10a7b1ab725a978ccf7e84f2b60cf1d24717c819664a46569099a88e57bc4", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "dce34e094109d0c0e096b1c304b8053a1aab66e9ae09916faf3e0e8a3000c4be", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "4cb189665ff62a96d317a44d708a4f75a8f7fb431fa2931ed24edc43b59df3b4", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "82d68a121058172ff532679a8d683add49b386285512ff53f6048a79b6b8e9b7", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "7019275bf53483f22cab4e0f568d2c2a8f785fa3b558024cd8ba12f3894bd6b0", "STRICT_FLAVOR"),
    ("Aroma / Flavor", "aa56ed6fb422135994486c580bcc477b959101421e8aaf752532104779547de0", "545ce787c410276d227955b06ea5e6c1f3e3d611dc3f50594e556cce34b5ce4e", "STRICT_FLAVOR"),
    ("Acidity", "ff5bd5743b9b1cafdb91750d88653ee9e989b5b0887eec0ca6e35d33e3a6d9c1", "7d108ddb9255c7f990a9ec23453aea2b99ac06e5150c1e70e804e64dc22ee748", "BROAD_SENSORY"),
    ("Acidity", "ff5bd5743b9b1cafdb91750d88653ee9e989b5b0887eec0ca6e35d33e3a6d9c1", "ea4b35e8f83279eab1e670e389d71201b360f291a0dc30c659ed708ac9c67d76", "BROAD_SENSORY"),
    ("Acidity", "ff5bd5743b9b1cafdb91750d88653ee9e989b5b0887eec0ca6e35d33e3a6d9c1", "8290c583738717f6ceea216b3c94302eeaf53dc81bcaf4337a593bb6a752b851", "BROAD_SENSORY"),
    ("Acidity", "ff5bd5743b9b1cafdb91750d88653ee9e989b5b0887eec0ca6e35d33e3a6d9c1", "832defad5e400860125df3678f2c59c9f2c8d727ad5a142553c6a22dec5164f4", "BROAD_SENSORY"),
    ("Overall", "ce09c7a3b723ba231e89eec6a5cd209a02fc0895d2489c1347056425d699dbde", "dcaecc3ba9958606018c05b33dc60ba0e387ab7ae160516b30abb580ed773e65", "BROAD_SENSORY"),
    ("Overall", "ce09c7a3b723ba231e89eec6a5cd209a02fc0895d2489c1347056425d699dbde", "33be1731e5a1fe7598d31ce6d84b3fe3bd57535aa9615abf0a743e30740bedfc", "STRICT_FLAVOR"),
    ("Overall", "ce09c7a3b723ba231e89eec6a5cd209a02fc0895d2489c1347056425d699dbde", "4b383ae9188130c4acdbd9cc4b0b60fc4911f08a8b26bc8d9d47963544ebe90a", "STRICT_FLAVOR"),
    ("Overall", "ce09c7a3b723ba231e89eec6a5cd209a02fc0895d2489c1347056425d699dbde", "0f151919b9ea8540476cb1e7aaff8c39ffffe133e74eb3162aba2f01e6a71438", "BROAD_SENSORY"),
    ("Overall", "ce09c7a3b723ba231e89eec6a5cd209a02fc0895d2489c1347056425d699dbde", "4fff1d64058c259e3df1624f65ce75c01a79667932cef2bdd2e93c08e090b733", "BROAD_SENSORY"),
)

ROUND4A_HASHES = {
    "DATASET_COMPATIBILITY_MATRIX.tsv": "62d56d6c075b6607c59a7625219e1ff000ee4d688358b2c42d1c3f492d9b59e7",
    "DESCRIPTOR_CORPUS_HEALTH.tsv": "8f75ba9605baf1bd1b5245f2aa34a33de395426cf88ef042d5408152b059d430",
    "DESCRIPTOR_GRAPH_COMPONENTS.tsv": "81b8f46870462b2b2ec405f3ebf1e664185d9eecbf9ab0461cadb71e078abb3b",
    "DESCRIPTOR_PAIR_EDGE.tsv": "3377ec03c7b4c14495a2f8aaa0f8acc84ca12e8679396e28a22e2a5ff8c67a97",
    "DESCRIPTOR_PAIR_SUPPORT_DISTRIBUTION.tsv": "a1d0be619093ae61c6b4e6a0738008d2cc14207a3ed6ca0efdeaa2204fdc37a4",
    "LABEL_SUPPORT_DISTRIBUTION.tsv": "ec7c4d7055f2d7e0bd715edddadf7947203eb5d60bb5d681abb391c47c90608c",
    "LONGITUDINAL_ARCHIVE_COMPLETENESS.tsv": "e5777fa7bb3e2b3d1f035f17a1cc44da2c369b149b86e3b7246cf9d44638b27e",
    "LONGITUDINAL_ARCHIVE_EXPECTATION.tsv": "e5777fa7bb3e2b3d1f035f17a1cc44da2c369b149b86e3b7246cf9d44638b27e",
    "PROFESSIONAL_REFERENCE_MANIFEST.json": "181714e67513345dd363962fe7d72e14387bb89fe531ae3786edcdb1205a9d26",
    "SOURCE_FAMILY_CONCENTRATION.tsv": "0d55045ea95581db30a142b14f4d452e63f3955b19ace37c49a6021360a27039",
    "SPLIT_FEASIBILITY.tsv": "361878faf78ece8a77d16eca3836c83535a2cf6ad4eeee82b4e6fb3198a528bc",
    "TASK_DATA_HEALTH.tsv": "7347fb33473f4b3a93b8458b758cab30317cdd0112dfd7bb020dce363e5127dc",
    "TRAINING_FEASIBILITY_DECISION.json": "bbba01ebef5ebf6788162865e7ac3a1a9915ab90a18dcd0d8593d74c1ad22587",
    "ROUND4A_MANIFEST.json": "46266b03303a2232ce71d38b1a52272c2caab221362b80422e6d1753c1716052",
    "SHA256SUMS": "NA_SELF_CHECKSUM_FILE_NOT_LISTED_IN_ITSELF",
}

ROUND4A_REJECTED = {
    "DATASET_COMPATIBILITY_MATRIX.tsv": "REDUNDANT_STATIC_MATRIX_NOT_CURRENT_MERGED_DATA",
    "DESCRIPTOR_GRAPH_COMPONENTS.tsv": "HASH_COMPONENTS_NOT_NORMALIZED_DESCRIPTOR_IDENTITIES",
    "LABEL_SUPPORT_DISTRIBUTION.tsv": "REDUNDANT_ZERO_LABEL_RECEIPT_REGENERATED_AS_SUPPORT_BANDS",
    "TASK_DATA_HEALTH.tsv": "REDUNDANT_TASK_REPORT_REPLACED_BY_CURRENT_GATE_STATUS",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(name: str, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fieldnames = list(fields)
    with (OUT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: scalar(row.get(field, "")) for field in fieldnames})


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    return value


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode()).hexdigest()[:24]}"


def data_rows(path: Path) -> str:
    if path.suffix != ".tsv":
        return "NA_NOT_TABULAR"
    with path.open(encoding="utf-8") as handle:
        return str(max(sum(1 for _ in handle) - 1, 0))


def inventory() -> list[dict[str, Any]]:
    fields = {
        "source_round_or_batch": "",
        "source_branch": "",
        "source_commit_sha": "",
        "repository_path_or_restricted_locator": "",
        "file_sha256": "",
        "file_size": "",
        "row_count": "",
        "descriptor_candidate_row_count": "",
        "effective_record_count": "",
        "data_role": "",
        "evidence_tiers_present": "",
        "rights_state": "",
        "review_state": "",
        "contains_raw_source_text": False,
        "public_commit_allowed": True,
        "overlap_expected_with": "",
        "current_disposition": "",
    }
    rows: list[dict[str, Any]] = []

    def local(
        dataset_id: str,
        name: str,
        path: Path,
        round_name: str,
        role: str,
        candidates: str,
        records: str,
        tiers: str,
        rights: str,
        review: str,
        overlap: str,
        disposition: str,
    ) -> None:
        rel = path.relative_to(ROOT).as_posix()
        row = dict(fields)
        row.update(
            dataset_id=dataset_id,
            dataset_name=name,
            source_round_or_batch=round_name,
            source_branch="origin/main",
            source_commit_sha=BASELINE_MAIN_SHA,
            repository_path_or_restricted_locator=rel,
            file_sha256=sha256_file(path),
            file_size=str(path.stat().st_size),
            row_count=data_rows(path),
            descriptor_candidate_row_count=candidates,
            effective_record_count=records,
            data_role=role,
            evidence_tiers_present=tiers,
            rights_state=rights,
            review_state=review,
            overlap_expected_with=overlap,
            current_disposition=disposition,
        )
        rows.append(row)

    local("round3m-live-assertions", "Round 3M live-pilot descriptor assertions", ROUND3M / "DESCRIPTOR_ASSERTION_LEDGER.tsv", "ROUND3M", "ROW_LEVEL_PRIMARY", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "PROVISIONAL_MACHINE_CLASSIFIED", "round4a-professional-reference|round4a-pair-edge", "CANONICAL_ROW_LEVEL_INPUT")
    local("round3m-effective-records", "Round 3M public-safe effective records", ADAPTER3M / "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "PROVISIONAL_MACHINE_CLASSIFIED", "round3m-live-assertions", "IDENTITY_BRIDGE")
    local("round3m-review-queue", "Round 3M merged review queue", ROUND3M / "DESCRIPTOR_REVIEW_QUEUE.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "REJECTED_NON_DESCRIPTOR|HUMAN_REVIEW_REQUIRED", "round3m-live-assertions|round3m-legacy-376", "REVIEW_LINEAGE")
    local("round3m-provisional-decisions", "Round 3M provisional decisions", ROUND3M / "DESCRIPTOR_PROVISIONAL_DECISIONS.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "CODEX_SOURCE_AUDIT_ONLY", "round3m-review-queue", "REVIEW_LINEAGE")
    local("round3m-normalization", "Round 3M normalization decisions", ROUND3M / "DESCRIPTOR_NORMALIZATION_DECISION.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "UNMAPPED_HASH_ONLY", "round3m-live-assertions", "NORMALIZATION_LINEAGE")
    local("round3m-provenance", "Round 3M provenance decisions", ROUND3M / "DESCRIPTOR_PROVENANCE_DECISION.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "CODEX_SOURCE_AUDIT_ONLY", "round3m-live-assertions", "PROVENANCE_LINEAGE")
    local("round3m-rights", "Round 3M purpose-specific rights decisions", ROUND3M / "DESCRIPTOR_RIGHTS_DECISION.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "CODEX_SOURCE_AUDIT_ONLY", "round3m-live-assertions", "RIGHTS_LINEAGE")
    local("round3m-duplicate", "Round 3M duplicate and repeat decisions", ROUND3M / "DUPLICATE_REPEAT_DECISION.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "140", "8", "P2|UNRESOLVED", "PENDING|UNKNOWN", "CODEX_SOURCE_AUDIT_ONLY", "round3m-live-assertions", "DEINFLATION_LINEAGE")
    local("round3m-pairs", "Round 3M co-assertion pair events", ROUND3M / "COASSERTION_EVENT.tsv", "ROUND3M", "ROW_LEVEL_DERIVED", "508", "5", "P2", "PENDING", "PROVISIONAL_MACHINE_CLASSIFIED", "round3m-live-assertions|round4a-pair-edge", "PAIR_EVENT_DERIVATION")
    local("round3l-restricted-receipt", "Round 3L restricted ledger receipt", ROUND3L / "RESTRICTED_LEDGER_RECEIPT.json", "ROUND3L", "AGGREGATE_RECEIPT_ONLY", "11801", "20994", "MIXED", "MIXED", "STAGED", "round3m-review-queue", "RESTRICTED_DATA_NOT_IMPORTED")
    local("round3l-public-checkpoint", "Round 3L public checkpoint", ROUND3L / "PUBLIC_CHECKPOINT.json", "ROUND3L", "AGGREGATE_RECEIPT_ONLY", "376", "26515", "UNRESOLVED", "MIXED", "STAGED", "round3m-legacy-376", "AGGREGATE_LINEAGE_ONLY")
    local("round3l-source-attempts", "Round 3L public source-attempt receipts", ROUND3L / "SOURCE_ATTEMPTS_PUBLIC.tsv", "ROUND3L", "ROW_LEVEL_DERIVED", "376", "NA_ATTEMPT_ROWS_NOT_COFFEE_RECORDS", "MIXED", "MIXED", "SOURCE_AUDITED", "round3m-source-census", "ACQUISITION_LINEAGE")
    local("round3m-normalized-language-reference", "Existing normalized expression assets", ROOT / "db/data/round3i/evaluation/language_expressions.tsv", "ROUND3I", "REFERENCE_ONLY", "0", "0", "REFERENCE_ONLY", "SOURCE_SPECIFIC", "HISTORICAL_FROZEN", "round3m-normalization", "NO_OBSERVATION_MERGE")
    local("round3m-c0-c1-receipt", "Current C0 and C1 evidence receipt", ROUND3M / "C0_C1_EVIDENCE_RECEIPT.json", "ROUND3M", "AGGREGATE_RECEIPT_ONLY", "0", "26515", "REFERENCE_ONLY", "MIXED", "SOURCE_AUDITED", "round3l-restricted-receipt", "CONTEXT_RECEIPT_ONLY")

    external = dict(fields)
    external.update(
        dataset_id="round3-external-descriptor-receipt",
        dataset_name="Descriptor-First Census external lower-bound receipt",
        source_round_or_batch="ROUND3_EXTERNAL_DESCRIPTOR_RECEIPT",
        source_branch="NA_EXTERNAL_REPORT_NOT_GIT_VERSIONED",
        source_commit_sha="NA_EXTERNAL_REPORT_NOT_GIT_VERSIONED",
        repository_path_or_restricted_locator="external-attachment://Descriptor-First-Census-of-Open-Professional-Coffee-Sensory-Evidence.pdf",
        file_sha256=ROUND3_EXTERNAL_REPORT_SHA256,
        file_size="122241",
        row_count="NA_AGGREGATE_RECEIPT_ONLY_REPORT_PRESENT_MACHINE_BUNDLE_MISSING",
        descriptor_candidate_row_count="303",
        effective_record_count="15",
        data_role="AGGREGATE_RECEIPT_ONLY",
        evidence_tiers_present="P2|P3|PROVENANCE_UNRESOLVED",
        rights_state="NOT_REPORTED_IN_HEADLINE_RECEIPT",
        review_state="DIRECTLY_INSPECTED_EXTERNAL_AUDIT_RECEIPT",
        overlap_expected_with="round3m-live-assertions|round3l-restricted-receipt",
        current_disposition="COUNTS_ONLY_REPORT_INSPECTED_NO_ROW_LEVEL_IMPORT",
    )
    rows.append(external)

    missing_bundle = dict(fields)
    missing_bundle.update(
        dataset_id="round3-descriptor-census-machine-bundle",
        dataset_name="Nine-file descriptor census machine-readable bundle",
        source_round_or_batch="ROUND3_EXTERNAL_DESCRIPTOR_RECEIPT",
        source_branch="NA_NOT_FOUND",
        source_commit_sha="NA_NOT_FOUND",
        repository_path_or_restricted_locator="missing-input://nine-file-machine-readable-descriptor-census-bundle",
        file_sha256="NA_NINE_REQUIRED_FILES_NOT_FOUND",
        file_size="NA_NINE_REQUIRED_FILES_NOT_FOUND",
        row_count="NA_NINE_REQUIRED_FILES_NOT_FOUND",
        descriptor_candidate_row_count="NA_NOT_RECONSTRUCTED_FROM_REPORT",
        effective_record_count="NA_NOT_RECONSTRUCTED_FROM_REPORT",
        data_role="AGGREGATE_RECEIPT_ONLY",
        evidence_tiers_present="NA_MISSING_INPUT",
        rights_state="NA_MISSING_INPUT",
        review_state="BLOCKED_MISSING_MACHINE_ARTIFACTS",
        overlap_expected_with="round3-external-descriptor-receipt",
        current_disposition="MISSING_LINEAGE_LIMITATION",
    )
    rows.append(missing_bundle)

    acquisition = dict(fields)
    acquisition.update(
        dataset_id="current-targeted-acquisition-hash-ledger",
        dataset_name="Batch 1 bounded official-field hash ledger",
        source_round_or_batch=BATCH_ID,
        source_branch="research/coffee-sensory-data-ml-readiness",
        source_commit_sha="NA_EXTERNAL_CAPTURE_NOT_FROM_GIT",
        repository_path_or_restricted_locator=NEW_SOURCE_URL,
        file_sha256=NEW_BODY_TEXT_SHA256,
        file_size=str(NEW_BODY_TEXT_BYTES),
        row_count=str(len(NEW_ATOMS)),
        descriptor_candidate_row_count=str(len(NEW_ATOMS)),
        effective_record_count="1",
        data_role="ROW_LEVEL_PRIMARY",
        evidence_tiers_present="PROVENANCE_UNRESOLVED_PROFESSIONAL",
        rights_state="UNKNOWN",
        review_state="HUMAN_REVIEW_REQUIRED",
        overlap_expected_with="round3m-live-assertions",
        current_disposition="RESEARCH_STAGED_HASH_ONLY",
    )
    rows.append(acquisition)

    for name, digest in sorted(ROUND4A_HASHES.items()):
        rejected = name in ROUND4A_REJECTED
        role = "DUPLICATE_DERIVATION"
        if name in {"ROUND4A_MANIFEST.json", "SHA256SUMS", "PROFESSIONAL_REFERENCE_MANIFEST.json", "TRAINING_FEASIBILITY_DECISION.json"}:
            role = "AGGREGATE_RECEIPT_ONLY"
        elif name.startswith("LONGITUDINAL"):
            role = "ROW_LEVEL_DERIVED"
        row = dict(fields)
        row.update(
            dataset_id=f"round4a-{name.lower().replace('_', '-').replace('.', '-')}",
            dataset_name=f"Round 4A {name}",
            source_round_or_batch="ROUND4A_DATA_HEALTH",
            source_branch="origin/codex/coffee-flavor-round4a-prototype-training-readiness-20260829",
            source_commit_sha=ROUND4A_SHA,
            repository_path_or_restricted_locator=f"git:{ROUND4A_SHA}:db/data/round4a/{name}",
            file_sha256=digest,
            file_size="NA_BRANCH_ONLY_ARTIFACT_NOT_IMPORTED",
            row_count="NA_BRANCH_ONLY_ARTIFACT_NOT_IMPORTED",
            descriptor_candidate_row_count="140" if name in {"DESCRIPTOR_CORPUS_HEALTH.tsv", "PROFESSIONAL_REFERENCE_MANIFEST.json"} else "0",
            effective_record_count="8" if name in {"DESCRIPTOR_CORPUS_HEALTH.tsv", "PROFESSIONAL_REFERENCE_MANIFEST.json"} else "NA_DERIVED_OR_AGGREGATE",
            data_role=role,
            evidence_tiers_present="P2|UNRESOLVED|REFERENCE_ONLY",
            rights_state="REFERENCE_ONLY",
            review_state="PROVISIONAL_MACHINE_CLASSIFIED",
            overlap_expected_with="round3m-live-assertions|round3m-pairs",
            current_disposition=(ROUND4A_REJECTED[name] if rejected else "ACCEPTED_SEMANTICS_REGENERATE_OR_LINEAGE_ONLY"),
        )
        rows.append(row)

    batch2_manifest = json.loads(BATCH2_MANIFEST.read_text(encoding="utf-8"))
    batch2_sidecar = dict(fields)
    batch2_sidecar.update(
        dataset_id="professional-descriptor-scaleup-batch2-public-safe",
        dataset_name="Batch 2 public-safe professional descriptor assertion sidecar",
        source_round_or_batch=BATCH_ID,
        source_branch="research/coffee-sensory-data-ml-readiness",
        source_commit_sha="NA_GENERATED_IN_CURRENT_RESEARCH_BRANCH",
        repository_path_or_restricted_locator=BATCH2_SIDECAR.relative_to(ROOT).as_posix(),
        file_sha256=sha256_file(BATCH2_SIDECAR),
        file_size=str(BATCH2_SIDECAR.stat().st_size),
        row_count=data_rows(BATCH2_SIDECAR),
        descriptor_candidate_row_count=str(
            batch2_manifest["net_new_deinflated_candidate_count"]
        ),
        effective_record_count="SEE_CURRENT_MERGE_RECEIPT",
        data_role="ROW_LEVEL_PRIMARY_PUBLIC_SAFE",
        evidence_tiers_present="P1|P2|P4|UNRESOLVED",
        rights_state="AFFIRMATIVE|PENDING|UNKNOWN",
        review_state="PROVISIONAL_MACHINE_CLASSIFIED",
        overlap_expected_with="current-targeted-acquisition-hash-ledger",
        current_disposition="MERGE_WITH_PUBLICATION_LAYER_DEINFLATION;MODEL_INELIGIBLE",
    )
    rows.append(batch2_sidecar)

    batch2_routes = dict(fields)
    batch2_routes.update(
        dataset_id="professional-descriptor-scaleup-batch2-route-receipt",
        dataset_name="Batch 2 source-route probe and yield receipt",
        source_round_or_batch=BATCH_ID,
        source_branch="research/coffee-sensory-data-ml-readiness",
        source_commit_sha="NA_GENERATED_IN_CURRENT_RESEARCH_BRANCH",
        repository_path_or_restricted_locator=BATCH2_ROUTES.relative_to(ROOT).as_posix(),
        file_sha256=sha256_file(BATCH2_ROUTES),
        file_size=str(BATCH2_ROUTES.stat().st_size),
        row_count=data_rows(BATCH2_ROUTES),
        descriptor_candidate_row_count="NA_ROUTE_AGGREGATE",
        effective_record_count="NA_ROUTE_AGGREGATE",
        data_role="AGGREGATE_RECEIPT_ONLY",
        evidence_tiers_present="P1|P2|P4|UNRESOLVED",
        rights_state="AFFIRMATIVE|PENDING|UNKNOWN",
        review_state="SOURCE_AUDITED_ROUTE_CLASSIFICATION",
        overlap_expected_with="professional-descriptor-scaleup-batch2-public-safe",
        current_disposition="ACQUISITION_LINEAGE_ONLY",
    )
    rows.append(batch2_routes)
    return rows


LEDGER_FIELDS = (
    "descriptor_assertion_id", "source_dataset_id", "source_artifact_id",
    "source_file_sha256", "source_route_id", "source_family_id", "organizer_id",
    "competition_series_id", "edition_id", "edition_year", "category_id",
    "round_id", "entry_or_lot_id", "coffee_identity_id", "preparation_service_id",
    "effective_record_id", "publication_layer", "source_field_label", "source_locator",
    "raw_source_text_or_restricted_pointer", "atomic_source_text_or_restricted_pointer",
    "source_language", "descriptor_class", "source_native_lexical_form_or_restricted_pointer",
    "normalized_descriptor_candidate_id", "evidence_tier", "provenance_state",
    "rights_state", "review_state", "corpus_state", "evidence_stratum",
    "duplicate_group_id", "mirror_group_id", "repeat_group_id",
    "same_coffee_cross_observation_group_id", "c0_source_status", "c0_family",
    "c1_source_status", "source_native_roast_value", "reviewed_c1_mapping",
    "source_commit_sha", "parser_version", "adapter_version", "created_at",
    "counts_as_assertion", "counts_as_record_unique_descriptor", "model_eligible",
    "source_field_text_sha256", "atomic_source_text_sha256", "source_text_storage_state",
    "source_text_non_storage_reason",
)


def canonical_ledger() -> list[dict[str, Any]]:
    ledger = read_tsv(ROUND3M / "DESCRIPTOR_ASSERTION_LEDGER.tsv")
    effective = {
        row["round3m_effective_record_id"]: row
        for row in read_tsv(ADAPTER3M / "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv")
    }
    duplicates = {
        row["descriptor_assertion_id"]: row
        for row in read_tsv(ROUND3M / "DUPLICATE_REPEAT_DECISION.tsv")
    }
    rights = {
        row["descriptor_assertion_id"]: row["rights_state"]
        for row in read_tsv(ROUND3M / "DESCRIPTOR_RIGHTS_DECISION.tsv")
        if row["purpose"] == "MODEL_RESEARCH"
    }
    rows: list[dict[str, Any]] = []
    for source in ledger:
        record = effective[source["effective_record_id"]]
        duplicate = duplicates[source["descriptor_assertion_id"]]
        tier = source["evidence_tier"]
        source_rights = rights[source["descriptor_assertion_id"]]
        rows.append(
            {
                "descriptor_assertion_id": source["descriptor_assertion_id"],
                "source_dataset_id": "round3m-live-assertions",
                "source_artifact_id": source["source_artifact_id"],
                "source_file_sha256": source["source_file_sha256"],
                "source_route_id": source["source_route_id"],
                "source_family_id": "family.ace_cup_of_excellence",
                "organizer_id": "organizer.ace",
                "competition_series_id": record["series_id"],
                "edition_id": record["edition_id"],
                "edition_year": record["edition_year"],
                "category_id": record["category_id"],
                "round_id": record["round_id"],
                "entry_or_lot_id": record["entry_or_lot_id"],
                "coffee_identity_id": record.get("coffee_identity_key") or record["entry_or_lot_id"],
                "preparation_service_id": record["preparation_service_code"],
                "effective_record_id": source["effective_record_id"],
                "publication_layer": source["publication_layer"],
                "source_field_label": source["source_field_label"],
                "source_locator": source["source_page_or_record_locator"],
                "raw_source_text_or_restricted_pointer": source["source_selector_or_locator"],
                "atomic_source_text_or_restricted_pointer": f"hash:sha256:{source['atomic_source_text_sha256']}",
                "source_language": source["source_language"],
                "descriptor_class": source["descriptor_class"],
                "source_native_lexical_form_or_restricted_pointer": f"hash:sha256:{source['source_native_lexical_form_sha256']}",
                "normalized_descriptor_candidate_id": source["normalized_candidate_form"],
                "evidence_tier": tier,
                "provenance_state": "SOURCE_AUDITED_EXPLICIT_JURY_FIELD" if tier == "P2" else "OFFICIAL_FIELD_ORIGIN_UNRESOLVED",
                "rights_state": source_rights,
                "review_state": source["review_state"],
                "corpus_state": "HUMAN_REVIEW_REQUIRED",
                "evidence_stratum": "B_CORE_RIGHTS_BLOCKED" if tier == "P2" else "C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED",
                "duplicate_group_id": source["within_record_repeat_group"],
                "mirror_group_id": source["mirror_group"],
                "repeat_group_id": source["cross_observation_repeat_group"],
                "same_coffee_cross_observation_group_id": source["cross_observation_repeat_group"],
                "c0_source_status": record.get("c0_source_status", "SOURCE_UNKNOWN"),
                "c0_family": record.get("c0_family", ""),
                "c1_source_status": record.get("c1_evidence_status", "SOURCE_UNKNOWN"),
                "source_native_roast_value": record.get("source_native_roast_value", ""),
                "reviewed_c1_mapping": record.get("reviewed_c1_mapping", ""),
                "source_commit_sha": BASELINE_MAIN_SHA,
                "parser_version": source["parser_version"],
                "adapter_version": source["adapter_version"],
                "created_at": source["created_at"],
                "counts_as_assertion": duplicate["counts_as_assertion"],
                "counts_as_record_unique_descriptor": duplicate["counts_as_record_unique_descriptor"],
                "model_eligible": False,
                "source_field_text_sha256": source["raw_field_text_sha256"],
                "atomic_source_text_sha256": source["atomic_source_text_sha256"],
                "source_text_storage_state": source["source_text_storage_state"],
                "source_text_non_storage_reason": source["source_text_non_storage_reason"],
            }
        )

    effective_id = f"effective-current:{NEW_RECORD_IDENTITY_SHA256[:24]}"
    artifact_id = f"capture-current:{NEW_BODY_TEXT_SHA256[:24]}"
    for index, (field, field_hash, atom_hash, descriptor_class) in enumerate(NEW_ATOMS, 1):
        assertion_id = stable_id("assertion-current", f"{BATCH_ID}|{effective_id}|{field}|{atom_hash}|{index}")
        rows.append(
            {
                "descriptor_assertion_id": assertion_id,
                "source_dataset_id": "current-targeted-acquisition-hash-ledger",
                "source_artifact_id": artifact_id,
                "source_file_sha256": NEW_BODY_TEXT_SHA256,
                "source_route_id": "route.coe.brazil-pulped-naturals-2009.generic-official-field",
                "source_family_id": "family.ace_cup_of_excellence",
                "organizer_id": "organizer.coe",
                "competition_series_id": "coe",
                "edition_id": "brazil-pulped-naturals-2009",
                "edition_year": "2009",
                "category_id": "pulped-naturals",
                "round_id": "competition-final",
                "entry_or_lot_id": "coe-brazil-pulped-naturals-2009-rank-21",
                "coffee_identity_id": f"coffee-current:{NEW_RECORD_IDENTITY_SHA256[:24]}",
                "preparation_service_id": "unresolved_preparation_service",
                "effective_record_id": effective_id,
                "publication_layer": "GENERIC_ORGANIZER_SENSORY_FIELD",
                "source_field_label": field,
                "source_locator": f"{NEW_SOURCE_URL}#lot-information",
                "raw_source_text_or_restricted_pointer": f"hash:sha256:{field_hash}",
                "atomic_source_text_or_restricted_pointer": f"hash:sha256:{atom_hash}",
                "source_language": "en",
                "descriptor_class": descriptor_class,
                "source_native_lexical_form_or_restricted_pointer": f"hash:sha256:{atom_hash}",
                "normalized_descriptor_candidate_id": "",
                "evidence_tier": "UNRESOLVED",
                "provenance_state": "OFFICIAL_FIELD_ORIGIN_UNRESOLVED",
                "rights_state": "UNKNOWN",
                "review_state": "PROVISIONAL_MACHINE_CLASSIFIED",
                "corpus_state": "HUMAN_REVIEW_REQUIRED",
                "evidence_stratum": "C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED",
                "duplicate_group_id": "",
                "mirror_group_id": "",
                "repeat_group_id": "",
                "same_coffee_cross_observation_group_id": "",
                "c0_source_status": "SOURCE_UNKNOWN",
                "c0_family": "",
                "c1_source_status": "SOURCE_UNKNOWN",
                "source_native_roast_value": "",
                "reviewed_c1_mapping": "",
                "source_commit_sha": "NA_EXTERNAL_CAPTURE_NOT_FROM_GIT",
                "parser_version": "current.field-parser.v1",
                "adapter_version": "current.targeted-browser-audit.v1",
                "created_at": f"{BATCH_DATE}T00:00:00+10:00",
                "counts_as_assertion": True,
                "counts_as_record_unique_descriptor": True,
                "model_eligible": False,
                "source_field_text_sha256": field_hash,
                "atomic_source_text_sha256": atom_hash,
                "source_text_storage_state": "HASH_ONLY",
                "source_text_non_storage_reason": "RIGHTS_UNKNOWN_PUBLIC_REPOSITORY_RETAINS_HASH_AND_LOCATOR_ONLY",
            }
        )

    for source in read_tsv(BATCH2_SIDECAR):
        tier = source["evidence_tier"]
        collection_tier = source["collection_tier"]
        if collection_tier == "GOLD":
            stratum = "A_GOLD_CANDIDATE_REVIEW_OR_RIGHTS_BLOCKED"
        elif collection_tier == "SILVER":
            stratum = "C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED"
        else:
            stratum = "D_BRONZE_AUXILIARY_PROFESSIONAL_FIELD"
        rows.append(
            {
                "descriptor_assertion_id": source["descriptor_assertion_id"],
                "source_dataset_id": "professional-descriptor-scaleup-batch2-public-safe",
                "source_artifact_id": f"artifact-b2:{source['source_artifact_sha256'][:24]}",
                "source_file_sha256": source["source_artifact_sha256"],
                "source_route_id": source["source_route_id"],
                "source_family_id": source["source_family_id"],
                "organizer_id": stable_id("organizer-b2", source["publisher"]),
                "competition_series_id": source["source_family_id"],
                "edition_id": stable_id(
                    "edition-b2",
                    f"{source['source_route_id']}|{source['edition_or_release']}",
                ),
                "edition_year": source["edition_year"] or "UNREPORTED",
                "category_id": "professional-sensory-record",
                "round_id": "source-publication",
                "entry_or_lot_id": source["effective_record_id"],
                "coffee_identity_id": source["coffee_identity_id"],
                "preparation_service_id": source["preparation_service"],
                "effective_record_id": source["effective_record_id"],
                "publication_layer": source["publication_layer"],
                "source_field_label": source["source_field_label"],
                "source_locator": source["source_locator"],
                "raw_source_text_or_restricted_pointer": (
                    f"hash:sha256:{source['raw_field_text_sha256']}"
                ),
                "atomic_source_text_or_restricted_pointer": (
                    f"hash:sha256:{source['atomic_source_text_sha256']}"
                ),
                "source_language": source["source_language"],
                "descriptor_class": source["descriptor_class"],
                "source_native_lexical_form_or_restricted_pointer": (
                    f"hash:sha256:{source['source_native_form_sha256']}"
                ),
                "normalized_descriptor_candidate_id": source[
                    "provisional_normalized_form_id"
                ],
                "evidence_tier": tier,
                "provenance_state": source["provenance_state"],
                "rights_state": source["rights_state"],
                "review_state": "PROVISIONAL_MACHINE_CLASSIFIED",
                "corpus_state": "CANDIDATE_ONLY_HUMAN_REVIEW_REQUIRED",
                "evidence_stratum": stratum,
                "duplicate_group_id": (
                    "CROSS_BATCH_PUBLICATION_LAYER_OVERLAP"
                    if source["counts_as_assertion"] == "false"
                    else ""
                ),
                "mirror_group_id": "",
                "repeat_group_id": "",
                "same_coffee_cross_observation_group_id": "",
                "c0_source_status": "SOURCE_UNKNOWN",
                "c0_family": "",
                "c1_source_status": "SOURCE_UNKNOWN",
                "source_native_roast_value": source[
                    "roast_evidence_sha256_or_state"
                ],
                "reviewed_c1_mapping": "",
                "source_commit_sha": "NA_GENERATED_IN_CURRENT_RESEARCH_BRANCH",
                "parser_version": "batch2.professional-source-parser.v1",
                "adapter_version": "batch2.public-safe-sidecar.v1",
                "created_at": f"{BATCH_DATE}T00:00:00+10:00",
                "counts_as_assertion": source["counts_as_assertion"],
                "counts_as_record_unique_descriptor": source[
                    "counts_as_record_unique_descriptor"
                ],
                "model_eligible": False,
                "source_field_text_sha256": source["raw_field_text_sha256"],
                "atomic_source_text_sha256": source["atomic_source_text_sha256"],
                "source_text_storage_state": source["source_text_storage_state"],
                "source_text_non_storage_reason": (
                    "RIGHTS_AND_REVIEW_BOUNDARY_HASH_ONLY_PUBLIC"
                ),
            }
        )
    return rows


def view_rows(ledger: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    deinf = [row for row in ledger if scalar(row["counts_as_assertion"]) == "true"]
    return {
        "ALL_PROFESSIONAL_CANDIDATES": deinf,
        "SOURCE_AUDITED_CANDIDATES": deinf,
        "GOLD_CANDIDATES": [
            row
            for row in deinf
            if row["evidence_stratum"].startswith(("A_", "B_"))
        ],
        "SILVER_CANDIDATES": [
            row for row in deinf if row["evidence_stratum"].startswith("C_")
        ],
        "BRONZE_CANDIDATES": [
            row for row in deinf if row["evidence_stratum"].startswith("D_")
        ],
        "HUMAN_REVIEWED_P1_P2": [],
        "CORE_ELIGIBLE": [],
        "MODEL_ELIGIBLE": [],
        "P3_P4_AUXILIARY": [
            row for row in deinf if row["evidence_tier"] in {"P3", "P4"}
        ],
        "PROVENANCE_UNRESOLVED": [
            row for row in deinf if row["evidence_tier"] == "UNRESOLVED"
        ],
        "RIGHTS_BLOCKED": [row for row in deinf if row["rights_state"] in {"PENDING", "UNKNOWN"}],
    }


def pair_metrics(ledger: list[dict[str, Any]]) -> dict[str, Any]:
    pair_records: dict[tuple[str, str], set[str]] = defaultdict(set)
    pair_families: dict[tuple[str, str], set[str]] = defaultdict(set)
    pair_years: dict[tuple[str, str], set[str]] = defaultdict(set)
    per_record: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in ledger:
        if scalar(row["counts_as_record_unique_descriptor"]) != "true":
            continue
        identity = row["normalized_descriptor_candidate_id"]
        if not identity:
            identity = f"source-hash:{row['atomic_source_text_sha256']}"
        per_record[row["effective_record_id"]][identity] = row

    event_count = 0
    provisional_event_count = 0
    provisional_pairs: set[tuple[str, str]] = set()
    provisional_pair_families: dict[tuple[str, str], set[str]] = defaultdict(set)
    provisional_pair_years: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record_id, identities in per_record.items():
        for left, right in itertools.combinations(sorted(identities), 2):
            pair = (left, right)
            source = identities[left]
            pair_records[pair].add(record_id)
            pair_families[pair].add(source["source_family_id"])
            pair_years[pair].add(source["edition_year"])
            event_count += 1
            if not left.startswith("source-hash:") and not right.startswith("source-hash:"):
                provisional_event_count += 1
                provisional_pairs.add(pair)
                provisional_pair_families[pair].add(source["source_family_id"])
                provisional_pair_years[pair].add(source["edition_year"])
    return {
        "pair_event_count": event_count,
        "unique_supported_pair_count": len(pair_records),
        "pair_with_multi_family_support_count": sum(len(value) > 1 for value in pair_families.values()),
        "pair_with_multi_year_support_count": sum(len(value) > 1 for value in pair_years.values()),
        "set_level_coassertion_record_count": sum(len(value) > 1 for value in per_record.values()),
        "provisional_normalized_pair_event_count": provisional_event_count,
        "unique_provisional_normalized_pair_count": len(provisional_pairs),
        "provisional_pair_with_multi_family_support_count": sum(
            len(value) > 1 for value in provisional_pair_families.values()
        ),
        "provisional_pair_with_multi_year_support_count": sum(
            len(value) > 1 for value in provisional_pair_years.values()
        ),
    }


def write_inventory_outputs(rows: list[dict[str, Any]]) -> None:
    fields = [
        "dataset_id", "dataset_name", "source_round_or_batch", "source_branch",
        "source_commit_sha", "repository_path_or_restricted_locator", "file_sha256",
        "file_size", "row_count", "descriptor_candidate_row_count", "effective_record_count",
        "data_role", "evidence_tiers_present", "rights_state", "review_state",
        "contains_raw_source_text", "public_commit_allowed", "overlap_expected_with",
        "current_disposition",
    ]
    write_tsv("DATASET_INVENTORY.tsv", fields, rows)
    lineage_fields = [
        "dataset_id", "source_round_or_batch", "source_branch", "source_commit_sha",
        "data_role", "overlap_expected_with", "current_disposition",
        "repository_path_or_restricted_locator", "file_sha256",
    ]
    write_tsv("DATASET_ROLE_AND_LINEAGE.tsv", lineage_fields, rows)


def write_merge_outputs(ledger: list[dict[str, Any]], pairs: dict[str, Any]) -> dict[str, Any]:
    deinf = [row for row in ledger if scalar(row["counts_as_assertion"]) == "true"]
    record_unique = [row for row in ledger if scalar(row["counts_as_record_unique_descriptor"]) == "true"]
    classes = Counter(row["descriptor_class"] for row in deinf)
    tiers = Counter(row["evidence_tier"] for row in deinf)
    rights = Counter(row["rights_state"] for row in deinf)
    records = {row["effective_record_id"] for row in deinf}
    native_forms = {row["atomic_source_text_sha256"] for row in deinf}
    normalized_forms = {
        row["normalized_descriptor_candidate_id"]
        for row in deinf
        if row["normalized_descriptor_candidate_id"]
    }
    routes = {row["source_route_id"] for row in deinf}
    families = Counter(row["source_family_id"] for row in deinf)
    years = {row["edition_year"] for row in deinf}
    editions = {row["edition_id"] for row in deinf}
    largest_family_share = max(families.values()) / len(deinf)
    # Use one integer-ratio division so Python 3.11 and 3.12+ serialize the
    # same value. Python 3.12 changed float summation and otherwise shifts the
    # final digit of this derived receipt.
    source_family_hhi = sum(count * count for count in families.values()) / (
        len(deinf) * len(deinf)
    )
    sidecar_rows = read_tsv(BATCH2_SIDECAR)
    judge_observations = {
        (row["effective_record_id"], row["judge_observation_id_sha256"])
        for row in sidecar_rows
        if row["counts_as_assertion"] == "true"
        and row["judge_observation_id_sha256"]
    }
    collection = Counter(
        "GOLD"
        if row["evidence_stratum"].startswith(("A_", "B_"))
        else "SILVER"
        if row["evidence_stratum"].startswith("C_")
        else "BRONZE"
        for row in deinf
    )
    metrics = {
        "raw_segmented": len(ledger),
        "assertion_deinflated": len(deinf),
        "record_unique": len(record_unique),
        "effective_records": len(records),
        "strict": classes["STRICT_FLAVOR"],
        "broad": classes["BROAD_SENSORY"],
        "p1": tiers["P1"], "p2": tiers["P2"], "p3": tiers["P3"], "p4": tiers["P4"],
        "unresolved": tiers["UNRESOLVED"],
        "source_native_forms": len(native_forms),
        "normalized_forms": len(normalized_forms),
        "provisional_mapping_coverage_count": sum(
            bool(row["normalized_descriptor_candidate_id"]) for row in deinf
        ),
        "provisional_mapping_coverage_rate": sum(
            bool(row["normalized_descriptor_candidate_id"]) for row in deinf
        )
        / len(deinf),
        "unmapped": sum(not row["normalized_descriptor_candidate_id"] for row in deinf),
        "source_routes": len(routes),
        "source_families": len(families),
        "largest_family_share": largest_family_share,
        "source_family_hhi": source_family_hhi,
        "edition_count": len(editions),
        "year_count": len(years),
        "rights_pending": rights["PENDING"],
        "rights_unknown": rights["UNKNOWN"],
        "rights_affirmative": rights["AFFIRMATIVE"],
        "rights_prohibited": rights["PROHIBITED"],
        "gold": collection["GOLD"],
        "silver": collection["SILVER"],
        "bronze": collection["BRONZE"],
        "judge_observations": len(judge_observations),
        "model_eligible": sum(scalar(row["model_eligible"]) == "true" for row in deinf),
        **pairs,
    }
    receipt_rows = [
        ("RAW_SEGMENTED_DESCRIPTOR_ASSERTION_COUNT", metrics["raw_segmented"], "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("ASSERTION_LEVEL_DEINFLATED_COUNT", metrics["assertion_deinflated"], "counts_as_assertion=true"),
        ("EFFECTIVE_RECORD_LEVEL_UNIQUE_DESCRIPTOR_COUNT", metrics["record_unique"], "counts_as_record_unique_descriptor=true"),
        ("DESCRIPTOR_BEARING_EFFECTIVE_RECORD_COUNT", metrics["effective_records"], "distinct effective_record_id"),
        ("JUDGE_OR_OBSERVATION_LEVEL_COUNT", metrics["judge_observations"], "Distinct effective-record and public-safe judge-observation hash pairs."),
        ("SET_LEVEL_COASSERTION_RECORD_COUNT", pairs["set_level_coassertion_record_count"], "records with at least two de-inflated source atoms"),
        ("PAIR_EDGE_EVENT_COUNT", pairs["pair_event_count"], "Round 3M events plus current record combinations"),
        ("UNIQUE_SUPPORTED_PAIR_COUNT", pairs["unique_supported_pair_count"], "unique sorted source-atom hash pairs"),
        ("PROVISIONAL_NORMALIZED_PAIR_EVENT_COUNT", pairs["provisional_normalized_pair_event_count"], "complete-record combinations of provisional normalized targets"),
        ("UNIQUE_PROVISIONAL_NORMALIZED_PAIR_COUNT", pairs["unique_provisional_normalized_pair_count"], "unique provisional normalized target pairs"),
        ("PROVISIONAL_PAIRS_WITH_MULTI_FAMILY_SUPPORT", pairs["provisional_pair_with_multi_family_support_count"], "provisional target pairs supported by more than one source family"),
        ("PROVISIONAL_PAIRS_WITH_MULTI_YEAR_SUPPORT", pairs["provisional_pair_with_multi_year_support_count"], "provisional target pairs supported in more than one year"),
        ("STRICT_FLAVOR_ASSERTION_COUNT", metrics["strict"], "assertion-level de-inflated"),
        ("BROAD_SENSORY_ASSERTION_COUNT", metrics["broad"], "assertion-level de-inflated"),
        ("P1_ASSERTION_COUNT", metrics["p1"], "assertion-level de-inflated"),
        ("P2_ASSERTION_COUNT", metrics["p2"], "assertion-level de-inflated"),
        ("P3_ASSERTION_COUNT", metrics["p3"], "assertion-level de-inflated"),
        ("P4_ASSERTION_COUNT", metrics["p4"], "assertion-level de-inflated"),
        ("PROVENANCE_UNRESOLVED_ASSERTION_COUNT", metrics["unresolved"], "assertion-level de-inflated"),
        ("GOLD_CANDIDATE_ASSERTION_COUNT", metrics["gold"], "candidate collection tier; not model eligibility"),
        ("SILVER_CANDIDATE_ASSERTION_COUNT", metrics["silver"], "candidate collection tier; not model eligibility"),
        ("BRONZE_CANDIDATE_ASSERTION_COUNT", metrics["bronze"], "candidate collection tier; not model eligibility"),
        ("SOURCE_NATIVE_HASH_IDENTITY_COUNT", metrics["source_native_forms"], "restricted lexical forms counted by SHA-256 identity"),
        ("PROVISIONAL_NORMALIZED_DESCRIPTOR_FORM_COUNT", metrics["normalized_forms"], "Machine-proposed identities; not reviewed canonical labels."),
        ("PROVISIONAL_MAPPING_COVERAGE_COUNT", metrics["provisional_mapping_coverage_count"], "Assertions with a machine-proposed normalization identity."),
        ("PROVISIONAL_MAPPING_COVERAGE_RATE", f"{metrics['provisional_mapping_coverage_rate']:.6f}", "Machine-proposed coverage only."),
        ("REVIEWED_NORMALIZED_DESCRIPTOR_FORM_COUNT", 0, "No source atoms have a reviewed canonical mapping."),
        ("UNMAPPED_DESCRIPTOR_ASSERTION_COUNT", metrics["unmapped"], "Baseline hash-only assertions remain unmapped."),
        ("MODEL_ELIGIBLE_ASSERTION_COUNT", metrics["model_eligible"], "Requires review, provenance, rights, and distribution gates."),
    ]
    write_tsv("DESCRIPTOR_MERGE_RECEIPT.tsv", ["metric", "observed_value", "basis"], [dict(zip(("metric", "observed_value", "basis"), row)) for row in receipt_rows])

    overlap = [
        ("ROUND3_EXTERNAL_DESCRIPTOR_RECEIPT", "ROUND3M_LIVE_PILOT", "OVERLAP_NOT_COMPUTABLE", "Machine-readable census bundle missing; headline counts are not added."),
        ("ROUND3M_LIVE_PILOT", "ROUND3L_RESTRICTED_STAGING", "PARTIAL_LINEAGE_RELATION_NOT_ARITHMETIC_MERGE", "Round 3M review artifacts inherit Round 3L staging lineage; the 140 live assertions are separate governed captures."),
        ("ROUND3M_LIVE_PILOT", "ROUND4A_DERIVED_GRAPH", "EXACT_DERIVED_SUBSET", "Round 4A reuses 140 assertions, 8 records and 508 pair events; added observation count is zero."),
        ("ROUND3M_LIVE_PILOT", "CURRENT_NORMALIZED_EXPRESSION_ASSETS", "REFERENCE_ONLY_NO_OBSERVATION_OVERLAP", "Language expressions are not coffee observations and are not promoted."),
        ("ROUND3M_LIVE_PILOT", "CURRENT_TARGETED_ACQUISITION", "NO_EFFECTIVE_RECORD_LOCATOR_OVERLAP_FOUND", "The 2009 official listing is absent from the eight-record live pilot."),
        ("CURRENT_TARGETED_ACQUISITION", "CURRENT_TARGETED_ARCHIVE_INDEX", "SAME_PUBLICATION_FIELD_REEXPORT", "Archive excerpt was discovery-only; detail structured fields are the sole segmented source."),
        ("CURRENT_TARGETED_ACQUISITION", "PROFESSIONAL_DESCRIPTOR_SCALEUP_BATCH2", "SAME_PUBLICATION_LAYER_SUPERSEDED_BY_EXISTING_CURRENT_RECORD", "The known Batch 1 detail URL is retained as a false-count audit copy in Batch 2."),
    ]
    write_tsv("DESCRIPTOR_OVERLAP_MAP.tsv", ["left_dataset", "right_dataset", "overlap_decision", "basis"], [dict(zip(("left_dataset", "right_dataset", "overlap_decision", "basis"), row)) for row in overlap])

    batch2_manifest = json.loads(BATCH2_MANIFEST.read_text(encoding="utf-8"))
    duplicate_rows = [
        ("ROUND3M_EXACT_WITHIN_FIELD_REPEAT", 1, "ASSERTION_LEVEL", "Removed from assertion-level count."),
        ("ROUND3M_CROSS_OBSERVATION_REPEAT", 2, "EFFECTIVE_RECORD_UNIQUE", "Retained as assertions; excluded from record-unique count."),
        ("ROUND4A_DERIVED_PAIR_VIEW", 508, "PAIR_EVENT", "Derived pair events add zero source observations."),
        ("CURRENT_ARCHIVE_INDEX_REEXPORT", 1, "PRE_SEGMENTATION_PUBLICATION_LAYER", "Index excerpt not segmented; detail field is canonical."),
        ("CURRENT_TARGETED_ASSERTION_DUPLICATE_LOSS", 0, "ASSERTION_LEVEL", "No repeat among the 18 canonical structured-field atoms."),
        ("BATCH2_ASSERTION_DUPLICATE_LOSS", batch2_manifest["assertion_duplicate_losses"], "ASSERTION_LEVEL", "Within-batch and cross-batch publication-layer losses retained as false-count audit rows."),
        ("BATCH2_CROSS_BATCH_PUBLICATION_LAYER_LOSS", batch2_manifest["cross_batch_publication_layer_duplicate_losses"], "ASSERTION_LEVEL", "Existing current publication supersedes the Batch 2 reinspection."),
        ("BATCH2_RECORD_LEVEL_REPEAT_LOSS", batch2_manifest["record_level_repeat_losses"], "EFFECTIVE_RECORD_UNIQUE", "Assertions retained; repeated provisional target within an effective record excluded from record-unique count."),
    ]
    write_tsv("DESCRIPTOR_DUPLICATE_RECEIPT.tsv", ["duplicate_type", "count", "count_surface", "disposition"], [dict(zip(("duplicate_type", "count", "count_surface", "disposition"), row)) for row in duplicate_rows])
    return metrics


def write_distributions(ledger: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    views = view_rows(ledger)
    descriptor_fields = [
        "corpus_view", "normalized_descriptor_candidate_id", "assertion_count",
        "effective_record_count", "coffee_identity_count", "source_family_count",
        "source_route_count", "edition_count", "year_count", "preparation_service_count",
        "c0_family_count", "direct_source_roast_count", "reviewed_c1_count", "p1_count",
        "p2_count", "p3_count", "p4_count", "unresolved_count", "rights_affirmative_count",
        "rights_pending_count", "rights_unknown_count", "human_reviewed_count",
        "gold_candidate_count", "silver_candidate_count", "bronze_candidate_count",
        "multi_target_record_count", "supported_pair_event_count",
    ]
    descriptor_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []

    bands = (
        ("SINGLETON", 1, 1, "1"),
        ("VERY_LOW", 2, 4, "2-4"),
        ("LOW", 5, 9, "5-9"),
        ("EMERGING", 10, 19, "10-19"),
        ("USABLE", 20, 49, "20-49"),
        ("STRONG", 50, 99, "50-99"),
        ("HIGH_SUPPORT", 100, 10**12, "100+"),
    )
    for view_name, rows in views.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        record_targets: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            target = row["normalized_descriptor_candidate_id"]
            if not target:
                continue
            groups[target].append(row)
            record_targets[row["effective_record_id"]].add(target)
        support_band_counts: Counter[str] = Counter()
        for target, group in sorted(groups.items()):
            records = {row["effective_record_id"] for row in group}
            record_support = len(records)
            for band, lower, upper, _ in bands:
                if lower <= record_support <= upper:
                    support_band_counts[band] += 1
                    break
            gold = sum(
                row["evidence_stratum"].startswith(("A_", "B_")) for row in group
            )
            silver = sum(row["evidence_stratum"].startswith("C_") for row in group)
            bronze = sum(row["evidence_stratum"].startswith("D_") for row in group)
            descriptor_rows.append(
                {
                    "corpus_view": view_name,
                    "normalized_descriptor_candidate_id": target,
                    "assertion_count": len(group),
                    "effective_record_count": record_support,
                    "coffee_identity_count": len({row["coffee_identity_id"] for row in group}),
                    "source_family_count": len({row["source_family_id"] for row in group}),
                    "source_route_count": len({row["source_route_id"] for row in group}),
                    "edition_count": len({row["edition_id"] for row in group}),
                    "year_count": len({row["edition_year"] for row in group}),
                    "preparation_service_count": len({row["preparation_service_id"] for row in group}),
                    "c0_family_count": len({row["c0_family"] for row in group if row["c0_family"]}),
                    "direct_source_roast_count": sum(
                        row["source_native_roast_value"].startswith("hash:sha256:")
                        for row in group
                    ),
                    "reviewed_c1_count": sum(bool(row["reviewed_c1_mapping"]) for row in group),
                    "p1_count": sum(row["evidence_tier"] == "P1" for row in group),
                    "p2_count": sum(row["evidence_tier"] == "P2" for row in group),
                    "p3_count": sum(row["evidence_tier"] == "P3" for row in group),
                    "p4_count": sum(row["evidence_tier"] == "P4" for row in group),
                    "unresolved_count": sum(row["evidence_tier"] == "UNRESOLVED" for row in group),
                    "rights_affirmative_count": sum(row["rights_state"] == "AFFIRMATIVE" for row in group),
                    "rights_pending_count": sum(row["rights_state"] == "PENDING" for row in group),
                    "rights_unknown_count": sum(row["rights_state"] == "UNKNOWN" for row in group),
                    "human_reviewed_count": 0,
                    "gold_candidate_count": gold,
                    "silver_candidate_count": silver,
                    "bronze_candidate_count": bronze,
                    "multi_target_record_count": sum(
                        len(record_targets[record_id]) >= 2 for record_id in records
                    ),
                    "supported_pair_event_count": sum(
                        max(len(record_targets[record_id]) - 1, 0) for record_id in records
                    ),
                }
            )
        for band, _, _, definition in bands:
            support_rows.append(
                {
                    "corpus_view": view_name,
                    "support_band": band,
                    "effective_record_support": definition,
                    "descriptor_count": support_band_counts[band],
                    "reason": "PROVISIONAL_MACHINE_NORMALIZATION_NOT_HUMAN_REVIEWED",
                }
            )
    write_tsv("DESCRIPTOR_DISTRIBUTION.tsv", descriptor_fields, descriptor_rows)

    write_tsv("DESCRIPTOR_SUPPORT_BANDS.tsv", ["corpus_view", "support_band", "effective_record_support", "descriptor_count", "reason"], support_rows)

    family_rows: list[dict[str, Any]] = []
    year_rows: list[dict[str, Any]] = []
    for view_name, rows in views.items():
        family_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        year_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            family_groups[row["source_family_id"]].append(row)
            year_groups[row["edition_year"]].append(row)
        for family, group in sorted(family_groups.items()):
            family_rows.append({"corpus_view": view_name, "source_family_id": family, "assertion_count": len(group), "effective_record_count": len({row["effective_record_id"] for row in group}), "share": f"{len(group) / len(rows):.6f}"})
        for year, group in sorted(year_groups.items()):
            year_rows.append({"corpus_view": view_name, "edition_year": year, "assertion_count": len(group), "effective_record_count": len({row["effective_record_id"] for row in group}), "source_family_count": len({row["source_family_id"] for row in group})})
    write_tsv("DESCRIPTOR_SOURCE_FAMILY_DISTRIBUTION.tsv", ["corpus_view", "source_family_id", "assertion_count", "effective_record_count", "share"], family_rows)
    write_tsv("DESCRIPTOR_YEAR_DISTRIBUTION.tsv", ["corpus_view", "edition_year", "assertion_count", "effective_record_count", "source_family_count"], year_rows)

    deinf = views["ALL_PROFESSIONAL_CANDIDATES"]
    prep = Counter(row["preparation_service_id"] for row in deinf)
    prep_rows = [{"preparation_service": key, "assertion_count": count, "effective_record_count": len({row["effective_record_id"] for row in deinf if row["preparation_service_id"] == key})} for key, count in sorted(prep.items())]
    write_tsv("DESCRIPTOR_PREPARATION_DISTRIBUTION.tsv", ["preparation_service", "assertion_count", "effective_record_count"], prep_rows)
    roast_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in deinf:
        value = row["source_native_roast_value"]
        state = "DIRECT_SOURCE_ROAST_HASH" if value.startswith("hash:sha256:") else value or "UNREPORTED"
        roast_groups[state].append(row)
    write_tsv(
        "DESCRIPTOR_ROAST_EVIDENCE_DISTRIBUTION.tsv",
        ["roast_evidence_state", "assertion_count", "effective_record_count"],
        [
            {
                "roast_evidence_state": state,
                "assertion_count": len(group),
                "effective_record_count": len({row["effective_record_id"] for row in group}),
            }
            for state, group in sorted(roast_groups.items())
        ],
    )
    rights = Counter(row["rights_state"] for row in deinf)
    write_tsv("DESCRIPTOR_RIGHTS_DISTRIBUTION.tsv", ["rights_state", "assertion_count", "model_eligible_count"], [{"rights_state": state, "assertion_count": rights[state], "model_eligible_count": 0} for state in ("AFFIRMATIVE", "PENDING", "UNKNOWN", "PROHIBITED")])
    review = Counter(row["review_state"] for row in deinf)
    write_tsv("DESCRIPTOR_REVIEW_DISTRIBUTION.tsv", ["review_state", "assertion_count", "human_reviewed", "expert_adjudicated"], [{"review_state": state, "assertion_count": count, "human_reviewed": state == "HUMAN_CONFIRMED", "expert_adjudicated": state == "EXPERT_ADJUDICATED"} for state, count in sorted(review.items())])

    direct_roast_records = len(
        {
            row["effective_record_id"]
            for row in deinf
            if row["source_native_roast_value"].startswith("hash:sha256:")
        }
    )
    provisional_multi_target_records = metrics["set_level_coassertion_record_count"]
    gaps = [
        ("reviewed_p1_p2_strict_assertions", 0, 500, 500, "REVIEW|RIGHTS", "Minimum deterministic evaluation checkpoint"),
        ("reviewed_normalized_forms", 0, 75, 75, "REVIEW|NORMALIZATION", f"{metrics['normalized_forms']} provisional machine mappings exist; none are human reviewed"),
        ("independent_core_source_families", 0, 3, 3, "RIGHTS|REVIEW", f"{metrics['source_families']} candidate families exist; none are core eligible"),
        ("descriptor_bearing_effective_records", metrics["effective_records"], 500, max(500 - metrics["effective_records"], 0), "NONE_IF_COUNT_ONLY", "Candidate record checkpoint reached; eligibility remains separate"),
        ("multi_target_records", provisional_multi_target_records, 500, max(500 - provisional_multi_target_records, 0), "REVIEW", "Provisional target sets are machine mapped and not reviewed"),
        ("direct_source_roast_records", direct_roast_records, 1, max(1 - direct_roast_records, 0), "DISTRIBUTION", "Direct roast evidence is concentrated in one source family"),
        ("filter_or_pour_over_records", 0, 1, 1, "ACQUISITION", "Preparation service unresolved"),
        ("espresso_records", 0, 1, 1, "ACQUISITION", "Preparation service unresolved"),
        ("rights_affirmative_model_assertions", 0, 1, 1, "RIGHTS|REVIEW", f"{metrics['rights_affirmative']} candidate assertions have affirmative noncommercial research rights but remain unreviewed"),
        ("held_out_source_family", 0, 1, 1, "DISTRIBUTION|RIGHTS|REVIEW", f"{metrics['source_families']} candidate families and zero eligible held-out families"),
    ]
    write_tsv("DESCRIPTOR_GAP_MATRIX.tsv", ["distribution_cell", "observed", "next_checkpoint_required", "gap", "blocker", "note"], [dict(zip(("distribution_cell", "observed", "next_checkpoint_required", "gap", "blocker", "note"), row)) for row in gaps])


def write_acquisition_outputs(
    ledger: list[dict[str, Any]], metrics: dict[str, Any]
) -> None:
    queue_fields = ["priority_tier", "target_descriptor_or_family", "current_effective_record_support", "current_source_family_support", "current_year_support", "current_preparation_support", "current_evidence_tier", "current_rights_state", "target_source_route", "expected_descriptor_yield", "expected_distribution_improvement", "known_provenance_risk", "known_rights_risk", "estimated_review_cost", "stop_condition"]
    queue = [
        ("P1", "ACTIVE_PROVISIONAL_NORMALIZATION_CLUSTERS", metrics["effective_records"], metrics["source_families"], metrics["year_count"], 1, "P1|P2|P4|UNRESOLVED", "AFFIRMATIVE|PENDING|UNKNOWN", "OWNER_CONTROLLED_RESTRICTED_CLUSTER_REVIEW", "NA_REVIEW_ROUTE", "REVIEWED_LABEL_SUPPORT_AND_PAIR_ELIGIBILITY", "LOW_IF_SOURCE_TEXT_VERIFIED", "UNCHANGED", "MAX_200_ACTIVE_CLUSTERS", "ONE_REVIEW_PACKET_MAX_200"),
        ("P1", "OFFICIAL_FIELD_ORIGIN_RESOLUTION", metrics["effective_records"], 1, metrics["year_count"], 1, "UNRESOLVED", "UNKNOWN", "ORGANIZER_PROVENANCE_REQUEST_FOR_GENERIC_AND_FREQUENCY_FIELDS", "NA_PROVENANCE_ROUTE", "SILVER_TO_GOLD_RECLASSIFICATION_IF_EVIDENCE_SUPPORTS", "HIGH_UNTIL_ORIGIN_CONFIRMED", "UNKNOWN", "UNKNOWN", "STOP_AT_RESPONSE_OR_POLICY_DECISION"),
        ("P1", "RIGHTS_CLEARANCE_FOR_REVIEWED_P1_P2", 0, metrics["source_families"], metrics["year_count"], 1, "P1|P2", "AFFIRMATIVE|PENDING", "PURPOSE_SPECIFIC_RIGHTS_REVIEW", "NA_RIGHTS_ROUTE", "MODEL_ELIGIBILITY_CANDIDATE_POOL", "UNCHANGED", "HIGH", "UNKNOWN", "STOP_AT_DOCUMENTED_PURPOSE_DECISION"),
        ("P2", "FILTER_OR_POUR_OVER_JUDGE_FIELDS", 0, 0, 0, 0, "NONE", "UNKNOWN", "FILLED_OFFICIAL_BREWERS_CUP_SCORESHEET_OR_JUDGE_FEEDBACK", "UNKNOWN_NO_MEASURED_ROUTE_YIELD", "PREPARATION_DIVERSITY", "MEDIUM", "UNKNOWN", "UNKNOWN", "ONE_BOUNDED_EDITION_FIELD_SCHEMA"),
        ("P2", "ESPRESSO_JUDGE_FIELDS", 0, 0, 0, 0, "NONE", "UNKNOWN", "FILLED_OFFICIAL_BARISTA_OR_ESPRESSO_JUDGE_FEEDBACK", "UNKNOWN_NO_MEASURED_ROUTE_YIELD", "PREPARATION_DIVERSITY", "MEDIUM", "UNKNOWN", "UNKNOWN", "ONE_BOUNDED_EDITION_FIELD_SCHEMA"),
        ("P3", "ADDITIONAL_INDEPENDENT_PROFESSIONAL_FAMILY", 0, metrics["source_families"], metrics["year_count"], 1, "NONE", "UNKNOWN", "FILLED_EXPLICIT_PROFESSIONAL_PANEL_OR_JUDGE_FIELDS", "UNKNOWN_NO_MEASURED_ROUTE_YIELD", "SOURCE_FAMILY_CONCENTRATION_AND_HELD_OUT_FEASIBILITY", "MEDIUM", "UNKNOWN", "UNKNOWN", "ONE_BOUNDED_ROUTE_STRATUM"),
    ]
    write_tsv("TARGETED_ACQUISITION_QUEUE.tsv", queue_fields, [dict(zip(queue_fields, row)) for row in queue])

    route_rows = read_tsv(BATCH2_ROUTES)
    result_fields = ["targeted_batch_id", *route_rows[0].keys()]
    results = [{"targeted_batch_id": BATCH_ID, **row} for row in route_rows]
    write_tsv("TARGETED_ACQUISITION_RESULT.tsv", result_fields, results)


def write_strictness_and_review(ledger: list[dict[str, Any]]) -> None:
    deinf = [row for row in ledger if scalar(row["counts_as_assertion"]) == "true"]
    unresolved = [row for row in deinf if row["evidence_tier"] == "UNRESOLVED"]
    affected_records = len({row["effective_record_id"] for row in unresolved})
    affected_classes = Counter(row["descriptor_class"] for row in unresolved)
    strict_fields = ["constraint_id", "constraint_description", "affected_source_routes", "affected_source_families", "affected_effective_record_count", "affected_strict_descriptor_count", "affected_broad_descriptor_count", "current_disposition", "core_retention_rate", "expected_retention_if_relaxed", "provenance_risk_if_relaxed", "rights_risk_if_relaxed", "duplicate_risk_if_relaxed", "safe_quarantine_alternative", "recommended_action", "user_decision_required"]
    strict_row = {
        "constraint_id": "SI-001-OFFICIAL-FIELD-ORIGIN-UNRESOLVED",
        "constraint_description": "At least 80% of each affected official-field route is quarantined because the author or jury origin is not explicit.",
        "affected_source_routes": sorted({row["source_route_id"] for row in unresolved}),
        "affected_source_families": sorted({row["source_family_id"] for row in unresolved}),
        "affected_effective_record_count": affected_records,
        "affected_strict_descriptor_count": affected_classes["STRICT_FLAVOR"],
        "affected_broad_descriptor_count": affected_classes["BROAD_SENSORY"],
        "current_disposition": "C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED;MODEL_INELIGIBLE",
        "core_retention_rate": "0.000000",
        "expected_retention_if_relaxed": "UNKNOWN_REQUIRES_OWNER_POLICY_AND_SOURCE_EVIDENCE",
        "provenance_risk_if_relaxed": "HIGH_ORIGIN_COULD_BE_PRODUCER_EDITOR_OR_AGGREGATED_PANEL",
        "rights_risk_if_relaxed": "UNCHANGED_UNKNOWN",
        "duplicate_risk_if_relaxed": "LOW_AFTER_CURRENT_PUBLICATION_LAYER_RULES",
        "safe_quarantine_alternative": "C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED",
        "recommended_action": "KEEP_AS_SILVER_CANDIDATE_AND_REQUEST_ORGANIZER_PROVENANCE",
        "user_decision_required": False,
    }
    write_tsv("STRICTNESS_IMPACT_LOG.tsv", strict_fields, [strict_row])

    review_fields = [
        "review_item_id", "priority_tier", "provisional_normalized_form_id",
        "assertion_count", "effective_record_count", "source_family_count",
        "year_count", "unresolved_assertion_count", "strict_assertion_count",
        "broad_assertion_count", "mapping_methods", "mapping_confidences",
        "mapping_bases", "rights_states", "distribution_gap_affected",
        "machine_recommendation", "reviewer_decision", "reviewer_reason",
    ]
    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in deinf:
        target = row["normalized_descriptor_candidate_id"]
        if target:
            clusters[target].append(row)
    sidecar_by_target: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_tsv(BATCH2_SIDECAR):
        if row["counts_as_assertion"] == "true":
            sidecar_by_target[row["provisional_normalized_form_id"]].append(row)

    ranked_clusters = sorted(
        clusters.items(),
        key=lambda item: (
            -len(item[1]),
            -len({row["source_family_id"] for row in item[1]}),
            -len({row["edition_year"] for row in item[1]}),
            -sum(row["evidence_tier"] == "UNRESOLVED" for row in item[1]),
            item[0],
        ),
    )
    review_rows = []
    for rank, (target, group) in enumerate(ranked_clusters[:200], 1):
        sidecar_group = sidecar_by_target[target]
        unresolved_count = sum(row["evidence_tier"] == "UNRESOLVED" for row in group)
        review_rows.append(
            {
                "review_item_id": stable_id("review-cluster-current", target),
                "priority_tier": "P1" if rank <= 50 else "P2" if rank <= 125 else "P3",
                "provisional_normalized_form_id": target,
                "assertion_count": len(group),
                "effective_record_count": len({row["effective_record_id"] for row in group}),
                "source_family_count": len({row["source_family_id"] for row in group}),
                "year_count": len({row["edition_year"] for row in group}),
                "unresolved_assertion_count": unresolved_count,
                "strict_assertion_count": sum(row["descriptor_class"] == "STRICT_FLAVOR" for row in group),
                "broad_assertion_count": sum(row["descriptor_class"] == "BROAD_SENSORY" for row in group),
                "mapping_methods": sorted({row["mapping_method"] for row in sidecar_group}),
                "mapping_confidences": sorted({row["mapping_confidence"] for row in sidecar_group}),
                "mapping_bases": sorted({row["mapping_basis"] for row in sidecar_group}),
                "rights_states": sorted({row["rights_state"] for row in group}),
                "distribution_gap_affected": "LABEL_SUPPORT|PAIR_SUPPORT|SOURCE_FAMILY|YEAR|PROVENANCE",
                "machine_recommendation": (
                    "VERIFY_CLUSTER_MEMBERSHIP_AND_CANONICAL_LABEL_OR_SPLIT_OR_ABSTAIN"
                    if unresolved_count
                    else "VERIFY_CLUSTER_MEMBERSHIP_AND_CANONICAL_LABEL_OR_ABSTAIN"
                ),
                "reviewer_decision": "",
                "reviewer_reason": "",
            }
        )
    write_tsv("REVIEW_QUEUE_RECEIPT.tsv", review_fields, review_rows)


def write_gates(metrics: dict[str, Any]) -> None:
    gates = {
        "GATE_500_EVALUATION": [
            ("candidate_corpus_assertions", metrics["assertion_deinflated"], 500, ""),
            ("candidate_effective_records", metrics["effective_records"], 100, ""),
            ("reviewed_p1_p2_strict_assertions", 0, 500, "REVIEW|RIGHTS"),
            ("reviewed_normalized_forms", 0, 75, "REVIEW|NORMALIZATION"),
            ("eligible_source_families", 0, 3, "DISTRIBUTION|RIGHTS"),
            ("complete_provenance_rate", 0, 1, "PROVENANCE|REVIEW"),
        ],
        "GATE_2000_NORMALIZATION": [
            ("candidate_corpus_assertions", metrics["assertion_deinflated"], 2000, ""),
            ("provisional_mapping_coverage_percent", int(metrics["provisional_mapping_coverage_rate"] * 100), 80, ""),
            ("reviewed_p1_p2_strict_assertions", 0, 2000, "REVIEW|RIGHTS"),
            ("eligible_descriptor_records", 0, 500, "DATA|RIGHTS"),
            ("reviewed_normalized_forms", 0, 100, "REVIEW|NORMALIZATION"),
            ("minimum_records_per_output_label", 0, 20, "DATA|NORMALIZATION"),
            ("eligible_source_families", 0, 3, "DISTRIBUTION|RIGHTS"),
        ],
        "GATE_5000_RANKING": [
            ("candidate_corpus_assertions", metrics["assertion_deinflated"], 5000, ""),
            ("reviewed_p1_p2_strict_assertions", 0, 5000, "REVIEW|RIGHTS"),
            ("eligible_descriptor_records", 0, 1000, "DATA|RIGHTS"),
            ("multi_target_records", 0, 500, "NORMALIZATION|REVIEW"),
            ("eligible_supported_pair_events", 0, 2500, "NORMALIZATION|REVIEW|RIGHTS"),
            ("eligible_source_families", 0, 4, "DISTRIBUTION|RIGHTS"),
            ("held_out_years", 0, 1, "DISTRIBUTION|RIGHTS"),
        ],
        "GATE_10000_RESEARCH_NORMALIZATION": [
            ("candidate_corpus_assertions", metrics["assertion_deinflated"], 10000, ""),
            ("reviewed_p1_p2_strict_assertions", 0, 10000, "REVIEW|RIGHTS"),
            ("eligible_descriptor_records", 0, 2500, "DATA|RIGHTS"),
            ("reviewed_normalized_forms", 0, 200, "REVIEW|NORMALIZATION"),
            ("minimum_records_per_output_label", 0, 50, "DATA|NORMALIZATION"),
            ("eligible_source_families", 0, 5, "DISTRIBUTION|RIGHTS"),
            ("held_out_source_families", 0, 2, "DISTRIBUTION|RIGHTS"),
            ("held_out_years", 0, 2, "DISTRIBUTION|RIGHTS"),
        ],
        "GATE_20000_RESEARCH_RANKING": [
            ("candidate_corpus_assertions", metrics["assertion_deinflated"], 20000, ""),
            ("reviewed_p1_p2_strict_assertions", 0, 20000, "REVIEW|RIGHTS"),
            ("eligible_descriptor_records", 0, 4000, "DATA|RIGHTS"),
            ("multi_target_records", 0, 2000, "NORMALIZATION|REVIEW"),
            ("eligible_supported_pair_events", 0, 15000, "NORMALIZATION|REVIEW|RIGHTS"),
            ("eligible_source_families", 0, 6, "DISTRIBUTION|RIGHTS"),
            ("held_out_source_families", 0, 2, "DISTRIBUTION|RIGHTS"),
            ("held_out_years", 0, 2, "DISTRIBUTION|RIGHTS"),
        ],
    }
    fields = ["gate_id", "criterion", "observed", "required", "gap", "pass", "data_blocker", "review_blocker", "rights_blocker", "distribution_blocker", "feasibility_assessment"]
    rows = []
    for gate_id, criteria in gates.items():
        for criterion, observed, required, blockers in criteria:
            rows.append({
                "gate_id": gate_id,
                "criterion": criterion,
                "observed": observed,
                "required": required,
                "gap": max(required - observed, 0),
                "pass": observed >= required,
                "data_blocker": "DATA" in blockers,
                "review_blocker": "REVIEW" in blockers,
                "rights_blocker": "RIGHTS" in blockers,
                "distribution_blocker": "DISTRIBUTION" in blockers,
                "feasibility_assessment": "FAIL_CURRENT_OPEN_REVIEWED_RIGHTS_CLEARED_CORPUS_INSUFFICIENT",
            })
        rows.append({
            "gate_id": gate_id,
            "criterion": "ALL_CRITERIA",
            "observed": 0,
            "required": len(criteria),
            "gap": len(criteria),
            "pass": False,
            "data_blocker": True,
            "review_blocker": True,
            "rights_blocker": True,
            "distribution_blocker": True,
            "feasibility_assessment": "FAIL_CANDIDATE_VOLUME_DOES_NOT_OVERRIDE_REVIEW_RIGHTS_OR_DISTRIBUTION_GATES",
        })
    write_tsv("TRAINING_GATE_STATUS.tsv", fields, rows)


def write_manifest(inventory_rows: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    role_counts = Counter(row["data_role"] for row in inventory_rows)
    batch2_manifest = json.loads(BATCH2_MANIFEST.read_text(encoding="utf-8"))
    manifest = {
        "schema": "coffee-flavor-current-descriptor-data-v1",
        "batch_id": BATCH_ID,
        "generated_date": BATCH_DATE,
        "baseline_main_sha": BASELINE_MAIN_SHA,
        "active_research_branch": "research/coffee-sensory-data-ml-readiness",
        "round4a_source_sha": ROUND4A_SHA,
        "round4a_implementation_sha": ROUND4A_IMPLEMENTATION_SHA,
        "round4a_product_files_imported": 0,
        "descriptor_census_machine_bundle_available": False,
        "descriptor_census_row_level_import_status": "BLOCKED_MISSING_MACHINE_ARTIFACTS;EXTERNAL_COUNTS_RECEIPT_ONLY",
        "schema_changed": False,
        "new_migration_count": 0,
        "model_training_run": False,
        "model_weight_file_count": 0,
        "targeted_acquisition": {
            "run": True,
            "source_route_count": batch2_manifest["source_route_count_inspected"],
            "artifact_count": batch2_manifest["artifact_count"],
            "new_descriptor_assertion_count": batch2_manifest[
                "net_new_deinflated_candidate_count"
            ],
            "new_record_unique_assertion_count": batch2_manifest[
                "record_unique_new_assertion_count"
            ],
            "new_strict_descriptor_candidate_count": batch2_manifest[
                "descriptor_class_distribution"
            ].get("STRICT_FLAVOR", 0),
            "new_broad_descriptor_candidate_count": batch2_manifest[
                "descriptor_class_distribution"
            ].get("BROAD_SENSORY", 0),
            "new_provenance_unresolved_count": batch2_manifest[
                "evidence_tier_distribution"
            ].get("UNRESOLVED", 0),
            "stop_condition": "FIRST_COMPLETE_RECORD_BOUNDARY_AT_OR_ABOVE_20000",
            "continuation_cursor": batch2_manifest["continuation_cursor"],
            "analyst_equivalent_minutes": "NA_AUTOMATED_ROUTES_REPORTED_SEPARATELY",
        },
        "metrics": metrics,
        "deltas_from_initial_current_snapshot": {
            "raw_segmented": metrics["raw_segmented"] - 158,
            "assertion_deinflated": metrics["assertion_deinflated"] - 157,
            "record_unique": metrics["record_unique"] - 155,
            "effective_records": metrics["effective_records"] - 9,
            "pair_event_count": metrics["pair_event_count"] - 661,
            "source_native_forms": metrics["source_native_forms"] - 130,
            "provisional_normalized_forms": metrics["normalized_forms"],
        },
        "dataset_inventory_count": len(inventory_rows),
        "dataset_role_counts": dict(sorted(role_counts.items())),
        "strictness_impact_triggered": True,
        "strictness_user_decision_required": False,
        "final_data_decision": "CANDIDATE_CORPUS_HARD_STOP_REACHED;MODEL_WORK_BLOCKED_BY_REVIEW_RIGHTS_PROVENANCE_AND_DISTRIBUTION_GATES",
        "phase_status": batch2_manifest["phase_status"],
        "milestone_10000_role": "HEALTHY_CANDIDATE_CORPUS_MILESTONE",
        "hard_stop_assertion_count": 20000,
        "stop_at_first_complete_record_boundary_at_or_above_20000": True,
        "full_clean_rebuild_required": False,
        "remote_ci_status": "NA_FINAL_REMOTE_SHA_NOT_AVAILABLE_INSIDE_SELF_REFERENTIAL_MANIFEST;REPORTED_IN_FINAL_RESPONSE",
        "files": [],
    }
    excluded = {"CURRENT_DATA_MANIFEST.json", "SHA256SUMS"}
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name not in excluded:
            manifest["files"].append({
                "path": path.name,
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
                "data_row_count": data_rows(path),
            })
    write_json("CURRENT_DATA_MANIFEST.json", manifest)
    checksum_paths = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.is_file():
            path.unlink()
    inventory_rows = inventory()
    ledger = canonical_ledger()
    pairs = pair_metrics(ledger)
    write_inventory_outputs(inventory_rows)
    write_tsv("CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv", LEDGER_FIELDS, ledger)
    metrics = write_merge_outputs(ledger, pairs)
    write_distributions(ledger, metrics)
    write_acquisition_outputs(ledger, metrics)
    write_strictness_and_review(ledger)
    write_gates(metrics)
    write_manifest(inventory_rows, metrics)
    subprocess.run(
        [sys.executable, str(ROOT / "db" / "scripts" / "generate-batch3-candidate-cleaning.py")],
        cwd=ROOT,
        check=True,
    )
    print(
        "CURRENT_DESCRIPTOR_DATA_PASS "
        f"inventory={len(inventory_rows)} raw={metrics['raw_segmented']} "
        f"deinflated={metrics['assertion_deinflated']} record_unique={metrics['record_unique']} "
        f"records={metrics['effective_records']} pairs={metrics['pair_event_count']}"
    )


if __name__ == "__main__":
    main()
