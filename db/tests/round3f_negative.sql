\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3f_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3f_failure$
DECLARE actual_state TEXT; actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3F negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                                actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3F_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
          test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3f_failure$;

SELECT pg_temp.expect_round3f_failure(
  'recurrent_expression_automatic_promotion',
  $$WITH expression AS (
      INSERT INTO kb.lexical_expression (
        expression_key, language_tag_code, expression_text,
        lifecycle_status_code
      ) VALUES (
        'negative.round3f.expression.espresso', 'en',
        'espresso', 'candidate'
      ) RETURNING expression_id
    )
    INSERT INTO kb.lexicalization (
      lexicalization_key, expression_id, concept_id,
      mapping_type_code, lifecycle_status_code, provenance_scope_code
    ) SELECT 'negative.round3f.lexicalization.espresso',
             expression.expression_id, concept.concept_id,
             'approved_variant', 'candidate', 'external'
      FROM expression
      CROSS JOIN LATERAL (
        SELECT concept_id FROM kb.concept ORDER BY concept_id LIMIT 1
      ) AS concept$$,
  '23514', 'lexicalization_round3e_candidate_approval_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'range_copresence_to_synonym',
  $$SELECT audit.reject_forbidden_round3f_inference(
      'RANGE_COMEMBERSHIP', 'SYNONYM'
    )$$,
  '23514', 'round3f_range_not_synonym_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'cooccurrence_to_sensory_neighbour',
  $$SELECT audit.reject_forbidden_round3f_inference(
      'COOCCURRENCE', 'SENSORY_NEIGHBOUR'
    )$$,
  '23514', 'round3f_cooccurrence_not_neighbour_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'exclusive_range_membership',
  $$UPDATE corpus.association_range_membership
    SET is_exclusive = TRUE
    WHERE membership_key = 'membership.fruit.berry'$$,
  '23514', 'association_range_membership_nonprobability_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'unresolved_candidate_forced_to_concept',
  $$INSERT INTO corpus.association_range_membership (
      membership_key, association_range_id, lexical_mapping_key,
      concept_id, membership_role, lifecycle_status, evidence_basis,
      evidence_key, provenance_path
    ) SELECT 'negative.round3f.forced-concept',
             range.association_range_id, candidate.mapping_key,
             concept.concept_id, 'AMBIGUOUS', 'CANDIDATE',
             'EXPLICIT_CURATED_REVIEW_DECISION',
             'negative fixture', 'negative fixture'
      FROM corpus.association_range AS range
      CROSS JOIN LATERAL (
        SELECT mapping_key FROM corpus.lexical_mapping_candidate
        ORDER BY mapping_key LIMIT 1
      ) AS candidate
      CROSS JOIN LATERAL (
        SELECT concept_id FROM kb.concept ORDER BY concept_id LIMIT 1
      ) AS concept
      ORDER BY range.association_range_id LIMIT 1$$,
  '23514', 'association_range_membership_subject_xor_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'source_local_range_mislabeled_cross_source',
  $$INSERT INTO corpus.association_range (
      range_key, display_name, research_definition, lifecycle_status,
      support_scope, evidence_key, independent_evidence_family_count
    ) VALUES (
      'negative-source-local-cross-source', 'Negative fixture',
      'Negative lifecycle fixture.', 'CROSS_SOURCE_SUPPORTED',
      'CROSS_SOURCE', 'one-source-family', 1
    )$$,
  '23514', 'association_range_cross_source_support_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'question_active_without_user_evidence',
  $$UPDATE calibration.question_research_candidate
    SET lifecycle_status = 'ACTIVE_FOR_CALIBRATION'
    WHERE question_version_key = 'round3e.floral_tea_reference.en'$$,
  '23514', 'question_research_user_validation_evidence_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'information_gain_without_observations',
  $$UPDATE calibration.question_range_target
    SET information_gain_status = 'ESTIMATED'
    WHERE question_range_target_key =
      'question-range.fruit-direction.fruit'$$,
  '23514', 'question_range_target_nonvalidation_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'source_absence_to_negative_relation',
  $$SELECT audit.reject_forbidden_round3f_inference(
      'SOURCE_ABSENCE', 'NEGATIVE_ASSOCIATION'
    )$$,
  '23514', 'round3f_absence_not_negative_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'new_canonical_concept_from_phrase',
  $$INSERT INTO kb.concept (
      concept_key, concept_type_code, lifecycle_status_code,
      provenance_scope_code, description
    ) VALUES (
      'negative.industry_phrase', 'sensory_attribute', 'candidate',
      'project_authored', 'Negative fixture.'
    )$$,
  '23514', 'round3f_canonical_ontology_frozen_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'split_existing_descriptor',
  $$UPDATE kb.concept
    SET concept_key = concept_key || '.negative_split'
    WHERE concept_id = (SELECT min(concept_id) FROM kb.concept)$$,
  '23514', 'round3f_canonical_ontology_frozen_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'round3f_data_in_model_run',
  $$INSERT INTO ml.model_run (
      model_run_key, model_version_id, model_run_status_code,
      input_corpus_id, started_at, run_configuration, result_metadata
    ) SELECT 'negative.round3f.model-run', version.model_version_id,
             'running', corpus.corpus_id,
             TIMESTAMPTZ '2026-08-25 00:00:00+00',
             '{"round":"3F","uses_association_range":"true"}', '{}'
      FROM ml.model_version AS version
      CROSS JOIN corpus.corpus AS corpus
      ORDER BY version.model_version_id, corpus.corpus_id LIMIT 1$$,
  '23514', 'round3f_model_run_prohibited_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'numeric_probability_membership',
  $$INSERT INTO corpus.association_range_membership (
      membership_key, association_range_id, lexical_mapping_key,
      membership_role, lifecycle_status, evidence_basis,
      evidence_key, provenance_path, membership_semantics
    ) SELECT 'negative.round3f.probability', range.association_range_id,
             candidate.mapping_key, 'AMBIGUOUS', 'CANDIDATE',
             'EXPLICIT_CURATED_REVIEW_DECISION',
             'negative fixture', 'negative fixture', 'PROBABILITY_0_8'
      FROM corpus.association_range AS range
      CROSS JOIN LATERAL (
        SELECT mapping_key FROM corpus.lexical_mapping_candidate
        ORDER BY mapping_key LIMIT 1
      ) AS candidate
      ORDER BY range.association_range_id LIMIT 1$$,
  '23514', 'association_range_membership_nonprobability_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'pairwise_chain_to_transitive_association',
  $$SELECT audit.reject_forbidden_round3f_inference(
      'PAIRWISE_ASSOCIATION_CHAIN', 'TRANSITIVE_ASSOCIATION'
    )$$,
  '23514', 'round3f_association_not_transitive_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'literal_translation_to_bilingual_equivalence',
  $$SELECT audit.reject_forbidden_round3f_inference(
      'LITERAL_TRANSLATION', 'BILINGUAL_EQUIVALENCE'
    )$$,
  '23514', 'round3f_translation_not_equivalence_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'range_active_without_review',
  $$UPDATE corpus.association_range
    SET lifecycle_status = 'ACTIVE_FOR_CALIBRATION'
    WHERE range_key = 'floral-tea'$$,
  '23514', 'association_range_calibration_review_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'measurement_without_method_configuration',
  $$INSERT INTO corpus.association_measurement (
      measurement_key, association_range_membership_id,
      method_key, method_version, source_snapshot_key,
      support_count, value_semantics, configuration
    ) SELECT 'negative.round3f.empty-config',
             association_range_membership_id,
             'RAW_COOCCURRENCE', 'negative-v1', 'negative-snapshot',
             2, 'negative fixture', '{}'
      FROM corpus.association_range_membership
      ORDER BY association_range_membership_id LIMIT 1$$,
  '23514', 'association_measurement_configuration_ck'
);

SELECT pg_temp.expect_round3f_failure(
  'new_canonical_relation_type',
  $$INSERT INTO ref.relation_type (
      relation_type_code, display_name, description, is_directional,
      is_symmetric, is_hierarchical, closure_is_transitive,
      allows_self, evidence_required
    ) VALUES (
      'range_synonym', 'Range synonym', 'Negative fixture.',
      TRUE, FALSE, FALSE, FALSE, FALSE, TRUE
    )$$,
  '23514', 'round3f_canonical_ontology_frozen_ck'
);

ROLLBACK;

\echo ROUND3F_NEGATIVE_TEST_COUNT=18
\echo ROUND3F_NEGATIVE_TEST_PASS=true
