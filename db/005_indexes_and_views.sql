\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Access paths and read models are kept in one directly executable migration.
-- All indexes are created in this transaction (never CONCURRENTLY), so a
-- failed definition leaves no partially applied migration.

BEGIN;

-- Stable-key and exact-expression access paths already exist as UNIQUE
-- indexes declared by migrations 001--003. Do not duplicate them here.

-- GiST is deliberate: lexical fallback is a K-nearest-neighbour query ordered
-- by trigram distance (<->) with LIMIT. GIN is effective for trigram predicate
-- filtering, but it cannot provide that KNN ordering. The lifecycle predicate
-- is immutable and local to the indexed row; query-time validity is evaluated
-- by the retrieval function rather than embedded in a partial-index predicate.
CREATE INDEX lexical_expression_normalized_trgm_gist_idx
    ON kb.lexical_expression
    USING GIST (normalized_text gist_trgm_ops)
    WHERE lifecycle_status_code = 'active';

COMMENT ON INDEX kb.lexical_expression_normalized_trgm_gist_idx IS
    'GiST (rather than GIN) supports ORDER BY normalized_text <-> query LIMIT k for lexical-only trigram retrieval; similarity is not sensory similarity.';

CREATE INDEX lexicalization_active_expression_idx
    ON kb.lexicalization (
        expression_id,
        mapping_type_code,
        valid_from,
        valid_until,
        concept_id
    )
    WHERE lifecycle_status_code = 'active';

CREATE INDEX lexicalization_active_concept_idx
    ON kb.lexicalization (
        concept_id,
        expression_id,
        valid_from,
        valid_until,
        mapping_type_code
    )
    WHERE lifecycle_status_code = 'active';

CREATE INDEX concept_active_type_idx
    ON kb.concept (concept_type_code, concept_id)
    WHERE lifecycle_status_code = 'active';

CREATE INDEX concept_relation_active_subject_type_idx
    ON kb.concept_relation (
        subject_concept_id,
        relation_type_code,
        valid_from,
        valid_until,
        object_concept_id
    )
    WHERE lifecycle_status_code = 'active';

CREATE INDEX concept_relation_active_object_type_idx
    ON kb.concept_relation (
        object_concept_id,
        relation_type_code,
        valid_from,
        valid_until,
        subject_concept_id
    )
    WHERE lifecycle_status_code = 'active';

CREATE INDEX concept_dimension_link_active_concept_idx
    ON kb.concept_dimension_link (concept_id, sensory_dimension_id)
    WHERE lifecycle_status_code = 'active';

-- Coverage can originate directly from a source version or indirectly through
-- a dataset. The XOR constraints make these two local partial indexes per
-- support table selective without requiring an illegal subquery predicate.
CREATE INDEX concept_support_source_version_idx
    ON evidence.concept_support (source_version_id, concept_id)
    WHERE source_version_id IS NOT NULL;

CREATE INDEX concept_support_dataset_idx
    ON evidence.concept_support (dataset_id, concept_id)
    WHERE dataset_id IS NOT NULL;

CREATE INDEX lexicalization_support_source_version_idx
    ON evidence.lexicalization_support (source_version_id, lexicalization_id)
    WHERE source_version_id IS NOT NULL;

CREATE INDEX lexicalization_support_dataset_idx
    ON evidence.lexicalization_support (dataset_id, lexicalization_id)
    WHERE dataset_id IS NOT NULL;

CREATE INDEX relation_support_source_version_idx
    ON evidence.relation_support (source_version_id, concept_relation_id)
    WHERE source_version_id IS NOT NULL;

CREATE INDEX relation_support_dataset_idx
    ON evidence.relation_support (dataset_id, concept_relation_id)
    WHERE dataset_id IS NOT NULL;

CREATE INDEX concept_dimension_link_support_source_version_idx
    ON evidence.concept_dimension_link_support (
        source_version_id,
        concept_dimension_link_id
    )
    WHERE source_version_id IS NOT NULL;

CREATE INDEX concept_dimension_link_support_dataset_idx
    ON evidence.concept_dimension_link_support (
        dataset_id,
        concept_dimension_link_id
    )
    WHERE dataset_id IS NOT NULL;

CREATE INDEX source_version_source_idx
    ON evidence.source_version (source_id, source_version_id);

CREATE INDEX source_version_license_policy_idx
    ON evidence.source_version (license_policy_id, source_version_id);

