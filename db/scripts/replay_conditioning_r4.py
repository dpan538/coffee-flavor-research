"""Seal and numerically replay R4 artifacts without refitting any model."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import alignment_metrics_r3 as metric
import flavor_conditioning_r4 as rt
import train_conditioning_r4 as training
from run_m2_r4 import ROOT, OUT, read, save, sha, now


def seal(owner):
    dst = owner / "revisions/r4"
    paths = []
    for name in ["models", "features", "verification"]:
        paths.extend(p for p in (dst / name).glob("*.json") if p.is_file())
    paths.extend(
        p
        for p in dst.glob("*.private.json")
        if p.name != "completion_manifest.private.json"
    )
    paths.extend(p for p in dst.glob("*.frozen.json"))
    manifest = {
        "sealed_utc": now(),
        "artifacts": {str(p.relative_to(owner)): sha(p) for p in sorted(set(paths))},
        "code": {
            n: sha(ROOT / "db/scripts" / n)
            for n in [
                "flavor_conditioning_r4.py",
                "train_conditioning_r4.py",
                "data_connections_r4.py",
                "verify_conditioning_r4.py",
                "alignment_metrics_r3.py",
                "run_m2_r4.py",
                "replay_conditioning_r4.py",
            ]
        },
        "contract_sha256": sha(OUT / "experiment_contract.json"),
    }
    save(dst / "completion_manifest.private.json", manifest, True)
    return manifest


def close(a, b):
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (float, int)) and isinstance(b, (float, int)):
        return bool(np.isclose(a, b, rtol=0, atol=1e-12))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(close(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b, strict=True))
    return a == b


def check_row(row):
    actual = metric.evaluate(
        row["ranking"],
        row["episode"]["relevance"],
        row["fixed_candidates"],
        excluded_visible=row["episode"]["visible"],
    )
    for key in ["raw_gap", "ndcg", "recall", "M", "M_star", "opportunity_gap"]:
        if not close(actual[key], row[key]):
            raise ValueError("REPLAY_METRIC_MISMATCH:" + key)
    return 1


def verify(owner):
    dst = owner / "revisions/r4"
    manifest = read(dst / "completion_manifest.private.json")
    if manifest["contract_sha256"] != sha(OUT / "experiment_contract.json"):
        raise ValueError("REGISTERED_CONTRACT_MISMATCH")
    for name, digest in manifest["artifacts"].items():
        if sha(owner / name) != digest:
            raise ValueError("SEALED_PRIVATE_ARTIFACT_CHANGED:" + name)
    for name, digest in manifest["code"].items():
        if sha(ROOT / "db/scripts" / name) != digest:
            raise ValueError("SEALED_CODE_CHANGED:" + name)
    endpoint_count = gain_count = aux_count = 0
    outer = []
    for fold in range(3):
        item = read(dst / f"outer{fold}_results.private.json")
        outer.append(item)
        endpoint_count += sum(
            check_row(r) for r in item["fixed_rows"] + item["policy_rows"]
        )
        allbranches = item["held_branches"] + [
            r for rows in item["inner_branches"].values() for r in rows
        ]
        for row in allbranches:
            a, s = row["outcomes"]["ASK"], row["outcomes"]["SKIP"]
            check_row(a)
            check_row(s)
            gain = (
                s["raw_gap"] - a["raw_gap"]
                if a["raw_gap"] is not None and s["raw_gap"] is not None
                else None
            )
            if not close(gain, row["gain"]):
                raise ValueError("SEALED_GAIN_RECALCULATION_MISMATCH")
            gain_count += 1
        model = read(owner / item["policy_model_path"])
        rt.check_bundle(model)
        for decision in [r for r in item["policy_rows"] if r["model"] == "KEY_CASE"]:
            branch = next(
                r
                for r in item["held_branches"]
                if r["record_id"] == decision["record_id"]
            )
            action = (
                "ASK"
                if rt.trigger_prediction(branch["features"], model["trigger"]) > 0.5
                else "SKIP"
            )
            if decision["q2_decision"]["action"] != action:
                raise ValueError("SEALED_KEY_CASE_DECISION_MISMATCH")
    aux = read(dst / "auxiliary_results.private.json")
    aux_count = sum(check_row(r) for r in aux["rows"])
    for task in ["MAIN_RECORD_DERIVED", "CROSS_GRADER_REVELATION"]:
        rows = [r for r in aux["rows"] if r["task"] == task]
        for variant in ["AKR", "AKR_AUX"]:
            actual = training.scalar_summary([r for r in rows if r["model"] == variant])
            if not close(actual, aux["summary"]["results"][task][variant]):
                raise ValueError("AUXILIARY_SUMMARY_REPLAY_MISMATCH")
        if not close(
            training.paired(rows, "AKR_AUX", "AKR"), aux["summary"]["contrasts"][task]
        ):
            raise ValueError("AUXILIARY_CONTRAST_REPLAY_MISMATCH")
    summary = read(dst / "final_summary.private.json")
    if not close(summary["auxiliary"], aux["summary"]):
        raise ValueError("FINAL_AUXILIARY_SUMMARY_MISMATCH")
    final = read(owner / summary["final"]["owner_relative_model_path"])
    rt.check_bundle(final)
    if (
        sha(owner / summary["final"]["owner_relative_model_path"])
        != summary["final"]["sha256"]
    ):
        raise ValueError("FINAL_MODEL_HASH_MISMATCH")
    receipt = {
        "operation": "SEALED_ARTIFACT_AND_NUMERICAL_REPLAY",
        "fit_calls": 0,
        "main_endpoint_rankings_recomputed": endpoint_count,
        "ASK_SKIP_gains_recomputed": gain_count,
        "auxiliary_rankings_recomputed": aux_count,
        "private_artifacts_verified": len(manifest["artifacts"]),
        "model_parameters_reloaded": True,
        "scope": "Scores/matching/gain/policy/auxiliary summaries recalculated; actual fresh live CLI and held trajectories are separately verified",
        "completion_sha256": sha(dst / "completion_manifest.private.json"),
    }
    training.publish(owner, outer, summary["auxiliary"], summary["final"], receipt)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner-dir", type=Path, required=True)
    p.add_argument("--seal", action="store_true")
    a = p.parse_args()
    if a.seal:
        seal(a.owner_dir)
    print(json.dumps(verify(a.owner_dir), sort_keys=True))
