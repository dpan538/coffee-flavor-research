import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"


def load(name: str):
    return json.loads((R11 / name).read_text(encoding="utf-8"))


class R11CorpusExpansionContractTest(unittest.TestCase):
    def test_round_is_zero_fit_and_no_real_metric(self):
        manifest = load("round_manifest.json")
        self.assertEqual(manifest["fit_count"], 0)
        self.assertEqual(manifest["real_label_model_vs_baseline_metric_count"], 0)
        self.assertTrue(manifest["training_pause_after_round"])
        blind = load("pipeline_validation.json")
        self.assertEqual(blind["status"], "PASS")
        self.assertEqual(blind["input_scope"], "SYNTHETIC_LABELS_ONLY")
        self.assertEqual(blind["attestation"]["fit_count"], 0)
        self.assertEqual(
            blind["attestation"]["real_data_model_vs_baseline_metrics_computed"], 0
        )

    def test_fixed_exit_thresholds_are_not_relaxed(self):
        report = load("exit_criterion_status.json")
        expected = {
            "DIRECT_T1_T2_T3_GROUPS": (">=", 250),
            "DIRECT_PLUS_MAPPED_T1_T2_T3_GROUPS": (">=", 600),
            "T4_GROUPS": (">=", 600),
            "T4_C0_GROUPS": (">=", 150),
            "T4_C1_GROUPS": (">=", 150),
            "T5_T6_ONTOLOGY_RECORDS": (">=", 200),
            "SOURCE_FAMILIES": (">=", 8),
            "CANDIDATES_WITH_TEN_GROUPS": (">=", 40),
            "MAX_SOURCE_FAMILY_SHARE": ("<=", 0.35),
        }
        actual = {
            row["criterion"]: (row["comparison"], row["target"])
            for row in report["criteria"]
        }
        self.assertEqual(actual, expected)
        self.assertFalse(report["thresholds_revised_downward"])

    def test_failure_taxonomy_accounts_for_all_248(self):
        report = load("failure_taxonomy.json")
        self.assertEqual(report["candidate_count"], 248)
        self.assertEqual(sum(report["diagnosis_class_counts"].values()), 248)
        self.assertEqual(len(report["records"]), 248)
        self.assertEqual(
            report["issued_addendum_count_check"]["status"],
            "INCONSISTENT_ISSUED_COUNTS_SUM_TO_250",
        )

    def test_typed_records_keep_tracks_separate(self):
        report = load("shape_distribution.json")
        records = report["records"]
        self.assertEqual(len(records), len({row["record_id"] for row in records}))
        allowed = {
            "CC0-1.0",
            "CC-BY-4.0",
            "CC-BY-3.0",
            "CC-BY-SA-4.0",
            "CC-BY-NC-4.0",
            "ODbL-1.0",
            "EXPLICIT-NONCOMMERCIAL-RESEARCH-TDM",
        }
        for row in records:
            self.assertIn(row["resolved_license"], allowed)
            self.assertNotIn("-ND-", row["resolved_license"])
            if row["shape_id"] == "T4":
                self.assertEqual(row["track"], "COFFEE_PROFESSIONAL_SUPERVISION")
                self.assertIsNotNone(row["native_dimension_id"])
            if row["shape_id"] in {"T5", "T6"}:
                self.assertEqual(row["track"], "ONTOLOGY_REVIEW_ONLY")
                self.assertNotIn("coffee_group_id", row)

    def test_frozen_mapping_only_and_direct_mapped_separate(self):
        mapping = load("mapping_audit.json")
        self.assertEqual(mapping["guards"]["registry_mutations"], 0)
        self.assertEqual(mapping["guards"]["formal_relation_edges_created"], 0)
        self.assertEqual(mapping["guards"]["specificity_increasing_mappings"], 0)
        for row in mapping["mapped_assertions"]:
            self.assertTrue(row["rule_id"])
            self.assertNotEqual(row["mapping_direction"], "SPECIFICATION")
        counts = load("direct_vs_mapped_counts.json")
        self.assertTrue(counts["counts_reported_separately"])
        self.assertEqual(counts["guards"]["unlabelled_merged_headline_count"], 0)

    def test_reconciliation_sums_and_discloses_provenance_mismatch(self):
        report = load("readmission_reconciliation.json")
        self.assertEqual(report["accounting"]["eligible_assertion_count"], 5819)
        self.assertEqual(report["accounting"]["accounted_total"], 5819)
        self.assertTrue(report["accounting"]["sums_to_5819"])
        mismatch = report["published_879_provenance_discrepancy"]
        self.assertEqual(mismatch["eligible_cohort_unique_occurrence_count"], 869)
        self.assertEqual(mismatch["whole_ledger_unique_occurrence_count"], 879)
        self.assertEqual(mismatch["unique_occurrences_outside_5819_count"], 10)
        self.assertEqual(mismatch["status"], "DISCLOSED_NOT_SILENTLY_RECONCILED")

    def test_historical_rights_boundary_and_owner_decision(self):
        calibration = load("contract_calibration_report.json")
        self.assertFalse(calibration["conclusion"]["rights_question_reopened"])
        self.assertEqual(calibration["conclusion"]["historical_hash_only_evidence_promoted"], 0)
        broad = calibration["broad_heterogeneous_inventory_3938"]
        self.assertEqual(broad["derived_total"], 3938)
        self.assertTrue(broad["matches_issued_starting_count"])
        owner = load("owner_decision.json")
        self.assertEqual(owner["status"], "PENDING_OWNER_DECISION")
        self.assertIsNone(owner["selected_option"])
        self.assertFalse(owner["training_authorized"])


if __name__ == "__main__":
    unittest.main()
