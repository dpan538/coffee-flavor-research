# Question-target review

All 18 current targets receive exactly one disposition in
`db/data/round3g/question_target_reviews.tsv` and
`calibration.question_target_review_decision`.

| Disposition                 | Count |
| --------------------------- | ----: |
| `RETAIN_HYPOTHESIS`         |    12 |
| `RESEARCH_SUPPORT_ADDED`    |     2 |
| `BILINGUAL_REVIEW_REQUIRED` |     4 |
| `REJECT_TARGET`             |     0 |
| `RETURN_TO_UNRESOLVED`      |     0 |

The roast-direction and roast-smoke targets gain research context because a
coffee RATA study contains separate Smoky Aroma and Roasty Flavor variables.
This is not wording validation. Four targets involving floral/jasmine,
tea-like/茶感, and bright/明亮 retain an explicit bilingual-review requirement.

Every target remains `HYPOTHESIZED`, `NOT_USER_VALIDATED` and
`NOT_ESTIMABLE`. No question becomes comprehension-ready or active for
calibration, and no information gain is estimated.
