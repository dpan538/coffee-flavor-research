"""Executable synthetic semantic invariants, never sensory evaluation labels."""

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import flavor_foundation_r1 as f
import flavor_m2_r1 as backend
import train_m2_r1 as trainer
import evaluate_foundation_r1 as evaluator
from test_flavor_sequential import fixture


class FoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fixture()
        cls.bundle = trainer.make_bundle(
            cls.records, manifest_hash="SYNTHETIC_UNIT_FIXTURE"
        )
        cls.model = f.fit_foundation(cls.records, cls.bundle)
        cls.active = copy.deepcopy(cls.bundle)
        cls.active["foundation_model"] = cls.model
        cls.active["foundation_check_enabled"] = True

    def test_partial_labels_do_not_invent_negatives(self):
        y, mask, complete = f.attribute_labels(
            {"source_family": "zenodo", "targets": ["sensory.jasmine"]}
        )
        self.assertEqual(int(mask.sum()), 1)
        self.assertFalse(complete.any())
        self.assertEqual(y[f.DIMENSIONS.index("floral")], 1.0)
        _, mask, complete = f.attribute_labels(
            {
                "source_family": "inera",
                "attribute_names": ["floral", "fruity"],
                "attribute_values": [0, None],
            }
        )
        self.assertTrue(mask[f.DIMENSIONS.index("floral")])
        self.assertFalse(mask[f.DIMENSIONS.index("fruity")])
        self.assertTrue(complete[f.DIMENSIONS.index("floral")])

    def test_positive_only_dimension_not_fitted_all_high(self):
        rows = [{**r, "source_family": "positive_only"} for r in self.records]
        model = f.fit_foundation(rows, self.bundle)
        self.assertEqual(model["supported_dimensions"], [])
        self.assertTrue(
            np.array_equal(
                np.asarray(model["coefficients"]), 0 * np.asarray(model["coefficients"])
            )
        )

    def test_partition_and_target_never_generate_answer_or_question(self):
        episode = f.split_episode(self.records[2])
        self.assertFalse(set(episode["A"]) & set(episode["B"]))
        self.assertFalse(set(episode["A"] + episode["B"]) & set(episode["T"]))
        replacement = copy.deepcopy(episode)
        replacement["T"] = ["sensory.arbitrary_hidden_only"]
        replacement["relevance"] = {"sensory.arbitrary_hidden_only": 999}
        _, before, answers = f.trajectory(
            self.records[2], self.active, backend, "V2", episode
        )
        _, after, second_answers = f.trajectory(
            self.records[2], self.active, backend, "V2", replacement
        )
        self.assertEqual(answers, second_answers)
        self.assertEqual(before[-1]["candidate_scores"], after[-1]["candidate_scores"])
        self.assertEqual(before[-1]["foundation"], after[-1]["foundation"])

    def test_equal_budget_frozen_state_and_once_only(self):
        rows = [
            f.evaluate_record(self.records[3], self.active, backend, variant)
            for variant in ["V0", "V1", "V2"]
        ]
        self.assertEqual(len({r["target_hash"] for r in rows}), 1)
        self.assertEqual(len({r["question_count"] for r in rows}), 1)
        self.assertEqual(len({r["option_budget"] for r in rows}), 1)
        _, states, answers = f.trajectory(self.records[3], self.active, backend, "V2")
        slots = [a["slot"] for a in answers]
        self.assertEqual(slots, ["Q0", "Q1", "Q2", "Q3", "Q4"])
        self.assertEqual(sum(a["axis"].startswith("foundation.") for a in answers), 1)
        self.assertEqual(
            backend.digest(states[-1]["foundation_before_check"]),
            states[-1]["foundation_before_check_hash"],
        )
        with self.assertRaises(ValueError):
            f.select_check_question(states[-1], self.active, self.model)
        with self.assertRaises(ValueError):
            f.select_check_question(states[3], self.active, self.model, "Q4")

    def test_repeated_evidence_and_derived_parent_have_zero_gain(self):
        state = f._concept_state(["sensory.jasmine"])
        before = f.predict_foundation(state, self.bundle, self.model)
        state["answers_by_question"]["Q3"] = copy.deepcopy(
            state["answers_by_question"]["Q0"]
        )
        after = f.predict_foundation(state, self.bundle, self.model)
        self.assertEqual(before, after)
        state["answers_by_question"]["Q4"] = f._concept_state(["attribute.floral"])[
            "answers_by_question"
        ]["Q0"]
        parent = f.predict_foundation(state, self.bundle, self.model)
        self.assertEqual(before["dimension_values"], parent["dimension_values"])
        check = f.compare_check(before, parent)
        self.assertEqual(check["evidence_status"], "DERIVED_REUSE")
        self.assertEqual(check["max_support_change"], 0.0)
        broad = f._concept_state(["attribute.floral"])
        before = f.predict_foundation(broad, self.bundle, self.model)
        broad["final_comparison"] = {"selected_candidates": ["attribute.floral"]}
        self.assertEqual(before, f.predict_foundation(broad, self.bundle, self.model))

    def test_new_evidence_can_correct_wrong_direction(self):
        model = copy.deepcopy(self.model)
        coefficients = np.zeros_like(np.asarray(model["coefficients"]))
        fruity, floral = f.DIMENSIONS.index("fruity"), f.DIMENSIONS.index("floral")
        coefficients[0, fruity] = 0.8
        coefficients[0, floral] = 0.2
        coefficients[1 + len(f.DIMENSIONS) + floral, floral] = 0.75
        model["coefficients"] = coefficients.tolist()
        before = f.predict_foundation(f._concept_state([]), self.bundle, model)
        after = f.predict_foundation(
            f._concept_state(["attribute.floral"]), self.bundle, model
        )
        self.assertEqual(
            before["competing_profile_hypotheses"][0]["dimension"], "fruity"
        )
        self.assertEqual(
            after["competing_profile_hypotheses"][0]["dimension"], "floral"
        )
        self.assertEqual(f.compare_check(before, after)["status"], "REVISION_REQUIRED")

    def test_none_is_scope_limited_reversible_and_idempotent(self):
        state = f._concept_state(["attribute.floral"])
        before = f.predict_foundation(state, self.bundle, self.model)
        negative = f._concept_state(["attribute.floral"])["answers_by_question"]["Q0"]
        negative.update(state="NONE_OF_THESE", selected_option_ids=[])
        state["answers_by_question"]["Q3"] = negative
        after = f.predict_foundation(state, self.bundle, self.model)
        self.assertLess(
            after["dimension_values"]["floral"], before["dimension_values"]["floral"]
        )
        check = f.compare_check(before, after)
        self.assertEqual(check["status"], "REVISION_REQUIRED")
        self.assertEqual(check["evidence_status"], "NEW_EXPOSED_NEGATIVE_EVIDENCE")
        self.assertTrue(check["new_evidence_unit_ids"])
        for dim in set(f.DIMENSIONS) - {"floral"}:
            self.assertEqual(
                after["dimension_values"][dim], before["dimension_values"][dim]
            )
        state["answers_by_question"]["Q4"] = copy.deepcopy(negative)
        self.assertEqual(
            f.predict_foundation(state, self.bundle, self.model)["dimension_values"],
            after["dimension_values"],
        )
        del state["answers_by_question"]["Q4"]
        state["answers_by_question"]["Q3"].update(state="UNSURE")
        self.assertEqual(
            f.predict_foundation(state, self.bundle, self.model)["dimension_values"],
            before["dimension_values"],
        )

    def test_all_positive_broad_inputs_monotone_for_every_representation(self):
        for representation in f.REPRESENTATIONS:
            model = f.fit_foundation(self.records, self.bundle, representation)
            state = f._concept_state(["sensory.jasmine"])
            before = f.predict_foundation(state, self.bundle, model)
            for dimension in f.DIMENSIONS:
                added = copy.deepcopy(state)
                added["answers_by_question"]["Q3"] = f._concept_state(
                    ["attribute." + dimension]
                )["answers_by_question"]["Q0"]
                after = f.predict_foundation(added, self.bundle, model)
                self.assertTrue(
                    all(
                        after["dimension_values"][d]
                        >= before["dimension_values"][d] - 1e-12
                        for d in f.DIMENSIONS
                    )
                )

    def test_cross_fit_excludes_every_prediction_group(self):
        rows, audit = f.cross_fit_foundation(
            self.records, self.bundle, "explicit_attributes"
        )
        self.assertEqual(
            {r["group_id"] for r in rows}, {r["group_id"] for r in self.records}
        )
        for fold in audit:
            self.assertFalse(set(fold["train_groups"]) & set(fold["prediction_groups"]))
        with self.assertRaises(ValueError):
            f.evaluate_experiment(self.records, self.records[:1], self.bundle, backend)

    def test_all_representations_reload_runtime_and_f2_terminal(self):
        for representation in f.REPRESENTATIONS:
            active = copy.deepcopy(self.active)
            active["foundation_model"] = f.fit_foundation(
                self.records, self.bundle, representation
            )
            active["foundation_model"]["fusion_strength"] = 0.5
            ep, states, answers = f.trajectory(self.records[0], active, backend, "V2")
            payload = {
                "contract_version": backend.VERSIONS["contract_version"],
                "context": ep["context"],
                "answers": answers,
            }
            live = f.run(payload, active)
            reload = f.run(payload, json.loads(json.dumps(active)))
            self.assertEqual(live, reload)
            self.assertEqual(
                states[-1]["candidate_scores"], live["state"]["candidate_scores"]
            )
            for change in live["state"]["last_answer_update"]:
                self.assertAlmostEqual(
                    change["score_after"] - change["score_before"],
                    sum(
                        change[key]
                        for key in [
                            "context_component",
                            "direct_answer_component",
                            "semantic_component",
                            "interaction_component",
                            "foundation_component",
                        ]
                    ),
                )
            exposure = live["exposure"]
            self.assertEqual(
                exposure["candidate_ids"],
                [r["candidate_id"] for r in live["main"] + live["secondary"]],
            )
            selected = [
                c
                for c in exposure["candidate_ids"]
                if c in live["state"]["interpreted_evidence"]["specific"]
            ]
            updated = f.apply_final_comparison(
                live["state"],
                exposure["candidate_ids"],
                selected,
                active,
                backend,
                feedback_source="SIMULATED",
                generation_version=active["bundle_id"],
            )
            self.assertEqual(updated["current_stage"], "FINAL_RESULT")
            self.assertEqual(
                updated["foundation"]["dimension_values"],
                live["state"]["foundation"]["dimension_values"],
            )
            self.assertEqual(
                [r["score"] for r in updated["candidate_scores"]],
                [r["score"] for r in live["state"]["candidate_scores"]],
            )
            with self.assertRaises(ValueError):
                f.apply_final_comparison(
                    updated,
                    exposure["candidate_ids"],
                    selected,
                    active,
                    backend,
                    feedback_source="SIMULATED",
                    generation_version=active["bundle_id"],
                )

    def test_grouped_replay_duplicate_and_replacement_match_runtime(self):
        ep, states, answers = f.trajectory(self.records[3], self.active, backend, "V2")
        payload = {
            "contract_version": backend.VERSIONS["contract_version"],
            "context": ep["context"],
            "answers": answers,
        }
        flat = f.run(payload, self.active)
        batched = f.run({**payload, "answers": [answers[:2], answers[2:]]}, self.active)
        self.assertEqual(flat, batched)
        duplicate = f.run({**payload, "answers": answers + [answers[3]]}, self.active)
        self.assertEqual(flat, duplicate)
        unchanged = f.update_state(
            states[-1], answers[3], self.active, backend, f.PROXY
        )
        self.assertEqual(unchanged, states[-1])
        replacement = {**answers[3], "selected_option_ids": [], "state": "UNSURE"}
        changed = f.run({**payload, "answers": answers + [replacement]}, self.active)
        self.assertEqual(len(changed["state"]["answers_by_question"]), 5)
        self.assertEqual(
            changed["state"]["answers_by_question"]["Q3"]["state"], "UNSURE"
        )

    def test_lower_attribute_error_is_improvement_and_empty_target_unknown(self):
        before = [{"record_id": "one", "group_id": "one", "mae": 0.1}]
        after = [{"record_id": "one", "group_id": "one", "mae": 0.2}]
        result = evaluator.paired(before, after, "mae", higher_is_better=False)
        self.assertEqual(result["status"], "NO_IMPROVEMENT")
        record = {
            **self.records[0],
            "targets": ["attribute.floral"],
            "relevance": {"attribute.floral": 1},
        }
        row = f.evaluate_record(record, self.active, backend, "V2")
        self.assertEqual(row["target_count"], 0)
        self.assertIsNone(row["proxy_initial_direction_in_T"])
        self.assertEqual(f.summarize([row])["proxy_wrong_initial_count"], 0)
        self.assertEqual(f.summarize([row])["records"], 1)

    def test_check_contract_does_not_silently_skip_q3(self):
        with self.assertRaises(ValueError):
            f.run(
                {
                    "contract_version": backend.VERSIONS["contract_version"],
                    "context": {"c0": backend.C0[0], "c1": "medium"},
                    "path": "P2",
                    "policy": "one_step",
                    "answers": [],
                },
                self.active,
            )
        disabled = {**self.active, "foundation_check_enabled": False}
        result = f.run(
            {
                "contract_version": backend.VERSIONS["contract_version"],
                "context": {"c0": backend.C0[0], "c1": "medium"},
                "path": "P2",
                "policy": "fixed",
                "answers": [],
            },
            disabled,
        )
        self.assertEqual(result["state"]["path"], "P2")


if __name__ == "__main__":
    unittest.main()
