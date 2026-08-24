# 05 — Query-Plan Review

- Receipt date: 2026-08-24
- Server: PostgreSQL 17.11
- Suite: `db/tests/query_plans.sql`

All three access patterns were executed with `EXPLAIN (ANALYZE, BUFFERS)`.
The seed is intentionally tiny, so the suite records the natural plan and then
uses transaction-local planner settings to prove the KNN path without changing
schema or production configuration.

## Trigram lookup

Query: active English expressions ordered by
`normalized_text <-> 'grapfruit'`, then stable expression key, `LIMIT 5`.

The natural tiny-seed plan used:

```text
Bitmap Index Scan on lexical_expression_normalized_trgm_gist_idx
Bitmap Heap Scan on kb.lexical_expression
top-N heapsort for distance plus deterministic key tie-break
```

This confirms the intended GiST index participates naturally. With
`enable_seqscan=off` and `enable_bitmapscan=off` set locally inside the
read-only test transaction, PostgreSQL used:

```text
Index Scan using lexical_expression_normalized_trgm_gist_idx
Order By: normalized_text <-> 'grapfruit'
Incremental Sort for expression_key tie-break
```

GiST is retained instead of GIN because it can provide ordered trigram KNN
scans. The similarity value remains a lexical retrieval signal only.

## Typed graph traversal

The outgoing Earl Grey query naturally used:

```text
concept_key_uq
concept_relation_active_subject_type_idx
```

The incoming bergamot query naturally used:

```text
concept_key_uq
concept_relation_active_object_type_idx
```

Forced-plan JSON assertions also required both named relation indexes. In the
recorded run the queries returned two outgoing rows and one incoming row with
no disk reads; exact execution time is environment-dependent and is not used
as a performance claim.

Partial predicates contain only immutable row-local lifecycle tests. Current
timestamp validity and source semantics remain in query/view joins, avoiding
the research draft's invalid partial-index subquery pattern.

```text
TRIGRAM_INDEX_USED=true
TRIGRAM_KNN_PATH_PROVEN=true
GRAPH_SUBJECT_INDEX_USED=true
GRAPH_OBJECT_INDEX_USED=true
QUERY_PLAN_PASS=true
```
