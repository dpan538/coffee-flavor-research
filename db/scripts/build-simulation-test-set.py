#!/usr/bin/env python3
"""A fixed test set for comparing question flows (owner, 2026-09-20): 500 real review records as simulated cups.

Each record gives a cup's context (preparation, roast, process, variety, origin where the app has the option), its
12-dimension vector, the flavor concepts the reviewer mentioned, and its aroma / aftertaste levels. A simulated drinker
who "tastes" exactly what the record says answers both question flows; see scripts/simulate-question-flows.mjs.
Stratified by roast band and preparation, seeded, records with at least three mapped concepts. Public files only.
Writes db/data/product-vector-v1/SIMULATION_TEST_SET.json.
"""
from __future__ import annotations
import csv, json, random, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PV = ROOT / "db" / "data" / "product-vector-v1"
LEDGER = ROOT / "db" / "data" / "current" / "CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv"
DIMS = ["acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted", "spice", "herbal_green", "woody_earthy", "defect"]
ROAST = {"Light": "light", "Medium-Light": "medium_light", "Medium": "medium", "Medium-Dark": "medium_dark", "Dark": "dark", "Very Dark": "very_dark"}
BAND = {"light": "light", "medium_light": "light", "medium": "medium", "medium_dark": "dark", "dark": "dark", "very_dark": "dark"}
# 500 cups (owner, 2026-09-20: 200 was the first run; more records for the re-validation), in the corpus' own proportions by and large
QUOTA = {("light", "CUPPING"): 225, ("medium", "CUPPING"): 100, ("dark", "CUPPING"): 75, ("any", "ESPRESSO"): 100}
SEED = 20260920
csv.field_size_limit(10**9)


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def cross_source() -> int:
    """--cross-source: 500 Cup of Excellence lots as cups — another organisation, another vocabulary, juror lists of
    fifteen descriptors instead of a reviewer's three or four. The question bank's tables are fitted on the other
    source, so this set shows how much of a result is that source's house style. Light-roast cupping, no other context."""
    lib = {r["effective_record_id"]: r for r in rows(PV / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE" and r["source_family_id"] == "family.ace_cup_of_excellence"}
    concepts: dict[str, set[str]] = defaultdict(set)
    with LEDGER.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["effective_record_id"] in lib:
                concepts[r["effective_record_id"]].update(c[8:] for c in r["canonical_concept_ids"].split("|") if c.startswith("sensory."))
    pool = [e for e in sorted(lib) if len(concepts[e]) >= 5]
    chosen = random.Random(SEED).sample(pool, 500)
    out = [{"id": e, "context": {"c0_preparation": "pour_over_v60", "c1_roast": "light"}, "vector": [float(lib[e]["v_" + d]) for d in DIMS], "concepts": sorted(concepts[e]), "aroma_level": "", "aftertaste_level": ""} for e in chosen]
    (PV / "SIMULATION_TEST_SET_COE.json").write_text(json.dumps({"seed": SEED, "source": "family.ace_cup_of_excellence", "dimensions": DIMS, "records": out}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(out), "pool": len(pool), "mean_concepts": round(sum(len(r["concepts"]) for r in out) / len(out), 1)}))
    return 0


def main() -> int:
    if "--cross-source" in sys.argv:
        return cross_source()
    bundle = json.loads((PV / "product-vector-v1.json").read_text(encoding="utf-8"))
    processes, varieties = set(bundle["matrix_k"]["C2_process"]), set(bundle["matrix_k"]["C2_variety"])
    origins = {v["label"]["en"].split(",")[0].lower(): k for k, v in bundle["context_rules"]["origin_regions"].items()}
    lib = {r["effective_record_id"]: r for r in rows(PV / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE" and r["source_family_id"] == "family.coffeereview_kaggle_parsed"}
    axes = {r["effective_record_id"]: r for r in rows(PV / "COFFEEREVIEW_STRUCTURE_AXES.tsv")}
    c2 = {r["effective_record_id"]: r for r in rows(PV / "COFFEEREVIEW_C2_LABELS.tsv")}
    structure = {r["effective_record_id"]: r for r in rows(PV / "COFFEEREVIEW_AROMA_AFTERTASTE_AXES.tsv")}
    concepts: dict[str, set[str]] = defaultdict(set)
    with LEDGER.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["effective_record_id"] in lib:
                concepts[r["effective_record_id"]].update(c[8:] for c in r["canonical_concept_ids"].split("|") if c.startswith("sensory."))
    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for e in sorted(lib):
        roast = ROAST.get(axes.get(e, {}).get("roast_level", ""))
        if not roast or len(concepts[e]) < 3:
            continue
        prep = lib[e]["preparation_service_id"]
        strata[("any", "ESPRESSO") if prep == "ESPRESSO" else (BAND[roast], "CUPPING")].append(e)
    rng = random.Random(SEED)
    chosen: list[str] = []
    for key, n in QUOTA.items():
        chosen += rng.sample(strata[key], n)
    out = []
    for e in chosen:
        roast = ROAST[axes[e]["roast_level"]]
        label = c2.get(e, {})
        context = {"c0_preparation": "espresso" if lib[e]["preparation_service_id"] == "ESPRESSO" else "pour_over_v60", "c1_roast": roast}
        if label.get("process") in processes: context["c2_process"] = label["process"]
        if label.get("variety") in varieties: context["c2_variety"] = label["variety"]
        origin = origins.get((axes[e].get("origin_country") or "").lower())
        if origin: context["c2_origin"] = origin
        out.append({"id": e, "context": context, "vector": [float(lib[e]["v_" + d]) for d in DIMS], "concepts": sorted(concepts[e]),
                    "aroma_level": structure.get(e, {}).get("aroma_level", ""), "aftertaste_level": structure.get(e, {}).get("aftertaste_level", "")})
    (PV / "SIMULATION_TEST_SET.json").write_text(json.dumps({"seed": SEED, "quota": {"|".join(k): v for k, v in QUOTA.items()}, "dimensions": DIMS, "records": out}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(out), "with_process": sum("c2_process" in r["context"] for r in out), "with_variety": sum("c2_variety" in r["context"] for r in out), "with_origin": sum("c2_origin" in r["context"] for r in out),
                      "mean_concepts": round(sum(len(r["concepts"]) for r in out) / len(out), 1)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
