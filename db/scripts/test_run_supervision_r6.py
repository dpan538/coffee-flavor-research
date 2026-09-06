"""Small orchestration invariants, distinct from scientific outcomes."""

import unittest
import run_supervision_r6 as run


class Tests(unittest.TestCase):
    def test_predeclared_tie_order(self):
        self.assertEqual(
            run.choose({"0.03": 0.5, "0.1": 0.5, "0.3": 0.5}, ["0.1", "0.3", "0.03"]),
            "0.1",
        )
        self.assertEqual(run.choose({"C00": 0.6, "C10": 0.5}, ["C00", "C10"]), "C10")

    def test_no_identifiable_selection_not_defaulted(self):
        with self.assertRaisesRegex(ValueError, "NO_IDENTIFIABLE"):
            run.choose({"C00": None}, ["C00"])

    def test_four_cell_id_set_required(self):
        base = {"record_id": "a", "group_id": "g", "ranking": []}
        cells = {c: [dict(base)] for c in run.CELLS}
        cells["C11"][0]["record_id"] = "b"
        with self.assertRaisesRegex(ValueError, "ID_ALIGNMENT"):
            run.summarize_cells(cells)

    def test_failed_output_and_empty_target_distinct(self):
        row = {
            "record_id": "a",
            "group_id": "g",
            "ranking": [],
            "full_T": {"sensory.apple": 1},
            "hidden_T": {"sensory.apple": 1},
            "initial_selected": [],
            "selected": {"ASK": []},
            "failure": {"slot": "Q4"},
        }
        self.assertEqual(run.evaluated(row)["raw_gap"], 1)
        self.assertIsNone(run.evaluated({**row, "full_T": {}})["raw_gap"])

    def test_evaluate_native_ranking_rows(self):
        row = {
            "record_id": "a",
            "group_id": "g",
            "ranking": [{"candidate_id": "sensory.apple"}],
            "full_T": {"sensory.apple": 1},
            "hidden_T": {},
            "initial_selected": ["sensory.apple"],
            "selected": {"ASK": ["sensory.apple"]},
        }
        self.assertEqual(run.evaluated(row)["raw_gap"], 0)


if __name__ == "__main__":
    unittest.main()
