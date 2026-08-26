# Round 3I contemporary tasting-language delta

Round 3I closes the hard contemporary-language gates with three independently originated, rights-cleared evaluation families. It also adds a conservatively dual-reviewed long tail from the already-governed Firstbloom family. These are language-document surfaces; they do not create new controlled sensory experiments or empirical coverage cells.

## Count decisions

| Batch                                        | New contemporary families | Countable contemporary documents | Other materialized language documents | Globally incremental normalized expressions | Occurrences |
| -------------------------------------------- | ------------------------: | -------------------------------: | ------------------------------------: | ------------------------------------------: | ----------: |
| Cotter, Bollen, and Vezzulli evaluation rows |                         3 |                            3,289 |                                     0 |                                          18 |      11,444 |
| Firstbloom pinned long tail                  |                         0 |                                0 |                                   840 |                                         952 |       1,058 |
| English-language subtotal                    |                         3 |                            3,289 |                                   840 |                                         970 |      12,502 |

The evaluation artifact contains 37 batch-deduplicated expression rows. The corrected generator reconciles against the complete 1,777-expression migrated baseline: 14 rows overlap the 1,713-entry Round 2B pilot file and five more overlap canonical lexical identities (`astringent`, `bitter`, `burnt`, `rubber`, and `sour`). The governed-global evaluation gain is therefore 18.

The Firstbloom artifact contains 953 independently agreed expression rows. `musty` already exists in the canonical lexical baseline, so its governed-global gain is 952. Starting from 1,777, the two English-language batches produce an intermediate inventory of 2,747. The separately governed Simplified-Chinese batch adds 249 more for the final Round 3I total of 2,996.

| Gate                                                   | Hard target |                                Round 3I result | Decision    |
| ------------------------------------------------------ | ----------: | ---------------------------------------------: | ----------- |
| New independent contemporary tasting-language families |           3 |                                              3 | PASS        |
| New countable contemporary tasting-language documents  |         500 |                                          3,289 | PASS        |
| Unique normalized observed expressions                 | 2,500 total | 2,996 total after the Simplified-Chinese batch | PASS        |
| Preferred contemporary-family depth                    |           5 |                                              3 | MISS by 2   |
| Preferred contemporary-document depth                  |       1,500 |                                          3,289 | PASS        |
| Preferred expression depth                             | 3,500 total |                                    2,996 total | MISS by 504 |

## Evaluation-document surface

The 3,289 countable documents preserve one source row or one published trained-panel profile per record:

- Cotter: 3,186 consumer evaluation rows, 17 binary CATA attributes, and 10,763 positive occurrences.
- Bollen: 95 genotype-harvest profiles, eight interpretable descriptor classes, and 530 positive occurrences.
- Vezzulli: eight species-by-extraction profiles, 19 flavor, aroma, taste, and texture descriptors, and 151 positive occurrences.

These are newly surfaced families in the governed contemporary-language plane, not new canonical sensory-study origins. In particular, language key `family.baseline.cotter-consumers` and the existing sensory or relationship key `family.legacy-cotter-consumers` both identify the same Dryad version 4 origin and count once for independence.

Document content is privacy-preserving and structured. Cotter evaluator-linkage fields are omitted. Bollen uses the sanitized governed TSV. Vezzulli emits published medians only. Article prose, chemistry, color, proprietary or third-party form definitions, and absent or non-positive cells are not language occurrences. CATA flags, rating values, descriptor frequencies, and medians retain their original source-local meanings; the project does not pool or calibrate their scales.

The evaluation generator verified exact inputs before emitting deterministic output. Its main receipts are:

