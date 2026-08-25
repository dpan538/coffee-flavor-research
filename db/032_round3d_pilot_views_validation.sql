\set ON_ERROR_STOP on

BEGIN;

CREATE INDEX pilot_session_slot_snapshot_cohort_idx
    ON calibration.pilot_session_slot (
        pilot_matrix_snapshot_id, cohort_code, assessor_slot_code
    );
CREATE INDEX pilot_presentation_slot_sample_idx
    ON calibration.pilot_presentation_slot (
        beverage_sample_id, pilot_session_slot_id
    );
CREATE INDEX pilot_question_assignment_presentation_idx
    ON calibration.pilot_question_assignment_slot (
        pilot_presentation_slot_id, step_number
    );
CREATE INDEX engineering_dry_run_case_snapshot_idx
    ON calibration.engineering_dry_run_case (
        pilot_matrix_snapshot_id, expected_stop_step
    );
CREATE INDEX capture_import_row_batch_origin_idx
    ON calibration.capture_import_row (
        capture_import_batch_id, record_origin_code
    );

CREATE VIEW calibration.v_round3d_pilot_inventory AS
SELECT
    snapshot.pilot_matrix_snapshot_key,
    snapshot.matrix_sha256,
    snapshot.randomization_sha256,
    snapshot.question_assignment_sha256,
    snapshot.protocol_sha256,
    snapshot.split_inventory_sha256,
    (SELECT count(*)::INTEGER FROM calibration.coffee_lot AS lot
     WHERE lot.study_id = snapshot.study_id) AS coffee_lot_count,
    (SELECT count(*)::INTEGER
     FROM calibration.roast_batch AS roast
     JOIN calibration.coffee_lot AS lot
       ON lot.coffee_lot_id = roast.coffee_lot_id
     WHERE lot.study_id = snapshot.study_id) AS roast_batch_count,
    (SELECT count(*)::INTEGER
     FROM calibration.preparation_condition AS preparation
     WHERE preparation.study_id = snapshot.study_id)
        AS preparation_condition_count,
    (SELECT count(*)::INTEGER
     FROM calibration.beverage_sample AS sample
     WHERE sample.study_id = snapshot.study_id) AS beverage_sample_count,
    (SELECT count(*)::INTEGER
     FROM calibration.pilot_session_slot AS session
     WHERE session.pilot_matrix_snapshot_id =
           snapshot.pilot_matrix_snapshot_id) AS session_slot_count,
    (SELECT count(*)::INTEGER
     FROM calibration.pilot_presentation_slot AS presentation
     JOIN calibration.pilot_session_slot AS session
       ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
     WHERE session.pilot_matrix_snapshot_id =
           snapshot.pilot_matrix_snapshot_id) AS presentation_slot_count,
    (SELECT count(*)::INTEGER
     FROM calibration.pilot_question_assignment_slot AS assignment
     JOIN calibration.pilot_presentation_slot AS presentation
       ON presentation.pilot_presentation_slot_id =
          assignment.pilot_presentation_slot_id
     JOIN calibration.pilot_session_slot AS session
       ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
     WHERE session.pilot_matrix_snapshot_id =
           snapshot.pilot_matrix_snapshot_id) AS question_assignment_slot_count,
    (SELECT count(*)::INTEGER
     FROM calibration.engineering_dry_run_case AS dry_run
     WHERE dry_run.pilot_matrix_snapshot_id =
           snapshot.pilot_matrix_snapshot_id) AS dry_run_fixture_count,
    study.empirical_observation_count AS real_observation_count,
    snapshot.is_frozen
FROM calibration.pilot_matrix_snapshot AS snapshot
JOIN calibration.study AS study ON study.study_id = snapshot.study_id;

