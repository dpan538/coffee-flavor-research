\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- Round 2A governed read models and
-- machine-runnable validation. Source-local schemes remain evidence artifacts;
-- none of these views converts a scheme node or edge into canonical knowledge.

BEGIN;

-- One row per active sensory concept. Label cardinality is exposed rather
-- than hidden so publication-readiness failures remain auditable. No score,
-- intensity, vector, or empirical coordinate is projected onto the concept.
CREATE VIEW kb.v_active_sensory_core AS
SELECT
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code,
    concept.provenance_scope_code,
    concept.description,
    concept.editorial_note,
    COALESCE(labels.preferred_english_label_count, 0::BIGINT)
        AS preferred_english_label_count,
    labels.preferred_expression_key,
    labels.preferred_english_label,
    COALESCE(labels.preferred_english_labels, '[]'::JSONB)
        AS preferred_english_labels
FROM kb.concept AS concept
LEFT JOIN LATERAL (
    SELECT
        count(*)::BIGINT AS preferred_english_label_count,
        min(expression.expression_key) AS preferred_expression_key,
        min(expression.expression_text) AS preferred_english_label,
        jsonb_agg(
            jsonb_build_object(
                'expression_key', expression.expression_key,
                'label', expression.expression_text
            )
            ORDER BY expression.normalized_text, expression.expression_key
        ) AS preferred_english_labels
    FROM kb.lexicalization AS lexicalization
    JOIN ref.mapping_type AS mapping_type
      ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
     AND mapping_type.is_preferred
    JOIN kb.lexical_expression AS expression
      ON expression.expression_id = lexicalization.expression_id
     AND expression.lifecycle_status_code = 'active'
     AND expression.language_tag_code = 'en'
    WHERE lexicalization.concept_id = concept.concept_id
      AND lexicalization.lifecycle_status_code = 'active'
      AND lexicalization.valid_from <= CURRENT_TIMESTAMP
      AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
          )
) AS labels ON TRUE
WHERE concept.concept_type_code = 'sensory_attribute'
  AND concept.lifecycle_status_code = 'active';

COMMENT ON VIEW kb.v_active_sensory_core IS
    'One row per active sensory concept with its auditable preferred-English-label cardinality; no intrinsic score, vector, desirability, or source-scheme ownership is implied.';

-- Node-complete projection: every current active scheme node is retained even
-- when it has no reviewed canonical mapping. A node with multiple reviewed
-- mappings produces multiple rows. Source labels remain governed by the
-- explicit licence columns; query visibility is not export permission.
CREATE VIEW kb.v_scheme_projection AS
SELECT
    scheme.concept_scheme_id,
    scheme.concept_scheme_key,
    scheme.name AS concept_scheme_name,
    source_version.source_version_id,
    source_version.source_version_key,
    source.source_id,
    source.source_key,
    license_policy.license_policy_id,
    license_policy.license_policy_key,
    license_policy.access_class_code,
    license_policy.rights_status_code,
    license_policy.production_export_allowed,
    node.concept_scheme_node_id,
    node.concept_scheme_node_key,
    node.source_node_key,
    node.source_label,
    node.valid_from AS node_valid_from,
    node.valid_until AS node_valid_until,
    mapping.concept_scheme_mapping_id,
    mapping.concept_scheme_mapping_key,
    mapping.scheme_concept_mapping_role_code,
    mapping.valid_from AS mapping_valid_from,
    mapping.valid_until AS mapping_valid_until,
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code AS concept_lifecycle_status_code,
    (mapping.concept_scheme_mapping_id IS NOT NULL) AS is_mapped
FROM evidence.concept_scheme_node AS node
JOIN evidence.concept_scheme AS scheme
  ON scheme.concept_scheme_id = node.concept_scheme_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = scheme.source_version_id
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS license_policy
  ON license_policy.license_policy_id = source_version.license_policy_id
LEFT JOIN evidence.concept_scheme_mapping AS mapping
  ON mapping.concept_scheme_id = node.concept_scheme_id
 AND mapping.concept_scheme_node_id = node.concept_scheme_node_id
 AND mapping.lifecycle_status_code = 'active'
 AND mapping.valid_from <= CURRENT_TIMESTAMP
 AND (mapping.valid_until IS NULL OR mapping.valid_until > CURRENT_TIMESTAMP)
LEFT JOIN kb.concept AS concept
  ON concept.concept_id = mapping.concept_id
WHERE scheme.lifecycle_status_code = 'active'
  AND scheme.valid_from <= CURRENT_TIMESTAMP
  AND (scheme.valid_until IS NULL OR scheme.valid_until > CURRENT_TIMESTAMP)
  AND node.lifecycle_status_code = 'active'
  AND node.valid_from <= CURRENT_TIMESTAMP
  AND (node.valid_until IS NULL OR node.valid_until > CURRENT_TIMESTAMP);

COMMENT ON VIEW kb.v_scheme_projection IS
    'Node-complete current source-scheme projection with zero, one, or multiple reviewed canonical mappings and explicit source/version/licence/export governance; visibility never implies redistribution permission.';

