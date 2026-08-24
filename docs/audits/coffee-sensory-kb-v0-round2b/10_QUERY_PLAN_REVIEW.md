# Round 2B query-plan review

Date: 2026-08-24

Status: `QUERY_PLAN_PASS=true`

## Review standard

The source-controlled
[query-plan suite](../../../db/tests/round2b_query_plans.sql) runs
`EXPLAIN (ANALYZE, BUFFERS)` for deterministic exact lookup, trigram candidate
generation, typed graph expansion, explicit abstention, corpus frequency,
co-occurrence, and audit persistence. The index contract is defined by the
[normalization/statistics schema](../../../db/013_round2b_normalization_statistics.sql)
and the
[retrieval/audit schema](../../../db/014_round2b_retrieval_and_audit.sql).

At this pilot scale, a sequential scan can be PostgreSQL's rational natural
choice. The review asks whether the complete query is bounded, whether indexes
remain executable where intended, and whether any join shape is already
pathological. Transaction-local forced plans are access-path diagnostics only.
They are not production configurations, comparable latency experiments, or an
index-superiority test.

The full PG17 harness emitted `ROUND2B_QUERY_PLAN_PASS=true` and
`DATABASE_TEST_PASS=true`. Its private log SHA-256 is
`ed5644ddf7af137a8c18b6d3cc85e33aff9a519aa8ca6543769abe4ac506044e`.
The 300-case follow-up benchmark is documented in
[the trigram audit](05_TRIGRAM_BENCHMARK.md); its aggregate/plan receipt SHA-256
is `b7df85626335c6c2ece4e524fe6757e23fdf96f4c2e770ef5e6eb4fc387bcd75`.

## Full-harness natural plans

These are single warm observations from the disposable PostgreSQL 17.11
database. They are not the repeated latency distribution reported by the
300-case benchmark.

| Plan label                                   | Result rows | Top-level access shape                               | Buffers           | Execution time | Result                |
| -------------------------------------------- | ----------: | ---------------------------------------------------- | ----------------- | -------------: | --------------------- |
| `audit_evaluation_join_natural`              |           0 | Sort over empty audit/evaluation joins               | shared hit 7      |       0.114 ms | Pass, structural only |
| `persisted_signal_ledger_natural`            |           0 | Sort over empty persisted-ledger joins               | shared hit 17     |       0.185 ms | Pass, structural only |
| `exact_normalized_dictionary_lookup_natural` |           1 | Indexed nested loops plus final sort                 | shared hit 119    |       0.694 ms | Pass                  |
| `exact_callable_natural`                     |           1 | Deterministic retrieval function scan                | shared hit 1,949  |       8.201 ms | Pass                  |
| `canonical_dictionary_knn_natural`           |          20 | Semi-join, top-N sort                                | shared hit 6,446  |       3.864 ms | Pass                  |
| `trigram_callable_natural`                   |           1 | Deterministic retrieval function scan                | shared hit 2,102  |       6.944 ms | Pass                  |
| `typed_graph_expansion_natural`              |           2 | Bounded relation/policy join plus sort               | shared hit 34     |       0.291 ms | Pass                  |
| `typed_graph_callable_natural`               |           3 | Deterministic retrieval function scan                | shared hit 1,121  |       5.826 ms | Pass                  |
| `explicit_unresolved_callable_natural`       |           1 | Deterministic retrieval function scan                | shared hit 2,104  |       6.609 ms | Pass                  |
| `unresolved_corpus_frequency_natural`        |          25 | Aggregate 5,564 occurrences, top-N limit             | shared hit 197    |      11.403 ms | Pass                  |
| `expression_frequency_natural`               |         100 | Statistic scan, keyed expression joins, top-N limit  | shared hit 8,655  |       3.489 ms | Pass                  |
| `npmi_neighbourhood_natural`                 |          20 | Pair scan, keyed expression joins, final filter/sort | shared hit 27,990 |       8.722 ms | Pass; monitor growth  |

The first two plans executed before a frozen evaluation result set was
persisted and therefore returned zero rows. They prove SQL and join-path
closure only; their timings do not characterize a populated 300-case audit.
The repeated benchmark covers the live retrieval function, not these empty
persistence joins.

## Natural planner findings

### Exact lookup

The exact normalized dictionary lookup used
`normalized_expression_trgm_knn_idx` with an equality index condition, then
keyed normalization, lexicalization, expression, mapping-type, and concept
lookups. PostgreSQL rechecked 13 GiST candidates and returned one governed row.
The final sort preserves mapping precedence and stable-key determinism.

