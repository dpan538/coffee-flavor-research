\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Machine-runnable, expected-zero validation contract.  These checks are
-- deliberately redundant with constraints: constraints prevent new invalid
-- writes, while this function makes the resulting database state auditable.

BEGIN;

CREATE FUNCTION audit.run_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_validation_queries$
    WITH RECURSIVE
    active_relations AS (
        SELECT
            relation.concept_relation_id,
            relation.relation_type_code,
            relation.subject_concept_id,
            relation.object_concept_id
        FROM kb.concept_relation AS relation
        WHERE relation.lifecycle_status_code = 'active'
    ),
    current_relations AS (
        SELECT
            relation.concept_relation_id,
            relation.relation_type_code,
            relation.subject_concept_id,
            relation.object_concept_id
        FROM kb.concept_relation AS relation
        WHERE relation.lifecycle_status_code = 'active'
          AND relation.valid_from <= CURRENT_TIMESTAMP
          AND (
              relation.valid_until IS NULL
              OR relation.valid_until > CURRENT_TIMESTAMP
          )
    ),
    hierarchy_walk (
        relation_type_code,
        start_concept_id,
        current_concept_id
    ) AS (
        SELECT
            relation.relation_type_code,
            relation.subject_concept_id,
            relation.object_concept_id
        FROM active_relations AS relation
        JOIN ref.relation_type AS relation_type
          ON relation_type.relation_type_code = relation.relation_type_code
        WHERE relation_type.is_hierarchical

        UNION

        SELECT
            walk.relation_type_code,
            walk.start_concept_id,
            relation.object_concept_id
        FROM hierarchy_walk AS walk
        JOIN active_relations AS relation
          ON relation.relation_type_code = walk.relation_type_code
         AND relation.subject_concept_id = walk.current_concept_id
    ),
    check_counts (check_key, violation_count) AS (
        SELECT
            'dangling_concept_relation_endpoints',
            count(*)::BIGINT
        FROM kb.concept_relation AS relation
        LEFT JOIN kb.concept AS subject
          ON subject.concept_id = relation.subject_concept_id
        LEFT JOIN kb.concept AS object
          ON object.concept_id = relation.object_concept_id
        WHERE subject.concept_id IS NULL
           OR object.concept_id IS NULL

        UNION ALL

        SELECT
            'duplicate_concept_keys',
            count(*)::BIGINT
        FROM (
            SELECT concept.concept_key
            FROM kb.concept AS concept
            GROUP BY concept.concept_key
            HAVING count(*) > 1
        ) AS duplicates

        UNION ALL

        SELECT
            'malformed_concept_keys',
            count(*)::BIGINT
        FROM kb.concept AS concept
        WHERE concept.concept_key !~ '^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$'

        UNION ALL

        SELECT
            'invalid_concept_lifecycle_replacements',
            count(*)::BIGINT
        FROM kb.concept AS concept
        LEFT JOIN kb.concept AS replacement
          ON replacement.concept_id = concept.replacement_concept_id
        WHERE (
                concept.lifecycle_status_code = 'merged'
                AND concept.replacement_concept_id IS NULL
              )
           OR (
                concept.lifecycle_status_code NOT IN ('deprecated', 'merged')
                AND concept.replacement_concept_id IS NOT NULL
              )
           OR concept.replacement_concept_id = concept.concept_id
           OR (
                concept.replacement_concept_id IS NOT NULL
                AND replacement.lifecycle_status_code <> 'active'
              )

        UNION ALL

        SELECT
            'illegal_self_relations',
            count(*)::BIGINT
        FROM kb.concept_relation AS relation
        JOIN ref.relation_type AS relation_type
          ON relation_type.relation_type_code = relation.relation_type_code
        WHERE NOT relation_type.allows_self
          AND relation.subject_concept_id = relation.object_concept_id

        UNION ALL

        SELECT
            'incorrectly_ordered_symmetric_relations',
            count(*)::BIGINT
        FROM kb.concept_relation AS relation
        JOIN ref.relation_type AS relation_type
          ON relation_type.relation_type_code = relation.relation_type_code
        WHERE relation_type.is_symmetric
          AND relation.subject_concept_id >= relation.object_concept_id

        UNION ALL

        SELECT
            'duplicate_current_symmetric_relations',
            count(*)::BIGINT
        FROM (
            SELECT
                relation.relation_type_code,
                least(
                    relation.subject_concept_id,
                    relation.object_concept_id
                ) AS lower_concept_id,
                greatest(
                    relation.subject_concept_id,
                    relation.object_concept_id
                ) AS upper_concept_id
            FROM current_relations AS relation
            JOIN ref.relation_type AS relation_type
              ON relation_type.relation_type_code = relation.relation_type_code
            WHERE relation_type.is_symmetric
            GROUP BY
                relation.relation_type_code,
                least(
                    relation.subject_concept_id,
                    relation.object_concept_id
                ),
                greatest(
                    relation.subject_concept_id,
                    relation.object_concept_id
                )
            HAVING count(*) > 1
        ) AS duplicates

        UNION ALL

        SELECT
            'active_hierarchy_cycles',
            count(*)::BIGINT
        FROM (
            SELECT DISTINCT
                walk.relation_type_code,
                walk.start_concept_id
            FROM hierarchy_walk AS walk
            WHERE walk.start_concept_id = walk.current_concept_id
        ) AS cycles

        UNION ALL

        SELECT
            'externally_sourced_active_concepts_without_provenance',
            count(*)::BIGINT
        FROM kb.concept AS concept
        JOIN ref.provenance_scope AS provenance_scope
          ON provenance_scope.provenance_scope_code = concept.provenance_scope_code
        WHERE concept.lifecycle_status_code = 'active'
          AND provenance_scope.requires_source_support
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.concept_support AS support
              WHERE support.concept_id = concept.concept_id
          )

        UNION ALL

        SELECT
            'externally_sourced_active_lexicalizations_without_provenance',
            count(*)::BIGINT
        FROM kb.lexicalization AS lexicalization
        JOIN ref.provenance_scope AS provenance_scope
          ON provenance_scope.provenance_scope_code = lexicalization.provenance_scope_code
        WHERE lexicalization.lifecycle_status_code = 'active'
          AND provenance_scope.requires_source_support
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.lexicalization_support AS support
              WHERE support.lexicalization_id = lexicalization.lexicalization_id
          )

        UNION ALL

        SELECT
            'externally_sourced_active_relations_without_provenance',
            count(*)::BIGINT
        FROM kb.concept_relation AS relation
        JOIN ref.relation_type AS relation_type
          ON relation_type.relation_type_code = relation.relation_type_code
        JOIN ref.provenance_scope AS provenance_scope
          ON provenance_scope.provenance_scope_code = relation.provenance_scope_code
        WHERE relation.lifecycle_status_code = 'active'
          AND provenance_scope.requires_source_support
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.relation_support AS support
              WHERE support.concept_relation_id = relation.concept_relation_id
          )

        UNION ALL

        SELECT
            'evidence_required_active_relations_without_provenance',
            count(*)::BIGINT
        FROM kb.concept_relation AS relation
        JOIN ref.relation_type AS relation_type
          ON relation_type.relation_type_code = relation.relation_type_code
        WHERE relation.lifecycle_status_code = 'active'
          AND relation_type.evidence_required
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.relation_support AS support
              WHERE support.concept_relation_id = relation.concept_relation_id
          )

        UNION ALL

        SELECT
            'externally_sourced_active_dimension_links_without_provenance',
            count(*)::BIGINT
        FROM kb.concept_dimension_link AS link
        JOIN ref.provenance_scope AS provenance_scope
          ON provenance_scope.provenance_scope_code = link.provenance_scope_code
        WHERE link.lifecycle_status_code = 'active'
          AND provenance_scope.requires_source_support
          AND NOT EXISTS (
              SELECT 1
              FROM evidence.concept_dimension_link_support AS support
              WHERE support.concept_dimension_link_id = link.concept_dimension_link_id
          )

        UNION ALL

        SELECT
            'source_versions_without_license_metadata',
            count(*)::BIGINT
        FROM evidence.source_version AS source_version
        LEFT JOIN evidence.license_policy AS license_policy
          ON license_policy.license_policy_id = source_version.license_policy_id
        LEFT JOIN ref.access_class AS access_class
          ON access_class.access_class_code = license_policy.access_class_code
        LEFT JOIN ref.rights_status AS rights_status
          ON rights_status.rights_status_code = license_policy.rights_status_code
        WHERE license_policy.license_policy_id IS NULL
           OR access_class.access_class_code IS NULL
           OR rights_status.rights_status_code IS NULL

        UNION ALL

        SELECT
            'unsafe_production_export_policies',
            count(*)::BIGINT
        FROM evidence.license_policy AS license_policy
        JOIN ref.access_class AS access_class
          ON access_class.access_class_code = license_policy.access_class_code
        JOIN ref.rights_status AS rights_status
          ON rights_status.rights_status_code = license_policy.rights_status_code
        WHERE license_policy.production_export_allowed
          AND (
              NOT rights_status.is_verified
              OR NOT access_class.permits_raw_text
              OR NOT license_policy.redistributable
              OR NOT license_policy.derivative_work_allowed
              OR NOT license_policy.commercial_use_allowed
              OR NOT license_policy.machine_use_allowed
          )

        UNION ALL

        SELECT
            'invalid_observation_resolutions',
            count(*)::BIGINT
        FROM corpus.observation_resolution AS resolution
        JOIN ref.resolution_status AS resolution_status
          ON resolution_status.resolution_status_code = resolution.resolution_status_code
        JOIN corpus.observation_expression AS observation_expression
          ON observation_expression.observation_expression_id = resolution.observation_expression_id
        LEFT JOIN kb.lexicalization AS lexicalization
          ON lexicalization.lexicalization_id = resolution.lexicalization_id
        WHERE resolution_status.is_resolved <> (resolution.lexicalization_id IS NOT NULL)
           OR (
                resolution.lexicalization_id IS NOT NULL
                AND lexicalization.expression_id <> observation_expression.expression_id
              )

        UNION ALL

        SELECT
            'out_of_range_empirical_pair_measurements',
            count(*)::BIGINT
        FROM evidence.empirical_pair_measurement AS measurement
        JOIN evidence.measurement_scale AS scale
          ON scale.measurement_scale_id = measurement.measurement_scale_id
        WHERE measurement.measured_value < scale.minimum_value
           OR measurement.measured_value > scale.maximum_value

        UNION ALL

        SELECT
            'out_of_range_reference_calibrations',
            count(*)::BIGINT
        FROM evidence.reference_calibration AS calibration
        JOIN evidence.measurement_scale AS scale
          ON scale.measurement_scale_id = calibration.measurement_scale_id
        WHERE calibration.minimum_value < scale.minimum_value
           OR calibration.maximum_value > scale.maximum_value
           OR calibration.minimum_value > calibration.typical_value
           OR calibration.typical_value > calibration.maximum_value

        UNION ALL

        SELECT
            'out_of_range_expression_cooccurrence_measurements',
            count(*)::BIGINT
        FROM corpus.expression_cooccurrence_measurement AS measurement
        JOIN evidence.measurement_scale AS scale
          ON scale.measurement_scale_id = measurement.measurement_scale_id
        WHERE measurement.measured_value < scale.minimum_value
           OR measurement.measured_value > scale.maximum_value

        UNION ALL

        SELECT
            'out_of_range_candidate_signals',
            count(*)::BIGINT
        FROM ml.candidate_signal AS signal
        JOIN evidence.measurement_scale AS scale
          ON scale.measurement_scale_id = signal.measurement_scale_id
        WHERE signal.signal_value < scale.minimum_value
           OR signal.signal_value > scale.maximum_value

        UNION ALL

        SELECT
            'noncanonical_nondirectional_pair_measurements',
            count(*)::BIGINT
        FROM evidence.empirical_pair_measurement AS measurement
        WHERE NOT measurement.is_directional
          AND measurement.subject_concept_id >= measurement.object_concept_id

        UNION ALL

        SELECT
            'terminal_model_runs_without_consistent_completion_time',
            count(*)::BIGINT
        FROM ml.model_run AS model_run
        JOIN ref.model_run_status AS model_run_status
          ON model_run_status.model_run_status_code = model_run.model_run_status_code
        WHERE model_run_status.is_terminal <> (model_run.completed_at IS NOT NULL)

        UNION ALL

        SELECT
            'mapping_inferences_with_invalid_candidate_counts',
            count(*)::BIGINT
        FROM ml.mapping_inference AS inference
        JOIN ref.resolution_status AS resolution_status
          ON resolution_status.resolution_status_code = inference.resolution_status_code
        LEFT JOIN LATERAL (
            SELECT count(*)::BIGINT AS candidate_count
            FROM ml.mapping_candidate AS candidate
            WHERE candidate.mapping_inference_id = inference.mapping_inference_id
        ) AS candidate_counts ON TRUE
        WHERE (
                inference.resolution_status_code = 'resolved'
                AND candidate_counts.candidate_count = 0
              )
           OR (
                inference.resolution_status_code = 'unresolved'
                AND candidate_counts.candidate_count <> 0
              )

        UNION ALL

        SELECT
            'model_candidates_without_versioned_model_runs',
            count(*)::BIGINT
        FROM ml.mapping_candidate AS candidate
        LEFT JOIN ml.mapping_inference AS inference
          ON inference.mapping_inference_id = candidate.mapping_inference_id
        LEFT JOIN ml.model_run AS model_run
          ON model_run.model_run_id = inference.model_run_id
        LEFT JOIN ml.model_version AS model_version
          ON model_version.model_version_id = model_run.model_version_id
        LEFT JOIN ml.model AS model
          ON model.model_id = model_version.model_id
        WHERE inference.mapping_inference_id IS NULL
           OR model_run.model_run_id IS NULL
           OR model_version.model_version_id IS NULL
           OR model.model_id IS NULL

        UNION ALL

        SELECT
            'malformed_promotion_target_counts',
            count(*)::BIGINT
        FROM audit.promotion_event AS promotion
        WHERE num_nonnulls(
            promotion.target_concept_id,
            promotion.target_lexicalization_id,
            promotion.target_concept_relation_id,
            promotion.target_concept_dimension_link_id
        ) <> 1

        UNION ALL

        SELECT
            'promotions_without_permitting_review',
            count(*)::BIGINT
        FROM audit.promotion_event AS promotion
        LEFT JOIN audit.review AS review
          ON review.review_id = promotion.review_id
        LEFT JOIN ref.review_decision AS review_decision
          ON review_decision.review_decision_code = review.review_decision_code
        WHERE review_decision.review_decision_code IS NULL
           OR NOT review_decision.permits_promotion

        UNION ALL

        SELECT
            'promotions_with_dangling_targets',
            count(*)::BIGINT
        FROM audit.promotion_event AS promotion
        LEFT JOIN kb.concept AS concept
          ON concept.concept_id = promotion.target_concept_id
        LEFT JOIN kb.lexicalization AS lexicalization
          ON lexicalization.lexicalization_id = promotion.target_lexicalization_id
        LEFT JOIN kb.concept_relation AS relation
          ON relation.concept_relation_id = promotion.target_concept_relation_id
        LEFT JOIN kb.concept_dimension_link AS dimension_link
          ON dimension_link.concept_dimension_link_id = promotion.target_concept_dimension_link_id
        WHERE (
                promotion.target_concept_id IS NOT NULL
                AND concept.concept_id IS NULL
              )
           OR (
                promotion.target_lexicalization_id IS NOT NULL
                AND lexicalization.lexicalization_id IS NULL
              )
           OR (
                promotion.target_concept_relation_id IS NOT NULL
                AND relation.concept_relation_id IS NULL
              )
           OR (
                promotion.target_concept_dimension_link_id IS NOT NULL
                AND dimension_link.concept_dimension_link_id IS NULL
              )

        UNION ALL

        SELECT
            'deprecated_concepts_exposed_in_current_ontology',
            count(*)::BIGINT
        FROM kb.v_current_canonical_ontology AS ontology
        WHERE ontology.concept_lifecycle_status_code <> 'active'
           OR (
                ontology.subject_concept_id IS NOT NULL
                AND ontology.subject_lifecycle_status_code <> 'active'
              )
           OR (
                ontology.object_concept_id IS NOT NULL
                AND ontology.object_lifecycle_status_code <> 'active'
              )

        UNION ALL

        SELECT
            'deprecated_or_expired_relations_exposed_in_current_ontology',
            count(*)::BIGINT
        FROM kb.v_current_canonical_ontology AS ontology
        WHERE ontology.concept_relation_id IS NOT NULL
          AND (
                ontology.relation_lifecycle_status_code <> 'active'
                OR ontology.relation_valid_from > CURRENT_TIMESTAMP
                OR (
                    ontology.relation_valid_until IS NOT NULL
                    AND ontology.relation_valid_until <= CURRENT_TIMESTAMP
                )
              )

        UNION ALL

        SELECT
            'restricted_raw_text_exposed_in_distributable_view',
            count(*)::BIGINT
        FROM corpus.v_distributable_observations AS distributable
        JOIN corpus.captured_document AS document
          ON document.captured_document_id = distributable.captured_document_id
        JOIN evidence.source_version AS source_version
          ON source_version.source_version_id = document.source_version_id
        JOIN evidence.license_policy AS license_policy
          ON license_policy.license_policy_id = source_version.license_policy_id
        JOIN ref.access_class AS access_class
          ON access_class.access_class_code = license_policy.access_class_code
        JOIN ref.rights_status AS rights_status
          ON rights_status.rights_status_code = license_policy.rights_status_code
        WHERE NOT license_policy.production_export_allowed
           OR NOT rights_status.is_verified
           OR NOT access_class.permits_raw_text

        UNION ALL

        SELECT
            'pgvector_extension_present',
            count(*)::BIGINT
        FROM pg_catalog.pg_extension AS extension
        WHERE extension.extname = 'vector'
    )
    SELECT
        checks.check_key,
        checks.violation_count,
        checks.violation_count = 0 AS passed
    FROM check_counts AS checks;
$run_validation_queries$;

COMMENT ON FUNCTION audit.run_validation_queries() IS
    'Returns the deterministic expected-zero Coffee Sensory KB V0 validation suite. Every row passes only when violation_count is zero.';

SELECT check_key, violation_count, passed
FROM audit.run_validation_queries()
ORDER BY check_key;

DO $validation_gate$
DECLARE
    failed_checks TEXT;
BEGIN
    SELECT string_agg(
        format('%s=%s', validation.check_key, validation.violation_count),
        ', ' ORDER BY validation.check_key
    )
    INTO failed_checks
    FROM audit.run_validation_queries() AS validation
    WHERE validation.passed IS NOT TRUE
       OR validation.violation_count <> 0;

    IF failed_checks IS NOT NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'coffee_sensory_kb_v0_validation_ck',
            MESSAGE = format(
                'Coffee Sensory KB V0 validation failed: %s',
                failed_checks
            );
    END IF;

    RAISE NOTICE 'VALIDATION_PASS=true';
END
$validation_gate$;

COMMIT;
