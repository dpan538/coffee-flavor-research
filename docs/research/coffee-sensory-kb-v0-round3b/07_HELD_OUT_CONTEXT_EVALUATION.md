# Held-out context evaluation

The benchmark contains 102 project-authored cases across preparation and roast,
English and Simplified Chinese, consumer beverage/device names, technical
method names, qualitative categories, variants, and protected unresolved
styles. The frozen split has 85 development and 17 held-out cases. Rules were
derived from development cases; the evaluation script read the held-out set
once and persisted all predictions and grades.

| Metric                                  |                   Result |
| --------------------------------------- | -----------------------: |
| C0 held-out size                        |                        9 |
| C0 family coverage / Recall@1 family    |          1.0000 / 1.0000 |
| C0 leaf coverage / Recall@1 leaf        |          0.8889 / 1.0000 |
| C0 ambiguous / unresolved / gross error | 0.0000 / 0.0000 / 0.0000 |
| C1 held-out size (known expected)       |                    8 (5) |
| C1 exact / adjacent agreement           |          1.0000 / 1.0000 |
| C1 coverage / unresolved                |          0.6250 / 0.3750 |
| C1 mapping precision / gross error      |          1.0000 / 0.0000 |

Coverage is not inflated by forcing protected roast labels into the nearest
category. Evaluation grade and unresolved state remain separate from sensory
probability. Because no independent ordinary-user sample was collected, both
normalization-data sufficiency decisions are false despite the clean regression
metrics.
