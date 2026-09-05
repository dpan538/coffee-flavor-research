# Product gap source-route audit v0.2

Reviewed on **2026-09-05** in the restored research worktree. This is an assistant-authored source-route audit, **not user evidence, owner approval, expert validation, or a dataset import**.

The bounded audit reviewed **8 existing candidate routes**, recorded **5 product evidence gaps**, imported **0 datasets**, and added **0 observations**. The import receipt deliberately contains only its header. All five gaps remain open. No C1 mapping, context prior, professional support count, inference score, or deployment/training authorization changes follow from this audit.

## Inputs and scope

- `../product-inference-v0/PRODUCT_INFERENCE_MANIFEST.json`: existing route candidates.
- `../round3h/source_candidate_register.tsv`: existing rights and acquisition decisions.
- `../product-inference-v0/PRODUCT_TASK_CONTRACT.json`: context, question and rights boundaries.
- Existing round3h batch manifests were consulted for lineage, without recopying their datasets.

Only C0 method comparison, C1 seven-level mapping, observed joint C0 × C1 structure, CATA/RATA bounded negatives, and descriptor salience/axis contrast were reviewed. Searches were limited to the eight selected papers and their publisher, author-institution or official deposit routes. Incidental search hits were not admitted as candidate routes. No broad catalog crawl, author contact, source-data download, instrument reproduction or source import was performed. PDF content was read through the web tool only to verify the cited paper; the unrelated database-course PDF and questionnaire submissions are outside this audit.

## Reading the files

`PRODUCT_GAP_SOURCE_CANDIDATE.tsv` has one row per source route. It records primary URLs, review date, evidence locator, authors, license verification granularity, attribution, modification status, availability, limitations and decisions. `PRODUCT_GAP_REGISTER.tsv` defines the five gaps and links their routes. `PRODUCT_GAP_IMPORT_RECEIPT.tsv` is empty by design.

Some direct fulltext routes returned rate limits, browser checks or fetch failures. Publisher-indexed source content or author-institution metadata could verify selected claims; these are explicitly distinguished from freshly opened fulltext and from inherited manifest facts. A review date does not guarantee the web index was crawled that day. Inaccessible dataset files remain unverified. Advertised file availability, an article license and an expected repository license are separate facts. No unknown exact license is promoted to clearance.

## Evidence boundaries

C1 remains neutral until a separately reviewed mapping identifies source metric, bean/ground measurement basis where available, instrument, thresholds and uncertainty. Source labels do not fill missing roast bins. Joint evidence requires actual observed cells; cross-products of marginal coverage remain prohibited.

CATA/RATA nonselection requires a known presented set, valid denominator and missingness policy. It is never a general absence label. Aggregate intensity, hedonic dislike, quality score and unreported attributes remain separate. Consumer studies remain consumer/instrument evidence and do not become professional candidate support. A paper demonstrating sensory differences does not validate user comprehension or project question usefulness.

Batali and Liang share the UC Davis research ecosystem; separate DOIs do not justify treating them as fully independent institutional replication. Rights remain scoped to the existing research workflow. Article access does not authorize deployment, training, or reuse of separately credited vocabulary, standards and forms.

## Verification

Local TSV checks confirm 8 unique route IDs, 5 unique gap IDs, valid route/gap cross-references, 0 import receipt rows and zero declared imports/observations. No source hashes were generated because there was no acquisition. The parent audit owns the final directory-level `SHA256SUMS`.
