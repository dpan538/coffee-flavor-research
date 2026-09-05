"""Guard the public research summaries against row/weight publication and drift."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r1"
sys.path.insert(0, str(ROOT / "db/scripts"))
from run_m2_r1 import scope_row


class R1ArtifactTests(unittest.TestCase):
    def test_two_axis_context_error_cannot_mean_one_axis_changed(self):
        from context_m2_r1 import perturb_context

        train = [{"c0": "immersion", "source_roast": None}]
        row = {"c0": "espresso", "source_roast": None}
        self.assertIsNone(perturb_context(row, train, "both"))
        self.assertIsNone(perturb_context(row, train, "c1_other"))
        self.assertEqual(perturb_context(row, train, "c0_other")["c0"], "immersion")
        train[0]["source_roast"] = "dark"
        row["source_roast"] = "light"
        changed = perturb_context(row, train, "both")
        self.assertNotEqual(changed["c0"], row["c0"])
        self.assertNotEqual(changed["source_roast"], row["source_roast"])

    def test_public_artifacts_do_not_contain_private_rows_or_model_weights(self):
        banned = {
            "record_id",
            "record_rows",
            "answers_by_question",
            "coefficients",
            "raw_features",
            "model_parameters",
            "selected_candidates",
            "exposed_candidates",
        }

        def inspect(value, path):
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertNotIn(key, banned, path)
                    if key in {"ranking", "raw_rows", "training_records"}:
                        self.assertNotIsInstance(item, (list, dict), path + "." + key)
                    if key == "targets":
                        self.assertNotIsInstance(item, list, path + "." + key)
                    if key == "relevant_coefficient_directions":
                        self.assertTrue(
                            all(
                                v in {"POSITIVE", "NEGATIVE", "ZERO"}
                                for v in item.values()
                            )
                        )
                    inspect(item, path + "." + key)
            elif isinstance(value, list):
                for item in value:
                    inspect(item, path + "[]")

        for path in PUBLIC.glob("*.json"):
            self.assertNotIn(".private.", path.name)
            self.assertNotIn(".model.", path.name)
            inspect(json.loads(path.read_text()), path.name)

    def test_scope_coverage_uses_the_same_filtered_denominator_as_ranking(self):
        row = {
            "ranking": ["attribute.fruity", "sensory.apple"],
            "recovery_ranking": ["attribute.fruity", "sensory.apple"],
            "hidden": ["attribute.fruity", "sensory.apple", "sensory.lemon"],
            "episode": {
                "relevance": {
                    "attribute.fruity": 1,
                    "sensory.apple": 1,
                    "sensory.lemon": 1,
                }
            },
            "candidate_target_coverage": 2 / 3,
            "direct": [],
            "coverage": 1,
        }
        filtered = scope_row(
            row, {"attribute.fruity", "sensory.apple", "sensory.lemon"}, "fine"
        )
        self.assertEqual(filtered["candidate_target_coverage"], 0.5)

    def test_real_answer_results_are_not_promoted_from_proxy(self):
        metrics = json.loads((PUBLIC / "metrics.json").read_text())
        self.assertEqual(
            metrics["final_feedback"]["real_feedback_effect"], "NOT_EVALUATED"
        )
        self.assertEqual(
            metrics["final_feedback"]["repeated_specific_and_broad_max_gain"], 0
        )
        controlled = metrics["sample_value_controlled"]
        self.assertTrue(controlled["comparability"]["same_training_question_bank"])
        self.assertFalse(
            controlled["confirmation_comparison"]["fresh_confirmation_claim_allowed"]
        )


if __name__ == "__main__":
    unittest.main()
