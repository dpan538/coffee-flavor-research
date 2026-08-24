# Coffee Sensory Knowledge Base V0 — Database Invariants

- Status: normative implementation requirements
- Evidence status: requirements only; see
  [Round 1 audits](../../audits/coffee-sensory-kb-v0-round1/) for test results

The words **MUST**, **MUST NOT**, **REQUIRED**, and **PROHIBITED** define the
engineering contract. They do not report that an implementation has passed.
Every enforceable invariant belongs in PostgreSQL constraints, indexes,
triggers, controlled reference data, or rights-filtered views, with
machine-runnable positive and negative tests.

## 1. Concept identity is language-neutral

- Every concept MUST have an immutable internal relational primary key and a
  stable, unique, machine-readable concept key.
- Internal primary keys SHOULD use bigint generated always as identity.
- A display label, English spelling, translation, slug, or category MUST NOT be
  used as conceptual identity.
- Duplicate stable keys MUST be rejected.
- Stable keys MUST survive display-name and lifecycle changes.

Representative keys include sensory.grapefruit, composite.earl_grey, and
qualifier.bright; these are identifiers, not display text.

## 2. Lexical expressions are independent records

- A lexical expression MUST have its own immutable identity, stable candidate
  key, language tag, surface form, and normalized lookup form.
- The schema MUST support multiple expressions per concept and MUST support
  zh-Hans, even if the V0 smoke seed contains no Chinese expression.
- Expression identity MUST NOT imply a canonical mapping.
- Lexicalizations MUST be separate assertion records linking expressions to
  concepts with mapping type, lifecycle, provenance, and validity.
- Polysemous forms such as winey MUST retain multiple context-dependent
  interpretations or candidates.
- No safe active mapping MUST be representable as UNRESOLVED; the system MUST
  NOT force the nearest candidate.

## 3. Concept types remain distinct

Controlled concept types MUST include at least:

```text
sensory_attribute
composite_reference
qualifier
affective_term
process_entity
category
```

The schema MUST NOT assume every coffee word is a sensory attribute. Descriptive
sensory content, composites, qualifiers, affective/value language, processing
entities, and categories MUST remain queryably distinguishable.

## 4. The graph is typed and polyhierarchical

- A concept MUST NOT have one required global family identifier or equivalent
  exclusive Flavor Wheel family.
- Source-specific grouping schemes MUST be represented as source-supported
  relations, many-to-many structures, or versioned projections.
- Canonical edges MUST identify a controlled relation type; a generic
  unqualified related-to edge is insufficient.
- Baseline relation types MUST include or semantically cover broader_than,
  sensory_neighbour, composite_has_component, consumer_reference_for, modifies,
  and contrasts_with.
- Every relation type MUST declare whether it is directional, symmetric,
  hierarchical, transitively closed, self-allowing, and evidence-requiring.
- A relation type MUST NOT be both directional and symmetric.
- Active hierarchical relations MUST be acyclic, including direct and indirect
  cycles.

## 5. Relation rows enforce type semantics

- A prohibited self-edge MUST fail.
- A symmetric relation MUST store endpoints in canonical order, such as the
  lesser concept ID followed by the greater concept ID.
- Current symmetric pairs MUST be unique so inserting both A–B and B–A fails.
- Directional relations MUST preserve subject/object meaning and MUST NOT be
  reordered as if symmetric.
- Relation validity/lifecycle MUST distinguish current, expired, deprecated,
  and rejected assertions.
- Relation endpoints MUST use foreign keys; dangling endpoints are prohibited.
- Cycle detection for active hierarchical edges MUST use recursive PostgreSQL
  logic and cover insert and relevant update operations.

## 6. Concept identity has no intrinsic intensity

- Concepts MUST NOT contain permanent fields such as intensity,
  default_intensity, acidity_score, pca_1, mds_x, or mds_y.
- Sensory reference calibration MUST be separate from concept identity and tied
  to a defined protocol, source/version, scale, and context.
- Sample observations and empirical concept associations MUST remain separate
  from reference calibration.
- The frontend's project-curated 0–5 association profiles MUST NOT be imported
  as canonical scientific properties merely because they exist.

## 7. Sensory dimensions are sample-level constructs

The initial dimension registry MUST support these explicitly interpretable
constructs:

```text
taste.sweetness
taste.sourness_acidity
taste.bitterness
taste.saltiness
tactile.body_fullness
tactile.drying_astringency
```

Dimension definitions and scales MUST be versionable and provenance-aware.
Fruitiness, floralness, and roastiness MUST NOT become universal orthogonal
numeric axes without independent justification.

## 8. Signal domains never collapse

Controlled signal domains MUST distinguish at least:

