\set ON_ERROR_STOP on

-- Deterministic Round 3D engineering-pilot seed.
-- Planned samples are not empirical observations. The only synthetic cases are
-- the five explicitly labelled DRY_RUN_FIXTURE mechanics checks.

BEGIN;

INSERT INTO calibration.pilot_matrix_snapshot (
    pilot_matrix_snapshot_key, study_id, protocol_version_id,
    generator_path, randomization_seed, matrix_sha256,
    randomization_sha256, question_assignment_sha256, protocol_sha256,
    split_inventory_sha256, coffee_lot_count, roast_batch_count,
    preparation_family_count, roast_category_count, condition_cell_count,
    beverage_sample_count, session_slot_count, presentation_slot_count,
    question_assignment_slot_count, dry_run_fixture_count,
    real_observation_count, is_frozen
)
SELECT
    'pilot_matrix.round3d.minimum.2026_08_25',
    study.study_id,
    protocol.protocol_version_id,
    'db/scripts/generate-round3d-pilot.py',
    'coffee-context-calibration-minimum-pilot-20260825-v1',
    'dbd56b90672e00af5fe17a4d8c2c50b996d020a29e39dce04e9bd752de6d356b',
    'eb7aa3fbfa6daf2d94819c007c42cdb43efcbbe4540335f231907b0b4a6edb4b',
    '3e48c83feff27767cf68792f6a9e4c51e80c21aabf0cb419a1cfb02261a528e9',
    '4c759fcae812203c40394d1f510e93c4a83430a3dfb298e832b5ffc49f5924ad',
    'fe76dab2f695a0e7a1d23eb0744c97fb7c832e069cd9b060d26da47c3cebe45a',
    2, 14, 7, 7, 66, 132, 192, 1512, 3600, 5, 0, TRUE
FROM calibration.study AS study
JOIN calibration.protocol_version AS protocol
  ON protocol.study_id = study.study_id
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND protocol.protocol_version_key =
      'protocol.context_calibration_v0.2026_08_25';

CREATE TEMPORARY TABLE round3d_coffee_lot_stage (
    coffee_lot_key TEXT,
    public_lot_code TEXT,
    record_status TEXT
);

\copy round3d_coffee_lot_stage FROM 'db/data/round3d/generated/coffee_lots.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.coffee_lot (
    coffee_lot_key, study_id, public_lot_code, material_metadata
)
SELECT
    stage.coffee_lot_key,
    study.study_id,
    stage.public_lot_code,
    jsonb_build_object('record_status', stage.record_status)
FROM round3d_coffee_lot_stage AS stage
CROSS JOIN calibration.study AS study
WHERE study.study_key = 'study.context_calibration_v0.minimum';

CREATE TEMPORARY TABLE round3d_roast_batch_stage (
    roast_batch_key TEXT,
    coffee_lot_key TEXT,
    roast_category_key TEXT,
    batch_code TEXT,
    record_status TEXT
);

\copy round3d_roast_batch_stage FROM 'db/data/round3d/generated/roast_batches.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.roast_batch (
    roast_batch_key, coffee_lot_id, roast_category_id, batch_code,
    roast_metadata
)
SELECT
    stage.roast_batch_key,
    lot.coffee_lot_id,
    category.roast_category_id,
    stage.batch_code,
    jsonb_build_object('record_status', stage.record_status)
FROM round3d_roast_batch_stage AS stage
JOIN calibration.coffee_lot AS lot
  ON lot.coffee_lot_key = stage.coffee_lot_key
JOIN context.roast_category AS category
  ON category.roast_category_key = stage.roast_category_key;

CREATE TEMPORARY TABLE round3d_preparation_stage (
    preparation_condition_key TEXT,
    preparation_concept_key TEXT,
    condition_code TEXT,
    coffee_mode_code TEXT,
    paired_black_condition_key TEXT,
    recipe_json TEXT
);

