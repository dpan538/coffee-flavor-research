# Held-out context metrics receipt

Split seed: `coffee-context-round3b-heldout-v1-20260825`  
Cases: 102 total / 17 held out  
Stratification: domain and authored semantic stratum  
Semantics: label-normalization quality, not coffee flavor accuracy

| Metric                                       |                    Value |
| -------------------------------------------- | -----------------------: |
| C0 held-out size                             |                        9 |
| C0 family coverage                           |                   1.0000 |
| C0 leaf coverage                             |                   0.8889 |
| C0 Recall@1 family                           |                   1.0000 |
| C0 Recall@1 leaf (expected-leaf denominator) |                   1.0000 |
| C0 ambiguous / unresolved / gross error      | 0.0000 / 0.0000 / 0.0000 |
| C1 held-out size / known expected            |                    8 / 5 |
| C1 exact / adjacent agreement                |          1.0000 / 1.0000 |
| C1 coverage / unresolved                     |          0.6250 / 0.3750 |
| C1 precision / gross error                   |          1.0000 / 0.0000 |
| C1 mean absolute ordinal category error      |                   0.0000 |

`C0_NORMALIZATION_DATA_SUFFICIENT=false` and
`C1_NORMALIZATION_DATA_SUFFICIENT=false`: cases are project-authored contract
fixtures, not an independent ordinary-user sample.
