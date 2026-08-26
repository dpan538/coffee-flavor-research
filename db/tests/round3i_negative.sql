\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3i_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID LANGUAGE plpgsql
AS $expect_round3i_failure$
DECLARE actual_state TEXT; actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3I negative unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3I_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3i_failure$;

CREATE FUNCTION pg_temp.attempt_round3i_raw_export_denied()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_raw_export_denied$
BEGIN
    INSERT INTO corpus.language_source_family (
        language_source_family_key, family_name, canonical_origin_key,
        counts_as_independent, mirror_of_language_source_family_key,
        counts_as_new_contemporary_family, counts_as_zh_hans_family,
        historical_baseline, source_authored, admitted,
        independence_basis, introduced_round
    ) VALUES (
        'family.negative.round3i.raw', 'Negative raw family',
        'origin.negative.round3i.raw', TRUE, NULL, FALSE, FALSE,
        FALSE, TRUE, TRUE, 'Negative fixture.', '3I'
    );
    INSERT INTO corpus.language_source (
        language_source_key, language_source_family_key, title,
        authors_or_owner, publication_year, doi_or_stable_url, repository,
        exact_version, access_date, license_expression, license_url,
        raw_text_internal_use, raw_text_public_redistribution,
        derived_expression_internal_use, derived_expression_public_release,
        derived_counts_internal_use, derived_counts_public_release,
        model_research_use, rights_basis, rights_review_complete,
        privacy_decision, privacy_review_complete, source_file_manifest,
        source_file_hash_complete, language_codes, geography, data_type,
        evidence_role, limitations, annotation_complete, admitted,
        row_count_unit, raw_row_count, admitted_row_count, excluded_row_count
    ) SELECT
        'source.negative.round3i.raw', 'family.negative.round3i.raw',
        title, authors_or_owner, publication_year, doi_or_stable_url,
        repository, exact_version, access_date, license_expression,
        license_url, 'ALLOW', 'DENY', derived_expression_internal_use,
        derived_expression_public_release, derived_counts_internal_use,
        derived_counts_public_release, model_research_use, rights_basis,
        rights_review_complete, privacy_decision, privacy_review_complete,
        source_file_manifest, source_file_hash_complete, language_codes,
        geography, data_type, evidence_role, limitations,
        annotation_complete, admitted,
        'negative_fixture_row', 1, 1, 0
    FROM corpus.language_source ORDER BY language_source_key LIMIT 1;
    INSERT INTO corpus.language_document (
        language_document_key, language_source_key,
        language_source_family_key, source_revision, source_date,
        source_row_locator, language_code, document_type,
        source_content_sha256, content, raw_text_public_export_allowed,
        counts_as_new_contemporary_document, counts_as_zh_hans_document,
        source_authored, machine_translated, artificial_variant,
        privacy_state, public_export_state, frozen_snapshot
    ) SELECT
        'document.negative.round3i.raw', 'source.negative.round3i.raw',
        'family.negative.round3i.raw', source_revision, source_date,
        'negative-raw-row', language_code, document_type,
        source_content_sha256, content, TRUE, FALSE, FALSE,
        TRUE, FALSE, FALSE, privacy_state, 'PUBLIC_RAW', FALSE
    FROM corpus.language_document WHERE language_code = 'en' LIMIT 1;
END;
$attempt_round3i_raw_export_denied$;

