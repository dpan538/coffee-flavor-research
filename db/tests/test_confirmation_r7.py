import sys
from pathlib import Path
import unittest
import json
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import confirmation_r7 as c


class Tests(unittest.TestCase):
    def row(self):
        return dict(
            record_id="r",
            group_id="new",
            sample_id="s",
            A=["sensory.apple"],
            B=["sensory.cocoa"],
            relevance_full={"sensory.apple": 1, "sensory.unmapped_source_term": 1},
            A_observation_unit_id="a",
            B_observation_unit_id="b",
            T_observation_unit_ids=["t"],
        )

    def test_concept_overlap_allowed_oov_preserved(self):
        r = self.row()
        self.assertEqual(c.validate_records([r], set())["nonempty_fixed_T"], 1)
        self.assertIn("sensory.unmapped_source_term", r["relevance_full"])

    def test_invalid_ids_and_conflicting_sample_group_rejected(self):
        r = self.row()
        r["sample_id"] = ""
        with self.assertRaisesRegex(ValueError, "IDENTITIES"):
            c.validate_records([r], set())
        r = self.row()
        s = {
            **r,
            "record_id": "r2",
            "group_id": "g2",
            "A_observation_unit_id": "a2",
            "B_observation_unit_id": "b2",
            "T_observation_unit_ids": ["t2"],
        }
        with self.assertRaisesRegex(ValueError, "SAMPLE_GROUP"):
            c.validate_records([r, s], set())
        r = self.row()
        r["relevance_full"] = {"sensory.apple": True}
        with self.assertRaisesRegex(ValueError, "TARGET"):
            c.validate_records([r], set())

    def test_source_role_collision_rejected(self):
        r = self.row()
        r["T_observation_unit_ids"] = ["a"]
        with self.assertRaisesRegex(ValueError, "DISJOINT"):
            c.validate_records([r], set())

    def test_existing_group_rejected(self):
        with self.assertRaisesRegex(ValueError, "PREVIOUSLY"):
            c.validate_records([self.row()], {"new"})

    def test_cross_record_observation_reuse_rejected(self):
        r = self.row()
        s = {**r, "record_id": "r2", "group_id": "g2", "sample_id": "s2"}
        with self.assertRaisesRegex(ValueError, "REUSE"):
            c.validate_records([r, s], set())

    def test_empty_T_retained_and_nonsensory_target_not_silently_ignored(self):
        r = self.row()
        r["relevance_full"] = {}
        self.assertEqual(c.validate_records([r], set())["records"], 1)
        r["relevance_full"] = {"quality.overall": 8}
        with self.assertRaisesRegex(ValueError, "TARGET"):
            c.validate_records([r], set())

    def test_freeze_evaluate_replay_preserves_targets_and_never_mutates_bundle(self):
        # Synthetic runtime boundary test, not a new coffee confirmation result.
        import candidate_c01_r7 as candidate

        with tempfile.TemporaryDirectory() as directory:
            owner = Path(directory)
            records_path, admission_path, bundle_path = [
                owner / name
                for name in ["records.json", "admission.json", "bundle.json"]
            ]
            row = self.row()
            records_path.write_text(json.dumps([row]))
            (owner / "recovery_records.json").write_text("[]")
            bundle_path.write_text("{}")
            bundle = {
                "scorer_training_groups": ["old"],
                "coverage_training_groups": ["old"],
                "generation_candidate_universe": ["sensory.apple"],
                "fixed_evaluation_candidate_universe": c.metrics.CANDIDATES,
            }
            admission = dict.fromkeys(
                [
                    "identity_verified",
                    "license_verified",
                    "observation_roles_verified",
                    "previous_use_checked",
                    "fixed_base_mapping_applied",
                ],
                True,
            )
            admission.update(
                source_id="synthetic-engineering",
                role="NEW_FIXED_CONFIRMATION",
                records_sha256=c.io.sha(records_path),
                measurement_scope="SYNTHETIC_UNIT_TEST_ONLY",
                identity_audit_evidence="synthetic fixture",
                license_evidence="synthetic fixture",
            )
            admission_path.write_text(json.dumps(admission))

            def offline(record, frozen, policy):
                self.assertEqual(frozen, bundle)
                self.assertEqual(record["relevance_full"], row["relevance_full"])
                self.assertEqual(
                    record["relevance_unexpressed"], {"sensory.unmapped_source_term": 1}
                )
                return {
                    "record_id": record["record_id"],
                    "group_id": record["group_id"],
                    "state": {"base_state": {"answers_by_question": {}}},
                    "ranking": [{"candidate_id": "sensory.apple"}],
                    "selected": [],
                    "full_T": record["relevance_full"],
                    "hidden_T": record["relevance_unexpressed"],
                    "ordinary_questions": 5,
                    "ordinary_options": 19,
                    "actual_final_exposure": 0,
                }

            with patch.object(
                candidate, "load_bundle", return_value=bundle
            ), patch.object(candidate, "offline_case", side_effect=offline):
                frozen = c.freeze_cohort(
                    owner, records_path, admission_path, bundle_path
                )
                contract = (
                    owner
                    / "revisions/r7/confirmation/synthetic-engineering/frozen_cohort.private.json"
                )
                self.assertEqual(frozen["fixed_targets"]["r"], row["relevance_full"])
                result = c.evaluate_cohort(owner, contract)
                self.assertEqual(result["comparison"]["delta_right_minus_left"], 0)
                self.assertEqual(
                    result["generation_target_coverage"][
                        "record_targets_outside_generation"
                    ],
                    1,
                )
                self.assertEqual(result["C00"]["raw_gap"], 0.5)
                self.assertEqual(
                    c.evaluate_cohort(owner, contract, replay=True)["status"],
                    "EXACT_SEALED_REPLAY",
                )
                records_path.write_text("[]")
                with self.assertRaisesRegex(ValueError, "INPUT_CHANGED"):
                    c.evaluate_cohort(owner, contract, replay=True)


if __name__ == "__main__":
    unittest.main()
