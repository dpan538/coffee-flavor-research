\set ON_ERROR_STOP on
\pset pager off

\if :{?round3m_gate_status_tsv}
\else
\echo 'ROUND3M_GATE_TSV_PARITY_FAIL missing --set=round3m_gate_status_tsv=/absolute/path'
\quit 3
\endif
\setenv ROUND3M_GATE_STATUS_TSV :round3m_gate_status_tsv

-- Independent Round 3M normalization-challenge regression. Every fixture is
-- transaction-local and is rolled back.

BEGIN;

CREATE TEMP TABLE round3m_checked_in_gate_status (
    gate_version TEXT,
    gate_name TEXT,
    criterion_ordinal TEXT,
    metric_name TEXT,
    operator TEXT,
    observed_value TEXT,
    required_value TEXT,
    universe TEXT,
    pass TEXT,
    not_applicable TEXT,
    rights_blocker TEXT,
    data_blocker TEXT,
    review_blocker TEXT,
    explanatory_note TEXT
) ON COMMIT DROP;

\copy pg_temp.round3m_checked_in_gate_status FROM PROGRAM 'exec cat -- "$ROUND3M_GATE_STATUS_TSV"' WITH (FORMAT csv, HEADER true, DELIMITER E'\t', ENCODING 'UTF8')
\setenv ROUND3M_GATE_STATUS_TSV

DO $checked_in_gate_tsv_matches_current_v2$
DECLARE
    checked_in_count BIGINT;
    database_count BIGINT;
    checked_in_identity_count BIGINT;
    checked_in_minus_database BIGINT;
    database_minus_checked_in BIGINT;
BEGIN
    SELECT count(*), count(DISTINCT (
        gate_version, gate_name, criterion_ordinal
    ))
    INTO STRICT checked_in_count, checked_in_identity_count
    FROM round3m_checked_in_gate_status;

    SELECT count(*) INTO STRICT database_count
    FROM audit.v_round3m_descriptor_gate_status;

    SELECT count(*) INTO STRICT checked_in_minus_database
    FROM (
        SELECT *
        FROM round3m_checked_in_gate_status
        EXCEPT ALL
        SELECT
            gate_version::TEXT, gate_name::TEXT,
            criterion_ordinal::TEXT, metric_name::TEXT, operator::TEXT,
            observed_value::TEXT, required_value::TEXT, universe::TEXT,
            pass::TEXT, not_applicable::TEXT, rights_blocker::TEXT,
            data_blocker::TEXT, review_blocker::TEXT,
            explanatory_note::TEXT
        FROM audit.v_round3m_descriptor_gate_status
    ) AS checked_in_only;

    SELECT count(*) INTO STRICT database_minus_checked_in
    FROM (
        SELECT
            gate_version::TEXT, gate_name::TEXT,
            criterion_ordinal::TEXT, metric_name::TEXT, operator::TEXT,
            observed_value::TEXT, required_value::TEXT, universe::TEXT,
            pass::TEXT, not_applicable::TEXT, rights_blocker::TEXT,
            data_blocker::TEXT, review_blocker::TEXT,
            explanatory_note::TEXT
        FROM audit.v_round3m_descriptor_gate_status
        EXCEPT ALL
        SELECT *
        FROM round3m_checked_in_gate_status
    ) AS database_only;

    IF checked_in_count <> 56
       OR checked_in_identity_count <> 56
       OR database_count <> 56
       OR checked_in_minus_database <> 0
       OR database_minus_checked_in <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_GATE_TSV_PARITY=expected exact bidirectional 56-row equality; checked_in=% identities=% database=% checked_in_only=% database_only=%',
            checked_in_count, checked_in_identity_count, database_count,
            checked_in_minus_database, database_minus_checked_in;
    END IF;

    RAISE NOTICE
        'ROUND3M_CONSTRAINT=checked_in_gate_TSV_exact_bidirectional_v2_56_row_parity PASS';
END
$checked_in_gate_tsv_matches_current_v2$;

CREATE TEMP TABLE round3m_normalization_challenge_baseline (
    challenge_count BIGINT NOT NULL
) ON COMMIT DROP;

INSERT INTO round3m_normalization_challenge_baseline (challenge_count)
SELECT reviewed_ambiguous_or_unresolved_challenge_count
FROM audit.v_round3m_descriptor_gate_metrics;

-- Minimal governed Round 3K competition/source identity for the linked
-- professional expression.
INSERT INTO competition.series (
    series_key, official_name, organizer_name, series_scope_code,
    lifecycle_status_code
) VALUES (
    'round3m.normalization.contract.series',
    'Round 3M normalization contract series',
    'Round 3M normalization contract organizer', 'GLOBAL', 'active'
);

INSERT INTO competition.edition (
    edition_key, series_id, series_local_edition_key, edition_name,
    edition_year, lifecycle_status_code
)
SELECT 'round3m.normalization.contract.edition.2026', series_id, '2026',
       'Round 3M normalization contract edition 2026', 2026, 'active'
FROM competition.series
WHERE series_key = 'round3m.normalization.contract.series';

INSERT INTO competition.rule_version (
    rule_version_key, series_id, rule_family_key, version_number,
    publication_status_code, official_version_label, official_locator,
    lifecycle_status_code
)
SELECT 'round3m.normalization.contract.rules.v1', series_id,
       'round3m.normalization.contract.rules', 1, 'VERSIONED',
       'Round 3M normalization contract rules v1',
       'fixture://round3m-normalization/rules/v1', 'active'
FROM competition.series
WHERE series_key = 'round3m.normalization.contract.series';

INSERT INTO competition.category (
    category_key, category_identity_key, identity_version, series_id,
    edition_id, rule_version_id, source_category_code, category_name,
    category_kind_code, lifecycle_status_code
)
SELECT 'round3m.normalization.contract.category.open.v1',
       'round3m.normalization.contract.category.open', 1,
       series.series_id, edition.edition_id, rule_version.rule_version_id,
       'OPEN', 'Round 3M normalization contract open category',
       'SERVICE_CLASS', 'active'
FROM competition.series AS series
JOIN competition.edition AS edition
  ON edition.series_id = series.series_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = series.series_id
WHERE series.series_key = 'round3m.normalization.contract.series'
  AND edition.edition_key =
      'round3m.normalization.contract.edition.2026'
  AND rule_version.rule_version_key =
      'round3m.normalization.contract.rules.v1';

INSERT INTO competition.round (
    round_key, round_identity_key, identity_version, series_id, edition_id,
    rule_version_id, source_round_code, round_name, round_kind_code,
    sequence_number, lifecycle_status_code
)
SELECT 'round3m.normalization.contract.round.final.v1',
       'round3m.normalization.contract.round.final', 1,
       category.series_id, category.edition_id, category.rule_version_id,
       'FINAL', 'Round 3M normalization contract final', 'FINAL', 1,
       'active'
FROM competition.category AS category
WHERE category.category_key =
      'round3m.normalization.contract.category.open.v1';

INSERT INTO competition.entry (
    entry_key, entry_identity_key, identity_version, series_id, edition_id,
    category_id, source_entry_identifier, entry_kind_code,
    lifecycle_status_code
)
SELECT 'round3m.normalization.contract.entry.v1',
       'round3m.normalization.contract.entry', 1,
       category.series_id, category.edition_id, category.category_id,
       'ROUND3M-NORMALIZATION-CONTRACT-ENTRY', 'COMPETITOR_ENTRY', 'active'
FROM competition.category AS category
WHERE category.category_key =
      'round3m.normalization.contract.category.open.v1';

INSERT INTO competition.coffee_identity (
    coffee_identity_key, coffee_identity_group_key, identity_version,
    identity_kind_code, source_native_coffee_identifier,
    lifecycle_status_code
) VALUES (
    'round3m.normalization.contract.coffee.v1',
    'round3m.normalization.contract.coffee', 1, 'SOURCE_DECLARED',
    'ROUND3M-NORMALIZATION-CONTRACT-COFFEE', 'active'
);

INSERT INTO competition.lot (
    lot_key, lot_identity_key, identity_version, series_id, edition_id,
    category_id, coffee_identity_id, source_lot_identifier, lot_kind_code,
    lifecycle_status_code
)
SELECT 'round3m.normalization.contract.lot.v1',
       'round3m.normalization.contract.lot', 1,
       category.series_id, category.edition_id, category.category_id,
       coffee.coffee_identity_id, 'ROUND3M-NORMALIZATION-CONTRACT-LOT',
       'COMPETITION_LOT', 'active'
FROM competition.category AS category
CROSS JOIN competition.coffee_identity AS coffee
WHERE category.category_key =
      'round3m.normalization.contract.category.open.v1'
  AND coffee.coffee_identity_key =
      'round3m.normalization.contract.coffee.v1';

INSERT INTO competition.entry_coffee_link (
    entry_coffee_link_key, series_id, edition_id, category_id, entry_id,
    coffee_identity_id, lot_id, link_role_code, linkage_status_code
)
SELECT 'round3m.normalization.contract.entry-coffee.primary',
       entry.series_id, entry.edition_id, entry.category_id, entry.entry_id,
       lot.coffee_identity_id, lot.lot_id, 'PRIMARY', 'SOURCE_DECLARED'
FROM competition.entry AS entry
JOIN competition.lot AS lot
  ON lot.series_id = entry.series_id
 AND lot.edition_id = entry.edition_id
 AND lot.category_id = entry.category_id
WHERE entry.entry_key = 'round3m.normalization.contract.entry.v1'
  AND lot.lot_key = 'round3m.normalization.contract.lot.v1';

INSERT INTO competition.preparation_service (
    preparation_service_key, series_id, edition_id, category_id, round_id,
    entry_id, entry_service_key, rule_version_id, scoresheet_status_code,
    fresh_preparation_confirmed, fresh_preparation_status_code,
    preparation_taxonomy_code, milk_auxiliary,
    black_coffee_core_candidate, c0_source_status_code,
    c0_preparation_concept_id, c0_assignment_basis_code,
    source_native_roast_status_code, c1_mapping_status_code,
    lifecycle_status_code
)
SELECT 'round3m.normalization.contract.service', entry.series_id,
       entry.edition_id, entry.category_id, round_record.round_id,
       entry.entry_id, 'round3m.normalization.contract.entry-service',
       rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
       'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'REPORTED',
       preparation.preparation_concept_id, 'OFFICIAL_PROTOCOL',
       'NOT_REPORTED', 'NOT_REPORTED', 'active'