CREATE FUNCTION pg_temp.attempt_round3i_raw_retention_denied()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_raw_retention_denied$
BEGIN
    INSERT INTO corpus.language_source_family (
        language_source_family_key, family_name, canonical_origin_key,
        counts_as_independent, mirror_of_language_source_family_key,
        counts_as_new_contemporary_family, counts_as_zh_hans_family,
        historical_baseline, source_authored, admitted,
        independence_basis, introduced_round
    ) VALUES (
        'family.negative.round3i.retention', 'Negative retention family',
        'origin.negative.round3i.retention', TRUE, NULL, FALSE, FALSE,
        FALSE, TRUE, TRUE, 'Negative fixture.', '3I'
    );
    INSERT INTO corpus.language_source (
        language_source_key, language_source_family_key, title,
        authors_or_owner, publication_year, doi_or_stable_url, repository,
        exact_version, access_date, license_expression, license_url,
        raw_text_internal_use, raw_text_public_redistribution,
        derived_expression_internal_use, derived_expression_public_release,
        derived_counts_internal_use, derived_counts_public_release,
        model_research_use, rights_basis, rights_review_complete,
        privacy_decision, privacy_review_complete, source_file_manifest,
        source_file_hash_complete, language_codes, geography, data_type,
        evidence_role, limitations, annotation_complete, admitted,
        row_count_unit, raw_row_count, admitted_row_count, excluded_row_count
    ) SELECT
        'source.negative.round3i.retention',
        'family.negative.round3i.retention', title, authors_or_owner,
        publication_year, doi_or_stable_url, repository, exact_version,
        access_date, license_expression, license_url, 'DENY', 'DENY',
        derived_expression_internal_use, derived_expression_public_release,
        derived_counts_internal_use, derived_counts_public_release,
        model_research_use, rights_basis, rights_review_complete,
        privacy_decision, privacy_review_complete, source_file_manifest,
        source_file_hash_complete, language_codes, geography, data_type,
        evidence_role, limitations, annotation_complete, admitted,
        'negative_fixture_row', 1, 1, 0
    FROM corpus.language_source ORDER BY language_source_key LIMIT 1;
    INSERT INTO corpus.language_document (
        language_document_key, language_source_key,
        language_source_family_key, source_revision, source_date,
        source_row_locator, language_code, document_type,
        source_content_sha256, content, raw_text_public_export_allowed,
        counts_as_new_contemporary_document, counts_as_zh_hans_document,
        source_authored, machine_translated, artificial_variant,
        privacy_state, public_export_state, frozen_snapshot
    ) SELECT
        'document.negative.round3i.retention',
        'source.negative.round3i.retention',
        'family.negative.round3i.retention', source_revision, source_date,
        'negative-retention-row', language_code, document_type,
        source_content_sha256, content, FALSE, FALSE, FALSE,
        TRUE, FALSE, FALSE, privacy_state, 'PUBLIC_DERIVED_ONLY', FALSE
    FROM corpus.language_document WHERE language_code = 'en' LIMIT 1;
    INSERT INTO corpus.language_expression_occurrence (
        language_occurrence_key, language_document_key,
        language_expression_key, raw_source_phrase, source_locator,
        observed_value
    ) SELECT 'occurrence.negative.round3i.retention',
        'document.negative.round3i.retention', language_expression_key,
        representative_source_phrase, 'negative-retention-locator',
        '{}'::JSONB
    FROM corpus.language_expression WHERE language_code = 'en' LIMIT 1;
END;
$attempt_round3i_raw_retention_denied$;

CREATE FUNCTION pg_temp.attempt_round3i_same_reviewer()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_same_reviewer$
DECLARE h TEXT := encode(sha256(convert_to('same reviewer phrase','UTF8')),'hex');
        key TEXT;
BEGIN
    key := 'round3i.negative.sha256_' || h;
    INSERT INTO corpus.language_review_candidate VALUES (
        key, repeat('1',64), h, 1, 1, 1, repeat('2',64), repeat('3',64), FALSE
    );
    INSERT INTO corpus.language_candidate_review_decision VALUES
      ('review.negative.round3i.same.a', key, 'reviewer.same', 'A',
       repeat('1',64), 'ADMIT_SENSORY_LANGUAGE', 'sensory',
       DATE '2026-08-26', FALSE, FALSE),
      ('review.negative.round3i.same.b', key, 'reviewer.same', 'B',
       repeat('1',64), 'ADMIT_SENSORY_LANGUAGE', 'sensory',
       DATE '2026-08-26', FALSE, FALSE);
END;
$attempt_round3i_same_reviewer$;

CREATE FUNCTION pg_temp.attempt_round3i_review_spoof()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_review_spoof$
DECLARE phrase TEXT := 'review spoof phrase';
        h TEXT := encode(sha256(convert_to(phrase,'UTF8')),'hex'); key TEXT;
