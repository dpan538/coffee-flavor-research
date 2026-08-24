# Round 2A semantic validation

Date: 2026-08-24

Status: `SEMANTIC_VALIDATION_PASS=true`

## Validation surfaces

Migration `011_ontology_validation.sql` creates four governed read models and a
47-check expected-zero validation contract:

- `kb.v_active_sensory_core` exposes one row per active sensory attribute and
  makes preferred-English-label cardinality auditable.
- `kb.v_scheme_projection` retains every current source-scheme node, including
  unmapped nodes, with source/version/licence/export fields.
- `kb.v_candidate_qualifiers` reports candidate qualifier governance data and
  counts prohibited numeric artifacts without creating a score.
- `kb.v_ontology_coverage` emits one deterministic value per concept,
  lifecycle, provenance-role, and scheme coverage metric.
- `audit.run_round2a_validation_queries()` returns `check_key`,
  `violation_count`, and `passed`; every row must be present, zero, and true.

The database test runner executes the full Round 1 suite before the Round 2A
negative, semantic, retrieval, and query-plan suites. This preserves the
validated canonical hierarchy and lexical behavior while extending the model.

## Required semantic boundaries

| Boundary                          | Implemented assertion                                                                                                                            | Runtime result |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| Active sensory range and snapshot | Count must be within 90--120 and exactly 92 for the frozen seed; candidate set must be exactly the eight reviewed keys                           | Pass           |
| Canonical hierarchy               | Round 1 acyclicity constraints and tests are rerun after all Round 2A migrations; no transitive closure is seeded                                | Pass           |
| Source-scheme hierarchy           | Current scheme graph must be acyclic; direct and indirect cycle insertions must fail                                                             | Pass           |
| Polyhierarchy                     | Project `sensory.metallic` must have more than one direct scheme parent without creating a cycle                                                 | Pass           |
| Scheme isolation                  | Canonical concept, lexicalization, and relation tables may not contain scheme ownership columns or foreign keys to scheme tables                 | Pass           |
| WCR projection safety             | Exactly 24 current nodes, 15 reviewed mappings, nine unmapped nodes, no hierarchy edges, no unsafe compound equivalences, and no exportable rows | Pass           |
| Process/sensory separation        | `sensory.fermented_character` and `process.fermentation` must remain distinct typed identities                                                   | Pass           |
| Affective separation              | `affective.pleasant` must remain an affective candidate with no sensory-dimension or numeric artifact                                            | Pass           |
| Qualifier safety                  | All six qualifiers remain candidates; `qualifier.bright` and peers must have no empirical pair value, projection value, or reference calibration | Pass           |
| Lexical ambiguity                 | `winey` retains two explicit senses and retrieval must return unresolved instead of forcing one                                                  | Pass           |
| Composite separation              | `Earl Grey` resolves to `composite.earl_grey`, never as a direct synonym of bergamot                                                             | Pass           |
| Candidate retrieval               | `pink-grapefruit` remains an unresolved expression attached to a distinct candidate, not an active grapefruit synonym                            | Pass           |
| Provenance closure                | Every required concept, relation, and assertion support resolves through source version and licence policy                                       | Pass           |
| Rights                            | WCR rows remain non-exportable and only the project scheme is production-exportable                                                              | Pass           |
| Stable dimensions                 | Six nonnumeric links only; no invented qualifier or affective measurements                                                                       | Pass           |
| Extension scope                   | `pgvector`/`vector` must not be installed                                                                                                        | Pass           |

## Failure-path tests

`db/tests/round2a_negative.sql` wraps every attempted mutation in a transaction
and requires the exact PostgreSQL SQLSTATE and named constraint:

| Attempted invalid operation                    | Required failure                                      |
| ---------------------------------------------- | ----------------------------------------------------- |
| Delete a source referenced by a source version | `23503`, `source_version_source_fk`                   |
| Delete a source version referenced by a scheme | `23503`, `concept_scheme_source_version_fk`           |
| Change a scheme's source version in place      | `23514`, `concept_scheme_source_version_immutable_ck` |
| Join edge endpoints from different schemes     | `23503`, `concept_scheme_edge_child_fk`               |
| Map a node through a different scheme          | `23503`, `concept_scheme_mapping_node_fk`             |
| Insert the inverse of an active scheme edge    | `23514`, `concept_scheme_hierarchy_cycle_ck`          |
| Insert a descendant-to-ancestor edge           | `23514`, `concept_scheme_hierarchy_cycle_ck`          |

The outer transaction rolls back, so negative tests cannot alter the retained
inventory. All seven operations failed with the expected SQLSTATE and named
constraint; `ROUND2A_NEGATIVE_PASS=true`.

## Retrieval tests

`db/tests/round2a_retrieval.sql` checks exact round trips for every active
preferred English label, exact-stage precedence over trigram fallback, the
`grapfruit` spelling fallback to grapefruit, explicit unresolved behavior for
`meteor fruit`, candidate safety for pink grapefruit, winey polysemy, and Earl
Grey composite resolution. Every assertion passed and the suite emitted
`ROUND2A_RETRIEVAL_PASS=true`.

## Validation result

```text
ROUND1_VALIDATION_CHECKS=31/31 zero violations
ROUND2A_VALIDATION_CHECKS=47/47 zero violations
ONTOLOGY_VALIDATION_PASS=true
SEMANTIC_VALIDATION_PASS=true
NEGATIVE_TEST_PASS=true
RETRIEVAL_PASS=true
```

All eight SQL suites passed against the final migration set in both fresh
PostgreSQL 17 databases.
