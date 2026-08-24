\set ON_ERROR_STOP on
\pset pager off

-- Round 2B deterministic retrieval contract. Normalization is mandatory
-- preprocessing, while A/B/C/D are ordinal candidate-generation tiers rather
-- than coefficients in a blended score. Seed-specific assertions are gated on
-- the immutable pilot snapshot key so migrations 012--014 remain testable
-- before the separately generated 015 data migration is installed.

BEGIN TRANSACTION READ ONLY;

DO $round2b_retrieval_reference_contract$
BEGIN
    IF EXISTS (
        (
            SELECT
                retrieval_tier_code,
                tier_order,
                is_graph_expansion
            FROM ref.retrieval_tier
            EXCEPT
            SELECT *
            FROM (
                VALUES
                    ('A'::TEXT, 1::SMALLINT, FALSE),
                    ('B', 2::SMALLINT, FALSE),
                    ('C', 3::SMALLINT, FALSE),
                    ('D', 4::SMALLINT, TRUE)
            ) AS expected(code, tier_order, is_graph_expansion)
        )
        UNION ALL
        (
            SELECT *
            FROM (
                VALUES
                    ('A'::TEXT, 1::SMALLINT, FALSE),
                    ('B', 2::SMALLINT, FALSE),
                    ('C', 3::SMALLINT, FALSE),
                    ('D', 4::SMALLINT, TRUE)
            ) AS expected(code, tier_order, is_graph_expansion)
            EXCEPT
            SELECT
                retrieval_tier_code,
                tier_order,
                is_graph_expansion
            FROM ref.retrieval_tier
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_retrieval_tier_contract_ck',
            MESSAGE = 'A/B/C/D retrieval tiers are not the exact ordinal contract';
    END IF;

    IF EXISTS (
        (
            SELECT audit_split_code, is_held_out
            FROM ref.audit_split
            EXCEPT
            SELECT *
            FROM (
                VALUES
                    ('development'::TEXT, FALSE),
                    ('held_out', TRUE)
            ) AS expected(audit_split_code, is_held_out)
        )
        UNION ALL
        (
            SELECT *
            FROM (
                VALUES
                    ('development'::TEXT, FALSE),
                    ('held_out', TRUE)
            ) AS expected(audit_split_code, is_held_out)
            EXCEPT
            SELECT audit_split_code, is_held_out
            FROM ref.audit_split
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_audit_split_contract_ck',
            MESSAGE = 'development and held-out audit splits are not independently governed';
    END IF;

    IF EXISTS (
        (
            SELECT
                relevance_grade_code,
                ordinal_value,
                gain_value,
                is_unresolved
            FROM ref.relevance_grade
            EXCEPT
            SELECT *
            FROM (
                VALUES
                    ('0'::TEXT, 0::SMALLINT, 0::NUMERIC, FALSE),
                    ('1', 1::SMALLINT, 1::NUMERIC, FALSE),
                    ('2', 2::SMALLINT, 3::NUMERIC, FALSE),
                    ('3', 3::SMALLINT, 7::NUMERIC, FALSE),
                    ('U', NULL::SMALLINT, NULL::NUMERIC, TRUE)
            ) AS expected(code, ordinal_value, gain_value, is_unresolved)
        )
        UNION ALL
        (
            SELECT *
            FROM (
                VALUES
                    ('0'::TEXT, 0::SMALLINT, 0::NUMERIC, FALSE),
                    ('1', 1::SMALLINT, 1::NUMERIC, FALSE),
                    ('2', 2::SMALLINT, 3::NUMERIC, FALSE),
                    ('3', 3::SMALLINT, 7::NUMERIC, FALSE),
                    ('U', NULL::SMALLINT, NULL::NUMERIC, TRUE)
            ) AS expected(code, ordinal_value, gain_value, is_unresolved)
            EXCEPT
            SELECT
                relevance_grade_code,
                ordinal_value,
                gain_value,
                is_unresolved
            FROM ref.relevance_grade
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_relevance_grade_contract_ck',
            MESSAGE = 'graded relevance or the case-level U expectation changed';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_proc AS procedure
        JOIN pg_namespace AS namespace
          ON namespace.oid = procedure.pronamespace
        WHERE namespace.nspname = 'audit'
          AND procedure.proname = 'calculate_retrieval_metrics'
          AND pg_get_function_identity_arguments(procedure.oid) =
              'audit_set_key text, model_run_key text, split_code text'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_metric_function_contract_ck',
            MESSAGE = 'the versioned graded retrieval metric interface is missing';
    END IF;

    RAISE NOTICE 'ROUND2B_RETRIEVAL_REFERENCE_CONTRACT_PASS=true';
END;
$round2b_retrieval_reference_contract$;

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

\echo ROUND2B_RETRIEVAL_SAMPLE_A
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'grapefruit', 'en', 'normalization.en_v1', 'A', 5, 0.35::REAL
);

\echo ROUND2B_RETRIEVAL_SAMPLE_B
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'earl grey tea', 'en', 'normalization.en_v1', 'B', 5, 0.35::REAL
);

\echo ROUND2B_RETRIEVAL_SAMPLE_C_OBSERVED_UNMAPPED
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'Hazelnuts', 'en', 'normalization.en_v1', 'C', 5, 0.35::REAL
);

\echo ROUND2B_RETRIEVAL_SAMPLE_D_GRAPH
SELECT *
FROM ml.retrieve_deterministic_candidates(
    'Earl Grey', 'en', 'normalization.en_v1', 'D', 10, 0.35::REAL
);

DO $round2b_retrieval_seed_contract$
DECLARE
    first_checksum TEXT;
    second_checksum TEXT;
    candidate_count BIGINT;
    minimum_rank INTEGER;
    maximum_rank INTEGER;
    distinct_rank_count BIGINT;
BEGIN
    -- NFC, case, whitespace, Unicode dash, apostrophe, and the deliberately
    -- small whole-phrase rule set are reproducible under the frozen v1 key.
    IF corpus.normalize_expression_v1(
           U&'Cafe\0301', 'normalization.en_v1'
       ) <> U&'caf\00E9'
       OR corpus.normalize_expression_v1(
           U&'  BLACK\00A0\00A0TEA  ', 'normalization.en_v1'
       ) <> 'black tea'
       OR corpus.normalize_expression_v1(
           U&'Tea\2014Like', 'normalization.en_v1'
       ) <> 'tea-like'
       OR corpus.normalize_expression_v1(
           U&'Farmer\2019s   Blend', 'normalization.en_v1'
       ) <> 'farmer''s blend'
       OR corpus.normalize_expression_v1(
           'Earl Gray', 'normalization.en_v1'
       ) <> 'earl grey'
       OR corpus.normalize_expression_v1(
           'Earl Gray Tea', 'normalization.en_v1'
       ) <> 'earl grey tea'
       OR corpus.normalize_expression_v1(
           'BLACK CURRANT', 'normalization.en_v1'
       ) <> 'blackcurrant' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_normalization_v1_contract_ck',
            MESSAGE = 'NFC, case, whitespace, punctuation, or whole-phrase v1 normalization changed';
    END IF;

    -- Normalization is preprocessing for baseline A, not a separately
    -- weighted or lower-precedence candidate lane.
    IF (
        SELECT count(*)
        FROM ml.retrieve_deterministic_candidates(
            '  GRAPEFRUIT  ', 'en', 'normalization.en_v1',
            'A', 5, 0.35::REAL
        )
    ) <> 1 OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            '  GRAPEFRUIT  ', 'en', 'normalization.en_v1',
            'A', 5, 0.35::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'RESOLVED'
          AND result.retrieval_tier_code = 'A'
          AND result.tier_order = 1
          AND result.concept_key = 'sensory.grapefruit'
          AND result.normalized_phrase_match
          AND NOT result.raw_surface_exact
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_normalization_preprocess_ck',
            MESSAGE = 'safe normalization did not remain mandatory preprocessing for tier A';
    END IF;

    -- A: current preferred lexicalization. No lower-precedence direct tier is
    -- permitted to compete after an exact preferred match.
    IF (
        SELECT count(*)
        FROM ml.retrieve_deterministic_candidates(
            'grapefruit', 'en', 'normalization.en_v1',
            'A', 5, 0.35::REAL
        )
    ) <> 1 OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'grapefruit', 'en', 'normalization.en_v1',
            'A', 5, 0.35::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'RESOLVED'
          AND result.candidate_rank = 1
          AND result.retrieval_tier_code = 'A'
          AND result.concept_key = 'sensory.grapefruit'
          AND result.mapping_type_code = 'preferred_label'
          AND result.raw_surface_exact
          AND result.normalized_phrase_match
          AND result.signal_ledger @>
              '[{"signal_code":"normalized_phrase_match"},
                {"signal_code":"raw_surface_exact"}]'::JSONB
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_tier_a_exact_ck',
            MESSAGE = 'preferred exact retrieval or its signal ledger changed';
    END IF;

    -- B: an approved variant is unavailable to A, but becomes the sole direct
    -- result in B. The Gray -> Grey rule still lands on B, not C.
    IF NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'earl grey tea', 'en', 'normalization.en_v1',
            'A', 5, 0.35::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'UNRESOLVED'
          AND result.concept_id IS NULL
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'earl grey tea', 'en', 'normalization.en_v1',
            'B', 5, 0.35::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'RESOLVED'
          AND result.candidate_rank = 1
          AND result.retrieval_tier_code = 'B'
          AND result.concept_key = 'composite.earl_grey'
          AND result.mapping_type_code = 'approved_variant'
          AND result.raw_surface_exact
          AND result.normalized_phrase_match
          AND result.signal_ledger @>
              '[{"signal_code":"normalized_phrase_match"},
                {"signal_code":"approved_variant_match"},
                {"signal_code":"raw_surface_exact"}]'::JSONB
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'Earl Gray Tea', 'en', 'normalization.en_v1',
            'B', 5, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'B'
          AND result.concept_key = 'composite.earl_grey'
          AND result.normalized_phrase_match
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_tier_b_variant_ck',
            MESSAGE = 'approved variant precedence or its signal ledger changed';
    END IF;

    -- C: the typo is absent under B, appears under C, and exposes only the
    -- orthographic similarity signal. Similarity is not sensory relevance.
    IF NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'grapfruit', 'en', 'normalization.en_v1',
            'B', 5, 0.30::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'UNRESOLVED'
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'grapfruit', 'en', 'normalization.en_v1',
            'C', 5, 0.30::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'CANDIDATE'
          AND result.retrieval_tier_code = 'C'
          AND result.concept_key = 'sensory.grapefruit'
          AND result.trigram_similarity >= 0.30::REAL
          AND jsonb_array_length(result.signal_ledger) = 1
          AND result.signal_ledger @>
              '[{"signal_code":"pg_trgm_similarity"}]'::JSONB
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_tier_c_trigram_ck',
            MESSAGE = 'canonical-dictionary trigram fallback or its signal ledger changed';
    END IF;

    -- The pilot contains an observed normalized identity for "hazelnuts" but
    -- that candidate expression has no approved canonical mapping. Its mere
    -- presence must not suppress fallback against the canonical dictionary.
    IF NOT EXISTS (
        SELECT 1
        FROM corpus.normalized_expression AS normalized
        JOIN corpus.normalized_expression_occurrence AS occurrence
          ON occurrence.normalized_expression_id =
             normalized.normalized_expression_id
        JOIN corpus.normalization_derivation_run AS derivation
          ON derivation.normalization_derivation_run_id =
             occurrence.normalization_derivation_run_id
        WHERE normalized.normalized_text = 'hazelnuts'
          AND derivation.normalization_derivation_run_key =
              'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
    ) OR EXISTS (
        SELECT 1
        FROM corpus.normalized_expression AS normalized
        JOIN corpus.lexical_expression_normalization AS normalization
          ON normalization.normalized_expression_id =
             normalized.normalized_expression_id
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = normalization.expression_id
         AND lexicalization.lifecycle_status_code = 'active'
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
         AND (
                mapping_type.is_preferred
                OR mapping_type.is_approved_variant
             )
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
         AND concept.lifecycle_status_code = 'active'
        WHERE normalized.normalized_text = 'hazelnuts'
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'Hazelnuts', 'en', 'normalization.en_v1',
            'C', 5, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'C'
          AND result.concept_key = 'sensory.hazelnut'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_observed_unmapped_fallback_ck',
            MESSAGE = 'an observed unmapped expression suppressed canonical trigram fallback';
    END IF;

    -- D: the composite seed stays rank one and exactly two current outgoing
    -- one-hop edges expose bergamot and black tea with separate graph ledgers.
    IF (
        SELECT count(*)
        FROM ml.retrieve_deterministic_candidates(
            'Earl Grey', 'en', 'normalization.en_v1',
            'D', 10, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
    ) <> 2 OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'Earl Grey', 'en', 'normalization.en_v1',
            'D', 10, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'A'
          AND result.candidate_rank = 1
          AND result.concept_key = 'composite.earl_grey'
    ) OR EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'Earl Grey', 'en', 'normalization.en_v1',
            'D', 10, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
          AND (
                result.seed_concept_key <> 'composite.earl_grey'
                OR result.relation_type_code NOT IN (
                    'consumer_reference_for',
                    'composite_has_component'
                )
                OR result.traversal_direction <> 'OUTGOING'
                OR result.graph_hop_count <> 1
                OR jsonb_array_length(result.signal_ledger) <> 1
                OR NOT result.signal_ledger @>
                    '[{"signal_code":"typed_graph_hop"}]'::JSONB
              )
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'Earl Grey', 'en', 'normalization.en_v1',
            'D', 10, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
          AND result.concept_key = 'sensory.bergamot'
          AND result.relation_type_code = 'consumer_reference_for'
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'Earl Grey', 'en', 'normalization.en_v1',
            'D', 10, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
          AND result.concept_key = 'sensory.black_tea'
          AND result.relation_type_code = 'composite_has_component'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_tier_d_graph_ck',
            MESSAGE = 'typed one-hop composite expansion or its signal ledger changed';
    END IF;

    -- The broader-than edge is deliberately tested in both stored directions.
    IF NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'grapefruit', 'en', 'normalization.en_v1',
            'D', 100, 1::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
          AND result.concept_key = 'category.citrus'
          AND result.relation_type_code = 'broader_than'
          AND result.traversal_direction = 'INCOMING'
    ) OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'citrus', 'en', 'normalization.en_v1',
            'D', 100, 1::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
          AND result.concept_key = 'sensory.grapefruit'
          AND result.relation_type_code = 'broader_than'
          AND result.traversal_direction = 'OUTGOING'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_graph_direction_ck',
            MESSAGE = 'typed broader/narrower traversal direction changed';
    END IF;

    -- Every D path must be a current canonical relation admitted by the frozen
    -- policy. Source-scheme edges, contrast, modifier, and process inference
    -- therefore cannot leak through the callable.
    IF EXISTS (
        SELECT 1
        FROM (
            VALUES
                ('Earl Grey'::TEXT),
                ('grapefruit'),
                ('citrus'),
                ('fermentation')
        ) AS probe(query_text)
        CROSS JOIN LATERAL ml.retrieve_deterministic_candidates(
            probe.query_text, 'en', 'normalization.en_v1',
            'D', 100, 0.35::REAL
        ) AS result
        LEFT JOIN kb.concept_relation AS relation
          ON relation.concept_relation_id = result.concept_relation_id
        LEFT JOIN ml.retrieval_graph_policy AS policy
          ON policy.retrieval_graph_policy_key = 'graph_policy.round2b.v1'
         AND policy.is_frozen
        LEFT JOIN ml.retrieval_graph_policy_rule AS policy_rule
          ON policy_rule.retrieval_graph_policy_id =
             policy.retrieval_graph_policy_id
         AND policy_rule.relation_type_code = result.relation_type_code
         AND policy_rule.traversal_direction = result.traversal_direction
         AND policy_rule.maximum_hops = result.graph_hop_count
        WHERE result.retrieval_tier_code = 'D'
          AND (
                relation.concept_relation_id IS NULL
                OR relation.lifecycle_status_code <> 'active'
                OR policy_rule.retrieval_graph_policy_rule_id IS NULL
                OR result.relation_type_code IN (
                    'contrasts_with', 'modifies'
                )
              )
    ) OR EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'fermentation', 'en', 'normalization.en_v1',
            'D', 100, 0.35::REAL
        ) AS result
        WHERE result.retrieval_tier_code = 'D'
          AND result.concept_type_code = 'sensory_attribute'
    ) OR EXISTS (
        SELECT 1
        FROM ml.retrieval_graph_policy
        WHERE retrieval_graph_policy_key = 'graph_policy.round2b.v1'
          AND (
                configuration ->> 'uses_source_schemes' <> 'false'
                OR configuration ->> 'uses_transitive_closure' <> 'false'
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_graph_boundary_ck',
            MESSAGE = 'scheme, process, contrast, modifier, or non-allowlisted graph inference leaked into retrieval';
    END IF;

    -- Global top-K is applied after tier ordering, not once per tier.
    SELECT
        count(*),
        min(result.candidate_rank),
        max(result.candidate_rank),
        count(DISTINCT result.candidate_rank)
    INTO
        candidate_count,
        minimum_rank,
        maximum_rank,
        distinct_rank_count
    FROM ml.retrieve_deterministic_candidates(
        'citrus', 'en', 'normalization.en_v1',
        'D', 3, 1::REAL
    ) AS result;

    IF candidate_count <> 3
       OR minimum_rank <> 1
       OR maximum_rank <> 3
       OR distinct_rank_count <> 3
       OR (
            SELECT count(*)
            FROM ml.retrieve_deterministic_candidates(
                'citrus', 'en', 'normalization.en_v1',
                'D', 1, 1::REAL
            )
       ) <> 1
       OR NOT EXISTS (
            SELECT 1
            FROM ml.retrieve_deterministic_candidates(
                'citrus', 'en', 'normalization.en_v1',
                'D', 1, 1::REAL
            ) AS result
            WHERE result.retrieval_tier_code = 'A'
              AND result.candidate_rank = 1
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_global_top_k_ck',
            MESSAGE = 'top_k is not a global deterministic cap after tier precedence';
    END IF;

    -- Identical calls must have identical ordering even where orthographic or
    -- graph candidates tie on their primary ordering keys.
    SELECT md5(string_agg(row_to_json(result)::TEXT, E'\n'
                          ORDER BY result.candidate_rank NULLS LAST))
    INTO first_checksum
    FROM ml.retrieve_deterministic_candidates(
        'fruit', 'en', 'normalization.en_v1',
        'D', 20, 0.20::REAL
    ) AS result;

    SELECT md5(string_agg(row_to_json(result)::TEXT, E'\n'
                          ORDER BY result.candidate_rank NULLS LAST))
    INTO second_checksum
    FROM ml.retrieve_deterministic_candidates(
        'fruit', 'en', 'normalization.en_v1',
        'D', 20, 0.20::REAL
    ) AS result;

    IF first_checksum IS NULL
       OR first_checksum IS DISTINCT FROM second_checksum
       OR EXISTS (
            SELECT 1
            FROM (
                SELECT
                    result.candidate_rank,
                    result.tier_order,
                    lag(result.tier_order) OVER (
                        ORDER BY result.candidate_rank
                    ) AS previous_tier_order
                FROM ml.retrieve_deterministic_candidates(
                    'fruit', 'en', 'normalization.en_v1',
                    'D', 20, 0.20::REAL
                ) AS result
                WHERE result.candidate_rank IS NOT NULL
            ) AS ordered
            WHERE ordered.tier_order < ordered.previous_tier_order
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_retrieval_tie_stability_ck',
            MESSAGE = 'repeated retrieval changed ordering or violated ordinal tier precedence';
    END IF;

    -- Empty candidate sets are represented by exactly one explicit row, with
    -- no fabricated nearest concept. The stricter threshold makes these short
    -- probes hard negatives rather than an assertion about all short strings.
    IF EXISTS (
        SELECT 1
        FROM (
            VALUES
                ('cash'::TEXT),
                ('pearls'),
                ('qx')
        ) AS hard_negative(query_text)
        CROSS JOIN LATERAL (
            SELECT
                count(*) AS row_count,
                count(*) FILTER (
                    WHERE result.retrieval_status_code = 'UNRESOLVED'
                      AND result.candidate_rank IS NULL
                      AND result.concept_id IS NULL
                      AND result.retrieval_tier_code IS NULL
                      AND result.signal_ledger @>
                          '[{"signal_code":"unresolved"}]'::JSONB
                ) AS unresolved_row_count
            FROM ml.retrieve_deterministic_candidates(
                hard_negative.query_text,
                'en',
                'normalization.en_v1',
                'D',
                5,
                0.80::REAL
            ) AS result
        ) AS observed
        WHERE observed.row_count <> 1
           OR observed.unresolved_row_count <> 1
    ) OR (
        SELECT count(*)
        FROM ml.retrieve_deterministic_candidates(
            'zzqv xylophonic meteor alloy',
            'en',
            'normalization.en_v1',
            'D',
            5,
            1::REAL
        )
    ) <> 1 OR NOT EXISTS (
        SELECT 1
        FROM ml.retrieve_deterministic_candidates(
            'zzqv xylophonic meteor alloy',
            'en',
            'normalization.en_v1',
            'D',
            5,
            1::REAL
        ) AS result
        WHERE result.retrieval_status_code = 'UNRESOLVED'
          AND result.candidate_rank IS NULL
          AND result.concept_id IS NULL
          AND result.matched_expression_id IS NULL
          AND jsonb_array_length(result.signal_ledger) = 1
          AND result.signal_ledger @>
              '[{"signal_code":"unresolved"}]'::JSONB
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_explicit_unresolved_ck',
            MESSAGE = 'a hard negative did not produce exactly one explicit UNRESOLVED row';
    END IF;

    RAISE NOTICE 'ROUND2B_RETRIEVAL_SEED_CONTRACT_PASS=true';
END;
$round2b_retrieval_seed_contract$;

\echo ROUND2B_RETRIEVAL_SEED_ASSERTIONS=true

\else

\echo ROUND2B_RETRIEVAL_SEED_ASSERTIONS_SKIPPED=true

\endif

COMMIT;

\echo ROUND2B_RETRIEVAL_PASS=true
