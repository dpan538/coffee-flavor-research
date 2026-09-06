import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import data_connections_r4 as d


class DataConnectionTests(unittest.TestCase):
    def fixture(self):
        order = d.ordered_graders({"grader-a": 1, "grader-b": 1, "grader-c": 1, "grader-d": 1})
        reports = {order[0]: {"sensory.apple"}, order[1]: {"sensory.apple", "sensory.rose"}, order[2]: {"sensory.orange", "sensory.rose"}, order[3]: {"sensory.rose", "sensory.cocoa"}}
        return d.episode_from_reports({"record_id": "synthetic", "group_id": "coffee-synthetic"}, reports), reports

    def test_reference_is_other_graders_and_only_a_exact_fine_is_excluded(self):
        episode, _ = self.fixture()
        self.assertEqual(episode["relevance"], {"sensory.cocoa": 1.0, "sensory.rose": 2.0, "sensory.orange": 1.0})
        self.assertIn("sensory.orange", episode["targets"])
        self.assertIn("sensory.rose", episode["B"])

    def test_t_does_not_change_visible_a_or_b(self):
        episode, _ = self.fixture()
        changed = copy.deepcopy(episode)
        changed["relevance"] = {"sensory.bitter": 900.0}
        for slot in ["Q0", "Q1", "Q2", "Q3", "Q4"]:
            self.assertEqual(d.available_evidence(episode, slot), d.available_evidence(changed, slot))
        self.assertEqual(d.available_evidence(episode, "Q1"), ["sensory.apple"])
        self.assertEqual(d.available_evidence(episode, "Q2"), ["sensory.apple", "sensory.rose"])

    def test_global_order_does_not_depend_on_mentions_or_dict_order(self):
        episode, reports = self.fixture()
        shuffled = dict(reversed(list(reports.items())))
        self.assertEqual(episode, d.episode_from_reports({"record_id": "synthetic", "group_id": "coffee-synthetic"}, shuffled))
        self.assertEqual(d.ordered_graders(reports), d.ordered_graders({g: {"different"} for g in reports}))

    def test_empty_t_and_exact_b_reuse_are_retained(self):
        reports = {g: {"sensory.apple"} for g in ["a", "b", "c"]}
        episode = d.episode_from_reports({"record_id": "r", "group_id": "g"}, reports)
        self.assertFalse(episode["evaluation_identifiable"])
        self.assertEqual(episode["relevance"], {})
        self.assertEqual(episode["B_new_exact_concepts"], [])
        self.assertEqual(d.available_evidence(episode, "Q4"), ["sensory.apple"])

    def test_no_recursive_shared_parent_chain(self):
        closure = d.semantic_closure({"sensory.cocoa"})
        self.assertIn("attribute.nutty_cocoa", closure)
        self.assertNotIn("sensory.dark_chocolate", closure)
        self.assertNotIn("sensory.smoky", closure)

    def test_broad_target_not_specialized_and_unknown_not_negative(self):
        order = d.ordered_graders({"a": 1, "b": 1, "c": 1})
        episode = d.episode_from_reports({"record_id": "r", "group_id": "g"}, {order[0]: {"attribute.fruity"}, order[1]: {"attribute.floral"}, order[2]: {"sensory.apple", "attribute.floral", "sensory.cocoa"}})
        self.assertEqual(episode["relevance"], {"sensory.cocoa": 1.0, "sensory.apple": 1.0})
        self.assertNotIn("negative", episode)
        with self.assertRaises(ValueError):
            d.available_evidence(episode, "FINAL")


if __name__ == "__main__":
    unittest.main()
