\set ON_ERROR_STOP on
\pset pager off

-- Every block below performs an operation that must fail, captures PostgreSQL's
-- actual SQLSTATE and constraint diagnostic, and then rolls back that block's
-- writes. The outer rollback also removes shared fixtures created for tests.

BEGIN;
SET CONSTRAINTS ALL DEFERRED;

DO $duplicate_concept$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.concept (
            concept_key,
            concept_type_code,
            lifecycle_status_code,
            provenance_scope_code,
            description
        ) VALUES (
            'sensory.grapefruit',
            'sensory_attribute',
            'active',
            'project_authored',
            'Negative-test duplicate that must never persist.'
        );
        RAISE EXCEPTION 'duplicate concept was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23505'
           OR actual_constraint IS DISTINCT FROM 'concept_key_uq' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=duplicate_concept SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$duplicate_concept$;

DO $self_neighbour$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.concept_relation (
            relation_key,
            relation_type_code,
            subject_concept_id,
            object_concept_id,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.self_neighbour.grapefruit',
            'sensory_neighbour',
            concept.concept_id,
            concept.concept_id,
            'active',
            'project_authored'
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'sensory.grapefruit';
        RAISE EXCEPTION 'self neighbour was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_relation_self_allowed_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=self_neighbour SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$self_neighbour$;

DO $symmetric_duplicate$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.concept_relation (
            relation_key,
            relation_type_code,
            subject_concept_id,
            object_concept_id,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.cardboard.neighbour.rubber.forward',
            'sensory_neighbour',
            cardboard.concept_id,
            rubber.concept_id,
            'active',
            'project_authored'
        FROM kb.concept AS cardboard
        CROSS JOIN kb.concept AS rubber
        WHERE cardboard.concept_key = 'sensory.cardboard'
          AND rubber.concept_key = 'sensory.rubber';

        INSERT INTO kb.concept_relation (
            relation_key,
            relation_type_code,
            subject_concept_id,
            object_concept_id,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.cardboard.neighbour.rubber.reverse',
            'sensory_neighbour',
            rubber.concept_id,
            cardboard.concept_id,
            'active',
            'project_authored'
        FROM kb.concept AS cardboard
        CROSS JOIN kb.concept AS rubber
        WHERE cardboard.concept_key = 'sensory.cardboard'
          AND rubber.concept_key = 'sensory.rubber';
        RAISE EXCEPTION 'inverse symmetric duplicate was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23505'
           OR actual_constraint IS DISTINCT FROM 'concept_relation_type_endpoints_uq' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=symmetric_duplicate SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$symmetric_duplicate$;

DO $direct_hierarchy_cycle$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.concept_relation (
            relation_key,
            relation_type_code,
            subject_concept_id,
            object_concept_id,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.grapefruit.broader_than.citrus',
            'broader_than',
            grapefruit.concept_id,
            citrus.concept_id,
            'active',
            'project_authored'
        FROM kb.concept AS grapefruit
        CROSS JOIN kb.concept AS citrus
        WHERE grapefruit.concept_key = 'sensory.grapefruit'
          AND citrus.concept_key = 'category.citrus';
        RAISE EXCEPTION 'direct hierarchy cycle was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_relation_hierarchy_cycle_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=direct_hierarchy_cycle SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$direct_hierarchy_cycle$;

DO $indirect_hierarchy_cycle$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.concept_relation (
            relation_key,
            relation_type_code,
            subject_concept_id,
            object_concept_id,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.indirect_hierarchy_cycle',
            'broader_than',
            path.descendant_concept_id,
            path.ancestor_concept_id,
            'active',
            'project_authored'
        FROM (
            SELECT
                first_edge.subject_concept_id AS ancestor_concept_id,
                second_edge.object_concept_id AS descendant_concept_id
            FROM kb.concept_relation AS first_edge
            JOIN kb.concept_relation AS second_edge
              ON second_edge.subject_concept_id =
                 first_edge.object_concept_id
             AND second_edge.relation_type_code = 'broader_than'
             AND second_edge.lifecycle_status_code = 'active'
            WHERE first_edge.relation_type_code = 'broader_than'
              AND first_edge.lifecycle_status_code = 'active'
            ORDER BY
                first_edge.relation_key,
                second_edge.relation_key
            LIMIT 1
        ) AS path;
        RAISE EXCEPTION 'indirect hierarchy cycle was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_relation_hierarchy_cycle_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=indirect_hierarchy_cycle SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$indirect_hierarchy_cycle$;

DO $unsupported_external_relation$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.concept_relation (
            relation_key,
            relation_type_code,
            subject_concept_id,
            object_concept_id,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.external.cardboard.consumer_reference_for.jasmine',
            'consumer_reference_for',
            cardboard.concept_id,
            jasmine.concept_id,
            'active',
            'external'
        FROM kb.concept AS cardboard
        CROSS JOIN kb.concept AS jasmine
        WHERE cardboard.concept_key = 'sensory.cardboard'
          AND jasmine.concept_key = 'sensory.jasmine';

        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION 'unsupported external relation was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'concept_relation_active_source_support_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=unsupported_external_relation SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
    SET CONSTRAINTS ALL DEFERRED;
END
$unsupported_external_relation$;

DO $unsupported_external_lexicalization$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO kb.lexicalization (
            lexicalization_key,
            expression_id,
            concept_id,
            mapping_type_code,
            lifecycle_status_code,
            provenance_scope_code
        )
        SELECT
            'negative.external.meteor_fruit.cardboard',
            expression.expression_id,
            concept.concept_id,
            'approved_variant',
            'active',
            'external'
        FROM kb.lexical_expression AS expression
        CROSS JOIN kb.concept AS concept
        WHERE expression.expression_key = 'expression.en.meteor_fruit'
          AND concept.concept_key = 'sensory.cardboard';

        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION 'unsupported external lexicalization was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'lexicalization_active_source_support_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=unsupported_external_lexicalization SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
    SET CONSTRAINTS ALL DEFERRED;
END
$unsupported_external_lexicalization$;

INSERT INTO audit.reviewer (
    reviewer_key,
    display_name,
    affiliation
) VALUES (
    'negative.reviewer',
    'Negative-test reviewer',
    'Test-only fixture'
);

INSERT INTO audit.review (
    review_key,
    reviewer_id,
    review_decision_code,
    reviewed_at,
    independence_statement,
    notes
)
SELECT
    review_seed.review_key,
    reviewer.reviewer_id,
    review_seed.review_decision_code,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    'Test-only independent constraint exercise.',
    'Rolled back after negative tests.'
FROM (
    VALUES
        ('negative.review.approved', 'approved'),
        ('negative.review.rejected', 'rejected')
) AS review_seed(review_key, review_decision_code)
CROSS JOIN audit.reviewer AS reviewer
WHERE reviewer.reviewer_key = 'negative.reviewer';

DO $promotion_zero_targets$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.promotion_event (
            promotion_event_key,
            review_id,
            rationale
        )
        SELECT
            'negative.promotion.zero_targets',
            review.review_id,
            'Negative test: zero targets must fail.'
        FROM audit.review AS review
        WHERE review.review_key = 'negative.review.approved';
        RAISE EXCEPTION 'zero-target promotion was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'promotion_event_exactly_one_target_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=promotion_zero_targets SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$promotion_zero_targets$;

DO $promotion_two_targets$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.promotion_event (
            promotion_event_key,
            review_id,
            target_concept_id,
            target_lexicalization_id,
            rationale
        )
        SELECT
            'negative.promotion.two_targets',
            review.review_id,
            concept.concept_id,
            lexicalization.lexicalization_id,
            'Negative test: two targets must fail.'
        FROM audit.review AS review
        CROSS JOIN kb.concept AS concept
        CROSS JOIN kb.lexicalization AS lexicalization
        WHERE review.review_key = 'negative.review.approved'
          AND concept.concept_key = 'sensory.grapefruit'
          AND lexicalization.lexicalization_key = 'lexicalization.en.grapefruit.preferred';
        RAISE EXCEPTION 'two-target promotion was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'promotion_event_exactly_one_target_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=promotion_two_targets SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$promotion_two_targets$;

DO $promotion_rejected_review$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.promotion_event (
            promotion_event_key,
            review_id,
            target_concept_id,
            rationale
        )
        SELECT
            'negative.promotion.rejected_review',
            review.review_id,
            concept.concept_id,
            'Negative test: a rejecting review cannot permit promotion.'
        FROM audit.review AS review
        CROSS JOIN kb.concept AS concept
        WHERE review.review_key = 'negative.review.rejected'
          AND concept.concept_key = 'sensory.grapefruit';
        RAISE EXCEPTION 'promotion with rejecting review was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'promotion_event_review_permits_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=promotion_rejected_review SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$promotion_rejected_review$;

DO $promotion_candidate_target$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.promotion_event (
            promotion_event_key,
            review_id,
            target_concept_id,
            rationale
        )
        SELECT
            'negative.promotion.candidate_target',
            review.review_id,
            concept.concept_id,
            'Negative test: promotion history targets an already-active canonical object.'
        FROM audit.review AS review
        CROSS JOIN kb.concept AS concept
        WHERE review.review_key = 'negative.review.approved'
          AND concept.concept_key = 'qualifier.bright';
        RAISE EXCEPTION 'promotion targeting candidate object was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'promotion_event_target_active_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=promotion_candidate_target SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$promotion_candidate_target$;

INSERT INTO evidence.sensory_reference (
    sensory_reference_key,
    concept_id,
    source_version_id,
    name,
    material_description,
    preparation_notes
)
SELECT
    'negative.reference.grapefruit',
    concept.concept_id,
    source_version.source_version_id,
    'Negative-test grapefruit reference',
    'Test-only synthetic material description.',
    'Never used outside the rolled-back constraint test.'
FROM kb.concept AS concept
CROSS JOIN evidence.source_version AS source_version
WHERE concept.concept_key = 'sensory.grapefruit'
  AND source_version.source_version_key = 'source_version.project_smoke_seed.2026-08-24';

DO $invalid_reference_calibration$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO evidence.reference_calibration (
            reference_calibration_key,
            sensory_reference_id,
            sensory_dimension_id,
            dataset_id,
            measurement_scale_id,
            minimum_value,
            typical_value,
            maximum_value,
            protocol
        )
        SELECT
            'negative.calibration.out_of_range',
            sensory_reference.sensory_reference_id,
            dimension.sensory_dimension_id,
            dataset.dataset_id,
            scale.measurement_scale_id,
            -0.1,
            0.5,
            0.9,
            '{"fixture":true}'::JSONB
        FROM evidence.sensory_reference AS sensory_reference
        CROSS JOIN kb.sensory_dimension AS dimension
        CROSS JOIN evidence.dataset AS dataset
        CROSS JOIN evidence.measurement_scale AS scale
        WHERE sensory_reference.sensory_reference_key = 'negative.reference.grapefruit'
          AND dimension.dimension_key = 'taste.sourness_acidity'
          AND dataset.dataset_key = 'dataset.project_smoke_seed'
          AND scale.scale_key = 'scale.test_unit_interval';
        RAISE EXCEPTION 'out-of-range calibration was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'reference_calibration_scale_bounds_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=invalid_reference_calibration SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$invalid_reference_calibration$;

INSERT INTO ml.model (
    model_key,
    name,
    model_family,
    description,
    external_metadata
) VALUES (
    'negative.model',
    'Negative-test model',
    'test-only',
    'A rolled-back fixture used only to exercise model-run constraints.',
    '{"fixture":true}'::JSONB
);

INSERT INTO ml.model_version (
    model_version_key,
    model_id,
    version_label,
    artifact_locator,
    configuration,
    created_at
)
SELECT
    'negative.model_version.v1',
    model.model_id,
    'v1',
    NULL,
    '{"fixture":true}'::JSONB,
    TIMESTAMPTZ '2026-08-24 00:00:00+00'
FROM ml.model AS model
WHERE model.model_key = 'negative.model';

DO $invalid_model_run_timestamp$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO ml.model_run (
            model_run_key,
            model_version_id,
            model_run_status_code,
            input_dataset_id,
            started_at,
            completed_at,
            run_configuration
        )
        SELECT
            'negative.model_run.nonterminal_with_completion',
            version.model_version_id,
            'queued',
            dataset.dataset_id,
            TIMESTAMPTZ '2026-08-24 00:00:00+00',
            TIMESTAMPTZ '2026-08-24 00:01:00+00',
            '{"fixture":true}'::JSONB
        FROM ml.model_version AS version
        CROSS JOIN evidence.dataset AS dataset
        WHERE version.model_version_key = 'negative.model_version.v1'
          AND dataset.dataset_key = 'dataset.project_smoke_seed';
        RAISE EXCEPTION 'nonterminal model run with completed_at was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'model_run_terminal_timestamp_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=model_run_terminal_timestamp SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$invalid_model_run_timestamp$;

INSERT INTO ml.model_run (
    model_run_key,
    model_version_id,
    model_run_status_code,
    input_dataset_id,
    started_at,
    completed_at,
    random_seed,
    run_configuration,
    result_metadata
)
SELECT
    'negative.model_run.completed',
    version.model_version_id,
    'completed',
    dataset.dataset_id,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    TIMESTAMPTZ '2026-08-24 00:01:00+00',
    538,
    '{"fixture":true}'::JSONB,
    '{"fixture":true}'::JSONB
FROM ml.model_version AS version
CROSS JOIN evidence.dataset AS dataset
WHERE version.model_version_key = 'negative.model_version.v1'
  AND dataset.dataset_key = 'dataset.project_smoke_seed';

DO $resolved_inference_without_candidate$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO ml.mapping_inference (
            mapping_inference_key,
            model_run_id,
            observation_expression_id,
            resolution_status_code,
            inferred_at,
            resolution_notes
        )
        SELECT
            'negative.inference.resolved_without_candidate',
            run.model_run_id,
            occurrence.observation_expression_id,
            'resolved',
            TIMESTAMPTZ '2026-08-24 00:02:00+00',
            'Negative test: a resolved inference requires a candidate.'
        FROM ml.model_run AS run
        CROSS JOIN corpus.observation_expression AS occurrence
        WHERE run.model_run_key = 'negative.model_run.completed'
          AND occurrence.observation_expression_key = 'observation_expression.public_pink_grapefruit';

        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION 'resolved inference without candidate was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'mapping_inference_resolved_candidate_count_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=resolved_inference_without_candidate SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
    SET CONSTRAINTS ALL DEFERRED;
END
$resolved_inference_without_candidate$;

DO $unresolved_inference_with_candidate$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO ml.mapping_inference (
            mapping_inference_key,
            model_run_id,
            observation_expression_id,
            resolution_status_code,
            inferred_at,
            resolution_notes
        )
        SELECT
            'negative.inference.unresolved_with_candidate',
            run.model_run_id,
            occurrence.observation_expression_id,
            'unresolved',
            TIMESTAMPTZ '2026-08-24 00:02:00+00',
            'Negative test: explicit unresolved must preserve zero candidates.'
        FROM ml.model_run AS run
        CROSS JOIN corpus.observation_expression AS occurrence
        WHERE run.model_run_key = 'negative.model_run.completed'
          AND occurrence.observation_expression_key = 'observation_expression.restricted_meteor_fruit';

        INSERT INTO ml.mapping_candidate (
            mapping_candidate_key,
            mapping_inference_id,
            concept_id,
            candidate_status_code,
            rank,
            rationale
        )
        SELECT
            'negative.candidate.for_unresolved_inference',
            inference.mapping_inference_id,
            concept.concept_id,
            'proposed',
            1,
            'Negative test: this candidate must make unresolved state fail.'
        FROM ml.mapping_inference AS inference
        CROSS JOIN kb.concept AS concept
        WHERE inference.mapping_inference_key = 'negative.inference.unresolved_with_candidate'
          AND concept.concept_key = 'sensory.grapefruit';

        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION 'unresolved inference with candidate was unexpectedly accepted';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM 'mapping_inference_unresolved_candidate_count_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'NEGATIVE_TEST=unresolved_inference_with_candidate SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
    SET CONSTRAINTS ALL DEFERRED;
END
$unresolved_inference_with_candidate$;

ROLLBACK;

\echo NEGATIVE_TEST_PASS=true
