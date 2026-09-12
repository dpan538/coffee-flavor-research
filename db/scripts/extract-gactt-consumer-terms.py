#!/usr/bin/env python3
"""Step 5 (owner R3-D12): consumer flavor vocabulary from GACTT (approved T2 consumer observations).

Reads the anonymised GACTT results under COFFEE_FLAVOR_RESTRICTED_ROOT/sources/gactt_maven, takes every
free-text tasting-notes column, tokenises the English notes, and writes PUBLIC aggregates only:
  db/data/product-vector-v1/GACTT_CONSUMER_TERM_FREQUENCY.tsv  term, respondents, mapping (dimension / concept), mapping_basis
No respondent text leaves the restricted root. Terms that map to a dimension but are not yet in the
lexicon are appended to CN_CONSUMER_FLAVOR_LEXICON.tsv as English consumer terms (owner_reviewed=false).
"""
from __future__ import annotations
import csv, json, os, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db" / "data" / "product-vector-v1"
DEFAULT_RESTRICTED_ROOT = Path.home() / "Desktop" / "Coffee_Flavor_Restricted"
DIMS = ["acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted", "spice", "herbal_green", "woody_earthy", "defect"]
# English consumer synonyms -> dimension (operator table; the concept tags cover the canonical words)
SYNONYMS = {
    "fermented_winey": ["winey", "wine", "boozy", "fermented", "funky", "funk", "rum", "whiskey", "whisky", "bourbon", "brandy", "liquor", "alcohol", "alcoholic", "yeasty", "kombucha", "cider", "vinegar", "sour beer", "port"],
    "acidity": ["acidic", "acidity", "acid", "tart", "tangy", "bright", "sour", "zesty", "citrusy", "citrus", "lemony", "juicy", "crisp", "sharp"],
    "sweetness": ["sweet", "sweetness", "sugary", "candy", "syrup", "honeyed", "jammy", "jam"],
    "body": ["body", "full-bodied", "full bodied", "heavy", "thick", "creamy", "smooth", "silky", "velvety", "rich", "thin", "watery", "light-bodied", "mouthfeel"],
    "floral": ["floral", "flowery", "flowers", "perfume", "perfumy", "tea-like", "tea like"],
    "fruity": ["fruity", "fruit", "berry", "berries", "stone fruit", "tropical", "melon", "apricot", "citrus fruit"],
    "nutty_chocolate": ["nutty", "chocolate", "chocolatey", "chocolaty", "cocoa", "nut", "nuts", "caramel", "toffee", "brownie", "fudge"],
    "bitter_roasted": ["bitter", "bitterness", "roasty", "roasted", "burnt", "burned", "smoky", "smokey", "charred", "ashy", "carbon", "dark roast", "over-roasted"],
    "spice": ["spicy", "spice", "spices", "peppery", "clove", "cinnamon"],
    "herbal_green": ["grassy", "grass", "green", "vegetal", "herbal", "herbaceous", "hay", "tea"],
    "woody_earthy": ["earthy", "woody", "wood", "tobacco", "leather", "musky", "mushroom", "dirt", "soil"],
    "defect": ["musty", "moldy", "mouldy", "stale", "cardboard", "papery", "rubbery", "metallic", "medicinal", "chemical", "off", "rancid", "plastic"],
}


# consumer words that describe structure or are too generic to print on a flavor card
NOT_DISPLAY = {"body", "mouthfeel", "thin", "watery", "heavy", "thick", "rich", "full bodied", "full-bodied", "off", "acidity", "acid", "acidic", "bitterness",
               "sweetness", "sharp", "bright", "fruit", "fruity", "nut", "nuts", "nutty", "chocolatey", "chocolaty", "green", "spices", "spice", "wood", "dirt", "tea like"}


