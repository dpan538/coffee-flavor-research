\set ON_ERROR_STOP on

BEGIN;

CREATE INDEX external_observation_snapshot_type_idx
    ON evidence.external_observation (
        dataset_snapshot_key, record_type, external_observation_id
    );
CREATE INDEX external_document_context_idx
    ON corpus.external_document (
        c0_candidate, black_milk, language_code, external_document_id
    );
CREATE INDEX external_expression_normalized_idx
    ON corpus.external_expression_occurrence (
        normalized_expression, language_code, expression_occurrence_key
    );
CREATE INDEX question_research_candidate_region_idx
    ON calibration.question_research_candidate (
        candidate_region, logical_question_code, language_code
    );
CREATE INDEX empirical_coverage_source_context_idx
    ON audit.empirical_coverage_cell (
        source_key, c0_preparation, c1_roast, black_milk
    );

CREATE VIEW evidence.v_external_snapshot_inventory AS
SELECT
    snapshot.dataset_snapshot_key,
    source.source_key,
    version.source_version_key,
    dataset.dataset_key,
    snapshot.source_version,
    snapshot.declared_row_count,
    snapshot.verified_row_count,
    snapshot.declared_field_count,
    snapshot.verified_field_count,
    snapshot.imported_record_count,
    snapshot.exclusion_count,
    snapshot.import_version,
    snapshot.import_code_sha,
    snapshot.license_expression,
    snapshot.rights_decision,
    snapshot.privacy_decision,
    snapshot.public_release_eligible,
    (SELECT count(*)::INTEGER
     FROM evidence.external_source_file AS file
     WHERE file.dataset_snapshot_key = snapshot.dataset_snapshot_key)
        AS source_file_count,
    (SELECT count(*)::INTEGER
     FROM evidence.external_source_file AS file
     WHERE file.dataset_snapshot_key = snapshot.dataset_snapshot_key
       AND file.declared_sha256 = file.observed_sha256)
        AS matched_file_hash_count,
    (SELECT count(*)::INTEGER
     FROM evidence.external_observation AS observation
     WHERE observation.dataset_snapshot_key = snapshot.dataset_snapshot_key)
        AS external_observation_count,
    (SELECT count(*)::INTEGER
     FROM corpus.external_document AS document
     WHERE document.dataset_snapshot_key = snapshot.dataset_snapshot_key)
        AS external_document_count
FROM evidence.external_dataset_snapshot AS snapshot
JOIN evidence.dataset AS dataset ON dataset.dataset_id = snapshot.dataset_id
JOIN evidence.source_version AS version
  ON version.source_version_id = dataset.source_version_id
JOIN evidence.source AS source ON source.source_id = version.source_id
;

CREATE VIEW calibration.v_round3e_question_research AS
SELECT
    logical_question_code,
    language_code,
    lifecycle_status,
    candidate_region,
    prompt_text,
    answer_options,
    information_gain_status,
    ordinary_user_validation_evidence,
    expected_information_role,
    unresolved_concerns
FROM calibration.question_research_candidate;

CREATE VIEW audit.v_round3e_empirical_coverage AS
SELECT
    source_key AS source,
    coffee_identity,
    c0_preparation,
    c1_roast,
    black_milk,
    sensory_method,
    participant_type,
    language_code AS language,
    observed_record_count,
    cell_status,
    interpretation_limit
FROM audit.empirical_coverage_cell;

