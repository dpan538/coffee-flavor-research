# Round 2B reproducibility

Date: 2026-08-24

Status: `REPRODUCIBILITY_PASS=true`

## Reproduction boundary

The schema, normalization rules, generated public corpus artifacts, derived
statistics, audit structure, and retrieval evaluation are source-controlled.
The complete commercial tasting-note fields, excluded fragments, consumer
reviews, and private review rationales are not.

A full local derivation therefore requires a separately obtained checkout of
the CC BY 4.0 Firstbloom repository pinned to
`a6cb0026d1af9642724793c799bbc48dc189ba35`. Its files must match the hashes in
the [source manifest](../../../db/data/round2b/firstbloom_source_manifest.json).
The project repository alone cannot reconstruct excluded source text, so
`raw_public_reproducibility_complete=false` is the accurate boundary.

## Frozen inputs and generators

| Artifact                              | Identity or hash                                                     |
| ------------------------------------- | -------------------------------------------------------------------- |
| Round 2A source commit                | `2d864d56496c587cff5b6774e0ea41be8b416e6c`                           |
| Firstbloom source commit              | `a6cb0026d1af9642724793c799bbc48dc189ba35`                           |
| Corpus version                        | `firstbloom-a6cb002-pilot-v1`                                        |
| Corpus generator code commit          | `d90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0`                           |
| Pilot seed SQL SHA-256                | `955fecba967cee169f24e7c81b5d350d0e34902019af729cb3cf6558e0d96042`   |
| Corpus generation receipt SHA-256     | `40f45e08b4014416f2f0631baa5f615a397a996a0de110cede7f332e7097a492`   |
| Audit-case private TSV SHA-256        | `0401ae2c3759044d4b9f5ab16ea1f374e27399080fc14717e27f79d0d96f1609`   |
| Candidate-pool private TSV SHA-256    | `00b087cabd36d1b50a258624e79e14ea10b3c135969143ca56c967e29c95cd45`   |
| Reviewer 1 private ledger SHA-256     | `5b6b055cb64d99ffda7310fbb787434740f945bbf6e87fb09d275e43dc55005a`   |
| Reviewer 2 private ledger SHA-256     | `ed1ce352de996711182b2bf9ac36bbd05c3d4e4faf0131aaf23906c68458219e`   |
| Adjudication private ledger SHA-256   | `7e9b4ce21697ffd614cc11e89632394411d1bf1813bc331f0cc66a1b506ef6e8`   |
| Candidate model freeze                | `a6abb4112cff3fc436b1613c37f9b40f51e65144` at `2026-08-24T07:48:49Z` |
| Database audit-set inventory SHA-256  | `f23fe402b542a482532149dd41de14ef04d95c34226e5d7de13ffc4cd036208b`   |
| Evaluation seed SQL SHA-256           | `2300911368607debafab935f6141d05a4521c68457da98ef7edb2956ab9bbe1d`   |
| Evaluation manifest SHA-256           | `d6876c621c95c53aecd9f07358dac20beafb6f8d789186a36f4aa6d169b1aabf`   |
| Resolution/feedback migration SHA-256 | `abd551b8f07dd08ad1a2a9626151a615ef1fc7e3add86d5e368d0fa9b417f905`   |
| Exact-resolution policy SHA-256       | `0ecc8362535084f0ec7928c5336f5864c539f2d62a46296d65a392707f6b085d`   |
| Resolution result inventory SHA-256   | `1084e534b81de40cf39dbf3c5c5e07fe035907b13b0f3df25079d288d9b7f33e`   |

The public [corpus generation receipt](../../../db/data/round2b/generation_receipt.json)
and [evaluation manifest](../../../db/data/round2b/evaluation/round2b_evaluation_manifest.json)
bind the detailed input and output hashes. Public evaluation files contain
stable hashed identities and receipts, not private phrases or rationales.

## Run-scoped resolution history

Migration 017 preserves the exact-resolution materialization as immutable,
versioned history rather than only a mutable current projection:

- `corpus.observation_resolution_run` binds the normalization derivation,
  policy version, deterministic as-of timestamp, allowed mapping types, policy
  hash, source baseline SHA, expected counts, and result inventory;
- `corpus.observation_resolution_run_result` preserves all 5,564 per-observation
  outcomes independently of the current `corpus.observation_resolution`
  materialization;
- a run must be inserted unfrozen, populated, and frozen only through a guarded
  update that verifies policy semantics, counts, and the computed inventory;
- once frozen, the run cannot be updated or deleted, and its result rows cannot
  be inserted, updated, or deleted;
- `corpus.v_resolution_coverage` projects counts by frozen run, allowing later
  policies to coexist without rewriting this receipt;
- validation recomputes the exact policy result and asserts that the current
  materialization equals the latest frozen run.

The frozen V1 run remains scoped to exact expression identity, current active
preferred or approved lexicalizations at `2026-08-24T08:31:00Z`, and exactly
one eligible concept. Normalized-phrase, trigram, graph, and
`polysemous_usage` mappings remain excluded.

## Deterministic derivation sequence

1. Verify the pinned source commit and every permitted source-file hash.
2. Run the pilot generator with its recorded configuration. Confirm the
   generated migration and all TSV/JSON inventory hashes.
3. Run the audit selector. Keep the phrase-bearing case and candidate files
   private with owner-only permissions.
4. Obtain two independent review ledgers and a distinct adjudication ledger.
   Verify all five private input hashes before compiling the evaluation.
