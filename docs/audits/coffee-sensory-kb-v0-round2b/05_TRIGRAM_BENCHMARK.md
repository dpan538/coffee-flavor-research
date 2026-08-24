# Round 2B trigram benchmark

Date: 2026-08-24

Status: `TRIGRAM_BASELINE_PASS=true`

## Scientific boundary

This benchmark measures deterministic language retrieval. Industry expressions
are language observations, trigram similarity is orthographic similarity, and
the relevance grades below are retrieval-review judgments. None of these
measurements is coffee flavor accuracy, perceptual distance, or evidence for a
canonical sensory relation.

The benchmark did not tune the `0.35` trigram threshold, change `top_k=5`, add a
weighted composite score, use embeddings, call an LLM at retrieval time, or
promote a corpus expression into the ontology. The implemented A--D order and
signal ledger are defined by the
[retrieval and audit schema](../../../db/014_round2b_retrieval_and_audit.sql)
and tested by the
[retrieval contract suite](../../../db/tests/round2b_retrieval.sql).

## Frozen inputs and environment

The source-controlled
[audit selector](../../../db/scripts/generate-round2b-audit.py) produced 300
unique normalized English expressions: 75 development cases and 225 held-out
cases. Development rows alone are tuning-eligible; every held-out row records
`tuning_eligible=false`. This run inspected both splits without changing any
retrieval rule or threshold.

| Receipt                               | Value                                                                     |
| ------------------------------------- | ------------------------------------------------------------------------- |
| Audit-case TSV SHA-256                | `0401ae2c3759044d4b9f5ab16ea1f374e27399080fc14717e27f79d0d96f1609`        |
| Frozen candidate-pool TSV SHA-256     | `00b087cabd36d1b50a258624e79e14ea10b3c135969143ca56c967e29c95cd45`        |
| Independent Reviewer-2 ledger SHA-256 | `ed1ce352de996711182b2bf9ac36bbd05c3d4e4faf0131aaf23906c68458219e`        |
| Candidate-model freeze                | `2026-08-24T17:48:49+10:00` at `a6abb4112cff3fc436b1613c37f9b40f51e65144` |
| Benchmark SQL SHA-256                 | `0dea5f4d24bddac8c0d8a038ce113e713cdb8b722b9266973bbe4728d6dcbd58`        |
| Aggregate/plan output SHA-256         | `b7df85626335c6c2ece4e524fe6757e23fdf96f4c2e770ef5e6eb4fc387bcd75`        |

The disposable database was
`coffee_sensory_kb_v0_round2b_final_d90b`, running PostgreSQL `17.11` and
`pg_trgm` `1.6`. The run retained the server defaults observed in the receipt:
JIT on, `shared_buffers=128MB`, `effective_cache_size=4GB`,
`random_page_cost=4`, `effective_io_concurrency=1`, and
`track_io_timing=off`. The transaction set only a five-second lock timeout, a
15-minute statement timeout, and `pg_trgm.similarity_threshold=0.35` to make
the temporary GIN operator use the same declared threshold. All loaded text,
candidate output, latency rows, and index copies were temporary, and the final
transaction was rolled back. No private phrase inventory was written to the
repository or emitted by the aggregate receipt.

## Latency method

The run used one server session and deterministic case ordering.

1. Materialize all 300 cases under each A--D baseline once for candidate-set
   accounting: 1,200 unmeasured calls.
2. Execute two complete unrecorded warm-up passes: 2,400 calls.
3. Execute seven measured passes: 8,400 calls.
4. Fully consume each set-returning function result inside the timed interval.
   Record `clock_timestamp()` elapsed time server-side, then insert the timing
   row outside that interval.
5. Take the median of each case's seven observations. Report p50, p95, and p99
   over the 300 per-case medians with `percentile_cont`.

The run therefore made 12,000 retrieval calls, of which 8,400 were measured.
It is a warm-cache, server-side benchmark. It excludes client/network latency
and is not a cold-start or service-level guarantee.

## Candidate-set size and abstention

Candidate counts exclude the single explicit `UNRESOLVED` sentinel row.

| Baseline | Split       | Cases | Total candidates |  Mean | Median | p95 | Max | Abstentions | Abstention rate |
| -------- | ----------- | ----: | ---------------: | ----: | -----: | --: | --: | ----------: | --------------: |
| A        | development |    75 |               11 | 0.147 |      0 |   1 |   1 |          64 |          0.8533 |
| A        | held-out    |   225 |               34 | 0.151 |      0 |   1 |   1 |         191 |          0.8489 |
| B        | development |    75 |               11 | 0.147 |      0 |   1 |   1 |          64 |          0.8533 |
| B        | held-out    |   225 |               35 | 0.156 |      0 |   1 |   1 |         190 |          0.8444 |
| C        | development |    75 |               43 | 0.573 |      0 |   2 |   2 |          38 |          0.5067 |
| C        | held-out    |   225 |              128 | 0.569 |      0 |   2 |   3 |         114 |          0.5067 |
| D        | development |    75 |               84 | 1.120 |      0 |   4 |   4 |          38 |          0.5067 |
| D        | held-out    |   225 |              264 | 1.173 |      0 |   4 |   5 |         114 |          0.5067 |

The complete candidate-count histograms are:

