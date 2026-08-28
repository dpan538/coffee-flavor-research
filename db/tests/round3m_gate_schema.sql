\set ON_ERROR_STOP on
\pset pager off

-- Round 3M descriptor-first positive and negative paths. All generated rows
-- are transaction-local structural fixtures and are rolled back.

BEGIN;

CREATE FUNCTION pg_temp.expect_round3m_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3m_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3M negative unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3M_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END
$expect_round3m_failure$;

DO $empty_and_contract_positive$
DECLARE
    gate_count BIGINT;
    criterion_count BIGINT;
BEGIN
    SELECT count(*) INTO gate_count
    FROM audit.round3m_descriptor_gate_definition
    WHERE gate_version = 'round3m-descriptor-gates-v1';
    SELECT count(*) INTO criterion_count
    FROM audit.round3m_descriptor_gate_criterion
    WHERE gate_version = 'round3m-descriptor-gates-v1';

    IF gate_count <> 7 OR criterion_count <> 56 THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=versioned_gate_contract expected 7/56 got %/%',
            gate_count, criterion_count;
    END IF;
    IF EXISTS (
        SELECT 1 FROM audit.v_round3m_descriptor_gate WHERE gate_pass
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=empty_database_never_passes failed';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM audit.v_round3m_descriptor_gate_status
        WHERE not_applicable AND pass
    ) THEN
        RAISE EXCEPTION 'ROUND3M_POSITIVE=na_never_passes failed';
    END IF;
    IF EXISTS (
        SELECT 1
        FROM audit.v_round3m_legacy_gate_status
        WHERE current_training_authority
           OR current_training_authorization_pass
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=legacy_gate_deprecation failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=versioned_gate_contract,empty_database_never_passes,na_never_passes,legacy_gate_deprecation PASS';
END
$empty_and_contract_positive$;

INSERT INTO audit.round3l_source_census (
    census_version, census_item_key, item_kind, series_key,
    source_family_key, edition_label, edition_year,
    official_url, discovery_basis, current_corpus_state,
    acquisition_state, rights_state, discovered_at
)
SELECT
    'round3m-test-v1', 'round3m:test:census:' || n,
    'PILOT_EDITION', 'round3m_test_series_' || n,
    'round3m_test_family_' || n, 'Round 3M fixture ' || n, 2020 + n,
    'https://family' || n || '.example.test/results',
    'TRANSACTION_LOCAL_STRUCTURAL_FIXTURE', 'DISCOVERED',
    'PUBLIC_OFFICIAL_EDITION_ROUTE', 'DIMENSION_SPECIFIC',
    '2026-08-28T01:00:00Z'
FROM generate_series(1, 3) AS fixture(n);

INSERT INTO audit.round3l_source_attempt (
    attempt_key, round3l_source_census_id, lane_key, attempt_sequence,
    attempted_at, acquisition_method, outcome, canonical_url, final_url,
    http_status, source_snapshot_sha256, artifact_byte_count,
    parsed_row_count, normalized_record_count, descriptor_assertion_count,
    next_cursor
)
SELECT
    'round3m.test.attempt.' || n,
    census.round3l_source_census_id, 'round3m_gate_test', n,
    '2026-08-28T01:01:00Z', 'TRANSACTION_LOCAL_FIXTURE', 'COMPLETED',
    census.official_url, census.official_url, 200,
    repeat(substr('abc', n, 1), 64), 1024, 0, 0, 0,
    'round3m:test:complete:' || n
FROM generate_series(1, 3) AS fixture(n)
JOIN audit.round3l_source_census AS census
  ON census.census_version = 'round3m-test-v1'
 AND census.census_item_key = 'round3m:test:census:' || n;

INSERT INTO evidence.round3m_independent_source_family (
    independent_source_family_id, organizer_id, family_name,
    independence_basis, rights_lineage_id,
    admitted_for_descriptor_research
)
SELECT
    'round3m.test.family.' || n, 'round3m.test.organizer.' || n,
    'Round 3M fixture family ' || n,
    'Transaction-local independent fixture origin ' || n,
    'round3m.test.rights.lineage.' || n, TRUE
FROM generate_series(1, 3) AS fixture(n);

INSERT INTO evidence.round3m_source_route (
    source_route_id, independent_source_family_id,
    round3l_source_census_id, organizer_id, publication_host,
    canonical_url, route_pattern, route_disposition,
    rights_lineage_id, mirror_lineage_id, discovered_at
)
SELECT
    'round3m.test.route.' || n, 'round3m.test.family.' || n,
    census.round3l_source_census_id, 'round3m.test.organizer.' || n,
    'family' || n || '.example.test', census.official_url,
    '/results/{edition}', 'PRIORITY_DESCRIPTOR_ROUTE',
    'round3m.test.rights.lineage.' || n,
    'round3m.test.mirror.lineage.' || n,
    '2026-08-28T01:00:00Z'
FROM generate_series(1, 3) AS fixture(n)
JOIN audit.round3l_source_census AS census
  ON census.census_version = 'round3m-test-v1'
 AND census.census_item_key = 'round3m:test:census:' || n;

INSERT INTO evidence.round3m_source_schema_signature (
    schema_signature_id, source_route_id, schema_version, host,
    route_pattern, edition_or_period, field_labels_json, selectors_json,
    publication_layer_rules_json, field_origin_assumptions_json,
    known_ambiguity, positive_fixture_locator, negative_fixture_locator,
    adapter_version, live_positive_fixture_present, validation_status
)
SELECT
    'round3m.test.schema.' || n, 'round3m.test.route.' || n, 1,
    'family' || n || '.example.test', '/results/{edition}',
    (2020 + n)::TEXT, '["Top Jury Descriptions"]'::JSONB,
    '{"field":"#top-jury"}'::JSONB,
    '{"Top Jury Descriptions":"PRIMARY_JURY_DESCRIPTION"}'::JSONB,
    '{"Top Jury Descriptions":"explicit jury attribution"}'::JSONB,
    'Transaction-local structural fixture only.',
    'https://family' || n || '.example.test/positive',
    'https://family' || n || '.example.test/ranking-negative',
    'round3m-test-adapter-v1', TRUE, 'VALIDATED'
FROM generate_series(1, 3) AS fixture(n);

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    round3l_source_attempt_id, governed_locator, source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    file_size_bytes, storage_state,
    non_storage_reason, parser_version, adapter_version
)
SELECT
    'round3m.test.artifact.' || n, 'round3m.test.route.' || n,
    'round3m.test.schema.' || n, attempt.round3l_source_attempt_id,
    attempt.canonical_url, '2026-08-28T01:01:00Z',
    repeat(substr('abc', n, 1), 64), '',
    'FULL_SOURCE_FILE_SHA256', '', 1024,
    'HASH_AND_LOCATOR_ONLY',
    'Transaction-local fixture stores hash and locator only.',
    'round3m-test-parser-v1', 'round3m-test-adapter-v1'
