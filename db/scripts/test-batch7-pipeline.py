#!/usr/bin/env python3
"""Fail-closed Batch 7 acquisition, 50K, semantics, and benchmark contracts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
STATE = ROOT / "db" / "data" / "acquisition-state"
POST50 = ROOT / "db" / "data" / "post50k-extension-staging"
RUNNER = ROOT / "db" / "scripts" / "descriptor-pipeline.py"
RAW_FIELDS = {"raw_field_text", "atomic_source_text", "source_native_form", "judge_observation_id"}
MODEL_SUFFIXES = {".pt", ".pth", ".onnx", ".safetensors", ".ckpt", ".h5", ".keras", ".pkl", ".joblib"}
ROUTE_STATES = {
    "DISCOVERED", "PROBE_PENDING", "PROBE_POSITIVE", "PROBE_ZERO_YIELD",
    "ACQUISITION_ACTIVE", "ACQUISITION_PAUSED", "EXHAUSTED", "BLOCKED_ACCESS",
    "BLOCKED_RIGHTS", "PARSER_FAILED", "SCHEMA_DRIFT", "DUPLICATE_SATURATED",
    "PARTNERSHIP_ONLY",
}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def document(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_sums(root: Path) -> None:
    listed = {}
    for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        listed[name] = digest
    actual = {path.name for path in root.iterdir() if path.is_file() and path.name != "SHA256SUMS"}
    check(set(listed) == actual, f"checksum inventory drift under {root.relative_to(ROOT)}")
    check(all(sha(root / name) == digest for name, digest in listed.items()), f"checksum mismatch under {root.relative_to(ROOT)}")


def validate_routes() -> None:
    registry = rows(STATE / "SOURCE_ROUTE_REGISTRY.tsv")
    transitions = rows(STATE / "SOURCE_ROUTE_STATE_TRANSITION.tsv")
    adapters = rows(STATE / "SOURCE_ADAPTER_REGISTRY.tsv")
    families = rows(STATE / "SOURCE_FAMILY_REGISTRY.tsv")
    schemas = rows(STATE / "ROUTE_SCHEMA_REGISTRY.tsv")
    attempts = rows(STATE / "NON_COE_ROUTE_ATTEMPT.tsv")
    cursors = rows(STATE / "ACQUISITION_CURSOR_REGISTRY.tsv")
    check(len(registry) == 13 and len(adapters) == 3, "route or adapter registry count drift")
    check(len(families) == len({row["source_family_id"] for row in registry}), "source-family registry count drift")
    check(len(schemas) == len({row["route_schema_id"] for row in registry}), "route-schema registry count drift")
    check(len({row["source_route_id"] for row in registry}) == len(registry), "route IDs are not unique")
    check(all(row["current_state"] in ROUTE_STATES for row in registry), "unregistered route state")
    check(all(row["previous_state"] in ROUTE_STATES | {""} and row["new_state"] in ROUTE_STATES for row in transitions), "route transition state drift")
    required_transition = {"timestamp", "previous_state", "new_state", "reason", "artifact_cursor", "commit_sha", "operator_type"}
    check(all(required_transition <= set(row) and all(row[field] or field == "previous_state" for field in required_transition) for row in transitions), "route transition provenance incomplete")
    check(len(attempts) >= 10, "fewer than ten non-CoE routes attempted")
    check(len({row["source_class"] for row in attempts}) >= 3, "fewer than three non-CoE source classes attempted")
    languages = {language for row in attempts for language in row["languages"].split("|") if language}
    check(len(languages) >= 2, "fewer than two non-CoE languages attempted")
    check(all(row["attempted"] == "true" for row in attempts), "route attempt receipt is incomplete")
    check(any(row["descriptor_bearing"] == "true" for row in attempts), "non-CoE discovery has no positive route")
    check(len(cursors) == 1 and cursors[0]["cursor_start"].startswith("archive-page=142;detail-index=2;"), "CoE cursor start drift")


def validate_50k() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    snapshot = document(CURRENT / "CANDIDATE_50K_SNAPSHOT_MANIFEST.json")
    cleaned = document(CURRENT / "CLEANED_50K_MANIFEST.json")
    source = rows(CURRENT / "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv")
    atoms = rows(CURRENT / "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv")
    check(snapshot["snapshot_version"] == "professional-descriptor-candidate-v3-50k", "50K snapshot version drift")
    check(snapshot["source_assertion_count"] == len(source) == 50034, "50K source denominator drift")
    check(len({row["descriptor_assertion_id"] for row in source}) == len(source), "50K source identities are not unique")
    check(snapshot["cleaner_contract_version"] == cleaned["cleaner_version"] == "batch4.semantic-cleaner.v2", "cleaner V2 changed")
    check(all(row["cleaner_contract_version"] == "batch4.semantic-cleaner.v2" for row in source), "source cleaner contract drift")
    check(sum(int(row["cleaned_output_atom_count"]) for row in source) == len(atoms) == cleaned["output_atom_count"], "source/output atom reconciliation failed")
    check(len({row["cleaned_output_atom_id"] for row in atoms}) == len(atoms), "cleaned output atom identities are not unique")
    check(all(row["model_eligible"] == "false" for row in atoms), "50K output was made model eligible")
    check(cleaned["source_assertion_reconciliation_pass"] is True and cleaned["model_run"] is False, "50K cleaned manifest governance drift")
    return source, atoms


def validate_s2_and_support() -> None:
    mining = document(STATE / "S2_REFERENCE_MINING_RECEIPT.json")
    seed = rows(STATE / "S2_REFERENCE_RELATION_SEED.tsv")
    sources = rows(CURRENT / "SEMANTIC_REFERENCE_SOURCE.tsv")
    edges = rows(CURRENT / "SEMANTIC_RELATION_EDGE.tsv")
    support = rows(CURRENT / "SEMANTIC_RELATION_SUPPORT.tsv")
    source_ids = {row["semantic_reference_source_id"] for row in sources}
    check(mining["reference_source_count"] >= 5 and mining["unique_relation_count"] >= 100, "S2 mining target shortfall")
    check(mining["target_concept_coverage_count"] >= 25, "S2 concept-coverage target shortfall")
    check(len(seed) == len({row["semantic_relation_id"] for row in seed}) == mining["unique_relation_count"], "S2 relation identity drift")
    check(all(row["semantic_reference_source_id"] in source_ids for row in seed), "S2 relation source is not traceable")
    check(all(row["evidence_authority"] == "S2_EXPLICIT_PROFESSIONAL_REFERENCE" for row in seed), "S2 authority drift")
    check(all(len(row["source_artifact_sha256"]) == len(row["source_term_sha256"]) == len(row["definition_or_category_sha256"]) == 64 for row in seed), "S2 hash traceability drift")
    edge_ids = {row["semantic_relation_id"] for row in edges}
    support_ids = {row["semantic_relation_id"] for row in support}
    check(edge_ids == support_ids, "relation-level support does not cover every semantic relation")
    check(len(support) == len(support_ids), "relation-support encoding is not one row per relation")
    check(all(int(row["support_occurrence_count"]) >= 1 for row in support), "relation occurrence count is invalid")
    s2_ids = {row["semantic_relation_id"] for row in seed}
    check(s2_ids <= edge_ids, "S2 relations were not admitted to the typed graph")
    check(all(row["supporting_output_atom_id"] == "NA_SEMANTIC_REFERENCE_NOT_OBSERVATION" for row in support if row["semantic_relation_id"] in s2_ids), "S2 reference was mislabeled as an observation")
    manifest = document(CURRENT / "BATCH7_SEMANTIC_MANIFEST.json")
    check(sum(int(row["support_occurrence_count"]) for row in support) == manifest["relation_support_occurrence_count"], "relation support occurrence reconciliation failed")
    check(len(support) == manifest["relation_level_support_row_count"], "relation support row reconciliation failed")
    check(sum(int(row["support_occurrence_count"]) for row in support if row["evidence_authority"] == "S3_MULTI_SOURCE_MACHINE_CANDIDATE") == manifest["s3_support_occurrence_count"], "S3 occurrence reconciliation failed")
    allowed_types = {
        "EXACT_EQUIVALENT", "APPROVED_ALIAS_OF", "MORPHOLOGICAL_VARIANT_OF",
        "INSTANCE_OR_SPECIFIC_FORM_OF", "MODIFIES", "COMPONENT_OF", "COASSERTED_WITH",
        "OBSERVED_UNDER_PREPARATION", "OBSERVED_WITH_ROAST_EVIDENCE",
        "EXPLICIT_DEFINITION_MATCH", "EXPLICIT_BROADER_NARROWER",
    }
    check(all(row["relation_type"] in allowed_types for row in edges), "semantic graph relation type drift")
    adjacency: dict[str, set[str]] = defaultdict(set)
    for row in edges:
        if row["relation_layer"] == "CONCEPT_HIERARCHY":
            adjacency[row["subject_node_id"]].add(row["object_node_id"])
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        check(node not in visiting, "concept hierarchy contains a cycle")
        if node in visited:
            return
        visiting.add(node)
        for child in adjacency.get(node, set()):
            visit(child)
        visiting.remove(node)
        visited.add(node)

    for node in sorted(adjacency):
        visit(node)


def validate_benchmark(atoms: list[dict[str, str]]) -> None:
    manifest = document(CURRENT / "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json")
    cases = rows(CURRENT / "CROSS_FORM_BENCHMARK_CANDIDATE.tsv")
    groups = rows(CURRENT / "CROSS_FORM_BENCHMARK_GROUP.tsv")
    audits = rows(CURRENT / "CROSS_FORM_BENCHMARK_LEAKAGE_AUDIT.tsv")
    check(manifest["contract_version"] == "batch7.cross-form-benchmark.v2", "benchmark V2 absent")
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in cases:
        by_case[row["benchmark_case_id"]].append(row)
    check(set(by_case) == {row["benchmark_case_id"] for row in groups} == {row["benchmark_case_id"] for row in audits}, "benchmark case surfaces do not reconcile")
    for case_id, case in by_case.items():
        train = [row for row in case if row["split"] == "TRAIN"]
        test = [row for row in case if row["split"] == "TEST"]
        check(train and test, f"benchmark fold lacks train/test rows: {case_id}")
        check(len({row["coffee_sample_group_id"] for row in test}) >= 3, f"held-out form below three groups: {case_id}")
        check(not ({row["cleaned_form_hash"] for row in train} & {row["cleaned_form_hash"] for row in test}), f"lexical-form leakage: {case_id}")
        check(not ({row["coffee_sample_group_id"] for row in train} & {row["coffee_sample_group_id"] for row in test}), f"sample-group leakage: {case_id}")
        check(not ({row["duplicate_publication_group_id"] for row in train} & {row["duplicate_publication_group_id"] for row in test}), f"publication leakage: {case_id}")
        check({row["target_concept_or_cluster_id"] for row in train} == {row["target_concept_or_cluster_id"] for row in test}, f"target-known condition failed: {case_id}")
    check(all(row["known_target_condition_pass"] == "true" for row in audits), "benchmark target-known audit failed")
    check(all(int(row["test_form_group_support"]) >= 3 for row in groups), "benchmark support threshold failed")
    check(all(row["relation_authority"] in {"S0_DETERMINISTIC_ORTHOGRAPHIC", "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS"} for row in groups if row["benchmark_tier"] == "PRIMARY_GOVERNED"), "primary benchmark authority drift")
    check(all(row["relation_authority"] == "S3_MULTI_SOURCE_MACHINE_CANDIDATE" for row in groups if row["benchmark_tier"] == "REVIEW_REQUIRED_S3"), "review benchmark authority drift")
    parent: dict[str, str] = {}

    def find(item: str) -> str:
        parent.setdefault(item, item)
        if parent[item] != item:
            parent[item] = find(parent[item])
        return parent[item]

    def union(left: str, right: str) -> None:
        a, b = find(left), find(right)
        if a != b:
            parent[b] = a

    for atom in atoms:
        if atom["counts_as_cleaned_descriptor_output"] == "true":
            union("coffee:" + (atom["coffee_identity_id"] or atom["effective_record_id"]), "form:" + atom["cleaned_lexical_form_sha256"])
    sizes = sorted(Counter(find(node) for node in parent).values())

    def percentile(q: float) -> int:
        import math
        return sizes[max(math.ceil(q * len(sizes)) - 1, 0)]

    check(manifest["global_component_count"] == len(sizes), "global component count is not graph-derived")
    check(manifest["largest_global_component_share"] == round(max(sizes) / sum(sizes), 6), "largest component share drift")
    check((manifest["p50_component_size"], manifest["p95_component_size"], manifest["p99_component_size"]) == (percentile(.5), percentile(.95), percentile(.99)), "component percentiles drift")
    check(manifest["leak_count"] == 0 and manifest["target_known_condition_pass"] is True and manifest["relation_authority_pass"] is True, "benchmark contract summary failed")
    owner = rows(CURRENT / "SEMANTIC_RELATION_OWNER_REVIEW_PACKET.tsv")
    owner_import = rows(CURRENT / "SEMANTIC_RELATION_OWNER_REVIEW_IMPORT_TEMPLATE.tsv")
    human = rows(CURRENT / "HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv")
    check(len(owner) == len(owner_import) == 100, "owner review packet is not the required 100 clusters")
    check(all(not row["project_owner_decision"] and not row["reviewer_id"] for row in owner), "owner decision was fabricated")
    check(len(human) == 500 and all(not row["reviewer_decision"] and not row["reviewer_id"] for row in human), "human benchmark template contract failed")


def validate_boundaries_and_model_audit() -> None:
    public_new = [
        *CURRENT.glob("*50K*"),
        CURRENT / "SEMANTIC_RELATION_SUPPORT.tsv",
        CURRENT / "SEMANTIC_RELATION_OWNER_REVIEW_PACKET.tsv",
        CURRENT / "SEMANTIC_RELATION_OWNER_REVIEW_IMPORT_TEMPLATE.tsv",
        *STATE.glob("*.tsv"),
        *POST50.glob("*.tsv"),
    ]
    for path in public_new:
        if path.suffix != ".tsv" or not path.is_file():
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            names = set(csv.DictReader(handle, delimiter="\t").fieldnames or [])
        check(not (RAW_FIELDS & names), f"raw source field leaked in {path.relative_to(ROOT)}")
    model_files = [path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*") if path.is_file() and path.suffix.casefold() in MODEL_SUFFIXES]
    check(not model_files, f"model files were created: {model_files}")


def validate_post50_if_present() -> None:
    manifest_path = POST50 / "POST50K_EXTENSION_MANIFEST.json"
    if not manifest_path.is_file():
        return
    manifest = document(manifest_path)
    check(manifest["extension_isolated_from_frozen_snapshot"] is True, "post-50K staging is not isolated")
    check(manifest["non_coe_attempts_completed_before_coe_continuation"] is True, "CoE continued before non-CoE routes")
    check(manifest["cursor_start"] == "archive-page=142;detail-index=2;url=https://farmdirectory.cupofexcellence.org/listing/abiyot-ethiopia-2022/", "post-50K cursor start drift")
    check(manifest["exact_cursor_validated"] is True, "post-50K exact cursor not validated")
    check(manifest["total_acquired_candidate_source_assertion_count"] >= 60000 and manifest["candidate_60k_checkpoint_reached"] is True, "60K candidate checkpoint not reached")
    check(manifest["model_eligible_assertion_count"] == 0 and manifest["model_training_run"] is False, "post-50K staging claimed model eligibility")


def run_checkpoint() -> None:
    subprocess.run([sys.executable, "-B", str(RUNNER), "checkpoint"], cwd=ROOT, check=True, capture_output=True, text=True)


def restricted_offline_replay() -> None:
    restricted = os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT")
    prior = os.environ.get("POST40K_RESTRICTED_ROOT")
    check(bool(restricted and prior), "restricted replay requires COFFEE_FLAVOR_RESTRICTED_ROOT and POST40K_RESTRICTED_ROOT")
    before = {name: sha(CURRENT / name) for name in (
        "CANDIDATE_50K_SNAPSHOT_MANIFEST.json", "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv",
        "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv", "BATCH7_SEMANTIC_MANIFEST.json",
        "SEMANTIC_RELATION_SUPPORT.tsv", "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json",
    )}
    prefix = [sys.executable, "-B", str(RUNNER), "--restricted-root", restricted, "--prior-post40-root", prior, "--offline"]
    for command in ("acquire", "clean", "semantic", "checkpoint"):
        subprocess.run([*prefix, command], cwd=ROOT, check=True)
    after = {name: sha(CURRENT / name) for name in before}
    check(before == after, "restricted offline replay did not reproduce public bytes")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--restricted-real", action="store_true")
    args = parser.parse_args()
    verify_sums(CURRENT)
    verify_sums(STATE)
    verify_sums(POST50)
    validate_routes()
    _source, atoms = validate_50k()
    validate_s2_and_support()
    validate_benchmark(atoms)
    validate_boundaries_and_model_audit()
    validate_post50_if_present()
    before = sha(CURRENT / "SHA256SUMS")
    run_checkpoint()
    check(sha(CURRENT / "SHA256SUMS") == before, "public checkpoint generation is not deterministic")
    if args.restricted_real:
        restricted_offline_replay()
    print("BATCH7_PIPELINE_CONTRACT_PASS=true")
    print(f"LOCAL_RESTRICTED_REAL_REPLAY_EXECUTED={str(args.restricted_real).lower()}")
    print(f"LOCAL_RESTRICTED_PUBLIC_BYTE_IDENTITY_PASS={str(args.restricted_real).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
