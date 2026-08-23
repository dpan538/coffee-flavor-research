# Coffee Sensory Knowledge Base V0 — Research Source

Status: current engineering contract  
Effective date: 2026-08-24  
Supersedes: the pre-Sensory-KB V0 product, frontend, data-methodology, and
decision documents listed in the
[archive manifest](../../archive/pre-sensory-kb-v0-20260824/MANIFEST.md)

## Source identity and availability

The research work named by the Round 1 brief is:

> Computational Coffee Sensory Space, NLP Normalization, and PostgreSQL
> Knowledge Base

The external Deep Research PDF was not available as a file in this workspace
and was not physically copied into the repository. Redistribution permission
for that external artifact was therefore not evaluated. This repository does
not invent or assert its authors, publisher, institution, DOI, publication
date, license, sample counts, or bibliographic citation.

For this round, the user-supplied engineering brief derived from that research
is the implementation contract. These four project-authored documents preserve
only the engineering constraints needed to build and audit KB V0. If a verified
copy of the research report becomes available later, it must be provenance-
checked and reviewed against this contract; it must not silently replace or
retroactively validate implementation choices.

## Authority and proof boundary

This research specification is canonical for the knowledge architecture. It is
not proof that migrations execute, constraints reject invalid writes, query
plans use intended indexes, or clean rebuilds are deterministic. Only recorded
database audit artifacts may establish those results. A requirement stated
here must not be reported as a passing test merely because it is documented.

The current public React application remains a compatibility baseline. Its
24-descriptor TypeScript dataset and project-curated association ranges are not
the canonical PostgreSQL knowledge base and are not scientific measurements.

## Binding engineering decisions

KB V0 must preserve all of the following distinctions:

- Target approximately 90–120 **active canonical sensory concepts** for V0,
  while allowing an open-ended number of multilingual lexical expressions.
- Use immutable internal concept identity and stable machine-readable keys;
  never use an English display label as identity.
- Represent knowledge as a typed, polyhierarchical graph. A concept cannot be
  restricted to one universal Flavor Wheel family.
- Treat Flavor Wheel groupings, when lawfully represented, as source-specific
  structures or projections rather than universal computational dimensions.
- Keep descriptive sensory knowledge separate from affective/value judgments
  and from processing entities.
- Keep standard sensory references and calibration separate from concept
  identity; a reference does not give a descriptor permanent intrinsic
  intensity.
- Treat PCA, MDS, correspondence-analysis, fuzzy, factor, and related
  coordinates as versioned dataset/model-specific empirical artifacts.
- Keep perceptual, linguistic-semantic, corpus-co-occurrence, structural,
  model-derived, and epistemic/governance signals distinguishable.
- Never interpret embedding similarity or corpus co-occurrence as sensory
  similarity without an independently justified measurement semantics.
- Treat evidence strength, confidence, and review status as governance or
  evaluation metadata, never as sensory weights.
- Do not introduce a fixed weighted-sum consumer ranking formula in V0.
- Make NLP a retrieval/ranking and candidate-generation process with explicit
  `UNRESOLVED`; never force a nearest-neighbour classification.
- Structurally separate raw observations, canonical knowledge, model inference,
  independent evaluation, and explicit promotion.
- Use PostgreSQL 17+ as system of record and require `pg_trgm` for the baseline.
  Do not require SQLite, MongoDB, Firebase, an external vector database, or
  `pgvector`.
- Never allow model output to promote itself silently into canonical knowledge.

## Rights and evidence boundary

Public web access does not imply reuse permission. KB V0 must not seed copied
WCR definitions or full reference tables, ISO definitions, the SCA Coffee
Taster's Flavor Wheel structure/artwork/full vocabulary, SCA proprietary form
text, or other protected source content. Bibliographic and rights metadata may
be stored, together with independently authored project descriptions, when its
provenance and permitted use are known.

No scientific citation or evidence claim may be fabricated to fill a missing
field. Unverified rights, measurements, terminology, or mappings remain
explicitly unknown, restricted, candidate, or unresolved.

## Round scope

This round covers legacy archival, a PostgreSQL schema and migration baseline,
lawful smoke data, relational and semantic negative tests, trigram retrieval,
query-plan review, two clean rebuilds, and evidence-backed audit receipts.

It explicitly stops before frontend redesign, consumer questionnaires,
large-scale roaster scraping, embeddings, model training, LLM normalization,
`pgvector`, personalization, consumer ranking coefficients, and recommendation
models.

## Specification set

- [01_V0_ARCHITECTURE.md](./01_V0_ARCHITECTURE.md) — logical architecture and
  information flow.
- [02_DATABASE_INVARIANTS.md](./02_DATABASE_INVARIANTS.md) — mandatory
  scientific and relational invariants.
- [03_ENGINEERING_DECISIONS.md](./03_ENGINEERING_DECISIONS.md) — accepted and
  deferred engineering decisions.
- [`db/`](../../../db/) — executable implementation; its presence alone is not
  validation.
- [Round 1 audits](../../audits/coffee-sensory-kb-v0-round1/) — the only place
  implementation pass/fail claims may be evidenced.
