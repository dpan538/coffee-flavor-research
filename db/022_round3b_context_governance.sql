\set ON_ERROR_STOP on

-- Round 3B forward-only interaction governance. Round 3A rows remain
-- queryable; the five-level scheme is retired only as the current product
-- projection.

BEGIN;

INSERT INTO evidence.source (
    source_key, title, creator, publisher, citation, source_url,
    external_metadata
)
VALUES (
    'source.project.coffee_sensory_kb_v0_round3b_context',
    'Coffee Sensory KB V0 Round 3B Context Interaction Decision',
    'Coffee Flavor Atlas project',
    'Coffee Flavor Atlas project',
    'Coffee Flavor Atlas project. Context interaction decision: mandatory C0 and seven-level C1. 2026.',
    NULL,
    '{"authorship":"project","interaction_constraint":true,"empirical_calibration_claim":false}'::JSONB
);

INSERT INTO evidence.source_version (
    source_version_key, source_id, license_policy_id, version_label,
    published_on, retrieved_on, version_locator, external_metadata
)
SELECT
    'source_version.project.context_v1.2026-08-25',
    source.source_id,
    policy.license_policy_id,
    'Round 3B context interaction decision 2026-08-25',
    DATE '2026-08-25',
    DATE '2026-08-25',
    'docs/decisions/CONTEXT_INTERACTION_DECISION_20260825.md',
    '{"scheme_semantics":"ordinal_not_interval","minimum_user_levels":7}'::JSONB
FROM evidence.source AS source
CROSS JOIN evidence.license_policy AS policy
WHERE source.source_key =
      'source.project.coffee_sensory_kb_v0_round3b_context'
  AND policy.license_policy_key = 'license.project_context.cc_by_4_0.v1';

