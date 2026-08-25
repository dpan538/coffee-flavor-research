\set ON_ERROR_STOP on

BEGIN;

INSERT INTO audit.round3f_checkpoint (
    checkpoint_key, source_sha,
    expected_canonical_concept_count,
    expected_active_sensory_attribute_count,
    text_first_lexical_candidate_intentional,
    canonical_ontology_frozen,
    ranking_model_trained, adaptive_policy_trained,
    deep_learning_model_run, embedding_baseline_run, pgvector_required,
    real_human_collection_performed, real_observation_count,
    question_user_validated_count,
    question_information_gain_estimated_count,
    product_frontend_modified
)
VALUES (
    'coffee-sensory-kb-v0-round3f',
    'eee5c140fb6d3ab61f87dfe472601aac2e4c39cf',
    130, 92, TRUE, TRUE,
    FALSE, FALSE, FALSE, FALSE, FALSE,
    FALSE, 0, 0, 0, FALSE
);

INSERT INTO corpus.association_range (
    range_key, display_name, research_definition,
    lifecycle_status, support_scope, evidence_key,
    independent_evidence_family_count
)
VALUES
    (
        'floral-tea', 'Floral / tea',
        'Research anchor for overlapping floral and tea references already used in governed question-language research; not a sensory family or ontology category.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:family_direction;round3e:floral_tea_reference', 1
    ),
    (
        'fruit', 'Fruit',
        'Research anchor for fruit-associated expressions already used in governed question-language research; not a complete fruit taxonomy.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:fruit_direction;round3e:fruit_region_reference', 1
    ),
    (
        'cocoa-nut-caramel', 'Cocoa / nut / caramel',
        'Research anchor for overlapping cocoa, nut and browned-sweet references already used in governed question-language research.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:roast_direction;round3e:cocoa_nut_reference,browned_sweet_reference', 1
    ),
    (
        'roast-spice-smoke', 'Roast / spice / smoke',
        'Research anchor for roast-associated references already used in governed question-language research; roast context and sensory response remain distinct.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:roast_direction;round3e:roast_smoke_reference', 1
    ),
    (
        'sweet-associated', 'Sweet-associated character',
        'Research anchor for perceived sweetness and sweet-associated references without implying measured sugar or ingredient identity.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:sweet_direction;round3e:sweetness_character', 1
    ),
    (
        'acidity-character', 'Acidity character',
        'Research anchor for acidity-language distinctions without treating bright, juicy, citrus-like, sour or clean as equivalent constructs.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:bright_acidity;round3e:acidity_character', 1
    ),
    (
        'texture-body-drying', 'Texture / body / drying',
        'Research anchor for tactile and structure references without collapsing body, viscosity, astringency, finish or sediment.',
        'CANDIDATE', 'GOVERNED_QUESTION_ANCHOR',
        'calibration.question:texture_direction;round3e:texture_character', 1
    );

