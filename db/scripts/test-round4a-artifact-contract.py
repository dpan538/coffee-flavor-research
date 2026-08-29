#!/usr/bin/env python3
"""Fail-closed contract checks for the public-safe Round 4A package."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db/data/round4a"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def value(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    expected = {
        "DATA_USE_REGIME.tsv", "DATASET_COMPATIBILITY_MATRIX.tsv", "TASK_DATA_HEALTH.tsv",
        "LABEL_SUPPORT_DISTRIBUTION.tsv", "SOURCE_FAMILY_CONCENTRATION.tsv", "SPLIT_FEASIBILITY.tsv",
        "PROJECT_REVIEW_PROTOCOL.tsv", "PROJECT_EXPERIMENT_MANIFEST.json", "PROFESSIONAL_REFERENCE_MANIFEST.json",
        "FIRST_PARTY_BEHAVIORAL_SCHEMA.json", "CANDIDATE_SET_FIXTURE.tsv", "TRAINING_FEASIBILITY_DECISION.json",
        "ROUND4A_MANIFEST.json", "LONGITUDINAL_ARCHIVE_EXPECTATION.tsv", "LONGITUDINAL_ARCHIVE_COMPLETENESS.tsv",
        "DESCRIPTOR_PAIR_EDGE.tsv", "DESCRIPTOR_PAIR_SUPPORT_DISTRIBUTION.tsv", "DESCRIPTOR_GRAPH_COMPONENTS.tsv",
        "DESCRIPTOR_CORPUS_HEALTH.tsv",
        "COMMUNITY_LANGUAGE_EDGE.tsv", "CANDIDATE_SET_SCORE_RECEIPT.tsv", "COHERENCE_ABLATION_PLAN.tsv",
        "COHERENCE_METRIC_STATUS.tsv", "SHA256SUMS",
    }
    check(expected == {path.name for path in DATA.iterdir() if path.is_file()}, "Round 4A output inventory drift")

    listed = {}
    for line in (DATA / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[name] = digest
    check(set(listed) == expected - {"SHA256SUMS"}, "SHA256SUMS inventory mismatch")
    for name, digest in listed.items():
        check(hashlib.sha256((DATA / name).read_bytes()).hexdigest() == digest, f"SHA mismatch: {name}")

    archive = rows("LONGITUDINAL_ARCHIVE_COMPLETENESS.tsv")
    primary = [row for row in archive if row["primary_denominator"] == "true"]
    check(len(primary) == 389, "frozen primary series-year denominator must remain 389")
    terminal = {
        "ACQUIRED_DESCRIPTOR_BEARING", "ACQUIRED_SCORE_ONLY", "ACQUIRED_RANKING_ONLY",
        "ACQUIRED_METADATA_ONLY", "ACQUIRED_PROTOCOL_ONLY", "NOT_PUBLISHED", "NOT_FOUND",
        "ACCESS_BLOCKED", "SOURCE_LOST", "SERIES_NOT_HELD", "CURRENT_YEAR_INCOMPLETE",
    }
    check(all(row["terminal_status"] in terminal for row in archive), "non-terminal archive status")
    check(all(row["terminal_status"] != "CURRENT_YEAR_INCOMPLETE" for row in primary), "2026 leaked into primary denominator")
    check(all(row["archive_rows_count_as_model_labels"] == "false" for row in archive), "archive rows promoted to labels")
    check(Counter(row["terminal_status"] for row in primary)["ACQUIRED_DESCRIPTOR_BEARING"] == 3, "descriptor-bearing year count drift")

    events = rows("../round3m/COASSERTION_EVENT.tsv") if False else []
    source_events = []
    with (ROOT / "db/data/round3m/COASSERTION_EVENT.tsv").open(newline="", encoding="utf-8") as handle:
        source_events = list(csv.DictReader(handle, delimiter="\t"))
    edges = rows("DESCRIPTOR_PAIR_EDGE.tsv")
    check(len(source_events) == 508, "professional pair event count drift")
    check(len(edges) == 506, "unique professional pair count drift")
    per_pair_record: dict[tuple[str, str, str], int] = defaultdict(int)
    for event in source_events:
        pair = tuple(sorted((event["left_atomic_source_text_sha256"], event["right_atomic_source_text_sha256"])))
        per_pair_record[(pair[0], pair[1], event["effective_record_id"])] += 1
        check(event["publication_layer"] == "PRIMARY_JURY_DESCRIPTION", "publication mirror created pair support")
    check(max(per_pair_record.values()) == 1, "repeated descriptor inflated pair support within one record")
    check(all(edge["graph_layer"] == "G_professional" for edge in edges), "professional graph layer drift")
    check(all(edge["normalized_candidate_edge_eligible"] == "false" for edge in edges), "hash edge entered candidate graph")
    check(len(rows("COMMUNITY_LANGUAGE_EDGE.tsv")) == 0, "community edge count must remain zero")
    corpus_health = rows("DESCRIPTOR_CORPUS_HEALTH.tsv")
    check(corpus_health[0]["multi_descriptor_record_count"] == "5", "multi-descriptor record count drift")
    check(corpus_health[0]["model_eligible_strict_descriptor_assertion_count"] == "0", "strict model label inflation")

    candidate_receipts = rows("CANDIDATE_SET_SCORE_RECEIPT.tsv")
    check({row["run_id"] for row in candidate_receipts} == {"floral_citrus_tea", "fruit_chocolate_spice", "rare_direct_answer", "insufficient_evidence"}, "candidate fixture receipt coverage drift")
    check(all(row["rule_version"] == "round4a-objective-m-deterministic-v1" for row in candidate_receipts), "candidate rule version drift")
    check(any(float(row["professional_coherence_contribution"]) > 0 for row in candidate_receipts), "professional coherence contribution not retained")
    check(any(row["override_applied"] == "true" for row in candidate_receipts), "direct answer override receipt absent")
    check(any(row["candidate"] == "ABSTAIN" for row in candidate_receipts), "abstention receipt absent")

    regimes = rows("DATA_USE_REGIME.tsv")
    check({row["regime"] for row in regimes} == {"REFERENCE_ONLY", "PROJECT_EXPERIMENT_ALLOWED", "FIRST_PARTY_BEHAVIORAL_ALLOWED", "DEPLOYMENT_ALLOWED", "PROHIBITED"}, "usage-regime set drift")
    check(all(row["automatic_widening_allowed"] == "false" for row in regimes), "rights regime widened automatically")
    compatibility = rows("DATASET_COMPATIBILITY_MATRIX.tsv")
    check(len(compatibility) == 64, "dataset-task compatibility matrix must be 8 by 8")
    check(all(row["eligible"] == "false" for row in compatibility), "ineligible surfaces pooled into training")
    check(value("PROJECT_EXPERIMENT_MANIFEST.json")["row_count"] == 0, "unknown-rights row entered experiment manifest")
    check(value("PROFESSIONAL_REFERENCE_MANIFEST.json")["model_eligible_count"] == 0, "reference rows entered model gate")

    event_schema = value("FIRST_PARTY_BEHAVIORAL_SCHEMA.json")
    check(event_schema["collection_default"] == "NO_REMOTE_COLLECTION", "behavioral collection default widened")
    check(event_schema["storage_default"] == "LOCAL_ONLY_OR_NO_OP", "behavioral storage default widened")
    check(event_schema["first_party_behavioral_ranking_phase"] == "POST_INITIAL_MODEL", "behavioral phase ordering drift")
    decision = value("TRAINING_FEASIBILITY_DECISION.json")
    check(decision["decision"] == "CONTINUE_TASK_TARGETED_DATA_REVIEW", "training decision drift")
    check(decision["empirical_classical_model_run"] is False, "empirical model claimed")
    check(decision["deep_learning_entry_ready"] is False, "deep-learning readiness claimed")
    manifest = value("ROUND4A_MANIFEST.json")
    check(manifest["migrations_000_059_modified"] is False, "historical migration modification claimed")
    check(manifest["archive_rows_counted_as_model_labels"] is False, "archive-label boundary failed")

    forbidden = {".ckpt", ".joblib", ".onnx", ".pkl", ".pt", ".pth", ".safetensors", ".tflite"}
    check(not any(path.suffix.lower() in forbidden for path in DATA.rglob("*")), "model weight persisted")
    client_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (ROOT / "public").rglob("*") if path.is_file()
    )
    check(not re.search(r"reviewer[_-](?:qualification|admission)|rights[_-]decision|restricted://", client_text, re.I), "restricted governance material exposed to client")

    print("ROUND4A_ARTIFACT_CONTRACT_PASS=true")
    print("EXPECTED_SERIES_YEAR_COUNT=389")
    print("TERMINALLY_CLASSIFIED_SERIES_YEAR_COUNT=389")
    print("PROFESSIONAL_DESCRIPTOR_PAIR_EVENT_COUNT=508")
    print("UNIQUE_PROFESSIONAL_PAIR_COUNT=506")
    print("COMMUNITY_EDGE_COUNTED_AS_PROFESSIONAL_PAIR_COUNT=0")
    print("PERSISTED_SYNTHETIC_TRAINING_ROW_COUNT=0")


if __name__ == "__main__":
    main()
