\set ON_ERROR_STOP on

-- Round 3B exact-source metadata, snapshot, 4,817 raw context rows, reviewed
-- lexical rules, frozen benchmark, held-out results, and sufficiency record.

BEGIN;

INSERT INTO evidence.license_policy (
    license_policy_key, access_class_code, rights_status_code,
    redistributable, derivative_work_allowed, commercial_use_allowed,
    machine_use_allowed, production_export_allowed, checked_on, notes
)
VALUES (
    'license.dryad_cc0_context_data.round3b_v1',
    'public', 'verified', TRUE, TRUE, TRUE, TRUE, TRUE,
    DATE '2026-08-25',
    'Dryad API metadata identifies CC0-1.0. Exact files were obtained from the official Zenodo DOI mirrors and match Dryad byte counts and SHA-256 values.'
);

INSERT INTO evidence.source (
    source_key, title, creator, publisher, citation, doi, source_url,
    external_metadata
)
VALUES (
    'source.dryad_yeager_2021_acids_meta_analysis_exact',
    'Acids in Coffee - A Review of Sensory Measurements and Meta-Analysis of Chemical Composition',
    'Sara Yeager', 'Dryad',
    'Yeager S. Acids in Coffee - A Review of Sensory Measurements and Meta-Analysis of Chemical Composition [Dataset]. Dryad. 2021.',
    '10.25338/B8C91C',
    'https://datadryad.org/dataset/doi%3A10.25338/B8C91C',
    '{"dryad_dataset_id":69447,"corrects_round3a_candidate_attribution":true}'::JSONB
);

INSERT INTO evidence.source_version (
    source_version_key, source_id, license_policy_id, version_label,
    published_on, retrieved_on, version_locator, external_metadata
)
SELECT
    version.source_version_key,
    source.source_id,
    policy.license_policy_id,
    version.version_label,
    version.published_on,
    DATE '2026-08-25',
    version.version_locator,
    version.external_metadata
FROM (VALUES
    (
        'source_version.dryad_cotter_black_coffee.version_4.215645',
        'source.dryad_cotter_2020_black_coffee',
        'Dryad version 4; version id 215645',
        DATE '2023-01-16',
        'https://datadryad.org/api/v2/versions/215645',
        '{"dryad_dataset_id":91366,"dryad_version_id":215645,"dryad_version_number":4,"license":"CC0-1.0"}'::JSONB
    ),
    (
        'source_version.dryad_yeager_acids.version_5.130006',
        'source.dryad_yeager_2021_acids_meta_analysis_exact',
        'Dryad version 5; version id 130006',
        DATE '2021-07-14',
        'https://datadryad.org/api/v2/versions/130006',
        '{"dryad_dataset_id":69447,"dryad_version_id":130006,"dryad_version_number":5,"license":"CC0-1.0"}'::JSONB
    )
) AS version(
    source_version_key, source_key, version_label, published_on,
    version_locator, external_metadata
)
JOIN evidence.source AS source ON source.source_key = version.source_key
CROSS JOIN evidence.license_policy AS policy
WHERE policy.license_policy_key =
      'license.dryad_cc0_context_data.round3b_v1';

INSERT INTO evidence.dataset (
    dataset_key, source_version_id, name, description, external_metadata
)
SELECT
    dataset.dataset_key,
    source_version.source_version_id,
    dataset.name,
    dataset.description,
    dataset.external_metadata
FROM (VALUES
    (
        'dataset.cotter_black_coffee.version_4.215645',
        'source_version.dryad_cotter_black_coffee.version_4.215645',
        'Consumer preference data for black coffee — exact version 4',
        'Rights-cleared 3,186-row consumer sensory dataset. Preparation and roast are fixed at dataset level, so it cannot identify their effects.',
        '{"row_count":3186,"column_count":48,"preparation_scope":"batch filter","roast_scope":"medium","coffee_mode":"black","sensory_outcomes":true}'::JSONB
    ),
    (
        'dataset.yeager_acids.version_5.130006',
        'source_version.dryad_yeager_acids.version_5.130006',
        'Coffee acid meta-analysis — exact version 5',
        'Rights-cleared chemistry meta-analysis with 1,631 source rows across the two measurement files. Context varies, but outcomes are chemical rather than sensory.',
        '{"row_count":1631,"context_data_files":2,"preparation_varies":true,"roast_varies":true,"sensory_outcomes":false}'::JSONB
    )
) AS dataset(
    dataset_key, source_version_key, name, description, external_metadata
)
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = dataset.source_version_key;

