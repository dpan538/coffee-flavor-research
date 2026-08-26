# Round 3I relationship-evidence delta

Round 3I adds one reviewed `SUPPORTS` claim from the Dryad Cotter consumer dataset. The evidence is a source-local correlation between brew-condition Citrus selection rate and mean Acidity JAR response. It improves independent-origin breadth for the acidity-character range but does not change any membership or range lifecycle.

## Frozen claim

| Field                   | Value                                                                                                                                         |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Claim key               | `claim.round3i.cotter.acidity-citrus.correlation`                                                                                             |
| Target membership       | `membership.acidity-character.citrus`                                                                                                         |
| Direction               | `SUPPORTS`                                                                                                                                    |
| Promotion decision      | `CORRELATIONAL_SUPPORT_RETAIN_SOURCE_LOCAL_MEMBERSHIP_LIFECYCLE`                                                                              |
| Range lifecycle changed | `false`                                                                                                                                       |
| Source                  | Andrew Cotter, William D. Ristenpart, and Jean-Xavier Guinard, [`Consumer preference data for black coffee`](https://doi.org/10.25338/B8993H) |
| Version                 | Dryad version 4 files published 2023-01-16                                                                                                    |
| License                 | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)                                                                                 |
| Frozen input            | 3,186 rows, 542,026 bytes, SHA-256 `931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114`                                         |

The relationship artifact's `family.legacy-cotter-consumers` and `dryad.cotter-black-coffee.relationship.v4` keys are role-specific aliases of the same canonical Dryad origin used by the language batch. They do not constitute another independent source family.

## Source-local calculation

The 3,186 repeated consumer rows comprise 27 controlled brew conditions with 118 rows per condition. `Citrus` is a binary CATA selection. `Acidity` is a 1–5 just-about-right adequacy response, not a pure intensity scale.

| Statistic                      |            Frozen value |
| ------------------------------ | ----------------------: |
| Citrus-selected rows           |                     577 |
| Citrus-not-selected rows       |                   2,609 |
| Mean Acidity JAR, selected     |       3.287694974003466 |
| Mean Acidity JAR, not selected |       3.109620544269835 |
| Row-level mean difference      |     0.17807442973363097 |
| Brew-condition Pearson `r`     |      0.7435702458531227 |
| Pearson two-sided `p`          | 0.000008814419733073104 |
| Brew-condition Spearman `rho`  |       0.673733353098996 |
| Spearman two-sided `p`         |  0.00011700493631573394 |

The claim rests on the brew-level association, with the row-level means retained as descriptive context. Repeated consumer rows are not treated as 3,186 independent brew conditions.

## Conservative interpretation

The association supports retaining a source-local relationship between acidity character and citrus language under the tested conditions. It does not show that `Citrus` and `Acidity` are synonyms, that citrus causes acidity, that a CATA selection and JAR response share a scale, or that the measured relationship generalizes to other coffees.

The experiment used one washed, medium-roast Honduras coffee and one batch-filter preparation family. Consumer response, brew recipe, and the distinction between CATA and JAR constructs remain material limitations. The terms stay distinct, their values are not pooled, and no universal coefficient enters the atlas.

The pre-existing membership was already `SOURCE_LOCAL_SUPPORTED`. Adding a different canonical origin alongside previously governed evidence raises the preferred count of ranges with cross-source evidence from three to four. That breadth result is an evidence-coverage decision, not a lifecycle promotion: the membership stays `SOURCE_LOCAL_SUPPORTED`, the acidity-character range stays `CANDIDATE`, and `range_lifecycle_changed=false`.

## Evidence-count delta

| Status         | Before | Delta | After |
| -------------- | -----: | ----: | ----: |
| `SUPPORTS`     |     47 |    +1 |    48 |
| `CHALLENGES`   |     18 |     0 |    18 |
| `MIXED`        |     14 |     0 |    14 |
| `INSUFFICIENT` |     17 |     0 |    17 |
| Total          |     96 |    +1 |    97 |

This claim adds zero language documents, expressions, occurrences, sensory outcome rows, sample identities, participants, or empirical coverage cells.

## Rights, privacy, and receipts

The source annotation records `ALLOW` for `raw_text_internal_use`, `raw_text_public_redistribution`, `derived_expression_internal_use`, `derived_expression_public_release`, `derived_counts_internal_use`, `derived_counts_public_release`, and `model_research_use`. CC0 permits the derived aggregate and count release; scholarly citation is retained.

Source identifiers were removed under IRB 1082568. Pseudonymous `Judge` codes remain internal and reidentification is prohibited. The published relationship surface contains condition aggregates and claim metadata, not evaluator rows or identities.

| Artifact                                    | Role                                                          | SHA-256                                                            |
| ------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| `cotter_brew_acidity_citrus_aggregates.tsv` | 27 brew-condition aggregates                                  | `adf26fd10be549b4f4bf74f2e5a45121f85405d1231e874f7cb9a2aecbb3118c` |
| `relationship_evidence_claims.tsv`          | one reviewed claim                                            | `9ef0aa5d19db683877a469ec229cfa156ddafd56e70c6346be2e438bab0577b0` |
| `source_annotation.json`                    | exact source, rights, privacy, file, and row-count annotation | `51ba8482867c64f05769d364c9f6e54f3ffb585849075b91809c408f97590190` |
| `batch_result.json`                         | batch assertions and decision                                 | `1fe5de836a60e466ef45e07628b06fa6207c2fa4f99d18761d06c01aad08c932` |

No model, embedding, classifier, ontology merge, user-validation assertion, or frontend change follows from this evidence delta.
