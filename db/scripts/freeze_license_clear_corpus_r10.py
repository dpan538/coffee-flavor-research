#!/usr/bin/env python3
"""Freeze the canonical license-clear R10 training corpus without fitting."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
SOURCE_LEDGER = "db/data/current/CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv"
DEFAULT_ELIGIBILITY = R10 / "eligibility_tiers.json"
DEFAULT_OWNER = Path(
    "/Users/jarlgiovanni/Desktop/Coffee_Flavor_Research_Private/"
    "backend-sequential-model-v2/revisions/r10"
)
FOLDS = 3


def stable_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_or_git(relative_path: str) -> tuple[str, str]:
    path = ROOT / relative_path
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    return text, sha(text.encode())


def true(value: str | None) -> bool:
    return (value or "").lower() == "true"


def build(eligibility_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    eligibility = json.loads(eligibility_path.read_text())
    tier = eligibility["tiers"]["NON_COMMERCIAL_RESEARCH"]
    if tier["model_eligible_assertion_count"] < 500 or tier["source_family_count"] < 3:
        raise SystemExit("R10_GO_GATE_NOT_MET_CANNOT_FREEZE")
    allowed_families = set(tier["source_family_assertion_counts"])
    registry = json.loads((R9 / "output_policy_contract.json").read_text())[
        "concept_role_registry"
    ]
    text, source_sha = file_or_git(SOURCE_LEDGER)
    rows = list(csv.DictReader(io.StringIO(text), delimiter="\t"))
    selected = [
        row
        for row in rows
        if row["source_family_id"] in allowed_families
        and row["rights_state"] == "AFFIRMATIVE"
        and row["semantic_class"] == "STRICT_FLAVOR"
        and true(row["counts_as_cleaned_descriptor_output"])
        and true(row["counts_as_record_unique_descriptor"])
        and row["canonical_concept_id"] in registry
        and registry[row["canonical_concept_id"]]["role"] == "NAMED_DESCRIPTOR"
    ]
    by_group: dict[str, dict[str, set[str]]] = {}
    for row in selected:
        group_id = row["coffee_identity_id"]
        if not group_id or "unknown" in group_id.lower() or "unresolved" in group_id.lower():
            raise ValueError("UNIDENTIFIED_COFFEE_REACHED_FREEZE")
        group = by_group.setdefault(
            group_id,
            {"families": set(), "records": set(), "descriptors": set()},
        )
        group["families"].add(row["source_family_id"])
        group["records"].add(row["effective_record_id"])
        group["descriptors"].add(row["canonical_concept_id"])
    if any(len(value["families"]) != 1 for value in by_group.values()):
        raise ValueError("CROSS_FAMILY_COFFEE_IDENTITY_REQUIRES_REVIEW")

    by_family: dict[str, list[str]] = defaultdict(list)
    for group_id, value in by_group.items():
        by_family[next(iter(value["families"]))].append(group_id)
    fold_map = {}
    for family, group_ids in by_family.items():
        ordered = sorted(group_ids, key=lambda value: hashlib.sha256(value.encode()).hexdigest())
        for index, group_id in enumerate(ordered):
            fold_map[group_id] = index % FOLDS
    groups = [
        {
            "coffee_group_id": group_id,
            "source_family_id": next(iter(value["families"])),
            "effective_record_ids": sorted(value["records"]),
            "descriptor_ids": sorted(value["descriptors"]),
            "outer_fold": fold_map[group_id],
        }
        for group_id, value in sorted(by_group.items())
    ]
    private = {
        "contract_version": "r10.license-clear-training-corpus.v1",
        "eligibility_tier": "NON_COMMERCIAL_RESEARCH",
        "source_ledger": SOURCE_LEDGER,
        "source_ledger_sha256": source_sha,
        "eligibility_sha256": sha(eligibility_path.read_bytes()),
        "candidate_ids": sorted({cid for group in groups for cid in group["descriptor_ids"]}),
        "groups": groups,
        "guards": {
            "training_run_count": 0,
            "user_subjective_rating_used": False,
            "protected_historical_regression_set_used": False,
            "unmentioned_descriptor_encoded_as_negative": False,
            "coffee_group_overlap_across_folds": False,
        },
    }
    raw = stable_bytes(private)
    group_counts = Counter(group["source_family_id"] for group in groups)
    occurrence_counts = Counter(
        group["source_family_id"] for group in groups for _ in group["descriptor_ids"]
    )
    manifest = {
        "contract_version": "r10.license-clear-training-corpus-manifest.v1",
        "status": "FROZEN_TRAINING_NOT_RUN",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "eligibility_tier": "NON_COMMERCIAL_RESEARCH",
        "gate_eligible_source_assertion_count": tier["model_eligible_assertion_count"],
        "gate_source_family_count": tier["source_family_count"],
        "canonical_training_occurrence_count": sum(len(group["descriptor_ids"]) for group in groups),
        "canonical_training_candidate_count": len(private["candidate_ids"]),
        "coffee_group_count": len(groups),
        "effective_record_count": len({rid for group in groups for rid in group["effective_record_ids"]}),
        "training_source_family_count": len(group_counts),
        "coffee_group_counts_by_source_family": dict(sorted(group_counts.items())),
        "canonical_occurrence_counts_by_source_family": dict(sorted(occurrence_counts.items())),
        "outer_fold_group_counts": {
            str(fold): sum(group["outer_fold"] == fold for group in groups)
            for fold in range(FOLDS)
        },
        "evaluable_group_count_at_least_two_descriptors": sum(
            len(group["descriptor_ids"]) >= 2 for group in groups
        ),
        "private_corpus": {"sha256": sha(raw), "bytes": len(raw)},
        "source_ledger_sha256": source_sha,
        "eligibility_sha256": sha(eligibility_path.read_bytes()),
        "scope": "CANONICAL_NAMED_DESCRIPTOR_POSITIVE_RECOVERY_ONLY",
        "training_run_count": 0,
    }
    return private, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eligibility", type=Path, default=DEFAULT_ELIGIBILITY)
    parser.add_argument("--owner-dir", type=Path, default=DEFAULT_OWNER)
    parser.add_argument("--output", type=Path, default=R10 / "training_corpus_manifest.json")
    args = parser.parse_args()
    private, manifest = build(args.eligibility)
    args.owner_dir.mkdir(parents=True, exist_ok=True)
    private_path = args.owner_dir / "training_corpus.private.json"
    private_path.write_bytes(stable_bytes(private))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(stable_bytes(manifest))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
