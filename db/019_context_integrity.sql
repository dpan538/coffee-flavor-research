\set ON_ERROR_STOP on

-- Round 3A integrity rules. These rules preserve polyhierarchy, ambiguity,
-- explicit unknowns, source provenance, and measured-context semantics.

BEGIN;

CREATE FUNCTION context.enforce_preparation_relation_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_preparation_relation_semantics$
DECLARE
    relation_is_hierarchical BOOLEAN;
    cycle_exists BOOLEAN;
BEGIN
    SELECT is_hierarchical
    INTO relation_is_hierarchical
    FROM ref.context_relation_type
    WHERE context_relation_type_code = NEW.context_relation_type_code;

    IF relation_is_hierarchical THEN
        WITH RECURSIVE descendants(concept_id) AS (
            SELECT relation.object_preparation_concept_id
            FROM context.preparation_relation AS relation
            WHERE relation.subject_preparation_concept_id =
                  NEW.object_preparation_concept_id
              AND relation.context_relation_type_code = 'broader_than'
              AND relation.lifecycle_status_code = 'active'
              AND relation.preparation_relation_id <>
                  COALESCE(NEW.preparation_relation_id, -1)
            UNION
            SELECT relation.object_preparation_concept_id
            FROM context.preparation_relation AS relation
            JOIN descendants
              ON descendants.concept_id =
                 relation.subject_preparation_concept_id
            WHERE relation.context_relation_type_code = 'broader_than'
              AND relation.lifecycle_status_code = 'active'
              AND relation.preparation_relation_id <>
                  COALESCE(NEW.preparation_relation_id, -1)
        )
        SELECT EXISTS (
            SELECT 1
            FROM descendants
            WHERE concept_id = NEW.subject_preparation_concept_id
        ) INTO cycle_exists;

        IF cycle_exists THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'preparation_relation_acyclic_ck',
                MESSAGE = 'preparation_relation_acyclic_ck: broader preparation relations must remain acyclic';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_preparation_relation_semantics$;

CREATE TRIGGER preparation_relation_semantics_biu
BEFORE INSERT OR UPDATE ON context.preparation_relation
FOR EACH ROW EXECUTE FUNCTION context.enforce_preparation_relation_semantics();

CREATE FUNCTION context.enforce_context_expression_mapping_ambiguity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_context_expression_mapping_ambiguity$
DECLARE
    conflicting_nonambiguous BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'preparation_expression_mapping' THEN
        SELECT EXISTS (
            SELECT 1
            FROM context.preparation_expression_mapping AS mapping
            JOIN ref.context_mapping_certainty AS certainty
              ON certainty.context_mapping_certainty_code =
                 mapping.context_mapping_certainty_code
            WHERE mapping.preparation_expression_id =
                  NEW.preparation_expression_id
              AND mapping.preparation_expression_mapping_id <>
                  COALESCE(NEW.preparation_expression_mapping_id, -1)
              AND mapping.lifecycle_status_code = 'active'
              AND (
                    NOT certainty.is_ambiguous
                    OR NEW.context_mapping_certainty_code <> 'ambiguous_candidate'
                  )
        ) INTO conflicting_nonambiguous;
    ELSE
        SELECT EXISTS (
            SELECT 1
            FROM context.roast_expression_mapping AS mapping
            JOIN ref.context_mapping_certainty AS certainty
              ON certainty.context_mapping_certainty_code =
                 mapping.context_mapping_certainty_code
            WHERE mapping.roast_expression_id = NEW.roast_expression_id
              AND mapping.roast_expression_mapping_id <>
                  COALESCE(NEW.roast_expression_mapping_id, -1)
              AND mapping.lifecycle_status_code = 'active'
              AND (
                    NOT certainty.is_ambiguous
                    OR NEW.context_mapping_certainty_code <> 'ambiguous_candidate'
                  )
        ) INTO conflicting_nonambiguous;
    END IF;

    IF NEW.lifecycle_status_code = 'active' AND conflicting_nonambiguous THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'context_expression_mapping_ambiguity_ck',
            MESSAGE = 'context_expression_mapping_ambiguity_ck: multiple active senses require every mapping to be explicitly ambiguous';
    END IF;
    RETURN NEW;
