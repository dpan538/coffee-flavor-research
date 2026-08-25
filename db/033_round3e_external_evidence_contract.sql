\set ON_ERROR_STOP on

-- Round 3E source-local evidence, corpus, question-research, and prohibition
-- contracts. External records remain outside canonical ontology tables.

BEGIN;

CREATE TABLE evidence.external_dataset_snapshot (
    dataset_snapshot_key TEXT NOT NULL,
    dataset_id BIGINT NOT NULL,
    source_version TEXT NOT NULL,
    file_hashes JSONB NOT NULL,
    declared_row_count INTEGER NOT NULL,
    verified_row_count INTEGER NOT NULL,
    declared_field_count INTEGER NOT NULL,
    verified_field_count INTEGER NOT NULL,
    imported_record_count INTEGER NOT NULL,
    exclusion_count INTEGER NOT NULL,
    import_version TEXT NOT NULL,
    import_code_sha TEXT NOT NULL,
    license_expression TEXT,
    rights_decision TEXT NOT NULL,
    privacy_decision TEXT NOT NULL,
    public_release_eligible BOOLEAN NOT NULL,
    created_on DATE NOT NULL,
    CONSTRAINT external_dataset_snapshot_pk PRIMARY KEY (
        dataset_snapshot_key
    ),
    CONSTRAINT external_dataset_snapshot_dataset_uq UNIQUE (dataset_id),
    CONSTRAINT external_dataset_snapshot_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT external_dataset_snapshot_key_ck CHECK (
        dataset_snapshot_key = lower(btrim(dataset_snapshot_key))
        AND dataset_snapshot_key <> ''
    ),
    CONSTRAINT external_dataset_snapshot_hashes_ck CHECK (
        jsonb_typeof(file_hashes) = 'object'
        AND file_hashes <> '{}'::JSONB
    ),
    CONSTRAINT external_dataset_snapshot_dimensions_ck CHECK (
        declared_row_count >= 0
        AND declared_row_count = verified_row_count
        AND declared_field_count > 0
        AND declared_field_count = verified_field_count
        AND imported_record_count >= 0
        AND exclusion_count >= 0
        AND imported_record_count + exclusion_count >= declared_row_count
    ),
    CONSTRAINT external_dataset_snapshot_text_ck CHECK (
        source_version = btrim(source_version) AND source_version <> ''
        AND import_version = btrim(import_version) AND import_version <> ''
        AND import_code_sha ~ '^[0-9a-f]{40}$'
        AND license_expression IS NOT NULL
        AND license_expression = btrim(license_expression)
        AND license_expression <> ''
        AND rights_decision IN (
            'IMPORT_RAW_AND_DERIVED', 'IMPORT_DERIVED_ONLY', 'METADATA_ONLY',
            'PRIVATE_RESEARCH_ONLY', 'REQUEST_PERMISSION', 'BLOCKED_RIGHTS',
            'BLOCKED_PRIVACY', 'NOT_RELEVANT'
        )
        AND privacy_decision = btrim(privacy_decision)
        AND privacy_decision <> ''
    ),
    CONSTRAINT external_dataset_snapshot_public_rights_ck CHECK (
        NOT public_release_eligible
        OR rights_decision IN ('IMPORT_RAW_AND_DERIVED', 'IMPORT_DERIVED_ONLY')
    )
);