FROM generate_series(1, 3) AS fixture(n)
JOIN audit.round3l_source_attempt AS attempt
  ON attempt.attempt_key = 'round3m.test.attempt.' || n;

INSERT INTO evidence.round3m_descriptor_rights_decision (
    rights_decision_id, rights_scope_id, decision_version,
    source_route_id, publication_layer, source_field_label,
    public_discovery, internal_research_analysis,
    derived_research_data, model_research,
    deployment_or_commercial_model, raw_redistribution,
    decision_authority_code, decision_actor_type, decision_basis,
    evidence_locator, decided_at
)
SELECT
    'round3m.test.rights.' || n, 'round3m.test.scope.' || n, 1,
    'round3m.test.route.' || n, 'PRIMARY_JURY_DESCRIPTION',
    'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
    'AFFIRMATIVE', 'AFFIRMATIVE', 'PENDING', 'PROHIBITED',
    'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
    'Transaction-local fixture permission evidence.',
    'https://family' || n || '.example.test/permission',
    '2026-08-28T01:02:00Z'
FROM generate_series(1, 3) AS fixture(n);

INSERT INTO corpus.professional_acquisition_record (
    professional_acquisition_record_key, round3l_source_attempt_id,
    source_family_key, series_key, edition_key, edition_year,
    category_key, round_key, source_record_key, entry_or_lot_key,
    coffee_identity_key, preparation_service_code, effective_record_key,
    evidence_tier, payload_kind, fresh_preparation_status,
    fresh_preparation_evidence_locator, c0_source_status,
    c1_evidence_status, source_snapshot_sha256, raw_record_sha256,
    public_results_use, public_descriptor_use, internal_research_use,
    public_derived_release, model_research_use, commercial_model_use,
    deduplication_disposition, corpus_state, label_review_status,
    ingested_at
)
SELECT
    'round3m.test.record.' || n,
    attempt.round3l_source_attempt_id,
    'round3m_test_family_' || family_n,
    'round3m_test_series_' || family_n,
    'round3m_test_edition_' || family_n,
    2020 + family_n, 'cupping', 'final', 'record-' || n,
    'lot-' || n, 'coffee-' || n, 'green_competition_cupping',
    'round3m.test.effective.' || n, 'P2', 'OFFICIAL_DESCRIPTOR',
    'CONFIRMED', 'https://family' || family_n ||
        '.example.test/protocol', 'NOT_REPORTED', 'NOT_REPORTED',
    repeat(substr('abc', family_n, 1), 64),
    audit.round3i_utf8_sha256('record-' || n),
    'ALLOWED', 'ALLOWED', 'ALLOWED', 'ALLOWED', 'ALLOWED',
    'PENDING', 'CANONICAL', 'RESEARCH_STAGED', 'NOT_REVIEWED',
    '2026-08-28T01:03:00Z'
