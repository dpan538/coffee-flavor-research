"""Public contracts and optional owner-local fitted artifact verification."""

import copy, json, os, sys, unittest
from pathlib import Path
import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import flavor_sequential as s
import flavor_backend as facade
import flavor_planning as planning
import train_sequential as t

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-sequential-model-v2"


class PublicV2(unittest.TestCase):
    def test_contract_and_scientific_scope(self):
        contract = json.loads((OUT / "backend_contract.json").read_text())
        jsonschema.Draft202012Validator.check_schema(contract)
        m = json.loads((OUT / "metrics.json").read_text())
        self.assertEqual(m["sequential"]["real_QA"], "NOT_EVALUATED")
        self.assertEqual(m["feedback"]["real_feedback_effect"], "NOT_EVALUATED")
        self.assertFalse(m["selection_decision"]["replace_historical_M1"])
        self.assertEqual(
            m["sequential"]["comparisons"]["HIER_minus_JOINT"]["status"],
            "NO_IMPROVEMENT",
        )
        for k, v in m["policy"]["models"].items():
            self.assertEqual(v["coverage"], 1.0)
            self.assertEqual(v["question_count"], 5)
            self.assertEqual(v["option_budget"], 20)

    def test_no_owner_data_or_weights_in_public_experiment(self):
        forbidden = {
            "model_weights",
            "model_intercepts",
            "professional_observed_evidence",
            "panelist_mention_sets",
            "answers_by_question",
            "recovery_ranking",
            "candidate_vocabulary",
            "coefficients",
        }

        # Contract schemas name data fields; all other public records contain only summaries.
        def scan(x):
            if isinstance(x, dict):
                self.assertFalse(forbidden & set(x))
                for v in x.values():
                    scan(v)
            elif isinstance(x, list):
                for v in x:
                    scan(v)

        for path in OUT.glob("*.json"):
            if path.name != "backend_contract.json":
                scan(json.loads(path.read_text()))


@unittest.skipUnless(
    os.getenv("COFFEE_SEQUENTIAL_V2_ROOT"), "Owner data not fetched by public tests"
)
class RetainedV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.owner = Path(os.environ["COFFEE_SEQUENTIAL_V2_ROOT"])
        cls.bundle = json.loads(
            (cls.owner / "models/selected_bundle.model.json").read_text()
        )
        cls.records = json.loads((cls.owner / "recovery_records.json").read_text())
        cls.payload = json.loads(
            (cls.owner / "example_request.private.json").read_text()
        )

    def test_manifest_and_nested_features_do_not_use_held_groups(self):
        manifest = json.loads(
            (self.owner / "training_manifest.private.json").read_text()
        )
        self.assertEqual(s.digest(manifest), self.bundle["data_manifest_hash"])
        folds = json.loads((self.owner / "cv/splits.private.json").read_text())
        historic = {
            r["group_id"] for r in self.records if r["split"] == "HISTORICAL_REGRESSION"
        }
        for path in (self.owner / "cv").glob("*fold*.model.json"):
            b = json.loads(path.read_text())
            fold = int(path.stem.split("fold")[1].split(".")[0])
            held = {g for g, f in folds.items() if f == fold}
            trained = {r["group_id"] for r in b["statistics"]["planning_records"]}
            self.assertFalse(trained & held)
            self.assertFalse(trained & historic)
            self.assertFalse(set(b["cluster_model"]["training_groups"]) & held)
            for audit in b["inner_feature_isolation"]:
                self.assertFalse(
                    set(audit["feature_training_groups"])
                    & set(audit["feature_output_groups"])
                )

    def test_public_facade_live_offline_scores_and_schema(self):
        contract = json.loads((OUT / "backend_contract.json").read_text())
        jsonschema.validate(self.payload, contract)
        live = facade.run(self.payload, self.bundle)
        offline = s.evaluation_entry(self.payload, self.bundle)
        self.assertEqual(live, offline)
        schema = {"$ref": "#/$defs/Result", "$defs": contract["$defs"]}
        jsonschema.validate(live, schema)
        self.assertEqual(
            live["state"]["features"],
            facade.encode_features(self.payload, self.bundle)["features"],
        )
        self.assertTrue(live["state"]["predicted_context_attributes"])
        self.assertFalse(
            live["state"]["context_attributes_used_for_descriptor_scoring"]
        )

    def test_all_56_full_paths_and_single_final_comparison(self):
        for c0 in s.C0:
            for c1 in s.C1:
                payload = copy.deepcopy(self.payload)
                payload["context"] = {"c0": c0, "c1": c1}
                out = facade.run(payload, self.bundle)
                exposed = out["exposure"]["candidate_ids"]
                final = facade.apply_final_comparison(
                    out["state"],
                    exposed,
                    exposed[:2],
                    self.bundle,
                    feedback_source="SIMULATED",
                    generation_version=self.bundle["bundle_id"],
                )
                self.assertEqual(
                    facade.plan_stage(final, self.bundle)["action"], "FINAL_RESULT"
                )
                result = facade.finalize_result(final, self.bundle)
                self.assertLessEqual(len(result["main"]), 5)
                self.assertLessEqual(len(result["secondary"]), 3)

    def test_visible_masks_q0_q1_and_blank_review(self):
        for record in self.records:
            ep = t.visible_episode(record)
            self.assertFalse(set(ep["visible"]) & set(ep["hidden"]))
        rows = json.loads((self.owner / "cv/M2_JOINT.private.json").read_text())
        for row in rows:
            self.assertEqual(
                [a["slot"] for a in row["payload"]["answers"][:2]], ["Q0", "Q1"]
            )
        pack = json.loads(
            (self.owner / "human_comparison_cases.private.json").read_text()
        )
        self.assertEqual(len(pack), 20)
        for r in pack:
            self.assertIsNone(r["human_choice"])
            self.assertIsNone(r["human_rationale"])

    def test_reloaded_weights_and_explicit_missing_context(self):
        self.assertEqual(
            s.run(self.payload, self.bundle),
            s.run(self.payload, json.loads(json.dumps(self.bundle))),
        )
        for key in ["context_c0", "context_c1", "context_answer_interaction"]:
            i = s.FEATURES.index(key)
            self.assertEqual(self.bundle["model_parameters"]["weights"][i], 0.0)
        for path in (self.owner / "models").glob("*.model.json"):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
