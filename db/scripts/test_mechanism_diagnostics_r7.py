"""Synthetic R7 intervention and posthoc measurement-audit invariants."""

import copy
import inspect
import unittest
from unittest.mock import patch

import mechanism_diagnostics_r7 as m


def question(slot, index):
    concepts = ["sensory.apple", "sensory.orange", "sensory.lemon", "sensory.lime"][
        : m.information.BUDGETS[slot]
    ]
    return {
        "slot": slot,
        "axis": "axis" + str(index),
        "question_id": "q" + str(index),
        "shown_option_ids": concepts,
        "options": [
            {"id": c, "kind": "specific", "attribute": "fruity"} for c in concepts
        ],
    }


class ProtocolTests(unittest.TestCase):
    def test_exactly_three_no_fit_diagnostics_and_fixed_budget(self):
        self.assertEqual(len(m.DIAGNOSTICS), 3)
        self.assertEqual(m.protocol()["fit_count"], 0)
        self.assertEqual(sum(m.protocol()["ordinary_budgets"].values()), 19)
        self.assertIn("NOT_DEPLOYABLE", m.protocol()["D_FIXED_EXPOSURE"])

    def test_executor_has_no_target_record_or_model_fit_argument(self):
        self.assertEqual(
            list(inspect.signature(m.run_trajectory).parameters),
            [
                "initial_observations",
                "later_observations",
                "context",
                "bundle",
                "coverage",
                "fixed_questions",
            ],
        )

    def test_channel_ownership_is_exact(self):
        base, mapped = {"A": ["base"]}, {"A": ["patched"]}
        c0, cp, qs = {"a": 0.1}, {"a": 0.2}, ["actual"]
        self.assertEqual(
            m.channel_inputs("D_COVERAGE_ONLY", base, mapped, c0, cp, qs),
            (base, cp, None),
        )
        self.assertEqual(
            m.channel_inputs("D_OBSERVATION_ONLY", base, mapped, c0, cp, qs),
            (mapped, c0, None),
        )
        self.assertEqual(
            m.channel_inputs("D_FIXED_EXPOSURE", base, mapped, c0, cp, qs),
            (mapped, c0, qs),
        )
        with self.assertRaises(ValueError):
            m.channel_inputs("D_FOURTH", base, mapped, c0, cp, qs)


class FixedExposureTests(unittest.TestCase):
    def setUp(self):
        self.questions = [
            question(slot, i) for i, slot in enumerate(m.information.BUDGETS)
        ]
        self.bundle = {"r1_expert": {}}

    def expose(self, base, slot, q, expert):
        return {**copy.deepcopy(base), "pending": copy.deepcopy(q)}

    def wrap(self, base, bundle, **kwargs):
        return {"base_state": base}

    def source_answer(self, q, visible, expert):
        selected = sorted(set(q["shown_option_ids"]) & set(visible))
        return {
            **q,
            "selected_option_ids": selected,
            "state": "SELECTED" if selected else "UNSURE",
        }

    def update(self, prepared, answer, bundle):
        state = copy.deepcopy(prepared)
        state["base_state"]["answers_by_question"][answer["slot"]] = answer
        state["candidate_scores"] = []
        return state

    def test_fixed_complete_questions_options_order_and_new_answers(self):
        with (
            patch.object(
                m.information,
                "initial_state",
                return_value={"base_state": {"answers_by_question": {}}},
            ),
            patch.object(
                m.information,
                "select",
                side_effect=AssertionError("NO_ADAPTIVE_RESELECTION"),
            ),
            patch.object(m.r1, "expose_question", side_effect=self.expose),
            patch.object(m.runtime, "wrap_state", side_effect=self.wrap),
            patch.object(
                m.runtime,
                "select_next_question",
                side_effect=lambda s, b: {"question": s["base_state"]["pending"]},
            ),
            patch.object(m.provider, "source_answer", side_effect=self.source_answer),
            patch.object(m.information, "update", side_effect=self.update),
        ):
            out = m.run_trajectory(
                ["sensory.apple"],
                ["sensory.orange"],
                {},
                self.bundle,
                {},
                self.questions,
            )
        self.assertEqual(out["questions"], self.questions)
        answers = out["state"]["base_state"]["answers_by_question"]
        self.assertEqual(answers["Q0"]["selected_option_ids"], ["sensory.apple"])
        self.assertEqual(
            answers["Q2"]["selected_option_ids"], ["sensory.apple", "sensory.orange"]
        )

    def test_incomplete_fixed_exposure_rejected_no_padding(self):
        with patch.object(m.information, "initial_state", return_value={}):
            with self.assertRaisesRegex(ValueError, "COMPLETE_C01"):
                m.run_trajectory([], [], {}, self.bundle, {}, self.questions[:-1])
            bad = copy.deepcopy(self.questions)
            bad[-1]["options"] = bad[-1]["options"][:2]
            with self.assertRaisesRegex(ValueError, "BUDGET_CHANGED"):
                m.run_trajectory([], [], {}, self.bundle, {}, bad)

    def test_option_presentation_order_is_not_new_budget_content(self):
        left = {"questions": copy.deepcopy(self.questions)}
        right = copy.deepcopy(left)
        right["questions"][2]["shown_option_ids"].reverse()
        right["questions"][2]["options"].reverse()
        flags = m.exposure_structure(left, right)
        self.assertTrue(flags["option_order_only_changed"])
        self.assertFalse(flags["whole_exposure_content_changed"])

    def test_swapping_equal_budget_axes_keeps_whole_exposure_content(self):
        left = {"questions": copy.deepcopy(self.questions)}
        right = copy.deepcopy(left)
        right["questions"][2], right["questions"][3] = (
            right["questions"][3],
            right["questions"][2],
        )
        flags = m.exposure_structure(left, right)
        self.assertTrue(flags["axis_sequence_only_changed"])
        self.assertFalse(flags["whole_exposure_content_changed"])


