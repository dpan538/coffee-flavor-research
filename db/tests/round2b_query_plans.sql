\set ON_ERROR_STOP on
\pset pager off

-- Round 2B representative query plans. Natural plans are captured before any
-- planner switches. The final transaction-local GiST/GIN section is an access-
-- path diagnostic only: forcing an index on this small pilot is not evidence
-- that the forced plan is faster or should be selected in production.

BEGIN;

DO $round2b_query_plan_index_contract$
BEGIN
    IF to_regclass('corpus.normalized_expression_trgm_knn_idx') IS NULL
       OR to_regclass(
              'corpus.normalized_expression_pipeline_text_uq'
          ) IS NULL
       OR to_regclass(
              'corpus.normalized_expression_frequency_rank_idx'
          ) IS NULL
       OR to_regclass(
              'corpus.normalized_expression_pair_subject_npmi_idx'
          ) IS NULL
       OR to_regclass(
              'corpus.normalized_expression_pair_object_npmi_idx'
          ) IS NULL
       OR to_regclass(
              'kb.concept_relation_active_subject_type_idx'
          ) IS NULL
       OR to_regclass(
              'kb.concept_relation_active_object_type_idx'
          ) IS NULL
       OR to_regclass('audit.retrieval_audit_case_split_idx') IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_query_plan_index_contract_ck',
            MESSAGE = 'a required Round 2B retrieval, statistic, graph, or audit index is missing';
    END IF;

    RAISE NOTICE 'ROUND2B_QUERY_PLAN_INDEX_CONTRACT_PASS=true';
END;
$round2b_query_plan_index_contract$;

\echo ROUND2B_QUERY_PLAN=audit_evaluation_join_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    audit_set.retrieval_audit_set_key,
    audit_case.audit_split_code,
    audit_case.case_ordinal,
    expression.expression_text,
    evaluation.retrieval_evaluation_key,
    inference.resolution_status_code,
    candidate.rank,
    candidate.concept_id,
    trace.retrieval_tier_code,
    review.expects_unresolved,
    judgment.relevance_grade_code
FROM audit.retrieval_audit_set AS audit_set
JOIN audit.retrieval_audit_case AS audit_case
  ON audit_case.retrieval_audit_set_id =
     audit_set.retrieval_audit_set_id
JOIN kb.lexical_expression AS expression
  ON expression.expression_id = audit_case.expression_id
LEFT JOIN audit.retrieval_evaluation AS evaluation
  ON evaluation.retrieval_audit_set_id =
     audit_set.retrieval_audit_set_id
 AND evaluation.audit_split_code = audit_case.audit_split_code
LEFT JOIN ml.mapping_inference AS inference
  ON inference.model_run_id = evaluation.model_run_id
 AND inference.observation_expression_id =
     audit_case.representative_observation_expression_id
LEFT JOIN ml.mapping_candidate AS candidate
  ON candidate.mapping_inference_id = inference.mapping_inference_id
LEFT JOIN ml.deterministic_candidate_trace AS trace
  ON trace.mapping_candidate_id = candidate.mapping_candidate_id
LEFT JOIN audit.retrieval_case_review AS review
  ON review.retrieval_audit_case_id = audit_case.retrieval_audit_case_id
 AND review.audit_review_role_code = 'adjudicated'
LEFT JOIN audit.retrieval_relevance_judgment AS judgment
  ON judgment.retrieval_case_review_id = review.retrieval_case_review_id
 AND judgment.concept_id = candidate.concept_id
ORDER BY
    audit_set.retrieval_audit_set_key,
    audit_case.audit_split_code,
    audit_case.case_ordinal,
    candidate.rank NULLS LAST;

\echo ROUND2B_QUERY_PLAN=persisted_signal_ledger_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    ledger.mapping_inference_key,
    ledger.candidate_rank,
    ledger.concept_key,
    ledger.retrieval_tier_code,
    ledger.retrieval_signal_code,
    ledger.signal_value,
    ledger.value_semantics
FROM ml.v_deterministic_candidate_signal_ledger AS ledger
ORDER BY
    ledger.mapping_inference_id,
    ledger.candidate_rank,
    ledger.signal_ordinal;

