#!/usr/bin/env python3
"""Audit descriptor-relation readiness over frozen R8 actual returns.

This is a zero-fit R9 diagnostic.  It never derives a descriptor edge from a
shared support dimension, identifier prefix, model score, target, or participant
judgment.  It validates an explicit relation registry, inventories relation-review
candidates, and reports which current OUT_SEPARATED rows could be strict semantic
assertions.  It does not rerank or replace any output.
"""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from acquire_supervision_r5 import save
import audit_output_quality_r9 as quality
from output_policy_r9 import NAMED_DESCRIPTOR, adapt_output, role_registry_from_contract

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.descriptor-relation-readiness.v1"
SUBJECTIVE_EVALUATION_KEYS = frozenset(
    {
        "participant_rating",
        "preference_label",
        "participant_preference",
        "participant_satisfaction",
        "perceived_fit_rating",
        "main_fit_rating_1_to_4",
        "specificity_choice",
        "new_expression_help_choice",
        "information_burden_choice",
        "profile_effect_choice",
        "post_output_acceptance",
        "profile_preference",
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


def nested_subjective_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return (set(value) & SUBJECTIVE_EVALUATION_KEYS) | {
            key for nested in value.values() for key in nested_subjective_keys(nested)
        }
    if isinstance(value, list):
        return {key for nested in value for key in nested_subjective_keys(nested)}
    return set()


def validate_relation_registry(
    contract: dict[str, Any], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    relation_contract = contract.get("descriptor_relation_contract")
    if not isinstance(relation_contract, dict):
        raise ValueError("DESCRIPTOR_RELATION_CONTRACT_REQUIRED")
    required = set(relation_contract.get("required_edge_fields", []))
    if not required:
        raise ValueError("RELATION_REQUIRED_EDGE_FIELDS_REQUIRED")
    allowed = set(relation_contract.get("allowed_relation_types", {}))
    directions = relation_contract.get("inference_directions", {})
    active_status = relation_contract.get("active_governance_status")
    edges = contract.get("descriptor_relation_registry")
    if not isinstance(edges, list):
        raise ValueError("DESCRIPTOR_RELATION_REGISTRY_LIST_REQUIRED")

    relation_ids = set()
    endpoint_keys = set()
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("DESCRIPTOR_RELATION_EDGE_OBJECT_REQUIRED")
        missing = required - set(edge)
        if missing:
            raise ValueError(
                "DESCRIPTOR_RELATION_EDGE_FIELDS_MISSING:" + ",".join(sorted(missing))
            )
        relation_id = edge["relation_id"]
        relation_type = edge["relation_type"]
        subject = edge["subject_concept_id"]
        object_id = edge["object_concept_id"]
        provenance_ids = edge["provenance_ids"]
        if not isinstance(relation_id, str) or not relation_id:
            raise ValueError("NONEMPTY_DESCRIPTOR_RELATION_ID_REQUIRED")
        if relation_id in relation_ids:
            raise ValueError("DUPLICATE_DESCRIPTOR_RELATION_ID:" + relation_id)
        relation_ids.add(relation_id)
        if relation_type not in allowed:
            raise ValueError(
                "UNREGISTERED_DESCRIPTOR_RELATION_TYPE:" + str(relation_type)
            )
        if subject not in registry or object_id not in registry:
            raise ValueError("UNREGISTERED_DESCRIPTOR_RELATION_ENDPOINT:" + relation_id)
        if (
            registry[subject]["role"] != NAMED_DESCRIPTOR
            or registry[object_id]["role"] != NAMED_DESCRIPTOR
        ):
            raise ValueError("NON_DESCRIPTOR_RELATION_ENDPOINT:" + relation_id)
        if subject == object_id:
            raise ValueError("SELF_DESCRIPTOR_RELATION_FORBIDDEN:" + relation_id)
        if edge["inference_direction"] != directions.get(relation_type):
            raise ValueError("DESCRIPTOR_RELATION_DIRECTION_MISMATCH:" + relation_id)
        if edge["governance_status"] != active_status:
            raise ValueError(
                "UNAPPROVED_EDGE_IN_ACTIVE_RELATION_REGISTRY:" + relation_id
            )
        if (
            not isinstance(provenance_ids, list)
            or not provenance_ids
            or any(not isinstance(value, str) or not value for value in provenance_ids)
        ):
            raise ValueError("DESCRIPTOR_RELATION_PROVENANCE_REQUIRED:" + relation_id)
        endpoint_key = (relation_type, subject, object_id)
        if endpoint_key in endpoint_keys:
            raise ValueError("DUPLICATE_DESCRIPTOR_RELATION_ENDPOINTS:" + relation_id)
        endpoint_keys.add(endpoint_key)
    return [dict(edge) for edge in edges]


def licensed_relation_ids(
    target_id: str,
    directly_supported_ids: set[str],
    edges: Iterable[dict[str, Any]],
) -> list[str]:
    """Return exact one-edge entailments; broad-to-child propagation is impossible."""

    licensed = []
    for edge in edges:
        relation_type = edge["relation_type"]
        subject = edge["subject_concept_id"]
        object_id = edge["object_concept_id"]
        if (
            relation_type == "IS_A"
            and subject in directly_supported_ids
            and target_id == object_id
        ):
            licensed.append(edge["relation_id"])
        elif relation_type == "SYNONYM" and (
            (subject in directly_supported_ids and target_id == object_id)
            or (object_id in directly_supported_ids and target_id == subject)
        ):
            licensed.append(edge["relation_id"])
    return sorted(licensed)


def dimension_co_membership_pairs(registry: dict[str, Any]) -> dict[str, Any]:
    """Count compatibility pairs without relabeling any of them as semantic edges."""

    named = sorted(
        candidate_id
        for candidate_id, entry in registry.items()
        if entry["role"] == NAMED_DESCRIPTOR
    )
    all_pairs = []
    middle_pairs = []
    for left, right in combinations(named, 2):
        shared = sorted(
            set(registry[left]["support_dimension_ids"])
            & set(registry[right]["support_dimension_ids"])
        )
        if not shared:
            continue
        row = {"left": left, "right": right, "shared_dimension_ids": shared}
        all_pairs.append(row)
        if (left in quality.MIDDLE_NAMED_IDS) != (right in quality.MIDDLE_NAMED_IDS):
            middle_pairs.append(row)
    return {
        "named_descriptor_pairs_sharing_a_dimension": len(all_pairs),
        "middle_to_other_named_pairs_sharing_a_dimension": len(middle_pairs),
        "automatic_relation_edges_created": 0,
        "interpretation": (
            "These are compatibility pairs only. Treating them as parent-child, synonym "
            "or co-hyponym edges would fabricate semantics."
        ),
    }


def relation_review_candidates(
    evidence_row: dict[str, Any], registry: dict[str, Any]
) -> list[dict[str, Any]]:
    if evidence_row["selected_or_confirmed_direct"]:
        return []
    target_id = evidence_row["descriptor_id"]
    broader = set(evidence_row["broader_support_sources"])
    result = []
    for source_id in sorted(broader):
        source_role = registry[source_id]["role"]
        candidate_type = (
            "DIRECTION_ASSOCIATION_NOT_DESCRIPTOR_EDGE"
            if source_role != NAMED_DESCRIPTOR
            else "POTENTIAL_NAMED_HIERARCHY_NEEDS_PROVENANCE"
        )
        result.append(
            {
                "source_concept_id": source_id,
                "target_concept_id": target_id,
                "candidate_type": candidate_type,
            }
        )
    for source_id in sorted(set(evidence_row["sibling_support_sources"]) - broader):
        result.append(
            {
                "source_concept_id": source_id,
                "target_concept_id": target_id,
                "candidate_type": "POTENTIAL_CO_HYPONYM_OR_OTHER_NEEDS_PROVENANCE",
            }
        )
    return result


def case_analysis(
    source: dict[str, Any], registry: dict[str, Any], edges: list[dict[str, Any]]
) -> dict[str, Any]:
    subjective_keys = nested_subjective_keys(source)
    if subjective_keys:
        raise ValueError(
            "SUBJECTIVE_EVALUATION_PRESENT_IN_RELATION_AUDIT_INPUT:"
            + ",".join(sorted(subjective_keys))
        )
    final = source["actual_return"]
    output = adapt_output(final, registry, "OUT_SEPARATED")
    directly_supported = quality.selected_user_concepts(final) | set(
        final["state"]["k1"].get("confirmed_concepts", [])
    )
    evidence = quality.evidence_rows(source, registry)
    assertion_rows = []
    review_rows = []
    frozen_relation_evidence_occurrences = 0
    for row in evidence:
        relation_ids = licensed_relation_ids(
            row["descriptor_id"], directly_supported, edges
        )
        direct = row["selected_or_confirmed_direct"]
        status = (
            "DIRECT_DESCRIPTOR_TRACE"
            if direct
            else (
                "REGISTERED_RELATION_TRACE"
                if relation_ids
                else "NOT_LICENSED_FOR_STRICT_ASSERTION"
            )
        )
        frozen_relation_evidence_occurrences += len(row["model_relation_evidence_ids"])
        assertion_rows.append(
            {
                "panel": row["panel"],
                "position": row["position"],
                "descriptor_id": row["descriptor_id"],
                "assertion_status": status,
                "licensed_relation_ids": relation_ids,
                "shared_supported_dimensions": row["shared_supported_dimensions"],
            }
        )
        for candidate in relation_review_candidates(row, registry):
            review_rows.append(
                {
                    **candidate,
                    "panel": row["panel"],
                    "position": row["position"],
                    "target_evidence_status": row["evidence_class"],
                }
            )
    strict_ids = [
        row["descriptor_id"]
        for row in assertion_rows
        if row["assertion_status"] != "NOT_LICENSED_FOR_STRICT_ASSERTION"
    ]
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "current_output_hash": output["output_hash"],
        "assertion_rows": assertion_rows,
        "strict_assertion_eligible_ids_in_current_order": strict_ids,
        "strict_assertion_eligible_count": len(strict_ids),
        "strict_comparison_status_if_enforced": (
            "ELIGIBLE_SHADOW_ONLY"
            if 3 <= len(strict_ids) <= 8
            else "NOT_EXECUTABLE_EXISTING_3_TO_8_CONTRACT"
        ),
        "relation_review_candidates": review_rows,
        "frozen_relation_evidence_occurrences": frozen_relation_evidence_occurrences,
        "output_changed": False,
        "T_used": False,
        "subjective_evaluation_used": False,
    }


def summarize(cases: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for generator in ("C00", "C01"):
        rows = [case for case in cases if case["generator"] == generator]
        assertions = [row for case in rows for row in case["assertion_rows"]]
        reviews = [row for case in rows for row in case["relation_review_candidates"]]
        assertion_counts = Counter(row["assertion_status"] for row in assertions)
        review_counts = Counter(row["candidate_type"] for row in reviews)
        unique_review_pairs = {
            (
                row["source_concept_id"],
                row["target_concept_id"],
                row["candidate_type"],
            )
            for row in reviews
        }
        result[generator] = {
            "records": len(rows),
            "coffee_groups": len({case["group_id"] for case in rows}),
            "descriptor_occurrences": len(assertions),
            "assertion_status_counts": dict(sorted(assertion_counts.items())),
            "strict_assertion_eligible_occurrences": sum(
                status != "NOT_LICENSED_FOR_STRICT_ASSERTION"
                for status in (row["assertion_status"] for row in assertions)
            ),
            "records_with_at_least_three_strict_assertions": sum(
                case["strict_assertion_eligible_count"] >= 3 for case in rows
            ),
            "relation_review_candidate_occurrences": len(reviews),
            "unique_relation_review_candidate_pairs": len(unique_review_pairs),
            "relation_review_candidate_type_counts": dict(
                sorted(review_counts.items())
            ),
            "frozen_relation_evidence_occurrences": sum(
                case["frozen_relation_evidence_occurrences"] for case in rows
            ),
            "outputs_changed": 0,
        }
    return result


def analyze(
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
    edges = validate_relation_registry(contract, registry)
    cases = [
        case_analysis(source, registry, edges) for source in read(actual_returns_path)
    ]
    summary = summarize(cases)
    private_payload = {
        "version": VERSION,
        "scope": "PRIVATE_RELATION_READINESS_NO_T_NO_SUBJECTIVE_EVALUATION",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "registered_relation_edges": edges,
        "summary": summary,
        "cases": cases,
    }
    artifact = save(private_output_path, private_payload)
    public = {
        "version": VERSION,
        "status": "COMPLETE_NO_REGISTERED_DESCRIPTOR_EDGES",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "relation_contract_version": contract["descriptor_relation_contract"][
            "version"
        ],
        "registered_relation_edge_count": len(edges),
        "dimension_co_membership_audit": dimension_co_membership_pairs(registry),
        "summary": summary,
        "algorithm_gate": {
            "relation_aware_assertion_check": "EXECUTED_BOOLEAN_ONE_EDGE",
            "weighted_evidence_propagation": "NOT_RUN_NO_DECAY_OR_HOP_WEIGHT_AUTHORITY",
            "MMR_reranking": "NOT_RUN_NO_APPROVED_RELATION_GRAPH_OR_LAMBDA_AUTHORITY",
            "submodular_selection": "NOT_RUN_NO_APPROVED_RELATION_GRAPH_OR_BETA_AUTHORITY",
            "dimension_only_similarity": "REJECTED_DOES_NOT_RESOLVE_DESCRIPTOR_SEMANTICS",
            "output_policy_or_default_changed": False,
        },
        "decision": (
            "The descriptor-relation schema is executable, but the active registry is empty. "
            "The next admissible work is provenance review and owner registration of exact "
            "edges; shared dimensions cannot bootstrap the graph."
        ),
        "private_detail": {
            "status": "OWNER_CONTROLLED_STORAGE",
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
        },
        "guards": {
            "fit_count": 0,
            "T_used": False,
            "subjective_evaluation_used": False,
            "relation_edges_inferred": 0,
            "weights_or_thresholds_selected": False,
            "output_changed": False,
        },
    }
    public_output_path.write_text(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return public


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-returns", type=Path, required=True)
    parser.add_argument(
        "--contract", type=Path, default=R9_PUBLIC / "output_policy_contract.json"
    )
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=R9_PUBLIC / "r9_descriptor_relation_readiness.json",
    )
    args = parser.parse_args()
    result = analyze(
        args.actual_returns, args.contract, args.private_output, args.output
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "fit_count": 0,
                "registered_relation_edge_count": result[
                    "registered_relation_edge_count"
                ],
                "private_sha256": result["private_detail"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
