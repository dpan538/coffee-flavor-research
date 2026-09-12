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
CURRENT = ROOT / "db" / "data" / "current"
DIMS = ["acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted",
        "spice", "herbal_green", "woody_earthy", "defect"]
ALPHA_DEFAULT = 0.5
MIN_VARIETY, MIN_PROCESS, MIN_CELL = 50, 30, 10
PRODUCT_OPTIONS = {
    # owner (review 5): the ways a cup is commonly made; the corpus only measures cupping and espresso, so filter and
    # immersion methods borrow the cupping row, moka borrows nothing (it is neither), cold methods have no row
    "C0": {"espresso": ("ESPRESSO", "CORPUS_MEASURED"), "pour_over_v60": ("CUPPING", "FILTER_IMMERSION_PROXY_FROM_CUPPING"),
           "moka_pot": (None, "NO_CORPUS_ROW (stovetop pressure is neither cupping nor espresso)"), "cold_brew": (None, "NO_CORPUS_ROW_LITERATURE_CLAIM_PENDING"),
           "siphon": ("CUPPING", "FILTER_IMMERSION_PROXY_FROM_CUPPING"), "cold_drip": (None, "NO_CORPUS_ROW (cold method)"),
           "french_press": ("CUPPING", "FILTER_IMMERSION_PROXY_FROM_CUPPING"), "turkish": (None, "NO_CORPUS_ROW (boiled, unfiltered)"),
           "aeropress": ("CUPPING", "FILTER_IMMERSION_PROXY_FROM_CUPPING")},
    "C1": {"very_light": ("Light", "VERY_LIGHT_PROXY_FROM_LIGHT_ROW"), "light": ("Light", "CORPUS_MEASURED"), "medium_light": ("Medium-Light", "CORPUS_MEASURED"), "medium": ("Medium", "CORPUS_MEASURED"),
           "medium_dark": ("Medium-Dark", "CORPUS_MEASURED"), "dark": ("Dark", "CORPUS_MEASURED"), "very_dark": ("Very Dark", "CORPUS_MEASURED")},
    # owner (2026-09-12, copy review 2): the eight processing methods drinkers meet on bags, plus decaf. A method without
    # enough reviews has no reference row: the option exists, V_pred simply gets nothing from it (basis says so).
    "C2_process": {"natural": ("natural", "CORPUS_MEASURED"), "washed": ("washed", "CORPUS_MEASURED"),
                   "honey": ("honey", "NO_CORPUS_ROW (honey / pulped natural / semi-washed reviews with a usable vector are below the minimum of 30)"),
                   "semi_washed": ("honey", "NO_CORPUS_ROW (grouped with honey by the extraction lexicon; below the minimum of 30)"),
                   "wet_hulled": (None, "NO_CORPUS_ROW (2 reviews, below the minimum of 30)"), "anaerobic": ("anaerobic", "CORPUS_MEASURED"),
                   "lactic": (None, "NO_CORPUS_ROW (not in the extraction lexicon)"), "barrel_aged": (None, "NO_CORPUS_ROW (not in the extraction lexicon)"),
                   "decaf": ("decaf", "CORPUS_MEASURED")},
}
# labels the UI shows for every context option (view.ts reads them from the bundle; the engine uses them for the reference line)
CONTEXT_LABELS = {
    "pour_over_v60": {"zh-CN": "手冲 Pour-over", "en": "Pour-over"}, "french_press": {"zh-CN": "法压壶 French press", "en": "French press"},
    "espresso": {"zh-CN": "意式萃取 Espresso", "en": "Espresso"}, "cold_brew": {"zh-CN": "冷萃 Cold brew", "en": "Cold brew"},
    "moka_pot": {"zh-CN": "摩卡壶 Moka pot", "en": "Moka pot"}, "siphon": {"zh-CN": "虹吸壶 Siphon", "en": "Siphon"},
    "cold_drip": {"zh-CN": "冰滴 Cold drip", "en": "Cold drip"}, "turkish": {"zh-CN": "土耳其壶 Turkish", "en": "Turkish pot"}, "aeropress": {"zh-CN": "爱乐压 AeroPress", "en": "AeroPress"},
    "very_light": {"zh-CN": "极浅烘", "en": "Very light"}, "light": {"zh-CN": "浅烘", "en": "Light"}, "medium_light": {"zh-CN": "中浅烘", "en": "Medium-light"},
    "medium": {"zh-CN": "中烘", "en": "Medium"}, "medium_dark": {"zh-CN": "中深烘", "en": "Medium-dark"}, "dark": {"zh-CN": "深烘", "en": "Dark"}, "very_dark": {"zh-CN": "极深烘", "en": "Very dark"},
    "gesha": {"zh-CN": "瑰夏 Gesha", "en": "Gesha"}, "bourbon": {"zh-CN": "波本 Bourbon", "en": "Bourbon"}, "typica": {"zh-CN": "铁皮卡 Typica", "en": "Typica"},
    "caturra": {"zh-CN": "卡杜拉 Caturra", "en": "Caturra"}, "catuai": {"zh-CN": "卡杜艾 Catuai", "en": "Catuai"}, "sl28_sl34": {"zh-CN": "SL28 / SL34", "en": "SL28 / SL34"},
    "pacamara": {"zh-CN": "帕卡马拉 Pacamara", "en": "Pacamara"}, "castillo": {"zh-CN": "卡斯蒂略 Castillo", "en": "Castillo"}, "robusta": {"zh-CN": "罗布斯塔 Robusta", "en": "Robusta"},
    "ethiopian_landrace": {"zh-CN": "埃塞原生种 Heirloom", "en": "Ethiopian landrace"},
    "natural": {"zh-CN": "日晒", "en": "Natural"}, "washed": {"zh-CN": "水洗", "en": "Washed"}, "honey": {"zh-CN": "蜜处理", "en": "Honey"},
    "semi_washed": {"zh-CN": "半水洗", "en": "Semi-washed"}, "wet_hulled": {"zh-CN": "湿刨法", "en": "Wet-hulled"}, "anaerobic": {"zh-CN": "厌氧发酵", "en": "Anaerobic"},
    "lactic": {"zh-CN": "乳酸发酵", "en": "Lactic fermentation"}, "barrel_aged": {"zh-CN": "酒桶发酵", "en": "Barrel-aged"}, "decaf": {"zh-CN": "低因", "en": "Decaf"},
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
    for axis in ("C0", "C1", "C2_process"):
        for product_option, (corpus_option, basis) in PRODUCT_OPTIONS[axis].items():
            v = kvec(axis, corpus_option) if corpus_option else None
            bundle_k[axis][product_option] = {"vector": v, "basis": basis, "member_count": krows.get((axis, corpus_option), {}).get("member_count") if corpus_option else None}
    for axis in ("C2_variety",):
        for (a, option), r in krows.items():
            if a == axis:
                bundle_k[axis][option] = {"vector": kvec(axis, option), "basis": r["basis"], "member_count": int(r["member_count"])}
    proj = {r["canonical_concept_id"]: [float(r[d]) for d in DIMS] for r in rows(OUT / "CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv")}
    profiles = [{"profile_id": r["profile_id"], "member_count": int(r["member_count"]), "top_dimensions": r["top_dimensions"], "centroid": [float(r[f"c_{d}"]) for d in DIMS],
                 "benchmark_beans": r["benchmark_beans"], "anchor_id": r["anchor_id"]} for r in rows(OUT / "FLAVOR_PROFILE_LIBRARY.tsv")]
    questions = {
        "Q5_acid": {"A": {"acidity": 2, "fruity": 1}, "B": {"acidity": 1, "fermented_winey": 2}, "C": {"body": 1}, "D": {"acidity": 2, "bitter_roasted": 1, "defect": 0.5}},  # D: sour and bitter with a sharp edge (owner review 4, 2026-09-12)
        "Q6_sweet": {"A": {"floral": 1, "sweetness": 2}, "B": {"nutty_chocolate": 2, "bitter_roasted": 1}, "C": {"fruity": 2, "sweetness": 2}, "D": {}},  # D: sweetness not noticeable — an absence adds nothing (owner copy review 2026-09-12)
        "Q7_body": {"A": {"body": 1}, "B": {"body": 2}, "C": {"body": 3, "bitter_roasted": 1}, "D": {"body": 1, "defect": 0.5}},  # D: astringent, drying (owner review 4)
        "Q8_aroma": {"A": {"floral": 3}, "B": {"nutty_chocolate": 3}, "C": {"fermented_winey": 2, "fruity": 2}, "D": {}},  # D: no clear aroma (owner copy review 2, 2026-09-12)
        "Q9_bitter": {"A": {"bitter_roasted": 1}, "B": {}, "C": {"bitter_roasted": 2}},  # intensity only (owner copy review 2, 2026-09-12): the label no longer says 回甘, so A no longer adds nutty_chocolate
        "Q10_clean": {"A": {"fermented_winey": 0.5, "body": 0.5, "fruity": 0.5}, "B": {"body": 1, "sweetness": 0.5}, "C": {"floral": 1, "acidity": 1}, "D": {}},  # owner review 5: A mixed, a little of everything; B full and consistent; C clear layers; D hard to say
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
                                   "evidence_state": r["evidence_state"], "citation_ref": r["citation_ref"], "source_id": r["source_id"],
                                   "source_title": r.get("source_title", "") or ("owner" if r["source_id"] == "owner" else r["source_id"])})
    merged_path = OUT / "CONTEXT_STATEMENTS_MERGED.tsv"
    with merged_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n"); w.writerow(["context_id", "context_parts", "statement_zh", "statement_en", "evidence_state", "citation_ref", "source_id"])
        for st in statements:
            w.writerow([st["context_id"], "|".join(f"{p['axis']}:{p['option']}" for p in st["parts"]), st["zh-CN"], st["en"], st["evidence_state"], st["citation_ref"], st["source_id"]])
    for pr, raw in zip(profiles, rows(OUT / "FLAVOR_PROFILE_LIBRARY.tsv")):
        pr["owner_name"] = {"zh-CN": raw["owner_name_zh"], "en": raw["owner_name_en"]}
        pr["display_tags"] = {"zh-CN": [t for t in raw["display_tags_zh"].split("|") if t], "en": [t for t in raw["display_tags_en"].split("|") if t]}
        pr["owner_reviewed"] = raw.get("owner_reviewed", "false") == "true"
    sources_path = OUT / "LITERATURE_SOURCES.json"
    sources = json.loads(sources_path.read_text(encoding="utf-8"))["sources"] if sources_path.is_file() else []
    for st in statements:
        if st["source_id"] != "owner":
            src = next((x for x in sources if x["source_id"] == st["source_id"]), None)
            if src:
                st["source_title"] = src["title"]
    presentation = {"locales": ["zh-CN", "en"], "tag_count": 4, "sources": sources, "dimension_labels": dimension_labels, "dimension_tags": dimension_tags, "concept_tags": concept_tags,
                    "delta_words": {"zh-CN": {"pos": "比这个语境的理论值更明显", "neg": "比这个语境的理论值更弱"}, "en": {"pos": "stronger than this context predicts", "neg": "weaker than this context predicts"}},
                    # consumer-facing layer (owner R3-D15): no raw enum reaches the screen; the calibration sentence reads as a
                    # sensory report, not as a correction of the drinker
                    # owner copy review 2026-09-12: the label says what kind of statement it is — a project note, a count from
                    # the data, a research reference — and never claims this cup was measured; a claim pending a locator or
                    # re-verification has no label and is filtered out of the UI (displayable_evidence_states)
                    # owner copy review 2 (2026-09-12): the owner's causal sentences (OWNER_STATEMENT) are project rules — they
                    # document how the initial reference is formed and live in the method notes, never on the card. The card
                    # shows: the initial reference (computed from V_pred), sourced research references, the difference line.
                    "evidence_labels": {"REFERENCE_BASIS": {"zh-CN": "初始参考", "en": "Initial reference"},
                                        "CORPUS_MEASURED": {"zh-CN": "资料统计", "en": "From the data"},
                                        "LITERATURE_CLAIM": {"zh-CN": "研究参考", "en": "Research reference"},
                                        "COMPUTED_DELTA": {"zh-CN": "你的描述", "en": "Your description"},
                                        "PRODUCT_NOTE": {"zh-CN": "提示", "en": "Note"}},
                    "displayable_evidence_states": ["REFERENCE_BASIS", "CORPUS_MEASURED", "LITERATURE_CLAIM", "COMPUTED_DELTA", "PRODUCT_NOTE"],
                    # ΔV compares the description with the initial reference; the sentence names that comparison and nothing else
                    "delta_templates": {"zh-CN": {"pos": "相较于初始参考，你的描述中，{label}更突出。", "neg": "相较于初始参考，你的描述中，{label}较弱。",
                                                  "pos_variants": ["相较于初始参考，你的描述中，{label}更突出。", "你的描述比初始参考更偏向{label}。", "{label}在你的描述里比初始参考更明显。"],
                                                  "neg_variants": ["相较于初始参考，你的描述中，{label}较弱。", "你的描述比初始参考更少提到{label}。", "{label}在你的描述里比初始参考淡一些。"],
                                                  "pair_variants": ["相较于初始参考，你的描述更偏向{label}，{label2}则弱一些。", "你的描述里{label}比初始参考更明显，{label2}没那么突出。"]},
                                        "en": {"pos": "Compared with the initial reference profile, {label} is more pronounced in your description.",
                                               "neg": "Compared with the initial reference profile, {label} is less pronounced in your description.",
                                               "pos_variants": ["Compared with the initial reference profile, {label} is more pronounced in your description.", "Your description leans more toward {label} than the initial reference does.", "{label} comes through more clearly in your description than in the initial reference."],
                                               "neg_variants": ["Compared with the initial reference profile, {label} is less pronounced in your description.", "Your description mentions {label} less than the initial reference does.", "{label} is fainter in your description than in the initial reference."],
                                               "pair_variants": ["Compared with the initial reference, your description leans toward {label}, with {label2} weaker.", "{label} stands out more in your description than in the initial reference, while {label2} recedes."]}},
                    "reference_basis_templates": {"zh-CN": {"text": "根据{context}，初始参考侧重{dims}。", "explain": "初始参考来自评审资料的统计，只是起点，不是这杯咖啡的测定。", "join": "、", "context_join": "、"},
                                                  "en": {"text": "From {context}, the initial reference leans toward {dims}.", "explain": "It comes from the review data and is a starting point, not a measurement of this cup.", "join": ", ", "context_join": ", "}},
                    "context_labels": CONTEXT_LABELS,
                    "citation_prefix": {"zh-CN": "参考资料：", "en": "Reference: "},
                    "card_heading": {"zh-CN": "风味卡", "en": "Flavor card"},
                    "preview_heading": {"zh-CN": "这杯咖啡的风味", "en": "This cup's flavor"},
                    "science_heading": {"zh-CN": "关于这段描述", "en": "About this description"},
                    # the papery / stale group: show the words, ask for a second look, judge nothing
                    "defect_note": {"zh-CN": "这些描述常与储存或处理有关，值得再喝一口确认。这里不对这杯咖啡做质量判断。",
                                    "en": "These descriptions are often linked to storage or processing; worth a second sip to confirm. No quality judgement is made here."},
                    "context_statements": statements,
                    "tag_rules": {"priority_1": "concept-level tags when concept ids are present, ranked by projection weight against the vector", "priority_2": "dimension-level tags for dominant dimensions (weight > 0.15), first unused tag of the dimension's list", "defect_guard": "defect tags only when defect dominates (>= 0.5)"},
                    "layout": {"headline": "owner_name + display_tags (3-4 minimalist tags)", "science": "collapsible: context statements whose parts are all answered (most specific first) + the two largest delta dimensions, each with evidence_state and citation_ref"}}
    lexicon = rows(OUT / "CN_CONSUMER_FLAVOR_LEXICON.tsv") if (OUT / "CN_CONSUMER_FLAVOR_LEXICON.tsv").is_file() else []
    consumer_terms = {}
    for r in lexicon:
        if r.get("display_eligible", "true") == "false":
            continue  # structural / generic consumer words: usable by the utterance mapper, never printed on a card
        consumer_terms.setdefault(r["primary_dimension"], {"zh-CN": [], "en": []})
        if r["surface_term_zh"]:
            consumer_terms[r["primary_dimension"]]["zh-CN"].append(r["surface_term_zh"])
        if r["surface_term_en"]:
            consumer_terms[r["primary_dimension"]]["en"].append(r["surface_term_en"])
    mapper_terms = {}
    for r in lexicon:
        mapper_terms.setdefault(r["primary_dimension"], {"zh-CN": [], "en": []})
        if r["surface_term_zh"]:
            mapper_terms[r["primary_dimension"]]["zh-CN"].append(r["surface_term_zh"])
        if r["surface_term_en"]:
            mapper_terms[r["primary_dimension"]]["en"].append(r["surface_term_en"])
    presentation["mapper_terms"] = mapper_terms
    presentation["consumer_terms"] = consumer_terms
    # owner's coherence decision tree (2026-09-12): base pair Q0-Q1, check Q2-Q3, confirm Q4-Q5, Q6 = escalation checkbox.
    # slot -> Matrix_Q question mapping is the operator's proposal (base pair = the two strongest movers).
    question_flow = {
        "slots": [{"slot": "Q0", "question": "Q5_acid", "role": "base"}, {"slot": "Q1", "question": "Q8_aroma", "role": "base"},
                  {"slot": "Q2", "question": "Q6_sweet", "role": "check"}, {"slot": "Q3", "question": "Q7_body", "role": "check"},
                  {"slot": "Q4", "question": "Q9_bitter", "role": "confirm"}, {"slot": "Q5", "question": "Q10_clean", "role": "confirm"}],
        # owner R3-D10 (2026-09-12): 0.80 coherent / 0.65 severe — Path 2 as the main path is the intended
        # product rhythm ("perceived expertise"), Path 1 for the ~30% with highly consistent answers.
        "thresholds": {"coherent": 0.80, "mild": 0.65},
        # Answers occupy 1-2 dimensions each, so raw sub-vector cosines are 0 for most answer pairs
        # (Q0-Q1 vs Q2-Q3: 76 of 81 combinations < 0.65). Coherence is therefore measured in profile-
        # signature space: each answer group -> its cosine to the 16 centroids -> cosine between signatures.
        "coherence_space": "profile_signature",
        "calibration_2026_09_12": {"Q0-Q1_vs_Q2-Q3_over_81_combinations": {"min": 0.62, "median": 0.73, "p75": 0.82, "max": 0.98, "coherent_at_0.85": 18, "mild": 56, "severe_below_0.65": 7},
                                    "note": "measured under 0.85/0.65; owner moved to 0.80/0.65 (R3-D10) so Path 2 stays the main path and Path 1 serves the most consistent ~30%."},
        "alpha_strong": 0.9,
        "first_description": {"main": 3, "secondary": 5, "pick_count": 5},
        "q6": {"option_count": 8, "kind": "dimension_words_by_largest_delta", "multi_select": True},
        # roast-polarity paradox guard: bright-light (+) vs dark-heavy (-). Two answer groups whose polarities
        # flip with magnitude >= min_magnitude are a sensory paradox (owner's Persona C: light-roast acidity
        # then heavy bitterness) and are demoted to severe. A context whose polarity flips against the base
        # pair (owner's Persona B: dark espresso, bright peach acid) caps the first check at mild -> Path 2.
        "polarity": {"weights": {"acidity": 1.0, "floral": 1.0, "herbal_green": 1.0, "bitter_roasted": -1.0, "woody_earthy": -1.0, "nutty_chocolate": -0.7},
                     "min_magnitude": 0.55, "context_min_magnitude": 0.25},
        # the hybrid utterance mapper (owner spec): score = alpha * cosine + beta * cue hits; negation forcing
        "utterance_mapper": {"alpha": 1.0, "beta": 0.5, "min_projection": 0.2, "direction_questions": ["Q0", "Q1", "Q2", "Q5"], "cue_questions": ["Q3", "Q4"],
                             "negation_prefixes": {"zh-CN": ["不", "没", "没有", "没什么", "无", "毫无", "几乎不", "几乎没", "不太", "怕", "不要", "不想要", "一点都不", "讨厌", "不喜欢", "不爱"], "en": ["not ", "no ", "without ", "hardly any ", "zero ", "hate ", "dislike "]},
                             "forced_by_negation": {"zh-CN": {"苦": ["Q4", "B"], "酸": ["Q0", "C"], "甜": ["Q2", "D"]}, "en": {"bitter": ["Q4", "B"], "acid": ["Q0", "C"], "sour": ["Q0", "C"], "sweet": ["Q2", "D"]}}},
        "closing": {"zh-CN": "感谢使用，祝你享受这杯咖啡！", "en": "Thank you — enjoy the cup!"},
        "slot_mapping_owner_reviewed": True,  # R3-D10: Q0 acid, Q1 aroma, Q2 sweetness, Q3 body, Q4 bitterness, Q5 complexity
    }
    # question bank: colloquial zh-CN / en prompts and option labels + cue words (utterance mapper); operator draft
    question_bank = {}
    for r in rows(OUT / "QUESTION_BANK.tsv"):
        q = question_bank.setdefault(r["slot"], {"question": r["question_id"], "prompt": {"zh-CN": r["prompt_zh_cn"], "en": r["prompt_en"]}, "options": {}, "owner_reviewed": r["owner_reviewed"] == "true"})
        q["options"][r["option"]] = {"label": {"zh-CN": r["label_zh_cn"], "en": r["label_en"]}, "cues": {"zh-CN": [c for c in r["cues_zh_cn"].split("|") if c], "en": [c for c in r["cues_en"].split("|") if c]}}
    # C2 refinements (owner R3-D13): blends = normalised mean of up to 3 variety rows; origin is an optional
    # macro-region chip that adds a small bias (delta 0.1) on named axes — never required, never dominant.
    context_rules = {
        "blend": {"max_varieties": 3, "composition": "normalize(sum of variety vectors)"},
        "origin_bias_delta": 0.1,
        "origin_continents": {"africa": {"zh-CN": "非洲", "en": "Africa"}, "asia": {"zh-CN": "亚洲", "en": "Asia"}, "americas": {"zh-CN": "美洲", "en": "Americas"}},
        # owner's origin chart (2026-09-12): countries grouped by continent; the continent's usual tendencies give the δ-0.1
        # nudge (Africa fruit / floral, light body; Asia woody / spice, medium body; Americas nut / cocoa, fuller body), with a
        # few country-level specifics. The chip shows only the place name — the nudge is internal.
        "origin_regions": {
            "ethiopia": {"label": {"zh-CN": "埃塞俄比亚", "en": "Ethiopia"}, "continent": "africa", "bias": ["floral", "fruity"]},
            "kenya": {"label": {"zh-CN": "肯尼亚", "en": "Kenya"}, "continent": "africa", "bias": ["acidity", "fruity"]},
            "rwanda": {"label": {"zh-CN": "卢旺达", "en": "Rwanda"}, "continent": "africa", "bias": ["fruity", "floral"]},
            "tanzania": {"label": {"zh-CN": "坦桑尼亚", "en": "Tanzania"}, "continent": "africa", "bias": ["acidity", "fruity"]},
            "yunnan": {"label": {"zh-CN": "中国云南", "en": "Yunnan, China"}, "continent": "asia", "bias": ["nutty_chocolate", "body"]},
            "india": {"label": {"zh-CN": "印度", "en": "India"}, "continent": "asia", "bias": ["spice", "body"]},
            "indonesia": {"label": {"zh-CN": "印尼", "en": "Indonesia"}, "continent": "asia", "bias": ["woody_earthy", "body"]},
            "vietnam": {"label": {"zh-CN": "越南", "en": "Vietnam"}, "continent": "asia", "bias": ["body", "nutty_chocolate"]},
            "yemen": {"label": {"zh-CN": "也门", "en": "Yemen"}, "continent": "asia", "bias": ["spice", "fruity"]},
            "philippines": {"label": {"zh-CN": "菲律宾", "en": "Philippines"}, "continent": "asia", "bias": ["body", "woody_earthy"]},
            "brazil": {"label": {"zh-CN": "巴西", "en": "Brazil"}, "continent": "americas", "bias": ["nutty_chocolate", "sweetness"]},
            "panama": {"label": {"zh-CN": "巴拿马", "en": "Panama"}, "continent": "americas", "bias": ["floral", "acidity"]},
            "jamaica": {"label": {"zh-CN": "牙买加", "en": "Jamaica"}, "continent": "americas", "bias": ["body", "sweetness"]},
            "mexico": {"label": {"zh-CN": "墨西哥", "en": "Mexico"}, "continent": "americas", "bias": ["nutty_chocolate", "body"]},
            "colombia": {"label": {"zh-CN": "哥伦比亚", "en": "Colombia"}, "continent": "americas", "bias": ["fruity", "sweetness"]},
            "guatemala": {"label": {"zh-CN": "危地马拉", "en": "Guatemala"}, "continent": "americas", "bias": ["nutty_chocolate", "fruity"]},
            "nicaragua": {"label": {"zh-CN": "尼加拉瓜", "en": "Nicaragua"}, "continent": "americas", "bias": ["nutty_chocolate", "sweetness"]},
            "honduras": {"label": {"zh-CN": "洪都拉斯", "en": "Honduras"}, "continent": "americas", "bias": ["sweetness", "nutty_chocolate"]},
            "costa_rica": {"label": {"zh-CN": "哥斯达黎加", "en": "Costa Rica"}, "continent": "americas", "bias": ["acidity", "sweetness"]},
        },
        "owner_reviewed": True,
    }
    cleaned = json.loads((CURRENT / "CLEANED_83K_MANIFEST.json").read_text(encoding="utf-8"))
    semantic = json.loads((CURRENT / "BATCH7_SEMANTIC_MANIFEST.json").read_text(encoding="utf-8"))
    gactt = json.loads((OUT / "GACTT_SUMMARY.json").read_text(encoding="utf-8")) if (OUT / "GACTT_SUMMARY.json").is_file() else {}
    library_rows = [r for r in rows(OUT / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE"]
    family_mass: dict[str, dict] = {}
    for r in library_rows:
        fam = family_mass.setdefault(r["source_family_id"].removeprefix("family."), {"family": r["source_family_id"].removeprefix("family."), "coffees": 0, "mass": [0.0] * len(DIMS)})
        fam["coffees"] += 1
        for i, d in enumerate(DIMS):
            fam["mass"][i] += float(r[f"v_{d}"])
    families = sorted(family_mass.values(), key=lambda f: -f["coffees"])
    for f in families:
        f["mass"] = [round(x, 2) for x in f["mass"]]
    corpus_facts = {"source_assertions": cleaned["source_assertion_count"], "valid_source_assertions": cleaned["valid_source_assertion_count"],
                    "families": families,
                    "coffees": len(rows(OUT / "COFFEE_VECTOR_LIBRARY.tsv")), "usable_coffee_vectors": sum(1 for r in rows(OUT / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE"),
                    "semantic_relation_edges": semantic["semantic_relation_count"], "canonical_concepts": len(proj), "dimensions": len(DIMS), "profiles": len(profiles),
                    "consumer_respondents": gactt.get("respondents", 0), "consumer_notes": gactt.get("notes", 0), "literature_sources": len(sources), "literature_claims": sum(s["claims"] for s in sources), "literature_claims_live": sum(s.get("claims_live", s["claims"]) for s in sources), "literature_claims_pending_review": sum(s.get("claims_pending_review", 0) for s in sources),
                    "mean_questions": 5.70}
    bundle = {"version": "product-vector-v1", "design": "docs/product/FLAVOR_VECTOR_DESIGN_V1.md", "dimensions": DIMS, "question_flow": question_flow, "question_bank": question_bank, "context_rules": context_rules, "corpus_facts": corpus_facts,
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