WITH membership_seed(
    membership_key, range_key, normalized_text,
    membership_role, evidence_key, provenance_path
) AS (
    VALUES
        (
            'membership.floral-tea.floral', 'floral-tea',
            'floral',
            'ANCHOR', 'question_option.family_direction.en.floral_tea',
            'calibration.question_option -> governed floral/tea range -> preserved normalized expression'
        ),
        (
            'membership.floral-tea.jasmine', 'floral-tea',
            'jasmine',
            'CONTEXTUAL_ASSOCIATE', 'round3e.floral_tea_reference.en',
            'calibration.question_research_candidate answer option -> governed floral/tea range -> preserved normalized expression'
        ),
        (
            'membership.floral-tea.black-tea', 'floral-tea',
            'black tea',
            'CONTEXTUAL_ASSOCIATE', 'round3e.tea_style_reference.en',
            'calibration.question_research_candidate answer option -> governed floral/tea range -> preserved normalized expression'
        ),
        (
            'membership.fruit.berry', 'fruit',
            'berry',
            'ANCHOR', 'question_option.fruit_direction.en.berry',
            'calibration.question_option -> governed fruit range -> preserved normalized expression'
        ),
        (
            'membership.fruit.citrus', 'fruit',
            'citrus',
            'FREQUENT_ASSOCIATE', 'question_option.fruit_direction.en.citrus',
            'calibration.question_option -> governed fruit range -> preserved normalized expression'
        ),
        (
            'membership.cocoa-nut-caramel.cocoa', 'cocoa-nut-caramel',
            'cocoa',
            'ANCHOR', 'round3e.cocoa_nut_reference.en',
            'calibration.question_research_candidate answer option -> governed cocoa/nut/caramel range -> preserved normalized expression'
        ),
        (
            'membership.cocoa-nut-caramel.dark-chocolate', 'cocoa-nut-caramel',
            'dark chocolate',
            'CONTEXTUAL_ASSOCIATE', 'round3e.cocoa_nut_reference.en',
            'calibration.question_research_candidate answer option -> governed cocoa/nut/caramel range -> preserved normalized expression'
        ),
        (
            'membership.cocoa-nut-caramel.caramel', 'cocoa-nut-caramel',
            'caramel',
            'ANCHOR', 'round3e.browned_sweet_reference.en',
            'calibration.question_research_candidate region and answer option -> governed cocoa/nut/caramel range -> preserved normalized expression'
        ),
        (
            'membership.cocoa-nut-caramel.honey', 'cocoa-nut-caramel',
            'honey',
            'AMBIGUOUS', 'round3e.browned_sweet_reference.en',
            'calibration.question_research_candidate region and answer option -> governed cocoa/nut/caramel range -> preserved normalized expression'
        ),
        (
            'membership.roast-spice-smoke.smoke', 'roast-spice-smoke',
            'smoke',
            'ANCHOR', 'question_option.roast_direction.en.smoke_char',
            'calibration.question_option -> governed roast/spice/smoke range -> preserved normalized expression'
        ),
        (
            'membership.sweet-associated.caramel', 'sweet-associated',
            'caramel',
            'ANCHOR', 'question_option.sweet_direction.en.caramel',
            'calibration.question_option -> governed sweet-associated range -> preserved normalized expression'
        ),
        (
            'membership.sweet-associated.honey', 'sweet-associated',
            'honey',
            'CONTEXTUAL_ASSOCIATE', 'question_option.sweet_direction.en.honey',
            'calibration.question_option -> governed sweet-associated range -> preserved normalized expression'
        ),
        (
            'membership.acidity-character.citrus', 'acidity-character',
            'citrus',
            'CONTEXTUAL_ASSOCIATE', 'question_option.bright_acidity.en.citrus_bright',
            'calibration.question_option -> governed acidity-character range -> preserved normalized expression'
        ),
        (
            'membership.acidity-character.juicy', 'acidity-character',
            'juicy',
            'AMBIGUOUS', 'question_option.bright_acidity.en.juicy',
            'calibration.question_option -> governed acidity-character range -> preserved normalized expression'
        ),
        (
            'membership.texture-body-drying.juicy', 'texture-body-drying',
            'juicy',
            'AMBIGUOUS', 'question_option.texture_direction.en.juicy_silky',
            'calibration.question_option -> governed texture/body/drying range -> preserved normalized expression'
        ),
        (
            'membership.texture-body-drying.silky', 'texture-body-drying',
            'silky',
            'ANCHOR', 'question_option.texture_direction.en.juicy_silky',
            'calibration.question_option -> governed texture/body/drying range -> preserved normalized expression'
        )
)
INSERT INTO corpus.association_range_membership (
    membership_key, association_range_id, normalized_expression_id,
    membership_role, lifecycle_status, evidence_basis,
    evidence_key, provenance_path
)
SELECT
    seed.membership_key, range.association_range_id,
    expression.normalized_expression_id,
    seed.membership_role, 'CANDIDATE',
    'EXISTING_GOVERNED_QUESTION_REGION',
    seed.evidence_key, seed.provenance_path
FROM membership_seed AS seed
JOIN corpus.association_range AS range ON range.range_key = seed.range_key
JOIN corpus.normalized_expression AS expression
  ON expression.normalized_text = seed.normalized_text
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id = expression.normalization_pipeline_id
 AND pipeline.normalization_pipeline_key = 'normalization.en_v1';

WITH membership_seed(
    membership_key, range_key, member_text, member_language_code,
    membership_role, evidence_key, provenance_path
) AS (
    VALUES
        (
            'membership.floral-tea.fragrant-tea', 'floral-tea',
            'fragrant tea', 'en', 'PERIPHERAL_CANDIDATE',
            'question_option.family_direction.en.floral_tea',
            'exact calibration.question_option text -> governed floral/tea range -> intentionally text-only candidate'
        ),
        (
            'membership.texture-body-drying.tea-like',
            'texture-body-drying', 'tea-like', 'en', 'AMBIGUOUS',
            'question_option.texture_direction.en.light_tea',
            'exact calibration.question_option text -> governed texture/body/drying range -> intentionally text-only candidate'
        )
)
INSERT INTO corpus.association_range_membership (
    membership_key, association_range_id, member_text,
    member_language_code, membership_role, lifecycle_status,
    evidence_basis, evidence_key, provenance_path
)
SELECT
    seed.membership_key, range.association_range_id,
    seed.member_text, seed.member_language_code, seed.membership_role,
    'CANDIDATE', 'EXISTING_GOVERNED_QUESTION_REGION',
    seed.evidence_key, seed.provenance_path
FROM membership_seed AS seed
JOIN corpus.association_range AS range ON range.range_key = seed.range_key;