def main() -> int:
    root = Path(os.environ.get("COFFEE_FLAVOR_RESTRICTED_ROOT", str(DEFAULT_RESTRICTED_ROOT)))
    src = next(iter((root / "sources" / "gactt_maven").glob("GACTT_RESULTS_ANONYMIZED*.csv")))
    with src.open(encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        note_cols = [c for c in (reader.fieldnames or []) if "notes" in c.lower()]
        rows = list(reader)
    notes = [(i, c, r[c].strip()) for i, r in enumerate(rows) for c in note_cols if r.get(c) and len(r[c].strip()) > 2]
    # vocabulary: en concept tags + dimension tag lists + synonyms
    tags = list(csv.DictReader((OUT / "CONCEPT_FLAVOR_TAGS.tsv").open(encoding="utf-8", newline=""), delimiter="\t"))
    vocab: dict[str, tuple[str, str, str]] = {}  # term -> (dimension, concept, basis)
    proj = {r["canonical_concept_id"]: r for r in csv.DictReader((OUT / "CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv").open(encoding="utf-8", newline=""), delimiter="\t")}
    for r in tags:
        if r["kind"] == "concept":
            pr = proj[r["key"]]
            dim = max(DIMS, key=lambda d: float(pr[d]))
            vocab[r["tags_en"].lower()] = (dim, r["key"], "CONCEPT_TAG_EN")
        else:
            for t in r["tags_en"].split("|"):
                vocab[t.lower()] = (r["key"].removeprefix("dim:"), "", "DIMENSION_TAG_EN")
    for dim, terms in SYNONYMS.items():
        for t in terms:
            vocab.setdefault(t.lower(), (dim, "", "CONSUMER_SYNONYM_EN"))
    # tokenise: count respondents mentioning each vocabulary term (longest terms first, no double counting inside a longer match)
    ordered = sorted(vocab, key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(re.escape(t) for t in ordered) + r")\b", re.I)
    respondents: dict[str, set[int]] = defaultdict(set)
    unknown: Counter[str] = Counter()
    for i, _c, text in notes:
        low = text.lower()
        found = set(m.group(1).lower() for m in pattern.finditer(low))
        for term in found:
            respondents[term].add(i)
        for tok in re.findall(r"[a-z][a-z\-']{2,}", low):
            if tok not in vocab and not any(tok in t for t in found):
                unknown[tok] += 1
    dim_total: Counter[str] = Counter()
    for term, ids in respondents.items():
        dim_total[vocab[term][0]] += len(ids)
    with (OUT / "GACTT_CONSUMER_TERM_FREQUENCY.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["term_en", "respondents", "dimension", "canonical_concept_id", "mapping_basis", "source"])
        for term, ids in sorted(respondents.items(), key=lambda kv: -len(kv[1])):
            dim, concept, basis = vocab[term]
            w.writerow([term, len(ids), dim, concept, basis, "GACTT_RESULTS_ANONYMIZED_v2 tasting notes (aggregate counts only; owner-approved T2)"])
    # append unmapped-to-lexicon English consumer terms (synonym table hits with >= 15 respondents) to the lexicon
    lex_path = OUT / "CN_CONSUMER_FLAVOR_LEXICON.tsv"
    lex = [r for r in csv.DictReader(lex_path.open(encoding="utf-8", newline=""), delimiter="\t") if not r["source"].startswith("GACTT_CONSUMER_TERMS")]
    for r in lex:
        r.setdefault("display_eligible", "true")
    have_en = {r["surface_term_en"].lower() for r in lex}
    added = []
    for term, ids in sorted(respondents.items(), key=lambda kv: -len(kv[1])):
        dim, concept, basis = vocab[term]
        if basis == "CONSUMER_SYNONYM_EN" and len(ids) >= 15 and term not in have_en:
            lex.append({"surface_term_zh": "", "surface_term_en": term, "primary_dimension": dim, "canonical_concept_id": concept, "secondary_effects": "",
                        "source": f"GACTT_CONSUMER_TERMS_2026-09-12 ({len(ids)} respondents); zh counterpart pending", "owner_reviewed": "false",
                        "display_eligible": "false" if term in NOT_DISPLAY else "true"})
            added.append((term, len(ids), dim, term not in NOT_DISPLAY))
    fields = ["surface_term_zh", "surface_term_en", "primary_dimension", "canonical_concept_id", "secondary_effects", "source", "owner_reviewed", "display_eligible"]
    with lex_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(lex)
    (OUT / "GACTT_SUMMARY.json").write_text(json.dumps({"respondents": len(rows), "notes": len(notes), "mapped_terms": len(respondents), "basis": "aggregate counts only; owner-approved T2"}, indent=2) + "\n", encoding="utf-8")
    summary = {"respondents": len(rows), "note_columns": note_cols, "notes": len(notes), "mapped_terms": len(respondents),
               "respondents_by_dimension": dict(dim_total.most_common()), "fermented_winey_terms": [(t, len(respondents[t])) for t in sorted(respondents, key=lambda t: -len(respondents[t])) if vocab[t][0] == "fermented_winey"][:12],
               "top_unknown_tokens": unknown.most_common(25), "lexicon_added_en": added}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
