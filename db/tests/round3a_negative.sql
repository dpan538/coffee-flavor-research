\set ON_ERROR_STOP on
\pset pager off

-- Round 3A failure-path tests. Fixtures are transaction-local and must fail
-- with the declared PostgreSQL diagnostic; no historical corpus row survives.

BEGIN;

CREATE FUNCTION pg_temp.expect_round3a_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3a_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3A negative statement unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR expected_constraint IS NOT NULL
              AND actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND3A_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, COALESCE(actual_constraint, '<none>');
    END;
END;
$expect_round3a_failure$;

SELECT pg_temp.expect_round3a_failure(
    'preparation_cycle',
    $sql$
        INSERT INTO context.preparation_relation (
            preparation_relation_key,
            subject_preparation_concept_id,
            context_relation_type_code,
            object_preparation_concept_id,
            source_version_id,
            context_assertion_role_code,
            evidence_locator,
            lifecycle_status_code
        )
        SELECT
            'negative.round3a.preparation_cycle',
            aeropress.preparation_concept_id,
            'broader_than',
            hybrid.preparation_concept_id,
            source_version.source_version_id,
            'project_authored',
            'db/tests/round3a_negative.sql',
            'active'
        FROM context.preparation_concept AS aeropress
        CROSS JOIN context.preparation_concept AS hybrid
        CROSS JOIN evidence.source_version AS source_version
        WHERE aeropress.preparation_concept_key = 'preparation.method.aeropress'
          AND hybrid.preparation_concept_key = 'preparation.family.hybrid'
          AND source_version.source_version_key =
              'source_version.project.context_v0.2026-08-25'
    $sql$,
    '23514',
    'preparation_relation_acyclic_ck'
);

SELECT pg_temp.expect_round3a_failure(
    'preparation_self_relation',
    $sql$
        INSERT INTO context.preparation_relation (
            preparation_relation_key,
            subject_preparation_concept_id,
            context_relation_type_code,
            object_preparation_concept_id,
            source_version_id,
            context_assertion_role_code,
            evidence_locator,
            lifecycle_status_code
        )
        SELECT
            'negative.round3a.preparation_self',
            concept.preparation_concept_id,
            'broader_than',
            concept.preparation_concept_id,
            source_version.source_version_id,
            'project_authored',
            'db/tests/round3a_negative.sql',
            'active'
        FROM context.preparation_concept AS concept
        CROSS JOIN evidence.source_version AS source_version
        WHERE concept.preparation_concept_key = 'preparation.method.aeropress'
          AND source_version.source_version_key =
              'source_version.project.context_v0.2026-08-25'
    $sql$,
    '23514',
    'preparation_relation_no_self_ck'
);

SELECT pg_temp.expect_round3a_failure(
    'conflicting_exact_preparation_mapping',
    $sql$
        INSERT INTO context.preparation_expression_mapping (
            preparation_expression_mapping_key,
            preparation_expression_id,
            preparation_concept_id,
            context_mapping_certainty_code,
            source_version_id,
            context_assertion_role_code,
            evidence_locator,
            lifecycle_status_code
        )
        SELECT
            'negative.round3a.conflicting_exact_mapping',
            expression.preparation_expression_id,
            target.preparation_concept_id,
            'exact_project_label',
            source_version.source_version_id,
            'lexical_mapping',
            'db/tests/round3a_negative.sql',
            'active'
        FROM context.preparation_expression AS expression
        CROSS JOIN context.preparation_concept AS target
        CROSS JOIN evidence.source_version AS source_version
        WHERE expression.normalized_text = 'americano'
          AND target.preparation_concept_key = 'preparation.beverage.long_black'
          AND source_version.source_version_key =
              'source_version.project.context_v0.2026-08-25'
    $sql$,
    '23514',
    'context_expression_mapping_ambiguity_ck'
);

SELECT pg_temp.expect_round3a_failure(
    'terminology_scheme_ordinal',
    $sql$
        INSERT INTO context.roast_category (
            roast_category_key, roast_scheme_id, source_category_code,
            preferred_label, ordinal_position, lifecycle_status_code,
            description
        )
        SELECT
            'negative.round3a.invented_trade_ordinal',
            roast_scheme_id,
            'invented_trade_ordinal',
            'Invented trade ordinal',
            99,
            'candidate',
            'Negative fixture.'
        FROM context.roast_scheme
        WHERE roast_scheme_key = 'roast.scheme.traditional_trade_labels'
    $sql$,
    '23514',
    'roast_category_scheme_ordinal_ck'
);

SELECT pg_temp.expect_round3a_failure(
    'roast_mapping_nonproject_target',
    $sql$
        INSERT INTO context.roast_category_mapping (
            roast_category_mapping_key,
            source_roast_category_id,
            normalized_roast_category_id,
            context_mapping_certainty_code,
            source_version_id,
            context_assertion_role_code,
            evidence_locator,
            lifecycle_status_code
        )
        SELECT
            'negative.round3a.nonproject_roast_target',
            source_category.roast_category_id,
            target_category.roast_category_id,
            'approximate',
            source_version.source_version_id,
            'interpretive',
            'db/tests/round3a_negative.sql',
            'active'
        FROM context.roast_category AS source_category
        CROSS JOIN context.roast_category AS target_category
        CROSS JOIN evidence.source_version AS source_version
        WHERE source_category.roast_category_key = 'roast.trade.city'
          AND target_category.roast_category_key = 'roast.common.light'
          AND source_version.source_version_key =
              'source_version.project.context_v0.2026-08-25'
    $sql$,
    '23514',
    'roast_category_mapping_target_ck'
);

