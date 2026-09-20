#!/usr/bin/env python3
"""Dynamic question bank (owner, 2026-09-19, R3-D40): the options every kind of coffee sees.

The question table (DYNAMIC_QUESTION_BANK.tsv, owner-reviewed wording) holds option pools of six to ten. The corpus only
PRUNES a pool to the four options this kind of coffee is most often described with — it never sorts them: the app shows
the survivors in the pool's fixed order, plus the question's own "does not stand out" option, five at most.

Reads public files only:
  DYNAMIC_QUESTION_BANK.tsv, DYNAMIC_QUESTION_PROMPTS.tsv      the questions, options, wordings, deltas, focus
  COFFEE_VECTOR_LIBRARY.tsv, COFFEEREVIEW_STRUCTURE_AXES.tsv   usable records, roast level, body percentile
  COFFEEREVIEW_C2_LABELS.tsv                                   variety and process
  COFFEEREVIEW_AROMA_AFTERTASTE_AXES.tsv                       aroma / aftertaste levels within a roast band
  db/data/current/CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv      the concepts each record mentions
Writes db/data/product-vector-v1/DYNAMIC_QUESTION_BANK_BUILD.json, which build-matrix-k-v1.py embeds in the bundle, and
DYNAMIC_OPTION_SHARES.tsv (the shares behind the pruning, for review; not shipped).

Source correction: 80% of the corpus is one publication, and its house style would pass for what coffee tastes like
("cedar" is in 22.6% of its reviews, 3.6% of Cup of Excellence records). For every option the within-question share is
compared between the two sources on comparable coffees (light-band cupping), the ratio is clamped to 0.33–3 and applied
half-way (geometric mean of the share and the corrected share).
"""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PV = ROOT / "db" / "data" / "product-vector-v1"
LEDGER = ROOT / "db" / "data" / "current" / "CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv"
MIN_N = 30  # a group smaller than this falls back to the next one in the priority list
# owner, 2026-09-20: a question shows FOUR options, chosen from its pool; five are acceptable only for the first
# questions and for a strong correction, and there "I can't say" is the fifth option — an option like the others, never
# a line under them. So:
#   first question (acidity and fruit)    three pruned options, "it does not stand out", "I can't say"            = 5
#   second question (main aroma)          three pruned options, "fruit stands out", and its "I can't say", worded
#                                         for an aroma: "it comes as a whole, I can't pick what stands out" (B0)      = 5
#   sweetness, mouthfeel                  three options and "it does not stand out"                                = 4
#   second level ("which one?")           three words and "I can't say" (a reader may know the kind, not the word)  = 4
#   aroma strength, overall impression    their four levels                                                        = 4
#   bitterness, aftertaste                four of their five levels, by roast (SCALE_WINDOWS); the full five levels
#                                         of bitterness only as a strong correction (answers in severe conflict)
KEEP = 3
# The aroma question has ten kinds of aroma to choose from and "fruit stands out" is always among its options: with
# three slots only two kinds would survive (light washed coffees would lose "flowers"). It keeps four, and its fifth
# option — "the aroma comes as a whole, I can't pick what stands out" — is its "I can't say".
KEEP_BY_QUESTION = {"B": 4}
SECOND_KEEP = 3
MAX_TAPPABLE = 5
TAPPABLE = {"A": 5, "B": 5, "default": 4}
# which four of a five-level scale a cup is shown, by roast band: charred bitterness is not offered for a light roast,
# "slight, like cocoa" not for a dark one; an aftertaste that turns sweet belongs to lighter roasts, one that is mostly
# bitter or drying to dark ones (operator draft for the owner's review, like the mouthfeel windows)
SCALE_WINDOWS = {"E3": {"light": ["E3a", "E3b", "E3c", "E3d"], "medium": ["E3a", "E3b", "E3c", "E3d"], "dark": ["E3a", "E3c", "E3d", "E3e"]},
                 "E2": {"light": ["E2a", "E2b", "E2c", "E2d"], "medium": ["E2a", "E2b", "E2c", "E2d"], "dark": ["E2a", "E2b", "E2c", "E2e"]}}
