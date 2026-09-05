"""Numerical and source-protocol tests; synthetic fixtures are not sensory truth."""

import copy, json, sys, unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sensory_views_m2_r1 as v


def ordinal_cell(value):
    return {
        "value": value,
        "status": "OBSERVED" if value is not None else "NOT_MEASURED",
        "scale": {"type": "ordinal", "zero_means_absence": False},
    }


def binary_cell(value):
    return {
        "value": value,
        "status": "OBSERVED" if value else "TRUE_ZERO",
        "scale": {"type": "binary CATA"},
    }


class SensoryViewTests(unittest.TestCase):
    def test_ordinal_zero_remains_low_observed_not_absence(self):
        self.assertEqual(v.observation_value(ordinal_cell(0), "ordinal"), 0)
        self.assertIsNone(v.observation_value(ordinal_cell(None), "ordinal"))
        bad = ordinal_cell(0)
        bad["status"] = "TRUE_ZERO"
        with self.assertRaises(ValueError):
            v.observation_value(bad, "ordinal")
        self.assertEqual(v.observation_value(binary_cell(0), "binary CATA"), 0)

    def test_ordered_head_thresholds_distributions_and_reload(self):
        x = np.linspace(-2, 2, 100)[:, None]
        y = np.digitize(x[:, 0], [-1.2, -0.4, 0.4, 1.2])
        head = v.fit_ordinal(x, y, np.ones(100))
        self.assertTrue(np.all(np.diff(head["thresholds"]) >= 0))
        p = v.predict_ordinal(x, head)
        self.assertTrue(np.all(p["category_distribution"] >= 0))
        np.testing.assert_allclose(p["category_distribution"].sum(axis=1), 1)
        np.testing.assert_allclose(
            p["category_distribution"],
            v.predict_ordinal(x, json.loads(json.dumps(head)))["category_distribution"],
        )
        self.assertTrue(np.all(np.diff(p["median_category"]) >= 0))

    def test_group_weight_is_not_inflated_by_repeated_panel_rows(self):
        records = [{"group_id": "a"}] * 10 + [{"group_id": "b"}] * 2
        weights = v.group_weights(records)
        self.assertAlmostEqual(weights[:10].sum(), 0.5)
        self.assertAlmostEqual(weights[10:].sum(), 0.5)

    def test_measurement_target_block_cannot_change_exposed_input_features(self):
        from test_flavor_sequential import fixture

        records = fixture()
        bundle = v.training.make_bundle(records, manifest_hash="unit-source-view")
        record = {
            **records[0],
            "evidence_unit_ids": ["unit:source-row"],
            "attribute_measurements": {
                target: ordinal_cell(0) for target in v.ORDINAL_TARGETS
            },
        }
        before, _ = v.prepared_states([record], bundle)
        changed = {
            **record,
            "attribute_measurements": {
                target: ordinal_cell(4) for target in v.ORDINAL_TARGETS
            },
        }
        after, _ = v.prepared_states([changed], bundle)
        for stage in v.STAGES:
            np.testing.assert_array_equal(
                v.encode_evidence(before[stage][0], bundle, v.evidence_spec(bundle)),
                v.encode_evidence(after[stage][0], bundle, v.evidence_spec(bundle)),
            )

    def test_cata_full_view_is_held_from_input_and_missing_never_zero(self):
        columns = [c for cols in v.CATA_VIEWS.values() for c in cols]
        records = []
        for i in range(80):
            values = {
                c: binary_cell(int((i * (j + 3) + j) % 7 < 3))
                for j, c in enumerate(columns)
            }
            records.append(
                {
                    "group_id": "unit-only-one-coffee",
                    "source_family": "cotter_2023",
                    "role": "AUX_COFFEE_WEAK_LABEL",
                    "split": "DEVELOPMENT",
                    "attribute_measurements": values,
                }
            )
        model, metrics = v.train_cata(records)
        self.assertEqual(metrics["cross_coffee_generalization"], "NOT_ESTIMABLE")
        self.assertFalse(metrics["row_random_split_used"])
        for target, head in model["heads"].items():
            self.assertFalse(
                set(head["input_concepts"])
                & set(v.CATA_VIEWS[head["held_attribute_view"]])
            )
        measurements = copy.deepcopy(records[0]["attribute_measurements"])
        self.assertTrue(
            all(p is not None for p in v.predict_cata(measurements, model).values())
        )
        measurements.pop("attribute.fruity")
        self.assertIsNone(v.predict_cata(measurements, model)["taste.sweetness"])
        self.assertNotIn("attribute.sweet", model["heads"])
        self.assertIn("compound.tea_floral", model["heads"])


class FullCATAViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        columns = [c for cols in v.FULL_CATA_VIEWS.values() for c in cols]
        cls.rows = []
        for judge in range(9):
            for condition in range(6):
                i = judge * 6 + condition
                cls.rows.append(
                    {
                        "record_id": "unit:" + str(i),
                        "group_id": "single-unit-coffee",
                        "panelist_id": "judge:" + str(judge),
                        "condition_id": "brew:" + str(condition),
                        "source_family": "cotter_2023",
                        "role": "AUX_COFFEE_WEAK_LABEL",
                        "split": "DEVELOPMENT",
                        "supervision": "COMPLETE_ORIGINAL_CONSUMER_CATA_MATRIX",
                        "attribute_measurements": {
                            c: binary_cell(
                                int((judge * (j + 1) + condition + j) % 5 < 2)
                            )
                            for j, c in enumerate(columns)
                        },
                    }
                )

    def test_complete_matrix_and_real_identity_holdout(self):
        shape = v.validate_full_cata(self.rows, expected_shape=(9, 6))
        self.assertEqual(shape["measured_binary_cells"], 54 * 17)
        self.assertEqual(shape["coffee_groups"], 1)
        for axis, field in v.FULL_CATA_AXES.items():
            assignment = v.full_cata_folds(self.rows, axis)
            self.assertEqual(
                assignment, v.full_cata_folds(list(reversed(self.rows)), axis)
            )
            for fold in range(3):
                train = [r for r in self.rows if assignment[r[field]] != fold]
                held = [r for r in self.rows if assignment[r[field]] == fold]
                self.assertFalse({r[field] for r in train} & {r[field] for r in held})

    def test_held_view_truth_and_lab_context_cannot_change_prediction(self):
        model = v.fit_full_cata(self.rows)
        measurements = copy.deepcopy(self.rows[0]["attribute_measurements"])
        before = v.predict_full_cata(measurements, model)
        for target in v.FULL_CATA_VIEWS["basic_tastes"]:
            measurements[target] = binary_cell(1 - measurements[target]["value"])
        after = v.predict_full_cata(measurements, model)
        for target in v.FULL_CATA_VIEWS["basic_tastes"]:
            self.assertEqual(before[target], after[target])
        self.assertEqual(
            after, v.predict_full_cata(measurements, json.loads(json.dumps(model)))
        )
        for head in model["heads"].values():
            self.assertFalse(
                set(head["input_concepts"])
                & set(v.FULL_CATA_VIEWS[head["held_attribute_view"]])
            )
        bad = copy.deepcopy(model)
        bad["heads"]["taste.sweetness"]["input_concepts"].append("taste.sweetness")
        with self.assertRaises(ValueError):
            v.predict_full_cata(measurements, bad)

    def test_holdout_evaluation_rejects_training_identity_and_keeps_true_zero(self):
        assignment = v.full_cata_folds(self.rows, "judge")
        train = [r for r in self.rows if assignment[r["panelist_id"]] != 0]
        held = [r for r in self.rows if assignment[r["panelist_id"]] == 0]
        model = v.fit_full_cata(train)
        rows = v.evaluate_full_cata(held, model, "judge", 0)
        self.assertEqual(len(rows), len(held) * 17)
        self.assertTrue(any(r["observed_binary_value"] == 0 for r in rows))
        with self.assertRaises(ValueError):
            v.evaluate_full_cata(train, model, "judge", 0)
        bad = copy.deepcopy(self.rows)
        bad[0]["attribute_measurements"]["taste.sweetness"]["status"] = "NOT_MEASURED"
        with self.assertRaises(ValueError):
            v.validate_full_cata(bad)


if __name__ == "__main__":
    unittest.main()