INSERT INTO context.context_source_review (
    context_source_review_key, dataset_id, source_version_id, doi,
    version_label, download_url, license_spdx, commercial_use_allowed,
    derivative_use_allowed, redistribution_allowed, machine_use_allowed,
    context_acquisition_status_code, inspected_row_count, columns,
    geography, time_period, preparation_coverage, roast_coverage,
    sensory_coverage, known_limitations, reviewed_on
)
SELECT
    review.review_key,
    dataset.dataset_id,
    source_version.source_version_id,
    review.doi,
    review.version_label,
    review.download_url,
    review.license_spdx,
    review.commercial_use_allowed,
    review.derivative_use_allowed,
    review.redistribution_allowed,
    review.machine_use_allowed,
    review.acquisition_status,
    review.row_count,
    review.columns,
    review.geography,
    review.time_period,
    review.preparation_coverage,
    review.roast_coverage,
    review.sensory_coverage,
    review.known_limitations,
    DATE '2026-08-25'
FROM (VALUES
    (
        'context.source_review.dryad_cotter_black_coffee.v4',
        'dataset.cotter_black_coffee.version_4.215645',
        'source_version.dryad_cotter_black_coffee.version_4.215645',
        '10.25338/B8993H', 'Dryad version 4; version id 215645',
        'https://datadryad.org/dataset/doi%3A10.25338/B8993H',
        'CC0-1.0', TRUE, TRUE, TRUE, TRUE, 'imported', 3186::BIGINT,
        '["Judge","Cluster","Week","Session Number","Position","Brew","Temp.x","TDS.x","PE.x","Dose","Setting","Grind","Empty Carafe","Full Carafe","Brew Mass","TDS__1","Percent Extraction","pH","Initial NaOH","Final NaOH","Titration pH","Volume","Brew Temperature","Pour Temp","90Sec Temp","Liking","Temp","Flavor.intensity","Acidity","Mouthfeel","Tea.floral","Fruit","Citrus","Green.veg","Paper.wood","Burnt","Cereal","Nutty","Dark.chocolate","Caramel","Bitter","Astringent","Roasted","Sour","Thick.viscous","Sweet","Rubber","Purchase.intent"]'::JSONB,
        'Sensory sessions at UC Davis, United States; one washed Honduras coffee.',
        'Study sessions reported by the source; dataset published 2023-01-16.',
        'Dataset-level drip/batch-filter black coffee; preparation does not vary.',
        'Dataset-level medium roast; roast does not vary.',
        'Consumer liking, JAR ratings, and 17 binary CATA attributes.',
        'The landing-page prose contains a 3,168-row typo; the exact CSV contains 3,186 rows, matching the stated 118 by 27 design.'
    ),
    (
        'context.source_review.dryad_yeager_acids.v5',
        'dataset.yeager_acids.version_5.130006',
        'source_version.dryad_yeager_acids.version_5.130006',
        '10.25338/B8C91C', 'Dryad version 5; version id 130006',
        'https://datadryad.org/dataset/doi%3A10.25338/B8C91C',
        'CC0-1.0', TRUE, TRUE, TRUE, TRUE, 'imported', 1631::BIGINT,
        '["Source","Type","Roast","Extraction","Stat/Stats","Other","Units","acid measurements","Notes"]'::JSONB,
        'A 121-publication meta-analysis; geography is heterogeneous and not one sampling frame.',
        'Underlying publications were reviewed April-December 2020; exact dataset version published 2021-07-14.',
        'Source labels include immersion, espresso, filter, French press, drip, cold brew, laboratory extraction, instant, and unresolved terms.',
        'Source labels include light, medium, dark, green, roasted, steamed, and unspecified.',
        'No sensory outcome rows; chemical acid concentrations only.',
        'The source harmonized roast descriptions into approximate classes. Wide files contain trailing empty columns; only named columns are imported into row JSON.'
    )
) AS review(
    review_key, dataset_key, source_version_key, doi, version_label,
    download_url, license_spdx, commercial_use_allowed,
    derivative_use_allowed, redistribution_allowed, machine_use_allowed,
    acquisition_status, row_count, columns, geography, time_period,
    preparation_coverage, roast_coverage, sensory_coverage, known_limitations
)
JOIN evidence.dataset AS dataset ON dataset.dataset_key = review.dataset_key
JOIN evidence.source_version AS source_version
  ON source_version.source_version_key = review.source_version_key;