SELECT pg_temp.expect_round3a_failure(
    'known_preparation_without_value',
    $sql$
        INSERT INTO context.observation_context (
            observation_context_key, captured_document_id,
            preparation_status_code, roast_status_code,
            addition_presence_code, context_assertion_role_code,
            evidence_locator
        )
        SELECT
            'negative.round3a.known_without_preparation',
            document.captured_document_id,
            'known', 'not_reported', 'not_reported',
            'source_reported', 'db/tests/round3a_negative.sql'
        FROM corpus.captured_document AS document
        ORDER BY document.captured_document_key
        LIMIT 1
    $sql$,
    '23514',
    'observation_context_preparation_value_ck'
);

INSERT INTO context.observation_context (
    observation_context_key, captured_document_id,
    preparation_status_code, roast_status_code,
    addition_presence_code, context_assertion_role_code,
    evidence_locator
)
SELECT
    'negative.round3a.fixture_context',
    document.captured_document_id,
    'not_reported', 'not_reported', 'absent',
    'source_reported', 'db/tests/round3a_negative.sql'
FROM corpus.captured_document AS document
ORDER BY document.captured_document_key
LIMIT 1;

SELECT pg_temp.expect_round3a_failure(
    'addition_row_when_absent',
    $sql$
        INSERT INTO context.observation_addition (
            observation_addition_key, observation_context_id,
            beverage_addition_type_id, reported_label
        )
        SELECT
            'negative.round3a.addition_when_absent',
            observation_context.observation_context_id,
            addition_type.beverage_addition_type_id,
            'vanilla syrup'
        FROM context.observation_context AS observation_context
        CROSS JOIN context.beverage_addition_type AS addition_type
        WHERE observation_context.observation_context_key =
              'negative.round3a.fixture_context'
          AND addition_type.beverage_addition_type_key =
              'addition.flavored_syrup'
    $sql$,
    '23514',
    'observation_addition_presence_ck'
);

SELECT pg_temp.expect_round3a_failure(
    'roast_measurement_out_of_bounds',
    $sql$
        INSERT INTO context.observation_roast_measurement (
            observation_roast_measurement_key,
            observation_context_id,
            roast_measurement_method_id,
            measured_value,
            source_version_id,
            evidence_locator
        )
        SELECT
            'negative.round3a.measurement_out_of_bounds',
            observation_context.observation_context_id,
            method.roast_measurement_method_id,
            151,
            source_version.source_version_id,
            'db/tests/round3a_negative.sql'
        FROM context.observation_context AS observation_context
        CROSS JOIN context.roast_measurement_method AS method
        CROSS JOIN evidence.source_version AS source_version
        WHERE observation_context.observation_context_key =
              'negative.round3a.fixture_context'
          AND method.roast_measurement_method_key =
              'roast_measurement.agtron_gourmet.ground'
          AND source_version.source_version_key =
              'source_version.project.context_v0.2026-08-25'
    $sql$,
    '23514',
    'observation_roast_measurement_bounds_ck'
);

-- A dedicated disposable source/version proves historical context support
-- closes source deletion with ON DELETE RESTRICT.
INSERT INTO evidence.source (
    source_key, title, citation, external_metadata
)
VALUES (
    'negative.round3a.source', 'Negative Round 3A source',
    'Transaction-local source.', '{}'::JSONB
);

INSERT INTO evidence.source_version (
    source_version_key, source_id, license_policy_id, version_label,
    retrieved_on, version_locator, external_metadata
)
SELECT
    'negative.round3a.source_version', source.source_id,
    policy.license_policy_id, 'Negative version', DATE '2026-08-25',
    'db/tests/round3a_negative.sql', '{}'::JSONB
FROM evidence.source AS source
CROSS JOIN evidence.license_policy AS policy
WHERE source.source_key = 'negative.round3a.source'
  AND policy.license_policy_key = 'license.project_context.cc_by_4_0.v1';

INSERT INTO context.preparation_concept_support (
    preparation_concept_support_key, preparation_concept_id,
    source_version_id, context_assertion_role_code, evidence_locator
)
SELECT
    'negative.round3a.source_support', concept.preparation_concept_id,
    source_version.source_version_id, 'corroboration',
    'db/tests/round3a_negative.sql'
FROM context.preparation_concept AS concept
CROSS JOIN evidence.source_version AS source_version
WHERE concept.preparation_concept_key = 'preparation.method.aeropress'
  AND source_version.source_version_key = 'negative.round3a.source_version';

SELECT pg_temp.expect_round3a_failure(
    'context_source_deletion_restricted',
    $sql$
        DELETE FROM evidence.source_version
        WHERE source_version_key = 'negative.round3a.source_version'
    $sql$,
    '23503',
    'preparation_concept_support_source_fk'
);

ROLLBACK;

\echo ROUND3A_NEGATIVE_TEST_PASS=true
