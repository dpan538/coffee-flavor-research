# CI negative and invariant tests

The CI decomposition is protected by `db/scripts/test-ci-workflow-contract.py`.
It passed locally with 17 classified contracts and zero mandatory skips.

Its invariant checks reject:

- a missing, duplicate, or unclassified historical/current contract;
- removal of any named public artifact test from the push entrypoint;
- removal of `rebuild-twice.sh` from the historical entrypoint;
- a restricted replay that does not require owner-controlled input;
- a current database path that omits migration, artifact load, or SQL tests;
- removal of a bounded push job; and
- a historical workflow without dispatch, schedule, the original historical
  command, or its documented dedicated budget.

The existing database contracts continue to test negative SQL, semantic,
retrieval, query-plan, artifact checksum, public-boundary, and restoration
conditions. No SQL assertion was removed.