CREATE INDEX dataset_source_version_idx
    ON evidence.dataset (source_version_id, dataset_id);

CREATE INDEX empirical_pair_measurement_pair_lookup_idx
    ON evidence.empirical_pair_measurement (
        subject_concept_id,
        object_concept_id,
        signal_domain_code,
        dataset_id,
        statistical_method_id
    );

CREATE INDEX captured_document_source_version_idx
    ON corpus.captured_document (source_version_id, captured_document_id);

CREATE INDEX raw_observation_document_idx
    ON corpus.raw_observation (captured_document_id, raw_observation_id);

CREATE INDEX observation_expression_expression_idx
    ON corpus.observation_expression (expression_id, raw_observation_id);

CREATE INDEX observation_resolution_unresolved_idx
    ON corpus.observation_resolution (observation_expression_id)
    WHERE resolution_status_code = 'unresolved';

CREATE INDEX mapping_candidate_status_rank_idx
    ON ml.mapping_candidate (
        candidate_status_code,
        mapping_inference_id,
        rank,
        concept_id
    );

CREATE INDEX mapping_review_candidate_idx
    ON audit.mapping_review (mapping_candidate_id, review_id);

-- One row is retained for every active concept. Current outgoing relations are
-- attached when present; isolated and incoming-only concepts therefore remain
-- visible as concept rows with NULL relation columns. A relation can enter the
-- view only when the relation and both endpoints are active and the relation's
-- half-open validity interval contains the statement timestamp.
CREATE VIEW kb.v_current_canonical_ontology AS
WITH current_relations AS (
    SELECT
        cr.concept_relation_id,
        cr.relation_key,
        cr.relation_type_code,
        rt.is_directional,
        rt.is_symmetric,
        cr.lifecycle_status_code AS relation_lifecycle_status_code,
        cr.provenance_scope_code AS relation_provenance_scope_code,
        cr.valid_from AS relation_valid_from,
        cr.valid_until AS relation_valid_until,
        subject_concept.concept_id AS subject_concept_id,
        subject_concept.concept_key AS subject_concept_key,
        subject_concept.lifecycle_status_code AS subject_lifecycle_status_code,
        object_concept.concept_id AS object_concept_id,
        object_concept.concept_key AS object_concept_key,
        object_concept.lifecycle_status_code AS object_lifecycle_status_code
    FROM kb.concept_relation AS cr
    JOIN ref.relation_type AS rt
      ON rt.relation_type_code = cr.relation_type_code
    JOIN kb.concept AS subject_concept
      ON subject_concept.concept_id = cr.subject_concept_id
     AND subject_concept.lifecycle_status_code = 'active'
    JOIN kb.concept AS object_concept
      ON object_concept.concept_id = cr.object_concept_id
     AND object_concept.lifecycle_status_code = 'active'
    WHERE cr.lifecycle_status_code = 'active'
      AND cr.valid_from <= CURRENT_TIMESTAMP
      AND (cr.valid_until IS NULL OR cr.valid_until > CURRENT_TIMESTAMP)
)
SELECT
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code AS concept_lifecycle_status_code,
    concept.provenance_scope_code AS concept_provenance_scope_code,
    concept.description AS concept_description,
    concept.editorial_note AS concept_editorial_note,
    relation.concept_relation_id,
    relation.relation_key,
    relation.relation_type_code,
    relation.is_directional AS relation_is_directional,
    relation.is_symmetric AS relation_is_symmetric,
    relation.relation_lifecycle_status_code,
    relation.relation_provenance_scope_code,
    relation.relation_valid_from,
    relation.relation_valid_until,
    relation.subject_concept_id,
    relation.subject_concept_key,
    relation.subject_lifecycle_status_code,
    relation.object_concept_id,
    relation.object_concept_key,
    relation.object_lifecycle_status_code
FROM kb.concept AS concept
LEFT JOIN current_relations AS relation
  ON relation.subject_concept_id = concept.concept_id
WHERE concept.lifecycle_status_code = 'active';

COMMENT ON VIEW kb.v_current_canonical_ontology IS
    'Active canonical concepts plus current active relations whose subject and object concepts are also active; expired and deprecated graph assertions are excluded.';

