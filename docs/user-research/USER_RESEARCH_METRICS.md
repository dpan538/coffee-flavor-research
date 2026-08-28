# User-research metrics

No single “accuracy” score represents usability, comprehension, sensory
agreement, behavioral relevance, and model performance. Each measure below has
a distinct interpretation and denominator.

| Metric                       | Layer                             | Definition                                                                              | Key qualification                              |
| ---------------------------- | --------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Task completion rate         | Usability                         | completed eligible tasks / started eligible tasks                                       | report exclusion and failure reasons           |
| Median completion time       | Usability                         | median elapsed time for defined task                                                    | separate completed and abandoned sessions      |
| Median number of questions   | Usability / policy burden         | median questions shown before result or exit                                            | stratify by stop reason                        |
| Q5 activation rate           | Policy burden                     | sessions shown exceptional Q5 / eligible sessions                                       | lower is not automatically better              |
| Drop-off by question         | Usability                         | exits after each exposure / exposures at that step                                      | separate technical failures                    |
| Descriptor familiarity       | Comprehension                     | self-report or recognition under specified instrument                                   | not evidence of correctness                    |
| Descriptor comprehension     | Comprehension                     | rubric-scored interpretation task                                                       | rubric needs independent review                |
| Candidate acceptance rate    | Behavioral relevance              | sessions selecting at least one exposed candidate / eligible sessions                   | exposure-dependent; not professional agreement |
| None-of-these rate           | Behavioral relevance / abstention | eligible sessions selecting no match / eligible sessions                                | a valid outcome, not always failure            |
| Context-prior override rate  | Product semantics                 | sessions where explicit answers reverse context-supported ordering / evaluable sessions | requires logged candidate state                |
| Post-result confidence       | User research                     | participant confidence on a prespecified scale                                          | not a sensory probability                      |
| Perceived usefulness         | User research                     | instrument response to usefulness item(s)                                               | report item wording and scale                  |
| Comparison usefulness        | User research                     | ability/helpfulness when comparing cups or package notes                                | separate subjective and task evidence          |
| Vocabulary-learning outcome  | Comprehension                     | pre/post change on a defined descriptor task                                            | practice and suggestion effects possible       |
| Short-term descriptor recall | Comprehension                     | correctly recalled/used terms after specified delay                                     | delay and scoring must be prespecified         |
| Qualitative trust concerns   | Qualitative research              | traceable coded concerns with contradictions                                            | counts do not imply population prevalence      |

## Model-evaluation measures

Model metrics such as macro-F1, Recall@5, nDCG, MRR, entropy reduction, and
abstention precision belong to an eligible held-out model evaluation. They must
not be computed from planned sessions or substituted for user usefulness.

## Sensory agreement

Agreement between a participant, package note, professional record, or model is
meaningful only when the comparison target and provenance are defined. Package
agreement is not ground-truth accuracy. Participant agreement can measure
communication or relevance without becoming expert adjudication.

## Reporting minimum

Every result must include metric version, population, inclusion/exclusion,
denominator, missingness, collection mode, uncertainty interval where suitable,
and research-state label. Small qualitative samples should emphasize evidence
and contradictions rather than prevalence estimates.
