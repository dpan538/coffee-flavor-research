import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import data_supervision_r5 as d


class SourceSupervisionTests(unittest.TestCase):
    def parsed(self):
        rows = []
        for identity, terms, value in [("a", ["sensory.apple"], 0), ("b", ["sensory.orange"], 1), ("t", ["sensory.apple", "sensory.orange"], None)]:
            rows.append({"observation_unit_id": identity, "strict_D0_concepts": terms, "legacy_R1_fixed_lexical_concepts": terms,
                         "ordinal_intensity_measurements": {k: {"value": value, "status": "OBSERVED" if value is not None else "NOT_MEASURED"} for k in d.ORDINAL_COLUMNS.values()}, "ordinal_intensity_masks": {k: value is not None for k in d.ORDINAL_COLUMNS.values()}})
        return {"observation_units": rows, "samples": [{"sample_id": "synthetic", "group_id": "same-coffee", "old_record_id": "old-record", "old_split": "HISTORICAL_REGRESSION", "traceable_coffee_name": True, "three_disjoint_observation_roles_possible": True, "ordered_observation_unit_ids": ["a", "b", "t"]}]}

    def build(self, parsed):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "synthetic.json"
            path.write_text(json.dumps({"registered_utc": "synthetic-fixture-not-actual-freeze", "data_supervision": d.proposal(), "source_parse_sha256": d.contract_parse_digest(parsed), "mapping_choice": "STRICT_D0_GOVERNED_PLUS_ORIGINAL_EXPLICIT_BROAD"}))
            return d.build_examples(parsed, path)

    def test_independent_reference_retains_A_and_B_overlap(self):
        row = self.build(self.parsed())[0]
        self.assertEqual(row["relevance_full"], {"sensory.apple": 1, "sensory.orange": 1})
        self.assertEqual(row["relevance_unexpressed"], {"sensory.orange": 1})
        self.assertNotIn(row["A_observation_unit_id"], row["T_observation_unit_ids"])
        self.assertNotIn(row["B_observation_unit_id"], row["T_observation_unit_ids"])

    def test_zero_is_low_and_missing_T_is_not_zero(self):
        row = self.build(self.parsed())[0]
        self.assertEqual(row["A_ordinal_measurements"]["taste.bitterness"]["value"], 0)
        self.assertEqual(row["T_ordinal"]["taste.bitterness"]["values"], [None])
        self.assertEqual(row["T_ordinal"]["taste.bitterness"]["masks"], [False])
        self.assertIsNone(row["T_ordinal"]["taste.bitterness"]["distribution"])

    def test_ordinal_reference_is_distribution_not_interval_mean(self):
        parsed = self.parsed()
        parsed["observation_units"][-1]["ordinal_intensity_measurements"] = {k: {"value": 2, "status": "OBSERVED"} for k in d.ORDINAL_COLUMNS.values()}
        parsed["observation_units"][-1]["ordinal_intensity_masks"] = {k: True for k in d.ORDINAL_COLUMNS.values()}
        row = self.build(parsed)[0]
        self.assertEqual(row["T_ordinal"]["taste.bitterness"]["distribution"], [0, 0, 1, 0, 0])
        self.assertEqual(row["T_ordinal"]["taste.bitterness"]["cumulative_probabilities"], [0, 0, 1, 1])

    def test_same_raw_observation_cannot_be_input_and_reference(self):
        parsed = self.parsed()
        parsed["samples"][0]["ordered_observation_unit_ids"] = ["a", "b", "a"]
        with self.assertRaisesRegex(ValueError, "DISJOINT_ORIGINAL"):
            self.build(parsed)

    def test_empty_input_mapping_does_not_rotate_roles(self):
        parsed = self.parsed()
        parsed["observation_units"][0]["strict_D0_concepts"] = []
        row = self.build(parsed)[0]
        self.assertEqual(row["A"], [])
        self.assertEqual(row["A_observation_unit_id"], "a")
        self.assertEqual(row["B_observation_unit_id"], "b")

    def test_no_formal_examples_before_protocol_freeze(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "empty.json"
            path.write_text("{}")
            with self.assertRaisesRegex(ValueError, "FROZEN_FIRST"):
                d.build_examples(self.parsed(), path)

    def test_unmapped_diagnostics_do_not_create_fine_truth(self):
        self.assertIn("NEGATION", d.diagnostic_unmapped_reason("not chocolate"))
        self.assertIn("NOT_SPLIT", d.diagnostic_unmapped_reason("chocolate/nuts"))

    def test_unicode_parse_hash_uses_frozen_root_canonicalization(self):
        from flavor_m2_r1 import digest
        parsed = self.parsed()
        parsed["source_label"] = "средняя 咖啡"
        self.assertEqual(d.contract_parse_digest(parsed), digest(parsed))
        self.assertNotEqual(d.contract_parse_digest(parsed), d.r4.digest(parsed))
        self.assertEqual(len(self.build(parsed)), 1)

    def test_reference_disagreement_keeps_missing_reports_and_single_grader_denominator(self):
        parsed = self.parsed()
        for row in parsed["observation_units"]:
            row["grader_hash"] = row["observation_unit_id"]
        parsed["observation_units"][1]["strict_D0_concepts"] = ["sensory.apple"]
        parsed["observation_units"][2]["strict_D0_concepts"] = []
        parsed["samples"][0]["raw_grader_rows"] = 3
        parsed["samples"].append({**parsed["samples"][0], "sample_id": "single-grader",
                                  "group_id": "another-coffee", "raw_grader_rows": 1,
                                  "ordered_observation_unit_ids": ["a"]})
        pairs, summary = d.reference_agreement(parsed)
        result = summary["cohorts"]["HISTORICAL_REGRESSION"]
        self.assertEqual(len(pairs), 3)
        self.assertEqual(result["all_named_coffee_dependency_groups"], 2)
        self.assertEqual(result["source_samples_without_two_grader_pair"], 1)
        self.assertEqual(result["both_fine_mapped_pairs"], 1)
        self.assertEqual(result["missing_fine_pair_comparisons"], 2)
        self.assertEqual(result["symmetric_exact_match_coffee_macro"], 1)
        numeric = result["ordinal"]["taste.bitterness"]
        self.assertEqual(numeric["observed_pairs"], 1)
        self.assertEqual(numeric["missing_pairs"], 2)
        self.assertEqual(numeric["ordinal_threshold_disagreement_coffee_macro"], .25)


if __name__ == "__main__":
    unittest.main()
