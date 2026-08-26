# Round 3J training-scale expected state

Frozen on 2026-08-26 before any Round 3J acquisition, download, or import. The
exact source checkpoint is
`c3ae9b880d85507a0b8b0298bb94ef013d02f928`, released as
`coffee-sensory-research-db-v0.1.0`. That database release, its annotated tag,
manifest, inventories, source snapshots, approved views, and historical
migrations are immutable. Round 3J is additive and may produce a later release
candidate only if its exit gate passes.

The machine-readable contract is
`db/data/round3j/training_scale_expected_state.tsv`.
`EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0` after acquisition starts. A
threshold may change only through a separate, evidence-backed methodology
commit demonstrating that the original metric is invalid; difficulty is not
evidence of invalidity.

## `BASELINE`

The verified v0.1.0 state is:

- `ROUND3_FOUNDATION_COMPLETE=true`
- `MODEL_PREBUILD_DATA_READY=true`
- `ROUND3_DATA_SCALE_COMPLETE=false`
- `ROUND3_TRAINING_CORPUS_READY=false`
- `ROUND3_EXIT_GATE_PASS=false`
- `TRAINING_EXPERIMENT_READY=false`
- `V0_1_0_MUTATION_COUNT=0`

The frozen inventory contains 2,996 governed unique normalized expressions;
three contemporary tasting-language source families and 3,289 contemporary
documents; two source-authored zh-Hans families and 249 zh-Hans sensory
expressions; nine coffee-sensory source families, 4,344 source-local sensory
observation rows, 230 source-local sample/configuration units, and 181 empirical
coverage cells. It also contains 97 relationship evidence claims, six
source-local supported memberships, four cross-source supported memberships,
six ranges with source-local evidence, four ranges with cross-source evidence,
20 model-prebuild features, and 12 model-prebuild source partitions.

The 230 source-local sample/configuration units are a baseline inventory count,
not yet a task-specific effective-sample count. Round 3J must separately audit
sensory effective samples, configurations, coffee identities, disclosed
participants/panels, and source families. Likewise, the 181 empirical coverage
cells must not be relabelled as preparation-by-roast cells without a
source-local context audit.

Canonical concepts remain 130 and active sensory attributes remain 92. No
canonical addition, split, merge, or retype is permitted.

## Effective training units

Round 3J does not define one global `TRAINING_SAMPLE_COUNT`. Each future task
uses its smallest defensible independent unit:

| Future task               | Effective training unit                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------ |
| Lexical normalization     | A unique source-authored expression with reviewed target or disposition and complete provenance        |
| Sensory/context modelling | An independent coffee/sample/configuration with source-local context and sensory outcome semantics     |
| Association modelling     | A source-qualified relationship, co-selection, or co-occurrence observation with method and provenance |

Raw rows, effective units, source-family gains, coverage gains, and unique
expression gains are reported separately. Repeated rows without new independent
units do not constitute material scale improvement.

## `MINIMUM_SCALE_STATE`

These are engineering entry targets for Round 4, not claims of statistical
power or scientific sufficiency.

| Plane                                                     | Minimum |
| --------------------------------------------------------- | ------: |
| Governed unique normalized expressions                    |   6,000 |
| Contemporary tasting-language source families             |       6 |
| Contemporary tasting documents                            |   6,000 |
| Source-authored zh-Hans source families                   |       4 |
| Source-authored zh-Hans sensory expressions               |     500 |
| Coffee-sensory source families                            |      12 |
| Source-local sensory effective sample/configuration units |     500 |

The lexical-normalization candidate additionally requires at least 5,000
training-eligible unique expressions, eight training source families, two
fully held-out source families, 500 source-authored zh-Hans eligible
expressions, label provenance of `1.0000`, deterministic duplicate control,
feasible grouped splits, a training-candidate maximum single-source-family
share no greater than `0.60`, and non-zero ambiguous and unresolved/abstention
evaluation strata.

The context candidate requires at least 400 effective samples, 250 observed
preparation-by-roast cells, eight contributing source families, and 300
coffee/sample groups. The relationship evidence plane requires at least 150
claims, six cross-source supported memberships, and five ranges with
cross-source evidence.

## `PREFERRED_SCALE_STATE`

| Plane                                                     | Preferred |
| --------------------------------------------------------- | --------: |
| Governed unique normalized expressions                    |    10,000 |
| Contemporary tasting-language source families             |        10 |
| Contemporary tasting documents                            |    12,000 |
| Source-authored zh-Hans source families                   |         6 |
| Source-authored zh-Hans sensory expressions               |     1,000 |
| Coffee-sensory source families                            |        15 |
| Source-local sensory effective sample/configuration units |     1,000 |
| Lexical training-eligible unique expressions              |     8,000 |
| Lexical training source families                          |        12 |
| Lexical held-out source families                          |         3 |
| zh-Hans lexical training-eligible expressions             |     1,000 |
| Context effective samples                                 |       800 |
| Observed preparation-by-roast cells                       |       400 |
| Context source families                                   |        12 |
| Relationship evidence claims                              |       250 |
| Cross-source supported memberships                        |         8 |
| Ranges with cross-source evidence                         |         6 |

The preferred training-candidate maximum single-source-family share is
`0.45`. A documented task-specific sampling or capping policy may reduce
training-candidate concentration, but the complete governed raw corpus must
remain preserved and every exclusion must retain its reason, source family,
original and retained counts, and deterministic seed/configuration.

## `TASK_SPECIFIC_READINESS_STATE`

All five readiness results are frozen as `false` before the eligibility,
duplicate, concentration, and grouped-split audits. v0.1.0 evidence rows are
not presumed to be training rows.

