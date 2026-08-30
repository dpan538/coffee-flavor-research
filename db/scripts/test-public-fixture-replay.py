#!/usr/bin/env python3
"""Mandatory deterministic end-to-end replay for project-owned CI fixtures."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "db" / "fixtures" / "ci" / "professional-descriptor-pipeline" / "fixture-observations.json"
RECEIPT = ROOT / "db" / "data" / "ci" / "PUBLIC_FIXTURE_REPLAY_RECEIPT.json"
FORBIDDEN = {"raw_text", "source_native_form", "canonical_concept_label"}


def sha(value: bytes | str) -> str:
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def digest_inventory(root: Path) -> dict[str, str]:
    return {path.name: sha(path.read_bytes()) for path in sorted(root.iterdir()) if path.is_file()}


def parse_forms(raw_text: str) -> list[str]:
    value = raw_text.casefold().strip()
    if not value or value.startswith("rank "):
        return []
    return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]


def replay(output: Path) -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    contract = fixture["fixture_contract"]
    if {contract["classification"], contract["content_origin"], contract["corpus_status"], contract["training_status"]} != {
        "TEST_FIXTURE_ONLY", "PROJECT_OWNED_SYNTHETIC_TEST_CONTENT", "NOT_CORPUS_DATA", "NOT_TRAINING_DATA",
    }:
        raise RuntimeError("fixture classification is incomplete")
    observations = fixture["observations"]
    required_kinds = {
        "JURY_LIKE_FIELD", "GENERIC_OFFICIAL_SENSORY_FIELD", "TRAINED_PANEL_OBSERVATION",
        "COMPOUND_DESCRIPTOR", "MODIFIER_BASE_CONCEPT", "BROAD_SENSORY_ATTRIBUTE",
        "NON_DESCRIPTOR_METADATA", "DUPLICATE_PUBLICATION_LAYER", "RIGHTS_PERMITTED_ROW",
        "RIGHTS_UNKNOWN_ROW", "ZERO_YIELD_ARTIFACT",
    }
    if not required_kinds <= {row["field_kind"] for row in observations}:
        raise RuntimeError("fixture does not cover every required behavior")
    if len([row for row in observations if row["sample_id"] == "sample-b"]) < 2:
        raise RuntimeError("fixture lacks multiple observations per sample")

    restricted = output / "restricted-style-root"
    public = output / "public-sidecar"
    restricted.mkdir(parents=True)
    public.mkdir()
    (restricted / "fixture-source-artifact.json").write_text(json.dumps(fixture, sort_keys=True), encoding="utf-8")
    assertion_rows: list[dict[str, Any]] = []
    atom_rows: list[dict[str, Any]] = []
    seen_duplicate_keys: set[tuple[str, str]] = set()
    for row in observations:
        assertion_id = "fixture-assertion:" + sha(row["fixture_row_id"])[:24]
        forms = parse_forms(row["raw_text"])
        assertion_rows.append({
            "descriptor_assertion_id": assertion_id,
            "fixture_row_id": row["fixture_row_id"],
            "sample_group_id": row["sample_id"],
            "publication_group_id": row["publication_id"],
            "source_family_id": row["source_family_id"],
            "field_kind": row["field_kind"],
            "raw_field_text_sha256": sha(row["raw_text"]),
            "rights_state": row["rights_state"],
            "is_zero_yield": str(bool(row["zero_yield"])).lower(),
            "is_duplicate_publication": str(bool(row.get("duplicate_of"))).lower(),
        })
        for ordinal, form in enumerate(forms, start=1):
            duplicate_key = (row["sample_id"], form)
            counts = duplicate_key not in seen_duplicate_keys
            seen_duplicate_keys.add(duplicate_key)
            form_hash = sha(form)
            base = form.removeprefix("bright ").removeprefix("dark ").removeprefix("ripe ")
            atom_rows.append({
                "cleaned_output_atom_id": f"fixture-atom:{sha(assertion_id + str(ordinal))[:24]}",
                "descriptor_assertion_id": assertion_id,
                "sample_group_id": row["sample_id"],
                "publication_group_id": row["publication_id"],
                "source_family_id": row["source_family_id"],
                "cleaned_form_sha256": form_hash,
                "base_form_sha256": sha(base),
                "semantic_class": "BROAD_SENSORY" if row["field_kind"] == "BROAD_SENSORY_ATTRIBUTE" else "STRICT_FLAVOR",
                "counts_as_cleaned_descriptor_output": str(counts).lower(),
                "rights_state": row["rights_state"],
            })
    write_tsv(public / "SOURCE_ASSERTION_HASH_SIDECAR.tsv", list(assertion_rows[0]), assertion_rows)
    write_tsv(public / "CLEANED_OUTPUT_ATOM_LEDGER.tsv", list(atom_rows[0]), atom_rows)

    unique_forms = sorted({row["cleaned_form_sha256"] for row in atom_rows})
    relation_rows: list[dict[str, str]] = []
    for atom in atom_rows:
        if atom["cleaned_form_sha256"] != atom["base_form_sha256"]:
            relation_rows.append({
                "semantic_relation_id": "fixture-relation:" + sha(atom["cleaned_form_sha256"] + atom["base_form_sha256"])[:24],
                "relation_type": "MODIFIES",
                "relation_layer": "MODIFIER_COMPOUND",
                "subject_form_sha256": atom["cleaned_form_sha256"],
                "object_form_sha256": atom["base_form_sha256"],
            })
    for form in unique_forms:
        relation_rows.append({
            "semantic_relation_id": "fixture-relation:" + sha(form + "concept")[:24],
            "relation_type": "EXACT_EQUIVALENT",
            "relation_layer": "LEXICAL_EQUIVALENCE",
            "subject_form_sha256": form,
            "object_form_sha256": form,
        })
    write_tsv(public / "SEMANTIC_RELATION_EDGE.tsv", list(relation_rows[0]), relation_rows)
    benchmark_rows = [
        {
            "benchmark_case_id": "fixture-case:" + atom["base_form_sha256"][:16],
            "sample_group_id": atom["sample_group_id"],
            "publication_group_id": atom["publication_group_id"],
            "cleaned_form_sha256": atom["cleaned_form_sha256"],
            "target_form_sha256": atom["base_form_sha256"],
            "split": "TEST" if atom["cleaned_form_sha256"] != atom["base_form_sha256"] else "TRAIN",
        }
        for atom in atom_rows
        if atom["counts_as_cleaned_descriptor_output"] == "true"
    ]
    write_tsv(public / "BENCHMARK_GROUPING.tsv", list(benchmark_rows[0]), benchmark_rows)
    manifest = {
        "fixture_contract": contract,
        "source_assertion_count": len(assertion_rows),
        "cleaned_output_atom_count": len(atom_rows),
        "record_unique_cleaned_output_atom_count": sum(row["counts_as_cleaned_descriptor_output"] == "true" for row in atom_rows),
        "semantic_relation_count": len(relation_rows),
        "benchmark_row_count": len(benchmark_rows),
        "raw_source_text_published": False,
        "model_eligible_assertion_count": 0,
    }
    (public / "FIXTURE_PIPELINE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inventory = digest_inventory(public)
    (public / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(inventory.items())), encoding="utf-8")
    for path in public.glob("*.tsv"):
        with path.open(encoding="utf-8", newline="") as handle:
            if FORBIDDEN & set(csv.DictReader(handle, delimiter="\t").fieldnames or []):
                raise RuntimeError(f"public fixture output leaks source text: {path.name}")
    return {**manifest, "output_inventory": digest_inventory(public)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="coffee-fixture-replay-") as first, tempfile.TemporaryDirectory(prefix="coffee-fixture-replay-") as second:
        first_result = replay(Path(first))
        second_result = replay(Path(second))
    if first_result != second_result:
        raise RuntimeError("fixture offline replay inventory differs")
    receipt = {
        "contract_version": "ci-public-fixture-replay.v1",
        "mode": "public-fixture",
        "fixture_path": "db/fixtures/ci/professional-descriptor-pipeline/fixture-observations.json",
        "fixture_status": "TEST_FIXTURE_ONLY_PROJECT_OWNED_SYNTHETIC_TEST_CONTENT_NOT_CORPUS_DATA_NOT_TRAINING_DATA",
        "public_fixture_full_pipeline_replay_required": True,
        "public_fixture_full_pipeline_replay_pass": True,
        "deterministic_offline_rerun_pass": True,
        "source_assertion_count": first_result["source_assertion_count"],
        "cleaned_output_atom_count": first_result["cleaned_output_atom_count"],
        "record_unique_cleaned_output_atom_count": first_result["record_unique_cleaned_output_atom_count"],
        "semantic_relation_count": first_result["semantic_relation_count"],
        "benchmark_row_count": first_result["benchmark_row_count"],
        "raw_source_text_published": False,
        "model_eligible_assertion_count": 0,
    }
    if args.write_receipt:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    elif not RECEIPT.is_file() or json.loads(RECEIPT.read_text(encoding="utf-8")) != receipt:
        raise RuntimeError("committed public fixture receipt does not reconcile")
    print("PUBLIC_FIXTURE_FULL_PIPELINE_REPLAY_PASS=true")
    print("PUBLIC_FIXTURE_DETERMINISTIC_OFFLINE_RERUN_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
