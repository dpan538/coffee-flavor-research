# File hash and import inventory

| File                                  | Role / export                                  |  Bytes |               Rows / fields | SHA-256                                                            |
| ------------------------------------- | ---------------------------------------------- | -----: | --------------------------: | ------------------------------------------------------------------ |
| `Dataset.xlsx`                        | raw external; participant codes; not committed | 834747 | 956 structural / 41 maximum | `299c4ee083b8cc5a67608c1280a75e963e93d64478d2d70755ad299f9e5e8dda` |
| `liberica_rata_summary_matrix.tsv`    | de-identified public aggregate                 |   1549 |                     10 / 10 | `05c70310bc9ca64bde3bd3f02da0c029a2043446799e340ad83ecafd2f01babc` |
| `enwiktionary_revision_metadata.json` | public revision metadata                       |   1206 |                       6 / 5 | `d3c68aa73dc9f4974abb104ae986017f90560b4befbd40670a4f20daeb72bfa8` |
| `zhwiktionary_revision_metadata.json` | public revision metadata                       |   1174 |                       9 / 5 | `fab81d42e2758bc7d656fa5e41ea305f7d92a8294d1a89c90e771a28dd280ac2` |

All four declared and verified hashes match. The three committed local artifacts
are rehashed by `db/scripts/test-round3g-artifact-contract.py`; the raw workbook
was locally rehashed against Mendeley metadata during acquisition and remains
at its immutable public locator.
