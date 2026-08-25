#!/usr/bin/env python3
"""Validate empty or populated Round 3D capture CSVs before staging."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


EXPECTED = {
    "coffee_lots.csv": "study_key,protocol_version_key,coffee_lot_key,public_lot_code,material_source_code,harvest_period,origin_country_code,process_code,received_on,rights_status,data_quality_flags",
    "roast_batches.csv": "study_key,protocol_version_key,roast_batch_key,coffee_lot_key,roast_category_key,batch_code,roasted_on,roaster_code,whole_bean_color_method,whole_bean_color_value,ground_color_method,ground_color_value,roast_metadata_json,data_quality_flags",
    "preparation_conditions.csv": "study_key,protocol_version_key,preparation_condition_key,preparation_concept_key,condition_code,coffee_mode_code,paired_black_condition_key,recipe_json,equipment_code,water_code,milk_code,data_quality_flags",
    "beverage_samples.csv": "study_key,protocol_version_key,beverage_sample_key,coffee_lot_key,roast_batch_key,preparation_condition_key,replicate_number,prepared_at,operator_code,dose_g,water_g,beverage_g,temperature_c,time_seconds,grind_setting,deviation_code,record_origin_code,data_quality_flags",
    "assessors.csv": "study_key,protocol_version_key,assessor_key,pseudonymous_code,cohort_code,language_tag_code,expertise_band,experience_category,consent_version_code,public_release_eligible,record_origin_code,data_quality_flags",
    "sessions.csv": "study_key,protocol_version_key,session_key,assessor_key,session_number,started_at,completed_at,randomization_schedule_key,withdrawal_status,record_origin_code,data_quality_flags",
    "presentations.csv": "study_key,protocol_version_key,presentation_key,session_key,beverage_sample_key,sequence_position,blinded_code,presented_at,repeat_identity_code,serving_temperature_c,record_origin_code,data_quality_flags",
    "descriptor_responses.csv": "study_key,protocol_version_key,presentation_key,sensory_observation_key,concept_key,response_code,intensity_value,confidence_value,response_time_ms,record_origin_code,data_quality_flags",
    "dimension_responses.csv": "study_key,protocol_version_key,presentation_key,sensory_observation_key,dimension_key,value,confidence_value,response_time_ms,record_origin_code,data_quality_flags",
    "question_responses.csv": "study_key,protocol_version_key,presentation_key,question_assignment_key,question_key,question_version,step_number,option_code,selection_order,response_status_code,response_time_ms,policy_code,uncertainty_before,uncertainty_after,stopped_after_response,explicit_context_override,record_origin_code,data_quality_flags",
    "candidate_judgments.csv": "study_key,protocol_version_key,presentation_key,concept_key,candidate_tier_code,rank_position,usefulness_code,judgment_confidence,response_time_ms,record_origin_code,data_quality_flags",
    "protocol_deviations.csv": "study_key,protocol_version_key,deviation_key,session_key,beverage_sample_key,deviation_code,severity_code,occurred_at,resolution_code,exclude_from_analysis,record_origin_code,data_quality_flags",
}
PII = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+?[0-9][0-9 ()-]{7,}[0-9]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("--ethics-gate", action="store_true")
    parser.add_argument("--consent-ready", action="store_true")
    parser.add_argument("--release-rights-ready", action="store_true")
    args = parser.parse_args()

    row_count = 0
    real_count = 0
    for name, header in EXPECTED.items():
        path = args.capture_dir / name
        if not path.is_file():
            raise SystemExit(f"CAPTURE_VALIDATION_ERROR=missing:{name}")
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != header.split(","):
                raise SystemExit(f"CAPTURE_VALIDATION_ERROR=header:{name}")
            for row in reader:
                row_count += 1
                serialized = json.dumps(row, ensure_ascii=False)
                if PII.search(serialized):
                    raise SystemExit(f"CAPTURE_VALIDATION_ERROR=direct_identifier:{name}")
                origin = row.get("record_origin_code", "")
                if origin == "real_observation":
                    real_count += 1
                elif origin and origin not in {"DRY_RUN_FIXTURE", "TEST_FIXTURE"}:
                    raise SystemExit(f"CAPTURE_VALIDATION_ERROR=origin:{name}")

    if real_count and not (
        args.ethics_gate and args.consent_ready and args.release_rights_ready
    ):
        raise SystemExit("CAPTURE_VALIDATION_ERROR=real_data_governance_gate_closed")

    print(f"CAPTURE_ROW_COUNT={row_count}")
    print(f"REAL_CAPTURE_ROW_COUNT={real_count}")
    print("CAPTURE_SCHEMA_PASS=true")
    print("CAPTURE_PII_SCAN_PASS=true")
    print("CAPTURE_GOVERNANCE_GATE_PASS=true")


if __name__ == "__main__":
    main()
