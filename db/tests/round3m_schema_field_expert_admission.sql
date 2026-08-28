\set ON_ERROR_STOP on
\pset pager off

-- Migration 058 acceptance contract. All positive evidence is synthetic,
-- transaction-local, and rolled back. No fixture can survive this file.

BEGIN;

CREATE FUNCTION pg_temp.expect_round3m_058_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3m_058_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND3M_058_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END
$expect_round3m_058_failure$;

CREATE TEMP TABLE round3m_058_targets AS
SELECT row_number() OVER (ORDER BY descriptor_assertion_id)::INTEGER AS n,
       descriptor_assertion_id, descriptor_assertion_key
FROM (
    SELECT descriptor_assertion_id, descriptor_assertion_key
    FROM corpus.round3m_descriptor_assertion
    WHERE descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
      AND NOT synthetic_generated
    ORDER BY (evidence_tier = 'P2') DESC, descriptor_assertion_id
    LIMIT 4
) AS selected;

DO $round3m_058_target_precondition$
BEGIN
    IF (SELECT count(*) FROM round3m_058_targets) <> 4 THEN
        RAISE EXCEPTION
            'Migration 058 tests require four loaded real assertion identities';
    END IF;
END
$round3m_058_target_precondition$;

INSERT INTO audit.reviewer (reviewer_key, display_name, affiliation)
VALUES
    ('round3m-058-human', 'Round 3M 058 human fixture',
     'Transaction-local test fixture'),
    ('round3m-058-other', 'Round 3M 058 mismatch fixture',
     'Transaction-local test fixture'),
    ('round3m-058-expert', 'Round 3M 058 expert fixture',
     'Transaction-local test fixture');

CREATE TEMP VIEW round3m_058_reviewers AS
SELECT reviewer_id, reviewer_key
FROM audit.reviewer
WHERE reviewer_key LIKE 'round3m-058-%';

-- Test-only artifacts emulate acquired governed evidence without storing PII.
INSERT INTO evidence.round3m_reviewer_evidence_artifact (
    reviewer_evidence_artifact_id, artifact_purpose_code,
    evidence_classification_code, governed_locator, artifact_sha256,
    byte_count, non_storage_reason, acquired_at, storage_state_code,
    privacy_state_code, supplying_authority, acquisition_method_code
)
VALUES
    ('fixture:058:qualification', 'REVIEWER_QUALIFICATION_EVIDENCE',
     'PROJECT_HUMAN_DECISION_WITH_EVIDENCE',
     'fixture://058/qualification',
     audit.round3i_utf8_sha256('fixture:058:qualification'), 0,
     'Transaction-local hash-only qualification fixture.',
     '2026-01-01T00:00:00Z', 'HASH_AND_LOCATOR_ONLY', 'PSEUDONYMOUS',
     'Round 3M test harness', 'GOVERNED_PROJECT_HUMAN_IMPORT'),
    ('fixture:058:admission', 'REVIEWER_ADMISSION_AUTHORIZATION',
     'PROJECT_HUMAN_DECISION_WITH_EVIDENCE',
     'fixture://058/admission',
     audit.round3i_utf8_sha256('fixture:058:admission'), 0,
     'Transaction-local hash-only admission fixture.',
     '2026-01-01T00:00:00Z', 'HASH_AND_LOCATOR_ONLY', 'PSEUDONYMOUS',
     'Round 3M test harness', 'GOVERNED_PROJECT_HUMAN_IMPORT'),
    ('fixture:058:decision', 'ROW_LEVEL_REVIEWER_DECISION_EXPORT',
     'PROJECT_HUMAN_DECISION_WITH_EVIDENCE',
     'fixture://058/decision-export',
     audit.round3i_utf8_sha256('fixture:058:decision'), 0,
     'Transaction-local hash-only row-decision fixture.',
     '2026-01-01T00:00:00Z', 'HASH_AND_LOCATOR_ONLY', 'PSEUDONYMOUS',
     'Round 3M test harness', 'GOVERNED_PROJECT_HUMAN_IMPORT');

-- Human qualification/admission: proportional descriptor-segmentation scope.
INSERT INTO audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id, qualification_identity_key,
    qualification_version, reviewer_id, reviewer_pseudonymous_code,
    qualification_scope_code, allowed_reviewer_role,
    qualification_level_code, qualification_protocol_version,
    qualification_evidence_artifact_id, qualification_evidence_locator,
    issuing_authority, valid_from, valid_to,
    qualification_state_code, deterministic_payload_sha256
)
SELECT 'fixture:058:q:human:v1', 'fixture:058:q:human', 1,
       reviewer_id, reviewer_key, 'DESCRIPTOR_SEGMENTATION_REVIEW',
       'PROFESSIONAL_SENSORY_REVIEWER', 'PROTOCOL_QUALIFIED',
       'round3m-058-human-v1', 'fixture:058:qualification',
       'fixture://058/qualification#human', 'Round 3M test authority',
       DATE '2026-01-01', DATE '2026-12-31', 'ACTIVE', repeat('0', 64)
FROM round3m_058_reviewers
WHERE reviewer_key = 'round3m-058-human';

INSERT INTO audit.round3m_reviewer_admission_receipt (
    admission_receipt_id, admission_identity_key, admission_version,
    reviewer_id, reviewer_pseudonymous_code, qualification_receipt_id,
    admitted_reviewer_role, admitted_protocol_version,
    review_scope_code, review_scope_key, admission_authority,
    admission_evidence_artifact_id, admission_evidence_locator,
    valid_from, valid_to, admission_state_code,
    deterministic_payload_sha256
)
SELECT 'fixture:058:a:human:v1', 'fixture:058:a:human', 1,
       reviewer_id, reviewer_key, 'fixture:058:q:human:v1',
       'PROFESSIONAL_SENSORY_REVIEWER', 'round3m-058-human-v1',
       'DESCRIPTOR_SEGMENTATION_REVIEW', 'descriptor:round3m-pilot',
       'Round 3M test authority', 'fixture:058:admission',
       'fixture://058/admission#human',
       '2026-01-01T00:00:00Z', '2026-12-31T23:59:59Z', 'ACTIVE',
       repeat('0', 64)
FROM round3m_058_reviewers
WHERE reviewer_key = 'round3m-058-human';

INSERT INTO audit.round3m_reviewer_decision_evidence (
    reviewer_decision_evidence_id, decision_evidence_identity_key,
    decision_evidence_version, reviewer_id, reviewer_pseudonymous_code,
    decision_target_kind, descriptor_assertion_id, review_decision_code,
    review_actor_type, reviewer_role, review_protocol_version,
    review_scope_code, review_scope_key, review_event_timestamp,
    source_decision_artifact_id, bounded_decision_locator,
    source_decision_payload_sha256, decision_batch_id,
    evidence_state_code, row_level_evidence, deterministic_payload_sha256
)
SELECT 'fixture:058:d:human:v1', 'fixture:058:d:human', 1,
       reviewer_id, reviewer_key, 'ROUND3M_DESCRIPTOR_ASSERTION',
       target.descriptor_assertion_id, 'CONFIRM_DESCRIPTOR',
       'HUMAN_REVIEWER', 'PROFESSIONAL_SENSORY_REVIEWER',
       'round3m-058-human-v1', 'DESCRIPTOR_SEGMENTATION_REVIEW',
       'descriptor:round3m-pilot', '2026-08-28T00:10:00Z',
       'fixture:058:decision', 'fixture://058/decision-export#row=1',
       audit.round3i_utf8_sha256('fixture:058:d:human:v1'),
       'fixture-058-batch', 'ACTIVE', TRUE, repeat('0', 64)
