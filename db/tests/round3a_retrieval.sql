\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

\echo ROUND3A_PREPARATION_EXACT_LOOKUP
SELECT
    expression.expression_text,
    mapping.context_mapping_certainty_code,
    concept.preparation_concept_key,
    concept.preferred_label
FROM context.preparation_expression AS expression
JOIN context.preparation_expression_mapping AS mapping
  ON mapping.preparation_expression_id = expression.preparation_expression_id
 AND mapping.lifecycle_status_code = 'active'
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_id = mapping.preparation_concept_id
WHERE expression.language_tag_code = 'en'
  AND expression.normalized_text = 'aeropress';

\echo ROUND3A_PREPARATION_UNRESOLVED_LOOKUP
SELECT expression_key, expression_text
FROM context.v_unresolved_context_labels
WHERE context_domain = 'preparation'
ORDER BY expression_key;

\echo ROUND3A_PREPARATION_POLYHIERARCHY
SELECT preparation_concept_key, direct_parent_keys
FROM context.v_preparation_taxonomy
WHERE preparation_concept_key = 'preparation.method.aeropress';

\echo ROUND3A_ROAST_EXACT_PROJECT_LOOKUP
SELECT
    expression.expression_text,
    category.roast_category_key,
    category.ordinal_position,
    scheme.roast_scheme_key
FROM context.roast_expression AS expression
JOIN context.roast_expression_mapping AS mapping
  ON mapping.roast_expression_id = expression.roast_expression_id
 AND mapping.lifecycle_status_code = 'active'
JOIN context.roast_category AS category
  ON category.roast_category_id = mapping.roast_category_id
JOIN context.roast_scheme AS scheme
  ON scheme.roast_scheme_id = category.roast_scheme_id
WHERE expression.normalized_text = 'medium';

\echo ROUND3A_ROAST_SOURCE_SCHEME_MAPPING
SELECT
    source_roast_category_key,
    source_label,
    context_mapping_certainty_code,
    normalized_roast_category_key,
    normalized_label
FROM context.v_roast_normalization
WHERE source_roast_scheme_key = 'roast.scheme.common_three_level'
ORDER BY source_ordinal_position;

\echo ROUND3A_ROAST_UNRESOLVED_LOOKUP
SELECT expression_key, expression_text
FROM context.v_unresolved_context_labels
WHERE context_domain = 'roast'
ORDER BY expression_key;

DO $round3a_retrieval_contract$
BEGIN
    IF (SELECT count(*)
        FROM context.preparation_expression_mapping AS mapping
        JOIN context.preparation_expression AS expression
          ON expression.preparation_expression_id =
             mapping.preparation_expression_id
        WHERE expression.normalized_text = 'aeropress'
          AND mapping.lifecycle_status_code = 'active') <> 1
       OR (SELECT count(*)
           FROM context.v_unresolved_context_labels
           WHERE context_domain = 'preparation') <> 2
       OR (SELECT count(*)
           FROM context.v_unresolved_context_labels
           WHERE context_domain = 'roast') <> 13 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_context_resolution_contract_ck',
            MESSAGE = 'Context exact and unresolved lookup counts changed';
    END IF;
    RAISE NOTICE 'ROUND3A_RETRIEVAL_PASS=true';
END;
$round3a_retrieval_contract$;

ROLLBACK;

\echo ROUND3A_RETRIEVAL_TEST_PASS=true