\copy round3d_preparation_stage FROM 'db/data/round3d/generated/preparation_conditions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.preparation_condition (
    preparation_condition_key, study_id, preparation_concept_id,
    condition_code, coffee_mode_code, paired_black_condition_id, recipe
)
SELECT
    stage.preparation_condition_key,
    study.study_id,
    concept.preparation_concept_id,
    stage.condition_code,
    stage.coffee_mode_code,
    NULL,
    stage.recipe_json::JSONB
FROM round3d_preparation_stage AS stage
CROSS JOIN calibration.study AS study
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_key = stage.preparation_concept_key
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND stage.coffee_mode_code = 'black_coffee';

INSERT INTO calibration.preparation_condition (
    preparation_condition_key, study_id, preparation_concept_id,
    condition_code, coffee_mode_code, paired_black_condition_id, recipe
)
SELECT
    stage.preparation_condition_key,
    study.study_id,
    concept.preparation_concept_id,
    stage.condition_code,
    stage.coffee_mode_code,
    paired.preparation_condition_id,
    stage.recipe_json::JSONB
FROM round3d_preparation_stage AS stage
CROSS JOIN calibration.study AS study
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_key = stage.preparation_concept_key
JOIN calibration.preparation_condition AS paired
  ON paired.preparation_condition_key = stage.paired_black_condition_key
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND stage.coffee_mode_code = 'milk_coffee';

CREATE TEMPORARY TABLE round3d_beverage_sample_stage (
    beverage_sample_key TEXT,
    coffee_lot_key TEXT,
    roast_batch_key TEXT,
    preparation_condition_key TEXT,
    replicate_number SMALLINT,
    record_origin_code TEXT
);

\copy round3d_beverage_sample_stage FROM 'db/data/round3d/generated/beverage_samples.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.beverage_sample (
    beverage_sample_key, study_id, protocol_version_id, coffee_lot_id,
    roast_batch_id, preparation_condition_id, replicate_number,
    record_origin_code, preparation_metadata
)
SELECT
    stage.beverage_sample_key,
    study.study_id,
    protocol.protocol_version_id,
    lot.coffee_lot_id,
    roast.roast_batch_id,
    preparation.preparation_condition_id,
    stage.replicate_number,
    stage.record_origin_code,
    jsonb_build_object('status', 'PLANNED_NOT_PREPARED')
FROM round3d_beverage_sample_stage AS stage
CROSS JOIN calibration.study AS study
JOIN calibration.protocol_version AS protocol
  ON protocol.study_id = study.study_id
JOIN calibration.coffee_lot AS lot
  ON lot.coffee_lot_key = stage.coffee_lot_key
JOIN calibration.roast_batch AS roast
  ON roast.roast_batch_key = stage.roast_batch_key
JOIN calibration.preparation_condition AS preparation
  ON preparation.preparation_condition_key = stage.preparation_condition_key
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND protocol.protocol_version_key =
      'protocol.context_calibration_v0.2026_08_25';

CREATE TEMPORARY TABLE round3d_session_slot_stage (
    session_slot_key TEXT,
    cohort_code TEXT,
    assessor_slot_code TEXT,
    session_number SMALLINT,
    sample_burden SMALLINT
);

\copy round3d_session_slot_stage FROM 'db/data/round3d/generated/session_slots.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.pilot_session_slot (
    pilot_matrix_snapshot_id, session_slot_key, cohort_code,
    assessor_slot_code, session_number, sample_burden
)
SELECT
    snapshot.pilot_matrix_snapshot_id,
    stage.session_slot_key,
    stage.cohort_code,
    stage.assessor_slot_code,
    stage.session_number,
    stage.sample_burden
FROM round3d_session_slot_stage AS stage
CROSS JOIN calibration.pilot_matrix_snapshot AS snapshot
WHERE snapshot.pilot_matrix_snapshot_key =
      'pilot_matrix.round3d.minimum.2026_08_25';

CREATE TEMPORARY TABLE round3d_presentation_slot_stage (
    presentation_slot_key TEXT,
    session_slot_key TEXT,
    beverage_sample_key TEXT,
    sequence_position SMALLINT,
    blinded_code TEXT
);

