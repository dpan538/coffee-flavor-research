# Database-freeze expected state

Frozen on 2026-08-26 before any Round 3I acquisition or import. The exact
source checkpoint is `ccf5769cb5e1f165209e59beaef9fe54017265f5`; the
machine-readable contract is
`db/data/round3i/database_freeze_expected_state.tsv`. Thresholds may not be
lowered after source inspection merely to produce a freeze. A demonstrably
invalid threshold requires a separate, committed decision record and remains
visible in the revision registry.

## Baseline

Round 3H left every non-language model-prebuild hard gate passing. The database
contains 130 canonical concepts, 92 active sensory attributes, nine independent
coffee-sensory source families, 4,344 source-local sensory rows, 230
samples/configurations, 181 empirical coverage cells, 96 reviewed relationship
claims, 20 model-prebuild features, and 12 federated partitions. The ontology,
model, human-study, and frontend prohibition flags are unchanged.

The exact unresolved hard gaps are three contemporary tasting-language source
families, 500 contemporary documents, 723 governed unique normalized
expressions, and two independent source-authored Simplified-Chinese lexical
families. Simplified-Chinese sensory depth of 200 expressions and a fourth
range with cross-source evidence are preferred rather than mandatory.

## Minimum freeze state

Every mandatory model-prebuild gate must pass. Source annotation, rights,
privacy, file hashes, and relationship provenance must each be complete at
`1.0000`. Canonical counts must remain 130 and 92. Schema integrity, global
data quality, leakage control, deterministic artifact generation, two clean
PostgreSQL 17 rebuilds, and both remote CI jobs must pass.

The freeze layer must declare current read surfaces, identify historical or
research-only surfaces, produce eleven deterministic inventory hashes, and
bind the release manifest to the exact repository SHA without a self-reference.
No model run, embedding, real-human collection, pgvector dependency, product
frontend modification, or canonical ontology change is permitted.

## Preferred freeze state

Preferred language breadth is five contemporary source families, 1,500 new
documents, 3,500 governed expressions, three source-authored Simplified-Chinese
families, and 200 Simplified-Chinese sensory expressions. Four ranges should
have cross-source evidence when a defensible reviewed path exists. Preferred
misses produce warnings; they never justify fabricated expressions or forced
relationship promotion.

## Observed and delta

At freeze time, Round 3I has not imported data and the result is
`DATABASE_FREEZE_BLOCKED_BY_DATA_GAP`. The four hard language gaps are measured
independently, while the otherwise passing evidence and governance planes must
not regress. Acquisition stops when all hard gates pass or after three
consecutive targeted no-gain batches.

## Freeze decision

`audit.run_research_database_freeze_gate()` will be authoritative once added by
a forward migration. Only an exact, green main checkpoint may become
`FROZEN`; a feature checkpoint remains `FREEZE_CANDIDATE`. If all hard gates
pass but preferred depth remains incomplete, the candidate may proceed with
explicit warnings. Otherwise no freeze tag or positive readiness state is
allowed.
