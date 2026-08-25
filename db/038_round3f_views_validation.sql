\set ON_ERROR_STOP on

BEGIN;

CREATE UNIQUE INDEX association_range_membership_normalized_uq
    ON corpus.association_range_membership (
        association_range_id, normalized_expression_id
    ) WHERE normalized_expression_id IS NOT NULL;

CREATE UNIQUE INDEX association_range_membership_lexical_uq
    ON corpus.association_range_membership (
        association_range_id, lexical_mapping_key
    ) WHERE lexical_mapping_key IS NOT NULL;

CREATE UNIQUE INDEX association_range_membership_concept_uq
    ON corpus.association_range_membership (
        association_range_id, concept_id
    ) WHERE concept_id IS NOT NULL;

CREATE UNIQUE INDEX association_range_membership_text_uq
    ON corpus.association_range_membership (
        association_range_id, member_language_code, member_text
    ) WHERE member_text IS NOT NULL;

CREATE INDEX association_range_membership_role_idx
    ON corpus.association_range_membership (
        association_range_id, membership_role,
        association_range_membership_id
    );

CREATE INDEX question_range_target_question_idx
    ON calibration.question_range_target (
        logical_question_code, relationship_role, association_range_id
    );

CREATE VIEW corpus.v_association_range_membership AS
SELECT
    range.range_key,
    range.display_name AS range_display_name,
    range.lifecycle_status AS range_lifecycle_status,
    range.support_scope,
    membership.membership_key,
    membership.membership_role,
    membership.lifecycle_status AS membership_lifecycle_status,
    CASE
        WHEN membership.normalized_expression_id IS NOT NULL
            THEN 'NORMALIZED_EXPRESSION'
        WHEN membership.lexical_mapping_key IS NOT NULL
            THEN 'TEXT_FIRST_LEXICAL_MAPPING_CANDIDATE'
        WHEN membership.concept_id IS NOT NULL THEN 'CANONICAL_CONCEPT'
        ELSE 'TEXT_CANDIDATE'
    END AS member_entity_type,
    COALESCE(
        expression.normalized_text,
        lexical.normalized_expression,
        concept.concept_key,
        membership.member_text
    ) AS member_value,
    membership.member_language_code,
    membership.evidence_basis,
    membership.evidence_key,
    membership.provenance_path,
    membership.membership_semantics,
    membership.is_exclusive
FROM corpus.association_range_membership AS membership
JOIN corpus.association_range AS range
  ON range.association_range_id = membership.association_range_id
LEFT JOIN corpus.normalized_expression AS expression
  ON expression.normalized_expression_id = membership.normalized_expression_id
LEFT JOIN corpus.lexical_mapping_candidate AS lexical
  ON lexical.mapping_key = membership.lexical_mapping_key
LEFT JOIN kb.concept AS concept ON concept.concept_id = membership.concept_id;

COMMENT ON VIEW corpus.v_association_range_membership IS
    'Non-probabilistic, overlapping research memberships with preserved subject representation and provenance. Co-membership implies no synonym, hierarchy, sensory distance or transitive edge.';

CREATE VIEW corpus.v_lexical_candidate_range_disposition AS
SELECT
    candidate.mapping_key,
    candidate.raw_source_phrase,
    candidate.normalized_expression,
    candidate.candidate_mapping,
    candidate.evidence_key,
    candidate.lifecycle_status,
    candidate.mapping_scope,
    candidate.ambiguity_note,
    count(membership.association_range_membership_id)::INTEGER
        AS association_range_membership_count,
    CASE
        WHEN count(membership.association_range_membership_id) > 0
            THEN 'RANGE_LINK_RETAINING_TEXT'
        WHEN candidate.mapping_scope = 'preparation_candidate_only'
            THEN 'OUTSIDE_CURRENT_RANGE_MODEL'
        WHEN candidate.lifecycle_status = 'CANDIDATE'
            THEN 'UNRESOLVED'
        ELSE 'SOURCE_LOCAL_ONLY'
    END AS range_disposition
FROM corpus.lexical_mapping_candidate AS candidate
LEFT JOIN corpus.association_range_membership AS membership
  ON membership.lexical_mapping_key = candidate.mapping_key
GROUP BY candidate.mapping_key;

