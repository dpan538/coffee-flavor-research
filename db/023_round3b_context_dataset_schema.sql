\set ON_ERROR_STOP on

-- Round 3B governed source review, frozen snapshot, raw context import,
-- lexical normalization, held-out audit, and statistical sufficiency schema.

BEGIN;

CREATE TABLE ref.context_acquisition_status (
    context_acquisition_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    permits_import BOOLEAN NOT NULL,
    CONSTRAINT context_acquisition_status_pk
        PRIMARY KEY (context_acquisition_status_code),
    CONSTRAINT context_acquisition_status_text_ck CHECK (
        context_acquisition_status_code = lower(btrim(context_acquisition_status_code))
        AND context_acquisition_status_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

INSERT INTO ref.context_acquisition_status VALUES
    ('imported', 'Imported', 'Rights and exact source bytes were verified and frozen.', TRUE),
    ('not_imported_inaccessible', 'Not imported: inaccessible', 'The exact version, rights record, or source bytes could not be acquired and no substitute was invented.', FALSE),
    ('not_imported_rights', 'Not imported: rights', 'The rights gate did not permit durable import.', FALSE),
    ('not_imported_scope', 'Not imported: scope', 'The source was reviewable but outside the approved import scope.', FALSE);

CREATE TABLE ref.context_coffee_mode (
    context_coffee_mode_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT context_coffee_mode_pk PRIMARY KEY (context_coffee_mode_code),
    CONSTRAINT context_coffee_mode_text_ck CHECK (
        context_coffee_mode_code = lower(btrim(context_coffee_mode_code))
        AND context_coffee_mode_code <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND description = btrim(description) AND description <> ''
    )
);

INSERT INTO ref.context_coffee_mode VALUES
    ('black_coffee', 'Black coffee', 'No milk beverage identity is reported for the row.'),
    ('milk_coffee', 'Milk coffee', 'A milk-coffee beverage identity is reported for the row.'),
    ('not_applicable', 'Not applicable', 'The row is not a consumer beverage observation for black/milk analysis.'),
    ('not_reported', 'Not reported', 'The source does not support a black/milk determination.');

CREATE TABLE context.context_source_review (
    context_source_review_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_source_review_key TEXT NOT NULL,
    dataset_id BIGINT,
    source_version_id BIGINT,
    doi TEXT NOT NULL,
    version_label TEXT NOT NULL,
    download_url TEXT NOT NULL,
    license_spdx TEXT NOT NULL,
    commercial_use_allowed BOOLEAN,
    derivative_use_allowed BOOLEAN,
    redistribution_allowed BOOLEAN,
    machine_use_allowed BOOLEAN,
    context_acquisition_status_code TEXT NOT NULL,
    inspected_row_count BIGINT,
    columns JSONB NOT NULL,
    geography TEXT NOT NULL,
    time_period TEXT NOT NULL,
    preparation_coverage TEXT NOT NULL,
    roast_coverage TEXT NOT NULL,
    sensory_coverage TEXT NOT NULL,
    known_limitations TEXT NOT NULL,
    reviewed_on DATE NOT NULL,
    CONSTRAINT context_source_review_pk PRIMARY KEY (context_source_review_id),
    CONSTRAINT context_source_review_key_uq UNIQUE (context_source_review_key),
    CONSTRAINT context_source_review_dataset_fk FOREIGN KEY (dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_source_review_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_source_review_acquisition_fk
        FOREIGN KEY (context_acquisition_status_code)
        REFERENCES ref.context_acquisition_status (context_acquisition_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_source_review_key_ck CHECK (
        context_source_review_key = lower(btrim(context_source_review_key))
        AND context_source_review_key <> ''
    ),
    CONSTRAINT context_source_review_text_ck CHECK (
        doi = btrim(doi) AND doi <> ''
        AND version_label = btrim(version_label) AND version_label <> ''
        AND download_url = btrim(download_url) AND download_url <> ''
        AND license_spdx = btrim(license_spdx) AND license_spdx <> ''
        AND geography = btrim(geography) AND geography <> ''
        AND time_period = btrim(time_period) AND time_period <> ''
        AND preparation_coverage = btrim(preparation_coverage)
        AND preparation_coverage <> ''
        AND roast_coverage = btrim(roast_coverage) AND roast_coverage <> ''
        AND sensory_coverage = btrim(sensory_coverage) AND sensory_coverage <> ''
        AND known_limitations = btrim(known_limitations)
        AND known_limitations <> ''
        AND jsonb_typeof(columns) = 'array'
    ),
    CONSTRAINT context_source_review_import_rights_ck CHECK (
        context_acquisition_status_code <> 'imported'
        OR dataset_id IS NOT NULL
           AND source_version_id IS NOT NULL
           AND commercial_use_allowed
           AND derivative_use_allowed
           AND redistribution_allowed
           AND machine_use_allowed
           AND inspected_row_count IS NOT NULL
    )
);

CREATE TABLE context.context_source_file (
    context_source_file_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_source_file_key TEXT NOT NULL,
    context_source_review_id BIGINT NOT NULL,
    repository_path TEXT NOT NULL,
    canonical_download_url TEXT NOT NULL,
    mirror_download_url TEXT,
    sha256 TEXT NOT NULL,
    byte_count BIGINT NOT NULL,
    row_count BIGINT,
    column_count INTEGER,
    imported_as_context_records BOOLEAN NOT NULL,
    CONSTRAINT context_source_file_pk PRIMARY KEY (context_source_file_id),
    CONSTRAINT context_source_file_key_uq UNIQUE (context_source_file_key),
    CONSTRAINT context_source_file_review_path_uq
        UNIQUE (context_source_review_id, repository_path),
    CONSTRAINT context_source_file_review_fk
        FOREIGN KEY (context_source_review_id)
        REFERENCES context.context_source_review (context_source_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_source_file_text_ck CHECK (
        context_source_file_key = lower(btrim(context_source_file_key))
        AND context_source_file_key <> ''
        AND repository_path = btrim(repository_path) AND repository_path <> ''
        AND canonical_download_url = btrim(canonical_download_url)
        AND canonical_download_url <> ''
        AND (mirror_download_url IS NULL
             OR mirror_download_url = btrim(mirror_download_url)
                AND mirror_download_url <> '')
        AND sha256 ~ '^[0-9a-f]{64}$'
        AND byte_count > 0
        AND (row_count IS NULL OR row_count >= 0)
        AND (column_count IS NULL OR column_count > 0)
    )
);

CREATE TABLE context.context_dataset_snapshot (
    context_dataset_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    snapshot_key TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    normalization_version TEXT NOT NULL,
    code_commit TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    split_seed TEXT NOT NULL,
    case_count INTEGER NOT NULL,
    held_out_case_count INTEGER NOT NULL,
    stratification TEXT NOT NULL,
    is_frozen BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT context_dataset_snapshot_pk
        PRIMARY KEY (context_dataset_snapshot_id),
    CONSTRAINT context_dataset_snapshot_key_uq UNIQUE (snapshot_key),
    CONSTRAINT context_dataset_snapshot_hash_uq UNIQUE (snapshot_hash),
    CONSTRAINT context_dataset_snapshot_text_ck CHECK (
        snapshot_key = lower(btrim(snapshot_key)) AND snapshot_key <> ''
        AND snapshot_hash ~ '^[0-9a-f]{64}$'
        AND normalization_version = lower(btrim(normalization_version))
        AND normalization_version <> ''
        AND code_commit ~ '^[0-9a-f]{40}$'
        AND split_seed = btrim(split_seed) AND split_seed <> ''
        AND stratification = btrim(stratification) AND stratification <> ''
        AND case_count > 0
        AND held_out_case_count > 0
        AND held_out_case_count < case_count
    )
);

CREATE TABLE context.context_dataset_snapshot_source (
    context_dataset_snapshot_id BIGINT NOT NULL,
    context_source_review_id BIGINT NOT NULL,
    CONSTRAINT context_dataset_snapshot_source_pk PRIMARY KEY (
        context_dataset_snapshot_id, context_source_review_id
    ),
    CONSTRAINT context_dataset_snapshot_source_snapshot_fk
        FOREIGN KEY (context_dataset_snapshot_id)
        REFERENCES context.context_dataset_snapshot (context_dataset_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_dataset_snapshot_source_review_fk
        FOREIGN KEY (context_source_review_id)
        REFERENCES context.context_source_review (context_source_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE context.raw_context_record (
    raw_context_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    raw_context_record_key TEXT NOT NULL,
    context_dataset_snapshot_id BIGINT NOT NULL,
    context_source_review_id BIGINT NOT NULL,
    context_source_file_id BIGINT NOT NULL,
    source_row_number BIGINT NOT NULL,
    raw_preparation_label TEXT,
    raw_roast_label TEXT,
    preparation_status_code TEXT NOT NULL,
    normalized_preparation_family_id BIGINT,
    normalized_preparation_leaf_id BIGINT,
    roast_status_code TEXT NOT NULL,
    normalized_roast_category_id BIGINT,
    context_coffee_mode_code TEXT NOT NULL,
    has_sensory_outcome BOOLEAN NOT NULL,
    has_chemical_outcome BOOLEAN NOT NULL,
    has_strong_addition BOOLEAN NOT NULL,
    raw_payload JSONB NOT NULL,
    CONSTRAINT raw_context_record_pk PRIMARY KEY (raw_context_record_id),
    CONSTRAINT raw_context_record_key_uq UNIQUE (raw_context_record_key),
    CONSTRAINT raw_context_record_locator_uq UNIQUE (
        context_source_file_id, source_row_number
    ),
    CONSTRAINT raw_context_record_snapshot_fk
        FOREIGN KEY (context_dataset_snapshot_id)
        REFERENCES context.context_dataset_snapshot (context_dataset_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_review_fk
        FOREIGN KEY (context_source_review_id)
        REFERENCES context.context_source_review (context_source_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_file_fk
        FOREIGN KEY (context_source_file_id)
        REFERENCES context.context_source_file (context_source_file_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_preparation_status_fk
        FOREIGN KEY (preparation_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_preparation_family_fk
        FOREIGN KEY (normalized_preparation_family_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_preparation_leaf_fk
        FOREIGN KEY (normalized_preparation_leaf_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_roast_status_fk
        FOREIGN KEY (roast_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_roast_category_fk
        FOREIGN KEY (normalized_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_mode_fk
        FOREIGN KEY (context_coffee_mode_code)
        REFERENCES ref.context_coffee_mode (context_coffee_mode_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT raw_context_record_text_ck CHECK (
        raw_context_record_key = lower(btrim(raw_context_record_key))
        AND raw_context_record_key <> ''
        AND source_row_number >= 2
        AND (raw_preparation_label IS NULL
             OR raw_preparation_label = btrim(raw_preparation_label)
                AND raw_preparation_label <> '')
        AND (raw_roast_label IS NULL
             OR raw_roast_label = btrim(raw_roast_label)
                AND raw_roast_label <> '')
        AND jsonb_typeof(raw_payload) = 'object'
    ),
    CONSTRAINT raw_context_record_preparation_value_ck CHECK (
        preparation_status_code = 'known'
            AND normalized_preparation_family_id IS NOT NULL
        OR preparation_status_code <> 'known'
            AND normalized_preparation_family_id IS NULL
            AND normalized_preparation_leaf_id IS NULL
    ),
    CONSTRAINT raw_context_record_roast_value_ck CHECK (
        roast_status_code = 'known'
            AND normalized_roast_category_id IS NOT NULL
        OR roast_status_code <> 'known'
            AND normalized_roast_category_id IS NULL
    )
);

CREATE TABLE context.context_lexical_rule (
    context_lexical_rule_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_lexical_rule_key TEXT NOT NULL,
    context_domain TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    normalized_expression TEXT NOT NULL,
    outcome_status_code TEXT NOT NULL,
    normalized_preparation_family_id BIGINT,
    normalized_preparation_leaf_id BIGINT,
    normalized_roast_category_id BIGINT,
    mapping_grade TEXT NOT NULL,
    review_decision_code TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    evidence_locator TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT context_lexical_rule_pk PRIMARY KEY (context_lexical_rule_id),
    CONSTRAINT context_lexical_rule_key_uq UNIQUE (context_lexical_rule_key),
    CONSTRAINT context_lexical_rule_expression_uq UNIQUE (
        context_domain, language_tag_code, normalized_expression
    ),
    CONSTRAINT context_lexical_rule_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_status_fk FOREIGN KEY (outcome_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_family_fk
        FOREIGN KEY (normalized_preparation_family_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_leaf_fk
        FOREIGN KEY (normalized_preparation_leaf_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_roast_fk
        FOREIGN KEY (normalized_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_review_fk
        FOREIGN KEY (review_decision_code)
        REFERENCES ref.review_decision (review_decision_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_lifecycle_fk
        FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_lexical_rule_text_ck CHECK (
        context_lexical_rule_key = lower(btrim(context_lexical_rule_key))
        AND context_lexical_rule_key <> ''
        AND context_domain IN ('preparation', 'roast')
        AND normalized_expression = lower(btrim(normalized_expression))
        AND normalized_expression <> ''
        AND mapping_grade = lower(btrim(mapping_grade)) AND mapping_grade <> ''
        AND evidence_locator = btrim(evidence_locator) AND evidence_locator <> ''
    ),
    CONSTRAINT context_lexical_rule_target_ck CHECK (
        context_domain = 'preparation'
          AND (
              outcome_status_code = 'known'
              AND normalized_preparation_family_id IS NOT NULL
              AND normalized_roast_category_id IS NULL
              OR outcome_status_code = 'reported_unresolved'
              AND normalized_preparation_family_id IS NULL
              AND normalized_preparation_leaf_id IS NULL
              AND normalized_roast_category_id IS NULL
          )
        OR context_domain = 'roast'
          AND normalized_preparation_family_id IS NULL
          AND normalized_preparation_leaf_id IS NULL
          AND (
              outcome_status_code = 'known'
              AND normalized_roast_category_id IS NOT NULL
              OR outcome_status_code = 'reported_unresolved'
              AND normalized_roast_category_id IS NULL
          )
    ),
    CONSTRAINT context_lexical_rule_review_target_ck CHECK (
        outcome_status_code <> 'known' OR review_decision_code = 'approved'
    )
);

CREATE TABLE context.roast_mapping_approval (
    roast_mapping_approval_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_lexical_rule_id BIGINT NOT NULL,
    normalized_roast_category_id BIGINT NOT NULL,
    source_version_id BIGINT NOT NULL,
    reviewer_receipt TEXT NOT NULL,
    approved_on DATE NOT NULL,
    CONSTRAINT roast_mapping_approval_pk PRIMARY KEY (roast_mapping_approval_id),
    CONSTRAINT roast_mapping_approval_fact_uq UNIQUE (
        context_lexical_rule_id, normalized_roast_category_id
    ),
    CONSTRAINT roast_mapping_approval_rule_fk
        FOREIGN KEY (context_lexical_rule_id)
        REFERENCES context.context_lexical_rule (context_lexical_rule_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_mapping_approval_category_fk
        FOREIGN KEY (normalized_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_mapping_approval_source_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_mapping_approval_receipt_ck CHECK (
        reviewer_receipt = btrim(reviewer_receipt) AND reviewer_receipt <> ''
    )
);

CREATE TABLE context.context_normalization_benchmark (
    context_normalization_benchmark_id BIGINT GENERATED ALWAYS AS IDENTITY,
    benchmark_key TEXT NOT NULL,
    context_dataset_snapshot_id BIGINT NOT NULL,
    split_seed TEXT NOT NULL,
    snapshot_hash TEXT NOT NULL,
    case_count INTEGER NOT NULL,
    held_out_case_count INTEGER NOT NULL,
    stratification TEXT NOT NULL,
    frozen_before_rule_evaluation BOOLEAN NOT NULL,
    CONSTRAINT context_normalization_benchmark_pk
        PRIMARY KEY (context_normalization_benchmark_id),
    CONSTRAINT context_normalization_benchmark_key_uq UNIQUE (benchmark_key),
    CONSTRAINT context_normalization_benchmark_snapshot_fk
        FOREIGN KEY (context_dataset_snapshot_id)
        REFERENCES context.context_dataset_snapshot (context_dataset_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_benchmark_text_ck CHECK (
        benchmark_key = lower(btrim(benchmark_key)) AND benchmark_key <> ''
        AND split_seed = btrim(split_seed) AND split_seed <> ''
        AND snapshot_hash ~ '^[0-9a-f]{64}$'
        AND case_count > 0
        AND held_out_case_count > 0
        AND held_out_case_count < case_count
        AND stratification = btrim(stratification) AND stratification <> ''
    )
);

CREATE TABLE context.context_normalization_case (
    context_normalization_case_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_normalization_case_key TEXT NOT NULL,
    context_normalization_benchmark_id BIGINT NOT NULL,
    context_domain TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    raw_expression TEXT NOT NULL,
    expected_status_code TEXT NOT NULL,
    expected_preparation_family_id BIGINT,
    expected_preparation_leaf_id BIGINT,
    expected_roast_category_id BIGINT,
    evaluation_split TEXT NOT NULL,
    stratum TEXT NOT NULL,
    split_hash_prefix TEXT NOT NULL,
    notes TEXT NOT NULL,
    CONSTRAINT context_normalization_case_pk
        PRIMARY KEY (context_normalization_case_id),
    CONSTRAINT context_normalization_case_key_uq
        UNIQUE (context_normalization_case_key),
    CONSTRAINT context_normalization_case_benchmark_fk
        FOREIGN KEY (context_normalization_benchmark_id)
        REFERENCES context.context_normalization_benchmark
            (context_normalization_benchmark_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_case_language_fk
        FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_case_status_fk
        FOREIGN KEY (expected_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_case_family_fk
        FOREIGN KEY (expected_preparation_family_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_case_leaf_fk
        FOREIGN KEY (expected_preparation_leaf_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_case_roast_fk
        FOREIGN KEY (expected_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_case_text_ck CHECK (
        context_normalization_case_key = lower(btrim(context_normalization_case_key))
        AND context_normalization_case_key <> ''
        AND context_domain IN ('preparation', 'roast')
        AND raw_expression = btrim(raw_expression) AND raw_expression <> ''
        AND evaluation_split IN ('development', 'held_out')
        AND stratum = btrim(stratum) AND stratum <> ''
        AND split_hash_prefix ~ '^[0-9a-f]{16}$'
        AND notes = btrim(notes) AND notes <> ''
    )
);

CREATE TABLE context.context_normalization_result (
    context_normalization_result_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_normalization_case_id BIGINT NOT NULL,
    predicted_status_code TEXT NOT NULL,
    predicted_preparation_family_id BIGINT,
    predicted_preparation_leaf_id BIGINT,
    predicted_roast_category_id BIGINT,
    evaluation_grade TEXT NOT NULL,
    ordinal_error SMALLINT,
    gross_error BOOLEAN NOT NULL,
    mapping_grade TEXT NOT NULL,
    normalization_version TEXT NOT NULL,
    CONSTRAINT context_normalization_result_pk
        PRIMARY KEY (context_normalization_result_id),
    CONSTRAINT context_normalization_result_case_uq
        UNIQUE (context_normalization_case_id),
    CONSTRAINT context_normalization_result_case_fk
        FOREIGN KEY (context_normalization_case_id)
        REFERENCES context.context_normalization_case
            (context_normalization_case_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_result_status_fk
        FOREIGN KEY (predicted_status_code)
        REFERENCES ref.context_value_status (context_value_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_result_family_fk
        FOREIGN KEY (predicted_preparation_family_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_result_leaf_fk
        FOREIGN KEY (predicted_preparation_leaf_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_result_roast_fk
        FOREIGN KEY (predicted_roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_normalization_result_text_ck CHECK (
        evaluation_grade IN ('3', '2', '1', '0', 'U', 'exact', 'adjacent', 'incorrect')
        AND (ordinal_error IS NULL OR ordinal_error >= 0)
        AND mapping_grade = lower(btrim(mapping_grade)) AND mapping_grade <> ''
        AND normalization_version = lower(btrim(normalization_version))
        AND normalization_version <> ''
    )
);

CREATE TABLE audit.context_statistic (
    context_statistic_id BIGINT GENERATED ALWAYS AS IDENTITY,
    context_statistic_key TEXT NOT NULL,
    context_dataset_snapshot_id BIGINT NOT NULL,
    statistic_group TEXT NOT NULL,
    statistic_value JSONB NOT NULL,
    research_question TEXT NOT NULL,
    input_data TEXT NOT NULL,
    assumptions TEXT NOT NULL,
    output_interpretation TEXT NOT NULL,
    limitations TEXT NOT NULL,
    CONSTRAINT context_statistic_pk PRIMARY KEY (context_statistic_id),
    CONSTRAINT context_statistic_key_uq UNIQUE (context_statistic_key),
    CONSTRAINT context_statistic_snapshot_fk
        FOREIGN KEY (context_dataset_snapshot_id)
        REFERENCES context.context_dataset_snapshot (context_dataset_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT context_statistic_text_ck CHECK (
        context_statistic_key = lower(btrim(context_statistic_key))
        AND context_statistic_key <> ''
        AND statistic_group = lower(btrim(statistic_group))
        AND statistic_group <> ''
        AND jsonb_typeof(statistic_value) IN ('object', 'array', 'number', 'string', 'boolean')
        AND research_question = btrim(research_question) AND research_question <> ''
        AND input_data = btrim(input_data) AND input_data <> ''
        AND assumptions = btrim(assumptions) AND assumptions <> ''
        AND output_interpretation = btrim(output_interpretation)
        AND output_interpretation <> ''
        AND limitations = btrim(limitations) AND limitations <> ''
    )
);

CREATE FUNCTION context.enforce_raw_context_targets()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_raw_context_targets$
DECLARE
    family_is_valid BOOLEAN;
    leaf_is_valid BOOLEAN;
    roast_is_current BOOLEAN;
    file_review_id BIGINT;
BEGIN
    SELECT file.context_source_review_id
    INTO file_review_id
    FROM context.context_source_file AS file
    WHERE file.context_source_file_id = NEW.context_source_file_id;
    IF file_review_id IS DISTINCT FROM NEW.context_source_review_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'raw_context_record_file_review_ck',
            MESSAGE = 'raw_context_record_file_review_ck: file and source review must agree';
    END IF;

    IF NEW.normalized_preparation_family_id IS NOT NULL THEN
        SELECT concept.preparation_concept_type_code = 'family'
               AND concept.lifecycle_status_code = 'active'
        INTO family_is_valid
        FROM context.preparation_concept AS concept
        WHERE concept.preparation_concept_id =
              NEW.normalized_preparation_family_id;
        IF family_is_valid IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'raw_context_record_family_target_ck',
                MESSAGE = 'raw_context_record_family_target_ck: normalized preparation family must be an active family';
        END IF;
    END IF;

    IF NEW.normalized_preparation_leaf_id IS NOT NULL THEN
        WITH RECURSIVE descendants(preparation_concept_id) AS (
            SELECT relation.object_preparation_concept_id
            FROM context.preparation_relation AS relation
            WHERE relation.subject_preparation_concept_id =
                  NEW.normalized_preparation_family_id
              AND relation.context_relation_type_code = 'broader_than'
              AND relation.lifecycle_status_code = 'active'
            UNION
            SELECT relation.object_preparation_concept_id
            FROM descendants
            JOIN context.preparation_relation AS relation
              ON relation.subject_preparation_concept_id =
                 descendants.preparation_concept_id
            WHERE relation.context_relation_type_code = 'broader_than'
              AND relation.lifecycle_status_code = 'active'
        )
        SELECT EXISTS (
            SELECT 1 FROM descendants
            WHERE preparation_concept_id = NEW.normalized_preparation_leaf_id
        ) INTO leaf_is_valid;
        IF leaf_is_valid IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'raw_context_record_leaf_family_ck',
                MESSAGE = 'raw_context_record_leaf_family_ck: normalized leaf must descend from the selected family';
        END IF;
    END IF;

    IF NEW.normalized_roast_category_id IS NOT NULL THEN
        SELECT scheme.is_project_normalized_target
               AND scheme.lifecycle_status_code = 'active'
               AND category.lifecycle_status_code = 'active'
        INTO roast_is_current
        FROM context.roast_category AS category
        JOIN context.roast_scheme AS scheme
          ON scheme.roast_scheme_id = category.roast_scheme_id
        WHERE category.roast_category_id = NEW.normalized_roast_category_id;
        IF roast_is_current IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'raw_context_record_current_roast_ck',
                MESSAGE = 'raw_context_record_current_roast_ck: normalized roast must belong to the current user scheme';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_raw_context_targets$;

CREATE TRIGGER raw_context_record_targets_biu
BEFORE INSERT OR UPDATE ON context.raw_context_record
FOR EACH ROW EXECUTE FUNCTION context.enforce_raw_context_targets();

CREATE FUNCTION context.enforce_protected_roast_abstention()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_protected_roast_abstention$
DECLARE
    approval_exists BOOLEAN;
BEGIN
    IF NEW.context_domain = 'roast'
       AND NEW.normalized_roast_category_id IS NOT NULL
       AND NEW.normalized_expression IN (
           'filter roast', 'espresso roast', 'omniroast', 'nordic roast',
           'city roast', 'city+', 'full city', 'full city roast',
           'vienna roast', 'french roast', 'italian roast', 'roasted'
       ) THEN
        SELECT EXISTS (
            SELECT 1
            FROM context.roast_mapping_approval AS approval
            WHERE approval.context_lexical_rule_id =
                  NEW.context_lexical_rule_id
              AND approval.normalized_roast_category_id =
                  NEW.normalized_roast_category_id
        ) INTO approval_exists;
        IF approval_exists IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'protected_roast_mapping_approval_ck',
                MESSAGE = 'protected_roast_mapping_approval_ck: brew-intent and unstable trade/style labels require an explicit approval receipt before darkness mapping';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_protected_roast_abstention$;

CREATE TRIGGER context_lexical_rule_protected_roast_biu
BEFORE INSERT OR UPDATE ON context.context_lexical_rule
FOR EACH ROW EXECUTE FUNCTION context.enforce_protected_roast_abstention();

CREATE FUNCTION context.protect_frozen_context_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_context_snapshot$
BEGIN
    IF OLD.is_frozen THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'frozen_context_snapshot_immutable_ck',
            MESSAGE = 'frozen_context_snapshot_immutable_ck: frozen snapshot metadata cannot be modified or deleted';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$protect_frozen_context_snapshot$;

CREATE TRIGGER context_dataset_snapshot_frozen_bud
BEFORE UPDATE OR DELETE ON context.context_dataset_snapshot
FOR EACH ROW EXECUTE FUNCTION context.protect_frozen_context_snapshot();

CREATE FUNCTION context.protect_frozen_raw_context_record()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_raw_context_record$
DECLARE
    snapshot_is_frozen BOOLEAN;
BEGIN
    SELECT snapshot.is_frozen
    INTO snapshot_is_frozen
    FROM context.context_dataset_snapshot AS snapshot
    WHERE snapshot.context_dataset_snapshot_id =
          OLD.context_dataset_snapshot_id;
    IF snapshot_is_frozen THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'frozen_raw_context_record_immutable_ck',
            MESSAGE = 'frozen_raw_context_record_immutable_ck: imported rows in a frozen snapshot cannot be modified or deleted';
    END IF;
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$protect_frozen_raw_context_record$;

CREATE TRIGGER raw_context_record_frozen_bud
BEFORE UPDATE OR DELETE ON context.raw_context_record
FOR EACH ROW EXECUTE FUNCTION context.protect_frozen_raw_context_record();

CREATE INDEX context_source_file_hash_idx
    ON context.context_source_file (sha256);
CREATE INDEX raw_context_record_snapshot_source_idx
    ON context.raw_context_record (
        context_dataset_snapshot_id, context_source_review_id
    );
CREATE INDEX raw_context_record_preparation_idx
    ON context.raw_context_record (
        normalized_preparation_family_id, preparation_status_code
    );
CREATE INDEX raw_context_record_roast_idx
    ON context.raw_context_record (
        normalized_roast_category_id, roast_status_code
    );
CREATE INDEX context_normalization_case_split_idx
    ON context.context_normalization_case (
        context_normalization_benchmark_id, context_domain, evaluation_split
    );

COMMIT;
