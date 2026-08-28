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

Subsequent release hardening is not represented by those two rebuilds. Focused
PostgreSQL 17 probe 10 compiled migrations 000-057 plus draft 059 and passed 68
of 68 global validations: 49 pre-v059 checks plus an exact 19-check v059 delta.
The focused normalization test and full Round 3M gate-schema test both exited
0, with `ROUND3M_GATE_SCHEMA_PASS`. The repository's contiguous migration plan nevertheless fails
closed because 059 is present while 058 is absent; the 058 decision requires
explicit user authorization. The full contiguous current-tree migration
pipeline, two clean rebuilds, and artifact regeneration therefore remain
unverified and no final local PostgreSQL pass is claimed.

An earlier local frontend run reached `format:check` and stopped on three Round
3M Markdown files. After formatting was corrected, an in-sandbox retry reached
browser startup and failed only because loopback bind to `::1` was denied with
`EPERM`. The authorized out-of-sandbox retry then passed format, the fail-fast
CI contract, typecheck, 9 Vitest tests, production prerender, and 12 Playwright
smoke paths with `CI_VERIFY_WEB_PASS=true`. Both failed attempts are retained in
the execution transcript.

The current-tree `npm run ci:verify:web` verification again encountered only
the sandbox `listen EPERM ::1` restriction during production prerender. The
outside-sandbox retry exited 0 and passed generated drift, format, fail-fast,
typecheck, 2 Vitest files/9 tests, production prerender, and Playwright 12/12,
ending with `CI_VERIFY_WEB_PASS=true`. This is a current local web pass, not a
remote-CI or PostgreSQL result. Remote frontend and PostgreSQL CI for the final
documentation branch tip have not yet produced run identifiers or results.

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
