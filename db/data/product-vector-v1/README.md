# product-vector-v1

Design: `docs/product/FLAVOR_VECTOR_DESIGN_V1.md`. Builders: `db/scripts/extract-coffeereview-structure-scores.py` (restricted root) then `db/scripts/build-product-vector-v1.py` (deterministic; no training).

| File | What |
|---|---|
| `CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv` | 94 canonical concepts → 12 dimensions (R3-D6). **Operator draft; `owner_reviewed=false` until the owner has gone through it.** `coverage_state_8d` keeps the diagnosis that forced the 4 extra dimensions. |
| `COFFEEREVIEW_STRUCTURE_AXES.tsv` | Body / acidity rank percentiles of CoffeeReview's editorial 1-10 scores, keyed by effective_record_id (R3-D6). Raw scores stay in the restricted root. |
| `FLAVOR_PROFILE_LIBRARY.tsv` | 16 deterministic k-means profiles over the usable vectors: centroid, members, top dimensions, family mix, defect mean. `owner_name_zh/en` and `benchmark_beans` are the owner's to fill. |
| `COFFEE_VECTOR_LIBRARY.tsv` | One row per coffee (effective record) in the 83K corpus: 12-dimension unit vector, `axis_basis`, support counts, `vector_state` (USABLE / THIN / EMPTY), `product_candidate_rights`. CoffeeReview rows are RESEARCH_ONLY_NOT_RECOMMENDABLE (R3-D2). |
| `PRODUCT_VECTOR_V1_MEASUREMENT.json` | The owner's four sufficiency criteria measured on the library: coverage, uniformity, query-horizon test; and what is not yet measurable. |

Rights: this directory contains no source text; vectors are derived from public-safe canonical concept ids. Recommending a
CoffeeReview coffee in a public product is not covered by R3-D2.
