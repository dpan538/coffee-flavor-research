\set ON_ERROR_STOP on
\pset pager off

-- Round 3B failure-path tests. Every fixture is transaction-local.

BEGIN;

CREATE FUNCTION pg_temp.expect_round3b_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3b_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3B negative statement unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND3B_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3b_failure$;

-- Build three non-current fixtures. Promotion, rather than insertion, is the
-- contract boundary so incomplete schemes remain legal drafting artifacts.
INSERT INTO context.roast_scheme (
    roast_scheme_key, roast_scheme_kind_code, lifecycle_status_code,
    source_version_id, name, description, is_project_normalized_target
)
SELECT fixture.scheme_key, 'project_user_scale', 'active',
       source_version.source_version_id, fixture.name,
       'Round 3B transaction-local negative fixture.', FALSE
FROM (VALUES
    ('negative.round3b.five_level', 'Five-level promotion fixture'),
    ('negative.round3b.missing_medium_light', 'Missing medium-light fixture'),
    ('negative.round3b.missing_medium_dark', 'Missing medium-dark fixture')
) AS fixture(scheme_key, name)
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.context_v1.2026-08-25';

INSERT INTO context.roast_category (
    roast_category_key, roast_scheme_id, source_category_code,
    preferred_label, ordinal_position, lifecycle_status_code, description
)
SELECT
    scheme.roast_scheme_key || '.' || category.category_code,
    scheme.roast_scheme_id, category.category_code, category.label,
    category.position, 'active', 'Round 3B transaction-local fixture.'
FROM context.roast_scheme AS scheme
CROSS JOIN (VALUES
    ('one', 'One', 1::SMALLINT), ('two', 'Two', 2::SMALLINT),
    ('three', 'Three', 3::SMALLINT), ('four', 'Four', 4::SMALLINT),
    ('five', 'Five', 5::SMALLINT)
) AS category(category_code, label, position)
WHERE scheme.roast_scheme_key = 'negative.round3b.five_level';

INSERT INTO context.roast_category (
    roast_category_key, roast_scheme_id, source_category_code,
    preferred_label, ordinal_position, lifecycle_status_code, description
)
SELECT
    scheme.roast_scheme_key || '.' || category.category_code,
    scheme.roast_scheme_id, category.category_code, category.label,
    category.position, 'active', 'Round 3B transaction-local fixture.'
FROM context.roast_scheme AS scheme
CROSS JOIN (VALUES
    ('extremely_light', 'Extremely light', 1::SMALLINT),
    ('light', 'Light', 2::SMALLINT), ('light_plus', 'Light plus', 3::SMALLINT),
    ('medium', 'Medium', 4::SMALLINT),
    ('medium_dark', 'Medium-dark', 5::SMALLINT),
    ('dark', 'Dark', 6::SMALLINT),
    ('extremely_dark', 'Extremely dark', 7::SMALLINT)
) AS category(category_code, label, position)
WHERE scheme.roast_scheme_key = 'negative.round3b.missing_medium_light';

INSERT INTO context.roast_category (
    roast_category_key, roast_scheme_id, source_category_code,
    preferred_label, ordinal_position, lifecycle_status_code, description
)
SELECT
    scheme.roast_scheme_key || '.' || category.category_code,
    scheme.roast_scheme_id, category.category_code, category.label,
    category.position, 'active', 'Round 3B transaction-local fixture.'
FROM context.roast_scheme AS scheme
CROSS JOIN (VALUES
    ('extremely_light', 'Extremely light', 1::SMALLINT),
    ('light', 'Light', 2::SMALLINT),
    ('medium_light', 'Medium-light', 3::SMALLINT),
    ('medium', 'Medium', 4::SMALLINT), ('dark_minus', 'Dark minus', 5::SMALLINT),
    ('dark', 'Dark', 6::SMALLINT),
    ('extremely_dark', 'Extremely dark', 7::SMALLINT)
) AS category(category_code, label, position)
WHERE scheme.roast_scheme_key = 'negative.round3b.missing_medium_dark';

