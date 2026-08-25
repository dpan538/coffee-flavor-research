# Database forward changes

Four forward-only migrations were appended:

- `026_calibration_governance.sql`: study, protocol, analysis, release, ethics,
  and direct-identifier governance;
- `027_calibration_experiment_schema.sql`: lots, roasts, preparation,
  beverages, pseudonymous assessors, sessions, randomization, observations,
  questions, judgments, grouped splits, analyses, and candidate output;
- `028_calibration_question_bank_and_plan_seed.sql`: zero-observation study,
  three design scales, frozen protocol/analysis plan, and 12
  language-specific question rows with 36 options;
- `029_calibration_views_validation.sql`: indexes, readiness/question/data
  inventory views, and 14 expected-zero checks.

`db/migration-baselines/round3b.sha256` freezes migrations 000-025. Historical
migration hashes, ontology rows, corpus snapshots, and Round 3A/3B context data
remain unchanged. Calibration records never enter canonical ontology tables.
