import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import alignment_metrics_r2 as metric


class AlignmentMetricTests(unittest.TestCase):
    def test_one_prediction_does_not_cover_every_related_target(self):
        result = metric.semantic_result(
            ["sensory.orange"], ["sensory.lemon", "sensory.apple"]
        )
        self.assertEqual(result["related_matches"], 1)
        self.assertEqual(result["gap"], 0.875)

    def test_repeated_visible_evidence_is_not_new_recovery(self):
        self.assertEqual(
            metric.semantic_gap(
                ["sensory.lemon"], ["sensory.orange"], ["sensory.lemon"]
            ),
            1,
        )

    def test_broadening_and_duplicate_predictions_cannot_improve_gap(self):
        target = ["sensory.lemon", "sensory.apple"]
        self.assertEqual(
            metric.semantic_gap(["attribute.fruity", "broad.citrus"], target), 1
        )
        self.assertEqual(metric.semantic_gap(["sensory.lemon"] * 8, target), 0.5)

    def test_empty_reference_is_unknown_but_empty_output_is_failure(self):
        self.assertIsNone(metric.semantic_gap(["sensory.lemon"], []))
        self.assertEqual(metric.semantic_gap([], ["sensory.lemon"]), 1)

    def test_out_of_vocabulary_target_cannot_disappear_from_denominator(self):
        result = metric.semantic_result(
            ["sensory.lemon"],
            ["sensory.lemon", "sensory.jasmine"],
            vocabulary=["sensory.lemon"],
        )
        self.assertEqual(result["gap"], 0.5)
        self.assertEqual(result["candidate_target_coverage"], 0.5)

    def test_coffee_group_weight_and_paired_scope_are_preserved(self):
        rows = [{"group_id": "a", "gap": 0.0}] * 20 + [
            {"group_id": "b", "gap": 1.0},
            {"group_id": "c", "gap": None},
        ]
        summary = metric.grouped_summary(rows)
        self.assertEqual(summary["group_macro_mean"], 0.5)
        self.assertEqual(summary["groups"], 3)
        self.assertEqual(summary["labelled_groups"], 2)
        with self.assertRaisesRegex(ValueError, "GROUPS_DIFFER"):
            metric.paired_group_delta(rows, rows[:1])


if __name__ == "__main__":
    unittest.main()
