"""R5 scientific invariants and actual small-model fit/reload checks."""

import copy
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import train_supervision_r5 as h
import run_supervision_r5 as runner


def example(i=0, target="sensory.apple"):
    return {
        "record_id": str(i),
        "group_id": str(i),
        "initial_selected": ["attribute.fruity"],
        "selected": {
            "ASK": ["attribute.fruity", "sensory.apple"],
            "SKIP": ["attribute.fruity"],
        },
        "full_T": {target: 1},
        "hidden_T": {target: 1},
        "condition_key": "same",
    }


class SupervisionTests(unittest.TestCase):
    def test_no_target_or_identity_features(self):
        row = example()
        other = copy.deepcopy(row)
        other.update(
            full_T={"sensory.bitter": 3},
            hidden_T={},
            record_id="other",
            group_id="other",
        )
        np.testing.assert_array_equal(h.features(row), h.features(other))

    def test_t1_has_identical_allocated_capacity_without_B(self):
        row = example()
        self.assertEqual(h.features(row, "T1").shape, h.features(row, "T2").shape)
        self.assertTrue(np.all(h.features(row, "T1")[1 + len(h.INPUTS) :] == 0))

    def test_duplicate_evidence_once(self):
        row = example()
        other = copy.deepcopy(row)
        other["initial_selected"] *= 3
        other["selected"]["ASK"] *= 4
        np.testing.assert_array_equal(h.features(row), h.features(other))

    def test_missing_reference_is_not_zero_loss(self):
        row = example()
        row.update(full_T={}, hidden_T={})
        self.assertIsNone(h.targets(row))
        self.assertIsNone(h.evaluate(row, h.CANDIDATES)["raw_gap"])

    def test_OOV_reference_retained(self):
        row = example(target="sensory.unregistered")
        self.assertIsNone(h.targets(row))
        self.assertEqual(h.evaluate(row, h.CANDIDATES)["raw_gap"], 1.0)

    def test_group_mass_normalized_across_repetition_and_expansion(self):
        rows = [example(0), example(0), example(1)]
        np.testing.assert_allclose(h.weights(rows), [0.25, 0.25, 0.5])
        self.assertAlmostEqual(sum(h.weights(rows + [example(2)])), 1)

    def test_full_target_keeps_A_overlap(self):
        row = example()
        row["initial_selected"] = ["sensory.apple"]
        row["hidden_T"] = {}
        result = h.evaluate(row, ["sensory.apple"])
        self.assertEqual(result["raw_gap"], 0)
        self.assertEqual(result["direct_exact_contribution"], 1)
        self.assertIsNone(result["hidden_gap"])

    def test_fit_reload_actual_information_and_same_model(self):
        rows = []
        for i in range(8):
            target = "sensory.apple" if i % 2 else "sensory.bitter"
            row = example(i, target)
            row["selected"]["ASK"] = ["attribute.fruity", target]
            rows.append(row)
        a, ab = h.fit(rows, "T1", {}), h.fit(rows, "T2", {})
        self.assertEqual(
            np.asarray(a["coefficients"]).shape, np.asarray(ab["coefficients"]).shape
        )
        reloaded = json.loads(json.dumps(ab))
        self.assertEqual(h.predict(rows[0], ab)[0], h.predict(rows[0], reloaded)[0])
        a_loss = h.aggregate([h.evaluate(r, *h.predict(r, a)) for r in rows])[
            "positive_mention_CE"
        ]
        ab_loss = h.aggregate([h.evaluate(r, *h.predict(r, ab)) for r in rows])[
            "positive_mention_CE"
        ]
        self.assertLess(ab_loss, a_loss)

    def test_mismatch_preserves_target_and_condition(self):
        rows = [example(i) for i in range(3)]
        output, receipt = h.mismatch(rows)
        self.assertEqual(receipt["changed_records"], 3)
        self.assertEqual(
            {r["record_id"] for r in output}, {r["record_id"] for r in rows}
        )
        for row in output:
            self.assertEqual(row["full_T"], rows[int(row["record_id"])]["full_T"])

    def test_paired_alignment_rejects_silent_truncation(self):
        with self.assertRaises(ValueError):
            h.paired([example()], [])

    def test_later_selection_is_direct_not_inferred(self):
        row = example()
        result = h.evaluate(row, ["sensory.apple"])
        self.assertEqual(result["initial_exact_contribution"], 0)
        self.assertEqual(result["later_exact_contribution"], 1)
        self.assertEqual(result["inferred_exact_contribution"], 0)

    def test_replay_rejects_modified_input_before_scoring(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = Path(directory)
            source = owner / "revisions/r5/information_cases.private.json"
            runner.save(source, [example()])
            expected = runner.sha(source)
            runner.save(
                owner / "revisions/r5/training/receipt.private.json",
                {"input_hashes": {source.name: expected}},
            )
            runner.save(source, [])
            with self.assertRaisesRegex(ValueError, "SEALED_INPUT_HASH_CHANGED"):
                runner.replay(owner)


if __name__ == "__main__":
    unittest.main()
