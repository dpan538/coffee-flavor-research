#!/usr/bin/env python3
"""The neighbour index of product-vector-v1 (owner, 2026-09-20, R3-D47): the usable record library in the smallest form
that lets the app ask "what are coffees like this one called?" for the word slots the reader gave no signal for.

usage: python3 db/scripts/build-neighbour-index.py [--holdout <test set json>]... [--out <path>]

Public files only. Per record the index keeps a 12-dimension vector quantised to one byte per dimension and the indices
of the flavor concepts it mentions, restricted to the concepts a candidate word can be scored by. It keeps NO record id,
name, source, year, text or score: a record is evidence for a word, never a coffee the app could name or recommend
(product_candidate_rights stays as it is in COFFEE_VECTOR_LIBRARY.tsv).

Which concept stands for which word comes from the owner-reviewed tables alone:
  exact   the concept of the word's second-level row in DYNAMIC_QUESTION_BANK.tsv (柠檬 → lemon)
  family  for a word without one, the concepts of its sub-family (tag_families in CONCEPT_FLAVOR_TAGS.tsv): the exact
          concepts of its sibling words plus those of the first-level option that points to the sub-family (白桃 → the
          stone fruit: cherry, plum, peach)
A word with neither is never scored; its place comes from the cup's rotation, as before.

--holdout leaves the records of a simulation test set out (scripts/simulate-question-flows.mjs), so a simulated cup
cannot find itself among its neighbours.
"""
import base64, csv, json, sys
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(10**9)
ROOT = Path(__file__).resolve().parents[2]
PV = ROOT / "db/data/product-vector-v1"
LEDGER = ROOT / "db/data/current/CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv"
DIMS = ["acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted", "spice", "herbal_green", "woody_earthy", "defect"]
NEIGHBOURS, POWER, FAMILY_WEIGHT = 60, 4, 0.3
# A concept counts for a cup only when it is DISTINCTIVE of the cup's neighbourhood (owner, 2026-09-20: steady what is
# evident but fluctuates, never reinforce what is strong everywhere): at least SUPPORT of the neighbourhood mentions it,
# and that rate is at least LIFT times its rate over all records (concept_share). Ranking by the plain share instead
# scores a few points more on the simulation and puts orange on 75% of enumerated cards, cocoa on 72%.
SUPPORT, LIFT = 0.10, 2.0


def rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def main():
    args = sys.argv[1:]
    holdout = set()
    for i, a in enumerate(args):
        if a == "--holdout":
            holdout |= {r["id"] for r in json.load(open(args[i + 1], encoding="utf-8"))["records"]}
    out_path = Path(args[args.index("--out") + 1]) if "--out" in args else PV / "product-vector-v1-neighbours.json"

    # ── which concepts score which word
    tags = [r for r in rows(PV / "CONCEPT_FLAVOR_TAGS.tsv") if r["kind"] == "dimension" and r["role"] == "candidate"]
    bank = rows(PV / "DYNAMIC_QUESTION_BANK.tsv")
    exact = {}  # (dimension, zh word) → concept
    for r in bank:
        if r["kind"] == "second" and r["role"] == "word" and r["concepts"]:
            dimension, word = r["focus"].split(":")
            exact[(dimension, word)] = r["concepts"].split("|")[0]
    family_concepts = defaultdict(set)  # (dimension, sub-family) → concepts
    for r in bank:
        if r["kind"] != "second" and r["focus"] and not r["focus"].endswith(":*") and r["concepts"]:
            family_concepts[tuple(r["focus"].split(":"))] |= set(r["concepts"].split("|"))
    words = {}  # dimension → [(zh word, sub-family)]
    for r in tags:
        dimension = r["key"][4:]
        zh, fams = r["tags_zh_cn"].split("|"), (r["tag_families"] or "").split("|")
        words[dimension] = [(w, fams[i] if i < len(fams) else "") for i, w in enumerate(zh)]
        for w, fam in words[dimension]:
            if fam and (dimension, w) in exact:
                family_concepts[(dimension, fam)].add(exact[(dimension, w)])
    concepts = sorted({c for c in exact.values()} | {c for s in family_concepts.values() for c in s})
    at = {c: i for i, c in enumerate(concepts)}
    assert len(concepts) < 255
    word_concepts = {}
    for dimension, items in words.items():
        entry = []
        for w, fam in items:
            if (dimension, w) in exact:
                entry.append({"exact": at[exact[(dimension, w)]]})
            elif family_concepts.get((dimension, fam)):
                entry.append({"family": sorted(at[c] for c in family_concepts[(dimension, fam)])})
            else:
                entry.append(None)
        word_concepts[dimension] = entry

    # ── the records: usable vectors, the concepts they mention
    library = {r["effective_record_id"]: r for r in rows(PV / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE" and r["effective_record_id"] not in holdout}
    mentioned = defaultdict(set)
    with open(LEDGER, encoding="utf-8") as handle:
        for r in csv.DictReader(handle, delimiter="\t"):
            if r["effective_record_id"] in library:
                mentioned[r["effective_record_id"]].update(at[c[8:]] for c in r["canonical_concept_ids"].split("|") if c.startswith("sensory.") and c[8:] in at)
    vectors, mentions, kept, seen = bytearray(), bytearray(), 0, [0] * len(concepts)
    for record_id in sorted(library):
        r = library[record_id]
        vectors += bytes(min(255, round(float(r["v_" + d]) * 255)) for d in DIMS)
        cs = sorted(mentioned[record_id])
        mentions += bytes([len(cs)] + cs)
        kept += 1
        for c in cs:
            seen[c] += 1

    out = {
        "contract_version": "product-vector-v1.neighbour-index.v1",
        "basis": "COFFEE_VECTOR_LIBRARY.tsv (vector_state USABLE) + CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv (canonical sensory concepts); word ↔ concept from DYNAMIC_QUESTION_BANK.tsv and CONCEPT_FLAVOR_TAGS.tsv; no record id, name, source, text or score",
        "holdout_records": len(holdout),
        "dimensions": DIMS,
        "neighbours": NEIGHBOURS,
        "power": POWER,
        "family_weight": FAMILY_WEIGHT,
        "support": SUPPORT,
        "lift": LIFT,
        "concepts": concepts,
        "concept_share": [round(n / kept, 5) for n in seen],
        "word_concepts": word_concepts,
        "records": kept,
        "vectors": base64.b64encode(bytes(vectors)).decode("ascii"),
        "mentions": base64.b64encode(bytes(mentions)).decode("ascii"),
    }
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    scored = sum(1 for e in word_concepts.values() for x in e if x)
    print(f"records {kept} | concepts {len(concepts)} | words scored {scored} of {sum(len(e) for e in word_concepts.values())} | {out_path.stat().st_size / 1024:.0f} KB → {out_path}")


if __name__ == "__main__":
    main()