BEGIN
    key := 'round3i.negative.sha256_' || h;
    INSERT INTO corpus.language_review_candidate VALUES (
        key, repeat('4',64), h, 1, 1, 1, repeat('5',64), repeat('6',64), FALSE
    );
    INSERT INTO corpus.language_candidate_review_decision VALUES
      ('review.negative.round3i.spoof.a', key, 'reviewer.a', 'A',
       repeat('4',64), 'ADMIT_SENSORY_LANGUAGE', 'sensory',
       DATE '2026-08-26', FALSE, FALSE),
      ('review.negative.round3i.spoof.b', key, 'reviewer.b', 'B',
       repeat('4',64), 'REJECT_UNCERTAIN', 'uncertain',
       DATE '2026-08-26', FALSE, FALSE);
    INSERT INTO corpus.language_expression (
        language_expression_key, language_code, representative_source_phrase,
        normalized_expression, expression_role, source_authored,
        machine_translated, artificial_variant, review_state,
        counts_toward_governed_total,
        counts_as_zh_hans_sensory_expression, public_export_allowed, limitation
    ) VALUES (
        'language.expression.negative.round3i.spoof', 'en', phrase, phrase,
        'SENSORY_ATTRIBUTE', TRUE, FALSE, FALSE, 'DUAL_CODEX_REVIEWED',
        TRUE, FALSE, TRUE, 'Negative fixture.'
    );
    SET CONSTRAINTS corpus.language_expression_review_aiu IMMEDIATE;
END;
$attempt_round3i_review_spoof$;

CREATE FUNCTION pg_temp.attempt_round3i_failed_language_gate()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_failed_language_gate$
BEGIN
    UPDATE corpus.language_source_family
    SET counts_as_new_contemporary_family = FALSE
    WHERE counts_as_new_contemporary_family;
    PERFORM audit.assert_research_database_freeze_ready();
END;
$attempt_round3i_failed_language_gate$;

CREATE FUNCTION pg_temp.attempt_round3i_missing_source_version()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_missing_source_version$
BEGIN
    INSERT INTO corpus.language_source (
      language_source_key,language_source_family_key,title,authors_or_owner,
      publication_year,doi_or_stable_url,repository,exact_version,access_date,
      license_expression,license_url,raw_text_internal_use,
      raw_text_public_redistribution,derived_expression_internal_use,
      derived_expression_public_release,derived_counts_internal_use,
      derived_counts_public_release,model_research_use,rights_basis,
      rights_review_complete,privacy_decision,privacy_review_complete,
      source_file_manifest,source_file_hash_complete,language_codes,geography,
      data_type,evidence_role,limitations,annotation_complete,admitted,
      lifecycle_status,qualifies_as_observed_tasting_language,row_count_unit,
      raw_row_count,admitted_row_count,excluded_row_count
    ) SELECT
      'source.negative.round3i.missing-version',language_source_family_key,
      title,authors_or_owner,publication_year,doi_or_stable_url,repository,'',
      access_date,license_expression,license_url,raw_text_internal_use,
      raw_text_public_redistribution,derived_expression_internal_use,
      derived_expression_public_release,derived_counts_internal_use,
      derived_counts_public_release,model_research_use,rights_basis,
      rights_review_complete,privacy_decision,privacy_review_complete,
      source_file_manifest,source_file_hash_complete,language_codes,geography,
      data_type,evidence_role,limitations,annotation_complete,admitted,
      lifecycle_status,qualifies_as_observed_tasting_language,
      'negative_fixture_row',1,1,0
    FROM corpus.language_source ORDER BY language_source_key LIMIT 1;
END;
$attempt_round3i_missing_source_version$;

CREATE FUNCTION pg_temp.attempt_round3i_model_run()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_model_run$
BEGIN
    INSERT INTO ml.model (
      model_key, name, model_family, description, external_metadata
    ) VALUES (
      'negative.round3i.model', 'Round 3I negative model', 'test-only',
      'Transactional negative fixture.', '{"fixture":true}'::JSONB
    );
    INSERT INTO ml.model_version (
      model_version_key, model_id, version_label, artifact_locator,
      configuration, created_at
    ) SELECT
      'negative.round3i.model-version', model_id, 'round3i-negative',
      NULL, '{"fixture":true}'::JSONB,
      TIMESTAMPTZ '2026-08-26 03:00:00+00'
    FROM ml.model WHERE model_key = 'negative.round3i.model';
    INSERT INTO ml.model_run (
      model_run_key, model_version_id, model_run_status_code,
      input_dataset_id, started_at, completed_at, random_seed,
      run_configuration, result_metadata
    ) SELECT
      'negative.round3i.model-run', version.model_version_id, 'queued',
      dataset.dataset_id, TIMESTAMPTZ '2026-08-26 03:00:00+00', NULL,
      538, '{"round":"3I","prebuild":false}'::JSONB,
      '{"fixture":true}'::JSONB
    FROM ml.model_version AS version
    CROSS JOIN evidence.dataset AS dataset
    WHERE version.model_version_key = 'negative.round3i.model-version'
      AND dataset.dataset_key = 'dataset.project_smoke_seed';
    SET CONSTRAINTS ml.round3i_model_run_prohibited_biu IMMEDIATE;
