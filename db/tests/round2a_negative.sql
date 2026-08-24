\set ON_ERROR_STOP on
\pset pager off

-- Round 2A failure-path tests. Each inner block must fail with PostgreSQL's
-- exact SQLSTATE and diagnostic constraint, then rolls back its own mutation.

BEGIN;

DO $source_delete_restrict$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        DELETE FROM evidence.source AS source
        WHERE source.source_id = (
            SELECT scheme_source.source_id
            FROM evidence.concept_scheme AS scheme
            JOIN evidence.source_version AS source_version
              ON source_version.source_version_id = scheme.source_version_id
            JOIN evidence.source AS scheme_source
              ON scheme_source.source_id = source_version.source_id
            ORDER BY scheme.concept_scheme_key
            LIMIT 1
        );
        RAISE EXCEPTION 'versioned scheme source was unexpectedly deletable';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23503'
           OR actual_constraint IS DISTINCT FROM 'source_version_source_fk' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=source_delete_restrict SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$source_delete_restrict$;

DO $scheme_source_version_delete_restrict$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
    disposable_source_version_id BIGINT;
BEGIN
    BEGIN
        INSERT INTO evidence.source_version (
            source_version_key,
            source_id,
            license_policy_id,
            version_label,
            published_on,
            retrieved_on,
            version_locator,
            external_metadata
        )
        SELECT
            'negative.round2a.scheme_source_version',
            source_version.source_id,
            source_version.license_policy_id,
            'Negative Round 2A scheme source version',
            DATE '2026-08-24',
            DATE '2026-08-24',
            'db/tests/round2a_negative.sql',
            '{"negative_test":true}'::JSONB
        FROM evidence.source_version AS source_version
        ORDER BY source_version.source_version_key
        LIMIT 1
        RETURNING source_version_id INTO STRICT disposable_source_version_id;

        INSERT INTO evidence.concept_scheme (
            concept_scheme_key,
            source_version_id,
            lifecycle_status_code,
            name,
            description,
            valid_from,
            valid_until,
            metadata
        )
        VALUES (
            'negative.round2a.scheme_source_version',
            disposable_source_version_id,
            'candidate',
            'Negative source-version delete fixture',
            'A transaction-local fixture proving source-version deletion is restricted.',
            TIMESTAMPTZ '2026-08-24 00:00:00+00',
            NULL,
            '{"negative_test":true}'::JSONB
        );

        DELETE FROM evidence.source_version AS source_version
        WHERE source_version.source_version_id = disposable_source_version_id;
        RAISE EXCEPTION 'scheme source version was unexpectedly deletable';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23503'
           OR actual_constraint IS DISTINCT FROM
                'concept_scheme_source_version_fk' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=scheme_source_version_delete_restrict SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$scheme_source_version_delete_restrict$;

DO $scheme_source_version_immutable$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        UPDATE evidence.concept_scheme AS scheme
        SET source_version_id = (
            SELECT source_version.source_version_id
            FROM evidence.source_version AS source_version
            WHERE source_version.source_version_id <> scheme.source_version_id
            ORDER BY source_version.source_version_key
            LIMIT 1
        )
        WHERE scheme.concept_scheme_id = (
            SELECT selected.concept_scheme_id
            FROM evidence.concept_scheme AS selected
            ORDER BY selected.concept_scheme_key
            LIMIT 1
        );
        RAISE EXCEPTION 'concept scheme source version was unexpectedly mutable';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_scheme_source_version_immutable_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=scheme_source_version_immutable SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$scheme_source_version_immutable$;

DO $cross_scheme_edge$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO evidence.concept_scheme_edge (
            concept_scheme_edge_key,
            concept_scheme_id,
            parent_node_id,
            child_node_id,
            lifecycle_status_code,
            valid_from,
            valid_until,
            notes
        )
        SELECT
            'negative.round2a.cross_scheme_edge',
            first_scheme.concept_scheme_id,
            first_node.concept_scheme_node_id,
            second_node.concept_scheme_node_id,
            'active',
            TIMESTAMPTZ '2026-08-24 00:00:00+00',
            NULL,
            'Negative test: source-scheme nodes cannot cross provenance boundaries.'
        FROM (
            SELECT scheme.concept_scheme_id
            FROM evidence.concept_scheme AS scheme
            ORDER BY scheme.concept_scheme_key
            LIMIT 1
        ) AS first_scheme
        JOIN LATERAL (
            SELECT node.concept_scheme_node_id
            FROM evidence.concept_scheme_node AS node
            WHERE node.concept_scheme_id = first_scheme.concept_scheme_id
            ORDER BY node.concept_scheme_node_key
            LIMIT 1
        ) AS first_node ON TRUE
        JOIN LATERAL (
            SELECT node.concept_scheme_node_id
            FROM evidence.concept_scheme_node AS node
            WHERE node.concept_scheme_id <> first_scheme.concept_scheme_id
            ORDER BY node.concept_scheme_node_key
            LIMIT 1
        ) AS second_node ON TRUE;
        RAISE EXCEPTION 'cross-scheme hierarchy edge was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23503'
           OR actual_constraint IS DISTINCT FROM 'concept_scheme_edge_child_fk' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=cross_scheme_edge SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$cross_scheme_edge$;