5. Run the evaluation compiler twice and require byte-identical public outputs
   and evaluation migration.
6. Create a fresh PostgreSQL 17 database and apply migrations 000 through 017
   in lexical order.
7. Run historical migration, negative, semantic, retrieval, query-plan, and
   Round 2B closure tests. Dump the stable-key and metric inventory.
8. Destroy the database and repeat steps 6–7. Compare both inventories and
   require identical hashes.

Migrations 000–011 are historical and must match their Round 2A hashes. Round
2B is forward-only through migrations 012–017. PostgreSQL constraints remain
the integrity authority even though large deterministic seeds are generated
from source-controlled TSV/JSON files.

## Frozen database inventory contract

Each rebuild must reproduce at least:

- 15 policy reviews, one acquired source, 215 publishers, 2,383 products, and
  2,474 documents;
- 6,818 raw fragment observations, 5,564 retained occurrences, and 1,254
  hash-only occurrences;
- 2,124 unique retained raw expressions and 1,713 normalized identities;
- 1,713 frequency rows and 4,600 co-occurrence pairs;
- 1,866 strictly resolved and 3,698 unresolved occurrences;
- 57 strictly resolved and 1,656 unresolved normalized identities;
- 300 audit cases, eight split/baseline evaluations, 665 adjudicated qrel rows,
  610 candidate traces, 796 candidate signals, and 80 metric values;
- 11 ontology-feedback candidates, 14 adjudicated nearest-concept links, and
  zero automatic ontology promotions.

## Final validation and paired rebuild

A fresh PostgreSQL 17.11 database successfully applied all 18 migrations,
verified the Round 1 and Round 2A historical fingerprints, and passed the full
SQL harness. The result includes 31 Round 1, 47 Round 2A, and 53 Round 2B
expected-zero checks, with no failure or `NULL` result. `pg_trgm` is version
1.6 and `pgvector` remains absent.

The definitive rebuild repeated the full migration and validation sequence in
two clean PostgreSQL 17.11 databases. Migration, seed, schema, stable-key,
reference-count, source-version, validation, ontology-coverage, Round 2B, and
`pg_trgm` inventories matched between runs. The full test log has SHA-256
`c044157b316ce2605744a9dc8a4f6fa53883e472dad43f4ebd03623a47f64306`;
the paired-rebuild log has SHA-256
`ea36481d9b3765bca7a2ed7c007120b6df5f0d5ffb86ddb7ab79ac717b2cec74`.
Cleanup completed after verification.

## Rebuild receipt

```text
POSTGRES_VERSION=17.11
PG_TRGM_VERSION=1.6
PGVECTOR_REQUIRED=false
CLEAN_REBUILD_COUNT=2
MIGRATION_COUNT=18
MIGRATION_PASS=true
DATABASE_TEST_PASS=true
ROUND1_VALIDATION_CHECK_COUNT=31
ROUND2A_VALIDATION_CHECK_COUNT=47
ROUND2B_VALIDATION_CHECK_COUNT=53
REPRODUCIBILITY_PASS=true
PAIRED_MIGRATION_INVENTORY_SHA256=dcdb437eb6830fec3865236ba19f2e24d673177053ec6d029a77c78dc1ed2178
PAIRED_SEED_INVENTORY_SHA256=7f1ce163d69bcb8aa4994a1b7e07dc229d2f4ca69460cd60e532a9dea8f376b7
PAIRED_SCHEMA_INVENTORY_SHA256=fd1734d0c2fa8ea350c81aa6f239b0020062b2775c0e92b0511e0cb8da0953f7
PAIRED_STABLE_KEY_INVENTORY_SHA256=af1f7d94e98628e11d2aff0d8ee5a96a13c3cdba33742e6cbc0734b86242e01d
PAIRED_REFERENCE_COUNT_INVENTORY_SHA256=1cd4bc023db85cfcce08cbfadb6f8a403950dd97dc9405b7da90fc23585d3797
PAIRED_SOURCE_VERSION_INVENTORY_SHA256=e06cc0dcbc1306eca8fa8d74f2c44db15d16901c45964756a38a11ec7cb8b5a8
PAIRED_VALIDATION_RESULT_INVENTORY_SHA256=80e390d3cee7309d7e565cdc9e6fe274db232da4e3c18ee904dd87e9ef24dce2
PAIRED_ONTOLOGY_COVERAGE_INVENTORY_SHA256=a21e78a89e9adf67a232faec5a8787f416896dbff652e90f49557b8b03208b88
PAIRED_ROUND2B_INVENTORY_SHA256=15f40c7ded21a23b082e47ac268724b1ab7cdce1a289deb7b9578f30374973bd
PAIRED_PG_TRGM_ARTIFACT_SHA256=e5cd57eee9635f3612a2a913746f7f794cdb573cc3e16f6b7d8e613f92beac83
FULL_TEST_LOG_SHA256=c044157b316ce2605744a9dc8a4f6fa53883e472dad43f4ebd03623a47f64306
PAIRED_REBUILD_LOG_SHA256=ea36481d9b3765bca7a2ed7c007120b6df5f0d5ffb86ddb7ab79ac717b2cec74
RAW_PUBLIC_REPRODUCIBILITY_COMPLETE=false
CLEANUP_COMPLETE=true
```

The source-controlled derivation, independent replay, and definitive paired
rebuild pass. Public raw reproducibility remains intentionally incomplete for
protected or excluded inputs; that boundary is a rights safeguard rather than
a rebuild defect.
