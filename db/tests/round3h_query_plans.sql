\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SET LOCAL enable_seqscan = off;

EXPLAIN (COSTS OFF)
SELECT partition_key, feature_key, harmonization_status, pooling_allowed
FROM evidence.model_prebuild_partition_feature
WHERE partition_key = 'partition.round3h.iswaldi'
  AND feature_key = 'feature.descriptor-intensity';

EXPLAIN (COSTS OFF)
SELECT context_cell_key, coffee_identity, preparation_family,
       roast_source_label
FROM audit.model_prebuild_context_cell
WHERE source_family_key = 'family.bollen-robusta-qgraders-2024'
  AND preparation_family = 'immersion-cupping'
  AND roast_source_label = 'medium_source_reported';

EXPLAIN (COSTS OFF)
SELECT evidence_claim_key, source_family_key, evidence_direction
FROM evidence.relationship_evidence_claim
WHERE target_entity_type = 'MEMBERSHIP'
  AND target_entity_key = 'membership.cocoa-nut-caramel.cocoa'
  AND evidence_direction = 'SUPPORTS';

EXPLAIN (COSTS OFF)
SELECT question_evidence_key, question_range_target_id,
       independent_origin_count
FROM calibration.model_prebuild_question_evidence
WHERE question_range_target_id = (
    SELECT question_range_target_id
    FROM calibration.question_range_target
    WHERE question_range_target_key =
        'question-range.acidity-character.acidity-character'
);

ROLLBACK;

\echo ROUND3H_QUERY_PLAN_TEST_PASS=true
