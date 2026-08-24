\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Cross-row and controlled-vocabulary semantics that cannot be expressed by
-- ordinary foreign keys or row-local CHECK constraints live here. Constraint
-- triggers re-read final transaction state so assertion and support rows may be
-- inserted in either order within one transaction.

BEGIN;

ALTER TABLE kb.concept
    ADD CONSTRAINT concept_key_format_ck CHECK (
        concept_key ~ '^[a-z][a-z0-9_]*[.][a-z][a-z0-9_]*([.][a-z][a-z0-9_]*)*$'
    );

COMMENT ON CONSTRAINT concept_key_format_ck ON kb.concept IS
    'Stable language-neutral keys use lowercase dot-separated machine-readable segments.';

CREATE FUNCTION kb.enforce_concept_lifecycle_replacement()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_concept_lifecycle_replacement$
DECLARE
    replacement_status TEXT;
BEGIN
    IF NEW.replacement_concept_id IS NOT NULL
       AND NEW.lifecycle_status_code NOT IN ('deprecated', 'merged') THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'concept_lifecycle_replacement_ck',
                MESSAGE = 'concept_lifecycle_replacement_ck: only deprecated or merged concepts may name a replacement';
    END IF;

    IF NEW.lifecycle_status_code = 'merged'
       AND NEW.replacement_concept_id IS NULL THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'concept_lifecycle_replacement_ck',
                MESSAGE = 'concept_lifecycle_replacement_ck: a merged concept must name a replacement';
    END IF;

    IF NEW.replacement_concept_id IS NOT NULL THEN
        SELECT c.lifecycle_status_code
        INTO replacement_status
        FROM kb.concept AS c
        WHERE c.concept_id = NEW.replacement_concept_id;

        -- A missing target is left to the ordinary foreign key, which provides
        -- the correct referential-integrity diagnostic.
        IF FOUND AND replacement_status <> 'active' THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'concept_lifecycle_replacement_ck',
                    MESSAGE = 'concept_lifecycle_replacement_ck: a replacement concept must be active';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_concept_lifecycle_replacement$;

COMMENT ON FUNCTION kb.enforce_concept_lifecycle_replacement() IS
    'Validates lifecycle-dependent replacement semantics without deleting or rewriting historical concept identities.';

CREATE TRIGGER concept_lifecycle_replacement_biu
BEFORE INSERT OR UPDATE OF lifecycle_status_code, replacement_concept_id
ON kb.concept
FOR EACH ROW
EXECUTE FUNCTION kb.enforce_concept_lifecycle_replacement();

COMMENT ON TRIGGER concept_lifecycle_replacement_biu ON kb.concept IS
    'Requires merged concepts to name an active replacement and prevents replacements on non-retired lifecycle states.';

CREATE FUNCTION kb.enforce_concept_relation_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_concept_relation_semantics$
DECLARE
    relation_semantics ref.relation_type%ROWTYPE;
    swap_concept_id BIGINT;
    excluded_relation_id BIGINT;
    creates_cycle BOOLEAN;
BEGIN
    SELECT rt.*
    INTO relation_semantics
    FROM ref.relation_type AS rt
    WHERE rt.relation_type_code = NEW.relation_type_code;

    -- A missing relation type is left to the ordinary foreign key.
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    IF NEW.subject_concept_id = NEW.object_concept_id
       AND NOT relation_semantics.allows_self THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'concept_relation_self_allowed_ck',
                MESSAGE = format(
                    'concept_relation_self_allowed_ck: relation type %s does not allow self-relations',
                    NEW.relation_type_code
                );
    END IF;

    IF relation_semantics.is_symmetric
       AND NEW.subject_concept_id > NEW.object_concept_id THEN
        swap_concept_id := NEW.subject_concept_id;
        NEW.subject_concept_id := NEW.object_concept_id;
        NEW.object_concept_id := swap_concept_id;
    END IF;

    IF relation_semantics.is_hierarchical THEN
        -- One database-wide transaction lock serializes active hierarchy
        -- mutations, including changes between hierarchy types. This avoids
        -- the two-transaction write skew that row locks cannot prevent.
        PERFORM pg_catalog.pg_advisory_xact_lock(
            pg_catalog.hashtextextended('kb.concept_relation.active_hierarchy', 0)
        );

        IF NEW.lifecycle_status_code = 'active' THEN
            excluded_relation_id := CASE
                WHEN TG_OP = 'UPDATE' THEN OLD.concept_relation_id
                ELSE NULL
            END;

            WITH RECURSIVE reachable(concept_id) AS (
                VALUES (NEW.object_concept_id)
                UNION
                SELECT cr.object_concept_id
                FROM reachable AS path
                JOIN kb.concept_relation AS cr
                  ON cr.subject_concept_id = path.concept_id
                WHERE cr.relation_type_code = NEW.relation_type_code
                  AND cr.lifecycle_status_code = 'active'
                  AND (
                      excluded_relation_id IS NULL
                      OR cr.concept_relation_id <> excluded_relation_id
                  )
            )
            SELECT EXISTS (
                SELECT 1
                FROM reachable
                WHERE concept_id = NEW.subject_concept_id
            )
            INTO creates_cycle;

            IF creates_cycle THEN
                RAISE EXCEPTION
                    USING
                        ERRCODE = '23514',
                        CONSTRAINT = 'concept_relation_hierarchy_cycle_ck',
                        MESSAGE = format(
                            'concept_relation_hierarchy_cycle_ck: active %s edge %s -> %s creates a cycle',
                            NEW.relation_type_code,
                            NEW.subject_concept_id,
                            NEW.object_concept_id
                        );
            END IF;
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_concept_relation_semantics$;

