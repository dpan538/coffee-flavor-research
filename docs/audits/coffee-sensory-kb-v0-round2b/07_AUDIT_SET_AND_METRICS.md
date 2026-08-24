# Round 2B audit set and metrics

Date: 2026-08-24

Audit set: `audit_set.round2b.firstbloom_pilot_v1`

Status: frozen held-out evaluation complete

## Audit-set construction

The source-controlled selector created 300 actual, unique normalized English
expressions from the frozen pilot: 75 development cases and 225 held-out cases.
It used no synthetic padding. The declared strata cover exact
lexicalizations, approved or orthographic variants, orthographic difficulty,
graph/reference cases, qualifier or polysemy cases, non-descriptive language,
hard negatives, and genuinely unresolved cases. Every held-out row records
`tuning_eligible=false`.

The private case TSV has SHA-256
`0401ae2c3759044d4b9f5ab16ea1f374e27399080fc14717e27f79d0d96f1609`.
The frozen 348-concept candidate pool has SHA-256
`00b087cabd36d1b50a258624e79e14ea10b3c135969143ca56c967e29c95cd45`.
Public repository artifacts replace expression text and rationales with stable
hashes while preserving selection, review, candidate, and metric receipts.

## Review policy and independence

Two reviewers independently graded all 300 cases, including every pooled
candidate and reviewer-added concepts where necessary. A third distinct pass
adjudicated the union. The candidate model was frozen before review at commit
`a6abb4112cff3fc436b1613c37f9b40f51e65144`, timestamp
`2026-08-24T07:48:49Z`. Neither reviewer inspected the other's ledger before
submitting it, and no retrieval rule was tuned after the held-out review.

All three passes were Codex-assisted project curation. They were not human
reviewers, sensory-panel members, or claims about what a coffee objectively
tastes like. This same-model-family limitation remains material even though
the ledgers were operationally independent.

| Review receipt                            |               Frozen value |
| ----------------------------------------- | -------------------------: |
| Reviewer 1 rows                           |                        628 |
| Reviewer 2 rows                           |                        614 |
| Adjudicated rows                          |                        665 |
| Adjudicated concept judgments             |                        646 |
| Adjudicated resolvable cases              |                        281 |
| Adjudicated unresolved cases              |                         19 |
| Reviewer case-level exact agreement       | 196/300 (`0.653333333333`) |
| Pooled-candidate raw grade agreement      | 322/348 (`0.925287356322`) |
| Pooled-candidate quadratic weighted kappa |           `0.936797988265` |
| Unresolved-status disagreements           |                         14 |

The weighted kappa covers only the 348 pooled concepts that both reviewers
graded 0–3. It excludes reviewer-added concepts and `U` case rows. The
case-level exact agreement is therefore reported alongside it rather than
allowing the high pooled-candidate statistic to hide broader disagreement.

The adjudication ledger SHA-256 is
`7e9b4ce21697ffd614cc11e89632394411d1bf1813bc331f0cc66a1b506ef6e8`.
Its grade distribution is 16 grade-0, 155 grade-1, 398 grade-2, 77 grade-3,
and 19 `U` rows.

## Relevance rubric

| Grade | Evaluation meaning                                          |
| ----- | ----------------------------------------------------------- |
| 3     | Same canonical concept or valid lexicalization.             |
| 2     | Defensible broader/narrower or composite-reference mapping. |
| 1     | Useful but indirect semantic or sensory neighbor.           |
| 0     | Misleading or unrelated.                                    |
| U     | The expression should remain genuinely unresolved.          |

Grades are ordinal retrieval relevance. They are neither probabilities nor
sensory values. Adjudicated qrels may reference an existing governed concept
that is not active, including a candidate qualifier or candidate sensory
attribute, when that reference documents information loss. The deterministic
model can emit active concepts only. This deliberate asymmetry can lower recall
but cannot activate, promote, or retroactively insert the qrel concept into a
frozen model output.

## Metric semantics

- Recall@K is macro recall of all adjudicated grade-2-or-3 concepts per
  resolvable case.
- MRR uses the rank of the first grade-2-or-3 result.
- nDCG@5 uses declared gains 0, 1, 3, and 7 for grades 0–3.
- Coverage is the fraction of all cases returning at least one candidate.
- Abstention rate is the fraction returning no candidate.
- Abstention error is the fraction of abstentions that were adjudicated
  resolvable; it is conditional on abstaining.
- Unsafe non-abstention is the fraction of genuinely unresolved cases for
  which the baseline returned a candidate.
- Median candidate-set size includes zero for an abstention.

Recall, MRR, and nDCG exclude `U` cases because they have no relevant concept
or defined ideal ranking. Coverage and abstention include them. This difference
in denominators is intentional and must be retained when interpreting the
results.

## Held-out Baseline D metrics

The headline evaluation contains 225 held-out cases: 209 resolvable and 16
adjudicated `U`.

| Metric                    |     Exact database value |
| ------------------------- | -----------------------: |
| Recall@1                  | `0.27910685805422647528` |
| Recall@3                  | `0.43620414673046251994` |
| Recall@5                  | `0.44098883572567783094` |
| MRR                       | `0.48803827751196172249` |
| nDCG@5                    | `0.45481865642031275923` |
| Coverage                  | `0.49333333333333333333` |
| Abstention rate           | `0.50666666666666666667` |
| Abstention error          | `0.86842105263157894737` |
| Unsafe non-abstention     |                 `0.0625` |
| Median candidate-set size |                      `0` |

The complete A–D comparison is in
[the retrieval-baseline audit](06_RETRIEVAL_BASELINES.md). Baseline D improves
deeper ranked retrieval but still abstains on 114 of 225 held-out cases, and 99
of those abstentions are false abstentions under the adjudicated rubric. One of
16 genuinely unresolved cases receives a candidate. The system therefore
preserves `UNRESOLVED` while exposing both coverage and unsafe non-abstention;
it does not optimize headline coverage by forcing every expression to a
concept.

These measurements evaluate deterministic language normalization and
retrieval. They must not be described as coffee flavor accuracy.

## Persistence closure

The repository stores 300 cases, eight split/baseline evaluation identities,
665 adjudicated qrel rows, 610 candidate traces, 796 candidate signals, and 80
metric values. The frozen database audit-set inventory SHA-256 is
`f23fe402b542a482532149dd41de14ef04d95c34226e5d7de13ffc4cd036208b`.
The evaluation seed SQL SHA-256 is
`2300911368607debafab935f6141d05a4521c68457da98ef7edb2956ab9bbe1d`.
The public evaluation manifest SHA-256 is
`d6876c621c95c53aecd9f07358dac20beafb6f8d789186a36f4aa6d169b1aabf`;
the [manifest itself](../../../db/data/round2b/evaluation/round2b_evaluation_manifest.json)
binds the phrase-free public artifacts to the private input hashes.
