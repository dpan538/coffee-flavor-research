\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- Round 3A contextual-condition domain.
-- Preparation, beverage additions, roast labels, and roast measurements are
-- experimental/serving context. They are deliberately not kb.concept rows,
-- corpus language truth, or model output.

BEGIN;

CREATE SCHEMA context;

COMMENT ON SCHEMA context IS
    'Versioned preparation, beverage-addition, and roast context kept separate from canonical sensory knowledge, corpus observations, and model inference.';

CREATE TABLE ref.context_value_status (
    context_value_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    has_normalized_value BOOLEAN NOT NULL,
    has_reported_unresolved_value BOOLEAN NOT NULL,
    CONSTRAINT context_value_status_pk PRIMARY KEY (context_value_status_code),
    CONSTRAINT context_value_status_text_ck CHECK (
        context_value_status_code = lower(btrim(context_value_status_code))
        AND context_value_status_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT context_value_status_semantics_ck CHECK (
        NOT (has_normalized_value AND has_reported_unresolved_value)
    )
);

CREATE TABLE ref.context_assertion_role (
    context_assertion_role_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT context_assertion_role_pk PRIMARY KEY (context_assertion_role_code),
    CONSTRAINT context_assertion_role_text_ck CHECK (
        context_assertion_role_code = lower(btrim(context_assertion_role_code))
        AND context_assertion_role_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.preparation_concept_type (
    preparation_concept_type_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT preparation_concept_type_pk PRIMARY KEY (preparation_concept_type_code),
    CONSTRAINT preparation_concept_type_text_ck CHECK (
        preparation_concept_type_code = lower(btrim(preparation_concept_type_code))
        AND preparation_concept_type_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.context_relation_type (
    context_relation_type_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_hierarchical BOOLEAN NOT NULL,
    is_symmetric BOOLEAN NOT NULL,
    CONSTRAINT context_relation_type_pk PRIMARY KEY (context_relation_type_code),
    CONSTRAINT context_relation_type_text_ck CHECK (
        context_relation_type_code = lower(btrim(context_relation_type_code))
        AND context_relation_type_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT context_relation_type_semantics_ck CHECK (
        NOT (is_hierarchical AND is_symmetric)
    )
);

CREATE TABLE ref.context_mapping_certainty (
    context_mapping_certainty_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_ambiguous BOOLEAN NOT NULL,
    CONSTRAINT context_mapping_certainty_pk PRIMARY KEY (context_mapping_certainty_code),
    CONSTRAINT context_mapping_certainty_text_ck CHECK (
        context_mapping_certainty_code = lower(btrim(context_mapping_certainty_code))
        AND context_mapping_certainty_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.roast_scheme_kind (
    roast_scheme_kind_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_ordinal BOOLEAN NOT NULL,
    CONSTRAINT roast_scheme_kind_pk PRIMARY KEY (roast_scheme_kind_code),
    CONSTRAINT roast_scheme_kind_text_ck CHECK (
        roast_scheme_kind_code = lower(btrim(roast_scheme_kind_code))
        AND roast_scheme_kind_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.roast_measurement_basis (
    roast_measurement_basis_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT roast_measurement_basis_pk PRIMARY KEY (roast_measurement_basis_code),
    CONSTRAINT roast_measurement_basis_text_ck CHECK (
        roast_measurement_basis_code = lower(btrim(roast_measurement_basis_code))
        AND roast_measurement_basis_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.addition_presence (
    addition_presence_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    allows_addition_rows BOOLEAN NOT NULL,
    CONSTRAINT addition_presence_pk PRIMARY KEY (addition_presence_code),
    CONSTRAINT addition_presence_text_ck CHECK (
        addition_presence_code = lower(btrim(addition_presence_code))
        AND addition_presence_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

CREATE TABLE context.preparation_concept (
    preparation_concept_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_concept_key TEXT NOT NULL,
    preparation_concept_type_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    preferred_label TEXT NOT NULL,
    description TEXT NOT NULL,
    c0_top_level BOOLEAN NOT NULL DEFAULT FALSE,
    c0_second_level BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT preparation_concept_pk PRIMARY KEY (preparation_concept_id),
    CONSTRAINT preparation_concept_key_uq UNIQUE (preparation_concept_key),
    CONSTRAINT preparation_concept_type_fk FOREIGN KEY (preparation_concept_type_code)
        REFERENCES ref.preparation_concept_type (preparation_concept_type_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_concept_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_concept_text_ck CHECK (
        preparation_concept_key = lower(btrim(preparation_concept_key))
        AND preparation_concept_key <> ''
        AND preferred_label = btrim(preferred_label) AND preferred_label <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT preparation_concept_c0_level_ck CHECK (
        NOT (c0_top_level AND c0_second_level)
        AND (NOT c0_top_level OR preparation_concept_type_code = 'family')
    )
);

CREATE TABLE context.preparation_concept_support (
    preparation_concept_support_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_concept_support_key TEXT NOT NULL,
    preparation_concept_id BIGINT NOT NULL,
    source_version_id BIGINT NOT NULL,
    context_assertion_role_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT preparation_concept_support_pk PRIMARY KEY (preparation_concept_support_id),
    CONSTRAINT preparation_concept_support_key_uq UNIQUE (preparation_concept_support_key),
    CONSTRAINT preparation_concept_support_fact_uq UNIQUE (
        preparation_concept_id, source_version_id, context_assertion_role_code, evidence_locator
    ),
    CONSTRAINT preparation_concept_support_concept_fk FOREIGN KEY (preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_concept_support_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_concept_support_role_fk FOREIGN KEY (context_assertion_role_code)
        REFERENCES ref.context_assertion_role (context_assertion_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_concept_support_text_ck CHECK (
        preparation_concept_support_key = lower(btrim(preparation_concept_support_key))
        AND preparation_concept_support_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
        AND (notes IS NULL OR (notes = btrim(notes) AND notes <> ''))
    )
);

CREATE TABLE context.preparation_relation (
    preparation_relation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_relation_key TEXT NOT NULL,
    subject_preparation_concept_id BIGINT NOT NULL,
    context_relation_type_code TEXT NOT NULL,
    object_preparation_concept_id BIGINT NOT NULL,
    source_version_id BIGINT NOT NULL,
    context_assertion_role_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT preparation_relation_pk PRIMARY KEY (preparation_relation_id),
    CONSTRAINT preparation_relation_key_uq UNIQUE (preparation_relation_key),
    CONSTRAINT preparation_relation_fact_uq UNIQUE (
        subject_preparation_concept_id,
        context_relation_type_code,
        object_preparation_concept_id
    ),
    CONSTRAINT preparation_relation_subject_fk FOREIGN KEY (subject_preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_relation_object_fk FOREIGN KEY (object_preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_relation_type_fk FOREIGN KEY (context_relation_type_code)
        REFERENCES ref.context_relation_type (context_relation_type_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_relation_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_relation_role_fk FOREIGN KEY (context_assertion_role_code)
        REFERENCES ref.context_assertion_role (context_assertion_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_relation_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_relation_text_ck CHECK (
        preparation_relation_key = lower(btrim(preparation_relation_key))
        AND preparation_relation_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
    ),
    CONSTRAINT preparation_relation_no_self_ck CHECK (
        subject_preparation_concept_id <> object_preparation_concept_id
    ),
    CONSTRAINT preparation_relation_symmetric_order_ck CHECK (
        context_relation_type_code <> 'related_to'
        OR subject_preparation_concept_id < object_preparation_concept_id
    )
);

CREATE TABLE context.preparation_expression (
    preparation_expression_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_expression_key TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    expression_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT preparation_expression_pk PRIMARY KEY (preparation_expression_id),
    CONSTRAINT preparation_expression_key_uq UNIQUE (preparation_expression_key),
    CONSTRAINT preparation_expression_normalized_uq UNIQUE (language_tag_code, normalized_text),
    CONSTRAINT preparation_expression_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_text_ck CHECK (
        preparation_expression_key = lower(btrim(preparation_expression_key))
        AND preparation_expression_key <> ''
        AND expression_text = btrim(expression_text) AND expression_text <> ''
        AND normalized_text = lower(btrim(normalized_text)) AND normalized_text <> ''
    )
);

CREATE TABLE context.preparation_expression_mapping (
    preparation_expression_mapping_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_expression_mapping_key TEXT NOT NULL,
    preparation_expression_id BIGINT NOT NULL,
    preparation_concept_id BIGINT NOT NULL,
    context_mapping_certainty_code TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    context_assertion_role_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT preparation_expression_mapping_pk PRIMARY KEY (preparation_expression_mapping_id),
    CONSTRAINT preparation_expression_mapping_key_uq UNIQUE (preparation_expression_mapping_key),
    CONSTRAINT preparation_expression_mapping_fact_uq UNIQUE (
        preparation_expression_id, preparation_concept_id
    ),
    CONSTRAINT preparation_expression_mapping_expression_fk FOREIGN KEY (preparation_expression_id)
        REFERENCES context.preparation_expression (preparation_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_mapping_concept_fk FOREIGN KEY (preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_mapping_certainty_fk FOREIGN KEY (context_mapping_certainty_code)
        REFERENCES ref.context_mapping_certainty (context_mapping_certainty_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_mapping_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_mapping_role_fk FOREIGN KEY (context_assertion_role_code)
        REFERENCES ref.context_assertion_role (context_assertion_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_mapping_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_expression_mapping_text_ck CHECK (
        preparation_expression_mapping_key = lower(btrim(preparation_expression_mapping_key))
        AND preparation_expression_mapping_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
    )
);

CREATE TABLE context.roast_scheme (
    roast_scheme_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_scheme_key TEXT NOT NULL,
    roast_scheme_kind_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_project_normalized_target BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT roast_scheme_pk PRIMARY KEY (roast_scheme_id),
    CONSTRAINT roast_scheme_key_uq UNIQUE (roast_scheme_key),
    CONSTRAINT roast_scheme_kind_fk FOREIGN KEY (roast_scheme_kind_code)
        REFERENCES ref.roast_scheme_kind (roast_scheme_kind_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_scheme_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_scheme_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_scheme_text_ck CHECK (
        roast_scheme_key = lower(btrim(roast_scheme_key)) AND roast_scheme_key <> ''
        AND name = btrim(name) AND name <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT roast_scheme_target_kind_ck CHECK (
        NOT is_project_normalized_target OR roast_scheme_kind_code = 'project_user_scale'
    )
);

CREATE UNIQUE INDEX roast_scheme_one_project_target_uq
    ON context.roast_scheme (is_project_normalized_target)
    WHERE is_project_normalized_target;

CREATE TABLE context.roast_category (
    roast_category_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_category_key TEXT NOT NULL,
    roast_scheme_id BIGINT NOT NULL,
    source_category_code TEXT NOT NULL,
    preferred_label TEXT NOT NULL,
    ordinal_position SMALLINT,
    lifecycle_status_code TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT roast_category_pk PRIMARY KEY (roast_category_id),
    CONSTRAINT roast_category_key_uq UNIQUE (roast_category_key),
    CONSTRAINT roast_category_scheme_code_uq UNIQUE (roast_scheme_id, source_category_code),
    CONSTRAINT roast_category_scheme_ordinal_uq UNIQUE (roast_scheme_id, ordinal_position),
    CONSTRAINT roast_category_scheme_fk FOREIGN KEY (roast_scheme_id)
        REFERENCES context.roast_scheme (roast_scheme_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_text_ck CHECK (
        roast_category_key = lower(btrim(roast_category_key)) AND roast_category_key <> ''
        AND source_category_code = lower(btrim(source_category_code)) AND source_category_code <> ''
        AND preferred_label = btrim(preferred_label) AND preferred_label <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT roast_category_ordinal_ck CHECK (
        ordinal_position IS NULL OR ordinal_position > 0
    )
);

CREATE TABLE context.roast_category_mapping (
    roast_category_mapping_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_category_mapping_key TEXT NOT NULL,
    source_roast_category_id BIGINT NOT NULL,
    normalized_roast_category_id BIGINT NOT NULL,
    context_mapping_certainty_code TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    context_assertion_role_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT roast_category_mapping_pk PRIMARY KEY (roast_category_mapping_id),
    CONSTRAINT roast_category_mapping_key_uq UNIQUE (roast_category_mapping_key),
    CONSTRAINT roast_category_mapping_fact_uq UNIQUE (
        source_roast_category_id, normalized_roast_category_id
    ),
    CONSTRAINT roast_category_mapping_source_category_fk FOREIGN KEY (source_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_mapping_target_category_fk FOREIGN KEY (normalized_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_mapping_certainty_fk FOREIGN KEY (context_mapping_certainty_code)
        REFERENCES ref.context_mapping_certainty (context_mapping_certainty_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_mapping_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_mapping_role_fk FOREIGN KEY (context_assertion_role_code)
        REFERENCES ref.context_assertion_role (context_assertion_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_mapping_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_category_mapping_text_ck CHECK (
        roast_category_mapping_key = lower(btrim(roast_category_mapping_key))
        AND roast_category_mapping_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
    ),
    CONSTRAINT roast_category_mapping_not_self_ck CHECK (
        source_roast_category_id <> normalized_roast_category_id
    )
);

CREATE TABLE context.roast_expression (
    roast_expression_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_expression_key TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    expression_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT roast_expression_pk PRIMARY KEY (roast_expression_id),
    CONSTRAINT roast_expression_key_uq UNIQUE (roast_expression_key),
    CONSTRAINT roast_expression_normalized_uq UNIQUE (language_tag_code, normalized_text),
    CONSTRAINT roast_expression_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_text_ck CHECK (
        roast_expression_key = lower(btrim(roast_expression_key)) AND roast_expression_key <> ''
        AND expression_text = btrim(expression_text) AND expression_text <> ''
        AND normalized_text = lower(btrim(normalized_text)) AND normalized_text <> ''
    )
);

CREATE TABLE context.roast_expression_mapping (
    roast_expression_mapping_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_expression_mapping_key TEXT NOT NULL,
    roast_expression_id BIGINT NOT NULL,
    roast_category_id BIGINT NOT NULL,
    context_mapping_certainty_code TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    context_assertion_role_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT roast_expression_mapping_pk PRIMARY KEY (roast_expression_mapping_id),
    CONSTRAINT roast_expression_mapping_key_uq UNIQUE (roast_expression_mapping_key),
    CONSTRAINT roast_expression_mapping_fact_uq UNIQUE (roast_expression_id, roast_category_id),
    CONSTRAINT roast_expression_mapping_expression_fk FOREIGN KEY (roast_expression_id)
        REFERENCES context.roast_expression (roast_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_mapping_category_fk FOREIGN KEY (roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_mapping_certainty_fk FOREIGN KEY (context_mapping_certainty_code)
        REFERENCES ref.context_mapping_certainty (context_mapping_certainty_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_mapping_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_mapping_role_fk FOREIGN KEY (context_assertion_role_code)
        REFERENCES ref.context_assertion_role (context_assertion_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_mapping_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_expression_mapping_text_ck CHECK (
        roast_expression_mapping_key = lower(btrim(roast_expression_mapping_key))
        AND roast_expression_mapping_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
    )
);

CREATE TABLE context.roast_measurement_method (
    roast_measurement_method_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_measurement_method_key TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    roast_measurement_basis_code TEXT NOT NULL,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    minimum_value NUMERIC NOT NULL,
    maximum_value NUMERIC NOT NULL,
    higher_value_is_lighter BOOLEAN NOT NULL,
    description TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT roast_measurement_method_pk PRIMARY KEY (roast_measurement_method_id),
    CONSTRAINT roast_measurement_method_key_uq UNIQUE (roast_measurement_method_key),
    CONSTRAINT roast_measurement_method_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_measurement_method_basis_fk FOREIGN KEY (roast_measurement_basis_code)
        REFERENCES ref.roast_measurement_basis (roast_measurement_basis_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_measurement_method_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_measurement_method_text_ck CHECK (
        roast_measurement_method_key = lower(btrim(roast_measurement_method_key))
        AND roast_measurement_method_key <> ''
        AND name = btrim(name) AND name <> ''
        AND unit = btrim(unit) AND unit <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT roast_measurement_method_bounds_ck CHECK (minimum_value < maximum_value)
);

CREATE TABLE context.beverage_addition_type (
    beverage_addition_type_id BIGINT GENERATED ALWAYS AS IDENTITY,
    beverage_addition_type_key TEXT NOT NULL,
    parent_beverage_addition_type_id BIGINT,
    preferred_label TEXT NOT NULL,
    description TEXT NOT NULL,
    is_strong_flavour_interference BOOLEAN NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT beverage_addition_type_pk PRIMARY KEY (beverage_addition_type_id),
    CONSTRAINT beverage_addition_type_key_uq UNIQUE (beverage_addition_type_key),
    CONSTRAINT beverage_addition_type_parent_fk FOREIGN KEY (parent_beverage_addition_type_id)
        REFERENCES context.beverage_addition_type (beverage_addition_type_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_addition_type_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_addition_type_text_ck CHECK (
        beverage_addition_type_key = lower(btrim(beverage_addition_type_key))
        AND beverage_addition_type_key <> ''
        AND preferred_label = btrim(preferred_label) AND preferred_label <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT beverage_addition_type_no_self_ck CHECK (
        parent_beverage_addition_type_id IS NULL
        OR parent_beverage_addition_type_id <> beverage_addition_type_id
    )
);

CREATE TABLE context.observation_context (
    observation_context_id BIGINT GENERATED ALWAYS AS IDENTITY,
    observation_context_key TEXT NOT NULL,
    captured_document_id BIGINT NOT NULL,
    preparation_status_code TEXT NOT NULL,
    reported_preparation_expression_id BIGINT,
    normalized_preparation_concept_id BIGINT,
    roast_status_code TEXT NOT NULL,
    reported_roast_expression_id BIGINT,
    normalized_roast_category_id BIGINT,
    addition_presence_code TEXT NOT NULL,
    context_assertion_role_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT observation_context_pk PRIMARY KEY (observation_context_id),
    CONSTRAINT observation_context_key_uq UNIQUE (observation_context_key),
    CONSTRAINT observation_context_document_uq UNIQUE (captured_document_id),
    CONSTRAINT observation_context_document_fk FOREIGN KEY (captured_document_id)
        REFERENCES corpus.captured_document (captured_document_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_preparation_status_fk FOREIGN KEY (preparation_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_preparation_expression_fk FOREIGN KEY (reported_preparation_expression_id)
        REFERENCES context.preparation_expression (preparation_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_preparation_concept_fk FOREIGN KEY (normalized_preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_roast_status_fk FOREIGN KEY (roast_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_roast_expression_fk FOREIGN KEY (reported_roast_expression_id)
        REFERENCES context.roast_expression (roast_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_roast_category_fk FOREIGN KEY (normalized_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_addition_presence_fk FOREIGN KEY (addition_presence_code)
        REFERENCES ref.addition_presence (addition_presence_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_role_fk FOREIGN KEY (context_assertion_role_code)
        REFERENCES ref.context_assertion_role (context_assertion_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_context_text_ck CHECK (
        observation_context_key = lower(btrim(observation_context_key))
        AND observation_context_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
        AND (notes IS NULL OR (notes = btrim(notes) AND notes <> ''))
    ),
    CONSTRAINT observation_context_preparation_value_ck CHECK (
        preparation_status_code = 'known'
            AND normalized_preparation_concept_id IS NOT NULL
        OR preparation_status_code = 'reported_unresolved'
            AND reported_preparation_expression_id IS NOT NULL
            AND normalized_preparation_concept_id IS NULL
        OR preparation_status_code IN ('unknown', 'not_reported', 'not_applicable')
            AND reported_preparation_expression_id IS NULL
            AND normalized_preparation_concept_id IS NULL
    ),
    CONSTRAINT observation_context_roast_value_ck CHECK (
        roast_status_code = 'known'
            AND normalized_roast_category_id IS NOT NULL
        OR roast_status_code = 'reported_unresolved'
            AND reported_roast_expression_id IS NOT NULL
            AND normalized_roast_category_id IS NULL
        OR roast_status_code IN ('unknown', 'not_reported', 'not_applicable')
            AND reported_roast_expression_id IS NULL
            AND normalized_roast_category_id IS NULL
    )
);

CREATE TABLE context.observation_addition (
    observation_addition_id BIGINT GENERATED ALWAYS AS IDENTITY,
    observation_addition_key TEXT NOT NULL,
    observation_context_id BIGINT NOT NULL,
    beverage_addition_type_id BIGINT NOT NULL,
    reported_label TEXT,
    notes TEXT,
    CONSTRAINT observation_addition_pk PRIMARY KEY (observation_addition_id),
    CONSTRAINT observation_addition_key_uq UNIQUE (observation_addition_key),
    CONSTRAINT observation_addition_fact_uq UNIQUE (observation_context_id, beverage_addition_type_id),
    CONSTRAINT observation_addition_context_fk FOREIGN KEY (observation_context_id)
        REFERENCES context.observation_context (observation_context_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_addition_type_fk FOREIGN KEY (beverage_addition_type_id)
        REFERENCES context.beverage_addition_type (beverage_addition_type_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_addition_text_ck CHECK (
        observation_addition_key = lower(btrim(observation_addition_key))
        AND observation_addition_key <> ''
        AND (reported_label IS NULL OR (reported_label = btrim(reported_label) AND reported_label <> ''))
        AND (notes IS NULL OR (notes = btrim(notes) AND notes <> ''))
    )
);

CREATE TABLE context.observation_roast_measurement (
    observation_roast_measurement_id BIGINT GENERATED ALWAYS AS IDENTITY,
    observation_roast_measurement_key TEXT NOT NULL,
    observation_context_id BIGINT NOT NULL,
    roast_measurement_method_id BIGINT NOT NULL,
    measured_value NUMERIC NOT NULL,
    source_version_id BIGINT NOT NULL,
    evidence_locator TEXT NOT NULL,
    CONSTRAINT observation_roast_measurement_pk PRIMARY KEY (observation_roast_measurement_id),
    CONSTRAINT observation_roast_measurement_key_uq UNIQUE (observation_roast_measurement_key),
    CONSTRAINT observation_roast_measurement_fact_uq UNIQUE (
        observation_context_id, roast_measurement_method_id
    ),
    CONSTRAINT observation_roast_measurement_context_fk FOREIGN KEY (observation_context_id)
        REFERENCES context.observation_context (observation_context_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_roast_measurement_method_fk FOREIGN KEY (roast_measurement_method_id)
        REFERENCES context.roast_measurement_method (roast_measurement_method_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_roast_measurement_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_roast_measurement_text_ck CHECK (
        observation_roast_measurement_key = lower(btrim(observation_roast_measurement_key))
        AND observation_roast_measurement_key <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
    )
);

CREATE INDEX preparation_relation_object_type_idx
    ON context.preparation_relation (object_preparation_concept_id, context_relation_type_code);
CREATE INDEX preparation_expression_mapping_concept_idx
    ON context.preparation_expression_mapping (preparation_concept_id, lifecycle_status_code);
CREATE INDEX roast_category_scheme_idx
    ON context.roast_category (roast_scheme_id, ordinal_position, roast_category_id);
CREATE INDEX roast_expression_mapping_category_idx
    ON context.roast_expression_mapping (roast_category_id, lifecycle_status_code);
CREATE INDEX observation_context_preparation_idx
    ON context.observation_context (normalized_preparation_concept_id, preparation_status_code);
CREATE INDEX observation_context_roast_idx
    ON context.observation_context (normalized_roast_category_id, roast_status_code);

COMMIT;
