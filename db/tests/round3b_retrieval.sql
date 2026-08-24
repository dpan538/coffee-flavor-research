\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

\echo ROUND3B_CURRENT_PREPARATION_CHOICES
SELECT preparation_concept_key, ordinal_position, candidate_user_label_en,
       candidate_user_label_zh_hans
FROM context.v_current_user_preparation
ORDER BY ordinal_position;

\echo ROUND3B_CURRENT_ROAST_CHOICES
SELECT roast_category_key, interaction_code, preferred_label,
       ordinal_position, scale_semantics
FROM context.v_current_user_roast
ORDER BY ordinal_position;

\echo ROUND3B_SOURCE_INVENTORY
SELECT context_source_review_key, doi, version_label, license_spdx,
       context_acquisition_status_code, inspected_row_count,
       frozen_file_count
FROM context.v_context_source_inventory
ORDER BY context_source_review_key;

\echo ROUND3B_HELD_OUT_FAILURE_QUEUE
SELECT selected_case.context_normalization_case_key,
       selected_case.raw_expression, selected_case.context_domain,
       result.evaluation_grade, result.mapping_grade, result.gross_error
FROM context.context_normalization_case AS selected_case
JOIN context.context_normalization_result AS result
  ON result.context_normalization_case_id =
     selected_case.context_normalization_case_id
WHERE selected_case.evaluation_split = 'held_out'
  AND (result.predicted_status_code = 'reported_unresolved'
       OR result.evaluation_grade IN ('0', '1', 'incorrect'))
ORDER BY selected_case.context_domain,
         selected_case.context_normalization_case_key;

DO $round3b_retrieval_contract$
BEGIN
    IF (SELECT count(*) FROM context.v_context_source_inventory) <> 3
       OR (SELECT count(*) FROM context.context_source_file) <> 6
       OR (SELECT count(*) FROM context.context_normalization_case
           WHERE evaluation_split = 'held_out') <> 17
       OR (SELECT count(*) FROM context.context_normalization_result AS result
           JOIN context.context_normalization_case AS selected_case
             ON selected_case.context_normalization_case_id =
                result.context_normalization_case_id
           WHERE selected_case.evaluation_split = 'held_out'
             AND result.gross_error) <> 0
       OR NOT EXISTS (
           SELECT 1 FROM context.context_lexical_rule
           WHERE context_domain = 'roast'
             AND normalized_expression = 'espresso roast'
             AND outcome_status_code = 'reported_unresolved'
             AND normalized_roast_category_id IS NULL
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_retrieval_contract_ck',
            MESSAGE = 'Round 3B source, benchmark, or abstention retrieval changed';
    END IF;
    RAISE NOTICE 'ROUND3B_RETRIEVAL_PASS=true';
END;
$round3b_retrieval_contract$;

ROLLBACK;

\echo ROUND3B_RETRIEVAL_TEST_PASS=true