FROM (
    SELECT n, ((n - 1) % 3) + 1 AS family_n
    FROM generate_series(1, 500) AS fixture(n)
) AS fixture
JOIN audit.round3l_source_attempt AS attempt
  ON attempt.attempt_key = 'round3m.test.attempt.' || family_n;

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, professional_acquisition_record_id,
    effective_record_key, edition_year, source_artifact_id,
    source_route_id, schema_signature_id, publication_layer,
    source_field_label, source_field_label_sha256,
    source_selector_or_locator,
    source_page_or_record_locator, source_observation_key,
    raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256,
    text_storage_state, source_text_non_storage_reason,
    source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator,
    review_state, review_actor_type, rights_decision_id,
    source_retrieved_at, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
)
SELECT
    'round3m.test.assertion.' || n,
    record.professional_acquisition_record_id,
    record.effective_record_key, record.edition_year,
    'round3m.test.artifact.' || family_n,
    'round3m.test.route.' || family_n,
    'round3m.test.schema.' || family_n,
    'PRIMARY_JURY_DESCRIPTION', 'Top Jury Descriptions',
    audit.round3i_utf8_sha256('Top Jury Descriptions'),
    '#top-jury', 'record-' || n || '#top-jury',
    'round3m.test.observation.' || n,
    'Flavor note ' || form_n,
    audit.round3i_utf8_sha256('Flavor note ' || form_n),
    'note-' || form_n,
    audit.round3i_utf8_sha256('note-' || form_n),
    'REVIEWED_EXCERPT', '', 'en', 'STRICT_FLAVOR',
    'note-' || form_n, audit.round3i_utf8_sha256('note-' || form_n),
    'note-' || form_n, audit.round3i_utf8_sha256('note-' || form_n),
    'UNICODE_NFC_WHITESPACE_CASE', 'P2',
    'EXPLICIT_TOP_JURY_FIELD',
    'Fixture explicitly identifies the Top Jury field.',
    'record-' || n || '#top-jury',
    'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
    'round3m.test.rights.' || family_n,
    '2026-08-28T01:01:00Z',
    repeat(substr('abc', family_n, 1), 64), '',
    'FULL_SOURCE_FILE_SHA256', '',
    'round3m-test-parser-v1', 'round3m-test-adapter-v1'
FROM (
    SELECT n, ((n - 1) % 3) + 1 AS family_n,
           ((n - 1) % 75) + 1 AS form_n
    FROM generate_series(1, 500) AS fixture(n)
) AS fixture
JOIN corpus.professional_acquisition_record AS record
  ON record.professional_acquisition_record_key =
     'round3m.test.record.' || n;

