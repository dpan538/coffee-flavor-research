\set ON_ERROR_STOP on
\pset pager off

-- Natural plans record PostgreSQL's judgment for the deterministic ontology.
-- The assertion block disables sequential/bitmap scans transaction-locally to
-- prove each purpose-built Round 2A index is a valid executable access path.

BEGIN TRANSACTION READ ONLY;

\echo ROUND2A_QUERY_PLAN=exact_concept_lookup_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code
FROM kb.concept AS concept
WHERE concept.concept_key = 'sensory.grapefruit';

\echo ROUND2A_QUERY_PLAN=lexical_candidate_resolution_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT result.*
FROM kb.retrieve_lexical_candidates(
    'grapefruit',
    'en',
    5,
    0.35::REAL
) AS result;

\echo ROUND2A_QUERY_PLAN=canonical_broader_narrower_traversal_natural
EXPLAIN (ANALYZE, BUFFERS)
WITH RECURSIVE narrower_concepts (
    concept_id,
    depth,
    visited
) AS (
    SELECT
        relation.object_concept_id,
        1,
        ARRAY[
            relation.subject_concept_id,
            relation.object_concept_id
        ]::BIGINT[]
    FROM kb.concept_relation AS relation
    JOIN kb.concept AS root
      ON root.concept_id = relation.subject_concept_id
    WHERE root.concept_key = 'category.citrus'
      AND relation.relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'

    UNION ALL

    SELECT
        relation.object_concept_id,
        traversal.depth + 1,
        traversal.visited || relation.object_concept_id
    FROM narrower_concepts AS traversal
    JOIN kb.concept_relation AS relation
      ON relation.subject_concept_id = traversal.concept_id
     AND relation.relation_type_code = 'broader_than'
     AND relation.lifecycle_status_code = 'active'
    WHERE NOT relation.object_concept_id = ANY(traversal.visited)
)
SELECT concept.concept_key, min(traversal.depth) AS minimum_depth
FROM narrower_concepts AS traversal
JOIN kb.concept AS concept
  ON concept.concept_id = traversal.concept_id
GROUP BY concept.concept_id, concept.concept_key
ORDER BY minimum_depth, concept.concept_key;

\echo ROUND2A_QUERY_PLAN=canonical_neighbour_lookup_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    neighbour.neighbour_concept_key,
    neighbour.relation_type_code,
    neighbour.traversal_direction
FROM kb.v_concept_neighbours AS neighbour
WHERE neighbour.concept_key = 'composite.earl_grey'
ORDER BY
    neighbour.relation_type_code,
    neighbour.neighbour_concept_key;

\echo ROUND2A_QUERY_PLAN=project_multi_parent_traversal_natural
EXPLAIN (ANALYZE, BUFFERS)
WITH RECURSIVE parent_paths (
    concept_scheme_id,
    start_node_id,
    ancestor_node_id,
    depth,
    visited
) AS (
    SELECT
        hierarchy.concept_scheme_id,
        hierarchy.child_node_id,
        hierarchy.parent_node_id,
        1,
        ARRAY[
            hierarchy.child_node_id,
            hierarchy.parent_node_id
        ]::BIGINT[]
    FROM evidence.v_current_scheme_hierarchy AS hierarchy
    WHERE hierarchy.concept_scheme_key =
        'scheme.project.coffee_sensory_kb_v0.2026-08-24'

    UNION ALL

    SELECT
        path.concept_scheme_id,
        path.start_node_id,
        hierarchy.parent_node_id,
        path.depth + 1,
        path.visited || hierarchy.parent_node_id
    FROM parent_paths AS path
    JOIN evidence.v_current_scheme_hierarchy AS hierarchy
      ON hierarchy.concept_scheme_id = path.concept_scheme_id
     AND hierarchy.child_node_id = path.ancestor_node_id
    WHERE NOT hierarchy.parent_node_id = ANY(path.visited)
)
SELECT
    start_node.concept_scheme_node_key,
    count(DISTINCT path.ancestor_node_id) AS ancestor_count,
    max(path.depth) AS maximum_depth
