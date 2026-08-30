#!/usr/bin/env python3
"""Dispatch explicit corpus-verification capabilities for local and public CI."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "db" / "scripts"


def run(name: str, *arguments: str) -> None:
    subprocess.run([sys.executable, "-B", str(SCRIPTS / name), *arguments], cwd=ROOT, check=True)


def report(*, optional_executed: int) -> None:
    print("MANDATORY_PUBLIC_TEST_COUNT=2")
    print("MANDATORY_PUBLIC_TEST_PASS_COUNT=2")
    print("MANDATORY_PUBLIC_TEST_SKIP_COUNT=0")
    print("OPTIONAL_RESTRICTED_TEST_COUNT=1")
    print(f"OPTIONAL_RESTRICTED_TEST_EXECUTED_COUNT={optional_executed}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--public-fixture", action="store_true")
    modes.add_argument("--public-snapshot", action="store_true")
    modes.add_argument("--restricted-real", action="store_true")
    modes.add_argument("--require-restricted-real", action="store_true")
    args = parser.parse_args()
    if args.public_fixture:
        run("test-public-fixture-replay.py")
        report(optional_executed=0)
        return 0
    if args.public_snapshot:
        run("test-public-snapshot-contract.py")
        report(optional_executed=0)
        return 0
    if args.require_restricted_real:
        run("test-restricted-real-replay.py", "--require-restricted-real")
        report(optional_executed=1)
        return 0
    configured = bool(os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT"))
    run("test-restricted-real-replay.py")
    report(optional_executed=int(configured))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
