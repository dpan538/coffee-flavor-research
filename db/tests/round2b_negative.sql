\set ON_ERROR_STOP on
\pset pager off

-- Round 2B failure-path tests. All fixtures and attempted mutations are
-- transaction-local. The helper requires the exact SQLSTATE and, when given,
-- the exact PostgreSQL constraint diagnostic.

BEGIN;

CREATE FUNCTION pg_temp.expect_round2b_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round2b_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 2B negative statement unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR (
                expected_constraint IS NOT NULL
                AND actual_constraint IS DISTINCT FROM expected_constraint
              ) THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2B_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key,
            actual_state,
            COALESCE(actual_constraint, '<none>');
    END;
END;
$expect_round2b_failure$;

-- Three deliberately distinct acquisition decisions share one project-owned
-- source version. The policy domain is the acquisition source, not a roaster
-- publisher domain.
INSERT INTO corpus.source_policy_review (
    source_policy_review_key,
    source_version_id,
    license_policy_id,
    domain,
    corpus_source_decision_code,
    robots_status_code,
    robots_locator,
    terms_status_code,
    terms_locator,
    corpus_access_method_code,
    copyright_status_code,
    document_metadata_allowed,
    raw_retention_allowed,
    derived_terms_allowed,
    derived_terms_redistribution_allowed,
    raw_redistribution_allowed,
    automated_acquisition_allowed,
    commercial_use_implications,
    checked_at,
    notes
)
SELECT
    policy_seed.policy_key,
    source_version.source_version_id,
    source_version.license_policy_id,
    policy_seed.domain,
    policy_seed.decision_code,
    'not_applicable',
    NULL,
    'not_applicable',
    NULL,
    'repository_fixture',
    'project_authored',
    policy_seed.metadata_allowed,
    FALSE,
    policy_seed.derived_allowed,
    policy_seed.derived_redistribution_allowed,
    FALSE,
    FALSE,
    'Transaction-local project fixture; no commercial-source permission is inferred.',
    policy_seed.checked_at,
    'Negative-test acquisition policy fixture.'
FROM (
    VALUES
        (
            'negative.round2b.policy.derived'::TEXT,
            'derived.fixture.invalid',
            'allow_derived_terms',
            TRUE,
            TRUE,
            TRUE,
            TIMESTAMPTZ '2026-08-24 01:00:00+00'
        ),
        (
            'negative.round2b.policy.metadata',
            'metadata.fixture.invalid',
            'allow_metadata_only',
            TRUE,
            FALSE,
            FALSE,
            TIMESTAMPTZ '2026-08-24 01:01:00+00'
        ),
        (
            'negative.round2b.policy.blocked',
            'blocked.fixture.invalid',
            'blocked',
            FALSE,
            FALSE,
            FALSE,
            TIMESTAMPTZ '2026-08-24 01:02:00+00'
        )
) AS policy_seed(
    policy_key,
    domain,
    decision_code,
    metadata_allowed,
    derived_allowed,
    derived_redistribution_allowed,
    checked_at
)
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key =
     'source_version.project_smoke_seed.2026-08-24';

SELECT pg_temp.expect_round2b_failure(
    'manual_only_automation',
    $sql$
        INSERT INTO corpus.source_policy_review (
            source_policy_review_key, source_version_id, license_policy_id,
            domain, corpus_source_decision_code, robots_status_code,
            robots_locator, terms_status_code, terms_locator,
            corpus_access_method_code, copyright_status_code,
            document_metadata_allowed, raw_retention_allowed,
            derived_terms_allowed, derived_terms_redistribution_allowed,
            raw_redistribution_allowed, automated_acquisition_allowed,
            commercial_use_implications, checked_at, notes
        )
        SELECT
            'negative.round2b.policy.manual_automation',
            source_version_id,
            license_policy_id,
            'manual.fixture.invalid',
            'manual_only',
            'allows',
            'https://manual.fixture.invalid/robots.txt',
            'permits_machine_analysis',
            'https://manual.fixture.invalid/terms',
            'automated_http',
            'project_authored',
            TRUE, FALSE, FALSE, FALSE, FALSE, TRUE,
            'Negative fixture.',
            TIMESTAMPTZ '2026-08-24 01:03:00+00',
            'A MANUAL_ONLY decision must reject automated acquisition.'
        FROM evidence.source_version
        WHERE source_version_key =
              'source_version.project_smoke_seed.2026-08-24'
    $sql$,
    '23514',
    'source_policy_review_automation_ck'
);

INSERT INTO corpus.industry_publisher (
    industry_publisher_key,
    source_policy_review_id,
    external_publisher_key,
    publisher_name,
    domain,
    roaster_country_code,
    notes
)
SELECT
    publisher_seed.publisher_key,
    policy.source_policy_review_id,
    publisher_seed.external_key,
    publisher_seed.publisher_name,
    publisher_seed.domain,
    NULL,
    'Transaction-local publisher fixture.'
FROM (
    VALUES
        ('negative.round2b.publisher.derived'::TEXT, 'negative-derived', 'Derived Fixture Roaster', 'roaster-derived.fixture.invalid', 'negative.round2b.policy.derived'),
        ('negative.round2b.publisher.metadata', 'negative-metadata', 'Metadata Fixture Roaster', 'roaster-metadata.fixture.invalid', 'negative.round2b.policy.metadata'),
        ('negative.round2b.publisher.blocked', 'negative-blocked', 'Blocked Fixture Roaster', 'roaster-blocked.fixture.invalid', 'negative.round2b.policy.blocked')
) AS publisher_seed(
    publisher_key,
    external_key,
    publisher_name,
    domain,
    policy_key
)
JOIN corpus.source_policy_review AS policy
  ON policy.source_policy_review_key = publisher_seed.policy_key;

INSERT INTO corpus.industry_product (
    industry_product_key,
    industry_publisher_id,
    external_product_key,
    product_name,
    coffee_origin_countries,
    coffee_regions,
    producer_names,
    variety_names,
    process_names,
    notes
)
SELECT
    product_seed.product_key,
    publisher.industry_publisher_id,
    product_seed.external_key,
    product_seed.product_name,
    '[]'::JSONB,
    '[]'::JSONB,
    '[]'::JSONB,
    '[]'::JSONB,
    '[]'::JSONB,
    'Transaction-local product fixture.'
