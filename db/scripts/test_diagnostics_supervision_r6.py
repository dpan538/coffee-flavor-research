import unittest
from diagnostics_supervision_r6 import aligned


class IdentityTests(unittest.TestCase):
    def cells(self):
        return {
            c: [
                {"record_id": "one", "group_id": "coffee", "full_T": {}, "hidden_T": {}}
            ]
            for c in ["C00", "C10", "C01", "C11"]
        }

    def test_empty_targets_retained(self):
        self.assertEqual(len(aligned(self.cells())["C00"]), 1)

    def test_no_silent_id_misalignment(self):
        cells = self.cells()
        cells["C11"][0]["record_id"] = "other"
        with self.assertRaisesRegex(ValueError, "NOT_ALIGNED"):
            aligned(cells)

    def test_duplicate_rejected(self):
        cells = self.cells()
        cells["C00"] *= 2
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            aligned(cells)

    def test_targets_fixed(self):
        cells = self.cells()
        cells["C10"][0]["full_T"] = {"sensory.apple": 1}
        with self.assertRaisesRegex(ValueError, "TARGET_MISMATCH"):
            aligned(cells)


if __name__ == "__main__":
    unittest.main()
