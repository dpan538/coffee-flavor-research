import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import semantic_mapping_r6 as m


class SemanticPatchTests(unittest.TestCase):
    def unit(self, identity, group, text, baseline=()):
        return {
            "observation_unit_id": identity,
            "group_id": group,
            "strict_D0_concepts": list(baseline),
            "description_fields": {"aroma": {"source_column": 5, "source_text": text}},
        }

    def example(self, name, a="a", b="b", baseline=()):
        return {
            "record_id": name,
            "group_id": name,
            "A": list(baseline),
            "B": [],
            "A_observation_unit_id": a,
            "B_observation_unit_id": b,
            "T_observation_unit_ids": [name + "-T"],
            "relevance_full": {"sensory.jasmine": 2},
            "relevance_unexpressed": {"sensory.jasmine": 2},
            "T_ordinal": {"native": [0, 4]},
            "source_C1": None,
        }

    def fixture(self, text):
        e = self.example("training")
        units = {
            "a": self.unit("a", "training", text),
            "b": self.unit("b", "training", ""),
        }
        return e, units

    def test_whole_span_and_polarity_preserved_without_substring(self):
        e, units = self.fixture(
            " floral notes, red berries; roasted nuts\n milk chocolate."
        )
        patch = m.fit_patch([e], units, {"training"})
        result = m.apply_inputs(e, units, patch)
        self.assertEqual(
            set(result["A"]),
            {"attribute.floral", "attribute.fruity", "broad.nutty", "broad.chocolate"},
        )
        self.assertNotIn("sensory.jasmine", result["A"])
        self.assertNotIn("sensory.dark_chocolate", result["A"])
        self.assertNotIn("sensory.cocoa", result["A"])
        for trace in result["mapping_input_trace"]:
            self.assertEqual(
                trace["source_text"][trace["span_start"] : trace["span_end"]],
                trace["raw_span"],
            )
            self.assertEqual(trace["status"], "SOURCE_CHECKED")
        self.assertEqual(e["A"], [])

    def test_negation_uncertainty_and_compound_never_create_positive(self):
        e, units = self.fixture("red berries")
        patch = m.fit_patch([e], units, {"training"})
        for text in [
            "not red berries",
            "red berries or nuts",
            "red berries/nuts",
            "maybe red berries",
            "no floral notes, red berries",
            "an odd red berries sensation",
            "red berries. no fruit",
        ]:
            with self.subTest(text=text):
                units["a"] = self.unit("a", "training", text)
                self.assertEqual(m.apply_inputs(e, units, patch)["A"], [])

    def test_independent_T_and_hidden_T_are_never_changed(self):
        e, units = self.fixture("floral notes")
        e["relevance_full"] = {"attribute.floral": 1, "sensory.jasmine": 2}
        before = copy.deepcopy(e)
        patch = m.fit_patch([e], units, {"training"})
        result = m.apply_inputs(e, units, patch)
        for key in before.keys() - {"A", "B"}:
            self.assertEqual(result[key], before[key])
        self.assertEqual(e, before)

    def test_training_support_excludes_held_unique_form_and_T_units(self):
        train, units = self.fixture("red berries")
        held = self.example("held", "held-a", "held-b")
        units.update(
            {
                "held-a": self.unit("held-a", "held", "roasted peanuts"),
                "held-b": self.unit("held-b", "held", ""),
                "training-T": self.unit("training-T", "training", "milk chocolate"),
            }
        )
        patch = m.fit_patch([train, held], units, {"training"}, {"held"})
        self.assertEqual(
            [r["normalized_span"] for r in patch["rules"]], ["red berries"]
        )
        self.assertEqual(m.apply_inputs(held, units, patch)["A"], [])
        with self.assertRaisesRegex(ValueError, "TRAINING_GROUP_LEAKAGE"):
            m.fit_patch([train, held], units, {"training", "held"}, {"held"})

    def test_target_content_does_not_select_rule(self):
        e, units = self.fixture("red berries")
        p1 = m.fit_patch([e], units, {"training"})
        e["relevance_full"] = {"sensory.cocoa": 1000}
        e["relevance_unexpressed"] = {"sensory.almond": 500}
        e["T_ordinal"] = {"completely": "different"}
        p2 = m.fit_patch([e], units, {"training"})
        self.assertEqual(p1, p2)

    def test_replayed_input_does_not_accumulate_concepts(self):
        e, units = self.fixture("red berries, red berries")
        patch = m.fit_patch([e], units, {"training"})
        first = m.apply_inputs(e, units, patch)
        second = m.apply_inputs(first, units, patch)
        self.assertEqual(first["A"], ["attribute.fruity"])
        self.assertEqual(second["A"], first["A"])
        self.assertEqual(
            sum(bool(t["added_concepts"]) for t in first["mapping_input_trace"]), 1
        )
        self.assertEqual(
            sum(bool(t["added_concepts"]) for t in second["mapping_input_trace"]), 0
        )

    def test_same_raw_row_cannot_be_input_and_T(self):
        e, units = self.fixture("red berries")
        e["T_observation_unit_ids"] = ["a"]
        with self.assertRaisesRegex(ValueError, "DISJOINT_INPUT"):
            m.fit_patch([e], units, {"training"})

    def test_rule_payload_and_unchecked_fine_child_are_rejected(self):
        e, units = self.fixture("floral notes")
        patch = m.fit_patch([e], units, {"training"})
        patch["rules"][0]["concepts"] = ["sensory.jasmine"]
        with self.assertRaisesRegex(ValueError, "PAYLOAD_CHANGED"):
            m.apply_inputs(e, units, patch)
        patch["patch_sha256"] = m.digest(
            {k: v for k, v in patch.items() if k != "patch_sha256"}
        )
        with self.assertRaisesRegex(ValueError, "UNCHECKED_RULE"):
            m.apply_inputs(e, units, patch)

    def test_tropical_modifier_is_not_fruit_and_unspecified_tea_is_not_specific(self):
        e, units = self.fixture("tropical, tropical fruits, tea")
        patch = m.fit_patch([e], units, {"training"})
        self.assertNotIn("tropical", [r["normalized_span"] for r in patch["rules"]])
        result = m.apply_inputs(e, units, patch)
        self.assertEqual(
            set(result["A"]), {"attribute.fruity", "attribute.green_vegetative"}
        )
        self.assertNotIn("sensory.black_tea", result["A"])
        self.assertNotIn("sensory.green_tea", result["A"])


if __name__ == "__main__":
    unittest.main()