FROM competition.entry AS entry
JOIN competition.round AS round_record
  ON round_record.series_id = entry.series_id
 AND round_record.edition_id = entry.edition_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = entry.series_id
CROSS JOIN context.preparation_concept AS preparation
WHERE entry.entry_key = 'round3m.normalization.contract.entry.v1'
  AND round_record.round_key =
      'round3m.normalization.contract.round.final.v1'
  AND rule_version.rule_version_key =
      'round3m.normalization.contract.rules.v1'
  AND preparation.preparation_concept_key =
      'preparation.family.filter_percolation';

INSERT INTO evidence.source_family (
    source_family_key, family_name, family_type, canonical_origin_key,
    counts_as_independent, mirror_of_source_family_key, independence_basis,
    admitted, introduced_round
) VALUES (
    'round3m.normalization.contract.round3k-family',
    'Round 3M normalization contract Round 3K source family',
    'PROFESSIONAL_COMPETITION',
    'round3m.normalization.contract.round3k-origin', TRUE, NULL,
    'Transaction-local independent professional source fixture.', TRUE, '3K'
);

INSERT INTO evidence.professional_source (
    professional_source_key, source_family_key, title, official_owner,
    canonical_url, source_type_code, evidence_tier_scope,
    access_state_code, automation_permission_state_code, data_custodian,
    independence_basis, admitted
) VALUES (
    'round3m.normalization.contract.round3k-source',
    'round3m.normalization.contract.round3k-family',
    'Round 3M normalization contract official results',
    'Round 3M normalization contract organizer',
    'https://example.invalid/round3m-normalization/results',
    'OFFICIAL_JSON_API', ARRAY['P2']::TEXT[], 'PUBLIC', 'PERMITTED',
    'Round 3M normalization contract organizer',
    'Direct official transaction-local source fixture.', TRUE
);

INSERT INTO evidence.professional_source_series (
    professional_source_id, series_id, source_role_code
)
SELECT source.professional_source_id, series.series_id, 'PRIMARY_RESULTS'
FROM evidence.professional_source AS source
CROSS JOIN competition.series AS series
WHERE source.professional_source_key =
      'round3m.normalization.contract.round3k-source'
  AND series.series_key = 'round3m.normalization.contract.series';

INSERT INTO evidence.professional_source_snapshot (
    professional_source_snapshot_key, professional_source_id,
    source_family_key, exact_version, retrieved_at, immutable_locator,
    snapshot_sha256, access_method_code,
    automated_access_compliance_code,
    lawfully_acquired_for_internal_research, source_record_count, admitted
)
SELECT 'round3m.normalization.contract.round3k-snapshot',
       professional_source_id, source_family_key, 'fixture-v1',
       '2026-08-28T01:00:00Z',
       'https://example.invalid/round3m-normalization/results#fixture-v1',
       repeat('c', 64), 'PERMITTED_HTTP', 'PERMITTED', TRUE, 1, TRUE
FROM evidence.professional_source
WHERE professional_source_key =
      'round3m.normalization.contract.round3k-source';

INSERT INTO evidence.professional_source_file (
    professional_source_file_key, professional_source_snapshot_id,
    filename, file_role_code, official_locator, local_path,
    declared_sha256, verified_sha256, file_size_bytes, row_count,
    field_count, hash_verified, retention_state_code,
    public_redistribution_allowed, source_owner, source_url,
    license_or_terms, attribution_requirement, modification_status
)
SELECT fixture.file_key, snapshot.professional_source_snapshot_id,
       fixture.filename, 'RAW_OFFICIAL', snapshot.immutable_locator,
       NULL, fixture.sha256, fixture.sha256, 2048, 1, 1, TRUE,
       'HASH_AND_LOCATOR_ONLY', FALSE,
       'Round 3M normalization contract organizer',
       'https://example.invalid/round3m-normalization/results',
       'Transaction-local explicit research fixture terms.',
       'Fixture organizer attribution required.', 'Unmodified fixture.'
FROM (VALUES
    (
        'round3m.normalization.contract.round3k-file',
        'round3m-normalization-contract.json', repeat('c', 64)
    ),
    (
        'round3m.normalization.contract.round3k-wrong-file',
        'round3m-normalization-contract-wrong.json', repeat('e', 64)
    )
) AS fixture(file_key, filename, sha256)
CROSS JOIN evidence.professional_source_snapshot AS snapshot
WHERE snapshot.professional_source_snapshot_key =
      'round3m.normalization.contract.round3k-snapshot';

INSERT INTO evidence.professional_rights_decision (
    professional_rights_decision_key, professional_source_snapshot_id,
    public_results_use, public_descriptor_use, internal_research_use,
    public_derived_release, model_research_use, commercial_model_use,
    decision_authority_code, evidence_basis, decided_on
)
SELECT 'round3m.normalization.contract.round3k-rights',
       professional_source_snapshot_id, 'ALLOWED', 'ALLOWED', 'ALLOWED',
       'DENIED', 'ALLOWED', 'PENDING', 'RIGHTS_HOLDER',
       'Transaction-local explicit organizer research permission.',
       DATE '2026-08-28'
FROM evidence.professional_source_snapshot
WHERE professional_source_snapshot_key =
      'round3m.normalization.contract.round3k-snapshot';

INSERT INTO evidence.professional_privacy_decision (
    professional_privacy_decision_key, professional_source_snapshot_id,
    personal_data_scope_code, direct_identifiers_retained,
    judge_identity_treatment_code, processing_basis,
    decision_state_code, decided_on
)
SELECT 'round3m.normalization.contract.round3k-privacy',
       professional_source_snapshot_id, 'NONE', FALSE, 'NOT_PRESENT',
       'Transaction-local fixture contains no personal data.',
       'ALLOWED', DATE '2026-08-28'
FROM evidence.professional_source_snapshot
WHERE professional_source_snapshot_key =
      'round3m.normalization.contract.round3k-snapshot';

INSERT INTO competition.organizer_published_note (
    organizer_published_note_key, preparation_service_id, edition_id,
    evidence_tier_code, note_role_code,
    professional_source_snapshot_id, professional_source_file_id,
    language_tag, raw_text,
    raw_text_sha256, source_locator
)
SELECT 'round3m.normalization.contract.organizer-note',
       service.preparation_service_id, service.edition_id, 'P2',
       'OFFICIAL_AGGREGATE_PROFILE', snapshot.professional_source_snapshot_id,
       source_file.professional_source_file_id, 'en',
       'qualified unresolved normalization challenge',
       audit.round3i_utf8_sha256(
           'qualified unresolved normalization challenge'
       ),
       snapshot.immutable_locator || '#qualified-unresolved'
FROM competition.preparation_service AS service
CROSS JOIN evidence.professional_source_snapshot AS snapshot
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id
 AND source_file.professional_source_file_key =
     'round3m.normalization.contract.round3k-file'
WHERE service.preparation_service_key =
      'round3m.normalization.contract.service'
  AND snapshot.professional_source_snapshot_key =
      'round3m.normalization.contract.round3k-snapshot';

INSERT INTO competition.descriptor_assertion (
    descriptor_assertion_key, preparation_service_id,
    organizer_published_note_id, assertion_type_code, evidence_tier_code,
    language_tag, raw_phrase, raw_phrase_sha256,
    professional_source_snapshot_id, professional_source_file_id,
    source_locator
)
SELECT 'round3m.normalization.contract.competition-assertion',
       note.preparation_service_id, note.organizer_published_note_id,
       'OFFICIAL_AGGREGATED_DESCRIPTOR', 'P2', 'en',
       'qualified unresolved normalization challenge',
       audit.round3i_utf8_sha256(
           'qualified unresolved normalization challenge'
       ), note.professional_source_snapshot_id,
       note.professional_source_file_id,
       note.source_locator || '#descriptor'
FROM competition.organizer_published_note AS note
WHERE note.organizer_published_note_key =
      'round3m.normalization.contract.organizer-note';

INSERT INTO corpus.professional_expression (
    professional_expression_key, descriptor_assertion_id, language_tag,
    normalized_phrase, normalization_rule_code
)
SELECT 'round3m.normalization.contract.expression',
       descriptor_assertion_id, language_tag,
       kb.normalize_expression(raw_phrase),
       'UNICODE_NFC_WHITESPACE_CASE'
FROM competition.descriptor_assertion
WHERE descriptor_assertion_key =
      'round3m.normalization.contract.competition-assertion';

-- Minimal governed Round 3M source, schema, artifact, and affirmative model
-- rights shared by the generic controls and the linked positive fixture.
INSERT INTO evidence.round3m_independent_source_family (
    independent_source_family_id, organizer_id, family_name,
    independence_basis, rights_lineage_id,
    admitted_for_descriptor_research
) VALUES (
    'round3m.normalization.contract.family',
    'round3m.normalization.contract.organizer',
    'Round 3M normalization contract family',
    'Transaction-local independent organizer/source origin.',
    'round3m.normalization.contract.rights-lineage', TRUE
);

INSERT INTO evidence.round3m_source_route (
    source_route_id, independent_source_family_id, organizer_id,
    publication_host, canonical_url, route_pattern, route_disposition,
    rights_lineage_id, mirror_lineage_id, discovered_at
) VALUES (
    'round3m.normalization.contract.route',
    'round3m.normalization.contract.family',
    'round3m.normalization.contract.organizer',
    'example.invalid',
    'https://example.invalid/round3m-normalization/results',
    '/round3m-normalization/results', 'PRIORITY_DESCRIPTOR_ROUTE',
    'round3m.normalization.contract.rights-lineage',
    'unresolved',
    '2026-08-28T01:00:00Z'
);

