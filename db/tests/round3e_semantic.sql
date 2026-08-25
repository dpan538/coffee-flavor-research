\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3e_semantic_contract$
DECLARE failed_count BIGINT;
BEGIN
  SELECT count(*) INTO failed_count
  FROM audit.run_round3e_validation_queries()
  WHERE passed IS NOT TRUE OR violation_count <> 0;
  IF failed_count <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3e_validation_contract_ck',
      MESSAGE = 'Round 3E validation contract reported violations';
  END IF;

  IF (SELECT count(*) FROM evidence.v_external_snapshot_inventory) <> 4
     OR (SELECT sum(imported_record_count)
         FROM evidence.external_dataset_snapshot) <> 459
     OR (SELECT sum(exclusion_count)
         FROM evidence.external_dataset_snapshot) <> 18
     OR (SELECT count(*) FROM calibration.v_round3e_question_research) <> 18
     OR (SELECT count(*) FROM audit.v_round3e_empirical_coverage) <> 52
     OR EXISTS (
       SELECT 1 FROM audit.round3e_prohibition
       WHERE ranking_model_trained OR adaptive_policy_trained
          OR deep_learning_model_run OR embedding_baseline_run
          OR pgvector_required OR real_human_collection_performed
          OR real_observation_count <> 0 OR product_frontend_modified
     ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3e_semantic_boundary_ck',
      MESSAGE = 'Round 3E source separation, zero-training, or evidence boundary changed';
  END IF;
  RAISE NOTICE 'ROUND3E_SEMANTIC_VALIDATION_PASS=true';
END;
$round3e_semantic_contract$;

SELECT * FROM audit.run_round3e_validation_queries() ORDER BY check_key;
SELECT * FROM evidence.v_external_snapshot_inventory
ORDER BY dataset_snapshot_key;
SELECT logical_question_code, language_code, lifecycle_status,
       information_gain_status
FROM calibration.v_round3e_question_research
ORDER BY logical_question_code, language_code;

ROLLBACK;

\echo ROUND3E_SEMANTIC_TEST_PASS=true

