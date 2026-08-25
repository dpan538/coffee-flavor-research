# Coffee Sensory Context Calibration Protocol V0

Status: preregistered design draft; physical collection is not authorized

## Study purpose

The study estimates how soft preparation/roast context support and low-burden
sensory answers can reduce candidate uncertainty while preserving explicit,
unusual perceptions. It does not test whether context objectively determines
flavor.

## Selected minimum pilot

The minimum engineering and protocol-feasibility design uses:

| Element                           |                        Selected value |
| --------------------------------- | ------------------------------------: |
| Green coffee lots                 |                                     2 |
| Roast batches                     | 14 (seven project categories per lot) |
| C0 families represented           |                                     7 |
| Unique condition cells            |                                    66 |
| Independent beverage replicates   |                                     2 |
| Beverage samples                  |                                   132 |
| Reference sensory assessors       |                                    12 |
| Ordinary users                    |                                    60 |
| Reference sessions per assessor   |                                     6 |
| Ordinary-user sessions per person |                                     2 |

Three core black-coffee families—filter/percolation, immersion, and
espresso/short pressure—are crossed with all seven roast categories for both
lots: `2 × 7 × 3 = 42` cells.

Four additional families—hybrid/manual pressure, espresso + water, cold
extraction, and espresso + milk—are included at light, medium, and dark anchor
categories for both lots: `2 × 3 × 4 = 24` cells.

The total is 66 cells and 132 independently prepared beverage samples at two
replicates. Stovetop/boiled is explicitly deferred from the minimum pilot and
must be added in a later release. The seven-level project scheme is not
collapsed.

## Feasibility and precision boundary

The minimum pilot is sized to rehearse 14 roast batches, seven preparation
families, all roast labels, repeats, schedules, capture, and import while
keeping a reference session to at most 11 samples. Six reference judgments per
beverage sample require 792 reference presentations, or 66 presentations per
assessor across six sessions. Sixty ordinary users tasting 12 samples each
provide 720 ordinary-user presentations.

At roughly five to six ordinary-user observations per beverage sample and six
reference judgments per sample, worst-case binomial uncertainty is far too wide
for production cell-level calibration. The minimum pilot is therefore justified
by operational feasibility, not statistical power for product claims. A
simulation using the observed variance and missingness is required before the
preferred study is launched.

Estimated physical collection is 12–16 preparation days plus 4–6 weeks for
participant scheduling and two weeks for quality review. Major costs are green
coffee, 14 controlled roast batches, preparation labor/equipment, measured
roast color, water and milk control, participant compensation, facilities, and
ethical administration.

## Preferred calibration study

The preferred study uses eight green lots, 56 roast batches, four core families
across all roasts, three additional families at anchor roasts, three beverage
replicates, 24 reference assessors, and 240 ordinary users. The planned matrix
contains 296 condition cells and 888 beverage samples. It supports partial
pooling, coffee-lot grouped development/validation/test splits, context
ablation, question-policy comparison, and preliminary subgroup estimates.

With 2,880 ordinary-user presentation trials, balanced allocation should target
at least 100 responses for major question/context strata, giving an approximate
worst-case proportion standard error near 0.05 before clustering. Final sample
size must be revised by simulation using minimum-pilot response variance,
dropout, question exposure, and intraclass correlation.

Estimated collection is 10–14 weeks. Major costs are 56 controlled roast
batches, 888 preparations, facilities, compensation, bilingual materials,
measurement, and data governance.

## Expanded public dataset

The expanded design targets 24 green lots, 168 roast batches, all eight C0
families, all seven roast categories, black and milk strata, three beverage
replicates, approximately 3,456 beverage samples, 40 reference assessors, and
800 ordinary users. It supports stronger language/expertise slices, milk-mode
analysis, lot-level external testing, and ML benchmarks. It is a staged
multi-site program, not a single pilot commitment.

Estimated collection is 9–18 months. Cost drivers include multi-site
coordination, all-family equipment, 168 controlled roasts, milk/alternative
milk arms, 3,456 preparations, participant compensation, bilingual governance,
archival release, and independent review.

## Milk mode

Milk samples use the same espresso base batch and recipe as their paired black
espresso condition. The minimum pilot uses one declared pasteurized dairy milk,
a frozen mass proportion, and a frozen served beverage volume. Milk identity,
mass, proportion, texture procedure, and serving time are captured. Alternative
milk is deferred. Black and milk observations are analyzed separately before
any hierarchical pooling.

## Cohorts

