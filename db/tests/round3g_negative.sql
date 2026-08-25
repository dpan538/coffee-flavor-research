\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3g_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3g_failure$
DECLARE actual_state TEXT; actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3G negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                                actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3G_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
          test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3g_failure$;

CREATE FUNCTION pg_temp.attempt_round3g_cross_one_family()
RETURNS VOID
LANGUAGE plpgsql
AS $attempt_round3g_cross_one_family$
BEGIN
  UPDATE kb.relationship_review_decision
  SET disposition = 'PROMOTE_CROSS_SOURCE',
      new_lifecycle = 'CROSS_SOURCE_SUPPORTED',
      supporting_source_families = ARRAY[
        'family.liberica-ratapanel-2025',
        'family.liberica-ratapanel-2025'
      ]
  WHERE review_key = 'review.membership.floral-tea.jasmine';

  INSERT INTO evidence.relationship_evidence_claim
  SELECT 'claim.negative.cross-one-family', 'MEMBERSHIP',
         'membership.floral-tea.jasmine', source_family_key,
         source_key, snapshot_key, evidence_basis, 'SUPPORTS',
         evidence_scope, evidence_locator, method, configuration,
         3, 2, 1, review_status, limitation,
         contradictory_evidence_retained
  FROM evidence.relationship_evidence_claim
  WHERE evidence_claim_key = 'claim.liberica.membership.smoke.supports';

  UPDATE corpus.association_range_membership
  SET lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
  WHERE membership_key = 'membership.floral-tea.jasmine';
END;
$attempt_round3g_cross_one_family$;

CREATE FUNCTION pg_temp.attempt_round3g_promotion_without_review()
RETURNS VOID
LANGUAGE plpgsql
AS $attempt_round3g_promotion_without_review$
BEGIN
  DELETE FROM kb.relationship_review_decision
  WHERE review_key = 'review.membership.floral-tea.floral';

  INSERT INTO evidence.relationship_evidence_claim
  SELECT 'claim.negative.no-review', 'MEMBERSHIP',
         'membership.floral-tea.floral', source_family_key,
         source_key, snapshot_key, evidence_basis, 'SUPPORTS',
         evidence_scope, evidence_locator, method, configuration,
         3, 2, 1, review_status, limitation,
         contradictory_evidence_retained
  FROM evidence.relationship_evidence_claim
  WHERE evidence_claim_key = 'claim.liberica.membership.smoke.supports';

  UPDATE corpus.association_range_membership
  SET lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
  WHERE membership_key = 'membership.floral-tea.floral';
END;
$attempt_round3g_promotion_without_review$;

CREATE FUNCTION pg_temp.attempt_round3g_below_threshold()
RETURNS VOID
LANGUAGE plpgsql
AS $attempt_round3g_below_threshold$
BEGIN
  UPDATE kb.relationship_review_decision
  SET disposition = 'PROMOTE_SOURCE_LOCAL',
      new_lifecycle = 'SOURCE_LOCAL_SUPPORTED',
      supporting_source_families =
        ARRAY['family.liberica-ratapanel-2025']
  WHERE review_key = 'review.membership.floral-tea.jasmine';

  INSERT INTO evidence.relationship_evidence_claim
  SELECT 'claim.negative.below-threshold', 'MEMBERSHIP',
         'membership.floral-tea.jasmine', source_family_key,
         source_key, snapshot_key, evidence_basis, 'SUPPORTS',
         evidence_scope, evidence_locator, method, configuration,
         1, 1, 1, review_status, limitation,
         contradictory_evidence_retained
  FROM evidence.relationship_evidence_claim
  WHERE evidence_claim_key = 'claim.liberica.membership.smoke.supports';

  UPDATE corpus.association_range_membership
  SET lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
  WHERE membership_key = 'membership.floral-tea.jasmine';
END;
$attempt_round3g_below_threshold$;

