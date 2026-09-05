"""Integrity, split isolation and reload checks for the retained model experiment."""

import copy, importlib.util, json, math, os, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-model-20260905"
sys.path.insert(0, str(ROOT / "db/scripts"))


def module(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


ext = module("extension_tests", ROOT / "db/scripts/extend-backend-model.py")


class PublicArtifacts(unittest.TestCase):
    def test_core_metrics_preserved_with_extension_results_separate(self):
        m = json.loads((OUT / "metrics.json").read_text())
        self.assertEqual(m["conclusion"], "INCONCLUSIVE")
        self.assertEqual(m["real_independent_answer_cases"], 0)
        self.assertEqual(m["runtime_extension"]["additional_fit_count"], 2)
        self.assertFalse(m["runtime_extension"]["dev_decision"]["auxiliary_retained"])
        for model in ["B0", "B1", "B2", "M1"]:
            self.assertEqual(m["models"][model]["coverage"], 1)
        self.assertEqual(
            m["diagnostics"]["live_backend"]["all_8_C0_x_7_C1_combinations_passed"],
            True,
        )

    def test_source_rights_roles_and_core_identity_disjoint(self):
        d = json.loads((OUT / "dataset_manifest.json").read_text())
        self.assertFalse(d["pre_split_statistics_estimated"])
        self.assertEqual(d["source_classes"]["complete_c0_c1_records"]["count"], 0)
        self.assertEqual(d["admitted_source"]["machine_license_field"], "CC BY 4.0")
        self.assertIn("Non-commercial", d["admitted_source"]["author_usage_notice"])
        self.assertTrue(
            all(
                d["admitted_source"]["conditions_checked"][k]
                for k in [
                    "attribution_in_manifest",
                    "noncommercial_local_research_only",
                    "raw_data_not_redistributed",
                    "model_weights_not_released",
                ]
            )
        )
        self.assertEqual(
            d["runtime_source_admission"]["source_family_count_with_aux"], 2
        )
        self.assertTrue(
            all(
                x["rights_state"] in {"PENDING", "UNKNOWN"}
                for x in d["source_exclusions"]
            )
        )

    def test_no_weights_raw_records_or_full_answers_in_public_experiment(self):
        forbidden = {
            "model_weights",
            "model_intercepts",
            "professional_observed_evidence",
            "source_roast_terms",
        }

        def scan(x):
            if isinstance(x, dict):
                self.assertFalse(forbidden & set(x))
                [scan(v) for v in x.values()]
            elif isinstance(x, list):
                [scan(v) for v in x]

        for p in OUT.glob("*.json"):
            scan(json.loads(p.read_text()))
        self.assertFalse(list(OUT.glob("*.model.json")))

    def test_frozen_records_cannot_be_overwritten(self):
        import tempfile

        prep = module(
            "guarded_prepare", ROOT / "db/scripts/prepare-backend-model-data.py"
        )
        with tempfile.TemporaryDirectory() as folder:
            owner = Path(folder)
            original = '[{"record_id":"owner-data"}]\n'
            (owner / "records.json").write_text(original)
            with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                prep.prepare(owner)
            self.assertEqual((owner / "records.json").read_text(), original)


@unittest.skipUnless(
    os.environ.get("COFFEE_BACKEND_MODEL_ROOT"),
    "Owner-only artifacts unavailable; public CI must not fetch restricted data",
)
class RetainedModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = Path(os.environ["COFFEE_BACKEND_MODEL_ROOT"])
        cls.engine, cls.runner = ext.frozen(cls.owner)
        cls.records = json.loads((cls.owner / "records.json").read_text())
        cls.bundle = json.loads((cls.owner / "models/M1.model.json").read_text())
        cls.eps = json.loads((cls.owner / "test_episodes.json").read_text())

    def test_freeze_and_source_groups_never_cross_splits(self):
        splits = {
            s: {r["group_id"] for r in self.records if r["split"] == s}
            for s in ["TRAIN", "DEV", "TEST"]
        }
        self.assertFalse(splits["TRAIN"] & splits["DEV"])
        self.assertFalse(splits["TRAIN"] & splits["TEST"])
        self.assertFalse(splits["DEV"] & splits["TEST"])
        self.assertEqual(
            [len(splits[s]) for s in ["TRAIN", "DEV", "TEST"]], [77, 16, 17]
        )
        self.assertEqual(
            ext.sha(self.owner / "models/M1.model.json"),
            ext.sha(self.owner / "core-freeze/M1.model.json"),
        )

    def test_train_statistics_rebuild_without_reading_dev_test(self):
        train = [r for r in self.records if r["split"] == "TRAIN"]
        fresh = self.runner.make_bundle(train)
        for field in [
            "vocabulary",
            "priors",
            "conditional",
            "interaction_pairs",
            "context_adjustments",
            "train_records",
            "evidence_by_candidate",
        ]:
            self.assertEqual(fresh[field], self.bundle[field])
        with self.assertRaises(AssertionError):
            self.runner.make_bundle(self.records)

    def test_masks_hide_target_and_do_not_treat_all_unmentioned_as_negative(self):
        for split, masks in [("TRAIN", 4), ("DEV", 1), ("TEST", 1)]:
            eps = self.runner.episodes(
                [r for r in self.records if r["split"] == split], self.bundle, masks
            )
            for e in eps:
                self.assertFalse(set(e["visible"]) & set(e["hidden"]))
                self.assertTrue(e["hidden"])
                self.assertLessEqual(len(e["visible"]), 3)
                observed = self.engine.observations(e["answers"], self.bundle)[0]
                self.assertLessEqual(observed, set(e["visible"]))
                self.assertFalse(observed & set(e["hidden"]))
                self.assertTrue(all(a["state"] == "SELECTED" for a in e["answers"]))

    def test_reloaded_predictions_match_frozen_core_without_fitting(self):
        expected = json.loads((self.owner / "predictions.private.json").read_text())
        lookup = {(r["episode_id"], r["model"]): r for r in expected}
        for e in self.eps:
            for model in ["B0", "B1", "B2", "M1"]:
                r = self.runner.evaluate(e, self.bundle, model)
                old = lookup[(e["episode_id"], model)]
                for key in [
                    "ranking",
                    "recovery_ranking",
                    "observed_recovery_ndcg_at_5",
                    "observed_recovery_recall_at_5",
                    "observed_recovery_recall_at_8",
                    "direct_restatement_recall_at_5",
                ]:
                    self.assertEqual(r[key], old[key])

    def test_equal_group_weights_and_balanced_identity(self):
        eps = self.runner.episodes(
            [r for r in self.records if r["split"] == "TRAIN"], self.bundle, 4
        )
        mass = {}
        for e in eps:
            mass[e["group_id"]] = mass.get(e["group_id"], 0) + e["weight"]
        self.assertTrue(all(abs(x - 1) < 1e-12 for x in mass.values()))
        b = json.loads((self.owner / "models/M1_BALANCED.model.json").read_text())
        self.assertEqual(b["model_weights"], self.bundle["model_weights"])
        self.assertEqual(b["model_intercepts"], self.bundle["model_intercepts"])

    def test_auxiliary_is_not_a_core_gold_source_or_duplicate_family(self):
        aux = json.loads((self.owner / "aux_records.json").read_text())
        self.assertEqual(len(aux), 21)
        self.assertFalse(
            {r["group_id"] for r in aux} & {r["group_id"] for r in self.records}
        )
        self.assertEqual({r["split"] for r in aux}, {"AUX_TRAIN_ONLY"})
        self.assertTrue(all(r["c0"] is None and r["c1"] is None for r in aux))
        b = json.loads((self.owner / "models/M1_AUX.model.json").read_text())
        for key in [
            "vocabulary",
            "priors",
            "feature_names",
            "train_records",
            "interaction_pairs",
        ]:
            self.assertEqual(b[key], self.bundle[key])

    def test_review_labels_are_blank_and_sets_disjoint(self):
        rows = json.loads(
            (self.owner / "human_comparison_cases.private.json").read_text()
        )
        key = json.loads((self.owner / "human_comparison_key.private.json").read_text())
        self.assertEqual(len(rows), 20)
        self.assertTrue(
            all(
                r["human_preference"] is None and r["human_reviewer"] is None
                for r in rows
            )
        )
        dev = {k["group_id"] for k in key if k["review_id"].startswith("development")}
        locked = {k["group_id"] for k in key if k["review_id"].startswith("locked")}
        self.assertFalse(dev & locked)

    def test_refit_cannot_overwrite_retained_model(self):
        current = module("guarded_run", ROOT / "db/scripts/run-backend-model.py")
        with self.assertRaisesRegex(RuntimeError, "Core model is frozen"):
            current.fit(self.owner)


if __name__ == "__main__":
    unittest.main()
