\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SELECT * FROM audit.v_model_prebuild_coverage;

SELECT source_family_key, observation_row_count, source_family_share,
       share_rank, largest_source_family_share,
       second_largest_source_family_share,
       meaningful_observation_family_count
FROM audit.v_model_prebuild_sensory_concentration
ORDER BY share_rank, source_family_key;

SELECT partition_key, source_family_key, sensory_method,
       future_training_surface_status, declared_feature_count,
       compatible_feature_count, partial_feature_count,
       non_poolable_feature_count, pooling_contract_consistent
FROM evidence.v_model_prebuild_source_partitions
ORDER BY partition_key;

SELECT feature_key, harmonization_status, available_partition_count,
       pooling_allowed_partition_count, missingness_semantics
FROM evidence.v_model_prebuild_feature_availability
ORDER BY feature_key;

SELECT source_family_key, preparation_family, roast_source_label,
       milk_mode, sensory_method, participant_type, language_code,
       observed_cell_count, coffee_identity_count,
       observed_only, no_zero_fill, crossed_eligible_cell_count
FROM audit.v_model_prebuild_context_coverage
ORDER BY source_family_key, preparation_family, roast_source_label, milk_mode;

SELECT * FROM corpus.v_model_prebuild_language_inventory
ORDER BY language_plane;

SELECT question_evidence_key, question_range_target_key,
       supporting_source_families, independent_origin_count,
       user_validation_status, information_gain_status
FROM calibration.v_model_prebuild_question_evidence
ORDER BY question_evidence_key;

SELECT * FROM audit.v_model_prebuild_relationship_delta;
SELECT * FROM audit.run_model_prebuild_readiness_gate()
ORDER BY readiness_key;
SELECT audit.model_prebuild_readiness_state();

ROLLBACK;

\echo ROUND3H_RETRIEVAL_TEST_PASS=true
