#!/usr/bin/env python3
"""Rebuild every sealed R8 actual return with the original frozen finalizer.

This is inference/replay only.  It imports the R8 implementation instead of
copying or approximating ``finalize_result``.  The sealed R8 artifact is never
overwritten: reconstructed rows, metrics and group summaries must match it
exactly before a deterministic private R9 receipt can be written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import output_alignment_r8 as r8
import train_conditioning_r4 as assembly
from acquire_supervision_r5 import save

VERSION = "m2-r9.r8-actual-return-rebuild.v1"


def serialized_sha256(value: Any) -> str:
    raw = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode()
    return hashlib.sha256(raw).hexdigest()


def rebuild(owner: Path, receipt_path: Path) -> dict[str, Any]:
    contract = r8.verify_inputs(owner)
    sealed_path = owner / r8.FINAL_ARTIFACTS / "actual_returns.private.json"
    if not sealed_path.exists():
        raise FileNotFoundError("MISSING_SEALED_R8_ACTUAL_RETURNS")
    expected_sha = r8.read(r8.PUBLIC / "output_alignment_results.json")[
        "private_artifact_hashes"
    ]["actual_returns.private.json"]
    if r8.sha(sealed_path) != expected_sha:
        raise ValueError("SEALED_R8_ACTUAL_RETURNS_HASH_MISMATCH")

    input_hashes_before = {
        name: r8.sha(owner / name) for name in contract["input_hashes"]
    }
    data = r8.read(owner / "revisions/r6/matrix_cases.private.json")
    indices = r8.pair_index(data)
    bundles = {
        fold: assembly.model_bundle(
            r8.read(owner / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{fold}.model.json")
        )
        for fold in range(3)
    }
    record_ids = sorted(indices["C00"], key=r8.digest)
    rebuilt = []
    for generator in ("C00", "C01"):
        for record_id in record_ids:
            source = indices[generator][record_id]
            model_path = (
                owner
                / f"revisions/r1/cv/M2_R1_FINAL_FIXED_fold{source['fold']}.model.json"
            )
            rebuilt.append(
                r8.extract(source, bundles[source["fold"]], r8.sha(model_path))
            )

    sealed = r8.read(sealed_path)
    if rebuilt != sealed:
        raise ValueError("RETURN_OR_METRIC_REBUILD_MISMATCH")
    if serialized_sha256(rebuilt) != expected_sha:
        raise ValueError("REBUILT_SERIALIZATION_HASH_MISMATCH")

    summary, groups = r8.aggregate(rebuilt)
    saved_summary = r8.read(
        owner / r8.FINAL_ARTIFACTS / "aggregate_results.private.json"
    )
    for key, value in summary.items():
        if json.loads(json.dumps(value)) != saved_summary[key]:
            raise ValueError("AGGREGATE_REBUILD_MISMATCH:" + key)
    if groups != r8.read(
        owner / r8.FINAL_ARTIFACTS / "paired_group_deltas.private.json"
    ):
        raise ValueError("GROUP_REBUILD_MISMATCH")

    r8.verify_inputs(owner)
    input_hashes_after = {
        name: r8.sha(owner / name) for name in contract["input_hashes"]
    }
    if input_hashes_before != input_hashes_after:
        raise ValueError("FROZEN_INPUT_CHANGED_DURING_REBUILD")

    receipt = {
        "version": VERSION,
        "status": "PASS",
        "operation": "ORIGINAL_HELD_STATE_TO_ACTUAL_RETURN_AND_METRIC_REBUILD",
        "sealed_output_action": "VERIFIED_EXISTING_NO_HISTORY_OVERWRITE",
        "records": len(rebuilt),
        "generators": {
            generator: sum(row["policy"] == generator for row in rebuilt)
            for generator in ("C00", "C01")
        },
        "coffee_groups": len({row["group_id"] for row in rebuilt}),
        "original_finalizer_calls": len(rebuilt),
        "fit_count": 0,
        "question_reselection_count": 0,
        "actual_returns_sha256": expected_sha,
        "frozen_input_hashes_unchanged": True,
        "model_weights_or_question_parameters_changed": False,
        "r8_summary_and_group_metrics_exact": True,
    }
    save(receipt_path, receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    receipt_path = args.receipt or (
        args.owner_dir / "revisions/r9/rebuild_actual_returns_r8_receipt.private.json"
    )
    receipt = rebuild(args.owner_dir, receipt_path)
    print(json.dumps({**receipt, "receipt": str(receipt_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
