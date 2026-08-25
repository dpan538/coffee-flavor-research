# Data-expansion expected-state result

| Layer                  | Baseline / expectation                  | Observed     | Delta / result         |
| ---------------------- | --------------------------------------- | ------------ | ---------------------- |
| ontology               | 130 concepts; 92 active sensory         | 130; 92      | 0; 0                   |
| ranges                 | 7 ranges; 18 memberships; 8 overlapping | 7; 18; 8     | 0; 0; 0                |
| supported ranges       | 0 local; 0 cross                        | 0; 0         | 0; 0                   |
| question targets       | 18; 0 user validated; 0 IG              | 18; 0; 0     | 0; 0; 0                |
| text-first candidates  | 107 total; 107 outside                  | 107; 107     | 0; 0                   |
| named candidates       | minimum 4                               | 6            | minimum passes         |
| independent families   | minimum 1; preferred 2                  | 2            | minimum/preferred pass |
| source types           | preferred coffee plus lexical/bilingual | 1 plus 1     | preferred passes       |
| snapshots / files      | minimum 1 snapshot; all hashes          | 3 / 4        | minimum/hard pass      |
| evidence               | more than 0; provenance 1.0000          | 20; 1.0000   | minimum/hard pass      |
| reviews                | 7 / 18 / 18 complete                    | 7 / 18 / 18  | minimum pass           |
| source-local promotion | soft target only                        | 1 membership | preferred passes       |

No metric failed. `EXPECTED_STATE_HARD_GATE_PASS=true`,
`MINIMUM_EXPECTED_STATE_PASS=true`, `PREFERRED_EXPECTED_STATE_PASS=true`, and
`EXPECTED_STATE_RESULT=PASS`.

PASS permits round closure; it does not permit claims that ranges are
scientifically validated, bilingual equivalence exists, questions are
user-validated, information gain is known, or a model has learned from these
sources.
