"""Synthetic masking and nested-selection contracts, not human observations."""

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import profile_alignment_r2 as p


def fixture(kind, n=18):
    records = []
    for i in range(n):
        cells = {}
        for j, target in enumerate(p.targets(kind)):
            if kind == "rocchetti":
                value = ((i * (j + 2) + j) % 18) / 2
                body = target == "mouthfeel.body"
                scale = {
                    "type": p.professional.SCALE_TYPE,
                    "min": 0,
                    "max": 9,
                    "anchors": ["ZERO", "MAX"],
                    "not_quality_score": True,
                    "zero_means_absence": not body,
                    "body_zero_reference": "source filter baseline" if body else None,
                }
                status = "OBSERVED" if value or body else "TRUE_ZERO"
            else:
                value = (i + i // 3 + j) % 2
                scale = {"type": "binary CATA"}
                status = "OBSERVED" if value else "TRUE_ZERO"
            cells[target] = {"value": value, "status": status, "scale": scale}
        records.append(
            {
                "record_id": f"unit:{i}",
                "group_id": f"coffee:{i}" if kind == "rocchetti" else "coffee:one",
                "panelist_id": f"judge:{i}",
                "condition_id": f"condition:{i % 3}",
                "split": "DEVELOPMENT",
                "attribute_measurements": cells,
                "attribute_masks": dict.fromkeys(cells, True),
            }
        )
    return records


class ProfileAlignmentTests(unittest.TestCase):
    def test_fixed_r1_native_fit_and_reload_parity(self):
        records = fixture("rocchetti")
        model = p.fit(records[:12], "rocchetti", 0.05)
        old = p.professional.fit(records[:12])
        for record in records[12:]:
            expected = p.professional.predict(record["attribute_measurements"], old)
            self.assertEqual(
                expected, p.predict(record["attribute_measurements"], model)
            )
            self.assertEqual(
                expected,
                p.predict(
                    record["attribute_measurements"], json.loads(json.dumps(model))
                ),
            )

    def test_fixed_r1_cata_fit_parity(self):
        records = fixture("cotter")
        model = p.fit(records[:12], "cotter", 0.05)
        old = p.response.fit_full_cata(records[:12])
        for record in records[12:]:
            self.assertEqual(
                p.response.predict_full_cata(record["attribute_measurements"], old),
                p.predict(record["attribute_measurements"], model),
            )

    def test_entire_held_view_and_metadata_never_inputs(self):
        for kind in ["rocchetti", "cotter"]:
            records = fixture(kind)
            model = p.fit(records[:12], kind, 0.05)
            cells = records[-1]["attribute_measurements"]
            original = p.predict(cells, model)
            for view, targets in p.views(kind).items():
                changed = copy.deepcopy(cells)
                for target in targets:
                    changed[target] = {"status": "NOT_MEASURED"}
                changed["quality_and_liking"] = {"value": 1e99}
                changed["future_feedback"] = {"value": 1e99}
                result = p.predict(changed, model)
                for target in targets:
                    self.assertEqual(original[target], result[target])
            corrupt = copy.deepcopy(model)
            head = next(iter(corrupt["heads"].values()))
            head["input_concepts"][0] = p.views(kind)[head["held_view"]][0]
            with self.assertRaisesRegex(ValueError, "HELD_VIEW"):
                p.predict(cells, corrupt)

    def test_masks_body_zero_and_no_imputation(self):
        records = fixture("rocchetti")
        for row in records:
            row["attribute_measurements"]["mouthfeel.body"]["value"] = 0
            row["attribute_measurements"]["mouthfeel.body"]["status"] = "OBSERVED"
        model = p.fit(records, "rocchetti", 0.05)
        self.assertEqual(model["heads"]["mouthfeel.body"]["true_zero_cells"], 0)
        missing = copy.deepcopy(records)
        missing[0]["attribute_measurements"]["mouthfeel.body"] = {
            "status": "NOT_MEASURED"
        }
        with self.assertRaisesRegex(ValueError, "COMPLETE"):
            p.fit(missing, "rocchetti", 0.05)
        false = copy.deepcopy(records)
        false[0]["attribute_masks"]["mouthfeel.body"] = False
        with self.assertRaisesRegex(ValueError, "MASK"):
            p.fit(false, "rocchetti", 0.05)

    def test_training_statistics_only_use_supplied_groups_and_constant_scale(self):
        records = fixture("rocchetti")
        model = p.fit(records[:12], "rocchetti", 0.5)
        for target, head in model["heads"].items():
            X = np.asarray(
                [
                    p.encode(
                        r["attribute_measurements"], "rocchetti", head["held_view"]
                    )
                    for r in records[:12]
                ]
            )
            np.testing.assert_array_equal(head["feature_mean"], X.mean(0))
            self.assertEqual(
                head["prior"],
                np.mean(
                    [r["attribute_measurements"][target]["value"] for r in records[:12]]
                ),
            )
        with self.assertRaisesRegex(ValueError, "HELD_IDENTITY"):
            p.evaluate(records[:1], model, "group_id", 0, "OUTER")
        historical = copy.deepcopy(records[:12])
        historical[0]["split"] = "CONFIRMATION"
        with self.assertRaisesRegex(ValueError, "ONLY_DEVELOPMENT"):
            p.fit(historical, "rocchetti", 0.5)

    def test_inner_selection_group_isolation_grid_and_deterministic_split(self):
        records = fixture("rocchetti")
        chosen, audit = p.select_ridge(records[:12], "rocchetti", "group_id", "unit")
        self.assertIn(chosen, p.RIDGES["rocchetti"])
        self.assertEqual(set(audit["scores"]), set(p.RIDGES["rocchetti"]))
        allowed = {r["group_id"] for r in records[:12]}
        counts = Counter()
        for fold in audit["inner_folds"]:
            a, b = set(fold["train_units"]), set(fold["held_units"])
            self.assertFalse(a & b)
            self.assertEqual(a | b, allowed)
            counts.update(b)
        self.assertEqual(set(counts.values()), {1})
        self.assertEqual(
            p.folds(records, "group_id", "unit"),
            p.folds(list(reversed(records)), "group_id", "unit"),
        )

    def test_macro_uses_units_and_lower_is_better(self):
        columns = p.targets("rocchetti")
        # Unequal observations must not let the large product dominate.
        rows = [
            {
                "unit": unit,
                "prior_loss": [1.0] * 12,
                "fixed_loss": [1.0] * 12,
                "selected_loss": [loss] * 12,
            }
            for unit, n, loss in [("a", 10, 0.9), ("b", 1, 0.3)]
            for _ in range(n)
        ]
        result = p.summary(rows, columns, "rocchetti")
        self.assertEqual(result["macro"]["held_units"], 2)
        self.assertEqual(result["macro"]["evaluated_cells"], 132)
        self.assertAlmostEqual(result["macro"]["P2_minus_P1"]["delta"], -0.4)
        self.assertEqual(
            result["macro"]["P2_minus_P1"]["status"], "SUPPORTED_IN_DECLARED_SCOPE"
        )

    def test_registered_protocol_keeps_tasks_and_costs_separate(self):
        protocol = p.protocol()
        self.assertEqual(len(p.targets("rocchetti")), 12)
        self.assertEqual(len(p.targets("cotter")), 17)
        self.assertFalse(protocol["main_M2_scoring_changed"])
        self.assertIsNone(protocol["cost"]["ordinary_question_count"])
        self.assertEqual(protocol["rocchetti"]["historical_products"], 9)
        self.assertEqual(protocol["cotter"]["cross_coffee"], "NOT_ESTIMABLE")


if __name__ == "__main__":
    unittest.main()
