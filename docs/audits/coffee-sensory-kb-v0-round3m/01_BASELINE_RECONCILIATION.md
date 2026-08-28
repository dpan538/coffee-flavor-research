# Baseline reconciliation audit

The required source commit was verified locally and remotely before the Round
3M branch was created. The clean source worktree was
`/private/tmp/coffee-flavor-round3l-sanitized`; the unrelated dirty main
worktree was left untouched.

The Round 3L public builder reran against the persistent restricted freeze and
passed every pinned count and receipt hash. `diff -rq` found only the
hand-authored public README absent from the regenerated output directory.

```text
COMMAND=python -B db/scripts/build-round3l-public-checkpoint.py --restricted-root <owner-controlled-root> --output-dir /private/tmp/round3m-baseline-recompute --gate-receipt <authoritative-receipt>
RESULT=ROUND3L_PUBLIC_CHECKPOINT_PASS
ARTIFACT_COUNT=848
ARTIFACT_BYTES=1327537497
STAGED_PUBLICATION_ROW_COUNT=26515
CANONICAL_PUBLICATION_ROW_COUNT=20994
STAGED_EFFECTIVE_CORE_CANDIDATE_COUNT=6754
```

`BASELINE_RECONCILIATION.json` records the exact expected/recomputed values,
the 131-to-11 route/family separation, and the missing machine-artifact blocker.
There is no baseline delta to explain and no historical receipt was overwritten.