COMMENT ON FUNCTION kb.enforce_concept_relation_semantics() IS
    'Reads relation-type semantics, rejects prohibited self-edges, orders symmetric endpoints, serializes hierarchy writes, and rejects active direct or indirect cycles.';

CREATE TRIGGER concept_relation_semantics_biu
BEFORE INSERT OR UPDATE OF
    relation_type_code,
    subject_concept_id,
    object_concept_id,
    lifecycle_status_code,
    valid_from,
    valid_until
ON kb.concept_relation
FOR EACH ROW
EXECUTE FUNCTION kb.enforce_concept_relation_semantics();

COMMENT ON TRIGGER concept_relation_semantics_biu ON kb.concept_relation IS
    'Applies controlled relation semantics before a graph edge is stored.';

CREATE FUNCTION ref.guard_relation_type_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_relation_type_semantics$
DECLARE
    used_relation_type_code TEXT;
    semantic_change BOOLEAN := FALSE;
BEGIN
    IF TG_OP = 'DELETE' THEN
        used_relation_type_code := OLD.relation_type_code;
        semantic_change := TRUE;
    ELSE
        used_relation_type_code := OLD.relation_type_code;
        semantic_change := ROW(
            OLD.relation_type_code,
            OLD.is_directional,
            OLD.is_symmetric,
            OLD.is_hierarchical,
            OLD.closure_is_transitive,
            OLD.allows_self,
            OLD.evidence_required
        ) IS DISTINCT FROM ROW(
            NEW.relation_type_code,
            NEW.is_directional,
            NEW.is_symmetric,
            NEW.is_hierarchical,
            NEW.closure_is_transitive,
            NEW.allows_self,
            NEW.evidence_required
        );
    END IF;

    IF semantic_change
       AND EXISTS (
           SELECT 1
           FROM kb.concept_relation AS cr
           WHERE cr.relation_type_code = used_relation_type_code
       ) THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'relation_type_used_semantics_immutable_ck',
                MESSAGE = format(
                    'relation_type_used_semantics_immutable_ck: semantic fields for used relation type %s cannot be changed or deleted',
                    used_relation_type_code
                );
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_relation_type_semantics$;

COMMENT ON FUNCTION ref.guard_relation_type_semantics() IS
    'Prevents changes to graph-defining semantics once a relation type has been used by a canonical edge.';

CREATE TRIGGER relation_type_used_semantics_bud
BEFORE UPDATE OR DELETE
ON ref.relation_type
FOR EACH ROW
EXECUTE FUNCTION ref.guard_relation_type_semantics();

COMMENT ON TRIGGER relation_type_used_semantics_bud ON ref.relation_type IS
    'Keeps stored graph edges interpretable by freezing used relation-type semantics.';

CREATE FUNCTION evidence.enforce_license_policy_export_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_license_policy_export_semantics$
DECLARE
    rights_are_verified BOOLEAN;
    access_permits_raw_text BOOLEAN;
BEGIN
    IF NOT NEW.production_export_allowed THEN
        RETURN NEW;
    END IF;

    SELECT rs.is_verified
    INTO rights_are_verified
    FROM ref.rights_status AS rs
    WHERE rs.rights_status_code = NEW.rights_status_code;

    IF FOUND AND NOT rights_are_verified THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'license_policy_export_verified_rights_ck',
                MESSAGE = 'license_policy_export_verified_rights_ck: production export requires a verified rights status';
    END IF;

    SELECT ac.permits_raw_text
    INTO access_permits_raw_text
    FROM ref.access_class AS ac
    WHERE ac.access_class_code = NEW.access_class_code;

    IF FOUND AND NOT access_permits_raw_text THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'license_policy_export_raw_text_access_ck',
                MESSAGE = 'license_policy_export_raw_text_access_ck: production export requires an access class that permits raw text';
    END IF;

    RETURN NEW;
END;
$enforce_license_policy_export_semantics$;

