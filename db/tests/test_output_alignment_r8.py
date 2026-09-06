"""R8 integration invariants; all fixtures synthetic, never sensory evidence."""

import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import output_alignment_r8 as r8
from r8_output_alignment_helper import returned_views


class OutputAlignmentTests(unittest.TestCase):
    def final(self, main=(), secondary=(), pool=None):
        return {
            "stage": "PRELIMINARY_RESULT",
            "main": [{"candidate_id": c} for c in main],
            "secondary": [{"candidate_id": c} for c in secondary],
            "exposure": (
                None
                if pool is None
                else {
                    "candidate_ids": list(pool),
                    "generation_version": "test-model",
                    "eligible_for_final_comparison": 3 <= len(pool) <= 8,
                }
            ),
        }

    def bundle(self):
        return {
            "bundle_id": "test-model",
            "r1_expert": {
                "candidate_vocabulary": [
                    "sensory.lemon",
                    "sensory.lime",
                    "sensory.cocoa",
                    "attribute.fruity",
                ]
            },
        }

    def test_real_parent_matching_is_one_to_one(self):
        x = r8.measure(
            ["sensory.lime"], {"sensory.lemon": 1, "sensory.grapefruit": 1}, 5
        )
        self.assertEqual(x["match_sum"], 0.25)
        self.assertEqual(x["raw_gap"], 0.875)
        self.assertEqual(x["ndcg_actual_positions"], 0)

    def test_broad_never_gets_fine_partial_credit(self):
        self.assertEqual(
            r8.measure(["attribute.fruity"], {"sensory.lemon": 1}, 5)["raw_gap"], 1
        )

    def test_actual_rank_four_stays_four(self):
        x = r8.measure(
            [
                "attribute.fruity",
                "attribute.sweet",
                "attribute.roasted",
                "sensory.lemon",
            ],
            {"sensory.lemon": 1},
            5,
        )
        self.assertAlmostEqual(x["ndcg_actual_positions"], 1 / math.log2(5))

    def test_short_panel_keeps_fixed_ideal_and_oov(self):
        x = r8.measure(
            ["sensory.lemon"], {"sensory.lemon": 2, "sensory.unregistered": 1}, 8
        )
        self.assertEqual(x["raw_gap"], 0.5)
        self.assertAlmostEqual(x["ndcg_actual_positions"], 2 / (2 + 1 / math.log2(3)))

    def test_unregistered_parent_does_not_match(self):
        self.assertEqual(r8.matching(["sensory.not_a"], ["sensory.not_b"], 5), 0)

    def test_missing_pool_not_synthesized(self):
        views, valid = r8.return_audit(self.final(["sensory.lemon"]), self.bundle())
        self.assertIsNone(views["proposed_pool"])
        self.assertIsNone(valid)

    def test_pool_two_recorded_invalid_not_padded(self):
        views, valid = r8.return_audit(
            self.final(["sensory.lemon"], pool=["sensory.lemon", "sensory.lime"]),
            self.bundle(),
        )
        self.assertFalse(valid)
        self.assertEqual(len(views["proposed_pool"]), 2)

    def test_pool_different_order_preserved(self):
        f = self.final(
            ["sensory.lemon", "sensory.lime"],
            ["sensory.cocoa"],
            ["sensory.cocoa", "sensory.lime", "sensory.lemon"],
        )
        old = copy.deepcopy(f)
        views, valid = r8.return_audit(f, self.bundle())
        self.assertTrue(valid)
        self.assertFalse(views["pool_matches_combined"])
        self.assertEqual(f, old)

    def test_duplicate_cross_interface_keeps_slot(self):
        f = self.final(["sensory.lemon"], ["sensory.lemon", "sensory.cocoa"])
        v = returned_views(f)
        score = r8.measure(
            v["main_plus_secondary"], {"sensory.lemon": 1, "sensory.cocoa": 1}, 8
        )
        self.assertEqual(score["duplicate_output_ids"], ["sensory.lemon"])
        self.assertAlmostEqual(
            score["ndcg_actual_positions"], 1.5 / (1 + 1 / math.log2(3))
        )

    def test_bad_version_and_stage_block(self):
        f = self.final(
            ["sensory.lemon"], pool=["sensory.lemon", "sensory.lime", "sensory.cocoa"]
        )
        f["exposure"]["generation_version"] = "wrong"
        with self.assertRaisesRegex(ValueError, "VERSION"):
            r8.return_audit(f, self.bundle())
        f = self.final()
        f["stage"] = "FINAL_RESULT"
        with self.assertRaisesRegex(ValueError, "PRE_FEEDBACK"):
            r8.return_audit(f, self.bundle())

    def test_oversized_and_unregistered_outputs_block(self):
        with self.assertRaisesRegex(ValueError, "BUDGET"):
            r8.return_audit(self.final(["sensory.lemon"] * 6), self.bundle())
        with self.assertRaisesRegex(ValueError, "UNREGISTERED"):
            r8.return_audit(self.final(["sensory.unknown"]), self.bundle())

    def test_pairing_does_not_depend_on_row_order(self):
        a = {
            "record_id": "a",
            "group_id": "g",
            "fold": 0,
            "full_T": {"sensory.lemon": 1},
            "hidden_T": {},
            "evaluation_universe": r8.CANDIDATES,
        }
        b = {**a, "record_id": "b"}
        self.assertEqual(
            set(r8.pair_index({"C00": [a, b], "C01": [b, a]})["C00"]), {"a", "b"}
        )
        for key, value in [("group_id", "wrong"), ("full_T", {}), ("fold", 1)]:
            with self.assertRaisesRegex(ValueError, "PAIRED_FIXED"):
                r8.pair_index({"C00": [a], "C01": [{**a, key: value}]})
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            r8.pair_index({"C00": [a, a], "C01": [a]})

    def test_outside_candidate_is_not_outside_hit(self):
        x = r8.outside_diagnostic(
            ["sensory.lemon", "sensory.cocoa"], ["sensory.lemon"], {"sensory.lemon": 1}
        )
        self.assertEqual(x["outside_ids"], ["sensory.cocoa"])
        self.assertEqual(x["outside_exact_target_hits"], [])
        self.assertEqual(x["necessary_matching_loss_without_replacement"], 0)

    def test_outside_partial_credit_is_not_added_twice(self):
        x = r8.outside_diagnostic(
            ["sensory.lime", "sensory.lemon"],
            ["sensory.lemon"],
            {"sensory.grapefruit": 1},
        )
        self.assertEqual(x["necessary_matching_loss_without_replacement"], 0)
        self.assertEqual(
            sum(
                e["weight"]
                for e in r8.witness(
                    ["sensory.lime", "sensory.lemon"], {"sensory.grapefruit": 1}
                )
            ),
            0.25,
        )

    def test_empty_T_and_true_empty_output_distinct(self):
        self.assertIsNone(r8.measure([], {}, 5)["raw_gap"])
        x = r8.measure([], {"sensory.lemon": 1}, 5)
        self.assertEqual(
            (x["raw_gap"], x["recall"], x["ndcg_actual_positions"]), (1, 0, 0)
        )

    def test_zero_weight_target_not_pool_outside_credit(self):
        x = r8.outside_diagnostic(["sensory.lemon"], [], {"sensory.lemon": 0})
        self.assertEqual(x["outside_exact_target_hits"], [])
        self.assertEqual(x["necessary_matching_loss_without_replacement"], 0)

    def test_missing_P_preserves_paired_denominator(self):
        panel = r8.measure(["sensory.lemon"], {"sensory.lemon": 1}, 8)
        rows = [
            {
                "record_id": "a",
                "group_id": "g",
                "policy": "C00",
                "panels": {"P": panel},
            },
            {"record_id": "a", "group_id": "g", "policy": "C01", "panels": {"P": None}},
        ]
        report, groups = r8.comparisons(rows, "P")
        self.assertEqual(report["metrics"]["raw_gap"]["groups"], 0)
        self.assertEqual(report["metrics"]["raw_gap"]["paired_records"], 0)
        self.assertIsNone(report["metrics"]["raw_gap"]["paired_C00_mean"])
        self.assertEqual(report["not_evaluable_groups"], 1)


if __name__ == "__main__":
    unittest.main()