INSERT INTO evidence.round3m_source_schema_signature (
    schema_signature_id, source_route_id, schema_version, host,
    route_pattern, edition_or_period, field_labels_json, selectors_json,
    publication_layer_rules_json, field_origin_assumptions_json,
    known_ambiguity, positive_fixture_locator, negative_fixture_locator,
    adapter_version, live_positive_fixture_present, validation_status
) VALUES (
    'round3m.normalization.contract.schema',
    'round3m.normalization.contract.route', 1, 'example.invalid',
    '/round3m-normalization/results', '2026',
    '["Top Jury Descriptions"]'::JSONB,
    '{"field":"#top-jury"}'::JSONB,
    '{"Top Jury Descriptions":"PRIMARY_JURY_DESCRIPTION"}'::JSONB,
    '{"Top Jury Descriptions":"explicit jury attribution"}'::JSONB,
    'Transaction-local contract fixture.',
    'fixture://round3m-normalization/schema/positive',
    'fixture://round3m-normalization/schema/negative',
    'round3m-normalization-contract-adapter-v1', TRUE, 'VALIDATED'
);

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    professional_source_file_id,
    governed_locator, source_retrieved_at, source_file_sha256,
    route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, file_size_bytes, storage_state,
    non_storage_reason, parser_version, adapter_version
) SELECT
    'round3m.normalization.contract.artifact',
    'round3m.normalization.contract.route',
    'round3m.normalization.contract.schema',
    source_file.professional_source_file_id,
    source_file.official_locator,
    '2026-08-28T01:01:00Z', source_file.verified_sha256, '',
    'FULL_SOURCE_FILE_SHA256', '', 2048, 'HASH_AND_LOCATOR_ONLY',
    'Transaction-local fixture retains only its hash and locator.',
    'round3m-normalization-contract-parser-v1',
    'round3m-normalization-contract-adapter-v1'
FROM evidence.professional_source_file AS source_file
WHERE source_file.professional_source_file_key =
      'round3m.normalization.contract.round3k-file';

INSERT INTO evidence.round3m_source_artifact (
    source_artifact_id, source_route_id, schema_signature_id,
    professional_source_file_id,
    governed_locator, source_retrieved_at, source_file_sha256,
    route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, file_size_bytes, storage_state,
    non_storage_reason, parser_version, adapter_version
)
SELECT 'round3m.normalization.contract.wrong-artifact',
       'round3m.normalization.contract.route',
       'round3m.normalization.contract.schema',
       source_file.professional_source_file_id,
       source_file.official_locator,
       '2026-08-28T01:01:00Z', source_file.verified_sha256, '',
       'FULL_SOURCE_FILE_SHA256', '', 2048, 'HASH_AND_LOCATOR_ONLY',
       'Transaction-local wrong-file control retains only hash and locator.',
       'round3m-normalization-contract-parser-v1',
       'round3m-normalization-contract-adapter-v1'
FROM evidence.professional_source_file AS source_file
WHERE source_file.professional_source_file_key =
      'round3m.normalization.contract.round3k-wrong-file';

INSERT INTO evidence.round3m_descriptor_rights_decision (
    rights_decision_id, rights_scope_id, decision_version, source_route_id,
    publication_layer, source_field_label, public_discovery,
    internal_research_analysis, derived_research_data, model_research,
    deployment_or_commercial_model, raw_redistribution,
    decision_authority_code, decision_actor_type, decision_basis,
    evidence_locator, decided_at
) VALUES (
    'round3m.normalization.contract.rights',
    'round3m.normalization.contract.rights-scope', 1,
    'round3m.normalization.contract.route', 'PRIMARY_JURY_DESCRIPTION',
    'Top Jury Descriptions', 'AFFIRMATIVE', 'AFFIRMATIVE', 'AFFIRMATIVE',
    'AFFIRMATIVE', 'PENDING', 'PROHIBITED', 'RIGHTS_HOLDER',
    'RIGHTS_HOLDER',
    'Transaction-local explicit permission for internal and model research.',
    'fixture://round3m-normalization/rights',
    '2026-08-28T01:02:00Z'
);

-- Generic ambiguity/unresolved assertion receipts are not normalization-label
-- evidence. Both controls are intentionally unlinked and non-confirming.
INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, preparation_service_id, effective_record_key,
    edition_year, source_artifact_id, source_route_id, schema_signature_id,
    publication_layer, source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256, text_storage_state,
    source_text_non_storage_reason, source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator, review_state,
    review_actor_type, rights_decision_id, source_retrieved_at,
    source_file_sha256, route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, parser_version, adapter_version
)
SELECT 'round3m.normalization.contract.generic.' || fixture.suffix,
       service.preparation_service_id, service.preparation_service_key,
       edition.edition_year, 'round3m.normalization.contract.artifact',
       'round3m.normalization.contract.route',
       'round3m.normalization.contract.schema',
       'PRIMARY_JURY_DESCRIPTION', 'Top Jury Descriptions',
       audit.round3i_utf8_sha256('Top Jury Descriptions'),
       '#generic-' || fixture.suffix,
       'fixture://round3m-normalization/generic/' || fixture.suffix,
       'round3m.normalization.contract.observation.generic.' ||
           fixture.suffix,
       fixture.phrase, audit.round3i_utf8_sha256(fixture.phrase),
       fixture.phrase, audit.round3i_utf8_sha256(fixture.phrase),
       'REVIEWED_EXCERPT', '', 'en', 'STRICT_FLAVOR', fixture.phrase,
       audit.round3i_utf8_sha256(fixture.phrase), fixture.phrase,
       audit.round3i_utf8_sha256(fixture.phrase),
       'UNICODE_NFC_WHITESPACE_CASE', 'P2',
       'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION',
       'Explicit organizer-published jury-description field.',
       'fixture://round3m-normalization/generic/' || fixture.suffix,
       'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
       'round3m.normalization.contract.rights',
       '2026-08-28T01:01:00Z', repeat('c', 64), '',
       'FULL_SOURCE_FILE_SHA256', '',
       'round3m-normalization-contract-parser-v1',
       'round3m-normalization-contract-adapter-v1'
FROM (VALUES
    ('ambiguous', 'generic ambiguous assertion receipt'),
    ('unresolved', 'generic unresolved assertion receipt')
) AS fixture(suffix, phrase)
CROSS JOIN competition.preparation_service AS service
JOIN competition.edition AS edition
  ON edition.edition_id = service.edition_id
WHERE service.preparation_service_key =
      'round3m.normalization.contract.service';

INSERT INTO audit.round3m_descriptor_review_receipt (
    review_receipt_key, descriptor_assertion_id, receipt_version,
    reviewer_id_or_pseudonymous_code, reviewer_role, review_actor_type,
    receipt_origin_code, human_event_evidence_sha256,
    review_protocol_version, decision, decision_reason, evidence_locator,
    reviewed_at, adjudication_status, previous_decision
)
SELECT 'round3m.normalization.contract.generic-receipt.' || fixture.suffix,
       assertion.descriptor_assertion_id, 1,
       'round3m-normalization-generic-human-' || fixture.suffix,
       'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
       'DOCUMENTED_HUMAN_EVENT', fixture.event_sha256,
       'round3m-normalization-generic-v1', fixture.decision,
       'Generic assertion-level review is not qualified normalization review.',
       'fixture://round3m-normalization/generic-review/' || fixture.suffix,
       transaction_timestamp() - interval '2 hours', 'NOT_REQUIRED',
       'PROVISIONAL_MACHINE_CLASSIFIED'
FROM (VALUES
    ('ambiguous', 'MARK_AMBIGUOUS', repeat('1', 64)),
    ('unresolved', 'MARK_UNRESOLVED', repeat('2', 64))
) AS fixture(suffix, decision, event_sha256)
JOIN corpus.round3m_descriptor_assertion AS assertion
  ON assertion.descriptor_assertion_key =
     'round3m.normalization.contract.generic.' || fixture.suffix;

UPDATE corpus.round3m_descriptor_assertion AS assertion
SET review_state = 'PROVENANCE_UNRESOLVED',
    review_actor_type = 'HUMAN_REVIEWER',
    current_review_receipt_id = receipt.review_receipt_id
FROM audit.round3m_descriptor_review_receipt AS receipt
WHERE receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
  AND assertion.descriptor_assertion_key LIKE
      'round3m.normalization.contract.generic.%';

DO $generic_assertion_receipts_add_zero$
DECLARE
    baseline_count BIGINT;
    current_count BIGINT;
    fixture_universe_count BIGINT;
BEGIN
    SELECT challenge_count INTO STRICT baseline_count
    FROM round3m_normalization_challenge_baseline;

    SELECT reviewed_ambiguous_or_unresolved_challenge_count
    INTO STRICT current_count
    FROM audit.v_round3m_descriptor_gate_metrics;

    SELECT count(*) INTO STRICT fixture_universe_count
    FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
    WHERE descriptor_assertion_key LIKE
          'round3m.normalization.contract.generic.%';

    IF current_count IS DISTINCT FROM baseline_count
       OR fixture_universe_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_NORMALIZATION_CHALLENGE=generic_receipt_only expected metric delta 0 and universe 0; baseline=% current=% universe=%',
            baseline_count, current_count, fixture_universe_count;
    END IF;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=generic_MARK_AMBIGUOUS_and_MARK_UNRESOLVED_add_zero PASS';
END
$generic_assertion_receipts_add_zero$;

