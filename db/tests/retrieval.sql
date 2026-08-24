\set ON_ERROR_STOP on
\pset pager off

-- Small interpretable retrieval prototype smoke tests.  Trigram scores below
-- are lexical spelling similarity only; typed graph rows carry no score.

BEGIN TRANSACTION READ ONLY;

\echo RETRIEVAL_CASE=grapefruit_exact
SELECT *
FROM kb.retrieve_lexical_candidates('grapefruit', 'en', 5, 0.35::REAL);

\echo RETRIEVAL_CASE=pink_grapefruit_approved_variant
SELECT *
FROM kb.retrieve_lexical_candidates('pink-grapefruit', 'en', 5, 0.35::REAL);

\echo RETRIEVAL_CASE=grapefruit_misspelling
SELECT *
FROM kb.retrieve_lexical_candidates('grapfruit', 'en', 5, 0.30::REAL);

\echo RETRIEVAL_CASE=earl_grey_graph_expansion
SELECT *
FROM kb.retrieve_lexical_candidates('Earl Grey', 'en', 5, 0.35::REAL);

\echo RETRIEVAL_CASE=meteor_fruit_unresolved
SELECT *
FROM kb.retrieve_lexical_candidates('meteor fruit', 'en', 5, 0.20::REAL);

DO $retrieval_smoke$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'grapefruit', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage = 'EXACT_PREFERRED_LABEL'
          AND result.stage_order = 1
          AND result.matched_expression_key = 'expression.en.grapefruit'
          AND result.concept_key = 'sensory.grapefruit'
          AND result.concept_type_code = 'sensory_attribute'
          AND result.relation_type_code IS NULL
          AND result.similarity_score = 1::REAL
          AND result.resolution_status = 'RESOLVED'
    ) OR EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'grapefruit', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage IN ('TRIGRAM', 'UNRESOLVED')
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_exact_precedes_trigram_ck',
            MESSAGE = 'retrieval smoke: grapefruit must resolve by exact preferred label without trigram fallback';
    END IF;

    IF pg_catalog.to_regprocedure(
        'audit.run_round2a_validation_queries()'
    ) IS NULL AND (
        NOT EXISTS (
            SELECT 1
            FROM kb.retrieve_lexical_candidates(
                'pink-grapefruit', 'en', 5, 0.35::REAL
            ) AS result
            WHERE result.stage = 'EXACT_APPROVED_VARIANT'
              AND result.stage_order = 2
              AND result.matched_expression_key = 'expression.en.pink_grapefruit_hyphenated'
              AND result.concept_key = 'sensory.pink_grapefruit'
              AND result.resolution_status = 'RESOLVED'
        ) OR EXISTS (
            SELECT 1
            FROM kb.retrieve_lexical_candidates(
                'pink-grapefruit', 'en', 5, 0.35::REAL
            ) AS result
            WHERE result.stage IN ('TRIGRAM', 'UNRESOLVED')
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_approved_variant_precedes_trigram_ck',
            MESSAGE = 'retrieval smoke: pink-grapefruit must use its approved variant mapping';
    ELSIF pg_catalog.to_regprocedure(
        'audit.run_round2a_validation_queries()'
    ) IS NOT NULL AND (
        (
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
              AND result.stage_order = 5
              AND result.matched_expression_key = 'expression.en.pink_grapefruit_hyphenated'
              AND result.concept_key IS NULL
              AND result.resolution_status = 'UNRESOLVED'
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_round2a_candidate_not_forced_ck',
            MESSAGE = 'retrieval smoke: Round 2A must not force the candidate pink-grapefruit identity into active retrieval';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'grapfruit', 'en', 5, 0.30::REAL
        ) AS result
        WHERE result.stage = 'TRIGRAM'
          AND result.stage_order = 3
          AND result.matched_expression_key = 'expression.en.grapefruit'
          AND result.concept_key = 'sensory.grapefruit'
          AND result.similarity_score >= 0.30::REAL
          AND result.similarity_score < 1::REAL
          AND result.resolution_status = 'RESOLVED'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_trigram_misspelling_ck',
            MESSAGE = 'retrieval smoke: grapfruit must find grapefruit through lexical trigram lookup';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'Earl Grey', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage = 'EXACT_PREFERRED_LABEL'
          AND result.concept_key = 'composite.earl_grey'
    ) OR (
        SELECT count(*)
        FROM kb.retrieve_lexical_candidates(
            'Earl Grey', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage = 'GRAPH_EXPANSION'
          AND (
                (
                    result.relation_type_code = 'consumer_reference_for'
                    AND result.concept_key = 'sensory.bergamot'
                )
                OR (
                    result.relation_type_code = 'composite_has_component'
                    AND result.concept_key = 'sensory.black_tea'
                )
              )
    ) <> 2 OR EXISTS (
        SELECT 1
        FROM kb.retrieve_lexical_candidates(
            'Earl Grey', 'en', 5, 0.35::REAL
        ) AS result
        WHERE result.stage IN ('EXACT_PREFERRED_LABEL', 'EXACT_APPROVED_VARIANT')
          AND result.concept_key = 'sensory.bergamot'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_earl_grey_typed_expansion_ck',
            MESSAGE = 'retrieval smoke: Earl Grey must resolve to the composite and expand to its two typed neighbours';
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
          AND result.stage_order = 5
          AND result.matched_expression_key = 'expression.en.meteor_fruit'
          AND result.concept_key IS NULL
          AND result.concept_type_code IS NULL
          AND result.relation_type_code IS NULL
          AND result.similarity_score IS NULL
          AND result.resolution_status = 'UNRESOLVED'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_exact_unmapped_stays_unresolved_ck',
            MESSAGE = 'retrieval smoke: an exact unmapped meteor-fruit expression must not fall through to a nearest concept';
    END IF;

    RAISE NOTICE 'TRIGRAM_RETRIEVAL_PASS=true';
END
$retrieval_smoke$;

COMMIT;

\echo TRIGRAM_RETRIEVAL_PASS=true
