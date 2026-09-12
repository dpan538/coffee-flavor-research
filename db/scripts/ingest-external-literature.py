#!/usr/bin/env python3
"""Ingest owner-approved literature claims (db/data/external-literature/*.claims.csv) into
db/data/product-vector-v1/LITERATURE_CLAIMS.tsv with evidence_state=LITERATURE_CLAIM.
Empty input is fine: the output then has only a header. See external-literature/README.md."""
from __future__ import annotations
import csv, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IN = ROOT / "db" / "data" / "external-literature"
OUT = ROOT / "db" / "data" / "product-vector-v1" / "LITERATURE_CLAIMS.tsv"
REQUIRED = ["source_id", "source_title", "source_locator", "licence_note", "context_axis", "option", "dimension_effects", "claim_zh_cn", "claim_en"]
AXES = {"C0", "C1", "C2_variety", "C2_process", "GENERAL"}
DIMS = {"acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted", "spice", "herbal_green", "woody_earthy", "defect"}


def main() -> int:
    rows, problems = [], []
    for path in sorted(IN.glob("*.claims.csv")):
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
            if missing:
                problems.append(f"{path.name}: missing columns {missing}")
                continue
            for n, r in enumerate(reader, 2):
                if r["context_axis"] not in AXES:
                    problems.append(f"{path.name}:{n}: context_axis {r['context_axis']!r}")
                    continue
                effects = r["dimension_effects"].strip()
                if effects and not all(re.fullmatch(r"(%s):[+-]?\d*\.?\d+" % "|".join(DIMS), part.strip()) for part in effects.split("|")):
                    problems.append(f"{path.name}:{n}: dimension_effects {effects!r}")
                    continue
                parts = [(r["context_axis"], r["option"].strip())] if r["option"].strip() else []
                rows.append({"context_id": "__".join(f"{a}_{o.upper()}" for a, o in parts) or f"GENERAL_{r['source_id']}_{n}",
                             "context_parts": "|".join(f"{a}:{o}" for a, o in parts),
                             "statement_zh": r["claim_zh_cn"].strip(), "statement_en": r["claim_en"].strip(), "evidence_state": "LITERATURE_CLAIM",
                             "citation_ref": f"{r['source_title']} — {r['source_locator']}", "source_id": r["source_id"], "licence_note": r["licence_note"],
                             "dimension_effects": effects, "owner_reviewed": "true"})
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["context_id", "context_parts", "statement_zh", "statement_en", "evidence_state", "citation_ref", "source_id", "licence_note", "dimension_effects", "owner_reviewed"], delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(json.dumps({"claim_files": len(list(IN.glob('*.claims.csv'))), "claims": len(rows), "problems": problems}, ensure_ascii=False))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
