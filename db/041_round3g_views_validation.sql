\set ON_ERROR_STOP on

BEGIN;

CREATE VIEW audit.v_round3g_source_completeness AS
WITH source_counts AS (
    SELECT
        count(*) FILTER (WHERE admitted)::NUMERIC AS admitted_count,
        count(*) FILTER (
            WHERE admitted
              AND source_family_key <> ''
              AND title <> '' AND authors_or_owner <> ''
              AND doi_or_stable_url <> '' AND repository <> ''
              AND exact_version <> '' AND source_type <> ''
              AND geography <> '' AND language <> ''
              AND population_or_panel <> '' AND sensory_method <> ''
              AND preparation_coverage <> '' AND roast_coverage <> ''
              AND milk_coverage <> '' AND license <> ''
              AND jsonb_array_length(file_list) > 0
              AND evidence_role <> '' AND evidence_locator <> ''
              AND limitations <> '' AND independence_note <> ''
        )::NUMERIC AS complete_count,
        count(*) FILTER (
            WHERE admitted AND rights_review_status = 'CLEARED'
        )::NUMERIC AS rights_count,
        count(*) FILTER (
            WHERE admitted AND privacy_review_status = 'REVIEWED'
              AND privacy_decision <> 'REJECTED_PRIVACY'
        )::NUMERIC AS privacy_count
    FROM evidence.relationship_source
), file_counts AS (
    SELECT
        count(*)::NUMERIC AS admitted_file_count,
        count(*) FILTER (
            WHERE hash_verified AND declared_sha256 = verified_sha256
        )::NUMERIC AS verified_file_count
    FROM evidence.relationship_source_file
)
SELECT
    admitted_count::BIGINT AS admitted_source_count,
    round(complete_count / NULLIF(admitted_count, 0), 4)
        AS source_annotation_completeness,
    round(rights_count / NULLIF(admitted_count, 0), 4)
        AS source_rights_review_rate,
    round(privacy_count / NULLIF(admitted_count, 0), 4)
        AS source_privacy_review_rate,
    admitted_file_count::BIGINT AS admitted_source_file_count,
    verified_file_count::BIGINT AS verified_source_file_count,
    round(verified_file_count / NULLIF(admitted_file_count, 0), 4)
        AS admitted_source_file_hash_rate
FROM source_counts CROSS JOIN file_counts;

CREATE VIEW audit.v_round3g_evidence_completeness AS
WITH claim_counts AS (
    SELECT
        count(*)::NUMERIC AS claim_count,
        count(*) FILTER (
            WHERE source_family_key <> '' AND source_key <> ''
              AND snapshot_key <> '' AND target_entity_key <> ''
              AND evidence_locator <> '' AND method <> ''
        )::NUMERIC AS provenance_count
    FROM evidence.relationship_evidence_claim
), review_counts AS (
    SELECT
        (
            (SELECT count(*) FROM kb.relationship_review_decision
             WHERE reviewed_round = '3G')
            + (SELECT count(*) FROM calibration.question_target_review_decision
               WHERE reviewed_round = '3G')
            + (SELECT count(*) FROM audit.range_review_decision
               WHERE reviewed_round = '3G')
        )::NUMERIC AS review_count
)
SELECT
    claim_count::BIGINT AS evidence_claim_count,
    provenance_count::BIGINT AS provenance_covered_claim_count,
    round(provenance_count / NULLIF(claim_count, 0), 4)
        AS relationship_evidence_provenance_rate,
    review_count::BIGINT AS review_disposition_count,
    round(review_count / 43.0, 4) AS relationship_review_disposition_rate
FROM claim_counts CROSS JOIN review_counts;

CREATE VIEW audit.v_round3g_range_review_coverage AS
SELECT
    count(*)::BIGINT AS current_range_count,
    count(decision.review_key)::BIGINT AS reviewed_range_count,
    count(decision.review_key) = count(*) AS all_ranges_reviewed
FROM corpus.association_range AS range
LEFT JOIN audit.range_review_decision AS decision
  ON decision.association_range_id = range.association_range_id
 AND decision.reviewed_round = '3G';