-- Candidate qualifiers are a governance queue, not a sensory vector. Counts
-- make accidental empirical values visible without exposing or aggregating
-- those values into a candidate score.
CREATE VIEW kb.v_candidate_qualifiers AS
SELECT
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code,
    concept.provenance_scope_code,
    concept.description,
    concept.editorial_note,
    COALESCE(labels.preferred_english_labels, '[]'::JSONB)
        AS preferred_english_labels,
    artifacts.empirical_pair_measurement_count,
    artifacts.projection_value_count,
    artifacts.reference_calibration_count,
    (
        artifacts.empirical_pair_measurement_count
        + artifacts.projection_value_count
        + artifacts.reference_calibration_count
    )::BIGINT AS numeric_artifact_count
FROM kb.concept AS concept
LEFT JOIN LATERAL (
    SELECT jsonb_agg(
        jsonb_build_object(
            'expression_key', expression.expression_key,
            'label', expression.expression_text,
            'language_tag_code', expression.language_tag_code
        )
        ORDER BY
            expression.language_tag_code,
            expression.normalized_text,
            expression.expression_key
    ) AS preferred_english_labels
    FROM kb.lexicalization AS lexicalization
    JOIN ref.mapping_type AS mapping_type
      ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
     AND mapping_type.is_preferred
    JOIN kb.lexical_expression AS expression
      ON expression.expression_id = lexicalization.expression_id
     AND expression.lifecycle_status_code = 'active'
    WHERE lexicalization.concept_id = concept.concept_id
      AND lexicalization.lifecycle_status_code = 'active'
      AND lexicalization.valid_from <= CURRENT_TIMESTAMP
      AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
          )
) AS labels ON TRUE
CROSS JOIN LATERAL (
    SELECT
        (
            SELECT count(*)::BIGINT
            FROM evidence.empirical_pair_measurement AS measurement
            WHERE measurement.subject_concept_id = concept.concept_id
               OR measurement.object_concept_id = concept.concept_id
        ) AS empirical_pair_measurement_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.concept_projection_value AS projection
            WHERE projection.concept_id = concept.concept_id
        ) AS projection_value_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.sensory_reference AS sensory_reference
            JOIN evidence.reference_calibration AS calibration
              ON calibration.sensory_reference_id =
                 sensory_reference.sensory_reference_id
            WHERE sensory_reference.concept_id = concept.concept_id
        ) AS reference_calibration_count
) AS artifacts
WHERE concept.concept_type_code = 'qualifier'
  AND concept.lifecycle_status_code = 'candidate';

COMMENT ON VIEW kb.v_candidate_qualifiers IS
    'Candidate qualifier governance surface with preferred labels and counts of prohibited numeric artifacts; counts are audit metadata, not sensory scores.';

