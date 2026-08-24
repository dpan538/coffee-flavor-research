# Round 2A reproducibility audit

Date: 2026-08-24

Status: `REPRODUCIBILITY_PASS=true`

## Source boundary

```text
SOURCE_ROUND1_SHA=26b014bd6fc4f87880e6e8f6a939a25cbbedb874
WORK_BRANCH=codex/coffee-sensory-kb-v0-round2a-ontology-20260824
MIGRATION_COUNT=12
FORWARD_MIGRATION_COUNT=4
```

`db/scripts/migration-plan.sh` discovers a contiguous `000`--`011` migration
sequence and verifies the immutable Round 1 fingerprint manifest before apply,
test, or rebuild. Current source-controlled forward-migration hashes are:

```text
02bd4caa5046f5bb136abdbd5f8334599d929ccc5808f211a347ade4a9ede655  008_concept_provenance.sql
ec6def373a90e8b30a7d2e569f39b01945318b4cb1f6992d76478678d8d18d58  009_concept_schemes.sql
fc6cbcabe63c93b3aa85b5a66f9a7b9810214622c45b6f3300514df0e3982a1d  010_canonical_ontology_seed.sql
9798a932b3f0816fbe8337a92449052fa486be7c177a14027463007dc049cdb0  011_ontology_validation.sql
```

These hashes match the forward migrations used in the final rebuild.

## Immutable Round 1 fingerprints

```text
3bcb5ad0e144ee8020df2b6a76efe253bb735d61612c20c498302b983c5ff133  000_extensions.sql
f82ca7f99e3993c8bf9570b357385e2a3d85f109c678534ea0531f4abcca59bc  001_reference_and_schemas.sql
6df4ca809d43c358976a47abc3ecc0c484c239d0ba54c9041105c4ffba54dd2f  002_core_schema.sql
df95e74948d1b90b4d4aac635898be67229c49c06b0ea4af62d57382cfc2b4de  003_evidence_corpus_ml_audit.sql
71c4d5ced3d7c08275b3583625b54acd233705e57d7b953cd12d252d636896cd  004_constraints_and_triggers.sql
3b32c451900c28bb4f9aac676c411d44d0ce01fea94ebb538a5f08b4c2c97ac3  005_indexes_and_views.sql
1b6ca835d5556d981b2709fcd3401d3df4e0f523ee2e458dd90445912b9fccb0  006_reference_seed.sql
255b37d1bbea27ae9a8bc92a39730b44a8e8d9ace8bce113cc2e989bff69d73c  007_validation_queries.sql
```

## Clean-rebuild procedure

`db/scripts/rebuild-twice.sh` requires PostgreSQL 17 or newer and an explicit
`COFFEE_KB_ALLOW_DATABASE_DROP=1` safety opt-in. It also requires two distinct,
previously absent disposable database names matching the restricted
`coffee_sensory_kb_v0_[a-z0-9_]+` pattern. For each build it:

1. creates a UTF-8 database from `template0`;
2. verifies and applies all migrations in order;
3. runs the Round 1 and Round 2A validation, negative, semantic, retrieval, and
   query-plan suites;
4. writes a normalized schema-only dump;
5. writes stable logical keys rather than unstable identity values;
6. writes reference-table counts, source/version/licence inventory, validation
   results, ontology coverage, migration/seed manifests, and the `pg_trgm`
   version; and
7. destroys both disposable databases through the exit cleanup trap.

The two builds must compare byte-for-byte for:

- migration manifest;
- seed-file manifest;
- normalized schema-only dump;
- stable-key inventory;
- reference-table row counts;
- source-version/licence inventory;
- Round 1 and Round 2A validation result counts;
- ontology coverage; and
- `pg_trgm` version.

The seed-manifest hashes are also compared explicitly. Negative-test sequence
consumption is excluded from the stable-key inventory by design.

## Required environment

Both builds used the official `postgres:17-bookworm` image at digest
`sha256:84560e3b9c6874893fc4e2854f5dc3e7c1a37bc9d1dfd7a8c641310ae22ba5ad`,
reporting PostgreSQL 17.11 (Debian) and `pg_trgm` 1.6. The host PostgreSQL 16
cluster was never used. `pgvector` is not required, and the Round 2A validation
confirmed that no `vector` extension was installed.

## Artifact comparison receipt

Each artifact was byte-identical between build one and build two.

| Compared artifact                | Matching SHA-256                                                   |
| -------------------------------- | ------------------------------------------------------------------ |
| Migration manifest               | `09d148d48ab6cc46f1ccae553e630d7ca71e89dd20b90fc532d381706389430e` |
| Seed-file manifest               | `13e70450fc37488ba54195cea5e8cf2a6892b5065b81e36898d1d29a7980cce3` |
| Normalized schema dump           | `83310deef5ad8fed1d5e896fdaa44baa013dfb36a2b9b283bce0a6c2b185b89e` |
| Stable-key inventory             | `f9975c50601a4bc80cbd1475314fdd26ea47eaceed1ad893e1a25aa343e3d3de` |
| Reference-table counts           | `68ea0a0b1006e0336028f812933c6009f0784cd8248027b123ddc27c3aaf80e3` |
| Source-version/licence inventory | `1f3b4b8c2f1f9e5e0697fb241e023221328314f1ab588e5e6537eac32412dcd1` |
| Validation results               | `bef9ff62d79f711c88e0c6cb2d7d9201210c066aa96d6e46d9a3859375d02ce5` |
| Ontology coverage                | `a21e78a89e9adf67a232faec5a8787f416896dbff652e90f49557b8b03208b88` |
| `pg_trgm` version                | `e5cd57eee9635f3612a2a913746f7f794cdb573cc3e16f6b7d8e613f92beac83` |

The stable-key inventory was generated and printed for both builds and matched
at `f9975c50601a4bc80cbd1475314fdd26ea47eaceed1ad893e1a25aa343e3d3de`;
it is intentionally reproducible from the harness rather than duplicated as a
manually maintained audit file.

## Result

```text
POSTGRES_VERSION=17.11 (Debian)
PG_TRGM_VERSION=1.6
ROUND1_MIGRATION_FINGERPRINT_PASS=true
MIGRATION_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
DISPOSABLE_DATABASES_DROPPED=true
REPOSITORY_TESTS_PASS=true
WORKTREE_CLEAN=RECORDED_BY_FINAL_GIT_RECEIPT
```

Both clean builds applied all 12 migrations, passed all eight SQL suites, and
produced matching artifacts. The cleanup trap dropped both disposable
databases. Repository type checks, nine Vitest tests, the production build,
nine Playwright smoke tests, harness syntax review, and immutable-manifest
checks also passed. The clean-worktree fact is reported after commit because
the audit package itself is part of that commit.