ALTER TABLE context.roast_scheme
    ADD COLUMN supersedes_roast_scheme_id BIGINT,
    ADD COLUMN activated_on DATE,
    ADD COLUMN retired_on DATE,
    ADD CONSTRAINT roast_scheme_supersedes_fk
        FOREIGN KEY (supersedes_roast_scheme_id)
        REFERENCES context.roast_scheme (roast_scheme_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT roast_scheme_no_self_supersession_ck CHECK (
        supersedes_roast_scheme_id IS NULL
        OR supersedes_roast_scheme_id <> roast_scheme_id
    ),
    ADD CONSTRAINT roast_scheme_current_active_ck CHECK (
        NOT is_project_normalized_target
        OR lifecycle_status_code = 'active' AND retired_on IS NULL
    );

UPDATE context.roast_scheme
SET
    lifecycle_status_code = 'deprecated',
    is_project_normalized_target = FALSE,
    activated_on = DATE '2026-08-25',
    retired_on = DATE '2026-08-25'
WHERE roast_scheme_key = 'roast.scheme.project_v0_five_level';

INSERT INTO context.roast_scheme (
    roast_scheme_key, roast_scheme_kind_code, lifecycle_status_code,
    source_version_id, name, description, is_project_normalized_target,
    supersedes_roast_scheme_id, activated_on
)
SELECT
    'roast.scheme.project_v1_seven_level',
    'project_user_scale',
    'active',
    source_version.source_version_id,
    'Project V1 seven-level roast context',
    'Current project-defined ordinal interaction categories. Positions provide order only and do not encode equal physical or sensory distance.',
    FALSE,
    historical.roast_scheme_id,
    DATE '2026-08-25'
FROM evidence.source_version AS source_version
CROSS JOIN context.roast_scheme AS historical
WHERE source_version.source_version_key =
      'source_version.project.context_v1.2026-08-25'
  AND historical.roast_scheme_key = 'roast.scheme.project_v0_five_level';

INSERT INTO context.roast_category (
    roast_category_key, roast_scheme_id, source_category_code,
    preferred_label, ordinal_position, lifecycle_status_code, description
)
SELECT
    category.category_key,
    scheme.roast_scheme_id,
    category.category_code,
    category.preferred_label,
    category.ordinal_position,
    'active',
    category.description
FROM (VALUES
    ('roast.project_v1.extremely_light', 'extremely_light', 'Extremely light', 1::SMALLINT, 'Lightest project interaction category; no universal color boundary is asserted.'),
    ('roast.project_v1.light', 'light', 'Light', 2::SMALLINT, 'Project interaction category; no universal color boundary is asserted.'),
    ('roast.project_v1.medium_light', 'medium_light', 'Medium-light', 3::SMALLINT, 'Distinct project interaction category retained for target-market terminology; no universal color boundary is asserted.'),
    ('roast.project_v1.medium', 'medium', 'Medium', 4::SMALLINT, 'Project interaction category; no universal color boundary is asserted.'),
    ('roast.project_v1.medium_dark', 'medium_dark', 'Medium-dark', 5::SMALLINT, 'Distinct project interaction category retained for target-market terminology; no universal color boundary is asserted.'),
    ('roast.project_v1.dark', 'dark', 'Dark', 6::SMALLINT, 'Project interaction category; no universal color boundary is asserted.'),
    ('roast.project_v1.extremely_dark', 'extremely_dark', 'Extremely dark', 7::SMALLINT, 'Darkest project interaction category; no universal color boundary is asserted.')
) AS category(
    category_key, category_code, preferred_label, ordinal_position, description
)
CROSS JOIN context.roast_scheme AS scheme
WHERE scheme.roast_scheme_key = 'roast.scheme.project_v1_seven_level';

CREATE FUNCTION context.enforce_current_user_roast_scheme()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_current_user_roast_scheme$
DECLARE
    active_category_count BIGINT;
    required_category_count BIGINT;
BEGIN
    IF NEW.is_project_normalized_target
       AND (TG_OP = 'INSERT'
            OR OLD.is_project_normalized_target IS DISTINCT FROM TRUE) THEN
        SELECT
            count(*) FILTER (WHERE category.lifecycle_status_code = 'active'),
            count(*) FILTER (
                WHERE category.lifecycle_status_code = 'active'
                  AND category.source_category_code IN (
                      'medium_light', 'medium', 'medium_dark'
                  )
            )
        INTO active_category_count, required_category_count
        FROM context.roast_category AS category
        WHERE category.roast_scheme_id = NEW.roast_scheme_id;

        IF NEW.roast_scheme_kind_code <> 'project_user_scale'
           OR NEW.lifecycle_status_code <> 'active'
           OR active_category_count < 7
           OR required_category_count <> 3 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'current_user_roast_scheme_contract_ck',
                MESSAGE = 'current_user_roast_scheme_contract_ck: promotion requires an active project user scale with at least seven categories and distinct medium-light, medium, and medium-dark positions';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_current_user_roast_scheme$;

CREATE TRIGGER roast_scheme_current_contract_biu
BEFORE INSERT OR UPDATE ON context.roast_scheme
FOR EACH ROW EXECUTE FUNCTION context.enforce_current_user_roast_scheme();

UPDATE context.roast_scheme
SET is_project_normalized_target = TRUE
WHERE roast_scheme_key = 'roast.scheme.project_v1_seven_level';

INSERT INTO context.roast_category_mapping (
    roast_category_mapping_key, source_roast_category_id,
    normalized_roast_category_id, context_mapping_certainty_code,
    source_version_id, context_assertion_role_code, evidence_locator,
    lifecycle_status_code
)
SELECT
    mapping.mapping_key,
    source_category.roast_category_id,
    target_category.roast_category_id,
    mapping.certainty,
    source_version.source_version_id,
    'interpretive',
    'docs/decisions/CONTEXT_INTERACTION_DECISION_20260825.md',
    'active'
FROM (VALUES
    ('roast_mapping.v0_very_light.v1_extremely_light', 'roast.project.very_light', 'roast.project_v1.extremely_light', 'approximate'),
    ('roast_mapping.v0_light.v1_light', 'roast.project.light', 'roast.project_v1.light', 'exact_project_label'),
    ('roast_mapping.v0_medium.v1_medium', 'roast.project.medium', 'roast.project_v1.medium', 'exact_project_label'),
    ('roast_mapping.v0_dark.v1_dark', 'roast.project.dark', 'roast.project_v1.dark', 'exact_project_label'),
    ('roast_mapping.v0_very_dark.v1_extremely_dark', 'roast.project.very_dark', 'roast.project_v1.extremely_dark', 'approximate'),
    ('roast_mapping.common_light.v1_light', 'roast.common.light', 'roast.project_v1.light', 'approximate'),
    ('roast_mapping.common_medium.v1_medium', 'roast.common.medium', 'roast.project_v1.medium', 'approximate'),
    ('roast_mapping.common_dark.v1_dark', 'roast.common.dark', 'roast.project_v1.dark', 'approximate')
) AS mapping(mapping_key, source_key, target_key, certainty)
JOIN context.roast_category AS source_category
  ON source_category.roast_category_key = mapping.source_key
JOIN context.roast_category AS target_category
  ON target_category.roast_category_key = mapping.target_key
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.context_v1.2026-08-25';

CREATE FUNCTION context.protect_round3a_five_level_scheme()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3a_five_level_scheme$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '23514',
        CONSTRAINT = 'round3a_five_level_scheme_frozen_ck',
        MESSAGE = 'round3a_five_level_scheme_frozen_ck: the superseded Round 3A scheme is immutable and historically queryable';
END;
$protect_round3a_five_level_scheme$;

CREATE TRIGGER roast_scheme_round3a_frozen_bud
BEFORE UPDATE OR DELETE ON context.roast_scheme
FOR EACH ROW
WHEN (OLD.roast_scheme_key = 'roast.scheme.project_v0_five_level')
EXECUTE FUNCTION context.protect_round3a_five_level_scheme();

CREATE FUNCTION context.protect_round3a_five_level_category()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3a_five_level_category$
DECLARE
    historical_scheme_id BIGINT;
BEGIN
    SELECT scheme.roast_scheme_id
    INTO historical_scheme_id
    FROM context.roast_scheme AS scheme
    WHERE scheme.roast_scheme_key = 'roast.scheme.project_v0_five_level';

    IF OLD.roast_scheme_id = historical_scheme_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_five_level_category_frozen_ck',
            MESSAGE = 'round3a_five_level_category_frozen_ck: Round 3A roast categories cannot be modified or deleted';
    END IF;
    RETURN OLD;
END;
$protect_round3a_five_level_category$;

CREATE TRIGGER roast_category_round3a_frozen_bud
BEFORE UPDATE OR DELETE ON context.roast_category
FOR EACH ROW EXECUTE FUNCTION context.protect_round3a_five_level_category();

CREATE FUNCTION context.reject_unknown_user_preparation_family()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $reject_unknown_user_preparation_family$
BEGIN
    IF NEW.c0_top_level
       AND (
           NEW.preparation_concept_key ~ '(^|[._])(unknown|unsure|not_reported|reported_unresolved|not_applicable)([._]|$)'
           OR lower(NEW.preferred_label) IN (
               'unknown', 'unsure', 'i don''t know', 'not reported',
               'reported unresolved', 'not applicable'
           )
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'user_c0_unknown_family_ck',
            MESSAGE = 'user_c0_unknown_family_ck: observation-status values cannot become user-selectable preparation families';
    END IF;
    RETURN NEW;
END;
$reject_unknown_user_preparation_family$;

CREATE TRIGGER preparation_concept_no_unknown_user_biu
BEFORE INSERT OR UPDATE ON context.preparation_concept
FOR EACH ROW EXECUTE FUNCTION context.reject_unknown_user_preparation_family();

CREATE VIEW context.v_current_user_preparation AS
SELECT
    concept.preparation_concept_key,
    CASE concept.preparation_concept_key
        WHEN 'preparation.family.filter_percolation' THEN 1
        WHEN 'preparation.family.immersion' THEN 2
        WHEN 'preparation.family.hybrid' THEN 3
        WHEN 'preparation.family.espresso_pressure' THEN 4
        WHEN 'preparation.family.diluted_espresso' THEN 5
        WHEN 'preparation.family.stovetop_boiled' THEN 6
        WHEN 'preparation.family.cold_extraction' THEN 7
        WHEN 'preparation.family.espresso_milk' THEN 8
    END::SMALLINT AS ordinal_position,
    concept.preferred_label AS internal_label,
    CASE concept.preparation_concept_key
        WHEN 'preparation.family.filter_percolation' THEN 'Filter coffee'
        WHEN 'preparation.family.immersion' THEN 'Immersion brew'
        WHEN 'preparation.family.hybrid' THEN 'AeroPress / hybrid'
        WHEN 'preparation.family.espresso_pressure' THEN 'Espresso'
        WHEN 'preparation.family.diluted_espresso' THEN 'Espresso + water'
        WHEN 'preparation.family.stovetop_boiled' THEN 'Stovetop / boiled'
        WHEN 'preparation.family.cold_extraction' THEN 'Cold brew'
        WHEN 'preparation.family.espresso_milk' THEN 'Milk coffee'
    END AS candidate_user_label_en,
    CASE concept.preparation_concept_key
        WHEN 'preparation.family.filter_percolation' THEN '滤泡咖啡'
        WHEN 'preparation.family.immersion' THEN '浸泡式咖啡'
        WHEN 'preparation.family.hybrid' THEN '爱乐压 / 混合式'
        WHEN 'preparation.family.espresso_pressure' THEN '意式浓缩'
        WHEN 'preparation.family.diluted_espresso' THEN '浓缩加水'
        WHEN 'preparation.family.stovetop_boiled' THEN '炉煮 / 煮制'
        WHEN 'preparation.family.cold_extraction' THEN '冷萃咖啡'
        WHEN 'preparation.family.espresso_milk' THEN '奶咖'
    END AS candidate_user_label_zh_hans
FROM context.preparation_concept AS concept
WHERE concept.c0_top_level
  AND concept.preparation_concept_type_code = 'family'
  AND concept.lifecycle_status_code = 'active';

COMMENT ON VIEW context.v_current_user_preparation IS
    'Exactly the current valid C0 families. Database observation statuses are intentionally absent; labels are candidate UI wording, not new identities.';

CREATE VIEW context.v_current_user_roast AS
SELECT
    scheme.roast_scheme_key,
    category.roast_category_key,
    category.source_category_code AS interaction_code,
    category.preferred_label,
    category.ordinal_position,
    'ordinal_not_interval'::TEXT AS scale_semantics
FROM context.roast_scheme AS scheme
JOIN context.roast_category AS category
  ON category.roast_scheme_id = scheme.roast_scheme_id
WHERE scheme.is_project_normalized_target
  AND scheme.lifecycle_status_code = 'active'
  AND category.lifecycle_status_code = 'active';

COMMENT ON VIEW context.v_current_user_roast IS
    'Current C1 product choices only. Ordinal positions provide order and do not assert equal physical or sensory distance.';

COMMIT;
