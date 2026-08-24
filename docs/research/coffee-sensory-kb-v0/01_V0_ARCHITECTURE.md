# Coffee Sensory Knowledge Base V0 Architecture

- Status: canonical target architecture
- Validation status: determined only by the
  [Round 1 audit receipts](../../audits/coffee-sensory-kb-v0-round1/)

## Architectural purpose

Coffee Sensory KB V0 is a research knowledge substrate for language
normalization, evidence-aware retrieval, graph traversal, and later evaluation.
PostgreSQL 17+ is the system of record. The model is deliberately not a Flavor
Wheel clone, a permanent sensory-coordinate system, a consumer preference
formula, or a warehouse of copied source text.

The target is approximately 90–120 active canonical sensory concepts, not a
fixed total vocabulary size. Multilingual lexical expressions, source records,
measurements, corpus observations, and model runs may grow independently.

## Logical separation

```text
lawful source metadata and datasets ───────────────┐
                                                   v
raw industry text -> lexical expression -> ML mapping candidate
                                              |
                                              v
                                    independent audit/review
                                              |
                                              v
                                     explicit promotion event
                                              |
                                              v
                                   canonical KB assertion

Canonical KB assertions never flow backward into raw captures, and model output
never crosses the promotion boundary automatically.
```

The database owns six logical schemas:

