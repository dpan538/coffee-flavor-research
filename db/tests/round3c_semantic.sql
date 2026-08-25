\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3c_semantic_contract$
DECLARE failed_count BIGINT;
BEGIN
  SELECT count(*) INTO failed_count
  FROM audit.run_round3c_validation_queries()
  WHERE passed IS NOT TRUE OR violation_count <> 0;
  IF failed_count <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3c_validation_contract_ck',
      MESSAGE = 'Round 3C validation contract reported violations';
  END IF;
  IF (SELECT count(*) FROM calibration.v_question_bank) <> 12
     OR (SELECT count(DISTINCT logical_question_code)
         FROM calibration.v_question_bank) <> 6
     OR EXISTS (
       SELECT 1 FROM calibration.v_study_readiness
       WHERE real_collection_permitted OR empirical_observation_count <> 0
     )
     OR (SELECT estimability_status
         FROM calibration.v_calibration_observation_inventory
         WHERE study_key = 'study.context_calibration_v0.minimum') <> 'NOT_ESTIMABLE' THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3c_semantic_boundary_ck',
      MESSAGE = 'Round 3C question, ethics, zero-data, or estimability boundary changed';
  END IF;
  RAISE NOTICE 'ROUND3C_SEMANTIC_VALIDATION_PASS=true';
END;
$round3c_semantic_contract$;

SELECT * FROM audit.run_round3c_validation_queries() ORDER BY check_key;
SELECT * FROM calibration.v_study_readiness;
SELECT * FROM calibration.v_calibration_observation_inventory;

ROLLBACK;

\echo ROUND3C_SEMANTIC_TEST_PASS=true