```text
PERCEPTUAL
LINGUISTIC_SEMANTIC
CORPUS_COOCCURRENCE
STRUCTURAL
MODEL_DERIVED
EPISTEMIC_GOVERNANCE
```

- Every empirical or candidate signal MUST identify its domain and value
  semantics.
- Embedding cosine MUST NOT be interpreted as sensory distance by default.
- Corpus co-occurrence MUST NOT be interpreted as sensory similarity.
- MDS distance MUST NOT be interpreted as corpus co-occurrence.
- Evidence strength, confidence, and review state MUST remain epistemic or
  governance metadata, not sensory weights.
- A universal weight, similarity, or fixed weighted-sum ranking field is
  prohibited in V0.

## 9. Empirical measurements are reproducible assertions

The schema MUST permit multiple independent measurements for the same concept
pair. Each measurement MUST identify:

- signal domain;
- statistical method and stable method key;
- dataset and dataset version/context;
- numeric value and value semantics;
- declared scale and valid bounds;
- sample size where relevant;
- uncertainty where available;
- context/reproducibility metadata;
- source/provenance links.

Values MUST satisfy declared ranges. Pair ordering and uniqueness MUST be
defined per measurement semantics rather than by one overly broad constraint.

## 10. Projection coordinates are versioned artifacts

- A projection space MUST identify dataset, method, model/version where
  applicable, and configuration.
- Projection axes and concept-coordinate values MUST be normalized child
  records.
- Multiple projection spaces and versions MUST coexist without overwriting one
  another.
- PCA, MDS, correspondence-analysis, fuzzy, factor, and similar coordinates
  MUST NOT be permanent concept columns.

## 11. Raw, canonical, inferred, and evaluated states are structural

Raw corpus observations, lexical expressions, canonical assertions, ML
candidates/signals, independent reviews, and promotion events MUST live in
different logical structures.

```text
raw observation
  -> normalized expression
  -> model candidate
  -> typed candidate signals
  -> independent review
  -> explicit promotion
  -> canonical assertion
```

- No trigger, view, score, or completed model state may auto-promote output.
- Canonical records MUST NOT be overwritten to store model inference.
- Audit/review history MUST remain append-oriented and attributable.

## 12. Promotion is explicit and singular

- A promotion event MUST reference exactly one canonical target object.
- Zero-target and multiple-target promotion records MUST fail.
- Target type and target identifier MUST agree.
- A promotion MUST retain candidate/review basis, actor, timestamp, decision,
  and rationale.
- Promotion does not erase the original candidate, signals, or review.

## 13. Provenance support is transactionally complete

- An active externally sourced lexicalization MUST have source support before
  transaction completion.
- An active externally sourced concept relation MUST have source support before
  transaction completion.
- Deferred constraint triggers are acceptable when they permit same-transaction
  assertion/support insertion and reject an unsupported final state.
- Source support MUST identify a source version rather than only a mutable
  source display name.
- Source and source-version keys MUST be stable and unique.
- Deleting a source, dataset, method, model, or run MUST NOT cascade away
  historical assertions or scientific outputs.

## 14. Rights metadata controls production export

Source/version rights policy SHOULD expose, where applicable:

```text
access_class
redistributable
derivative_work_allowed
commercial_use_allowed
machine_use_allowed
production_export_allowed
checked_on
rights_notes
```

- Source versions MUST carry explicit license/rights status, including unknown
  or restricted when permission is not verified.
- Restricted or unknown raw text MUST NOT appear in distributable production
  views.
- Raw text may appear in corpus.v_distributable_observations only when verified
  policy permits production export.
- The smoke seed MUST NOT copy WCR definitions/reference tables, ISO
  definitions, SCA Flavor Wheel structure/artwork/full vocabulary, SCA form
  text, or other protected material.
- Missing rights or citation details MUST remain unknown; they MUST NOT be
  invented.

## 15. Lifecycle preserves history

Concept lifecycle MUST include candidate, active, deprecated, merged, and
rejected.

- Deprecated and merged concepts MAY reference a replacement concept.
- Replacement links MUST prohibit invalid self-reference and preserve stable
  historical IDs.
- A concept MUST NOT be physically deleted merely because terminology evolves.
- Historical model runs and audit records MUST continue to resolve original
  concept IDs.
- Canonical, provenance, scientific, model-history, and audit foreign keys
  SHOULD use ON UPDATE RESTRICT and ON DELETE RESTRICT unless a narrower
  documented exception is proven safe.

## 16. Relational normalization and key strategy

- Major relations MUST be analyzed for functional dependencies, candidate keys,
  primary keys, foreign keys, UNIQUE, NOT NULL, and CHECK constraints.
