"""Synthetic masking, support, grouped selection and reload contracts."""

import copy
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import multi_view_r3 as m
from test_profile_alignment_r2 import fixture as professional_fixture
from test_profile_increment_r2 import fixture as nominal_fixture


def numeric_fixture(n=24):
    rng = np.random.default_rng(17)
    return [{"record_id": f"synthetic:{i}", "group_id": f"synthetic:{i}", "split": "DEVELOPMENT",
             "attribute_measurements": dict(zip(m.targets("barahona"), rng.uniform(2, 8, 7))),
             "attribute_masks": dict.fromkeys(m.targets("barahona"), True),
             "attribute_states": dict.fromkeys(m.targets("barahona"), "OBSERVED")}
            for i in range(n)]


class MultiViewTests(unittest.TestCase):
    def test_source_native_main_matches_retained_r2_equations(self):
        for kind, rows in [("barahona", numeric_fixture()), ("rocchetti", professional_fixture("rocchetti"))]:
            model = m.fit(rows[:-2], kind, "group_id", "H0_MAIN", 0.5)
            old = m.increment.fit_barahona(rows[:-2]) if kind == "barahona" else m.prior.fit(rows[:-2], kind, 0.5)
            for row in rows[-2:]:
                before, after = m.baseline_predict(row, old, kind), m.predict(row, model)
                np.testing.assert_allclose([before[c] for c in m.targets(kind)], [after[c] for c in m.targets(kind)], atol=1e-12)
        rows = nominal_fixture(9, 6)
        model = m.fit(rows, "liberica", "participant_id", "H0_MAIN", 0.05)
        old = m.increment.fit(rows)
        for target, probability in m.predict(rows[0], model).items():
            np.testing.assert_allclose(probability, m.increment.predict(rows[0], old)[target], atol=1e-12)

    def test_whole_view_hidden_metadata_excluded_and_reload(self):
        for kind, rows, axis, ridge in [("barahona", numeric_fixture(), "group_id", 0.5),
                                        ("liberica", nominal_fixture(12, 6), "participant_id", 0.05)]:
            model = m.fit(rows[:-6], kind, axis, "H2_PAIRS_TRIPLES", ridge)
            row = rows[-1]
            before = m.predict(row, model)
            self.assertEqual(before, m.predict(row, json.loads(json.dumps(model))))
            for view, block in m.views(kind).items():
                hidden = copy.deepcopy(row)
                for target in block:
                    hidden["response_masks" if kind == "liberica" else "attribute_masks"][target] = False
                    hidden["responses" if kind == "liberica" else "attribute_measurements"][target] = -999
                hidden.update(participant_id="ignored", group_id="ignored", liking=1e99, C0="ignored", future_target=1e99)
                for target in block:
                    self.assertEqual(before[target], m.predict(hidden, model, only_target=target)[target])
            broken = copy.deepcopy(model)
            head = next(iter(broken["heads"].values()))
            head["input_fields"][0] = m.views(kind)[head["view"]][0]
            with self.assertRaisesRegex(ValueError, "TARGET_VIEW_LEAKAGE"):
                m.predict(row, broken)

    def test_masks_and_zero_semantics_and_history_exclusion(self):
        rows = nominal_fixture(9, 6)
        self.assertEqual(m.observed(rows[0], m.targets("liberica")[0], "liberica"), 0)
        for field, value in [("response_masks", False), ("response_states", "TRUE_ZERO")]:
            bad = copy.deepcopy(rows)
            bad[0][field][m.targets("liberica")[0]] = value
            with self.assertRaisesRegex(ValueError, "MASKS"):
                m.fit(bad, "liberica", "participant_id", "H0_MAIN", 0.05)
        for field in ("participant_split", "condition_split"):
            bad = copy.deepcopy(rows)
            bad[0][field] = "CONFIRMATION"
            with self.assertRaisesRegex(ValueError, "DEVELOPMENT"):
                m.fit(bad, "liberica", "participant_id", "H0_MAIN", 0.05)
        roc = professional_fixture("rocchetti")
        roc[0]["attribute_masks"][m.targets("rocchetti")[0]] = False
        with self.assertRaisesRegex(ValueError, "MASKS"):
            m.fit(roc, "rocchetti", "group_id", "H0_MAIN", 0.5)

    def test_train_only_scaler_selection_support_caps_and_heredity(self):
        rows = numeric_fixture()
        model = m.fit(rows[:18], "barahona", "group_id", "H2_PAIRS_TRIPLES", 0.5)
        for target, h in model["heads"].items():
            X = np.array([m.raw_inputs(row, "barahona", h["view"]) for row in rows[:18]])
            np.testing.assert_array_equal(h["base_encoding"]["feature_mean"], X.mean(0))
            self.assertLessEqual(len(h["pairs"]), 4)
            self.assertLessEqual(len(h["triples"]), 2)
            for term in h["pairs"] + h["triples"]:
                self.assertGreaterEqual(term["nonzero_support_groups"], 3)
                self.assertEqual(term["train_group_count"], 18)
                self.assertTrue(set(term["term"]) <= set(h["input_fields"]))
            for triple in h["triples"]:
                self.assertTrue(any(set(pair["term"]) <= set(triple["term"]) for pair in h["pairs"]))
        with self.assertRaisesRegex(ValueError, "HELD_RECORD"):
            m.held_rows(rows[:1], model, "group_id")

    def test_nominal_interactions_are_category_conjunctions_and_group_support(self):
        raw = np.array([[0, 1], [0, 1], [0, 1], [2, 3], [2, 3], [2, 3]])
        base, _ = m.train_base(raw, "liberica")
        term = [["a", 0], ["b", 1]]
        np.testing.assert_array_equal(m.term_values(raw, base, term, ["a", "b"], "liberica"), [1, 1, 1, 0, 0, 0])
        residual = np.eye(6)[[0, 0, 0, 1, 1, 1]] - 1 / 6
        selected, _ = m.select_terms(raw, base, ["a", "b"], list("abcdef"), residual, "liberica", 2, [])
        self.assertTrue(selected)
        blocked, _ = m.select_terms(raw, base, ["a", "b"], ["one"] * 3 + ["two"] * 3, residual, "liberica", 2, [])
        self.assertFalse(blocked)  # Six rows are still only two independent people.

    def test_numeric_triple_is_actually_fitted_not_only_labelled(self):
        rows = numeric_fixture(150)
        for row in rows:
            v = row["attribute_measurements"]
            x, y, z = ((v[name] - 5) / 3 for name in ("acidity", "bitter", "sweet"))
            v["body"] = 5 + x * y + 3 * x * y * z
        train, held = rows[:120], rows[120:]
        pair = m.fit(train, "barahona", "group_id", "H1_PAIRS", 0.5)
        triple = m.fit(train, "barahona", "group_id", "H2_PAIRS_TRIPLES", 0.5)
        self.assertEqual(pair["heads"]["body"]["pairs"], triple["heads"]["body"]["pairs"])
        self.assertTrue(triple["heads"]["body"]["triples"])
        def error(model):
            return np.mean([abs(r["attribute_measurements"]["body"] - m.predict(r, model, only_target="body")["body"]) for r in held])
        self.assertLess(error(triple), error(pair))

    def test_inner_folds_recompute_only_allowed_training_rows(self):
        rows = numeric_fixture(15)
        ridge, audit = m.select_ridge(rows, "barahona", "group_id", "H1_PAIRS")
        self.assertIn(ridge, [0.5, 5.0])
        self.assertEqual(set(audit["all_inner_scores"]), {"0.5", "5.0"})
        for fold in audit["fold_audit"]:
            train, held = set(fold["train_units"]), set(fold["held_units"])
            self.assertFalse(train & held)
            self.assertEqual(train | held, {r["group_id"] for r in rows})
            for head in fold["target_selection"].values():
                for term in head["pairs"]:
                    self.assertEqual(term["train_group_count"], len(train))
        self.assertEqual(m.inner_folds(rows, "group_id"), m.inner_folds(list(reversed(rows)), "group_id"))

    def test_denominator_macro_direction_and_small_history(self):
        rows = []
        for unit, n, value in [("a", 9, 0.8), ("b", 1, 0.2)]:
            for i in range(n):
                rows.append({"unit": unit, "losses": {"R2_RETAINED": [1.0] * 7, "H0_MAIN": [1.0] * 7,
                                                       "H1_PAIRS": [value] * 7, "H2_PAIRS_TRIPLES": [value + 0.1] * 7}})
        summary = m.summarize(rows, "barahona", historical=True)
        self.assertEqual(summary["evaluated_cells_per_model"], 70)
        self.assertEqual(summary["held_units"], 2)
        self.assertAlmostEqual(summary["macro"]["scores"]["H1_PAIRS"], 0.5)
        c = summary["macro"]["comparisons"]["H2_PAIRS_TRIPLES_MINUS_H1_PAIRS"]
        self.assertAlmostEqual(c["delta"], 0.1)
        self.assertIsNone(c["paired_group_95_interval"])
        self.assertEqual(c["status"], "HISTORICAL_REGRESSION_DESCRIPTIVE")


if __name__ == "__main__":
    unittest.main()