SELECT CASE
           WHEN EXISTS (
               SELECT 1
               FROM corpus.corpus_snapshot
               WHERE corpus_snapshot_key =
                     'corpus_snapshot.firstbloom_a6cb002_pilot_v1'
           ) THEN 'true'
           ELSE 'false'
       END AS round2b_seed_present
\gset

\if :round2b_seed_present

\echo ROUND2B_QUERY_PLAN=exact_normalized_dictionary_lookup_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    normalized.normalized_expression_id,
    normalized.normalized_expression_key,
    normalized.normalized_text,
    expression.expression_key,
    concept.concept_key,
    lexicalization.mapping_type_code
FROM corpus.normalization_pipeline AS pipeline
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalization_pipeline_id =
     pipeline.normalization_pipeline_id
JOIN corpus.lexical_expression_normalization AS normalization
  ON normalization.normalization_pipeline_id =
     pipeline.normalization_pipeline_id
 AND normalization.normalized_expression_id =
     normalized.normalized_expression_id
JOIN kb.lexical_expression AS expression
  ON expression.expression_id = normalization.expression_id
 AND expression.lifecycle_status_code = 'active'
 AND expression.language_tag_code = pipeline.language_tag_code
JOIN kb.lexicalization AS lexicalization
  ON lexicalization.expression_id = expression.expression_id
 AND lexicalization.lifecycle_status_code = 'active'
 AND lexicalization.valid_from <= CURRENT_TIMESTAMP
 AND (
        lexicalization.valid_until IS NULL
        OR lexicalization.valid_until > CURRENT_TIMESTAMP
     )
JOIN ref.mapping_type AS mapping_type
  ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
 AND (mapping_type.is_preferred OR mapping_type.is_approved_variant)
JOIN kb.concept AS concept
  ON concept.concept_id = lexicalization.concept_id
 AND concept.lifecycle_status_code = 'active'
WHERE pipeline.normalization_pipeline_key = 'normalization.en_v1'
  AND normalized.normalized_text = corpus.normalize_expression_v1(
      '  GRAPEFRUIT  ',
      'normalization.en_v1'
  )
ORDER BY
    mapping_type.retrieval_precedence,
    expression.expression_key,
    concept.concept_key;

\echo ROUND2B_QUERY_PLAN=exact_callable_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'grapefruit', 'en', 'normalization.en_v1', 'A', 5, 0.35::REAL
);

\echo ROUND2B_QUERY_PLAN=canonical_dictionary_knn_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    normalized.normalized_expression_id,
    normalized.normalized_expression_key,
    normalized.normalized_text,
    similarity(normalized.normalized_text, 'grapfruit') AS similarity
FROM corpus.normalized_expression AS normalized
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id =
     normalized.normalization_pipeline_id
WHERE pipeline.normalization_pipeline_key = 'normalization.en_v1'
  AND EXISTS (
      SELECT 1
      FROM corpus.lexical_expression_normalization AS normalization
      JOIN kb.lexical_expression AS expression
        ON expression.expression_id = normalization.expression_id
       AND expression.lifecycle_status_code = 'active'
       AND expression.language_tag_code = 'en'
      JOIN kb.lexicalization AS lexicalization
        ON lexicalization.expression_id = expression.expression_id
       AND lexicalization.lifecycle_status_code = 'active'
       AND lexicalization.valid_from <= CURRENT_TIMESTAMP
       AND (
              lexicalization.valid_until IS NULL
              OR lexicalization.valid_until > CURRENT_TIMESTAMP
           )
      JOIN ref.mapping_type AS mapping_type
        ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
       AND (
              mapping_type.is_preferred
              OR mapping_type.is_approved_variant
           )
      JOIN kb.concept AS concept
        ON concept.concept_id = lexicalization.concept_id
       AND concept.lifecycle_status_code = 'active'
      WHERE normalization.normalization_pipeline_id =
            pipeline.normalization_pipeline_id
        AND normalization.normalized_expression_id =
            normalized.normalized_expression_id
  )
ORDER BY
    normalized.normalized_text <-> 'grapfruit',
    normalized.normalized_expression_key
LIMIT 20;

\echo ROUND2B_QUERY_PLAN=trigram_callable_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'Hazelnuts', 'en', 'normalization.en_v1', 'C', 5, 0.35::REAL
);

