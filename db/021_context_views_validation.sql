\set ON_ERROR_STOP on

-- Round 3A governed read models and validation. These projections expose
-- uncertainty and source-scheme boundaries; they never emit sensory weights.

BEGIN;

CREATE VIEW context.v_preparation_taxonomy AS
SELECT
    concept.preparation_concept_id,
    concept.preparation_concept_key,
    concept.preparation_concept_type_code,
    concept.lifecycle_status_code,
    concept.preferred_label,
    concept.description,
    concept.c0_top_level,
    concept.c0_second_level,
    COALESCE(parents.parent_count, 0::BIGINT) AS direct_parent_count,
    COALESCE(parents.parent_keys, ARRAY[]::TEXT[]) AS direct_parent_keys,
    COALESCE(children.child_count, 0::BIGINT) AS direct_child_count,
    COALESCE(support.support_count, 0::BIGINT) AS support_count,
    COALESCE(support.external_support_count, 0::BIGINT) AS external_support_count
FROM context.preparation_concept AS concept
LEFT JOIN LATERAL (
    SELECT
        count(*)::BIGINT AS parent_count,
        array_agg(parent.preparation_concept_key ORDER BY parent.preparation_concept_key)
            AS parent_keys
    FROM context.preparation_relation AS relation
    JOIN context.preparation_concept AS parent
      ON parent.preparation_concept_id = relation.subject_preparation_concept_id
    WHERE relation.object_preparation_concept_id = concept.preparation_concept_id
      AND relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'
) AS parents ON TRUE
LEFT JOIN LATERAL (
    SELECT count(*)::BIGINT AS child_count
    FROM context.preparation_relation AS relation
    WHERE relation.subject_preparation_concept_id = concept.preparation_concept_id
      AND relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'
) AS children ON TRUE
LEFT JOIN LATERAL (
    SELECT
        count(*)::BIGINT AS support_count,
        count(*) FILTER (
            WHERE source.source_key <>
                  'source.project.coffee_sensory_kb_v0_round3a_context'
        )::BIGINT AS external_support_count
    FROM context.preparation_concept_support AS concept_support
    JOIN evidence.source_version AS source_version
      ON source_version.source_version_id = concept_support.source_version_id
    JOIN evidence.source AS source
      ON source.source_id = source_version.source_id
    WHERE concept_support.preparation_concept_id = concept.preparation_concept_id
) AS support ON TRUE;

COMMENT ON VIEW context.v_preparation_taxonomy IS
    'Preparation concepts with direct polyhierarchy and provenance counts. Family placement is project organization, not universal perceptual geometry.';

CREATE VIEW context.v_roast_normalization AS
SELECT
    source_scheme.roast_scheme_id AS source_roast_scheme_id,
    source_scheme.roast_scheme_key AS source_roast_scheme_key,
    source_scheme.roast_scheme_kind_code,
    source_scheme.lifecycle_status_code AS source_scheme_lifecycle_status_code,
    source_category.roast_category_id AS source_roast_category_id,
    source_category.roast_category_key AS source_roast_category_key,
    source_category.preferred_label AS source_label,
    source_category.ordinal_position AS source_ordinal_position,
    mapping.roast_category_mapping_id,
    mapping.roast_category_mapping_key,
    mapping.context_mapping_certainty_code,
    target_scheme.roast_scheme_key AS normalized_roast_scheme_key,
    target_category.roast_category_id AS normalized_roast_category_id,
    target_category.roast_category_key AS normalized_roast_category_key,
    target_category.preferred_label AS normalized_label,
    target_category.ordinal_position AS normalized_ordinal_position,
    source_version.source_version_key AS mapping_source_version_key,
    mapping.context_assertion_role_code,
    mapping.evidence_locator,
    (mapping.roast_category_mapping_id IS NOT NULL) AS is_normalized
