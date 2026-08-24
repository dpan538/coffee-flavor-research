# Round 2B sampling frame

Date: 2026-08-24

Corpus version: `firstbloom-a6cb002-pilot-v1`

## Frame design

The pilot is a deterministic, publisher-balanced sample from the pinned
[Firstbloom Data](https://github.com/alexcaza/firstbloom-data) repository at
`a6cb0026d1af9642724793c799bbc48dc189ba35`. It is a historical secondary
aggregation, not a live-roaster scrape.

The eligible frame contains every Firstbloom publisher with at least one
release whose roaster tasting-note field is explicit and nonempty. Each batch
selects the next release for each publisher under a deterministic SHA-256 rank,
so a publisher contributes at most one release per batch. No missing country,
publisher size, process, or product metadata was inferred to manufacture
strata.

The source-controlled frame hash is
`3da254bf0ab64e73e532aad31125ab51050b0f56556eb6e6a0025377db25d7cf`.
The governing records are seeded in
[migration 015](../../../db/015_round2b_pilot_seed.sql), and the source hashes,
selection receipt, and stopping rule are recorded in the
[generation receipt](../../../db/data/round2b/generation_receipt.json).

## Captured frame

| Measure                      |                  Frozen value |
| ---------------------------- | ----------------------------: |
| Acquired licensed datasets   |                             1 |
| Industry publishers          |                           215 |
| Industry products            |                         2,383 |
| Historical release documents |                         2,474 |
| Acquisition batches          |                            16 |
| Source listing-date range    | 2017-12-29 through 2021-01-13 |
| Contract capture timestamp   |       2026-08-24 00:00:00 UTC |

The 16 batch document counts are `215, 203, 200, 195, 190, 182, 173, 159,
149, 130, 125, 121, 115, 110, 107, 100`. The difference between 2,383 products
and 2,474 documents preserves historical releases rather than overwriting an
older observation.

## Explicit metadata coverage

The sample spans 36 explicit Firstbloom coffee-origin source codes. These are
source metadata and are not asserted to be ISO identifiers. Multi-country
documents count once under each explicit code. `ET` has the largest final
document share at `0.2158447858`; this is coffee-origin metadata, not roaster
geography.

Explicit process metadata is present on 2,198 documents. Selected process
counts are:

| Source process label   | Documents |
| ---------------------- | --------: |
| Wet/Washed             |     1,536 |
| Dry/Natural            |       433 |
| Honey                  |        73 |
| Anaerobic Fermentation |        37 |

These counts can overlap because a document may carry more than one explicit
process label. They demonstrate pilot coverage; they do not establish balanced
process strata or sensory outcomes.

Publisher concentration is low under the frame: the largest publisher share is
`0.0064672595`, and the publisher-document Herfindahl-Hirschman index is
`0.0055539617`. Roaster country and publisher size are absent in the source and
remain unassessed rather than inferred.

## Staged stopping decision

The pilot stopped after batch 16 as a bounded baseline, not because vocabulary
discovery had converged:

- the top-25 normalized-expression set overlapped 25 of 25 with batch 15;
- the top-100 set overlapped 98 of 100 with batch 15;
- fixed-seed document-bootstrap top-five-neighbour median Jaccard was `3/7`
  (`0.4285714286`) for batches 14, 15, and 16;
- final bootstrap mean Jaccard was only `0.3686790531`;
- batch 16 still introduced 48 normalized expressions.

High-frequency rank stability was therefore strong, while vocabulary discovery
and co-occurrence-neighbour stability remained incomplete. Another acquisition
round could be informative only if an additional source passes a fresh rights
review.

## Representativeness statement

This corpus is not globally or currently representative. It contains one
licensed historical repository snapshot, even though that snapshot names 215
publishers and many coffee origins. No claim is made about present-day
offerings, global roaster prevalence, country prevalence, market share, or the
objective sensory properties of coffee.
