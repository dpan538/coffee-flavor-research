\set ON_ERROR_STOP on
\pset pager off

BEGIN;

DO $round3b_query_plan_index_contract$
BEGIN
    IF to_regclass('context.context_source_file_hash_idx') IS NULL
       OR to_regclass('context.raw_context_record_snapshot_source_idx') IS NULL
       OR to_regclass('context.raw_context_record_preparation_idx') IS NULL
       OR to_regclass('context.raw_context_record_roast_idx') IS NULL
       OR to_regclass('context.context_normalization_case_split_idx') IS NULL
       OR to_regclass('context.context_lexical_rule_expression_uq') IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_query_plan_index_contract_ck',
            MESSAGE = 'A required Round 3B source, context, or benchmark index is missing';
    END IF;
    RAISE NOTICE 'ROUND3B_QUERY_PLAN_INDEX_CONTRACT_PASS=true';
END;
$round3b_query_plan_index_contract$;

\echo ROUND3B_QUERY_PLAN=current_preparation_projection
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM context.v_current_user_preparation ORDER BY ordinal_position;

\echo ROUND3B_QUERY_PLAN=current_roast_projection
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM context.v_current_user_roast ORDER BY ordinal_position;

\echo ROUND3B_QUERY_PLAN=lexical_rule_lookup
EXPLAIN (ANALYZE, BUFFERS)
SELECT outcome_status_code, normalized_preparation_family_id,
       normalized_preparation_leaf_id, normalized_roast_category_id
FROM context.context_lexical_rule
WHERE context_domain = 'preparation'
  AND language_tag_code = 'zh-Hans'
  AND normalized_expression = '法压壶';

\echo ROUND3B_QUERY_PLAN=snapshot_preparation_distribution
EXPLAIN (ANALYZE, BUFFERS)
SELECT normalized_preparation_family_id, preparation_status_code, count(*)
FROM context.raw_context_record
WHERE context_dataset_snapshot_id = (
    SELECT context_dataset_snapshot_id
    FROM context.context_dataset_snapshot
    WHERE snapshot_key = 'context.snapshot.round3b_v1'
)
GROUP BY normalized_preparation_family_id, preparation_status_code;

\echo ROUND3B_QUERY_PLAN=held_out_benchmark
EXPLAIN (ANALYZE, BUFFERS)
SELECT selected_case.context_domain, result.evaluation_grade, count(*)
FROM context.context_normalization_case AS selected_case
JOIN context.context_normalization_result AS result
  ON result.context_normalization_case_id =
     selected_case.context_normalization_case_id
WHERE selected_case.context_normalization_benchmark_id = (
    SELECT context_normalization_benchmark_id
    FROM context.context_normalization_benchmark
    WHERE benchmark_key = 'context.benchmark.round3b_v1'
)
  AND selected_case.evaluation_split = 'held_out'
GROUP BY selected_case.context_domain, result.evaluation_grade;

ROLLBACK;

\echo ROUND3B_QUERY_PLAN_PASS=true
