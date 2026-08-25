# Round 3G data-expansion expected state

Frozen on 2026-08-25 before any Round 3G named-source search, acquisition,
download, import, relationship review, or association calculation.

Source checkpoint:
`adf615af06ae8cb9ee4d659034157e111476044f`.

Machine-readable contract: `db/data/round3g/expected_state.tsv`.

## BASELINE

| Metric                                                | Frozen value |
| ----------------------------------------------------- | -----------: |
| canonical concepts                                    |          130 |
| active sensory attributes                             |           92 |
| association ranges                                    |            7 |
| association-range memberships                         |           18 |
| overlapping membership rows                           |            8 |
| source-local-supported ranges                         |            0 |
| cross-source-supported ranges                         |            0 |
| question-range targets                                |           18 |
| text-first lexical candidates                         |          107 |
| text-first candidates outside the current range model |          107 |
| user-validated questions                              |            0 |
| real observations                                     |            0 |

Any checkout that differs from this baseline is an integrity failure, not an
invitation to rewrite the baseline.

## MINIMUM_EXPECTED

Hard integrity gates require the baseline ontology and range counts to remain
fixed, all admitted-source rights/privacy/hash rates to equal `1.0000`, all
evidence and review records to have provenance/dispositions, and all prohibited
promotion, model, embedding, validation, information-gain, and observation
counts to remain zero.

Minimum expansion gates require:

- all 7 current ranges searched or reviewed;
- all 18 current memberships reviewed;
- all 18 current question targets reviewed;
- at least 4 actual named source candidates reviewed;
- at least 1 new independent source family admitted;
- at least 1 immutable snapshot admitted; and
- more than 0 new evidence records admitted.

If acquisition is complete but these expansion gates are not met, the only
non-blocked result is `COMPLETE_WITH_EVIDENCE_GAP`.

## PREFERRED_EXPECTED

The preferred state is at least two new independent source families, preferably
including one coffee sensory or consumer family and one bilingual, lexical, or
contemporary-language family. A source-local promotion of an existing
membership or range is also preferred when the complete evidence matrix
supports it. These are soft targets, not fabrication quotas.

## OBSERVED

The post-acquisition database gate observes 130 concepts, 92 active sensory
attributes, 7 ranges, 18 memberships, 18 question targets, 6 named candidates,
2 admitted independent families, 3 admitted sources, 3 immutable snapshots, 4
verified files, and 20 evidence claims. All source-annotation, rights, privacy,
file-hash, evidence-provenance, and disposition rates are `1.0000`.

All seven ranges, all 18 memberships, and all 18 question targets have one
Round 3G review. One membership is source-local-supported; all ranges remain
candidate. Hard, minimum, and preferred gates pass.

## DELTA

Ontology, active-sensory, range, membership, overlap, question-target,
text-first-candidate, supported-range, validation, information-gain, model, and
real-observation deltas are zero. Expansion deltas are `+6` named candidates,
`+2` independent families, `+3` admitted sources, `+3` snapshots, `+4` source
file records, `+20` evidence claims, and `+1` source-local membership
promotion. The detailed machine result is in `db/data/round3g/expected_state.tsv`.

`EXPECTED_STATE_RESULT=PASS`; thresholds were not changed after acquisition.

## Frozen association thresholds

These apply only if an admitted source has compatible expression/document data:

| Control                       | Frozen rule                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| minimum expression occurrence | 3 occurrences in the source family                                                            |
| minimum document count        | 2 distinct source documents or source-defined sample records                                  |
| minimum source diversity      | 1 family for source-local evidence; 2 independent families for cross-source support           |
| long-tail handling            | below-threshold relationships receive `INSUFFICIENT_FOR_RANGE`                                |
| stability requirement         | exact configuration and support counts must reproduce; no pooling across incompatible methods |

No threshold is a claim that co-occurrence means sensory similarity. No
association values are combined into a global score.

## Revision policy

`EXPECTED_STATE_THRESHOLD_REVISION_COUNT=0`

A revision requires a separate descriptive commit made before affected results
are accepted, an explanation of why the original contract was invalid rather
than inconvenient, and an explicit epistemic-impact statement.
