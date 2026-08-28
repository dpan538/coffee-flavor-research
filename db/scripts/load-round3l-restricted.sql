\set ON_ERROR_STOP on

\if :{?round3l_ingest_root}
\else
    \echo 'round3l_ingest_root is required'
    SELECT 1 / 0 AS round3l_ingest_root_required;
\endif

\if :{?round3l_freeze_id}
\else
    \echo 'round3l_freeze_id is required'
    SELECT 1 / 0 AS round3l_freeze_id_required;
\endif

\if :{?round3l_manifest_sha256}
\else
    \echo 'round3l_manifest_sha256 is required'
    SELECT 1 / 0 AS round3l_manifest_sha256_required;
\endif

\set round3l_source_census_path :round3l_ingest_root '/SOURCE_CENSUS.tsv'
\set round3l_source_attempts_path :round3l_ingest_root '/SOURCE_ATTEMPTS.tsv'
\set round3l_records_path :round3l_ingest_root '/PROFESSIONAL_RECORDS.tsv'
\set round3l_assertions_path :round3l_ingest_root '/PROFESSIONAL_ASSERTIONS.tsv'
\set round3l_blockers_path :round3l_ingest_root '/BLOCKER_QUEUE.tsv'

SELECT
    EXISTS (
        SELECT 1
        FROM audit.round3l_restricted_ingest_freeze
        WHERE freeze_id = :'round3l_freeze_id'
    ) AS round3l_freeze_exists,
    EXISTS (
        SELECT 1
        FROM audit.round3l_restricted_ingest_freeze
        WHERE freeze_id = :'round3l_freeze_id'
          AND manifest_sha256 = :'round3l_manifest_sha256'
    ) AS round3l_freeze_matches
\gset

\if :round3l_freeze_exists
    \if :round3l_freeze_matches
        \echo 'ROUND3L_RESTRICTED_INGEST_ALREADY_LOADED=true'
        \quit
    \else
        \echo 'Round 3L freeze ID already exists with a different manifest hash'
        SELECT 1 / 0 AS round3l_freeze_manifest_mismatch;
    \endif
\endif

-- Deterministic restricted Round 3L real-source acquisition loader.
--
-- The canonical TSV ledgers are produced by build-round3l-ingest.py after its
-- cross-lane provenance, key, rights, deduplication, and count checks.  This
-- loader performs only typed loading and stable-key resolution.  In
-- particular, it copies rights and corpus states exactly as frozen; it does
-- not promote any source or record.

BEGIN;

CREATE TEMP TABLE round3l_source_census_stage (
    census_version TEXT,
    census_item_key TEXT,
    item_kind TEXT,
    parent_key TEXT,
    series_key TEXT,
    source_family_key TEXT,
    edition_label TEXT,
    edition_year TEXT,
    country_or_community TEXT,
    category_or_round TEXT,
    official_url TEXT,
    discovery_basis TEXT,
    source_snapshot_sha256 TEXT,
    current_corpus_state TEXT,
    acquisition_state TEXT,
    rights_state TEXT,
    note TEXT,
    discovered_at TEXT
) ON COMMIT DROP;

COPY round3l_source_census_stage FROM :'round3l_source_census_path' WITH (FORMAT csv, HEADER true, DELIMITER E'\t');

CREATE TEMP TABLE round3l_source_attempt_stage (
    attempt_key TEXT,
    census_item_key TEXT,
    lane_key TEXT,
    attempt_sequence TEXT,
    attempted_at TEXT,
    acquisition_method TEXT,
    outcome TEXT,
    canonical_url TEXT,
    final_url TEXT,
    http_status TEXT,
    source_snapshot_sha256 TEXT,
    artifact_byte_count TEXT,
    parsed_row_count TEXT,
    normalized_record_count TEXT,
    descriptor_assertion_count TEXT,
    external_action_type TEXT,
    blocker_detail TEXT,
    next_cursor TEXT,
    evidence_json TEXT
) ON COMMIT DROP;

