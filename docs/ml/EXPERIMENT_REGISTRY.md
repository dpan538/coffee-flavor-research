# Experiment registry

## Current receipt

```text
MODEL_RUN_COUNT=1
NORMALIZATION_ENGINEERING_SMOKE_RUN=true
CONDITIONAL_EXPERIMENTAL_NORMALIZATION_BASELINE_RUN=true
FIXED_CONFIGURATION_COUNT=6
ML_BASELINE_RUN=true
EMBEDDING_BASELINE_RUN=false
CROSS_ENCODER_RUN=false
DEEP_LEARNING_MODEL_RUN=false
RANKING_MODEL_TRAINED=false
ADAPTIVE_POLICY_TRAINED=false
MODEL_WEIGHT_FILE_COUNT=0
PRODUCT_MODEL_STATUS=NOT_AUTHORIZED
```

## Normalization engineering smoke — Batch 5

| Field                        | Recorded value                                                                                                  |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `experiment_id`              | `normalization-engineering-smoke-batch5-20260830`                                                               |
| `task_contract_version`      | `batch5.normalization-engineering-smoke.v1`                                                                     |
| `task`                       | cleaned professional lexical expression → governed canonical sensory concept ID                                 |
| `code_sha`                   | `NA_SELF_REFERENTIAL_COMMIT_SHA_REPORTED_IN_FINAL_TASK_RESPONSE`                                                |
| `input_corpus`               | `professional-descriptor-candidate-v1-30k` cleaned with `batch4.semantic-cleaner.v2`                            |
| `input_manifest_sha`         | `1383beaf6eed9dd2a0fdc2e1ffb02c581b82cd07d677c0f1056164bccf381532`                                              |
| `dataset_manifest_sha`       | `f30f7e03f7105d07defffe1a1b3f63c260c547cb4610db72ce3ceda8f2cf9daf`                                              |
| `rights_snapshot_sha`        | `9d056f851183f72609e4ca7727b2a4e06bb02a197dc509d62943825c085e054e`                                              |
| `rights_filter`              | `NONCOMMERCIAL_MODEL_RESEARCH ∈ {AFFIRMATIVE, AFFIRMATIVE_WITH_CONDITIONS}`                                     |
| `mapping filter`             | `VALID_STRICT_FLAVOR` + `MACHINE_GOVERNED_HIGH_CONFIDENCE` + governed target                                    |
| `eligible outputs`           | 1,005 across 198 lineage groups, 219 effective records, three families and 52 targets                           |
| `split_manifest_sha`         | `7824189b5f197cdb1221a34cb5129099a4d554d4533eb057a3b977a0b8bf8a15`                                              |
| `split protocol`             | deterministic grouped 70/15/15 plus all three leave-one-family-out runs                                         |
| `seed`                       | `20260829`                                                                                                      |
| `configuration matrix`       | six fixed lookup, majority, character/word TF-IDF nearest-neighbour or SGD log-loss configurations              |
| `selected configuration`     | `B2_CHAR_LINEAR`, selected once by grouped DEV macro-F1                                                         |
| `metrics_artifact_sha`       | `28688cd0b5ed2e972882839b8f0b642209d8e0b4d0d98b68b9c5d45187ddc12b`                                              |
| `selected grouped TEST`      | top-1 `0.984252`; top-3 `0.984252`; supported-target macro-F1 `1.000000`                                        |
| `primary unseen-form result` | top-1 `0.000000`; top-3 `0.000000` on two unseen test forms                                                     |
| `worst family holdout`       | Zenodo; macro-F1 `0.151142`                                                                                     |
| `runtime`                    | 15.879391 seconds, one model thread, peak RSS 678.484375 MB                                                     |
| `result interpretation`      | `SEEN_FORM_LOOKUP_ONLY`                                                                                         |
| `limitations`                | only 29 supported targets; 23 low-support targets; lexical-form-disjoint split infeasible; family transfer weak |
| `weight disposition`         | no estimator serialized, committed or released                                                                  |
| `status`                     | `ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY`                                                              |
| `promotion_decision`         | fixed baseline complete; ranking, product and further model work not authorized                                 |

The high grouped score is not a generalization claim. Of 127 grouped test
outputs, 125 use cleaned-form identities already present in training. Both
unseen forms fail at top-1 and top-3, while the largest source-family holdout
falls sharply. Metrics are machine-governed target self-consistency measures,
not human sensory, professional-judge, product, or deployment accuracy.

## Future registry fields

| Field                              | Requirement                                                |
| ---------------------------------- | ---------------------------------------------------------- |
| `experiment_id`                    | immutable task-specific ID                                 |
| `task_contract_version`            | exact problem definition                                   |
| `code_sha`                         | Git commit used                                            |
| `dataset_manifest_sha`             | immutable eligible data manifest                           |
| `rights_snapshot_sha`              | model/deployment/derived-output permissions                |
| `split_manifest_sha`               | grouped train/dev/test membership                          |
| `baseline_id`                      | prior system to beat                                       |
| `model_family` and `configuration` | reproducible algorithm/hyperparameters                     |
| `feature_manifest_sha`             | feature definitions and provenance                         |
| `started_at`, `completed_at`       | run timestamps                                             |
| `metrics_artifact_sha`             | complete results, including slices                         |
| `error_analysis_artifact_sha`      | failures, abstentions, contradictions                      |
| `status`                           | PLANNED, BLOCKED, VALIDATED, or historical run disposition |
| `promotion_decision`               | fail-closed outcome and authority                          |

## Advancement checklist

- task label source is allowed and sufficient;
- reviewed assertion and companion gates pass;
- model-use rights/consent pass;
- duplicate/leakage grouping passes;
- deterministic baseline is reproduced;
- metrics and rollback conditions are prespecified;
- no persistent synthetic empirical rows enter the run; and
- model training has separate authorization.

Any work beyond this fixed normalization baseline requires a new explicit
project-owner authorization.
