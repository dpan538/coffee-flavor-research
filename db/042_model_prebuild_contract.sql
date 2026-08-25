\set ON_ERROR_STOP on

BEGIN;

ALTER TABLE evidence.source_family
    DROP CONSTRAINT source_family_text_ck;

ALTER TABLE evidence.source_family
    ADD CONSTRAINT source_family_text_ck CHECK (
        source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND family_name = btrim(family_name) AND family_name <> ''
        AND canonical_origin_key = lower(btrim(canonical_origin_key))
        AND canonical_origin_key <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
        AND introduced_round IN ('3G', '3H')
    );

ALTER TABLE kb.relationship_review_decision
    DROP CONSTRAINT relationship_review_decision_disposition_ck;
ALTER TABLE kb.relationship_review_decision
    ADD CONSTRAINT relationship_review_decision_disposition_ck CHECK (
        disposition IN (
            'PROMOTE_SOURCE_LOCAL', 'PROMOTE_CROSS_SOURCE',
            'RETAIN_CANDIDATE', 'REJECT', 'RETURN_TO_UNRESOLVED'
        )
        AND prior_lifecycle IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED',
            'BILINGUAL_REVIEWED', 'REJECTED', 'DEPRECATED'
        )
        AND new_lifecycle IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED',
            'REJECTED', 'DEPRECATED'
        )
        AND reviewed_round IN ('3G', '3H')
    );

ALTER TABLE calibration.question_target_review_decision
    DROP CONSTRAINT question_target_review_decision_disposition_ck;
ALTER TABLE calibration.question_target_review_decision
    ADD CONSTRAINT question_target_review_decision_disposition_ck CHECK (
        disposition IN (
            'RETAIN_HYPOTHESIS', 'RESEARCH_SUPPORT_ADDED',
            'BILINGUAL_REVIEW_REQUIRED', 'REJECT_TARGET',
            'RETURN_TO_UNRESOLVED'
        )
        AND reviewed_round IN ('3G', '3H')
    );

ALTER TABLE evidence.relationship_source_file
    ADD CONSTRAINT model_prebuild_raw_export_rights_ck CHECK (
        file_role <> 'RAW_EXTERNAL'
        OR public_export_decision = 'EXTERNAL_ONLY'
    );

CREATE OR REPLACE FUNCTION audit.enforce_round3g_membership_promotion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3g_membership_promotion$
DECLARE
    independent_origin_count INTEGER;
