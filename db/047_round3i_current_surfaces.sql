\set ON_ERROR_STOP on

BEGIN;

CREATE VIEW corpus.v_current_language_corpus AS
WITH selected_release AS MATERIALIZED (
    SELECT audit.current_research_database_release_version() AS freeze_version
), round3i_rows AS (
    SELECT
        occurrence.language_occurrence_key AS record_key,
        'ROUND3I_OBSERVED_OCCURRENCE'::TEXT AS corpus_layer,
        expression.language_code,
        expression.representative_source_phrase,
        expression.normalized_expression,
        expression.expression_role,
        expression.review_state,
        family.language_source_family_key,
        source.language_source_key,
        document.language_document_key,
        occurrence.source_locator,
        CASE WHEN document.raw_text_public_export_allowed
                   AND source.raw_text_public_redistribution = 'ALLOW'
             THEN occurrence.raw_source_phrase END AS public_raw_source_phrase,
        occurrence.raw_source_phrase_sha256,
        document.counts_as_new_contemporary_document,
        document.counts_as_zh_hans_document,
        expression.counts_toward_governed_total,
        expression.counts_as_zh_hans_sensory_expression,
        expression.limitation
    FROM selected_release AS release
    JOIN audit.research_database_release_member AS expression_member
      ON expression_member.freeze_version = release.freeze_version
     AND expression_member.member_table = 'corpus.language_expression'
    JOIN corpus.language_expression AS expression
      ON expression.language_expression_key = expression_member.member_key
    JOIN corpus.language_expression_occurrence AS occurrence
      ON occurrence.language_expression_key = expression.language_expression_key
     AND occurrence.lifecycle_status = 'ADMITTED'
    JOIN audit.research_database_release_member AS occurrence_member
      ON occurrence_member.freeze_version = release.freeze_version
     AND occurrence_member.member_table =
         'corpus.language_expression_occurrence'
     AND occurrence_member.member_key = occurrence.language_occurrence_key
    JOIN corpus.language_document AS document
      ON document.language_document_key = occurrence.language_document_key
     AND document.lifecycle_status = 'ADMITTED'
    JOIN audit.research_database_release_member AS document_member
      ON document_member.freeze_version = release.freeze_version
     AND document_member.member_table = 'corpus.language_document'
     AND document_member.member_key = document.language_document_key
    JOIN corpus.language_source AS source
      ON source.language_source_key = document.language_source_key
     AND source.admitted AND source.lifecycle_status = 'ADMITTED'
     AND source.derived_expression_public_release = 'ALLOW'
    JOIN audit.research_database_release_member AS source_member
      ON source_member.freeze_version = release.freeze_version
     AND source_member.member_table = 'corpus.language_source'
     AND source_member.member_key = source.language_source_key
    JOIN corpus.language_source_family AS family
      ON family.language_source_family_key = document.language_source_family_key
     AND family.admitted AND family.lifecycle_status = 'ADMITTED'
    JOIN audit.research_database_release_member AS family_member
      ON family_member.freeze_version = release.freeze_version
     AND family_member.member_table = 'corpus.language_source_family'
     AND family_member.member_key = family.language_source_family_key
    WHERE expression.review_state IN (
              'SOURCE_REVIEWED', 'DUAL_CODEX_REVIEWED'
          )
      AND expression.public_export_allowed
), legacy_rows AS (
    SELECT
        expression.normalized_expression_key AS record_key,
        'ROUND2B_FROZEN_NORMALIZED_EXPRESSION'::TEXT AS corpus_layer,
        pipeline.language_tag_code AS language_code,
        expression.normalized_text AS representative_source_phrase,
        expression.normalized_text AS normalized_expression,
        'UNRESOLVED'::TEXT AS expression_role,
        'HISTORICAL_FROZEN'::TEXT AS review_state,
        'family.baseline.firstbloom-industry'::TEXT
            AS language_source_family_key,
        NULL::TEXT AS language_source_key,
        NULL::TEXT AS language_document_key,
        NULL::TEXT AS source_locator,
        NULL::TEXT AS public_raw_source_phrase,
        encode(sha256(convert_to(expression.normalized_text, 'UTF8')), 'hex')
            AS raw_source_phrase_sha256,
        FALSE AS counts_as_new_contemporary_document,
        FALSE AS counts_as_zh_hans_document,
        TRUE AS counts_toward_governed_total,
        FALSE AS counts_as_zh_hans_sensory_expression,
        'Frozen Round 2B normalized baseline; no raw text is exposed.'::TEXT
            AS limitation
    FROM corpus.normalized_expression AS expression
    JOIN corpus.normalization_pipeline AS pipeline
      ON pipeline.normalization_pipeline_id = expression.normalization_pipeline_id
    WHERE pipeline.frozen_at IS NOT NULL
)
SELECT * FROM legacy_rows
UNION ALL
SELECT * FROM round3i_rows;

