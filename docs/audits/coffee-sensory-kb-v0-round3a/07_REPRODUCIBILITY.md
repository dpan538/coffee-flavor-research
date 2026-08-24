# Reproducibility audit

## Required procedure

The repository script creates two distinct disposable PostgreSQL 17 databases. For each build it:

1. verifies immutable Round 1, Round 2A, and Round 2B migration hashes;
2. applies migrations `000`–`021` in contiguous order;
3. loads deterministic ontology, corpus, evaluation, and context seeds;
4. runs all historical validation contracts;
5. runs Round 3A validation, negative, semantic, retrieval, and plan tests;
6. records schema, stable keys, reference counts, source versions, ontology coverage, Round 2B inventory, Round 3A inventory, and pg_trgm version;
7. compares every artifact byte-for-byte;
8. drops both disposable databases.

The stable-key inventory now includes the `context` schema. The validation inventory includes all four round contracts. The new Round 3A inventory contains coverage, preparation nodes, roast projections, unresolved labels, and measurement methods.

## Result

```text
POSTGRES_VERSION=17.11
PG_TRGM_VERSION=1.6
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
```

Both builds produced byte-identical migration and seed manifests, schema-only dumps, stable-key inventories, reference counts, source-version inventories, validation results, ontology coverage, Round 2B inventories, Round 3A inventories, and pg_trgm version receipts. The matching PostgreSQL 17 client from the disposable official server image generated the schema dumps because the host's Homebrew client is PostgreSQL 16 and correctly refuses to dump a PostgreSQL 17 server.

The candidate Dryad files are not required for rebuild because Round 3A registers only source/version/dataset metadata; no protected or remote raw dependency is hidden.