SELECT pg_temp.expect_round3g_failure(
  'source_with_no_source_family',
  $$INSERT INTO evidence.relationship_source
    SELECT 'negative.source.no-family', 'family.missing',
           title, authors_or_owner, publication_year, doi_or_stable_url,
           repository, exact_version, access_date, source_type, geography,
           language, population_or_panel, sensory_method,
           preparation_coverage, roast_coverage, milk_coverage, license,
           commercial_use_allowed, derivative_use_allowed,
           redistribution_allowed, machine_use_allowed,
           rights_review_status, privacy_review_status, privacy_decision,
           public_export_decision, file_list, row_count, field_count,
           evidence_role, supported_relationship_keys,
           challenged_relationship_keys, evidence_locator, limitations,
           independence_note, admitted
    FROM evidence.relationship_source
    WHERE source_key = 'wiktionary.en.revision-set.20260825'$$,
  '23503', 'relationship_source_family_fk'
);

SELECT pg_temp.expect_round3g_failure(
  'source_file_mismatched_hash',
  $$INSERT INTO evidence.relationship_source_file
    SELECT 'negative.file.hash', snapshot_key, source_key,
           source_family_key, filename, file_role, locator, license,
           file_size_bytes, declared_sha256, repeat('0', 64), row_count,
           field_count, TRUE, contains_participant_identifiers,
           public_export_decision, local_path
    FROM evidence.relationship_source_file
    WHERE file_key = 'file.liberica.rata-summary'$$,
  '23514', 'relationship_source_file_hash_match_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'source_independent_from_own_mirror',
  $$INSERT INTO evidence.source_family (
      source_family_key, family_name, family_type, canonical_origin_key,
      counts_as_independent, mirror_of_source_family_key,
      independence_basis, admitted
    ) VALUES (
      'family.negative.own-mirror', 'Negative mirror', 'OTHER_RESEARCH',
      'origin.negative.own-mirror', TRUE,
      'family.liberica-ratapanel-2025', 'Negative fixture', TRUE
    )$$,
  '23514', 'source_family_mirror_independence_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'two_files_counted_as_two_families',
  $$INSERT INTO evidence.source_family (
      source_family_key, family_name, family_type, canonical_origin_key,
      counts_as_independent, independence_basis, admitted
    ) VALUES (
      'family.negative.duplicate-origin', 'Negative duplicate',
      'OTHER_RESEARCH', 'origin.doi.10.17632.m3n2gc4dv6.1', TRUE,
      'A second file is not independent.', TRUE
    )$$,
  '23505', 'source_family_independent_origin_uq'
);