FROM round3m_058_reviewers
CROSS JOIN round3m_058_targets AS target
WHERE reviewer_key = 'round3m-058-human' AND target.n = 1;

-- Wrong-scope chain for exact scope mismatch tests.
INSERT INTO audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id, qualification_identity_key,
    qualification_version, reviewer_id, reviewer_pseudonymous_code,
    qualification_scope_code, allowed_reviewer_role,
    qualification_level_code, qualification_protocol_version,
    qualification_evidence_artifact_id, qualification_evidence_locator,
    issuing_authority, valid_from, valid_to,
    qualification_state_code, deterministic_payload_sha256
)
SELECT 'fixture:058:q:norm:v1', 'fixture:058:q:norm', 1,
       reviewer_id, reviewer_key, 'NORMALIZATION_TARGET_REVIEW',
       'PROFESSIONAL_SENSORY_REVIEWER', 'PROTOCOL_QUALIFIED',
       'round3m-058-human-v1', 'fixture:058:qualification',
       'fixture://058/qualification#norm', 'Round 3M test authority',
       DATE '2026-01-01', DATE '2026-12-31', 'ACTIVE', repeat('0', 64)
FROM round3m_058_reviewers WHERE reviewer_key = 'round3m-058-human';

INSERT INTO audit.round3m_reviewer_admission_receipt (
    admission_receipt_id, admission_identity_key, admission_version,
    reviewer_id, reviewer_pseudonymous_code, qualification_receipt_id,
    admitted_reviewer_role, admitted_protocol_version,
    review_scope_code, review_scope_key, admission_authority,
    admission_evidence_artifact_id, admission_evidence_locator,
    valid_from, valid_to, admission_state_code,
    deterministic_payload_sha256
)
SELECT 'fixture:058:a:norm:v1', 'fixture:058:a:norm', 1,
       reviewer_id, reviewer_key, 'fixture:058:q:norm:v1',
       'PROFESSIONAL_SENSORY_REVIEWER', 'round3m-058-human-v1',
       'NORMALIZATION_TARGET_REVIEW', 'descriptor:round3m-pilot',
       'Round 3M test authority', 'fixture:058:admission',
       'fixture://058/admission#norm',
       '2026-01-01T00:00:00Z', '2026-12-31T23:59:59Z', 'ACTIVE',
       repeat('0', 64)
FROM round3m_058_reviewers WHERE reviewer_key = 'round3m-058-human';

