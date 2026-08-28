# Dataset card draft

`DATASET_STATUS=NOT_FROZEN_FOR_TRAINING`

`CURRENT_MODEL_ELIGIBLE_COUNT=0`

This draft describes current strata and the requirements for a future task
dataset. It is not a dataset release and does not widen rights.

## Intended future uses

- professional source-native descriptor normalization;
- evidence-aware candidate retrieval/ranking;
- bounded co-assertion analysis;
- held-out source-family evaluation;
- consumer-language comprehension research; and
- separately consented interaction/policy evaluation.

Each use requires its own eligible manifest.

## Current strata

| Stratum                                | Current role                                                | Review state                                         | Model-use state                       |
| -------------------------------------- | ----------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------- |
| Canonical concepts and lexicalizations | governed reference vocabulary                               | frozen/validated foundation                          | depends on source/field rights        |
| Professional acquisition census        | source discovery and acquisition scale                      | mixed/provisional                                    | not a training universe               |
| Round 3M hash-only descriptor pilot    | provenance, duplicate, assertion, pair-event infrastructure | machine provisional; no qualified human confirmation | zero eligible                         |
| P3/P4 industry and commercial language | vocabulary and comparison support                           | source-role governed                                 | source-specific                       |
| P5 consumer language                   | communication/UX research only                              | not professional review                              | rights and purpose review required    |
| First-party interview/interaction data | future behavioral and product evidence                      | no data collected                                    | separate consent required             |
| Synthetic/test fixtures                | constraint and workflow verification                        | test-only                                            | prohibited as empirical training data |

## Evidence and review tiers

P1/P2 professional evidence must have verified source role, source-native
descriptor text, bounded locator, effective-record identity, duplicate/repeat
disposition, review state, and rights state. P3/P4/P5 and unresolved observations
remain distinct. Human review credit requires qualification, admission, and
row-level decision evidence.

## Rights states

Research access, model research, deployment, raw redistribution, and derived
output rights are independent. Public availability is not permission. Pending,
unknown, or prohibited states fail closed for the applicable use.

## Current composition and gaps

- acquisition coverage spans multiple source families and editions, but
  publication scale is much larger than descriptor-bearing professional scale;
- the public-safe pilot has hash/locator provenance but source text is not
  redistributed;
- qualified reviewed professional assertions are absent;
- current model eligibility is zero;
- source-family, language, preparation, roast, multi-target, challenge, and
  rights coverage require task-specific generation before any freeze; and
- no first-party participant data exists.

## Intended limitations

This future dataset would not represent objective coffee flavor, universal
human perception, all producing regions, all languages, or all preparation
contexts. Professional judging, industry notes, consumer language, and user
choices have different biases and must not be collapsed.

## Prohibited uses

- claims that a model tastes coffee or identifies true flavor;
- inference of protected/sensitive participant attributes;
- automatic professional label promotion from consumer language;
- re-identification of reviewers or participants;
- redistribution of restricted source text; and
- training outside the rights, consent, task, and split scope of a frozen
  release.

## Release requirements

A future card must include manifest SHA, exact task, unit, included artifacts,
evidence/review/rights distributions, source-family/language/context coverage,
duplicate losses, split groups, withdrawal policy, known biases, and change log.
