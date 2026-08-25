\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3h_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3h_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION
            'Round 3H negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3H_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END
$expect_round3h_failure$;

CREATE FUNCTION pg_temp.attempt_round3h_promotion_without_evidence()
RETURNS VOID
LANGUAGE plpgsql
AS $attempt_round3h_promotion_without_evidence$
DECLARE
    selected_membership_id BIGINT;
BEGIN
    SELECT association_range_membership_id INTO selected_membership_id
    FROM corpus.association_range_membership
    WHERE membership_key = 'membership.floral-tea.jasmine';

    INSERT INTO kb.relationship_review_decision (
        review_key, association_range_membership_id, disposition,
        prior_lifecycle, new_lifecycle, supporting_source_families,
        challenging_source_families, decision_reason,
        remaining_uncertainty, review_protocol, reviewed_round
    ) VALUES (
        'negative.round3h.promotion-without-evidence',
        selected_membership_id, 'PROMOTE_SOURCE_LOCAL', 'CANDIDATE',
        'SOURCE_LOCAL_SUPPORTED',
        ARRAY['family.iswaldi-rataconsumers-2026'], ARRAY[]::TEXT[],
        'Negative fixture.', 'Negative fixture.',
        'ROUND3H_NEGATIVE_FIXTURE', '3H'
    );

    UPDATE corpus.association_range_membership
    SET lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
    WHERE association_range_membership_id = selected_membership_id;
END
$attempt_round3h_promotion_without_evidence$;

SELECT pg_temp.expect_round3h_failure(
    'dataset_without_source_family',
    $$INSERT INTO evidence.model_prebuild_source_partition (
        partition_key, source_family_key, dataset_snapshot_key,
        source_registry_path, coffee_identity_availability,
        participant_type, sensory_method, context_fields,
        descriptor_fields, language_fields, sample_count, row_count,
        feature_keys, rights_boundary, grouping_keys,
        future_training_surface_status, compatible_join_group
      ) SELECT
        'partition.round3h.negative-no-family', 'family.missing',
        dataset_snapshot_key, source_registry_path,
        coffee_identity_availability, participant_type, sensory_method,
        context_fields, descriptor_fields, language_fields,
        sample_count, row_count, feature_keys, rights_boundary,
        grouping_keys, future_training_surface_status,
        compatible_join_group
      FROM evidence.model_prebuild_source_partition
      WHERE partition_key = 'partition.round3h.iswaldi'$$,
    '23503', 'model_prebuild_partition_source_family_fk'
);

