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

SELECT pg_temp.expect_round3m_failure(
    'one_governed_origin_cannot_split_into_multiple_families',
    $sql$
        INSERT INTO evidence.round3m_independent_source_family (
            independent_source_family_id, organizer_id, family_name,
            independence_basis, rights_lineage_id,
            admitted_for_descriptor_research
        ) VALUES (
            'round3m.test.family.split', 'round3m.test.organizer.1',
            'Invalid split family',
            'Same organizer and rights origin cannot inflate diversity.',
            'round3m.test.rights.lineage.1', TRUE
        )
    $sql$,
    '23505', 'round3m_independent_source_family_origin_uq'
);

SELECT pg_temp.expect_round3m_failure(
    'route_must_match_family_organizer_and_rights_scope',
    $sql$
        INSERT INTO evidence.round3m_source_route (
            source_route_id, independent_source_family_id,
            organizer_id, publication_host, canonical_url,
            route_pattern, route_disposition, rights_lineage_id,
            mirror_lineage_id, discovered_at
        ) VALUES (
            'round3m.test.route.bad-family-scope',
            'round3m.test.family.1', 'round3m.test.organizer.2',
            'bad-family.example.test',
            'https://bad-family.example.test/results',
            '/results/{edition}', 'PROVENANCE_PILOT_ONLY',
            'round3m.test.rights.lineage.2',
            'round3m.test.mirror.bad-family',
            '2026-08-28T01:00:00Z'
        )
    $sql$,
    '23514', 'round3m_source_route_family_scope_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'source_route_family_identity_is_immutable',
    $sql$
        UPDATE evidence.round3m_source_route
        SET independent_source_family_id = 'round3m.test.family.2',
            organizer_id = 'round3m.test.organizer.2',
            rights_lineage_id = 'round3m.test.rights.lineage.2'
        WHERE source_route_id = 'round3m.test.route.1'
    $sql$,
    '23514', 'round3m_source_route_identity_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'source_family_descriptor_admission_is_immutable',
    $sql$
        UPDATE evidence.round3m_independent_source_family
        SET admitted_for_descriptor_research = FALSE
        WHERE independent_source_family_id = 'round3m.test.family.1'
    $sql$,
    '23514', 'round3m_source_family_identity_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'mirror_lineage_cannot_span_independent_families',
    $sql$
        INSERT INTO evidence.round3m_source_route (
            source_route_id, independent_source_family_id,
            organizer_id, publication_host, canonical_url,
            route_pattern, route_disposition, rights_lineage_id,
            mirror_lineage_id, discovered_at
        )
        SELECT 'round3m.test.route.cross-family-mirror',
               'round3m.test.family.2', family.organizer_id,
               'cross-family-mirror.example.test',
               'https://cross-family-mirror.example.test/results',
               '/results', 'PRIORITY_DESCRIPTOR_ROUTE',
               family.rights_lineage_id,
               source.mirror_lineage_id,
               '2026-08-28T01:00:00Z'
        FROM evidence.round3m_independent_source_family AS family
        CROSS JOIN evidence.round3m_source_route AS source
        WHERE family.independent_source_family_id =
              'round3m.test.family.2'
          AND source.source_route_id = 'round3m.test.route.1'
    $sql$,
    '23514', 'round3m_mirror_lineage_one_family_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'resolved_mirror_needs_credit_route_before_second_route',
    $sql$
        INSERT INTO evidence.round3m_source_route (
            source_route_id, independent_source_family_id,
            organizer_id, publication_host, canonical_url,
            route_pattern, route_disposition, rights_lineage_id,
            mirror_lineage_id, discovered_at
        )
        SELECT 'round3m.test.route.uncredited-mirror',
               source.independent_source_family_id,
               source.organizer_id, 'uncredited-mirror.example.test',
               'https://uncredited-mirror.example.test/results',
               source.route_pattern, 'PROVENANCE_PILOT_ONLY',
               source.rights_lineage_id, source.mirror_lineage_id,
               '2026-08-28T01:00:00Z'
        FROM evidence.round3m_source_route AS source
        WHERE source.source_route_id = 'round3m.test.route.1'
    $sql$,
    '23514',
    'round3m_mirror_credit_required_before_additional_route_ck'
);

INSERT INTO evidence.round3m_mirror_lineage_credit_route (
    mirror_lineage_id, independent_source_family_id,
    canonical_source_route_id, decision_basis, evidence_locator,
    decided_at
)
SELECT mirror_lineage_id, independent_source_family_id, source_route_id,
       'Transaction-local canonical publication selection fixture.',
       'fixture://mirror-credit/lineage-1',
       '2026-08-28T01:00:00Z'
FROM evidence.round3m_source_route
WHERE source_route_id = 'round3m.test.route.1';

INSERT INTO evidence.round3m_source_route (
    source_route_id, independent_source_family_id,
    organizer_id, publication_host, canonical_url,
    route_pattern, route_disposition, rights_lineage_id,
    mirror_lineage_id, discovered_at
)
SELECT 'round3m.test.route.mirror.1',
       source.independent_source_family_id,
       source.organizer_id, 'mirror1.example.test',
       'https://mirror1.example.test/results',
       source.route_pattern, 'PROVENANCE_PILOT_ONLY',
       source.rights_lineage_id, source.mirror_lineage_id,
       '2026-08-28T01:00:00Z'
FROM evidence.round3m_source_route AS source
WHERE source.source_route_id = 'round3m.test.route.1';

CREATE TEMP TABLE round3m_mirror_assertion_probe (
    source_route_id TEXT NOT NULL,
    descriptor_class TEXT NOT NULL,
    deduplication_disposition TEXT NOT NULL,
    mirror_group TEXT
) ON COMMIT DROP;

CREATE TRIGGER round3m_mirror_assertion_probe_biu
BEFORE INSERT OR UPDATE ON round3m_mirror_assertion_probe
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_round3m_resolved_mirror_credit();

SELECT pg_temp.expect_round3m_failure(
    'noncanonical_mirror_route_cannot_receive_descriptor_credit',
    $sql$
        INSERT INTO round3m_mirror_assertion_probe (
            source_route_id, descriptor_class,
            deduplication_disposition, mirror_group
        ) VALUES (
            'round3m.test.route.mirror.1', 'STRICT_FLAVOR',
            'CANONICAL', NULL
        )
    $sql$,
    '23514', 'round3m_resolved_mirror_noncanonical_ck'
);

INSERT INTO round3m_mirror_assertion_probe (
    source_route_id, descriptor_class,
    deduplication_disposition, mirror_group
) VALUES (
    'round3m.test.route.mirror.1', 'STRICT_FLAVOR',
    'MIRROR_PUBLICATION', 'round3m.test.mirror.lineage.1'
);

SELECT pg_temp.expect_round3m_failure(
    'mirror_credit_route_is_immutable',
    $sql$
        UPDATE evidence.round3m_mirror_lineage_credit_route
        SET evidence_locator = 'fixture://mirror-credit/mutated'
        WHERE mirror_lineage_id = 'round3m.test.mirror.lineage.1'
    $sql$,
    '23514', 'round3m_immutable_evidence_ck'
);

DO $resolved_mirror_credit_positive$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM round3m_mirror_assertion_probe
        WHERE deduplication_disposition = 'MIRROR_PUBLICATION'
          AND mirror_group = 'round3m.test.mirror.lineage.1'
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=resolved_mirror_is_preserved_without_credit failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=resolved_mirror_is_preserved_without_credit PASS';
END
$resolved_mirror_credit_positive$;

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

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    round3l_source_attempt_id, governed_locator, source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    file_size_bytes, storage_state, non_storage_reason,
    parser_version, adapter_version
)
SELECT
    'round3m.test.artifact.1-reidentified', source_route_id,
    schema_signature_id, round3l_source_attempt_id,
    governed_locator || '#alternate-publication-locator',
    source_retrieved_at, source_file_sha256, route_index_sha256,
    'RENAMED_SCOPE_ALIAS_NOT_IDENTITY', source_file_nonstorage_reason,
    file_size_bytes, storage_state,
    'Transaction-local re-identification negative fixture.',
    parser_version, adapter_version
FROM evidence.round3m_source_artifact
WHERE source_artifact_id = 'round3m.test.artifact.1';

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

SELECT pg_temp.expect_round3m_failure(
    'rights_successor_cannot_drift_publication_field_scope',
    $sql$
        INSERT INTO evidence.round3m_descriptor_rights_decision (
            rights_decision_id, rights_scope_id, decision_version,
            supersedes_rights_decision_id, source_route_id,
            publication_layer, source_field_label,
            public_discovery, internal_research_analysis,
            derived_research_data, model_research,
            deployment_or_commercial_model, raw_redistribution,
            decision_authority_code, decision_actor_type,
            decision_basis, evidence_locator, decided_at
        ) VALUES (
            'round3m.test.rights.scope-drift',
            'round3m.test.scope.1', 2, 'round3m.test.rights.1',
            'round3m.test.route.1', 'PRIMARY_JURY_DESCRIPTION',
            'Other Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
            'AFFIRMATIVE', 'AFFIRMATIVE', 'PENDING', 'PROHIBITED',
            'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
            'Invalid field-scope drift fixture.',
            'fixture://rights/scope-drift',
            '2026-08-28T01:03:00Z'
        )
    $sql$,
    '23514', 'round3m_descriptor_rights_lineage_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'deployment_affirmative_requires_internal_and_model_rights',
    $sql$
        INSERT INTO evidence.round3m_descriptor_rights_decision (
            rights_decision_id, rights_scope_id, decision_version,
            source_route_id, publication_layer, source_field_label,
            public_discovery, internal_research_analysis,
            derived_research_data, model_research,
            deployment_or_commercial_model, raw_redistribution,
            decision_authority_code, decision_actor_type,
            decision_basis, evidence_locator, decided_at
        ) VALUES (
            'round3m.test.rights.bad-deployment-chain',
            'round3m.test.scope.bad-deployment-chain', 1,
            'round3m.test.route.1', 'PRIMARY_JURY_DESCRIPTION',
            'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
            'AFFIRMATIVE', 'PENDING', 'AFFIRMATIVE', 'PROHIBITED',
            'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
            'Invalid deployment-chain fixture.',
            'fixture://rights/bad-deployment-chain',
            '2026-08-28T01:03:00Z'
        )
    $sql$,
    '23514', 'round3m_deployment_requires_model_rights_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'future_rights_decision_cannot_be_current',
    $sql$
        INSERT INTO evidence.round3m_descriptor_rights_decision (
            rights_decision_id, rights_scope_id, decision_version,
            source_route_id, publication_layer, source_field_label,
            public_discovery, internal_research_analysis,
            derived_research_data, model_research,
            deployment_or_commercial_model, raw_redistribution,
            decision_authority_code, decision_actor_type,
            decision_basis, evidence_locator, decided_at
        ) VALUES (
            'round3m.test.rights.future', 'round3m.test.scope.future', 1,
            'round3m.test.route.1', 'PRIMARY_JURY_DESCRIPTION',
            'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
            'AFFIRMATIVE', 'AFFIRMATIVE', 'PENDING', 'PROHIBITED',
            'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
            'Future rights evidence must not become current.',
            'fixture://rights/future', transaction_timestamp() + interval '1 day'
        )
    $sql$,
    '23514', 'round3m_descriptor_rights_chronology_ck'
);

DO $natural_rights_scope_conflict_fails_closed$
DECLARE
    rollback_marker CONSTANT TEXT :=
        'round3m-natural-rights-conflict-rollback';
