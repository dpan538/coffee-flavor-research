# Round 3J file-hash and import inventory

Only the bounded `guchengf` snapshot is stored under the repository raw-data
path. Golovinsky, Bichlmaier, and Xian Zhang payloads were inspected in a
temporary audit workspace and are not public-corpus artifacts. Liang supplied
no source payload. No audited raw file was imported into a database by this
acquisition stage.

## Repository raw snapshot

Path:
`db/data/round3j/raw/candidate.r3j.guchengf-coffee-reviews-2025/2025-posts-snapshot-20260826/`

| File                                                           |                    Bytes | SHA-256                                                            | Role                                                  |
| -------------------------------------------------------------- | -----------------------: | ------------------------------------------------------------------ | ----------------------------------------------------- |
| `00_home.html`                                                 |                    7,210 | `822da848a0cb1da0f3454cd0e44f61b2853a3e751c13375fdd55ea465c4c7a8a` | License locator; not a language document              |
| `01_sangaria-crown-coffee-260ml.html`                          |                    2,959 | `56b2fd603f9690c27605ac9183908e46a92da9ae33da12136e9f092442b6b542` | Source-authored review                                |
| `02_review-georgia-the-black-coffee-500ml.html`                |                    3,138 | `4d59ea2920dfa7a0e769ae20e0437853ade00ed9f50efc470550fe7b751edc6a` | Source-authored review                                |
| `03_review-ucc-shokunin-no-coffee-sugar-free-black-900ml.html` |                    3,562 | `66903b74256748af4b16f6a0f2d75d01861dd1c08e5875de7b8104bcfbfe113b` | Source-authored review                                |
| `04_review-kirin-fire-one-day-black-coffee-600-ml.html`        |                    3,266 | `51abc486d0ba3a446fa1c588474ae89b2479130b6a941a5e968f343ad08de167` | Source-authored review                                |
| `ACQUISITION_MANIFEST.json`                                    | Generated audit artifact | `3de9a815409774f815bc0d6dee6255d4e21eebc0b10062634a4b531d3a85302e` | Version, candidate row, URLs, byte counts, and hashes |
| `SHA256SUMS`                                                   | Generated audit artifact | `1ebfb823c330fe9e8a6a260739a72f588bb40be39435fbf8ab9ffc0188d944f7` | Hash inventory for manifest and five source files     |

Source-file hash completeness is `5/5 = 1.0000`. The destination is
version-addressed and uses `REFUSE_EXISTING_DESTINATION`; overwriting an
existing snapshot is not permitted.

The deterministic boundary-review artifact is
`db/data/round3j/derived/guchengf_2025_zh_hans_sensory_expressions.tsv`
(98,273 bytes; SHA-256
`35ae3ad4c93db44cd248387edb5d5b28afe1755b27bf5462de91d9961fb4899b`).
It contains 22 source-reviewed occurrences, 22 unique normalized expressions,
four documents, one candidate family, and zero duplicate extra occurrences.
All 22 rows explicitly allow raw-text public export, derived-expression public
release, and model research under CC BY attribution, but all 22 also have
`counts_toward_governed_total=false`,
`admission_state=DERIVED_CANDIDATE_NOT_IMPORTED`, and
`sampling_eligible=false`. The derived file is not a raw source file and its
rows are not raw HTML imports or eligible training units.

## Temporary Golovinsky audit files

Zenodo advertised four files. Only the two files needed for rights, privacy,
row, and sensory-schema review were downloaded. Both were SHA-256 hashed.

| File                       |   Bytes | SHA-256                                                            | Import state                             |
| -------------------------- | ------: | ------------------------------------------------------------------ | ---------------------------------------- |
| `readme.md`                |   2,782 | `cabe9369a6aa9d5fae4bd9c79a1ce71fc86d209ce107c5771b794e834827990a` | Not committed; not imported              |
| `panelists_scores_EN.xlsx` | 148,639 | `85df699ea18f5849ef3104100a20570d5df13e7d6cc7ce53e20c3df8a5219150` | Quarantined; not committed; not imported |

The two electrochemical archives were not acquired because they were not
needed to decide the sensory-corpus rights and privacy question. Hash
completeness therefore means 2/2 audited files, not 4/4 record files.

## Temporary Bichlmaier audit files

The version-1 archive was 97,595,750 bytes and had SHA-256
`28df7f0d72ee9e979a42b14349d1d62bf8221d0875e00f3f2dfbafd32ee365be`.
It contained 571 file entries. The 14 official top-level files reported by the
Mendeley file API all matched their repository SHA-256 values:

