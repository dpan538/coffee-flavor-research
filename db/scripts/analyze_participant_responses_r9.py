"""Validate and descriptively summarize real R9 formative-study TSV rows.

No synthetic rows, imputation, calibration, composite score, ANOVA, or model fit
is provided.  Output contains pseudonymous participant IDs and belongs in private
owner-controlled storage, not the public repository.
These observations may describe product comprehension and wording usability only.
They are prohibited as training labels, calibration targets, metric weights,
thresholds, ontology changes, or architecture-selection evidence.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import datetime
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

from flavor_backend import C0, C1
from output_policy_r9 import POLICIES, digest

VERSION = "m2-r9.formative-response.v1"
STAGES = "PRE_OUTPUT>MAIN_POLICY>PROFILE_AB"
CHOICES = {
    "main_fit_rating_1_to_4": {
        "1_NOT_FIT",
        "2_SLIGHTLY_FIT",
        "3_MOSTLY_FIT",
        "4_STRONGLY_FIT",
    },
    "specificity_choice": {"TOO_BROAD", "ABOUT_RIGHT", "TOO_SPECIFIC", "MIXED"},
    "new_expression_help_choice": {"NONE", "A_LITTLE", "SOME", "A_LOT"},
    "information_burden_choice": {
        "TOO_LITTLE",
        "ABOUT_RIGHT",
        "SOMEWHAT_TOO_MUCH",
        "MUCH_TOO_MUCH",
    },
    "profile_effect_choice": {"SUPPLEMENT", "REPEAT", "DISTRACT", "NO_HELP"},
    "profile_pair_order": {"WITH_PROFILE_FIRST", "WITHOUT_PROFILE_FIRST"},
    "previous_study_exposure": {
        "NONE",
        "R8_OR_EARLIER_OUTPUT",
        "PRIOR_R9_PARTICIPANT",
        "OTHER_RECORDED_PRIVATE",
    },
}
REQUIRED = {
    "schema_version",
    "response_row_uid",
    "participant_uid",
    "session_id",
    "cup_task_id",
    "profile_pair_id",
    "coffee_id",
    "preparation_batch_or_condition",
    "coffee_order",
    "generator_id",
    "policy_id",
    "model_bundle_id",
    "answer_state_hash",
    "c0_id",
    "c1_id",
    "qa_transcript_private_ref",
    "pre_output_impression_private_ref",
    "main_candidate_ids_ordered_json",
    "secondary_candidate_ids_ordered_json",
    "main_count",
    "secondary_count",
    "comparison_pool_count",
    "final_comparison_status",
    "profile_candidate_ids_ordered_json",
    "profile_count",
    "output_hash",
    "exposure_stage_sequence",
    "main_fit_rating_1_to_4",
    "specificity_choice",
    "new_expression_help_choice",
    "information_burden_choice",
    "main_feedback_private_ref",
    "profile_pair_order",
    "profile_pair_main_content_hash",
    "profile_pair_profile_ids_ordered_json",
    "profile_effect_choice",
    "profile_feedback_private_ref",
    "main_started_at_utc",
    "main_completed_at_utc",
    "main_duration_seconds",
    "profile_pair_started_at_utc",
    "profile_pair_completed_at_utc",
    "profile_pair_duration_seconds",
    "previous_study_exposure",
}


def _ordered_ids(value: str, field: str) -> list[str]:
    try:
        result = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("INVALID_ORDERED_ID_JSON:" + field) from exc
    if (
        not isinstance(result, list)
        or any(not isinstance(item, str) or not item for item in result)
        or len(result) != len(set(result))
    ):
        raise ValueError("UNIQUE_ORDERED_ID_ARRAY_REQUIRED:" + field)
    return result


def _integer(value: str, field: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError("INTEGER_REQUIRED:" + field) from exc
    if str(parsed) != value:
        raise ValueError("CANONICAL_INTEGER_REQUIRED:" + field)
    return parsed


def _duration(row: dict[str, str], prefix: str) -> float | None:
    fields = [
        row[prefix + "_started_at_utc"],
        row[prefix + "_completed_at_utc"],
        row[prefix + "_duration_seconds"],
    ]
    if not any(fields):
        return None
    if not all(fields):
        raise ValueError("PARTIAL_TIMING_FIELDS:" + prefix)
    try:
        started = datetime.datetime.fromisoformat(fields[0].replace("Z", "+00:00"))
        completed = datetime.datetime.fromisoformat(fields[1].replace("Z", "+00:00"))
        duration = float(fields[2])
    except ValueError as exc:
        raise ValueError("INVALID_TIMING_FIELDS:" + prefix) from exc
    if duration < 0 or completed < started:
        raise ValueError("NEGATIVE_TIMING:" + prefix)
    if abs((completed - started).total_seconds() - duration) > 1.0:
        raise ValueError("TIMING_DURATION_MISMATCH:" + prefix)
    return duration


def validate(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None or set(reader.fieldnames) != REQUIRED:
            missing = sorted(REQUIRED - set(reader.fieldnames or []))
            extra = sorted(set(reader.fieldnames or []) - REQUIRED)
            raise ValueError(f"R9_TSV_SCHEMA_MISMATCH:missing={missing}:extra={extra}")
        raw = list(reader)
    rows = []
    unique = {
        field: set() for field in ("response_row_uid", "cup_task_id", "profile_pair_id")
    }
    participant_policy: dict[str, set[str]] = defaultdict(set)
    session_participant: dict[str, set[str]] = defaultdict(set)
    participant_orders: dict[str, set[int]] = defaultdict(set)
    for line, row in enumerate(raw, 2):
        for field in REQUIRED:
            if (
                field
                not in {
                    "main_feedback_private_ref",
                    "profile_feedback_private_ref",
                    "main_started_at_utc",
                    "main_completed_at_utc",
                    "main_duration_seconds",
                    "profile_pair_started_at_utc",
                    "profile_pair_completed_at_utc",
                    "profile_pair_duration_seconds",
                }
                and not row[field]
            ):
                raise ValueError(f"REQUIRED_VALUE_MISSING:{field}:line={line}")
        if row["schema_version"] != VERSION:
            raise ValueError("R9_RESPONSE_VERSION_MISMATCH")
        if row["generator_id"] != "C01":
            raise ValueError("R9_FORMATIVE_STUDY_REQUIRES_FROZEN_C01")
        if row["policy_id"] not in POLICIES:
            raise ValueError("REGISTERED_OUTPUT_POLICY_REQUIRED")
        if row["c0_id"] not in C0 or row["c1_id"] not in C1:
            raise ValueError("EXACT_C0_C1_REQUIRED")
        if row["exposure_stage_sequence"] != STAGES:
            raise ValueError("R9_EXPOSURE_SEQUENCE_REQUIRED")
        for field, allowed in CHOICES.items():
            if row[field] not in allowed:
                raise ValueError("REGISTERED_RESPONSE_CHOICE_REQUIRED:" + field)
        for field, seen in unique.items():
            if row[field] in seen:
                raise ValueError("DUPLICATE_GLOBAL_ROW_OR_PAIR_ID:" + field)
            seen.add(row[field])

        main = _ordered_ids(row["main_candidate_ids_ordered_json"], "main")
        secondary = _ordered_ids(
            row["secondary_candidate_ids_ordered_json"], "secondary"
        )
        profile = _ordered_ids(row["profile_candidate_ids_ordered_json"], "profile")
        profile_pair = _ordered_ids(
            row["profile_pair_profile_ids_ordered_json"], "profile_pair"
        )
        pool = main + secondary
        if len(pool) != len(set(pool)):
            raise ValueError("DUPLICATE_MAIN_SECONDARY_ID")
        if set(pool) & set(profile):
            raise ValueError("PROFILE_OVERLAPS_ASSIGNED_COMPARISON_POOL")
        expected_counts = (len(main), len(secondary), len(pool), len(profile))
        recorded_counts = tuple(
            _integer(row[field], field)
            for field in (
                "main_count",
                "secondary_count",
                "comparison_pool_count",
                "profile_count",
            )
        )
        if expected_counts != recorded_counts:
            raise ValueError("RECORDED_OUTPUT_COUNT_MISMATCH")
        if len(main) > 5 or len(secondary) > 3 or len(pool) > 8 or len(profile) > 3:
            raise ValueError("R9_OUTPUT_BUDGET_VIOLATION")
        expected_status = (
            "ELIGIBLE"
            if 3 <= len(pool) <= 8
            else "NOT_EXECUTABLE_EXISTING_3_TO_8_CONTRACT"
        )
        if row["final_comparison_status"] != expected_status:
            raise ValueError("FINAL_COMPARISON_STATUS_MISMATCH")
        if len(profile_pair) > 3:
            raise ValueError("PROFILE_PAIR_BUDGET_VIOLATION")
        if row["profile_pair_main_content_hash"] != digest(
            {"main": main, "secondary": secondary}
        ):
            raise ValueError("PROFILE_PAIR_CHANGED_MAIN_CONTENT")
        for field in ("answer_state_hash", "output_hash"):
            if len(row[field]) != 64 or any(
                c not in "0123456789abcdef" for c in row[field]
            ):
                raise ValueError("SHA256_REQUIRED:" + field)

        coffee_order = _integer(row["coffee_order"], "coffee_order")
        if coffee_order not in {1, 2}:
            raise ValueError("ONE_OR_TWO_COFFEE_ORDER_REQUIRED")
        if coffee_order in participant_orders[row["participant_uid"]]:
            raise ValueError("DUPLICATE_PARTICIPANT_COFFEE_ORDER")
        participant_orders[row["participant_uid"]].add(coffee_order)
        participant_policy[row["participant_uid"]].add(row["policy_id"])
        session_participant[row["session_id"]].add(row["participant_uid"])
        enriched: dict[str, Any] = dict(row)
        enriched.update(
            main_ids=main,
            secondary_ids=secondary,
            profile_ids=profile,
            profile_pair_ids=profile_pair,
            coffee_order_value=coffee_order,
            main_fit_value=int(row["main_fit_rating_1_to_4"].split("_", 1)[0]),
            main_duration_value=_duration(row, "main"),
            profile_pair_duration_value=_duration(row, "profile_pair"),
        )
        rows.append(enriched)
    if any(len(values) != 1 for values in participant_policy.values()):
        raise ValueError("PARTICIPANT_EXPOSED_TO_MULTIPLE_MAIN_POLICIES")
    if any(len(values) != 1 for values in session_participant.values()):
        raise ValueError("SESSION_ID_COLLIDES_ACROSS_PARTICIPANTS")
    if any(not 1 <= len(values) <= 2 for values in participant_orders.values()):
        raise ValueError("PARTICIPANT_MUST_HAVE_ONE_OR_TWO_COFFEE_TASKS")
    return rows


def categorical(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in rows).items()))


def summarize(rows: list[dict[str, Any]], source_sha256: str) -> dict[str, Any]:
    if not rows:
        return {
            "version": VERSION,
            "status": "NO_REAL_RESPONSES",
            "source_sha256": source_sha256,
            "participants": 0,
            "coffee_tasks": 0,
            "real_feedback": "NOT_EVALUATED",
            "permitted_use": "PRODUCT_COMPREHENSION_AND_WORDING_USABILITY_ONLY",
            "model_training_or_architecture_input": "PROHIBITED",
            "fit_count": 0,
        }
    by_participant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_coffee: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_policy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_participant[row["participant_uid"]].append(row)
        by_coffee[row["coffee_id"]].append(row)
        by_policy[row["policy_id"]].append(row)
    participant_results = []
    for participant, values in sorted(by_participant.items()):
        participant_results.append(
            {
                "participant_uid": participant,
                "policy_id": values[0]["policy_id"],
                "coffee_tasks": len(values),
                "main_fit_mean": statistics.fmean(
                    row["main_fit_value"] for row in values
                ),
                "specificity": categorical(values, "specificity_choice"),
                "new_expression_help": categorical(
                    values, "new_expression_help_choice"
                ),
                "information_burden": categorical(values, "information_burden_choice"),
                "profile_effect": categorical(values, "profile_effect_choice"),
            }
        )
    policy_results = {}
    for policy_id, values in sorted(by_policy.items()):
        participants = [
            row for row in participant_results if row["policy_id"] == policy_id
        ]
        policy_results[policy_id] = {
            "participants": len(participants),
            "coffee_tasks": len(values),
            "main_fit_mean_of_participant_means": statistics.fmean(
                row["main_fit_mean"] for row in participants
            ),
            "cup_level_specificity_distribution": categorical(
                values, "specificity_choice"
            ),
            "cup_level_new_expression_help_distribution": categorical(
                values, "new_expression_help_choice"
            ),
            "cup_level_information_burden_distribution": categorical(
                values, "information_burden_choice"
            ),
            "cup_level_profile_effect_distribution": categorical(
                values, "profile_effect_choice"
            ),
        }
    coffee_results = {
        coffee: {
            "coffee_tasks": len(values),
            "policy_distribution": categorical(values, "policy_id"),
            "main_fit_distribution": categorical(values, "main_fit_rating_1_to_4"),
            "specificity_distribution": categorical(values, "specificity_choice"),
            "profile_effect_distribution": categorical(values, "profile_effect_choice"),
        }
        for coffee, values in sorted(by_coffee.items())
    }
    return {
        "version": VERSION,
        "status": "REAL_FORMATIVE_RESPONSES_DESCRIBED",
        "source_sha256": source_sha256,
        "participants": len(by_participant),
        "coffee_tasks": len(rows),
        "coffees": len(by_coffee),
        "participant_results": participant_results,
        "coffee_results": coffee_results,
        "policy_results": policy_results,
        "sample_size_note": "Observed formative range only; not a powered confirmation sample.",
        "inference": "NOT_RUN_DESCRIPTIVE_ONLY",
        "composite_score": "NOT_DEFINED",
        "calibration_or_metric_weight_fit": "NOT_RUN",
        "permitted_use": "PRODUCT_COMPREHENSION_AND_WORDING_USABILITY_ONLY",
        "model_training_or_architecture_input": "PROHIBITED",
        "fit_count": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = validate(args.responses)
    source_hash = hashlib.sha256(args.responses.read_bytes()).hexdigest()
    result = summarize(rows, source_hash)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "fit_count": 0}))


if __name__ == "__main__":
    main()
