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
                 "benchmark_beans": r["benchmark_beans"], "anchor_id": r["anchor_id"]} for r in rows(OUT / "FLAVOR_PROFILE_LIBRARY.tsv")]
    questions = {
        "Q5_acid": {"A": {"acidity": 2, "fruity": 1}, "B": {"acidity": 1, "fermented_winey": 2}, "C": {"body": 1}},
        "Q6_sweet": {"A": {"floral": 1, "sweetness": 2}, "B": {"nutty_chocolate": 2, "bitter_roasted": 1}, "C": {"fruity": 2, "sweetness": 2}},
        "Q7_body": {"A": {"body": 1}, "B": {"body": 2}, "C": {"body": 3, "bitter_roasted": 1}},
        "Q8_aroma": {"A": {"floral": 3}, "B": {"nutty_chocolate": 3}, "C": {"fermented_winey": 2, "fruity": 2}},
        "Q9_bitter": {"A": {"nutty_chocolate": 1, "bitter_roasted": 1}, "B": {}},
        "Q10_clean": {"A": {"floral": 1, "acidity": 1}, "B": {"fermented_winey": 1, "body": 1}},
    }
    # presentation layer (owner 2026-09-12): one vector backend, two languages. Minimalist CN tag
    # arrays for zh-CN, scientific wording for en; the science line is a collapsible second layer.
    tags = rows(OUT / "CONCEPT_FLAVOR_TAGS.tsv")
    split = lambda v: [t for t in v.split("|") if t]
    dimension_labels = {r["key"].removeprefix("dim:"): {"zh-CN": r["label_zh_cn"], "en": r["label_en"]} for r in tags if r["kind"] == "dimension"}
    dimension_tags = {r["key"].removeprefix("dim:"): {"zh-CN": split(r["tags_zh_cn"]), "en": split(r["tags_en"])} for r in tags if r["kind"] == "dimension"}
    concept_tags = {r["key"]: {"zh-CN": r["tags_zh_cn"], "en": r["tags_en"]} for r in tags if r["kind"] == "concept"}
    statements = []
    for name in ("CONTEXT_STATEMENTS.tsv", "LITERATURE_CLAIMS.tsv"):
        path = OUT / name
        if path.is_file():
            for r in rows(path):
                parts = [{"axis": part.split(":")[0], "option": part.split(":")[1]} for part in r["context_parts"].split("|") if ":" in part]
                statements.append({"context_id": r["context_id"], "parts": parts, "zh-CN": r["statement_zh"], "en": r["statement_en"],
                                   "evidence_state": r["evidence_state"], "citation_ref": r["citation_ref"], "source_id": r["source_id"]})
    merged_path = OUT / "CONTEXT_STATEMENTS_MERGED.tsv"
    with merged_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(["context_id", "context_parts", "statement_zh", "statement_en", "evidence_state", "citation_ref", "source_id"])
        for st in statements:
            w.writerow([st["context_id"], "|".join(f"{p['axis']}:{p['option']}" for p in st["parts"]), st["zh-CN"], st["en"], st["evidence_state"], st["citation_ref"], st["source_id"]])
    for pr, raw in zip(profiles, rows(OUT / "FLAVOR_PROFILE_LIBRARY.tsv")):
        pr["owner_name"] = {"zh-CN": raw["owner_name_zh"], "en": raw["owner_name_en"]}
        pr["display_tags"] = {"zh-CN": [t for t in raw["display_tags_zh"].split("|") if t], "en": [t for t in raw["display_tags_en"].split("|") if t]}
        pr["owner_reviewed"] = raw.get("owner_reviewed", "false") == "true"
    presentation = {"locales": ["zh-CN", "en"], "tag_count": 4, "dimension_labels": dimension_labels, "dimension_tags": dimension_tags, "concept_tags": concept_tags,
                    "delta_words": {"zh-CN": {"pos": "比这个语境的理论值更明显", "neg": "比这个语境的理论值更弱"}, "en": {"pos": "stronger than this context predicts", "neg": "weaker than this context predicts"}},
                    "context_statements": statements,
                    "tag_rules": {"priority_1": "concept-level tags when concept ids are present, ranked by projection weight against the vector", "priority_2": "dimension-level tags for dominant dimensions (weight > 0.15), first unused tag of the dimension's list", "defect_guard": "defect tags only when defect dominates (>= 0.5)"},
                    "layout": {"headline": "owner_name + display_tags (3-4 minimalist tags)", "science": "collapsible: context statements whose parts are all answered (most specific first) + the two largest delta dimensions, each with evidence_state and citation_ref"}}
    lexicon = rows(OUT / "CN_CONSUMER_FLAVOR_LEXICON.tsv") if (OUT / "CN_CONSUMER_FLAVOR_LEXICON.tsv").is_file() else []
    consumer_terms = {}
    for r in lexicon:
        consumer_terms.setdefault(r["primary_dimension"], {"zh-CN": [], "en": []})
        consumer_terms[r["primary_dimension"]]["zh-CN"].append(r["surface_term_zh"]); consumer_terms[r["primary_dimension"]]["en"].append(r["surface_term_en"])
    presentation["consumer_terms"] = consumer_terms
    # owner's coherence decision tree (2026-09-12): base pair Q0-Q1, check Q2-Q3, confirm Q4-Q5, Q6 = escalation checkbox.
    # slot -> Matrix_Q question mapping is the operator's proposal (base pair = the two strongest movers).
    question_flow = {
        "slots": [{"slot": "Q0", "question": "Q5_acid", "role": "base"}, {"slot": "Q1", "question": "Q8_aroma", "role": "base"},
                  {"slot": "Q2", "question": "Q6_sweet", "role": "check"}, {"slot": "Q3", "question": "Q7_body", "role": "check"},
                  {"slot": "Q4", "question": "Q9_bitter", "role": "confirm"}, {"slot": "Q5", "question": "Q10_clean", "role": "confirm"}],
        "thresholds": {"coherent": 0.85, "mild": 0.65},
        # Answers occupy 1-2 dimensions each, so raw sub-vector cosines are 0 for most answer pairs
        # (Q0-Q1 vs Q2-Q3: 76 of 81 combinations < 0.65). Coherence is therefore measured in profile-
        # signature space: each answer group -> its cosine to the 16 centroids -> cosine between signatures.
        "coherence_space": "profile_signature",
        "calibration_2026_09_12": {"Q0-Q1_vs_Q2-Q3_over_81_combinations": {"min": 0.62, "median": 0.73, "p75": 0.82, "max": 0.98, "coherent_at_0.85": 18, "mild": 56, "severe_below_0.65": 7},
                                    "note": "owner thresholds kept; with them Path 2 (mild) is the common path. 0.80/0.65 or 0.75/0.62 would make Path 1 common."},
        "alpha_strong": 0.9,
        "first_description": {"main": 3, "secondary": 5, "pick_count": 5},
        "q6": {"option_count": 8, "kind": "dimension_words_by_largest_delta", "multi_select": True},
        "closing": {"zh-CN": "感谢使用，祝你享受这杯咖啡！", "en": "Thank you — enjoy the cup!"},
        "slot_mapping_owner_reviewed": False,
    }
    bundle = {"version": "product-vector-v1", "design": "docs/product/FLAVOR_VECTOR_DESIGN_V1.md", "dimensions": DIMS, "question_flow": question_flow,
              "alpha_default": ALPHA_DEFAULT, "structure_axis_weight": 0.6, "score_semantics": "cosine similarity; not a probability; uncalibrated",
              "training_run_count": 0, "concept_projection": proj, "matrix_k": bundle_k, "matrix_q": questions, "profiles": profiles,
              "benchmark_beans": [], "presentation": presentation,
              "notes": ["benchmark_beans are the owner's names per profile (benchmark_beans column); vectors for them are not yet built", "cold_brew has no corpus row",
                        "literature claims arrive via db/data/external-literature (ingest-external-literature.py)"]}
    (OUT / "product-vector-v1.json").write_text(json.dumps(bundle, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = {"matrix_rows": len(matrix), "by_axis": {a: sum(1 for r in matrix if r["context_axis"] == a) for a in ("C0", "C1", "C2_variety", "C2_process")},
               "variety_rows": [(r["option"], r["member_count"]) for r in matrix if r["context_axis"] == "C2_variety"],
               "process_rows": [(r["option"], r["member_count"]) for r in matrix if r["context_axis"] == "C2_process"],
               "cells": [(c["preparation"], c["roast_level"], c["member_count"], c["sufficiency"]) for c in cell_rows]}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