-- Positive assertion: the source descriptor itself is model-eligible and
-- human-confirmed. Its normalization remains a separately governed qualified-
-- human UNRESOLVED decision.
INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, competition_descriptor_assertion_id,
    preparation_service_id, effective_record_key, edition_year,
    source_artifact_id, source_route_id, schema_signature_id,
    publication_layer, source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256, text_storage_state,
    source_text_non_storage_reason, source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator, review_state,
    review_actor_type, rights_decision_id, source_retrieved_at,
    source_file_sha256, route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, parser_version, adapter_version
)
SELECT 'round3m.normalization.contract.qualified-assertion',
       competition_assertion.descriptor_assertion_id,
       service.preparation_service_id, service.preparation_service_key,
       edition.edition_year, 'round3m.normalization.contract.artifact',
       'round3m.normalization.contract.route',
       'round3m.normalization.contract.schema',
       'PRIMARY_JURY_DESCRIPTION', 'Top Jury Descriptions',
       audit.round3i_utf8_sha256('Top Jury Descriptions'),
       '#qualified-unresolved',
       competition_assertion.source_locator,
       'round3m.normalization.contract.observation.qualified',
       competition_assertion.raw_phrase,
       competition_assertion.raw_phrase_sha256,
       competition_assertion.raw_phrase,
       competition_assertion.raw_phrase_sha256,
       'REVIEWED_EXCERPT', '', competition_assertion.language_tag,
       'STRICT_FLAVOR', competition_assertion.raw_phrase,
       competition_assertion.raw_phrase_sha256,
       kb.normalize_expression(competition_assertion.raw_phrase),
       audit.round3i_utf8_sha256(
           kb.normalize_expression(competition_assertion.raw_phrase)
       ), 'UNICODE_NFC_WHITESPACE_CASE', 'P2',
       'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION',
       'Explicit organizer-published jury-description field.',
       'fixture://round3m-normalization/qualified-unresolved',
       'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
       'round3m.normalization.contract.rights',
       '2026-08-28T01:01:00Z', repeat('c', 64), '',
       'FULL_SOURCE_FILE_SHA256', '',
       'round3m-normalization-contract-parser-v1',
       'round3m-normalization-contract-adapter-v1'
FROM competition.descriptor_assertion AS competition_assertion
JOIN competition.preparation_service AS service
  ON service.preparation_service_id =
     competition_assertion.preparation_service_id
JOIN competition.edition AS edition
  ON edition.edition_id = service.edition_id
WHERE competition_assertion.descriptor_assertion_key =
      'round3m.normalization.contract.competition-assertion';

INSERT INTO audit.round3m_descriptor_review_receipt (
    review_receipt_key, descriptor_assertion_id, receipt_version,
    reviewer_id_or_pseudonymous_code, reviewer_role, review_actor_type,
    receipt_origin_code, human_event_evidence_sha256,
    review_protocol_version, decision, decision_reason, evidence_locator,
    reviewed_at, adjudication_status, previous_decision
)
SELECT 'round3m.normalization.contract.confirmation-receipt',
       descriptor_assertion_id, 1,
       'round3m-normalization-confirming-human',
       'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
       'DOCUMENTED_HUMAN_EVENT', repeat('3', 64),
       'round3m-normalization-confirmation-v1', 'CONFIRM_DESCRIPTOR',
       'Actual-human confirmation of the source-native descriptor instance.',
       'fixture://round3m-normalization/confirmation',
       transaction_timestamp() - interval '2 hours', 'NOT_REQUIRED',
       'PROVISIONAL_MACHINE_CLASSIFIED'
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key =
      'round3m.normalization.contract.qualified-assertion';

UPDATE corpus.round3m_descriptor_assertion AS assertion
SET review_state = 'HUMAN_CONFIRMED',
    review_actor_type = 'HUMAN_REVIEWER',
    current_review_receipt_id = receipt.review_receipt_id
FROM audit.round3m_descriptor_review_receipt AS receipt
WHERE receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
  AND assertion.descriptor_assertion_key =
      'round3m.normalization.contract.qualified-assertion';

INSERT INTO audit.reviewer (reviewer_key, display_name, affiliation)
VALUES
    (
        'round3m.normalization.contract.reviewer.independent-1',
        'Round 3M normalization independent reviewer 1',
        'Transaction-local fixture'
    ),
    (
        'round3m.normalization.contract.reviewer.independent-2',
        'Round 3M normalization independent reviewer 2',
        'Transaction-local fixture'
    ),
    (
        'round3m.normalization.contract.reviewer.adjudicator',
        'Round 3M normalization adjudicator',
        'Transaction-local fixture'
    );

INSERT INTO audit.round3m_human_reviewer_identity_receipt (
    reviewer_identity_receipt_key, reviewer_id,
    canonical_human_identity_sha256, identity_evidence_sha256,
    receipt_origin_code, evidence_locator
)
SELECT 'round3m.normalization.contract.identity.' || fixture.suffix,
       reviewer.reviewer_id,
       audit.round3i_utf8_sha256(
           'round3m canonical human identity ' || fixture.suffix
       ),
       audit.round3i_utf8_sha256(
           'round3m human identity evidence ' || fixture.suffix
       ),
       'DOCUMENTED_HUMAN_EVENT',
       'fixture://round3m-normalization/human-identity/' ||
           fixture.suffix
FROM (VALUES
    (
        'independent-1',
        'round3m.normalization.contract.reviewer.independent-1'
    ),
    (
        'independent-2',
        'round3m.normalization.contract.reviewer.independent-2'
    ),
    (
        'adjudicator',
        'round3m.normalization.contract.reviewer.adjudicator'
    )
) AS fixture(suffix, reviewer_key)
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = fixture.reviewer_key;

DO $duplicate_canonical_human_identity_rejected$
DECLARE
    rejected_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO audit.reviewer (
            reviewer_key, display_name, affiliation
        ) VALUES (
            'round3m.normalization.contract.reviewer.duplicate-human',
            'Round 3M duplicate-human negative control',
            'Transaction-local fixture'
        );

        INSERT INTO audit.round3m_human_reviewer_identity_receipt (
            reviewer_identity_receipt_key, reviewer_id,
            canonical_human_identity_sha256, identity_evidence_sha256,
            receipt_origin_code, evidence_locator
        )
        SELECT 'round3m.normalization.contract.identity.duplicate-human',
               duplicate_reviewer.reviewer_id,
               existing_identity.canonical_human_identity_sha256,
               repeat('f', 64), 'DOCUMENTED_HUMAN_EVENT',
               'fixture://round3m-normalization/human-identity/duplicate'
        FROM audit.reviewer AS duplicate_reviewer
        CROSS JOIN audit.round3m_human_reviewer_identity_receipt AS
            existing_identity
        WHERE duplicate_reviewer.reviewer_key =
              'round3m.normalization.contract.reviewer.duplicate-human'
          AND existing_identity.reviewer_identity_receipt_key =
              'round3m.normalization.contract.identity.independent-1';

        RAISE EXCEPTION USING
            ERRCODE = 'P0001',
            MESSAGE = 'expected duplicate canonical-human digest rejection';
    EXCEPTION
        WHEN unique_violation THEN
            GET STACKED DIAGNOSTICS
                rejected_constraint = CONSTRAINT_NAME;
            IF rejected_constraint IS DISTINCT FROM
               'round3m_human_reviewer_identity_digest_uq' THEN
                RAISE;
            END IF;
    END;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=duplicate_canonical_human_identity_digest_rejected PASS';
END
$duplicate_canonical_human_identity_rejected$;

INSERT INTO audit.professional_reviewer_qualification (
    reviewer_id, qualification_scope_code, source_language_tag,
    qualification_evidence, verified_on, eligible
)
SELECT reviewer.reviewer_id, qualification.scope_code, NULL,
       qualification.evidence,
       (transaction_timestamp() AT TIME ZONE 'UTC')::DATE - 1, TRUE
FROM (VALUES
    (
        'round3m.normalization.contract.reviewer.independent-1',
        'PROFESSIONAL_COFFEE_SENSORY',
        'Independent reviewer 1 professional sensory fixture evidence.'
    ),
    (
        'round3m.normalization.contract.reviewer.independent-2',
        'COMPETITION_JUDGING',
        'Independent reviewer 2 competition judging fixture evidence.'
    ),
    (
        'round3m.normalization.contract.reviewer.adjudicator',
        'PROFESSIONAL_COFFEE_SENSORY',
        'Adjudicator professional sensory fixture evidence.'
    ),
    (
        'round3m.normalization.contract.reviewer.adjudicator',
        'ADJUDICATION',
        'Adjudicator qualification fixture evidence.'
    )
) AS qualification(reviewer_key, scope_code, evidence)
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = qualification.reviewer_key;

INSERT INTO corpus.professional_label_decision (
    professional_label_decision_key, professional_expression_id,
    decision_version, label_disposition_code, decision_method_code,
    independent_qualified_reviewer_count, adjudicator_present,
    expert_review_complete, candidate_only, decision_status_code,
    provenance_complete, decision_basis, decided_at
)
SELECT 'round3m.normalization.contract.label.unresolved.final',
       professional_expression_id, 1, 'UNRESOLVED', 'QUALIFIED_REVIEW',
       2, TRUE, TRUE, FALSE, 'FINAL', TRUE,
       'Two qualified independent reviews and adjudication found no governed target.',
       transaction_timestamp()
FROM corpus.professional_expression
WHERE professional_expression_key =
      'round3m.normalization.contract.expression';

INSERT INTO audit.professional_label_review (
    professional_label_decision_id, reviewer_id, reviewer_role_code,
    review_outcome_code, review_evidence, reviewed_at
)
SELECT decision.professional_label_decision_id, reviewer.reviewer_id,
       fixture.role_code, 'ACCEPT', fixture.review_evidence,
       fixture.reviewed_at
FROM (VALUES
    (
        'round3m.normalization.contract.reviewer.independent-1',
        'INDEPENDENT_REVIEWER',
        'Independent review 1 supports the unresolved disposition.',
        transaction_timestamp() - interval '2 hours'
    ),
    (
        'round3m.normalization.contract.reviewer.independent-2',
        'INDEPENDENT_REVIEWER',
        'Independent review 2 supports the unresolved disposition.',
        transaction_timestamp() - interval '110 minutes'
    ),
    (
        'round3m.normalization.contract.reviewer.adjudicator',
        'ADJUDICATOR',
        'Adjudicator finalizes the unresolved disposition.',
        transaction_timestamp() - interval '90 minutes'
    )
) AS fixture(reviewer_key, role_code, review_evidence, reviewed_at)
CROSS JOIN corpus.professional_label_decision AS decision
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = fixture.reviewer_key
WHERE decision.professional_label_decision_key =
      'round3m.normalization.contract.label.unresolved.final';

