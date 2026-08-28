\set ON_ERROR_STOP on
\pset pager off

-- Round 3L four-state acquisition, blocker-continuation, rights, and
-- anti-inflation failure paths.  Every fixture is transaction-local.

BEGIN;

CREATE TEMP TABLE round3l_metric_baseline ON COMMIT DROP AS
SELECT * FROM audit.v_round3l_acquisition_metrics;

CREATE FUNCTION pg_temp.expect_round3l_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3l_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION
            'Round 3L negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND3L_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3l_failure$;

INSERT INTO audit.round3l_restricted_ingest_freeze (
    freeze_id,
    manifest_sha256,
    census_row_count,
    attempt_row_count,
    professional_record_row_count,
    professional_assertion_row_count,
    blocker_row_count
) VALUES (
    'round3l.test.freeze', repeat('f', 64), 2, 2, 2, 1, 1
);

INSERT INTO audit.round3l_source_census (
    census_version, census_item_key, item_kind, series_key,
    source_family_key, edition_label, edition_year,
    country_or_community, official_url, discovery_basis,
    current_corpus_state, acquisition_state, rights_state,
    discovered_at
) VALUES
(
    'round3l-test-v1', 'edition:test:open', 'COMPETITION_EDITION',
    'test_series', 'test_family_open', 'Open fixture edition', 2026,
    'Test origin', 'https://example.test/open', 'TRANSACTION_FIXTURE',
    'DISCOVERED', 'PUBLIC_OFFICIAL_EDITION_ROUTE',
    'UNKNOWN_DIMENSION_SPECIFIC', '2026-08-28T00:00:00Z'
),
(
    'round3l-test-v1', 'edition:test:blocked', 'COMPETITION_EDITION',
    'test_series', 'test_family_blocked', 'Blocked fixture edition', 2025,
    'Test origin', 'https://example.test/blocked', 'TRANSACTION_FIXTURE',
    'DISCOVERED', 'REQUEST_REQUIRED', 'UNKNOWN_DIMENSION_SPECIFIC',
    '2026-08-28T00:00:00Z'
);

INSERT INTO audit.round3l_source_attempt (
    attempt_key, round3l_source_census_id, lane_key, attempt_sequence,
    attempted_at, acquisition_method, outcome, canonical_url, final_url,
    http_status, source_snapshot_sha256, artifact_byte_count,
    parsed_row_count, normalized_record_count,
    descriptor_assertion_count, next_cursor
)
SELECT
    'round3l.test.open.1', round3l_source_census_id, 'round3l_test', 1,
    '2026-08-28T00:01:00Z', 'OFFICIAL_HTTPS_SNAPSHOT', 'COMPLETED',
    official_url, official_url, 200, repeat('a', 64), 1024, 2, 2, 1,
    'edition:test:blocked|attempt official route'
FROM audit.round3l_source_census
WHERE census_version = 'round3l-test-v1'
  AND census_item_key = 'edition:test:open';

INSERT INTO audit.round3l_source_attempt (
    attempt_key, round3l_source_census_id, lane_key, attempt_sequence,
    attempted_at, acquisition_method, outcome, canonical_url,
    artifact_byte_count, parsed_row_count, normalized_record_count,
    descriptor_assertion_count, external_action_type, blocker_detail,
    next_cursor
)
SELECT
    'round3l.test.blocked.2', round3l_source_census_id, 'round3l_test', 2,
    '2026-08-28T00:02:00Z', 'OFFICIAL_PUBLIC_ROUTE_REVIEW',
    'BLOCKED_EXTERNAL_ACTION', official_url, 0, 0, 0, 0,
    'ORGANIZER_RESPONSE', 'Underlying score export is organizer-held.',
    'edition:test:after_blocked|continue without waiting'
FROM audit.round3l_source_census
WHERE census_version = 'round3l-test-v1'
  AND census_item_key = 'edition:test:blocked';

INSERT INTO audit.round3l_blocker_queue (
    blocker_key, round3l_source_attempt_id, external_action_type,
    blocker_state, recorded_at, continuation_cursor
)
SELECT
    'round3l.test.blocker.organizer', round3l_source_attempt_id,
    'ORGANIZER_RESPONSE', 'OPEN', '2026-08-28T00:02:01Z',
    'edition:test:after_blocked|continue without waiting'
FROM audit.round3l_source_attempt
WHERE attempt_key = 'round3l.test.blocked.2';

