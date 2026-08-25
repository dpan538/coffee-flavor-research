#!/usr/bin/env python3
"""Negative and reproducibility tests for the Round 3E artifact contract."""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "db/scripts/generate-round3e-artifacts.py"
SPEC = importlib.util.spec_from_file_location("round3e_generator", GENERATOR)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load Round 3E generator")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def tree_hashes(path: Path) -> dict[str, str]:
    return {
        str(item.relative_to(path)): hashlib.sha256(item.read_bytes()).hexdigest()
        for item in sorted(path.rglob("*"))
        if item.is_file()
    }


def expect_contract_error(name: str, manifest: dict[str, object], raw_root: Path, expected: str) -> None:
    manifest_path = raw_root / f"{name}.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    previous = MODULE.RAW_ROOT
    MODULE.RAW_ROOT = raw_root
    try:
        try:
            MODULE.verify_manifest(manifest)
        except MODULE.ContractError as error:
            if expected not in str(error):
                raise AssertionError(f"{name}: expected {expected!r}, got {error!r}") from error
        else:
            raise AssertionError(f"{name}: invalid manifest was accepted")
    finally:
        MODULE.RAW_ROOT = previous
    print(f"NEGATIVE_TEST={name} PASS")


def main() -> int:
    source_raw = ROOT / "db/data/round3e/raw"
    manifest = json.loads((source_raw / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="round3e-artifact-contract-") as temp_name:
        temp = Path(temp_name)
        raw = temp / "raw"
        shutil.copytree(source_raw, raw)

        mutation = copy.deepcopy(manifest)
        mutation["snapshots"].append(copy.deepcopy(mutation["snapshots"][0]))
        expect_contract_error("duplicate_external_snapshot_key", mutation, raw, "duplicate external snapshot key")

        mutation = copy.deepcopy(manifest)
        mutation["snapshots"][0]["files"][0]["sha256"] = "0" * 64
        expect_contract_error("mismatched_file_hash", mutation, raw, "mismatched file hash")

        mutation = copy.deepcopy(manifest)
        mutation["snapshots"][0]["declared_row_count"] = 319
        expect_contract_error("wrong_declared_row_count", mutation, raw, "wrong declared row count")

        mutation = copy.deepcopy(manifest)
        mutation["snapshots"][0]["license"] = ""
        expect_contract_error("missing_license_decision", mutation, raw, "missing license decision")

        mutation = copy.deepcopy(manifest)
        mutation["snapshots"][0]["rights_decision"] = "BLOCKED_RIGHTS"
        expect_contract_error("public_export_of_blocked_raw_text", mutation, raw, "public export of blocked raw text")

        if not MODULE.PII_HEADER.fullmatch("participant_email") and not MODULE.PII_EMAIL.search("participant@example.org"):
            raise AssertionError("direct participant identifier detection failed")
        print("NEGATIVE_TEST=direct_participant_identifier PASS")

        if MODULE.normalize_expression("  Café  Latte ") != "café latte":
            raise AssertionError("normalization contract changed")
        print("NEGATIVE_TEST=source_local_raw_value_preserved_separately PASS")

        questions = json.loads((ROOT / "db/data/round3e/source/question_candidates.json").read_text(encoding="utf-8"))
        questions["ordinary_user_validation_count"] = 1
        invalid_questions = temp / "invalid-questions.json"
        invalid_questions.write_text(json.dumps(questions), encoding="utf-8")
        previous_question_path = MODULE.QUESTION_PATH
        MODULE.QUESTION_PATH = invalid_questions
        try:
            try:
                MODULE.build_questions()
            except MODULE.ContractError as error:
                if "user-validated" not in str(error):
                    raise
            else:
                raise AssertionError("candidate question validation claim was accepted")
        finally:
            MODULE.QUESTION_PATH = previous_question_path
        print("NEGATIVE_TEST=candidate_question_user_validation_without_evidence PASS")

        output_one = temp / "output-one"
        output_two = temp / "output-two"
        for output in (output_one, output_two):
            subprocess.run(
                [sys.executable, str(GENERATOR), "--manifest", str(raw / "SOURCE_MANIFEST.json"), "--output-dir", str(output)],
                cwd=ROOT,
                check=True,
                stdout=subprocess.DEVNULL,
            )
        if tree_hashes(output_one) != tree_hashes(output_two):
            raise AssertionError("nondeterministic manifest or generated artifact")
        print("NEGATIVE_TEST=nondeterministic_manifest PASS")

        with (output_one / "external_field_dictionary.tsv").open(encoding="utf-8") as handle:
            field_rows = list(csv.DictReader(handle, delimiter="\t"))
        if any(
            row["normalization_rule"] not in {"identity_no_unit_conversion", "trim_outer_whitespace_only"}
            for row in field_rows
        ):
            raise AssertionError("silent unit conversion detected")
        print("NEGATIVE_TEST=silent_unit_conversion PASS")

        observation_header = (output_one / "external_observations.tsv").read_text(encoding="utf-8").splitlines()[0]
        if "raw_value_json" not in observation_header or "normalized_value_json" not in observation_header:
            raise AssertionError("source-local raw value could be overwritten by normalized value")
        print("NEGATIVE_TEST=source_local_value_overwrite PASS")

        stale = tree_hashes(output_one)
        with (output_one / "coverage_cube.tsv").open("a", encoding="utf-8") as handle:
            handle.write("stale\n")
        if stale == tree_hashes(output_one):
            raise AssertionError("stale artifact was not detected")
        print("NEGATIVE_TEST=stale_generated_artifact PASS")

    print("ROUND3E_ARTIFACT_CONTRACT_TEST_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
