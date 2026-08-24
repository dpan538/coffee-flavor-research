\set ON_ERROR_STOP on

-- Round 3B read models and validation. Round 3A's coverage view remains a
-- historical receipt and deliberately counts its own five-level scheme.

BEGIN;

CREATE OR REPLACE VIEW context.v_context_coverage AS
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
            WHERE scheme.roast_scheme_key =
                  'roast.scheme.project_v0_five_level'
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
    'Frozen Round 3A coverage receipt. The five-level count is historical and does not represent the current user projection.';

CREATE VIEW context.v_context_source_inventory AS
SELECT
    review.context_source_review_key,
    review.doi,
    review.version_label,
    review.license_spdx,
    review.commercial_use_allowed,
    review.derivative_use_allowed,
    review.redistribution_allowed,
    review.machine_use_allowed,
    review.context_acquisition_status_code,
    review.inspected_row_count,
    review.columns,
    review.geography,
    review.time_period,
    review.preparation_coverage,
    review.roast_coverage,
    review.sensory_coverage,
    review.known_limitations,
    count(file.context_source_file_id)::BIGINT AS frozen_file_count,
    COALESCE(sum(file.byte_count), 0)::BIGINT AS frozen_byte_count
FROM context.context_source_review AS review
LEFT JOIN context.context_source_file AS file
  ON file.context_source_review_id = review.context_source_review_id
GROUP BY review.context_source_review_id;

CREATE VIEW context.v_round3b_context_coverage AS
WITH selected_snapshot AS (
    SELECT context_dataset_snapshot_id
    FROM context.context_dataset_snapshot
    WHERE snapshot_key = 'context.snapshot.round3b_v1'
),
record_counts AS (
    SELECT
        count(*)::NUMERIC AS record_count,
        count(*) FILTER (WHERE preparation_status_code = 'known')::NUMERIC
            AS preparation_known_count,
        count(*) FILTER (WHERE roast_status_code = 'known')::NUMERIC
            AS roast_known_count,
        count(*) FILTER (
            WHERE context_coffee_mode_code = 'black_coffee'
        )::NUMERIC AS black_count,
        count(*) FILTER (
            WHERE context_coffee_mode_code = 'milk_coffee'
        )::NUMERIC AS milk_count,
        count(*) FILTER (WHERE has_strong_addition)::NUMERIC
            AS strong_addition_count
    FROM context.raw_context_record AS record
    JOIN selected_snapshot AS snapshot
      ON snapshot.context_dataset_snapshot_id =
         record.context_dataset_snapshot_id
),
source_counts AS (
    SELECT
        count(*)::NUMERIC AS reviewed_count,
        count(*) FILTER (
            WHERE context_acquisition_status_code = 'imported'
        )::NUMERIC AS imported_count
    FROM context.context_source_review
),
projection_counts AS (
    SELECT
        (SELECT count(*)::NUMERIC
         FROM context.v_current_user_preparation) AS c0_count,
        (SELECT count(*)::NUMERIC
         FROM context.v_current_user_roast) AS c1_count
)
SELECT metric.metric_key, metric.metric_value
FROM record_counts
CROSS JOIN source_counts
CROSS JOIN projection_counts
CROSS JOIN LATERAL (VALUES
    ('CONTEXT_DATA_SOURCE_COUNT', source_counts.reviewed_count),
    ('RIGHTS_CLEARED_IMPORTED_SOURCE_COUNT', source_counts.imported_count),
    ('CONTEXT_DATASET_ROW_COUNT', record_counts.record_count),
    ('PREPARATION_KNOWN_ROW_COUNT', record_counts.preparation_known_count),
    ('ROAST_KNOWN_ROW_COUNT', record_counts.roast_known_count),
    ('BLACK_COFFEE_ROW_COUNT', record_counts.black_count),
    ('MILK_COFFEE_ROW_COUNT', record_counts.milk_count),
    ('STRONG_ADDITION_EXCLUDED_ROW_COUNT', record_counts.strong_addition_count),
    ('CURRENT_USER_C0_FAMILY_COUNT', projection_counts.c0_count),
    ('CURRENT_USER_ROAST_LEVEL_COUNT', projection_counts.c1_count)
) AS metric(metric_key, metric_value);

