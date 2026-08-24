\set ON_ERROR_STOP on
\pset pager off

-- Round 2A retrieval verifies that the expanded ontology remains addressable
-- through canonical lexicalizations only. Source-scheme labels and ambiguous
-- candidate mappings do not silently become canonical classifier output.

BEGIN TRANSACTION READ ONLY;

\echo ROUND2A_RETRIEVAL_SAMPLE
SELECT result.*
FROM (
    SELECT expression.expression_text
    FROM kb.concept AS concept
    JOIN kb.lexicalization AS lexicalization
      ON lexicalization.concept_id = concept.concept_id
    JOIN ref.mapping_type AS mapping_type
      ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
     AND mapping_type.is_preferred
    JOIN kb.lexical_expression AS expression
      ON expression.expression_id = lexicalization.expression_id
    WHERE concept.lifecycle_status_code = 'active'
      AND concept.concept_type_code = 'sensory_attribute'
      AND expression.language_tag_code = 'en'
    ORDER BY concept.concept_key
    LIMIT 1
) AS sample
CROSS JOIN LATERAL kb.retrieve_lexical_candidates(
    sample.expression_text,
    'en',
    5,
    0.35::REAL
) AS result;

\echo ROUND2A_RETRIEVAL_AMBIGUITY
SELECT *
FROM kb.retrieve_lexical_candidates('winey', 'en', 5, 0.35::REAL);

DO $round2a_retrieval$
BEGIN
    -- Every active concept's required preferred English label must round-trip
    -- to that same concept at the exact-preferred stage.
    IF EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.concept_id = concept.concept_id
         AND lexicalization.lifecycle_status_code = 'active'
         AND lexicalization.valid_from <= CURRENT_TIMESTAMP
         AND (
                lexicalization.valid_until IS NULL
                OR lexicalization.valid_until > CURRENT_TIMESTAMP
             )
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
         AND mapping_type.is_preferred
        JOIN kb.lexical_expression AS expression
          ON expression.expression_id = lexicalization.expression_id
         AND expression.lifecycle_status_code = 'active'
         AND expression.language_tag_code = 'en'
        WHERE concept.lifecycle_status_code = 'active'
          AND NOT EXISTS (
              SELECT 1
              FROM kb.retrieve_lexical_candidates(
                  expression.expression_text,
                  expression.language_tag_code,
                  5,
                  1::REAL
              ) AS result
              WHERE result.stage = 'EXACT_PREFERRED_LABEL'
                AND result.concept_key = concept.concept_key
                AND result.resolution_status = 'RESOLVED'
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_preferred_label_roundtrip_ck',
            MESSAGE = 'an active concept preferred English label failed exact canonical retrieval';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM kb.lexical_expression AS expression
        WHERE expression.lifecycle_status_code = 'active'
          AND expression.language_tag_code = 'en'
          AND EXISTS (
              SELECT 1
              FROM kb.lexicalization AS lexicalization
              JOIN ref.mapping_type AS mapping_type
                ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
              JOIN kb.concept AS concept
                ON concept.concept_id = lexicalization.concept_id
              WHERE lexicalization.expression_id = expression.expression_id
                AND lexicalization.lifecycle_status_code = 'active'
                AND mapping_type.is_preferred
                AND concept.lifecycle_status_code = 'active'
          )
          AND EXISTS (
              SELECT 1
              FROM kb.retrieve_lexical_candidates(
                  expression.expression_text,
                  'en',
                  5,
                  0.35::REAL
              ) AS result
              WHERE result.stage IN ('TRIGRAM', 'UNRESOLVED')
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_exact_precedes_fallback_ck',
            MESSAGE = 'an exact active preferred expression incorrectly reached trigram or unresolved fallback';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'grapfruit', 'en', 5, 0.30::REAL
        ) AS result
        WHERE result.stage = 'TRIGRAM'
          AND result.concept_key = 'sensory.grapefruit'
          AND result.similarity_score >= 0.30::REAL
          AND result.similarity_score < 1::REAL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_trigram_retrieval_ck',
            MESSAGE = 'expanded ontology no longer retrieves grapefruit for the grapfruit spelling variant';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'sensory.pink_grapefruit'
          AND concept.concept_type_code = 'sensory_attribute'
          AND concept.lifecycle_status_code = 'candidate'
    ) OR (
        SELECT count(*)
        FROM kb.retrieve_lexical_candidates(
            'pink-grapefruit', 'en', 5, 0.35::REAL
        ) AS result
    ) <> 1 OR NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'pink-grapefruit', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage = 'UNRESOLVED'
          AND result.matched_expression_key =
                'expression.en.pink_grapefruit_hyphenated'
          AND result.concept_key IS NULL
          AND result.resolution_status = 'UNRESOLVED'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_pink_grapefruit_candidate_safety_ck',
            MESSAGE = 'pink grapefruit must remain a distinct candidate identity that retrieval does not force active';
    END IF;

    IF (
        SELECT count(*)
        FROM kb.retrieve_lexical_candidates(
            'meteor fruit', 'en', 5, 0.20::REAL
        ) AS result
    ) <> 1 OR NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'meteor fruit', 'en', 5, 0.20::REAL
        ) AS result
        WHERE result.stage = 'UNRESOLVED'
          AND result.concept_key IS NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_unresolved_preserved_ck',
            MESSAGE = 'meteor fruit must remain a single explicit UNRESOLVED result after ontology expansion';
    END IF;

    -- Winey remains explicitly polysemous in canonical source data, while
    -- retrieval refuses to force the ambiguous expression through a
    -- polysemous/candidate mapping without contextual disambiguation.
    IF (
        SELECT count(DISTINCT lexicalization.concept_id)
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        WHERE expression.expression_key = 'expression.en.winey'
          AND lexicalization.lifecycle_status_code = 'active'
    ) <> 2 OR (
        SELECT count(*)
        FROM kb.retrieve_lexical_candidates(
            'winey', 'en', 5, 0.35::REAL
        ) AS result
    ) <> 1 OR NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'winey', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage = 'UNRESOLVED'
          AND result.concept_key IS NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_ambiguous_retrieval_safety_ck',
            MESSAGE = 'winey ambiguity must remain explicit and must not be forced to one canonical concept';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'Earl Grey', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage IN ('EXACT_PREFERRED_LABEL', 'EXACT_APPROVED_VARIANT')
          AND result.concept_key = 'sensory.bergamot'
    ) OR NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'Earl Grey', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage = 'EXACT_PREFERRED_LABEL'
          AND result.concept_key = 'composite.earl_grey'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2a_composite_retrieval_safety_ck',
            MESSAGE = 'Earl Grey must resolve to its composite identity, not lexicalize directly as bergamot';
    END IF;

    RAISE NOTICE 'ROUND2A_RETRIEVAL_PASS=true';
END
$round2a_retrieval$;

COMMIT;

\echo ROUND2A_RETRIEVAL_PASS=true
