# Model card draft

`MODEL_STATUS=NOT_TRAINED`

No model artifact, parameters, evaluation run, performance metric, probability,
or deployment exists. This card defines the information required if a separately
authorized experiment later passes its data gate.

## Intended task

Initial candidate: professional descriptor normalization or 5+3 candidate
ranking. The experiment must choose exactly one primary task contract and name
any auxiliary objectives.

## Candidate architecture

Start with the existing deterministic lexical/relationship baseline. The first
learned candidate should be interpretable: regularized linear classification or
ranking, calibrated tree/boosting, or a simple pairwise ranker. Embedding and
neural candidates require later gates and direct comparison with simpler models.

## Required input

- frozen source-native or interaction inputs with governed locators;
- task-eligible targets and review lineage;
- feature definitions with provenance and missingness;
- exact candidate universe and exposure policy;
- model-use rights/consent snapshot; and
- grouped split manifest.

## Target interpretation

A normalization output is a governed candidate or abstention. A ranking output
orders perception-compatible references for the provided evidence. Neither is
proof of objective flavor or expert sensory judgment.

## Evaluation plan

Use [the evaluation and split plan](./EVALUATION_AND_SPLIT_PLAN.md). Compare
against deterministic and simple baselines; report family/language/context/tail
slices, abstention, coverage, calibration where defined, and user-research
outcomes separately.

## Foreseeable risks and failure modes

- publication, coffee, phrase, reviewer, or participant leakage;
- dominant-source or frequent-label bias;
- package-note suggestion and exposure bias;
- false precision for broad/translation-sensitive descriptors;
- incorrect use of context as a hard label prior;
- rights or consent drift after data freeze;
- low coverage hidden by aggregate metrics;
- consumer language promoted as professional truth; and
- confident output when abstention is appropriate.

## Abstention and uncertainty

The system must support unresolved normalization, no candidate above threshold,
none-of-these, and policy stop. Thresholds require held-out calibration and
cannot be invented in UI copy.

## Monitoring if later deployed

Monitor input/candidate drift, coverage, abstention, latency, family/language
slices, question burden, none-of-these, user trust, rights/consent changes, and
reported harms. Deployment requires a rollback path to the deterministic
baseline.

## Retraining or retirement conditions

Retraining would require a new eligible manifest, split audit, rights/consent
snapshot, evaluation, and versioned receipt. Retire or roll back if source rights
change, leakage is found, held-out performance regresses, abstention fails,
unsupported groups are harmed, or user burden rises without benefit.

## Empty performance section

| Metric            | Value         | Status      |
| ----------------- | ------------- | ----------- |
| All model metrics | not available | NOT_STARTED |
