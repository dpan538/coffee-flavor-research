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

## Per-source conventions (owner, 2026-09-12)

| file | focus | context binding |
|---|---|---|
| `wcr_sensory_lexicon.claims.csv` | chemical references and grading sentences for floral, fruity, acidity, sweetness | `C2_variety` (genetic ceiling) and `C1_roast` |
| `uc_davis_coffee_center.claims.csv` | grind – temperature – TDS – sensory map; extraction assertions ("hot fast extraction pulls polar acids", "fine grind amplifies large-molecule bitterness") | `C0_brew` |
| `coffee_ad_astra.claims.csv` | channeling, extraction yield vs mid-palate sweetness and late off-notes (`defect` / `bitter`) | `C0_brew` and `C0_brew__C1_roast` combinations via `context_parts` |

`context_axis` accepts the aliases `C0_brew`, `C1_roast`; a combination sentence sets `context_parts` (e.g. `C0:pour_over_v60|C1:light`).
Templates with the exact columns and example rows live in `templates/` (not ingested). The example claim texts there are placeholders,
not citations — replace them with sentences taken from the source.

## Declaration state (owner rule, R3-D14)

A claim row whose `source_locator` and `licence_note` are both filled ingests as `LITERATURE_CLAIM`. A row missing either ingests as
`LITERATURE_CLAIM_PENDING_LOCATOR`: it is still shown in the product with its source name, and the About page says the DOI / link is
pending. The ingest writes `db/data/product-vector-v1/LITERATURE_SOURCES.json` (one row per source: title, locator, licence note,
claim count, state) which the About page reads. The three current files carry the owner's core content (11 claims) with locator and
licence filled on 2026-09-12; edit a row and re-run `ingest-external-literature.py`.

`review_state` / `review_note` (optional columns, owner copy review 2026-09-12): a row marked `NEEDS_REVERIFICATION` is ingested as
`LITERATURE_CLAIM_NEEDS_REVERIFICATION` — declared in the data and counted on the About page as "held back until re-verified", but never shown
in the product. Use it when an external check finds that the cited source does not support the sentence (the WCR Gesha claim, the two UC Davis
extraction-order claims); clear it once a supporting source is added or the sentence is rewritten.

`use_note` (optional column, copy review 2, 2026-09-12): how this project uses the source, kept apart from the source's own
terms (`licence_note`). Both reach the About page as separate fields ("来源条款" / "本项目的使用").

UC Davis (2026-09-12): the DOI on file, 10.1016/j.foodchem.2020.126567, resolves to a turmeric-powder authentication paper,
not a coffee study. All four rows carry `NEEDS_REVERIFICATION` with an empty locator; the source is not shown to readers until
the owner re-establishes it from the paper actually read.
