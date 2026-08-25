# Reproducibility

Two clean databases were built from migration 000 through 029 on PostgreSQL
17.11. Each build ran all Round 1, 2A, 2B, 3A, 3B, and 3C validations and
tests. Normalized schema, migration/seed hashes, stable key/code inventory,
reference counts, source versions, validation results, ontology coverage, and
Round 2B/3A/3B/3C receipts were byte-compared.

```text
POSTGRES_VERSION=17.11
MIGRATION_COUNT=30
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
ROUND3C_QUESTION_BANK_COUNT=12
ROUND3C_REAL_OBSERVATION_COUNT=0
ROUND3C_ESTIMABILITY_STATUS=NOT_ESTIMABLE
```

Frontend isolation also passed: formatting, TypeScript, nine unit tests,
production prerender, and 12 Playwright smoke paths at mobile, tablet, and
desktop viewports were green. Round 3C changed no file under `app/`.