END;
$attempt_round3i_model_run$;

CREATE FUNCTION pg_temp.attempt_round3i_future_in_place_mutation()
RETURNS VOID LANGUAGE plpgsql AS $attempt_round3i_future_in_place_mutation$
BEGIN
    INSERT INTO audit.research_database_reproducibility_attestation (
      freeze_version,clean_rebuild_count,postgresql_major,
      freeze_artifact_count,hashes_match_across_rebuilds,
      committed_artifacts_match,evidence_path,verified_at
    ) VALUES (
      'coffee-sensory-research-db-v0.1.0',2,17,11,TRUE,TRUE,
      'transactional-negative-fixture',
      TIMESTAMPTZ '2026-08-26 03:00:00+00'
    );
    PERFORM audit.finalize_research_database_release(
      'coffee-sensory-research-db-v0.1.0', repeat('1', 40),
      'coffee-sensory-research-db-v0.1.0', repeat('2', 40),
      'round3i-negative-test',
      'Transactional negative fixture; rolled back after mutation rejection.'
    );
    UPDATE corpus.language_expression
    SET limitation = limitation || ' forbidden mutation'
    WHERE language_expression_key = (
      SELECT language_expression_key FROM corpus.language_expression
      ORDER BY language_expression_key LIMIT 1
    );
END;
$attempt_round3i_future_in_place_mutation$;

SELECT pg_temp.expect_round3i_failure(
 'mirror_counted_independent',
 $$INSERT INTO corpus.language_source_family VALUES
 ('family.negative.round3i.mirror','Negative','origin.negative.mirror',TRUE,
  (SELECT language_source_family_key FROM corpus.language_source_family LIMIT 1),
  FALSE,FALSE,FALSE,TRUE,TRUE,'Negative fixture.','3I','ADMITTED')$$,
 '23514','language_source_family_mirror_origin_ck');

SELECT pg_temp.expect_round3i_failure(
 'duplicate_independent_origin',
 $$INSERT INTO corpus.language_source_family
 (language_source_family_key,family_name,canonical_origin_key,
  counts_as_independent,mirror_of_language_source_family_key,
  counts_as_new_contemporary_family,counts_as_zh_hans_family,
  historical_baseline,source_authored,admitted,independence_basis,introduced_round)
 SELECT 'family.negative.round3i.duplicate','Negative duplicate',canonical_origin_key,
 TRUE,NULL,FALSE,FALSE,FALSE,TRUE,TRUE,'Negative fixture.','3I'
 FROM corpus.language_source_family WHERE counts_as_independent LIMIT 1$$,
 '23505','language_source_family_independent_origin_uq');

SELECT pg_temp.expect_round3i_failure(
 'project_authored_zh_translation_counted',
 $$INSERT INTO corpus.language_source_family VALUES
 ('family.negative.round3i.project-translation',
  'Negative project-authored translation',
  'origin.negative.round3i.project-translation',TRUE,NULL,FALSE,TRUE,FALSE,
  FALSE,TRUE,'Project-authored translation is not source-authored evidence.',
  '3I','ADMITTED')$$,
 '23514','language_source_family_independence_ck');

SELECT pg_temp.expect_round3i_failure(
 'machine_translated_document_counted',
 $$INSERT INTO corpus.language_document
 SELECT 'document.negative.round3i.machine',language_source_key,
 language_source_family_key,source_revision,source_date,'negative-machine',
 language_code,document_type,source_content_sha256,content,
 raw_text_public_export_allowed,FALSE,TRUE,TRUE,TRUE,FALSE,privacy_state,
 public_export_state,FALSE,'ADMITTED',TRUE
 FROM corpus.language_document WHERE counts_as_zh_hans_document LIMIT 1$$,
 '23514','language_document_countability_ck');

