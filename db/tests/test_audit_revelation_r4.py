import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_revelation_r4 as audit
from train_m2_r1 import answer_for
from flavor_m2_r1 import PARENTS


class RevelationAuditTests(unittest.TestCase):
    def answer(self, slot, options, visible):
        question = {"slot": slot, "question_id": slot + "-synthetic", "axis": slot, "shown_option_ids": [o["id"] for o in options], "options": options}
        return {**question, **answer_for(question, visible, {"candidate_attributes": PARENTS})}

    def specific(self, concept):
        return {"id": concept, "kind": "specific"}

    def broad(self, attr):
        return {"id": "attribute." + attr, "kind": "broad", "attribute": attr}

    def test_b_same_parent_specific_not_exposed_is_not_falsely_claimed(self):
        episode = {"A": ["sensory.apple"], "B": ["sensory.orange"]}
        answers = [self.answer("Q0", [self.specific("sensory.apple")], episode["A"]), self.answer("Q2", [self.broad("fruity")], episode["A"] + episode["B"])]
        result = audit.exposure_novelty(episode, answers, answer_for, {"candidate_attributes": PARENTS})
        self.assertEqual(result["B_actual_new_specific"], [])
        self.assertEqual(result["B_new_system_canonical"], [])
        self.assertEqual(result["source_B_new_specific_not_selected"], ["sensory.orange"])

    def test_actual_same_parent_new_fine_is_retained(self):
        episode = {"A": ["sensory.apple"], "B": ["sensory.orange"]}
        answers = [self.answer("Q0", [self.specific("sensory.apple")], episode["A"]), self.answer("Q2", [self.specific("sensory.orange")], episode["A"] + episode["B"])]
        result = audit.exposure_novelty(episode, answers, answer_for, {"candidate_attributes": PARENTS})
        self.assertEqual(result["B_actual_new_specific"], ["sensory.orange"])
        self.assertEqual(result["B_actual_new_related_specific"], ["sensory.orange"])

    def test_newly_exposed_a_is_not_attributed_to_b(self):
        episode = {"A": ["sensory.apple", "sensory.rose"], "B": ["sensory.apple"]}
        answers = [self.answer("Q0", [self.specific("sensory.apple")], episode["A"]), self.answer("Q2", [self.specific("sensory.rose")], episode["A"] + episode["B"])]
        result = audit.exposure_novelty(episode, answers, answer_for, {"candidate_attributes": PARENTS})
        self.assertEqual(result["A_only_later_new_system_canonical"], ["sensory.rose"])
        self.assertFalse(result["B_new_system_canonical"])

    def test_targets_cannot_influence_novelty_and_repeats_do_not_add(self):
        episode = {"A": ["sensory.apple"], "B": ["sensory.rose"], "relevance": {"sensory.cocoa": 1}}
        answers = [self.answer("Q0", [self.specific("sensory.apple")], episode["A"]), self.answer("Q2", [self.specific("sensory.rose")], episode["A"] + episode["B"]), self.answer("Q3", [self.specific("sensory.rose")], episode["A"] + episode["B"])]
        original = audit.exposure_novelty(episode, answers, answer_for, {"candidate_attributes": PARENTS})
        altered = copy.deepcopy(episode)
        altered["relevance"] = {"sensory.rose": 1000}
        self.assertEqual(original, audit.exposure_novelty(altered, answers, answer_for, {"candidate_attributes": PARENTS}))
        self.assertEqual(original["B_new_system_canonical"], ["sensory.rose"])
        self.assertEqual(original["exposure_trace"][-1]["new_canonical_at_this_stage"], [])

    def test_unexposed_selection_rejected(self):
        with self.assertRaises(ValueError):
            audit.canonical_selection({"options": [self.specific("sensory.apple")], "shown_option_ids": [], "selected_option_ids": ["sensory.apple"]})


if __name__ == "__main__":
    unittest.main()