END;
$enforce_context_expression_mapping_ambiguity$;

CREATE TRIGGER preparation_expression_mapping_ambiguity_biu
BEFORE INSERT OR UPDATE ON context.preparation_expression_mapping
FOR EACH ROW EXECUTE FUNCTION context.enforce_context_expression_mapping_ambiguity();

CREATE TRIGGER roast_expression_mapping_ambiguity_biu
BEFORE INSERT OR UPDATE ON context.roast_expression_mapping
FOR EACH ROW EXECUTE FUNCTION context.enforce_context_expression_mapping_ambiguity();

CREATE FUNCTION context.enforce_roast_category_scheme_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_roast_category_scheme_semantics$
DECLARE
    scheme_is_ordinal BOOLEAN;
BEGIN
    SELECT kind.is_ordinal
    INTO scheme_is_ordinal
    FROM context.roast_scheme AS scheme
    JOIN ref.roast_scheme_kind AS kind
      ON kind.roast_scheme_kind_code = scheme.roast_scheme_kind_code
    WHERE scheme.roast_scheme_id = NEW.roast_scheme_id;

    IF scheme_is_ordinal IS DISTINCT FROM (NEW.ordinal_position IS NOT NULL) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'roast_category_scheme_ordinal_ck',
            MESSAGE = 'roast_category_scheme_ordinal_ck: ordinal schemes require positions and terminology schemes prohibit invented ordering';
    END IF;
    RETURN NEW;
END;
$enforce_roast_category_scheme_semantics$;

CREATE TRIGGER roast_category_scheme_semantics_biu
BEFORE INSERT OR UPDATE ON context.roast_category
FOR EACH ROW EXECUTE FUNCTION context.enforce_roast_category_scheme_semantics();

CREATE FUNCTION context.enforce_roast_category_mapping_target()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_roast_category_mapping_target$
DECLARE
    target_is_project_normalized BOOLEAN;
BEGIN
    SELECT scheme.is_project_normalized_target
    INTO target_is_project_normalized
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    WHERE category.roast_category_id = NEW.normalized_roast_category_id;

    IF target_is_project_normalized IS NOT TRUE THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'roast_category_mapping_target_ck',
            MESSAGE = 'roast_category_mapping_target_ck: normalized targets must belong to the one explicit project target scheme';
    END IF;
    RETURN NEW;
END;
$enforce_roast_category_mapping_target$;

CREATE TRIGGER roast_category_mapping_target_biu
BEFORE INSERT OR UPDATE ON context.roast_category_mapping
FOR EACH ROW EXECUTE FUNCTION context.enforce_roast_category_mapping_target();

CREATE FUNCTION context.enforce_observation_context_targets()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_observation_context_targets$
DECLARE
    preparation_is_current BOOLEAN;
    roast_is_project_target BOOLEAN;
BEGIN
    IF NEW.normalized_preparation_concept_id IS NOT NULL THEN
        SELECT lifecycle_status_code = 'active'
        INTO preparation_is_current
        FROM context.preparation_concept
        WHERE preparation_concept_id = NEW.normalized_preparation_concept_id;

        IF preparation_is_current IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'observation_context_preparation_target_ck',
                MESSAGE = 'observation_context_preparation_target_ck: normalized preparation must be an active project context concept';
        END IF;
    END IF;

    IF NEW.normalized_roast_category_id IS NOT NULL THEN
        SELECT scheme.is_project_normalized_target
        INTO roast_is_project_target
        FROM context.roast_category AS category
        JOIN context.roast_scheme AS scheme
          ON scheme.roast_scheme_id = category.roast_scheme_id
        WHERE category.roast_category_id = NEW.normalized_roast_category_id;

        IF roast_is_project_target IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'observation_context_roast_target_ck',
                MESSAGE = 'observation_context_roast_target_ck: normalized roast must belong to the explicit project target scheme';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_observation_context_targets$;

CREATE TRIGGER observation_context_targets_biu
BEFORE INSERT OR UPDATE ON context.observation_context
FOR EACH ROW EXECUTE FUNCTION context.enforce_observation_context_targets();

