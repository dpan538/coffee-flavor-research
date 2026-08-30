#!/usr/bin/env python3
"""Fail-closed Batch 6 semantic corpus and benchmark contract tests."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
POST40 = ROOT / "db" / "data" / "post40k-extension-staging"
GENERATOR = ROOT / "db" / "scripts" / "generate-batch6-semantic-corpus.py"


def rows(name: str, root: Path = CURRENT) -> list[dict[str, str]]:
    with (root / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Batch6SemanticCorpus(unittest.TestCase):
    def test_frozen_40k_snapshot_and_cleaner_reconcile(self) -> None:
        snapshot = json.loads((CURRENT / "CANDIDATE_40K_SNAPSHOT_MANIFEST.json").read_text())
        source = rows("CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv")
        atoms = rows("CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv")
        cleaned = json.loads((CURRENT / "CLEANED_40K_MANIFEST.json").read_text())
        self.assertEqual(snapshot["snapshot_version"], "professional-descriptor-candidate-v2-40k")
        self.assertTrue(snapshot["immutable"])
        self.assertEqual(snapshot["source_assertion_count"], 40030)
        self.assertEqual(len(source), 40030)
        self.assertEqual(sum(row["corpus_segment"] == "POST30K_EXTENSION" for row in source), 10020)
        self.assertEqual(sum(int(row["cleaned_output_atom_count"]) for row in source), len(atoms))
        self.assertTrue(cleaned["source_assertion_reconciliation_pass"])
        self.assertTrue(all(row["cleaner_contract_version"] == "batch4.semantic-cleaner.v2" for row in source))
        self.assertTrue(all(row["model_eligible"] == "false" for row in atoms))

    def test_typed_relations_do_not_promote_observations(self) -> None:
        edges = rows("SEMANTIC_RELATION_EDGE.tsv")
        evidence = rows("SEMANTIC_RELATION_EVIDENCE.tsv")
        self.assertTrue(edges and evidence)
        allowed = {
            "EXACT_EQUIVALENT", "APPROVED_ALIAS_OF", "MORPHOLOGICAL_VARIANT_OF",
            "INSTANCE_OR_SPECIFIC_FORM_OF", "MODIFIES", "COMPONENT_OF",
            "COASSERTED_WITH", "OBSERVED_UNDER_PREPARATION", "OBSERVED_WITH_ROAST_EVIDENCE",
        }
        self.assertTrue(all(row["relation_type"] in allowed for row in edges))
        self.assertTrue(all(row["semantic_evidence_authority"] in {
            "S0_DETERMINISTIC_ORTHOGRAPHIC", "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS",
            "S3_MULTI_SOURCE_MACHINE_CANDIDATE",
        } for row in edges))
        self.assertFalse(any(row["relation_layer"] == "LEXICAL_EQUIVALENCE" and row["relation_type"] == "COASSERTED_WITH" for row in edges))
        self.assertTrue(all(row["human_reviewed"] == "false" and row["sensory_expert_adjudicated"] == "false" for row in edges))
        pairs = {(row["subject_node_id"], row["relation_type"], row["object_node_id"]) for row in edges if row["relation_layer"] == "LEXICAL_EQUIVALENCE"}
        self.assertTrue(all((right, kind, left) in pairs for left, kind, right in pairs))
        self.assertTrue(all(row["raw_definition_published"] == "false" for row in evidence))

    def test_benchmark_distinguishes_known_target_and_open_set(self) -> None:
        cases = rows("CROSS_FORM_BENCHMARK_CANDIDATE.tsv")
        groups = rows("CROSS_FORM_BENCHMARK_GROUP.tsv")
        open_set = rows("OPEN_SET_UNSEEN_TARGET_BENCHMARK.tsv")
        self.assertTrue(cases and groups and open_set)
        by_case = defaultdict(list)
        for row in cases:
            by_case[row["benchmark_case_id"]].append(row)
        for case_rows in by_case.values():
            train = [row for row in case_rows if row["split"] == "TRAIN"]
            test = [row for row in case_rows if row["split"] == "TEST"]
            self.assertTrue(train and test)
            self.assertFalse({row["cleaned_form_hash"] for row in train} & {row["cleaned_form_hash"] for row in test})
            self.assertEqual({row["target_concept_or_cluster_id"] for row in train}, {row["target_concept_or_cluster_id"] for row in test})
            self.assertFalse({row["coffee_sample_group_id"] for row in train} & {row["coffee_sample_group_id"] for row in test})
        self.assertTrue(all(row["target_present_in_training"] == "false" for row in open_set))
        self.assertTrue(all(row["expected_response"] == "ABSTAIN|ONTOLOGY_CANDIDATE|TARGET_NOT_SUPPORTED" for row in open_set))

    def test_smoke_addendum_reconciles_test_only_targets(self) -> None:
        addendum = json.loads((CURRENT / "SMOKE_BENCHMARK_INTERPRETATION_ADDENDUM.json").read_text())
        correction = rows("SMOKE_TARGET_SUPPORT_CORRECTION.tsv")
        self.assertEqual(addendum["SMOKE_FINAL_STATUS"], "ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY")
        self.assertEqual(addendum["SEEN_FORM_KNOWN_TARGET_OUTPUT_COUNT"], 125)
        self.assertEqual(addendum["UNSEEN_FORM_KNOWN_TARGET_OUTPUT_COUNT"], 0)
        self.assertEqual(addendum["UNSEEN_TARGET_OPEN_SET_OUTPUT_COUNT"], 2)
        unsupported = [row for row in correction if row["corrected_status"] == "TRAIN_UNSUPPORTED_TARGET"]
        self.assertEqual(len(unsupported), 2)
        self.assertTrue(all(row["train_output_count"] == "0" and int(row["test_output_count"]) > 0 for row in unsupported))

    def test_review_packets_are_bounded_and_public_safe(self) -> None:
        review = rows("CROSS_FORM_OWNER_REVIEW_PACKET.tsv")
        imports = rows("CROSS_FORM_OWNER_REVIEW_IMPORT_TEMPLATE.tsv")
        human = rows("HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv")
        self.assertLessEqual(len(review), 200)
        self.assertEqual(len(review), len(imports))
        self.assertEqual(len(human), 500)
        self.assertTrue(all(not row["project_owner_decision"] for row in review))
        self.assertTrue(all(not row["reviewer_decision"] and not row["reviewer_id"] for row in human))
        forbidden = {"raw_field_text", "atomic_source_text", "source_native_form", "canonical_concept_label"}
        for name in ["CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv", "CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv", "CROSS_FORM_OWNER_REVIEW_PACKET.tsv", "HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv"]:
            with (CURRENT / name).open(encoding="utf-8", newline="") as handle:
                self.assertFalse(forbidden & set(csv.DictReader(handle, delimiter="\t").fieldnames or []), name)

    def test_manifest_hashes_and_repeat_generation_are_stable(self) -> None:
        listed = {
            name: value
            for value, name in (
                line.split("  ", 1)
                for line in (CURRENT / "SHA256SUMS").read_text().splitlines()
            )
        }
        self.assertTrue(all(digest(CURRENT / name) == value for name, value in listed.items()))
        self.assertTrue((POST40 / "SHA256SUMS").is_file())
        before = digest(CURRENT / "SHA256SUMS")
        subprocess.run([sys.executable, "-B", str(GENERATOR)], cwd=ROOT, check=True, capture_output=True, text=True)
        self.assertEqual(digest(CURRENT / "SHA256SUMS"), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
