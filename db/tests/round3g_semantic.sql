\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3g_semantic_contract$
DECLARE failed_count BIGINT;
DECLARE hard_pass BOOLEAN;
DECLARE minimum_pass BOOLEAN;
DECLARE preferred_pass BOOLEAN;
BEGIN
  SELECT count(*) INTO failed_count
  FROM audit.run_round3g_validation_queries()
  WHERE passed IS NOT TRUE OR violation_count <> 0;

  IF failed_count <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3g_validation_contract_ck',
      MESSAGE = 'Round 3G validation contract reported violations';
  END IF;

  SELECT
    bool_and(passed) FILTER (WHERE hard_gate),
    bool_and(passed) FILTER (WHERE minimum_gate),
    bool_and(passed) FILTER (WHERE preferred_gate)
  INTO hard_pass, minimum_pass, preferred_pass
  FROM audit.run_round3g_expected_state_gate();

  IF hard_pass IS NOT TRUE OR minimum_pass IS NOT TRUE
     OR preferred_pass IS NOT TRUE
     OR audit.round3g_expected_state_result() <> 'PASS' THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3g_expected_state_semantic_ck',
      MESSAGE = 'Round 3G expected-state result is not hard/minimum/preferred PASS';
  END IF;

  IF (SELECT count(*) FROM evidence.relationship_evidence_claim) <> 20
     OR (SELECT count(*) FROM evidence.relationship_evidence_claim
         WHERE evidence_direction = 'SUPPORTS') <> 1
     OR (SELECT count(*) FROM evidence.relationship_evidence_claim
         WHERE evidence_direction = 'CHALLENGES') <> 3
     OR (SELECT count(*) FROM evidence.relationship_evidence_claim
         WHERE evidence_direction = 'MIXED') <> 1
     OR (SELECT count(*) FROM evidence.relationship_evidence_claim
         WHERE evidence_direction = 'INSUFFICIENT') <> 15 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3g_evidence_direction_inventory_ck',
      MESSAGE = 'Round 3G evidence direction inventory changed';
  END IF;

  IF (SELECT count(*) FROM kb.relationship_review_decision
      WHERE disposition = 'PROMOTE_SOURCE_LOCAL') <> 1
     OR (SELECT count(*) FROM kb.relationship_review_decision
         WHERE disposition = 'RETAIN_CANDIDATE') <> 17
     OR (SELECT count(*)
         FROM calibration.question_target_review_decision
         WHERE disposition = 'RETAIN_HYPOTHESIS') <> 12
     OR (SELECT count(*)
         FROM calibration.question_target_review_decision
         WHERE disposition = 'RESEARCH_SUPPORT_ADDED') <> 2
     OR (SELECT count(*)
         FROM calibration.question_target_review_decision
         WHERE disposition = 'BILINGUAL_REVIEW_REQUIRED') <> 4 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3g_review_inventory_ck',
      MESSAGE = 'Round 3G membership or question disposition inventory changed';
  END IF;

  IF EXISTS (
      SELECT 1 FROM calibration.question_range_target
      WHERE user_validation_status <> 'NOT_USER_VALIDATED'
         OR information_gain_status <> 'NOT_ESTIMABLE'
    ) OR EXISTS (
      SELECT 1 FROM corpus.association_range
      WHERE lifecycle_status <> 'CANDIDATE'
    ) OR EXISTS (
      SELECT 1 FROM audit.data_access_request_update
      WHERE request_sent
    ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3g_nonclaim_boundary_ck',
      MESSAGE = 'Round 3G validation, range or request-sending boundary changed';
  END IF;

  RAISE NOTICE 'ROUND3G_SEMANTIC_VALIDATION_PASS=true';
END;
$round3g_semantic_contract$;

SELECT * FROM audit.run_round3g_validation_queries() ORDER BY check_key;
SELECT * FROM audit.run_round3g_expected_state_gate() ORDER BY metric_key;
SELECT * FROM audit.v_round3g_relationship_constraint_delta;

ROLLBACK;

\echo ROUND3G_SEMANTIC_TEST_PASS=true
