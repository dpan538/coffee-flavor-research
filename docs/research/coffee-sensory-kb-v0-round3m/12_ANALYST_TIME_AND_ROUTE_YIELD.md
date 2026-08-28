# Analyst time and route yield

Round 3L did not preserve an analyst-hour denominator suitable for historical
yield rates. `SOURCE_ROUTE_YIELD.tsv` therefore reports per-artifact staged
candidate yield but uses `NA` for prior descriptors per analyst hour.

Round 3M logs measured start/end timestamps, active minutes, automated runtime,
actor type, artifacts, candidates, and reviewed counts in
`db/data/round3m/ANALYST_TIME_LOG.tsv`. No historical hours are backfilled.

The current generated receipt measures `2026-08-28T04:56:44Z` through
`2026-08-28T08:09:06Z`, or 192.367 elapsed analyst-equivalent minutes. It covers
851 source/capture artifacts and 516 candidate decisions as one
`MULTIPLE_ROUTES` aggregate. Automated runtime remains
`NA_NOT_INSTRUMENTED_FROM_TASK_START`; no zero is substituted.

Human-reviewed descriptor yield per analyst hour remains `NA` because no human
or expert review occurred. Codex source-audit activity is identified as
machine-assisted and is never relabeled as qualified human review.

The stop-loss result is decisive: broad result and award routes receive zero
new acquisition budget. Targeted work is restricted to descriptor-bearing CoE
schema paths and an authoritative completed WCC scoresheet only if one is
actually found.

`LOW_YIELD_EXCLUSION_REGISTER.tsv` retains 11 named route classes, each with
`new_round3m_broad_acquisition_budget=0`. This is preserved negative evidence,
not deletion from the discovered census.
