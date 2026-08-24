\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Independently authored, deterministic smoke data for schema and retrieval
-- tests only. This is not a complete ontology, a coffee standard, an empirical
-- dataset, or a source of intrinsic descriptor scores.

BEGIN;

INSERT INTO ref.lifecycle_status (
    lifecycle_status_code,
    display_name,
    description
)
VALUES
    ('candidate', 'Candidate', 'A project proposal awaiting canonical acceptance.'),
    ('active', 'Active', 'A current canonical assertion or identity.'),
    ('deprecated', 'Deprecated', 'A retained historical record that is no longer current.'),
    ('merged', 'Merged', 'A retained historical identity resolved to a replacement concept.'),
    ('rejected', 'Rejected', 'A retained proposal that was not accepted as canonical knowledge.');

INSERT INTO ref.concept_type (
    concept_type_code,
    display_name,
    description
)
VALUES
    ('sensory_attribute', 'Sensory attribute', 'A descriptive sensory-language concept.'),
    ('composite_reference', 'Composite reference', 'A familiar composite used as a sensory-language reference.'),
    ('qualifier', 'Qualifier', 'A contextual modifier that is not assumed to be a sensory substance or score.'),
    ('affective_term', 'Affective term', 'An evaluative or hedonic concept kept separate from descriptive sensation.'),
    ('process_entity', 'Process entity', 'A production or preparation process kept separate from perceived character.'),
    ('category', 'Category', 'A language-neutral conceptual region used for typed hierarchy.');

INSERT INTO ref.relation_type (
    relation_type_code,
    display_name,
    description,
    is_directional,
    is_symmetric,
    is_hierarchical,
    closure_is_transitive,
    allows_self,
    evidence_required
)
VALUES
    (
        'broader_than',
        'Broader than',
        'The subject is a broader conceptual region than the object.',
        TRUE, FALSE, TRUE, TRUE, FALSE, TRUE
    ),
    (
        'sensory_neighbour',
        'Sensory neighbour',
        'The two concepts have a symmetric, explicitly supported sensory-neighbour assertion.',
        FALSE, TRUE, FALSE, FALSE, FALSE, TRUE
    ),
    (
        'composite_has_component',
        'Composite has component',
        'The subject composite reference includes the object as a named component for the assertion context.',
        TRUE, FALSE, FALSE, FALSE, FALSE, TRUE
    ),
    (
        'consumer_reference_for',
        'Consumer reference for',
        'The subject is a familiar consumer reference used to communicate the object concept without asserting synonymy.',
        TRUE, FALSE, FALSE, FALSE, FALSE, TRUE
    ),
    (
        'modifies',
        'Modifies',
        'The subject qualifier modifies the interpretation of the object in an explicitly supported context.',
        TRUE, FALSE, FALSE, FALSE, FALSE, TRUE
    ),
    (
        'contrasts_with',
        'Contrasts with',
        'The concepts form a symmetric, explicitly supported contrast in the assertion context.',
        FALSE, TRUE, FALSE, FALSE, FALSE, TRUE
    );

INSERT INTO ref.mapping_type (
    mapping_type_code,
    display_name,
    description,
    is_preferred,
    is_approved_variant,
    allows_polysemy,
    retrieval_precedence
)
VALUES
    (
        'preferred_label',
        'Preferred label',
        'The preferred project-authored expression for a concept and language.',
        TRUE, FALSE, FALSE, 1
    ),
    (
        'approved_variant',
        'Approved variant',
        'An approved spelling or wording variant considered after preferred labels.',
        FALSE, TRUE, FALSE, 2
    ),
    (
        'polysemous_usage',
        'Polysemous usage',
        'A context-sensitive interpretation that deliberately permits one expression to map to more than one concept.',
        FALSE, FALSE, TRUE, 3
    );

INSERT INTO ref.language_tag (
    language_tag_code,
    display_name,
    description
)
VALUES
    ('en', 'English', 'English lexical expressions.'),
    ('zh-Hans', 'Simplified Chinese', 'Simplified Chinese lexical expressions using a BCP 47-style tag.');

