\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SELECT source_family_key, family_type, canonical_origin_key,
       counts_as_independent, admitted
FROM evidence.source_family
ORDER BY source_family_key;

SELECT source_key, exact_version, license, privacy_decision,
       public_export_decision, evidence_role
FROM evidence.relationship_source
ORDER BY source_key;

SELECT evidence_claim_key, target_entity_type, target_entity_key,
       source_family_key, evidence_direction, evidence_locator,
       support_count, document_count
FROM evidence.relationship_evidence_claim
ORDER BY evidence_claim_key;

SELECT membership.membership_key, membership.lifecycle_status,
       decision.disposition, decision.supporting_source_families,
       decision.challenging_source_families
FROM corpus.association_range_membership AS membership
JOIN kb.relationship_review_decision AS decision
  ON decision.association_range_membership_id =
     membership.association_range_membership_id
ORDER BY membership.membership_key;

SELECT target.question_range_target_key, decision.disposition,
       target.user_validation_status, target.information_gain_status
FROM calibration.question_range_target AS target
JOIN calibration.question_target_review_decision AS decision
  ON decision.question_range_target_id = target.question_range_target_id
ORDER BY target.question_range_target_key;

SELECT * FROM audit.v_round3g_source_completeness;
SELECT * FROM audit.v_round3g_evidence_completeness;
SELECT * FROM audit.v_round3g_range_review_coverage;
SELECT * FROM audit.v_round3g_promotion_audit;
SELECT audit.round3g_expected_state_result();

ROLLBACK;

\echo ROUND3G_RETRIEVAL_TEST_PASS=true