INSERT INTO audit.round3m_descriptor_review_receipt (
    review_receipt_key, descriptor_assertion_id, receipt_version,
    reviewer_id_or_pseudonymous_code, reviewer_role,
    review_actor_type, receipt_origin_code,
    human_event_evidence_sha256, review_protocol_version,
    decision, decision_reason, evidence_locator, reviewed_at,
    adjudication_status, previous_decision
)
SELECT
    'round3m.test.review.' || descriptor_assertion_id,
    descriptor_assertion_id, 1, 'human-reviewer-fixture-1',
    'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
    'HUMAN_REVIEW_IMPORT', repeat('9', 64),
    'round3m-human-review-fixture-v1', 'CONFIRM_DESCRIPTOR',
    'Transaction-local positive human-review fixture.',
    'fixture://review/' || descriptor_assertion_id,
    '2026-08-28T01:04:00Z', 'NOT_REQUIRED',
    'PROVISIONAL_MACHINE_CLASSIFIED'
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key LIKE 'round3m.test.assertion.%';

UPDATE corpus.round3m_descriptor_assertion AS assertion
SET review_state = 'HUMAN_CONFIRMED',
    review_actor_type = 'HUMAN_REVIEWER',
    current_review_receipt_id = receipt.review_receipt_id
FROM audit.round3m_descriptor_review_receipt AS receipt
WHERE receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
  AND assertion.descriptor_assertion_key LIKE
      'round3m.test.assertion.%';

INSERT INTO corpus.round3m_descriptor_label_target (
    descriptor_assertion_id, target_ordinal, output_label_key,
    normalization_decision, review_receipt_id
)
SELECT
    assertion.descriptor_assertion_id, 1,
    'round3m.test.label.' ||
        split_part(assertion.normalized_candidate_form, '-', 2),
    'EXACT_CANONICAL_TARGET', assertion.current_review_receipt_id
FROM corpus.round3m_descriptor_assertion AS assertion
WHERE assertion.descriptor_assertion_key LIKE
      'round3m.test.assertion.%';

DO $positive_gate$
DECLARE
    metric audit.v_round3m_descriptor_gate_metrics%ROWTYPE;
BEGIN
    SELECT * INTO STRICT metric
    FROM audit.v_round3m_descriptor_gate_metrics;

    IF metric.reviewed_p1_p2_strict_assertion_count <> 500
       OR metric.reviewed_descriptor_bearing_record_count <> 500
       OR metric.reviewed_unique_normalized_form_count <> 75
       OR metric.reviewed_independent_source_family_count <> 3
       OR metric.source_provenance_completeness <> 1
       OR metric.label_provenance_completeness <> 1
       OR metric.source_and_label_provenance_completeness <> 1
       OR metric.model_research_rights_rate <> 1 THEN
        RAISE EXCEPTION 'Round 3M positive metric reconciliation failed: %',
            row_to_json(metric);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM audit.v_round3m_descriptor_gate
        WHERE gate_name = 'GATE_500_EVALUATION'
          AND gate_pass
          AND NOT rights_blocker
          AND NOT data_blocker
          AND NOT review_blocker
          AND NOT training_authorization_pass
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=gate_500_evaluation expected pass without training authority';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.v_round3m_descriptor_gate
        WHERE gate_name <> 'GATE_500_EVALUATION' AND gate_pass
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=higher_gates_remain_closed failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=actual_human_receipts,model_rights,source_provenance,label_provenance,gate_500_evaluation,higher_gates_remain_closed PASS';
END
$positive_gate$;

