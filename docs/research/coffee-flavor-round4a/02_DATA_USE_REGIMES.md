# Data-use regimes

The authoritative regimes are `REFERENCE_ONLY`, `PROJECT_EXPERIMENT_ALLOWED`,
`FIRST_PARTY_BEHAVIORAL_ALLOWED`, `DEPLOYMENT_ALLOWED`, and `PROHIBITED`.
Promotion between them is never inferred.

- `REFERENCE_ONLY` supports display, audit, source-frequency statistics, and
  candidate generation without gradient updates.
- `PROJECT_EXPERIMENT_ALLOWED` additionally requires explicit rights, task and
  label provenance, project review, and leakage-safe grouped splits.
- `FIRST_PARTY_BEHAVIORAL_ALLOWED` requires versioned consent, pseudonymous
  participant/session identity, withdrawal/deletion, and participant grouping.
- `DEPLOYMENT_ALLOWED` additionally requires deployment/commercial rights,
  privacy and retention controls, a deployment manifest, model card,
  monitoring, and rollback.
- `PROHIBITED` supplies no model, redistribution, or automatic promotion use.

The machine contract is `db/data/round4a/DATA_USE_REGIME.tsv`. Human review
does not create model rights, and public availability does not create reuse
permission.
