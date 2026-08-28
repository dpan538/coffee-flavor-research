# Evaluation and split plan

## Status

`EVALUATION_STATUS=PLANNED`

No model metrics are reported because no model has been run. This plan defines
the grouping and measures required before a future experiment.

## Leakage groups

The split manifest must group or exclude leakage across:

- canonical/effective coffee identity;
- entry or lot identity;
- competition or source family;
- edition year;
- publication mirror and alternate result view;
- repeated preparation service;
- reviewer and review batch;
- normalized phrase/template family;
- participant/user identity and session where applicable; and
- protocol, question-bank, candidate-set, and model version.

Primary reporting should include source-family holdouts. A random row split is
insufficient because it can place the same coffee, phrase, publication, reviewer,
or participant on both sides.

## Normalization metrics

- macro-F1 and micro-F1;
- top-k recall;
- abstention precision and coverage;
- tail-label performance;
- multi-target exact/partial agreement; and
- worst held-out-family slice.

## Candidate-ranking metrics

- Recall@5 and Recall@8;
- nDCG@5 and nDCG@8;
- mean reciprocal rank;
- worst held-out-family nDCG;
- candidate coverage and abstention rate;
- calibration where a probability interpretation is explicitly defined; and
- ranking stability across context/user/source slices.

## Question-selection and stopping metrics

- average/median questions;
- candidate-set entropy reduction;
- ranking gain per question;
- exceptional Q5 activation;
- completion time and drop-off;
- stop/continue utility under prespecified burden cost; and
- abstention quality.

## User-research measures

- task success and completion burden;
- descriptor comprehension and recall;
- post-result confidence;
- perceived/comparison usefulness; and
- qualitative trust and suggestion-bias concerns.

User usefulness is not interchangeable with professional-label agreement or
ranking performance.

## Evaluation protocol

1. Freeze eligible data manifest, rights snapshot, task contract, candidate
   universe, and split groups.
2. Audit duplicates and group leakage before feature construction.
3. Fit/tune only within the training/development groups.
4. Keep a held-out source-family set untouched until the final comparison.
5. Compare against unresolved-only, lexical, popularity, context-only, and best
   prior baselines as applicable.
6. Report missingness, abstention, tail labels, family/language/context slices,
   and negative results.
7. Do not promote a model or refresh a public claim without a versioned model
   receipt and rights decision.

## Stopping rule

If data gates, model rights, split independence, or label provenance fail, the
experiment status is `BLOCKED`; the remedy is not to relax the split or relabel
publication rows.