CREATE TABLE evidence.external_source_file (
    dataset_snapshot_key TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    file_role TEXT NOT NULL,
    declared_sha256 TEXT NOT NULL,
    observed_sha256 TEXT NOT NULL,
    declared_row_count INTEGER NOT NULL,
    declared_field_count INTEGER NOT NULL,
    included_row_count INTEGER NOT NULL,
    exclusion_count INTEGER NOT NULL,
    counts_toward_snapshot BOOLEAN NOT NULL,
    raw_public_export_allowed BOOLEAN NOT NULL,
    pii_scan_pass BOOLEAN NOT NULL,
    CONSTRAINT external_source_file_pk PRIMARY KEY (
        dataset_snapshot_key, source_file_path
    ),
    CONSTRAINT external_source_file_snapshot_fk FOREIGN KEY (
        dataset_snapshot_key
    ) REFERENCES evidence.external_dataset_snapshot (dataset_snapshot_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT external_source_file_hash_ck CHECK (
        declared_sha256 ~ '^[0-9a-f]{64}$'
        AND declared_sha256 = observed_sha256
    ),
    CONSTRAINT external_source_file_value_ck CHECK (
        source_file_path = btrim(source_file_path) AND source_file_path <> ''
        AND file_role IN ('source_data', 'repository_file_inventory')
        AND declared_row_count >= 0 AND declared_field_count > 0
        AND included_row_count >= 0 AND exclusion_count >= 0
        AND included_row_count + exclusion_count <= declared_row_count
    )
);

CREATE FUNCTION evidence.enforce_external_file_export_policy()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_external_file_export_policy$
DECLARE
    snapshot_public BOOLEAN;
BEGIN
    SELECT snapshot.public_release_eligible INTO STRICT snapshot_public
    FROM evidence.external_dataset_snapshot AS snapshot
    WHERE snapshot.dataset_snapshot_key = NEW.dataset_snapshot_key;

    IF NEW.raw_public_export_allowed AND NOT snapshot_public THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'external_source_file_public_export_ck',
            MESSAGE = 'blocked external raw text cannot be marked for public export';
    END IF;
    RETURN NEW;
END
$enforce_external_file_export_policy$;

CREATE TRIGGER external_source_file_public_export_trg
BEFORE INSERT OR UPDATE ON evidence.external_source_file
FOR EACH ROW EXECUTE FUNCTION evidence.enforce_external_file_export_policy();

CREATE TABLE evidence.external_field_dictionary (
    external_field_dictionary_id BIGINT GENERATED ALWAYS AS IDENTITY,
    dataset_snapshot_key TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_local_column_name TEXT NOT NULL,
    project_field_key TEXT NOT NULL,
    source_local_unit TEXT NOT NULL,
    normalization_rule TEXT NOT NULL,
    unit_conversion_applied BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT external_field_dictionary_pk PRIMARY KEY (
        external_field_dictionary_id
    ),
    CONSTRAINT external_field_dictionary_uq UNIQUE (
        dataset_snapshot_key, source_file_path, source_local_column_name,
        project_field_key
    ),
    CONSTRAINT external_field_dictionary_file_fk FOREIGN KEY (
        dataset_snapshot_key, source_file_path
    ) REFERENCES evidence.external_source_file (
        dataset_snapshot_key, source_file_path
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT external_field_dictionary_no_silent_conversion_ck CHECK (
        NOT unit_conversion_applied
        AND normalization_rule IN (
            'identity_no_unit_conversion', 'trim_outer_whitespace_only'
        )
    )
);

CREATE FUNCTION evidence.round3e_reject_direct_identifiers(input JSONB)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $round3e_reject_direct_identifiers$
    SELECT input::TEXT !~* '(^|["{,[:space:]_])(name|full.?name|email|phone|address|street|postcode|postal.?code)["[:space:]_]*:'
       AND input::TEXT !~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
$round3e_reject_direct_identifiers$;

CREATE TABLE evidence.external_observation (
    external_observation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    dataset_snapshot_key TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_row_identity TEXT NOT NULL,
    record_type TEXT NOT NULL,
    raw_value JSONB NOT NULL,
    parsed_value JSONB NOT NULL,
    normalized_value JSONB NOT NULL,
    normalization_rule TEXT NOT NULL,
    raw_value_preserved BOOLEAN NOT NULL DEFAULT TRUE,
    exclusion_reason TEXT,
    CONSTRAINT external_observation_pk PRIMARY KEY (
        external_observation_id
    ),
    CONSTRAINT external_observation_source_uq UNIQUE (
        dataset_snapshot_key, source_file_path, source_row_identity
    ),
    CONSTRAINT external_observation_file_fk FOREIGN KEY (
        dataset_snapshot_key, source_file_path
    ) REFERENCES evidence.external_source_file (
        dataset_snapshot_key, source_file_path
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT external_observation_json_ck CHECK (
        jsonb_typeof(raw_value) = 'object'
        AND jsonb_typeof(parsed_value) = 'object'
        AND jsonb_typeof(normalized_value) = 'object'
    ),
    CONSTRAINT external_observation_raw_preserved_ck CHECK (
        raw_value_preserved
        AND evidence.round3e_reject_direct_identifiers(raw_value)
    ),
    CONSTRAINT external_observation_text_ck CHECK (
        source_row_identity = btrim(source_row_identity)
        AND source_row_identity <> ''
        AND record_type = btrim(record_type) AND record_type <> ''
        AND normalization_rule = btrim(normalization_rule)
        AND normalization_rule <> ''
        AND (exclusion_reason IS NULL
             OR exclusion_reason = btrim(exclusion_reason)
                AND exclusion_reason <> '')
    )
);

CREATE TABLE corpus.external_document (
    external_document_id BIGINT GENERATED ALWAYS AS IDENTITY,
    dataset_snapshot_key TEXT NOT NULL,
    source_document_key TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    source_date DATE NOT NULL,
    geography TEXT NOT NULL,
    language_code TEXT NOT NULL,
    raw_text JSONB NOT NULL,
    raw_text_public_export_allowed BOOLEAN NOT NULL,
    capture_method TEXT NOT NULL,
    c0_candidate TEXT NOT NULL,
    c1_source_local TEXT NOT NULL,
    black_milk TEXT NOT NULL,
    sensory_method TEXT NOT NULL,
    participant_type TEXT NOT NULL,
    CONSTRAINT external_document_pk PRIMARY KEY (external_document_id),
    CONSTRAINT external_document_source_uq UNIQUE (
        dataset_snapshot_key, source_document_key
    ),
    CONSTRAINT external_document_snapshot_fk FOREIGN KEY (
        dataset_snapshot_key
    ) REFERENCES evidence.external_dataset_snapshot (dataset_snapshot_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT external_document_json_ck CHECK (
        jsonb_typeof(raw_text) = 'object'
    )
);

CREATE TABLE corpus.external_expression_occurrence (
    expression_occurrence_key TEXT NOT NULL,
    dataset_snapshot_key TEXT NOT NULL,
    source_document_key TEXT NOT NULL,
    language_code TEXT NOT NULL,
    raw_source_phrase TEXT NOT NULL,
    normalized_expression TEXT NOT NULL,
    expression_role TEXT NOT NULL,
    candidate_canonical_mappings JSONB NOT NULL,
    lexical_candidates JSONB NOT NULL,
    review_state TEXT NOT NULL,
    automatic_promotion_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    regional_or_register_note TEXT NOT NULL,
    CONSTRAINT external_expression_occurrence_pk PRIMARY KEY (
        expression_occurrence_key
    ),
    CONSTRAINT external_expression_occurrence_document_fk FOREIGN KEY (
        dataset_snapshot_key, source_document_key
    ) REFERENCES corpus.external_document (
        dataset_snapshot_key, source_document_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT external_expression_occurrence_json_ck CHECK (
        jsonb_typeof(candidate_canonical_mappings) = 'array'
        AND jsonb_typeof(lexical_candidates) = 'array'
    ),
    CONSTRAINT external_expression_no_auto_promotion_ck CHECK (
        NOT automatic_promotion_allowed
        AND review_state IN (
            'CANDIDATE', 'RESEARCH_REVIEWED', 'BILINGUAL_REVIEWED',
            'EXPERT_REVIEWED', 'REJECTED', 'DEPRECATED'
        )
    )
);

CREATE TABLE corpus.lexical_mapping_candidate (
    mapping_key TEXT NOT NULL,
    raw_source_phrase TEXT NOT NULL,
    normalized_expression TEXT NOT NULL,
    candidate_mapping TEXT NOT NULL,
    evidence_key TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    mapping_scope TEXT NOT NULL,
    ambiguity_note TEXT NOT NULL,
    CONSTRAINT lexical_mapping_candidate_pk PRIMARY KEY (mapping_key),
    CONSTRAINT lexical_mapping_candidate_status_ck CHECK (
        lifecycle_status IN (
            'CANDIDATE', 'RESEARCH_REVIEWED', 'BILINGUAL_REVIEWED',
            'EXPERT_REVIEWED', 'REJECTED', 'DEPRECATED'
        )
    )
);

CREATE TABLE audit.lexical_promotion_approval (
    lexical_promotion_approval_key TEXT NOT NULL,
    language_code TEXT NOT NULL,
    normalized_expression TEXT NOT NULL,
    reviewed_by TEXT NOT NULL,
    reviewed_on DATE NOT NULL,
    evidence_note TEXT NOT NULL,
    CONSTRAINT lexical_promotion_approval_pk PRIMARY KEY (
        lexical_promotion_approval_key
    ),
    CONSTRAINT lexical_promotion_approval_expression_uq UNIQUE (
        language_code, normalized_expression
    )
);

CREATE FUNCTION corpus.prevent_unreviewed_candidate_promotion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_unreviewed_candidate_promotion$
DECLARE
    candidate_language TEXT;
    candidate_normalized TEXT;
BEGIN
    SELECT expression.language_tag_code, expression.normalized_text
    INTO STRICT candidate_language, candidate_normalized
    FROM kb.lexical_expression AS expression
    WHERE expression.expression_id = NEW.expression_id;

    IF EXISTS (
        SELECT 1
        FROM corpus.external_expression_occurrence AS occurrence
        WHERE lower(occurrence.language_code) = lower(candidate_language)
          AND occurrence.normalized_expression = candidate_normalized
          AND NOT occurrence.automatic_promotion_allowed
    ) AND NOT EXISTS (
        SELECT 1
        FROM audit.lexical_promotion_approval AS approval
        WHERE lower(approval.language_code) = lower(candidate_language)
          AND approval.normalized_expression = candidate_normalized
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'lexicalization_round3e_candidate_approval_ck',
            MESSAGE = 'recurrent external expression requires an explicit lexical promotion approval';
    END IF;
    RETURN NEW;
END
$prevent_unreviewed_candidate_promotion$;

CREATE TRIGGER lexicalization_round3e_candidate_approval_trg
BEFORE INSERT OR UPDATE ON kb.lexicalization
FOR EACH ROW EXECUTE FUNCTION corpus.prevent_unreviewed_candidate_promotion();

CREATE TABLE calibration.question_research_candidate (
    question_version_key TEXT NOT NULL,
    logical_question_code TEXT NOT NULL,
    language_code TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    target_distinction TEXT NOT NULL,
    eligible_c0 JSONB NOT NULL,
    eligible_c1 JSONB NOT NULL,
    candidate_region TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    answer_options JSONB NOT NULL,
    sensory_modality TEXT NOT NULL,
    evidence JSONB NOT NULL,
    consumer_familiarity_assumptions TEXT NOT NULL,
    translation_notes TEXT NOT NULL,
    ambiguity TEXT NOT NULL,
    expected_information_role TEXT NOT NULL,
    unresolved_concerns TEXT NOT NULL,
    information_gain_status TEXT NOT NULL,
    ordinary_user_validation_evidence TEXT,
    CONSTRAINT question_research_candidate_pk PRIMARY KEY (
        question_version_key
    ),
    CONSTRAINT question_research_candidate_language_uq UNIQUE (
        logical_question_code, language_code
    ),
    CONSTRAINT question_research_candidate_json_ck CHECK (
        jsonb_typeof(eligible_c0) = 'array'
        AND jsonb_typeof(eligible_c1) = 'array'
        AND jsonb_typeof(answer_options) = 'array'
        AND jsonb_array_length(answer_options) BETWEEN 2 AND 8
        AND jsonb_typeof(evidence) = 'array'
    ),
    CONSTRAINT question_research_candidate_status_ck CHECK (
        lifecycle_status IN (
            'CANDIDATE', 'RESEARCH_REVIEWED', 'BILINGUAL_REVIEWED',
            'EXPERT_REVIEWED', 'COMPREHENSION_READY',
            'ACTIVE_FOR_CALIBRATION', 'REJECTED', 'DEPRECATED'
        )
        AND information_gain_status = 'NOT_ESTIMABLE'
    )
);

CREATE FUNCTION calibration.enforce_question_validation_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_question_validation_evidence$
BEGIN
    IF NEW.lifecycle_status IN (
        'COMPREHENSION_READY', 'ACTIVE_FOR_CALIBRATION'
    ) AND NEW.ordinary_user_validation_evidence IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'question_research_user_validation_evidence_ck',
            MESSAGE = 'ordinary-user validation evidence is required for this lifecycle';
    END IF;
    RETURN NEW;
END
$enforce_question_validation_evidence$;

CREATE TRIGGER question_research_validation_evidence_trg
BEFORE INSERT OR UPDATE ON calibration.question_research_candidate
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_question_validation_evidence();

CREATE TABLE audit.external_import_run (
    external_import_run_key TEXT NOT NULL,
    import_version TEXT NOT NULL,
    import_code_sha TEXT NOT NULL,
    raw_snapshot_row_count INTEGER NOT NULL,
    imported_record_count INTEGER NOT NULL,
    exclusion_count INTEGER NOT NULL,
    source_file_count INTEGER NOT NULL,
    source_file_hash_count INTEGER NOT NULL,
    pii_scan_pass BOOLEAN NOT NULL,
    rights_review_pass BOOLEAN NOT NULL,
    public_export_policy_pass BOOLEAN NOT NULL,
    quality_profile JSONB NOT NULL,
    CONSTRAINT external_import_run_pk PRIMARY KEY (external_import_run_key),
    CONSTRAINT external_import_run_hash_ck CHECK (
        import_code_sha ~ '^[0-9a-f]{40}$'
    ),
    CONSTRAINT external_import_run_count_ck CHECK (
        raw_snapshot_row_count = imported_record_count + exclusion_count
        AND source_file_count = source_file_hash_count
        AND pii_scan_pass AND rights_review_pass AND public_export_policy_pass
        AND jsonb_typeof(quality_profile) = 'object'
    )
);

CREATE TABLE audit.empirical_coverage_cell (
    empirical_coverage_cell_id BIGINT GENERATED ALWAYS AS IDENTITY,
    source_key TEXT NOT NULL,
    coffee_identity TEXT NOT NULL,
    c0_preparation TEXT NOT NULL,
    c1_roast TEXT NOT NULL,
    black_milk TEXT NOT NULL,
    sensory_method TEXT NOT NULL,
    participant_type TEXT NOT NULL,
    language_code TEXT NOT NULL,
    observed_record_count INTEGER NOT NULL,
    cell_status TEXT NOT NULL,
    interpretation_limit TEXT NOT NULL,
    CONSTRAINT empirical_coverage_cell_pk PRIMARY KEY (
        empirical_coverage_cell_id
    ),
    CONSTRAINT empirical_coverage_cell_uq UNIQUE (
        source_key, coffee_identity, c0_preparation, c1_roast, black_milk,
        sensory_method, participant_type, language_code
    ),
    CONSTRAINT empirical_coverage_cell_observed_ck CHECK (
        observed_record_count > 0
        AND cell_status = 'OBSERVED_SOURCE_LOCAL_EVIDENCE'
    )
);

CREATE TABLE audit.round3e_artifact_hash (
    artifact_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    CONSTRAINT round3e_artifact_hash_pk PRIMARY KEY (artifact_key),
    CONSTRAINT round3e_artifact_hash_value_ck CHECK (
        sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE audit.round3e_prohibition (
    prohibition_key TEXT NOT NULL,
    ranking_model_trained BOOLEAN NOT NULL,
    adaptive_policy_trained BOOLEAN NOT NULL,
    deep_learning_model_run BOOLEAN NOT NULL,
    embedding_baseline_run BOOLEAN NOT NULL,
    pgvector_required BOOLEAN NOT NULL,
    real_human_collection_performed BOOLEAN NOT NULL,
    real_observation_count INTEGER NOT NULL,
    product_frontend_modified BOOLEAN NOT NULL,
    CONSTRAINT round3e_prohibition_pk PRIMARY KEY (prohibition_key),
    CONSTRAINT round3e_prohibition_all_false_ck CHECK (
        NOT ranking_model_trained AND NOT adaptive_policy_trained
        AND NOT deep_learning_model_run AND NOT embedding_baseline_run
        AND NOT pgvector_required AND NOT real_human_collection_performed
        AND real_observation_count = 0 AND NOT product_frontend_modified
    )
);

CREATE FUNCTION evidence.prevent_external_observation_ontology_support()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_external_observation_ontology_support$
BEGIN
    IF NEW.dataset_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM evidence.external_dataset_snapshot AS snapshot
        WHERE snapshot.dataset_id = NEW.dataset_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'concept_support_external_observation_boundary_ck',
            MESSAGE = 'external source-local observations cannot be inserted into canonical ontology support';
    END IF;
    RETURN NEW;
END
$prevent_external_observation_ontology_support$;

CREATE TRIGGER concept_support_external_observation_boundary_trg
BEFORE INSERT OR UPDATE ON evidence.concept_support
FOR EACH ROW EXECUTE FUNCTION evidence.prevent_external_observation_ontology_support();

CREATE FUNCTION audit.prevent_round3e_model_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3e_model_run$
BEGIN
    IF NEW.input_dataset_id IS NOT NULL AND EXISTS (
        SELECT 1 FROM evidence.external_dataset_snapshot AS snapshot
        WHERE snapshot.dataset_id = NEW.input_dataset_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3e_model_run_prohibited_ck',
            MESSAGE = 'Round 3E external snapshots cannot be used for model runs';
    END IF;
    RETURN NEW;
END
$prevent_round3e_model_run$;

CREATE TRIGGER round3e_model_run_prohibited_trg
BEFORE INSERT OR UPDATE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3e_model_run();

COMMIT;
