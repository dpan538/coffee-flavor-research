\set ON_ERROR_STOP on
\pset pager off

BEGIN;

DO $round3a_query_plan_index_contract$
BEGIN
    IF to_regclass('context.preparation_relation_object_type_idx') IS NULL
       OR to_regclass('context.preparation_expression_normalized_uq') IS NULL
       OR to_regclass('context.roast_category_scheme_idx') IS NULL
       OR to_regclass('context.roast_expression_normalized_uq') IS NULL
       OR to_regclass('context.observation_context_preparation_idx') IS NULL
       OR to_regclass('context.observation_context_roast_idx') IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_query_plan_index_contract_ck',
            MESSAGE = 'A required Round 3A context lookup, hierarchy, or observation index is missing';
    END IF;
    RAISE NOTICE 'ROUND3A_QUERY_PLAN_INDEX_CONTRACT_PASS=true';
END;
$round3a_query_plan_index_contract$;

\echo ROUND3A_QUERY_PLAN=preparation_exact_lookup
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    expression.preparation_expression_key,
    mapping.context_mapping_certainty_code,
    concept.preparation_concept_key
FROM context.preparation_expression AS expression
JOIN context.preparation_expression_mapping AS mapping
  ON mapping.preparation_expression_id = expression.preparation_expression_id
 AND mapping.lifecycle_status_code = 'active'
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_id = mapping.preparation_concept_id
WHERE expression.language_tag_code = 'en'
  AND expression.normalized_text = 'aeropress';

\echo ROUND3A_QUERY_PLAN=preparation_broader_traversal
EXPLAIN (ANALYZE, BUFFERS)
WITH RECURSIVE ancestors(preparation_concept_id, depth) AS (
    SELECT concept.preparation_concept_id, 0
    FROM context.preparation_concept AS concept
    WHERE concept.preparation_concept_key = 'preparation.method.aeropress'
    UNION ALL
    SELECT relation.subject_preparation_concept_id, ancestors.depth + 1
    FROM ancestors
    JOIN context.preparation_relation AS relation
      ON relation.object_preparation_concept_id =
         ancestors.preparation_concept_id
    WHERE relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'
)
SELECT concept.preparation_concept_key, ancestors.depth
FROM ancestors
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_id = ancestors.preparation_concept_id
ORDER BY ancestors.depth, concept.preparation_concept_key;

\echo ROUND3A_QUERY_PLAN=preparation_narrower_traversal
EXPLAIN (ANALYZE, BUFFERS)
WITH RECURSIVE descendants(preparation_concept_id, depth) AS (
    SELECT concept.preparation_concept_id, 0
    FROM context.preparation_concept AS concept
    WHERE concept.preparation_concept_key = 'preparation.family.espresso_milk'
    UNION ALL
    SELECT relation.object_preparation_concept_id, descendants.depth + 1
    FROM descendants
    JOIN context.preparation_relation AS relation
      ON relation.subject_preparation_concept_id =
         descendants.preparation_concept_id
    WHERE relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'
)
SELECT concept.preparation_concept_key, descendants.depth
FROM descendants
JOIN context.preparation_concept AS concept
  ON concept.preparation_concept_id = descendants.preparation_concept_id
ORDER BY descendants.depth, concept.preparation_concept_key;

\echo ROUND3A_QUERY_PLAN=preparation_provenance
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    concept.preparation_concept_key,
    support.context_assertion_role_code,
    source_version.source_version_key,
    source.source_key,
    policy.production_export_allowed
FROM context.preparation_concept AS concept
JOIN context.preparation_concept_support AS support
  ON support.preparation_concept_id = concept.preparation_concept_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = support.source_version_id
JOIN evidence.source AS source ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS policy
  ON policy.license_policy_id = source_version.license_policy_id
WHERE concept.preparation_concept_key = 'preparation.family.espresso_milk'
ORDER BY source_version.source_version_key;

\echo ROUND3A_QUERY_PLAN=roast_source_scheme_projection
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM context.v_roast_normalization
WHERE source_roast_scheme_key = 'roast.scheme.common_three_level'
ORDER BY source_ordinal_position;

\echo ROUND3A_QUERY_PLAN=unresolved_context_queue
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM context.v_unresolved_context_labels
ORDER BY context_domain, normalized_text;

\echo ROUND3A_QUERY_PLAN=current_context_coverage
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM context.v_context_coverage ORDER BY metric_key;

ROLLBACK;

\echo ROUND3A_QUERY_PLAN_PASS=true
