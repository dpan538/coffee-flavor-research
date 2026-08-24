# Round 2B retrieval baselines

Date: 2026-08-24

Model: `model.round2b.deterministic_retrieval_v1`

Status: frozen held-out ablation complete

## Retrieval contract

Every query passes through `normalization.en_v1` before candidate generation.
Candidate tiers are ordinal precedence rules; they are not sensory weights or
probabilities.

| Baseline | Maximum tier             | Candidate rule                                                                          |
| -------- | ------------------------ | --------------------------------------------------------------------------------------- |
| A        | Approved preferred exact | Normalized query exactly matches a current active preferred lexicalization.             |
| B        | Approved lexical variant | Baseline A plus an exact match to a current active approved variant.                    |
| C        | PostgreSQL trigram       | Baseline B plus canonical-dictionary `pg_trgm` fallback at the frozen `0.35` threshold. |
| D        | Typed graph expansion    | Baseline C plus one allowlisted canonical relation hop from a direct seed.              |

Tier C runs only when no exact A/B candidate exists. Tier D cannot create a
candidate without an A/B/C seed. The one-hop graph policy allows outgoing
`composite_has_component`, outgoing `consumer_reference_for`, incoming and
outgoing `broader_than`, and symmetric `sensory_neighbour`. It excludes
source-scheme edges, corpus co-occurrence, process identity, and transitive
closure.

The function returns at most five governed concepts. If no candidate survives,
it emits exactly one `UNRESOLVED` sentinel. Each candidate persists its tier,
mapping type, orthographic similarity when applicable, graph path when
applicable, and structured signal ledger. No unexplained aggregate score is
calculated.

## Held-out ablation

The authoritative comparison uses 225 held-out cases: 209 adjudicated
resolvable and 16 adjudicated `U`. Recall, MRR, and nDCG exclude the `U` cases;
coverage and abstention use all 225. Values below are rounded to six decimal
places from the frozen database rows.

| Baseline | Recall@1 | Recall@3 | Recall@5 |      MRR |   nDCG@5 |
| -------- | -------: | -------: | -------: | -------: | -------: |
| A        | 0.080542 | 0.080542 | 0.080542 | 0.162679 | 0.127024 |
| B        | 0.082137 | 0.082137 | 0.082137 | 0.167464 | 0.130247 |
| C        | 0.279107 | 0.319777 | 0.319777 | 0.478469 | 0.357894 |
| D        | 0.279107 | 0.436204 | 0.440989 | 0.488038 | 0.454819 |

| Baseline | Coverage | Abstention rate | Abstention error | Unsafe non-abstention | Median candidates |
| -------- | -------: | --------------: | ---------------: | --------------------: | ----------------: |
| A        | 0.151111 |        0.848889 |         0.916230 |                     0 |                 0 |
| B        | 0.155556 |        0.844444 |         0.915789 |                     0 |                 0 |
| C        | 0.493333 |        0.506667 |         0.868421 |              0.062500 |                 0 |
| D        | 0.493333 |        0.506667 |         0.868421 |              0.062500 |                 0 |

Baseline B adds only a small approved-variant gain over preferred exact lookup.
Trigram fallback materially raises coverage and first-result recall, but it
also returns a candidate for one of the 16 genuinely unresolved cases. Typed
graph expansion leaves first-result recall and coverage unchanged while
improving Recall@3, Recall@5, and nDCG@5 by exposing additional defensible
one-hop candidates.

The median candidate count is zero for every baseline because more than half
of held-out cases abstain. Mean held-out candidate counts from the independent
benchmark are `0.1511`, `0.1556`, `0.5689`, and `1.1733` for A through D.

The large Baseline D abstention error (`0.868421`) means 99 of 114 abstentions
were adjudicated resolvable. It is evidence that the deterministic dictionary
remains deliberately sparse, not a reason to force a nearest match.

The qrel pool may include existing governed but non-active candidate concepts
to measure ontology information loss. Model outputs are restricted to active
concepts, so those qrels can lower recall without becoming candidates or
triggering ontology promotion.

## Candidate-set ablation before grading

Candidate counts exclude the `UNRESOLVED` sentinel.

| Baseline | Held-out candidates | Held-out abstentions | Interpretation                                                           |
| -------- | ------------------: | -------------------: | ------------------------------------------------------------------------ |
| A        |                  34 |                  191 | Preferred exact coverage only.                                           |
| B        |                  35 |                  190 | One held-out case gains an approved-variant candidate.                   |
| C        |                 128 |                  114 | Orthographic fallback materially expands candidate coverage.             |
| D        |                 264 |                  114 | Graph expansion adds alternatives but cannot reduce seedless abstention. |

Development-case candidate counts show the same structural pattern: 11, 11,
43, and 84 candidates for A through D, with 64, 64, 38, and 38 abstentions.
This accounting alone does not establish relevance; the adjudicated metric
tables above are the outcome measure.

## Exact headline values

The final receipt uses Baseline D held-out values without rounding:

```text
RECALL_AT_1=0.27910685805422647528
RECALL_AT_3=0.43620414673046251994
RECALL_AT_5=0.44098883572567783094
MRR=0.48803827751196172249
NDCG_AT_5=0.45481865642031275923
COVERAGE=0.49333333333333333333
ABSTENTION_RATE=0.50666666666666666667
ABSTENTION_ERROR=0.86842105263157894737
UNSAFE_NONABSTENTION=0.0625
MEDIAN_CANDIDATE_SET_SIZE=0
```

These are language-retrieval metrics against graded semantic judgments. They
are not coffee flavor accuracy.

## Implementation and safety result

The model freeze is commit
`a6abb4112cff3fc436b1613c37f9b40f51e65144` at
`2026-08-24T07:48:49Z`. The 300-case selection, candidate pool, and retrieval
rules were frozen before review. Held-out rows are not tuning-eligible, and the
threshold was not tuned after inspecting either split.

```text
EXACT_BASELINE_PASS=true
VARIANT_BASELINE_PASS=true
TRIGRAM_BASELINE_PASS=true
GRAPH_EXPANSION_PASS=true
UNRESOLVED_PASS=true
TRIGRAM_THRESHOLD=0.35
TOP_K=5
WEIGHTED_COMPOSITE_SCORE=false
PGVECTOR_REQUIRED=false
EMBEDDING_BASELINE_RUN=false
```

Latency, index behavior, and trigram false-neighbor patterns are reported in
[the trigram benchmark](05_TRIGRAM_BENCHMARK.md) and
[the query-plan review](10_QUERY_PLAN_REVIEW.md).
