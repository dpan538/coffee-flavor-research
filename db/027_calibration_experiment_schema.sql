\set ON_ERROR_STOP on

BEGIN;

CREATE TABLE calibration.coffee_lot (
    coffee_lot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    coffee_lot_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    public_lot_code TEXT NOT NULL,
    material_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT coffee_lot_pk PRIMARY KEY (coffee_lot_id),
    CONSTRAINT coffee_lot_key_uq UNIQUE (coffee_lot_key),
    CONSTRAINT coffee_lot_study_code_uq UNIQUE (study_id, public_lot_code),
    CONSTRAINT coffee_lot_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT coffee_lot_text_ck CHECK (
        coffee_lot_key = lower(btrim(coffee_lot_key)) AND coffee_lot_key <> ''
        AND public_lot_code = btrim(public_lot_code) AND public_lot_code <> ''
        AND jsonb_typeof(material_metadata) = 'object'
    )
);

CREATE TABLE calibration.roast_batch (
    roast_batch_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_batch_key TEXT NOT NULL,
    coffee_lot_id BIGINT NOT NULL,
    roast_category_id BIGINT NOT NULL,
    batch_code TEXT NOT NULL,
    roast_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT roast_batch_pk PRIMARY KEY (roast_batch_id),
    CONSTRAINT roast_batch_key_uq UNIQUE (roast_batch_key),
    CONSTRAINT roast_batch_lot_category_uq UNIQUE (coffee_lot_id, roast_category_id),
    CONSTRAINT roast_batch_lot_code_uq UNIQUE (coffee_lot_id, batch_code),
    CONSTRAINT roast_batch_lot_fk FOREIGN KEY (coffee_lot_id)
        REFERENCES calibration.coffee_lot (coffee_lot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_batch_category_fk FOREIGN KEY (roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT roast_batch_text_ck CHECK (
        roast_batch_key = lower(btrim(roast_batch_key)) AND roast_batch_key <> ''
        AND batch_code = btrim(batch_code) AND batch_code <> ''
        AND jsonb_typeof(roast_metadata) = 'object'
    )
);

CREATE FUNCTION calibration.enforce_current_roast_category()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_current_roast_category$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM context.v_current_user_roast AS roast
        WHERE roast.roast_category_key = (
            SELECT category.roast_category_key
            FROM context.roast_category AS category
            WHERE category.roast_category_id = NEW.roast_category_id
        )
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'roast_batch_current_c1_ck',
          MESSAGE = 'roast_batch_current_c1_ck: roast batch must use a current seven-level C1 category';
    END IF;
    RETURN NEW;
END;
$enforce_current_roast_category$;

CREATE TRIGGER roast_batch_current_c1_biu
BEFORE INSERT OR UPDATE ON calibration.roast_batch
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_current_roast_category();

CREATE FUNCTION calibration.protect_current_c1_categories()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_current_c1_categories$
BEGIN
    IF EXISTS (
        SELECT 1 FROM context.roast_scheme AS scheme
        WHERE scheme.roast_scheme_id = OLD.roast_scheme_id
          AND scheme.is_project_normalized_target
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'round3c_current_c1_category_frozen_ck',
          MESSAGE = 'round3c_current_c1_category_frozen_ck: the current seven-level C1 distinctions are immutable';
    END IF;
    RETURN OLD;
END;
$protect_current_c1_categories$;

CREATE TRIGGER roast_category_round3c_current_frozen_bud
BEFORE UPDATE OR DELETE ON context.roast_category
FOR EACH ROW EXECUTE FUNCTION calibration.protect_current_c1_categories();

CREATE TABLE calibration.preparation_condition (
    preparation_condition_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_condition_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    preparation_concept_id BIGINT NOT NULL,
    condition_code TEXT NOT NULL,
    coffee_mode_code TEXT NOT NULL,
    paired_black_condition_id BIGINT,
    recipe JSONB NOT NULL,
    CONSTRAINT preparation_condition_pk PRIMARY KEY (preparation_condition_id),
    CONSTRAINT preparation_condition_key_uq UNIQUE (preparation_condition_key),
    CONSTRAINT preparation_condition_study_code_uq UNIQUE (study_id, condition_code),
    CONSTRAINT preparation_condition_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_condition_c0_fk FOREIGN KEY (preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_condition_pair_fk FOREIGN KEY (paired_black_condition_id)
        REFERENCES calibration.preparation_condition (preparation_condition_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_condition_text_ck CHECK (
        preparation_condition_key = lower(btrim(preparation_condition_key))
        AND preparation_condition_key <> ''
        AND condition_code = btrim(condition_code) AND condition_code <> ''
        AND coffee_mode_code IN ('black_coffee', 'milk_coffee')
        AND jsonb_typeof(recipe) = 'object' AND recipe <> '{}'::JSONB
        AND (coffee_mode_code = 'milk_coffee') = (paired_black_condition_id IS NOT NULL)
    )
);

CREATE FUNCTION calibration.enforce_current_preparation_family()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_current_preparation_family$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM context.v_current_user_preparation AS prep
        WHERE prep.preparation_concept_key = (
            SELECT concept.preparation_concept_key
            FROM context.preparation_concept AS concept
            WHERE concept.preparation_concept_id = NEW.preparation_concept_id
        )
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'preparation_condition_current_c0_ck',
          MESSAGE = 'preparation_condition_current_c0_ck: condition must use a current C0 family';
    END IF;
    RETURN NEW;
END;
$enforce_current_preparation_family$;

CREATE TRIGGER preparation_condition_current_c0_biu
BEFORE INSERT OR UPDATE ON calibration.preparation_condition
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_current_preparation_family();

CREATE TABLE calibration.beverage_sample (
    beverage_sample_id BIGINT GENERATED ALWAYS AS IDENTITY,
    beverage_sample_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    protocol_version_id BIGINT NOT NULL,
    coffee_lot_id BIGINT NOT NULL,
    roast_batch_id BIGINT NOT NULL,
    preparation_condition_id BIGINT NOT NULL,
    replicate_number SMALLINT NOT NULL,
    record_origin_code TEXT NOT NULL DEFAULT 'planned_real_sample',
    preparation_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT beverage_sample_pk PRIMARY KEY (beverage_sample_id),
    CONSTRAINT beverage_sample_key_uq UNIQUE (beverage_sample_key),
    CONSTRAINT beverage_sample_identity_uq UNIQUE (
        study_id, protocol_version_id, coffee_lot_id, roast_batch_id,
        preparation_condition_id, replicate_number
    ),
    CONSTRAINT beverage_sample_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_sample_protocol_fk FOREIGN KEY (protocol_version_id)
        REFERENCES calibration.protocol_version (protocol_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_sample_lot_fk FOREIGN KEY (coffee_lot_id)
        REFERENCES calibration.coffee_lot (coffee_lot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_sample_roast_fk FOREIGN KEY (roast_batch_id)
        REFERENCES calibration.roast_batch (roast_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_sample_preparation_fk FOREIGN KEY (preparation_condition_id)
        REFERENCES calibration.preparation_condition (preparation_condition_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT beverage_sample_text_ck CHECK (
        beverage_sample_key = lower(btrim(beverage_sample_key))
        AND beverage_sample_key <> ''
        AND replicate_number BETWEEN 1 AND 99
        AND record_origin_code IN ('planned_real_sample', 'real_observation', 'DRY_RUN_FIXTURE')
        AND jsonb_typeof(preparation_metadata) = 'object'
    )
);

CREATE FUNCTION calibration.enforce_beverage_sample_linkage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_beverage_sample_linkage$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM calibration.roast_batch AS roast
        JOIN calibration.coffee_lot AS lot
          ON lot.coffee_lot_id = roast.coffee_lot_id
        JOIN calibration.preparation_condition AS prep
          ON prep.preparation_condition_id = NEW.preparation_condition_id
        JOIN calibration.protocol_version AS protocol
          ON protocol.protocol_version_id = NEW.protocol_version_id
        WHERE roast.roast_batch_id = NEW.roast_batch_id
          AND roast.coffee_lot_id = NEW.coffee_lot_id
          AND lot.study_id = NEW.study_id
          AND prep.study_id = NEW.study_id
          AND protocol.study_id = NEW.study_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'beverage_sample_linkage_ck',
          MESSAGE = 'beverage_sample_linkage_ck: sample study, protocol, lot, roast batch, and preparation must agree';
    END IF;
    RETURN NEW;
END;
$enforce_beverage_sample_linkage$;

CREATE TRIGGER beverage_sample_linkage_biu
BEFORE INSERT OR UPDATE ON calibration.beverage_sample
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_beverage_sample_linkage();

CREATE TABLE calibration.assessor (
    assessor_id BIGINT GENERATED ALWAYS AS IDENTITY,
    assessor_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    cohort_code TEXT NOT NULL,
    pseudonymous_code TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    expertise_band TEXT NOT NULL,
    approved_public_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    record_origin_code TEXT NOT NULL DEFAULT 'real_observation',
    CONSTRAINT assessor_pk PRIMARY KEY (assessor_id),
    CONSTRAINT assessor_key_uq UNIQUE (assessor_key),
    CONSTRAINT assessor_study_pseudonym_uq UNIQUE (study_id, pseudonymous_code),
    CONSTRAINT assessor_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT assessor_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT assessor_text_ck CHECK (
        assessor_key = lower(btrim(assessor_key)) AND assessor_key <> ''
        AND pseudonymous_code ~ '^[A-Z0-9_-]{4,32}$'
        AND cohort_code IN ('reference', 'ordinary_user')
        AND expertise_band IN ('trained', 'experienced', 'ordinary', 'not_reported')
        AND record_origin_code IN ('real_observation', 'DRY_RUN_FIXTURE')
        AND jsonb_typeof(approved_public_metadata) = 'object'
        AND calibration.reject_direct_identifiers(approved_public_metadata)
    )
);

CREATE TABLE calibration.session (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY,
    session_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    assessor_id BIGINT NOT NULL,
    protocol_version_id BIGINT NOT NULL,
    session_number SMALLINT NOT NULL,
    record_origin_code TEXT NOT NULL DEFAULT 'real_observation',
    CONSTRAINT session_pk PRIMARY KEY (session_id),
    CONSTRAINT session_key_uq UNIQUE (session_key),
    CONSTRAINT session_assessor_number_uq UNIQUE (assessor_id, session_number),
    CONSTRAINT session_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT session_assessor_fk FOREIGN KEY (assessor_id)
        REFERENCES calibration.assessor (assessor_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT session_protocol_fk FOREIGN KEY (protocol_version_id)
        REFERENCES calibration.protocol_version (protocol_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT session_text_ck CHECK (
        session_key = lower(btrim(session_key)) AND session_key <> ''
        AND session_number > 0
        AND record_origin_code IN ('real_observation', 'DRY_RUN_FIXTURE')
    )
);

CREATE TABLE calibration.randomization_schedule (
    randomization_schedule_id BIGINT GENERATED ALWAYS AS IDENTITY,
    randomization_schedule_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    algorithm TEXT NOT NULL,
    random_seed TEXT NOT NULL,
    input_manifest_sha256 TEXT NOT NULL,
    output_sha256 TEXT NOT NULL,
    CONSTRAINT randomization_schedule_pk PRIMARY KEY (randomization_schedule_id),
    CONSTRAINT randomization_schedule_key_uq UNIQUE (randomization_schedule_key),
    CONSTRAINT randomization_schedule_output_uq UNIQUE (study_id, output_sha256),
    CONSTRAINT randomization_schedule_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT randomization_schedule_text_ck CHECK (
        randomization_schedule_key = lower(btrim(randomization_schedule_key))
        AND randomization_schedule_key <> ''
        AND algorithm = btrim(algorithm) AND algorithm <> ''
        AND random_seed = btrim(random_seed) AND random_seed <> ''
        AND input_manifest_sha256 ~ '^[0-9a-f]{64}$'
        AND output_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE calibration.presentation (
    presentation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    presentation_key TEXT NOT NULL,
    session_id BIGINT NOT NULL,
    beverage_sample_id BIGINT NOT NULL,
    randomization_schedule_id BIGINT NOT NULL,
    sequence_position SMALLINT NOT NULL,
    blinded_code TEXT NOT NULL,
    record_origin_code TEXT NOT NULL DEFAULT 'real_observation',
    CONSTRAINT presentation_pk PRIMARY KEY (presentation_id),
    CONSTRAINT presentation_key_uq UNIQUE (presentation_key),
    CONSTRAINT presentation_session_position_uq UNIQUE (session_id, sequence_position),
    CONSTRAINT presentation_session_sample_uq UNIQUE (session_id, beverage_sample_id),
    CONSTRAINT presentation_session_fk FOREIGN KEY (session_id)
        REFERENCES calibration.session (session_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT presentation_sample_fk FOREIGN KEY (beverage_sample_id)
        REFERENCES calibration.beverage_sample (beverage_sample_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT presentation_schedule_fk FOREIGN KEY (randomization_schedule_id)
        REFERENCES calibration.randomization_schedule (randomization_schedule_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT presentation_text_ck CHECK (
        presentation_key = lower(btrim(presentation_key)) AND presentation_key <> ''
        AND sequence_position > 0
        AND blinded_code ~ '^[0-9]{3,6}$'
        AND record_origin_code IN ('real_observation', 'DRY_RUN_FIXTURE')
    )
);

CREATE TABLE calibration.sensory_observation (
    sensory_observation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    sensory_observation_key TEXT NOT NULL,
    presentation_id BIGINT NOT NULL,
    observation_role_code TEXT NOT NULL,
    confidence_value NUMERIC(4,3),
    record_origin_code TEXT NOT NULL DEFAULT 'real_observation',
    CONSTRAINT sensory_observation_pk PRIMARY KEY (sensory_observation_id),
    CONSTRAINT sensory_observation_key_uq UNIQUE (sensory_observation_key),
    CONSTRAINT sensory_observation_presentation_uq UNIQUE (presentation_id),
    CONSTRAINT sensory_observation_presentation_fk FOREIGN KEY (presentation_id)
        REFERENCES calibration.presentation (presentation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sensory_observation_role_ck CHECK (
        observation_role_code = 'raw_observation'
        AND (confidence_value IS NULL OR confidence_value BETWEEN 0 AND 1)
        AND record_origin_code IN ('real_observation', 'DRY_RUN_FIXTURE')
    )
);

CREATE TABLE calibration.descriptor_response (
    descriptor_response_id BIGINT GENERATED ALWAYS AS IDENTITY,
    sensory_observation_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    response_code TEXT NOT NULL,
    intensity_value NUMERIC(4,2),
    CONSTRAINT descriptor_response_pk PRIMARY KEY (descriptor_response_id),
    CONSTRAINT descriptor_response_fact_uq UNIQUE (sensory_observation_id, concept_id),
    CONSTRAINT descriptor_response_observation_fk FOREIGN KEY (sensory_observation_id)
        REFERENCES calibration.sensory_observation (sensory_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_response_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_response_value_ck CHECK (
        response_code IN ('present', 'absent', 'uncertain')
        AND (intensity_value IS NULL OR intensity_value BETWEEN 0 AND 5)
    )
);

CREATE TABLE calibration.dimension_response (
    dimension_response_id BIGINT GENERATED ALWAYS AS IDENTITY,
    sensory_observation_id BIGINT NOT NULL,
    sensory_dimension_id BIGINT NOT NULL,
    value NUMERIC(4,2) NOT NULL,
    CONSTRAINT dimension_response_pk PRIMARY KEY (dimension_response_id),
    CONSTRAINT dimension_response_fact_uq UNIQUE (sensory_observation_id, sensory_dimension_id),
    CONSTRAINT dimension_response_observation_fk FOREIGN KEY (sensory_observation_id)
        REFERENCES calibration.sensory_observation (sensory_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT dimension_response_dimension_fk FOREIGN KEY (sensory_dimension_id)
        REFERENCES kb.sensory_dimension (sensory_dimension_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT dimension_response_value_ck CHECK (value BETWEEN 0 AND 5)
);

CREATE TABLE calibration.question (
    question_id BIGINT GENERATED ALWAYS AS IDENTITY,
    question_key TEXT NOT NULL,
    logical_question_code TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    min_selections SMALLINT NOT NULL,
    max_selections SMALLINT NOT NULL,
    interaction_position_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT question_pk PRIMARY KEY (question_id),
    CONSTRAINT question_key_uq UNIQUE (question_key),
    CONSTRAINT question_language_uq UNIQUE (logical_question_code, language_tag_code),
    CONSTRAINT question_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_text_ck CHECK (
        question_key = lower(btrim(question_key)) AND question_key <> ''
        AND logical_question_code = lower(btrim(logical_question_code))
        AND logical_question_code <> ''
        AND prompt_text = btrim(prompt_text) AND prompt_text <> ''
        AND min_selections BETWEEN 1 AND 5
        AND max_selections BETWEEN min_selections AND 5
        AND interaction_position_code IN ('q1_candidate', 'q2_q4_candidate', 'q5_exceptional')
        AND lifecycle_status_code IN ('draft', 'active', 'retired')
    )
);

CREATE TABLE calibration.question_option (
    question_option_id BIGINT GENERATED ALWAYS AS IDENTITY,
    question_option_key TEXT NOT NULL,
    question_id BIGINT NOT NULL,
    option_code TEXT NOT NULL,
    option_text TEXT NOT NULL,
    ordinal_position SMALLINT NOT NULL,
    CONSTRAINT question_option_pk PRIMARY KEY (question_option_id),
    CONSTRAINT question_option_key_uq UNIQUE (question_option_key),
    CONSTRAINT question_option_code_uq UNIQUE (question_id, option_code),
    CONSTRAINT question_option_position_uq UNIQUE (question_id, ordinal_position),
    CONSTRAINT question_option_question_fk FOREIGN KEY (question_id)
        REFERENCES calibration.question (question_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_option_text_ck CHECK (
        question_option_key = lower(btrim(question_option_key))
        AND question_option_key <> ''
        AND option_code = lower(btrim(option_code)) AND option_code <> ''
        AND option_text = btrim(option_text) AND option_text <> ''
        AND ordinal_position BETWEEN 1 AND 8
    )
);

CREATE FUNCTION calibration.enforce_question_option_count()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_question_option_count$
DECLARE option_count INTEGER;
BEGIN
    SELECT count(*) INTO option_count
    FROM calibration.question_option AS option
    WHERE option.question_id = NEW.question_id;
    IF option_count NOT BETWEEN 2 AND 8 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'question_option_count_ck',
          MESSAGE = 'question_option_count_ck: an active question requires between two and eight options';
    END IF;
    RETURN NEW;
END;
$enforce_question_option_count$;

CREATE CONSTRAINT TRIGGER question_option_count_after_question
AFTER INSERT OR UPDATE OF lifecycle_status_code ON calibration.question
DEFERRABLE INITIALLY IMMEDIATE
FOR EACH ROW WHEN (NEW.lifecycle_status_code = 'active')
EXECUTE FUNCTION calibration.enforce_question_option_count();

CREATE TABLE calibration.question_eligibility (
    question_eligibility_id BIGINT GENERATED ALWAYS AS IDENTITY,
    question_id BIGINT NOT NULL,
    preparation_concept_id BIGINT,
    roast_category_id BIGINT,
    minimum_step SMALLINT NOT NULL,
    maximum_step SMALLINT NOT NULL,
    eligibility_semantics TEXT NOT NULL,
    CONSTRAINT question_eligibility_pk PRIMARY KEY (question_eligibility_id),
    CONSTRAINT question_eligibility_fact_uq UNIQUE NULLS NOT DISTINCT (
        question_id, preparation_concept_id, roast_category_id,
        minimum_step, maximum_step
    ),
    CONSTRAINT question_eligibility_question_fk FOREIGN KEY (question_id)
        REFERENCES calibration.question (question_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_eligibility_preparation_fk FOREIGN KEY (preparation_concept_id)
        REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_eligibility_roast_fk FOREIGN KEY (roast_category_id)
        REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_eligibility_step_ck CHECK (
        minimum_step BETWEEN 1 AND 5
        AND maximum_step BETWEEN minimum_step AND 5
        AND eligibility_semantics = btrim(eligibility_semantics)
        AND eligibility_semantics <> ''
    )
);

CREATE TABLE calibration.question_assignment (
    question_assignment_id BIGINT GENERATED ALWAYS AS IDENTITY,
    question_assignment_key TEXT NOT NULL,
    presentation_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    step_number SMALLINT NOT NULL,
    policy_code TEXT NOT NULL,
    eligibility_snapshot JSONB NOT NULL,
    record_origin_code TEXT NOT NULL DEFAULT 'real_observation',
    CONSTRAINT question_assignment_pk PRIMARY KEY (question_assignment_id),
    CONSTRAINT question_assignment_key_uq UNIQUE (question_assignment_key),
    CONSTRAINT question_assignment_step_uq UNIQUE (presentation_id, step_number),
    CONSTRAINT question_assignment_question_uq UNIQUE (presentation_id, question_id),
    CONSTRAINT question_assignment_presentation_fk FOREIGN KEY (presentation_id)
        REFERENCES calibration.presentation (presentation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_assignment_question_fk FOREIGN KEY (question_id)
        REFERENCES calibration.question (question_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_assignment_text_ck CHECK (
        question_assignment_key = lower(btrim(question_assignment_key))
        AND question_assignment_key <> ''
        AND step_number BETWEEN 1 AND 5
        AND policy_code IN ('fixed', 'context_adaptive_q1', 'information_gain')
        AND jsonb_typeof(eligibility_snapshot) = 'object'
        AND record_origin_code IN ('real_observation', 'DRY_RUN_FIXTURE')
    )
);

CREATE FUNCTION calibration.enforce_question_assignment_eligibility()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_question_assignment_eligibility$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM calibration.question_eligibility AS eligibility
        JOIN calibration.presentation AS presentation
          ON presentation.presentation_id = NEW.presentation_id
        JOIN calibration.beverage_sample AS sample
          ON sample.beverage_sample_id = presentation.beverage_sample_id
        JOIN calibration.preparation_condition AS prep
          ON prep.preparation_condition_id = sample.preparation_condition_id
        JOIN calibration.roast_batch AS roast
          ON roast.roast_batch_id = sample.roast_batch_id
        WHERE eligibility.question_id = NEW.question_id
          AND NEW.step_number BETWEEN eligibility.minimum_step AND eligibility.maximum_step
          AND (eligibility.preparation_concept_id IS NULL
               OR eligibility.preparation_concept_id = prep.preparation_concept_id)
          AND (eligibility.roast_category_id IS NULL
               OR eligibility.roast_category_id = roast.roast_category_id)
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'question_assignment_eligible_ck',
          MESSAGE = 'question_assignment_eligible_ck: question is not eligible for this context and step';
    END IF;
    RETURN NEW;
END;
$enforce_question_assignment_eligibility$;

CREATE TRIGGER question_assignment_eligible_biu
BEFORE INSERT OR UPDATE ON calibration.question_assignment
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_question_assignment_eligibility();

CREATE TABLE calibration.question_response (
    question_response_id BIGINT GENERATED ALWAYS AS IDENTITY,
    question_assignment_id BIGINT NOT NULL,
    response_status_code TEXT NOT NULL,
    response_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT question_response_pk PRIMARY KEY (question_response_id),
    CONSTRAINT question_response_assignment_uq UNIQUE (question_assignment_id),
    CONSTRAINT question_response_assignment_fk FOREIGN KEY (question_assignment_id)
        REFERENCES calibration.question_assignment (question_assignment_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_response_text_ck CHECK (
        response_status_code IN ('answered', 'skipped', 'unresolved')
        AND jsonb_typeof(response_metadata) = 'object'
    )
);

CREATE TABLE calibration.question_response_selection (
    question_response_id BIGINT NOT NULL,
    question_option_id BIGINT NOT NULL,
    selection_order SMALLINT NOT NULL,
    CONSTRAINT question_response_selection_pk PRIMARY KEY (
        question_response_id, question_option_id
    ),
    CONSTRAINT question_response_selection_order_uq UNIQUE (
        question_response_id, selection_order
    ),
    CONSTRAINT question_response_selection_response_fk FOREIGN KEY (question_response_id)
        REFERENCES calibration.question_response (question_response_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_response_selection_option_fk FOREIGN KEY (question_option_id)
        REFERENCES calibration.question_option (question_option_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_response_selection_order_ck CHECK (selection_order BETWEEN 1 AND 5)
);

CREATE FUNCTION calibration.enforce_question_response_cardinality()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_question_response_cardinality$
DECLARE selected_count INTEGER; min_count INTEGER; max_count INTEGER;
BEGIN
    SELECT count(*), question.min_selections, question.max_selections
    INTO selected_count, min_count, max_count
    FROM calibration.question_response_selection AS selection
    JOIN calibration.question_response AS response
      ON response.question_response_id = NEW.question_response_id
    JOIN calibration.question_assignment AS assignment
      ON assignment.question_assignment_id = response.question_assignment_id
    JOIN calibration.question AS question ON question.question_id = assignment.question_id
    WHERE selection.question_response_id = NEW.question_response_id
    GROUP BY question.min_selections, question.max_selections;
    IF selected_count IS NOT NULL AND selected_count > max_count THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'question_response_cardinality_ck',
          MESSAGE = 'question_response_cardinality_ck: selected option count exceeds question cardinality';
    END IF;
    IF EXISTS (
        SELECT 1 FROM calibration.question_response_selection AS selection
        JOIN calibration.question_option AS option
          ON option.question_option_id = selection.question_option_id
        JOIN calibration.question_response AS response
          ON response.question_response_id = selection.question_response_id
        JOIN calibration.question_assignment AS assignment
          ON assignment.question_assignment_id = response.question_assignment_id
        WHERE selection.question_response_id = NEW.question_response_id
          AND option.question_id <> assignment.question_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'question_response_option_membership_ck',
          MESSAGE = 'question_response_option_membership_ck: selected option belongs to a different question';
    END IF;
    RETURN NEW;
END;
$enforce_question_response_cardinality$;

CREATE CONSTRAINT TRIGGER question_response_cardinality_aiu
AFTER INSERT OR UPDATE ON calibration.question_response_selection
DEFERRABLE INITIALLY IMMEDIATE
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_question_response_cardinality();

CREATE TABLE calibration.candidate_reference_judgment (
    candidate_reference_judgment_id BIGINT GENERATED ALWAYS AS IDENTITY,
    presentation_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    usefulness_code TEXT NOT NULL,
    rank_position SMALLINT,
    record_origin_code TEXT NOT NULL DEFAULT 'real_observation',
    CONSTRAINT candidate_reference_judgment_pk PRIMARY KEY (candidate_reference_judgment_id),
    CONSTRAINT candidate_reference_judgment_fact_uq UNIQUE (presentation_id, concept_id),
    CONSTRAINT candidate_reference_judgment_presentation_fk FOREIGN KEY (presentation_id)
        REFERENCES calibration.presentation (presentation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_reference_judgment_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT candidate_reference_judgment_value_ck CHECK (
        usefulness_code IN ('useful', 'not_useful', 'uncertain')
        AND (rank_position IS NULL OR rank_position BETWEEN 1 AND 8)
        AND record_origin_code IN ('real_observation', 'DRY_RUN_FIXTURE')
    )
);

CREATE TABLE calibration.grouped_split (
    grouped_split_id BIGINT GENERATED ALWAYS AS IDENTITY,
    analysis_plan_id BIGINT NOT NULL,
    coffee_lot_id BIGINT NOT NULL,
    split_code TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL,
    CONSTRAINT grouped_split_pk PRIMARY KEY (grouped_split_id),
    CONSTRAINT grouped_split_lot_uq UNIQUE (analysis_plan_id, coffee_lot_id),
    CONSTRAINT grouped_split_analysis_fk FOREIGN KEY (analysis_plan_id)
        REFERENCES calibration.analysis_plan (analysis_plan_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT grouped_split_lot_fk FOREIGN KEY (coffee_lot_id)
        REFERENCES calibration.coffee_lot (coffee_lot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT grouped_split_value_ck CHECK (
        split_code IN ('development', 'validation', 'held_out_test')
        AND snapshot_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE calibration.analysis_run (
    analysis_run_id BIGINT GENERATED ALWAYS AS IDENTITY,
    analysis_run_key TEXT NOT NULL,
    analysis_plan_id BIGINT NOT NULL,
    release_snapshot_id BIGINT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    input_snapshot_sha256 TEXT NOT NULL,
    estimability_status TEXT NOT NULL,
    result_metadata JSONB NOT NULL,
    CONSTRAINT analysis_run_pk PRIMARY KEY (analysis_run_id),
    CONSTRAINT analysis_run_key_uq UNIQUE (analysis_run_key),
    CONSTRAINT analysis_run_analysis_fk FOREIGN KEY (analysis_plan_id)
        REFERENCES calibration.analysis_plan (analysis_plan_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT analysis_run_release_fk FOREIGN KEY (release_snapshot_id)
        REFERENCES calibration.release_snapshot (release_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT analysis_run_text_ck CHECK (
        analysis_run_key = lower(btrim(analysis_run_key)) AND analysis_run_key <> ''
        AND code_commit_sha ~ '^[0-9a-f]{40}$'
        AND input_snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND estimability_status IN ('NOT_ESTIMABLE', 'ESTIMABLE')
        AND jsonb_typeof(result_metadata) = 'object'
    )
);

CREATE TABLE calibration.model_candidate_output (
    model_candidate_output_id BIGINT GENERATED ALWAYS AS IDENTITY,
    analysis_run_id BIGINT NOT NULL,
    presentation_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    candidate_tier_code TEXT NOT NULL,
    rank_position SMALLINT NOT NULL,
    score_value NUMERIC,
    output_role_code TEXT NOT NULL,
    CONSTRAINT model_candidate_output_pk PRIMARY KEY (model_candidate_output_id),
    CONSTRAINT model_candidate_output_rank_uq UNIQUE (
        analysis_run_id, presentation_id, rank_position
    ),
    CONSTRAINT model_candidate_output_concept_uq UNIQUE (
        analysis_run_id, presentation_id, concept_id
    ),
    CONSTRAINT model_candidate_output_analysis_fk FOREIGN KEY (analysis_run_id)
        REFERENCES calibration.analysis_run (analysis_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_candidate_output_presentation_fk FOREIGN KEY (presentation_id)
        REFERENCES calibration.presentation (presentation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_candidate_output_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT model_candidate_output_role_ck CHECK (
        candidate_tier_code IN ('primary', 'secondary')
        AND rank_position BETWEEN 1 AND 8
        AND output_role_code = 'model_candidate_reference'
    )
);

COMMIT;