| Official file                                           | SHA-256                                                            |
| ------------------------------------------------------- | ------------------------------------------------------------------ |
| `20240712_statistics_calibration_raw data.xlsx`         | `3014104dbe1e5157cbc9283e932bcba551f93dee3c43bb39972cdd67316b6dd9` |
| `20240715_extraction_ANOVA_Tukeys correction.xlsx`      | `9a858c32593610d5c91b403a979de18467d05a98600fd21888ae508886a84512` |
| `20240715_intra- and interday precision.xlsx`           | `2f255537b96d817560b17e011f6fe8fa7d767d2a56d2c233aa9c3ff043562252` |
| `20240715_model_roasting_series_mozambioside.xlsx`      | `4f66f93315b1912cf770323e0c60e3a0889543743579b837bbd329db36a04f38` |
| `20240715_Pacande roasting series.xlsx`                 | `05cedf34c117e0e041794f8c63c79b919cc668ceda670daec5b254c934e735c3` |
| `20240715_repeatability crema espresso.xlsx`            | `a4250e5429b4b9cf18a5ab25749add48c4ca0ae3436ab64a668b4615be474059` |
| `20240716_authentic coffee samples.xlsx`                | `8e2527ae59733c8c559d24245f2df400517539c6b62d7cead28c15fd554d8182` |
| `20240717_green coffee extraction.xlsx`                 | `3f28bf7b06b2d9b08380dfd5a730519339091485e2ac48b8edb82305a3e95fa8` |
| `20241031_brewing methods.xlsx`                         | `afff35accc79191bf8d20f3aee6d1719e59bc97eb689f84c42f13342412d3cde` |
| `20241031_DoT.xlsx`                                     | `bf9def3f5476511f818220877e387a1455176cbf3122503a739b399d9cce6968` |
| `20241101_extraction rates coffee brew.xlsx`            | `593ad0845623a77505ec70c24424ff213ed118d875059b90cb8a9e7bb43fe021` |
| `20241104_brewing methods_ANOVA_Tukeys correction.xlsx` | `dff605e7ca5b91f68d9eec158988356997c8a702914b9a139ba9b401ee3d2709` |
| `20241104_human sensory evaluation.xlsx`                | `928f72702ff8c96f27d35f90cd807def47b6a8fa17ce0b9d19a44d8adbd09b38` |
| `Bichlmaier et al 2024 Purity check.docx`               | `18fc1ef1f47592797dad770712d04d2959c4803020994ed51eb6c40ce49aee5f` |

The archive and extracted files were not committed or imported. Genotype and
participant-bearing files are quarantined; safe chemistry/configuration files
did not yield source-local sensory outcomes.

## Temporary Xian Zhang audit files

The version-2 archive was 171,645 bytes and had SHA-256
`12b5e06d9c8356242cad138c0e22abe484be8596455d1c0925422ab27fb5c359`.
All six archive members matched the Mendeley file API:

| Official file        |  Bytes | SHA-256                                                            |
| -------------------- | -----: | ------------------------------------------------------------------ |
| `CH3-codes.do`       |  8,873 | `db7d3b24cad4b024519ff7c9772030851e06f9bdb7c8900c01d434ef9fd5215b` |
| `merged.xlsx`        | 61,484 | `bc6845f2a5e84e84b906a7386612a5b149f93ab9de3f5de3b60b2ec17c7e2ba4` |
| `overall.xlsx`       | 70,519 | `5a0611f6c5d11795b5c1cf281785831e681f50ace4f5b368f04630df31159a7f` |
| `readme.docx`        | 18,959 | `74e66b9317ac643cf8a354693ac0410e3c72a14d4df79fd41d1b3f71d85378c7` |
| `sentiment.R`        |  1,610 | `fce51975c66cb2fd2232ce6ea02974494b2c5cd25e3a0d1f7a594f25105327e6` |
| `with_sentiment.dta` | 94,684 | `f78a830e08cccca84c3c9e7aa3e025cb650c37afd2fffe2449f46a14ec337eab` |

The API's six individual file sizes total 256,129 bytes; that is distinct from
the compressed archive-container size. None of the six files was committed or
imported.

## Inaccessible Liang record

The 172-byte transient Dryad API response had SHA-256
`2371b6f0477574b1a804042e1ce2584763a434d7eafe5253ca37ae97c74851ef`.
It is an access-failure receipt, not a source payload, and it was not committed
as raw data.

## Inventory totals and boundary

- `AUDITED_PAYLOAD_FILE_COUNT=584`
- `AUDITED_SOURCE_PAYLOAD_BYTES=97938951`
- `METADATA_OR_API_RECEIPT_BYTES=172`
- `REPOSITORY_SOURCE_FILE_COUNT=5`
- `SOURCE_FILE_HASH_COMPLETENESS_FOR_REPOSITORY_SNAPSHOT=1.0000`
- `DERIVED_SOURCE_REVIEWED_CANDIDATE_EXPRESSION_COUNT=22`
- `DERIVED_GOVERNED_EXPRESSION_COUNT=0`
- `DERIVED_TRAINING_ELIGIBLE_COUNT=0`
- `RAW_IMPORT_PERFORMED=false`
- `TEMPORARY_SENSITIVE_OR_RIGHTS_BLOCKED_PAYLOAD_COMMITTED=false`

The 584 count is a file-audit count: 571 Bichlmaier archive members, 6 Xian
archive members, 5 repository HTML source files, and 2 inspected Golovinsky
files. Archive containers, generated manifests, hash-list files, and metadata
API receipts are excluded so that the count is not inflated by packaging.
The 97,938,951 source-payload bytes likewise exclude the 172-byte Liang API
failure receipt. The derived TSV is separately hashed and is not added to
either raw-source measure.