FROM (
    VALUES
        ('negative.round2b.product.derived.one'::TEXT, 'negative-derived-product-1', 'Derived product one', 'negative.round2b.publisher.derived'),
        ('negative.round2b.product.derived.two', 'negative-derived-product-2', 'Derived product two', 'negative.round2b.publisher.derived'),
        ('negative.round2b.product.metadata', 'negative-metadata-product', 'Metadata product', 'negative.round2b.publisher.metadata'),
        ('negative.round2b.product.blocked', 'negative-blocked-product', 'Blocked product', 'negative.round2b.publisher.blocked')
) AS product_seed(product_key, external_key, product_name, publisher_key)
JOIN corpus.industry_publisher AS publisher
  ON publisher.industry_publisher_key = product_seed.publisher_key;

INSERT INTO corpus.sampling_frame (
    sampling_frame_key,
    name,
    language_tag_code,
    frame_sha256,
    created_at,
    description,
    representativeness_note
)
VALUES
    ('negative.round2b.frame.draft', 'Negative draft frame', 'und', repeat('1', 64), TIMESTAMPTZ '2026-08-24 01:00:00+00', 'Transaction-local draft sampling frame.', 'A synthetic negative-test frame with no representativeness claim.'),
    ('negative.round2b.frame.frozen', 'Negative frozen frame', 'und', repeat('2', 64), TIMESTAMPTZ '2026-08-24 01:00:00+00', 'Transaction-local frozen sampling frame.', 'A synthetic negative-test frame with no representativeness claim.');

INSERT INTO corpus.sampling_frame_member (
    sampling_frame_id,
    industry_publisher_id,
    source_policy_review_id,
    selected,
    roaster_size_stratum,
    process_focus_stratum,
    offering_period_stratum,
    selection_rationale
)
SELECT
    frame.sampling_frame_id,
    publisher.industry_publisher_id,
    policy.source_policy_review_id,
    TRUE,
    'negative_fixture',
    'not_inferred',
    'transaction_local',
    'Required only to exercise frozen-frame governance.'
FROM (
    VALUES
        ('negative.round2b.frame.draft'::TEXT, 'negative.round2b.publisher.derived', 'negative.round2b.policy.derived'),
        ('negative.round2b.frame.draft', 'negative.round2b.publisher.metadata', 'negative.round2b.policy.metadata'),
        ('negative.round2b.frame.draft', 'negative.round2b.publisher.blocked', 'negative.round2b.policy.blocked'),
        ('negative.round2b.frame.frozen', 'negative.round2b.publisher.derived', 'negative.round2b.policy.derived')
) AS member_seed(frame_key, publisher_key, policy_key)
JOIN corpus.sampling_frame AS frame
  ON frame.sampling_frame_key = member_seed.frame_key
JOIN corpus.industry_publisher AS publisher
  ON publisher.industry_publisher_key = member_seed.publisher_key
JOIN corpus.source_policy_review AS policy
  ON policy.source_policy_review_key = member_seed.policy_key;

INSERT INTO corpus.normalization_pipeline (
    normalization_pipeline_key,
    version_label,
    language_tag_code,
    unicode_form,
    rules_sha256,
    code_commit_sha,
    parser_version,
    description,
    created_at,
    frozen_at
)
VALUES (
    'negative.round2b.pipeline.v1',
    'negative-round2b-v1',
    'und',
    'NFC',
    repeat('3', 64),
    repeat('4', 40),
    'negative-parser-v1',
    'Transaction-local frozen normalization pipeline.',
    TIMESTAMPTZ '2026-08-24 01:00:00+00',
    TIMESTAMPTZ '2026-08-24 01:01:00+00'
);

INSERT INTO corpus.corpus (
    corpus_key,
    name,
    language_tag_code,
    description,
    capture_metadata
)
VALUES
    ('negative.round2b.corpus.draft', 'Negative draft corpus', 'und', 'Transaction-local draft corpus.', '{"negative_test":true}'::JSONB),
    ('negative.round2b.corpus.frozen', 'Negative frozen corpus', 'und', 'Transaction-local frozen corpus.', '{"negative_test":true}'::JSONB);

INSERT INTO corpus.corpus_snapshot (
    corpus_snapshot_key,
    corpus_id,
    corpus_version,
    manifest_dataset_id,
    sampling_frame_id,
    normalization_pipeline_id,
    capture_window_start,
    capture_window_end,
    source_inventory_sha256,
    document_inventory_sha256,
    code_commit_sha,
    expected_document_count,
    expected_observation_count,
    expected_normalized_expression_count,
    raw_public_reproducibility_complete,
    reproducibility_boundary,
    frozen_at
)
SELECT
    snapshot_seed.snapshot_key,
    corpus_record.corpus_id,
    snapshot_seed.version_label,
    dataset.dataset_id,
    frame.sampling_frame_id,
    pipeline.normalization_pipeline_id,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    TIMESTAMPTZ '2026-08-25 00:00:00+00',
    repeat(snapshot_seed.hash_character, 64),
    repeat(snapshot_seed.hash_character, 64),
    repeat('4', 40),
    snapshot_seed.document_count,
    snapshot_seed.observation_count,
    0,
    FALSE,
    'Raw fixture rows are transaction-local and never exported.',
    NULL
FROM (
    VALUES
        ('negative.round2b.snapshot.draft'::TEXT, 'negative.round2b.corpus.draft', 'negative-round2b-draft', 'negative.round2b.frame.draft', '5', 0::BIGINT, 0::BIGINT),
        ('negative.round2b.snapshot.frozen', 'negative.round2b.corpus.frozen', 'negative-round2b-frozen', 'negative.round2b.frame.frozen', '6', 2::BIGINT, 1::BIGINT)
) AS snapshot_seed(
    snapshot_key,
    corpus_key,
    version_label,
    frame_key,
    hash_character,
    document_count,
    observation_count
)
JOIN corpus.corpus AS corpus_record
  ON corpus_record.corpus_key = snapshot_seed.corpus_key
JOIN corpus.sampling_frame AS frame
  ON frame.sampling_frame_key = snapshot_seed.frame_key
