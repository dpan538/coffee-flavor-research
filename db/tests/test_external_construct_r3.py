import copy
import itertools
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import external_construct_r3 as e


class ExternalConstructTests(unittest.TestCase):
    def test_node_permutations_preserve_complete_matrix(self):
        a = np.array([[0, 1, 2, 4, 8], [1, 0, 3, 5, 9], [2, 3, 0, 6, 10], [4, 5, 6, 0, 7], [8, 9, 10, 7, 0]], float)
        result = e.node_permutation_test(a, a)
        self.assertAlmostEqual(result["rho"], 1)
        self.assertEqual(result["permutation_count"], 120)
        self.assertEqual(len({tuple(r["node_permutation"]) for r in result["permutations"]}), 120)
        self.assertEqual(result["p_two_sided"], result["extreme_or_equal_count"] / 120)
        tri = np.triu_indices(5, 1)
        for p in itertools.permutations(range(5)):
            b = a[np.ix_(p, p)]
            np.testing.assert_array_equal(sorted(a[tri]), sorted(b[tri]))
            self.assertEqual(sorted(a.sum(axis=1)), sorted(b.sum(axis=1)))

    def test_distances_ties_and_constant_are_defined(self):
        p = np.array([[[1, 0], [0, 1]], [[0, 1], [0, 1]]], float)
        d = e.distance_matrix(p, "sqrt_jensen_shannon", 0.5)
        self.assertAlmostEqual(d[0, 1], 0.5 * np.sqrt(np.log(2)))
        self.assertAlmostEqual(e.distance_matrix(p, "cosine", 0.25)[0, 1], 0.25)
        self.assertIsNone(e.matrix_correlation(np.zeros((5, 5)), np.zeros((5, 5))))
        self.assertEqual(e.normalized_token("  Café  CAFÉ "), "café café")

    def test_participant_block_profile_and_mask(self):
        tensor = np.array([[[[1, 0], [0, 1]], [[0, 1], [1, 0]]], [[[0, 1], [1, 0]], [[1, 0], [0, 1]]]], float)
        p = {"tensor": tensor, "mask": np.ones((2, 2, 2), bool), "participants": ["a", "b"]}
        np.testing.assert_array_equal(e.expression_profiles(p, [2, 0]), tensor[0])
        np.testing.assert_array_equal(e.expression_profiles(p, [0, 2]), tensor[1])
        partial = copy.deepcopy(p)
        partial["mask"][0, 0] = False
        self.assertIsNone(e.expression_profiles(partial, [2, 0]))

    def test_contract_requires_exact_nested_value(self):
        self.assertTrue(e.contract_contains({"external": e.protocol()}, e.protocol()))
        changed = e.protocol()
        changed["seed"] += 1
        self.assertFalse(e.contract_contains({"external": changed}, e.protocol()))


if __name__ == "__main__":
    unittest.main()
