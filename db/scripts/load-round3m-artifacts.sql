\set ON_ERROR_STOP on

-- Idempotent public-safe Round 3M artifact import.  The Python contract
-- validator runs before this file.  This transaction repeats the essential
-- row counts and lineage checks so direct SQL use also fails closed.

BEGIN;

CREATE TEMP TABLE stage_round3m_census (
    census_item_key TEXT, item_kind TEXT, source_family_id TEXT,
    source_route_id TEXT, organizer_id TEXT, edition_id TEXT,
    schema_signature_id TEXT, publication_host TEXT,
    independent_source_family_id TEXT, independence_state TEXT,
    rights_lineage_id TEXT, mirror_lineage_id TEXT,
    route_disposition TEXT, artifact_count TEXT,
    publication_row_count TEXT, effective_record_candidate_count TEXT,
    gate_descriptor_candidate_count TEXT, reviewed_strict_count TEXT,
    reviewed_broad_count TEXT, p1_count TEXT, p2_count TEXT,
    p3_count TEXT, unresolved_count TEXT,
    rights_affirmative_model_count TEXT, analyst_minutes TEXT,
    descriptor_yield_per_artifact TEXT,
    descriptor_yield_per_analyst_hour TEXT, corpus_universe TEXT,
    official_url TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_route (
    source_route_id TEXT, source_family_id TEXT, organizer_id TEXT,
    independent_source_family_id TEXT, route_disposition TEXT,
    census_item_count TEXT, artifact_count TEXT,
    publication_row_count TEXT, effective_record_candidate_count TEXT,
    gate_descriptor_candidate_count TEXT, disposition_basis TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_schema (
    schema_signature_id TEXT, source_route_id TEXT, schema_version TEXT,
    host TEXT, route_pattern TEXT, edition_or_period TEXT,
    field_labels_json TEXT, selectors_json TEXT,
    publication_layer_rules_json TEXT,
    field_origin_assumptions_json TEXT, known_ambiguity TEXT,
    positive_fixture_locator TEXT, negative_fixture_locator TEXT,
    adapter_version TEXT, live_positive_fixture_present TEXT,
    validation_status TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_source_artifact (
    source_artifact_id TEXT, source_route_id TEXT,
    schema_signature_id TEXT, governed_locator TEXT,
    source_retrieved_at TEXT, source_file_sha256 TEXT,
    file_size_bytes TEXT, storage_state TEXT, non_storage_reason TEXT,
    parser_version TEXT, adapter_version TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_effective_record (
    round3m_effective_record_id TEXT, effective_record_key TEXT,
    series_id TEXT, edition_id TEXT, edition_year TEXT, category_id TEXT,
    round_id TEXT, subject_kind TEXT, entry_or_lot_id TEXT,
    preparation_service_code TEXT, preparation_evidence_locator TEXT,
    source_route_id TEXT, source_artifact_id TEXT,
    source_record_locator TEXT, source_file_sha256 TEXT,
    record_identity_sha256 TEXT, identity_resolution_state TEXT,
    synthetic_generated TEXT, preparation_inferred_from_descriptor TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_queue (
    review_queue_id TEXT, descriptor_assertion_id TEXT,
    professional_record_id TEXT, source_family_id TEXT,
    source_route_id TEXT, edition_id TEXT, edition_year TEXT,
    source_artifact_id TEXT, source_file_sha256 TEXT,
    route_index_sha256 TEXT, source_file_sha256_scope TEXT,
    source_file_nonstorage_reason TEXT, raw_record_sha256 TEXT,
    source_locator TEXT, source_language TEXT, source_text_sha256 TEXT,
    source_text_storage_state TEXT, source_text_non_storage_reason TEXT,
    source_field_contract TEXT, publication_layer TEXT,
    descriptor_class TEXT, evidence_tier TEXT, review_state TEXT,
    review_actor_type TEXT, current_disposition TEXT,
    disposition_reason_code TEXT, human_review_required TEXT,
    model_eligible TEXT, decision_effective_date TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_decision (
    decision_id TEXT, review_queue_id TEXT, descriptor_assertion_id TEXT,
    current_disposition TEXT, descriptor_class TEXT, review_state TEXT,
    review_actor_type TEXT, review_protocol_version TEXT,
    decision_reason_code TEXT, decision_basis TEXT, evidence_locator TEXT,
    source_file_sha256 TEXT, route_index_sha256 TEXT,
    source_file_sha256_scope TEXT, source_file_nonstorage_reason TEXT,
    source_text_sha256 TEXT, human_confirmed TEXT,
    expert_adjudicated TEXT, counts_as_reviewed_descriptor TEXT,
    model_eligible TEXT, decision_effective_date TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_rights (
    rights_decision_id TEXT, descriptor_assertion_id TEXT,
    source_artifact_id TEXT, purpose TEXT, rights_state TEXT,
    decision_basis TEXT, rights_evidence_locator TEXT,
    review_actor_type TEXT, model_eligibility_effect TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_ledger (
    descriptor_assertion_id TEXT, effective_record_id TEXT,
    source_artifact_id TEXT, source_route_id TEXT,
    schema_signature_id TEXT, publication_layer TEXT,
    source_field_label TEXT, source_field_label_sha256 TEXT,
    source_selector_or_locator TEXT, source_page_or_record_locator TEXT,
    raw_field_text TEXT, raw_field_text_sha256 TEXT,
    atomic_source_text TEXT, atomic_source_text_sha256 TEXT,
    source_language TEXT, descriptor_class TEXT,
    source_native_lexical_form TEXT,
    source_native_lexical_form_sha256 TEXT,
    normalized_candidate_form TEXT,
    normalized_candidate_form_sha256 TEXT, evidence_tier TEXT,
    evidence_origin_type TEXT, origin_decision_basis TEXT,
    origin_evidence_locator TEXT, review_state TEXT,
    review_actor_type TEXT, review_receipt_id TEXT,
    rights_decision_id TEXT, within_record_repeat_group TEXT,
    cross_observation_repeat_group TEXT, mirror_group TEXT,
    created_at TEXT, source_retrieved_at TEXT,
    source_file_sha256 TEXT, route_index_sha256 TEXT,
    source_file_sha256_scope TEXT, source_file_nonstorage_reason TEXT,
    parser_version TEXT, adapter_version TEXT,
    source_text_storage_state TEXT, source_text_non_storage_reason TEXT,
    counts_as_reviewed_descriptor TEXT, model_eligible TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_duplicate (
    duplicate_decision_id TEXT, descriptor_assertion_id TEXT,
    professional_record_id TEXT, deduplication_disposition TEXT,
    within_record_repeat_group TEXT, cross_observation_repeat_group TEXT,
    mirror_group TEXT, decision_basis TEXT, counts_as_assertion TEXT,
    counts_as_record_unique_descriptor TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_pair (
    coassertion_event_id TEXT, effective_record_id TEXT,
    left_descriptor_assertion_id TEXT,
    right_descriptor_assertion_id TEXT, left_normalized_form TEXT,
    right_normalized_form TEXT, left_normalized_form_sha256 TEXT,
    right_normalized_form_sha256 TEXT,
    left_atomic_source_text_sha256 TEXT,
    right_atomic_source_text_sha256 TEXT, evidence_tier TEXT,
    publication_layer TEXT, pair_support_event_count TEXT,
    source_file_sha256 TEXT, route_index_sha256 TEXT,
    source_file_sha256_scope TEXT, source_file_nonstorage_reason TEXT
) ON COMMIT DROP;

CREATE TEMP TABLE stage_round3m_analyst_time (
    analyst_time_log_key TEXT, task_type TEXT, source_route_id TEXT,
    artifact_count TEXT, candidate_count TEXT, reviewed_count TEXT,
    started_at TEXT, ended_at TEXT, active_minutes TEXT,
    automated_runtime_seconds TEXT, review_actor_type TEXT, notes TEXT
) ON COMMIT DROP;

\copy stage_round3m_census FROM '__ROUND3M_CENSUS_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_route FROM '__ROUND3M_ROUTE_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_schema FROM '__ROUND3M_SCHEMA_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_source_artifact FROM '__ROUND3M_SOURCE_ARTIFACT_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_effective_record FROM '__ROUND3M_EFFECTIVE_RECORD_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_queue FROM '__ROUND3M_QUEUE_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_decision FROM '__ROUND3M_DECISION_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_rights FROM '__ROUND3M_RIGHTS_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_ledger FROM '__ROUND3M_LEDGER_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_duplicate FROM '__ROUND3M_DUPLICATE_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_pair FROM '__ROUND3M_PAIR_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')
\copy stage_round3m_analyst_time FROM '__ROUND3M_ANALYST_TIME_FILE__' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', NULL '\N', QUOTE E'\b')

DO $round3m_stage_contract$
BEGIN
    IF (SELECT count(*) FROM stage_round3m_census) <> 480
       OR (SELECT count(DISTINCT census_item_key)
           FROM stage_round3m_census) <> 480 THEN
        RAISE EXCEPTION 'Round 3M census staging must contain 480 unique items';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_route) <> 131
       OR (SELECT count(DISTINCT source_route_id)
           FROM stage_round3m_route) <> 131 THEN
        RAISE EXCEPTION 'Round 3M route staging must contain 131 unique routes';
    END IF;
    IF (SELECT count(DISTINCT independent_source_family_id)
        FROM stage_round3m_route) <> 11 THEN
        RAISE EXCEPTION 'Round 3M routes must collapse to 11 independent source families';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_schema) <> 4
       OR (SELECT count(DISTINCT schema_signature_id)
           FROM stage_round3m_schema) <> 4 THEN
        RAISE EXCEPTION 'Round 3M schema staging must contain four unique signatures';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_source_artifact) <> 8
       OR (SELECT count(DISTINCT source_artifact_id)
           FROM stage_round3m_source_artifact) <> 8 THEN
        RAISE EXCEPTION 'Round 3M live artifact staging must contain eight unique rows';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_effective_record) <> 8
       OR (SELECT count(DISTINCT round3m_effective_record_id)
           FROM stage_round3m_effective_record) <> 8 THEN
        RAISE EXCEPTION 'Round 3M effective-record bridge staging must contain eight unique rows';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_queue) <> 516
       OR (SELECT count(DISTINCT descriptor_assertion_id)
           FROM stage_round3m_queue) <> 516 THEN
        RAISE EXCEPTION 'Round 3M queue staging must contain 516 unique candidates';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_decision) <> 516
       OR (SELECT count(DISTINCT descriptor_assertion_id)
           FROM stage_round3m_decision) <> 516 THEN
        RAISE EXCEPTION 'Round 3M decision staging must contain 516 unique candidates';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_rights) <> 3096
       OR (SELECT count(DISTINCT rights_decision_id)
           FROM stage_round3m_rights) <> 3096 THEN
        RAISE EXCEPTION 'Round 3M rights staging must contain 3,096 unique decisions';
    END IF;
    IF EXISTS (
        SELECT descriptor_assertion_id
        FROM stage_round3m_rights
        GROUP BY descriptor_assertion_id
        HAVING count(*) <> 6 OR count(DISTINCT purpose) <> 6
    ) THEN
        RAISE EXCEPTION 'each Round 3M candidate requires six distinct purpose-specific rights decisions';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_ledger) <> 140
       OR (SELECT count(DISTINCT descriptor_assertion_id)
           FROM stage_round3m_ledger) <> 140 THEN
        RAISE EXCEPTION 'Round 3M admitted pilot staging must contain 140 unique assertions';
    END IF;
    IF EXISTS (
        SELECT 1 FROM stage_round3m_ledger
        WHERE coalesce(raw_field_text, '') <> ''
           OR coalesce(atomic_source_text, '') <> ''
           OR coalesce(source_native_lexical_form, '') <> ''
           OR coalesce(normalized_candidate_form, '') <> ''
           OR source_text_storage_state <> 'HASH_ONLY'
           OR counts_as_reviewed_descriptor <> 'false'
           OR model_eligible <> 'false'
    ) THEN
        RAISE EXCEPTION 'Round 3M public pilot assertions must remain hash-only, provisional, and non-model-eligible';
    END IF;
    IF (SELECT count(*) FROM stage_round3m_pair) <> 508
       OR (SELECT count(DISTINCT coassertion_event_id)
           FROM stage_round3m_pair) <> 508 THEN
        RAISE EXCEPTION 'Round 3M pair staging must contain 508 unique events';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM stage_round3m_analyst_time)
       OR EXISTS (
           SELECT 1 FROM stage_round3m_analyst_time
           WHERE reviewed_count <> '0'
              OR review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
       ) THEN
        RAISE EXCEPTION 'Round 3M analyst time must be present without fabricated human review';
    END IF;
