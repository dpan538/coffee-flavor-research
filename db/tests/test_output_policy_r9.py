"""R9 output-policy boundaries; fixtures are software tests, not coffee evidence."""

import copy
import inspect
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import flavor_m2_r1 as r1
import compare_output_policies_r9 as comparison
import output_policy_r9 as r9


class OutputPolicyTests(unittest.TestCase):
    def registry(self):
        return {
            "attribute.fruity": {
                "role": r9.PROFILE_DIRECTION,
                "support_dimension_ids": ["fruity"],
            },
            "attribute.floral": {
                "role": r9.PROFILE_DIRECTION,
                "support_dimension_ids": ["floral"],
            },
            "attribute.sweet": {
                "role": r9.PROFILE_DIRECTION,
                "support_dimension_ids": ["sweet"],
            },
            "sensory.lemon": {
                "role": r9.NAMED_DESCRIPTOR,
                "support_dimension_ids": ["fruity"],
            },
            "sensory.jasmine": {
                "role": r9.NAMED_DESCRIPTOR,
                "support_dimension_ids": ["floral"],
            },
            "broad.citrus": {
                "role": r9.NAMED_DESCRIPTOR,
                "support_dimension_ids": ["fruity"],
            },
            "sensory.cocoa": {
                "role": r9.NAMED_DESCRIPTOR,
                "support_dimension_ids": ["nutty_cocoa"],
            },
            "sensory.honey": {
                "role": r9.NAMED_DESCRIPTOR,
                "support_dimension_ids": ["sweet"],
            },
            "sensory.lime": {
                "role": r9.NAMED_DESCRIPTOR,
                "support_dimension_ids": ["fruity"],
            },
            "native.body": {
                "role": r9.OTHER_NATIVE_MEASUREMENT,
                "support_dimension_ids": [],
            },
        }

    def final(self):
        candidate_ids = [
            "attribute.fruity",
            "sensory.lemon",
            "attribute.floral",
            "sensory.jasmine",
            "broad.citrus",
            "sensory.cocoa",
            "attribute.sweet",
            "sensory.honey",
            "native.body",
            "sensory.lime",
        ]
        rows = [
            {
                "candidate_id": candidate_id,
                "score": 10 - position,
                "legal": True,
                "explicit": candidate_id in {"sensory.lemon", "sensory.honey"},
                "evidence_ids": ["fixture-evidence"],
            }
            for position, candidate_id in enumerate(candidate_ids)
        ]
        main, secondary = copy.deepcopy(rows[:5]), copy.deepcopy(rows[5:8])
        return {
            "state": {
                "candidate_scores": rows,
                "k1": {
                    "confirmed_concepts": ["sensory.lemon", "sensory.honey"],
                    "dimensions": {
                        "fruity": {"supported": 1.0},
                        "floral": {"supported": 1.0},
                        "sweet": {"supported": 0.0},
                    },
                },
            },
            "main": main,
            "secondary": secondary,
            "stage": "PRELIMINARY_RESULT",
            "exposure": {
                "candidate_ids": [row["candidate_id"] for row in main + secondary],
                "generation_version": "frozen-test-model",
                "state_hash": "frozen-answer-state",
                "eligible_for_final_comparison": True,
            },
        }

    def test_mixed_preserves_r8_fields_exactly_and_does_not_mutate(self):
        final = self.final()
        old = copy.deepcopy(final)
        output = r9.adapt_output(final, self.registry(), "OUT_MIXED")
        self.assertEqual(output["main"], final["main"])
        self.assertEqual(output["secondary"], final["secondary"])
        self.assertEqual(output["exposure"], final["exposure"])
        self.assertEqual(output["overall_profile"], [])
        self.assertEqual(final, old)

    def test_specific_first_preserves_order_inside_roles(self):
        output = r9.adapt_output(self.final(), self.registry(), "OUT_SPECIFIC_FIRST")
        self.assertEqual(
            [row["candidate_id"] for row in output["main"]],
            [
                "sensory.lemon",
                "sensory.jasmine",
                "broad.citrus",
                "sensory.cocoa",
                "sensory.honey",
            ],
        )
        self.assertEqual(
            [row["candidate_id"] for row in output["secondary"]],
            ["sensory.lime", "attribute.fruity", "attribute.floral"],
        )
        self.assertNotIn("native.body", output["comparison_pool_candidate_ids"])

    def test_separated_returns_named_only_and_supported_profile(self):
        output = r9.adapt_output(self.final(), self.registry(), "OUT_SEPARATED")
        self.assertEqual(
            output["comparison_pool_candidate_ids"],
            [
                "sensory.lemon",
                "sensory.jasmine",
                "broad.citrus",
                "sensory.cocoa",
                "sensory.honey",
                "sensory.lime",
            ],
        )
        self.assertEqual(
            [row["candidate_id"] for row in output["overall_profile"]],
            ["attribute.fruity", "attribute.floral"],
        )
        self.assertEqual(
            output["exposure"]["candidate_ids"],
            output["comparison_pool_candidate_ids"],
        )

    def test_short_separated_output_is_not_backfilled(self):
        final = self.final()
        keep = {
            "attribute.fruity",
            "attribute.floral",
            "sensory.lemon",
            "sensory.honey",
        }
        final["state"]["candidate_scores"] = [
            row
            for row in final["state"]["candidate_scores"]
            if row["candidate_id"] in keep
        ]
        final["main"] = copy.deepcopy(final["state"]["candidate_scores"])
        final["secondary"] = []
        final["exposure"]["candidate_ids"] = [
            row["candidate_id"] for row in final["main"]
        ]
        output = r9.adapt_output(final, self.registry(), "OUT_SEPARATED")
        self.assertEqual(
            output["comparison_pool_candidate_ids"],
            ["sensory.lemon", "sensory.honey"],
        )
        self.assertEqual(
            output["final_comparison_status"],
            "NOT_EXECUTABLE_EXISTING_3_TO_8_CONTRACT",
        )
        self.assertFalse(output["exposure"]["eligible_for_final_comparison"])

    def test_policy_never_invents_child_for_supported_direction(self):
        final = self.final()
        final["state"]["candidate_scores"] = [
            row
            for row in final["state"]["candidate_scores"]
            if row["candidate_id"] != "sensory.lemon"
        ]
        final["main"] = copy.deepcopy(final["state"]["candidate_scores"][:5])
        final["secondary"] = copy.deepcopy(final["state"]["candidate_scores"][5:8])
        final["exposure"]["candidate_ids"] = [
            row["candidate_id"] for row in final["main"] + final["secondary"]
        ]
        output = r9.adapt_output(final, self.registry(), "OUT_SPECIFIC_FIRST")
        self.assertNotIn("sensory.lemon", output["comparison_pool_candidate_ids"])

    def test_explicit_named_row_and_evidence_are_preserved_without_T(self):
        output = r9.adapt_output(self.final(), self.registry(), "OUT_SEPARATED")
        lemon = next(
            row for row in output["main"] if row["candidate_id"] == "sensory.lemon"
        )
        self.assertTrue(lemon["explicit"])
        self.assertEqual(lemon["evidence_ids"], ["fixture-evidence"])
        self.assertNotIn("T", inspect.signature(r9.adapt_output).parameters)
        self.assertNotIn("target", inspect.signature(r9.adapt_output).parameters)

    def test_T_or_participant_evaluation_in_endpoint_is_rejected(self):
        for key in r9.FORBIDDEN_EVALUATION_KEYS:
            final = self.final()
            final[key] = {}
            with self.assertRaisesRegex(ValueError, "MUST_NOT_RECEIVE"):
                r9.adapt_output(final, self.registry(), "OUT_SEPARATED")

    def test_duplicate_and_inconsistent_original_exposure_are_rejected(self):
        final = self.final()
        final["secondary"][0] = copy.deepcopy(final["main"][0])
        final["exposure"]["candidate_ids"] = [
            row["candidate_id"] for row in final["main"] + final["secondary"]
        ]
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ORIGINAL"):
            r9.adapt_output(final, self.registry(), "OUT_MIXED")
        final = self.final()
        final["exposure"]["candidate_ids"] = list(
            reversed(final["exposure"]["candidate_ids"])
        )
        with self.assertRaisesRegex(ValueError, "EXPOSURE_MUST_MATCH"):
            r9.adapt_output(final, self.registry(), "OUT_MIXED")

    def test_registered_semantics_not_prefix_decides_role(self):
        final = self.final()
        final["state"]["candidate_scores"][0]["candidate_id"] = "concept.direction_x"
        final["main"][0]["candidate_id"] = "concept.direction_x"
        final["exposure"]["candidate_ids"][0] = "concept.direction_x"
        registry = self.registry()
        registry["concept.direction_x"] = {
            "role": r9.PROFILE_DIRECTION,
            "support_dimension_ids": ["fruity"],
        }
        del registry["attribute.fruity"]
        output = r9.adapt_output(final, registry, "OUT_SEPARATED")
        self.assertEqual(
            output["overall_profile"][0]["candidate_id"], "concept.direction_x"
        )

    def test_equivalent_outputs_are_labeled(self):
        first = r9.adapt_output(self.final(), self.registry(), "OUT_SEPARATED")
        second = copy.deepcopy(first)
        self.assertEqual(r9.equivalence(first, second)["status"], "EQUIVALENT_ON_CASE")
        second["overall_profile"] = []
        value = r9.equivalence(first, second)
        self.assertTrue(value["main"])
        self.assertTrue(value["full_return"])
        self.assertFalse(value["overall_profile"])

    def test_repository_contract_registers_all_current_candidate_semantics(self):
        contract = json.loads(
            (
                ROOT
                / "db/data/backend-sequential-model-v2/revisions/r9/output_policy_contract.json"
            ).read_text()
        )
        registry = r9.role_registry_from_contract(contract)
        self.assertTrue(set(r1.PARENTS) <= set(registry))
        self.assertTrue(
            all(
                registry[value]["role"] == r9.NAMED_DESCRIPTOR
                for value in r1.PARENTS
                if value.startswith("sensory.")
            )
        )
        self.assertTrue(
            all(
                registry[value]["role"] == r9.PROFILE_DIRECTION
                for value in r1.PARENTS
                if value.startswith("attribute.")
            )
        )
        self.assertTrue(
            all(
                registry[value]["role"] == r9.NAMED_DESCRIPTOR
                for value in r1.PARENTS
                if value.startswith("broad.")
            )
        )

    def test_zero_fit_evaluator_scores_only_after_outputs_exist(self):
        sources = []
        for generator in ("C00", "C01"):
            sources.append(
                {
                    "record_id": "record-" + generator,
                    "group_id": "coffee-1",
                    "policy": generator,
                    "actual_return": self.final(),
                    "full_T": {"sensory.lemon": 1.0, "sensory.honey": 1.0},
                }
            )
        cells = [
            comparison.detail(source, policy, self.registry())
            for source in sources
            for policy in r9.POLICIES
        ]
        summary = comparison.summarize_cells(cells)
        differences = comparison.difference_summary(sources, cells)
        self.assertEqual(summary["C01"]["OUT_MIXED"]["records"], 1)
        self.assertEqual(
            summary["C01"]["OUT_SEPARATED"]["mechanism_diagnostics"][
                "duplicate_records"
            ],
            0,
        )
        self.assertEqual(differences["case_level_counts"]["C01"]["cases"], 1)
        self.assertEqual(
            differences["case_level_counts"]["C01"][
                "specific_vs_separated_content_difference_without_shortage"
            ],
            0,
        )


if __name__ == "__main__":
    unittest.main()