CREATE FUNCTION context.enforce_observation_addition_presence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_observation_addition_presence$
DECLARE
    addition_rows_allowed BOOLEAN;
BEGIN
    SELECT presence.allows_addition_rows
    INTO addition_rows_allowed
    FROM context.observation_context AS observation_context
    JOIN ref.addition_presence AS presence
      ON presence.addition_presence_code =
         observation_context.addition_presence_code
    WHERE observation_context.observation_context_id =
          NEW.observation_context_id;

    IF addition_rows_allowed IS NOT TRUE THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'observation_addition_presence_ck',
            MESSAGE = 'observation_addition_presence_ck: addition rows require an explicit present status';
    END IF;
    RETURN NEW;
END;
$enforce_observation_addition_presence$;

CREATE TRIGGER observation_addition_presence_biu
BEFORE INSERT OR UPDATE ON context.observation_addition
FOR EACH ROW EXECUTE FUNCTION context.enforce_observation_addition_presence();

CREATE FUNCTION context.enforce_roast_measurement_bounds()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_roast_measurement_bounds$
DECLARE
    allowed_minimum NUMERIC;
    allowed_maximum NUMERIC;
BEGIN
    SELECT method.minimum_value, method.maximum_value
    INTO allowed_minimum, allowed_maximum
    FROM context.roast_measurement_method AS method
    WHERE method.roast_measurement_method_id =
          NEW.roast_measurement_method_id;

    IF NEW.measured_value < allowed_minimum
       OR NEW.measured_value > allowed_maximum THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'observation_roast_measurement_bounds_ck',
            MESSAGE = 'observation_roast_measurement_bounds_ck: value lies outside the declared measurement-method range';
    END IF;
    RETURN NEW;
END;
$enforce_roast_measurement_bounds$;

CREATE TRIGGER observation_roast_measurement_bounds_biu
BEFORE INSERT OR UPDATE ON context.observation_roast_measurement
FOR EACH ROW EXECUTE FUNCTION context.enforce_roast_measurement_bounds();

CREATE FUNCTION context.enforce_beverage_addition_hierarchy()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_beverage_addition_hierarchy$
DECLARE
    cycle_exists BOOLEAN;
BEGIN
    IF NEW.parent_beverage_addition_type_id IS NULL THEN
        RETURN NEW;
    END IF;

    WITH RECURSIVE ancestors(addition_type_id) AS (
        SELECT parent_beverage_addition_type_id
        FROM context.beverage_addition_type
        WHERE beverage_addition_type_id =
              NEW.parent_beverage_addition_type_id
        UNION
        SELECT addition.parent_beverage_addition_type_id
        FROM context.beverage_addition_type AS addition
        JOIN ancestors
          ON ancestors.addition_type_id = addition.beverage_addition_type_id
        WHERE addition.parent_beverage_addition_type_id IS NOT NULL
    )
    SELECT EXISTS (
        SELECT 1 FROM ancestors
        WHERE addition_type_id = NEW.beverage_addition_type_id
    ) INTO cycle_exists;

    IF cycle_exists THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'beverage_addition_type_acyclic_ck',
            MESSAGE = 'beverage_addition_type_acyclic_ck: beverage-addition hierarchy must remain acyclic';
    END IF;
    RETURN NEW;
END;
$enforce_beverage_addition_hierarchy$;

CREATE TRIGGER beverage_addition_hierarchy_biu
BEFORE INSERT OR UPDATE ON context.beverage_addition_type
FOR EACH ROW EXECUTE FUNCTION context.enforce_beverage_addition_hierarchy();

COMMENT ON FUNCTION context.enforce_context_expression_mapping_ambiguity() IS
    'Preserves polysemy only when every competing current mapping is explicitly marked ambiguous; ambiguity is never erased to satisfy uniqueness.';
COMMENT ON FUNCTION context.enforce_roast_category_mapping_target() IS
    'Prevents a source-specific or industry terminology scheme from silently becoming the normalized project roast scale.';
COMMENT ON FUNCTION context.enforce_observation_context_targets() IS
    'Ensures normalized observation values resolve only to active preparation context or the designated project roast target; unknown remains a status, not a category.';

COMMIT;
