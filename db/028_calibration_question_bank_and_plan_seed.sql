\set ON_ERROR_STOP on

-- Deterministic Round 3C governance and bilingual draft question-bank seed.
-- No assessor, presentation, response, or sensory-observation row is seeded.

BEGIN;

CREATE TABLE calibration.study_design_target (
    study_design_target_id BIGINT GENERATED ALWAYS AS IDENTITY,
    study_id BIGINT NOT NULL,
    design_scale_code TEXT NOT NULL,
    coffee_lot_count INTEGER NOT NULL,
    roast_batch_count INTEGER NOT NULL,
    preparation_family_count INTEGER NOT NULL,
    roast_category_count INTEGER NOT NULL,
    condition_cell_count INTEGER NOT NULL,
    beverage_replicates_per_cell INTEGER NOT NULL,
    beverage_sample_count INTEGER NOT NULL,
    reference_assessor_count INTEGER NOT NULL,
    ordinary_user_count INTEGER NOT NULL,
    reference_presentation_count INTEGER NOT NULL,
    ordinary_user_presentation_count INTEGER NOT NULL,
    includes_milk_mode BOOLEAN NOT NULL,
    calibration_power_status TEXT NOT NULL,
    CONSTRAINT study_design_target_pk PRIMARY KEY (study_design_target_id),
    CONSTRAINT study_design_target_study_scale_uq UNIQUE (study_id, design_scale_code),
    CONSTRAINT study_design_target_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT study_design_target_counts_ck CHECK (
        design_scale_code IN ('minimum', 'preferred', 'expanded')
        AND coffee_lot_count > 0 AND roast_batch_count > 0
        AND preparation_family_count BETWEEN 1 AND 8
        AND roast_category_count = 7
        AND condition_cell_count > 0
        AND beverage_replicates_per_cell > 0
        AND beverage_sample_count = condition_cell_count * beverage_replicates_per_cell
        AND reference_assessor_count > 0 AND ordinary_user_count > 0
        AND reference_presentation_count > 0
        AND ordinary_user_presentation_count > 0
        AND calibration_power_status IN (
            'FEASIBILITY_ONLY', 'CALIBRATION_CANDIDATE', 'BENCHMARK_CANDIDATE'
        )
    )
);

INSERT INTO calibration.study (
    study_key, title, design_scale_code, lifecycle_status_code,
    human_participant_ethics_required, institutional_approval_status,
    public_data_consent_required, ethics_or_approval_gate,
    consent_material_ready, public_release_rights_ready,
    empirical_observation_count
)
VALUES (
    'study.context_calibration_v0.minimum',
    'Coffee Sensory Context Calibration Dataset minimum pilot',
    'minimum', 'design', TRUE, 'NOT_OBTAINED', TRUE,
    FALSE, FALSE, FALSE, 0
);

INSERT INTO calibration.protocol_version (
    protocol_version_key, study_id, version_label, repository_path,
    content_sha256, frozen_on, is_frozen
)
SELECT
    'protocol.context_calibration_v0.2026_08_25',
    study.study_id,
    'v0.1.0-design',
    'docs/protocols/COFFEE_SENSORY_CONTEXT_CALIBRATION_PROTOCOL_V0.md',
    '4c759fcae812203c40394d1f510e93c4a83430a3dfb298e832b5ffc49f5924ad',
    DATE '2026-08-25', TRUE
FROM calibration.study AS study
WHERE study.study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.analysis_plan (
    analysis_plan_key, study_id, version_label, repository_path,
    content_sha256, split_method, split_seed, grouping_variable,
    estimability_status, is_frozen
)
SELECT
    'analysis_plan.context_calibration_v0.2026_08_25',
    study.study_id,
    'v0.1.0-preregistered',
    'docs/research/coffee-sensory-kb-v0-round3c/09_STATISTICAL_ANALYSIS_PLAN.md',
    'eff65944d1dabee250827c2d3f9681b6479d60a818184f61a64eb8f1e4f83b10',
    'lot-grouped development/validation/held-out test; not available at minimum scale',
    'coffee-context-calibration-v0-lot-split-20260825',
    'coffee_lot_id', 'NOT_ESTIMABLE', TRUE
FROM calibration.study AS study
WHERE study.study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.study_design_target (
    study_id, design_scale_code, coffee_lot_count, roast_batch_count,
    preparation_family_count, roast_category_count, condition_cell_count,
    beverage_replicates_per_cell, beverage_sample_count,
    reference_assessor_count, ordinary_user_count,
    reference_presentation_count, ordinary_user_presentation_count,
    includes_milk_mode, calibration_power_status
)
SELECT study.study_id, design.design_scale_code, design.coffee_lot_count,
       design.roast_batch_count, design.preparation_family_count,
       7, design.condition_cell_count, design.replicates,
       design.sample_count, design.reference_count, design.ordinary_count,
       design.reference_presentations, design.ordinary_presentations,
       TRUE, design.power_status
FROM calibration.study AS study
CROSS JOIN (VALUES
    ('minimum', 2, 14, 7, 66, 2, 132, 12, 60, 792, 720, 'FEASIBILITY_ONLY'),
    ('preferred', 8, 56, 7, 296, 3, 888, 24, 240, 3552, 2880, 'CALIBRATION_CANDIDATE'),
    ('expanded', 24, 168, 8, 1152, 3, 3456, 40, 800, 13824, 9600, 'BENCHMARK_CANDIDATE')
) AS design(
    design_scale_code, coffee_lot_count, roast_batch_count,
    preparation_family_count, condition_cell_count, replicates,
    sample_count, reference_count, ordinary_count,
    reference_presentations, ordinary_presentations, power_status
)
WHERE study.study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.release_snapshot (
    release_snapshot_key, study_id, protocol_version_id, analysis_plan_id,
    version_label, lifecycle_status_code, real_observation_count,
    dry_run_fixture_count
)
SELECT
    'release.context_calibration_v0.design_contract',
    study.study_id, protocol.protocol_version_id, plan.analysis_plan_id,
    'v0.1.0-design-contract', 'design', 0, 0