COMMENT ON FUNCTION evidence.enforce_license_policy_export_semantics() IS
    'Prevents the production-export gate from being enabled without verified rights and raw-text access permission.';

CREATE TRIGGER license_policy_export_semantics_biu
BEFORE INSERT OR UPDATE OF
    access_class_code,
    rights_status_code,
    production_export_allowed
ON evidence.license_policy
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_license_policy_export_semantics();

COMMENT ON TRIGGER license_policy_export_semantics_biu ON evidence.license_policy IS
    'Checks controlled rights and access semantics before a licence policy can permit production export.';

CREATE FUNCTION evidence.enforce_concept_source_support()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_concept_source_support$
DECLARE
    concept_ids BIGINT[];
    checked_concept_id BIGINT;
BEGIN
    IF TG_TABLE_SCHEMA = 'kb' THEN
        concept_ids := ARRAY[NEW.concept_id];
    ELSIF TG_OP = 'INSERT' THEN
        concept_ids := ARRAY[NEW.concept_id];
    ELSIF TG_OP = 'DELETE' THEN
        concept_ids := ARRAY[OLD.concept_id];
    ELSE
        concept_ids := ARRAY[OLD.concept_id, NEW.concept_id];
    END IF;

    FOREACH checked_concept_id IN ARRAY concept_ids LOOP
        IF EXISTS (
            SELECT 1
            FROM kb.concept AS c
            JOIN ref.provenance_scope AS ps
              ON ps.provenance_scope_code = c.provenance_scope_code
            WHERE c.concept_id = checked_concept_id
              AND c.lifecycle_status_code = 'active'
              AND ps.requires_source_support
              AND NOT EXISTS (
                  SELECT 1
                  FROM evidence.concept_support AS support
                  WHERE support.concept_id = c.concept_id
              )
        ) THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'concept_active_source_support_ck',
                    MESSAGE = format(
                        'concept_active_source_support_ck: active concept %s requires source-version or dataset support',
                        checked_concept_id
                    );
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_concept_source_support$;

COMMENT ON FUNCTION evidence.enforce_concept_source_support() IS
    'Deferred final-state validator for active concepts whose provenance scope requires source support.';

CREATE CONSTRAINT TRIGGER concept_source_support_assertion_ct
AFTER INSERT OR UPDATE
ON kb.concept
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_concept_source_support();

COMMENT ON TRIGGER concept_source_support_assertion_ct ON kb.concept IS
    'Rechecks required concept support at transaction completion after concept insertion or mutation.';

CREATE CONSTRAINT TRIGGER concept_source_support_reciprocal_ct
AFTER INSERT OR UPDATE OR DELETE
ON evidence.concept_support
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_concept_source_support();

COMMENT ON TRIGGER concept_source_support_reciprocal_ct ON evidence.concept_support IS
    'Rechecks both sides of concept-support insertion, deletion, and retargeting against final state.';

CREATE FUNCTION evidence.enforce_lexicalization_source_support()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_lexicalization_source_support$
DECLARE
    lexicalization_ids BIGINT[];
    checked_lexicalization_id BIGINT;
BEGIN
    IF TG_TABLE_SCHEMA = 'kb' THEN
        lexicalization_ids := ARRAY[NEW.lexicalization_id];
    ELSIF TG_OP = 'INSERT' THEN
        lexicalization_ids := ARRAY[NEW.lexicalization_id];
    ELSIF TG_OP = 'DELETE' THEN
        lexicalization_ids := ARRAY[OLD.lexicalization_id];
    ELSE
        lexicalization_ids := ARRAY[
            OLD.lexicalization_id,
            NEW.lexicalization_id
        ];
    END IF;

    FOREACH checked_lexicalization_id IN ARRAY lexicalization_ids LOOP
        IF EXISTS (
            SELECT 1
            FROM kb.lexicalization AS l
            JOIN ref.provenance_scope AS ps
              ON ps.provenance_scope_code = l.provenance_scope_code
            WHERE l.lexicalization_id = checked_lexicalization_id
              AND l.lifecycle_status_code = 'active'
              AND ps.requires_source_support
              AND NOT EXISTS (
                  SELECT 1
                  FROM evidence.lexicalization_support AS support
                  WHERE support.lexicalization_id = l.lexicalization_id
              )
        ) THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'lexicalization_active_source_support_ck',
                    MESSAGE = format(
                        'lexicalization_active_source_support_ck: active lexicalization %s requires source-version or dataset support',
                        checked_lexicalization_id
                    );
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_lexicalization_source_support$;

COMMENT ON FUNCTION evidence.enforce_lexicalization_source_support() IS
    'Deferred final-state validator for active lexicalizations whose provenance scope requires support.';

CREATE CONSTRAINT TRIGGER lexicalization_support_assertion_ct
AFTER INSERT OR UPDATE
ON kb.lexicalization
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_lexicalization_source_support();