\copy round3d_presentation_slot_stage FROM 'db/data/round3d/generated/presentation_slots.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.pilot_presentation_slot (
    pilot_session_slot_id, presentation_slot_key, beverage_sample_id,
    sequence_position, blinded_code
)
SELECT
    session.pilot_session_slot_id,
    stage.presentation_slot_key,
    sample.beverage_sample_id,
    stage.sequence_position,
    stage.blinded_code
FROM round3d_presentation_slot_stage AS stage
JOIN calibration.pilot_session_slot AS session
  ON session.session_slot_key = stage.session_slot_key
JOIN calibration.beverage_sample AS sample
  ON sample.beverage_sample_key = stage.beverage_sample_key;

CREATE TEMPORARY TABLE round3d_question_assignment_stage (
    question_assignment_slot_key TEXT,
    presentation_slot_key TEXT,
    step_number SMALLINT,
    logical_question_code TEXT,
    assignment_status TEXT
);

\copy round3d_question_assignment_stage FROM 'db/data/round3d/generated/question_assignment_slots.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.pilot_question_assignment_slot (
    pilot_presentation_slot_id, question_assignment_slot_key,
    step_number, logical_question_code, assignment_status
)
SELECT
    presentation.pilot_presentation_slot_id,
    stage.question_assignment_slot_key,
    stage.step_number,
    stage.logical_question_code,
    stage.assignment_status
FROM round3d_question_assignment_stage AS stage
JOIN calibration.pilot_presentation_slot AS presentation
  ON presentation.presentation_slot_key = stage.presentation_slot_key;

CREATE TEMPORARY TABLE round3d_dry_run_case_stage (
    dry_run_case_key TEXT,
    c0_code TEXT,
    c1_code TEXT,
    answer_path TEXT,
    expected_stop_step SMALLINT,
    explicit_override BOOLEAN,
    fixture_label TEXT
);

\copy round3d_dry_run_case_stage FROM 'db/data/round3d/generated/dry_run_cases.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO calibration.engineering_dry_run_case (
    pilot_matrix_snapshot_id, dry_run_case_key, c0_code, c1_code,
    answer_path, expected_stop_step, explicit_override, fixture_label,
    mechanics_pass
)
SELECT
    snapshot.pilot_matrix_snapshot_id,
    stage.dry_run_case_key,
    stage.c0_code,
    stage.c1_code,
    stage.answer_path,
    stage.expected_stop_step,
    stage.explicit_override,
    stage.fixture_label,
    TRUE
FROM round3d_dry_run_case_stage AS stage
CROSS JOIN calibration.pilot_matrix_snapshot AS snapshot
WHERE snapshot.pilot_matrix_snapshot_key =
      'pilot_matrix.round3d.minimum.2026_08_25';

INSERT INTO calibration.capture_import_batch (
    capture_import_batch_key, study_id, protocol_version_id,
    source_manifest_sha256, staged_row_count, real_row_count,
    fixture_row_count, pii_scan_pass, governance_gate_pass,
    promotion_status
)
SELECT
    'capture_import.round3d.empty_template.2026_08_25',
    study.study_id,
    protocol.protocol_version_id,
    '062198d21cf56d3ac1f1bf9faea30169ca89efb12cbbabc0190178b4dfb8d063',
    0, 0, 0, TRUE, FALSE, 'validated_empty'
FROM calibration.study AS study
JOIN calibration.protocol_version AS protocol
  ON protocol.study_id = study.study_id
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND protocol.protocol_version_key =
      'protocol.context_calibration_v0.2026_08_25';

INSERT INTO calibration.analysis_plan (
    analysis_plan_key, study_id, version_label, repository_path,
    content_sha256, split_method, split_seed, grouping_variable,
    estimability_status, is_frozen
)
SELECT
    'analysis_plan.context_calibration_v0.round3d.2026_08_25',
    study.study_id,
    'v0.1.0-pilot-dry-run',
    'db/data/round3d/generated/baseline_analysis.json',
    '4a7688075dd1306b0026bf06b9c05080b45c208fe0c995b67d43e2f371d1381d',
    'lot-grouped development/validation/held-out test; unavailable for the two-lot feasibility pilot',
    'coffee-context-calibration-v0-lot-split-20260825',
    'coffee_lot_id',
    'NOT_ESTIMABLE',
    TRUE