CROSS JOIN LATERAL (
    SELECT dataset_id
    FROM evidence.dataset
    ORDER BY dataset_key
    LIMIT 1
) AS dataset
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_key = 'negative.round2b.pipeline.v1';

INSERT INTO corpus.corpus_snapshot_source (
    corpus_snapshot_id,
    industry_publisher_id,
    source_policy_review_id,
    source_ordinal,
    sampling_stratum,
    inclusion_note
)
SELECT
    snapshot.corpus_snapshot_id,
    publisher.industry_publisher_id,
    policy.source_policy_review_id,
    source_seed.source_ordinal,
    'negative_fixture',
    'Transaction-local source membership.'
FROM (
    VALUES
        ('negative.round2b.snapshot.draft'::TEXT, 'negative.round2b.publisher.derived', 'negative.round2b.policy.derived', 1),
        ('negative.round2b.snapshot.draft', 'negative.round2b.publisher.metadata', 'negative.round2b.policy.metadata', 2),
        ('negative.round2b.snapshot.draft', 'negative.round2b.publisher.blocked', 'negative.round2b.policy.blocked', 3),
        ('negative.round2b.snapshot.frozen', 'negative.round2b.publisher.derived', 'negative.round2b.policy.derived', 1)
) AS source_seed(snapshot_key, publisher_key, policy_key, source_ordinal)
JOIN corpus.corpus_snapshot AS snapshot
  ON snapshot.corpus_snapshot_key = source_seed.snapshot_key
JOIN corpus.industry_publisher AS publisher
  ON publisher.industry_publisher_key = source_seed.publisher_key
JOIN corpus.source_policy_review AS policy
  ON policy.source_policy_review_key = source_seed.policy_key;

INSERT INTO corpus.acquisition_batch (
    acquisition_batch_key,
    corpus_snapshot_id,
    batch_ordinal,
    captured_from,
    captured_until,
    batch_inventory_sha256,
    expected_document_count,
    notes
)
SELECT
    batch_seed.batch_key,
    snapshot.corpus_snapshot_id,
    1,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    TIMESTAMPTZ '2026-08-25 00:00:00+00',
    repeat(batch_seed.hash_character, 64),
    batch_seed.document_count,
    'Transaction-local acquisition batch.'
FROM (
    VALUES
        ('negative.round2b.batch.draft'::TEXT, 'negative.round2b.snapshot.draft', '7', 0::BIGINT),
        ('negative.round2b.batch.frozen', 'negative.round2b.snapshot.frozen', '8', 2::BIGINT)
) AS batch_seed(batch_key, snapshot_key, hash_character, document_count)
JOIN corpus.corpus_snapshot AS snapshot
  ON snapshot.corpus_snapshot_key = batch_seed.snapshot_key;

-- Two historical releases of one stable industry product are prepared before
-- freezing. Their review records that product identity does not collapse the
-- releases; content and metadata receipts remain distinct.
INSERT INTO corpus.captured_document (
    captured_document_key,
    corpus_id,
    source_version_id,
    external_document_key,
    captured_at,
    raw_text,
    capture_metadata,
    industry_product_id,
    source_policy_review_id,
    acquisition_batch_id,
    canonical_url,
    content_sha256,
    raw_text_sha256,
    metadata_composite_sha256
)
SELECT
    document_seed.document_key,
    corpus_record.corpus_id,
    policy.source_version_id,
    document_seed.external_key,
    TIMESTAMPTZ '2026-08-24 12:00:00+00',
    NULL,
    '{"negative_test":true}'::JSONB,
    product.industry_product_id,
    policy.source_policy_review_id,
    batch.acquisition_batch_id,
    NULL,
    repeat(document_seed.hash_character, 64),
    repeat(document_seed.raw_hash_character, 64),
    repeat(document_seed.metadata_hash_character, 64)
FROM (
    VALUES
        ('negative.round2b.document.frozen.one'::TEXT, 'negative-frozen-release-1', 'negative.round2b.product.derived.one', '9', 'a', 'b'),
        ('negative.round2b.document.frozen.two', 'negative-frozen-release-2', 'negative.round2b.product.derived.one', 'c', 'd', 'e')
) AS document_seed(
    document_key,
    external_key,
    product_key,
    hash_character,
    raw_hash_character,
    metadata_hash_character
)
JOIN corpus.corpus AS corpus_record
  ON corpus_record.corpus_key = 'negative.round2b.corpus.frozen'
JOIN corpus.industry_product AS product
  ON product.industry_product_key = document_seed.product_key
JOIN corpus.source_policy_review AS policy
  ON policy.source_policy_review_key = 'negative.round2b.policy.derived'
JOIN corpus.acquisition_batch AS batch
  ON batch.acquisition_batch_key = 'negative.round2b.batch.frozen';

INSERT INTO corpus.document_duplicate_review (
    document_duplicate_review_key,
    earlier_document_id,
    later_document_id,
    duplicate_match_basis_code,
    duplicate_review_decision_code,
    reviewed_at,
    rationale
)
SELECT
    'negative.round2b.duplicate_review.frozen',
    LEAST(first_document.captured_document_id,
          second_document.captured_document_id),
    GREATEST(first_document.captured_document_id,
             second_document.captured_document_id),
    'publisher_product_key',
    'distinct',
    TIMESTAMPTZ '2026-08-24 12:30:00+00',
    'Stable product identity does not overwrite distinct historical releases.'
FROM corpus.captured_document AS first_document
JOIN corpus.captured_document AS second_document
  ON second_document.captured_document_key =
     'negative.round2b.document.frozen.two'
WHERE first_document.captured_document_key =
      'negative.round2b.document.frozen.one';

INSERT INTO corpus.raw_observation (
    raw_observation_key,
    captured_document_id,
    observation_text,
    character_start,
    character_end,
    observation_metadata,
    observation_sha256,
    character_count,
    observation_retention_code
)
SELECT
    'negative.round2b.observation.frozen',
    document.captured_document_id,
    'target phrase',
    NULL,
    NULL,
    '{"negative_test":true}'::JSONB,
    repeat('f', 64),
    char_length('target phrase'),
    'derived_phrase'
FROM corpus.captured_document AS document
WHERE document.captured_document_key =
      'negative.round2b.document.frozen.one';