BEGIN
    BEGIN
        INSERT INTO evidence.round3m_descriptor_rights_decision (
            rights_decision_id, rights_scope_id, decision_version,
            source_route_id, publication_layer, source_field_label,
            public_discovery, internal_research_analysis,
            derived_research_data, model_research,
            deployment_or_commercial_model, raw_redistribution,
            decision_authority_code, decision_actor_type,
            decision_basis, evidence_locator, decided_at
        ) VALUES (
            'round3m.test.rights.conflicting-natural-scope',
            'round3m.test.scope.conflicting-natural-scope', 1,
            'round3m.test.route.1', 'PRIMARY_JURY_DESCRIPTION',
            'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
            'AFFIRMATIVE', 'PENDING', 'PENDING', 'PROHIBITED',
            'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
            'Transaction-local conflicting natural-scope fixture.',
            'fixture://rights/conflicting-natural-scope',
            '2026-08-28T01:03:00Z'
        );

        IF NOT EXISTS (
            SELECT 1
            FROM evidence.v_round3m_current_descriptor_rights
            WHERE source_route_id = 'round3m.test.route.1'
              AND publication_layer = 'PRIMARY_JURY_DESCRIPTION'
              AND source_field_label = 'Top Jury Descriptions'
              AND NOT unambiguous_current_decision
        ) THEN
            RAISE EXCEPTION
                'conflicting current natural rights scope did not fail closed';
        END IF;

        RAISE EXCEPTION '%', rollback_marker;
    EXCEPTION WHEN RAISE_EXCEPTION THEN
        IF SQLERRM <> rollback_marker THEN
            RAISE;
        END IF;
    END;

    IF EXISTS (
        SELECT 1
        FROM evidence.round3m_descriptor_rights_decision
        WHERE rights_decision_id =
              'round3m.test.rights.conflicting-natural-scope'
    ) THEN
        RAISE EXCEPTION 'natural-scope conflict rollback failed';
    END IF;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=conflicting_current_natural_rights_scope_fails_closed PASS';
END
$natural_rights_scope_conflict_fails_closed$;

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

SELECT pg_temp.expect_round3m_failure(
    'reidentified_artifact_and_observation_cannot_duplicate_bounded_assertion',
    $sql$
        INSERT INTO corpus.round3m_descriptor_assertion (
            descriptor_assertion_key,
            professional_acquisition_record_id,
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
            normalized_candidate_form,
            normalized_candidate_form_sha256,
            normalization_method_code, evidence_tier,
            evidence_origin_type, origin_decision_basis,
            origin_evidence_locator, review_state, review_actor_type,
            rights_decision_id, source_retrieved_at,
            source_file_sha256, route_index_sha256,
            source_file_sha256_scope, source_file_nonstorage_reason,
            parser_version, adapter_version
        )
        SELECT
            'round3m.test.assertion.reidentified-duplicate',
            alternate.professional_acquisition_record_id,
            alternate.effective_record_key, alternate.edition_year,
            'round3m.test.artifact.1-reidentified', base.source_route_id,
            base.schema_signature_id, base.publication_layer,
            base.source_field_label, base.source_field_label_sha256,
            base.source_selector_or_locator,
            base.source_page_or_record_locator,
            'round3m.test.observation.reidentified-duplicate',
            base.raw_field_text, base.raw_field_text_sha256,
            base.atomic_source_text, base.atomic_source_text_sha256,
            base.text_storage_state, base.source_text_non_storage_reason,
            base.source_language, base.descriptor_class,
            base.source_native_lexical_form,
            base.source_native_lexical_form_sha256,
            base.normalized_candidate_form,
            base.normalized_candidate_form_sha256,
            base.normalization_method_code, base.evidence_tier,
            base.evidence_origin_type, base.origin_decision_basis,
            base.origin_evidence_locator,
            'PROVISIONAL_MACHINE_CLASSIFIED',
            'CODEX_SOURCE_AUDITOR', base.rights_decision_id,
            base.source_retrieved_at, base.source_file_sha256,
            base.route_index_sha256, 'RENAMED_SCOPE_ALIAS_NOT_IDENTITY',
            base.source_file_nonstorage_reason, base.parser_version,
            base.adapter_version
        FROM corpus.round3m_descriptor_assertion AS base
        CROSS JOIN corpus.professional_acquisition_record AS alternate
        WHERE base.descriptor_assertion_key = 'round3m.test.assertion.1'
          AND alternate.professional_acquisition_record_key =
              'round3m.test.record.4'
    $sql$,
    '23505', 'round3m_countable_source_assertion_natural_uq'
);

INSERT INTO evidence.round3m_independent_source_family (
    independent_source_family_id, organizer_id, family_name,
    independence_basis, rights_lineage_id,
    admitted_for_descriptor_research
) VALUES (
    'round3m.test.family.unadmitted',
    'round3m.test.organizer.unadmitted',
    'Round 3M unadmitted fixture family',
    'Transaction-local family retained in discovery but not admitted.',
    'round3m.test.rights.lineage.unadmitted', FALSE
);

INSERT INTO evidence.round3m_source_route (
    source_route_id, independent_source_family_id, organizer_id,
    publication_host, canonical_url, route_pattern,
    route_disposition, rights_lineage_id, mirror_lineage_id,
    discovered_at
) VALUES (
    'round3m.test.route.unadmitted',
    'round3m.test.family.unadmitted',
    'round3m.test.organizer.unadmitted',
    'unadmitted.example.test',
    'https://unadmitted.example.test/results', '/results',
    'PROVENANCE_PILOT_ONLY',
    'round3m.test.rights.lineage.unadmitted',
    'round3m.test.mirror.lineage.unadmitted',
    '2026-08-28T01:00:00Z'
);

INSERT INTO evidence.round3m_source_schema_signature (
    schema_signature_id, source_route_id, schema_version, host,
    route_pattern, edition_or_period, field_labels_json,
    selectors_json, publication_layer_rules_json,
    field_origin_assumptions_json, known_ambiguity,
    positive_fixture_locator, negative_fixture_locator,
    adapter_version, live_positive_fixture_present, validation_status
) VALUES (
    'round3m.test.schema.unadmitted',
    'round3m.test.route.unadmitted', 1,
    'unadmitted.example.test', '/results', '2021',
    '["Top Jury Descriptions"]'::JSONB,
    '{"field":"#top-jury"}'::JSONB,
    '{"Top Jury Descriptions":"PRIMARY_JURY_DESCRIPTION"}'::JSONB,
    '{"Top Jury Descriptions":"explicit jury attribution"}'::JSONB,
    'Transaction-local unadmitted-family fixture.',
    'https://unadmitted.example.test/results#positive',
    'https://unadmitted.example.test/results#negative',
    'round3m-test-adapter-v1', TRUE, 'VALIDATED'
);

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    governed_locator, source_retrieved_at, source_file_sha256,
    route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, file_size_bytes, storage_state,
    non_storage_reason, parser_version, adapter_version
) VALUES (
    'round3m.test.artifact.unadmitted',
    'round3m.test.route.unadmitted',
    'round3m.test.schema.unadmitted',
    'https://unadmitted.example.test/results#snapshot',
    '2026-08-28T01:01:00Z', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '', 1024,
    'HASH_AND_LOCATOR_ONLY',
    'Transaction-local fixture stores hash and locator only.',
    'round3m-test-parser-v1', 'round3m-test-adapter-v1'
);

INSERT INTO evidence.round3m_descriptor_rights_decision (
    rights_decision_id, rights_scope_id, decision_version,
    source_route_id, publication_layer, source_field_label,
    public_discovery, internal_research_analysis,
    derived_research_data, model_research,
    deployment_or_commercial_model, raw_redistribution,
    decision_authority_code, decision_actor_type, decision_basis,
    evidence_locator, decided_at
) VALUES (
    'round3m.test.rights.unadmitted',
    'round3m.test.scope.unadmitted', 1,
    'round3m.test.route.unadmitted', 'PRIMARY_JURY_DESCRIPTION',
    'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
    'AFFIRMATIVE', 'AFFIRMATIVE', 'PENDING', 'PROHIBITED',
    'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
    'Transaction-local affirmative rights fixture.',
    'fixture://rights/unadmitted', '2026-08-28T01:02:00Z'
);

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, professional_acquisition_record_id,
    effective_record_key, edition_year, source_artifact_id,
    source_route_id, schema_signature_id, publication_layer,
    source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
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
SELECT 'round3m.test.assertion.unadmitted',
       professional_acquisition_record_id, effective_record_key,
       edition_year, 'round3m.test.artifact.unadmitted',
       'round3m.test.route.unadmitted',
       'round3m.test.schema.unadmitted', publication_layer,
       source_field_label, source_field_label_sha256,
       '#top-jury-unadmitted', 'record-1#top-jury-unadmitted',
       'round3m.test.observation.unadmitted',
       'Unadmitted family descriptor',
       audit.round3i_utf8_sha256('Unadmitted family descriptor'),
       'unadmitted descriptor',
       audit.round3i_utf8_sha256('unadmitted descriptor'),
       'REVIEWED_EXCERPT', '', source_language, 'STRICT_FLAVOR',
       'unadmitted descriptor',
       audit.round3i_utf8_sha256('unadmitted descriptor'),
       'unadmitted descriptor',
       audit.round3i_utf8_sha256('unadmitted descriptor'),
       'UNICODE_NFC_WHITESPACE_CASE', 'P2', evidence_origin_type,
       origin_decision_basis, 'record-1#top-jury-unadmitted',
       'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
       'round3m.test.rights.unadmitted', source_retrieved_at,
       source_file_sha256, route_index_sha256,
       source_file_sha256_scope, source_file_nonstorage_reason,
       parser_version, adapter_version
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key = 'round3m.test.assertion.1';