CREATE VIEW calibration.v_round3d_analysis_status AS
SELECT
    analysis.analysis_run_key,
    analysis.estimability_status,
    release.version_label AS release_version,
    release.real_observation_count,
    release.dry_run_fixture_count,
    analysis.result_metadata ->> 'analysis_status' AS analysis_status,
    (analysis.result_metadata ->> 'fixture_exclusion_pass')::BOOLEAN
        AS fixture_exclusion_pass,
    (analysis.result_metadata ->> 'deep_learning_model_run')::BOOLEAN
        AS deep_learning_model_run,
    (analysis.result_metadata ->> 'embedding_baseline_run')::BOOLEAN
        AS embedding_baseline_run,
    (analysis.result_metadata ->> 'pgvector_required')::BOOLEAN
        AS pgvector_required,
    analysis.result_metadata -> 'outputs' AS outputs
FROM calibration.analysis_run AS analysis
JOIN calibration.release_snapshot AS release
  ON release.release_snapshot_id = analysis.release_snapshot_id
WHERE analysis.analysis_run_key =
      'analysis_run.round3d.minimum.zero_real_observations';

CREATE FUNCTION audit.run_round3d_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3d_validation_queries$
    WITH checks AS (
      SELECT 'round3d.single_frozen_snapshot'::TEXT AS check_key,
             abs(1 - count(*))::BIGINT AS violation_count
      FROM calibration.pilot_matrix_snapshot
      WHERE is_frozen
      UNION ALL
      SELECT 'round3d.snapshot_contract_exact', count(*)::BIGINT
      FROM calibration.pilot_matrix_snapshot
      WHERE coffee_lot_count <> 2 OR roast_batch_count <> 14
         OR preparation_family_count <> 7 OR roast_category_count <> 7
         OR condition_cell_count <> 66 OR beverage_sample_count <> 132
         OR session_slot_count <> 192 OR presentation_slot_count <> 1512
         OR question_assignment_slot_count <> 3600
         OR dry_run_fixture_count <> 5 OR real_observation_count <> 0
         OR matrix_sha256 <> 'dbd56b90672e00af5fe17a4d8c2c50b996d020a29e39dce04e9bd752de6d356b'
         OR randomization_sha256 <> 'eb7aa3fbfa6daf2d94819c007c42cdb43efcbbe4540335f231907b0b4a6edb4b'
         OR question_assignment_sha256 <> '3e48c83feff27767cf68792f6a9e4c51e80c21aabf0cb419a1cfb02261a528e9'
         OR protocol_sha256 <> '4c759fcae812203c40394d1f510e93c4a83430a3dfb298e832b5ffc49f5924ad'
         OR split_inventory_sha256 <> 'fe76dab2f695a0e7a1d23eb0744c97fb7c832e069cd9b060d26da47c3cebe45a'
      UNION ALL
      SELECT 'round3d.coffee_lot_count_2', abs(2 - count(*))::BIGINT
      FROM calibration.coffee_lot
      WHERE coffee_lot_key LIKE 'pilot.round3d.%'
      UNION ALL
      SELECT 'round3d.roast_batch_count_14', abs(14 - count(*))::BIGINT
      FROM calibration.roast_batch
      WHERE roast_batch_key LIKE 'pilot.round3d.%'
      UNION ALL
      SELECT 'round3d.each_lot_has_seven_roasts', count(*)::BIGINT
      FROM (
        SELECT lot.coffee_lot_id
        FROM calibration.coffee_lot AS lot
        JOIN calibration.roast_batch AS roast
          ON roast.coffee_lot_id = lot.coffee_lot_id
        WHERE lot.coffee_lot_key LIKE 'pilot.round3d.%'
        GROUP BY lot.coffee_lot_id
        HAVING count(DISTINCT roast.roast_category_id) <> 7
      ) AS invalid_lot
      UNION ALL
      SELECT 'round3d.preparation_condition_count_7',
             abs(7 - count(*))::BIGINT
      FROM calibration.preparation_condition
      WHERE preparation_condition_key LIKE 'pilot.round3d.%'
      UNION ALL
      SELECT 'round3d.milk_pair_exactly_one',
             abs(1 - count(*))::BIGINT
      FROM calibration.preparation_condition
      WHERE preparation_condition_key LIKE 'pilot.round3d.%'
        AND coffee_mode_code = 'milk_coffee'
        AND paired_black_condition_id IS NOT NULL
      UNION ALL
      SELECT 'round3d.condition_cells_66', abs(66 - count(*))::BIGINT
      FROM (
        SELECT sample.coffee_lot_id, sample.roast_batch_id,
               sample.preparation_condition_id
        FROM calibration.beverage_sample AS sample
        WHERE sample.beverage_sample_key LIKE 'pilot.round3d.%'
        GROUP BY sample.coffee_lot_id, sample.roast_batch_id,
                 sample.preparation_condition_id
      ) AS cell
      UNION ALL
      SELECT 'round3d.two_replicates_per_cell', count(*)::BIGINT
      FROM (
        SELECT sample.coffee_lot_id, sample.roast_batch_id,
               sample.preparation_condition_id
        FROM calibration.beverage_sample AS sample
        WHERE sample.beverage_sample_key LIKE 'pilot.round3d.%'
        GROUP BY sample.coffee_lot_id, sample.roast_batch_id,
                 sample.preparation_condition_id
        HAVING count(*) <> 2
            OR min(sample.replicate_number) <> 1
            OR max(sample.replicate_number) <> 2
      ) AS invalid_cell
      UNION ALL
      SELECT 'round3d.planned_samples_132_not_observations', count(*)::BIGINT
      FROM calibration.beverage_sample
      WHERE beverage_sample_key LIKE 'pilot.round3d.%'
        AND record_origin_code <> 'planned_real_sample'
      UNION ALL
      SELECT 'round3d.session_slots_192', abs(192 - count(*))::BIGINT
      FROM calibration.pilot_session_slot
      UNION ALL
      SELECT 'round3d.reference_session_slots_72',
             abs(72 - count(*))::BIGINT
      FROM calibration.pilot_session_slot WHERE cohort_code = 'reference'
      UNION ALL
      SELECT 'round3d.ordinary_session_slots_120',
             abs(120 - count(*))::BIGINT
      FROM calibration.pilot_session_slot WHERE cohort_code = 'ordinary_user'
      UNION ALL
      SELECT 'round3d.presentation_slots_1512',
             abs(1512 - count(*))::BIGINT
      FROM calibration.pilot_presentation_slot
      UNION ALL
      SELECT 'round3d.session_burden_matches_presentations', count(*)::BIGINT
      FROM (
        SELECT session.pilot_session_slot_id, session.sample_burden
        FROM calibration.pilot_session_slot AS session
        LEFT JOIN calibration.pilot_presentation_slot AS presentation
          ON presentation.pilot_session_slot_id = session.pilot_session_slot_id
        GROUP BY session.pilot_session_slot_id
        HAVING count(presentation.pilot_presentation_slot_id) <>
               session.sample_burden
      ) AS invalid_session
      UNION ALL
      SELECT 'round3d.reference_presentations_792',
             abs(792 - count(*))::BIGINT
      FROM calibration.pilot_presentation_slot AS presentation
      JOIN calibration.pilot_session_slot AS session
        ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
      WHERE session.cohort_code = 'reference'
      UNION ALL
      SELECT 'round3d.ordinary_presentations_720',
             abs(720 - count(*))::BIGINT
      FROM calibration.pilot_presentation_slot AS presentation
      JOIN calibration.pilot_session_slot AS session
        ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
      WHERE session.cohort_code = 'ordinary_user'
      UNION ALL
      SELECT 'round3d.reference_sample_exposure_exactly_6', count(*)::BIGINT
      FROM (
        SELECT sample.beverage_sample_id
        FROM calibration.beverage_sample AS sample
        LEFT JOIN calibration.pilot_presentation_slot AS presentation
          ON presentation.beverage_sample_id = sample.beverage_sample_id
        LEFT JOIN calibration.pilot_session_slot AS session
          ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
        WHERE sample.beverage_sample_key LIKE 'pilot.round3d.%'
        GROUP BY sample.beverage_sample_id
        HAVING count(presentation.pilot_presentation_slot_id) FILTER (
          WHERE session.cohort_code = 'reference'
        ) <> 6
      ) AS invalid_exposure
      UNION ALL
      SELECT 'round3d.ordinary_sample_exposure_5_or_6', count(*)::BIGINT
      FROM (
        SELECT sample.beverage_sample_id
        FROM calibration.beverage_sample AS sample
        LEFT JOIN calibration.pilot_presentation_slot AS presentation
          ON presentation.beverage_sample_id = sample.beverage_sample_id
        LEFT JOIN calibration.pilot_session_slot AS session
          ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
        WHERE sample.beverage_sample_key LIKE 'pilot.round3d.%'
        GROUP BY sample.beverage_sample_id
        HAVING count(presentation.pilot_presentation_slot_id) FILTER (
          WHERE session.cohort_code = 'ordinary_user'
        ) NOT BETWEEN 5 AND 6
      ) AS invalid_exposure
      UNION ALL
      SELECT 'round3d.question_assignment_slots_3600',
             abs(3600 - count(*))::BIGINT
      FROM calibration.pilot_question_assignment_slot
      UNION ALL
      SELECT 'round3d.question_slots_only_ordinary', count(*)::BIGINT
      FROM calibration.pilot_question_assignment_slot AS assignment
      JOIN calibration.pilot_presentation_slot AS presentation
        ON presentation.pilot_presentation_slot_id =
           assignment.pilot_presentation_slot_id
      JOIN calibration.pilot_session_slot AS session
        ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
      WHERE session.cohort_code <> 'ordinary_user'
      UNION ALL
      SELECT 'round3d.five_question_slots_per_ordinary_presentation',
             count(*)::BIGINT
      FROM (
        SELECT presentation.pilot_presentation_slot_id
        FROM calibration.pilot_presentation_slot AS presentation
        JOIN calibration.pilot_session_slot AS session
          ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
        LEFT JOIN calibration.pilot_question_assignment_slot AS assignment
          ON assignment.pilot_presentation_slot_id =
             presentation.pilot_presentation_slot_id
        WHERE session.cohort_code = 'ordinary_user'
        GROUP BY presentation.pilot_presentation_slot_id
        HAVING count(assignment.pilot_question_assignment_slot_id) <> 5
          OR min(assignment.step_number) <> 1
          OR max(assignment.step_number) <> 5
      ) AS invalid_assignment
      UNION ALL
      SELECT 'round3d.q1_mandatory_later_conditional', count(*)::BIGINT
      FROM calibration.pilot_question_assignment_slot
      WHERE (step_number = 1 AND assignment_status <> 'mandatory')
         OR (step_number > 1 AND assignment_status <> 'conditional')
      UNION ALL
      SELECT 'round3d.dry_run_fixtures_5', abs(5 - count(*))::BIGINT
      FROM calibration.engineering_dry_run_case
      WHERE fixture_label = 'DRY_RUN_FIXTURE' AND mechanics_pass
      UNION ALL
      SELECT 'round3d.dry_run_stop_paths_1_2_4_5',
             abs(4 - count(DISTINCT expected_stop_step))::BIGINT
      FROM calibration.engineering_dry_run_case
      WHERE expected_stop_step IN (1, 2, 4, 5)
      UNION ALL
      SELECT 'round3d.explicit_override_fixture_present',
             abs(1 - count(*))::BIGINT
      FROM calibration.engineering_dry_run_case
      WHERE explicit_override
        AND dry_run_case_key = 'dry_run.round3d.user_override_jasmine'
      UNION ALL
      SELECT 'round3d.no_real_observation_rows',
             (
               (SELECT count(*) FROM calibration.assessor
                WHERE record_origin_code = 'real_observation')
               + (SELECT count(*) FROM calibration.session
                  WHERE record_origin_code = 'real_observation')
               + (SELECT count(*) FROM calibration.presentation
                  WHERE record_origin_code = 'real_observation')
               + (SELECT count(*) FROM calibration.sensory_observation
                  WHERE record_origin_code = 'real_observation')
               + (SELECT count(*) FROM calibration.question_assignment
                  WHERE record_origin_code = 'real_observation')
               + (SELECT count(*) FROM calibration.candidate_reference_judgment
                  WHERE record_origin_code = 'real_observation')
               + (SELECT count(*) FROM calibration.capture_import_row
                  WHERE record_origin_code = 'real_observation')
             )::BIGINT
      UNION ALL
      SELECT 'round3d.study_real_count_zero_and_gates_closed', count(*)::BIGINT
      FROM calibration.study
      WHERE study_key = 'study.context_calibration_v0.minimum'
        AND (empirical_observation_count <> 0
             OR ethics_or_approval_gate
             OR consent_material_ready
             OR public_release_rights_ready)
      UNION ALL
      SELECT 'round3d.empty_capture_batch_validated', count(*)::BIGINT
      FROM calibration.capture_import_batch
      WHERE capture_import_batch_key =
            'capture_import.round3d.empty_template.2026_08_25'
        AND (staged_row_count <> 0 OR real_row_count <> 0
             OR fixture_row_count <> 0 OR NOT pii_scan_pass
             OR governance_gate_pass
             OR promotion_status <> 'validated_empty')
      UNION ALL
      SELECT 'round3d.capture_import_rows_zero', count(*)::BIGINT
      FROM calibration.capture_import_row
      UNION ALL
      SELECT 'round3d.internal_release_metadata_exact', count(*)::BIGINT
      FROM calibration.release_snapshot
      WHERE release_snapshot_key =
            'release.context_calibration_v0.protocol_schema_v0_1_0'
        AND (lifecycle_status_code <> 'internal'
             OR manifest_sha256 <> '062198d21cf56d3ac1f1bf9faea30169ca89efb12cbbabc0190178b4dfb8d063'
             OR checksums_sha256 <> '1ac82525c830148bd54f25236148ea2ba8317ad07d318fe61142e40b63bbf30a'
             OR license_spdx <> 'CC-BY-4.0'
             OR split_snapshot_sha256 <> 'fe76dab2f695a0e7a1d23eb0744c97fb7c832e069cd9b060d26da47c3cebe45a'
             OR real_observation_count <> 0
             OR dry_run_fixture_count <> 5)
      UNION ALL
      SELECT 'round3d.analysis_not_estimable', count(*)::BIGINT
      FROM calibration.v_round3d_analysis_status
      WHERE estimability_status <> 'NOT_ESTIMABLE'
         OR real_observation_count <> 0
         OR dry_run_fixture_count <> 5
         OR analysis_status <> 'PASS_WITH_NOT_ESTIMABLE_OUTPUTS'
         OR NOT fixture_exclusion_pass
         OR deep_learning_model_run
         OR embedding_baseline_run
         OR pgvector_required
      UNION ALL
      SELECT 'round3d.all_analysis_outputs_not_estimable',
             count(*) FILTER (WHERE value <> 'NOT_ESTIMABLE')::BIGINT
             + abs(13 - count(*))::BIGINT
      FROM calibration.v_round3d_analysis_status AS status
      CROSS JOIN LATERAL jsonb_each_text(status.outputs)
      UNION ALL
      SELECT 'round3d.no_model_candidate_outputs', count(*)::BIGINT
      FROM calibration.model_candidate_output
    )
    SELECT checks.check_key, checks.violation_count,
           checks.violation_count = 0 AS passed
    FROM checks
$run_round3d_validation_queries$;

COMMENT ON VIEW calibration.v_round3d_pilot_inventory IS
    'Frozen Round 3D planned-material, randomization, question-slot, fixture, and zero-real-observation inventory.';
COMMENT ON VIEW calibration.v_round3d_analysis_status IS
    'Round 3D zero-data baseline: every empirical output is NOT_ESTIMABLE; no deep, embedding, or pgvector path ran.';

COMMIT;