INSERT INTO context.context_source_review (
    context_source_review_key, doi, version_label, download_url,
    license_spdx, commercial_use_allowed, derivative_use_allowed,
    redistribution_allowed, machine_use_allowed,
    context_acquisition_status_code, inspected_row_count, columns,
    geography, time_period, preparation_coverage, roast_coverage,
    sensory_coverage, known_limitations, reviewed_on
)
VALUES (
    'context.source_review.dryad_liang_immersion.unavailable_20260825',
    '10.5061/dryad.v15dv423h',
    'No accessible Dryad version on 2026-08-25',
    'https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.v15dv423h',
    'UNVERIFIED_FOR_INACCESSIBLE_RECORD',
    NULL, NULL, NULL, NULL,
    'not_imported_inaccessible', NULL, '[]'::JSONB,
    'Not verified from an accessible dataset record.',
    'Associated article published 2024.',
    'Associated article reports full immersion; exact source fields were not inspected.',
    'Associated article reports two roast treatments; exact source fields were not inspected.',
    'Associated article reports descriptive sensory analysis; exact source fields were not inspected.',
    'Dryad API returned identifier cannot be viewed or is missing required elements. No exact version, rights record, file hash, or source row was invented.',
    DATE '2026-08-25'
);

INSERT INTO context.context_source_file (
    context_source_file_key, context_source_review_id, repository_path,
    canonical_download_url, mirror_download_url, sha256, byte_count,
    row_count, column_count, imported_as_context_records
)
SELECT
    file.file_key,
    review.context_source_review_id,
    file.repository_path,
    file.canonical_url,
    file.mirror_url,
    file.sha256,
    file.byte_count,
    file.row_count,
    file.column_count,
    file.imported
FROM (VALUES
    ('context.source_file.cotter_v4.data', 'context.source_review.dryad_cotter_black_coffee.v4', 'db/data/round3b/raw/cotter_2020_black_coffee/cotter_dataset.csv', 'https://datadryad.org/api/v2/files/2041575/download', 'https://zenodo.org/records/7542610/files/cotter_dataset.csv?download=1', '931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114', 542026::BIGINT, 3186::BIGINT, 48, TRUE),
    ('context.source_file.cotter_v4.readme', 'context.source_review.dryad_cotter_black_coffee.v4', 'db/data/round3b/raw/cotter_2020_black_coffee/README.txt', 'https://datadryad.org/api/v2/files/2041574/download', 'https://zenodo.org/records/7542610/files/README.txt?download=1', 'f6d8f508bad2824a27be8785c841e8df4c75751b58726820f9e3dd226fe3fb5e', 8479::BIGINT, NULL::BIGINT, NULL::INTEGER, FALSE),
    ('context.source_file.yeager_v5.cga', 'context.source_review.dryad_yeager_acids.v5', 'db/data/round3b/raw/yeager_2021_acids_meta/Acids_in_Coffee_-CGAs.csv', 'https://datadryad.org/api/v2/files/811668/download', 'https://zenodo.org/records/5083325/files/Acids_in_Coffee_-CGAs.csv?download=1', '3cd45f9640db5e1d3cff1e188daa56e64bf3aa5c0659b3d7319188da2d32a112', 1461458::BIGINT, 1344::BIGINT, 33, TRUE),
    ('context.source_file.yeager_v5.oa', 'context.source_review.dryad_yeager_acids.v5', 'db/data/round3b/raw/yeager_2021_acids_meta/Acids_in_Coffee_-OAs.csv', 'https://datadryad.org/api/v2/files/811667/download', 'https://zenodo.org/records/5083325/files/Acids_in_Coffee_-OAs.csv?download=1', '3de0483c14b310dfa0f960d0f5096df014483dcdb14ef217d239432c316b808d', 36082::BIGINT, 287::BIGINT, 35, TRUE),
    ('context.source_file.yeager_v5.references', 'context.source_review.dryad_yeager_acids.v5', 'db/data/round3b/raw/yeager_2021_acids_meta/Acids_in_Coffee_-References.csv', 'https://datadryad.org/api/v2/files/811665/download', 'https://zenodo.org/records/5083325/files/Acids_in_Coffee_-References.csv?download=1', 'd43166417e425f471be6d14d03d2c28a3eb5edf3c8ac30106c31b415ac46a9b5', 50950::BIGINT, 183::BIGINT, 1, FALSE),
    ('context.source_file.yeager_v5.readme', 'context.source_review.dryad_yeager_acids.v5', 'db/data/round3b/raw/yeager_2021_acids_meta/ReadMe.xlsx', 'https://datadryad.org/api/v2/files/811666/download', 'https://zenodo.org/records/5083325/files/ReadMe.xlsx?download=1', '6d6e6edb55cd46c02a957e8a84072d11a2b19ff2ac794b1ba132c8c6a3a11530', 13689::BIGINT, 79::BIGINT, 13, FALSE)
) AS file(
    file_key, review_key, repository_path, canonical_url, mirror_url,
    sha256, byte_count, row_count, column_count, imported
)
JOIN context.context_source_review AS review
  ON review.context_source_review_key = file.review_key;

