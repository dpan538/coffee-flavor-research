"""Synthetic native-code and tiny-source data-budget contracts."""

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import castillo_increment_r3 as c
import admit_multiview_sources_r3 as a


def fixture():
    return [{"record_id": f"synthetic:{g}|{condition}", "grader_id": f"synthetic:{g}", "condition_id": condition,
             "source_native_scores": {field: 5 + 0.2 * g + 0.1 * j + 0.15 * (condition == "IW") for j, field in enumerate(a.CASTILLO_FIELDS)},
             "score_masks": dict.fromkeys(a.CASTILLO_FIELDS, True), "score_states": dict.fromkeys(a.CASTILLO_FIELDS, "OBSERVED")}
            for g in range(3) for condition in ("SW", "IW")]


class CastilloTests(unittest.TestCase):
    def test_fixed_feature_order_masks_and_exact_reload(self):
        rows = fixture()
        for budget in (1, 4):
            model = c.fit(rows[:4], budget)
            row = rows[-1]
            before = c.predict(row, model)
            self.assertEqual(before, c.predict(row, json.loads(json.dumps(model))))
            for target in c.TARGETS:
                changed = copy.deepcopy(row)
                changed["score_masks"][target] = False
                changed["source_native_scores"][target] = -1e99
                for excluded in a.CASTILLO_FIELDS[5:]:
                    changed["source_native_scores"][excluded] = 1e99
                changed.update(grader_id="unused", condition_id="unused", chemistry=1e99)
                self.assertEqual(before[target], c.predict(changed, model, target)[target])
                self.assertEqual(len(model["heads"][target]["input_fields"]), budget)
            with self.assertRaisesRegex(ValueError, "HELD_GRADER"):
                c.evaluate(rows[:2], [model])

    def test_true_singleton_data_budget_averages_losses_not_predictions(self):
        rows = fixture()
        models = [c.fit(rows[:2], 1), c.fit(rows[2:4], 1)]
        for model, constant in zip(models, (1, 9)):
            for head in model["heads"].values():
                head["coefficients"] = [0]
                head["target_mean"] = constant
        held = copy.deepcopy(rows[4:])
        for row in held:
            for target in c.TARGETS:
                row["source_native_scores"][target] = 5
        actual = c.evaluate(held, models)
        self.assertEqual(actual[0]["losses"], [4] * 5)
        self.assertEqual(actual[0]["losses_each_model"], [[4] * 5, [4] * 5])

    def test_train_only_means_and_target_exclusion(self):
        rows = fixture()
        model = c.fit(rows[:2], 4)
        for target, head in model["heads"].items():
            self.assertNotIn(target, head["input_fields"])
            X = np.array([[r["source_native_scores"][f] for f in head["input_fields"]] for r in rows[:2]])
            np.testing.assert_array_equal(X.mean(0), head["feature_mean"])
        corrupt = copy.deepcopy(model)
        corrupt["heads"]["aroma"]["input_fields"][0] = "aroma"
        with self.assertRaisesRegex(ValueError, "TARGET_LEAK"):
            c.predict(rows[-1], corrupt)
        missing = copy.deepcopy(rows[:2])
        missing[0]["score_masks"]["body"] = False
        with self.assertRaisesRegex(ValueError, "OBSERVED"):
            c.fit(missing, 4)

    def test_commercial_missing_is_not_zero_and_literal_zero_has_no_absence_claim(self):
        self.assertFalse(a.mean_sd_cell("ND e")["mask"])
        self.assertIsNone(a.mean_sd_cell("-")["mean"])
        self.assertEqual(a.mean_sd_cell("0")["state"], "SOURCE_ROUNDED_ZERO_NO_ABSENCE_CLAIM")
        self.assertEqual(a.mean_sd_cell("1.22 ± 0.06 ab")["mean"], 1.22)
        with self.assertRaisesRegex(ValueError, "UNRECOGNIZED"):
            a.mean_sd_cell("approximately 2")

    def test_tiny_denominator_and_all_held_graders_retained_without_interval(self):
        rows = fixture()
        results = {}
        for name, loss in [("N1V1", 0.4), ("N1V4", 0.3), ("N2V1", 0.2), ("N2V4", 0.1)]:
            results[name] = [{"record_id": r["record_id"], "grader_id": r["grader_id"], "losses": [loss] * 5, "prior_losses": [0.5] * 5} for r in rows]
        summary = c.summarize(results)
        self.assertEqual(summary["target_cells_per_strategy"], 30)
        for result in summary["macro"]["comparisons"].values():
            self.assertIsNone(result["formal_interval"])
            self.assertEqual(len(result["held_fold_deltas"]), 3)
            self.assertEqual(result["status"], "TINY_SOURCE_DESCRIPTIVE_ONLY")
        self.assertAlmostEqual(summary["macro"]["comparisons"]["N2V1_MINUS_N1V1"]["delta"], -0.2)
        results["N1V4"].pop()
        with self.assertRaisesRegex(ValueError, "SAME_SIX"):
            c.summarize(results)


if __name__ == "__main__":
    unittest.main()
