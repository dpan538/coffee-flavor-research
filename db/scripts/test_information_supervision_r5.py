import unittest
from unittest.mock import patch
import information_supervision_r5 as info


class InformationTests(unittest.TestCase):
    def test_nonmention_not_negative(self):
        with patch.object(
            info.training.base_training,
            "answer_for",
            return_value={"state": "NONE_OF_THESE", "selected_option_ids": []},
        ):
            self.assertEqual(info.source_answer({}, [], {})["state"], "UNSURE")

    def test_real_positive_retained(self):
        with patch.object(
            info.training.base_training,
            "answer_for",
            return_value={"state": "SELECTED", "selected_option_ids": ["x"]},
        ):
            self.assertEqual(
                info.source_answer({}, [], {})["selected_option_ids"], ["x"]
            )

    def test_group_normalization(self):
        rows = [
            {"group_id": "a", "B": ["x"]},
            {"group_id": "a", "B": ["x"]},
            {"group_id": "b", "B": ["y"]},
        ]
        self.assertEqual(info.coverage_counts(rows), {"x": 0.5, "y": 0.5})

    def test_unknown_gain_retained(self):
        self.assertIsNone(info.macro([{"group_id": "a", "gain": None}], "gain"))

    def test_full_diagnostic_preserves_initial_only_adds_B(self):
        initial = {
            "base_state": {"answers_by_question": {"Q0": {"sentinel": "original"}}}
        }
        row = {"A": ["sensory.apple"], "B": ["sensory.cocoa"]}
        with patch.object(
            info.r1, "recompute", side_effect=lambda state, bundle: state
        ), patch.object(
            info.runtime, "wrap_state", side_effect=lambda state, bundle: state
        ):
            output = info.full_state(row, {"r1_expert": {}}, initial)
        self.assertEqual(output["answers_by_question"]["Q0"], {"sentinel": "original"})
        self.assertEqual(
            output["answers_by_question"]["Q2"]["selected_option_ids"],
            ["sensory.cocoa"],
        )
        self.assertNotIn("Q2", initial["base_state"]["answers_by_question"])


if __name__ == "__main__":
    unittest.main()
