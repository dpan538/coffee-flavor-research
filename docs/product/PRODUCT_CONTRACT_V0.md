# Coffee sensory product contract V0

Status: current product-semantics source of truth

This contract defines what the intended Coffee Flavor Atlas product is trying
to do and how its output should be interpreted. It freezes product semantics,
not a final interface, questionnaire, universal roast standard, or ranking
implementation. The current C0/C1 interaction constraints were updated by the
Round 3B decision record on 2026-08-25.

## User

The target user is a person tasting coffee at home, in a café, or in another
ordinary drinking context. Professional cupping experience is not required.

The user wants to translate their own sensory experience into a more
structured set of coffee flavor references. Their perception is an input to be
supported, not an answer to be graded.

## Product goal

The system provides:

> Research-grounded sensory candidates that are compatible with the user's
> current perception.

Those candidates may help the user:

- strengthen an existing perception;
- refine a vague impression;
- discover a more specific descriptor;
- compare their perception with roaster, store, or packaging tasting notes;
- build a better sensory vocabulary; and
- remember sensory associations across future coffees.

The system is not designed to tell the user, “You are wrong,” and does not
treat the interaction as a sensory exam. A recommendation may indirectly
change or correct a user's interpretation, but correction is a possible
learning outcome rather than the objective function.

Industry tasting notes are language observations. Agreement or disagreement
with a note does not establish an objective flavor label for the coffee.

## Current interaction contract

The conceptual interaction is:

```text
C0 — Mandatory preparation / beverage context

C1 — Mandatory seven-level roast context

Q1
Q2
Q3
Q4

optional adaptive Q5

↓

5 primary sensory candidates
+
3 secondary candidates
```

C0 and C1 are required before sensory questions begin. C0 has no user-facing
`unknown`, `unsure`, or “I don't know” choice. C1 exposes at least seven
ordered project categories. C0 and C1 describe context. Q1 through Q4 describe
the user's current perception. Q5 is permitted only when an additional
low-burden discriminator is expected to improve a materially ambiguous result.

The eight C0 computational families and seven-level C1 minimum constrain the
data architecture. Final user wording, conditional subtypes, question wording,
branching policy, mappings from external source terms, and ranking features
still require research and held-out evaluation.

## C0 — preparation and beverage context

Preparation is mandatory in the first implemented product. The user selects
one valid broad family; exact brewer knowledge is optional and can be resolved
from familiar beverage names such as latte, V60, French press, cold brew, or
long black.

The current computational families are:

```text
filter / percolation
immersion
hybrid / manual pressure
espresso / short pressure
espresso + water
stovetop / boiled
cold extraction
espresso + milk
```

These technical labels are stable internal identities, not final UI copy.

Current research candidates include:

```text
pour-over / manual filter
batch filter
AeroPress
French press / immersion
espresso
ristretto / lungo
Americano / long black
moka
cold brew
cold drip
nitro
espresso + milk beverages
```

Possible milk-based subtypes include:

```text
flat white
latte
cappuccino
cortado
piccolo
macchiato
```

These are context identities, not sensory attributes or universal coffee
categories. Ongoing validation determines:

- an appropriate parent/child organization;
- which preparation differences materially affect sensory-reference ranking;
- which methods can share a broad computational family while retaining their
  distinct identities; and
- whether milk-based coffee requires a separate sensory mode.

`UNKNOWN`, `NOT_REPORTED`, `REPORTED_UNRESOLVED`, and `NOT_APPLICABLE` remain
valid database observation states for imported evidence. They are not user C0
choices. If a common consumer expression cannot yet be resolved, that is a
curation problem; it does not restore an unknown button.

A shared parent must not erase a meaningful distinction. For example, this
contract does not claim that `flat white = latte` or that
`long black = cold brew`.

## C1 — roast context

Roast context is mandatory in the first implemented product.

The proposed initial interaction scale is:

```text
extremely light
light
medium-light
medium
medium-dark
dark
extremely dark
```

This is the minimum current product interaction scheme. The categories are
project-defined and ordinal. They are not equal physical intervals, a
validated universal roast standard, a measured roast-color equivalence, or a
claim that all roasters use the terms consistently. In particular, ordinal
positions do not assert equal distance between adjacent categories.

Research and source review continue to investigate:

