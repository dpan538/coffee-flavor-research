# Experiment registry

## Current receipt

```text
MODEL_RUN_COUNT=0
ML_BASELINE_RUN=false
EMBEDDING_BASELINE_RUN=false
CROSS_ENCODER_RUN=false
DEEP_LEARNING_MODEL_RUN=false
RANKING_MODEL_TRAINED=false
ADAPTIVE_POLICY_TRAINED=false
```

No experiment entry is active. Architecture documents, SQL `ml` schemas,
synthetic fixtures, or dry-run workflows do not count as model runs.

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

Until these conditions and authorization exist, the correct action is to leave
the registry empty.
