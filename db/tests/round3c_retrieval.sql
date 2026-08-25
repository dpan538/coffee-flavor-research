\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SELECT logical_question_code, language_tag_code, prompt_text,
       option_count, interaction_position_code
FROM calibration.v_question_bank
ORDER BY logical_question_code, language_tag_code;

SELECT design_scale_code, coffee_lot_count, roast_batch_count,
       preparation_family_count, roast_category_count,
       condition_cell_count, beverage_sample_count, includes_milk_mode,
       calibration_power_status
FROM calibration.study_design_target
ORDER BY study_design_target_id;

DO $round3c_retrieval_contract$
BEGIN
  IF (SELECT beverage_sample_count FROM calibration.study_design_target
      WHERE design_scale_code = 'minimum') <> 132
     OR (SELECT condition_cell_count FROM calibration.study_design_target
         WHERE design_scale_code = 'minimum') <> 66
     OR (SELECT count(*) FROM calibration.question_option) <> 36
     OR EXISTS (SELECT 1 FROM calibration.assessor)
     OR EXISTS (SELECT 1 FROM calibration.sensory_observation) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3c_retrieval_contract_ck',
      MESSAGE = 'Round 3C frozen design or no-observation boundary changed';
  END IF;
  RAISE NOTICE 'ROUND3C_RETRIEVAL_PASS=true';
END;
$round3c_retrieval_contract$;

ROLLBACK;

\echo ROUND3C_RETRIEVAL_TEST_PASS=true
