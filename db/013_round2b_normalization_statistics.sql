\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- Round 2B
-- Deterministic expression normalization and versioned corpus-derived
-- statistics.  Every object in this migration remains observational: neither
-- frequency nor co-occurrence promotes a concept or canonical relation.

BEGIN;

-- corpus.normalization_pipeline is introduced by migration 012 because the
-- immutable corpus-snapshot identity must reference its selected pipeline.

CREATE TABLE corpus.normalization_rule (
    normalization_rule_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalization_rule_key TEXT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    rule_order SMALLINT NOT NULL,
    rule_kind TEXT NOT NULL,
    input_normalized_text TEXT NOT NULL,
    output_normalized_text TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT normalization_rule_pk PRIMARY KEY (normalization_rule_id),
    CONSTRAINT normalization_rule_key_uq UNIQUE (normalization_rule_key),
    CONSTRAINT normalization_rule_pipeline_order_uq UNIQUE (
        normalization_pipeline_id,
        rule_order
    ),
    CONSTRAINT normalization_rule_pipeline_input_uq UNIQUE (
        normalization_pipeline_id,
        input_normalized_text
    ),
    CONSTRAINT normalization_rule_pipeline_fk FOREIGN KEY (
        normalization_pipeline_id
    ) REFERENCES corpus.normalization_pipeline (normalization_pipeline_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalization_rule_key_nonempty_ck CHECK (
        normalization_rule_key = btrim(normalization_rule_key)
        AND normalization_rule_key <> ''
    ),
    CONSTRAINT normalization_rule_order_positive_ck CHECK (rule_order > 0),
    CONSTRAINT normalization_rule_kind_ck CHECK (
        rule_kind = 'WHOLE_PHRASE'
    ),
    CONSTRAINT normalization_rule_input_nonempty_ck CHECK (
        input_normalized_text = btrim(input_normalized_text)
        AND input_normalized_text <> ''
    ),
    CONSTRAINT normalization_rule_output_nonempty_ck CHECK (
        output_normalized_text = btrim(output_normalized_text)
        AND output_normalized_text <> ''
    ),
    CONSTRAINT normalization_rule_not_identity_ck CHECK (
        input_normalized_text <> output_normalized_text
    ),
    CONSTRAINT normalization_rule_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

COMMENT ON TABLE corpus.normalization_rule IS
    'Ordered exact whole-phrase transformations applied after Unicode, punctuation, case, and whitespace normalization. Substring replacement and stemming are intentionally absent.';

CREATE FUNCTION corpus.guard_frozen_normalization_pipeline()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_normalization_pipeline$
DECLARE
    checked_pipeline_id BIGINT;
    pipeline_is_frozen BOOLEAN;
BEGIN
    checked_pipeline_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.normalization_pipeline_id
        ELSE NEW.normalization_pipeline_id
    END;

    SELECT pipeline.frozen_at IS NOT NULL
    INTO pipeline_is_frozen
    FROM corpus.normalization_pipeline AS pipeline
    WHERE pipeline.normalization_pipeline_id = checked_pipeline_id;

    IF COALESCE(pipeline_is_frozen, FALSE) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'normalization_rule_pipeline_frozen_ck',
            MESSAGE = 'normalization_rule_pipeline_frozen_ck: rules of a frozen normalization pipeline cannot be inserted, updated, or deleted';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_normalization_pipeline$;

CREATE TRIGGER normalization_rule_pipeline_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.normalization_rule
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_normalization_pipeline();

CREATE FUNCTION corpus.normalize_expression_base_v1(input_text TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
PARALLEL SAFE
SET search_path = pg_catalog
AS $normalize_expression_base_v1$
DECLARE
    normalized_value TEXT;
BEGIN
    IF input_text IS NULL THEN
        RETURN NULL;
    END IF;

    -- The order is part of the v1 contract. NFC precedes an explicit,
    -- conservative character translation. No punctuation is deleted.
    normalized_value := normalize(input_text, NFC);
    normalized_value := replace(normalized_value, U&'\2018', chr(39));
    normalized_value := replace(normalized_value, U&'\2019', chr(39));
    normalized_value := replace(normalized_value, U&'\02BC', chr(39));
    normalized_value := replace(normalized_value, U&'\201C', chr(34));
    normalized_value := replace(normalized_value, U&'\201D', chr(34));
    normalized_value := replace(normalized_value, U&'\2010', '-');
    normalized_value := replace(normalized_value, U&'\2011', '-');
    normalized_value := replace(normalized_value, U&'\2012', '-');
    normalized_value := replace(normalized_value, U&'\2013', '-');
    normalized_value := replace(normalized_value, U&'\2014', '-');
    normalized_value := replace(normalized_value, U&'\2015', '-');
    normalized_value := replace(normalized_value, U&'\2212', '-');
    normalized_value := replace(normalized_value, U&'\2026', '...');
    normalized_value := replace(normalized_value, U&'\00A0', ' ');
    normalized_value := replace(normalized_value, U&'\202F', ' ');
    normalized_value := lower(normalized_value);

    RETURN btrim(
        regexp_replace(normalized_value, '[[:space:]]+', ' ', 'g')
    );
END;
$normalize_expression_base_v1$;

COMMENT ON FUNCTION corpus.normalize_expression_base_v1(TEXT) IS
    'Internal rule-free portion of the Round 2B v1 normalizer, shared by rule validation and the public pipeline-aware function.';

CREATE FUNCTION corpus.enforce_normalization_rule_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_normalization_rule_semantics$
BEGIN
    IF corpus.normalize_expression_base_v1(NEW.input_normalized_text)
       <> NEW.input_normalized_text
       OR corpus.normalize_expression_base_v1(NEW.output_normalized_text)
          <> NEW.output_normalized_text THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalization_rule_base_form_ck',
            MESSAGE = 'normalization_rule_base_form_ck: whole-phrase rule endpoints must already be in v1 base-normalized form';
    END IF;

    RETURN NEW;
END;
$enforce_normalization_rule_semantics$;

CREATE TRIGGER normalization_rule_semantics_biu
BEFORE INSERT OR UPDATE
ON corpus.normalization_rule
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_normalization_rule_semantics();

CREATE FUNCTION corpus.normalize_expression_v1(
    input_text TEXT,
    normalization_pipeline_key TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
SET search_path = pg_catalog
AS $normalize_expression_v1$
DECLARE
    selected_pipeline_id BIGINT;
    normalized_value TEXT;
    selected_rule RECORD;
BEGIN
    IF NULLIF(btrim($2), '') IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'normalize_expression_v1_pipeline_key_ck',
            MESSAGE = 'normalize_expression_v1_pipeline_key_ck: normalization_pipeline_key is required';
    END IF;

    SELECT pipeline.normalization_pipeline_id
    INTO selected_pipeline_id
    FROM corpus.normalization_pipeline AS pipeline
    WHERE pipeline.normalization_pipeline_key =
          btrim($2)
      AND pipeline.unicode_form = 'NFC'
      AND pipeline.frozen_at IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'normalize_expression_v1_pipeline_ck',
            MESSAGE = 'normalize_expression_v1_pipeline_ck: v1 normalization requires a known frozen NFC pipeline';
    END IF;

    normalized_value := corpus.normalize_expression_base_v1(input_text);

    IF normalized_value IS NULL THEN
        RETURN NULL;
    END IF;

    FOR selected_rule IN
        SELECT
            rule.input_normalized_text,
            rule.output_normalized_text
        FROM corpus.normalization_rule AS rule
        WHERE rule.normalization_pipeline_id = selected_pipeline_id
          AND rule.rule_kind = 'WHOLE_PHRASE'
        ORDER BY rule.rule_order
    LOOP
        IF normalized_value = selected_rule.input_normalized_text THEN
            normalized_value := selected_rule.output_normalized_text;
        END IF;
    END LOOP;

    RETURN normalized_value;
END;
$normalize_expression_v1$;

COMMENT ON FUNCTION corpus.normalize_expression_v1(TEXT, TEXT) IS
    'Versioned deterministic NFC, punctuation, lowercase, whitespace, and ordered whole-phrase normalization. It performs no stemming or semantic inference.';

CREATE TABLE corpus.normalized_expression (
    normalized_expression_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalized_expression_key TEXT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    normalized_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT normalized_expression_pk PRIMARY KEY (
        normalized_expression_id
    ),
    CONSTRAINT normalized_expression_key_uq UNIQUE (
        normalized_expression_key
    ),
    CONSTRAINT normalized_expression_pipeline_text_uq UNIQUE (
        normalization_pipeline_id,
        normalized_text
    ),
    CONSTRAINT normalized_expression_id_pipeline_uq UNIQUE (
        normalized_expression_id,
        normalization_pipeline_id
    ),
    CONSTRAINT normalized_expression_pipeline_fk FOREIGN KEY (
        normalization_pipeline_id
    ) REFERENCES corpus.normalization_pipeline (normalization_pipeline_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_key_nonempty_ck CHECK (
        normalized_expression_key = btrim(normalized_expression_key)
        AND normalized_expression_key <> ''
    ),
    CONSTRAINT normalized_expression_text_nonempty_ck CHECK (
        normalized_text = btrim(normalized_text)
        AND normalized_text <> ''
    )
);

COMMENT ON TABLE corpus.normalized_expression IS
    'One stable expression identity per frozen pipeline and normalized phrase; observed language may exist here without any canonical concept mapping.';

CREATE TABLE corpus.lexical_expression_normalization (
    lexical_expression_normalization_id BIGINT GENERATED ALWAYS AS IDENTITY,
    lexical_expression_normalization_key TEXT NOT NULL,
    expression_id BIGINT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    normalized_expression_id BIGINT NOT NULL,
    surface_sha256 TEXT NOT NULL,
    derived_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT lexical_expression_normalization_pk PRIMARY KEY (
        lexical_expression_normalization_id
    ),
    CONSTRAINT lexical_expression_normalization_key_uq UNIQUE (
        lexical_expression_normalization_key
    ),
    CONSTRAINT lexical_expression_normalization_pipeline_expression_uq UNIQUE (
        normalization_pipeline_id,
        expression_id
    ),
    CONSTRAINT lexical_expression_normalization_expression_fk FOREIGN KEY (
        expression_id
    ) REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexical_expression_normalization_normalized_expression_fk FOREIGN KEY (
        normalized_expression_id,
        normalization_pipeline_id
    ) REFERENCES corpus.normalized_expression (
        normalized_expression_id,
        normalization_pipeline_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexical_expression_normalization_key_nonempty_ck CHECK (
        lexical_expression_normalization_key =
            btrim(lexical_expression_normalization_key)
        AND lexical_expression_normalization_key <> ''
    ),
    CONSTRAINT lexical_expression_normalization_surface_sha256_ck CHECK (
        surface_sha256 ~ '^[0-9a-f]{64}$'
    )
);

COMMENT ON TABLE corpus.lexical_expression_normalization IS
    'Reproducible mapping from a preserved lexical surface to one normalized expression under one frozen pipeline.';

CREATE TABLE corpus.normalization_derivation_run (
    normalization_derivation_run_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalization_derivation_run_key TEXT NOT NULL,
    corpus_snapshot_id BIGINT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    input_inventory_sha256 TEXT NOT NULL,
    output_inventory_sha256 TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    frozen_at TIMESTAMPTZ,
    input_observation_count BIGINT NOT NULL,
    output_occurrence_count BIGINT,
    configuration JSONB NOT NULL,
    notes TEXT,
    CONSTRAINT normalization_derivation_run_pk PRIMARY KEY (
        normalization_derivation_run_id
    ),
    CONSTRAINT normalization_derivation_run_key_uq UNIQUE (
        normalization_derivation_run_key
    ),
    CONSTRAINT normalization_derivation_run_snapshot_version_uq UNIQUE (
        corpus_snapshot_id,
        version_label
    ),
    CONSTRAINT normalization_derivation_run_id_pipeline_uq UNIQUE (
        normalization_derivation_run_id,
        normalization_pipeline_id
    ),
    CONSTRAINT normalization_derivation_run_snapshot_fk FOREIGN KEY (
        corpus_snapshot_id
    ) REFERENCES corpus.corpus_snapshot (corpus_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalization_derivation_run_pipeline_fk FOREIGN KEY (
        normalization_pipeline_id
    ) REFERENCES corpus.normalization_pipeline (normalization_pipeline_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalization_derivation_run_key_nonempty_ck CHECK (
        normalization_derivation_run_key =
            btrim(normalization_derivation_run_key)
        AND normalization_derivation_run_key <> ''
    ),
    CONSTRAINT normalization_derivation_run_version_nonempty_ck CHECK (
        version_label = btrim(version_label) AND version_label <> ''
    ),
    CONSTRAINT normalization_derivation_run_code_commit_sha_ck CHECK (
        code_commit_sha ~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
    ),
    CONSTRAINT normalization_derivation_run_input_inventory_sha256_ck CHECK (
        input_inventory_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT normalization_derivation_run_output_inventory_sha256_ck CHECK (
        output_inventory_sha256 IS NULL
        OR output_inventory_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT normalization_derivation_run_time_order_ck CHECK (
        completed_at IS NULL OR completed_at >= started_at
    ),
    CONSTRAINT normalization_derivation_run_freeze_order_ck CHECK (
        frozen_at IS NULL
        OR (completed_at IS NOT NULL AND frozen_at >= completed_at)
    ),
    CONSTRAINT normalization_derivation_run_input_count_nonnegative_ck CHECK (
        input_observation_count >= 0
    ),
    CONSTRAINT normalization_derivation_run_output_count_nonnegative_ck CHECK (
        output_occurrence_count IS NULL OR output_occurrence_count >= 0
    ),
    CONSTRAINT normalization_derivation_run_completion_shape_ck CHECK (
        (completed_at IS NULL AND output_inventory_sha256 IS NULL)
        OR (completed_at IS NOT NULL AND output_inventory_sha256 IS NOT NULL)
    ),
    CONSTRAINT normalization_derivation_run_freeze_shape_ck CHECK (
        frozen_at IS NULL
        OR (completed_at IS NOT NULL AND output_occurrence_count IS NOT NULL)
    ),
    CONSTRAINT normalization_derivation_run_configuration_object_ck CHECK (
        jsonb_typeof(configuration) = 'object'
    ),
    CONSTRAINT normalization_derivation_run_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

COMMENT ON TABLE corpus.normalization_derivation_run IS
    'Versioned, hash-addressed derivation of occurrence normalizations for one frozen corpus snapshot and pipeline.';

CREATE TABLE corpus.normalized_expression_occurrence (
    normalized_expression_occurrence_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalized_expression_occurrence_key TEXT NOT NULL,
    normalization_derivation_run_id BIGINT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    observation_expression_id BIGINT NOT NULL,
    normalized_expression_id BIGINT NOT NULL,
    source_observation_sha256 TEXT NOT NULL,
    source_surface_sha256 TEXT NOT NULL,
    source_character_start INTEGER NOT NULL,
    source_character_end INTEGER NOT NULL,
    source_offset_unit TEXT NOT NULL DEFAULT 'UNICODE_CODE_POINT',
    CONSTRAINT normalized_expression_occurrence_pk PRIMARY KEY (
        normalized_expression_occurrence_id
    ),
    CONSTRAINT normalized_expression_occurrence_key_uq UNIQUE (
        normalized_expression_occurrence_key
    ),
    CONSTRAINT normalized_expression_occurrence_run_observation_uq UNIQUE (
        normalization_derivation_run_id,
        observation_expression_id
    ),
    CONSTRAINT normalized_expression_occurrence_run_pipeline_fk FOREIGN KEY (
        normalization_derivation_run_id,
        normalization_pipeline_id
    ) REFERENCES corpus.normalization_derivation_run (
        normalization_derivation_run_id,
        normalization_pipeline_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_occurrence_observation_fk FOREIGN KEY (
        observation_expression_id
    ) REFERENCES corpus.observation_expression (observation_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_occurrence_normalized_expression_fk FOREIGN KEY (
        normalized_expression_id,
        normalization_pipeline_id
    ) REFERENCES corpus.normalized_expression (
        normalized_expression_id,
        normalization_pipeline_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_occurrence_key_nonempty_ck CHECK (
        normalized_expression_occurrence_key =
            btrim(normalized_expression_occurrence_key)
        AND normalized_expression_occurrence_key <> ''
    ),
    CONSTRAINT normalized_expression_occurrence_observation_sha256_ck CHECK (
        source_observation_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT normalized_expression_occurrence_surface_sha256_ck CHECK (
        source_surface_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT normalized_expression_occurrence_offsets_ck CHECK (
        source_character_start >= 0
        AND source_character_end > source_character_start
    ),
    CONSTRAINT normalized_expression_occurrence_offset_unit_ck CHECK (
        source_offset_unit = 'UNICODE_CODE_POINT'
    )
);

COMMENT ON TABLE corpus.normalized_expression_occurrence IS
    'Derived phrase occurrence with raw-observation and surface hashes plus non-destructive source offsets; protected full note text is not required for public reproduction.';

CREATE TABLE corpus.corpus_statistic_run (
    corpus_statistic_run_id BIGINT GENERATED ALWAYS AS IDENTITY,
    corpus_statistic_run_key TEXT NOT NULL,
    normalization_derivation_run_id BIGINT NOT NULL,
    statistical_method_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    configuration JSONB NOT NULL,
    sample_document_count BIGINT NOT NULL,
    sample_observation_count BIGINT NOT NULL,
    sample_occurrence_count BIGINT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    frozen_at TIMESTAMPTZ,
    result_inventory_sha256 TEXT,
    value_semantics TEXT NOT NULL,
    CONSTRAINT corpus_statistic_run_pk PRIMARY KEY (corpus_statistic_run_id),
    CONSTRAINT corpus_statistic_run_key_uq UNIQUE (corpus_statistic_run_key),
    CONSTRAINT corpus_statistic_run_derivation_version_method_uq UNIQUE (
        normalization_derivation_run_id,
        version_label,
        statistical_method_id
    ),
    CONSTRAINT corpus_statistic_run_derivation_fk FOREIGN KEY (
        normalization_derivation_run_id
    ) REFERENCES corpus.normalization_derivation_run (
        normalization_derivation_run_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_statistic_run_method_fk FOREIGN KEY (
        statistical_method_id
    ) REFERENCES evidence.statistical_method (statistical_method_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_statistic_run_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_statistic_run_key_nonempty_ck CHECK (
        corpus_statistic_run_key = btrim(corpus_statistic_run_key)
        AND corpus_statistic_run_key <> ''
    ),
    CONSTRAINT corpus_statistic_run_version_nonempty_ck CHECK (
        version_label = btrim(version_label) AND version_label <> ''
    ),
    CONSTRAINT corpus_statistic_run_code_commit_sha_ck CHECK (
        code_commit_sha ~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
    ),
    CONSTRAINT corpus_statistic_run_configuration_sha256_ck CHECK (
        configuration_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT corpus_statistic_run_configuration_object_ck CHECK (
        jsonb_typeof(configuration) = 'object'
    ),
    CONSTRAINT corpus_statistic_run_sample_counts_positive_ck CHECK (
        sample_document_count > 0
        AND sample_observation_count > 0
        AND sample_occurrence_count > 0
    ),
    CONSTRAINT corpus_statistic_run_time_order_ck CHECK (
        completed_at IS NULL OR completed_at >= started_at
    ),
    CONSTRAINT corpus_statistic_run_freeze_order_ck CHECK (
        frozen_at IS NULL
        OR (completed_at IS NOT NULL AND frozen_at >= completed_at)
    ),
    CONSTRAINT corpus_statistic_run_result_inventory_sha256_ck CHECK (
        result_inventory_sha256 IS NULL
        OR result_inventory_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT corpus_statistic_run_completion_shape_ck CHECK (
        (completed_at IS NULL AND result_inventory_sha256 IS NULL)
        OR (completed_at IS NOT NULL AND result_inventory_sha256 IS NOT NULL)
    ),
    CONSTRAINT corpus_statistic_run_freeze_shape_ck CHECK (
        frozen_at IS NULL OR completed_at IS NOT NULL
    ),
    CONSTRAINT corpus_statistic_run_value_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    )
);

COMMENT ON TABLE corpus.corpus_statistic_run IS
    'Frozen method, configuration, sample counts, and value semantics for corpus-derived statistics.';

CREATE TABLE corpus.normalized_expression_frequency (
    normalized_expression_frequency_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalized_expression_frequency_key TEXT NOT NULL,
    corpus_statistic_run_id BIGINT NOT NULL,
    normalized_expression_id BIGINT NOT NULL,
    expression_frequency BIGINT NOT NULL,
    document_frequency BIGINT NOT NULL,
    publisher_prevalence_count BIGINT NOT NULL,
    publisher_sample_count BIGINT NOT NULL,
    country_prevalence_count BIGINT,
    country_sample_count BIGINT,
    composite_reference_occurrence_count BIGINT NOT NULL DEFAULT 0,
    qualifier_occurrence_count BIGINT NOT NULL DEFAULT 0,
    unresolved_occurrence_count BIGINT NOT NULL DEFAULT 0,
    value_semantics TEXT NOT NULL,
    CONSTRAINT normalized_expression_frequency_pk PRIMARY KEY (
        normalized_expression_frequency_id
    ),
    CONSTRAINT normalized_expression_frequency_key_uq UNIQUE (
        normalized_expression_frequency_key
    ),
    CONSTRAINT normalized_expression_frequency_run_expression_uq UNIQUE (
        corpus_statistic_run_id,
        normalized_expression_id
    ),
    CONSTRAINT normalized_expression_frequency_run_fk FOREIGN KEY (
        corpus_statistic_run_id
    ) REFERENCES corpus.corpus_statistic_run (corpus_statistic_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_frequency_expression_fk FOREIGN KEY (
        normalized_expression_id
    ) REFERENCES corpus.normalized_expression (normalized_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_frequency_key_nonempty_ck CHECK (
        normalized_expression_frequency_key =
            btrim(normalized_expression_frequency_key)
        AND normalized_expression_frequency_key <> ''
    ),
    CONSTRAINT normalized_expression_frequency_counts_positive_ck CHECK (
        expression_frequency > 0
        AND document_frequency > 0
        AND publisher_prevalence_count > 0
        AND publisher_sample_count > 0
    ),
    CONSTRAINT normalized_expression_frequency_frequency_order_ck CHECK (
        document_frequency <= expression_frequency
        AND publisher_prevalence_count <= document_frequency
        AND publisher_prevalence_count <= publisher_sample_count
    ),
    CONSTRAINT normalized_expression_frequency_country_pair_ck CHECK (
        (country_prevalence_count IS NULL AND country_sample_count IS NULL)
        OR (
            country_prevalence_count > 0
            AND country_sample_count > 0
            AND country_prevalence_count <= country_sample_count
        )
    ),
    CONSTRAINT normalized_expression_frequency_type_counts_ck CHECK (
        composite_reference_occurrence_count >= 0
        AND qualifier_occurrence_count >= 0
        AND unresolved_occurrence_count >= 0
        AND composite_reference_occurrence_count <= expression_frequency
        AND qualifier_occurrence_count <= expression_frequency
        AND unresolved_occurrence_count <= expression_frequency
    ),
    CONSTRAINT normalized_expression_frequency_value_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    )
);

CREATE TABLE corpus.normalized_expression_pair_measurement (
    normalized_expression_pair_measurement_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalized_expression_pair_measurement_key TEXT NOT NULL,
    corpus_statistic_run_id BIGINT NOT NULL,
    subject_normalized_expression_id BIGINT NOT NULL,
    object_normalized_expression_id BIGINT NOT NULL,
    cooccurrence_document_count BIGINT NOT NULL,
    normalized_pmi NUMERIC NOT NULL,
    subject_given_object_probability NUMERIC,
    object_given_subject_probability NUMERIC,
    value_semantics TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT normalized_expression_pair_measurement_pk PRIMARY KEY (
        normalized_expression_pair_measurement_id
    ),
    CONSTRAINT normalized_expression_pair_measurement_key_uq UNIQUE (
        normalized_expression_pair_measurement_key
    ),
    CONSTRAINT normalized_expression_pair_measurement_run_pair_uq UNIQUE (
        corpus_statistic_run_id,
        subject_normalized_expression_id,
        object_normalized_expression_id
    ),
    CONSTRAINT normalized_expression_pair_measurement_run_fk FOREIGN KEY (
        corpus_statistic_run_id
    ) REFERENCES corpus.corpus_statistic_run (corpus_statistic_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_pair_measurement_subject_fk FOREIGN KEY (
        subject_normalized_expression_id
    ) REFERENCES corpus.normalized_expression (normalized_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_pair_measurement_object_fk FOREIGN KEY (
        object_normalized_expression_id
    ) REFERENCES corpus.normalized_expression (normalized_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalized_expression_pair_measurement_key_nonempty_ck CHECK (
        normalized_expression_pair_measurement_key =
            btrim(normalized_expression_pair_measurement_key)
        AND normalized_expression_pair_measurement_key <> ''
    ),
    CONSTRAINT normalized_expression_pair_measurement_endpoint_order_ck CHECK (
        subject_normalized_expression_id < object_normalized_expression_id
    ),
    CONSTRAINT normalized_expression_pair_measurement_count_positive_ck CHECK (
        cooccurrence_document_count > 0
    ),
    CONSTRAINT normalized_expression_pair_measurement_npmi_bounds_ck CHECK (
        normalized_pmi BETWEEN -1 AND 1
    ),
    CONSTRAINT normalized_expression_pair_measurement_conditional_bounds_ck CHECK (
        (
            subject_given_object_probability IS NULL
            OR subject_given_object_probability BETWEEN 0 AND 1
        )
        AND (
            object_given_subject_probability IS NULL
            OR object_given_subject_probability BETWEEN 0 AND 1
        )
    ),
    CONSTRAINT normalized_expression_pair_value_semantics_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    ),
    CONSTRAINT normalized_expression_pair_measurement_context_object_ck CHECK (
        jsonb_typeof(context) = 'object'
    )
);

COMMENT ON TABLE corpus.normalized_expression_pair_measurement IS
    'Document-window co-occurrence, NPMI, and optional conditional rates for normalized expressions. These are language observations, not sensory-neighbour assertions.';

CREATE TABLE corpus.acquisition_batch_diagnostic (
    acquisition_batch_diagnostic_id BIGINT GENERATED ALWAYS AS IDENTITY,
    acquisition_batch_diagnostic_key TEXT NOT NULL,
    acquisition_batch_id BIGINT NOT NULL,
    corpus_statistic_run_id BIGINT NOT NULL,
    diagnostic_code TEXT NOT NULL,
    measured_value NUMERIC NOT NULL,
    sample_count BIGINT NOT NULL,
    value_semantics TEXT NOT NULL,
    bootstrap_configuration JSONB,
    context JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT acquisition_batch_diagnostic_pk PRIMARY KEY (
        acquisition_batch_diagnostic_id
    ),
    CONSTRAINT acquisition_batch_diagnostic_key_uq UNIQUE (
        acquisition_batch_diagnostic_key
    ),
    CONSTRAINT acquisition_batch_diagnostic_scope_uq UNIQUE (
        acquisition_batch_id,
        corpus_statistic_run_id,
        diagnostic_code
    ),
    CONSTRAINT acquisition_batch_diagnostic_batch_fk FOREIGN KEY (
        acquisition_batch_id
    ) REFERENCES corpus.acquisition_batch (acquisition_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT acquisition_batch_diagnostic_run_fk FOREIGN KEY (
        corpus_statistic_run_id
    ) REFERENCES corpus.corpus_statistic_run (corpus_statistic_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT acquisition_batch_diagnostic_key_nonempty_ck CHECK (
        acquisition_batch_diagnostic_key =
            btrim(acquisition_batch_diagnostic_key)
        AND acquisition_batch_diagnostic_key <> ''
    ),
    CONSTRAINT acquisition_batch_diagnostic_code_ck CHECK (
        diagnostic_code IN (
            'VOCABULARY_DISCOVERY_RATE',
            'HIGH_FREQUENCY_RANK_STABILITY',
            'COOCCURRENCE_NEIGHBOUR_STABILITY',
            'PUBLISHER_CONCENTRATION',
            'GEOGRAPHIC_CONCENTRATION'
        )
    ),
    CONSTRAINT acquisition_batch_diagnostic_sample_count_positive_ck CHECK (
        sample_count > 0
    ),
    CONSTRAINT acquisition_batch_diagnostic_value_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    ),
    CONSTRAINT acquisition_batch_diagnostic_bootstrap_object_ck CHECK (
        bootstrap_configuration IS NULL
        OR jsonb_typeof(bootstrap_configuration) = 'object'
    ),
    CONSTRAINT acquisition_batch_diagnostic_bootstrap_required_ck CHECK (
        diagnostic_code <> 'COOCCURRENCE_NEIGHBOUR_STABILITY'
        OR bootstrap_configuration IS NOT NULL
    ),
    CONSTRAINT acquisition_batch_diagnostic_context_object_ck CHECK (
        jsonb_typeof(context) = 'object'
    )
);

CREATE TABLE corpus.ontology_extension_candidate (
    ontology_extension_candidate_id BIGINT GENERATED ALWAYS AS IDENTITY,
    ontology_extension_candidate_key TEXT NOT NULL,
    corpus_statistic_run_id BIGINT NOT NULL,
    normalized_expression_id BIGINT NOT NULL,
    expression_frequency BIGINT NOT NULL,
    publisher_diversity_count BIGINT NOT NULL,
    information_lost TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    evidence_status TEXT NOT NULL,
    curation_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ontology_extension_candidate_pk PRIMARY KEY (
        ontology_extension_candidate_id
    ),
    CONSTRAINT ontology_extension_candidate_key_uq UNIQUE (
        ontology_extension_candidate_key
    ),
    CONSTRAINT ontology_extension_candidate_run_expression_uq UNIQUE (
        corpus_statistic_run_id,
        normalized_expression_id
    ),
    CONSTRAINT ontology_extension_candidate_run_fk FOREIGN KEY (
        corpus_statistic_run_id
    ) REFERENCES corpus.corpus_statistic_run (corpus_statistic_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ontology_extension_candidate_expression_fk FOREIGN KEY (
        normalized_expression_id
    ) REFERENCES corpus.normalized_expression (normalized_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ontology_extension_candidate_key_nonempty_ck CHECK (
        ontology_extension_candidate_key =
            btrim(ontology_extension_candidate_key)
        AND ontology_extension_candidate_key <> ''
    ),
    CONSTRAINT ontology_extension_candidate_counts_positive_ck CHECK (
        expression_frequency > 0 AND publisher_diversity_count > 0
    ),
    CONSTRAINT ontology_extension_candidate_information_lost_nonempty_ck CHECK (
        information_lost = btrim(information_lost)
        AND information_lost <> ''
    ),
    CONSTRAINT ontology_extension_candidate_recommended_action_nonempty_ck CHECK (
        recommended_action = btrim(recommended_action)
        AND recommended_action <> ''
    ),
    CONSTRAINT ontology_extension_candidate_evidence_status_ck CHECK (
        evidence_status IN (
            'CORPUS_OBSERVATION_ONLY',
            'REQUIRES_COFFEE_SENSORY_EVIDENCE',
            'INSUFFICIENTLY_DISTINCT'
        )
    ),
    CONSTRAINT ontology_extension_candidate_curation_status_ck CHECK (
        curation_status IN ('OPEN', 'DEFERRED', 'REJECTED')
    )
);

COMMENT ON TABLE corpus.ontology_extension_candidate IS
    'Governed feedback queue for information loss observed in industry language. Rows cannot activate or modify kb.concept.';

CREATE TABLE corpus.ontology_extension_candidate_nearest_concept (
    ontology_extension_candidate_nearest_concept_id BIGINT
        GENERATED ALWAYS AS IDENTITY,
    ontology_extension_candidate_nearest_concept_key TEXT NOT NULL,
    ontology_extension_candidate_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    candidate_rank SMALLINT NOT NULL,
    comparison_basis TEXT NOT NULL,
    orthographic_similarity REAL,
    information_preserved TEXT NOT NULL,
    CONSTRAINT ontology_extension_candidate_nearest_concept_pk PRIMARY KEY (
        ontology_extension_candidate_nearest_concept_id
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_key_uq UNIQUE (
        ontology_extension_candidate_nearest_concept_key
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_rank_uq UNIQUE (
        ontology_extension_candidate_id,
        candidate_rank
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_concept_uq UNIQUE (
        ontology_extension_candidate_id,
        concept_id
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_candidate_fk FOREIGN KEY (
        ontology_extension_candidate_id
    ) REFERENCES corpus.ontology_extension_candidate (
        ontology_extension_candidate_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ontology_extension_candidate_nearest_concept_concept_fk FOREIGN KEY (
        concept_id
    ) REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT ontology_extension_candidate_nearest_concept_key_nonempty_ck CHECK (
        ontology_extension_candidate_nearest_concept_key =
            btrim(ontology_extension_candidate_nearest_concept_key)
        AND ontology_extension_candidate_nearest_concept_key <> ''
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_rank_positive_ck CHECK (
        candidate_rank > 0
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_basis_nonempty_ck CHECK (
        comparison_basis = btrim(comparison_basis)
        AND comparison_basis <> ''
    ),
    CONSTRAINT ontology_extension_candidate_nearest_concept_similarity_ck CHECK (
        orthographic_similarity IS NULL
        OR orthographic_similarity BETWEEN 0::REAL AND 1::REAL
    ),
    CONSTRAINT ontology_extension_nearest_preserved_nonempty_ck CHECK (
        information_preserved = btrim(information_preserved)
        AND information_preserved <> ''
    )
);

CREATE FUNCTION corpus.enforce_normalized_expression_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_normalized_expression_semantics$
DECLARE
    selected_pipeline_key TEXT;
BEGIN
    SELECT pipeline.normalization_pipeline_key
    INTO selected_pipeline_key
    FROM corpus.normalization_pipeline AS pipeline
    WHERE pipeline.normalization_pipeline_id = NEW.normalization_pipeline_id
      AND pipeline.frozen_at IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalized_expression_frozen_pipeline_ck',
            MESSAGE = 'normalized_expression_frozen_pipeline_ck: normalized expressions require a frozen pipeline';
    END IF;

    IF corpus.normalize_expression_v1(
           NEW.normalized_text,
           selected_pipeline_key
       ) <> NEW.normalized_text THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalized_expression_canonical_form_ck',
            MESSAGE = 'normalized_expression_canonical_form_ck: normalized_text is not canonical under its pipeline';
    END IF;

    RETURN NEW;
END;
$enforce_normalized_expression_semantics$;

CREATE TRIGGER normalized_expression_semantics_biu
BEFORE INSERT OR UPDATE
ON corpus.normalized_expression
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_normalized_expression_semantics();

CREATE FUNCTION corpus.enforce_lexical_expression_normalization()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_lexical_expression_normalization$
DECLARE
    selected_pipeline_key TEXT;
    selected_pipeline_language TEXT;
    selected_expression_language TEXT;
    selected_expression_text TEXT;
    selected_normalized_text TEXT;
BEGIN
    SELECT
        pipeline.normalization_pipeline_key,
        pipeline.language_tag_code
    INTO
        selected_pipeline_key,
        selected_pipeline_language
    FROM corpus.normalization_pipeline AS pipeline
    WHERE pipeline.normalization_pipeline_id = NEW.normalization_pipeline_id
      AND pipeline.frozen_at IS NOT NULL;

    SELECT
        expression.language_tag_code,
        expression.expression_text
    INTO
        selected_expression_language,
        selected_expression_text
    FROM kb.lexical_expression AS expression
    WHERE expression.expression_id = NEW.expression_id;

    SELECT normalized.normalized_text
    INTO selected_normalized_text
    FROM corpus.normalized_expression AS normalized
    WHERE normalized.normalized_expression_id = NEW.normalized_expression_id
      AND normalized.normalization_pipeline_id =
          NEW.normalization_pipeline_id;

    IF selected_pipeline_key IS NULL
       OR selected_expression_text IS NULL
       OR selected_normalized_text IS NULL THEN
        RETURN NEW;
    END IF;

    IF selected_pipeline_language <> selected_expression_language THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'lexical_expression_normalization_language_ck',
            MESSAGE = 'lexical_expression_normalization_language_ck: pipeline and lexical-expression language tags must match';
    END IF;

    IF corpus.normalize_expression_v1(
           selected_expression_text,
           selected_pipeline_key
       ) <> selected_normalized_text THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'lexical_expression_normalization_value_ck',
            MESSAGE = 'lexical_expression_normalization_value_ck: normalized expression does not equal deterministic v1 output';
    END IF;

    IF encode(
           sha256(convert_to(selected_expression_text, 'UTF8')),
           'hex'
       ) <> NEW.surface_sha256 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'lexical_expression_normalization_surface_hash_ck',
            MESSAGE = 'lexical_expression_normalization_surface_hash_ck: surface hash must be the SHA-256 of the preserved expression text';
    END IF;

    RETURN NEW;
END;
$enforce_lexical_expression_normalization$;

CREATE TRIGGER lexical_expression_normalization_semantics_biu
BEFORE INSERT OR UPDATE
ON corpus.lexical_expression_normalization
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_lexical_expression_normalization();

CREATE FUNCTION corpus.enforce_normalized_occurrence_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_normalized_occurrence_semantics$
DECLARE
    selected_expression_id BIGINT;
    selected_observation_sha256 TEXT;
    selected_character_start INTEGER;
    selected_character_end INTEGER;
    selected_snapshot_id BIGINT;
    selected_run_snapshot_id BIGINT;
BEGIN
    SELECT
        occurrence.expression_id,
        observation.observation_sha256,
        observation.character_start,
        observation.character_end,
        snapshot.corpus_snapshot_id
    INTO
        selected_expression_id,
        selected_observation_sha256,
        selected_character_start,
        selected_character_end,
        selected_snapshot_id
    FROM corpus.observation_expression AS occurrence
    JOIN corpus.raw_observation AS observation
      ON observation.raw_observation_id = occurrence.raw_observation_id
    JOIN corpus.captured_document AS document
      ON document.captured_document_id = observation.captured_document_id
    JOIN corpus.corpus_snapshot AS snapshot
      ON snapshot.corpus_id = document.corpus_id
    WHERE occurrence.observation_expression_id =
          NEW.observation_expression_id;

    SELECT derivation.corpus_snapshot_id
    INTO selected_run_snapshot_id
    FROM corpus.normalization_derivation_run AS derivation
    WHERE derivation.normalization_derivation_run_id =
          NEW.normalization_derivation_run_id;

    IF selected_snapshot_id IS DISTINCT FROM selected_run_snapshot_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalized_expression_occurrence_snapshot_ck',
            MESSAGE = 'normalized_expression_occurrence_snapshot_ck: occurrence and derivation run must belong to the same frozen corpus snapshot';
    END IF;

    IF selected_observation_sha256 IS DISTINCT FROM
       NEW.source_observation_sha256 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalized_expression_occurrence_hash_ck',
            MESSAGE = 'normalized_expression_occurrence_hash_ck: occurrence observation hash must match its source observation';
    END IF;

    IF selected_character_start IS NOT NULL
       AND (
            selected_character_start <> NEW.source_character_start
            OR selected_character_end <> NEW.source_character_end
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalized_expression_occurrence_offsets_source_ck',
            MESSAGE = 'normalized_expression_occurrence_offsets_source_ck: derived offsets must preserve available source-observation offsets';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM corpus.lexical_expression_normalization AS mapping
        WHERE mapping.expression_id = selected_expression_id
          AND mapping.normalization_pipeline_id =
              NEW.normalization_pipeline_id
          AND mapping.normalized_expression_id =
              NEW.normalized_expression_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalized_expression_occurrence_mapping_ck',
            MESSAGE = 'normalized_expression_occurrence_mapping_ck: occurrence must use the deterministic mapping of its lexical expression';
    END IF;

    RETURN NEW;
END;
$enforce_normalized_occurrence_semantics$;

CREATE TRIGGER normalized_expression_occurrence_semantics_biu
BEFORE INSERT OR UPDATE
ON corpus.normalized_expression_occurrence
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_normalized_occurrence_semantics();

CREATE FUNCTION corpus.enforce_normalization_derivation_run_context()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_normalization_derivation_run_context$
DECLARE
    selected_snapshot_pipeline_id BIGINT;
    selected_snapshot_frozen BOOLEAN;
    selected_pipeline_frozen BOOLEAN;
    stored_occurrence_count BIGINT;
BEGIN
    SELECT
        snapshot.normalization_pipeline_id,
        snapshot.frozen_at IS NOT NULL
    INTO
        selected_snapshot_pipeline_id,
        selected_snapshot_frozen
    FROM corpus.corpus_snapshot AS snapshot
    WHERE snapshot.corpus_snapshot_id = NEW.corpus_snapshot_id;

    SELECT pipeline.frozen_at IS NOT NULL
    INTO selected_pipeline_frozen
    FROM corpus.normalization_pipeline AS pipeline
    WHERE pipeline.normalization_pipeline_id =
          NEW.normalization_pipeline_id;

    IF NOT COALESCE(selected_snapshot_frozen, FALSE)
       OR NOT COALESCE(selected_pipeline_frozen, FALSE)
       OR selected_snapshot_pipeline_id IS DISTINCT FROM
          NEW.normalization_pipeline_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'normalization_derivation_run_snapshot_pipeline_ck',
            MESSAGE = 'normalization_derivation_run_snapshot_pipeline_ck: derivation requires a frozen snapshot and its exact frozen pipeline';
    END IF;

    IF NEW.frozen_at IS NOT NULL THEN
        SELECT count(*)::BIGINT
        INTO stored_occurrence_count
        FROM corpus.normalized_expression_occurrence AS occurrence
        WHERE occurrence.normalization_derivation_run_id =
              NEW.normalization_derivation_run_id;

        IF stored_occurrence_count IS DISTINCT FROM
           NEW.output_occurrence_count THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'normalization_derivation_run_output_count_ck',
                MESSAGE = 'normalization_derivation_run_output_count_ck: declared output count must equal the frozen occurrence inventory';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_normalization_derivation_run_context$;

CREATE TRIGGER normalization_derivation_run_context_biu
BEFORE INSERT OR UPDATE
ON corpus.normalization_derivation_run
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_normalization_derivation_run_context();

CREATE FUNCTION corpus.guard_frozen_normalization_dictionary()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_normalization_dictionary$
DECLARE
    checked_pipeline_id BIGINT;
BEGIN
    checked_pipeline_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.normalization_pipeline_id
        ELSE NEW.normalization_pipeline_id
    END;

    IF EXISTS (
        SELECT 1
        FROM corpus.corpus_snapshot AS snapshot
        WHERE snapshot.normalization_pipeline_id = checked_pipeline_id
          AND snapshot.frozen_at IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'normalization_dictionary_snapshot_frozen_ck',
            MESSAGE = 'normalization_dictionary_snapshot_frozen_ck: normalized identities and mappings used by a frozen snapshot cannot change';
    END IF;

    IF TG_OP = 'UPDATE'
       AND OLD.normalization_pipeline_id <> NEW.normalization_pipeline_id
       AND EXISTS (
            SELECT 1
            FROM corpus.corpus_snapshot AS snapshot
            WHERE snapshot.normalization_pipeline_id =
                  OLD.normalization_pipeline_id
              AND snapshot.frozen_at IS NOT NULL
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'normalization_dictionary_source_snapshot_frozen_ck',
            MESSAGE = 'normalization_dictionary_source_snapshot_frozen_ck: a row cannot be moved away from a pipeline used by a frozen snapshot';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_normalization_dictionary$;

CREATE TRIGGER normalized_expression_snapshot_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.normalized_expression
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_normalization_dictionary();

CREATE TRIGGER lexical_expression_normalization_snapshot_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.lexical_expression_normalization
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_normalization_dictionary();

CREATE FUNCTION corpus.guard_frozen_mapped_lexical_expression()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_mapped_lexical_expression$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.lexical_expression_normalization AS mapping
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.normalization_pipeline_id =
             mapping.normalization_pipeline_id
         AND snapshot.frozen_at IS NOT NULL
        WHERE mapping.expression_id = OLD.expression_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'lexical_expression_frozen_snapshot_mapping_ck',
            MESSAGE = 'lexical_expression_frozen_snapshot_mapping_ck: a lexical expression mapped under a frozen snapshot pipeline cannot be updated or deleted';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_mapped_lexical_expression$;

CREATE TRIGGER lexical_expression_frozen_snapshot_mapping_bud
BEFORE UPDATE OR DELETE
ON kb.lexical_expression
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_mapped_lexical_expression();

CREATE FUNCTION corpus.guard_frozen_derivation_inventory()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_derivation_inventory$
DECLARE
    old_run_id BIGINT;
    new_run_id BIGINT;
BEGIN
    IF TG_TABLE_NAME = 'normalization_derivation_run' THEN
        IF OLD.frozen_at IS NOT NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000',
                CONSTRAINT = 'normalization_derivation_run_frozen_ck',
                MESSAGE = 'normalization_derivation_run_frozen_ck: a frozen derivation run cannot be updated or deleted';
        END IF;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP <> 'INSERT' THEN
        old_run_id := OLD.normalization_derivation_run_id;
    END IF;
    IF TG_OP <> 'DELETE' THEN
        new_run_id := NEW.normalization_derivation_run_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.normalization_derivation_run AS run
        WHERE run.normalization_derivation_run_id IN (
                  old_run_id,
                  new_run_id
              )
          AND run.frozen_at IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'normalized_occurrence_derivation_frozen_ck',
            MESSAGE = 'normalized_occurrence_derivation_frozen_ck: occurrence inventory of a frozen derivation run cannot change';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_derivation_inventory$;

CREATE TRIGGER normalization_derivation_run_frozen_bud
BEFORE UPDATE OR DELETE
ON corpus.normalization_derivation_run
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_derivation_inventory();

CREATE TRIGGER normalized_expression_occurrence_derivation_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.normalized_expression_occurrence
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_derivation_inventory();

CREATE FUNCTION corpus.guard_frozen_statistic_inventory()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_statistic_inventory$
DECLARE
    old_run_id BIGINT;
    new_run_id BIGINT;
BEGIN
    IF TG_TABLE_NAME = 'corpus_statistic_run' THEN
        IF OLD.frozen_at IS NOT NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000',
                CONSTRAINT = 'corpus_statistic_run_frozen_ck',
                MESSAGE = 'corpus_statistic_run_frozen_ck: a frozen statistic run cannot be updated or deleted';
        END IF;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    ELSIF TG_TABLE_NAME =
          'ontology_extension_candidate_nearest_concept' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT candidate.corpus_statistic_run_id
            INTO old_run_id
            FROM corpus.ontology_extension_candidate AS candidate
            WHERE candidate.ontology_extension_candidate_id =
                  OLD.ontology_extension_candidate_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT candidate.corpus_statistic_run_id
            INTO new_run_id
            FROM corpus.ontology_extension_candidate AS candidate
            WHERE candidate.ontology_extension_candidate_id =
                  NEW.ontology_extension_candidate_id;
        END IF;
    ELSE
        IF TG_OP <> 'INSERT' THEN
            old_run_id := OLD.corpus_statistic_run_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_run_id := NEW.corpus_statistic_run_id;
        END IF;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.corpus_statistic_run AS run
        WHERE run.corpus_statistic_run_id IN (old_run_id, new_run_id)
          AND run.frozen_at IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'corpus_statistic_inventory_frozen_ck',
            MESSAGE = 'corpus_statistic_inventory_frozen_ck: outputs of a frozen statistic run cannot change';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_statistic_inventory$;

CREATE FUNCTION corpus.enforce_corpus_statistic_run_context()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_corpus_statistic_run_context$
DECLARE
    derivation_is_frozen BOOLEAN;
    derivation_input_count BIGINT;
    derivation_output_count BIGINT;
    snapshot_document_count BIGINT;
    stored_frequency_count BIGINT;
BEGIN
    SELECT
        derivation.frozen_at IS NOT NULL,
        derivation.input_observation_count,
        derivation.output_occurrence_count,
        snapshot.expected_document_count
    INTO
        derivation_is_frozen,
        derivation_input_count,
        derivation_output_count,
        snapshot_document_count
    FROM corpus.normalization_derivation_run AS derivation
    JOIN corpus.corpus_snapshot AS snapshot
      ON snapshot.corpus_snapshot_id = derivation.corpus_snapshot_id
    WHERE derivation.normalization_derivation_run_id =
          NEW.normalization_derivation_run_id;

    IF NOT COALESCE(derivation_is_frozen, FALSE) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'corpus_statistic_run_frozen_derivation_ck',
            MESSAGE = 'corpus_statistic_run_frozen_derivation_ck: statistics require a frozen normalization derivation';
    END IF;

    IF NEW.sample_document_count > snapshot_document_count
       OR NEW.sample_observation_count > derivation_input_count
       OR NEW.sample_occurrence_count > derivation_output_count THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'corpus_statistic_run_sample_scope_ck',
            MESSAGE = 'corpus_statistic_run_sample_scope_ck: statistic samples cannot exceed the frozen snapshot and derivation inventories';
    END IF;

    IF NEW.frozen_at IS NOT NULL THEN
        SELECT count(*)::BIGINT
        INTO stored_frequency_count
        FROM corpus.normalized_expression_frequency AS frequency
        WHERE frequency.corpus_statistic_run_id =
              NEW.corpus_statistic_run_id;

        IF stored_frequency_count = 0 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'corpus_statistic_run_frequency_inventory_ck',
                MESSAGE = 'corpus_statistic_run_frequency_inventory_ck: a frozen statistic run requires normalized frequency rows';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_corpus_statistic_run_context$;

CREATE TRIGGER corpus_statistic_run_context_biu
BEFORE INSERT OR UPDATE
ON corpus.corpus_statistic_run
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_corpus_statistic_run_context();

CREATE FUNCTION corpus.enforce_statistic_expression_context()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_statistic_expression_context$
DECLARE
    selected_pipeline_id BIGINT;
    selected_sample_document_count BIGINT;
    selected_sample_occurrence_count BIGINT;
    subject_pipeline_id BIGINT;
    object_pipeline_id BIGINT;
BEGIN
    SELECT
        derivation.normalization_pipeline_id,
        statistic_run.sample_document_count,
        statistic_run.sample_occurrence_count
    INTO
        selected_pipeline_id,
        selected_sample_document_count,
        selected_sample_occurrence_count
    FROM corpus.corpus_statistic_run AS statistic_run
    JOIN corpus.normalization_derivation_run AS derivation
      ON derivation.normalization_derivation_run_id =
         statistic_run.normalization_derivation_run_id
    WHERE statistic_run.corpus_statistic_run_id =
          NEW.corpus_statistic_run_id;

    IF TG_TABLE_NAME = 'normalized_expression_pair_measurement' THEN
        SELECT subject.normalization_pipeline_id,
               object_expression.normalization_pipeline_id
        INTO subject_pipeline_id, object_pipeline_id
        FROM corpus.normalized_expression AS subject
        JOIN corpus.normalized_expression AS object_expression
          ON object_expression.normalized_expression_id =
             NEW.object_normalized_expression_id
        WHERE subject.normalized_expression_id =
              NEW.subject_normalized_expression_id;

        IF subject_pipeline_id IS DISTINCT FROM selected_pipeline_id
           OR object_pipeline_id IS DISTINCT FROM selected_pipeline_id THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'normalized_expression_pair_pipeline_ck',
                MESSAGE = 'normalized_expression_pair_pipeline_ck: pair endpoints must use the statistic run pipeline';
        END IF;

        IF NEW.cooccurrence_document_count >
           selected_sample_document_count THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'normalized_expression_pair_sample_count_ck',
                MESSAGE = 'normalized_expression_pair_sample_count_ck: co-occurrence count cannot exceed sampled documents';
        END IF;
    ELSE
        SELECT normalized.normalization_pipeline_id
        INTO subject_pipeline_id
        FROM corpus.normalized_expression AS normalized
        WHERE normalized.normalized_expression_id =
              NEW.normalized_expression_id;

        IF subject_pipeline_id IS DISTINCT FROM selected_pipeline_id THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'statistic_normalized_expression_pipeline_ck',
                MESSAGE = 'statistic_normalized_expression_pipeline_ck: statistic output must use the run pipeline';
        END IF;

        IF TG_TABLE_NAME = 'normalized_expression_frequency' THEN
            IF NEW.document_frequency > selected_sample_document_count
               OR NEW.publisher_sample_count >
                  selected_sample_document_count
               OR NEW.expression_frequency >
                  selected_sample_occurrence_count THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'normalized_expression_frequency_sample_scope_ck',
                    MESSAGE = 'normalized_expression_frequency_sample_scope_ck: frequency values cannot exceed declared statistic samples';
            END IF;
        ELSIF TG_TABLE_NAME = 'ontology_extension_candidate' THEN
            IF NEW.expression_frequency > selected_sample_occurrence_count
               OR NEW.publisher_diversity_count >
                  selected_sample_document_count THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'ontology_extension_candidate_sample_scope_ck',
                    MESSAGE = 'ontology_extension_candidate_sample_scope_ck: candidate evidence counts cannot exceed declared statistic samples';
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_statistic_expression_context$;

CREATE TRIGGER normalized_expression_frequency_context_biu
BEFORE INSERT OR UPDATE
ON corpus.normalized_expression_frequency
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_statistic_expression_context();

CREATE TRIGGER normalized_expression_pair_context_biu
BEFORE INSERT OR UPDATE
ON corpus.normalized_expression_pair_measurement
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_statistic_expression_context();

CREATE TRIGGER ontology_extension_candidate_context_biu
BEFORE INSERT OR UPDATE
ON corpus.ontology_extension_candidate
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_statistic_expression_context();

CREATE FUNCTION corpus.enforce_acquisition_batch_diagnostic_context()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_acquisition_batch_diagnostic_context$
DECLARE
    batch_snapshot_id BIGINT;
    statistic_snapshot_id BIGINT;
BEGIN
    SELECT batch.corpus_snapshot_id
    INTO batch_snapshot_id
    FROM corpus.acquisition_batch AS batch
    WHERE batch.acquisition_batch_id = NEW.acquisition_batch_id;

    SELECT derivation.corpus_snapshot_id
    INTO statistic_snapshot_id
    FROM corpus.corpus_statistic_run AS statistic_run
    JOIN corpus.normalization_derivation_run AS derivation
      ON derivation.normalization_derivation_run_id =
         statistic_run.normalization_derivation_run_id
    WHERE statistic_run.corpus_statistic_run_id =
          NEW.corpus_statistic_run_id;

    IF batch_snapshot_id IS DISTINCT FROM statistic_snapshot_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'acquisition_batch_diagnostic_snapshot_ck',
            MESSAGE = 'acquisition_batch_diagnostic_snapshot_ck: batch diagnostic and statistic run must use the same snapshot';
    END IF;

    RETURN NEW;
END;
$enforce_acquisition_batch_diagnostic_context$;

CREATE TRIGGER acquisition_batch_diagnostic_context_biu
BEFORE INSERT OR UPDATE
ON corpus.acquisition_batch_diagnostic
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_acquisition_batch_diagnostic_context();

CREATE TRIGGER corpus_statistic_run_frozen_bud
BEFORE UPDATE OR DELETE
ON corpus.corpus_statistic_run
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_statistic_inventory();

CREATE TRIGGER normalized_expression_frequency_statistic_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.normalized_expression_frequency
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_statistic_inventory();

CREATE TRIGGER normalized_expression_pair_statistic_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.normalized_expression_pair_measurement
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_statistic_inventory();

CREATE TRIGGER acquisition_batch_diagnostic_statistic_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.acquisition_batch_diagnostic
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_statistic_inventory();

CREATE TRIGGER ontology_extension_candidate_statistic_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.ontology_extension_candidate
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_statistic_inventory();

CREATE TRIGGER ontology_extension_nearest_statistic_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.ontology_extension_candidate_nearest_concept
FOR EACH ROW
EXECUTE FUNCTION corpus.guard_frozen_statistic_inventory();

CREATE INDEX normalized_expression_trgm_knn_idx
    ON corpus.normalized_expression
    USING GIST (normalized_text gist_trgm_ops (siglen = 64));

CREATE INDEX lexical_expression_normalization_normalized_idx
    ON corpus.lexical_expression_normalization (
        normalization_pipeline_id,
        normalized_expression_id,
        expression_id
    );

CREATE INDEX normalized_expression_occurrence_expression_idx
    ON corpus.normalized_expression_occurrence (
        normalized_expression_id,
        normalization_derivation_run_id,
        observation_expression_id
    );

CREATE INDEX normalized_expression_frequency_rank_idx
    ON corpus.normalized_expression_frequency (
        corpus_statistic_run_id,
        expression_frequency DESC,
        normalized_expression_id
    );

CREATE INDEX normalized_expression_pair_subject_npmi_idx
    ON corpus.normalized_expression_pair_measurement (
        corpus_statistic_run_id,
        subject_normalized_expression_id,
        normalized_pmi DESC,
        object_normalized_expression_id
    );

CREATE INDEX normalized_expression_pair_object_npmi_idx
    ON corpus.normalized_expression_pair_measurement (
        corpus_statistic_run_id,
        object_normalized_expression_id,
        normalized_pmi DESC,
        subject_normalized_expression_id
    );

CREATE VIEW corpus.v_normalized_expression_frequency AS
SELECT
    statistic_run.corpus_statistic_run_id,
    statistic_run.corpus_statistic_run_key,
    derivation.corpus_snapshot_id,
    pipeline.normalization_pipeline_key,
    normalized.normalized_expression_id,
    normalized.normalized_expression_key,
    normalized.normalized_text,
    frequency.expression_frequency,
    frequency.document_frequency,
    frequency.publisher_prevalence_count,
    frequency.publisher_sample_count,
    frequency.country_prevalence_count,
    frequency.country_sample_count,
    frequency.composite_reference_occurrence_count,
    frequency.qualifier_occurrence_count,
    frequency.unresolved_occurrence_count,
    frequency.value_semantics
FROM corpus.normalized_expression_frequency AS frequency
JOIN corpus.corpus_statistic_run AS statistic_run
  ON statistic_run.corpus_statistic_run_id =
     frequency.corpus_statistic_run_id
JOIN corpus.normalization_derivation_run AS derivation
  ON derivation.normalization_derivation_run_id =
     statistic_run.normalization_derivation_run_id
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalized_expression_id = frequency.normalized_expression_id
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id = normalized.normalization_pipeline_id;

COMMENT ON VIEW corpus.v_normalized_expression_frequency IS
    'Versioned normalized frequency, document frequency, publisher prevalence, optional explicit-country prevalence, and type/resolution observations.';

CREATE VIEW corpus.v_normalized_long_tail AS
SELECT
    frequency.*,
    frequency.expression_frequency = 1 AS is_hapax,
    CASE
        WHEN frequency.expression_frequency = 1 THEN 'HAPAX'
        WHEN frequency.expression_frequency <= 3 THEN 'VERY_RARE'
        WHEN frequency.expression_frequency <= 10 THEN 'RARE'
        ELSE 'RECURRENT'
    END AS frequency_band
FROM corpus.v_normalized_expression_frequency AS frequency;

COMMENT ON VIEW corpus.v_normalized_long_tail IS
    'Transparent long-tail bands; cut points are reporting conveniences, not ontology-admission thresholds.';

CREATE VIEW corpus.v_modifier_context AS
WITH directional_pair AS (
    SELECT
        pair.corpus_statistic_run_id,
        pair.subject_normalized_expression_id AS modifier_expression_id,
        pair.object_normalized_expression_id AS context_expression_id,
        pair.cooccurrence_document_count,
        pair.normalized_pmi,
        pair.subject_given_object_probability,
        pair.object_given_subject_probability,
        pair.value_semantics
    FROM corpus.normalized_expression_pair_measurement AS pair
    UNION ALL
    SELECT
        pair.corpus_statistic_run_id,
        pair.object_normalized_expression_id,
        pair.subject_normalized_expression_id,
        pair.cooccurrence_document_count,
        pair.normalized_pmi,
        pair.object_given_subject_probability,
        pair.subject_given_object_probability,
        pair.value_semantics
    FROM corpus.normalized_expression_pair_measurement AS pair
)
SELECT
    directional_pair.corpus_statistic_run_id,
    modifier.normalized_expression_key AS modifier_expression_key,
    modifier.normalized_text AS modifier_text,
    context.normalized_expression_key AS context_expression_key,
    context.normalized_text AS context_text,
    directional_pair.cooccurrence_document_count,
    directional_pair.normalized_pmi,
    directional_pair.subject_given_object_probability
        AS modifier_given_context_probability,
    directional_pair.object_given_subject_probability
        AS context_given_modifier_probability,
    directional_pair.value_semantics
FROM directional_pair
JOIN corpus.normalized_expression AS modifier
  ON modifier.normalized_expression_id =
     directional_pair.modifier_expression_id
JOIN corpus.normalized_expression AS context
  ON context.normalized_expression_id =
     directional_pair.context_expression_id
WHERE modifier.normalized_text IN (
    'bright',
    'clean',
    'juicy',
    'jammy',
    'tea-like',
    'winey'
);

COMMENT ON VIEW corpus.v_modifier_context IS
    'Observed co-occurrence contexts for the six Round 2B modifier probes. It does not assign formulas, intensities, or canonical modifier semantics.';

CREATE VIEW corpus.v_unresolved_normalized_expressions AS
SELECT
    occurrence.normalization_derivation_run_id,
    occurrence.normalized_expression_id,
    normalized.normalized_expression_key,
    normalized.normalized_text,
    count(*)::BIGINT AS occurrence_count,
    count(DISTINCT observation.captured_document_id)::BIGINT
        AS document_count
FROM corpus.normalized_expression_occurrence AS occurrence
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalized_expression_id = occurrence.normalized_expression_id
JOIN corpus.observation_expression AS observation_expression
  ON observation_expression.observation_expression_id =
     occurrence.observation_expression_id
JOIN corpus.raw_observation AS observation
  ON observation.raw_observation_id = observation_expression.raw_observation_id
LEFT JOIN corpus.observation_resolution AS resolution
  ON resolution.observation_expression_id =
     observation_expression.observation_expression_id
LEFT JOIN ref.resolution_status AS resolution_status
  ON resolution_status.resolution_status_code = resolution.resolution_status_code
WHERE NOT COALESCE(resolution_status.is_resolved, FALSE)
GROUP BY
    occurrence.normalization_derivation_run_id,
    occurrence.normalized_expression_id,
    normalized.normalized_expression_key,
    normalized.normalized_text;

COMMENT ON VIEW corpus.v_unresolved_normalized_expressions IS
    'Pending or explicitly unresolved observed expressions grouped under a frozen normalization derivation; absence of a forced mapping is preserved.';

CREATE VIEW corpus.v_round2b_normalization_inventory AS
SELECT
    derivation.normalization_derivation_run_id,
    derivation.normalization_derivation_run_key,
    derivation.corpus_snapshot_id,
    pipeline.normalization_pipeline_key,
    derivation.input_observation_count,
    derivation.output_occurrence_count,
    count(occurrence.normalized_expression_occurrence_id)::BIGINT
        AS stored_occurrence_count,
    count(DISTINCT occurrence.normalized_expression_id)::BIGINT
        AS unique_normalized_expression_count,
    count(DISTINCT observation_expression.expression_id)::BIGINT
        AS unique_surface_expression_count,
    derivation.input_inventory_sha256,
    derivation.output_inventory_sha256,
    derivation.code_commit_sha,
    derivation.frozen_at
FROM corpus.normalization_derivation_run AS derivation
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id = derivation.normalization_pipeline_id
LEFT JOIN corpus.normalized_expression_occurrence AS occurrence
  ON occurrence.normalization_derivation_run_id =
     derivation.normalization_derivation_run_id
LEFT JOIN corpus.observation_expression AS observation_expression
  ON observation_expression.observation_expression_id =
     occurrence.observation_expression_id
GROUP BY
    derivation.normalization_derivation_run_id,
    derivation.normalization_derivation_run_key,
    derivation.corpus_snapshot_id,
    pipeline.normalization_pipeline_key,
    derivation.input_observation_count,
    derivation.output_occurrence_count,
    derivation.input_inventory_sha256,
    derivation.output_inventory_sha256,
    derivation.code_commit_sha,
    derivation.frozen_at;

COMMENT ON VIEW corpus.v_round2b_normalization_inventory IS
    'Hash-addressed normalization inventory and declared-versus-stored occurrence counts for rebuild receipts.';

COMMIT;
