"""R9 response-processing tests use synthetic schema rows, never effect evidence."""

import copy
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import analyze_participant_responses_r9 as study
from output_policy_r9 import digest


class ParticipantResponseTests(unittest.TestCase):
    template = (
        ROOT
        / "db/data/backend-sequential-model-v2/revisions/r9"
        / "participant_task_and_response_template.tsv"
    )

    def fields(self):
        with self.template.open(newline="") as handle:
            return next(csv.reader(handle, delimiter="\t"))

    def row(self):
        main = ["sensory.lemon", "sensory.jasmine", "broad.citrus"]
        secondary = ["sensory.honey"]
        profile = ["attribute.fruity", "attribute.floral"]
        values = dict.fromkeys(self.fields(), "")
        values.update(
            schema_version=study.VERSION,
            response_row_uid="response-global-001",
            participant_uid="participant-global-001",
            session_id="session-global-001",
            cup_task_id="cup-task-global-001",
            profile_pair_id="profile-pair-global-001",
            coffee_id="coffee-001",
            preparation_batch_or_condition="batch-001/filter-recipe-001",
            coffee_order="1",
            generator_id="C01",
            policy_id="OUT_SEPARATED",
            model_bundle_id="frozen-C01-bundle",
            answer_state_hash="a" * 64,
            c0_id="preparation.family.filter_percolation",
            c1_id="medium",
            qa_transcript_private_ref="private://qa/session-global-001",
            pre_output_impression_private_ref="private://impression/cup-task-global-001",
            main_candidate_ids_ordered_json=json.dumps(main),
            secondary_candidate_ids_ordered_json=json.dumps(secondary),
            main_count=str(len(main)),
            secondary_count=str(len(secondary)),
            comparison_pool_count=str(len(main + secondary)),
            final_comparison_status="ELIGIBLE",
            profile_candidate_ids_ordered_json=json.dumps(profile),
            profile_count=str(len(profile)),
            output_hash="b" * 64,
            exposure_stage_sequence=study.STAGES,
            main_fit_rating_1_to_4="3_MOSTLY_FIT",
            specificity_choice="ABOUT_RIGHT",
            new_expression_help_choice="SOME",
            information_burden_choice="ABOUT_RIGHT",
            profile_pair_order="WITH_PROFILE_FIRST",
            profile_pair_main_content_hash=digest(
                {"main": main, "secondary": secondary}
            ),
            profile_pair_profile_ids_ordered_json=json.dumps(profile),
            profile_effect_choice="SUPPLEMENT",
            previous_study_exposure="NONE",
        )
        return values

    def write(self, rows):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".tsv", newline="", delete=False
        )
        with handle:
            writer = csv.DictWriter(handle, fieldnames=self.fields(), delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        self.addCleanup(Path(handle.name).unlink, missing_ok=True)
        return Path(handle.name)

    def test_blank_checked_in_template_is_valid_and_not_evaluated(self):
        rows = study.validate(self.template)
        self.assertEqual(rows, [])
        summary = study.summarize(rows, "f" * 64)
        self.assertEqual(summary["real_feedback"], "NOT_EVALUATED")
        self.assertEqual(summary["fit_count"], 0)

    def test_one_real_shaped_row_retains_participant_and_coffee(self):
        rows = study.validate(self.write([self.row()]))
        result = study.summarize(rows, "f" * 64)
        self.assertEqual(result["participants"], 1)
        self.assertEqual(result["coffee_tasks"], 1)
        self.assertIn("participant-global-001", str(result["participant_results"]))
        self.assertIn("coffee-001", result["coffee_results"])
        self.assertEqual(result["inference"], "NOT_RUN_DESCRIPTIVE_ONLY")
        self.assertEqual(result["composite_score"], "NOT_DEFINED")

    def test_same_participant_cannot_cross_policy_groups(self):
        first = self.row()
        second = copy.deepcopy(first)
        second.update(
            response_row_uid="response-global-002",
            cup_task_id="cup-task-global-002",
            profile_pair_id="profile-pair-global-002",
            coffee_id="coffee-002",
            coffee_order="2",
            policy_id="OUT_MIXED",
        )
        with self.assertRaisesRegex(ValueError, "MULTIPLE_MAIN_POLICIES"):
            study.validate(self.write([first, second]))

    def test_pair_id_and_output_counts_cannot_be_silently_pivoted(self):
        first = self.row()
        second = copy.deepcopy(first)
        second["response_row_uid"] = "response-global-002"
        with self.assertRaisesRegex(ValueError, "DUPLICATE_GLOBAL"):
            study.validate(self.write([first, second]))
        wrong = self.row()
        wrong["main_count"] = "2"
        with self.assertRaisesRegex(ValueError, "COUNT_MISMATCH"):
            study.validate(self.write([wrong]))

    def test_missing_C1_and_random_generator_are_rejected(self):
        missing = self.row()
        missing["c1_id"] = ""
        with self.assertRaisesRegex(ValueError, "REQUIRED_VALUE_MISSING:c1_id"):
            study.validate(self.write([missing]))
        wrong = self.row()
        wrong["generator_id"] = "C00"
        with self.assertRaisesRegex(ValueError, "REQUIRES_FROZEN_C01"):
            study.validate(self.write([wrong]))

    def test_partial_or_fabricated_timing_is_rejected(self):
        row = self.row()
        row["main_duration_seconds"] = "12"
        with self.assertRaisesRegex(ValueError, "PARTIAL_TIMING"):
            study.validate(self.write([row]))


if __name__ == "__main__":
    unittest.main()
