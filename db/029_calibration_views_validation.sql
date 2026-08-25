\set ON_ERROR_STOP on

BEGIN;

CREATE INDEX roast_batch_category_idx
    ON calibration.roast_batch (roast_category_id, coffee_lot_id);
CREATE INDEX preparation_condition_family_idx
    ON calibration.preparation_condition (preparation_concept_id, study_id);
CREATE INDEX beverage_sample_condition_idx
    ON calibration.beverage_sample (
        study_id, preparation_condition_id, roast_batch_id, replicate_number
    );
CREATE INDEX presentation_sample_idx
    ON calibration.presentation (beverage_sample_id, session_id);
CREATE INDEX question_assignment_policy_idx
    ON calibration.question_assignment (policy_code, question_id, step_number);
CREATE INDEX descriptor_response_concept_idx
    ON calibration.descriptor_response (concept_id, sensory_observation_id);
CREATE INDEX candidate_judgment_concept_idx
    ON calibration.candidate_reference_judgment (concept_id, usefulness_code);

CREATE VIEW calibration.v_study_readiness AS
SELECT
    study.study_key,
    study.human_participant_ethics_required,
    study.institutional_approval_status,
    study.public_data_consent_required,
    study.ethics_or_approval_gate,
    study.consent_material_ready,
    study.public_release_rights_ready,
    study.empirical_observation_count,
    study.ethics_or_approval_gate
      AND study.consent_material_ready
      AND study.public_release_rights_ready AS real_collection_permitted
FROM calibration.study AS study;

CREATE VIEW calibration.v_question_bank AS
SELECT
    question.question_key,
    question.logical_question_code,
    question.language_tag_code,
    question.prompt_text,
    question.min_selections,
    question.max_selections,
    question.interaction_position_code,
    count(option.question_option_id)::INTEGER AS option_count
FROM calibration.question AS question
LEFT JOIN calibration.question_option AS option
  ON option.question_id = question.question_id
WHERE question.lifecycle_status_code = 'active'
GROUP BY question.question_id;

CREATE VIEW calibration.v_calibration_observation_inventory AS
SELECT
    study.study_key,
    count(DISTINCT sample.beverage_sample_id) FILTER (
      WHERE sample.record_origin_code = 'real_observation'
    ) AS real_beverage_sample_count,
    count(DISTINCT observation.sensory_observation_id) FILTER (
      WHERE observation.record_origin_code = 'real_observation'
    ) AS real_sensory_observation_count,
    count(DISTINCT observation.sensory_observation_id) FILTER (
      WHERE observation.record_origin_code = 'DRY_RUN_FIXTURE'
    ) AS dry_run_sensory_observation_count,
    CASE WHEN count(DISTINCT observation.sensory_observation_id) FILTER (
      WHERE observation.record_origin_code = 'real_observation'
    ) = 0 THEN 'NOT_ESTIMABLE' ELSE 'ESTIMABLE' END AS estimability_status
FROM calibration.study AS study
LEFT JOIN calibration.beverage_sample AS sample ON sample.study_id = study.study_id
LEFT JOIN calibration.presentation AS presentation
  ON presentation.beverage_sample_id = sample.beverage_sample_id
LEFT JOIN calibration.sensory_observation AS observation
  ON observation.presentation_id = presentation.presentation_id
GROUP BY study.study_id;

CREATE FUNCTION audit.run_round3c_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3c_validation_queries$
    WITH checks AS (
      SELECT 'round3c.current_c0_exactly_8'::TEXT AS check_key,
             abs(8 - count(*))::BIGINT AS violation_count
      FROM context.v_current_user_preparation
      UNION ALL
      SELECT 'round3c.current_c1_exactly_7', abs(7 - count(*))::BIGINT
      FROM context.v_current_user_roast
      UNION ALL
      SELECT 'round3c.c1_required_middle_distinctions',
             abs(3 - count(*))::BIGINT
      FROM context.v_current_user_roast
      WHERE interaction_code IN ('medium_light', 'medium', 'medium_dark')
      UNION ALL
      SELECT 'round3c.question_bank_language_rows_12',
             abs(12 - count(*))::BIGINT
      FROM calibration.v_question_bank
      UNION ALL
      SELECT 'round3c.question_bank_six_logical_pairs',
             count(*) FILTER (WHERE language_count <> 2)::BIGINT
      FROM (
        SELECT logical_question_code, count(DISTINCT language_tag_code) AS language_count
        FROM calibration.v_question_bank GROUP BY logical_question_code
      ) AS pairs
      UNION ALL
      SELECT 'round3c.question_option_count_valid', count(*)::BIGINT
      FROM calibration.v_question_bank
      WHERE option_count NOT BETWEEN 2 AND 8
         OR max_selections > option_count
      UNION ALL
      SELECT 'round3c.no_direct_identifier_metadata', count(*)::BIGINT
      FROM calibration.assessor
      WHERE NOT calibration.reject_direct_identifiers(approved_public_metadata)
      UNION ALL
      SELECT 'round3c.raw_observation_role_only', count(*)::BIGINT
      FROM calibration.sensory_observation
      WHERE observation_role_code <> 'raw_observation'
      UNION ALL
      SELECT 'round3c.model_output_role_only', count(*)::BIGINT
      FROM calibration.model_candidate_output
      WHERE output_role_code <> 'model_candidate_reference'
      UNION ALL
      SELECT 'round3c.grouped_split_lot_exclusive',
             count(*)::BIGINT
      FROM (
        SELECT analysis_plan_id, coffee_lot_id
        FROM calibration.grouped_split
        GROUP BY analysis_plan_id, coffee_lot_id
        HAVING count(DISTINCT split_code) > 1
      ) AS leakage
      UNION ALL
      SELECT 'round3c.public_release_metadata_complete', count(*)::BIGINT
      FROM calibration.release_snapshot
      WHERE lifecycle_status_code = 'public'
        AND (manifest_sha256 IS NULL OR checksums_sha256 IS NULL
             OR license_spdx IS NULL OR rights_statement IS NULL
             OR split_snapshot_sha256 IS NULL)
      UNION ALL
      SELECT 'round3c.no_seeded_empirical_observations', count(*)::BIGINT
      FROM calibration.study
      WHERE empirical_observation_count <> 0
      UNION ALL
      SELECT 'round3c.real_collection_gate_closed', count(*)::BIGINT
      FROM calibration.v_study_readiness
      WHERE real_collection_permitted
      UNION ALL
      SELECT 'round3c.protocol_and_analysis_frozen',
             (SELECT count(*) FROM calibration.study)::BIGINT
             - least(
                 (SELECT count(*) FROM calibration.protocol_version WHERE is_frozen),
                 (SELECT count(*) FROM calibration.analysis_plan WHERE is_frozen)
               )::BIGINT
    )
    SELECT checks.check_key, checks.violation_count,
           checks.violation_count = 0 AS passed
    FROM checks
$run_round3c_validation_queries$;

COMMENT ON VIEW calibration.v_calibration_observation_inventory IS
    'Separates real observations from conspicuous engineering fixtures and makes zero-data estimability explicit.';

COMMIT;