WITH target_seed(
    target_key, logical_question_code, question_source, range_key,
    relationship_role, direction_kind, option_scope, evidence_key
) AS (
    VALUES
        ('question-range.family-direction.floral-tea', 'family_direction', 'ROUND3C_QUESTION_BANK', 'floral-tea', 'QUESTION_DISTINGUISHES_RANGES', 'CROSS_RANGE', 'floral_tea', 'question_option.family_direction.*.floral_tea'),
        ('question-range.family-direction.fruit', 'family_direction', 'ROUND3C_QUESTION_BANK', 'fruit', 'QUESTION_DISTINGUISHES_RANGES', 'CROSS_RANGE', 'fruit_bright', 'question_option.family_direction.*.fruit_bright'),
        ('question-range.family-direction.cocoa-nut-caramel', 'family_direction', 'ROUND3C_QUESTION_BANK', 'cocoa-nut-caramel', 'QUESTION_DISTINGUISHES_RANGES', 'CROSS_RANGE', 'cocoa_roast', 'question_option.family_direction.*.cocoa_roast'),
        ('question-range.family-direction.roast-spice-smoke', 'family_direction', 'ROUND3C_QUESTION_BANK', 'roast-spice-smoke', 'QUESTION_DISTINGUISHES_RANGES', 'CROSS_RANGE', 'cocoa_roast', 'question_option.family_direction.*.cocoa_roast'),
        ('question-range.fruit-direction.fruit', 'fruit_direction', 'ROUND3C_QUESTION_BANK', 'fruit', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'calibration.question:fruit_direction'),
        ('question-range.sweet-direction.sweet-associated', 'sweet_direction', 'ROUND3C_QUESTION_BANK', 'sweet-associated', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'calibration.question:sweet_direction'),
        ('question-range.roast-direction.roast-spice-smoke', 'roast_direction', 'ROUND3C_QUESTION_BANK', 'roast-spice-smoke', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'calibration.question:roast_direction'),
        ('question-range.bright-acidity.acidity-character', 'bright_acidity', 'ROUND3C_QUESTION_BANK', 'acidity-character', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'calibration.question:bright_acidity'),
        ('question-range.texture-direction.texture-body-drying', 'texture_direction', 'ROUND3C_QUESTION_BANK', 'texture-body-drying', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'calibration.question:texture_direction'),
        ('question-range.floral-tea-reference.floral-tea', 'floral_tea_reference', 'ROUND3E_RESEARCH_CANDIDATE', 'floral-tea', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.floral_tea_reference.*'),
        ('question-range.tea-style-reference.floral-tea', 'tea_style_reference', 'ROUND3E_RESEARCH_CANDIDATE', 'floral-tea', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.tea_style_reference.*'),
        ('question-range.fruit-region-reference.fruit', 'fruit_region_reference', 'ROUND3E_RESEARCH_CANDIDATE', 'fruit', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.fruit_region_reference.*'),
        ('question-range.cocoa-nut-reference.cocoa-nut-caramel', 'cocoa_nut_reference', 'ROUND3E_RESEARCH_CANDIDATE', 'cocoa-nut-caramel', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.cocoa_nut_reference.*'),
        ('question-range.browned-sweet-reference.cocoa-nut-caramel', 'browned_sweet_reference', 'ROUND3E_RESEARCH_CANDIDATE', 'cocoa-nut-caramel', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.browned_sweet_reference.*'),
        ('question-range.roast-smoke-reference.roast-spice-smoke', 'roast_smoke_reference', 'ROUND3E_RESEARCH_CANDIDATE', 'roast-spice-smoke', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.roast_smoke_reference.*'),
        ('question-range.sweetness-character.sweet-associated', 'sweetness_character', 'ROUND3E_RESEARCH_CANDIDATE', 'sweet-associated', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.sweetness_character.*'),
        ('question-range.acidity-character.acidity-character', 'acidity_character', 'ROUND3E_RESEARCH_CANDIDATE', 'acidity-character', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.acidity_character.*'),
        ('question-range.texture-character.texture-body-drying', 'texture_character', 'ROUND3E_RESEARCH_CANDIDATE', 'texture-body-drying', 'QUESTION_TARGETS_RANGE', 'WITHIN_RANGE', NULL, 'round3e.texture_character.*')
)
INSERT INTO calibration.question_range_target (
    question_range_target_key, logical_question_code, question_source,
    association_range_id, relationship_role, direction_kind, option_scope,
    evidence_key, context_eligibility_status, user_validation_status,
    information_gain_status
)
SELECT
    seed.target_key, seed.logical_question_code, seed.question_source,
    range.association_range_id, seed.relationship_role,
    seed.direction_kind, seed.option_scope, seed.evidence_key,
    'HYPOTHESIZED', 'NOT_USER_VALIDATED', 'NOT_ESTIMABLE'
FROM target_seed AS seed
JOIN corpus.association_range AS range ON range.range_key = seed.range_key;

WITH semantic_seed(
    relationship_key, relationship_domain, subject_entity_type,
    predicate, object_entity_type, database_representation, current_status
) AS (
    VALUES
        ('lexical.preferred-lexicalization', 'LEXICAL', 'kb.lexical_expression', 'preferred_lexicalization_of', 'kb.concept', 'kb.lexicalization(mapping_type=preferred_label)', 'ENFORCED'),
        ('lexical.orthographic-variant', 'LEXICAL', 'kb.lexical_expression', 'orthographic_variant_of', 'kb.concept', 'kb.lexicalization(mapping_type=approved_variant)', 'ENFORCED'),
        ('lexical.language-variant', 'LEXICAL', 'text expression', 'language_variant_candidate_of', 'text expression', 'text-first research records; no bilingual-equivalence edge', 'DOCUMENTED_BOUNDARY'),
        ('lexical.source-local-expression', 'LEXICAL', 'source record', 'contains_source_local_expression', 'preserved expression', 'corpus.observation_expression and corpus.external_expression_occurrence', 'ENFORCED'),
        ('lexical.candidate-mapping', 'LEXICAL', 'normalized expression', 'candidate_lexical_mapping', 'text mapping', 'corpus.lexical_mapping_candidate', 'ENFORCED'),
        ('canonical.broader-than', 'CANONICAL_ONTOLOGY', 'kb.concept', 'broader_than', 'kb.concept', 'kb.concept_relation', 'ENFORCED'),
        ('canonical.sensory-neighbour', 'CANONICAL_ONTOLOGY', 'kb.concept', 'sensory_neighbour', 'kb.concept', 'kb.concept_relation', 'ENFORCED'),
        ('canonical.composite-has-component', 'CANONICAL_ONTOLOGY', 'kb.concept', 'composite_has_component', 'kb.concept', 'kb.concept_relation', 'ENFORCED'),
        ('canonical.consumer-reference-for', 'CANONICAL_ONTOLOGY', 'kb.concept', 'consumer_reference_for', 'kb.concept', 'kb.concept_relation', 'ENFORCED'),
        ('canonical.modifies', 'CANONICAL_ONTOLOGY', 'kb.concept', 'modifies', 'kb.concept', 'kb.concept_relation', 'ENFORCED'),
        ('canonical.contrasts-with', 'CANONICAL_ONTOLOGY', 'kb.concept', 'contrasts_with', 'kb.concept', 'kb.concept_relation', 'ENFORCED'),
        ('empirical.co-occurs-with', 'SOURCE_LOCAL_EMPIRICAL', 'normalized expression', 'co_occurs_with', 'normalized expression', 'corpus.normalized_expression_pair_measurement', 'ENFORCED'),
        ('empirical.co-selected-with', 'SOURCE_LOCAL_EMPIRICAL', 'source-local response', 'co_selected_with', 'source-local response', 'no admitted Round 3F instances', 'UNRESOLVED'),
        ('empirical.same-source-record', 'SOURCE_LOCAL_EMPIRICAL', 'source-local expression', 'appears_in_same_source_record', 'source-local expression', 'corpus observation links; derived only within snapshot', 'AUDITED'),
        ('empirical.source-defined-grouping', 'SOURCE_LOCAL_EMPIRICAL', 'source-local expression', 'source_defined_grouping', 'source-local grouping', 'corpus.association_measurement(method=SOURCE_DEFINED_GROUPING)', 'ENFORCED'),
        ('empirical.source-local-association', 'SOURCE_LOCAL_EMPIRICAL', 'source-local expression', 'source_local_association', 'source-local expression', 'method-specific source-local measurement only', 'DOCUMENTED_BOUNDARY'),
        ('range.anchor', 'ASSOCIATION_RANGE', 'expression/concept/text candidate', 'anchor_of_range', 'corpus.association_range', 'corpus.association_range_membership(role=ANCHOR)', 'ENFORCED'),
        ('range.frequent-associate', 'ASSOCIATION_RANGE', 'expression/concept/text candidate', 'frequent_associate_in_range', 'corpus.association_range', 'corpus.association_range_membership(role=FREQUENT_ASSOCIATE)', 'ENFORCED'),
        ('range.contextual-associate', 'ASSOCIATION_RANGE', 'expression/concept/text candidate', 'contextual_associate_in_range', 'corpus.association_range', 'corpus.association_range_membership(role=CONTEXTUAL_ASSOCIATE)', 'ENFORCED'),
        ('range.peripheral-candidate', 'ASSOCIATION_RANGE', 'expression/concept/text candidate', 'peripheral_candidate_in_range', 'corpus.association_range', 'corpus.association_range_membership(role=PERIPHERAL_CANDIDATE)', 'ENFORCED'),
        ('range.ambiguous', 'ASSOCIATION_RANGE', 'expression/concept/text candidate', 'ambiguous_in_range', 'corpus.association_range', 'corpus.association_range_membership(role=AMBIGUOUS)', 'ENFORCED'),
        ('question.targets-range', 'QUESTION', 'logical question', 'question_targets_range', 'corpus.association_range', 'calibration.question_range_target', 'ENFORCED'),
        ('question.option-indicates-range', 'QUESTION', 'question option', 'option_indicates_range', 'corpus.association_range', 'calibration.question_range_target(option_scope)', 'ENFORCED'),
        ('question.eligible-for-context', 'QUESTION', 'logical question', 'question_eligible_for_context', 'context hypothesis', 'calibration.question_eligibility and JSONB candidate eligibility', 'AUDITED'),
        ('question.distinguishes-ranges', 'QUESTION', 'logical question', 'question_distinguishes_ranges', 'corpus.association_range', 'calibration.question_range_target', 'ENFORCED'),
        ('evidence.supported-by-source', 'EVIDENCE', 'canonical assertion', 'supported_by_source', 'versioned source/dataset', 'evidence support tables', 'ENFORCED'),
        ('evidence.derived-from-snapshot', 'EVIDENCE', 'derived record', 'derived_from_snapshot', 'immutable snapshot', 'snapshot foreign keys and stable keys', 'ENFORCED'),
        ('evidence.measured-by-method', 'EVIDENCE', 'quantitative observation', 'measured_by_method', 'method/configuration', 'method-specific measurement tables', 'ENFORCED'),
        ('evidence.reviewed-under-protocol', 'EVIDENCE', 'candidate/assertion', 'reviewed_under_protocol', 'review receipt/protocol', 'audit review and approval tables', 'AUDITED'),
        ('governance.candidate-promoted-by-review', 'GOVERNANCE', 'candidate', 'candidate_promoted_by_review', 'canonical assertion', 'audit.promotion_event plus required approval', 'ENFORCED'),
        ('governance.superseded-by', 'GOVERNANCE', 'historical assertion', 'superseded_by', 'replacement assertion', 'lifecycle/replacement fields', 'ENFORCED'),
        ('governance.rejected-by', 'GOVERNANCE', 'candidate', 'rejected_by', 'review decision', 'audit review tables', 'AUDITED'),
        ('governance.requires-evidence', 'GOVERNANCE', 'candidate/assertion', 'requires_evidence', 'evidence gate', 'constraints, triggers and curation policy', 'ENFORCED'),
        ('governance.forbidden-from-promotion', 'GOVERNANCE', 'source-local/candidate record', 'forbidden_from_promotion', 'canonical assertion', 'promotion triggers and audit.forbidden_inference_rule', 'ENFORCED')
)
INSERT INTO audit.relationship_semantic_rule (
    relationship_key, relationship_domain, subject_entity_type,
    predicate, object_entity_type, cardinality, directionality, symmetry,
    transitivity, exclusivity, evidence_requirement, provenance_path,
    lifecycle, computational_role, allowed_inference, forbidden_inference,
    database_representation, validation_method, negative_test, current_status
)
SELECT
    seed.relationship_key, seed.relationship_domain,
    seed.subject_entity_type, seed.predicate, seed.object_entity_type,
    'zero-to-many unless a named database key narrows cardinality',
    CASE WHEN seed.predicate IN (
        'sensory_neighbour', 'contrasts_with', 'co_occurs_with',
        'co_selected_with', 'appears_in_same_source_record'
    ) THEN 'UNDIRECTED' ELSE 'DIRECTED' END,
    CASE WHEN seed.predicate IN (
        'sensory_neighbour', 'contrasts_with', 'co_occurs_with',
        'co_selected_with', 'appears_in_same_source_record'
    ) THEN 'SYMMETRIC' ELSE 'NOT_SYMMETRIC' END,
    CASE WHEN seed.predicate = 'broader_than'
        THEN 'TRANSITIVE_CLOSURE_ALLOWED_FOR_SAME_CANONICAL_TYPE_ONLY'
        ELSE 'NOT_TRANSITIVE' END,
    'NON_EXCLUSIVE',
    'Named evidence basis or explicit documented boundary is required.',
    seed.database_representation,
    'Lifecycle is local to the represented assertion and never promotes another domain automatically.',
    'Retrieval, audit or candidate research only as stated by the relationship domain.',
    'Only the stored relation and its documented read model may be asserted.',
    'No cross-domain truth, synonymy, hierarchy, probability, bilingual equivalence or promotion may be inferred.',
    seed.database_representation,
    'PostgreSQL constraint/trigger, audit query, CI gate or documented curation review as registered.',
    'Round 3F negative suite or explicit NOT_APPLICABLE boundary.',
    seed.current_status
FROM semantic_seed AS seed;

INSERT INTO audit.forbidden_inference_rule (
    forbidden_inference_key, source_fact, forbidden_claim, rule_text,
    enforcement_layer, constraint_name, negative_test
)
VALUES
    ('forbidden.range-to-synonym', 'RANGE_COMEMBERSHIP', 'SYNONYM', 'same range does not imply synonymy', 'CI_GATE', 'round3f_range_not_synonym_ck', 'range_copresence_to_synonym'),
    ('forbidden.range-to-hierarchy', 'RANGE_COMEMBERSHIP', 'HIERARCHY', 'same range does not imply an IS_A or broader/narrower hierarchy', 'CI_GATE', 'round3f_range_not_hierarchy_ck', 'range_copresence_to_hierarchy'),
    ('forbidden.range-to-neighbour', 'RANGE_COMEMBERSHIP', 'SENSORY_NEIGHBOUR', 'same range does not imply canonical sensory-neighbour status', 'CI_GATE', 'round3f_range_not_neighbour_ck', 'range_copresence_to_sensory_neighbour'),
    ('forbidden.cooccurrence-to-neighbour', 'COOCCURRENCE', 'SENSORY_NEIGHBOUR', 'source-local co-occurrence does not imply sensory similarity or neighbour status', 'CI_GATE', 'round3f_cooccurrence_not_neighbour_ck', 'cooccurrence_to_sensory_neighbour'),
    ('forbidden.frequency-to-validity', 'FREQUENCY', 'SENSORY_VALIDITY', 'frequency does not establish sensory validity', 'CURATION_POLICY', 'round3f_frequency_not_sensory_validity_ck', 'frequency_to_sensory_validity'),
    ('forbidden.frequency-to-promotion', 'FREQUENCY', 'CANONICAL_PROMOTION', 'frequency does not permit canonical promotion', 'POSTGRESQL_TRIGGER', 'round3f_frequency_not_promotion_ck', 'recurrent_expression_automatic_promotion'),
    ('forbidden.membership-to-probability', 'RANGE_MEMBERSHIP', 'PROBABILITY', 'range membership is not a numeric probability', 'POSTGRESQL_CONSTRAINT', 'round3f_membership_not_probability_ck', 'numeric_probability_membership'),
    ('forbidden.question-to-validation', 'QUESTION_TARGET', 'VALIDATED_QUESTION', 'a question target does not establish ordinary-user validation', 'POSTGRESQL_CONSTRAINT', 'round3f_question_target_not_validation_ck', 'question_target_to_validated'),
    ('forbidden.translation-to-equivalence', 'LITERAL_TRANSLATION', 'BILINGUAL_EQUIVALENCE', 'literal translation does not establish bilingual experiential equivalence', 'CI_GATE', 'round3f_translation_not_equivalence_ck', 'literal_translation_to_bilingual_equivalence'),
    ('forbidden.absence-to-negative', 'SOURCE_ABSENCE', 'NEGATIVE_ASSOCIATION', 'absence of observation is not negative or contrast evidence', 'CI_GATE', 'round3f_absence_not_negative_ck', 'source_absence_to_negative_relation'),
    ('forbidden.text-to-canonical', 'TEXT_CANDIDATE', 'MANDATORY_CANONICAL_CONCEPT', 'a text-first candidate need not resolve to one canonical concept', 'POSTGRESQL_CONSTRAINT', 'round3f_text_not_mandatory_concept_ck', 'unresolved_candidate_forced_to_concept'),
    ('forbidden.one-range-to-exclusive', 'ONE_RANGE_MEMBERSHIP', 'EXCLUSIVE_MEMBERSHIP', 'one observed membership does not make range membership exclusive', 'POSTGRESQL_CONSTRAINT', 'round3f_one_range_not_exclusive_ck', 'exclusive_range_membership'),
    ('forbidden.context-to-effect', 'CONTEXT_ELIGIBILITY', 'MEASURED_CONTEXT_EFFECT', 'context eligibility is a hypothesis until observations support an effect', 'CI_GATE', 'round3f_context_not_measured_effect_ck', 'context_eligibility_to_measured_effect'),
    ('forbidden.pair-chain-to-transitive', 'PAIRWISE_ASSOCIATION_CHAIN', 'TRANSITIVE_ASSOCIATION', 'two pairwise association observations do not create a transitive edge', 'CI_GATE', 'round3f_association_not_transitive_ck', 'pairwise_chain_to_transitive_association');

WITH constraint_seed(
    constraint_key, scope, category, rule, rationale,
    enforcement_layer, negative_test, current_status, introduced_round
) AS (
    VALUES
        ('constraint.core.primary-keys', 'all governed base tables', 'PK', 'Every governed entity row has a primary key.', 'Stable identity and duplicate rejection.', 'POSTGRESQL_CONSTRAINT', 'duplicate primary-key fixtures across round suites', 'ENFORCED', 'PRE_3F'),
        ('constraint.core.foreign-keys', 'normalized cross-table references', 'FK', 'Typed references resolve to existing governed rows.', 'Referential integrity must not depend on prose.', 'POSTGRESQL_CONSTRAINT', 'invalid foreign-key fixtures across round suites', 'ENFORCED', 'PRE_3F'),
        ('constraint.core.candidate-keys', 'stable *_key and *_code fields', 'CANDIDATE_KEY', 'Stable logical keys are unique.', 'Rebuild comparison relies on stable identities.', 'POSTGRESQL_CONSTRAINT', 'duplicate stable-key fixtures across round suites', 'ENFORCED', 'PRE_3F'),
        ('constraint.core.checks', 'typed value domains and row semantics', 'CHECK', 'Controlled values and row-local invariants are checked.', 'Invalid local states should fail at write time.', 'POSTGRESQL_CONSTRAINT', 'row-domain fixtures across round suites', 'ENFORCED', 'PRE_3F'),
        ('constraint.core.deferred-support', 'active canonical assertions', 'DEFERRED_TRIGGER', 'Required support may be inserted in the same transaction but must exist at constraint check.', 'Support reciprocity is multi-row.', 'POSTGRESQL_TRIGGER', 'canonical support negative fixtures', 'ENFORCED', 'PRE_3F'),
        ('constraint.license.public-export', 'rights-governed source data', 'PUBLIC_EXPORT_GATE', 'Public export requires recorded rights and privacy permission.', 'Visibility is not reuse permission.', 'POSTGRESQL_TRIGGER', 'public_export_of_blocked_raw_text', 'ENFORCED', 'PRE_3F'),
        ('constraint.privacy.no-direct-identifiers', 'external and calibration capture', 'PII_GATE', 'Direct participant identifiers are rejected from governed evidence JSON.', 'Research evidence must preserve privacy boundaries.', 'POSTGRESQL_CONSTRAINT', 'direct_participant_identifier', 'ENFORCED', 'PRE_3F'),
        ('constraint.model.round3e-input-prohibited', 'Round 3E source-local snapshots', 'MODEL_RUN_PROHIBITION', 'Round 3E external datasets cannot enter ml.model_run.', 'Evidence expansion was not a training round.', 'POSTGRESQL_TRIGGER', 'model_output_despite_training_prohibition', 'ENFORCED', 'PRE_3F'),
        ('constraint.ci.generated-clean', 'active generated artifacts', 'CI_ARTIFACT_GATE', 'Generation runs twice, hashes match, formatting passes and Git remains clean.', 'Committed generated outputs must be reproducible.', 'CI_GATE', 'artifact contract test', 'ENFORCED', 'PRE_3F'),
        ('constraint.ci.two-rebuilds', 'all migrations and deterministic seeds', 'REPRODUCIBILITY_GATE', 'Two clean PostgreSQL 17 rebuilds must have identical inventories.', 'Order and environment drift must be visible.', 'CI_GATE', 'db/scripts/rebuild-twice.sh', 'ENFORCED', 'PRE_3F'),
        ('constraint.lexical.text-first-preserved', 'corpus.lexical_mapping_candidate', 'TEXT_FIRST_BOUNDARY', 'candidate_mapping, evidence_key, mapping_scope and ambiguity_note remain text and no concept FK is mandatory.', 'Composite and ambiguous language cannot be losslessly forced into one concept.', 'POSTGRESQL_CONSTRAINT', 'unresolved_candidate_forced_to_concept', 'ENFORCED', '3F'),
        ('constraint.range.non-ontological', 'corpus.association_range', 'NON_INFERENCE', 'Ranges have no canonical ontology effect.', 'Research grouping is not ontology truth.', 'POSTGRESQL_CONSTRAINT', 'range_copresence_to_hierarchy', 'ENFORCED', '3F'),
        ('constraint.range.overlap-permitted', 'corpus.association_range_membership', 'CARDINALITY', 'A subject may have zero, one or multiple memberships.', 'Overlap and absence are valid states.', 'POSTGRESQL_CONSTRAINT', 'exclusive_range_membership', 'ENFORCED', '3F'),
        ('constraint.range.subject-xor', 'corpus.association_range_membership', 'CHECK', 'A membership preserves exactly one subject representation.', 'Text candidates must not be silently accompanied by a canonical concept.', 'POSTGRESQL_CONSTRAINT', 'unresolved_candidate_forced_to_concept', 'ENFORCED', '3F'),
        ('constraint.range.evidence-required', 'corpus.association_range_membership', 'EVIDENCE_GATE', 'Every membership records an allowed evidence basis, key and provenance path.', 'World knowledge and LLM completion are inadmissible.', 'POSTGRESQL_CONSTRAINT', 'membership_without_evidence', 'ENFORCED', '3F'),
        ('constraint.range.non-probability', 'corpus.association_range_membership', 'NON_INFERENCE', 'Membership semantics are non-probabilistic and no universal weight exists.', 'Methods have incompatible value semantics.', 'POSTGRESQL_CONSTRAINT', 'numeric_probability_membership', 'ENFORCED', '3F'),
        ('constraint.range.non-transitive', 'association-range research', 'NON_INFERENCE', 'Range membership and pairwise association do not create transitive edges.', 'Association is context-local.', 'CI_GATE', 'pairwise_chain_to_transitive_association', 'ENFORCED', '3F'),
        ('constraint.range.source-local-gate', 'corpus.association_range', 'LIFECYCLE_GATE', 'SOURCE_LOCAL_SUPPORTED requires one named evidence family and SOURCE_LOCAL scope.', 'Source-local support must remain labeled.', 'POSTGRESQL_TRIGGER', 'source_local_range_mislabeled_cross_source', 'ENFORCED', '3F'),
        ('constraint.range.cross-source-gate', 'corpus.association_range', 'LIFECYCLE_GATE', 'Cross-source support requires two independent families or a formal grouping.', 'Derived tables and duplicate files are not independent evidence.', 'POSTGRESQL_TRIGGER', 'source_local_range_mislabeled_cross_source', 'ENFORCED', '3F'),
        ('constraint.range.calibration-review', 'corpus.association_range', 'PROMOTION_GATE', 'ACTIVE_FOR_CALIBRATION requires explicit review evidence.', 'Range activation is a human governance decision.', 'POSTGRESQL_TRIGGER', 'range_active_without_review', 'ENFORCED', '3F'),
        ('constraint.measurement.method-specific', 'corpus.association_measurement', 'MEASUREMENT_BOUNDARY', 'Every value retains method, snapshot, counts, semantics and configuration.', 'PPMI, Jaccard and fuzzy membership are not interchangeable.', 'POSTGRESQL_CONSTRAINT', 'measurement_without_method_configuration', 'ENFORCED', '3F'),
        ('constraint.question.target-not-validation', 'calibration.question_range_target', 'NON_INFERENCE', 'Question targeting remains not user validated.', 'Design intent is not comprehension evidence.', 'POSTGRESQL_CONSTRAINT', 'question_target_to_validated', 'ENFORCED', '3F'),
        ('constraint.question.no-information-gain', 'calibration.question_range_target', 'OBSERVATION_GATE', 'Information gain remains NOT_ESTIMABLE.', 'There are zero real observations.', 'POSTGRESQL_CONSTRAINT', 'information_gain_without_observations', 'ENFORCED', '3F'),
        ('constraint.question.context-hypothesis', 'calibration.question_range_target', 'NON_INFERENCE', 'Context eligibility remains HYPOTHESIZED.', 'Eligibility is not a measured context effect.', 'POSTGRESQL_CONSTRAINT', 'context_eligibility_to_measured_effect', 'ENFORCED', '3F'),
        ('constraint.translation.no-equivalence', 'English and Simplified Chinese candidates', 'BILINGUAL_BOUNDARY', 'Literal translation does not establish experiential equivalence or shared range membership.', 'Polysemy and register differ across languages.', 'CURATION_POLICY', 'literal_translation_to_bilingual_equivalence', 'ENFORCED', '3F'),
        ('constraint.absence.no-negative', 'source and range inventories', 'NON_INFERENCE', 'Absence is not contrast or negative association evidence.', 'Unobserved does not mean impossible.', 'CI_GATE', 'source_absence_to_negative_relation', 'ENFORCED', '3F'),
        ('constraint.canonical.count-freeze', 'kb.concept', 'CANONICAL_FREEZE', 'Total concepts remain 130 and active sensory attributes remain 92.', 'Round 3F is not an ontology-expansion round.', 'AUDIT_QUERY', 'canonical_inventory_exact', 'ENFORCED', '3F'),
        ('constraint.canonical.no-mutation', 'kb.concept', 'CANONICAL_FREEZE', 'Insert, update and delete are blocked while the Round 3F checkpoint is active.', 'No add, split, merge, retype or deprecation is authorized.', 'POSTGRESQL_TRIGGER', 'new_canonical_concept_from_phrase;split_existing_descriptor', 'ENFORCED', '3F'),
        ('constraint.canonical.relation-types-freeze', 'ref.relation_type', 'CANONICAL_FREEZE', 'Canonical relation types cannot be added or reinterpreted in Round 3F.', 'Clusters must not become new canonical predicates.', 'POSTGRESQL_TRIGGER', 'new_canonical_relation_type', 'ENFORCED', '3F'),
        ('constraint.frequency.no-promotion', 'recurrent expressions', 'PROMOTION_GATE', 'Frequency cannot automatically create a lexicalization or concept.', 'Common wording is not canonical sensory truth.', 'POSTGRESQL_TRIGGER', 'recurrent_expression_automatic_promotion', 'ENFORCED', '3F'),
        ('constraint.round3f.no-model-run', 'ml.model_run', 'MODEL_RUN_PROHIBITION', 'Round 3F relationship or range data cannot be used in a model run.', 'Round 3F is architecture and constraint research only.', 'POSTGRESQL_TRIGGER', 'round3f_data_in_model_run', 'ENFORCED', '3F'),
        ('constraint.future-round.delta-required', 'substantive rounds after 3F', 'CI_ARTIFACT_GATE', 'Each future substantive round must include RELATIONSHIP_CONSTRAINT_DELTA.md.', 'Relationship semantics and constraints need explicit change receipts.', 'CURATION_POLICY', 'future round packaging review', 'DOCUMENTED_ONLY', '3F'),
        ('constraint.relationship.provenance', 'registered relationship instances', 'EVIDENCE_GATE', 'Admitted relationship instances expose a provenance path or documented boundary.', 'Counts without traceability do not improve quality.', 'AUDIT_QUERY', 'relationship_provenance_coverage', 'ENFORCED', '3F'),
        ('constraint.graph.no-tree-completion', 'ontology and association research', 'CURATION_BOUNDARY', 'No balanced tree, placeholder node or invented sibling is created for completeness.', 'Sparse overlapping structure is epistemically valid.', 'CURATION_POLICY', 'canonical freeze and review audit', 'ENFORCED', '3F'),
        ('constraint.additional-range.review', 'additional range proposals', 'PROMOTION_GATE', 'Additional project-level ranges remain in the candidate register pending evidence and user review.', 'Visual balance is not evidence.', 'CURATION_POLICY', 'additional range candidate register review', 'DOCUMENTED_ONLY', '3F')
)
INSERT INTO audit.constraint_registry_entry (
    constraint_key, scope, constraint_category, rule, rationale,
    enforcement_layer, failure_behavior, override_policy,
    promotion_requirement, negative_test, current_status, introduced_round
)
SELECT
    seed.constraint_key, seed.scope, seed.category, seed.rule, seed.rationale,
    seed.enforcement_layer,
    CASE WHEN seed.enforcement_layer IN (
        'POSTGRESQL_CONSTRAINT', 'POSTGRESQL_TRIGGER', 'CI_GATE', 'AUDIT_QUERY'
    ) THEN 'Reject the write or fail validation/CI.'
    ELSE 'Retain UNRESOLVED and stop promotion.' END,
    CASE WHEN seed.introduced_round = '3F'
        THEN 'Only a future explicit, evidence-backed forward change may override; never ad hoc.'
        ELSE 'Follow the existing owning-round governance and forward-migration policy.' END,
    'Explicit evidence and the named review gate are required; no automatic promotion path exists.',
    seed.negative_test, seed.current_status, seed.introduced_round
FROM constraint_seed AS seed;

COMMIT;
