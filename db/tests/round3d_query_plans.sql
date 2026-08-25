\set ON_ERROR_STOP on
\pset pager off

BEGIN;

DO $round3d_query_plan_index_contract$
BEGIN
  IF to_regclass('calibration.pilot_session_slot_snapshot_cohort_idx') IS NULL
     OR to_regclass('calibration.pilot_presentation_slot_sample_idx') IS NULL
     OR to_regclass('calibration.pilot_question_assignment_presentation_idx') IS NULL
     OR to_regclass('calibration.engineering_dry_run_case_snapshot_idx') IS NULL
     OR to_regclass('calibration.capture_import_row_batch_origin_idx') IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3d_query_plan_index_contract_ck',
      MESSAGE = 'A required Round 3D pilot or capture index is missing';
  END IF;
END;
$round3d_query_plan_index_contract$;

EXPLAIN (ANALYZE, BUFFERS)
SELECT presentation.presentation_slot_key, presentation.sequence_position,
       sample.beverage_sample_key
FROM calibration.pilot_session_slot AS session
JOIN calibration.pilot_presentation_slot AS presentation
  ON presentation.pilot_session_slot_id = session.pilot_session_slot_id
JOIN calibration.beverage_sample AS sample
  ON sample.beverage_sample_id = presentation.beverage_sample_id
WHERE session.pilot_matrix_snapshot_id = (
        SELECT pilot_matrix_snapshot_id
        FROM calibration.pilot_matrix_snapshot
        WHERE pilot_matrix_snapshot_key =
              'pilot_matrix.round3d.minimum.2026_08_25'
      )
  AND session.cohort_code = 'ordinary_user'
ORDER BY session.assessor_slot_code, session.session_number,
         presentation.sequence_position
LIMIT 24;

EXPLAIN (ANALYZE, BUFFERS)
SELECT assignment.step_number, assignment.logical_question_code,
       assignment.assignment_status
FROM calibration.pilot_question_assignment_slot AS assignment
WHERE assignment.pilot_presentation_slot_id = (
  SELECT min(pilot_presentation_slot_id)
  FROM calibration.pilot_question_assignment_slot
);

ROLLBACK;

\echo ROUND3D_QUERY_PLAN_PASS=true