COMMENT ON TRIGGER lexicalization_support_assertion_ct ON kb.lexicalization IS
    'Rechecks required lexicalization support at transaction completion after assertion insertion or mutation.';

CREATE CONSTRAINT TRIGGER lexicalization_support_reciprocal_ct
AFTER INSERT OR UPDATE OR DELETE
ON evidence.lexicalization_support
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_lexicalization_source_support();

COMMENT ON TRIGGER lexicalization_support_reciprocal_ct ON evidence.lexicalization_support IS
    'Rechecks both sides of lexicalization-support insertion, deletion, and retargeting against final state.';

CREATE FUNCTION evidence.enforce_relation_source_support()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_relation_source_support$
DECLARE
    relation_ids BIGINT[];
    checked_relation_id BIGINT;
BEGIN
    IF TG_TABLE_SCHEMA = 'kb' THEN
        relation_ids := ARRAY[NEW.concept_relation_id];
    ELSIF TG_OP = 'INSERT' THEN
        relation_ids := ARRAY[NEW.concept_relation_id];
    ELSIF TG_OP = 'DELETE' THEN
        relation_ids := ARRAY[OLD.concept_relation_id];
    ELSE
        relation_ids := ARRAY[
            OLD.concept_relation_id,
            NEW.concept_relation_id
        ];
    END IF;

    FOREACH checked_relation_id IN ARRAY relation_ids LOOP
        IF EXISTS (
            SELECT 1
            FROM kb.concept_relation AS cr
            JOIN ref.provenance_scope AS ps
              ON ps.provenance_scope_code = cr.provenance_scope_code
            JOIN ref.relation_type AS rt
              ON rt.relation_type_code = cr.relation_type_code
            WHERE cr.concept_relation_id = checked_relation_id
              AND cr.lifecycle_status_code = 'active'
              AND (ps.requires_source_support OR rt.evidence_required)
              AND NOT EXISTS (
                  SELECT 1
                  FROM evidence.relation_support AS support
                  WHERE support.concept_relation_id = cr.concept_relation_id
              )
        ) THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'concept_relation_active_source_support_ck',
                    MESSAGE = format(
                        'concept_relation_active_source_support_ck: active relation %s requires source-version or dataset support',
                        checked_relation_id
                    );
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_relation_source_support$;

COMMENT ON FUNCTION evidence.enforce_relation_source_support() IS
    'Deferred final-state validator for active relations required by provenance scope or relation-type semantics to have support.';

CREATE CONSTRAINT TRIGGER relation_source_support_assertion_ct
AFTER INSERT OR UPDATE
ON kb.concept_relation
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_relation_source_support();

COMMENT ON TRIGGER relation_source_support_assertion_ct ON kb.concept_relation IS
    'Rechecks required relation support at transaction completion after assertion insertion or mutation.';

CREATE CONSTRAINT TRIGGER relation_source_support_reciprocal_ct
AFTER INSERT OR UPDATE OR DELETE
ON evidence.relation_support
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_relation_source_support();

COMMENT ON TRIGGER relation_source_support_reciprocal_ct ON evidence.relation_support IS
    'Rechecks both sides of relation-support insertion, deletion, and retargeting against final state.';

CREATE FUNCTION evidence.enforce_dimension_link_source_support()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_dimension_link_source_support$
DECLARE
    link_ids BIGINT[];
    checked_link_id BIGINT;
BEGIN
    IF TG_TABLE_SCHEMA = 'kb' THEN
        link_ids := ARRAY[NEW.concept_dimension_link_id];
    ELSIF TG_OP = 'INSERT' THEN
        link_ids := ARRAY[NEW.concept_dimension_link_id];
    ELSIF TG_OP = 'DELETE' THEN
        link_ids := ARRAY[OLD.concept_dimension_link_id];
    ELSE
        link_ids := ARRAY[
            OLD.concept_dimension_link_id,
            NEW.concept_dimension_link_id
        ];
    END IF;

    FOREACH checked_link_id IN ARRAY link_ids LOOP
        IF EXISTS (
            SELECT 1
            FROM kb.concept_dimension_link AS link
            JOIN ref.provenance_scope AS ps
              ON ps.provenance_scope_code = link.provenance_scope_code
            WHERE link.concept_dimension_link_id = checked_link_id
              AND link.lifecycle_status_code = 'active'
              AND ps.requires_source_support
              AND NOT EXISTS (
                  SELECT 1
                  FROM evidence.concept_dimension_link_support AS support
                  WHERE support.concept_dimension_link_id = link.concept_dimension_link_id
              )
        ) THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'concept_dimension_link_active_source_support_ck',
                    MESSAGE = format(
                        'concept_dimension_link_active_source_support_ck: active concept-dimension link %s requires source-version or dataset support',
                        checked_link_id
                    );
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_dimension_link_source_support$;

