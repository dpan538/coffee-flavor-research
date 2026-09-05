import json, sys, unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))
from flavor_context import *


class Context(unittest.TestCase):
    def test_native_roast_never_automaps_production_seven_bins(self):
        for c0 in C0:
            for c1 in C1:
                x = encode_context({"c0": c0, "c1": c1}, "C_JOINT")
                self.assertEqual(x[8:11], [0, 0, 0])
        for x in [None, "unsure", "unknown", "skip"]:
            with self.assertRaises(ValueError):
                encode_context({"c0": C0[0], "c1": x}, "C_C0")

    def test_prediction_uses_context_not_target_truth(self):
        rows = [
            {
                "c0": C0[i % 2],
                "source_roast": None,
                "targets": [float(i)],
                "target_names": ["measurement"],
                "units": ["g/L"],
            }
            for i in range(6)
        ]
        model = fit_context(rows, "C_C0")
        before = predict_context(rows[0], model)
        changed = dict(rows[0], targets=[999999])
        self.assertEqual(before, predict_context(changed, model))
        self.assertEqual(rows[0]["targets"], [0.0])
        bad = dict(model, context_mapping_version="other")
        with self.assertRaisesRegex(ValueError, "CONTEXT_VERSION_MISMATCH"):
            predict_context(rows[0], bad)

    def test_scaler_is_training_only_and_reloaded_model_equal(self):
        rows = [
            {
                "c0": C0[i % 2],
                "source_roast": None,
                "targets": [float(i)],
                "target_names": ["m"],
                "units": ["g/L"],
            }
            for i in range(6)
        ]
        model = fit_context(rows[:4], "C_C0")
        self.assertEqual(model["scaler_parameters"]["mean"], [1.5])
        self.assertEqual(
            predict_context(rows[4], model),
            predict_context(rows[4], json.loads(json.dumps(model))),
        )

    def test_no_seven_bin_effect_claimed_from_aggregate_models(self):
        d = json.loads(
            (ROOT / "db/data/backend-sequential-model-v2/metrics.json").read_text()
        )
        self.assertEqual(d["independent_product_confirmation"], "NOT_EVALUATED")
        self.assertEqual(
            d["context"]["stanek_chemical"]["comparisons"]["C_C1_minus_C_BASE"][
                "status"
            ],
            "NOT_ESTIMABLE",
        )
        self.assertEqual(
            d["context"]["iswaldi_chemical"]["independent_coffee_groups"], 2
        )


if __name__ == "__main__":
    unittest.main()