CREATE FUNCTION pg_temp.insert_round3m_058_receipt(
    p_key TEXT,
    p_assertion_id BIGINT,
    p_reviewer_id BIGINT,
    p_pseudonym TEXT,
    p_role TEXT,
    p_actor TEXT,
    p_hash TEXT,
    p_protocol TEXT,
    p_decision TEXT,
    p_locator TEXT,
    p_reviewed_at TIMESTAMPTZ,
    p_adjudication TEXT,
    p_qualification TEXT,
    p_admission TEXT,
    p_decision_evidence TEXT,
    p_artifact TEXT,
    p_version INTEGER DEFAULT 1,
    p_supersedes BIGINT DEFAULT NULL,
    p_previous TEXT DEFAULT 'PROVISIONAL_MACHINE_CLASSIFIED'
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $insert_round3m_058_receipt$
DECLARE
    inserted_id BIGINT;
BEGIN
    INSERT INTO audit.round3m_descriptor_review_receipt (
        review_receipt_key, descriptor_assertion_id, receipt_version,
        supersedes_review_receipt_id, reviewer_id,
        reviewer_id_or_pseudonymous_code, reviewer_role,
        review_actor_type, receipt_origin_code,
        human_event_evidence_sha256, review_protocol_version,
        decision, decision_reason, evidence_locator, reviewed_at,
        adjudication_status, previous_decision,
        qualification_receipt_id, admission_receipt_id,
        reviewer_decision_evidence_id, reviewer_decision_artifact_id
    ) VALUES (
        p_key, p_assertion_id, p_version, p_supersedes, p_reviewer_id,
        p_pseudonym, p_role, p_actor, 'HUMAN_REVIEW_IMPORT', p_hash,
        p_protocol, p_decision, 'Transaction-local migration 058 fixture.',
        p_locator, p_reviewed_at, p_adjudication, p_previous,
        p_qualification, p_admission, p_decision_evidence, p_artifact
    ) RETURNING review_receipt_id INTO inserted_id;
    RETURN inserted_id;
END
$insert_round3m_058_receipt$;

-- 1--11: receipt-only and exact-binding failures.
SELECT pg_temp.expect_round3m_058_failure(
    '01_arbitrary_sha_only',
    format($sql$SELECT pg_temp.insert_round3m_058_receipt(
        'fixture:058:bad:hash-only', %s, NULL, 'round3m-058-human',
        'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER', repeat('a',64),
        'round3m-058-human-v1', 'CONFIRM_DESCRIPTOR',
        'fixture://058/bad/hash-only', '2026-08-28T00:10:00Z',
        'NOT_REQUIRED', NULL, NULL, NULL, NULL)$sql$,
        (SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=1)),
    '23514', 'round3m_human_review_full_chain_required_ck');

SELECT pg_temp.expect_round3m_058_failure(
    '02_no_qualification',
    format($sql$SELECT pg_temp.insert_round3m_058_receipt(
        'fixture:058:bad:no-q', %s, %s, 'round3m-058-human',
        'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER', %L,
        'round3m-058-human-v1', 'CONFIRM_DESCRIPTOR',
        'fixture://058/decision-export#row=1', '2026-08-28T00:10:00Z',
        'NOT_REQUIRED', NULL, 'fixture:058:a:human:v1',
        'fixture:058:d:human:v1', 'fixture:058:decision')$sql$,
        (SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=1),
        (SELECT reviewer_id FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human'),
        audit.round3i_utf8_sha256('fixture:058:d:human:v1')),
    '23514', 'round3m_human_review_full_chain_required_ck');

DO $round3m_058_no_admission_and_decision$
DECLARE
    target_id BIGINT;
    human_id BIGINT;
    payload TEXT := audit.round3i_utf8_sha256('fixture:058:d:human:v1');
    actual_state TEXT;
    actual_constraint TEXT;
    test_case RECORD;
BEGIN
    SELECT descriptor_assertion_id INTO STRICT target_id
    FROM round3m_058_targets WHERE n=1;
    SELECT reviewer_id INTO STRICT human_id
    FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';
    FOR test_case IN
        SELECT * FROM (VALUES
            ('03_no_admission', 'fixture:058:q:human:v1'::TEXT,
             NULL::TEXT, 'fixture:058:d:human:v1'::TEXT,
             'fixture:058:decision'::TEXT),
            ('04_no_row_decision_evidence', 'fixture:058:q:human:v1',
             'fixture:058:a:human:v1', NULL, NULL)
        ) AS cases(test_key, qualification_id, admission_id,
                   decision_id, artifact_id)
    LOOP
        BEGIN
            PERFORM pg_temp.insert_round3m_058_receipt(
                'fixture:058:bad:' || test_case.test_key, target_id,
                human_id, 'round3m-058-human',
                'PROFESSIONAL_SENSORY_REVIEWER', 'HUMAN_REVIEWER',
                payload, 'round3m-058-human-v1', 'CONFIRM_DESCRIPTOR',
                'fixture://058/decision-export#row=1',
                '2026-08-28T00:10:00Z', 'NOT_REQUIRED',
                test_case.qualification_id, test_case.admission_id,
                test_case.decision_id, test_case.artifact_id);
            RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: %',
                test_case.test_key;
        EXCEPTION WHEN OTHERS THEN
            GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                actual_constraint = CONSTRAINT_NAME;
            IF actual_state <> '23514'
               OR actual_constraint IS DISTINCT FROM
                  'round3m_human_review_full_chain_required_ck' THEN
                RAISE;
            END IF;
            RAISE NOTICE
                'ROUND3M_058_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
                test_case.test_key, actual_state, actual_constraint;
        END;
    END LOOP;
END
$round3m_058_no_admission_and_decision$;

-- 5--11 use a complete but deliberately mismatched chain.
DO $round3m_058_exact_mismatch_negatives$
DECLARE
    target_one BIGINT;
    target_two BIGINT;
    human_id BIGINT;
    other_id BIGINT;
    payload TEXT := audit.round3i_utf8_sha256('fixture:058:d:human:v1');
    actual_state TEXT;
    actual_constraint TEXT;
    test_case RECORD;
BEGIN
    SELECT descriptor_assertion_id INTO STRICT target_one
    FROM round3m_058_targets WHERE n=1;
    SELECT descriptor_assertion_id INTO STRICT target_two
    FROM round3m_058_targets WHERE n=2;
    SELECT reviewer_id INTO STRICT human_id FROM round3m_058_reviewers
    WHERE reviewer_key='round3m-058-human';
    SELECT reviewer_id INTO STRICT other_id FROM round3m_058_reviewers
    WHERE reviewer_key='round3m-058-other';

    FOR test_case IN
        SELECT * FROM (VALUES
          ('05_reviewer_id_mismatch', target_one, other_id,
           'round3m-058-human', 'CONFIRM_DESCRIPTOR',
           'round3m-058-human-v1', 'fixture:058:q:human:v1',
           'fixture:058:a:human:v1'),
          ('06_reviewer_pseudonym_mismatch', target_one, human_id,
           'round3m-058-other', 'CONFIRM_DESCRIPTOR',
           'round3m-058-human-v1', 'fixture:058:q:human:v1',
           'fixture:058:a:human:v1'),
          ('07_assertion_id_mismatch', target_two, human_id,
           'round3m-058-human', 'CONFIRM_DESCRIPTOR',
           'round3m-058-human-v1', 'fixture:058:q:human:v1',
           'fixture:058:a:human:v1'),
          ('08_decision_mismatch', target_one, human_id,
           'round3m-058-human', 'MARK_AMBIGUOUS',
           'round3m-058-human-v1', 'fixture:058:q:human:v1',
           'fixture:058:a:human:v1'),
          ('09_protocol_version_mismatch', target_one, human_id,
           'round3m-058-human', 'CONFIRM_DESCRIPTOR',
           'round3m-058-human-v2', 'fixture:058:q:human:v1',
           'fixture:058:a:human:v1'),
          ('10_qualification_scope_mismatch', target_one, human_id,
           'round3m-058-human', 'CONFIRM_DESCRIPTOR',
           'round3m-058-human-v1', 'fixture:058:q:norm:v1',
           'fixture:058:a:norm:v1'),
          ('11_admission_scope_mismatch', target_one, human_id,
           'round3m-058-human', 'CONFIRM_DESCRIPTOR',
           'round3m-058-human-v1', 'fixture:058:q:human:v1',
           'fixture:058:a:norm:v1')
        ) AS cases(test_key, assertion_id, reviewer_id, pseudonym,
                   decision_code, protocol_version, qualification_id,
                   admission_id)
    LOOP
        BEGIN
            PERFORM pg_temp.insert_round3m_058_receipt(
                'fixture:058:bad:' || test_case.test_key,
                test_case.assertion_id, test_case.reviewer_id,
                test_case.pseudonym, 'PROFESSIONAL_SENSORY_REVIEWER',
                'HUMAN_REVIEWER', payload, test_case.protocol_version,
                test_case.decision_code,
                'fixture://058/decision-export#row=1',
                '2026-08-28T00:10:00Z', 'NOT_REQUIRED',
                test_case.qualification_id, test_case.admission_id,
                'fixture:058:d:human:v1', 'fixture:058:decision');
            RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: %',
                test_case.test_key;
        EXCEPTION WHEN OTHERS THEN
            GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE,
                actual_constraint = CONSTRAINT_NAME;
            IF actual_state <> '23514'
               OR actual_constraint IS DISTINCT FROM
                  'round3m_descriptor_review_full_chain_exact_ck' THEN
                RAISE;
            END IF;
            RAISE NOTICE
                'ROUND3M_058_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
                test_case.test_key, actual_state, actual_constraint;
        END;
    END LOOP;
END
$round3m_058_exact_mismatch_negatives$;

-- Additional qualification/admission states used by negatives 12--15.
INSERT INTO audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id, qualification_identity_key,
    qualification_version, reviewer_id, reviewer_pseudonymous_code,
    qualification_scope_code, allowed_reviewer_role,
    qualification_level_code, qualification_protocol_version,
    qualification_evidence_artifact_id, qualification_evidence_locator,
    issuing_authority, valid_from, valid_to,
    qualification_state_code, deterministic_payload_sha256
)
SELECT id, identity_key, 1, reviewer_id, reviewer_key,
       'DESCRIPTOR_SEGMENTATION_REVIEW',
       'PROFESSIONAL_SENSORY_REVIEWER', 'PROTOCOL_QUALIFIED', protocol,
       'fixture:058:qualification', 'fixture://058/qualification#' || suffix,
       'Round 3M test authority', valid_from, valid_to, 'ACTIVE', repeat('0',64)
FROM round3m_058_reviewers
CROSS JOIN (VALUES
  ('fixture:058:q:expired:v1','fixture:058:q:expired','round3m-058-expired-v1','expired',DATE '2025-01-01',DATE '2025-12-31'),
  ('fixture:058:q:revoked:v1','fixture:058:q:revoked','round3m-058-revoked-v1','revoked',DATE '2026-01-01',DATE '2026-12-31'),
  ('fixture:058:q:admrev:v1','fixture:058:q:admrev','round3m-058-admrev-v1','admrev',DATE '2026-01-01',DATE '2026-12-31'),
  ('fixture:058:q:outside:v1','fixture:058:q:outside','round3m-058-outside-v1','outside',DATE '2025-01-01',DATE '2026-12-31')
) AS q(id,identity_key,protocol,suffix,valid_from,valid_to)
WHERE reviewer_key='round3m-058-human';

INSERT INTO audit.round3m_reviewer_admission_receipt (
    admission_receipt_id, admission_identity_key, admission_version,
    reviewer_id, reviewer_pseudonymous_code, qualification_receipt_id,
    admitted_reviewer_role, admitted_protocol_version,
    review_scope_code, review_scope_key, admission_authority,
    admission_evidence_artifact_id, admission_evidence_locator,
    valid_from, valid_to, admission_state_code,
    deterministic_payload_sha256
)
SELECT 'fixture:058:a:' || suffix || ':v1',
       'fixture:058:a:' || suffix, 1, reviewer_id, reviewer_key,
       qualification_id, 'PROFESSIONAL_SENSORY_REVIEWER', protocol,
       'DESCRIPTOR_SEGMENTATION_REVIEW', 'descriptor:round3m-pilot',
       'Round 3M test authority', 'fixture:058:admission',
       'fixture://058/admission#' || suffix,
       admission_from, admission_to, 'ACTIVE', repeat('0',64)
FROM round3m_058_reviewers
CROSS JOIN (VALUES
  ('expired','fixture:058:q:expired:v1','round3m-058-expired-v1','2025-01-01T00:00:00Z'::TIMESTAMPTZ,'2025-12-31T23:59:59Z'::TIMESTAMPTZ),
  ('revoked','fixture:058:q:revoked:v1','round3m-058-revoked-v1','2026-01-01T00:00:00Z','2026-12-31T23:59:59Z'),
  ('admrev','fixture:058:q:admrev:v1','round3m-058-admrev-v1','2026-01-01T00:00:00Z','2026-12-31T23:59:59Z'),
  ('outside','fixture:058:q:outside:v1','round3m-058-outside-v1','2026-01-01T00:00:00Z','2026-12-31T23:59:59Z')
) AS a(suffix,qualification_id,protocol,admission_from,admission_to)
WHERE reviewer_key='round3m-058-human';

INSERT INTO audit.round3m_reviewer_decision_evidence (
    reviewer_decision_evidence_id, decision_evidence_identity_key,
    decision_evidence_version, reviewer_id, reviewer_pseudonymous_code,
    decision_target_kind, descriptor_assertion_id, review_decision_code,
    review_actor_type, reviewer_role, review_protocol_version,
    review_scope_code, review_scope_key, review_event_timestamp,
    source_decision_artifact_id, bounded_decision_locator,
    source_decision_payload_sha256, evidence_state_code,
    row_level_evidence, deterministic_payload_sha256
)
SELECT 'fixture:058:d:' || suffix || ':v1', 'fixture:058:d:' || suffix, 1,
       reviewer_id, reviewer_key, 'ROUND3M_DESCRIPTOR_ASSERTION',
       target.descriptor_assertion_id, 'CONFIRM_DESCRIPTOR',
       'HUMAN_REVIEWER', 'PROFESSIONAL_SENSORY_REVIEWER', protocol,
       'DESCRIPTOR_SEGMENTATION_REVIEW', 'descriptor:round3m-pilot',
       event_at, 'fixture:058:decision',
       'fixture://058/decision-export#row=' || suffix,
       audit.round3i_utf8_sha256('fixture:058:d:' || suffix || ':v1'),
       'ACTIVE', TRUE, repeat('0',64)
FROM round3m_058_reviewers
CROSS JOIN round3m_058_targets AS target
CROSS JOIN (VALUES
  ('expired','round3m-058-expired-v1','2025-06-01T00:00:00Z'::TIMESTAMPTZ),
  ('revoked','round3m-058-revoked-v1','2026-08-28T00:13:00Z'),
  ('admrev','round3m-058-admrev-v1','2026-08-28T00:14:00Z'),
  ('outside','round3m-058-outside-v1','2025-12-31T12:00:00Z')
) AS d(suffix,protocol,event_at)
WHERE reviewer_key='round3m-058-human' AND target.n=4;

-- Revoke qualification and admission only after their v1 dependants exist.
INSERT INTO audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id, qualification_identity_key,
    qualification_version, supersedes_qualification_receipt_id,
    reviewer_id, reviewer_pseudonymous_code, qualification_scope_code,
    allowed_reviewer_role, qualification_level_code,
    qualification_protocol_version, qualification_evidence_artifact_id,
    qualification_evidence_locator, issuing_authority, valid_from,
    valid_to, qualification_state_code, deterministic_payload_sha256
)
SELECT 'fixture:058:q:revoked:v2', 'fixture:058:q:revoked', 2,
       'fixture:058:q:revoked:v1', reviewer_id, reviewer_key,
       'DESCRIPTOR_SEGMENTATION_REVIEW',
       'PROFESSIONAL_SENSORY_REVIEWER', 'PROTOCOL_QUALIFIED',
       'round3m-058-revoked-v1', 'fixture:058:qualification',
       'fixture://058/qualification#revoked-v2',
       'Round 3M test authority', DATE '2026-01-01', DATE '2026-12-31',
       'REVOKED', repeat('0',64)
FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';

INSERT INTO audit.round3m_reviewer_admission_receipt (
    admission_receipt_id, admission_identity_key, admission_version,
    supersedes_admission_receipt_id, reviewer_id,
    reviewer_pseudonymous_code, qualification_receipt_id,
    admitted_reviewer_role, admitted_protocol_version,
    review_scope_code, review_scope_key, admission_authority,
    admission_evidence_artifact_id, admission_evidence_locator,
    valid_from, valid_to, admission_state_code,
    deterministic_payload_sha256
)
SELECT 'fixture:058:a:admrev:v2', 'fixture:058:a:admrev', 2,
       'fixture:058:a:admrev:v1', reviewer_id, reviewer_key,
       'fixture:058:q:admrev:v1', 'PROFESSIONAL_SENSORY_REVIEWER',
       'round3m-058-admrev-v1', 'DESCRIPTOR_SEGMENTATION_REVIEW',
       'descriptor:round3m-pilot', 'Round 3M test authority',
       'fixture:058:admission', 'fixture://058/admission#admrev-v2',
       '2026-01-01T00:00:00Z', '2026-12-31T23:59:59Z', 'REVOKED',
       repeat('0',64)
FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';

DO $round3m_058_state_negatives$
DECLARE
    target_id BIGINT;
    human_id BIGINT;
    actual_state TEXT;
    actual_constraint TEXT;
    test_case RECORD;
BEGIN
    SELECT descriptor_assertion_id INTO STRICT target_id
    FROM round3m_058_targets WHERE n=4;
    SELECT reviewer_id INTO STRICT human_id FROM round3m_058_reviewers
    WHERE reviewer_key='round3m-058-human';
    FOR test_case IN SELECT * FROM (VALUES
      ('12_expired_qualification','expired','2025-06-01T00:00:00Z'::TIMESTAMPTZ),
      ('13_revoked_or_superseded_qualification','revoked','2026-08-28T00:13:00Z'),
      ('14_superseded_admission','admrev','2026-08-28T00:14:00Z'),
      ('15_decision_outside_admission_period','outside','2025-12-31T12:00:00Z')
    ) AS cases(test_key,suffix,event_at)
    LOOP
      BEGIN
        PERFORM pg_temp.insert_round3m_058_receipt(
          'fixture:058:bad:'||test_case.test_key, target_id, human_id,
          'round3m-058-human','PROFESSIONAL_SENSORY_REVIEWER',
          'HUMAN_REVIEWER',
          audit.round3i_utf8_sha256('fixture:058:d:'||test_case.suffix||':v1'),
          'round3m-058-'||test_case.suffix||'-v1','CONFIRM_DESCRIPTOR',
          'fixture://058/decision-export#row='||test_case.suffix,
          test_case.event_at,'NOT_REQUIRED',
          'fixture:058:q:'||test_case.suffix||':v1',
          'fixture:058:a:'||test_case.suffix||':v1',
          'fixture:058:d:'||test_case.suffix||':v1','fixture:058:decision');
        RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: %',test_case.test_key;
      EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state=RETURNED_SQLSTATE,
          actual_constraint=CONSTRAINT_NAME;
        IF actual_state<>'23514' OR actual_constraint IS DISTINCT FROM
          'round3m_descriptor_review_full_chain_exact_ck' THEN RAISE; END IF;
        RAISE NOTICE 'ROUND3M_058_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
          test_case.test_key,actual_state,actual_constraint;
      END;
    END LOOP;
END
$round3m_058_state_negatives$;

-- 16--18: evidence reuse and automated-human impersonation.
DO $round3m_058_reuse_actor_negatives$
DECLARE
  target_one BIGINT; target_two BIGINT; human_id BIGINT;
  actual_state TEXT; actual_constraint TEXT; test_case RECORD;
