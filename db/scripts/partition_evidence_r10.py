#!/usr/bin/env python3
"""Partition the 480 non-strict C01 output occurrences into four R10 buckets."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
DEFAULT_INPUT = Path("/private/tmp/r9_semantic_integrity_after_relation_contract.private.json")
DEFAULT_OUTPUT = R10 / "evidence_partition_r10.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bucket(row: dict[str, Any]) -> str:
    if row["strict_assertion_trace_ready"]:
        raise ValueError("STRICT_ROW_NOT_PART_OF_NON_STRICT_PARTITION")
    if row["selected_or_confirmed_direct"]:
        return "RECOVERABLE_DIRECT"
    if row["evidence_status"] == "NO_CURRENT_ANSWER_SEMANTIC_TRACE":
        return "INSUFFICIENT_EVIDENCE_ABSTAIN"
    if row["specificity_status"] in {
        "MIDDLE_FROM_DIRECTION_REQUIRES_RELATION_EDGE",
        "SPECIFIC_FROM_BROADER_OR_SIBLING_REQUIRES_RELATION_EDGE",
    }:
        return "REQUIRES_OWNER_ONTOLOGY_REVIEW"
    if row["evidence_status"] == "SUPPORTED_DIMENSION_COMPATIBILITY_ONLY":
        return "SHARED_DIMENSION_ONLY"
    raise ValueError("UNPARTITIONED_NON_STRICT_OCCURRENCE")


def action(value: str) -> str:
    return {
        "RECOVERABLE_DIRECT": "BUILD_DIRECT_TRACE_AND_MARK_STRICT",
        "SHARED_DIMENSION_ONLY": "KEEP_EXPLICITLY_NON_STRICT",
        "INSUFFICIENT_EVIDENCE_ABSTAIN": "REMOVE_FROM_MAIN_AND_SECONDARY_NO_BACKFILL",
        "REQUIRES_OWNER_ONTOLOGY_REVIEW": "KEEP_NON_STRICT_AND_QUEUE_RELATION_REVIEW",
    }[value]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic-audit", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    public = json.loads((R9 / "r9_semantic_integrity_audit.json").read_text())
    expected_sha = public["private_detail"]["sha256"]
    if sha256(args.semantic_audit) != expected_sha:
        raise SystemExit("R9_SEMANTIC_AUDIT_PRIVATE_HASH_MISMATCH")
    audit = json.loads(args.semantic_audit.read_text())
    c01_cases = [case for case in audit["cases"] if case["generator"] == "C01"]
    strict = []
    partition = []
    case_summaries = []
    for case in c01_cases:
        case_partition = []
        before = case["descriptor_evidence"]
        for row in before:
            occurrence_id = hashlib.sha256(
                (
                    f"{case['record_id']}|{row['panel']}|{row['position']}|"
                    f"{row['descriptor_id']}"
                ).encode()
            ).hexdigest()
            if row["strict_assertion_trace_ready"]:
                strict.append(occurrence_id)
                continue
            value = bucket(row)
            item = {
                "occurrence_id": occurrence_id,
                "record_id": case["record_id"],
                "group_id": case["group_id"],
                "panel": row["panel"],
                "position": row["position"],
                "descriptor_id": row["descriptor_id"],
                "bucket": value,
                "runtime_action": action(value),
                "evidence_status": row["evidence_status"],
                "specificity_status": row["specificity_status"],
                "registered_dimensions": row["registered_dimensions"],
                "strict_assertion_after_r10": value == "RECOVERABLE_DIRECT",
            }
            partition.append(item)
            case_partition.append(item)
        abstained = [
            row
            for row in case_partition
            if row["bucket"] == "INSUFFICIENT_EVIDENCE_ABSTAIN"
        ]
        remaining_count = len(before) - len(abstained)
        case_summaries.append(
            {
                "record_id": case["record_id"],
                "group_id": case["group_id"],
                "before_pool_count": len(before),
                "abstained_count": len(abstained),
                "after_pool_count": remaining_count,
                "comparison_executable_after_abstention": remaining_count >= 3,
            }
        )
    if len(partition) != 480:
        raise SystemExit(f"EXPECTED_480_NON_STRICT_OCCURRENCES_FOUND_{len(partition)}")
    counts = Counter(row["bucket"] for row in partition)
    for required in (
        "RECOVERABLE_DIRECT",
        "SHARED_DIMENSION_ONLY",
        "INSUFFICIENT_EVIDENCE_ABSTAIN",
        "REQUIRES_OWNER_ONTOLOGY_REVIEW",
    ):
        counts.setdefault(required, 0)
    strict_after = len(strict) + counts["RECOVERABLE_DIRECT"]
    denominator_after = len(strict) + len(partition) - counts["INSUFFICIENT_EVIDENCE_ABSTAIN"]
    report = {
        "contract_version": "r10.evidence-partition.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": {
            "path": str(args.semantic_audit),
            "sha256": expected_sha,
            "generator": "C01",
            "T_used": False,
            "participant_rating_used": False,
        },
        "bucket_counts": {key: counts[key] for key in sorted(counts)},
        "strict_evidence": {
            "before": {
                "strict_occurrences": len(strict),
                "output_occurrences": len(strict) + len(partition),
                "rate": len(strict) / (len(strict) + len(partition)),
            },
            "after_abstention": {
                "strict_occurrences": strict_after,
                "output_occurrences": denominator_after,
                "rate": strict_after / denominator_after,
                "abstained_occurrences": counts["INSUFFICIENT_EVIDENCE_ABSTAIN"],
            },
        },
        "runtime_contract": {
            "remove_bucket": "INSUFFICIENT_EVIDENCE_ABSTAIN",
            "backfill": False,
            "shared_dimension_rows_presented_as_strict": False,
            "owner_relation_edges_added": 0,
            "comparison_underflow_cases": sum(
                not row["comparison_executable_after_abstention"] for row in case_summaries
            ),
        },
        "cases": case_summaries,
        "partition": partition,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "bucket_counts": report["bucket_counts"],
                "strict_evidence": report["strict_evidence"],
                "comparison_underflow_cases": report["runtime_contract"][
                    "comparison_underflow_cases"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
