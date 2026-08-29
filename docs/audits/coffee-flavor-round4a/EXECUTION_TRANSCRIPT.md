# Execution transcript

1. Verified source/main SHAs, 29/0 history, clean promotion worktree, and source
   CI run `33202334916`.
2. Created remote backup ref and fast-forwarded main without force.
3. Verified exact-main CI run `33220393687`, then created the annotated release
   tag.
4. Created the isolated Round 4A branch at the promoted SHA.
5. Recomputed repository counts and generated the archive, usage, task-health,
   split, graph, candidate, event, and training-decision artifacts.
6. Implemented and tested the deterministic two-stage objective M and 5+3 UI.
7. Implemented the PWA shell and local-only synthetic event preview.
8. Ran the rollback-only pipeline smoke test.
9. Ran deterministic regeneration, full local frontend CI, 23 unit tests, the
   rollback-only pipeline smoke, 21 Playwright checks, and production prerender.
10. Ran the full PostgreSQL 17 harness against two separate empty disposable
    databases; all migration fingerprints, tests, dumps, and governed
    inventories matched.
11. Final commit, branch push, and remote branch CI: pending.

No external request, contract acceptance, purchase, participant collection,
model training, rights widening, corpus freeze, or migration change occurred.
