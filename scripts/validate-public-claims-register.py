#!/usr/bin/env python3
"""Validate public quantitative claim markers against the evidence register."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs/portfolio/PUBLIC_CLAIMS_REGISTER.tsv"
SURFACES = [
    ROOT / "README.md",
    ROOT / "PORTFOLIO.md",
    ROOT / "PROJECT_STATUS.md",
    ROOT / "app/routes/methodology.tsx",
]
REQUIRED_COLUMNS = [
    "claim_id",
    "public_claim",
    "claim_category",
    "allowed_surface",
    "evidence_path",
    "evidence_sha_or_version",
    "status",
    "qualification",
    "last_reviewed_at",
]


def main() -> int:
    failures: list[str] = []
    if not REGISTER.is_file():
        print("PUBLIC_CLAIMS_REGISTER_CREATED=false", file=sys.stderr)
        return 1

    with REGISTER.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != REQUIRED_COLUMNS:
            failures.append("public claims register columns do not match the contract")
        rows = list(reader)

    claims: dict[str, dict[str, str]] = {}
    for row_number, row in enumerate(rows, 2):
        claim_id = row.get("claim_id", "")
        if not re.fullmatch(r"[A-Z][A-Z0-9_]+", claim_id):
            failures.append(f"row {row_number}: invalid claim_id {claim_id!r}")
            continue
        if claim_id in claims:
            failures.append(f"row {row_number}: duplicate claim_id {claim_id}")
        claims[claim_id] = row
        for column in REQUIRED_COLUMNS:
            if not row.get(column, "").strip():
                failures.append(f"row {row_number}: {claim_id} has empty {column}")
        evidence = ROOT / row.get("evidence_path", "")
        if not evidence.exists():
            failures.append(f"row {row_number}: evidence path is missing: {evidence}")

    marker_pattern = re.compile(r"claim:\s*([A-Z][A-Z0-9_]+)")
    marker_ids: list[str] = []
    for surface in SURFACES:
        if not surface.is_file():
            failures.append(f"public claim surface is missing: {surface.relative_to(ROOT)}")
            continue
        marker_ids.extend(marker_pattern.findall(surface.read_text(encoding="utf-8")))

    for marker_id in sorted(set(marker_ids)):
        if marker_id not in claims:
            failures.append(f"unregistered public claim marker: {marker_id}")
    for claim_id in sorted(claims):
        if claim_id not in marker_ids:
            failures.append(f"registered claim is unused on a public surface: {claim_id}")

    for message in failures:
        print(message, file=sys.stderr)
    print("PUBLIC_CLAIMS_REGISTER_CREATED=true")
    print(f"PUBLIC_QUANTITATIVE_CLAIM_COUNT={len(claims)}")
    print(f"PUBLIC_QUANTITATIVE_CLAIM_MARKER_COUNT={len(marker_ids)}")
    print(f"PUBLIC_CLAIMS_REGISTER_FAILURE_COUNT={len(failures)}")
    print(f"PUBLIC_CLAIMS_REGISTER_COVERAGE_PASS={'true' if not failures else 'false'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
