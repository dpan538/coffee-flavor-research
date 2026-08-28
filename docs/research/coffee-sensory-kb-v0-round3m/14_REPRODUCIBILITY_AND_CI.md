# Reproducibility and CI

## Required verification layers

Round 3M verification covers:

- exact Round 3L public-checkpoint regeneration;
- baseline count reconciliation;
- artifact schema and checksum contract;
- idempotent artifact generation and import;
- live adapter positive and negative paths;
- SQL descriptor ledger and gate semantics;
- two clean database rebuilds from separate empty databases before a final
  current-tree pass can be claimed;
- local frontend verification;
- local PostgreSQL verification;
- remote frontend and PostgreSQL 17 CI.

The review-artifact builder was also run twice independently against the same
governed Round 3L root, descriptor census PDF, and live export. Both temporary
outputs contained 22 files, `diff -rq` was empty, and the verifier emitted
`ROUND3M_REVIEW_BUILD_DETERMINISM_PASS`.

At reproducibility checkpoint
`bdc9bca15dad58a910a943ab5fed41176cc77af8`, local PostgreSQL 17 verification
applied the then-current 57 migrations, loaded the artifacts idempotently, and
completed two separate empty-database rebuilds. These markers are historical,
not final current-tree results:

```text
ROUND3M_GATE_SCHEMA_PASS
ROUND3M_VALIDATION_PASS=true
DATABASE_TEST_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
CI_VERIFY_DATABASE_PASS=true
```

That checkpoint imported 516 queue/decision rows, 3,096 rights rows, 140
assertions, 139 assertion-level observations, 137 record-level unique
observations, 508 pair events, 0 human-confirmed rows, and 0 model-eligible
rows. The artifact validator and all 18 restricted live-adapter tests passed.

The current contiguous 60-migration tree applied 058 first to disposable
PostgreSQL 17, ran 3 focused positives, 32 focused negatives, the corrected 059
suite, all 84 current gate invariants, and the complete database harness. The
84 include the original 68 focused invariants plus 16 evidence-binding and gate
rebinding checks.

Two further empty databases independently applied the full tree and artifacts.
Their 41-file schema, manifest, stable-key, reference-count, validation,
ontology, and Round 2/3 inventory packages were byte-identical; both databases
were disposed by the guarded cleanup path. Current markers are:

```text
DATABASE_TEST_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
CI_VERIFY_DATABASE_PASS=true
LOCAL_POSTGRES_CI_PASS=true
```

An earlier local frontend run reached `format:check` and stopped on three Round
3M Markdown files. After formatting was corrected, an in-sandbox retry reached
browser startup and failed only because loopback bind to `::1` was denied with
`EPERM`. The authorized out-of-sandbox retry then passed format, the fail-fast
CI contract, typecheck, 9 Vitest tests, production prerender, and 12 Playwright
smoke paths with `CI_VERIFY_WEB_PASS=true`. Both failed attempts are retained in
the execution transcript.

The post-058 `npm run ci:verify:web` command exited 0 and passed generated
drift, format, fail-fast, typecheck, 2 Vitest files/9 tests, production
prerender, and Playwright 12/12, ending with `CI_VERIFY_WEB_PASS=true`. Remote
frontend and PostgreSQL CI for the final branch tip remain post-push receipts.

An earlier remote baseline run for reproducibility checkpoint
`bdc9bca15dad58a910a943ab5fed41176cc77af8` did complete successfully: workflow
run `33151084412`, frontend job `98782973168`, and PostgreSQL 17 job
`98782973442`. That run predates this documentation checkpoint and cannot stand
in for the required final branch-tip CI run.

Passing equality proves deterministic output, not corpus scale.

No source-drift timestamp is used as an assertion count. Governed bounded field
captures stay outside public Git while their public artifacts retain hashes,
locators, retrieval times, and explicit storage state. Full official page
bodies were not acquired.