INSERT INTO context.context_dataset_snapshot (
    snapshot_key, snapshot_hash, normalization_version, code_commit,
    created_at, split_seed, case_count, held_out_case_count,
    stratification, is_frozen
)
VALUES (
    'context.snapshot.round3b_v1',
    'aca93ed92f0c032f81709bc35d3db102a10bfdddf684c09765228ee1a5481355',
    'context_normalization_v1',
    '6e2aa59d407982e77f05d5df539348719490f179',
    TIMESTAMPTZ '2026-08-25 00:00:00+10',
    'coffee-context-round3b-heldout-v1-20260825',
    102, 17,
    'Domain and authored semantic stratum; deterministic SHA-256 allocation.',
    FALSE
);

INSERT INTO context.context_dataset_snapshot_source (
    context_dataset_snapshot_id, context_source_review_id
)
SELECT snapshot.context_dataset_snapshot_id, review.context_source_review_id
FROM context.context_dataset_snapshot AS snapshot
CROSS JOIN context.context_source_review AS review
WHERE snapshot.snapshot_key = 'context.snapshot.round3b_v1'
  AND review.context_acquisition_status_code = 'imported';

CREATE TEMP TABLE round3b_context_record_stage (
    record_key TEXT,
    source_key TEXT,
    file_relative_path TEXT,
    source_row_number BIGINT,
    raw_preparation_label TEXT,
    raw_roast_label TEXT,
    preparation_status_code TEXT,
    normalized_preparation_family_key TEXT,
    normalized_preparation_leaf_key TEXT,
    roast_status_code TEXT,
    normalized_roast_code TEXT,
    coffee_mode_code TEXT,
    has_sensory_outcome BOOLEAN,
    has_chemical_outcome BOOLEAN,
    has_strong_addition BOOLEAN,
    raw_payload JSONB
);

\copy round3b_context_record_stage FROM 'db/data/round3b/derived/context_records.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO context.raw_context_record (
    raw_context_record_key, context_dataset_snapshot_id,
    context_source_review_id, context_source_file_id, source_row_number,
    raw_preparation_label, raw_roast_label, preparation_status_code,
    normalized_preparation_family_id, normalized_preparation_leaf_id,
    roast_status_code, normalized_roast_category_id,
    context_coffee_mode_code, has_sensory_outcome, has_chemical_outcome,
    has_strong_addition, raw_payload
)
SELECT
    stage.record_key,
    snapshot.context_dataset_snapshot_id,
    review.context_source_review_id,
    file.context_source_file_id,
    stage.source_row_number,
    NULLIF(stage.raw_preparation_label, ''),
    NULLIF(stage.raw_roast_label, ''),
    stage.preparation_status_code,
    family.preparation_concept_id,
    leaf.preparation_concept_id,
    stage.roast_status_code,
    roast.roast_category_id,
    stage.coffee_mode_code,
    stage.has_sensory_outcome,
    stage.has_chemical_outcome,
    stage.has_strong_addition,
    stage.raw_payload