INSERT INTO ref.signal_domain (
    signal_domain_code,
    display_name,
    description
)
VALUES
    ('perceptual', 'Perceptual', 'Signals produced by a declared sensory observation or perceptual protocol.'),
    ('linguistic_semantic', 'Linguistic semantic', 'Signals about language-form or meaning similarity, not sensory distance.'),
    ('corpus_cooccurrence', 'Corpus co-occurrence', 'Signals derived from expression co-occurrence in a declared corpus.'),
    ('structural', 'Structural', 'Signals derived from declared graph or record structure.'),
    ('model_derived', 'Model derived', 'Signals emitted by a versioned computational model or run.'),
    ('epistemic_governance', 'Epistemic or governance', 'Evidence, confidence, or review signals that are not sensory weights.');

INSERT INTO ref.review_decision (
    review_decision_code,
    display_name,
    description,
    permits_promotion
)
VALUES
    ('approved', 'Approved', 'The reviewer approves the reviewed proposal for an explicit promotion decision.', TRUE),
    ('rejected', 'Rejected', 'The reviewer does not approve the reviewed proposal.', FALSE),
    ('changes_requested', 'Changes requested', 'The reviewer requests revision before another decision.', FALSE),
    ('abstained', 'Abstained', 'The reviewer records no approval or rejection decision.', FALSE);

INSERT INTO ref.provenance_scope (
    provenance_scope_code,
    display_name,
    description,
    requires_source_support
)
VALUES
    (
        'project_authored',
        'Project authored',
        'Independently authored project material; support records may identify its fixed project source version.',
        FALSE
    ),
    (
        'external',
        'External',
        'An assertion derived from an external source and requiring versioned source support while active.',
        TRUE
    );

INSERT INTO ref.resolution_status (
    resolution_status_code,
    display_name,
    description,
    is_resolved
)
VALUES
    ('pending', 'Pending', 'Resolution has not yet been completed.', FALSE),
    ('resolved', 'Resolved', 'Resolution identifies an explicit canonical lexicalization.', TRUE),
    ('unresolved', 'Unresolved', 'No safe canonical lexicalization is asserted.', FALSE);

INSERT INTO ref.model_run_status (
    model_run_status_code,
    display_name,
    description,
    is_terminal,
    is_successful
)
VALUES
    ('queued', 'Queued', 'The versioned model run has not started.', FALSE, FALSE),
    ('running', 'Running', 'The versioned model run is in progress.', FALSE, FALSE),
    ('completed', 'Completed', 'The run completed successfully without any automatic canonical promotion.', TRUE, TRUE),
    ('failed', 'Failed', 'The run ended unsuccessfully.', TRUE, FALSE),
    ('cancelled', 'Cancelled', 'The run was cancelled before successful completion.', TRUE, FALSE);

INSERT INTO ref.candidate_status (
    candidate_status_code,
    display_name,
    description,
    is_reviewable,
    is_terminal
)
VALUES
    ('proposed', 'Proposed', 'A generated candidate available for independent review.', TRUE, FALSE),
    ('under_review', 'Under review', 'A candidate currently subject to independent review.', TRUE, FALSE),
    ('accepted', 'Accepted', 'A reviewed candidate accepted as a proposal; canonical promotion remains a separate event.', FALSE, TRUE),
    ('rejected', 'Rejected', 'A reviewed candidate rejected without deleting its history.', FALSE, TRUE),
    ('superseded', 'Superseded', 'A retained candidate replaced by later inference or review work.', FALSE, TRUE);

INSERT INTO ref.access_class (
    access_class_code,
    display_name,
    description,
    permits_raw_text
)
VALUES
    ('public', 'Public', 'Raw text may be stored and may be exported only when the full rights policy also permits it.', TRUE),
    ('restricted', 'Restricted', 'Raw text may be stored for authorized testing but is excluded from public export.', TRUE),
    ('metadata_only', 'Metadata only', 'Only metadata may be retained; raw source text is not permitted.', FALSE);

INSERT INTO ref.rights_status (
    rights_status_code,
    display_name,
    description,
    is_verified
)
VALUES
    ('verified', 'Verified', 'The rights decision was explicitly checked for the identified source version.', TRUE),
    ('unknown', 'Unknown', 'Reuse rights have not been verified and must not be inferred.', FALSE);

