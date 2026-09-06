"""Synthetic-only checks for the R6 fixed-capacity mention head."""

import copy
import json
import unittest

import numpy as np

import train_supervision_r5 as r5
import train_supervision_r6 as h


def example(i=0, target="sensory.apple"):
    return {
        "record_id": str(i),
        "group_id": str(i),
        "initial_selected": ["attribute.fruity"],
        "selected": {"ASK": ["attribute.fruity", target], "SKIP": ["attribute.fruity"]},
        "full_T": {target: 1},
        "hidden_T": {target: 1},
    }


class ObjectiveTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(602)
        self.x = np.column_stack((np.ones(5), rng.normal(size=(5, 3))))
        self.y = rng.uniform(0.1, 1, size=(5, 3))
        self.y /= self.y.sum(axis=1, keepdims=True)
        self.w = np.array([0.125, 0.125, 0.25, 0.25, 0.25])
        self.flat = rng.normal(size=12)

    def objective(self, flat, ridge):
        return h.objective_and_gradient(flat, self.x, self.y, self.w, ridge)

    def test_central_difference_all_three_declared_ridges(self):
        for ridge in h.RIDGES:
            with self.subTest(ridge=ridge):
                _, gradient = self.objective(self.flat, ridge)
                numeric = []
                for j in range(len(self.flat)):
                    step = np.zeros_like(self.flat)
                    step[j] = 1e-5
                    numeric.append(
                        (
                            self.objective(self.flat + step, ridge)[0]
                            - self.objective(self.flat - step, ridge)[0]
                        )
                        / 2e-5
                    )
                self.assertLess(np.max(np.abs(gradient - numeric)), 3e-8)

    def test_ridge_difference_matches_exact_penalty_and_no_intercept(self):
        low_loss, low_grad = self.objective(self.flat, 0.03)
        high_loss, high_grad = self.objective(self.flat, 0.3)
        coef = self.flat.reshape(4, 3)
        self.assertAlmostEqual(high_loss - low_loss, 0.5 * 0.27 * np.sum(coef[1:] ** 2))
        delta = (high_grad - low_grad).reshape(4, 3)
        np.testing.assert_array_equal(delta[0], np.zeros(3))
        np.testing.assert_allclose(delta[1:], 0.27 * coef[1:])

    def test_group_replication_preserves_data_loss_and_gradient(self):
        loss, gradient = self.objective(self.flat, 0.1)
        repeated = h.objective_and_gradient(
            self.flat,
            np.repeat(self.x, 3, axis=0),
            np.repeat(self.y, 3, axis=0),
            np.repeat(self.w / 3, 3),
            0.1,
        )
        self.assertAlmostEqual(loss, repeated[0])
        np.testing.assert_allclose(gradient, repeated[1], atol=1e-15)

    def test_invalid_normalizer_or_gradient_schema_rejected(self):
        cases = [
            (self.x, self.y, self.w * 2),
            (self.x, self.y * 2, self.w),
            (self.x[:, 1:], self.y, self.w),
            (self.x, self.y, np.array([0, 0.25, 0.25, 0.25, 0.25])),
        ]
        for x, y, w in cases:
            with self.subTest(shape=x.shape), self.assertRaises(ValueError):
                h.objective_and_gradient(self.flat, x, y, w, 0.1)


