# Reproducibility

Historical migrations 000–041 are frozen by 42 SHA-256 entries in
`db/migration-baselines/round3g.sha256`. Round 3H adds exactly three forward
migrations, 042–044. The migration-plan verifier expects 45 total migrations.

Two disposable PostgreSQL 17 databases were rebuilt independently from all 45
migrations. Both complete DB suites passed, their schema and governed inventory
artifacts compared identically, and the script returned
`CLEAN_REBUILD_COUNT=2` and `REPRODUCIBILITY_PASS=true`. Artifact-contract,
generated-artifact drift, web, and remote-CI results complete the release gate.
