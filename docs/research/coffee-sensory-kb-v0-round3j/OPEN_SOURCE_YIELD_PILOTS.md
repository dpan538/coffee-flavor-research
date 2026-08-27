# Open-source yield pilots

Round 3J used bounded, source-specific pilots. A large downloadable file was
never treated as proof of flavor-description yield. The machine-readable
results are in `db/data/round3j/global-corpus/OPEN_SOURCE_YIELD_PILOT.tsv`.

| Source                         | Stage             | Result                                                                                          |                                     Admitted yield |
| ------------------------------ | ----------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------: |
| Open Food Facts                | Stage 2 attempted | `BLOCKED_ACCESS` after three official API requests returned HTTP 503                            |                                                  0 |
| FoodRepo v3                    | Stage 1 complete  | `BLOCKED_ACCESS`; filtered access requires a token and the legacy full dump was not substituted |                                                  0 |
| `guchengf` 2025 author archive | Stage 3 complete  | `ADMIT_RAW_AND_DERIVED`                                                                         |                        4 documents, 22 expressions |
| MFACT 2017 article             | Stage 3 complete  | `ADMIT_DERIVED_ONLY`                                                                            | 1 document, 3 flavor expressions, 4 configurations |
| Bressani 2021 article          | Stage 3 complete  | `ADMIT_DERIVED_ONLY`                                                                            |           1 document, 12 expressions, 2 conditions |

Open Food Facts remains governed by ODbL/DbCL and its share-alike and
attribution boundary. FoodRepo images remain excluded. The Great American
Coffee Taste Test did not advance beyond rights/privacy triage: the accessible
mirror has 4,042 rows and four free-text note fields, but a mirror declaration
does not establish rights to the original participant text. FlavorReasonBench
is retained as evaluation-only and contributes zero observed documents.

The two article pilots retain only source-authored aggregate sensory terms.
Participant records, direct identifiers, demographics, questionnaires,
supplementary assessment forms, proprietary scale definitions, and preference
variables are excluded from the flavor-expression corpus.
