# Public dataset sufficiency audit

Search closed: 2026-08-25

## Stopping rule and decision

The search covered Dryad, Mendeley Data, NCBI/PMC supplements, institutional
repositories, GitHub, and a large public taste-test source. A candidate was
sufficient only if it could support context, preparation/roast variation,
question-response mapping or a defensible proxy, and held-out performance with
reusable rights and sample-level rows.

```text
PUBLIC_DATASET_CANDIDATE_COUNT=10
RIGHTS_CLEARED_USABLE_DATASET_COUNT=3
SUFFICIENT_PUBLIC_CALIBRATION_DATASET=false
```

The search stops here unless a new named dataset or lawful file becomes
available. Repeating broad searches is not a future phase gate.

## Candidate inventory

### 1. Consumer preference data for black coffee

- Source: [Dryad 10.25338/B8993H](https://datadryad.org/dataset/doi:10.25338/B8993H)
- Exact version: Dryad version 4, published 2023-01-16.
- License: CC0; commercial, derivative, and machine reuse allowed.
- Inspected files: `cotter_dataset.csv` (542,026 bytes,
  `931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114`)
  and `README.txt` (8,479 bytes,
  `f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e`).
- Rows/scope: 3,186 consumer tastings, 118 consumers, 27 controlled drip
  conditions, one medium-roast washed Honduras coffee, black only.
- Sensory/metadata: CATA, JAR, liking, purchase intent, session/order, TDS,
  extraction, pH, temperature; randomized and IRB-approved.
- Limitations: one preparation family, one roast, no milk, no adaptive question
  bank, no same-coffee preparation-by-roast comparison.
- Decision: rights-cleared reusable fragment; insufficient alone.

### 2. Acids in Coffee review and meta-analysis

- Source: [Dryad 10.25338/B8C91C](https://datadryad.org/dataset/doi:10.25338/B8C91C)
- Exact version: Dryad version 5, published 2021-07-14.
- License: CC0; commercial, derivative, and machine reuse allowed.
- Inspected files/hashes: `Acids_in_Coffee_-CGAs.csv`
  (`3cd45f9640db5e1d3cff1e188daa56e64bf3aa5c0659b3d7319188da2d32a112`),
  `Acids_in_Coffee_-OAs.csv`
  (`3de0483c14b310dfa0f960d0f5096df014483dcdb14ef217d239432c316b808d`),
  `Acids_in_Coffee_-References.csv`
  (`d43166417e425f471be6d14d03d2c28a3eb5edf3c8ac30106c31b415ac46a9b5`),
  and `ReadMe.xlsx`
  (`6d6e6edb55cd46c02a957e8a84072d11a2b19ff2ac794b1ba132c8c6a3a11530`).
- Scope: publication-level chemical meta-analysis with approximate roast
  normalization; heterogeneous extraction protocols and geography.
- Limitations: not a replicated sensory/question dataset and not a controlled
  preparation-by-roast matrix.
- Decision: rights-cleared reusable metadata fragment; insufficient.

### 3. Full-immersion temperature, roast, and time data

- Source/article: [Scientific Reports 10.1038/s41598-024-69867-6](https://doi.org/10.1038/s41598-024-69867-6)
- Claimed repository: Dryad `10.5061/dryad.v15dv423h`.
- Exact article design: 2024 version of record; one Central American blend, two
  roast levels, three temperatures, five time points, 30 samples in triplicate,
  descriptive sensory panel.
- File inspection: the DOI remained inaccessible/not found on 2026-08-25, so
  no dataset files, hashes, or data license could be verified.
- Limitations: one immersion family, two roast levels, trained-panel only, no
  milk or ordinary-user question responses; actual repository unavailable.
- Decision: not importable; insufficient.

### 4. Cold versus hot full-immersion sensory study

- Source: [Foods 10.3390/foods11162440](https://doi.org/10.3390/foods11162440)
- Version/design: 2022 version of record; three origins × three roast levels ×
  three brew temperatures, 81 preparations including triplicates, trained
  descriptive assessment.
- License: CC BY 4.0 article/supplement.
- Inspected file: `foods-11-02440-s001.zip` (133,529 bytes,
  `1428fb57a0cceb168993775822ae20a2124ae5186037bb031af180fffa5c7730`),
  containing only a 151,557-byte one-page PCA supplement. The article states
  that data are available on request.
- Limitations: no public raw assessor rows, one preparation family, no milk or
  ordinary-user questions.
- Decision: design evidence only; insufficient and not a reusable raw dataset.

### 5. Brew strength, yield, and roast sensory study

- Source: [Journal of Food Science 10.1111/1750-3841.15326](https://doi.org/10.1111/1750-3841.15326)
- Version/design: 2020 version of record; one washed Arabica, three roast
  levels, nine target drip brews per roast, 12 assessors, triplicate tasting.
- Listed supporting file: `jfds15326-sup-0001-SuppMat.docx` (778.5 KB),
  containing calculated F-ratios, mean intensities, and figure renderings rather
  than public sample-level assessor rows.
- Rights: article/supporting-data reuse was not established as a standalone
  public dataset license.
- Limitations: one preparation family, three roast levels, no ordinary-user
  questions or milk.
- Decision: methodological evidence only; insufficient.

### 6. FT-NIR spectra and sensory scores

- Source: [Mendeley Data 10.17632/nz2fr76trm.4](https://data.mendeley.com/datasets/nz2fr76trm/4)
- Exact version: version 4, issued 2025-11-24.
- License: CC BY 4.0; commercial, derivative, and machine reuse allowed with
  attribution.
- Actual inventory: 18 XLSX files. Inspected
  `SensoryQuality_RoastedCoffee.xlsx` (12,712 bytes,
  `4d6a39b332887f2f3a519bf73bd7631a77821a784bc9094a4a52e932c02a3174`)
  with 192 replicate rows for 64 samples, and
  `Sample origin and sensory score_Specialty Coffee.xlsx` (16,961 bytes,
  `71926de32c4d183c4c627efb00d5c32fa530844e92d5e4ea011f6d05e1a35a8e`).
- Scope: origin/variety, green/roasted spectra, and overall cup-quality points.
- Limitations: no preparation conditions, roast-category treatment matrix,
  descriptor responses, milk, question responses, or assessor metadata.
- Decision: rights-cleared reusable quality/spectra fragment; insufficient.

### 7. CONFES coffee consumption and user experience

- Source: [KIT 10.35097/u6nn58apj7z60eaa](https://doi.org/10.35097/u6nn58apj7z60eaa)
- Exact version: complete repository version 1, published 2026-07-07.
- License: CC BY-NC-SA 4.0; commercial reuse is not allowed.
- Inspected archive: 9,639,424-byte TAR,
  `27d430f792caca843fe4eabea2a64bdb89fb42d21f847ca739418850eccd9a7c`.
  Inspected CSV: 2,574 rows plus header,
  `7fbd48d98f738bc5b7ba0bc1406af770d604e2af8b96761225f48b5d4e3829b7`.
- Scope: 89 participants; espresso, café crème, cappuccino, latte macchiato,
  milk coffee and additions; recipe, context, overall/intensity/taste/smell
  ratings.
- Privacy: pseudonymous participant keys plus age, height, weight, gender,
  allergy, diet, smoking, location/time, and environmental data require a new
  re-identification and minimization review.
- Limitations: no linked roast variation, canonical descriptor responses,
  controlled coffee identity, or adaptive question bank; noncommercial license.
- Decision: informative but not usable for the intended public commercial
  calibration artifact.

### 8. Liberica Coffee Sensory

- Source: [Mendeley Data 10.17632/m3n2gc4dv6.1](https://data.mendeley.com/datasets/m3n2gc4dv6/1)
- Exact version: version 1, published 2025-10-11.
- License: CC BY 4.0.
- Inspected file: `Dataset.xlsx` (834,747 bytes,
  `299c4ee083b8cc5a67608c1280a75e963e93d64478d2d70755ad299f9e5e8dda`).
- Scope: nine roast/coffee-leaf treatments, chemistry, hedonic and RATA sheets.
- Privacy: workbook headings include a panelist-name field (`Nama Panelis`), so
  direct-identifier review and redaction are required before reuse.
- Limitations: specialized coffee-bag/leaf-infusion product, no comparable
  preparation families, no seven-level scheme or adaptive questions.
- Decision: not usable without privacy remediation and not sufficient.

### 9. Coffee Quality Institute scrape

- Source: [jldbc/coffee-quality-database](https://github.com/jldbc/coffee-quality-database)
- Exact inspected commit: `e3b22b2b1e597887188b97c2ada7f745e1914ec7`.
- Repository license: MIT. Underlying CQI page/data redistribution rights are
  not established by the scraper repository license.
- Inspected files: Arabica raw/clean
  (`90e4d5e0e805f8d86dda5e4259a2e9077c90375be2a4e44928741aac75f8f65c`,
  `f99e588fcdd564e43a779a4b0f3870760018b1ffec7eab7f43db7bedf8f6d670`)
  and Robusta raw/clean
  (`eeedaba933ce18944588ee8d8f26184ddf70e5d0d3652d0ead25173e44400736`,
  `bde9e70dc9e6d1529d4bb690c80a227766a8f747582144a30754a7d4713753bf`).
- Scope: 1,340 quality reviews with farm/process and aggregate quality scores.
- Limitations: no controlled same-lot preparation/roast conditions, no raw
  assessor responses, no replication, no ordinary-user questions, and unclear
  source-data rights.
- Decision: excluded.

### 10. Great American Coffee Taste Test

- Primary release context: [James Hoffmann results video](https://www.youtube.com/watch?v=bMOOQfeloH0)
- Derivative catalog: Kaggle Open Database License listing, updated 2024; no DOI
  or immutable original release version was identified.
- Scope: approximately 4,042 anonymized respondents rating four standardized
  flash-frozen coffee extracts, preferences, flavor notes, habits, and broad
  demographic questions.
- Rights: the original CSV was publicly linked, but a stable source license and
  versioned archival manifest were not verified; the Kaggle license does not
  resolve provenance for every original content field.
- Limitations: four fixed coffees, no crossed preparation or roast treatments,
  no reference sensory cohort, no repeat samples, and no adaptive
  counterfactual assignment.
- Decision: useful question-language precedent; excluded from import and
  insufficient.

## Combined sufficiency conclusion

The strongest controlled sensory studies vary roast or brew conditions within
one preparation family and lack ordinary-user adaptive responses. The strongest
ordinary-user resources lack controlled coffee/preparation/roast linkage or
reference observations. Rights and privacy constraints further prevent simple
pooling.

Protocol heterogeneity, label incompatibility, different coffee identities,
and absent counterfactual question assignments mean that these resources
cannot be concatenated into a defensible calibration dataset. The original
study design is required.
