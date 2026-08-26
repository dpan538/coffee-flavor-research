# Freeze-manifest audit

The release path is
`db/data/freeze/coffee-sensory-research-db-v0/`. It must contain exactly 11
files:

1. `CANONICAL_INVENTORY.tsv`
2. `SOURCE_INVENTORY.tsv`
3. `RAW_FILE_MANIFEST.tsv`
4. `SENSORY_INVENTORY.tsv`
5. `CONTEXT_COVERAGE.tsv`
6. `LANGUAGE_CORPUS.tsv`
7. `RELATIONSHIP_EVIDENCE.tsv`
8. `QUESTION_EVIDENCE.tsv`
9. `FEATURE_REGISTRY.tsv`
10. `SOURCE_PARTITION.tsv`
11. `FREEZE_MANIFEST.json`

The 10 TSVs are deterministic PostgreSQL exports. The manifest records their
paths, row counts, and SHA-256 values plus the database engine, release version,
expected-state checkpoint, coverage inventory, and prohibited-execution flags.
The manifest intentionally excludes its own digest; its byte hash is registered
externally in migration 048 and the release row.

The declared release is `coffee-sensory-research-db-v0.1.0`. Its verified
starting source checkpoint is
`ccf5769cb5e1f165209e59beaef9fe54017265f5`, and its separately frozen
expected-state checkpoint is
`602624143fef8fa4250e5e84f07478101b0846ff`. Manifest state
`READY_TO_FREEZE` means the artifact set is a candidate, not that exact-main
attestation or the release tag already exists.

The offline contract requires exact coverage values: 9 sensory families, 4,344
sensory rows, 230 samples/configurations, 181 empirical cells, 3 contemporary
language families, 3,289 contemporary documents, 2,996 governed expressions,
2 `zh-Hans` families, 249 `zh-Hans` expressions, 97 relationship claims, 6/4
supported memberships, 6/4 range-evidence breadth, 12 question targets, 20
features, 12 partitions, and 8 approved plus 8 deprecated surfaces.

| Manifest receipt               | Current state                                                       |
| ------------------------------ | ------------------------------------------------------------------- |
| Inventory count                | 10 TSV inventories                                                  |
| Total freeze artifact count    | 11                                                                  |
| Non-self-reference check       | pass                                                                |
| Manifest SHA-256               | `10ed5e29972082bc5046e6fb9c14be3f24b103a94a79c2482e5cd4819aa3991e`  |
| All registered hashes verified | pass: all 11 candidate artifacts match migration 048                |
| Two-rebuild equality           | pass: build one, build two, and committed copies are byte-identical |

`db/scripts/test-round3i-freeze-artifact-contract.py` reports
`ROUND3I_FREEZE_ARTIFACT_CONTRACT_PASS=true`,
`ROUND3I_FREEZE_NON_SELF_REFERENTIAL_MANIFEST_PASS=true`, artifact count 11,
and the manifest digest above. No placeholder digest remains in migration 048.
The external rebuild script reports `CLEAN_REBUILD_COUNT=2`, artifact count 11,
`ROUND3I_FREEZE_REPRODUCIBILITY_PASS=true`, and
`REPRODUCIBILITY_PASS=true`; an independent `cmp` pass found no mismatch among
either rebuild and the committed candidate artifacts.

The local artifact-verification log receipt is SHA-256
`25ac2cebcfec7ebfcc51c733d0c3459f46deed309023e891e3086859ca62c363`
for the 32-line runner output at `/private/tmp/round3i-artifacts-verify-2.log`.