- The target is at least third normal form, with BCNF where appropriate.
- Stable candidate keys MUST exist for concepts, relations/expressions, sources,
  datasets, methods, models/versions, and runs.
- JSONB is limited to sparse external metadata, raw capture metadata, model
  configuration, and experiment reproducibility metadata.
- Canonical graph structure, core relation semantics, lifecycle, rights
  decisions, and promotion targets MUST NOT be hidden in JSONB blobs.

## 17. PostgreSQL baseline and logical schemas

- PostgreSQL 17 or newer is REQUIRED; the exact tested version MUST be recorded.
- CREATE EXTENSION IF NOT EXISTS pg_trgm is REQUIRED and its tested version
  MUST be recorded.
- pgvector is future work and MUST NOT be a dependency of V0.
- SQLite, MongoDB, Firebase, and an external vector database MUST NOT be
  required.
- The implementation MUST use ref, kb, evidence, corpus, ml, and audit with the
  ownership boundaries in
  [01_V0_ARCHITECTURE.md](./01_V0_ARCHITECTURE.md).

## 18. Migration invariants

The migration tree MUST be ordered, deterministic, directly executable through
psql, split by dependency, fail loudly, and avoid hidden application setup.

Research-generated draft SQL is a specification candidate, not executable
truth. PostgreSQL syntax, object order, trigger feasibility, data order,
partial-index limitations, and uniqueness scope MUST be tested and repaired
without weakening the scientific model. A partial-index predicate MUST NOT
contain a subquery because PostgreSQL does not permit one.

## 19. Required current and governance views

The implementation MUST provide and validate semantic equivalents of:

```text
kb.v_current_canonical_ontology
kb.v_lexical_resolution
kb.v_concept_neighbours
kb.v_concept_profile
evidence.v_source_coverage
corpus.v_distributable_observations
corpus.v_unresolved_industry_terms
ml.v_inferred_mappings_requiring_review
```

- The current ontology view MUST exclude deprecated concepts, deprecated
  relations, and expired relations.
- Lexical resolution MUST preserve unresolved expressions and MUST NOT expose
  unapproved model candidates as canonical.
- Distributable observations MUST exclude restricted text.
- Review queues MUST identify versioned models/runs and remain distinct from
  canonical views.

## 20. Indexes serve known access patterns

Indexes MUST be evaluated for stable concept-key lookup, normalized and trigram
expression lookup, lexicalizations by expression/concept, relations by
subject/object/type/status, source coverage, pair measurements, unresolved
corpus observations, model candidate ranking, and review lookup.

GiST versus GIN follows actual planned queries. Trigram retrieval and
graph-neighbour plans MUST be recorded with EXPLAIN (ANALYZE, BUFFERS); an index
definition alone is not a pass.

## 21. Required semantic behavior

- **Pink grapefruit:** retains its own concept; may be broader-linked to
  grapefruit; MUST NOT collapse automatically into grapefruit.
- **Earl Grey:** is a composite; may be consumer_reference_for bergamot and
  composite_has_component black tea; MUST NOT be a bergamot synonym.
- **Bright:** is a candidate qualifier with no arbitrary intrinsic acidity
  formula.
- **Tea-like:** is a qualifier distinct from black tea.
- **Fermented:** sensory character remains distinct from fermentation process.
- **Winey:** lexical treatment preserves possible polysemy.
- **Meteor fruit:** may exist with no active canonical mapping and MUST return
  UNRESOLVED.

## 22. Mandatory negative and expected-zero validation

Automated negative tests MUST attempt and reject:

1. a duplicate sensory.grapefruit concept key;
2. a prohibited self sensory-neighbour edge;
3. reversed insertion of an existing symmetric pair;
4. a direct active hierarchy cycle;
5. an indirect active hierarchy cycle;
6. an active external assertion without provenance;
7. a promotion with zero or two canonical targets;
8. an out-of-range reference calibration.

Tests MUST capture the actual PostgreSQL error or constraint name.

Expected-zero queries MUST cover dangling endpoints, duplicate concept keys,
illegal self-relations, incorrectly ordered or duplicate current symmetric
relations, active hierarchy cycles, unsupported active external relations and
lexicalizations, source versions without rights metadata, deprecated concepts
in current views, restricted raw text in distributable views, completed model
candidates without versioned model/run identity, and malformed promotions.

## 23. Reproducibility is a data invariant

Validation MUST start from an empty disposable PostgreSQL database and repeat
twice. Each run applies every migration and the lawful seed, then runs
validation, negative, semantic, retrieval, and query-plan tests. The two runs
MUST compare migration hashes, seed hash, schema dump hash, stable-key inventory,
reference-table row counts, source-version inventory, and validation counts.

An incrementally repaired database is insufficient. No pass may be claimed
until both clean builds produce the same logical state.
