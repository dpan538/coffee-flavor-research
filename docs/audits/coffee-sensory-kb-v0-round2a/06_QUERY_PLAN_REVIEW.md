# Round 2A query-plan review

Date: 2026-08-24

Status: `QUERY_PLAN_PASS=true`

## Review standard

`db/tests/round2a_query_plans.sql` runs
`EXPLAIN (ANALYZE, BUFFERS)` on the natural plan for each governed access
pattern. At this ontology size a sequential scan may be PostgreSQL's rational
choice; that alone is not a failure. The review looks for complete execution,
bounded traversal, sensible row cardinality, and absence of pathological loops
or accidental cross products.

The suite then disables sequential and bitmap scans transaction-locally for
four targeted queries. This does not benchmark an artificial production
configuration; it proves that each purpose-built index is a valid executable
access path.

## Plan inventory

| Plan label                                     | Access pattern                                                | Warm observed execution time | Result |
| ---------------------------------------------- | ------------------------------------------------------------- | ---------------------------: | ------ |
| `exact_concept_lookup_natural`                 | Stable-key concept lookup for `sensory.grapefruit`            |                     0.116 ms | Pass   |
| `lexical_candidate_resolution_natural`         | `kb.retrieve_lexical_candidates('grapefruit', 'en', 5, 0.35)` |                    16.421 ms | Pass   |
| `canonical_broader_narrower_traversal_natural` | Recursive traversal below `category.citrus`                   |                     0.324 ms | Pass   |
| `canonical_neighbour_lookup_natural`           | Current neighbors of `composite.earl_grey`                    |                     0.334 ms | Pass   |
| `project_multi_parent_traversal_natural`       | Recursive ancestor paths in the project scheme                |                     1.452 ms | Pass   |
| `source_scheme_projection_natural`             | Full WCR partial projection                                   |                     0.304 ms | Pass   |
| `concept_provenance_natural`                   | Concept-and-role support lookup                               |                     0.062 ms | Pass   |
| `active_scheme_source_natural`                 | Active schemes by source version                              |                     0.013 ms | Pass   |
| `scheme_reverse_edge_natural`                  | Parent lookup by active child node                            |                     0.106 ms | Pass   |
| `scheme_mapping_by_concept_natural`            | Current source-scheme mappings by canonical concept           |                     0.165 ms | Pass   |

## Forced index assertions

| Access path                                    | Required index                                       | Runtime result |
| ---------------------------------------------- | ---------------------------------------------------- | -------------- |
| Concept provenance by concept and support role | `evidence.concept_support_concept_role_idx`          | Pass           |
| Active scheme by source version                | `evidence.concept_scheme_active_source_version_idx`  | Pass           |
| Active reverse edge traversal                  | `evidence.concept_scheme_edge_active_child_idx`      | Pass           |
| Active scheme mapping by concept               | `evidence.concept_scheme_mapping_active_concept_idx` | Pass           |

Existing Round 1 indexes continue to cover trigram lexical search, active
lexicalization lookup, concept type/lifecycle lookup, canonical relation
subject/object traversal, and source-support joins. Round 2A adds only indexes
with a demonstrated governance or traversal purpose.

## Result

```text
POSTGRES_VERSION=17.11 (Debian)
QUERY_PLAN_PASS=true
```

The suite emitted `ROUND2A_QUERY_PLAN_PASS=true`. Natural and forced-index plans
completed without pathological loops or accidental cross products. Timings are
single warm observations from the disposable validation database, not a
latency guarantee or benchmark; buffer details remain in the command output.
