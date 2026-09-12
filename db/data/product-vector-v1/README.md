# product-vector-v1

Design: `docs/product/FLAVOR_VECTOR_DESIGN_V1.md`. Builders, in order: `extract-coffeereview-structure-scores.py` and `extract-coffeereview-c2-labels.py` (need the restricted root), then `build-product-vector-v1.py`, then `build-matrix-k-v1.py` (all deterministic; no training).

| File | What |
|---|---|
| `CONCEPT_DIMENSION_PROJECTION_DRAFT.tsv` | 94 canonical concepts → 12 dimensions (R3-D6). **Operator draft; `owner_reviewed=false` until the owner has gone through it.** `coverage_state_8d` keeps the diagnosis that forced the 4 extra dimensions. |
| `COFFEEREVIEW_STRUCTURE_AXES.tsv` | Body / acidity rank percentiles of CoffeeReview's editorial 1-10 scores, keyed by effective_record_id (R3-D6). Raw scores stay in the restricted root. |
| `COFFEEREVIEW_C2_LABELS.tsv` | Variety / process labels per CoffeeReview review from a keyword lexicon over the review text (Step 3); categorical only, no text. |
| `MATRIX_K.tsv`, `MATRIX_K_C0_C1_CELLS.tsv` | Matrix_K measured from the corpus (Step 2): C0, C1, C2 variety (n>=50), C2 process (n>=30) rows and the joint C0 x C1 cells with sufficiency. |
| `product-vector-v1.json` | Runtime bundle consumed by `packages/flavor-data/src/product-vector-v1`: dimensions, projection, Matrix_K, Matrix_Q, profiles, alpha, weights. |
| `FLAVOR_PROFILE_LIBRARY.tsv` | 16 deterministic k-means profiles over the usable vectors: centroid, members, top dimensions, family mix, defect mean. `owner_name_zh/en` and `benchmark_beans` are the owner's to fill. |
| `COFFEE_VECTOR_LIBRARY.tsv` | One row per coffee (effective record) in the 83K corpus: 12-dimension unit vector, `axis_basis`, support counts, `vector_state` (USABLE / THIN / EMPTY), `product_candidate_rights`. CoffeeReview rows are RESEARCH_ONLY_NOT_RECOMMENDABLE (R3-D2). |
| `PRODUCT_VECTOR_V1_MEASUREMENT.json` | The owner's four sufficiency criteria measured on the library: coverage, uniformity, query-horizon test; and what is not yet measurable. |

Rights: this directory contains no source text; vectors are derived from public-safe canonical concept ids. Recommending a
CoffeeReview coffee in a public product is not covered by R3-D2.
