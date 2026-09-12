# external-literature

Owner-approved literature for the attribution layer (R3-D7): WCR Varieties Catalog, UC Davis Coffee Center, Coffee Ad Astra (Gagné).
Per the per-dataset rule, the owner places the material here after their own review; nothing is fetched automatically.

## What to drop here

One CSV (UTF-8, comma-separated) per source, name `<source_id>.claims.csv`, one row per claim:

| column | meaning |
|---|---|
| `source_id` | short id, e.g. `wcr_varieties_2024` |
| `source_title` | full title |
| `source_locator` | URL / DOI / page reference |
| `licence_note` | what the owner checked (e.g. "CC BY 4.0", "personal research use, no redistribution") |
| `context_axis` | `C0`, `C1`, `C2_variety`, `C2_process`, or `GENERAL` |
| `option` | the product option the claim is about (`espresso`, `light`, `gesha`, `washed`, …) or blank |
| `dimension_effects` | optional, `acidity:-0.3|body:+0.4` — signed effects on the 12 dimensions, for a future literature-based K row |
| `claim_zh_cn` | one sentence, product-level wording |
| `claim_en` | one sentence |

Markdown notes are also accepted (`<source_id>.md`) and stay as reading material; only CSV rows become claims.

## What happens

`db/scripts/ingest-external-literature.py` reads every `*.claims.csv`, validates the columns, and writes
`db/data/product-vector-v1/LITERATURE_CLAIMS.tsv` with `evidence_state=LITERATURE_CLAIM`. `build-matrix-k-v1.py` merges
these with the owner's own sentences (`CONTEXT_STATEMENTS_OWNER.tsv`, `evidence_state=OWNER_STATEMENT`) into the runtime
bundle's `presentation.context_statements`, so the attribution text can cite its evidence state.

Raw PDFs or full text of third-party sources do not belong in git; keep them under the restricted root and point to them
from `source_locator`.
