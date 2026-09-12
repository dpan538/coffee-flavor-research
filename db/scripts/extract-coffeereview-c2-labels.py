#!/usr/bin/env python3
"""Step 3 (owner R3-D6 confirmation): variety and processing labels for CoffeeReview
reviews, extracted from the review text with a keyword lexicon, so K[C2] can be
measured from the corpus instead of asserted.

Reads the owner-reviewed CSV under COFFEE_FLAVOR_RESTRICTED_ROOT (fields: Coffee Name,
Coffee Origin, Blind Assessment, Notes). Writes only categorical labels keyed by
effective_record_id to db/data/product-vector-v1/COFFEEREVIEW_C2_LABELS.tsv; no text.
Multi-variety blends get the first match plus a MULTI flag.
"""
from __future__ import annotations
import csv, importlib.util, json, os, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db" / "data" / "product-vector-v1"
PARSER = ROOT / "db" / "scripts" / "acquire-coffeereview-round3.py"

VARIETY = [  # (label, regex) — order matters for specificity
    ("gesha", r"\b(?:gesha|geisha)\b"),
    ("pink_bourbon", r"\bpink\s+bourbon\b"),
    ("yellow_bourbon", r"\b(?:yellow|amarelo)\s+bourbon\b"),
    ("red_bourbon", r"\bred\s+bourbon\b"),
    ("bourbon", r"\bbourbon\b"),
    ("typica", r"\btypica\b"),
    ("caturra", r"\bcaturra\b"),
    ("catuai", r"\bcatua[ií]\b"),
    ("sl28_sl34", r"\bsl[\s-]?(?:28|34)\b"),
    ("pacamara", r"\bpacamara\b"),
    ("maragogype", r"\bmaragogyp[ei]\b"),
    ("pacas", r"\bpacas\b"),
    ("mundo_novo", r"\bmundo\s+novo\b"),
    ("castillo", r"\bcastillo\b"),
    ("colombia_variety", r"\bcolombia\s+variety\b"),
    ("catimor", r"\bcatimor\b"),
    ("sarchimor", r"\bsarchimor\b"),
    ("villa_sarchi", r"\bvilla\s+sarch[ií]\b"),
    ("sidra", r"\bsidra\b"),
    ("wush_wush", r"\bwush\s+wush\b"),
    ("java_variety", r"\bjava\s+(?:variety|varietal)\b"),
    ("ethiopian_landrace", r"\b(?:heirloom|landrace|indigenous)\b"),
    ("robusta", r"\b(?:robusta|canephora)\b"),
    ("liberica", r"\b(?:liberica|excelsa)\b"),
    ("kent", r"\bkent\b"),
    ("s795", r"\bs\.?\s?795\b"),
    ("laurina", r"\blaurina\b"),
    ("maracaturra", r"\bmaracaturra\b"),
    ("tekisic", r"\btekisic\b"),
    ("jackson", r"\bjackson\b"),
    ("blue_mountain", r"\bblue\s+mountain\b"),
]
PROCESS = [
    ("carbonic_maceration", r"\bcarbonic\s+maceration\b"),
    ("anaerobic", r"\banaerobic\b"),
    ("co_fermented", r"\bco-?ferment"),
    ("extended_fermentation", r"\b(?:extended|prolonged|double)\s+ferment"),
    ("honey", r"\b(?:honey[\s-]process|honey-?processed|pulped[\s-]natural|semi-?washed|miel)\b"),
    ("wet_hulled", r"\b(?:wet-?hull|giling\s+basah)\b"),
    ("natural", r"\b(?:natural|dry-?process|dry\s+process|sun-?dried\s+in\s+the\s+fruit|dried\s+in\s+the\s+(?:whole\s+)?fruit)\b"),
    ("washed", r"\b(?:washed|wet-?process|wet\s+process|fully\s+washed)\b"),
    ("decaf", r"\b(?:decaf|decaffeinated|swiss\s+water|sugar\s?cane\s+(?:ea\s+)?process)\b"),
]


def load_parser():
    spec = importlib.util.spec_from_file_location("crparser", PARSER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def first_match(table, text):
    hits = [label for label, rx in table if re.search(rx, text, re.I)]
    return (hits[0] if hits else "UNRESOLVED"), len(hits)


def main() -> int:
    cr = load_parser()
    root = cr.require_restricted_root(Path(os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT", str(cr.DEFAULT_RESTRICTED_ROOT))))
    b2 = cr.load_b2()
    out, vc, pc, both = [], Counter(), Counter(), 0
    with (root / cr.SOURCE_REL).open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            url = (r.get("URL") or "").strip()
            if not url:
                continue
            eff = b2.stable_id("effective-b2", cr.SOURCE["route"], url, "BLIND_ASSESSMENT")
            head = " ".join((r.get("Coffee Name") or "", r.get("Coffee Origin") or ""))
            body = " ".join((r.get("Blind Assessment") or "", r.get("Notes") or ""))
            v, vn = first_match(VARIETY, head + " " + body)
            v_field = "NAME_OR_ORIGIN" if re.search("|".join(rx for _, rx in VARIETY), head, re.I) else ("REVIEW_TEXT" if v != "UNRESOLVED" else "")
            p, pn = first_match(PROCESS, head + " " + body)
            if p == "natural" and re.search(r"\bnatural(?:ly)?\s+(?:sweet|acid|bright|balanced|fruit)", body, re.I) and not re.search(r"\b(?:natural[\s-]process|dry[\s-]process|processed|sun-?dried)\b", head + " " + body, re.I):
                p, pn = "UNRESOLVED", 0  # "naturally sweet" is not a process claim
            out.append({"effective_record_id": eff, "variety": v, "variety_multi": "true" if vn > 1 else "false", "variety_evidence_field": v_field,
                        "process": p, "process_multi": "true" if pn > 1 else "false", "basis": "KEYWORD_LEXICON_OVER_REVIEW_TEXT;R3-D6_STEP3"})
            vc[v] += 1; pc[p] += 1
            both += (v != "UNRESOLVED" and p != "UNRESOLVED")
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "COFFEEREVIEW_C2_LABELS.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(out)
    print(json.dumps({"reviews": len(out), "variety_resolved": len(out) - vc["UNRESOLVED"], "process_resolved": len(out) - pc["UNRESOLVED"], "both_resolved": both,
                      "variety_top": vc.most_common(14), "process": pc.most_common()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
