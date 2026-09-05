"""Executable backend invariants and governed semantic regression counterexamples."""

import copy, importlib.util, json, math, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))
import flavor_backend as b
from jsonschema import Draft202012Validator


def fixture():
    vocab = [
        "sensory.apple",
        "sensory.orange",
        "sensory.jasmine",
        "sensory.rose",
        "sensory.cocoa",
        "sensory.dark_chocolate",
        "sensory.almond",
        "sensory.caramel",
        "sensory.honey",
        "sensory.bitter",
        "sensory.wine_like_character",
    ]
    return {
        "bundle_id": "TEST_ONLY_SYNTHETIC_NOT_TRAINING",
        "vocabulary": vocab,
        "priors": {c: -i / 20 for i, c in enumerate(vocab)},
        "conditional": {},
        "context_adjustments": {"c1:dark": {c: 100 for c in vocab}},
        "evidence_by_candidate": {c: ["fixture:source"] for c in vocab},
        "candidate_rights": {c: "ADMITTED_SOURCE_CONDITIONS_SATISFIED" for c in vocab},
        "train_records": [
            {
                "group_id": str(i),
                "targets": (
                    ["sensory.apple", "sensory.jasmine"]
                    if i < 3
                    else ["sensory.cocoa", "sensory.almond"]
                ),
            }
            for i in range(6)
        ],
        "model_weights": {
            c: {"observed:sensory.cocoa": 1 if c == "sensory.dark_chocolate" else 0}
            for c in vocab
        },
        "model_intercepts": {c: -i / 20 for i, c in enumerate(vocab)},
        "fit_id": "SYNTHETIC_TEST_WEIGHTS_NOT_A_MODEL_RESULT",
    }


def answer(bundle, qid, selected, state="SELECTED"):
    q = next(
        q for q in b.question_bank(bundle["vocabulary"]) if q["question_id"] == qid
    )
    return {
        "question_id": qid,
        "shown_option_ids": [o["option_id"] for o in q["options"]],
        "selected_option_ids": selected,
        "state": state,
    }


