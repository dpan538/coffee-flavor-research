\set ON_ERROR_STOP on

-- Round 3C governance for a future human-participant calibration dataset.
-- This migration contains contracts and no sensory observations.

BEGIN;

CREATE SCHEMA calibration;

CREATE TABLE calibration.study (
    study_id BIGINT GENERATED ALWAYS AS IDENTITY,
    study_key TEXT NOT NULL,
    title TEXT NOT NULL,
    design_scale_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    human_participant_ethics_required BOOLEAN NOT NULL,
    institutional_approval_status TEXT NOT NULL,
    public_data_consent_required BOOLEAN NOT NULL,
    ethics_or_approval_gate BOOLEAN NOT NULL,
    consent_material_ready BOOLEAN NOT NULL,
    public_release_rights_ready BOOLEAN NOT NULL,
    empirical_observation_count INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT study_pk PRIMARY KEY (study_id),
    CONSTRAINT study_key_uq UNIQUE (study_key),
    CONSTRAINT study_key_ck CHECK (
        study_key = lower(btrim(study_key)) AND study_key <> ''
    ),
    CONSTRAINT study_text_ck CHECK (
        title = btrim(title) AND title <> ''
        AND design_scale_code IN ('minimum', 'preferred', 'expanded')
        AND lifecycle_status_code IN ('design', 'approved', 'collecting', 'closed')
        AND institutional_approval_status IN (
            'NOT_OBTAINED', 'NOT_REQUIRED', 'OBTAINED', 'EXPIRED', 'WITHDRAWN'
        )
        AND empirical_observation_count >= 0
    ),
    CONSTRAINT study_collection_gate_ck CHECK (
        lifecycle_status_code NOT IN ('approved', 'collecting')
        OR ethics_or_approval_gate
           AND consent_material_ready
           AND public_release_rights_ready
    )
);

CREATE TABLE calibration.protocol_version (
    protocol_version_id BIGINT GENERATED ALWAYS AS IDENTITY,
    protocol_version_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    repository_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    frozen_on DATE NOT NULL,
    is_frozen BOOLEAN NOT NULL,
    CONSTRAINT protocol_version_pk PRIMARY KEY (protocol_version_id),
    CONSTRAINT protocol_version_key_uq UNIQUE (protocol_version_key),
    CONSTRAINT protocol_version_study_version_uq UNIQUE (study_id, version_label),
    CONSTRAINT protocol_version_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT protocol_version_text_ck CHECK (
        protocol_version_key = lower(btrim(protocol_version_key))
        AND protocol_version_key <> ''
        AND version_label = btrim(version_label) AND version_label <> ''
        AND repository_path = btrim(repository_path) AND repository_path <> ''
        AND content_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE calibration.analysis_plan (
    analysis_plan_id BIGINT GENERATED ALWAYS AS IDENTITY,
    analysis_plan_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    repository_path TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    split_method TEXT NOT NULL,
    split_seed TEXT NOT NULL,
    grouping_variable TEXT NOT NULL,
    estimability_status TEXT NOT NULL,
    is_frozen BOOLEAN NOT NULL,
    CONSTRAINT analysis_plan_pk PRIMARY KEY (analysis_plan_id),
    CONSTRAINT analysis_plan_key_uq UNIQUE (analysis_plan_key),
    CONSTRAINT analysis_plan_study_version_uq UNIQUE (study_id, version_label),
    CONSTRAINT analysis_plan_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT analysis_plan_text_ck CHECK (
        analysis_plan_key = lower(btrim(analysis_plan_key))
        AND analysis_plan_key <> ''
        AND version_label = btrim(version_label) AND version_label <> ''
        AND repository_path = btrim(repository_path) AND repository_path <> ''
        AND content_sha256 ~ '^[0-9a-f]{64}$'
        AND split_method = btrim(split_method) AND split_method <> ''
        AND split_seed = btrim(split_seed) AND split_seed <> ''
        AND grouping_variable = btrim(grouping_variable)
        AND grouping_variable <> ''
        AND estimability_status IN ('NOT_ESTIMABLE', 'ESTIMABLE')
    )
);

CREATE TABLE calibration.release_snapshot (
    release_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    release_snapshot_key TEXT NOT NULL,
    study_id BIGINT NOT NULL,
    protocol_version_id BIGINT NOT NULL,
    analysis_plan_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    manifest_sha256 TEXT,
    checksums_sha256 TEXT,
    license_spdx TEXT,
    rights_statement TEXT,
    split_snapshot_sha256 TEXT,
    real_observation_count INTEGER NOT NULL DEFAULT 0,
    dry_run_fixture_count INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT release_snapshot_pk PRIMARY KEY (release_snapshot_id),
    CONSTRAINT release_snapshot_key_uq UNIQUE (release_snapshot_key),
    CONSTRAINT release_snapshot_study_version_uq UNIQUE (study_id, version_label),
    CONSTRAINT release_snapshot_study_fk FOREIGN KEY (study_id)
        REFERENCES calibration.study (study_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT release_snapshot_protocol_fk FOREIGN KEY (protocol_version_id)
        REFERENCES calibration.protocol_version (protocol_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT release_snapshot_analysis_fk FOREIGN KEY (analysis_plan_id)
        REFERENCES calibration.analysis_plan (analysis_plan_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT release_snapshot_text_ck CHECK (
        release_snapshot_key = lower(btrim(release_snapshot_key))
        AND release_snapshot_key <> ''
        AND version_label = btrim(version_label) AND version_label <> ''
        AND lifecycle_status_code IN ('design', 'internal', 'public')
        AND (manifest_sha256 IS NULL OR manifest_sha256 ~ '^[0-9a-f]{64}$')
        AND (checksums_sha256 IS NULL OR checksums_sha256 ~ '^[0-9a-f]{64}$')
        AND (split_snapshot_sha256 IS NULL
             OR split_snapshot_sha256 ~ '^[0-9a-f]{64}$')
        AND real_observation_count >= 0
        AND dry_run_fixture_count >= 0
    ),
    CONSTRAINT release_snapshot_public_metadata_ck CHECK (
        lifecycle_status_code <> 'public'
        OR manifest_sha256 IS NOT NULL
           AND checksums_sha256 IS NOT NULL
           AND license_spdx IS NOT NULL AND btrim(license_spdx) <> ''
           AND rights_statement IS NOT NULL AND btrim(rights_statement) <> ''
           AND split_snapshot_sha256 IS NOT NULL
    )
);

CREATE FUNCTION calibration.reject_direct_identifiers(input JSONB)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $reject_direct_identifiers$
    SELECT input::TEXT !~* '(^|["{,[:space:]])(name|email|phone|address|street|postcode|postal_code)["[:space:]]*:'
       AND input::TEXT !~* '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}'
$reject_direct_identifiers$;

COMMENT ON SCHEMA calibration IS
    'Experimental calibration governance, conditions, observations, question interactions, analyses, and release provenance; never canonical sensory truth.';

COMMIT;
