\set ON_ERROR_STOP on
\pset pager off

-- Semantic smoke tests protect distinctions that relational validity alone
-- cannot express.  Every assertion is read-only against the lawful V0 seed.

BEGIN TRANSACTION READ ONLY;

SELECT
    concept_key,
    concept_type_code,
    lifecycle_status_code
FROM kb.concept
ORDER BY concept_key;

SELECT
    expression_text,
    resolution_status,
    concept_key,
    concept_type_code,
    mapping_type_code
FROM kb.v_lexical_resolution
WHERE normalized_text IN (
    'pink grapefruit',
    'earl grey',
    'bright',
    'tea-like',
    'winey',
    'meteor fruit',
    'fermented',
    'fermentation'
)
ORDER BY normalized_text, concept_key NULLS LAST;

DO $semantic_smoke$
DECLARE
    public_document_id BIGINT;
    restricted_document_id BIGINT;
BEGIN
    IF (SELECT count(*) FROM kb.concept) <> 19 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_seed_concept_count_ck',
            MESSAGE = 'semantic smoke: expected exactly 19 lawful seed concepts';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'sensory.pink_grapefruit'
          AND concept.concept_type_code = 'sensory_attribute'
          AND concept.lifecycle_status_code = 'active'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_pink_grapefruit_identity_ck',
            MESSAGE = 'semantic smoke: pink grapefruit must retain its own active sensory concept';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
        WHERE expression.language_tag_code = 'en'
          AND expression.normalized_text = 'pink grapefruit'
          AND mapping_type.is_preferred
          AND lexicalization.lifecycle_status_code = 'active'
          AND concept.concept_key = 'sensory.pink_grapefruit'
    ) OR EXISTS (
        SELECT 1
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
        WHERE expression.expression_key IN (
            'expression.en.pink_grapefruit',
            'expression.en.pink_grapefruit_hyphenated'
        )
          AND lexicalization.lifecycle_status_code = 'active'
          AND concept.concept_key = 'sensory.grapefruit'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_pink_grapefruit_not_collapsed_ck',
            MESSAGE = 'semantic smoke: pink grapefruit must resolve independently and never collapse into grapefruit';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept_relation AS relation
        JOIN kb.concept AS broader
          ON broader.concept_id = relation.subject_concept_id
        JOIN kb.concept AS narrower
          ON narrower.concept_id = relation.object_concept_id
        WHERE relation.relation_type_code = 'broader_than'
          AND relation.lifecycle_status_code = 'active'
          AND broader.concept_key = 'sensory.grapefruit'
          AND narrower.concept_key = 'sensory.pink_grapefruit'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_pink_grapefruit_hierarchy_ck',
            MESSAGE = 'semantic smoke: grapefruit must be broader than the distinct pink-grapefruit concept';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'composite.earl_grey'
          AND concept.concept_type_code = 'composite_reference'
          AND concept.lifecycle_status_code = 'active'
    ) OR EXISTS (
        SELECT 1
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
        WHERE expression.expression_key IN (
            'expression.en.earl_grey',
            'expression.en.earl_grey_tea'
        )
          AND lexicalization.lifecycle_status_code = 'active'
          AND concept.concept_key = 'sensory.bergamot'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_earl_grey_not_synonym_ck',
            MESSAGE = 'semantic smoke: Earl Grey must be a composite, not a bergamot lexical synonym';
    END IF;

    IF (
        SELECT count(*)
        FROM kb.concept_relation AS relation
        JOIN kb.concept AS subject
          ON subject.concept_id = relation.subject_concept_id
        JOIN kb.concept AS object
          ON object.concept_id = relation.object_concept_id
        WHERE subject.concept_key = 'composite.earl_grey'
          AND relation.lifecycle_status_code = 'active'
          AND (
                (
                    relation.relation_type_code = 'consumer_reference_for'
                    AND object.concept_key = 'sensory.bergamot'
                )
                OR (
                    relation.relation_type_code = 'composite_has_component'
                    AND object.concept_key = 'sensory.black_tea'
                )
              )
    ) <> 2 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_earl_grey_typed_relations_ck',
            MESSAGE = 'semantic smoke: Earl Grey must expose the reference and component relations';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS concept
        WHERE concept.concept_key = 'qualifier.bright'
          AND concept.concept_type_code = 'qualifier'
          AND concept.lifecycle_status_code = 'candidate'
    ) OR EXISTS (
        SELECT 1
        FROM information_schema.columns AS column_definition
        WHERE column_definition.table_schema = 'kb'
          AND column_definition.table_name = 'concept'
          AND column_definition.column_name ~ '(intensity|score|weight|acidity)'
    ) OR EXISTS (
        SELECT 1
        FROM evidence.concept_projection_value AS projection
        JOIN kb.concept AS concept
          ON concept.concept_id = projection.concept_id
        WHERE concept.concept_key = 'qualifier.bright'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_bright_qualifier_without_score_ck',
            MESSAGE = 'semantic smoke: bright must remain a candidate qualifier without an intrinsic numeric formula';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS tea_like
        CROSS JOIN kb.concept AS black_tea
        WHERE tea_like.concept_key = 'qualifier.tea_like'
          AND tea_like.concept_type_code = 'qualifier'
          AND black_tea.concept_key = 'sensory.black_tea'
          AND black_tea.concept_type_code = 'sensory_attribute'
          AND tea_like.concept_id <> black_tea.concept_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_tea_like_distinct_from_black_tea_ck',
            MESSAGE = 'semantic smoke: tea-like qualifier must remain distinct from black tea';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.v_lexical_resolution AS resolution
        WHERE resolution.expression_key = 'expression.en.meteor_fruit'
          AND resolution.resolution_status = 'UNRESOLVED'
          AND resolution.lexicalization_id IS NULL
          AND resolution.concept_id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        WHERE expression.expression_key = 'expression.en.meteor_fruit'
          AND lexicalization.lifecycle_status_code = 'active'
          AND lexicalization.valid_from <= CURRENT_TIMESTAMP
          AND (
                lexicalization.valid_until IS NULL
                OR lexicalization.valid_until > CURRENT_TIMESTAMP
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_meteor_fruit_unresolved_ck',
            MESSAGE = 'semantic smoke: meteor fruit must remain explicitly unresolved';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM kb.concept AS sensory
        CROSS JOIN kb.concept AS process
        WHERE sensory.concept_key = 'sensory.fermented_character'
          AND sensory.concept_type_code = 'sensory_attribute'
          AND process.concept_key = 'process.fermentation'
          AND process.concept_type_code = 'process_entity'
          AND sensory.concept_id <> process.concept_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_fermented_process_separation_ck',
            MESSAGE = 'semantic smoke: fermented character must remain distinct from fermentation process';
    END IF;

    IF (
        SELECT count(DISTINCT concept.concept_id)
        FROM kb.lexical_expression AS expression
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
        WHERE expression.expression_key = 'expression.en.winey'
          AND lexicalization.lifecycle_status_code = 'active'
          AND concept.concept_key IN (
              'qualifier.winey',
              'sensory.wine_like_character'
          )
    ) <> 2 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_winey_polysemy_ck',
            MESSAGE = 'semantic smoke: winey must retain both qualifier and sensory interpretations';
    END IF;

    SELECT document.captured_document_id
    INTO STRICT public_document_id
    FROM corpus.captured_document AS document
    WHERE document.captured_document_key = 'document.public_pink_grapefruit_fixture';

    SELECT document.captured_document_id
    INTO STRICT restricted_document_id
    FROM corpus.captured_document AS document
    WHERE document.captured_document_key = 'document.restricted_meteor_fruit_fixture';

    IF NOT EXISTS (
        SELECT 1
        FROM corpus.v_distributable_observations AS distributable
        WHERE distributable.captured_document_id = public_document_id
          AND distributable.raw_observation_key = 'observation.public_pink_grapefruit'
    ) OR EXISTS (
        SELECT 1
        FROM corpus.v_distributable_observations AS distributable
        WHERE distributable.captured_document_id = restricted_document_id
           OR distributable.observation_text ILIKE '%meteor fruit%'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_distributable_rights_gate_ck',
            MESSAGE = 'semantic smoke: distributable observations must include public content and exclude restricted content';
    END IF;

    IF (
        SELECT
            (SELECT count(*) FROM evidence.empirical_pair_measurement)
          + (SELECT count(*) FROM evidence.reference_calibration)
          + (SELECT count(*) FROM corpus.expression_cooccurrence_measurement)
          + (SELECT count(*) FROM ml.candidate_signal)
    ) <> 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_seed_has_no_empirical_scores_ck',
            MESSAGE = 'semantic smoke: the lawful seed must not masquerade as empirical numeric evidence';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM ref.language_tag
        WHERE language_tag_code = 'zh-Hans'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_zh_hans_supported_ck',
            MESSAGE = 'semantic smoke: schema must support future zh-Hans expressions';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM pg_catalog.pg_extension
        WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'semantic_pgvector_not_required_ck',
            MESSAGE = 'semantic smoke: pgvector must not be a V0 dependency';
    END IF;

    RAISE NOTICE 'SEMANTIC_SMOKE_PASS=true';
END
$semantic_smoke$;

COMMIT;

\echo SEMANTIC_SMOKE_PASS=true
