"""Field-scope correction tests; synthetic cases never sensory labels."""

import copy
import unittest
from unittest.mock import patch

import local_scope_repair_r7 as s


class LocalScopeTests(unittest.TestCase):
    def setUp(self):
        self.record, self.units, self.patch = s.synthetic_inputs()

    def test_registered_mechanism_fixtures_pass(self):
        self.assertTrue(all(s.synthetic_checks().values()))

    def test_exact_predicate_not_a_general_body_or_tea_filter(self):
        self.assertTrue(
            s.blocked({"field": "body_description", "normalized_span": "tea"})
        )
        for field, word in [
            ("aroma", "tea"),
            ("body_description", "black tea"),
            ("body_description", "tea and milk"),
            ("body_description", "herbaceous"),
        ]:
            self.assertFalse(s.blocked({"field": field, "normalized_span": word}))

    def test_does_not_mutate_original_inputs_or_frozen_rules(self):
        before = copy.deepcopy((self.record, self.units, self.patch))
        s.apply_inputs(self.record, self.units, self.patch)
        self.assertEqual((self.record, self.units, self.patch), before)

    def test_no_real_rule_selection_or_fit_during_application(self):
        with patch.object(
            s.m.semantic, "fit_patch", side_effect=AssertionError("NO_RULE_SELECTION")
        ):
            output = s.apply_inputs(self.record, self.units, self.patch)
        self.assertEqual(output["mapping_patch_sha256"], self.patch["patch_sha256"])

    def test_blocked_trace_preserves_raw_span_bounds_and_prior_projection(self):
        old = s.m.semantic.apply_inputs(self.record, self.units, self.patch)
        new = s.apply_inputs(self.record, self.units, self.patch)
        for before, after in zip(
            old["mapping_input_trace"], new["mapping_input_trace"], strict=True
        ):
            if s.blocked(after):
                for key in (
                    "source_text",
                    "raw_span",
                    "span_start",
                    "span_end",
                    "source_column",
                    "observation_unit_id",
                    "polarity",
                ):
                    self.assertEqual(after[key], before[key])
                self.assertEqual(after["legacy_projected_concepts"], [s.GREEN])
                self.assertFalse(after["flavour_support_allowed"])
                self.assertEqual(after["concepts"], [])
                self.assertEqual(after["added_concepts"], [])

    def test_nonbody_later_trace_is_reaccumulated_after_blocked_body(self):
        for unit in self.units.values():
            del unit["description_fields"]["aroma"]
            unit["description_fields"]["sweetness_description"] = {
                "source_text": "tea",
                "source_column": 14,
            }
        output = s.apply_inputs(self.record, self.units, self.patch)
        for role in ("A", "B"):
            self.assertIn(s.GREEN, output[role])
            later = next(
                t
                for t in output["mapping_input_trace"]
                if t["role"] == role and t["field"] == "sweetness_description"
            )
            self.assertEqual(later["added_concepts"], [s.GREEN])

    def test_nonbody_rules_and_original_base_are_identical(self):
        for unit in self.units.values():
            del unit["description_fields"]["body_description"]
        self.record["A"] = ["sensory.apple", s.GREEN]
        old = s.m.semantic.apply_inputs(self.record, self.units, self.patch)
        new = s.apply_inputs(self.record, self.units, self.patch)
        self.assertEqual(
            {k: v for k, v in new.items() if k != "source_scope_repair"}, old
        )

    def test_T_change_cannot_change_mapped_inputs_or_B_coverage(self):
        changed = copy.deepcopy(self.record)
        changed["relevance_full"] = {"sensory.orange": 20}
        changed["relevance_unexpressed"] = {}
        a = s.apply_inputs(self.record, self.units, self.patch)
        b = s.apply_inputs(changed, self.units, self.patch)
        for field in ("A", "B", "mapping_input_trace"):
            self.assertEqual(a[field], b[field])
        self.assertEqual(
            s.m.information.coverage_for([a], set()),
            s.m.information.coverage_for([b], set()),
        )

    def test_held_coverage_rejected_before_inspecting_units(self):
        with self.assertRaisesRegex(ValueError, "TRAIN_HELD_OVERLAP"):
            s.coverage_inputs([self.record], {}, self.patch, {self.record["group_id"]})

    def test_body_other_registered_form_keeps_old_behavior(self):
        for unit in self.units.values():
            unit["description_fields"] = {
                "body_description": {"source_text": "herbaceous", "source_column": 20}
            }
        old = s.m.semantic.apply_inputs(self.record, self.units, self.patch)
        new = s.apply_inputs(self.record, self.units, self.patch)
        self.assertEqual(old["A"], new["A"])
        self.assertEqual(old["mapping_input_trace"], new["mapping_input_trace"])

    def test_reporting_A_is_fixed_reference_not_interpreted_evidence(self):
        old = [{"record_id": "case", "A": ["sensory.apple"]}]
        rows = [
            {
                "record_id": "case",
                "A": ["sensory.apple", "sensory.orange"],
                "B": [s.GREEN],
                "interpreted_A": ["sensory.apple", "sensory.orange"],
                "interpreted_B": [s.GREEN],
                "ranking": ["sensory.orange"],
                "full_T": {"sensory.orange": 1},
                "hidden_T": {"sensory.orange": 1},
                "state": {"actual": "unchanged"},
            }
        ]
        original = copy.deepcopy(rows)
        result = s.corrected_reporting_rows(rows, old)
        self.assertEqual(result[0]["A"], old[0]["A"])
        self.assertNotIn("B", result[0])
        self.assertEqual(rows, original)
        for field in (
            "interpreted_A",
            "interpreted_B",
            "ranking",
            "state",
            "full_T",
            "hidden_T",
        ):
            self.assertEqual(result[0][field], rows[0][field])


if __name__ == "__main__":
    unittest.main()
