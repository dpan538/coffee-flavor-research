#!/usr/bin/env python3
"""Bounded M2 R4 registration, actual training, replay and publication."""

from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db/data/backend-sequential-model-v2/revisions/r4"
BASE = "12dfb7ae82bf0332909905971ffff1e6bc75cace"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, value, private=False):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    )
    if private:
        p.chmod(0o600)


def freeze(owner):
    from flavor_conditioning_r4 import protocol as runtime_protocol
    from train_conditioning_r4 import protocol as fit_protocol
    import alignment_metrics_r3

    dst = owner / "revisions/r4"
    if (OUT / "experiment_contract.json").exists():
        return verify(owner)
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    if head != BASE:
        raise ValueError("EXPECTED_R3_BASELINE_REQUIRED_NO_HISTORY_ROLLBACK")
    records = read(owner / "recovery_records.json")
    dev = [r for r in records if r["split"] == "DEVELOPMENT"]
    if len(dev) != 211 or len({r["group_id"] for r in dev}) != 187:
        raise ValueError("FROZEN_CORE_SCOPE_MISMATCH")
    deleted = subprocess.check_output(
        ["git", "ls-files", "--deleted"], cwd=ROOT, text=True
    ).splitlines()
    previous = read(owner / "revisions/r3/excluded_worktree_deletions.private.json")
    if sorted(deleted) != sorted(previous):
        raise ValueError("UNRELATED_DELETION_SCOPE_CHANGED")
    inputs = {
        "recovery_records.json": sha(owner / "recovery_records.json"),
        "revisions/r1/D0_folds.private.json": sha(
            owner / "revisions/r1/D0_folds.private.json"
        ),
        "revisions/r3/constraints_completion_manifest.private.json": sha(
            owner / "revisions/r3/constraints_completion_manifest.private.json"
        ),
    }
    contract = {
        "experiment_id": "M2_R4_K1_CONDITIONING_SHARED_RELATION_KEY_CASE",
        "registered_utc": now(),
        "baseline_sha": head,
        "primary_task": "Grouped recovery of fixed hidden positive fine mentions at fixed ASK Q4, RECORD_DERIVED_PROXY; not independent sensory truth",
        "primary_effect": "R3 raw_gap group macro; AKR minus A0; AK and AR explain the fixed 2x2 contrast",
        "primary_cost": "Actual ordinary offered options; context2questions/15options and final3to8 pool reported separately; no measured human time",
        "candidate_scope": "Each frozen outer base expert fine vocabulary before soft effects, identical A0/AK/AR/AKR and policies; all fixed targets retained",
        "metrics": alignment_metrics_r3.protocol(),
        "runtime": runtime_protocol(),
        "fitting": fit_protocol(),
        "data_inputs": inputs,
        "validation_scope": "Development-time coffee-group comparison only; historical17 and previously viewed R3 not new confirmation; participant isolation not inferred from compound keys",
        "auxiliary_task_limit": 1,
        "auxiliary_registration": "Source/identity/role and bounded same-representation on-off contrast must be frozen before any auxiliary fit",
        "information_origin": "Old main task uses frozen A for all answers: DERIVED_REUSE. Independently recorded B requires separate actual source adapter, not model-generated answers",
        "defaults": {
            "B2": "UNCHANGED",
            "FOUNDATION_CHECK": False,
            "research_only": True,
        },
        "preservation": "Old source/results/weights retained; historical code via baseline Git SHA and dependencies, no whole-repository immutability requirement",
        "scientific_outcomes": [
            "SUPPORTED_IN_DECLARED_SCOPE",
            "NO_IMPROVEMENT",
            "INCONCLUSIVE",
            "NOT_ESTIMABLE",
            "NOT_EVALUATED",
        ],
        "public_scope": "Only code, configuration, aggregate traces/metrics and hashes; individual trajectories/raw data/weights persistent private",
    }
    save(dst / "excluded_deletions.private.json", deleted, True)
    save(OUT / "experiment_contract.json", contract)
    save(dst / "experiment_contract.frozen.json", contract, True)
    save(
        OUT / "run_receipt.json",
        {
            "status": "FROZEN_BEFORE_R4_FITS",
            "first_observed_environment_clock_utc": "2026-09-05T23:45:28+00:00",
            "registered_utc": contract["registered_utc"],
            "baseline_sha": head,
            "contract_sha256": sha(OUT / "experiment_contract.json"),
            "default": "B2_UNCHANGED",
            "foundation_check": False,
            "baseline_remote_CI": "PASS",
            "baseline_remote_historical_replay": "PASS",
            "unrelated_deletions_excluded": len(deleted),
        },
    )
    return contract


def verify(owner):
    from flavor_conditioning_r4 import protocol as runtime_protocol
    from train_conditioning_r4 import protocol as fit_protocol

    contract = read(OUT / "experiment_contract.json")
    if sha(OUT / "experiment_contract.json") != sha(
        owner / "revisions/r4/experiment_contract.frozen.json"
    ):
        raise ValueError("R4_REGISTERED_CONTRACT_CHANGED")
    if (
        contract["runtime"] != runtime_protocol()
        or contract["fitting"] != fit_protocol()
    ):
        raise ValueError("R4_PROTOCOL_CHANGED_REQUIRES_EXPLICIT_DATED_VERSION")
    for name, digest in contract["data_inputs"].items():
        if sha(owner / name) != digest:
            raise ValueError("R4_FIXED_INPUT_CHANGED:" + name)
    return contract


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner-dir", type=Path, required=True)
    parser.add_argument(
        "--phase",
        choices=["freeze", "verify", "train", "retrain", "replay"],
        required=True,
    )
    parser.add_argument("--checkpoint-one", action="store_true")
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze(args.owner_dir)
    elif args.phase == "verify":
        verify(args.owner_dir)
    else:
        verify(args.owner_dir)
        if args.phase == "replay":
            from replay_conditioning_r4 import verify as replay_verified

            print(json.dumps(replay_verified(args.owner_dir), sort_keys=True))
        else:
            from train_conditioning_r4 import run

            run(
                args.owner_dir,
                OUT / "experiment_contract.json",
                checkpoint_one=args.checkpoint_one,
                fresh=args.phase == "retrain",
            )
