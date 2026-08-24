\set ON_ERROR_STOP on
\pset pager off

BEGIN TRANSACTION READ ONLY;

DO $round3a_semantic_contract$
DECLARE
    failed_check_count BIGINT;
BEGIN
    SELECT count(*) INTO failed_check_count
    FROM audit.run_round3a_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0;

    IF failed_check_count <> 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_validation_contract_ck',
            MESSAGE = 'Round 3A validation contract reported one or more violations';
    END IF;

    IF (SELECT metric_value FROM context.v_context_coverage
        WHERE metric_key = 'PREPARATION_FAMILY_COUNT') <> 8
       OR (SELECT metric_value FROM context.v_context_coverage
           WHERE metric_key = 'PREPARATION_LEAF_COUNT') <> 22
       OR (SELECT metric_value FROM context.v_context_coverage
           WHERE metric_key = 'RECOMMENDED_C0_TOP_LEVEL_CHOICE_COUNT') <> 8
       OR (SELECT metric_value FROM context.v_context_coverage
           WHERE metric_key = 'RECOMMENDED_USER_ROAST_LEVEL_COUNT') <> 5 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_taxonomy_receipt_ck',
            MESSAGE = 'Round 3A preparation or roast receipt differs from the reviewed V0 recommendation';
    END IF;

    IF (SELECT metric_value FROM context.v_context_coverage
        WHERE metric_key = 'CURRENT_CORPUS_PREPARATION_COVERAGE') <> 0
       OR (SELECT metric_value FROM context.v_context_coverage
           WHERE metric_key = 'CURRENT_CORPUS_ROAST_COVERAGE') <> 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_no_context_inference_ck',
            MESSAGE = 'Round 2B context coverage must remain zero until explicit context metadata is acquired';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM context.v_preparation_taxonomy
        WHERE preparation_concept_key = 'preparation.method.aeropress'
          AND direct_parent_count = 2
          AND direct_parent_keys @> ARRAY[
              'preparation.family.hybrid',
              'preparation.family.immersion'
          ]::TEXT[]
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_aeropress_polyhierarchy_ck',
            MESSAGE = 'AeroPress must retain explicit immersion and hybrid parents';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM context.preparation_relation AS relation
        JOIN context.preparation_concept AS subject
          ON subject.preparation_concept_id = relation.subject_preparation_concept_id
        JOIN context.preparation_concept AS object
          ON object.preparation_concept_id = relation.object_preparation_concept_id
        WHERE relation.context_relation_type_code = 'related_to'
          AND subject.preparation_concept_key = 'preparation.beverage.americano'
          AND object.preparation_concept_key = 'preparation.beverage.long_black'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_diluted_espresso_distinction_ck',
            MESSAGE = 'Americano and long black must be related but not merged';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM context.preparation_relation AS relation
        JOIN context.preparation_concept AS subject
          ON subject.preparation_concept_id = relation.subject_preparation_concept_id
        JOIN context.preparation_concept AS object
          ON object.preparation_concept_id = relation.object_preparation_concept_id
        WHERE subject.preparation_concept_key = 'preparation.beverage.long_black'
          AND object.preparation_concept_key LIKE 'preparation.%cold%'
           OR object.preparation_concept_key = 'preparation.beverage.long_black'
              AND subject.preparation_concept_key LIKE 'preparation.%cold%'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_long_black_cold_brew_separation_ck',
            MESSAGE = 'Long black must not be classified as cold brew';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM context.v_preparation_taxonomy AS flat_white
        CROSS JOIN context.v_preparation_taxonomy AS latte
        WHERE flat_white.preparation_concept_key =
              'preparation.beverage.flat_white'
          AND latte.preparation_concept_key = 'preparation.beverage.latte'
          AND flat_white.preparation_concept_id <>
              latte.preparation_concept_id
          AND flat_white.direct_parent_keys = latte.direct_parent_keys
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_milk_style_sibling_ck',
            MESSAGE = 'Flat white and latte must remain distinct siblings under espresso plus milk';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM context.v_unresolved_context_labels
        WHERE context_domain = 'roast'
          AND expression_text IN (
              'City roast', 'Nordic roast', 'filter roast',
              'espresso roast', 'omniroast'
          )
        GROUP BY context_domain
        HAVING count(*) <> 5
    ) OR NOT EXISTS (
        SELECT 1
        FROM context.v_unresolved_context_labels
        WHERE context_domain = 'roast' AND expression_text = 'Nordic roast'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_roast_label_abstention_ck',
            MESSAGE = 'Trade and brew-intent labels must remain unresolved rather than acquire invented darkness mappings';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM context.beverage_addition_type
        WHERE beverage_addition_type_key = 'addition.flavored_syrup'
          AND is_strong_flavour_interference
    ) OR EXISTS (
        SELECT 1 FROM kb.concept WHERE concept_key = 'addition.flavored_syrup'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3a_additive_boundary_ck',
            MESSAGE = 'Flavored syrup must remain strong-interference beverage context, not canonical sensory knowledge';
    END IF;

    RAISE NOTICE 'ROUND3A_SEMANTIC_VALIDATION_PASS=true';
END;
$round3a_semantic_contract$;

SELECT * FROM context.v_context_coverage ORDER BY metric_key;
SELECT
    preparation_concept_key, preferred_label, direct_parent_count,
    direct_parent_keys, direct_child_count, support_count
FROM context.v_preparation_taxonomy
ORDER BY preparation_concept_key;
SELECT * FROM context.v_roast_normalization
ORDER BY source_roast_scheme_key, source_ordinal_position NULLS LAST,
         source_roast_category_key;

ROLLBACK;

\echo ROUND3A_SEMANTIC_TEST_PASS=true