SELECT pg_temp.expect_round3m_failure(
    'human_state_without_receipt',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET review_state = 'HUMAN_CONFIRMED',
            review_actor_type = 'HUMAN_REVIEWER',
            current_review_receipt_id = NULL
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_descriptor_assertion_review_shape_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'codex_cannot_create_human_receipt',
    $sql$
        INSERT INTO audit.round3m_descriptor_review_receipt (
            review_receipt_key, descriptor_assertion_id, receipt_version,
            supersedes_review_receipt_id,
            reviewer_id_or_pseudonymous_code, reviewer_role,
            review_actor_type, receipt_origin_code,
            human_event_evidence_sha256, review_protocol_version,
            decision, decision_reason, evidence_locator, reviewed_at,
            adjudication_status, previous_decision
        )
        SELECT 'round3m.test.bad.codex.human', descriptor_assertion_id, 2,
               current_review_receipt_id,
               'codex', 'PROFESSIONAL_SENSORY_REVIEWER',
               'HUMAN_REVIEWER', 'CODEX_SOURCE_AUDIT', NULL,
               'round3m-test-v1', 'CONFIRM_DESCRIPTOR',
               'Invalid impersonated human receipt.', 'fixture://bad',
               '2026-08-28T01:05:00Z', 'NOT_REQUIRED',
               'HUMAN_CONFIRMED'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_human_review_receipt_origin_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'public_visibility_not_model_permission',
    $sql$
        INSERT INTO evidence.round3m_descriptor_rights_decision (
            rights_decision_id, rights_scope_id, decision_version,
            source_route_id, publication_layer, source_field_label,
            public_discovery, internal_research_analysis,
            derived_research_data, model_research,
            deployment_or_commercial_model, raw_redistribution,
            decision_authority_code, decision_actor_type, decision_basis,
            evidence_locator, decided_at
        ) VALUES (
            'round3m.test.rights.bad.public', 'round3m.test.scope.bad', 1,
            'round3m.test.route.1', 'PRIMARY_JURY_DESCRIPTION',
            'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
            'PENDING', 'AFFIRMATIVE', 'PENDING', 'PROHIBITED',
            'PROJECT_RIGHTS_AUDIT', 'CODEX_SOURCE_AUDITOR',
            'Public visibility only.', 'fixture://public',
            '2026-08-28T01:05:00Z'
        )
    $sql$,
    '23514', 'round3m_public_visibility_not_model_permission_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'secondary_layer_cannot_double_credit_primary_observation',
    $sql$
        INSERT INTO corpus.round3m_descriptor_assertion (
            descriptor_assertion_key, professional_acquisition_record_id,
            effective_record_key, edition_year, source_artifact_id,
            source_route_id, schema_signature_id, publication_layer,
            source_field_label, source_field_label_sha256,
            source_selector_or_locator,
            source_page_or_record_locator, source_observation_key,
            raw_field_text, raw_field_text_sha256,
            atomic_source_text, atomic_source_text_sha256,
            text_storage_state, source_text_non_storage_reason,
            source_language, descriptor_class,
            source_native_lexical_form,
            source_native_lexical_form_sha256,
            normalized_candidate_form, normalized_candidate_form_sha256,
            normalization_method_code, evidence_tier,
            evidence_origin_type, origin_decision_basis,
            origin_evidence_locator, review_state, review_actor_type,
            rights_decision_id, source_retrieved_at, source_file_sha256,
            route_index_sha256, source_file_sha256_scope,
            source_file_nonstorage_reason,
            parser_version, adapter_version
        )
        SELECT 'round3m.test.duplicate.secondary',
               professional_acquisition_record_id, effective_record_key,
               edition_year, 'round3m.test.artifact.1',
               'round3m.test.route.1', 'round3m.test.schema.1',
               'PRIMARY_JURY_DESCRIPTION', 'Top Jury Descriptions',
               source_field_label_sha256,
               '#secondary', source_page_or_record_locator,
               source_observation_key, raw_field_text,
               raw_field_text_sha256, atomic_source_text,
               atomic_source_text_sha256, text_storage_state,
               source_text_non_storage_reason,
               source_language, descriptor_class,
               source_native_lexical_form,
               source_native_lexical_form_sha256,
               normalized_candidate_form, normalized_candidate_form_sha256,
               normalization_method_code, evidence_tier,
               evidence_origin_type, origin_decision_basis,
               origin_evidence_locator,
               'PROVISIONAL_MACHINE_CLASSIFIED',
               'CODEX_SOURCE_AUDITOR', 'round3m.test.rights.1',
               source_retrieved_at, source_file_sha256,
               route_index_sha256, source_file_sha256_scope,
               source_file_nonstorage_reason,
               parser_version, adapter_version
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23505', 'round3m_descriptor_observation_canonical_uq'
);

SELECT pg_temp.expect_round3m_failure(
    'cross_record_coassertion_rejected',
    $sql$
        INSERT INTO corpus.round3m_coassertion_event (
            coassertion_event_key, coassertion_set_key,
            effective_record_key, source_observation_key,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id, generated_by_version
        )
        SELECT 'round3m.test.bad.pair', 'round3m.test.bad.set',
               left_assertion.effective_record_key,
               left_assertion.source_observation_key,
               least(left_assertion.descriptor_assertion_id,
                     right_assertion.descriptor_assertion_id),
               greatest(left_assertion.descriptor_assertion_id,
                        right_assertion.descriptor_assertion_id),
               'round3m-test-pair-v1'
        FROM corpus.round3m_descriptor_assertion AS left_assertion
        CROSS JOIN corpus.round3m_descriptor_assertion AS right_assertion
        WHERE left_assertion.descriptor_assertion_key =
              'round3m.test.assertion.1'
          AND right_assertion.descriptor_assertion_key =
              'round3m.test.assertion.2'
    $sql$,
    '23514', 'round3m_coassertion_effective_record_boundary_ck'
);

