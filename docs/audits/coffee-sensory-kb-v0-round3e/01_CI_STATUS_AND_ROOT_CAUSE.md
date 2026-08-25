# CI status and root-cause receipt

- Source main SHA: `52c29e53a8f3d3ab60b72f2a6e5f60419b6173e5`
- Source main run: `32807372976`
- Source main frontend job: success
- Source main PostgreSQL 17 job: success
- Active main blocker at source: false
- Historical failed runs reviewed: 6
- Root-cause classes: 2
- Round 3E CI fixes: 2 (unified fail-fast orchestration; deterministic
  generated-artifact cleanliness)

Five reviewed runs failed only at formatting. One run failed formatting and its
database rebuild because a negative-test helper was created after a trigger
fired; the helper ordering was repaired in a later commit and subsequent
database jobs passed. None of these historical failures is reported as active.

See `docs/research/coffee-sensory-kb-v0-round3e/01_CI_RELIABILITY_AUDIT.md`
for the run-by-run table.
