"""Synthetic nominal-category contracts; no inferred sensory participants."""

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import profile_increment_r2 as p


def fixture(participants=6, conditions=3):
    return [
        {
            "record_id": f"unit:{i}:{j}",
            "participant_id": f"participant:{i}",
            "condition_id": f"condition:{j}",
            "participant_split": "DEVELOPMENT",
            "condition_split": "DEVELOPMENT",
            "responses": {c: (i + j + k) % 6 for k, c in enumerate(p.TARGETS)},
            "response_masks": dict.fromkeys(p.TARGETS, True),
            "response_states": dict.fromkeys(p.TARGETS, "OBSERVED"),
        }
        for i in range(participants)
        for j in range(conditions)
    ]


class ProfileIncrementTests(unittest.TestCase):
    def barahona_fixture(self):
        return [
            {
                "record_id": f"product:{i}",
                "group_id": f"product:{i}",
                "split": "DEVELOPMENT",
                "attribute_measurements": {
                    c: 1.0 + (i * (j + 1) % 80) / 10
                    for j, c in enumerate(p.BARAHONA_TARGETS)
                },
                "attribute_masks": dict.fromkeys(p.BARAHONA_TARGETS, True),
                "attribute_states": dict.fromkeys(p.BARAHONA_TARGETS, "OBSERVED"),
            }
            for i in range(18)
        ]

    def test_barahona_native_masks_scaler_and_no_liking_or_held_view(self):
        rows = self.barahona_fixture()
        model = p.fit_barahona(rows[:12])
        row = rows[-1]
        before = p.predict_barahona(row, model)
        self.assertEqual(before, p.predict_barahona(row, json.loads(json.dumps(model))))
        for view, block in p.BARAHONA_VIEWS.items():
            changed = copy.deepcopy(row)
            for target in block:
                changed["attribute_masks"][target] = False
                changed["attribute_measurements"][target] = -1e99
            changed["price"] = 1e99
            changed["liking"] = -1e99
            after = p.predict_barahona(changed, model)
            for target in block:
                self.assertEqual(before[target], after[target])
                h = model["heads"][target]
                X = np.asarray([p.encode_barahona(r, view) for r in rows[:12]])
                np.testing.assert_array_equal(h["feature_mean"], X.mean(0))
        with self.assertRaisesRegex(ValueError, "HELD_PRODUCT"):
            p.evaluate_barahona(rows[:1], model, "UNIT")
        bad = copy.deepcopy(rows[:12])
        bad[0]["split"] = "CONFIRMATION"
        with self.assertRaisesRegex(ValueError, "DEVELOPMENT"):
            p.fit_barahona(bad)

    def test_barahona_four_product_confirmation_never_claims_robust_gain(self):
        rows = [
            {"unit": f"product:{i}", "model_mae": [0.1] * 7, "prior_mae": [0.8] * 7}
            for i in range(4)
        ]
        result = p.summarize_barahona(rows, confirmation=True)
        self.assertIsNone(result["macro"]["paired_product_95_interval"])
        self.assertEqual(result["macro"]["status"], "INCONCLUSIVE")
        self.assertEqual(result["macro"]["evaluated_cells"], 28)

    def test_increment_protocol_has_separate_scales_and_fixed_parameters(self):
        protocol = p.increment_protocol()
        self.assertEqual(protocol["liberica"]["recorded_categories"], list(range(6)))
        self.assertEqual(protocol["liberica"]["fixed_ridge"], 0.05)
        self.assertEqual(protocol["barahona"]["fixed_ridge"], 0.5)
        self.assertEqual(protocol["barahona"]["confirmation_products"], 4)
        self.assertFalse(protocol["main_M2_scoring_changed"])

    def test_half_products_are_fixed_hash_subset_with_ceil_count(self):
        rows = self.barahona_fixture()
        for count in [9, 10, 14]:
            selected = p.half_products(rows[:count])
            self.assertEqual(len(selected), (count + 1) // 2)
            self.assertEqual(selected, p.half_products(list(reversed(rows[:count]))))
            self.assertTrue(
                {r["group_id"] for r in selected}
                <= {r["group_id"] for r in rows[:count]}
            )
        bad = copy.deepcopy(rows[:9])
        bad[-1]["split"] = "CONFIRMATION"
        with self.assertRaisesRegex(ValueError, "DEVELOPMENT"):
            p.half_products(bad)

    def test_learning_curve_compares_same_targets_and_full_minus_half(self):
        full = [
            {
                "record_id": f"product:{i}",
                "unit": f"product:{i}",
                "truth": [5.0] * 7,
                "model_mae": [0.2] * 7,
            }
            for i in range(4)
        ]
        half = copy.deepcopy(full)
        for row in half:
            row["model_mae"] = [0.5] * 7
        result = p.summarize_learning_curve(full, half, True)
        self.assertAlmostEqual(result["macro"]["delta_full_minus_half"], -0.3)
        self.assertEqual(result["macro"]["status"], "INCONCLUSIVE")
        half[0]["truth"][0] = 6.0
        with self.assertRaisesRegex(ValueError, "IDENTICAL"):
            p.summarize_learning_curve(full, half)

    def test_zero_is_nominal_observed_and_masks_cannot_impute(self):
        row = fixture()[0]
        target = p.TARGETS[0]
        self.assertEqual(p.observed(row, target), 0)
        row["response_masks"][target] = False
        self.assertIsNone(p.observed(row, target))
        row["response_masks"][target] = True
        row["response_states"][target] = "TRUE_ZERO"
        self.assertIsNone(p.observed(row, target))
        row["response_states"][target] = "OBSERVED"
        row["responses"][target] = True
        with self.assertRaisesRegex(ValueError, "NOMINAL"):
            p.observed(row, target)

    def test_same_encoder_whole_block_mask_and_reload(self):
        rows = fixture()
        model = p.fit(rows[:12])
        row = rows[-1]
        original = p.predict(row, model)
        self.assertEqual(original, p.predict(row, json.loads(json.dumps(model))))
        for view, block in p.VIEWS.items():
            changed = copy.deepcopy(row)
            for target in block:
                changed["response_masks"][target] = False
                changed["responses"][target] = -1
            changed["hedonic"] = 1e99
            changed["participant_id"] = "forbidden-identity"
            after = p.predict(changed, model)
            for target in block:
                self.assertEqual(original[target], after[target])
        for values in original.values():
            self.assertAlmostEqual(sum(values), 1)
            self.assertTrue(all(0 <= value <= 1 for value in values))
        corrupt = copy.deepcopy(model)
        head = next(iter(corrupt["heads"].values()))
        head["input_fields"][0] = p.VIEWS[head["target_view"]][0]
        with self.assertRaisesRegex(ValueError, "HELD_VIEW"):
            p.predict(row, corrupt)

    def test_codes_are_one_hot_not_ordinal_magnitudes(self):
        row = fixture()[0]
        vector = p.encode(row, next(iter(p.VIEWS)))
        self.assertEqual(len(vector), 6 * len(p.inputs(next(iter(p.VIEWS)))))
        np.testing.assert_array_equal(vector.reshape(-1, 6).sum(1), 1)
        self.assertTrue(set(vector) <= {0, 1})

    def test_both_confirmation_axes_quarantined(self):
        rows = fixture(25, 9)
        for row in rows:
            if row["participant_id"] in {"participant:20", "participant:24"}:
                row["participant_split"] = "CONFIRMATION"
            if row["condition_id"] == "condition:8":
                row["condition_split"] = "CONFIRMATION"
        parts = p.partition(rows)
        self.assertEqual(
            {k: len(v) for k, v in parts.items()},
            {
                "development": 184,
                "held_participant": 16,
                "held_condition": 23,
                "both_axes_held": 2,
            },
        )
        dev_ids = {r["record_id"] for r in parts["development"]}
        for name in ["held_participant", "held_condition", "both_axes_held"]:
            self.assertFalse(dev_ids & {r["record_id"] for r in parts[name]})
            with self.assertRaisesRegex(ValueError, "BOTH_IDENTITY"):
                p.fit(parts["development"][:10] + parts[name][:1])

    def test_axis_guard_and_exact_brier_denominator(self):
        rows = fixture()
        model = p.fit(rows[:12])
        results = p.evaluate(rows[12:], model, "participant_id", "UNIT")
        self.assertEqual(len(results), 6)
        row = results[0]
        expected = (
            (np.asarray(row["probabilities"])[0] - np.eye(6)[row["codes"][0]]) ** 2
        ).sum() / 6
        self.assertEqual(row["model_brier"][0], expected)
        with self.assertRaisesRegex(ValueError, "HELD_IDENTITY"):
            p.evaluate(rows[:1], model, "participant_id", "UNIT")

    def test_tiny_confirmation_is_descriptive_and_public_strips_ids(self):
        for count in [1, 2, 3]:
            rows = [
                {
                    "unit": f"private:{i}",
                    "model_brier": [0.1] * 10,
                    "prior_brier": [0.2] * 10,
                }
                for i in range(count)
            ]
            result = p.summary(rows)
            if count < 3:
                self.assertIsNone(result["macro"]["paired_unit_95_interval"])
                self.assertEqual(
                    result["macro"]["status"],
                    "NOT_ESTIMABLE" if count == 1 else "INCONCLUSIVE",
                )
            else:
                self.assertEqual(
                    result["macro"]["status"], "SUPPORTED_IN_DECLARED_SCOPE"
                )
            self.assertNotIn("private:", json.dumps(p.public_summary(result)))

    def test_constant_or_absent_categories_fit_without_fabricated_examples(self):
        X = np.tile(np.eye(6), (2, 1))
        y = np.zeros(len(X), dtype=int)
        fitted = p.fit_multinomial(X, y)
        self.assertEqual(fitted["prior"], [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.assertTrue(np.isfinite(fitted["coefficients"]).all())


if __name__ == "__main__":
    unittest.main()
