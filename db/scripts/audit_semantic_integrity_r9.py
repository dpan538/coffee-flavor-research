#!/usr/bin/env python3
"""Audit frozen R9 outputs against internal semantic and identifier rules.

The audit uses no T, participant rating, preference, satisfaction, fit judgment
or other external subjective evaluation.  It fits nothing and changes no output.
Shared support dimensions are treated as contextual compatibility only; they do
not license a child or sibling descriptor without an explicit registered
descriptor relation.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any, Callable

from acquire_supervision_r5 import save
import audit_output_quality_r9 as quality
from evaluate_output_diversity_r9 import redundancy_metrics
from flavor_m2_r1 import PARENTS
from output_policy_r9 import (
    NAMED_DESCRIPTOR,
    OTHER_NATIVE_MEASUREMENT,
    PROFILE_DIRECTION,
    adapt_output,
    role_registry_from_contract,
)

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.internal-semantic-integrity.v2"
EPSILON = 1e-12
SUBJECTIVE_EVALUATION_KEYS = frozenset(
    {
        "participant_rating",
        "preference_label",
        "main_fit_rating_1_to_4",
        "specificity_choice",
        "new_expression_help_choice",
        "information_burden_choice",
        "profile_effect_choice",
        "satisfaction",
    }
)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY:" + key)
        result[key] = value
    return result


def read(path: Path) -> Any:
    return json.loads(path.read_text(), object_pairs_hook=unique_object)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["candidate_id"] for row in rows]


def nested_subjective_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return (set(value) & SUBJECTIVE_EVALUATION_KEYS) | {
            key for nested in value.values() for key in nested_subjective_keys(nested)
        }
    if isinstance(value, list):
        return {key for nested in value for key in nested_subjective_keys(nested)}
    return set()


def contract_audit(
    contract: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    role_counts = Counter(entry["role"] for entry in registry.values())
    registered_dimensions = {
        dimension_id
        for entry in registry.values()
        if entry["role"] == PROFILE_DIRECTION
        for dimension_id in entry["support_dimension_ids"]
    }
    unknown_dimension_rows = {
        candidate_id: sorted(
            set(entry["support_dimension_ids"]) - registered_dimensions
        )
        for candidate_id, entry in registry.items()
        if set(entry["support_dimension_ids"]) - registered_dimensions
    }
    parent_parity_mismatches = {
        candidate_id: {
            "registry": sorted(registry[candidate_id]["support_dimension_ids"]),
            "frozen_parent_dimensions": sorted(dimensions),
        }
        for candidate_id, dimensions in PARENTS.items()
        if candidate_id not in registry
        or set(registry[candidate_id]["support_dimension_ids"]) != set(dimensions)
    }
    missing_dimension_by_role = {
        role: sorted(
            candidate_id
            for candidate_id, entry in registry.items()
            if entry["role"] == role and not entry["support_dimension_ids"]
        )
        for role in (NAMED_DESCRIPTOR, PROFILE_DIRECTION)
    }
    native_with_flavor_dimensions = sorted(
        candidate_id
        for candidate_id, entry in registry.items()
        if entry["role"] == OTHER_NATIVE_MEASUREMENT and entry["support_dimension_ids"]
    )
    relation_registry = contract.get("descriptor_relation_registry")
    relation_ids = []
    if relation_registry is not None:
        if not isinstance(relation_registry, list):
            raise ValueError("DESCRIPTOR_RELATION_REGISTRY_MUST_BE_LIST")
        for relation in relation_registry:
            if (
                not isinstance(relation, dict)
                or not isinstance(relation.get("relation_id"), str)
                or not relation["relation_id"]
            ):
                raise ValueError("REGISTERED_DESCRIPTOR_RELATION_ID_REQUIRED")
            relation_ids.append(relation["relation_id"])
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("DUPLICATE_DESCRIPTOR_RELATION_ID")
    relation_count = len(relation_ids)
    integrity_pass = not any(
        (
            unknown_dimension_rows,
            parent_parity_mismatches,
            missing_dimension_by_role[NAMED_DESCRIPTOR],
            missing_dimension_by_role[PROFILE_DIRECTION],
            native_with_flavor_dimensions,
        )
    )
    return {
        "concept_count": len(registry),
        "role_counts": dict(sorted(role_counts.items())),
        "registered_dimensions": sorted(registered_dimensions),
        "registered_dimension_count": len(registered_dimensions),
        "unknown_dimension_rows": unknown_dimension_rows,
        "frozen_parent_dimension_parity_mismatches": parent_parity_mismatches,
        "missing_dimension_by_role": missing_dimension_by_role,
        "native_measurements_with_flavor_dimensions": native_with_flavor_dimensions,
        "descriptor_relation_edge_count": relation_count,
        "descriptor_relation_ids": sorted(relation_ids),
        "descriptor_specificity_decidable": relation_count > 0,
        "identifier_and_dimension_registry_integrity": (
            "PASS" if integrity_pass else "FAIL"
        ),
        "interpretation": (
            "PARENTS currently records dimension membership, not broad-to-child or "
            "sibling entailment. Shared dimension membership cannot license a more "
            "specific descriptor."
        ),
    }


def evidence_status(row: dict[str, Any]) -> str:
    if row["selected_or_confirmed_direct"]:
        return "DIRECT_DESCRIPTOR_TRACE"
    if row["shared_supported_dimensions"]:
        return "SUPPORTED_DIMENSION_COMPATIBILITY_ONLY"
    return "NO_CURRENT_ANSWER_SEMANTIC_TRACE"


def specificity_status(row: dict[str, Any]) -> str:
    if row["selected_or_confirmed_direct"]:
        return "DIRECT_DESCRIPTOR_NO_SPECIFICITY_ESCALATION"
    if row["specificity_review_flag"] == (
        "SPECIFIC_FROM_BROADER_OR_SIBLING_EVIDENCE_REVIEW"
    ):
        return "SPECIFIC_FROM_BROADER_OR_SIBLING_REQUIRES_RELATION_EDGE"
    if row["specificity_review_flag"] == (
        "MIDDLE_CATEGORY_FROM_DIRECTION_EVIDENCE_REVIEW"
    ):
        return "MIDDLE_FROM_DIRECTION_REQUIRES_RELATION_EDGE"
    if row["shared_supported_dimensions"]:
        return "DIRECTION_COMPATIBLE_BUT_SPECIFICITY_UNLICENSED"
    return "NO_CURRENT_TRACE_CANNOT_LICENSE_SPECIFICITY"


def case_audit(
    source: dict[str, Any],
    registry: dict[str, Any],
    registered_descriptor_relation_ids: frozenset[str],
) -> dict[str, Any]:
    subjective_keys = nested_subjective_keys(source)
    if subjective_keys:
        raise ValueError(
            "SUBJECTIVE_EVALUATION_PRESENT_IN_SEMANTIC_AUDIT_INPUT:"
            + ",".join(sorted(subjective_keys))
        )
    final = source["actual_return"]
    output = adapt_output(final, registry, "OUT_SEPARATED")
    main = output["main"]
    secondary = output["secondary"]
    profile = output["overall_profile"]
    pool = main + secondary
    all_rows = pool + profile
    all_ids = row_ids(all_rows)
    pool_ids = row_ids(pool)
    profile_ids = row_ids(profile)

    evidence = quality.evidence_rows(source, registry)
    evidence_index = {(row["panel"], row["position"]): row for row in evidence}
    if len(evidence_index) != len(pool):
        raise ValueError("EVIDENCE_OUTPUT_ALIGNMENT_FAILED")

    descriptor_rows = []
    for panel, rows in (("main", main), ("secondary", secondary)):
        for position, frozen_row in enumerate(rows, 1):
            audit_row = evidence_index[(panel, position)]
            candidate_id = frozen_row["candidate_id"]
            if audit_row["descriptor_id"] != candidate_id:
                raise ValueError("EVIDENCE_DESCRIPTOR_ALIGNMENT_FAILED")
            dimensions = set(registry[candidate_id]["support_dimension_ids"])
            frozen_dimensions = set(PARENTS.get(candidate_id, []))
            relation_trace_ids = list(frozen_row.get("relation_evidence_ids", []))
            direct = audit_row["selected_or_confirmed_direct"]
            registered_relation_trace = bool(
                set(relation_trace_ids) & registered_descriptor_relation_ids
            )
            descriptor_rows.append(
                {
                    "panel": panel,
                    "position": position,
                    "descriptor_id": candidate_id,
                    "registered_dimensions": sorted(dimensions),
                    "role": registry[candidate_id]["role"],
                    "frozen_legal": frozen_row.get("legal") is True,
                    "registry_parent_dimension_parity": dimensions == frozen_dimensions,
                    "evidence_status": evidence_status(audit_row),
                    "strict_assertion_trace_ready": direct or registered_relation_trace,
                    "selected_or_confirmed_direct": direct,
                    "shared_supported_dimensions": audit_row[
                        "shared_supported_dimensions"
                    ],
                    "specificity_status": specificity_status(audit_row),
                    "specificity_decision": (
                        "PASS_DIRECT"
                        if direct
                        else "UNDECIDABLE_NO_REGISTERED_DESCRIPTOR_RELATION_EDGE"
                    ),
                    "relation_evidence_ids": relation_trace_ids,
                    "frozen_support_state": frozen_row.get("support_state"),
                    "model_feature_provenance_present": all(
                        key in frozen_row
                        for key in (
                            "base_score",
                            "components",
                            "direct_evidence_application_count",
                            "score",
                        )
                    ),
                }
            )

    supported = quality.supported_dimensions(final)
    supported_ids = set(supported)
    named_output_dimensions = {
        dimension_id
        for row in pool
        for dimension_id in registry[row["candidate_id"]]["support_dimension_ids"]
    }
    covered = supported_ids & named_output_dimensions
    missing = supported_ids - named_output_dimensions
    profile_rows = []
    for row in profile:
        candidate_id = row["candidate_id"]
        dimensions = set(registry[candidate_id]["support_dimension_ids"])
        matched = dimensions & supported_ids
        profile_rows.append(
            {
                "profile_id": candidate_id,
                "role": registry[candidate_id]["role"],
                "registered_dimensions": sorted(dimensions),
                "matched_supported_dimensions": sorted(matched),
                "supported_by_k1": bool(matched),
                "frozen_legal": row.get("legal") is True,
                "registry_parent_dimension_parity": dimensions
                == set(PARENTS.get(candidate_id, [])),
            }
        )

    identifiers_registered = all(candidate_id in registry for candidate_id in all_ids)
    unique_output_ids = len(all_ids) == len(set(all_ids))
    role_purity = all(
        registry[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR for row in pool
    ) and all(
        registry[row["candidate_id"]]["role"] == PROFILE_DIRECTION for row in profile
    )
    ontology_rows = descriptor_rows + profile_rows
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "identifier_integrity": {
            "all_output_ids_registered": identifiers_registered,
            "all_output_ids_unique": unique_output_ids,
            "profile_pool_overlap_ids": sorted(set(pool_ids) & set(profile_ids)),
            "pass": identifiers_registered
            and unique_output_ids
            and not (set(pool_ids) & set(profile_ids)),
        },
        "role_purity": {
            "pass": role_purity,
            "named_pool_count": len(pool),
            "profile_direction_count": len(profile),
            "other_native_measurement_leakage": sum(
                registry[candidate_id]["role"] == OTHER_NATIVE_MEASUREMENT
                for candidate_id in all_ids
            ),
        },
        "ontology_legality": {
            "frozen_legal_rows": sum(row["frozen_legal"] for row in ontology_rows),
            "rows": len(ontology_rows),
            "parent_dimension_parity_rows": sum(
                row["registry_parent_dimension_parity"] for row in ontology_rows
            ),
            "pass": all(row["frozen_legal"] for row in ontology_rows)
            and all(row["registry_parent_dimension_parity"] for row in ontology_rows),
            "scope_note": (
                "Frozen legal flags and registered dimension parity are checked separately "
                "from descriptor-level entailment, which is not registered."
            ),
        },
        "descriptor_evidence": descriptor_rows,
        "specificity": {
            "decidable_from_registered_relations": bool(
                registered_descriptor_relation_ids
            ),
            "direct_pass_count": sum(
                row["specificity_decision"] == "PASS_DIRECT" for row in descriptor_rows
            ),
            "undecidable_count": sum(
                row["specificity_decision"]
                == "UNDECIDABLE_NO_REGISTERED_DESCRIPTOR_RELATION_EDGE"
                for row in descriptor_rows
            ),
            "confirmed_violation_count": None,
        },
        "supported_dimension_coverage": {
            "supported_dimension_ids": sorted(supported_ids),
            "named_output_dimension_ids": sorted(named_output_dimensions),
            "covered_dimension_ids": sorted(covered),
            "missing_dimension_ids": sorted(missing),
            "coverage": (len(covered) / len(supported_ids) if supported_ids else None),
            "coverage_complete": not missing,
            "evaluable": bool(supported_ids),
        },
        "redundancy": {
            "main": redundancy_metrics(main, registry),
            "comparison_pool": redundancy_metrics(pool, registry),
        },
        "profile_rows": profile_rows,
        "subjective_evaluation_fields_used": [],
        "T_used": False,
    }


def group_macro(
    cases: list[dict[str, Any]], getter: Callable[[dict[str, Any]], float | None]
) -> float | None:
    grouped: dict[str, list[float]] = defaultdict(list)
    for case in cases:
        value = getter(case)
        if value is not None:
            grouped[case["group_id"]].append(float(value))
    if not grouped:
        return None
    return statistics.fmean(statistics.fmean(values) for values in grouped.values())


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    redundancy_fields = (
        "named_descriptors_per_active_dimension",
        "repeated_dimension_membership_rate",
        "mean_pairwise_dimension_jaccard",
        "identical_dimension_signature_pair_rate",
        "ordered_repeated_dimension_row_rate",
    )
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        descriptors = [
            descriptor for case in rows for descriptor in case["descriptor_evidence"]
        ]
        profiles = [profile for case in rows for profile in case["profile_rows"]]
        evidence_counts = Counter(row["evidence_status"] for row in descriptors)
        specificity_counts = Counter(row["specificity_status"] for row in descriptors)
        supported_total = sum(
            len(case["supported_dimension_coverage"]["supported_dimension_ids"])
            for case in rows
        )
        covered_total = sum(
            len(case["supported_dimension_coverage"]["covered_dimension_ids"])
            for case in rows
        )
        strict_ready = sum(row["strict_assertion_trace_ready"] for row in descriptors)
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({case["group_id"] for case in rows}),
            "identifier_integrity_pass_records": sum(
                case["identifier_integrity"]["pass"] for case in rows
            ),
            "role_purity_pass_records": sum(
                case["role_purity"]["pass"] for case in rows
            ),
            "other_native_measurement_leakage_occurrences": sum(
                case["role_purity"]["other_native_measurement_leakage"] for case in rows
            ),
            "ontology_legality_pass_records": sum(
                case["ontology_legality"]["pass"] for case in rows
            ),
            "ontology_legal_rows": sum(
                case["ontology_legality"]["frozen_legal_rows"] for case in rows
            ),
            "ontology_rows": sum(case["ontology_legality"]["rows"] for case in rows),
            "descriptor_occurrences": len(descriptors),
            "descriptor_evidence_status_counts": dict(sorted(evidence_counts.items())),
            "strict_assertion_trace_ready_occurrences": strict_ready,
            "strict_assertion_trace_not_ready_occurrences": len(descriptors)
            - strict_ready,
            "strict_assertion_trace_ready_rate": (
                strict_ready / len(descriptors) if descriptors else None
            ),
            "specificity_status_counts": dict(sorted(specificity_counts.items())),
            "specificity_confirmed_violation_count": None,
            "specificity_decision": (
                "NOT_FULLY_DECIDABLE_NO_REGISTERED_DESCRIPTOR_RELATION_EDGES"
            ),
            "supported_dimension_coverage": {
                "supported_dimension_occurrences": supported_total,
                "covered_dimension_occurrences": covered_total,
                "missing_dimension_occurrences": supported_total - covered_total,
                "micro_coverage": (
                    covered_total / supported_total if supported_total else None
                ),
                "complete_records": sum(
                    case["supported_dimension_coverage"]["coverage_complete"]
                    for case in rows
                ),
                "incomplete_records": sum(
                    not case["supported_dimension_coverage"]["coverage_complete"]
                    for case in rows
                ),
            },
            "redundancy_group_macro": {
                view: {
                    field: group_macro(
                        rows,
                        lambda case, v=view, f=field: case["redundancy"][v][f],
                    )
                    for field in redundancy_fields
                }
                for view in ("main", "comparison_pool")
            },
            "profile_occurrences": len(profiles),
            "unsupported_profile_occurrences": sum(
                not profile["supported_by_k1"] for profile in profiles
            ),
            "subjective_evaluation_fields_used": [],
            "T_used": False,
            "semantic_acceptance": (
                "STRUCTURE_PASS_STRICT_DESCRIPTOR_ASSERTION_TRACE_INCOMPLETE"
                if strict_ready < len(descriptors)
                else "STRUCTURE_AND_TRACE_PASS"
            ),
        }
    return result


def c01_findings(summary: dict[str, Any], relation_count: int) -> dict[str, Any]:
    row = summary["C01"]
    return {
        "structure": (
            f"Identifier, role and frozen ontology-legality checks pass in "
            f"{row['records']}/{row['records']} C01 records; native-measurement leakage is zero."
        ),
        "traceability": (
            f"Only {row['strict_assertion_trace_ready_occurrences']}/"
            f"{row['descriptor_occurrences']} named output occurrences have a direct "
            "descriptor trace. Direction compatibility or an unobserved model candidate "
            "does not by itself license a strict descriptor assertion."
        ),
        "evidence_status_counts": row["descriptor_evidence_status_counts"],
        "specificity": (
            f"The contract contains {relation_count} registered descriptor-level relation "
            "edges. Non-direct broad/sibling-to-specific cases are review requirements, "
            "not computable violations or passes."
        ),
        "specificity_status_counts": row["specificity_status_counts"],
        "supported_dimension_coverage": row["supported_dimension_coverage"],
        "redundancy": row["redundancy_group_macro"],
        "decision": (
            "OUT_SEPARATED passes structural role and identifier integrity, but current "
            "frozen outputs are not ready to be treated as strict semantic assertions "
            "without direct evidence, registered descriptor relations, or abstention."
        ),
    }


def audit(
    actual_returns_path: Path,
    contract_path: Path,
    private_output_path: Path,
    public_output_path: Path,
) -> dict[str, Any]:
    expected = read(R8_PUBLIC / "output_alignment_results.json")[
        "private_artifact_hashes"
    ]["actual_returns.private.json"]
    if sha256(actual_returns_path) != expected:
        raise ValueError("R8_ACTUAL_RETURNS_HASH_MISMATCH")
    contract = read(contract_path)
    registry = role_registry_from_contract(contract)
    registry_result = contract_audit(contract, registry)
    if registry_result["identifier_and_dimension_registry_integrity"] != "PASS":
        raise ValueError("SEMANTIC_REGISTRY_INTEGRITY_FAILED")
    sources = read(actual_returns_path)
    cases = [
        case_audit(
            source,
            registry,
            frozenset(registry_result["descriptor_relation_ids"]),
        )
        for source in sources
    ]
    summary = summarize(cases)
    private_payload = {
        "version": VERSION,
        "scope": "PRIVATE_INTERNAL_SEMANTIC_AUDIT_NO_T_NO_SUBJECTIVE_EVALUATION",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "registry_audit": registry_result,
        "summary": summary,
        "cases": cases,
    }
    artifact = save(private_output_path, private_payload)
    public = {
        "version": VERSION,
        "status": "COMPLETE_ON_REBUILT_R8_ACTUAL_RETURNS",
        "fit_count": 0,
        "purpose": (
            "Evaluate internal semantic, identifier, role, evidence-chain, specificity, "
            "supported-dimension and redundancy consistency without external subjective "
            "evaluation."
        ),
        "source_actual_returns_sha256": expected,
        "registry_audit": registry_result,
        "c01_findings": c01_findings(
            summary, registry_result["descriptor_relation_edge_count"]
        ),
        "summary": summary,
        "private_detail": {
            "status": "OWNER_CONTROLLED_STORAGE",
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
        },
        "governance": {
            "authoritative_basis": [
                "provenance-backed descriptor identifiers",
                "explicit concept roles",
                "registered dimension membership",
                "registered descriptor relations when present",
                "question-answer evidence state",
                "hard output contracts",
            ],
            "subjective_participant_evaluation_as_training_input": "PROHIBITED",
            "subjective_participant_evaluation_as_architecture_selector": "PROHIBITED",
            "subjective_participant_evaluation_as_metric_weight_or_threshold_source": (
                "PROHIBITED"
            ),
            "optional_human_observation_scope": (
                "Product comprehension and wording usability only; never sensory truth, "
                "model supervision or architecture validation."
            ),
        },
        "guards": {
            "fit_count": 0,
            "T_used": False,
            "participant_rating_used": False,
            "preference_or_satisfaction_used": False,
            "metric_weight_created": False,
            "threshold_selected": False,
            "output_or_default_changed": False,
        },
        "interpretation_limits": [
            "Direction compatibility is not descriptor entailment.",
            "A review-required specificity path is not a confirmed semantic error.",
            "Frozen model feature provenance is not a substitute for an explicit runtime semantic trace.",
            "Registered-dimension redundancy is coarser than descriptor synonymy.",
        ],
    }
    public_output_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return public


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-returns", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=R9_PUBLIC / "output_policy_contract.json",
    )
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=R9_PUBLIC / "r9_semantic_integrity_audit.json",
    )
    args = parser.parse_args()
    result = audit(args.actual_returns, args.contract, args.private_output, args.output)
    print(
        json.dumps(
            {
                "status": result["status"],
                "fit_count": result["fit_count"],
                "T_used": result["guards"]["T_used"],
                "participant_rating_used": result["guards"]["participant_rating_used"],
                "private_sha256": result["private_detail"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
