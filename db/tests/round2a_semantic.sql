\set ON_ERROR_STOP on
\pset pager off

-- Round 2A ontology semantics.  Exact inventories are printed by the coverage
-- view and reproducibility harness; gates here protect scientific boundaries
-- without conflating all concept types with the 90--120 sensory-attribute
-- target.

BEGIN TRANSACTION READ ONLY;

\echo ROUND2A_COVERAGE
SELECT metric_key, metric_value
FROM kb.v_ontology_coverage
ORDER BY metric_key;

\echo ROUND2A_CONCEPT_TYPE_STATUS_COUNTS
SELECT
    concept_type_code,
    lifecycle_status_code,
    count(*) AS concept_count
FROM kb.concept
GROUP BY concept_type_code, lifecycle_status_code
ORDER BY concept_type_code, lifecycle_status_code;

\echo ROUND2A_PROVENANCE_ROLE_COUNTS
SELECT concept_support_role_code, count(*) AS support_count
FROM evidence.concept_support
GROUP BY concept_support_role_code
ORDER BY concept_support_role_code;

\echo ROUND2A_SCHEME_COUNTS
SELECT
    scheme.concept_scheme_key,
    count(DISTINCT node.concept_scheme_node_id) AS node_count,
    count(DISTINCT edge.concept_scheme_edge_id) AS edge_count,
    count(DISTINCT mapping.concept_scheme_mapping_id) AS mapping_count
FROM evidence.concept_scheme AS scheme
LEFT JOIN evidence.concept_scheme_node AS node
  ON node.concept_scheme_id = scheme.concept_scheme_id
LEFT JOIN evidence.concept_scheme_edge AS edge
  ON edge.concept_scheme_id = scheme.concept_scheme_id
LEFT JOIN evidence.concept_scheme_mapping AS mapping
  ON mapping.concept_scheme_id = scheme.concept_scheme_id
GROUP BY scheme.concept_scheme_id, scheme.concept_scheme_key
ORDER BY scheme.concept_scheme_key;

DO $round2a_semantic$
DECLARE
    active_sensory_attribute_count BIGINT;
