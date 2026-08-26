\set ON_ERROR_STOP on

-- Round 3I release candidate, deterministic artifact registry, and final gates.
BEGIN;

ALTER TABLE corpus.language_source
    ADD COLUMN row_count_unit TEXT,
    ADD COLUMN raw_row_count INTEGER,
    ADD COLUMN admitted_row_count INTEGER,
    ADD COLUMN excluded_row_count INTEGER;

WITH source_counts(
    language_source_key, row_count_unit,
    raw_row_count, admitted_row_count, excluded_row_count
) AS (VALUES
    ('dryad.cotter-v4', 'reviewed_candidate_sensory_occurrence_or_cell', 54162, 10763, 43399),
    ('figshare.bollen-2024', 'reviewed_candidate_sensory_occurrence_or_cell', 760, 530, 230),
    ('pmc.vezzulli-2022', 'reviewed_candidate_sensory_occurrence_or_cell', 152, 151, 1),
    ('github.firstbloom-data.a6cb0026', 'reviewed_candidate_sensory_occurrence_or_cell', 4827, 1058, 3769),
    ('zhangdeweb_junru_zhang_tasting_notes', 'reviewed_candidate_sensory_occurrence_or_cell', 230, 230, 0),
    ('rinzemoon_lengcui_lingshiyue', 'reviewed_candidate_sensory_occurrence_or_cell', 23, 23, 0)
)
UPDATE corpus.language_source AS source
SET row_count_unit = source_counts.row_count_unit,
    raw_row_count = source_counts.raw_row_count,
    admitted_row_count = source_counts.admitted_row_count,
    excluded_row_count = source_counts.excluded_row_count
FROM source_counts
WHERE source.language_source_key = source_counts.language_source_key;

ALTER TABLE corpus.language_source
    ALTER COLUMN row_count_unit SET NOT NULL,
    ALTER COLUMN raw_row_count SET NOT NULL,
    ALTER COLUMN admitted_row_count SET NOT NULL,
    ALTER COLUMN excluded_row_count SET NOT NULL,
    ADD CONSTRAINT language_source_row_accounting_ck CHECK (
        row_count_unit = btrim(row_count_unit) AND row_count_unit <> ''
        AND raw_row_count >= 0
        AND admitted_row_count >= 0
        AND excluded_row_count >= 0
        AND raw_row_count = admitted_row_count + excluded_row_count
        AND (NOT admitted OR admitted_row_count > 0)
    );

INSERT INTO audit.research_database_release (
    freeze_version, lifecycle_status, source_checkpoint_sha,
    final_repository_sha, final_repository_ref,
    release_tag_target_sha, release_tag_object_sha,
    manifest_path, manifest_sha256, expected_state_commit_sha,
    release_tag, supersedes_freeze_version, created_on, frozen_on,
    limitation
) VALUES (
    'coffee-sensory-research-db-v0.1.0', 'FREEZE_CANDIDATE',
    'ccf5769cb5e1f165209e59beaef9fe54017265f5',
    NULL, NULL, NULL, NULL,
    'db/data/freeze/coffee-sensory-research-db-v0/FREEZE_MANIFEST.json',
    '10ed5e29972082bc5046e6fb9c14be3f24b103a94a79c2482e5cd4819aa3991e',
    '602624143fef8fa4250e5e84f07478101b0846ff',
    'coffee-sensory-research-db-v0.1.0', NULL, DATE '2026-08-26', NULL,
    'The release candidate contains governed research data and metadata only; final main-branch and annotated-tag identities are supplied by post-commit attestation.'
);

SELECT audit.refresh_research_database_release_members(
    'coffee-sensory-research-db-v0.1.0'
);

INSERT INTO audit.research_database_current_surface (
    freeze_version, surface_key, surface_role, database_object_name,
    object_definition_sha256, lifecycle_status,
    approved_for_future_prebuild, required_for_freeze,
    supersedes_object_name, contract_note
)
SELECT
    'coffee-sensory-research-db-v0.1.0',
    'round3i.current.' || lower(replace(surface.surface_role, '_', '-')),
    surface.surface_role, surface.database_object_name,
    encode(sha256(convert_to(
        pg_get_viewdef(to_regclass(surface.database_object_name), TRUE),
        'UTF8')), 'hex'),
    'CURRENT_APPROVED', TRUE, TRUE, surface.supersedes_object_name,
    'Round 3I current-only governed research surface.'
FROM (VALUES
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
) AS surface(surface_role, database_object_name, supersedes_object_name);

INSERT INTO audit.research_database_current_surface (
    freeze_version, surface_key, surface_role, database_object_name,
    object_definition_sha256, lifecycle_status,
    approved_for_future_prebuild, required_for_freeze,
    supersedes_object_name, contract_note
)
SELECT
    'coffee-sensory-research-db-v0.1.0',
    'round3i.deprecated.' || replace(object.object_name, '.', '-'),
    NULL, object.object_name,
    encode(sha256(convert_to(
        pg_get_viewdef(to_regclass(object.object_name), TRUE), 'UTF8')), 'hex'),
    'DEPRECATED_RESEARCH', FALSE, FALSE, NULL,
    'Superseded research surface retained for historical reproducibility only.'
