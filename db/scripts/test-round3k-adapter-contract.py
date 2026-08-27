#!/usr/bin/env python3
"""Positive and adversarial tests for the Round 3K adapter contract."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
ADAPTERS = ROOT / "db" / "adapters"
FIXTURE = ADAPTERS / "round3k" / "fixtures" / "STRUCTURAL_TEST_FIXTURE"
sys.path.insert(0, str(ADAPTERS))

from round3k import (  # noqa: E402
    REQUIRED_TABLE_FILES,
    SOURCE_PROFILES,
    SUPPORTED_SOURCE_KINDS,
    TABLE_SCHEMAS,
    ContractViolation,
    ExplicitRecordAdapter,
    emit_bundle,
    read_table,
    validate_bundle,
)


def _manifest(bundle: Path) -> dict[str, object]:
    with (bundle / "SOURCE_MANIFEST.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _write_manifest(bundle: Path, manifest: dict[str, object]) -> None:
    (bundle / "SOURCE_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _rows(bundle: Path, filename: str) -> list[dict[str, str]]:
    return read_table(bundle / filename, TABLE_SCHEMAS[filename])


def _write_table(
    bundle: Path,
    filename: str,
    rows: list[dict[str, str]],
    *,
    fieldnames: tuple[str, ...] | None = None,
    sync_count: bool = True,
) -> None:
    columns = fieldnames or TABLE_SCHEMAS[filename]
    with (bundle / filename).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
    if sync_count:
        manifest = _manifest(bundle)
        record_counts = manifest["record_counts"]
        assert isinstance(record_counts, dict)
        record_counts[filename] = len(rows)
        _write_manifest(bundle, manifest)


def _mutate_row(bundle: Path, filename: str, field: str, value: str) -> None:
    rows = _rows(bundle, filename)
    rows[0][field] = value
    _write_table(bundle, filename, rows)


def _rehash(bundle: Path) -> None:
    lines = []
    for path in sorted(
        (item for item in bundle.rglob("*") if item.is_file() and item.name != "SHA256SUMS"),
        key=lambda item: item.relative_to(bundle).as_posix(),
    ):
        relative = path.relative_to(bundle).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative}\n")
    (bundle / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def _make_nonfixture(bundle: Path) -> None:
    manifest = _manifest(bundle)
    manifest.update(
        {
            "acquisition_authorization": "PUBLIC_OFFICIAL",
            "adapter_status": "VALIDATED",
            "contains_observed_coffee_data": True,
            "core_count_eligible": False,
            "structural_test_fixture": False,
        }
    )
    quality = manifest["quality_gate_results"]
    assert isinstance(quality, dict)
    quality.update(
        {
            "DESCRIPTOR_SPAN_PRECISION": 1,
            "DUPLICATE_LINKAGE_ACCURACY": 1,
            "ENTRY_IDENTITY_FIELD_ACCURACY": 1,
            "FALSE_FLAVOR_DOCUMENT_RATE": 0,
            "SCORE_FIELD_ACCURACY": 1,
            "audited_record_count": 1,
            "parsed_record_count": 1,
            "quality_gate_status": "PASS",
        }
    )
    _write_manifest(bundle, manifest)

    for filename in REQUIRED_TABLE_FILES[:7]:
        rows = _rows(bundle, filename)
        for row in rows:
            row["structural_test_fixture"] = "false"
        _write_table(bundle, filename, rows)
    _mutate_row(
        bundle,
        "EFFECTIVE_RECORD_REPORT.tsv",
        "structural_test_fixture",
        "false",
    )
    _mutate_row(
        bundle,
        "EFFECTIVE_RECORD_REPORT.tsv",
        "exclusion_reason",
        "NOT_CORE_ELIGIBLE",
    )
    rights = _rows(bundle, "RIGHTS_REPORT.tsv")
    for dimension in (
        "public_results_use",
        "public_descriptor_use",
        "internal_research_use",
        "public_derived_release",
        "model_research_use",
        "commercial_model_use",
    ):
        rights[0][dimension] = "pending"
    rights[0]["rights_decision_status"] = "PENDING"
    rights[0]["review_status"] = "PENDING"
    _write_table(bundle, "RIGHTS_REPORT.tsv", rights)


def _make_observed_core(bundle: Path, *, model_eligible: bool = False) -> None:
    _make_nonfixture(bundle)
    manifest = _manifest(bundle)
    manifest["core_count_eligible"] = True
    _write_manifest(bundle, manifest)
    for filename in REQUIRED_TABLE_FILES[:7]:
        rows = _rows(bundle, filename)
        for row in rows:
            row["core_count_eligible"] = "true"
        _write_table(bundle, filename, rows)

    descriptor = _rows(bundle, "RAW_DESCRIPTOR_ASSERTION.tsv")
    descriptor[0]["label_disposition"] = "POSITIVE"
    _write_table(bundle, "RAW_DESCRIPTOR_ASSERTION.tsv", descriptor)

    effective = _rows(bundle, "EFFECTIVE_RECORD_REPORT.tsv")
    effective[0].update(
        {
            "observed_core_eligible": "true",
            "model_eligible": "true" if model_eligible else "false",
            "auxiliary_eligible": "false",
            "exclusion_reason": "",
        }
    )
    _write_table(bundle, "EFFECTIVE_RECORD_REPORT.tsv", effective)

    rights = _rows(bundle, "RIGHTS_REPORT.tsv")
    rights[0]["internal_research_use"] = "true"
    rights[0]["model_research_use"] = "true" if model_eligible else "false"
    rights[0]["rights_decision_status"] = "REVIEWED_RESTRICTED"
    rights[0]["review_status"] = "REVIEWED"
    _write_table(bundle, "RIGHTS_REPORT.tsv", rights)


class Round3KAdapterContractTests(unittest.TestCase):
    maxDiff = None

    def _copy_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory(prefix="round3k-adapter-contract-")
        bundle = Path(temporary.name) / "bundle"
        shutil.copytree(FIXTURE, bundle)
        return temporary, bundle

    def _assert_violation(
        self,
        expected_code: str,
        mutation: Callable[[Path], None],
        *,
        rehash: bool = True,
    ) -> None:
        temporary, bundle = self._copy_fixture()
        with temporary:
            mutation(bundle)
            if rehash:
                _rehash(bundle)
            with self.assertRaises(ContractViolation) as raised:
                validate_bundle(bundle)
            self.assertEqual(expected_code, raised.exception.code, str(raised.exception))

    def test_fixture_validates_and_is_ineligible(self) -> None:
        summary = validate_bundle(FIXTURE)
        self.assertTrue(summary.structural_test_fixture)
        self.assertEqual("STRUCTURAL_TEST_ONLY", summary.adapter_status)
        self.assertEqual(1, summary.table_counts["EFFECTIVE_RECORD_REPORT.tsv"])
        manifest = _manifest(FIXTURE)
        self.assertFalse(manifest["contains_observed_coffee_data"])
        self.assertFalse(manifest["core_count_eligible"])

    def test_all_eleven_source_profiles_share_one_emitter(self) -> None:
        self.assertEqual(11, len(SUPPORTED_SOURCE_KINDS))
        self.assertEqual(set(SUPPORTED_SOURCE_KINDS), set(SOURCE_PROFILES))
        for source_kind in SUPPORTED_SOURCE_KINDS:
            self.assertEqual(source_kind, ExplicitRecordAdapter(source_kind).profile.source_kind)

    def test_emitter_reproduces_fixture_byte_for_byte(self) -> None:
        manifest = _manifest(FIXTURE)
        tables = {
            filename: _rows(FIXTURE, filename) for filename in REQUIRED_TABLE_FILES
        }
        sources = {"STRUCTURAL_SOURCE.txt": (FIXTURE / "STRUCTURAL_SOURCE.txt").read_bytes()}
        with tempfile.TemporaryDirectory(prefix="round3k-emitter-") as temporary:
            output = Path(temporary) / "emitted"
            summary = emit_bundle(output, manifest, tables, sources)
            self.assertTrue(summary.structural_test_fixture)
            expected_files = sorted(
                item.relative_to(FIXTURE).as_posix()
                for item in FIXTURE.rglob("*")
                if item.is_file()
            )
            emitted_files = sorted(
                item.relative_to(output).as_posix()
                for item in output.rglob("*")
                if item.is_file()
            )
            self.assertEqual(expected_files, emitted_files)
            for relative in expected_files:
                self.assertEqual((FIXTURE / relative).read_bytes(), (output / relative).read_bytes())

    def test_rejects_missing_manifest(self) -> None:
        self._assert_violation(
            "MISSING_FILE", lambda bundle: (bundle / "SOURCE_MANIFEST.json").unlink(), rehash=False
        )

    def test_rejects_missing_hash_file(self) -> None:
        self._assert_violation(
            "MISSING_FILE", lambda bundle: (bundle / "SHA256SUMS").unlink(), rehash=False
        )

    def test_rejects_missing_required_table(self) -> None:
        self._assert_violation(
            "MISSING_FILE", lambda bundle: (bundle / "RAW_SCORE.tsv").unlink(), rehash=False
        )

    def test_rejects_missing_hash_entry(self) -> None:
        def mutation(bundle: Path) -> None:
            lines = (bundle / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
            kept = [line for line in lines if not line.endswith("  RAW_SCORE.tsv")]
            (bundle / "SHA256SUMS").write_text("\n".join(kept) + "\n", encoding="utf-8")

        self._assert_violation("HASH_INVENTORY", mutation, rehash=False)

    def test_rejects_hash_mismatch(self) -> None:
        def mutation(bundle: Path) -> None:
            path = bundle / "RAW_SCORE.tsv"
            path.write_bytes(path.read_bytes() + b"\n")

        self._assert_violation("HASH_MISMATCH", mutation, rehash=False)

    def test_rejects_duplicate_hash_path(self) -> None:
        def mutation(bundle: Path) -> None:
            path = bundle / "SHA256SUMS"
            lines = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join([*lines, lines[0]]) + "\n", encoding="utf-8")

        self._assert_violation("HASH_DUPLICATE", mutation, rehash=False)

    def test_rejects_nondeterministic_hash_order(self) -> None:
        def mutation(bundle: Path) -> None:
            path = bundle / "SHA256SUMS"
            lines = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")

        self._assert_violation("HASH_ORDER", mutation, rehash=False)

    def test_rejects_undeclared_extra_file(self) -> None:
        self._assert_violation(
            "UNDECLARED_FILE",
            lambda bundle: (bundle / "UNDECLARED.txt").write_text("extra\n", encoding="utf-8"),
            rehash=False,
        )

    def test_rejects_unknown_source_kind(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            manifest["source_kind"] = "BESPOKE_MAGIC_SOURCE"
            _write_manifest(bundle, manifest)

        self._assert_violation("SOURCE_KIND", mutation)

    def test_rejects_award_force_without_authorized_export(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_nonfixture(bundle)
            manifest = _manifest(bundle)
            manifest["source_kind"] = "AWARD_FORCE_AUTHORIZED_EXPORT"
            manifest["acquisition_authorization"] = "PUBLIC_OFFICIAL"
            _write_manifest(bundle, manifest)

        self._assert_violation("SOURCE_AUTHORIZATION", mutation)

    def test_rejects_competition_platform_without_authorized_export(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_nonfixture(bundle)
            manifest = _manifest(bundle)
            manifest["source_kind"] = "COMPETITION_PLATFORM_AUTHORIZED_EXPORT"
            manifest["acquisition_authorization"] = "PUBLIC_OFFICIAL"
            _write_manifest(bundle, manifest)

        self._assert_violation("SOURCE_AUTHORIZATION", mutation)

    def test_rejects_transcript_without_permission(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_nonfixture(bundle)
            manifest = _manifest(bundle)
            manifest["source_kind"] = "PERMITTED_TRANSCRIPT"
            manifest["acquisition_authorization"] = "PUBLIC_OFFICIAL"
            _write_manifest(bundle, manifest)

        self._assert_violation("SOURCE_AUTHORIZATION", mutation)

    def test_rejects_collapsed_manifest_rights(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            manifest["rights_dimensions"] = ["OPEN_OR_CLOSED"]
            _write_manifest(bundle, manifest)

        self._assert_violation("RIGHTS_DIMENSIONS", mutation)

    def test_rejects_collapsed_rights_report_columns(self) -> None:
        def mutation(bundle: Path) -> None:
            rows = _rows(bundle, "RIGHTS_REPORT.tsv")
            columns = (
                "rights_id",
                "source_family_id",
                "open_or_closed",
                "rights_decision_status",
                "evidence_locator",
                "review_status",
            )
            collapsed = [
                {
                    "rights_id": rows[0]["rights_id"],
                    "source_family_id": rows[0]["source_family_id"],
                    "open_or_closed": "closed",
                    "rights_decision_status": rows[0]["rights_decision_status"],
                    "evidence_locator": rows[0]["evidence_locator"],
                    "review_status": rows[0]["review_status"],
                }
            ]
            _write_table(bundle, "RIGHTS_REPORT.tsv", collapsed, fieldnames=columns)

        self._assert_violation("TSV_SCHEMA", mutation)

    def test_rejects_ambiguous_rights_value(self) -> None:
        self._assert_violation(
            "RIGHTS_VALUE",
            lambda bundle: _mutate_row(
                bundle, "RIGHTS_REPORT.tsv", "model_research_use", "open"
            ),
        )

    def test_rejects_structural_fixture_claiming_observed_data(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            manifest["contains_observed_coffee_data"] = True
            _write_manifest(bundle, manifest)

        self._assert_violation("FIXTURE_OBSERVED_DATA", mutation)

    def test_rejects_structural_fixture_core_eligibility(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            manifest["core_count_eligible"] = True
            _write_manifest(bundle, manifest)

        self._assert_violation("STRUCTURAL_CORE_ELIGIBILITY", mutation)

    def test_rejects_row_fixture_flag_disagreement(self) -> None:
        self._assert_violation(
            "FIXTURE_FLAG",
            lambda bundle: _mutate_row(
                bundle, "RAW_ENTRY.tsv", "structural_test_fixture", "false"
            ),
        )

    def test_rejects_semantic_inference_permission(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            manifest["semantic_inference_permitted"] = True
            _write_manifest(bundle, manifest)

        self._assert_violation("SEMANTIC_INFERENCE", mutation)

    def test_rejects_llm_generated_field_permission(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            manifest["llm_generated_fields_permitted"] = True
            _write_manifest(bundle, manifest)

        self._assert_violation("LLM_FIELDS", mutation)

    def test_rejects_declared_source_hash_drift(self) -> None:
        def mutation(bundle: Path) -> None:
            source = bundle / "STRUCTURAL_SOURCE.txt"
            source.write_bytes(source.read_bytes() + b"changed\n")

        self._assert_violation("SOURCE_HASH_DECLARATION", mutation)

    def test_rejects_source_path_traversal(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            source_files = manifest["source_files"]
            assert isinstance(source_files, list)
            source_files[0]["path"] = "../STRUCTURAL_SOURCE.txt"
            _write_manifest(bundle, manifest)

        self._assert_violation("UNSAFE_PATH", mutation)

    def test_rejects_manifest_record_count_drift(self) -> None:
        def mutation(bundle: Path) -> None:
            manifest = _manifest(bundle)
            counts = manifest["record_counts"]
            assert isinstance(counts, dict)
            counts["RAW_SCORE.tsv"] = 2
            _write_manifest(bundle, manifest)

        self._assert_violation("RECORD_COUNT_MISMATCH", mutation)

    def test_rejects_duplicate_source_identifier(self) -> None:
        def mutation(bundle: Path) -> None:
            rows = _rows(bundle, "RAW_SCORE.tsv")
            rows.append(dict(rows[0]))
            _write_table(bundle, "RAW_SCORE.tsv", rows)

        self._assert_violation("DUPLICATE_IDENTIFIER", mutation)

    def test_rejects_orphan_entry(self) -> None:
        self._assert_violation(
            "ORPHAN_REFERENCE",
            lambda bundle: _mutate_row(
                bundle, "RAW_ENTRY.tsv", "edition_id", "missing-edition"
            ),
        )

    def test_rejects_orphan_score(self) -> None:
        self._assert_violation(
            "ORPHAN_REFERENCE",
            lambda bundle: _mutate_row(
                bundle, "RAW_SCORE.tsv", "preparation_service_id", "missing-service"
            ),
        )

    def test_rejects_preparation_inferred_from_category(self) -> None:
        self._assert_violation(
            "PREPARATION_INFERENCE",
            lambda bundle: _mutate_row(
                bundle,
                "RAW_PREPARATION_SERVICE.tsv",
                "preparation_evidence",
                "INFERRED_FROM_COMPETITION_CATEGORY",
            ),
        )

    def test_rejects_category_to_roast_shortcut(self) -> None:
        def mutation(bundle: Path) -> None:
            rows = _rows(bundle, "RAW_PREPARATION_SERVICE.tsv")
            rows[0].update(
                {
                    "roast_source_text": "filter category",
                    "roast_code": "LIGHT",
                    "roast_evidence": "INFERRED_FROM_COMPETITION_CATEGORY",
                }
            )
            _write_table(bundle, "RAW_PREPARATION_SERVICE.tsv", rows)

        self._assert_violation("ROAST_INFERENCE", mutation)

    def test_rejects_roast_code_without_explicit_source_text(self) -> None:
        def mutation(bundle: Path) -> None:
            rows = _rows(bundle, "RAW_PREPARATION_SERVICE.tsv")
            rows[0].update(
                {
                    "roast_source_text": "",
                    "roast_code": "LIGHT",
                    "roast_evidence": "EXPLICIT_SOURCE_FIELD",
                }
            )
            _write_table(bundle, "RAW_PREPARATION_SERVICE.tsv", rows)

        self._assert_violation("ROAST_INFERENCE", mutation)

    def test_rejects_synthetic_descriptor(self) -> None:
        self._assert_violation(
            "DESCRIPTOR_INVENTION",
            lambda bundle: _mutate_row(
                bundle, "RAW_DESCRIPTOR_ASSERTION.tsv", "extraction_method", "SYNTHETIC"
            ),
        )

    def test_rejects_llm_manufactured_descriptor(self) -> None:
        self._assert_violation(
            "DESCRIPTOR_INVENTION",
            lambda bundle: _mutate_row(
                bundle, "RAW_DESCRIPTOR_ASSERTION.tsv", "extraction_method", "LLM_GENERATED"
            ),
        )

    def test_rejects_inferred_descriptor_from_score(self) -> None:
        self._assert_violation(
            "DESCRIPTOR_INVENTION",
            lambda bundle: _mutate_row(
                bundle,
                "RAW_DESCRIPTOR_ASSERTION.tsv",
                "extraction_method",
                "INFERRED_FROM_SCORE",
            ),
        )

    def test_rejects_descriptor_without_verbatim_span(self) -> None:
        self._assert_violation(
            "DESCRIPTOR_LINEAGE",
            lambda bundle: _mutate_row(
                bundle, "RAW_DESCRIPTOR_ASSERTION.tsv", "source_span", "unrelated text"
            ),
        )

    def test_rejects_unresolved_assertion_actor(self) -> None:
        self._assert_violation(
            "ASSERTION_ACTOR",
            lambda bundle: _mutate_row(
                bundle, "RAW_DESCRIPTOR_ASSERTION.tsv", "assertion_actor_role", "UNKNOWN"
            ),
        )

    def test_rejects_judge_competitor_note_conflation(self) -> None:
        self._assert_violation(
            "ASSERTION_ACTOR",
            lambda bundle: _mutate_row(
                bundle, "RAW_DESCRIPTOR_ASSERTION.tsv", "assertion_actor_role", "COMPETITOR"
            ),
        )

    def test_rejects_semantic_normalization_rule(self) -> None:
        def mutation(bundle: Path) -> None:
            row = {
                "normalization_id": "normalization-001",
                "target_file": "RAW_DESCRIPTOR_ASSERTION.tsv",
                "target_record_id": "fixture-descriptor-001",
                "field_name": "descriptor_text",
                "raw_value": "fixture-citrus",
                "normalized_value": "citrus",
                "normalization_rule": "INFER_CANONICAL_DESCRIPTOR",
                "semantic_change": "false",
                "review_status": "AUTO_ALLOWED",
            }
            _write_table(bundle, "NORMALIZATION_REPORT.tsv", [row])

        self._assert_violation("NORMALIZATION_RULE", mutation)

    def test_rejects_normalization_semantic_change(self) -> None:
        def mutation(bundle: Path) -> None:
            row = {
                "normalization_id": "normalization-001",
                "target_file": "RAW_DESCRIPTOR_ASSERTION.tsv",
                "target_record_id": "fixture-descriptor-001",
                "field_name": "descriptor_text",
                "raw_value": "fixture-citrus",
                "normalized_value": "citrus",
                "normalization_rule": "WHITESPACE_NORMALIZATION",
                "semantic_change": "true",
                "review_status": "REVIEWED_ALLOWED",
            }
            _write_table(bundle, "NORMALIZATION_REPORT.tsv", [row])

        self._assert_violation("SEMANTIC_NORMALIZATION", mutation)

    def test_rejects_judge_row_multiplication(self) -> None:
        def mutation(bundle: Path) -> None:
            rows = _rows(bundle, "EFFECTIVE_RECORD_REPORT.tsv")
            duplicate = dict(rows[0])
            duplicate["effective_record_id"] = "fixture-effective-judge-002"
            rows.append(duplicate)
            _write_table(bundle, "EFFECTIVE_RECORD_REPORT.tsv", rows)

        self._assert_violation("JUDGE_MULTIPLICATION", mutation)

    def test_rejects_judge_observation_count_inflation(self) -> None:
        self._assert_violation(
            "JUDGE_COUNT",
            lambda bundle: _mutate_row(
                bundle, "EFFECTIVE_RECORD_REPORT.tsv", "judge_observation_count", "20"
            ),
        )

    def test_rejects_descriptor_assertion_count_inflation(self) -> None:
        self._assert_violation(
            "DESCRIPTOR_COUNT",
            lambda bundle: _mutate_row(
                bundle,
                "EFFECTIVE_RECORD_REPORT.tsv",
                "descriptor_assertion_count",
                "20",
            ),
        )

    def test_rejects_observed_core_without_fresh_preparation(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_observed_core(bundle)
            _mutate_row(
                bundle,
                "RAW_PREPARATION_SERVICE.tsv",
                "fresh_preparation_confirmed",
                "false",
            )

        self._assert_violation("FRESH_PREPARATION", mutation)

    def test_rejects_model_record_with_pending_model_rights(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_observed_core(bundle, model_eligible=True)
            _mutate_row(bundle, "RIGHTS_REPORT.tsv", "model_research_use", "pending")

        self._assert_violation("MODEL_RIGHTS", mutation)

    def test_rejects_observed_core_with_broken_identity_lineage(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_observed_core(bundle)
            _mutate_row(
                bundle, "RAW_COFFEE_IDENTITY.tsv", "core_count_eligible", "false"
            )

        self._assert_violation("CORE_LINEAGE", mutation)

    def test_rejects_quality_failure_not_blocked(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_nonfixture(bundle)
            manifest = _manifest(bundle)
            results = manifest["quality_gate_results"]
            assert isinstance(results, dict)
            results["ENTRY_IDENTITY_FIELD_ACCURACY"] = 0.5
            results["quality_gate_status"] = "BLOCKED_QUALITY"
            _write_manifest(bundle, manifest)

        self._assert_violation("QUALITY_STATUS", mutation)

    def test_rejects_false_quality_pass(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_nonfixture(bundle)
            manifest = _manifest(bundle)
            results = manifest["quality_gate_results"]
            assert isinstance(results, dict)
            results["FALSE_FLAVOR_DOCUMENT_RATE"] = 0.5
            _write_manifest(bundle, manifest)

        self._assert_violation("QUALITY_STATUS", mutation)

    def test_rejects_insufficient_manual_audit_sample(self) -> None:
        def mutation(bundle: Path) -> None:
            _make_nonfixture(bundle)
            manifest = _manifest(bundle)
            results = manifest["quality_gate_results"]
            assert isinstance(results, dict)
            results["audited_record_count"] = 0
            results["quality_gate_status"] = "BLOCKED_QUALITY"
            _write_manifest(bundle, manifest)

        self._assert_violation("QUALITY_AUDIT_SAMPLE", mutation)


def _run() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Round3KAdapterContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    negative_count = sum(
        name.startswith("test_rejects_")
        for name in unittest.defaultTestLoader.getTestCaseNames(Round3KAdapterContractTests)
    )
    if negative_count < 20:
        raise SystemExit("Round 3K adapter contract requires at least 20 negative tests")
    print("ROUND3K_ADAPTER_CONTRACT_TEST_PASS=true")
    print(f"SUPPORTED_SOURCE_KIND_COUNT={len(SUPPORTED_SOURCE_KINDS)}")
    print(f"NEGATIVE_CONTRACT_TEST_COUNT={negative_count}")
    print("STRUCTURAL_TEST_FIXTURE_CORE_COUNT_ELIGIBLE=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