CREATE VIEW context.v_held_out_normalization_metrics AS
WITH held AS (
    SELECT
        selected_case.context_domain,
        selected_case.expected_status_code,
        selected_case.expected_preparation_family_id,
        selected_case.expected_preparation_leaf_id,
        selected_case.expected_roast_category_id,
        result.predicted_status_code,
        result.predicted_preparation_family_id,
        result.predicted_preparation_leaf_id,
        result.predicted_roast_category_id,
        result.evaluation_grade,
        result.ordinal_error,
        result.gross_error
    FROM context.context_normalization_case AS selected_case
    JOIN context.context_normalization_result AS result
      ON result.context_normalization_case_id =
         selected_case.context_normalization_case_id
    WHERE selected_case.evaluation_split = 'held_out'
),
c0 AS (
    SELECT
        count(*)::NUMERIC AS n,
        count(*) FILTER (
            WHERE predicted_preparation_family_id IS NOT NULL
        )::NUMERIC AS family_covered,
        count(*) FILTER (
            WHERE predicted_preparation_leaf_id IS NOT NULL
        )::NUMERIC AS leaf_covered,
        count(*) FILTER (
            WHERE predicted_status_code = 'reported_unresolved'
        )::NUMERIC AS unresolved,
        count(*) FILTER (WHERE evaluation_grade = '1')::NUMERIC AS ambiguous,
        count(*) FILTER (WHERE gross_error)::NUMERIC AS gross_error
    FROM held WHERE context_domain = 'preparation'
),
c1 AS (
    SELECT
        count(*)::NUMERIC AS n,
        count(*) FILTER (WHERE expected_status_code = 'known')::NUMERIC
            AS known_n,
        count(*) FILTER (
            WHERE expected_status_code = 'known' AND ordinal_error = 0
        )::NUMERIC AS exact,
        count(*) FILTER (
            WHERE expected_status_code = 'known' AND ordinal_error <= 1
        )::NUMERIC AS adjacent,
        count(*) FILTER (
            WHERE expected_status_code = 'known' AND gross_error
        )::NUMERIC AS gross_error,
        count(*) FILTER (
            WHERE predicted_roast_category_id IS NOT NULL
        )::NUMERIC AS covered,
        count(*) FILTER (
            WHERE predicted_status_code = 'reported_unresolved'
        )::NUMERIC AS unresolved
    FROM held WHERE context_domain = 'roast'
)
SELECT metric.metric_key, metric.metric_value
FROM c0
CROSS JOIN c1
CROSS JOIN LATERAL (VALUES
    ('C0_HELD_OUT_SIZE', c0.n),
    ('C0_FAMILY_COVERAGE', round(c0.family_covered / NULLIF(c0.n, 0), 4)),
    ('C0_LEAF_COVERAGE', round(c0.leaf_covered / NULLIF(c0.n, 0), 4)),
    ('C0_UNRESOLVED_RATE', round(c0.unresolved / NULLIF(c0.n, 0), 4)),
    ('C0_AMBIGUOUS_RATE', round(c0.ambiguous / NULLIF(c0.n, 0), 4)),
    ('C0_GROSS_ERROR_RATE', round(c0.gross_error / NULLIF(c0.n, 0), 4)),
    ('C1_HELD_OUT_SIZE', c1.n),
    ('C1_EXACT_CATEGORY_AGREEMENT', round(c1.exact / NULLIF(c1.known_n, 0), 4)),
    ('C1_ADJACENT_CATEGORY_AGREEMENT', round(c1.adjacent / NULLIF(c1.known_n, 0), 4)),
    ('C1_GROSS_CATEGORY_ERROR', round(c1.gross_error / NULLIF(c1.known_n, 0), 4)),
    ('C1_NORMALIZATION_COVERAGE', round(c1.covered / NULLIF(c1.n, 0), 4)),
    ('C1_UNRESOLVED_RATE', round(c1.unresolved / NULLIF(c1.n, 0), 4))
) AS metric(metric_key, metric_value);

COMMENT ON VIEW context.v_held_out_normalization_metrics IS
    'Held-out C0/C1 label-normalization metrics. These are not coffee flavor accuracy or sensory ranking metrics.';

CREATE VIEW context.v_context_signal_sufficiency AS
SELECT
    (statistic.statistic_value ->>
        'preparation_signal_data_sufficient')::BOOLEAN
        AS preparation_signal_data_sufficient,
    (statistic.statistic_value ->>
        'roast_signal_data_sufficient')::BOOLEAN
        AS roast_signal_data_sufficient,
    (statistic.statistic_value ->>
        'preparation_roast_interaction_data_sufficient')::BOOLEAN
        AS preparation_roast_interaction_data_sufficient,
    (statistic.statistic_value ->>
        'milk_mode_data_sufficient')::BOOLEAN
        AS milk_mode_data_sufficient,
    statistic.statistic_value ->> 'preparation_signal_result'
        AS preparation_signal_result,
    statistic.statistic_value ->> 'roast_signal_result'
        AS roast_signal_result,
    statistic.statistic_value ->> 'preparation_roast_interaction_result'
        AS preparation_roast_interaction_result,
    statistic.statistic_value ->> 'milk_mode_result'
        AS milk_mode_result
