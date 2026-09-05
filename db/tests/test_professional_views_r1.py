"""Algorithm/masking checks use synthetic codes, never asserted sensory truth."""

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import professional_views_m2_r1 as v


def cell(target, value):
    body = target == "mouthfeel.body"
    return {
        "value": value,
        "status": "OBSERVED" if value or body else "TRUE_ZERO",
        "scale": {
            "type": v.SCALE_TYPE,
            "min": 0,
            "max": 9,
            "anchors": ["ZERO", "MAX"],
            "not_quality_score": True,
            "zero_means_absence": not body,
            "body_zero_reference": "filter-coffee viscosity baseline" if body else None,
        },
    }


def fixture(n=30):
    return [
        {
            "record_id": f"unit:{i}",
            "group_id": f"unit-product:{i}",
            "split": "DEVELOPMENT",
            "attribute_measurements": {
                target: cell(target, float((i * (j + 2) + j) % 18) / 2)
                for j, target in enumerate(v.TARGETS)
            },
        }
        for i in range(n)
    ]


class ProfessionalViewTests(unittest.TestCase):
    def test_source_zero_semantics_and_unknown_masks(self):
        self.assertEqual(
            v.observation_value(cell("mouthfeel.body", 0), "mouthfeel.body"), 0
        )
        self.assertEqual(
            v.observation_value(cell("taste.bitterness", 0), "taste.bitterness"), 0
        )
        bad = cell("mouthfeel.body", 0)
        bad["status"] = "TRUE_ZERO"
        with self.assertRaisesRegex(ValueError, "ZERO_STATUS"):
            v.observation_value(bad, "mouthfeel.body")
        bad = cell("taste.bitterness", 0)
        bad["status"] = "NOT_MEASURED"
        self.assertIsNone(v.observation_value(bad, "taste.bitterness"))
        self.assertIsNone(v.observation_value(None, "taste.bitterness"))
        bad = cell("taste.bitterness", 10)
        with self.assertRaisesRegex(ValueError, "OUTSIDE"):
            v.observation_value(bad, "taste.bitterness")

    def test_whole_target_view_and_metadata_cannot_change_prediction(self):
        rows = fixture()
        model = v.fit(rows[:20])
        original = rows[25]["attribute_measurements"]
        before = v.predict(original, model)
        for view, targets in v.VIEWS.items():
            changed = copy.deepcopy(original)
            for target in targets:
                changed[target] = {"status": "NOT_MEASURED", "value": None}
            changed["HEDONIC LEVEL"] = {"value": 1e50}
            after = v.predict(changed, model)
            for target in targets:
                self.assertEqual(before[target], after[target])
                self.assertFalse(
                    set(model["heads"][target]["input_concepts"]) & set(targets)
                )

    def test_training_scaler_prior_and_mask_use_only_observed_train_rows(self):
        rows = fixture()
        target = "taste.bitterness"
        rows[0]["attribute_measurements"][target] = {"status": "NOT_MEASURED"}
        model = v.fit(rows[:20])
        head = model["heads"][target]
        self.assertEqual(len(head["training_groups"]), 19)
        X = np.asarray(
            [
                v.encode_view(r["attribute_measurements"], "basic_taste")
                for r in rows[1:20]
            ]
        )
        np.testing.assert_allclose(head["feature_mean"], X.mean(axis=0))
        expected_y = np.mean(
            [r["attribute_measurements"][target]["value"] for r in rows[1:20]]
        )
        self.assertEqual(head["mean_prior"], expected_y)
        held_changed = copy.deepcopy(rows[20:])
        for row in held_changed:
            row["attribute_measurements"][target] = cell(target, 9)
        self.assertEqual(v.fit(rows[:20]), model)

    def test_group_split_training_confirmation_guard_and_reload_parity(self):
        rows = fixture()
        split = v.fold_assignments(rows)
        self.assertEqual(split, v.fold_assignments(list(reversed(rows))))
        self.assertEqual(len(set(split)), len(rows))
        train = [row for row in rows if split[row["group_id"]] != 0]
        held = [row for row in rows if split[row["group_id"]] == 0]
        model = v.fit(train)
        reloaded = json.loads(json.dumps(model))
        for row in held:
            self.assertEqual(
                v.predict(row["attribute_measurements"], model),
                v.predict(row["attribute_measurements"], reloaded),
            )
        self.assertEqual(len(v.evaluate(held, reloaded, "UNIT")), len(held) * 12)
        with self.assertRaisesRegex(ValueError, "HELD_PRODUCT"):
            v.evaluate(train, model, "UNIT")
        bad = copy.deepcopy(train)
        bad[0]["split"] = "CONFIRMATION"
        with self.assertRaisesRegex(ValueError, "TRAIN_ONLY"):
            v.fit(bad)
        with self.assertRaisesRegex(ValueError, "REPEATED_PRODUCTS"):
            v.fit(train + [train[0]])

    def test_corrupt_held_view_feature_spec_and_missing_input_rejected(self):
        rows = fixture()
        model = v.fit(rows[:20])
        bad = copy.deepcopy(model)
        bad["heads"]["taste.bitterness"]["input_concepts"][0] = "taste.bitterness"
        with self.assertRaisesRegex(ValueError, "HELD_VIEW"):
            v.predict(rows[25]["attribute_measurements"], bad)
        missing = copy.deepcopy(rows[25]["attribute_measurements"])
        missing["mouthfeel.body"] = {"status": "NOT_MEASURED"}
        self.assertIsNone(v.predict(missing, model)["taste.bitterness"])
        self.assertIsNotNone(v.predict(missing, model)["mouthfeel.body"])

    def test_macro_uncertainty_uses_products_not_twelve_attribute_cells(self):
        rows = fixture()
        model = v.fit(rows[:20])
        summary = v.summarize(v.evaluate(rows[20:], model, "UNIT"))
        self.assertEqual(summary["macro_product"]["product_groups"], 10)
        self.assertEqual(summary["macro_product"]["measured_cells"], 120)
        self.assertEqual(summary["by_view"]["aroma"]["measured_cells"], 80)


if __name__ == "__main__":
    unittest.main()