INSERT INTO audit.round3m_professional_label_review_attestation (
    attestation_key, professional_label_review_id, review_actor_type,
    receipt_origin_code, reviewer_id_or_pseudonymous_code,
    reviewer_identity_receipt_key, human_event_evidence_sha256,
    human_event_member_sha256, review_payload_sha256,
    decision_review_set_sha256, reviewer_independence_set_sha256,
    evidence_locator, independence_evidence_locator
)
SELECT 'round3m.normalization.contract.attestation.' || fixture.suffix,
       review.professional_label_review_id, fixture.actor_type,
       'DOCUMENTED_HUMAN_EVENT',
       reviewer.reviewer_key,
       identity.reviewer_identity_receipt_key,
       fixture.human_event_sha256,
       audit.round3m_human_review_event_member_sha256(
           review.professional_label_review_id,
           fixture.human_event_sha256
       ),
       audit.round3m_professional_label_review_payload_sha256(
           review.professional_label_review_id
       ),
       audit.round3m_professional_label_review_set_sha256(
           decision.professional_label_decision_id
       ),
       audit.round3m_professional_reviewer_independence_set_sha256(
           decision.professional_label_decision_id
       ),
       'fixture://round3m-normalization/professional-review/' ||
           fixture.suffix,
       'fixture://round3m-normalization/independence/' || fixture.suffix
FROM (VALUES
    (
        'independent-1',
        'round3m.normalization.contract.reviewer.independent-1',
        'HUMAN_REVIEWER', repeat('4', 64)
    ),
    (
        'independent-2',
        'round3m.normalization.contract.reviewer.independent-2',
        'HUMAN_REVIEWER', repeat('5', 64)
    ),
    (
        'adjudicator',
        'round3m.normalization.contract.reviewer.adjudicator',
        'EXPERT_REVIEWER', repeat('6', 64)
    )
) AS fixture(suffix, reviewer_key, actor_type, human_event_sha256)
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = fixture.reviewer_key
JOIN audit.round3m_human_reviewer_identity_receipt AS identity
  ON identity.reviewer_id = reviewer.reviewer_id
JOIN audit.professional_label_review AS review
  ON review.reviewer_id = reviewer.reviewer_id
JOIN corpus.professional_label_decision AS decision
  ON decision.professional_label_decision_id =
     review.professional_label_decision_id
 AND decision.professional_label_decision_key =
     'round3m.normalization.contract.label.unresolved.final';

SET CONSTRAINTS ALL IMMEDIATE;

DO $qualified_human_normalization_challenge_adds_one$
DECLARE
    baseline_count BIGINT;
    current_count BIGINT;
    fixture_universe_count BIGINT;
BEGIN
    SELECT challenge_count INTO STRICT baseline_count
    FROM round3m_normalization_challenge_baseline;

    SELECT reviewed_ambiguous_or_unresolved_challenge_count
    INTO STRICT current_count
    FROM audit.v_round3m_descriptor_gate_metrics;

    SELECT count(*) INTO STRICT fixture_universe_count
    FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
    WHERE descriptor_assertion_key =
          'round3m.normalization.contract.qualified-assertion';

    IF current_count IS DISTINCT FROM baseline_count + 1
       OR fixture_universe_count <> 1 THEN
        RAISE EXCEPTION
            'ROUND3M_NORMALIZATION_CHALLENGE=qualified_UNRESOLVED expected metric delta 1 and universe 1; baseline=% current=% universe=%',
            baseline_count, current_count, fixture_universe_count;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
        WHERE descriptor_assertion_key LIKE
              'round3m.normalization.contract.generic.%'
    ) THEN
        RAISE EXCEPTION
            'ROUND3M_NORMALIZATION_CHALLENGE=generic assertion receipt leaked into qualified universe';
    END IF;

    RAISE NOTICE
        'ROUND3M_POSITIVE=model_eligible_confirmed_linked_FINAL_qualified_UNRESOLVED_adds_exactly_one PASS';
END
$qualified_human_normalization_challenge_adds_one$;

-- A fully reviewed and attested label decision still adds zero when its
-- Round 3M artifact names a different file/hash from the linked Round 3K
-- descriptor assertion.  The v1 candidate -> v2 final lineage also supplies
-- an unattested ancestor with an attested successor for immutability tests.
SET CONSTRAINTS ALL DEFERRED;

INSERT INTO competition.descriptor_assertion (
    descriptor_assertion_key, preparation_service_id,
    organizer_published_note_id, assertion_type_code, evidence_tier_code,
    language_tag, raw_phrase, raw_phrase_sha256,
    professional_source_snapshot_id, professional_source_file_id,
    source_locator
)
SELECT 'round3m.normalization.contract.wrong-binding.competition-assertion',
       note.preparation_service_id, note.organizer_published_note_id,
       'OFFICIAL_AGGREGATED_DESCRIPTOR', 'P2', 'en',
       'qualified unresolved wrong file binding',
       audit.round3i_utf8_sha256(
           'qualified unresolved wrong file binding'
       ), note.professional_source_snapshot_id,
       note.professional_source_file_id,
       note.source_locator || '#wrong-binding-descriptor'
FROM competition.organizer_published_note AS note
WHERE note.organizer_published_note_key =
      'round3m.normalization.contract.organizer-note';

INSERT INTO corpus.professional_expression (
    professional_expression_key, descriptor_assertion_id, language_tag,
    normalized_phrase, normalization_rule_code, created_at
)
SELECT 'round3m.normalization.contract.wrong-binding.expression',
       descriptor_assertion_id, language_tag,
       kb.normalize_expression(raw_phrase),
       'UNICODE_NFC_WHITESPACE_CASE',
       transaction_timestamp() - interval '4 hours'
FROM competition.descriptor_assertion
WHERE descriptor_assertion_key =
      'round3m.normalization.contract.wrong-binding.competition-assertion';

INSERT INTO corpus.round3m_descriptor_assertion (
    descriptor_assertion_key, competition_descriptor_assertion_id,
    preparation_service_id, effective_record_key, edition_year,
    source_artifact_id, source_route_id, schema_signature_id,
    publication_layer, source_field_label, source_field_label_sha256,
    source_selector_or_locator, source_page_or_record_locator,
    source_observation_key, raw_field_text, raw_field_text_sha256,
    atomic_source_text, atomic_source_text_sha256, text_storage_state,
    source_text_non_storage_reason, source_language, descriptor_class,
    source_native_lexical_form, source_native_lexical_form_sha256,
    normalized_candidate_form, normalized_candidate_form_sha256,
    normalization_method_code, evidence_tier, evidence_origin_type,
    origin_decision_basis, origin_evidence_locator, review_state,
    review_actor_type, rights_decision_id, source_retrieved_at,
    source_file_sha256, route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, parser_version, adapter_version
)
SELECT 'round3m.normalization.contract.wrong-binding.assertion',
       source_assertion.descriptor_assertion_id,
       service.preparation_service_id, service.preparation_service_key,
       edition.edition_year,
       'round3m.normalization.contract.wrong-artifact',
       'round3m.normalization.contract.route',
       'round3m.normalization.contract.schema',
       'PRIMARY_JURY_DESCRIPTION', 'Top Jury Descriptions',
       audit.round3i_utf8_sha256('Top Jury Descriptions'),
       '#wrong-file-binding', source_assertion.source_locator,
       'round3m.normalization.contract.observation.wrong-binding',
       source_assertion.raw_phrase, source_assertion.raw_phrase_sha256,
       source_assertion.raw_phrase, source_assertion.raw_phrase_sha256,
       'REVIEWED_EXCERPT', '', source_assertion.language_tag,
       'STRICT_FLAVOR', source_assertion.raw_phrase,
       source_assertion.raw_phrase_sha256,
       kb.normalize_expression(source_assertion.raw_phrase),
       audit.round3i_utf8_sha256(
           kb.normalize_expression(source_assertion.raw_phrase)
       ), 'UNICODE_NFC_WHITESPACE_CASE', 'P2',
       'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION',
       'Explicit jury field with deliberately mismatched Round 3M artifact.',
       'fixture://round3m-normalization/wrong-file-binding',
       'PROVISIONAL_MACHINE_CLASSIFIED', 'CODEX_SOURCE_AUDITOR',
       'round3m.normalization.contract.rights',
       '2026-08-28T01:01:00Z', repeat('e', 64), '',
       'FULL_SOURCE_FILE_SHA256', '',
       'round3m-normalization-contract-parser-v1',
       'round3m-normalization-contract-adapter-v1'
FROM competition.descriptor_assertion AS source_assertion
JOIN competition.preparation_service AS service
  ON service.preparation_service_id =
     source_assertion.preparation_service_id
JOIN competition.edition AS edition
  ON edition.edition_id = service.edition_id
WHERE source_assertion.descriptor_assertion_key =
      'round3m.normalization.contract.wrong-binding.competition-assertion';

INSERT INTO audit.round3m_descriptor_review_receipt (
    review_receipt_key, descriptor_assertion_id, receipt_version,
    reviewer_id_or_pseudonymous_code, reviewer_role, review_actor_type,
    receipt_origin_code, human_event_evidence_sha256,
    review_protocol_version, decision, decision_reason, evidence_locator,
    reviewed_at, adjudication_status, previous_decision
)
SELECT 'round3m.normalization.contract.wrong-binding.confirmation-receipt',
       descriptor_assertion_id, 1,
       'round3m-normalization-wrong-binding-human',
       'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
       'DOCUMENTED_HUMAN_EVENT', repeat('d', 64),
       'round3m-normalization-wrong-binding-v1', 'CONFIRM_DESCRIPTOR',
       'Human confirmation cannot repair a cross-file source mismatch.',
       'fixture://round3m-normalization/wrong-binding-confirmation',
       transaction_timestamp() - interval '2 hours', 'NOT_REQUIRED',
       'PROVISIONAL_MACHINE_CLASSIFIED'
FROM corpus.round3m_descriptor_assertion
WHERE descriptor_assertion_key =
      'round3m.normalization.contract.wrong-binding.assertion';

