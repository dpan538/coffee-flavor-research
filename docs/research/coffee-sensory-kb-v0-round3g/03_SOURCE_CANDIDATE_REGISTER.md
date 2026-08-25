# Source candidate register

The authoritative machine register is
`db/data/round3g/source_candidate_register.tsv`.

| Candidate               | Named source                                                                                                                      | Decision               | Stop reason                                                                                      |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------ |
| Mendeley Liberica       | [Liberica Coffee Sensory, v1](https://doi.org/10.17632/m3n2gc4dv6.1)                                                              | `ADMIT_AGGREGATE_ONLY` | CC BY 4.0; raw workbook has panelist initials, so only aggregate rows are exported               |
| Wiktionary revision set | [English Wiktionary](https://en.wiktionary.org/) and [Chinese Wiktionary](https://zh.wiktionary.org/)                             | `ADMIT_METADATA_ONLY`  | CC BY-SA 4.0/GFDL; exact revision/title metadata only                                            |
| Mendeley mozambioside   | [Contribution of mozambioside roasting products to coffee's bitter taste, v1](https://doi.org/10.17632/xzjppbmn58.1)              | `REJECT_OUT_OF_SCOPE`  | repository sensory folders are receptor/NMR experiment files, not range-association observations |
| Zenodo electrochemical  | [Electrochemical profiles of coffee drink samples](https://doi.org/10.5281/zenodo.20840464)                                       | `REJECT_RIGHTS`        | CC BY-NC 4.0 is incompatible with the public baseline                                            |
| WCR Lexicon 2.0         | [World Coffee Research Sensory Lexicon](https://worldcoffeeresearch.org/read-more/news/174-world-coffee-research-sensory-lexicon) | `REJECT_RIGHTS`        | official page permits personal-use copies, not dataset republication                             |
| CC-CEDICT               | [MDBG CC-CEDICT release page](https://www.mdbg.net/chinese/dictionary?lang=en&page=cc-cedict)                                     | `REJECT_ACCESS_TERMS`  | page states automated or scripted access is prohibited                                           |

Generic queries are not counted. Each row records its targeted gap, access and
rights result, decision, next action and stop status.