FROM (VALUES
    ('kb.v_current_canonical_ontology'),
    ('kb.v_lexical_resolution'),
    ('audit.v_model_prebuild_context_coverage'),
    ('evidence.v_model_prebuild_source_partitions'),
    ('corpus.v_model_prebuild_language_inventory'),
    ('audit.v_model_prebuild_relationship_delta'),
    ('calibration.v_model_prebuild_question_evidence'),
    ('evidence.v_model_prebuild_feature_availability')
) AS object(object_name);

INSERT INTO audit.research_database_artifact_hash (
    freeze_version, artifact_key, artifact_type, artifact_path,
    sha256, verified_sha256, hash_verified, database_derived,
    required_for_freeze, hash_semantics
)
SELECT
    'coffee-sensory-research-db-v0.1.0', artifact_key, artifact_type,
    'db/data/freeze/coffee-sensory-research-db-v0/' || filename,
    artifact_sha256, artifact_sha256, TRUE, database_derived, TRUE,
    CASE WHEN artifact_type = 'FREEZE_MANIFEST'
      THEN 'SHA-256 of exact UTF-8 manifest bytes; the manifest intentionally excludes its own digest.'
      ELSE 'SHA-256 of exact deterministic PostgreSQL TSV export bytes.' END
FROM (VALUES
    ('round3i.freeze.canonical-inventory', 'CANONICAL_INVENTORY',
     'CANONICAL_INVENTORY.tsv', '5370b37e46b2e38e978633c69d027e94f04d39b2355062cc69f455a4c5abe715', TRUE),
    ('round3i.freeze.source-inventory', 'SOURCE_INVENTORY',
     'SOURCE_INVENTORY.tsv', '37263bd203e736aa2832f5a090dc25afd07610b07ac63965e0874d6be9b16363', TRUE),
    ('round3i.freeze.raw-file-manifest', 'RAW_FILE_MANIFEST',
     'RAW_FILE_MANIFEST.tsv', '36acdc2f2a49642bbd0609e1b51f136d94ac62ee8fa9995ca3d06ee6038764f1', TRUE),
    ('round3i.freeze.sensory-inventory', 'SENSORY_INVENTORY',
     'SENSORY_INVENTORY.tsv', '1de3f11919ee264a7bafffd491522c4eb161b9649c2019dc034bf67e87b495f3', TRUE),
    ('round3i.freeze.context-coverage', 'CONTEXT_COVERAGE',
     'CONTEXT_COVERAGE.tsv', '3a17d6d2db7e6499a6dc13c1a59e96898c6c135dcd2a8d13034aeb251a7cfc68', TRUE),
    ('round3i.freeze.language-corpus', 'LANGUAGE_CORPUS',
     'LANGUAGE_CORPUS.tsv', 'b5509f8d60cea90a76421a7fad489be10456d2ccb8c66ef0bc135acf02fbbb02', TRUE),
    ('round3i.freeze.relationship-evidence', 'RELATIONSHIP_EVIDENCE',
     'RELATIONSHIP_EVIDENCE.tsv', '8565053a83f369b8dbd627f315d6ec82f5bf4a06a8c4ad5a58a14395eb53ccb2', TRUE),
    ('round3i.freeze.question-evidence', 'QUESTION_EVIDENCE',
     'QUESTION_EVIDENCE.tsv', '17ff588f8452a85805dc34a2dfae4a1844fa0d6c733c4885a7832996e341ff24', TRUE),
    ('round3i.freeze.feature-registry', 'FEATURE_REGISTRY',
     'FEATURE_REGISTRY.tsv', '2691f475037976d51104e4007d6b6cc9aa138b0e730621994617bfc6b4577ef6', TRUE),
    ('round3i.freeze.source-partition', 'SOURCE_PARTITION',
     'SOURCE_PARTITION.tsv', '978a494af8e534633768c75fd5844394f53e2445a6ad523c69afa7eb6890ac10', TRUE),
    ('round3i.freeze.manifest', 'FREEZE_MANIFEST',
     'FREEZE_MANIFEST.json', '10ed5e29972082bc5046e6fb9c14be3f24b103a94a79c2482e5cd4819aa3991e', FALSE)
) AS artifact(
    artifact_key, artifact_type, filename, artifact_sha256, database_derived
);

CREATE TABLE audit.round3i_execution_baseline (
    baseline_key TEXT NOT NULL PRIMARY KEY,
    model_run_count INTEGER NOT NULL,
    model_version_count INTEGER NOT NULL,
    embedding_configuration_count INTEGER NOT NULL,
    captured_on DATE NOT NULL,
    CONSTRAINT round3i_execution_baseline_ck CHECK (
        baseline_key = 'round3i.research-database-freeze'
        AND model_run_count >= 0 AND model_version_count >= 0
        AND embedding_configuration_count >= 0
        AND captured_on = DATE '2026-08-26'
    )
);