INSERT INTO kb.sensory_dimension (
    dimension_key,
    lifecycle_status_code,
    name,
    measurement_semantics,
    unit
)
VALUES
    (
        'taste.sweetness',
        'active',
        'Sweetness',
        'A future protocol-specific sample measurement of perceived sweetness; not a permanent concept property.',
        NULL
    ),
    (
        'taste.sourness_acidity',
        'active',
        'Sourness/acidity',
        'A future protocol-specific sample measurement of perceived sourness or acidity; not a permanent concept property.',
        NULL
    ),
    (
        'taste.bitterness',
        'active',
        'Bitterness',
        'A future protocol-specific sample measurement of perceived bitterness; not a permanent concept property.',
        NULL
    ),
    (
        'taste.saltiness',
        'active',
        'Saltiness',
        'A future protocol-specific sample measurement of perceived saltiness; not a permanent concept property.',
        NULL
    ),
    (
        'tactile.body_fullness',
        'active',
        'Body/fullness',
        'A future protocol-specific sample measurement of perceived body or fullness; not a permanent concept property.',
        NULL
    ),
    (
        'tactile.drying_astringency',
        'active',
        'Drying/astringency',
        'A future protocol-specific sample measurement of perceived drying or astringency; not a permanent concept property.',
        NULL
    );

INSERT INTO evidence.license_policy (
    license_policy_key,
    access_class_code,
    rights_status_code,
    redistributable,
    derivative_work_allowed,
    commercial_use_allowed,
    machine_use_allowed,
    production_export_allowed,
    checked_on,
    notes
)
VALUES
    (
        'license.project_smoke_seed.public.v1',
        'public',
        'verified',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        DATE '2026-08-24',
        'Applies only to the independently authored test content in this seed under the repository documented content licence.'
    ),
    (
        'license.synthetic_fixture.restricted.v1',
        'restricted',
        'verified',
        FALSE,
        FALSE,
        FALSE,
        TRUE,
        FALSE,
        DATE '2026-08-24',
        'Deliberately restricted project-owned synthetic text used only to verify access filtering.'
    );

INSERT INTO evidence.source (
    source_key,
    title,
    creator,
    publisher,
    citation,
    doi,
    source_url,
    external_metadata
)
VALUES
    (
        'source.project_smoke_seed',
        'Coffee Sensory KB V0 Project Smoke Seed',
        'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project. Coffee Sensory KB V0 Project Smoke Seed. 2026-08-24.',
        NULL,
        NULL,
        '{"authorship":"project","fixture":true}'::JSONB
    ),
    (
        'source.synthetic_restricted_fixture',
        'Coffee Sensory KB V0 Restricted Synthetic Fixture',
        'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project',
        'Coffee Flavor Atlas project. Coffee Sensory KB V0 Restricted Synthetic Fixture. 2026-08-24.',
        NULL,
        NULL,
        '{"authorship":"project","fixture":true,"synthetic":true}'::JSONB
    );

INSERT INTO evidence.source_version (
    source_version_key,
    source_id,
    license_policy_id,
    version_label,
    published_on,
    retrieved_on,
    version_locator,
    external_metadata
)
SELECT
    seed.source_version_key,
    source.source_id,
    policy.license_policy_id,
    seed.version_label,
    DATE '2026-08-24',
    DATE '2026-08-24',
    seed.version_locator,
    seed.external_metadata
FROM (
    VALUES
        (
            'source_version.project_smoke_seed.2026-08-24',
            'source.project_smoke_seed',
            'license.project_smoke_seed.public.v1',
            '2026-08-24',
            'db/006_reference_seed.sql',
            '{"fixture":true}'::JSONB
        ),
        (
            'source_version.synthetic_restricted_fixture.2026-08-24',
            'source.synthetic_restricted_fixture',
            'license.synthetic_fixture.restricted.v1',
            '2026-08-24',
            'db/006_reference_seed.sql#restricted-synthetic-fixture',
            '{"fixture":true,"synthetic":true}'::JSONB
        )
) AS seed(
    source_version_key,
    source_key,
    license_policy_key,
    version_label,
    version_locator,
    external_metadata
)
JOIN evidence.source AS source
    ON source.source_key = seed.source_key
