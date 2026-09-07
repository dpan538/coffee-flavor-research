#!/usr/bin/env python3
"""Write a zero-fit semantic target draft for a separately authorized round.

The draft permits only provenance-backed semantic evidence, identifiers, concept
roles, explicit descriptor relations and hard inference constraints as future
model inputs. Participant preference, satisfaction, perceived fit and other
subjective evaluations are prohibited as training or architecture inputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from acquire_supervision_r5 import save

ROOT = Path(__file__).resolve().parents[2]
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.future-training-target-spec.v2"


def specification(decision: dict, contract: dict) -> dict:
    owner = decision["owner_decision"]
    if (
        owner.get("status") != "OWNER_APPROVED"
        or owner.get("approved_policy") != "OUT_SEPARATED"
    ):
        raise ValueError("OUT_SEPARATED_OWNER_APPROVAL_REQUIRED")
    if contract["training_pause"]["fit_count"] != 0:
        raise ValueError("R9_ZERO_FIT_CONTRACT_REQUIRED")
    governance = contract.get("semantic_model_governance", {})
    if governance.get("status") != "OWNER_REQUIRED_CONSTRAINT":
        raise ValueError("SEMANTIC_MODEL_GOVERNANCE_REQUIRED")
    return {
        "version": VERSION,
        "status": "DRAFT_FOR_FUTURE_ROUND_NOT_AUTHORIZED_FOR_EXECUTION",
        "policy": "OUT_SEPARATED",
        "owner_approval_utc": owner["approved_utc"],
        "fit_count": 0,
        "training_authorized": False,
        "training_freeze_condition": (
            "R9_OVERRIDE_REMAINS_IN_EFFECT; separate owner authorization is required "
            "even though the output-role and semantic-governance contracts are approved."
        ),
        "semantic_training_governance": {
            "system_type": governance["system_type"],
            "authoritative_inputs": governance["authoritative_inputs"],
            "prohibited_model_or_architecture_inputs": governance[
                "prohibited_model_or_architecture_inputs"
            ],
            "prohibited_uses": governance["prohibited_uses"],
            "external_subjective_evaluation_dependency": "PROHIBITED",
            "optional_human_observation_scope": governance[
                "optional_human_observation_scope"
            ],
        },
        "role_objectives": {
            "NAMED_DESCRIPTOR": {
                "output": "main<=5 then secondary<=3",
                "candidate_objective": (
                    "Rank named descriptors by auditable semantic evidence and registered "
                    "relations; never convert direction compatibility into child confirmation."
                ),
                "hard_constraints": [
                    "preserve legal explicit user expressions",
                    "require direct evidence or an explicit provenance-backed descriptor relation for strict assertion",
                    "do not infer a child or sibling solely from shared dimension support",
                    "return short instead of inventing a descriptor",
                ],
            },
            "PROFILE_DIRECTION": {
                "output": "overall_profile<=3 outside the 5+3 comparison budget",
                "candidate_objective": (
                    "Select supported whole-profile directions without expanding them into "
                    "children."
                ),
            },
            "OTHER_NATIVE_MEASUREMENT": {
                "output": "excluded from flavor output",
                "hard_metric": "native_measurement_leakage_rate=0",
            },
        },
        "future_internal_objectives_not_authorized": {
            "evidence_trace_order": {
                "candidate_form": (
                    "Pairwise or constrained ordering over categorical trace states: direct "
                    "descriptor evidence or a registered descriptor relation precedes "
                    "direction-only compatibility, which precedes no current semantic trace."
                ),
                "weight_policy": (
                    "No 1.0/0.6/0.4 scalar or other tradeoff weight is adopted in R9."
                ),
                "label_source": (
                    "Versioned question-answer evidence state and provenance-backed explicit "
                    "descriptor relations only."
                ),
                "status": "FORM_DEFINED_RELATION_REGISTRY_INCOMPLETE_NO_TRAINING",
            },
            "ontology_legality": {
                "candidate_form": (
                    "Hard candidate mask over registered identifiers, concept roles, dimension "
                    "membership and explicit relation endpoints."
                ),
                "status": "HARD_CONSTRAINT_NO_FIT_REQUIRED",
            },
            "specificity_restraint": {
                "candidate_form": (
                    "A more specific or sibling descriptor requires exact direct evidence or "
                    "an explicit directed relation with source provenance; shared dimension "
                    "membership is insufficient."
                ),
                "status": "NOT_FULLY_DECIDABLE_UNTIL_RELATION_EDGES_ARE_REGISTERED",
            },
            "role_separation": {
                "candidate_form": (
                    "Hard decoding contract: named descriptors only in main/secondary, profile "
                    "directions only in overall_profile, native measurements in neither."
                ),
                "status": "IMPLEMENTED_BY_R9_RESEARCH_ADAPTER",
            },
            "supported_dimension_coverage": {
                "candidate_form": (
                    "Report which supported K1 dimensions have named representation, missing "
                    "dimensions and output-budget conflicts."
                ),
                "status": "SEPARATE_INTERNAL_DIAGNOSTIC_NO_OBJECTIVE_WEIGHT",
            },
            "registered_dimension_redundancy": {
                "candidate_form": (
                    "Report registered-dimension overlap separately; do not equate same "
                    "dimension with synonymy."
                ),
                "status": "SEPARATE_INTERNAL_DIAGNOSTIC_NO_OBJECTIVE_WEIGHT",
            },
        },
        "external_subjective_evaluation": {
            "status": "PROHIBITED_AS_MODEL_OR_ARCHITECTURE_INPUT",
            "excluded_fields": governance["prohibited_model_or_architecture_inputs"],
            "excluded_decisions": governance["prohibited_uses"],
            "note": (
                "Optional product-comprehension observations remain outside training, "
                "calibration, ontology and architecture decisions."
            ),
        },
        "composite_objective": {
            "status": "NOT_DEFINED",
            "reason": (
                "Evidence trace, ontology legality, specificity restraint, role integrity, "
                "coverage and redundancy remain separate constraints or diagnostics."
            ),
        },
        "data_requirements": {
            "required_fields": [
                "globally unique semantic state and coffee-group IDs",
                "C0 exact existing family",
                "C1 exact existing level",
                "ordered questions and selected answer concept IDs",
                "candidate IDs, roles and ordered output positions",
                "versioned evidence paths",
                "registered descriptor relation IDs and direction when used",
                "source provenance and rights state for every registered relation",
                "ontology and identifier registry version",
                "model bundle and answer-state hashes",
            ],
            "dependency_structure": [
                "retain repeated semantic states within coffee group",
                "retain shared source and relation dependencies",
                "never treat multiple states from one coffee group as independent cases",
            ],
            "split_requirements": [
                "split by coffee and source/relation dependency group before any model selection",
                "freeze identifier, role and relation registries before evaluation",
                "reserve independent semantic cases unused for objective or threshold selection",
            ],
            "participant_or_preference_fields": "FORBIDDEN",
        },
        "acceptance_contract": {
            "hard_zero_tolerance": {
                "duplicate_output_ids": 0,
                "unregistered_output_ids": 0,
                "OTHER_NATIVE_MEASUREMENT_leakage": 0,
                "role_placement_violations": 0,
                "invented_child_or_sibling_relations": 0,
                "strict_descriptor_assertions_without_direct_or_registered_relation_trace": 0,
                "subjective_evaluation_read_by_training_or_architecture": 0,
                "T_or_participant_rating_read_by_output_policy": 0,
                "mixed_reference_regression_when_replaying_OUT_MIXED": 0,
            },
            "empirical_thresholds": {
                "semantic_ranking": "NOT_SET",
                "supported_dimension_coverage": "REPORT_SEPARATELY_NO_COMPOSITE",
                "registered_dimension_redundancy": "REPORT_SEPARATELY_NO_COMPOSITE",
                "external_subjective_evaluation": "PROHIBITED_NOT_A_THRESHOLD",
            },
            "threshold_setting_rule": (
                "Any future threshold must be justified from frozen internal semantic "
                "contracts and independent semantic cases, never participant preference."
            ),
            "automatic_approval": False,
        },
        "prohibited_shortcuts": [
            "participant preference, satisfaction or perceived fit as labels",
            "post-output word acceptance as semantic truth",
            "shared dimension membership as a parent-child edge",
            "unregistered descriptor relation inference",
            "arbitrary evidence-tier scalar weights presented as learned confidence",
            "selecting architecture from subjective feedback",
            "synthetic preference fitting",
            "selecting weights and claiming independent confirmation on the same cases",
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
                "external_subjective_evaluation_dependency": value[
                    "semantic_training_governance"
                ]["external_subjective_evaluation_dependency"],
                "sha256": artifact["sha256"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