CREATE VIEW audit.v_round3g_promotion_audit AS
WITH membership_promotions AS (
    SELECT
        membership.membership_key,
        membership.lifecycle_status,
        decision.disposition,
        count(DISTINCT family.canonical_origin_key) FILTER (
            WHERE claim.evidence_direction = 'SUPPORTS'
              AND claim.review_status = 'REVIEWED'
              AND claim.support_count >= 3
              AND claim.document_count >= 2
              AND family.counts_as_independent
        ) AS independent_supporting_origin_count,
        count(claim.evidence_claim_key) FILTER (
            WHERE claim.evidence_direction = 'SUPPORTS'
              AND claim.evidence_locator <> ''
        ) AS located_supporting_claim_count
    FROM corpus.association_range_membership AS membership
    LEFT JOIN kb.relationship_review_decision AS decision
      ON decision.association_range_membership_id =
         membership.association_range_membership_id
     AND decision.reviewed_round = '3G'
    LEFT JOIN evidence.relationship_evidence_claim AS claim
      ON claim.target_entity_type = 'MEMBERSHIP'
     AND claim.target_entity_key = membership.membership_key
    LEFT JOIN evidence.source_family AS family
      ON family.source_family_key = claim.source_family_key
    WHERE membership.lifecycle_status IN (
        'SOURCE_LOCAL_SUPPORTED', 'CROSS_SOURCE_SUPPORTED'
    )
    GROUP BY membership.membership_key, membership.lifecycle_status,
             decision.disposition
)
SELECT
    count(*)::BIGINT AS promoted_membership_count,
    count(*) FILTER (
        WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
    )::BIGINT AS source_local_promoted_membership_count,
    count(*) FILTER (
        WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
    )::BIGINT AS cross_source_promoted_membership_count,
    count(*) FILTER (
        WHERE located_supporting_claim_count = 0
           OR disposition IS NULL
           OR (
               lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
               AND independent_supporting_origin_count < 1
           )
           OR (
               lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
               AND independent_supporting_origin_count < 2
           )
    )::BIGINT AS unsupported_promotion_count
FROM membership_promotions;

CREATE VIEW audit.v_round3g_relationship_constraint_delta AS
SELECT
    (SELECT count(*) FROM evidence.source_family
     WHERE admitted AND introduced_round = '3G')::BIGINT
        AS new_source_family_count,
    (SELECT count(*) FROM evidence.relationship_source
     WHERE admitted)::BIGINT AS new_source_count,
    (SELECT count(*) FROM evidence.relationship_source_snapshot
     WHERE admitted)::BIGINT AS new_snapshot_count,
    (SELECT count(*) FROM evidence.relationship_evidence_claim)::BIGINT
        AS new_evidence_claim_count,
    (SELECT count(*) FROM kb.relationship_review_decision
     WHERE reviewed_round = '3G')::BIGINT AS reviewed_membership_count,
    (SELECT count(*) FROM kb.relationship_review_decision
     WHERE reviewed_round = '3G'
       AND disposition IN (
           'PROMOTE_SOURCE_LOCAL', 'PROMOTE_CROSS_SOURCE'
       ))::BIGINT AS promoted_membership_count,
    (SELECT count(*) FROM kb.relationship_review_decision
     WHERE reviewed_round = '3G'
       AND disposition = 'RETAIN_CANDIDATE')::BIGINT
        AS retained_membership_count,
    (SELECT count(*) FROM kb.relationship_review_decision
     WHERE reviewed_round = '3G'
       AND disposition = 'REJECT')::BIGINT AS rejected_membership_count,
    (SELECT count(*) FROM kb.relationship_review_decision
     WHERE reviewed_round = '3G'
       AND disposition = 'RETURN_TO_UNRESOLVED')::BIGINT
        AS unresolved_membership_count,
    (SELECT count(*) FROM calibration.question_target_review_decision
     WHERE reviewed_round = '3G')::BIGINT
        AS reviewed_question_target_count,
    (SELECT count(*) FROM calibration.question_target_review_decision
     WHERE reviewed_round = '3G'
       AND disposition = 'RETAIN_HYPOTHESIS')::BIGINT
        AS retained_question_target_count,
    (SELECT count(*) FROM calibration.question_target_review_decision
     WHERE reviewed_round = '3G'
       AND disposition = 'REJECT_TARGET')::BIGINT
        AS rejected_question_target_count,
    4::INTEGER AS new_relationship_type_count,
    (
        (SELECT count(*) FROM evidence.relationship_evidence_claim)
        + (SELECT count(*) FROM kb.relationship_review_decision
           WHERE reviewed_round = '3G')
        + (SELECT count(*) FROM calibration.question_target_review_decision
           WHERE reviewed_round = '3G')
        + (SELECT count(*) FROM audit.range_review_decision
           WHERE reviewed_round = '3G')
    )::BIGINT AS new_relationship_instance_count,
    (SELECT count(*) FROM audit.round3g_constraint_registry)::BIGINT
        AS new_constraint_count,
    20::INTEGER AS new_negative_test_count,
    (SELECT count(*) FROM audit.round3g_constraint_registry
     WHERE constraint_key LIKE '%promotion%'
        OR constraint_key LIKE '%independence%')::BIGINT
        AS new_promotion_gate_count,
    0::INTEGER AS automatic_promotion_path_count,
    0::INTEGER AS canonical_concept_change_count,
    0::INTEGER AS active_range_change_count;

