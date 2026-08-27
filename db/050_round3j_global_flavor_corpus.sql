\set ON_ERROR_STOP on

-- Round 3J global flavor-corpus checkpoint. These audit relations are additive
-- and do not mutate the frozen coffee-sensory-research-db-v0.1.0 surfaces.
BEGIN;

CREATE TABLE audit.round3j_global_flavor_document (
    document_key TEXT PRIMARY KEY,
    source_family_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_version TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_file_sha256 TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_date TEXT NOT NULL,
    source_geography TEXT NOT NULL,
    market_geography TEXT NOT NULL,
    language_tag TEXT NOT NULL,
    script TEXT NOT NULL,
    evidence_register TEXT NOT NULL,
    coffee_or_product_identity_key TEXT NOT NULL,
    source_authored BOOLEAN NOT NULL,
    license_expression TEXT NOT NULL,
    rights_state TEXT NOT NULL,
    privacy_state TEXT NOT NULL,
    model_research_allowed BOOLEAN NOT NULL,
    public_derived_release_allowed BOOLEAN NOT NULL,
    upstream_source_family_key TEXT NOT NULL,
    duplicate_group_key TEXT,
    admission_state TEXT NOT NULL,
    training_eligibility_state TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT round3j_global_document_text_ck CHECK (
        document_key = lower(btrim(document_key))
        AND document_key <> ''
        AND source_family_key = lower(btrim(source_family_key))
        AND source_key = lower(btrim(source_key))
        AND source_file_sha256 ~ '^[0-9a-f]{64}$'
        AND source_url ~ '^https://'
        AND source_authored
    ),
    CONSTRAINT round3j_global_document_register_ck CHECK (
        evidence_register IN (
            'CONSUMER_FREE_TEXT',
            'CONSUMER_STRUCTURED_SENSORY',
            'PROFESSIONAL_PRODUCT_NOTE',
            'TRAINED_PANEL',
            'Q_GRADER_OR_COMPETITION',
            'AUCTION_OR_JURY',
            'AUTHOR_TASTING_PROSE',
            'STRUCTURED_PRODUCT_LABEL'
        )
    ),
    CONSTRAINT round3j_global_document_admission_ck CHECK (
        admission_state IN ('ADMIT_RAW_AND_DERIVED', 'ADMIT_DERIVED_ONLY')
        AND rights_state = 'CLEARED'
        AND model_research_allowed
        AND training_eligibility_state = 'ELIGIBLE_UNRESOLVED'
    )
);

CREATE TABLE audit.round3j_global_flavor_occurrence (
    occurrence_key TEXT PRIMARY KEY,
    document_key TEXT NOT NULL REFERENCES audit.round3j_global_flavor_document(document_key),
    source_family_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_version TEXT NOT NULL,
    raw_source_phrase TEXT NOT NULL,
    normalized_expression TEXT NOT NULL,
    language_tag TEXT NOT NULL,
    script TEXT NOT NULL,
    expression_role TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    source_authored BOOLEAN NOT NULL,
    deterministic_normalization TEXT NOT NULL,
    machine_translated BOOLEAN NOT NULL,
    project_translation BOOLEAN NOT NULL,
    preference_evidence BOOLEAN NOT NULL,
    label_disposition TEXT NOT NULL,
    candidate_target_keys TEXT NOT NULL,
    review_state TEXT NOT NULL,
    training_eligible BOOLEAN NOT NULL,
    duplicate_group_key TEXT,
    duplicate_reason TEXT NOT NULL,
    rights_state TEXT NOT NULL,
    privacy_state TEXT NOT NULL,
    provenance_complete BOOLEAN NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT round3j_global_occurrence_text_ck CHECK (
        occurrence_key = lower(btrim(occurrence_key))
        AND raw_source_phrase = btrim(raw_source_phrase)
        AND raw_source_phrase <> ''
        AND normalized_expression = btrim(normalized_expression)
        AND normalized_expression <> ''
        AND source_locator = btrim(source_locator)
        AND source_locator <> ''
    ),
    CONSTRAINT round3j_global_occurrence_authorship_ck CHECK (
        source_authored
        AND NOT machine_translated
        AND NOT project_translation
        AND NOT preference_evidence
        AND rights_state = 'CLEARED'
        AND review_state = 'SOURCE_REVIEWED'
        AND provenance_complete
    ),
    CONSTRAINT round3j_global_occurrence_label_ck CHECK (
        label_disposition = 'UNRESOLVED'
        AND candidate_target_keys = '[]'
        AND training_eligible
    ),
    CONSTRAINT round3j_global_occurrence_role_ck CHECK (
        expression_role IN (
            'SENSORY_ATTRIBUTE', 'COMPOSITE_REFERENCE', 'QUALIFIER',
            'BASIC_TASTE', 'AROMA_REFERENCE', 'TEXTURE',
            'DEFECT_OR_NEGATIVE_CHARACTER', 'PROCESS_LANGUAGE',
            'PREPARATION_LANGUAGE', 'ROAST_LANGUAGE',
            'AFFECTIVE_OR_LIKING', 'CONSUMER_METAPHOR',
            'UNRESOLVED', 'OUT_OF_SCOPE'
        )
    )
);

