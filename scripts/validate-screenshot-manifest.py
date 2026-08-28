#!/usr/bin/env python3
"""Validate real portfolio screenshot assets and their capture metadata."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/portfolio/SCREENSHOT_MANIFEST.md"
REQUIRED_ROUTES = {"/", "/atlas?view=index&q=cacao&compare=jasmine,dark-chocolate", "/methodology#project-status"}


def main() -> int:
    failures: list[str] = []
    if not MANIFEST.is_file():
        print("SCREENSHOT_MANIFEST_PASS=false", file=sys.stderr)
        return 1

    rows: list[list[str]] = []
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "File | Route" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 7 and cells[0].endswith(".png`"):
            rows.append(cells)

    desktop = 0
    mobile = 0
    routes: set[str] = set()
    for cells in rows:
        filename = cells[0].strip("`")
        route = cells[1].strip("`")
        viewport = cells[2].strip("`")
        capture_date = cells[3]
        browser = cells[4]
        commit_sha = cells[5].strip("`")
        recorded_hash = cells[6].strip("`")
        path = MANIFEST.parent / "assets" / filename
        routes.add(route)
        if not path.is_file():
            failures.append(f"missing screenshot: {path.relative_to(ROOT)}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != recorded_hash:
            failures.append(f"hash mismatch: {path.relative_to(ROOT)}")
        match = re.fullmatch(r"(\d+)x(\d+)", viewport)
        if not match:
            failures.append(f"invalid viewport: {viewport}")
        elif int(match.group(1)) <= 520:
            mobile += 1
        else:
            desktop += 1
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", capture_date):
            failures.append(f"invalid capture date: {capture_date}")
        if "Chrom" not in browser:
            failures.append(f"unsupported browser receipt: {browser}")
        if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
            failures.append(f"invalid commit SHA: {commit_sha}")
        else:
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"],
                cwd=ROOT,
                capture_output=True,
                check=False,
            )
            if result.returncode != 0:
                failures.append(f"screenshot commit is not in repository: {commit_sha}")

    if len(rows) < 4:
        failures.append(f"expected at least four screenshot rows, found {len(rows)}")
    if not REQUIRED_ROUTES.issubset(routes):
        failures.append("required landing, interaction, or status route is absent")
    if desktop < 3 or mobile < 1:
        failures.append(f"expected at least three desktop and one mobile capture; got {desktop}/{mobile}")

    for message in failures:
        print(message, file=sys.stderr)
    print(f"DESKTOP_SCREENSHOT_COUNT={desktop}")
    print(f"MOBILE_SCREENSHOT_COUNT={mobile}")
    print(f"SCREENSHOT_MANIFEST_FAILURE_COUNT={len(failures)}")
    print(f"SCREENSHOT_MANIFEST_PASS={'true' if not failures else 'false'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