\echo ROUND2B_QUERY_PLAN=typed_graph_expansion_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    neighbour.neighbour_concept_id,
    neighbour.neighbour_concept_key,
    neighbour.neighbour_concept_type_code,
    neighbour.concept_relation_id,
    neighbour.relation_type_code,
    neighbour.traversal_direction,
    policy_rule.rule_order
FROM kb.v_concept_neighbours AS neighbour
JOIN ml.retrieval_graph_policy AS policy
  ON policy.retrieval_graph_policy_key = 'graph_policy.round2b.v1'
 AND policy.is_frozen
JOIN ml.retrieval_graph_policy_rule AS policy_rule
  ON policy_rule.retrieval_graph_policy_id =
     policy.retrieval_graph_policy_id
 AND policy_rule.relation_type_code = neighbour.relation_type_code
 AND policy_rule.traversal_direction = neighbour.traversal_direction
 AND policy_rule.maximum_hops = 1
WHERE neighbour.concept_key = 'composite.earl_grey'
ORDER BY
    policy_rule.rule_order,
    neighbour.relation_key,
    neighbour.neighbour_concept_key;

\echo ROUND2B_QUERY_PLAN=typed_graph_callable_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'Earl Grey', 'en', 'normalization.en_v1', 'D', 10, 0.35::REAL
);

\echo ROUND2B_QUERY_PLAN=explicit_unresolved_callable_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'zzqv xylophonic meteor alloy',
    'en',
    'normalization.en_v1',
    'D',
    5,
    1::REAL
);

\echo ROUND2B_QUERY_PLAN=unresolved_corpus_frequency_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    unresolved.normalized_expression_key,
    unresolved.normalized_text,
    unresolved.occurrence_count,
    unresolved.document_count
FROM corpus.v_unresolved_normalized_expressions AS unresolved
WHERE unresolved.normalization_derivation_run_id = (
    SELECT derivation.normalization_derivation_run_id
    FROM corpus.normalization_derivation_run AS derivation
    WHERE derivation.normalization_derivation_run_key =
          'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
)
ORDER BY
    unresolved.occurrence_count DESC,
    unresolved.normalized_expression_key
LIMIT 25;

\echo ROUND2B_QUERY_PLAN=expression_frequency_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    frequency.normalized_expression_key,
    frequency.normalized_text,
    frequency.expression_frequency,
    frequency.document_frequency,
    frequency.publisher_prevalence_count,
    frequency.unresolved_occurrence_count
FROM corpus.v_normalized_expression_frequency AS frequency
WHERE frequency.corpus_statistic_run_key =
      'statistic_run.firstbloom_a6cb002_pilot_v1.v1'
ORDER BY
    frequency.expression_frequency DESC,
    frequency.normalized_expression_id
LIMIT 100;

\echo ROUND2B_QUERY_PLAN=npmi_neighbourhood_natural
EXPLAIN (ANALYZE, BUFFERS)
SELECT
    subject.normalized_text AS subject_text,
    object_expression.normalized_text AS object_text,
    pair.cooccurrence_document_count,
    pair.normalized_pmi,
    pair.subject_given_object_probability,
    pair.object_given_subject_probability,
    pair.value_semantics
FROM corpus.corpus_statistic_run AS statistic_run
JOIN corpus.normalized_expression_pair_measurement AS pair
  ON pair.corpus_statistic_run_id =
     statistic_run.corpus_statistic_run_id
JOIN corpus.normalized_expression AS subject
  ON subject.normalized_expression_id =
     pair.subject_normalized_expression_id
JOIN corpus.normalized_expression AS object_expression
  ON object_expression.normalized_expression_id =
     pair.object_normalized_expression_id
WHERE statistic_run.corpus_statistic_run_key =
      'statistic_run.firstbloom_a6cb002_pilot_v1.v1'
  AND (
        subject.normalized_text = 'bright'
        OR object_expression.normalized_text = 'bright'
      )
ORDER BY
    pair.normalized_pmi DESC,
    pair.normalized_expression_pair_measurement_id
LIMIT 25;