SELECT pg_temp.expect_round3i_failure(
 'artificial_expression_counted',
 $$INSERT INTO corpus.language_expression
 (language_expression_key,language_code,representative_source_phrase,
 normalized_expression,expression_role,source_authored,machine_translated,
 artificial_variant,review_state,counts_toward_governed_total,
 counts_as_zh_hans_sensory_expression,public_export_allowed,limitation)
 VALUES ('language.expression.negative.artificial','en','Artificial phrase',
 'artificial phrase','SENSORY_ATTRIBUTE',TRUE,FALSE,TRUE,'SOURCE_REVIEWED',
 TRUE,FALSE,TRUE,'Negative fixture.')$$,
 '23514','language_expression_countability_ck');

SELECT pg_temp.expect_round3i_failure(
 'duplicate_normalized_expression_counted',
 $$INSERT INTO corpus.language_expression (
  language_expression_key,language_code,representative_source_phrase,
  normalized_expression,expression_role,source_authored,machine_translated,
  artificial_variant,review_state,counts_toward_governed_total,
  counts_as_zh_hans_sensory_expression,public_export_allowed,limitation)
 SELECT 'language.expression.negative.round3i.duplicate-normalized',
  language_code,representative_source_phrase,normalized_expression,
  expression_role,source_authored,machine_translated,artificial_variant,
  review_state,counts_toward_governed_total,
  counts_as_zh_hans_sensory_expression,public_export_allowed,
  'Negative duplicate normalized-expression fixture.'
 FROM corpus.language_expression
 ORDER BY language_expression_key LIMIT 1$$,
 '23505','language_expression_normalized_uq');

SELECT pg_temp.expect_round3i_failure(
 'preparation_expression_counted',
 $$INSERT INTO corpus.language_expression
 (language_expression_key,language_code,representative_source_phrase,
 normalized_expression,expression_role,source_authored,machine_translated,
 artificial_variant,review_state,counts_toward_governed_total,
 counts_as_zh_hans_sensory_expression,public_export_allowed,limitation)
 VALUES ('language.expression.negative.preparation','en','Pour over',
 'pour over','PREPARATION',TRUE,FALSE,FALSE,'SOURCE_REVIEWED',TRUE,FALSE,
 TRUE,'Negative fixture.')$$,
 '23514','language_expression_countability_ck');

SELECT pg_temp.expect_round3i_failure(
 'zh_roast_expression_counted',
 $$INSERT INTO corpus.language_expression
 (language_expression_key,language_code,representative_source_phrase,
 normalized_expression,expression_role,source_authored,machine_translated,
 artificial_variant,review_state,counts_toward_governed_total,
 counts_as_zh_hans_sensory_expression,public_export_allowed,limitation)
 VALUES ('language.expression.negative.zh-roast','zh-Hans','深烘焙','深烘焙',
 'ROAST',TRUE,FALSE,FALSE,'SOURCE_REVIEWED',TRUE,TRUE,TRUE,'Negative fixture.')$$,
 '23514','language_expression_countability_ck');

SELECT pg_temp.expect_round3i_failure(
 'rights_review_omitted',
 $$INSERT INTO corpus.language_source (
 language_source_key,language_source_family_key,title,authors_or_owner,
 publication_year,doi_or_stable_url,repository,exact_version,access_date,
 license_expression,license_url,raw_text_internal_use,
 raw_text_public_redistribution,derived_expression_internal_use,
 derived_expression_public_release,derived_counts_internal_use,
 derived_counts_public_release,model_research_use,rights_basis,
 rights_review_complete,privacy_decision,privacy_review_complete,
 source_file_manifest,source_file_hash_complete,language_codes,geography,
 data_type,evidence_role,limitations,annotation_complete,admitted,
 lifecycle_status,qualifies_as_observed_tasting_language,row_count_unit,
 raw_row_count,admitted_row_count,excluded_row_count)
 SELECT 'source.negative.round3i.rights',language_source_family_key,title,
 authors_or_owner,publication_year,doi_or_stable_url,repository,exact_version,
 access_date,license_expression,license_url,raw_text_internal_use,
 raw_text_public_redistribution,derived_expression_internal_use,
 derived_expression_public_release,derived_counts_internal_use,
 derived_counts_public_release,model_research_use,rights_basis,FALSE,
 privacy_decision,privacy_review_complete,source_file_manifest,
 source_file_hash_complete,language_codes,geography,data_type,evidence_role,
 limitations,annotation_complete,TRUE,'ADMITTED',TRUE,
 'negative_fixture_row',1,1,0
 FROM corpus.language_source LIMIT 1$$,
 '23514','language_source_admission_ck');