COMMENT ON VIEW corpus.v_current_language_corpus IS
    'Frozen Round 2B normalized inventory plus release-member Round 3I observed language; rejected, quarantined, deprecated, unreviewed, and rights-blocked rows are excluded.';

CREATE VIEW kb.v_current_canonical_concept AS
SELECT * FROM kb.v_current_canonical_ontology;

CREATE VIEW kb.v_current_lexical_evidence AS
SELECT
    language.record_key AS lexical_evidence_key,
    language.corpus_layer,
    language.language_code,
    language.representative_source_phrase,
    language.normalized_expression,
    language.expression_role,
    language.review_state,
    resolution.resolution_status,
    resolution.concept_key,
    resolution.concept_type_code,
    language.language_source_family_key,
    language.language_source_key,
    language.language_document_key,
    language.source_locator,
    language.limitation
FROM corpus.v_current_language_corpus AS language
LEFT JOIN kb.v_lexical_resolution AS resolution
  ON resolution.language_tag_code = language.language_code
 AND resolution.normalized_text = language.normalized_expression;

CREATE VIEW context.v_current_context AS
SELECT cell.*
FROM audit.model_prebuild_context_cell AS cell
JOIN evidence.source_family AS family
  ON family.source_family_key = cell.source_family_key
 AND family.admitted
WHERE cell.evidence_status = 'OBSERVED_SOURCE_LOCAL_EVIDENCE'
  AND NOT cell.zero_filled;

CREATE VIEW evidence.v_current_sensory_partition AS
SELECT partition.*
FROM evidence.v_model_prebuild_source_partitions AS partition
WHERE partition.future_training_surface_status =
      'ELIGIBLE_AFTER_FUTURE_PROTOCOL';

CREATE VIEW evidence.v_current_relationship_evidence AS
SELECT claim.*
FROM evidence.relationship_evidence_claim AS claim
JOIN evidence.relationship_source AS source
  ON source.source_key = claim.source_key
 AND source.source_family_key = claim.source_family_key
 AND source.admitted
JOIN evidence.relationship_source_snapshot AS snapshot
  ON snapshot.snapshot_key = claim.snapshot_key
 AND snapshot.source_key = claim.source_key
 AND snapshot.source_family_key = claim.source_family_key
 AND snapshot.admitted
WHERE claim.review_status = 'REVIEWED'
  AND claim.evidence_direction IN ('SUPPORTS', 'CHALLENGES', 'MIXED');

CREATE VIEW calibration.v_current_question_evidence AS
SELECT evidence.*
FROM calibration.v_model_prebuild_question_evidence AS evidence
WHERE evidence.research_decision = 'RESEARCH_SUPPORT_ADDED'
  AND NOT EXISTS (
      SELECT 1
      FROM unnest(evidence.supporting_source_families) AS key(source_family_key)
      LEFT JOIN evidence.source_family AS family
        ON family.source_family_key = key.source_family_key
       AND family.admitted
      WHERE family.source_family_key IS NULL
  );

CREATE VIEW evidence.v_current_model_prebuild_feature AS
SELECT
    definition.feature_key,
    definition.semantics,
    definition.source_method,
    definition.data_type,
    definition.unit,
    definition.missingness_semantics,
    definition.harmonization_status AS definition_harmonization_status,
    definition.model_use_status,
    feature.partition_key,
    feature.availability_status,
    feature.source_field_locator,
    feature.harmonization_status AS partition_harmonization_status,
    feature.pooling_allowed,
    definition.limitation
FROM evidence.model_prebuild_feature_definition AS definition
JOIN evidence.model_prebuild_partition_feature AS feature
  ON feature.feature_key = definition.feature_key
JOIN evidence.model_prebuild_source_partition AS partition
  ON partition.partition_key = feature.partition_key
WHERE definition.model_use_status = 'PREBUILD_ONLY'
  AND definition.harmonization_status <> 'UNRESOLVED'
  AND feature.harmonization_status NOT IN ('NOT_COMPATIBLE', 'UNRESOLVED')
  AND partition.future_training_surface_status =
      'ELIGIBLE_AFTER_FUTURE_PROTOCOL';

INSERT INTO audit.research_database_current_surface (
    freeze_version, surface_key, surface_role, database_object_name,
    object_definition_sha256, lifecycle_status,
    approved_for_future_prebuild, required_for_freeze,
    supersedes_object_name, contract_note
)
SELECT
    release.freeze_version,
    'round3i.current.' || lower(replace(surface.surface_role, '_', '-')),
    surface.surface_role,
    surface.database_object_name,
    encode(sha256(convert_to(
        pg_get_viewdef(to_regclass(surface.database_object_name), TRUE),
        'UTF8')), 'hex'),
    'CURRENT_APPROVED', TRUE, TRUE,
    surface.supersedes_object_name,
    'Round 3I current-only governed research surface.'