FROM context.roast_category AS source_category
JOIN context.roast_scheme AS source_scheme
  ON source_scheme.roast_scheme_id = source_category.roast_scheme_id
LEFT JOIN context.roast_category_mapping AS mapping
  ON mapping.source_roast_category_id = source_category.roast_category_id
 AND mapping.lifecycle_status_code = 'active'
LEFT JOIN context.roast_category AS target_category
  ON target_category.roast_category_id = mapping.normalized_roast_category_id
LEFT JOIN context.roast_scheme AS target_scheme
  ON target_scheme.roast_scheme_id = target_category.roast_scheme_id
LEFT JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = mapping.source_version_id;

COMMENT ON VIEW context.v_roast_normalization IS
    'Source-scheme-complete roast projection. Unmapped labels remain visible and do not acquire invented numeric or normalized boundaries.';

CREATE VIEW context.v_observation_context AS
SELECT
    observation_context.observation_context_id,
    observation_context.observation_context_key,
    document.captured_document_id,
    document.captured_document_key,
    selected_corpus.corpus_id,
    selected_corpus.corpus_key,
    document.industry_product_id,
    observation_context.preparation_status_code,
    preparation_expression.expression_text AS reported_preparation_label,
    preparation.preparation_concept_key AS normalized_preparation_key,
    preparation.preferred_label AS normalized_preparation_label,
    observation_context.roast_status_code,
    roast_expression.expression_text AS reported_roast_label,
    roast_category.roast_category_key AS normalized_roast_key,
    roast_category.preferred_label AS normalized_roast_label,
    observation_context.addition_presence_code,
    COALESCE(additions.addition_count, 0::BIGINT) AS addition_count,
    COALESCE(additions.strong_interference_count, 0::BIGINT)
        AS strong_interference_addition_count,
    observation_context.context_assertion_role_code,
    observation_context.evidence_locator,
    observation_context.notes
FROM context.observation_context AS observation_context
JOIN corpus.captured_document AS document
  ON document.captured_document_id = observation_context.captured_document_id
JOIN corpus.corpus AS selected_corpus
  ON selected_corpus.corpus_id = document.corpus_id
LEFT JOIN context.preparation_expression AS preparation_expression
  ON preparation_expression.preparation_expression_id =
     observation_context.reported_preparation_expression_id
LEFT JOIN context.preparation_concept AS preparation
  ON preparation.preparation_concept_id =
     observation_context.normalized_preparation_concept_id
LEFT JOIN context.roast_expression AS roast_expression
  ON roast_expression.roast_expression_id =
     observation_context.reported_roast_expression_id
LEFT JOIN context.roast_category AS roast_category
  ON roast_category.roast_category_id =
     observation_context.normalized_roast_category_id
LEFT JOIN LATERAL (
    SELECT
        count(*)::BIGINT AS addition_count,
        count(*) FILTER (
            WHERE addition_type.is_strong_flavour_interference
        )::BIGINT AS strong_interference_count
    FROM context.observation_addition AS observation_addition
    JOIN context.beverage_addition_type AS addition_type
      ON addition_type.beverage_addition_type_id =
         observation_addition.beverage_addition_type_id
    WHERE observation_addition.observation_context_id =
          observation_context.observation_context_id
) AS additions ON TRUE;

COMMENT ON VIEW context.v_observation_context IS
    'Corpus-document context with reported and normalized preparation/roast values kept distinct and additions exposed as serving context.';

CREATE VIEW context.v_unresolved_context_labels AS
SELECT
    'preparation'::TEXT AS context_domain,
    expression.preparation_expression_key AS expression_key,
    expression.language_tag_code,
    expression.expression_text,
    expression.normalized_text,
    expression.lifecycle_status_code
FROM context.preparation_expression AS expression
WHERE NOT EXISTS (
    SELECT 1
    FROM context.preparation_expression_mapping AS mapping
    WHERE mapping.preparation_expression_id = expression.preparation_expression_id
      AND mapping.lifecycle_status_code = 'active'
)
UNION ALL
SELECT
    'roast'::TEXT,
    expression.roast_expression_key,
    expression.language_tag_code,
    expression.expression_text,
    expression.normalized_text,
    expression.lifecycle_status_code
