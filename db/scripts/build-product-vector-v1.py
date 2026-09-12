#!/usr/bin/env python3
"""Product vector v1 (design pivot 2026-09-12): project the 83K corpus into the
12-dimension flavor space (owner D-open-1), replace the body / acidity axes of
CoffeeReview coffees with their editorial 1-10 scores as rank percentiles (owner
D-open-3), cut data-driven flavor profiles (owner D-open-2: profile-first output),
and measure the owner's four sufficiency criteria.

Inputs : db/data/current/CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv (canonical_concept_ids per assertion)
         db/data/product-vector-v1/CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv (concept -> 12 dims, owner-reviewable)
         db/data/product-vector-v1/COFFEEREVIEW_STRUCTURE_AXES.tsv (body / acidity rank percentiles, from extract-coffeereview-structure-scores.py)
Outputs: db/data/product-vector-v1/COFFEE_VECTOR_LIBRARY.tsv   one row per coffee (effective record): 12 dims, support, rights
         db/data/product-vector-v1/FLAVOR_PROFILE_LIBRARY.tsv   k-means profiles over the usable vectors (centroids, members, top dims); names are the owner's
         db/data/product-vector-v1/PRODUCT_VECTOR_V1_MEASUREMENT.json  coverage, uniformity, query-horizon test
No training, no weights: a projection matrix, a set of vectors and a cosine.
"""
from __future__ import annotations
import csv, json, math, itertools
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
OUT = ROOT / "db" / "data" / "product-vector-v1"
DIMS = ["acidity", "sweetness", "body", "floral", "fruity", "nutty_chocolate", "fermented_winey", "bitter_roasted",
        "spice", "herbal_green", "woody_earthy", "defect"]
