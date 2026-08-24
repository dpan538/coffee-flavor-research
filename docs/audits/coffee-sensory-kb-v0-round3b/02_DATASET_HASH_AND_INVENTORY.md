# Dataset hash and inventory receipt

`SNAPSHOT_KEY=context.snapshot.round3b_v1`

`SNAPSHOT_SHA256=aca93ed92f0c032f81709bc35d3db102a10bfdddf684c09765228ee1a5481355`

`CONTEXT_DATASET_ROW_COUNT=4817`

| Frozen file                       |   Bytes | Rows | SHA-256                                                            |
| --------------------------------- | ------: | ---: | ------------------------------------------------------------------ |
| `cotter_dataset.csv`              |  542026 | 3186 | `931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114` |
| `README.txt`                      |    8479 |  n/a | `f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e` |
| `Acids_in_Coffee_-CGAs.csv`       | 1461458 | 1344 | `3cd45f9640db5e1d3cff1e188daa56e64bf3aa5c0659b3d7319188da2d32a112` |
| `Acids_in_Coffee_-OAs.csv`        |   36082 |  287 | `3de0483c14b310dfa0f960d0f5096df014483dcdb14ef217d239432c316b808d` |
| `Acids_in_Coffee_-References.csv` |   50950 |  183 | `d43166417e425f471be6d14d03d2c28a3eb5edf3c8ac30106c31b415ac46a9b5` |
| `ReadMe.xlsx`                     |   13689 |   79 | `6d6e6edb55cd46c02a957e8a84072d11a2b19ff2ac794b1ba132c8c6a3a11530` |

The context record derivation is 3,186 + 1,344 + 287 = 4,817. Raw labels,
file/row locators, source payload, normalized context, outcome flags, and
black/milk mode are stored separately. Snapshot and raw-row freeze triggers
make the persisted receipt immutable.