FROM context.roast_expression AS expression
WHERE NOT EXISTS (
    SELECT 1
    FROM context.roast_expression_mapping AS mapping
    WHERE mapping.roast_expression_id = expression.roast_expression_id
      AND mapping.lifecycle_status_code = 'active'
);

COMMENT ON VIEW context.v_unresolved_context_labels IS
    'Explicit preparation and roast labels that have no active safe normalization; nearest labels are never forced.';

CREATE VIEW context.v_context_coverage AS
WITH corpus_totals AS (
    SELECT count(*)::NUMERIC AS document_count
    FROM corpus.captured_document AS document
    JOIN corpus.corpus AS selected_corpus
      ON selected_corpus.corpus_id = document.corpus_id
    WHERE selected_corpus.corpus_key = 'corpus.firstbloom_a6cb002_pilot_v1'
),
context_totals AS (
    SELECT
        count(*)::NUMERIC AS context_count,
        count(*) FILTER (WHERE preparation_status_code = 'known')::NUMERIC
            AS preparation_known_count,
        count(*) FILTER (WHERE roast_status_code = 'known')::NUMERIC
            AS roast_known_count
    FROM context.observation_context AS observation_context
    JOIN corpus.captured_document AS document
      ON document.captured_document_id = observation_context.captured_document_id
    JOIN corpus.corpus AS selected_corpus
      ON selected_corpus.corpus_id = document.corpus_id
    WHERE selected_corpus.corpus_key = 'corpus.firstbloom_a6cb002_pilot_v1'
),
preparation_counts AS (
    SELECT
        count(*) FILTER (
            WHERE concept.preparation_concept_type_code = 'family'
              AND concept.lifecycle_status_code = 'active'
        )::NUMERIC AS family_count,
        count(*) FILTER (
            WHERE concept.lifecycle_status_code = 'active'
              AND NOT EXISTS (
                    SELECT 1
                    FROM context.preparation_relation AS relation
                    WHERE relation.subject_preparation_concept_id =
                          concept.preparation_concept_id
                      AND relation.context_relation_type_code = 'broader_than'
                      AND relation.lifecycle_status_code = 'active'
              )
        )::NUMERIC AS leaf_count,
        count(*) FILTER (
            WHERE concept.c0_top_level
              AND concept.lifecycle_status_code = 'active'
        )::NUMERIC AS c0_top_level_count
    FROM context.preparation_concept AS concept
),
roast_counts AS (
    SELECT
        (SELECT count(*)::NUMERIC FROM context.roast_scheme) AS scheme_count,
        count(*) FILTER (
            WHERE scheme.is_project_normalized_target
              AND category.lifecycle_status_code = 'active'
        )::NUMERIC AS user_level_count
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
),
unresolved_counts AS (
    SELECT
        count(*) FILTER (WHERE context_domain = 'preparation')::NUMERIC
            AS preparation_unresolved_count,
        count(*) FILTER (WHERE context_domain = 'roast')::NUMERIC
            AS roast_unresolved_count
    FROM context.v_unresolved_context_labels
),
rights_counts AS (
    SELECT count(*)::NUMERIC AS rights_cleared_source_count
    FROM evidence.dataset AS dataset
    JOIN evidence.source_version AS source_version
      ON source_version.source_version_id = dataset.source_version_id
    JOIN evidence.license_policy AS policy
      ON policy.license_policy_id = source_version.license_policy_id
    WHERE dataset.dataset_key IN (
        'dataset.liang_2024_full_immersion_context',
        'dataset.cotter_2020_black_coffee_context',
        'dataset.cotter_2023_acids_meta_analysis'
    )
      AND policy.rights_status_code = 'verified'
      AND policy.production_export_allowed
)
SELECT metric.metric_key, metric.metric_value
FROM corpus_totals
CROSS JOIN context_totals
CROSS JOIN preparation_counts
CROSS JOIN roast_counts
CROSS JOIN unresolved_counts
CROSS JOIN rights_counts
CROSS JOIN LATERAL (VALUES
    ('CURRENT_CORPUS_DOCUMENT_COUNT', corpus_totals.document_count),
    ('CONTEXT_OBSERVATION_COUNT', context_totals.context_count),
    ('PREPARATION_KNOWN_DOCUMENT_COUNT', context_totals.preparation_known_count),
    ('ROAST_KNOWN_DOCUMENT_COUNT', context_totals.roast_known_count),
    ('CURRENT_CORPUS_PREPARATION_COVERAGE',
        CASE WHEN corpus_totals.document_count = 0 THEN 0::NUMERIC
             ELSE round(context_totals.preparation_known_count /
                        corpus_totals.document_count, 4) END),
    ('CURRENT_CORPUS_ROAST_COVERAGE',
        CASE WHEN corpus_totals.document_count = 0 THEN 0::NUMERIC
             ELSE round(context_totals.roast_known_count /
                        corpus_totals.document_count, 4) END),
    ('PREPARATION_FAMILY_COUNT', preparation_counts.family_count),
    ('PREPARATION_LEAF_COUNT', preparation_counts.leaf_count),
    ('RECOMMENDED_C0_TOP_LEVEL_CHOICE_COUNT', preparation_counts.c0_top_level_count),
    ('ROAST_SCHEME_COUNT', roast_counts.scheme_count),
    ('RECOMMENDED_USER_ROAST_LEVEL_COUNT', roast_counts.user_level_count),
    ('UNRESOLVED_PREPARATION_LABEL_COUNT', unresolved_counts.preparation_unresolved_count),
    ('UNRESOLVED_ROAST_LABEL_COUNT', unresolved_counts.roast_unresolved_count),
    ('RIGHTS_CLEARED_CONTEXT_SOURCE_COUNT', rights_counts.rights_cleared_source_count)
) AS metric(metric_key, metric_value);