| Artifact                                         | Rows or role                         | SHA-256                                                            |
| ------------------------------------------------ | ------------------------------------ | ------------------------------------------------------------------ |
| `evaluation/language_documents.tsv`              | 3,289 documents                      | `e2732974ee76eed920a5ae517bd301b77374d5fb623521ecb525e2c0bf53c359` |
| `evaluation/language_expressions.tsv`            | 37 deduplicated expressions          | `4bd7b824ee461ca6043c5546e8f3a242a0983bbbc38d3c01b6fbb5d83e51a174` |
| `evaluation/language_expression_occurrences.tsv` | 11,444 occurrences                   | `ac6a3cfbc3af911913e7a2f3d8567ba6c64d24a7e6431620887aabeea9a5d173` |
| `evaluation/language_source_families.tsv`        | three families                       | `1270a65dd628c25a4f38342cc3d573f7a1ce9402cd9de1c594c6246469104869` |
| `evaluation/language_sources.tsv`                | seven-dimensional rights annotations | `1bcd0f6c6cf7aeacbc4028734df02943cd6e444037db24e72723106575497731` |

## Firstbloom long-tail review

The pinned `product_releases.csv` produced 1,020 text-free candidate identities. Two independent Codex review passes used only candidate key plus the standalone observed phrase; `human_review=false` and `automatic_language_detection=false`. Pass A admitted 958, rejected 55 as non-sensory, and rejected seven as uncertain. Pass B admitted 986, rejected 29 as non-sensory, and rejected five as uncertain. The passes disagreed on 42 identities; the conservative intersection excluded every disagreement and admitted the 953 identities for which both passes returned `ADMIT_SENSORY_LANGUAGE`. The materializer then emitted 840 source-row documents and 1,058 expression occurrences.

The source family remains `family.baseline.firstbloom-industry`. It is a historical secondary aggregation already present in the baseline, so the committed artifact sets `counts_as_new_contemporary_document=false`. The 840 documents are valid governed corpus records but do not inflate either the new-family or contemporary-document gate. All 953 agreed expressions remain attributable language-artifact rows; global uniqueness counting excludes the one pre-existing `musty` identity.

| Artifact                                     | Rows or role               | SHA-256                                                            |
| -------------------------------------------- | -------------------------- | ------------------------------------------------------------------ |
| `firstbloom_review_candidates_text_free.tsv` | 1,020 candidate identities | `28bd9dbf1edf9a7234c1eb63d2ece6f3a2fab8ea947f254d3eab4c167342d604` |
| `firstbloom_review_consensus.tsv`            | 1,020 rows; 953 admitted   | `e035383fb42c23ab150426bbe9a5d2aa9f5d186d9295f7e3a07b588e1d60b996` |
| `firstbloom_review_decisions.tsv`            | 2,040 decisions            | `320d613125a731b3433f969bdb4490dfe652a7a62c972821f13198a8cf18364c` |
| `firstbloom/language_documents.tsv`          | 840 documents              | `13d1a270ddfe523c48eb95b76cebcac004e76735a9c8ce6209f15d48380b9ab5` |
| `firstbloom/language_expressions.tsv`        | 953 expressions            | `322b1a21567f9e3c0ed219bd02627da25271f1e18439bf9b7f95c823c55fdb4b` |
| `firstbloom/language_occurrences.tsv`        | 1,058 occurrences          | `8095dd024e2df55a266955d2c29612886e45c4e2f697d77fc7225550330254a8` |

The retained phrases are observations of industry tasting language, not objective flavor truths. Complete descriptions, narrative fragments, product or producer metadata, reviews, disagreements, non-sensory strings, and uncertain candidates remain out of scope.

## Rights, privacy, and modeling boundary

Each of the four source annotations records `ALLOW` for raw internal use, raw public redistribution, derived-expression internal use, derived-expression public release, derived-count internal use, derived-count public release, and model-research use. The project nevertheless applies a narrower public policy: evaluation and Firstbloom documents are `PUBLIC_DERIVED_ONLY` and set raw-document export to false.

No machine translation, proprietary definition, generated wording, article prose, model feature, embedding, training set, or ontology node is created here. Admission changes the governed language plane only.
