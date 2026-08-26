# Reproducibility

The reproducibility contract has two checkpoints. First, migrations `000`--`044`
must match the 45 hashes in `db/migration-baselines/round3h.sha256`, rebuild,
pass `audit.run_round3h_validation_queries()`, and pass the Round 3H negative,
semantic, retrieval, and query-plan tests. Only then may forward migrations
`045`--`048` be applied.

Each clean PostgreSQL 17 build must then:

1. run the complete database test suite and the Round 3I freeze gate;
2. export normalized schema, validation, seed, and round inventories;
3. export all 10 deterministic Round 3I TSV inventories and the JSON manifest;
4. compare the two builds byte-for-byte;
5. compare each rebuilt freeze artifact with its committed counterpart; and
6. verify the database artifact registry matches every committed SHA-256.

The migration does not seed a claim that these external steps occurred.
`audit.research_database_reproducibility_attestation` accepts only a receipt for
exactly two PostgreSQL 17 rebuilds and 11 artifacts whose hashes agree across
both rebuilds and with the committed copies. That receipt is immutable. The
final release-attestation trigger refuses insertion until this independent
receipt exists and every hard freeze gate still passes.

The required result is 49 migrations, two clean disposable databases, 11
matching freeze artifacts, identical database-derived hashes, and no drift in
the historical checkpoint. The manifest is compared by exact bytes and remains
non-self-referential.

| Reproducibility receipt        | State                                                            |
| ------------------------------ | ---------------------------------------------------------------- |
| Round 3H migration fingerprint | pass: all 45 protected migration hashes match                    |
| Round 3H checkpoint validation | pass in the complete local database suite                        |
| Clean rebuild count            | 2 PostgreSQL 17 disposable databases                             |
| Freeze artifact equality       | true: all 11 files match across both builds and committed copies |
| Overall reproducibility pass   | true                                                             |

Both builds return `DATABASE_TEST_PASS=true` and
`ROUND3I_FREEZE_EXPORT_PASS=true`. The comparison receipt returns
`CLEAN_REBUILD_COUNT=2`, `ROUND3I_FREEZE_ARTIFACT_COUNT=11`,
`ROUND3I_FREEZE_REPRODUCIBILITY_PASS=true`, and `REPRODUCIBILITY_PASS=true`.
Byte comparison against the committed candidate directory also reports no
mismatch.

The 5,184-line complete-suite log at `/private/tmp/round3i-test-5.log` has
SHA-256
`76c69f037c61f26c0cecbc953f212441af960714a28e10fbcf3b4ff9e64d4353`.
That run exercised 33 Round 3I rejection fixtures. Two explicit
language-countability fixtures were added afterward, bringing the final source
to 35 without changing migrations or deterministic exports. Therefore the
artifact reproducibility result remains valid, while the exact-candidate remote
PostgreSQL 17 receipt must still demonstrate 35/35.

A later rerun was started only after splitting the catalog-count stdout into
71 relational constraints, 31 table triggers, and two event triggers. The host
ran out of disk during that rerun's second build, so its partial output is not
used as reproducibility evidence. The positive receipt rests on the earlier
complete exit-zero two-build run and independent 11-file comparisons. The exact
candidate's remote PostgreSQL 17 job must rerun the final script on a fresh
runner.
