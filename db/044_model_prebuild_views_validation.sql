\set ON_ERROR_STOP on

BEGIN;

CREATE VIEW evidence.v_model_prebuild_source_partitions AS
SELECT
    partition.partition_key,
    partition.source_family_key,
    partition.dataset_snapshot_key,
    partition.participant_type,
    partition.sensory_method,
    partition.sample_count,
    partition.row_count,
    partition.future_training_surface_status,
    partition.compatible_join_group,
    count(feature.feature_key)::INTEGER AS declared_feature_count,
    count(*) FILTER (
        WHERE feature.harmonization_status = 'SEMANTICALLY_COMPATIBLE'
    )::INTEGER AS compatible_feature_count,
    count(*) FILTER (
        WHERE feature.harmonization_status = 'PARTIALLY_COMPATIBLE'
    )::INTEGER AS partial_feature_count,
    count(*) FILTER (
        WHERE feature.harmonization_status IN (
            'NOT_COMPATIBLE', 'SOURCE_LOCAL_ONLY', 'UNRESOLVED'
        )
    )::INTEGER AS non_poolable_feature_count,
    bool_and(
        feature.pooling_allowed = (
            feature.harmonization_status = 'SEMANTICALLY_COMPATIBLE'
        )
    ) AS pooling_contract_consistent,
    partition.rights_boundary
FROM evidence.model_prebuild_source_partition AS partition
JOIN evidence.model_prebuild_partition_feature AS feature
  ON feature.partition_key = partition.partition_key
GROUP BY partition.partition_key;

CREATE VIEW evidence.v_model_prebuild_feature_availability AS
SELECT
    definition.feature_key,
    definition.semantics,
    definition.data_type,
    definition.unit,
    definition.harmonization_status,
    definition.model_use_status,
    count(feature.partition_key)::INTEGER AS available_partition_count,
    count(*) FILTER (WHERE feature.pooling_allowed)::INTEGER
        AS pooling_allowed_partition_count,
    array_agg(feature.partition_key ORDER BY feature.partition_key)
        AS available_partitions,
    definition.missingness_semantics,
    definition.limitation
FROM evidence.model_prebuild_feature_definition AS definition
LEFT JOIN evidence.model_prebuild_partition_feature AS feature
  ON feature.feature_key = definition.feature_key
GROUP BY definition.feature_key;

CREATE VIEW audit.v_model_prebuild_coverage AS
WITH source_totals AS (
    SELECT
        count(*) FILTER (WHERE counts_as_sensory_outcome)::INTEGER
            AS new_sensory_source_count,
        count(DISTINCT sensory_method_family) FILTER (
            WHERE counts_as_sensory_outcome
        )::INTEGER AS sensory_method_family_count,
        count(*) FILTER (WHERE counts_as_ordinary_user)::INTEGER
            AS new_ordinary_user_source_count,
        count(*) FILTER (WHERE counts_as_reference_panel)::INTEGER
            AS new_reference_panel_source_count,
        count(*) FILTER (WHERE counts_as_milk_sensory)::INTEGER
            AS milk_sensory_source_count,
        sum(source_local_observation_row_count) FILTER (
            WHERE counts_as_sensory_outcome
        )::INTEGER AS new_observation_row_count,
        sum(source_local_sample_count) FILTER (
            WHERE counts_as_sensory_outcome
        )::INTEGER AS new_sample_count,
        sum(participant_or_panel_count) FILTER (
            WHERE counts_as_sensory_outcome
        )::INTEGER AS new_participant_or_panel_count,
        sum(empirical_coverage_cell_count) FILTER (
            WHERE counts_as_sensory_outcome
        )::INTEGER AS new_empirical_coverage_cell_count,
        sum(crossed_preparation_roast_cell_count) FILTER (
            WHERE counts_as_sensory_outcome
        )::INTEGER AS new_crossed_cell_count
    FROM evidence.model_prebuild_source_profile
), preparation_totals AS (
    SELECT count(DISTINCT preparation)::INTEGER AS preparation_count
    FROM evidence.model_prebuild_source_profile AS profile
    CROSS JOIN LATERAL unnest(profile.preparation_families)
        AS item(preparation)
    WHERE profile.counts_as_sensory_outcome
), roast_totals AS (
    SELECT count(DISTINCT roast)::INTEGER AS new_roast_scheme_count
    FROM evidence.model_prebuild_source_profile AS profile
    CROSS JOIN LATERAL unnest(profile.roast_schemes) AS item(roast)
    WHERE profile.counts_as_sensory_outcome
)
SELECT
    4 + source_totals.new_sensory_source_count
        AS coffee_sensory_source_family_count,
    source_totals.sensory_method_family_count,
    3689 + source_totals.new_observation_row_count
        AS source_local_sensory_observation_row_count,
    101 + source_totals.new_sample_count
        AS source_local_sensory_sample_count,
    236 + source_totals.new_participant_or_panel_count
        AS source_local_participant_or_panel_count,
    preparation_totals.preparation_count
        AS sensory_outcome_preparation_family_count,
    4 + roast_totals.new_roast_scheme_count
        AS sensory_outcome_roast_category_or_scheme_count,
    1 + source_totals.new_crossed_cell_count
        AS crossed_preparation_roast_observed_cell_count,
    source_totals.milk_sensory_source_count
        AS milk_sensory_outcome_source_family_count,
    2 + source_totals.new_ordinary_user_source_count
        AS ordinary_user_sensory_source_family_count,
    1 + source_totals.new_reference_panel_source_count
        AS reference_panel_source_family_count,
    52 + source_totals.new_empirical_coverage_cell_count
        AS empirical_coverage_cell_count,
    (SELECT count(*) FROM audit.model_prebuild_context_cell)
        AS new_context_cell_count
