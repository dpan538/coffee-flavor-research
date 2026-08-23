\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Provenance, empirical evidence, captured language, regenerable model output,
-- and human governance are intentionally separated from canonical kb tables.
-- No table in this migration stores a universal sensory weight or promotes a
-- model result automatically.

BEGIN;

CREATE TABLE evidence.license_policy (
    license_policy_id BIGINT GENERATED ALWAYS AS IDENTITY,
    license_policy_key TEXT NOT NULL,
    access_class_code TEXT NOT NULL,
    rights_status_code TEXT NOT NULL,
    redistributable BOOLEAN NOT NULL,
    derivative_work_allowed BOOLEAN NOT NULL,
    commercial_use_allowed BOOLEAN NOT NULL,
    machine_use_allowed BOOLEAN NOT NULL,
    production_export_allowed BOOLEAN NOT NULL,
    checked_on DATE NOT NULL,
    notes TEXT,
    CONSTRAINT license_policy_pk PRIMARY KEY (license_policy_id),
    CONSTRAINT license_policy_key_uq UNIQUE (license_policy_key),
    CONSTRAINT license_policy_access_class_fk FOREIGN KEY (access_class_code)
        REFERENCES ref.access_class (access_class_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT license_policy_rights_status_fk FOREIGN KEY (rights_status_code)
        REFERENCES ref.rights_status (rights_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT license_policy_key_nonempty_ck CHECK (
        license_policy_key = btrim(license_policy_key)
        AND license_policy_key <> ''
    ),
    CONSTRAINT license_policy_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    ),
    CONSTRAINT license_policy_export_redistributable_ck CHECK (
        NOT production_export_allowed OR redistributable
    ),
    CONSTRAINT license_policy_export_derivatives_ck CHECK (
        NOT production_export_allowed OR derivative_work_allowed
    ),
    CONSTRAINT license_policy_export_commercial_ck CHECK (
        NOT production_export_allowed OR commercial_use_allowed
    ),
    CONSTRAINT license_policy_export_machine_use_ck CHECK (
        NOT production_export_allowed OR machine_use_allowed
    )
);

COMMENT ON TABLE evidence.license_policy IS
    'Versionable machine-readable rights decision. Production export is opt-in and implies all required reuse permissions.';

CREATE TABLE evidence.source (
    source_id BIGINT GENERATED ALWAYS AS IDENTITY,
    source_key TEXT NOT NULL,
    title TEXT NOT NULL,
    creator TEXT,
    publisher TEXT,
    citation TEXT NOT NULL,
    doi TEXT,
    source_url TEXT,
    external_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT source_pk PRIMARY KEY (source_id),
    CONSTRAINT source_key_uq UNIQUE (source_key),
    CONSTRAINT source_key_nonempty_ck CHECK (
        source_key = btrim(source_key) AND source_key <> ''
    ),
    CONSTRAINT source_title_nonempty_ck CHECK (
        title = btrim(title) AND title <> ''
    ),
    CONSTRAINT source_creator_nonempty_ck CHECK (
        creator IS NULL OR (creator = btrim(creator) AND creator <> '')
    ),
    CONSTRAINT source_publisher_nonempty_ck CHECK (
        publisher IS NULL OR (publisher = btrim(publisher) AND publisher <> '')
    ),
    CONSTRAINT source_citation_nonempty_ck CHECK (
        citation = btrim(citation) AND citation <> ''
    ),
    CONSTRAINT source_doi_nonempty_ck CHECK (
        doi IS NULL OR (doi = btrim(doi) AND doi <> '')
    ),
    CONSTRAINT source_url_nonempty_ck CHECK (
        source_url IS NULL OR (source_url = btrim(source_url) AND source_url <> '')
    ),
    CONSTRAINT source_external_metadata_object_ck CHECK (
        jsonb_typeof(external_metadata) = 'object'
    )
);

COMMENT ON TABLE evidence.source IS
    'Bibliographic identity only; copied definitions and source content do not belong in this table.';

CREATE TABLE evidence.source_version (
    source_version_id BIGINT GENERATED ALWAYS AS IDENTITY,
    source_version_key TEXT NOT NULL,
    source_id BIGINT NOT NULL,
    license_policy_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    published_on DATE,
    retrieved_on DATE,
    version_locator TEXT,
    external_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT source_version_pk PRIMARY KEY (source_version_id),
    CONSTRAINT source_version_key_uq UNIQUE (source_version_key),
    CONSTRAINT source_version_source_label_uq UNIQUE (source_id, version_label),
    CONSTRAINT source_version_source_fk FOREIGN KEY (source_id)
        REFERENCES evidence.source (source_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_version_license_policy_fk FOREIGN KEY (license_policy_id)
        REFERENCES evidence.license_policy (license_policy_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_version_key_nonempty_ck CHECK (
        source_version_key = btrim(source_version_key)
        AND source_version_key <> ''
    ),
    CONSTRAINT source_version_label_nonempty_ck CHECK (
        version_label = btrim(version_label) AND version_label <> ''
    ),
    CONSTRAINT source_version_locator_nonempty_ck CHECK (
        version_locator IS NULL
        OR (version_locator = btrim(version_locator) AND version_locator <> '')
    ),
    CONSTRAINT source_version_retrieval_date_ck CHECK (
        published_on IS NULL OR retrieved_on IS NULL OR retrieved_on >= published_on
    ),
    CONSTRAINT source_version_external_metadata_object_ck CHECK (
        jsonb_typeof(external_metadata) = 'object'
    )
);

COMMENT ON TABLE evidence.source_version IS
    'A citable source state with a mandatory, explicit licence and access decision.';

CREATE TABLE evidence.dataset (
    dataset_id BIGINT GENERATED ALWAYS AS IDENTITY,
    dataset_key TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    external_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT dataset_pk PRIMARY KEY (dataset_id),
    CONSTRAINT dataset_key_uq UNIQUE (dataset_key),
    CONSTRAINT dataset_source_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT dataset_key_nonempty_ck CHECK (
        dataset_key = btrim(dataset_key) AND dataset_key <> ''
    ),
    CONSTRAINT dataset_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT dataset_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    ),
    CONSTRAINT dataset_external_metadata_object_ck CHECK (
        jsonb_typeof(external_metadata) = 'object'
    )
);

COMMENT ON TABLE evidence.dataset IS
    'Versioned empirical or derived dataset; its source version supplies the applicable rights policy.';

CREATE TABLE evidence.statistical_method (
    statistical_method_id BIGINT GENERATED ALWAYS AS IDENTITY,
    method_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT statistical_method_pk PRIMARY KEY (statistical_method_id),
    CONSTRAINT statistical_method_key_uq UNIQUE (method_key),
    CONSTRAINT statistical_method_key_nonempty_ck CHECK (
        method_key = btrim(method_key) AND method_key <> ''
    ),
    CONSTRAINT statistical_method_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT statistical_method_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

CREATE TABLE evidence.measurement_scale (
    measurement_scale_id BIGINT GENERATED ALWAYS AS IDENTITY,
    scale_key TEXT NOT NULL,
    name TEXT NOT NULL,
    minimum_value NUMERIC NOT NULL,
    maximum_value NUMERIC NOT NULL,
    unit TEXT,
    value_semantics TEXT NOT NULL,
    CONSTRAINT measurement_scale_pk PRIMARY KEY (measurement_scale_id),
    CONSTRAINT measurement_scale_key_uq UNIQUE (scale_key),
    CONSTRAINT measurement_scale_key_nonempty_ck CHECK (
        scale_key = btrim(scale_key) AND scale_key <> ''
    ),
    CONSTRAINT measurement_scale_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT measurement_scale_bounds_ck CHECK (
        minimum_value < maximum_value
    ),
    CONSTRAINT measurement_scale_unit_nonempty_ck CHECK (
        unit IS NULL OR (unit = btrim(unit) AND unit <> '')
    ),
    CONSTRAINT measurement_scale_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    )
);

COMMENT ON TABLE evidence.measurement_scale IS
    'Declared numeric range and interpretation used by measurements; values are range-checked by a later trigger.';

CREATE TABLE evidence.concept_support (
    concept_support_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_support_key TEXT NOT NULL,
    concept_id BIGINT NOT NULL,
    source_version_id BIGINT,
    dataset_id BIGINT,
    locator TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT concept_support_pk PRIMARY KEY (concept_support_id),
    CONSTRAINT concept_support_key_uq UNIQUE (concept_support_key),
    CONSTRAINT concept_support_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_support_source_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_support_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_support_key_nonempty_ck CHECK (
        concept_support_key = btrim(concept_support_key)
        AND concept_support_key <> ''
    ),
    CONSTRAINT concept_support_origin_xor_ck CHECK (
        num_nonnulls(source_version_id, dataset_id) = 1
    ),
    CONSTRAINT concept_support_locator_nonempty_ck CHECK (
        locator = btrim(locator) AND locator <> ''
    ),
    CONSTRAINT concept_support_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE evidence.lexicalization_support (
    lexicalization_support_id BIGINT GENERATED ALWAYS AS IDENTITY,
    lexicalization_support_key TEXT NOT NULL,
    lexicalization_id BIGINT NOT NULL,
    source_version_id BIGINT,
    dataset_id BIGINT,
    locator TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT lexicalization_support_pk PRIMARY KEY (lexicalization_support_id),
    CONSTRAINT lexicalization_support_key_uq UNIQUE (lexicalization_support_key),
    CONSTRAINT lexicalization_support_lexicalization_fk FOREIGN KEY (lexicalization_id)
        REFERENCES kb.lexicalization (lexicalization_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_support_source_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_support_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_support_key_nonempty_ck CHECK (
        lexicalization_support_key = btrim(lexicalization_support_key)
        AND lexicalization_support_key <> ''
    ),
    CONSTRAINT lexicalization_support_origin_xor_ck CHECK (
        num_nonnulls(source_version_id, dataset_id) = 1
    ),
    CONSTRAINT lexicalization_support_locator_nonempty_ck CHECK (
        locator = btrim(locator) AND locator <> ''
    ),
    CONSTRAINT lexicalization_support_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE evidence.relation_support (
    relation_support_id BIGINT GENERATED ALWAYS AS IDENTITY,
    relation_support_key TEXT NOT NULL,
    concept_relation_id BIGINT NOT NULL,
    source_version_id BIGINT,
    dataset_id BIGINT,
    locator TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT relation_support_pk PRIMARY KEY (relation_support_id),
    CONSTRAINT relation_support_key_uq UNIQUE (relation_support_key),
    CONSTRAINT relation_support_relation_fk FOREIGN KEY (concept_relation_id)
        REFERENCES kb.concept_relation (concept_relation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relation_support_source_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relation_support_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relation_support_key_nonempty_ck CHECK (
        relation_support_key = btrim(relation_support_key)
        AND relation_support_key <> ''
    ),
    CONSTRAINT relation_support_origin_xor_ck CHECK (
        num_nonnulls(source_version_id, dataset_id) = 1
    ),
    CONSTRAINT relation_support_locator_nonempty_ck CHECK (
        locator = btrim(locator) AND locator <> ''
    ),
    CONSTRAINT relation_support_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE evidence.concept_dimension_link_support (
    concept_dimension_link_support_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_dimension_link_support_key TEXT NOT NULL,
    concept_dimension_link_id BIGINT NOT NULL,
    source_version_id BIGINT,
    dataset_id BIGINT,
    locator TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT concept_dimension_link_support_pk PRIMARY KEY (concept_dimension_link_support_id),
    CONSTRAINT concept_dimension_link_support_key_uq UNIQUE (concept_dimension_link_support_key),
    CONSTRAINT concept_dimension_link_support_link_fk FOREIGN KEY (concept_dimension_link_id)
        REFERENCES kb.concept_dimension_link (concept_dimension_link_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_support_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_support_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_support_key_nonempty_ck CHECK (
        concept_dimension_link_support_key = btrim(concept_dimension_link_support_key)
        AND concept_dimension_link_support_key <> ''
    ),
    CONSTRAINT concept_dimension_link_support_origin_xor_ck CHECK (
        num_nonnulls(source_version_id, dataset_id) = 1
    ),
    CONSTRAINT concept_dimension_link_support_locator_nonempty_ck CHECK (
        locator = btrim(locator) AND locator <> ''
    ),
    CONSTRAINT concept_dimension_link_support_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE evidence.empirical_pair_measurement (
    empirical_pair_measurement_id BIGINT GENERATED ALWAYS AS IDENTITY,
    measurement_key TEXT NOT NULL,
    subject_concept_id BIGINT NOT NULL,
    object_concept_id BIGINT NOT NULL,
    is_directional BOOLEAN NOT NULL,
    signal_domain_code TEXT NOT NULL,
    statistical_method_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,
    measurement_scale_id BIGINT NOT NULL,
    measured_value NUMERIC NOT NULL,
    value_semantics TEXT NOT NULL,
    sample_size BIGINT,
    uncertainty_value NUMERIC,
    uncertainty_semantics TEXT,
    context JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT empirical_pair_measurement_pk PRIMARY KEY (empirical_pair_measurement_id),
    CONSTRAINT empirical_pair_measurement_key_uq UNIQUE (measurement_key),
    CONSTRAINT empirical_pair_subject_fk FOREIGN KEY (subject_concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT empirical_pair_object_fk FOREIGN KEY (object_concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT empirical_pair_signal_domain_fk FOREIGN KEY (signal_domain_code)
        REFERENCES ref.signal_domain (signal_domain_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT empirical_pair_method_fk FOREIGN KEY (statistical_method_id)
        REFERENCES evidence.statistical_method (statistical_method_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT empirical_pair_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT empirical_pair_scale_fk FOREIGN KEY (measurement_scale_id)
        REFERENCES evidence.measurement_scale (measurement_scale_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT empirical_pair_key_nonempty_ck CHECK (
        measurement_key = btrim(measurement_key) AND measurement_key <> ''
    ),
    CONSTRAINT empirical_pair_distinct_endpoints_ck CHECK (
        subject_concept_id <> object_concept_id
    ),
    CONSTRAINT empirical_pair_nondirectional_order_ck CHECK (
        is_directional OR subject_concept_id < object_concept_id
    ),
    CONSTRAINT empirical_pair_value_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    ),
    CONSTRAINT empirical_pair_sample_size_positive_ck CHECK (
        sample_size IS NULL OR sample_size > 0
    ),
    CONSTRAINT empirical_pair_uncertainty_nonnegative_ck CHECK (
        uncertainty_value IS NULL OR uncertainty_value >= 0
    ),
    CONSTRAINT empirical_pair_uncertainty_semantics_ck CHECK (
        (uncertainty_value IS NULL AND uncertainty_semantics IS NULL)
        OR (
            uncertainty_value IS NOT NULL
            AND uncertainty_semantics = btrim(uncertainty_semantics)
            AND uncertainty_semantics <> ''
        )
    ),
    CONSTRAINT empirical_pair_context_object_ck CHECK (
        jsonb_typeof(context) = 'object'
    )
);

COMMENT ON TABLE evidence.empirical_pair_measurement IS
    'Independent typed pair measurements. Repeated rows for the same pair, dataset, and method remain permitted.';

CREATE TABLE evidence.projection_space (
    projection_space_id BIGINT GENERATED ALWAYS AS IDENTITY,
    projection_space_key TEXT NOT NULL,
    dataset_id BIGINT NOT NULL,
    statistical_method_id BIGINT NOT NULL,
    signal_domain_code TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    configuration JSONB NOT NULL,
    CONSTRAINT projection_space_pk PRIMARY KEY (projection_space_id),
    CONSTRAINT projection_space_key_uq UNIQUE (projection_space_key),
    CONSTRAINT projection_space_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT projection_space_method_fk FOREIGN KEY (statistical_method_id)
        REFERENCES evidence.statistical_method (statistical_method_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT projection_space_signal_domain_fk FOREIGN KEY (signal_domain_code)
        REFERENCES ref.signal_domain (signal_domain_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT projection_space_key_nonempty_ck CHECK (
        projection_space_key = btrim(projection_space_key)
        AND projection_space_key <> ''
    ),
    CONSTRAINT projection_space_model_name_nonempty_ck CHECK (
        model_name = btrim(model_name) AND model_name <> ''
    ),
    CONSTRAINT projection_space_model_version_nonempty_ck CHECK (
        model_version = btrim(model_version) AND model_version <> ''
    ),
    CONSTRAINT projection_space_configuration_object_ck CHECK (
        jsonb_typeof(configuration) = 'object'
    )
);

COMMENT ON TABLE evidence.projection_space IS
    'Dataset-, method-, signal-, and model-version-specific coordinate system; coordinates are never concept columns.';

CREATE TABLE evidence.projection_axis (
    projection_axis_id BIGINT GENERATED ALWAYS AS IDENTITY,
    projection_axis_key TEXT NOT NULL,
    projection_space_id BIGINT NOT NULL,
    axis_number SMALLINT NOT NULL,
    name TEXT NOT NULL,
    axis_semantics TEXT NOT NULL,
    explained_variance_ratio NUMERIC,
    CONSTRAINT projection_axis_pk PRIMARY KEY (projection_axis_id),
    CONSTRAINT projection_axis_key_uq UNIQUE (projection_axis_key),
    CONSTRAINT projection_axis_space_number_uq UNIQUE (projection_space_id, axis_number),
    CONSTRAINT projection_axis_space_fk FOREIGN KEY (projection_space_id)
        REFERENCES evidence.projection_space (projection_space_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT projection_axis_key_nonempty_ck CHECK (
        projection_axis_key = btrim(projection_axis_key)
        AND projection_axis_key <> ''
    ),
    CONSTRAINT projection_axis_number_positive_ck CHECK (axis_number > 0),
    CONSTRAINT projection_axis_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT projection_axis_semantics_nonempty_ck CHECK (
        axis_semantics = btrim(axis_semantics) AND axis_semantics <> ''
    ),
    CONSTRAINT projection_axis_variance_ratio_ck CHECK (
        explained_variance_ratio IS NULL
        OR (explained_variance_ratio >= 0 AND explained_variance_ratio <= 1)
    )
);

CREATE TABLE evidence.concept_projection_value (
    concept_projection_value_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_projection_value_key TEXT NOT NULL,
    projection_axis_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    coordinate_value NUMERIC NOT NULL,
    CONSTRAINT concept_projection_value_pk PRIMARY KEY (concept_projection_value_id),
    CONSTRAINT concept_projection_value_key_uq UNIQUE (concept_projection_value_key),
    CONSTRAINT concept_projection_value_axis_concept_uq UNIQUE (projection_axis_id, concept_id),
    CONSTRAINT concept_projection_value_axis_fk FOREIGN KEY (projection_axis_id)
        REFERENCES evidence.projection_axis (projection_axis_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_projection_value_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_projection_value_key_nonempty_ck CHECK (
        concept_projection_value_key = btrim(concept_projection_value_key)
        AND concept_projection_value_key <> ''
    )
);

CREATE TABLE evidence.sensory_reference (
    sensory_reference_id BIGINT GENERATED ALWAYS AS IDENTITY,
    sensory_reference_key TEXT NOT NULL,
    concept_id BIGINT NOT NULL,
    source_version_id BIGINT,
    name TEXT NOT NULL,
    material_description TEXT NOT NULL,
    preparation_notes TEXT,
    CONSTRAINT sensory_reference_pk PRIMARY KEY (sensory_reference_id),
    CONSTRAINT sensory_reference_key_uq UNIQUE (sensory_reference_key),
    CONSTRAINT sensory_reference_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sensory_reference_source_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sensory_reference_key_nonempty_ck CHECK (
        sensory_reference_key = btrim(sensory_reference_key)
        AND sensory_reference_key <> ''
    ),
    CONSTRAINT sensory_reference_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT sensory_reference_material_nonempty_ck CHECK (
        material_description = btrim(material_description)
        AND material_description <> ''
    ),
    CONSTRAINT sensory_reference_preparation_nonempty_ck CHECK (
        preparation_notes IS NULL
        OR (preparation_notes = btrim(preparation_notes) AND preparation_notes <> '')
    )
);

COMMENT ON TABLE evidence.sensory_reference IS
    'Protocol material associated with a concept; its existence does not assign an intrinsic intensity to that concept.';

CREATE TABLE evidence.reference_calibration (
    reference_calibration_id BIGINT GENERATED ALWAYS AS IDENTITY,
    reference_calibration_key TEXT NOT NULL,
    sensory_reference_id BIGINT NOT NULL,
    sensory_dimension_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,
    measurement_scale_id BIGINT NOT NULL,
    minimum_value NUMERIC NOT NULL,
    typical_value NUMERIC NOT NULL,
    maximum_value NUMERIC NOT NULL,
    protocol JSONB NOT NULL,
    CONSTRAINT reference_calibration_pk PRIMARY KEY (reference_calibration_id),
    CONSTRAINT reference_calibration_key_uq UNIQUE (reference_calibration_key),
    CONSTRAINT reference_calibration_reference_fk FOREIGN KEY (sensory_reference_id)
        REFERENCES evidence.sensory_reference (sensory_reference_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT reference_calibration_dimension_fk FOREIGN KEY (sensory_dimension_id)
        REFERENCES kb.sensory_dimension (sensory_dimension_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT reference_calibration_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT reference_calibration_scale_fk FOREIGN KEY (measurement_scale_id)
        REFERENCES evidence.measurement_scale (measurement_scale_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT reference_calibration_key_nonempty_ck CHECK (
        reference_calibration_key = btrim(reference_calibration_key)
        AND reference_calibration_key <> ''
    ),
    CONSTRAINT reference_calibration_value_order_ck CHECK (
        minimum_value <= typical_value AND typical_value <= maximum_value
    ),
    CONSTRAINT reference_calibration_protocol_object_ck CHECK (
        jsonb_typeof(protocol) = 'object'
    )
);

COMMENT ON TABLE evidence.reference_calibration IS
    'Dataset- and protocol-specific reference range; scale-bound validation is added in the constraints migration.';

CREATE TABLE corpus.corpus (
    corpus_id BIGINT GENERATED ALWAYS AS IDENTITY,
    corpus_key TEXT NOT NULL,
    name TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    description TEXT NOT NULL,
    capture_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT corpus_pk PRIMARY KEY (corpus_id),
    CONSTRAINT corpus_key_uq UNIQUE (corpus_key),
    CONSTRAINT corpus_language_tag_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_key_nonempty_ck CHECK (
        corpus_key = btrim(corpus_key) AND corpus_key <> ''
    ),
    CONSTRAINT corpus_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT corpus_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    ),
    CONSTRAINT corpus_capture_metadata_object_ck CHECK (
        jsonb_typeof(capture_metadata) = 'object'
    )
);

CREATE TABLE corpus.captured_document (
    captured_document_id BIGINT GENERATED ALWAYS AS IDENTITY,
    captured_document_key TEXT NOT NULL,
    corpus_id BIGINT NOT NULL,
    source_version_id BIGINT NOT NULL,
    external_document_key TEXT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    raw_text TEXT NOT NULL,
    capture_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT captured_document_pk PRIMARY KEY (captured_document_id),
    CONSTRAINT captured_document_key_uq UNIQUE (captured_document_key),
    CONSTRAINT captured_document_corpus_fk FOREIGN KEY (corpus_id)
        REFERENCES corpus.corpus (corpus_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT captured_document_source_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT captured_document_key_nonempty_ck CHECK (
        captured_document_key = btrim(captured_document_key)
        AND captured_document_key <> ''
    ),
    CONSTRAINT captured_document_external_key_nonempty_ck CHECK (
        external_document_key IS NULL
        OR (external_document_key = btrim(external_document_key) AND external_document_key <> '')
    ),
    CONSTRAINT captured_document_raw_text_nonempty_ck CHECK (
        btrim(raw_text) <> ''
    ),
    CONSTRAINT captured_document_metadata_object_ck CHECK (
        jsonb_typeof(capture_metadata) = 'object'
    )
);

COMMENT ON TABLE corpus.captured_document IS
    'Rights-gated raw source capture. Raw text is never canonical knowledge and is excluded from production export unless policy permits.';

CREATE TABLE corpus.raw_observation (
    raw_observation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    raw_observation_key TEXT NOT NULL,
    captured_document_id BIGINT NOT NULL,
    observation_text TEXT NOT NULL,
    character_start INTEGER,
    character_end INTEGER,
    observation_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT raw_observation_pk PRIMARY KEY (raw_observation_id),
    CONSTRAINT raw_observation_key_uq UNIQUE (raw_observation_key),
    CONSTRAINT raw_observation_document_fk FOREIGN KEY (captured_document_id)
        REFERENCES corpus.captured_document (captured_document_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_observation_key_nonempty_ck CHECK (
        raw_observation_key = btrim(raw_observation_key)
        AND raw_observation_key <> ''
    ),
    CONSTRAINT raw_observation_text_nonempty_ck CHECK (
        btrim(observation_text) <> ''
    ),
    CONSTRAINT raw_observation_offsets_ck CHECK (
        (character_start IS NULL AND character_end IS NULL)
        OR (
            character_start IS NOT NULL
            AND character_end IS NOT NULL
            AND character_start >= 0
            AND character_end > character_start
        )
    ),
    CONSTRAINT raw_observation_metadata_object_ck CHECK (
        jsonb_typeof(observation_metadata) = 'object'
    )
);

CREATE TABLE corpus.observation_expression (
    observation_expression_id BIGINT GENERATED ALWAYS AS IDENTITY,
    observation_expression_key TEXT NOT NULL,
    raw_observation_id BIGINT NOT NULL,
    expression_id BIGINT NOT NULL,
    occurrence_ordinal SMALLINT NOT NULL,
    CONSTRAINT observation_expression_pk PRIMARY KEY (observation_expression_id),
    CONSTRAINT observation_expression_key_uq UNIQUE (observation_expression_key),
    CONSTRAINT observation_expression_observation_ordinal_uq UNIQUE (
        raw_observation_id,
        occurrence_ordinal
    ),
    CONSTRAINT observation_expression_observation_fk FOREIGN KEY (raw_observation_id)
        REFERENCES corpus.raw_observation (raw_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_expression_expression_fk FOREIGN KEY (expression_id)
        REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_expression_key_nonempty_ck CHECK (
        observation_expression_key = btrim(observation_expression_key)
        AND observation_expression_key <> ''
    ),
    CONSTRAINT observation_expression_ordinal_positive_ck CHECK (
        occurrence_ordinal > 0
    )
);

CREATE TABLE corpus.observation_resolution (
    observation_resolution_id BIGINT GENERATED ALWAYS AS IDENTITY,
    observation_resolution_key TEXT NOT NULL,
    observation_expression_id BIGINT NOT NULL,
    resolution_status_code TEXT NOT NULL,
    lexicalization_id BIGINT,
    resolution_note TEXT,
    CONSTRAINT observation_resolution_pk PRIMARY KEY (observation_resolution_id),
    CONSTRAINT observation_resolution_key_uq UNIQUE (observation_resolution_key),
    CONSTRAINT observation_resolution_expression_uq UNIQUE (observation_expression_id),
    CONSTRAINT observation_resolution_expression_fk FOREIGN KEY (observation_expression_id)
        REFERENCES corpus.observation_expression (observation_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_status_fk FOREIGN KEY (resolution_status_code)
        REFERENCES ref.resolution_status (resolution_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_lexicalization_fk FOREIGN KEY (lexicalization_id)
        REFERENCES kb.lexicalization (lexicalization_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_key_nonempty_ck CHECK (
        observation_resolution_key = btrim(observation_resolution_key)
        AND observation_resolution_key <> ''
    ),
    CONSTRAINT observation_resolution_note_nonempty_ck CHECK (
        resolution_note IS NULL
        OR (resolution_note = btrim(resolution_note) AND resolution_note <> '')
    )
);

COMMENT ON TABLE corpus.observation_resolution IS
    'Current human/rule resolution of an observed expression. Status-to-nullability consistency is enforced by a later semantic trigger.';

CREATE TABLE corpus.expression_cooccurrence_measurement (
    expression_cooccurrence_measurement_id BIGINT GENERATED ALWAYS AS IDENTITY,
    measurement_key TEXT NOT NULL,
    corpus_id BIGINT NOT NULL,
    subject_expression_id BIGINT NOT NULL,
    object_expression_id BIGINT NOT NULL,
    signal_domain_code TEXT NOT NULL,
    statistical_method_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,
    measurement_scale_id BIGINT NOT NULL,
    measured_value NUMERIC NOT NULL,
    value_semantics TEXT NOT NULL,
    observation_count BIGINT,
    context JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT expression_cooccurrence_measurement_pk PRIMARY KEY (
        expression_cooccurrence_measurement_id
    ),
    CONSTRAINT expression_cooccurrence_measurement_key_uq UNIQUE (measurement_key),
    CONSTRAINT expression_cooccurrence_corpus_fk FOREIGN KEY (corpus_id)
        REFERENCES corpus.corpus (corpus_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_subject_fk FOREIGN KEY (subject_expression_id)
        REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_object_fk FOREIGN KEY (object_expression_id)
        REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_signal_domain_fk FOREIGN KEY (signal_domain_code)
        REFERENCES ref.signal_domain (signal_domain_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_method_fk FOREIGN KEY (statistical_method_id)
        REFERENCES evidence.statistical_method (statistical_method_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_scale_fk FOREIGN KEY (measurement_scale_id)
        REFERENCES evidence.measurement_scale (measurement_scale_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT expression_cooccurrence_key_nonempty_ck CHECK (
        measurement_key = btrim(measurement_key) AND measurement_key <> ''
    ),
    CONSTRAINT expression_cooccurrence_endpoint_order_ck CHECK (
        subject_expression_id < object_expression_id
    ),
    CONSTRAINT expression_cooccurrence_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    ),
    CONSTRAINT expression_cooccurrence_count_positive_ck CHECK (
        observation_count IS NULL OR observation_count > 0
    ),
    CONSTRAINT expression_cooccurrence_context_object_ck CHECK (
        jsonb_typeof(context) = 'object'
    )
);

COMMENT ON TABLE corpus.expression_cooccurrence_measurement IS
    'Typed corpus association measurement; co-occurrence is not a perceptual or linguistic-semantic similarity assertion.';

CREATE TABLE ml.model (
    model_id BIGINT GENERATED ALWAYS AS IDENTITY,
    model_key TEXT NOT NULL,
    name TEXT NOT NULL,
    model_family TEXT NOT NULL,
    description TEXT NOT NULL,
    external_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT model_pk PRIMARY KEY (model_id),
    CONSTRAINT model_key_uq UNIQUE (model_key),
    CONSTRAINT model_key_nonempty_ck CHECK (
        model_key = btrim(model_key) AND model_key <> ''
    ),
    CONSTRAINT model_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT model_family_nonempty_ck CHECK (
        model_family = btrim(model_family) AND model_family <> ''
    ),
    CONSTRAINT model_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    ),
    CONSTRAINT model_external_metadata_object_ck CHECK (
        jsonb_typeof(external_metadata) = 'object'
    )
);

CREATE TABLE ml.model_version (
    model_version_id BIGINT GENERATED ALWAYS AS IDENTITY,
    model_version_key TEXT NOT NULL,
    model_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    artifact_locator TEXT,
    configuration JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT model_version_pk PRIMARY KEY (model_version_id),
    CONSTRAINT model_version_key_uq UNIQUE (model_version_key),
    CONSTRAINT model_version_model_label_uq UNIQUE (model_id, version_label),
    CONSTRAINT model_version_model_fk FOREIGN KEY (model_id)
        REFERENCES ml.model (model_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_version_key_nonempty_ck CHECK (
        model_version_key = btrim(model_version_key)
        AND model_version_key <> ''
    ),
    CONSTRAINT model_version_label_nonempty_ck CHECK (
        version_label = btrim(version_label) AND version_label <> ''
    ),
    CONSTRAINT model_version_artifact_locator_nonempty_ck CHECK (
        artifact_locator IS NULL
        OR (artifact_locator = btrim(artifact_locator) AND artifact_locator <> '')
    ),
    CONSTRAINT model_version_configuration_object_ck CHECK (
        jsonb_typeof(configuration) = 'object'
    )
);

CREATE TABLE ml.model_run (
    model_run_id BIGINT GENERATED ALWAYS AS IDENTITY,
    model_run_key TEXT NOT NULL,
    model_version_id BIGINT NOT NULL,
    model_run_status_code TEXT NOT NULL,
    input_dataset_id BIGINT,
    input_corpus_id BIGINT,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    random_seed BIGINT,
    run_configuration JSONB NOT NULL,
    result_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT model_run_pk PRIMARY KEY (model_run_id),
    CONSTRAINT model_run_key_uq UNIQUE (model_run_key),
    CONSTRAINT model_run_model_version_fk FOREIGN KEY (model_version_id)
        REFERENCES ml.model_version (model_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_run_status_fk FOREIGN KEY (model_run_status_code)
        REFERENCES ref.model_run_status (model_run_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_run_dataset_fk FOREIGN KEY (input_dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_run_corpus_fk FOREIGN KEY (input_corpus_id)
        REFERENCES corpus.corpus (corpus_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_run_key_nonempty_ck CHECK (
        model_run_key = btrim(model_run_key) AND model_run_key <> ''
    ),
    CONSTRAINT model_run_input_present_ck CHECK (
        num_nonnulls(input_dataset_id, input_corpus_id) >= 1
    ),
    CONSTRAINT model_run_time_order_ck CHECK (
        completed_at IS NULL OR completed_at >= started_at
    ),
    CONSTRAINT model_run_configuration_object_ck CHECK (
        jsonb_typeof(run_configuration) = 'object'
    ),
    CONSTRAINT model_run_result_metadata_object_ck CHECK (
        jsonb_typeof(result_metadata) = 'object'
    )
);

CREATE TABLE ml.mapping_inference (
    mapping_inference_id BIGINT GENERATED ALWAYS AS IDENTITY,
    mapping_inference_key TEXT NOT NULL,
    model_run_id BIGINT NOT NULL,
    observation_expression_id BIGINT NOT NULL,
    resolution_status_code TEXT NOT NULL,
    inferred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolution_notes TEXT,
    CONSTRAINT mapping_inference_pk PRIMARY KEY (mapping_inference_id),
    CONSTRAINT mapping_inference_key_uq UNIQUE (mapping_inference_key),
    CONSTRAINT mapping_inference_run_expression_uq UNIQUE (
        model_run_id,
        observation_expression_id
    ),
    CONSTRAINT mapping_inference_model_run_fk FOREIGN KEY (model_run_id)
        REFERENCES ml.model_run (model_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_inference_observation_expression_fk FOREIGN KEY (observation_expression_id)
        REFERENCES corpus.observation_expression (observation_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_inference_resolution_status_fk FOREIGN KEY (resolution_status_code)
        REFERENCES ref.resolution_status (resolution_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_inference_key_nonempty_ck CHECK (
        mapping_inference_key = btrim(mapping_inference_key)
        AND mapping_inference_key <> ''
    ),
    CONSTRAINT mapping_inference_notes_nonempty_ck CHECK (
        resolution_notes IS NULL
        OR (resolution_notes = btrim(resolution_notes) AND resolution_notes <> '')
    )
);

COMMENT ON TABLE ml.mapping_inference IS
    'Model-run-specific retrieval outcome. An explicit unresolved status may have no candidates and is never forced to a concept.';

CREATE TABLE ml.mapping_candidate (
    mapping_candidate_id BIGINT GENERATED ALWAYS AS IDENTITY,
    mapping_candidate_key TEXT NOT NULL,
    mapping_inference_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    candidate_status_code TEXT NOT NULL,
    rank INTEGER NOT NULL,
    rationale TEXT,
    CONSTRAINT mapping_candidate_pk PRIMARY KEY (mapping_candidate_id),
    CONSTRAINT mapping_candidate_key_uq UNIQUE (mapping_candidate_key),
    CONSTRAINT mapping_candidate_inference_rank_uq UNIQUE (mapping_inference_id, rank),
    CONSTRAINT mapping_candidate_inference_concept_uq UNIQUE (mapping_inference_id, concept_id),
    CONSTRAINT mapping_candidate_inference_fk FOREIGN KEY (mapping_inference_id)
        REFERENCES ml.mapping_inference (mapping_inference_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_candidate_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_candidate_status_fk FOREIGN KEY (candidate_status_code)
        REFERENCES ref.candidate_status (candidate_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_candidate_key_nonempty_ck CHECK (
        mapping_candidate_key = btrim(mapping_candidate_key)
        AND mapping_candidate_key <> ''
    ),
    CONSTRAINT mapping_candidate_rank_positive_ck CHECK (rank > 0),
    CONSTRAINT mapping_candidate_rationale_nonempty_ck CHECK (
        rationale IS NULL OR (rationale = btrim(rationale) AND rationale <> '')
    )
);

COMMENT ON TABLE ml.mapping_candidate IS
    'Ranked candidate concept without a universal aggregate score; heterogeneous evidence remains in candidate_signal.';

CREATE TABLE ml.candidate_signal (
    candidate_signal_id BIGINT GENERATED ALWAYS AS IDENTITY,
    candidate_signal_key TEXT NOT NULL,
    mapping_candidate_id BIGINT NOT NULL,
    signal_domain_code TEXT NOT NULL,
    statistical_method_id BIGINT NOT NULL,
    dataset_id BIGINT NOT NULL,
    measurement_scale_id BIGINT NOT NULL,
    signal_value NUMERIC NOT NULL,
    value_semantics TEXT NOT NULL,
    context JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT candidate_signal_pk PRIMARY KEY (candidate_signal_id),
    CONSTRAINT candidate_signal_key_uq UNIQUE (candidate_signal_key),
    CONSTRAINT candidate_signal_candidate_fk FOREIGN KEY (mapping_candidate_id)
        REFERENCES ml.mapping_candidate (mapping_candidate_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_signal_domain_fk FOREIGN KEY (signal_domain_code)
        REFERENCES ref.signal_domain (signal_domain_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_signal_method_fk FOREIGN KEY (statistical_method_id)
        REFERENCES evidence.statistical_method (statistical_method_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_signal_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_signal_scale_fk FOREIGN KEY (measurement_scale_id)
        REFERENCES evidence.measurement_scale (measurement_scale_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_signal_key_nonempty_ck CHECK (
        candidate_signal_key = btrim(candidate_signal_key)
        AND candidate_signal_key <> ''
    ),
    CONSTRAINT candidate_signal_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    ),
    CONSTRAINT candidate_signal_context_object_ck CHECK (
        jsonb_typeof(context) = 'object'
    )
);

CREATE TABLE audit.reviewer (
    reviewer_id BIGINT GENERATED ALWAYS AS IDENTITY,
    reviewer_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    affiliation TEXT,
    CONSTRAINT reviewer_pk PRIMARY KEY (reviewer_id),
    CONSTRAINT reviewer_key_uq UNIQUE (reviewer_key),
    CONSTRAINT reviewer_key_nonempty_ck CHECK (
        reviewer_key = btrim(reviewer_key) AND reviewer_key <> ''
    ),
    CONSTRAINT reviewer_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT reviewer_affiliation_nonempty_ck CHECK (
        affiliation IS NULL
        OR (affiliation = btrim(affiliation) AND affiliation <> '')
    )
);

CREATE TABLE audit.review (
    review_id BIGINT GENERATED ALWAYS AS IDENTITY,
    review_key TEXT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    review_decision_code TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    independence_statement TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT review_pk PRIMARY KEY (review_id),
    CONSTRAINT review_key_uq UNIQUE (review_key),
    CONSTRAINT review_reviewer_fk FOREIGN KEY (reviewer_id)
        REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT review_decision_fk FOREIGN KEY (review_decision_code)
        REFERENCES ref.review_decision (review_decision_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT review_key_nonempty_ck CHECK (
        review_key = btrim(review_key) AND review_key <> ''
    ),
    CONSTRAINT review_independence_nonempty_ck CHECK (
        independence_statement = btrim(independence_statement)
        AND independence_statement <> ''
    ),
    CONSTRAINT review_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE audit.mapping_review (
    review_id BIGINT NOT NULL,
    mapping_candidate_id BIGINT NOT NULL,
    CONSTRAINT mapping_review_pk PRIMARY KEY (review_id),
    CONSTRAINT mapping_review_review_fk FOREIGN KEY (review_id)
        REFERENCES audit.review (review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT mapping_review_candidate_fk FOREIGN KEY (mapping_candidate_id)
        REFERENCES ml.mapping_candidate (mapping_candidate_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

COMMENT ON TABLE audit.mapping_review IS
    'Subtype of audit.review targeting one inferred mapping candidate; multiple independent reviews of a candidate are permitted.';

CREATE TABLE audit.concept_lifecycle_event (
    concept_lifecycle_event_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_lifecycle_event_key TEXT NOT NULL,
    concept_id BIGINT NOT NULL,
    review_id BIGINT,
    from_lifecycle_status_code TEXT,
    to_lifecycle_status_code TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rationale TEXT NOT NULL,
    CONSTRAINT concept_lifecycle_event_pk PRIMARY KEY (concept_lifecycle_event_id),
    CONSTRAINT concept_lifecycle_event_key_uq UNIQUE (concept_lifecycle_event_key),
    CONSTRAINT concept_lifecycle_event_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_lifecycle_event_review_fk FOREIGN KEY (review_id)
        REFERENCES audit.review (review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_lifecycle_event_from_status_fk FOREIGN KEY (from_lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_lifecycle_event_to_status_fk FOREIGN KEY (to_lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_lifecycle_event_key_nonempty_ck CHECK (
        concept_lifecycle_event_key = btrim(concept_lifecycle_event_key)
        AND concept_lifecycle_event_key <> ''
    ),
    CONSTRAINT concept_lifecycle_event_status_change_ck CHECK (
        from_lifecycle_status_code IS NULL
        OR from_lifecycle_status_code <> to_lifecycle_status_code
    ),
    CONSTRAINT concept_lifecycle_event_rationale_nonempty_ck CHECK (
        rationale = btrim(rationale) AND rationale <> ''
    )
);

CREATE TABLE audit.promotion_event (
    promotion_event_id BIGINT GENERATED ALWAYS AS IDENTITY,
    promotion_event_key TEXT NOT NULL,
    review_id BIGINT NOT NULL,
    target_concept_id BIGINT,
    target_lexicalization_id BIGINT,
    target_concept_relation_id BIGINT,
    target_concept_dimension_link_id BIGINT,
    promoted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rationale TEXT NOT NULL,
    CONSTRAINT promotion_event_pk PRIMARY KEY (promotion_event_id),
    CONSTRAINT promotion_event_key_uq UNIQUE (promotion_event_key),
    CONSTRAINT promotion_event_review_fk FOREIGN KEY (review_id)
        REFERENCES audit.review (review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT promotion_event_concept_fk FOREIGN KEY (target_concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT promotion_event_lexicalization_fk FOREIGN KEY (target_lexicalization_id)
        REFERENCES kb.lexicalization (lexicalization_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT promotion_event_relation_fk FOREIGN KEY (target_concept_relation_id)
        REFERENCES kb.concept_relation (concept_relation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT promotion_event_dimension_link_fk FOREIGN KEY (target_concept_dimension_link_id)
        REFERENCES kb.concept_dimension_link (concept_dimension_link_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT promotion_event_key_nonempty_ck CHECK (
        promotion_event_key = btrim(promotion_event_key)
        AND promotion_event_key <> ''
    ),
    CONSTRAINT promotion_event_exactly_one_target_ck CHECK (
        num_nonnulls(
            target_concept_id,
            target_lexicalization_id,
            target_concept_relation_id,
            target_concept_dimension_link_id
        ) = 1
    ),
    CONSTRAINT promotion_event_rationale_nonempty_ck CHECK (
        rationale = btrim(rationale) AND rationale <> ''
    )
);

COMMENT ON TABLE audit.promotion_event IS
    'Explicit governance event targeting exactly one canonical object. A later trigger verifies that the linked review permits promotion.';

COMMIT;
