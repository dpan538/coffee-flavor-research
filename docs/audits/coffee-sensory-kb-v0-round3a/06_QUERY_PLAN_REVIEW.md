# Query-plan review

## Scope

Representative PostgreSQL 17 `EXPLAIN (ANALYZE, BUFFERS)` plans are captured by `db/tests/round3a_query_plans.sql` for:

- exact preparation expression lookup;
- broader/parent traversal;
- narrower/child traversal;
- multi-source preparation provenance;
- source-specific roast projection and normalization;
- unresolved context labels;
- current corpus context coverage.

## Index contract

The test requires:

- `preparation_expression_normalized_uq`;
- `preparation_relation_object_type_idx`;
- `roast_expression_normalized_uq`;
- `roast_category_scheme_idx`;
- `observation_context_preparation_idx`;
- `observation_context_roast_idx`.

## Result

All representative queries complete in the millisecond range at the current scale. Exact and scheme lookups use unique or targeted indexes. Small seed tables may use sequential scans, which is appropriate. Coverage scans 2,474 pilot documents and uses the unique observation-context document index; measured execution remains trivial.

No planner switch is forced, and no micro-optimization claim is made. The purpose of the review is to detect pathological joins and missing access paths, not benchmark hardware.

```text
QUERY_PLAN_PASS=true
```