### Canonical trigram lookup

For the complete governed dictionary KNN query, PostgreSQL naturally scanned
1,777 normalized-expression identities, used the pipeline key index, applied a
semi-join to the 115 approved dictionary expressions, and performed a top-N
sort. It did not use the trigram GiST index for the `<->` order in this complete
join shape. The 3.864 ms source-harness observation and the independent 3.801
ms follow-up observation are consistent at pilot scale, but they are not a
guarantee that the plan remains appropriate as the observed-expression table
grows.

The follow-up plan had 6,446 shared-buffer hits and no reported reads. A pure
isolated `<-> LIMIT` query can use the GiST KNN index, while the governed
dictionary join and deterministic secondary ordering can lead the planner to a
scan and sort. Therefore this audit does not claim that the production callable
physically used GiST merely because the index exists.

### Typed graph expansion and abstention

The direct graph query returned two allowlisted one-hop neighbors in 0.291 ms.
The callable returned its direct seed plus two graph candidates in 5.826 ms.
The explicit hard-negative callable returned exactly one `UNRESOLVED` row in
6.609 ms. These plans preserve bounded one-hop traversal and abstention; no
scheme edge, process identity, or corpus co-occurrence becomes a canonical
sensory relation.

### Corpus statistics

The unresolved-frequency query grouped all 5,564 normalized occurrences into
1,713 unresolved normalized expressions before taking 25 rows; it completed in
11.403 ms. The frequency view scanned 1,713 versioned statistic rows and joined
stable normalized-expression identities before taking 100 rows; it completed
in 3.489 ms.

The NPMI neighborhood query scanned 4,600 versioned pair measurements and made
keyed lookups for both endpoints before filtering to 20 rows. Its 27,990 shared
hits and 8.722 ms execution time are acceptable for this pilot but are the
clearest growth-monitoring point. NPMI remains corpus evidence and is not
materialized as a sensory-neighbor edge.

## Forced access-path diagnostics

The source harness copied exactly 115 governed dictionary expressions into
separate transaction-local tables. It then disabled sequential scans only for
the diagnostic and inspected independent GiST and GIN operator classes.

| Diagnostic                                   | Access path                               | Rows | Buffers      | Execution time |
| -------------------------------------------- | ----------------------------------------- | ---: | ------------ | -------------: |
| `forced_gist_knn_not_superiority_claim`      | GiST index scan ordered by `<->`          |   10 | local hit 6  |       0.080 ms |
| `forced_gin_threshold_not_superiority_claim` | GIN bitmap index/heap scan, recheck, sort |    2 | local hit 24 |       0.045 ms |

The harness's GIN visibility check set a transaction-local threshold of `0.30`
for its controlled spelling fixture; both copied tables had two candidates at
that diagnostic threshold. This was not threshold selection or calibration.
The retrieval policy and the 300-case benchmark remained fixed at `0.35`, and
no result from the `0.30` visibility check was used to tune them.

The repeated `0.35` follow-up supplied the policy-level semantic comparison:
KNN-top-20-then-threshold and GIN-`%`-then-sort had identical candidate sets and
ranks for all 300 cases because no case had more than four passing expressions.
Its natural GIN plan chose a sequential scan over the 115-row temporary table
(`0.170 ms`, local hit 4); the forced GIN diagnostic used its bitmap index
(`0.022 ms`, local hit 22). The natural governed KNN shape again used
scan/semi-join/sort (`3.801 ms`, shared hit 6,446). Those observations describe
planner choices under different query semantics and table shapes. Their times
must not be compared as evidence that one index is superior.

## Index and performance conclusion

The pilot has no pathological retrieval, traversal, frequency, or
co-occurrence plan. Exact, trigram, graph, unresolved, frequency, NPMI, audit,
and signal-ledger SQL all executed. The natural planner sensibly preferred
scans for some small relations; the forced diagnostics proved that both trigram
operator classes are executable.

The canonical dictionary KNN join and the NPMI endpoint-filter shape should be
re-inspected when corpus or dictionary cardinality grows. That is a monitoring
requirement, not authorization to redesign the schema, tune the threshold, or
replace the deterministic baseline.

```text
POSTGRES_VERSION=17.11
PG_TRGM_VERSION=1.6
QUERY_PLAN_PASS=true
THRESHOLD_TUNING_PERFORMED=false
INDEX_SUPERIORITY_CLAIMED=false
```
