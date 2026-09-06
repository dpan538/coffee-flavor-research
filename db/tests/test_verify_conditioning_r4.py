"""Bounded no-fit verifier regression; fixture records are engineering-only."""

import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_conditioning_r4 as verify
import flavor_conditioning_r4 as r4
import flavor_constraints_r3 as r3
from test_conditioning_r4 import fixture_expert, weighted_bundle
from test_flavor_sequential import fixture


class ExecutionVerificationTests(unittest.TestCase):
    def test_recomputed_a0_prefixes_and_actual_cli_once_final(self):
        expert = fixture_expert()
        old = r3.make_bundle(expert)
        a0 = r4.make_bundle(expert)
        details = verify.compare_a0_record(fixture()[0], old, a0)
        self.assertEqual(len(details["prefixes"]), 6)
        self.assertEqual(details["prefixes"][-1]["slot"], "Q4")
        weighted = weighted_bundle(expert)
        payload = verify.new_legal_payload(weighted)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "fixture.model.json"
            verify.save_private(path, weighted)
            result = verify.execute_payload(path, payload, root / "cli")
            self.assertTrue(result["public_summary"]["ordinary_multi_select_present"])
            self.assertTrue(
                result["public_summary"]["hashseed_complete_output_identical"]
            )
            self.assertEqual(result["public_summary"]["actual_cli_processes"], 4)
            self.assertEqual(result["final"]["stage"], "FINAL_RESULT")
            private_mode = path.stat().st_mode & 0o777
            self.assertEqual(private_mode, 0o600)
            bad = copy.deepcopy(result["final"])
            bad["state"]["base_state"]["answers_by_question"].pop("Q4")
            with self.assertRaises(ValueError):
                verify._check_output(bad, terminal=True)


if __name__ == "__main__":
    unittest.main()
