# Existing constraint inventory

PostgreSQL catalog counts after migration 038 are:

| Category                         | Count | Status                                      |
| -------------------------------- | ----: | ------------------------------------------- |
| primary key                      |   199 | database enforced                           |
| foreign key                      |   378 | database enforced                           |
| unique/candidate key             |   243 | database enforced                           |
| check                            |   550 | database enforced                           |
| constraint-trigger catalog entry |    14 | database enforced, including deferred gates |
| triggers                         |   138 | database enforced                           |

The permanent semantic registry contains 35 major project rules: 25 enforced by
PostgreSQL constraints/triggers, two by audit queries, four by CI and four by
curation policy. It covers lifecycle, promotion, public export, PII, model-run,
generated-artifact, reproducibility and the new non-inference gates.

## Enforcement findings

- Already enforced: keys, support reciprocity, graph cycles, export/PII,
  external-data model prohibitions, question validation, canonical freeze,
  range lifecycle, evidence, non-probability and subject XOR.
- Documented only by design: future-round delta packaging and additional-range
  user review. These are repository-governance decisions, not row-local facts.
- Intentionally not enforced as triggers: cross-cultural experiential
  equivalence, semantic tree completeness and whether a conceptual grouping is
  scientifically persuasive.
- Missing but enforceable: none among the 35 registered major rules at this
  checkpoint. Two rules are `DOCUMENTED_ONLY` because enforcement belongs to
  promotion review, not PostgreSQL.