-- LEFT JOIN semantics are intentional. Every active expression is represented,
-- and an expression without a current active mapping to an active concept gets
-- exactly one explicit UNRESOLVED row. Multiple current mappings remain as
-- separate RESOLVED rows so polysemy is not collapsed.
CREATE VIEW kb.v_lexical_resolution AS
WITH current_mappings AS (
    SELECT
        lexicalization.lexicalization_id,
        lexicalization.lexicalization_key,
        lexicalization.expression_id,
        lexicalization.mapping_type_code,
        lexicalization.provenance_scope_code,
        lexicalization.valid_from,
        lexicalization.valid_until,
        concept.concept_id,
        concept.concept_key,
        concept.concept_type_code,
        concept.lifecycle_status_code AS concept_lifecycle_status_code
    FROM kb.lexicalization AS lexicalization
    JOIN kb.concept AS concept
      ON concept.concept_id = lexicalization.concept_id
     AND concept.lifecycle_status_code = 'active'
    WHERE lexicalization.lifecycle_status_code = 'active'
      AND lexicalization.valid_from <= CURRENT_TIMESTAMP
      AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
          )
)
SELECT
    expression.expression_id,
    expression.expression_key,
    expression.language_tag_code,
    expression.expression_text,
    expression.normalized_text,
    CASE
        WHEN lexicalization.lexicalization_id IS NULL THEN 'UNRESOLVED'::TEXT
        ELSE 'RESOLVED'::TEXT
    END AS resolution_status,
    lexicalization.lexicalization_id,
    lexicalization.lexicalization_key,
    lexicalization.mapping_type_code,
    lexicalization.provenance_scope_code AS lexicalization_provenance_scope_code,
    lexicalization.valid_from AS lexicalization_valid_from,
    lexicalization.valid_until AS lexicalization_valid_until,
    lexicalization.concept_id,
    lexicalization.concept_key,
    lexicalization.concept_type_code,
    lexicalization.concept_lifecycle_status_code
FROM kb.lexical_expression AS expression
LEFT JOIN current_mappings AS lexicalization
  ON lexicalization.expression_id = expression.expression_id
WHERE expression.lifecycle_status_code = 'active';

COMMENT ON VIEW kb.v_lexical_resolution IS
    'All active expressions with current active canonical mappings or one explicit UNRESOLVED row; one expression may resolve to multiple concepts.';

-- Directional relations produce one OUTGOING and one INCOMING traversal row.
-- Symmetric relations produce both endpoint traversals labelled SYMMETRIC, so
-- callers never have to infer semantics from canonical storage order.
CREATE VIEW kb.v_concept_neighbours AS
WITH current_edges AS (
    SELECT
        cr.concept_relation_id,
        cr.relation_key,
        cr.relation_type_code,
        cr.valid_from,
        cr.valid_until,
        rt.is_directional,
        rt.is_symmetric,
        subject_concept.concept_id AS subject_concept_id,
        subject_concept.concept_key AS subject_concept_key,
        subject_concept.concept_type_code AS subject_concept_type_code,
        object_concept.concept_id AS object_concept_id,
        object_concept.concept_key AS object_concept_key,
        object_concept.concept_type_code AS object_concept_type_code
    FROM kb.concept_relation AS cr
    JOIN ref.relation_type AS rt
      ON rt.relation_type_code = cr.relation_type_code
    JOIN kb.concept AS subject_concept
      ON subject_concept.concept_id = cr.subject_concept_id
     AND subject_concept.lifecycle_status_code = 'active'
    JOIN kb.concept AS object_concept
      ON object_concept.concept_id = cr.object_concept_id
     AND object_concept.lifecycle_status_code = 'active'
    WHERE cr.lifecycle_status_code = 'active'
      AND cr.valid_from <= CURRENT_TIMESTAMP
      AND (cr.valid_until IS NULL OR cr.valid_until > CURRENT_TIMESTAMP)
)
SELECT
    edge.subject_concept_id AS concept_id,
    edge.subject_concept_key AS concept_key,
    edge.subject_concept_type_code AS concept_type_code,
    edge.object_concept_id AS neighbour_concept_id,
    edge.object_concept_key AS neighbour_concept_key,
    edge.object_concept_type_code AS neighbour_concept_type_code,
    edge.concept_relation_id,
    edge.relation_key,
    edge.relation_type_code,
    CASE
        WHEN edge.is_symmetric THEN 'SYMMETRIC'::TEXT
        ELSE 'OUTGOING'::TEXT
    END AS traversal_direction,
    edge.is_directional,
    edge.is_symmetric,
    edge.valid_from AS relation_valid_from,
    edge.valid_until AS relation_valid_until
