# Canonical freeze receipt

| Metric                          | Before | After |
| ------------------------------- | -----: | ----: |
| canonical concepts              |    130 |   130 |
| active sensory attributes       |     92 |    92 |
| concept additions               |      0 |     0 |
| splits                          |      0 |     0 |
| merges                          |      0 |     0 |
| retypes                         |      0 |     0 |
| deprecations                    |      0 |     0 |
| canonical relation-type changes |      0 |     0 |

Audit queries assert both inventories. Post-row freeze triggers reject an
otherwise valid concept or relation-type mutation while preserving the expected
failure ordering of historical negative tests.

`CANONICAL_FREEZE_PASS=true`
