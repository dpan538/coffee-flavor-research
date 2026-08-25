# Methodology overview

## Purpose

Coffee Flavor Atlas is intended to provide research-grounded sensory references
that are compatible with an ordinary user's current coffee perception. It is
not intended to detect an objective hidden flavor, reproduce a proprietary
flavor wheel, or score the user against a professional panel.

This document describes the validated foundation through Round 3B and the
Round 3C calibration architecture required before the planned adaptive
consumer interaction can be called validated.

## Research architecture

```text
coffee sensory science
        ↓
canonical sensory knowledge base
        ↓
industry-language observations
        ↓
deterministic normalization
        ↓
NLP / ML candidate retrieval
        ↓
evaluated ranking
        ↓
context-prior calibration + adaptive questions
        ↓
consumer sensory references
```

The ontology, corpus, deterministic retrieval, and context-normalization layers
have validated V0 foundations. The calibration layer currently has a governed
protocol and database contract only. Consumer-conditioned ranking and the final
sensory-reference interaction remain future empirical work.

### Coffee sensory science

Coffee-specific formal sensory foundations and peer-reviewed coffee sensory
research provide evidence for concept admission, concept typing, and careful
interpretation. Transferable sensory methodology is used only when it is
needed to define modeling or evaluation semantics.

Protected source definitions are not copied. Project descriptions are written
independently, and source versions retain rights, access, and production-export
decisions.

### Canonical sensory knowledge base

The canonical knowledge base represents language-neutral concepts,
lexicalizations, typed relations, lifecycle state, concept-level provenance,
and source-specific concept schemes. Source-local organization is not treated
as universal perceptual geometry.

The validated ontology contains 130 concepts, including 92 active canonical
sensory attributes. Qualifiers, composite references, affective terms,
categories, and process entities retain distinct types and governance.

### Industry-language observations

Round 2B records how a rights-reviewed historical source describes coffee. The
pilot contains 2,474 documents, 6,818 parsed fragment observations, and 1,713
unique normalized expressions.

These records are language observations:

```text
high frequency ≠ sensory validity
co-occurrence ≠ perceptual similarity
roaster note ≠ ground truth
```

Corpus statistics stay in empirical layers. They do not silently become
canonical sensory relations.

### Deterministic normalization

The current English normalization pipeline is versioned and reproducible. It
uses Unicode normalization, case and whitespace normalization, safe
punctuation handling, curated orthographic variants, and controlled phrase
normalization without destructive stemming.

Raw phrases and normalized identities remain distinguishable. Multiword
references such as `pink grapefruit`, `Earl Grey`, or `black tea` are not
destroyed by aggressive tokenization.

### NLP/ML candidate retrieval

The Round 2B deterministic baseline applies ordinal layers:

```text
approved preferred exact match
↓
approved lexical variant
↓
pg_trgm orthographic candidate generation
↓
one-hop typed graph expansion
↓
ranked candidates or UNRESOLVED
```

Each candidate retains the signal that produced it. The layers are precedence
tiers, not universal sensory coefficients, and the system does not flatten
lexical, graph, or trigram evidence into an unexplained probability.

### Evaluated ranking

The deterministic retrieval baseline has a frozen development/held-out audit
and ablation comparison. The final graph-expanded baseline was evaluated on
225 held-out cases, with 209 adjudicated as resolvable and 16 as genuinely
unresolved.

Headline values include Recall@1 `0.2791`, Recall@3 `0.4362`, Recall@5
`0.4410`, MRR `0.4880`, nDCG@5 `0.4548`, coverage `0.4933`, and abstention rate
`0.5067`.

These are **deterministic language-retrieval metrics against graded semantic
judgments**. They are not coffee flavor accuracy, sensory probabilities, or
evidence that a coffee objectively tastes like a returned concept. The high
abstention error also shows that the current lexical bridge misses many
resolvable expressions.

Consumer-conditioned ranking has not yet been calibrated. A future model must
be evaluated independently of the data used to design questions, features, or
thresholds.

### Context-prior calibration and adaptive questions

C0 preparation and C1 roast provide a soft contextual support envelope. They
may regularize a candidate region, break ties, stabilize noisy answers, or
provide a fallback. They are not direct flavor predictors and do not hard
exclude descriptors. Strong user answers can overcome weak context support.

Q1 is mandatory and adaptive. Q2 through Q4 are conditional on residual
uncertainty and expected marginal value; Q5 is exceptional. Calibration mode
must assign competing questions so counterfactual question value can be
estimated. Product-simulation mode measures the sequential policy, question
count, stopping, candidate usefulness, and override behavior.

The selected V0 research criterion is expected information gain accompanied by
interpretable candidate-elimination and burden diagnostics. No production
formula, weight, or stopping threshold is claimed before lawful real
observations support estimation.

### Consumer sensory references

The intended output is five primary and three secondary candidates that can
help the user name, refine, compare, and remember their own impression. Output
language must preserve candidate and reference semantics. The
[Product Contract V0](../product/PRODUCT_CONTRACT_V0.md) governs this layer.