-- Queue identities precede provisional and purpose-specific rights rows.
INSERT INTO audit.round3m_descriptor_review_queue_item (
    review_queue_id, descriptor_assertion_id, professional_record_id,
    source_family_id, source_route_id, edition_id, edition_year,
    source_artifact_id, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    raw_record_sha256, source_locator, source_language,
    source_text_sha256, source_text_storage_state,
    source_text_non_storage_reason, source_field_contract,
    publication_layer, descriptor_class, evidence_tier,
    review_state, review_actor_type, current_disposition,
    disposition_reason_code, human_review_required, model_eligible,
    decision_effective_date
) VALUES (
    'round3m.test.queue', 'round3m.test.hash.only',
    'round3m.test.bridge.record', 'round3m.test.family.1',
    'round3m.test.route.1', '2021', 2021,
    'round3m.test.artifact.1', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '',
    '', 'fixture://queue', 'en', repeat('e', 64),
    'HASH_ONLY', 'Raw source text is not stored in the public fixture.',
    'round3m.test.schema.1', 'PRIMARY_JURY_DESCRIPTION',
    'STRICT_FLAVOR', 'P2', 'PROVISIONAL_MACHINE_CLASSIFIED',
    'AUTOMATED_PARSER', 'HUMAN_REVIEW_REQUIRED',
    'LIVE_HASH_ONLY_CANDIDATE_REQUIRES_HUMAN_REVIEW',
    TRUE, FALSE, '2026-08-28'
);

INSERT INTO audit.round3m_descriptor_provisional_decision (
    decision_id, review_queue_id, descriptor_assertion_id,
    current_disposition, descriptor_class, review_state,
    review_actor_type, review_protocol_version, decision_reason_code,
    decision_basis, evidence_locator, source_file_sha256,
    route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, source_text_sha256,
    human_confirmed, expert_adjudicated,
    counts_as_reviewed_descriptor, model_eligible,
    decision_effective_date
) VALUES (
    'round3m.test.provisional.hash.only', 'round3m.test.queue',
    'round3m.test.hash.only', 'HUMAN_REVIEW_REQUIRED',
    'STRICT_FLAVOR', 'PROVISIONAL_MACHINE_CLASSIFIED',
    'AUTOMATED_PARSER', 'round3m-descriptor-review-v1',
    'LIVE_HASH_ONLY_CANDIDATE_REQUIRES_HUMAN_REVIEW',
    'Machine extraction is provisional and is not human review.',
    'fixture://queue', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '', repeat('e', 64),
    FALSE, FALSE, FALSE, FALSE, '2026-08-28'
);

INSERT INTO evidence.round3m_candidate_rights_decision (
    rights_decision_id, descriptor_assertion_id,
    source_artifact_id, purpose, rights_state, decision_basis,
    rights_evidence_locator, review_actor_type,
    model_eligibility_effect
) VALUES (
    'round3m.test.candidate.rights.public',
    'round3m.test.hash.only', 'round3m.test.artifact.1',
    'PUBLIC_DISCOVERY', 'UNKNOWN',
    'Machine-carried rights state is not affirmative permission.',
    'fixture://rights-unknown', 'AUTOMATED_PARSER',
    'INELIGIBLE_PENDING_OR_UNKNOWN_RIGHTS_AND_NO_HUMAN_REVIEW'
);

