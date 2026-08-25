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

`PENDING_PRE_ACQUISITION`

Observed values must be generated from the final database and source manifest.
No observed value exists at this freeze checkpoint.

## DELTA

`PENDING_PRE_ACQUISITION`

Delta values must be computed as observed minus baseline or evaluated against
the declared predicate. Thresholds may not be changed after acquisition merely
because a result is difficult to reach.

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