SELECT pg_temp.expect_round3i_failure(
 'manifest_hash_omitted',
 $$INSERT INTO corpus.language_source (
 language_source_key,language_source_family_key,title,authors_or_owner,
 publication_year,doi_or_stable_url,repository,exact_version,access_date,
 license_expression,license_url,raw_text_internal_use,
 raw_text_public_redistribution,derived_expression_internal_use,
 derived_expression_public_release,derived_counts_internal_use,
 derived_counts_public_release,model_research_use,rights_basis,
 rights_review_complete,privacy_decision,privacy_review_complete,
 source_file_manifest,source_file_hash_complete,language_codes,geography,
 data_type,evidence_role,limitations,annotation_complete,admitted,
 lifecycle_status,qualifies_as_observed_tasting_language,row_count_unit,
 raw_row_count,admitted_row_count,excluded_row_count)
 SELECT 'source.negative.round3i.manifest',language_source_family_key,title,
 authors_or_owner,publication_year,doi_or_stable_url,repository,exact_version,
 access_date,license_expression,license_url,raw_text_internal_use,
 raw_text_public_redistribution,derived_expression_internal_use,
 derived_expression_public_release,derived_counts_internal_use,
 derived_counts_public_release,model_research_use,rights_basis,
 rights_review_complete,privacy_decision,privacy_review_complete,
 '[{"path":"missing-hash.tsv"}]'::JSONB,TRUE,language_codes,geography,
 data_type,evidence_role,limitations,annotation_complete,TRUE,'ADMITTED',TRUE,
 'negative_fixture_row',1,1,0
 FROM corpus.language_source LIMIT 1$$,
 '23514','language_source_file_manifest_ck');

SELECT pg_temp.expect_round3i_failure(
 'raw_public_redistribution_denied',
 $$SELECT pg_temp.attempt_round3i_raw_export_denied()$$,
 '23514','language_document_raw_redistribution_ck');

SELECT pg_temp.expect_round3i_failure(
 'raw_internal_retention_denied',
 $$SELECT pg_temp.attempt_round3i_raw_retention_denied()$$,
 '23514','language_occurrence_raw_retention_ck');

SELECT pg_temp.expect_round3i_failure(
 'candidate_hash_missing',
 $$INSERT INTO corpus.language_review_candidate VALUES
 ('round3i.negative.sha256_'||repeat('a',64),'bad',repeat('a',64),1,1,1,
 repeat('b',64),repeat('c',64),FALSE)$$,
 '23514','language_review_candidate_key_ck');

SELECT pg_temp.expect_round3i_failure(
 'candidate_text_retained',
 $$INSERT INTO corpus.language_review_candidate VALUES
 ('round3i.negative.sha256_'||repeat('d',64),repeat('e',64),repeat('d',64),
 1,1,1,repeat('f',64),repeat('0',64),TRUE)$$,
 '23514','language_review_candidate_key_ck');

SELECT pg_temp.expect_round3i_failure(
 'review_missing_candidate',
 $$INSERT INTO corpus.language_candidate_review_decision VALUES
 ('review.negative.round3i.missing','round3i.missing.sha256_'||repeat('a',64),
 'reviewer.a','A',repeat('b',64),'ADMIT_SENSORY_LANGUAGE','sensory',
 DATE '2026-08-26',FALSE,FALSE)$$,
 '23503','language_candidate_review_candidate_fk');

SELECT pg_temp.expect_round3i_failure(
 'same_reviewer_both_passes',
 $$SELECT pg_temp.attempt_round3i_same_reviewer()$$,
 '23514','language_candidate_review_independent_reviewer_ck');

SELECT pg_temp.expect_round3i_failure(
 'dual_review_consensus_spoof',
 $$SELECT pg_temp.attempt_round3i_review_spoof()$$,
 '23514','language_expression_dual_review_consensus_ck');

