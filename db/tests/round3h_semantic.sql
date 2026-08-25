\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3h_semantic_contract$
DECLARE
    coverage audit.v_model_prebuild_coverage%ROWTYPE;
    failed_validation_count BIGINT;
    failed_hard_gate_count BIGINT;
    largest_share NUMERIC;
    second_share NUMERIC;
    meaningful_family_count BIGINT;
BEGIN
    SELECT count(*) INTO failed_validation_count
    FROM audit.run_round3h_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0;

    IF failed_validation_count <> 0 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_validation_contract_ck',
            MESSAGE = 'Round 3H validation contract reported violations';
    END IF;

    SELECT count(*) INTO failed_hard_gate_count
    FROM audit.run_model_prebuild_readiness_gate()
    WHERE hard_gate AND NOT passed;

    IF failed_hard_gate_count <> 4
       OR audit.model_prebuild_readiness_state()
          <> 'COMPLETE_WITH_DATA_COVERAGE_GAP' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_readiness_state_ck',
            MESSAGE = 'Round 3H must retain exactly four hard language gaps';
    END IF;

    SELECT * INTO coverage FROM audit.v_model_prebuild_coverage;
    IF coverage.coffee_sensory_source_family_count <> 9
       OR coverage.sensory_method_family_count <> 4
       OR coverage.source_local_sensory_observation_row_count <> 4344
       OR coverage.source_local_sensory_sample_count <> 230
       OR coverage.source_local_participant_or_panel_count <> 520
       OR coverage.sensory_outcome_preparation_family_count <> 8
       OR coverage.sensory_outcome_roast_category_or_scheme_count <> 9
       OR coverage.crossed_preparation_roast_observed_cell_count <> 118
       OR coverage.milk_sensory_outcome_source_family_count <> 2
       OR coverage.ordinary_user_sensory_source_family_count <> 5
       OR coverage.reference_panel_source_family_count <> 4
       OR coverage.empirical_coverage_cell_count <> 181
       OR coverage.new_context_cell_count <> 129 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_coverage_inventory_ck',
            MESSAGE = 'Round 3H coverage inventory changed';
    END IF;

    IF (SELECT count(*) FROM evidence.model_prebuild_feature_definition) <> 20
       OR (SELECT count(*) FROM evidence.model_prebuild_source_partition) <> 12
       OR (SELECT count(*) FROM evidence.model_prebuild_partition_feature) <> 108
       OR (SELECT count(*) FROM evidence.model_prebuild_feature_definition
           WHERE harmonization_status = 'SEMANTICALLY_COMPATIBLE') <> 7
       OR (SELECT count(*) FROM evidence.model_prebuild_feature_definition
           WHERE harmonization_status = 'PARTIALLY_COMPATIBLE') <> 7
       OR (SELECT count(*) FROM evidence.model_prebuild_feature_definition
           WHERE harmonization_status = 'NOT_COMPATIBLE') <> 3
       OR (SELECT count(*) FROM evidence.model_prebuild_feature_definition
           WHERE harmonization_status = 'SOURCE_LOCAL_ONLY') <> 3 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_federated_feature_inventory_ck',
            MESSAGE = 'Round 3H feature or partition inventory changed';
    END IF;

    IF (SELECT count(*) FROM evidence.relationship_evidence_claim) <> 96
       OR (SELECT count(*) FROM evidence.relationship_evidence_claim
           WHERE evidence_direction = 'SUPPORTS') <> 47
       OR (SELECT count(*) FROM evidence.relationship_evidence_claim
           WHERE evidence_direction = 'CHALLENGES') <> 18
       OR (SELECT count(*) FROM evidence.relationship_evidence_claim
           WHERE evidence_direction = 'MIXED') <> 14
       OR (SELECT count(*) FROM evidence.relationship_evidence_claim
           WHERE evidence_direction = 'INSUFFICIENT') <> 17
       OR (SELECT count(*) FROM corpus.association_range_membership
           WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED') <> 6
       OR (SELECT count(*) FROM corpus.association_range_membership
           WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED') <> 4 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_relationship_inventory_ck',
            MESSAGE = 'Round 3H relationship evidence inventory changed';
    END IF;

    IF (SELECT count(*) FROM calibration.model_prebuild_question_evidence) <> 12
       OR EXISTS (
           SELECT 1 FROM calibration.model_prebuild_question_evidence
           WHERE user_validation_status <> 'NOT_USER_VALIDATED'
              OR information_gain_status <> 'NOT_ESTIMABLE'
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_question_nonvalidation_ck',
            MESSAGE = 'Round 3H question research boundary changed';
    END IF;

    IF (SELECT count(*)
        FROM corpus.model_prebuild_language_source_decision) <> 14
       OR EXISTS (
           SELECT 1 FROM corpus.model_prebuild_language_source_decision
           WHERE countable_family_gain <> 0
              OR countable_document_gain <> 0
              OR countable_expression_gain <> 0
              OR machine_translated OR artificial_variant
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_language_no_gain_ck',
            MESSAGE = 'Round 3H language no-gain result changed';
    END IF;

    SELECT max(largest_source_family_share),
           max(second_largest_source_family_share),
           max(meaningful_observation_family_count)
    INTO largest_share, second_share, meaningful_family_count
    FROM audit.v_model_prebuild_sensory_concentration;

    IF largest_share <= 0.70 OR largest_share >= 0.80
       OR second_share <= 0.05 OR second_share >= 0.10
       OR meaningful_family_count <> 9 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_sensory_concentration_ck',
            MESSAGE = 'Round 3H concentration report changed';
    END IF;

    IF EXISTS (
        SELECT 1 FROM audit.model_prebuild_readiness_assertion
        WHERE model_prebuild_data_ready
           OR readiness_state <> 'COMPLETE_WITH_DATA_COVERAGE_GAP'
    ) OR EXISTS (
        SELECT 1 FROM audit.model_prebuild_execution_guard
        WHERE ranking_model_run_count <> 0
           OR adaptive_policy_run_count <> 0
           OR deep_learning_run_count <> 0
           OR embedding_run_count <> 0
           OR real_human_collection_performed
           OR real_observation_count <> 0
           OR product_frontend_modified
           OR canonical_concept_change_count <> 0
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_prebuild_only_boundary_ck',
            MESSAGE = 'Round 3H prebuild-only boundary changed';
    END IF;

    RAISE NOTICE 'ROUND3H_SEMANTIC_VALIDATION_PASS=true';
END
$round3h_semantic_contract$;

SELECT * FROM audit.run_round3h_validation_queries() ORDER BY check_key;
SELECT * FROM audit.run_model_prebuild_readiness_gate() ORDER BY readiness_key;
SELECT * FROM audit.v_model_prebuild_relationship_delta;

ROLLBACK;

\echo ROUND3H_SEMANTIC_TEST_PASS=true