END
$round3m_stage_contract$;

CREATE TEMP VIEW expected_round3m_family AS
SELECT
    route.independent_source_family_id,
    min(route.organizer_id) AS organizer_id,
    route.independent_source_family_id AS family_name,
    'ROUND3M_CONSERVATIVE_PUBLICATION_ORIGIN_GROUP_FROM_RECONCILED_CENSUS'::TEXT
        AS independence_basis,
    lower(min(census.rights_lineage_id)) AS rights_lineage_id,
    FALSE AS admitted_for_descriptor_research
FROM stage_round3m_route AS route
JOIN stage_round3m_census AS census
  ON census.source_route_id = route.source_route_id
GROUP BY route.independent_source_family_id;

INSERT INTO evidence.round3m_independent_source_family (
    independent_source_family_id, organizer_id, family_name,
    independence_basis, rights_lineage_id,
    admitted_for_descriptor_research
)
SELECT * FROM expected_round3m_family
ON CONFLICT (independent_source_family_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_route AS
WITH reconciled AS (
    SELECT
        route.source_route_id,
        route.independent_source_family_id,
        route.organizer_id,
        min(census.publication_host) AS publication_host,
        min(census.official_url) AS canonical_url,
        min(census.official_url) AS route_pattern,
        route.route_disposition,
        lower(min(census.rights_lineage_id)) AS rights_lineage_id,
        lower(min(census.mirror_lineage_id)) AS mirror_lineage_id,
        TIMESTAMPTZ '2026-08-28 04:00:00+00' AS discovered_at
    FROM stage_round3m_route AS route
    JOIN stage_round3m_census AS census
      ON census.source_route_id = route.source_route_id
    GROUP BY route.source_route_id,
             route.independent_source_family_id,
             route.organizer_id, route.route_disposition
), signature_route AS (
    SELECT
        signature.source_route_id,
        CASE WHEN signature.schema_signature_id LIKE 'schema.coe.%'
             THEN 'family.ace_cup_of_excellence'
             ELSE 'family.world_coffee_events' END
            AS independent_source_family_id,
        CASE WHEN signature.schema_signature_id LIKE 'schema.coe.%'
             THEN 'organizer.ace'
             ELSE 'organizer.world_coffee_events' END AS organizer_id,
        signature.host AS publication_host,
        coalesce(
            min(record.source_record_locator),
            min(census.official_url),
            signature.positive_fixture_locator
        ) AS canonical_url,
        signature.route_pattern,
        CASE
            WHEN signature.schema_signature_id =
                 'schema.coe.honduras-2017.explicit-top-jury.v1'
            THEN 'PRIORITY_DESCRIPTOR_ROUTE'
            ELSE 'PROVENANCE_PILOT_ONLY'
        END AS route_disposition,
        CASE WHEN signature.schema_signature_id LIKE 'schema.coe.%'
             THEN 'rights.ace_cup_of_excellence'
             ELSE 'rights.world_coffee_events' END AS rights_lineage_id,
        'unresolved'::TEXT AS mirror_lineage_id,
        TIMESTAMPTZ '2026-08-28 04:30:00+00' AS discovered_at
    FROM stage_round3m_schema AS signature
    LEFT JOIN stage_round3m_effective_record AS record
      ON record.source_route_id = signature.source_route_id
    LEFT JOIN stage_round3m_census AS census
      ON census.independent_source_family_id =
         CASE WHEN signature.schema_signature_id LIKE 'schema.coe.%'
              THEN 'family.ace_cup_of_excellence'
              ELSE 'family.world_coffee_events' END
    GROUP BY signature.source_route_id, signature.schema_signature_id,
             signature.host, signature.positive_fixture_locator,
             signature.route_pattern
)
SELECT * FROM reconciled
UNION ALL
SELECT * FROM signature_route
WHERE NOT EXISTS (
    SELECT 1 FROM reconciled
    WHERE reconciled.source_route_id = signature_route.source_route_id
);

INSERT INTO evidence.round3m_source_route (
    source_route_id, independent_source_family_id,
    round3l_source_census_id, organizer_id, publication_host,
    canonical_url, route_pattern, route_disposition, rights_lineage_id,
    mirror_lineage_id, discovered_at
)
SELECT
    source_route_id, independent_source_family_id, NULL::BIGINT,
    organizer_id, publication_host, canonical_url, route_pattern,
    route_disposition, rights_lineage_id, mirror_lineage_id, discovered_at
FROM expected_round3m_route
ON CONFLICT (source_route_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_schema AS
SELECT
    schema_signature_id, source_route_id, schema_version::INTEGER,
    host, route_pattern, edition_or_period, field_labels_json::JSONB,
    selectors_json::JSONB, publication_layer_rules_json::JSONB,
    field_origin_assumptions_json::JSONB, known_ambiguity,
    positive_fixture_locator, negative_fixture_locator,
    adapter_version, live_positive_fixture_present::BOOLEAN,
    validation_status
FROM stage_round3m_schema;

INSERT INTO evidence.round3m_source_schema_signature (
    schema_signature_id, source_route_id, schema_version, host,
    route_pattern, edition_or_period, field_labels_json, selectors_json,
    publication_layer_rules_json, field_origin_assumptions_json,
    known_ambiguity, positive_fixture_locator, negative_fixture_locator,
    adapter_version, live_positive_fixture_present, validation_status
)
SELECT * FROM expected_round3m_schema
ON CONFLICT (schema_signature_id) DO NOTHING;

CREATE TEMP VIEW stage_round3m_artifact_lineage AS
SELECT
    source_artifact_id,
    min(route_index_sha256) AS route_index_sha256,
    min(source_file_sha256_scope) AS source_file_sha256_scope,
    min(source_file_nonstorage_reason) AS source_file_nonstorage_reason
FROM stage_round3m_ledger
GROUP BY source_artifact_id;

DO $round3m_artifact_lineage$
BEGIN
    IF (SELECT count(*) FROM stage_round3m_artifact_lineage) <> 8
       OR EXISTS (
          SELECT source_artifact_id
          FROM stage_round3m_ledger
          GROUP BY source_artifact_id
          HAVING count(DISTINCT route_index_sha256) <> 1
             OR count(DISTINCT source_file_sha256_scope) <> 1
             OR count(DISTINCT source_file_nonstorage_reason) <> 1
       ) THEN
        RAISE EXCEPTION 'live artifact lineage is not singular per source artifact';
    END IF;
END
$round3m_artifact_lineage$;

CREATE TEMP VIEW expected_round3m_source_artifact AS
SELECT
    artifact.source_artifact_id, artifact.source_route_id,
    artifact.schema_signature_id, artifact.governed_locator,
    artifact.source_retrieved_at::TIMESTAMPTZ,
    artifact.source_file_sha256, lineage.route_index_sha256,
    lineage.source_file_sha256_scope,
    lineage.source_file_nonstorage_reason,
    artifact.file_size_bytes::BIGINT, artifact.storage_state,
    artifact.non_storage_reason, artifact.parser_version,
    artifact.adapter_version
FROM stage_round3m_source_artifact AS artifact
JOIN stage_round3m_artifact_lineage AS lineage
  USING (source_artifact_id);

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    round3l_source_attempt_id, professional_source_file_id,
    governed_locator, source_retrieved_at, source_file_sha256,
    route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, file_size_bytes, storage_state,
    non_storage_reason, parser_version, adapter_version
)
SELECT
    source_artifact_id, source_route_id, schema_signature_id,
    NULL::BIGINT, NULL::BIGINT, governed_locator, source_retrieved_at,
    source_file_sha256, route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, file_size_bytes, storage_state,
    non_storage_reason, parser_version, adapter_version
FROM expected_round3m_source_artifact
ON CONFLICT (source_artifact_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_effective_record AS
SELECT
    record.round3m_effective_record_id, record.effective_record_key,
    record.series_id, record.edition_id, record.edition_year::INTEGER,
    record.category_id, record.round_id, record.subject_kind,
    record.entry_or_lot_id, record.preparation_service_code,
    record.preparation_evidence_locator, record.source_route_id,
    record.source_artifact_id, record.source_record_locator,
    record.source_file_sha256, lineage.route_index_sha256,
    lineage.source_file_sha256_scope,
    lineage.source_file_nonstorage_reason,
    record.record_identity_sha256, record.identity_resolution_state,
    record.synthetic_generated::BOOLEAN,
    record.preparation_inferred_from_descriptor::BOOLEAN
FROM stage_round3m_effective_record AS record
JOIN stage_round3m_artifact_lineage AS lineage
  USING (source_artifact_id);

INSERT INTO competition.round3m_effective_record_bridge (
    round3m_effective_record_id, effective_record_key, series_id,
    edition_id, edition_year, category_id, round_id, subject_kind,
    entry_or_lot_id, preparation_service_code,
    preparation_evidence_locator, source_route_id, source_artifact_id,
    source_record_locator, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    record_identity_sha256, preparation_service_id,
    professional_acquisition_record_id, identity_resolution_state,
    synthetic_generated, preparation_inferred_from_descriptor
)
SELECT
    round3m_effective_record_id, effective_record_key, series_id,
    edition_id, edition_year, category_id, round_id, subject_kind,
    entry_or_lot_id, preparation_service_code,
    preparation_evidence_locator, source_route_id, source_artifact_id,
    source_record_locator, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    record_identity_sha256, NULL::BIGINT, NULL::BIGINT,
    identity_resolution_state, synthetic_generated,
    preparation_inferred_from_descriptor
FROM expected_round3m_effective_record
ON CONFLICT (round3m_effective_record_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_queue AS
SELECT
    queue.review_queue_id, queue.descriptor_assertion_id,
    queue.professional_record_id, queue.source_family_id,
    queue.source_route_id, NULLIF(queue.edition_id, '') AS edition_id,
    NULLIF(queue.edition_year, '')::INTEGER AS edition_year,
    queue.source_artifact_id,
    coalesce(NULLIF(queue.source_file_sha256, ''),
             artifact.source_file_sha256, '') AS source_file_sha256,
    queue.route_index_sha256, queue.source_file_sha256_scope,
    queue.source_file_nonstorage_reason, queue.raw_record_sha256,
    queue.source_locator, queue.source_language,
    queue.source_text_sha256, queue.source_text_storage_state,
    queue.source_text_non_storage_reason, queue.source_field_contract,
    queue.publication_layer, queue.descriptor_class,
    queue.evidence_tier, queue.review_state, queue.review_actor_type,
    queue.current_disposition, queue.disposition_reason_code,
    queue.human_review_required::BOOLEAN, queue.model_eligible::BOOLEAN,
    queue.decision_effective_date::DATE
FROM stage_round3m_queue AS queue
LEFT JOIN expected_round3m_source_artifact AS artifact
  USING (source_artifact_id);

INSERT INTO audit.round3m_descriptor_review_queue_item (
    review_queue_id, descriptor_assertion_id, professional_record_id,
    source_family_id, source_route_id, edition_id, edition_year,
    source_artifact_id, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    raw_record_sha256, source_locator, source_language,
    source_text_sha256, source_text_storage_state,
    source_text_non_storage_reason, source_field_contract,
    publication_layer, descriptor_class, evidence_tier, review_state,
    review_actor_type, current_disposition, disposition_reason_code,
    human_review_required, model_eligible, decision_effective_date
)
SELECT * FROM expected_round3m_queue
ON CONFLICT (review_queue_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_decision AS
SELECT
    decision.decision_id, decision.review_queue_id,
    decision.descriptor_assertion_id, decision.current_disposition,
    decision.descriptor_class, decision.review_state,
    decision.review_actor_type, decision.review_protocol_version,
    decision.decision_reason_code, decision.decision_basis,
    decision.evidence_locator,
    coalesce(NULLIF(decision.source_file_sha256, ''),
             artifact.source_file_sha256, '') AS source_file_sha256,
    decision.route_index_sha256, decision.source_file_sha256_scope,
    decision.source_file_nonstorage_reason, decision.source_text_sha256,
    decision.human_confirmed::BOOLEAN,
    decision.expert_adjudicated::BOOLEAN,
    decision.counts_as_reviewed_descriptor::BOOLEAN,
    decision.model_eligible::BOOLEAN,
    decision.decision_effective_date::DATE
FROM stage_round3m_decision AS decision
JOIN stage_round3m_queue AS queue
  USING (review_queue_id, descriptor_assertion_id)
LEFT JOIN expected_round3m_source_artifact AS artifact
  ON artifact.source_artifact_id = queue.source_artifact_id;

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
)
SELECT * FROM expected_round3m_decision
ON CONFLICT (decision_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_candidate_rights AS
SELECT
    rights_decision_id, descriptor_assertion_id, source_artifact_id,
    purpose, rights_state, decision_basis, rights_evidence_locator,
    review_actor_type, model_eligibility_effect
FROM stage_round3m_rights;

INSERT INTO evidence.round3m_candidate_rights_decision (
    rights_decision_id, descriptor_assertion_id, source_artifact_id,
    purpose, rights_state, decision_basis, rights_evidence_locator,
    review_actor_type, model_eligibility_effect
)
SELECT * FROM expected_round3m_candidate_rights
ON CONFLICT (rights_decision_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_rights_bundle AS
SELECT
    ledger.rights_decision_id,
    ledger.rights_decision_id AS rights_scope_id,
    1::INTEGER AS decision_version,
    NULL::TEXT AS supersedes_rights_decision_id,
    ledger.source_route_id, ledger.publication_layer,
    ledger.source_field_label,
    max(rights.rights_state) FILTER (
        WHERE rights.purpose = 'PUBLIC_DISCOVERY'
    ) AS public_discovery,
    max(rights.rights_state) FILTER (
        WHERE rights.purpose = 'INTERNAL_RESEARCH_ANALYSIS'
    ) AS internal_research_analysis,
    max(rights.rights_state) FILTER (
        WHERE rights.purpose = 'DERIVED_RESEARCH_DATA'
    ) AS derived_research_data,
    max(rights.rights_state) FILTER (
        WHERE rights.purpose = 'MODEL_RESEARCH'
    ) AS model_research,
    max(rights.rights_state) FILTER (
        WHERE rights.purpose = 'DEPLOYMENT_OR_COMMERCIAL_MODEL'
    ) AS deployment_or_commercial_model,
    max(rights.rights_state) FILTER (
        WHERE rights.purpose = 'RAW_REDISTRIBUTION'
    ) AS raw_redistribution,
    'UNKNOWN'::TEXT AS decision_authority_code,
    'CODEX_SOURCE_AUDITOR'::TEXT AS decision_actor_type,
    'SIX_PURPOSE_PUBLIC_SAFE_PILOT_RIGHTS_PIVOT;NO_AFFIRMATIVE_PERMISSION_INFERRED'::TEXT
        AS decision_basis,
    min(rights.rights_evidence_locator) AS evidence_locator,
    ledger.created_at::TIMESTAMPTZ AS decided_at
FROM stage_round3m_ledger AS ledger
JOIN stage_round3m_rights AS rights
  ON rights.descriptor_assertion_id = ledger.descriptor_assertion_id
GROUP BY ledger.descriptor_assertion_id, ledger.rights_decision_id,
         ledger.source_route_id, ledger.publication_layer,
         ledger.source_field_label, ledger.created_at;

INSERT INTO evidence.round3m_descriptor_rights_decision (
    rights_decision_id, rights_scope_id, decision_version,
    supersedes_rights_decision_id, source_route_id, publication_layer,
    source_field_label, public_discovery, internal_research_analysis,
    derived_research_data, model_research,
    deployment_or_commercial_model, raw_redistribution,
    decision_authority_code, decision_actor_type, decision_basis,
    evidence_locator, decided_at
)
SELECT * FROM expected_round3m_rights_bundle
ON CONFLICT (rights_decision_id) DO NOTHING;

CREATE TEMP VIEW expected_round3m_assertion AS
SELECT
    ledger.descriptor_assertion_id AS descriptor_assertion_key,
    ledger.effective_record_id AS round3m_effective_record_id,
    bridge.effective_record_key, bridge.edition_year,
    ledger.source_artifact_id, ledger.source_route_id,
    ledger.schema_signature_id, ledger.publication_layer,
    ledger.source_field_label, ledger.source_field_label_sha256,
    ledger.source_selector_or_locator,
    ledger.source_page_or_record_locator,
    'observation:' || substr(
        audit.round3i_utf8_sha256(
            ledger.effective_record_id || E'\x1f' ||
            ledger.source_artifact_id || E'\x1f' ||
            ledger.source_selector_or_locator
        ), 1, 24
    ) AS source_observation_key,
    NULLIF(ledger.raw_field_text, '') AS raw_field_text,
    ledger.raw_field_text_sha256,
    NULLIF(ledger.atomic_source_text, '') AS atomic_source_text,
    ledger.atomic_source_text_sha256,
    ledger.source_text_storage_state AS text_storage_state,
    ledger.source_text_non_storage_reason,
    ledger.source_language, ledger.descriptor_class,
    NULLIF(ledger.source_native_lexical_form, '')
        AS source_native_lexical_form,
    ledger.source_native_lexical_form_sha256,
    NULLIF(ledger.normalized_candidate_form, '')
        AS normalized_candidate_form,
    ledger.normalized_candidate_form_sha256,
    'NONE'::TEXT AS normalization_method_code,
    ledger.evidence_tier, ledger.evidence_origin_type,
    ledger.origin_decision_basis, ledger.origin_evidence_locator,
    ledger.review_state, ledger.review_actor_type,
    NULL::BIGINT AS current_review_receipt_id,
    ledger.review_receipt_id AS provisional_decision_id,
    ledger.rights_decision_id,
    duplicate.deduplication_disposition,
    NULLIF(duplicate.within_record_repeat_group, '')
        AS within_record_repeat_group,
    NULLIF(duplicate.cross_observation_repeat_group, '')
        AS cross_observation_repeat_group,
    NULLIF(duplicate.mirror_group, '') AS mirror_group,
    FALSE AS translation_generated, FALSE AS synthetic_generated,
    FALSE AS roast_inferred_from_descriptor,
    FALSE AS preparation_inferred_from_descriptor,
    ledger.created_at::TIMESTAMPTZ, ledger.source_retrieved_at::TIMESTAMPTZ,
    artifact.source_file_sha256, ledger.route_index_sha256,
    ledger.source_file_sha256_scope, ledger.source_file_nonstorage_reason,
    ledger.parser_version, ledger.adapter_version
FROM stage_round3m_ledger AS ledger
JOIN expected_round3m_effective_record AS bridge
  ON bridge.round3m_effective_record_id = ledger.effective_record_id
JOIN expected_round3m_source_artifact AS artifact
  ON artifact.source_artifact_id = ledger.source_artifact_id
JOIN stage_round3m_duplicate AS duplicate
  USING (descriptor_assertion_id);

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, competition_descriptor_assertion_id,
    professional_acquisition_assertion_id, preparation_service_id,
    professional_acquisition_record_id, round3m_effective_record_id,
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
    origin_decision_basis, origin_evidence_locator, review_state,
    review_actor_type, current_review_receipt_id,
    provisional_decision_id, rights_decision_id,
    deduplication_disposition, within_record_repeat_group,
    cross_observation_repeat_group, mirror_group, translation_generated,
    synthetic_generated, roast_inferred_from_descriptor,
    preparation_inferred_from_descriptor, created_at,
    source_retrieved_at, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
)
SELECT
    descriptor_assertion_key, NULL::BIGINT, NULL::BIGINT, NULL::BIGINT,
    NULL::BIGINT, round3m_effective_record_id, effective_record_key,
    edition_year, source_artifact_id, source_route_id,
    schema_signature_id, publication_layer, source_field_label,
    source_field_label_sha256, source_selector_or_locator,
    source_page_or_record_locator, source_observation_key,
    raw_field_text, raw_field_text_sha256, atomic_source_text,
    atomic_source_text_sha256, text_storage_state,
    source_text_non_storage_reason, source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator, review_state,
    review_actor_type, current_review_receipt_id,
    provisional_decision_id, rights_decision_id,
    deduplication_disposition, within_record_repeat_group,
    cross_observation_repeat_group, mirror_group, translation_generated,
    synthetic_generated, roast_inferred_from_descriptor,
    preparation_inferred_from_descriptor, created_at,
    source_retrieved_at, source_file_sha256, route_index_sha256,
    source_file_sha256_scope, source_file_nonstorage_reason,
    parser_version, adapter_version
FROM expected_round3m_assertion
ON CONFLICT (descriptor_assertion_key) DO NOTHING;

CREATE TEMP VIEW expected_round3m_pair AS
SELECT
    pair.coassertion_event_id AS coassertion_event_key,
    'coassertion-set:' || substr(
        audit.round3i_utf8_sha256(
            left_assertion.effective_record_key || E'\x1f' ||
            left_assertion.source_observation_key
        ), 1, 24
    ) AS coassertion_set_key,
    left_assertion.effective_record_key,
    left_assertion.source_observation_key,
    least(left_assertion.descriptor_assertion_id,
          right_assertion.descriptor_assertion_id)
        AS left_descriptor_assertion_id,
    greatest(left_assertion.descriptor_assertion_id,
             right_assertion.descriptor_assertion_id)
        AS right_descriptor_assertion_id,
    'round3m.coassertion-builder.v1'::TEXT AS generated_by_version
FROM stage_round3m_pair AS pair
JOIN corpus.round3m_descriptor_assertion AS left_assertion
  ON left_assertion.descriptor_assertion_key =
     pair.left_descriptor_assertion_id
JOIN corpus.round3m_descriptor_assertion AS right_assertion
  ON right_assertion.descriptor_assertion_key =
     pair.right_descriptor_assertion_id;

INSERT INTO corpus.round3m_coassertion_event (
    coassertion_event_key, coassertion_set_key, effective_record_key,
    source_observation_key, left_descriptor_assertion_id,
    right_descriptor_assertion_id, generated_by_version
)
SELECT * FROM expected_round3m_pair
ON CONFLICT (coassertion_event_key) DO NOTHING;

CREATE TEMP VIEW expected_round3m_analyst_time AS
SELECT
    analyst_time_log_key, task_type,
    CASE WHEN NULLIF(source_route_id, '') IS NULL THEN 'MULTIPLE_ROUTES'
         ELSE 'SOURCE_ROUTE' END AS scope_type,
    NULLIF(source_route_id, '') AS source_route_id,
    artifact_count::BIGINT, candidate_count::BIGINT,
    reviewed_count::BIGINT, started_at::TIMESTAMPTZ,
    ended_at::TIMESTAMPTZ, active_minutes::NUMERIC(12, 3),
    CASE WHEN automated_runtime_seconds LIKE 'NA\_%' ESCAPE '\'
         THEN NULL::NUMERIC(16, 3)
         ELSE automated_runtime_seconds::NUMERIC(16, 3)
    END AS automated_runtime_seconds,
    review_actor_type, notes
FROM stage_round3m_analyst_time;

INSERT INTO audit.round3m_analyst_time_log (
    analyst_time_log_key, task_type, scope_type, source_route_id,
    artifact_count, candidate_count, reviewed_count, started_at,
    ended_at, active_minutes, automated_runtime_seconds,
    review_actor_type, notes
)
SELECT * FROM expected_round3m_analyst_time
ON CONFLICT (analyst_time_log_key) DO NOTHING;

DO $round3m_idempotence_and_counts$
BEGIN
    IF (SELECT count(*) FROM evidence.round3m_independent_source_family) <> 11
       OR (SELECT count(*) FROM evidence.round3m_source_route) <> 135
       OR (SELECT count(*) FROM evidence.round3m_source_schema_signature) <> 4
       OR (SELECT count(*) FROM evidence.round3m_source_artifact) <> 8
       OR (SELECT count(*) FROM competition.round3m_effective_record_bridge) <> 8
       OR (SELECT count(*) FROM audit.round3m_descriptor_review_queue_item) <> 516
       OR (SELECT count(*) FROM audit.round3m_descriptor_provisional_decision) <> 516
       OR (SELECT count(*) FROM evidence.round3m_candidate_rights_decision) <> 3096
       OR (SELECT count(*) FROM evidence.round3m_descriptor_rights_decision) <> 140
       OR (SELECT count(*) FROM corpus.round3m_descriptor_assertion) <> 140
       OR (SELECT count(*) FROM corpus.round3m_coassertion_event) <> 508
       OR (SELECT count(*) FROM audit.round3m_analyst_time_log) < 1 THEN
        RAISE EXCEPTION 'Round 3M import table counts differ from the validated package';
    END IF;

    IF EXISTS (
        SELECT * FROM expected_round3m_family
        EXCEPT
        SELECT independent_source_family_id, organizer_id, family_name,
               independence_basis, rights_lineage_id,
               admitted_for_descriptor_research
        FROM evidence.round3m_independent_source_family
    ) OR EXISTS (
        SELECT source_route_id, independent_source_family_id,
               organizer_id, publication_host, canonical_url,
               route_pattern, route_disposition, rights_lineage_id,
               mirror_lineage_id, discovered_at
        FROM expected_round3m_route
        EXCEPT
        SELECT source_route_id, independent_source_family_id,
               organizer_id, publication_host, canonical_url,
               route_pattern, route_disposition, rights_lineage_id,
               mirror_lineage_id, discovered_at
        FROM evidence.round3m_source_route
    ) OR EXISTS (
        SELECT * FROM expected_round3m_schema
        EXCEPT
        SELECT schema_signature_id, source_route_id, schema_version,
               host, route_pattern, edition_or_period,
               field_labels_json, selectors_json,
               publication_layer_rules_json,
               field_origin_assumptions_json, known_ambiguity,
               positive_fixture_locator, negative_fixture_locator,
               adapter_version, live_positive_fixture_present,
               validation_status
        FROM evidence.round3m_source_schema_signature
    ) OR EXISTS (
        SELECT * FROM expected_round3m_source_artifact
        EXCEPT
        SELECT source_artifact_id, source_route_id, schema_signature_id,
               governed_locator, source_retrieved_at, source_file_sha256,
               route_index_sha256, source_file_sha256_scope,
               source_file_nonstorage_reason, file_size_bytes,
               storage_state, non_storage_reason, parser_version,
               adapter_version
        FROM evidence.round3m_source_artifact
    ) OR EXISTS (
        SELECT * FROM expected_round3m_effective_record
        EXCEPT
        SELECT round3m_effective_record_id, effective_record_key,
               series_id, edition_id, edition_year, category_id, round_id,
               subject_kind, entry_or_lot_id, preparation_service_code,
               preparation_evidence_locator, source_route_id,
               source_artifact_id, source_record_locator,
               source_file_sha256, route_index_sha256,
               source_file_sha256_scope, source_file_nonstorage_reason,
               record_identity_sha256, identity_resolution_state,
               synthetic_generated, preparation_inferred_from_descriptor
        FROM competition.round3m_effective_record_bridge
    ) THEN
        RAISE EXCEPTION 'Round 3M immutable source identity conflicts with staged artifacts';
    END IF;

    IF EXISTS (
        SELECT * FROM expected_round3m_queue
        EXCEPT
        SELECT review_queue_id, descriptor_assertion_id,
               professional_record_id, source_family_id, source_route_id,
               edition_id, edition_year, source_artifact_id,
               source_file_sha256, route_index_sha256,
               source_file_sha256_scope, source_file_nonstorage_reason,
               raw_record_sha256, source_locator, source_language,
               source_text_sha256, source_text_storage_state,
               source_text_non_storage_reason, source_field_contract,
               publication_layer, descriptor_class, evidence_tier,
               review_state, review_actor_type, current_disposition,
               disposition_reason_code, human_review_required,
               model_eligible, decision_effective_date
        FROM audit.round3m_descriptor_review_queue_item
    ) OR EXISTS (
        SELECT * FROM expected_round3m_decision
        EXCEPT
        SELECT decision_id, review_queue_id, descriptor_assertion_id,
               current_disposition, descriptor_class, review_state,
               review_actor_type, review_protocol_version,
               decision_reason_code, decision_basis, evidence_locator,
               source_file_sha256, route_index_sha256,
               source_file_sha256_scope, source_file_nonstorage_reason,
               source_text_sha256, human_confirmed,
               expert_adjudicated, counts_as_reviewed_descriptor,
               model_eligible, decision_effective_date
        FROM audit.round3m_descriptor_provisional_decision
    ) OR EXISTS (
        SELECT * FROM expected_round3m_candidate_rights
        EXCEPT
        SELECT rights_decision_id, descriptor_assertion_id,
               source_artifact_id, purpose, rights_state, decision_basis,
               rights_evidence_locator, review_actor_type,
               model_eligibility_effect
        FROM evidence.round3m_candidate_rights_decision
    ) OR EXISTS (
        SELECT * FROM expected_round3m_rights_bundle
        EXCEPT
        SELECT rights_decision_id, rights_scope_id, decision_version,
               supersedes_rights_decision_id, source_route_id,
               publication_layer, source_field_label, public_discovery,
               internal_research_analysis, derived_research_data,
               model_research, deployment_or_commercial_model,
               raw_redistribution, decision_authority_code,
               decision_actor_type, decision_basis, evidence_locator,
               decided_at
        FROM evidence.round3m_descriptor_rights_decision
    ) THEN
        RAISE EXCEPTION 'Round 3M queue, decision, or rights identity conflicts with staged artifacts';
    END IF;

    IF EXISTS (
        SELECT * FROM expected_round3m_assertion
        EXCEPT
        SELECT descriptor_assertion_key, round3m_effective_record_id,
               effective_record_key, edition_year, source_artifact_id,
               source_route_id, schema_signature_id, publication_layer,
               source_field_label, source_field_label_sha256,
               source_selector_or_locator, source_page_or_record_locator,
               source_observation_key, raw_field_text,
               raw_field_text_sha256, atomic_source_text,
               atomic_source_text_sha256, text_storage_state,
               source_text_non_storage_reason, source_language,
               descriptor_class, source_native_lexical_form,
               source_native_lexical_form_sha256,
               normalized_candidate_form,
               normalized_candidate_form_sha256,
               normalization_method_code, evidence_tier,
               evidence_origin_type, origin_decision_basis,
               origin_evidence_locator, review_state, review_actor_type,
               current_review_receipt_id, provisional_decision_id,
               rights_decision_id, deduplication_disposition,
               within_record_repeat_group, cross_observation_repeat_group,
               mirror_group, translation_generated, synthetic_generated,
               roast_inferred_from_descriptor,
               preparation_inferred_from_descriptor, created_at,
               source_retrieved_at, source_file_sha256,
               route_index_sha256, source_file_sha256_scope,
               source_file_nonstorage_reason, parser_version,
               adapter_version
        FROM corpus.round3m_descriptor_assertion
    ) OR EXISTS (
        SELECT * FROM expected_round3m_pair
        EXCEPT
        SELECT coassertion_event_key, coassertion_set_key,
               effective_record_key, source_observation_key,
               left_descriptor_assertion_id,
               right_descriptor_assertion_id, generated_by_version
        FROM corpus.round3m_coassertion_event
    ) OR EXISTS (
        SELECT * FROM expected_round3m_analyst_time
        EXCEPT
        SELECT analyst_time_log_key, task_type, scope_type,
               source_route_id, artifact_count, candidate_count,
               reviewed_count, started_at, ended_at, active_minutes,
               automated_runtime_seconds, review_actor_type, notes
        FROM audit.round3m_analyst_time_log
    ) THEN
        RAISE EXCEPTION 'Round 3M assertion, pair, or analyst-time identity conflicts with staged artifacts';
    END IF;

    IF (SELECT count(*) FROM corpus.v_round3m_assertion_level_deinflated) <> 139
       OR (SELECT count(*) FROM corpus.v_round3m_record_unique_descriptor) <> 137
       OR (SELECT count(*) FROM corpus.v_round3m_human_reviewed_descriptor_universe) <> 0
       OR (SELECT count(*) FROM corpus.v_round3m_model_eligible_descriptor_universe) <> 0
       OR EXISTS (
          SELECT 1 FROM corpus.round3m_descriptor_assertion
          WHERE current_review_receipt_id IS NOT NULL
             OR review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
             OR raw_field_text IS NOT NULL
             OR atomic_source_text IS NOT NULL
             OR source_native_lexical_form IS NOT NULL
             OR normalized_candidate_form IS NOT NULL
             OR synthetic_generated
             OR translation_generated
             OR roast_inferred_from_descriptor
             OR preparation_inferred_from_descriptor
       ) THEN
        RAISE EXCEPTION 'Round 3M promotion or public-text boundary was violated';
    END IF;
END
$round3m_idempotence_and_counts$;

COMMIT;

SELECT
    (SELECT count(*) FROM audit.round3m_descriptor_review_queue_item)
        AS review_queue_count,
    (SELECT count(*) FROM evidence.round3m_candidate_rights_decision)
        AS purpose_rights_count,
    (SELECT count(*) FROM corpus.round3m_descriptor_assertion)
        AS live_assertion_count,
    (SELECT count(*) FROM corpus.v_round3m_assertion_level_deinflated)
        AS assertion_level_deinflated_count,
    (SELECT count(*) FROM corpus.v_round3m_record_unique_descriptor)
        AS record_level_unique_count,
    (SELECT count(*) FROM corpus.round3m_coassertion_event)
        AS coassertion_event_count,
    (SELECT count(*) FROM corpus.v_round3m_human_reviewed_descriptor_universe)
        AS human_reviewed_count,
    (SELECT count(*) FROM corpus.v_round3m_model_eligible_descriptor_universe)
        AS model_eligible_count;

\echo ROUND3M_ARTIFACT_IMPORT_PASS
