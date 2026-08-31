#!/usr/bin/env python3
"""Batch 4 fixtures and cleaned-30k governance artifact contract."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
STAGING = ROOT / "db" / "data" / "candidate-cleaning-v2-staging"
BUILDER_PATH = ROOT / "db" / "scripts" / "build-batch4-cleaning-staging.py"
GENERATOR = ROOT / "db" / "scripts" / "generate-batch4-cleaned-30k.py"
BATCH6_GENERATOR = ROOT / "db" / "scripts" / "generate-batch6-semantic-corpus.py"
BATCH7_RUNNER = ROOT / "db" / "scripts" / "descriptor-pipeline.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("batch4_cleaner", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Batch 4 cleaner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


B = load_builder()


def rows(name: str, root: Path = CURRENT) -> list[dict[str, str]]:
    with (root / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PositiveFixtures(unittest.TestCase):
    def test_source_assertion_splits_into_multiple_valid_output_atoms(self) -> None:
        cleaned, segmentation, _, _ = B.V1.clean_atom("jasmine and peach")
        self.assertEqual(segmentation, "SAFE_LIST_SPLIT")
        self.assertEqual(B.disposition_for(cleaned, segmentation), "VALID_COMPOUND_SPLIT")
        self.assertEqual(cleaned, [("jasmine", "STRICT_FLAVOR"), ("peach", "STRICT_FLAVOR")])

    def test_compound_is_preserved(self) -> None:
        cleaned, segmentation, _, _ = B.V1.clean_atom("dark chocolate")
        self.assertEqual(segmentation, "KEEP_AS_ESTABLISHED_COMPOUND")
        self.assertEqual(B.disposition_for(cleaned, segmentation), "VALID_COMPOUND_PRESERVED")

    def test_modifier_is_separated(self) -> None:
        cleaned, segmentation, _, _ = B.V1.clean_atom("ripe peach")
        self.assertEqual(segmentation, "HEAD_PLUS_MODIFIER")
        self.assertEqual(cleaned[1], ("ripe", "INTENSITY_OR_QUALITY_MODIFIER"))

    def test_ontology_alias_consolidates_to_exact_cluster(self) -> None:
        by_label, _ = B.V1.ontology()
        alias = B.v2_mapping("black currant", "STRICT_FLAVOR", "en", by_label)
        exact = B.v2_mapping("blackcurrant", "STRICT_FLAVOR", "en", by_label)
        self.assertEqual(alias[0], "EXISTING_CANONICAL_ALIAS")
        self.assertEqual(alias[1], exact[1])
        self.assertEqual(
            B.cluster_id_for(B.sha256_text("black currant"), alias[0], alias[1], alias[4]),
            B.cluster_id_for(B.sha256_text("blackcurrant"), exact[0], exact[1], exact[4]),
        )

    def test_genuine_ontology_candidate_remains_candidate(self) -> None:
        by_label, _ = B.V1.ontology()
        mapping = B.v2_mapping("unmapped sensory nebula", "STRICT_FLAVOR", "en", by_label)
        self.assertEqual(mapping[0], "GENUINE_ONTOLOGY_CANDIDATE")
        self.assertEqual(mapping[2], "NO_GOVERNED_AUTHORITY")

    def test_gold_mapping_remains_non_human_reviewed(self) -> None:
        gold = next(row for row in rows("SEMANTIC_CLEANING_V2_DECISION.tsv") if row["collection_tier"] == "GOLD")
        self.assertEqual(gold["human_reviewed"], "false")
        self.assertEqual(gold["expert_adjudicated"], "false")

    def test_zenodo_sample_keeps_all_panelists_in_one_group(self) -> None:
        ledger = rows("CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv")
        zenodo = [row for row in ledger if row["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset"]
        identity_by_effective: dict[str, set[str]] = defaultdict(set)
        for row in zenodo:
            identity_by_effective[row["effective_record_id"]].add(row["coffee_identity_id"])
        self.assertTrue(identity_by_effective)
        self.assertTrue(all(len(values) == 1 for values in identity_by_effective.values()))
        group_rows = rows("GROUPED_SPLIT_GROUPS.tsv")
        group_by_effective: dict[str, set[str]] = defaultdict(set)
        for row in group_rows:
            for effective_id in filter(None, row["effective_record_ids"].split("|")):
                group_by_effective[effective_id].add(row["split_group_id"])
        self.assertTrue(all(len(group_by_effective[key]) == 1 for key in identity_by_effective))

    def test_mixed_rights_cluster_stays_separated_by_purpose(self) -> None:
        propagation = rows("RIGHTS_PROPAGATION_RECEIPT.tsv")
        atom_rows = [row for row in propagation if row["propagation_layer"] == "CLEANED_OUTPUT_ATOM"]
        clusters = [row for row in propagation if row["propagation_layer"] == "CONCEPT_CLUSTER"]
        self.assertTrue(any(row["NONCOMMERCIAL_MODEL_RESEARCH"] == "AFFIRMATIVE_WITH_CONDITIONS" for row in atom_rows))
        self.assertTrue(any(row["NONCOMMERCIAL_MODEL_RESEARCH"] == "UNKNOWN" for row in clusters))
        subset = next(row for row in propagation if row["propagation_entity_id"] == "subset.noncommercial_research_permitted")
        self.assertEqual(subset["NONCOMMERCIAL_MODEL_RESEARCH"], "AFFIRMATIVE_WITH_CONDITIONS")

    def test_coe_false_identity_candidate_is_not_merged(self) -> None:
        coe = rows("COE_ENTITY_RESOLUTION_V2.tsv")
        self.assertTrue(any(row["match_state"] in {"DISTINCT_RECORD", "INSUFFICIENT_EVIDENCE", "POSSIBLE_SAME_RECORD"} for row in coe))
        self.assertTrue(all(row["identity_merge_authorized"] == "false" for row in coe))


class NegativeFixtures(unittest.TestCase):
    def test_human_review_is_not_fabricated(self) -> None:
        review = rows("PROJECT_OWNER_REVIEW_PACKET.tsv")
        audit = rows("HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv")
        self.assertTrue(all(not row["project_owner_decision"] for row in review))
        self.assertTrue(all(not row["human_disposition"] and not row["reviewer_id"] for row in audit))

    def test_scalar_rights_are_not_copied_to_all_purposes(self) -> None:
        matrix = rows("PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv")
        by_artifact: dict[str, set[str]] = defaultdict(set)
        for row in matrix:
            by_artifact[row["source_artifact_id"]].add(row["purpose_rights_status"])
        self.assertTrue(all(len(states) >= 2 for states in by_artifact.values()))
        self.assertFalse(any(row["purpose"] == "COMMERCIAL_MODEL_TRAINING" and row["purpose_rights_status"] == "AFFIRMATIVE" for row in matrix))

    def test_score_is_not_converted_to_descriptor(self) -> None:
        cleaned, _, _, _ = B.V1.clean_atom("score")
        self.assertEqual(cleaned, [("score", "NON_DESCRIPTOR")])

    def test_translation_is_not_converted_to_source_assertion(self) -> None:
        by_label, _ = B.V1.ontology()
        mapping = B.v2_mapping("桃", "STRICT_FLAVOR", "zh", by_label)
        self.assertEqual(mapping[0], "CROSS_LANGUAGE_REVIEW_REQUIRED")
        self.assertFalse(mapping[1])

    def test_same_sample_is_not_split_across_feasibility_buckets(self) -> None:
        leakage = {row["leakage_check"]: row for row in rows("GROUPED_SPLIT_LEAKAGE_AUDIT.tsv")}
        self.assertEqual(leakage["SAMPLE_OR_EFFECTIVE_RECORD"]["cross_bucket_leak_count"], "0")

    def test_pair_event_is_not_counted_as_source_assertion(self) -> None:
        snapshot = json.loads((CURRENT / "CANDIDATE_30K_SNAPSHOT_MANIFEST.json").read_text())
        manifest = json.loads((CURRENT / "CURRENT_DATA_MANIFEST.json").read_text())
        self.assertEqual(snapshot["mechanically_deinflated_source_assertion_count"], 30010)
        self.assertNotEqual(manifest["batch4_metrics"]["pair_metrics"]["pair_event_count"], 30010)

    def test_ontology_candidate_is_not_auto_promoted(self) -> None:
        mappings = rows("ONTOLOGY_CONSOLIDATION_MAP.tsv")
        candidates = [row for row in mappings if row["mapping_state"] == "GENUINE_ONTOLOGY_CANDIDATE"]
        self.assertTrue(candidates)
        self.assertTrue(all(row["normalization_authority"] == "NO_GOVERNED_AUTHORITY" for row in candidates))

    def test_coe_is_not_deleted_to_improve_balance(self) -> None:
        ledger = rows("CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv")
        self.assertGreater(sum(row["source_family_id"] == "family.ace_cup_of_excellence" for row in ledger), 20000)


class ArtifactContract(unittest.TestCase):
    REQUIRED = {
        "CANDIDATE_30K_SNAPSHOT_MANIFEST.json",
        "CLEANER_V1_V2_DELTA.tsv",
        "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv",
        "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv",
        "SEMANTIC_CLEANING_V2_DECISION.tsv",
        "CONCEPT_CLUSTER.tsv",
        "ONTOLOGY_CONSOLIDATION_MAP.tsv",
        "ONTOLOGY_GAP_REGISTER.tsv",
        "MACHINE_GOVERNED_MAPPING.tsv",
        "PROJECT_OWNER_REVIEW_PACKET.tsv",
        "PROJECT_OWNER_REVIEW_IMPORT_TEMPLATE.tsv",
        "HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv",
        "PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv",
        "RIGHTS_PROPAGATION_RECEIPT.tsv",
        "GROUPED_SPLIT_FEASIBILITY.tsv",
        "GROUPED_SPLIT_GROUPS.tsv",
        "GROUPED_SPLIT_LEAKAGE_AUDIT.tsv",
        "SOURCE_FAMILY_HOLDOUT_PLAN.tsv",
        "YEAR_HOLDOUT_PLAN.tsv",
        "PAIR_EVENT_CONTRIBUTION_DISTRIBUTION.tsv",
        "CLEANED_30K_PAIR_EVENT_RECEIPT.tsv",
        "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json",
        "CURRENT_DATA_MANIFEST.json",
        "SHA256SUMS",
    }

    def test_required_artifacts_and_counts(self) -> None:
        self.assertFalse(self.REQUIRED - {path.name for path in CURRENT.iterdir()})
        decisions = rows("SEMANTIC_CLEANING_V2_DECISION.tsv")
        atoms = rows("CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv")
        self.assertEqual(len(decisions), 30010)
        self.assertEqual(len(atoms), sum(int(row["cleaned_output_atom_count"]) for row in decisions))
        self.assertEqual(len(rows("CLEANER_V1_V2_DELTA.tsv")), 20003)
        self.assertLessEqual(len(rows("PROJECT_OWNER_REVIEW_PACKET.tsv")), 250)
        self.assertGreaterEqual(len(rows("HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv")), 800)
        self.assertLessEqual(len(rows("HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv")), 1000)

    def test_rights_completeness_and_authority_integrity(self) -> None:
        artifacts = rows("BATCH4_ARTIFACT_RIGHTS_INPUT.tsv", STAGING)
        matrix = rows("PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv")
        self.assertEqual(len(matrix), len(artifacts) * 8)
        governed = rows("MACHINE_GOVERNED_MAPPING.tsv")
        allowed = {
            "EXISTING_CANONICAL_EXACT",
            "EXISTING_CANONICAL_ALIAS",
            "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT",
        }
        self.assertTrue(all(row["mapping_state"] in allowed for row in governed))
        self.assertTrue(all(row["project_owner_reviewed"] == "false" for row in governed))

    def test_public_boundary(self) -> None:
        forbidden_columns = {
            "raw_field_text", "atomic_source_text", "source_native_form",
            "provisional_normalized_form", "canonical_concept_label",
        }
        for name in [
            "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv",
            "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv",
            "ONTOLOGY_CONSOLIDATION_MAP.tsv",
            "HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv",
        ]:
            with (CURRENT / name).open(encoding="utf-8", newline="") as handle:
                fieldnames = set(csv.DictReader(handle, delimiter="\t").fieldnames or [])
            self.assertFalse(fieldnames & forbidden_columns, name)

    def test_snapshot_and_no_model_contract(self) -> None:
        snapshot = json.loads((CURRENT / "CANDIDATE_30K_SNAPSHOT_MANIFEST.json").read_text())
        smoke = json.loads((CURRENT / "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json").read_text())
        self.assertEqual(snapshot["snapshot_version"], "professional-descriptor-candidate-v1-30k")
        self.assertTrue(snapshot["candidate_20k_snapshot_preserved"])
        self.assertFalse(snapshot["post30k_extension_included_in_snapshot"])
        self.assertFalse(snapshot["training_corpus_frozen"])
        self.assertFalse(smoke["model_training_run"])
        self.assertFalse(smoke["training_split_created"])

    def test_checksums_and_generator_are_deterministic(self) -> None:
        expected = {}
        for line in (CURRENT / "SHA256SUMS").read_text().splitlines():
            value, name = line.split("  ", 1)
            expected[name] = value
        self.assertTrue(expected)
        self.assertTrue(all(digest(CURRENT / name) == value for name, value in expected.items()))
        before = digest(CURRENT / "SHA256SUMS")
        subprocess.run([sys.executable, "-B", str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, "-B", str(BATCH6_GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, "-B", str(BATCH7_RUNNER), "semantic"], cwd=ROOT, check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, "-B", str(BATCH7_RUNNER), "checkpoint"], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(digest(CURRENT / "SHA256SUMS"), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
