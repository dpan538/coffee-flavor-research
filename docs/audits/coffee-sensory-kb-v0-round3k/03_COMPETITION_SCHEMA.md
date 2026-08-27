# Competition schema audit

## Forward architecture

Four forward migrations implement Round 3K without changing the frozen 000-048
baseline:

- `049_round3k_competition_core.sql` creates normalized competition identity,
  edition, versioned rules and scoresheets, category and round, entry, coffee,
  lot, entry-coffee link, roast batch, and preparation service entities.
- `050_round3k_competition_evidence.sql` adds professional source snapshots and
  hashes, six-dimensional rights, preparation evidence, panels, judges,
  observations, structured scores, declared/published notes, descriptor
  assertions, and consensus lineage.
- `051_round3k_competition_corpus_mapping.sql` adds frozen checkpoints, privacy,
  expressions, mapping rules, qualified review, labels, targets, coassertions,
  acquisition outcomes, duplicate/repeat audits, training candidates, grouped
  split candidates, and Round 3K model-artifact prohibitions.
- `052_round3k_competition_views_gates.sql` adds current-decision, observed-core,
  model-eligible, auxiliary, concentration, coverage, label, leakage, metric,
  gate, and validation views/functions.

## Effective grain and lineage

The stable record key is series × edition × category × round × entry-or-lot ×
preparation service. Entry and lot are mutually exclusive service subjects.
Judge observations and structured scores are children of the service and cannot
multiply the effective record. Repeated rounds require explicit parent/repeat
lineage. Fresh-preparation, rule/scoresheet, source snapshot, file hash, and
rights decisions are mandatory admission evidence.

Detailed competition preparation services remain separate from the product's C0
projection. Source-native roast data remains separate from reviewed C1. Milk and
plant-milk services are auxiliary; signature/additive services and packaged RTD
products cannot enter the black-coffee core.

## Enforcement scope

Constraints and deferred/row triggers enforce version lineage, edition and
series scope, entry/lot identity, service semantics, current context, source and
panel lineage, assertion actor/type lineage, label cardinality and reviewer
requirements, duplicate groups, repeat links, rights-aware training candidates,
split grouping, and the Round 3K no-model boundary.

Native PostgreSQL 17 application passes. Relative to the frozen Round 3I
checkpoint, the final catalog adds 385 relational constraints and 36 user
triggers (421 combined); the receipt's `NEW_CONSTRAINT_COUNT` uses the requested
relational-constraint semantics and is therefore 385.
