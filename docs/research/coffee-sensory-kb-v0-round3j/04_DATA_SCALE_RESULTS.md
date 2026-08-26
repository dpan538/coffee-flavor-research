# Round 3J data-scale results

This document reports the acquisition-audit checkpoint, not a training-corpus
freeze. The authoritative row-level evidence is
`db/data/round3j/acquisition_outcome_ledger.tsv`; execution-batch and stop-rule
evidence is in `db/data/round3j/acquisition_batch_ledger.tsv`. Raw observations,
admitted rows, effective units, and material acquisition gain are deliberately
separate measures.

## Acquisition-scale result

| Measure | Result | Counting boundary |
| --- | ---: | --- |
| Registered named candidates | 17 | Canonical candidates after mirror and frozen-baseline reconciliation |
| Candidates authorized for file audit | 5 | Authorization did not imply admission or model use |
| Audited payload files | 584 | 2 Zenodo files, 571 Bichlmaier archive members, 5 `guchengf` HTML files, and 6 Xian Zhang archive members |
| Audited source-payload bytes | 97,938,951 | Compressed archive bytes for the two Mendeley deposits plus directly audited Zenodo and HTML bytes; not decompressed corpus size and excludes the 172-byte Liang API receipt |
| Metadata/API receipt bytes | 172 | Liang access-failure response; explicitly not a source payload or raw acquisition |
| Known raw-observation lower bound | 934 | 526 Golovinsky spreadsheet rows, 404 overlapping Xian workbook rows, and 4 `guchengf` review documents; Bichlmaier rows were not enumerated |
| Source-authored candidate documents acquired | 4 | `guchengf` review pages; the fifth HTML file is the license locator |
| Source-reviewed unique zh-Hans candidate expressions | 22 | Exact source-authored substrings after the bounded text review; all remain unresolved, non-gold, not governed, not imported, and not sampling eligible |
| New independent source-family feasibility | 1 | `guchengf`; this is an acquisition gain, not a canonical ontology or frozen-corpus count |
| Acquisition-stage admitted rows | 0 | No raw source was imported by this audit |
| Acquisition-stage effective training units | 0 | No raw occurrence was promoted to an eligible training example |
| Consecutive targeted no-gain batches after the gain batch | 3 | `R3J-AQ-002` through `R3J-AQ-004` |
| Stop rule | `CONDITION_B_MET_STOP_ACQUISITION` | Three consecutive targeted batches added no material gain toward a failed gate |

The value 934 is a heterogeneous lower bound and is not an effective-sample
total. It must not be used for readiness, source concentration, or split size.
It deliberately excludes unenumerated Bichlmaier workbook/NMR records and all
reported article sample counts whose raw records were unavailable.

## Authorized file-audit outcomes

### Liang / Dryad

The DOI resolver and Dryad API identified record `124603`, but the API returned
that the identifier could not be viewed or was missing required elements. No
payload, version, row, context cell, relationship, or effective sample was
inferred. Result: `NO_MATERIAL_GAIN_INACCESSIBLE`.

### Golovinsky / Zenodo

Version 1.1 exposed four dataset files; the readme and sensory workbook were
audited. The workbook had 526 raw data rows, 196 unique sample IDs, 330 repeated
sample rows, and four named panelists. Zenodo's structured license field said
CC BY 4.0 while the record description imposed CC BY-NC / non-commercial use.
Direct public panelist names and the unresolved rights conflict force zero
admitted and zero effective units. Result:
`QUARANTINED_RIGHTS_AND_PRIVACY`.

### Bichlmaier / Mendeley

The version-1 archive contained 571 files; all 14 official top-level file hashes
matched the repository inventory. The deposit is CC BY 4.0, but the human
sensory evaluation and DoT workbooks contain participant and
TAS2R43-style genotype fields. Safe brewing, roasting, and chemistry files do
not provide source-local sensory outcomes. Raw rows remain
`UNKNOWN_NOT_ENUMERATED`; admitted and effective units are zero. Result:
`NO_MATERIAL_GAIN_QUARANTINED_OR_NON_SENSORY`.

### `guchengf` / author archive

Five HTML files totaling 20,135 bytes were acquired into a version-addressed,
no-overwrite path and hashed completely. Four are source-authored 2025 zh-Hans
coffee-review documents; the home page is the CC BY 4.0 license locator and is
not a language document. The bounded author-main-prose review produced 22
source-reviewed occurrences and 22 unique normalized candidate expressions,
with zero duplicate extra occurrences and zero machine/project translations.
Every candidate remains `UNRESOLVED`, `gold_label=false`,
`counts_toward_governed_total=false`,
`admission_state=DERIVED_CANDIDATE_NOT_IMPORTED`, and
`sampling_eligible=false`. This establishes one independent source-family
feasibility gain, four candidate documents, and material observed candidate
coverage without adding any governed or training-eligible row. Result:
`MATERIAL_ACQUISITION_GAIN_DERIVED_CANDIDATES_NOT_IMPORTED`.

### Xian Zhang / Mendeley

All six version-2 files matched the repository hashes. `merged.xlsx` and
`overall.xlsx` each contain 202 subject rows, so 404 is a raw representation
count for 202 participant groups, not 404 independent people. The workbooks
contain participant IDs, demographics, experimental variables, and free text.
The two comment columns contained 124 and 125 nonempty values respectively,
but zero source-authored zh-Hans comments. Result:
`NO_MATERIAL_GAIN_PRIVACY_AND_LANGUAGE`.

## Scale interpretation

The acquisition stage increased reproducible candidate coverage only through
the bounded `guchengf` snapshot and its 22 source-reviewed but unresolved
candidate expressions. It did not add governed expressions, effective samples,
context cells, relationship evidence, training-eligible examples, or a frozen
split. Rights-cleared bytes, raw-row volume, and non-eligible derived candidates
are not substitutes for task-specific eligibility. A later governance/import
decision, if any, must report admitted rows and effective units separately
without rewriting the raw-acquisition counts.
