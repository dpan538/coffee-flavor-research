\set ON_ERROR_STOP on

BEGIN;

CREATE TEMP TABLE round3i_language_family_stage (
    language_source_family_key TEXT,
    family_name TEXT,
    canonical_origin_key TEXT,
    counts_as_independent BOOLEAN,
    mirror_of_language_source_family_key TEXT,
    counts_as_new_contemporary_family BOOLEAN,
    counts_as_zh_hans_family BOOLEAN,
    historical_baseline BOOLEAN,
    source_authored BOOLEAN,
    admitted BOOLEAN,
    independence_basis TEXT,
    introduced_round TEXT
) ON COMMIT DROP;

\copy round3i_language_family_stage FROM 'db/data/round3i/evaluation/language_source_families.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_family_stage FROM 'db/data/round3i/firstbloom/language_source_families.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_family_stage FROM 'db/data/round3i/zh_hans/language_source_families.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_source_family (
    language_source_family_key, family_name, canonical_origin_key,
    counts_as_independent, mirror_of_language_source_family_key,
    counts_as_new_contemporary_family, counts_as_zh_hans_family,
    historical_baseline, source_authored, admitted,
    independence_basis, introduced_round
)
SELECT
    language_source_family_key, family_name, canonical_origin_key,
    counts_as_independent,
    NULLIF(mirror_of_language_source_family_key, ''),
    counts_as_new_contemporary_family, counts_as_zh_hans_family,
    historical_baseline, source_authored, admitted,
    independence_basis, introduced_round
FROM round3i_language_family_stage
ORDER BY language_source_family_key;

CREATE TEMP TABLE round3i_language_source_stage (
    language_source_key TEXT,
    language_source_family_key TEXT,
    title TEXT,
    authors_or_owner TEXT,
    publication_year INTEGER,
    doi_or_stable_url TEXT,
    repository TEXT,
    exact_version TEXT,
    access_date DATE,
    license_expression TEXT,
    license_url TEXT,
    raw_text_internal_use TEXT,
    raw_text_public_redistribution TEXT,
    derived_expression_internal_use TEXT,
    derived_expression_public_release TEXT,
    derived_counts_internal_use TEXT,
    derived_counts_public_release TEXT,
    model_research_use TEXT,
    rights_basis TEXT,
    rights_review_complete BOOLEAN,
    privacy_decision TEXT,
    privacy_review_complete BOOLEAN,
    source_file_manifest JSONB,
    source_file_hash_complete BOOLEAN,
    language_codes JSONB,
    geography TEXT,
    data_type TEXT,
    evidence_role TEXT,
    limitations TEXT,
    annotation_complete BOOLEAN,
    admitted BOOLEAN
) ON COMMIT DROP;

\copy round3i_language_source_stage FROM 'db/data/round3i/evaluation/language_sources.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_source_stage FROM 'db/data/round3i/firstbloom/language_sources.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_source_stage FROM 'db/data/round3i/zh_hans/language_sources.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_source (
    language_source_key, language_source_family_key, title,
    authors_or_owner, publication_year, doi_or_stable_url,
    repository, exact_version, access_date, license_expression,
    license_url, raw_text_internal_use,
    raw_text_public_redistribution, derived_expression_internal_use,
    derived_expression_public_release, derived_counts_internal_use,
    derived_counts_public_release, model_research_use, rights_basis,
    rights_review_complete, privacy_decision, privacy_review_complete,
    source_file_manifest, source_file_hash_complete, language_codes,
    geography, data_type, evidence_role, limitations,
    annotation_complete, admitted
)
SELECT
    language_source_key, language_source_family_key, title,
    authors_or_owner, publication_year, doi_or_stable_url,
    repository, exact_version, access_date, license_expression,
    license_url, raw_text_internal_use,
    raw_text_public_redistribution, derived_expression_internal_use,
    derived_expression_public_release, derived_counts_internal_use,
    derived_counts_public_release, model_research_use, rights_basis,
    rights_review_complete, privacy_decision, privacy_review_complete,
    source_file_manifest, source_file_hash_complete,
    ARRAY(SELECT jsonb_array_elements_text(language_codes)),
    geography, data_type, evidence_role, limitations,
    annotation_complete, admitted
FROM round3i_language_source_stage
ORDER BY language_source_key;