INSERT INTO kb.lexical_expression (
    expression_key,
    language_tag_code,
    expression_text,
    lifecycle_status_code
)
VALUES
    ('negative.round2b.expression.target', 'und', 'target phrase', 'active'),
    ('negative.round2b.expression.draft', 'und', 'draft phrase', 'active');

INSERT INTO corpus.observation_expression (
    observation_expression_key,
    raw_observation_id,
    expression_id,
    occurrence_ordinal
)
SELECT
    'negative.round2b.occurrence.frozen',
    observation.raw_observation_id,
    expression.expression_id,
    1
FROM corpus.raw_observation AS observation
JOIN kb.lexical_expression AS expression
  ON expression.expression_key = 'negative.round2b.expression.target'
WHERE observation.raw_observation_key =
      'negative.round2b.observation.frozen';

UPDATE corpus.corpus_snapshot
SET frozen_at = TIMESTAMPTZ '2026-08-25 00:00:00+00'
WHERE corpus_snapshot_key = 'negative.round2b.snapshot.frozen';

-- Draft documents remain mutable and provide OLD-side rows for move tests.
INSERT INTO corpus.captured_document (
    captured_document_key, corpus_id, source_version_id,
    external_document_key, captured_at, raw_text, capture_metadata,
    industry_product_id, source_policy_review_id, acquisition_batch_id,
    canonical_url, content_sha256, raw_text_sha256,
    metadata_composite_sha256
)
SELECT
    document_seed.document_key,
    corpus_record.corpus_id,
    policy.source_version_id,
    document_seed.external_key,
    TIMESTAMPTZ '2026-08-24 12:00:00+00',
    NULL,
    '{"negative_test":true}'::JSONB,
    product.industry_product_id,
    policy.source_policy_review_id,
    batch.acquisition_batch_id,
    document_seed.canonical_url,
    repeat(document_seed.hash_character, 64),
    repeat(document_seed.raw_hash_character, 64),
    repeat(document_seed.metadata_hash_character, 64)
FROM (
    VALUES
        ('negative.round2b.document.draft.one'::TEXT, 'negative-draft-release-1', 'negative.round2b.product.derived.one', NULL::TEXT, '1', '2', '3'),
        ('negative.round2b.document.draft.two', 'negative-draft-release-2', 'negative.round2b.product.derived.one', NULL, '4', '5', '6'),
        ('negative.round2b.document.draft.url', 'negative-draft-release-url', 'negative.round2b.product.derived.two', 'https://roaster-derived.fixture.invalid/releases/url', '7', '8', '9'),
        ('negative.round2b.document.metadata', 'negative-metadata-release', 'negative.round2b.product.metadata', NULL, 'a', 'b', 'c')
) AS document_seed(
    document_key,
    external_key,
    product_key,
    canonical_url,
    hash_character,
    raw_hash_character,
    metadata_hash_character
)
JOIN corpus.corpus AS corpus_record
  ON corpus_record.corpus_key = 'negative.round2b.corpus.draft'
JOIN corpus.industry_product AS product
  ON product.industry_product_key = document_seed.product_key
JOIN corpus.industry_publisher AS publisher
  ON publisher.industry_publisher_id = product.industry_publisher_id
JOIN corpus.source_policy_review AS policy
  ON policy.source_policy_review_id = publisher.source_policy_review_id
JOIN corpus.acquisition_batch AS batch
  ON batch.acquisition_batch_key = 'negative.round2b.batch.draft';

INSERT INTO corpus.raw_observation (
    raw_observation_key, captured_document_id, observation_text,
    character_start, character_end, observation_metadata,
    observation_sha256, character_count, observation_retention_code
)
SELECT
    'negative.round2b.observation.draft',
    document.captured_document_id,
    'draft phrase',
    NULL,
    NULL,
    '{"negative_test":true}'::JSONB,
    repeat('d', 64),
    char_length('draft phrase'),
    'derived_phrase'
FROM corpus.captured_document AS document
WHERE document.captured_document_key =
      'negative.round2b.document.draft.one';

INSERT INTO corpus.observation_expression (
    observation_expression_key, raw_observation_id, expression_id,
    occurrence_ordinal
)
SELECT
    'negative.round2b.occurrence.draft',
    observation.raw_observation_id,
    expression.expression_id,
    1
FROM corpus.raw_observation AS observation
JOIN kb.lexical_expression AS expression
  ON expression.expression_key = 'negative.round2b.expression.draft'
WHERE observation.raw_observation_key =
      'negative.round2b.observation.draft';

INSERT INTO corpus.document_duplicate_review (
    document_duplicate_review_key,
    earlier_document_id,
    later_document_id,
    duplicate_match_basis_code,
    duplicate_review_decision_code,
    reviewed_at,
    rationale
)
SELECT
    'negative.round2b.duplicate_review.draft',
    LEAST(first_document.captured_document_id,
          second_document.captured_document_id),
    GREATEST(first_document.captured_document_id,
             second_document.captured_document_id),
    'publisher_product_key',
    'distinct',
    TIMESTAMPTZ '2026-08-24 13:00:00+00',
    'Distinct historical release fixture.'
FROM corpus.captured_document AS first_document
JOIN corpus.captured_document AS second_document
  ON second_document.captured_document_key =
     'negative.round2b.document.draft.two'
WHERE first_document.captured_document_key =
      'negative.round2b.document.draft.one';