JOIN evidence.license_policy AS policy
    ON policy.license_policy_key = seed.license_policy_key;

INSERT INTO evidence.dataset (
    dataset_key,
    source_version_id,
    name,
    description,
    external_metadata
)
SELECT
    seed.dataset_key,
    source_version.source_version_id,
    seed.name,
    seed.description,
    seed.external_metadata
FROM (
    VALUES
        (
            'dataset.project_smoke_seed',
            'source_version.project_smoke_seed.2026-08-24',
            'Project smoke seed records',
            'Test-only project-authored rows used to validate schema and retrieval semantics; contains no empirical measurements.',
            '{"fixture":true,"empirical":false}'::JSONB
        ),
        (
            'dataset.synthetic_restricted_fixture',
            'source_version.synthetic_restricted_fixture.2026-08-24',
            'Restricted synthetic fixture records',
            'Test-only synthetic records used to verify restricted-text filtering; contains no empirical measurements.',
            '{"fixture":true,"empirical":false,"synthetic":true}'::JSONB
        )
) AS seed(dataset_key, source_version_key, name, description, external_metadata)
JOIN evidence.source_version AS source_version
    ON source_version.source_version_key = seed.source_version_key;

INSERT INTO evidence.statistical_method (
    method_key,
    name,
    description
)
VALUES
    (
        'method.test_fixture_direct_value',
        'Test-fixture direct value',
        'A test-only method identity for constraint checks; this seed creates no measurement using it.'
    ),
    (
        'method.test_fixture_rank_order',
        'Test-fixture rank order',
        'A test-only rank method identity for query checks; this seed creates no measurement using it.'
    );

INSERT INTO evidence.measurement_scale (
    scale_key,
    name,
    minimum_value,
    maximum_value,
    unit,
    value_semantics
)
VALUES
    (
        'scale.test_unit_interval',
        'Test unit interval',
        0,
        1,
        NULL,
        'A bounded zero-to-one test scale; no empirical interpretation is implied.'
    ),
    (
        'scale.test_zero_to_five',
        'Test zero-to-five',
        0,
        5,
        NULL,
        'A bounded zero-to-five test scale used only by constraint tests; no concept score is seeded.'
    );

