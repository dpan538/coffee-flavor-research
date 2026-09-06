"""Engineering interventions only; these fixtures are never sensory labels."""

import copy
import json
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flavor_conditioning_r4 as s
import train_m2_r1 as training
from test_flavor_sequential import fixture


def fixture_expert():
    records = fixture()
    stats = training.statistics(records)
    attrs = {c: s.r1.PARENTS.get(c, []) for c in stats["vocabulary"]}
    return training.make_bundle(
        records,
        manifest_hash="engineering-fixture-only",
        bank_override=training.legacy.make_bank(stats, attrs),
        canonical_broad_feedback=True,
    )


def weighted_bundle(expert):
    return s.make_bundle(
        expert,
        model_parameters={
            "feature_names": s.FEATURES,
            "weights": [0.7] * len(s.FEATURES),
            "mean": [0.0] * len(s.FEATURES),
            "scale": [1.0] * len(s.FEATURES),
        },
        selected_variant="AKR",
    )


def semantic_fixture(expert, concepts):
    """Prevalidated-semantic-state fixture, not a fake product exposure."""
    base = s.r1.initial_state({"c0": s.r1.C0[0], "c1": "medium"}, expert)
    for slot, selected in zip(["Q0", "Q1", "Q2"], concepts):
        options = [
            {
                "id": c,
                "kind": "broad" if c.startswith("attribute.") else "specific",
                "attribute": c.split(".", 1)[1] if c.startswith("attribute.") else None,
            }
            for c in selected
        ]
        base["answers_by_question"][slot] = {
            "slot": slot,
            "question_id": "ENGINEERING:" + slot,
            "axis": "fixture-semantic-axis-" + slot,
            "shown_option_ids": list(selected),
            "selected_option_ids": list(selected),
            "state": "SELECTED",
            "options": options,
        }
    return base


