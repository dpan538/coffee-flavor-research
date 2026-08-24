# 02 — Schema Implementation

- Receipt date: 2026-08-24
- Migration root: `db/`
- Execution contract: PostgreSQL 17 or newer, direct `psql`, `ON_ERROR_STOP`

## Dependency-ordered migration tree

| migration                          | responsibility                                                                                                                      |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `000_extensions.sql`               | Reject servers older than PostgreSQL 17 and enable `pg_trgm`.                                                                       |
| `001_reference_and_schemas.sql`    | Create the six logical schemas and controlled semantic registries.                                                                  |
| `002_core_schema.sql`              | Create language-neutral concepts, expressions, lexicalizations, typed relations, dimensions, and qualitative dimension links.       |
| `003_evidence_corpus_ml_audit.sql` | Create rights/provenance, empirical, projection, raw corpus, model-run, candidate-signal, review, lifecycle, and promotion records. |
| `004_constraints_and_triggers.sql` | Enforce cross-row and cross-table scientific invariants that PostgreSQL `CHECK` constraints cannot express.                         |
| `005_indexes_and_views.sql`        | Add access-pattern indexes, current/rights-filtered views, and the lexical retrieval prototype.                                     |
| `006_reference_seed.sql`           | Insert the small, independently authored deterministic semantic fixture.                                                            |
| `007_validation_queries.sql`       | Install and run the machine-readable expected-zero validation contract.                                                             |

The application has no hidden migration dependency. The scripts under
`db/scripts/` enumerate exactly one migration for each prefix `000` through
`007` and refuse incomplete or ambiguous trees.

## Domain boundaries

```text
ref       controlled values and their declared semantics
kb        canonical identities, language, graph, and measurement constructs
evidence  sources, versions, rights, support, datasets, and empirical artifacts
corpus    captured raw language, expression occurrences, and resolutions
ml        versioned models, runs, inferences, ranked candidates, and typed signals
audit     independent review, lifecycle history, promotion, and validation
```

Canonical concept identity has an internal `BIGINT GENERATED ALWAYS AS
IDENTITY` primary key plus a stable unique `concept_key`. Display language is
stored in `kb.lexical_expression`, and mappings are explicit rows in
`kb.lexicalization`. A concept therefore has neither a mandatory global family
nor an English label as its identity.

All major domain rows have explicit primary and candidate keys. Foreign keys
in the canonical, provenance, corpus, ML, and audit history use explicit
`ON UPDATE RESTRICT ON DELETE RESTRICT`. Controlled code tables use text
candidate keys because the code itself is the stable semantic identity. The
design meets the requested 3NF baseline: controlled meanings, source versions,
datasets, methods, scales, mappings, and relation types are factored into their
own relations. JSONB is limited to sparse metadata/configuration and does not
hold canonical graph structure.

## Scientific distinctions preserved

- Concepts contain no intrinsic intensity, similarity, score, weight, or
  permanent projection coordinates.
- Six sample-level sensory dimensions are registries of interpretable
  measurement constructs, not permanent concept-vector axes.
- Pair measurements remain repeatable by dataset, method, scale, and signal
  domain. Perceptual, linguistic-semantic, corpus, structural, model-derived,
  and governance signals are not interchangeable.
- Projection axes and values belong to versioned projection spaces rather than
  to concept columns.
- Raw observations, ML candidates, independent reviews, and explicit promotion
  events remain separate. Nothing auto-promotes.
- `pending`, `resolved`, and `unresolved` are explicit controlled resolution
  states. A resolution is not manufactured from its nearest trigram.
- Source-version rights are mandatory. Product export is affirmative and
  machine-checkable, not inferred from public accessibility.

## Draft-SQL defects repaired in the executable design

1. Cross-table semantics cannot be expressed by ordinary `CHECK` constraints;
   relation-type behavior, support-at-commit, scale bounds, observation
   resolution, model-run state, and promotion eligibility are implemented with
   named triggers instead.
2. PostgreSQL does not allow a subquery or time-dependent expression in a
   partial-index predicate. Partial indexes use immutable row predicates, and
   source/current semantics remain in joins and views.
3. Symmetric uniqueness cannot rely on callers presenting endpoints in one
   order. A `BEFORE` trigger canonicalizes symmetric endpoints before the
   ordinary unique key is evaluated.
4. Active hierarchical cycles require recursive graph inspection. The write
   path serializes same-type hierarchy edits with a transaction advisory lock
   and rejects direct or indirect cycles.
5. Support may be inserted after its canonical assertion in the same
   transaction. Deferrable constraint triggers validate support at transaction
   completion and reciprocal support deletion/retargeting.
6. A single generic similarity or weight would erase signal provenance. The
   design stores typed, dataset-specific measurements and candidate signals
   without an aggregate canonical score.
7. A rights-filtered view must join the exact source version to its verified
   policy. It does not classify content from a source title, URL, or access
   assumption.

## Seed boundary

The seed contains 19 concepts, 23 expressions, 23 active lexicalizations, five
typed relations, six sensory dimensions, and small provenance/corpus fixtures.
It contains zero empirical measurements, projections, calibrations, models,
runs, candidates, reviews, or promotions. Its fixed timestamps and stable keys
exist for deterministic testing; it is not the planned 90–120-concept V0
ontology and makes no scientific population claim.

No WCR, SCA, ISO, Cup of Excellence, commercial definition, proprietary form,
or flavor-wheel structure was copied. The physically absent Deep Research PDF
was not fabricated or placed in the repository.