COMMENT ON FUNCTION evidence.enforce_dimension_link_source_support() IS
    'Deferred final-state validator for active concept-dimension links whose provenance scope requires support.';

CREATE CONSTRAINT TRIGGER dimension_link_support_assertion_ct
AFTER INSERT OR UPDATE
ON kb.concept_dimension_link
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_dimension_link_source_support();

COMMENT ON TRIGGER dimension_link_support_assertion_ct ON kb.concept_dimension_link IS
    'Rechecks required concept-dimension support after canonical link insertion or mutation.';

CREATE CONSTRAINT TRIGGER dimension_link_support_reciprocal_ct
AFTER INSERT OR UPDATE OR DELETE
ON evidence.concept_dimension_link_support
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_dimension_link_source_support();

COMMENT ON TRIGGER dimension_link_support_reciprocal_ct ON evidence.concept_dimension_link_support IS
    'Rechecks both sides of concept-dimension support insertion, deletion, and retargeting against final state.';

CREATE FUNCTION corpus.enforce_observation_resolution_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_observation_resolution_semantics$
DECLARE
    status_is_resolved BOOLEAN;
    observed_expression_id BIGINT;
    lexicalized_expression_id BIGINT;
BEGIN
    SELECT rs.is_resolved
    INTO status_is_resolved
    FROM ref.resolution_status AS rs
    WHERE rs.resolution_status_code = NEW.resolution_status_code;

    -- A missing status is left to the ordinary foreign key.
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    IF status_is_resolved <> (NEW.lexicalization_id IS NOT NULL) THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'observation_resolution_semantics_ck',
                MESSAGE = 'observation_resolution_semantics_ck: resolved status requires a lexicalization and non-resolved status forbids one';
    END IF;

    IF NEW.lexicalization_id IS NOT NULL THEN
        SELECT oe.expression_id
        INTO observed_expression_id
        FROM corpus.observation_expression AS oe
        WHERE oe.observation_expression_id = NEW.observation_expression_id;

        SELECT l.expression_id
        INTO lexicalized_expression_id
        FROM kb.lexicalization AS l
        WHERE l.lexicalization_id = NEW.lexicalization_id;

        -- Missing referenced rows are left to their ordinary foreign keys.
        IF observed_expression_id IS NOT NULL
           AND lexicalized_expression_id IS NOT NULL
           AND observed_expression_id <> lexicalized_expression_id THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'observation_resolution_expression_match_ck',
                    MESSAGE = 'observation_resolution_expression_match_ck: resolution lexicalization must use the observed lexical expression';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_observation_resolution_semantics$;

COMMENT ON FUNCTION corpus.enforce_observation_resolution_semantics() IS
    'Enforces status-driven resolution nullability and requires a resolved lexicalization to use the observed expression.';

CREATE TRIGGER observation_resolution_semantics_biu
BEFORE INSERT OR UPDATE OF
    observation_expression_id,
    resolution_status_code,
    lexicalization_id
ON corpus.observation_resolution
FOR EACH ROW
EXECUTE FUNCTION corpus.enforce_observation_resolution_semantics();

COMMENT ON TRIGGER observation_resolution_semantics_biu ON corpus.observation_resolution IS
    'Preserves explicit unresolved observations and rejects cross-expression resolutions.';

COMMENT ON CONSTRAINT empirical_pair_nondirectional_order_ck
ON evidence.empirical_pair_measurement IS
    'Nondirectional empirical pairs use lesser concept ID first; directional measurements preserve subject/object roles.';

COMMENT ON CONSTRAINT expression_cooccurrence_endpoint_order_ck
ON corpus.expression_cooccurrence_measurement IS
    'Expression co-occurrence is nondirectional and stores each pair in strict lesser-ID-first order.';

CREATE FUNCTION evidence.enforce_scaled_value_bounds()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_scaled_value_bounds$
DECLARE
    selected_scale_id BIGINT;
    scale_minimum NUMERIC;
    scale_maximum NUMERIC;
    values_to_check NUMERIC[];
    checked_value NUMERIC;
    diagnostic_name TEXT;
