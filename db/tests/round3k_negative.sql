\set ON_ERROR_STOP on
\pset pager off

-- Integrated Round 3K source, evidence, mapping, integrity, and no-training
-- failure paths.  Every fixture and attempted mutation is transaction-local.

BEGIN;

CREATE FUNCTION pg_temp.expect_round3k_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3k_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        SET CONSTRAINTS ALL IMMEDIATE;
        RAISE EXCEPTION
            'Round 3K negative statement unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND3K_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3k_failure$;

CREATE FUNCTION pg_temp.expect_round3k_gate_count(
    test_key TEXT,
    statement_text TEXT,
    expected_count BIGINT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3k_gate_count$
DECLARE
    actual_count BIGINT;
BEGIN
    EXECUTE statement_text INTO STRICT actual_count;
    IF actual_count IS DISTINCT FROM expected_count THEN
        RAISE EXCEPTION
            'Round 3K gate assertion % expected %, received %',
            test_key, expected_count, actual_count;
    END IF;
    RAISE NOTICE 'ROUND3K_GATE=% COUNT=% PASS', test_key, actual_count;
END;
$expect_round3k_gate_count$;

-- Competition-native fixture grain.
INSERT INTO competition.series (
    series_key, official_name, organizer_name, series_scope_code,
    lifecycle_status_code
) VALUES (
    'negative.round3k.integrated.series',
    'Round 3K integrated negative series',
    'Round 3K transaction fixture organizer', 'GLOBAL', 'active'
);

INSERT INTO competition.edition (
    edition_key, series_id, series_local_edition_key, edition_name,
    edition_year, lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.edition.2026', series_id, '2026',
    'Round 3K integrated negative edition 2026', 2026, 'active'
FROM competition.series
WHERE series_key = 'negative.round3k.integrated.series';

INSERT INTO competition.rule_version (
    rule_version_key, series_id, rule_family_key, version_number,
    publication_status_code, official_version_label, official_locator,
    lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.rules.v1', series_id,
    'negative.round3k.integrated.rules', 1, 'VERSIONED',
    'Round 3K transaction fixture rules v1',
    'db/tests/round3k_negative.sql#rules', 'active'
FROM competition.series
WHERE series_key = 'negative.round3k.integrated.series';

INSERT INTO competition.category (
    category_key, category_identity_key, identity_version, series_id,
    edition_id, rule_version_id, source_category_code, category_name,
    category_kind_code, lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.category.open.v1',
    'negative.round3k.integrated.category.open', 1,
    series.series_id, edition.edition_id, rule_version.rule_version_id,
    'OPEN', 'Round 3K transaction fixture open category',
    'SERVICE_CLASS', 'active'
FROM competition.series AS series
JOIN competition.edition AS edition
  ON edition.series_id = series.series_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = series.series_id
WHERE series.series_key = 'negative.round3k.integrated.series'
  AND edition.edition_key = 'negative.round3k.integrated.edition.2026'
  AND rule_version.rule_version_key =
      'negative.round3k.integrated.rules.v1';

INSERT INTO competition.round (
    round_key, round_identity_key, identity_version, series_id, edition_id,
    rule_version_id, source_round_code, round_name, round_kind_code,
    sequence_number, lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.round.final.v1',
    'negative.round3k.integrated.round.final', 1,
    category.series_id, category.edition_id, category.rule_version_id,
    'FINAL', 'Round 3K transaction fixture final', 'FINAL', 1, 'active'
FROM competition.category AS category
WHERE category.category_key =
      'negative.round3k.integrated.category.open.v1';

INSERT INTO competition.entry (
    entry_key, entry_identity_key, identity_version, series_id, edition_id,
    category_id, source_entry_identifier, entry_kind_code,
    lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.entry.' || seed.entry_suffix || '.v1',
    'negative.round3k.integrated.entry.' || seed.entry_suffix,
    1, category.series_id, category.edition_id, category.category_id,
    'ENTRY-' || seed.source_suffix, 'COMPETITOR_ENTRY', 'active'
FROM competition.category AS category
CROSS JOIN (VALUES
    ('core', 'CORE'),
    ('p3', 'P3'),
    ('p4', 'P4'),
    ('no_protocol', 'NO-PROTOCOL')
) AS seed(entry_suffix, source_suffix)
WHERE category.category_key =
      'negative.round3k.integrated.category.open.v1';

INSERT INTO competition.coffee_identity (
    coffee_identity_key, coffee_identity_group_key, identity_version,
    identity_kind_code, source_native_coffee_identifier,
    lifecycle_status_code
) VALUES (
    'negative.round3k.integrated.coffee.v1',
    'negative.round3k.integrated.coffee', 1,
    'SOURCE_DECLARED', 'COFFEE-ROUND3K-NEGATIVE', 'active'
);

INSERT INTO competition.lot (
    lot_key, lot_identity_key, identity_version, series_id, edition_id,
    category_id, coffee_identity_id, source_lot_identifier, lot_kind_code,
    lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.lot.v1',
    'negative.round3k.integrated.lot', 1,
    category.series_id, category.edition_id, category.category_id,
    coffee.coffee_identity_id, 'LOT-ROUND3K-NEGATIVE',
    'COMPETITION_LOT', 'active'
FROM competition.category AS category
CROSS JOIN competition.coffee_identity AS coffee
WHERE category.category_key =
      'negative.round3k.integrated.category.open.v1'
  AND coffee.coffee_identity_key =
      'negative.round3k.integrated.coffee.v1';

INSERT INTO competition.entry_coffee_link (
    entry_coffee_link_key, series_id, edition_id, category_id, entry_id,
    coffee_identity_id, lot_id, link_role_code, linkage_status_code
)
SELECT
    replace(entry.entry_key, '.v1', '.coffee.primary'),
    entry.series_id, entry.edition_id, entry.category_id, entry.entry_id,
    lot.coffee_identity_id, lot.lot_id, 'PRIMARY', 'SOURCE_DECLARED'
FROM competition.entry AS entry
JOIN competition.lot AS lot
  ON lot.series_id = entry.series_id
 AND lot.edition_id = entry.edition_id
 AND lot.category_id = entry.category_id
WHERE entry.entry_identity_key LIKE
      'negative.round3k.integrated.entry.%'
  AND lot.lot_key = 'negative.round3k.integrated.lot.v1';

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
SELECT
    'negative.round3k.integrated.service.' || seed.service_suffix,
    entry.series_id, entry.edition_id, entry.category_id,
    round_record.round_id, entry.entry_id,
    'negative.round3k.integrated.entry_service.' || seed.service_suffix,
    rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
    'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'REPORTED',
    preparation.preparation_concept_id, 'OFFICIAL_PROTOCOL',
    'NOT_REPORTED', 'NOT_REPORTED', 'active'
FROM (VALUES
    ('core', 'core'),
    ('p3', 'p3'),
    ('p4', 'p4'),
    ('no_protocol', 'no_protocol')
) AS seed(entry_suffix, service_suffix)
JOIN competition.entry AS entry
  ON entry.entry_identity_key =
     'negative.round3k.integrated.entry.' || seed.entry_suffix
JOIN competition.round AS round_record
  ON round_record.series_id = entry.series_id
 AND round_record.edition_id = entry.edition_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = entry.series_id
CROSS JOIN context.preparation_concept AS preparation
WHERE round_record.round_key =
      'negative.round3k.integrated.round.final.v1'
  AND rule_version.rule_version_key =
      'negative.round3k.integrated.rules.v1'
  AND preparation.preparation_concept_key =
      'preparation.family.filter_percolation';

-- Three independent source snapshots isolate denied, pending, and affirmative
-- model-research rights.  Public visibility is deliberately identical.
INSERT INTO evidence.source_family (
    source_family_key, family_name, family_type, canonical_origin_key,
    counts_as_independent, mirror_of_source_family_key, independence_basis,
    admitted, introduced_round
)
SELECT
    'negative.round3k.integrated.source_family.' || suffix,
    'Round 3K transaction source family ' || upper(suffix),
    'PROFESSIONAL_COMPETITION',
    'negative.round3k.integrated.origin.' || suffix,
    TRUE, NULL, 'Independent transaction fixture ' || upper(suffix),
    TRUE, '3K'
FROM (VALUES ('a'), ('b'), ('c')) AS seed(suffix);

INSERT INTO evidence.professional_source (
    professional_source_key, source_family_key, title, official_owner,
    canonical_url, source_type_code, evidence_tier_scope,
    access_state_code, automation_permission_state_code, data_custodian,
    independence_basis, admitted
)
SELECT
    'negative.round3k.integrated.source.' || suffix,
    'negative.round3k.integrated.source_family.' || suffix,
    'Round 3K transaction official results ' || upper(suffix),
    'Round 3K fixture organizer ' || upper(suffix),
    'https://example.invalid/round3k/' || suffix,
    'OFFICIAL_JSON_API', ARRAY['P0', 'P1', 'P2', 'P3', 'P4']::TEXT[],
    'PUBLIC', 'PERMITTED', 'Round 3K fixture custodian',
    'Direct official transaction fixture', TRUE
FROM (VALUES ('a'), ('b'), ('c')) AS seed(suffix);

INSERT INTO evidence.professional_source_series (
    professional_source_id, series_id, source_role_code
)
SELECT source.professional_source_id, series.series_id, 'PRIMARY_RESULTS'
FROM evidence.professional_source AS source
CROSS JOIN competition.series AS series
WHERE source.professional_source_key LIKE
      'negative.round3k.integrated.source._'
  AND series.series_key = 'negative.round3k.integrated.series';

INSERT INTO evidence.professional_source_snapshot (
    professional_source_snapshot_key, professional_source_id,
    source_family_key, exact_version, retrieved_at, immutable_locator,
    snapshot_sha256, access_method_code,
    automated_access_compliance_code,
    lawfully_acquired_for_internal_research, source_record_count, admitted
)
SELECT
    'negative.round3k.integrated.snapshot.' || seed.suffix,
    source.professional_source_id, source.source_family_key,
    'fixture-v1-' || seed.suffix, CURRENT_TIMESTAMP,
    'https://example.invalid/round3k/' || seed.suffix || '#v1',
    repeat(seed.hash_character, 64), 'PERMITTED_HTTP', 'PERMITTED',
    TRUE, 4, TRUE
FROM (VALUES ('a', 'a'), ('b', 'b'), ('c', 'c'))
    AS seed(suffix, hash_character)
JOIN evidence.professional_source AS source
  ON source.professional_source_key =
     'negative.round3k.integrated.source.' || seed.suffix;

INSERT INTO evidence.professional_source_file (
    professional_source_file_key, professional_source_snapshot_id,
    filename, file_role_code, official_locator, local_path,
    declared_sha256, verified_sha256, file_size_bytes, row_count,
    field_count, hash_verified, retention_state_code,
    public_redistribution_allowed, source_owner, source_url,
    license_or_terms, attribution_requirement, modification_status
)
SELECT
    'negative.round3k.integrated.file.' || seed.suffix,
    snapshot.professional_source_snapshot_id,
    'round3k-' || seed.suffix || '.json', 'RAW_OFFICIAL',
    snapshot.immutable_locator, NULL, repeat(seed.hash_character, 64),
    repeat(seed.hash_character, 64), 1024, 4, 8, TRUE,
    'HASH_AND_LOCATOR_ONLY', FALSE,
    'Round 3K fixture organizer ' || upper(seed.suffix),
    snapshot.immutable_locator, 'Internal research fixture only',
    'Retain source owner and locator', 'Unmodified transaction fixture'
FROM (VALUES ('a', 'a'), ('b', 'b'), ('c', 'c'))
    AS seed(suffix, hash_character)
JOIN evidence.professional_source_snapshot AS snapshot
  ON snapshot.professional_source_snapshot_key =
     'negative.round3k.integrated.snapshot.' || seed.suffix;

INSERT INTO evidence.professional_rights_decision (
    professional_rights_decision_key, professional_source_snapshot_id,
    public_results_use, public_descriptor_use, internal_research_use,
    public_derived_release, model_research_use, commercial_model_use,
    decision_authority_code, evidence_basis, decided_on
)
SELECT
    'negative.round3k.integrated.rights.' || seed.suffix,
    snapshot.professional_source_snapshot_id,
    'ALLOWED', 'ALLOWED', 'ALLOWED', seed.public_derived_release,
    seed.model_research_use, 'DENIED', 'PROJECT_RIGHTS_REVIEW',
    seed.evidence_basis, CURRENT_DATE
FROM (VALUES
    ('a', 'DENIED',  'PENDING', 'Public results do not grant model use'),
    ('b', 'PENDING', 'PENDING', 'Model research rights remain pending'),
    ('c', 'ALLOWED', 'ALLOWED', 'Affirmative internal model research fixture')
) AS seed(
    suffix, model_research_use, public_derived_release, evidence_basis
)
JOIN evidence.professional_source_snapshot AS snapshot
  ON snapshot.professional_source_snapshot_key =
     'negative.round3k.integrated.snapshot.' || seed.suffix;

INSERT INTO evidence.professional_privacy_decision (
    professional_privacy_decision_key,
    professional_source_snapshot_id, personal_data_scope_code,
    direct_identifiers_retained, judge_identity_treatment_code,
    processing_basis, decision_state_code, decided_on
)
SELECT
    'negative.round3k.integrated.privacy.c',
    professional_source_snapshot_id, 'NONE', FALSE, 'NOT_PRESENT',
    'Transaction fixture contains no direct personal identifiers',
    'ALLOWED', CURRENT_DATE
FROM evidence.professional_source_snapshot
WHERE professional_source_snapshot_key =
      'negative.round3k.integrated.snapshot.c';

-- Core service links all rights states for isolated rights-gate tests.  The
-- auxiliary P3/P4 services use only the affirmative snapshot.  The final
-- service intentionally lacks a PREPARATION_PROTOCOL row for the 052 gate.
INSERT INTO competition.preparation_service_evidence (
    preparation_service_evidence_key, preparation_service_id,
    professional_source_snapshot_id, professional_source_file_id,
    evidence_role_code, source_locator,
    explicit_fresh_preparation_evidence
)
SELECT
    'negative.round3k.integrated.service_evidence.' ||
        seed.service_suffix || '.' || seed.source_suffix || '.' ||
        lower(seed.role_code),
    service.preparation_service_id,
    snapshot.professional_source_snapshot_id,
    source_file.professional_source_file_id,
    seed.role_code,
    snapshot.immutable_locator || '#' || lower(seed.role_code),
    seed.explicit_fresh
FROM (VALUES
    ('core', 'a', 'PREPARATION_PROTOCOL', TRUE),
    ('core', 'a', 'OFFICIAL_RESULT', TRUE),
    ('core', 'b', 'OFFICIAL_RESULT', TRUE),
    ('core', 'c', 'PREPARATION_PROTOCOL', TRUE),
    ('core', 'c', 'RULE_VERSION', FALSE),
    ('core', 'c', 'OFFICIAL_RESULT', TRUE),
    ('p3', 'c', 'PREPARATION_PROTOCOL', TRUE),
    ('p3', 'c', 'RULE_VERSION', FALSE),
    ('p3', 'c', 'OFFICIAL_RESULT', TRUE),
    ('p4', 'c', 'PREPARATION_PROTOCOL', TRUE),
    ('p4', 'c', 'RULE_VERSION', FALSE),
    ('p4', 'c', 'OFFICIAL_RESULT', TRUE),
    ('no_protocol', 'c', 'RULE_VERSION', FALSE),
    ('no_protocol', 'c', 'OFFICIAL_RESULT', FALSE)
) AS seed(service_suffix, source_suffix, role_code, explicit_fresh)
JOIN competition.preparation_service AS service
  ON service.preparation_service_key =
     'negative.round3k.integrated.service.' || seed.service_suffix
JOIN evidence.professional_source_snapshot AS snapshot
  ON snapshot.professional_source_snapshot_key =
     'negative.round3k.integrated.snapshot.' || seed.source_suffix
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id;

-- Official jury lineage and explicit P1 descriptors from multiple snapshots.
INSERT INTO competition.panel (
    panel_key, series_id, edition_id, category_id, round_id,
    panel_type_code, official_panel_key,
    professional_source_snapshot_id
)
SELECT
    'negative.round3k.integrated.panel.final', service.series_id,
    service.edition_id, service.category_id, service.round_id,
    'SENSORY_JURY', 'PANEL-FINAL',
    snapshot.professional_source_snapshot_id
FROM competition.preparation_service AS service
CROSS JOIN evidence.professional_source_snapshot AS snapshot
WHERE service.preparation_service_key =
      'negative.round3k.integrated.service.core'
  AND snapshot.professional_source_snapshot_key =
      'negative.round3k.integrated.snapshot.a';

INSERT INTO competition.judge (
    judge_key, pseudonymous_label, identity_scope_code,
    certification_state_code, judge_metadata
) VALUES
    (
        'negative.round3k.integrated.judge.official',
        'Fixture sensory judge', 'PSEUDONYMOUS', 'CURRENT',
        '{"fixture_role":"official_judge"}'::JSONB
    ),
    (
        'negative.round3k.integrated.judge.competitor',
        'Fixture competitor identity', 'PSEUDONYMOUS', 'NOT_APPLICABLE',
        '{"fixture_role":"competitor"}'::JSONB
    );

INSERT INTO competition.panel_membership (
    panel_membership_key, panel_id, judge_id, judge_role_code,
    professional_source_snapshot_id
)
SELECT
    'negative.round3k.integrated.panel_membership.official',
    panel.panel_id, judge.judge_id, 'SENSORY_JUDGE',
    panel.professional_source_snapshot_id
FROM competition.panel AS panel
CROSS JOIN competition.judge AS judge
WHERE panel.panel_key = 'negative.round3k.integrated.panel.final'
  AND judge.judge_key = 'negative.round3k.integrated.judge.official';

INSERT INTO competition.judge_observation (
    judge_observation_key, preparation_service_id, panel_id, judge_id,
    observation_type_code, official_confirmed,
    professional_source_snapshot_id, professional_source_file_id,
    source_observation_key, source_locator
)
SELECT
    'negative.round3k.integrated.observation.' || seed.observation_suffix,
    service.preparation_service_id, panel.panel_id, judge.judge_id,
    'JUDGE', TRUE, snapshot.professional_source_snapshot_id,
    source_file.professional_source_file_id,
    'OBS-' || upper(seed.observation_suffix),
    snapshot.immutable_locator || '#observation-' ||
        seed.observation_suffix
FROM (VALUES
    ('a', 'a', 'core'),
    ('b', 'b', 'core'),
    ('c', 'c', 'core'),
    ('no_protocol', 'c', 'no_protocol')
) AS seed(observation_suffix, source_suffix, service_suffix)
JOIN competition.preparation_service AS service
  ON service.preparation_service_key =
     'negative.round3k.integrated.service.' || seed.service_suffix
CROSS JOIN competition.panel AS panel
CROSS JOIN competition.judge AS judge
JOIN evidence.professional_source_snapshot AS snapshot
  ON snapshot.professional_source_snapshot_key =
     'negative.round3k.integrated.snapshot.' || seed.source_suffix
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id
WHERE panel.panel_key = 'negative.round3k.integrated.panel.final'
  AND judge.judge_key = 'negative.round3k.integrated.judge.official';

INSERT INTO competition.descriptor_assertion (
    descriptor_assertion_key, preparation_service_id,
    judge_observation_id, panel_id, assertion_type_code,
    evidence_tier_code, language_tag, raw_phrase, raw_phrase_sha256,
    professional_source_snapshot_id, professional_source_file_id,
    source_locator
)
SELECT
    'negative.round3k.integrated.assertion.' || seed.assertion_suffix,
    observation.preparation_service_id, observation.judge_observation_id,
    observation.panel_id, 'OFFICIAL_JUDGE_DESCRIPTOR', 'P1', 'en',
    seed.raw_phrase, audit.round3i_utf8_sha256(seed.raw_phrase),
    observation.professional_source_snapshot_id,
    observation.professional_source_file_id,
    observation.source_locator || '#' || seed.assertion_suffix
FROM (VALUES
    ('a.jasmine', 'a', 'Jasmine'),
    ('b.cocoa', 'b', 'Cocoa'),
    ('c.citrus', 'c', 'Citrus'),
    ('c.stone_fruit', 'c', 'Stone fruit'),
    ('c.machine_candidate', 'c', 'Machine candidate phrase'),
    ('c.project_candidate', 'c', 'Project candidate phrase'),
    ('c.no_protocol', 'no_protocol', 'Missing fresh protocol descriptor')
) AS seed(assertion_suffix, observation_suffix, raw_phrase)
JOIN competition.judge_observation AS observation
  ON observation.judge_observation_key =
     'negative.round3k.integrated.observation.' ||
     seed.observation_suffix;

INSERT INTO competition.competitor_declared_note (
    competitor_declared_note_key, preparation_service_id,
    professional_source_snapshot_id, professional_source_file_id,
    language_tag, raw_text, raw_text_sha256, source_locator
)
SELECT
    'negative.round3k.integrated.competitor_note.p3',
    service.preparation_service_id,
    snapshot.professional_source_snapshot_id,
    source_file.professional_source_file_id, 'en',
    'Competitor berry note',
    audit.round3i_utf8_sha256('Competitor berry note'),
    snapshot.immutable_locator || '#competitor-note'
FROM competition.preparation_service AS service
CROSS JOIN evidence.professional_source_snapshot AS snapshot
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id
WHERE service.preparation_service_key =
      'negative.round3k.integrated.service.p3'
  AND snapshot.professional_source_snapshot_key =
      'negative.round3k.integrated.snapshot.c';

INSERT INTO competition.descriptor_assertion (
    descriptor_assertion_key, preparation_service_id,
    competitor_declared_note_id, assertion_type_code,
    evidence_tier_code, language_tag, raw_phrase, raw_phrase_sha256,
    professional_source_snapshot_id, professional_source_file_id,
    source_locator
)
SELECT
    'negative.round3k.integrated.assertion.p3',
    note.preparation_service_id, note.competitor_declared_note_id,
    'COMPETITOR_DECLARED_DESCRIPTOR', 'P3', 'en',
    'Competitor berry', audit.round3i_utf8_sha256('Competitor berry'),
    note.professional_source_snapshot_id,
    note.professional_source_file_id, note.source_locator || '#descriptor'
FROM competition.competitor_declared_note AS note
WHERE note.competitor_declared_note_key =
      'negative.round3k.integrated.competitor_note.p3';

INSERT INTO competition.organizer_published_note (
    organizer_published_note_key, preparation_service_id, edition_id,
    evidence_tier_code, note_role_code,
    professional_source_snapshot_id, professional_source_file_id,
    language_tag, raw_text, raw_text_sha256, source_locator
)
SELECT
    'negative.round3k.integrated.organizer_note.p4',
    service.preparation_service_id, service.edition_id, 'P4',
    'ORGANIZER_MARKETING', snapshot.professional_source_snapshot_id,
    source_file.professional_source_file_id, 'en',
    'Luxury floral marketing note',
    audit.round3i_utf8_sha256('Luxury floral marketing note'),
    snapshot.immutable_locator || '#marketing-note'
FROM competition.preparation_service AS service
CROSS JOIN evidence.professional_source_snapshot AS snapshot
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id
WHERE service.preparation_service_key =
      'negative.round3k.integrated.service.p4'
  AND snapshot.professional_source_snapshot_key =
      'negative.round3k.integrated.snapshot.c';

INSERT INTO competition.descriptor_assertion (
    descriptor_assertion_key, preparation_service_id,
    organizer_published_note_id, assertion_type_code,
    evidence_tier_code, language_tag, raw_phrase, raw_phrase_sha256,
    professional_source_snapshot_id, professional_source_file_id,
    source_locator
)
SELECT
    'negative.round3k.integrated.assertion.p4',
    note.preparation_service_id, note.organizer_published_note_id,
    'ORGANIZER_MARKETING_DESCRIPTION', 'P4', 'en',
    'Luxury floral', audit.round3i_utf8_sha256('Luxury floral'),
    note.professional_source_snapshot_id,
    note.professional_source_file_id, note.source_locator || '#descriptor'
FROM competition.organizer_published_note AS note
WHERE note.organizer_published_note_key =
      'negative.round3k.integrated.organizer_note.p4';

-- Explicit professional expressions.  The machine/project candidates above
-- intentionally remain without expression rows for their negative attempts.
INSERT INTO corpus.professional_expression (
    professional_expression_key, descriptor_assertion_id, language_tag,
    normalized_phrase, normalization_rule_code
)
SELECT
    'negative.round3k.integrated.expression.' || seed.expression_suffix,
    assertion.descriptor_assertion_id, assertion.language_tag,
    kb.normalize_expression(assertion.raw_phrase),
    'UNICODE_NFC_WHITESPACE_CASE'
FROM (VALUES
    ('a.jasmine', 'a.jasmine'),
    ('c.citrus', 'c.citrus'),
    ('c.stone_fruit', 'c.stone_fruit'),
    ('p3', 'p3'),
    ('p4', 'p4')
) AS seed(expression_suffix, assertion_suffix)
JOIN competition.descriptor_assertion AS assertion
  ON assertion.descriptor_assertion_key =
     'negative.round3k.integrated.assertion.' || seed.assertion_suffix;

INSERT INTO corpus.professional_mapping_rule (
    professional_mapping_rule_key, rule_version, language_tag,
    exact_raw_phrase, normalized_phrase, target_concept_id,
    rule_basis_code, professional_source_snapshot_id, evidence_locator,
    mapping_date, lifecycle_status_code
)
SELECT
    'negative.round3k.integrated.mapping.' || seed.rule_suffix,
    1, 'en', seed.raw_phrase, kb.normalize_expression(seed.raw_phrase),
    concept.concept_id, 'EXPLICIT_SOURCE_DEFINED_DESCRIPTOR_IDENTITY',
    snapshot.professional_source_snapshot_id,
    snapshot.immutable_locator || '#mapping-' || seed.rule_suffix,
    CURRENT_DATE, 'active'
FROM (VALUES
    ('citrus', 'Citrus', 'category.citrus'),
    ('jasmine', 'Jasmine', 'category.citrus')
) AS seed(rule_suffix, raw_phrase, concept_key)
JOIN kb.concept AS concept ON concept.concept_key = seed.concept_key
CROSS JOIN evidence.professional_source_snapshot AS snapshot
WHERE snapshot.professional_source_snapshot_key =
      'negative.round3k.integrated.snapshot.c';

-- A valid final deterministic label supports later gate checks.
INSERT INTO corpus.professional_label_decision (
    professional_label_decision_key, professional_expression_id,
    decision_version, label_disposition_code, decision_method_code,
    professional_mapping_rule_id, independent_qualified_reviewer_count,
    adjudicator_present, expert_review_complete, candidate_only,
    decision_status_code, provenance_complete, decision_basis, decided_at
)
SELECT
    'negative.round3k.integrated.label.citrus.final',
    expression.professional_expression_id, 1,
    'EXACT_CANONICAL_TARGET', 'LEVEL_ONE_DETERMINISTIC',
    mapping_rule.professional_mapping_rule_id, 0,
    FALSE, FALSE, FALSE, 'FINAL', TRUE,
    'Exact governed transaction-fixture mapping', CURRENT_TIMESTAMP
FROM corpus.professional_expression AS expression
CROSS JOIN corpus.professional_mapping_rule AS mapping_rule
WHERE expression.professional_expression_key =
      'negative.round3k.integrated.expression.c.citrus'
  AND mapping_rule.professional_mapping_rule_key =
      'negative.round3k.integrated.mapping.citrus';

INSERT INTO corpus.professional_label_target (
    professional_label_decision_id, target_ordinal, concept_id,
    target_role_code
)
SELECT decision.professional_label_decision_id, 1,
       mapping_rule.target_concept_id, 'PRIMARY'
FROM corpus.professional_label_decision AS decision
JOIN corpus.professional_mapping_rule AS mapping_rule
  ON mapping_rule.professional_mapping_rule_id =
     decision.professional_mapping_rule_id
WHERE decision.professional_label_decision_key =
      'negative.round3k.integrated.label.citrus.final';

-- Candidate-only decisions stay unresolved and never masquerade as reviewed
-- labels.  They also provide isolated P3/P4 training-gate fixtures.
INSERT INTO corpus.professional_label_decision (
    professional_label_decision_key, professional_expression_id,
    decision_version, label_disposition_code, decision_method_code,
    independent_qualified_reviewer_count, adjudicator_present,
    expert_review_complete, candidate_only, decision_status_code,
    provenance_complete, decision_basis, decided_at
)
SELECT
    'negative.round3k.integrated.label.' || seed.decision_suffix ||
        '.candidate',
    expression.professional_expression_id, 1, 'UNRESOLVED',
    'CODEX_CANDIDATE', 0, FALSE, FALSE, TRUE, 'CANDIDATE', FALSE,
    'Unreviewed software candidate retained only for review',
    CURRENT_TIMESTAMP
FROM (VALUES
    ('stone_fruit', 'c.stone_fruit'),
    ('p3', 'p3'),
    ('p4', 'p4')
) AS seed(decision_suffix, expression_suffix)
JOIN corpus.professional_expression AS expression
  ON expression.professional_expression_key =
     'negative.round3k.integrated.expression.' || seed.expression_suffix;

INSERT INTO audit.reviewer (
    reviewer_key, display_name, affiliation
) VALUES (
    'negative.round3k.integrated.reviewer.fixture',
    'Round 3K transaction fixture reviewer',
    'Round 3K transaction fixture only'
);

-- Excluded candidates can be inventoried without asserting eligibility.  One
-- deterministic assignment establishes the within-plan leakage boundary.
INSERT INTO ml.professional_training_candidate (
    professional_training_candidate_key, preparation_service_id,
    task_code, professional_rights_decision_id, candidate_status_code,
    provenance_complete, rights_complete, integrity_complete, included,
    exclusion_reason_code
)
SELECT
    'negative.round3k.integrated.training.' || seed.service_suffix ||
        '.excluded',
    service.preparation_service_id, 'ADAPTIVE_CANDIDATE_RESEARCH',
    rights.professional_rights_decision_id, 'EXCLUDED',
    TRUE, TRUE, TRUE, FALSE, 'OTHER_GOVERNED'
FROM (VALUES ('core'), ('p3')) AS seed(service_suffix)
JOIN competition.preparation_service AS service
  ON service.preparation_service_key =
     'negative.round3k.integrated.service.' || seed.service_suffix
CROSS JOIN evidence.professional_rights_decision AS rights
WHERE rights.professional_rights_decision_key =
      'negative.round3k.integrated.rights.c';

INSERT INTO ml.professional_split_plan (
    professional_split_plan_key, plan_version,
    deterministic_rule_version, random_row_split, lifecycle_status_code
) VALUES (
    'negative.round3k.integrated.split', 1,
    'round3k-transaction-fixture-v1', FALSE, 'CANDIDATE'
);

INSERT INTO ml.professional_split_assignment (
    professional_split_plan_id, professional_training_candidate_id,
    partition_code, assignment_key, deterministic_assignment_sha256
)
SELECT plan.professional_split_plan_id,
       candidate.professional_training_candidate_id,
       'TRAIN', 'negative.round3k.integrated.assignment.core.train',
       repeat('d', 64)
FROM ml.professional_split_plan AS plan
CROSS JOIN ml.professional_training_candidate AS candidate
WHERE plan.professional_split_plan_key =
      'negative.round3k.integrated.split'
  AND candidate.professional_training_candidate_key =
      'negative.round3k.integrated.training.core.excluded';

-- Validate every positive fixture before isolating the negative assertions.
SET CONSTRAINTS ALL IMMEDIATE;
SET CONSTRAINTS ALL DEFERRED;

SELECT pg_temp.expect_round3k_failure(
    'source_snapshot_hash_missing',
    $sql$
        INSERT INTO evidence.professional_source_snapshot (
            professional_source_snapshot_key, professional_source_id,
            source_family_key, exact_version, retrieved_at,
            immutable_locator, snapshot_sha256, access_method_code,
            automated_access_compliance_code,
            lawfully_acquired_for_internal_research,
            source_record_count, admitted
        )
        SELECT
            'negative.round3k.integrated.snapshot.missing_hash',
            professional_source_id, source_family_key, 'missing-hash-v1',
            CURRENT_TIMESTAMP,
            'https://example.invalid/round3k/missing-hash',
            'missing', 'PERMITTED_HTTP', 'PERMITTED', TRUE, 0, TRUE
        FROM evidence.professional_source
        WHERE professional_source_key =
              'negative.round3k.integrated.source.a'
    $sql$,
    '23514', 'professional_source_snapshot_text_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'source_file_hash_missing',
    $sql$
        INSERT INTO evidence.professional_source_file (
            professional_source_file_key,
            professional_source_snapshot_id, filename, file_role_code,
            official_locator, declared_sha256, verified_sha256,
            file_size_bytes, row_count, field_count, hash_verified,
            retention_state_code, public_redistribution_allowed,
            source_owner, source_url, license_or_terms,
            attribution_requirement, modification_status
        )
        SELECT
            'negative.round3k.integrated.file.missing_hash',
            professional_source_snapshot_id, 'missing-hash.json',
            'RAW_OFFICIAL', immutable_locator, 'missing', repeat('a', 64),
            0, 0, 0, FALSE, 'HASH_AND_LOCATOR_ONLY', FALSE,
            'Fixture owner', immutable_locator, 'Internal fixture',
            'Retain owner', 'Unmodified'
        FROM evidence.professional_source_snapshot
        WHERE professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.a'
    $sql$,
    '23514', 'professional_source_file_text_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'verified_source_file_hash_mismatch',
    $sql$
        INSERT INTO evidence.professional_source_file (
            professional_source_file_key,
            professional_source_snapshot_id, filename, file_role_code,
            official_locator, declared_sha256, verified_sha256,
            file_size_bytes, row_count, field_count, hash_verified,
            retention_state_code, public_redistribution_allowed,
            source_owner, source_url, license_or_terms,
            attribution_requirement, modification_status
        )
        SELECT
            'negative.round3k.integrated.file.hash_mismatch',
            professional_source_snapshot_id, 'hash-mismatch.json',
            'RAW_OFFICIAL', immutable_locator, repeat('a', 64),
            repeat('b', 64), 0, 0, 0, TRUE,
            'HASH_AND_LOCATOR_ONLY', FALSE, 'Fixture owner',
            immutable_locator, 'Internal fixture', 'Retain owner',
            'Unmodified'
        FROM evidence.professional_source_snapshot
        WHERE professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.a'
    $sql$,
    '23514', 'professional_source_file_shape_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'mismatched_source_file_and_snapshot',
    $sql$
        INSERT INTO competition.preparation_service_evidence (
            preparation_service_evidence_key, preparation_service_id,
            professional_source_snapshot_id, professional_source_file_id,
            evidence_role_code, source_locator,
            explicit_fresh_preparation_evidence
        )
        SELECT
            'negative.round3k.integrated.service_evidence.mismatch',
            service.preparation_service_id,
            snapshot_b.professional_source_snapshot_id,
            file_a.professional_source_file_id, 'ORGANIZER_EXPORT',
            snapshot_b.immutable_locator || '#mismatched-file', FALSE
        FROM competition.preparation_service AS service
        CROSS JOIN evidence.professional_source_snapshot AS snapshot_b
        CROSS JOIN evidence.professional_source_file AS file_a
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND snapshot_b.professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.b'
          AND file_a.professional_source_file_key =
              'negative.round3k.integrated.file.a'
    $sql$,
    '23503', 'preparation_service_evidence_file_snapshot_fk'
);

SELECT pg_temp.expect_round3k_failure(
    'competitor_identity_cannot_supply_judge_observation',
    $sql$
        INSERT INTO competition.judge_observation (
            judge_observation_key, preparation_service_id, panel_id,
            judge_id, observation_type_code, official_confirmed,
            professional_source_snapshot_id, professional_source_file_id,
            source_observation_key, source_locator
        )
        SELECT
            'negative.round3k.integrated.observation.competitor',
            service.preparation_service_id, panel.panel_id,
            competitor.judge_id, 'JUDGE', TRUE,
            snapshot.professional_source_snapshot_id,
            source_file.professional_source_file_id,
            'OBS-COMPETITOR', snapshot.immutable_locator || '#competitor'
        FROM competition.preparation_service AS service
        CROSS JOIN competition.panel AS panel
        CROSS JOIN competition.judge AS competitor
        CROSS JOIN evidence.professional_source_snapshot AS snapshot
        JOIN evidence.professional_source_file AS source_file
          ON source_file.professional_source_snapshot_id =
             snapshot.professional_source_snapshot_id
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND panel.panel_key =
              'negative.round3k.integrated.panel.final'
          AND competitor.judge_key =
              'negative.round3k.integrated.judge.competitor'
          AND snapshot.professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.a'
    $sql$,
    '23514', 'competition_judge_observation_lineage_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'competitor_note_cannot_be_promoted_to_judge_p1',
    $sql$
        INSERT INTO competition.descriptor_assertion (
            descriptor_assertion_key, preparation_service_id,
            competitor_declared_note_id, assertion_type_code,
            evidence_tier_code, language_tag, raw_phrase,
            raw_phrase_sha256, professional_source_snapshot_id,
            professional_source_file_id, source_locator
        )
        SELECT
            'negative.round3k.integrated.assertion.competitor_as_judge',
            note.preparation_service_id, note.competitor_declared_note_id,
            'OFFICIAL_JUDGE_DESCRIPTOR', 'P1', 'en', 'Competitor berry',
            audit.round3i_utf8_sha256('Competitor berry'),
            note.professional_source_snapshot_id,
            note.professional_source_file_id,
            note.source_locator || '#promoted-to-p1'
        FROM competition.competitor_declared_note AS note
        WHERE note.competitor_declared_note_key =
              'negative.round3k.integrated.competitor_note.p3'
    $sql$,
    '23514', 'descriptor_assertion_lineage_shape_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'organizer_marketing_cannot_be_p1',
    $sql$
        INSERT INTO competition.organizer_published_note (
            organizer_published_note_key, preparation_service_id,
            edition_id, evidence_tier_code, note_role_code,
            professional_source_snapshot_id, professional_source_file_id,
            language_tag, raw_text, raw_text_sha256, source_locator
        )
        SELECT
            'negative.round3k.integrated.organizer_note.marketing_p1',
            service.preparation_service_id, service.edition_id, 'P1',
            'ORGANIZER_MARKETING', snapshot.professional_source_snapshot_id,
            source_file.professional_source_file_id, 'en',
            'Marketing is not judge evidence',
            audit.round3i_utf8_sha256('Marketing is not judge evidence'),
            snapshot.immutable_locator || '#marketing-p1'
        FROM competition.preparation_service AS service
        CROSS JOIN evidence.professional_source_snapshot AS snapshot
        JOIN evidence.professional_source_file AS source_file
          ON source_file.professional_source_snapshot_id =
             snapshot.professional_source_snapshot_id
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND snapshot.professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.a'
    $sql$,
    '23514', 'organizer_published_note_role_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'judge_rows_cannot_inflate_effective_service_grain',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, c0_preparation_concept_id,
            c0_assignment_basis_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.integrated.service.core.duplicate',
            series_id, edition_id, category_id, round_id, entry_id,
            entry_service_key, rule_version_id, scoresheet_status_code,
            fresh_preparation_confirmed, fresh_preparation_status_code,
            preparation_taxonomy_code, milk_auxiliary,
            black_coffee_core_candidate, c0_source_status_code,
            c0_preparation_concept_id, c0_assignment_basis_code,
            source_native_roast_status_code, c1_mapping_status_code,
            lifecycle_status_code
        FROM competition.preparation_service
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.core'
    $sql$,
    '23514', 'competition_preparation_service_repeat_link_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'fresh_service_without_confirmed_protocol_status',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, c0_preparation_concept_id,
            c0_assignment_basis_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.integrated.service.fresh_without_status',
            series_id, edition_id, category_id, round_id, entry_id,
            'negative.round3k.integrated.entry_service.fresh_without_status',
            rule_version_id, scoresheet_status_code, TRUE, 'NOT_REPORTED',
            preparation_taxonomy_code, milk_auxiliary,
            black_coffee_core_candidate, c0_source_status_code,
            c0_preparation_concept_id, c0_assignment_basis_code,
            source_native_roast_status_code, c1_mapping_status_code,
            lifecycle_status_code
        FROM competition.preparation_service
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.core'
    $sql$,
    '23514', 'competition_preparation_service_fresh_status_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'missing_or_out_of_scope_rule_version',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, c0_preparation_concept_id,
            c0_assignment_basis_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.integrated.service.missing_rule',
            series_id, edition_id, category_id, round_id, entry_id,
            'negative.round3k.integrated.entry_service.missing_rule',
            9223372036854775000::BIGINT, scoresheet_status_code,
            fresh_preparation_confirmed, fresh_preparation_status_code,
            preparation_taxonomy_code, milk_auxiliary,
            black_coffee_core_candidate, c0_source_status_code,
            c0_preparation_concept_id, c0_assignment_basis_code,
            source_native_roast_status_code, c1_mapping_status_code,
            lifecycle_status_code
        FROM competition.preparation_service
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.core'
    $sql$,
    '23503', 'competition_preparation_service_category_scope_fk'
);

SELECT pg_temp.expect_round3k_failure(
    'public_results_permission_is_not_model_permission',
    $sql$
        INSERT INTO ml.professional_training_candidate (
            professional_training_candidate_key, preparation_service_id,
            task_code, professional_rights_decision_id,
            candidate_status_code, provenance_complete, rights_complete,
            integrity_complete, included
        )
        SELECT
            'negative.round3k.integrated.training.public_not_model',
            service.preparation_service_id, 'C0_C1_CONTEXT',
            rights.professional_rights_decision_id, 'ELIGIBLE',
            TRUE, TRUE, TRUE, TRUE
        FROM competition.preparation_service AS service
        CROSS JOIN evidence.professional_rights_decision AS rights
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND rights.professional_rights_decision_key =
              'negative.round3k.integrated.rights.a'
    $sql$,
    '23514', 'professional_training_candidate_rights_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'rights_pending_cannot_be_model_eligible',
    $sql$
        INSERT INTO ml.professional_training_candidate (
            professional_training_candidate_key, preparation_service_id,
            task_code, professional_rights_decision_id,
            candidate_status_code, provenance_complete, rights_complete,
            integrity_complete, included
        )
        SELECT
            'negative.round3k.integrated.training.pending_model_rights',
            service.preparation_service_id, 'C0_C1_CONTEXT',
            rights.professional_rights_decision_id, 'ELIGIBLE',
            TRUE, TRUE, TRUE, TRUE
        FROM competition.preparation_service AS service
        CROSS JOIN evidence.professional_rights_decision AS rights
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND rights.professional_rights_decision_key =
              'negative.round3k.integrated.rights.b'
    $sql$,
    '23514', 'professional_training_candidate_rights_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'p3_competitor_only_cannot_satisfy_final_label_gate',
    $sql$
        INSERT INTO ml.professional_training_candidate (
            professional_training_candidate_key, preparation_service_id,
            task_code, professional_rights_decision_id,
            candidate_status_code, provenance_complete, rights_complete,
            integrity_complete, included
        )
        SELECT
            'negative.round3k.integrated.training.p3_only',
            service.preparation_service_id, 'DESCRIPTOR_NORMALIZATION',
            rights.professional_rights_decision_id, 'ELIGIBLE',
            TRUE, TRUE, TRUE, TRUE
        FROM competition.preparation_service AS service
        CROSS JOIN evidence.professional_rights_decision AS rights
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.p3'
          AND rights.professional_rights_decision_key =
              'negative.round3k.integrated.rights.c'
    $sql$,
    '23514', 'professional_training_candidate_label_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'p4_marketing_only_cannot_satisfy_final_label_gate',
    $sql$
        INSERT INTO ml.professional_training_candidate (
            professional_training_candidate_key, preparation_service_id,
            task_code, professional_rights_decision_id,
            candidate_status_code, provenance_complete, rights_complete,
            integrity_complete, included
        )
        SELECT
            'negative.round3k.integrated.training.p4_only',
            service.preparation_service_id, 'DESCRIPTOR_NORMALIZATION',
            rights.professional_rights_decision_id, 'ELIGIBLE',
            TRUE, TRUE, TRUE, TRUE
        FROM competition.preparation_service AS service
        CROSS JOIN evidence.professional_rights_decision AS rights
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.p4'
          AND rights.professional_rights_decision_key =
              'negative.round3k.integrated.rights.c'
    $sql$,
    '23514', 'professional_training_candidate_label_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'forced_single_target_rejected_for_multi_disposition',
    $sql$
        WITH decision AS (
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
            SELECT
                'negative.round3k.integrated.label.forced_single',
                expression.professional_expression_id, 2,
                predecessor.professional_label_decision_id,
                'MULTI_CANONICAL_TARGET', 'CODEX_CANDIDATE', 0,
                FALSE, FALSE, TRUE, 'CANDIDATE', FALSE,
                'Single software target cannot collapse multi-target review',
                CURRENT_TIMESTAMP
            FROM corpus.professional_expression AS expression
            JOIN corpus.professional_label_decision AS predecessor
              ON predecessor.professional_expression_id =
                 expression.professional_expression_id
            WHERE expression.professional_expression_key =
                  'negative.round3k.integrated.expression.c.stone_fruit'
            RETURNING professional_label_decision_id
        )
        INSERT INTO corpus.professional_label_target (
            professional_label_decision_id, target_ordinal, concept_id,
            target_role_code
        )
        SELECT decision.professional_label_decision_id, 1,
               concept.concept_id, 'PRIMARY'
        FROM decision
        CROSS JOIN kb.concept AS concept
        WHERE concept.concept_key = 'category.citrus'
    $sql$,
    '23514', 'professional_label_target_cardinality_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'software_candidate_cannot_be_treated_as_reviewed_label',
    $sql$
        INSERT INTO audit.professional_label_review (
            professional_label_decision_id, reviewer_id,
            reviewer_role_code, review_outcome_code,
            review_evidence, reviewed_at
        )
        SELECT decision.professional_label_decision_id,
               reviewer.reviewer_id, 'INDEPENDENT_REVIEWER', 'ACCEPT',
               'A review row cannot convert candidate-only state',
               CURRENT_TIMESTAMP
        FROM corpus.professional_label_decision AS decision
        CROSS JOIN audit.reviewer AS reviewer
        WHERE decision.professional_label_decision_key =
              'negative.round3k.integrated.label.stone_fruit.candidate'
          AND reviewer.reviewer_key =
              'negative.round3k.integrated.reviewer.fixture'
    $sql$,
    '23514', 'professional_label_nonexpert_review_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'deterministic_target_must_match_mapping_rule',
    $sql$
        WITH decision AS (
            INSERT INTO corpus.professional_label_decision (
                professional_label_decision_key,
                professional_expression_id, decision_version,
                label_disposition_code, decision_method_code,
                professional_mapping_rule_id,
                independent_qualified_reviewer_count,
                adjudicator_present, expert_review_complete,
                candidate_only, decision_status_code,
                provenance_complete, decision_basis, decided_at
            )
            SELECT
                'negative.round3k.integrated.label.jasmine.mismatch',
                expression.professional_expression_id, 1,
                'EXACT_CANONICAL_TARGET', 'LEVEL_ONE_DETERMINISTIC',
                mapping_rule.professional_mapping_rule_id, 0,
                FALSE, FALSE, FALSE, 'FINAL', TRUE,
                'Deliberately mismatched deterministic target',
                CURRENT_TIMESTAMP
            FROM corpus.professional_expression AS expression
            CROSS JOIN corpus.professional_mapping_rule AS mapping_rule
            WHERE expression.professional_expression_key =
                  'negative.round3k.integrated.expression.a.jasmine'
              AND mapping_rule.professional_mapping_rule_key =
                  'negative.round3k.integrated.mapping.jasmine'
            RETURNING professional_label_decision_id
        )
        INSERT INTO corpus.professional_label_target (
            professional_label_decision_id, target_ordinal, concept_id,
            target_role_code
        )
        SELECT decision.professional_label_decision_id, 1,
               concept.concept_id, 'PRIMARY'
        FROM decision
        CROSS JOIN kb.concept AS concept
        WHERE concept.concept_key = 'sensory.jasmine'
    $sql$,
    '23514', 'professional_label_deterministic_target_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'cross_source_coassertion_rejected',
    $sql$
        INSERT INTO corpus.professional_coassertion_event (
            professional_coassertion_event_key, preparation_service_id,
            judge_observation_id, panel_id,
            left_descriptor_assertion_id,
            right_descriptor_assertion_id,
            professional_source_snapshot_id, coassertion_method_code
        )
        SELECT
            'negative.round3k.integrated.coassertion.cross_source',
            left_assertion.preparation_service_id,
            left_assertion.judge_observation_id,
            left_assertion.panel_id,
            left_assertion.descriptor_assertion_id,
            right_assertion.descriptor_assertion_id,
            left_assertion.professional_source_snapshot_id,
            'SAME_JUDGE_OBSERVATION'
        FROM competition.descriptor_assertion AS left_assertion
        CROSS JOIN competition.descriptor_assertion AS right_assertion
        WHERE left_assertion.descriptor_assertion_key =
              'negative.round3k.integrated.assertion.a.jasmine'
          AND right_assertion.descriptor_assertion_key =
              'negative.round3k.integrated.assertion.b.cocoa'
    $sql$,
    '23514', 'professional_coassertion_lineage_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'orphan_panel_consensus_rejected',
    $sql$
        INSERT INTO competition.descriptor_assertion (
            descriptor_assertion_key, preparation_service_id, panel_id,
            assertion_type_code, evidence_tier_code, language_tag,
            raw_phrase, raw_phrase_sha256,
            professional_source_snapshot_id, professional_source_file_id,
            source_locator, derived_from_judge_observations
        )
        SELECT
            'negative.round3k.integrated.assertion.orphan_consensus',
            service.preparation_service_id, panel.panel_id,
            'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR', 'P1', 'en',
            'Orphan consensus',
            audit.round3i_utf8_sha256('Orphan consensus'),
            snapshot.professional_source_snapshot_id,
            source_file.professional_source_file_id,
            snapshot.immutable_locator || '#orphan-consensus', TRUE
        FROM competition.preparation_service AS service
        CROSS JOIN competition.panel AS panel
        CROSS JOIN evidence.professional_source_snapshot AS snapshot
        JOIN evidence.professional_source_file AS source_file
          ON source_file.professional_source_snapshot_id =
             snapshot.professional_source_snapshot_id
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND panel.panel_key =
              'negative.round3k.integrated.panel.final'
          AND snapshot.professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.a'
    $sql$,
    '23514', 'descriptor_assertion_consensus_lineage_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'duplicate_group_requires_duplicate_member',
    $sql$
        WITH duplicate_group AS (
            INSERT INTO audit.professional_duplicate_group (
                professional_duplicate_group_key, duplicate_type_code,
                decision_basis_code, reviewed
            ) VALUES (
                'negative.round3k.integrated.duplicate.one_member',
                'EXACT_RECORD_DUPLICATE', 'SOURCE_IDENTIFIER', TRUE
            ) RETURNING professional_duplicate_group_id
        )
        INSERT INTO audit.professional_duplicate_group_member (
            professional_duplicate_group_id, member_ordinal,
            preparation_service_id, member_role_code
        )
        SELECT duplicate_group.professional_duplicate_group_id, 1,
               service.preparation_service_id, 'CANONICAL'
        FROM duplicate_group
        CROSS JOIN competition.preparation_service AS service
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
    $sql$,
    '23514', 'professional_duplicate_group_shape_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'mirror_group_requires_snapshot_members',
    $sql$
        WITH mirror_group AS (
            INSERT INTO audit.professional_duplicate_group (
                professional_duplicate_group_key, duplicate_type_code,
                decision_basis_code, reviewed
            ) VALUES (
                'negative.round3k.integrated.duplicate.bad_mirror',
                'MIRROR_SOURCE', 'OFFICIAL_LINK', TRUE
            ) RETURNING professional_duplicate_group_id
        )
        INSERT INTO audit.professional_duplicate_group_member (
            professional_duplicate_group_id, member_ordinal,
            preparation_service_id, professional_source_snapshot_id,
            member_role_code
        )
        SELECT mirror_group.professional_duplicate_group_id,
               seed.ordinal,
               CASE WHEN seed.member_kind = 'SERVICE'
                    THEN service.preparation_service_id END,
               CASE WHEN seed.member_kind = 'SNAPSHOT'
                    THEN snapshot.professional_source_snapshot_id END,
               seed.member_role
        FROM mirror_group
        CROSS JOIN (VALUES
            (1, 'SERVICE', 'CANONICAL'),
            (2, 'SNAPSHOT', 'MIRROR')
        ) AS seed(ordinal, member_kind, member_role)
        CROSS JOIN competition.preparation_service AS service
        CROSS JOIN evidence.professional_source_snapshot AS snapshot
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND snapshot.professional_source_snapshot_key =
              'negative.round3k.integrated.snapshot.b'
    $sql$,
    '23514', 'professional_duplicate_group_shape_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'repeat_audit_must_match_service_relationship',
    $sql$
        INSERT INTO audit.professional_repeat_audit (
            preparation_service_id, repeats_preparation_service_id,
            repeat_relationship_code, relationship_status_code,
            evidence_basis
        )
        SELECT child.preparation_service_id, parent.preparation_service_id,
               'LATER_ROUND', 'REVIEWED_CONFIRMED',
               'Deliberately absent service repeat relationship'
        FROM competition.preparation_service AS child
        CROSS JOIN competition.preparation_service AS parent
        WHERE child.preparation_service_key =
              'negative.round3k.integrated.service.p3'
          AND parent.preparation_service_key =
              'negative.round3k.integrated.service.core'
    $sql$,
    '23514', 'professional_repeat_audit_lineage_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'filter_service_cannot_infer_light_roast',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, reviewed_c1_roast_category_id,
            c1_mapping_basis_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.integrated.service.filter_roast_inference',
            service.series_id, service.edition_id, service.category_id,
            service.round_id, service.entry_id,
            'negative.round3k.integrated.entry_service.filter_inference',
            service.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'NOT_APPLICABLE',
            'NOT_REPORTED', 'REVIEWED', roast.roast_category_id,
            'GOVERNED_REVIEW', 'active'
        FROM competition.preparation_service AS service
        CROSS JOIN context.roast_category AS roast
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND roast.roast_category_key = 'roast.project_v1.light'
    $sql$,
    '23514', 'competition_preparation_service_c1_status_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'espresso_service_cannot_infer_dark_roast',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, reviewed_c1_roast_category_id,
            c1_mapping_basis_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.integrated.service.espresso_roast_inference',
            service.series_id, service.edition_id, service.category_id,
            service.round_id, service.entry_id,
            'negative.round3k.integrated.entry_service.espresso_inference',
            service.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'ESPRESSO', FALSE, TRUE, 'NOT_APPLICABLE',
            'NOT_REPORTED', 'REVIEWED', roast.roast_category_id,
            'GOVERNED_REVIEW', 'active'
        FROM competition.preparation_service AS service
        CROSS JOIN context.roast_category AS roast
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND roast.roast_category_key = 'roast.project_v1.dark'
    $sql$,
    '23514', 'competition_preparation_service_c1_status_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'nordic_identity_cannot_infer_roast',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, reviewed_c1_roast_category_id,
            c1_mapping_basis_code, lifecycle_status_code, service_metadata
        )
        SELECT
            'negative.round3k.integrated.service.nordic_roast_inference',
            service.series_id, service.edition_id, service.category_id,
            service.round_id, service.entry_id,
            'negative.round3k.integrated.entry_service.nordic_inference',
            service.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'NOT_APPLICABLE',
            'NOT_REPORTED', 'REVIEWED', roast.roast_category_id,
            'GOVERNED_REVIEW', 'active',
            '{"regional_identity":"Nordic"}'::JSONB
        FROM competition.preparation_service AS service
        CROSS JOIN context.roast_category AS roast
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.core'
          AND roast.roast_category_key = 'roast.project_v1.extremely_light'
    $sql$,
    '23514', 'competition_preparation_service_c1_status_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'semantically_inferred_descriptor_rejected',
    $sql$
        INSERT INTO competition.descriptor_assertion (
            descriptor_assertion_key, preparation_service_id,
            judge_observation_id, panel_id, assertion_type_code,
            evidence_tier_code, language_tag, raw_phrase,
            raw_phrase_sha256, professional_source_snapshot_id,
            professional_source_file_id, source_locator,
            semantic_inference_used
        )
        SELECT
            'negative.round3k.integrated.assertion.semantic_inference',
            observation.preparation_service_id,
            observation.judge_observation_id, observation.panel_id,
            'OFFICIAL_JUDGE_DESCRIPTOR', 'P1', 'en',
            'Inferred descriptor',
            audit.round3i_utf8_sha256('Inferred descriptor'),
            observation.professional_source_snapshot_id,
            observation.professional_source_file_id,
            observation.source_locator || '#semantic-inference', TRUE
        FROM competition.judge_observation AS observation
        WHERE observation.judge_observation_key =
              'negative.round3k.integrated.observation.a'
    $sql$,
    '23514', 'descriptor_assertion_type_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'llm_generated_expression_rejected',
    $sql$
        INSERT INTO corpus.professional_expression (
            professional_expression_key, descriptor_assertion_id,
            language_tag, normalized_phrase, normalization_rule_code,
            machine_generated
        )
        SELECT
            'negative.round3k.integrated.expression.machine_generated',
            descriptor_assertion_id, language_tag,
            kb.normalize_expression(raw_phrase),
            'UNICODE_NFC_WHITESPACE_CASE', TRUE
        FROM competition.descriptor_assertion
        WHERE descriptor_assertion_key =
              'negative.round3k.integrated.assertion.c.machine_candidate'
    $sql$,
    '23514', 'professional_expression_text_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'project_authored_expression_rejected',
    $sql$
        INSERT INTO corpus.professional_expression (
            professional_expression_key, descriptor_assertion_id,
            language_tag, normalized_phrase, normalization_rule_code,
            project_authored
        )
        SELECT
            'negative.round3k.integrated.expression.project_authored',
            descriptor_assertion_id, language_tag,
            kb.normalize_expression(raw_phrase),
            'UNICODE_NFC_WHITESPACE_CASE', TRUE
        FROM competition.descriptor_assertion
        WHERE descriptor_assertion_key =
              'negative.round3k.integrated.assertion.c.project_candidate'
    $sql$,
    '23514', 'professional_expression_text_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'round3k_model_run_prohibited',
    $sql$
        INSERT INTO ml.model_run (
            model_run_key, model_version_id, model_run_status_code,
            input_dataset_id, input_corpus_id, started_at, completed_at,
            random_seed, run_configuration, result_metadata
        )
        SELECT
            'negative.round3k.integrated.model_run', model_version_id,
            model_run_status_code, input_dataset_id, input_corpus_id,
            started_at, completed_at, random_seed,
            run_configuration || '{"round":"3K"}'::JSONB,
            '{}'::JSONB
        FROM ml.model_run
        ORDER BY model_run_id
        LIMIT 1
    $sql$,
    '23514', 'round3k_model_run_prohibited_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'model_weight_artifact_prohibited',
    $sql$
        INSERT INTO audit.round3k_artifact_registry (
            round3k_artifact_key, artifact_type_code, artifact_path,
            artifact_sha256, model_weight_artifact, embedding_artifact
        ) VALUES (
            'negative.round3k.integrated.artifact.weights',
            'TRAINING_CORPUS_CANDIDATE_MANIFEST',
            'db/data/round3k/forbidden-weights.bin', repeat('e', 64),
            TRUE, FALSE
        )
    $sql$,
    '23514', 'round3k_artifact_registry_text_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'embedding_artifact_prohibited',
    $sql$
        INSERT INTO audit.round3k_artifact_registry (
            round3k_artifact_key, artifact_type_code, artifact_path,
            artifact_sha256, model_weight_artifact, embedding_artifact
        ) VALUES (
            'negative.round3k.integrated.artifact.embedding',
            'TRAINING_CORPUS_CANDIDATE_MANIFEST',
            'db/data/round3k/forbidden-embedding.bin', repeat('f', 64),
            FALSE, TRUE
        )
    $sql$,
    '23514', 'round3k_artifact_registry_text_ck'
);

SELECT pg_temp.expect_round3k_failure(
    'same_candidate_cannot_cross_partitions_in_one_plan',
    $sql$
        INSERT INTO ml.professional_split_assignment (
            professional_split_plan_id,
            professional_training_candidate_id, partition_code,
            assignment_key, deterministic_assignment_sha256
        )
        SELECT plan.professional_split_plan_id,
               candidate.professional_training_candidate_id,
               'TEST',
               'negative.round3k.integrated.assignment.core.test',
               repeat('1', 64)
        FROM ml.professional_split_plan AS plan
        CROSS JOIN ml.professional_training_candidate AS candidate
        WHERE plan.professional_split_plan_key =
              'negative.round3k.integrated.split'
          AND candidate.professional_training_candidate_key =
              'negative.round3k.integrated.training.core.excluded'
    $sql$,
    '23505', 'professional_split_assignment_pk'
);

-- Migration 052 gate surfaces: auxiliary descriptors must stay out of the
-- observed core, and an otherwise valid P1 service without explicit fresh
-- provenance must not enter that core.
SELECT pg_temp.expect_round3k_gate_count(
    'p3_service_excluded_from_observed_core',
    $sql$
        SELECT count(*)
        FROM competition.v_round3k_observed_core_professional_record
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.p3'
    $sql$,
    0
);

SELECT pg_temp.expect_round3k_gate_count(
    'p3_service_retained_as_auxiliary',
    $sql$
        SELECT count(*)
        FROM competition.v_round3k_auxiliary_professional_record
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.p3'
    $sql$,
    1
);

SELECT pg_temp.expect_round3k_gate_count(
    'p4_service_excluded_from_observed_core',
    $sql$
        SELECT count(*)
        FROM competition.v_round3k_observed_core_professional_record
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.p4'
    $sql$,
    0
);

SELECT pg_temp.expect_round3k_gate_count(
    'p4_service_retained_as_auxiliary',
    $sql$
        SELECT count(*)
        FROM competition.v_round3k_auxiliary_professional_record
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.p4'
    $sql$,
    1
);

SELECT pg_temp.expect_round3k_gate_count(
    'missing_fresh_protocol_has_p1_payload',
    $sql$
        SELECT count(*)
        FROM competition.v_round3k_professional_payload AS payload
        JOIN competition.preparation_service AS service
          ON service.preparation_service_id =
             payload.preparation_service_id
        WHERE service.preparation_service_key =
              'negative.round3k.integrated.service.no_protocol'
    $sql$,
    1
);

SELECT pg_temp.expect_round3k_gate_count(
    'missing_fresh_protocol_excluded_from_observed_core',
    $sql$
        SELECT count(*)
        FROM competition.v_round3k_observed_core_professional_record
        WHERE preparation_service_key =
              'negative.round3k.integrated.service.no_protocol'
    $sql$,
    0
);

SELECT pg_temp.expect_round3k_gate_count(
    'round3k_validation_queries_clean_before_leak_fixture',
    $sql$
        SELECT count(*)
        FROM audit.run_round3k_validation_queries()
        WHERE NOT passed
    $sql$,
    0
);

-- The split gate is intentionally view-enforced rather than a row constraint:
-- construct two otherwise model-eligible services sharing one coffee identity
-- across TRAIN/TEST, assert both the leakage view and the guaranteed validation
-- function detect it, then discard the entire attempted leak.
SAVEPOINT round3k_split_leakage_fixture;

DELETE FROM corpus.professional_expression
WHERE professional_expression_key =
      'negative.round3k.integrated.expression.a.jasmine';

DELETE FROM competition.descriptor_assertion
WHERE descriptor_assertion_key IN (
    'negative.round3k.integrated.assertion.a.jasmine',
    'negative.round3k.integrated.assertion.b.cocoa'
);

INSERT INTO competition.preparation_service_evidence (
    preparation_service_evidence_key, preparation_service_id,
    professional_source_snapshot_id, professional_source_file_id,
    evidence_role_code, source_locator,
    explicit_fresh_preparation_evidence
)
SELECT
    'negative.round3k.integrated.service_evidence.no_protocol.c.' ||
        'attempted_fresh_protocol',
    service.preparation_service_id,
    snapshot.professional_source_snapshot_id,
    source_file.professional_source_file_id, 'PREPARATION_PROTOCOL',
    snapshot.immutable_locator || '#attempted-fresh-protocol', TRUE
FROM competition.preparation_service AS service
CROSS JOIN evidence.professional_source_snapshot AS snapshot
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id
WHERE service.preparation_service_key =
      'negative.round3k.integrated.service.no_protocol'
  AND snapshot.professional_source_snapshot_key =
      'negative.round3k.integrated.snapshot.c';

INSERT INTO ml.professional_training_candidate (
    professional_training_candidate_key, preparation_service_id,
    task_code, professional_rights_decision_id, candidate_status_code,
    provenance_complete, rights_complete, integrity_complete, included
)
SELECT
    'negative.round3k.integrated.training.leak.' || seed.service_suffix,
    service.preparation_service_id, 'DESCRIPTOR_ASSOCIATION',
    rights.professional_rights_decision_id, 'ELIGIBLE',
    TRUE, TRUE, TRUE, TRUE
FROM (VALUES ('core'), ('no_protocol')) AS seed(service_suffix)
JOIN competition.preparation_service AS service
  ON service.preparation_service_key =
     'negative.round3k.integrated.service.' || seed.service_suffix
CROSS JOIN evidence.professional_rights_decision AS rights
WHERE rights.professional_rights_decision_key =
      'negative.round3k.integrated.rights.c';

INSERT INTO ml.professional_split_assignment (
    professional_split_plan_id, professional_training_candidate_id,
    partition_code, assignment_key, deterministic_assignment_sha256
)
SELECT
    plan.professional_split_plan_id,
    candidate.professional_training_candidate_id,
    seed.partition_code,
    'negative.round3k.integrated.assignment.leak.' ||
        seed.service_suffix,
    repeat(seed.hash_character, 64)
FROM (VALUES
    ('core', 'TRAIN', '2'),
    ('no_protocol', 'TEST', '3')
) AS seed(service_suffix, partition_code, hash_character)
CROSS JOIN ml.professional_split_plan AS plan
JOIN ml.professional_training_candidate AS candidate
  ON candidate.professional_training_candidate_key =
     'negative.round3k.integrated.training.leak.' || seed.service_suffix
WHERE plan.professional_split_plan_key =
      'negative.round3k.integrated.split';

SET CONSTRAINTS ALL IMMEDIATE;

SELECT pg_temp.expect_round3k_gate_count(
    'cross_split_coffee_identity_leak_detected',
    $sql$
        SELECT cross_split_coffee_identity_leak_count
        FROM audit.v_round3k_split_leakage
    $sql$,
    1
);

SELECT pg_temp.expect_round3k_gate_count(
    'validation_query_reports_cross_split_coffee_leak',
    $sql$
        SELECT violation_count
        FROM audit.run_round3k_validation_queries()
        WHERE check_key = 'round3k.cross_split_coffee_identity_leaks'
    $sql$,
    1
);

ROLLBACK TO SAVEPOINT round3k_split_leakage_fixture;
RELEASE SAVEPOINT round3k_split_leakage_fixture;
SET CONSTRAINTS ALL DEFERRED;

SELECT pg_temp.expect_round3k_gate_count(
    'round3k_validation_queries_clean_after_leak_rollback',
    $sql$
        SELECT count(*)
        FROM audit.run_round3k_validation_queries()
        WHERE NOT passed
    $sql$,
    0
);

SELECT 'ROUND3K_NEGATIVE_PASS' AS round3k_negative_status;

ROLLBACK;