SELECT pg_temp.expect_round3b_failure(
    'five_level_promotion',
    $$UPDATE context.roast_scheme SET is_project_normalized_target = TRUE
      WHERE roast_scheme_key = 'negative.round3b.five_level'$$,
    '23514', 'current_user_roast_scheme_contract_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'missing_medium_light_promotion',
    $$UPDATE context.roast_scheme SET is_project_normalized_target = TRUE
      WHERE roast_scheme_key = 'negative.round3b.missing_medium_light'$$,
    '23514', 'current_user_roast_scheme_contract_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'missing_medium_dark_promotion',
    $$UPDATE context.roast_scheme SET is_project_normalized_target = TRUE
      WHERE roast_scheme_key = 'negative.round3b.missing_medium_dark'$$,
    '23514', 'current_user_roast_scheme_contract_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'duplicate_current_ordinal',
    $$INSERT INTO context.roast_category (
          roast_category_key, roast_scheme_id, source_category_code,
          preferred_label, ordinal_position, lifecycle_status_code, description
      )
      SELECT 'negative.round3b.duplicate_ordinal', roast_scheme_id,
             'duplicate_ordinal', 'Duplicate ordinal', 4, 'candidate',
             'Negative fixture.'
      FROM context.roast_scheme
      WHERE roast_scheme_key = 'roast.scheme.project_v1_seven_level'$$,
    '23505', 'roast_category_scheme_ordinal_uq'
);

SELECT pg_temp.expect_round3b_failure(
    'unknown_c0_family',
    $$INSERT INTO context.preparation_concept (
          preparation_concept_key, preparation_concept_type_code,
          preferred_label, description, lifecycle_status_code,
          c0_top_level, c0_second_level
      ) VALUES (
          'preparation.family.unknown', 'family', 'Unknown',
          'Negative fixture.', 'candidate', TRUE, FALSE
      )$$,
    '23514', 'user_c0_unknown_family_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'espresso_roast_without_approval',
    $$UPDATE context.context_lexical_rule
      SET outcome_status_code = 'known',
          normalized_roast_category_id = (
              SELECT roast_category_id FROM context.roast_category
              WHERE roast_category_key = 'roast.project_v1.dark'
          ),
          review_decision_code = 'approved',
          mapping_grade = 'invented_negative_fixture'
      WHERE context_domain = 'roast'
        AND normalized_expression = 'espresso roast'$$,
    '23514', 'protected_roast_mapping_approval_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'city_plus_without_approval',
    $$UPDATE context.context_lexical_rule
      SET outcome_status_code = 'known',
          normalized_roast_category_id = (
              SELECT roast_category_id FROM context.roast_category
              WHERE roast_category_key = 'roast.project_v1.dark'
          ),
          review_decision_code = 'approved',
          mapping_grade = 'invented_negative_fixture'
      WHERE context_domain = 'roast'
        AND normalized_expression = 'city+'$$,
    '23514', 'protected_roast_mapping_approval_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'modify_historical_five_level_scheme',
    $$UPDATE context.roast_scheme SET name = 'Changed historical name'
      WHERE roast_scheme_key = 'roast.scheme.project_v0_five_level'$$,
    '23514', 'round3a_five_level_scheme_frozen_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'delete_historical_five_level_category',
    $$DELETE FROM context.roast_category
      WHERE roast_category_key = 'roast.project.medium'$$,
    '23514', 'round3a_five_level_category_frozen_ck'
);

SELECT pg_temp.expect_round3b_failure(
    'modify_frozen_raw_context_record',
    $$UPDATE context.raw_context_record SET raw_payload = raw_payload || '{"changed":true}'::jsonb
      WHERE raw_context_record_id = (
          SELECT min(raw_context_record_id) FROM context.raw_context_record
      )$$,
    '23514', 'frozen_raw_context_record_immutable_ck'
);

-- Unknown remains a valid database observation state even though it is not a
-- current user choice.
INSERT INTO context.observation_context (
    observation_context_key, captured_document_id,
    preparation_status_code, roast_status_code, addition_presence_code,
    context_assertion_role_code, evidence_locator
)
SELECT 'negative.round3b.unknown_observation_state',
       document.captured_document_id, 'unknown', 'unknown', 'not_reported',
       'source_reported', 'db/tests/round3b_negative.sql'
FROM corpus.captured_document AS document
WHERE NOT EXISTS (
    SELECT 1 FROM context.observation_context AS existing
    WHERE existing.captured_document_id = document.captured_document_id
)
ORDER BY document.captured_document_key
LIMIT 1;

DO $unknown_state_contract$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM context.observation_context
        WHERE observation_context_key =
              'negative.round3b.unknown_observation_state'
          AND preparation_status_code = 'unknown'
          AND roast_status_code = 'unknown'
    ) THEN
        RAISE EXCEPTION 'Database unknown observation state was not preserved';
    END IF;
END;
$unknown_state_contract$;

ROLLBACK;

\echo ROUND3B_NEGATIVE_TEST_PASS=true
