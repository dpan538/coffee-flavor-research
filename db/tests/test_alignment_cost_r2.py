import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import evaluate_alignment_cost_r2 as cost


def row(i, gap=0.2, options=20, final=0):
    return {
        "record_id": str(i),
        "group_id": str(i),
        "target_sha256": "fixed_T",
        "visible_sha256": "fixed_A",
        "candidate_vocabulary": ["sensory.lemon"],
        "gap": gap,
        "ordinary_questions": 5 if options == 20 else 6,
        "ordinary_options": options,
        "final_comparison_candidates": final,
        "ordinary_endpoint": True,
        "path": "P1" if options == 20 else "P4",
    }


class InformationCostTests(unittest.TestCase):
    def test_primary_cost_and_alignment_share_the_evaluable_cohort(self):
        shorter = [row(i) for i in range(20)] + [row(21, gap=None)]
        longer = [row(i, options=24) for i in range(20)] + [
            row(21, gap=None, options=24)
        ]
        result = cost.information_efficiency(shorter, longer, 0.02)
        self.assertEqual(result["gap_difference"]["groups"], 20)
        self.assertEqual(result["cost_difference"]["ordinary_options"]["groups"], 20)
        self.assertEqual(
            result["full_coverage_cost_diagnostics"]["ordinary_options"]["groups"], 21
        )
        self.assertEqual(result["full_coverage_records"], 21)

    def test_final_comparison_cannot_be_free_when_claiming_cost_reduction(self):
        shorter = [row(i, final=8) for i in range(20)]
        longer = [row(i, options=24) for i in range(20)]
        result = cost.information_efficiency(shorter, longer, 0.02)
        self.assertTrue(result["upper_interval_within_margin"])
        self.assertFalse(result["same_final_candidate_cost"])
        self.assertNotEqual(result["status"], "SUPPORTED_IN_DECLARED_SCOPE")

    def test_unreached_and_unidentifiable_cases_remain_in_threshold_report(self):
        result = cost.threshold_summary([row(1), row(2, 0.9), row(3, None)])
        self.assertEqual(result["records"], 3)
        self.assertEqual(result["unidentifiable_records_retained"], 1)
        self.assertEqual(result["not_reached_labelled_records"], 1)
        self.assertEqual(result["attainment"]["group_macro_mean"], 0.5)
        self.assertEqual(
            result["conditional_cost_among_reached_only"]["labelled_records"], 1
        )

    def test_threshold_does_not_create_new_early_exit(self):
        early = dict(row(1), ordinary_endpoint=False)
        with self.assertRaisesRegex(ValueError, "LEGAL_ENDPOINTS"):
            cost.threshold_summary([early])

    def test_matched_target_alone_does_not_permit_different_inputs_or_scope(self):
        for key, changed in [
            ("visible_sha256", "different_A"),
            ("candidate_vocabulary", []),
        ]:
            with self.assertRaisesRegex(ValueError, "FIXED_COFFEE_TARGET"):
                cost.matching_rows([row(1)], [dict(row(1), **{key: changed})])


if __name__ == "__main__":
    unittest.main()