## Why this can be scientifically credible

Credibility depends on the complete evidence chain:

- evidence-grounded ontology admission and concept typing;
- source and version provenance;
- rights-aware evidence retention and export policy;
- coffee sensory-science research;
- empirical datasets with documented sampling boundaries;
- explicit statistical and relation semantics;
- separate development and held-out evaluation;
- ablation against simpler baselines;
- calibrated uncertainty and abstention;
- reproducible normalization, migrations, and derived results; and
- honest reporting of unresolved cases and limitations.

Deep learning may later improve candidate generation or ranking, but its use
would not itself make the system scientific. It must demonstrate measurable
held-out benefit, preserve epistemic boundaries, and justify additional
complexity. The current validated baseline has no embedding, `pgvector`, or
production LLM dependency.

## PostgreSQL knowledge architecture

PostgreSQL 17 is the canonical system of record. Eight logical domains separate
claim types:

| Domain        | Responsibility                                                                                                   |
| ------------- | ---------------------------------------------------------------------------------------------------------------- |
| `ref`         | Controlled codes and their semantics.                                                                            |
| `kb`          | Canonical concepts, lexicalizations, schemes, relations, and governed sensory constructs.                        |
| `evidence`    | Sources, versions, rights, concept support, measurements, projections, and reference calibration.                |
| `corpus`      | Documents, raw and normalized observations, resolutions, frequencies, and co-occurrence statistics.              |
| `context`     | Preparation, beverage-addition, roast-scheme, and measured-roast context.                                       |
| `calibration` | Studies, protocols, conditions, samples, pseudonymous cohorts, questions, observations, analysis, and releases. |
| `ml`          | Versioned models, runs, mapping candidates, and candidate-signal ledgers.                                     |
| `audit`       | Independent review, lifecycle history, validation results, and explicit promotion.                            |

The fundamental separation is:

```text
canonical knowledge
≠ preparation / roast context
≠ raw corpus observation
≠ calibration observation or derived reference distribution
≠ model inference
≠ evaluation result
```

For example, a frequent corpus expression can remain an unresolved lexical
observation. A trigram candidate can remain a model inference. Neither becomes
a canonical concept or relation without an explicit, evidence-backed
governance decision.

The detailed schema and invariants are documented in the
[database guide](../../db/README.md),
[V0 architecture](../research/coffee-sensory-kb-v0/01_V0_ARCHITECTURE.md), and
[database invariants](../research/coffee-sensory-kb-v0/02_DATABASE_INVARIANTS.md).

## Uncertainty and abstention

`UNRESOLVED` is a valid result, not an implementation failure. The nearest
orthographic or graph candidate is not automatically safe. A candidate set
must preserve why each item appeared, and future ranking must distinguish lack
of evidence from evidence of absence.

The intended five-plus-three output is a product target, not permission to
force eight weak mappings. The final user behavior when fewer candidates meet
the support threshold remains a Round 3A-or-later research question.

## Current limitations

The current evidence supports a bounded foundation, not a finished consumer
system:

- The Round 2B corpus is primarily one historical secondary source spanning
  2017–2021; it is not globally or currently representative.
- No live roaster site was scraped, and publisher identities are not equivalent
  to independently rights-reviewed corpus sources.
- The lexical bridge is sparse: 57 of 1,713 normalized identities are strictly
  resolved, while 1,656 remain explicitly unresolved.
- Deterministic retrieval coverage is low, and the held-out audit used
  Codex-assisted non-human review rather than independent human reviewers.
- Preparation and roast context are represented, but the Round 2B corpus has
  zero structured coverage and no context-conditioned model is calibrated.
- The mandatory eight-family C0 and seven-level C1 projections remain untested
  with independent ordinary users; measured roast methods are stored without
  invented category cutoffs.
- Consumer-to-sensory-region ranking is not calibrated.
- Embeddings have not been benchmarked.
- No adaptive question policy or stopping threshold has been calibrated.
- No real replicated preparation-by-roast calibration observations or
  milk-mode sensory outcomes have been collected for this project.
- The protocol and schema are not a completed public sensory dataset.
- The PostgreSQL knowledge base is not connected to the static frontend.

Complete Round 2B boundaries are preserved in the
[executive receipt](../audits/coffee-sensory-kb-v0-round2b/00_EXECUTIVE_RECEIPT.md)
and [known gaps](../audits/coffee-sensory-kb-v0-round2b/12_KNOWN_GAPS.md).

## Next methodological work

The immediate program is an ethics-gated, same-coffee incomplete-factorial
pilot with separate reference-sensory and ordinary-user cohorts. It must
collect repeated sensory observations, calibration-mode question responses,
and product-simulation judgments without exposing roaster notes. Independent
evaluation and an embedding ablation follow only when the underlying evidence
can support them.

The ordered stages and gates are maintained in the
[Research Roadmap](../research/RESEARCH_ROADMAP.md).