class MeasurementAuditTests(unittest.TestCase):
    def record(self):
        return {
            "group_id": "coffee",
            "A_observation_unit_id": "A",
            "B_observation_unit_id": "B",
            "T_observation_unit_ids": ["T"],
            "relevance_full": {},
        }

    def unit(self, text):
        return {
            "T": {
                "group_id": "coffee",
                "observation_unit_id": "T",
                "description_fields": {
                    "aroma": {"source_text": text, "source_column": "AROMA"}
                },
            }
        }

    def test_source_T_explicit_alias_loss_is_flagged_without_target_mutation(self):
        record = self.record()
        old = copy.deepcopy(record)
        result = m.target_measurement_audit(
            record, self.unit("Red apple"), [{"added_concepts": ["sensory.apple"]}]
        )
        self.assertEqual(
            result["fine_concepts_explicit_in_raw_T_but_missing_fixed_T"],
            ["sensory.apple"],
        )
        self.assertEqual(record, old)
        self.assertFalse(result["target_mutated"])

    def test_negative_compound_and_broad_T_do_not_manufacture_fine_target(self):
        for text in ("not red apple", "red apple / pear", "floral notes"):
            result = m.target_measurement_audit(
                self.record(),
                self.unit(text),
                [{"added_concepts": ["sensory.apple", "attribute.floral"]}],
            )
            self.assertEqual(
                result["fine_concepts_explicit_in_raw_T_but_missing_fixed_T"], []
            )

    def test_already_represented_T_not_counted_as_mapping_loss(self):
        record = self.record()
        record["relevance_full"] = {"sensory.apple": 1}
        result = m.target_measurement_audit(
            record, self.unit("red apple"), [{"added_concepts": ["sensory.apple"]}]
        )
        self.assertEqual(
            result["verified_rule_matches"][0]["status"], "ALREADY_IN_FIXED_TARGET"
        )

    def test_newly_exposed_existing_concept_also_receives_posthoc_T_audit(self):
        result = m.target_measurement_audit(
            self.record(), self.unit("red apple"), [], ["sensory.apple"]
        )
        self.assertEqual(
            result["fine_concepts_explicit_in_raw_T_but_missing_fixed_T"],
            ["sensory.apple"],
        )

    def test_role_overlap_rejected(self):
        record = self.record()
        record["T_observation_unit_ids"] = ["A"]
        with self.assertRaisesRegex(ValueError, "OVERLAP"):
            m.target_measurement_audit(record, {}, [])

    def test_nonmention_not_labeled_source_mapping_error_or_disagreement(self):
        a = {"questions": [], "selected": {"ASK": []}, "full_T": {"sensory.orange": 1}}
        b = {**a, "selected": {"ASK": ["sensory.apple"]}}
        c = m.category(a, b, [])
        self.assertEqual(c["classification"], "UNRESOLVED")
        self.assertFalse(c["source_mapping_error_established"])
        self.assertFalse(c["class4_disagreement_established"])

    def test_detail_sampling_preserves_strata_and_limit(self):
        rows = [
            {
                "record_id": str(i),
                "changed": True,
                "comparisons": {
                    "C11": {
                        "outcome": (
                            "REGRESSION",
                            "IMPROVEMENT",
                            "TIE",
                            "NO_EVALUABLE_T",
                        )[i % 4],
                        "gap_delta": (
                            0.1
                            if i % 4 == 0
                            else -0.1 if i % 4 == 1 else None if i % 4 == 3 else 0
                        ),
                    }
                },
            }
            for i in range(30)
        ]
        chosen = m.choose_details(rows)
        self.assertEqual(len(chosen), 12)
        self.assertEqual(
            {r["comparisons"]["C11"]["outcome"] for r in chosen},
            {"REGRESSION", "IMPROVEMENT", "TIE", "NO_EVALUABLE_T"},
        )
        self.assertEqual(chosen, m.choose_details(list(reversed(rows))))


if __name__ == "__main__":
    unittest.main()
