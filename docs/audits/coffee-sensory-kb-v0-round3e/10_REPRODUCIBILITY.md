# Reproducibility receipt

PostgreSQL 17.11 completed two disposable clean rebuilds from migrations
000–035. Both builds ran all historical and Round 3E validation, negative,
semantic, retrieval and query-plan suites.

Compared across builds:

- migration and seed manifests;
- normalized schema dumps;
- stable-key inventories;
- source snapshot keys, versions, file hashes, declared/imported/excluded counts;
- source-local quality profiles and hashes;
- empirical coverage rows;
- question lifecycle/information-gain states; and
- named question-bank, lexical-mapping, coverage-cube, data-quality and CI
  inventory hashes.

`CLEAN_REBUILD_COUNT=2`

`REPRODUCIBILITY_PASS=true`

`CI_INVENTORY_HASH=e61ebe79810d0a2638619fe500620e377d3f411e89414cab9a683d4839fb4c81`
