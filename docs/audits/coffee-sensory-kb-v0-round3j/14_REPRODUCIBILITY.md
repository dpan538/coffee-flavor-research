# Reproducibility

`db/scripts/generate-round3j-global-corpus.py` deterministically regenerates
the TSVs, source manifests, hashes, and global manifest from committed inputs.
The verifier checks every generated artifact and admitted source-file hash.

GitHub Actions run `33050779740` on implementation SHA
`c9da8a797008a33773e7e6e8c28f1e5b3d09e377` used PostgreSQL 17.11 and
reported:

- `CLEAN_REBUILD_COUNT=2`
- `ROUND3I_FREEZE_REPRODUCIBILITY_PASS=true`
- `REPRODUCIBILITY_PASS=true`
- `CI_VERIFY_DATABASE_PASS=true`

The local deterministic artifact replay also reported zero generated-artifact
drift and zero nondeterminism. Reproducibility is therefore true for that
implementation checkpoint. The documentation-only closeout commit is subject
to the same exact-sha CI gate.
