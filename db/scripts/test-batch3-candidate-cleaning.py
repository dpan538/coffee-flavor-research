#!/usr/bin/env python3
"""Positive/negative semantic fixtures and Batch 3 isolation checks."""

from __future__ import annotations

import csv
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "db" / "scripts" / "build-batch3-cleaning-staging.py"
CURRENT = ROOT / "db" / "data" / "current"


def load_builder():
    spec = importlib.util.spec_from_file_location("batch3_cleaner", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot import Batch 3 cleaner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_builder()


def rows(name: str) -> list[dict[str, str]]:
    with (CURRENT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class SemanticPositiveFixtures(unittest.TestCase):
    def test_established_compound_is_retained(self) -> None:
        cleaned, decision, _, confidence = B.clean_atom("Dark Chocolate")
        self.assertEqual(cleaned, [("dark chocolate", "STRICT_FLAVOR")])
        self.assertEqual(decision, "KEEP_AS_ESTABLISHED_COMPOUND")
        self.assertEqual(confidence, "1.000000")

    def test_safe_coordinated_list_is_split(self) -> None:
        cleaned, decision, _, _ = B.clean_atom("jasmine and peach")
        self.assertEqual(cleaned, [("jasmine", "STRICT_FLAVOR"), ("peach", "STRICT_FLAVOR")])
        self.assertEqual(decision, "SAFE_LIST_SPLIT")

    def test_sentence_leakage_is_rejected(self) -> None:
        cleaned, decision, _, _ = B.clean_atom(
            "This coffee was grown at high elevation by a producer in the western region"
        )
        self.assertEqual(cleaned[0][1], "NON_DESCRIPTOR")
        self.assertEqual(decision, "SENTENCE_LEAKAGE_REJECTED")

    def test_modifier_is_preserved_separately(self) -> None:
        cleaned, decision, _, _ = B.clean_atom("ripe peach")
        self.assertEqual(
            cleaned,
            [("peach", "STRICT_FLAVOR"), ("ripe", "INTENSITY_OR_QUALITY_MODIFIER")],
        )
        self.assertEqual(decision, "HEAD_PLUS_MODIFIER")

    def test_broad_and_strict_classes_are_distinct(self) -> None:
        self.assertEqual(B.clean_atom("juicy")[0], [("juicy", "BROAD_SENSORY")])
        self.assertEqual(B.clean_atom("peach")[0], [("peach", "STRICT_FLAVOR")])

    def test_same_coe_name_and_year_resolves_without_url_only_identity(self) -> None:
        score, state = B.coe_name_year_match_state(
            "Finca La Esperanza",
            "2008",
            "https://farmdirectory.cupofexcellence.org/listing/1-finca-la-esperanza-colombia-2008/",
            "2008",
        )
        self.assertEqual(score, 1.0)
        self.assertEqual(state, "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD")

    def test_legitimate_parallel_layers_retain_both_artifacts(self) -> None:
        decision = B.coe_publication_duplicate_policy(
            "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD",
            3,
            independent_observation=True,
        )
        self.assertEqual(decision["retain_both_source_artifacts"], "true")
        self.assertEqual(
            decision["publication_layer_relation"],
            "DISTINCT_EVIDENCE_PRODUCER_OR_OBSERVATION",
        )
        self.assertEqual(decision["duplicate_assertion_credit_suppressed"], "false")

    def test_zenodo_observations_group_under_samples(self) -> None:
        manifest = json.loads((CURRENT / "CURRENT_DATA_MANIFEST.json").read_text(encoding="utf-8"))
        metrics = manifest["batch3_cleaning_metrics"]
        self.assertEqual(metrics["zenodo_panelist_sample_observation_count"], 360)
        self.assertEqual(metrics["zenodo_effective_sample_count"], 112)
        self.assertEqual(metrics["zenodo_sample_consensus_record_count"], 112)


class SemanticNegativeFixtures(unittest.TestCase):
    def test_ranking_score_and_process_are_not_flavors(self) -> None:
        self.assertEqual(B.clean_atom("ranking")[0][0][1], "NON_DESCRIPTOR")
        self.assertEqual(B.clean_atom("score")[0][0][1], "NON_DESCRIPTOR")
        self.assertEqual(B.clean_atom("washed process")[0][0][1], "PROCESS_OR_ORIGIN_METADATA")

    def test_cross_language_form_is_not_silently_translated(self) -> None:
        by_label, _ = B.ontology()
        state, concept, method, _ = B.map_concept("limón", "STRICT_FLAVOR", by_label)
        self.assertEqual(state, "ONTOLOGY_CANDIDATE")
        self.assertEqual(concept, "")
        self.assertEqual(method, "MACHINE_PROVISIONAL_REVIEW")

    def test_same_name_different_year_is_not_merged(self) -> None:
        _, state = B.coe_name_year_match_state(
            "La Esperanza",
            "2008",
            "https://farmdirectory.cupofexcellence.org/listing/1-la-esperanza-colombia-2020/",
            "2020",
        )
        self.assertEqual(state, "DISTINCT_ROUND_OR_SERVICE")

    def test_publication_mirror_cannot_receive_duplicate_assertion_credit(self) -> None:
        decision = B.coe_publication_duplicate_policy(
            "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD",
            3,
            independent_observation=False,
        )
        self.assertEqual(decision["retain_both_source_artifacts"], "true")
        self.assertEqual(decision["duplicate_assertion_credit_suppressed"], "true")
        self.assertEqual(decision["suppressed_assertion_count"], "3")

    def test_evidence_rights_and_pair_surfaces_fail_closed(self) -> None:
        source = {row["descriptor_assertion_id"]: row for row in rows("CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")}
        for decision in rows("SEMANTIC_CLEANING_DECISION.tsv"):
            original = source[decision["descriptor_assertion_id"]]
            self.assertEqual(decision["evidence_tier"], original["evidence_tier"])
            self.assertEqual(decision["rights_state"], original["rights_state"])
            self.assertEqual(decision["model_eligible"], "false")
        pair_rows = rows("CLEANED_PAIR_EVENT_RECEIPT.tsv")
        self.assertTrue(all(row["pair_counted_as_source_assertion"] == "false" for row in pair_rows))

    def test_frozen_snapshot_excludes_post20k_extension(self) -> None:
        snapshot = json.loads((CURRENT / "CANDIDATE_20K_SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertFalse(snapshot["post20k_extension_included_in_snapshot"])
        self.assertEqual(snapshot["frozen_mechanically_deinflated_assertion_count"], 20003)


if __name__ == "__main__":
    unittest.main(verbosity=2)
