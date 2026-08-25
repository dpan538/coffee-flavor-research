\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3e_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3e_failure$
DECLARE actual_state TEXT; actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3E negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                                actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3E_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
          test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3e_failure$;

SELECT pg_temp.expect_round3e_failure(
  'duplicate_external_snapshot_key',
  $$INSERT INTO evidence.external_dataset_snapshot (
      dataset_snapshot_key, dataset_id, source_version, file_hashes,
      declared_row_count, verified_row_count, declared_field_count,
      verified_field_count, imported_record_count, exclusion_count,
      import_version, import_code_sha, license_expression, rights_decision,
      privacy_decision, public_release_eligible, created_on
    ) SELECT snapshot.dataset_snapshot_key, dataset.dataset_id, 'negative',
             '{"negative":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'::JSONB,
             1, 1, 1, 1, 1, 0, 'negative', repeat('a', 40), 'CC0-1.0',
             'IMPORT_RAW_AND_DERIVED', 'PASS', TRUE, DATE '2026-08-25'
      FROM evidence.external_dataset_snapshot AS snapshot
      CROSS JOIN LATERAL (
        SELECT dataset_id FROM evidence.dataset
        WHERE dataset_id NOT IN (
          SELECT dataset_id FROM evidence.external_dataset_snapshot
        ) ORDER BY dataset_id LIMIT 1
      ) AS dataset LIMIT 1$$,
  '23505', 'external_dataset_snapshot_pk'
);

