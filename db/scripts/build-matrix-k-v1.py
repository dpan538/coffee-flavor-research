#!/usr/bin/env python3
"""Step 2 + Step 3 (owner R3-D6 confirmation): Matrix_K measured from the corpus.

K[option] = re-normalised mean of the unit vectors of the CoffeeReview coffees carrying
that option (COFFEE_VECTOR_LIBRARY, USABLE rows only), for
  C0 preparation  (cupping / espresso; product options V60 and French press use the cupping
                   row as a filter/immersion proxy, cold brew has no corpus row)
  C1 roast level  (CoffeeReview six levels)
  C2 variety      (COFFEEREVIEW_C2_LABELS, n >= 50)
  C2 process      (n >= 30)
Also writes the joint C0 x C1 cell table and the runtime bundle product-vector-v1.json
(dims, projection, Matrix_K, Matrix_Q, profiles, alpha, weights). Everything is
CORPUS_MEASURED unless marked otherwise; nothing is fitted.
"""
from __future__ import annotations
import csv, json, math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db" / "data" / "product-vector-v1"
DIMS = ["acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted",
        "spice", "herbal_green", "woody_earthy", "defect"]
ALPHA_DEFAULT = 0.5
MIN_VARIETY, MIN_PROCESS, MIN_CELL = 50, 30, 10
PRODUCT_OPTIONS = {
    "C0": {"pour_over_v60": ("CUPPING", "FILTER_IMMERSION_PROXY_FROM_CUPPING"), "french_press": ("CUPPING", "FILTER_IMMERSION_PROXY_FROM_CUPPING"),
           "espresso": ("ESPRESSO", "CORPUS_MEASURED"), "cold_brew": (None, "NO_CORPUS_ROW_LITERATURE_CLAIM_PENDING")},
    "C1": {"light": ("Light", "CORPUS_MEASURED"), "medium_light": ("Medium-Light", "CORPUS_MEASURED"), "medium": ("Medium", "CORPUS_MEASURED"),
           "medium_dark": ("Medium-Dark", "CORPUS_MEASURED"), "dark": ("Dark", "CORPUS_MEASURED"), "very_dark": ("Very Dark", "CORPUS_MEASURED")},
}


def rows(p: Path):
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def mean_unit(vectors):
    if not vectors:
        return None
    m = [sum(col) / len(vectors) for col in zip(*vectors)]
    n = math.sqrt(sum(x * x for x in m)) or 1.0
    return [x / n for x in m]