FROM current_edges AS edge
UNION
SELECT
    edge.object_concept_id AS concept_id,
    edge.object_concept_key AS concept_key,
    edge.object_concept_type_code AS concept_type_code,
    edge.subject_concept_id AS neighbour_concept_id,
    edge.subject_concept_key AS neighbour_concept_key,
    edge.subject_concept_type_code AS neighbour_concept_type_code,
    edge.concept_relation_id,
    edge.relation_key,
    edge.relation_type_code,
    CASE
        WHEN edge.is_symmetric THEN 'SYMMETRIC'::TEXT
        ELSE 'INCOMING'::TEXT
    END AS traversal_direction,
    edge.is_directional,
    edge.is_symmetric,
    edge.valid_from AS relation_valid_from,
    edge.valid_until AS relation_valid_until
FROM current_edges AS edge;

COMMENT ON VIEW kb.v_concept_neighbours IS
    'Bidirectional traversal surface for current active typed graph assertions; symmetric traversal is labelled explicitly and carries no universal weight.';

-- This is a qualitative profile only. It deliberately contains neither
-- empirical coordinates nor an intrinsic concept intensity/vector.
CREATE VIEW kb.v_concept_profile AS
SELECT
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.description,
    concept.editorial_note,
    COALESCE(labels.preferred_labels, '[]'::JSONB) AS preferred_labels,
    COALESCE(dimensions.qualitative_dimension_links, '[]'::JSONB)
        AS qualitative_dimension_links
FROM kb.concept AS concept
LEFT JOIN LATERAL (
    SELECT jsonb_agg(
        jsonb_build_object(
            'language_tag_code', expression.language_tag_code,
            'expression_key', expression.expression_key,
            'label', expression.expression_text,
            'mapping_type_code', lexicalization.mapping_type_code
        )
        ORDER BY
            expression.language_tag_code,
            mapping_type.retrieval_precedence,
            expression.normalized_text,
            expression.expression_key
    ) AS preferred_labels
    FROM kb.lexicalization AS lexicalization
    JOIN ref.mapping_type AS mapping_type
      ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
     AND mapping_type.is_preferred
    JOIN kb.lexical_expression AS expression
      ON expression.expression_id = lexicalization.expression_id
     AND expression.lifecycle_status_code = 'active'
    WHERE lexicalization.concept_id = concept.concept_id
      AND lexicalization.lifecycle_status_code = 'active'
      AND lexicalization.valid_from <= CURRENT_TIMESTAMP
      AND (
            lexicalization.valid_until IS NULL
            OR lexicalization.valid_until > CURRENT_TIMESTAMP
          )
) AS labels ON TRUE
LEFT JOIN LATERAL (
    SELECT jsonb_agg(
        jsonb_build_object(
            'link_key', link.link_key,
            'dimension_key', dimension.dimension_key,
            'dimension_name', dimension.name,
            'measurement_semantics', dimension.measurement_semantics,
            'unit', dimension.unit,
            'link_semantics', link.link_semantics
        )
        ORDER BY dimension.dimension_key, link.link_key
    ) AS qualitative_dimension_links
    FROM kb.concept_dimension_link AS link
    JOIN kb.sensory_dimension AS dimension
      ON dimension.sensory_dimension_id = link.sensory_dimension_id
     AND dimension.lifecycle_status_code = 'active'
    WHERE link.concept_id = concept.concept_id
      AND link.lifecycle_status_code = 'active'
) AS dimensions ON TRUE
WHERE concept.lifecycle_status_code = 'active';

COMMENT ON VIEW kb.v_concept_profile IS
    'One row per active concept with ordered preferred labels and qualitative dimension links; no numeric sensory vector or intrinsic intensity is exposed.';

