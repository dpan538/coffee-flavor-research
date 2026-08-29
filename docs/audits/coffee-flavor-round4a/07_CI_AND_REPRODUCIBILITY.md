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

Final branch and remote CI identifiers are recorded in the executive receipt
only after the branch push completes.
