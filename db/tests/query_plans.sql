\set ON_ERROR_STOP on
\pset pager off

-- The lawful seed is intentionally tiny, so both natural plans and forced
-- index-eligible plans are recorded.  Natural plans describe current planner
-- judgment; the local planner settings in the assertion block prove that the
-- intended GiST KNN and active-edge paths are usable without changing schema
-- or production settings.

BEGIN TRANSACTION READ ONLY;

\echo QUERY_PLAN=trigram_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    expression.expression_key,
    expression.normalized_text,
    public.similarity(expression.normalized_text, 'grapfruit')
        AS lexical_similarity
FROM kb.lexical_expression AS expression
WHERE expression.lifecycle_status_code = 'active'
  AND expression.language_tag_code = 'en'
ORDER BY
    expression.normalized_text OPERATOR(public.<->) 'grapfruit',
    expression.expression_key
LIMIT 5;

\echo QUERY_PLAN=graph_subject_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    relation.relation_key,
    relation.relation_type_code,
    relation.object_concept_id
FROM kb.concept_relation AS relation
WHERE relation.lifecycle_status_code = 'active'
  AND relation.subject_concept_id = (
      SELECT concept.concept_id
      FROM kb.concept AS concept
      WHERE concept.concept_key = 'composite.earl_grey'
  )
  AND relation.relation_type_code IN (
      'consumer_reference_for',
      'composite_has_component'
  );

\echo QUERY_PLAN=graph_object_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    relation.relation_key,
    relation.relation_type_code,
    relation.subject_concept_id
FROM kb.concept_relation AS relation
WHERE relation.lifecycle_status_code = 'active'
  AND relation.object_concept_id = (
      SELECT concept.concept_id
      FROM kb.concept AS concept
      WHERE concept.concept_key = 'sensory.bergamot'
  )
  AND relation.relation_type_code = 'consumer_reference_for';

DO $query_plan_assertions$
DECLARE
    plan_document JSON;
    plan_text TEXT;
BEGIN
    -- A tiny seed can legitimately prefer a sequential or bitmap path. These
    -- transaction-local settings make the access-path proof deterministic and
    -- do not leak into the database or application configuration.
    PERFORM pg_catalog.set_config('enable_seqscan', 'off', TRUE);
    PERFORM pg_catalog.set_config('enable_bitmapscan', 'off', TRUE);

    FOR plan_document IN EXECUTE $plan$
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT
            expression.expression_key,
            expression.normalized_text,
            public.similarity(expression.normalized_text, 'grapfruit')
                AS lexical_similarity
        FROM kb.lexical_expression AS expression
        WHERE expression.lifecycle_status_code = 'active'
          AND expression.language_tag_code = 'en'
        ORDER BY
            expression.normalized_text OPERATOR(public.<->) 'grapfruit',
            expression.expression_key
        LIMIT 5
    $plan$ LOOP
        plan_text := plan_document::TEXT;
    END LOOP;

    RAISE NOTICE 'FORCED_TRIGRAM_PLAN=%', plan_text;

    IF position(
        'lexical_expression_normalized_trgm_gist_idx' IN plan_text
    ) = 0 OR position('Order By' IN plan_text) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'query_plan_trigram_gist_knn_ck',
            MESSAGE = 'query-plan smoke: trigram KNN plan did not use lexical_expression_normalized_trgm_gist_idx with index ordering';
    END IF;

    FOR plan_document IN EXECUTE $plan$
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT
            relation.relation_key,
            relation.relation_type_code,
            relation.object_concept_id
        FROM kb.concept_relation AS relation
        WHERE relation.lifecycle_status_code = 'active'
          AND relation.subject_concept_id = (
              SELECT concept.concept_id
              FROM kb.concept AS concept
              WHERE concept.concept_key = 'composite.earl_grey'
          )
          AND relation.relation_type_code IN (
              'consumer_reference_for',
              'composite_has_component'
          )
    $plan$ LOOP
        plan_text := plan_document::TEXT;
    END LOOP;

    RAISE NOTICE 'FORCED_GRAPH_SUBJECT_PLAN=%', plan_text;

    IF position(
        'concept_relation_active_subject_type_idx' IN plan_text
    ) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'query_plan_graph_subject_index_ck',
            MESSAGE = 'query-plan smoke: outgoing graph plan did not use concept_relation_active_subject_type_idx';
    END IF;

    FOR plan_document IN EXECUTE $plan$
        EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
        SELECT
            relation.relation_key,
            relation.relation_type_code,
            relation.subject_concept_id
        FROM kb.concept_relation AS relation
        WHERE relation.lifecycle_status_code = 'active'
          AND relation.object_concept_id = (
              SELECT concept.concept_id
              FROM kb.concept AS concept
              WHERE concept.concept_key = 'sensory.bergamot'
          )
          AND relation.relation_type_code = 'consumer_reference_for'
    $plan$ LOOP
        plan_text := plan_document::TEXT;
    END LOOP;

    RAISE NOTICE 'FORCED_GRAPH_OBJECT_PLAN=%', plan_text;

    IF position(
        'concept_relation_active_object_type_idx' IN plan_text
    ) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'query_plan_graph_object_index_ck',
            MESSAGE = 'query-plan smoke: incoming graph plan did not use concept_relation_active_object_type_idx';
    END IF;

    RAISE NOTICE 'QUERY_PLAN_PASS=true';
END
$query_plan_assertions$;

COMMIT;

\echo QUERY_PLAN_PASS=true