DO $unadmitted_family_is_discovered_but_not_staged$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM evidence.v_round3m_discovered_source_universe
        WHERE source_route_id = 'round3m.test.route.unadmitted'
    ) OR EXISTS (
        SELECT 1
        FROM corpus.v_round3m_research_staged_descriptor_universe
        WHERE descriptor_assertion_key =
              'round3m.test.assertion.unadmitted'
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=unadmitted_family_universe_separation failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_NEGATIVE=unadmitted_family_retained_in_discovery_but_excluded_from_research_staged PASS';
END
$unadmitted_family_is_discovered_but_not_staged$;

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
WHERE descriptor_assertion_key ~ '^round3m[.]test[.]assertion[.][0-9]+$';

UPDATE corpus.round3m_descriptor_assertion AS assertion
SET review_state = 'HUMAN_CONFIRMED',
    review_actor_type = 'HUMAN_REVIEWER',
    current_review_receipt_id = receipt.review_receipt_id
FROM audit.round3m_descriptor_review_receipt AS receipt
WHERE receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
  AND assertion.descriptor_assertion_key ~
      '^round3m[.]test[.]assertion[.][0-9]+$';

SELECT pg_temp.expect_round3m_failure(
    'future_human_review_cannot_enter_reviewed_universe',
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
        SELECT 'round3m.test.review.future', descriptor_assertion_id, 2,
               current_review_receipt_id, 'human-reviewer-fixture-1',
               'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
               'HUMAN_REVIEW_IMPORT', repeat('7', 64),
               'round3m-human-review-fixture-v2', 'CONFIRM_DESCRIPTOR',
               'Future review evidence must not count.',
               'fixture://review/future',
               transaction_timestamp() + interval '1 day',
               'NOT_REQUIRED', 'CONFIRM_DESCRIPTOR'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_descriptor_review_receipt_chronology_ck'
);

CREATE TEMP TABLE round3m_test_form_concept AS
WITH active_concept AS (
    SELECT concept_id, concept_key,
           row_number() OVER (ORDER BY concept_key) AS concept_ordinal,
           count(*) OVER () AS concept_count
    FROM kb.concept
    WHERE lifecycle_status_code = 'active'
      AND replacement_concept_id IS NULL
), form_number AS (
    SELECT generate_series(1, 75) AS form_ordinal
)
SELECT form.form_ordinal, concept.concept_id, concept.concept_key
FROM form_number AS form
JOIN active_concept AS concept
  ON concept.concept_ordinal =
     ((form.form_ordinal - 1) % concept.concept_count) + 1;

DO $round3m_test_concept_fixture$
BEGIN
    IF (SELECT count(*) FROM round3m_test_form_concept) <> 75 THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=governed_concept_fixture expected 75 mappings';
    END IF;
END
$round3m_test_concept_fixture$;

INSERT INTO audit.round3m_descriptor_label_mapping_receipt (
    label_mapping_receipt_id, descriptor_assertion_id,
    review_receipt_id, label_set_sha256, mapping_evidence_sha256,
    mapping_evidence_locator
)
SELECT
    'round3m.test.mapping.' || assertion.descriptor_assertion_id,
    assertion.descriptor_assertion_id,
    assertion.current_review_receipt_id,
    audit.round3i_utf8_sha256(
        '1' || chr(31) || concept.concept_key || chr(31) ||
        'EXACT_CANONICAL_TARGET' || chr(31) ||
        'concept:' || concept.concept_id::TEXT
    ),
    repeat('9', 64),
    'fixture://review/' || assertion.descriptor_assertion_id ||
        '#label-mapping'
FROM corpus.round3m_descriptor_assertion AS assertion
JOIN round3m_test_form_concept AS concept
  ON concept.form_ordinal =
     split_part(assertion.normalized_candidate_form, '-', 2)::INTEGER
WHERE assertion.descriptor_assertion_key ~
      '^round3m[.]test[.]assertion[.][0-9]+$';

INSERT INTO corpus.round3m_descriptor_label_target (
    descriptor_assertion_id, target_ordinal, output_label_key,
    normalization_decision, review_receipt_id,
    label_mapping_receipt_id, concept_id
)
SELECT
    assertion.descriptor_assertion_id, 1, concept.concept_key,
    'EXACT_CANONICAL_TARGET', assertion.current_review_receipt_id,
    'round3m.test.mapping.' || assertion.descriptor_assertion_id,
    concept.concept_id
FROM corpus.round3m_descriptor_assertion AS assertion
JOIN round3m_test_form_concept AS concept
  ON concept.form_ordinal =
     split_part(assertion.normalized_candidate_form, '-', 2)::INTEGER
WHERE assertion.descriptor_assertion_key ~
      '^round3m[.]test[.]assertion[.][0-9]+$';

SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
    corpus.round3m_label_mapping_set_target_ci IMMEDIATE;
SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
    corpus.round3m_label_mapping_set_target_ci DEFERRED;

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

DO $stale_review_supersession_negative$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.round3m_descriptor_review_receipt (
            review_receipt_key, descriptor_assertion_id,
            receipt_version, supersedes_review_receipt_id,
            reviewer_id_or_pseudonymous_code, reviewer_role,
            review_actor_type, receipt_origin_code,
            human_event_evidence_sha256, review_protocol_version,
            decision, decision_reason, evidence_locator, reviewed_at,
            adjudication_status, previous_decision
        )
        SELECT
            'round3m.test.review.stale-successor',
            descriptor_assertion_id, 2, current_review_receipt_id,
            'human-reviewer-fixture-1',
            'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
            'HUMAN_REVIEW_IMPORT', repeat('8', 64),
            'round3m-human-review-fixture-v2', 'CONFIRM_DESCRIPTOR',
            'Invalid stale-pointer supersession fixture.',
            'fixture://review/stale-successor',
            '2026-08-28T01:06:00Z', 'NOT_REQUIRED',
            'CONFIRM_DESCRIPTOR'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1';

        SET CONSTRAINTS audit.round3m_current_review_receipt_leaf_ci
            IMMEDIATE;
        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: stale_review_receipt_pointer_after_supersession';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_current_review_receipt_leaf_ck' THEN
            RAISE;
        END IF;
    END;

    SET CONSTRAINTS audit.round3m_current_review_receipt_leaf_ci DEFERRED;
    RAISE NOTICE
        'ROUND3M_NEGATIVE=stale_review_receipt_pointer_after_supersession SQLSTATE=% CONSTRAINT=% PASS',
        actual_state, actual_constraint;
END
$stale_review_supersession_negative$;

SELECT pg_temp.expect_round3m_failure(
    'review_successor_must_name_previous_decision',
    $sql$
        INSERT INTO audit.round3m_descriptor_review_receipt (
            review_receipt_key, descriptor_assertion_id,
            receipt_version, supersedes_review_receipt_id,
            reviewer_id_or_pseudonymous_code, reviewer_role,
            review_actor_type, receipt_origin_code,
            human_event_evidence_sha256, review_protocol_version,
            decision, decision_reason, evidence_locator, reviewed_at,
            adjudication_status, previous_decision
        )
        SELECT 'round3m.test.review.bad-previous',
               descriptor_assertion_id, 2, current_review_receipt_id,
               'human-reviewer-fixture-1',
               'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
               'HUMAN_REVIEW_IMPORT', repeat('7', 64),
               'round3m-human-review-fixture-v2',
               'CONFIRM_DESCRIPTOR',
               'Invalid predecessor-decision fixture.',
               'fixture://review/bad-previous',
               '2026-08-28T01:06:00Z', 'NOT_REQUIRED',
               'SOURCE_AUDIT_COMPLETE'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.52'
    $sql$,
    '23514', 'round3m_review_receipt_previous_decision_ck'
);

DO $review_supersession_positive$
DECLARE
    target_assertion_id BIGINT;
    successor_receipt_id BIGINT;
    leaf_violation_count BIGINT;
    minimum_label_support NUMERIC;
    multi_target_record_count BIGINT;
    label_provenance_rate NUMERIC;
    target_concept_id BIGINT;
    target_concept_key TEXT;
BEGIN
    SELECT assertion.descriptor_assertion_id
    INTO STRICT target_assertion_id
    FROM corpus.round3m_descriptor_assertion AS assertion
    WHERE assertion.descriptor_assertion_key =
          'round3m.test.assertion.51';

    INSERT INTO audit.round3m_descriptor_review_receipt (
        review_receipt_key, descriptor_assertion_id, receipt_version,
        supersedes_review_receipt_id,
        reviewer_id_or_pseudonymous_code, reviewer_role,
        review_actor_type, receipt_origin_code,
        human_event_evidence_sha256, review_protocol_version,
        decision, decision_reason, evidence_locator, reviewed_at,
        adjudication_status, previous_decision
    )
    SELECT
        'round3m.test.review.successor', descriptor_assertion_id, 2,
        current_review_receipt_id, 'human-reviewer-fixture-1',
        'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
        'HUMAN_REVIEW_IMPORT', repeat('8', 64),
        'round3m-human-review-fixture-v2', 'CONFIRM_DESCRIPTOR',
        'Transaction-local positive review successor fixture.',
        'fixture://review/successor', '2026-08-28T01:06:00Z',
        'NOT_REQUIRED', 'CONFIRM_DESCRIPTOR'
    FROM corpus.round3m_descriptor_assertion AS assertion
    WHERE assertion.descriptor_assertion_id = target_assertion_id
    RETURNING review_receipt_id INTO successor_receipt_id;

    IF EXISTS (
        SELECT 1
        FROM corpus.v_round3m_human_reviewed_descriptor_universe
        WHERE descriptor_assertion_id = target_assertion_id
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=superseded_receipt_excluded_from_human_universe failed';
    END IF;

    SELECT violation_count INTO STRICT leaf_violation_count
    FROM audit.run_round3m_gate_validation_queries()
    WHERE check_key = 'round3m.current_review_pointer_is_leaf';

    IF leaf_violation_count <> 1 THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=superseded_receipt_validation expected 1 got %',
            leaf_violation_count;
    END IF;

    UPDATE corpus.round3m_descriptor_assertion
    SET current_review_receipt_id = successor_receipt_id
    WHERE descriptor_assertion_id = target_assertion_id;

    SELECT target.concept_id, target.output_label_key
    INTO STRICT target_concept_id, target_concept_key
    FROM corpus.round3m_descriptor_label_target AS target
    WHERE target.descriptor_assertion_id = target_assertion_id
    ORDER BY target.review_receipt_id
    LIMIT 1;

    INSERT INTO audit.round3m_descriptor_label_mapping_receipt (
        label_mapping_receipt_id, descriptor_assertion_id,
        review_receipt_id, label_set_sha256,
        mapping_evidence_sha256, mapping_evidence_locator
    ) VALUES (
        'round3m.test.mapping.successor', target_assertion_id,
        successor_receipt_id,
        audit.round3i_utf8_sha256(
            '1' || chr(31) || target_concept_key || chr(31) ||
            'EXACT_CANONICAL_TARGET' || chr(31) ||
            'concept:' || target_concept_id::TEXT
        ),
        repeat('8', 64), 'fixture://review/successor#label-mapping'
    );

    -- Retain the predecessor-backed target as immutable history and add the
    -- successor-backed current target.  Only the latter may affect metrics.
    INSERT INTO corpus.round3m_descriptor_label_target (
        descriptor_assertion_id, target_ordinal, output_label_key,
        normalization_decision, review_receipt_id,
        label_mapping_receipt_id, concept_id
    ) VALUES (
        target_assertion_id, 1, target_concept_key,
        'EXACT_CANONICAL_TARGET', successor_receipt_id,
        'round3m.test.mapping.successor', target_concept_id
    );

    SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
        corpus.round3m_label_mapping_set_target_ci IMMEDIATE;
    SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
        corpus.round3m_label_mapping_set_target_ci DEFERRED;

    SET CONSTRAINTS audit.round3m_current_review_receipt_leaf_ci IMMEDIATE;
    SET CONSTRAINTS audit.round3m_current_review_receipt_leaf_ci DEFERRED;

    IF NOT EXISTS (
        SELECT 1
        FROM corpus.v_round3m_human_reviewed_descriptor_universe
        WHERE descriptor_assertion_id = target_assertion_id
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=current_leaf_review_successor failed';
    END IF;

    SELECT violation_count INTO STRICT leaf_violation_count
    FROM audit.run_round3m_gate_validation_queries()
    WHERE check_key = 'round3m.current_review_pointer_is_leaf';

    IF leaf_violation_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=current_leaf_validation expected 0 got %',
            leaf_violation_count;
    END IF;

    SELECT minimum_records_per_output_label,
           reviewed_multi_target_record_count,
           label_provenance_completeness
    INTO STRICT minimum_label_support, multi_target_record_count,
                label_provenance_rate
    FROM audit.v_round3m_descriptor_gate_metrics;

    IF minimum_label_support <> 6
       OR multi_target_record_count <> 0
       OR label_provenance_rate <> 1 THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=stale_label_targets_excluded expected min=6/multi=0/provenance=1 got %/%/%',
            minimum_label_support, multi_target_record_count,
            label_provenance_rate;
    END IF;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=superseded_receipt_excluded_from_human_universe,superseded_receipt_validation PASS';
    RAISE NOTICE
        'ROUND3M_POSITIVE=current_leaf_review_successor,current_leaf_validation,stale_label_targets_excluded PASS';
END
$review_supersession_positive$;

DO $superseded_review_pointer_restore_negative$
DECLARE
    target_assertion_id BIGINT;
    predecessor_receipt_id BIGINT;
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    SELECT assertion.descriptor_assertion_id,
           successor.supersedes_review_receipt_id
    INTO STRICT target_assertion_id, predecessor_receipt_id
    FROM corpus.round3m_descriptor_assertion AS assertion
    JOIN audit.round3m_descriptor_review_receipt AS successor
      ON successor.review_receipt_id = assertion.current_review_receipt_id
    WHERE assertion.descriptor_assertion_key =
          'round3m.test.assertion.51';

    BEGIN
        UPDATE corpus.round3m_descriptor_assertion
        SET current_review_receipt_id = predecessor_receipt_id
        WHERE descriptor_assertion_id = target_assertion_id;

        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: assertion_cannot_restore_superseded_review_pointer';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_descriptor_review_receipt_scope_ck' THEN
            RAISE;
        END IF;
    END;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=assertion_cannot_restore_superseded_review_pointer SQLSTATE=% CONSTRAINT=% PASS',
        actual_state, actual_constraint;
END
$superseded_review_pointer_restore_negative$;

SELECT pg_temp.expect_round3m_failure(
    'reviewed_normalized_form_requires_human_successor',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET normalized_candidate_form = 'mutated-note',
            normalized_candidate_form_sha256 =
                audit.round3i_utf8_sha256('mutated-note')
        WHERE descriptor_assertion_key = 'round3m.test.assertion.53'
    $sql$,
    '23514', 'round3m_reviewed_semantics_receipt_binding_ck'
);

DO $translated_normalized_form_gate_exclusion$
DECLARE
    target_assertion_id BIGINT;
    successor_receipt_id BIGINT;
    normalized_form_count BIGINT;
    target_concept_id BIGINT;
    target_concept_key TEXT;
BEGIN
    SELECT descriptor_assertion_id
    INTO STRICT target_assertion_id
    FROM corpus.round3m_descriptor_assertion
    WHERE descriptor_assertion_key = 'round3m.test.assertion.54';

    INSERT INTO audit.round3m_descriptor_review_receipt (
        review_receipt_key, descriptor_assertion_id, receipt_version,
        supersedes_review_receipt_id,
        reviewer_id_or_pseudonymous_code, reviewer_role,
        review_actor_type, receipt_origin_code,
        human_event_evidence_sha256, review_protocol_version,
        decision, decision_reason, evidence_locator, reviewed_at,
        adjudication_status, previous_decision
    )
    SELECT 'round3m.test.review.translation-successor',
           descriptor_assertion_id, 2, current_review_receipt_id,
           'human-reviewer-fixture-1',
           'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
           'HUMAN_REVIEW_IMPORT', repeat('6', 64),
           'round3m-human-review-fixture-v2', 'CONFIRM_DESCRIPTOR',
           'Actual-human successor records a translated form but cannot use it for vocabulary scale.',
           'fixture://review/translation-successor',
           '2026-08-28T01:07:00Z', 'NOT_REQUIRED',
           'CONFIRM_DESCRIPTOR'
    FROM corpus.round3m_descriptor_assertion
    WHERE descriptor_assertion_id = target_assertion_id
    RETURNING review_receipt_id INTO successor_receipt_id;

    UPDATE corpus.round3m_descriptor_assertion
    SET normalized_candidate_form = 'translation-only-form',
        normalized_candidate_form_sha256 =
            audit.round3i_utf8_sha256('translation-only-form'),
        translation_generated = TRUE,
        current_review_receipt_id = successor_receipt_id
    WHERE descriptor_assertion_id = target_assertion_id;

    SELECT target.concept_id, target.output_label_key
    INTO STRICT target_concept_id, target_concept_key
    FROM corpus.round3m_descriptor_label_target AS target
    WHERE target.descriptor_assertion_id = target_assertion_id
    ORDER BY target.review_receipt_id
    LIMIT 1;

    INSERT INTO audit.round3m_descriptor_label_mapping_receipt (
        label_mapping_receipt_id, descriptor_assertion_id,
        review_receipt_id, label_set_sha256,
        mapping_evidence_sha256, mapping_evidence_locator
    ) VALUES (
        'round3m.test.mapping.translation-successor',
        target_assertion_id, successor_receipt_id,
        audit.round3i_utf8_sha256(
            '1' || chr(31) || target_concept_key || chr(31) ||
            'EXACT_CANONICAL_TARGET' || chr(31) ||
            'concept:' || target_concept_id::TEXT
        ),
        repeat('6', 64),
        'fixture://review/translation-successor#label-mapping'
    );

    INSERT INTO corpus.round3m_descriptor_label_target (
        descriptor_assertion_id, target_ordinal, output_label_key,
        normalization_decision, review_receipt_id,
        label_mapping_receipt_id, concept_id
    ) VALUES (
        target_assertion_id, 1, target_concept_key,
        'EXACT_CANONICAL_TARGET', successor_receipt_id,
        'round3m.test.mapping.translation-successor', target_concept_id
    );

    SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
        corpus.round3m_label_mapping_set_target_ci IMMEDIATE;
    SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
        corpus.round3m_label_mapping_set_target_ci DEFERRED;

    SELECT reviewed_unique_normalized_form_count
    INTO STRICT normalized_form_count
    FROM audit.v_round3m_descriptor_gate_metrics;

    IF normalized_form_count <> 75 OR EXISTS (
        SELECT 1
        FROM corpus.v_round3m_model_eligible_descriptor_universe
        WHERE descriptor_assertion_id = target_assertion_id
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=translation_generated_form_inflated_gate count=%',
            normalized_form_count;
    END IF;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=translation_generated_form_excluded_from_gate_and_model PASS';
END
$translated_normalized_form_gate_exclusion$;

SELECT pg_temp.expect_round3m_failure(
    'same_human_successor_cannot_authorize_second_semantic_mutation',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET normalized_candidate_form = 'translation-second-mutation',
            normalized_candidate_form_sha256 =
                audit.round3i_utf8_sha256('translation-second-mutation')
        WHERE descriptor_assertion_key = 'round3m.test.assertion.54'
    $sql$,
    '23514', 'round3m_reviewed_semantics_receipt_binding_ck'
);

DO $review_downgrade_then_mutate_negative$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        UPDATE corpus.round3m_descriptor_assertion
        SET review_state = 'PROVISIONAL_MACHINE_CLASSIFIED',
            review_actor_type = 'CODEX_SOURCE_AUDITOR',
            current_review_receipt_id = NULL
        WHERE descriptor_assertion_key = 'round3m.test.assertion.57';

        UPDATE corpus.round3m_descriptor_assertion
        SET normalized_candidate_form = 'downgrade-bypass',
            normalized_candidate_form_sha256 =
                audit.round3i_utf8_sha256('downgrade-bypass')
        WHERE descriptor_assertion_key = 'round3m.test.assertion.57';

        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: review_downgrade_cannot_bypass_semantic_binding';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_reviewed_semantics_receipt_binding_ck' THEN
            RAISE;
        END IF;
    END;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=review_downgrade_cannot_bypass_semantic_binding SQLSTATE=% CONSTRAINT=% PASS',
        actual_state, actual_constraint;
END
$review_downgrade_then_mutate_negative$;

SELECT pg_temp.expect_round3m_failure(
    'post_receipt_label_mapping_cannot_be_backfilled',
    $sql$
        INSERT INTO audit.round3m_descriptor_label_mapping_receipt (
            label_mapping_receipt_id, descriptor_assertion_id,
            review_receipt_id, label_set_sha256,
            mapping_evidence_sha256, mapping_evidence_locator,
            created_at
        )
        SELECT 'round3m.test.mapping.posthoc', descriptor_assertion_id,
               current_review_receipt_id,
               audit.round3i_utf8_sha256(''), repeat('9', 64),
               'fixture://review/posthoc-label-mapping',
               transaction_timestamp() + interval '1 second'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.55'
    $sql$,
    '23514', 'round3m_label_mapping_human_evidence_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'label_target_requires_its_exact_mapping_receipt',
    $sql$
        INSERT INTO corpus.round3m_descriptor_label_target (
            descriptor_assertion_id, target_ordinal, output_label_key,
            normalization_decision, review_receipt_id,
            label_mapping_receipt_id, concept_id
        )
        SELECT target.descriptor_assertion_id, 99,
               alternate.concept_key,
               'EXACT_CANONICAL_TARGET', target.review_receipt_id,
               other.label_mapping_receipt_id, alternate.concept_id
        FROM corpus.round3m_descriptor_label_target AS target
        CROSS JOIN corpus.round3m_descriptor_label_target AS other
        CROSS JOIN LATERAL (
            SELECT concept_id, concept_key
            FROM kb.concept
            WHERE lifecycle_status_code = 'active'
              AND replacement_concept_id IS NULL
              AND concept_id <> target.concept_id
            ORDER BY concept_key
            LIMIT 1
        ) AS alternate
        WHERE target.descriptor_assertion_id = (
            SELECT descriptor_assertion_id
            FROM corpus.round3m_descriptor_assertion
            WHERE descriptor_assertion_key = 'round3m.test.assertion.55'
        )
          AND other.descriptor_assertion_id = (
            SELECT descriptor_assertion_id
            FROM corpus.round3m_descriptor_assertion
            WHERE descriptor_assertion_key = 'round3m.test.assertion.56'
        )
        LIMIT 1
    $sql$,
    '23503', 'round3m_label_target_mapping_receipt_fk'
);

SELECT pg_temp.expect_round3m_failure(
    'arbitrary_output_label_key_cannot_impersonate_canonical_target',
    $sql$
        INSERT INTO corpus.round3m_descriptor_label_target (
            descriptor_assertion_id, target_ordinal, output_label_key,
            normalization_decision, review_receipt_id,
            label_mapping_receipt_id, concept_id
        )
        SELECT target.descriptor_assertion_id, 99,
               'round3m.test.arbitrary-label-key',
               'EXACT_CANONICAL_TARGET', target.review_receipt_id,
               target.label_mapping_receipt_id, target.concept_id
        FROM corpus.round3m_descriptor_label_target AS target
        JOIN corpus.round3m_descriptor_assertion AS assertion
          ON assertion.descriptor_assertion_id =
             target.descriptor_assertion_id
        WHERE assertion.descriptor_assertion_key =
              'round3m.test.assertion.55'
        LIMIT 1
    $sql$,
    '23514', 'round3m_label_target_canonical_key_ck'
);

DO $exact_label_cardinality_negative$
DECLARE
    target_assertion_id BIGINT;
    successor_receipt_id BIGINT;
    mapping_digest TEXT;
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        SELECT descriptor_assertion_id INTO STRICT target_assertion_id
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.61';

        INSERT INTO audit.round3m_descriptor_review_receipt (
            review_receipt_key, descriptor_assertion_id,
            receipt_version, supersedes_review_receipt_id,
            reviewer_id_or_pseudonymous_code, reviewer_role,
            review_actor_type, receipt_origin_code,
            human_event_evidence_sha256, review_protocol_version,
            decision, decision_reason, evidence_locator, reviewed_at,
            adjudication_status, previous_decision
        )
        SELECT 'round3m.test.review.bad-exact-cardinality',
               descriptor_assertion_id, 2,
               current_review_receipt_id, 'human-reviewer-fixture-1',
               'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
               'HUMAN_REVIEW_IMPORT', repeat('3', 64),
               'round3m-human-review-fixture-v2',
               'CONFIRM_DESCRIPTOR',
               'Invalid two-target exact mapping fixture.',
               'fixture://review/bad-exact-cardinality',
               '2026-08-28T01:08:00Z', 'NOT_REQUIRED',
               'CONFIRM_DESCRIPTOR'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_id = target_assertion_id
        RETURNING review_receipt_id INTO successor_receipt_id;

        UPDATE corpus.round3m_descriptor_assertion
        SET current_review_receipt_id = successor_receipt_id
        WHERE descriptor_assertion_id = target_assertion_id;

        WITH target AS (
            SELECT concept_id, concept_key,
                   row_number() OVER (ORDER BY concept_key) AS ordinal
            FROM kb.concept
            WHERE lifecycle_status_code = 'active'
              AND replacement_concept_id IS NULL
            ORDER BY concept_key
            LIMIT 2
        )
        SELECT audit.round3i_utf8_sha256(
            string_agg(
                ordinal::TEXT || chr(31) || concept_key || chr(31) ||
                'EXACT_CANONICAL_TARGET' || chr(31) ||
                'concept:' || concept_id::TEXT,
                chr(30) ORDER BY ordinal
            )
        ) INTO STRICT mapping_digest
        FROM target;

        INSERT INTO audit.round3m_descriptor_label_mapping_receipt (
            label_mapping_receipt_id, descriptor_assertion_id,
            review_receipt_id, label_set_sha256,
            mapping_evidence_sha256, mapping_evidence_locator
        ) VALUES (
            'round3m.test.mapping.bad-exact-cardinality',
            target_assertion_id, successor_receipt_id, mapping_digest,
            repeat('3', 64),
            'fixture://review/bad-exact-cardinality#label-mapping'
        );

        INSERT INTO corpus.round3m_descriptor_label_target (
            descriptor_assertion_id, target_ordinal, output_label_key,
            normalization_decision, review_receipt_id,
            label_mapping_receipt_id, concept_id
        )
        SELECT target_assertion_id,
               row_number() OVER (ORDER BY concept_key)::INTEGER,
               concept_key, 'EXACT_CANONICAL_TARGET',
               successor_receipt_id,
               'round3m.test.mapping.bad-exact-cardinality', concept_id
        FROM kb.concept
        WHERE lifecycle_status_code = 'active'
          AND replacement_concept_id IS NULL
        ORDER BY concept_key
        LIMIT 2;

        SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
            corpus.round3m_label_mapping_set_target_ci IMMEDIATE;
        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: exact_label_mapping_requires_one_target';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_label_mapping_cardinality_ck' THEN
            RAISE;
        END IF;
    END;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=exact_label_mapping_requires_one_target SQLSTATE=% CONSTRAINT=% PASS',
        actual_state, actual_constraint;
END
$exact_label_cardinality_negative$;

DO $label_mapping_contiguous_ordinal_negative$
DECLARE
    target_assertion_id BIGINT;
    successor_receipt_id BIGINT;
    selected_concept_id BIGINT;
    selected_concept_key TEXT;
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        SELECT descriptor_assertion_id INTO STRICT target_assertion_id
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.62';

        SELECT concept_id, concept_key
        INTO STRICT selected_concept_id, selected_concept_key
        FROM kb.concept
        WHERE lifecycle_status_code = 'active'
          AND replacement_concept_id IS NULL
        ORDER BY concept_key
        LIMIT 1;

        INSERT INTO audit.round3m_descriptor_review_receipt (
            review_receipt_key, descriptor_assertion_id,
            receipt_version, supersedes_review_receipt_id,
            reviewer_id_or_pseudonymous_code, reviewer_role,
            review_actor_type, receipt_origin_code,
            human_event_evidence_sha256, review_protocol_version,
            decision, decision_reason, evidence_locator, reviewed_at,
            adjudication_status, previous_decision
        )
        SELECT 'round3m.test.review.bad-label-ordinal',
               descriptor_assertion_id, 2,
               current_review_receipt_id, 'human-reviewer-fixture-1',
               'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
               'HUMAN_REVIEW_IMPORT', repeat('2', 64),
               'round3m-human-review-fixture-v2',
               'CONFIRM_DESCRIPTOR',
               'Invalid noncontiguous label ordinal fixture.',
               'fixture://review/bad-label-ordinal',
               '2026-08-28T01:08:00Z', 'NOT_REQUIRED',
               'CONFIRM_DESCRIPTOR'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_id = target_assertion_id
        RETURNING review_receipt_id INTO successor_receipt_id;

        UPDATE corpus.round3m_descriptor_assertion
        SET current_review_receipt_id = successor_receipt_id
        WHERE descriptor_assertion_id = target_assertion_id;

        INSERT INTO audit.round3m_descriptor_label_mapping_receipt (
            label_mapping_receipt_id, descriptor_assertion_id,
            review_receipt_id, label_set_sha256,
            mapping_evidence_sha256, mapping_evidence_locator
        ) VALUES (
            'round3m.test.mapping.bad-label-ordinal',
            target_assertion_id, successor_receipt_id,
            audit.round3i_utf8_sha256(
                '2' || chr(31) || selected_concept_key || chr(31) ||
                'EXACT_CANONICAL_TARGET' || chr(31) ||
                'concept:' || selected_concept_id::TEXT
            ), repeat('2', 64),
            'fixture://review/bad-label-ordinal#label-mapping'
        );

        INSERT INTO corpus.round3m_descriptor_label_target (
            descriptor_assertion_id, target_ordinal, output_label_key,
            normalization_decision, review_receipt_id,
            label_mapping_receipt_id, concept_id
        ) VALUES (
            target_assertion_id, 2, selected_concept_key,
            'EXACT_CANONICAL_TARGET', successor_receipt_id,
            'round3m.test.mapping.bad-label-ordinal',
            selected_concept_id
        );

        SET CONSTRAINTS audit.round3m_label_mapping_set_receipt_ci,
            corpus.round3m_label_mapping_set_target_ci IMMEDIATE;
        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: label_mapping_ordinals_must_be_contiguous';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_label_mapping_cardinality_ck' THEN
            RAISE;
        END IF;
    END;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=label_mapping_ordinals_must_be_contiguous SQLSTATE=% CONSTRAINT=% PASS',
        actual_state, actual_constraint;
END
$label_mapping_contiguous_ordinal_negative$;

DO $post_receipt_label_append_negative$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO corpus.round3m_descriptor_label_target (
            descriptor_assertion_id, target_ordinal, output_label_key,
            normalization_decision, review_receipt_id,
            label_mapping_receipt_id, concept_id
        )
        SELECT target.descriptor_assertion_id, 99,
               alternate.concept_key,
               'EXACT_CANONICAL_TARGET', target.review_receipt_id,
               target.label_mapping_receipt_id, alternate.concept_id
        FROM corpus.round3m_descriptor_label_target AS target
        CROSS JOIN LATERAL (
            SELECT concept_id, concept_key
            FROM kb.concept
            WHERE lifecycle_status_code = 'active'
              AND replacement_concept_id IS NULL
              AND concept_id <> target.concept_id
            ORDER BY concept_key
            LIMIT 1
        ) AS alternate
        WHERE target.descriptor_assertion_id = (
            SELECT descriptor_assertion_id
            FROM corpus.round3m_descriptor_assertion
            WHERE descriptor_assertion_key = 'round3m.test.assertion.55'
        )
        LIMIT 1;

        SET CONSTRAINTS corpus.round3m_label_mapping_set_target_ci
            IMMEDIATE;
        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: post_receipt_label_append_rejected';
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_label_mapping_set_digest_ck' THEN
            RAISE;
        END IF;
    END;

    SET CONSTRAINTS corpus.round3m_label_mapping_set_target_ci DEFERRED;
    RAISE NOTICE
        'ROUND3M_NEGATIVE=post_receipt_label_append_rejected SQLSTATE=% CONSTRAINT=% PASS',
        actual_state, actual_constraint;
END
$post_receipt_label_append_negative$;

SELECT pg_temp.expect_round3m_failure(
    'label_target_update_is_immutable',
    $sql$
        UPDATE corpus.round3m_descriptor_label_target
        SET created_at = created_at + interval '1 second'
        WHERE descriptor_assertion_id = (
            SELECT descriptor_assertion_id
            FROM corpus.round3m_descriptor_assertion
            WHERE descriptor_assertion_key = 'round3m.test.assertion.55'
        )
    $sql$,
    '23514', 'round3m_label_target_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'label_target_delete_is_immutable',
    $sql$
        DELETE FROM corpus.round3m_descriptor_label_target
        WHERE descriptor_assertion_id = (
            SELECT descriptor_assertion_id
            FROM corpus.round3m_descriptor_assertion
            WHERE descriptor_assertion_key = 'round3m.test.assertion.55'
        )
    $sql$,
    '23514', 'round3m_label_target_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'human_review_receipt_is_append_only',
    $sql$
        UPDATE audit.round3m_descriptor_review_receipt
        SET decision_reason = 'Invalid mutable human review evidence.'
        WHERE review_receipt_id = (
            SELECT current_review_receipt_id
            FROM corpus.round3m_descriptor_assertion
            WHERE descriptor_assertion_key = 'round3m.test.assertion.55'
        )
    $sql$,
    '23514', 'round3m_immutable_evidence_ck'
);

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
               '2026-08-28T01:07:00Z', 'NOT_REQUIRED',
               'CONFIRM_DESCRIPTOR'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_human_review_receipt_origin_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'unqualified_actor_cannot_claim_expert_adjudication',
    $sql$
        INSERT INTO audit.round3m_descriptor_review_receipt (
            review_receipt_key, descriptor_assertion_id,
            receipt_version, supersedes_review_receipt_id,
            reviewer_id, reviewer_id_or_pseudonymous_code,
            reviewer_role, review_actor_type, receipt_origin_code,
            human_event_evidence_sha256, review_protocol_version,
            decision, decision_reason, evidence_locator, reviewed_at,
            adjudication_status, previous_decision
        )
        SELECT 'round3m.test.bad.unqualified-expert',
               descriptor_assertion_id, 2,
               current_review_receipt_id, NULL,
               'unqualified-expert-fixture', 'ADJUDICATOR',
               'EXPERT_REVIEWER', 'HUMAN_REVIEW_IMPORT',
               repeat('4', 64), 'round3m-test-v2',
               'ADJUDICATE_DESCRIPTOR',
               'Invalid unqualified expert fixture.',
               'fixture://review/unqualified-expert',
               '2026-08-28T01:08:00Z', 'FINAL',
               'CONFIRM_DESCRIPTOR'
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.60'
    $sql$,
    '23514', 'round3m_expert_review_qualification_ck'
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
    'descriptor_route_index_must_match_source_artifact',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET route_index_sha256 = repeat('d', 64)
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_descriptor_artifact_lineage_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'descriptor_hash_scope_must_match_source_artifact',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET source_file_sha256_scope = 'ROUTE_INDEX_SHA256'
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_descriptor_artifact_lineage_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'descriptor_nonstorage_reason_must_match_source_artifact',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET source_file_nonstorage_reason =
            'Invalid assertion-only non-storage reason.'
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1'
    $sql$,
    '23514', 'round3m_descriptor_artifact_lineage_ck'
);

INSERT INTO evidence.round3m_descriptor_rights_decision (
    rights_decision_id, rights_scope_id, decision_version,
    source_route_id, publication_layer, source_field_label,
    public_discovery, internal_research_analysis,
    derived_research_data, model_research,
    deployment_or_commercial_model, raw_redistribution,
    decision_authority_code, decision_actor_type, decision_basis,
    evidence_locator, decided_at
) VALUES
(
    'round3m.test.rights.result-metadata',
    'round3m.test.scope.result-metadata', 1,
    'round3m.test.route.1', 'RESULT_METADATA',
    'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
    'PENDING', 'PENDING', 'PENDING', 'PROHIBITED',
    'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
    'Transaction-local publication semantic fixture.',
    'fixture://rights/result-metadata', '2026-08-28T01:02:00Z'
),
(
    'round3m.test.rights.producer-profile',
    'round3m.test.scope.producer-profile', 1,
    'round3m.test.route.1', 'PRODUCER_OR_FARM_PROFILE',
    'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
    'PENDING', 'PENDING', 'PENDING', 'PROHIBITED',
    'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
    'Transaction-local publication semantic fixture.',
    'fixture://rights/producer-profile', '2026-08-28T01:02:00Z'
),
(
    'round3m.test.rights.judge-level',
    'round3m.test.scope.judge-level', 1,
    'round3m.test.route.1', 'JUDGE_LEVEL_OBSERVATION',
    'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE',
    'PENDING', 'PENDING', 'PENDING', 'PROHIBITED',
    'RIGHTS_HOLDER', 'RIGHTS_HOLDER',
    'Transaction-local publication semantic fixture.',
    'fixture://rights/judge-level', '2026-08-28T01:02:00Z'
);

CREATE FUNCTION pg_temp.expect_round3m_publication_failure(
    test_key TEXT,
    publication_layer_value TEXT,
    rights_decision_value TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3m_publication_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO corpus.round3m_descriptor_assertion (
            descriptor_assertion_key,
            professional_acquisition_record_id,
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
            normalized_candidate_form,
            normalized_candidate_form_sha256,
            normalization_method_code, evidence_tier,
            evidence_origin_type, origin_decision_basis,
            origin_evidence_locator, review_state, review_actor_type,
            rights_decision_id, source_retrieved_at,
            source_file_sha256, route_index_sha256,
            source_file_sha256_scope, source_file_nonstorage_reason,
            parser_version, adapter_version
        )
        SELECT
            'round3m.test.publication.' || test_key,
            professional_acquisition_record_id,
            effective_record_key, edition_year, source_artifact_id,
            source_route_id, schema_signature_id,
            publication_layer_value, source_field_label,
            source_field_label_sha256,
            '#invalid-publication-' || test_key,
            'record-1#invalid-publication-' || test_key,
            'round3m.test.observation.invalid-publication.' || test_key,
            'Invalid publication ' || test_key,
            audit.round3i_utf8_sha256(
                'Invalid publication ' || test_key
            ),
            'invalid-publication-' || test_key,
            audit.round3i_utf8_sha256(
                'invalid-publication-' || test_key
            ),
            'REVIEWED_EXCERPT', '', source_language,
            'STRICT_FLAVOR', 'invalid-publication-' || test_key,
            audit.round3i_utf8_sha256(
                'invalid-publication-' || test_key
            ),
            'invalid-publication-' || test_key,
            audit.round3i_utf8_sha256(
                'invalid-publication-' || test_key
            ),
            'UNICODE_NFC_WHITESPACE_CASE', 'P2',
            'EXPLICIT_TOP_JURY_FIELD',
            'Invalid reverse publication semantic fixture.',
            'fixture://publication/' || test_key,
            'PROVISIONAL_MACHINE_CLASSIFIED',
            'CODEX_SOURCE_AUDITOR', rights_decision_value,
            source_retrieved_at, source_file_sha256,
            route_index_sha256, source_file_sha256_scope,
            source_file_nonstorage_reason, parser_version,
            adapter_version
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key = 'round3m.test.assertion.1';

        RAISE EXCEPTION
            'Round 3M negative unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> '23514'
           OR actual_constraint IS DISTINCT FROM
              'round3m_publication_layer_semantics_ck' THEN
            RAISE;
        END IF;
    END;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
        test_key, actual_state, actual_constraint;
END
$expect_round3m_publication_failure$;

SELECT pg_temp.expect_round3m_publication_failure(
    'result_metadata_cannot_be_strict_p2', 'RESULT_METADATA',
    'round3m.test.rights.result-metadata'
);
SELECT pg_temp.expect_round3m_publication_failure(
    'producer_profile_cannot_be_p2_jury', 'PRODUCER_OR_FARM_PROFILE',
    'round3m.test.rights.producer-profile'
);
SELECT pg_temp.expect_round3m_publication_failure(
    'judge_level_cannot_be_p2_top_jury', 'JUDGE_LEVEL_OBSERVATION',
    'round3m.test.rights.judge-level'
);

INSERT INTO evidence.round3m_source_schema_signature (
    schema_signature_id, source_route_id, schema_version, host,
    route_pattern, edition_or_period, field_labels_json, selectors_json,
    publication_layer_rules_json, field_origin_assumptions_json,
    known_ambiguity, positive_fixture_locator, negative_fixture_locator,
    adapter_version, live_positive_fixture_present, validation_status
) VALUES (
    'round3m.test.schema.secondary', 'round3m.test.route.1', 2,
    'family1.example.test', '/results/{edition}', '2021',
    '["Secondary Sensory Table"]'::JSONB,
    '{"field":"#secondary-sensory-table"}'::JSONB,
    '{"Secondary Sensory Table":"SECONDARY_SENSORY_TABLE"}'::JSONB,
    '{"Secondary Sensory Table":"secondary publication origin unresolved"}'::JSONB,
    'Secondary publication is retained for review without primary credit.',
    'https://family1.example.test/positive-secondary',
    'https://family1.example.test/negative-secondary',
    'round3m-test-adapter-v1', TRUE, 'VALIDATED'
);

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    round3l_source_attempt_id, governed_locator, source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    file_size_bytes, storage_state, non_storage_reason,
    parser_version, adapter_version
)
SELECT
    'round3m.test.artifact.secondary', 'round3m.test.route.1',
    'round3m.test.schema.secondary', attempt.round3l_source_attempt_id,
    'https://family1.example.test/results/secondary',
    '2026-08-28T01:01:00Z', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '', 1024, 'HASH_AND_LOCATOR_ONLY',
    'Transaction-local secondary fixture stores hash and locator only.',
    'round3m-test-parser-v1', 'round3m-test-adapter-v1'
FROM audit.round3l_source_attempt AS attempt
WHERE attempt.attempt_key = 'round3m.test.attempt.1';

INSERT INTO evidence.round3m_descriptor_rights_decision (
    rights_decision_id, rights_scope_id, decision_version,
    source_route_id, publication_layer, source_field_label,
    public_discovery, internal_research_analysis,
    derived_research_data, model_research,
    deployment_or_commercial_model, raw_redistribution,
    decision_authority_code, decision_actor_type, decision_basis,
    evidence_locator, decided_at
) VALUES (
    'round3m.test.rights.secondary', 'round3m.test.scope.secondary', 1,
    'round3m.test.route.1', 'SECONDARY_SENSORY_TABLE',
    'Secondary Sensory Table', 'AFFIRMATIVE', 'UNKNOWN', 'UNKNOWN',
    'UNKNOWN', 'UNKNOWN', 'PROHIBITED', 'PROJECT_RIGHTS_AUDIT',
    'CODEX_SOURCE_AUDITOR',
    'Secondary publication rights remain unresolved and non-counting.',
    'https://family1.example.test/results/secondary',
    '2026-08-28T01:02:00Z'
);

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
    deduplication_disposition, source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
)
SELECT
    'round3m.test.secondary.review-only',
    record.professional_acquisition_record_id,
    record.effective_record_key, record.edition_year,
    'round3m.test.artifact.secondary', 'round3m.test.route.1',
    'round3m.test.schema.secondary', 'SECONDARY_SENSORY_TABLE',
    'Secondary Sensory Table',
    audit.round3i_utf8_sha256('Secondary Sensory Table'),
    '#secondary-sensory-table',
    'record-1#secondary-sensory-table',
    'round3m.test.observation.secondary.1',
    'Secondary flavor note',
    audit.round3i_utf8_sha256('Secondary flavor note'),
    'secondary-note', audit.round3i_utf8_sha256('secondary-note'),
    'REVIEWED_EXCERPT', '', 'en', 'STRICT_FLAVOR',
    'secondary-note', audit.round3i_utf8_sha256('secondary-note'),
    'secondary-note', audit.round3i_utf8_sha256('secondary-note'),
    'UNICODE_NFC_WHITESPACE_CASE', 'UNRESOLVED', 'UNKNOWN_ORIGIN',
    'Secondary table origin is unresolved and cannot receive primary credit.',
    'record-1#secondary-sensory-table',
    'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
    'round3m.test.rights.secondary', 'UNRESOLVED',
    '2026-08-28T01:01:00Z', repeat('a', 64), '',
    'FULL_SOURCE_FILE_SHA256', '',
    'round3m-test-parser-v1', 'round3m-test-adapter-v1'
FROM corpus.professional_acquisition_record AS record
WHERE record.professional_acquisition_record_key =
      'round3m.test.record.1';

DO $secondary_layer_positive$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_assertion_key =
              'round3m.test.secondary.review-only'
          AND publication_layer = 'SECONDARY_SENSORY_TABLE'
          AND source_selector_or_locator = '#secondary-sensory-table'
          AND source_observation_key =
              'round3m.test.observation.secondary.1'
          AND deduplication_disposition = 'UNRESOLVED'
    ) OR EXISTS (
        SELECT 1
        FROM corpus.v_round3m_assertion_level_deinflated
        WHERE descriptor_assertion_key =
              'round3m.test.secondary.review-only'
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=secondary_layer_preserved_noncounting failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=secondary_layer_preserved_noncounting,distinct_secondary_observation PASS';
END
$secondary_layer_positive$;

SELECT pg_temp.expect_round3m_failure(
    'secondary_layer_cannot_become_canonical_counting_assertion',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET deduplication_disposition = 'CANONICAL'
        WHERE descriptor_assertion_key =
              'round3m.test.secondary.review-only'
    $sql$,
    '23514', 'round3m_secondary_publication_layer_noncounting_ck'
);

-- Three primary companion assertions provide two governed observations with
-- enough distinct endpoints to exercise pair and set-identity anti-inflation.
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
    fixture.companion_assertion_key,
    base.professional_acquisition_record_id,
    base.effective_record_key, base.edition_year,
    base.source_artifact_id, base.source_route_id,
    base.schema_signature_id, base.publication_layer,
    base.source_field_label, base.source_field_label_sha256,
    base.source_selector_or_locator,
    base.source_page_or_record_locator, base.source_observation_key,
    'Co-assertion fixture ' || fixture.companion_form,
    audit.round3i_utf8_sha256(
        'Co-assertion fixture ' || fixture.companion_form
    ),
    fixture.companion_form,
    audit.round3i_utf8_sha256(fixture.companion_form),
    'REVIEWED_EXCERPT', '', base.source_language, 'STRICT_FLAVOR',
    fixture.companion_form,
    audit.round3i_utf8_sha256(fixture.companion_form),
    fixture.companion_form,
    audit.round3i_utf8_sha256(fixture.companion_form),
    'UNICODE_NFC_WHITESPACE_CASE', 'P2',
    'EXPLICIT_TOP_JURY_FIELD',
    'Fixture explicitly identifies the Top Jury field.',
    base.origin_evidence_locator,
    'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
    base.rights_decision_id, base.source_retrieved_at,
    base.source_file_sha256, base.route_index_sha256,
    base.source_file_sha256_scope, base.source_file_nonstorage_reason,
    base.parser_version, base.adapter_version
FROM (VALUES
    (
        'round3m.test.assertion.1',
        'round3m.test.pair.assertion.1b', 'pair-note-1b'
    ),
    (
        'round3m.test.assertion.1',
        'round3m.test.pair.assertion.1c', 'pair-note-1c'
    ),
    (
        'round3m.test.assertion.2',
        'round3m.test.pair.assertion.2b', 'pair-note-2b'
    )
) AS fixture(
    base_assertion_key, companion_assertion_key, companion_form
)
JOIN corpus.round3m_descriptor_assertion AS base
  ON base.descriptor_assertion_key = fixture.base_assertion_key;

-- This endpoint is otherwise a valid P2 primary assertion for the same
-- observation, but it is bound to a different artifact/schema publication.
-- It exists solely to prove that co-assertion edges cannot cross that source
-- publication boundary.
INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, professional_acquisition_record_id,
    effective_record_key, edition_year, source_artifact_id,
    source_route_id, schema_signature_id, publication_layer,
    source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
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
    'round3m.test.pair.assertion.cross-artifact',
    base.professional_acquisition_record_id,
    base.effective_record_key, base.edition_year,
    'round3m.test.artifact.secondary', base.source_route_id,
    'round3m.test.schema.secondary', base.publication_layer,
    base.source_field_label, base.source_field_label_sha256,
    base.source_selector_or_locator, base.source_page_or_record_locator,
    base.source_observation_key,
    'Co-assertion cross-artifact fixture',
    audit.round3i_utf8_sha256('Co-assertion cross-artifact fixture'),
    'pair-note-cross-artifact',
    audit.round3i_utf8_sha256('pair-note-cross-artifact'),
    'REVIEWED_EXCERPT', '', base.source_language, 'STRICT_FLAVOR',
    'pair-note-cross-artifact',
    audit.round3i_utf8_sha256('pair-note-cross-artifact'),
    'pair-note-cross-artifact',
    audit.round3i_utf8_sha256('pair-note-cross-artifact'),
    'UNICODE_NFC_WHITESPACE_CASE', 'P2',
    'EXPLICIT_TOP_JURY_FIELD',
    'Fixture explicitly identifies the Top Jury field.',
    base.origin_evidence_locator,
    'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
    base.rights_decision_id, base.source_retrieved_at,
    base.source_file_sha256, base.route_index_sha256,
    base.source_file_sha256_scope, base.source_file_nonstorage_reason,
    base.parser_version, base.adapter_version
FROM corpus.round3m_descriptor_assertion AS base
WHERE base.descriptor_assertion_key = 'round3m.test.assertion.1';

INSERT INTO corpus.round3m_coassertion_event (
    coassertion_event_key, coassertion_set_key,
    effective_record_key, source_observation_key,
    left_descriptor_assertion_id,
    right_descriptor_assertion_id, generated_by_version
)
SELECT
    'round3m.test.pair.observation.1.initial',
    'round3m.test.set.observation.1',
    left_assertion.effective_record_key,
    left_assertion.source_observation_key,
    least(
        left_assertion.descriptor_assertion_id,
        right_assertion.descriptor_assertion_id
    ),
    greatest(
        left_assertion.descriptor_assertion_id,
        right_assertion.descriptor_assertion_id
    ),
    'round3m-test-pair-v1'
FROM corpus.round3m_descriptor_assertion AS left_assertion
CROSS JOIN corpus.round3m_descriptor_assertion AS right_assertion
WHERE left_assertion.descriptor_assertion_key =
          'round3m.test.assertion.1'
  AND right_assertion.descriptor_assertion_key =
          'round3m.test.pair.assertion.1b';

SELECT pg_temp.expect_round3m_failure(
    'coassertion_endpoint_semantics_are_immutable_until_regenerated',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion
        SET origin_decision_basis =
            origin_decision_basis || ' Mutated after edge creation.'
        WHERE descriptor_assertion_key =
              'round3m.test.pair.assertion.1b'
    $sql$,
    '23514', 'round3m_coassertion_endpoint_governance_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'coassertion_cannot_cross_artifact_or_schema_publication_boundary',
    $sql$
        INSERT INTO corpus.round3m_coassertion_event (
            coassertion_event_key, coassertion_set_key,
            effective_record_key, source_observation_key,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id, generated_by_version
        )
        SELECT 'round3m.test.bad.pair.cross-artifact',
               'round3m.test.set.observation.1',
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
                  'round3m.test.pair.assertion.cross-artifact'
    $sql$,
    '23514', 'round3m_coassertion_publication_boundary_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'coassertion_endpoint_pair_cannot_repeat_under_alternate_set',
    $sql$
        INSERT INTO corpus.round3m_coassertion_event (
            coassertion_event_key, coassertion_set_key,
            effective_record_key, source_observation_key,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id, generated_by_version
        )
        SELECT 'round3m.test.bad.pair.duplicate-endpoints',
               'round3m.test.set.observation.1',
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
                  'round3m.test.pair.assertion.1b'
    $sql$,
    '23505', 'round3m_coassertion_event_pair_uq'
);

SELECT pg_temp.expect_round3m_failure(
    'coassertion_observation_cannot_use_alternate_set_key',
    $sql$
        INSERT INTO corpus.round3m_coassertion_event (
            coassertion_event_key, coassertion_set_key,
            effective_record_key, source_observation_key,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id, generated_by_version
        )
        SELECT 'round3m.test.bad.pair.alternate-set',
               'round3m.test.set.alternate-observation-1',
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
                  'round3m.test.pair.assertion.1c'
    $sql$,
    '23514', 'round3m_coassertion_set_identity_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'coassertion_set_key_cannot_span_observations',
    $sql$
        INSERT INTO corpus.round3m_coassertion_event (
            coassertion_event_key, coassertion_set_key,
            effective_record_key, source_observation_key,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id, generated_by_version
        )
        SELECT 'round3m.test.bad.pair.reused-set',
               'round3m.test.set.observation.1',
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
                  'round3m.test.assertion.2'
          AND right_assertion.descriptor_assertion_key =
                  'round3m.test.pair.assertion.2b'
    $sql$,
    '23514', 'round3m_coassertion_set_identity_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'coassertion_event_identity_must_match_endpoints',
    $sql$
        INSERT INTO corpus.round3m_coassertion_event (
            coassertion_event_key, coassertion_set_key,
            effective_record_key, source_observation_key,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id, generated_by_version
        )
        SELECT 'round3m.test.bad.pair.forged-event-identity',
               'round3m.test.set.observation.1',
               forged_identity.effective_record_key,
               forged_identity.source_observation_key,
               least(left_assertion.descriptor_assertion_id,
                     right_assertion.descriptor_assertion_id),
               greatest(left_assertion.descriptor_assertion_id,
                        right_assertion.descriptor_assertion_id),
               'round3m-test-pair-v1'
        FROM corpus.round3m_descriptor_assertion AS left_assertion
        CROSS JOIN corpus.round3m_descriptor_assertion AS right_assertion
        CROSS JOIN corpus.round3m_descriptor_assertion AS forged_identity
        WHERE left_assertion.descriptor_assertion_key =
                  'round3m.test.assertion.1'
          AND right_assertion.descriptor_assertion_key =
                  'round3m.test.pair.assertion.1c'
          AND forged_identity.descriptor_assertion_key =
                  'round3m.test.assertion.2'
    $sql$,
    '23514', 'round3m_coassertion_effective_record_boundary_ck'
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
    'FULL_SOURCE_FILE_SHA256', '',
    competition.round3m_effective_record_identity_sha256(
        'round3m.test.series.1', 'round3m.test.edition.1', 2021,
        'cupping', 'final', 'LOT', 'lot-hash-only',
        'green_competition_cupping', 'round3m.test.route.1',
        repeat('a', 64), '', 'fixture://queue'
    ),
    'SOURCE_NATIVE_PROVISIONAL', FALSE, FALSE
);

SELECT pg_temp.expect_round3m_failure(
    'effective_source_record_cannot_mint_second_bridge_identity',
    $sql$
        INSERT INTO competition.round3m_effective_record_bridge (
            round3m_effective_record_id, effective_record_key,
            series_id, edition_id, edition_year, category_id, round_id,
            subject_kind, entry_or_lot_id, preparation_service_code,
            preparation_evidence_locator, source_route_id,
            source_artifact_id, source_record_locator,
            source_file_sha256, route_index_sha256,
            source_file_sha256_scope, source_file_nonstorage_reason,
            record_identity_sha256, identity_resolution_state,
            synthetic_generated, preparation_inferred_from_descriptor
        ) VALUES (
            'round3m.test.bridge.record.reminted',
            'round3m.test.bridge.effective.reminted',
            'round3m.test.series.1', 'round3m.test.edition.1', 2021,
            'cupping', 'final', 'LOT', 'lot-hash-only-reminted',
            'green_competition_cupping',
            'fixture://protocol/fresh-cupping',
            'round3m.test.route.1', 'round3m.test.artifact.1',
            'fixture://queue', repeat('a', 64), '',
            'FULL_SOURCE_FILE_SHA256', '',
            competition.round3m_effective_record_identity_sha256(
                'round3m.test.series.1', 'round3m.test.edition.1',
                2021, 'cupping', 'final', 'LOT',
                'lot-hash-only-reminted', 'green_competition_cupping',
                'round3m.test.route.1', repeat('a', 64), '',
                'fixture://queue'
            ),
            'SOURCE_NATIVE_PROVISIONAL', FALSE, FALSE
        )
    $sql$,
    '23505', 'round3m_effective_record_source_identity_uq'
);

SELECT pg_temp.expect_round3m_failure(
    'effective_bridge_governed_identity_is_immutable',
    $sql$
        UPDATE competition.round3m_effective_record_bridge
        SET entry_or_lot_id = 'lot-hash-only-mutated'
        WHERE round3m_effective_record_id = 'round3m.test.bridge.record'
    $sql$,
    '23514', 'round3m_effective_record_identity_immutable_ck'
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

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, professional_acquisition_record_id,
    effective_record_key, edition_year, source_artifact_id,
    source_route_id, schema_signature_id, publication_layer,
    source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256,
    text_storage_state, source_text_non_storage_reason,
    source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator,
    review_state, review_actor_type, rights_decision_id,
    deduplication_disposition, source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
)
SELECT
    'round3m.test.challenge.canonical',
    professional_acquisition_record_id, effective_record_key,
    edition_year, source_artifact_id, source_route_id,
    schema_signature_id, publication_layer, source_field_label,
    source_field_label_sha256, '#challenge-canonical',
    source_page_or_record_locator || '#challenge-canonical',
    'round3m.test.observation.challenge-canonical',
    'Ambiguous sensory challenge phrase',
    audit.round3i_utf8_sha256('Ambiguous sensory challenge phrase'),
    'ambiguous sensory challenge',
    audit.round3i_utf8_sha256('ambiguous sensory challenge'),
    'REVIEWED_EXCERPT', '', source_language, 'STRICT_FLAVOR',
    'ambiguous sensory challenge',
    audit.round3i_utf8_sha256('ambiguous sensory challenge'),
    NULL, '', 'NONE', 'P2', evidence_origin_type,
    origin_decision_basis,
    source_page_or_record_locator || '#challenge-canonical',
    'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
    rights_decision_id, 'CANONICAL', source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key = 'round3m.test.assertion.1';

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, professional_acquisition_record_id,
    effective_record_key, edition_year, source_artifact_id,
    source_route_id, schema_signature_id, publication_layer,
    source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256,
    text_storage_state, source_text_non_storage_reason,
    source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator,
    review_state, review_actor_type, rights_decision_id,
    deduplication_disposition, within_record_repeat_group,
    source_retrieved_at,
    source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
)
SELECT
    'round3m.test.challenge.exact-repeat',
    professional_acquisition_record_id, effective_record_key,
    edition_year, source_artifact_id, source_route_id,
    schema_signature_id, publication_layer, source_field_label,
    source_field_label_sha256, '#challenge-canonical',
    source_page_or_record_locator || '#challenge-canonical',
    'round3m.test.observation.challenge-repeat',
    'Ambiguous sensory challenge phrase',
    audit.round3i_utf8_sha256('Ambiguous sensory challenge phrase'),
    'ambiguous sensory challenge',
    audit.round3i_utf8_sha256('ambiguous sensory challenge'),
    'REVIEWED_EXCERPT', '', source_language, 'STRICT_FLAVOR',
    'ambiguous sensory challenge',
    audit.round3i_utf8_sha256('ambiguous sensory challenge'),
    NULL, '', 'NONE', 'P2', evidence_origin_type,
    origin_decision_basis,
    source_page_or_record_locator || '#challenge-canonical',
    'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
    rights_decision_id, 'EXACT_WITHIN_FIELD_REPEAT',
    'round3m.test.repeat.challenge',
    source_retrieved_at, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key = 'round3m.test.assertion.1';

INSERT INTO audit.round3m_descriptor_review_receipt (
    review_receipt_key, descriptor_assertion_id, receipt_version,
    reviewer_id_or_pseudonymous_code, reviewer_role,
    review_actor_type, receipt_origin_code,
    human_event_evidence_sha256, review_protocol_version,
    decision, decision_reason, evidence_locator, reviewed_at,
    adjudication_status, previous_decision
)
SELECT 'round3m.test.review.' || descriptor_assertion_key,
       descriptor_assertion_id, 1, 'human-reviewer-fixture-2',
       'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
       'DOCUMENTED_HUMAN_EVENT', repeat('1', 64),
       'round3m-normalization-challenge-v1', 'MARK_AMBIGUOUS',
       'Actual-human ambiguous normalization challenge fixture.',
       'fixture://review/' || descriptor_assertion_key,
       '2026-08-28T01:09:00Z', 'NOT_REQUIRED',
       'PROVISIONAL_MACHINE_CLASSIFIED'
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key IN (
    'round3m.test.challenge.canonical',
    'round3m.test.challenge.exact-repeat'
);

UPDATE corpus.round3m_descriptor_assertion AS assertion
SET review_state = 'PROVENANCE_UNRESOLVED',
    review_actor_type = 'HUMAN_REVIEWER',
    current_review_receipt_id = receipt.review_receipt_id
FROM audit.round3m_descriptor_review_receipt AS receipt
WHERE receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
  AND assertion.descriptor_assertion_key IN (
      'round3m.test.challenge.canonical',
      'round3m.test.challenge.exact-repeat'
  );

DO $generic_review_markers_do_not_count_as_normalization_challenges$
DECLARE
    challenge_count BIGINT;
BEGIN
    SELECT reviewed_ambiguous_or_unresolved_challenge_count
    INTO STRICT challenge_count
    FROM audit.v_round3m_descriptor_gate_metrics;

    IF challenge_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=generic_review_marker_inflated_normalization_challenge value=%',
            challenge_count;
    END IF;
    RAISE NOTICE
        'ROUND3M_NEGATIVE=generic_assertion_mark_ambiguous_cannot_count_as_normalization_challenge PASS';
    RAISE NOTICE
        'ROUND3M_NEGATIVE=exact_repeat_cannot_inflate_human_challenge_count PASS';
END
$generic_review_markers_do_not_count_as_normalization_challenges$;

INSERT INTO audit.round3m_descriptor_review_receipt (
    review_receipt_key, descriptor_assertion_id, receipt_version,
    reviewer_id_or_pseudonymous_code, reviewer_role,
    review_actor_type, receipt_origin_code,
    human_event_evidence_sha256, review_protocol_version,
    decision, decision_reason, evidence_locator, reviewed_at,
    adjudication_status, previous_decision
)
SELECT 'round3m.test.review.hash-only-abstain',
       descriptor_assertion_id, 1, 'human-reviewer-fixture-2',
       'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
       'DOCUMENTED_HUMAN_EVENT', repeat('0', 64),
       'round3m-normalization-challenge-v1', 'ABSTAIN',
       'Abstention is not an ambiguous or unresolved decision.',
       'fixture://review/hash-only-abstain',
       '2026-08-28T01:09:00Z', 'NOT_REQUIRED',
       'PROVISIONAL_MACHINE_CLASSIFIED'
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key = 'round3m.test.hash.only';

SELECT pg_temp.expect_round3m_failure(
    'abstain_cannot_be_attached_as_ambiguous_or_unresolved_state',
    $sql$
        UPDATE corpus.round3m_descriptor_assertion AS assertion
        SET review_state = 'PROVENANCE_UNRESOLVED',
            review_actor_type = 'HUMAN_REVIEWER',
            current_review_receipt_id = receipt.review_receipt_id
        FROM audit.round3m_descriptor_review_receipt AS receipt
        WHERE assertion.descriptor_assertion_key =
              'round3m.test.hash.only'
          AND receipt.review_receipt_key =
              'round3m.test.review.hash-only-abstain'
    $sql$,
    '23514', 'round3m_descriptor_review_state_receipt_ck'
);

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

SELECT pg_temp.expect_round3m_failure(
    'split_plan_cannot_be_inserted_directly_as_frozen',
    $sql$
        INSERT INTO ml.professional_split_plan (
            professional_split_plan_key, plan_version,
            deterministic_rule_version, lifecycle_status_code,
            frozen_at, freeze_receipt_sha256
        ) VALUES (
            'round3m.descriptor-gate-holdout', 99,
            'round3m-test-split-v99', 'FROZEN',
            transaction_timestamp(), repeat('a', 64)
        )
    $sql$,
    '23514', 'round3m_split_freeze_transition_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'split_plan_cannot_be_inserted_directly_as_superseded',
    $sql$
        INSERT INTO ml.professional_split_plan (
            professional_split_plan_key, plan_version,
            deterministic_rule_version, lifecycle_status_code,
            frozen_at, freeze_receipt_sha256
        ) VALUES (
            'round3m.descriptor-gate-holdout', 98,
            'round3m-test-split-v98', 'SUPERSEDED',
            transaction_timestamp(), repeat('a', 64)
        )
    $sql$,
    '23514', 'round3m_split_freeze_transition_ck'
);

INSERT INTO ml.professional_split_plan (
    professional_split_plan_key, plan_version,
    deterministic_rule_version, lifecycle_status_code
) VALUES (
    'round3k.legacy-frozen-contract-fixture', 1,
    'round3k-legacy-receipt-v1', 'FROZEN'
);

DO $legacy_split_contract_remains_scoped$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM ml.professional_split_plan
        WHERE professional_split_plan_key =
              'round3k.legacy-frozen-contract-fixture'
          AND lifecycle_status_code = 'FROZEN'
          AND frozen_at IS NULL
          AND freeze_receipt_sha256 IS NULL
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=legacy_non_target_split_contract_is_unchanged failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=legacy_non_target_split_contract_is_unchanged PASS';
END
$legacy_split_contract_remains_scoped$;

INSERT INTO ml.professional_split_plan (
    professional_split_plan_key, plan_version,
    deterministic_rule_version, lifecycle_status_code
) VALUES (
    'round3k.legacy-candidate-contract-fixture', 1,
    'round3k-legacy-candidate-v1', 'CANDIDATE'
);

INSERT INTO ml.professional_split_group (
    professional_split_plan_id, split_group_kind_code,
    split_group_key, source_basis
)
SELECT professional_split_plan_id, 'COMPETITION_FAMILY',
       'round3k.legacy.movable.family',
       'Legacy-to-legacy plan-move compatibility fixture.'
FROM ml.professional_split_plan
WHERE professional_split_plan_key =
      'round3k.legacy-frozen-contract-fixture';

UPDATE ml.professional_split_group AS legacy_group
SET professional_split_plan_id = destination.professional_split_plan_id
FROM ml.professional_split_plan AS source
CROSS JOIN ml.professional_split_plan AS destination
WHERE source.professional_split_plan_key =
      'round3k.legacy-frozen-contract-fixture'
  AND destination.professional_split_plan_key =
      'round3k.legacy-candidate-contract-fixture'
  AND legacy_group.professional_split_plan_id =
      source.professional_split_plan_id
  AND legacy_group.split_group_key =
      'round3k.legacy.movable.family';

DO $legacy_group_move_remains_allowed$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM ml.professional_split_group AS split_group
        JOIN ml.professional_split_plan AS plan
          ON plan.professional_split_plan_id =
             split_group.professional_split_plan_id
        WHERE split_group.split_group_key =
              'round3k.legacy.movable.family'
          AND plan.professional_split_plan_key =
              'round3k.legacy-candidate-contract-fixture'
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_POSITIVE=legacy_group_plan_move_remains_allowed failed';
    END IF;
    RAISE NOTICE
        'ROUND3M_POSITIVE=legacy_group_plan_move_remains_allowed PASS';
END
$legacy_group_move_remains_allowed$;

SELECT pg_temp.expect_round3m_failure(
    'non_target_plan_cannot_be_renamed_into_round3m_contract',
    $sql$
        UPDATE ml.professional_split_plan
        SET professional_split_plan_key =
            'round3m.descriptor-gate-holdout'
        WHERE professional_split_plan_key =
              'round3k.legacy-frozen-contract-fixture'
    $sql$,
    '23514', 'round3m_split_plan_identity_immutable_ck'
);

INSERT INTO ml.professional_split_plan (
    professional_split_plan_key, plan_version,
    deterministic_rule_version, lifecycle_status_code
) VALUES (
    'round3m.descriptor-gate-holdout', 1,
    'round3m-test-split-v1', 'CANDIDATE'
);

INSERT INTO ml.professional_split_group (
    professional_split_plan_id, split_group_kind_code,
    split_group_key, source_basis
)
SELECT professional_split_plan_id, 'COMPETITION_FAMILY',
       'round3m.test.family.not-admitted',
       'Transaction-local invalid family holdout fixture.'
FROM ml.professional_split_plan
WHERE professional_split_plan_key =
      'round3m.descriptor-gate-holdout'
  AND plan_version = 1;

SELECT pg_temp.expect_round3m_failure(
    'holdout_cannot_bind_candidate_split_plan',
    $sql$
        INSERT INTO audit.round3m_descriptor_holdout (
            holdout_key, holdout_kind, holdout_value, declared_at,
            declaration_receipt_sha256, professional_split_plan_id,
            professional_split_group_id
        )
        SELECT 'round3m.test.holdout.nonfrozen',
               'INDEPENDENT_SOURCE_FAMILY',
               split_group.split_group_key,
               transaction_timestamp(), repeat('b', 64),
               plan.professional_split_plan_id,
               split_group.professional_split_group_id
        FROM ml.professional_split_plan AS plan
        JOIN ml.professional_split_group AS split_group
          ON split_group.professional_split_plan_id =
             plan.professional_split_plan_id
        WHERE plan.professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND plan.plan_version = 1
    $sql$,
    '23514', 'round3m_holdout_frozen_split_binding_ck'
);

UPDATE ml.professional_split_plan
SET lifecycle_status_code = 'FROZEN',
    frozen_at = transaction_timestamp(),
    freeze_receipt_sha256 = repeat('b', 64)
WHERE professional_split_plan_key =
      'round3m.descriptor-gate-holdout'
  AND plan_version = 1;

SELECT pg_temp.expect_round3m_failure(
    'holdout_family_must_exist_and_be_admitted',
    $sql$
        INSERT INTO audit.round3m_descriptor_holdout (
            holdout_key, holdout_kind, holdout_value, declared_at,
            declaration_receipt_sha256, professional_split_plan_id,
            professional_split_group_id
        )
        SELECT 'round3m.test.holdout.unadmitted',
               'INDEPENDENT_SOURCE_FAMILY',
               split_group.split_group_key, plan.frozen_at,
               plan.freeze_receipt_sha256,
               plan.professional_split_plan_id,
               split_group.professional_split_group_id
        FROM ml.professional_split_plan AS plan
        JOIN ml.professional_split_group AS split_group
          ON split_group.professional_split_plan_id =
             plan.professional_split_plan_id
        WHERE plan.professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND plan.plan_version = 1
    $sql$,
    '23514', 'round3m_holdout_admitted_family_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'frozen_split_group_is_immutable',
    $sql$
        UPDATE ml.professional_split_group
        SET source_basis = 'Invalid post-freeze mutation.'
        WHERE professional_split_plan_id = (
            SELECT professional_split_plan_id
            FROM ml.professional_split_plan
            WHERE professional_split_plan_key =
                  'round3m.descriptor-gate-holdout'
              AND plan_version = 1
        )
    $sql$,
    '23514', 'round3m_frozen_split_children_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'frozen_split_cannot_accept_new_group',
    $sql$
        INSERT INTO ml.professional_split_group (
            professional_split_plan_id, split_group_kind_code,
            split_group_key, source_basis
        )
        SELECT professional_split_plan_id, 'COMPETITION_FAMILY',
               'round3m.test.family.post-freeze',
               'Invalid group inserted after freeze.'
        FROM ml.professional_split_plan
        WHERE professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND plan_version = 1
    $sql$,
    '23514', 'round3m_frozen_split_children_immutable_ck'
);

SELECT pg_temp.expect_round3m_failure(
    'frozen_split_plan_is_immutable',
    $sql$
        UPDATE ml.professional_split_plan
        SET deterministic_rule_version = 'invalid-post-freeze'
        WHERE professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND plan_version = 1
    $sql$,
    '23514', 'round3m_frozen_split_plan_immutable_ck'
);

INSERT INTO ml.professional_split_plan (
    professional_split_plan_key, plan_version,
    deterministic_rule_version, lifecycle_status_code
) VALUES (
    'round3m.descriptor-gate-holdout', 2,
    'round3m-test-split-v2', 'CANDIDATE'
);

INSERT INTO ml.professional_split_group (
    professional_split_plan_id, split_group_kind_code,
    split_group_key, source_basis
)
SELECT professional_split_plan_id, 'COMPETITION_FAMILY',
       'round3m.test.family.1',
       'Transaction-local admitted family holdout fixture.'
FROM ml.professional_split_plan
WHERE professional_split_plan_key =
      'round3m.descriptor-gate-holdout'
  AND plan_version = 2;

SELECT pg_temp.expect_round3m_failure(
    'split_group_cannot_move_between_plans',
    $sql$
        UPDATE ml.professional_split_group AS moving_group
        SET professional_split_plan_id = frozen_plan.professional_split_plan_id
        FROM ml.professional_split_plan AS frozen_plan
        JOIN ml.professional_split_plan AS candidate_plan
          ON candidate_plan.professional_split_plan_key =
             frozen_plan.professional_split_plan_key
         AND candidate_plan.plan_version = 2
        WHERE frozen_plan.professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND frozen_plan.plan_version = 1
          AND moving_group.professional_split_plan_id =
              candidate_plan.professional_split_plan_id
    $sql$,
    '23514', 'round3m_split_group_plan_immutable_ck'
);

UPDATE ml.professional_split_plan
SET lifecycle_status_code = 'FROZEN',
    frozen_at = transaction_timestamp(),
    freeze_receipt_sha256 = repeat('c', 64)
WHERE professional_split_plan_key =
      'round3m.descriptor-gate-holdout'
  AND plan_version = 2;

INSERT INTO audit.round3m_descriptor_holdout (
    holdout_key, holdout_kind, holdout_value, declared_at,
    declaration_receipt_sha256, professional_split_plan_id,
    professional_split_group_id
)
SELECT 'round3m.test.holdout.admitted-family-1',
       'INDEPENDENT_SOURCE_FAMILY', split_group.split_group_key,
       plan.frozen_at, plan.freeze_receipt_sha256,
       plan.professional_split_plan_id,
       split_group.professional_split_group_id
FROM ml.professional_split_plan AS plan
JOIN ml.professional_split_group AS split_group
  ON split_group.professional_split_plan_id =
     plan.professional_split_plan_id
WHERE plan.professional_split_plan_key =
      'round3m.descriptor-gate-holdout'
  AND plan.plan_version = 2;

DO $empty_frozen_group_never_counts_as_holdout$
DECLARE
    heldout_family_count BIGINT;
BEGIN
    SELECT held_out_independent_family_count
    INTO STRICT heldout_family_count
    FROM audit.v_round3m_descriptor_gate_metrics;

    IF heldout_family_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_NEGATIVE=empty_or_unassigned_holdout_group_counted value=%',
            heldout_family_count;
    END IF;
    RAISE NOTICE
        'ROUND3M_NEGATIVE=empty_or_unassigned_frozen_group_never_counts_as_holdout PASS';
END
$empty_frozen_group_never_counts_as_holdout$;

SELECT pg_temp.expect_round3m_failure(
    'holdout_declaration_is_immutable',
    $sql$
        UPDATE audit.round3m_descriptor_holdout
        SET active = FALSE
        WHERE holdout_key =
              'round3m.test.holdout.admitted-family-1'
    $sql$,
    '23514', 'round3m_immutable_evidence_ck'
);

DO $final_validation$
DECLARE
    failure_count BIGINT;
    failed_check RECORD;
BEGIN
    FOR failed_check IN
        SELECT check_key, violation_count
        FROM audit.run_round3m_gate_validation_queries()
        WHERE passed IS NOT TRUE OR violation_count <> 0
        ORDER BY check_key
    LOOP
        RAISE NOTICE 'ROUND3M_VALIDATION_FAILURE=% violations=%',
            failed_check.check_key, failed_check.violation_count;
    END LOOP;

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
