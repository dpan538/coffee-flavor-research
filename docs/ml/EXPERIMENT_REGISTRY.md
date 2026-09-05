# Experiment registry

## M2 R1 repair and sensory foundation — 2026-09-05

R1 preserves D0 and all earlier weights/results. The preferred valid repaired
candidate is `M2_R1_FINAL_FIXED`; B2 remains the backend default. Positive broad
support no longer produces the diagnosed negative child contribution (54 to 0
synthetic cases), repeated evidence has zero gain, and direct-answer retention
is 1.0 before and after postprocessing. Full D0 recovery NDCG@5 is 0.475626,
below old JOINT's 0.536926. Common fine-descriptor comparisons with B2 in grouped
development CV and frozen M1 on the 17 historical groups remain inconclusive.

The separate, fixed A/B/T foundation experiment gives V0/V1-explicit/V2-CHECK
NDCG@5 of 0.444088/0.446288/0.425308. Explicit native-attribute MAE is 0.172885,
versus NMF's 0.249060. More complex profiles do not improve on the simple
attribute representation. CHECK corrects 2/90 initially wrong proxy directions
and loses 2/105 initially correct ones; 16 records are not identifiable for
directional evaluation. Both reloadable foundation bundles retain zero scoring
fusion, and CHECK remains a research component. Real-answer efficacy is not
evaluated. These A/B/T numbers cannot be directly compared to the earlier
visible/hidden recovery protocol's scores.

Strictly locked D0/D0+D1 vocabulary, outer/inner question catalogs and objectives
give 0.475626/0.459685 recovery NDCG@5; the interval crosses zero. New professional
source-native attributes and complete CATA support separate measured-view tasks,
without becoming runtime inputs or fine-descriptor negatives. Source products,
coffee lots, conditions and assessor observations are counted separately.
Acquisition and protocol checks continue within the authorized source block.

The single [R1 receipt](../../db/data/backend-sequential-model-v2/revisions/r1/run_receipt.json)
indexes retained local models, validation and actual data increments; the
[metrics](../../db/data/backend-sequential-model-v2/revisions/r1/metrics.json)
retain successful, failed and inconclusive comparisons. No frontend, CI
architecture, main-branch merge or weight release is part of this revision.

## Context-Validated Sequential Flavor Model v2 — active

V2 preserves the 973f814 experiment and treats its inspected 17 groups as
historical regression only. The first actual numerical checkpoint fits
C_BASE/C_C0/C_C1/C_ADD/C_JOINT with leave-one-coffee-group-out evaluation on
separate source-native aggregate targets. C0 standardized MAE reductions are
0.09055 (Iswaldi chemistry, two coffees), 0.06520 (Iswaldi consumer sensory,
same two coffees), 0.02767 (Stanek chemistry, six coffees), and 0.12519
(Vezzulli professional panel, two coffees). Source-native roast effects are
estimable only in Iswaldi's two-coffee crossed study; production seven-bin C1
effects remain NOT_ESTIMABLE. Small source-specific groups and aggregate
observations prevent a broad efficacy claim. No descriptor-ranking or user
accuracy claim follows from these numerical results.

The five model forms and all raw-unit errors, group intervals, perturbations,
source conditions and persistent model paths are recorded in the single
[v2 experiment](../../db/data/backend-sequential-model-v2/run_receipt.json).
M2 actual fitting is complete on 211 development records / 187 coffee groups
from Zenodo, INERA and Lengupá; one record lacks an interpretable target and
remains in the coverage denominator. Three-fold development recovery NDCG@5
is 0.534871 (ADD), 0.536926 (JOINT), and 0.528348 (HIER). JOINT minus ADD
is +0.002055, group 95% interval [-0.001821, 0.005967]: INCONCLUSIVE. HIER
minus JOINT is -0.008578 [-0.014935, -0.002840]: NO_IMPROVEMENT; the factor
branch is not selected. These are positive-description recovery proxies,
not independent product confirmation. Six-slot execution, feature parity,
answer replacement and terminal one-time feedback pass local unit tests.
Same-budget policy and F0/F1/F2 diagnostics are complete. The initial numerical
checkpoint is preserved externally; overall_liking was removed from the
consumer sensory-attribute block because it is a hedonic target.

At exactly five questions / 20 actual options, fixed/random/one-step/two-step
recovery NDCG@5 is 0.534849 / 0.496403 / 0.538193 / 0.539409. One-step and
two-step deltas versus fixed have intervals crossing zero; mean full-chain
simulation latency is approximately 38 / 37 / 296 / 2476 ms respectively.
Keep the fixed policy as the default. Q1 has zero measured ranking contribution;
Q0 alone has no supported gain but its removal from the complete chain loses
0.050161. Q2/Q3/Q4 prefix gains are 0.058792 / 0.039138 / 0.029968. These are
development trajectory diagnostics, not independent human question value.

