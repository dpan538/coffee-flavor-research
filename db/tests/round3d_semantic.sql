\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3d_semantic_contract$
DECLARE failed_count BIGINT;
BEGIN
  SELECT count(*) INTO failed_count
  FROM audit.run_round3d_validation_queries()
  WHERE passed IS NOT TRUE OR violation_count <> 0;
  IF failed_count <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3d_validation_contract_ck',
      MESSAGE = 'Round 3D validation contract reported violations';
  END IF;
  IF (SELECT count(*) FROM calibration.v_round3d_pilot_inventory) <> 1
     OR EXISTS (
       SELECT 1 FROM calibration.v_round3d_pilot_inventory
       WHERE coffee_lot_count <> 2 OR roast_batch_count <> 14
          OR preparation_condition_count <> 7 OR beverage_sample_count <> 132
          OR session_slot_count <> 192 OR presentation_slot_count <> 1512
          OR question_assignment_slot_count <> 3600
          OR dry_run_fixture_count <> 5 OR real_observation_count <> 0
          OR NOT is_frozen
     )
     OR EXISTS (
       SELECT 1 FROM calibration.v_round3d_analysis_status
       WHERE estimability_status <> 'NOT_ESTIMABLE'
          OR real_observation_count <> 0 OR dry_run_fixture_count <> 5
          OR deep_learning_model_run OR embedding_baseline_run
          OR pgvector_required
     )
     OR EXISTS (SELECT 1 FROM calibration.model_candidate_output) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3d_semantic_boundary_ck',
      MESSAGE = 'Round 3D matrix, fixture, zero-data, or abstention boundary changed';
  END IF;
  RAISE NOTICE 'ROUND3D_SEMANTIC_VALIDATION_PASS=true';
END;
$round3d_semantic_contract$;

SELECT * FROM audit.run_round3d_validation_queries() ORDER BY check_key;
SELECT * FROM calibration.v_round3d_pilot_inventory;
SELECT analysis_run_key, estimability_status, release_version,
       real_observation_count, dry_run_fixture_count, analysis_status,
       deep_learning_model_run, embedding_baseline_run, pgvector_required
FROM calibration.v_round3d_analysis_status;

ROLLBACK;

\echo ROUND3D_SEMANTIC_TEST_PASS=true