FROM parent_paths AS path
JOIN evidence.concept_scheme_node AS start_node
  ON start_node.concept_scheme_id = path.concept_scheme_id
 AND start_node.concept_scheme_node_id = path.start_node_id
GROUP BY start_node.concept_scheme_node_id, start_node.concept_scheme_node_key
HAVING count(DISTINCT path.ancestor_node_id) > 1
ORDER BY start_node.concept_scheme_node_key;

\echo ROUND2A_QUERY_PLAN=source_scheme_projection_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    projection.concept_scheme_node_key,
    projection.source_node_key,
    projection.concept_key,
    projection.scheme_concept_mapping_role_code,
    projection.production_export_allowed
FROM kb.v_scheme_projection AS projection
WHERE projection.concept_scheme_key =
    'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
ORDER BY
    projection.concept_scheme_node_key,
    projection.concept_key NULLS LAST;

\echo ROUND2A_QUERY_PLAN=concept_provenance_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT support.concept_support_key, support.locator
FROM evidence.concept_support AS support
WHERE support.concept_id = (
    SELECT selected.concept_id
    FROM evidence.concept_support AS selected
    ORDER BY selected.concept_support_key
    LIMIT 1
)
  AND support.concept_support_role_code = (
    SELECT selected.concept_support_role_code
    FROM evidence.concept_support AS selected
    ORDER BY selected.concept_support_key
    LIMIT 1
);

\echo ROUND2A_QUERY_PLAN=active_scheme_source_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT scheme.concept_scheme_key, scheme.name
FROM evidence.concept_scheme AS scheme
WHERE scheme.lifecycle_status_code = 'active'
  AND scheme.source_version_id = (
      SELECT selected.source_version_id
      FROM evidence.concept_scheme AS selected
      ORDER BY selected.concept_scheme_key
      LIMIT 1
  );

\echo ROUND2A_QUERY_PLAN=scheme_reverse_edge_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT edge.concept_scheme_edge_key, edge.parent_node_id
FROM evidence.concept_scheme_edge AS edge
WHERE edge.lifecycle_status_code = 'active'
  AND (edge.concept_scheme_id, edge.child_node_id) = (
      SELECT
          selected.concept_scheme_id,
          selected.child_node_id
      FROM evidence.concept_scheme_edge AS selected
      WHERE selected.lifecycle_status_code = 'active'
      ORDER BY selected.concept_scheme_edge_key
      LIMIT 1
  );

\echo ROUND2A_QUERY_PLAN=scheme_mapping_by_concept_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    mapping.concept_scheme_mapping_key,
    mapping.concept_scheme_id,
    mapping.concept_scheme_node_id
FROM evidence.concept_scheme_mapping AS mapping
WHERE mapping.lifecycle_status_code = 'active'
  AND mapping.concept_id = (
      SELECT selected.concept_id
      FROM evidence.concept_scheme_mapping AS selected
      WHERE selected.lifecycle_status_code = 'active'
      ORDER BY selected.concept_scheme_mapping_key
      LIMIT 1
  );

DO $round2a_query_plan_assertions$
DECLARE
    support_concept_id BIGINT;
    support_role_code TEXT;
    scheme_source_version_id BIGINT;
    edge_scheme_id BIGINT;
    edge_child_node_id BIGINT;
    mapping_concept_id BIGINT;
    plan_document JSON;
    plan_text TEXT;