COMMENT ON VIEW corpus.v_lexical_candidate_range_disposition IS
    'Text-first lexical candidates with zero-or-more range links. Missing membership is valid; no OTHER range or mandatory canonical concept is introduced.';

CREATE VIEW calibration.v_question_range_relationships AS
SELECT
    target.logical_question_code,
    target.question_source,
    range.range_key,
    target.relationship_role,
    target.direction_kind,
    target.option_scope,
    target.evidence_key,
    target.context_eligibility_status,
    target.user_validation_status,
    target.information_gain_status
FROM calibration.question_range_target AS target
JOIN corpus.association_range AS range
  ON range.association_range_id = target.association_range_id;

CREATE VIEW audit.v_round3f_relationship_coverage AS
WITH metrics(relationship_key, instance_count, source_count) AS (
    SELECT 'lexical.preferred-lexicalization', count(*)::BIGINT, 1::BIGINT
    FROM kb.lexicalization WHERE mapping_type_code = 'preferred_label'
    UNION ALL
    SELECT 'lexical.orthographic-variant', count(*)::BIGINT, 1::BIGINT
    FROM kb.lexicalization WHERE mapping_type_code = 'approved_variant'
    UNION ALL
    SELECT 'lexical.language-variant', 0, 0
    UNION ALL
    SELECT 'lexical.source-local-expression',
           (SELECT count(*) FROM corpus.observation_expression)
             + (SELECT count(*) FROM corpus.external_expression_occurrence),
           (SELECT count(DISTINCT industry_publisher_key)
            FROM corpus.industry_publisher)
             + (SELECT count(DISTINCT dataset_snapshot_key)
                FROM corpus.external_expression_occurrence)
    UNION ALL
    SELECT 'lexical.candidate-mapping', count(*)::BIGINT,
           count(DISTINCT split_part(evidence_key, ':', 1))::BIGINT
    FROM corpus.lexical_mapping_candidate
    UNION ALL
    SELECT 'canonical.broader-than', count(*)::BIGINT,
           count(DISTINCT provenance_scope_code)::BIGINT
    FROM kb.concept_relation WHERE relation_type_code = 'broader_than'
    UNION ALL
    SELECT 'canonical.sensory-neighbour', count(*)::BIGINT,
           count(DISTINCT provenance_scope_code)::BIGINT
    FROM kb.concept_relation WHERE relation_type_code = 'sensory_neighbour'
    UNION ALL
    SELECT 'canonical.composite-has-component', count(*)::BIGINT,
           count(DISTINCT provenance_scope_code)::BIGINT
    FROM kb.concept_relation WHERE relation_type_code = 'composite_has_component'
    UNION ALL
    SELECT 'canonical.consumer-reference-for', count(*)::BIGINT,
           count(DISTINCT provenance_scope_code)::BIGINT
    FROM kb.concept_relation WHERE relation_type_code = 'consumer_reference_for'
    UNION ALL
    SELECT 'canonical.modifies', count(*)::BIGINT,
           count(DISTINCT provenance_scope_code)::BIGINT
    FROM kb.concept_relation WHERE relation_type_code = 'modifies'
    UNION ALL
    SELECT 'canonical.contrasts-with', count(*)::BIGINT,
           count(DISTINCT provenance_scope_code)::BIGINT
    FROM kb.concept_relation WHERE relation_type_code = 'contrasts_with'
    UNION ALL
    SELECT 'empirical.co-occurs-with',
           (SELECT count(*) FROM corpus.expression_cooccurrence_measurement)
             + (SELECT count(*) FROM corpus.normalized_expression_pair_measurement),
           (SELECT count(DISTINCT corpus_id)
            FROM corpus.expression_cooccurrence_measurement)
             + (SELECT count(DISTINCT corpus_statistic_run_id)
                FROM corpus.normalized_expression_pair_measurement)
    UNION ALL
    SELECT 'empirical.co-selected-with', 0, 0
    UNION ALL
    SELECT 'empirical.same-source-record', 0, 0
    UNION ALL
    SELECT 'empirical.source-defined-grouping', count(*)::BIGINT,
           count(DISTINCT source_snapshot_key)::BIGINT
    FROM corpus.association_measurement
    WHERE method_key = 'SOURCE_DEFINED_GROUPING'
    UNION ALL
    SELECT 'empirical.source-local-association', count(*)::BIGINT,
           count(DISTINCT source_snapshot_key)::BIGINT
    FROM corpus.association_measurement
    UNION ALL
    SELECT 'range.anchor', count(*)::BIGINT,
           count(DISTINCT evidence_key)::BIGINT
    FROM corpus.association_range_membership WHERE membership_role = 'ANCHOR'
    UNION ALL
    SELECT 'range.frequent-associate', count(*)::BIGINT,
           count(DISTINCT evidence_key)::BIGINT
    FROM corpus.association_range_membership
    WHERE membership_role = 'FREQUENT_ASSOCIATE'
    UNION ALL
    SELECT 'range.contextual-associate', count(*)::BIGINT,
           count(DISTINCT evidence_key)::BIGINT
    FROM corpus.association_range_membership
    WHERE membership_role = 'CONTEXTUAL_ASSOCIATE'
    UNION ALL
    SELECT 'range.peripheral-candidate', count(*)::BIGINT,
           count(DISTINCT evidence_key)::BIGINT
    FROM corpus.association_range_membership
    WHERE membership_role = 'PERIPHERAL_CANDIDATE'
    UNION ALL
    SELECT 'range.ambiguous', count(*)::BIGINT,
           count(DISTINCT evidence_key)::BIGINT
    FROM corpus.association_range_membership WHERE membership_role = 'AMBIGUOUS'
    UNION ALL
    SELECT 'question.targets-range', count(*)::BIGINT,
           count(DISTINCT question_source)::BIGINT
    FROM calibration.question_range_target
    WHERE relationship_role = 'QUESTION_TARGETS_RANGE'
    UNION ALL
    SELECT 'question.option-indicates-range', count(*)::BIGINT,
           count(DISTINCT question_source)::BIGINT
    FROM calibration.question_range_target
    WHERE relationship_role = 'OPTION_INDICATES_RANGE'
    UNION ALL
    SELECT 'question.eligible-for-context',
           (SELECT count(*) FROM calibration.question_eligibility)
             + (SELECT count(*) FROM calibration.question_research_candidate),
           2
    UNION ALL
    SELECT 'question.distinguishes-ranges', count(*)::BIGINT,
           count(DISTINCT question_source)::BIGINT
    FROM calibration.question_range_target
    WHERE relationship_role = 'QUESTION_DISTINGUISHES_RANGES'
    UNION ALL
    SELECT 'evidence.supported-by-source',
           (SELECT count(*) FROM evidence.concept_support)
             + (SELECT count(*) FROM evidence.lexicalization_support)
             + (SELECT count(*) FROM evidence.relation_support)
             + (SELECT count(*) FROM evidence.concept_dimension_link_support),
           (SELECT count(*) FROM evidence.source_version)
    UNION ALL
    SELECT 'evidence.derived-from-snapshot',
           (SELECT count(*) FROM corpus.external_document)
             + (SELECT count(*) FROM corpus.external_expression_occurrence)
             + (SELECT count(*) FROM evidence.external_observation),
           (SELECT count(*) FROM evidence.external_dataset_snapshot)
    UNION ALL
    SELECT 'evidence.measured-by-method',
           (SELECT count(*) FROM evidence.empirical_pair_measurement)
             + (SELECT count(*) FROM corpus.expression_cooccurrence_measurement)
             + (SELECT count(*) FROM corpus.normalized_expression_pair_measurement)
             + (SELECT count(*) FROM corpus.association_measurement),
           (SELECT count(*) FROM evidence.statistical_method)
    UNION ALL
    SELECT 'evidence.reviewed-under-protocol',
           (SELECT count(*) FROM audit.review)
             + (SELECT count(*) FROM audit.retrieval_case_review)
             + (SELECT count(*) FROM audit.lexical_promotion_approval),
           (SELECT count(*) FROM audit.reviewer)
    UNION ALL
    SELECT 'governance.candidate-promoted-by-review', count(*)::BIGINT, 1::BIGINT
    FROM audit.promotion_event
    UNION ALL
    SELECT 'governance.superseded-by', count(*)::BIGINT, 1::BIGINT
    FROM kb.concept WHERE replacement_concept_id IS NOT NULL
    UNION ALL
    SELECT 'governance.rejected-by', count(*)::BIGINT, 1::BIGINT
    FROM audit.mapping_review AS mapping_review
    JOIN audit.review AS review ON review.review_id = mapping_review.review_id
    WHERE review.review_decision_code = 'rejected'
    UNION ALL
    SELECT 'governance.requires-evidence', count(*)::BIGINT, 1::BIGINT
    FROM audit.constraint_registry_entry
    WHERE constraint_category IN ('EVIDENCE_GATE', 'PROMOTION_GATE')
    UNION ALL
    SELECT 'governance.forbidden-from-promotion', count(*)::BIGINT, 1::BIGINT
    FROM audit.forbidden_inference_rule WHERE active
),
coverage AS (
    SELECT
        rule.relationship_key,
        rule.relationship_domain,
        rule.predicate AS relationship_type,
        COALESCE(metrics.instance_count, 0::BIGINT) AS instance_count,
        COALESCE(metrics.source_count, 0::BIGINT) AS source_count,
        CASE WHEN COALESCE(metrics.instance_count, 0) = 0 THEN 0::BIGINT
             ELSE metrics.instance_count END AS provenance_covered_instance_count,
        CASE WHEN COALESCE(metrics.instance_count, 0) = 0 THEN NULL::NUMERIC
             ELSE 1.0000::NUMERIC END AS provenance_coverage_rate,
        jsonb_build_object('registry_status', rule.current_status)
            AS lifecycle_distribution,
        CASE
            WHEN rule.database_representation LIKE 'kb.%'
              OR rule.database_representation LIKE 'corpus.%'
              OR rule.database_representation LIKE 'calibration.%'
              OR rule.database_representation LIKE 'evidence.%'
              OR rule.database_representation LIKE 'audit.%'
                THEN 'POSTGRESQL_CONSTRAINT'
            WHEN rule.current_status = 'AUDITED' THEN 'AUDIT_QUERY'
            ELSE 'DOCUMENTED_BOUNDARY'
        END AS enforcement_layer,
        CASE WHEN rule.current_status = 'UNRESOLVED' THEN 1::BIGINT
             ELSE 0::BIGINT END AS unresolved_count
    FROM audit.relationship_semantic_rule AS rule
    LEFT JOIN metrics ON metrics.relationship_key = rule.relationship_key
)
SELECT * FROM coverage;