INSERT INTO audit.round3i_execution_baseline (
    baseline_key, model_run_count, model_version_count,
    embedding_configuration_count, captured_on
)
SELECT
    'round3i.research-database-freeze',
    (SELECT count(*) FROM ml.model_run),
    (SELECT count(*) FROM ml.model_version),
    (SELECT count(*) FROM ml.model_version
     WHERE coalesce((configuration ->> 'embeddings')::BOOLEAN, FALSE)),
    DATE '2026-08-26';

CREATE FUNCTION audit.prevent_round3i_model_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3i_model_run$
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit.research_database_release
        WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3i_model_run_prohibited_ck',
            MESSAGE = 'the frozen research database cannot create or mutate model runs';
    END IF;
    RETURN NEW;
END;
$prevent_round3i_model_run$;

CREATE CONSTRAINT TRIGGER round3i_model_run_prohibited_biu
AFTER INSERT OR UPDATE ON ml.model_run
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3i_model_run();

CREATE FUNCTION audit.prevent_round3i_model_version()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3i_model_version$
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit.research_database_release
        WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3i_model_version_prohibited_ck',
            MESSAGE = 'the frozen research database cannot create model or embedding versions';
    END IF;
    RETURN NEW;
END;
$prevent_round3i_model_version$;

CREATE CONSTRAINT TRIGGER round3i_model_version_prohibited_biu
AFTER INSERT OR UPDATE ON ml.model_version
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3i_model_version();