SELECT pg_temp.expect_round3i_failure(
 'generic_document_gamed_as_sensory',
 $$INSERT INTO corpus.language_document
 SELECT 'document.negative.round3i.generic',language_source_key,
 language_source_family_key,source_revision,source_date,'negative-generic',
 language_code,document_type,source_content_sha256,content,
 raw_text_public_export_allowed,FALSE,TRUE,TRUE,FALSE,FALSE,privacy_state,
 public_export_state,FALSE,'ADMITTED',FALSE
 FROM corpus.language_document WHERE counts_as_zh_hans_document LIMIT 1$$,
 '23514','language_document_countability_ck');

SELECT pg_temp.expect_round3i_failure(
 'artifact_hash_mismatch',
 $$INSERT INTO audit.research_database_artifact_hash
 SELECT freeze_version,'negative.round3i.artifact','FEATURE_REGISTRY',
 'negative/artifact.tsv',repeat('1',64),repeat('2',64),TRUE,TRUE,FALSE,
 'Negative fixture.' FROM audit.research_database_release LIMIT 1$$,
 '23514','research_database_artifact_hash_ck');

SELECT pg_temp.expect_round3i_failure(
 'current_surface_role_spoof',
 $$INSERT INTO audit.research_database_current_surface
 SELECT freeze_version,'round3i.negative.surface','CANONICAL_CONCEPT',
 'kb.v_current_lexical_evidence',repeat('1',64),'CURRENT_APPROVED',TRUE,TRUE,
 'kb.v_lexical_resolution','Negative fixture.'
 FROM audit.research_database_release LIMIT 1$$,
 '23514','research_database_current_surface_role_ck');

SELECT pg_temp.expect_round3i_failure(
 'deprecated_surface_approved',
 $$INSERT INTO audit.research_database_current_surface
 SELECT freeze_version,'round3i.negative.deprecated',NULL,
 'audit.v_current_research_database_surface',repeat('1',64),
 'DEPRECATED_RESEARCH',TRUE,FALSE,NULL,'Negative fixture.'
 FROM audit.research_database_release LIMIT 1$$,
 '23514','research_database_current_surface_ck');

SELECT pg_temp.expect_round3i_failure(
 'threshold_lowered_without_approval',
 $$INSERT INTO audit.research_database_threshold_revision VALUES
 ('threshold.negative.round3i',(SELECT freeze_version
 FROM audit.research_database_release LIMIT 1),'language.documents','500','1',
 'LOWERED','NOT_REQUIRED','negative.tsv',repeat('1',64))$$,
 '23514','research_database_threshold_revision_ck');

SELECT pg_temp.expect_round3i_failure(
 'freeze_without_attestation',
 $$UPDATE audit.research_database_release SET lifecycle_status='FROZEN',
 final_repository_sha=repeat('1',40),final_repository_ref='refs/heads/main',
 release_tag_target_sha=repeat('1',40),release_tag_object_sha=repeat('2',40),
 frozen_on=DATE '2026-08-26' WHERE lifecycle_status='FREEZE_CANDIDATE'$$,
 '23514','research_database_freeze_attestation_required_ck');

SELECT pg_temp.expect_round3i_failure(
 'frozen_document_mutation',
 $$UPDATE corpus.language_document SET source_revision=source_revision||'-bad'
 WHERE frozen_snapshot$$,
 '23514','language_document_frozen_immutable_ck');

SELECT pg_temp.expect_round3i_failure(
 'failed_mandatory_language_gate',
 $$SELECT pg_temp.attempt_round3i_failed_language_gate()$$,
 '23514','round3i_research_database_freeze_gate_ck');

SELECT pg_temp.expect_round3i_failure(
 'missing_source_version',
 $$SELECT pg_temp.attempt_round3i_missing_source_version()$$,
 '23514','language_source_key_ck');

SELECT pg_temp.expect_round3i_failure(
 'orphan_relationship_evidence',
 $$UPDATE evidence.relationship_evidence_claim
 SET source_key='source.negative.round3i.orphan'
 WHERE evidence_claim_key=(SELECT evidence_claim_key
 FROM evidence.relationship_evidence_claim ORDER BY evidence_claim_key LIMIT 1)$$,
 '23503','relationship_evidence_claim_source_fk');