DO $rights_and_duplicate_failures$
BEGIN
    PERFORM pg_temp.expect_round2b_failure(
        'blocked_document_capture',
        $sql$
            INSERT INTO corpus.captured_document (
                captured_document_key, corpus_id, source_version_id,
                external_document_key, captured_at, raw_text,
                capture_metadata, industry_product_id,
                source_policy_review_id, acquisition_batch_id,
                content_sha256, raw_text_sha256,
                metadata_composite_sha256
            )
            SELECT
                'negative.round2b.document.blocked', corpus_record.corpus_id,
                policy.source_version_id, 'negative-blocked-release',
                TIMESTAMPTZ '2026-08-24 12:00:00+00', NULL,
                '{"negative_test":true}'::JSONB,
                product.industry_product_id,
                policy.source_policy_review_id,
                batch.acquisition_batch_id,
                repeat('1',64), repeat('2',64), repeat('3',64)
            FROM corpus.corpus AS corpus_record
            JOIN corpus.industry_product AS product
              ON product.industry_product_key =
                 'negative.round2b.product.blocked'
            JOIN corpus.source_policy_review AS policy
              ON policy.source_policy_review_key =
                 'negative.round2b.policy.blocked'
            JOIN corpus.acquisition_batch AS batch
              ON batch.acquisition_batch_key =
                 'negative.round2b.batch.draft'
            WHERE corpus_record.corpus_key =
                  'negative.round2b.corpus.draft'
        $sql$,
        '23514',
        'captured_document_source_policy_ck'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'raw_document_under_derived_only_policy',
        $sql$
            UPDATE corpus.captured_document
            SET raw_text = 'commercial source prose must remain absent'
            WHERE captured_document_key =
                  'negative.round2b.document.draft.one'
        $sql$,
        '23514',
        'captured_document_raw_retention_ck'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'full_text_observation_under_derived_only_policy',
        $sql$
            INSERT INTO corpus.raw_observation (
                raw_observation_key, captured_document_id,
                observation_text, observation_metadata,
                observation_sha256, character_count,
                observation_retention_code
            )
            SELECT
                'negative.round2b.observation.full_text.invalid',
                captured_document_id,
                'source prose must not cross a derived-term-only boundary',
                '{"negative_test":true}'::JSONB,
                repeat('e',64),
                char_length(
                    'source prose must not cross a derived-term-only boundary'
                ),
                'full_text'
            FROM corpus.captured_document
            WHERE captured_document_key =
                  'negative.round2b.document.draft.one'
        $sql$,
        '23514',
        'raw_observation_policy_ck'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'derived_phrase_under_metadata_only_policy',
        $sql$
            INSERT INTO corpus.raw_observation (
                raw_observation_key, captured_document_id,
                observation_text, observation_metadata,
                observation_sha256, character_count,
                observation_retention_code
            )
            SELECT
                'negative.round2b.observation.metadata.invalid',
                captured_document_id,
                'forbidden phrase',
                '{"negative_test":true}'::JSONB,
                repeat('4',64),
                char_length('forbidden phrase'),
                'derived_phrase'
            FROM corpus.captured_document
            WHERE captured_document_key =
                  'negative.round2b.document.metadata'
        $sql$,
        '23514',
        'raw_observation_policy_ck'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'duplicate_external_release_identity',
        $sql$
            INSERT INTO corpus.captured_document (
                captured_document_key, corpus_id, source_version_id,
                external_document_key, captured_at, raw_text,
                capture_metadata, industry_product_id,
                source_policy_review_id, acquisition_batch_id,
                content_sha256, raw_text_sha256,
                metadata_composite_sha256
            )
            SELECT
                'negative.round2b.document.duplicate_external', corpus_id,
                source_version_id, external_document_key, captured_at, NULL,
                '{"negative_test":true}'::JSONB, industry_product_id,
                source_policy_review_id, acquisition_batch_id,
                repeat('d',64), repeat('e',64), repeat('f',64)
            FROM corpus.captured_document
            WHERE captured_document_key =
                  'negative.round2b.document.draft.one'
        $sql$,
        '23505',
        'captured_document_external_release_uq'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'duplicate_canonical_url_identity',
        $sql$
            INSERT INTO corpus.captured_document (
                captured_document_key, corpus_id, source_version_id,
                external_document_key, captured_at, raw_text,
                capture_metadata, industry_product_id,
                source_policy_review_id, acquisition_batch_id,
                canonical_url, content_sha256, raw_text_sha256,
                metadata_composite_sha256
            )
            SELECT
                'negative.round2b.document.duplicate_url', corpus_id,
                source_version_id, 'negative-draft-release-url-copy',
                captured_at, NULL, '{"negative_test":true}'::JSONB,
                industry_product_id, source_policy_review_id,
                acquisition_batch_id, canonical_url,
                repeat('a',64), repeat('b',64), repeat('c',64)
            FROM corpus.captured_document
            WHERE captured_document_key =
                  'negative.round2b.document.draft.url'
        $sql$,
        '23505',
        'captured_document_canonical_url_uq'
    );
END
$rights_and_duplicate_failures$;

