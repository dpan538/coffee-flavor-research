\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3f_semantic_contract$
DECLARE failed_count BIGINT;
BEGIN
  SELECT count(*) INTO failed_count
  FROM audit.run_round3f_validation_queries()
  WHERE passed IS NOT TRUE OR violation_count <> 0;

  IF failed_count <> 0 THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3f_validation_contract_ck',
      MESSAGE = 'Round 3F validation contract reported violations';
  END IF;

  IF EXISTS (
      SELECT 1 FROM corpus.v_association_range_membership
      WHERE membership_semantics <> 'NON_PROBABILISTIC'
         OR is_exclusive
  ) OR EXISTS (
      SELECT 1 FROM calibration.v_question_range_relationships
      WHERE user_validation_status <> 'NOT_USER_VALIDATED'
         OR information_gain_status <> 'NOT_ESTIMABLE'
         OR context_eligibility_status <> 'HYPOTHESIZED'
  ) THEN
    RAISE EXCEPTION USING ERRCODE = '23514',
      CONSTRAINT = 'round3f_semantic_boundary_ck',
      MESSAGE = 'Round 3F overlap, probability or question-validation boundary changed';
  END IF;

  RAISE NOTICE 'ROUND3F_SEMANTIC_VALIDATION_PASS=true';
END;
$round3f_semantic_contract$;

SELECT * FROM audit.run_round3f_validation_queries() ORDER BY check_key;
SELECT * FROM audit.v_round3f_relationship_constraint_delta;

ROLLBACK;

\echo ROUND3F_SEMANTIC_TEST_PASS=true
