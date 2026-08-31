#!/usr/bin/env python3
"""Mandatory public-package contract verification with no restricted replay claim."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
POST40 = ROOT / "db" / "data" / "post40k-extension-staging"
POST50 = ROOT / "db" / "data" / "post50k-extension-staging"
CI = ROOT / "db" / "data" / "ci"
RECEIPT = ROOT / "db" / "data" / "ci" / "PUBLIC_SNAPSHOT_CONTRACT_RECEIPT.json"
MODEL_SUFFIXES = {".pt", ".pth", ".onnx", ".safetensors", ".ckpt", ".h5", ".keras"}
# Canonical project vocabulary may be public; source-native/raw fields may not.
RAW_FIELD_NAMES = {"raw_field_text", "atomic_source_text", "source_native_form"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def verify_sums(root: Path) -> int:
    listed = {}
    for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        value, name = line.split("  ", 1)
        listed[name] = value
    if not listed or any(not (root / name).is_file() or sha(root / name) != value for name, value in listed.items()):
        raise RuntimeError(f"SHA256SUMS mismatch under {root.relative_to(ROOT)}")
    return len(listed)


def verify_public_ledgers() -> tuple[int, int]:
    public_tsvs = sorted(CURRENT.glob("*.tsv")) + sorted(POST40.glob("*.tsv")) + sorted(POST50.glob("*.tsv"))
    for path in public_tsvs:
        with path.open(encoding="utf-8", newline="") as handle:
            fields = set(csv.DictReader(handle, delimiter="\t").fieldnames or [])
        forbidden = RAW_FIELD_NAMES & fields
        if forbidden:
            raise RuntimeError(f"public ledger leaks raw source fields in {path.name}: {sorted(forbidden)}")
    source = rows(CURRENT / "CLEANED_50K_SOURCE_ASSERTION_LEDGER.tsv")
    atoms = rows(CURRENT / "CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv")
    if len(source) != 50034 or not atoms:
        raise RuntimeError("frozen 50k ledgers do not reconcile")
    if len({row["descriptor_assertion_id"] for row in source}) != len(source):
        raise RuntimeError("source assertion identifiers are not stable and unique")
    if len({row["cleaned_output_atom_id"] for row in atoms}) != len(atoms):
        raise RuntimeError("cleaned output identifiers are not stable and unique")
    if any(row.get("model_eligible") != "false" for row in atoms):
        raise RuntimeError("public snapshot contains model-eligible assertion")
    return len(source), len(atoms)


def verify_semantics_and_benchmark() -> tuple[int, int]:
    edges = rows(CURRENT / "SEMANTIC_RELATION_EDGE.tsv")
    allowed_layers = {"LEXICAL_EQUIVALENCE", "LEXICAL_DEFINITION", "CONCEPT_HIERARCHY", "MODIFIER_COMPOUND", "OBSERVATIONAL", "CONTEXT"}
    allowed_authorities = {
        "S0_DETERMINISTIC_ORTHOGRAPHIC", "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS",
        "S3_MULTI_SOURCE_MACHINE_CANDIDATE",
        "S2_EXPLICIT_PROFESSIONAL_REFERENCE",
    }
    if not edges or any(row["relation_layer"] not in allowed_layers for row in edges):
        raise RuntimeError("semantic relation layer contract fails")
    if any(row["semantic_evidence_authority"] not in allowed_authorities for row in edges):
        raise RuntimeError("semantic evidence authority contract fails")
    cases = rows(CURRENT / "CROSS_FORM_BENCHMARK_CANDIDATE.tsv")
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in cases:
        grouped[row["benchmark_case_id"]].append(row)
    if not grouped:
        raise RuntimeError("cross-form benchmark is missing")
    for case in grouped.values():
        train = [row for row in case if row["split"] == "TRAIN"]
        test = [row for row in case if row["split"] == "TEST"]
        if not train or not test:
            raise RuntimeError("benchmark case lacks a train or test partition")
        if {row["cleaned_form_hash"] for row in train} & {row["cleaned_form_hash"] for row in test}:
            raise RuntimeError("benchmark lexical-form leakage")
        if {row["coffee_sample_group_id"] for row in train} & {row["coffee_sample_group_id"] for row in test}:
            raise RuntimeError("benchmark sample-group leakage")
    return len(edges), len(grouped)


def verify_model_audit() -> int:
    # The PostgreSQL CI job runs inside the official database container, which
    # deliberately has no Git executable. Audit the repository surfaces
    # directly so this mandatory public check does not depend on a developer
    # tool that is absent from its declared runtime.
    audit_roots = [ROOT / name for name in ("app", "db", "docs", "packages", "scripts", ".github")]
    audited = [
        path.relative_to(ROOT).as_posix()
        for base in audit_roots if base.exists()
        for path in base.rglob("*") if path.is_file()
    ]
    model_files = [name for name in audited if Path(name).suffix.casefold() in MODEL_SUFFIXES]
    if model_files:
        raise RuntimeError(f"model files are not permitted: {model_files}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    current_files = verify_sums(CURRENT)
    post40_files = verify_sums(POST40)
    post50_files = verify_sums(POST50)
    ci_files = verify_sums(CI)
    source_count, atom_count = verify_public_ledgers()
    edge_count, case_count = verify_semantics_and_benchmark()
    model_count = verify_model_audit()
    manifest = json.loads((CURRENT / "CANDIDATE_50K_SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))
    receipt = {
        "contract_version": "ci-public-snapshot-contract.v2",
        "mode": "public-snapshot",
        "public_snapshot_contract_required": True,
        "public_snapshot_contract_pass": True,
        "restricted_source_text_independently_replayed": False,
        "restricted_source_text_status": "NOT_EXECUTED_PUBLIC_CI_RESTRICTED_INPUT_INTENTIONALLY_UNAVAILABLE",
        "candidate_50k_snapshot_version": manifest["snapshot_version"],
        "candidate_50k_source_assertion_count": source_count,
        "cleaned_50k_output_atom_count": atom_count,
        "semantic_relation_edge_count": edge_count,
        "cross_form_case_count": case_count,
        "current_sha256_receipt_file_count": current_files,
        "post40k_sha256_receipt_file_count": post40_files,
        "post50k_sha256_receipt_file_count": post50_files,
        "ci_sha256_receipt_file_count": ci_files,
        "model_file_count": model_count,
        "raw_source_text_published": False,
    }
    if args.write_receipt:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif not RECEIPT.is_file() or json.loads(RECEIPT.read_text(encoding="utf-8")) != receipt:
        raise RuntimeError("committed public snapshot receipt does not reconcile")
    print("PUBLIC_SNAPSHOT_CONTRACT_PASS=true")
    print("PUBLIC_SNAPSHOT_RESTRICTED_REAL_REPLAY_STATUS=NOT_EXECUTED_PUBLIC_CI_RESTRICTED_INPUT_INTENTIONALLY_UNAVAILABLE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
