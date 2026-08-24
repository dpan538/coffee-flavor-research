# Round 2B corpus inventory

Date: 2026-08-24

Corpus version: `firstbloom-a6cb002-pilot-v1`

Status: frozen, historical language-observation pilot

## Identity and receipts

| Item                                   | Frozen value                                                       |
| -------------------------------------- | ------------------------------------------------------------------ |
| Round 2A source SHA                    | `2d864d56496c587cff5b6774e0ea41be8b416e6c`                         |
| Corpus-generation code commit          | `d90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0`                         |
| Pinned Firstbloom SHA                  | `a6cb0026d1af9642724793c799bbc48dc189ba35`                         |
| Generated seed SHA-256                 | `955fecba967cee169f24e7c81b5d350d0e34902019af729cb3cf6558e0d96042` |
| Source inventory SHA-256               | `ce659e34c1f96b457789f720692e214b0ad5b021bf409c769cfc0df874036bda` |
| Document inventory SHA-256             | `75132e0bda01641cef8a1ad042ac1d5d313df894383617822c557c32578e2c53` |
| Normalization input inventory SHA-256  | `792ed3e77f7975c92b6feb8de0124cc047245c2d2640280913a8a94ef16e18c7` |
| Normalization output inventory SHA-256 | `301c45168413d1cf281f7c5a927bbc0e8ce57910dc68bf0cb07ec5ef8a845d76` |

The complete artifact-hash map is in the
[generation receipt](../../../db/data/round2b/generation_receipt.json). The
[generated migration](../../../db/015_round2b_pilot_seed.sql) is deterministic
and was reproduced byte-for-byte twice before database validation.

## Frozen counts

| Entity or observation class            | Count |
| -------------------------------------- | ----: |
| Reviewed source policies               |    15 |
| Acquired corpus sources                |     1 |
| Industry publishers                    |   215 |
| Industry products                      | 2,383 |
| Captured historical release documents  | 2,474 |
| Parsed raw observations                | 6,818 |
| Retained short observation occurrences | 5,564 |
| Hash-only observation occurrences      | 1,254 |
| Unique retained raw expressions        | 2,124 |
| Observed lexical-expression identities | 1,716 |
| Unique normalized expressions          | 1,713 |
| Frequency rows                         | 1,713 |
| Document-level co-occurrence pairs     | 4,600 |
| Duplicate-review rows                  |   129 |
| Acquisition diagnostic rows            |    80 |

“Raw observation” here means a delimiter-derived fragment plus its source hash
and offsets. It does not mean a stored complete tasting-note field. Of 6,818
fragment occurrences, 5,564 retain a short admitted surface and 1,254 retain
only a hash and exclusion reason. The repository contains no complete
tasting-note strings, roaster descriptions, or consumer-review text.

The source-controlled inventories are:

- [publishers](../../../db/data/round2b/pilot_publishers.tsv)
- [products](../../../db/data/round2b/pilot_products.tsv)
- [documents](../../../db/data/round2b/pilot_inventory.tsv)
- [observations](../../../db/data/round2b/pilot_observations.tsv)
- [lexical expressions](../../../db/data/round2b/pilot_expressions.tsv)
- [frequency measurements](../../../db/data/round2b/pilot_expression_statistics.tsv)
- [co-occurrence measurements](../../../db/data/round2b/pilot_cooccurrence.tsv)
- [duplicate reviews](../../../db/data/round2b/pilot_duplicate_reviews.tsv)
- [staged diagnostics](../../../db/data/round2b/pilot_diagnostics.json)

## Raw and normalized separation

Each captured document stores stable source identifiers, listing/capture
metadata when explicit, content and metadata hashes, and structured source
metadata. The document `raw_text` column is `NULL`. Each parsed observation
stores a SHA-256 digest, Unicode character count, zero-based half-open source
offsets, and either:

- `derived_phrase`: a short English surface admitted by the dual-review and
  structural policy; or
- `hash_only`: no surface text, with a controlled exclusion reason.

Retained observations resolve to observed `kb.lexical_expression` rows. This is
lexical admission only: an observed industry expression does not become a
canonical concept or a sensory assertion. The 1,716 observed lexical identities
collapse to 1,713 normalized identities under the three approved whole-phrase
orthographic rules.

## Duplicate and history handling

All 129 duplicate candidates were explicitly reviewed. Ninety-six candidates
were identified by publisher plus external product key, and 33 by content hash.
Historical releases remain distinct documents; a later release does not
overwrite an earlier capture. Product identity and document-snapshot identity
are therefore deliberately separate.

## Public reproducibility boundary

Schema, generated data, and statistics can be regenerated from the separately
obtained pinned CC BY 4.0 checkout, the source-controlled generator, the
hash-only admission inventory, and the recorded hashes. They cannot be rebuilt
from this repository alone because the repository intentionally does not vendor
complete tasting notes, rejected review phrases, descriptions, or consumer
reviews. Accordingly, the frozen snapshot records
`raw_public_reproducibility_complete=false`.
