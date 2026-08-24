\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- source-local concept schemes
-- A source's hierarchy or grouping is an evidence artifact, not a canonical
-- kb.concept_relation. Scheme nodes, edges, and mappings therefore remain in
-- evidence, retain their exact source version, and use independent lifecycle
-- and validity semantics.

BEGIN;

CREATE TABLE ref.scheme_concept_mapping_role (
    scheme_concept_mapping_role_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT scheme_concept_mapping_role_pk PRIMARY KEY (
        scheme_concept_mapping_role_code
    ),
    CONSTRAINT scheme_concept_mapping_role_code_nonempty_ck CHECK (
        scheme_concept_mapping_role_code = btrim(
            scheme_concept_mapping_role_code
        )
        AND scheme_concept_mapping_role_code <> ''
    ),
    CONSTRAINT scheme_concept_mapping_role_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT scheme_concept_mapping_role_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.scheme_concept_mapping_role IS
    'Controlled direction-aware correspondence from a source-local scheme node to a canonical concept; it is not a canonical graph predicate.';

INSERT INTO ref.scheme_concept_mapping_role (
    scheme_concept_mapping_role_code,
    display_name,
    description
)
VALUES
    (
        'equivalent_scope',
        'Equivalent scope',
        'The source-local node and canonical concept are reviewed as equivalent in scope for this version, without creating synonymy or a canonical relation.'
    ),
    (
        'source_broader_than_concept',
        'Source node broader than concept',
        'The source-local node has broader scope than the canonical concept for this reviewed mapping.'
    ),
    (
        'source_narrower_than_concept',
        'Source node narrower than concept',
        'The source-local node has narrower scope than the canonical concept for this reviewed mapping.'
    ),
    (
        'associated_with_concept',
        'Associated with concept',
        'The source-local node is associated with the canonical concept without asserting equivalent, broader, or narrower scope.'
    );

CREATE TABLE evidence.concept_scheme (
    concept_scheme_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_scheme_key TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT concept_scheme_pk PRIMARY KEY (concept_scheme_id),
    CONSTRAINT concept_scheme_key_uq UNIQUE (concept_scheme_key),
    CONSTRAINT concept_scheme_source_version_fk FOREIGN KEY (
        source_version_id
    ) REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_lifecycle_status_fk FOREIGN KEY (
        lifecycle_status_code
    ) REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_key_nonempty_ck CHECK (
        concept_scheme_key = btrim(concept_scheme_key)
        AND concept_scheme_key <> ''
    ),
    CONSTRAINT concept_scheme_name_nonempty_ck CHECK (
        name = btrim(name)
        AND name <> ''
    ),
    CONSTRAINT concept_scheme_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT concept_scheme_validity_ck CHECK (
        valid_until IS NULL OR valid_until > valid_from
    ),
    CONSTRAINT concept_scheme_metadata_object_ck CHECK (
        jsonb_typeof(metadata) = 'object'
    )
);

COMMENT ON TABLE evidence.concept_scheme IS
    'A lifecycle-managed source-local grouping or vocabulary scheme tied immutably to one citable source version.';
COMMENT ON COLUMN evidence.concept_scheme.source_version_id IS
    'Immutable provenance boundary; a revised source is represented by a new source_version and concept_scheme row.';

CREATE TABLE evidence.concept_scheme_node (
    concept_scheme_node_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_scheme_node_key TEXT NOT NULL,
    concept_scheme_id BIGINT NOT NULL,
    source_node_key TEXT NOT NULL,
    source_label TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    notes TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT concept_scheme_node_pk PRIMARY KEY (concept_scheme_node_id),
    CONSTRAINT concept_scheme_node_key_uq UNIQUE (concept_scheme_node_key),
    CONSTRAINT concept_scheme_node_scheme_source_key_uq UNIQUE (
        concept_scheme_id,
        source_node_key
    ),
    CONSTRAINT concept_scheme_node_scheme_identity_uq UNIQUE (
        concept_scheme_id,
        concept_scheme_node_id
    ),
    CONSTRAINT concept_scheme_node_scheme_fk FOREIGN KEY (
        concept_scheme_id
    ) REFERENCES evidence.concept_scheme (concept_scheme_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_node_lifecycle_status_fk FOREIGN KEY (
        lifecycle_status_code
    ) REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_node_key_nonempty_ck CHECK (
        concept_scheme_node_key = btrim(concept_scheme_node_key)
        AND concept_scheme_node_key <> ''
    ),
    CONSTRAINT concept_scheme_node_source_key_nonempty_ck CHECK (
        source_node_key = btrim(source_node_key)
        AND source_node_key <> ''
    ),
    CONSTRAINT concept_scheme_node_source_label_nonempty_ck CHECK (
        source_label = btrim(source_label)
        AND source_label <> ''
    ),
    CONSTRAINT concept_scheme_node_validity_ck CHECK (
        valid_until IS NULL OR valid_until > valid_from
    ),
    CONSTRAINT concept_scheme_node_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    ),
    CONSTRAINT concept_scheme_node_metadata_object_ck CHECK (
        jsonb_typeof(metadata) = 'object'
    )
);

COMMENT ON TABLE evidence.concept_scheme_node IS
    'A source-local scheme node. Its label and structure do not become canonical concept identity or lexicalization.';
COMMENT ON COLUMN evidence.concept_scheme_node.source_node_key IS
    'Stable node identifier within one source-version-specific concept scheme.';
COMMENT ON COLUMN evidence.concept_scheme_node.source_label IS
    'Source-local label governed by the scheme source version rights policy; storage visibility is not redistribution permission.';

CREATE TABLE evidence.concept_scheme_edge (
    concept_scheme_edge_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_scheme_edge_key TEXT NOT NULL,
    concept_scheme_id BIGINT NOT NULL,
    parent_node_id BIGINT NOT NULL,
    child_node_id BIGINT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    notes TEXT,
    CONSTRAINT concept_scheme_edge_pk PRIMARY KEY (concept_scheme_edge_id),
    CONSTRAINT concept_scheme_edge_key_uq UNIQUE (concept_scheme_edge_key),
    CONSTRAINT concept_scheme_edge_nodes_uq UNIQUE (
        concept_scheme_id,
        parent_node_id,
        child_node_id
    ),
    CONSTRAINT concept_scheme_edge_scheme_fk FOREIGN KEY (
        concept_scheme_id
    ) REFERENCES evidence.concept_scheme (concept_scheme_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_edge_parent_fk FOREIGN KEY (
        concept_scheme_id,
        parent_node_id
    ) REFERENCES evidence.concept_scheme_node (
        concept_scheme_id,
        concept_scheme_node_id
    )
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_edge_child_fk FOREIGN KEY (
        concept_scheme_id,
        child_node_id
    ) REFERENCES evidence.concept_scheme_node (
        concept_scheme_id,
        concept_scheme_node_id
    )
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_edge_lifecycle_status_fk FOREIGN KEY (
        lifecycle_status_code
    ) REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_edge_key_nonempty_ck CHECK (
        concept_scheme_edge_key = btrim(concept_scheme_edge_key)
        AND concept_scheme_edge_key <> ''
    ),
    CONSTRAINT concept_scheme_edge_distinct_nodes_ck CHECK (
        parent_node_id <> child_node_id
    ),
    CONSTRAINT concept_scheme_edge_validity_ck CHECK (
        valid_until IS NULL OR valid_until > valid_from
    ),
    CONSTRAINT concept_scheme_edge_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

COMMENT ON TABLE evidence.concept_scheme_edge IS
    'A directed parent-to-child edge inside exactly one source-local scheme; multiple active parents are permitted, while cycles are not.';

CREATE TABLE evidence.concept_scheme_mapping (
    concept_scheme_mapping_id BIGINT GENERATED ALWAYS AS IDENTITY,
    concept_scheme_mapping_key TEXT NOT NULL,
    concept_scheme_id BIGINT NOT NULL,
    concept_scheme_node_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    scheme_concept_mapping_role_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMPTZ,
    notes TEXT,
    CONSTRAINT concept_scheme_mapping_pk PRIMARY KEY (
        concept_scheme_mapping_id
    ),
    CONSTRAINT concept_scheme_mapping_key_uq UNIQUE (
        concept_scheme_mapping_key
    ),
    CONSTRAINT concept_scheme_mapping_node_concept_role_uq UNIQUE (
        concept_scheme_id,
        concept_scheme_node_id,
        concept_id,
        scheme_concept_mapping_role_code
    ),
    CONSTRAINT concept_scheme_mapping_scheme_fk FOREIGN KEY (
        concept_scheme_id
    ) REFERENCES evidence.concept_scheme (concept_scheme_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_mapping_node_fk FOREIGN KEY (
        concept_scheme_id,
        concept_scheme_node_id
    ) REFERENCES evidence.concept_scheme_node (
        concept_scheme_id,
        concept_scheme_node_id
    )
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_mapping_concept_fk FOREIGN KEY (
        concept_id
    ) REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_mapping_role_fk FOREIGN KEY (
        scheme_concept_mapping_role_code
    ) REFERENCES ref.scheme_concept_mapping_role (
        scheme_concept_mapping_role_code
    )
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_mapping_lifecycle_status_fk FOREIGN KEY (
        lifecycle_status_code
    ) REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,
    CONSTRAINT concept_scheme_mapping_key_nonempty_ck CHECK (
        concept_scheme_mapping_key = btrim(concept_scheme_mapping_key)
        AND concept_scheme_mapping_key <> ''
    ),
    CONSTRAINT concept_scheme_mapping_validity_ck CHECK (
        valid_until IS NULL OR valid_until > valid_from
    ),
    CONSTRAINT concept_scheme_mapping_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

COMMENT ON TABLE evidence.concept_scheme_mapping IS
    'Lifecycle-managed reviewed crosswalk from a source-local node to a canonical concept; it never creates a kb lexicalization or concept relation.';

CREATE FUNCTION evidence.enforce_concept_scheme_source_version()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_concept_scheme_source_version$
BEGIN
    IF NEW.source_version_id IS DISTINCT FROM OLD.source_version_id THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'concept_scheme_source_version_immutable_ck',
                MESSAGE = 'concept_scheme_source_version_immutable_ck: a concept scheme cannot be retargeted to another source version; create a new versioned scheme';
    END IF;

    RETURN NEW;
END;
$enforce_concept_scheme_source_version$;

COMMENT ON FUNCTION evidence.enforce_concept_scheme_source_version() IS
    'Preserves scheme provenance by requiring each revised source version to receive a new scheme identity.';

CREATE TRIGGER concept_scheme_source_version_bu
BEFORE UPDATE OF source_version_id
ON evidence.concept_scheme
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_concept_scheme_source_version();

COMMENT ON TRIGGER concept_scheme_source_version_bu ON evidence.concept_scheme IS
    'Rejects in-place source-version retargeting while allowing lifecycle and descriptive metadata updates.';

CREATE FUNCTION evidence.enforce_concept_scheme_edge_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_concept_scheme_edge_semantics$
DECLARE
    excluded_edge_id BIGINT;
    creates_cycle BOOLEAN;
BEGIN
    -- A per-scheme transaction lock prevents concurrent hierarchy writes from
    -- passing cycle checks against mutually stale graph states.
    PERFORM pg_catalog.pg_advisory_xact_lock(
        pg_catalog.hashtextextended(
            'evidence.concept_scheme.active_hierarchy:'
                || NEW.concept_scheme_id::TEXT,
            0
        )
    );

    IF NEW.lifecycle_status_code = 'active' THEN
        excluded_edge_id := CASE
            WHEN TG_OP = 'UPDATE' THEN OLD.concept_scheme_edge_id
            ELSE NULL
        END;

        WITH RECURSIVE reachable(node_id) AS (
            VALUES (NEW.child_node_id)
            UNION
            SELECT edge.child_node_id
            FROM reachable AS path
            JOIN evidence.concept_scheme_edge AS edge
              ON edge.parent_node_id = path.node_id
            WHERE edge.concept_scheme_id = NEW.concept_scheme_id
              AND edge.lifecycle_status_code = 'active'
              AND (
                  excluded_edge_id IS NULL
                  OR edge.concept_scheme_edge_id <> excluded_edge_id
              )
        )
        SELECT EXISTS (
            SELECT 1
            FROM reachable
            WHERE node_id = NEW.parent_node_id
        )
        INTO creates_cycle;

        IF creates_cycle THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'concept_scheme_hierarchy_cycle_ck',
                    MESSAGE = format(
                        'concept_scheme_hierarchy_cycle_ck: active scheme %s edge %s -> %s creates a cycle',
                        NEW.concept_scheme_id,
                        NEW.parent_node_id,
                        NEW.child_node_id
                    );
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_concept_scheme_edge_semantics$;

COMMENT ON FUNCTION evidence.enforce_concept_scheme_edge_semantics() IS
    'Serializes source-scheme hierarchy writes and rejects direct or indirect cycles while retaining legal polyhierarchy.';

CREATE TRIGGER concept_scheme_edge_semantics_biu
BEFORE INSERT OR UPDATE OF
    concept_scheme_id,
    parent_node_id,
    child_node_id,
    lifecycle_status_code,
    valid_from,
    valid_until
ON evidence.concept_scheme_edge
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_concept_scheme_edge_semantics();

COMMENT ON TRIGGER concept_scheme_edge_semantics_biu ON evidence.concept_scheme_edge IS
    'Applies lifecycle-active acyclic hierarchy semantics before storing a source-local scheme edge.';

CREATE INDEX concept_scheme_active_source_version_idx
    ON evidence.concept_scheme (source_version_id, concept_scheme_id)
    WHERE lifecycle_status_code = 'active';

COMMENT ON INDEX evidence.concept_scheme_active_source_version_idx IS
    'Supports source-version lookup of lifecycle-active schemes.';

CREATE INDEX concept_scheme_edge_active_child_idx
    ON evidence.concept_scheme_edge (
        concept_scheme_id,
        child_node_id,
        parent_node_id
    )
    WHERE lifecycle_status_code = 'active';

COMMENT ON INDEX evidence.concept_scheme_edge_active_child_idx IS
    'Supports reverse traversal of active source-scheme hierarchy edges; the unique edge index covers forward traversal.';

CREATE INDEX concept_scheme_mapping_active_concept_idx
    ON evidence.concept_scheme_mapping (
        concept_id,
        concept_scheme_id,
        concept_scheme_node_id
    )
    WHERE lifecycle_status_code = 'active';

COMMENT ON INDEX evidence.concept_scheme_mapping_active_concept_idx IS
    'Supports finding current source-scheme crosswalks from a canonical concept.';

CREATE VIEW evidence.v_current_scheme_hierarchy AS
SELECT
    scheme.concept_scheme_id,
    scheme.concept_scheme_key,
    scheme.name AS concept_scheme_name,
    source_version.source_version_id,
    source_version.source_version_key,
    source.source_id,
    source.source_key,
    license_policy.license_policy_id,
    license_policy.license_policy_key,
    license_policy.access_class_code,
    license_policy.rights_status_code,
    license_policy.production_export_allowed,
    edge.concept_scheme_edge_id,
    edge.concept_scheme_edge_key,
    edge.valid_from AS edge_valid_from,
    edge.valid_until AS edge_valid_until,
    parent.concept_scheme_node_id AS parent_node_id,
    parent.concept_scheme_node_key AS parent_node_key,
    parent.source_node_key AS parent_source_node_key,
    parent.source_label AS parent_source_label,
    child.concept_scheme_node_id AS child_node_id,
    child.concept_scheme_node_key AS child_node_key,
    child.source_node_key AS child_source_node_key,
    child.source_label AS child_source_label
FROM evidence.concept_scheme_edge AS edge
JOIN evidence.concept_scheme AS scheme
  ON scheme.concept_scheme_id = edge.concept_scheme_id
JOIN evidence.concept_scheme_node AS parent
  ON parent.concept_scheme_id = edge.concept_scheme_id
 AND parent.concept_scheme_node_id = edge.parent_node_id
JOIN evidence.concept_scheme_node AS child
  ON child.concept_scheme_id = edge.concept_scheme_id
 AND child.concept_scheme_node_id = edge.child_node_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = scheme.source_version_id
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS license_policy
  ON license_policy.license_policy_id = source_version.license_policy_id
WHERE scheme.lifecycle_status_code = 'active'
  AND scheme.valid_from <= CURRENT_TIMESTAMP
  AND (scheme.valid_until IS NULL OR scheme.valid_until > CURRENT_TIMESTAMP)
  AND parent.lifecycle_status_code = 'active'
  AND parent.valid_from <= CURRENT_TIMESTAMP
  AND (parent.valid_until IS NULL OR parent.valid_until > CURRENT_TIMESTAMP)
  AND child.lifecycle_status_code = 'active'
  AND child.valid_from <= CURRENT_TIMESTAMP
  AND (child.valid_until IS NULL OR child.valid_until > CURRENT_TIMESTAMP)
  AND edge.lifecycle_status_code = 'active'
  AND edge.valid_from <= CURRENT_TIMESTAMP
  AND (edge.valid_until IS NULL OR edge.valid_until > CURRENT_TIMESTAMP);

COMMENT ON VIEW evidence.v_current_scheme_hierarchy IS
    'Current source-local parent-child edges with source/version/licence identifiers and explicit production-export permission; rows never become canonical kb relations.';

CREATE VIEW evidence.v_current_scheme_concept_mapping AS
SELECT
    scheme.concept_scheme_id,
    scheme.concept_scheme_key,
    scheme.name AS concept_scheme_name,
    source_version.source_version_id,
    source_version.source_version_key,
    source.source_id,
    source.source_key,
    license_policy.license_policy_id,
    license_policy.license_policy_key,
    license_policy.access_class_code,
    license_policy.rights_status_code,
    license_policy.production_export_allowed,
    node.concept_scheme_node_id,
    node.concept_scheme_node_key,
    node.source_node_key,
    node.source_label,
    mapping.concept_scheme_mapping_id,
    mapping.concept_scheme_mapping_key,
    mapping.scheme_concept_mapping_role_code,
    mapping.valid_from AS mapping_valid_from,
    mapping.valid_until AS mapping_valid_until,
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code
FROM evidence.concept_scheme_mapping AS mapping
JOIN evidence.concept_scheme AS scheme
  ON scheme.concept_scheme_id = mapping.concept_scheme_id
JOIN evidence.concept_scheme_node AS node
  ON node.concept_scheme_id = mapping.concept_scheme_id
 AND node.concept_scheme_node_id = mapping.concept_scheme_node_id
JOIN kb.concept AS concept
  ON concept.concept_id = mapping.concept_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = scheme.source_version_id
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS license_policy
  ON license_policy.license_policy_id = source_version.license_policy_id
WHERE scheme.lifecycle_status_code = 'active'
  AND scheme.valid_from <= CURRENT_TIMESTAMP
  AND (scheme.valid_until IS NULL OR scheme.valid_until > CURRENT_TIMESTAMP)
  AND node.lifecycle_status_code = 'active'
  AND node.valid_from <= CURRENT_TIMESTAMP
  AND (node.valid_until IS NULL OR node.valid_until > CURRENT_TIMESTAMP)
  AND mapping.lifecycle_status_code = 'active'
  AND mapping.valid_from <= CURRENT_TIMESTAMP
  AND (mapping.valid_until IS NULL OR mapping.valid_until > CURRENT_TIMESTAMP)
  AND concept.lifecycle_status_code = 'active';

COMMENT ON VIEW evidence.v_current_scheme_concept_mapping IS
    'Current reviewed source-node crosswalks to active canonical concepts with source/version/licence identifiers and explicit production-export permission.';

COMMIT;