CREATE TABLE audit.research_database_reproducibility_attestation (
    freeze_version TEXT NOT NULL PRIMARY KEY,
    clean_rebuild_count INTEGER NOT NULL,
    postgresql_major INTEGER NOT NULL,
    freeze_artifact_count INTEGER NOT NULL,
    hashes_match_across_rebuilds BOOLEAN NOT NULL,
    committed_artifacts_match BOOLEAN NOT NULL,
    evidence_path TEXT NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT research_database_reproducibility_release_fk FOREIGN KEY (
        freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_reproducibility_attestation_ck CHECK (
        clean_rebuild_count = 2 AND postgresql_major = 17
        AND freeze_artifact_count = 11
        AND hashes_match_across_rebuilds AND committed_artifacts_match
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
    )
);

CREATE FUNCTION audit.prevent_reproducibility_attestation_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_reproducibility_attestation_mutation$
BEGIN
    RAISE EXCEPTION USING ERRCODE = '23514',
        CONSTRAINT = 'research_database_reproducibility_attestation_immutable_ck',
        MESSAGE = 'external two-rebuild evidence is immutable';
END;
$prevent_reproducibility_attestation_mutation$;

CREATE TRIGGER research_database_reproducibility_attestation_bud
BEFORE UPDATE OR DELETE ON audit.research_database_reproducibility_attestation
FOR EACH ROW EXECUTE FUNCTION audit.prevent_reproducibility_attestation_mutation();

CREATE VIEW audit.v_round3i_source_governance_completeness AS
SELECT
    count(*)::INTEGER AS admitted_source_count,
    count(*) FILTER (WHERE
        title <> '' AND authors_or_owner <> ''
        AND publication_year IS NOT NULL AND doi_or_stable_url <> ''
        AND repository <> '' AND exact_version <> ''
        AND access_date IS NOT NULL AND license_expression <> ''
        AND rights_basis <> '' AND privacy_decision <> ''
        AND jsonb_array_length(source_file_manifest) > 0
        AND source_file_hash_complete
        AND row_count_unit <> ''
        AND raw_row_count = admitted_row_count + excluded_row_count
        AND cardinality(language_codes) > 0 AND geography <> ''
        AND data_type <> '' AND evidence_role <> '' AND limitations <> ''
        AND annotation_complete
    )::INTEGER AS fully_annotated_source_count,
    count(*) FILTER (WHERE
        rights_review_complete
        AND derived_expression_internal_use = 'ALLOW'
        AND derived_counts_internal_use = 'ALLOW'
        AND model_research_use = 'ALLOW'
    )::INTEGER AS rights_complete_source_count,
    count(*) FILTER (WHERE privacy_review_complete)::INTEGER
        AS privacy_complete_source_count,
    count(*) FILTER (WHERE
        source_file_hash_complete
        AND corpus.language_source_manifest_is_complete(source_file_manifest)
    )::INTEGER AS file_hash_complete_source_count
FROM corpus.language_source
WHERE admitted;

CREATE VIEW audit.v_round3i_relationship_provenance_completeness AS
SELECT
    count(*)::INTEGER AS reviewed_claim_count,
    count(*) FILTER (WHERE
        source.admitted AND snapshot.admitted
        AND EXISTS (
            SELECT 1 FROM evidence.relationship_source_file AS file
            WHERE file.snapshot_key = claim.snapshot_key
              AND file.source_key = claim.source_key
              AND file.source_family_key = claim.source_family_key
              AND file.hash_verified
              AND file.declared_sha256 = file.verified_sha256
        )
    )::INTEGER AS provenance_complete_claim_count
FROM evidence.relationship_evidence_claim AS claim
JOIN evidence.relationship_source AS source
  ON source.source_key = claim.source_key
 AND source.source_family_key = claim.source_family_key
JOIN evidence.relationship_source_snapshot AS snapshot
  ON snapshot.snapshot_key = claim.snapshot_key
 AND snapshot.source_key = claim.source_key
 AND snapshot.source_family_key = claim.source_family_key
WHERE claim.review_status = 'REVIEWED';

ALTER FUNCTION audit.run_model_prebuild_readiness_gate()
RENAME TO run_round3h_model_prebuild_readiness_gate;

CREATE FUNCTION audit.run_model_prebuild_readiness_gate()
RETURNS TABLE (
    readiness_key TEXT, minimum_required TEXT, preferred_required TEXT,
    observed TEXT, hard_gate BOOLEAN, passed BOOLEAN,
    evidence_path TEXT, limitation TEXT
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_model_prebuild_readiness_gate$
WITH language_counts AS (
    SELECT
      (SELECT count(*) FROM corpus.language_source_family
       WHERE counts_as_new_contemporary_family)::INTEGER AS contemporary_families,
      (SELECT count(*) FROM corpus.language_document
       WHERE counts_as_new_contemporary_document)::INTEGER AS contemporary_documents,
      (SELECT count(*) FROM (
          SELECT normalized_text FROM corpus.normalized_expression
          UNION
          SELECT normalized_expression FROM corpus.language_expression
          WHERE counts_toward_governed_total
       ) AS governed)::INTEGER AS governed_expressions,
      (SELECT count(*) FROM corpus.language_source_family
       WHERE counts_as_zh_hans_family)::INTEGER AS zh_hans_families,
      (SELECT count(*) FROM corpus.language_expression
       WHERE counts_as_zh_hans_sensory_expression)::INTEGER AS zh_hans_expressions
), gates AS (
    SELECT *
    FROM audit.run_round3h_model_prebuild_readiness_gate()
    WHERE readiness_key NOT LIKE 'language.%'
    UNION ALL
    SELECT 'language.contemporary_source_family_count', '3', '5',
        contemporary_families::TEXT, TRUE, contemporary_families >= 3,
        'corpus.language_source_family',
        'Independent source-authored contemporary tasting-language families only.'
    FROM language_counts
    UNION ALL
    SELECT 'language.new_contemporary_document_count', '500', '1500',
        contemporary_documents::TEXT, TRUE, contemporary_documents >= 500,
        'corpus.language_document',
        'Only source-authored observed tasting-language documents count.'
    FROM language_counts
    UNION ALL
    SELECT 'language.unique_expression_count', '2500', '3500',
        governed_expressions::TEXT, TRUE, governed_expressions >= 2500,
        'corpus.normalized_expression + corpus.language_expression',
        'Globally de-duplicated governed observed expressions only.'
    FROM language_counts
    UNION ALL
    SELECT 'language.zh_hans_source_family_count', '2', '3',
        zh_hans_families::TEXT, TRUE, zh_hans_families >= 2,
        'corpus.language_source_family',
        'Machine translation and artificial variants do not establish a family.'
    FROM language_counts
    UNION ALL
    SELECT 'language.zh_hans_sensory_expression_count', '0', '200',
        zh_hans_expressions::TEXT, FALSE, zh_hans_expressions >= 200,
        'corpus.language_expression',
        'Preferred source-authored Simplified-Chinese sensory depth.'
    FROM language_counts
)
SELECT * FROM gates ORDER BY readiness_key
$run_model_prebuild_readiness_gate$;

CREATE OR REPLACE VIEW audit.v_model_prebuild_readiness_gate AS
SELECT * FROM audit.run_model_prebuild_readiness_gate();

CREATE OR REPLACE FUNCTION audit.model_prebuild_readiness_state()
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $model_prebuild_readiness_state$
SELECT CASE
    WHEN NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'governance.rights') THEN 'BLOCKED_RIGHTS'
    WHEN NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'governance.hashes')
      OR NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'quality.explicit_missingness_and_harmonization')
      OR NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'analysis.manifest') THEN 'BLOCKED_REPRODUCIBILITY'
    WHEN NOT EXISTS (
        SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
        WHERE hard_gate AND NOT passed
    ) AND (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'milk.sensory_outcome_source_family_count')
      THEN 'MODEL_PREBUILD_READY'
    WHEN NOT EXISTS (
        SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
        WHERE hard_gate AND NOT passed
    ) THEN 'MODEL_PREBUILD_READY_BLACK_COFFEE_ONLY'
    ELSE 'COMPLETE_WITH_DATA_COVERAGE_GAP'
END
$model_prebuild_readiness_state$;

