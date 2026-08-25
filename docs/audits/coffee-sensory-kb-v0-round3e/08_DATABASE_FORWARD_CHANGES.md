# Database forward-change receipt

Only three new migrations were added:

- `033_round3e_external_evidence_contract.sql`: snapshot/file/dictionary,
  source-local observation, corpus, question-research, coverage, audit and
  prohibition contracts with blocking triggers.
- `034_round3e_external_evidence_seed.sql`: deterministic import of the exact
  four snapshots and derived source-local artifacts.
- `035_round3e_views_validation.sql`: distributable views, inventories and
  validation checks.

Existing `evidence`, `corpus`, `context`, `calibration` and `audit` schemas are
used. No Round 3E schema was created. External observations are not inserted
into canonical ontology tables. Migrations 000–032 and all frozen Round 3C/3D
decisions/evidence remain unchanged.

`FORWARD_MIGRATION_COUNT=3`

`PGVECTOR_EXTENSION_PRESENT=false`
