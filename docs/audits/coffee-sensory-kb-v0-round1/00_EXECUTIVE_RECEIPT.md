# 00 — Executive Receipt

Receipt date: 2026-08-24

```text
PHASE_STATUS=PASS
SOURCE_SHA=1755915d3918013c8bd7c5f744e5ce8a0e972167
WORK_BRANCH=codex/coffee-sensory-kb-v0-round1-20260824
FINAL_LOCAL_SHA=RESOLVE_AT_HANDOFF_WITH_git_rev-parse_HEAD
FINAL_REMOTE_SHA=NOT_PUSHED
REMOTE_DIVERGENCE=8_ahead_0_behind_vs_origin/main
WORKTREE_CLEAN=true

POSTGRES_VERSION=17.11 (Debian 17.11-1.pgdg12+2)
PG_TRGM_VERSION=1.6
PGVECTOR_REQUIRED=false

LEGACY_ARTIFACTS_DISCOVERED=10
LEGACY_ARTIFACTS_ARCHIVED=5
LEGACY_RUNTIME_REFERENCED=5
ARCHIVE_COMPLETE=true

MIGRATION_COUNT=8
MIGRATION_PASS=true
CLEAN_REBUILD_COUNT=2
VALIDATION_PASS=true
NEGATIVE_TEST_PASS=true
SEMANTIC_SMOKE_PASS=true
TRIGRAM_RETRIEVAL_PASS=true
REPRODUCIBILITY_PASS=true

CANONICAL_SEED_CONCEPTS=19
SCHEMA_DOMAINS=ref,kb,evidence,corpus,ml,audit
SEED_CONCEPT_COUNT=19
UNRESOLVED_SMOKE_CASE_PASS=true
UNRESOLVED_TEST=true
RESTRICTED_TEXT_EXPORT_PASS=true

KNOWN_BLOCKERS=none
NEXT_RECOMMENDED_PHASE=rights-reviewed corpus/NLP acquisition and ontology curation
```

`FINAL_LOCAL_SHA` cannot contain the SHA of the commit that contains this file:
adding that value changes the commit itself. The immutable branch-tip SHA is
therefore resolved with `git rev-parse HEAD` and reported in the final
engineering receipt. The branch was not pushed, so no remote branch SHA or
pull request is claimed.

## Execution environment

The validated server was the official `postgres:17-bookworm` image at digest:

```text
postgres@sha256:84560e3b9c6874893fc4e2854f5dc3e7c1a37bc9d1dfd7a8c641310ae22ba5ad
```

It reported:

```text
PostgreSQL 17.11 (Debian 17.11-1.pgdg12+2) on aarch64-unknown-linux-gnu,
compiled by gcc (Debian 12.2.0-14+deb12u1) 12.2.0, 64-bit
```

The container used no network, kept its PostgreSQL data directory in tmpfs,
and mounted the isolated worktree read-only. The host's existing PostgreSQL
16.13 cluster and its user-owned databases were not modified.

## Receipt links

- [Discovery and archive](./01_DISCOVERY_AND_ARCHIVE.md)
- [Schema implementation](./02_SCHEMA_IMPLEMENTATION.md)
- [Constraint tests](./03_CONSTRAINT_TESTS.md)
- [Semantic smoke tests](./04_SEMANTIC_SMOKE_TESTS.md)
- [Query-plan review](./05_QUERY_PLAN_REVIEW.md)
- [Reproducibility](./06_REPRODUCIBILITY.md)
- [Known gaps](./07_KNOWN_GAPS.md)

The external Deep Research PDF was not physically present in the attachment or
repository. It was not copied or fabricated; the supplied engineering contract
is recorded as the research source.