def actual_answer(state, bundle, selection=None):
    question = s.select_next_question(state, bundle)["question"]
    chosen = question["shown_option_ids"][:1] if selection is None else selection
    return {
        k: question[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
    } | {"selected_option_ids": chosen, "state": "SELECTED" if chosen else "UNSURE"}


def comparison_core(state):
    return {k: state[k] for k in ["candidate_scores", "k1", "conditioning_trace"]}


class ConditioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expert = fixture_expert()
        cls.bundle = weighted_bundle(cls.expert)
        cls.base = semantic_fixture(cls.expert, [["sensory.apple"], ["sensory.almond"]])

    def initial(self, variant="AKR", policy="ALWAYS_ASK"):
        return s.initial_state(
            {"c0": s.r1.C0[0], "c1": "medium"}, self.bundle, variant, policy
        )

    def test_01_new_direction_changes_k1_and_defined_components(self):
        before = s.score(
            semantic_fixture(self.expert, [["sensory.apple"]]), self.bundle, "AKR"
        )
        after = s.score(self.base, self.bundle, "AKR")
        self.assertEqual(
            before["encoded"]["k1"]["dimensions"]["nutty_cocoa"]["supported"], 0
        )
        self.assertEqual(
            after["encoded"]["k1"]["dimensions"]["nutty_cocoa"]["supported"], 1
        )
        self.assertTrue(
            any(r["relation_delta"] != 0 for r in after["candidate_scores"])
        )
        self.assertNotEqual(
            before["encoded"]["raw_features"], after["encoded"]["raw_features"]
        )

    def test_02_unrelated_k1_dimension_has_no_unrelated_candidate_effect(self):
        encoded = s.features(self.base, self.bundle, "AKR")
        k1 = copy.deepcopy(encoded["k1"])
        k1["dimensions"]["floral"]["supported"] = 1.0
        altered = s.features(self.base, self.bundle, "AKR", k1_override=k1)
        i = encoded["candidate_ids"].index("sensory.lemon")
        self.assertEqual(encoded["features"][i], altered["features"][i])

    def test_03_k1_off_removes_numeric_component(self):
        on = s.score(self.base, self.bundle, "AKR")
        off = s.score(self.base, self.bundle, "AR")
        self.assertTrue(any(row["k1_delta"] != 0 for row in on["candidate_scores"]))
        self.assertTrue(all(row["k1_delta"] == 0 for row in off["candidate_scores"]))
        self.assertEqual(on["encoded"]["k1"], off["encoded"]["k1"])

    def test_04_relation_off_still_executes_numeric_k1(self):
        result = s.score(self.base, self.bundle, "AK")
        self.assertTrue(result["encoded"]["k1"]["computed_before_candidate_scoring"])
        self.assertTrue(any(row["k1_delta"] != 0 for row in result["candidate_scores"]))
        self.assertTrue(
            all(row["relation_delta"] == 0 for row in result["candidate_scores"])
        )

    def test_05_shuffled_k1_is_detected_as_negative_diagnostic(self):
        native = s.score(self.base, self.bundle, "AKR")
        other = semantic_fixture(self.expert, [["sensory.jasmine"], ["sensory.honey"]])
        shuffled = s.build_k1(s.normalize(other, self.bundle), self.bundle)
        altered = s.score(self.base, self.bundle, "AKR", k1_override=shuffled)
        native_map = {
            r["candidate_id"]: r["k1_delta"] for r in native["candidate_scores"]
        }
        altered_map = {
            r["candidate_id"]: r["k1_delta"] for r in altered["candidate_scores"]
        }
        self.assertNotEqual(native_map, altered_map)
        self.assertTrue(altered["encoded"]["diagnostic_k1_override"])

    def test_06_exact_replay_is_idempotent(self):
        start = self.initial()
        answer = actual_answer(start, self.bundle)
        state = s.update_state(start, answer, self.bundle)
        self.assertEqual(state, s.update_state(state, answer, self.bundle))

    def test_07_batch_grouping_core_parity(self):
        state, answers = self.initial(), []
        for _ in range(3):
            answer = actual_answer(state, self.bundle)
            answers.append(answer)
            state = s.update_state(state, answer, self.bundle)
        payload = {
            "contract_version": s.VERSION,
            "context": state["base_state"]["context"],
            "variant": "AKR",
            "trigger_policy": "ALWAYS_ASK",
            "answers": answers,
        }
        flat = s.run(payload, self.bundle)
        payload["answers"] = [answers[:1], answers[1:]]
        grouped = s.run(payload, self.bundle)
        self.assertEqual(flat, grouped)
        self.assertEqual(
            s.live_features(state, self.bundle),
            s.live_features(grouped["state"], self.bundle),
        )

    def test_08_replacement_removes_old_effect_without_accumulation(self):
        initial = self.initial()
        first = actual_answer(initial, self.bundle)
        state = s.update_state(initial, first, self.bundle)
        replacement = dict(first, selected_option_ids=first["shown_option_ids"][1:2])
        replaced = s.update_state(state, replacement, self.bundle)
        fresh = s.update_state(initial, replacement, self.bundle)
        self.assertEqual(comparison_core(replaced), comparison_core(fresh))
        self.assertEqual(
            s.live_features(replaced, self.bundle), s.live_features(fresh, self.bundle)
        )

    def test_k1_projection_cannot_read_poisoned_scores_or_targets(self):
        poison = copy.deepcopy(self.base)
        poison.update(
            candidate_scores=[{"candidate_id": "POISON", "score": 1e9}],
            targets=["POISON"],
            hidden_targets=["POISON"],
            future_answers=["POISON"],
            source_family="POISON",
        )
        self.assertEqual(
            s.normalize(self.base, self.bundle), s.normalize(poison, self.bundle)
        )
        self.assertEqual(
            s.build_k1(s.normalize(self.base, self.bundle), self.bundle),
            s.build_k1(s.normalize(poison, self.bundle), self.bundle),
        )

    def test_shared_pair_generalizes_over_complete_exposure_tuple(self):
        changed = copy.deepcopy(self.base)
        answer = changed["answers_by_question"]["Q0"]
        answer["question_id"] = "ENGINEERING:NEW_EXPOSURE"
        answer["shown_option_ids"].append("sensory.honey")
        answer["options"].append(
            {"id": "sensory.honey", "kind": "specific", "attribute": None}
        )
        a, b = s.features(self.base, self.bundle, "AKR"), s.features(
            changed, self.bundle, "AKR"
        )
        self.assertEqual(a["features"], b["features"])
        self.assertNotEqual(
            a["normalized_evidence"]["exposure_scopes"],
            b["normalized_evidence"]["exposure_scopes"],
        )

    def test_parent_child_and_repeated_concept_do_not_create_pair(self):
        for concepts in [
            [["attribute.fruity"], ["sensory.apple"]],
            [["sensory.apple"], ["sensory.apple"]],
        ]:
            result = s.features(
                semantic_fixture(self.expert, concepts), self.bundle, "AKR"
            )
            self.assertEqual(result["positive_pairs"], [])
        compound = semantic_fixture(self.expert, [["sensory.wine_like_character"]])
        self.assertEqual(
            s.normalize(compound, self.bundle)["concepts"][0]["concept_id"],
            "sensory.wine_like_character",
        )

    def test_direct_protection_and_a0_exact_base_preservation(self):
        for variant in s.VARIANTS:
            result = s.score(self.base, self.bundle, variant)
            for row in result["candidate_scores"]:
                if (
                    row["explicit"]
                    or variant == "A0"
                    or not row["candidate_id"].startswith("sensory.")
                ):
                    self.assertEqual(row["conditioning_delta"], 0)
                    self.assertEqual(row["score"], row["base_score"])
        base = s.r1.rank_candidates(self.base, self.expert)
        r4 = s.score(self.base, self.bundle, "A0")["candidate_scores"]
        self.assertEqual(
            [(r["candidate_id"], r["score"]) for r in base],
            [(r["candidate_id"], r["score"]) for r in r4],
        )

    def test_unknown_neutral_explicit_rejection_gate_never_prunes(self):
        empty = s.features(self.initial()["base_state"], self.bundle, "AKR")
        self.assertTrue(all(d["unknown"] for d in empty["k1"]["dimensions"].values()))
        self.assertFalse(np.asarray(empty["features"]).any())
        self.assertTrue(all(g == 1 for g in empty["relation_gates"]))
        rejected = copy.deepcopy(self.base)
        rejected["answers_by_question"]["Q2"] = semantic_fixture(
            self.expert, [["attribute.fruity"]]
        )["answers_by_question"]["Q0"] | {
            "slot": "Q2",
            "selected_option_ids": [],
            "state": "NONE_OF_THESE",
        }
        result = s.features(rejected, self.bundle, "AKR")
        i = result["candidate_ids"].index("sensory.lemon")
        self.assertEqual(result["relation_gates"][i], 0)
        self.assertTrue(result["legal_mask"][i])
        self.assertTrue(all(v == 0 for v in result["features"][i][4:]))

    def test_masked_normalization_extreme_scores_and_no_legal_candidate(self):
        result = s.masked_normalize([10000, 9999, 1e100], [True, True, False])
        self.assertAlmostEqual(sum(result["weights"]), 1)
        self.assertIsNone(result["log_weights"][-1])
        self.assertEqual(result["weights"][-1], 0)
        self.assertTrue(
            s.masked_normalize([1, 2], [False, False])["status"].startswith("NO_LEGAL")
        )
        parameters = copy.deepcopy(self.bundle["model_parameters"])
        parameters["mean"][0] = 0.1
        with self.assertRaises(ValueError):
            s.make_bundle(self.expert, parameters)

    def test_legal_skip_once_final_reload_and_train_live_matrix(self):
        start = self.initial(policy="ALWAYS_SKIP")
        state = start
        for _ in range(3):
            state = s.update_state(
                state, actual_answer(state, self.bundle), self.bundle
            )
        self.assertEqual(
            s.select_next_question(state, self.bundle)["question"]["slot"], "Q4"
        )
        self.assertNotIn("Q3", state["base_state"]["answers_by_question"])
        self.assertIsNone(s.finalize_result(state, self.bundle)["exposure"])
        state = s.update_state(state, actual_answer(state, self.bundle), self.bundle)
        result = s.finalize_result(state, self.bundle)
        self.assertLessEqual(len(result["main"]), 5)
        self.assertLessEqual(len(result["secondary"]), 3)
        selected = [
            c
            for c in result["exposure"]["candidate_ids"]
            if c in state["k1"]["confirmed_concepts"]
        ]
        feedback = {
            "generation_version": self.bundle["bundle_id"],
            "exposed_candidates": result["exposure"]["candidate_ids"],
            "selected_candidates": selected,
            "feedback_source": "SIMULATED",
        }
        final = s.apply_final_comparison(state, feedback, self.bundle)
        self.assertEqual(
            [
                (r["candidate_id"], r["score"], r["conditioning_delta"])
                for r in state["candidate_scores"]
            ],
            [
                (r["candidate_id"], r["score"], r["conditioning_delta"])
                for r in final["candidate_scores"]
            ],
        )
        self.assertEqual(s.finalize_result(final, self.bundle)["stage"], "FINAL_RESULT")
        self.assertEqual(
            s.select_next_question(final, self.bundle)["action"], "FINAL_RESULT"
        )
        with self.assertRaises(ValueError):
            s.apply_final_comparison(final, feedback, self.bundle)
        with self.assertRaises(ValueError):
            s.update_state(final, actual_answer(start, self.bundle), self.bundle)
        reloaded = json.loads(json.dumps(self.bundle))
        self.assertEqual(
            s.finalize_result(final, self.bundle), s.finalize_result(final, reloaded)
        )
        encoded = s.features(state, self.bundle, "AKR")
        deltas = np.asarray(encoded["features"]) @ np.asarray(
            self.bundle["model_parameters"]["weights"]
        )
        by_id = {r["candidate_id"]: r for r in state["candidate_scores"]}
        for c, delta in zip(encoded["candidate_ids"], deltas):
            self.assertEqual(delta, by_id[c]["conditioning_delta"])

    def test_c0_c1_strict_and_hidden_input_rejected(self):
        self.assertEqual(len(s.r1.C0), 8)
        self.assertEqual(len(s.r1.C1), 7)
        for value in [None, "unknown", "", "skip"]:
            with self.assertRaises(ValueError):
                s.initial_state({"c0": s.r1.C0[0], "c1": value}, self.bundle)
        with self.assertRaises(ValueError):
            s.run(
                {
                    "contract_version": s.VERSION,
                    "context": {"c0": s.r1.C0[0], "c1": "medium"},
                    "hidden_targets": [],
                },
                self.bundle,
            )


def engineering_diagnostics():
    """Public-safe checkpoint; no source records or fitted weights are emitted."""
    names = [
        name
        for name in unittest.defaultTestLoader.getTestCaseNames(ConditioningTests)
        if name.startswith("test_0")
    ]
    result = unittest.TestResult()
    unittest.TestSuite(ConditioningTests(name) for name in names).run(result)
    bad = {test._testMethodName for test, _ in result.failures + result.errors}
    return {
        "status": "PASS" if result.wasSuccessful() else "FAIL",
        "diagnostics": {name[8:]: "FAIL" if name in bad else "PASS" for name in names},
        "passed": result.testsRun - len(bad),
        "total": len(names),
        "scope": "SYNTHETIC_ENGINEERING_INTERVENTIONS_NOT_SENSORY_VALIDATION",
        "actual_r4_fits_performed": 0,
        "feature_count": len(s.FEATURES),
        "feature_protocol_sha256": s.r1.digest(s.protocol()),
    }


if __name__ == "__main__":
    if "--diagnostics" in sys.argv:
        print(json.dumps(engineering_diagnostics(), sort_keys=True))
    else:
        unittest.main()
