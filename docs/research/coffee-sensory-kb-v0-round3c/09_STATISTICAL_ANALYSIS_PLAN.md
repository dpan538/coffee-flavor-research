# Statistical analysis plan

Status: preregistration contract. All empirical quantities are `NOT_ESTIMABLE` until lawful real observations exist.

## Frozen comparisons

Candidate engines: (A) answers only, (B) C0/C1 only, (C) C0/C1 + Q1, (D) C0/C1 + Q1-Q2, (E) C0/C1 + adaptive Q1-Q4, and (F) C0/C1 + adaptive Q1-Q5. Context ablations are no context, C0 only, C1 only, and C0+C1. Question policies are fixed order, context-adaptive Q1, and expected-information-gain sequence. Soft-prior strengths are compared without hard sensory exclusion.

## V0 methods

Primary candidates are hierarchical/partial-pooling ordinal or logistic models and regularized logistic or learning-to-rank baselines. A small interpretable decision tree is a policy baseline. Bayesian models may quantify coffee, condition, assessor, and replicate uncertainty. Deep learning, embeddings, and pgvector are excluded from the first pilot because the anticipated data are small and interpretability is essential.

## Metrics

- candidate utility: Recall@5/@8, nDCG@5/@8, MRR when meaningful, region overlap, diversity, and judged usefulness;
- context behavior: implausible-candidate and context-conflict rates, explicit-answer override rate, and sensitivity to incorrect C0/C1;
- policy: average/median question count, uncertainty reduction, early-stop and unresolved rates, and marginal value of Q2-Q5;
- reliability: repeat stability, assessor agreement, and coffee-, assessor-, language-, and expertise-group uncertainty.

These are candidate-reference metrics, never objective-flavor accuracy.

## Split and decision rules

The preferred study freezes lot-grouped development, validation, and held-out test assignments before tuning, with a registered seed, snapshot hash, grouping inventory, and no shared lot or replicate family across splits. Hyperparameters and stopping thresholds use development/validation only. The held-out test is opened once. Confidence intervals and multiplicity handling are reported; missingness, deviations, exclusions, and all departures from this plan are disclosed.
