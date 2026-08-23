\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Canonical ontology and lexical structures are normalized relational data.
-- These tables meet at least 3NF (and BCNF for their declared candidate keys):
-- identities and stable keys determine row facts, while controlled semantics
-- live behind foreign keys. JSONB, intrinsic concept intensity, universal
-- weights/similarity, and empirical measurements are deliberately absent.

BEGIN;

CREATE FUNCTION kb.normalize_expression(input_text TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $normalize_expression$
    SELECT btrim(
        regexp_replace(lower(input_text), '[[:space:]]+', ' ', 'g')
    );
$normalize_expression$;

COMMENT ON FUNCTION kb.normalize_expression(TEXT) IS
    'Deterministic V0 lexical lookup normalization: lowercase, collapse whitespace, and trim. It does not assert a concept mapping.';

CREATE TABLE kb.concept (
    concept_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_key TEXT NOT NULL,
    concept_type_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    provenance_scope_code TEXT NOT NULL,
    replacement_concept_id BIGINT,
    description TEXT NOT NULL,
    editorial_note TEXT,
    CONSTRAINT concept_pk PRIMARY KEY (concept_id),
    CONSTRAINT concept_key_uq UNIQUE (concept_key),
    CONSTRAINT concept_type_fk FOREIGN KEY (concept_type_code)
        REFERENCES ref.concept_type (concept_type_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_lifecycle_status_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_provenance_scope_fk FOREIGN KEY (provenance_scope_code)
        REFERENCES ref.provenance_scope (provenance_scope_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_replacement_fk FOREIGN KEY (replacement_concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_key_nonempty_ck CHECK (
        concept_key = btrim(concept_key)
        AND concept_key <> ''
    ),
    CONSTRAINT concept_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT concept_editorial_note_nonempty_ck CHECK (
        editorial_note IS NULL
        OR (editorial_note = btrim(editorial_note) AND editorial_note <> '')
    ),
    CONSTRAINT concept_replacement_not_self_ck CHECK (
        replacement_concept_id IS NULL
        OR replacement_concept_id <> concept_id
    )
);

COMMENT ON TABLE kb.concept IS
    'Language-neutral canonical concept identities. Labels, spellings, intrinsic intensities, and empirical coordinates do not belong here.';
COMMENT ON COLUMN kb.concept.concept_key IS
    'Stable machine-readable candidate key that survives wording and lifecycle changes.';
COMMENT ON COLUMN kb.concept.replacement_concept_id IS
    'Optional historical resolution for a retired concept; a self-reference is prohibited.';
COMMENT ON COLUMN kb.concept.description IS
    'Project-authored semantic scope description, not a display label or copied source definition.';

CREATE TABLE kb.lexical_expression (
    expression_id BIGINT GENERATED ALWAYS AS IDENTITY,
    expression_key TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    expression_text TEXT NOT NULL,
    normalized_text TEXT GENERATED ALWAYS AS (
        kb.normalize_expression(expression_text)
    ) STORED,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT lexical_expression_pk PRIMARY KEY (expression_id),
    CONSTRAINT lexical_expression_key_uq UNIQUE (expression_key),
    CONSTRAINT lexical_expression_language_normalized_uq UNIQUE (
        language_tag_code,
        normalized_text
    ),
    CONSTRAINT lexical_expression_language_tag_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexical_expression_lifecycle_status_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexical_expression_key_nonempty_ck CHECK (
        expression_key = btrim(expression_key)
        AND expression_key <> ''
    ),
    CONSTRAINT lexical_expression_text_nonempty_ck CHECK (
        expression_text = btrim(expression_text)
        AND expression_text <> ''
    ),
    CONSTRAINT lexical_expression_normalized_nonempty_ck CHECK (
        normalized_text <> ''
    )
);

COMMENT ON TABLE kb.lexical_expression IS
    'Language-tagged surface forms independent from concepts; an expression may remain unresolved or participate in polysemy.';
COMMENT ON COLUMN kb.lexical_expression.normalized_text IS
    'Stored output of kb.normalize_expression, unique within a language for exact and trigram retrieval.';

CREATE TABLE kb.lexicalization (
    lexicalization_id BIGINT GENERATED ALWAYS AS IDENTITY,
    lexicalization_key TEXT NOT NULL,
    expression_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    mapping_type_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    provenance_scope_code TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    CONSTRAINT lexicalization_pk PRIMARY KEY (lexicalization_id),
    CONSTRAINT lexicalization_key_uq UNIQUE (lexicalization_key),
    CONSTRAINT lexicalization_expression_concept_mapping_uq UNIQUE (
        expression_id,
        concept_id,
        mapping_type_code
    ),
    CONSTRAINT lexicalization_expression_fk FOREIGN KEY (expression_id)
        REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_mapping_type_fk FOREIGN KEY (mapping_type_code)
        REFERENCES ref.mapping_type (mapping_type_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_lifecycle_status_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_provenance_scope_fk FOREIGN KEY (provenance_scope_code)
        REFERENCES ref.provenance_scope (provenance_scope_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT lexicalization_key_nonempty_ck CHECK (
        lexicalization_key = btrim(lexicalization_key)
        AND lexicalization_key <> ''
    ),
    CONSTRAINT lexicalization_validity_ck CHECK (
        valid_until IS NULL OR valid_until > valid_from
    )
);

COMMENT ON TABLE kb.lexicalization IS
    'Canonical assertion that an expression lexicalizes a concept under controlled mapping, lifecycle, provenance, and validity semantics.';
COMMENT ON COLUMN kb.lexicalization.valid_until IS
    'Exclusive end of assertion validity; NULL denotes an open-ended interval.';

CREATE TABLE kb.concept_relation (
    concept_relation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    relation_key TEXT NOT NULL,
    relation_type_code TEXT NOT NULL,
    subject_concept_id BIGINT NOT NULL,
    object_concept_id BIGINT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    provenance_scope_code TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    CONSTRAINT concept_relation_pk PRIMARY KEY (concept_relation_id),
    CONSTRAINT concept_relation_key_uq UNIQUE (relation_key),
    CONSTRAINT concept_relation_type_endpoints_uq UNIQUE (
        relation_type_code,
        subject_concept_id,
        object_concept_id
    ),
    CONSTRAINT concept_relation_type_fk FOREIGN KEY (relation_type_code)
        REFERENCES ref.relation_type (relation_type_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_relation_subject_fk FOREIGN KEY (subject_concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_relation_object_fk FOREIGN KEY (object_concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_relation_lifecycle_status_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_relation_provenance_scope_fk FOREIGN KEY (provenance_scope_code)
        REFERENCES ref.provenance_scope (provenance_scope_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_relation_key_nonempty_ck CHECK (
        relation_key = btrim(relation_key)
        AND relation_key <> ''
    ),
    CONSTRAINT concept_relation_validity_ck CHECK (
        valid_until IS NULL OR valid_until > valid_from
    )
);

COMMENT ON TABLE kb.concept_relation IS
    'Typed canonical graph assertion. It stores neither a universal weight nor a generic similarity value.';
COMMENT ON COLUMN kb.concept_relation.subject_concept_id IS
    'Predicate subject. For BROADER_THAN, the subject concept is broader than the object concept.';
COMMENT ON COLUMN kb.concept_relation.object_concept_id IS
    'Predicate object. Symmetric types use canonical endpoint ordering enforced by a later semantic trigger.';

CREATE TABLE kb.sensory_dimension (
    sensory_dimension_id BIGINT GENERATED ALWAYS AS IDENTITY,
    dimension_key TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    name TEXT NOT NULL,
    measurement_semantics TEXT NOT NULL,
    unit TEXT,
    CONSTRAINT sensory_dimension_pk PRIMARY KEY (sensory_dimension_id),
    CONSTRAINT sensory_dimension_key_uq UNIQUE (dimension_key),
    CONSTRAINT sensory_dimension_lifecycle_status_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sensory_dimension_key_nonempty_ck CHECK (
        dimension_key = btrim(dimension_key)
        AND dimension_key <> ''
    ),
    CONSTRAINT sensory_dimension_name_nonempty_ck CHECK (
        name = btrim(name)
        AND name <> ''
    ),
    CONSTRAINT sensory_dimension_measurement_semantics_nonempty_ck CHECK (
        measurement_semantics = btrim(measurement_semantics)
        AND measurement_semantics <> ''
    ),
    CONSTRAINT sensory_dimension_unit_nonempty_ck CHECK (
        unit IS NULL OR (unit = btrim(unit) AND unit <> '')
    )
);

COMMENT ON TABLE kb.sensory_dimension IS
    'Registry of interpretable sample-level measurement constructs; it does not assign a numeric value to any concept.';
COMMENT ON COLUMN kb.sensory_dimension.measurement_semantics IS
    'Definition of what a future sample-level measurement means, independent from any observed value or scale instance.';

CREATE TABLE kb.concept_dimension_link (
    concept_dimension_link_id BIGINT GENERATED ALWAYS AS IDENTITY,
    link_key TEXT NOT NULL,
    concept_id BIGINT NOT NULL,
    sensory_dimension_id BIGINT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    provenance_scope_code TEXT NOT NULL,
    link_semantics TEXT NOT NULL,
    CONSTRAINT concept_dimension_link_pk PRIMARY KEY (concept_dimension_link_id),
    CONSTRAINT concept_dimension_link_key_uq UNIQUE (link_key),
    CONSTRAINT concept_dimension_link_concept_dimension_uq UNIQUE (
        concept_id,
        sensory_dimension_id
    ),
    CONSTRAINT concept_dimension_link_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_dimension_fk FOREIGN KEY (sensory_dimension_id)
        REFERENCES kb.sensory_dimension (sensory_dimension_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_lifecycle_status_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_provenance_scope_fk FOREIGN KEY (provenance_scope_code)
        REFERENCES ref.provenance_scope (provenance_scope_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT concept_dimension_link_key_nonempty_ck CHECK (
        link_key = btrim(link_key)
        AND link_key <> ''
    ),
    CONSTRAINT concept_dimension_link_semantics_nonempty_ck CHECK (
        link_semantics = btrim(link_semantics)
        AND link_semantics <> ''
    )
);

COMMENT ON TABLE kb.concept_dimension_link IS
    'Non-numeric statement that a concept is meaningfully associated with a sample-level measurement construct.';
COMMENT ON COLUMN kb.concept_dimension_link.link_semantics IS
    'Explains the kind of association without storing a concept score, intensity, coefficient, or weight.';

COMMIT;
