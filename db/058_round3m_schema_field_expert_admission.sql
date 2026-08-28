BEGIN;

-- Migration 055 already made review receipts append-only.  Migration 058
-- closes the separate initial-truth gap: an actual-human claim must bind a
-- governed acquired artifact, a current qualification, a current admission,
-- and one bounded row-level reviewer decision.  No reviewer evidence is
-- seeded by this migration.

CREATE TABLE audit.round3m_migration_058_approval_contract (
    migration_key TEXT NOT NULL,
    user_approved BOOLEAN NOT NULL,
    approval_scope_code TEXT NOT NULL,
    user_approval_counts_as_reviewer_evidence BOOLEAN NOT NULL,
    main_promotion_allowed BOOLEAN NOT NULL,
    model_training_allowed BOOLEAN NOT NULL,
    training_corpus_freeze_allowed BOOLEAN NOT NULL,
    approval_record_locator TEXT NOT NULL,
    approved_on DATE NOT NULL,
    CONSTRAINT round3m_migration_058_approval_contract_pk PRIMARY KEY (
        migration_key
    ),
    CONSTRAINT round3m_migration_058_approval_contract_ck CHECK (
        migration_key = 'round3m.migration-058'
        AND user_approved
        AND approval_scope_code =
            'SCHEMA_APPLICATION_REBUILDS_CI_COMMIT_BRANCH_PUSH'
        AND NOT user_approval_counts_as_reviewer_evidence
        AND NOT main_promotion_allowed
        AND NOT model_training_allowed
        AND NOT training_corpus_freeze_allowed
        AND approval_record_locator =
            'conversation://round3m/migration-058-explicit-approval'
        AND approved_on = DATE '2026-08-28'
    )
);

INSERT INTO audit.round3m_migration_058_approval_contract (
    migration_key, user_approved, approval_scope_code,
    user_approval_counts_as_reviewer_evidence, main_promotion_allowed,
    model_training_allowed, training_corpus_freeze_allowed,
    approval_record_locator, approved_on
) VALUES (
    'round3m.migration-058', TRUE,
    'SCHEMA_APPLICATION_REBUILDS_CI_COMMIT_BRANCH_PUSH',
    FALSE, FALSE, FALSE, FALSE,
    'conversation://round3m/migration-058-explicit-approval',
    DATE '2026-08-28'
);

CREATE TRIGGER round3m_migration_058_approval_contract_bud
BEFORE UPDATE OR DELETE ON audit.round3m_migration_058_approval_contract
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

-- A pre-058 human/expert row cannot be upgraded by adding references after
-- the fact.  The public checkpoint has zero such rows, so fail rather than
-- manufacture an evidence chain for historical claims.
DO $round3m_no_pre058_self_attested_human_receipts$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt
        WHERE review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_pre058_human_receipt_absent_ck',
            MESSAGE = 'migration 058 requires zero pre-existing human/expert descriptor receipts; unsupported old claims cannot be upgraded in place';
    END IF;
END
$round3m_no_pre058_self_attested_human_receipts$;

