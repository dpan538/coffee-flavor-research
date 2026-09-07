#!/usr/bin/env python3
"""Build the zero-fit multi-view R9 semantic lineage report.

The report combines registered descriptor features, rule-based coffee profiles,
observed answer-evidence trajectories, and formal-context associations.  It reads
neither T nor subjective evaluation, fits nothing, creates no semantic relation
edge, and changes no output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from acquire_supervision_r5 import save
import analyze_descriptor_relations_r9 as relations
import coffee_profile_assignment_r9 as profiles
import descriptor_feature_extraction_r9 as descriptors
import formal_concept_analysis_r9 as fca
from output_policy_r9 import role_registry_from_contract
import trajectory_analysis_r9 as trajectories

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.semantic-lineage-analysis.v1"


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
    relation_edges = relations.validate_relation_registry(contract, registry)
    sources = read(actual_returns_path)
    subjective_keys = relations.nested_subjective_keys(sources)
    if subjective_keys:
        raise ValueError(
            "SUBJECTIVE_EVALUATION_PRESENT_IN_SEMANTIC_LINEAGE_INPUT:"
            + ",".join(sorted(subjective_keys))
        )
    c01_sources = [source for source in sources if source["policy"] == "C01"]
    if not c01_sources:
        raise ValueError("C01_FROZEN_SOURCES_REQUIRED")

    descriptor_features = descriptors.build_descriptor_features(c01_sources, registry)
    profile_cases = [profiles.profile_case(source, registry) for source in sources]
    trajectory_cases = [
        trajectories.extract_trajectory(source, registry) for source in sources
    ]
    formal_context = fca.build_formal_context(c01_sources, registry)
    formal_analysis = fca.analyze_formal_context(formal_context)
    if formal_analysis["formal_concepts"]["enumeration_truncated"]:
        raise ValueError("FORMAL_INTENT_ENUMERATION_SAFETY_LIMIT_REACHED")

    private_payload = {
        "version": VERSION,
        "status": "RESEARCH_OBSERVATION_ONLY",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "descriptor_features": descriptor_features,
        "case_profiles": profile_cases,
        "answer_evidence_trajectories": trajectory_cases,
        "formal_context_analysis": formal_analysis,
    }
    artifact = save(private_output_path, private_payload)
    public = {
        "version": VERSION,
        "status": "RESEARCH_OBSERVATION_ONLY",
        "fit_count": 0,
        "source_actual_returns_sha256": expected,
        "contract_version": contract["version"],
        "relation_registry": {
            "approved_edge_count": len(relation_edges),
            "edges_created_by_this_analysis": 0,
        },
        "views": {
            "descriptor_lineage": {
                "scope": "REGISTERED_HIGH_DIMENSIONAL_FEATURE_MATRIX",
                "summary": descriptors.summarize(descriptor_features),
                "PCA_or_MDS": "NOT_RUN_R9_EMBEDDING_PROHIBITED",
                "interpretation": (
                    "Coordinates were not manufactured. The auditable object is the exact "
                    "registered multi-hot and categorical feature matrix."
                ),
            },
            "case_profile_lineage": {
                "scope": "RULE_BASED_REGISTERED_DIMENSION_COUNT_TYPES_NOT_CLUSTERS",
                "summary": profiles.summarize(profile_cases),
            },
            "dynamic_evidence_trajectory": {
                "scope": "OBSERVED_Q0_TO_Q4_ANSWER_EVIDENCE_PREFIXES",
                "summary": trajectories.summarize(trajectory_cases),
                "intermediate_candidate_or_output_trajectory": (
                    "NOT_EVALUATED_FINAL_ENDPOINT_ONLY"
                ),
            },
            "formal_concept_analysis": {
                "scope": "C01_OUT_SEPARATED_FROZEN_OUTPUT_CONTEXT",
                "summary": formal_analysis["summary"],
            },
        },
        "decision": (
            "The four views expose structure and dynamics without collapsing them into a "
            "single concentration score. Descriptor co-membership and frozen-context "
            "implications remain review candidates and cannot populate the relation registry."
        ),
        "research_limits": [
            "No intermediate candidate rankings or outputs were saved, so only answer-evidence prefixes are analyzed dynamically.",
            "Rule-based profile types describe output dimension counts and are not coffee taxonomies or learned clusters.",
            "Formal implications are conditional on the repeatedly viewed frozen output context and are not semantic entailments.",
            "No PCA, MDS, embedding, clustering, MMR, propagation weight, threshold or composite score was run or selected.",
        ],
        "private_detail": {
            "status": "OWNER_CONTROLLED_STORAGE",
            "sha256": artifact["sha256"],
            "bytes": artifact["bytes"],
        },
        "guards": {
            "fit_count": 0,
            "T_used": False,
            "subjective_evaluation_used": False,
            "embedding_or_cluster_fit": False,
            "relation_edges_created": 0,
            "output_or_default_changed": False,
            "trigger_or_stopping_rule_changed": False,
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
        default=R9_PUBLIC / "r9_semantic_lineage_report.json",
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
                "T_used": False,
                "private_sha256": result["private_detail"]["sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
