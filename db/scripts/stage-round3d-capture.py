#!/usr/bin/env python3
"""Create a deterministic, reviewable staging bundle for PostgreSQL import.

This command does not promote rows to observations. It validates capture files
and emits JSONL for calibration.capture_import_row. Promotion remains a
separate, authorized transaction after governance review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    args = parser.parse_args()

    validator = ROOT / "db" / "scripts" / "validate-round3d-capture.py"
    subprocess.run(["python3", str(validator), str(args.capture_dir)], check=True)

    rows: list[dict[str, object]] = []
    for path in sorted(args.capture_dir.glob("*.csv")):
        with path.open(encoding="utf-8", newline="") as handle:
            for row_number, row in enumerate(csv.DictReader(handle), start=2):
                rows.append(
                    {
                        "source_file": path.name,
                        "source_row_number": row_number,
                        "row_payload": row,
                    }
                )
    args.output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )
    args.output_jsonl.write_text(content, encoding="utf-8")
    print(f"STAGED_CAPTURE_ROW_COUNT={len(rows)}")
    print(f"STAGED_CAPTURE_SHA256={hashlib.sha256(content.encode()).hexdigest()}")
    print("STAGED_CAPTURE_PROMOTED=false")
    print("CAPTURE_STAGING_PASS=true")


if __name__ == "__main__":
    main()
