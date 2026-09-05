import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r2"


class R2PublicArtifactTests(unittest.TestCase):
    def test_public_summaries_do_not_contain_private_weights_or_observations(self):
        forbidden = {
            "record_id",
            "training_record_ids",
            "training_identities",
            "record_rows",
            "coefficients",
            "advantage_coefficients",
            "model_parameters",
            "feature_mean",
            "feature_scale",
            "target_mean",
            "target_scale",
            "raw_text",
            "answer_sequence",
            "attribute_measurements",
        }

        def inspect(value, path):
            if isinstance(value, dict):
                self.assertFalse(forbidden & set(value), str(path))
                for key, item in value.items():
                    inspect(item, f"{path}.{key}")
            elif isinstance(value, list):
                for item in value:
                    inspect(item, path)

        for path in PUBLIC.glob("*.json"):
            inspect(json.loads(path.read_text()), path.name)

    def test_new_objective_does_not_relabel_r1_or_real_user_results(self):
        contract = json.loads(
            (PUBLIC / "objective_and_metric_contract.json").read_text()
        )
        receipt = json.loads((PUBLIC / "run_receipt.json").read_text())
        self.assertEqual(contract["primary_task"], "OBSERVED_DESCRIPTOR_RECOVERY")
        self.assertEqual(
            contract["primary_cost"], "ACTUALLY_OFFERED_ORDINARY_OPTION_COUNT"
        )
        self.assertEqual(contract["foundation"]["default"], "OFF")
        self.assertFalse(receipt["old_results_reinterpreted"])
        self.assertEqual(receipt["real_user_alignment"], "NOT_EVALUATED")
        self.assertEqual(receipt["real_user_time_efficiency"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