BEGIN
    IF TG_TABLE_SCHEMA = 'evidence'
       AND TG_TABLE_NAME = 'empirical_pair_measurement' THEN
        selected_scale_id := NEW.measurement_scale_id;
        values_to_check := ARRAY[NEW.measured_value];
        diagnostic_name := 'empirical_pair_measurement_scale_bounds_ck';
    ELSIF TG_TABLE_SCHEMA = 'evidence'
          AND TG_TABLE_NAME = 'reference_calibration' THEN
        selected_scale_id := NEW.measurement_scale_id;
        values_to_check := ARRAY[
            NEW.minimum_value,
            NEW.typical_value,
            NEW.maximum_value
        ];
        diagnostic_name := 'reference_calibration_scale_bounds_ck';
    ELSIF TG_TABLE_SCHEMA = 'corpus'
          AND TG_TABLE_NAME = 'expression_cooccurrence_measurement' THEN
        selected_scale_id := NEW.measurement_scale_id;
        values_to_check := ARRAY[NEW.measured_value];
        diagnostic_name := 'expression_cooccurrence_scale_bounds_ck';
    ELSIF TG_TABLE_SCHEMA = 'ml'
          AND TG_TABLE_NAME = 'candidate_signal' THEN
        selected_scale_id := NEW.measurement_scale_id;
        values_to_check := ARRAY[NEW.signal_value];
        diagnostic_name := 'candidate_signal_scale_bounds_ck';
    ELSE
        RAISE EXCEPTION
            USING
                ERRCODE = '55000',
                MESSAGE = format(
                    'evidence.enforce_scaled_value_bounds is not configured for %.%',
                    TG_TABLE_SCHEMA,
                    TG_TABLE_NAME
                );
    END IF;

    SELECT scale.minimum_value, scale.maximum_value
    INTO scale_minimum, scale_maximum
    FROM evidence.measurement_scale AS scale
    WHERE scale.measurement_scale_id = selected_scale_id;

    -- A missing scale is left to the ordinary foreign key.
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    FOREACH checked_value IN ARRAY values_to_check LOOP
        IF checked_value < scale_minimum OR checked_value > scale_maximum THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = diagnostic_name,
                    MESSAGE = format(
                        '%s: value %s is outside scale %s bounds [%s, %s]',
                        diagnostic_name,
                        checked_value,
                        selected_scale_id,
                        scale_minimum,
                        scale_maximum
                    );
        END IF;
    END LOOP;

    RETURN NEW;
END;
$enforce_scaled_value_bounds$;

COMMENT ON FUNCTION evidence.enforce_scaled_value_bounds() IS
    'Validates every scaled empirical, calibration, corpus, or candidate value against the selected measurement-scale bounds.';

CREATE TRIGGER empirical_pair_scale_bounds_biu
BEFORE INSERT OR UPDATE OF measurement_scale_id, measured_value
ON evidence.empirical_pair_measurement
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_scaled_value_bounds();

COMMENT ON TRIGGER empirical_pair_scale_bounds_biu ON evidence.empirical_pair_measurement IS
    'Rejects empirical pair values outside their declared measurement scale.';

CREATE TRIGGER reference_calibration_scale_bounds_biu
BEFORE INSERT OR UPDATE OF
    measurement_scale_id,
    minimum_value,
    typical_value,
    maximum_value
ON evidence.reference_calibration
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_scaled_value_bounds();

COMMENT ON TRIGGER reference_calibration_scale_bounds_biu ON evidence.reference_calibration IS
    'Rejects any calibration endpoint or typical value outside its declared measurement scale.';

CREATE TRIGGER cooccurrence_scale_bounds_biu
BEFORE INSERT OR UPDATE OF measurement_scale_id, measured_value
ON corpus.expression_cooccurrence_measurement
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_scaled_value_bounds();

COMMENT ON TRIGGER cooccurrence_scale_bounds_biu ON corpus.expression_cooccurrence_measurement IS
    'Rejects corpus co-occurrence values outside their declared measurement scale.';

CREATE TRIGGER candidate_signal_scale_bounds_biu
BEFORE INSERT OR UPDATE OF measurement_scale_id, signal_value
ON ml.candidate_signal
FOR EACH ROW
EXECUTE FUNCTION evidence.enforce_scaled_value_bounds();

COMMENT ON TRIGGER candidate_signal_scale_bounds_biu ON ml.candidate_signal IS
    'Rejects model candidate signals outside their declared measurement scale.';

CREATE FUNCTION evidence.guard_used_measurement_scale()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_used_measurement_scale$
DECLARE
    semantic_change BOOLEAN := FALSE;
