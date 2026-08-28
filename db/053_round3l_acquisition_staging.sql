-- Round 3L real-source acquisition staging and four-state governance.
--
-- This migration exists because rights-pending public snapshots must remain
-- ingestible without weakening the authoritative Round 3K observed/model gate.
-- DISCOVERED and RESEARCH_STAGED rows are evidence-preserving acquisition
-- states; REVIEWED records have completed source QA; MODEL_ELIGIBLE additionally
-- requires affirmative internal/model-research rights.  No state authorizes
-- model training in this round.

BEGIN;

CREATE TABLE audit.round3l_source_census (
    round3l_source_census_id BIGINT GENERATED ALWAYS AS IDENTITY,
    census_version TEXT NOT NULL,
    census_item_key TEXT NOT NULL,
    item_kind TEXT NOT NULL,
    parent_key TEXT,
    series_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    edition_label TEXT,
    edition_year INTEGER,
    country_or_community TEXT,
    category_or_round TEXT,
    official_url TEXT NOT NULL,
    discovery_basis TEXT NOT NULL,
    source_snapshot_sha256 TEXT,
    current_corpus_state TEXT NOT NULL DEFAULT 'DISCOVERED',
    acquisition_state TEXT NOT NULL,
    rights_state TEXT NOT NULL,
    note TEXT,
    discovered_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT round3l_source_census_pk PRIMARY KEY (round3l_source_census_id),
    CONSTRAINT round3l_source_census_key_uq UNIQUE (
        census_version, census_item_key
    ),
    CONSTRAINT round3l_source_census_item_kind_ck CHECK (
        item_kind IN (
            'COMPETITION_SERIES',
            'SOURCE_ACCESS_ROUTE',
            'COMPETITION_EDITION',
            'PILOT_EDITION',
            'EDITION_COUNT_CLAIM',
            'RESULT_ARCHIVE',
            'SCORESHEET'
        )
    ),
    CONSTRAINT round3l_source_census_state_ck CHECK (
        current_corpus_state IN (
            'DISCOVERED', 'RESEARCH_STAGED', 'REVIEWED', 'MODEL_ELIGIBLE'
        )
    ),
    CONSTRAINT round3l_source_census_text_ck CHECK (
        census_version = btrim(census_version)
        AND census_version <> ''
        AND census_item_key = btrim(census_item_key)
        AND census_item_key <> ''
        AND series_key = btrim(series_key)
        AND series_key <> ''
        AND source_family_key = btrim(source_family_key)
        AND source_family_key <> ''
        AND official_url = btrim(official_url)
        AND official_url <> ''
        AND discovery_basis = btrim(discovery_basis)
        AND discovery_basis <> ''
        AND acquisition_state = btrim(acquisition_state)
        AND acquisition_state <> ''
        AND rights_state = btrim(rights_state)
        AND rights_state <> ''
    ),
    CONSTRAINT round3l_source_census_year_ck CHECK (
        edition_year IS NULL OR edition_year BETWEEN 1900 AND 2100
    ),
    CONSTRAINT round3l_source_census_hash_ck CHECK (
        source_snapshot_sha256 IS NULL
        OR source_snapshot_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE audit.round3l_source_attempt (
    round3l_source_attempt_id BIGINT GENERATED ALWAYS AS IDENTITY,
    attempt_key TEXT NOT NULL,
    round3l_source_census_id BIGINT NOT NULL,
    lane_key TEXT NOT NULL,
    attempt_sequence INTEGER NOT NULL,
    attempted_at TIMESTAMPTZ NOT NULL,
    acquisition_method TEXT NOT NULL,
    outcome TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    final_url TEXT,
    http_status SMALLINT,
    source_snapshot_sha256 TEXT,
    artifact_byte_count BIGINT NOT NULL DEFAULT 0,
    parsed_row_count BIGINT NOT NULL DEFAULT 0,
    normalized_record_count BIGINT NOT NULL DEFAULT 0,
    descriptor_assertion_count BIGINT NOT NULL DEFAULT 0,
    external_action_type TEXT,
    blocker_detail TEXT,
    next_cursor TEXT NOT NULL,
    evidence_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT round3l_source_attempt_pk PRIMARY KEY (
        round3l_source_attempt_id
    ),
    CONSTRAINT round3l_source_attempt_key_uq UNIQUE (attempt_key),
    CONSTRAINT round3l_source_attempt_sequence_uq UNIQUE (
        lane_key, attempt_sequence
    ),
    CONSTRAINT round3l_source_attempt_census_fk FOREIGN KEY (
        round3l_source_census_id
    ) REFERENCES audit.round3l_source_census (round3l_source_census_id),
    CONSTRAINT round3l_source_attempt_text_ck CHECK (
        attempt_key = lower(btrim(attempt_key))
        AND attempt_key <> ''
        AND lane_key = lower(btrim(lane_key))
        AND lane_key <> ''
        AND acquisition_method = btrim(acquisition_method)
        AND acquisition_method <> ''
        AND canonical_url = btrim(canonical_url)
        AND canonical_url <> ''
        AND next_cursor = btrim(next_cursor)
        AND next_cursor <> ''
    ),
    CONSTRAINT round3l_source_attempt_sequence_ck CHECK (
        attempt_sequence > 0
    ),
    CONSTRAINT round3l_source_attempt_outcome_ck CHECK (
        outcome IN (
            'COMPLETED',
            'PARTIAL',
            'BLOCKED_EXTERNAL_ACTION',
            'NOT_FOUND',
            'NO_RECORD_PAYLOAD',
            'TRANSIENT_TECHNICAL_FAILURE'
        )
    ),
    CONSTRAINT round3l_source_attempt_http_ck CHECK (
        http_status IS NULL OR http_status BETWEEN 100 AND 599
    ),
    CONSTRAINT round3l_source_attempt_hash_ck CHECK (
        source_snapshot_sha256 IS NULL
        OR source_snapshot_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3l_source_attempt_counts_ck CHECK (
        artifact_byte_count >= 0
        AND parsed_row_count >= 0
        AND normalized_record_count >= 0
        AND descriptor_assertion_count >= 0
        AND normalized_record_count <= parsed_row_count
    ),
    CONSTRAINT round3l_source_attempt_blocker_ck CHECK (
        (
            outcome = 'BLOCKED_EXTERNAL_ACTION'
            AND external_action_type IS NOT NULL
            AND external_action_type IN (
                'PERMISSION',
                'PURCHASE',
                'CREDENTIALS',
                'CONTRACT_ACCEPTANCE',
                'ORGANIZER_RESPONSE',
                'VENDOR_EXPORT'
            )
            AND blocker_detail IS NOT NULL
            AND btrim(blocker_detail) <> ''
        )
        OR (
            outcome <> 'BLOCKED_EXTERNAL_ACTION'
            AND external_action_type IS NULL
        )
    ),
    CONSTRAINT round3l_source_attempt_artifact_ck CHECK (
        source_snapshot_sha256 IS NULL
        OR artifact_byte_count > 0
    )
);

CREATE TABLE audit.round3l_blocker_queue (
    round3l_blocker_queue_id BIGINT GENERATED ALWAYS AS IDENTITY,
    blocker_key TEXT NOT NULL,
    round3l_source_attempt_id BIGINT NOT NULL,
    external_action_type TEXT NOT NULL,
    blocker_state TEXT NOT NULL DEFAULT 'OPEN',
    recorded_at TIMESTAMPTZ NOT NULL,
    resolution_evidence TEXT,
    continuation_cursor TEXT NOT NULL,
    CONSTRAINT round3l_blocker_queue_pk PRIMARY KEY (
        round3l_blocker_queue_id
    ),
    CONSTRAINT round3l_blocker_queue_key_uq UNIQUE (blocker_key),
    CONSTRAINT round3l_blocker_queue_attempt_uq UNIQUE (
        round3l_source_attempt_id
    ),
    CONSTRAINT round3l_blocker_queue_attempt_fk FOREIGN KEY (
        round3l_source_attempt_id
    ) REFERENCES audit.round3l_source_attempt (round3l_source_attempt_id),
    CONSTRAINT round3l_blocker_queue_type_ck CHECK (
        external_action_type IN (
            'PERMISSION',
            'PURCHASE',
            'CREDENTIALS',
            'CONTRACT_ACCEPTANCE',
            'ORGANIZER_RESPONSE',
            'VENDOR_EXPORT'
        )
    ),
    CONSTRAINT round3l_blocker_queue_state_ck CHECK (
        blocker_state IN ('OPEN', 'AUTHORIZED', 'RESOLVED', 'DECLINED')
    ),
    CONSTRAINT round3l_blocker_queue_text_ck CHECK (
        blocker_key = lower(btrim(blocker_key))
        AND blocker_key <> ''
        AND continuation_cursor = btrim(continuation_cursor)
        AND continuation_cursor <> ''
    ),
    CONSTRAINT round3l_blocker_queue_resolution_ck CHECK (
        blocker_state = 'OPEN'
        OR (
            resolution_evidence IS NOT NULL
            AND btrim(resolution_evidence) <> ''
        )
    )
);

CREATE TABLE corpus.professional_acquisition_record (
    professional_acquisition_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_acquisition_record_key TEXT NOT NULL,
    round3l_source_attempt_id BIGINT NOT NULL,
    source_family_key TEXT NOT NULL,
    series_key TEXT NOT NULL,
    edition_key TEXT NOT NULL,
    edition_year INTEGER NOT NULL,
    category_key TEXT NOT NULL,
    round_key TEXT NOT NULL,
    source_record_key TEXT NOT NULL,
    entry_or_lot_key TEXT NOT NULL,
    coffee_identity_key TEXT,
    preparation_service_code TEXT,
    effective_record_key TEXT,
    evidence_tier TEXT NOT NULL,
    payload_kind TEXT NOT NULL,
    official_score_value NUMERIC,
    official_score_text TEXT,
    official_score_scale TEXT,
    fresh_preparation_status TEXT NOT NULL,
    fresh_preparation_evidence_locator TEXT,
    c0_source_status TEXT NOT NULL,
    c0_family TEXT,
    source_native_roast_value TEXT,
    source_native_roast_scheme TEXT,
    c1_evidence_status TEXT NOT NULL,
    reviewed_c1_mapping TEXT,
    source_snapshot_sha256 TEXT NOT NULL,
    raw_record_sha256 TEXT NOT NULL,
    public_results_use TEXT NOT NULL,
    public_descriptor_use TEXT NOT NULL,
    internal_research_use TEXT NOT NULL,
    public_derived_release TEXT NOT NULL,
    model_research_use TEXT NOT NULL,
    commercial_model_use TEXT NOT NULL,
    deduplication_disposition TEXT NOT NULL DEFAULT 'CANONICAL',
    canonical_record_key TEXT,
    duplicate_group_key TEXT,
    mirror_group_key TEXT,
    repeat_group_key TEXT,
    corpus_state TEXT NOT NULL DEFAULT 'RESEARCH_STAGED',
    label_review_status TEXT NOT NULL DEFAULT 'NOT_REVIEWED',
    is_synthetic BOOLEAN NOT NULL DEFAULT FALSE,
    semantic_inference_used BOOLEAN NOT NULL DEFAULT FALSE,
    ingested_at TIMESTAMPTZ NOT NULL,
    reviewed_at TIMESTAMPTZ,
    model_eligible_at TIMESTAMPTZ,
    CONSTRAINT professional_acquisition_record_pk PRIMARY KEY (
        professional_acquisition_record_id
    ),
    CONSTRAINT professional_acquisition_record_key_uq UNIQUE (
        professional_acquisition_record_key
    ),
    CONSTRAINT professional_acquisition_record_source_uq UNIQUE (
        round3l_source_attempt_id, source_record_key
    ),
    CONSTRAINT professional_acquisition_record_attempt_fk FOREIGN KEY (
        round3l_source_attempt_id
    ) REFERENCES audit.round3l_source_attempt (round3l_source_attempt_id),
    CONSTRAINT professional_acquisition_record_text_ck CHECK (
        professional_acquisition_record_key =
            lower(btrim(professional_acquisition_record_key))
        AND professional_acquisition_record_key <> ''
        AND source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND series_key = lower(btrim(series_key))
        AND series_key <> ''
        AND edition_key = lower(btrim(edition_key))
        AND edition_key <> ''
        AND category_key = lower(btrim(category_key))
        AND category_key <> ''
        AND round_key = lower(btrim(round_key))
        AND round_key <> ''
        AND source_record_key = btrim(source_record_key)
        AND source_record_key <> ''
        AND entry_or_lot_key = btrim(entry_or_lot_key)
        AND entry_or_lot_key <> ''
    ),
    CONSTRAINT professional_acquisition_record_year_ck CHECK (
        edition_year BETWEEN 1900 AND 2100
    ),
    CONSTRAINT professional_acquisition_record_tier_ck CHECK (
        evidence_tier IN ('P0', 'P1', 'P2', 'P3', 'P4', 'P5')
    ),
    CONSTRAINT professional_acquisition_record_payload_ck CHECK (
        payload_kind IN (
            'OFFICIAL_STRUCTURED_SCORE',
            'OFFICIAL_DESCRIPTOR',
            'OFFICIAL_SCORE_AND_DESCRIPTOR',
            'RANKING_ONLY',
            'RESULT_METADATA_ONLY'
        )
    ),
    CONSTRAINT professional_acquisition_record_score_ck CHECK (
        official_score_value IS NULL
        OR official_score_text IS NOT NULL
    ),
    CONSTRAINT professional_acquisition_record_fresh_ck CHECK (
        fresh_preparation_status IN (
            'CONFIRMED', 'PENDING', 'NOT_CONFIRMED', 'NOT_APPLICABLE'
        )
        AND (
            fresh_preparation_status <> 'CONFIRMED'
            OR (
                preparation_service_code IS NOT NULL
                AND fresh_preparation_evidence_locator IS NOT NULL
                AND btrim(fresh_preparation_evidence_locator) <> ''
            )
        )
    ),
    CONSTRAINT professional_acquisition_record_c0_ck CHECK (
        c0_source_status IN (
            'REPORTED',
            'NOT_REPORTED',
            'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED',
            'NOT_APPLICABLE'
        )
        AND (c0_source_status <> 'REPORTED' OR c0_family IS NOT NULL)
    ),
    CONSTRAINT professional_acquisition_record_c1_ck CHECK (
        c1_evidence_status IN (
            'REVIEWED',
            'REPORTED_UNRESOLVED',
            'NOT_REPORTED',
            'SOURCE_UNKNOWN',
            'NOT_APPLICABLE'
        )
        AND (
            c1_evidence_status <> 'REVIEWED'
            OR reviewed_c1_mapping IN (
                'extremely_light',
                'light',
                'medium_light',
                'medium',
                'medium_dark',
                'dark',
                'extremely_dark'
            )
        )
    ),
    CONSTRAINT professional_acquisition_record_hash_ck CHECK (
        source_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND raw_record_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT professional_acquisition_record_rights_ck CHECK (
        public_results_use IN (
            'ALLOWED', 'PROHIBITED', 'PENDING', 'UNKNOWN', 'NOT_APPLICABLE'
        )
        AND public_descriptor_use IN (
            'ALLOWED', 'PROHIBITED', 'PENDING', 'UNKNOWN', 'NOT_APPLICABLE'
        )
        AND internal_research_use IN (
            'ALLOWED', 'PROHIBITED', 'PENDING', 'UNKNOWN', 'NOT_APPLICABLE'
        )
        AND public_derived_release IN (
            'ALLOWED', 'PROHIBITED', 'PENDING', 'UNKNOWN', 'NOT_APPLICABLE'
        )
        AND model_research_use IN (
            'ALLOWED', 'PROHIBITED', 'PENDING', 'UNKNOWN', 'NOT_APPLICABLE'
        )
        AND commercial_model_use IN (
            'ALLOWED', 'PROHIBITED', 'PENDING', 'UNKNOWN', 'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT professional_acquisition_record_dedup_ck CHECK (
        deduplication_disposition IN (
            'CANONICAL',
            'DUPLICATE_PUBLICATION',
            'MIRROR',
            'REPEATED_SERVICE',
            'UNRESOLVED'
        )
        AND (
            (
                deduplication_disposition = 'CANONICAL'
                AND canonical_record_key IS NULL
            )
            OR (
                deduplication_disposition <> 'CANONICAL'
                AND canonical_record_key IS NOT NULL
                AND canonical_record_key <>
                    professional_acquisition_record_key
            )
        )
        AND (
            deduplication_disposition = 'CANONICAL'
            OR effective_record_key IS NULL
        )
    ),
    CONSTRAINT professional_acquisition_record_state_ck CHECK (
        corpus_state IN (
            'DISCOVERED', 'RESEARCH_STAGED', 'REVIEWED', 'MODEL_ELIGIBLE'
        )
        AND (
            corpus_state NOT IN ('REVIEWED', 'MODEL_ELIGIBLE')
            OR reviewed_at IS NOT NULL
        )
        AND (
            corpus_state <> 'MODEL_ELIGIBLE'
            OR (
                evidence_tier IN ('P1', 'P2')
                AND payload_kind IN (
                    'OFFICIAL_STRUCTURED_SCORE',
                    'OFFICIAL_DESCRIPTOR',
                    'OFFICIAL_SCORE_AND_DESCRIPTOR'
                )
                AND fresh_preparation_status = 'CONFIRMED'
                AND effective_record_key IS NOT NULL
                AND internal_research_use = 'ALLOWED'
                AND model_research_use = 'ALLOWED'
                AND deduplication_disposition = 'CANONICAL'
                AND label_review_status IN ('REVIEWED', 'NOT_APPLICABLE')
                AND model_eligible_at IS NOT NULL
            )
        )
    ),
    CONSTRAINT professional_acquisition_record_label_review_ck CHECK (
        label_review_status IN (
            'NOT_REVIEWED', 'PENDING', 'REVIEWED', 'ABSTAINED', 'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT professional_acquisition_record_real_only_ck CHECK (
        is_synthetic IS FALSE
        AND semantic_inference_used IS FALSE
    )
);

CREATE UNIQUE INDEX professional_acquisition_effective_canonical_uq
    ON corpus.professional_acquisition_record (effective_record_key)
    WHERE effective_record_key IS NOT NULL
      AND deduplication_disposition = 'CANONICAL';

CREATE INDEX professional_acquisition_state_idx
    ON corpus.professional_acquisition_record (
        corpus_state, evidence_tier, payload_kind
    );

CREATE INDEX professional_acquisition_family_idx
    ON corpus.professional_acquisition_record (
        source_family_key, series_key, edition_year
    );

CREATE TABLE corpus.professional_acquisition_assertion (
    professional_acquisition_assertion_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_acquisition_assertion_key TEXT NOT NULL,
    professional_acquisition_record_id BIGINT NOT NULL,
    assertion_type TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    source_language_code TEXT,
    source_defined_descriptor_key TEXT,
    assertion_text TEXT,
    assertion_text_sha256 TEXT NOT NULL,
    text_storage_state TEXT NOT NULL,
    semantic_inference_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT professional_acquisition_assertion_pk PRIMARY KEY (
        professional_acquisition_assertion_id
    ),
    CONSTRAINT professional_acquisition_assertion_key_uq UNIQUE (
        professional_acquisition_assertion_key
    ),
    CONSTRAINT professional_acquisition_assertion_record_fk FOREIGN KEY (
        professional_acquisition_record_id
    ) REFERENCES corpus.professional_acquisition_record (
        professional_acquisition_record_id
    ),
    CONSTRAINT professional_acquisition_assertion_text_ck CHECK (
        professional_acquisition_assertion_key =
            lower(btrim(professional_acquisition_assertion_key))
        AND professional_acquisition_assertion_key <> ''
        AND source_locator = btrim(source_locator)
        AND source_locator <> ''
        AND assertion_text_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT professional_acquisition_assertion_type_ck CHECK (
        assertion_type IN (
            'OFFICIAL_JUDGE_DESCRIPTOR',
            'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR',
            'OFFICIAL_AGGREGATED_DESCRIPTOR',
            'OFFICIAL_STRUCTURED_SCORE',
            'COMPETITOR_DECLARED_DESCRIPTOR',
            'ROASTER_SUBMITTED_DESCRIPTOR',
            'ORGANIZER_MARKETING_DESCRIPTION'
        )
    ),
    CONSTRAINT professional_acquisition_assertion_storage_ck CHECK (
        text_storage_state IN (
            'HASH_ONLY', 'CAPTURED_RESTRICTED', 'REVIEWED_TEXT'
        )
        AND (
            text_storage_state <> 'HASH_ONLY'
            OR assertion_text IS NULL
        )
        AND (
            assertion_text IS NOT NULL
            OR source_defined_descriptor_key IS NOT NULL
            OR text_storage_state = 'HASH_ONLY'
        )
    ),
    CONSTRAINT professional_acquisition_assertion_no_inference_ck CHECK (
        semantic_inference_used IS FALSE
    )
);

CREATE INDEX professional_acquisition_assertion_record_idx
    ON corpus.professional_acquisition_assertion (
        professional_acquisition_record_id, assertion_type
    );

CREATE TABLE audit.round3l_corpus_state_event (
    round3l_corpus_state_event_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_acquisition_record_id BIGINT NOT NULL,
    previous_state TEXT,
    new_state TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL,
    evidence_note TEXT NOT NULL,
    CONSTRAINT round3l_corpus_state_event_pk PRIMARY KEY (
        round3l_corpus_state_event_id
    ),
    CONSTRAINT round3l_corpus_state_event_record_fk FOREIGN KEY (
        professional_acquisition_record_id
    ) REFERENCES corpus.professional_acquisition_record (
        professional_acquisition_record_id
    ),
    CONSTRAINT round3l_corpus_state_event_state_ck CHECK (
        (
            previous_state IS NULL
            OR previous_state IN (
                'DISCOVERED', 'RESEARCH_STAGED', 'REVIEWED', 'MODEL_ELIGIBLE'
            )
        )
        AND new_state IN (
            'DISCOVERED', 'RESEARCH_STAGED', 'REVIEWED', 'MODEL_ELIGIBLE'
        )
    ),
    CONSTRAINT round3l_corpus_state_event_note_ck CHECK (
        evidence_note = btrim(evidence_note)
        AND evidence_note <> ''
    )
);

CREATE OR REPLACE FUNCTION corpus.enforce_round3l_state_transition()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $function$
DECLARE
    old_rank INTEGER;
    new_rank INTEGER;
BEGIN
    old_rank := CASE OLD.corpus_state
        WHEN 'DISCOVERED' THEN 1
        WHEN 'RESEARCH_STAGED' THEN 2
        WHEN 'REVIEWED' THEN 3
        WHEN 'MODEL_ELIGIBLE' THEN 4
    END;
    new_rank := CASE NEW.corpus_state
        WHEN 'DISCOVERED' THEN 1
        WHEN 'RESEARCH_STAGED' THEN 2
        WHEN 'REVIEWED' THEN 3
        WHEN 'MODEL_ELIGIBLE' THEN 4
    END;
    IF new_rank < old_rank THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'professional_acquisition_state_regression_ck',
            MESSAGE = 'Round 3L corpus states are forward-only';
    END IF;
    RETURN NEW;
END
$function$;

CREATE TRIGGER professional_acquisition_state_transition_trg
BEFORE UPDATE OF corpus_state
ON corpus.professional_acquisition_record
FOR EACH ROW
WHEN (OLD.corpus_state IS DISTINCT FROM NEW.corpus_state)
EXECUTE FUNCTION corpus.enforce_round3l_state_transition();

CREATE VIEW corpus.v_round3l_core_candidate AS
SELECT
    record.*,
    record.internal_research_use = 'ALLOWED' AS observed_rights_eligible,
    record.model_research_use = 'ALLOWED'
        AND record.internal_research_use = 'ALLOWED' AS model_rights_eligible
FROM corpus.professional_acquisition_record AS record
WHERE record.evidence_tier IN ('P1', 'P2')
  AND record.payload_kind IN (
      'OFFICIAL_STRUCTURED_SCORE',
      'OFFICIAL_DESCRIPTOR',
      'OFFICIAL_SCORE_AND_DESCRIPTOR'
  )
  AND record.fresh_preparation_status = 'CONFIRMED'
  AND record.effective_record_key IS NOT NULL
  AND record.deduplication_disposition = 'CANONICAL'
  AND record.is_synthetic IS FALSE
  AND record.semantic_inference_used IS FALSE;

CREATE VIEW audit.v_round3l_rights_distribution AS
SELECT
    record.corpus_state,
    record.internal_research_use,
    record.model_research_use,
    count(*)::BIGINT AS record_count
FROM corpus.professional_acquisition_record AS record
GROUP BY
    record.corpus_state,
    record.internal_research_use,
    record.model_research_use;

CREATE VIEW audit.v_round3l_acquisition_metrics AS
WITH census AS (
    SELECT
        count(DISTINCT source_family_key)::BIGINT AS discovered_source_families,
        count(*) FILTER (
            WHERE item_kind IN ('COMPETITION_EDITION', 'PILOT_EDITION')
        )::BIGINT AS discovered_editions
    FROM audit.round3l_source_census
), attempts AS (
    SELECT
        count(DISTINCT round3l_source_census_id)::BIGINT AS attempted_sources,
        count(DISTINCT round3l_source_census_id) FILTER (
            WHERE outcome = 'COMPLETED'
        )::BIGINT AS completed_sources,
        count(*) FILTER (
            WHERE source_snapshot_sha256 IS NOT NULL
        )::BIGINT AS acquired_file_count,
        coalesce(sum(artifact_byte_count), 0)::BIGINT AS acquired_byte_count,
        coalesce(sum(parsed_row_count), 0)::BIGINT AS parsed_row_count
    FROM audit.round3l_source_attempt
), records AS (
    SELECT
        count(*)::BIGINT AS ingested_record_count,
        count(*) FILTER (
            WHERE corpus_state = 'RESEARCH_STAGED'
        )::BIGINT AS research_staged_record_count,
        count(*) FILTER (
            WHERE corpus_state IN ('REVIEWED', 'MODEL_ELIGIBLE')
        )::BIGINT AS reviewed_record_count,
        count(*) FILTER (
            WHERE corpus_state = 'MODEL_ELIGIBLE'
        )::BIGINT AS model_eligible_record_count,
        count(*) FILTER (
            WHERE fresh_preparation_status = 'CONFIRMED'
        )::BIGINT AS preparation_confirmed_record_count,
        count(*) FILTER (
            WHERE c0_source_status = 'REPORTED'
        )::BIGINT AS c0_reported_record_count,
        count(*) FILTER (
            WHERE c1_evidence_status = 'REVIEWED'
        )::BIGINT AS c1_reviewed_record_count,
        count(*) FILTER (
            WHERE deduplication_disposition = 'DUPLICATE_PUBLICATION'
        )::BIGINT AS duplicate_loss_count,
        count(*) FILTER (
            WHERE deduplication_disposition = 'MIRROR'
        )::BIGINT AS mirror_loss_count,
        count(*) FILTER (
            WHERE deduplication_disposition = 'REPEATED_SERVICE'
        )::BIGINT AS repeated_service_loss_count
    FROM corpus.professional_acquisition_record
), core AS (
    SELECT
        count(*) FILTER (
            WHERE observed_rights_eligible
        )::BIGINT AS staged_observed_core_eligible_count,
        count(*) FILTER (
            WHERE model_rights_eligible
        )::BIGINT AS staged_model_rights_eligible_count
    FROM corpus.v_round3l_core_candidate
), assertions AS (
    SELECT count(*) FILTER (
        WHERE assertion_type IN (
            'OFFICIAL_JUDGE_DESCRIPTOR',
            'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR',
            'OFFICIAL_AGGREGATED_DESCRIPTOR'
        )
    )::BIGINT AS professional_descriptor_assertion_count
    FROM corpus.professional_acquisition_assertion
), blockers AS (
    SELECT count(*) FILTER (
        WHERE blocker_state = 'OPEN'
    )::BIGINT AS open_external_blocker_count
    FROM audit.round3l_blocker_queue
)
SELECT
    census.*,
    attempts.*,
    records.*,
    core.*,
    assertions.*,
    blockers.*,
    greatest(7000 - core.staged_observed_core_eligible_count, 0)::BIGINT
        AS remaining_gap_to_7000,
    greatest(10000 - records.model_eligible_record_count, 0)::BIGINT
        AS remaining_gap_to_10000
FROM census
CROSS JOIN attempts
CROSS JOIN records
CROSS JOIN core
CROSS JOIN assertions
CROSS JOIN blockers;

CREATE OR REPLACE FUNCTION audit.run_round3l_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE sql
STABLE
AS $function$
    SELECT
        'round3l.staged_records_have_hashes',
        count(*)::BIGINT,
        count(*) = 0
    FROM corpus.professional_acquisition_record
    WHERE corpus_state IN ('RESEARCH_STAGED', 'REVIEWED', 'MODEL_ELIGIBLE')
      AND (
          source_snapshot_sha256 !~ '^[0-9a-f]{64}$'
          OR raw_record_sha256 !~ '^[0-9a-f]{64}$'
      )
    UNION ALL
    SELECT
        'round3l.no_synthetic_or_inferred_records',
        count(*)::BIGINT,
        count(*) = 0
    FROM corpus.professional_acquisition_record
    WHERE is_synthetic OR semantic_inference_used
    UNION ALL
    SELECT
        'round3l.no_inferred_assertions',
        count(*)::BIGINT,
        count(*) = 0
    FROM corpus.professional_acquisition_assertion
    WHERE semantic_inference_used
    UNION ALL
    SELECT
        'round3l.dedup_losses_do_not_claim_effective_key',
        count(*)::BIGINT,
        count(*) = 0
    FROM corpus.professional_acquisition_record
    WHERE deduplication_disposition <> 'CANONICAL'
      AND effective_record_key IS NOT NULL
    UNION ALL
    SELECT
        'round3l.model_eligible_has_affirmative_rights',
        count(*)::BIGINT,
        count(*) = 0
    FROM corpus.professional_acquisition_record
    WHERE corpus_state = 'MODEL_ELIGIBLE'
      AND (
          internal_research_use <> 'ALLOWED'
          OR model_research_use <> 'ALLOWED'
      )
    UNION ALL
    SELECT
        'round3l.external_blockers_are_queued',
        count(*)::BIGINT,
        count(*) = 0
    FROM audit.round3l_source_attempt AS attempt
    LEFT JOIN audit.round3l_blocker_queue AS blocker
      ON blocker.round3l_source_attempt_id = attempt.round3l_source_attempt_id
    WHERE attempt.outcome = 'BLOCKED_EXTERNAL_ACTION'
      AND blocker.round3l_blocker_queue_id IS NULL
    ORDER BY 1;
$function$;

COMMENT ON TABLE audit.round3l_source_census IS
    'Immutable reconciled Round 2/3K discovery universe for the Round 3L run.';
COMMENT ON TABLE audit.round3l_source_attempt IS
    'Append-only edition/source acquisition attempts; one blocker never blocks another source.';
COMMENT ON TABLE audit.round3l_blocker_queue IS
    'External-action queue for permission, purchase, credentials, contracts, organizer response, or vendor export.';
COMMENT ON TABLE corpus.professional_acquisition_record IS
    'Real normalized professional source rows in DISCOVERED, RESEARCH_STAGED, REVIEWED, or MODEL_ELIGIBLE state.';
COMMENT ON TABLE corpus.professional_acquisition_assertion IS
    'Explicit source assertions with text-or-hash lineage; numeric scores never count as descriptor assertions.';
COMMENT ON VIEW corpus.v_round3l_core_candidate IS
    'Deduplicated P1/P2 fresh-preparation score/descriptor rows; rights flags remain independent.';
COMMENT ON VIEW audit.v_round3l_acquisition_metrics IS
    'Round 3L checkpoint metrics, including staged records, rights-qualified core candidates, losses, and target gaps.';

COMMIT;