CREATE TEMP TABLE round3i_language_document_stage (
    language_document_key TEXT,
    language_source_key TEXT,
    language_source_family_key TEXT,
    source_revision TEXT,
    source_date DATE,
    source_row_locator TEXT,
    language_code TEXT,
    document_type TEXT,
    source_content_sha256 TEXT,
    content JSONB,
    raw_text_public_export_allowed BOOLEAN,
    counts_as_new_contemporary_document BOOLEAN,
    counts_as_zh_hans_document BOOLEAN,
    source_authored BOOLEAN,
    machine_translated BOOLEAN,
    artificial_variant BOOLEAN,
    privacy_state TEXT,
    public_export_state TEXT,
    frozen_snapshot BOOLEAN
) ON COMMIT DROP;

\copy round3i_language_document_stage FROM 'db/data/round3i/evaluation/language_documents.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_document_stage FROM 'db/data/round3i/firstbloom/language_documents.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_document_stage FROM 'db/data/round3i/zh_hans/language_documents.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_document (
    language_document_key, language_source_key,
    language_source_family_key, source_revision, source_date,
    source_row_locator, language_code, document_type,
    source_content_sha256, content, raw_text_public_export_allowed,
    counts_as_new_contemporary_document, counts_as_zh_hans_document,
    source_authored, machine_translated, artificial_variant,
    privacy_state, public_export_state, frozen_snapshot
)
SELECT *
FROM round3i_language_document_stage
ORDER BY language_document_key;

CREATE TEMP TABLE round3i_language_expression_stage (
    language_expression_key TEXT,
    language_code TEXT,
    representative_source_phrase TEXT,
    normalized_expression TEXT,
    expression_role TEXT,
    source_authored BOOLEAN,
    machine_translated BOOLEAN,
    artificial_variant BOOLEAN,
    review_state TEXT,
    counts_toward_governed_total BOOLEAN,
    counts_as_zh_hans_sensory_expression BOOLEAN,
    public_export_allowed BOOLEAN,
    limitation TEXT
) ON COMMIT DROP;

\copy round3i_language_expression_stage FROM 'db/data/round3i/evaluation/language_expressions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_expression_stage FROM 'db/data/round3i/firstbloom/language_expressions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_expression_stage FROM 'db/data/round3i/zh_hans/language_expressions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_expression (
    language_expression_key, language_code,
    representative_source_phrase, normalized_expression,
    expression_role, source_authored, machine_translated,
    artificial_variant, review_state, counts_toward_governed_total,
    counts_as_zh_hans_sensory_expression, public_export_allowed,
    limitation
)
SELECT *
FROM round3i_language_expression_stage
ORDER BY language_code, normalized_expression;

CREATE TEMP TABLE round3i_language_occurrence_stage (
    language_occurrence_key TEXT,
    language_document_key TEXT,
    language_expression_key TEXT,
    raw_source_phrase TEXT,
    source_locator TEXT,
    observed_value JSONB
) ON COMMIT DROP;

\copy round3i_language_occurrence_stage FROM 'db/data/round3i/evaluation/language_expression_occurrences.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_occurrence_stage FROM 'db/data/round3i/firstbloom/language_occurrences.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
\copy round3i_language_occurrence_stage FROM 'db/data/round3i/zh_hans/language_occurrences.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_expression_occurrence (
    language_occurrence_key, language_document_key,
    language_expression_key, raw_source_phrase, source_locator,
    observed_value
)
SELECT *
FROM round3i_language_occurrence_stage
ORDER BY language_occurrence_key;

CREATE TEMP TABLE round3i_review_candidate_stage (
    candidate_key TEXT,
    candidate_inventory_sha256 TEXT,
    normalized_expression_sha256 TEXT,
    raw_variant_count INTEGER,
    occurrence_count INTEGER,
    document_count INTEGER,
    raw_surface_hash_inventory_sha256 TEXT,
    source_document_inventory_sha256 TEXT,
    candidate_text_retained BOOLEAN
) ON COMMIT DROP;

\copy round3i_review_candidate_stage FROM 'db/data/round3i/firstbloom/firstbloom_review_candidates_text_free.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_review_candidate (
    candidate_key, candidate_inventory_sha256,
    normalized_expression_sha256, raw_variant_count,
    occurrence_count, document_count,
    raw_surface_hash_inventory_sha256,
    source_document_inventory_sha256, candidate_text_retained
)
SELECT * FROM round3i_review_candidate_stage ORDER BY candidate_key;

CREATE TEMP TABLE round3i_review_decision_stage (
    candidate_review_key TEXT,
    candidate_key TEXT,
    reviewer_key TEXT,
    review_pass TEXT,
    candidate_inventory_sha256 TEXT,
    decision_code TEXT,
    reason_code TEXT,
    reviewed_on DATE,
    human_review BOOLEAN,
    automatic_language_detection BOOLEAN
) ON COMMIT DROP;

