\set ON_ERROR_STOP on
\pset pager off

-- Round 2B semantic and governance invariants. Industry records remain
-- language observations and empirical retrieval evidence; they never become
-- canonical sensory concepts or relations through this pipeline.

BEGIN TRANSACTION READ ONLY;

\echo ROUND2B_CANONICAL_BOUNDARY
SELECT
    (SELECT count(*) FROM kb.concept) AS canonical_concept_count,
    (
        SELECT count(*)
        FROM kb.concept
        WHERE concept_type_code = 'sensory_attribute'
          AND lifecycle_status_code = 'active'
    ) AS active_sensory_attribute_count,
    (SELECT count(*) FROM kb.concept_relation) AS stored_concept_relation_count,
    (
        SELECT count(*)
        FROM kb.concept_relation
        WHERE lifecycle_status_code = 'active'
          AND valid_from <= CURRENT_TIMESTAMP
          AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
    ) AS current_canonical_relation_count;

\echo ROUND2B_CORPUS_INVENTORY
SELECT
    snapshot.corpus_snapshot_key,
    snapshot.corpus_version,
    snapshot.frozen_at IS NOT NULL AS is_frozen,
    snapshot.expected_document_count,
    count(DISTINCT document.captured_document_id)::BIGINT
        AS stored_document_count,
    snapshot.expected_observation_count,
    count(DISTINCT observation.raw_observation_id)::BIGINT
        AS stored_observation_count,
    snapshot.expected_normalized_expression_count
FROM corpus.corpus_snapshot AS snapshot
LEFT JOIN corpus.captured_document AS document
  ON document.corpus_id = snapshot.corpus_id
LEFT JOIN corpus.raw_observation AS observation
  ON observation.captured_document_id = document.captured_document_id
GROUP BY
    snapshot.corpus_snapshot_id,
    snapshot.corpus_snapshot_key,
    snapshot.corpus_version,
    snapshot.frozen_at,
    snapshot.expected_document_count,
    snapshot.expected_observation_count,
    snapshot.expected_normalized_expression_count
ORDER BY snapshot.corpus_snapshot_key;

\echo ROUND2B_RIGHTS_DECISIONS
SELECT
    policy.corpus_source_decision_code,
    count(*)::BIGINT AS review_count,
    count(*) FILTER (WHERE policy.automated_acquisition_allowed)::BIGINT
        AS automation_allowed_count,
    count(*) FILTER (WHERE policy.raw_retention_allowed)::BIGINT
        AS raw_retention_allowed_count,
    count(*) FILTER (WHERE policy.derived_terms_allowed)::BIGINT
        AS derived_terms_allowed_count
FROM corpus.source_policy_review AS policy
GROUP BY policy.corpus_source_decision_code
ORDER BY policy.corpus_source_decision_code;

\echo ROUND2B_NORMALIZATION_INVENTORY
SELECT *
FROM corpus.v_round2b_normalization_inventory
ORDER BY normalization_derivation_run_key;

\echo ROUND2B_AUDIT_INVENTORY
SELECT
    audit_set.retrieval_audit_set_key,
    audit_case.audit_split_code,
    count(DISTINCT audit_case.retrieval_audit_case_id)::BIGINT AS case_count,
    count(DISTINCT review.reviewer_id) FILTER (
        WHERE review.audit_review_role_code = 'independent'
    )::BIGINT AS independent_reviewer_count,
    count(DISTINCT review.retrieval_case_review_id) FILTER (
        WHERE review.audit_review_role_code = 'adjudicated'
    )::BIGINT AS adjudicated_review_count
FROM audit.retrieval_audit_set AS audit_set
LEFT JOIN audit.retrieval_audit_case AS audit_case
  ON audit_case.retrieval_audit_set_id = audit_set.retrieval_audit_set_id
LEFT JOIN audit.retrieval_case_review AS review
  ON review.retrieval_audit_case_id = audit_case.retrieval_audit_case_id
GROUP BY
    audit_set.retrieval_audit_set_id,
    audit_set.retrieval_audit_set_key,
    audit_case.audit_split_code
ORDER BY audit_set.retrieval_audit_set_key, audit_case.audit_split_code;

