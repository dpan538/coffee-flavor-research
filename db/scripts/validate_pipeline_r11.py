#!/usr/bin/env python3
"""Blind R11 pipeline plumbing validation with synthetic labels only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def stable(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def synthetic_groups() -> list[dict]:
    candidates = [f"synthetic.descriptor.{index:02d}" for index in range(9)]
    rows = []
    for index in range(48):
        group_id = f"synthetic.group.{index:03d}"
        rows.append(
            {
                "group_id": group_id,
                "source_family_id": f"synthetic.family.{index % 8}",
                "c0": index % 8,
                "c1": index % 7,
                "evidence_count": index % 5,
                "labels": sorted({candidates[index % 9], candidates[(index * 5 + 1) % 9]}),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=R11 / "pipeline_validation.json")
    args = parser.parse_args()
    groups = synthetic_groups()
    for row in groups:
        row["fold"] = int(sha(row["group_id"])[:8], 16) % 3
        row["features"] = [
            *[1 if row["c0"] == value else 0 for value in range(8)],
            *[1 if row["c1"] == value else 0 for value in range(7)],
            row["evidence_count"],
        ]
        row["abstain"] = row["evidence_count"] == 0
        # Synthetic score ordering is a fixed hash permutation, not a fitted
        # estimator and not a function of any repository label.
        row["prediction"] = sorted(
            [f"synthetic.descriptor.{index:02d}" for index in range(9)],
            key=lambda candidate: sha(f"{row['group_id']}|{candidate}"),
        )[:3]

    folds = {fold: {row["group_id"] for row in groups if row["fold"] == fold} for fold in range(3)}
    overlap = any(folds[left] & folds[right] for left in folds for right in folds if left < right)
    if overlap:
        raise ValueError("SYNTHETIC_GROUP_LEAKAGE")
    if any(len(row["features"]) != 16 for row in groups):
        raise ValueError("FEATURE_ASSEMBLY_WIDTH_MISMATCH")
    if not any(row["abstain"] for row in groups) or not any(not row["abstain"] for row in groups):
        raise ValueError("ABSTENTION_HEAD_NOT_EXERCISED")

    # Exercise rank-metric plumbing on synthetic labels, but store no value:
    # only a checksum of the deterministic internal receipt is retained.
    metric_terms = []
    for row in groups:
        hits = [1 if candidate in row["labels"] else 0 for candidate in row["prediction"]]
        metric_terms.append(sum(hit / (rank + 1) for rank, hit in enumerate(hits)))
    metric_receipt_sha256 = sha(stable(metric_terms))

    report = {
        "contract_version": "r11.blind-pipeline-validation.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "PASS",
        "input_scope": "SYNTHETIC_LABELS_ONLY",
        "checks": {
            "deterministic_fold_construction": "PASS",
            "group_level_leakage_check": "PASS",
            "feature_assembly": "PASS",
            "abstention_head_plumbing": "PASS",
            "synthetic_metric_computation_executed": "PASS",
            "artifact_serialization": "PASS",
        },
        "fold_group_counts": {str(fold): len(values) for fold, values in folds.items()},
        "synthetic_group_count": len(groups),
        "synthetic_metric_receipt_sha256": metric_receipt_sha256,
        "attestation": {
            "fit_count": 0,
            "real_label_rows_read": 0,
            "real_data_model_vs_baseline_metrics_computed": 0,
            "real_data_model_vs_baseline_metrics_logged_printed_or_stored": 0,
            "contaminated_result": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(stable(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["attestation"]}, indent=2))


if __name__ == "__main__":
    main()
