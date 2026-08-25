# Reproducibility receipt

Local database verification used PostgreSQL 17.11 and discovered 39 ordered
migrations. `db/scripts/rebuild-twice.sh` created two disposable databases,
applied every migration, ran the complete historical and Round 3F validation,
negative, semantic, retrieval and query-plan suites, normalized schema dumps,
and compared migration, seed, stable-key, count and research inventories.

Result:

`CLEAN_REBUILD_COUNT=2`

`REPRODUCIBILITY_PASS=true`

`DATABASE_TEST_PASS=true`

`ROUND3F_NEGATIVE_TEST_COUNT=18`

`ROUND3F_NEGATIVE_TEST_PASS=true`

Round 3F generates no new association-range artifact files; therefore no new
generator hash contract is needed. Existing active generated-artifact gates
remain unchanged and are exercised by `npm run ci:verify`.