DO $cross_scheme_mapping$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO evidence.concept_scheme_mapping (
            concept_scheme_mapping_key,
            concept_scheme_id,
            concept_scheme_node_id,
            concept_id,
            scheme_concept_mapping_role_code,
            lifecycle_status_code,
            valid_from,
            valid_until,
            notes
        )
        SELECT
            'negative.round2a.cross_scheme_mapping',
            first_scheme.concept_scheme_id,
            second_node.concept_scheme_node_id,
            concept.concept_id,
            'associated_with_concept',
            'active',
            TIMESTAMPTZ '2026-08-24 00:00:00+00',
            NULL,
            'Negative test: mapping node must belong to the named source scheme.'
        FROM (
            SELECT scheme.concept_scheme_id
            FROM evidence.concept_scheme AS scheme
            ORDER BY scheme.concept_scheme_key
            LIMIT 1
        ) AS first_scheme
        JOIN LATERAL (
            SELECT node.concept_scheme_node_id
            FROM evidence.concept_scheme_node AS node
            WHERE node.concept_scheme_id <> first_scheme.concept_scheme_id
            ORDER BY node.concept_scheme_node_key
            LIMIT 1
        ) AS second_node ON TRUE
        CROSS JOIN LATERAL (
            SELECT active_concept.concept_id
            FROM kb.concept AS active_concept
            WHERE active_concept.lifecycle_status_code = 'active'
            ORDER BY active_concept.concept_key
            LIMIT 1
        ) AS concept;
        RAISE EXCEPTION 'cross-scheme concept mapping was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23503'
           OR actual_constraint IS DISTINCT FROM 'concept_scheme_mapping_node_fk' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=cross_scheme_mapping SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$cross_scheme_mapping$;

DO $direct_scheme_cycle$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO evidence.concept_scheme_edge (
            concept_scheme_edge_key,
            concept_scheme_id,
            parent_node_id,
            child_node_id,
            lifecycle_status_code,
            valid_from,
            valid_until,
            notes
        )
        SELECT
            'negative.round2a.direct_scheme_cycle',
            hierarchy.concept_scheme_id,
            hierarchy.child_node_id,
            hierarchy.parent_node_id,
            'active',
            TIMESTAMPTZ '2026-08-24 00:00:00+00',
            NULL,
            'Negative test: inverse of an active edge creates a direct cycle.'
        FROM evidence.v_current_scheme_hierarchy AS hierarchy
        ORDER BY hierarchy.concept_scheme_key, hierarchy.concept_scheme_edge_key
        LIMIT 1;
        RAISE EXCEPTION 'direct source-scheme cycle was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_scheme_hierarchy_cycle_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=direct_scheme_cycle SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$direct_scheme_cycle$;

DO $indirect_scheme_cycle$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO evidence.concept_scheme_edge (
            concept_scheme_edge_key,
            concept_scheme_id,
            parent_node_id,
            child_node_id,
            lifecycle_status_code,
            valid_from,
            valid_until,
            notes
        )
        WITH RECURSIVE paths (
            concept_scheme_id,
            ancestor_node_id,
            descendant_node_id,
            depth,
            visited
        ) AS (
            SELECT
                hierarchy.concept_scheme_id,
                hierarchy.parent_node_id,
                hierarchy.child_node_id,
                1,
                ARRAY[
                    hierarchy.parent_node_id,
                    hierarchy.child_node_id
                ]::BIGINT[]
            FROM evidence.v_current_scheme_hierarchy AS hierarchy

            UNION ALL

            SELECT
                paths.concept_scheme_id,
                paths.ancestor_node_id,
                hierarchy.child_node_id,
                paths.depth + 1,
                paths.visited || hierarchy.child_node_id
            FROM paths
            JOIN evidence.v_current_scheme_hierarchy AS hierarchy
              ON hierarchy.concept_scheme_id = paths.concept_scheme_id
             AND hierarchy.parent_node_id = paths.descendant_node_id
            WHERE NOT hierarchy.child_node_id = ANY(paths.visited)
        )
        SELECT
            'negative.round2a.indirect_scheme_cycle',
            path.concept_scheme_id,
            path.descendant_node_id,
            path.ancestor_node_id,
            'active',
            TIMESTAMPTZ '2026-08-24 00:00:00+00',
            NULL,
            'Negative test: descendant-to-ancestor edge creates an indirect cycle.'
        FROM paths AS path
        WHERE path.depth >= 2
        ORDER BY path.depth, path.concept_scheme_id, path.ancestor_node_id
        LIMIT 1;
        RAISE EXCEPTION 'indirect source-scheme cycle was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_scheme_hierarchy_cycle_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2A_NEGATIVE=indirect_scheme_cycle SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$indirect_scheme_cycle$;

ROLLBACK;

\echo ROUND2A_NEGATIVE_PASS=true