class FeatureSchemaTests(unittest.TestCase):
    def test_exact_r5_capacity_and_features_without_target_or_identity(self):
        row = example()
        np.testing.assert_array_equal(h.features(row), r5.features(row))
        self.assertEqual(h.CANDIDATES, r5.CANDIDATES)
        self.assertEqual(h.INPUTS, r5.INPUTS)
        live = {k: row[k] for k in ("initial_selected", "selected")}
        np.testing.assert_array_equal(h.features(row), h.features(live))
        poison = {
            **live,
            "full_T": object(),
            "hidden_T": object(),
            "group_id": object(),
        }
        np.testing.assert_array_equal(h.features(row), h.features(poison))

    def test_actual_endpoint_is_used_without_I1_assumption(self):
        row = example()
        row["selected"]["I1"] = ["sensory.bitter"]
        original = h.features(row)
        row["selected"]["I1"] = ["sensory.chocolate"]
        np.testing.assert_array_equal(original, h.features(row))
        row["selected"]["ASK"] = ["attribute.fruity", "sensory.bitter"]
        self.assertFalse(np.array_equal(original, h.features(row)))
        row["selected"]["C11"] = row["selected"]["ASK"]
        np.testing.assert_array_equal(h.features(row), h.features(row, branch="C11"))

    def test_duplicate_and_initial_overlap_count_once(self):
        row = example()
        original = h.features(row)
        row["initial_selected"] *= 3
        row["selected"]["ASK"] *= 4
        np.testing.assert_array_equal(original, h.features(row))
        index = 1 + len(h.INPUTS) + h.INPUTS.index("attribute.fruity")
        self.assertEqual(original[index], 0)

    def test_T1_same_capacity_and_zero_later_block(self):
        row = example()
        self.assertEqual(h.features(row, "T1").shape, h.features(row, "T2").shape)
        self.assertTrue(np.all(h.features(row, "T1")[1 + len(h.INPUTS) :] == 0))

    def test_schema_rejects_raw_text_unknown_concepts_and_missing_branch(self):
        for field, value in [
            ("initial_selected", "sensory.apple"),
            ("initial_selected", ["Apple"]),
            ("initial_selected", ["sensory.unknown"]),
            ("selected", {"I1": ["sensory.apple"]}),
            ("selected", {"ASK": None}),
        ]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                h.features({**example(), field: value})
        with self.assertRaises(ValueError):
            h.features(example(), "C11")

    def test_reference_rejects_all_invalid_weights_including_OOV(self):
        for value in (-1, float("nan"), float("inf"), "1", True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                h.targets({"full_T": {"sensory.unregistered": value}})

    def test_fixed_reference_and_unidentifiable_rows_remain_in_evaluation(self):
        row = example()
        row["full_T"] = {"sensory.apple": 1, "sensory.unregistered": 1}
        row["hidden_T"] = dict(row["full_T"])
        self.assertAlmostEqual(h.targets(row).sum(), 1)
        self.assertEqual(h.evaluate(row, ["sensory.apple"])["raw_gap"], 0.5)
        row["full_T"] = {"sensory.unregistered": 1}
        self.assertIsNone(h.targets(row))
        self.assertEqual(h.evaluate(row, h.CANDIDATES)["raw_gap"], 1)
        row.update(full_T={}, hidden_T={})
        result = h.evaluate(row, [])
        self.assertIsNone(result["raw_gap"])
        self.assertEqual(h.aggregate([result])["records"], 1)

    def test_group_weights_unit_mass_and_equal_total_per_coffee(self):
        rows = [example(0), example(0), example(1)]
        np.testing.assert_allclose(h.weights(rows), [0.25, 0.25, 0.5])
        self.assertAlmostEqual(h.weights(rows + [example(2)]).sum(), 1)
        self.assertEqual(len(h.weights([])), 0)
        with self.assertRaises(ValueError):
            h.weights([{"group_id": None}])


class FitReloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [
            example(i, "sensory.apple" if i % 2 else "sensory.bitter") for i in range(8)
        ]
        cls.models = {
            ridge: h.fit(cls.rows, ridge=ridge, lineage={"synthetic_only": True})
            for ridge in h.RIDGES
        }

    def test_three_penalty_fits_same_capacity_and_json_reload_exact(self):
        for ridge, model in self.models.items():
            with self.subTest(ridge=ridge):
                self.assertEqual(np.asarray(model["coefficients"]).shape, h.SHAPE)
                self.assertEqual(model["ridge"], ridge)
                self.assertAlmostEqual(model["training_data_weight_sum"], 1)
                reloaded = json.loads(json.dumps(model))
                h.check_model(reloaded)
                for row in self.rows:
                    left, right = h.predict(row, model), h.predict(row, reloaded)
                    self.assertEqual(left[0], right[0])
                    np.testing.assert_array_equal(left[1], right[1])
                    self.assertEqual(h.evaluate(row, *left), h.evaluate(row, *right))

    def test_same_ridge_reproduces_r5_head_ranking_and_scores(self):
        old = r5.fit(self.rows, "T2", {"synthetic_only": True})
        np.testing.assert_allclose(
            self.models[0.1]["coefficients"], old["coefficients"], atol=1e-10, rtol=0
        )
        for row in self.rows:
            self.assertEqual(
                h.predict(row, self.models[0.1])[0], r5.predict(row, old)[0]
            )

    def test_model_contract_and_nonfinite_weight_rejection(self):
        for key, value in [
            ("ridge", 0.2),
            ("version", "R5"),
            ("variant", "C11"),
            ("candidates", list(reversed(h.CANDIDATES))),
            ("coefficients", [[float("nan")]]),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                h.check_model({**self.models[0.1], key: value})

    def test_no_identifiable_training_reference_rejected_not_zero_fit(self):
        row = example()
        for target in ({}, {"sensory.unregistered": 1}):
            with self.subTest(target=target), self.assertRaisesRegex(
                ValueError, "NO_IDENTIFIABLE"
            ):
                h.fit([{**row, "full_T": target}])

    def test_unusable_training_rows_are_counted_without_target_truncation(self):
        unseen = example(999)
        unseen["full_T"] = {"sensory.unregistered": 1}
        fitted = h.fit(self.rows + [unseen], ridge=0.1)
        self.assertEqual(fitted["unidentifiable_training_records"], 1)
        self.assertIn("999", fitted["training_groups"])
        self.assertNotIn("999", fitted["usable_training_groups"])
        np.testing.assert_array_equal(
            fitted["coefficients"], self.models[0.1]["coefficients"]
        )


if __name__ == "__main__":
    unittest.main()