CREATE TABLE audit.round3j_global_source_class_result (
    source_class TEXT PRIMARY KEY,
    named_candidate_rows_reviewed INTEGER NOT NULL,
    independent_candidate_families_counted INTEGER NOT NULL,
    coverage_gate_pass BOOLEAN NOT NULL,
    admitted_new_source_family_count INTEGER NOT NULL,
    targeted_no_material_gain_batch_count INTEGER NOT NULL,
    saturated BOOLEAN NOT NULL,
    blocked BOOLEAN NOT NULL,
    closure_state TEXT NOT NULL,
    evidence_backed_explanation TEXT NOT NULL,
    CONSTRAINT round3j_global_source_class_key_ck CHECK (
        source_class IN ('A','B','C','D','E','F','G','H','I')
    ),
    CONSTRAINT round3j_global_source_class_counts_ck CHECK (
        named_candidate_rows_reviewed >= independent_candidate_families_counted
        AND independent_candidate_families_counted >= 0
        AND admitted_new_source_family_count >= 0
        AND targeted_no_material_gain_batch_count >= 0
        AND NOT saturated
    )
);

CREATE TABLE audit.round3j_global_corpus_metric (
    metric TEXT PRIMARY KEY,
    value BIGINT NOT NULL,
    counting_boundary TEXT NOT NULL,
    CONSTRAINT round3j_global_metric_text_ck CHECK (
        metric = upper(btrim(metric)) AND metric <> ''
        AND counting_boundary = btrim(counting_boundary)
        AND counting_boundary <> ''
        AND value >= 0
    )
);

CREATE TEMP TABLE round3j_global_document_stage
(LIKE audit.round3j_global_flavor_document INCLUDING DEFAULTS);
\copy round3j_global_document_stage FROM 'db/data/round3j/global-corpus/ADMITTED_FLAVOR_DOCUMENT.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
INSERT INTO audit.round3j_global_flavor_document
SELECT * FROM round3j_global_document_stage ORDER BY document_key;

CREATE TEMP TABLE round3j_global_occurrence_stage
(LIKE audit.round3j_global_flavor_occurrence INCLUDING DEFAULTS);
\copy round3j_global_occurrence_stage FROM 'db/data/round3j/global-corpus/ADMITTED_FLAVOR_EXPRESSION_OCCURRENCE.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
INSERT INTO audit.round3j_global_flavor_occurrence
SELECT * FROM round3j_global_occurrence_stage ORDER BY occurrence_key;

CREATE TEMP TABLE round3j_global_source_class_stage
(LIKE audit.round3j_global_source_class_result INCLUDING DEFAULTS);
\copy round3j_global_source_class_stage FROM 'db/data/round3j/global-corpus/SOURCE_CLASS_SATURATION.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
INSERT INTO audit.round3j_global_source_class_result
SELECT * FROM round3j_global_source_class_stage ORDER BY source_class;

CREATE TEMP TABLE round3j_global_metric_stage
(LIKE audit.round3j_global_corpus_metric INCLUDING DEFAULTS);
\copy round3j_global_metric_stage FROM 'db/data/round3j/global-corpus/GLOBAL_FLAVOR_CORPUS_METRIC.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')
INSERT INTO audit.round3j_global_corpus_metric
SELECT * FROM round3j_global_metric_stage ORDER BY metric;

DO $round3j_global_seed_gate$
BEGIN
    IF (SELECT count(*) FROM audit.round3j_global_flavor_document) <> 6
       OR (SELECT count(*) FROM audit.round3j_global_flavor_occurrence) <> 37
       OR (SELECT count(DISTINCT normalized_expression)
           FROM audit.round3j_global_flavor_occurrence) <> 37
       OR (SELECT count(*) FROM audit.round3j_global_source_class_result) <> 9
       OR EXISTS (
           SELECT 1 FROM audit.round3j_global_source_class_result
           WHERE saturated
       ) THEN
        RAISE EXCEPTION 'Round 3J global seed contract failed';
    END IF;
END
$round3j_global_seed_gate$;

COMMIT;