| schema     | responsibility                                                  | representative records                                                                                                                               |
| ---------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ref`      | Controlled semantics used across domains.                       | lifecycle statuses, concept types, relation types and properties, mapping types, language tags, signal domains, review decisions                     |
| `kb`       | Current and historical canonical knowledge.                     | concepts, lexical expressions, lexicalizations, typed concept relations, sensory dimensions, concept-dimension links                                 |
| `evidence` | Scientific/source provenance and versioned empirical artifacts. | sources, source versions, rights policy, datasets, statistical methods, support records, pair measurements, projection spaces, reference calibration |
| `corpus`   | Raw and derived industry-language observations.                 | corpora, captured documents, raw observations, expression co-occurrence measurements                                                                 |
| `ml`       | Regenerable model-specific inference.                           | versioned models, runs, mapping candidates, typed candidate signals                                                                                  |
| `audit`    | Independent review and controlled state change.                 | mapping reviews, explicit promotion events, actor/time/decision trace                                                                                |

Cross-schema foreign keys preserve provenance without merging domain semantics.
Canonical ontology structure is relational, not stored as JSON blobs.

## Canonical concepts

A concept is language-neutral. It has an immutable internal identity and a
stable candidate key such as `sensory.grapefruit`, `composite.earl_grey`, or
`qualifier.bright`. Display labels and spellings live elsewhere and may change
without changing identity.

At minimum, concept types include:

- `sensory_attribute`
- `composite_reference`
- `qualifier`
- `affective_term`
- `process_entity`
- `category`

These types stop heterogeneous coffee terms from being flattened into one
descriptor class. Concept lifecycle includes `candidate`, `active`,
`deprecated`, `merged`, and `rejected`; replacement links preserve historical
resolution. Concepts are retired by status, not physical deletion.

## Lexical expressions and lexicalizations

Lexical expressions store language-tagged forms independently from concepts.
One concept may have many English, Simplified Chinese (`zh-Hans`), or future
expressions, while one expression may require multiple context-sensitive
candidate interpretations. Chinese content is not required in the smoke seed,
but the schema must support it.

A lexicalization is an asserted mapping between an expression and a concept,
with status, mapping semantics, provenance, validity, and review state. External
active lexicalizations require source support. Absence of a safe active mapping
is a valid state, surfaced as `UNRESOLVED`.

## Typed concept relations

The canonical graph is polyhierarchical and uses controlled relation types,
not a generic universal `related_to` edge. Baseline relation semantics include:

- `broader_than`
- `sensory_neighbour`
- `composite_has_component`
- `consumer_reference_for`
- `modifies`
- `contrasts_with`

Each type declares whether it is directional, symmetric, hierarchical,
transitively closed, self-allowing, and evidence-requiring. Active hierarchical
edges must be acyclic. Symmetric relations use canonical endpoint ordering so
`A–B` and `B–A` cannot coexist as duplicate current assertions. A source-
specific family can be expressed through typed/source-supported structure or a
projection; no concept has one mandatory universal family.

## Sensory dimensions

The initial stable dimensions are interpretable sample-level measurement
constructs:

- `taste.sweetness`
- `taste.sourness_acidity`
- `taste.bitterness`
- `taste.saltiness`
- `tactile.body_fullness`
- `tactile.drying_astringency`

They are not permanent numeric properties of concepts. `Fruitiness`,
`floralness`, and `roastiness` are not assumed to be universal orthogonal axes;
they may remain conceptual regions or appear in source-specific empirical work.

## Empirical measurements

Multiple measurements may coexist for the same concept pair because they
answer different questions. A bergamot–jasmine pair could have independently
stored expert-sorting proximity, MDS distance, CATA co-selection, embedding
cosine, and corpus PMI.

Every measurement identifies its signal domain, statistical method, dataset,
value, value semantics, scale, applicable sample size, available uncertainty,
and contextual metadata. The data model never collapses these into a universal
`similarity` or `weight` field.

## Projection spaces

PCA, MDS, correspondence-analysis, factor, fuzzy, and related coordinates are
versioned empirical artifacts. A projection space identifies its dataset,
method, model/version, and configuration; axes and concept-coordinate values
are normalized child records. Permanent columns such as `concept.pca_1` or
`concept.mds_x` are prohibited.

## Sources, versions, and rights

`evidence` distinguishes a conceptual source from its version and rights review.
Machine-readable rights policy should capture, where applicable,
`access_class`, `redistributable`, `derivative_work_allowed`,
`commercial_use_allowed`, `machine_use_allowed`,
`production_export_allowed`, `checked_on`, and `rights_notes`.

Externally sourced canonical assertions link to explicit support records. A
production/distributable corpus view excludes raw text unless verified rights
metadata allows production export. Source or model deletion cannot cascade away
historical scientific outputs.

## Industry corpus observations

`corpus` preserves collection context, captured documents, raw text or lawful
references to it, normalized observation candidates, and corpus-specific
co-occurrence statistics. Raw captures remain distinct from lexical expressions
and canonical mappings. Restricted text remains queryable only within its
permitted access boundary and never leaks through distributable views.

Corpus co-occurrence is `CORPUS_COOCCURRENCE`, not sensory similarity. An
unmapped observation remains unresolved rather than being forced to its nearest
known expression.

## ML runs and mapping candidates

`ml` identifies a model and version separately from reproducible runs. A run
stores configuration and generation metadata, then produces mapping candidates
and typed candidate signals. Linguistic embeddings, edit/trigram signals,
structural features, and other model outputs retain their own domains and
semantics.

Model artifacts are regenerable. They do not modify ontology state, and future
vectors—if separately approved—must reference model/version and expression or
concept identity. `pgvector` is not a V0 dependency.

## Audit, review, and promotion governance

Reviews are independent records, not columns overwritten on candidates.
Promotion is an explicit event with actor, time, decision, rationale, and
exactly one canonical target. A completed model run, high confidence score, or
passing threshold never promotes itself. Evidence strength and model confidence
remain governance/evaluation metadata and cannot act as sensory weights.

## Retrieval contract

The minimal V0 lexical retrieval sequence is:

1. exact lexical lookup;
2. approved lexical variant lookup;
3. `pg_trgm` top-k candidates;
4. typed graph expansion;
5. explicit `UNRESOLVED` when no approved mapping is safe.

Embeddings, learned fusion, and universal thresholds are outside V0. Intended
trigram and graph indexes must be evaluated with `EXPLAIN (ANALYZE, BUFFERS)`;
their mere existence is not evidence of use.

## Semantic fixtures

The lawful smoke seed is small and independently authored. It tests distinctions
rather than claiming a complete ontology:

- Pink grapefruit remains its own concept and may be broader-linked to
  grapefruit.
- Earl Grey is a composite consumer reference for bergamot and has black tea as
  a component; it is not a synonym of bergamot.
- Bright is a candidate qualifier with no invented acidity formula.
- Tea-like is a qualifier distinct from black tea.
- Fermented sensory character remains separate from fermentation process.
- Winey can preserve polysemy rather than forcing one interpretation.
- `meteor fruit` can exist as an expression with no active mapping and returns
  `UNRESOLVED`.

## Public frontend compatibility boundary

The React Router/Vite application remains statically buildable with `ssr:
false` and imports its compatibility data from `packages/flavor-data`. KB V0
does not silently replace that runtime dataset in this round. The legacy
TypeScript data may demonstrate interface behavior, but its exclusive
categories and descriptor-attached 0–5 profiles are not PostgreSQL canonical
knowledge.

Any future frontend integration must be an explicit architecture phase with a
documented export/API contract, rights filtering, and migration plan. Until
then, the static public baseline and the canonical research substrate coexist
without pretending to be synchronized.

## Explicitly deferred questions

V0 does not invent a universal coffee perceptual distance, stable
cross-cultural geometry, numeric decompositions of bright/clean/juicy, optimal
consumer questions, a final consumer-to-region ranking formula, a universal
similarity threshold, embedding/rule coefficients, or a measure of roaster-note
“accuracy.” The schema may support future evidence about these questions, but
does not answer them by construction.