UPDATE corpus.round3m_descriptor_assertion AS assertion
SET review_state = 'HUMAN_CONFIRMED',
    review_actor_type = 'HUMAN_REVIEWER',
    current_review_receipt_id = receipt.review_receipt_id
FROM audit.round3m_descriptor_review_receipt AS receipt
WHERE receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
  AND assertion.descriptor_assertion_key =
      'round3m.normalization.contract.wrong-binding.assertion';

INSERT INTO corpus.professional_label_decision (
    professional_label_decision_key, professional_expression_id,
    decision_version, label_disposition_code, decision_method_code,
    independent_qualified_reviewer_count, adjudicator_present,
    expert_review_complete, candidate_only, decision_status_code,
    provenance_complete, decision_basis, decided_at
)
SELECT 'round3m.normalization.contract.wrong-binding.label.candidate',
       professional_expression_id, 1, 'UNRESOLVED',
       'SOURCE_RETAINED_CANDIDATE', 0, FALSE, FALSE, TRUE, 'CANDIDATE',
       TRUE, 'Unattested predecessor candidate for lineage protection.',
       transaction_timestamp() - interval '3 hours'
FROM corpus.professional_expression
WHERE professional_expression_key =
      'round3m.normalization.contract.wrong-binding.expression';

INSERT INTO corpus.professional_label_decision (
    professional_label_decision_key, professional_expression_id,
    decision_version, supersedes_decision_id, label_disposition_code,
    decision_method_code, independent_qualified_reviewer_count,
    adjudicator_present, expert_review_complete, candidate_only,
    decision_status_code, provenance_complete, decision_basis, decided_at
)
SELECT 'round3m.normalization.contract.wrong-binding.label.final',
       predecessor.professional_expression_id, 2,
       predecessor.professional_label_decision_id, 'UNRESOLVED',
       'QUALIFIED_REVIEW', 2, TRUE, TRUE, FALSE, 'FINAL', TRUE,
       'Qualified review retained unresolved status despite wrong file link.',
       transaction_timestamp()
FROM corpus.professional_label_decision AS predecessor
WHERE predecessor.professional_label_decision_key =
      'round3m.normalization.contract.wrong-binding.label.candidate';

INSERT INTO audit.professional_label_review (
    professional_label_decision_id, reviewer_id, reviewer_role_code,
    review_outcome_code, review_evidence, reviewed_at
)
SELECT decision.professional_label_decision_id, reviewer.reviewer_id,
       fixture.role_code, 'ACCEPT', fixture.review_evidence,
       fixture.reviewed_at
FROM (VALUES
    (
        'round3m.normalization.contract.reviewer.independent-1',
        'INDEPENDENT_REVIEWER',
        'Independent review 1 accepts the wrong-binding control decision.',
        transaction_timestamp() - interval '2 hours'
    ),
    (
        'round3m.normalization.contract.reviewer.independent-2',
        'INDEPENDENT_REVIEWER',
        'Independent review 2 accepts the wrong-binding control decision.',
        transaction_timestamp() - interval '110 minutes'
    ),
    (
        'round3m.normalization.contract.reviewer.adjudicator',
        'ADJUDICATOR',
        'Adjudicator accepts the wrong-binding control decision.',
        transaction_timestamp() - interval '90 minutes'
    )
) AS fixture(reviewer_key, role_code, review_evidence, reviewed_at)
CROSS JOIN corpus.professional_label_decision AS decision
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = fixture.reviewer_key
WHERE decision.professional_label_decision_key =
      'round3m.normalization.contract.wrong-binding.label.final';

INSERT INTO audit.round3m_professional_label_review_attestation (
    attestation_key, professional_label_review_id, review_actor_type,
    receipt_origin_code, reviewer_id_or_pseudonymous_code,
    reviewer_identity_receipt_key, human_event_evidence_sha256,
    human_event_member_sha256, review_payload_sha256,
    decision_review_set_sha256, reviewer_independence_set_sha256,
    evidence_locator, independence_evidence_locator
)
SELECT 'round3m.normalization.contract.wrong-binding.attestation.' ||
           fixture.suffix,
       review.professional_label_review_id, fixture.actor_type,
       'DOCUMENTED_HUMAN_EVENT', reviewer.reviewer_key,
       identity.reviewer_identity_receipt_key,
       fixture.human_event_sha256,
       audit.round3m_human_review_event_member_sha256(
           review.professional_label_review_id,
           fixture.human_event_sha256
       ),
       audit.round3m_professional_label_review_payload_sha256(
           review.professional_label_review_id
       ),
       audit.round3m_professional_label_review_set_sha256(
           decision.professional_label_decision_id
       ),
       audit.round3m_professional_reviewer_independence_set_sha256(
           decision.professional_label_decision_id
       ),
       'fixture://round3m-normalization/wrong-binding-review/' ||
           fixture.suffix,
       'fixture://round3m-normalization/wrong-binding-independence/' ||
           fixture.suffix
FROM (VALUES
    (
        'independent-1',
        'round3m.normalization.contract.reviewer.independent-1',
        'HUMAN_REVIEWER', repeat('7', 64)
    ),
    (
        'independent-2',
        'round3m.normalization.contract.reviewer.independent-2',
        'HUMAN_REVIEWER', repeat('8', 64)
    ),
    (
        'adjudicator',
        'round3m.normalization.contract.reviewer.adjudicator',
        'EXPERT_REVIEWER', repeat('9', 64)
    )
) AS fixture(suffix, reviewer_key, actor_type, human_event_sha256)
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_key = fixture.reviewer_key
JOIN audit.round3m_human_reviewer_identity_receipt AS identity
  ON identity.reviewer_id = reviewer.reviewer_id
JOIN audit.professional_label_review AS review
  ON review.reviewer_id = reviewer.reviewer_id
JOIN corpus.professional_label_decision AS decision
  ON decision.professional_label_decision_id =
     review.professional_label_decision_id
 AND decision.professional_label_decision_key =
     'round3m.normalization.contract.wrong-binding.label.final';

SET CONSTRAINTS ALL IMMEDIATE;

DO $wrong_round3m_round3k_file_binding_adds_zero$
DECLARE
    baseline_count BIGINT;
    current_count BIGINT;
    fixture_universe_count BIGINT;
    exact_binding_count BIGINT;
BEGIN
    SELECT challenge_count INTO STRICT baseline_count
    FROM round3m_normalization_challenge_baseline;

    SELECT reviewed_ambiguous_or_unresolved_challenge_count
    INTO STRICT current_count
    FROM audit.v_round3m_descriptor_gate_metrics;

    SELECT count(*) INTO STRICT fixture_universe_count
    FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
    WHERE descriptor_assertion_key =
          'round3m.normalization.contract.wrong-binding.assertion';

    SELECT count(*) INTO STRICT exact_binding_count
    FROM corpus.v_round3m_round3k_exact_descriptor_source_binding AS binding
    JOIN corpus.round3m_descriptor_assertion AS assertion
      ON assertion.descriptor_assertion_id = binding.descriptor_assertion_id
    WHERE assertion.descriptor_assertion_key =
          'round3m.normalization.contract.wrong-binding.assertion';

    IF current_count IS DISTINCT FROM baseline_count + 1
       OR fixture_universe_count <> 0
       OR exact_binding_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_NORMALIZATION_CHALLENGE=wrong_file_binding expected metric delta 0, universe 0, exact binding 0; baseline=% current=% universe=% binding=%',
            baseline_count, current_count, fixture_universe_count,
            exact_binding_count;
    END IF;

    RAISE NOTICE
        'ROUND3M_NEGATIVE=wrong_Round3M_Round3K_file_hash_binding_adds_zero PASS';
END
$wrong_round3m_round3k_file_binding_adds_zero$;

-- Build a transaction-local qualified successor and prove that the
-- attestation trigger rejects non-ACCEPT outcomes, digest substitution, and
-- future chronology.  Each expected exception rolls the whole fixture back.
SET CONSTRAINTS ALL DEFERRED;

CREATE FUNCTION pg_temp.assert_round3m_attestation_rejected(
    case_key TEXT,
    selected_outcome TEXT,
    selected_review_offset INTERVAL,
    selected_decision_offset INTERVAL,
    selected_receipt_offset INTERVAL,
    corrupt_review_set BOOLEAN,
    corrupt_independence_set BOOLEAN
)
RETURNS VOID
LANGUAGE plpgsql
AS $assert_round3m_attestation_rejected$
DECLARE
    rejected_constraint TEXT;
