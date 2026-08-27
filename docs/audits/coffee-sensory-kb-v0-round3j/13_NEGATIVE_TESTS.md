# Negative tests

`db/scripts/test-round3j-global-corpus.py` implements 29 offline checks,
including every required rights, mirror, source-authorship, preference,
evaluation-only, class-closure, scale-gate, and no-model condition. The test
must pass in local verification and PostgreSQL-independent CI.