CREATE VIEW kb.v_ontology_coverage AS
WITH current_lexicalizations AS (
    SELECT lexicalization.lexicalization_id
    FROM kb.lexicalization AS lexicalization
    WHERE lexicalization.lifecycle_status_code = 'active'
      AND lexicalization.valid_from <= CURRENT_TIMESTAMP
      AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
          )
),
current_relations AS (
    SELECT relation.concept_relation_id
    FROM kb.concept_relation AS relation
    WHERE relation.lifecycle_status_code = 'active'
      AND relation.valid_from <= CURRENT_TIMESTAMP
      AND (
            relation.valid_until IS NULL
            OR relation.valid_until > CURRENT_TIMESTAMP
          )
),
fixed_metrics (metric_key, metric_value) AS (
    SELECT 'concepts.total'::TEXT, count(*)::BIGINT FROM kb.concept
    UNION ALL
    SELECT 'concepts.active', count(*)::BIGINT
    FROM kb.concept WHERE lifecycle_status_code = 'active'
    UNION ALL
    SELECT 'concepts.candidate', count(*)::BIGINT
    FROM kb.concept WHERE lifecycle_status_code = 'candidate'
    UNION ALL
    SELECT 'sensory_attributes.active', count(*)::BIGINT
    FROM kb.concept
    WHERE concept_type_code = 'sensory_attribute'
      AND lifecycle_status_code = 'active'
    UNION ALL
    SELECT 'sensory_attributes.candidate', count(*)::BIGINT
    FROM kb.concept
    WHERE concept_type_code = 'sensory_attribute'
      AND lifecycle_status_code = 'candidate'
    UNION ALL
    SELECT 'lexical_expressions.active', count(*)::BIGINT
    FROM kb.lexical_expression WHERE lifecycle_status_code = 'active'
    UNION ALL
    SELECT 'lexicalizations.current', count(*)::BIGINT
    FROM current_lexicalizations
    UNION ALL
    SELECT 'concept_relations.current', count(*)::BIGINT
    FROM current_relations
    UNION ALL
    SELECT 'concept_dimension_links.active', count(*)::BIGINT
    FROM kb.concept_dimension_link WHERE lifecycle_status_code = 'active'
    UNION ALL
    SELECT 'concept_support_rows.total', count(*)::BIGINT
    FROM evidence.concept_support
    UNION ALL
    SELECT 'concept_support_rows.legacy_unspecified', count(*)::BIGINT
    FROM evidence.concept_support
    WHERE concept_support_role_code = 'legacy_unspecified'
    UNION ALL
    SELECT 'schemes.active', count(*)::BIGINT
    FROM evidence.concept_scheme WHERE lifecycle_status_code = 'active'
    UNION ALL
    SELECT 'scheme_nodes.current', count(DISTINCT concept_scheme_node_id)::BIGINT
    FROM kb.v_scheme_projection
    UNION ALL
    SELECT 'scheme_edges.current', count(*)::BIGINT
    FROM evidence.v_current_scheme_hierarchy
    UNION ALL
    SELECT 'scheme_mappings.current', count(concept_scheme_mapping_id)::BIGINT
    FROM kb.v_scheme_projection
    UNION ALL
    SELECT 'candidate_qualifiers.total', count(*)::BIGINT
    FROM kb.v_candidate_qualifiers
    UNION ALL
    SELECT 'candidate_qualifiers.numeric_artifacts',
           COALESCE(sum(numeric_artifact_count), 0)::BIGINT
    FROM kb.v_candidate_qualifiers
),
concept_type_status_metrics AS (
    SELECT
        format(
            'concepts.type.%s.status.%s',
            concept_type.concept_type_code,
            lifecycle.lifecycle_status_code
        ) AS metric_key,
        count(concept.concept_id)::BIGINT AS metric_value
    FROM ref.concept_type AS concept_type
    CROSS JOIN ref.lifecycle_status AS lifecycle
    LEFT JOIN kb.concept AS concept
      ON concept.concept_type_code = concept_type.concept_type_code
     AND concept.lifecycle_status_code = lifecycle.lifecycle_status_code
    GROUP BY
        concept_type.concept_type_code,
        lifecycle.lifecycle_status_code
),
support_role_metrics AS (
    SELECT
        'concept_support.role.' || role.concept_support_role_code
            AS metric_key,
        count(support.concept_support_id)::BIGINT AS metric_value
    FROM ref.concept_support_role AS role
    LEFT JOIN evidence.concept_support AS support
      ON support.concept_support_role_code = role.concept_support_role_code
    GROUP BY role.concept_support_role_code
),
scheme_metrics AS (
    SELECT
        scheme.concept_scheme_key,
        (
            SELECT count(*)::BIGINT
            FROM evidence.concept_scheme_node AS node
            WHERE node.concept_scheme_id = scheme.concept_scheme_id
        ) AS total_node_count,
        count(DISTINCT projection.concept_scheme_node_id)::BIGINT
            AS node_count,
        (
            count(DISTINCT projection.concept_scheme_node_id)
                FILTER (
                    WHERE projection.concept_scheme_mapping_id IS NOT NULL
                )
        )::BIGINT AS mapped_node_count,
        (
            count(DISTINCT projection.concept_scheme_node_id)
                FILTER (
                    WHERE projection.concept_scheme_mapping_id IS NULL
                )
        )::BIGINT AS unmapped_node_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.concept_scheme_mapping AS mapping
            WHERE mapping.concept_scheme_id = scheme.concept_scheme_id
        ) AS total_mapping_count,
        count(projection.concept_scheme_mapping_id)::BIGINT AS mapping_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.concept_scheme_edge AS edge
            WHERE edge.concept_scheme_id = scheme.concept_scheme_id
        ) AS total_edge_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.concept_scheme_edge AS edge
            WHERE edge.concept_scheme_id = scheme.concept_scheme_id
              AND edge.lifecycle_status_code = 'active'
        ) AS active_edge_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.concept_scheme_edge AS edge
            WHERE edge.concept_scheme_id = scheme.concept_scheme_id
              AND edge.lifecycle_status_code = 'candidate'
        ) AS candidate_edge_count,
        (
            SELECT count(*)::BIGINT
            FROM evidence.v_current_scheme_hierarchy AS hierarchy
            WHERE hierarchy.concept_scheme_id = scheme.concept_scheme_id
        ) AS edge_count
    FROM evidence.concept_scheme AS scheme
    LEFT JOIN kb.v_scheme_projection AS projection
      ON projection.concept_scheme_id = scheme.concept_scheme_id
    WHERE scheme.lifecycle_status_code = 'active'
    GROUP BY scheme.concept_scheme_id, scheme.concept_scheme_key
),
scheme_metric_rows AS (
    SELECT
        'schemes.' || concept_scheme_key || '.nodes.total' AS metric_key,
        total_node_count AS metric_value
    FROM scheme_metrics
    UNION ALL
    SELECT
        'schemes.' || concept_scheme_key || '.nodes.current' AS metric_key,
        node_count AS metric_value
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.nodes.mapped', mapped_node_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.nodes.unmapped', unmapped_node_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.mappings.total', total_mapping_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.mappings.current', mapping_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.edges.total', total_edge_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.edges.current', edge_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.edges.active', active_edge_count
    FROM scheme_metrics
    UNION ALL
    SELECT 'schemes.' || concept_scheme_key || '.edges.candidate', candidate_edge_count
    FROM scheme_metrics
)
SELECT metric_key, metric_value
FROM fixed_metrics
UNION ALL
SELECT metric_key, metric_value
FROM concept_type_status_metrics
UNION ALL
SELECT metric_key, metric_value
FROM support_role_metrics
UNION ALL
SELECT metric_key, metric_value
FROM scheme_metric_rows;