DO $round2b_semantic$
DECLARE
    pilot_snapshot_id BIGINT;
BEGIN
    -- The Round 2A ontology is an immutable scientific boundary for this
    -- corpus/retrieval round. Empirical rows may reference it but not enlarge
    -- or rewrite it.
    IF (SELECT count(*) FROM kb.concept) <> 130
       OR (
            SELECT count(*)
            FROM kb.concept
            WHERE concept_type_code = 'sensory_attribute'
              AND lifecycle_status_code = 'active'
       ) <> 92
       OR (SELECT count(*) FROM kb.concept_relation) <> 110
       OR (
            SELECT count(*)
            FROM kb.concept_relation
            WHERE lifecycle_status_code = 'active'
              AND valid_from <= CURRENT_TIMESTAMP
              AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)
       ) <> 100 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_canonical_inventory_boundary_ck',
            MESSAGE = 'Round 2B corpus or ML work changed the frozen Round 2A canonical concept/relation inventory';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM kb.concept
        WHERE concept_key LIKE 'corpus.%'
           OR concept_key LIKE 'ml.%'
    ) OR EXISTS (
        SELECT 1
        FROM kb.concept_relation
        WHERE relation_key LIKE 'corpus.%'
           OR relation_key LIKE 'ml.%'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_no_empirical_canonical_promotion_ck',
            MESSAGE = 'Corpus and ML namespaces must not auto-promote rows into the canonical ontology';
    END IF;

    -- Every policy remains below both its controlled decision ceiling and the
    -- rights attached to the exact source version.
    IF EXISTS (
        SELECT 1
        FROM corpus.source_policy_review AS policy
        JOIN ref.corpus_source_decision AS decision
          ON decision.corpus_source_decision_code =
             policy.corpus_source_decision_code
        JOIN evidence.source_version AS source_version
          ON source_version.source_version_id = policy.source_version_id
        JOIN evidence.license_policy AS license_policy
          ON license_policy.license_policy_id = policy.license_policy_id
        JOIN ref.access_class AS access_class
          ON access_class.access_class_code = license_policy.access_class_code
        WHERE source_version.license_policy_id <> policy.license_policy_id
           OR policy.document_metadata_allowed
              AND NOT decision.permits_document_metadata
           OR policy.raw_retention_allowed
              AND (
                    NOT decision.permits_raw_retention
                    OR NOT access_class.permits_raw_text
                 )
           OR policy.derived_terms_allowed
              AND (
                    NOT decision.permits_derived_terms
                    OR NOT license_policy.machine_use_allowed
                 )
           OR policy.derived_terms_redistribution_allowed
              AND (
                    NOT decision.permits_derived_redistribution
                    OR NOT policy.derived_terms_allowed
                    OR NOT license_policy.redistributable
                    OR NOT license_policy.derivative_work_allowed
                 )
           OR policy.raw_redistribution_allowed
              AND (
                    NOT decision.permits_raw_redistribution
                    OR NOT license_policy.production_export_allowed
                 )
           OR decision.is_blocking
              AND (
                    policy.document_metadata_allowed
                    OR policy.raw_retention_allowed
                    OR policy.derived_terms_allowed
                    OR policy.derived_terms_redistribution_allowed
                    OR policy.raw_redistribution_allowed
                    OR policy.automated_acquisition_allowed
                 )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_source_policy_ceiling_ck',
            MESSAGE = 'A source policy exceeds its decision, source-version licence, or access-class ceiling';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.source_policy_review AS policy
        JOIN ref.corpus_source_decision AS decision
          ON decision.corpus_source_decision_code =
             policy.corpus_source_decision_code
        JOIN ref.robots_status AS robots
          ON robots.robots_status_code = policy.robots_status_code
        JOIN ref.terms_status AS terms
          ON terms.terms_status_code = policy.terms_status_code
        JOIN ref.corpus_access_method AS access_method
          ON access_method.corpus_access_method_code =
             policy.corpus_access_method_code
        JOIN evidence.license_policy AS license_policy
          ON license_policy.license_policy_id = policy.license_policy_id
        WHERE policy.automated_acquisition_allowed
          AND (
                NOT access_method.is_automated
                OR NOT robots.automation_not_prohibited
                OR NOT terms.machine_access_not_prohibited
                OR NOT license_policy.machine_use_allowed
                OR decision.requires_manual_access
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_automation_rights_ck',
            MESSAGE = 'Automated acquisition lacks a defensible method, robots, terms, or machine-use basis';
    END IF;

    -- Snapshot-backed documents require a stable release identity and complete
    -- non-content receipts. Blocked/unknown and metadata-denying sources never
    -- enter a corpus snapshot.
    IF EXISTS (
        SELECT 1
        FROM corpus.captured_document AS document
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.corpus_id = document.corpus_id
        LEFT JOIN corpus.source_policy_review AS policy
          ON policy.source_policy_review_id = document.source_policy_review_id
        LEFT JOIN ref.corpus_source_decision AS decision
          ON decision.corpus_source_decision_code =
             policy.corpus_source_decision_code
        WHERE document.industry_product_id IS NULL
           OR document.source_policy_review_id IS NULL
           OR document.acquisition_batch_id IS NULL
           OR document.content_sha256 IS NULL
           OR document.raw_text_sha256 IS NULL
           OR document.external_document_key IS NULL
              AND document.canonical_url IS NULL
           OR policy.source_version_id IS DISTINCT FROM document.source_version_id
           OR NOT COALESCE(policy.document_metadata_allowed, FALSE)
           OR COALESCE(decision.is_blocking, TRUE)
           OR document.raw_text IS NOT NULL
              AND NOT COALESCE(policy.raw_retention_allowed, FALSE)
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_snapshot_document_rights_ck',
            MESSAGE = 'A snapshot document lacks its stable receipt or exceeds the reviewed acquisition policy';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.raw_observation AS observation
        JOIN corpus.captured_document AS document
          ON document.captured_document_id = observation.captured_document_id
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.corpus_id = document.corpus_id
        JOIN corpus.source_policy_review AS policy
          ON policy.source_policy_review_id = document.source_policy_review_id
        WHERE observation.observation_sha256 IS NULL
           OR observation.character_count IS NULL
           OR observation.observation_retention_code IS NULL
           OR observation.observation_retention_code = 'hash_only'
              AND observation.observation_text IS NOT NULL
           OR observation.observation_retention_code = 'full_text'
              AND NOT policy.raw_retention_allowed
           OR observation.observation_retention_code = 'derived_phrase'
              AND NOT policy.derived_terms_allowed
           OR observation.observation_text IS NOT NULL
              AND observation.character_count <>
                  char_length(observation.observation_text)
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_observation_retention_ck',
            MESSAGE = 'A snapshot observation lacks its hash/length disposition or leaks text beyond policy';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.observation_expression AS occurrence
        JOIN corpus.raw_observation AS observation
          ON observation.raw_observation_id = occurrence.raw_observation_id
        JOIN corpus.captured_document AS document
          ON document.captured_document_id = observation.captured_document_id
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.corpus_id = document.corpus_id
        JOIN corpus.source_policy_review AS policy
          ON policy.source_policy_review_id = document.source_policy_review_id
        WHERE NOT policy.derived_terms_allowed
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_expression_rights_ck',
            MESSAGE = 'A retained expression crosses a source policy that forbids derived terms';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.v_distributable_observations AS distributable
        JOIN corpus.raw_observation AS observation
          ON observation.raw_observation_id = distributable.raw_observation_id
        JOIN corpus.captured_document AS document
          ON document.captured_document_id = observation.captured_document_id
        JOIN corpus.source_policy_review AS policy
          ON policy.source_policy_review_id = document.source_policy_review_id
        WHERE distributable.observation_text IS NOT NULL
          AND (
                observation.observation_retention_code = 'full_text'
                AND NOT policy.raw_redistribution_allowed
                OR observation.observation_retention_code = 'derived_phrase'
                   AND NOT policy.derived_terms_redistribution_allowed
                OR observation.observation_retention_code = 'hash_only'
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_distributable_text_leak_ck',
            MESSAGE = 'A production-facing view exposes observation text beyond the Round 2B source policy';
    END IF;

    -- Stable external release identity is unique while multiple historical
    -- releases may legitimately retain the same industry product identity.
    IF EXISTS (
        SELECT corpus_id, source_version_id, external_document_key
        FROM corpus.captured_document
        WHERE external_document_key IS NOT NULL
        GROUP BY corpus_id, source_version_id, external_document_key
        HAVING count(*) > 1
    ) OR EXISTS (
        SELECT corpus_id, canonical_url
        FROM corpus.captured_document
        WHERE canonical_url IS NOT NULL
        GROUP BY corpus_id, canonical_url
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_release_identity_unique_ck',
            MESSAGE = 'Stable external release identifiers or canonical URLs are duplicated inside one snapshot';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.document_duplicate_review AS review
        JOIN corpus.captured_document AS earlier
          ON earlier.captured_document_id = review.earlier_document_id
        JOIN corpus.captured_document AS later
          ON later.captured_document_id = review.later_document_id
        WHERE earlier.corpus_id <> later.corpus_id
           OR review.earlier_document_id >= review.later_document_id
    ) OR EXISTS (
        SELECT 1
        FROM corpus.corpus_snapshot AS snapshot
        JOIN corpus.v_document_duplicate_candidates AS candidate
          ON EXISTS (
                SELECT 1
                FROM corpus.captured_document AS document
                WHERE document.captured_document_id =
                      candidate.earlier_document_id
                  AND document.corpus_id = snapshot.corpus_id
             )
        WHERE snapshot.frozen_at IS NOT NULL
          AND NOT EXISTS (
                SELECT 1
                FROM corpus.document_duplicate_review AS review
                WHERE review.earlier_document_id =
                      candidate.earlier_document_id
                  AND review.later_document_id =
                      candidate.later_document_id
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_duplicate_review_complete_ck',
            MESSAGE = 'Duplicate review ordering, snapshot scope, or frozen-snapshot coverage is incomplete';
    END IF;

    -- Frozen snapshot identities close over source membership, acquisition
    -- batches, documents, observations, and their frozen pipeline.
    IF EXISTS (
        SELECT 1
        FROM corpus.corpus_snapshot AS snapshot
        LEFT JOIN corpus.normalization_pipeline AS pipeline
          ON pipeline.normalization_pipeline_id =
             snapshot.normalization_pipeline_id
        WHERE snapshot.frozen_at IS NOT NULL
          AND (
                pipeline.frozen_at IS NULL
                OR snapshot.expected_document_count <>
                   (
                       SELECT count(*)
                       FROM corpus.captured_document AS document
                       WHERE document.corpus_id = snapshot.corpus_id
                   )
                OR snapshot.expected_observation_count <>
                   (
                       SELECT count(*)
                       FROM corpus.raw_observation AS observation
                       JOIN corpus.captured_document AS document
                         ON document.captured_document_id =
                            observation.captured_document_id
                       WHERE document.corpus_id = snapshot.corpus_id
                   )
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_frozen_snapshot_inventory_ck',
            MESSAGE = 'A frozen corpus snapshot differs from its declared document/observation inventory or pipeline';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.acquisition_batch AS batch
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.corpus_snapshot_id = batch.corpus_snapshot_id
        WHERE snapshot.frozen_at IS NOT NULL
          AND batch.expected_document_count <>
              (
                  SELECT count(*)
                  FROM corpus.captured_document AS document
                  WHERE document.acquisition_batch_id =
                        batch.acquisition_batch_id
              )
    ) OR EXISTS (
        SELECT 1
        FROM corpus.corpus_snapshot_source AS member
        JOIN corpus.industry_publisher AS publisher
          ON publisher.industry_publisher_id = member.industry_publisher_id
        WHERE publisher.source_policy_review_id IS NOT NULL
          AND publisher.source_policy_review_id <>
              member.source_policy_review_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_snapshot_source_batch_ck',
            MESSAGE = 'A frozen batch count or inherited publisher-policy membership is inconsistent';
    END IF;

    -- Normalization is pipeline-specific, deterministic, and non-destructive.
    IF EXISTS (
        SELECT 1
        FROM corpus.normalized_expression AS normalized
        JOIN corpus.normalization_pipeline AS pipeline
          ON pipeline.normalization_pipeline_id =
             normalized.normalization_pipeline_id
        WHERE pipeline.frozen_at IS NULL
           OR corpus.normalize_expression_v1(
                  normalized.normalized_text,
                  pipeline.normalization_pipeline_key
              ) <> normalized.normalized_text
    ) OR EXISTS (
        SELECT 1
        FROM corpus.lexical_expression_normalization AS mapping
        JOIN kb.lexical_expression AS expression
          ON expression.expression_id = mapping.expression_id
        JOIN corpus.normalized_expression AS normalized
          ON normalized.normalized_expression_id =
             mapping.normalized_expression_id
        JOIN corpus.normalization_pipeline AS pipeline
          ON pipeline.normalization_pipeline_id =
             mapping.normalization_pipeline_id
        WHERE normalized.normalization_pipeline_id <>
              mapping.normalization_pipeline_id
           OR expression.language_tag_code <> pipeline.language_tag_code
           OR normalized.normalized_text <>
              corpus.normalize_expression_v1(
                  expression.expression_text,
                  pipeline.normalization_pipeline_key
              )
           OR mapping.surface_sha256 <>
              encode(
                  sha256(convert_to(expression.expression_text, 'UTF8')),
                  'hex'
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_normalization_determinism_ck',
            MESSAGE = 'A normalized identity or lexical projection is not reproducible under its frozen pipeline';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.v_round2b_normalization_inventory AS inventory
        WHERE inventory.frozen_at IS NOT NULL
          AND inventory.output_occurrence_count <>
              inventory.stored_occurrence_count
    ) OR EXISTS (
        SELECT 1
        FROM corpus.normalized_expression_occurrence AS occurrence
        JOIN corpus.normalization_derivation_run AS derivation
          ON derivation.normalization_derivation_run_id =
             occurrence.normalization_derivation_run_id
        JOIN corpus.normalized_expression AS normalized
          ON normalized.normalized_expression_id =
             occurrence.normalized_expression_id
        WHERE occurrence.normalization_pipeline_id <>
              derivation.normalization_pipeline_id
           OR occurrence.normalization_pipeline_id <>
              normalized.normalization_pipeline_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_normalization_inventory_ck',
            MESSAGE = 'A frozen normalization run count or pipeline-specific occurrence identity is inconsistent';
    END IF;

    -- Corpus statistics are versioned normalized-language measurements, never
    -- perceptual relations. Pair endpoints share a pipeline and remain within
    -- their explicit NPMI/probability bounds.
    IF EXISTS (
        SELECT 1
        FROM corpus.normalized_expression_frequency AS frequency
        JOIN corpus.corpus_statistic_run AS statistic_run
          ON statistic_run.corpus_statistic_run_id =
             frequency.corpus_statistic_run_id
        JOIN corpus.normalization_derivation_run AS derivation
          ON derivation.normalization_derivation_run_id =
             statistic_run.normalization_derivation_run_id
        JOIN corpus.normalized_expression AS normalized
          ON normalized.normalized_expression_id =
             frequency.normalized_expression_id
        WHERE normalized.normalization_pipeline_id <>
              derivation.normalization_pipeline_id
    ) OR EXISTS (
        SELECT 1
        FROM corpus.normalized_expression_pair_measurement AS pair
        JOIN corpus.corpus_statistic_run AS statistic_run
          ON statistic_run.corpus_statistic_run_id =
             pair.corpus_statistic_run_id
        JOIN corpus.normalization_derivation_run AS derivation
          ON derivation.normalization_derivation_run_id =
             statistic_run.normalization_derivation_run_id
        JOIN corpus.normalized_expression AS subject
          ON subject.normalized_expression_id =
             pair.subject_normalized_expression_id
        JOIN corpus.normalized_expression AS object_expression
          ON object_expression.normalized_expression_id =
             pair.object_normalized_expression_id
        WHERE subject.normalization_pipeline_id <>
              derivation.normalization_pipeline_id
           OR object_expression.normalization_pipeline_id <>
              derivation.normalization_pipeline_id
           OR pair.subject_normalized_expression_id >=
              pair.object_normalized_expression_id
           OR pair.normalized_pmi NOT BETWEEN -1 AND 1
           OR pair.subject_given_object_probability NOT BETWEEN 0 AND 1
           OR pair.object_given_subject_probability NOT BETWEEN 0 AND 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_normalized_statistics_scope_ck',
            MESSAGE = 'A normalized frequency or pair statistic escapes its derivation pipeline or declared value bounds';
    END IF;

    -- The sole production graph policy is an exact, frozen, one-hop allowlist.
    IF NOT EXISTS (
        SELECT 1
        FROM ml.retrieval_graph_policy
        WHERE retrieval_graph_policy_key = 'graph_policy.round2b.v1'
          AND is_frozen
          AND configuration @> '{"maximum_hops":1,"uses_source_schemes":false,"uses_transitive_closure":false,"weighted_score":false}'::JSONB
    ) OR EXISTS (
        SELECT
            rule.relation_type_code,
            rule.traversal_direction,
            rule.maximum_hops
        FROM ml.retrieval_graph_policy_rule AS rule
        JOIN ml.retrieval_graph_policy AS policy
          ON policy.retrieval_graph_policy_id =
             rule.retrieval_graph_policy_id
        WHERE policy.retrieval_graph_policy_key =
              'graph_policy.round2b.v1'
        EXCEPT
        SELECT *
        FROM (
            VALUES
                ('composite_has_component'::TEXT, 'OUTGOING'::TEXT, 1::SMALLINT),
                ('consumer_reference_for', 'OUTGOING', 1::SMALLINT),
                ('broader_than', 'INCOMING', 1::SMALLINT),
                ('broader_than', 'OUTGOING', 1::SMALLINT),
                ('sensory_neighbour', 'SYMMETRIC', 1::SMALLINT)
        ) AS expected(relation_type_code, traversal_direction, maximum_hops)
    ) OR EXISTS (
        SELECT *
        FROM (
            VALUES
                ('composite_has_component'::TEXT, 'OUTGOING'::TEXT, 1::SMALLINT),
                ('consumer_reference_for', 'OUTGOING', 1::SMALLINT),
                ('broader_than', 'INCOMING', 1::SMALLINT),
                ('broader_than', 'OUTGOING', 1::SMALLINT),
                ('sensory_neighbour', 'SYMMETRIC', 1::SMALLINT)
        ) AS expected(relation_type_code, traversal_direction, maximum_hops)
        EXCEPT
        SELECT
            rule.relation_type_code,
            rule.traversal_direction,
            rule.maximum_hops
        FROM ml.retrieval_graph_policy_rule AS rule
        JOIN ml.retrieval_graph_policy AS policy
          ON policy.retrieval_graph_policy_id =
             rule.retrieval_graph_policy_id
        WHERE policy.retrieval_graph_policy_key =
              'graph_policy.round2b.v1'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_graph_allowlist_ck',
            MESSAGE = 'The Round 2B graph policy is not the exact frozen canonical one-hop allowlist';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM ml.retrieval_graph_policy_rule
        WHERE maximum_hops <> 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_graph_one_hop_ck',
            MESSAGE = 'A deterministic graph policy permits more than one stored hop';
    END IF;

    -- U is a case-level abstention expectation. Candidate judgments use only
    -- grades 0--3, and every review has the required positive/non-positive
    -- shape. Frozen held-out inventories have independent review redundancy.
    IF EXISTS (
        SELECT 1
        FROM audit.retrieval_relevance_judgment
        WHERE relevance_grade_code NOT IN ('0', '1', '2', '3')
    ) OR EXISTS (
        SELECT 1
        FROM audit.retrieval_case_review AS review
        LEFT JOIN audit.retrieval_relevance_judgment AS judgment
          ON judgment.retrieval_case_review_id =
             review.retrieval_case_review_id
        LEFT JOIN ref.relevance_grade AS grade
          ON grade.relevance_grade_code = judgment.relevance_grade_code
        GROUP BY
            review.retrieval_case_review_id,
            review.expects_unresolved
        HAVING review.expects_unresolved
               AND count(*) FILTER (WHERE grade.ordinal_value >= 2) <> 0
            OR NOT review.expects_unresolved
               AND count(*) FILTER (WHERE grade.ordinal_value >= 2) < 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_audit_grade_semantics_ck',
            MESSAGE = 'Audit relevance grades conflate U with a candidate or violate the review abstention decision';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.retrieval_audit_set AS audit_set
        JOIN audit.retrieval_audit_case AS audit_case
          ON audit_case.retrieval_audit_set_id =
             audit_set.retrieval_audit_set_id
        WHERE audit_set.frozen_at IS NOT NULL
          AND (
                NOT EXISTS (
                    SELECT 1
                    FROM audit.retrieval_audit_case_stratum AS stratum
                    WHERE stratum.retrieval_audit_case_id =
                          audit_case.retrieval_audit_case_id
                )
                OR NOT EXISTS (
                    SELECT 1
                    FROM audit.retrieval_case_review AS review
                    WHERE review.retrieval_audit_case_id =
                          audit_case.retrieval_audit_case_id
                      AND review.audit_review_role_code = 'adjudicated'
                )
                OR audit_case.audit_split_code = 'held_out'
                   AND (
                       SELECT count(DISTINCT review.reviewer_id)
                       FROM audit.retrieval_case_review AS review
                       WHERE review.retrieval_audit_case_id =
                             audit_case.retrieval_audit_case_id
                         AND review.audit_review_role_code = 'independent'
                   ) < 2
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_frozen_audit_inventory_ck',
            MESSAGE = 'A frozen audit case lacks strata, adjudication, or held-out independent review coverage';
    END IF;

    -- The checked-in pilot is optional while 015 is being assembled. Once its
    -- stable key exists, its declared snapshot receipts become mandatory.
    SELECT snapshot.corpus_snapshot_id
    INTO pilot_snapshot_id
    FROM corpus.corpus_snapshot AS snapshot
    WHERE snapshot.corpus_snapshot_key =
          'corpus_snapshot.firstbloom_a6cb002_pilot_v1';

    IF FOUND THEN
        IF EXISTS (
            SELECT 1
            FROM corpus.corpus_snapshot AS snapshot
            JOIN corpus.normalization_pipeline AS pipeline
              ON pipeline.normalization_pipeline_id =
                 snapshot.normalization_pipeline_id
            WHERE snapshot.corpus_snapshot_id = pilot_snapshot_id
              AND (
                    snapshot.frozen_at IS NULL
                    OR pipeline.normalization_pipeline_key <>
                       'normalization.en_v1'
                    OR pipeline.frozen_at IS NULL
                    OR snapshot.raw_public_reproducibility_complete
                    OR snapshot.expected_document_count = 0
                    OR snapshot.expected_observation_count = 0
                    OR snapshot.expected_normalized_expression_count = 0
                  )
        ) OR EXISTS (
            SELECT 1
            FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE snapshot.corpus_snapshot_id = pilot_snapshot_id
              AND document.raw_text IS NOT NULL
        ) OR NOT EXISTS (
            SELECT 1
            FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            GROUP BY document.industry_product_id
            HAVING count(*) > 1
        ) OR NOT EXISTS (
            SELECT 1
            FROM corpus.normalization_derivation_run AS derivation
            WHERE derivation.corpus_snapshot_id = pilot_snapshot_id
              AND derivation.frozen_at IS NOT NULL
        ) OR NOT EXISTS (
            SELECT 1
            FROM corpus.corpus_statistic_run AS statistic_run
            JOIN corpus.normalization_derivation_run AS derivation
              ON derivation.normalization_derivation_run_id =
                 statistic_run.normalization_derivation_run_id
            WHERE derivation.corpus_snapshot_id = pilot_snapshot_id
              AND statistic_run.frozen_at IS NOT NULL
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round2b_firstbloom_pilot_receipt_ck',
                MESSAGE = 'The Firstbloom pilot exists but is not a frozen, raw-redacted, versioned normalization/statistics snapshot';
        END IF;

        RAISE NOTICE
            'ROUND2B_PILOT_SEED_PRESENT=true SNAPSHOT_ID=%',
            pilot_snapshot_id;
    ELSE
        RAISE NOTICE
            'ROUND2B_PILOT_SEED_PRESENT=false (015 seed-dependent checks skipped)';
    END IF;
END;
$round2b_semantic$;

ROLLBACK;

\echo ROUND2B_SEMANTIC_PASS=true
