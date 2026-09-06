import inspect
import unittest
from unittest.mock import patch
import information_supervision_r6 as r6


class ObservableTests(unittest.TestCase):
    def state(self):
        return {
            "base_state": {
                "answers_by_question": {
                    s: {
                        "slot": s,
                        "axis": s,
                        "options": [
                            {"id": c, "kind": "specific", "attribute": "fruity"}
                        ],
                        "selected_option_ids": [c],
                        "shown_option_ids": [c],
                    }
                    for s, c in [("Q0", "sensory.apple"), ("Q1", "sensory.orange")]
                }
            }
        }

    def test_selector_has_no_record_argument(self):
        self.assertEqual(
            list(inspect.signature(r6.select_r6_question).parameters),
            ["state", "expert", "train_coverage", "option_budget"],
        )

    def test_initial_only_no_later_information(self):
        state = self.state()
        state["base_state"]["answers_by_question"]["Q2"] = {
            "slot": "Q2",
            "options": [{"id": "sensory.honey", "kind": "specific"}],
            "selected_option_ids": ["sensory.honey"],
            "shown_option_ids": ["sensory.honey"],
        }
        self.assertEqual(
            r6.initial_concepts(state), frozenset({"sensory.apple", "sensory.orange"})
        )

    def test_legal_parent_only(self):
        self.assertEqual(r6.directions(["attribute.floral"]), ["attribute.floral"])
        self.assertNotIn("sensory.jasmine", r6.directions(["attribute.floral"]))

    def test_budget_is_predetermined(self):
        self.assertEqual(r6.BUDGETS, {"Q0": 4, "Q1": 4, "Q2": 4, "Q3": 4, "Q4": 3})

    def test_train_coverage_excludes_held(self):
        row = {
            "B_observation_unit_id": "x",
            "group_id": "held",
            "record_id": "r",
            "B": ["sensory.apple"],
        }
        with self.assertRaises(ValueError):
            r6.coverage_for([row], {"held"})

    def test_full_source_not_present_in_selection(self):
        state = self.state()
        expert = {
            "question_bank": {
                "correction": [
                    {
                        "axis": "a",
                        "options": [
                            {
                                "id": "sensory.apple",
                                "kind": "specific",
                                "attribute": "fruity",
                            }
                        ],
                    }
                ]
            }
        }
        result = r6.select_r6_question(state, expert, {"sensory.apple": 0.5}, 1)
        self.assertEqual(result["axis"], "a")

    def test_capacity_failure_not_padded(self):
        state = self.state()
        expert = {
            "question_bank": {
                "correction": [
                    {
                        "axis": "a",
                        "options": [
                            {
                                "id": "sensory.apple",
                                "kind": "specific",
                                "attribute": "fruity",
                            }
                        ],
                    }
                ]
            }
        }
        with self.assertRaisesRegex(ValueError, "NO_LEGAL_AXIS"):
            r6.select_r6_question(state, expert, {"sensory.apple": 0.5}, 4)

    def test_update_cannot_bypass_fixed_budget(self):
        with self.assertRaisesRegex(ValueError, "R6_PREDECLARED"):
            r6.update({}, {"slot": "Q4", "shown_option_ids": ["a", "b", "c", "d"]}, {})


if __name__ == "__main__":
    unittest.main()