BEGIN
    IF TG_OP = 'DELETE' THEN
        semantic_change := TRUE;
    ELSE
        semantic_change := ROW(
            OLD.measurement_scale_id,
            OLD.scale_key,
            OLD.minimum_value,
            OLD.maximum_value,
            OLD.unit,
            OLD.value_semantics
        ) IS DISTINCT FROM ROW(
            NEW.measurement_scale_id,
            NEW.scale_key,
            NEW.minimum_value,
            NEW.maximum_value,
            NEW.unit,
            NEW.value_semantics
        );
    END IF;

    IF semantic_change
       AND (
           EXISTS (
               SELECT 1
               FROM evidence.empirical_pair_measurement AS measurement
               WHERE measurement.measurement_scale_id = OLD.measurement_scale_id
           )
           OR EXISTS (
               SELECT 1
               FROM evidence.reference_calibration AS calibration
               WHERE calibration.measurement_scale_id = OLD.measurement_scale_id
           )
           OR EXISTS (
               SELECT 1
               FROM corpus.expression_cooccurrence_measurement AS cooccurrence
               WHERE cooccurrence.measurement_scale_id = OLD.measurement_scale_id
           )
           OR EXISTS (
               SELECT 1
               FROM ml.candidate_signal AS signal
               WHERE signal.measurement_scale_id = OLD.measurement_scale_id
           )
       ) THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'measurement_scale_used_semantics_immutable_ck',
                MESSAGE = format(
                    'measurement_scale_used_semantics_immutable_ck: used measurement scale %s cannot be changed or deleted',
                    OLD.measurement_scale_id
                );
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_used_measurement_scale$;

COMMENT ON FUNCTION evidence.guard_used_measurement_scale() IS
    'Freezes the identity, key, range, unit, and value semantics of a measurement scale after any scientific or model row uses it.';

CREATE TRIGGER measurement_scale_used_semantics_bud
BEFORE UPDATE OR DELETE
ON evidence.measurement_scale
FOR EACH ROW
EXECUTE FUNCTION evidence.guard_used_measurement_scale();

COMMENT ON TRIGGER measurement_scale_used_semantics_bud ON evidence.measurement_scale IS
    'Prevents changing the interpretation or bounds of values already recorded against a scale.';

CREATE FUNCTION ml.enforce_model_run_terminal_timestamp()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_model_run_terminal_timestamp$
DECLARE
    status_is_terminal BOOLEAN;
BEGIN
    SELECT status.is_terminal
    INTO status_is_terminal
    FROM ref.model_run_status AS status
    WHERE status.model_run_status_code = NEW.model_run_status_code;

    -- A missing status is left to the ordinary foreign key.
    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    IF status_is_terminal <> (NEW.completed_at IS NOT NULL) THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'model_run_terminal_timestamp_ck',
                MESSAGE = 'model_run_terminal_timestamp_ck: terminal model runs require completed_at and non-terminal runs forbid it';
    END IF;

    RETURN NEW;
END;
$enforce_model_run_terminal_timestamp$;

COMMENT ON FUNCTION ml.enforce_model_run_terminal_timestamp() IS
    'Keeps model-run terminal status semantics synchronized with completion timestamp presence without promoting any output.';

CREATE TRIGGER model_run_terminal_timestamp_biu
BEFORE INSERT OR UPDATE OF model_run_status_code, completed_at
ON ml.model_run
FOR EACH ROW
EXECUTE FUNCTION ml.enforce_model_run_terminal_timestamp();

COMMENT ON TRIGGER model_run_terminal_timestamp_biu ON ml.model_run IS
    'Rejects terminal runs without completion timestamps and non-terminal runs with completion timestamps.';

CREATE FUNCTION ml.enforce_mapping_inference_candidate_count()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_mapping_inference_candidate_count$
DECLARE
    inference_ids BIGINT[];
    checked_inference_id BIGINT;
    checked_resolution_status_code TEXT;
    status_is_resolved BOOLEAN;
    candidate_count BIGINT;
BEGIN
    IF TG_TABLE_NAME = 'mapping_inference' THEN
        inference_ids := ARRAY[NEW.mapping_inference_id];
    ELSIF TG_OP = 'INSERT' THEN
        inference_ids := ARRAY[NEW.mapping_inference_id];
    ELSIF TG_OP = 'DELETE' THEN
        inference_ids := ARRAY[OLD.mapping_inference_id];
    ELSE
        inference_ids := ARRAY[
            OLD.mapping_inference_id,
            NEW.mapping_inference_id
        ];
    END IF;

    FOREACH checked_inference_id IN ARRAY inference_ids LOOP
        SELECT
            inference.resolution_status_code,
            status.is_resolved,
            count(candidate.mapping_candidate_id)
        INTO
            checked_resolution_status_code,
            status_is_resolved,
            candidate_count
        FROM ml.mapping_inference AS inference
        JOIN ref.resolution_status AS status
          ON status.resolution_status_code = inference.resolution_status_code
        LEFT JOIN ml.mapping_candidate AS candidate
          ON candidate.mapping_inference_id = inference.mapping_inference_id
        WHERE inference.mapping_inference_id = checked_inference_id
        GROUP BY
            inference.resolution_status_code,
            status.is_resolved;

        -- A deleted inference has no final-state obligation.
        IF NOT FOUND THEN
            CONTINUE;
        END IF;

        IF status_is_resolved AND candidate_count < 1 THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'mapping_inference_resolved_candidate_count_ck',
                    MESSAGE = format(
                        'mapping_inference_resolved_candidate_count_ck: resolved inference %s requires at least one candidate',
                        checked_inference_id
                    );
        ELSIF checked_resolution_status_code = 'unresolved'
              AND candidate_count <> 0 THEN
            RAISE EXCEPTION
                USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'mapping_inference_unresolved_candidate_count_ck',
                    MESSAGE = format(
                        'mapping_inference_unresolved_candidate_count_ck: unresolved inference %s must have zero candidates',
                        checked_inference_id
                    );
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_mapping_inference_candidate_count$;