INSERT INTO corpus.professional_acquisition_record (
    professional_acquisition_record_key, round3l_source_attempt_id,
    source_family_key, series_key, edition_key, edition_year,
    category_key, round_key, source_record_key, entry_or_lot_key,
    coffee_identity_key, preparation_service_code,
    effective_record_key, evidence_tier, payload_kind,
    official_score_value, official_score_text, official_score_scale,
    fresh_preparation_status, fresh_preparation_evidence_locator,
    c0_source_status, c0_family, c1_evidence_status,
    source_snapshot_sha256, raw_record_sha256,
    public_results_use, public_descriptor_use, internal_research_use,
    public_derived_release, model_research_use, commercial_model_use,
    deduplication_disposition, corpus_state, label_review_status,
    ingested_at
)
SELECT
    'round3l.test.record.canonical', round3l_source_attempt_id,
    'test_family_open', 'test_series', 'test_2026', 2026,
    'cupping', 'final', 'LOT-1', 'LOT-1', 'COFFEE-1',
    'green_competition_cupping',
    'test_series|test_2026|cupping|final|LOT-1|green_competition_cupping',
    'P2', 'OFFICIAL_SCORE_AND_DESCRIPTOR', 90.25, '90.25',
    'SOURCE_TOTAL_100', 'CONFIRMED',
    'https://example.test/protocol#cupping', 'REPORTED',
    'filter_percolation', 'NOT_REPORTED', repeat('a', 64),
    repeat('b', 64), 'PENDING', 'PENDING', 'PENDING', 'PENDING',
    'PENDING', 'PENDING', 'CANONICAL', 'RESEARCH_STAGED',
    'NOT_REVIEWED', '2026-08-28T00:03:00Z'
FROM audit.round3l_source_attempt
WHERE attempt_key = 'round3l.test.open.1';

INSERT INTO corpus.professional_acquisition_record (
    professional_acquisition_record_key, round3l_source_attempt_id,
    source_family_key, series_key, edition_key, edition_year,
    category_key, round_key, source_record_key, entry_or_lot_key,
    coffee_identity_key, preparation_service_code,
    evidence_tier, payload_kind, official_score_value,
    official_score_text, official_score_scale,
    fresh_preparation_status, fresh_preparation_evidence_locator,
    c0_source_status, c0_family, c1_evidence_status,
    source_snapshot_sha256, raw_record_sha256,
    public_results_use, public_descriptor_use, internal_research_use,
    public_derived_release, model_research_use, commercial_model_use,
    deduplication_disposition, canonical_record_key,
    duplicate_group_key, corpus_state, label_review_status, ingested_at
)
SELECT
    'round3l.test.record.duplicate', round3l_source_attempt_id,
    'test_family_open', 'test_series', 'test_2026', 2026,
    'cupping', 'final', 'LOT-1-MIRROR', 'LOT-1', 'COFFEE-1',
    'green_competition_cupping', 'P2', 'OFFICIAL_STRUCTURED_SCORE',
    90.25, '90.25', 'SOURCE_TOTAL_100', 'CONFIRMED',
    'https://example.test/protocol#cupping', 'REPORTED',
    'filter_percolation', 'NOT_REPORTED', repeat('a', 64),
    repeat('c', 64), 'PENDING', 'PENDING', 'PENDING', 'PENDING',
    'PENDING', 'PENDING', 'DUPLICATE_PUBLICATION',
    'round3l.test.record.canonical', 'round3l.test.duplicate.group.1',
    'RESEARCH_STAGED', 'NOT_APPLICABLE', '2026-08-28T00:03:01Z'
FROM audit.round3l_source_attempt
WHERE attempt_key = 'round3l.test.open.1';

INSERT INTO corpus.professional_acquisition_assertion (
    professional_acquisition_assertion_key,
    professional_acquisition_record_id, assertion_type, source_locator,
    source_language_code, assertion_text_sha256, text_storage_state,
    created_at
)
SELECT
    'round3l.test.assertion.1', professional_acquisition_record_id,
    'OFFICIAL_AGGREGATED_DESCRIPTOR',
    'https://example.test/open#lot-1-descriptor-1', 'en',
    repeat('d', 64), 'HASH_ONLY', '2026-08-28T00:04:00Z'
FROM corpus.professional_acquisition_record
WHERE professional_acquisition_record_key =
      'round3l.test.record.canonical';