BEGIN
    IF NEW.lifecycle_status = 'BILINGUAL_REVIEWED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_bilingual_review_prohibited_ck',
            MESSAGE = 'No independent bilingual reviewer record permits this lifecycle';
    END IF;

    IF NEW.lifecycle_status = 'ACTIVE_FOR_CALIBRATION' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_membership_calibration_prohibited_ck',
            MESSAGE = 'Evidence review cannot activate a membership for calibration';
    END IF;

    IF NEW.lifecycle_status IN (
        'SOURCE_LOCAL_SUPPORTED', 'CROSS_SOURCE_SUPPORTED'
    ) AND NEW.lifecycle_status IS DISTINCT FROM OLD.lifecycle_status THEN
        IF NOT EXISTS (
            SELECT 1
            FROM kb.relationship_review_decision AS decision
            WHERE decision.association_range_membership_id =
                NEW.association_range_membership_id
              AND decision.reviewed_round IN ('3G', '3H')
              AND decision.new_lifecycle = NEW.lifecycle_status
              AND decision.disposition = CASE NEW.lifecycle_status
                  WHEN 'SOURCE_LOCAL_SUPPORTED' THEN 'PROMOTE_SOURCE_LOCAL'
                  ELSE 'PROMOTE_CROSS_SOURCE'
              END
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3g_membership_promotion_review_ck',
                MESSAGE = 'membership promotion requires a matching reviewed decision';
        END IF;

        SELECT count(DISTINCT family.canonical_origin_key)
        INTO independent_origin_count
        FROM evidence.relationship_evidence_claim AS claim
        JOIN evidence.source_family AS family
          ON family.source_family_key = claim.source_family_key
        WHERE claim.target_entity_type = 'MEMBERSHIP'
          AND claim.target_entity_key = NEW.membership_key
          AND claim.evidence_direction = 'SUPPORTS'
          AND claim.review_status = 'REVIEWED'
          AND claim.support_count >= 3
          AND claim.document_count >= 1
          AND family.counts_as_independent
          AND family.admitted;

        IF independent_origin_count < (CASE NEW.lifecycle_status
            WHEN 'SOURCE_LOCAL_SUPPORTED' THEN 1 ELSE 2 END) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3g_membership_promotion_evidence_ck',
                MESSAGE = 'membership promotion does not meet source/support thresholds';
        END IF;
    END IF;
    RETURN NEW;
END
$enforce_round3g_membership_promotion$;

CREATE OR REPLACE VIEW audit.v_round3g_promotion_audit AS
WITH membership_promotions AS (
    SELECT
        membership.membership_key,
        membership.lifecycle_status,
        decision.disposition,
        count(DISTINCT family.canonical_origin_key) FILTER (
            WHERE claim.evidence_direction = 'SUPPORTS'
              AND claim.review_status = 'REVIEWED'
              AND claim.support_count >= 3
              AND claim.document_count >= 1
              AND family.counts_as_independent
              AND family.admitted
        ) AS independent_supporting_origin_count,
        count(claim.evidence_claim_key) FILTER (
            WHERE claim.evidence_direction = 'SUPPORTS'
              AND claim.evidence_locator <> ''
        ) AS located_supporting_claim_count
    FROM corpus.association_range_membership AS membership
    LEFT JOIN LATERAL (
        SELECT review.disposition
        FROM kb.relationship_review_decision AS review
        WHERE review.association_range_membership_id =
            membership.association_range_membership_id
        ORDER BY review.reviewed_round DESC
        LIMIT 1
    ) AS decision ON TRUE
    LEFT JOIN evidence.relationship_evidence_claim AS claim
      ON claim.target_entity_type = 'MEMBERSHIP'
     AND claim.target_entity_key = membership.membership_key
    LEFT JOIN evidence.source_family AS family
      ON family.source_family_key = claim.source_family_key
    WHERE membership.lifecycle_status IN (
        'SOURCE_LOCAL_SUPPORTED', 'CROSS_SOURCE_SUPPORTED'
    )
    GROUP BY membership.membership_key, membership.lifecycle_status,
             decision.disposition
)
SELECT
    count(*)::BIGINT AS promoted_membership_count,
    count(*) FILTER (
        WHERE lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
    )::BIGINT AS source_local_promoted_membership_count,
    count(*) FILTER (
        WHERE lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
    )::BIGINT AS cross_source_promoted_membership_count,
    count(*) FILTER (
        WHERE located_supporting_claim_count = 0
           OR disposition IS NULL
           OR (
               lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
               AND independent_supporting_origin_count < 1
           )
           OR (
               lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
               AND independent_supporting_origin_count < 2
           )
    )::BIGINT AS unsupported_promotion_count
FROM membership_promotions;

CREATE TABLE evidence.model_prebuild_source_profile (
    source_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    source_role TEXT NOT NULL,
    sensory_method_family TEXT NOT NULL,
    preparation_families TEXT[] NOT NULL,
    roast_schemes TEXT[] NOT NULL,
    milk_modes TEXT[] NOT NULL,
    participant_type TEXT NOT NULL,
    languages TEXT[] NOT NULL,
    counts_as_sensory_outcome BOOLEAN NOT NULL,
    counts_as_ordinary_user BOOLEAN NOT NULL,
    counts_as_reference_panel BOOLEAN NOT NULL,
    counts_as_milk_sensory BOOLEAN NOT NULL,
    chemistry_only BOOLEAN NOT NULL,
    preparation_only BOOLEAN NOT NULL,
    survey_without_sensory_variables BOOLEAN NOT NULL,
    source_local_observation_row_count INTEGER NOT NULL,
    source_local_sample_count INTEGER NOT NULL,
    participant_or_panel_count INTEGER NOT NULL,
    empirical_coverage_cell_count INTEGER NOT NULL,
    crossed_preparation_roast_cell_count INTEGER NOT NULL,
    annotation_complete BOOLEAN NOT NULL,
    rights_review_complete BOOLEAN NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_source_profile_pk PRIMARY KEY (source_key),
    CONSTRAINT model_prebuild_source_profile_source_fk FOREIGN KEY (
        source_key, source_family_key
    ) REFERENCES evidence.relationship_source (
        source_key, source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_prebuild_source_profile_role_ck CHECK (
        source_role IN (
            'SENSORY_OUTCOME', 'QUESTION_INSTRUMENT',
            'CONTEMPORARY_LANGUAGE', 'ZH_HANS_LANGUAGE'
        )
        AND sensory_method_family IN (
            'RATA_HEDONIC', 'TRAINED_DESCRIPTIVE', 'Q_GRADER_CUPPING',
            'CATA_HEDONIC', 'INSTRUMENT_ONLY'
        )
        AND participant_type IN (
            'ORDINARY_USER', 'TRAINED_PANEL', 'EXPERT_PANEL',
            'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT model_prebuild_source_profile_counts_ck CHECK (
        source_local_observation_row_count >= 0
        AND source_local_sample_count >= 0
        AND participant_or_panel_count >= 0
        AND empirical_coverage_cell_count >= 0
        AND crossed_preparation_roast_cell_count >= 0
        AND cardinality(preparation_families) >= 1
        AND cardinality(roast_schemes) >= 1
        AND cardinality(milk_modes) >= 1
        AND cardinality(languages) >= 1
    ),
    CONSTRAINT model_prebuild_source_profile_semantics_ck CHECK (
        NOT (chemistry_only AND counts_as_sensory_outcome)
        AND NOT (preparation_only AND counts_as_milk_sensory)
        AND NOT (survey_without_sensory_variables AND counts_as_sensory_outcome)
        AND (NOT counts_as_milk_sensory OR counts_as_sensory_outcome)
        AND (NOT counts_as_ordinary_user OR counts_as_sensory_outcome)
        AND (NOT counts_as_reference_panel OR counts_as_sensory_outcome)
        AND (NOT counts_as_sensory_outcome OR (
            source_local_observation_row_count > 0
            AND source_local_sample_count > 0
            AND empirical_coverage_cell_count > 0
        ))
    ),
    CONSTRAINT model_prebuild_source_profile_review_ck CHECK (
        annotation_complete AND rights_review_complete
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE TABLE evidence.model_prebuild_feature_definition (
    feature_key TEXT NOT NULL,
    semantics TEXT NOT NULL,
    source_method TEXT NOT NULL,
    data_type TEXT NOT NULL,
    unit TEXT NOT NULL,
    missingness_semantics TEXT[] NOT NULL,
    available_source_families TEXT[] NOT NULL,
    harmonization_status TEXT NOT NULL,
    model_use_status TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_feature_definition_pk PRIMARY KEY (feature_key),
    CONSTRAINT model_prebuild_feature_definition_key_ck CHECK (
        feature_key = lower(btrim(feature_key)) AND feature_key <> ''
        AND semantics = btrim(semantics) AND semantics <> ''
        AND source_method = btrim(source_method) AND source_method <> ''
        AND data_type IN ('BOOLEAN', 'NUMERIC', 'TEXT', 'CATEGORY', 'ARRAY')
        AND unit = btrim(unit) AND unit <> ''
        AND cardinality(missingness_semantics) >= 1
        AND cardinality(available_source_families) >= 1
        AND harmonization_status IN (
            'SOURCE_LOCAL_ONLY', 'SEMANTICALLY_COMPATIBLE',
            'PARTIALLY_COMPATIBLE', 'NOT_COMPATIBLE', 'UNRESOLVED'
        )
        AND model_use_status = 'PREBUILD_ONLY'
        AND limitation = btrim(limitation) AND limitation <> ''
    ),
    CONSTRAINT model_prebuild_feature_missingness_ck CHECK (
        missingness_semantics <@ ARRAY[
            'NOT_REPORTED', 'NOT_MEASURED', 'NOT_APPLICABLE',
            'SOURCE_UNKNOWN', 'REPORTED_UNRESOLVED',
            'STRUCTURALLY_MISSING'
        ]::TEXT[]
    )
);

CREATE TABLE evidence.model_prebuild_source_partition (
    partition_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    dataset_snapshot_key TEXT NOT NULL,
    source_registry_path TEXT NOT NULL,
    coffee_identity_availability TEXT NOT NULL,
    participant_type TEXT NOT NULL,
    sensory_method TEXT NOT NULL,
    context_fields TEXT[] NOT NULL,
    descriptor_fields TEXT[] NOT NULL,
    language_fields TEXT[] NOT NULL,
    sample_count INTEGER NOT NULL,
    row_count INTEGER NOT NULL,
    feature_keys TEXT[] NOT NULL,
    rights_boundary TEXT NOT NULL,
    grouping_keys TEXT[] NOT NULL,
    future_training_surface_status TEXT NOT NULL,
    compatible_join_group TEXT NOT NULL,
    CONSTRAINT model_prebuild_source_partition_pk PRIMARY KEY (partition_key),
    CONSTRAINT model_prebuild_source_partition_key_ck CHECK (
        partition_key = lower(btrim(partition_key)) AND partition_key <> ''
        AND source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND dataset_snapshot_key = lower(btrim(dataset_snapshot_key))
        AND dataset_snapshot_key <> ''
        AND source_registry_path = btrim(source_registry_path)
        AND source_registry_path <> ''
        AND coffee_identity_availability IN (
            'AVAILABLE', 'PARTIAL', 'NOT_REPORTED', 'NOT_APPLICABLE'
        )
        AND participant_type IN (
            'ORDINARY_USER', 'TRAINED_PANEL', 'EXPERT_PANEL',
            'NOT_APPLICABLE'
        )
        AND sample_count >= 0 AND row_count >= 0
        AND cardinality(context_fields) >= 1
        AND cardinality(descriptor_fields) >= 1
        AND cardinality(language_fields) >= 1
        AND cardinality(feature_keys) >= 1
        AND cardinality(grouping_keys) >= 1
        AND rights_boundary = btrim(rights_boundary)
        AND rights_boundary <> ''
        AND future_training_surface_status IN (
            'ELIGIBLE_AFTER_FUTURE_PROTOCOL', 'INELIGIBLE',
            'METADATA_ONLY'
        )
        AND compatible_join_group = btrim(compatible_join_group)
        AND compatible_join_group <> ''
    )
);

CREATE FUNCTION evidence.enforce_model_prebuild_partition_source_family()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_model_prebuild_partition_source_family$
BEGIN
    IF NEW.partition_key NOT LIKE 'partition.baseline.%'
       AND NOT EXISTS (
           SELECT 1 FROM evidence.source_family AS family
           WHERE family.source_family_key = NEW.source_family_key
             AND family.admitted
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503',
            CONSTRAINT = 'model_prebuild_partition_source_family_fk',
            MESSAGE = 'Round 3H partitions require an admitted source family';
    END IF;
    RETURN NEW;
END
$enforce_model_prebuild_partition_source_family$;

CREATE TRIGGER model_prebuild_partition_source_family_biu
BEFORE INSERT OR UPDATE ON evidence.model_prebuild_source_partition
FOR EACH ROW EXECUTE FUNCTION
    evidence.enforce_model_prebuild_partition_source_family();

CREATE TABLE evidence.model_prebuild_partition_feature (
    partition_key TEXT NOT NULL,
    feature_key TEXT NOT NULL,
    availability_status TEXT NOT NULL,
    source_field_locator TEXT NOT NULL,
    missingness_semantics TEXT NOT NULL,
    harmonization_status TEXT NOT NULL,
    pooling_allowed BOOLEAN NOT NULL,
    CONSTRAINT model_prebuild_partition_feature_pk PRIMARY KEY (
        partition_key, feature_key
    ),
    CONSTRAINT model_prebuild_partition_feature_partition_fk FOREIGN KEY (
        partition_key
    ) REFERENCES evidence.model_prebuild_source_partition (partition_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_prebuild_partition_feature_feature_fk FOREIGN KEY (
        feature_key
    ) REFERENCES evidence.model_prebuild_feature_definition (feature_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_prebuild_partition_feature_semantics_ck CHECK (
        availability_status IN (
            'AVAILABLE', 'PARTIAL', 'NOT_REPORTED', 'NOT_MEASURED',
            'NOT_APPLICABLE', 'SOURCE_UNKNOWN', 'REPORTED_UNRESOLVED',
            'STRUCTURALLY_MISSING'
        )
        AND source_field_locator = btrim(source_field_locator)
        AND source_field_locator <> ''
        AND missingness_semantics IN (
            'NOT_REPORTED', 'NOT_MEASURED', 'NOT_APPLICABLE',
            'SOURCE_UNKNOWN', 'REPORTED_UNRESOLVED',
            'STRUCTURALLY_MISSING'
        )
        AND harmonization_status IN (
            'SOURCE_LOCAL_ONLY', 'SEMANTICALLY_COMPATIBLE',
            'PARTIALLY_COMPATIBLE', 'NOT_COMPATIBLE', 'UNRESOLVED'
        )
        AND pooling_allowed = (
            harmonization_status = 'SEMANTICALLY_COMPATIBLE'
        )
    )
);

CREATE TABLE evidence.model_prebuild_split_candidate (
    split_candidate_key TEXT NOT NULL,
    partition_key TEXT NOT NULL,
    grouping_dimensions TEXT[] NOT NULL,
    prohibited_cross_split_keys TEXT[] NOT NULL,
    split_status TEXT NOT NULL,
    leakage_risk_status TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_split_candidate_pk PRIMARY KEY (
        split_candidate_key
    ),
    CONSTRAINT model_prebuild_split_candidate_partition_fk FOREIGN KEY (
        partition_key
    ) REFERENCES evidence.model_prebuild_source_partition (partition_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_prebuild_split_candidate_shape_ck CHECK (
        split_candidate_key = lower(btrim(split_candidate_key))
        AND split_candidate_key <> ''
        AND cardinality(grouping_dimensions) >= 1
        AND cardinality(prohibited_cross_split_keys) >= 1
        AND split_status = 'CANDIDATE_NOT_EXECUTED'
        AND leakage_risk_status IN (
            'CONTROL_DEFINED', 'PARTIAL_CONTROL', 'UNRESOLVED'
        )
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE FUNCTION evidence.enforce_model_prebuild_split_grouping()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_model_prebuild_split_grouping$
DECLARE
    partition_grouping_keys TEXT[];
BEGIN
    SELECT grouping_keys INTO partition_grouping_keys
    FROM evidence.model_prebuild_source_partition
    WHERE partition_key = NEW.partition_key;

    IF partition_grouping_keys @> ARRAY['coffee_identity']::TEXT[]
       AND NOT (
           NEW.grouping_dimensions @> ARRAY['coffee_identity']::TEXT[]
           AND NEW.prohibited_cross_split_keys
               @> ARRAY['coffee_identity']::TEXT[]
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'model_prebuild_same_coffee_split_ck',
            MESSAGE = 'coffee identity must remain grouped and prohibited across future split candidates';
    END IF;

    IF NOT (NEW.prohibited_cross_split_keys <@ NEW.grouping_dimensions) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'model_prebuild_split_grouping_subset_ck',
            MESSAGE = 'prohibited cross-split keys must be declared grouping dimensions';
    END IF;
    RETURN NEW;
END
$enforce_model_prebuild_split_grouping$;

CREATE TRIGGER model_prebuild_split_grouping_biu
BEFORE INSERT OR UPDATE ON evidence.model_prebuild_split_candidate
FOR EACH ROW EXECUTE FUNCTION evidence.enforce_model_prebuild_split_grouping();

CREATE TABLE audit.model_prebuild_context_cell (
    context_cell_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    coffee_identity TEXT NOT NULL,
    preparation_family TEXT NOT NULL,
    roast_source_label TEXT NOT NULL,
    milk_mode TEXT NOT NULL,
    sensory_method TEXT NOT NULL,
    participant_type TEXT NOT NULL,
    language_code TEXT NOT NULL,
    evidence_status TEXT NOT NULL,
    zero_filled BOOLEAN NOT NULL,
    crossed_preparation_roast_eligible BOOLEAN NOT NULL,
    source_row_locator TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_context_cell_pk PRIMARY KEY (context_cell_key),
    CONSTRAINT model_prebuild_context_cell_observed_ck CHECK (
        context_cell_key = lower(btrim(context_cell_key))
        AND context_cell_key <> ''
        AND source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND coffee_identity = btrim(coffee_identity)
        AND coffee_identity <> ''
        AND preparation_family = btrim(preparation_family)
        AND preparation_family <> ''
        AND roast_source_label = btrim(roast_source_label)
        AND roast_source_label <> ''
        AND milk_mode IN ('BLACK', 'DAIRY', 'PLANT_ALTERNATIVE')
        AND participant_type IN (
            'ORDINARY_USER', 'TRAINED_PANEL', 'EXPERT_PANEL'
        )
        AND language_code IN ('en', 'id', 'it', 'th')
        AND evidence_status = 'OBSERVED_SOURCE_LOCAL_EVIDENCE'
        AND NOT zero_filled
        AND source_row_locator = btrim(source_row_locator)
        AND source_row_locator <> ''
        AND limitation = btrim(limitation) AND limitation <> ''
        AND (NOT crossed_preparation_roast_eligible
             OR roast_source_label <> 'SOURCE_UNKNOWN')
    ),
    CONSTRAINT model_prebuild_context_cell_unique_uq UNIQUE (
        source_family_key, coffee_identity, preparation_family,
        roast_source_label, milk_mode, sensory_method,
        participant_type, language_code
    )
);

CREATE TABLE corpus.model_prebuild_language_source_decision (
    decision_key TEXT NOT NULL,
    candidate_key TEXT NOT NULL,
    language_plane TEXT NOT NULL,
    rights_status TEXT NOT NULL,
    observation_status TEXT NOT NULL,
    source_authored BOOLEAN NOT NULL,
    machine_translated BOOLEAN NOT NULL,
    artificial_variant BOOLEAN NOT NULL,
    evidence_role TEXT NOT NULL DEFAULT 'CANDIDATE_REVIEW',
    countable_family_gain INTEGER NOT NULL,
    countable_document_gain INTEGER NOT NULL,
    countable_expression_gain INTEGER NOT NULL,
    decision TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_language_source_decision_pk PRIMARY KEY (
        decision_key
    ),
    CONSTRAINT model_prebuild_language_source_decision_candidate_uq UNIQUE (
        candidate_key, language_plane
    ),
    CONSTRAINT model_prebuild_language_source_decision_counts_ck CHECK (
        language_plane IN ('CONTEMPORARY', 'ZH_HANS')
        AND countable_family_gain >= 0
        AND countable_document_gain >= 0
        AND countable_expression_gain >= 0
        AND NOT machine_translated
        AND NOT artificial_variant
        AND evidence_role IN (
            'CANDIDATE_REVIEW', 'OBSERVED_COFFEE_TASTING_LANGUAGE',
            'DICTIONARY_REFERENCE', 'PREPARATION_REFERENCE',
            'FORMAL_STANDARD', 'SYNTHETIC_STIMULUS'
        )
        AND (
            (countable_family_gain = 0 AND countable_document_gain = 0
                AND countable_expression_gain = 0)
            OR (
                source_authored
                AND observation_status = 'VERIFIED_OBSERVED'
                AND evidence_role = 'OBSERVED_COFFEE_TASTING_LANGUAGE'
            )
        )
        AND decision = btrim(decision) AND decision <> ''
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE TABLE calibration.model_prebuild_question_evidence (
    question_evidence_key TEXT NOT NULL,
    question_range_target_id BIGINT NOT NULL,
    supporting_source_families TEXT[] NOT NULL,
    independent_origin_count INTEGER NOT NULL,
    research_decision TEXT NOT NULL,
    research_basis TEXT NOT NULL,
    user_validation_status TEXT NOT NULL,
    information_gain_status TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_question_evidence_pk PRIMARY KEY (
        question_evidence_key
    ),
    CONSTRAINT model_prebuild_question_evidence_target_fk FOREIGN KEY (
        question_range_target_id
    ) REFERENCES calibration.question_range_target (
        question_range_target_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_prebuild_question_evidence_target_uq UNIQUE (
        question_range_target_id
    ),
    CONSTRAINT model_prebuild_question_evidence_review_ck CHECK (
        question_evidence_key = lower(btrim(question_evidence_key))
        AND question_evidence_key <> ''
        AND cardinality(supporting_source_families) >= 1
        AND independent_origin_count >= 1
        AND independent_origin_count = cardinality(supporting_source_families)
        AND research_decision = 'RESEARCH_SUPPORT_ADDED'
        AND research_basis = btrim(research_basis)
        AND research_basis <> ''
        AND user_validation_status = 'NOT_USER_VALIDATED'
        AND information_gain_status = 'NOT_ESTIMABLE'
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE TABLE audit.model_prebuild_range_evidence_summary (
    range_key TEXT NOT NULL,
    source_local_supporting_membership_count INTEGER NOT NULL,
    cross_source_supporting_membership_count INTEGER NOT NULL,
    supporting_source_families TEXT[] NOT NULL,
    challenging_source_families TEXT[] NOT NULL,
    range_lifecycle_changed BOOLEAN NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_range_evidence_summary_pk PRIMARY KEY (
        range_key
    ),
    CONSTRAINT model_prebuild_range_evidence_summary_range_fk FOREIGN KEY (
        range_key
    ) REFERENCES corpus.association_range (range_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_prebuild_range_evidence_summary_counts_ck CHECK (
        source_local_supporting_membership_count >= 0
        AND cross_source_supporting_membership_count >= 0
        AND cardinality(supporting_source_families) >= 0
        AND cardinality(challenging_source_families) >= 0
        AND NOT range_lifecycle_changed
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE TABLE audit.model_prebuild_leakage_risk (
    leakage_risk_key TEXT NOT NULL,
    risk_type TEXT NOT NULL,
    affected_partitions TEXT[] NOT NULL,
    detection_rule TEXT NOT NULL,
    control_status TEXT NOT NULL,
    control_key TEXT NOT NULL,
    audit_pass BOOLEAN NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT model_prebuild_leakage_risk_pk PRIMARY KEY (leakage_risk_key),
    CONSTRAINT model_prebuild_leakage_risk_control_ck CHECK (
        leakage_risk_key = lower(btrim(leakage_risk_key))
        AND leakage_risk_key <> ''
        AND risk_type IN (
            'SAME_COFFEE', 'SAME_PARTICIPANT', 'DUPLICATE_PRODUCT_PAGE',
            'MIRRORED_SOURCE', 'DERIVED_RAW_OVERLAP',
            'TRANSLATION_VARIANT', 'CONTEXT_DERIVATIVE'
        )
        AND cardinality(affected_partitions) >= 1
        AND detection_rule = btrim(detection_rule)
        AND detection_rule <> ''
        AND control_status IN ('CONTROL_DEFINED', 'NOT_APPLICABLE')
        AND control_key = btrim(control_key) AND control_key <> ''
        AND audit_pass
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE TABLE audit.model_prebuild_batch_result (
    batch_key TEXT NOT NULL,
    targeted_gap TEXT NOT NULL,
    new_source_family_count INTEGER NOT NULL,
    new_coverage_count INTEGER NOT NULL,
    meaningful_coverage_gain BOOLEAN NOT NULL,
    consecutive_no_gain_number INTEGER NOT NULL,
    stop_status TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    CONSTRAINT model_prebuild_batch_result_pk PRIMARY KEY (batch_key),
    CONSTRAINT model_prebuild_batch_result_shape_ck CHECK (
        batch_key = lower(btrim(batch_key)) AND batch_key <> ''
        AND targeted_gap = btrim(targeted_gap) AND targeted_gap <> ''
        AND new_source_family_count >= 0
        AND new_coverage_count >= 0
        AND consecutive_no_gain_number BETWEEN 0 AND 2
        AND stop_status IN ('CONTINUE', 'STOP_MINIMUM_REACHED',
            'STOP_TWO_CONSECUTIVE_NO_GAIN')
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
        AND (meaningful_coverage_gain OR (
            new_source_family_count = 0 AND new_coverage_count = 0
        ))
    )
);

CREATE TABLE audit.model_prebuild_threshold_revision (
    revision_key TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    original_value TEXT NOT NULL,
    revised_value TEXT NOT NULL,
    written_reason TEXT NOT NULL,
    epistemic_impact TEXT NOT NULL,
    invalidity_evidence TEXT NOT NULL,
    decision_record_key TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT model_prebuild_threshold_revision_pk PRIMARY KEY (revision_key),
    CONSTRAINT model_prebuild_threshold_revision_decision_ck CHECK (
        revision_key = lower(btrim(revision_key)) AND revision_key <> ''
        AND metric_key = lower(btrim(metric_key)) AND metric_key <> ''
        AND original_value <> revised_value
        AND written_reason = btrim(written_reason) AND written_reason <> ''
        AND epistemic_impact = btrim(epistemic_impact)
        AND epistemic_impact <> ''
        AND invalidity_evidence = btrim(invalidity_evidence)
        AND invalidity_evidence <> ''
        AND decision_record_key = btrim(decision_record_key)
        AND decision_record_key <> ''
    )
);

CREATE TABLE audit.model_prebuild_execution_guard (
    guard_key TEXT NOT NULL,
    ranking_model_run_count INTEGER NOT NULL,
    adaptive_policy_run_count INTEGER NOT NULL,
    deep_learning_run_count INTEGER NOT NULL,
    embedding_run_count INTEGER NOT NULL,
    pgvector_required BOOLEAN NOT NULL,
    real_human_collection_performed BOOLEAN NOT NULL,
    real_observation_count INTEGER NOT NULL,
    product_frontend_modified BOOLEAN NOT NULL,
    canonical_concept_change_count INTEGER NOT NULL,
    CONSTRAINT model_prebuild_execution_guard_pk PRIMARY KEY (guard_key),
    CONSTRAINT model_prebuild_execution_guard_prohibition_ck CHECK (
        ranking_model_run_count = 0
        AND adaptive_policy_run_count = 0
        AND deep_learning_run_count = 0
        AND embedding_run_count = 0
        AND NOT pgvector_required
        AND NOT real_human_collection_performed
        AND real_observation_count = 0
        AND NOT product_frontend_modified
        AND canonical_concept_change_count = 0
    )
);

CREATE TABLE audit.model_prebuild_checkpoint (
    checkpoint_key TEXT NOT NULL,
    source_sha TEXT NOT NULL,
    expected_state_commit_sha TEXT NOT NULL,
    expected_state_file TEXT NOT NULL,
    expected_state_frozen_before_import BOOLEAN NOT NULL,
    threshold_revision_count INTEGER NOT NULL,
    canonical_concept_count_before INTEGER NOT NULL,
    active_sensory_attribute_count_before INTEGER NOT NULL,
    baseline_empirical_coverage_cell_count INTEGER NOT NULL,
    acquisition_stop_status TEXT NOT NULL,
    CONSTRAINT model_prebuild_checkpoint_pk PRIMARY KEY (checkpoint_key),
    CONSTRAINT model_prebuild_checkpoint_contract_ck CHECK (
        source_sha ~ '^[0-9a-f]{40}$'
        AND expected_state_commit_sha ~ '^[0-9a-f]{40}$'
        AND expected_state_file =
            'db/data/round3h/model_prebuild_expected_state.tsv'
        AND expected_state_frozen_before_import
        AND threshold_revision_count = 0
        AND canonical_concept_count_before = 130
        AND active_sensory_attribute_count_before = 92
        AND baseline_empirical_coverage_cell_count = 52
        AND acquisition_stop_status =
            'STOP_TWO_CONSECUTIVE_TARGETED_NO_GAIN_BATCHES'
    )
);

CREATE TABLE audit.model_prebuild_artifact_hash (
    artifact_key TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    artifact_role TEXT NOT NULL,
    CONSTRAINT model_prebuild_artifact_hash_pk PRIMARY KEY (artifact_key),
    CONSTRAINT model_prebuild_artifact_hash_value_ck CHECK (
        artifact_key = lower(btrim(artifact_key)) AND artifact_key <> ''
        AND artifact_path = btrim(artifact_path) AND artifact_path <> ''
        AND sha256 ~ '^[0-9a-f]{64}$'
        AND artifact_role IN (
            'MODEL_PREBUILD_MANIFEST', 'EXPECTED_STATE',
            'SOURCE_FILE', 'AUDIT_RECEIPT'
        )
    )
);

CREATE TABLE audit.model_prebuild_data_access_request (
    request_key TEXT NOT NULL,
    source_doi TEXT NOT NULL,
    corresponding_author_route TEXT NOT NULL,
    desired_file_structure TEXT NOT NULL,
    requested_reuse_terms TEXT NOT NULL,
    prepared_request_text_path TEXT NOT NULL,
    request_ready BOOLEAN NOT NULL,
    request_sent BOOLEAN NOT NULL,
    CONSTRAINT model_prebuild_data_access_request_pk PRIMARY KEY (request_key),
    CONSTRAINT model_prebuild_data_access_request_unsent_ck CHECK (
        request_key = lower(btrim(request_key)) AND request_key <> ''
        AND source_doi = btrim(source_doi) AND source_doi <> ''
        AND corresponding_author_route = btrim(corresponding_author_route)
        AND corresponding_author_route <> ''
        AND desired_file_structure = btrim(desired_file_structure)
        AND desired_file_structure <> ''
        AND requested_reuse_terms = btrim(requested_reuse_terms)
        AND requested_reuse_terms <> ''
        AND prepared_request_text_path = btrim(prepared_request_text_path)
        AND prepared_request_text_path <> ''
        AND request_ready AND NOT request_sent
    )
);

CREATE TABLE audit.model_prebuild_constraint_registry (
    constraint_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    rule TEXT NOT NULL,
    enforcement_layer TEXT NOT NULL,
    negative_test TEXT NOT NULL,
    CONSTRAINT model_prebuild_constraint_registry_pk PRIMARY KEY (
        constraint_key
    ),
    CONSTRAINT model_prebuild_constraint_registry_text_ck CHECK (
        constraint_key = lower(btrim(constraint_key))
        AND constraint_key <> ''
        AND scope = btrim(scope) AND scope <> ''
        AND rule = btrim(rule) AND rule <> ''
        AND enforcement_layer IN (
            'POSTGRESQL_CONSTRAINT', 'POSTGRESQL_TRIGGER',
            'AUDIT_QUERY', 'CI_GATE', 'CURATION_POLICY'
        )
        AND negative_test = btrim(negative_test)
        AND negative_test <> ''
    )
);

CREATE TABLE audit.model_prebuild_readiness_assertion (
    assertion_key TEXT NOT NULL,
    model_prebuild_data_ready BOOLEAN NOT NULL,
    readiness_state TEXT NOT NULL,
    asserted_at TIMESTAMPTZ NOT NULL,
    evidence_path TEXT NOT NULL,
    CONSTRAINT model_prebuild_readiness_assertion_pk PRIMARY KEY (
        assertion_key
    ),
    CONSTRAINT model_prebuild_readiness_assertion_state_ck CHECK (
        readiness_state IN (
            'MODEL_PREBUILD_READY',
            'MODEL_PREBUILD_READY_BLACK_COFFEE_ONLY',
            'COMPLETE_WITH_DATA_COVERAGE_GAP',
            'BLOCKED_RIGHTS', 'BLOCKED_PRIVACY',
            'BLOCKED_REPRODUCIBILITY', 'BLOCKED_REMOTE_CI'
        )
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
    )
);

CREATE FUNCTION audit.prevent_model_prebuild_model_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_model_prebuild_model_run$
BEGIN
    IF EXISTS (SELECT 1 FROM audit.model_prebuild_checkpoint)
       AND (
           NEW.run_configuration ->> 'round' = '3H'
           OR coalesce(
               (NEW.run_configuration ->> 'prebuild')::BOOLEAN,
               FALSE
           )
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'model_prebuild_model_run_prohibited_ck',
            MESSAGE = 'Round 3H is metadata-only and cannot create model runs';
    END IF;
    RETURN NEW;
END
$prevent_model_prebuild_model_run$;

CREATE TRIGGER model_prebuild_model_run_prohibited_biu
BEFORE INSERT OR UPDATE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION audit.prevent_model_prebuild_model_run();

CREATE FUNCTION audit.prevent_model_prebuild_model_version()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_model_prebuild_model_version$
BEGIN
    IF EXISTS (SELECT 1 FROM audit.model_prebuild_checkpoint)
       AND (
           NEW.configuration ->> 'round' = '3H'
           OR coalesce(
               (NEW.configuration ->> 'embeddings')::BOOLEAN,
               FALSE
           )
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'model_prebuild_embedding_generation_prohibited_ck',
            MESSAGE = 'Round 3H cannot create model or embedding artifacts';
    END IF;
    RETURN NEW;
END
$prevent_model_prebuild_model_version$;

CREATE TRIGGER model_prebuild_model_version_prohibited_biu
BEFORE INSERT OR UPDATE ON ml.model_version
FOR EACH ROW EXECUTE FUNCTION audit.prevent_model_prebuild_model_version();

COMMIT;
