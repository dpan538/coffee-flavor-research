\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SELECT pilot_matrix_snapshot_key, matrix_sha256, randomization_sha256,
       question_assignment_sha256, coffee_lot_count, roast_batch_count,
       preparation_condition_count, beverage_sample_count,
       session_slot_count, presentation_slot_count,
       question_assignment_slot_count, dry_run_fixture_count,
       real_observation_count
FROM calibration.v_round3d_pilot_inventory;

SELECT session.cohort_code, count(DISTINCT session.pilot_session_slot_id)
       AS session_count, count(presentation.pilot_presentation_slot_id)
       AS presentation_count
FROM calibration.pilot_session_slot AS session
JOIN calibration.pilot_presentation_slot AS presentation
  ON presentation.pilot_session_slot_id = session.pilot_session_slot_id
GROUP BY session.cohort_code
ORDER BY session.cohort_code;

SELECT dry_run_case_key, expected_stop_step, explicit_override,
       fixture_label, mechanics_pass
FROM calibration.engineering_dry_run_case
ORDER BY dry_run_case_key;

SELECT release_snapshot_key, version_label, lifecycle_status_code,
       manifest_sha256, checksums_sha256, license_spdx,
       real_observation_count, dry_run_fixture_count
FROM calibration.release_snapshot
WHERE release_snapshot_key =
      'release.context_calibration_v0.protocol_schema_v0_1_0';

DO $round3d_retrieval_contract$
BEGIN
  IF (SELECT count(*) FROM calibration.pilot_presentation_slot) <> 1512
     OR (SELECT count(*) FROM calibration.pilot_question_assignment_slot) <> 3600
     OR (SELECT count(*) FROM calibration.engineering_dry_run_case) <> 5
     OR EXISTS (SELECT 1 FROM calibration.capture_import_row)
     OR EXISTS (SELECT 1 FROM calibration.assessor)
     OR EXISTS (SELECT 1 FROM calibration.sensory_observation) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3d_retrieval_contract_ck',
      MESSAGE = 'Round 3D retrieval inventory or no-observation boundary changed';
  END IF;
  RAISE NOTICE 'ROUND3D_RETRIEVAL_PASS=true';
END;
$round3d_retrieval_contract$;

ROLLBACK;

\echo ROUND3D_RETRIEVAL_TEST_PASS=true
