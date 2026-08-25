\set ON_ERROR_STOP on
\pset pager off

BEGIN;

DO $round3c_query_plan_index_contract$
BEGIN
  IF to_regclass('calibration.roast_batch_category_idx') IS NULL
     OR to_regclass('calibration.preparation_condition_family_idx') IS NULL
     OR to_regclass('calibration.beverage_sample_condition_idx') IS NULL
     OR to_regclass('calibration.presentation_sample_idx') IS NULL
     OR to_regclass('calibration.question_assignment_policy_idx') IS NULL
     OR to_regclass('calibration.descriptor_response_concept_idx') IS NULL
     OR to_regclass('calibration.candidate_judgment_concept_idx') IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3c_query_plan_index_contract_ck',
      MESSAGE = 'A required Round 3C index is missing';
  END IF;
END;
$round3c_query_plan_index_contract$;

EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM calibration.v_question_bank
WHERE language_tag_code = 'zh-Hans'
ORDER BY logical_question_code;

EXPLAIN (ANALYZE, BUFFERS)
SELECT sample.beverage_sample_key, roast.roast_batch_key,
       prep.preparation_condition_key
FROM calibration.beverage_sample AS sample
JOIN calibration.roast_batch AS roast ON roast.roast_batch_id = sample.roast_batch_id
JOIN calibration.preparation_condition AS prep
  ON prep.preparation_condition_id = sample.preparation_condition_id
WHERE sample.study_id = (SELECT study_id FROM calibration.study
                         WHERE study_key = 'study.context_calibration_v0.minimum');

ROLLBACK;

\echo ROUND3C_QUERY_PLAN_PASS=true