BEGIN
  SELECT descriptor_assertion_id INTO STRICT target_one FROM round3m_058_targets WHERE n=1;
  SELECT descriptor_assertion_id INTO STRICT target_two FROM round3m_058_targets WHERE n=2;
  SELECT reviewer_id INTO STRICT human_id FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';
  FOR test_case IN SELECT * FROM (VALUES
    ('16_decision_evidence_reused_for_another_assertion',target_two,'round3m-058-human','CONFIRM_DESCRIPTOR'),
    ('17_decision_evidence_reused_for_different_decision',target_one,'round3m-058-human','MARK_AMBIGUOUS'),
    ('18_automated_actor_presented_as_human',target_one,'codex','CONFIRM_DESCRIPTOR')
  ) AS cases(test_key,assertion_id,pseudonym,decision_code)
  LOOP
    BEGIN
      PERFORM pg_temp.insert_round3m_058_receipt(
        'fixture:058:bad:'||test_case.test_key,test_case.assertion_id,human_id,
        test_case.pseudonym,'PROFESSIONAL_SENSORY_REVIEWER','HUMAN_REVIEWER',
        audit.round3i_utf8_sha256('fixture:058:d:human:v1'),
        'round3m-058-human-v1',test_case.decision_code,
        'fixture://058/decision-export#row=1','2026-08-28T00:10:00Z',
        'NOT_REQUIRED','fixture:058:q:human:v1','fixture:058:a:human:v1',
        'fixture:058:d:human:v1','fixture:058:decision');
      RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: %',test_case.test_key;
    EXCEPTION WHEN OTHERS THEN
      GET STACKED DIAGNOSTICS actual_state=RETURNED_SQLSTATE,actual_constraint=CONSTRAINT_NAME;
      IF actual_state<>'23514' OR actual_constraint IS DISTINCT FROM
        'round3m_descriptor_review_full_chain_exact_ck' THEN RAISE; END IF;
      RAISE NOTICE 'ROUND3M_058_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
        test_case.test_key,actual_state,actual_constraint;
    END;
  END LOOP;
END
$round3m_058_reuse_actor_negatives$;

-- Expert qualification, admission, and row-level decision evidence.
INSERT INTO audit.round3m_reviewer_qualification_receipt (
  qualification_receipt_id,qualification_identity_key,qualification_version,
  reviewer_id,reviewer_pseudonymous_code,qualification_scope_code,
  allowed_reviewer_role,qualification_level_code,qualification_protocol_version,
  qualification_evidence_artifact_id,qualification_evidence_locator,
  issuing_authority,valid_from,valid_to,qualification_state_code,
  deterministic_payload_sha256)
SELECT 'fixture:058:q:expert:v1','fixture:058:q:expert',1,reviewer_id,reviewer_key,
  'SENSORY_ADJUDICATION','ADJUDICATOR','EXPERT','round3m-058-expert-v1',
  'fixture:058:qualification','fixture://058/qualification#expert',
  'Round 3M test authority',DATE '2026-01-01',DATE '2026-12-31','ACTIVE',repeat('0',64)
FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-expert';

INSERT INTO audit.round3m_reviewer_admission_receipt (
  admission_receipt_id,admission_identity_key,admission_version,reviewer_id,
  reviewer_pseudonymous_code,qualification_receipt_id,admitted_reviewer_role,
  admitted_protocol_version,review_scope_code,review_scope_key,
  admission_authority,admission_evidence_artifact_id,admission_evidence_locator,
  valid_from,valid_to,admission_state_code,deterministic_payload_sha256)
SELECT 'fixture:058:a:expert:v1','fixture:058:a:expert',1,reviewer_id,reviewer_key,
  'fixture:058:q:expert:v1','ADJUDICATOR','round3m-058-expert-v1',
  'SENSORY_ADJUDICATION','descriptor:round3m-pilot','Round 3M test authority',
  'fixture:058:admission','fixture://058/admission#expert',
  '2026-01-01T00:00:00Z','2026-12-31T23:59:59Z','ACTIVE',repeat('0',64)
FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-expert';

INSERT INTO audit.round3m_reviewer_decision_evidence (
  reviewer_decision_evidence_id,decision_evidence_identity_key,
  decision_evidence_version,reviewer_id,reviewer_pseudonymous_code,
  decision_target_kind,descriptor_assertion_id,review_decision_code,
  review_actor_type,reviewer_role,review_protocol_version,review_scope_code,
  review_scope_key,review_event_timestamp,source_decision_artifact_id,
  bounded_decision_locator,source_decision_payload_sha256,evidence_state_code,
  row_level_evidence,deterministic_payload_sha256)
SELECT 'fixture:058:d:expert:v1','fixture:058:d:expert',1,reviewer_id,reviewer_key,
  'ROUND3M_DESCRIPTOR_ASSERTION',target.descriptor_assertion_id,
  'ADJUDICATE_DESCRIPTOR','EXPERT_REVIEWER','ADJUDICATOR',
  'round3m-058-expert-v1','SENSORY_ADJUDICATION','descriptor:round3m-pilot',
  '2026-08-28T00:12:00Z','fixture:058:decision',
  'fixture://058/decision-export#row=expert',
  audit.round3i_utf8_sha256('fixture:058:d:expert:v1'),'ACTIVE',TRUE,repeat('0',64)
FROM round3m_058_reviewers CROSS JOIN round3m_058_targets target
WHERE reviewer_key='round3m-058-expert' AND target.n=2;

-- 19 project reviewer cannot claim expert scope; 20 expert must be FINAL.
DO $round3m_058_expert_negatives$
DECLARE
  target_one BIGINT; target_two BIGINT; human_id BIGINT; expert_id BIGINT;
  actual_state TEXT; actual_constraint TEXT;
BEGIN
  SELECT descriptor_assertion_id INTO STRICT target_one FROM round3m_058_targets WHERE n=1;
  SELECT descriptor_assertion_id INTO STRICT target_two FROM round3m_058_targets WHERE n=2;
  SELECT reviewer_id INTO STRICT human_id FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';
  SELECT reviewer_id INTO STRICT expert_id FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-expert';
  BEGIN
    PERFORM pg_temp.insert_round3m_058_receipt('fixture:058:bad:project-as-expert',
      target_one,human_id,'round3m-058-human','ADJUDICATOR','EXPERT_REVIEWER',
      audit.round3i_utf8_sha256('fixture:058:d:human:v1'),'round3m-058-human-v1',
      'ADJUDICATE_DESCRIPTOR','fixture://058/decision-export#row=1',
      '2026-08-28T00:10:00Z','FINAL','fixture:058:q:human:v1',
      'fixture:058:a:human:v1','fixture:058:d:human:v1','fixture:058:decision');
    RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: 19';
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS actual_state=RETURNED_SQLSTATE,actual_constraint=CONSTRAINT_NAME;
    IF actual_state<>'23514' OR actual_constraint IS DISTINCT FROM
      'round3m_descriptor_review_full_chain_exact_ck' THEN RAISE; END IF;
    RAISE NOTICE 'ROUND3M_058_NEGATIVE=19_project_reviewer_as_expert SQLSTATE=% CONSTRAINT=% PASS',actual_state,actual_constraint;
  END;
  BEGIN
    PERFORM pg_temp.insert_round3m_058_receipt('fixture:058:bad:expert-not-final',
      target_two,expert_id,'round3m-058-expert','ADJUDICATOR','EXPERT_REVIEWER',
      audit.round3i_utf8_sha256('fixture:058:d:expert:v1'),'round3m-058-expert-v1',
      'ADJUDICATE_DESCRIPTOR','fixture://058/decision-export#row=expert',
      '2026-08-28T00:12:00Z','NOT_REQUIRED','fixture:058:q:expert:v1',
      'fixture:058:a:expert:v1','fixture:058:d:expert:v1','fixture:058:decision');
    RAISE EXCEPTION 'Migration 058 negative unexpectedly succeeded: 20';
  EXCEPTION WHEN OTHERS THEN
    GET STACKED DIAGNOSTICS actual_state=RETURNED_SQLSTATE,actual_constraint=CONSTRAINT_NAME;
    IF actual_state<>'23514' OR actual_constraint IS DISTINCT FROM
      'round3m_expert_adjudication_full_chain_ck' THEN RAISE; END IF;
    RAISE NOTICE 'ROUND3M_058_NEGATIVE=20_expert_without_final SQLSTATE=% CONSTRAINT=% PASS',actual_state,actual_constraint;
  END;