- `LEXICAL_NORMALIZATION_TRAINING_READY=false`. It may become true only when
  all lexical volume, source diversity, held-out-family, zh-Hans, provenance,
  duplicate-control, concentration, split-feasibility, and non-zero
  ambiguous/unresolved evaluation-stratum conditions pass. Candidate outcomes
  may be `ONE_CANONICAL_TARGET`, `MULTIPLE_PLAUSIBLE_TARGETS`,
  `RANGE_LEVEL_TARGET`, `SOURCE_LOCAL_ONLY`, `AMBIGUOUS`, `UNRESOLVED`,
  `ABSTAIN`, or `OUTSIDE_CURRENT_ONTOLOGY`; unresolved material must not be
  forced to one label.
- `ASSOCIATION_MODEL_TRAINING_READY=false`. It may become true only when
  multiple independent evidence families exist, source-local methods remain
  explicit, declared cross-source minima pass, positive and
  challenging/mixed evidence are sufficiently represented, grouped holdout is
  feasible, and no absence-derived negative labels exist.
- `CONTEXT_MODEL_TRAINING_READY=false`. It may become true only when effective
  sample/configuration, source-family, preparation/roast, and coffee/sample
  holdout gates pass while source-local outcome semantics remain available and
  no false pooled sensory scale is introduced.
- `QUESTION_MODEL_TRAINING_READY=false` because there are no real ordinary-user
  sequential responses, measured information gain, or observed stopping
  outcomes.
- `ADAPTIVE_POLICY_TRAINING_READY=false` for the same reason.

## `OBSERVED`

At the pre-acquisition checkpoint, every known main scale target is below its
minimum. Task-specific eligible counts, source concentration, duplicate groups,
label distributions, and split counts are `NOT_YET_AUDITED`; they must not be
inferred from raw inventory totals. `TRAINING_CORPUS_FROZEN=false`,
`HELD_OUT_SOURCE_SPLIT_READY=false`, and
`TRAINING_CORPUS_REPRODUCIBLE=false` until deterministic artifacts and gates
exist.

## `DELTA`

| Metric                                          | Minimum gap | Preferred gap |
| ----------------------------------------------- | ----------: | ------------: |
| Governed unique normalized expressions          |       3,004 |         7,004 |
| Contemporary tasting-language source families   |           3 |             7 |
| Contemporary tasting documents                  |       2,711 |         8,711 |
| Source-authored zh-Hans source families         |           2 |             4 |
| Source-authored zh-Hans sensory expressions     |         251 |           751 |
| Coffee-sensory source families                  |           3 |             6 |
| Source-local sensory sample/configuration units |         270 |           770 |
| Relationship evidence claims                    |          53 |           153 |
| Cross-source supported memberships              |           2 |             4 |
| Ranges with cross-source evidence               |           1 |             2 |

Lexical-eligibility and context gaps remain `NOT_COMPUTABLE_UNTIL_AUDIT`.
Their baselines must be derived under the task-specific effective-unit,
provenance, rights, and duplicate rules rather than copied from global row
counts.

## `DECISION`

`audit.run_training_experiment_readiness_gate()` or a repository-consistent
equivalent will report each task independently. Readiness is conjunctive within
each task; there is no weighted aggregate and no readiness result based on raw
database size alone. Unreviewed automatic normalization is not a gold label,
project or machine translation is not independent zh-Hans evidence, absence is
not negative association evidence, and incompatible source-local sensory
methods are never pooled for convenience.

Acquisition stops under exactly one of two conditions:

1. The Round 3 exit gate passes; freeze a reproducible training-corpus
   candidate and prepare Round 4.
2. Three consecutive targeted acquisition batches produce no material gain
   toward any failed training-readiness gate; return
   `ROUND3_SCALEUP_COMPLETE_WITH_TRAINING_GAP` and do not search indefinitely.

The Round 3 exit gate may become true only when all of the following hold:

- `TRAINING_CORPUS_FROZEN=true`
- `LEXICAL_NORMALIZATION_TRAINING_READY=true`
- at least one of `ASSOCIATION_MODEL_TRAINING_READY=true` or
  `CONTEXT_MODEL_TRAINING_READY=true`
- `HELD_OUT_SOURCE_SPLIT_READY=true`
- `TRAINING_LABEL_PROVENANCE_RATE=1.0000`
- `TRAINING_SET_SOURCE_CONCENTRATION_ACCEPTABLE=true`
- `TRAINING_CORPUS_REPRODUCIBLE=true`

Until then, `ROUND3_EXIT_GATE_PASS=false`. Question and adaptive-policy
readiness do not block Round 4 when the lexical gate and at least one of the
association/context gates pass. Only tasks marked ready may later be authorized
for Round 4 experimentation.

Throughout Round 3J:

- `ML_BASELINE_RUN=false`
- `RANKING_MODEL_TRAINED=false`
- `ADAPTIVE_POLICY_TRAINED=false`
- `DEEP_LEARNING_MODEL_RUN=false`
- `EMBEDDING_BASELINE_RUN=false`
- `PGVECTOR_REQUIRED=false`
- `REAL_HUMAN_COLLECTION_PERFORMED=false`
- `REAL_OBSERVATION_COUNT=0`
- `QUESTION_USER_VALIDATED_COUNT=0`
- `QUESTION_INFORMATION_GAIN_ESTIMATED_COUNT=0`

Deterministic statistics, descriptive association analysis, corpus profiling,
split construction, and training-corpus validation are allowed. Model fitting,
embedding generation or benchmarking, cross-encoder or learning-to-rank work,
adaptive-policy or context-prior fitting, fine-tuning, hyperparameter search,
fabricated participant responses, fabricated lexical variants, and ontology
expansion are prohibited.