-- A normalized support inventory resolves the XOR source origin to an
-- effective source version while retaining the optional dataset identity.
CREATE VIEW evidence.v_source_coverage AS
WITH support_rows AS (
    SELECT
        'concept'::TEXT AS assertion_kind,
        concept.concept_id AS assertion_id,
        concept.concept_key AS assertion_key,
        support.concept_support_id AS support_id,
        support.concept_support_key AS support_key,
        support.source_version_id AS direct_source_version_id,
        support.dataset_id,
        support.locator,
        support.notes
    FROM evidence.concept_support AS support
    JOIN kb.concept AS concept
      ON concept.concept_id = support.concept_id

    UNION ALL

    SELECT
        'lexicalization'::TEXT,
        lexicalization.lexicalization_id,
        lexicalization.lexicalization_key,
        support.lexicalization_support_id,
        support.lexicalization_support_key,
        support.source_version_id,
        support.dataset_id,
        support.locator,
        support.notes
    FROM evidence.lexicalization_support AS support
    JOIN kb.lexicalization AS lexicalization
      ON lexicalization.lexicalization_id = support.lexicalization_id

    UNION ALL

    SELECT
        'concept_relation'::TEXT,
        relation.concept_relation_id,
        relation.relation_key,
        support.relation_support_id,
        support.relation_support_key,
        support.source_version_id,
        support.dataset_id,
        support.locator,
        support.notes
    FROM evidence.relation_support AS support
    JOIN kb.concept_relation AS relation
      ON relation.concept_relation_id = support.concept_relation_id

    UNION ALL

    SELECT
        'concept_dimension_link'::TEXT,
        link.concept_dimension_link_id,
        link.link_key,
        support.concept_dimension_link_support_id,
        support.concept_dimension_link_support_key,
        support.source_version_id,
        support.dataset_id,
        support.locator,
        support.notes
    FROM evidence.concept_dimension_link_support AS support
    JOIN kb.concept_dimension_link AS link
      ON link.concept_dimension_link_id = support.concept_dimension_link_id
)
SELECT
    support.assertion_kind,
    support.assertion_id,
    support.assertion_key,
    support.support_id,
    support.support_key,
    support.locator,
    support.notes,
    dataset.dataset_id,
    dataset.dataset_key,
    source_version.source_version_id,
    source_version.source_version_key,
    source.source_id,
    source.source_key,
    source.title AS source_title,
    policy.license_policy_id,
    policy.license_policy_key,
    policy.access_class_code,
    access_class.permits_raw_text AS access_permits_raw_text,
    policy.rights_status_code,
    rights_status.is_verified AS rights_is_verified,
    policy.redistributable,
    policy.derivative_work_allowed,
    policy.commercial_use_allowed,
    policy.machine_use_allowed,
    policy.production_export_allowed,
    policy.checked_on AS rights_checked_on
FROM support_rows AS support
LEFT JOIN evidence.dataset AS dataset
  ON dataset.dataset_id = support.dataset_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = COALESCE(
        support.direct_source_version_id,
        dataset.source_version_id
     )
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS policy
  ON policy.license_policy_id = source_version.license_policy_id
JOIN ref.access_class AS access_class
  ON access_class.access_class_code = policy.access_class_code
JOIN ref.rights_status AS rights_status
  ON rights_status.rights_status_code = policy.rights_status_code;

COMMENT ON VIEW evidence.v_source_coverage IS
    'Canonical assertion support resolved to versioned sources, datasets, and explicit rights metadata; it exposes no copied source content.';

-- Security-barrier evaluation prevents caller predicates from being pushed
-- beneath the rights gates. The view exposes observation snippets, never the
-- captured document raw_text column, and only when all three independent
-- policy checks explicitly permit production raw-text export.
CREATE VIEW corpus.v_distributable_observations
WITH (security_barrier = true) AS
SELECT
    observation.raw_observation_id,
    observation.raw_observation_key,
    observation.observation_text,
    observation.character_start,
    observation.character_end,
    observation.observation_metadata,
    document.captured_document_id,
    document.captured_document_key,
    document.external_document_key,
    document.captured_at,
    corpus_record.corpus_id,
    corpus_record.corpus_key,
    corpus_record.language_tag_code,
    source_version.source_version_id,
    source_version.source_version_key,
    source.source_id,
    source.source_key,
    policy.license_policy_id,
    policy.license_policy_key
FROM corpus.raw_observation AS observation
JOIN corpus.captured_document AS document
  ON document.captured_document_id = observation.captured_document_id
JOIN corpus.corpus AS corpus_record
  ON corpus_record.corpus_id = document.corpus_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = document.source_version_id
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS policy
  ON policy.license_policy_id = source_version.license_policy_id
JOIN ref.rights_status AS rights_status
  ON rights_status.rights_status_code = policy.rights_status_code