\copy round3i_review_decision_stage FROM 'db/data/round3i/firstbloom/firstbloom_review_decisions.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO corpus.language_candidate_review_decision (
    candidate_review_key, candidate_key, reviewer_key, review_pass,
    candidate_inventory_sha256, decision_code, reason_code,
    reviewed_on, human_review, automatic_language_detection
)
SELECT * FROM round3i_review_decision_stage ORDER BY candidate_review_key;

INSERT INTO audit.round3i_acquisition_batch (
    batch_key, targeted_gap, named_sources_reviewed, sources_admitted,
    source_families_added, rows_added, documents_added,
    unique_expressions_added, zh_hans_expressions_added,
    coverage_cells_added, relationship_support_added,
    rights_blocked_count, access_blocked_count, marginal_coverage_gain,
    readiness_state_after, result_path, completed_on
)
VALUES
    ('round3i.batch1.evaluation-language', 'Rights-cleared contemporary coffee evaluation-language families and documents', 3, 3, 3, 11444, 3289, 18, 0, 0, 0, 0, 0, 'HIGH', 'FAMILY_AND_DOCUMENT_GATES_PASS_UNIQUE_EXPRESSION_GAP_REMAINS', 'db/data/round3i/evaluation/batch_result.json', DATE '2026-08-26'),
    ('round3i.batch2.firstbloom-language-expansion', 'TOTAL_GOVERNED_UNIQUE_NORMALIZED_EXPRESSION_COUNT', 1, 1, 0, 1058, 840, 952, 0, 0, 0, 0, 0, 'HIGH', 'LANGUAGE_EXPRESSION_GATE_PENDING_ZH_HANS', 'db/data/round3i/firstbloom/batch_result.json', DATE '2026-08-26'),
    ('round3i.batch3.zh-hans-language-closure', 'SIMPLIFIED_CHINESE_LANGUAGE_FAMILY_AND_DEPTH_GATES', 2, 2, 2, 253, 8, 249, 249, 0, 0, 0, 0, 'HIGH', 'ALL_MANDATORY_LANGUAGE_GATES_PASS', 'db/data/round3i/zh_hans/batch_result.json', DATE '2026-08-26'),
    ('round3i.batch4.relationship-depth', 'RANGE_WITH_CROSS_SOURCE_EVIDENCE_COUNT_PREFERRED', 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 'HIGH', 'ALL_HARD_GATES_AND_FOURTH_RANGE_PREFERRED_GATE_PASS', 'db/data/round3i/relationship/batch_result.json', DATE '2026-08-26');

INSERT INTO evidence.source_family (
    source_family_key, family_name, family_type, canonical_origin_key,
    counts_as_independent, mirror_of_source_family_key,
    independence_basis, admitted, introduced_round
)
VALUES (
    'family.legacy-cotter-consumers',
    'Cotter black-coffee consumer evaluations',
    'CONSUMER_STUDY', 'origin.doi.10.25338/b8993h', TRUE, NULL,
    'Pre-existing independent Dryad consumer-study origin, registered in the relationship-evidence family table without creating a new Round 3I family gain.',
    TRUE, '3H'
);

INSERT INTO evidence.relationship_source (
    source_key, source_family_key, title, authors_or_owner,
    publication_year, doi_or_stable_url, repository, exact_version,
    access_date, source_type, geography, language,
    population_or_panel, sensory_method, preparation_coverage,
    roast_coverage, milk_coverage, license, commercial_use_allowed,
    derivative_use_allowed, redistribution_allowed, machine_use_allowed,
    rights_review_status, privacy_review_status, privacy_decision,
    public_export_decision, file_list, row_count, field_count,
    evidence_role, supported_relationship_keys,
    challenged_relationship_keys, evidence_locator, limitations,
    independence_note, admitted
)
VALUES (
    'dryad.cotter-black-coffee.relationship.v4',
    'family.legacy-cotter-consumers',
    'Consumer preference data for black coffee',
    'Andrew Cotter; William D. Ristenpart; Jean-Xavier Guinard',
    2023, 'https://doi.org/10.25338/B8993H', 'Dryad',
    'Dataset version 4 files published 2023-01-16',
    DATE '2026-08-26', 'CONSUMER_SENSORY_DATASET',
    'Davis, California, United States', 'English',
    '118 ordinary consumers; 3,186 repeated tasting rows',
    'Binary CATA Citrus and 1-5 Acidity JAR adequacy',
    '27 controlled batch-filter brew conditions',
    'One source-reported medium-roast washed Honduras coffee',
    'Black only', 'CC0-1.0', TRUE, TRUE, TRUE, TRUE,
    'CLEARED', 'REVIEWED',
    'PUBLIC_AGGREGATE_ONLY',
    'MIXED_EXTERNAL_RAW_PUBLIC_DERIVED',
    '["file.cotter.relationship-v4.raw","file.cotter.relationship-v4.aggregate"]'::JSONB,
    3186, 48,
    'Correlational support for the acidity-character/citrus relationship',
    ARRAY['membership.acidity-character.citrus'], ARRAY[]::TEXT[],
    'cotter_dataset.csv grouped by Brew; Citrus and Acidity columns',
    'One coffee, repeated consumers, source-local JAR/CATA constructs, and correlational analysis; no causality or general law.',
    'Independent of the Condelli consumer-study family; the Dryad and existing context rows share one Cotter origin and count once.',
    TRUE
);