FROM source_totals, preparation_totals, roast_totals;

CREATE VIEW audit.v_model_prebuild_sensory_concentration AS
WITH family_rows(source_family_key, observation_row_count, count_basis) AS (
    VALUES
        ('family.baseline.cotter-consumers', 3186, 'Frozen Round 3H baseline allocation'),
        ('family.baseline.taste-sensitivity', 93, 'Frozen Round 3H baseline allocation'),
        ('family.baseline.ftnir-reference', 320, 'Frozen Round 3H baseline allocation'),
        ('family.liberica-ratapanel-2025', 90, 'Ten descriptors by nine observed configurations')
    UNION ALL
    SELECT
        source_family_key, source_local_observation_row_count,
        'Round 3H governed source profile'
    FROM evidence.model_prebuild_source_profile
    WHERE counts_as_sensory_outcome
), ranked AS (
    SELECT
        source_family_key,
        observation_row_count,
        observation_row_count::NUMERIC
            / sum(observation_row_count) OVER () AS source_family_share,
        dense_rank() OVER (ORDER BY observation_row_count DESC) AS share_rank,
        count(*) OVER () AS contributing_family_count,
        count(*) FILTER (WHERE observation_row_count > 0) OVER ()
            AS meaningful_observation_family_count,
        count_basis
    FROM family_rows
)
SELECT
    source_family_key, observation_row_count, source_family_share,
    share_rank, contributing_family_count,
    meaningful_observation_family_count,
    max(source_family_share) OVER () AS largest_source_family_share,
    max(source_family_share) FILTER (WHERE share_rank = 2) OVER ()
        AS second_largest_source_family_share,
    count_basis,
    'Shares are descriptive; incompatible source-local methods are not pooled.'::TEXT
        AS limitation
FROM ranked;

CREATE VIEW audit.v_model_prebuild_context_coverage AS
SELECT
    source_family_key, preparation_family, roast_source_label, milk_mode,
    sensory_method, participant_type, language_code,
    count(*)::INTEGER AS observed_cell_count,
    count(DISTINCT coffee_identity)::INTEGER AS coffee_identity_count,
    bool_and(evidence_status = 'OBSERVED_SOURCE_LOCAL_EVIDENCE')
        AS observed_only,
    bool_and(NOT zero_filled) AS no_zero_fill,
    count(*) FILTER (WHERE crossed_preparation_roast_eligible)::INTEGER
        AS crossed_eligible_cell_count
FROM audit.model_prebuild_context_cell
GROUP BY
    source_family_key, preparation_family, roast_source_label, milk_mode,
    sensory_method, participant_type, language_code;

CREATE VIEW corpus.v_model_prebuild_language_inventory AS
SELECT
    language_plane,
    count(*)::INTEGER AS reviewed_candidate_count,
    sum(countable_family_gain)::INTEGER AS countable_source_family_count,
    sum(countable_document_gain)::INTEGER AS countable_document_count,
    sum(countable_expression_gain)::INTEGER AS countable_expression_count,
    count(*) FILTER (WHERE machine_translated)::INTEGER
        AS machine_translated_count,
    count(*) FILTER (WHERE artificial_variant)::INTEGER
        AS artificial_variant_count,
    count(*) FILTER (WHERE source_authored)::INTEGER
        AS verified_source_authored_candidate_count,
    'No Round 3H candidate produced lawful countable language gain.'::TEXT
        AS limitation
FROM corpus.model_prebuild_language_source_decision
GROUP BY language_plane;