BEGIN
    BEGIN
        INSERT INTO corpus.professional_label_decision (
            professional_label_decision_key, professional_expression_id,
            decision_version, supersedes_decision_id,
            label_disposition_code, decision_method_code,
            independent_qualified_reviewer_count, adjudicator_present,
            expert_review_complete, candidate_only, decision_status_code,
            provenance_complete, decision_basis, decided_at
        )
        SELECT 'round3m.normalization.contract.negative.' || case_key ||
                   '.decision',
               predecessor.professional_expression_id, 2,
               predecessor.professional_label_decision_id,
               'UNRESOLVED', 'QUALIFIED_REVIEW', 2, TRUE, TRUE, FALSE,
               'FINAL', TRUE,
               'Expected attestation rejection for ' || case_key || '.',
               transaction_timestamp() + selected_decision_offset
        FROM corpus.professional_label_decision AS predecessor
        WHERE predecessor.professional_label_decision_key =
              'round3m.normalization.contract.label.unresolved.final';

        INSERT INTO audit.professional_label_review (
            professional_label_decision_id, reviewer_id,
            reviewer_role_code, review_outcome_code, review_evidence,
            reviewed_at
        )
        SELECT decision.professional_label_decision_id,
               reviewer.reviewer_id, fixture.role_code,
               CASE
                   WHEN fixture.suffix = 'independent-1'
                       THEN selected_outcome
                   ELSE 'ACCEPT'
               END,
               'Expected attestation rejection review for ' || case_key ||
                   ' / ' || fixture.suffix || '.',
               CASE
                   WHEN fixture.suffix = 'independent-1'
                       THEN transaction_timestamp() +
                            selected_review_offset
                   ELSE transaction_timestamp() - interval '2 hours'
               END
        FROM (VALUES
            (
                'independent-1',
                'round3m.normalization.contract.reviewer.independent-1',
                'INDEPENDENT_REVIEWER'
            ),
            (
                'independent-2',
                'round3m.normalization.contract.reviewer.independent-2',
                'INDEPENDENT_REVIEWER'
            ),
            (
                'adjudicator',
                'round3m.normalization.contract.reviewer.adjudicator',
                'ADJUDICATOR'
            )
        ) AS fixture(suffix, reviewer_key, role_code)
        CROSS JOIN corpus.professional_label_decision AS decision
        JOIN audit.reviewer AS reviewer
          ON reviewer.reviewer_key = fixture.reviewer_key
        WHERE decision.professional_label_decision_key =
              'round3m.normalization.contract.negative.' || case_key ||
              '.decision';

        INSERT INTO audit.round3m_professional_label_review_attestation (
            attestation_key, professional_label_review_id,
            review_actor_type, receipt_origin_code,
            reviewer_id_or_pseudonymous_code,
            reviewer_identity_receipt_key,
            human_event_evidence_sha256, human_event_member_sha256,
            review_payload_sha256,
            decision_review_set_sha256,
            reviewer_independence_set_sha256, evidence_locator,
            independence_evidence_locator, created_at
        )
        SELECT 'round3m.normalization.contract.negative.' || case_key ||
                   '.attestation',
               review.professional_label_review_id, 'HUMAN_REVIEWER',
               'DOCUMENTED_HUMAN_EVENT', reviewer.reviewer_key,
               identity.reviewer_identity_receipt_key,
               audit.round3i_utf8_sha256('negative-event-' || case_key),
               audit.round3m_human_review_event_member_sha256(
                   review.professional_label_review_id,
                   audit.round3i_utf8_sha256(
                       'negative-event-' || case_key
                   )
               ),
               audit.round3m_professional_label_review_payload_sha256(
                   review.professional_label_review_id
               ),
               CASE
                   WHEN corrupt_review_set THEN repeat('a', 64)
                   ELSE audit.round3m_professional_label_review_set_sha256(
                       decision.professional_label_decision_id
                   )
               END,
               CASE
                   WHEN corrupt_independence_set THEN repeat('b', 64)
                   ELSE audit.round3m_professional_reviewer_independence_set_sha256(
                       decision.professional_label_decision_id
                   )
               END,
               'fixture://round3m-normalization/negative/' || case_key,
               'fixture://round3m-normalization/negative-independence/' ||
                   case_key,
               transaction_timestamp() + selected_receipt_offset
        FROM audit.professional_label_review AS review
        JOIN audit.reviewer AS reviewer
          ON reviewer.reviewer_id = review.reviewer_id
        JOIN audit.round3m_human_reviewer_identity_receipt AS identity
          ON identity.reviewer_id = reviewer.reviewer_id
        JOIN corpus.professional_label_decision AS decision
          ON decision.professional_label_decision_id =
             review.professional_label_decision_id
        WHERE decision.professional_label_decision_key =
              'round3m.normalization.contract.negative.' || case_key ||
              '.decision'
          AND reviewer.reviewer_key =
              'round3m.normalization.contract.reviewer.independent-1';

        RAISE EXCEPTION USING
            ERRCODE = 'P0001',
            MESSAGE = 'expected 059 attestation rejection was not raised: ' ||
                      case_key;
    EXCEPTION
        WHEN check_violation THEN
            GET STACKED DIAGNOSTICS
                rejected_constraint = CONSTRAINT_NAME;
            IF rejected_constraint IS DISTINCT FROM
               'round3m_prof_label_review_human_attestation_ck' THEN
                RAISE;
            END IF;
    END;

    RAISE NOTICE 'ROUND3M_NEGATIVE=%_attestation_rejected PASS', case_key;
END
$assert_round3m_attestation_rejected$;

SELECT pg_temp.assert_round3m_attestation_rejected(
    'outcome_abstain', 'ABSTAIN', interval '-2 hours', interval '0',
    interval '0', FALSE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'outcome_revise', 'REVISE', interval '-2 hours', interval '0',
    interval '0', FALSE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'outcome_reject', 'REJECT', interval '-2 hours', interval '0',
    interval '0', FALSE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'outcome_conflict', 'CONFLICT', interval '-2 hours', interval '0',
    interval '0', FALSE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'review_set_digest_mismatch', 'ACCEPT', interval '-2 hours',
    interval '0', interval '0', TRUE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'independence_digest_mismatch', 'ACCEPT', interval '-2 hours',
    interval '0', interval '0', FALSE, TRUE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'future_review', 'ACCEPT', interval '1 minute', interval '0',
    interval '0', FALSE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'future_decision', 'ACCEPT', interval '-2 hours', interval '1 minute',
    interval '0', FALSE, FALSE
);
SELECT pg_temp.assert_round3m_attestation_rejected(
    'future_receipt', 'ACCEPT', interval '-2 hours', interval '0',
    interval '1 minute', FALSE, FALSE
);

-- The corrected per-kind target uniqueness permits two distinct concept
-- targets.  Two current roots are representable/countable, while replacing
-- the additional root with a real frozen-ontology candidate is not.
DO $current_and_candidate_target_sets$
DECLARE
    primary_concept_id BIGINT;
    additional_concept_id BIGINT;
    candidate_concept_id BIGINT;
    selected_decision_id BIGINT;
BEGIN
    SELECT concept_id INTO STRICT primary_concept_id
    FROM kb.concept
    WHERE lifecycle_status_code = 'active'
      AND replacement_concept_id IS NULL
    ORDER BY concept_id
    LIMIT 1;

    SELECT concept_id INTO STRICT additional_concept_id
    FROM kb.concept
    WHERE lifecycle_status_code = 'active'
      AND replacement_concept_id IS NULL
      AND concept_id <> primary_concept_id
    ORDER BY concept_id
    LIMIT 1;

    SELECT concept_id INTO STRICT candidate_concept_id
    FROM kb.concept
    WHERE lifecycle_status_code = 'candidate'
      AND replacement_concept_id IS NULL
    ORDER BY concept_id
    LIMIT 1;

    BEGIN
        INSERT INTO corpus.professional_label_decision (
            professional_label_decision_key,
            professional_expression_id, decision_version,
            supersedes_decision_id, label_disposition_code,
            decision_method_code,
            independent_qualified_reviewer_count,
            adjudicator_present, expert_review_complete,
            candidate_only, decision_status_code,
            provenance_complete, decision_basis, decided_at
        )
        SELECT 'round3m.normalization.contract.target-positive.active-roots',
               predecessor.professional_expression_id, 2,
               predecessor.professional_label_decision_id,
               'AMBIGUOUS_TARGET', 'QUALIFIED_REVIEW', 2,
               TRUE, TRUE, FALSE, 'FINAL', TRUE,
               'Two distinct current-root target representability control.',
               transaction_timestamp()
        FROM corpus.professional_label_decision AS predecessor
        WHERE predecessor.professional_label_decision_key =
              'round3m.normalization.contract.label.unresolved.final'
        RETURNING professional_label_decision_id
        INTO STRICT selected_decision_id;

        INSERT INTO corpus.professional_label_target (
            professional_label_decision_id, target_ordinal,
            concept_id, association_range_id, target_role_code
        ) VALUES
            (
                selected_decision_id, 1, primary_concept_id, NULL,
                'PRIMARY'
            ),
            (
                selected_decision_id, 2, additional_concept_id, NULL,
                'ADDITIONAL'
            );

        IF audit.round3m_professional_label_target_set_is_countable(
            selected_decision_id
        ) IS DISTINCT FROM TRUE THEN
            RAISE EXCEPTION
                'ROUND3M_NORMALIZATION_CHALLENGE=two active concept targets are not representable/countable';
        END IF;

        RAISE NOTICE
            'ROUND3M_POSITIVE=two_distinct_active_concept_targets_representable_and_countable PASS';
        RAISE EXCEPTION USING
            ERRCODE = 'ZX201',
            MESSAGE = 'rollback active target representability fixture';
    EXCEPTION
        WHEN SQLSTATE 'ZX201' THEN NULL;
    END;

    BEGIN
        INSERT INTO corpus.professional_label_decision (
            professional_label_decision_key,
            professional_expression_id, decision_version,
            supersedes_decision_id, label_disposition_code,
            decision_method_code,
            independent_qualified_reviewer_count,
            adjudicator_present, expert_review_complete,
            candidate_only, decision_status_code,
            provenance_complete, decision_basis, decided_at
        )
        SELECT 'round3m.normalization.contract.target-negative.candidate',
               predecessor.professional_expression_id, 2,
               predecessor.professional_label_decision_id,
               'AMBIGUOUS_TARGET', 'QUALIFIED_REVIEW', 2,
               TRUE, TRUE, FALSE, 'FINAL', TRUE,
               'Frozen-ontology candidate target exclusion control.',
               transaction_timestamp()
        FROM corpus.professional_label_decision AS predecessor
        WHERE predecessor.professional_label_decision_key =
              'round3m.normalization.contract.label.unresolved.final'
        RETURNING professional_label_decision_id
        INTO STRICT selected_decision_id;

        INSERT INTO corpus.professional_label_target (
            professional_label_decision_id, target_ordinal,
            concept_id, association_range_id, target_role_code
        ) VALUES
            (
                selected_decision_id, 1, primary_concept_id, NULL,
                'PRIMARY'
            ),
            (
                selected_decision_id, 2, candidate_concept_id, NULL,
                'ADDITIONAL'
            );

        IF audit.round3m_professional_label_target_set_is_countable(
            selected_decision_id
        ) IS DISTINCT FROM FALSE THEN
            RAISE EXCEPTION
                'ROUND3M_NORMALIZATION_CHALLENGE=candidate target unexpectedly countable';
        END IF;

        RAISE NOTICE 'ROUND3M_NEGATIVE=candidate_target_excluded PASS';
        RAISE EXCEPTION USING
            ERRCODE = 'ZX202',
            MESSAGE = 'rollback candidate target exclusion fixture';
    EXCEPTION
        WHEN SQLSTATE 'ZX202' THEN NULL;
    END;
