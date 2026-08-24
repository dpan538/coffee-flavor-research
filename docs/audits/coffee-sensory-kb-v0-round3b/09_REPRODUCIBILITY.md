# Reproducibility receipt

Migrations `000`–`021` are protected by exact SHA-256 entries in
`db/migration-baselines/round3a.sha256`; Round 3B appends four forward
migrations. The planner requires contiguous numbering and refuses any mismatch
at the Round 1, Round 2A, Round 2B, or Round 3A immutable boundary.

The clean-rebuild runner creates two named disposable PostgreSQL 17 databases,
applies all migrations, runs every validation/negative/semantic/retrieval/
query-plan suite, then compares migration and seed hashes, schema-only dumps,
stable keys, reference counts, source-version inventory, all validation
results, ontology coverage, Round 2B/3A historical receipts, and the Round 3B
source/snapshot/projection/metric inventory. Test-generated identity sequence
positions are intentionally excluded.

The final clean-rebuild count and artifact hashes are captured by the local run
and remote PostgreSQL CI rather than embedded as a self-referential commit SHA.

Local PostgreSQL 17.11 receipt:

- `CLEAN_REBUILD_COUNT=2`
- `REPRODUCIBILITY_PASS=true`
- migration inventory SHA-256:
  `18d0647a5b6fc347f01e1a67e93491bcb22629d28f796e65cd2cde4f441e695d`
- schema-only dump SHA-256:
  `d2948a592ab07a02cb795fc2adcd21ac8ebc65761cd33080bf3a2c54e90bf4be`
- Round 3A inventory SHA-256:
  `44c880b248f83f9ca7148e6c7302b99a7f820e1caaf3d2f86b95ff2782443640`
- Round 3B inventory SHA-256:
  `025f2e05a98ad7bccf26f601f5d1c37d06e38c03e772bc2f6acb0b8f367c1e54`
