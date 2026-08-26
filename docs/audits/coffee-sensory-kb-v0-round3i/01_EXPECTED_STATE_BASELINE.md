# Expected-state baseline

The machine-readable contract is
`db/data/round3i/database_freeze_expected_state.tsv`, SHA-256
`ea3d599eb3f5eca4a0cecfadaa72be9a382d5425d7c1b87259fabae53c196955`.
It was committed at
`602624143fef8fa4250e5e84f07478101b0846ff` before the first Round 3I data
import. The threshold-revision count remains zero.

| Dimension                          | Baseline |      Minimum | Preferred | Round 3I evidence result |
| ---------------------------------- | -------: | -----------: | --------: | -----------------------: |
| Canonical concepts                 |      130 |          130 |       130 |                      130 |
| Active sensory attributes          |       92 |           92 |        92 |                       92 |
| Contemporary language families     |        0 |            3 |         5 |                        3 |
| New contemporary documents         |        0 |          500 |     1,500 |                    3,289 |
| Governed unique expressions        |    1,777 |        2,500 |     3,500 |                    2,996 |
| Source-authored `zh-Hans` families |        0 |            2 |         3 |                        2 |
| `zh-Hans` sensory expressions      |        0 | non-blocking |       200 |                      249 |
| Relationship claims                |       96 |           80 |       150 |                       97 |
| Source-local-supported memberships |        6 |            6 |        10 |                        6 |
| Cross-source-supported memberships |        4 |            4 |         6 |                        4 |
| Ranges with source-local evidence  |        6 |            6 |         7 |                        6 |
| Ranges with cross-source evidence  |        3 | non-blocking |         4 |                        4 |
| Feature definitions                |       20 |           20 |        20 |                       20 |
| Source partitions                  |       12 |           12 |        12 |                       12 |

The expected state also requires complete rights, privacy, file-hash, source,
and relationship provenance; eight approved current views; 11 verified freeze
artifacts; two reproducible PostgreSQL 17 rebuilds; green feature and main CI;
and exact-main annotated-tag attestation. The local database, artifact, and
two-rebuild conditions now pass; exact candidate/main identities, remote CI,
promotion, and tag attestation remain externally bound finalization work until
their immutable outputs exist.

The target was not relaxed after source inspection. Preferred misses remain
visible and do not become fabricated hard passes.
