#!/usr/bin/env python3
"""Explicit owner-controlled real-data replay; never treated as a public CI pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "db" / "data" / "ci" / "RESTRICTED_REAL_REPLAY_RECEIPT.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory() -> dict[str, str]:
    roots = [
        ROOT / "db" / "data" / "current",
        ROOT / "db" / "data" / "post20k-extension-staging",
        ROOT / "db" / "data" / "post30k-extension-staging",
        ROOT / "db" / "data" / "post40k-extension-staging",
    ]
    return {
        path.relative_to(ROOT).as_posix(): sha(path)
        for root in roots for path in sorted(root.glob("SHA256SUMS"))
    }


def roots(root: Path) -> dict[str, Path]:
    candidates = {
        "round3m": root / "coffee-flavor-round3m-restricted",
        "post20": root / "coffee-flavor-round3m-post20k",
        "post30": root / "coffee-flavor-round3m-post30k",
        "post40": root / "coffee-flavor-round3m-post40k",
    }
    if (root / "CAPTURE_MANIFEST.json").is_file():
        candidates["round3m"] = root
    missing = [name for name, path in candidates.items() if not path.is_dir()]
    if missing:
        raise RuntimeError(f"restricted root is incomplete; missing {', '.join(missing)}")
    return candidates


def run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-restricted-real", action="store_true")
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args()
    configured = os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT")
    if not configured:
        if args.require_restricted_real:
            raise RuntimeError("COFFEE_FLAVOR_RESTRICTED_ROOT is required for --require-restricted-real")
        print("RESTRICTED_REAL_REPLAY_EXECUTED=false")
        print("RESTRICTED_REAL_REPLAY_STATUS=NOT_EXECUTED_PUBLIC_CI_RESTRICTED_INPUT_INTENTIONALLY_UNAVAILABLE")
        return 0
    resolved = roots(Path(configured).resolve())
    before = inventory()
    env = os.environ.copy()
    env.update({
        "ROUND3M_RESTRICTED_ROOT": str(resolved["round3m"]),
        "POST20K_RESTRICTED_ROOT": str(resolved["post20"]),
        "POST30K_RESTRICTED_ROOT": str(resolved["post30"]),
        "POST40K_RESTRICTED_ROOT": str(resolved["post40"]),
        "BATCH6_POST30_RESTRICTED_ROOT": str(resolved["post30"] / "post30k_extension"),
    })
    for test in [
        "test-current-descriptor-data.py", "test-batch3-candidate-cleaning.py",
        "test-post20k-extension.py", "test-batch4-cleaned-30k.py",
        "test-post30k-extension.py", "test-batch6-semantic-corpus.py",
        "test-post40k-extension.py", "test-round3m-live-adapters.py",
    ]:
        run([sys.executable, "-B", str(ROOT / "db" / "scripts" / test)], env)
    after = inventory()
    if before != after:
        raise RuntimeError("restricted-real replay changed public SHA256 receipts")
    receipt = {
        "contract_version": "ci-restricted-real-replay.v1",
        "mode": "restricted-real",
        "restricted_root_environment_variable": "COFFEE_FLAVOR_RESTRICTED_ROOT",
        "local_restricted_real_replay_executed": True,
        "local_restricted_real_replay_pass": True,
        "local_restricted_public_byte_identity_pass": True,
        "remote_restricted_real_replay_executed": False,
        "remote_restricted_real_replay_status": "NOT_EXECUTED_PUBLIC_CI_RESTRICTED_INPUT_INTENTIONALLY_UNAVAILABLE",
        "restricted_source_text_published": False,
    }
    if args.write_receipt:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("LOCAL_RESTRICTED_REAL_REPLAY_EXECUTED=true")
    print("LOCAL_RESTRICTED_REAL_REPLAY_PASS=true")
    print("LOCAL_RESTRICTED_PUBLIC_BYTE_IDENTITY_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