FROM audit.context_statistic AS statistic
WHERE statistic.context_statistic_key =
      'context.statistic.round3b.signal_sufficiency';

-- Preserve the Round 3A validation receipt as a historical contract. Its
-- original function remains queryable under a legacy name; only the four
-- checks whose implementation depended on "currently selected" are pinned
-- to the immutable V0 scheme after V1 is promoted.
ALTER FUNCTION audit.run_round3a_validation_queries()
    RENAME TO run_round3a_validation_queries_legacy;

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
WITH checks AS (
    SELECT legacy.check_key, legacy.violation_count
    FROM audit.run_round3a_validation_queries_legacy() AS legacy
    WHERE legacy.check_key NOT IN (
        'project_roast_target_count',
        'project_roast_level_count',
        'project_roast_ordinal_gap',
        'roast_mapping_outside_project_target'
    )

    UNION ALL
    SELECT 'project_roast_target_count',
           CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM context.roast_scheme
    WHERE roast_scheme_key = 'roast.scheme.project_v0_five_level'

    UNION ALL
    SELECT 'project_roast_level_count', abs(count(*) - 5)::BIGINT
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    WHERE scheme.roast_scheme_key = 'roast.scheme.project_v0_five_level'

    UNION ALL
    SELECT 'project_roast_ordinal_gap',
           CASE WHEN min(category.ordinal_position) = 1
                  AND max(category.ordinal_position) = count(*)
                THEN 0 ELSE 1 END::BIGINT
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    WHERE scheme.roast_scheme_key = 'roast.scheme.project_v0_five_level'

    UNION ALL
    SELECT 'roast_mapping_outside_project_target', count(*)::BIGINT
    FROM context.roast_category_mapping AS mapping
    JOIN evidence.source_version AS source_version
      ON source_version.source_version_id = mapping.source_version_id
    JOIN context.roast_category AS target
      ON target.roast_category_id = mapping.normalized_roast_category_id
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = target.roast_scheme_id
    WHERE source_version.source_version_key =
          'source_version.project.context_v0.2026-08-25'
      AND scheme.roast_scheme_key <>
          'roast.scheme.project_v0_five_level'
)
SELECT checks.check_key, checks.violation_count,
       checks.violation_count = 0 AS passed
FROM checks;
$run_round3a_validation_queries$;

COMMENT ON FUNCTION audit.run_round3a_validation_queries() IS
    'Frozen Round 3A validation receipt. V0 roast checks remain pinned to the preserved five-level scheme after the forward-only V1 promotion.';

