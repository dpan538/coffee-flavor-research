\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3b_semantic_contract$
DECLARE
    failed_check_count BIGINT;
BEGIN
    SELECT count(*) INTO failed_check_count
    FROM audit.run_round3b_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0;

    IF failed_check_count <> 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_validation_contract_ck',
            MESSAGE = 'Round 3B validation contract reported one or more violations';
    END IF;

    IF (SELECT count(*) FROM context.v_current_user_preparation) <> 8
       OR (SELECT count(*) FROM context.v_current_user_roast) <> 7
       OR (SELECT count(DISTINCT ordinal_position)
           FROM context.v_current_user_roast) <> 7
       OR EXISTS (
           SELECT 1 FROM context.v_current_user_roast
           WHERE scale_semantics <> 'ordinal_not_interval'
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_interaction_projection_ck',
            MESSAGE = 'Current C0/C1 projections differ from the frozen product contract';
    END IF;

    IF (SELECT metric_value FROM context.v_context_coverage
        WHERE metric_key = 'RECOMMENDED_USER_ROAST_LEVEL_COUNT') <> 5
       OR (SELECT count(*) FROM context.roast_category AS category
           JOIN context.roast_scheme AS scheme
             ON scheme.roast_scheme_id = category.roast_scheme_id
           WHERE scheme.roast_scheme_key =
                 'roast.scheme.project_v0_five_level') <> 5 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_round3a_history_ck',
            MESSAGE = 'Round 3A historical five-level receipt was not preserved';
    END IF;

    IF (SELECT metric_value FROM context.v_round3b_context_coverage
        WHERE metric_key = 'CONTEXT_DATA_SOURCE_COUNT') <> 3
       OR (SELECT metric_value FROM context.v_round3b_context_coverage
           WHERE metric_key = 'RIGHTS_CLEARED_IMPORTED_SOURCE_COUNT') <> 2
       OR (SELECT metric_value FROM context.v_round3b_context_coverage
           WHERE metric_key = 'CONTEXT_DATASET_ROW_COUNT') <> 4817 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_context_snapshot_receipt_ck',
            MESSAGE = 'Round 3B governed context snapshot receipt changed';
    END IF;

    IF (SELECT metric_value FROM context.v_held_out_normalization_metrics
        WHERE metric_key = 'C0_HELD_OUT_SIZE') <> 9
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C0_FAMILY_COVERAGE') <> 1
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C0_LEAF_COVERAGE') <> 0.8889
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C0_GROSS_ERROR_RATE') <> 0
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C1_HELD_OUT_SIZE') <> 8
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C1_EXACT_CATEGORY_AGREEMENT') <> 1
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C1_ADJACENT_CATEGORY_AGREEMENT') <> 1
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C1_NORMALIZATION_COVERAGE') <> 0.625
       OR (SELECT metric_value FROM context.v_held_out_normalization_metrics
           WHERE metric_key = 'C1_UNRESOLVED_RATE') <> 0.375 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_normalization_receipt_ck',
            MESSAGE = 'Frozen held-out label-normalization metrics changed';
    END IF;

    IF EXISTS (
        SELECT 1 FROM context.v_context_signal_sufficiency
        WHERE preparation_signal_data_sufficient
           OR roast_signal_data_sufficient
           OR preparation_roast_interaction_data_sufficient
           OR milk_mode_data_sufficient
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3b_signal_abstention_ck',
            MESSAGE = 'Insufficient context/sensory cells cannot become empirical signal claims';
    END IF;

    RAISE NOTICE 'ROUND3B_SEMANTIC_VALIDATION_PASS=true';
END;
$round3b_semantic_contract$;

SELECT * FROM audit.run_round3b_validation_queries() ORDER BY check_key;
SELECT * FROM context.v_round3b_context_coverage ORDER BY metric_key;
SELECT * FROM context.v_held_out_normalization_metrics ORDER BY metric_key;
SELECT * FROM context.v_context_signal_sufficiency;

ROLLBACK;

\echo ROUND3B_SEMANTIC_TEST_PASS=true