BEGIN
    SELECT support.concept_id, support.concept_support_role_code
    INTO STRICT support_concept_id, support_role_code
    FROM evidence.concept_support AS support
    ORDER BY support.concept_support_key
    LIMIT 1;

    SELECT scheme.source_version_id
    INTO STRICT scheme_source_version_id
    FROM evidence.concept_scheme AS scheme
    WHERE scheme.lifecycle_status_code = 'active'
    ORDER BY scheme.concept_scheme_key
    LIMIT 1;

    SELECT edge.concept_scheme_id, edge.child_node_id
    INTO STRICT edge_scheme_id, edge_child_node_id
    FROM evidence.concept_scheme_edge AS edge
    WHERE edge.lifecycle_status_code = 'active'
    ORDER BY edge.concept_scheme_edge_key
    LIMIT 1;

    SELECT mapping.concept_id
    INTO STRICT mapping_concept_id
    FROM evidence.concept_scheme_mapping AS mapping
    WHERE mapping.lifecycle_status_code = 'active'
    ORDER BY mapping.concept_scheme_mapping_key
    LIMIT 1;

    PERFORM pg_catalog.set_config('enable_seqscan', 'off', TRUE);
    PERFORM pg_catalog.set_config('enable_bitmapscan', 'off', TRUE);

    FOR plan_document IN EXECUTE format(
        'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
         SELECT concept_support_key, locator
         FROM evidence.concept_support
         WHERE concept_id = %L
           AND concept_support_role_code = %L',
        support_concept_id,
        support_role_code
    ) LOOP
        plan_text := plan_document::TEXT;
    END LOOP;
    RAISE NOTICE 'ROUND2A_FORCED_PROVENANCE_PLAN=%', plan_text;
    IF position('concept_support_concept_role_idx' IN plan_text) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_query_plan_concept_provenance_idx_ck',
            MESSAGE = 'concept provenance plan did not use concept_support_concept_role_idx';
    END IF;

    FOR plan_document IN EXECUTE format(
        'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
         SELECT concept_scheme_key, name
         FROM evidence.concept_scheme
         WHERE lifecycle_status_code = ''active''
           AND source_version_id = %L',
        scheme_source_version_id
    ) LOOP
        plan_text := plan_document::TEXT;
    END LOOP;
    RAISE NOTICE 'ROUND2A_FORCED_SCHEME_SOURCE_PLAN=%', plan_text;
    IF position('concept_scheme_active_source_version_idx' IN plan_text) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_query_plan_scheme_source_idx_ck',
            MESSAGE = 'active scheme source plan did not use concept_scheme_active_source_version_idx';
    END IF;

    FOR plan_document IN EXECUTE format(
        'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
         SELECT concept_scheme_edge_key, parent_node_id
         FROM evidence.concept_scheme_edge
         WHERE lifecycle_status_code = ''active''
           AND concept_scheme_id = %L
           AND child_node_id = %L',
        edge_scheme_id,
        edge_child_node_id
    ) LOOP
        plan_text := plan_document::TEXT;
    END LOOP;
    RAISE NOTICE 'ROUND2A_FORCED_REVERSE_EDGE_PLAN=%', plan_text;
    IF position('concept_scheme_edge_active_child_idx' IN plan_text) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_query_plan_scheme_reverse_edge_idx_ck',
            MESSAGE = 'reverse hierarchy plan did not use concept_scheme_edge_active_child_idx';
    END IF;

    FOR plan_document IN EXECUTE format(
        'EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
         SELECT concept_scheme_mapping_key,
                concept_scheme_id,
                concept_scheme_node_id
         FROM evidence.concept_scheme_mapping
         WHERE lifecycle_status_code = ''active''
           AND concept_id = %L',
        mapping_concept_id
    ) LOOP
        plan_text := plan_document::TEXT;
    END LOOP;
    RAISE NOTICE 'ROUND2A_FORCED_MAPPING_PLAN=%', plan_text;
    IF position('concept_scheme_mapping_active_concept_idx' IN plan_text) = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_query_plan_scheme_mapping_idx_ck',
            MESSAGE = 'concept-to-scheme mapping plan did not use concept_scheme_mapping_active_concept_idx';
    END IF;

    RAISE NOTICE 'ROUND2A_QUERY_PLAN_PASS=true';
END
$round2a_query_plan_assertions$;

COMMIT;

\echo ROUND2A_QUERY_PLAN_PASS=true
