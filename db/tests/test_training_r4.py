"""R4 identity, missing-label and training-scope regression checks."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import train_conditioning_r4 as t


class TrainingContracts(unittest.TestCase):
    def rows(self):
        rows = []
        for i, gain in enumerate([0.0, 0.0, 0.2, None]):
            rows.append(
                {
                    "record_id": str(i),
                    "group_id": str(i),
                    "gain": gain,
                    "features": {"x": float(i)},
                    "scorer_training_groups": [],
                    "scorer_bundle_id": "frozen_" + str(i),
                }
            )
        return rows

    def test_unknown_gain_is_not_a_tie(self):
        r = t.fit_key_case(self.rows(), ["x"], {"0", "1", "2", "3"}, set())
        self.assertEqual(r["labelled_records"], 3)
        self.assertEqual(r["all_records"], 4)
        self.assertEqual(r["ties"], 2)
        self.assertEqual(r["key_records"], 1)

    def test_scorer_oof_required(self):
        rows = self.rows()
        rows[0]["scorer_training_groups"] = ["0"]
        with self.assertRaisesRegex(ValueError, "OUT_OF_GROUP"):
            t.fit_key_case(rows, ["x"], {"0", "1", "2", "3"}, set())

    def test_single_class_is_not_dynamic(self):
        rows = self.rows()[:2]
        r = t.fit_key_case(rows, ["x"], {"0", "1"}, set())
        self.assertEqual(r["constant_probability"], 0)
        self.assertIn("NOT_DYNAMIC", r["fit_status"])

    def test_no_silent_pair_drop(self):
        rows = [
            {"model": "a", "record_id": "1", "group_id": "g", "raw_gap": 0.2},
            {"model": "b", "record_id": "2", "group_id": "g", "raw_gap": 0.2},
        ]
        with self.assertRaisesRegex(ValueError, "ALIGN"):
            t.paired(rows, "a", "b")

    def test_same_record_repeats_not_extra_group_weight(self):
        rows = [{"record_id": "a", "group_id": "g", "slot": "Q2"}] * 2
        self.assertAlmostEqual(sum(t.group_weights(rows)), 1.0)


if __name__ == "__main__":
    unittest.main()