CREATE FUNCTION audit.run_round3b_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3b_validation_queries$
WITH checks(check_key, violation_count) AS (
    SELECT 'exactly_one_current_user_roast_scheme',
           abs(count(*) - 1)::BIGINT
    FROM context.roast_scheme
    WHERE is_project_normalized_target
      AND lifecycle_status_code = 'active'

    UNION ALL
    SELECT 'current_user_roast_level_count_seven',
           abs(count(*) - 7)::BIGINT
    FROM context.v_current_user_roast

    UNION ALL
    SELECT 'current_user_roast_required_middle_distinctions',
           (3 - count(*))::BIGINT
    FROM context.v_current_user_roast
    WHERE interaction_code IN ('medium_light', 'medium', 'medium_dark')

    UNION ALL
    SELECT 'current_user_roast_dense_ordinal_order', count(*)::BIGINT
    FROM (
        SELECT ordinal_position,
               row_number() OVER (ORDER BY ordinal_position) AS expected_position
        FROM context.v_current_user_roast
    ) AS ordered
    WHERE ordinal_position <> expected_position

    UNION ALL
    SELECT 'historical_five_level_scheme_preserved',
           CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM context.roast_scheme
    WHERE roast_scheme_key = 'roast.scheme.project_v0_five_level'
      AND lifecycle_status_code = 'deprecated'
      AND is_project_normalized_target IS FALSE

    UNION ALL
    SELECT 'historical_five_level_category_count',
           abs(count(*) - 5)::BIGINT
    FROM context.roast_category AS category
    JOIN context.roast_scheme AS scheme
      ON scheme.roast_scheme_id = category.roast_scheme_id
    WHERE scheme.roast_scheme_key = 'roast.scheme.project_v0_five_level'

    UNION ALL
    SELECT 'current_user_c0_family_count', abs(count(*) - 8)::BIGINT
    FROM context.v_current_user_preparation

    UNION ALL
    SELECT 'current_user_c0_excludes_observation_status', count(*)::BIGINT
    FROM context.v_current_user_preparation
    WHERE preparation_concept_key ~
          '(^|[._])(unknown|unsure|not_reported|reported_unresolved|not_applicable)([._]|$)'
       OR lower(candidate_user_label_en) IN (
           'unknown', 'unsure', 'i don''t know', 'not reported',
           'reported unresolved', 'not applicable'
       )

    UNION ALL
    SELECT 'database_unknown_preparation_state_preserved',
           CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM ref.context_value_status
    WHERE context_value_status_code = 'unknown'

    UNION ALL
    SELECT 'protected_roast_labels_abstain', count(*)::BIGINT
    FROM context.context_lexical_rule
    WHERE normalized_expression IN (
        'filter roast', 'espresso roast', 'omniroast', 'nordic roast',
        'city roast', 'city+', 'full city', 'vienna roast',
        'french roast', 'italian roast'
    )
      AND normalized_roast_category_id IS NOT NULL

    UNION ALL
    SELECT 'no_interval_distance_encoding', count(*)::BIGINT
    FROM information_schema.columns
    WHERE table_schema = 'context'
      AND table_name IN ('roast_scheme', 'roast_category')
      AND column_name ~ '(distance|interval|equal_step)'

    UNION ALL
    SELECT 'frozen_imported_context_row_count',
           abs(count(*) - 4817)::BIGINT
    FROM context.raw_context_record AS record
    JOIN context.context_dataset_snapshot AS snapshot
      ON snapshot.context_dataset_snapshot_id =
         record.context_dataset_snapshot_id
    WHERE snapshot.snapshot_key = 'context.snapshot.round3b_v1'
      AND snapshot.is_frozen

    UNION ALL
    SELECT 'rights_cleared_imported_source_count',
           abs(count(*) - 2)::BIGINT
    FROM context.context_source_review
    WHERE context_acquisition_status_code = 'imported'
      AND commercial_use_allowed
      AND derivative_use_allowed
      AND redistribution_allowed
      AND machine_use_allowed

    UNION ALL
    SELECT 'inaccessible_source_not_imported',
           CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM context.context_source_review
    WHERE doi = '10.5061/dryad.v15dv423h'
      AND context_acquisition_status_code = 'not_imported_inaccessible'
      AND dataset_id IS NULL

    UNION ALL
    SELECT 'source_file_hash_inventory', abs(count(*) - 6)::BIGINT
    FROM context.context_source_file
    WHERE sha256 ~ '^[0-9a-f]{64}$'

    UNION ALL
    SELECT 'normalization_case_count', abs(count(*) - 102)::BIGINT
    FROM context.context_normalization_case

    UNION ALL
    SELECT 'normalization_result_count', abs(count(*) - 102)::BIGINT
    FROM context.context_normalization_result

    UNION ALL
    SELECT 'held_out_case_count', abs(count(*) - 17)::BIGINT
    FROM context.context_normalization_case
    WHERE evaluation_split = 'held_out'

    UNION ALL
    SELECT 'held_out_gross_error_count', count(*)::BIGINT
    FROM context.context_normalization_case AS selected_case
    JOIN context.context_normalization_result AS result
      ON result.context_normalization_case_id =
         selected_case.context_normalization_case_id
    WHERE selected_case.evaluation_split = 'held_out'
      AND result.gross_error

    UNION ALL
    SELECT 'signal_sufficiency_no_forced_claim', count(*)::BIGINT
    FROM context.v_context_signal_sufficiency
    WHERE preparation_signal_data_sufficient
       OR roast_signal_data_sufficient
       OR preparation_roast_interaction_data_sufficient
       OR milk_mode_data_sufficient

    UNION ALL
    SELECT 'context_not_inserted_into_sensory_ontology', count(*)::BIGINT
    FROM kb.concept
    WHERE concept_key LIKE 'preparation.%'
       OR concept_key LIKE 'roast.%'
)
SELECT check_key, violation_count, violation_count = 0 AS passed
FROM checks;
$run_round3b_validation_queries$;

COMMIT;
