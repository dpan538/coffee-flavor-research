#!/usr/bin/env python3
"""Run a command while emitting public-safe progress heartbeats.

The child inherits stdout and stderr unchanged.  This wrapper does not impose a
second timeout or terminate the child: the CI job retains the authoritative
timeout and receives the child's original exit code.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.interval < 1 or args.interval > 60:
        parser.error("--interval must be between 1 and 60 seconds")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("a command is required after --")
    started = time.monotonic()
    child = subprocess.Popen(command)
    while child.poll() is None:
        time.sleep(args.interval)
        if child.poll() is None:
            elapsed = int(time.monotonic() - started)
            print(f"CI_HEARTBEAT elapsed={elapsed}s phase={args.phase}", flush=True)
    return child.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
