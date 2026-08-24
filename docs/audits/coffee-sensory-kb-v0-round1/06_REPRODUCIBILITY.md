# 06 — Reproducibility

- Receipt date: 2026-08-24
- Runner: `db/scripts/rebuild-twice.sh`

## Isolation and command contract

The runner connected only to the isolated PostgreSQL 17 container. It required
the explicit destructive opt-in `COFFEE_KB_ALLOW_DATABASE_DROP=1`, accepted
only target names matching `^coffee_sensory_kb_v0_[a-z0-9_]+$`, refused to
replace existing databases, and created:

```text
coffee_sensory_kb_v0_rebuild_one
coffee_sensory_kb_v0_rebuild_two
```

For each fresh database it applied all eight migrations, ran 31 expected-zero
checks, exercised 15 prohibited writes, ran semantic/retrieval tests, and
executed query-plan assertions. The exit cleanup dropped both databases; a
post-run query found zero remaining rebuild databases.

## Exact runtime

```text
POSTGRES_VERSION=17.11 (Debian 17.11-1.pgdg12+2)
PG_TRGM_VERSION=1.6
PGVECTOR_REQUIRED=false
IMAGE_DIGEST=postgres@sha256:84560e3b9c6874893fc4e2854f5dc3e7c1a37bc9d1dfd7a8c641310ae22ba5ad
```

## Migration content hashes

| migration                          | SHA-256                                                            |
| ---------------------------------- | ------------------------------------------------------------------ |
| `000_extensions.sql`               | `3bcb5ad0e144ee8020df2b6a76efe253bb735d61612c20c498302b983c5ff133` |
| `001_reference_and_schemas.sql`    | `f82ca7f99e3993c8bf9570b357385e2a3d85f109c678534ea0531f4abcca59bc` |
| `002_core_schema.sql`              | `6df4ca809d43c358976a47abc3ecc0c484c239d0ba54c9041105c4ffba54dd2f` |
| `003_evidence_corpus_ml_audit.sql` | `df95e74948d1b90b4d4aac635898be67229c49c06b0ea4af62d57382cfc2b4de` |
| `004_constraints_and_triggers.sql` | `71c4d5ced3d7c08275b3583625b54acd233705e57d7b953cd12d252d636896cd` |
| `005_indexes_and_views.sql`        | `3b32c451900c28bb4f9aac676c411d44d0ce01fea94ebb538a5f08b4c2c97ac3` |
| `006_reference_seed.sql`           | `1b6ca835d5556d981b2709fcd3401d3df4e0f523ee2e458dd90445912b9fccb0` |
| `007_validation_queries.sql`       | `255b37d1bbea27ae9a8bc92a39730b44a8e8d9ace8bce113cc2e989bff69d73c` |

## Compared logical artifacts

Both builds produced byte-identical copies of every compared artifact.

| artifact                          | build-one/build-two SHA-256                                        | result |
| --------------------------------- | ------------------------------------------------------------------ | ------ |
| Migration hash manifest           | `add0a5d120c5a17e73c2ab9f2bcc00d60a5c0a667cd9fb95967366248f3208ac` | MATCH  |
| Seed SQL content                  | `1b6ca835d5556d981b2709fcd3401d3df4e0f523ee2e458dd90445912b9fccb0` | MATCH  |
| Normalized schema-only dump       | `24a03d1db6ea1d2ea916d7acbf65a1e2c0276ab859514dc540642698f2dd6cf5` | MATCH  |
| Stable `*_key`/`*_code` inventory | `2912ce4cf6808301ed0b632a7889d769e670db8480b095fcc6149582c977cd17` | MATCH  |
| Reference-table row counts        | `0b5113bbcb77d3c58ce67ed7fefec0c5fc1c2e3c49b22c4dfcdb11ab1fa49604` | MATCH  |
| Source-version inventory          | `4a6884835f52d452121f12d2b4fece165609e8a525cfd8b39c4e8ca25a0fdf66` | MATCH  |
| Validation result counts          | `2b1c698276b02e57e90634a3744b2e308d949b8d8b12bfaa6b8d7851f0a1ff09` | MATCH  |
| pg_trgm version record            | `e5cd57eee9635f3612a2a913746f7f794cdb573cc3e16f6b7d8e613f92beac83` | MATCH  |

The 13 controlled reference tables contained the same 52 rows in each build;
both source-version inventories contained the same public project fixture and
restricted synthetic fixture. All 31 validation counts were zero in both
builds.

The raw comparison artifacts were copied before container teardown to the
ignored local directory `db/.test-output/rebuild.xErKxm/`. They are not tracked
and are not required to reproduce the result; rerunning the script creates a
new auditable artifact directory.

```text
MIGRATION_COUNT=8
MIGRATION_PASS=true
CLEAN_REBUILD_COUNT=2
VALIDATION_CHECK_COUNT=31
VALIDATION_PASS=true
REPRODUCIBILITY_PASS=true
DISPOSABLE_DATABASES_REMAINING=0
```