FROM round3b_context_record_stage AS stage
CROSS JOIN context.context_dataset_snapshot AS snapshot
JOIN context.context_source_review AS review
  ON review.context_source_review_key = CASE stage.source_key
      WHEN 'dryad_cotter_black_coffee'
          THEN 'context.source_review.dryad_cotter_black_coffee.v4'
      WHEN 'dryad_yeager_acids_meta_analysis'
          THEN 'context.source_review.dryad_yeager_acids.v5'
  END
JOIN context.context_source_file AS file
  ON file.context_source_review_id = review.context_source_review_id
 AND replace(file.repository_path, 'db/data/round3b/raw/', '') =
     stage.file_relative_path
LEFT JOIN context.preparation_concept AS family
  ON family.preparation_concept_key =
     NULLIF(stage.normalized_preparation_family_key, '')
LEFT JOIN context.preparation_concept AS leaf
  ON leaf.preparation_concept_key =
     NULLIF(stage.normalized_preparation_leaf_key, '')
LEFT JOIN context.v_current_user_roast AS current_roast
  ON current_roast.interaction_code = NULLIF(stage.normalized_roast_code, '')
LEFT JOIN context.roast_category AS roast
  ON roast.roast_category_key = current_roast.roast_category_key
WHERE snapshot.snapshot_key = 'context.snapshot.round3b_v1';

CREATE TEMP TABLE round3b_lexical_rule_stage (
    rule_key TEXT,
    domain TEXT,
    language_tag TEXT,
    normalized_expression TEXT,
    outcome_status TEXT,
    family_key TEXT,
    leaf_key TEXT,
    roast_code TEXT,
    mapping_grade TEXT,
    review_decision TEXT,
    evidence_locator TEXT
);

\copy round3b_lexical_rule_stage FROM 'db/data/round3b/derived/lexical_rules.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO context.context_lexical_rule (
    context_lexical_rule_key, context_domain, language_tag_code,
    normalized_expression, outcome_status_code,
    normalized_preparation_family_id, normalized_preparation_leaf_id,
    normalized_roast_category_id, mapping_grade, review_decision_code,
    source_version_id, evidence_locator, lifecycle_status_code
)
SELECT
    stage.rule_key,
    stage.domain,
    stage.language_tag,
    stage.normalized_expression,
    stage.outcome_status,
    family.preparation_concept_id,
    leaf.preparation_concept_id,
    roast.roast_category_id,
    stage.mapping_grade,
    stage.review_decision,
    source_version.source_version_id,
    stage.evidence_locator,
    'active'
FROM round3b_lexical_rule_stage AS stage
LEFT JOIN context.preparation_concept AS family
  ON family.preparation_concept_key = NULLIF(stage.family_key, '')
LEFT JOIN context.preparation_concept AS leaf
  ON leaf.preparation_concept_key = NULLIF(stage.leaf_key, '')
LEFT JOIN context.v_current_user_roast AS current_roast
  ON current_roast.interaction_code = NULLIF(stage.roast_code, '')
LEFT JOIN context.roast_category AS roast
  ON roast.roast_category_key = current_roast.roast_category_key
CROSS JOIN evidence.source_version AS source_version
WHERE source_version.source_version_key =
      'source_version.project.context_v1.2026-08-25';

INSERT INTO context.context_normalization_benchmark (
    benchmark_key, context_dataset_snapshot_id, split_seed, snapshot_hash,
    case_count, held_out_case_count, stratification,
    frozen_before_rule_evaluation
)
SELECT
    'context.benchmark.round3b_v1',
    snapshot.context_dataset_snapshot_id,
    snapshot.split_seed,
    snapshot.snapshot_hash,
    snapshot.case_count,
    snapshot.held_out_case_count,
    snapshot.stratification,
    TRUE
FROM context.context_dataset_snapshot AS snapshot
WHERE snapshot.snapshot_key = 'context.snapshot.round3b_v1';

