# Question bank and adaptive policy

## V0 bank

Round 3C seeds 12 language-specific question versions: six logical distinctions
in English and Simplified Chinese.

| Logical code        | Target distinction                                        | Options |
| ------------------- | --------------------------------------------------------- | ------: |
| `family_direction`  | floral/tea vs cocoa/nut/caramel vs roast/spice/smoke      |       3 |
| `fruit_direction`   | citrus vs berry vs tropical/dried fruit                   |       3 |
| `sweet_direction`   | sugar/brown sugar vs honey/caramel vs little/no sweetness |       3 |
| `roast_direction`   | smoke/ash vs cocoa/toast vs neither                       |       3 |
| `bright_acidity`    | bright/tangy present                                      |       2 |
| `texture_direction` | light/tea-like vs round/creamy vs heavy/drying            |       3 |

The copy is a design draft. It has not passed independent ordinary-user or
bilingual comprehension testing.

## Assignment semantics

Definitions store language, type, target, eligibility, modality, familiarity,
evidence status, options, and lifecycle. Each assignment stores calibration or
product-simulation mode, step, randomization key, and the actual candidate set
before the question.

Calibration mode balances competing questions to estimate counterfactual answer
distributions. Product-simulation mode chooses sequentially. The V0 research
criterion is expected information gain, accompanied by candidate-elimination,
nDCG, dispersion, and burden diagnostics.

## Stopping

Q1 is mandatory. After each answer the eventual policy evaluates residual
uncertainty, candidate-set stability, marginal information, and safety/conflict
conditions. Q2-Q4 are conditional and Q5 is exceptional. Thresholds remain
`UNRESOLVED` until real calibration observations exist.
