# Round 2B executive receipt

Date: 2026-08-24

Phase: rights-reviewed historical corpus and deterministic retrieval baseline

Status: `PHASE_STATUS=PASS`

## Outcome

Round 2B builds a provenance-preserving pilot from one licensed, pinned
Firstbloom repository snapshot. It treats tasting notes as language
observations, not objective flavor labels. The pilot includes 215 publisher
identities, 2,474 historical documents, 6,818 parsed fragment observations,
and 5,564 retained short occurrences. It does not scrape live roaster sites or
commit complete commercial tasting-note fields.

The deterministic retrieval stack implements approved preferred exact lookup,
approved variants, `pg_trgm` candidate generation, one-hop typed graph
expansion, a signal ledger, and explicit `UNRESOLVED`. No embedding, `pgvector`,
LLM runtime dependency, weighted sensory score, or automatic ontology promotion
is present.

## Frozen identity

| Item                       | Value                                                                |
| -------------------------- | -------------------------------------------------------------------- |
| Round 2A source SHA        | `2d864d56496c587cff5b6774e0ea41be8b416e6c`                           |
| Work branch                | `codex/coffee-sensory-kb-v0-round2b-corpus-20260824`                 |
| Corpus version             | `firstbloom-a6cb002-pilot-v1`                                        |
| Pinned Firstbloom SHA      | `a6cb0026d1af9642724793c799bbc48dc189ba35`                           |
| Deterministic model freeze | `a6abb4112cff3fc436b1613c37f9b40f51e65144` at `2026-08-24T07:48:49Z` |
| PostgreSQL                 | `17.11`                                                              |
| `pg_trgm`                  | `1.6`                                                                |
| `pgvector` required        | `false`                                                              |
| Embedding baseline run     | `false`                                                              |

## Corpus and resolution inventory

| Measure                                     | Frozen value |
| ------------------------------------------- | -----------: |
| Acquired corpus sources                     |            1 |
| Publisher identities                        |          215 |
| Products                                    |        2,383 |
| Historical documents                        |        2,474 |
| Parsed raw fragment observations            |        6,818 |
| Retained short occurrences                  |        5,564 |
| Hash-only occurrences                       |        1,254 |
| Unique retained raw expressions             |        2,124 |
| Unique normalized expressions               |        1,713 |
| Strictly resolved normalized identities     |           57 |
| Explicitly unresolved normalized identities |        1,656 |
| Strictly resolved occurrences               |        1,866 |
| Explicitly unresolved occurrences           |        3,698 |
| Ontology-extension candidates               |           11 |

Strict unique-identity resolution coverage is
`0.03327495621716287215`; occurrence coverage is
`0.33537023723939611790`. Normalized-phrase, trigram, graph, and polysemous
suggestions remain retrieval candidates and do not inflate those counts.

## Held-out retrieval outcome

Baseline D was evaluated on 225 held-out cases, of which 209 were adjudicated
resolvable and 16 genuinely unresolved. It reached Recall@1 `0.2791068581`,
Recall@3 `0.4362041467`, Recall@5 `0.4409888357`, MRR `0.4880382775`, and
nDCG@5 `0.4548186564`. Coverage was `0.4933333333`; abstention remained
`0.5066666667`. Among abstentions, `0.8684210526` were resolvable cases, while
unsafe non-abstention among genuinely unresolved cases was `0.0625`.

These are deterministic language-retrieval metrics against graded semantic
judgments. They are not coffee flavor accuracy.

## Governance result

- Fifteen source policies were reviewed: one `ALLOW_DERIVED_TERMS`, eight
  `BLOCKED`, three `MANUAL_ONLY`, and three `UNKNOWN` rows treated as blocked.
- The legacy metadata-only licence policy retains
  `production_export_allowed=false`. A narrower source policy permits
  redistribution of governed short derived terms and structured metadata; it
  never permits excluded raw commercial text.
