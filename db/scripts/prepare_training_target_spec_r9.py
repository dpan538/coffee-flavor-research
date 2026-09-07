#!/usr/bin/env python3
"""Write a zero-fit draft target specification for a separately authorized round.

The artifact defines candidate objectives and the data needed to make them
estimable.  It deliberately leaves empirical weights and numerical thresholds
unset because R9 has no real participant evidence and training remains paused.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from acquire_supervision_r5 import save

ROOT = Path(__file__).resolve().parents[2]
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.future-training-target-spec.v1"


def specification(decision: dict, contract: dict) -> dict:
    owner = decision["owner_decision"]
    if (
        owner.get("status") != "OWNER_APPROVED"
        or owner.get("approved_policy") != "OUT_SEPARATED"
    ):
        raise ValueError("OUT_SEPARATED_OWNER_APPROVAL_REQUIRED")
    if contract["training_pause"]["fit_count"] != 0:
        raise ValueError("R9_ZERO_FIT_CONTRACT_REQUIRED")
    return {
        "version": VERSION,
        "status": "DRAFT_FOR_FUTURE_ROUND_NOT_AUTHORIZED_FOR_EXECUTION",
        "policy": "OUT_SEPARATED",
        "owner_approval_utc": owner["approved_utc"],
        "fit_count": 0,
        "training_authorized": False,
        "training_freeze_condition": (
            "R9_OVERRIDE_REMAINS_IN_EFFECT; separate owner authorization is required "
            "even though the output-role contract is approved."
        ),
        "role_objectives": {
            "NAMED_DESCRIPTOR": {
                "output": "main<=5 then secondary<=3",
                "candidate_objective": "Rank independently evidence-supported named descriptors above unsupported named descriptors.",
                "hard_constraints": [
                    "preserve legal explicit user expressions",
                    "do not infer a child solely from parent support",
                    "return short instead of inventing a descriptor",
                ],
            },
            "PROFILE_DIRECTION": {
                "output": "overall_profile<=3 outside the 5+3 comparison budget",
                "candidate_objective": "Select independently supported whole-profile directions without expanding them into children.",
            },
            "OTHER_NATIVE_MEASUREMENT": {
                "output": "excluded from flavor output",
                "hard_metric": "native_measurement_leakage_rate=0",
            },
        },
        "candidate_losses_not_yet_approved": {
            "named_descriptor_ranking": {
                "candidate_form": (
                    "For coffee task t with independent nonnegative relevance y[t,c], "
                    "L_rank=-sum_c normalize(y[t,c])*log_softmax(score[t,*])[c]."
                ),
                "label_requirement": (
                    "Descriptor-level relevance collected independently before model-word "
                    "exposure; post-output acceptance is not independent sensory truth."
                ),
                "status": "FORM_DEFINED_WEIGHTS_AND_LABEL_PROTOCOL_NOT_APPROVED",
            },
            "profile_direction": {
                "candidate_form": (
                    "Binary cross-entropy over the nine registered directions, evaluated "
                    "separately as recall and false-positive burden at the fixed top-3 output."
                ),
                "label_requirement": (
                    "Direction labels independent of the same K1 rule being evaluated; K1 "
                    "self-reproduction cannot count as confirmation."
                ),
                "status": "FORM_DEFINED_LABEL_SOURCE_NOT_AVAILABLE",
            },
            "specificity_risk": {
                "candidate_form": (
                    "Descriptor-level penalty only when a real judgment labels a returned "
                    "descriptor TOO_SPECIFIC or MISLEADING for that coffee task."
                ),
                "label_requirement": (
                    "Per-descriptor judgment with exposure stage and broad/sibling evidence "
                    "path retained; whole-output specificity is insufficient as a leaf label."
                ),
                "status": "NOT_ESTIMABLE_FROM_CURRENT_R9_TEMPLATE",
            },
        },
        "composite_objective": {
            "status": "NOT_DEFINED",
            "reason": "No owner-approved tradeoff weights exist for fit, specificity, expression help, burden and profile value.",
        },
        "data_requirements": {
            "new_independent_coffee_groups_minimum": "NOT_SET_REQUIRES_PRECISION_POWER_AND_FEASIBILITY_JUSTIFICATION",
            "required_fields": [
                "globally unique participant_uid",
                "session_id",
                "coffee_id and preparation batch/condition",
                "C0 exact existing family",
                "C1 exact existing level",
                "ordered questions and answers",
                "pre-output raw impression",
                "candidate IDs, evidence paths and exposure positions",
                "descriptor-level relevance and specificity judgments when used as labels",
                "previous-study exposure",
            ],
            "dependency_structure": [
                "retain repeated observations within participant",
                "retain repeated observations within coffee",
                "never analyze rating rows as independent samples",
            ],
            "split_requirements": [
                "split by coffee group before any model or weight selection",
                "audit participant overlap and model it when participants taste multiple coffees",
                "reserve a confirmation set unused for objective, threshold or policy selection",
            ],
        },
        "acceptance_contract": {
            "hard_zero_tolerance": {
                "duplicate_output_ids": 0,
                "OTHER_NATIVE_MEASUREMENT_leakage": 0,
                "invented_child_descriptors": 0,
                "T_or_participant_rating_read_by_output_policy": 0,
                "mixed_reference_regression_when_replaying_OUT_MIXED": 0,
            },
            "empirical_thresholds": {
                "descriptor_ranking": "NOT_SET",
                "profile_direction": "NOT_SET",
                "specificity_risk": "NOT_SET",
                "user_fit_help_and_burden": "REPORT_SEPARATELY_NO_COMPOSITE",
            },
            "threshold_setting_rule": (
                "Pre-register after real label reliability, variance and feasible sample size "
                "are known; do not select and confirm on the same data."
            ),
            "automatic_approval": False,
        },
        "prohibited_shortcuts": [
            "AUC>0.6 or gain>0.02 as automatic approval",
            "random gap or NDCG values",
            "synthetic preference fitting",
            "using post-output word recognition as pre-output sensory truth",
            "selecting weights and claiming independent calibration on the same observations",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--decision",
        type=Path,
        default=R9_PUBLIC / "decision_record.json",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=R9_PUBLIC / "output_policy_contract.json",
    )
    args = parser.parse_args()
    value = specification(
        json.loads(args.decision.read_text()), json.loads(args.contract.read_text())
    )
    artifact = save(args.output, value)
    print(
        json.dumps(
            {
                "status": value["status"],
                "fit_count": 0,
                "training_authorized": False,
                "sha256": artifact["sha256"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