END
$current_and_candidate_target_sets$;

-- Direct mutation controls for the bidirectional decision chain, reverse
-- Round 3K source protections, and released v2 gate surface.
CREATE FUNCTION pg_temp.assert_round3m_check_rejected(
    case_key TEXT,
    command_text TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $assert_round3m_check_rejected$
DECLARE
    rejected_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE command_text;
        RAISE EXCEPTION USING
            ERRCODE = 'P0001',
            MESSAGE = 'expected 059 mutation rejection was not raised: ' ||
                      case_key;
    EXCEPTION
        WHEN check_violation THEN
            GET STACKED DIAGNOSTICS
                rejected_constraint = CONSTRAINT_NAME;
            IF rejected_constraint IS DISTINCT FROM expected_constraint THEN
                RAISE;
            END IF;
    END;

    RAISE NOTICE 'ROUND3M_NEGATIVE=%_rejected PASS', case_key;
END
$assert_round3m_check_rejected$;

SELECT pg_temp.assert_round3m_check_rejected(
    'unattested_ancestor_update_with_attested_successor',
    $sql$
        UPDATE corpus.professional_label_decision
        SET decision_basis = decision_basis || ' blocked mutation'
        WHERE professional_label_decision_key =
              'round3m.normalization.contract.wrong-binding.label.candidate'
    $sql$,
    'round3m_superseded_prof_label_decision_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'unattested_ancestor_delete_with_attested_successor',
    $sql$
        DELETE FROM corpus.professional_label_decision
        WHERE professional_label_decision_key =
              'round3m.normalization.contract.wrong-binding.label.candidate'
    $sql$,
    'round3m_superseded_prof_label_decision_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'attested_successor_update',
    $sql$
        UPDATE corpus.professional_label_decision
        SET decision_basis = decision_basis || ' blocked mutation'
        WHERE professional_label_decision_key =
              'round3m.normalization.contract.wrong-binding.label.final'
    $sql$,
    'round3m_attested_prof_label_decision_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'attested_successor_delete',
    $sql$
        DELETE FROM corpus.professional_label_decision
        WHERE professional_label_decision_key =
              'round3m.normalization.contract.wrong-binding.label.final'
    $sql$,
    'round3m_attested_prof_label_decision_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'attested_successor_repoint',
    $sql$
        UPDATE corpus.professional_label_decision
        SET supersedes_decision_id = NULL
        WHERE professional_label_decision_key =
              'round3m.normalization.contract.wrong-binding.label.final'
    $sql$,
    'round3m_attested_prof_label_decision_immutable_ck'
);

SELECT pg_temp.assert_round3m_check_rejected(
    'reverse_competition_descriptor_source_update',
    $sql$
        UPDATE competition.descriptor_assertion
        SET source_locator = source_locator || '#blocked'
        WHERE descriptor_assertion_key =
              'round3m.normalization.contract.competition-assertion'
    $sql$,
    'round3m_attested_descriptor_source_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'reverse_competition_descriptor_source_delete',
    $sql$
        DELETE FROM competition.descriptor_assertion
        WHERE descriptor_assertion_key =
              'round3m.normalization.contract.competition-assertion'
    $sql$,
    'round3m_attested_descriptor_source_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'reverse_professional_source_file_update',
    $sql$
        UPDATE evidence.professional_source_file
        SET filename = filename || '.blocked'
        WHERE professional_source_file_key =
              'round3m.normalization.contract.round3k-file'
    $sql$,
    'round3m_attested_source_identity_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'reverse_professional_source_snapshot_update',
    $sql$
        UPDATE evidence.professional_source_snapshot
        SET exact_version = exact_version || '-blocked'
        WHERE professional_source_snapshot_key =
              'round3m.normalization.contract.round3k-snapshot'
    $sql$,
    'round3m_attested_source_identity_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'reverse_professional_rights_update',
    $sql$
        UPDATE evidence.professional_rights_decision
        SET evidence_basis = evidence_basis || ' Blocked mutation.'
        WHERE professional_rights_decision_key =
              'round3m.normalization.contract.round3k-rights'
    $sql$,
    'round3m_attested_source_identity_immutable_ck'
);

SELECT pg_temp.assert_round3m_check_rejected(
    'released_v2_gate_definition_insert',
    $sql$
        INSERT INTO audit.round3m_descriptor_gate_definition (
            gate_version, gate_name, gate_order, gate_purpose,
            default_universe, authorizes_training, active,
            explanatory_note
        )
        SELECT gate_version, 'GATE_LATE_INSERT_CONTROL', 99,
               'Released-contract insert rejection control.',
               default_universe, FALSE, TRUE,
               'This row must never enter a released contract.'
        FROM audit.round3m_descriptor_gate_definition
        WHERE gate_version = 'round3m-descriptor-gates-v2'
        ORDER BY gate_order
        LIMIT 1
    $sql$,
    'round3m_released_gate_contract_immutable_ck'
);
SELECT pg_temp.assert_round3m_check_rejected(
    'released_v2_gate_criterion_insert',
    $sql$
        INSERT INTO audit.round3m_descriptor_gate_criterion (
            gate_version, gate_name, criterion_ordinal, metric_name,
            operator, required_numeric, required_boolean, required_value,
            universe, blocker_class, explanatory_note
        )
        SELECT gate_version, gate_name, 99, 'LATE_INSERT_CONTROL',
               '>=', 1, NULL, '1', universe, 'DATA',
               'This row must never enter a released contract.'
        FROM audit.round3m_descriptor_gate_criterion
        WHERE gate_version = 'round3m-descriptor-gates-v2'
        ORDER BY gate_name, criterion_ordinal
        LIMIT 1
    $sql$,
    'round3m_released_gate_contract_immutable_ck'
);

SET CONSTRAINTS ALL IMMEDIATE;

CREATE TEMP TABLE round3m_current_gate_validation
ON COMMIT DROP
AS
SELECT *
FROM audit.run_round3m_gate_validation_queries();

CREATE TEMP TABLE round3m_pre_v059_gate_validation
ON COMMIT DROP
AS
SELECT *
FROM audit.run_round3m_gate_validation_queries_pre_v059();

DO $normalization_challenge_validation_contract$
DECLARE
    expected_new_check_keys TEXT[] := ARRAY[
        'round3m.competition_descriptor_assertion_link_is_unique',
        'round3m.current_descriptor_gate_release_is_exact_v2',
        'round3m.descriptor_gate_release_payloads_are_exact',
        'round3m.descriptor_gate_release_shapes_are_exact',
        'round3m.descriptor_gate_status_is_exact_v2_surface',
        'round3m.descriptor_gate_summary_is_exact_v2_surface',
        'round3m.descriptor_gate_v2_criterion_parity_is_55_plus_1',
        'round3m.descriptor_gate_v2_definition_parity_is_6_plus_1_nontraining',
        'round3m.exact_source_binding_identity_is_unique',
        'round3m.normalization_challenge_criterion_universe_is_exact',
        'round3m.normalization_challenge_exact_source_binding_is_unique',
        'round3m.normalization_challenge_metric_matches_governed_universe',
        'round3m.normalization_challenge_target_set_is_countable',
        'round3m.professional_label_attestation_human_identity_is_exact',
        'round3m.professional_label_attestation_identity_outcome_chronology_is_exact',
        'round3m.professional_label_attestation_payload_is_exact',
        'round3m.professional_label_attestation_sets_are_exact',
        'round3m.professional_label_attested_lineage_is_valid',
        'round3m.professional_label_attested_parent_marker_is_exact'
    ];
    actual_new_check_keys TEXT[];
    actual_new_check_row_count BIGINT;
    passing_new_check_count BIGINT;
    failure_count BIGINT;
    failed_check RECORD;
BEGIN
    SELECT coalesce(array_agg(check_key ORDER BY check_key), ARRAY[]::TEXT[])
    INTO STRICT actual_new_check_keys
    FROM (
        SELECT check_key
        FROM round3m_current_gate_validation
        EXCEPT
        SELECT check_key
        FROM round3m_pre_v059_gate_validation
    ) AS current_only;

    SELECT count(*) INTO STRICT actual_new_check_row_count
    FROM round3m_current_gate_validation AS current_check
    WHERE NOT EXISTS (
        SELECT 1
        FROM round3m_pre_v059_gate_validation AS prior
        WHERE prior.check_key = current_check.check_key
    );

    SELECT count(*) INTO passing_new_check_count
    FROM round3m_current_gate_validation
    WHERE check_key = ANY(expected_new_check_keys)
      AND passed
      AND violation_count = 0;

    SELECT count(*) INTO failure_count
    FROM round3m_current_gate_validation
    WHERE passed IS NOT TRUE OR violation_count <> 0;

    FOR failed_check IN
        SELECT check_key, violation_count
        FROM round3m_current_gate_validation
        WHERE passed IS NOT TRUE OR violation_count <> 0
        ORDER BY check_key
    LOOP
        RAISE NOTICE
            'ROUND3M_NORMALIZATION_CHALLENGE_VALIDATION_FAILURE=% violations=%',
            failed_check.check_key, failed_check.violation_count;
    END LOOP;

    IF actual_new_check_keys IS DISTINCT FROM expected_new_check_keys
       OR actual_new_check_row_count <> cardinality(expected_new_check_keys)
       OR passing_new_check_count <> cardinality(expected_new_check_keys)
       OR failure_count <> 0 THEN
        RAISE EXCEPTION
            'ROUND3M_NORMALIZATION_CHALLENGE=validation expected_keys=% actual_keys=% actual_rows=% passing=% failures=%',
            expected_new_check_keys, actual_new_check_keys,
            actual_new_check_row_count, passing_new_check_count,
            failure_count;
    END IF;

    RAISE NOTICE
        'ROUND3M_CONSTRAINT=normalization_challenge_validation_contract PASS';
END
$normalization_challenge_validation_contract$;

ROLLBACK;