CREATE TEMP TABLE round3b_case_stage (
    case_key TEXT,
    domain TEXT,
    language_tag TEXT,
    raw_expression TEXT,
    expected_status TEXT,
    expected_family_key TEXT,
    expected_leaf_key TEXT,
    expected_roast_code TEXT,
    stratum TEXT,
    notes TEXT,
    split TEXT,
    split_hash_prefix TEXT
);

\copy round3b_case_stage FROM 'db/data/round3b/benchmark/context_cases_frozen.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO context.context_normalization_case (
    context_normalization_case_key, context_normalization_benchmark_id,
    context_domain, language_tag_code, raw_expression,
    expected_status_code, expected_preparation_family_id,
    expected_preparation_leaf_id, expected_roast_category_id,
    evaluation_split, stratum, split_hash_prefix, notes
)
SELECT
    stage.case_key,
    benchmark.context_normalization_benchmark_id,
    stage.domain,
    stage.language_tag,
    stage.raw_expression,
    stage.expected_status,
    family.preparation_concept_id,
    leaf.preparation_concept_id,
    roast.roast_category_id,
    stage.split,
    stage.stratum,
    stage.split_hash_prefix,
    stage.notes
FROM round3b_case_stage AS stage
CROSS JOIN context.context_normalization_benchmark AS benchmark
LEFT JOIN context.preparation_concept AS family
  ON family.preparation_concept_key = NULLIF(stage.expected_family_key, '')
LEFT JOIN context.preparation_concept AS leaf
  ON leaf.preparation_concept_key = NULLIF(stage.expected_leaf_key, '')
LEFT JOIN context.v_current_user_roast AS current_roast
  ON current_roast.interaction_code = NULLIF(stage.expected_roast_code, '')
LEFT JOIN context.roast_category AS roast
  ON roast.roast_category_key = current_roast.roast_category_key
WHERE benchmark.benchmark_key = 'context.benchmark.round3b_v1';

CREATE TEMP TABLE round3b_result_stage (
    case_key TEXT,
    domain TEXT,
    split TEXT,
    expected_status TEXT,
    predicted_status TEXT,
    expected_family_key TEXT,
    predicted_family_key TEXT,
    expected_leaf_key TEXT,
    predicted_leaf_key TEXT,
    expected_roast_code TEXT,
    predicted_roast_code TEXT,
    evaluation_grade TEXT,
    ordinal_error TEXT,
    gross_error BOOLEAN,
    mapping_grade TEXT
);

\copy round3b_result_stage FROM 'db/data/round3b/benchmark/normalization_results.tsv' WITH (FORMAT csv, HEADER true, DELIMITER E'\t')

INSERT INTO context.context_normalization_result (
    context_normalization_case_id, predicted_status_code,
    predicted_preparation_family_id, predicted_preparation_leaf_id,
    predicted_roast_category_id, evaluation_grade, ordinal_error,
    gross_error, mapping_grade, normalization_version
)
SELECT
    selected_case.context_normalization_case_id,
    stage.predicted_status,
    family.preparation_concept_id,
    leaf.preparation_concept_id,
    roast.roast_category_id,
    stage.evaluation_grade,
    NULLIF(stage.ordinal_error, '')::SMALLINT,
    stage.gross_error,
    stage.mapping_grade,
    'context_normalization_v1'
FROM round3b_result_stage AS stage
JOIN context.context_normalization_case AS selected_case
  ON selected_case.context_normalization_case_key = stage.case_key
LEFT JOIN context.preparation_concept AS family
  ON family.preparation_concept_key = NULLIF(stage.predicted_family_key, '')
LEFT JOIN context.preparation_concept AS leaf
  ON leaf.preparation_concept_key = NULLIF(stage.predicted_leaf_key, '')
LEFT JOIN context.v_current_user_roast AS current_roast
  ON current_roast.interaction_code = NULLIF(stage.predicted_roast_code, '')
LEFT JOIN context.roast_category AS roast
  ON roast.roast_category_key = current_roast.roast_category_key;

INSERT INTO audit.context_statistic (
    context_statistic_key, context_dataset_snapshot_id, statistic_group,
    statistic_value, research_question, input_data, assumptions,
    output_interpretation, limitations
)
SELECT
    statistic.statistic_key,
    snapshot.context_dataset_snapshot_id,
    statistic.statistic_group,
    statistic.statistic_value,
    statistic.research_question,
    'context.snapshot.round3b_v1',
    statistic.assumptions,
    statistic.output_interpretation,
    statistic.limitations