CREATE FUNCTION audit.model_prebuild_data_ready()
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $model_prebuild_data_ready$
SELECT NOT EXISTS (
    SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
    WHERE hard_gate AND NOT passed
)
$model_prebuild_data_ready$;

INSERT INTO audit.model_prebuild_readiness_assertion (
    assertion_key, model_prebuild_data_ready, readiness_state,
    asserted_at, evidence_path
) VALUES (
    'assertion.round3i.research-database-freeze', TRUE,
    audit.model_prebuild_readiness_state(),
    TIMESTAMPTZ '2026-08-26 02:00:00+00',
    'audit.run_model_prebuild_readiness_gate()'
);

CREATE FUNCTION audit.run_research_database_freeze_gate()
RETURNS TABLE (
    freeze_gate_key TEXT, required TEXT, observed TEXT, passed BOOLEAN,
    severity TEXT, evidence_path TEXT, limitation TEXT
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_research_database_freeze_gate$
WITH language_counts AS (
    SELECT
      (SELECT count(*) FROM corpus.language_source_family
       WHERE counts_as_new_contemporary_family)::INTEGER AS contemporary_families,
      (SELECT count(*) FROM corpus.language_document
       WHERE counts_as_new_contemporary_document)::INTEGER AS contemporary_documents,
      (SELECT count(*) FROM (
          SELECT normalized_text FROM corpus.normalized_expression
          UNION
          SELECT normalized_expression FROM corpus.language_expression
          WHERE counts_toward_governed_total
       ) AS governed)::INTEGER AS governed_expressions,
      (SELECT count(*) FROM corpus.language_source_family
       WHERE counts_as_zh_hans_family)::INTEGER AS zh_hans_families,
      (SELECT count(*) FROM corpus.language_expression
       WHERE counts_as_zh_hans_sensory_expression)::INTEGER AS zh_hans_expressions
), source_governance AS (
    SELECT * FROM audit.v_round3i_source_governance_completeness
), relationship_provenance AS (
    SELECT * FROM audit.v_round3i_relationship_provenance_completeness
), legacy_validation AS (
    SELECT coalesce(sum(violation_count), 0)::BIGINT AS violation_count
    FROM (
      SELECT violation_count FROM audit.run_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round2a_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round2b_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3a_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3b_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3c_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3d_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3e_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3f_validation_queries()
      UNION ALL SELECT violation_count FROM audit.run_round3g_validation_queries()
    ) AS checks
), execution_delta AS (
    SELECT
      (SELECT count(*) FROM ml.model_run) - baseline.model_run_count
        AS model_run_delta,
      (SELECT count(*) FROM ml.model_version) - baseline.model_version_count
        AS model_version_delta,
      (SELECT count(*) FROM ml.model_version
       WHERE coalesce((configuration ->> 'embeddings')::BOOLEAN, FALSE))
        - baseline.embedding_configuration_count AS embedding_delta
    FROM audit.round3i_execution_baseline AS baseline
    WHERE baseline_key = 'round3i.research-database-freeze'
), reproducibility AS (
    SELECT EXISTS (
      SELECT 1 FROM audit.research_database_reproducibility_attestation
      WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
        AND clean_rebuild_count = 2 AND postgresql_major = 17
        AND freeze_artifact_count = 11
        AND hashes_match_across_rebuilds AND committed_artifacts_match
    ) AS externally_verified
), quality AS (
    SELECT
      (SELECT count(*) FROM kb.concept) AS canonical_count,
      (SELECT count(*) FROM kb.concept
       WHERE concept_type_code = 'sensory_attribute'
         AND lifecycle_status_code = 'active') AS active_sensory_count,
      (SELECT count(*) FROM corpus.language_expression_occurrence occurrence
       LEFT JOIN corpus.language_document document
         ON document.language_document_key = occurrence.language_document_key
       LEFT JOIN corpus.language_expression expression
         ON expression.language_expression_key = occurrence.language_expression_key
       WHERE document.language_document_key IS NULL
          OR expression.language_expression_key IS NULL) AS orphan_count,
      (SELECT count(*) FROM audit.model_prebuild_leakage_risk
       WHERE NOT audit_pass) AS leakage_failure_count,
      (SELECT count(*) FROM corpus.language_expression
       WHERE counts_toward_governed_total
         AND (machine_translated OR artificial_variant
              OR expression_role IN ('PREPARATION', 'ROAST'))) AS fake_gain_count,
      (SELECT count(*) FROM pg_constraint AS constraint_record
       JOIN pg_namespace AS namespace
         ON namespace.oid = constraint_record.connamespace
       WHERE namespace.nspname IN (
         'audit','calibration','context','corpus','evidence','kb','ml','ref'
       ) AND NOT constraint_record.convalidated) AS unvalidated_constraint_count
), gates(
    freeze_gate_key, required, observed, passed, severity,
    evidence_path, limitation
) AS (
    SELECT 'language.minimum.contemporary_source_families'::TEXT,
      '>=3', contemporary_families::TEXT, contemporary_families >= 3,
      'HARD'::TEXT, 'corpus.language_source_family'::TEXT,
      'Independent source-authored contemporary tasting-language families.'::TEXT
    FROM language_counts
    UNION ALL SELECT 'language.minimum.contemporary_documents', '>=500',
      contemporary_documents::TEXT, contemporary_documents >= 500, 'HARD',
      'corpus.language_document', 'Observed contemporary tasting documents.'
    FROM language_counts
    UNION ALL SELECT 'language.minimum.governed_unique_expressions', '>=2500',
      governed_expressions::TEXT, governed_expressions >= 2500, 'HARD',
      'corpus.normalized_expression + corpus.language_expression',
      'Globally de-duplicated governed observed expressions.'
    FROM language_counts
    UNION ALL SELECT 'language.minimum.zh_hans_source_families', '>=2',
      zh_hans_families::TEXT, zh_hans_families >= 2, 'HARD',
      'corpus.language_source_family', 'Independent source-authored zh-Hans families.'
    FROM language_counts
    UNION ALL SELECT 'language.preferred.contemporary_source_families', '>=5',
      contemporary_families::TEXT, contemporary_families >= 5, 'PREFERRED',
      'corpus.language_source_family', 'Preferred breadth; not a freeze blocker.'
    FROM language_counts
    UNION ALL SELECT 'language.preferred.contemporary_documents', '>=1500',
      contemporary_documents::TEXT, contemporary_documents >= 1500, 'PREFERRED',
      'corpus.language_document', 'Preferred document depth.'
    FROM language_counts
    UNION ALL SELECT 'language.preferred.governed_unique_expressions', '>=3500',
      governed_expressions::TEXT, governed_expressions >= 3500, 'PREFERRED',
      'corpus.language_expression', 'Preferred lexical breadth.'
    FROM language_counts
    UNION ALL SELECT 'language.preferred.zh_hans_source_families', '>=3',
      zh_hans_families::TEXT, zh_hans_families >= 3, 'PREFERRED',
      'corpus.language_source_family', 'Preferred zh-Hans origin breadth.'
    FROM language_counts
    UNION ALL SELECT 'language.preferred.zh_hans_sensory_expressions', '>=200',
      zh_hans_expressions::TEXT, zh_hans_expressions >= 200, 'PREFERRED',
      'corpus.language_expression', 'Preferred source-authored zh-Hans depth.'
    FROM language_counts
    UNION ALL SELECT 'governance.source_annotation_completeness', '=1.0000',
      round(fully_annotated_source_count::NUMERIC
            / NULLIF(admitted_source_count, 0), 4)::TEXT,
      admitted_source_count > 0
        AND fully_annotated_source_count = admitted_source_count,
      'HARD', 'audit.v_round3i_source_governance_completeness',
      'Every admitted language source includes identity, rights, file, row-count, language, geography, role, and limitation fields.'
    FROM source_governance
    UNION ALL SELECT 'governance.rights_review_completeness', '=1.0000',
      round(rights_complete_source_count::NUMERIC
            / NULLIF(admitted_source_count, 0), 4)::TEXT,
      admitted_source_count > 0
        AND rights_complete_source_count = admitted_source_count,
      'HARD', 'audit.v_round3i_source_governance_completeness',
      'Rights are evaluated separately for raw, derivative, counts, and model-research use.'
    FROM source_governance
    UNION ALL SELECT 'governance.privacy_review_completeness', '=1.0000',
      round(privacy_complete_source_count::NUMERIC
            / NULLIF(admitted_source_count, 0), 4)::TEXT,
      admitted_source_count > 0
        AND privacy_complete_source_count = admitted_source_count,
      'HARD', 'audit.v_round3i_source_governance_completeness',
      'Every admitted language source has an explicit privacy review.'
    FROM source_governance
    UNION ALL SELECT 'governance.source_file_hash_completeness', '=1.0000',
      round(file_hash_complete_source_count::NUMERIC
            / NULLIF(admitted_source_count, 0), 4)::TEXT,
      admitted_source_count > 0
        AND file_hash_complete_source_count = admitted_source_count,
      'HARD', 'audit.v_round3i_source_governance_completeness',
      'Every admitted language source has a complete locator and SHA-256 manifest.'
    FROM source_governance
    UNION ALL SELECT 'governance.relationship_provenance_completeness', '=1.0000',
      round(provenance_complete_claim_count::NUMERIC
            / NULLIF(reviewed_claim_count, 0), 4)::TEXT,
      reviewed_claim_count > 0
        AND provenance_complete_claim_count = reviewed_claim_count,
      'HARD', 'audit.v_round3i_relationship_provenance_completeness',
      'Every reviewed relationship claim resolves to an admitted immutable source snapshot and verified file.'
    FROM relationship_provenance
    UNION ALL SELECT 'quality.canonical_freeze', '130 concepts; 92 active sensory',
      canonical_count::TEXT || ' concepts; ' || active_sensory_count::TEXT || ' active sensory',
      canonical_count = 130 AND active_sensory_count = 92, 'HARD',
      'kb.concept', 'Round 3I makes no canonical additions, splits, or merges.'
    FROM quality
    UNION ALL SELECT 'quality.schema_integrity', '0 orphan rows',
      (orphan_count + unvalidated_constraint_count)::TEXT,
      orphan_count = 0 AND unvalidated_constraint_count = 0, 'HARD',
      'pg_constraint + corpus.language_expression_occurrence',
      'All governed constraints are validated and language occurrence foreign keys resolve.'
    FROM quality
    UNION ALL SELECT 'quality.data_quality_pass', '0 critical violations',
      (legacy_validation.violation_count + quality.orphan_count
       + quality.fake_gain_count + quality.leakage_failure_count)::TEXT,
      legacy_validation.violation_count = 0 AND quality.orphan_count = 0
       AND quality.fake_gain_count = 0 AND quality.leakage_failure_count = 0,
      'HARD',
      'audit.run_validation_queries() through audit.run_round3g_validation_queries() + Round 3I gates',
      'Round 3H exact end-state validation is executed at the immutable migration-044 checkpoint; forward validation uses current-state contracts.'
    FROM legacy_validation CROSS JOIN quality
    UNION ALL SELECT 'quality.no_fake_language_gain', '0',
      fake_gain_count::TEXT, fake_gain_count = 0, 'HARD',
      'corpus.language_expression', 'Machine translation, artificial variants, preparation, and roast terms cannot game the gate.'
    FROM quality
    UNION ALL SELECT 'quality.leakage_audit', '0 failed controls',
      leakage_failure_count::TEXT, leakage_failure_count = 0, 'HARD',
      'audit.model_prebuild_leakage_risk', 'No model split was run; all declared future controls pass.'
    FROM quality
    UNION ALL SELECT 'model_prebuild.data_ready', '=true',
      audit.model_prebuild_data_ready()::TEXT,
      audit.model_prebuild_data_ready(), 'HARD',
      'audit.run_model_prebuild_readiness_gate()',
      'Every mandatory model-prebuild data gate, including Round 3I language closure, passes.'
    UNION ALL SELECT 'model_prebuild.no_model_or_embedding_delta', '0/0/0',
      model_run_delta::TEXT || '/' || model_version_delta::TEXT || '/'
        || embedding_delta::TEXT,
      model_run_delta = 0 AND model_version_delta = 0 AND embedding_delta = 0,
      'HARD', 'audit.round3i_execution_baseline',
      'No model run, model version, or embedding artifact was added during the freeze round.'
    FROM execution_delta
    UNION ALL SELECT 'release.current_approved_surfaces', '=8', count(*)::TEXT,
      count(*) = 8, 'HARD', 'audit.research_database_current_surface',
      'Only eight versioned current surfaces are approved for future prebuild use.'
    FROM audit.research_database_current_surface
    WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
      AND lifecycle_status = 'CURRENT_APPROVED'
      AND approved_for_future_prebuild AND required_for_freeze
    UNION ALL SELECT 'release.verified_artifact_hashes', '=11', count(*)::TEXT,
      count(*) = 11, 'HARD', 'audit.research_database_artifact_hash',
      'Ten inventories plus one non-self-referential manifest are required.'
    FROM audit.research_database_artifact_hash
    WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
      AND required_for_freeze AND hash_verified AND sha256 = verified_sha256
    UNION ALL SELECT 'release.member_inventory_complete', '=true',
      audit.research_database_release_members_complete(
        'coffee-sensory-research-db-v0.1.0')::TEXT,
      audit.research_database_release_members_complete(
        'coffee-sensory-research-db-v0.1.0'),
      'HARD', 'audit.research_database_release_member',
      'All governed Round 3I language rows have stable membership hashes.'
    UNION ALL SELECT 'reproducibility.external_two_rebuild',
      '2 PostgreSQL 17 rebuilds; 11 hashes match committed artifacts',
      CASE WHEN externally_verified THEN 'VERIFIED' ELSE 'PENDING_EXTERNAL_CI' END,
      externally_verified, 'INFORMATIONAL',
      'db/scripts/rebuild-twice.sh + audit.research_database_reproducibility_attestation',
      'External evidence is intentionally not seeded by a migration; final release attestation requires it.'
    FROM reproducibility
    UNION ALL SELECT 'relationship.preferred.cross_source_ranges', '>=4',
      range_with_cross_source_evidence_count::TEXT,
      range_with_cross_source_evidence_count >= 4, 'PREFERRED',
      'audit.v_model_prebuild_relationship_delta',
      'Preferred corroboration; range membership lifecycle is not forced.'
    FROM audit.v_model_prebuild_relationship_delta
)
SELECT * FROM gates ORDER BY freeze_gate_key
$run_research_database_freeze_gate$;

CREATE VIEW audit.v_research_database_freeze_gate AS
SELECT * FROM audit.run_research_database_freeze_gate();

CREATE FUNCTION audit.research_database_freeze_state()
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $research_database_freeze_state$
SELECT CASE
  WHEN EXISTS (
    SELECT 1 FROM audit.run_research_database_freeze_gate()
    WHERE severity = 'HARD' AND NOT passed
      AND freeze_gate_key LIKE 'governance.rights%'
  ) THEN 'DATABASE_FREEZE_BLOCKED_BY_RIGHTS'
  WHEN EXISTS (
    SELECT 1 FROM audit.run_research_database_freeze_gate()
    WHERE severity = 'HARD' AND NOT passed
      AND freeze_gate_key LIKE 'governance.privacy%'
  ) THEN 'DATABASE_FREEZE_BLOCKED_BY_PRIVACY'
  WHEN EXISTS (
    SELECT 1 FROM audit.run_research_database_freeze_gate()
    WHERE severity = 'HARD' AND NOT passed
      AND freeze_gate_key LIKE 'language.%'
  ) THEN 'DATABASE_FREEZE_BLOCKED_BY_DATA_GAP'
  WHEN EXISTS (
    SELECT 1 FROM audit.run_research_database_freeze_gate()
    WHERE severity = 'HARD' AND NOT passed
  ) THEN 'DATABASE_FREEZE_BLOCKED_BY_INTEGRITY'
  WHEN EXISTS (
    SELECT 1 FROM audit.research_database_release
    WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
      AND lifecycle_status = 'FROZEN'
  ) THEN 'RESEARCH_DATABASE_V0_FROZEN'
  WHEN EXISTS (
    SELECT 1 FROM audit.run_research_database_freeze_gate()
    WHERE severity = 'PREFERRED' AND NOT passed
  ) THEN 'FREEZE_CANDIDATE_WITH_PREFERRED_GAPS'
  ELSE 'FREEZE_CANDIDATE_WITH_PREFERRED_GAPS'
END
$research_database_freeze_state$;

CREATE FUNCTION audit.assert_research_database_freeze_ready()
RETURNS VOID
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $assert_research_database_freeze_ready$
BEGIN
    IF NOT audit.model_prebuild_data_ready()
       OR NOT EXISTS (
           SELECT 1 FROM audit.run_research_database_freeze_gate()
       )
       OR EXISTS (
           SELECT 1 FROM audit.run_research_database_freeze_gate()
           WHERE severity = 'HARD' AND NOT passed
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3i_research_database_freeze_gate_ck',
            MESSAGE = 'a mandatory Round 3I research-database freeze gate failed';
    END IF;
END;
$assert_research_database_freeze_ready$;

CREATE FUNCTION audit.enforce_round3i_release_attestation_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3i_release_attestation_gate$
BEGIN
    IF NEW.freeze_version = 'coffee-sensory-research-db-v0.1.0' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM audit.research_database_reproducibility_attestation
            WHERE freeze_version = NEW.freeze_version
              AND clean_rebuild_count = 2 AND postgresql_major = 17
              AND freeze_artifact_count = 11
              AND hashes_match_across_rebuilds
              AND committed_artifacts_match
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3i_reproducibility_attestation_required_ck',
                MESSAGE = 'final attestation requires external two-rebuild evidence';
        END IF;
        PERFORM audit.assert_research_database_freeze_ready();
    END IF;
    RETURN NEW;
END;
$enforce_round3i_release_attestation_gate$;

CREATE TRIGGER research_database_round3i_hard_gate_bi
BEFORE INSERT ON audit.research_database_release_attestation
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3i_release_attestation_gate();

CREATE FUNCTION audit.prevent_round3i_freeze_artifact_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3i_freeze_artifact_mutation$
BEGIN
    IF OLD.freeze_version = 'coffee-sensory-research-db-v0.1.0' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3i_freeze_artifact_immutable_ck',
            MESSAGE = 'a registered Round 3I freeze artifact cannot be overwritten';
    END IF;
    RETURN OLD;
END;
$prevent_round3i_freeze_artifact_mutation$;

CREATE TRIGGER round3i_freeze_artifact_immutable_bud
BEFORE UPDATE OR DELETE ON audit.research_database_artifact_hash
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3i_freeze_artifact_mutation();

CREATE FUNCTION audit.enforce_round3i_freeze_version_hash_binding()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3i_freeze_version_hash_binding$
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit.research_database_release AS existing
        WHERE existing.freeze_version = NEW.freeze_version
          AND existing.manifest_sha256 <> NEW.manifest_sha256
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3i_freeze_version_hash_binding_ck',
            MESSAGE = 'one freeze version cannot bind to two manifest hashes';
    END IF;
    RETURN NEW;
END;
$enforce_round3i_freeze_version_hash_binding$;

CREATE TRIGGER research_database_release_version_hash_binding_bi
BEFORE INSERT ON audit.research_database_release
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3i_freeze_version_hash_binding();

DO $round3i_freeze_gate$
BEGIN
    PERFORM audit.assert_research_database_freeze_ready();
END;
$round3i_freeze_gate$;

COMMIT;
