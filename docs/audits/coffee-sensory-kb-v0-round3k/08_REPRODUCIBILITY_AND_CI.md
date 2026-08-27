# Reproducibility and CI audit

## Deterministic rebuild contract

The rebuild process first verifies exact fingerprints for migrations 000-048,
reconstructs the frozen Round 3I checkpoint, then applies forward migrations
049-052. A valid final run must perform two clean PostgreSQL rebuilds and compare
eight independently regenerated inventories:

1. competition-series inventory;
2. edition inventory;
3. effective-record inventory;
4. descriptor-assertion inventory;
5. rights inventory;
6. duplicate/repeat inventory;
7. label-disposition inventory;
8. training-corpus manifest.

The grouped split schema stores stable plan versions, groups, membership, and
assignments; random row splitting is prohibited. Hash comparison must fail on
any nondeterminism.

## Validation layers

The final receipt requires formatting, TypeScript checks, unit tests, smoke
tests, production build, adapter-contract tests, migration planning, SQL
negative tests, Round 3K validation queries, two clean PostgreSQL 17 rebuilds,
and both frontend and PostgreSQL remote CI.

The SQL adversarial suites target core identity/version rules and integrated
failures including missing hashes, cross-source lineage, actor/type confusion,
fresh-preparation fraud, rights inflation, P3/P4 leakage, forced labels,
coassertion mismatch, duplicate/repeat defects, C1 inference, semantic invention,
model runs, and weight/embedding artifacts.

## Verified checkpoint receipt

```text
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
CONSTRAINT_TEST_PASS=true
REMOTE_FRONTEND_CI_PASS=true
REMOTE_POSTGRES_CI_PASS=true
REMOTE_VALIDATED_CHECKPOINT_SHA=ab7c886f0ea3d3a59709a618c148f82fe892d927
REMOTE_CI_RUN=33075085741
REMOTE_FRONTEND_JOB=98527071160
REMOTE_POSTGRES_JOB=98527071265
```

The PostgreSQL job used PostgreSQL 17.11, applied all 53 migrations, passed the
Round 3K validation function, reproduced all eight inventories across two clean
databases, and reported `NEW_CONSTRAINT_COUNT=385`. Each Round 3K inventory is
truthfully empty and hashes to the SHA-256 of an empty file because no corpus
row is admitted; equality proves determinism, not data volume. The final
documentation-only audit commit requires one additional green feature-branch
run before handoff.