CREATE VIEW calibration.v_model_prebuild_question_evidence AS
SELECT
    evidence.question_evidence_key,
    target.question_range_target_key,
    evidence.supporting_source_families,
    evidence.independent_origin_count,
    evidence.research_decision,
    evidence.research_basis,
    evidence.user_validation_status,
    evidence.information_gain_status,
    evidence.limitation
FROM calibration.model_prebuild_question_evidence AS evidence
JOIN calibration.question_range_target AS target
  ON target.question_range_target_id = evidence.question_range_target_id;

CREATE VIEW audit.v_model_prebuild_rights_completeness AS
SELECT
    profile.source_key,
    profile.source_family_key,
    profile.annotation_complete,
    profile.rights_review_complete,
    source.rights_review_status,
    source.commercial_use_allowed,
    source.derivative_use_allowed,
    source.redistribution_allowed,
    source.machine_use_allowed,
    count(file.file_key)::INTEGER AS governed_file_count,
    bool_and(file.hash_verified) AS all_files_hash_verified,
    bool_and(file.declared_sha256 = file.verified_sha256)
        AS all_file_hashes_match
FROM evidence.model_prebuild_source_profile AS profile
JOIN evidence.relationship_source AS source
  ON source.source_key = profile.source_key
LEFT JOIN evidence.relationship_source_file AS file
  ON file.source_key = profile.source_key
GROUP BY profile.source_key, profile.source_family_key,
    profile.annotation_complete, profile.rights_review_complete,
    source.rights_review_status, source.commercial_use_allowed,
    source.derivative_use_allowed, source.redistribution_allowed,
    source.machine_use_allowed;

CREATE VIEW audit.v_model_prebuild_relationship_delta AS
SELECT
    (SELECT count(*) FROM evidence.relationship_evidence_claim)::INTEGER
        AS relationship_evidence_claim_count,
    count(*) FILTER (
        WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
    )::INTEGER AS source_local_supported_membership_count,
    count(*) FILTER (
        WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
    )::INTEGER AS cross_source_supported_membership_count,
    (SELECT count(*) FROM audit.model_prebuild_range_evidence_summary
        WHERE source_local_supporting_membership_count > 0)::INTEGER
        AS range_with_source_local_evidence_count,
    (SELECT count(*) FROM audit.model_prebuild_range_evidence_summary
        WHERE cross_source_supporting_membership_count > 0)::INTEGER
        AS range_with_cross_source_evidence_count,
    count(*) FILTER (
        WHERE lifecycle_status IN (
            'SOURCE_LOCAL_SUPPORTED', 'CROSS_SOURCE_SUPPORTED'
        )
    )::INTEGER AS total_supported_membership_count,
    'Counts are reviewed evidence states, not probabilities or model weights.'::TEXT
        AS limitation
FROM corpus.association_range_membership;

