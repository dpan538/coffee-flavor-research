# Reproducibility and remote CI

Local Python 3.12.13 runs pass the direct Batch 6 generator, current descriptor
contract, complete current-artifact entrypoint, workflow classification, and
product inference suite. The product test invokes its generator again and
compares every generated file hash to the pre-run snapshot.

Remote run `33461527537` validates the parent checkpoint's full two-clean-
database PostgreSQL 17 replay. Recovery run `33468931133` validates frontend
and the current PostgreSQL 17 contract but fails the public diagnostic at a
macOS-only `/private/tmp` default. Its traceback classifies the defect as
`PATH_OR_WORKING_DIRECTORY`, not Python 3.12 language compatibility.

The bounded second recovery SHA `88cd394` uses `tempfile.gettempdir()` while
retaining the explicit environment override. Run `33470462970` passes frontend
in 1m21s, public artifacts in 3m54s under CPython 3.12, and the PostgreSQL 17
current contract in 18m19s. Matching historical run `33470462938` passes the
full two-clean-database replay in 35m01s. This exceeds the former 35-minute
unified boundary but completes inside the explicit 75-minute historical
budget, directly validating the decomposition. Final product-checkpoint runs
are recorded only after their actual conclusions.

The standalone Batch 6 diagnostic runs with `-X dev` and restores the accepted
artifact state on exit. The canonical determinism test remains the complete
ordered generator chain. Failed child generators now expose command, return
code, stdout, stderr, Python version, working directory, and relevant
environment.

```text
PRODUCT_BYTE_REPRODUCIBILITY_PASS=true
PRODUCT_PUBLIC_SAFE_PASS=true
MODEL_FILE_COUNT_DELTA=0
FORCE_PUSH_USED=false
```
