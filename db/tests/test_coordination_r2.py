"""R2 coordination mechanism/isolation tests; fixtures are not sensory labels."""

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flavor_coordination_r2 as s
import train_coordination_r2 as t
import train_m2_r1 as r1t
from test_flavor_sequential import fixture


class CoordinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fixture()
        stats = r1t.statistics(cls.records)
        attrs = {c: s.r1.PARENTS.get(c, []) for c in stats["vocabulary"]}
        cls.expert = r1t.make_bundle(
            cls.records,
            manifest_hash="unit",
            bank_override=r1t.legacy.make_bank(stats, attrs),
            canonical_broad_feedback=True,
        )
        cls.bundle = s.make_bundle(cls.expert, s.default_router(), "unit-contract")

    def answer(self, state, selected=None, status="SELECTED"):
        q = s.r1.select_next_question(state["base_state"], self.expert)["question"]
        return {
            k: q[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
        } | {
            "selected_option_ids": (
                q["shown_option_ids"][:1] if selected is None else selected
            ),
            "state": status,
        }

    def initial(self):
        return s.initial_state({"c0": s.r1.C0[0], "c1": "medium"}, self.bundle)

    def test_rank_percentiles_ties_and_single_semantics(self):
        np.testing.assert_allclose(
            s.midrank_percentile([1, 1, 2]), [1 / 3, 1 / 3, 5 / 6]
        )
        start = self.initial()
        q = s.r1.select_next_question(start["base_state"], self.expert)["question"]
        all_broad = s.update_state(
            start, self.answer(start, q["shown_option_ids"]), self.bundle
        )
        before = start["expert_predictions"]
        after = all_broad["expert_predictions"]
        # Broad evidence is isolated from both residual experts and applied once.
        self.assertEqual(
            before["rank_percentile_scores"], after["rank_percentile_scores"]
        )
        self.assertTrue(any(value == 0.25 for value in after["shared_semantic_scores"]))
        self.assertEqual(max(after["shared_semantic_scores"]), 0.25)
        for row in all_broad["candidate_scores"]:
            self.assertFalse(row["specific_confirmation_eligible"])

    def test_duplicate_replacement_batch_and_model_freeze(self):
        initial = self.initial()
        answer = self.answer(initial)
        state = s.update_state(initial, answer, self.bundle)
        self.assertEqual(state, s.update_state(state, answer, self.bundle))
        changed = dict(answer, selected_option_ids=answer["shown_option_ids"][1:3])
        replaced = s.update_state(state, changed, self.bundle)
        fresh = s.update_state(initial, changed, self.bundle)
        self.assertEqual(replaced["candidate_scores"], fresh["candidate_scores"])
        payload = {
            "contract_version": s.VERSION,
            "context": initial["base_state"]["context"],
            "answers": [[changed], [changed]],
        }
        self.assertEqual(
            s.run(payload, self.bundle)["state"]["candidate_scores"],
            fresh["candidate_scores"],
        )
        mutated = copy.deepcopy(self.bundle)
        mutated["router"]["global_alpha"] = 0.25
        with self.assertRaisesRegex(ValueError, "PARAMETERS_CHANGED"):
            s.rank_candidates(fresh["base_state"], mutated)

    def test_none_is_exposure_local_and_not_duplicate_negative(self):
        initial = self.initial()
        answer = self.answer(initial, [], "NONE_OF_THESE")
        state = s.update_state(initial, answer, self.bundle)
        predictions = state["expert_predictions"]
        self.assertEqual(
            predictions["rank_percentile_scores"],
            initial["expert_predictions"]["rank_percentile_scores"],
        )
        for value, rejected in zip(
            predictions["shared_semantic_scores"], predictions["rejected"]
        ):
            self.assertEqual(value, -1.0 if rejected else 0.0)
        self.assertEqual(state, s.update_state(state, answer, self.bundle))

    def test_actual_final_exposure_once_repeated_evidence_and_reload(self):
        episode, states, answers = r1t.trajectory(
            self.records[0], self.expert, "P1", "fixed"
        )
        state = s.wrap_state(states[-1], self.bundle, "G3")
        pre = s.finalize_result(state, self.bundle)
        direct = set(pre["state"]["base_state"]["interpreted_evidence"]["confirmed"])
        selected = [c for c in pre["exposure"]["candidate_ids"] if c in direct]
        feedback = {
            "exposed_candidates": pre["exposure"]["candidate_ids"],
            "selected_candidates": selected,
            "feedback_source": "SIMULATED",
            "generation_version": self.bundle["bundle_id"],
        }
        after = s.apply_final_comparison(pre["state"], feedback, self.bundle)
        self.assertEqual(pre["state"]["candidate_scores"], after["candidate_scores"])
        self.assertEqual(pre["state"]["routing_weights"], after["routing_weights"])
        with self.assertRaisesRegex(ValueError, "ALREADY_USED"):
            s.apply_final_comparison(after, feedback, self.bundle)
        with self.assertRaisesRegex(ValueError, "TERMINAL"):
            s.update_state(after, answers[-1], self.bundle)
        payload = {
            "contract_version": s.VERSION,
            "context": episode["context"],
            "answers": answers,
            "final_comparison": feedback,
        }
        live = s.run(payload, self.bundle)
        reload = s.evaluation_entry(payload, json.loads(json.dumps(self.bundle)))
        self.assertEqual(live, reload)
        self.assertEqual(live["stage"], "FINAL_RESULT")

    def test_live_feature_whitelist_cannot_read_targets_or_source(self):
        state = self.initial()["base_state"]
        original = s.rank_candidates(state, self.bundle)
        changed = dict(
            state,
            source_family="label-leak",
            coffee_id="test",
            hidden_targets=["sensory.apple"],
            measured_lab_values=[999],
        )
        self.assertEqual(original, s.rank_candidates(changed, self.bundle))
        bad = dict(original["routing_features"], source_family=1)
        with self.assertRaisesRegex(ValueError, "WHITELIST"):
            s.route_from_features(bad, "INITIAL", self.bundle["router"], "G3")

    def synthetic_oof(self):
        base = self.initial()
        predictions = copy.deepcopy(base["expert_predictions"])
        candidates = predictions["candidate_ids"]
        rows = []
        for index in range(8):
            group = f"unit:{index}"
            training_groups = [f"unit:{j}" for j in range(8) if j % 2 != index % 2]
            for stage in s.STAGES:
                features = dict(base["routing_features"])
                features["explicit_specific_count"] = index % 2
                rows.append(
                    {
                        "group_id": group,
                        "record_id": group,
                        "path": "P1",
                        "stage": stage,
                        "episode": {
                            "visible": [],
                            "hidden": [candidates[index % len(candidates)]],
                        },
                        "predictions": predictions,
                        "live_features": features,
                        "out_of_group_verified": True,
                        "expert_training_groups": training_groups,
                        "expert_training_groups_sha256": s.r1.digest(training_groups),
                    }
                )
        return rows

    def test_router_train_outer_and_inner_group_isolation_and_zero_unseen_feature(self):
        rows = self.synthetic_oof()
        groups = {row["group_id"] for row in rows}
        router = t.fit_router(rows, groups, ["outer:held"])
        self.assertEqual(router["fit_status"], "FITTED_FROM_NESTED_INNER_EXPERT_OOF")
        self.assertEqual(
            router["advantage_coefficients"][s.FEATURES.index("novel_final_feedback")],
            0,
        )
        self.assertEqual(router["stage_shrinkage"]["INITIAL"], 8 / 58)
        with self.assertRaisesRegex(ValueError, "SCOPE"):
            t.fit_router(rows, groups, [rows[0]["group_id"]])
        bad = copy.deepcopy(rows)
        bad[0]["expert_training_groups"].append(bad[0]["group_id"])
        with self.assertRaisesRegex(ValueError, "PROVENANCE_LEAK"):
            t.fit_router(bad, groups)
        bad = copy.deepcopy(rows)
        bad[0]["live_features"]["oracle_expert_id"] = 1
        with self.assertRaisesRegex(ValueError, "CANNOT_USE"):
            t.fit_router(bad, groups)

    def test_equal_group_record_path_stage_weights(self):
        rows = self.synthetic_oof()
        duplicated = rows + [dict(rows[0]) for _ in range(20)]
        w = t.hierarchical_row_weights(duplicated)
        for group in {r["group_id"] for r in duplicated}:
            self.assertAlmostEqual(
                sum(
                    weight
                    for row, weight in zip(duplicated, w)
                    if row["group_id"] == group
                ),
                1,
            )


if __name__ == "__main__":
    unittest.main()
