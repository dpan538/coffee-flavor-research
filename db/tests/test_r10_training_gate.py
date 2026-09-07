#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import unittest

from output_policy_r10 import evidence_disposition


ROOT = Path(__file__).resolve().parents[2]
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"


def read(name: str):
    return json.loads((R10 / name).read_text())


class R10GateTests(unittest.TestCase):
    def test_unknown_resolution_is_complete_and_fail_closed(self):
        report = read("license_resolution_report.json")
        self.assertEqual(len(report["records"]), 13_952)
        self.assertEqual(
            len({row["assertion_id"] for row in report["records"]}), 13_952
        )
        self.assertEqual(report["summary"]["resolved_assertion_count"], 0)
        self.assertEqual(report["summary"]["remaining_unknown_assertion_count"], 13_952)
        self.assertEqual(
            {row["http_status"] for row in report["source_resolutions"]["landing_page"].values()},
            {200},
        )

    def test_tiers_are_independent_and_go_is_numeric(self):
        tiers = read("eligibility_tiers.json")
        self.assertEqual(tiers["tiers"]["COMMERCIAL_GRADE"]["model_eligible_assertion_count"], 0)
        nc = tiers["tiers"]["NON_COMMERCIAL_RESEARCH"]
        self.assertEqual(nc["model_eligible_assertion_count"], 5_819)
        self.assertEqual(nc["source_family_count"], 5)
        self.assertTrue(tiers["pii_schema_check"]["pass"])
        self.assertFalse(
            any("-ND-" in (row.get("resolved_license") or "") for row in tiers["resolved_source_licenses"])
        )
        gate = read("go_no_go.json")
        self.assertEqual(gate["verdict"], "GO")
        self.assertEqual(gate["N_eligible"], 5_819)
        self.assertEqual(gate["source_family_count"], 5)
        self.assertEqual(gate["training_execution"]["fit_count_this_run"], 0)

    def test_evidence_partition_and_abstention(self):
        report = read("evidence_partition_r10.json")
        self.assertEqual(sum(report["bucket_counts"].values()), 480)
        self.assertEqual(report["bucket_counts"]["RECOVERABLE_DIRECT"], 0)
        self.assertEqual(report["bucket_counts"]["SHARED_DIMENSION_ONLY"], 12)
        self.assertEqual(report["bucket_counts"]["INSUFFICIENT_EVIDENCE_ABSTAIN"], 156)
        self.assertEqual(report["bucket_counts"]["REQUIRES_OWNER_ONTOLOGY_REVIEW"], 312)
        self.assertGreater(
            report["strict_evidence"]["after_abstention"]["rate"],
            report["strict_evidence"]["before"]["rate"],
        )
        self.assertEqual(report["runtime_contract"]["owner_relation_edges_added"], 0)

    def test_runtime_disposition_uses_no_target(self):
        registry = {
            "sensory.lemon": {"support_dimension_ids": ["fruity"]},
            "sensory.cocoa": {"support_dimension_ids": ["nutty_cocoa"]},
        }
        self.assertEqual(
            evidence_disposition("sensory.lemon", registry, {"sensory.lemon"}, set()),
            "STRICT_DIRECT_ASSERTION",
        )
        self.assertEqual(
            evidence_disposition("sensory.cocoa", registry, set(), {"nutty_cocoa"}),
            "NON_STRICT_SHARED_DIMENSION_ONLY",
        )
        self.assertEqual(
            evidence_disposition("sensory.cocoa", registry, set(), {"fruity"}),
            "INSUFFICIENT_EVIDENCE_ABSTAIN",
        )

    def test_corpus_freeze_is_group_isolated(self):
        manifest = read("training_corpus_manifest.json")
        self.assertEqual(manifest["canonical_training_occurrence_count"], 879)
        self.assertEqual(manifest["canonical_training_candidate_count"], 53)
        self.assertEqual(manifest["coffee_group_count"], 204)
        self.assertEqual(sum(manifest["outer_fold_group_counts"].values()), 204)
        self.assertEqual(manifest["training_run_count"], 0)

    def test_acquisition_retains_no_unadapted_rows(self):
        manifest = read("acquisition_manifest.json")
        self.assertEqual(manifest["query_count"], 12)
        self.assertTrue(all(row["status"] == "COMPLETE" for row in manifest["queries"]))
        self.assertEqual(manifest["new_record_count"], 0)
        self.assertEqual(manifest["new_records"], [])
        self.assertNotIn("email", json.dumps(manifest).lower())


if __name__ == "__main__":
    unittest.main()
