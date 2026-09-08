"""A4 — direct unit tests for the seven R9 component modules.

The components have no CLI and write no artefacts, so they are only ever
exercised through a synthesiser. A defect inside one surfaces three layers up as
a wrong number, which is exactly how the operator's own F12 claim went wrong:
the measurement was a proxy, not the code under test.

These tests hit each component directly with small fixtures and assert
properties that are checkable without any frozen state: metric axioms, closure
laws, ordering, and boundary behaviour.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import descriptor_association_analysis_r9 as association  # noqa: E402
import descriptor_feature_extraction_r9 as features  # noqa: E402
import formal_concept_analysis_r9 as fca  # noqa: E402
import tripartite_semantic_structure_r9 as tripartite  # noqa: E402


class JaccardAxioms(unittest.TestCase):
    """jaccard is defined in two components independently. Both must agree."""

    def test_identity_is_one(self):
        for fn in (association.jaccard, features.jaccard):
            with self.subTest(fn=fn.__module__):
                self.assertEqual(fn({"a", "b"}, {"a", "b"}), 1.0)

    def test_disjoint_is_zero(self):
        for fn in (association.jaccard, features.jaccard):
            with self.subTest(fn=fn.__module__):
                self.assertEqual(fn({"a"}, {"b"}), 0.0)

    def test_symmetric(self):
        left, right = {"a", "b", "c"}, {"b", "c", "d"}
        for fn in (association.jaccard, features.jaccard):
            with self.subTest(fn=fn.__module__):
                self.assertEqual(fn(left, right), fn(right, left))

    def test_known_value(self):
        # |intersection| 2, |union| 4
        for fn in (association.jaccard, features.jaccard):
            with self.subTest(fn=fn.__module__):
                self.assertAlmostEqual(fn({"a", "b", "c"}, {"b", "c", "d"}), 0.5)

    def test_two_implementations_agree(self):
        cases = [({"a"}, {"a"}), ({"a"}, {"b"}), ({"a", "b"}, {"b", "c"}), (set(), set())]
        for left, right in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(
                    association.jaccard(left, right), features.jaccard(left, right)
                )


class OptionalJaccardAndCosine(unittest.TestCase):
    def test_optional_jaccard_returns_none_when_undefined(self):
        self.assertIsNone(association.optional_jaccard(set(), set()))

    def test_mapping_cosine_identity(self):
        vector = {"a": 3, "b": 4}
        self.assertAlmostEqual(association.mapping_cosine(vector, vector), 1.0)

    def test_mapping_cosine_orthogonal(self):
        self.assertAlmostEqual(association.mapping_cosine({"a": 1}, {"b": 1}), 0.0)

    def test_mapping_cosine_none_only_when_both_empty(self):
        """Contract read from the source: None only when BOTH norms are zero.
        A one-sided empty vector is 0.0, not undefined."""
        self.assertIsNone(association.mapping_cosine({}, {}))
        self.assertEqual(association.mapping_cosine({}, {"a": 1}), 0.0)

    def test_total_variation_identical_distributions(self):
        self.assertAlmostEqual(
            association.total_variation_similarity([0.5, 0.5], [0.5, 0.5]), 1.0
        )

    def test_total_variation_disjoint_distributions(self):
        self.assertAlmostEqual(
            association.total_variation_similarity([1.0, 0.0], [0.0, 1.0]), 0.0
        )


class FormalConceptClosure(unittest.TestCase):
    """Intent enumeration must be closed under intersection."""

    def _context(self, objects):
        """Mirrors build_formal_context: a context carries both the full
        attribute universe and the per-object intents."""
        attributes = sorted({a for intent in objects for a in intent})
        return {
            "policy_id": "OUT_SEPARATED",
            "attributes": attributes,
            "objects": [
                {"object_id": f"o{i}", "group_id": f"g{i}", "attributes": sorted(a)}
                for i, a in enumerate(objects)
            ],
        }

    def test_closure_contains_pairwise_intersections(self):
        context = self._context([{"x", "y"}, {"y", "z"}, {"x", "z"}])
        # enumerate_formal_intents returns (intents, truncated)
        raw, truncated = fca.enumerate_formal_intents(context)
        self.assertFalse(truncated)
        intents = {frozenset(i) for i in raw}
        for left in list(intents):
            for right in list(intents):
                inter = left & right
                if inter:
                    self.assertIn(inter, intents, f"{sorted(inter)} missing from closure")

    def test_identical_objects_yield_one_intent(self):
        context = self._context([{"x", "y"}, {"x", "y"}, {"x", "y"}])
        raw, _ = fca.enumerate_formal_intents(context)
        self.assertEqual(len({frozenset(i) for i in raw if i}), 1)

    def test_empty_context_is_safe(self):
        """An empty context yields only the empty intent, and does not truncate."""
        raw, truncated = fca.enumerate_formal_intents(self._context([]))
        self.assertFalse(truncated)
        self.assertEqual([i for i in raw if i], [])

    def test_implications_hold_on_every_object(self):
        # y always accompanies x, so x -> y must be produced and must never fail.
        context = self._context([{"x", "y"}, {"x", "y"}, {"y"}])
        rows = fca.exact_singleton_implications(context)
        self.assertTrue(rows, "x always co-occurs with y, so an implication must be found")
        for row in rows:
            premise = row["antecedent_descriptor_id"]
            conclusion = row["consequent_descriptor_id"]
            self.assertEqual(row["exception_record_count"], 0,
                             "an exact implication may not carry exceptions")
            self.assertEqual(row["semantic_status"],
                             "CO_OCCURRENCE_CANDIDATE_ONLY_NOT_RELATION_EDGE",
                             "implications must not be labelled as relation edges")
            for obj in context["objects"]:
                if premise in obj["attributes"]:
                    self.assertIn(conclusion, obj["attributes"],
                                  f"{premise} -> {conclusion} violated by {obj['object_id']}")


class BetweennessCentrality(unittest.TestCase):
    def test_star_centre_has_highest_betweenness(self):
        adjacency = {"c": {"a", "b", "d"}, "a": {"c"}, "b": {"c"}, "d": {"c"}}
        scores = tripartite.betweenness_centrality(adjacency)
        self.assertGreater(scores["c"], scores["a"])
        self.assertEqual(scores["a"], scores["b"])

    def test_leaves_are_zero(self):
        adjacency = {"c": {"a", "b"}, "a": {"c"}, "b": {"c"}}
        scores = tripartite.betweenness_centrality(adjacency)
        self.assertEqual(scores["a"], 0.0)
        self.assertEqual(scores["b"], 0.0)

    def test_disconnected_nodes_are_zero(self):
        adjacency = {"a": set(), "b": set()}
        scores = tripartite.betweenness_centrality(adjacency)
        self.assertEqual(set(scores.values()), {0.0})

    def test_normalised_to_unit_interval(self):
        adjacency = {"c": {"a", "b", "d"}, "a": {"c"}, "b": {"c"}, "d": {"c"}}
        for value in tripartite.betweenness_centrality(adjacency).values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)


if __name__ == "__main__":
    unittest.main()