FROM calibration.study AS study
WHERE study.study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.release_snapshot (
    release_snapshot_key, study_id, protocol_version_id, analysis_plan_id,
    version_label, lifecycle_status_code, manifest_sha256,
    checksums_sha256, license_spdx, rights_statement,
    split_snapshot_sha256, real_observation_count, dry_run_fixture_count
)
SELECT
    'release.context_calibration_v0.protocol_schema_v0_1_0',
    study.study_id,
    protocol.protocol_version_id,
    plan.analysis_plan_id,
    'protocol-and-schema-v0.1.0',
    'internal',
    '062198d21cf56d3ac1f1bf9faea30169ca89efb12cbbabc0190178b4dfb8d063',
    '1ac82525c830148bd54f25236148ea2ba8317ad07d318fe61142e40b63bbf30a',
    'CC-BY-4.0',
    'Protocol, schema, data dictionary, and zero-row templates only; no participant observations and no permission to collect before governance approval.',
    'fe76dab2f695a0e7a1d23eb0744c97fb7c832e069cd9b060d26da47c3cebe45a',
    0,
    5
FROM calibration.study AS study
JOIN calibration.protocol_version AS protocol
  ON protocol.study_id = study.study_id
JOIN calibration.analysis_plan AS plan
  ON plan.study_id = study.study_id
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND protocol.protocol_version_key =
      'protocol.context_calibration_v0.2026_08_25'
  AND plan.analysis_plan_key =
      'analysis_plan.context_calibration_v0.round3d.2026_08_25';

INSERT INTO calibration.analysis_run (
    analysis_run_key, analysis_plan_id, release_snapshot_id,
    code_commit_sha, input_snapshot_sha256, estimability_status,
    result_metadata
)
SELECT
    'analysis_run.round3d.minimum.zero_real_observations',
    plan.analysis_plan_id,
    release.release_snapshot_id,
    '181f7a93e3ba55fd809705f929338717854030c7',
    '062198d21cf56d3ac1f1bf9faea30169ca89efb12cbbabc0190178b4dfb8d063',
    'NOT_ESTIMABLE',
    '{
      "analysis_status":"PASS_WITH_NOT_ESTIMABLE_OUTPUTS",
      "deep_learning_model_run":false,
      "embedding_baseline_run":false,
      "fixture_exclusion_pass":true,
      "fixture_observation_count":5,
      "outputs":{
        "assessor_uncertainty":"NOT_ESTIMABLE",
        "average_questions_required":"NOT_ESTIMABLE",
        "candidate_ranking_baseline":"NOT_ESTIMABLE",
        "context_conflict_rate":"NOT_ESTIMABLE",
        "context_support_distributions":"NOT_ESTIMABLE",
        "early_stop_rate":"NOT_ESTIMABLE",
        "explicit_user_override_rate":"NOT_ESTIMABLE",
        "q2_marginal_value":"NOT_ESTIMABLE",
        "q3_marginal_value":"NOT_ESTIMABLE",
        "q4_marginal_value":"NOT_ESTIMABLE",
        "q5_marginal_value":"NOT_ESTIMABLE",
        "question_information_gain":"NOT_ESTIMABLE",
        "repeat_stability":"NOT_ESTIMABLE"
      },
      "pgvector_required":false,
      "real_observation_count":0
    }'::JSONB
FROM calibration.analysis_plan AS plan
JOIN calibration.release_snapshot AS release
  ON release.analysis_plan_id = plan.analysis_plan_id
WHERE plan.analysis_plan_key =
      'analysis_plan.context_calibration_v0.round3d.2026_08_25'
  AND release.release_snapshot_key =
      'release.context_calibration_v0.protocol_schema_v0_1_0';

COMMIT;
