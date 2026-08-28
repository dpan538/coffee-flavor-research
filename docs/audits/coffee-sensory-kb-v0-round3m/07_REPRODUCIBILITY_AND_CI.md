# Reproducibility and CI audit

The local audit records:

1. deterministic Round 3L baseline regeneration;
2. two deterministic Round 3M artifact builds;
3. artifact-contract and checksum validation;
4. idempotent artifact import;
5. named live-adapter tests;
6. named SQL positive and negative tests;
7. two separate clean database rebuilds at the historical reproducibility
   checkpoint;
8. final current-tree PostgreSQL 17 CI;
9. current-tree local frontend CI.

The independent Round 3M review-artifact determinism check wrote 22 files to
each of two separate temporary directories from the same governed Round 3L
root, report PDF, and live export. `diff -rq` returned no differences and the
check emitted `ROUND3M_REVIEW_BUILD_DETERMINISM_PASS`.

The completed markers below belong to historical reproducibility checkpoint
`bdc9bca15dad58a910a943ab5fed41176cc77af8`, not the current hardening tree:

```text
ROUND3M_ARTIFACT_CONTRACT_PASS
ROUND3M_GATE_SCHEMA_PASS
ROUND3M_VALIDATION_PASS=true
DATABASE_TEST_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
CI_VERIFY_DATABASE_PASS=true
```

Those builds started from separate empty databases and imported the same 516
queue/decision rows, 3,096 rights rows, 140 assertions, 139 assertion-level
observations, 137 record-level unique observations, and 508 pair events. The
first completed PostgreSQL 17 attempt exposed only a macOS `mktemp` filename
collision after the database tests; the suffix-free template fix was followed
by a full two-build pass.

The current contiguous 60-migration tree applied 058 first to disposable
PostgreSQL 17, ran its 3 positive and 32 negative cases, ran the corrected 059
suite, and passed all 84 current gate invariants. The 84 include the original
68 focused checks plus 16 evidence-binding and gate-rebinding checks. The
complete database harness passed before two further empty-database rebuilds.

Both clean rebuilds imported the same artifact set and produced byte-identical
41-file schema, manifest, stable-key, reference-count, validation, ontology,
and Round 2/3 inventory packages. The rebuild script then disposed both
databases. The enclosing verification emitted the current-tree pass markers:

```text
DATABASE_TEST_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
CI_VERIFY_DATABASE_PASS=true
LOCAL_POSTGRES_CI_PASS=true
```

An earlier frontend run stopped at `format:check` on three new Markdown files.
After correction, an in-sandbox run failed only when Playwright's server could
not bind `::1` (`EPERM`). The authorized out-of-sandbox retry passed the
fail-fast CI contract, formatting, typecheck, 9 Vitest tests, production
prerender, and 12 Playwright smoke paths, ending with
`CI_VERIFY_WEB_PASS=true` for that earlier tree.

The post-058 `npm run ci:verify:web` command exited 0 and passed generated-drift
checks, format, the fail-fast contract, typecheck, 2 Vitest files with 9 tests,
production prerender, and all 12 Playwright smoke paths. This establishes
`LOCAL_FRONTEND_CI_PASS=true`. Remote frontend/PostgreSQL outcomes remain
`NA_POST_COMMIT_VERIFICATION_REPORTED_IN_FINAL_RESPONSE` in the committed
receipt because they depend on the final pushed commit.

The preceding reproducibility checkpoint did receive a successful remote
baseline run: workflow `33151084412` at
`bdc9bca15dad58a910a943ab5fed41176cc77af8`, with frontend job `98782973168`
and PostgreSQL 17 job `98782973442` both successful. Because this audit package
was not in that commit, the run is historical evidence only; it does not change
the final remote fields from `NA`.

The worktree must be clean and the final remote SHA must match the local SHA;
those self-referential checks cannot be embedded in the commit they identify.
CI equality is an engineering receipt, not evidence that a descriptor gate has
passed.