CREATE FUNCTION audit.run_round3e_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3e_validation_queries$
    WITH checks AS (
      SELECT 'round3e.snapshot_count_4'::TEXT AS check_key,
             abs(4 - count(*))::BIGINT AS violation_count
      FROM evidence.external_dataset_snapshot
      UNION ALL
      SELECT 'round3e.source_file_count_7', abs(7 - count(*))::BIGINT
      FROM evidence.external_source_file
      UNION ALL
      SELECT 'round3e.source_file_hashes_match', count(*)::BIGINT
      FROM evidence.external_source_file
      WHERE declared_sha256 <> observed_sha256
      UNION ALL
      SELECT 'round3e.snapshot_dimensions_match', count(*)::BIGINT
      FROM evidence.external_dataset_snapshot
      WHERE declared_row_count <> verified_row_count
         OR declared_field_count <> verified_field_count
      UNION ALL
      SELECT 'round3e.file_rows_reconcile', count(*)::BIGINT
      FROM (
        SELECT snapshot.dataset_snapshot_key
        FROM evidence.external_dataset_snapshot AS snapshot
        JOIN evidence.external_source_file AS file
          ON file.dataset_snapshot_key = snapshot.dataset_snapshot_key
         AND file.counts_toward_snapshot
        GROUP BY snapshot.dataset_snapshot_key, snapshot.declared_row_count
        HAVING sum(file.declared_row_count) <> snapshot.declared_row_count
      ) AS mismatch
      UNION ALL
      SELECT 'round3e.imported_records_reconcile', count(*)::BIGINT
      FROM (
        SELECT snapshot.dataset_snapshot_key
        FROM evidence.external_dataset_snapshot AS snapshot
        LEFT JOIN evidence.external_observation AS observation
          ON observation.dataset_snapshot_key = snapshot.dataset_snapshot_key
        LEFT JOIN corpus.external_document AS document
          ON document.dataset_snapshot_key = snapshot.dataset_snapshot_key
        GROUP BY snapshot.dataset_snapshot_key,
                 snapshot.imported_record_count
        HAVING count(DISTINCT observation.external_observation_id)
             + count(DISTINCT document.external_document_id)
             <> snapshot.imported_record_count
      ) AS mismatch
      UNION ALL
      SELECT 'round3e.external_observation_count_413',
             abs(413 - count(*))::BIGINT
      FROM evidence.external_observation
      UNION ALL
      SELECT 'round3e.corpus_document_count_46',
             abs(46 - count(*))::BIGINT
      FROM corpus.external_document
      UNION ALL
      SELECT 'round3e.corpus_expression_count_215',
             abs(215 - count(*))::BIGINT
      FROM corpus.external_expression_occurrence
      UNION ALL
      SELECT 'round3e.lexical_mapping_count_107',
             abs(107 - count(*))::BIGINT
      FROM corpus.lexical_mapping_candidate
      UNION ALL
      SELECT 'round3e.no_expression_auto_promotion', count(*)::BIGINT
      FROM corpus.external_expression_occurrence
      WHERE automatic_promotion_allowed
      UNION ALL
      SELECT 'round3e.question_version_count_18',
             abs(18 - count(*))::BIGINT
      FROM calibration.question_research_candidate
      UNION ALL
      SELECT 'round3e.question_logical_count_9',
             abs(9 - count(DISTINCT logical_question_code))::BIGINT
      FROM calibration.question_research_candidate
      UNION ALL
      SELECT 'round3e.question_not_user_validated', count(*)::BIGINT
      FROM calibration.question_research_candidate
      WHERE ordinary_user_validation_evidence IS NOT NULL
         OR lifecycle_status IN (
             'COMPREHENSION_READY', 'ACTIVE_FOR_CALIBRATION'
         )
         OR information_gain_status <> 'NOT_ESTIMABLE'
      UNION ALL
      SELECT 'round3e.coverage_observed_cells_52',
             abs(52 - count(*))::BIGINT
      FROM audit.empirical_coverage_cell
      UNION ALL
      SELECT 'round3e.coverage_contains_presence_only', count(*)::BIGINT
      FROM audit.empirical_coverage_cell
      WHERE cell_status <> 'OBSERVED_SOURCE_LOCAL_EVIDENCE'
         OR observed_record_count <= 0
      UNION ALL
      SELECT 'round3e.raw_values_preserved', count(*)::BIGINT
      FROM evidence.external_observation
      WHERE NOT raw_value_preserved
         OR NOT evidence.round3e_reject_direct_identifiers(raw_value)
      UNION ALL
      SELECT 'round3e.no_silent_unit_conversion', count(*)::BIGINT
      FROM evidence.external_field_dictionary
      WHERE unit_conversion_applied
      UNION ALL
      SELECT 'round3e.public_export_policy', count(*)::BIGINT
      FROM evidence.external_source_file AS file
      JOIN evidence.external_dataset_snapshot AS snapshot
        ON snapshot.dataset_snapshot_key = file.dataset_snapshot_key
      WHERE file.raw_public_export_allowed
        AND NOT snapshot.public_release_eligible
      UNION ALL
      SELECT 'round3e.external_not_canonical_support', count(*)::BIGINT
      FROM evidence.concept_support AS support
      JOIN evidence.external_dataset_snapshot AS snapshot
        ON snapshot.dataset_id = support.dataset_id
      UNION ALL
      SELECT 'round3e.external_not_model_input', count(*)::BIGINT
      FROM ml.model_run AS run
      JOIN evidence.external_dataset_snapshot AS snapshot
        ON snapshot.dataset_id = run.input_dataset_id
      UNION ALL
      SELECT 'round3e_prohibition_flags_false', count(*)::BIGINT
      FROM audit.round3e_prohibition
      WHERE ranking_model_trained OR adaptive_policy_trained
         OR deep_learning_model_run OR embedding_baseline_run
         OR pgvector_required OR real_human_collection_performed
         OR real_observation_count <> 0 OR product_frontend_modified
      UNION ALL
      SELECT 'round3e.artifact_named_hashes_5', abs(5 - count(*))::BIGINT
      FROM audit.round3e_artifact_hash
      UNION ALL
      SELECT 'round3e.import_run_exact', count(*)::BIGINT
      FROM audit.external_import_run
      WHERE raw_snapshot_row_count <> 477
         OR imported_record_count <> 459
         OR exclusion_count <> 18
         OR source_file_count <> 7
         OR source_file_hash_count <> 7
         OR NOT pii_scan_pass OR NOT rights_review_pass
         OR NOT public_export_policy_pass
    )
    SELECT checks.check_key, checks.violation_count,
           checks.violation_count = 0 AS passed
    FROM checks
$run_round3e_validation_queries$;

COMMENT ON VIEW audit.v_round3e_empirical_coverage IS
    'Observed source-local evidence cells only. Missing combinations are not inferred or materialized as empty.';

COMMIT;
