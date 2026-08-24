# Context data source review

## Rights gate

Dryad states that data published through its repository are released under
CC0; the exact dataset/version metadata and file hashes were checked before
import. CC0 permits commercial use, derivatives, redistribution, and machine
processing. The repository still records attribution and provenance even
where the legal instrument does not require it. See the [Dryad terms of
service](https://datadryad.org/stash/terms).

## Reviewed candidates

- [10.25338/B8993H](https://datadryad.org/dataset/doi:10.25338/B8993H):
  Dryad version ID 215645, version 4, published 2023-01-16, CC0-1.0. Imported
  files are a 3,186-row/48-column consumer black-coffee dataset and its README.
- [10.25338/B8C91C](https://datadryad.org/dataset/doi:10.25338/B8C91C):
  Dryad version ID 130006, version 5, published 2021-07-14, CC0-1.0. The correct
  dataset attribution is Sara Yeager (2021); four files were frozen and 1,631
  chemistry rows were imported. This is a forward correction of project
  metadata, not an edit to Round 3A history.
- `10.5061/dryad.v15dv423h`: not imported. On 2026-08-25 the Dryad API did not
  expose a viewable version, files, or a version-specific license record. The
  candidate is retained as an inaccessible review record with zero files and
  zero imported rows.

The authoritative machine-readable inventory is
[`SOURCE_MANIFEST.json`](../../../db/data/round3b/raw/SOURCE_MANIFEST.json).
Exact source bytes are frozen under `db/data/round3b/raw/`; the six committed
hashes are rechecked by `db/scripts/freeze-round3b-context.py`.
