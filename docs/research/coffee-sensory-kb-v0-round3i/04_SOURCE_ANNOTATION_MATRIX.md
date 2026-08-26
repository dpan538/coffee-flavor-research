# Round 3I source annotation matrix

This matrix records the exact admitted language origins and the one relationship-evidence reuse in the committed Round 3I batches. A source family means one canonical upstream origin, not one repository mirror, file, or database role. The Cotter language and relationship records therefore remain one Dryad origin even though their role-specific keys differ.

## Admitted source-local surfaces

| Canonical origin                                                                                                                                                                           | Exact version and license                                                                                                                                                     | Frozen source file                                                                                                                                                                                                           | Admitted Round 3I surface                                                                                                                                                                                 | Privacy and public-export boundary                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Andrew Cotter, William D. Ristenpart, and Jean-Xavier Guinard, [`Consumer preference data for black coffee`](https://doi.org/10.25338/B8993H), 2023                                        | Dryad version 4, published 2023-01-16; [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)                                                                          | `cotter_dataset.csv`, 542,026 bytes, 3,186 rows, SHA-256 `931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114`; README, 8,479 bytes, SHA-256 `f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e` | 3,186 consumer-evaluation language documents; 10,763 positive CATA occurrences; 17 family-local expressions. The relationship batch separately derives 27 brew-condition aggregates from these same rows. | Source identifiers were removed under IRB 1082568. Public language documents omit `Judge`, `Cluster`, session, position, purchase-intent, and other evaluator-linkage fields. Export state is `PUBLIC_DERIVED_ONLY`; raw-row public export is disabled.                                                          |
| Robrecht Bollen et al., [`Sensory profiles of Robusta coffee genetic resources from the Democratic Republic of the Congo`](https://doi.org/10.3389/fsufs.2024.1382976.s002), 2024          | Frontiers Figshare item 25735122 version 1, published 2024-05-02T04:25:40Z; [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)                                         | Official XLSX, 31,426 bytes, SHA-256 `4ca2bff21183d2615e244f68b330ba23282f56e6d012c7be762f04baa19abb0a`; sanitized 95-row TSV, 24,359 bytes, SHA-256 `af06701d39891c3af2d92d1a493461d33aa8995db1c6a2d39d7239178af20073`      | 95 trained-panel profile documents; 530 positive occurrences; eight family-local descriptor classes. Source-local score and count fields are not pooled.                                                  | The governed TSV contains genotype, harvest, and aggregate sample values but no participant identifiers. Public export uses the sanitized derived TSV, not the workbook metadata. Export state is `PUBLIC_DERIVED_ONLY`.                                                                                         |
| Fosca Vezzulli et al., [`Metabolomics Combined with Sensory Analysis Reveals the Impact of Different Extraction Methods on Coffee Beverages`](https://doi.org/10.3390/foods11060807), 2022 | PMC8953325 full-text XML released 2022-03-26; article Table 2; [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)                                                      | XML, 148,989 bytes, SHA-256 `1120133f98712a44d4af364a578f90bc348d31b51de948381fa1b835b5b26c75`; governed 160-row Table 2 TSV, 28,153 bytes, SHA-256 `1ae24e67eb77ddcf7c85e6fc085a504e022d22df3642211d21d81ee23040066b`       | Eight species-by-extraction trained-panel profile documents; 151 positive occurrences; 19 family-local sensory expressions.                                                                               | Only published panel medians are emitted. Individual panelist rows are unavailable. Color, chemistry, article prose, and third-party form definitions are excluded. Export state is `PUBLIC_DERIVED_ONLY`.                                                                                                       |
| Alex Caza, [`Firstbloom Data`](https://github.com/alexcaza/firstbloom-data), 2023                                                                                                          | Git commit `a6cb0026d1af9642724793c799bbc48dc189ba35`; [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)                                                              | `product_releases.csv`, 627,708 bytes, 5,339 data rows, SHA-256 `f0b556742dfbb7f4122ae00c9b31051c9a2ff233444771742bb538281cf6a8c0`                                                                                           | 840 source-row documents; 1,058 occurrences; 953 dual-reviewed short expressions. This is the historical Round 2B family, so it adds neither a new family nor a countable contemporary document.          | No reviews or personal data are imported. Complete fields, descriptions, disagreement text, and consumer material remain excluded. Public release is restricted to attributed, change-indicated, dual-reviewed short phrases: `PUBLIC_DERIVED_ONLY`.                                                             |
| Junru Zhang, [`Tasting Notes`](https://zhangdeweb.site/2025/03/06/coffee/index.html), 2025                                                                                                 | Git commit `dc5d02885c599df207f6bbd8c2bbc4009a4303e8`; blob `f757d6f40372e33b4d7edb96ec4af69fed237f02`; page footer [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | `2025/03/06/coffee/index.html`, 45,613 bytes, SHA-256 `19c8cce17bf4f97f8354d29a79e7e1e860be4ef8422a8ce65d479e91545dc3c4`                                                                                                     | Seven source-authored Simplified-Chinese documents; 230 occurrences; 226 unique expressions.                                                                                                              | Public author identity only. The admitted scope is the author overview and personal-feeling sections for seven coffee blocks. Reference-flavor package copy, alcohol blocks, images, theme, and UI are excluded. Admitted source phrases are `PUBLIC_RAW` with attribution, license link, and change indication. |
| 泠時月, [`首次冷萃记录`](https://rinzemoon.top/article/articles/LengCui), 2026                                                                                                             | Page dated 2026-04-25; ETag `W/"66db-zkjFNR3Mqp1vGFeK5G55s3we/4U"`; page footer [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)                                     | 26,331-byte response, SHA-256 `bfefe1bba5efbeb508e87f4ea4a45d77adf49683e0b0fb606ee208f0e12a2f7f`                                                                                                                             | One source-authored Simplified-Chinese document; 23 occurrences; 23 unique expressions.                                                                                                                   | Public author identity only. AI advice, comments, contact or security metadata, avatars, images, a friend remark, appearance, milk-preparation context, and the site shell are excluded. Admitted source phrases are `PUBLIC_RAW` with attribution, license link, and change indication.                         |

The six rows represent six canonical language origins. Three are newly countable contemporary evaluation families, Firstbloom is a pre-existing historical family, and the two Simplified-Chinese origins are language-coverage families rather than controlled sensory-outcome families.

## Raw, admitted, and excluded row accounting

Row counts use the reviewed source-local unit named below; they are not silently
interchanged with document, unique-expression, or final occurrence totals. Every
row satisfies `RAW_ROW_COUNT = ADMITTED_ROW_COUNT + EXCLUDED_ROW_COUNT`.

| Role-specific source key                    | Row-count unit                                        |    Raw | Admitted | Excluded |
| ------------------------------------------- | ----------------------------------------------------- | -----: | -------: | -------: |
| `dryad.cotter-v4`                           | candidate CATA sensory cells (`3,186 × 17`)           | 54,162 |   10,763 |   43,399 |
| `figshare.bollen-2024`                      | candidate descriptor-class cells (`95 × 8`)           |    760 |      530 |      230 |
| `pmc.vezzulli-2022`                         | candidate sensory cells excluding color (`8 × 19`)    |    152 |      151 |        1 |
| `github.firstbloom-data.a6cb0026`           | structurally eligible incremental phrase occurrences  |  4,827 |    1,058 |    3,769 |
| `zhangdeweb_junru_zhang_tasting_notes`      | reviewed source-authored sensory occurrences          |    230 |      230 |        0 |
| `rinzemoon_lengcui_lingshiyue`              | reviewed source-authored sensory occurrences          |     23 |       23 |        0 |
| `dryad.cotter-black-coffee.relationship.v4` | consumer tasting rows used in the governed reanalysis |  3,186 |    3,186 |        0 |

The relationship-role admission derives 27 brew-condition aggregates and one
reviewed claim from its 3,186 admitted source rows. Those derived outputs do not
change the source row-accounting unit. Bollen zero-valued/non-reported class
cells, Vezzulli's one zero-valued sensory cell, Cotter's unselected CATA cells,
and Firstbloom fragments rejected by the structural and dual-review gates remain
explicitly excluded rather than fabricated as observed expressions.

## Non-admitted candidate decisions

The frozen ten-row acquisition register also preserves four candidates that were not admitted:

| Candidate                        | Stable locator and terms state                                                                                                             | Decision                               | Controlling limitation                                                                                                                           |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Open Food Facts product database | [Fixed snapshot not yet selected](https://huggingface.co/datasets/openfoodfacts/product-database); ODbL 1.0 database and DbCL 1.0 contents | `PENDING_FIXED_SNAPSHOT_AND_PARTITION` | A separate share-alike federation, exact snapshot, database/content partition, and verified sensory-field yield are required before acquisition. |
| RoastDB                          | [Unversioned register locator](https://github.com/roastdb/data); HTTP 404 on 2026-08-26; upstream content rights unresolved                | `REJECT_RIGHTS`                        | A stale or visible repository locator is not reuse permission.                                                                                   |
| LoffeeLabs coffee data           | [Unversioned organization](https://github.com/LoffeeLabs); upstream content rights unresolved                                              | `REJECT_RIGHTS`                        | No traceable grant covers the catalog tasting text.                                                                                              |
| Coffee Quality Institute mirrors | [Upstream site](https://database.coffeeinstitute.org/); upstream terms unresolved                                                          | `REJECT_RIGHTS_AND_INDEPENDENCE`       | Mirrors cannot clear upstream rights and cannot count as independent origins.                                                                    |

These candidates have no admitted source annotation. Conservatively, all seven language-rights dimensions remain `PENDING` for Open Food Facts and `NOT_CLEARED` for RoastDB, LoffeeLabs, and the CQI mirrors. No raw text, derived expression, derived count, or model-research use is authorized by this register. The register is SHA-256 `4688ef6da5c1b7cdbb667316529ff42e33b34f25b07e9212ee16a5f5603cb3e2`.

## Seven-dimensional rights decision

The stored dimensions are:

- `RT-I`: `raw_text_internal_use`
- `RT-P`: `raw_text_public_redistribution`
- `DE-I`: `derived_expression_internal_use`
- `DE-P`: `derived_expression_public_release`
- `DC-I`: `derived_counts_internal_use`
- `DC-P`: `derived_counts_public_release`
- `MR`: `model_research_use`

| Source key                             | RT-I  | RT-P  | DE-I  | DE-P  | DC-I  | DC-P  | MR    |
| -------------------------------------- | ----- | ----- | ----- | ----- | ----- | ----- | ----- |
| `dryad.cotter-v4`                      | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| `figshare.bollen-2024`                 | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| `pmc.vezzulli-2022`                    | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| `github.firstbloom-data.a6cb0026`      | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| `zhangdeweb_junru_zhang_tasting_notes` | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| `rinzemoon_lengcui_lingshiyue`         | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |

`ALLOW` records the upstream reuse basis. It does not force the project to publish the broadest legally permitted payload. Privacy minimization, third-party-material exclusions, and the public-export states in the first table remain controlling.

## Cotter relationship-role reuse

The relationship artifact uses source key `dryad.cotter-black-coffee.relationship.v4` and family key `family.legacy-cotter-consumers`, while the language artifact uses `dryad.cotter-v4` and `family.baseline.cotter-consumers`. Both resolve to the same Dryad version 4 origin and the same 3,186-row SHA-256. They must not be counted as independent families. The relationship aggregate is SHA-256 `adf26fd10be549b4f4bf74f2e5a45121f85405d1231e874f7cb9a2aecbb3118c`.

## Frozen artifact receipts

| Batch result                                     | SHA-256                                                            |
| ------------------------------------------------ | ------------------------------------------------------------------ |
| `db/data/round3i/evaluation/batch_result.json`   | `b1555abead882226d5fc48e28595003a2fc8728dfe00f28f21f1231b2507815e` |
| `db/data/round3i/firstbloom/batch_result.json`   | `5d48fd82f43344a8c6c4d8447a80f30917997925669188546747108b9909d5b2` |
| `db/data/round3i/zh_hans/batch_result.json`      | `f3b31c938daf723e4b9e5a53ebd0dc5fb4ba4b27ac81766976a75d4c92301a5d` |
| `db/data/round3i/relationship/batch_result.json` | `1fe5de836a60e466ef45e07628b06fa6207c2fa4f99d18761d06c01aad08c932` |

All annotations were accessed or reviewed on 2026-08-26. No source-local scale, phrase, or construct is promoted into a universal coffee standard by admission.