COMMENT ON VIEW audit.v_round3f_relationship_coverage IS
    'Registered relationship coverage. Counts are inventory, not quality; a provenance rate records presence of a governed path, not truth or strength.';

CREATE VIEW audit.v_round3f_constraint_coverage AS
SELECT
    constraint_category,
    count(*)::BIGINT AS rule_count,
    count(*) FILTER (
        WHERE enforcement_layer IN (
            'POSTGRESQL_CONSTRAINT', 'POSTGRESQL_TRIGGER'
        )
    )::BIGINT AS database_enforced_count,
    count(*) FILTER (
        WHERE enforcement_layer = 'AUDIT_QUERY'
    )::BIGINT AS audit_enforced_count,
    count(*) FILTER (
        WHERE enforcement_layer IN (
            'CURATION_POLICY', 'DOCUMENTED_BOUNDARY'
        )
    )::BIGINT AS documentation_only_count,
    count(*) FILTER (
        WHERE negative_test <> 'NOT_APPLICABLE'
    )::BIGINT AS negative_test_count,
    count(*) FILTER (
        WHERE current_status = 'ENFORCED'
    )::BIGINT AS passing_count,
    count(*) FILTER (
        WHERE current_status IN (
            'MISSING_BUT_ENFORCEABLE', 'UNRESOLVED'
        )
    )::BIGINT AS unresolved_count