INSERT INTO kb.concept (
    concept_key,
    concept_type_code,
    lifecycle_status_code,
    provenance_scope_code,
    replacement_concept_id,
    description,
    editorial_note
)
VALUES
    (
        'category.citrus', 'category', 'active', 'project_authored', NULL,
        'A project vocabulary region used to test a citrus hierarchy.',
        'This category is a compact smoke fixture, not a reproduction of any third-party flavor-wheel family.'
    ),
    (
        'sensory.grapefruit', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with grapefruit wording.',
        'Kept distinct from the narrower pink-grapefruit concept in this test ontology.'
    ),
    (
        'sensory.pink_grapefruit', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations specifically described with pink-grapefruit wording.',
        'This separate identity tests that a more specific expression is not collapsed into grapefruit.'
    ),
    (
        'sensory.bergamot', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with bergamot wording.',
        'It remains distinct from the Earl Grey composite consumer reference.'
    ),
    (
        'sensory.jasmine', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with jasmine wording.',
        'Its seeded neighbour relation is a test assertion, not a universal sensory distance.'
    ),
    (
        'sensory.black_tea', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with black-tea wording.',
        'This component identity stays separate from the Earl Grey composite reference.'
    ),
    (
        'composite.earl_grey', 'composite_reference', 'active', 'project_authored', NULL,
        'A project composite reference used to test component and consumer-reference relations.',
        'It is not a synonym or lexicalization of bergamot.'
    ),
    (
        'sensory.fermented_character', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for perceived fermented character.',
        'Perceived character is kept separate from the fermentation process entity.'
    ),
    (
        'process.fermentation', 'process_entity', 'active', 'project_authored', NULL,
        'A project process identity for fermentation metadata.',
        'A process record does not assert that a sample has fermented sensory character.'
    ),
    (
        'sensory.cardboard', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with cardboard wording.',
        'No desirability, cause, intensity, or prevalence is assigned by this fixture.'
    ),
    (
        'sensory.rubber', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with rubber wording.',
        'No desirability, cause, intensity, or prevalence is assigned by this fixture.'
    ),
    (
        'qualifier.bright', 'qualifier', 'candidate', 'project_authored', NULL,
        'A candidate project qualifier for context described as bright.',
        'No formula, acidity score, or intrinsic numeric meaning is assigned.'
    ),
    (
        'qualifier.clean', 'qualifier', 'candidate', 'project_authored', NULL,
        'A candidate project qualifier for context described as clean.',
        'The candidate does not encode an automatic quality judgment or score.'
    ),
    (
        'qualifier.juicy', 'qualifier', 'candidate', 'project_authored', NULL,
        'A candidate project qualifier for context described as juicy.',
        'The candidate has no intrinsic sample measurement or sensory coordinate.'
    ),
    (
        'qualifier.tea_like', 'qualifier', 'candidate', 'project_authored', NULL,
        'A candidate project qualifier for context described as tea-like.',
        'The qualifier remains distinct from the black-tea sensory concept.'
    ),
    (
        'qualifier.winey', 'qualifier', 'candidate', 'project_authored', NULL,
        'A candidate project qualifier for contextual use of winey wording.',
        'The shared winey expression is deliberately polysemous in this fixture.'
    ),
    (
        'sensory.wine_like_character', 'sensory_attribute', 'candidate', 'project_authored', NULL,
        'A candidate project sensory concept for a perceived wine-like character.',
        'This sensory interpretation remains distinct from the winey qualifier interpretation.'
    ),
    (
        'sensory.bitter', 'sensory_attribute', 'active', 'project_authored', NULL,
        'A project sensory-language concept for observations described with bitter wording.',
        'The concept has no permanent intensity value; sample measurements belong elsewhere.'
    ),
    (
        'affective.pleasant', 'affective_term', 'candidate', 'project_authored', NULL,
        'A candidate project affective concept for pleasant evaluation language.',
        'Affective judgment is kept separate from descriptive sensory concepts.'
    );

INSERT INTO kb.lexical_expression (
    expression_key,
    language_tag_code,
    expression_text,
    lifecycle_status_code
)
VALUES
    ('expression.en.citrus', 'en', 'citrus', 'active'),
    ('expression.en.grapefruit', 'en', 'grapefruit', 'active'),
    ('expression.en.pink_grapefruit', 'en', 'pink grapefruit', 'active'),
    ('expression.en.bergamot', 'en', 'bergamot', 'active'),
    ('expression.en.jasmine', 'en', 'jasmine', 'active'),
    ('expression.en.black_tea', 'en', 'black tea', 'active'),
    ('expression.en.earl_grey', 'en', 'Earl Grey', 'active'),
    ('expression.en.fermented', 'en', 'fermented', 'active'),
    ('expression.en.fermentation', 'en', 'fermentation', 'active'),
    ('expression.en.cardboard', 'en', 'cardboard', 'active'),
    ('expression.en.rubber', 'en', 'rubber', 'active'),
    ('expression.en.bright', 'en', 'bright', 'active'),
    ('expression.en.clean', 'en', 'clean', 'active'),
    ('expression.en.juicy', 'en', 'juicy', 'active'),
    ('expression.en.tea_like_hyphenated', 'en', 'tea-like', 'active'),
    ('expression.en.winey', 'en', 'winey', 'active'),
    ('expression.en.wine_like_character', 'en', 'wine-like character', 'active'),
    ('expression.en.bitter', 'en', 'bitter', 'active'),
    ('expression.en.pleasant', 'en', 'pleasant', 'active'),
    ('expression.en.pink_grapefruit_hyphenated', 'en', 'pink-grapefruit', 'active'),
    ('expression.en.earl_grey_tea', 'en', 'earl grey tea', 'active'),
    ('expression.en.tea_like_spaced', 'en', 'tea like', 'active'),
    ('expression.en.meteor_fruit', 'en', 'meteor fruit', 'active');

