#!/usr/bin/env python3
"""Data for the "heavier computation" experiments of the question-flow simulation (owner, 2026-09-20).

usage: python3 db/scripts/build-flow-experiment-data.py <out json>      (a scratch path: the output is not a repository artifact)
Everything excludes the test cups of both sets: the usable record library with the concepts each record mentions (for a
nearest-record word choice), and option weights learned from the corpus (what records that mention an option's
concepts look like against all records) in the place of the hand-set ones. Public files only.
Then: FLAGS="knn-fill" EXPERIMENT_DATA=<out json> node scripts/simulate-question-flows.mjs <hold-out build json>
"""
import csv, json, sys
from collections import defaultdict
csv.field_size_limit(10**9)
PV = "db/data/product-vector-v1/"
DIMS = ["acidity","sweetness","body","floral","fruity","nutty_chocolate","fermented_winey","bitter_roasted","spice","herbal_green","woody_earthy","defect"]
test = {r["id"] for name in ("SIMULATION_TEST_SET.json", "SIMULATION_TEST_SET_COE.json") for r in json.load(open(PV + name))["records"]}
lib = {r["effective_record_id"]: r for r in csv.DictReader(open(PV + "COFFEE_VECTOR_LIBRARY.tsv"), delimiter="\t") if r["vector_state"] == "USABLE" and r["effective_record_id"] not in test}
concepts = defaultdict(set)
for r in csv.DictReader(open("db/data/current/CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv"), delimiter="\t"):
    if r["effective_record_id"] in lib:
        concepts[r["effective_record_id"]].update(c[8:] for c in r["canonical_concept_ids"].split("|") if c.startswith("sensory."))
index = sorted({c for s in concepts.values() for c in s}); pos = {c: i for i, c in enumerate(index)}
records = [{"v": [float(r["v_" + d]) for d in DIMS], "c": sorted(pos[c] for c in concepts[e]), "f": 0 if r["source_family_id"].endswith("coffeereview_kaggle_parsed") else 1} for e, r in lib.items()]
# learned option vectors: what records that mention an option's concepts look like, against all records; positive part,
# scaled to the hand-set option's length so the questions keep their relative weight
bank = list(csv.DictReader(open(PV + "DYNAMIC_QUESTION_BANK.tsv"), delimiter="\t"))
mean = lambda vs: [sum(col) / len(vs) for col in zip(*vs)]
overall = mean([r["v"] for r in records])
learned = {}
for o in bank:
    if o["role"] != "data" or not o["concepts"]: continue
    cs = {pos[c] for c in o["concepts"].split("|") if c in pos}
    hit = [r["v"] for r in records if cs & set(r["c"])]
    if len(hit) < 30: continue
    diff = [max(0.0, a - b) for a, b in zip(mean(hit), overall)]
    hand = {k: float(v) for k, v in (x.split(":") for x in o["deltas"].split(";") if x)}
    hand_norm = sum(v * v for v in hand.values()) ** 0.5; norm = sum(x * x for x in diff) ** 0.5 or 1
    learned[o["option_id"]] = {"n": len(hit), "deltas": {d: round(x / norm * hand_norm, 3) for d, x in zip(DIMS, diff) if x / norm * hand_norm >= 0.05}, "hand": hand}
json.dump({"concepts": index, "records": records, "learned": learned}, open(sys.argv[1], "w"))
print("records", len(records), "| concepts", len(index), "| learned options", len(learned))
for k in ["A1", "A2", "B5", "B8", "C3"]: print(" ", k, "hand", learned[k]["hand"], "→ learned", learned[k]["deltas"], f"(n={learned[k]['n']})")
