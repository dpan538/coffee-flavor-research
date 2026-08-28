# Round 3L public aggregate checkpoint

This directory is the public-safe audit surface for the Round 3L professional
competition acquisition snapshot. The full record and assertion ledgers remain
under `restricted_lanes/` and `restricted_ingest/` in an owner-controlled root
outside the repository; they are intentionally not tracked in Git while source
rights are pending or unknown.

The public files contain only aggregate metrics, acquisition-attempt metadata,
blocker states, deterministic continuation cursors, artifact URLs with SHA-256
and byte counts, and hashes of the restricted ledgers. They contain no
professional record rows, assertion rows, participant/company/product result
fields, score values or score text, source-native descriptors, or raw OCR.
Lawful official-route metadata is retained, including URLs whose slugs may
contain source-authored names.

## Files

- `PUBLIC_CHECKPOINT.json` is the standardized cumulative progress checkpoint.
- `LANE_METRICS.json` reports aggregate metrics and the exact resume cursor for
  each acquisition lane.
- `SOURCE_ATTEMPTS_PUBLIC.tsv` omits the restricted `evidence_json` and
  `blocker_detail` fields.
- `BLOCKER_QUEUE_PUBLIC.tsv` reports blocker state and continuation metadata;
  resolution evidence is reduced to a presence flag.
- `ARTIFACT_MANIFEST.tsv` lists only safe URL, hash, byte, status, and inventory
  metadata for acquired artifacts.
- `RESTRICTED_LEDGER_RECEIPT.json` provides deterministic hashes and byte/row
  counts for the restricted inputs without publishing their contents.
- `AUTHORITATIVE_GATE_RECEIPT.json` records the separately verified PostgreSQL
  query result from `audit.v_round3k_professional_corpus_metrics`. The builder
  never substitutes staging-derived zeroes for that authoritative query.

## Gate interpretation

The 6,754 core candidates and 376 gate-type descriptor assertions are
**research-staged only**. They have not been promoted into the authoritative
Round 3K governed source and preparation structures. The authoritative gate
therefore remains at zero observed core records, zero model-eligible records,
and zero countable descriptor assertions. The phase remains
`IN_PROGRESS_ACQUISITION`.

Artifact availability does not establish reuse permission. A source with any
captured artifact is not automatically complete; the checkpoint separately
reports `sources_with_completed_attempt`.

The unresolved-review inventory remains quarantined: one cross-family raw-hash
group covering three staged rows and two source-conflict rows require review.
They are not counted as losses and are not automatically collapsed.

The authoritative gate receipt came from PostgreSQL 16.13 in an existing
disposable integration database. It does not claim a local clean PostgreSQL 17
rebuild. The repository-required clean 55-migration PostgreSQL 17 verification
is delegated to CI and is reported separately from this local receipt.

## Deterministic regeneration

From the repository root, with the restricted snapshot present:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B \
  db/scripts/build-round3l-public-checkpoint.py \
  --restricted-root /absolute/path/to/owner-controlled-round3l-root \
  --gate-receipt /absolute/path/to/verified-gate-receipt.json
```

The builder validates cross-lane equality, references, hashes, pinned snapshot
totals, six-dimensional rights distributions, aggregate gate semantics, and
the public-output schema. It fails closed if the restricted snapshot is missing,
partial, or has drifted. Generated data files should not be edited manually.
