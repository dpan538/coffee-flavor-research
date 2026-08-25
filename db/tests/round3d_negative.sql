\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3d_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3d_failure$
DECLARE actual_state TEXT; actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3D negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                                actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3D_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
          test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3d_failure$;

SELECT pg_temp.expect_round3d_failure(
  'impossible_matrix_count',
  $$INSERT INTO calibration.pilot_matrix_snapshot (
      pilot_matrix_snapshot_key, study_id, protocol_version_id,
      generator_path, randomization_seed, matrix_sha256,
      randomization_sha256, question_assignment_sha256, protocol_sha256,
      split_inventory_sha256, coffee_lot_count, roast_batch_count,
      preparation_family_count, roast_category_count, condition_cell_count,
      beverage_sample_count, session_slot_count, presentation_slot_count,
      question_assignment_slot_count, dry_run_fixture_count,
      real_observation_count, is_frozen
    ) SELECT 'negative.round3d.invalid_matrix', study.study_id,
             protocol.protocol_version_id, 'negative fixture', 'seed',
             repeat('a',64), repeat('b',64), repeat('c',64), repeat('d',64),
             repeat('e',64), 3, 14, 7, 7, 66, 132, 192, 1512, 3600, 5, 0,
             FALSE
      FROM calibration.study AS study
      JOIN calibration.protocol_version AS protocol
        ON protocol.study_id = study.study_id
      WHERE study.study_key = 'study.context_calibration_v0.minimum'$$,
  '23514', 'pilot_matrix_snapshot_text_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'frozen_schedule_mutation',
  $$DELETE FROM calibration.pilot_session_slot
    WHERE session_slot_key =
          'pilot.round3d.session_slot.reference.assessor_001.session_01'$$,
  '23514', 'round3d_frozen_pilot_plan_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'duplicate_assessor_session_slot',
  $$INSERT INTO calibration.pilot_session_slot (
      pilot_matrix_snapshot_id, session_slot_key, cohort_code,
      assessor_slot_code, session_number, sample_burden
    ) SELECT pilot_matrix_snapshot_id,
             'negative.round3d.duplicate_session', cohort_code,
             assessor_slot_code, session_number, sample_burden
      FROM calibration.pilot_session_slot
      WHERE session_slot_key =
            'pilot.round3d.session_slot.reference.assessor_001.session_01'$$,
  '23505', 'pilot_session_slot_assessor_session_uq'
);

SELECT pg_temp.expect_round3d_failure(
  'invalid_session_burden',
  $$INSERT INTO calibration.pilot_session_slot (
      pilot_matrix_snapshot_id, session_slot_key, cohort_code,
      assessor_slot_code, session_number, sample_burden
    ) SELECT pilot_matrix_snapshot_id,
             'negative.round3d.invalid_burden', 'reference',
             'NEGATIVE_SLOT_001', 1, 10
      FROM calibration.pilot_matrix_snapshot
      WHERE pilot_matrix_snapshot_key =
            'pilot_matrix.round3d.minimum.2026_08_25'$$,
  '23514', 'pilot_session_slot_value_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'duplicate_presentation_position',
  $$INSERT INTO calibration.pilot_presentation_slot (
      pilot_session_slot_id, presentation_slot_key, beverage_sample_id,
      sequence_position, blinded_code
    ) SELECT source.pilot_session_slot_id,
             'negative.round3d.duplicate_position', replacement.beverage_sample_id,
             source.sequence_position, '999'
      FROM calibration.pilot_presentation_slot AS source
      CROSS JOIN LATERAL (
        SELECT sample.beverage_sample_id
        FROM calibration.beverage_sample AS sample
        WHERE sample.beverage_sample_id <> source.beverage_sample_id
        ORDER BY sample.beverage_sample_id DESC LIMIT 1
      ) AS replacement
      WHERE source.presentation_slot_key =
            'pilot.round3d.session_slot.reference.assessor_001.session_01.position_01'$$,
  '23505', 'pilot_presentation_slot_position_uq'
);