def main() -> int:
    lib = {r["effective_record_id"]: r for r in rows(OUT / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE" and r["source_family_id"] == "family.coffeereview_kaggle_parsed"}
    axes = {r["effective_record_id"]: r for r in rows(OUT / "COFFEEREVIEW_STRUCTURE_AXES.tsv")}
    c2 = {r["effective_record_id"]: r for r in rows(OUT / "COFFEEREVIEW_C2_LABELS.tsv")}
    vec = {k: [float(r[f"v_{d}"]) for d in DIMS] for k, r in lib.items()}
    groups = defaultdict(list)
    cells = defaultdict(list)
    for k, v in vec.items():
        prep = lib[k]["preparation_service_id"]
        roast = axes.get(k, {}).get("roast_level", "UNREPORTED")
        groups[("C0", prep)].append(v)
        if roast not in ("", "UNREPORTED", "NA"):
            groups[("C1", roast)].append(v)
            cells[(prep, roast)].append(v)
        lab = c2.get(k)
        if lab:
            if lab["variety"] != "UNRESOLVED" and lab["variety_multi"] == "false":
                groups[("C2_variety", lab["variety"])].append(v)
            if lab["process"] != "UNRESOLVED" and lab["process_multi"] == "false":
                groups[("C2_process", lab["process"])].append(v)
    minimum = {"C0": 1, "C1": MIN_CELL, "C2_variety": MIN_VARIETY, "C2_process": MIN_PROCESS}
    matrix = []
    for (axis, option), vs in sorted(groups.items()):
        if len(vs) < minimum[axis]:
            continue
        m = mean_unit(vs)
        matrix.append({"context_axis": axis, "option": option, "member_count": len(vs), **{f"k_{d}": f"{x:.4f}" for d, x in zip(DIMS, m)},
                       "basis": "CORPUS_MEASURED_COFFEEREVIEW_USABLE_VECTORS", "owner_reviewed": "false"})
    with (OUT / "MATRIX_K.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(matrix[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(matrix)
    cell_rows = []
    for (prep, roast), vs in sorted(cells.items(), key=lambda kv: -len(kv[1])):
        m = mean_unit(vs)
        cell_rows.append({"preparation": prep, "roast_level": roast, "member_count": len(vs), "sufficiency": "MAIN" if len(vs) >= 100 else ("INTERPOLATION" if len(vs) >= MIN_CELL else "SPARSE"),
                          **{f"k_{d}": f"{x:.4f}" for d, x in zip(DIMS, m)}})
    with (OUT / "MATRIX_K_C0_C1_CELLS.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cell_rows[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(cell_rows)

    # runtime bundle
    krows = {(r["context_axis"], r["option"]): r for r in matrix}
    def kvec(axis, option):
        r = krows.get((axis, option))
        return [float(r[f"k_{d}"]) for d in DIMS] if r else None
    bundle_k = {"C0": {}, "C1": {}, "C2_variety": {}, "C2_process": {}}
    for axis in ("C0", "C1"):
        for product_option, (corpus_option, basis) in PRODUCT_OPTIONS[axis].items():
            v = kvec(axis, corpus_option) if corpus_option else None
            bundle_k[axis][product_option] = {"vector": v, "basis": basis, "member_count": krows.get((axis, corpus_option), {}).get("member_count") if corpus_option else None}
    for axis in ("C2_variety", "C2_process"):
        for (a, option), r in krows.items():
            if a == axis:
                bundle_k[axis][option] = {"vector": kvec(axis, option), "basis": r["basis"], "member_count": int(r["member_count"])}
    proj = {r["canonical_concept_id"]: [float(r[d]) for d in DIMS] for r in rows(OUT / "CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv")}
    profiles = [{"profile_id": r["profile_id"], "member_count": int(r["member_count"]), "top_dimensions": r["top_dimensions"], "centroid": [float(r[f"c_{d}"]) for d in DIMS],
                 "owner_name_zh": r["owner_name_zh"], "owner_name_en": r["owner_name_en"], "benchmark_beans": r["benchmark_beans"]} for r in rows(OUT / "FLAVOR_PROFILE_LIBRARY.tsv")]
    questions = {
        "Q5_acid": {"A": {"acidity": 2, "fruity": 1}, "B": {"acidity": 1, "fermented_winey": 2}, "C": {"body": 1}},
        "Q6_sweet": {"A": {"floral": 1, "sweetness": 2}, "B": {"nutty_chocolate": 2, "bitter_roasted": 1}, "C": {"fruity": 2, "sweetness": 2}},
        "Q7_body": {"A": {"body": 1}, "B": {"body": 2}, "C": {"body": 3, "bitter_roasted": 1}},
        "Q8_aroma": {"A": {"floral": 3}, "B": {"nutty_chocolate": 3}, "C": {"fermented_winey": 2, "fruity": 2}},
        "Q9_bitter": {"A": {"nutty_chocolate": 1, "bitter_roasted": 1}, "B": {}},
        "Q10_clean": {"A": {"floral": 1, "acidity": 1}, "B": {"fermented_winey": 1, "body": 1}},
    }
    bundle = {"version": "product-vector-v1", "design": "docs/product/FLAVOR_VECTOR_DESIGN_V1.md", "dimensions": DIMS,
              "alpha_default": ALPHA_DEFAULT, "structure_axis_weight": 0.6, "score_semantics": "cosine similarity; not a probability; uncalibrated",
              "training_run_count": 0, "concept_projection": proj, "matrix_k": bundle_k, "matrix_q": questions, "profiles": profiles,
              "benchmark_beans": [], "notes": ["profiles carry no owner names yet", "benchmark_beans are the owner's; empty", "cold_brew has no corpus row"]}
    (OUT / "product-vector-v1.json").write_text(json.dumps(bundle, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {"matrix_rows": len(matrix), "by_axis": {a: sum(1 for r in matrix if r["context_axis"] == a) for a in ("C0", "C1", "C2_variety", "C2_process")},
               "variety_rows": [(r["option"], r["member_count"]) for r in matrix if r["context_axis"] == "C2_variety"],
               "process_rows": [(r["option"], r["member_count"]) for r in matrix if r["context_axis"] == "C2_process"],
               "cells": [(c["preparation"], c["roast_level"], c["member_count"], c["sufficiency"]) for c in cell_rows]}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
