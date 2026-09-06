import unittest
from unittest.mock import patch
import candidate_c01_r7 as c


class CandidateTests(unittest.TestCase):
    def test_model_identity_not_linear_head(self):
        with self.assertRaisesRegex(ValueError, "IDENTITY"):
            c.check({"model_kind": "M2_R6_LINEAR"})

    def test_production_context_required(self):
        with patch.object(c, "check"):
            for context in [None, {}, {"c0": c.C0[0]}, {"c0": c.C0[0], "c1": None}]:
                with self.assertRaises((ValueError, TypeError)):
                    c.initial(context, {}, "PRODUCTION")

    def test_neutral_mode_does_not_accept_pretend_observation(self):
        with patch.object(c, "check"):
            with self.assertRaisesRegex(ValueError, "MISSING_SOURCE"):
                c.initial({"c0": c.C0[0], "c1": "medium"}, {}, c.OFFLINE)

    def test_confirmation_group_exclusion(self):
        package = {"scorer_training_groups": ["known"], "coverage_training_groups": []}
        with self.assertRaisesRegex(ValueError, "PREVIOUSLY_USED"):
            c.offline_case({"group_id": "known"}, package)

    def test_unknown_request_fields_block_source_targets(self):
        with patch.object(c, "check"):
            with self.assertRaisesRegex(ValueError, "SCHEMA"):
                c.run({"contract_version": c.VERSION, "A": [], "B": [], "T": []}, {})

    def test_eval_universe_fixed(self):
        self.assertEqual(len(c.EVALUATION_CANDIDATES), 56)
        self.assertEqual(len(set(c.EVALUATION_CANDIDATES)), 56)

    def test_infer_cannot_use_offline_context_escape(self):
        with patch.object(c, "check"):
            with self.assertRaisesRegex(ValueError, "INFER_REQUIRES"):
                c.run({"contract_version": c.VERSION, "execution_mode": c.OFFLINE}, {})

    def test_capacity_failure_retains_targets(self):
        package = {
            "scorer_training_groups": [],
            "coverage_training_groups": [],
            "runtime_bundle": {},
        }
        record = {
            "record_id": "new",
            "group_id": "new",
            "relevance_full": {"sensory.apple": 1},
            "relevance_unexpressed": {"sensory.apple": 1},
        }
        with patch.object(c, "initial", return_value={}), patch.object(
            c, "select", side_effect=ValueError("NO_LEGAL_AXIS_AT_FROZEN_BUDGET:Q0")
        ), patch.object(c.runtime, "finalize_result", return_value={}), patch.object(
            c.acquisition.previous, "selected", return_value=[]
        ):
            row = c.offline_case(record, package)
        self.assertEqual(row["ranking"], [])
        self.assertEqual(row["full_T"], record["relevance_full"])
        self.assertEqual(row["ordinary_options"], 0)
        self.assertEqual(row["status"], "CAPACITY_FAILURE")


if __name__ == "__main__":
    unittest.main()