CREATE FUNCTION audit.run_round3g_expected_state_gate()
RETURNS TABLE (
    metric_key TEXT,
    baseline_value TEXT,
    minimum_expected_value TEXT,
    preferred_expected_value TEXT,
    observed_value TEXT,
    hard_gate BOOLEAN,
    minimum_gate BOOLEAN,
    preferred_gate BOOLEAN,
    passed BOOLEAN,
    evidence_path TEXT
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3g_expected_state_gate$
    WITH observed AS (
        SELECT
            (SELECT count(*) FROM kb.concept) AS concepts,
            (SELECT count(*) FROM kb.concept
             WHERE concept_type_code = 'sensory_attribute'
               AND lifecycle_status_code = 'active') AS sensory,
            (SELECT count(*) FROM corpus.association_range) AS ranges,
            (SELECT count(*) FROM corpus.association_range_membership)
                AS memberships,
            (SELECT count(*) FROM corpus.association_range_membership AS m
             WHERE COALESCE(
                 m.normalized_expression_id::TEXT, m.lexical_mapping_key,
                 m.concept_id::TEXT,
                 m.member_language_code || ':' || m.member_text
             ) IN (
                 SELECT COALESCE(
                     x.normalized_expression_id::TEXT,
                     x.lexical_mapping_key, x.concept_id::TEXT,
                     x.member_language_code || ':' || x.member_text
                 )
                 FROM corpus.association_range_membership AS x
                 GROUP BY COALESCE(
                     x.normalized_expression_id::TEXT,
                     x.lexical_mapping_key, x.concept_id::TEXT,
                     x.member_language_code || ':' || x.member_text
                 ) HAVING count(DISTINCT x.association_range_id) > 1
             )) AS overlaps,
            (SELECT count(*) FROM corpus.association_range
             WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED')
                AS local_ranges,
            (SELECT count(*) FROM corpus.association_range
             WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED')
                AS cross_ranges,
            (SELECT count(*) FROM calibration.question_range_target)
                AS question_targets,
            (SELECT count(*) FROM corpus.lexical_mapping_candidate)
                AS lexical_candidates,
            (SELECT count(*)
             FROM corpus.v_lexical_candidate_range_disposition
             WHERE range_disposition = 'OUTSIDE_CURRENT_RANGE_MODEL')
                AS outside_candidates,
            (SELECT source_annotation_completeness
             FROM audit.v_round3g_source_completeness) AS source_complete,
            (SELECT source_rights_review_rate
             FROM audit.v_round3g_source_completeness) AS rights_rate,
            (SELECT source_privacy_review_rate
             FROM audit.v_round3g_source_completeness) AS privacy_rate,
            (SELECT admitted_source_file_hash_rate
             FROM audit.v_round3g_source_completeness) AS hash_rate,
            (SELECT relationship_evidence_provenance_rate
             FROM audit.v_round3g_evidence_completeness) AS evidence_rate,
            (SELECT relationship_review_disposition_rate
             FROM audit.v_round3g_evidence_completeness) AS review_rate,
            (SELECT unsupported_promotion_count
             FROM audit.v_round3g_promotion_audit) AS unsupported_promotions,
            (SELECT count(*) FROM audit.range_review_decision
             WHERE reviewed_round = '3G') AS range_reviews,
            (SELECT count(*) FROM kb.relationship_review_decision
             WHERE reviewed_round = '3G') AS membership_reviews,
            (SELECT count(*)
             FROM calibration.question_target_review_decision
             WHERE reviewed_round = '3G') AS question_reviews,
            (SELECT count(*) FROM evidence.source_candidate_register)
                AS candidates,
            (SELECT count(*) FROM evidence.source_family
             WHERE admitted AND counts_as_independent) AS families,
            (SELECT count(*) FROM evidence.source_family
             WHERE admitted AND family_type IN (
                 'COFFEE_SENSORY', 'CONSUMER_STUDY'
             )) AS coffee_families,
            (SELECT count(*) FROM evidence.source_family
             WHERE admitted AND family_type IN (
                 'BILINGUAL_LEXICAL', 'CONTEMPORARY_LANGUAGE'
             )) AS lexical_families,
            (SELECT count(*) FROM evidence.relationship_source_snapshot
             WHERE admitted) AS snapshots,
            (SELECT count(*) FROM evidence.relationship_evidence_claim)
                AS claims,
            (SELECT source_local_promoted_membership_count
             FROM audit.v_round3g_promotion_audit) AS local_promotions,
            (SELECT count(*) FROM audit.round3g_threshold_revision)
                AS threshold_revisions,
            (SELECT bool_and(expected_state_frozen_before_import)
             FROM audit.round3g_checkpoint) AS expected_frozen,
            (SELECT coalesce(sum(question_user_validated_count), 0)
             FROM audit.round3g_checkpoint) AS user_validated,
            (SELECT coalesce(sum(question_information_gain_estimated_count), 0)
             FROM audit.round3g_checkpoint) AS information_gain,
            (SELECT coalesce(sum(model_or_embedding_run_count), 0)
             FROM audit.round3g_checkpoint) AS model_runs,
            (SELECT coalesce(sum(real_observation_count), 0)
             FROM audit.round3g_checkpoint) AS observations,
            (SELECT coalesce(sum(automatic_promotion_path_count), 0)
             FROM audit.round3g_checkpoint) AS automatic_promotions
    ), metrics AS (
        SELECT value.*
        FROM observed AS o
        CROSS JOIN LATERAL (
            VALUES
                ('CANONICAL_CONCEPT_COUNT', '130', '130', NULL, o.concepts::TEXT, TRUE, FALSE, FALSE, o.concepts = 130, 'kb.concept'),
                ('ACTIVE_SENSORY_ATTRIBUTE_COUNT', '92', '92', NULL, o.sensory::TEXT, TRUE, FALSE, FALSE, o.sensory = 92, 'kb.concept'),
                ('ASSOCIATION_RANGE_COUNT', '7', '7', NULL, o.ranges::TEXT, TRUE, FALSE, FALSE, o.ranges = 7, 'corpus.association_range'),
                ('ASSOCIATION_RANGE_MEMBERSHIP_COUNT', '18', '18', NULL, o.memberships::TEXT, TRUE, FALSE, FALSE, o.memberships = 18, 'corpus.association_range_membership'),
                ('OVERLAPPING_MEMBERSHIP_COUNT', '8', '8', NULL, o.overlaps::TEXT, TRUE, FALSE, FALSE, o.overlaps = 8, 'corpus.association_range_membership'),
                ('SOURCE_LOCAL_SUPPORTED_RANGE_COUNT', '0', '0', NULL, o.local_ranges::TEXT, TRUE, FALSE, FALSE, o.local_ranges = 0, 'corpus.association_range'),
                ('CROSS_SOURCE_SUPPORTED_RANGE_COUNT', '0', '0', NULL, o.cross_ranges::TEXT, TRUE, FALSE, FALSE, o.cross_ranges = 0, 'corpus.association_range'),
                ('QUESTION_RANGE_TARGET_COUNT', '18', '18', NULL, o.question_targets::TEXT, TRUE, FALSE, FALSE, o.question_targets = 18, 'calibration.question_range_target'),
                ('TEXT_FIRST_LEXICAL_CANDIDATE_COUNT', '107', '107', NULL, o.lexical_candidates::TEXT, TRUE, FALSE, FALSE, o.lexical_candidates = 107, 'corpus.lexical_mapping_candidate'),
                ('TEXT_FIRST_OUTSIDE_RANGE_COUNT', '107', '107', NULL, o.outside_candidates::TEXT, TRUE, FALSE, FALSE, o.outside_candidates = 107, 'corpus.v_lexical_candidate_range_disposition'),
                ('SOURCE_ANNOTATION_COMPLETENESS', NULL, '1.0000', NULL, to_char(o.source_complete, 'FM0.0000'), TRUE, FALSE, FALSE, o.source_complete = 1.0000, 'audit.v_round3g_source_completeness'),
                ('ADMITTED_SOURCE_RIGHTS_REVIEW_RATE', NULL, '1.0000', NULL, to_char(o.rights_rate, 'FM0.0000'), TRUE, FALSE, FALSE, o.rights_rate = 1.0000, 'audit.v_round3g_source_completeness'),
                ('ADMITTED_SOURCE_PRIVACY_REVIEW_RATE', NULL, '1.0000', NULL, to_char(o.privacy_rate, 'FM0.0000'), TRUE, FALSE, FALSE, o.privacy_rate = 1.0000, 'audit.v_round3g_source_completeness'),
                ('ADMITTED_SOURCE_FILE_HASH_RATE', NULL, '1.0000', NULL, to_char(o.hash_rate, 'FM0.0000'), TRUE, FALSE, FALSE, o.hash_rate = 1.0000, 'audit.v_round3g_source_completeness'),
                ('RELATIONSHIP_EVIDENCE_PROVENANCE_RATE', NULL, '1.0000', NULL, to_char(o.evidence_rate, 'FM0.0000'), TRUE, FALSE, FALSE, o.evidence_rate = 1.0000, 'audit.v_round3g_evidence_completeness'),
                ('RELATIONSHIP_REVIEW_DISPOSITION_RATE', NULL, '1.0000', NULL, to_char(o.review_rate, 'FM0.0000'), TRUE, FALSE, FALSE, o.review_rate = 1.0000, 'audit.v_round3g_evidence_completeness'),
                ('AUTOMATIC_PROMOTION_PATH_COUNT', NULL, '0', NULL, o.automatic_promotions::TEXT, TRUE, FALSE, FALSE, o.automatic_promotions = 0, 'audit.round3g_checkpoint'),
                ('UNSUPPORTED_PROMOTION_COUNT', NULL, '0', NULL, o.unsupported_promotions::TEXT, TRUE, FALSE, FALSE, o.unsupported_promotions = 0, 'audit.v_round3g_promotion_audit'),
                ('QUESTION_USER_VALIDATED_COUNT', '0', '0', NULL, o.user_validated::TEXT, TRUE, FALSE, FALSE, o.user_validated = 0, 'audit.round3g_checkpoint'),
                ('QUESTION_INFORMATION_GAIN_ESTIMATED_COUNT', '0', '0', NULL, o.information_gain::TEXT, TRUE, FALSE, FALSE, o.information_gain = 0, 'audit.round3g_checkpoint'),
                ('MODEL_OR_EMBEDDING_RUN_COUNT', '0', '0', NULL, o.model_runs::TEXT, TRUE, FALSE, FALSE, o.model_runs = 0, 'audit.round3g_checkpoint'),
                ('REAL_OBSERVATION_COUNT', '0', '0', NULL, o.observations::TEXT, TRUE, FALSE, FALSE, o.observations = 0, 'audit.round3g_checkpoint'),
                ('EXPECTED_STATE_FROZEN_BEFORE_IMPORT', NULL, 'true', NULL, o.expected_frozen::TEXT, TRUE, FALSE, FALSE, o.expected_frozen, 'audit.round3g_checkpoint'),
                ('EXPECTED_STATE_THRESHOLD_REVISION_COUNT', NULL, '0', NULL, o.threshold_revisions::TEXT, TRUE, FALSE, FALSE, o.threshold_revisions = 0, 'audit.round3g_threshold_revision'),
                ('ALL_7_CURRENT_RANGES_SEARCHED_OR_REVIEWED', NULL, 'true', NULL, (o.range_reviews = 7)::TEXT, FALSE, TRUE, FALSE, o.range_reviews = 7, 'audit.range_review_decision'),
                ('ALL_18_CURRENT_MEMBERSHIPS_REVIEWED', NULL, 'true', NULL, (o.membership_reviews = 18)::TEXT, FALSE, TRUE, FALSE, o.membership_reviews = 18, 'kb.relationship_review_decision'),
                ('ALL_18_CURRENT_QUESTION_TARGETS_REVIEWED', NULL, 'true', NULL, (o.question_reviews = 18)::TEXT, FALSE, TRUE, FALSE, o.question_reviews = 18, 'calibration.question_target_review_decision'),
                ('NEW_NAMED_SOURCE_CANDIDATE_COUNT', NULL, '>=4', NULL, o.candidates::TEXT, FALSE, TRUE, FALSE, o.candidates >= 4, 'evidence.source_candidate_register'),
                ('NEW_INDEPENDENT_SOURCE_FAMILY_ADMITTED_COUNT', NULL, '>=1', NULL, o.families::TEXT, FALSE, TRUE, FALSE, o.families >= 1, 'evidence.source_family'),
                ('NEW_IMMUTABLE_SOURCE_SNAPSHOT_COUNT', NULL, '>=1', NULL, o.snapshots::TEXT, FALSE, TRUE, FALSE, o.snapshots >= 1, 'evidence.relationship_source_snapshot'),
                ('NEW_ADMITTED_EVIDENCE_RECORD_COUNT', NULL, '>0', NULL, o.claims::TEXT, FALSE, TRUE, FALSE, o.claims > 0, 'evidence.relationship_evidence_claim'),
                ('NEW_INDEPENDENT_SOURCE_FAMILY_ADMITTED_COUNT', NULL, NULL, '>=2', o.families::TEXT, FALSE, FALSE, TRUE, o.families >= 2, 'evidence.source_family'),
                ('NEW_COFFEE_SENSORY_OR_CONSUMER_SOURCE_FAMILY_COUNT', NULL, NULL, '>=1', o.coffee_families::TEXT, FALSE, FALSE, TRUE, o.coffee_families >= 1, 'evidence.source_family'),
                ('NEW_BILINGUAL_LEXICAL_OR_CONTEMPORARY_SOURCE_FAMILY_COUNT', NULL, NULL, '>=1', o.lexical_families::TEXT, FALSE, FALSE, TRUE, o.lexical_families >= 1, 'evidence.source_family'),
                ('SOURCE_LOCAL_RELATIONSHIP_PROMOTION_COUNT', NULL, NULL, '>=1 soft target', o.local_promotions::TEXT, FALSE, FALSE, TRUE, o.local_promotions >= 1, 'audit.v_round3g_promotion_audit')
        ) AS value(
            metric_key, baseline_value, minimum_expected_value,
            preferred_expected_value, observed_value, hard_gate,
            minimum_gate, preferred_gate, passed, evidence_path
        )
    )
    SELECT * FROM metrics
$run_round3g_expected_state_gate$;

CREATE FUNCTION audit.round3g_expected_state_result()
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $round3g_expected_state_result$
    WITH state AS (
        SELECT
            bool_and(passed) FILTER (WHERE hard_gate) AS hard_pass,
            bool_and(passed) FILTER (WHERE minimum_gate) AS minimum_pass
        FROM audit.run_round3g_expected_state_gate()
    )
    SELECT CASE
        WHEN NOT hard_pass THEN 'BLOCKED_INTEGRITY'
        WHEN NOT minimum_pass THEN 'COMPLETE_WITH_EVIDENCE_GAP'
        ELSE 'PASS'
    END
    FROM state
$round3g_expected_state_result$;

CREATE FUNCTION audit.assert_round3g_expected_state_result(
    requested_result TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
SET search_path = pg_catalog
AS $assert_round3g_expected_state_result$
DECLARE actual_result TEXT;
BEGIN
    SELECT audit.round3g_expected_state_result() INTO actual_result;
    IF upper(btrim(requested_result)) IS DISTINCT FROM actual_result THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_expected_state_truth_ck',
            MESSAGE = format(
                'requested result %s does not match actual result %s',
                requested_result, actual_result
            );
    END IF;
    RETURN actual_result;
END
$assert_round3g_expected_state_result$;

CREATE FUNCTION audit.assert_round3g_gate_classification(
    requested_result TEXT,
    hard_gate_pass BOOLEAN,
    minimum_gate_pass BOOLEAN
)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
SET search_path = pg_catalog
AS $assert_round3g_gate_classification$
DECLARE expected_result TEXT;
BEGIN
    expected_result := CASE
        WHEN NOT hard_gate_pass THEN 'BLOCKED_INTEGRITY'
        WHEN NOT minimum_gate_pass THEN 'COMPLETE_WITH_EVIDENCE_GAP'
        ELSE 'PASS'
    END;
    IF upper(btrim(requested_result)) IS DISTINCT FROM expected_result THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_expected_state_truth_ck',
            MESSAGE = 'requested expected-state classification contradicts gate inputs';
    END IF;
    RETURN expected_result;
END
$assert_round3g_gate_classification$;

CREATE FUNCTION audit.run_round3g_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3g_validation_queries$
    WITH checks AS (
        SELECT 'round3g.canonical_concept_count_130'::TEXT AS check_key,
               abs(130 - count(*))::BIGINT AS violation_count
        FROM kb.concept
        UNION ALL
        SELECT 'round3g.active_sensory_attribute_count_92',
               abs(92 - count(*))::BIGINT
        FROM kb.concept
        WHERE concept_type_code = 'sensory_attribute'
          AND lifecycle_status_code = 'active'
        UNION ALL
        SELECT 'round3g.association_range_count_7',
               abs(7 - count(*))::BIGINT
        FROM corpus.association_range
        UNION ALL
        SELECT 'round3g.association_membership_count_18',
               abs(18 - count(*))::BIGINT
        FROM corpus.association_range_membership
        UNION ALL
        SELECT 'round3g.no_active_or_new_range', count(*)::BIGINT
        FROM corpus.association_range
        WHERE lifecycle_status = 'ACTIVE_FOR_CALIBRATION'
        UNION ALL
        SELECT 'round3g.named_source_candidates_at_least_4',
               greatest(4 - count(*), 0)::BIGINT
        FROM evidence.source_candidate_register
        UNION ALL
        SELECT 'round3g.independent_families_at_least_1',
               greatest(1 - count(*), 0)::BIGINT
        FROM evidence.source_family
        WHERE admitted AND counts_as_independent
        UNION ALL
        SELECT 'round3g.immutable_snapshots_at_least_1',
               greatest(1 - count(*), 0)::BIGINT
        FROM evidence.relationship_source_snapshot WHERE admitted
        UNION ALL
        SELECT 'round3g.admitted_evidence_present',
               CASE WHEN count(*) > 0 THEN 0 ELSE 1 END::BIGINT
        FROM evidence.relationship_evidence_claim
        UNION ALL
        SELECT 'round3g.source_annotation_complete',
               CASE WHEN source_annotation_completeness = 1.0000
                    THEN 0 ELSE 1 END::BIGINT
        FROM audit.v_round3g_source_completeness
        UNION ALL
        SELECT 'round3g.source_rights_complete',
               CASE WHEN source_rights_review_rate = 1.0000
                    THEN 0 ELSE 1 END::BIGINT
        FROM audit.v_round3g_source_completeness
        UNION ALL
        SELECT 'round3g.source_privacy_complete',
               CASE WHEN source_privacy_review_rate = 1.0000
                    THEN 0 ELSE 1 END::BIGINT
        FROM audit.v_round3g_source_completeness
        UNION ALL
        SELECT 'round3g.file_hash_complete',
               CASE WHEN admitted_source_file_hash_rate = 1.0000
                    THEN 0 ELSE 1 END::BIGINT
        FROM audit.v_round3g_source_completeness
        UNION ALL
        SELECT 'round3g.evidence_provenance_complete',
               CASE WHEN relationship_evidence_provenance_rate = 1.0000
                    THEN 0 ELSE 1 END::BIGINT
        FROM audit.v_round3g_evidence_completeness
        UNION ALL
        SELECT 'round3g.review_disposition_complete',
               CASE WHEN relationship_review_disposition_rate = 1.0000
                    THEN 0 ELSE 1 END::BIGINT
        FROM audit.v_round3g_evidence_completeness
        UNION ALL
        SELECT 'round3g.all_7_ranges_reviewed', abs(7 - count(*))::BIGINT
        FROM audit.range_review_decision WHERE reviewed_round = '3G'
        UNION ALL
        SELECT 'round3g.all_18_memberships_reviewed',
               abs(18 - count(*))::BIGINT
        FROM kb.relationship_review_decision WHERE reviewed_round = '3G'
        UNION ALL
        SELECT 'round3g.all_18_question_targets_reviewed',
               abs(18 - count(*))::BIGINT
        FROM calibration.question_target_review_decision
        WHERE reviewed_round = '3G'
        UNION ALL
        SELECT 'round3g.contradictory_evidence_retained', count(*)::BIGINT
        FROM evidence.relationship_evidence_claim
        WHERE evidence_direction IN ('CHALLENGES', 'MIXED')
          AND NOT contradictory_evidence_retained
        UNION ALL
        SELECT 'round3g.unsupported_promotion_count_0',
               unsupported_promotion_count::BIGINT
        FROM audit.v_round3g_promotion_audit
        UNION ALL
        SELECT 'round3g.no_bilingual_review_claim', count(*)::BIGINT
        FROM corpus.association_range_membership
        WHERE lifecycle_status = 'BILINGUAL_REVIEWED'
        UNION ALL
        SELECT 'round3g.question_not_validated_or_estimated', count(*)::BIGINT
        FROM calibration.question_range_target
        WHERE user_validation_status <> 'NOT_USER_VALIDATED'
           OR information_gain_status <> 'NOT_ESTIMABLE'
        UNION ALL
        SELECT 'round3g.expected_state_revision_count_0', count(*)::BIGINT
        FROM audit.round3g_threshold_revision
        UNION ALL
        SELECT 'round3g.expected_state_frozen_before_import', count(*)::BIGINT
        FROM audit.round3g_checkpoint
        WHERE NOT expected_state_frozen_before_import
        UNION ALL
        SELECT 'round3g.prohibition_flags_false', count(*)::BIGINT
        FROM audit.round3g_checkpoint
        WHERE new_active_association_range_count <> 0
           OR automatic_promotion_path_count <> 0
           OR real_human_collection_performed
           OR real_observation_count <> 0
           OR question_user_validated_count <> 0
           OR question_information_gain_estimated_count <> 0
           OR model_or_embedding_run_count <> 0
           OR product_frontend_modified
        UNION ALL
        SELECT 'round3g.raw_participant_file_external_only', count(*)::BIGINT
        FROM evidence.relationship_source_file
        WHERE contains_participant_identifiers
          AND (public_export_decision <> 'EXTERNAL_ONLY'
               OR local_path IS NOT NULL)
        UNION ALL
        SELECT 'round3g.no_duplicate_independent_origin',
               count(*)::BIGINT
        FROM (
            SELECT canonical_origin_key
            FROM evidence.source_family
            WHERE counts_as_independent
            GROUP BY canonical_origin_key HAVING count(*) > 1
        ) AS duplicate_origin
        UNION ALL
        SELECT 'round3g.two_access_requests_unsent',
               abs(2 - count(*))::BIGINT
        FROM audit.data_access_request_update WHERE NOT request_sent
        UNION ALL
        SELECT 'round3g.expected_state_result_pass',
               CASE WHEN audit.round3g_expected_state_result() = 'PASS'
                    THEN 0 ELSE 1 END::BIGINT
    )
    SELECT checks.check_key, checks.violation_count,
           checks.violation_count = 0 AS passed
    FROM checks
$run_round3g_validation_queries$;

COMMIT;