def old_claims(rows):
    spec = importlib.util.spec_from_file_location(
        "historical_inference", ROOT / "db/scripts/generate-product-inference-v0.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.read_tsv = lambda _: rows
    return m.build_structured_claims()[0]


class Backend(unittest.TestCase):
    def setUp(self):
        self.bundle = fixture()
        self.context = {"c0": b.C0[0], "c1": "medium"}

    def state(self, model="B2"):
        return b.build_candidate_state(self.context, self.bundle, model)

    def test_context_all_56_legal_combinations_and_no_default(self):
        for c0 in b.C0:
            for c1 in b.C1:
                self.assertEqual(
                    b.validate_context({"c0": c0, "c1": c1}), {"c0": c0, "c1": c1}
                )
        for c1 in [None, "unknown", "unsure", "", 0, [], {}, "skip", "Medium roast"]:
            with self.assertRaises(ValueError):
                b.validate_context({"c0": b.C0[0], "c1": c1})
        for x in [
            {},
            {"c0": b.C0[0]},
            {"c1": "medium"},
            None,
            [],
            {"c0": "espresso", "c1": "dark"},
        ]:
            with self.assertRaises(ValueError):
                b.validate_context(x)

    def test_new_json_changes_live_rank_and_contract(self):
        contract = json.loads(
            (ROOT / "db/data/backend-model-20260905/backend_contract.json").read_text()
        )
        a = answer(self.bundle, "q.nut_cocoa", ["sensory.cocoa", "sensory.almond"])
        payload = {"context": self.context, "answers": [a]}
        result = b.run(payload, self.bundle)
        for key, value in [
            ("Request", payload),
            ("Response", result),
            ("InterpretedAnswer", b.interpret_answer(a, self.bundle)),
        ]:
            Draft202012Validator(
                {"$ref": "#/$defs/" + key, "$defs": contract["$defs"]}
            ).validate(value)
        self.assertNotEqual(
            self.state()["candidates"], result["candidate_state"]["candidates"]
        )
        self.assertEqual(len(result["final_result"]["main"]), 5)
        self.assertEqual(len(result["final_result"]["secondary"]), 3)
        self.assertEqual(
            len(
                {
                    r["candidate_id"]
                    for r in result["final_result"]["main"]
                    + result["final_result"]["secondary"]
                }
            ),
            8,
        )

    def test_multi_select_bounded_not_conflicting_unselected_neutral(self):
        a = answer(self.bundle, "q.nut_cocoa", ["sensory.cocoa", "sensory.almond"])
        s = b.update_candidate_state(self.state(), a, self.bundle)
        self.assertAlmostEqual(
            sum(r["direct_answer_component"] for r in s["candidates"]), 3
        )
        self.assertEqual(
            next(
                r
                for r in s["candidates"]
                if r["candidate_id"] == "sensory.dark_chocolate"
            )["direct_answer_component"],
            0,
        )

    def test_retry_is_exactly_idempotent_correction_replaces_and_is_order_invariant(
        self,
    ):
        a = answer(self.bundle, "q.nut_cocoa", ["sensory.cocoa", "sensory.almond"])
        s = b.update_candidate_state(self.state(), a, self.bundle)
        reverse = copy.deepcopy(a)
        reverse["shown_option_ids"].reverse()
        reverse["selected_option_ids"].reverse()
        self.assertEqual(s, b.update_candidate_state(s, reverse, self.bundle))
        corrected = answer(self.bundle, "q.nut_cocoa", ["sensory.dark_chocolate"])
        updated = b.update_candidate_state(s, corrected, self.bundle)
        fresh = b.update_candidate_state(self.state(), corrected, self.bundle)
        self.assertEqual(updated["candidates"], fresh["candidates"])
        self.assertEqual(len(updated["answers"]), 1)
        self.assertTrue(
            updated["updates"][-1][0]["update_reason"].startswith("REPLACE")
        )

    def test_trace_has_consistent_components_and_shared_evidence(self):
        a = answer(self.bundle, "q.direction", ["family.floral"])
        s = b.update_candidate_state(self.state(), a, self.bundle)
        rel = b.interpret_answer(a, self.bundle)["relations"]
        self.assertEqual(len({r["evidence_id"] for r in rel}), 1)
        for r in s["updates"][-1]:
            self.assertAlmostEqual(
                r["score_after"],
                sum(
                    r[k]
                    for k in [
                        "base_component",
                        "context_component",
                        "direct_answer_component",
                        "semantic_component",
                        "interaction_component",
                    ]
                ),
            )
            self.assertEqual(r["context_component"], 0)

    def test_floral_is_weak_direction_not_jasmine_confirmation(self):
        a = answer(self.bundle, "q.direction", ["family.floral"])
        s = b.update_candidate_state(self.state(), a, self.bundle)
        j = next(r for r in s["candidates"] if r["candidate_id"] == "sensory.jasmine")
        self.assertEqual(j["direct_answer_component"], 0)
        self.assertFalse(j["directly_expressed"])
        self.assertLessEqual(j["semantic_component"], 0.625)

    def test_cocoa_does_not_confirm_dark_chocolate(self):
        a = answer(self.bundle, "q.nut_cocoa", ["sensory.cocoa"])
        s = b.update_candidate_state(self.state(), a, self.bundle)
        c = next(
            r for r in s["candidates"] if r["candidate_id"] == "sensory.dark_chocolate"
        )
        self.assertEqual(c["direct_answer_component"], 0)
        self.assertFalse(c["directly_expressed"])

    def test_all_broad_options_do_not_raise_certainty_or_scores(self):
        a = answer(self.bundle, "q.direction", [])
        a["selected_option_ids"] = a["shown_option_ids"][:]
        for model in ["B2", "M1"]:
            initial = self.state(model)
            after = b.update_candidate_state(initial, a, self.bundle)
            self.assertEqual(
                [r["score"] for r in initial["candidates"]],
                [r["score"] for r in after["candidates"]],
            )

    def test_native_combined_category_not_automatically_split(self):
        a = answer(self.bundle, "q.nut_cocoa", ["Nutty/Cocoa"])
        with self.assertRaises(ValueError):
            b.interpret_answer(a, self.bundle)
        claim = {
            "evidence_id": "row1",
            "artifact_id": "x",
            "subject_id": "Nutty/Cocoa",
            "object_id": "sensory.dark_chocolate",
            "relation_type": "COMPOUND",
            "support": 1,
            "role": "CORE_PROFESSIONAL",
        }
        r = b.interpret_semantic_evidence(
            [claim],
            {
                "x": {
                    "use_basis": "NONCOMMERCIAL_RESEARCH_USE",
                    "conditions_satisfied": True,
                }
            },
        )["accepted"][0]
        self.assertFalse(r["confirms_candidate"])
        self.assertEqual(r["bounded_support"], 0)

    def test_source_permission_does_not_propagate_and_paths_deduplicate(self):
        c = {
            "evidence_id": "observation1",
            "artifact_id": "allowed",
            "subject_id": "coffee1",
            "object_id": "sensory.cocoa",
            "relation_type": "DIRECT_OBSERVATION",
            "support": 1,
            "role": "CORE_PROFESSIONAL",
        }
        p = {
            "allowed": {
                "use_basis": "NONCOMMERCIAL_RESEARCH_USE",
                "conditions_satisfied": True,
            },
            "pending": {
                "use_basis": "NONCOMMERCIAL_RESEARCH_USE",
                "conditions_satisfied": False,
            },
        }
        r = b.interpret_semantic_evidence(
            [
                c,
                dict(c, method="alternate semantic path"),
                dict(c, artifact_id="pending"),
                dict(c, artifact_id="other"),
            ],
            p,
        )
        self.assertEqual(len(r["accepted"]), 1)
        self.assertEqual(len(r["withheld"]), 2)
        self.assertEqual(r["accepted"][0]["bounded_support"], 1)

    def test_cooccurrence_modifier_and_weak_evidence_not_equivalence(self):
        for kind in ["COOCCURRENCE", "MODIFIER", "COMPOUND"]:
            c = {
                "evidence_id": "e",
                "artifact_id": "a",
                "subject_id": "sensory.cocoa",
                "object_id": "sensory.dark_chocolate",
                "relation_type": kind,
                "support": 1,
                "role": "CORE_PROFESSIONAL",
            }
            r = b.interpret_semantic_evidence(
                [c],
                {
                    "a": {
                        "use_basis": "NONCOMMERCIAL_RESEARCH_USE",
                        "conditions_satisfied": True,
                    }
                },
            )["accepted"][0]
            self.assertFalse(r["confirms_candidate"])
            self.assertEqual(r["bounded_support"], 0)

    def test_method_keywords_are_not_observations_legacy_regression(self):
        row = {
            "review_status": "REVIEWED",
            "evidence_direction": "SUPPORTS",
            "target_entity_key": "instrument.calibration",
            "method": "floral cocoa keywords in method",
            "support_count": "1",
            "source_family_key": "fixture",
        }
        old = old_claims([row])
        self.assertEqual(old["sensory.jasmine"], 1)
        self.assertEqual(old["sensory.dark_chocolate"], 1)
        with self.assertRaises(ValueError):
            b.interpret_semantic_evidence([row], {})

    def test_bitter_is_not_fermented_child(self):
        q = next(
            q
            for q in b.question_bank(self.bundle["vocabulary"])
            if q["question_id"] == "q.fermented"
        )
        self.assertNotIn("sensory.bitter", [o["option_id"] for o in q["options"]])

    def test_question_requires_supported_material_outcomes_and_stops(self):
        nxt = b.select_next_question(self.state(), self.bundle)
        self.assertEqual(nxt["action"], "ASK")
        self.assertGreater(nxt["estimated_gain_bits"], 0)
        same = copy.deepcopy(self.bundle)
        same["train_records"] = [
            {"group_id": str(i), "targets": ["sensory.apple"]} for i in range(6)
        ]
        self.assertEqual(b.select_next_question(self.state(), same)["action"], "STOP")
        insufficient = copy.deepcopy(self.bundle)
        insufficient["train_records"] = self.bundle["train_records"][::3]
        self.assertEqual(
            b.select_next_question(self.state(), insufficient)["action"], "STOP"
        )
        s = self.state()
        for q in b.question_bank(self.bundle["vocabulary"])[:5]:
            s = b.update_candidate_state(
                s, answer(self.bundle, q["question_id"], [], "UNSURE"), self.bundle
            )
        self.assertEqual(
            b.select_next_question(s, self.bundle)["reason"], "QUESTION_BUDGET"
        )

    def test_invalid_options_states_and_wrong_bundle_rejected(self):
        good = answer(self.bundle, "q.fruit", ["sensory.apple"])
        for change in [
            {"question_id": []},
            {"state": []},
            {"shown_option_ids": []},
            {"selected_option_ids": ["sensory.apple", "sensory.apple"]},
            {"selected_option_ids": ["sensory.cocoa"]},
            {"state": "UNSURE"},
        ]:
            with self.assertRaises(ValueError):
                b.interpret_answer(dict(good, **change), self.bundle)
        with self.assertRaises(ValueError):
            b.run({"context": self.context, "model": []}, self.bundle)
        s = self.state()
        s["bundle_id"] = "other"
        with self.assertRaises(ValueError):
            b.update_candidate_state(s, good, self.bundle)

    def test_c1_remains_required_but_unreviewed_context_effect_masked(self):
        a = b.run({"context": self.context}, self.bundle)
        c = b.run({"context": dict(self.context, c1="dark")}, self.bundle)
        self.assertEqual(
            a["candidate_state"]["candidates"], c["candidate_state"]["candidates"]
        )


if __name__ == "__main__":
    unittest.main()
