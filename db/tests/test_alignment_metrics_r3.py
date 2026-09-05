import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import alignment_metrics_r3 as metric


class R3MetricTests(unittest.TestCase):
    def test_rank_swap_changes_ndcg_but_not_matching(self):
        candidates = [f"sensory.test{i}" for i in range(5)]
        weights = {candidates[0]: 3, candidates[4]: 1}
        a = metric.evaluate(candidates, weights, candidates)
        b = metric.evaluate(candidates[::-1], weights, candidates)
        self.assertEqual(a["M"], b["M"])
        self.assertGreater(a["ndcg"], b["ndcg"])

    def test_one_prediction_cannot_credit_two_targets(self):
        self.assertLessEqual(
            metric.maximum_matching(
                ["sensory.apple"], ["sensory.apple", "sensory.pear"], 5
            ),
            1,
        )

    def test_unknown_relations_and_broad_terms_do_not_match(self):
        self.assertEqual(metric.similarity("sensory.unknown_a", "sensory.unknown_b"), 0)
        self.assertEqual(metric.similarity("attribute.fruity", "sensory.apple"), 0)
        self.assertEqual(metric.similarity("broad.citrus", "sensory.lemon"), 0)

    def test_duplicate_predictions_cannot_improve(self):
        candidates = ["sensory.apple", "sensory.lemon"]
        a = metric.evaluate(candidates, candidates, candidates)
        b = metric.evaluate(
            [candidates[0]] * 8 + candidates[1:], candidates, candidates
        )
        self.assertEqual(a, b)

    def test_empty_and_missing_predictions_are_distinct(self):
        self.assertIsNone(metric.evaluate([], [], ["sensory.apple"])["raw_gap"])
        r = metric.evaluate([], ["sensory.apple"], ["sensory.apple"])
        self.assertEqual((r["raw_gap"], r["ndcg"], r["recall"]), (1, 0, 0))
        self.assertFalse(r["prediction_available"])

    def test_ideal_achieves_exact_upper_bound(self):
        candidates = [f"sensory.test{i}" for i in range(8)]
        r = metric.evaluate(candidates, candidates, candidates)
        self.assertEqual(r["M_star"], 5)
        self.assertEqual(r["opportunity_gap"], 0)
        self.assertEqual(r["raw_gap"], 3 / 8)
        self.assertTrue(r["threshold_0_5_reachable"])

    def test_target_count_alone_does_not_determine_reachability(self):
        candidates = [f"sensory.test{i}" for i in range(12)]
        self.assertTrue(
            metric.evaluate(candidates, candidates[:10], candidates)[
                "threshold_0_5_reachable"
            ]
        )
        self.assertFalse(
            metric.evaluate(candidates, candidates[:11], candidates)[
                "threshold_0_5_reachable"
            ]
        )
        self.assertFalse(
            metric.evaluate(candidates[:1], candidates[:5], candidates[:1])[
                "threshold_0_5_reachable"
            ]
        )

    def test_wrong_pruning_does_not_shrink_denominator(self):
        candidates = ["sensory.apple", "sensory.lemon"]
        a = metric.evaluate(candidates[:1], candidates, candidates)
        b = metric.evaluate(
            candidates[:1], candidates, candidates, soft_candidates=candidates[:1]
        )
        self.assertEqual(a["opportunity_gap"], b["opportunity_gap"])
        self.assertGreater(b["wrong_pruning_extra_floor"], 0)

    def test_out_of_vocabulary_target_retains_raw_failure(self):
        r = metric.evaluate([], ["sensory.unknown"], ["sensory.other"])
        self.assertEqual(r["raw_gap"], 1)
        self.assertIsNone(r["opportunity_gap"])
        self.assertEqual(r["M_star"], 0)

    def test_cardinality_assignment_matches_brute_force(self):
        candidates = [
            "sensory.apple",
            "sensory.pear",
            "sensory.lemon",
            "sensory.caramel",
        ]
        targets = ["sensory.apple", "sensory.orange", "sensory.honey"]
        for k in [1, 2, 3, 5]:
            expected = max(
                sum(metric.similarity(a, b) for a, b in zip(subset, perm, strict=True))
                for n in range(min(k, len(candidates), len(targets)) + 1)
                for subset in itertools.combinations(candidates, n)
                for perm in itertools.permutations(targets, n)
            )
            self.assertAlmostEqual(
                metric.maximum_matching(candidates, targets, k), expected
            )

    def test_explicit_independent_relation_is_separate(self):
        relation = {("sensory.x", "sensory.y"): 0.4}
        self.assertEqual(metric.similarity("sensory.x", "sensory.y"), 0)
        self.assertEqual(
            metric.similarity("sensory.x", "sensory.y", "relation", relation), 0.4
        )

    def test_id_lengths_duplicates_and_alignment(self):
        with self.assertRaises(ValueError):
            metric.align_by_id(["a", "b"], [1], ["a"], [2])
        with self.assertRaises(ValueError):
            metric.align_by_id(["a", "a"], [1, 2], ["a", "b"], [2, 3])
        with self.assertRaises(ValueError):
            metric.align_by_id(["a"], [1], ["b"], [2])
        self.assertEqual(
            metric.align_by_id(["a", "b"], [1, 2], ["b", "a"], [3, 4]),
            [("a", 1, 4), ("b", 2, 3)],
        )


if __name__ == "__main__":
    unittest.main()