END
$round3m_058_expert_negatives$;

-- Positive A: fully evidenced human confirmation increments exactly one.
CREATE TEMP TABLE round3m_058_positive_receipts (kind TEXT PRIMARY KEY, receipt_id BIGINT);
INSERT INTO round3m_058_positive_receipts
SELECT 'human-v1', pg_temp.insert_round3m_058_receipt(
  'fixture:058:review:human:v1',target.descriptor_assertion_id,reviewer.reviewer_id,
  reviewer.reviewer_key,'PROFESSIONAL_SENSORY_REVIEWER','HUMAN_REVIEWER',
  audit.round3i_utf8_sha256('fixture:058:d:human:v1'),'round3m-058-human-v1',
  'CONFIRM_DESCRIPTOR','fixture://058/decision-export#row=1',
  '2026-08-28T00:10:00Z','NOT_REQUIRED','fixture:058:q:human:v1',
  'fixture:058:a:human:v1','fixture:058:d:human:v1','fixture:058:decision')
FROM round3m_058_targets target CROSS JOIN round3m_058_reviewers reviewer
WHERE target.n=1 AND reviewer.reviewer_key='round3m-058-human';

UPDATE corpus.round3m_descriptor_assertion assertion
SET review_state='HUMAN_CONFIRMED',review_actor_type='HUMAN_REVIEWER',
    current_review_receipt_id=receipt.receipt_id
FROM round3m_058_targets target CROSS JOIN round3m_058_positive_receipts receipt
WHERE target.n=1 AND receipt.kind='human-v1'
  AND assertion.descriptor_assertion_id=target.descriptor_assertion_id;

DO $round3m_058_positive_a$
BEGIN
  IF (SELECT count(*)
      FROM audit.v_round3m_qualified_human_descriptor_review_receipt
      WHERE descriptor_assertion_id=(SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=1)) <> 1 THEN
    RAISE EXCEPTION 'ROUND3M_058_POSITIVE=A qualified human did not receive exactly one confirmation credit';
  END IF;
  RAISE NOTICE 'ROUND3M_058_POSITIVE=A_QUALIFIED_HUMAN_CONFIRMATION PASS';
END
$round3m_058_positive_a$;

-- 21: the human decision row/event cannot be reused as independent expert adjudication.
SELECT pg_temp.expect_round3m_058_failure(
  '21_unsupported_self_adjudication',
  format($sql$SELECT pg_temp.insert_round3m_058_receipt(
    'fixture:058:bad:self-adjudication',%s,%s,'round3m-058-human','ADJUDICATOR',
    'EXPERT_REVIEWER',%L,'round3m-058-human-v1','ADJUDICATE_DESCRIPTOR',
    'fixture://058/decision-export#row=1','2026-08-28T00:10:00Z','FINAL',
    'fixture:058:q:human:v1','fixture:058:a:human:v1',
    'fixture:058:d:human:v1','fixture:058:decision',2,%s,'CONFIRM_DESCRIPTOR')$sql$,
    (SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=1),
    (SELECT reviewer_id FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human'),
    audit.round3i_utf8_sha256('fixture:058:d:human:v1'),
    (SELECT receipt_id FROM round3m_058_positive_receipts WHERE kind='human-v1')),
  '23514','round3m_descriptor_review_full_chain_exact_ck');

-- 22--27: ordinary mutation of evidence, qualification/admission, and row decisions is rejected.
SELECT pg_temp.expect_round3m_058_failure('22_update_qualification_evidence',
  $$UPDATE evidence.round3m_reviewer_evidence_artifact SET non_storage_reason='bad' WHERE reviewer_evidence_artifact_id='fixture:058:qualification'$$,
  '23514','round3m_immutable_evidence_ck');
SELECT pg_temp.expect_round3m_058_failure('23_delete_qualification_evidence',
  $$DELETE FROM evidence.round3m_reviewer_evidence_artifact WHERE reviewer_evidence_artifact_id='fixture:058:qualification'$$,
  '23514','round3m_immutable_evidence_ck');
SELECT pg_temp.expect_round3m_058_failure('24_update_admission_receipt',
  $$UPDATE audit.round3m_reviewer_admission_receipt SET admission_state_code='REVOKED' WHERE admission_receipt_id='fixture:058:a:human:v1'$$,
  '23514','round3m_immutable_evidence_ck');
SELECT pg_temp.expect_round3m_058_failure('25_delete_admission_receipt',
  $$DELETE FROM audit.round3m_reviewer_admission_receipt WHERE admission_receipt_id='fixture:058:a:human:v1'$$,
  '23514','round3m_immutable_evidence_ck');
SELECT pg_temp.expect_round3m_058_failure('26_update_reviewer_decision_evidence',
  $$UPDATE audit.round3m_reviewer_decision_evidence SET evidence_state_code='REVOKED' WHERE reviewer_decision_evidence_id='fixture:058:d:human:v1'$$,
  '23514','round3m_immutable_evidence_ck');
SELECT pg_temp.expect_round3m_058_failure('27_delete_reviewer_decision_evidence',
  $$DELETE FROM audit.round3m_reviewer_decision_evidence WHERE reviewer_decision_evidence_id='fixture:058:d:human:v1'$$,
  '23514','round3m_immutable_evidence_ck');

-- 28--29: forked successors and duplicate current leaves are structurally impossible.
SELECT pg_temp.expect_round3m_058_failure('28_forked_successor_chain',
  $$INSERT INTO audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id,qualification_identity_key,qualification_version,
    supersedes_qualification_receipt_id,reviewer_id,reviewer_pseudonymous_code,
    qualification_scope_code,allowed_reviewer_role,qualification_level_code,
    qualification_protocol_version,qualification_evidence_artifact_id,
    qualification_evidence_locator,issuing_authority,valid_from,valid_to,
    qualification_state_code,deterministic_payload_sha256)
  SELECT 'fixture:058:q:revoked:fork','fixture:058:q:revoked',2,
    'fixture:058:q:revoked:v1',reviewer_id,reviewer_key,
    'DESCRIPTOR_SEGMENTATION_REVIEW','PROFESSIONAL_SENSORY_REVIEWER',
    'PROTOCOL_QUALIFIED','round3m-058-revoked-v1','fixture:058:qualification',
    'fixture://058/qualification#fork','Round 3M test authority',
    DATE '2026-01-01',DATE '2026-12-31','ACTIVE',repeat('0',64)
  FROM audit.reviewer WHERE reviewer_key='round3m-058-human'$$,
  '23505','round3m_reviewer_qualification_identity_version_uq');
SELECT pg_temp.expect_round3m_058_failure('29_multiple_current_leaves',
  $$INSERT INTO audit.round3m_reviewer_qualification_receipt (
    qualification_receipt_id,qualification_identity_key,qualification_version,
    reviewer_id,reviewer_pseudonymous_code,qualification_scope_code,
    allowed_reviewer_role,qualification_level_code,qualification_protocol_version,
    qualification_evidence_artifact_id,qualification_evidence_locator,
    issuing_authority,valid_from,valid_to,qualification_state_code,
    deterministic_payload_sha256)
  SELECT 'fixture:058:q:human:parallel','fixture:058:q:human:parallel',1,
    reviewer_id,reviewer_key,'DESCRIPTOR_SEGMENTATION_REVIEW',
    'PROFESSIONAL_SENSORY_REVIEWER','PROTOCOL_QUALIFIED',
    'round3m-058-human-v1','fixture:058:qualification',
    'fixture://058/qualification#parallel','Round 3M test authority',
    DATE '2026-01-01',DATE '2026-12-31','ACTIVE',repeat('0',64)
  FROM audit.reviewer WHERE reviewer_key='round3m-058-human'$$,
  '23505','round3m_reviewer_qualification_natural_version_uq');

