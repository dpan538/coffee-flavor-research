# File hash and import inventory

| Snapshot             | File                                                    | SHA-256                                                            |
| -------------------- | ------------------------------------------------------- | ------------------------------------------------------------------ |
| FT-NIR v4            | `file_inventory.json`                                   | `2303a63cfaecee7ca19104993c43b7b01a08dceb94c2fcde3df2977329d3c664` |
| FT-NIR v4            | `Sample_origin_and_sensory_score_Specialty_Coffee.xlsx` | `71926de32c4d183c4c627efb00d5c32fa530844e92d5e4ea011f6d05e1a35a8e` |
| FT-NIR v4            | `SensoryQuality_RoastedCoffee.xlsx`                     | `4d6a39b332887f2f3a519bf73bd7631a77821a784bc9094a4a52e932c02a3174` |
| taste sensitivity v1 | `file_inventory.json`                                   | `2600818a4ef26b84b7b52c479137545c5c18c11779919e5edb0e670b3d8eb644` |
| taste sensitivity v1 | `Coffee_sensory_information_data.xlsx`                  | `1ef4bc85e81ff56e396c98108373a0b4626f89dc9c920f521b001979c590bab3` |
| Wikidata             | `entities.json`                                         | `c2a65e166483124750118ac8c57f9cf92f5610ca7f3cebe5d45a8f596c0bbc42` |
| USDA FDC             | `coffee_search.json`                                    | `7f72598967e210c1479ac8d399f16213fde6ba5e53852b8c2a625ce28868de36` |

| Metric                          | Count |
| ------------------------------- | ----: |
| snapshots                       |     4 |
| frozen files / validated hashes | 7 / 7 |
| declared raw rows               |   477 |
| imported source-local records   |   459 |
| external observations           |   413 |
| corpus documents                |    46 |
| explicit exclusions             |    18 |

Each snapshot records version, row/field count, import version,
`IMPORT_CODE_SHA`, license, rights/privacy decisions and creation date. Derived
records reference the exact snapshot. Raw, parsed and normalized values occupy
separate fields.