COMMENT ON VIEW context.v_context_coverage IS
    'Round 3A coverage receipt. Coverage counts only explicit normalized context rows and never infers preparation or roast from product names.';

CREATE FUNCTION audit.run_round3a_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3a_validation_queries$
WITH RECURSIVE preparation_paths(ancestor_id, descendant_id) AS (
    SELECT
        relation.subject_preparation_concept_id,
        relation.object_preparation_concept_id
    FROM context.preparation_relation AS relation
    WHERE relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'
    UNION
    SELECT
        path.ancestor_id,
        relation.object_preparation_concept_id
    FROM preparation_paths AS path
    JOIN context.preparation_relation AS relation
      ON relation.subject_preparation_concept_id = path.descendant_id
    WHERE relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'
),
addition_paths(ancestor_id, descendant_id) AS (
    SELECT parent_beverage_addition_type_id, beverage_addition_type_id
    FROM context.beverage_addition_type
    WHERE parent_beverage_addition_type_id IS NOT NULL
    UNION
    SELECT path.ancestor_id, addition.beverage_addition_type_id
    FROM addition_paths AS path
    JOIN context.beverage_addition_type AS addition
      ON addition.parent_beverage_addition_type_id = path.descendant_id
),
checks(check_key, violation_count) AS (
    SELECT
        'active_preparation_without_provenance',
        count(*)::BIGINT
    FROM context.preparation_concept AS concept
    WHERE concept.lifecycle_status_code = 'active'
      AND NOT EXISTS (
          SELECT 1 FROM context.preparation_concept_support AS support
          WHERE support.preparation_concept_id = concept.preparation_concept_id
      )

    UNION ALL
    SELECT 'active_preparation_relation_without_source', count(*)::BIGINT
    FROM context.preparation_relation AS relation
    WHERE relation.lifecycle_status_code = 'active'
      AND (relation.source_version_id IS NULL OR relation.evidence_locator = '')

    UNION ALL
    SELECT 'preparation_hierarchy_cycle', count(*)::BIGINT
    FROM preparation_paths WHERE ancestor_id = descendant_id

    UNION ALL
    SELECT 'beverage_addition_hierarchy_cycle', count(*)::BIGINT
    FROM addition_paths WHERE ancestor_id = descendant_id

    UNION ALL
    SELECT 'unexpected_c0_top_level_count',
           abs(count(*) - 8)::BIGINT
    FROM context.preparation_concept
    WHERE c0_top_level AND lifecycle_status_code = 'active'

    UNION ALL
    SELECT 'aeropress_missing_polyhierarchy',
           CASE WHEN count(*) >= 2 THEN 0 ELSE 1 END::BIGINT
    FROM context.preparation_relation AS relation
    JOIN context.preparation_concept AS concept
      ON concept.preparation_concept_id = relation.object_preparation_concept_id
    WHERE concept.preparation_concept_key = 'preparation.method.aeropress'
      AND relation.context_relation_type_code = 'broader_than'
      AND relation.lifecycle_status_code = 'active'

    UNION ALL
    SELECT 'americano_long_black_identity_collapse',
           CASE WHEN count(DISTINCT preparation_concept_id) = 2 THEN 0 ELSE 1 END::BIGINT
    FROM context.preparation_concept
    WHERE preparation_concept_key IN (
        'preparation.beverage.americano',
        'preparation.beverage.long_black'
    )

    UNION ALL
    SELECT 'unknown_modeled_as_taxonomy_value', count(*)::BIGINT
    FROM (
        SELECT preparation_concept_key AS stable_key
        FROM context.preparation_concept
        WHERE preparation_concept_key LIKE '%unknown%'
        UNION ALL
        SELECT roast_category_key
        FROM context.roast_category
        WHERE roast_category_key LIKE '%unknown%'
           OR source_category_code = 'unknown'
    ) AS prohibited_unknown

    UNION ALL
    SELECT 'project_roast_target_count', abs(count(*) - 1)::BIGINT
    FROM context.roast_scheme WHERE is_project_normalized_target

    UNION ALL
    SELECT 'project_roast_level_count', abs(count(*) - 5)::BIGINT
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    WHERE scheme.is_project_normalized_target
      AND category.lifecycle_status_code = 'active'

    UNION ALL
    SELECT 'project_roast_ordinal_gap',
           CASE WHEN min(category.ordinal_position) = 1
                  AND max(category.ordinal_position) = count(*)
                THEN 0 ELSE 1 END::BIGINT
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    WHERE scheme.is_project_normalized_target
      AND category.lifecycle_status_code = 'active'

    UNION ALL
    SELECT 'roast_mapping_outside_project_target', count(*)::BIGINT
    FROM context.roast_category_mapping AS mapping
    JOIN context.roast_category AS target
      ON target.roast_category_id = mapping.normalized_roast_category_id
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = target.roast_scheme_id
    WHERE NOT scheme.is_project_normalized_target

    UNION ALL
    SELECT 'terminology_scheme_with_invented_ordinal', count(*)::BIGINT
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    JOIN ref.roast_scheme_kind AS kind
      ON kind.roast_scheme_kind_code = scheme.roast_scheme_kind_code
    WHERE NOT kind.is_ordinal AND category.ordinal_position IS NOT NULL

    UNION ALL
    SELECT 'active_context_mapping_without_provenance', count(*)::BIGINT
    FROM (
        SELECT source_version_id, evidence_locator
        FROM context.preparation_expression_mapping
        WHERE lifecycle_status_code = 'active'
        UNION ALL
        SELECT source_version_id, evidence_locator
        FROM context.roast_expression_mapping
        WHERE lifecycle_status_code = 'active'
        UNION ALL
        SELECT source_version_id, evidence_locator
        FROM context.roast_category_mapping
        WHERE lifecycle_status_code = 'active'
    ) AS mapping
    WHERE mapping.source_version_id IS NULL OR mapping.evidence_locator = ''

    UNION ALL
    SELECT 'present_addition_status_without_rows', count(*)::BIGINT
    FROM context.observation_context AS observation_context
    WHERE observation_context.addition_presence_code = 'present'
      AND NOT EXISTS (
          SELECT 1 FROM context.observation_addition AS addition
          WHERE addition.observation_context_id = observation_context.observation_context_id
      )

    UNION ALL
    SELECT 'addition_row_without_present_status', count(*)::BIGINT
    FROM context.observation_addition AS addition
    JOIN context.observation_context AS observation_context
      ON observation_context.observation_context_id = addition.observation_context_id
    WHERE observation_context.addition_presence_code <> 'present'

    UNION ALL
    SELECT 'addition_leaked_into_canonical_kb', count(*)::BIGINT
    FROM kb.concept WHERE concept_key LIKE 'addition.%'

    UNION ALL
    SELECT 'context_contains_sensory_score_column', count(*)::BIGINT
    FROM information_schema.columns
    WHERE table_schema = 'context'
      AND (
        column_name LIKE '%sensory%score%'
        OR column_name LIKE '%flavor%probability%'
        OR column_name LIKE '%sensory%weight%'
      )

    UNION ALL
    SELECT 'historical_ontology_concept_count_changed',
           abs(count(*) - 130)::BIGINT
    FROM kb.concept

    UNION ALL
    SELECT 'historical_active_sensory_count_changed',
           abs(count(*) - 92)::BIGINT
    FROM kb.concept
    WHERE concept_type_code = 'sensory_attribute'
      AND lifecycle_status_code = 'active'

    UNION ALL
    SELECT 'historical_corpus_document_count_changed',
           abs(count(*) - 2474)::BIGINT
    FROM corpus.captured_document AS document
    JOIN corpus.corpus AS selected_corpus
      ON selected_corpus.corpus_id = document.corpus_id
    WHERE selected_corpus.corpus_key = 'corpus.firstbloom_a6cb002_pilot_v1'

    UNION ALL
    SELECT 'historical_corpus_observation_count_changed',
           abs(count(*) - 6818)::BIGINT
    FROM corpus.raw_observation AS observation
    JOIN corpus.captured_document AS document
      ON document.captured_document_id = observation.captured_document_id
    JOIN corpus.corpus AS selected_corpus
      ON selected_corpus.corpus_id = document.corpus_id
    WHERE selected_corpus.corpus_key = 'corpus.firstbloom_a6cb002_pilot_v1'

    UNION ALL
    SELECT 'rights_cleared_context_dataset_count',
           abs(count(*) - 3)::BIGINT
    FROM evidence.dataset AS dataset
    JOIN evidence.source_version AS source_version
      ON source_version.source_version_id = dataset.source_version_id
    JOIN evidence.license_policy AS policy
      ON policy.license_policy_id = source_version.license_policy_id
    WHERE dataset.dataset_key IN (
        'dataset.liang_2024_full_immersion_context',
        'dataset.cotter_2020_black_coffee_context',
        'dataset.cotter_2023_acids_meta_analysis'
    )
      AND policy.rights_status_code = 'verified'
      AND policy.production_export_allowed
)
SELECT checks.check_key, checks.violation_count,
       checks.violation_count = 0 AS passed
FROM checks;
$run_round3a_validation_queries$;

COMMENT ON FUNCTION audit.run_round3a_validation_queries() IS
    'Round 3A context integrity gate: hierarchy, explicit unknowns, scheme isolation, provenance, ontology/corpus preservation, additions, rights, and absence of invented sensory scores.';

COMMIT;
