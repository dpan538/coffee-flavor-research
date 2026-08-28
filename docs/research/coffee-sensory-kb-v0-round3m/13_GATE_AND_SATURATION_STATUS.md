# Gate and saturation status

All active descriptor gates fail. The human-reviewed P1/P2 strict universe is
empty, model-research rights are not affirmative, and missing denominators are
represented as `NA` rather than zero or pass.

The last generated version-one metric surface is in
`db/data/round3m/DESCRIPTOR_GATE_STATUS.tsv`. Historical record-first gates are
deprecated for current readiness and cannot authorize a training run. Draft
059 gate changes are not yet represented by a contiguous migration plan or
final regenerated artifact.

That version-one surface contains 7 gates and 56 criteria. Passing criteria are 0. Seventeen missing-denominator criteria are marked not applicable, and all 17
still have `pass=false`. Reviewed P1/P2 strict assertions, reviewed
descriptor-bearing records, reviewed normalized forms, human-confirmed review,
expert adjudication, and model eligibility are all zero.

In that artifact, field-level blocker flags occur on 38 criteria for data, 13 for review, and
6 for rights. These flags are non-exclusive; a criterion may expose more than
one blocker.

Final gate, criterion, NA, and blocker counts remain unclaimed until the draft
059 contract, missing-058 decision, artifact regeneration, and full CI are
resolved.

Round 3M implements future saturation measurement fields for lexical yield,
canonical mapping, co-assertion edges, weighted-Jaccard stability, duplicate
rate, held-out-source normalization, held-out-family NDCG@8, worst-family
delta, and under-covered domains.

```text
SATURATION_EVALUATED=false
SATURATION_PASS=false
```

There are not three successive reviewed increments or authorized evaluation
models. No saturation claim is made.