Reference sensory assessors use a reduced descriptor shortlist, controlled
dimension scales, repeats, and uncertainty capture. Their observations form a
reproducible reference distribution, not objective truth.

Ordinary users answer short consumer-readable questions, report familiarity
and optional confidence where approved, and judge candidate-reference
usefulness. Expertise and language are stored separately. Cohorts are never
silently merged.

## Observation instruments

Reference sessions combine reduced CATA, RATA only where intensity adds value,
basic taste/tactile scales, and a free-text discovery field. No assessor sees
all 92 descriptors. Each form uses:

```text
core descriptors
+ context-relevant candidates
+ randomized adjacent/negative descriptors
+ free text
```

The shortlist and order are versioned. Negative and adjacent items prevent the
form from mechanically forcing the ontology.

Ordinary-user questions use yes/no, A/B, A/B/C, four choices, or four choose at
most two. Long expert multi-select instruments are excluded from the product
simulation.

## Calibration and product-simulation modes

Calibration mode assigns a balanced subset of competing questions independent
of the current path. It estimates answer distributions and question value.

Product-simulation mode applies the frozen policy state machine:

```text
C0 + C1 -> Q1 -> update -> stop or Q2 -> ... -> exceptional Q5
```

The two modes use separate assignment records. Calibration-mode burden is not
reported as the final product experience.

## Randomization and bias control

- Generate sample and question schedules from a recorded deterministic seed.
- Balance sample order within cohort and session.
- Randomize question and descriptor-list order within declared constraints.
- Blind coffee identity, roast, preparation details, and roaster notes during
  primary collection.
- Reveal roaster notes only in a separate comparison stage.
- Separate repeat samples and avoid obvious adjacent duplicates.
- Cap reference sessions at 11 samples and ordinary-user sessions at 6.
- Provide the same palate reset, rest interval, and neutral instructions.
- Freeze serving temperature windows and record deviations.
- Counterbalance language order in bilingual material.
- Record carryover, fatigue, protocol deviations, and incomplete responses.

## Preregistered baselines

Compare:

```text
A. question answers only
B. C0/C1 prior only
C. C0/C1 + Q1
D. C0/C1 + Q1-Q2
E. C0/C1 + adaptive Q1-Q4
F. C0/C1 + adaptive Q1-Q5
```

Context ablations are no context, C0 only, C1 only, and C0 + C1. Question
policies are fixed order, context-adaptive Q1, and expected-information-gain
adaptive sequence. Prior strength comparisons use interpretable soft weights;
hard context exclusion is not a baseline.

Methods evaluated are Bayesian hierarchical, mixed-effects logistic/ordinal,
partial-pooling prevalence, regularized logistic, decision-tree information
gain, and simple learning-to-rank baselines. Deep learning, embeddings, and
`pgvector` are outside Round 3D.

## Outcomes and metrics

Candidate metrics include Recall@5/@8, nDCG@5/@8, MRR where meaningful,
candidate-region overlap, usefulness, and diversity. Context metrics include
implausible-candidate rate, conflict rate, explicit-user-override rate, and
sensitivity to incorrect C0/C1. Adaptive metrics include question count,
information reduction, early stop, unresolved rate by step, and marginal value
of Q2–Q5. Reliability includes repeat stability, assessor agreement, and
uncertainty by coffee, expertise, and language.

These are not objective flavor-accuracy metrics.

## Analysis and split gate

No model tuning begins until a snapshot, grouped split, seed, grouping
variable, and case inventory are frozen. Coffee lot is the primary split group;
repeated samples and roast/preparation derivatives cannot cross splits.
Assessor holdout is a separate generalization analysis. The two-lot minimum
pilot cannot provide a defensible three-way lot split and is limited to
feasibility and descriptive rehearsal.

## Ethics, consent, and release gate

```text
HUMAN_PARTICIPANT_ETHICS_REQUIRED=true
INSTITUTIONAL_APPROVAL_STATUS=NOT_OBTAINED
PUBLIC_DATA_CONSENT_REQUIRED=true
ETHICS_OR_APPROVAL_GATE=false
CONSENT_MATERIAL_READY=false
PUBLIC_RELEASE_RIGHTS_READY=false
```

Engineering preparation and synthetic dry runs may proceed. Recruitment,
physical tasting, and real observation collection may not begin until all
three collection/release gates are true.

## Current scientific boundary

This protocol supports a future calibration study. It does not establish that
preparation and roast predict flavor, validate an adaptive policy, or create a
public sensory dataset before lawful real observations are collected and
released.