INSERT INTO kb.lexicalization (
    lexicalization_key,
    expression_id,
    concept_id,
    mapping_type_code,
    lifecycle_status_code,
    provenance_scope_code,
    valid_from,
    valid_until
)
SELECT
    seed.lexicalization_key,
    expression.expression_id,
    concept.concept_id,
    seed.mapping_type_code,
    'active',
    'project_authored',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL
FROM (
    VALUES
        ('lexicalization.en.citrus.preferred', 'expression.en.citrus', 'category.citrus', 'preferred_label'),
        ('lexicalization.en.grapefruit.preferred', 'expression.en.grapefruit', 'sensory.grapefruit', 'preferred_label'),
        ('lexicalization.en.pink_grapefruit.preferred', 'expression.en.pink_grapefruit', 'sensory.pink_grapefruit', 'preferred_label'),
        ('lexicalization.en.bergamot.preferred', 'expression.en.bergamot', 'sensory.bergamot', 'preferred_label'),
        ('lexicalization.en.jasmine.preferred', 'expression.en.jasmine', 'sensory.jasmine', 'preferred_label'),
        ('lexicalization.en.black_tea.preferred', 'expression.en.black_tea', 'sensory.black_tea', 'preferred_label'),
        ('lexicalization.en.earl_grey.preferred', 'expression.en.earl_grey', 'composite.earl_grey', 'preferred_label'),
        ('lexicalization.en.fermented_character.preferred', 'expression.en.fermented', 'sensory.fermented_character', 'preferred_label'),
        ('lexicalization.en.fermentation.preferred', 'expression.en.fermentation', 'process.fermentation', 'preferred_label'),
        ('lexicalization.en.cardboard.preferred', 'expression.en.cardboard', 'sensory.cardboard', 'preferred_label'),
        ('lexicalization.en.rubber.preferred', 'expression.en.rubber', 'sensory.rubber', 'preferred_label'),
        ('lexicalization.en.bright.preferred', 'expression.en.bright', 'qualifier.bright', 'preferred_label'),
        ('lexicalization.en.clean.preferred', 'expression.en.clean', 'qualifier.clean', 'preferred_label'),
        ('lexicalization.en.juicy.preferred', 'expression.en.juicy', 'qualifier.juicy', 'preferred_label'),
        ('lexicalization.en.tea_like.preferred', 'expression.en.tea_like_hyphenated', 'qualifier.tea_like', 'preferred_label'),
        ('lexicalization.en.winey.preferred', 'expression.en.winey', 'qualifier.winey', 'preferred_label'),
        ('lexicalization.en.wine_like_character.preferred', 'expression.en.wine_like_character', 'sensory.wine_like_character', 'preferred_label'),
        ('lexicalization.en.bitter.preferred', 'expression.en.bitter', 'sensory.bitter', 'preferred_label'),
        ('lexicalization.en.pleasant.preferred', 'expression.en.pleasant', 'affective.pleasant', 'preferred_label'),
        ('lexicalization.en.pink_grapefruit.approved_variant', 'expression.en.pink_grapefruit_hyphenated', 'sensory.pink_grapefruit', 'approved_variant'),
        ('lexicalization.en.earl_grey.approved_variant', 'expression.en.earl_grey_tea', 'composite.earl_grey', 'approved_variant'),
        ('lexicalization.en.tea_like.approved_variant', 'expression.en.tea_like_spaced', 'qualifier.tea_like', 'approved_variant'),
        ('lexicalization.en.winey.sensory_polysemous', 'expression.en.winey', 'sensory.wine_like_character', 'polysemous_usage')
) AS seed(lexicalization_key, expression_key, concept_key, mapping_type_code)
JOIN kb.lexical_expression AS expression
    ON expression.expression_key = seed.expression_key
JOIN kb.concept AS concept
    ON concept.concept_key = seed.concept_key;

