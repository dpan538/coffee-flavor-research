"""Synthetic mechanism fixtures are never independent sensory evaluations."""

import copy, json, sys, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flavor_m2_r1 as s
import train_m2_r1 as t
import flavor_sequential as legacy_s
import train_sequential as legacy_t
from test_flavor_sequential import fixture


class R1MechanismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = fixture()
        cls.old = legacy_t.make_bundle(cls.records, "M2_JOINT", "unit")
        cls.bundle = t.make_bundle(
            cls.records, manifest_hash="unit", bank_override=cls.old["question_bank"]
        )

    def initial(self):
        return s.initial_state({"c0": s.C0[0], "c1": "medium"}, self.bundle)

    def answer(self, state, chosen=None, status=None):
        q = s.select_next_question(state, self.bundle)["question"]
        chosen = q["shown_option_ids"][:1] if chosen is None else chosen
        return {
            k: q[k] for k in ["slot", "question_id", "axis", "shown_option_ids"]
        } | {
            "selected_option_ids": chosen,
            "state": status or ("SELECTED" if chosen else "UNSURE"),
        }

    def inject(self, state, slot, concepts, kind="specific", attr="fruity"):
        opts = [{"id": c, "kind": kind, "attribute": attr} for c in concepts]
        state["answers_by_question"][slot] = {
            "slot": slot,
            "axis": ("broad." if kind == "broad" else "refine.") + slot,
            "question_id": "synthetic:" + slot,
            "options": opts,
            "shown_option_ids": concepts,
            "selected_option_ids": concepts,
            "state": "SELECTED",
        }

    def test_legacy_failure_and_fixed_positive_broad(self):
        result = t.mechanism_checks(self.old, self.bundle)
        self.assertGreater(
            result["broad_support"]["old_negative_child_contribution_count"], 0
        )
        self.assertEqual(
            result["broad_support"]["r1_negative_child_contribution_count"], 0
        )
        self.assertGreater(
            result["exposure_and_none"][1][
                "explicit_none_candidates_with_negative_score_delta"
            ],
            0,
        )
        state = self.initial()
        selected = s.update_joint_state(state, self.answer(state), self.bundle)
        for row in selected["candidate_scores"]:
            if row["support_state"] == "BROADLY_COMPATIBLE_NOT_CONFIRMED":
                self.assertFalse(row["specific_confirmation_eligible"])
                self.assertFalse(row["explicit"])

    def test_all_shown_local_options_keep_support(self):
        state = self.initial()
        ids = s.select_next_question(state, self.bundle)["question"]["shown_option_ids"]
        after = s.update_joint_state(state, self.answer(state, ids), self.bundle)
        self.assertEqual(len(after["interpreted_evidence"]["broad"]), len(ids))
        self.assertNotEqual(after["features"], state["features"])
        self.assertFalse(
            after["interpreted_evidence"]["exposure_scopes"][0][
                "complete_registered_range"
            ]
        )

    def test_idempotence_replacement_batches_and_none_scope(self):
        initial = self.initial()
        answer = self.answer(initial)
        state = s.update_joint_state(initial, answer, self.bundle)
        self.assertEqual(state, s.update_joint_state(state, answer, self.bundle))
        changed = dict(answer, selected_option_ids=answer["shown_option_ids"][1:3])
        replaced = s.update_joint_state(state, changed, self.bundle)
        fresh = s.update_joint_state(initial, changed, self.bundle)
        self.assertEqual(replaced["candidate_scores"], fresh["candidate_scores"])
        for status in ["UNSURE", "SKIP"]:
            empty = s.update_joint_state(
                initial, dict(answer, state=status, selected_option_ids=[]), self.bundle
            )
            self.assertEqual(empty["features"], initial["features"])
        no = s.update_joint_state(
            initial,
            dict(answer, state="NONE_OF_THESE", selected_option_ids=[]),
            self.bundle,
        )
        rejected = set(no["interpreted_evidence"]["negative_broad"])
        for before, after in zip(
            sorted(initial["candidate_scores"], key=lambda r: r["candidate_id"]),
            sorted(no["candidate_scores"], key=lambda r: r["candidate_id"]),
        ):
            if (
                not set(
                    self.bundle["candidate_attributes"].get(after["candidate_id"], [])
                )
                & rejected
            ):
                self.assertEqual(before["score"], after["score"])
        ep, states, answers = t.trajectory(self.records[0], self.bundle)
        payload = {
            "contract_version": s.VERSIONS["contract_version"],
            "context": ep["context"],
            "answers": answers,
        }
        flat = s.run(payload, self.bundle)
        grouped = s.run(dict(payload, answers=[answers[:2], answers[2:]]), self.bundle)
        self.assertEqual(flat, grouped)

    def test_direct_multiselect_parent_and_repeated_concept_do_not_duplicate(self):
        state = self.initial()
        self.inject(state, "Q2", ["sensory.apple", "sensory.lemon"])
        encoded = s.encode_features(state, self.bundle)
        for c in ["sensory.apple", "sensory.lemon"]:
            self.assertEqual(
                encoded["raw_features"][encoded["candidate_ids"].index(c)][1], 1
            )
        self.inject(state, "Q0", ["attribute.fruity"], "broad")
        self.assertEqual(
            encoded["features"], s.encode_features(state, self.bundle)["features"]
        )
        self.inject(state, "Q3", ["sensory.apple"])
        self.assertEqual(
            encoded["features"], s.encode_features(state, self.bundle)["features"]
        )
        relations = s.evidence(state, self.bundle)["relations"]
        self.assertEqual(len(relations), len({r["evidence_id"] for r in relations}))

    def test_add_and_joint_do_not_fit_nmf(self):
        rows = [
            {
                k: v
                for k, v in r.items()
                if k not in {"attribute_values", "attribute_names"}
            }
            | {"source_family": "positive_only"}
            for r in self.records
        ]
        with patch.object(
            legacy_t, "clusters", side_effect=AssertionError("NMF forbidden")
        ):
            for kind in ["M2_R1_FIXED", "M2_R1_ADD"]:
                bundle = t.make_bundle(
                    rows, kind, "unit", bank_override=self.old["question_bank"]
                )
                self.assertEqual(bundle["cluster_dimension"], 0)
                s.initial_state({"c0": s.C0[0], "c1": "medium"}, bundle)
        with self.assertRaises(ValueError):
            legacy_t.make_bundle(rows, "M2_JOINT", "unit")

    def test_versioned_reload_live_evaluation_and_final_once(self):
        ep, states, answers = t.trajectory(self.records[0], self.bundle)
        payload = {
            "contract_version": s.VERSIONS["contract_version"],
            "context": ep["context"],
            "answers": answers,
        }
        live = s.run(payload, self.bundle)
        self.assertEqual(live, s.evaluation_entry(payload, self.bundle))
        self.assertEqual(live, s.run(payload, json.loads(json.dumps(self.bundle))))
        self.assertEqual(
            s.encode_features(payload, self.bundle)["features"],
            live["state"]["features"],
        )
        with self.assertRaises(ValueError):
            s.check_bundle(self.old)
        with self.assertRaises(ValueError):
            legacy_s.check_bundle(self.bundle)
        ex = live["exposure"]["candidate_ids"]
        end = s.apply_final_comparison(
            live["state"],
            ex,
            ex[:1],
            self.bundle,
            feedback_source="SIMULATED",
            generation_version=self.bundle["bundle_id"],
        )
        self.assertEqual(s.finalize_result(end, self.bundle)["stage"], "FINAL_RESULT")
        with self.assertRaises(ValueError):
            s.update_joint_state(end, answers[0], self.bundle)
        with self.assertRaises(ValueError):
            s.apply_final_comparison(
                end,
                ex,
                [],
                self.bundle,
                feedback_source="SIMULATED",
                generation_version=self.bundle["bundle_id"],
            )

    def test_feedback_repeat_is_no_new_score_evidence(self):
        ep, states, answers = t.trajectory(self.records[0], self.bundle)
        pre = s.finalize_result(states[-1], self.bundle)
        ex = pre["exposure"]["candidate_ids"]
        chosen = [
            c for c in ex if c in pre["state"]["interpreted_evidence"]["specific"]
        ]
        self.assertTrue(chosen)
        end = s.apply_final_comparison(
            pre["state"],
            ex,
            chosen,
            self.bundle,
            feedback_source="SIMULATED",
            generation_version=self.bundle["bundle_id"],
        )
        self.assertEqual(pre["state"]["features"], end["features"])
        self.assertEqual(
            [r["score"] for r in pre["state"]["candidate_scores"]],
            [r["score"] for r in end["candidate_scores"]],
        )

    def test_layer_masks_never_make_unmentioned_leaves_negative(self):
        state = self.initial()
        record = self.records[0]
        ep = t.visible_episode(record)
        masks = t.supervision_targets(record, ep, state, self.bundle)
        leaf_indices = [
            i
            for i, c in enumerate(self.bundle["candidate_vocabulary"])
            if c.startswith("sensory.")
        ]
        self.assertEqual(masks["leaf"]["mask"].sum(), 0)
        self.assertTrue(np.all(masks["attr"]["mask"][leaf_indices] == 0))
        self.assertEqual(
            int(
                (
                    (masks["recovery"]["values"] == 0) & (masks["recovery"]["mask"] > 0)
                ).sum()
            ),
            0,
        )
        structured = dict(
            record,
            source_family="inera",
            supervision="SOURCE_NATIVE_STRUCTURED_MENTION_FREQUENCIES",
            attribute_names=["fruity", "floral"],
            attribute_values=[0, 9],
            targets=["attribute.floral"],
            relevance={"attribute.floral": 1},
        )
        mask = t.supervision_targets(
            structured, t.visible_episode(structured), state, self.bundle
        )
        for name in ["leaf", "recovery"]:
            self.assertTrue(np.all(mask[name]["mask"][leaf_indices] == 0))
        self.assertEqual(
            mask["attr"]["mask"][
                self.bundle["candidate_vocabulary"].index("attribute.fruity")
            ],
            1,
        )
        self.assertEqual(
            mask["attr"]["values"][
                self.bundle["candidate_vocabulary"].index("attribute.fruity")
            ],
            0,
        )

    def test_q01_fitted_from_training_only_and_complementary(self):
        train = self.records[:32]
        bundle = t.make_bundle(train, manifest_hash="unit")
        audit = bundle["question_bank"]["initial_pair_selection"]
        self.assertFalse(
            set(audit["training_groups"]) & {r["group_id"] for r in self.records[32:]}
        )
        chosen = audit["selected"]
        self.assertGreater(chosen["q1_conditional_entropy_given_q0_bits"], 0)
        self.assertEqual(len(chosen["q0_attributes"]), 4)
        self.assertEqual(len(chosen["q1_attributes"]), 4)
        self.assertFalse(set(chosen["q0_attributes"]) & set(chosen["q1_attributes"]))

    def test_train_oof_masks_and_fitted_monotonic_weights(self):
        bundle, receipt = t.fit(
            self.records,
            "unit",
            bank_override=self.old["question_bank"],
            loss_mode="layered",
        )
        for split in receipt["inner_feature_audit"]:
            self.assertFalse(
                set(split["feature_training_groups"])
                & set(split["feature_output_groups"])
            )
            self.assertTrue(split["question_bank_scope"].startswith("INNER_TRAIN_ONLY"))
        weights = dict(zip(s.FEATURES, bundle["model_parameters"]["weights"]))
        self.assertGreaterEqual(weights["broad_related_support"], 0)
        self.assertEqual(weights["exposed_rejection"], -1)
        self.assertEqual(receipt["mask_counts"]["leaf"]["observed_zero_cells"], 0)
        self.assertEqual(receipt["mask_counts"]["recovery"]["observed_zero_cells"], 0)
        self.assertEqual(
            t.mechanism_checks(self.old, bundle)["broad_support"][
                "r1_negative_child_contribution_count"
            ],
            0,
        )

    def test_conditional_recovery_is_same_level_and_preserves_positive_masks(self):
        bundle, receipt = t.fit(
            self.records,
            "unit",
            C=0.01,
            bank_override=self.old["question_bank"],
            loss_mode="layered_conditional",
        )
        self.assertEqual(receipt["loss_mode"], "layered_conditional")
        self.assertEqual(
            receipt["conditional_recovery_levels"][0]["candidate_count"],
            sum(c.startswith("sensory.") for c in bundle["candidate_vocabulary"]),
        )
        self.assertEqual(receipt["mask_counts"]["leaf"]["observed_zero_cells"], 0)
        self.assertEqual(receipt["mask_counts"]["recovery"]["observed_zero_cells"], 0)
        self.assertIn("NOT_SENSORY_PRESENCE", receipt["recovery_statistical_object"])
        t.evaluate_record(self.records[0], bundle)

    def test_complete_vs_local_classification_is_explicit_metadata(self):
        # Nine registered attributes exceed the ordinary four-option budget;
        # this encoder-only fixture checks the scope definition, not a new path.
        state = self.initial()
        opts = [
            {"id": "attribute." + a, "kind": "broad", "attribute": a} for a in s.ATTRS
        ]
        state["answers_by_question"]["Q0"] = {
            "slot": "Q0",
            "question_id": "unit:complete",
            "axis": "broad.complete",
            "options": opts,
            "shown_option_ids": [o["id"] for o in opts],
            "selected_option_ids": [o["id"] for o in opts],
            "state": "SELECTED",
            "classification_scope": "COMPLETE_REGISTERED_ATTRIBUTE_RANGE",
        }
        evidence = s.evidence(state, self.bundle)
        self.assertTrue(evidence["exposure_scopes"][0]["complete_registered_range"])
        self.assertEqual(
            evidence["exposure_scopes"][0]["interpretation"],
            "NONDISCRIMINATING_WITHIN_COMPLETE_RANGE",
        )
        self.assertEqual(set(evidence["broad"]), set(s.ATTRS))
        self.assertEqual(evidence["specific"], [])


if __name__ == "__main__":
    unittest.main()