COMMENT ON FUNCTION ml.enforce_mapping_inference_candidate_count() IS
    'Deferred final-state validator: resolved inference requires candidates, explicit unresolved requires none, and pending workflow states remain reviewable.';

CREATE CONSTRAINT TRIGGER inference_candidate_count_inference_ct
AFTER INSERT OR UPDATE
ON ml.mapping_inference
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION ml.enforce_mapping_inference_candidate_count();

COMMENT ON TRIGGER inference_candidate_count_inference_ct ON ml.mapping_inference IS
    'Rechecks candidate cardinality after inference insertion or status changes at transaction completion.';

CREATE CONSTRAINT TRIGGER inference_candidate_count_candidate_ct
AFTER INSERT OR UPDATE OR DELETE
ON ml.mapping_candidate
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION ml.enforce_mapping_inference_candidate_count();

COMMENT ON TRIGGER inference_candidate_count_candidate_ct ON ml.mapping_candidate IS
    'Reciprocally rechecks old and new inferences after candidate insertion, deletion, or retargeting.';

CREATE FUNCTION audit.enforce_promotion_event_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_promotion_event_semantics$
DECLARE
    review_permits_promotion BOOLEAN;
    target_status TEXT;
BEGIN
    IF pg_catalog.num_nonnulls(
        NEW.target_concept_id,
        NEW.target_lexicalization_id,
        NEW.target_concept_relation_id,
        NEW.target_concept_dimension_link_id
    ) <> 1 THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'promotion_event_exactly_one_target_ck',
                MESSAGE = 'promotion_event_exactly_one_target_ck: a promotion event must target exactly one canonical object';
    END IF;

    SELECT decision.permits_promotion
    INTO review_permits_promotion
    FROM audit.review AS review
    JOIN ref.review_decision AS decision
      ON decision.review_decision_code = review.review_decision_code
    WHERE review.review_id = NEW.review_id;

    -- A missing review is left to the ordinary foreign key.
    IF FOUND AND NOT review_permits_promotion THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'promotion_event_review_permits_ck',
                MESSAGE = 'promotion_event_review_permits_ck: the linked review decision does not permit promotion';
    END IF;

    IF NEW.target_concept_id IS NOT NULL THEN
        SELECT c.lifecycle_status_code
        INTO target_status
        FROM kb.concept AS c
        WHERE c.concept_id = NEW.target_concept_id;
    ELSIF NEW.target_lexicalization_id IS NOT NULL THEN
        SELECT l.lifecycle_status_code
        INTO target_status
        FROM kb.lexicalization AS l
        WHERE l.lexicalization_id = NEW.target_lexicalization_id;
    ELSIF NEW.target_concept_relation_id IS NOT NULL THEN
        SELECT cr.lifecycle_status_code
        INTO target_status
        FROM kb.concept_relation AS cr
        WHERE cr.concept_relation_id = NEW.target_concept_relation_id;
    ELSE
        SELECT link.lifecycle_status_code
        INTO target_status
        FROM kb.concept_dimension_link AS link
        WHERE link.concept_dimension_link_id = NEW.target_concept_dimension_link_id;
    END IF;

    -- A missing target is left to its ordinary foreign key.
    IF FOUND AND target_status <> 'active' THEN
        RAISE EXCEPTION
            USING
                ERRCODE = '23514',
                CONSTRAINT = 'promotion_event_target_active_ck',
                MESSAGE = 'promotion_event_target_active_ck: a promotion event target must be lifecycle-active at event write';
    END IF;

    RETURN NEW;
END;
$enforce_promotion_event_semantics$;

COMMENT ON FUNCTION audit.enforce_promotion_event_semantics() IS
    'Validates singular explicit promotion, a permitting independent review decision, and a lifecycle-active canonical target at event write without mutating that target.';

CREATE TRIGGER promotion_event_semantics_biu
BEFORE INSERT OR UPDATE OF
    review_id,
    target_concept_id,
    target_lexicalization_id,
    target_concept_relation_id,
    target_concept_dimension_link_id
ON audit.promotion_event
FOR EACH ROW
EXECUTE FUNCTION audit.enforce_promotion_event_semantics();

COMMENT ON TRIGGER promotion_event_semantics_biu ON audit.promotion_event IS
    'Guards explicit promotion records but never promotes, rewrites, or creates a canonical assertion.';

COMMIT;