- formal roast-degree terminology;
- specialty-roaster terminology;
- measured roast-color systems;
- light, medium, and dark conventions;
- filter roast;
- espresso roast;
- omniroast;
- regional terminology; and
- other commonly used roast classifications.

Research must determine what can be asked reliably of an ordinary user, what
can be derived only from measured metadata, and how uncertainty should be
represented when a packaging term is ambiguous. A source label may remain
`REPORTED_UNRESOLVED`; the seven-level interaction minimum does not require a
forced mapping. `filter roast`, `espresso roast`, `omniroast`, Nordic, City,
and measured color systems remain source-specific unless evidence supports an
explicit mapping.

Interaction constraints are product decisions. Scientific calibration remains
empirical. The product requires at least seven ordinal roast categories to
retain distinctions important to the target market; empirical work validates
mappings into those categories. It does not prove seven objectively equal or
universal roast levels.

## Sensory question contract

The intended interaction burden is deliberately low:

```text
default: 4 sensory questions
optional: 5th adaptive discriminator
```

Preferred answer forms are:

```text
A / B / C
Yes / No
3-choice
4-choice
at most 4 choose 2
```

The default product should avoid full expert CATA forms, long descriptor
matrices, 15-point trained-panel scales, and large multi-select questionnaires.
Those methods may inform research, but they are not the intended ordinary
tasting interaction.

The final questions remain unresolved. Before adoption, they must be tested
for sensory meaning, user comprehension, discriminatory value, burden,
context sensitivity, and ranking benefit.

## Output contract

The intended output is:

```text
5 primary candidates
3 secondary candidates
```

Appropriate user-facing terms include:

```text
closest references
primary candidates
also consider
secondary candidates
```

The output must not be described as a `true flavor probability`, `accuracy of
tasting`, or `correct answer`. A candidate ranking is a governed reference
result conditioned on available user input, evidence, and model limitations.

Internal ranking scores may exist later. User-visible percentages must not
imply calibrated sensory probabilities unless a future research round defines,
calibrates, and validates that interpretation explicitly.

The system must be able to express uncertainty, weak support, and abstention.
It must not force a superficially plausible reference simply to fill an output
slot. The final interface behavior for fewer than eight supportable candidates
remains to be researched.

## Scientific and model contract

The product may combine:

- evidence-grounded canonical sensory knowledge;
- preparation and roast context;
- rights-governed industry-language observations;
- deterministic lexical normalization;
- statistical models;
- NLP/ML candidate retrieval and ranking; and
- calibrated uncertainty and explicit abstention.

Scientific credibility comes from sensory-science research, source provenance,
empirical data, explicit statistical semantics, held-out evaluation,
uncertainty handling, and reproducibility. Deep learning does not make a result
scientific by itself. Any future embedding or deep-learning component must
show a measurable held-out improvement over simpler baselines and retain an
interpretable candidate-signal record.

Canonical knowledge, corpus observations, model inference, and evaluation
results must remain distinguishable. Model output and corpus frequency cannot
automatically promote or modify canonical ontology assertions.

## What V0 freezes

This contract freezes:

- the ordinary tasting user and context;
- assistance and vocabulary learning as the product goal;
- compatibility with current perception rather than correction as the
  objective;
- low interaction burden;
- mandatory preparation and roast context before sensory questions;
- eight valid C0 computational families with no user-facing unknown choice;
- at least seven ordered C1 categories with distinct medium-light, medium, and
  medium-dark positions;
- a default of four sensory questions with at most one adaptive discriminator;
- five primary plus three secondary candidates as the intended output shape;
- non-probabilistic user-facing candidate language; and
- evidence, evaluation, reproducibility, and uncertainty as scientific gates.

## What remains open

This contract does not freeze:

- final consumer wording for the eight C0 families and conditional subtypes;
- mappings from external roast schemes to the seven project categories or to
  measured roast color;
- the wording or order of Q1–Q5;
- adaptive-question triggers;
- a sensory-region representation;
- consumer-to-region model features;
- ranking algorithms or thresholds;
- whether embeddings provide useful incremental value;
- the API contract; or
- final frontend interaction and visual design.

Those questions belong to the staged program in the
[Research Roadmap](../research/RESEARCH_ROADMAP.md). The supporting scientific
boundary is documented in the
[Methodology Overview](../methodology/METHODOLOGY_OVERVIEW.md).