INSERT INTO kb.concept_relation (
    relation_key,
    relation_type_code,
    subject_concept_id,
    object_concept_id,
    lifecycle_status_code,
    provenance_scope_code,
    valid_from,
    valid_until
)
SELECT
    seed.relation_key,
    seed.relation_type_code,
    subject.concept_id,
    object.concept_id,
    'active',
    'project_authored',
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    NULL
FROM (
    VALUES
        ('relation.citrus.broader_than.grapefruit', 'broader_than', 'category.citrus', 'sensory.grapefruit'),
        ('relation.grapefruit.broader_than.pink_grapefruit', 'broader_than', 'sensory.grapefruit', 'sensory.pink_grapefruit'),
        ('relation.earl_grey.consumer_reference_for.bergamot', 'consumer_reference_for', 'composite.earl_grey', 'sensory.bergamot'),
        ('relation.earl_grey.composite_has_component.black_tea', 'composite_has_component', 'composite.earl_grey', 'sensory.black_tea'),
        ('relation.bergamot.sensory_neighbour.jasmine', 'sensory_neighbour', 'sensory.bergamot', 'sensory.jasmine')
) AS seed(relation_key, relation_type_code, subject_concept_key, object_concept_key)
JOIN kb.concept AS subject
    ON subject.concept_key = seed.subject_concept_key
JOIN kb.concept AS object
    ON object.concept_key = seed.object_concept_key;

-- Stable support records make every smoke assertion traceable even though the
-- project-authored provenance class does not require support to commit.
INSERT INTO evidence.concept_support (
    concept_support_key,
    concept_id,
    source_version_id,
    dataset_id,
    locator,
    notes
)
SELECT
    'support.concept.' || concept.concept_key || '.project_smoke_seed',
    concept.concept_id,
    source_version.source_version_id,
    NULL,
    'db/006_reference_seed.sql#concepts',
    'Independently authored test-only concept scope.'
FROM kb.concept AS concept
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key = 'source_version.project_smoke_seed.2026-08-24';

INSERT INTO evidence.lexicalization_support (
    lexicalization_support_key,
    lexicalization_id,
    source_version_id,
    dataset_id,
    locator,
    notes
)
SELECT
    'support.' || lexicalization.lexicalization_key || '.project_smoke_seed',
    lexicalization.lexicalization_id,
    source_version.source_version_id,
    NULL,
    'db/006_reference_seed.sql#lexicalizations',
    'Independently authored test-only lexical mapping.'
FROM kb.lexicalization AS lexicalization
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key = 'source_version.project_smoke_seed.2026-08-24';

INSERT INTO evidence.relation_support (
    relation_support_key,
    concept_relation_id,
    source_version_id,
    dataset_id,
    locator,
    notes
)
SELECT
    'support.' || relation.relation_key || '.project_smoke_seed',
    relation.concept_relation_id,
    source_version.source_version_id,
    NULL,
    'db/006_reference_seed.sql#relations',
    'Independently authored test relation; not a universal empirical claim.'
FROM kb.concept_relation AS relation
JOIN ref.relation_type AS relation_type
    ON relation_type.relation_type_code = relation.relation_type_code
CROSS JOIN evidence.source_version AS source_version
WHERE relation.lifecycle_status_code = 'active'
  AND relation_type.evidence_required
  AND source_version.source_version_key = 'source_version.project_smoke_seed.2026-08-24';

INSERT INTO corpus.corpus (
    corpus_key,
    name,
    language_tag_code,
    description,
    capture_metadata
)
VALUES (
    'corpus.english_smoke_fixture',
    'English smoke fixture corpus',
    'en',
    'A tiny independently authored corpus containing one public and one restricted semantic test document.',
    '{"authorship":"project","fixture":true,"synthetic":true}'::JSONB
);

INSERT INTO corpus.captured_document (
    captured_document_key,
    corpus_id,
    source_version_id,
    external_document_key,
    captured_at,
    raw_text,
    capture_metadata
)
SELECT
    seed.captured_document_key,
    corpus.corpus_id,
    source_version.source_version_id,
    seed.external_document_key,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    seed.raw_text,
    seed.capture_metadata