DO $both_sided_frozen_move_guards$
BEGIN
    PERFORM pg_temp.expect_round2b_failure(
        'source_membership_move_into_frozen_snapshot',
        $sql$
            UPDATE corpus.corpus_snapshot_source
            SET corpus_snapshot_id = (
                SELECT corpus_snapshot_id FROM corpus.corpus_snapshot
                WHERE corpus_snapshot_key =
                      'negative.round2b.snapshot.frozen'
            )
            WHERE corpus_snapshot_id = (
                SELECT corpus_snapshot_id FROM corpus.corpus_snapshot
                WHERE corpus_snapshot_key =
                      'negative.round2b.snapshot.draft'
            )
              AND industry_publisher_id = (
                SELECT industry_publisher_id FROM corpus.industry_publisher
                WHERE industry_publisher_key =
                      'negative.round2b.publisher.blocked'
              )
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'batch_move_into_frozen_snapshot',
        $sql$
            UPDATE corpus.acquisition_batch
            SET corpus_snapshot_id = (
                SELECT corpus_snapshot_id FROM corpus.corpus_snapshot
                WHERE corpus_snapshot_key =
                      'negative.round2b.snapshot.frozen'
            )
            WHERE acquisition_batch_key =
                  'negative.round2b.batch.draft'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'document_move_into_frozen_snapshot',
        $sql$
            UPDATE corpus.captured_document
            SET corpus_id = (
                SELECT corpus_id FROM corpus.corpus
                WHERE corpus_key = 'negative.round2b.corpus.frozen'
            )
            WHERE captured_document_key =
                  'negative.round2b.document.draft.one'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'observation_move_into_frozen_snapshot',
        $sql$
            UPDATE corpus.raw_observation
            SET captured_document_id = (
                SELECT captured_document_id FROM corpus.captured_document
                WHERE captured_document_key =
                      'negative.round2b.document.frozen.one'
            )
            WHERE raw_observation_key =
                  'negative.round2b.observation.draft'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'expression_occurrence_move_into_frozen_snapshot',
        $sql$
            UPDATE corpus.observation_expression
            SET raw_observation_id = (
                SELECT raw_observation_id FROM corpus.raw_observation
                WHERE raw_observation_key =
                      'negative.round2b.observation.frozen'
            )
            WHERE observation_expression_key =
                  'negative.round2b.occurrence.draft'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'duplicate_review_move_into_frozen_snapshot',
        $sql$
            UPDATE corpus.document_duplicate_review
            SET
                earlier_document_id = (
                    SELECT captured_document_id
                    FROM corpus.captured_document
                    WHERE captured_document_key =
                          'negative.round2b.document.frozen.one'
                ),
                later_document_id = (
                    SELECT captured_document_id
                    FROM corpus.captured_document
                    WHERE captured_document_key =
                          'negative.round2b.document.frozen.two'
                )
            WHERE document_duplicate_review_key =
                  'negative.round2b.duplicate_review.draft'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'sampling_member_move_into_frozen_frame',
        $sql$
            UPDATE corpus.sampling_frame_member
            SET sampling_frame_id = (
                SELECT sampling_frame_id FROM corpus.sampling_frame
                WHERE sampling_frame_key =
                      'negative.round2b.frame.frozen'
            )
            WHERE sampling_frame_id = (
                SELECT sampling_frame_id FROM corpus.sampling_frame
                WHERE sampling_frame_key =
                      'negative.round2b.frame.draft'
            )
              AND industry_publisher_id = (
                SELECT industry_publisher_id FROM corpus.industry_publisher
                WHERE industry_publisher_key =
                      'negative.round2b.publisher.blocked'
              )
        $sql$,
        '55000'
    );

    -- The OLD side is independently protected: changing the foreign key does
    -- not permit a row to escape from an already frozen inventory.
    PERFORM pg_temp.expect_round2b_failure(
        'source_membership_move_out_of_frozen_snapshot',
        $sql$
            UPDATE corpus.corpus_snapshot_source
            SET corpus_snapshot_id = (
                SELECT corpus_snapshot_id FROM corpus.corpus_snapshot
                WHERE corpus_snapshot_key =
                      'negative.round2b.snapshot.draft'
            )
            WHERE corpus_snapshot_id = (
                SELECT corpus_snapshot_id FROM corpus.corpus_snapshot
                WHERE corpus_snapshot_key =
                      'negative.round2b.snapshot.frozen'
            )
              AND industry_publisher_id = (
                SELECT industry_publisher_id FROM corpus.industry_publisher
                WHERE industry_publisher_key =
                      'negative.round2b.publisher.derived'
              )
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'batch_move_out_of_frozen_snapshot',
        $sql$
            UPDATE corpus.acquisition_batch
            SET corpus_snapshot_id = (
                SELECT corpus_snapshot_id FROM corpus.corpus_snapshot
                WHERE corpus_snapshot_key =
                      'negative.round2b.snapshot.draft'
            )
            WHERE acquisition_batch_key =
                  'negative.round2b.batch.frozen'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'document_move_out_of_frozen_snapshot',
        $sql$
            UPDATE corpus.captured_document
            SET corpus_id = (
                SELECT corpus_id FROM corpus.corpus
                WHERE corpus_key = 'negative.round2b.corpus.draft'
            )
            WHERE captured_document_key =
                  'negative.round2b.document.frozen.one'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'observation_move_out_of_frozen_snapshot',
        $sql$
            UPDATE corpus.raw_observation
            SET captured_document_id = (
                SELECT captured_document_id FROM corpus.captured_document
                WHERE captured_document_key =
                      'negative.round2b.document.draft.one'
            )
            WHERE raw_observation_key =
                  'negative.round2b.observation.frozen'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'expression_occurrence_move_out_of_frozen_snapshot',
        $sql$
            UPDATE corpus.observation_expression
            SET raw_observation_id = (
                SELECT raw_observation_id FROM corpus.raw_observation
                WHERE raw_observation_key =
                      'negative.round2b.observation.draft'
            )
            WHERE observation_expression_key =
                  'negative.round2b.occurrence.frozen'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'duplicate_review_move_out_of_frozen_snapshot',
        $sql$
            UPDATE corpus.document_duplicate_review
            SET
                earlier_document_id = LEAST(
                    (SELECT captured_document_id
                     FROM corpus.captured_document
                     WHERE captured_document_key =
                           'negative.round2b.document.draft.one'),
                    (SELECT captured_document_id
                     FROM corpus.captured_document
                     WHERE captured_document_key =
                           'negative.round2b.document.draft.two')
                ),
                later_document_id = GREATEST(
                    (SELECT captured_document_id
                     FROM corpus.captured_document
                     WHERE captured_document_key =
                           'negative.round2b.document.draft.one'),
                    (SELECT captured_document_id
                     FROM corpus.captured_document
                     WHERE captured_document_key =
                           'negative.round2b.document.draft.two')
                )
            WHERE document_duplicate_review_key =
                  'negative.round2b.duplicate_review.frozen'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'sampling_member_move_out_of_frozen_frame',
        $sql$
            UPDATE corpus.sampling_frame_member
            SET sampling_frame_id = (
                SELECT sampling_frame_id FROM corpus.sampling_frame
                WHERE sampling_frame_key =
                      'negative.round2b.frame.draft'
            )
            WHERE sampling_frame_id = (
                SELECT sampling_frame_id FROM corpus.sampling_frame
                WHERE sampling_frame_key =
                      'negative.round2b.frame.frozen'
            )
              AND industry_publisher_id = (
                SELECT industry_publisher_id FROM corpus.industry_publisher
                WHERE industry_publisher_key =
                      'negative.round2b.publisher.derived'
              )
        $sql$,
        '55000'
    );
END
$both_sided_frozen_move_guards$;

