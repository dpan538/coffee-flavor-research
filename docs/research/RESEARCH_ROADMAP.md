# Coffee sensory research roadmap

Status: current ordered research program

This roadmap sequences evidence and engineering dependencies. It does not
promise delivery dates. A later stage begins only when the relevant evidence,
rights, evaluation, and reproducibility gates of the preceding stage are
satisfied.

The product semantics are governed by the
[Product Contract V0](../product/PRODUCT_CONTRACT_V0.md); the scientific
boundaries are described in the
[Methodology Overview](../methodology/METHODOLOGY_OVERVIEW.md).

## Done

### Research foundation

- Defined scientific, epistemic, licensing, and rights boundaries.
- Archived pre-V0 exploratory product and frontend material without rewriting
  its history.

### PostgreSQL architecture

- Established PostgreSQL 17 as the system of record.
- Separated `ref`, `kb`, `evidence`, `corpus`, `context`, `ml`, and `audit`
  claim domains.
- Validated constraints, negative cases, query plans, and repeatable rebuilds.

### Canonical sensory ontology

- Curated 130 governed concepts, including 92 active canonical sensory
  attributes.
- Added concept provenance, source-version governance, rights policy,
  independent descriptions, lifecycle status, polyhierarchy, and isolated
  source-specific schemes.

### Pilot industry-language corpus

- Created a rights-reviewed, frozen historical pilot with 2,474 documents,
  6,818 observations, and 1,713 normalized expressions.
- Preserved language observations separately from canonical sensory claims.
- Documented sampling, rights, redistribution, and public-reproducibility
  limits.

### Deterministic retrieval baseline

- Implemented exact, approved-variant, `pg_trgm`, and typed one-hop graph
  candidate retrieval.
- Preserved candidate-signal provenance and explicit `UNRESOLVED` behavior.
- Evaluated four ablations on a frozen development/held-out audit without
  embeddings, `pgvector`, or automatic ontology promotion.

### Preparation and roast context

- Reviewed preparation, milk, roast, and preparation-by-roast evidence.
- Defined eight broad internal C0 families with conditional subtypes and
  separate database observation-status semantics.
- Preserved the historical Round 3A five-level C1 projection, source-scheme
  isolation, measured-method separation, and unresolved terminology.
- Added forward-only normalized context migrations, provenance, semantic and
  negative tests, query plans, and repeatable inventory.

### Round 3B interaction decision

- Made one valid C0 family mandatory in the user interaction with no
  user-facing unknown option; database unknown states remain valid.
- Superseded the historical five-level user projection with a current minimum
  seven-level ordinal scheme that preserves medium-light and medium-dark.
- Kept interaction constraints separate from empirical mapping calibration.

## Now

### Context dataset and interaction validation

- Freeze and hash a rights-cleared context dataset before import.
- Validate common consumer preparation expressions against the mandatory
  eight-family C0 projection.
- Validate source roast expressions against the seven-level C1 projection
  without forced assignment.
- Define held-out evaluation slices for known, unresolved, unknown, black,
  milk, preparation, and roast contexts.
- Test context value without inventing flavor coefficients.

### Multi-source corpus enrichment

- Develop a lawful, stratified, contemporary source frame beyond the current
  historical secondary source.
- Review robots, terms, copyright, redistribution, and machine-access policy
  before acquisition.
- Measure source, geographic, preparation, roast, origin, and process
  concentration without inferring absent metadata.

### Lexical normalization expansion

- Expand governed expressions and variants from rights-reviewed evidence.
- Prioritize unresolved held-out cases and recurrent industry-language gaps.
- Preserve phrases, polysemy, concept types, and abstention.
- Queue ontology-extension candidates for explicit curation rather than
  automatic promotion.

## Next

### Independent evaluation refinement

- Add genuinely independent human review where feasible.
- Refine development and held-out audit strata without tuning on the held-out
  result.
- Re-evaluate relevance, coverage, abstention error, unsafe non-abstention, and
  disagreement.
- Define evaluation slices for preparation and roast contexts.

### Embedding benchmark

- Benchmark embeddings only after the deterministic lexical bridge and audit
  are stronger.
- Compare retrieval quality, latency, cost, explainability, and abstention with
  the deterministic baseline.
- Require measurable held-out incremental value; deep learning is not a
  scientific gate by itself.
- Keep `pgvector` optional unless evidence justifies a future dependency.

### Hybrid retrieval benchmark

- Compare exact, variant, trigram, graph, embedding, and hybrid candidate
  generation through explicit ablation.
- Retain signal ledgers instead of collapsing heterogeneous evidence into an
  unexplained score.
- Calibrate thresholds and uncertainty without presenting ranking scores as
  true flavor probabilities.

## Later

### Four-to-five-question sensory-region research

- Identify low-burden questions that discriminate useful sensory regions.
- Test question comprehension, order effects, adaptation triggers, and burden.
- Validate a default of four questions and the value of an optional fifth.
- Avoid importing trained-panel instruments directly into an ordinary tasting
  interaction without evidence.

### Consumer-region model

- Define a consumer-perception representation and contextual ranking target.
- Calibrate preparation, roast, answer, lexical, and ontology signals.
- Evaluate candidate ranking, uncertainty, subgroup behavior, and learning
  outcomes on independent held-out data.
- Treat correction as a possible learning outcome, not the objective function.

### API contract

- Specify typed inputs for C0, C1, Q1–Q5, language, and uncertainty.
- Specify five primary and three secondary candidate outputs, provenance, and
  abstention behavior.
- Define rights-filtered data surfaces without exposing restricted evidence.

### Feature decomposition

- Separate knowledge access, normalization, candidate generation, ranking,
  explanation, telemetry, and evaluation responsibilities.
- Establish versioning and reproducibility boundaries for every deployed
  inference path.

### Frontend / PWA

- Design and validate the ordinary tasting interaction only after the product,
  question, model, and API contracts are evidence-backed.
- Preserve accessibility, low burden, uncertainty, and candidate—not answer—
  language.
- Do not treat the existing static public baseline as the validated consumer
  product.

## Cross-stage gates

Every material research or engineering stage must preserve:

- source and version provenance;
- rights and redistribution decisions;
- canonical/corpus/model/evaluation separation;
- descriptive commits, remote feature-branch checkpoints, and audit receipts;
- held-out evaluation where model claims are made;
- explicit uncertainty and abstention;
- forward-only database migration history; and
- reproducible validation appropriate to the change.