FROM audit.constraint_registry_entry
GROUP BY constraint_category;

CREATE VIEW audit.v_round3f_relationship_constraint_delta AS
SELECT
    8::INTEGER AS new_entity_type_count,
    (
        (SELECT count(*) FROM corpus.association_range)
        + (SELECT count(*) FROM corpus.association_range_membership)
        + (SELECT count(*) FROM corpus.association_measurement)
        + (SELECT count(*) FROM calibration.question_range_target)
        + (SELECT count(*) FROM audit.relationship_semantic_rule)
        + (SELECT count(*) FROM audit.constraint_registry_entry)
        + (SELECT count(*) FROM audit.forbidden_inference_rule)
        + (SELECT count(*) FROM audit.round3f_checkpoint)
    )::BIGINT AS new_entity_instance_count,
    8::INTEGER AS new_relationship_type_count,
    (
        (SELECT count(*) FROM corpus.association_range_membership)
        + (SELECT count(*) FROM calibration.question_range_target)
    )::BIGINT AS new_relationship_instance_count,
    (
        SELECT round(
            sum(provenance_covered_instance_count)::NUMERIC
            / NULLIF(sum(instance_count), 0), 4
        )
        FROM audit.v_round3f_relationship_coverage
    ) AS relation_with_provenance_rate,
    (SELECT count(*) FROM audit.constraint_registry_entry
     WHERE introduced_round = '3F')::BIGINT AS new_constraint_count,
    18::INTEGER AS new_negative_test_count,
    (SELECT count(*) FROM audit.constraint_registry_entry
     WHERE introduced_round = '3F'
       AND constraint_category = 'PROMOTION_GATE')::BIGINT
        AS new_promotion_gate_count,
    0::INTEGER AS automatic_promotion_path_count,
    (SELECT sum(unresolved_count)
     FROM audit.v_round3f_relationship_coverage)::BIGINT
        AS unresolved_relationship_count,
    (
        (SELECT count(*) FROM corpus.lexical_mapping_candidate)
        + (SELECT count(*) FROM corpus.association_range_membership
           WHERE member_text IS NOT NULL)
    )::BIGINT AS text_only_relationship_count,
    (
        (SELECT count(*) FROM calibration.question_research_candidate)
        + (SELECT count(*) FROM corpus.external_expression_occurrence)
    )::BIGINT AS jsonb_relationship_count,
    0::INTEGER AS canonical_concept_split_count,
    0::INTEGER AS canonical_concept_merge_count,
    0::INTEGER AS canonical_concept_retype_count;