# Against overfitting (owner, 2026-09-20): a small group's shares are pulled toward its parent group's — with n records
# the group keeps n / (n + SHRINK) of its own estimate. At 30 records a group is mostly its parent; at 1,500 mostly itself.
SHRINK = 60.0
CR, COE = "family.coffeereview_kaggle_parsed", "family.ace_cup_of_excellence"
BAND = {"Light": "light", "Medium-Light": "light", "Medium": "medium", "Medium-Dark": "dark", "Dark": "dark", "Very Dark": "dark"}
SEP = " ‖ "
csv.field_size_limit(10**9)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def parse_deltas(text: str) -> dict[str, float]:
    return {k: float(v) for k, v in (item.split(":") for item in text.split(";") if item)}


def main() -> int:
    # --holdout <test set json> --out <path>: build without the test set's records, for the flow simulation
    # (scripts/simulate-question-flows.mjs); the repository's own build uses every record
    args = sys.argv[1:]
    holdout = set()
    for i, a in enumerate(args):  # --holdout may be given more than once
        if a == "--holdout":
            holdout |= {r["id"] for r in json.loads(Path(args[i + 1]).read_text(encoding="utf-8"))["records"]}
    shrink = float(args[args.index("--shrink") + 1]) if "--shrink" in args else SHRINK
    out_path = Path(args[args.index("--out") + 1]) if "--out" in args else PV / "DYNAMIC_QUESTION_BANK_BUILD.json"
    bank = rows(PV / "DYNAMIC_QUESTION_BANK.tsv")
    prompts = rows(PV / "DYNAMIC_QUESTION_PROMPTS.tsv")
    lib = {r["effective_record_id"]: r for r in rows(PV / "COFFEE_VECTOR_LIBRARY.tsv") if r["vector_state"] == "USABLE" and r["effective_record_id"] not in holdout}
    axes = {r["effective_record_id"]: r for r in rows(PV / "COFFEEREVIEW_STRUCTURE_AXES.tsv")}
    c2 = {r["effective_record_id"]: r for r in rows(PV / "COFFEEREVIEW_C2_LABELS.tsv")}
    structure = {r["effective_record_id"]: r for r in rows(PV / "COFFEEREVIEW_AROMA_AFTERTASTE_AXES.tsv")}
    concepts: dict[str, set[str]] = defaultdict(set)
    with LEDGER.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["effective_record_id"] in lib:
                concepts[r["effective_record_id"]].update(c[8:] for c in r["canonical_concept_ids"].split("|") if c.startswith("sensory."))

    cr = [e for e, r in lib.items() if r["source_family_id"] == CR and e in axes and BAND.get(axes[e]["roast_level"])]
    coe = [e for e, r in lib.items() if r["source_family_id"] == COE]
    comparable = [e for e in cr if BAND[axes[e]["roast_level"]] == "light" and lib[e]["preparation_service_id"] == "CUPPING"]

    def facets(e: str) -> dict[str, str]:
        label = c2.get(e, {})
        known = lambda value: "" if value in ("", "UNRESOLVED") else value  # an unresolved label is no facet at all
        return {"band": BAND[axes[e]["roast_level"]], "process": known(label.get("process") or ""), "variety": known(label.get("variety") or ""),
                "prep": "espresso" if lib[e]["preparation_service_id"] == "ESPRESSO" else ""}

    # every combination of facets the app may look up, most specific first (the app walks the same list)
    PRIORITY = [("band", "process", "variety"), ("band", "variety"), ("band", "process"), ("variety",), ("band", "prep"), ("band",), ("process",), ("prep",), ()]
    members: dict[str, list[str]] = defaultdict(list)
    for e in cr:
        f = facets(e)
        for combo in PRIORITY:
            if all(f[k] for k in combo):
                members["|".join(f"{k}={f[k]}" for k in combo) or "all"].append(e)
    groups = {key: ids for key, ids in members.items() if len(ids) >= MIN_N}

    by_question: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in bank:
        by_question[r["question_id"]].append(r)

    def within(ids: list[str], options: list[dict[str, str]]) -> dict[str, float]:
        raw = {o["option_id"]: sum(1 for e in ids if concepts[e] & set(o["concepts"].split("|"))) if o["concepts"] else 0 for o in options}
        total = sum(raw.values()) or 1
        return {k: v / total for k, v in raw.items()}

    factors: dict[str, float] = {}
    for q in ("A", "B", "C"):
        data = [o for o in by_question[q] if o["role"] == "data"]
        a, b = within(comparable, data), within(coe, data)
        for o in data:
            factors[o["option_id"]] = max(0.33, min(3.0, (b[o["option_id"]] + 0.01) / (a[o["option_id"]] + 0.01)))

    def mean_body(ids: list[str]) -> float:
        values = [float(axes[e]["body_axis_percentile"]) for e in ids if axes[e]["body_axis_percentile"]]
        return sum(values) / len(values) if values else 0.5

    def parent_of(key: str) -> str:
        mine = set(key.split("|")) if key != "all" else set()
        best = "all"
        for other in groups:
            theirs = set(other.split("|")) if other != "all" else set()
            if other != key and theirs < mine and len(theirs) > (len(best.split("|")) if best != "all" else 0):
                best = other
        return best

    def shrunk(key: str, estimate, depth: int = 0):
        """estimate(ids) → {option: share}; a group's own shares pulled toward its parent's (itself shrunk), by size."""
        own = estimate(groups[key])
        if key == "all" or shrink <= 0 or depth > 4:
            return own
        up = shrunk(parent_of(key), estimate, depth + 1)
        weight = len(groups[key]) / (len(groups[key]) + shrink)
        return {k: weight * own[k] + (1 - weight) * up.get(k, 0.0) for k in own}

    out_groups: dict[str, dict] = {}
    review_rows: list[list] = []
    for key, ids in sorted(groups.items()):
        keep: dict[str, list[str]] = {}
        shares: dict[str, dict[str, float]] = {}
        for q in ("A", "B", "C"):
            options = by_question[q]
            data = [o for o in options if o["role"] == "data"]
            w = shrunk(key, lambda members, data=data: within(members, data))
            adjusted = {k: math.sqrt(v * v * factors[k]) for k, v in w.items()}
            total = sum(adjusted.values()) or 1
            adjusted = {k: v / total for k, v in adjusted.items()}
            shares[q] = {k: round(v, 4) for k, v in adjusted.items()}
            slots = KEEP_BY_QUESTION.get(q, KEEP) - sum(1 for o in options if o["role"] == "always")
            light = key.startswith("band=light") or key == "all"
            fixed = [o["option_id"] for o in options if o["role"] == "default_light" and light]
            ranked = sorted(data, key=lambda o: (-adjusted[o["option_id"]], int(o["position"])))
            chosen = {o["option_id"] for o in ranked[: slots - len(fixed)]} | set(fixed) | {o["option_id"] for o in options if o["role"] == "always"}
            keep[q] = [o["option_id"] for o in options if o["option_id"] in chosen]  # the pool's order, never the ranking
        body = mean_body(ids)  # kept for the record only, see MOUTHFEEL_WINDOWS
        # second level: the words of each family, the ones with corpus support first, three at most; and the examples
        second: dict[str, list[str]] = {}
        for parent in sorted({o["parent_option"] for o in by_question["S"]}):
            words = [o for o in by_question["S"] if o["parent_option"] == parent]
            def word_shares(members, words=words):
                raw = {o["option_id"]: (sum(1 for e in members if o["concepts"] in concepts[e]) if o["concepts"] else 0) for o in words}
                total = sum(raw.values()) or 1
                return {k: v / total for k, v in raw.items()}
            count = shrunk(key, word_shares)
            ranked = sorted(words, key=lambda o: (-count[o["option_id"]], int(o["position"])))[:SECOND_KEEP]
            second[parent] = [o["option_id"] for o in ranked]  # the first three become the option's examples; the app shows them in the pool's order
        # aroma and aftertaste, within this group's own roast band only
        levels = [structure[e] for e in ids if e in structure]
        aroma = [r["aroma_level"] for r in levels if r["aroma_level"]]
        after = [r["aftertaste_level"] for r in levels if r["aftertaste_level"]]
        review_rows.extend([key, len(ids), q, k, f"{v:.4f}", "kept" if k in keep[q] else ""] for q, table in shares.items() for k, v in table.items())
        out_groups[key] = {"n": len(ids), "keep": keep, "second": second, "body_percentile_mean": round(body, 3),
                           "aroma_high": round(sum(x == "high" for x in aroma) / len(aroma), 3) if aroma else None,
                           "aftertaste_high": round(sum(x == "high" for x in after) / len(after), 3) if after else None,
                           "aftertaste_low": round(sum(x == "low" for x in after) / len(after), 3) if after else None}

    options_out: dict[str, list[dict]] = defaultdict(list)
    for r in bank:
        zh, en = r["label_zh_cn"].split(SEP), r["label_en"].split(SEP)
        assert len(zh) == len(en), r["option_id"]
        options_out[r["question_id"]].append({"id": r["option_id"], "parent": r["parent_option"], "role": r["role"], "label": {"zh-CN": zh, "en": en}, "deltas": parse_deltas(r["deltas"]),
                                              "focus": r["focus"], "card_row": {"zh-CN": r["card_row_zh_cn"], "en": r["card_row_en"]} if r["card_row_zh_cn"] else None,
                                              "lead_in": {"zh-CN": r["lead_in_zh_cn"], "en": r["lead_in_en"]} if r.get("lead_in_zh_cn") else None,
                                              "short": {"zh-CN": r["short_zh_cn"], "en": r["short_en"]} if r.get("short_zh_cn") else None})
    build = {"version": "dynamic-question-bank-v1", "max_options": MAX_TAPPABLE, "tappable": TAPPABLE, "scale_windows": SCALE_WINDOWS, "strong_correction_full_scale": ["E3"], "min_group_n": MIN_N, "group_priority": [list(c) for c in PRIORITY],
             "roast_band": {"light": "light", "medium_light": "light", "medium": "medium", "medium_dark": "dark", "dark": "dark"},
             "espresso_preparations": ["espresso", "americano", "milk_coffee", "moka_pot"],
             # Mouthfeel is a scale, and it is NOT pruned by the corpus: the reviewers' Body score is a quality score too (lighter
             # roasts score higher), which would give dark espresso the thin end of the scale. The window follows the brewing
             # method instead — the operator's domain rule, for the owner's review. The drying option always shows.
             "mouthfeel_windows": {"heavy": {"preparations": ["espresso", "moka_pot", "milk_coffee", "turkish"], "keep": ["D2", "D3", "D5"]},
                                   "light": {"preparations": ["pour_over_v60", "drip_bag", "americano", "siphon", "cold_drip"], "keep": ["D6", "D1", "D5"]},
                                   "middle": {"preparations": ["french_press", "aeropress", "cold_brew"], "keep": ["D1", "D2", "D5"]}},
             "prompts": {p["question_id"]: {"kind": p["kind"], "zh-CN": p["prompt_zh_cn"], "en": p["prompt_en"],
                                            "tail": {"zh-CN": p["tail_zh_cn"], "en": p["tail_en"]} if p.get("tail_zh_cn") else None} for p in prompts},
             "options": options_out, "source_correction": {k: round(v, 3) for k, v in factors.items()}, "groups": out_groups,
             "shrinkage": shrink,
             "notes": ["a small group's shares are pulled toward its parent group's: weight n / (n + shrinkage)", "the corpus prunes the option pool, it does not sort it: `keep` lists the survivors in the pool's order", "aroma / aftertaste shares compare within one roast band only"]}
    out_path.write_text(json.dumps(build, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    if holdout:
        print(json.dumps({"holdout": len(holdout), "groups": len(out_groups), "out": str(out_path)}))
        return 0
    # the shares behind the pruning, for review; not shipped with the app
    with (PV / "DYNAMIC_OPTION_SHARES.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["group", "n", "question_id", "option_id", "within_question_share_corrected", "pruning"])
        w.writerows(review_rows)
    print(json.dumps({"groups": len(out_groups), "records": len(cr), "options": len(bank), "largest": sorted(((v["n"], k) for k, v in out_groups.items()), reverse=True)[:4]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
