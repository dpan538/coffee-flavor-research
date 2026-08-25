\set ON_ERROR_STOP on
\pset pager off

BEGIN;

CREATE FUNCTION pg_temp.expect_round3c_failure(
    test_key TEXT, statement_text TEXT,
    expected_state TEXT, expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3c_failure$
DECLARE actual_state TEXT; actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Round 3C negative statement unexpectedly succeeded: %', test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                                actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE 'ROUND3C_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
          test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3c_failure$;

INSERT INTO calibration.coffee_lot (
    coffee_lot_key, study_id, public_lot_code
)
SELECT 'negative.round3c.lot_a', study_id, 'NEG-LOT-A'
FROM calibration.study
WHERE study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.coffee_lot (
    coffee_lot_key, study_id, public_lot_code
)
SELECT 'negative.round3c.lot_b', study_id, 'NEG-LOT-B'
FROM calibration.study
WHERE study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.roast_batch (
    roast_batch_key, coffee_lot_id, roast_category_id, batch_code
)
SELECT 'negative.round3c.roast_a_light', lot.coffee_lot_id,
       roast.roast_category_id, 'NEG-A-LIGHT'
FROM calibration.coffee_lot AS lot
CROSS JOIN context.roast_category AS roast
WHERE lot.coffee_lot_key = 'negative.round3c.lot_a'
  AND roast.roast_category_key = 'roast.project_v1.light';

INSERT INTO calibration.preparation_condition (
    preparation_condition_key, study_id, preparation_concept_id,
    condition_code, coffee_mode_code, recipe
)
SELECT 'negative.round3c.filter', study.study_id,
       prep.preparation_concept_id, 'NEG-FILTER', 'black_coffee',
       '{"dose_g":15,"water_g":250}'::JSONB
FROM calibration.study AS study
CROSS JOIN context.preparation_concept AS prep
WHERE study.study_key = 'study.context_calibration_v0.minimum'
  AND prep.preparation_concept_key = 'preparation.family.filter_percolation';

INSERT INTO calibration.beverage_sample (
    beverage_sample_key, study_id, protocol_version_id, coffee_lot_id,
    roast_batch_id, preparation_condition_id, replicate_number,
    record_origin_code
)
SELECT 'negative.round3c.sample_valid', study.study_id,
       protocol.protocol_version_id, lot.coffee_lot_id,
       roast.roast_batch_id, prep.preparation_condition_id, 1,
       'DRY_RUN_FIXTURE'
FROM calibration.study AS study
JOIN calibration.protocol_version AS protocol ON protocol.study_id = study.study_id
JOIN calibration.coffee_lot AS lot ON lot.study_id = study.study_id
JOIN calibration.roast_batch AS roast ON roast.coffee_lot_id = lot.coffee_lot_id
JOIN calibration.preparation_condition AS prep ON prep.study_id = study.study_id
WHERE lot.coffee_lot_key = 'negative.round3c.lot_a'
  AND prep.preparation_condition_key = 'negative.round3c.filter';

INSERT INTO calibration.assessor (
    assessor_key, study_id, cohort_code, pseudonymous_code,
    language_tag_code, expertise_band, record_origin_code
)
SELECT 'negative.round3c.assessor', study_id, 'ordinary_user',
       'NEG_USER_01', 'en', 'ordinary', 'DRY_RUN_FIXTURE'
FROM calibration.study
WHERE study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.session (
    session_key, study_id, assessor_id, protocol_version_id,
    session_number, record_origin_code
)
SELECT 'negative.round3c.session', study.study_id, assessor.assessor_id,
       protocol.protocol_version_id, 1, 'DRY_RUN_FIXTURE'
FROM calibration.study AS study
JOIN calibration.assessor AS assessor ON assessor.study_id = study.study_id
JOIN calibration.protocol_version AS protocol ON protocol.study_id = study.study_id
WHERE assessor.assessor_key = 'negative.round3c.assessor';

INSERT INTO calibration.randomization_schedule (
    randomization_schedule_key, study_id, algorithm, random_seed,
    input_manifest_sha256, output_sha256
)
SELECT 'negative.round3c.schedule', study_id, 'negative fixture', 'seed',
       repeat('a', 64), repeat('b', 64)
FROM calibration.study
WHERE study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.presentation (
    presentation_key, session_id, beverage_sample_id,
    randomization_schedule_id, sequence_position, blinded_code,
    record_origin_code
)
SELECT 'negative.round3c.presentation', session.session_id,
       sample.beverage_sample_id, schedule.randomization_schedule_id,
       1, '731', 'DRY_RUN_FIXTURE'
FROM calibration.session AS session
CROSS JOIN calibration.beverage_sample AS sample
CROSS JOIN calibration.randomization_schedule AS schedule
WHERE session.session_key = 'negative.round3c.session'
  AND sample.beverage_sample_key = 'negative.round3c.sample_valid'
  AND schedule.randomization_schedule_key = 'negative.round3c.schedule';

SELECT pg_temp.expect_round3c_failure(
  'duplicate_sample_identity',
  $$INSERT INTO calibration.beverage_sample (
      beverage_sample_key, study_id, protocol_version_id, coffee_lot_id,
      roast_batch_id, preparation_condition_id, replicate_number, record_origin_code
    ) SELECT 'negative.round3c.sample_duplicate', study_id, protocol_version_id,
             coffee_lot_id, roast_batch_id, preparation_condition_id,
             replicate_number, 'DRY_RUN_FIXTURE'
      FROM calibration.beverage_sample
      WHERE beverage_sample_key = 'negative.round3c.sample_valid'$$,
  '23505', 'beverage_sample_identity_uq'
);

SELECT pg_temp.expect_round3c_failure(
  'invalid_c0_family',
  $$INSERT INTO calibration.preparation_condition (
      preparation_condition_key, study_id, preparation_concept_id,
      condition_code, coffee_mode_code, recipe
    ) SELECT 'negative.round3c.invalid_c0', study.study_id,
             prep.preparation_concept_id, 'INVALID-C0', 'black_coffee',
             '{"recipe":"fixture"}'::JSONB
      FROM calibration.study AS study
      CROSS JOIN context.preparation_concept AS prep
      WHERE study.study_key = 'study.context_calibration_v0.minimum'
        AND NOT prep.c0_top_level LIMIT 1$$,
  '23514', 'preparation_condition_current_c0_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'invalid_c1_category',
  $$INSERT INTO calibration.roast_batch (
      roast_batch_key, coffee_lot_id, roast_category_id, batch_code
    ) SELECT 'negative.round3c.invalid_c1', lot.coffee_lot_id,
             roast.roast_category_id, 'INVALID-C1'
      FROM calibration.coffee_lot AS lot
      CROSS JOIN context.roast_category AS roast
      WHERE lot.coffee_lot_key = 'negative.round3c.lot_a'
        AND roast.roast_category_key = 'roast.project.medium'$$,
  '23514', 'roast_batch_current_c1_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'remove_required_seven_level_distinction',
  $$DELETE FROM context.roast_category
    WHERE roast_category_key = 'roast.project_v1.medium_light'$$,
  '23514', 'round3c_current_c1_category_frozen_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'participant_identifier_leakage',
  $$INSERT INTO calibration.assessor (
      assessor_key, study_id, cohort_code, pseudonymous_code,
      language_tag_code, expertise_band, approved_public_metadata
    ) SELECT 'negative.round3c.pii', study_id, 'ordinary_user',
             'NEG_PII_01', 'en', 'ordinary', '{"email":"person@example.org"}'::JSONB
      FROM calibration.study
      WHERE study_key = 'study.context_calibration_v0.minimum'$$,
  '23514', 'assessor_text_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'question_invalid_option_count',
  $$INSERT INTO calibration.question (
      question_key, logical_question_code, language_tag_code, prompt_text,
      min_selections, max_selections, interaction_position_code,
      lifecycle_status_code
    ) VALUES ('negative.round3c.no_options', 'negative_no_options', 'en',
              'Invalid fixture?', 1, 1, 'q1_candidate', 'active')$$,
  '23514', 'question_option_count_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'missing_protocol_version',
  $$INSERT INTO calibration.beverage_sample (
      beverage_sample_key, study_id, protocol_version_id, coffee_lot_id,
      roast_batch_id, preparation_condition_id, replicate_number, record_origin_code
    ) SELECT 'negative.round3c.missing_protocol', study_id, -1,
             coffee_lot_id, roast_batch_id, preparation_condition_id, 2,
             'DRY_RUN_FIXTURE'
      FROM calibration.beverage_sample
      WHERE beverage_sample_key = 'negative.round3c.sample_valid'$$,
  '23514', 'beverage_sample_linkage_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'sample_linkage_mismatch',
  $$INSERT INTO calibration.beverage_sample (
      beverage_sample_key, study_id, protocol_version_id, coffee_lot_id,
      roast_batch_id, preparation_condition_id, replicate_number, record_origin_code
    ) SELECT 'negative.round3c.bad_link', sample.study_id,
             sample.protocol_version_id, lot_b.coffee_lot_id,
             sample.roast_batch_id, sample.preparation_condition_id, 2,
             'DRY_RUN_FIXTURE'
      FROM calibration.beverage_sample AS sample
      CROSS JOIN calibration.coffee_lot AS lot_b
      WHERE sample.beverage_sample_key = 'negative.round3c.sample_valid'
        AND lot_b.coffee_lot_key = 'negative.round3c.lot_b'$$,
  '23514', 'beverage_sample_linkage_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'duplicate_randomization_position',
  $$INSERT INTO calibration.presentation (
      presentation_key, session_id, beverage_sample_id,
      randomization_schedule_id, sequence_position, blinded_code,
      record_origin_code
    ) SELECT 'negative.round3c.presentation_duplicate', session_id,
             beverage_sample_id, randomization_schedule_id, sequence_position,
             '732', 'DRY_RUN_FIXTURE'
      FROM calibration.presentation
      WHERE presentation_key = 'negative.round3c.presentation'$$,
  '23505', 'presentation_session_position_uq'
);

SELECT pg_temp.expect_round3c_failure(
  'derived_consensus_as_raw_observation',
  $$INSERT INTO calibration.sensory_observation (
      sensory_observation_key, presentation_id, observation_role_code,
      record_origin_code
    ) SELECT 'negative.round3c.consensus', presentation_id,
             'derived_consensus', 'DRY_RUN_FIXTURE'
      FROM calibration.presentation
      WHERE presentation_key = 'negative.round3c.presentation'$$,
  '23514', 'sensory_observation_role_ck'
);

INSERT INTO calibration.analysis_run (
    analysis_run_key, analysis_plan_id, release_snapshot_id,
    code_commit_sha, input_snapshot_sha256, estimability_status,
    result_metadata
)
SELECT 'negative.round3c.analysis_run', plan.analysis_plan_id,
       release.release_snapshot_id, repeat('e', 40), repeat('f', 64),
       'NOT_ESTIMABLE', '{"reason":"negative fixture"}'::JSONB
FROM calibration.analysis_plan AS plan
JOIN calibration.release_snapshot AS release
  ON release.analysis_plan_id = plan.analysis_plan_id
WHERE plan.analysis_plan_key = 'analysis_plan.context_calibration_v0.2026_08_25';

SELECT pg_temp.expect_round3c_failure(
  'model_output_as_canonical_knowledge',
  $$INSERT INTO calibration.model_candidate_output (
      analysis_run_id, presentation_id, concept_id, candidate_tier_code,
      rank_position, output_role_code
    ) SELECT run.analysis_run_id, presentation.presentation_id,
             concept.concept_id, 'primary', 1, 'canonical_sensory_knowledge'
      FROM calibration.analysis_run AS run
      CROSS JOIN calibration.presentation AS presentation
      CROSS JOIN kb.concept AS concept
      WHERE run.analysis_run_key = 'negative.round3c.analysis_run'
        AND presentation.presentation_key = 'negative.round3c.presentation'
        AND concept.concept_type_code = 'sensory_attribute'
      ORDER BY concept.concept_id LIMIT 1$$,
  '23514', 'model_candidate_output_role_ck'
);

SELECT pg_temp.expect_round3c_failure(
  'held_out_split_leakage',
  $$INSERT INTO calibration.grouped_split (
      analysis_plan_id, coffee_lot_id, split_code, snapshot_sha256
    ) SELECT plan.analysis_plan_id, lot.coffee_lot_id, split.split_code,
             repeat(split.hash_character, 64)
      FROM calibration.analysis_plan AS plan
      CROSS JOIN calibration.coffee_lot AS lot
      CROSS JOIN (VALUES ('development', 'c'), ('held_out_test', 'd'))
        AS split(split_code, hash_character)
      WHERE plan.analysis_plan_key = 'analysis_plan.context_calibration_v0.2026_08_25'
        AND lot.coffee_lot_key = 'negative.round3c.lot_a'$$,
  '23505', 'grouped_split_lot_uq'
);

SELECT pg_temp.expect_round3c_failure(
  'release_without_manifest_checksum_license',
  $$UPDATE calibration.release_snapshot SET lifecycle_status_code = 'public'
    WHERE release_snapshot_key = 'release.context_calibration_v0.design_contract'$$,
  '23514', 'release_snapshot_public_metadata_ck'
);

-- Valid assignment first, then reject an ineligible Q1 at step two.
INSERT INTO calibration.question_assignment (
    question_assignment_key, presentation_id, question_id, step_number,
    policy_code, eligibility_snapshot, record_origin_code
)
SELECT 'negative.round3c.assignment_q1', presentation.presentation_id,
       question.question_id, 1, 'context_adaptive_q1',
       '{"eligible":true}'::JSONB, 'DRY_RUN_FIXTURE'
FROM calibration.presentation AS presentation
CROSS JOIN calibration.question AS question
WHERE presentation.presentation_key = 'negative.round3c.presentation'
  AND question.question_key = 'question.family_direction.en';

SELECT pg_temp.expect_round3c_failure(
  'response_to_ineligible_question',
  $$INSERT INTO calibration.question_assignment (
      question_assignment_key, presentation_id, question_id, step_number,
      policy_code, eligibility_snapshot, record_origin_code
    ) SELECT 'negative.round3c.assignment_ineligible', presentation.presentation_id,
             question.question_id, 2, 'information_gain',
             '{"eligible":false}'::JSONB, 'DRY_RUN_FIXTURE'
      FROM calibration.presentation AS presentation
      CROSS JOIN calibration.question AS question
      WHERE presentation.presentation_key = 'negative.round3c.presentation'
        AND question.question_key = 'question.family_direction.zh_hans'$$,
  '23514', 'question_assignment_eligible_ck'
);

INSERT INTO calibration.question_response (
    question_assignment_id, response_status_code
)
SELECT question_assignment_id, 'answered'
FROM calibration.question_assignment
WHERE question_assignment_key = 'negative.round3c.assignment_q1';

INSERT INTO calibration.question_response_selection (
    question_response_id, question_option_id, selection_order
)
SELECT response.question_response_id, option.question_option_id, 1
FROM calibration.question_response AS response
JOIN calibration.question_assignment AS assignment
  ON assignment.question_assignment_id = response.question_assignment_id
JOIN calibration.question_option AS option ON option.question_id = assignment.question_id
WHERE assignment.question_assignment_key = 'negative.round3c.assignment_q1'
ORDER BY option.ordinal_position LIMIT 1;

SELECT pg_temp.expect_round3c_failure(
  'answer_count_exceeds_cardinality',
  $$INSERT INTO calibration.question_response_selection (
      question_response_id, question_option_id, selection_order
    ) SELECT response.question_response_id, option.question_option_id, 2
      FROM calibration.question_response AS response
      JOIN calibration.question_assignment AS assignment
        ON assignment.question_assignment_id = response.question_assignment_id
      JOIN calibration.question_option AS option ON option.question_id = assignment.question_id
      WHERE assignment.question_assignment_key = 'negative.round3c.assignment_q1'
      ORDER BY option.ordinal_position OFFSET 1 LIMIT 1$$,
  '23514', 'question_response_cardinality_ck'
);

ROLLBACK;

\echo ROUND3C_NEGATIVE_TEST_PASS=true
