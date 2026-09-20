#!/usr/bin/env python3
"""CoffeeReview structured scores (owner D-open-3, 2026-09-12): Body and Acidity
(1-10 editorial scales) become the body / acidity axes of the coffee vectors,
because descriptor lists under-report structure.

Reads the owner-reviewed CSV under COFFEE_FLAVOR_RESTRICTED_ROOT, writes
  restricted: <family_dir>/COFFEEREVIEW_STRUCTURE_SCORES_RESTRICTED.tsv   (url + raw scores)
  public    : db/data/product-vector-v1/COFFEEREVIEW_STRUCTURE_AXES.tsv     (effective_record_id + rank-percentile axes)
Rank percentile (0-1) within CoffeeReview, not (score-1)/9: the scales are compressed
(Body is 8 or 9 for 84% of reviews), so only the rank carries information.
'Acidity' (pre-2010s) and 'Acidity/Structure' (later) are the same column renamed; merged.
"""
from __future__ import annotations
import csv, importlib.util, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db" / "data" / "product-vector-v1"
PARSER = ROOT / "db" / "scripts" / "acquire-coffeereview-round3.py"


def load_parser():
    spec = importlib.util.spec_from_file_location("crparser", PARSER)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


COUNTRIES = ["Ethiopia", "Kenya", "Colombia", "Panama", "Guatemala", "Costa Rica", "Brazil", "Honduras", "El Salvador", "Nicaragua",
             "Peru", "Bolivia", "Ecuador", "Mexico", "Rwanda", "Burundi", "Tanzania", "Uganda", "Yemen", "Indonesia", "Sumatra", "Java",
             "Sulawesi", "Papua New Guinea", "India", "Vietnam", "Thailand", "Taiwan", "China", "Yunnan", "Hawaii", "Kona", "Jamaica",
             "Dominican", "Puerto Rico", "Cuba", "Haiti", "Venezuela", "Malawi", "Zambia", "Zimbabwe", "Congo", "Cameroon", "Laos",
             "Myanmar", "Nepal", "Philippines", "Timor", "Australia", "Ecuador"]
ALIAS = {"Sumatra": "Indonesia", "Java": "Indonesia", "Sulawesi": "Indonesia", "Kona": "Hawaii", "Yunnan": "China", "Dominican": "Dominican Republic"}


def origin_country(text: str) -> str:
    low = text.lower()
    for name in COUNTRIES:
        if name.lower() in low:
            return ALIAS.get(name, name)
    return "UNRESOLVED"


def percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values.items(), key=lambda kv: kv[1])
    ranks: dict[str, float] = {}
    i = 0
    n = len(ordered)
    while i < n:
        j = i
        while j + 1 < n and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        mid = (i + j) / 2  # average rank for ties
        for k in range(i, j + 1):
            ranks[ordered[k][0]] = round(mid / (n - 1), 4) if n > 1 else 0.5
        i = j + 1
    return ranks


