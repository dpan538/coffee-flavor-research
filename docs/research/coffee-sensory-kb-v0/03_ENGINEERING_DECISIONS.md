# Coffee Sensory Knowledge Base V0 — Engineering Decisions

Status: current decision record  
Effective date: 2026-08-24

This record turns the research contract into implementation choices. It does
not duplicate database test evidence and does not claim the implementation has
passed. Superseded product/frontend decisions remain available in the
[archive](../../archive/pre-sensory-kb-v0-20260824/decisions/DECISIONS.md).

## Accepted decisions

### KBV0-001 — Research architecture is canonical

The contract in this directory supersedes conflicting pre-KB product, frontend,
descriptor-vector, and speculative backend designs. Earlier material remains
archived for traceability.

Consequence: reviews start from the scientific invariants, not from the shape of
the 24-descriptor frontend data.

### KBV0-002 — Preserve the static frontend as a compatibility baseline

The existing React Router Framework Mode application, Vite build, and
packages/flavor-data runtime stay operational. KB V0 does not redesign the UI
or silently switch its data source.

Consequence: frontend data can demonstrate the public prototype, but it is
non-canonical and its draft ranges are not scientific facts. Future integration
requires a rights-filtered export or API contract.

### KBV0-003 — PostgreSQL 17+ is the sole V0 system of record

The canonical KB uses PostgreSQL 17 or newer and enables pg_trgm. It does not
require SQLite, MongoDB, Firebase, an external vector database, or pgvector.

Consequence: exact PostgreSQL and pg_trgm versions belong in audit receipts.
PGVECTOR_REQUIRED=false remains an explicit gate.

### KBV0-004 — Use six ownership domains

Use ref, kb, evidence, corpus, ml, and audit schemas. Cross-domain references
are explicit and guarded by foreign keys or deferred checks.

Consequence: raw observations, canonical facts, provenance, model artifacts,
and review decisions cannot collapse into one convenience table.

### KBV0-005 — Use surrogate relational keys plus stable candidate keys

Prefer bigint generated always as identity for internal primary keys and unique
stable keys for domain objects. Display names and translations are not IDs.

Consequence: labels may evolve while historical model, source, and audit links
remain resolvable.

### KBV0-006 — Model language separately from concepts

Expressions and lexicalizations are independent from language-neutral concepts.
The schema supports open-ended languages, including zh-Hans, without making
Chinese seed data a Round 1 requirement.

Consequence: variants, translations, polysemy, candidates, and unresolved terms
remain representable without duplicating concepts.

### KBV0-007 — Use typed polyhierarchy, not one global wheel family

Relations use controlled semantics and metadata for symmetry, directionality,
hierarchy, transitivity, self-relations, provenance, ordering, and cycles.

Consequence: source taxonomies can be represented without becoming universal
classification. Generic related-to edges and mandatory family IDs are rejected.

### KBV0-008 — Store measurements by domain and provenance

Perceptual, linguistic-semantic, corpus, structural, model-derived, and
governance signals remain distinct. Pair measurements and projection spaces are
versioned empirical records tied to datasets and methods.

Consequence: no universal similarity, weight, concept intensity, or permanent
PCA/MDS coordinate is introduced.

### KBV0-009 — Treat promotion as an audited state transition

Model candidates and reviews are durable records. An explicit promotion event
with exactly one canonical target is the only route from evaluated inference to
canonical assertion.

Consequence: confidence thresholds and completed runs never auto-promote
knowledge.

### KBV0-010 — Preserve unresolved retrieval outcomes

V0 performs exact lookup, approved variant lookup, trigram top-k, typed graph
expansion, then returns UNRESOLVED if no approved mapping is safe.

Consequence: meteor fruit is a required negative semantic fixture. Nearest
neighbour output is a candidate, not a forced classification.

### KBV0-011 — Make rights filtering structural

Sources, versions, and rights policy are machine-readable. Distributable views
exclude raw text unless production export is affirmatively permitted.

Consequence: the seed is independently authored and does not copy WCR, ISO,
SCA, or other protected content. Missing license/citation facts remain unknown.

### KBV0-012 — Prefer normalized relational structures

Target 3NF at minimum and BCNF where appropriate. JSONB is reserved for sparse
external metadata, raw capture metadata, model configuration, and experiment
reproducibility; it does not hold canonical graph structure.