SELECT pg_temp.expect_round3d_failure(
  'q1_cannot_be_conditional',
  $$INSERT INTO calibration.pilot_question_assignment_slot (
      pilot_presentation_slot_id, question_assignment_slot_key,
      step_number, logical_question_code, assignment_status
    ) SELECT presentation.pilot_presentation_slot_id,
             'negative.round3d.q1_conditional', 1,
             'family_direction', 'conditional'
      FROM calibration.pilot_presentation_slot AS presentation
      JOIN calibration.pilot_session_slot AS session
        ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
      WHERE session.cohort_code = 'reference'
      ORDER BY presentation.pilot_presentation_slot_id LIMIT 1$$,
  '23514', 'pilot_question_assignment_slot_value_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'unlabelled_dry_run_fixture',
  $$INSERT INTO calibration.engineering_dry_run_case (
      pilot_matrix_snapshot_id, dry_run_case_key, c0_code, c1_code,
      answer_path, expected_stop_step, explicit_override, fixture_label
    ) SELECT pilot_matrix_snapshot_id, 'negative.round3d.unlabelled',
             'immersion', 'medium', 'family_direction:fruit_bright',
             1, FALSE, 'real_observation'
      FROM calibration.pilot_matrix_snapshot
      WHERE pilot_matrix_snapshot_key =
            'pilot_matrix.round3d.minimum.2026_08_25'$$,
  '23514', 'engineering_dry_run_case_value_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'capture_direct_identifier',
  $$INSERT INTO calibration.capture_import_row (
      capture_import_batch_id, source_file, source_row_number,
      row_payload, record_origin_code
    ) SELECT capture_import_batch_id, 'assessors.csv', 2,
             '{"email":"participant@example.org"}'::JSONB,
             'TEST_FIXTURE'
      FROM calibration.capture_import_batch
      WHERE capture_import_batch_key =
            'capture_import.round3d.empty_template.2026_08_25'$$,
  '23514', 'capture_import_row_value_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'real_capture_with_governance_gate_closed',
  $$INSERT INTO calibration.capture_import_row (
      capture_import_batch_id, source_file, source_row_number,
      row_payload, record_origin_code
    ) SELECT capture_import_batch_id, 'assessors.csv', 2,
             '{"pseudonymous_code":"SAFE_001"}'::JSONB,
             'real_observation'
      FROM calibration.capture_import_batch
      WHERE capture_import_batch_key =
            'capture_import.round3d.empty_template.2026_08_25'$$,
  '23514', 'real_observation_collection_governance_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'real_assessor_with_governance_gate_closed',
  $$INSERT INTO calibration.assessor (
      assessor_key, study_id, cohort_code, pseudonymous_code,
      language_tag_code, expertise_band, record_origin_code
    ) SELECT 'negative.round3d.real_assessor', study_id, 'ordinary_user',
             'SAFE_REAL_001', 'en', 'ordinary', 'real_observation'
      FROM calibration.study
      WHERE study_key = 'study.context_calibration_v0.minimum'$$,
  '23514', 'real_observation_collection_governance_ck'
);

SELECT pg_temp.expect_round3d_failure(
  'capture_promotion_with_governance_gate_closed',
  $$INSERT INTO calibration.capture_import_batch (
      capture_import_batch_key, study_id, protocol_version_id,
      source_manifest_sha256, staged_row_count, real_row_count,
      fixture_row_count, pii_scan_pass, governance_gate_pass,
      promotion_status
    ) SELECT 'negative.round3d.illegal_promotion', study.study_id,
             protocol.protocol_version_id, repeat('f',64), 1, 1, 0,
             TRUE, TRUE, 'promoted'
      FROM calibration.study AS study
      JOIN calibration.protocol_version AS protocol
        ON protocol.study_id = study.study_id
      WHERE study.study_key = 'study.context_calibration_v0.minimum'$$,
  '23514', 'capture_import_promotion_governance_ck'
);

ROLLBACK;

\echo ROUND3D_NEGATIVE_TEST_PASS=true