INSERT INTO evidence.relationship_source_snapshot (
    snapshot_key, source_key, source_family_key, exact_version,
    acquired_at, immutable_locator, snapshot_sha256,
    source_record_count, admitted
)
VALUES (
    'snapshot.dryad-cotter-relationship.v4',
    'dryad.cotter-black-coffee.relationship.v4',
    'family.legacy-cotter-consumers',
    'Dryad version 4 files published 2023-01-16',
    TIMESTAMPTZ '2026-08-26 00:00:00+00',
    'https://datadryad.org/api/v2/files/2041575/download',
    '931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114',
    3186, TRUE
);

INSERT INTO evidence.relationship_source_file (
    file_key, snapshot_key, source_key, source_family_key, filename,
    file_role, locator, license, file_size_bytes, declared_sha256,
    verified_sha256, row_count, field_count, hash_verified,
    contains_participant_identifiers, public_export_decision, local_path
)
VALUES
    ('file.cotter.relationship-v4.raw',
     'snapshot.dryad-cotter-relationship.v4',
     'dryad.cotter-black-coffee.relationship.v4',
     'family.legacy-cotter-consumers', 'cotter_dataset.csv',
     'RAW_EXTERNAL',
     'https://datadryad.org/api/v2/files/2041575/download',
     'CC0-1.0', 542026,
     '931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114',
     '931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114',
     3186, 48, TRUE, TRUE, 'EXTERNAL_ONLY', NULL),
    ('file.cotter.relationship-v4.aggregate',
     'snapshot.dryad-cotter-relationship.v4',
     'dryad.cotter-black-coffee.relationship.v4',
     'family.legacy-cotter-consumers',
     'cotter_brew_acidity_citrus_aggregates.tsv',
     'DERIVED_AGGREGATE',
     'db/data/round3i/relationship/cotter_brew_acidity_citrus_aggregates.tsv',
     'CC0-1.0', 1385,
     'adf26fd10be549b4f4bf74f2e5a45121f85405d1231e874f7cb9a2aecbb3118c',
     'adf26fd10be549b4f4bf74f2e5a45121f85405d1231e874f7cb9a2aecbb3118c',
     27, 5, TRUE, FALSE, 'PUBLIC_AGGREGATE',
     'db/data/round3i/relationship/cotter_brew_acidity_citrus_aggregates.tsv');

CREATE TEMP TABLE round3i_relationship_claim_stage (
    evidence_claim_key TEXT,
    target_entity_type TEXT,
    target_entity_key TEXT,
    source_family_key TEXT,
    source_key TEXT,
    snapshot_key TEXT,
    evidence_basis TEXT,
    evidence_direction TEXT,
    evidence_scope TEXT,
    evidence_locator TEXT,
    method TEXT,
    configuration JSONB,
    support_count INTEGER,
    document_count INTEGER,
    source_diversity INTEGER,
    review_status TEXT,
    limitation TEXT,
    contradictory_evidence_retained BOOLEAN
) ON COMMIT DROP;

\copy round3i_relationship_claim_stage FROM 'db/data/round3i/relationship/relationship_evidence_claims.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO evidence.relationship_evidence_claim (
    evidence_claim_key, target_entity_type, target_entity_key,
    source_family_key, source_key, snapshot_key, evidence_basis,
    evidence_direction, evidence_scope, evidence_locator, method,
    configuration, support_count, document_count, source_diversity,
    review_status, limitation, contradictory_evidence_retained
)
SELECT * FROM round3i_relationship_claim_stage;

UPDATE audit.model_prebuild_range_evidence_summary
SET cross_source_supporting_membership_count = 1,
    supporting_source_families =
        supporting_source_families
        || ARRAY['family.legacy-cotter-consumers'],
    limitation = 'Independent Condelli and Cotter paths support an acidity/citrus relationship; the positive Dryad correlation is non-causal and does not merge Citrus with Acidity or change the source-local membership lifecycle.'
WHERE range_key = 'acidity-character';

COMMIT;