FROM (
    VALUES
        (
            'document.public_pink_grapefruit_fixture',
            'source_version.project_smoke_seed.2026-08-24',
            'fixture-public-001',
            'The tasting note names pink grapefruit without assigning a score.',
            '{"fixture":true,"access_expectation":"public"}'::JSONB
        ),
        (
            'document.restricted_meteor_fruit_fixture',
            'source_version.synthetic_restricted_fixture.2026-08-24',
            'fixture-restricted-001',
            'The private synthetic note contains the invented phrase meteor fruit.',
            '{"fixture":true,"synthetic":true,"access_expectation":"restricted"}'::JSONB
        )
) AS seed(
    captured_document_key,
    source_version_key,
    external_document_key,
    raw_text,
    capture_metadata
)
CROSS JOIN corpus.corpus AS corpus
JOIN evidence.source_version AS source_version
    ON source_version.source_version_key = seed.source_version_key
WHERE corpus.corpus_key = 'corpus.english_smoke_fixture';

INSERT INTO corpus.raw_observation (
    raw_observation_key,
    captured_document_id,
    observation_text,
    character_start,
    character_end,
    observation_metadata
)
SELECT
    seed.raw_observation_key,
    document.captured_document_id,
    seed.observation_text,
    NULL,
    NULL,
    seed.observation_metadata
FROM (
    VALUES
        (
            'observation.public_pink_grapefruit',
            'document.public_pink_grapefruit_fixture',
            'pink grapefruit',
            '{"fixture":true,"resolution_expectation":"resolved"}'::JSONB
        ),
        (
            'observation.restricted_meteor_fruit',
            'document.restricted_meteor_fruit_fixture',
            'meteor fruit',
            '{"fixture":true,"synthetic":true,"resolution_expectation":"unresolved"}'::JSONB
        )
) AS seed(
    raw_observation_key,
    captured_document_key,
    observation_text,
    observation_metadata
)
JOIN corpus.captured_document AS document
    ON document.captured_document_key = seed.captured_document_key;

INSERT INTO corpus.observation_expression (
    observation_expression_key,
    raw_observation_id,
    expression_id,
    occurrence_ordinal
)
SELECT
    seed.observation_expression_key,
    observation.raw_observation_id,
    expression.expression_id,
    1
FROM (
    VALUES
        (
            'observation_expression.public_pink_grapefruit',
            'observation.public_pink_grapefruit',
            'expression.en.pink_grapefruit'
        ),
        (
            'observation_expression.restricted_meteor_fruit',
            'observation.restricted_meteor_fruit',
            'expression.en.meteor_fruit'
        )
) AS seed(observation_expression_key, raw_observation_key, expression_key)
JOIN corpus.raw_observation AS observation
    ON observation.raw_observation_key = seed.raw_observation_key
JOIN kb.lexical_expression AS expression
    ON expression.expression_key = seed.expression_key;

INSERT INTO corpus.observation_resolution (
    observation_resolution_key,
    observation_expression_id,
    resolution_status_code,
    lexicalization_id,
    resolution_note
)
SELECT
    seed.observation_resolution_key,
    observation_expression.observation_expression_id,
    seed.resolution_status_code,
    lexicalization.lexicalization_id,
    seed.resolution_note
FROM (
    VALUES
        (
            'observation_resolution.public_pink_grapefruit',
            'observation_expression.public_pink_grapefruit',
            'resolved',
            'lexicalization.en.pink_grapefruit.preferred',
            'The exact preferred expression resolves to the distinct pink-grapefruit concept.'
        ),
        (
            'observation_resolution.restricted_meteor_fruit',
            'observation_expression.restricted_meteor_fruit',
            'unresolved',
            NULL,
            'UNRESOLVED: no active canonical lexicalization is asserted for this invented fixture expression.'
        )
) AS seed(
    observation_resolution_key,
    observation_expression_key,
    resolution_status_code,
    lexicalization_key,
    resolution_note
)
JOIN corpus.observation_expression AS observation_expression
    ON observation_expression.observation_expression_key = seed.observation_expression_key
LEFT JOIN kb.lexicalization AS lexicalization
    ON lexicalization.lexicalization_key = seed.lexicalization_key;

COMMIT;
