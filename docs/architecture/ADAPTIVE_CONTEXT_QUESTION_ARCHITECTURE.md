# Adaptive context and question architecture

Status: Round 3C V0 architecture contract, updated by the Round 4A sequence

## Purpose

This architecture defines how preparation, roast, sensory answers, semantic
signals, and ontology structure may contribute to an ordinary user's candidate
references. It is a calibration contract, not a claim that preparation or roast
determines flavor.

## Input sequence

```text
C0 mandatory preparation
C1 mandatory seven-level roast
Q1 mandatory adaptive question
Q2-Q4 required adaptive questions
Q5 exceptional
```

Question content remains context-adaptive, while Round 4A requires Q1–Q4 in
every completed prototype path. Q5 is available only for exceptional residual
ambiguity. A future learned stopping policy may be evaluated only after the
task-specific behavioral contract and data gates pass.

## Candidate flow

```text
C0 + C1
-> initial contextual envelope
-> Q1 selection
-> candidate update
-> uncertainty check
-> next-question selection or stop
-> 5 primary + 3 secondary candidates
```

Conceptually, the candidate state after answer step `t` is:

```text
P(D | C0, C1, A1...At)
```

`D` denotes descriptor candidates and `A1...At` denotes user answers. This
notation describes the desired conditional state; it does not declare that the
current system estimates calibrated probabilities.

## Signal separation

The candidate engine must retain the meaning and provenance of each signal:

| Signal                       | Permitted role                                                      | Must not be interpreted as                     |
| ---------------------------- | ------------------------------------------------------------------- | ---------------------------------------------- |
| Context support              | Soft prior, tie-breaker, noisy-answer stabilizer, fallback envelope | A direct flavor generator or hard sensory rule |
| Sensory-answer evidence      | Direct evidence about the user's current perception                 | Objective coffee truth                         |
| Semantic/NLP similarity      | Candidate generation from language similarity                       | Perceptual identity or calibrated probability  |
| Ontology structure           | Typed navigation and bounded graph expansion                        | Universal perceptual distance                  |
| Industry-language prevalence | Descriptive evidence about language use                             | Sensory validity or coffee ground truth        |
| Epistemic confidence         | Uncertainty about evidence, mappings, or model support              | User correctness                               |

Scores from different signals must not be flattened into an unexplained
percentage. Candidate ledgers must record which signal admitted or moved an
item and the semantics of any internal score.

## Context prior and override behavior

C0 and C1 define a soft contextual support envelope. They may reduce implausible
equivocation, break ties, stabilize noisy answers, down-rank weakly supported
candidates, or provide a fallback when answers are sparse. They do not create
flavor labels.

Strong sensory-answer evidence can override weak context support. The V0
calibration study must measure the rate and quality of such overrides rather
than treat them as errors.

Roast and preparation alone must not hard-delete a descriptor. A descriptor may
receive low context support and still rank highly when the user's answers
provide strong compatible evidence.

## Limited hard exclusions

Hard exclusion is reserved for governed boundary conditions, not ordinary
preparation or roast differences. Possible cases are:

- a strongly added flavoring outside the default bean-sensory scope;
- an invalid or impossible database state;
- an explicit product-boundary exclusion; or
- a rights or lifecycle rule that prevents an item from entering an output.

Milk mode remains a separate evaluation stratum. It is not permission to erase
explicit perception or to pool milk and black-coffee evidence without testing.

## Q1 selection

Q1 may test a broad family, a contrast, a familiar reference, or a specific
candidate cluster. It need not always be a generic taste question. A V0 policy
may use an interpretable decision tree or expected information-gain lookup only
after calibration data support the split.

Round 3C compares entropy reduction, expected candidate elimination, expected
nDCG gain, candidate-region dispersion, tree impurity, and Bayesian expected
information gain. The selected V0 research policy is expected information gain
with explicit candidate-elimination and burden diagnostics. The exact formula,
weights, and thresholds remain preregistered targets, not invented production
coefficients.

## Adaptive stopping

After each answer the engine must evaluate residual uncertainty and the marginal
value of another question. A later calibrated policy may stop when all declared
criteria pass, for example:

- the primary candidate region is sufficiently concentrated;
- the estimated marginal information gain is below a frozen threshold;
- the 5 + 3 candidate set is stable under plausible answer noise; and
- no declared safety, abstention, or conflict condition requires another
  discriminator.

Q2 through Q4 are conditional. Q5 is exceptional. The maximum sensory-question
budget is five. Until real observations support thresholds, the policy is a
protocol target and dry-run state machine only.

## Illustrative, non-universal path

The following example demonstrates override behavior. It is not a universal
dark-filter question or a scientific rule:

```text
C0 = filter / percolation
C1 = dark

context envelope:
  jasmine support is relatively low

Q1:
  A. jasmine / flower / fragrant tea
  B. cocoa / nut / caramel
  C. roast / spice / smoke

user answer:
  A, followed by strong jasmine-compatible evidence

candidate update:
  jasmine may rank highly despite weak initial context support
```

The incorrect implementation is `dark roast -> jasmine forbidden`.

## Calibration and product-simulation modes

Calibration mode assigns a randomized or balanced subset of competing
questions. It estimates answer distributions and counterfactual question value.
It is deliberately not the final product experience.

Product-simulation mode selects questions sequentially and measures question
count, stopping, candidate usefulness, context conflicts, and explicit-user
overrides. Evaluation must compare fixed order, context-adaptive Q1, and
information-gain sequences.

## Output semantics

The product returns five primary and three secondary candidate references when
support permits. It does not return a correct tasting answer, objective flavor,
or true flavor probability. Internal values must retain their actual semantics,
and the system may abstain when support is inadequate.

## Frozen and unresolved

Frozen in Round 3C:

- C0 and C1 are soft contextual priors;
- Q1-Q4 are required and adaptive in content;
- Q5 is exceptional;
- explicit sensory evidence may override weak context support;
- roast and preparation do not hard-delete descriptors;
- calibration and product-simulation modes are distinct; and
- the output remains candidate references.

Unresolved until lawful real observations exist:

- production prior strengths;
- question information-gain estimates;
- stopping thresholds;
- subgroup calibration;
- candidate-ranking weights; and
- the final consumer wording and interface.
