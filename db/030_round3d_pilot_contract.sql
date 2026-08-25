\set ON_ERROR_STOP on

BEGIN;

CREATE TABLE calibration.pilot_matrix_snapshot (
    pilot_matrix_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    pilot_matrix_snapshot_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    protocol_version_id BIGINT NOT NULL,
    generator_path TEXT NOT NULL,
    randomization_seed TEXT NOT NULL,
    matrix_sha256 TEXT NOT NULL,
    randomization_sha256 TEXT NOT NULL,
    question_assignment_sha256 TEXT NOT NULL,
    protocol_sha256 TEXT NOT NULL,
    split_inventory_sha256 TEXT NOT NULL,
    coffee_lot_count INTEGER NOT NULL,
    roast_batch_count INTEGER NOT NULL,
    preparation_family_count INTEGER NOT NULL,
    roast_category_count INTEGER NOT NULL,
    condition_cell_count INTEGER NOT NULL,
    beverage_sample_count INTEGER NOT NULL,
    session_slot_count INTEGER NOT NULL,
    presentation_slot_count INTEGER NOT NULL,
    question_assignment_slot_count INTEGER NOT NULL,
    dry_run_fixture_count INTEGER NOT NULL,
    real_observation_count INTEGER NOT NULL,
    is_frozen BOOLEAN NOT NULL,
    CONSTRAINT pilot_matrix_snapshot_pk PRIMARY KEY (pilot_matrix_snapshot_id),
    CONSTRAINT pilot_matrix_snapshot_key_uq UNIQUE (pilot_matrix_snapshot_key),
    CONSTRAINT pilot_matrix_snapshot_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT pilot_matrix_snapshot_protocol_fk FOREIGN KEY (protocol_version_id)
        REFERENCES calibration.protocol_version (protocol_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT pilot_matrix_snapshot_text_ck CHECK (
        pilot_matrix_snapshot_key = lower(btrim(pilot_matrix_snapshot_key))
        AND pilot_matrix_snapshot_key <> ''
        AND generator_path = btrim(generator_path) AND generator_path <> ''
        AND randomization_seed = btrim(randomization_seed)
        AND randomization_seed <> ''
        AND matrix_sha256 ~ '^[0-9a-f]{64}$'
        AND randomization_sha256 ~ '^[0-9a-f]{64}$'
        AND question_assignment_sha256 ~ '^[0-9a-f]{64}$'
        AND protocol_sha256 ~ '^[0-9a-f]{64}$'
        AND split_inventory_sha256 ~ '^[0-9a-f]{64}$'
        AND coffee_lot_count = 2
        AND roast_batch_count = 14
        AND preparation_family_count = 7
        AND roast_category_count = 7
        AND condition_cell_count = 66
        AND beverage_sample_count = 132
        AND session_slot_count = 192
        AND presentation_slot_count = 1512
        AND question_assignment_slot_count = 3600
        AND dry_run_fixture_count = 5
        AND real_observation_count = 0
    )
);

CREATE TABLE calibration.pilot_session_slot (
    pilot_session_slot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    pilot_matrix_snapshot_id BIGINT NOT NULL,
    session_slot_key TEXT NOT NULL,
    cohort_code TEXT NOT NULL,
    assessor_slot_code TEXT NOT NULL,
    session_number SMALLINT NOT NULL,
    sample_burden SMALLINT NOT NULL,
    CONSTRAINT pilot_session_slot_pk PRIMARY KEY (pilot_session_slot_id),
    CONSTRAINT pilot_session_slot_key_uq UNIQUE (session_slot_key),
    CONSTRAINT pilot_session_slot_assessor_session_uq UNIQUE (
        pilot_matrix_snapshot_id, assessor_slot_code, session_number
    ),
    CONSTRAINT pilot_session_slot_snapshot_fk FOREIGN KEY (pilot_matrix_snapshot_id)
        REFERENCES calibration.pilot_matrix_snapshot (pilot_matrix_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT pilot_session_slot_value_ck CHECK (
        session_slot_key = lower(btrim(session_slot_key)) AND session_slot_key <> ''
        AND cohort_code IN ('reference', 'ordinary_user')
        AND assessor_slot_code ~ '^[A-Z0-9_]{4,32}$'
        AND session_number > 0
        AND (cohort_code = 'reference' AND sample_burden = 11
             OR cohort_code = 'ordinary_user' AND sample_burden = 6)
    )
);

CREATE TABLE calibration.pilot_presentation_slot (
    pilot_presentation_slot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    pilot_session_slot_id BIGINT NOT NULL,
    presentation_slot_key TEXT NOT NULL,
    beverage_sample_id BIGINT NOT NULL,
    sequence_position SMALLINT NOT NULL,
    blinded_code TEXT NOT NULL,
    CONSTRAINT pilot_presentation_slot_pk PRIMARY KEY (pilot_presentation_slot_id),
    CONSTRAINT pilot_presentation_slot_key_uq UNIQUE (presentation_slot_key),
    CONSTRAINT pilot_presentation_slot_position_uq UNIQUE (
        pilot_session_slot_id, sequence_position
    ),
    CONSTRAINT pilot_presentation_slot_sample_uq UNIQUE (
        pilot_session_slot_id, beverage_sample_id
    ),
    CONSTRAINT pilot_presentation_slot_session_fk FOREIGN KEY (pilot_session_slot_id)
        REFERENCES calibration.pilot_session_slot (pilot_session_slot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT pilot_presentation_slot_sample_fk FOREIGN KEY (beverage_sample_id)
        REFERENCES calibration.beverage_sample (beverage_sample_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT pilot_presentation_slot_value_ck CHECK (
        presentation_slot_key = lower(btrim(presentation_slot_key))
        AND presentation_slot_key <> ''
        AND sequence_position > 0
        AND blinded_code ~ '^[0-9]{3}$'
    )
);

CREATE TABLE calibration.pilot_question_assignment_slot (
    pilot_question_assignment_slot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    pilot_presentation_slot_id BIGINT NOT NULL,
    question_assignment_slot_key TEXT NOT NULL,
    step_number SMALLINT NOT NULL,
    logical_question_code TEXT NOT NULL,
    assignment_status TEXT NOT NULL,
    CONSTRAINT pilot_question_assignment_slot_pk PRIMARY KEY (pilot_question_assignment_slot_id),
    CONSTRAINT pilot_question_assignment_slot_key_uq UNIQUE (question_assignment_slot_key),
    CONSTRAINT pilot_question_assignment_slot_step_uq UNIQUE (
        pilot_presentation_slot_id, step_number
    ),
    CONSTRAINT pilot_question_assignment_slot_presentation_fk FOREIGN KEY (pilot_presentation_slot_id)
        REFERENCES calibration.pilot_presentation_slot (pilot_presentation_slot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT pilot_question_assignment_slot_value_ck CHECK (
        question_assignment_slot_key = lower(btrim(question_assignment_slot_key))
        AND question_assignment_slot_key <> ''
        AND step_number BETWEEN 1 AND 5
        AND logical_question_code IN (
            'family_direction', 'fruit_direction', 'sweet_direction',
            'roast_direction', 'bright_acidity', 'texture_direction'
        )
        AND (step_number = 1 AND assignment_status = 'mandatory'
             OR step_number > 1 AND assignment_status = 'conditional')
    )
);

CREATE TABLE calibration.engineering_dry_run_case (
    engineering_dry_run_case_id BIGINT GENERATED ALWAYS AS IDENTITY,
    pilot_matrix_snapshot_id BIGINT NOT NULL,
    dry_run_case_key TEXT NOT NULL,
    c0_code TEXT NOT NULL,
    c1_code TEXT NOT NULL,
    answer_path TEXT NOT NULL,
    expected_stop_step SMALLINT NOT NULL,
    explicit_override BOOLEAN NOT NULL,
    fixture_label TEXT NOT NULL,
    mechanics_pass BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT engineering_dry_run_case_pk PRIMARY KEY (engineering_dry_run_case_id),
    CONSTRAINT engineering_dry_run_case_key_uq UNIQUE (dry_run_case_key),
    CONSTRAINT engineering_dry_run_case_snapshot_fk FOREIGN KEY (pilot_matrix_snapshot_id)
        REFERENCES calibration.pilot_matrix_snapshot (pilot_matrix_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT engineering_dry_run_case_value_ck CHECK (
        dry_run_case_key = lower(btrim(dry_run_case_key)) AND dry_run_case_key <> ''
        AND c0_code IN (
            'filter_percolation', 'immersion', 'hybrid',
            'espresso_pressure', 'diluted_espresso', 'stovetop_boiled',
            'cold_extraction', 'espresso_milk'
        )
        AND c1_code IN (
            'extremely_light', 'light', 'medium_light', 'medium',
            'medium_dark', 'dark', 'extremely_dark'
        )
        AND answer_path = btrim(answer_path) AND answer_path <> ''
        AND expected_stop_step BETWEEN 1 AND 5
        AND fixture_label = 'DRY_RUN_FIXTURE'
    )
);

CREATE TABLE calibration.capture_import_batch (
    capture_import_batch_id BIGINT GENERATED ALWAYS AS IDENTITY,
    capture_import_batch_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    protocol_version_id BIGINT NOT NULL,
    source_manifest_sha256 TEXT NOT NULL,
    staged_row_count INTEGER NOT NULL,
    real_row_count INTEGER NOT NULL,
    fixture_row_count INTEGER NOT NULL,
    pii_scan_pass BOOLEAN NOT NULL,
    governance_gate_pass BOOLEAN NOT NULL,
    promotion_status TEXT NOT NULL,
    CONSTRAINT capture_import_batch_pk PRIMARY KEY (capture_import_batch_id),
    CONSTRAINT capture_import_batch_key_uq UNIQUE (capture_import_batch_key),
    CONSTRAINT capture_import_batch_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT capture_import_batch_protocol_fk FOREIGN KEY (protocol_version_id)
        REFERENCES calibration.protocol_version (protocol_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT capture_import_batch_value_ck CHECK (
        capture_import_batch_key = lower(btrim(capture_import_batch_key))
        AND capture_import_batch_key <> ''
        AND source_manifest_sha256 ~ '^[0-9a-f]{64}$'
        AND staged_row_count >= 0 AND real_row_count >= 0
        AND fixture_row_count >= 0
        AND staged_row_count = real_row_count + fixture_row_count
        AND promotion_status IN ('validated_empty', 'staged', 'promoted', 'rejected')
        AND (promotion_status <> 'promoted'
             OR real_row_count > 0 AND pii_scan_pass AND governance_gate_pass)
    )
);

CREATE TABLE calibration.capture_import_row (
    capture_import_row_id BIGINT GENERATED ALWAYS AS IDENTITY,
    capture_import_batch_id BIGINT NOT NULL,
    source_file TEXT NOT NULL,
    source_row_number INTEGER NOT NULL,
    row_payload JSONB NOT NULL,
    record_origin_code TEXT NOT NULL,
    CONSTRAINT capture_import_row_pk PRIMARY KEY (capture_import_row_id),
    CONSTRAINT capture_import_row_source_uq UNIQUE (
        capture_import_batch_id, source_file, source_row_number
    ),
    CONSTRAINT capture_import_row_batch_fk FOREIGN KEY (capture_import_batch_id)
        REFERENCES calibration.capture_import_batch (capture_import_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT capture_import_row_value_ck CHECK (
        source_file = btrim(source_file) AND source_file <> ''
        AND source_row_number >= 2
        AND jsonb_typeof(row_payload) = 'object'
        AND calibration.reject_direct_identifiers(row_payload)
        AND record_origin_code IN (
            'real_observation', 'DRY_RUN_FIXTURE', 'TEST_FIXTURE'
        )
    )
);

CREATE FUNCTION calibration.protect_frozen_pilot_plan()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_pilot_plan$
DECLARE
    snapshot_id BIGINT;
BEGIN
    CASE TG_TABLE_NAME
      WHEN 'pilot_matrix_snapshot' THEN
        snapshot_id := OLD.pilot_matrix_snapshot_id;
      WHEN 'pilot_session_slot' THEN
        snapshot_id := OLD.pilot_matrix_snapshot_id;
      WHEN 'pilot_presentation_slot' THEN
        SELECT session.pilot_matrix_snapshot_id INTO snapshot_id
        FROM calibration.pilot_session_slot AS session
        WHERE session.pilot_session_slot_id = OLD.pilot_session_slot_id;
      WHEN 'pilot_question_assignment_slot' THEN
        SELECT session.pilot_matrix_snapshot_id INTO snapshot_id
        FROM calibration.pilot_presentation_slot AS presentation
        JOIN calibration.pilot_session_slot AS session
          ON session.pilot_session_slot_id = presentation.pilot_session_slot_id
        WHERE presentation.pilot_presentation_slot_id =
              OLD.pilot_presentation_slot_id;
      WHEN 'engineering_dry_run_case' THEN
        snapshot_id := OLD.pilot_matrix_snapshot_id;
      ELSE
        RAISE EXCEPTION 'unsupported frozen-plan table: %', TG_TABLE_NAME;
    END CASE;

    IF EXISTS (
        SELECT 1 FROM calibration.pilot_matrix_snapshot AS snapshot
        WHERE snapshot.pilot_matrix_snapshot_id = snapshot_id
          AND snapshot.is_frozen
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'round3d_frozen_pilot_plan_ck',
          MESSAGE = 'round3d_frozen_pilot_plan_ck: frozen matrix, schedule, assignment, and fixture rows are immutable';
    END IF;
    RETURN OLD;
END;
$protect_frozen_pilot_plan$;

CREATE TRIGGER pilot_matrix_snapshot_frozen_bud
BEFORE UPDATE OR DELETE ON calibration.pilot_matrix_snapshot
FOR EACH ROW EXECUTE FUNCTION calibration.protect_frozen_pilot_plan();
CREATE TRIGGER pilot_session_slot_frozen_bud
BEFORE UPDATE OR DELETE ON calibration.pilot_session_slot
FOR EACH ROW EXECUTE FUNCTION calibration.protect_frozen_pilot_plan();
CREATE TRIGGER pilot_presentation_slot_frozen_bud
BEFORE UPDATE OR DELETE ON calibration.pilot_presentation_slot
FOR EACH ROW EXECUTE FUNCTION calibration.protect_frozen_pilot_plan();
CREATE TRIGGER pilot_question_assignment_slot_frozen_bud
BEFORE UPDATE OR DELETE ON calibration.pilot_question_assignment_slot
FOR EACH ROW EXECUTE FUNCTION calibration.protect_frozen_pilot_plan();
CREATE TRIGGER engineering_dry_run_case_frozen_bud
BEFORE UPDATE OR DELETE ON calibration.engineering_dry_run_case
FOR EACH ROW EXECUTE FUNCTION calibration.protect_frozen_pilot_plan();

CREATE FUNCTION calibration.enforce_real_observation_collection_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_real_observation_collection_gate$
DECLARE
    target_study_id BIGINT;
BEGIN
    IF NEW.record_origin_code <> 'real_observation' THEN
        RETURN NEW;
    END IF;

    CASE TG_TABLE_NAME
      WHEN 'beverage_sample', 'assessor', 'session' THEN
        target_study_id := NEW.study_id;
      WHEN 'presentation' THEN
        SELECT session.study_id INTO target_study_id
        FROM calibration.session AS session
        WHERE session.session_id = NEW.session_id;
      WHEN 'sensory_observation' THEN
        SELECT session.study_id INTO target_study_id
        FROM calibration.presentation AS presentation
        JOIN calibration.session AS session
          ON session.session_id = presentation.session_id
        WHERE presentation.presentation_id = NEW.presentation_id;
      WHEN 'question_assignment', 'candidate_reference_judgment' THEN
        SELECT session.study_id INTO target_study_id
        FROM calibration.presentation AS presentation
        JOIN calibration.session AS session
          ON session.session_id = presentation.session_id
        WHERE presentation.presentation_id = NEW.presentation_id;
      WHEN 'capture_import_row' THEN
        SELECT batch.study_id INTO target_study_id
        FROM calibration.capture_import_batch AS batch
        WHERE batch.capture_import_batch_id = NEW.capture_import_batch_id;
      ELSE
        RAISE EXCEPTION 'unsupported real-observation gate table: %',
          TG_TABLE_NAME;
    END CASE;

    IF target_study_id IS NULL OR NOT EXISTS (
        SELECT 1 FROM calibration.study AS study
        WHERE study.study_id = target_study_id
          AND study.ethics_or_approval_gate
          AND study.consent_material_ready
          AND study.public_release_rights_ready
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'real_observation_collection_governance_ck',
          MESSAGE = 'real_observation_collection_governance_ck: real observation writes require ethics, consent, and public-release rights gates';
    END IF;
    RETURN NEW;
END;
$enforce_real_observation_collection_gate$;

CREATE TRIGGER beverage_sample_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.beverage_sample
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER assessor_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.assessor
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER session_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.session
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER presentation_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.presentation
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER sensory_observation_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.sensory_observation
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER question_assignment_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.question_assignment
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER candidate_judgment_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.candidate_reference_judgment
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();
CREATE TRIGGER capture_import_row_real_observation_aiu
AFTER INSERT OR UPDATE ON calibration.capture_import_row
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_real_observation_collection_gate();

CREATE FUNCTION calibration.enforce_capture_promotion_gate()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_capture_promotion_gate$
BEGIN
    IF NEW.promotion_status = 'promoted' AND NOT EXISTS (
        SELECT 1 FROM calibration.study AS study
        WHERE study.study_id = NEW.study_id
          AND study.ethics_or_approval_gate
          AND study.consent_material_ready
          AND study.public_release_rights_ready
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
          CONSTRAINT = 'capture_import_promotion_governance_ck',
          MESSAGE = 'capture_import_promotion_governance_ck: real capture promotion requires ethics, consent, and public-release rights gates';
    END IF;
    RETURN NEW;
END;
$enforce_capture_promotion_gate$;

CREATE TRIGGER capture_import_batch_promotion_biu
BEFORE INSERT OR UPDATE ON calibration.capture_import_batch
FOR EACH ROW EXECUTE FUNCTION calibration.enforce_capture_promotion_gate();

COMMIT;