-- 30 old receipt-only gate path remains closed.
SELECT pg_temp.expect_round3m_058_failure(
  '30_old_receipt_only_gate_path',
  format($sql$SELECT pg_temp.insert_round3m_058_receipt(
    'fixture:058:bad:old-path',%s,NULL,'legacy-reviewer-code',
    'PROFESSIONAL_SENSORY_REVIEWER','HUMAN_REVIEWER',repeat('f',64),
    'legacy-v1','CONFIRM_DESCRIPTOR','fixture://legacy/batch',
    '2026-08-28T00:00:00Z','NOT_REQUIRED',NULL,NULL,NULL,NULL)$sql$,
    (SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=3)),
  '23514','round3m_human_review_full_chain_required_ck');

-- 31 test-only synthetic evidence cannot be admitted as governed evidence.
SELECT pg_temp.expect_round3m_058_failure('31_test_only_synthetic_evidence',
  $$INSERT INTO evidence.round3m_reviewer_evidence_artifact (
    reviewer_evidence_artifact_id,artifact_purpose_code,
    evidence_classification_code,governed_locator,artifact_sha256,byte_count,
    non_storage_reason,acquired_at,storage_state_code,privacy_state_code,
    supplying_authority,acquisition_method_code)
  VALUES ('fixture:058:synthetic','ROW_LEVEL_REVIEWER_DECISION_EXPORT',
    'TEST_ONLY_SYNTHETIC','fixture://058/synthetic',repeat('1',64),0,
    'Must never persist.','2026-01-01T00:00:00Z','HASH_AND_LOCATOR_ONLY',
    'NO_PERSONAL_DATA','Round 3M test harness','GOVERNED_PROJECT_HUMAN_IMPORT')$$,
  '23514','round3m_reviewer_evidence_artifact_values_ck');

-- 32 the user's migration approval is application authority only.
SELECT pg_temp.expect_round3m_058_failure('32_user_approval_as_reviewer_evidence',
  $$INSERT INTO evidence.round3m_reviewer_evidence_artifact (
    reviewer_evidence_artifact_id,artifact_purpose_code,
    evidence_classification_code,governed_locator,artifact_sha256,byte_count,
    non_storage_reason,acquired_at,storage_state_code,privacy_state_code,
    supplying_authority,acquisition_method_code)
  VALUES ('fixture:058:user-approval','REVIEWER_QUALIFICATION_EVIDENCE',
    'PROJECT_HUMAN_DECISION_WITH_EVIDENCE',
    'conversation://round3m/migration-058-explicit-approval',repeat('2',64),0,
    'Approval is not review evidence.','2026-08-28T00:00:00Z',
    'HASH_AND_LOCATOR_ONLY','NO_PERSONAL_DATA','Migration approval message',
    'GOVERNED_PROJECT_HUMAN_IMPORT')$$,
  '23514','round3m_user_approval_not_reviewer_evidence_ck');

-- Positive B: v2 correction leaves v1 immutable, changes the current leaves,
-- and restores gate credit only after a matching successor receipt is linked.
INSERT INTO audit.round3m_reviewer_qualification_receipt (
  qualification_receipt_id,qualification_identity_key,qualification_version,
  supersedes_qualification_receipt_id,reviewer_id,reviewer_pseudonymous_code,
  qualification_scope_code,allowed_reviewer_role,qualification_level_code,
  qualification_protocol_version,qualification_evidence_artifact_id,
  qualification_evidence_locator,issuing_authority,valid_from,valid_to,
  qualification_state_code,deterministic_payload_sha256)
SELECT 'fixture:058:q:human:v2','fixture:058:q:human',2,
  'fixture:058:q:human:v1',reviewer_id,reviewer_key,
  'DESCRIPTOR_SEGMENTATION_REVIEW','PROFESSIONAL_SENSORY_REVIEWER',
  'PROTOCOL_QUALIFIED','round3m-058-human-v1','fixture:058:qualification',
  'fixture://058/qualification#human-v2','Round 3M test authority',
  DATE '2026-01-01',DATE '2026-12-31','ACTIVE',repeat('0',64)
FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';

INSERT INTO audit.round3m_reviewer_admission_receipt (
  admission_receipt_id,admission_identity_key,admission_version,
  supersedes_admission_receipt_id,reviewer_id,reviewer_pseudonymous_code,
  qualification_receipt_id,admitted_reviewer_role,admitted_protocol_version,
  review_scope_code,review_scope_key,admission_authority,
  admission_evidence_artifact_id,admission_evidence_locator,valid_from,valid_to,
  admission_state_code,deterministic_payload_sha256)
SELECT 'fixture:058:a:human:v2','fixture:058:a:human',2,
  'fixture:058:a:human:v1',reviewer_id,reviewer_key,'fixture:058:q:human:v2',
  'PROFESSIONAL_SENSORY_REVIEWER','round3m-058-human-v1',
  'DESCRIPTOR_SEGMENTATION_REVIEW','descriptor:round3m-pilot',
  'Round 3M test authority','fixture:058:admission',
  'fixture://058/admission#human-v2','2026-01-01T00:00:00Z',
  '2026-12-31T23:59:59Z','ACTIVE',repeat('0',64)
FROM round3m_058_reviewers WHERE reviewer_key='round3m-058-human';

INSERT INTO audit.round3m_reviewer_decision_evidence (
  reviewer_decision_evidence_id,decision_evidence_identity_key,
  decision_evidence_version,supersedes_decision_evidence_id,reviewer_id,
  reviewer_pseudonymous_code,decision_target_kind,descriptor_assertion_id,
  review_decision_code,review_actor_type,reviewer_role,review_protocol_version,
  review_scope_code,review_scope_key,review_event_timestamp,
  source_decision_artifact_id,bounded_decision_locator,
  source_decision_payload_sha256,evidence_state_code,row_level_evidence,
  deterministic_payload_sha256)
SELECT 'fixture:058:d:human:v2','fixture:058:d:human',2,
  'fixture:058:d:human:v1',reviewer_id,reviewer_key,
  'ROUND3M_DESCRIPTOR_ASSERTION',target.descriptor_assertion_id,
  'CONFIRM_DESCRIPTOR','HUMAN_REVIEWER','PROFESSIONAL_SENSORY_REVIEWER',
  'round3m-058-human-v1','DESCRIPTOR_SEGMENTATION_REVIEW',
  'descriptor:round3m-pilot','2026-08-28T00:20:00Z','fixture:058:decision',
  'fixture://058/decision-export#row=1-v2',
  audit.round3i_utf8_sha256('fixture:058:d:human:v2'),'ACTIVE',TRUE,repeat('0',64)
FROM round3m_058_reviewers CROSS JOIN round3m_058_targets target
WHERE reviewer_key='round3m-058-human' AND target.n=1;

