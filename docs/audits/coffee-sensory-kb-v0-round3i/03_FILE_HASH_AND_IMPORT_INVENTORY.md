# File-hash and import inventory

The candidate register and pre-import contract are hash-governed:

| Artifact                                             | SHA-256                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------ |
| `db/data/round3i/source_candidate_register.tsv`      | `4688ef6da5c1b7cdbb667316529ff42e33b34f25b07e9212ee16a5f5603cb3e2` |
| `db/data/round3i/database_freeze_expected_state.tsv` | `ea3d599eb3f5eca4a0cecfadaa72be9a382d5425d7c1b87259fabae53c196955` |
| Evaluation batch result                              | `b1555abead882226d5fc48e28595003a2fc8728dfe00f28f21f1231b2507815e` |
| Firstbloom batch result                              | `5d48fd82f43344a8c6c4d8447a80f30917997925669188546747108b9909d5b2` |
| `zh-Hans` batch result                               | `f3b31c938daf723e4b9e5a53ebd0dc5fb4ba4b27ac81766976a75d4c92301a5d` |
| Relationship source annotation                       | `51ba8482867c64f05769d364c9f6e54f3ffb585849075b91809c408f97590190` |
| Relationship batch result                            | `1fe5de836a60e466ef45e07628b06fa6207c2fa4f99d18761d06c01aad08c932` |

## Row inventory

| Batch                                | Documents | Expression rows |              Occurrences or claims | Global expression gain |
| ------------------------------------ | --------: | --------------: | ---------------------------------: | ---------------------: |
| Evaluation: Cotter, Bollen, Vezzulli |     3,289 |              37 |                             11,444 |                     18 |
| Firstbloom long tail                 |       840 |             953 |                              1,058 |                    952 |
| Source-authored `zh-Hans`            |         8 |             249 |                                253 |                    249 |
| Cotter relationship                  |         0 |               0 | 1 claim; 27 derived condition rows |                      0 |
| Total                                |     4,137 |           1,239 |       12,755 occurrences + 1 claim |                  1,219 |

The imported-row receipt is therefore 12,756 governed additions when language
occurrences and the one relationship claim are counted; document and
expression registries are reported separately to avoid double counting.

Source annotation also reports raw/admitted/excluded candidate occurrence or
cell accounting under the exact unit
`reviewed_candidate_sensory_occurrence_or_cell`. It is not interchangeable with
the physical-file row counts, 4,137 document rows, or 12,755 admitted occurrence
rows reported in this inventory.

The Cotter relationship-role record uses the different, explicit unit
`source_consumer_evaluation_row`: 3,186 rows reviewed, 3,186 admitted, and zero
excluded. Its 27 condition aggregates and one claim are derived outputs, not
additional source rows or a new independent family.

`NEW_IMMUTABLE_SNAPSHOT_COUNT=7` counts governed role/version snapshots: three
evaluation sources, one Firstbloom source, two source-authored `zh-Hans`
sources, and one Cotter relationship source/version role. The relationship role
shares Cotter's canonical origin and therefore does not inflate the independent
family count.

Firstbloom governance additionally stores 1,020 text-free candidate identities,
2,040 review decisions, and 1,020 consensus rows. Of those identities, 953
receive two independent admitting decisions; one overlaps the governed
baseline, so the incremental gain is 952.

Every admitted source manifest includes exact file locators and SHA-256 values.
The freeze exporter produced these candidate artifacts:

| Freeze artifact             |   Rows | SHA-256                                                            |
| --------------------------- | -----: | ------------------------------------------------------------------ |
| `CANONICAL_INVENTORY.tsv`   |    193 | `5370b37e46b2e38e978633c69d027e94f04d39b2355062cc69f455a4c5abe715` |
| `SOURCE_INVENTORY.tsv`      |     35 | `37263bd203e736aa2832f5a090dc25afd07610b07ac63965e0874d6be9b16363` |
| `RAW_FILE_MANIFEST.tsv`     |     38 | `36acdc2f2a49642bbd0609e1b51f136d94ac62ee8fa9995ca3d06ee6038764f1` |
| `SENSORY_INVENTORY.tsv`     |     24 | `1de3f11919ee264a7bafffd491522c4eb161b9649c2019dc034bf67e87b495f3` |
| `CONTEXT_COVERAGE.tsv`      |    129 | `3a17d6d2db7e6499a6dc13c1a59e96898c6c135dcd2a8d13034aeb251a7cfc68` |
| `LANGUAGE_CORPUS.tsv`       | 14,532 | `b5509f8d60cea90a76421a7fad489be10456d2ccb8c66ef0bc135acf02fbbb02` |
| `RELATIONSHIP_EVIDENCE.tsv` |     80 | `8565053a83f369b8dbd627f315d6ec82f5bf4a06a8c4ad5a58a14395eb53ccb2` |
| `QUESTION_EVIDENCE.tsv`     |     12 | `17ff588f8452a85805dc34a2dfae4a1844fa0d6c733c4885a7832996e341ff24` |
| `FEATURE_REGISTRY.tsv`      |     77 | `2691f475037976d51104e4007d6b6cc9aa138b0e730621994617bfc6b4577ef6` |
| `SOURCE_PARTITION.tsv`      |     12 | `978a494af8e534633768c75fd5844394f53e2445a6ad523c69afa7eb6890ac10` |
| `FREEZE_MANIFEST.json`      |    n/a | `10ed5e29972082bc5046e6fb9c14be3f24b103a94a79c2482e5cd4819aa3991e` |

The row counts exclude each TSV header. The JSON manifest is intentionally
non-self-referential: it registers the 10 TSV digests, while its own exact-byte
digest is bound externally in migration 048. Independent two-rebuild equality
is still reported in `12_REPRODUCIBILITY.md` rather than inferred from this
single export.