FROM calibration.study AS study
JOIN calibration.protocol_version AS protocol ON protocol.study_id = study.study_id
JOIN calibration.analysis_plan AS plan ON plan.study_id = study.study_id
WHERE study.study_key = 'study.context_calibration_v0.minimum';

INSERT INTO calibration.question (
    question_key, logical_question_code, language_tag_code, prompt_text,
    min_selections, max_selections, interaction_position_code,
    lifecycle_status_code
)
VALUES
    ('question.family_direction.en', 'family_direction', 'en', 'Which sensory family is closest?', 1, 1, 'q1_candidate', 'draft'),
    ('question.family_direction.zh_hans', 'family_direction', 'zh-Hans', '哪一类感官方向最接近？', 1, 1, 'q1_candidate', 'draft'),
    ('question.fruit_direction.en', 'fruit_direction', 'en', 'If fruit is present, which direction is closest?', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.fruit_direction.zh_hans', 'fruit_direction', 'zh-Hans', '如果有水果感，哪个方向最接近？', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.sweet_direction.en', 'sweet_direction', 'en', 'Which sweet reference is closest?', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.sweet_direction.zh_hans', 'sweet_direction', 'zh-Hans', '哪一种甜香参照最接近？', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.roast_direction.en', 'roast_direction', 'en', 'Which roast-related direction is closest?', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.roast_direction.zh_hans', 'roast_direction', 'zh-Hans', '哪一种烘焙相关方向最接近？', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.bright_acidity.en', 'bright_acidity', 'en', 'Which bright or acidity direction is closest?', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.bright_acidity.zh_hans', 'bright_acidity', 'zh-Hans', '哪一种明亮或酸感方向最接近？', 1, 1, 'q2_q4_candidate', 'draft'),
    ('question.texture_direction.en', 'texture_direction', 'en', 'If ambiguity remains, which texture is closest?', 1, 1, 'q5_exceptional', 'draft'),
    ('question.texture_direction.zh_hans', 'texture_direction', 'zh-Hans', '如果仍然难以区分，哪一种口感最接近？', 1, 1, 'q5_exceptional', 'draft');

INSERT INTO calibration.question_option (
    question_option_key, question_id, option_code, option_text, ordinal_position
)
SELECT
    'question_option.' || question.logical_question_code || '.' ||
        lower(replace(question.language_tag_code, '-', '_')) || '.' || option.option_code,
    question.question_id, option.option_code,
    CASE question.language_tag_code WHEN 'en' THEN option.text_en ELSE option.text_zh END,
    option.ordinal_position
FROM calibration.question AS question
JOIN (VALUES
    ('family_direction', 'floral_tea', 'Floral / fragrant tea', '花香 / 芳香茶', 1),
    ('family_direction', 'fruit_bright', 'Fruit / bright', '水果 / 明亮', 2),
    ('family_direction', 'cocoa_roast', 'Cocoa / nut / roast', '可可 / 坚果 / 烘烤', 3),
    ('fruit_direction', 'citrus', 'Citrus', '柑橘', 1),
    ('fruit_direction', 'berry', 'Berry', '莓果', 2),
    ('fruit_direction', 'dried_tropical', 'Dried / tropical fruit', '果干 / 热带水果', 3),
    ('sweet_direction', 'caramel', 'Caramel / brown sugar', '焦糖 / 红糖', 1),
    ('sweet_direction', 'honey', 'Honey / floral sweet', '蜂蜜 / 花甜', 2),
    ('sweet_direction', 'vanilla', 'Vanilla / soft sweet', '香草 / 柔和甜香', 3),
    ('roast_direction', 'cocoa_nut', 'Cocoa / nut', '可可 / 坚果', 1),
    ('roast_direction', 'spice', 'Roast spice', '烘焙香料', 2),
    ('roast_direction', 'smoke_char', 'Smoke / char', '烟熏 / 焦炭', 3),
    ('bright_acidity', 'citrus_bright', 'Citrus-bright', '柑橘明亮', 1),
    ('bright_acidity', 'juicy', 'Juicy', '多汁', 2),
    ('bright_acidity', 'soft_round', 'Soft / round', '柔和 / 圆润', 3),
    ('texture_direction', 'light_tea', 'Light / tea-like', '轻盈 / 茶感', 1),
    ('texture_direction', 'juicy_silky', 'Juicy / silky', '多汁 / 丝滑', 2),
    ('texture_direction', 'heavy_drying', 'Heavy / drying', '厚重 / 干涩', 3)
) AS option(
    logical_question_code, option_code, text_en, text_zh, ordinal_position
) ON option.logical_question_code = question.logical_question_code;

UPDATE calibration.question SET lifecycle_status_code = 'active';

INSERT INTO calibration.question_eligibility (
    question_id, preparation_concept_id, roast_category_id,
    minimum_step, maximum_step, eligibility_semantics
)
SELECT
    question.question_id, NULL, NULL,
    CASE question.interaction_position_code WHEN 'q1_candidate' THEN 1
         WHEN 'q2_q4_candidate' THEN 2 ELSE 5 END,
    CASE question.interaction_position_code WHEN 'q1_candidate' THEN 1
         WHEN 'q2_q4_candidate' THEN 4 ELSE 5 END,
    'Draft global eligibility; production context-specific information gain remains unresolved.'
FROM calibration.question AS question;

COMMIT;
