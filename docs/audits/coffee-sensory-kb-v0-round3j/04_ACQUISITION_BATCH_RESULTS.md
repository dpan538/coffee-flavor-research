# Round 3J acquisition-batch results

The execution batches below are distinct from the A--F gap codes in the source
candidate register. A candidate may target several gap codes, while each
execution batch is one bounded acquisition decision used for the Round 3J stop
rule. The machine-readable authority is
`db/data/round3j/acquisition_batch_ledger.tsv`.

## Batch ledger

| Sequence | Execution batch | Scope                                                                                               | Raw payload result                                                                                                                                                     | Material gain                                                                                                                                                                              | Consecutive no-gain count | Stop state                         |
| -------: | --------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------: | ---------------------------------- |
|        1 | `R3J-AQ-001`    | Five preregistered candidates authorized for versioned file/schema audit                            | 584 payload files; 97,938,951 source-payload bytes; 172 separate API-receipt bytes; known heterogeneous raw-observation lower bound 934; zero admitted/effective units | Yes: bounded `guchengf` snapshot established one new independent family feasibility, four source-authored zh-Hans candidate documents, and 22 unique source-reviewed candidate expressions |                         0 | Continue after gain                |
|        2 | `R3J-AQ-002`    | Carvalho, Münchow, Juravle, and Birke Rune sensory/context metadata closure                         | No authorized raw payload; reported article counts excluded                                                                                                            | No: dataset rights/version, raw access, privacy, or source-local outcome missing                                                                                                           |                         1 | Continue                           |
|        3 | `R3J-AQ-003`    | Open Food Facts, Beans with Beanie, Open Coffee Hub, and Cherrybook multilingual aggregator closure | No fixed rights-cleared source snapshot                                                                                                                                | No: immutable version, content rights, upstream chain, or permitted access missing                                                                                                         |                         2 | Continue                           |
|        4 | `R3J-AQ-004`    | Duran, Slegetank, Hans, and OSF zh-Hans/long-tail closure                                           | Metadata and article evidence only                                                                                                                                     | No: model-use rights, derivative provenance, file license, or tasting-corpus role missing                                                                                                  |                         3 | `CONDITION_B_MET_STOP_ACQUISITION` |

## Stop-rule proof

`R3J-AQ-001` resets the no-gain sequence to zero because acquisition added an
independent source-family feasibility and the bounded review added 22 unique
source-reviewed candidate expressions, even though no raw HTML row or derived
candidate was imported. The next three targeted batches each added zero of
every material-gain class:

- independent source family eligible for current use;
- material unique-expression or source-authored zh-Hans coverage;
- effective sensory sample or observed context cell;
- held-out source feasibility;
- cross-source relationship evidence; or
- long-tail target coverage.

Therefore the terminal sequence is exactly `0, 1, 2, 3`, and Condition B is
met after `R3J-AQ-004`. Further open-ended acquisition is outside this round.
This stop decision does not declare a training task ready and does not permit a
corpus freeze; the task-readiness and Round 3 exit gates remain separate.

## No-inflation controls

The batch totals intentionally exclude reported-but-unavailable article rows,
catalog display totals, roaster counts, mirrors, duplicate workbook
representations, and unenumerated Bichlmaier records. The 934 raw-observation
lower bound is not an effective-sample count. The 404 Xian workbook rows remain
202 participant groups across two representations; the 526 Golovinsky rows
remain 196 sample IDs plus repeats; and the four `guchengf` pages plus 22
derived expressions remain candidate evidence. All 22 are unresolved,
non-gold, not governed, not imported, and not sampling eligible.

## Batch outcome

- `MATERIAL_GAIN_BATCH_COUNT=1`
- `POST_GAIN_CONSECUTIVE_NO_MATERIAL_GAIN_BATCH_COUNT=3`
- `STOP_RULE_CONDITION_A=false`
- `STOP_RULE_CONDITION_B=true`
- `ACQUISITION_STOP_STATE=CONDITION_B_MET_STOP_ACQUISITION`
