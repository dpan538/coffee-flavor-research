"""Synthetic unit fixtures only; never sensory gold or model evaluation labels."""

import copy, json, sys, unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flavor_sequential as s
import flavor_planning as p
import train_sequential as t


def fixture():
    leaves = [
        ["sensory.apple", "sensory.lemon"],
        ["sensory.jasmine", "sensory.rose"],
        ["sensory.honey", "sensory.caramel"],
        ["sensory.cocoa", "sensory.almond"],
        ["sensory.cinnamon", "sensory.clove"],
        ["sensory.tobacco", "sensory.malt"],
        ["sensory.hay", "sensory.earthy"],
        ["sensory.alcoholic", "sensory.wine_like_character"],
    ]
    rows = []
    for i in range(40):
        targets = sorted(
            set(leaves[i % 8] + leaves[(i + 3) % 8] + ["attribute." + s.ATTRS[i % 8]])
        )
        rows.append(
            {
                "record_id": "unit:" + str(i),
                "group_id": "unit:" + str(i),
                "source_family": "inera",
                "split": "DEVELOPMENT",
                "targets": targets,
                "relevance": dict.fromkeys(targets, 1),
                "attribute_values": [(i * (j + 1) + j) % 10 for j in range(8)],
                "attribute_names": s.ATTRS[:8],
            }
        )
    return rows


class SequentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fixture()
        cls.bundle = t.make_bundle(
            cls.records, "M2_HIER", "unit-fixture-not-real-data", tag="unit"
        )

    def state(self, path="P1"):
        return s.initial_state({"c0": s.C0[0], "c1": "medium"}, self.bundle, path)

    def answer(self, st, selection=None):
        q = p.select_next_question(st, self.bundle)["question"]
        chosen = q["shown_option_ids"][:1] if selection is None else selection
        return {
            k: q[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
        } | {"selected_option_ids": chosen, "state": "SELECTED" if chosen else "UNSURE"}

    def test_all_contexts_and_missing(self):
        for c0 in s.C0:
            for c1 in s.C1:
                self.assertEqual(
                    s.initial_state({"c0": c0, "c1": c1}, self.bundle)["context"],
                    {"c0": c0, "c1": c1},
                )
        for v in [None, "unknown", "unsure", "skip", "", 8]:
            with self.assertRaises(ValueError):
                s.initial_state({"c0": s.C0[0], "c1": v}, self.bundle)
        with self.assertRaises(ValueError):
            s.run({"contract_version": s.VERSIONS["contract_version"]}, self.bundle)

    def test_all_paths_and_q0_q1_and_six_slots(self):
        for path in s.PATHS:
            ep, states, answers = t.trajectory(self.records[0], self.bundle, path)
            slots = [a["slot"] for a in answers]
            self.assertEqual(slots[:2], ["Q0", "Q1"])
            self.assertIn(slots[-1], ["Q4", "Q5"])
            self.assertEqual(len(slots), len(set(slots)))
            self.assertTrue(all(len(a["shown_option_ids"]) <= 4 for a in answers))
            if path == "P4":
                self.assertEqual(slots, list("Q" + str(i) for i in range(6)))
            self.assertEqual(
                s.finalize_result(states[-1], self.bundle)["stage"],
                "PRELIMINARY_RESULT",
            )
            self.assertEqual(
                s.finalize_result(states[-1], self.bundle)["state"][
                    "remaining_question_slots"
                ],
                [],
            )

    def test_same_path_features_scores_reload_and_grouping(self):
        ep, states, answers = t.trajectory(self.records[0], self.bundle)
        payload = {
            "contract_version": s.VERSIONS["contract_version"],
            "context": ep["context"],
            "answers": answers,
        }
        live = s.run(payload, self.bundle)
        offline = s.evaluation_entry(payload, self.bundle)
        reload = s.run(payload, json.loads(json.dumps(self.bundle)))
        self.assertEqual(live, offline)
        self.assertEqual(live, reload)
        self.assertEqual(
            s.encode_features(payload, self.bundle)["features"],
            live["state"]["features"],
        )
        grouped = s.run(dict(payload, answers=[answers[:2], answers[2:]]), self.bundle)
        self.assertEqual(
            grouped["state"]["candidate_scores"], live["state"]["candidate_scores"]
        )

    def test_idempotence_replacement_multiselect(self):
        st = self.state()
        a = self.answer(st)
        one = s.update_joint_state(st, a, self.bundle)
        self.assertEqual(one, s.update_joint_state(one, a, self.bundle))
        changed = dict(a, selected_option_ids=a["shown_option_ids"][1:3])
        replaced = s.update_joint_state(one, changed, self.bundle)
        fresh = s.update_joint_state(st, changed, self.bundle)
        self.assertEqual(replaced["candidate_scores"], fresh["candidate_scores"])
        self.assertEqual(len(replaced["answers_by_question"]), 1)
        self.assertEqual(replaced["interpreted_evidence"]["specific"], [])
        for row in replaced["last_answer_update"]:
            self.assertAlmostEqual(
                row["score_after"] - row["score_before"],
                sum(
                    row[k]
                    for k in [
                        "context_component",
                        "direct_answer_component",
                        "semantic_component",
                        "interaction_component",
                    ]
                ),
            )

    def test_full_broad_nondiscriminating_and_no_child_confirmation(self):
        st = self.state()
        q = p.select_next_question(st, self.bundle)["question"]
        a = self.answer(st, q["shown_option_ids"])
        full = s.update_joint_state(st, a, self.bundle)
        self.assertEqual(full["candidate_scores"], st["candidate_scores"])
        one = s.update_joint_state(st, self.answer(st), self.bundle)
        self.assertFalse(any(r["explicit"] for r in one["candidate_scores"]))
        self.assertNotIn("sensory.jasmine", one["interpreted_evidence"]["specific"])
        self.assertEqual(s.PARENTS["attribute.nutty_cocoa"], ["nutty_cocoa"])

    def test_specific_not_diluted_and_parent_not_counted_twice(self):
        st = self.state()

        # Test the pure evidence encoder with unit-only explicit source instances.
        def inject(slot, axis, opts, selected):
            return {
                "slot": slot,
                "question_id": "unit-" + slot,
                "axis": axis,
                "shown_option_ids": [x["id"] for x in opts],
                "selected_option_ids": selected,
                "state": "SELECTED",
                "options": opts,
            }

        opts = [
            {"id": c, "kind": "specific", "attribute": "fruity"}
            for c in ["sensory.apple", "sensory.lemon"]
        ]
        st["answers_by_question"]["Q2"] = inject(
            "Q2", "refine.fruity", opts, [o["id"] for o in opts]
        )
        enc = s.encode_features(st, self.bundle)
        for c in ["sensory.apple", "sensory.lemon"]:
            self.assertEqual(enc["raw_features"][enc["candidate_ids"].index(c)][1], 1.0)
        before = enc["features"]
        st["answers_by_question"]["Q0"] = inject(
            "Q0",
            "broad.initial0",
            [
                {"id": "attribute.fruity", "kind": "broad", "attribute": "fruity"},
                {"id": "attribute.sweet", "kind": "broad", "attribute": "sweet"},
            ],
            ["attribute.fruity"],
        )
        self.assertEqual(before, s.encode_features(st, self.bundle)["features"])

    def test_no_future_target_or_lab_input(self):
        payload = {
            "contract_version": s.VERSIONS["contract_version"],
            "context": self.state()["context"],
        }
        for key in ["future_answers", "targets", "measurements", "tds"]:
            with self.assertRaises(ValueError):
                s.run(dict(payload, **{key: 123}), self.bundle)
        ep = t.visible_episode(self.records[0])
        q = p.select_next_question(self.state(), self.bundle)["question"]
        answer = t.answer_for(q, ep["visible"], self.bundle)
        self.assertEqual(answer, t.answer_for(q, list(ep["visible"]), self.bundle))
        self.assertFalse(
            s.encode_features(self.state(), self.bundle)["sensory_attribute_state"][
                "measured_attribute_truth_used"
            ]
        )

    def test_statistics_and_cluster_isolation(self):
        train = self.records[:28]
        held = self.records[28:]
        b = t.make_bundle(train, "M2_HIER", "unit")
        self.assertFalse(
            set(b["cluster_model"]["training_groups"]) & {r["group_id"] for r in held}
        )
        self.assertFalse(
            {r["group_id"] for r in b["statistics"]["planning_records"]}
            & {r["group_id"] for r in held}
        )
        with self.assertRaises(AssertionError):
            t.statistics([dict(train[0], split="HISTORICAL_REGRESSION")])
        bad = copy.deepcopy(b)
        bad["semantic_version"] = "old"
        with self.assertRaises(ValueError):
            s.run(
                {
                    "contract_version": s.VERSIONS["contract_version"],
                    "context": self.state()["context"],
                },
                bad,
            )

    def test_final_comparison_once_exposure_subset_terminal(self):
        ep, states, answers = t.trajectory(self.records[0], self.bundle)
        st = states[-1]
        pre = s.finalize_result(st, self.bundle)
        ex = pre["exposure"]["candidate_ids"]
        chosen = ex[2:4]
        for mode in ["F1", "F2"]:
            end = s.apply_final_comparison(
                st,
                ex,
                chosen,
                self.bundle,
                feedback_source="SIMULATED",
                generation_version=self.bundle["bundle_id"],
                mode=mode,
            )
            final = s.finalize_result(end, self.bundle)
            self.assertEqual(final["stage"], "FINAL_RESULT")
            self.assertEqual(final["next"]["action"], "FINAL_RESULT")
            self.assertTrue(
                set(chosen)
                <= {r["candidate_id"] for r in final["main"] + final["secondary"]}
            )
            with self.assertRaises(ValueError):
                s.update_joint_state(end, answers[0], self.bundle)
            with self.assertRaises(ValueError):
                s.apply_final_comparison(
                    end,
                    ex,
                    chosen,
                    self.bundle,
                    feedback_source="SIMULATED",
                    generation_version=self.bundle["bundle_id"],
                )
        f1 = s.apply_final_comparison(
            st,
            ex,
            chosen,
            self.bundle,
            feedback_source="SIMULATED",
            generation_version=self.bundle["bundle_id"],
            mode="F1",
        )
        self.assertEqual(
            [
                r["candidate_id"]
                for r in f1["candidate_scores"]
                if r["candidate_id"] not in chosen
            ],
            [
                r["candidate_id"]
                for r in st["candidate_scores"]
                if r["candidate_id"] not in chosen
            ],
        )
        for exposed, selected in [
            (list(reversed(ex)), chosen),
            (ex, ["not-exposed"]),
            (ex, [None]),
        ]:
            with self.assertRaises(ValueError):
                s.apply_final_comparison(
                    st,
                    exposed,
                    selected,
                    self.bundle,
                    feedback_source="SIMULATED",
                    generation_version=self.bundle["bundle_id"],
                )

    def test_q3_cannot_be_duplicate_question_or_q6(self):
        ep, states, answers = t.trajectory(self.records[0], self.bundle)
        st = states[-1]
        self.assertEqual(st, s.update_joint_state(st, answers[3], self.bundle))
        with self.assertRaises(ValueError):
            s.update_joint_state(st, dict(answers[3], slot="Q6"), self.bundle)
        with self.assertRaises(ValueError):
            s.update_joint_state(self.state(), answers[3], self.bundle)

    def test_conditional_paths_and_planner_cannot_see_future_answers(self):
        for path in ["P2", "P3", "P4"]:
            for policy in ["one_step", "two_step"]:
                ep, states, answers = t.trajectory(
                    self.records[0], self.bundle, path, policy
                )
                slots = [a["slot"] for a in answers]
                self.assertIn(slots[-1], ["Q4", "Q5"])
                self.assertEqual(slots.count("Q3"), int("Q3" in slots))
                current = states[2]
                q = p.select_next_question(current, self.bundle)
                polluted = copy.deepcopy(current)
                polluted["future_targets"] = ["sensory.clove"]
                polluted["future_answers"] = ["not observed"]
                self.assertEqual(q, p.select_next_question(polluted, self.bundle))

    def test_low_support_soft_conditioning_does_not_discard_history(self):
        st = self.state()
        a = self.answer(st)
        after = s.update_joint_state(st, a, self.bundle)
        w0 = p.soft_weights(st, self.bundle)
        w1 = p.soft_weights(after, self.bundle)
        self.assertAlmostEqual(w1.sum(), 1.0)
        self.assertTrue(np.all(w1 > 0))
        self.assertFalse(np.allclose(w0, w1))

    def test_full_legal_multiselect_keeps_evidence_when_output_budget_is_full(self):
        state = self.state("P4")
        while True:
            q = p.select_next_question(state, self.bundle)
            if q["action"] != "ASK":
                break
            answer = self.answer(state, q["question"]["shown_option_ids"])
            state = s.update_joint_state(state, answer, self.bundle)
        result = s.finalize_result(state, self.bundle)
        self.assertEqual(len(state["answers_by_question"]), 6)
        self.assertGreaterEqual(len(state["interpreted_evidence"]["specific"]), 8)
        self.assertEqual(len(result["main"]) + len(result["secondary"]), 8)
        self.assertEqual(
            result["explicit_overflow"],
            max(0, len(state["interpreted_evidence"]["specific"]) - 8),
        )


if __name__ == "__main__":
    unittest.main()