FROM audit.research_database_release AS release
CROSS JOIN (VALUES
    ('CANONICAL_CONCEPT', 'kb.v_current_canonical_concept',
     'kb.v_current_canonical_ontology'),
    ('LEXICAL_EVIDENCE', 'kb.v_current_lexical_evidence',
     'kb.v_lexical_resolution'),
    ('CONTEXT', 'context.v_current_context',
     'audit.v_model_prebuild_context_coverage'),
    ('SENSORY_PARTITION', 'evidence.v_current_sensory_partition',
     'evidence.v_model_prebuild_source_partitions'),
    ('LANGUAGE_CORPUS', 'corpus.v_current_language_corpus',
     'corpus.v_model_prebuild_language_inventory'),
    ('RELATIONSHIP_EVIDENCE', 'evidence.v_current_relationship_evidence',
     'audit.v_model_prebuild_relationship_delta'),
    ('QUESTION_EVIDENCE', 'calibration.v_current_question_evidence',
     'calibration.v_model_prebuild_question_evidence'),
    ('MODEL_PREBUILD_FEATURE', 'evidence.v_current_model_prebuild_feature',
     'evidence.v_model_prebuild_feature_availability')
) AS surface(surface_role, database_object_name, supersedes_object_name)
WHERE release.freeze_version = 'coffee-sensory-research-db-v0.1.0';

INSERT INTO audit.research_database_current_surface (
    freeze_version, surface_key, surface_role, database_object_name,
    object_definition_sha256, lifecycle_status,
    approved_for_future_prebuild, required_for_freeze,
    supersedes_object_name, contract_note
)
SELECT
    release.freeze_version,
    'round3i.deprecated.' || replace(object.object_name, '.', '-'),
    NULL, object.object_name,
    encode(sha256(convert_to(
        pg_get_viewdef(to_regclass(object.object_name), TRUE), 'UTF8')), 'hex'),
    'DEPRECATED_RESEARCH', FALSE, FALSE, NULL,
    'Superseded research surface retained for historical reproducibility only.'
FROM audit.research_database_release AS release
CROSS JOIN (VALUES
    ('kb.v_current_canonical_ontology'), ('kb.v_lexical_resolution'),
    ('audit.v_model_prebuild_context_coverage'),
    ('evidence.v_model_prebuild_source_partitions'),
    ('corpus.v_model_prebuild_language_inventory'),
    ('audit.v_model_prebuild_relationship_delta'),
    ('calibration.v_model_prebuild_question_evidence'),
    ('evidence.v_model_prebuild_feature_availability')
) AS object(object_name)
WHERE release.freeze_version = 'coffee-sensory-research-db-v0.1.0';

CREATE VIEW audit.v_current_research_database_surface AS
SELECT surface.*, release.lifecycle_status AS release_lifecycle_status
FROM audit.research_database_current_surface AS surface
JOIN audit.research_database_release AS release
  ON release.freeze_version = surface.freeze_version
WHERE surface.lifecycle_status = 'CURRENT_APPROVED'
  AND surface.approved_for_future_prebuild;

CREATE FUNCTION audit.guard_frozen_current_view_ddl()
RETURNS event_trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_current_view_ddl$
DECLARE command RECORD;
BEGIN
    FOR command IN SELECT * FROM pg_event_trigger_ddl_commands() LOOP
        IF command.object_type = 'view' AND EXISTS (
            SELECT 1
            FROM audit.research_database_current_surface AS surface
            JOIN audit.research_database_release_attestation AS attestation
              ON attestation.freeze_version = surface.freeze_version
            WHERE surface.database_object_name = command.object_identity
              AND surface.lifecycle_status = 'CURRENT_APPROVED'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'research_database_frozen_current_view_immutable_ck',
                MESSAGE = 'a frozen current view definition is immutable';
        END IF;
    END LOOP;
END;
$guard_frozen_current_view_ddl$;

CREATE EVENT TRIGGER round3i_frozen_current_view_ddl
ON ddl_command_end
WHEN TAG IN ('CREATE VIEW', 'ALTER VIEW')
EXECUTE FUNCTION audit.guard_frozen_current_view_ddl();

CREATE FUNCTION audit.guard_frozen_current_view_drop()
RETURNS event_trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_current_view_drop$
DECLARE dropped RECORD;
BEGIN
    FOR dropped IN SELECT * FROM pg_event_trigger_dropped_objects() LOOP
        IF dropped.object_type = 'view' AND EXISTS (
            SELECT 1
            FROM audit.research_database_current_surface AS surface
            JOIN audit.research_database_release_attestation AS attestation
              ON attestation.freeze_version = surface.freeze_version
            WHERE surface.database_object_name = dropped.object_identity
              AND surface.lifecycle_status = 'CURRENT_APPROVED'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'research_database_frozen_current_view_immutable_ck',
                MESSAGE = 'a frozen current view cannot be dropped';
        END IF;
    END LOOP;
END;
$guard_frozen_current_view_drop$;

CREATE EVENT TRIGGER round3i_frozen_current_view_drop
ON sql_drop EXECUTE FUNCTION audit.guard_frozen_current_view_drop();

COMMIT;
