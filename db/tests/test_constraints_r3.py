"""Executable contracts and isolated fitting fixtures, not sensory labels."""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flavor_constraints_r3 as s
import train_constraints_r3 as t
import train_m2_r1 as r1t
from test_flavor_sequential import fixture


class ConstraintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fixture()
        stats = r1t.statistics(cls.records)
        attrs = {c: s.r1.PARENTS.get(c, []) for c in stats["vocabulary"]}
        cls.expert = r1t.make_bundle(
            cls.records,
            manifest_hash="fixture",
            bank_override=r1t.legacy.make_bank(stats, attrs),
            canonical_broad_feedback=True,
        )
        cls.bundle = s.make_bundle(cls.expert, contract_hash="fixture")

    def initial(self, policy="ALWAYS_ASK"):
        return s.initial_state(
            {"c0": s.r1.C0[0], "c1": "medium"}, self.bundle, "E1", policy
        )

    def answer(self, state, none=False):
        q = s.select_next_question(state, self.bundle)["question"]
        return {
            k: q[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
        } | {
            "selected_option_ids": [] if none else q["shown_option_ids"][:1],
            "state": "NONE_OF_THESE" if none else "SELECTED",
        }

    def test_e1_preserves_full_raw_r1_competence(self):
        state = self.initial()
        for _ in range(3):
            state = s.update_state(state, self.answer(state), self.bundle)
            raw = s.r1.rank_candidates(state["base_state"], self.expert)
            self.assertEqual(
                [(r["candidate_id"], r["score"]) for r in raw],
                [(r["candidate_id"], r["score"]) for r in state["candidate_scores"]],
            )
            self.assertTrue(
                all(r["relation_delta"] == 0 for r in state["candidate_scores"])
            )

    def test_replacement_replay_and_canonical_k1(self):
        start = self.initial()
        answer = self.answer(start)
        state = s.update_state(start, answer, self.bundle)
        self.assertEqual(state, s.update_state(state, answer, self.bundle))
        replacement = dict(answer, selected_option_ids=answer["shown_option_ids"][1:2])
        replaced = s.update_state(state, replacement, self.bundle)
        fresh = s.update_state(start, replacement, self.bundle)
        self.assertEqual(replaced["candidate_scores"], fresh["candidate_scores"])
        self.assertTrue(any(k["status"] == "REVISED" for k in replaced["k1"]))
        self.assertTrue(all(not k["hard_deleted_candidates"] for k in replaced["k1"]))
        payload = {
            "contract_version": s.VERSION,
            "context": start["base_state"]["context"],
            "variant": "E1",
            "trigger_policy": "ALWAYS_ASK",
            "answers": [[replacement], [replacement]],
        }
        self.assertEqual(
            s.run(payload, self.bundle)["state"]["candidate_scores"],
            fresh["candidate_scores"],
        )

    def test_skip_q3_requires_q4_and_no_fake_answer(self):
        state = self.initial("LEARNED")
        for _ in range(3):
            state = s.update_state(state, self.answer(state), self.bundle)
        self.assertEqual(state["q2_decision"]["action"], "SKIP")
        self.assertNotIn("Q3", state["base_state"]["answers_by_question"])
        self.assertEqual(
            s.select_next_question(state, self.bundle)["question"]["slot"], "Q4"
        )
        self.assertIsNone(s.finalize_result(state, self.bundle)["exposure"])
        state = s.update_state(state, self.answer(state), self.bundle)
        self.assertEqual(
            s.finalize_result(state, self.bundle)["stage"], "PRELIMINARY_RESULT"
        )

    def test_final_exposure_once_limits_reload_and_f2_repeat(self):
        episode, states, answers = t.trajectory(self.records[0], self.bundle)
        pre = s.finalize_result(states[-1], self.bundle)
        self.assertLessEqual(len(pre["main"]), 5)
        self.assertLessEqual(len(pre["secondary"]), 3)
        direct = set(pre["state"]["base_state"]["interpreted_evidence"]["confirmed"])
        selected = [c for c in pre["exposure"]["candidate_ids"] if c in direct]
        feedback = {
            "exposed_candidates": pre["exposure"]["candidate_ids"],
            "selected_candidates": selected,
            "feedback_source": "SIMULATED",
            "generation_version": self.bundle["bundle_id"],
        }
        after = s.apply_final_comparison(pre["state"], feedback, self.bundle)
        self.assertEqual(
            [(r["candidate_id"], r["score"]) for r in pre["state"]["candidate_scores"]],
            [(r["candidate_id"], r["score"]) for r in after["candidate_scores"]],
        )
        self.assertEqual(s.finalize_result(after, self.bundle)["stage"], "FINAL_RESULT")
        with self.assertRaises(ValueError):
            s.apply_final_comparison(after, feedback, self.bundle)
        with self.assertRaises(ValueError):
            s.update_state(after, answers[0], self.bundle)
        restored = json.loads(json.dumps(self.bundle))
        self.assertEqual(
            s.finalize_result(after, restored), s.finalize_result(after, self.bundle)
        )

    def test_sparse_term_ids_semantic_not_ephemeral_and_no_none_term(self):
        state = self.initial()
        for _ in range(2):
            state = s.update_state(state, self.answer(state), self.bundle)
        terms = s.available_terms(state["base_state"])
        renamed = copy.deepcopy(state["base_state"])
        for answer in renamed["answers_by_question"].values():
            answer["question_id"] = "new-ephemeral-instance"
        self.assertEqual(terms, s.available_terms(renamed))
        renamed["answers_by_question"]["Q0"]["state"] = "NONE_OF_THESE"
        renamed["answers_by_question"]["Q0"]["selected_option_ids"] = []
        self.assertEqual(s.available_terms(renamed), [])

    def test_explicit_delta_zero_and_fit_live_shared_path(self):
        state = self.initial()
        rows = s.r1.rank_candidates(state["base_state"], self.expert)
        rows[0]["explicit"] = True
        term = {
            "term_id": "fixture",
            "coefficients": {r["candidate_id"]: 100.0 for r in rows},
        }
        scored = s.rank_from_base_rows(rows, [term])
        direct = next(r for r in scored if r["candidate_id"] == rows[0]["candidate_id"])
        self.assertEqual(direct["relation_delta"], 0.0)
        self.assertTrue(any(r["relation_delta"] == 100 for r in scored))

    def test_trigger_ties_retained_and_group_leak_rejected(self):
        rows = [
            {
                "group_id": f"g{i}",
                "record_id": f"r{i}",
                "features": dict.fromkeys(s.FEATURES, 0.0),
                "gain": 0.0,
                "relation_training_groups": [f"g{1-i}"],
            }
            for i in range(2)
        ]
        fitted = t.fit_trigger_a(rows, {"g0", "g1"}, {"held"})
        self.assertEqual(fitted["tied_rows"], 2)
        self.assertEqual(fitted["labelled_groups"], 2)
        self.assertEqual(s.trigger_prediction(rows[0]["features"], fitted), 0)
        rows[0]["relation_training_groups"].append("g0")
        with self.assertRaisesRegex(ValueError, "OOF_ISOLATION"):
            t.fit_trigger_a(rows, {"g0", "g1"})

    def test_context_and_parameter_freeze(self):
        with self.assertRaises(ValueError):
            s.initial_state({"c0": s.r1.C0[0], "c1": "unsure"}, self.bundle)
        mutated = copy.deepcopy(self.bundle)
        mutated["trigger_a"]["intercept"] = 1.0
        with self.assertRaisesRegex(ValueError, "PARAMETERS_CHANGED"):
            s.update_state(self.initial(), self.answer(self.initial()), mutated)

    def test_p1_amendment_preserves_each_train_axis_and_isolation(self):
        stats = r1t.statistics(self.records)
        attrs = {c: s.r1.PARENTS.get(c, []) for c in stats["vocabulary"]}
        self.assertEqual(
            t.train_qualified_p1_bank(stats, attrs), r1t.legacy.make_bank(stats, attrs)
        )
        arrays = t.p1_internal_training_arrays(self.records, self.expert, "fixture")
        for audit in arrays[3]:
            self.assertFalse(
                set(audit["feature_training_groups"])
                & set(audit["feature_output_groups"])
            )
            self.assertEqual(audit["feature_path"], "P1")
            self.assertGreaterEqual(audit["qualified_correction_axes"], 3)


if __name__ == "__main__":
    unittest.main()