SELECT pg_temp.expect_round3h_failure(
    'file_with_mismatched_hash',
    $$INSERT INTO evidence.relationship_source_file
      SELECT 'file.negative.round3h.hash', snapshot_key, source_key,
             source_family_key, filename, file_role, locator, license,
             file_size_bytes, declared_sha256, repeat('0', 64), row_count,
             field_count, TRUE, contains_participant_identifiers,
             public_export_decision, local_path
      FROM evidence.relationship_source_file
      WHERE file_key = 'file.iswaldi.table3-derived'$$,
    '23514', 'relationship_source_file_hash_match_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'rights_unknown_raw_export',
    $$INSERT INTO evidence.relationship_source_file
      SELECT 'file.negative.round3h.raw-export', snapshot_key, source_key,
             source_family_key, 'negative-raw.xlsx', 'RAW_EXTERNAL',
             locator, license, file_size_bytes, declared_sha256,
             verified_sha256, row_count, field_count, hash_verified,
             FALSE, 'PUBLIC_AGGREGATE',
             'db/data/round3h/negative-raw.xlsx'
      FROM evidence.relationship_source_file
      WHERE file_key = 'file.iswaldi.table3-derived'$$,
    '23514', 'model_prebuild_raw_export_rights_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'two_mirrors_counted_as_independent',
    $$INSERT INTO evidence.source_family (
        source_family_key, family_name, family_type, canonical_origin_key,
        counts_as_independent, mirror_of_source_family_key,
        independence_basis, admitted, introduced_round
      ) VALUES (
        'family.negative.round3h-mirror', 'Negative Round 3H mirror',
        'OTHER_RESEARCH', 'origin.negative.round3h-mirror', TRUE,
        'family.iswaldi-rataconsumers-2026', 'Negative fixture.', TRUE, '3H'
      )$$,
    '23514', 'source_family_mirror_independence_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'chemistry_only_source_counted_as_sensory_outcome',
    $$UPDATE evidence.model_prebuild_source_profile
      SET chemistry_only = TRUE, counts_as_sensory_outcome = TRUE
      WHERE source_key = 'pmc.condelli-2022'$$,
    '23514', 'model_prebuild_source_profile_semantics_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'preparation_only_metadata_counted_as_milk_sensory',
    $$UPDATE evidence.model_prebuild_source_profile
      SET preparation_only = TRUE, counts_as_milk_sensory = TRUE
      WHERE source_key = 'pmc.heo-2019'$$,
    '23514', 'model_prebuild_source_profile_semantics_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'dictionary_counted_as_sensory_language_validation',
    $$INSERT INTO corpus.model_prebuild_language_source_decision (
        decision_key, candidate_key, language_plane, rights_status,
        observation_status, source_authored, machine_translated,
        artificial_variant, evidence_role, countable_family_gain,
        countable_document_gain, countable_expression_gain,
        decision, limitation
      ) VALUES (
        'language.negative.round3h.dictionary',
        'candidate.negative.round3h.dictionary', 'CONTEMPORARY',
        'CC BY', 'VERIFIED_OBSERVED', TRUE, FALSE, FALSE,
        'DICTIONARY_REFERENCE', 1, 1, 1,
        'Negative fixture.', 'Negative fixture.'
      )$$,
    '23514', 'model_prebuild_language_source_decision_counts_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'survey_without_sensory_variables_counted_as_sensory_source',
    $$UPDATE evidence.model_prebuild_source_profile
      SET survey_without_sensory_variables = TRUE,
          counts_as_sensory_outcome = TRUE
      WHERE source_key = 'pmc.coffee-cuality-2026'$$,
    '23514', 'model_prebuild_source_profile_semantics_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'inferred_context_cell_counted_as_observed',
    $$INSERT INTO audit.model_prebuild_context_cell
      SELECT 'context.negative.round3h.inferred', source_family_key,
             coffee_identity || '/negative-inferred', preparation_family,
             roast_source_label, milk_mode, sensory_method,
             participant_type, language_code, 'INFERRED', FALSE,
             crossed_preparation_roast_eligible, source_row_locator,
             limitation
      FROM audit.model_prebuild_context_cell
      WHERE context_cell_key = 'context.round3h.iswaldi.gayo.light.v60'$$,
    '23514', 'model_prebuild_context_cell_observed_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'zero_filled_context_cell',
    $$INSERT INTO audit.model_prebuild_context_cell
      SELECT 'context.negative.round3h.zero-filled', source_family_key,
             coffee_identity || '/negative-zero', preparation_family,
             roast_source_label, milk_mode, sensory_method,
             participant_type, language_code, evidence_status, TRUE,
             crossed_preparation_roast_eligible, source_row_locator,
             limitation
      FROM audit.model_prebuild_context_cell
      WHERE context_cell_key = 'context.round3h.iswaldi.gayo.light.v60'$$,
    '23514', 'model_prebuild_context_cell_observed_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'artificial_lexical_variant_for_threshold',
    $$INSERT INTO corpus.model_prebuild_language_source_decision (
        decision_key, candidate_key, language_plane, rights_status,
        observation_status, source_authored, machine_translated,
        artificial_variant, evidence_role, countable_family_gain,
        countable_document_gain, countable_expression_gain,
        decision, limitation
      ) VALUES (
        'language.negative.round3h.artificial',
        'candidate.negative.round3h.artificial', 'CONTEMPORARY',
        'CC BY', 'VERIFIED_OBSERVED', TRUE, FALSE, TRUE,
        'OBSERVED_COFFEE_TASTING_LANGUAGE', 1, 1, 1,
        'Negative fixture.', 'Negative fixture.'
      )$$,
    '23514', 'model_prebuild_language_source_decision_counts_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'machine_translated_chinese_counted_as_observed',
    $$INSERT INTO corpus.model_prebuild_language_source_decision (
        decision_key, candidate_key, language_plane, rights_status,
        observation_status, source_authored, machine_translated,
        artificial_variant, evidence_role, countable_family_gain,
        countable_document_gain, countable_expression_gain,
        decision, limitation
      ) VALUES (
        'language.negative.round3h.machine-zh',
        'candidate.negative.round3h.machine-zh', 'ZH_HANS',
        'CC BY', 'VERIFIED_OBSERVED', TRUE, TRUE, FALSE,
        'OBSERVED_COFFEE_TASTING_LANGUAGE', 1, 1, 1,
        'Negative fixture.', 'Negative fixture.'
      )$$,
    '23514', 'model_prebuild_language_source_decision_counts_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'incompatible_rata_cata_values_silently_pooled',
    $$UPDATE evidence.model_prebuild_partition_feature
      SET pooling_allowed = TRUE
      WHERE partition_key = 'partition.round3h.iswaldi'
        AND feature_key = 'feature.descriptor-intensity'$$,
    '23514', 'model_prebuild_partition_feature_semantics_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'missingness_categories_collapsed_without_declaration',
    $$UPDATE evidence.model_prebuild_feature_definition
      SET missingness_semantics = ARRAY[]::TEXT[]
      WHERE feature_key = 'feature.descriptor-intensity'$$,
    '23514', 'model_prebuild_feature_definition_key_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'source_local_partition_joined_to_incompatible_source',
    $$UPDATE evidence.model_prebuild_partition_feature
      SET harmonization_status = 'SEMANTICALLY_COMPATIBLE',
          pooling_allowed = FALSE
      WHERE partition_key = 'partition.round3h.vezzulli'
        AND feature_key = 'feature.descriptor-intensity'$$,
    '23514', 'model_prebuild_partition_feature_semantics_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'same_coffee_across_split_candidates',
    $$UPDATE evidence.model_prebuild_split_candidate
      SET grouping_dimensions = ARRAY['source_family','roast','preparation'],
          prohibited_cross_split_keys = ARRAY['source_family','roast','preparation']
      WHERE split_candidate_key = 'split.round3h.iswaldi'$$,
    '23514', 'model_prebuild_same_coffee_split_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'relationship_promotion_without_independent_evidence',
    $$SELECT pg_temp.attempt_round3h_promotion_without_evidence()$$,
    '23514', 'round3g_membership_promotion_evidence_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'canonical_concept_created_to_increase_coverage',
    $$INSERT INTO kb.concept (
        concept_key, concept_type_code, lifecycle_status_code,
        provenance_scope_code, description
      ) VALUES (
        'negative.round3h.coverage.concept', 'sensory_attribute',
        'candidate', 'project_authored', 'Negative fixture.'
      )$$,
    '23514', 'round3f_canonical_ontology_frozen_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'model_run_created_from_prebuild_dataset',
    $$INSERT INTO ml.model_run (
        model_run_key, model_version_id, model_run_status_code,
        input_dataset_id, input_corpus_id, started_at, completed_at,
        random_seed, run_configuration, result_metadata
      ) SELECT
        'negative.round3h.model-run', model_version_id,
        model_run_status_code, input_dataset_id, input_corpus_id,
        started_at, completed_at, random_seed,
        '{"round":"3H","prebuild":true}'::JSONB, result_metadata
      FROM ml.model_run ORDER BY model_run_id LIMIT 1$$,
    '23514', 'model_prebuild_model_run_prohibited_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'embedding_generated',
    $$INSERT INTO ml.model_version (
        model_version_key, model_id, version_label,
        artifact_locator, configuration, created_at
      ) SELECT
        'negative.round3h.embedding', model_id,
        'negative-round3h-embedding', 'negative://embedding',
        '{"embeddings":true}'::JSONB, CURRENT_TIMESTAMP
      FROM ml.model_version ORDER BY model_version_id LIMIT 1$$,
    '23514', 'model_prebuild_embedding_generation_prohibited_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'expected_state_threshold_reduced_without_decision',
    $$UPDATE audit.model_prebuild_checkpoint
      SET threshold_revision_count = 1
      WHERE checkpoint_key = 'checkpoint.round3h.model-prebuild'$$,
    '23514', 'model_prebuild_checkpoint_contract_ck'
);

SELECT pg_temp.expect_round3h_failure(
    'readiness_true_while_mandatory_gate_fails',
    $$UPDATE audit.model_prebuild_readiness_assertion
      SET model_prebuild_data_ready = TRUE,
          readiness_state = 'MODEL_PREBUILD_READY'
      WHERE assertion_key = 'assertion.round3h.final'$$,
    '23514', 'model_prebuild_readiness_hard_gate_ck'
);

ROLLBACK;

\echo ROUND3H_NEGATIVE_TEST_COUNT=22
\echo ROUND3H_NEGATIVE_TEST_PASS=true
