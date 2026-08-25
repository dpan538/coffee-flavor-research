# Round 3 context-calibration architecture decision

Date: 2026-08-25

Status: accepted for Round 3C protocol and database design

## Decision

The project will treat C0 preparation and C1 roast as soft contextual priors,
require a context-adaptive Q1, ask Q2 through Q4 only while additional
discrimination is useful, and reserve Q5 for exceptional ambiguity. Strong
sensory-answer evidence may override weak context support. The project will
design an original public calibration dataset because no reviewed public
resource is sufficient for this complete function.

## Evidence-status vocabulary

- `PRODUCT DECISION`: a governed interaction or output choice.
- `DIRECTLY SUPPORTED`: supported by inspected coffee-specific evidence.
- `SUPPORTED BY TRANSFERABLE METHOD`: supported by established sensory,
  experimental-design, or statistical methodology applied cautiously.
- `DESIGN INFERENCE`: a provisional design selected for testing.
- `UNRESOLVED`: requires data or governance not yet available.

## Rationale

### C0 and C1 are contextual priors

`PRODUCT DECISION`: Preparation and roast are mandatory context inputs.

`DIRECTLY SUPPORTED`: Reviewed coffee studies demonstrate that roast and brew
conditions can change sensory distributions under controlled conditions. They
do not establish universal descriptor rules across all coffees, recipes, or
people.

`DESIGN INFERENCE`: Context may regularize a candidate region, break ties, and
stabilize noisy answers. It must not be represented as a direct flavor
generator.

### Q1 may be fine-grained

`SUPPORTED BY TRANSFERABLE METHOD`: An information-seeking question is useful
when its response partitions the current candidate state. The best partition
may be a broad family, a contrast, or a specific familiar reference.

`PRODUCT DECISION`: Q1 may therefore be specific when a calibrated policy shows
that it is the most useful low-burden discriminator for the current context.

### Q2 is conditional

`PRODUCT DECISION`: The product will not impose four fixed sensory questions.

`DESIGN INFERENCE`: If Q1 produces a stable, concentrated candidate region,
another question may add burden without material ranking value. Q2-Q4 are asked
only while residual uncertainty and expected marginal value justify them. Q5 is
exceptional.

### User evidence may override context

`PRODUCT DECISION`: Explicit perception is more direct evidence about the
user's current experience than a population-level context tendency.

`DESIGN INFERENCE`: A soft prior can be overcome by strong compatible answers.
The calibration study will measure override behavior and context conflicts. It
will not label unusual but coherent perceptions as errors merely because they
are contextually uncommon.

### Why an original public calibration dataset is needed

`DIRECTLY SUPPORTED`: The Round 3C source audit found useful public fragments:
consumer CATA/JAR rows, controlled roast/brew sensory experiments, chemical
meta-analysis, quality scores, milk/preparation usage records, and large taste
surveys. No inspected resource combines controlled coffee identity, multiple
preparation families, multiple roast categories, replicated sensory outcomes,
ordinary-user adaptive-question responses, suitable held-out grouping, and
rights compatible with the intended public artifact.

`PRODUCT DECISION`: The project will publish a versioned protocol, schema, and
eventually lawfully collected observations under the provisional title Coffee
Sensory Context Calibration Dataset. A protocol-only package is not called a
sensory dataset release.

### Why corpus and ontology resources are insufficient

`DIRECTLY SUPPORTED`: The ontology represents governed concepts and the corpus
represents observed language. Neither records counterfactual user answers to
competing questions or controlled same-coffee preparation-by-roast sensory
responses.

`PRODUCT DECISION`: Canonical ontology, corpus observations, calibration
observations, derived reference distributions, and model outputs remain
separate claim layers.

### Why expert intuition cannot define the final policy

`SUPPORTED BY TRANSFERABLE METHOD`: Adaptive selection and stopping require
answer distributions, competing-question comparisons, uncertainty estimates,
and held-out evaluation. Expert intuition may propose candidates, but using it
as the final policy would conceal assumptions and prevent calibration.

`UNRESOLVED`: Production question weights, prior strengths, and stopping
thresholds await lawful real observations.

## Frozen decisions

- C0 is mandatory and one of the current eight preparation families.
- C1 is mandatory and uses the current seven-level ordinal project scheme.
- C0/C1 provide soft support and no roast/preparation-only hard exclusion.
- Q1 is mandatory and adaptive.
- Q2-Q4 are conditional; Q5 is the maximum exceptional discriminator.
- Calibration mode and product-simulation mode are distinct.
- Output is five primary plus three secondary candidate references.
- The minimum engineering pilot preserves all seven roast labels and multiple
  C0 families using an incomplete, same-coffee crossed design.
- Real human observations require ethics/approval, consent, privacy, and public
  release rights gates.

## Unresolved decisions

- independently validated consumer wording;
- sufficient reference and ordinary-user sample sizes for production claims;
- calibrated context-prior strength;
- question information gain and stopping thresholds;
- milk-mode generalization;
- final ranking model and uncertainty semantics; and
- institutional approval and public-release authorization for collection.

## Consequences

Round 3C may implement architecture, preregistration, and a forward-only
calibration schema without collecting observations. Round 3D may implement and
dry-run the pilot infrastructure. Neither phase may fabricate sensory data or
claim that preparation and roast predict flavor.
