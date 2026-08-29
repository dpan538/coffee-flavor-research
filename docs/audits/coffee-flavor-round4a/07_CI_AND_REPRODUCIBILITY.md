# CI and reproducibility

Exact-main CI completed before Round 4A development. Local verification
regenerated Round 4A artifacts twice with zero drift, ran the complete frontend
contract, and ran the PostgreSQL 17 harness with two empty-database rebuilds.
The rebuilds produced matching migration, seed, schema-only dump, stable-key,
reference-row-count, source-version, validation, ontology, and prior-round
inventory hashes.

The local runtime reports Node 22.21.0 while React Router requests 22.22.0 or
newer. Type checking, tests, and the production build execute despite the
warning; remote CI remains authoritative for the configured runner.

```ini
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
LOCAL_FRONTEND_CI_PASS=true
LOCAL_POSTGRES_CI_PASS=true
```

Remote CI run `33225428359` validated implementation checkpoint
`3781afc46495ad4e6ad94e0d4dd238f6f71a293f`. Frontend job `99028079844`
passed in 1m25s; PostgreSQL 17 job `99028080047` passed in 32m1s. GitHub emitted
only a platform annotation about actions that still target Node 20 internals
being forced onto Node 24; neither repository job failed.

```ini
REMOTE_FRONTEND_CI_PASS=true
REMOTE_POSTGRES_CI_PASS=true
REMOTE_CI_RUN_ID=33225428359
REMOTE_CI_VALIDATED_SHA=3781afc46495ad4e6ad94e0d4dd238f6f71a293f
```