-- Two transaction-local copies keep the operator classes independently
-- observable. Both contain only governed canonical-dictionary expressions;
-- the full pilot remains available above for natural planner decisions.
CREATE TEMPORARY TABLE round2b_trgm_gist_benchmark
ON COMMIT DROP
AS
SELECT DISTINCT
    normalized.normalized_expression_id,
    normalized.normalized_expression_key,
    normalized.normalized_text
FROM corpus.normalized_expression AS normalized
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id =
     normalized.normalization_pipeline_id
JOIN corpus.lexical_expression_normalization AS normalization
  ON normalization.normalization_pipeline_id =
     pipeline.normalization_pipeline_id
 AND normalization.normalized_expression_id =
     normalized.normalized_expression_id
JOIN kb.lexical_expression AS expression
  ON expression.expression_id = normalization.expression_id
 AND expression.lifecycle_status_code = 'active'
JOIN kb.lexicalization AS lexicalization
  ON lexicalization.expression_id = expression.expression_id
 AND lexicalization.lifecycle_status_code = 'active'
 AND lexicalization.valid_from <= CURRENT_TIMESTAMP
 AND (
        lexicalization.valid_until IS NULL
        OR lexicalization.valid_until > CURRENT_TIMESTAMP
     )
JOIN ref.mapping_type AS mapping_type
  ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
 AND (mapping_type.is_preferred OR mapping_type.is_approved_variant)
JOIN kb.concept AS concept
  ON concept.concept_id = lexicalization.concept_id
 AND concept.lifecycle_status_code = 'active'
WHERE pipeline.normalization_pipeline_key = 'normalization.en_v1';

CREATE TEMPORARY TABLE round2b_trgm_gin_benchmark
ON COMMIT DROP
AS
SELECT *
FROM round2b_trgm_gist_benchmark;

CREATE INDEX round2b_temp_trgm_gist_idx
    ON round2b_trgm_gist_benchmark
    USING GIST (normalized_text gist_trgm_ops (siglen = 64));

CREATE INDEX round2b_temp_trgm_gin_idx
    ON round2b_trgm_gin_benchmark
    USING GIN (normalized_text gin_trgm_ops);

ANALYZE round2b_trgm_gist_benchmark;
ANALYZE round2b_trgm_gin_benchmark;

\echo ROUND2B_QUERY_PLAN_DIAGNOSTIC_ONLY=forced_gist_knn_not_superiority_claim
SET LOCAL enable_seqscan = off;
EXPLAIN (ANALYZE, BUFFERS, SETTINGS)
SELECT
    normalized_expression_key,
    normalized_text,
    similarity(normalized_text, 'grapfruit') AS similarity
FROM round2b_trgm_gist_benchmark
ORDER BY normalized_text <-> 'grapfruit'
LIMIT 10;

\echo ROUND2B_QUERY_PLAN_DIAGNOSTIC_ONLY=forced_gin_threshold_not_superiority_claim
SET LOCAL pg_trgm.similarity_threshold = 0.30;
EXPLAIN (ANALYZE, BUFFERS, SETTINGS)
SELECT
    normalized_expression_key,
    normalized_text,
    similarity(normalized_text, 'grapfruit') AS similarity
FROM round2b_trgm_gin_benchmark
WHERE normalized_text % 'grapfruit'
ORDER BY
    similarity(normalized_text, 'grapfruit') DESC,
    normalized_expression_key
LIMIT 10;

SET LOCAL enable_seqscan = on;

\echo ROUND2B_QUERY_PLAN_DIAGNOSTIC_ONLY=candidate_count_comparison
SELECT
    (
        SELECT count(*)
        FROM round2b_trgm_gist_benchmark
        WHERE similarity(normalized_text, 'grapfruit') >= 0.30::REAL
    ) AS gist_table_threshold_candidate_count,
    (
        SELECT count(*)
        FROM round2b_trgm_gin_benchmark
        WHERE normalized_text % 'grapfruit'
    ) AS gin_table_threshold_candidate_count;

\echo ROUND2B_QUERY_PLAN_SEED_ASSERTIONS=true

\else

\echo ROUND2B_QUERY_PLAN_SEED_ASSERTIONS_SKIPPED=true

\endif

ROLLBACK;

\echo ROUND2B_QUERY_PLAN_PASS=true