SELECT pg_temp.expect_round3i_failure(
 'canonical_change_after_prebuild_checkpoint',
 $$INSERT INTO kb.concept (
 concept_key,concept_type_code,lifecycle_status_code,
 provenance_scope_code,description)
 VALUES ('sensory.negative_round3i_canonical_change','sensory_attribute','candidate',
 'project_authored','Negative fixture.')$$,
 '23514','round3f_canonical_ontology_frozen_ck');

SELECT pg_temp.expect_round3i_failure(
 'model_run_after_research_database_freeze',
 $$SELECT pg_temp.attempt_round3i_model_run()$$,
 '23514','round3i_model_run_prohibited_ck');

SELECT pg_temp.expect_round3i_failure(
 'embedding_after_research_database_freeze',
 $$INSERT INTO ml.model_version (
 model_version_key,model_id,version_label,artifact_locator,configuration,created_at)
 SELECT 'negative.round3i.embedding',model_id,'negative-round3i-embedding',
 'negative://round3i-embedding','{"embeddings":true}'::JSONB,CURRENT_TIMESTAMP
 FROM ml.model_version ORDER BY model_version_id LIMIT 1$$,
 '23514','model_prebuild_embedding_generation_prohibited_ck');

SELECT pg_temp.expect_round3i_failure(
 'frontend_change_claim',
 $$UPDATE audit.model_prebuild_execution_guard
 SET product_frontend_modified=TRUE$$,
 '23514','model_prebuild_execution_guard_prohibition_ck');

SELECT pg_temp.expect_round3i_failure(
 'freeze_manifest_overwrite',
 $$UPDATE audit.research_database_artifact_hash
 SET sha256=repeat('9',64),verified_sha256=repeat('9',64)
 WHERE freeze_version='coffee-sensory-research-db-v0.1.0'
 AND artifact_type='FREEZE_MANIFEST'$$,
 '23514','round3i_freeze_artifact_immutable_ck');

SELECT pg_temp.expect_round3i_failure(
 'same_version_different_manifest_sha',
 $$INSERT INTO audit.research_database_release
 SELECT freeze_version,lifecycle_status,repeat('3',40),NULL,NULL,NULL,NULL,
 manifest_path,repeat('9',64),expected_state_commit_sha,release_tag,
 supersedes_freeze_version,created_on,NULL,limitation
 FROM audit.research_database_release
 WHERE freeze_version='coffee-sensory-research-db-v0.1.0'$$,
 '23514','round3i_freeze_version_hash_binding_ck');

SELECT pg_temp.expect_round3i_failure(
 'attestation_without_two_rebuild_evidence',
 $$SELECT audit.finalize_research_database_release(
 'coffee-sensory-research-db-v0.1.0',repeat('1',40),
 'coffee-sensory-research-db-v0.1.0',repeat('2',40),
 'round3i-negative-test','Missing two-rebuild evidence fixture.')$$,
 '23514','round3i_reproducibility_attestation_required_ck');

SELECT pg_temp.expect_round3i_failure(
 'future_frozen_member_in_place_mutation',
 $$SELECT pg_temp.attempt_round3i_future_in_place_mutation()$$,
 '23514','research_database_frozen_member_immutable_ck');

DO $round3i_current_surface_assertions$
BEGIN
    IF EXISTS (
        SELECT 1 FROM corpus.v_current_language_corpus
        WHERE review_state IN ('REJECTED','QUARANTINED','DEPRECATED')
    ) OR EXISTS (
        SELECT 1 FROM evidence.v_current_relationship_evidence
        WHERE review_status <> 'REVIEWED'
           OR evidence_direction NOT IN ('SUPPORTS','CHALLENGES','MIXED')
    ) OR EXISTS (
        SELECT 1 FROM evidence.v_current_sensory_partition
        WHERE future_training_surface_status <>
              'ELIGIBLE_AFTER_FUTURE_PROTOCOL'
    ) THEN
        RAISE EXCEPTION 'Round 3I current surface leaked non-current evidence';
    END IF;
    RAISE NOTICE 'ROUND3I_NEGATIVE=current_surface_exclusion PASS';
END;
$round3i_current_surface_assertions$;

ROLLBACK;

\echo ROUND3I_NEGATIVE_TEST_COUNT=35
\echo ROUND3I_NEGATIVE_TEST_PASS=true
