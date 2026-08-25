\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

SELECT range_key, member_entity_type, member_value, membership_role,
       evidence_basis, evidence_key
FROM corpus.v_association_range_membership
ORDER BY range_key, membership_role, member_value;

SELECT normalized_expression, candidate_mapping, range_disposition
FROM corpus.v_lexical_candidate_range_disposition
ORDER BY mapping_key
LIMIT 20;

SELECT logical_question_code, range_key, relationship_role,
       direction_kind, context_eligibility_status,
       user_validation_status, information_gain_status
FROM calibration.v_question_range_relationships
ORDER BY logical_question_code, range_key;

SELECT relationship_domain, relationship_type, instance_count,
       source_count, provenance_coverage_rate, enforcement_layer,
       unresolved_count
FROM audit.v_round3f_relationship_coverage
ORDER BY relationship_domain, relationship_type;

SELECT * FROM audit.v_round3f_constraint_coverage
ORDER BY constraint_category;

ROLLBACK;

\echo ROUND3F_RETRIEVAL_TEST_PASS=true