INSERT INTO round3m_058_positive_receipts
SELECT 'human-v2',pg_temp.insert_round3m_058_receipt(
  'fixture:058:review:human:v2',target.descriptor_assertion_id,reviewer.reviewer_id,
  reviewer.reviewer_key,'PROFESSIONAL_SENSORY_REVIEWER','HUMAN_REVIEWER',
  audit.round3i_utf8_sha256('fixture:058:d:human:v2'),'round3m-058-human-v1',
  'CONFIRM_DESCRIPTOR','fixture://058/decision-export#row=1-v2',
  '2026-08-28T00:20:00Z','NOT_REQUIRED','fixture:058:q:human:v2',
  'fixture:058:a:human:v2','fixture:058:d:human:v2','fixture:058:decision',2,
  old.receipt_id,'CONFIRM_DESCRIPTOR')
FROM round3m_058_targets target CROSS JOIN round3m_058_reviewers reviewer
CROSS JOIN round3m_058_positive_receipts old
WHERE target.n=1 AND reviewer.reviewer_key='round3m-058-human' AND old.kind='human-v1';

UPDATE corpus.round3m_descriptor_assertion assertion
SET current_review_receipt_id=receipt.receipt_id
FROM round3m_058_targets target CROSS JOIN round3m_058_positive_receipts receipt
WHERE target.n=1 AND receipt.kind='human-v2'
  AND assertion.descriptor_assertion_id=target.descriptor_assertion_id;

DO $round3m_058_positive_b$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM audit.round3m_reviewer_qualification_receipt
      WHERE qualification_receipt_id='fixture:058:q:human:v1')
     OR NOT EXISTS (SELECT 1 FROM audit.v_round3m_current_reviewer_qualification_receipt
      WHERE qualification_receipt_id='fixture:058:q:human:v2')
     OR EXISTS (SELECT 1 FROM audit.v_round3m_current_reviewer_qualification_receipt
      WHERE qualification_receipt_id='fixture:058:q:human:v1')
     OR (SELECT count(*)
         FROM audit.v_round3m_qualified_human_descriptor_review_receipt
         WHERE descriptor_assertion_id=(SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=1))<>1 THEN
    RAISE EXCEPTION 'ROUND3M_058_POSITIVE=B successor correction path failed';
  END IF;
  RAISE NOTICE 'ROUND3M_058_POSITIVE=B_VERSIONED_CORRECTION PASS';
END
$round3m_058_positive_b$;

-- Positive C: expert surface accepts only the full expert sensory chain.
INSERT INTO round3m_058_positive_receipts
SELECT 'expert-v1',pg_temp.insert_round3m_058_receipt(
  'fixture:058:review:expert:v1',target.descriptor_assertion_id,reviewer.reviewer_id,
  reviewer.reviewer_key,'ADJUDICATOR','EXPERT_REVIEWER',
  audit.round3i_utf8_sha256('fixture:058:d:expert:v1'),'round3m-058-expert-v1',
  'ADJUDICATE_DESCRIPTOR','fixture://058/decision-export#row=expert',
  '2026-08-28T00:12:00Z','FINAL','fixture:058:q:expert:v1',
  'fixture:058:a:expert:v1','fixture:058:d:expert:v1','fixture:058:decision')
FROM round3m_058_targets target CROSS JOIN round3m_058_reviewers reviewer
WHERE target.n=2 AND reviewer.reviewer_key='round3m-058-expert';

UPDATE corpus.round3m_descriptor_assertion assertion
SET review_state='EXPERT_ADJUDICATED',review_actor_type='EXPERT_REVIEWER',
    current_review_receipt_id=receipt.receipt_id
FROM round3m_058_targets target CROSS JOIN round3m_058_positive_receipts receipt
WHERE target.n=2 AND receipt.kind='expert-v1'
  AND assertion.descriptor_assertion_id=target.descriptor_assertion_id;

DO $round3m_058_positive_c_and_gate_rebind$
DECLARE
  old_path_count BIGINT;
  failed_gate_checks TEXT;
BEGIN
  IF (SELECT count(*)
      FROM audit.v_round3m_qualified_expert_descriptor_review_receipt
      WHERE descriptor_assertion_id=(SELECT descriptor_assertion_id FROM round3m_058_targets WHERE n=2))<>1 THEN
    RAISE EXCEPTION 'ROUND3M_058_POSITIVE=C expert surface failed';
  END IF;
  SELECT count(*) INTO old_path_count
  FROM audit.round3m_descriptor_review_receipt receipt
  JOIN corpus.round3m_descriptor_assertion assertion
    ON assertion.descriptor_assertion_id=receipt.descriptor_assertion_id
   AND assertion.current_review_receipt_id=receipt.review_receipt_id
  WHERE receipt.review_actor_type IN ('HUMAN_REVIEWER','EXPERT_REVIEWER')
    AND NOT audit.round3m_descriptor_review_receipt_has_full_evidence(receipt.review_receipt_id)
    AND NOT EXISTS (
      SELECT 1 FROM audit.round3m_descriptor_review_receipt successor
      WHERE successor.supersedes_review_receipt_id=receipt.review_receipt_id
    );
  SELECT string_agg(format('%s=%s',check_key,violation_count),', ' ORDER BY check_key)
  INTO failed_gate_checks
  FROM audit.run_round3m_gate_validation_queries()
  WHERE passed IS NOT TRUE OR violation_count<>0;
  IF old_path_count<>0 OR failed_gate_checks IS NOT NULL THEN
    RAISE EXCEPTION
      'ROUND3M_058_POSITIVE=gate rebind/full-chain validation failed old_path_count=% failed_gate_checks=%',
      old_path_count,COALESCE(failed_gate_checks,'none');
  END IF;
  RAISE NOTICE 'ROUND3M_058_POSITIVE=C_QUALIFIED_EXPERT_ADJUDICATION PASS';
  RAISE NOTICE 'OLD_SELF_ATTESTING_GATE_PATH_COUNT=0';
  RAISE NOTICE 'CURRENT_GATE_REQUIRES_QUALIFICATION=true';
  RAISE NOTICE 'CURRENT_GATE_REQUIRES_ADMISSION=true';
  RAISE NOTICE 'CURRENT_GATE_REQUIRES_ROW_DECISION_EVIDENCE=true';
END
$round3m_058_positive_c_and_gate_rebind$;

ROLLBACK;

-- Fail if any transaction-local reviewer fixture survived rollback.
DO $round3m_058_persistence_zero$
BEGIN
  IF EXISTS (SELECT 1 FROM evidence.round3m_reviewer_evidence_artifact
             WHERE reviewer_evidence_artifact_id LIKE 'fixture:058:%')
     OR EXISTS (SELECT 1 FROM audit.round3m_reviewer_qualification_receipt
               WHERE qualification_receipt_id LIKE 'fixture:058:%')
     OR EXISTS (SELECT 1 FROM audit.round3m_reviewer_admission_receipt
               WHERE admission_receipt_id LIKE 'fixture:058:%')
     OR EXISTS (SELECT 1 FROM audit.round3m_reviewer_decision_evidence
               WHERE reviewer_decision_evidence_id LIKE 'fixture:058:%')
     OR EXISTS (SELECT 1 FROM audit.round3m_descriptor_review_receipt
               WHERE review_receipt_key LIKE 'fixture:058:%') THEN
    RAISE EXCEPTION 'PERSISTED_SYNTHETIC_HUMAN_FIXTURE_COUNT is not zero';
  END IF;
  RAISE NOTICE 'PERSISTED_SYNTHETIC_HUMAN_FIXTURE_COUNT=0';
  RAISE NOTICE 'NEW_058_POSITIVE_TEST_COUNT=3';
  RAISE NOTICE 'NEW_058_NEGATIVE_TEST_COUNT=32';
  RAISE NOTICE 'ROUND3M_SCHEMA_FIELD_EXPERT_ADMISSION_PASS=true';
END
$round3m_058_persistence_zero$;