Consequence: keys, rights, relation semantics, and promotion targets stay
visible to PostgreSQL constraints and query planning.

### KBV0-013 — Preserve history with restrictive foreign keys

Canonical and historical objects use lifecycle state instead of destructive
deletion. Prefer ON UPDATE RESTRICT and ON DELETE RESTRICT for scientific,
source, model, and audit history unless an exception is narrowly justified.

Consequence: deprecated or merged concepts and old runs retain stable
resolution.

### KBV0-014 — Use a dependency-ordered migration tree

The preferred executable sequence is:

```text
db/000_extensions.sql
db/001_reference_and_schemas.sql
db/002_core_schema.sql
db/003_evidence_corpus_ml_audit.sql
db/004_constraints_and_triggers.sql
db/005_indexes_and_views.sql
db/006_reference_seed.sql
db/007_validation_queries.sql
```

Additional splits are acceptable when they improve dependency clarity. Each
migration runs directly through psql, fails loudly, and avoids hidden
application dependencies.

Consequence: draft research SQL is tested and repaired rather than copied
uncritically. PostgreSQL limitations, including subqueries being forbidden in
partial-index predicates, shape valid implementation without changing the
scientific contract.

### KBV0-015 — Seed only lawful semantic fixtures

The smoke seed is small and independently authored. It includes enough concepts
and expressions to test grapefruit/pink grapefruit, bergamot, jasmine, black
tea/Earl Grey, fermented, cardboard, rubber, bright, clean, juicy, tea-like,
winey, and unresolved meteor fruit behavior.

Consequence: seed size is not evidence that the target 90–120 active-concept V0
ontology has been curated. Hundreds of descriptors are not seeded in Round 1.

### KBV0-016 — Prove constraints with negative tests

Unique keys, self-edge rejection, symmetric normalization, cycle prevention,
deferred provenance support, singular promotion targets, and scale bounds
require executable failure tests that record PostgreSQL error or constraint
names.

Consequence: schema review alone cannot produce NEGATIVE_TEST_PASS=true.

### KBV0-017 — Choose indexes from access patterns and inspect plans

Indexes cover stable-key lookup, lexical resolution, relation traversal,
provenance coverage, measurements, unresolved corpus work, candidate ranking,
and review. GiST/GIN choices follow observed queries.

Consequence: trigram and graph queries require EXPLAIN (ANALYZE, BUFFERS)
evidence; index existence is not a query-plan pass.

### KBV0-018 — Require two clean deterministic rebuilds

Validation destroys and recreates a disposable empty database, applies the
complete migration and seed sequence, and runs all validation classes twice.

Consequence: migration, seed, and schema hashes plus stable keys, reference row
counts, source-version inventory, and validation counts must agree. Incremental
repair does not establish reproducibility.

## Rejected shortcuts

- Reusing English labels as concept IDs.
- Treating categories as one mandatory Flavor Wheel family per concept.
- Copying frontend association ranges into canonical concept columns.
- Merging embedding cosine, corpus PMI, MDS distance, and perceptual evidence
  into one similarity or weight.
- Auto-promoting high-confidence model candidates.
- Mapping every expression to its nearest neighbour.
- Storing canonical ontology structure in JSONB.
- Adding embeddings or pgvector before the V0 substrate passes.
- Claiming public web content is redistributable without a rights decision.
- Treating migrations or documentation as validation evidence.

## Deferred research decisions

The following remain deliberately unresolved:

- universal coffee perceptual distance;
- stable cross-cultural sensory geometry;
- numeric decompositions of bright, clean, or juicy;
- the optimal four or five consumer questions;
- a final consumer-to-region ranking model;
- a universal similarity threshold;
- embedding/rule fusion coefficients;
- roaster-note accuracy;
- embedding model selection, vector storage, and training;
- large-scale corpus collection and NLP normalization.

Schema extensibility is allowed; inventing answers in seed data, constraints,
or ranking code is not.

## Decision verification gates

The implementation is ready for a later NLP/corpus round only when audit
evidence shows fresh PostgreSQL 17+ migration success, all expected-zero and
negative tests passing, semantic fixtures preserved, restricted text excluded,
trigram and graph plans reviewed, and two deterministic clean rebuilds. Until
then, the architecture is current but the database is unvalidated.