COPY round3l_source_attempt_stage FROM :'round3l_source_attempts_path' WITH (FORMAT csv, HEADER true, DELIMITER E'\t');

CREATE TEMP TABLE round3l_professional_record_stage (
    professional_acquisition_record_key TEXT,
    attempt_key TEXT,
    source_record_key TEXT,
    source_family_key TEXT,
    series_key TEXT,
    edition_key TEXT,
    edition_year TEXT,
    category_key TEXT,
    round_key TEXT,
    entry_or_lot_key TEXT,
    coffee_identity_key TEXT,
    preparation_service_code TEXT,
    effective_record_key TEXT,
    evidence_tier TEXT,
    payload_kind TEXT,
    official_score_value TEXT,
    official_score_text TEXT,
    official_score_scale TEXT,
    fresh_preparation_status TEXT,
    fresh_preparation_evidence_locator TEXT,
    c0_source_status TEXT,
    c0_family TEXT,
    source_native_roast_value TEXT,
    source_native_roast_scheme TEXT,
    c1_evidence_status TEXT,
    reviewed_c1_mapping TEXT,
    source_snapshot_sha256 TEXT,
    raw_record_sha256 TEXT,
    public_results_use TEXT,
    public_descriptor_use TEXT,
    internal_research_use TEXT,
    public_derived_release TEXT,
    model_research_use TEXT,
    commercial_model_use TEXT,
    deduplication_disposition TEXT,
    canonical_record_key TEXT,
    duplicate_group_key TEXT,
    mirror_group_key TEXT,
    repeat_group_key TEXT,
    corpus_state TEXT,
    label_review_status TEXT,
    is_synthetic TEXT,
    semantic_inference_used TEXT,
    ingested_at TEXT,
    reviewed_at TEXT,
    model_eligible_at TEXT
) ON COMMIT DROP;

COPY round3l_professional_record_stage FROM :'round3l_records_path' WITH (FORMAT csv, HEADER true, DELIMITER E'\t');

CREATE TEMP TABLE round3l_professional_assertion_stage (
    professional_acquisition_assertion_key TEXT,
    professional_acquisition_record_key TEXT,
    assertion_type TEXT,
    source_locator TEXT,
    source_language_code TEXT,
    source_defined_descriptor_key TEXT,
    assertion_text TEXT,
    assertion_text_sha256 TEXT,
    text_storage_state TEXT,
    semantic_inference_used TEXT,
    created_at TEXT
) ON COMMIT DROP;

COPY round3l_professional_assertion_stage FROM :'round3l_assertions_path' WITH (FORMAT csv, HEADER true, DELIMITER E'\t');

CREATE TEMP TABLE round3l_blocker_queue_stage (
    blocker_key TEXT,
    attempt_key TEXT,
    external_action_type TEXT,
    blocker_state TEXT,
    recorded_at TEXT,
    resolution_evidence TEXT,
    continuation_cursor TEXT
) ON COMMIT DROP;

COPY round3l_blocker_queue_stage FROM :'round3l_blockers_path' WITH (FORMAT csv, HEADER true, DELIMITER E'\t');