CREATE FUNCTION audit.run_model_prebuild_readiness_gate()
RETURNS TABLE (
    readiness_key TEXT,
    minimum_required TEXT,
    preferred_required TEXT,
    observed TEXT,
    hard_gate BOOLEAN,
    passed BOOLEAN,
    evidence_path TEXT,
    limitation TEXT
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_model_prebuild_readiness_gate$
WITH coverage AS (
    SELECT * FROM audit.v_model_prebuild_coverage
), relationship AS (
    SELECT * FROM audit.v_model_prebuild_relationship_delta
), contemporary AS (
    SELECT * FROM corpus.v_model_prebuild_language_inventory
    WHERE language_plane = 'CONTEMPORARY'
), zh_hans AS (
    SELECT * FROM corpus.v_model_prebuild_language_inventory
    WHERE language_plane = 'ZH_HANS'
), gates AS (
    SELECT 'sensory.source_family_count'::TEXT AS readiness_key,
        '5'::TEXT AS minimum_required, '8'::TEXT AS preferred_required,
        coffee_sensory_source_family_count::TEXT AS observed,
        TRUE AS hard_gate, coffee_sensory_source_family_count >= 5 AS passed,
        'audit.v_model_prebuild_coverage'::TEXT AS evidence_path,
        'Independent governed sensory origins; chemistry-only and marketing corpora excluded.'::TEXT AS limitation
    FROM coverage
    UNION ALL SELECT 'sensory.method_family_count', '3', '4',
        sensory_method_family_count::TEXT, TRUE,
        sensory_method_family_count >= 3,
        'evidence.model_prebuild_source_profile',
        'CATA, RATA, trained descriptive, and Q-grader semantics remain separate.'
    FROM coverage
    UNION ALL SELECT 'context.preparation_sensory_coverage', '3', '5',
        sensory_outcome_preparation_family_count::TEXT, TRUE,
        sensory_outcome_preparation_family_count >= 3,
        'audit.v_model_prebuild_coverage',
        'Only preparation labels attached to sensory outcomes count.'
    FROM coverage
    UNION ALL SELECT 'context.roast_sensory_coverage', '4', '6',
        sensory_outcome_roast_category_or_scheme_count::TEXT, TRUE,
        sensory_outcome_roast_category_or_scheme_count >= 4,
        'audit.v_model_prebuild_coverage',
        'Source-local roast schemes are counted without silent harmonization.'
    FROM coverage
    UNION ALL SELECT 'context.crossed_cell_count', '12', '50',
        crossed_preparation_roast_observed_cell_count::TEXT, TRUE,
        crossed_preparation_roast_observed_cell_count >= 12,
        'audit.model_prebuild_context_cell',
        'Observed coffee-by-preparation-by-roast cells only.'
    FROM coverage
    UNION ALL SELECT 'context.empirical_coverage_cell_count', '120', '180',
        empirical_coverage_cell_count::TEXT, TRUE,
        empirical_coverage_cell_count >= 120,
        'audit.v_model_prebuild_coverage',
        'Engineering coverage count; not a statistical-significance claim.'
    FROM coverage
    UNION ALL SELECT 'consumer.ordinary_user_source_count', '2', '4',
        ordinary_user_sensory_source_family_count::TEXT, TRUE,
        ordinary_user_sensory_source_family_count >= 2,
        'audit.v_model_prebuild_coverage',
        'General surveys without sensory response variables are excluded.'
    FROM coverage
    UNION ALL SELECT 'reference.panel_source_count', '2', '3',
        reference_panel_source_family_count::TEXT, TRUE,
        reference_panel_source_family_count >= 2,
        'audit.v_model_prebuild_coverage',
        'Reference and trained panels remain separate from ordinary users.'
    FROM coverage
    UNION ALL SELECT 'milk.sensory_outcome_source_family_count', '0', '1',
        milk_sensory_outcome_source_family_count::TEXT, FALSE,
        milk_sensory_outcome_source_family_count >= 1,
        'evidence.model_prebuild_source_profile',
        'Preferred only; black-coffee-only readiness is allowed when every hard gate passes.'
    FROM coverage
    UNION ALL SELECT 'language.contemporary_source_family_count', '3', '5',
        coalesce(contemporary.countable_source_family_count, 0)::TEXT, TRUE,
        coalesce(contemporary.countable_source_family_count, 0) >= 3,
        'corpus.v_model_prebuild_language_inventory',
        'Firstbloom, dictionaries, mirrors, and non-redistributable catalogs are excluded.'
    FROM contemporary
    UNION ALL SELECT 'language.new_contemporary_document_count', '500', '1500',
        coalesce(contemporary.countable_document_count, 0)::TEXT, TRUE,
        coalesce(contemporary.countable_document_count, 0) >= 500,
        'corpus.v_model_prebuild_language_inventory',
        'Documents must contain lawful observed coffee tasting language.'
    FROM contemporary
    UNION ALL SELECT 'language.unique_expression_count', '2500', '3500',
        (SELECT count(*) FROM corpus.normalized_expression)::TEXT, TRUE,
        (SELECT count(*) FROM corpus.normalized_expression) >= 2500,
        'corpus.normalized_expression',
        'Only observed or explicitly sourced normalized expressions count.'
    UNION ALL SELECT 'language.zh_hans_source_family_count', '2', '3',
        coalesce(zh_hans.countable_source_family_count, 0)::TEXT, TRUE,
        coalesce(zh_hans.countable_source_family_count, 0) >= 2,
        'corpus.v_model_prebuild_language_inventory',
        'Machine translation and automatic script conversion do not establish a source family.'
    FROM zh_hans
    UNION ALL SELECT 'language.zh_hans_sensory_expression_count', '0', '200',
        coalesce(zh_hans.countable_expression_count, 0)::TEXT, FALSE,
        coalesce(zh_hans.countable_expression_count, 0) >= 200,
        'corpus.v_model_prebuild_language_inventory',
        'Preferred observed sensory-language breadth; artificial variants are prohibited.'
    FROM zh_hans
    UNION ALL SELECT 'relationship.evidence_claim_count', '80', '150',
        relationship_evidence_claim_count::TEXT, TRUE,
        relationship_evidence_claim_count >= 80,
        'audit.v_model_prebuild_relationship_delta',
        'Evidence-specific claims only; raw rows are not mechanically multiplied.'
    FROM relationship
    UNION ALL SELECT 'relationship.source_local_membership_count', '6', '10',
        source_local_supported_membership_count::TEXT, TRUE,
        source_local_supported_membership_count >= 6,
        'audit.v_model_prebuild_relationship_delta',
        'Each promotion requires reviewed evidence from at least one independent origin.'
    FROM relationship
    UNION ALL SELECT 'relationship.cross_source_membership_count', '3', '6',
        cross_source_supported_membership_count::TEXT, TRUE,
        cross_source_supported_membership_count >= 3,
        'audit.v_model_prebuild_relationship_delta',
        'Each cross-source promotion requires at least two independent origins.'
    FROM relationship
    UNION ALL SELECT 'relationship.range_with_source_local_evidence_count', '5', '5',
        range_with_source_local_evidence_count::TEXT, TRUE,
        range_with_source_local_evidence_count >= 5,
        'audit.model_prebuild_range_evidence_summary',
        'A supported membership path does not lifecycle-promote its whole range.'
    FROM relationship
    UNION ALL SELECT 'relationship.range_with_cross_source_evidence_count', '0', '4',
        range_with_cross_source_evidence_count::TEXT, FALSE,
        range_with_cross_source_evidence_count >= 4,
        'audit.model_prebuild_range_evidence_summary',
        'Preferred corroboration only; range lifecycles remain unchanged.'
    FROM relationship
    UNION ALL SELECT 'question.independent_research_target_count', '6', '10',
        count(*)::TEXT, TRUE, count(*) >= 6,
        'calibration.v_model_prebuild_question_evidence',
        'Research constructs do not imply wording validation or information gain.'
    FROM calibration.model_prebuild_question_evidence
    UNION ALL SELECT 'question.user_validated_count', '0', '0',
        count(*) FILTER (WHERE user_validation_status <> 'NOT_USER_VALIDATED')::TEXT,
        TRUE,
        count(*) FILTER (WHERE user_validation_status <> 'NOT_USER_VALIDATED') = 0,
        'calibration.model_prebuild_question_evidence',
        'No real-human question validation occurred.'
    FROM calibration.model_prebuild_question_evidence
    UNION ALL SELECT 'question.information_gain_estimated_count', '0', '0',
        count(*) FILTER (WHERE information_gain_status <> 'NOT_ESTIMABLE')::TEXT,
        TRUE,
        count(*) FILTER (WHERE information_gain_status <> 'NOT_ESTIMABLE') = 0,
        'calibration.model_prebuild_question_evidence',
        'No response observations exist from which to estimate information gain.'
    FROM calibration.model_prebuild_question_evidence
    UNION ALL SELECT 'governance.source_annotation', 'true', 'true',
        bool_and(annotation_complete)::TEXT, TRUE,
        count(*) = 8 AND bool_and(annotation_complete),
        'audit.v_model_prebuild_rights_completeness',
        'All eight newly admitted origins require complete source annotations.'
    FROM audit.v_model_prebuild_rights_completeness
    UNION ALL SELECT 'governance.rights', 'true', 'true',
        bool_and(rights_review_complete AND rights_review_status = 'CLEARED'
            AND commercial_use_allowed AND derivative_use_allowed
            AND redistribution_allowed AND machine_use_allowed)::TEXT,
        TRUE,
        count(*) = 8 AND bool_and(rights_review_complete
            AND rights_review_status = 'CLEARED' AND commercial_use_allowed
            AND derivative_use_allowed AND redistribution_allowed
            AND machine_use_allowed),
        'audit.v_model_prebuild_rights_completeness',
        'Unknown, noncommercial, request-only, and trademarked materials are excluded from public derivatives.'
    FROM audit.v_model_prebuild_rights_completeness
    UNION ALL SELECT 'governance.hashes', 'true', 'true',
        bool_and(all_files_hash_verified AND all_file_hashes_match)::TEXT,
        TRUE,
        count(*) = 8 AND bool_and(all_files_hash_verified
            AND all_file_hashes_match),
        'audit.v_model_prebuild_rights_completeness',
        'All ten newly governed logical files resolve to verified SHA-256 records.'
    FROM audit.v_model_prebuild_rights_completeness
    UNION ALL SELECT 'quality.explicit_missingness_and_harmonization',
        'true', 'true',
        (count(*) = 20 AND count(*) FILTER (
            WHERE cardinality(missingness_semantics) >= 1
            AND harmonization_status <> 'UNRESOLVED'
        ) = 20)::TEXT,
        TRUE,
        count(*) = 20 AND count(*) FILTER (
            WHERE cardinality(missingness_semantics) >= 1
            AND harmonization_status <> 'UNRESOLVED'
        ) = 20,
        'evidence.model_prebuild_feature_definition',
        'Source scales and missingness categories remain explicit and federated.'
    FROM evidence.model_prebuild_feature_definition
    UNION ALL SELECT 'analysis.feature_registry', 'true', 'true',
        (count(*) = 20)::TEXT, TRUE, count(*) = 20,
        'evidence.v_model_prebuild_feature_availability',
        'Feature declarations are prebuild metadata, not a pooled design matrix.'
    FROM evidence.model_prebuild_feature_definition
    UNION ALL SELECT 'analysis.source_partitions', 'true', 'true',
        (count(*) = 12 AND bool_and(pooling_contract_consistent))::TEXT,
        TRUE, count(*) = 12 AND bool_and(pooling_contract_consistent),
        'evidence.v_model_prebuild_source_partitions',
        'Partitions preserve source semantics and grouping keys.'
    FROM evidence.v_model_prebuild_source_partitions
    UNION ALL SELECT 'analysis.leakage_audit', 'true', 'true',
        (count(*) = 7 AND bool_and(audit_pass))::TEXT,
        TRUE, count(*) = 7 AND bool_and(audit_pass),
        'audit.model_prebuild_leakage_risk',
        'Seven future split-leakage classes have declared controls; no split was executed.'
    FROM audit.model_prebuild_leakage_risk
    UNION ALL SELECT 'analysis.manifest', 'true', 'true',
        EXISTS (
            SELECT 1 FROM audit.round3e_artifact_hash
            WHERE artifact_key = 'round3h.model-prebuild-manifest'
        )::TEXT,
        TRUE,
        EXISTS (
            SELECT 1 FROM audit.round3e_artifact_hash
            WHERE artifact_key = 'round3h.model-prebuild-manifest'
              AND sha256 ~ '^[0-9a-f]{64}$'
        ),
        'db/data/model-prebuild/v0/MODEL_PREBUILD_MANIFEST.json',
        'The manifest is metadata-only and explicitly prohibits model execution.'
    UNION ALL SELECT 'analysis.prebuild_only_guard', 'true', 'true',
        (count(*) = 1)::TEXT, TRUE, count(*) = 1,
        'audit.model_prebuild_execution_guard',
        'No model, embedding, pgvector, real-human, frontend, or ontology operation occurred.'
    FROM audit.model_prebuild_execution_guard
    UNION ALL SELECT 'expected_state.threshold_revision_count', '0', '0',
        count(*)::TEXT, TRUE, count(*) = 0,
        'audit.model_prebuild_threshold_revision',
        'Frozen thresholds were not reduced after acquisition.'
    FROM audit.model_prebuild_threshold_revision
)
SELECT * FROM gates
ORDER BY readiness_key
$run_model_prebuild_readiness_gate$;

CREATE VIEW audit.v_model_prebuild_readiness_gate AS
SELECT * FROM audit.run_model_prebuild_readiness_gate();

CREATE FUNCTION audit.model_prebuild_readiness_state()
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $model_prebuild_readiness_state$
SELECT CASE
    WHEN NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'governance.rights')
        THEN 'BLOCKED_RIGHTS'
    WHEN NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'governance.hashes')
        OR NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'quality.explicit_missingness_and_harmonization')
        OR NOT (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'analysis.manifest')
        THEN 'BLOCKED_REPRODUCIBILITY'
    WHEN NOT EXISTS (
        SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
        WHERE hard_gate AND NOT passed
    ) AND (SELECT passed FROM audit.run_model_prebuild_readiness_gate()
        WHERE readiness_key = 'milk.sensory_outcome_source_family_count')
        THEN 'MODEL_PREBUILD_READY'
    WHEN NOT EXISTS (
        SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
        WHERE hard_gate AND NOT passed
    ) THEN 'MODEL_PREBUILD_READY_BLACK_COFFEE_ONLY'
    ELSE 'COMPLETE_WITH_DATA_COVERAGE_GAP'
