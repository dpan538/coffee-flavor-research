\set ON_ERROR_STOP on
\pset pager off

-- Read-only reconciliation of a deterministic restricted Round 3L ingest.

DO $round3l_restricted_ingestion_test$
DECLARE
    metric audit.v_round3l_acquisition_metrics%ROWTYPE;
    expected_descriptor_count BIGINT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM audit.round3l_source_census) THEN
        RAISE EXCEPTION 'Round 3L source census was not loaded';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM audit.round3l_source_attempt) THEN
        RAISE EXCEPTION 'Round 3L source attempts were not loaded';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM corpus.professional_acquisition_record
    ) THEN
        RAISE EXCEPTION 'Round 3L professional records were not loaded';
    END IF;

    IF (SELECT count(*) FROM corpus.professional_acquisition_record) <>
       (
           SELECT coalesce(sum(normalized_record_count), 0)
           FROM audit.round3l_source_attempt
       )
    THEN
        RAISE EXCEPTION
            'Round 3L loaded records do not reconcile to attempt totals';
    END IF;

    SELECT count(*) INTO STRICT expected_descriptor_count
    FROM corpus.professional_acquisition_assertion
    WHERE assertion_type IN (
        'OFFICIAL_JUDGE_DESCRIPTOR',
        'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR',
        'OFFICIAL_AGGREGATED_DESCRIPTOR'
    );

    IF expected_descriptor_count <> (
        SELECT coalesce(sum(descriptor_assertion_count), 0)
        FROM audit.round3l_source_attempt
    ) THEN
        RAISE EXCEPTION
            'Round 3L loaded descriptor assertions do not reconcile to attempt totals';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_acquisition_record AS record
        LEFT JOIN audit.round3l_corpus_state_event AS event
          ON event.professional_acquisition_record_id =
             record.professional_acquisition_record_id
         AND event.previous_state IS NULL
         AND event.new_state = record.corpus_state
        WHERE event.round3l_corpus_state_event_id IS NULL
    ) OR (
        SELECT count(*) FROM audit.round3l_corpus_state_event
    ) <> (
        SELECT count(*) FROM corpus.professional_acquisition_record
    ) THEN
        RAISE EXCEPTION
            'Round 3L records do not have exactly one matching initial state event';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.round3l_source_attempt AS attempt
        LEFT JOIN audit.round3l_source_census AS census
          ON census.round3l_source_census_id =
             attempt.round3l_source_census_id
        WHERE census.round3l_source_census_id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM corpus.professional_acquisition_record AS record
        LEFT JOIN audit.round3l_source_attempt AS attempt
          ON attempt.round3l_source_attempt_id =
             record.round3l_source_attempt_id
        WHERE attempt.round3l_source_attempt_id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM corpus.professional_acquisition_assertion AS assertion
        LEFT JOIN corpus.professional_acquisition_record AS record
          ON record.professional_acquisition_record_id =
             assertion.professional_acquisition_record_id
        WHERE record.professional_acquisition_record_id IS NULL
    ) THEN
        RAISE EXCEPTION 'Round 3L restricted ingest contains an orphaned foreign-key row';
    END IF;

    SELECT * INTO STRICT metric
    FROM audit.v_round3l_acquisition_metrics;

    IF metric.discovered_source_families <> (
           SELECT count(DISTINCT source_family_key)
           FROM audit.round3l_source_census
       )
       OR metric.discovered_editions <> (
           SELECT count(*)
           FROM audit.round3l_source_census
           WHERE item_kind IN ('COMPETITION_EDITION', 'PILOT_EDITION')
       )
       OR metric.attempted_sources <> (
           SELECT count(DISTINCT round3l_source_census_id)
           FROM audit.round3l_source_attempt
       )
       OR metric.completed_sources <> (
           SELECT count(*)
           FROM (
               SELECT round3l_source_census_id
               FROM audit.round3l_source_attempt
               GROUP BY round3l_source_census_id
               HAVING bool_and(outcome = 'COMPLETED')
           ) AS completed_source
       )
       OR metric.acquired_file_count <> (
           SELECT count(*)
           FROM audit.round3l_source_attempt
           WHERE source_snapshot_sha256 IS NOT NULL
       )
       OR metric.acquired_byte_count <> (
           SELECT coalesce(sum(artifact_byte_count), 0)
           FROM audit.round3l_source_attempt
       )
       OR metric.parsed_row_count <> (
           SELECT coalesce(sum(parsed_row_count), 0)
           FROM audit.round3l_source_attempt
       )
       OR metric.ingested_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
       )
       OR metric.research_staged_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE corpus_state = 'RESEARCH_STAGED'
       )
       OR metric.reviewed_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE corpus_state IN ('REVIEWED', 'MODEL_ELIGIBLE')
       )
       OR metric.preparation_confirmed_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE fresh_preparation_status = 'CONFIRMED'
       )
       OR metric.c0_reported_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE c0_source_status = 'REPORTED'
       )
       OR metric.c1_reviewed_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE c1_evidence_status = 'REVIEWED'
       )
       OR metric.duplicate_loss_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE deduplication_disposition = 'DUPLICATE_PUBLICATION'
       )
       OR metric.mirror_loss_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE deduplication_disposition = 'MIRROR'
       )
       OR metric.repeated_service_loss_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE deduplication_disposition = 'REPEATED_SERVICE'
       )
       OR metric.staged_core_candidate_count <> (
           SELECT count(*) FROM corpus.v_round3l_core_candidate
       )
       OR metric.staged_observed_core_eligible_count <> (
           SELECT count(*)
           FROM corpus.v_round3l_core_candidate
           WHERE observed_rights_eligible
       )
       OR metric.staged_model_rights_eligible_count <> (
           SELECT count(*)
           FROM corpus.v_round3l_core_candidate
           WHERE model_rights_eligible
       )
       OR metric.model_eligible_record_count <> (
           SELECT count(*)
           FROM corpus.professional_acquisition_record
           WHERE corpus_state = 'MODEL_ELIGIBLE'
       )
       OR metric.professional_descriptor_assertion_count <>
          expected_descriptor_count
       OR metric.open_external_blocker_count <> (
           SELECT count(*)
           FROM audit.round3l_blocker_queue
           WHERE blocker_state = 'OPEN'
       )
       OR metric.remaining_gap_to_7000 <>
          greatest(7000 - metric.staged_observed_core_eligible_count, 0)
       OR metric.remaining_gap_to_10000 <>
          greatest(10000 - metric.staged_observed_core_eligible_count, 0)
    THEN
        RAISE EXCEPTION
            'Round 3L restricted-ingest metric reconciliation failed: %',
            row_to_json(metric);
    END IF;

    IF (
        SELECT coalesce(sum(record_count), 0)
        FROM audit.v_round3l_rights_distribution
    ) <> metric.ingested_record_count THEN
        RAISE EXCEPTION
            'Round 3L rights distribution does not reconcile to records';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM audit.run_round3l_validation_queries()
    ) OR EXISTS (
        SELECT 1
        FROM audit.run_round3l_validation_queries()
        WHERE passed IS NOT TRUE OR violation_count <> 0
    ) THEN
        RAISE EXCEPTION
            'Round 3L restricted acquisition validation contract failed';
    END IF;
END
$round3l_restricted_ingestion_test$;

SELECT 'ROUND3L_RESTRICTED_INGESTION_PASS' AS result;