- The 300-case audit has 75 development and 225 held-out cases, no synthetic
  padding, and `tuning_eligible=false` for every held-out case.
- Two independent Codex-assisted non-human reviews and one distinct
  Codex-assisted non-human adjudication produced the frozen relevance ledger.
  No human-review claim is made.
- Eleven corpus observations were queued for later ontology review: ten are
  open and `honey melon` is deferred. All retain
  `REQUIRES_COFFEE_SENSORY_EVIDENCE`; none was promoted. Fourteen adjudicated
  nearest-concept links preserve the comparison basis.
- The Round 2A canonical boundary remains unchanged at 130 concepts, 110 stored
  canonical relations, and 134 canonical lexicalizations.
- A fresh PostgreSQL 17.11 replay through the superseding migration 017 and the
  full SQL harness pass, including all 53 Round 2B expected-zero checks. The
  definitive two-rebuild comparison for this exact migration also passes with
  identical inventory hashes, and both temporary databases were removed.

## Verification receipt

```text
PHASE_STATUS=PASS

SOURCE_SHA=2d864d56496c587cff5b6774e0ea41be8b416e6c
WORK_BRANCH=codex/coffee-sensory-kb-v0-round2b-corpus-20260824
POSTGRES_VERSION=17.11
PG_TRGM_VERSION=1.6
PGVECTOR_REQUIRED=false
EMBEDDING_BASELINE_RUN=false

CORPUS_VERSION=firstbloom-a6cb002-pilot-v1
CORPUS_SOURCE_COUNT=1
CORPUS_ALLOWED_SOURCE_COUNT=1
CORPUS_BLOCKED_SOURCE_COUNT=11
CORPUS_DOCUMENT_COUNT=2474
RAW_OBSERVATION_COUNT=6818
UNIQUE_RAW_EXPRESSION_COUNT=2124
UNIQUE_NORMALIZED_EXPRESSION_COUNT=1713

RESOLVED_EXPRESSION_COUNT=57
UNRESOLVED_EXPRESSION_COUNT=1656
RESOLUTION_COVERAGE=0.03327495621716287215

AUDIT_SET_SIZE=300
RECALL_AT_1=0.27910685805422647528
RECALL_AT_3=0.43620414673046251994
RECALL_AT_5=0.44098883572567783094
MRR=0.48803827751196172249
NDCG_AT_5=0.45481865642031275923
ABSTENTION_RATE=0.50666666666666666667
ABSTENTION_ERROR=0.86842105263157894737

EXACT_BASELINE_PASS=true
VARIANT_BASELINE_PASS=true
TRIGRAM_BASELINE_PASS=true
GRAPH_EXPANSION_PASS=true
UNRESOLVED_PASS=true
CORPUS_STATISTICS_PASS=true
RIGHTS_REVIEW_PASS=true
QUERY_PLAN_PASS=true
MIGRATION_PASS=true
CLEAN_REBUILD_COUNT=2
ROUND2B_VALIDATION_CHECK_COUNT=53
REPRODUCIBILITY_PASS=true

ONTOLOGY_EXTENSION_CANDIDATE_COUNT=11
ONTOLOGY_EXTENSION_OPEN_COUNT=10
ONTOLOGY_EXTENSION_DEFERRED_COUNT=1
ONTOLOGY_EXTENSION_NEAREST_LINK_COUNT=14
AUDIT_RECEIPT=docs/audits/coffee-sensory-kb-v0-round2b/00_EXECUTIVE_RECEIPT.md
KNOWN_BLOCKERS=none
NEXT_RECOMMENDED_PHASE=independent human review and a newly rights-cleared multi-source contemporary corpus expansion before any optional embedding sub-round
```

The known limitations are material: one historical secondary source, no human
retrieval reviewers, no roaster-country metadata, no vocabulary convergence,
and no current/live corpus. See [known gaps](12_KNOWN_GAPS.md) for the complete
boundary. They constrain generalization but do not block the bounded Round 2B
deliverable.
