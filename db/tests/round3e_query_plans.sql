\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3e_index_contract$
BEGIN
  IF to_regclass('evidence.external_observation_snapshot_type_idx') IS NULL
     OR to_regclass('corpus.external_document_context_idx') IS NULL
     OR to_regclass('corpus.external_expression_normalized_idx') IS NULL
     OR to_regclass('calibration.question_research_candidate_region_idx') IS NULL
     OR to_regclass('audit.empirical_coverage_source_context_idx') IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '42P01',
      CONSTRAINT = 'round3e_index_contract_ck',
      MESSAGE = 'Round 3E query index contract is incomplete';
  END IF;
END;
$round3e_index_contract$;

SET LOCAL enable_seqscan = off;

EXPLAIN (COSTS OFF)
SELECT source_row_identity, record_type
FROM evidence.external_observation
WHERE dataset_snapshot_key = 'mendeley.ftnir-specialty-coffee.v4.selected'
  AND record_type = 'sensory_score_replicate'
ORDER BY external_observation_id;

EXPLAIN (COSTS OFF)
SELECT expression_occurrence_key, raw_source_phrase
FROM corpus.external_expression_occurrence
WHERE normalized_expression = 'espresso'
  AND language_code = 'en';

EXPLAIN (COSTS OFF)
SELECT logical_question_code, prompt_text
FROM calibration.question_research_candidate
WHERE candidate_region = 'acidity'
ORDER BY logical_question_code, language_code;

EXPLAIN (COSTS OFF)
SELECT coffee_identity, observed_record_count
FROM audit.empirical_coverage_cell
WHERE source_key = 'dryad.cotter-black-coffee.v4'
  AND c0_preparation = 'filter_percolation';

ROLLBACK;

\echo ROUND3E_QUERY_PLAN_TEST_PASS=true