FROM (VALUES
    (
        'context.statistic.round3b.normalization_metrics',
        'normalization_metrics',
        '{"metric_semantics":"label-normalization quality; not coffee flavor accuracy","held_out_size":17,"c0":{"held_out_size":9,"recall_at_1_leaf":1.0,"recall_at_1_family":1.0,"family_coverage":1.0,"leaf_coverage":0.8889,"unresolved_rate":0.0,"ambiguous_rate":0.0,"gross_family_error_rate":0.0},"c1":{"held_out_size":8,"known_expected_size":5,"exact_category_agreement":1.0,"adjacent_category_agreement":1.0,"gross_category_error_rate":0.0,"coverage":0.625,"unresolved_rate":0.375,"mapping_precision":1.0,"mean_absolute_category_error_on_mapped_known":0.0,"equal_physical_distance_assumed":false},"c0_normalization_data_sufficient":false,"c1_normalization_data_sufficient":false}'::JSONB,
        'Can reviewed raw preparation and roast expressions be normalized without forced assignment?',
        'Exact string lookup against rules frozen after a deterministic development/held-out split.',
        'Coverage and error are reported separately; abstention is not converted into an incorrect nearest category.',
        'The cases are project-authored contract cases, not an independent ordinary-user sample.'
    ),
    (
        'context.statistic.round3b.representativeness',
        'representativeness',
        '{"context_record_count":4817,"source_distribution":{"dryad_cotter_black_coffee":3186,"dryad_yeager_acids_meta_analysis":1631},"source_concentration_max_share":0.6614,"country_distribution":{"united_states_sensory_sessions_honduras_coffee":3186,"heterogeneous_meta_analysis_not_row_normalized":1631},"preparation_distribution":{"not_applicable":506,"not_reported":167,"preparation.family.cold_extraction":1,"preparation.family.espresso_milk":3,"preparation.family.espresso_pressure":228,"preparation.family.filter_percolation":3365,"preparation.family.immersion":473,"reported_unresolved":74},"roast_distribution":{"dark":123,"light":111,"medium":3595,"not_applicable":569,"not_reported":364,"reported_unresolved":55},"black_milk_distribution":{"black_coffee":4141,"milk_coffee":3,"not_applicable":673}}'::JSONB,
        'What populations and contexts are represented in the imported snapshot?',
        'Descriptive counts only; no population weighting or generalization.',
        'The two source datasets use different units of observation and are not pooled as one sampling frame.',
        'Country is available only at source-study scope; row-level country normalization would invent metadata.'
    ),
    (
        'context.statistic.round3b.signal_sufficiency',
        'signal_sufficiency',
        '{"sensory_row_count":3186,"sensory_preparation_family_count":1,"sensory_roast_category_count":1,"sensory_preparation_roast_cell_count":1,"milk_sensory_row_count":0,"preparation_signal_data_sufficient":false,"roast_signal_data_sufficient":false,"preparation_roast_interaction_data_sufficient":false,"milk_mode_data_sufficient":false,"preparation_signal_result":"NOT_ESTIMABLE","roast_signal_result":"NOT_ESTIMABLE","preparation_roast_interaction_result":"NOT_ESTIMABLE","milk_mode_result":"EVIDENCE_INSUFFICIENT"}'::JSONB,
        'Do preparation, roast, or their interaction add information about sensory outcomes?',
        'At least two populated levels per main effect and replicated crossed cells for interaction.',
        'No production coefficient or significance claim is emitted because the effects are not identifiable in the imported sensory rows.',
        'Cotter fixes preparation and roast; Yeager varies context but reports chemistry rather than sensory outcomes.'
    )
) AS statistic(
    statistic_key, statistic_group, statistic_value, research_question,
    assumptions, output_interpretation, limitations
)
CROSS JOIN context.context_dataset_snapshot AS snapshot
WHERE snapshot.snapshot_key = 'context.snapshot.round3b_v1';

UPDATE context.context_dataset_snapshot
SET is_frozen = TRUE
WHERE snapshot_key = 'context.snapshot.round3b_v1';

COMMIT;