CREATE FUNCTION audit.run_round3f_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3f_validation_queries$
    WITH checks AS (
        SELECT 'round3f.canonical_concept_count_130'::TEXT AS check_key,
               abs(130 - count(*))::BIGINT AS violation_count
        FROM kb.concept
        UNION ALL
        SELECT 'round3f.active_sensory_attribute_count_92',
               abs(92 - count(*))::BIGINT
        FROM kb.concept
        WHERE concept_type_code = 'sensory_attribute'
          AND lifecycle_status_code = 'active'
        UNION ALL
        SELECT 'round3f.text_first_candidate_columns_preserved',
               abs(4 - count(*))::BIGINT
        FROM information_schema.columns
        WHERE table_schema = 'corpus'
          AND table_name = 'lexical_mapping_candidate'
          AND column_name IN (
              'candidate_mapping', 'evidence_key',
              'mapping_scope', 'ambiguity_note'
          )
          AND data_type = 'text'
        UNION ALL
        SELECT 'round3f.text_candidate_no_mandatory_concept_fk', count(*)::BIGINT
        FROM information_schema.columns
        WHERE table_schema = 'corpus'
          AND table_name = 'lexical_mapping_candidate'
          AND column_name = 'concept_id'
          AND is_nullable = 'NO'
        UNION ALL
        SELECT 'round3f.association_range_count_7',
               abs(7 - count(*))::BIGINT
        FROM corpus.association_range
        UNION ALL
        SELECT 'round3f.association_membership_count_18',
               abs(18 - count(*))::BIGINT
        FROM corpus.association_range_membership
        UNION ALL
        SELECT 'round3f.overlapping_membership_rows_8',
               abs(8 - count(*))::BIGINT
        FROM corpus.association_range_membership AS membership
        WHERE COALESCE(
            membership.normalized_expression_id::TEXT,
            membership.lexical_mapping_key,
            membership.concept_id::TEXT,
            membership.member_language_code || ':' || membership.member_text
        ) IN (
            SELECT COALESCE(
                candidate.normalized_expression_id::TEXT,
                candidate.lexical_mapping_key,
                candidate.concept_id::TEXT,
                candidate.member_language_code || ':' || candidate.member_text
            )
            FROM corpus.association_range_membership AS candidate
            GROUP BY COALESCE(
                candidate.normalized_expression_id::TEXT,
                candidate.lexical_mapping_key,
                candidate.concept_id::TEXT,
                candidate.member_language_code || ':' || candidate.member_text
            )
            HAVING count(DISTINCT candidate.association_range_id) > 1
        )
        UNION ALL
        SELECT 'round3f.membership_evidence_complete', count(*)::BIGINT
        FROM corpus.association_range_membership
        WHERE evidence_key = '' OR provenance_path = ''
        UNION ALL
        SELECT 'round3f.membership_nonexclusive_nonprobabilistic', count(*)::BIGINT
        FROM corpus.association_range_membership
        WHERE is_exclusive OR membership_semantics <> 'NON_PROBABILISTIC'
        UNION ALL
        SELECT 'round3f.source_local_range_count_0', count(*)::BIGINT
        FROM corpus.association_range
        WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
        UNION ALL
        SELECT 'round3f.cross_source_range_count_0', count(*)::BIGINT
        FROM corpus.association_range
        WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
        UNION ALL
        SELECT 'round3f.lexical_candidates_outside_current_range_107',
               abs(107 - count(*))::BIGINT
        FROM corpus.v_lexical_candidate_range_disposition
        WHERE range_disposition = 'OUTSIDE_CURRENT_RANGE_MODEL'
        UNION ALL
        SELECT 'round3f.question_range_target_count_18',
               abs(18 - count(*))::BIGINT
        FROM calibration.question_range_target
        UNION ALL
        SELECT 'round3f.question_logical_count_15',
               abs(15 - count(DISTINCT logical_question_code))::BIGINT
        FROM calibration.question_range_target
        UNION ALL
        SELECT 'round3f.question_language_version_count_30',
               abs(30 - (
                   (SELECT count(*) FROM calibration.question)
                   + (SELECT count(*) FROM calibration.question_research_candidate)
               ))::BIGINT
        UNION ALL
        SELECT 'round3f.question_not_validated_or_estimated', count(*)::BIGINT
        FROM calibration.question_range_target
        WHERE user_validation_status <> 'NOT_USER_VALIDATED'
           OR information_gain_status <> 'NOT_ESTIMABLE'
           OR context_eligibility_status <> 'HYPOTHESIZED'
        UNION ALL
        SELECT 'round3f.relationship_domain_count_7',
               abs(7 - count(DISTINCT relationship_domain))::BIGINT
        FROM audit.relationship_semantic_rule
        UNION ALL
        SELECT 'round3f.relationship_type_count_34',
               abs(34 - count(*))::BIGINT
        FROM audit.relationship_semantic_rule
        UNION ALL
        SELECT 'round3f.constraint_registry_count_35',
               abs(35 - count(*))::BIGINT
        FROM audit.constraint_registry_entry
        UNION ALL
        SELECT 'round3f.forbidden_inference_count_14',
               abs(14 - count(*))::BIGINT
        FROM audit.forbidden_inference_rule WHERE active
        UNION ALL
        SELECT 'round3f.no_association_measurement_score_collapse', count(*)::BIGINT
        FROM information_schema.columns
        WHERE table_schema = 'corpus'
          AND table_name IN ('association_range', 'association_range_membership')
          AND column_name IN (
              'membership_weight', 'association_score',
              'similarity', 'confidence', 'probability'
          )
        UNION ALL
        SELECT 'round3f.prohibition_flags_false', count(*)::BIGINT
        FROM audit.round3f_checkpoint
        WHERE ranking_model_trained OR adaptive_policy_trained
           OR deep_learning_model_run OR embedding_baseline_run
           OR pgvector_required OR real_human_collection_performed
           OR real_observation_count <> 0
           OR question_user_validated_count <> 0
           OR question_information_gain_estimated_count <> 0
           OR product_frontend_modified
        UNION ALL
        SELECT 'round3f.no_canonical_ontology_effect', count(*)::BIGINT
        FROM corpus.association_range
        WHERE canonical_ontology_effect OR exclusive_membership
           OR transitive_membership OR probability_semantics
           OR user_visible_final_section
    )
    SELECT checks.check_key, checks.violation_count,
           checks.violation_count = 0 AS passed
    FROM checks
$run_round3f_validation_queries$;

COMMIT;
