"""R8 adapter: evaluate returned IDs without promoting hidden fine candidates.

This is a small integration example, not a replacement for the repository's
frozen matching definition. Supply its maximum_matching function via a callback.
Only synthetic tests run with --self-test; no private coffee data are included.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from typing import Any

Matcher = Callable[[Sequence[str], Sequence[str], int], float]


def _ids(items: Sequence[Any]) -> tuple[str, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("EXPECTED_ORDERED_ID_SEQUENCE")
    result: list[str] = []
    for item in items:
        value = item.get("candidate_id") if isinstance(item, Mapping) else item
        if not isinstance(value, str) or not value:
            raise ValueError("NONEMPTY_CANDIDATE_ID_REQUIRED")
        result.append(value)
    return tuple(result)


def returned_views(final_result: Mapping[str, Any]) -> dict[str, Any]:
    """Read actual output fields; never reconstruct exposure from a full rank."""
    if "main" not in final_result or "secondary" not in final_result:
        raise ValueError("ACTUAL_OUTPUT_FIELDS_REQUIRED")
    main = _ids(final_result["main"])
    secondary = _ids(final_result["secondary"])
    if len(main) > 5 or len(secondary) > 3:
        raise ValueError("OUTPUT_BUDGET_VIOLATION")
    exposure = final_result.get("exposure")
    pool = None
    if exposure is not None:
        if not isinstance(exposure, Mapping) or "candidate_ids" not in exposure:
            raise ValueError("EXPOSURE_IDS_REQUIRED")
        pool = _ids(exposure["candidate_ids"])
        if len(pool) > 8:
            raise ValueError("EXPOSURE_BUDGET_VIOLATION")
    return {
        "stage": final_result.get("stage"),
        "main": main,
        "secondary": secondary,
        "main_plus_secondary": main + secondary,
        "proposed_pool": pool,
        "pool_matches_combined": None if pool is None else pool == main + secondary,
    }


def score_returned_panel(
    ordered_ids: Sequence[str],
    target_weights: Mapping[str, float],
    *,
    k: int,
    fine_universe: Sequence[str] | frozenset[str],
    maximum_matching: Matcher,
) -> dict[str, Any]:
    """Evaluate fine-reference coverage AT actual positions of a mixed panel.

    Broad/non-fine entries get no fine-target credit, but keep their slots.
    That is a limitation of this fine-reference task, not evidence of their
    sensory irrelevance. All positive target weights, including OOV targets,
    stay in the reference and ideal-ranking denominator.

    Duplicate output IDs are flagged. Their later occurrences retain positions
    but get no repeated credit. No lower-ranked item is moved into the panel.
    """
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError("POSITIVE_INTEGER_K_REQUIRED")
    original = _ids(ordered_ids)
    panel = original[:k]  # IMPORTANT: cut the actual budget BEFORE fine filtering.
    if isinstance(fine_universe, (str, bytes)):
        raise ValueError("FINE_UNIVERSE_MUST_BE_COLLECTION")
    universe_ids = _ids(tuple(fine_universe))
    if len(set(universe_ids)) != len(universe_ids):
        raise ValueError("DUPLICATE_FINE_UNIVERSE_ID")
    allowed = frozenset(universe_ids)
    if not isinstance(target_weights, Mapping):
        raise ValueError("FROZEN_TARGET_WEIGHT_MAPPING_REQUIRED")
    weights: dict[str, float] = {}
    for identity, weight in target_weights.items():
        if not isinstance(identity, str) or not identity:
            raise ValueError("NONEMPTY_TARGET_ID_REQUIRED")
        if isinstance(weight, bool) or not isinstance(weight, (float, int)):
            raise ValueError("NUMERIC_TARGET_WEIGHT_REQUIRED")
        if not math.isfinite(weight) or weight < 0:
            raise ValueError("FINITE_NONNEGATIVE_TARGET_WEIGHT_REQUIRED")
        if weight > 0:
            weights[identity] = float(weight)

    seen: set[str] = set()
    duplicates: list[str] = []
    eligible: list[str] = []
    dcg = 0.0
    for position, identity in enumerate(panel):
        if identity in seen:
            duplicates.append(identity)
            continue  # Keep its rank position; do not backfill.
        seen.add(identity)
        if identity in allowed:
            eligible.append(identity)
            dcg += weights.get(identity, 0.0) / math.log2(position + 2)

    n = len(weights)
    match = float(maximum_matching(eligible, tuple(weights), k)) if n else 0.0
    if (
        not math.isfinite(match)
        or not -1e-10 <= match <= min(len(eligible), n, k) + 1e-10
    ):
        raise ValueError("MATCHER_RESULT_OUTSIDE_BOUNDED_ONE_TO_ONE_RANGE")
    match = min(max(match, 0.0), float(min(len(eligible), n, k)))
    ideal = sum(
        value / math.log2(position + 2)
        for position, value in enumerate(sorted(weights.values(), reverse=True)[:k])
    )
    hits = sorted(set(eligible) & weights.keys())
    return {
        "metric_scope": "FINE_REFERENCE_ON_ACTUAL_RETURNED_POSITIONS",
        "scored_ids": list(panel),
        "declared_budget": k,
        "returned_slots_scored": len(panel),
        "fine_unique_count": len(eligible),
        "non_fine_or_outside_universe_slots": sum(c not in allowed for c in panel),
        "duplicate_output_ids": duplicates,
        "target_count": n,
        "positive_targets_outside_fine_universe": sorted(weights.keys() - allowed),
        "exact_target_hits": hits,
        "match_sum": match if n else None,
        "raw_gap": 1 - match / n if n else None,
        "recall": len(hits) / n if n else None,
        "ndcg_actual_positions": dcg / ideal if ideal > 0 else None,
        "evaluable": bool(n),
    }


def _self_test() -> None:
    import copy
    import unittest

    class Tests(unittest.TestCase):
        universe = ("sensory.lemon", "sensory.cocoa", "sensory.lime")

        @staticmethod
        def exact_match(preds: Sequence[str], targets: Sequence[str], k: int) -> float:
            return float(min(k, len(set(preds) & set(targets))))

        def score(self, ids, target=None, k=5, matcher=None):
            return score_returned_panel(
                ids,
                {"sensory.lemon": 1.0} if target is None else target,
                k=k,
                fine_universe=self.universe,
                maximum_matching=matcher or self.exact_match,
            )

        def test_actual_positions_are_preserved(self):
            value = self.score(["attribute.fruit", "attribute.sweet", "sensory.lemon"])
            self.assertAlmostEqual(value["ndcg_actual_positions"], 0.5)
            self.assertEqual(value["raw_gap"], 0.0)

        def test_no_hidden_candidate_backfill(self):
            ids = [f"attribute.a{i}" for i in range(5)] + ["sensory.lemon"]
            value = self.score(ids)
            self.assertEqual(value["raw_gap"], 1.0)
            self.assertNotIn("sensory.lemon", value["scored_ids"])

        def test_order_changes_rank_not_set(self):
            a = self.score(["sensory.lemon", "attribute.fruit"])
            b = self.score(["attribute.fruit", "sensory.lemon"])
            self.assertEqual(a["raw_gap"], b["raw_gap"])
            self.assertGreater(a["ndcg_actual_positions"], b["ndcg_actual_positions"])

        def test_duplicate_gets_no_extra_credit_or_rank_compression(self):
            value = self.score(
                ["sensory.lemon", "sensory.lemon", "sensory.cocoa"],
                {"sensory.lemon": 1, "sensory.cocoa": 1},
            )
            self.assertEqual(value["duplicate_output_ids"], ["sensory.lemon"])
            self.assertEqual(value["recall"], 1.0)
            self.assertAlmostEqual(
                value["ndcg_actual_positions"], 1.5 / (1 + 1 / math.log2(3))
            )

        def test_oov_target_stays_in_denominator(self):
            value = self.score(
                ["sensory.lemon", "sensory.unknown"],
                {"sensory.lemon": 1, "sensory.unknown": 1},
            )
            self.assertEqual(value["raw_gap"], 0.5)
            self.assertEqual(
                value["positive_targets_outside_fine_universe"], ["sensory.unknown"]
            )

        def test_matcher_sees_only_already_returned_fine_ids(self):
            def checked(preds, targets, k):
                self.assertEqual(list(preds), ["sensory.lemon"])
                return 1.0

            self.score(["attribute.fruit", "sensory.lemon"], matcher=checked)

        def test_empty_target_is_not_evaluable(self):
            value = self.score(["sensory.lemon"], {})
            self.assertFalse(value["evaluable"])
            self.assertIsNone(value["raw_gap"])
            self.assertIsNone(value["ndcg_actual_positions"])

        def test_empty_output_with_target_is_failure(self):
            value = self.score([])
            self.assertEqual(value["raw_gap"], 1.0)
            self.assertEqual(value["recall"], 0.0)
            self.assertEqual(value["ndcg_actual_positions"], 0.0)

        def test_short_output_does_not_shrink_ideal(self):
            value = self.score(
                ["sensory.lemon"], {"sensory.lemon": 1, "sensory.cocoa": 1}
            )
            self.assertAlmostEqual(
                value["ndcg_actual_positions"], 1 / (1 + 1 / math.log2(3))
            )

        def test_reference_is_not_mutated(self):
            target = {"sensory.lemon": 2, "sensory.cocoa": 0}
            old = copy.deepcopy(target)
            self.score(["sensory.lemon"], target)
            self.assertEqual(target, old)

        def test_partial_matching_can_be_injected(self):
            value = self.score(["sensory.lime"], matcher=lambda p, t, k: 0.25)
            self.assertEqual(value["raw_gap"], 0.75)
            self.assertEqual(value["recall"], 0.0)

        def test_invalid_k_rejected(self):
            for bad in (True, 0, -1, 1.5):
                with self.assertRaises(ValueError):
                    self.score([], k=bad)

        def test_invalid_weights_rejected(self):
            for bad in (float("nan"), float("inf"), -1, True):
                with self.assertRaises(ValueError):
                    self.score([], {"sensory.lemon": bad})

        def test_invalid_matcher_output_rejected(self):
            with self.assertRaises(ValueError):
                self.score(["sensory.lemon"], matcher=lambda p, t, k: 2.0)

        def test_explicit_pool_is_not_rebuilt(self):
            final = {
                "stage": "PRELIMINARY_RESULT",
                "main": [{"candidate_id": "sensory.lemon"}],
                "secondary": [],
                "exposure": {"candidate_ids": ["sensory.cocoa"]},
            }
            old = copy.deepcopy(final)
            views = returned_views(final)
            self.assertEqual(views["proposed_pool"], ("sensory.cocoa",))
            self.assertFalse(views["pool_matches_combined"])
            self.assertEqual(final, old)

        def test_missing_exposure_stays_none(self):
            views = returned_views(
                {"main": ["sensory.lemon"], "secondary": [], "exposure": None}
            )
            self.assertIsNone(views["proposed_pool"])

        def test_illegal_size_not_silently_truncated(self):
            with self.assertRaises(ValueError):
                returned_views({"main": ["x"] * 6, "secondary": []})

        def test_five_and_eight_are_separate_budgets(self):
            ids = [f"attribute.a{i}" for i in range(5)] + ["sensory.lemon"]
            self.assertEqual(self.score(ids, k=5)["recall"], 0)
            self.assertEqual(self.score(ids, k=8)["recall"], 1)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
    else:
        parser.print_help()
