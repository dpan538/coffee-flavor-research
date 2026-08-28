# ML/DL problem definition

## Status

`MODEL_STATUS=NOT_TRAINED`

Six task definitions are staged below. A task becomes executable only after its
label, rights, review, diversity, and split requirements pass. “Model” here
describes a future problem class, not a completed run.

## Task 1 — professional descriptor normalization

| Field                     | Contract                                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------------------------- |
| Unit of observation       | one atomic source-native professional descriptor assertion                                              |
| Input                     | source-native expression, language, bounded context, source/evidence metadata                           |
| Target                    | one or more governed canonical descriptor candidates, or unresolved/abstention                          |
| Label source              | qualified reviewed P1/P2 strict professional evidence                                                   |
| Non-label auxiliary data  | P3/P4/P5 vocabulary, lexical similarity, typed relations, C0/C1 where observed                          |
| Loss type                 | multilabel classification/ranking with explicit abstention; deterministic baseline first                |
| Evaluation metrics        | macro/micro-F1, top-k recall, abstention precision, tail-label performance                              |
| Split unit                | effective coffee/entry/lot plus source family, edition, mirror, repeated service, review batch          |
| Rights requirements       | model-research permission for inputs/targets and allowed derived outputs                                |
| Known leakage risks       | publication mirrors, repeated services, same phrase across train/test, reviewer batch, source templates |
| Abstention behavior       | return `UNRESOLVED` when no governed candidate clears threshold                                         |
| Deployment interpretation | normalized reference candidate, not proof of objective flavor                                           |

## Task 2 — 5+3 sensory candidate ranking

| Field                     | Contract                                                                                                         |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Unit of observation       | one context-and-answer state with an exposed candidate universe                                                  |
| Input                     | C0, C1, question responses, governed candidate evidence                                                          |
| Target                    | ordered five primary and three secondary candidates or abstention                                                |
| Label source              | reviewed professional compatibility evidence plus separately consented behavioral relevance; roles kept distinct |
| Non-label auxiliary data  | relationship graph, source diversity, evidence/review strength, question state                                   |
| Loss type                 | pointwise/pairwise/listwise ranking; deterministic ordering baseline                                             |
| Evaluation metrics        | Recall@5, Recall@8, nDCG@5, nDCG@8, MRR, coverage, abstention rate, worst-family nDCG                            |
| Split unit                | coffee/lot, source family, edition, mirror, service, review batch, and user where applicable                     |
| Rights requirements       | model-use rights for professional inputs and explicit model-use consent for first-party signals                  |
| Known leakage risks       | same coffee/source in multiple layers, candidate exposure bias, user overlap, package-note leakage               |
| Abstention behavior       | show none-of-these and withhold low-confidence references                                                        |
| Deployment interpretation | ranks perception-compatible references; does not identify one true flavor                                        |

## Task 3 — co-assertion or association estimation

| Field                     | Contract                                                                        |
| ------------------------- | ------------------------------------------------------------------------------- |
| Unit of observation       | within-effective-record unordered descriptor pair/event                         |
| Input                     | de-inflated descriptor assertions with evidence/source/record identity          |
| Target                    | bounded association estimate with uncertainty, not ontology membership          |
| Label source              | governed within-record reviewed P1/P2 co-assertions                             |
| Non-label auxiliary data  | context, preparation service, source family, descriptor frequency               |
| Loss type                 | count/statistical association or calibrated pair model                          |
| Evaluation metrics        | held-out likelihood/ranking, stability, family-stratified coverage, calibration |
| Split unit                | effective record, coffee/lot, family, edition, mirror, repeated service         |
| Rights requirements       | model/statistical-use rights for contributing assertions                        |
| Known leakage risks       | pair explosion, duplicates, repeated services, dominant-source frequency        |
| Abstention behavior       | no association where support/diversity thresholds fail                          |
| Deployment interpretation | empirical co-assertion support, never fixed sensory causality                   |

## Task 4 — adaptive question selection

| Field                     | Contract                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| Unit of observation       | one eligible interaction state before the next question                                    |
| Input                     | candidate distribution, previous answers, context, remaining question bank                 |
| Target                    | next useful question or stop candidate                                                     |
| Label source              | consented interaction outcomes and prespecified information/usefulness objectives          |
| Non-label auxiliary data  | question semantics, latency, accessibility/burden flags                                    |
| Loss type                 | information-gain heuristic first; later contextual bandit or supervised policy             |
| Evaluation metrics        | entropy/ranking gain per question, completion time, drop-off, Q5 activation                |
| Split unit                | user, session, candidate set, question version, study batch                                |
| Rights requirements       | explicit consent for analytics and model use; question-bank rights                         |
| Known leakage risks       | repeat users, evolving question/candidate versions, outcome observed after policy exposure |
| Abstention behavior       | stop if expected value is low or burden/risk is high                                       |
| Deployment interpretation | chooses an information-seeking prompt, not a sensory conclusion                            |

## Task 5 — stopping policy

| Field                     | Contract                                                                                     |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| Unit of observation       | one post-answer interaction state                                                            |
| Input                     | current candidate distribution, uncertainty, question count, burden signals                  |
| Target                    | stop, continue, or exceptional Q5                                                            |
| Label source              | consented task outcomes and prespecified utility/cost tradeoff                               |
| Non-label auxiliary data  | latency, drop-off history, accessibility preferences                                         |
| Loss type                 | rule/threshold baseline; later cost-sensitive sequential prediction                          |
| Evaluation metrics        | average questions, task success, candidate gain, drop-off, Q5 activation, abstention quality |
| Split unit                | user, session, protocol/question/candidate version                                           |
| Rights requirements       | explicit first-party research/model consent                                                  |
| Known leakage risks       | tuning on test participants, post-outcome signals, policy/version drift                      |
| Abstention behavior       | stop without candidates if uncertainty remains too high                                      |
| Deployment interpretation | controls burden and uncertainty; not confidence theatre                                      |

## Task 6 — consumer-language comprehension mapping

| Field                     | Contract                                                                           |
| ------------------------- | ---------------------------------------------------------------------------------- |
| Unit of observation       | consumer phrase or consented user free-text span                                   |
| Input                     | wording, language, bounded context, source/consent role                            |
| Target                    | vocabulary variants, familiarity/ambiguity tags, candidate mappings, or unresolved |
| Label source              | rights-reviewed consumer-language annotations and consented comprehension tasks    |
| Non-label auxiliary data  | P3/P4 language, lexical frequency, translations                                    |
| Loss type                 | retrieval/classification/clustering with human review and abstention               |
| Evaluation metrics        | retrieval recall, mapping precision, ambiguity detection, subgroup comprehension   |
| Split unit                | source/author or user, product, time, language, review/session batch               |
| Rights requirements       | source model-use rights or explicit first-party model-use consent                  |
| Known leakage risks       | copied package text, repeated reviews, user overlap, translation near-duplicates   |
| Abstention behavior       | preserve unfamiliar/unresolved wording rather than force canonical promotion       |
| Deployment interpretation | helps communication and question design; not professional label truth              |

## Non-goals

- infer roast from flavor descriptors;
- treat rankings or scores as sensory labels;
- train on public material without model-use rights;
- collapse professional and behavioral relevance targets;
- produce an undifferentiated sensory “accuracy” score; or
- add a deep model before a task-specific deterministic/interpretable baseline.