DO $metrics$
DECLARE
    metric audit.v_round3l_acquisition_metrics%ROWTYPE;
    baseline audit.v_round3l_acquisition_metrics%ROWTYPE;
BEGIN
    SELECT * INTO STRICT metric FROM audit.v_round3l_acquisition_metrics;
    SELECT * INTO STRICT baseline FROM round3l_metric_baseline;
    IF metric.discovered_source_families <>
          baseline.discovered_source_families + 2
       OR metric.discovered_editions <> baseline.discovered_editions + 2
       OR metric.attempted_sources <> baseline.attempted_sources + 2
       OR metric.completed_sources <> baseline.completed_sources + 1
       OR metric.acquired_file_count <> baseline.acquired_file_count + 1
       OR metric.parsed_row_count <> baseline.parsed_row_count + 2
       OR metric.ingested_record_count <> baseline.ingested_record_count + 2
       OR metric.research_staged_record_count <>
          baseline.research_staged_record_count + 2
       OR metric.staged_core_candidate_count <>
          baseline.staged_core_candidate_count + 1
       OR metric.staged_observed_core_eligible_count <>
          baseline.staged_observed_core_eligible_count
       OR metric.professional_descriptor_assertion_count <>
          baseline.professional_descriptor_assertion_count + 1
       OR metric.duplicate_loss_count <> baseline.duplicate_loss_count + 1
       OR metric.open_external_blocker_count <>
          baseline.open_external_blocker_count + 1
       OR metric.remaining_gap_to_7000 <> baseline.remaining_gap_to_7000
       OR metric.remaining_gap_to_10000 <> baseline.remaining_gap_to_10000 THEN
        RAISE EXCEPTION 'Round 3L metric fixture mismatch: %', row_to_json(metric);
    END IF;
END
$metrics$;

UPDATE corpus.professional_acquisition_record
SET corpus_state = 'REVIEWED',
    reviewed_at = '2026-08-28T00:05:00Z'
WHERE professional_acquisition_record_key =
      'round3l.test.record.canonical';

SELECT pg_temp.expect_round3l_failure(
    'state_regression',
    $sql$
        UPDATE corpus.professional_acquisition_record
        SET corpus_state = 'RESEARCH_STAGED'
        WHERE professional_acquisition_record_key =
              'round3l.test.record.canonical'
    $sql$,
    '23514',
    'professional_acquisition_state_regression_ck'
);

SELECT pg_temp.expect_round3l_failure(
    'pending_rights_cannot_be_model_eligible',
    $sql$
        UPDATE corpus.professional_acquisition_record
        SET corpus_state = 'MODEL_ELIGIBLE',
            model_eligible_at = '2026-08-28T00:06:00Z',
            label_review_status = 'REVIEWED'
        WHERE professional_acquisition_record_key =
              'round3l.test.record.canonical'
    $sql$,
    '23514',
    'professional_acquisition_record_state_ck'
);

SELECT pg_temp.expect_round3l_failure(
    'synthetic_record_rejected',
    $sql$
        UPDATE corpus.professional_acquisition_record
        SET is_synthetic = TRUE
        WHERE professional_acquisition_record_key =
              'round3l.test.record.duplicate'
    $sql$,
    '23514',
    'professional_acquisition_record_real_only_ck'
);

SELECT pg_temp.expect_round3l_failure(
    'blocker_requires_external_action_type',
    $sql$
        UPDATE audit.round3l_source_attempt
        SET external_action_type = NULL
        WHERE attempt_key = 'round3l.test.blocked.2'
    $sql$,
    '23514',
    'round3l_source_attempt_blocker_ck'
);

SELECT pg_temp.expect_round3l_failure(
    'restricted_freeze_manifest_hash_required',
    $sql$
        UPDATE audit.round3l_restricted_ingest_freeze
        SET manifest_sha256 = 'not-a-sha256'
        WHERE freeze_id = 'round3l.test.freeze'
    $sql$,
    '23514',
    'round3l_restricted_ingest_freeze_text_ck'
);

DO $validation$
DECLARE
    failure_count BIGINT;
BEGIN
    SELECT count(*) INTO STRICT failure_count
    FROM audit.run_round3l_validation_queries()
    WHERE passed IS NOT TRUE OR violation_count <> 0;
    IF failure_count <> 0 THEN
        RAISE EXCEPTION 'Round 3L validation fixture has % failures', failure_count;
    END IF;
END
$validation$;

ROLLBACK;

SELECT 'ROUND3L_ACQUISITION_PASS' AS result;
