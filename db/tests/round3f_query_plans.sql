\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3f_index_contract$
BEGIN
  IF to_regclass('corpus.association_range_membership_role_idx') IS NULL
     OR to_regclass('calibration.question_range_target_question_idx') IS NULL
     OR to_regclass('corpus.association_range_membership_normalized_uq') IS NULL
     OR to_regclass('corpus.association_range_membership_text_uq') IS NULL THEN
    RAISE EXCEPTION USING ERRCODE = '42P01',
      CONSTRAINT = 'round3f_index_contract_ck',
      MESSAGE = 'Round 3F query index contract is incomplete';
  END IF;
END;
$round3f_index_contract$;

SET LOCAL enable_seqscan = off;

EXPLAIN (COSTS OFF)
SELECT association_range_membership_id, membership_role
FROM corpus.association_range_membership
WHERE association_range_id = (
    SELECT association_range_id FROM corpus.association_range
    WHERE range_key = 'fruit'
)
  AND membership_role = 'ANCHOR'
ORDER BY association_range_membership_id;

EXPLAIN (COSTS OFF)
SELECT question_range_target_key, relationship_role
FROM calibration.question_range_target
WHERE logical_question_code = 'family_direction'
ORDER BY association_range_id;

ROLLBACK;

\echo ROUND3F_QUERY_PLAN_TEST_PASS=true
