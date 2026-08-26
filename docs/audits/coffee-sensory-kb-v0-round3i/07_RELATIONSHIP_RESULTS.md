# Relationship results

Round 3I adds one reviewed claim:
`claim.round3i.cotter.acidity-citrus.correlation`. It targets
`membership.acidity-character.citrus`, has direction `SUPPORTS`, and records
the decision
`CORRELATIONAL_SUPPORT_RETAIN_SOURCE_LOCAL_MEMBERSHIP_LIFECYCLE`.

The source is Cotter, Ristenpart, and Guinard, _Consumer preference data for
black coffee_, Dryad dataset version 4, CC0-1.0. The frozen raw input has 3,186
rows and SHA-256
`931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114`.
The public derivative has 27 brew-condition aggregates and SHA-256
`adf26fd10be549b4f4bf74f2e5a45121f85405d1231e874f7cb9a2aecbb3118c`.

| Source-local statistic         |                   Value |
| ------------------------------ | ----------------------: |
| Citrus-selected rows           |                     577 |
| Citrus-not-selected rows       |                   2,609 |
| Mean Acidity JAR, selected     |       3.287694974003466 |
| Mean Acidity JAR, not selected |       3.109620544269835 |
| Brew-condition Pearson `r`     |      0.7435702458531227 |
| Pearson two-sided `p`          | 0.000008814419733073104 |
| Brew-condition Spearman `rho`  |       0.673733353098996 |
| Spearman two-sided `p`         |  0.00011700493631573394 |

These are correlational, source-local results for one washed, medium-roast
Honduras coffee under batch-filter conditions. CATA Citrus and 1--5 JAR
Acidity are distinct constructs and are not pooled or declared synonymous.

| Relationship metric                | Before | Delta | After |
| ---------------------------------- | -----: | ----: | ----: |
| Reviewed claims                    |     96 |    +1 |    97 |
| `SUPPORTS`                         |     47 |    +1 |    48 |
| `CHALLENGES`                       |     18 |     0 |    18 |
| `MIXED`                            |     14 |     0 |    14 |
| `INSUFFICIENT`                     |     17 |     0 |    17 |
| Source-local-supported memberships |      6 |     0 |     6 |
| Cross-source-supported memberships |      4 |     0 |     4 |
| Ranges with source-local evidence  |      6 |     0 |     6 |
| Ranges with cross-source evidence  |      3 |    +1 |     4 |

The existing membership stays `SOURCE_LOCAL_SUPPORTED`; the
acidity-character range and all seven association ranges stay `CANDIDATE`.
The fourth-range result is an evidence-breadth summary, not a lifecycle
promotion. Challenging, mixed, and insufficient evidence remains preserved in
the underlying registry.
