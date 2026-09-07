#!/usr/bin/env python3
"""Run the zero-fit R9 evidence and semantic-structure analyses.

The analysis projects sealed R8 actual returns onto record identity, generator and
the frozen final endpoint before any analysis function is called. It does not pass
T or participant evaluation to a policy or semantic analysis, fit parameters,
create descriptor relations, or change an output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from acquire_supervision_r5 import save
import analyze_descriptor_relations_r9 as relations
import descriptor_association_analysis_r9 as associations
import descriptor_feature_extraction_r9 as descriptor_features
import evidence_structure_analysis_r9 as evidence_structure
from output_policy_r9 import role_registry_from_contract
import tripartite_semantic_structure_r9 as tripartite

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.semantic-structure-analysis.v1"


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


def semantic_projection(source: dict[str, Any]) -> dict[str, Any]:
    """Copy only frozen semantic inputs; deliberately omit T and evaluation fields."""

    required = ("record_id", "group_id", "policy", "actual_return")
    missing = [key for key in required if key not in source]
    if missing:
        raise ValueError("SEMANTIC_PROJECTION_FIELD_REQUIRED:" + ",".join(missing))
    return {key: source[key] for key in required}


def analyze(
    actual_returns_path: Path,
    contract_path: Path,
    private_output_path: Path,
    public_output_path: Path,
) -> dict[str, Any]:
    expected_hash = read(R8_PUBLIC / "output_alignment_results.json")[
        "private_artifact_hashes"
    ]["actual_returns.private.json"]
    if sha256(actual_returns_path) != expected_hash:
        raise ValueError("R8_ACTUAL_RETURNS_HASH_MISMATCH")

    raw_sources = read(actual_returns_path)
    subjective_keys = relations.nested_subjective_keys(raw_sources)
    if subjective_keys:
        raise ValueError(
            "SUBJECTIVE_EVALUATION_PRESENT_IN_SEMANTIC_STRUCTURE_INPUT:"
            + ",".join(sorted(subjective_keys))
        )
    sources = [
        semantic_projection(source)
        for source in raw_sources
        if source.get("policy") == "C01"
    ]
    if not sources:
        raise ValueError("C01_FROZEN_SOURCES_REQUIRED")

    contract = read(contract_path)
    registry = role_registry_from_contract(contract)
    registered_relation_edges = relations.validate_relation_registry(contract, registry)

    evidence_rows = evidence_structure.evidence_stratified_rows(sources, registry)
    question_rows = evidence_structure.question_source_rows(sources, registry)
    k1_rows = evidence_structure.k1_output_rows(sources, registry)
    features = descriptor_features.build_descriptor_features(sources, registry)
    cooccurrence = associations.cooccurrence_network(sources, registry)
    similarities = associations.descriptor_similarity_views(
        features, cooccurrence, registry
    )
    tripartite_graph = tripartite.build_tripartite_graph(sources, registry)

    evidence_summary = evidence_structure.summarize_evidence_strata(evidence_rows)
    question_summary = evidence_structure.summarize_question_sources(question_rows)
    k1_summary = evidence_structure.summarize_k1(k1_rows)
    position_summary = evidence_structure.summarize_position_evidence(evidence_rows)
    profile_summary = evidence_structure.profile_cross_summary(sources, registry)

    private_payload = {
        "version": VERSION,
        "status": "RESEARCH_OBSERVATION_ONLY",
        "fit_count": 0,
        "source_actual_returns_sha256": expected_hash,
        "analysis_scope": {
            "generator": "C01_FROZEN_RESEARCH_GENERATOR",
            "record_count": len(sources),
            "coffee_group_count": len({source["group_id"] for source in sources}),
            "input_projection_fields": [
                "record_id",
                "group_id",
                "policy",
                "actual_return",
            ],
            "T_field_projected": False,
        },
        "evidence_strata": {"rows": evidence_rows, "summary": evidence_summary},
        "question_source_provenance": {
            "rows": question_rows,
            "summary": question_summary,
        },
        "k1_output_association": {"rows": k1_rows, "summary": k1_summary},
        "main_secondary_evidence": position_summary,
        "profile_type_cross_analysis": profile_summary,
        "descriptor_features": features,
        "descriptor_cooccurrence_network": cooccurrence,
        "descriptor_similarity_views": similarities,
        "evidence_dimension_descriptor_graph": tripartite_graph,
    }
    private_artifact = save(private_output_path, private_payload)

    public = {
        "version": VERSION,
        "status": "RESEARCH_OBSERVATION_ONLY",
        "source_actual_returns_sha256": expected_hash,
        "contract_version": contract["version"],
        "scope": {
            "generator": "C01_FROZEN_RESEARCH_GENERATOR",
            "records": len(sources),
            "coffee_groups": len({source["group_id"] for source in sources}),
            "registered_named_descriptors": features["descriptor_count"],
            "registered_relation_edges_before_analysis": len(registered_relation_edges),
            "relation_edges_created_by_analysis": 0,
        },
        "analysis_groups": {
            "evidence_chain_strata": evidence_summary,
            "question_source_provenance": question_summary,
            "k1_status_output_association": k1_summary,
            "main_secondary_evidence": position_summary,
            "profile_type_cross_analysis": profile_summary,
            "descriptor_cooccurrence_network": cooccurrence["summary"],
            "descriptor_similarity_views": similarities["summary"],
            "evidence_dimension_descriptor_graph": tripartite_graph["summary"],
        },
        "decision": (
            "The frozen data support multiple separate descriptions of evidence trace, "
            "registered-dimension coverage, redundancy, output position, co-occurrence and "
            "graph topology. They do not support a single concentration score or automatic "
            "descriptor relation. OUT_SEPARATED remains the approved role contract; these "
            "observations do not change its selector or claim empirical superiority."
        ),
        "research_limits": [
            "Evidence classes remain categorical; no 1/0.5/0 strength score was defined.",
            "First compatible question slot is provenance, not causal contribution or child-descriptor entailment.",
            "K1 statuses are preserved exactly as observed and are not remapped to an assumed ordinal scale.",
            "Profile types describe output composition and are not coffee classes or learned clusters.",
            "All positive co-occurrences are retained without a selected frequency threshold.",
            "Similarity views remain separate because no cross-view weights are authorized.",
            "Tripartite centrality is topology induced by registry membership and observed selections, not evidence sufficiency.",
            "Records and coffee groups are reported separately; no independent-row inference is run.",
        ],
        "private_detail": {
            "status": "OWNER_CONTROLLED_STORAGE",
            "sha256": private_artifact["sha256"],
            "bytes": private_artifact["bytes"],
        },
        "guards": {
            "fit_count": 0,
            "T_used": False,
            "subjective_evaluation_used": False,
            "scalar_evidence_strength_defined": False,
            "composite_similarity_defined": False,
            "frequency_threshold_selected": False,
            "embedding_or_cluster_fit": False,
            "semantic_relation_edges_created": 0,
            "output_or_default_changed": False,
            "trigger_or_stopping_rule_changed": False,
        },
    }
    public_output_path.write_text(
        json.dumps(public, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
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
        default=R9_PUBLIC / "r9_semantic_structure_analysis.json",
    )
    args = parser.parse_args()
    result = analyze(
        args.actual_returns, args.contract, args.private_output, args.output
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "fit_count": result["guards"]["fit_count"],
                "T_used": result["guards"]["T_used"],
                "private_sha256": result["private_detail"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