N = len(DIMS)
PROFILE_K = 16
# rights per family for the *product candidate library*: research-only sources may calibrate
# and validate, but are not recommendable items in a public product without an owner decision.
RESEARCH_ONLY = {"family.coffeereview_kaggle_parsed"}
# Q5-Q10 option increments exactly as specified by the owner (2026-09-12)
QUESTIONS = {
    "Q5_acid": {"A": {"acidity": 2, "fruity": 1}, "B": {"acidity": 1, "fermented_winey": 2}, "C": {"body": 1}},
    "Q6_sweet": {"A": {"floral": 1, "sweetness": 2}, "B": {"nutty_chocolate": 2, "bitter_roasted": 1}, "C": {"fruity": 2, "sweetness": 2}},
    "Q7_body": {"A": {"body": 1}, "B": {"body": 2}, "C": {"body": 3, "bitter_roasted": 1}},
    "Q8_aroma": {"A": {"floral": 3}, "B": {"nutty_chocolate": 3}, "C": {"fermented_winey": 2, "fruity": 2}},
    "Q9_bitter": {"A": {"nutty_chocolate": 1, "bitter_roasted": 1}, "B": {}},
    "Q10_clean": {"A": {"floral": 1, "acidity": 1}, "B": {"fermented_winey": 1, "body": 1}},
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def cosine(a: list[float], b: list[float]) -> float:
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def main() -> int:
    proj = {r["canonical_concept_id"]: [float(r[d]) for d in DIMS] for r in rows(OUT / "CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv")}
    mapped = {c for c, v in proj.items() if any(v)}
    axes_path = OUT / "COFFEEREVIEW_STRUCTURE_AXES.tsv"
    structure = {r["effective_record_id"]: r for r in rows(axes_path)} if axes_path.is_file() else {}
    coffees: dict[str, dict] = {}
    for r in rows(CURRENT / "CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv"):
        c = coffees.setdefault(r["effective_record_id"], {"family": r["source_family_id"], "year": r["year_id"], "prep": r["preparation_service_id"], "assertions": 0, "mapped": 0, "vec": [0.0] * N, "concepts": Counter()})
        c["assertions"] += 1
        for cid in r["canonical_concept_ids"].split("|"):
            if cid in mapped:
                c["mapped"] += 1
                c["concepts"][cid] += 1
                for i, wgt in enumerate(proj[cid]):
                    c["vec"][i] += wgt
    lib = []
    structure_used = 0
    for rid, c in sorted(coffees.items()):
        # descriptor axes: scale so the strongest descriptor axis of the coffee is 1
        peak = max(c["vec"]) if any(c["vec"]) else 0.0
        vec = [x / peak for x in c["vec"]] if peak else [0.0] * N
        basis = "DESCRIPTORS_ONLY"
        st = structure.get(rid)
        if st and (st["body_axis_percentile"] or st["acidity_axis_percentile"]):
            # owner D-open-3: editorial scores replace the under-reported structure axes
            if st["body_axis_percentile"]:
                vec[DIMS.index("body")] = float(st["body_axis_percentile"])
            if st["acidity_axis_percentile"]:
                vec[DIMS.index("acidity")] = max(vec[DIMS.index("acidity")], float(st["acidity_axis_percentile"]))
            basis = "DESCRIPTORS+COFFEEREVIEW_STRUCTURE_SCORES"
            structure_used += 1
        norm = math.sqrt(sum(x * x for x in vec))
        unit = [x / norm for x in vec] if norm else [0.0] * N
        mapped_mentions = c["mapped"] + (2 if basis != "DESCRIPTORS_ONLY" else 0)
        lib.append({"effective_record_id": rid, "source_family_id": c["family"], "year_id": c["year"], "preparation_service_id": c["prep"],
                    "assertion_count": c["assertions"], "mapped_concept_mentions": c["mapped"], "distinct_mapped_concepts": len(c["concepts"]),
                    **{f"v_{d}": f"{u:.4f}" for d, u in zip(DIMS, unit)},
                    "axis_basis": basis,
                    "vector_state": "USABLE" if mapped_mentions >= 2 else ("THIN" if mapped_mentions == 1 else "EMPTY"),
                    "product_candidate_rights": "RESEARCH_ONLY_NOT_RECOMMENDABLE" if c["family"] in RESEARCH_ONLY else "PUBLIC_RECORD_RIGHTS_UNRESOLVED",
                    "projection_basis": "CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv (owner review pending)"})
    with (OUT / "COFFEE_VECTOR_LIBRARY.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lib[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(lib)

    usable = [c for c in lib if c["vector_state"] == "USABLE"]
    vecs = [[float(c[f"v_{d}"]) for d in DIMS] for c in usable]
    # uniformity: how many usable coffees have each dimension as their top axis, and per-axis mass
    top_axis = Counter(DIMS[max(range(N), key=lambda i: v[i])] for v in vecs)
    axis_mass = {d: round(sum(v[i] for v in vecs) / len(vecs), 4) for i, d in enumerate(DIMS)}
    # query horizon: every Q5-Q10 answer combination -> V_user -> top-3 by cosine
    combos = list(itertools.product(*[list(q.keys()) for q in QUESTIONS.values()]))
    sims, distinct_ok, hits85 = [], 0, 0
    top3_pool: Counter[str] = Counter()
    for combo in combos:
        u = [0.0] * N  # Q5-Q10 only move the first 8 axes; spice/herbal/woody/defect stay 0 (defect > 0 in a bean lowers its cosine)
        for (qid, opts), a in zip(QUESTIONS.items(), combo):
            for d, inc in opts[a].items():
                u[DIMS.index(d)] += inc
        scored = sorted(((cosine(u, v), i) for i, v in enumerate(vecs)), reverse=True)[:3]
        sims.append(scored[0][0])
        if all(s > 0.85 for s, _ in scored):
            hits85 += 1
        ids = [usable[i]["effective_record_id"] for _, i in scored]
        if len(set(ids)) == 3:
            distinct_ok += 1
        top3_pool.update(ids)
    # owner D-open-2: profile-first output. Deterministic k-means (farthest-point seeding from the
    # first usable vector, 25 iterations) over the usable unit vectors; names are the owner's.
    def dist2(a, b):
        return sum((x - y) ** 2 for x, y in zip(a, b))
    centroids = [vecs[0]]
    while len(centroids) < PROFILE_K:
        far = max(range(len(vecs)), key=lambda i: min(dist2(vecs[i], c) for c in centroids))
        centroids.append(vecs[far])
    assign = [0] * len(vecs)
    for _ in range(25):
        assign = [min(range(PROFILE_K), key=lambda k: dist2(v, centroids[k])) for v in vecs]
        for k in range(PROFILE_K):
            members = [v for v, a in zip(vecs, assign) if a == k]
            if members:
                mean = [sum(col) / len(members) for col in zip(*members)]
                nm = math.sqrt(sum(x * x for x in mean)) or 1.0
                centroids[k] = [x / nm for x in mean]
    profiles = []
    for k in range(PROFILE_K):
        idx = [i for i, a in enumerate(assign) if a == k]
        cen = centroids[k]
        top = sorted(range(N), key=lambda i: -cen[i])[:3]
        fam = Counter(usable[i]["source_family_id"] for i in idx)
        profiles.append({"profile_id": f"profile-v1:{k:02d}", "member_count": len(idx), "member_share": f"{len(idx) / len(vecs):.3f}",
                         "top_dimensions": "|".join(f"{DIMS[i]}={cen[i]:.2f}" for i in top),
                         **{f"c_{d}": f"{x:.4f}" for d, x in zip(DIMS, cen)},
                         "family_mix": "|".join(f"{f.removeprefix('family.')}={n}" for f, n in fam.most_common(3)),
                         "mean_defect_axis": f"{sum(vecs[i][DIMS.index('defect')] for i in idx) / max(len(idx), 1):.4f}",
                         "owner_name_zh": "", "owner_name_en": "", "benchmark_beans": "", "owner_reviewed": "false"})
    profiles.sort(key=lambda p: -p["member_count"])
    with (OUT / "FLAVOR_PROFILE_LIBRARY.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(profiles[0]), delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(profiles)

    measurement = {
        "contract_version": "product-vector-v1.measurement.v2",
        "design": "docs/product/FLAVOR_VECTOR_DESIGN_V1.md",
        "corpus": "CLEANED_83K_SOURCE_ASSERTION_LEDGER.tsv",
        "dimensions": DIMS,
        "projection": {"concepts": len(proj), "with_nonzero_projection": len(mapped), "owner_reviewed": False},
        "structure_axes": {"coffees_with_coffeereview_scores": structure_used, "basis": "body / acidity rank percentile of CoffeeReview editorial 1-10 scores (owner D-open-3)"},
        "profiles": {"k": PROFILE_K, "member_counts": [p["member_count"] for p in profiles], "top_dimensions": [p["top_dimensions"] for p in profiles]},
        "coverage": {"coffees": len(lib), "usable_(>=2 mapped mentions)": len(usable), "thin_(1)": sum(c["vector_state"] == "THIN" for c in lib), "empty_(0)": sum(c["vector_state"] == "EMPTY" for c in lib),
                     "usable_by_family": dict(Counter(c["source_family_id"] for c in usable)),
                     "usable_recommendable_in_public_product": sum(c["product_candidate_rights"] != "RESEARCH_ONLY_NOT_RECOMMENDABLE" for c in usable),
                     "mean_distinct_mapped_concepts_per_usable_coffee": round(sum(c["distinct_mapped_concepts"] for c in usable) / len(usable), 2)},
        "uniformity": {"top_axis_share": {d: round(n / len(vecs), 3) for d, n in top_axis.most_common()}, "mean_unit_mass_per_axis": axis_mass,
                       "reading": "axes with a near-zero top-axis share are long-tail regions the corpus barely describes in this projection"},
        "query_horizon_test": {"simulated_users": len(combos), "top1_similarity_mean": round(sum(sims) / len(sims), 4), "top1_similarity_min": round(min(sims), 4),
                               "users_with_top3_all_above_0.85": hits85, "users_with_3_distinct_top3": distinct_ok,
                               "distinct_coffees_appearing_in_any_top3": len(top3_pool), "most_recommended_coffee_hits": top3_pool.most_common(1)[0][1],
                               "reading": "owner criterion: every simulated user finds >0.85 and non-repeating candidates"},
        "not_yet_measured": ["profile names / benchmark beans: owner's (FLAVOR_PROFILE_LIBRARY owner_* columns)",
                              "C2 (variety x processing) sparsity: not extractable from the current ledgers; needs a targeted extraction from the CoffeeReview text and an approved WCR/processing source",
                              "V_pred / Matrix_K: not built; needs owner decision on the physics table's evidence basis"],
    }
    (OUT / "PRODUCT_VECTOR_V1_MEASUREMENT.json").write_text(json.dumps(measurement, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: measurement[k] for k in ("coverage", "structure_axes", "uniformity", "query_horizon_test", "profiles")}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
