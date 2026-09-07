"""R9 workflow tests use software fixtures only, never product-effect evidence."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import audit_output_quality_r9 as audit
import audit_semantic_integrity_r9 as semantic
import analyze_dimension_structure_r9 as dimensions
import evaluate_output_diversity_r9 as diversity
import generate_user_study_pack_r9 as pack
import prepare_training_target_spec_r9 as target_spec
import update_owner_decision_r9 as decision
from output_policy_r9 import role_registry_from_contract


class OwnerDecisionTests(unittest.TestCase):
    def test_pending_decision_is_approved_and_same_approval_is_idempotent(self):
        source = {
            "recorded_utc": "old",
            "owner_decision": {"status": "PENDING_OWNER_DECISION"},
            "recommendation": {
                "status": "PRODUCT_STRUCTURE_RECOMMENDATION_NOT_OWNER_APPROVAL"
            },
            "training_after_R9": "PAUSED_REQUIRES_SEPARATE_FUTURE_OWNER_AUTHORIZATION",
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "decision.json"
            path.write_text(json.dumps(source))
            updated, changed = decision.update(path, "2026-09-07T07:00:00+00:00")
            self.assertTrue(changed)
            self.assertEqual(updated["owner_decision"]["status"], "OWNER_APPROVED")
            self.assertEqual(
                updated["owner_decision"]["approved_policy"], "OUT_SEPARATED"
            )
            self.assertIn("PAUSED", updated["training_after_R9"])
            same, changed = decision.update(path, "2026-09-07T08:00:00+00:00")
            self.assertFalse(changed)
            self.assertEqual(
                same["owner_decision"]["approved_utc"],
                "2026-09-07T07:00:00+00:00",
            )


class FormativePackTests(unittest.TestCase):
    def registry(self):
        contract = json.loads(
            (
                ROOT
                / "db/data/backend-sequential-model-v2/revisions/r9/output_policy_contract.json"
            ).read_text()
        )
        return role_registry_from_contract(contract)

    def final(self):
        candidate_ids = [
            "attribute.fruity",
            "sensory.apple",
            "attribute.floral",
            "sensory.lemon",
            "broad.citrus",
            "sensory.jasmine",
            "sensory.cocoa",
            "sensory.honey",
            "sensory.lime",
            "sensory.rose",
        ]
        rows = [
            {
                "candidate_id": candidate_id,
                "score": 10 - index,
                "legal": True,
                "explicit": candidate_id == "sensory.lemon",
            }
            for index, candidate_id in enumerate(candidate_ids)
        ]
        main, secondary = rows[:5], rows[5:8]
        return {
            "stage": "PRELIMINARY_RESULT",
            "state": {
                "candidate_scores": rows,
                "base_state": {
                    "context": {
                        "c0": "preparation.family.filter_percolation",
                        "c1": "medium",
                    },
                    "policy": "fixed",
                    "final_comparison": None,
                },
                "k1": {
                    "confirmed_concepts": ["sensory.lemon"],
                    "dimensions": {
                        "fruity": {"supported": 1.0},
                        "floral": {"supported": 1.0},
                    },
                },
            },
            "main": main,
            "secondary": secondary,
            "exposure": {
                "candidate_ids": [row["candidate_id"] for row in main + secondary],
                "generation_version": "frozen-C01-test-bundle",
                "state_hash": "a" * 64,
                "eligible_for_final_comparison": True,
            },
        }

    def test_prepare_creates_unassigned_out_separated_slots_without_fake_data(self):
        rows = pack.prepare_rows(12, 2)
        self.assertEqual(len(rows), 24)
        self.assertEqual({row["policy_id"] for row in rows}, {"OUT_SEPARATED"})
        self.assertEqual({row["participant_uid"] for row in rows}, {""})
        self.assertEqual(
            {row["assignment_status"] for row in rows},
            {"UNASSIGNED_NO_REAL_DATA"},
        )
        self.assertEqual(
            {row["profile_pair_order"] for row in rows},
            {"WITH_PROFILE_FIRST", "WITHOUT_PROFILE_FIRST"},
        )

    def test_materialize_uses_live_results_and_leaves_judgments_blank(self):
        tasks = [
            {
                "participant_uid": f"participant-{index:02d}",
                "session_id": f"session-{index:02d}",
                "coffee_id": f"coffee-{index % 3}",
                "preparation_batch_or_condition": "shared-batch/filter-recipe",
                "coffee_order": 1,
                "previous_study_exposure": "NONE",
                "qa_transcript_private_ref": f"private://qa/{index:02d}",
                "pre_output_impression_private_ref": f"private://impression/{index:02d}",
                "actual_c01_return": self.final(),
            }
            for index in range(9)
        ]
        rows = pack.materialize_rows(tasks, self.registry(), pack.response_fields())
        self.assertEqual(len(rows), 9)
        self.assertEqual({row["policy_id"] for row in rows}, {"OUT_SEPARATED"})
        self.assertEqual({row["main_fit_rating_1_to_4"] for row in rows}, {""})
        self.assertTrue(
            all(json.loads(row["profile_candidate_ids_ordered_json"]) for row in rows)
        )
        self.assertTrue(all(row["output_hash"] for row in rows))

    def test_mechanism_evidence_and_profile_audits_keep_claim_boundaries(self):
        source = {
            "record_id": "record-001",
            "group_id": "coffee-group-001",
            "policy": "C01",
            "full_T": {"sensory.apple": 1.0},
            "actual_return": self.final(),
        }
        mechanism = audit.mechanism_case(source, self.registry())
        self.assertEqual(
            mechanism["mechanism"],
            "PROFILE_DIRECTION_REMOVED_NAMED_PROMOTED",
        )
        self.assertTrue(mechanism["within_role_order_preserved"])
        evidence = audit.evidence_rows(source, self.registry())
        lemon = next(row for row in evidence if row["descriptor_id"] == "sensory.lemon")
        self.assertEqual(lemon["evidence_class"], "EXPLICIT_USER_EXPRESSION")
        self.assertIn("not an over-specification finding", lemon["scope_note"])
        profile = audit.profile_case(source, self.registry())
        self.assertTrue(profile["all_profiles_supported_by_k1"])
        self.assertEqual(profile["profile_pool_overlap_ids"], [])

    def test_future_training_spec_has_no_authorization_or_invented_thresholds(self):
        contract = json.loads(
            (
                ROOT
                / "db/data/backend-sequential-model-v2/revisions/r9/output_policy_contract.json"
            ).read_text()
        )
        decision_record = {
            "owner_decision": {
                "status": "OWNER_APPROVED",
                "approved_policy": "OUT_SEPARATED",
                "approved_utc": "2026-09-07T07:18:54+00:00",
            }
        }
        spec = target_spec.specification(decision_record, contract)
        self.assertFalse(spec["training_authorized"])
        self.assertEqual(spec["fit_count"], 0)
        self.assertEqual(
            set(spec["acceptance_contract"]["empirical_thresholds"].values()),
            {
                "NOT_SET",
                "REPORT_SEPARATELY_NO_COMPOSITE",
                "PROHIBITED_NOT_A_THRESHOLD",
            },
        )
        self.assertEqual(
            spec["semantic_training_governance"][
                "external_subjective_evaluation_dependency"
            ],
            "PROHIBITED",
        )
        self.assertEqual(
            spec["data_requirements"]["participant_or_preference_fields"],
            "FORBIDDEN",
        )

    def test_registered_dimension_extensions_are_static_and_multi_label(self):
        final = self.final()
        final["state"]["base_state"]["answers_by_question"] = {
            "Q0": {
                "question_id": "question-001",
                "selected_option_ids": ["sensory.dark_chocolate"],
            }
        }
        source = {
            "record_id": "record-001",
            "group_id": "coffee-group-001",
            "policy": "C01",
            "full_T": {"sensory.apple": 1.0},
            "actual_return": final,
        }
        registry = self.registry()
        links = dimensions.evidence_reception_rows(source, registry)
        self.assertGreater(len(links), 1)
        self.assertEqual(len({row["evidence_id"] for row in links}), 1)
        self.assertAlmostEqual(
            sum(row["uniform_membership_weight"] for row in links), 1.0
        )
        registered = dimensions.registered_dimensions(registry)
        concentration = dimensions.consensus_case(source, registry, registered)
        self.assertLessEqual(
            concentration["policies"]["OUT_SEPARATED"]["active_dimension_count"],
            9,
        )
        vote = dimensions.single_pass_case(source, registry)
        self.assertTrue(
            vote["factor_graph_single_pass_equals_cluster_vote_under_this_definition"]
        )
        curves = dimensions.prefix_curve_case(source, registry)
        self.assertEqual(
            [point["k"] for point in curves["policies"]["OUT_SEPARATED"]],
            list(range(1, 9)),
        )

    def test_diversity_metrics_separate_coverage_redundancy_and_fit(self):
        registry = self.registry()
        rows = [
            {"candidate_id": "sensory.apple"},
            {"candidate_id": "sensory.lemon"},
            {"candidate_id": "sensory.rose"},
        ]
        coverage = diversity.coverage_metrics(
            rows, ["sensory.apple", "sensory.rose"], registry
        )
        self.assertEqual(coverage["all_roles"]["target_dimension_recall"], 1.0)
        self.assertEqual(coverage["all_roles"]["output_dimension_precision"], 1.0)
        redundancy = diversity.redundancy_metrics(rows[:2], registry)
        self.assertEqual(redundancy["repeated_dimension_membership_rate"], 0.5)
        self.assertEqual(redundancy["mean_pairwise_dimension_jaccard"], 1.0)
        no_penalty = diversity.diversity_adjusted_fit(
            rows[:2],
            ["sensory.apple", "sensory.lemon"],
            registry,
            alpha=0.0,
            declared_budget=2,
        )
        penalty = diversity.diversity_adjusted_fit(
            rows[:2],
            ["sensory.apple", "sensory.lemon"],
            registry,
            alpha=0.5,
            declared_budget=2,
        )
        self.assertLess(
            penalty["alpha_ndcg_optimistic"],
            no_penalty["alpha_ndcg_optimistic"],
        )

    def test_missing_target_dimensions_are_not_scored_as_zero_precision(self):
        coverage = diversity.coverage_metrics(
            [{"candidate_id": "sensory.apple"}], [], self.registry()
        )
        self.assertFalse(coverage["evaluable"])
        self.assertIsNone(coverage["all_roles"]["target_dimension_recall"])
        self.assertIsNone(coverage["all_roles"]["output_dimension_precision"])
        self.assertIsNone(coverage["all_roles"]["dimension_jaccard"])

    def test_semantic_integrity_separates_structure_from_assertion_trace(self):
        contract = json.loads(
            (
                ROOT
                / "db/data/backend-sequential-model-v2/revisions/r9/output_policy_contract.json"
            ).read_text()
        )
        registry = role_registry_from_contract(contract)
        registry_audit = semantic.contract_audit(contract, registry)
        self.assertEqual(
            registry_audit["identifier_and_dimension_registry_integrity"], "PASS"
        )
        self.assertEqual(registry_audit["descriptor_relation_edge_count"], 0)
        source = {
            "record_id": "record-001",
            "group_id": "coffee-group-001",
            "policy": "C01",
            "full_T": {"sensory.apple": 1.0},
            "actual_return": self.final(),
        }
        result = semantic.case_audit(source, registry, frozenset())
        self.assertTrue(result["identifier_integrity"]["pass"])
        self.assertTrue(result["role_purity"]["pass"])
        self.assertTrue(result["ontology_legality"]["pass"])
        self.assertTrue(result["supported_dimension_coverage"]["coverage_complete"])
        self.assertTrue(result["T_used"] is False)
        self.assertTrue(
            any(
                not row["strict_assertion_trace_ready"]
                for row in result["descriptor_evidence"]
            )
        )
        with self.assertRaisesRegex(
            ValueError, "SUBJECTIVE_EVALUATION_PRESENT_IN_SEMANTIC_AUDIT_INPUT"
        ):
            semantic.case_audit(
                {**source, "participant_rating": 4}, registry, frozenset()
            )


if __name__ == "__main__":
    unittest.main()