SELECT pg_temp.expect_round3e_failure(
  'mismatched_file_hash',
  $$UPDATE evidence.external_source_file
    SET observed_sha256 = repeat('0', 64)
    WHERE source_file_path =
      'mendeley_ftnir_v4/SensoryQuality_RoastedCoffee.xlsx'$$,
  '23514', 'external_source_file_hash_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'wrong_declared_row_count',
  $$UPDATE evidence.external_dataset_snapshot
    SET verified_row_count = declared_row_count - 1
    WHERE dataset_snapshot_key =
      'mendeley.ftnir-specialty-coffee.v4.selected'$$,
  '23514', 'external_dataset_snapshot_dimensions_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'missing_license_decision',
  $$UPDATE evidence.external_dataset_snapshot
    SET license_expression = NULL
    WHERE dataset_snapshot_key =
      'mendeley.ftnir-specialty-coffee.v4.selected'$$,
  '23514', 'external_dataset_snapshot_text_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'public_export_of_blocked_raw_text',
  $$WITH blocked AS (
      UPDATE evidence.external_dataset_snapshot
      SET public_release_eligible = FALSE
      WHERE dataset_snapshot_key =
        'usda.fdc-coffee-search.fndds-2021-2023.20260825'
      RETURNING dataset_snapshot_key
    )
    UPDATE evidence.external_source_file AS file
    SET raw_public_export_allowed = TRUE
    FROM blocked
    WHERE file.dataset_snapshot_key = blocked.dataset_snapshot_key$$,
  '23514', 'external_source_file_public_export_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'direct_participant_identifier',
  $$INSERT INTO evidence.external_observation (
      dataset_snapshot_key, source_file_path, source_row_identity,
      record_type, raw_value, parsed_value, normalized_value,
      normalization_rule, exclusion_reason
    ) VALUES (
      'mendeley.coffee-taste-sensitivity.v1',
      'mendeley_taste_sensitivity_v1/Coffee_sensory_information_data.xlsx',
      'raw data!negative-email', 'negative',
      '{"email":"participant@example.org"}', '{}', '{}',
      'identity; negative fixture', NULL
    )$$,
  '23514', 'external_observation_raw_preserved_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'silent_unit_conversion',
  $$INSERT INTO evidence.external_field_dictionary (
      dataset_snapshot_key, source_file_path, source_local_column_name,
      project_field_key, source_local_unit, normalization_rule,
      unit_conversion_applied
    ) VALUES (
      'mendeley.ftnir-specialty-coffee.v4.selected',
      'mendeley_ftnir_v4/SensoryQuality_RoastedCoffee.xlsx',
      'negative converted score', 'negative_converted_score',
      'source-local points', 'identity_no_unit_conversion', TRUE
    )$$,
  '23514', 'external_field_dictionary_no_silent_conversion_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'source_local_value_overwritten',
  $$INSERT INTO evidence.external_observation (
      dataset_snapshot_key, source_file_path, source_row_identity,
      record_type, raw_value, parsed_value, normalized_value,
      normalization_rule, raw_value_preserved
    ) VALUES (
      'mendeley.ftnir-specialty-coffee.v4.selected',
      'mendeley_ftnir_v4/SensoryQuality_RoastedCoffee.xlsx',
      'Cup quality_RoastedCoffee!negative-overwrite', 'negative',
      '{}', '{}', '{"score":99}', 'negative overwrite fixture', FALSE
    )$$,
  '23514', 'external_observation_raw_preserved_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'external_observation_in_canonical_ontology',
  $$INSERT INTO evidence.concept_support (
      concept_support_key, concept_id, dataset_id, locator, notes,
      concept_support_role_code
    ) SELECT 'negative.round3e.external.canonical', concept.concept_id,
             snapshot.dataset_id, 'negative fixture', NULL,
             'empirical_observation'
      FROM kb.concept AS concept
      CROSS JOIN evidence.external_dataset_snapshot AS snapshot
      ORDER BY concept.concept_id, snapshot.dataset_id LIMIT 1$$,
  '23514', 'concept_support_external_observation_boundary_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'recurrent_term_automatic_promotion',
  $$WITH expression AS (
      INSERT INTO kb.lexical_expression (
        expression_key, language_tag_code, expression_text,
        lifecycle_status_code
      ) VALUES (
        'negative.round3e.expression.espresso', 'en', 'espresso', 'candidate'
      ) RETURNING expression_id
    )
    INSERT INTO kb.lexicalization (
      lexicalization_key, expression_id, concept_id, mapping_type_code,
      lifecycle_status_code, provenance_scope_code
    ) SELECT 'negative.round3e.lexicalization.espresso',
             expression.expression_id, concept.concept_id,
             'approved_variant', 'candidate', 'external'
      FROM expression
      CROSS JOIN LATERAL (
        SELECT concept_id FROM kb.concept ORDER BY concept_id LIMIT 1
      ) AS concept$$,
  '23514', 'lexicalization_round3e_candidate_approval_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'candidate_question_user_validated_without_evidence',
  $$INSERT INTO calibration.question_research_candidate (
      question_version_key, logical_question_code, language_code,
      lifecycle_status, target_distinction, eligible_c0, eligible_c1,
      candidate_region, prompt_text, answer_options, sensory_modality,
      evidence, consumer_familiarity_assumptions, translation_notes,
      ambiguity, expected_information_role, unresolved_concerns,
      information_gain_status, ordinary_user_validation_evidence
    ) SELECT 'negative.round3e.question.active',
             'negative_without_evidence', 'en',
             'ACTIVE_FOR_CALIBRATION', target_distinction,
             eligible_c0, eligible_c1, candidate_region, prompt_text,
             answer_options, sensory_modality, evidence,
             consumer_familiarity_assumptions, translation_notes,
             ambiguity, expected_information_role, unresolved_concerns,
             'NOT_ESTIMABLE', NULL
      FROM calibration.question_research_candidate
      ORDER BY question_version_key LIMIT 1$$,
  '23514', 'question_research_user_validation_evidence_ck'
);

SELECT pg_temp.expect_round3e_failure(
  'model_output_despite_training_prohibition',
  $$INSERT INTO ml.model_run (
      model_run_key, model_version_id, model_run_status_code,
      input_dataset_id, started_at, run_configuration, result_metadata
    ) SELECT 'negative.round3e.prohibited_model_run',
             version.model_version_id, 'running', snapshot.dataset_id,
             TIMESTAMPTZ '2026-08-25 00:00:00+00',
             '{"round":"3E"}', '{"candidate_output":true}'
      FROM ml.model_version AS version
      CROSS JOIN evidence.external_dataset_snapshot AS snapshot
      ORDER BY version.model_version_id, snapshot.dataset_id LIMIT 1$$,
  '23514', 'round3e_model_run_prohibited_ck'
);

ROLLBACK;

\echo ROUND3E_NEGATIVE_TEST_PASS=true
