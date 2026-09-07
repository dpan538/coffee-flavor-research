#!/usr/bin/env python3
"""Compute the R10 gate from committed, script-generated artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
DEFAULT_OUTPUT = R10 / "go_no_go.json"


def read(name: str) -> dict[str, Any]:
    return json.loads((R10 / name).read_text())


def digest(name: str) -> str:
    return hashlib.sha256((R10 / name).read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    eligibility = read("eligibility_tiers.json")
    licenses = read("license_resolution_report.json")
    acquisition = read("acquisition_manifest.json")
    evidence = read("evidence_partition_r10.json")
    corpus = read("training_corpus_manifest.json")
    tier = eligibility["tiers"]["NON_COMMERCIAL_RESEARCH"]
    n_eligible = tier["model_eligible_assertion_count"]
    families = tier["source_family_count"]
    if n_eligible >= 500 and families >= 3:
        verdict = "GO"
    elif 200 <= n_eligible < 500:
        verdict = "CONDITIONAL"
    else:
        verdict = "NO_GO"
    report = {
        "contract_version": "r10.go-no-go.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "eligibility_tier": "NON_COMMERCIAL_RESEARCH",
        "N_eligible": n_eligible,
        "source_family_count": families,
        "source_family_assertion_counts": tier["source_family_assertion_counts"],
        "threshold": {
            "GO": "N_eligible >= 500 AND source_family_count >= 3",
            "CONDITIONAL": "200 <= N_eligible < 500",
            "NO_GO": "N_eligible < 200",
        },
        "verdict": verdict,
        "can_train_on_license_clear_data": verdict == "GO",
        "commercial_grade_model_eligible_assertion_count": eligibility["tiers"][
            "COMMERCIAL_GRADE"
        ]["model_eligible_assertion_count"],
        "unknown_resolution": licenses["summary"],
        "new_acquisition": {
            "query_count": acquisition["query_count"],
            "license_filtered_discovery_candidate_count": acquisition[
                "license_filtered_discovery_candidate_count"
            ],
            "new_record_count": acquisition["new_record_count"],
            "gate_dependency": acquisition["gate_dependency"],
        },
        "exact_query_filters": [
            {
                "query_id": row["query_id"],
                "source_system": row["source_system"],
                "url": row["url"],
                "status": row["status"],
                "response_sha256": row.get("response_sha256"),
            }
            for row in acquisition["queries"]
        ],
        "frozen_training_corpus": {
            "status": corpus["status"],
            "canonical_training_occurrence_count": corpus[
                "canonical_training_occurrence_count"
            ],
            "canonical_training_candidate_count": corpus[
                "canonical_training_candidate_count"
            ],
            "coffee_group_count": corpus["coffee_group_count"],
            "training_source_family_count": corpus["training_source_family_count"],
            "outer_fold_group_counts": corpus["outer_fold_group_counts"],
            "training_run_count": corpus["training_run_count"],
        },
        "evidence_correctness": {
            "bucket_counts": evidence["bucket_counts"],
            "strict_evidence_rate_before": evidence["strict_evidence"]["before"]["rate"],
            "strict_evidence_rate_after_abstention": evidence["strict_evidence"][
                "after_abstention"
            ]["rate"],
            "comparison_underflow_cases": evidence["runtime_contract"][
                "comparison_underflow_cases"
            ],
        },
        "training_execution": {
            "gate_state": "ELIGIBLE_TO_LIFT_PAUSE" if verdict == "GO" else "PAUSED",
            "fit_count_this_run": 0,
            "status": "NOT_RUN_REQUIRES_EXPLICIT_IN_CHAT_CONFIRMATION",
            "production_default_changed": False,
            "protected_regression_set_used": False,
        },
        "diagnosis": {
            "existing_license_clear_training_data": "SUFFICIENT" if verdict == "GO" else "INSUFFICIENT",
            "historical_unknown_block": (
                "UNRESOLVED_RIGHTS_METADATA_AND_PERMISSION_PROBLEM_NOT_A_ROW_COUNT_PROBLEM"
                if licenses["summary"]["resolved_assertion_count"] == 0
                else "PARTLY_RESOLVED_METADATA_PROBLEM"
            ),
            "canonical_mapping_bottleneck": (
                f"Only {corpus['canonical_training_occurrence_count']} governed, record-unique "
                f"named-descriptor occurrences across {corpus['coffee_group_count']} coffee groups "
                f"enter the frozen canonical training table, despite {n_eligible} license-eligible "
                "source assertions."
            ),
        },
        "artifact_sha256": {
            name: digest(name)
            for name in (
                "license_resolution_report.json",
                "eligibility_tiers.json",
                "acquisition_manifest.json",
                "evidence_partition_r10.json",
                "training_corpus_manifest.json",
            )
        },
    }
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "N_eligible": n_eligible,
                "source_family_count": families,
                "verdict": verdict,
                "fit_count": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