JOIN ref.access_class AS access_class
  ON access_class.access_class_code = policy.access_class_code
WHERE policy.production_export_allowed IS TRUE
  AND rights_status.is_verified IS TRUE
  AND access_class.permits_raw_text IS TRUE;

COMMENT ON VIEW corpus.v_distributable_observations IS
    'Rights-gated observation snippets for production export. Restricted, unverified, and raw-text-prohibited source versions cannot enter this security-barrier view.';

-- This governance view contains identifiers and extracted term forms, not raw
-- document or observation text. A stored unresolved decision is shown only
-- while the expression still has no current active lexicalization.
CREATE VIEW corpus.v_unresolved_industry_terms AS
SELECT
    resolution.observation_resolution_id,
    resolution.observation_resolution_key,
    resolution.resolution_status_code,
    resolution.resolution_note,
    occurrence.observation_expression_id,
    occurrence.observation_expression_key,
    occurrence.occurrence_ordinal,
    expression.expression_id,
    expression.expression_key,
    expression.language_tag_code,
    expression.expression_text,
    expression.normalized_text,
    observation.raw_observation_id,
    observation.raw_observation_key,
    document.captured_document_id,
    document.captured_document_key,
    document.source_version_id,
    corpus_record.corpus_id,
    corpus_record.corpus_key
FROM corpus.observation_resolution AS resolution
JOIN corpus.observation_expression AS occurrence
  ON occurrence.observation_expression_id = resolution.observation_expression_id
JOIN kb.lexical_expression AS expression
  ON expression.expression_id = occurrence.expression_id
 AND expression.lifecycle_status_code = 'active'
JOIN corpus.raw_observation AS observation
  ON observation.raw_observation_id = occurrence.raw_observation_id
JOIN corpus.captured_document AS document
  ON document.captured_document_id = observation.captured_document_id
JOIN corpus.corpus AS corpus_record
  ON corpus_record.corpus_id = document.corpus_id
WHERE resolution.resolution_status_code = 'unresolved'
  AND NOT EXISTS (
        SELECT 1
        FROM kb.lexicalization AS lexicalization
        WHERE lexicalization.expression_id = expression.expression_id
          AND lexicalization.lifecycle_status_code = 'active'
          AND lexicalization.valid_from <= CURRENT_TIMESTAMP
          AND (
                lexicalization.valid_until IS NULL
                OR lexicalization.valid_until > CURRENT_TIMESTAMP
              )
  );

COMMENT ON VIEW corpus.v_unresolved_industry_terms IS
    'Explicitly unresolved observed expressions that still have no current active canonical lexicalization; raw captured and observation text is excluded.';

CREATE VIEW ml.v_inferred_mappings_requiring_review AS
SELECT
    candidate.mapping_candidate_id,
    candidate.mapping_candidate_key,
    candidate.candidate_status_code,
    candidate.rank AS candidate_rank,
    candidate.rationale AS candidate_rationale,
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code AS concept_lifecycle_status_code,
    inference.mapping_inference_id,
    inference.mapping_inference_key,
    inference.resolution_status_code AS inference_resolution_status_code,
    inference.inferred_at,
    inference.resolution_notes,
    run.model_run_id,
    run.model_run_key,
    run.model_run_status_code,
    run.input_dataset_id,
    run.input_corpus_id,
    run.started_at,
    run.completed_at,
    version.model_version_id,
    version.model_version_key,
    version.version_label AS model_version_label,
    version.created_at AS model_version_created_at,
    model.model_id,
    model.model_key,
    model.name AS model_name,
    model.model_family,
    occurrence.observation_expression_id,
    occurrence.observation_expression_key,
    expression.expression_id,
    expression.expression_key,
    expression.language_tag_code,
    expression.expression_text,
    expression.normalized_text
FROM ml.mapping_candidate AS candidate
JOIN ref.candidate_status AS candidate_status
  ON candidate_status.candidate_status_code = candidate.candidate_status_code
 AND candidate_status.is_reviewable
JOIN ml.mapping_inference AS inference
  ON inference.mapping_inference_id = candidate.mapping_inference_id
JOIN ml.model_run AS run
  ON run.model_run_id = inference.model_run_id
JOIN ml.model_version AS version
  ON version.model_version_id = run.model_version_id
JOIN ml.model AS model
  ON model.model_id = version.model_id
