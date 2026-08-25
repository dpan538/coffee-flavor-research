\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SELECT dataset_snapshot_key, source_key, source_version,
       declared_row_count, declared_field_count,
       imported_record_count, exclusion_count,
       source_file_count, matched_file_hash_count,
       external_observation_count, external_document_count
FROM evidence.v_external_snapshot_inventory
ORDER BY dataset_snapshot_key;

SELECT source, c0_preparation, c1_roast, black_milk,
       sensory_method, participant_type, language,
       sum(observed_record_count) AS observed_record_count
FROM audit.v_round3e_empirical_coverage
GROUP BY source, c0_preparation, c1_roast, black_milk,
         sensory_method, participant_type, language
ORDER BY source, c0_preparation, c1_roast, black_milk;

SELECT normalized_expression, language_code, count(*) AS occurrence_count
FROM corpus.external_expression_occurrence
GROUP BY normalized_expression, language_code
ORDER BY occurrence_count DESC, normalized_expression, language_code
LIMIT 30;

SELECT logical_question_code, language_code, candidate_region,
       lifecycle_status, prompt_text, answer_options,
       information_gain_status
FROM calibration.v_round3e_question_research
ORDER BY logical_question_code, language_code;

ROLLBACK;

\echo ROUND3E_RETRIEVAL_TEST_PASS=true