F2 exceeds mechanical F1 by 0.027848 [0.010905, 0.044883] on hidden observed
descriptor recovery with visible-only simulated feedback: PROXY improvement
only. Selected candidates were already exposed, so 100% retention@8 by itself
is tautological and not a gain. Real feedback and independent product
confirmation remain NOT_EVALUATED. All 211 development cases remain in coverage;
one has no interpretable target and cannot contribute labelled ranking utility.

The new model does not replace old M1/B2. On common fine descriptors, the
new model is below B2 in development CV by 0.054455, and below frozen M1 on
17 historical regression groups by 0.077259 [0.004632, 0.169813] in error
magnitude. Broader vocabulary and source-native attribute recovery are not
proof of better fine flavor inference. The proxy can learn suppression of
already visible broad categories; this is an explicit product limitation.
All new and old weights are retained. Source hashes, nested feature isolation,
56 full context paths, feature parity, answer traces and reload checks pass.
Twenty anonymous comparison cases are retained privately with empty judgments;
10 development and 10 frozen historical review cases are separate, with no
fresh confirmation claim. The single experiment receipt gives the model path,
commands, fitted dependency versions, errors and local verification status.

## Backend flavor recovery — 2026-09-05 (current)

The owner authorized backend fitting for personal noncommercial research on
2026-09-05. Earlier no-training receipts below describe historical scope.

`backend-flavor-record-recovery-20260905` fits a regularized linear candidate
scorer on 79 records / 77 coffee groups, with 16 development and 17 locked test
groups. The task is `RECORD_RECOVERY_PROXY`; independent user-answer labels are
not available. Three regularization settings were actually fitted; development
data selected the retained M1 model. Test observed-descriptor recovery NDCG@5 is
0.495329 for M1 versus 0.465651 for B1/B2. The paired coffee-group difference is
0.029679, with 95% bootstrap interval [-0.037823, 0.097955]: `INCONCLUSIVE`.
All models cover every test case. Weights remain in owner-controlled local
storage. The core run remains frozen. Two additional fits completed with the
same core configuration: M1_BALANCED reproduces M1 because its one source was
already weighted equally by coffee group; M1_AUX adds allowed coffee cooccurrence
features from 21 Lengupá samples (15 have exact in-vocabulary leaf descriptions).
Both score 0.495329 on unchanged TEST. DEV did not improve, so the auxiliary
branch is rejected (`NO_IMPROVEMENT`). This is two source families used in
training features, with only the original source represented in TEST.

The live backend accepts required C0/C1 and arbitrary valid catalog answers,
recomputes idempotent answer updates and returns main ≤ 5 / secondary ≤ 3 with
an evidence-based next question or stop. Source-native roast text is not a
validated seven-level C1 mapping; live learned context effects are masked.
The frozen proxy's nominal roast features are reported as a limitation, not
as validated product context. B2 remains the guarded deterministic fallback;
M1_BALANCED is retained for proxy research, without a product promotion.

Question diagnostics show positive mean recovery changes for fruit (+0.03365)
and nut/cocoa (+0.01503), a small negative change for sweet (-0.00289), and zero
measured change in three other observed axes. Floral has no frozen answer
cases. These small-group intervals do not establish question value. Adaptive
versus fixed qualified order differs by +0.00260 at five questions under an
explicit visible-descriptor oracle; this is not real-user validation.

Twenty anonymous record comparisons (12 development / 8 locked evaluation)
are prepared locally; no human judgments have been entered. Complete validated
C0/C1 product cases and independent user-answer judgments remain unavailable.

Authoritative records: [manifest](../../db/data/backend-model-20260905/dataset_manifest.json),
[configuration](../../db/data/backend-model-20260905/experiment_config.json),
[metrics](../../db/data/backend-model-20260905/metrics.json), and
[run receipt](../../db/data/backend-model-20260905/run_receipt.json).

## Historical Batch 5 receipt

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

## Batch 6 status — no experiment run

`MODEL_RUN_COUNT` remains `1`: the historical Batch 5 engineering smoke is
unchanged. Batch 6 constructs `professional-descriptor-candidate-v2-40k`, a
typed semantic relation layer, cross-form benchmark candidates and a leakage
audit only. It does not train, select, rerun, serialize or release any model.

The Batch 5 interpretation addendum classifies its 127 selected test outputs
as 125 `SEEN_FORM_KNOWN_TARGET`, 0 `UNSEEN_FORM_KNOWN_TARGET`, and 2
`UNSEEN_TARGET_OPEN_SET`; the test-only clove and hay targets are correctly
recorded as train-unsupported. A later model authorization requires the
governed/review-ready cross-form benchmark, a fresh leakage audit and explicit
project-owner authorization.