END
$model_prebuild_readiness_state$;

CREATE FUNCTION audit.enforce_model_prebuild_readiness_assertion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_model_prebuild_readiness_assertion$
DECLARE
    computed_ready BOOLEAN;
    computed_state TEXT;
BEGIN
    SELECT NOT EXISTS (
        SELECT 1
        FROM audit.run_model_prebuild_readiness_gate()
        WHERE hard_gate AND NOT passed
    ) INTO computed_ready;

    SELECT audit.model_prebuild_readiness_state() INTO computed_state;

    IF NEW.model_prebuild_data_ready IS DISTINCT FROM computed_ready THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'model_prebuild_readiness_hard_gate_ck',
            MESSAGE = 'readiness boolean must match all mandatory hard gates';
    END IF;

    IF NEW.readiness_state IS DISTINCT FROM computed_state THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'model_prebuild_readiness_state_match_ck',
            MESSAGE = 'readiness state must match the deterministic gate result';
    END IF;

    RETURN NEW;
END
$enforce_model_prebuild_readiness_assertion$;

CREATE TRIGGER model_prebuild_readiness_assertion_biu
BEFORE INSERT OR UPDATE ON audit.model_prebuild_readiness_assertion
FOR EACH ROW EXECUTE FUNCTION audit.enforce_model_prebuild_readiness_assertion();

