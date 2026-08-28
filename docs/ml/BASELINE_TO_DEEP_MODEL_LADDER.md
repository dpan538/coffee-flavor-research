# Baseline-to-deep-model ladder

`CURRENT_MODEL_LEVEL=LEVEL_0_DETERMINISTIC`

This is a gate sequence, not a roadmap that promises every level will be built.
Each level must beat the prior baseline on a frozen grouped split and must have
a rollback condition.

| Level                         | Candidate methods                                                                                            | Minimum data state                                                                       | Baseline to beat                          | Evaluation split                                 | Interpretability requirement                                            | Rollback condition                                              | Current status                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------- |
| 0 — deterministic             | exact lexical match, approved variants, `pg_trgm`, governed typed relationships, context filters, abstention | governed concepts and lexical evidence                                                   | unresolved-only and simple exact match    | source/phrase holdout where available            | explain matched phrase, rule, source, and abstention                    | remove a rule if it harms held-out precision or rights boundary | IMPLEMENTED / VALIDATED baseline |
| 1 — interpretable statistical | regularized logistic/linear ranker, calibrated tree/boosting, simple pairwise model, count features          | reviewed rights-cleared labels at task gate; stable features                             | Level 0                                   | coffee + source-family grouped                   | feature provenance, coefficients/importances, calibration, error slices | no material held-out gain or poor calibration/tail behavior     | BLOCKED                          |
| 2 — learning-to-rank          | pointwise, pairwise, or listwise candidate models                                                            | stable candidate generation, relevance targets, sufficient multi-target records          | best Level 0/1 ranker                     | coffee/family/edition/mirror/service/user groups | candidate features, exposure policy, rank rationale and ablation        | worst-family regression, exposure bias, or unstable coverage    | BLOCKED                          |
| 3 — embedding retrieval       | source-native phrase encoder, bi-encoder retrieval, multilingual consumer mapping                            | rights-cleared text/labels, multilingual test set, frozen candidate corpus               | deterministic and statistical retrieval   | source/phrase/translation-family holdouts        | nearest evidence examples, retrieval coverage, language slices          | no robust recall gain, harmful drift, or rights ambiguity       | BLOCKED                          |
| 4 — neural reranker           | cross-encoder or other neural candidate reranker                                                             | enough reviewed labels, stable retrieval, source-family holdouts, allowed model use      | best Level 2/3                            | strict grouped and temporal holdouts             | calibrated score meaning, error analysis, ablations, cost report        | gain not material after cost/latency/fairness review            | BLOCKED                          |
| 5 — adaptive policy           | information-gain heuristic, contextual bandit, supervised/sequential policy                                  | consented interaction histories, versioned exposures/outcomes, safe exploration contract | fixed question order and heuristic policy | user/session/protocol/time groups                | per-question expected value, stop reason, burden monitoring             | increased drop-off, unsafe exploration, or no task/user gain    | BLOCKED                          |

## Advancement rule

A level advances only when:

```text
GOVERNED_LABEL_GATE
AND MODEL_USE_RIGHTS
AND FROZEN_GROUPED_SPLIT
AND BASELINE_REPRODUCIBILITY
AND MATERIAL_HELD_OUT_GAIN
AND ERROR_AND_ABSTENTION_REVIEW
```

Do not begin with reinforcement learning for novelty. A deterministic
information-gain heuristic is the first policy baseline. Deep learning is an
option to evaluate, not an expected endpoint.
