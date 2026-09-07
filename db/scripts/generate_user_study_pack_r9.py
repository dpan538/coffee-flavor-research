#!/usr/bin/env python3
"""Prepare or materialize the private R9 OUT_SEPARATED formative-study pack.

``prepare`` creates a deterministic 12-person/2-cup assignment sheet with no
invented identities, coffees, answers, outputs or ratings.  ``materialize``
accepts owner-supplied live C01 final results and writes response rows with the
real output fields filled and judgments left blank.  Neither mode fits anything.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from flavor_backend import C0, C1
from output_policy_r9 import adapt_output, digest, role_registry_from_contract

ROOT = Path(__file__).resolve().parents[2]
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
ASSIGNMENT_VERSION = "m2-r9.formative-assignment.v1"
RESPONSE_VERSION = "m2-r9.formative-response.v1"
POLICY = "OUT_SEPARATED"
STAGES = "PRE_OUTPUT>MAIN_POLICY>PROFILE_AB"
ASSIGNMENT_FIELDS = [
    "assignment_version",
    "assignment_status",
    "participant_slot_id",
    "participant_uid",
    "session_id",
    "coffee_id",
    "preparation_batch_or_condition",
    "coffee_order",
    "policy_id",
    "profile_pair_order",
    "previous_study_exposure",
    "live_c01_result_private_ref",
    "pre_output_impression_private_ref",
]


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def prepare_rows(
    participants: int, coffees_per_participant: int
) -> list[dict[str, str]]:
    if participants < 9 or participants > 12:
        raise ValueError("FORMATIVE_PARTICIPANTS_MUST_BE_9_TO_12")
    if coffees_per_participant not in {1, 2}:
        raise ValueError("ONE_OR_TWO_COFFEES_PER_PARTICIPANT_REQUIRED")
    rows = []
    for participant_index in range(participants):
        pair_order = (
            "WITH_PROFILE_FIRST"
            if participant_index % 2 == 0
            else "WITHOUT_PROFILE_FIRST"
        )
        for coffee_order in range(1, coffees_per_participant + 1):
            rows.append(
                {
                    "assignment_version": ASSIGNMENT_VERSION,
                    "assignment_status": "UNASSIGNED_NO_REAL_DATA",
                    "participant_slot_id": f"R9_SLOT_{participant_index + 1:02d}",
                    "participant_uid": "",
                    "session_id": "",
                    "coffee_id": "",
                    "preparation_batch_or_condition": "",
                    "coffee_order": str(coffee_order),
                    "policy_id": POLICY,
                    "profile_pair_order": pair_order,
                    "previous_study_exposure": "",
                    "live_c01_result_private_ref": "",
                    "pre_output_impression_private_ref": "",
                }
            )
    return rows


def _ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["candidate_id"] for row in rows]


def _identifier(prefix: str, values: Any) -> str:
    return prefix + "-" + digest(values)[:24]


def materialize_rows(
    tasks: list[dict[str, Any]], registry: dict[str, Any], response_fields: list[str]
) -> list[dict[str, str]]:
    participants = {task.get("participant_uid") for task in tasks}
    if None in participants or "" in participants or not 9 <= len(participants) <= 12:
        raise ValueError("NINE_TO_TWELVE_REAL_PSEUDONYMOUS_PARTICIPANTS_REQUIRED")
    counts = {participant: 0 for participant in participants}
    orders = {participant: set() for participant in participants}
    pair_orders: dict[str, str] = {}
    rows = []
    for task in tasks:
        required = {
            "participant_uid",
            "session_id",
            "coffee_id",
            "preparation_batch_or_condition",
            "coffee_order",
            "previous_study_exposure",
            "qa_transcript_private_ref",
            "pre_output_impression_private_ref",
            "actual_c01_return",
        }
        missing = sorted(
            key for key in required if task.get(key) is None or task.get(key) == ""
        )
        if missing:
            raise ValueError("REAL_TASK_FIELDS_REQUIRED:" + ",".join(missing))
        participant = task["participant_uid"]
        coffee_order = int(task["coffee_order"])
        counts[participant] += 1
        if (
            counts[participant] > 2
            or coffee_order not in {1, 2}
            or coffee_order in orders[participant]
        ):
            raise ValueError("ONE_OR_TWO_COFFEE_TASKS_PER_PARTICIPANT")
        orders[participant].add(coffee_order)
        final = task["actual_c01_return"]
        state = final.get("state", {})
        base = state.get("base_state", {})
        context = base.get("context", {})
        if context.get("c0") not in C0 or context.get("c1") not in C1:
            raise ValueError("LIVE_C01_RESULT_REQUIRES_EXACT_C0_C1")
        if base.get("policy") != "fixed" or final.get("stage") != "PRELIMINARY_RESULT":
            raise ValueError("FROZEN_C01_PRELIMINARY_RESULT_REQUIRED")
        if base.get("final_comparison"):
            raise ValueError("SECOND_FINAL_COMPARISON_NOT_ALLOWED")
        output = adapt_output(final, registry, POLICY)
        main = _ids(output["main"])
        secondary = _ids(output["secondary"])
        profile = _ids(output["overall_profile"])
        participant_position = sorted(participants).index(participant)
        pair_order = (
            "WITH_PROFILE_FIRST"
            if participant_position % 2 == 0
            else "WITHOUT_PROFILE_FIRST"
        )
        if participant in pair_orders and pair_orders[participant] != pair_order:
            raise ValueError("PROFILE_PAIR_ORDER_CHANGED_WITHIN_PARTICIPANT")
        pair_orders[participant] = pair_order
        identity = {
            "participant_uid": participant,
            "session_id": task["session_id"],
            "coffee_id": task["coffee_id"],
            "coffee_order": coffee_order,
        }
        values = dict.fromkeys(response_fields, "")
        values.update(
            schema_version=RESPONSE_VERSION,
            response_row_uid=_identifier("response", identity),
            participant_uid=participant,
            session_id=task["session_id"],
            cup_task_id=_identifier("cup", identity),
            profile_pair_id=_identifier("profile-pair", identity),
            coffee_id=task["coffee_id"],
            preparation_batch_or_condition=task["preparation_batch_or_condition"],
            coffee_order=str(coffee_order),
            generator_id="C01",
            policy_id=POLICY,
            model_bundle_id=output["exposure"]["generation_version"],
            answer_state_hash=output["exposure"]["state_hash"],
            c0_id=context["c0"],
            c1_id=context["c1"],
            qa_transcript_private_ref=task["qa_transcript_private_ref"],
            pre_output_impression_private_ref=task["pre_output_impression_private_ref"],
            main_candidate_ids_ordered_json=json.dumps(main, separators=(",", ":")),
            secondary_candidate_ids_ordered_json=json.dumps(
                secondary, separators=(",", ":")
            ),
            main_count=str(len(main)),
            secondary_count=str(len(secondary)),
            comparison_pool_count=str(len(main + secondary)),
            final_comparison_status=output["final_comparison_status"],
            profile_candidate_ids_ordered_json=json.dumps(
                profile, separators=(",", ":")
            ),
            profile_count=str(len(profile)),
            output_hash=output["output_hash"],
            exposure_stage_sequence=STAGES,
            profile_pair_order=pair_order,
            profile_pair_main_content_hash=digest(
                {"main": main, "secondary": secondary}
            ),
            profile_pair_profile_ids_ordered_json=json.dumps(
                profile, separators=(",", ":")
            ),
            previous_study_exposure=task["previous_study_exposure"],
        )
        rows.append(values)
    if any(count not in {1, 2} for count in counts.values()):
        raise ValueError("ONE_OR_TWO_COFFEE_TASKS_PER_PARTICIPANT")
    return rows


def response_fields() -> list[str]:
    with (R9_PUBLIC / "participant_task_and_response_template.tsv").open(
        newline="", encoding="utf-8"
    ) as handle:
        fields = next(csv.reader(handle, delimiter="\t"))
    return fields


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--participants", type=int, default=12)
    prepare.add_argument("--coffees-per-participant", type=int, default=2)
    materialize = sub.add_parser("materialize")
    materialize.add_argument("--task-input", type=Path, required=True)
    materialize.add_argument("--output", type=Path, required=True)
    materialize.add_argument(
        "--contract",
        type=Path,
        default=R9_PUBLIC / "output_policy_contract.json",
    )
    args = parser.parse_args()
    if args.operation == "prepare":
        rows = prepare_rows(args.participants, args.coffees_per_participant)
        write_tsv(args.output, ASSIGNMENT_FIELDS, rows)
        status = "READY_FOR_OWNER_ASSIGNMENT_NO_REAL_DATA"
    else:
        tasks = json.loads(args.task_input.read_text())
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("NONEMPTY_REAL_TASK_ARRAY_REQUIRED")
        registry = role_registry_from_contract(json.loads(args.contract.read_text()))
        fields = response_fields()
        rows = materialize_rows(tasks, registry, fields)
        write_tsv(args.output, fields, rows)
        status = "REAL_TASK_OUTPUTS_MATERIALIZED_JUDGMENTS_BLANK"
    print(
        json.dumps(
            {
                "status": status,
                "rows": len(rows),
                "policy_id": POLICY,
                "fit_count": 0,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
