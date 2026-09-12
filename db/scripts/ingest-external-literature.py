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
OPTIONAL = ["context_parts", "review_state", "review_note", "use_note", "claim_zh_cn_alt", "claim_en_alt"]  # *_alt: a second phrasing of the same claim, same source, so the card can vary  # use_note: how this project uses the source (kept apart from the source's own terms)  # context_parts: "C0:pour_over_v60|C1:light"; review_state NEEDS_REVERIFICATION (owner copy review 2026-09-12) keeps a claim out of the UI until a supporting source is listed
AXES = {"C0", "C1", "C2_variety", "C2_process", "GENERAL"}
AXIS_ALIAS = {"C0_brew": "C0", "C0_BREW": "C0", "C1_roast": "C1", "C1_ROAST": "C1", "C2": "C2_variety", "C2_VARIETY": "C2_variety", "C2_PROCESS": "C2_process", "general": "GENERAL"}
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
                r["context_axis"] = AXIS_ALIAS.get(r["context_axis"].strip(), r["context_axis"].strip())
                combo = (r.get("context_parts") or "").strip()
                if combo:
                    parts_in = [part.strip() for part in combo.split("|") if part.strip()]
                    bad = [part for part in parts_in if ":" not in part or AXIS_ALIAS.get(part.split(":")[0], part.split(":")[0]) not in AXES - {"GENERAL"}]
                    if bad:
                        problems.append(f"{path.name}:{n}: context_parts {combo!r}")
                        continue
                elif r["context_axis"] not in AXES:
                    problems.append(f"{path.name}:{n}: context_axis {r['context_axis']!r}")
                    continue
                effects = r["dimension_effects"].strip()
                if effects and not all(re.fullmatch(r"(%s):[+-]?\d*\.?\d+" % "|".join(DIMS), part.strip()) for part in effects.split("|")):
                    problems.append(f"{path.name}:{n}: dimension_effects {effects!r}")
                    continue
                if combo:
                    parts = [(AXIS_ALIAS.get(part.split(":")[0], part.split(":")[0]), part.split(":", 1)[1]) for part in parts_in]
                else:
                    parts = [(r["context_axis"], r["option"].strip())] if r["option"].strip() else []
                rows.append({"context_id": "__".join(f"{a}_{o.upper()}" for a, o in parts) or f"GENERAL_{r['source_id']}_{n}",
                             "context_parts": "|".join(f"{a}:{o}" for a, o in parts),
                             "statement_zh": r["claim_zh_cn"].strip(), "statement_en": r["claim_en"].strip(),
                             "statement_zh_alt": (r.get("claim_zh_cn_alt") or "").strip(), "statement_en_alt": (r.get("claim_en_alt") or "").strip(),
                             # a literature claim is only fully declared once it carries a DOI / link and a licence note (owner rule, R3-D14)
                             "evidence_state": ("LITERATURE_CLAIM_NEEDS_REVERIFICATION" if (r.get("review_state") or "").strip() == "NEEDS_REVERIFICATION"
                                                else "LITERATURE_CLAIM" if (r["source_locator"].strip() and r["licence_note"].strip()) else "LITERATURE_CLAIM_PENDING_LOCATOR"),
                             "citation_ref": f"{r['source_title']} — {r['source_locator'].strip() or 'DOI / link pending'}", "source_id": r["source_id"], "licence_note": r["licence_note"].strip() or "licence note pending",
                             "dimension_effects": effects, "owner_reviewed": "true"})
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["context_id", "context_parts", "statement_zh", "statement_en", "statement_zh_alt", "statement_en_alt", "evidence_state", "citation_ref", "source_id", "licence_note", "dimension_effects", "owner_reviewed"], delimiter="\t", lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    # source registry for the About page (title, locator, licence, claim count, declaration state)
    registry: dict[str, dict] = {}
    for r in rows:
        reg = registry.setdefault(r["source_id"], {"source_id": r["source_id"], "title": "", "locator": "", "licence_note": "", "terms_short": "", "use": "", "claims": 0, "claims_live": 0, "claims_pending_review": 0, "state": "LITERATURE_CLAIM"})
        reg["claims"] += 1
        if r["evidence_state"] == "LITERATURE_CLAIM_NEEDS_REVERIFICATION":
            reg["claims_pending_review"] += 1  # declared, but not shown to users until re-verified (owner copy review 2026-09-12)
        else:
            reg["claims_live"] += 1
        if r["evidence_state"] == "LITERATURE_CLAIM_PENDING_LOCATOR":
            reg["state"] = "LITERATURE_CLAIM_PENDING_LOCATOR"
    for path in sorted(IN.glob("*.claims.csv")):
        with path.open(encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                reg = registry.get(r["source_id"])
                if reg:
                    reg["title"] = reg["title"] or r["source_title"].strip()
                    reg["locator"] = reg["locator"] or r["source_locator"].strip()
                    reg["licence_note"] = reg["licence_note"] or r["licence_note"].strip()
                    reg["terms_short"] = reg["terms_short"] or r["licence_note"].strip().split(";")[0].split(" — ")[0].strip()
                    reg["use"] = reg["use"] or (r.get("use_note") or "").strip()
    (OUT.parent / "LITERATURE_SOURCES.json").write_text(json.dumps({"sources": list(registry.values()), "rule": "raw PDFs / full text never enter git; locator and licence note are the owner's; a claim without both is LITERATURE_CLAIM_PENDING_LOCATOR; a claim with review_state NEEDS_REVERIFICATION is LITERATURE_CLAIM_NEEDS_REVERIFICATION and never reaches the UI"}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"claim_files": len(list(IN.glob('*.claims.csv'))), "claims": len(rows), "pending_locator": sum(r["evidence_state"] == "LITERATURE_CLAIM_PENDING_LOCATOR" for r in rows), "needs_reverification": sum(r["evidence_state"] == "LITERATURE_CLAIM_NEEDS_REVERIFICATION" for r in rows), "sources": [(k, v["claims"], v["state"]) for k, v in registry.items()], "problems": problems}, ensure_ascii=False))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