| Baseline | Development (`candidate count:cases`) | Held-out (`candidate count:cases`) |
| -------- | ------------------------------------- | ---------------------------------- |
| A        | `0:64, 1:11`                          | `0:191, 1:34`                      |
| B        | `0:64, 1:11`                          | `0:190, 1:35`                      |
| C        | `0:38, 1:31, 2:6`                     | `0:114, 1:96, 2:13, 3:2`           |
| D        | `0:38, 2:31, 3:2, 4:4`                | `0:114, 2:91, 3:3, 4:12, 5:5`      |

Tier D increased the information returned for cases with a direct seed but did
not reduce Tier C abstention: one-hop graph expansion cannot begin without a
direct A, B, or C candidate. This is the intended ordinal policy, not a reason
to force a nearest match.

## Retrieval latency

| Baseline | Cases | p50 ms | p95 ms | p99 ms | Maximum ms |
| -------- | ----: | -----: | -----: | -----: | ---------: |
| A        |   300 | 0.6150 | 0.6210 | 0.6230 |     0.6280 |
| B        |   300 | 0.6130 | 0.6191 | 0.6250 |     0.6280 |
| C        |   300 | 1.4015 | 1.5554 | 1.6732 |     1.8540 |
| D        |   300 | 1.4490 | 1.7461 | 1.8152 |     1.9250 |

The 102 cases that actually returned Tier C candidates had a per-case latency
p50 of `1.4350 ms` and p95 of `1.5460 ms` under Baseline C.

## Tier C orthographic behavior

Tier C appeared in 102 cases and returned 125 candidates. Returned trigram
similarity had median `0.4545`, p95 `0.6000`, minimum `0.3529`, and maximum
`0.6923`.

The following table joins those candidates to the frozen independent Reviewer-2
ledger. It is a diagnostic before final adjudication, not a gold audit set and
not a reported retrieval metric.

| Diagnostic grade | Semantics                                           | Candidates |  Share |
| ---------------- | --------------------------------------------------- | ---------: | -----: |
| 0                | Misleading or unrelated                             |          7 | 0.0560 |
| 1                | Indirect but potentially useful                     |          9 | 0.0720 |
| 2                | Defensible broader, narrower, or composite relation |         99 | 0.7920 |
| 3                | Same concept or valid lexicalization                |         10 | 0.0800 |

### False-neighbour and short-string patterns

Length is PostgreSQL `char_length` of the normalized expression. Empty cells
are zero observations, not inferred zero risk.

| Normalized length | Tier C candidates | Grade 0 | Grade 1 | Grade 2/3 | Grade-0 share |
| ----------------- | ----------------: | ------: | ------: | --------: | ------------: |
| 3 or fewer        |                 1 |       1 |       0 |         0 |        1.0000 |
| 4--5              |                 0 |       0 |       0 |         0 |           n/a |
| 6--8              |                 8 |       2 |       0 |         6 |        0.2500 |
| 9 or more         |               116 |       4 |       9 |       103 |        0.0345 |

Only one expression occupied the shortest bucket, so its result is a warning
case rather than an estimable error rate. Across all 300 Baseline C cases, the
length buckets contained respectively `1`, `32`, `42`, and `225` cases; Tier C
appeared in `1`, `0`, `7`, and `94`, while abstention occurred in `0`, `16`,
`19`, and `117`.

| Similarity band | Candidates | Grade 0 | Grade 1 | Grade 2/3 |
| --------------- | ---------: | ------: | ------: | --------: |
| 0.35--0.49      |         78 |       4 |       6 |        68 |
| 0.50--0.69      |         47 |       3 |       3 |        41 |
| 0.70--1.00      |          0 |       0 |       0 |         0 |

The higher observed band did not eliminate misleading or indirect candidates.
Orthographic similarity must therefore remain a candidate-generation signal,
never a semantic probability or sensory-neighbour score.

## GiST KNN and temporary GIN equivalence

The comparison projected the same 115 governed canonical-dictionary normalized
expressions into two access shapes:

- production KNN semantics: order by `<->`, take 20 expressions, then retain
  similarity at least `0.35`;
- temporary GIN semantics: set the transaction-local `%` threshold to `0.35`,
  retrieve every passing expression, sort by similarity and stable key, then
  take 20.

Across all 300 cases there were 190 passing expression occurrences, no top-20
set differences, and no rank differences. No case had more than four passing
expressions, so the two orderings were equivalent for this pilot.

This is not a general equivalence proof. `%` reads the session threshold,
whereas the retrieval function applies its explicit `REAL` threshold after a
KNN pre-limit. A larger dictionary with more than 20 qualifying expressions,
different floating-point boundary behavior, or an incorrectly configured GUC
can make the sets diverge. The comparison does not establish that GIN is faster
or better; natural and forced plan evidence is reviewed separately in
[the query-plan audit](10_QUERY_PLAN_REVIEW.md).

## Result

```text
POSTGRES_VERSION=17.11
PG_TRGM_VERSION=1.6
TRIGRAM_THRESHOLD=0.35
TRIGRAM_BASELINE_PASS=true
UNRESOLVED_PASS=true
THRESHOLD_TUNING_PERFORMED=false
INDEX_SUPERIORITY_CLAIMED=false
EMBEDDING_BASELINE_RUN=false
PGVECTOR_REQUIRED=false
```
