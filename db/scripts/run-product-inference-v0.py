#!/usr/bin/env python3
"""Inspect one committed product-inference V0 policy case as JSON."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "product-inference-v0"


def rows(name: str) -> list[dict[str, str]]:
    with (DATA / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    cases = {row["inference_case_id"]: row for row in rows("PRODUCT_INFERENCE_CASE.tsv")}
    results = {row["inference_case_id"]: row for row in rows("PRODUCT_INFERENCE_RESULT.tsv")}
    if args.case_id not in cases:
        parser.error(f"unknown case id: {args.case_id}")
    explanations = [
        row for row in rows("PRODUCT_OUTPUT_EXPLANATION.tsv")
        if row["inference_case_id"] == args.case_id
    ]
    print(
        json.dumps(
            {
                "case": cases[args.case_id],
                "result": results[args.case_id],
                "explanations": explanations,
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