BEGIN
    SELECT count(*)
    INTO active_sensory_attribute_count
    FROM kb.concept AS concept
    WHERE concept.concept_type_code = 'sensory_attribute'
      AND concept.lifecycle_status_code = 'active';

    IF active_sensory_attribute_count NOT BETWEEN 90 AND 120 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_active_sensory_attribute_range_ck',
            MESSAGE = format(
                'Round 2A requires 90--120 active sensory attributes; found %s',
                active_sensory_attribute_count
            );
    END IF;

    IF active_sensory_attribute_count <> 92 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_active_sensory_attribute_snapshot_ck',
            MESSAGE = format(
                'Round 2A frozen seed requires exactly 92 active sensory attributes; found %s',
                active_sensory_attribute_count
            );
    END IF;

    IF (
        SELECT count(*)
        FROM kb.concept AS concept
        WHERE concept.concept_type_code = 'sensory_attribute'
          AND concept.lifecycle_status_code = 'candidate'
    ) <> 8 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_candidate_sensory_attribute_snapshot_ck',
            MESSAGE = 'Round 2A frozen seed requires exactly eight evidence-limited candidate sensory attributes';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_type_code = 'sensory_attribute'
          AND concept.lifecycle_status_code = 'candidate'
          AND concept.concept_key <> ALL(ARRAY[
              'sensory.pink_grapefruit',
              'sensory.blackcurrant',
              'sensory.orange_blossom',
              'sensory.mint',
              'sensory.eucalyptus',
              'sensory.lemongrass',
              'sensory.green_tea',
              'sensory.leather'
          ]::TEXT[])
    ) OR EXISTS (
        SELECT expected.concept_key
        FROM unnest(ARRAY[
            'sensory.pink_grapefruit',
            'sensory.blackcurrant',
            'sensory.orange_blossom',
            'sensory.mint',
            'sensory.eucalyptus',
            'sensory.lemongrass',
            'sensory.green_tea',
            'sensory.leather'
        ]::TEXT[]) AS expected(concept_key)
        WHERE NOT EXISTS (
            SELECT 1
            FROM kb.concept AS concept
            WHERE concept.concept_key = expected.concept_key
              AND concept.concept_type_code = 'sensory_attribute'
              AND concept.lifecycle_status_code = 'candidate'
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_candidate_sensory_identity_snapshot_ck',
            MESSAGE = 'Round 2A candidate sensory identities differ from the evidence-audited frozen set';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM kb.v_ontology_coverage)
       OR EXISTS (
            SELECT 1
            FROM kb.v_ontology_coverage AS coverage
            WHERE coverage.metric_key IS NULL
               OR coverage.metric_key = ''
               OR coverage.metric_value < 0
       )
       OR EXISTS (
            SELECT coverage.metric_key
            FROM kb.v_ontology_coverage AS coverage
            GROUP BY coverage.metric_key
            HAVING count(*) <> 1
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_coverage_view_contract_ck',
            MESSAGE = 'Round 2A coverage must expose one nonnegative value for every uniquely named metric';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM (
            VALUES
                ('concepts.total'::TEXT, 130::BIGINT),
                ('concepts.active', 114::BIGINT),
                ('concepts.candidate', 16::BIGINT),
                ('sensory_attributes.active', 92::BIGINT),
                ('sensory_attributes.candidate', 8::BIGINT),
                ('schemes.active', 2::BIGINT),
                (
                    'schemes.scheme.project.coffee_sensory_kb_v0.2026-08-24.nodes.total',
                    130::BIGINT
                ),
                (
                    'schemes.scheme.project.coffee_sensory_kb_v0.2026-08-24.mappings.total',
                    130::BIGINT
                ),
                (
                    'schemes.scheme.project.coffee_sensory_kb_v0.2026-08-24.edges.total',
                    106::BIGINT
                ),
                (
                    'schemes.scheme.project.coffee_sensory_kb_v0.2026-08-24.edges.active',
                    98::BIGINT
                ),
                (
                    'schemes.scheme.project.coffee_sensory_kb_v0.2026-08-24.edges.candidate',
                    8::BIGINT
                ),
                (
                    'schemes.scheme.wcr.sensory_lexicon_2_0.public_24_partial.nodes.total',
                    24::BIGINT
                ),
                (
                    'schemes.scheme.wcr.sensory_lexicon_2_0.public_24_partial.mappings.total',
                    15::BIGINT
                ),
                (
                    'schemes.scheme.wcr.sensory_lexicon_2_0.public_24_partial.edges.total',
                    0::BIGINT
                )
        ) AS expected(metric_key, metric_value)
        LEFT JOIN kb.v_ontology_coverage AS observed
          ON observed.metric_key = expected.metric_key
        WHERE observed.metric_key IS NULL
           OR observed.metric_value <> expected.metric_value
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_coverage_snapshot_ck',
            MESSAGE = 'Round 2A coverage metrics differ from the frozen seed inventory';
    END IF;

    -- Every active concept, regardless of type, needs one current preferred
    -- English expression. Candidate and historical concepts are intentionally
    -- outside this publication-readiness invariant.
    IF EXISTS (
        SELECT concept.concept_id
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
        HAVING count(expression.expression_id) <> 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_active_concept_preferred_english_label_ck',
            MESSAGE = 'every active concept must have exactly one current preferred English label';
    END IF;

    -- Provenance closure: a support row is insufficient unless its direct or
    -- dataset origin resolves all the way to a source version and licence.
    IF EXISTS (
        SELECT 1
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
    ) OR EXISTS (
        SELECT 1
        FROM kb.lexicalization AS lexicalization
        JOIN ref.provenance_scope AS provenance_scope
          ON provenance_scope.provenance_scope_code = lexicalization.provenance_scope_code
        WHERE lexicalization.lifecycle_status_code = 'active'
          AND provenance_scope.requires_source_support
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.v_source_coverage AS coverage
              WHERE coverage.assertion_kind = 'lexicalization'
                AND coverage.assertion_id = lexicalization.lexicalization_id
          )
    ) OR EXISTS (
        SELECT 1
        FROM kb.concept_relation AS relation
        JOIN ref.provenance_scope AS provenance_scope
          ON provenance_scope.provenance_scope_code = relation.provenance_scope_code
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
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_active_assertion_provenance_closure_ck',
            MESSAGE = 'active assertions requiring provenance must resolve through support to a versioned, licensed source';
    END IF;

    IF (SELECT count(*) FROM ref.concept_support_role) <> 9
       OR (SELECT count(*) FROM ref.scheme_concept_mapping_role) <> 4 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_controlled_role_inventory_ck',
            MESSAGE = 'Round 2A controlled provenance and scheme-mapping role inventories are incomplete';
    END IF;

    -- Source schemes are evidence projections. The canonical KB must neither
    -- acquire a scheme ownership column nor reference scheme tables by FK.
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns AS column_definition
        WHERE column_definition.table_schema = 'kb'
          AND column_definition.table_name IN (
              'concept',
              'lexicalization',
              'concept_relation'
          )
          AND column_definition.column_name LIKE '%scheme%'
    ) OR EXISTS (
        SELECT 1
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
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_source_scheme_isolation_ck',
            MESSAGE = 'source-local schemes must not become canonical concept ownership or hierarchy';
    END IF;

    IF (SELECT count(*) FROM evidence.concept_scheme WHERE lifecycle_status_code = 'active') <> 2
       OR NOT EXISTS (SELECT 1 FROM evidence.v_current_scheme_hierarchy)
       OR NOT EXISTS (SELECT 1 FROM evidence.v_current_scheme_concept_mapping)
       OR EXISTS (
            SELECT 1
            FROM evidence.v_current_scheme_hierarchy AS hierarchy
            WHERE hierarchy.source_version_id IS NULL
               OR hierarchy.source_id IS NULL
               OR hierarchy.license_policy_id IS NULL
       )
       OR EXISTS (
            SELECT 1
            FROM evidence.v_current_scheme_concept_mapping AS mapping
            WHERE mapping.source_version_id IS NULL
               OR mapping.source_id IS NULL
               OR mapping.license_policy_id IS NULL
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_current_scheme_provenance_ck',
            MESSAGE = 'exactly two current source schemes plus versioned hierarchy and mappings are required';
    END IF;

    -- Legal polyhierarchy is positive coverage: at least one current node has
    -- two distinct parents in the project-authored scheme. The WCR public-page
    -- projection is intentionally flat and must never be treated as copied
    -- source hierarchy.
    IF NOT EXISTS (
        SELECT
            hierarchy.concept_scheme_id,
            hierarchy.child_node_id
        FROM evidence.v_current_scheme_hierarchy AS hierarchy
        JOIN kb.v_scheme_projection AS projection
          ON projection.concept_scheme_id = hierarchy.concept_scheme_id
         AND projection.concept_scheme_node_id = hierarchy.child_node_id
        WHERE hierarchy.concept_scheme_key =
            'scheme.project.coffee_sensory_kb_v0.2026-08-24'
          AND projection.concept_key = 'sensory.metallic'
        GROUP BY
            hierarchy.concept_scheme_id,
            hierarchy.child_node_id
        HAVING count(DISTINCT hierarchy.parent_node_id) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_scheme_polyhierarchy_fixture_ck',
            MESSAGE = 'Round 2A seed must demonstrate legal metallic polyhierarchy in the project scheme';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.lifecycle_status_code = 'active'
          AND concept.concept_type_code = 'sensory_attribute'
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.v_current_scheme_concept_mapping AS mapping
              WHERE mapping.concept_scheme_key =
                    'scheme.project.coffee_sensory_kb_v0.2026-08-24'
                AND mapping.concept_id = concept.concept_id
          )
    ) OR EXISTS (
        SELECT mapping.concept_id
        FROM evidence.v_current_scheme_concept_mapping AS mapping
        JOIN kb.concept AS concept
          ON concept.concept_id = mapping.concept_id
        WHERE mapping.concept_scheme_key =
                'scheme.project.coffee_sensory_kb_v0.2026-08-24'
          AND concept.lifecycle_status_code = 'active'
          AND concept.concept_type_code = 'sensory_attribute'
        GROUP BY mapping.concept_id
        HAVING count(*) <> 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_project_scheme_sensory_coverage_ck',
            MESSAGE = 'the project V0 scheme must map every active sensory attribute exactly once';
    END IF;

    IF (
        SELECT count(DISTINCT projection.concept_scheme_node_id)
        FROM kb.v_scheme_projection AS projection
        WHERE projection.concept_scheme_key =
            'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
    ) <> 24 OR (
        SELECT count(DISTINCT projection.concept_scheme_node_id)
        FROM kb.v_scheme_projection AS projection
        WHERE projection.concept_scheme_key =
            'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
          AND projection.concept_scheme_mapping_id IS NOT NULL
    ) <> 15 OR (
        SELECT count(DISTINCT projection.concept_scheme_node_id)
        FROM kb.v_scheme_projection AS projection
        WHERE projection.concept_scheme_key =
            'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
          AND projection.concept_scheme_mapping_id IS NULL
    ) <> 9 OR (
        SELECT count(*)
        FROM evidence.concept_scheme_edge AS edge
        JOIN evidence.concept_scheme AS scheme
          ON scheme.concept_scheme_id = edge.concept_scheme_id
        WHERE scheme.concept_scheme_key =
            'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
    ) <> 0 OR EXISTS (
        SELECT 1
        FROM evidence.v_current_scheme_concept_mapping AS mapping
        WHERE mapping.concept_scheme_key =
            'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
          AND lower(btrim(mapping.source_label)) IN (
              'butyric acid',
              'isovaleric acid',
              'fresh',
              'brown spice',
              'vanillin',
              'floral'
          )
    ) OR EXISTS (
        SELECT 1
        FROM evidence.v_current_scheme_concept_mapping AS mapping
        WHERE mapping.concept_scheme_key =
            'scheme.wcr.sensory_lexicon_2_0.public_24_partial'
          AND mapping.source_label LIKE '%/%'
          AND mapping.scheme_concept_mapping_role_code = 'equivalent_scope'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_wcr_partial_flat_projection_ck',
            MESSAGE = 'WCR partial must have 24 active nodes, reviewed safe mappings, no unsafe collapsed labels, and zero copied hierarchy edges';
    END IF;

    IF EXISTS (
        WITH RECURSIVE walk (
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
            FROM walk
            JOIN evidence.v_current_scheme_hierarchy AS hierarchy
              ON hierarchy.concept_scheme_id = walk.concept_scheme_id
             AND hierarchy.parent_node_id = walk.current_node_id
        )
        SELECT 1
        FROM walk
        WHERE start_node_id = current_node_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_scheme_hierarchy_acyclic_ck',
            MESSAGE = 'current source-scheme hierarchy contains a cycle';
    END IF;

    -- The unsupported narrower pink-grapefruit term remains a separate
    -- candidate identity and is never folded into active grapefruit.
    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS candidate
        CROSS JOIN kb.concept AS broader
        WHERE candidate.concept_key = 'sensory.pink_grapefruit'
          AND candidate.concept_type_code = 'sensory_attribute'
          AND candidate.lifecycle_status_code = 'candidate'
          AND broader.concept_key = 'sensory.grapefruit'
          AND broader.lifecycle_status_code = 'active'
          AND candidate.concept_id <> broader.concept_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_pink_grapefruit_candidate_identity_ck',
            MESSAGE = 'pink grapefruit must remain a distinct candidate rather than collapse into active grapefruit';
    END IF;

    -- Process metadata and perceived character remain separate identities.
    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS sensory
        CROSS JOIN kb.concept AS process
        WHERE sensory.concept_key = 'sensory.fermented_character'
          AND sensory.concept_type_code = 'sensory_attribute'
          AND process.concept_key = 'process.fermentation'
          AND process.concept_type_code = 'process_entity'
          AND sensory.concept_id <> process.concept_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_process_sensory_separation_ck',
            MESSAGE = 'fermented sensory character must remain separate from fermentation process metadata';
    END IF;

    -- Affective language is not a sensory attribute and cannot acquire a
    -- sensory calibration through a concept-dimension path in this seed.
    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'affective.pleasant'
          AND concept.concept_type_code = 'affective_term'
    ) OR EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        JOIN kb.concept_dimension_link AS link
          ON link.concept_id = concept.concept_id
        WHERE concept.concept_type_code = 'affective_term'
          AND link.lifecycle_status_code = 'active'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_affective_exclusion_ck',
            MESSAGE = 'affective terms must remain typed separately and outside sensory-dimension calibration';
    END IF;

    -- Candidate qualifiers remain vocabulary proposals, not vectors or
    -- empirical measurements. Qualitative metadata is allowed elsewhere.
    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'qualifier.bright'
          AND concept.concept_type_code = 'qualifier'
          AND concept.lifecycle_status_code = 'candidate'
    ) OR EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        LEFT JOIN evidence.empirical_pair_measurement AS pair_measurement
          ON pair_measurement.subject_concept_id = concept.concept_id
          OR pair_measurement.object_concept_id = concept.concept_id
        LEFT JOIN evidence.concept_projection_value AS projection
          ON projection.concept_id = concept.concept_id
        LEFT JOIN evidence.sensory_reference AS sensory_reference
          ON sensory_reference.concept_id = concept.concept_id
        LEFT JOIN evidence.reference_calibration AS calibration
          ON calibration.sensory_reference_id = sensory_reference.sensory_reference_id
        WHERE concept.concept_type_code = 'qualifier'
          AND concept.lifecycle_status_code = 'candidate'
          AND (
                pair_measurement.empirical_pair_measurement_id IS NOT NULL
                OR projection.concept_projection_value_id IS NOT NULL
                OR calibration.reference_calibration_id IS NOT NULL
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_candidate_qualifier_numeric_safety_ck',
            MESSAGE = 'candidate qualifiers must not carry empirical, projection, or calibration values';
    END IF;

    -- Winey deliberately demonstrates lexical ambiguity. Its two concept
    -- interpretations remain explicit, and at least one mapping opts into the
    -- controlled polysemy semantics.
    IF (
        SELECT count(DISTINCT lexicalization.concept_id)
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        WHERE expression.expression_key = 'expression.en.winey'
          AND lexicalization.lifecycle_status_code = 'active'
    ) <> 2 OR NOT EXISTS (
        SELECT 1
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
        WHERE expression.expression_key = 'expression.en.winey'
          AND lexicalization.lifecycle_status_code = 'active'
          AND mapping_type.allows_polysemy
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_winey_polysemy_ck',
            MESSAGE = 'winey must retain two explicit interpretations including a polysemy-aware mapping';
    END IF;

    RAISE NOTICE 'ROUND2A_SEMANTIC_PASS=true';
END
$round2a_semantic$;

COMMIT;

\echo ROUND2A_SEMANTIC_PASS=true