JOIN corpus.observation_expression AS occurrence
  ON occurrence.observation_expression_id = inference.observation_expression_id
JOIN kb.lexical_expression AS expression
  ON expression.expression_id = occurrence.expression_id
JOIN kb.concept AS concept
  ON concept.concept_id = candidate.concept_id
WHERE NOT EXISTS (
    SELECT 1
    FROM audit.mapping_review AS mapping_review
    WHERE mapping_review.mapping_candidate_id = candidate.mapping_candidate_id
);

COMMENT ON VIEW ml.v_inferred_mappings_requiring_review IS
    'Reviewable, unreviewed mapping candidates with their immutable model, version, run, inference, observed-expression, and candidate-concept chain; no promotion is implied.';

-- Lexical candidate retrieval is deliberately bounded and interpretable:
-- preferred exact mappings, approved exact variants, lexical-only trigram KNN
-- when no exact expression exists, then explicitly typed graph neighbours.
-- No embedding, weighted score, automatic promotion, or sensory interpretation
-- is introduced. An exact but unmapped expression therefore returns only the
-- explicit UNRESOLVED row and cannot fall through to a nearby spelling.
CREATE FUNCTION kb.retrieve_lexical_candidates(
    query TEXT,
    language TEXT DEFAULT 'en',
    top_k INTEGER DEFAULT 5,
    threshold REAL DEFAULT 0.35::REAL
)
RETURNS TABLE (
    stage TEXT,
    stage_order INTEGER,
    matched_expression_key TEXT,
    concept_key TEXT,
    concept_type_code TEXT,
    relation_type_code TEXT,
    similarity_score REAL,
    resolution_status TEXT
)
LANGUAGE SQL
STABLE
PARALLEL SAFE
SET search_path = pg_catalog, public
AS $retrieve_lexical_candidates$
WITH params AS (
    SELECT
        kb.normalize_expression($1) AS normalized_query,
        COALESCE(NULLIF(btrim($2), ''), 'en') AS language_tag_code,
        GREATEST(COALESCE($3, 5), 1) AS requested_top_k,
        LEAST(GREATEST(COALESCE($4, 0.35::REAL), 0::REAL), 1::REAL)
            AS similarity_threshold
),
exact_expression AS (
    SELECT
        expression.expression_id,
        expression.expression_key
    FROM kb.lexical_expression AS expression
    CROSS JOIN params
    WHERE expression.language_tag_code = params.language_tag_code
      AND expression.normalized_text = params.normalized_query
      AND expression.lifecycle_status_code = 'active'
),
exact_candidates AS (
    SELECT
        CASE
            WHEN mapping_type.is_preferred THEN 'EXACT_PREFERRED_LABEL'::TEXT
            ELSE 'EXACT_APPROVED_VARIANT'::TEXT
        END AS stage,
        CASE WHEN mapping_type.is_preferred THEN 1 ELSE 2 END::INTEGER
            AS stage_order,
        expression.expression_key AS matched_expression_key,
        concept.concept_id,
        concept.concept_key,
        concept.concept_type_code,
        NULL::TEXT AS relation_type_code,
        1::REAL AS similarity_score,
        'RESOLVED'::TEXT AS resolution_status
    FROM exact_expression AS expression
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
),
nearest_expressions AS (
    SELECT
        nearest.expression_id,
        nearest.expression_key,
        public.similarity(nearest.normalized_text, params.normalized_query)
            AS similarity_score
    FROM params
    CROSS JOIN LATERAL (
        SELECT
            expression.expression_id,
            expression.expression_key,
            expression.normalized_text
        FROM kb.lexical_expression AS expression
        WHERE expression.language_tag_code = params.language_tag_code
          AND expression.lifecycle_status_code = 'active'
          AND params.normalized_query <> ''
        ORDER BY
            expression.normalized_text OPERATOR(public.<->) params.normalized_query,
            expression.expression_key
        LIMIT params.requested_top_k
    ) AS nearest
    WHERE NOT EXISTS (SELECT 1 FROM exact_expression)
),
fuzzy_ranked AS (
    SELECT
        nearest.expression_key AS matched_expression_key,
        concept.concept_id,
        concept.concept_key,
        concept.concept_type_code,
        nearest.similarity_score,
        ROW_NUMBER() OVER (
            PARTITION BY concept.concept_id
            ORDER BY
                nearest.similarity_score DESC,
                mapping_type.retrieval_precedence,
                nearest.expression_key,
                concept.concept_key
        ) AS concept_match_rank
    FROM nearest_expressions AS nearest
    CROSS JOIN params
    JOIN kb.lexicalization AS lexicalization
      ON lexicalization.expression_id = nearest.expression_id
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
    WHERE nearest.similarity_score >= params.similarity_threshold
),
fuzzy_candidates AS (
    SELECT
        'TRIGRAM'::TEXT AS stage,
        3::INTEGER AS stage_order,
        fuzzy.matched_expression_key,
        fuzzy.concept_id,
        fuzzy.concept_key,
        fuzzy.concept_type_code,
        NULL::TEXT AS relation_type_code,
        fuzzy.similarity_score::REAL,
        'RESOLVED'::TEXT AS resolution_status
    FROM fuzzy_ranked AS fuzzy
    WHERE fuzzy.concept_match_rank = 1
),
direct_candidates AS (
    SELECT * FROM exact_candidates
    UNION ALL
    SELECT * FROM fuzzy_candidates
),
graph_seeds AS (
    SELECT DISTINCT ON (candidate.concept_id)
        candidate.concept_id,
        candidate.matched_expression_key
    FROM direct_candidates AS candidate
    ORDER BY
        candidate.concept_id,
        candidate.stage_order,
        candidate.matched_expression_key
),
graph_ranked AS (
    SELECT
        seed.matched_expression_key,
        neighbour.neighbour_concept_key AS concept_key,
        neighbour.neighbour_concept_type_code AS concept_type_code,
        neighbour.relation_type_code,
        ROW_NUMBER() OVER (
            ORDER BY
                neighbour.relation_type_code,
                neighbour.neighbour_concept_key,
                seed.matched_expression_key,
                neighbour.concept_relation_id
        ) AS graph_rank
    FROM graph_seeds AS seed
    JOIN kb.v_concept_neighbours AS neighbour
      ON neighbour.concept_id = seed.concept_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM direct_candidates AS direct
        WHERE direct.concept_key = neighbour.neighbour_concept_key
    )
),
graph_candidates AS (
    SELECT
        'GRAPH_EXPANSION'::TEXT AS stage,
        4::INTEGER AS stage_order,
        graph.matched_expression_key,
        NULL::BIGINT AS concept_id,
        graph.concept_key,
        graph.concept_type_code,
        graph.relation_type_code,
        NULL::REAL AS similarity_score,
        'RESOLVED'::TEXT AS resolution_status
    FROM graph_ranked AS graph
    CROSS JOIN params
    WHERE graph.graph_rank <= params.requested_top_k
),
unresolved AS (
    SELECT
        'UNRESOLVED'::TEXT AS stage,
        5::INTEGER AS stage_order,
        (
            SELECT expression.expression_key
            FROM exact_expression AS expression
            ORDER BY expression.expression_key
            LIMIT 1
        ) AS matched_expression_key,
        NULL::BIGINT AS concept_id,
        NULL::TEXT AS concept_key,
        NULL::TEXT AS concept_type_code,
        NULL::TEXT AS relation_type_code,
        NULL::REAL AS similarity_score,
        'UNRESOLVED'::TEXT AS resolution_status
    WHERE NOT EXISTS (SELECT 1 FROM direct_candidates)
),
all_results AS (
    SELECT * FROM direct_candidates
    UNION ALL
    SELECT * FROM graph_candidates
    UNION ALL
    SELECT * FROM unresolved
)
SELECT
    result.stage,
    result.stage_order,
    result.matched_expression_key,
    result.concept_key,
    result.concept_type_code,
    result.relation_type_code,
    result.similarity_score,
    result.resolution_status
FROM all_results AS result
ORDER BY
    result.stage_order,
    result.similarity_score DESC NULLS LAST,
    result.matched_expression_key NULLS LAST,
    result.relation_type_code NULLS FIRST,
    result.concept_key NULLS LAST;
$retrieve_lexical_candidates$;

COMMENT ON FUNCTION kb.retrieve_lexical_candidates(TEXT, TEXT, INTEGER, REAL) IS
    'Deterministic lexical retrieval: exact preferred labels, exact approved variants, GiST trigram fallback only without an exact expression, typed graph expansion, or one explicit UNRESOLVED result. Scores are lexical trigram similarity only, never sensory similarity.';

COMMIT;