def main() -> int:
    cr = load_parser()
    root = cr.require_restricted_root(Path(os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT", str(cr.DEFAULT_RESTRICTED_ROOT))))
    src = root / cr.SOURCE_REL
    b2 = cr.load_b2()
    restricted_rows, body, acid, aroma, after = [], {}, {}, {}, {}
    roast_of: dict[str, str] = {}
    origin_of: dict[str, str] = {}
    with src.open(encoding="utf-8", errors="replace", newline="") as fh:
        for r in csv.DictReader(fh):
            url = (r.get("URL") or "").strip()
            if not url:
                continue
            eff = b2.stable_id("effective-b2", cr.SOURCE["route"], url, "BLIND_ASSESSMENT")
            a = (r.get("Acidity/Structure") or "").strip() or (r.get("Acidity") or "").strip()
            b = (r.get("Body") or "").strip()
            restricted_rows.append({"url": url, "effective_record_id": eff, "body_score": b, "acidity_score": a, "aroma_score": (r.get("Aroma") or "").strip(),
                                    "flavor_score": (r.get("Flavor") or "").strip(), "aftertaste_score": (r.get("Aftertaste") or "").strip(), "rating": (r.get("Rating") or "").strip()})
            if b: body[eff] = float(b)
            if a: acid[eff] = float(a)
            for store, column in ((aroma, "Aroma"), (after, "Aftertaste")):
                value = (r.get(column) or "").strip()
                if value: store[eff] = float(value)
            roast_of[eff] = (r.get("Roast Level") or "").strip() or "UNREPORTED"
            origin_of[eff] = origin_country((r.get("Coffee Origin") or "") + " " + (r.get("Coffee Name") or ""))
    fam = root / cr.FAMILY_DIR
    fam.mkdir(parents=True, exist_ok=True)
    with (fam / "COFFEEREVIEW_STRUCTURE_SCORES_RESTRICTED.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(restricted_rows[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(restricted_rows)
    pb, pa = percentile_ranks(body), percentile_ranks(acid)
    OUT.mkdir(parents=True, exist_ok=True)
    ids = sorted(set(pb) | set(pa))
    with (OUT / "COFFEEREVIEW_STRUCTURE_AXES.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["effective_record_id", "body_axis_percentile", "acidity_axis_percentile", "roast_level", "origin_country", "basis"])
        for eff in sorted(set(ids) | set(roast_of)):
            w.writerow([eff, "" if eff not in pb else f"{pb[eff]:.4f}", "" if eff not in pa else f"{pa[eff]:.4f}", roast_of.get(eff, "UNREPORTED"), origin_of.get(eff, "UNRESOLVED"),
                        "COFFEEREVIEW_EDITORIAL_1_10_RANK_PERCENTILE;OWNER_D-OPEN-3"])
    # Aroma and Aftertaste (owner, 2026-09-19): rank percentiles WITHIN a roast band, never across bands — the scores are
    # compressed quality scores (aroma is 8 or 9 for 94% of reviews) and follow the reviewers' preference for lighter
    # roasts, so a cross-roast comparison would pass a quality judgement. They stay outside the 12-dimension vector;
    # a separate file keeps COFFEEREVIEW_STRUCTURE_AXES.tsv byte-identical. Levels: aroma high = 9+, aftertaste
    # low = 7 or less, mid = 8, high = 9+.
    band_of = {"Light": "light", "Medium-Light": "light", "Medium": "medium", "Medium-Dark": "dark", "Dark": "dark", "Very Dark": "dark"}
    within: dict[str, dict[str, float]] = {"aroma": {}, "aftertaste": {}}
    for name, scores in (("aroma", aroma), ("aftertaste", after)):
        for band in ("light", "medium", "dark"):
            within[name].update(percentile_ranks({e: v for e, v in scores.items() if band_of.get(roast_of.get(e, "")) == band}))
    with (OUT / "COFFEEREVIEW_AROMA_AFTERTASTE_AXES.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["effective_record_id", "roast_band", "aroma_percentile_within_roast", "aroma_level", "aftertaste_percentile_within_roast", "aftertaste_level", "basis"])
        for eff in sorted(set(within["aroma"]) | set(within["aftertaste"])):
            w.writerow([eff, band_of[roast_of[eff]], "" if eff not in within["aroma"] else f"{within['aroma'][eff]:.4f}", "" if eff not in aroma else ("high" if aroma[eff] >= 9 else "low"),
                        "" if eff not in within["aftertaste"] else f"{within['aftertaste'][eff]:.4f}", "" if eff not in after else ("high" if after[eff] >= 9 else "mid" if after[eff] >= 8 else "low"),
                        "COFFEEREVIEW_EDITORIAL_1_10_RANK_PERCENTILE_WITHIN_ROAST_BAND;OWNER_2026-09-19_R3-D40"])
    summary = {"reviews": len(restricted_rows), "with_aroma_in_a_roast_band": len(within["aroma"]), "with_aftertaste_in_a_roast_band": len(within["aftertaste"]), "with_body": len(body), "with_acidity": len(acid), "with_both": len(set(body) & set(acid)),
               "body_score_distribution": {str(int(v)): sum(1 for x in body.values() if x == v) for v in sorted(set(body.values()))},
               "acidity_score_distribution": {str(int(v)): sum(1 for x in acid.values() if x == v) for v in sorted(set(acid.values()))}}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