DO $round3l_stage_contract$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM round3l_source_census_stage) THEN
        RAISE EXCEPTION
            'Round 3L restricted ingest requires a non-empty reconciled source census';
    END IF;

    IF EXISTS (
        SELECT census_item_key
        FROM round3l_source_census_stage
        GROUP BY census_item_key
        HAVING count(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Round 3L staged census keys are not unique';
    END IF;

    IF EXISTS (
        SELECT attempt_key
        FROM round3l_source_attempt_stage
        GROUP BY attempt_key
        HAVING count(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Round 3L staged attempt keys are not unique';
    END IF;

    IF EXISTS (
        SELECT professional_acquisition_record_key
        FROM round3l_professional_record_stage
        GROUP BY professional_acquisition_record_key
        HAVING count(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Round 3L staged record keys are not unique';
    END IF;

    IF EXISTS (
        SELECT professional_acquisition_assertion_key
        FROM round3l_professional_assertion_stage
        GROUP BY professional_acquisition_assertion_key
        HAVING count(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Round 3L staged assertion keys are not unique';
    END IF;

    IF EXISTS (
        SELECT blocker_key
        FROM round3l_blocker_queue_stage
        GROUP BY blocker_key
        HAVING count(*) <> 1
    ) THEN
        RAISE EXCEPTION 'Round 3L staged blocker keys are not unique';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM round3l_professional_record_stage
        WHERE is_synthetic::BOOLEAN
           OR semantic_inference_used::BOOLEAN
    ) OR EXISTS (
        SELECT 1
        FROM round3l_professional_assertion_stage
        WHERE semantic_inference_used::BOOLEAN
    ) THEN
        RAISE EXCEPTION
            'Round 3L restricted ingest rejects synthetic or semantically inferred rows';
    END IF;
END
$round3l_stage_contract$;

INSERT INTO audit.round3l_source_census (
    census_version,
    census_item_key,
    item_kind,
    parent_key,
    series_key,
    source_family_key,
    edition_label,
    edition_year,
    country_or_community,
    category_or_round,
    official_url,
    discovery_basis,
    source_snapshot_sha256,
    current_corpus_state,
    acquisition_state,
    rights_state,
    note,
    discovered_at
)
SELECT
    census_version,
    census_item_key,
    item_kind,
    NULLIF(parent_key, ''),
    series_key,
    source_family_key,
    NULLIF(edition_label, ''),
    -- UNKNOWN is the census's explicit unresolved-year token.  The governed
    -- column is nullable integer; the source token remains visible in the
    -- edition label and note rather than being invented as a year.
    NULLIF(NULLIF(edition_year, ''), 'UNKNOWN')::INTEGER,
    NULLIF(country_or_community, ''),
    NULLIF(category_or_round, ''),
    official_url,
    discovery_basis,
    NULLIF(source_snapshot_sha256, ''),
    current_corpus_state,
    acquisition_state,
    rights_state,
    NULLIF(note, ''),
    discovered_at::TIMESTAMPTZ
FROM round3l_source_census_stage
ORDER BY census_version, census_item_key;

INSERT INTO audit.round3l_source_attempt (
    attempt_key,
    round3l_source_census_id,
    lane_key,
    attempt_sequence,
    attempted_at,
    acquisition_method,
    outcome,
    canonical_url,
    final_url,
    http_status,
    source_snapshot_sha256,
    artifact_byte_count,
    parsed_row_count,
    normalized_record_count,
    descriptor_assertion_count,
    external_action_type,
    blocker_detail,
    next_cursor,
    evidence_json
)
SELECT
    stage.attempt_key,
    census.round3l_source_census_id,
    stage.lane_key,
    stage.attempt_sequence::INTEGER,
    stage.attempted_at::TIMESTAMPTZ,
    stage.acquisition_method,
    stage.outcome,
    stage.canonical_url,
    NULLIF(stage.final_url, ''),
    NULLIF(stage.http_status, '')::SMALLINT,
    NULLIF(stage.source_snapshot_sha256, ''),
    stage.artifact_byte_count::BIGINT,
    stage.parsed_row_count::BIGINT,
    stage.normalized_record_count::BIGINT,
    stage.descriptor_assertion_count::BIGINT,
    NULLIF(stage.external_action_type, ''),
    NULLIF(stage.blocker_detail, ''),
    stage.next_cursor,
    COALESCE(NULLIF(stage.evidence_json, ''), '{}')::JSONB
FROM round3l_source_attempt_stage AS stage
JOIN audit.round3l_source_census AS census
  ON census.census_item_key = stage.census_item_key
ORDER BY stage.lane_key, stage.attempt_sequence::INTEGER, stage.attempt_key;

INSERT INTO corpus.professional_acquisition_record (
    professional_acquisition_record_key,
    round3l_source_attempt_id,
    source_family_key,
    series_key,
    edition_key,
    edition_year,
    category_key,
    round_key,
    source_record_key,
    entry_or_lot_key,
    coffee_identity_key,
    preparation_service_code,
    effective_record_key,
    evidence_tier,
    payload_kind,
    official_score_value,
    official_score_text,
    official_score_scale,
    fresh_preparation_status,
    fresh_preparation_evidence_locator,
    c0_source_status,
    c0_family,
    source_native_roast_value,
    source_native_roast_scheme,
    c1_evidence_status,
    reviewed_c1_mapping,
    source_snapshot_sha256,
    raw_record_sha256,
    public_results_use,
    public_descriptor_use,
    internal_research_use,
    public_derived_release,
    model_research_use,
    commercial_model_use,
    deduplication_disposition,
    canonical_record_key,
    duplicate_group_key,
    mirror_group_key,
    repeat_group_key,
    corpus_state,
    label_review_status,
    is_synthetic,
    semantic_inference_used,
    ingested_at,
    reviewed_at,
    model_eligible_at
)
SELECT
    stage.professional_acquisition_record_key,
    attempt.round3l_source_attempt_id,
    stage.source_family_key,
    stage.series_key,
    stage.edition_key,
    stage.edition_year::INTEGER,
    stage.category_key,
    stage.round_key,
    stage.source_record_key,
    stage.entry_or_lot_key,
    NULLIF(stage.coffee_identity_key, ''),
    NULLIF(stage.preparation_service_code, ''),
    NULLIF(stage.effective_record_key, ''),
    stage.evidence_tier,
    stage.payload_kind,
    NULLIF(stage.official_score_value, '')::NUMERIC,
    NULLIF(stage.official_score_text, ''),
    NULLIF(stage.official_score_scale, ''),
    stage.fresh_preparation_status,
    NULLIF(stage.fresh_preparation_evidence_locator, ''),
    stage.c0_source_status,
    NULLIF(stage.c0_family, ''),
    NULLIF(stage.source_native_roast_value, ''),
    NULLIF(stage.source_native_roast_scheme, ''),
    stage.c1_evidence_status,
    NULLIF(stage.reviewed_c1_mapping, ''),
    stage.source_snapshot_sha256,
    stage.raw_record_sha256,
    stage.public_results_use,
    stage.public_descriptor_use,
    stage.internal_research_use,
    stage.public_derived_release,
    stage.model_research_use,
    stage.commercial_model_use,
    stage.deduplication_disposition,
    NULLIF(stage.canonical_record_key, ''),
    NULLIF(stage.duplicate_group_key, ''),
    NULLIF(stage.mirror_group_key, ''),
    NULLIF(stage.repeat_group_key, ''),
    stage.corpus_state,
    stage.label_review_status,
    stage.is_synthetic::BOOLEAN,
    stage.semantic_inference_used::BOOLEAN,
    stage.ingested_at::TIMESTAMPTZ,
    NULLIF(stage.reviewed_at, '')::TIMESTAMPTZ,
    NULLIF(stage.model_eligible_at, '')::TIMESTAMPTZ
FROM round3l_professional_record_stage AS stage
JOIN audit.round3l_source_attempt AS attempt
  ON attempt.attempt_key = stage.attempt_key
ORDER BY stage.professional_acquisition_record_key;

INSERT INTO corpus.professional_acquisition_assertion (
    professional_acquisition_assertion_key,
    professional_acquisition_record_id,
    assertion_type,
    source_locator,
    source_language_code,
    source_defined_descriptor_key,
    assertion_text,
    assertion_text_sha256,
    text_storage_state,
    semantic_inference_used,
    created_at
)
SELECT
    stage.professional_acquisition_assertion_key,
    record.professional_acquisition_record_id,
    stage.assertion_type,
    stage.source_locator,
    NULLIF(stage.source_language_code, ''),
    NULLIF(stage.source_defined_descriptor_key, ''),
    NULLIF(stage.assertion_text, ''),
    stage.assertion_text_sha256,
    stage.text_storage_state,
    stage.semantic_inference_used::BOOLEAN,
    stage.created_at::TIMESTAMPTZ
FROM round3l_professional_assertion_stage AS stage
JOIN corpus.professional_acquisition_record AS record
  ON record.professional_acquisition_record_key =
     stage.professional_acquisition_record_key
ORDER BY stage.professional_acquisition_assertion_key;

INSERT INTO audit.round3l_blocker_queue (
    blocker_key,
    round3l_source_attempt_id,
    external_action_type,
    blocker_state,
    recorded_at,
    resolution_evidence,
    continuation_cursor
)
SELECT
    stage.blocker_key,
    attempt.round3l_source_attempt_id,
    stage.external_action_type,
    stage.blocker_state,
    stage.recorded_at::TIMESTAMPTZ,
    NULLIF(stage.resolution_evidence, ''),
    stage.continuation_cursor
FROM round3l_blocker_queue_stage AS stage
JOIN audit.round3l_source_attempt AS attempt
  ON attempt.attempt_key = stage.attempt_key
ORDER BY stage.blocker_key;

INSERT INTO audit.round3l_corpus_state_event (
    professional_acquisition_record_id,
    previous_state,
    new_state,
    changed_at,
    evidence_note
)
SELECT
    record.professional_acquisition_record_id,
    NULL,
    record.corpus_state,
    CASE record.corpus_state
        WHEN 'MODEL_ELIGIBLE' THEN record.model_eligible_at
        WHEN 'REVIEWED' THEN record.reviewed_at
        ELSE record.ingested_at
    END,
    'Initial state copied exactly from the canonical Round 3L acquisition ledger; no rights or state promotion applied.'
FROM corpus.professional_acquisition_record AS record
ORDER BY record.professional_acquisition_record_key;

DO $round3l_restricted_ingest_contract$
DECLARE
    census_count BIGINT;
    attempt_count BIGINT;
    record_count BIGINT;
    assertion_count BIGINT;
    blocker_count BIGINT;
    descriptor_count BIGINT;
    metric audit.v_round3l_acquisition_metrics%ROWTYPE;
BEGIN
    SELECT count(*) INTO STRICT census_count
    FROM round3l_source_census_stage;
    SELECT count(*) INTO STRICT attempt_count
    FROM round3l_source_attempt_stage;
    SELECT count(*) INTO STRICT record_count
    FROM round3l_professional_record_stage;
    SELECT count(*) INTO STRICT assertion_count
    FROM round3l_professional_assertion_stage;
    SELECT count(*) INTO STRICT blocker_count
    FROM round3l_blocker_queue_stage;
    SELECT count(*) INTO STRICT descriptor_count
    FROM round3l_professional_assertion_stage
    WHERE assertion_type IN (
        'OFFICIAL_JUDGE_DESCRIPTOR',
        'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR',
        'OFFICIAL_AGGREGATED_DESCRIPTOR'
    );

    IF census_count <> (SELECT count(*) FROM audit.round3l_source_census)
       OR attempt_count <> (SELECT count(*) FROM audit.round3l_source_attempt)
       OR record_count <>
          (SELECT count(*) FROM corpus.professional_acquisition_record)
       OR assertion_count <>
          (SELECT count(*) FROM corpus.professional_acquisition_assertion)
       OR blocker_count <> (SELECT count(*) FROM audit.round3l_blocker_queue)
       OR record_count <> (SELECT count(*) FROM audit.round3l_corpus_state_event)
    THEN
        RAISE EXCEPTION
            'Round 3L restricted-ingest row-count reconciliation failed: census %, attempts %, records %, assertions %, blockers %',
            census_count, attempt_count, record_count, assertion_count,
            blocker_count;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.round3l_source_census AS census
        JOIN round3l_source_census_stage AS stage
          ON stage.census_version = census.census_version
         AND stage.census_item_key = census.census_item_key
        WHERE census.current_corpus_state IS DISTINCT FROM
              stage.current_corpus_state
           OR census.acquisition_state IS DISTINCT FROM
              stage.acquisition_state
           OR census.rights_state IS DISTINCT FROM stage.rights_state
    ) THEN
        RAISE EXCEPTION
            'Round 3L restricted ingest changed a frozen census state or rights value';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_acquisition_record AS record
        JOIN round3l_professional_record_stage AS stage
          ON stage.professional_acquisition_record_key =
             record.professional_acquisition_record_key
        WHERE record.corpus_state IS DISTINCT FROM stage.corpus_state
           OR record.public_results_use IS DISTINCT FROM
              stage.public_results_use
           OR record.public_descriptor_use IS DISTINCT FROM
              stage.public_descriptor_use
           OR record.internal_research_use IS DISTINCT FROM
              stage.internal_research_use
           OR record.public_derived_release IS DISTINCT FROM
              stage.public_derived_release
           OR record.model_research_use IS DISTINCT FROM
              stage.model_research_use
           OR record.commercial_model_use IS DISTINCT FROM
              stage.commercial_model_use
    ) THEN
        RAISE EXCEPTION
            'Round 3L restricted ingest changed a frozen rights or corpus-state value';
    END IF;

    IF record_count <> (
        SELECT coalesce(sum(normalized_record_count), 0)
        FROM audit.round3l_source_attempt
    ) THEN
        RAISE EXCEPTION
            'Round 3L attempt normalized-record counts do not reconcile';
    END IF;

    IF descriptor_count <> (
        SELECT coalesce(sum(descriptor_assertion_count), 0)
        FROM audit.round3l_source_attempt
    ) THEN
        RAISE EXCEPTION
            'Round 3L attempt descriptor-assertion counts do not reconcile';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM round3l_professional_record_stage AS stage
        WHERE NULLIF(stage.canonical_record_key, '') IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM corpus.professional_acquisition_record AS canonical
              WHERE canonical.professional_acquisition_record_key =
                    stage.canonical_record_key
                AND canonical.deduplication_disposition = 'CANONICAL'
          )
    ) THEN
        RAISE EXCEPTION
            'Round 3L restricted ingest contains an unresolved canonical-record target';
    END IF;

    SELECT * INTO STRICT metric
    FROM audit.v_round3l_acquisition_metrics;

    IF metric.discovered_source_families < 1
       OR metric.ingested_record_count <> record_count
       OR metric.professional_descriptor_assertion_count <>
          descriptor_count
       OR metric.open_external_blocker_count <> (
          SELECT count(*)
          FROM audit.round3l_blocker_queue
          WHERE blocker_state = 'OPEN'
       )
       OR metric.remaining_gap_to_7000 < 0
       OR metric.remaining_gap_to_10000 < 0
    THEN
        RAISE EXCEPTION
            'Round 3L acquisition metrics do not reconcile: %',
            row_to_json(metric);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM audit.run_round3l_validation_queries()
    ) OR EXISTS (
        SELECT 1
        FROM audit.run_round3l_validation_queries()
        WHERE passed IS NOT TRUE OR violation_count <> 0
    ) THEN
        RAISE EXCEPTION
            'Round 3L post-ingest validation contract failed';
    END IF;
END
$round3l_restricted_ingest_contract$;

INSERT INTO audit.round3l_restricted_ingest_freeze (
    freeze_id,
    manifest_sha256,
    census_row_count,
    attempt_row_count,
    professional_record_row_count,
    professional_assertion_row_count,
    blocker_row_count
)
SELECT
    :'round3l_freeze_id',
    :'round3l_manifest_sha256',
    (SELECT count(*) FROM round3l_source_census_stage),
    (SELECT count(*) FROM round3l_source_attempt_stage),
    (SELECT count(*) FROM round3l_professional_record_stage),
    (SELECT count(*) FROM round3l_professional_assertion_stage),
    (SELECT count(*) FROM round3l_blocker_queue_stage);

COMMIT;

\echo 'ROUND3L_RESTRICTED_INGEST_PASS=true'