DO $frozen_governance_failures$
BEGIN
    PERFORM pg_temp.expect_round2b_failure(
        'frozen_source_policy_mutation',
        $sql$
            UPDATE corpus.source_policy_review
            SET notes = 'Mutation must fail.'
            WHERE source_policy_review_key =
                  'negative.round2b.policy.derived'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'frozen_product_mutation',
        $sql$
            UPDATE corpus.industry_product
            SET notes = 'Mutation must fail.'
            WHERE industry_product_key =
                  'negative.round2b.product.derived.one'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'frozen_pipeline_mutation',
        $sql$
            UPDATE corpus.normalization_pipeline
            SET description = 'Mutation must fail.'
            WHERE normalization_pipeline_key =
                  'negative.round2b.pipeline.v1'
        $sql$,
        '55000'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'frozen_pipeline_rule_insert',
        $sql$
            INSERT INTO corpus.normalization_rule (
                normalization_rule_key, normalization_pipeline_id,
                rule_order, rule_kind, input_normalized_text,
                output_normalized_text, description
            )
            SELECT
                'negative.round2b.rule.frozen', normalization_pipeline_id,
                99, 'WHOLE_PHRASE', 'bad input', 'bad output',
                'Frozen pipeline rule insertion must fail.'
            FROM corpus.normalization_pipeline
            WHERE normalization_pipeline_key =
                  'negative.round2b.pipeline.v1'
        $sql$,
        '55000',
        'normalization_rule_pipeline_frozen_ck'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'frozen_normalized_dictionary_insert',
        $sql$
            INSERT INTO corpus.normalized_expression (
                normalized_expression_key,
                normalization_pipeline_id,
                normalized_text
            )
            SELECT
                'negative.round2b.normalized.frozen',
                normalization_pipeline_id,
                'already normalized'
            FROM corpus.normalization_pipeline
            WHERE normalization_pipeline_key =
                  'negative.round2b.pipeline.v1'
        $sql$,
        '55000',
        'normalization_dictionary_snapshot_frozen_ck'
    );

    PERFORM pg_temp.expect_round2b_failure(
        'frozen_graph_policy_rule_insert',
        $sql$
            INSERT INTO ml.retrieval_graph_policy_rule (
                retrieval_graph_policy_rule_key,
                retrieval_graph_policy_id,
                rule_order,
                relation_type_code,
                traversal_direction,
                maximum_hops,
                description
            )
            SELECT
                'negative.round2b.graph_rule.frozen',
                retrieval_graph_policy_id,
                99,
                'contrasts_with',
                'SYMMETRIC',
                1,
                'Frozen allowlist mutation must fail.'
            FROM ml.retrieval_graph_policy
            WHERE retrieval_graph_policy_key = 'graph_policy.round2b.v1'
        $sql$,
        '55000',
        'retrieval_graph_policy_rule_frozen_ck'
    );
END
$frozen_governance_failures$;

INSERT INTO ml.retrieval_graph_policy (
    retrieval_graph_policy_key,
    version_label,
    name,
    description,
    rules_sha256,
    code_commit_sha,
    is_frozen,
    created_at,
    configuration
)
VALUES (
    'negative.round2b.graph_policy.draft',
    'negative-v1',
    'Negative draft graph policy',
    'Transaction-local graph-policy constraint fixture.',
    repeat('a', 64),
    repeat('b', 40),
    FALSE,
    TIMESTAMPTZ '2026-08-24 01:00:00+00',
    '{"negative_test":true}'::JSONB
);

SELECT pg_temp.expect_round2b_failure(
    'graph_policy_more_than_one_hop',
    $sql$
        INSERT INTO ml.retrieval_graph_policy_rule (
            retrieval_graph_policy_rule_key,
            retrieval_graph_policy_id,
            rule_order,
            relation_type_code,
            traversal_direction,
            maximum_hops,
            description
        )
        SELECT
            'negative.round2b.graph_rule.two_hops',
            retrieval_graph_policy_id,
            1,
            'broader_than',
            'OUTGOING',
            2,
            'Two-hop storage must fail.'
        FROM ml.retrieval_graph_policy
        WHERE retrieval_graph_policy_key =
              'negative.round2b.graph_policy.draft'
    $sql$,
    '23514',
    'retrieval_graph_policy_rule_one_hop_ck'
);

-- Audit-grade fixtures use a real frozen snapshot occurrence. No question is
-- asked about objective coffee flavour; grades concern normalization relevance.
INSERT INTO audit.retrieval_audit_set (
    retrieval_audit_set_key,
    corpus_snapshot_id,
    version_label,
    name,
    description,
    sampling_configuration,
    inventory_sha256,
    code_commit_sha,
    created_at,
    frozen_at
)
SELECT
    'negative.round2b.audit_set',
    corpus_snapshot_id,
    'negative-v1',
    'Negative retrieval audit set',
    'Transaction-local relevance-grade fixture.',
    '{"negative_test":true}'::JSONB,
    repeat('c', 64),
    repeat('d', 40),
    TIMESTAMPTZ '2026-08-24 14:00:00+00',
    NULL
FROM corpus.corpus_snapshot
WHERE corpus_snapshot_key = 'negative.round2b.snapshot.frozen';

INSERT INTO audit.retrieval_audit_case (
    retrieval_audit_case_key,
    retrieval_audit_set_id,
    expression_id,
    representative_observation_expression_id,
    audit_split_code,
    case_ordinal,
    notes
)
SELECT
    'negative.round2b.audit_case',
    audit_set.retrieval_audit_set_id,
    expression.expression_id,
    occurrence.observation_expression_id,
    'held_out',
    1,
    'Transaction-local audit case.'
FROM audit.retrieval_audit_set AS audit_set
JOIN kb.lexical_expression AS expression
  ON expression.expression_key = 'negative.round2b.expression.target'
JOIN corpus.observation_expression AS occurrence
  ON occurrence.observation_expression_key =
     'negative.round2b.occurrence.frozen'
WHERE audit_set.retrieval_audit_set_key = 'negative.round2b.audit_set';

INSERT INTO audit.retrieval_audit_case_stratum (
    retrieval_audit_case_id,
    retrieval_audit_stratum_code
)
SELECT retrieval_audit_case_id, 'unresolved'
FROM audit.retrieval_audit_case
WHERE retrieval_audit_case_key = 'negative.round2b.audit_case';

INSERT INTO audit.reviewer (reviewer_key, display_name, affiliation)
VALUES
    ('negative.round2b.reviewer.one', 'Negative reviewer one', NULL),
    ('negative.round2b.reviewer.two', 'Negative reviewer two', NULL);