SELECT pg_temp.expect_round3g_failure(
  'cross_source_with_one_family',
  $$SELECT pg_temp.attempt_round3g_cross_one_family()$$,
  '23514', 'round3g_membership_promotion_evidence_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'promotion_without_evidence_locator',
  $$INSERT INTO evidence.relationship_evidence_claim
    SELECT 'claim.negative.no-locator', target_entity_type,
           target_entity_key, source_family_key, source_key, snapshot_key,
           evidence_basis, evidence_direction, evidence_scope, '', method,
           configuration, support_count, document_count, source_diversity,
           review_status, limitation, contradictory_evidence_retained
    FROM evidence.relationship_evidence_claim
    WHERE evidence_claim_key =
      'claim.liberica.membership.smoke.supports'$$,
  '23514', 'relationship_evidence_claim_text_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'promotion_without_review',
  $$SELECT pg_temp.attempt_round3g_promotion_without_review()$$,
  '23514', 'round3g_membership_promotion_review_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'membership_from_unsupported_text_intuition',
  $$INSERT INTO corpus.association_range_membership (
      membership_key, association_range_id, member_text,
      member_language_code, membership_role, lifecycle_status,
      evidence_basis, evidence_key, provenance_path
    ) SELECT 'membership.negative.text-intuition', association_range_id,
             'invented relation', 'en', 'AMBIGUOUS', 'CANDIDATE',
             'TEXT_INTUITION', 'negative fixture', 'negative fixture'
      FROM corpus.association_range
      WHERE range_key = 'fruit'$$,
  '23514', 'association_range_membership_evidence_basis_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'isolated_occurrence_below_threshold',
  $$SELECT pg_temp.attempt_round3g_below_threshold()$$,
  '23514', 'round3g_membership_promotion_evidence_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'question_target_marked_user_validated',
  $$UPDATE calibration.question_range_target
    SET user_validation_status = 'USER_VALIDATED'
    WHERE question_range_target_key =
      'question-range.fruit-direction.fruit'$$,
  '23514', 'question_range_target_nonvalidation_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'question_information_gain_assigned',
  $$UPDATE calibration.question_range_target
    SET information_gain_status = 'ESTIMATED'
    WHERE question_range_target_key =
      'question-range.fruit-direction.fruit'$$,
  '23514', 'question_range_target_nonvalidation_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'literal_translation_promoted_bilingual_reviewed',
  $$UPDATE corpus.association_range_membership
    SET lifecycle_status = 'BILINGUAL_REVIEWED'
    WHERE membership_key = 'membership.floral-tea.jasmine'$$,
  '23514', 'round3g_bilingual_review_prohibited_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'range_activated_for_calibration',
  $$UPDATE corpus.association_range
    SET lifecycle_status = 'ACTIVE_FOR_CALIBRATION',
        explicit_review_evidence = 'negative fixture'
    WHERE range_key = 'floral-tea'$$,
  '23514', 'round3g_active_range_prohibited_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'new_active_range_created',
  $$INSERT INTO corpus.association_range (
      range_key, display_name, research_definition, lifecycle_status,
      support_scope, evidence_key, independent_evidence_family_count,
      explicit_review_evidence
    ) VALUES (
      'negative-new-active-range', 'Negative active range',
      'Negative fixture.', 'ACTIVE_FOR_CALIBRATION',
      'UNRESOLVED', 'negative fixture', 0, 'negative fixture'
    )$$,
  '23514', 'round3g_active_range_prohibited_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'canonical_concept_from_expression',
  $$INSERT INTO kb.concept (
      concept_key, concept_type_code, lifecycle_status_code,
      provenance_scope_code, description
    ) VALUES (
      'negative.round3g.expression', 'sensory_attribute', 'candidate',
      'project_authored', 'Negative fixture.'
    )$$,
  '23514', 'round3f_canonical_ontology_frozen_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'cooccurrence_promoted_to_sensory_neighbour',
  $$SELECT audit.reject_forbidden_round3f_inference(
      'COOCCURRENCE', 'SENSORY_NEIGHBOUR'
    )$$,
  '23514', 'round3f_cooccurrence_not_neighbour_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'challenged_evidence_silently_deleted',
  $$DELETE FROM evidence.relationship_evidence_claim
    WHERE evidence_claim_key = 'claim.liberica.range.roast.distinct'$$,
  '23514', 'round3g_contradictory_evidence_retained_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'failed_minimum_reported_as_pass',
  $$SELECT audit.assert_round3g_gate_classification(
      'PASS', TRUE, FALSE
    )$$,
  '23514', 'round3g_expected_state_truth_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'threshold_changed_after_import_without_decision',
  $$INSERT INTO audit.round3g_threshold_revision (
      revision_key, metric_key, original_value, revised_value,
      written_reason, epistemic_impact, invalidity_evidence,
      decision_record_key, recorded_at
    ) VALUES (
      'revision.negative', 'MINIMUM_OCCURRENCE_COUNT', '3', '3',
      '', '', '', '', TIMESTAMPTZ '2026-08-25 00:00:00+00'
    )$$,
  '23514', 'round3g_threshold_revision_decision_ck'
);

SELECT pg_temp.expect_round3g_failure(
  'round3g_source_used_in_model_run',
  $$INSERT INTO ml.model_run (
      model_run_key, model_version_id, model_run_status_code,
      input_corpus_id, started_at, run_configuration, result_metadata
    ) SELECT 'negative.round3g.model-run', version.model_version_id,
             'running', corpus.corpus_id,
             TIMESTAMPTZ '2026-08-25 00:00:00+00',
             '{"round":"3G","uses_round3g_evidence":"true"}', '{}'
      FROM ml.model_version AS version
      CROSS JOIN corpus.corpus AS corpus
      ORDER BY version.model_version_id, corpus.corpus_id LIMIT 1$$,
  '23514', 'round3g_model_run_prohibited_ck'
);

ROLLBACK;

\echo ROUND3G_NEGATIVE_TEST_PASS=true
