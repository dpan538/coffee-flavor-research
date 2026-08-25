\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SET LOCAL enable_seqscan = off;

EXPLAIN (COSTS OFF)
SELECT evidence_claim_key, source_family_key, evidence_direction
FROM evidence.relationship_evidence_claim
WHERE target_entity_type = 'MEMBERSHIP'
  AND target_entity_key = 'membership.roast-spice-smoke.smoke'
  AND evidence_direction = 'SUPPORTS';

EXPLAIN (COSTS OFF)
SELECT evidence_claim_key, target_entity_key, evidence_direction
FROM evidence.relationship_evidence_claim
WHERE source_family_key = 'family.liberica-ratapanel-2025'
  AND source_key = 'mendeley.liberica-sensory.v1'
  AND snapshot_key = 'snapshot.mendeley-liberica.v1';

EXPLAIN (COSTS OFF)
SELECT review_key, disposition, new_lifecycle
FROM kb.relationship_review_decision
WHERE association_range_membership_id = (
    SELECT association_range_membership_id
    FROM corpus.association_range_membership
    WHERE membership_key = 'membership.roast-spice-smoke.smoke'
)
AND reviewed_round = '3G';

ROLLBACK;

\echo ROUND3G_QUERY_PLAN_TEST_PASS=true