COMMENT ON VIEW kb.v_ontology_coverage IS
    'Deterministic one-row-per-metric ontology, lifecycle, provenance-role, and source-scheme coverage inventory for rebuild comparison; counts are not sensory measurements.';

CREATE FUNCTION audit.run_round2a_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round2a_validation_queries$
WITH RECURSIVE
expected_schemes (concept_scheme_key) AS (
    VALUES
        ('scheme.project.coffee_sensory_kb_v0.2026-08-24'::TEXT),
        ('scheme.wcr.sensory_lexicon_2_0.public_24_partial'::TEXT)
),
expected_candidate_sensory (concept_key) AS (
    VALUES
        ('sensory.pink_grapefruit'::TEXT),
        ('sensory.blackcurrant'::TEXT),
        ('sensory.orange_blossom'::TEXT),
        ('sensory.mint'::TEXT),
        ('sensory.eucalyptus'::TEXT),
        ('sensory.lemongrass'::TEXT),
        ('sensory.green_tea'::TEXT),
        ('sensory.leather'::TEXT)
),
active_preferred_english_counts AS (
    SELECT
        concept.concept_id,
        count(expression.expression_id)::BIGINT AS preferred_label_count
    FROM kb.concept AS concept
    LEFT JOIN kb.lexicalization AS lexicalization
      ON lexicalization.concept_id = concept.concept_id
     AND lexicalization.lifecycle_status_code = 'active'
     AND lexicalization.valid_from <= CURRENT_TIMESTAMP
     AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
         )
    LEFT JOIN ref.mapping_type AS mapping_type
      ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
     AND mapping_type.is_preferred
    LEFT JOIN kb.lexical_expression AS expression
      ON expression.expression_id = lexicalization.expression_id
     AND mapping_type.mapping_type_code IS NOT NULL
     AND expression.lifecycle_status_code = 'active'
     AND expression.language_tag_code = 'en'
    WHERE concept.lifecycle_status_code = 'active'
    GROUP BY concept.concept_id
),
scheme_walk (
    concept_scheme_id,
    start_node_id,
    current_node_id
) AS (
    SELECT
        hierarchy.concept_scheme_id,
        hierarchy.parent_node_id,
        hierarchy.child_node_id
    FROM evidence.v_current_scheme_hierarchy AS hierarchy

    UNION

    SELECT
        walk.concept_scheme_id,
        walk.start_node_id,
        hierarchy.child_node_id
    FROM scheme_walk AS walk
    JOIN evidence.v_current_scheme_hierarchy AS hierarchy
      ON hierarchy.concept_scheme_id = walk.concept_scheme_id
     AND hierarchy.parent_node_id = walk.current_node_id
),
check_counts (check_key, violation_count) AS (
    SELECT
        'active_sensory_attributes_outside_v0_range',
        CASE
            WHEN count(*) BETWEEN 90 AND 120 THEN 0::BIGINT
            ELSE 1::BIGINT
        END
    FROM kb.concept AS concept
    WHERE concept.concept_type_code = 'sensory_attribute'
      AND concept.lifecycle_status_code = 'active'

    UNION ALL

    SELECT
        'concept_total_snapshot_deviation',
        abs(count(*) - 130)::BIGINT
    FROM kb.concept

    UNION ALL

    SELECT
        'active_concept_snapshot_deviation',
        abs(count(*) - 114)::BIGINT
    FROM kb.concept
    WHERE lifecycle_status_code = 'active'

    UNION ALL

    SELECT
        'candidate_concept_snapshot_deviation',
        abs(count(*) - 16)::BIGINT
    FROM kb.concept
    WHERE lifecycle_status_code = 'candidate'

    UNION ALL

    SELECT
        'active_sensory_attribute_snapshot_deviation',
        abs(count(*) - 92)::BIGINT
    FROM kb.concept AS concept
    WHERE concept.concept_type_code = 'sensory_attribute'
      AND concept.lifecycle_status_code = 'active'

    UNION ALL

    SELECT
        'candidate_sensory_attribute_snapshot_deviation',
        abs(count(*) - 8)::BIGINT
    FROM kb.concept AS concept
    WHERE concept.concept_type_code = 'sensory_attribute'
      AND concept.lifecycle_status_code = 'candidate'

    UNION ALL

    SELECT
        'candidate_sensory_attribute_identity_mismatches',
        count(*)::BIGINT
    FROM expected_candidate_sensory AS expected
    FULL JOIN (
        SELECT concept.concept_key
        FROM kb.concept AS concept
        WHERE concept.concept_type_code = 'sensory_attribute'
          AND concept.lifecycle_status_code = 'candidate'
    ) AS actual
      ON actual.concept_key = expected.concept_key
    WHERE expected.concept_key IS NULL
       OR actual.concept_key IS NULL

    UNION ALL

    SELECT
        'active_concepts_without_exactly_one_preferred_english_label',
        count(*)::BIGINT
    FROM active_preferred_english_counts AS label_count
    WHERE label_count.preferred_label_count <> 1

    UNION ALL

    SELECT
        'active_sensory_core_label_cardinality_violations',
        count(*)::BIGINT
    FROM kb.v_active_sensory_core AS sensory
    WHERE sensory.preferred_english_label_count <> 1

    UNION ALL

    SELECT
        'externally_sourced_active_concepts_without_versioned_provenance',
        count(*)::BIGINT
    FROM kb.concept AS concept
    JOIN ref.provenance_scope AS provenance_scope
      ON provenance_scope.provenance_scope_code = concept.provenance_scope_code
    WHERE concept.lifecycle_status_code = 'active'
      AND provenance_scope.requires_source_support
      AND NOT EXISTS (
          SELECT 1
          FROM evidence.v_concept_provenance AS provenance
          WHERE provenance.concept_id = concept.concept_id
      )

    UNION ALL

    SELECT
        'externally_sourced_active_lexicalizations_without_versioned_provenance',
        count(*)::BIGINT
    FROM kb.lexicalization AS lexicalization
    JOIN ref.provenance_scope AS provenance_scope
      ON provenance_scope.provenance_scope_code =
         lexicalization.provenance_scope_code
    WHERE lexicalization.lifecycle_status_code = 'active'
      AND provenance_scope.requires_source_support
      AND NOT EXISTS (
          SELECT 1
          FROM evidence.v_source_coverage AS coverage
          WHERE coverage.assertion_kind = 'lexicalization'
            AND coverage.assertion_id = lexicalization.lexicalization_id
      )

    UNION ALL

    SELECT
        'active_relations_without_required_versioned_provenance',
        count(*)::BIGINT
    FROM kb.concept_relation AS relation
    JOIN ref.provenance_scope AS provenance_scope
      ON provenance_scope.provenance_scope_code =
         relation.provenance_scope_code
    JOIN ref.relation_type AS relation_type
      ON relation_type.relation_type_code = relation.relation_type_code
    WHERE relation.lifecycle_status_code = 'active'
      AND (
            provenance_scope.requires_source_support
            OR relation_type.evidence_required
          )
      AND NOT EXISTS (
          SELECT 1
          FROM evidence.v_source_coverage AS coverage
          WHERE coverage.assertion_kind = 'concept_relation'
            AND coverage.assertion_id = relation.concept_relation_id
      )

    UNION ALL

    SELECT
        'concept_support_rows_without_resolved_source_and_license',
        count(*)::BIGINT
    FROM evidence.concept_support AS support
    LEFT JOIN evidence.v_concept_provenance AS provenance
      ON provenance.concept_support_id = support.concept_support_id
    WHERE provenance.concept_support_id IS NULL
       OR provenance.source_version_id IS NULL
       OR provenance.source_id IS NULL
       OR provenance.license_policy_id IS NULL

    UNION ALL

    SELECT
        'active_scheme_key_mismatches',
        count(*)::BIGINT
    FROM (
        SELECT missing.concept_scheme_key
        FROM (
            SELECT expected.concept_scheme_key
            FROM expected_schemes AS expected
            EXCEPT
            SELECT scheme.concept_scheme_key
            FROM evidence.concept_scheme AS scheme
            WHERE scheme.lifecycle_status_code = 'active'
        ) AS missing

        UNION ALL

        SELECT unexpected.concept_scheme_key
        FROM (
            SELECT scheme.concept_scheme_key
            FROM evidence.concept_scheme AS scheme
            WHERE scheme.lifecycle_status_code = 'active'
            EXCEPT
            SELECT expected.concept_scheme_key
            FROM expected_schemes AS expected
        ) AS unexpected
    ) AS mismatch

    UNION ALL

    SELECT
        'active_schemes_outside_current_validity',
        count(*)::BIGINT
    FROM evidence.concept_scheme AS scheme
    WHERE scheme.lifecycle_status_code = 'active'
      AND (
            scheme.valid_from > CURRENT_TIMESTAMP
            OR (
                scheme.valid_until IS NOT NULL
                AND scheme.valid_until <= CURRENT_TIMESTAMP
            )
          )

    UNION ALL

    SELECT
        'active_schemes_without_source_version_license_closure',
        count(*)::BIGINT
    FROM evidence.concept_scheme AS scheme
    LEFT JOIN evidence.source_version AS source_version
      ON source_version.source_version_id = scheme.source_version_id
    LEFT JOIN evidence.source AS source
      ON source.source_id = source_version.source_id
    LEFT JOIN evidence.license_policy AS license_policy
      ON license_policy.license_policy_id = source_version.license_policy_id
    WHERE scheme.lifecycle_status_code = 'active'
      AND (
            source_version.source_version_id IS NULL
            OR source.source_id IS NULL
            OR license_policy.license_policy_id IS NULL
          )

    UNION ALL

    SELECT
        'canonical_tables_with_source_scheme_ownership',
        count(*)::BIGINT
    FROM information_schema.columns AS column_definition
    WHERE column_definition.table_schema = 'kb'
      AND column_definition.table_name IN (
          'concept',
          'lexicalization',
          'concept_relation'
      )
      AND column_definition.column_name LIKE '%scheme%'

    UNION ALL

    SELECT
        'canonical_foreign_keys_to_source_scheme_tables',
        count(*)::BIGINT
    FROM pg_catalog.pg_constraint AS constraint_definition
    JOIN pg_catalog.pg_class AS local_table
      ON local_table.oid = constraint_definition.conrelid
    JOIN pg_catalog.pg_namespace AS local_schema
      ON local_schema.oid = local_table.relnamespace
    JOIN pg_catalog.pg_class AS referenced_table
      ON referenced_table.oid = constraint_definition.confrelid
    JOIN pg_catalog.pg_namespace AS referenced_schema
      ON referenced_schema.oid = referenced_table.relnamespace
    WHERE constraint_definition.contype = 'f'
      AND local_schema.nspname = 'kb'
      AND referenced_schema.nspname = 'evidence'
      AND referenced_table.relname LIKE 'concept_scheme%'

    UNION ALL

    SELECT
        'project_scheme_node_snapshot_deviation',
        abs(count(*) - 130)::BIGINT
    FROM evidence.concept_scheme_node AS node
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = node.concept_scheme_id
    WHERE scheme.concept_scheme_key =
        'scheme.project.coffee_sensory_kb_v0.2026-08-24'

    UNION ALL

    SELECT
        'project_scheme_mapping_snapshot_deviation',
        abs(count(*) - 130)::BIGINT
    FROM evidence.concept_scheme_mapping AS mapping
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = mapping.concept_scheme_id
    WHERE scheme.concept_scheme_key =
        'scheme.project.coffee_sensory_kb_v0.2026-08-24'

    UNION ALL

    SELECT
        'project_scheme_edge_snapshot_deviation',
        abs(count(*) - 106)::BIGINT
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
        'scheme.project.coffee_sensory_kb_v0.2026-08-24'

    UNION ALL

    SELECT
        'project_scheme_active_edge_snapshot_deviation',
        abs(count(*) - 98)::BIGINT
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
        'scheme.project.coffee_sensory_kb_v0.2026-08-24'
      AND edge.lifecycle_status_code = 'active'

    UNION ALL

    SELECT
        'project_scheme_candidate_edge_snapshot_deviation',
        abs(count(*) - 8)::BIGINT
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
        'scheme.project.coffee_sensory_kb_v0.2026-08-24'
      AND edge.lifecycle_status_code = 'candidate'

    UNION ALL

    SELECT
        'project_scheme_nodes_without_exactly_one_mapping',
        count(*)::BIGINT
    FROM (
        SELECT projection.concept_scheme_node_id
        FROM kb.v_scheme_projection AS projection
        WHERE projection.concept_scheme_key =
            'scheme.project.coffee_sensory_kb_v0.2026-08-24'
        GROUP BY projection.concept_scheme_node_id
        HAVING count(projection.concept_scheme_mapping_id) <> 1
    ) AS invalid_node

    UNION ALL

    SELECT
        'project_scheme_active_sensory_mapping_cardinality_violations',
        count(*)::BIGINT
    FROM (
        SELECT concept.concept_id
        FROM kb.concept AS concept
        LEFT JOIN kb.v_scheme_projection AS projection
          ON projection.concept_scheme_key =
             'scheme.project.coffee_sensory_kb_v0.2026-08-24'
         AND projection.concept_id = concept.concept_id
        WHERE concept.concept_type_code = 'sensory_attribute'
          AND concept.lifecycle_status_code = 'active'
        GROUP BY concept.concept_id
        HAVING count(projection.concept_scheme_mapping_id) <> 1
    ) AS invalid_mapping

    UNION ALL

    SELECT
        'project_scheme_metallic_polyhierarchy_missing',
        CASE WHEN EXISTS (
            SELECT 1
            FROM evidence.v_current_scheme_hierarchy AS hierarchy
            JOIN kb.v_scheme_projection AS projection
              ON projection.concept_scheme_id = hierarchy.concept_scheme_id
             AND projection.concept_scheme_node_id = hierarchy.child_node_id
            WHERE hierarchy.concept_scheme_key =
                'scheme.project.coffee_sensory_kb_v0.2026-08-24'
              AND projection.concept_key = 'sensory.metallic'
            GROUP BY hierarchy.concept_scheme_id, hierarchy.child_node_id
            HAVING count(DISTINCT hierarchy.parent_node_id) > 1
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'wcr_partial_node_snapshot_deviation',
        abs(count(DISTINCT projection.concept_scheme_node_id) - 24)::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'

    UNION ALL

    SELECT
        'wcr_partial_mapped_node_snapshot_deviation',
        abs(
            count(DISTINCT projection.concept_scheme_node_id)
                FILTER (
                    WHERE projection.concept_scheme_mapping_id IS NOT NULL
                )
            - 15
        )::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'

    UNION ALL

    SELECT
        'wcr_partial_unmapped_node_snapshot_deviation',
        abs(
            count(DISTINCT projection.concept_scheme_node_id)
                FILTER (
                    WHERE projection.concept_scheme_mapping_id IS NULL
                )
            - 9
        )::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'

    UNION ALL

    SELECT
        'wcr_partial_mapping_snapshot_deviation',
        abs(count(projection.concept_scheme_mapping_id) - 15)::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'

    UNION ALL

    SELECT
        'wcr_partial_hierarchy_edges',
        count(*)::BIGINT
    FROM evidence.concept_scheme_edge AS edge
    JOIN evidence.concept_scheme AS scheme
      ON scheme.concept_scheme_id = edge.concept_scheme_id
    WHERE scheme.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'

    UNION ALL

    SELECT
        'wcr_partial_unsafe_reviewed_mappings',
        count(*)::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
      AND projection.concept_scheme_mapping_id IS NOT NULL
      AND (
            lower(btrim(projection.source_label)) IN (
                'butyric acid',
                'isovaleric acid',
                'fresh',
                'musty/earthy',
                'musty/dusty',
                'moldy/damp',
                'brown spice',
                'vanillin',
                'floral'
            )
            OR (
                projection.source_label LIKE '%/%'
                AND projection.scheme_concept_mapping_role_code =
                    'equivalent_scope'
            )
          )

    UNION ALL

    SELECT
        'wcr_partial_mappings_to_nonactive_concepts',
        count(*)::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
      AND projection.concept_scheme_mapping_id IS NOT NULL
      AND projection.concept_lifecycle_status_code <> 'active'

    UNION ALL

    SELECT
        'wcr_partial_rows_marked_exportable',
        count(*)::BIGINT
    FROM kb.v_scheme_projection AS projection
    WHERE projection.concept_scheme_key =
        'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
      AND projection.production_export_allowed

    UNION ALL

    SELECT
        'project_scheme_export_permission_missing',
        CASE WHEN EXISTS (
            SELECT 1
            FROM kb.v_scheme_projection AS projection
            WHERE projection.concept_scheme_key =
                'scheme.project.coffee_sensory_kb_v0.2026-08-24'
              AND projection.production_export_allowed
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'current_source_scheme_hierarchy_cycles',
        count(*)::BIGINT
    FROM (
        SELECT DISTINCT walk.concept_scheme_id, walk.start_node_id
        FROM scheme_walk AS walk
        WHERE walk.start_node_id = walk.current_node_id
    ) AS cycle

    UNION ALL

    SELECT
        'cross_scheme_edge_endpoints',
        count(*)::BIGINT
    FROM evidence.concept_scheme_edge AS edge
    LEFT JOIN evidence.concept_scheme_node AS parent
      ON parent.concept_scheme_node_id = edge.parent_node_id
    LEFT JOIN evidence.concept_scheme_node AS child
      ON child.concept_scheme_node_id = edge.child_node_id
    WHERE parent.concept_scheme_node_id IS NULL
       OR child.concept_scheme_node_id IS NULL
       OR parent.concept_scheme_id <> edge.concept_scheme_id
       OR child.concept_scheme_id <> edge.concept_scheme_id

    UNION ALL

    SELECT
        'cross_scheme_mapping_nodes',
        count(*)::BIGINT
    FROM evidence.concept_scheme_mapping AS mapping
    LEFT JOIN evidence.concept_scheme_node AS node
      ON node.concept_scheme_node_id = mapping.concept_scheme_node_id
    WHERE node.concept_scheme_node_id IS NULL
       OR node.concept_scheme_id <> mapping.concept_scheme_id

    UNION ALL

    SELECT
        'pink_grapefruit_candidate_identity_violations',
        CASE WHEN (
            SELECT count(*)
            FROM kb.concept AS concept
            WHERE concept.concept_key = 'sensory.pink_grapefruit'
              AND concept.concept_type_code = 'sensory_attribute'
              AND concept.lifecycle_status_code = 'candidate'
        ) = 1 AND NOT EXISTS (
            SELECT 1
            FROM kb.v_lexical_resolution AS resolution
            WHERE resolution.normalized_text IN (
                'pink grapefruit',
                'pink-grapefruit'
            )
              AND resolution.resolution_status = 'RESOLVED'
        ) AND NOT EXISTS (
            SELECT 1
            FROM kb.lexical_expression AS expression
            JOIN kb.lexicalization AS lexicalization
              ON lexicalization.expression_id = expression.expression_id
            JOIN kb.concept AS concept
              ON concept.concept_id = lexicalization.concept_id
            WHERE expression.normalized_text IN (
                'pink grapefruit',
                'pink-grapefruit'
            )
              AND concept.concept_key = 'sensory.grapefruit'
              AND lexicalization.lifecycle_status_code = 'active'
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'fermented_sensory_process_identity_violations',
        CASE WHEN EXISTS (
            SELECT 1
            FROM kb.concept AS sensory
            CROSS JOIN kb.concept AS process
            WHERE sensory.concept_key = 'sensory.fermented_character'
              AND sensory.concept_type_code = 'sensory_attribute'
              AND sensory.lifecycle_status_code = 'active'
              AND process.concept_key = 'process.fermentation'
              AND process.concept_type_code = 'process_entity'
              AND sensory.concept_id <> process.concept_id
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'affective_terms_with_sensory_numeric_artifacts',
        count(*)::BIGINT
    FROM (
        SELECT link.concept_dimension_link_id::TEXT AS artifact_key
        FROM kb.concept AS concept
        JOIN kb.concept_dimension_link AS link
          ON link.concept_id = concept.concept_id
        WHERE concept.concept_type_code = 'affective_term'
          AND link.lifecycle_status_code = 'active'

        UNION ALL

        SELECT measurement.empirical_pair_measurement_id::TEXT
        FROM kb.concept AS concept
        JOIN evidence.empirical_pair_measurement AS measurement
          ON measurement.subject_concept_id = concept.concept_id
          OR measurement.object_concept_id = concept.concept_id
        WHERE concept.concept_type_code = 'affective_term'

        UNION ALL

        SELECT projection.concept_projection_value_id::TEXT
        FROM kb.concept AS concept
        JOIN evidence.concept_projection_value AS projection
          ON projection.concept_id = concept.concept_id
        WHERE concept.concept_type_code = 'affective_term'

        UNION ALL

        SELECT calibration.reference_calibration_id::TEXT
        FROM kb.concept AS concept
        JOIN evidence.sensory_reference AS sensory_reference
          ON sensory_reference.concept_id = concept.concept_id
        JOIN evidence.reference_calibration AS calibration
          ON calibration.sensory_reference_id =
             sensory_reference.sensory_reference_id
        WHERE concept.concept_type_code = 'affective_term'
    ) AS artifact

    UNION ALL

    SELECT
        'pleasant_affective_identity_missing',
        CASE WHEN EXISTS (
            SELECT 1
            FROM kb.concept AS concept
            WHERE concept.concept_key = 'affective.pleasant'
              AND concept.concept_type_code = 'affective_term'
              AND concept.lifecycle_status_code = 'candidate'
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'candidate_qualifier_numeric_artifacts',
        COALESCE(sum(qualifier.numeric_artifact_count), 0)::BIGINT
    FROM kb.v_candidate_qualifiers AS qualifier

    UNION ALL

    SELECT
        'bright_candidate_qualifier_missing',
        CASE WHEN EXISTS (
            SELECT 1
            FROM kb.v_candidate_qualifiers AS qualifier
            WHERE qualifier.concept_key = 'qualifier.bright'
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'winey_polysemy_contract_violations',
        CASE WHEN (
            SELECT count(DISTINCT lexicalization.concept_id)
            FROM kb.lexical_expression AS expression
            JOIN kb.lexicalization AS lexicalization
              ON lexicalization.expression_id = expression.expression_id
            WHERE expression.expression_key = 'expression.en.winey'
              AND lexicalization.lifecycle_status_code = 'active'
        ) = 2 AND EXISTS (
            SELECT 1
            FROM kb.lexical_expression AS expression
            JOIN kb.lexicalization AS lexicalization
              ON lexicalization.expression_id = expression.expression_id
            JOIN ref.mapping_type AS mapping_type
              ON mapping_type.mapping_type_code =
                 lexicalization.mapping_type_code
            WHERE expression.expression_key = 'expression.en.winey'
              AND lexicalization.lifecycle_status_code = 'active'
              AND mapping_type.allows_polysemy
        ) THEN 0::BIGINT ELSE 1::BIGINT END

    UNION ALL

    SELECT
        'ontology_coverage_metric_contract_violations',
        count(*)::BIGINT
    FROM (
        SELECT coverage.metric_key
        FROM kb.v_ontology_coverage AS coverage
        GROUP BY coverage.metric_key
        HAVING count(*) <> 1 OR min(coverage.metric_value) < 0
    ) AS invalid_metric

    UNION ALL

    SELECT
        'pgvector_extensions_installed',
        count(*)::BIGINT
    FROM pg_catalog.pg_extension AS extension
    WHERE extension.extname = 'vector'
)
SELECT
    counts.check_key,
    counts.violation_count,
    counts.violation_count = 0 AS passed
FROM check_counts AS counts;
$run_round2a_validation_queries$;

COMMENT ON FUNCTION audit.run_round2a_validation_queries() IS
    'Expected-zero Round 2A validation contract for canonical coverage, provenance closure, source-scheme isolation, rights, polyhierarchy, and semantic safety.';

SELECT check_key, violation_count, passed
FROM audit.run_round2a_validation_queries()
ORDER BY check_key;

DO $round2a_validation_gate$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM audit.run_round2a_validation_queries()
    ) OR EXISTS (
        SELECT 1
        FROM audit.run_round2a_validation_queries()
        WHERE passed IS NOT TRUE
           OR violation_count <> 0
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_validation_gate_ck',
            MESSAGE = 'Round 2A validation failed: one or more expected-zero checks reported violations';
    END IF;
END
$round2a_validation_gate$;

COMMIT;