CREATE FUNCTION audit.run_round3h_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3h_validation_queries$
WITH checks AS (
    SELECT 'canonical.concept_count'::TEXT AS check_key,
        abs(count(*) - 130)::BIGINT AS violation_count
    FROM kb.concept
    UNION ALL SELECT 'canonical.active_sensory_attribute_count',
        abs(count(*) - 92)::BIGINT
    FROM kb.concept
    WHERE concept_type_code = 'sensory_attribute'
      AND lifecycle_status_code = 'active'
    UNION ALL SELECT 'round3h.new_source_family_count',
        abs(count(*) - 8)::BIGINT
    FROM evidence.source_family
    WHERE introduced_round = '3H'
    UNION ALL SELECT 'round3h.new_snapshot_count',
        abs(count(*) - 8)::BIGINT
    FROM evidence.relationship_source_snapshot AS snapshot
    JOIN evidence.source_family AS family
      ON family.source_family_key = snapshot.source_family_key
    WHERE family.introduced_round = '3H'
    UNION ALL SELECT 'round3h.new_imported_file_count',
        abs(count(*) - 10)::BIGINT
    FROM evidence.relationship_source_file AS file
    JOIN evidence.source_family AS family
      ON family.source_family_key = file.source_family_key
    WHERE family.introduced_round = '3H'
    UNION ALL SELECT 'round3h.new_imported_row_count',
        abs(coalesce(sum(file.row_count), 0) - 724)::BIGINT
    FROM evidence.relationship_source_file AS file
    JOIN evidence.source_family AS family
      ON family.source_family_key = file.source_family_key
    WHERE family.introduced_round = '3H'
    UNION ALL SELECT 'round3h.source_file_hashes',
        count(*) FILTER (
            WHERE NOT file.hash_verified
               OR file.declared_sha256 <> file.verified_sha256
        )::BIGINT
    FROM evidence.relationship_source_file AS file
    JOIN evidence.source_family AS family
      ON family.source_family_key = file.source_family_key
    WHERE family.introduced_round = '3H'
    UNION ALL SELECT 'round3h.source_rights',
        count(*) FILTER (
            WHERE source.rights_review_status <> 'CLEARED'
               OR NOT source.commercial_use_allowed
               OR NOT source.derivative_use_allowed
               OR NOT source.redistribution_allowed
               OR NOT source.machine_use_allowed
        )::BIGINT
    FROM evidence.relationship_source AS source
    JOIN evidence.source_family AS family
      ON family.source_family_key = source.source_family_key
    WHERE family.introduced_round = '3H'
    UNION ALL SELECT 'round3h.context_cell_count',
        abs(count(*) - 129)::BIGINT
    FROM audit.model_prebuild_context_cell
    UNION ALL SELECT 'round3h.context_observed_only',
        count(*) FILTER (
            WHERE evidence_status <> 'OBSERVED_SOURCE_LOCAL_EVIDENCE'
               OR zero_filled
        )::BIGINT
    FROM audit.model_prebuild_context_cell
    UNION ALL SELECT 'round3h.total_empirical_coverage',
        abs(empirical_coverage_cell_count - 181)::BIGINT
    FROM audit.v_model_prebuild_coverage
    UNION ALL SELECT 'round3h.sensory_source_family_count',
        abs(coffee_sensory_source_family_count - 9)::BIGINT
    FROM audit.v_model_prebuild_coverage
    UNION ALL SELECT 'round3h.sensory_observation_row_count',
        abs(source_local_sensory_observation_row_count - 4344)::BIGINT
    FROM audit.v_model_prebuild_coverage
    UNION ALL SELECT 'round3h.sensory_sample_count',
        abs(source_local_sensory_sample_count - 230)::BIGINT
    FROM audit.v_model_prebuild_coverage
    UNION ALL SELECT 'round3h.sensory_participant_or_panel_count',
        abs(source_local_participant_or_panel_count - 520)::BIGINT
    FROM audit.v_model_prebuild_coverage
    UNION ALL SELECT 'round3h.relationship_claim_count',
        abs(count(*) - 96)::BIGINT
    FROM evidence.relationship_evidence_claim
    UNION ALL SELECT 'round3h.source_local_membership_count',
        abs(count(*) - 6)::BIGINT
    FROM corpus.association_range_membership
    WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
    UNION ALL SELECT 'round3h.cross_source_membership_count',
        abs(count(*) - 4)::BIGINT
    FROM corpus.association_range_membership
    WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
    UNION ALL SELECT 'round3h.question_research_count',
        abs(count(*) - 12)::BIGINT
    FROM calibration.model_prebuild_question_evidence
    UNION ALL SELECT 'round3h.question_user_validation_prohibited',
        count(*) FILTER (
            WHERE user_validation_status <> 'NOT_USER_VALIDATED'
        )::BIGINT
    FROM calibration.model_prebuild_question_evidence
    UNION ALL SELECT 'round3h.question_information_gain_prohibited',
        count(*) FILTER (
            WHERE information_gain_status <> 'NOT_ESTIMABLE'
        )::BIGINT
    FROM calibration.model_prebuild_question_evidence
    UNION ALL SELECT 'round3h.language_no_artificial_gain',
        count(*) FILTER (
            WHERE machine_translated OR artificial_variant
               OR countable_family_gain <> 0
               OR countable_document_gain <> 0
               OR countable_expression_gain <> 0
        )::BIGINT
    FROM corpus.model_prebuild_language_source_decision
    UNION ALL SELECT 'round3h.feature_count',
        abs(count(*) - 20)::BIGINT
    FROM evidence.model_prebuild_feature_definition
    UNION ALL SELECT 'round3h.source_partition_count',
        abs(count(*) - 12)::BIGINT
    FROM evidence.model_prebuild_source_partition
    UNION ALL SELECT 'round3h.leakage_audit',
        count(*) FILTER (WHERE NOT audit_pass)::BIGINT
            + abs(count(*) - 7)::BIGINT
    FROM audit.model_prebuild_leakage_risk
    UNION ALL SELECT 'round3h.constraint_registry_count',
        abs(count(*) - 24)::BIGINT
    FROM audit.model_prebuild_constraint_registry
    UNION ALL SELECT 'round3h.threshold_revision_count',
        count(*)::BIGINT
    FROM audit.model_prebuild_threshold_revision
    UNION ALL SELECT 'round3h.data_access_request_ready_unsent',
        count(*) FILTER (WHERE NOT request_ready OR request_sent)::BIGINT
            + abs(count(*) - 2)::BIGINT
    FROM audit.model_prebuild_data_access_request
    UNION ALL SELECT 'round3h.execution_guard',
        CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM audit.model_prebuild_execution_guard
    UNION ALL SELECT 'round3h.manifest_hash_registry',
        CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM audit.round3e_artifact_hash
    WHERE artifact_key = 'round3h.model-prebuild-manifest'
      AND sha256 = 'ea895bc0a9a8f9ee2edf567d86ee42bb6acf9570aa9dc8d3dd73f63cd5368569'
    UNION ALL SELECT 'round3h.readiness_false',
        CASE WHEN EXISTS (
            SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
            WHERE hard_gate AND NOT passed
        ) THEN 0 ELSE 1 END::BIGINT
    UNION ALL SELECT 'round3h.readiness_state',
        CASE WHEN audit.model_prebuild_readiness_state()
            = 'COMPLETE_WITH_DATA_COVERAGE_GAP'
            THEN 0 ELSE 1 END::BIGINT
    UNION ALL SELECT 'round3h.expected_state_frozen',
        count(*) FILTER (
            WHERE NOT expected_state_frozen_before_import
               OR threshold_revision_count <> 0
               OR source_sha <> 'aa6a18ca5f4c289d5fa588e1996c7fa219f99eca'
               OR expected_state_commit_sha <> 'a2d85ecc1e03a96f129342f4ee4ed9755d7c4a75'
        )::BIGINT + abs(count(*) - 1)::BIGINT
    FROM audit.model_prebuild_checkpoint
)
SELECT check_key, violation_count, violation_count = 0 AS passed
FROM checks
ORDER BY check_key
$run_round3h_validation_queries$;

UPDATE audit.model_prebuild_readiness_assertion
SET model_prebuild_data_ready = FALSE,
    readiness_state = audit.model_prebuild_readiness_state(),
    evidence_path = 'audit.run_model_prebuild_readiness_gate()'
WHERE assertion_key = 'assertion.round3h.final';

DO $round3h_validation$
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit.run_round3h_validation_queries()
        WHERE NOT passed
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3h_validation_gate_ck',
            MESSAGE = 'Round 3H deterministic validation query failed';
    END IF;
END
$round3h_validation$;

COMMIT;