INSERT INTO competition.round3m_effective_record_bridge (
    round3m_effective_record_id, effective_record_key,
    series_id, edition_id, edition_year, category_id, round_id,
    subject_kind, entry_or_lot_id, preparation_service_code,
    preparation_evidence_locator, source_route_id, source_artifact_id,
    source_record_locator, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    record_identity_sha256, identity_resolution_state,
    synthetic_generated, preparation_inferred_from_descriptor
) VALUES (
    'round3m.test.bridge.record', 'round3m.test.bridge.effective',
    'round3m.test.series.1', 'round3m.test.edition.1', 2021,
    'cupping', 'final', 'LOT', 'lot-hash-only',
    'green_competition_cupping', 'fixture://protocol/fresh-cupping',
    'round3m.test.route.1', 'round3m.test.artifact.1',
    'fixture://queue', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '', repeat('6', 64),
    'SOURCE_NATIVE_PROVISIONAL', FALSE, FALSE
);

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, round3m_effective_record_id,
    effective_record_key, edition_year, source_artifact_id,
    source_route_id, schema_signature_id, publication_layer,
    source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256, text_storage_state,
    source_text_non_storage_reason, source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator,
    review_state, review_actor_type, rights_decision_id,
    source_retrieved_at, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version, provisional_decision_id
) VALUES (
    'round3m.test.hash.only', 'round3m.test.bridge.record',
    'round3m.test.bridge.effective', 2021,
    'round3m.test.artifact.1', 'round3m.test.route.1',
    'round3m.test.schema.1', 'PRIMARY_JURY_DESCRIPTION',
    'Top Jury Descriptions',
    audit.round3i_utf8_sha256('Top Jury Descriptions'),
    '#top-jury', 'fixture://queue',
    'round3m.test.observation.hash.only', NULL, repeat('f', 64),
    NULL, repeat('e', 64), 'HASH_ONLY',
    'Raw source text is not stored in the public fixture.',
    'en', 'STRICT_FLAVOR', NULL, repeat('e', 64),
    NULL, '', 'NONE', 'P2',
    'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION',
    'The source field is explicitly labelled as a jury description.',
    'fixture://queue', 'PROVISIONAL_MACHINE_CLASSIFIED',
    'AUTOMATED_PARSER', 'round3m.test.rights.1',
    '2026-08-28T01:01:00Z', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '',
    'round3m-test-parser-v1', 'round3m-test-adapter-v1',
    'round3m.test.provisional.hash.only'
);

DO $hash_only_positive$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.hash.only'
          AND round3m_effective_record_id = 'round3m.test.bridge.record'
          AND source_native_lexical_form IS NULL
          AND source_native_lexical_form_sha256 = repeat('e', 64)
          AND current_review_receipt_id IS NULL
          AND provisional_decision_id =
              'round3m.test.provisional.hash.only'
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=hash_only_bridge_and_provisional_lineage failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=hash_only_bridge_and_provisional_lineage,candidate_rights_artifact_enum PASS';
END
$hash_only_positive$;

SELECT pg_temp.expect_round3m_failure(
    'not_applicable_model_rights_never_supports_eligibility',
    $sql$
        INSERT INTO evidence.round3m_candidate_rights_decision (
            rights_decision_id, descriptor_assertion_id,
            source_artifact_id, purpose, rights_state, decision_basis,
            rights_evidence_locator, review_actor_type,
            model_eligibility_effect
        ) VALUES (
            'round3m.test.candidate.rights.na.2',
            'round3m.test.hash.only', 'round3m.test.artifact.1',
            'MODEL_RESEARCH', 'NOT_APPLICABLE',
            'NA cannot support eligibility.', 'fixture://rights-na',
            'CODEX_SOURCE_AUDITOR', 'SUPPORTS_MODEL_ELIGIBILITY'
        )
    $sql$,
    '23514', 'round3m_candidate_public_visibility_not_permission_ck'
);

DO $final_validation$
DECLARE
    failure_count BIGINT;
BEGIN
    SELECT count(*) INTO failure_count
    FROM audit.run_round3m_gate_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0;

    IF failure_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_CONSTRAINT=validation_contract failures=%',
            failure_count;
    END IF;
    IF EXISTS (
        SELECT 1
        FROM audit.v_current_professional_training_readiness
        WHERE current_training_authorization_pass
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=no_training_authority failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_CONSTRAINT=validation_contract,no_training_authority,saturation_false PASS';
END
$final_validation$;

SELECT check_key, violation_count, passed
FROM audit.run_round3m_gate_validation_queries()
ORDER BY check_key;

ROLLBACK;

\echo ROUND3M_GATE_SCHEMA_PASS