CREATE TABLE evidence.round3m_reviewer_evidence_artifact (
    reviewer_evidence_artifact_id TEXT NOT NULL,
    artifact_purpose_code TEXT NOT NULL,
    evidence_classification_code TEXT NOT NULL,
    governed_locator TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    byte_count BIGINT NOT NULL,
    non_storage_reason TEXT,
    acquired_at TIMESTAMPTZ NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    storage_state_code TEXT NOT NULL,
    privacy_state_code TEXT NOT NULL,
    supplying_authority TEXT NOT NULL,
    acquisition_method_code TEXT NOT NULL,
    manifest_sha256 TEXT,
    container_sha256 TEXT,
    CONSTRAINT round3m_reviewer_evidence_artifact_pk PRIMARY KEY (
        reviewer_evidence_artifact_id
    ),
    CONSTRAINT round3m_reviewer_evidence_artifact_hash_locator_uq UNIQUE (
        artifact_sha256, governed_locator
    ),
    CONSTRAINT round3m_reviewer_evidence_artifact_text_ck CHECK (
        reviewer_evidence_artifact_id =
            lower(btrim(reviewer_evidence_artifact_id))
        AND reviewer_evidence_artifact_id ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND governed_locator = btrim(governed_locator)
        AND governed_locator <> ''
        AND artifact_sha256 ~ '^[0-9a-f]{64}$'
        AND supplying_authority = btrim(supplying_authority)
        AND supplying_authority <> ''
        AND lower(supplying_authority)
            !~ '(^|[._ /-])codex($|[._ /-])'
        AND (
            manifest_sha256 IS NULL
            OR manifest_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND (
            container_sha256 IS NULL
            OR container_sha256 ~ '^[0-9a-f]{64}$'
        )
    ),
    CONSTRAINT round3m_reviewer_evidence_artifact_values_ck CHECK (
        artifact_purpose_code IN (
            'REVIEWER_IDENTITY_EVIDENCE',
            'REVIEWER_QUALIFICATION_EVIDENCE',
            'PROTOCOL_TRAINING_ACKNOWLEDGEMENT',
            'REVIEWER_ADMISSION_AUTHORIZATION',
            'REVIEWER_DECISION_BATCH',
            'ROW_LEVEL_REVIEWER_DECISION_EXPORT'
        )
        AND evidence_classification_code IN (
            'ACTUAL_EXTERNAL_HUMAN_DECISION',
            'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
        )
        AND storage_state_code IN (
            'RESTRICTED_RETAINED', 'HASH_AND_LOCATOR_ONLY',
            'EXTERNAL_AUTHORITY_CONTROLLED'
        )
        AND privacy_state_code IN (
            'PSEUDONYMOUS', 'RESTRICTED_PERSONAL_DATA',
            'NO_PERSONAL_DATA'
        )
        AND acquisition_method_code IN (
            'EXTERNAL_FILE_IMPORT', 'GOVERNED_PROJECT_HUMAN_IMPORT',
            'EXTERNAL_AUTHORITY_HASH_RECEIPT'
        )
        AND byte_count >= 0
        AND acquired_at <= imported_at
        AND (
            storage_state_code = 'RESTRICTED_RETAINED'
            AND byte_count > 0
            AND non_storage_reason IS NULL
            OR storage_state_code IN (
                'HASH_AND_LOCATOR_ONLY',
                'EXTERNAL_AUTHORITY_CONTROLLED'
            )
            AND non_storage_reason = btrim(non_storage_reason)
            AND non_storage_reason <> ''
        )
    )
);

CREATE FUNCTION evidence.validate_round3m_reviewer_evidence_artifact()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_reviewer_evidence_artifact$
BEGIN
    IF NEW.imported_at IS DISTINCT FROM transaction_timestamp()
       OR NEW.acquired_at > NEW.imported_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewer_evidence_artifact_import_ck',
            MESSAGE = 'reviewer evidence artifact imported_at is the immutable database import time and acquisition cannot be future-dated';
    END IF;
    IF NEW.governed_locator =
           'conversation://round3m/migration-058-explicit-approval'
       OR lower(NEW.supplying_authority)
          ~ 'migration[ _-]*approval' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT =
                'round3m_user_approval_not_reviewer_evidence_ck',
            MESSAGE = 'migration application approval cannot be imported as reviewer qualification, admission, or decision evidence';
    END IF;
    RETURN NEW;
END
$validate_round3m_reviewer_evidence_artifact$;

CREATE TRIGGER round3m_reviewer_evidence_artifact_bi
BEFORE INSERT ON evidence.round3m_reviewer_evidence_artifact
FOR EACH ROW EXECUTE FUNCTION
    evidence.validate_round3m_reviewer_evidence_artifact();

CREATE TRIGGER round3m_reviewer_evidence_artifact_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_reviewer_evidence_artifact
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TABLE audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id TEXT NOT NULL,
    qualification_identity_key TEXT NOT NULL,
    qualification_version INTEGER NOT NULL,
    supersedes_qualification_receipt_id TEXT,
    reviewer_id BIGINT NOT NULL,
    reviewer_pseudonymous_code TEXT NOT NULL,
    qualification_scope_code TEXT NOT NULL,
    allowed_reviewer_role TEXT NOT NULL,
    qualification_level_code TEXT NOT NULL,
    qualification_protocol_version TEXT NOT NULL,
    qualification_evidence_artifact_id TEXT NOT NULL,
    qualification_evidence_locator TEXT NOT NULL,
    issuing_authority TEXT NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE,
    qualification_state_code TEXT NOT NULL,
    deterministic_payload_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_reviewer_qualification_receipt_pk PRIMARY KEY (
        qualification_receipt_id
    ),
    CONSTRAINT round3m_reviewer_qualification_identity_version_uq UNIQUE (
        qualification_identity_key, qualification_version
    ),
    CONSTRAINT round3m_reviewer_qualification_natural_version_uq UNIQUE (
        reviewer_id, qualification_scope_code, allowed_reviewer_role,
        qualification_protocol_version, qualification_version
    ),
    CONSTRAINT round3m_reviewer_qualification_successor_uq UNIQUE (
        supersedes_qualification_receipt_id
    ),
    CONSTRAINT round3m_reviewer_qualification_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_qualification_artifact_fk FOREIGN KEY (
        qualification_evidence_artifact_id
    ) REFERENCES evidence.round3m_reviewer_evidence_artifact (
        reviewer_evidence_artifact_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_qualification_supersedes_fk FOREIGN KEY (
        supersedes_qualification_receipt_id
    ) REFERENCES audit.round3m_reviewer_qualification_receipt (
        qualification_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_qualification_text_ck CHECK (
        qualification_receipt_id = lower(btrim(qualification_receipt_id))
        AND qualification_receipt_id ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND qualification_identity_key =
            lower(btrim(qualification_identity_key))
        AND qualification_identity_key ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND qualification_version > 0
        AND (qualification_version = 1) =
            (supersedes_qualification_receipt_id IS NULL)
        AND reviewer_pseudonymous_code =
            btrim(reviewer_pseudonymous_code)
        AND reviewer_pseudonymous_code <> ''
        AND lower(reviewer_pseudonymous_code)
            !~ '(^|[._ -])codex($|[._ -])'
        AND qualification_protocol_version =
            btrim(qualification_protocol_version)
        AND qualification_protocol_version <> ''
        AND qualification_evidence_locator =
            btrim(qualification_evidence_locator)
        AND qualification_evidence_locator <> ''
        AND issuing_authority = btrim(issuing_authority)
        AND issuing_authority <> ''
        AND lower(issuing_authority)
            !~ '(^|[._ /-])codex($|[._ /-])'
        AND deterministic_payload_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_reviewer_qualification_values_ck CHECK (
        qualification_scope_code IN (
            'SOURCE_PROVENANCE_REVIEW',
            'DESCRIPTOR_SEGMENTATION_REVIEW',
            'NORMALIZATION_TARGET_REVIEW',
            'SENSORY_ADJUDICATION',
            'RIGHTS_REVIEW'
        )
        AND allowed_reviewer_role IN (
            'SOURCE_AUDITOR', 'PROFESSIONAL_SENSORY_REVIEWER',
            'INDEPENDENT_REVIEWER', 'ADJUDICATOR', 'RIGHTS_REVIEWER'
        )
        AND qualification_level_code IN (
            'PROTOCOL_QUALIFIED', 'PROFESSIONAL', 'EXPERT'
        )
        AND qualification_state_code IN ('ACTIVE', 'REVOKED')
        AND (valid_to IS NULL OR valid_to >= valid_from)
        AND (
            qualification_scope_code <> 'SENSORY_ADJUDICATION'
            OR allowed_reviewer_role = 'ADJUDICATOR'
               AND qualification_level_code = 'EXPERT'
        )
    )
);

CREATE FUNCTION audit.round3m_reviewer_qualification_payload_sha256(
    receipt_value audit.round3m_reviewer_qualification_receipt
)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $round3m_reviewer_qualification_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    (to_jsonb(receipt_value) - ARRAY[
        'deterministic_payload_sha256', 'created_at'
    ])::TEXT
)
$round3m_reviewer_qualification_payload_sha256$;

CREATE FUNCTION audit.validate_round3m_reviewer_qualification_receipt()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_reviewer_qualification_receipt$
DECLARE
    reviewer audit.reviewer%ROWTYPE;
    artifact evidence.round3m_reviewer_evidence_artifact%ROWTYPE;
    predecessor audit.round3m_reviewer_qualification_receipt%ROWTYPE;
BEGIN
    SELECT * INTO STRICT reviewer
    FROM audit.reviewer
    WHERE reviewer_id = NEW.reviewer_id
    FOR KEY SHARE;

    SELECT * INTO STRICT artifact
    FROM evidence.round3m_reviewer_evidence_artifact
    WHERE reviewer_evidence_artifact_id =
          NEW.qualification_evidence_artifact_id
    FOR KEY SHARE;

    IF reviewer.reviewer_key IS DISTINCT FROM
           NEW.reviewer_pseudonymous_code
       OR artifact.artifact_purpose_code NOT IN (
           'REVIEWER_QUALIFICATION_EVIDENCE',
           'PROTOCOL_TRAINING_ACKNOWLEDGEMENT'
       )
       OR artifact.evidence_classification_code NOT IN (
           'ACTUAL_EXTERNAL_HUMAN_DECISION',
           'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
       )
       OR artifact.imported_at > NEW.created_at
       OR NEW.created_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewer_qualification_evidence_ck',
            MESSAGE = 'qualification must bind the exact reviewer and a previously imported governed qualification artifact';
    END IF;

    IF NEW.supersedes_qualification_receipt_id IS NOT NULL THEN
        SELECT * INTO STRICT predecessor
        FROM audit.round3m_reviewer_qualification_receipt
        WHERE qualification_receipt_id =
              NEW.supersedes_qualification_receipt_id
        FOR UPDATE;

        IF predecessor.qualification_identity_key IS DISTINCT FROM
               NEW.qualification_identity_key
           OR predecessor.reviewer_id IS DISTINCT FROM NEW.reviewer_id
           OR predecessor.qualification_scope_code IS DISTINCT FROM
               NEW.qualification_scope_code
           OR predecessor.allowed_reviewer_role IS DISTINCT FROM
               NEW.allowed_reviewer_role
           OR predecessor.qualification_protocol_version IS DISTINCT FROM
               NEW.qualification_protocol_version
           OR predecessor.qualification_version + 1 <>
               NEW.qualification_version
           OR predecessor.created_at > NEW.created_at THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_reviewer_qualification_lineage_ck',
                MESSAGE = 'qualification correction must be the next version of the same reviewer, scope, role, and protocol identity';
        END IF;
    END IF;

    NEW.deterministic_payload_sha256 :=
        audit.round3m_reviewer_qualification_payload_sha256(NEW);
    RETURN NEW;
END
$validate_round3m_reviewer_qualification_receipt$;

CREATE TRIGGER round3m_reviewer_qualification_receipt_bi
BEFORE INSERT ON audit.round3m_reviewer_qualification_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_reviewer_qualification_receipt();

CREATE TRIGGER round3m_reviewer_qualification_receipt_bud
BEFORE UPDATE OR DELETE ON audit.round3m_reviewer_qualification_receipt
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE VIEW audit.v_round3m_current_reviewer_qualification_receipt AS
SELECT receipt.*
FROM audit.round3m_reviewer_qualification_receipt AS receipt
JOIN evidence.round3m_reviewer_evidence_artifact AS artifact
  ON artifact.reviewer_evidence_artifact_id =
     receipt.qualification_evidence_artifact_id
WHERE receipt.qualification_state_code = 'ACTIVE'
  AND receipt.created_at <= transaction_timestamp()
  AND receipt.valid_from <=
      (transaction_timestamp() AT TIME ZONE 'UTC')::DATE
  AND (
      receipt.valid_to IS NULL
      OR receipt.valid_to >=
         (transaction_timestamp() AT TIME ZONE 'UTC')::DATE
  )
  AND receipt.deterministic_payload_sha256 IS NOT DISTINCT FROM
      audit.round3m_reviewer_qualification_payload_sha256(receipt)
  AND artifact.imported_at <= transaction_timestamp()
  AND artifact.evidence_classification_code IN (
      'ACTUAL_EXTERNAL_HUMAN_DECISION',
      'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_reviewer_qualification_receipt AS successor
      WHERE successor.supersedes_qualification_receipt_id =
            receipt.qualification_receipt_id
  );

CREATE TABLE audit.round3m_reviewer_admission_receipt (
    admission_receipt_id TEXT NOT NULL,
    admission_identity_key TEXT NOT NULL,
    admission_version INTEGER NOT NULL,
    supersedes_admission_receipt_id TEXT,
    reviewer_id BIGINT NOT NULL,
    reviewer_pseudonymous_code TEXT NOT NULL,
    qualification_receipt_id TEXT NOT NULL,
    admitted_reviewer_role TEXT NOT NULL,
    admitted_protocol_version TEXT NOT NULL,
    review_scope_code TEXT NOT NULL,
    review_scope_key TEXT NOT NULL,
    admission_authority TEXT NOT NULL,
    admission_evidence_artifact_id TEXT NOT NULL,
    admission_evidence_locator TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,
    admission_state_code TEXT NOT NULL,
    deterministic_payload_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_reviewer_admission_receipt_pk PRIMARY KEY (
        admission_receipt_id
    ),
    CONSTRAINT round3m_reviewer_admission_identity_version_uq UNIQUE (
        admission_identity_key, admission_version
    ),
    CONSTRAINT round3m_reviewer_admission_natural_version_uq UNIQUE (
        reviewer_id, admitted_reviewer_role,
        admitted_protocol_version, review_scope_code,
        review_scope_key, admission_version
    ),
    CONSTRAINT round3m_reviewer_admission_successor_uq UNIQUE (
        supersedes_admission_receipt_id
    ),
    CONSTRAINT round3m_reviewer_admission_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_admission_qualification_fk FOREIGN KEY (
        qualification_receipt_id
    ) REFERENCES audit.round3m_reviewer_qualification_receipt (
        qualification_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_admission_artifact_fk FOREIGN KEY (
        admission_evidence_artifact_id
    ) REFERENCES evidence.round3m_reviewer_evidence_artifact (
        reviewer_evidence_artifact_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_admission_supersedes_fk FOREIGN KEY (
        supersedes_admission_receipt_id
    ) REFERENCES audit.round3m_reviewer_admission_receipt (
        admission_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_admission_text_ck CHECK (
        admission_receipt_id = lower(btrim(admission_receipt_id))
        AND admission_receipt_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND admission_identity_key = lower(btrim(admission_identity_key))
        AND admission_identity_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND admission_version > 0
        AND (admission_version = 1) =
            (supersedes_admission_receipt_id IS NULL)
        AND reviewer_pseudonymous_code =
            btrim(reviewer_pseudonymous_code)
        AND reviewer_pseudonymous_code <> ''
        AND lower(reviewer_pseudonymous_code)
            !~ '(^|[._ -])codex($|[._ -])'
        AND admitted_protocol_version =
            btrim(admitted_protocol_version)
        AND admitted_protocol_version <> ''
        AND review_scope_key = lower(btrim(review_scope_key))
        AND review_scope_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND admission_authority = btrim(admission_authority)
        AND admission_authority <> ''
        AND lower(admission_authority)
            !~ '(^|[._ /-])codex($|[._ /-])'
        AND admission_evidence_locator =
            btrim(admission_evidence_locator)
        AND admission_evidence_locator <> ''
        AND deterministic_payload_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_reviewer_admission_values_ck CHECK (
        admitted_reviewer_role IN (
            'SOURCE_AUDITOR', 'PROFESSIONAL_SENSORY_REVIEWER',
            'INDEPENDENT_REVIEWER', 'ADJUDICATOR', 'RIGHTS_REVIEWER'
        )
        AND review_scope_code IN (
            'SOURCE_PROVENANCE_REVIEW',
            'DESCRIPTOR_SEGMENTATION_REVIEW',
            'NORMALIZATION_TARGET_REVIEW',
            'SENSORY_ADJUDICATION',
            'RIGHTS_REVIEW'
        )
        AND admission_state_code IN ('ACTIVE', 'REVOKED')
        AND (valid_to IS NULL OR valid_to >= valid_from)
        AND (
            review_scope_code <> 'SENSORY_ADJUDICATION'
            OR admitted_reviewer_role = 'ADJUDICATOR'
        )
    )
);

CREATE FUNCTION audit.round3m_reviewer_admission_payload_sha256(
    receipt_value audit.round3m_reviewer_admission_receipt
)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $round3m_reviewer_admission_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    (to_jsonb(receipt_value) - ARRAY[
        'deterministic_payload_sha256', 'created_at'
    ])::TEXT
)
$round3m_reviewer_admission_payload_sha256$;

CREATE FUNCTION audit.validate_round3m_reviewer_admission_receipt()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_reviewer_admission_receipt$
DECLARE
    reviewer audit.reviewer%ROWTYPE;
    qualification audit.round3m_reviewer_qualification_receipt%ROWTYPE;
    artifact evidence.round3m_reviewer_evidence_artifact%ROWTYPE;
    predecessor audit.round3m_reviewer_admission_receipt%ROWTYPE;
BEGIN
    SELECT * INTO STRICT reviewer
    FROM audit.reviewer
    WHERE reviewer_id = NEW.reviewer_id
    FOR KEY SHARE;

    SELECT * INTO STRICT qualification
    FROM audit.round3m_reviewer_qualification_receipt
    WHERE qualification_receipt_id = NEW.qualification_receipt_id
    FOR KEY SHARE;

    SELECT * INTO STRICT artifact
    FROM evidence.round3m_reviewer_evidence_artifact
    WHERE reviewer_evidence_artifact_id =
          NEW.admission_evidence_artifact_id
    FOR KEY SHARE;

    IF reviewer.reviewer_key IS DISTINCT FROM
           NEW.reviewer_pseudonymous_code
       OR qualification.reviewer_id IS DISTINCT FROM NEW.reviewer_id
       OR qualification.reviewer_pseudonymous_code IS DISTINCT FROM
           NEW.reviewer_pseudonymous_code
       OR qualification.allowed_reviewer_role IS DISTINCT FROM
           NEW.admitted_reviewer_role
       OR qualification.qualification_scope_code IS DISTINCT FROM
           NEW.review_scope_code
       OR qualification.qualification_protocol_version IS DISTINCT FROM
           NEW.admitted_protocol_version
       OR qualification.qualification_state_code <> 'ACTIVE'
       OR EXISTS (
           SELECT 1
           FROM audit.round3m_reviewer_qualification_receipt AS successor
           WHERE successor.supersedes_qualification_receipt_id =
                 qualification.qualification_receipt_id
       )
       OR (NEW.valid_from AT TIME ZONE 'UTC')::DATE <
          qualification.valid_from
       OR qualification.valid_to IS NOT NULL
          AND (NEW.valid_to IS NULL OR
               (NEW.valid_to AT TIME ZONE 'UTC')::DATE >
               qualification.valid_to)
       OR artifact.artifact_purpose_code <>
          'REVIEWER_ADMISSION_AUTHORIZATION'
       OR artifact.evidence_classification_code NOT IN (
           'ACTUAL_EXTERNAL_HUMAN_DECISION',
           'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
       )
       OR artifact.imported_at > NEW.created_at
       OR NEW.created_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewer_admission_evidence_ck',
            MESSAGE = 'admission must bind the exact current qualification, reviewer, role, protocol, scope, validity period, and governed authorization artifact';
    END IF;

    IF NEW.supersedes_admission_receipt_id IS NOT NULL THEN
        SELECT * INTO STRICT predecessor
        FROM audit.round3m_reviewer_admission_receipt
        WHERE admission_receipt_id =
              NEW.supersedes_admission_receipt_id
        FOR UPDATE;

        IF predecessor.admission_identity_key IS DISTINCT FROM
               NEW.admission_identity_key
           OR predecessor.reviewer_id IS DISTINCT FROM NEW.reviewer_id
           OR predecessor.admitted_reviewer_role IS DISTINCT FROM
               NEW.admitted_reviewer_role
           OR predecessor.admitted_protocol_version IS DISTINCT FROM
               NEW.admitted_protocol_version
           OR predecessor.review_scope_code IS DISTINCT FROM
               NEW.review_scope_code
           OR predecessor.review_scope_key IS DISTINCT FROM
               NEW.review_scope_key
           OR predecessor.admission_version + 1 <>
               NEW.admission_version
           OR predecessor.created_at > NEW.created_at THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_reviewer_admission_lineage_ck',
                MESSAGE = 'admission correction must be the next version of the same reviewer, role, protocol, and review scope identity';
        END IF;
    END IF;

    NEW.deterministic_payload_sha256 :=
        audit.round3m_reviewer_admission_payload_sha256(NEW);
    RETURN NEW;
END
$validate_round3m_reviewer_admission_receipt$;

CREATE TRIGGER round3m_reviewer_admission_receipt_bi
BEFORE INSERT ON audit.round3m_reviewer_admission_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_reviewer_admission_receipt();

CREATE TRIGGER round3m_reviewer_admission_receipt_bud
BEFORE UPDATE OR DELETE ON audit.round3m_reviewer_admission_receipt
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE VIEW audit.v_round3m_current_reviewer_admission_receipt AS
SELECT admission.*
FROM audit.round3m_reviewer_admission_receipt AS admission
JOIN audit.v_round3m_current_reviewer_qualification_receipt AS qualification
  ON qualification.qualification_receipt_id =
     admission.qualification_receipt_id
 AND qualification.reviewer_id = admission.reviewer_id
 AND qualification.reviewer_pseudonymous_code =
     admission.reviewer_pseudonymous_code
 AND qualification.allowed_reviewer_role =
     admission.admitted_reviewer_role
 AND qualification.qualification_scope_code = admission.review_scope_code
 AND qualification.qualification_protocol_version =
     admission.admitted_protocol_version
JOIN evidence.round3m_reviewer_evidence_artifact AS artifact
  ON artifact.reviewer_evidence_artifact_id =
     admission.admission_evidence_artifact_id
WHERE admission.admission_state_code = 'ACTIVE'
  AND admission.created_at <= transaction_timestamp()
  AND admission.valid_from <= transaction_timestamp()
  AND (admission.valid_to IS NULL OR admission.valid_to >=
       transaction_timestamp())
  AND admission.deterministic_payload_sha256 IS NOT DISTINCT FROM
      audit.round3m_reviewer_admission_payload_sha256(admission)
  AND artifact.imported_at <= transaction_timestamp()
  AND artifact.evidence_classification_code IN (
      'ACTUAL_EXTERNAL_HUMAN_DECISION',
      'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_reviewer_admission_receipt AS successor
      WHERE successor.supersedes_admission_receipt_id =
            admission.admission_receipt_id
  );

CREATE TABLE audit.round3m_reviewer_decision_evidence (
    reviewer_decision_evidence_id TEXT NOT NULL,
    decision_evidence_identity_key TEXT NOT NULL,
    decision_evidence_version INTEGER NOT NULL,
    supersedes_decision_evidence_id TEXT,
    reviewer_id BIGINT NOT NULL,
    reviewer_pseudonymous_code TEXT NOT NULL,
    decision_target_kind TEXT NOT NULL,
    descriptor_assertion_id BIGINT,
    professional_label_review_id BIGINT,
    review_decision_code TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    reviewer_role TEXT NOT NULL,
    review_protocol_version TEXT NOT NULL,
    review_scope_code TEXT NOT NULL,
    review_scope_key TEXT NOT NULL,
    review_event_timestamp TIMESTAMPTZ NOT NULL,
    source_decision_artifact_id TEXT NOT NULL,
    bounded_decision_locator TEXT NOT NULL,
    source_decision_payload_sha256 TEXT NOT NULL,
    decision_batch_id TEXT,
    evidence_state_code TEXT NOT NULL,
    row_level_evidence BOOLEAN NOT NULL,
    deterministic_payload_sha256 TEXT NOT NULL,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_reviewer_decision_evidence_pk PRIMARY KEY (
        reviewer_decision_evidence_id
    ),
    CONSTRAINT round3m_reviewer_decision_identity_version_uq UNIQUE (
        decision_evidence_identity_key, decision_evidence_version
    ),
    CONSTRAINT round3m_reviewer_decision_natural_version_uq
        UNIQUE NULLS NOT DISTINCT (
            decision_target_kind, descriptor_assertion_id,
            professional_label_review_id, reviewer_id,
            review_protocol_version, decision_evidence_version
        ),
    CONSTRAINT round3m_reviewer_decision_successor_uq UNIQUE (
        supersedes_decision_evidence_id
    ),
    CONSTRAINT round3m_reviewer_decision_artifact_locator_uq UNIQUE (
        source_decision_artifact_id, bounded_decision_locator
    ),
    CONSTRAINT round3m_reviewer_decision_source_payload_uq UNIQUE (
        source_decision_payload_sha256
    ),
    CONSTRAINT round3m_reviewer_decision_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_decision_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_decision_label_review_fk FOREIGN KEY (
        professional_label_review_id
    ) REFERENCES audit.professional_label_review (
        professional_label_review_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_decision_artifact_fk FOREIGN KEY (
        source_decision_artifact_id
    ) REFERENCES evidence.round3m_reviewer_evidence_artifact (
        reviewer_evidence_artifact_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_decision_supersedes_fk FOREIGN KEY (
        supersedes_decision_evidence_id
    ) REFERENCES audit.round3m_reviewer_decision_evidence (
        reviewer_decision_evidence_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_reviewer_decision_text_ck CHECK (
        reviewer_decision_evidence_id =
            lower(btrim(reviewer_decision_evidence_id))
        AND reviewer_decision_evidence_id ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND decision_evidence_identity_key =
            lower(btrim(decision_evidence_identity_key))
        AND decision_evidence_identity_key ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND decision_evidence_version > 0
        AND (decision_evidence_version = 1) =
            (supersedes_decision_evidence_id IS NULL)
        AND reviewer_pseudonymous_code =
            btrim(reviewer_pseudonymous_code)
        AND reviewer_pseudonymous_code <> ''
        AND lower(reviewer_pseudonymous_code)
            !~ '(^|[._ -])codex($|[._ -])'
        AND review_protocol_version = btrim(review_protocol_version)
        AND review_protocol_version <> ''
        AND review_scope_key = lower(btrim(review_scope_key))
        AND review_scope_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND bounded_decision_locator = btrim(bounded_decision_locator)
        AND bounded_decision_locator <> ''
        AND source_decision_payload_sha256 ~ '^[0-9a-f]{64}$'
        AND (
            decision_batch_id IS NULL
            OR decision_batch_id = btrim(decision_batch_id)
               AND decision_batch_id <> ''
        )
        AND deterministic_payload_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_reviewer_decision_values_ck CHECK (
        decision_target_kind IN (
            'ROUND3M_DESCRIPTOR_ASSERTION',
            'PROFESSIONAL_LABEL_REVIEW'
        )
        AND (
            decision_target_kind = 'ROUND3M_DESCRIPTOR_ASSERTION'
            AND descriptor_assertion_id IS NOT NULL
            AND professional_label_review_id IS NULL
            OR decision_target_kind = 'PROFESSIONAL_LABEL_REVIEW'
            AND descriptor_assertion_id IS NULL
            AND professional_label_review_id IS NOT NULL
        )
        AND review_decision_code IN (
            'SOURCE_AUDIT_COMPLETE', 'CONFIRM_DESCRIPTOR',
            'ADJUDICATE_DESCRIPTOR', 'REJECT_NON_DESCRIPTOR',
            'REJECT_DUPLICATE', 'MARK_SOURCE_UNAVAILABLE',
            'MARK_AMBIGUOUS', 'MARK_UNRESOLVED', 'ABSTAIN',
            'RIGHTS_BLOCK', 'ACCEPT', 'REVISE', 'REJECT', 'CONFLICT'
        )
        AND review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
        AND reviewer_role IN (
            'SOURCE_AUDITOR', 'PROFESSIONAL_SENSORY_REVIEWER',
            'INDEPENDENT_REVIEWER', 'ADJUDICATOR', 'RIGHTS_REVIEWER'
        )
        AND review_scope_code IN (
            'SOURCE_PROVENANCE_REVIEW',
            'DESCRIPTOR_SEGMENTATION_REVIEW',
            'NORMALIZATION_TARGET_REVIEW',
            'SENSORY_ADJUDICATION',
            'RIGHTS_REVIEW'
        )
        AND evidence_state_code IN ('ACTIVE', 'REVOKED')
        AND row_level_evidence
        AND (
            review_actor_type <> 'EXPERT_REVIEWER'
            OR reviewer_role = 'ADJUDICATOR'
               AND review_scope_code = 'SENSORY_ADJUDICATION'
               AND review_decision_code IN (
                   'ADJUDICATE_DESCRIPTOR', 'ACCEPT', 'REVISE',
                   'REJECT', 'CONFLICT', 'ABSTAIN'
               )
        )
    )
);

CREATE FUNCTION audit.round3m_reviewer_decision_payload_sha256(
    evidence_value audit.round3m_reviewer_decision_evidence
)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $round3m_reviewer_decision_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    (to_jsonb(evidence_value) - ARRAY[
        'deterministic_payload_sha256', 'imported_at'
    ])::TEXT
)
$round3m_reviewer_decision_payload_sha256$;

CREATE FUNCTION audit.validate_round3m_reviewer_decision_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_reviewer_decision_evidence$
DECLARE
    reviewer audit.reviewer%ROWTYPE;
    artifact evidence.round3m_reviewer_evidence_artifact%ROWTYPE;
    label_review audit.professional_label_review%ROWTYPE;
    predecessor audit.round3m_reviewer_decision_evidence%ROWTYPE;
    expected_role TEXT;
    expected_actor TEXT;
    expected_scope TEXT;
BEGIN
    SELECT * INTO STRICT reviewer
    FROM audit.reviewer
    WHERE reviewer_id = NEW.reviewer_id
    FOR KEY SHARE;

    SELECT * INTO STRICT artifact
    FROM evidence.round3m_reviewer_evidence_artifact
    WHERE reviewer_evidence_artifact_id =
          NEW.source_decision_artifact_id
    FOR KEY SHARE;

    IF reviewer.reviewer_key IS DISTINCT FROM
           NEW.reviewer_pseudonymous_code
       OR artifact.artifact_purpose_code <>
          'ROW_LEVEL_REVIEWER_DECISION_EXPORT'
       OR artifact.evidence_classification_code NOT IN (
           'ACTUAL_EXTERNAL_HUMAN_DECISION',
           'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
       )
       OR artifact.imported_at > NEW.imported_at
       OR NEW.review_event_timestamp > NEW.imported_at
       OR NEW.imported_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewer_decision_artifact_binding_ck',
            MESSAGE = 'row-level decision evidence must bind the exact reviewer and a governed bounded decision artifact imported no later than the evidence row';
    END IF;

    IF NEW.decision_target_kind = 'PROFESSIONAL_LABEL_REVIEW' THEN
        SELECT * INTO STRICT label_review
        FROM audit.professional_label_review
        WHERE professional_label_review_id =
              NEW.professional_label_review_id
        FOR KEY SHARE;

        expected_role := CASE label_review.reviewer_role_code
            WHEN 'INDEPENDENT_REVIEWER' THEN 'INDEPENDENT_REVIEWER'
            WHEN 'ADJUDICATOR' THEN 'ADJUDICATOR'
        END;
        expected_actor := CASE label_review.reviewer_role_code
            WHEN 'INDEPENDENT_REVIEWER' THEN 'HUMAN_REVIEWER'
            WHEN 'ADJUDICATOR' THEN 'EXPERT_REVIEWER'
        END;
        expected_scope := CASE label_review.reviewer_role_code
            WHEN 'INDEPENDENT_REVIEWER' THEN
                'NORMALIZATION_TARGET_REVIEW'
            WHEN 'ADJUDICATOR' THEN 'SENSORY_ADJUDICATION'
        END;

        IF label_review.reviewer_id IS DISTINCT FROM NEW.reviewer_id
           OR label_review.review_outcome_code IS DISTINCT FROM
              NEW.review_decision_code
           OR label_review.reviewed_at IS DISTINCT FROM
              NEW.review_event_timestamp
           OR NEW.reviewer_role IS DISTINCT FROM expected_role
           OR NEW.review_actor_type IS DISTINCT FROM expected_actor
           OR NEW.review_scope_code IS DISTINCT FROM expected_scope THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_reviewer_decision_label_review_ck',
                MESSAGE = 'professional-label decision evidence must exactly match its reviewer, outcome, event time, role, and proportional scope';
        END IF;
    END IF;

    IF NEW.supersedes_decision_evidence_id IS NOT NULL THEN
        SELECT * INTO STRICT predecessor
        FROM audit.round3m_reviewer_decision_evidence
        WHERE reviewer_decision_evidence_id =
              NEW.supersedes_decision_evidence_id
        FOR UPDATE;

        IF predecessor.decision_evidence_identity_key IS DISTINCT FROM
               NEW.decision_evidence_identity_key
           OR predecessor.reviewer_id IS DISTINCT FROM NEW.reviewer_id
           OR predecessor.decision_target_kind IS DISTINCT FROM
               NEW.decision_target_kind
           OR predecessor.descriptor_assertion_id IS DISTINCT FROM
               NEW.descriptor_assertion_id
           OR predecessor.professional_label_review_id IS DISTINCT FROM
               NEW.professional_label_review_id
           OR predecessor.review_protocol_version IS DISTINCT FROM
               NEW.review_protocol_version
           OR predecessor.review_scope_code IS DISTINCT FROM
               NEW.review_scope_code
           OR predecessor.review_scope_key IS DISTINCT FROM
               NEW.review_scope_key
           OR predecessor.decision_evidence_version + 1 <>
               NEW.decision_evidence_version
           OR predecessor.review_event_timestamp >
              NEW.review_event_timestamp
           OR predecessor.imported_at > NEW.imported_at THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_reviewer_decision_lineage_ck',
                MESSAGE = 'decision-evidence correction must be the next version of the same reviewer, target, protocol, and review-scope identity';
        END IF;
    END IF;

    NEW.deterministic_payload_sha256 :=
        audit.round3m_reviewer_decision_payload_sha256(NEW);
    RETURN NEW;
END
$validate_round3m_reviewer_decision_evidence$;

CREATE TRIGGER round3m_reviewer_decision_evidence_bi
BEFORE INSERT ON audit.round3m_reviewer_decision_evidence
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_reviewer_decision_evidence();

CREATE TRIGGER round3m_reviewer_decision_evidence_bud
BEFORE UPDATE OR DELETE ON audit.round3m_reviewer_decision_evidence
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE VIEW audit.v_round3m_current_reviewer_decision_evidence AS
SELECT decision.*
FROM audit.round3m_reviewer_decision_evidence AS decision
JOIN evidence.round3m_reviewer_evidence_artifact AS artifact
  ON artifact.reviewer_evidence_artifact_id =
     decision.source_decision_artifact_id
WHERE decision.evidence_state_code = 'ACTIVE'
  AND decision.row_level_evidence
  AND decision.review_event_timestamp <= decision.imported_at
  AND decision.imported_at <= transaction_timestamp()
  AND decision.deterministic_payload_sha256 IS NOT DISTINCT FROM
      audit.round3m_reviewer_decision_payload_sha256(decision)
  AND artifact.artifact_purpose_code =
      'ROW_LEVEL_REVIEWER_DECISION_EXPORT'
  AND artifact.evidence_classification_code IN (
      'ACTUAL_EXTERNAL_HUMAN_DECISION',
      'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
  )
  AND artifact.imported_at <= transaction_timestamp()
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_reviewer_decision_evidence AS successor
      WHERE successor.supersedes_decision_evidence_id =
            decision.reviewer_decision_evidence_id
  );

ALTER TABLE audit.round3m_descriptor_review_receipt
    ADD COLUMN qualification_receipt_id TEXT,
    ADD COLUMN admission_receipt_id TEXT,
    ADD COLUMN reviewer_decision_evidence_id TEXT,
    ADD COLUMN reviewer_decision_artifact_id TEXT,
    ADD CONSTRAINT round3m_descriptor_review_qualification_fk
        FOREIGN KEY (qualification_receipt_id)
        REFERENCES audit.round3m_reviewer_qualification_receipt (
            qualification_receipt_id
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_descriptor_review_admission_fk
        FOREIGN KEY (admission_receipt_id)
        REFERENCES audit.round3m_reviewer_admission_receipt (
            admission_receipt_id
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_descriptor_review_decision_evidence_fk
        FOREIGN KEY (reviewer_decision_evidence_id)
        REFERENCES audit.round3m_reviewer_decision_evidence (
            reviewer_decision_evidence_id
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_descriptor_review_decision_artifact_fk
        FOREIGN KEY (reviewer_decision_artifact_id)
        REFERENCES evidence.round3m_reviewer_evidence_artifact (
            reviewer_evidence_artifact_id
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_descriptor_review_decision_evidence_uq UNIQUE (
        reviewer_decision_evidence_id
    ),
    ADD CONSTRAINT round3m_descriptor_review_full_chain_shape_ck CHECK (
        review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
        AND reviewer_id IS NOT NULL
        AND qualification_receipt_id IS NOT NULL
        AND admission_receipt_id IS NOT NULL
        AND reviewer_decision_evidence_id IS NOT NULL
        AND reviewer_decision_artifact_id IS NOT NULL
        OR review_actor_type NOT IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
        AND qualification_receipt_id IS NULL
        AND admission_receipt_id IS NULL
        AND reviewer_decision_evidence_id IS NULL
        AND reviewer_decision_artifact_id IS NULL
    );

CREATE FUNCTION audit.round3m_expected_descriptor_review_scope(
    decision_value TEXT,
    actor_type_value TEXT,
    reviewer_role_value TEXT
)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $round3m_expected_descriptor_review_scope$
SELECT CASE
    WHEN actor_type_value = 'EXPERT_REVIEWER'
      OR decision_value = 'ADJUDICATE_DESCRIPTOR'
      OR reviewer_role_value = 'ADJUDICATOR'
        THEN 'SENSORY_ADJUDICATION'
    WHEN decision_value IN ('MARK_AMBIGUOUS', 'MARK_UNRESOLVED')
        THEN 'NORMALIZATION_TARGET_REVIEW'
    WHEN decision_value = 'CONFIRM_DESCRIPTOR'
        THEN 'DESCRIPTOR_SEGMENTATION_REVIEW'
    WHEN decision_value = 'RIGHTS_BLOCK'
      OR reviewer_role_value = 'RIGHTS_REVIEWER'
        THEN 'RIGHTS_REVIEW'
    ELSE 'SOURCE_PROVENANCE_REVIEW'
END
$round3m_expected_descriptor_review_scope$;

CREATE FUNCTION audit.validate_round3m_descriptor_review_full_chain()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_review_full_chain$
DECLARE
    reviewer audit.reviewer%ROWTYPE;
    qualification audit.round3m_reviewer_qualification_receipt%ROWTYPE;
    admission audit.round3m_reviewer_admission_receipt%ROWTYPE;
    decision_evidence audit.round3m_reviewer_decision_evidence%ROWTYPE;
    expected_scope TEXT;
BEGIN
    IF NEW.review_actor_type NOT IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER') THEN
        IF NEW.qualification_receipt_id IS NOT NULL
           OR NEW.admission_receipt_id IS NOT NULL
           OR NEW.reviewer_decision_evidence_id IS NOT NULL
           OR NEW.reviewer_decision_artifact_id IS NOT NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_nonhuman_review_chain_null_ck',
                MESSAGE = 'non-human review actors cannot carry human qualification, admission, or decision-evidence references';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.reviewer_id IS NULL
       OR NEW.qualification_receipt_id IS NULL
       OR NEW.admission_receipt_id IS NULL
       OR NEW.reviewer_decision_evidence_id IS NULL
       OR NEW.reviewer_decision_artifact_id IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_human_review_full_chain_required_ck',
            MESSAGE = 'human and expert receipts require qualification, admission, and row-level reviewer-decision evidence';
    END IF;

    SELECT * INTO STRICT reviewer
    FROM audit.reviewer
    WHERE reviewer_id = NEW.reviewer_id
    FOR KEY SHARE;

    SELECT * INTO STRICT qualification
    FROM audit.round3m_reviewer_qualification_receipt
    WHERE qualification_receipt_id = NEW.qualification_receipt_id
    FOR KEY SHARE;

    SELECT * INTO STRICT admission
    FROM audit.round3m_reviewer_admission_receipt
    WHERE admission_receipt_id = NEW.admission_receipt_id
    FOR KEY SHARE;

    SELECT * INTO STRICT decision_evidence
    FROM audit.round3m_reviewer_decision_evidence
    WHERE reviewer_decision_evidence_id =
          NEW.reviewer_decision_evidence_id
    FOR KEY SHARE;

    expected_scope := audit.round3m_expected_descriptor_review_scope(
        NEW.decision, NEW.review_actor_type, NEW.reviewer_role
    );

    IF reviewer.reviewer_key IS DISTINCT FROM
           NEW.reviewer_id_or_pseudonymous_code
       OR qualification.reviewer_id IS DISTINCT FROM NEW.reviewer_id
       OR qualification.reviewer_pseudonymous_code IS DISTINCT FROM
           NEW.reviewer_id_or_pseudonymous_code
       OR qualification.allowed_reviewer_role IS DISTINCT FROM
           NEW.reviewer_role
       OR qualification.qualification_scope_code IS DISTINCT FROM
           expected_scope
       OR qualification.qualification_protocol_version IS DISTINCT FROM
           NEW.review_protocol_version
       OR qualification.qualification_state_code <> 'ACTIVE'
       OR qualification.valid_from >
          (NEW.reviewed_at AT TIME ZONE 'UTC')::DATE
       OR qualification.valid_to IS NOT NULL
          AND qualification.valid_to <
              (NEW.reviewed_at AT TIME ZONE 'UTC')::DATE
       OR EXISTS (
           SELECT 1
           FROM audit.round3m_reviewer_qualification_receipt AS successor
           WHERE successor.supersedes_qualification_receipt_id =
                 qualification.qualification_receipt_id
       )
       OR NOT EXISTS (
           SELECT 1
           FROM audit.v_round3m_current_reviewer_qualification_receipt
           WHERE qualification_receipt_id =
                 qualification.qualification_receipt_id
       )
       OR admission.reviewer_id IS DISTINCT FROM NEW.reviewer_id
       OR admission.reviewer_pseudonymous_code IS DISTINCT FROM
           NEW.reviewer_id_or_pseudonymous_code
       OR admission.qualification_receipt_id IS DISTINCT FROM
           qualification.qualification_receipt_id
       OR admission.admitted_reviewer_role IS DISTINCT FROM
           NEW.reviewer_role
       OR admission.admitted_protocol_version IS DISTINCT FROM
           NEW.review_protocol_version
       OR admission.review_scope_code IS DISTINCT FROM expected_scope
       OR admission.admission_state_code <> 'ACTIVE'
       OR admission.valid_from > NEW.reviewed_at
       OR admission.valid_to IS NOT NULL
          AND admission.valid_to < NEW.reviewed_at
       OR EXISTS (
           SELECT 1
           FROM audit.round3m_reviewer_admission_receipt AS successor
           WHERE successor.supersedes_admission_receipt_id =
                 admission.admission_receipt_id
       )
       OR NOT EXISTS (
           SELECT 1
           FROM audit.v_round3m_current_reviewer_admission_receipt
           WHERE admission_receipt_id = admission.admission_receipt_id
       )
       OR decision_evidence.decision_target_kind <>
          'ROUND3M_DESCRIPTOR_ASSERTION'
       OR decision_evidence.descriptor_assertion_id IS DISTINCT FROM
           NEW.descriptor_assertion_id
       OR decision_evidence.reviewer_id IS DISTINCT FROM NEW.reviewer_id
       OR decision_evidence.reviewer_pseudonymous_code IS DISTINCT FROM
           NEW.reviewer_id_or_pseudonymous_code
       OR decision_evidence.review_decision_code IS DISTINCT FROM
           NEW.decision
       OR decision_evidence.review_actor_type IS DISTINCT FROM
           NEW.review_actor_type
       OR decision_evidence.reviewer_role IS DISTINCT FROM
           NEW.reviewer_role
       OR decision_evidence.review_protocol_version IS DISTINCT FROM
           NEW.review_protocol_version
       OR decision_evidence.review_scope_code IS DISTINCT FROM
           expected_scope
       OR decision_evidence.review_scope_key IS DISTINCT FROM
           admission.review_scope_key
       OR decision_evidence.review_event_timestamp IS DISTINCT FROM
           NEW.reviewed_at
       OR decision_evidence.bounded_decision_locator IS DISTINCT FROM
           NEW.evidence_locator
       OR decision_evidence.source_decision_artifact_id IS DISTINCT FROM
           NEW.reviewer_decision_artifact_id
       OR decision_evidence.source_decision_payload_sha256 IS DISTINCT FROM
           NEW.human_event_evidence_sha256
       OR decision_evidence.evidence_state_code <> 'ACTIVE'
       OR NOT decision_evidence.row_level_evidence
       OR EXISTS (
           SELECT 1
           FROM audit.round3m_reviewer_decision_evidence AS successor
           WHERE successor.supersedes_decision_evidence_id =
                 decision_evidence.reviewer_decision_evidence_id
       )
       OR NOT EXISTS (
           SELECT 1
           FROM audit.v_round3m_current_reviewer_decision_evidence
           WHERE reviewer_decision_evidence_id =
                 decision_evidence.reviewer_decision_evidence_id
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_full_chain_exact_ck',
            MESSAGE = 'human review receipt must exactly match the current qualification, admission, and bounded row-level decision evidence chain';
    END IF;

    IF NEW.review_actor_type = 'EXPERT_REVIEWER'
       AND (
           expected_scope <> 'SENSORY_ADJUDICATION'
           OR qualification.qualification_level_code <> 'EXPERT'
           OR NEW.reviewer_role <> 'ADJUDICATOR'
           OR NEW.decision <> 'ADJUDICATE_DESCRIPTOR'
           OR NEW.adjudication_status <> 'FINAL'
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_expert_adjudication_full_chain_ck',
            MESSAGE = 'expert adjudication requires expert sensory scope, adjudicator admission, ADJUDICATE_DESCRIPTOR, and FINAL status';
    END IF;

    RETURN NEW;
END
$validate_round3m_descriptor_review_full_chain$;

CREATE TRIGGER round3m_058_descriptor_review_full_chain_bi
BEFORE INSERT ON audit.round3m_descriptor_review_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_descriptor_review_full_chain();

CREATE OR REPLACE FUNCTION audit.validate_round3m_expert_review_qualification()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_expert_review_qualification$
BEGIN
    IF NEW.review_actor_type = 'EXPERT_REVIEWER'
       AND NOT EXISTS (
           SELECT 1
           FROM audit.v_round3m_current_reviewer_qualification_receipt AS qualification
           JOIN audit.v_round3m_current_reviewer_admission_receipt AS admission
             ON admission.qualification_receipt_id =
                qualification.qualification_receipt_id
            AND admission.admission_receipt_id = NEW.admission_receipt_id
           WHERE qualification.qualification_receipt_id =
                 NEW.qualification_receipt_id
             AND qualification.reviewer_id = NEW.reviewer_id
             AND qualification.qualification_scope_code =
                 'SENSORY_ADJUDICATION'
             AND qualification.allowed_reviewer_role = 'ADJUDICATOR'
             AND qualification.qualification_level_code = 'EXPERT'
             AND admission.admitted_reviewer_role = 'ADJUDICATOR'
             AND admission.review_scope_code = 'SENSORY_ADJUDICATION'
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_expert_review_qualification_ck',
            MESSAGE = 'expert adjudication requires a current 058 expert-sensory qualification and matching adjudicator admission';
    END IF;
    RETURN NEW;
END
$validate_round3m_expert_review_qualification$;

CREATE FUNCTION audit.round3m_descriptor_review_receipt_has_full_evidence(
    review_receipt_id_value BIGINT,
    reverify_immutable_payload_hashes BOOLEAN DEFAULT TRUE
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_descriptor_review_receipt_has_full_evidence$
SELECT EXISTS (
    SELECT 1
    FROM audit.round3m_descriptor_review_receipt AS receipt
    JOIN audit.round3m_reviewer_qualification_receipt AS qualification
      ON qualification.qualification_receipt_id =
         receipt.qualification_receipt_id
     AND qualification.reviewer_id = receipt.reviewer_id
     AND qualification.reviewer_pseudonymous_code =
         receipt.reviewer_id_or_pseudonymous_code
     AND qualification.allowed_reviewer_role = receipt.reviewer_role
     AND qualification.qualification_protocol_version =
         receipt.review_protocol_version
    JOIN evidence.round3m_reviewer_evidence_artifact AS
         qualification_artifact
      ON qualification_artifact.reviewer_evidence_artifact_id =
         qualification.qualification_evidence_artifact_id
    JOIN audit.round3m_reviewer_admission_receipt AS admission
      ON admission.admission_receipt_id = receipt.admission_receipt_id
     AND admission.qualification_receipt_id =
         qualification.qualification_receipt_id
     AND admission.reviewer_id = receipt.reviewer_id
     AND admission.reviewer_pseudonymous_code =
         receipt.reviewer_id_or_pseudonymous_code
     AND admission.admitted_reviewer_role = receipt.reviewer_role
     AND admission.admitted_protocol_version =
         receipt.review_protocol_version
     AND admission.review_scope_code =
         audit.round3m_expected_descriptor_review_scope(
             receipt.decision, receipt.review_actor_type,
             receipt.reviewer_role
         )
     AND admission.valid_from <= receipt.reviewed_at
     AND (admission.valid_to IS NULL OR
          admission.valid_to >= receipt.reviewed_at)
    JOIN evidence.round3m_reviewer_evidence_artifact AS admission_artifact
      ON admission_artifact.reviewer_evidence_artifact_id =
         admission.admission_evidence_artifact_id
    JOIN audit.round3m_reviewer_decision_evidence AS decision_evidence
      ON decision_evidence.reviewer_decision_evidence_id =
         receipt.reviewer_decision_evidence_id
     AND decision_evidence.decision_target_kind =
         'ROUND3M_DESCRIPTOR_ASSERTION'
     AND decision_evidence.descriptor_assertion_id =
         receipt.descriptor_assertion_id
     AND decision_evidence.reviewer_id = receipt.reviewer_id
     AND decision_evidence.reviewer_pseudonymous_code =
         receipt.reviewer_id_or_pseudonymous_code
     AND decision_evidence.review_decision_code = receipt.decision
     AND decision_evidence.review_actor_type = receipt.review_actor_type
     AND decision_evidence.reviewer_role = receipt.reviewer_role
     AND decision_evidence.review_protocol_version =
         receipt.review_protocol_version
     AND decision_evidence.review_scope_code = admission.review_scope_code
     AND decision_evidence.review_scope_key = admission.review_scope_key
     AND decision_evidence.review_event_timestamp = receipt.reviewed_at
     AND decision_evidence.bounded_decision_locator =
         receipt.evidence_locator
     AND decision_evidence.source_decision_artifact_id =
         receipt.reviewer_decision_artifact_id
     AND decision_evidence.source_decision_payload_sha256 =
         receipt.human_event_evidence_sha256
    JOIN evidence.round3m_reviewer_evidence_artifact AS decision_artifact
      ON decision_artifact.reviewer_evidence_artifact_id =
         decision_evidence.source_decision_artifact_id
    WHERE receipt.review_receipt_id = review_receipt_id_value
      AND receipt.review_actor_type IN (
          'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
      )
      AND receipt.receipt_origin_code IN (
          'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
      )
      AND receipt.reviewed_at <= receipt.created_at
      AND receipt.created_at <= transaction_timestamp()
      AND qualification.valid_from <=
          (receipt.reviewed_at AT TIME ZONE 'UTC')::DATE
      AND (qualification.valid_to IS NULL OR
           qualification.valid_to >=
           (receipt.reviewed_at AT TIME ZONE 'UTC')::DATE)
      AND qualification.qualification_state_code = 'ACTIVE'
      AND qualification.created_at <= transaction_timestamp()
      AND qualification.valid_from <=
          (transaction_timestamp() AT TIME ZONE 'UTC')::DATE
      AND (qualification.valid_to IS NULL OR
           qualification.valid_to >=
           (transaction_timestamp() AT TIME ZONE 'UTC')::DATE)
      AND (
          NOT reverify_immutable_payload_hashes
          OR qualification.deterministic_payload_sha256 IS NOT DISTINCT FROM
             audit.round3m_reviewer_qualification_payload_sha256(
                 qualification
             )
      )
      AND qualification.qualification_scope_code =
          audit.round3m_expected_descriptor_review_scope(
              receipt.decision, receipt.review_actor_type,
              receipt.reviewer_role
          )
      AND qualification_artifact.artifact_purpose_code IN (
          'REVIEWER_QUALIFICATION_EVIDENCE',
          'PROTOCOL_TRAINING_ACKNOWLEDGEMENT'
      )
      AND qualification_artifact.evidence_classification_code IN (
          'ACTUAL_EXTERNAL_HUMAN_DECISION',
          'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
      )
      AND qualification_artifact.imported_at <= transaction_timestamp()
      AND NOT EXISTS (
          SELECT 1
          FROM audit.round3m_reviewer_qualification_receipt AS successor
          WHERE successor.supersedes_qualification_receipt_id =
                qualification.qualification_receipt_id
      )
      AND admission.admission_state_code = 'ACTIVE'
      AND admission.created_at <= transaction_timestamp()
      AND admission.valid_from <= transaction_timestamp()
      AND (admission.valid_to IS NULL OR
           admission.valid_to >= transaction_timestamp())
      AND (
          NOT reverify_immutable_payload_hashes
          OR admission.deterministic_payload_sha256 IS NOT DISTINCT FROM
             audit.round3m_reviewer_admission_payload_sha256(admission)
      )
      AND admission_artifact.artifact_purpose_code =
          'REVIEWER_ADMISSION_AUTHORIZATION'
      AND admission_artifact.evidence_classification_code IN (
          'ACTUAL_EXTERNAL_HUMAN_DECISION',
          'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
      )
      AND admission_artifact.imported_at <= transaction_timestamp()
      AND NOT EXISTS (
          SELECT 1
          FROM audit.round3m_reviewer_admission_receipt AS successor
          WHERE successor.supersedes_admission_receipt_id =
                admission.admission_receipt_id
      )
      AND decision_evidence.evidence_state_code = 'ACTIVE'
      AND decision_evidence.row_level_evidence
      AND decision_evidence.review_event_timestamp <=
          decision_evidence.imported_at
      AND decision_evidence.imported_at <= transaction_timestamp()
      AND (
          NOT reverify_immutable_payload_hashes
          OR decision_evidence.deterministic_payload_sha256 IS NOT DISTINCT
             FROM audit.round3m_reviewer_decision_payload_sha256(
                 decision_evidence
             )
      )
      AND decision_artifact.artifact_purpose_code =
          'ROW_LEVEL_REVIEWER_DECISION_EXPORT'
      AND decision_artifact.evidence_classification_code IN (
          'ACTUAL_EXTERNAL_HUMAN_DECISION',
          'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
      )
      AND decision_artifact.imported_at <= transaction_timestamp()
      AND NOT EXISTS (
          SELECT 1
          FROM audit.round3m_reviewer_decision_evidence AS successor
          WHERE successor.supersedes_decision_evidence_id =
                decision_evidence.reviewer_decision_evidence_id
      )
)
$round3m_descriptor_review_receipt_has_full_evidence$;

COMMENT ON FUNCTION
    audit.round3m_descriptor_review_receipt_has_full_evidence(BIGINT, BOOLEAN)
IS 'Verifies the complete 058 qualification, admission, and row-level decision-evidence chain. Operational current views may skip repeated payload-hash recomputation because insert triggers validated the hashes and ordinary UPDATE/DELETE is rejected; authoritative validation calls retain the default full hash recheck. Superuser or DDL-owner bypass remains outside the database-enforced threat model and is detected by full validation/manifests.';

CREATE FUNCTION audit.round3m_descriptor_assertion_source_payload_sha256(
    descriptor_assertion_id_value BIGINT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_descriptor_assertion_source_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    (to_jsonb(assertion) - ARRAY[
        'review_state', 'review_actor_type',
        'current_review_receipt_id'
    ])::TEXT
)
FROM corpus.round3m_descriptor_assertion AS assertion
WHERE assertion.descriptor_assertion_id = descriptor_assertion_id_value
$round3m_descriptor_assertion_source_payload_sha256$;

CREATE FUNCTION audit.round3m_descriptor_review_chain_payload_sha256(
    review_receipt_id_value BIGINT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_descriptor_review_chain_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    jsonb_build_object(
        'review_receipt', to_jsonb(receipt) - 'created_at',
        'qualification_payload_sha256',
            qualification.deterministic_payload_sha256,
        'admission_payload_sha256',
            admission.deterministic_payload_sha256,
        'decision_evidence_payload_sha256',
            decision_evidence.deterministic_payload_sha256
    )::TEXT
)
FROM audit.round3m_descriptor_review_receipt AS receipt
JOIN audit.round3m_reviewer_qualification_receipt AS qualification
  ON qualification.qualification_receipt_id =
     receipt.qualification_receipt_id
JOIN audit.round3m_reviewer_admission_receipt AS admission
  ON admission.admission_receipt_id = receipt.admission_receipt_id
JOIN audit.round3m_reviewer_decision_evidence AS decision_evidence
  ON decision_evidence.reviewer_decision_evidence_id =
     receipt.reviewer_decision_evidence_id
WHERE receipt.review_receipt_id = review_receipt_id_value
$round3m_descriptor_review_chain_payload_sha256$;

CREATE TABLE audit.round3m_reviewed_assertion_admission_snapshot (
    assertion_admission_snapshot_id TEXT NOT NULL,
    assertion_admission_identity_key TEXT NOT NULL,
    snapshot_version INTEGER NOT NULL,
    supersedes_assertion_admission_snapshot_id TEXT,
    descriptor_assertion_id BIGINT NOT NULL,
    review_receipt_id BIGINT NOT NULL,
    qualification_receipt_id TEXT NOT NULL,
    admission_receipt_id TEXT NOT NULL,
    reviewer_decision_evidence_id TEXT NOT NULL,
    assertion_source_payload_sha256 TEXT NOT NULL,
    review_chain_payload_sha256 TEXT NOT NULL,
    admission_state_code TEXT NOT NULL,
    deterministic_payload_sha256 TEXT NOT NULL,
    admitted_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_reviewed_assertion_admission_snapshot_pk PRIMARY KEY (
        assertion_admission_snapshot_id
    ),
    CONSTRAINT round3m_assertion_admission_identity_version_uq UNIQUE (
        assertion_admission_identity_key, snapshot_version
    ),
    CONSTRAINT round3m_assertion_admission_review_uq UNIQUE (
        review_receipt_id
    ),
    CONSTRAINT round3m_assertion_admission_successor_uq UNIQUE (
        supersedes_assertion_admission_snapshot_id
    ),
    CONSTRAINT round3m_assertion_admission_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_assertion_admission_review_fk FOREIGN KEY (
        review_receipt_id
    ) REFERENCES audit.round3m_descriptor_review_receipt (
        review_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_assertion_admission_qualification_fk FOREIGN KEY (
        qualification_receipt_id
    ) REFERENCES audit.round3m_reviewer_qualification_receipt (
        qualification_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_assertion_admission_admission_fk FOREIGN KEY (
        admission_receipt_id
    ) REFERENCES audit.round3m_reviewer_admission_receipt (
        admission_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_assertion_admission_decision_evidence_fk FOREIGN KEY (
        reviewer_decision_evidence_id
    ) REFERENCES audit.round3m_reviewer_decision_evidence (
        reviewer_decision_evidence_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_assertion_admission_supersedes_fk FOREIGN KEY (
        supersedes_assertion_admission_snapshot_id
    ) REFERENCES audit.round3m_reviewed_assertion_admission_snapshot (
        assertion_admission_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_assertion_admission_text_ck CHECK (
        assertion_admission_snapshot_id =
            lower(btrim(assertion_admission_snapshot_id))
        AND assertion_admission_snapshot_id ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND assertion_admission_identity_key =
            lower(btrim(assertion_admission_identity_key))
        AND assertion_admission_identity_key ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND snapshot_version > 0
        AND (snapshot_version = 1) =
            (supersedes_assertion_admission_snapshot_id IS NULL)
        AND assertion_source_payload_sha256 ~ '^[0-9a-f]{64}$'
        AND review_chain_payload_sha256 ~ '^[0-9a-f]{64}$'
        AND deterministic_payload_sha256 ~ '^[0-9a-f]{64}$'
        AND admission_state_code IN ('ADMITTED', 'REVOKED')
    )
);

CREATE FUNCTION audit.round3m_assertion_admission_payload_sha256(
    snapshot_value audit.round3m_reviewed_assertion_admission_snapshot
)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $round3m_assertion_admission_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    (to_jsonb(snapshot_value) - ARRAY[
        'deterministic_payload_sha256', 'admitted_at'
    ])::TEXT
)
$round3m_assertion_admission_payload_sha256$;

CREATE FUNCTION audit.validate_round3m_assertion_admission_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_assertion_admission_snapshot$
DECLARE
    receipt audit.round3m_descriptor_review_receipt%ROWTYPE;
    predecessor audit.round3m_reviewed_assertion_admission_snapshot%ROWTYPE;
BEGIN
    SELECT * INTO STRICT receipt
    FROM audit.round3m_descriptor_review_receipt
    WHERE review_receipt_id = NEW.review_receipt_id
    FOR KEY SHARE;

    IF receipt.descriptor_assertion_id IS DISTINCT FROM
           NEW.descriptor_assertion_id
       OR receipt.qualification_receipt_id IS DISTINCT FROM
           NEW.qualification_receipt_id
       OR receipt.admission_receipt_id IS DISTINCT FROM
           NEW.admission_receipt_id
       OR receipt.reviewer_decision_evidence_id IS DISTINCT FROM
           NEW.reviewer_decision_evidence_id
       OR NOT audit.round3m_descriptor_review_receipt_has_full_evidence(
           receipt.review_receipt_id
       )
       OR NEW.assertion_source_payload_sha256 IS DISTINCT FROM
          audit.round3m_descriptor_assertion_source_payload_sha256(
              NEW.descriptor_assertion_id
          )
       OR NEW.review_chain_payload_sha256 IS DISTINCT FROM
          audit.round3m_descriptor_review_chain_payload_sha256(
              NEW.review_receipt_id
          )
       OR NEW.admitted_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_assertion_admission_exact_snapshot_ck',
            MESSAGE = 'admitted assertion snapshot must bind the exact source payload and full current 058 review-evidence chain';
    END IF;

    IF NEW.supersedes_assertion_admission_snapshot_id IS NOT NULL THEN
        SELECT * INTO STRICT predecessor
        FROM audit.round3m_reviewed_assertion_admission_snapshot
        WHERE assertion_admission_snapshot_id =
              NEW.supersedes_assertion_admission_snapshot_id
        FOR UPDATE;

        IF predecessor.assertion_admission_identity_key IS DISTINCT FROM
               NEW.assertion_admission_identity_key
           OR predecessor.snapshot_version + 1 <> NEW.snapshot_version
           OR predecessor.admitted_at > NEW.admitted_at THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_assertion_admission_lineage_ck',
                MESSAGE = 'assertion-admission correction must be the next version of the same governed snapshot identity';
        END IF;
    END IF;

    NEW.deterministic_payload_sha256 :=
        audit.round3m_assertion_admission_payload_sha256(NEW);
    RETURN NEW;
END
$validate_round3m_assertion_admission_snapshot$;

CREATE TRIGGER round3m_assertion_admission_snapshot_bi
BEFORE INSERT ON audit.round3m_reviewed_assertion_admission_snapshot
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_assertion_admission_snapshot();

CREATE TRIGGER round3m_assertion_admission_snapshot_bud
BEFORE UPDATE OR DELETE ON audit.round3m_reviewed_assertion_admission_snapshot
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE FUNCTION audit.capture_round3m_assertion_admission_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $capture_round3m_assertion_admission_snapshot$
DECLARE
    predecessor_snapshot
        audit.round3m_reviewed_assertion_admission_snapshot%ROWTYPE;
    next_snapshot_version INTEGER := 1;
BEGIN
    IF NEW.review_actor_type NOT IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER') THEN
        RETURN NEW;
    END IF;

    IF NEW.supersedes_review_receipt_id IS NOT NULL THEN
        SELECT snapshot.* INTO predecessor_snapshot
        FROM audit.round3m_reviewed_assertion_admission_snapshot AS snapshot
        WHERE snapshot.review_receipt_id =
              NEW.supersedes_review_receipt_id;

        IF predecessor_snapshot.assertion_admission_snapshot_id IS NOT NULL
        THEN
            next_snapshot_version := predecessor_snapshot.snapshot_version + 1;
        END IF;
    END IF;

    INSERT INTO audit.round3m_reviewed_assertion_admission_snapshot (
        assertion_admission_snapshot_id,
        assertion_admission_identity_key, snapshot_version,
        supersedes_assertion_admission_snapshot_id,
        descriptor_assertion_id, review_receipt_id,
        qualification_receipt_id, admission_receipt_id,
        reviewer_decision_evidence_id,
        assertion_source_payload_sha256, review_chain_payload_sha256,
        admission_state_code
    ) VALUES (
        'round3m.review-snapshot:' || NEW.review_receipt_key,
        'round3m.descriptor-assertion:' || NEW.descriptor_assertion_id::TEXT,
        next_snapshot_version,
        predecessor_snapshot.assertion_admission_snapshot_id,
        NEW.descriptor_assertion_id, NEW.review_receipt_id,
        NEW.qualification_receipt_id, NEW.admission_receipt_id,
        NEW.reviewer_decision_evidence_id,
        audit.round3m_descriptor_assertion_source_payload_sha256(
            NEW.descriptor_assertion_id
        ),
        audit.round3m_descriptor_review_chain_payload_sha256(
            NEW.review_receipt_id
        ),
        'ADMITTED'
    );

    RETURN NEW;
END
$capture_round3m_assertion_admission_snapshot$;

CREATE TRIGGER round3m_058_capture_assertion_admission_ai
AFTER INSERT ON audit.round3m_descriptor_review_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.capture_round3m_assertion_admission_snapshot();

CREATE VIEW audit.v_round3m_current_reviewed_assertion_admission
WITH (security_barrier = true) AS
SELECT snapshot.*
FROM audit.round3m_reviewed_assertion_admission_snapshot AS snapshot
JOIN corpus.round3m_descriptor_assertion AS assertion
  ON assertion.descriptor_assertion_id = snapshot.descriptor_assertion_id
 AND assertion.current_review_receipt_id = snapshot.review_receipt_id
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = snapshot.review_receipt_id
 AND receipt.descriptor_assertion_id = snapshot.descriptor_assertion_id
WHERE snapshot.admission_state_code = 'ADMITTED'
  AND snapshot.admitted_at <= transaction_timestamp()
  AND audit.round3m_descriptor_review_receipt_has_full_evidence(
      snapshot.review_receipt_id,
      FALSE
      )
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_reviewed_assertion_admission_snapshot AS successor
      WHERE successor.supersedes_assertion_admission_snapshot_id =
            snapshot.assertion_admission_snapshot_id
  )
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_descriptor_review_receipt AS successor
      WHERE successor.supersedes_review_receipt_id =
            receipt.review_receipt_id
  );

COMMENT ON VIEW audit.v_round3m_current_reviewed_assertion_admission IS
    'Operational current-admission surface: joins immutable admitted snapshots to the exact current 058 chain and leaf receipt. Snapshot/source/chain hashes are captured at admission and reverified by the authoritative gate-validation function; ordinary UPDATE/DELETE is rejected, while a superuser or DDL owner can bypass database enforcement.';

CREATE FUNCTION corpus.protect_round3m_admitted_assertion_source_snapshot()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_admitted_assertion_source_snapshot$
DECLARE
    source_changed BOOLEAN;
BEGIN
    source_changed := TG_OP = 'DELETE' OR
        (to_jsonb(OLD) - ARRAY[
            'review_state', 'review_actor_type',
            'current_review_receipt_id'
        ]) IS DISTINCT FROM
        (to_jsonb(NEW) - ARRAY[
            'review_state', 'review_actor_type',
            'current_review_receipt_id'
        ]);

    IF source_changed AND EXISTS (
        SELECT 1
        FROM audit.round3m_reviewed_assertion_admission_snapshot AS snapshot
        WHERE snapshot.descriptor_assertion_id = OLD.descriptor_assertion_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_admitted_assertion_source_immutable_ck',
            MESSAGE = 'source, effective-record, publication, tier, rights, and normalization identity of an admitted assertion are immutable; create a new assertion and admission successor';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_admitted_assertion_source_snapshot$;

CREATE TRIGGER round3m_admitted_assertion_source_snapshot_bud
BEFORE UPDATE OR DELETE ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    corpus.protect_round3m_admitted_assertion_source_snapshot();

CREATE OR REPLACE FUNCTION corpus.validate_round3m_review_state()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_review_state$
DECLARE
    receipt audit.round3m_descriptor_review_receipt%ROWTYPE;
    decision_matches BOOLEAN;
BEGIN
    IF NEW.current_review_receipt_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO STRICT receipt
    FROM audit.round3m_descriptor_review_receipt
    WHERE review_receipt_id = NEW.current_review_receipt_id;

    IF receipt.descriptor_assertion_id IS DISTINCT FROM
          NEW.descriptor_assertion_id
       OR receipt.review_actor_type IS DISTINCT FROM NEW.review_actor_type
       OR EXISTS (
            SELECT 1
            FROM audit.round3m_descriptor_review_receipt AS successor
            WHERE successor.supersedes_review_receipt_id =
                  receipt.review_receipt_id
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_receipt_scope_ck',
            MESSAGE = 'current review receipt must be the leaf receipt for the same assertion and actor type';
    END IF;

    decision_matches := CASE NEW.review_state
        WHEN 'SOURCE_AUDITED' THEN
            receipt.decision = 'SOURCE_AUDIT_COMPLETE'
        WHEN 'HUMAN_CONFIRMED' THEN
            receipt.decision = 'CONFIRM_DESCRIPTOR'
        WHEN 'EXPERT_ADJUDICATED' THEN
            receipt.decision = 'ADJUDICATE_DESCRIPTOR'
        WHEN 'REJECTED_NON_DESCRIPTOR' THEN
            receipt.decision = 'REJECT_NON_DESCRIPTOR'
        WHEN 'REJECTED_DUPLICATE' THEN
            receipt.decision = 'REJECT_DUPLICATE'
        WHEN 'SOURCE_UNAVAILABLE' THEN
            receipt.decision = 'MARK_SOURCE_UNAVAILABLE'
        WHEN 'PROVENANCE_UNRESOLVED' THEN
            receipt.decision IN ('MARK_AMBIGUOUS', 'MARK_UNRESOLVED')
        WHEN 'RIGHTS_BLOCKED' THEN
            receipt.decision = 'RIGHTS_BLOCK'
        ELSE FALSE
    END;

    IF decision_matches IS NOT TRUE THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_state_receipt_ck',
            MESSAGE = 'review state must match the current receipt decision';
    END IF;

    IF NEW.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
       AND NOT audit.round3m_descriptor_review_receipt_has_full_evidence(
           receipt.review_receipt_id
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_human_full_chain_ck',
            MESSAGE = 'human and expert review states require the complete current 058 qualification, admission, and row-level decision-evidence chain';
    END IF;

    RETURN NEW;
END
$validate_round3m_review_state$;

CREATE OR REPLACE FUNCTION audit.validate_round3m_label_mapping_receipt()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_label_mapping_receipt$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt AS receipt
        JOIN corpus.round3m_descriptor_assertion AS assertion
          ON assertion.descriptor_assertion_id = receipt.descriptor_assertion_id
        JOIN audit.v_round3m_current_reviewed_assertion_admission AS snapshot
          ON snapshot.review_receipt_id = receipt.review_receipt_id
         AND snapshot.descriptor_assertion_id =
             receipt.descriptor_assertion_id
        WHERE receipt.review_receipt_id = NEW.review_receipt_id
          AND receipt.descriptor_assertion_id = NEW.descriptor_assertion_id
          AND assertion.current_review_receipt_id = receipt.review_receipt_id
          AND assertion.review_state IN (
              'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
          )
          AND audit.round3m_descriptor_review_receipt_has_full_evidence(
              receipt.review_receipt_id
          )
          AND receipt.human_event_evidence_sha256 =
              NEW.mapping_evidence_sha256
          AND receipt.decision IN (
              'CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR'
          )
          AND receipt.created_at = NEW.created_at
          AND NEW.created_at = transaction_timestamp()
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_label_mapping_human_evidence_ck',
            MESSAGE = 'label mapping must be bound in the same transaction to the current admitted assertion and complete 058 human evidence chain';
    END IF;

    RETURN NEW;
END
$validate_round3m_label_mapping_receipt$;

CREATE OR REPLACE VIEW corpus.v_round3m_human_reviewed_descriptor_universe
WITH (security_barrier = true) AS
SELECT audited.*
FROM corpus.v_round3m_source_audited_descriptor_universe AS audited
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = audited.current_review_receipt_id
 AND receipt.descriptor_assertion_id = audited.descriptor_assertion_id
JOIN audit.v_round3m_current_reviewed_assertion_admission AS snapshot
  ON snapshot.review_receipt_id = receipt.review_receipt_id
 AND snapshot.descriptor_assertion_id = receipt.descriptor_assertion_id
WHERE audited.review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
  AND receipt.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
  AND receipt.receipt_origin_code IN (
      'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
  )
  AND receipt.decision IN ('CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR');

COMMENT ON VIEW corpus.v_round3m_human_reviewed_descriptor_universe IS
    'Source-audited assertions whose current leaf review is bound to a governed 058 qualification, admission, bounded row-level reviewer decision, and immutable admitted source snapshot.';

CREATE VIEW corpus.v_round3m_expert_adjudicated_descriptor_universe AS
SELECT reviewed.*
FROM corpus.v_round3m_human_reviewed_descriptor_universe AS reviewed
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = reviewed.current_review_receipt_id
JOIN audit.v_round3m_current_reviewer_qualification_receipt AS qualification
  ON qualification.qualification_receipt_id =
     receipt.qualification_receipt_id
WHERE reviewed.review_state = 'EXPERT_ADJUDICATED'
  AND receipt.review_actor_type = 'EXPERT_REVIEWER'
  AND receipt.reviewer_role = 'ADJUDICATOR'
  AND receipt.decision = 'ADJUDICATE_DESCRIPTOR'
  AND receipt.adjudication_status = 'FINAL'
  AND qualification.qualification_scope_code = 'SENSORY_ADJUDICATION'
  AND qualification.qualification_level_code = 'EXPERT';

-- Evidence-qualified review surfaces are deliberately independent of rights
-- eligibility. They support review-ledger audit without converting human
-- review into research/model/deployment permission.
CREATE VIEW audit.v_round3m_qualified_human_descriptor_review_receipt AS
SELECT receipt.*
FROM audit.round3m_descriptor_review_receipt AS receipt
JOIN corpus.round3m_descriptor_assertion AS assertion
  ON assertion.descriptor_assertion_id = receipt.descriptor_assertion_id
 AND assertion.current_review_receipt_id = receipt.review_receipt_id
JOIN audit.v_round3m_current_reviewed_assertion_admission AS snapshot
  ON snapshot.descriptor_assertion_id = receipt.descriptor_assertion_id
 AND snapshot.review_receipt_id = receipt.review_receipt_id
WHERE receipt.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
  AND receipt.decision IN ('CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR')
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_descriptor_review_receipt AS successor
      WHERE successor.supersedes_review_receipt_id =
            receipt.review_receipt_id
  );

CREATE VIEW audit.v_round3m_qualified_expert_descriptor_review_receipt AS
SELECT receipt.*
FROM audit.v_round3m_qualified_human_descriptor_review_receipt AS receipt
JOIN audit.v_round3m_current_reviewer_qualification_receipt AS qualification
  ON qualification.qualification_receipt_id =
     receipt.qualification_receipt_id
WHERE receipt.review_actor_type = 'EXPERT_REVIEWER'
  AND receipt.reviewer_role = 'ADJUDICATOR'
  AND receipt.decision = 'ADJUDICATE_DESCRIPTOR'
  AND receipt.adjudication_status = 'FINAL'
  AND qualification.qualification_scope_code = 'SENSORY_ADJUDICATION'
  AND qualification.qualification_level_code = 'EXPERT';

COMMENT ON VIEW audit.v_round3m_qualified_human_descriptor_review_receipt IS
    'Current fully evidenced 058 human/expert confirmation receipts regardless of independent rights eligibility; this surface grants no research, model, deployment, or redistribution permission.';
COMMENT ON VIEW audit.v_round3m_qualified_expert_descriptor_review_receipt IS
    'Current fully evidenced 058 FINAL expert sensory adjudications; this audit surface grants no rights permission.';

CREATE OR REPLACE VIEW corpus.v_round3m_verified_descriptor_label_target
WITH (security_barrier = true) AS
SELECT target.*
FROM corpus.round3m_descriptor_label_target AS target
JOIN audit.round3m_descriptor_label_mapping_receipt AS mapping
  ON mapping.label_mapping_receipt_id = target.label_mapping_receipt_id
 AND mapping.descriptor_assertion_id = target.descriptor_assertion_id
 AND mapping.review_receipt_id = target.review_receipt_id
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = mapping.review_receipt_id
 AND receipt.descriptor_assertion_id = mapping.descriptor_assertion_id
JOIN audit.v_round3m_current_reviewed_assertion_admission AS snapshot
  ON snapshot.review_receipt_id = receipt.review_receipt_id
 AND snapshot.descriptor_assertion_id = receipt.descriptor_assertion_id
WHERE receipt.human_event_evidence_sha256 =
      mapping.mapping_evidence_sha256
  AND mapping.label_set_sha256 =
      audit.round3m_descriptor_label_set_sha256(
          mapping.label_mapping_receipt_id
      )
  AND target.normalization_decision IN (
      'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET'
  )
  AND target.concept_id IS NOT NULL
  AND EXISTS (
      SELECT 1
      FROM kb.concept AS concept
      WHERE concept.concept_id = target.concept_id
        AND concept.concept_key = target.output_label_key
        AND concept.lifecycle_status_code = 'active'
        AND concept.replacement_concept_id IS NULL
  );

CREATE VIEW audit.v_round3m_reviewer_evidence_contract_metrics AS
SELECT
    (SELECT count(*)::BIGINT
     FROM evidence.round3m_reviewer_evidence_artifact) AS
        reviewer_evidence_artifact_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_reviewer_qualification_receipt) AS
        reviewer_qualification_receipt_count,
    (SELECT count(*)::BIGINT
     FROM audit.v_round3m_current_reviewer_qualification_receipt) AS
        current_valid_qualification_receipt_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_reviewer_admission_receipt) AS
        reviewer_admission_receipt_count,
    (SELECT count(*)::BIGINT
     FROM audit.v_round3m_current_reviewer_admission_receipt) AS
        current_valid_admission_receipt_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_reviewer_decision_evidence) AS
        reviewer_decision_evidence_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_reviewer_decision_evidence
     WHERE row_level_evidence) AS row_level_decision_evidence_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_descriptor_review_receipt AS receipt
     WHERE receipt.review_actor_type IN (
         'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
     ) AND receipt.qualification_receipt_id IS NULL) AS
        human_review_claim_without_qualification_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_descriptor_review_receipt AS receipt
     WHERE receipt.review_actor_type IN (
         'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
     ) AND receipt.admission_receipt_id IS NULL) AS
        human_review_claim_without_admission_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_descriptor_review_receipt AS receipt
     WHERE receipt.review_actor_type IN (
         'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
     ) AND receipt.reviewer_decision_evidence_id IS NULL) AS
        human_review_claim_without_decision_evidence_count,
    (SELECT count(*)::BIGINT
     FROM audit.round3m_descriptor_review_receipt AS receipt
     JOIN corpus.round3m_descriptor_assertion AS assertion
       ON assertion.descriptor_assertion_id = receipt.descriptor_assertion_id
      AND assertion.current_review_receipt_id = receipt.review_receipt_id
     WHERE receipt.review_actor_type IN (
         'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
     ) AND NOT audit.round3m_descriptor_review_receipt_has_full_evidence(
         receipt.review_receipt_id
     )
       AND NOT EXISTS (
           SELECT 1
           FROM audit.round3m_descriptor_review_receipt AS successor
           WHERE successor.supersedes_review_receipt_id =
                 receipt.review_receipt_id
       )) AS human_review_decision_mismatch_count,
    (SELECT count(*)::BIGINT
     FROM corpus.v_round3m_human_reviewed_descriptor_universe) AS
        human_confirmed_review_count,
    (SELECT count(*)::BIGINT
     FROM corpus.v_round3m_expert_adjudicated_descriptor_universe) AS
        expert_adjudicated_review_count,
    (SELECT count(*)::BIGINT
     FROM audit.v_round3m_qualified_human_descriptor_review_receipt) AS
        qualified_human_confirmation_receipt_count,
    (SELECT count(*)::BIGINT
     FROM audit.v_round3m_qualified_expert_descriptor_review_receipt) AS
        qualified_expert_adjudication_receipt_count;

ALTER FUNCTION audit.run_round3m_gate_validation_queries()
    RENAME TO run_round3m_gate_validation_queries_pre_v058;

CREATE FUNCTION audit.run_round3m_gate_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3m_gate_validation_queries$
WITH evidence_checks AS (
    SELECT
        'round3m.migration_058_approval_is_nonreview_scope'::TEXT AS
            check_key,
        CASE WHEN count(*) = 1
                   AND bool_and(user_approved)
                   AND bool_and(
                       NOT user_approval_counts_as_reviewer_evidence
                       AND NOT main_promotion_allowed
                       AND NOT model_training_allowed
                       AND NOT training_corpus_freeze_allowed
                   )
             THEN 0 ELSE 1 END::BIGINT AS violation_count
    FROM audit.round3m_migration_058_approval_contract
    UNION ALL
    SELECT
        'round3m.reviewer_evidence_artifact_is_governed',
        count(*)::BIGINT
    FROM evidence.round3m_reviewer_evidence_artifact AS artifact
    WHERE artifact.artifact_sha256 !~ '^[0-9a-f]{64}$'
       OR artifact.acquired_at > artifact.imported_at
       OR artifact.imported_at > transaction_timestamp()
       OR artifact.evidence_classification_code NOT IN (
           'ACTUAL_EXTERNAL_HUMAN_DECISION',
           'PROJECT_HUMAN_DECISION_WITH_EVIDENCE'
       )
       OR lower(artifact.supplying_authority)
          ~ '(^|[._ /-])codex($|[._ /-])'
       OR artifact.governed_locator =
          'conversation://round3m/migration-058-explicit-approval'
       OR lower(artifact.supplying_authority)
          ~ 'migration[ _-]*approval'
    UNION ALL
    SELECT
        'round3m.reviewer_qualification_payloads_are_exact',
        count(*)::BIGINT
    FROM audit.round3m_reviewer_qualification_receipt AS qualification
    WHERE qualification.deterministic_payload_sha256 IS DISTINCT FROM
          audit.round3m_reviewer_qualification_payload_sha256(
              qualification
          )
    UNION ALL
    SELECT
        'round3m.reviewer_qualification_current_leaf_is_unique',
        count(*)::BIGINT
    FROM (
        SELECT reviewer_id, qualification_scope_code,
               allowed_reviewer_role, qualification_protocol_version
        FROM audit.round3m_reviewer_qualification_receipt AS receipt
        WHERE NOT EXISTS (
            SELECT 1
            FROM audit.round3m_reviewer_qualification_receipt AS successor
            WHERE successor.supersedes_qualification_receipt_id =
                  receipt.qualification_receipt_id
        )
        GROUP BY reviewer_id, qualification_scope_code,
                 allowed_reviewer_role, qualification_protocol_version
        HAVING count(*) > 1
    ) AS duplicate_leaf
    UNION ALL
    SELECT
        'round3m.reviewer_admission_payloads_are_exact',
        count(*)::BIGINT
    FROM audit.round3m_reviewer_admission_receipt AS admission
    WHERE admission.deterministic_payload_sha256 IS DISTINCT FROM
          audit.round3m_reviewer_admission_payload_sha256(admission)
    UNION ALL
    SELECT
        'round3m.reviewer_admission_current_leaf_is_unique',
        count(*)::BIGINT
    FROM (
        SELECT reviewer_id, admitted_reviewer_role,
               admitted_protocol_version, review_scope_code,
               review_scope_key
        FROM audit.round3m_reviewer_admission_receipt AS receipt
        WHERE NOT EXISTS (
            SELECT 1
            FROM audit.round3m_reviewer_admission_receipt AS successor
            WHERE successor.supersedes_admission_receipt_id =
                  receipt.admission_receipt_id
        )
        GROUP BY reviewer_id, admitted_reviewer_role,
                 admitted_protocol_version, review_scope_code,
                 review_scope_key
        HAVING count(*) > 1
    ) AS duplicate_leaf
    UNION ALL
    SELECT
        'round3m.reviewer_decision_payloads_are_exact',
        count(*)::BIGINT
    FROM audit.round3m_reviewer_decision_evidence AS decision_evidence
    WHERE decision_evidence.deterministic_payload_sha256 IS DISTINCT FROM
          audit.round3m_reviewer_decision_payload_sha256(
              decision_evidence
          )
       OR NOT decision_evidence.row_level_evidence
       OR decision_evidence.imported_at > transaction_timestamp()
    UNION ALL
    SELECT
        'round3m.reviewer_decision_current_leaf_is_unique',
        count(*)::BIGINT
    FROM (
        SELECT decision_target_kind, descriptor_assertion_id,
               professional_label_review_id, reviewer_id,
               review_protocol_version
        FROM audit.round3m_reviewer_decision_evidence AS decision_evidence
        WHERE NOT EXISTS (
            SELECT 1
            FROM audit.round3m_reviewer_decision_evidence AS successor
            WHERE successor.supersedes_decision_evidence_id =
                  decision_evidence.reviewer_decision_evidence_id
        )
        GROUP BY decision_target_kind, descriptor_assertion_id,
                 professional_label_review_id, reviewer_id,
                 review_protocol_version
        HAVING count(*) > 1
    ) AS duplicate_leaf
    UNION ALL
    SELECT
        'round3m.human_review_receipts_require_full_058_chain',
        count(*)::BIGINT
    FROM audit.round3m_descriptor_review_receipt AS receipt
    JOIN corpus.round3m_descriptor_assertion AS assertion
      ON assertion.descriptor_assertion_id = receipt.descriptor_assertion_id
     AND assertion.current_review_receipt_id = receipt.review_receipt_id
    WHERE receipt.review_actor_type IN (
            'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
      AND NOT audit.round3m_descriptor_review_receipt_has_full_evidence(
          receipt.review_receipt_id
      )
      AND NOT EXISTS (
          SELECT 1
          FROM audit.round3m_descriptor_review_receipt AS successor
          WHERE successor.supersedes_review_receipt_id =
                receipt.review_receipt_id
      )
    UNION ALL
    SELECT
        'round3m.expert_reviewers_are_qualified',
        count(*)::BIGINT
    FROM audit.round3m_descriptor_review_receipt AS receipt
    JOIN corpus.round3m_descriptor_assertion AS assertion
      ON assertion.descriptor_assertion_id = receipt.descriptor_assertion_id
     AND assertion.current_review_receipt_id = receipt.review_receipt_id
    WHERE receipt.review_actor_type = 'EXPERT_REVIEWER'
      AND NOT audit.round3m_descriptor_review_receipt_has_full_evidence(
          receipt.review_receipt_id
      )
      AND NOT EXISTS (
          SELECT 1
          FROM audit.round3m_descriptor_review_receipt AS successor
          WHERE successor.supersedes_review_receipt_id =
                receipt.review_receipt_id
      )
    UNION ALL
    SELECT
        'round3m.nonhuman_receipts_have_no_human_chain',
        count(*)::BIGINT
    FROM audit.round3m_descriptor_review_receipt AS receipt
    WHERE receipt.review_actor_type NOT IN (
            'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
      AND (
          receipt.qualification_receipt_id IS NOT NULL
          OR receipt.admission_receipt_id IS NOT NULL
          OR receipt.reviewer_decision_evidence_id IS NOT NULL
          OR receipt.reviewer_decision_artifact_id IS NOT NULL
      )
    UNION ALL
    SELECT
        'round3m.admitted_assertion_snapshots_are_exact',
        count(*)::BIGINT
    FROM audit.round3m_reviewed_assertion_admission_snapshot AS snapshot
    WHERE snapshot.assertion_source_payload_sha256 IS DISTINCT FROM
          audit.round3m_descriptor_assertion_source_payload_sha256(
              snapshot.descriptor_assertion_id
          )
       OR snapshot.review_chain_payload_sha256 IS DISTINCT FROM
          audit.round3m_descriptor_review_chain_payload_sha256(
              snapshot.review_receipt_id
          )
       OR snapshot.deterministic_payload_sha256 IS DISTINCT FROM
          audit.round3m_assertion_admission_payload_sha256(snapshot)
    UNION ALL
    SELECT
        'round3m.human_reviewed_universe_requires_058_admission',
        count(*)::BIGINT
    FROM corpus.v_round3m_human_reviewed_descriptor_universe AS reviewed
    WHERE NOT EXISTS (
        SELECT 1
        FROM audit.v_round3m_current_reviewed_assertion_admission AS snapshot
        WHERE snapshot.descriptor_assertion_id =
              reviewed.descriptor_assertion_id
          AND snapshot.review_receipt_id =
              reviewed.current_review_receipt_id
    )
    UNION ALL
    SELECT
        'round3m.verified_label_targets_require_058_admission',
        count(*)::BIGINT
    FROM corpus.v_round3m_verified_descriptor_label_target AS target
    WHERE NOT EXISTS (
        SELECT 1
        FROM audit.v_round3m_current_reviewed_assertion_admission AS snapshot
        WHERE snapshot.descriptor_assertion_id =
              target.descriptor_assertion_id
          AND snapshot.review_receipt_id = target.review_receipt_id
    )
    UNION ALL
    SELECT
        'round3m.active_descriptor_views_use_058_chain',
        CASE WHEN
            pg_get_viewdef(
                'corpus.v_round3m_human_reviewed_descriptor_universe'::regclass,
                TRUE
            ) LIKE '%v_round3m_current_reviewed_assertion_admission%'
            AND pg_get_viewdef(
                'corpus.v_round3m_verified_descriptor_label_target'::regclass,
                TRUE
            ) LIKE '%v_round3m_current_reviewed_assertion_admission%'
            THEN 0 ELSE 1 END::BIGINT
)
SELECT prior.check_key, prior.violation_count, prior.passed
FROM audit.run_round3m_gate_validation_queries_pre_v058() AS prior
WHERE prior.check_key <> 'round3m.expert_reviewers_are_qualified'
UNION ALL
SELECT evidence.check_key, evidence.violation_count,
       evidence.violation_count = 0 AS passed
FROM evidence_checks AS evidence
ORDER BY check_key
$run_round3m_gate_validation_queries$;

COMMENT ON FUNCTION audit.run_round3m_gate_validation_queries() IS
    'Round 3M invariants including migration 058 acquired reviewer artifacts, qualification, admission, row-level decision evidence, and admitted assertion snapshots. User migration approval is never reviewer evidence.';

REVOKE UPDATE, DELETE
ON evidence.round3m_reviewer_evidence_artifact,
   audit.round3m_reviewer_qualification_receipt,
   audit.round3m_reviewer_admission_receipt,
   audit.round3m_reviewer_decision_evidence,
   audit.round3m_reviewed_assertion_admission_snapshot
FROM PUBLIC;

DO $round3m_revoke_ordinary_role_mutation$
DECLARE
    role_name TEXT;
BEGIN
    FOR role_name IN
        SELECT rolname
        FROM pg_roles
        WHERE rolname IN (
            'coffee_ingest', 'coffee_application', 'coffee_app',
            'application_user', 'ingestion_user'
        )
    LOOP
        EXECUTE format(
            'REVOKE UPDATE, DELETE ON evidence.round3m_reviewer_evidence_artifact, audit.round3m_reviewer_qualification_receipt, audit.round3m_reviewer_admission_receipt, audit.round3m_reviewer_decision_evidence, audit.round3m_reviewed_assertion_admission_snapshot FROM %I',
            role_name
        );
    END LOOP;
END
$round3m_revoke_ordinary_role_mutation$;

COMMENT ON TABLE evidence.round3m_reviewer_evidence_artifact IS
    'Hash/locator-first acquired reviewer evidence. Private credentials and reviewer PII stay outside public Git. Database enforcement is append-only for ordinary operation; a superuser or DDL owner can bypass it.';
COMMENT ON TABLE audit.round3m_reviewer_qualification_receipt IS
    'Versioned immutable reviewer qualification bound to governed acquired evidence; scope is proportional and never inferred from a reviewer code.';
COMMENT ON TABLE audit.round3m_reviewer_admission_receipt IS
    'Versioned immutable admission of one qualified reviewer to one role, protocol, and bounded review scope.';
COMMENT ON TABLE audit.round3m_reviewer_decision_evidence IS
    'One bounded row-level reviewer decision. Batch hashes alone cannot authorize human credit, and one evidence row cannot be reused for another target or decision.';
COMMENT ON TABLE audit.round3m_reviewed_assertion_admission_snapshot IS
    'Immutable admitted source snapshot for a fully evidenced human/expert receipt. Review-pointer changes are versioned; source/record/tier/rights identity changes require a new assertion.';

COMMIT;