INSERT INTO audit.retrieval_case_review (
    retrieval_case_review_key,
    retrieval_audit_case_id,
    reviewer_id,
    audit_review_role_code,
    expects_unresolved,
    reviewed_at,
    notes
)
SELECT
    'negative.round2b.review.unresolved',
    audit_case.retrieval_audit_case_id,
    reviewer.reviewer_id,
    'independent',
    TRUE,
    TIMESTAMPTZ '2026-08-24 14:30:00+00',
    'Unresolved review fixture.'
FROM audit.retrieval_audit_case AS audit_case
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = 'negative.round2b.reviewer.one'
WHERE audit_case.retrieval_audit_case_key =
      'negative.round2b.audit_case';

SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

SELECT pg_temp.expect_round2b_failure(
    'unresolved_grade_not_candidate_judgment',
    $sql$
        INSERT INTO audit.retrieval_relevance_judgment (
            retrieval_relevance_judgment_key,
            retrieval_case_review_id,
            concept_id,
            relevance_grade_code,
            rationale
        )
        SELECT
            'negative.round2b.judgment.u',
            review.retrieval_case_review_id,
            concept.concept_id,
            'U',
            'U belongs to case-level abstention expectation, not a concept row.'
        FROM audit.retrieval_case_review AS review
        CROSS JOIN LATERAL (
            SELECT concept_id FROM kb.concept ORDER BY concept_key LIMIT 1
        ) AS concept
        WHERE review.retrieval_case_review_key =
              'negative.round2b.review.unresolved'
    $sql$,
    '23514',
    'retrieval_relevance_judgment_candidate_grade_ck'
);

DO $invalid_review_semantics$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.retrieval_relevance_judgment (
            retrieval_relevance_judgment_key,
            retrieval_case_review_id,
            concept_id,
            relevance_grade_code,
            rationale
        )
        SELECT
            'negative.round2b.judgment.unresolved_grade_three',
            review.retrieval_case_review_id,
            concept.concept_id,
            '3',
            'An unresolved review must not have a positive mapping.'
        FROM audit.retrieval_case_review AS review
        CROSS JOIN LATERAL (
            SELECT concept_id FROM kb.concept ORDER BY concept_key LIMIT 1
        ) AS concept
        WHERE review.retrieval_case_review_key =
              'negative.round2b.review.unresolved';
        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION 'unresolved review accepted a grade-three concept';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'retrieval_case_review_unresolved_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2B_NEGATIVE=unresolved_review_positive_grade SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;

    BEGIN
        INSERT INTO audit.retrieval_case_review (
            retrieval_case_review_key,
            retrieval_audit_case_id,
            reviewer_id,
            audit_review_role_code,
            expects_unresolved,
            reviewed_at,
            notes
        )
        SELECT
            'negative.round2b.review.resolvable_without_positive',
            audit_case.retrieval_audit_case_id,
            reviewer.reviewer_id,
            'independent',
            FALSE,
            TIMESTAMPTZ '2026-08-24 14:31:00+00',
            'A resolvable review requires grade 2 or 3.'
        FROM audit.retrieval_audit_case AS audit_case
        JOIN audit.reviewer AS reviewer
          ON reviewer.reviewer_key = 'negative.round2b.reviewer.two'
        WHERE audit_case.retrieval_audit_case_key =
              'negative.round2b.audit_case';
        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION 'resolvable review without positive judgment succeeded';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'retrieval_case_review_resolvable_ck' THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND2B_NEGATIVE=resolvable_review_requires_positive SQLSTATE=% CONSTRAINT=% PASS',
            actual_state,
            actual_constraint;
    END;
END
$invalid_review_semantics$;

-- Complete the transaction-local held-out case before freezing it: two
-- independent reviewers plus one adjudicated unresolved decision.
INSERT INTO audit.retrieval_case_review (
    retrieval_case_review_key,
    retrieval_audit_case_id,
    reviewer_id,
    audit_review_role_code,
    expects_unresolved,
    reviewed_at,
    notes
)
SELECT
    review_seed.review_key,
    audit_case.retrieval_audit_case_id,
    reviewer.reviewer_id,
    review_seed.review_role,
    TRUE,
    review_seed.reviewed_at,
    'Valid unresolved review used only to complete the frozen audit fixture.'
FROM (
    VALUES
        (
            'negative.round2b.review.independent.two'::TEXT,
            'negative.round2b.reviewer.two'::TEXT,
            'independent'::TEXT,
            TIMESTAMPTZ '2026-08-24 14:32:00+00'
        ),
        (
            'negative.round2b.review.adjudicated',
            'negative.round2b.reviewer.two',
            'adjudicated',
            TIMESTAMPTZ '2026-08-24 14:33:00+00'
        )
) AS review_seed(review_key, reviewer_key, review_role, reviewed_at)
JOIN audit.retrieval_audit_case AS audit_case
  ON audit_case.retrieval_audit_case_key =
     'negative.round2b.audit_case'
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = review_seed.reviewer_key;

SET CONSTRAINTS ALL IMMEDIATE;

UPDATE audit.retrieval_audit_set
SET frozen_at = TIMESTAMPTZ '2026-08-24 15:00:00+00'
WHERE retrieval_audit_set_key = 'negative.round2b.audit_set';

SELECT pg_temp.expect_round2b_failure(
    'frozen_audit_case_inventory_insert',
    $sql$
        INSERT INTO audit.retrieval_audit_case (
            retrieval_audit_case_key, retrieval_audit_set_id,
            expression_id, representative_observation_expression_id,
            audit_split_code, case_ordinal, notes
        )
        SELECT
            'negative.round2b.audit_case.after_freeze',
            audit_set.retrieval_audit_set_id,
            expression.expression_id,
            occurrence.observation_expression_id,
            'development',
            2,
            'Frozen audit inventory insertion must fail.'
        FROM audit.retrieval_audit_set AS audit_set
        JOIN kb.lexical_expression AS expression
          ON expression.expression_key =
             'negative.round2b.expression.target'
        JOIN corpus.observation_expression AS occurrence
          ON occurrence.observation_expression_key =
             'negative.round2b.occurrence.frozen'
        WHERE audit_set.retrieval_audit_set_key =
              'negative.round2b.audit_set'
    $sql$,
    '55000',
    'retrieval_audit_inventory_frozen_ck'
);

ROLLBACK;

\echo ROUND2B_NEGATIVE_PASS=true
