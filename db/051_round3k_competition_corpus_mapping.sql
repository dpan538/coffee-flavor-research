\set ON_ERROR_STOP on

-- Round 3K professional expression, governed label, duplicate/repeat, split,
-- acquisition-audit, and no-training contract.  This layer never turns a
-- candidate proposed by software into a reviewed training label.

BEGIN;

CREATE TABLE audit.round3k_checkpoint (
    checkpoint_key TEXT NOT NULL,
    frozen_release_version TEXT NOT NULL,
    frozen_main_sha TEXT NOT NULL,
    failed_round3j_branch_sha TEXT NOT NULL,
    phase_a_commit_sha TEXT NOT NULL,
    expected_state_path TEXT NOT NULL,
    db049_semantics_retained BOOLEAN NOT NULL,
    db049_code_cherry_picked BOOLEAN NOT NULL,
    db049_dependency_audit_pass BOOLEAN NOT NULL,
    db050_active_role_superseded BOOLEAN NOT NULL,
    db050_forced_unresolved_contract_reused BOOLEAN NOT NULL,
    model_run_count_at_start BIGINT NOT NULL,
    model_version_count_at_start BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT round3k_checkpoint_pk PRIMARY KEY (checkpoint_key),
    CONSTRAINT round3k_checkpoint_release_fk FOREIGN KEY (
        frozen_release_version
    ) REFERENCES audit.research_database_release (freeze_version)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3k_checkpoint_contract_ck CHECK (
        checkpoint_key = 'round3k.professional-competition-corpus'
        AND frozen_release_version = 'coffee-sensory-research-db-v0.1.0'
        AND frozen_main_sha =
            'c3ae9b880d85507a0b8b0298bb94ef013d02f928'
        AND failed_round3j_branch_sha =
            'a92b448043e8dad468339b3ca2cdfd2b7f6aa772'
        AND phase_a_commit_sha =
            '6e0279e75622f59341cef5464940c385381c82c7'
        AND expected_state_path =
            'db/data/round3k/PROFESSIONAL_CORPUS_EXPECTED_STATE.tsv'
        AND db049_semantics_retained
        AND NOT db049_code_cherry_picked
        AND db049_dependency_audit_pass
        AND db050_active_role_superseded
        AND NOT db050_forced_unresolved_contract_reused
        AND model_run_count_at_start >= 0
        AND model_version_count_at_start >= 0
    )
);

CREATE FUNCTION audit.guard_round3k_checkpoint()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_round3k_checkpoint$
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3k_checkpoint_immutable_ck',
            MESSAGE = 'the Round 3K baseline checkpoint is immutable';
    END IF;

    IF NEW.model_run_count_at_start <> (SELECT count(*) FROM ml.model_run)
       OR NEW.model_version_count_at_start <>
          (SELECT count(*) FROM ml.model_version) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3k_checkpoint_model_baseline_ck',
            MESSAGE = 'Round 3K checkpoint model counts must equal the live frozen baseline';
    END IF;

    RETURN NEW;
END
$guard_round3k_checkpoint$;

CREATE TRIGGER round3k_checkpoint_bi
BEFORE INSERT ON audit.round3k_checkpoint
FOR EACH ROW EXECUTE FUNCTION audit.guard_round3k_checkpoint();

CREATE TRIGGER round3k_checkpoint_bud
BEFORE UPDATE OR DELETE ON audit.round3k_checkpoint
FOR EACH ROW EXECUTE FUNCTION audit.guard_round3k_checkpoint();

INSERT INTO audit.round3k_checkpoint (
    checkpoint_key, frozen_release_version, frozen_main_sha,
    failed_round3j_branch_sha, phase_a_commit_sha, expected_state_path,
    db049_semantics_retained, db049_code_cherry_picked,
    db049_dependency_audit_pass, db050_active_role_superseded,
    db050_forced_unresolved_contract_reused,
    model_run_count_at_start, model_version_count_at_start
)
SELECT
    'round3k.professional-competition-corpus',
    'coffee-sensory-research-db-v0.1.0',
    'c3ae9b880d85507a0b8b0298bb94ef013d02f928',
    'a92b448043e8dad468339b3ca2cdfd2b7f6aa772',
    '6e0279e75622f59341cef5464940c385381c82c7',
    'db/data/round3k/PROFESSIONAL_CORPUS_EXPECTED_STATE.tsv',
    TRUE, FALSE, TRUE, TRUE, FALSE,
    count(*), (SELECT count(*) FROM ml.model_version)
FROM ml.model_run;

CREATE TABLE evidence.professional_privacy_decision (
    professional_privacy_decision_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_privacy_decision_key TEXT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    personal_data_scope_code TEXT NOT NULL,
    direct_identifiers_retained BOOLEAN NOT NULL,
    judge_identity_treatment_code TEXT NOT NULL,
    processing_basis TEXT NOT NULL,
    decision_state_code TEXT NOT NULL,
    decided_on DATE NOT NULL,
    CONSTRAINT professional_privacy_decision_pk PRIMARY KEY (
        professional_privacy_decision_id
    ),
    CONSTRAINT professional_privacy_decision_key_uq UNIQUE (
        professional_privacy_decision_key
    ),
    CONSTRAINT professional_privacy_decision_snapshot_uq UNIQUE (
        professional_source_snapshot_id
    ),
    CONSTRAINT professional_privacy_decision_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_privacy_decision_text_ck CHECK (
        professional_privacy_decision_key =
            lower(btrim(professional_privacy_decision_key))
        AND professional_privacy_decision_key <> ''
        AND processing_basis = btrim(processing_basis)
        AND processing_basis <> ''
    ),
    CONSTRAINT professional_privacy_decision_state_ck CHECK (
        personal_data_scope_code IN (
            'NONE', 'PUBLIC_COMPETITOR_IDENTITY',
            'PSEUDONYMOUS_JUDGE_IDENTITY', 'MIXED_PUBLIC_AND_PSEUDONYMOUS'
        )
        AND judge_identity_treatment_code IN (
            'NOT_PRESENT', 'ANONYMOUS', 'PSEUDONYMOUS', 'PUBLIC_WITH_BASIS'
        )
        AND decision_state_code IN ('ALLOWED', 'DENIED', 'PENDING')
        AND (
            judge_identity_treatment_code <> 'PUBLIC_WITH_BASIS'
            OR decision_state_code = 'ALLOWED'
        )
    )
);

CREATE TABLE corpus.professional_expression (
    professional_expression_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_expression_key TEXT NOT NULL,
    descriptor_assertion_id BIGINT NOT NULL,
    language_tag TEXT NOT NULL,
    normalized_phrase TEXT NOT NULL,
    normalization_rule_code TEXT NOT NULL,
    source_span_start INTEGER,
    source_span_end INTEGER,
    project_authored BOOLEAN NOT NULL DEFAULT FALSE,
    machine_generated BOOLEAN NOT NULL DEFAULT FALSE,
    semantic_inference_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT professional_expression_pk PRIMARY KEY (
        professional_expression_id
    ),
    CONSTRAINT professional_expression_key_uq UNIQUE (
        professional_expression_key
    ),
    CONSTRAINT professional_expression_assertion_uq UNIQUE (
        descriptor_assertion_id
    ),
    CONSTRAINT professional_expression_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES competition.descriptor_assertion (descriptor_assertion_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_expression_text_ck CHECK (
        professional_expression_key =
            lower(btrim(professional_expression_key))
        AND professional_expression_key <> ''
        AND language_tag = btrim(language_tag) AND language_tag <> ''
        AND normalized_phrase = kb.normalize_expression(normalized_phrase)
        AND normalized_phrase <> ''
        AND normalization_rule_code IN (
            'UNICODE_NFC_WHITESPACE_CASE',
            'UNICODE_NFC_WHITESPACE_CASE_PUNCTUATION',
            'SOURCE_DECLARED_IDENTIFIER'
        )
        AND (
            source_span_start IS NULL AND source_span_end IS NULL
            OR source_span_start >= 0 AND source_span_end > source_span_start
        )
        AND NOT project_authored
        AND NOT machine_generated
        AND NOT semantic_inference_used
    )
);

CREATE FUNCTION corpus.enforce_professional_expression_source()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_professional_expression_source$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM competition.descriptor_assertion AS assertion
        WHERE assertion.descriptor_assertion_id = NEW.descriptor_assertion_id
          AND assertion.assertion_type_code <> 'OFFICIAL_STRUCTURED_SCORE'
          AND assertion.raw_phrase IS NOT NULL
          AND assertion.language_tag = NEW.language_tag
          AND kb.normalize_expression(assertion.raw_phrase) =
              NEW.normalized_phrase
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_expression_source_ck',
            MESSAGE = 'professional expression must be a normalized explicit non-score source phrase';
    END IF;

    RETURN NEW;
END
$enforce_professional_expression_source$;

CREATE TRIGGER professional_expression_source_biu
BEFORE INSERT OR UPDATE ON corpus.professional_expression
FOR EACH ROW EXECUTE FUNCTION
    corpus.enforce_professional_expression_source();

CREATE TABLE corpus.professional_mapping_rule (
    professional_mapping_rule_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_mapping_rule_key TEXT NOT NULL,
    rule_version INTEGER NOT NULL,
    language_tag TEXT NOT NULL,
    exact_raw_phrase TEXT NOT NULL,
    normalized_phrase TEXT NOT NULL,
    target_concept_id BIGINT NOT NULL,
    rule_basis_code TEXT NOT NULL,
    source_version_id BIGINT,
    professional_source_snapshot_id BIGINT,
    evidence_locator TEXT NOT NULL,
    mapping_date DATE NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT professional_mapping_rule_pk PRIMARY KEY (
        professional_mapping_rule_id
    ),
    CONSTRAINT professional_mapping_rule_key_version_uq UNIQUE (
        professional_mapping_rule_key, rule_version
    ),
    CONSTRAINT professional_mapping_rule_phrase_version_uq UNIQUE (
        language_tag, normalized_phrase, rule_version
    ),
    CONSTRAINT professional_mapping_rule_target_fk FOREIGN KEY (
        target_concept_id
    ) REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_mapping_rule_source_version_fk FOREIGN KEY (
        source_version_id
    ) REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_mapping_rule_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_mapping_rule_lifecycle_fk FOREIGN KEY (
        lifecycle_status_code
    ) REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_mapping_rule_text_ck CHECK (
        professional_mapping_rule_key =
            lower(btrim(professional_mapping_rule_key))
        AND professional_mapping_rule_key <> ''
        AND rule_version > 0
        AND language_tag = btrim(language_tag) AND language_tag <> ''
        AND exact_raw_phrase = btrim(exact_raw_phrase)
        AND exact_raw_phrase <> ''
        AND normalized_phrase = kb.normalize_expression(exact_raw_phrase)
        AND normalized_phrase <> ''
        AND rule_basis_code IN (
            'GOVERNED_WCR_ATTRIBUTE', 'GOVERNED_SCA_TERM',
            'APPROVED_PROJECT_LEXICALIZATION',
            'OFFICIAL_SCORESHEET_FIELD',
            'EXPLICIT_SOURCE_DEFINED_DESCRIPTOR_IDENTITY'
        )
        AND num_nonnulls(
            source_version_id, professional_source_snapshot_id
        ) = 1
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
    )
);

CREATE TABLE audit.professional_reviewer_qualification (
    professional_reviewer_qualification_id BIGINT
        GENERATED ALWAYS AS IDENTITY,
    reviewer_id BIGINT NOT NULL,
    qualification_scope_code TEXT NOT NULL,
    source_language_tag TEXT,
    qualification_evidence TEXT NOT NULL,
    verified_on DATE NOT NULL,
    eligible BOOLEAN NOT NULL,
    CONSTRAINT professional_reviewer_qualification_pk PRIMARY KEY (
        professional_reviewer_qualification_id
    ),
    CONSTRAINT professional_reviewer_qualification_scope_uq
        UNIQUE NULLS NOT DISTINCT (
            reviewer_id, qualification_scope_code, source_language_tag
        ),
    CONSTRAINT professional_reviewer_qualification_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_reviewer_qualification_text_ck CHECK (
        qualification_scope_code IN (
            'PROFESSIONAL_COFFEE_SENSORY', 'COMPETITION_JUDGING',
            'SOURCE_LANGUAGE', 'ADJUDICATION'
        )
        AND (
            source_language_tag IS NULL
            OR source_language_tag = btrim(source_language_tag)
               AND source_language_tag <> ''
        )
        AND qualification_evidence = btrim(qualification_evidence)
        AND qualification_evidence <> ''
    )
);

CREATE TABLE audit.professional_review_queue (
    professional_review_queue_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_review_queue_key TEXT NOT NULL,
    professional_expression_id BIGINT NOT NULL,
    queue_reason_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    codex_candidates_present BOOLEAN NOT NULL DEFAULT FALSE,
    qualified_review_required BOOLEAN NOT NULL DEFAULT TRUE,
    queued_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT professional_review_queue_pk PRIMARY KEY (
        professional_review_queue_id
    ),
    CONSTRAINT professional_review_queue_key_uq UNIQUE (
        professional_review_queue_key
    ),
    CONSTRAINT professional_review_queue_expression_reason_uq UNIQUE (
        professional_expression_id, queue_reason_code
    ),
    CONSTRAINT professional_review_queue_expression_fk FOREIGN KEY (
        professional_expression_id
    ) REFERENCES corpus.professional_expression (professional_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_review_queue_text_ck CHECK (
        professional_review_queue_key =
            lower(btrim(professional_review_queue_key))
        AND professional_review_queue_key <> ''
        AND queue_reason_code IN (
            'COMPOSITE_REFERENCE', 'METAPHOR', 'QUALIFIER',
            'MULTI_TARGET', 'MULTILINGUAL', 'SOURCE_LOCAL', 'AMBIGUOUS',
            'CONFLICTING_ASSERTIONS', 'OUTSIDE_ONTOLOGY', 'OTHER_REVIEWED'
        )
        AND lifecycle_status_code IN (
            'QUEUED', 'IN_REVIEW', 'ADJUDICATION', 'COMPLETE', 'BLOCKED'
        )
        AND qualified_review_required
    )
);

CREATE TABLE corpus.professional_label_decision (
    professional_label_decision_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_label_decision_key TEXT NOT NULL,
    professional_expression_id BIGINT NOT NULL,
    decision_version INTEGER NOT NULL,
    supersedes_decision_id BIGINT,
    label_disposition_code TEXT NOT NULL,
    decision_method_code TEXT NOT NULL,
    professional_mapping_rule_id BIGINT,
    independent_qualified_reviewer_count INTEGER NOT NULL,
    adjudicator_present BOOLEAN NOT NULL,
    expert_review_complete BOOLEAN NOT NULL,
    candidate_only BOOLEAN NOT NULL,
    decision_status_code TEXT NOT NULL,
    provenance_complete BOOLEAN NOT NULL,
    decision_basis TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT professional_label_decision_pk PRIMARY KEY (
        professional_label_decision_id
    ),
    CONSTRAINT professional_label_decision_key_uq UNIQUE (
        professional_label_decision_key
    ),
    CONSTRAINT professional_label_decision_expression_version_uq UNIQUE (
        professional_expression_id, decision_version
    ),
    CONSTRAINT professional_label_decision_supersedes_uq UNIQUE (
        supersedes_decision_id
    ),
    CONSTRAINT professional_label_decision_expression_fk FOREIGN KEY (
        professional_expression_id
    ) REFERENCES corpus.professional_expression (professional_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_decision_supersedes_fk FOREIGN KEY (
        supersedes_decision_id
    ) REFERENCES corpus.professional_label_decision (
        professional_label_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_decision_rule_fk FOREIGN KEY (
        professional_mapping_rule_id
    ) REFERENCES corpus.professional_mapping_rule (
        professional_mapping_rule_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_decision_text_ck CHECK (
        professional_label_decision_key =
            lower(btrim(professional_label_decision_key))
        AND professional_label_decision_key <> ''
        AND decision_version > 0
        AND label_disposition_code IN (
            'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET',
            'RANGE_LEVEL_TARGET', 'SOURCE_LOCAL_TARGET',
            'AMBIGUOUS_TARGET', 'CONTRADICTORY_TARGET', 'UNRESOLVED',
            'ABSTAIN', 'OUTSIDE_ONTOLOGY'
        )
        AND decision_method_code IN (
            'LEVEL_ONE_DETERMINISTIC', 'QUALIFIED_REVIEW',
            'CODEX_CANDIDATE', 'SOURCE_RETAINED_CANDIDATE'
        )
        AND independent_qualified_reviewer_count >= 0
        AND decision_status_code IN (
            'CANDIDATE', 'FINAL', 'SUPERSEDED', 'REJECTED'
        )
        AND decision_basis = btrim(decision_basis)
        AND decision_basis <> ''
    ),
    CONSTRAINT professional_label_decision_method_ck CHECK (
        decision_method_code = 'LEVEL_ONE_DETERMINISTIC'
        AND label_disposition_code = 'EXACT_CANONICAL_TARGET'
        AND professional_mapping_rule_id IS NOT NULL
        AND independent_qualified_reviewer_count = 0
        AND NOT adjudicator_present
        AND NOT expert_review_complete
        AND NOT candidate_only
        AND decision_status_code = 'FINAL'
        AND provenance_complete
        OR decision_method_code = 'QUALIFIED_REVIEW'
        AND professional_mapping_rule_id IS NULL
        AND independent_qualified_reviewer_count >= 2
        AND adjudicator_present
        AND expert_review_complete
        AND NOT candidate_only
        AND decision_status_code = 'FINAL'
        AND provenance_complete
        OR decision_method_code IN (
            'CODEX_CANDIDATE', 'SOURCE_RETAINED_CANDIDATE'
        )
        AND independent_qualified_reviewer_count = 0
        AND NOT adjudicator_present
        AND NOT expert_review_complete
        AND candidate_only
        AND decision_status_code = 'CANDIDATE'
    ),
    CONSTRAINT professional_label_decision_version_ck CHECK (
        (decision_version = 1) = (supersedes_decision_id IS NULL)
    )
);

CREATE FUNCTION corpus.enforce_professional_label_decision_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_professional_label_decision_lineage$
DECLARE
    predecessor corpus.professional_label_decision%ROWTYPE;
BEGIN
    IF NEW.supersedes_decision_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO predecessor
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id = NEW.supersedes_decision_id;

    IF predecessor.professional_label_decision_id IS NULL
       OR predecessor.professional_expression_id IS DISTINCT FROM
          NEW.professional_expression_id
       OR predecessor.decision_version <> NEW.decision_version - 1
       OR predecessor.decided_at > NEW.decided_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_label_decision_lineage_ck',
            MESSAGE = 'label decision supersession must use the prior version of the same expression';
    END IF;

    RETURN NEW;
END
$enforce_professional_label_decision_lineage$;

CREATE TRIGGER professional_label_decision_lineage_biu
BEFORE INSERT OR UPDATE ON corpus.professional_label_decision
FOR EACH ROW EXECUTE FUNCTION
    corpus.enforce_professional_label_decision_lineage();

CREATE TABLE audit.professional_label_review (
    professional_label_review_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_label_decision_id BIGINT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    reviewer_role_code TEXT NOT NULL,
    review_outcome_code TEXT NOT NULL,
    review_evidence TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT professional_label_review_pk PRIMARY KEY (
        professional_label_review_id
    ),
    CONSTRAINT professional_label_review_reviewer_uq UNIQUE (
        professional_label_decision_id, reviewer_id
    ),
    CONSTRAINT professional_label_review_decision_fk FOREIGN KEY (
        professional_label_decision_id
    ) REFERENCES corpus.professional_label_decision (
        professional_label_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_review_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_review_text_ck CHECK (
        reviewer_role_code IN ('INDEPENDENT_REVIEWER', 'ADJUDICATOR')
        AND review_outcome_code IN (
            'ACCEPT', 'REVISE', 'ABSTAIN', 'REJECT', 'CONFLICT'
        )
        AND review_evidence = btrim(review_evidence)
        AND review_evidence <> ''
    )
);

CREATE FUNCTION audit.validate_professional_label_review()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_professional_label_review$
DECLARE
    affected_decision_id BIGINT;
    selected corpus.professional_label_decision%ROWTYPE;
    independent_count BIGINT;
    adjudicator_count BIGINT;
    ineligible_count BIGINT;
    expression_language_tag TEXT;
BEGIN
    affected_decision_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.professional_label_decision_id
        ELSE NEW.professional_label_decision_id
    END;

    SELECT * INTO selected
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id = affected_decision_id;

    IF selected.professional_label_decision_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT expression.language_tag INTO expression_language_tag
    FROM corpus.professional_expression AS expression
    WHERE expression.professional_expression_id =
          selected.professional_expression_id;

    SELECT
        count(*) FILTER (
            WHERE review.reviewer_role_code = 'INDEPENDENT_REVIEWER'
        ),
        count(*) FILTER (
            WHERE review.reviewer_role_code = 'ADJUDICATOR'
        ),
        count(*) FILTER (
            WHERE NOT EXISTS (
                SELECT 1
                FROM audit.professional_reviewer_qualification AS qualification
                WHERE qualification.reviewer_id = review.reviewer_id
                  AND qualification.eligible
                  AND qualification.qualification_scope_code IN (
                      'PROFESSIONAL_COFFEE_SENSORY',
                      'COMPETITION_JUDGING', 'ADJUDICATION'
                  )
            )
            OR lower(split_part(expression_language_tag, '-', 1)) <> 'en'
               AND NOT EXISTS (
                    SELECT 1
                    FROM audit.professional_reviewer_qualification AS language_qualification
                    WHERE language_qualification.reviewer_id =
                          review.reviewer_id
                      AND language_qualification.eligible
                      AND language_qualification.qualification_scope_code =
                          'SOURCE_LANGUAGE'
                      AND lower(split_part(
                          language_qualification.source_language_tag,
                          '-', 1
                      )) = lower(split_part(expression_language_tag, '-', 1))
               )
        )
    INTO independent_count, adjudicator_count, ineligible_count
    FROM audit.professional_label_review AS review
    WHERE review.professional_label_decision_id = affected_decision_id;

    IF selected.decision_method_code = 'QUALIFIED_REVIEW' THEN
        IF independent_count < 2
           OR adjudicator_count <> 1
           OR ineligible_count <> 0
           OR independent_count IS DISTINCT FROM
              selected.independent_qualified_reviewer_count
           OR selected.adjudicator_present IS NOT TRUE
           OR selected.expert_review_complete IS NOT TRUE THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'professional_label_qualified_review_ck',
                MESSAGE = 'qualified decision requires two eligible independent reviewers and one eligible adjudicator';
        END IF;
    ELSIF independent_count <> 0 OR adjudicator_count <> 0 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_label_nonexpert_review_ck',
            MESSAGE = 'deterministic and candidate decisions cannot claim expert-review rows';
    END IF;

    RETURN NULL;
END
$validate_professional_label_review$;

CREATE CONSTRAINT TRIGGER professional_label_decision_review_aiu
AFTER INSERT OR UPDATE ON corpus.professional_label_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_professional_label_review();

CREATE CONSTRAINT TRIGGER professional_label_review_aiud
AFTER INSERT OR UPDATE OR DELETE ON audit.professional_label_review
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_professional_label_review();

CREATE TABLE corpus.professional_label_target (
    professional_label_decision_id BIGINT NOT NULL,
    target_ordinal INTEGER NOT NULL,
    concept_id BIGINT,
    association_range_id BIGINT,
    target_role_code TEXT NOT NULL,
    CONSTRAINT professional_label_target_pk PRIMARY KEY (
        professional_label_decision_id, target_ordinal
    ),
    CONSTRAINT professional_label_target_decision_concept_uq
        UNIQUE NULLS NOT DISTINCT (
        professional_label_decision_id, concept_id
    ),
    CONSTRAINT professional_label_target_decision_range_uq
        UNIQUE NULLS NOT DISTINCT (
        professional_label_decision_id, association_range_id
    ),
    CONSTRAINT professional_label_target_decision_fk FOREIGN KEY (
        professional_label_decision_id
    ) REFERENCES corpus.professional_label_decision (
        professional_label_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_target_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_target_range_fk FOREIGN KEY (
        association_range_id
    ) REFERENCES corpus.association_range (association_range_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_label_target_shape_ck CHECK (
        target_ordinal > 0
        AND num_nonnulls(concept_id, association_range_id) = 1
        AND target_role_code IN (
            'PRIMARY', 'ADDITIONAL', 'RANGE', 'CONFLICTING_ALTERNATIVE'
        )
    )
);

CREATE FUNCTION corpus.validate_professional_label_targets()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_professional_label_targets$
DECLARE
    affected_decision_id BIGINT;
    selected corpus.professional_label_decision%ROWTYPE;
    concept_count BIGINT;
    range_count BIGINT;
BEGIN
    affected_decision_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.professional_label_decision_id
        ELSE NEW.professional_label_decision_id
    END;

    SELECT * INTO selected
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id = affected_decision_id;

    IF selected.professional_label_decision_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT
        count(*) FILTER (WHERE concept_id IS NOT NULL),
        count(*) FILTER (WHERE association_range_id IS NOT NULL)
    INTO concept_count, range_count
    FROM corpus.professional_label_target
    WHERE professional_label_decision_id = affected_decision_id;

    IF selected.decision_method_code = 'LEVEL_ONE_DETERMINISTIC'
       AND NOT EXISTS (
            SELECT 1
            FROM corpus.professional_label_target AS target
            JOIN corpus.professional_mapping_rule AS rule
              ON rule.professional_mapping_rule_id =
                 selected.professional_mapping_rule_id
             AND rule.target_concept_id = target.concept_id
            WHERE target.professional_label_decision_id =
                  affected_decision_id
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_label_deterministic_target_ck',
            MESSAGE = 'deterministic decision target must equal the governed mapping-rule target';
    END IF;

    IF selected.label_disposition_code = 'EXACT_CANONICAL_TARGET'
       AND (concept_count <> 1 OR range_count <> 0)
       OR selected.label_disposition_code = 'MULTI_CANONICAL_TARGET'
       AND (concept_count < 2 OR range_count <> 0)
       OR selected.label_disposition_code = 'RANGE_LEVEL_TARGET'
       AND (range_count < 1 OR concept_count <> 0)
       OR selected.label_disposition_code IN (
            'AMBIGUOUS_TARGET', 'CONTRADICTORY_TARGET'
       ) AND (concept_count < 2 OR range_count <> 0)
       OR selected.label_disposition_code IN (
            'SOURCE_LOCAL_TARGET', 'UNRESOLVED', 'ABSTAIN',
            'OUTSIDE_ONTOLOGY'
       ) AND (concept_count <> 0 OR range_count <> 0) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_label_target_cardinality_ck',
            MESSAGE = 'label target cardinality must match its controlled disposition';
    END IF;

    RETURN NULL;
END
$validate_professional_label_targets$;

CREATE CONSTRAINT TRIGGER professional_label_decision_targets_aiu
AFTER INSERT OR UPDATE ON corpus.professional_label_decision
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_professional_label_targets();

CREATE CONSTRAINT TRIGGER professional_label_targets_aiud
AFTER INSERT OR UPDATE OR DELETE ON corpus.professional_label_target
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_professional_label_targets();

CREATE TABLE corpus.professional_coassertion_event (
    professional_coassertion_event_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_coassertion_event_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    judge_observation_id BIGINT,
    panel_id BIGINT,
    left_descriptor_assertion_id BIGINT NOT NULL,
    right_descriptor_assertion_id BIGINT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    coassertion_method_code TEXT NOT NULL,
    absence_is_negative BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT professional_coassertion_event_pk PRIMARY KEY (
        professional_coassertion_event_id
    ),
    CONSTRAINT professional_coassertion_event_key_uq UNIQUE (
        professional_coassertion_event_key
    ),
    CONSTRAINT professional_coassertion_event_pair_uq UNIQUE (
        left_descriptor_assertion_id, right_descriptor_assertion_id,
        coassertion_method_code
    ),
    CONSTRAINT professional_coassertion_event_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_coassertion_event_observation_fk FOREIGN KEY (
        judge_observation_id
    ) REFERENCES competition.judge_observation (judge_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_coassertion_event_panel_fk FOREIGN KEY (panel_id)
        REFERENCES competition.panel (panel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_coassertion_event_left_fk FOREIGN KEY (
        left_descriptor_assertion_id
    ) REFERENCES competition.descriptor_assertion (descriptor_assertion_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_coassertion_event_right_fk FOREIGN KEY (
        right_descriptor_assertion_id
    ) REFERENCES competition.descriptor_assertion (descriptor_assertion_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_coassertion_event_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_coassertion_event_text_ck CHECK (
        professional_coassertion_event_key =
            lower(btrim(professional_coassertion_event_key))
        AND professional_coassertion_event_key <> ''
        AND left_descriptor_assertion_id < right_descriptor_assertion_id
        AND coassertion_method_code IN (
            'SAME_JUDGE_OBSERVATION', 'SAME_PANEL_CONSENSUS',
            'SAME_ORGANIZER_AGGREGATE'
        )
        AND NOT absence_is_negative
    )
);

CREATE FUNCTION corpus.enforce_professional_coassertion_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_professional_coassertion_lineage$
DECLARE
    left_assertion competition.descriptor_assertion%ROWTYPE;
    right_assertion competition.descriptor_assertion%ROWTYPE;
BEGIN
    SELECT * INTO left_assertion
    FROM competition.descriptor_assertion
    WHERE descriptor_assertion_id = NEW.left_descriptor_assertion_id;
    SELECT * INTO right_assertion
    FROM competition.descriptor_assertion
    WHERE descriptor_assertion_id = NEW.right_descriptor_assertion_id;

    IF left_assertion.preparation_service_id IS DISTINCT FROM
           NEW.preparation_service_id
       OR right_assertion.preparation_service_id IS DISTINCT FROM
           NEW.preparation_service_id
       OR left_assertion.professional_source_snapshot_id IS DISTINCT FROM
           NEW.professional_source_snapshot_id
       OR right_assertion.professional_source_snapshot_id IS DISTINCT FROM
           NEW.professional_source_snapshot_id
       OR left_assertion.evidence_tier_code NOT IN ('P1', 'P2')
       OR right_assertion.evidence_tier_code NOT IN ('P1', 'P2')
       OR left_assertion.assertion_type_code = 'OFFICIAL_STRUCTURED_SCORE'
       OR right_assertion.assertion_type_code = 'OFFICIAL_STRUCTURED_SCORE'
       OR NEW.coassertion_method_code = 'SAME_JUDGE_OBSERVATION'
          AND (
              NEW.judge_observation_id IS NULL
              OR left_assertion.judge_observation_id IS DISTINCT FROM
                 NEW.judge_observation_id
              OR right_assertion.judge_observation_id IS DISTINCT FROM
                 NEW.judge_observation_id
          )
       OR NEW.coassertion_method_code = 'SAME_PANEL_CONSENSUS'
          AND (
              NEW.panel_id IS NULL
              OR left_assertion.panel_id IS DISTINCT FROM NEW.panel_id
              OR right_assertion.panel_id IS DISTINCT FROM NEW.panel_id
          )
       OR NEW.coassertion_method_code = 'SAME_ORGANIZER_AGGREGATE'
          AND (
              left_assertion.organizer_published_note_id IS NULL
              OR left_assertion.organizer_published_note_id IS DISTINCT FROM
                 right_assertion.organizer_published_note_id
          ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_coassertion_lineage_ck',
            MESSAGE = 'co-assertion events require two explicit P1/P2 descriptors from the same governed source event';
    END IF;

    RETURN NEW;
END
$enforce_professional_coassertion_lineage$;

CREATE TRIGGER professional_coassertion_lineage_biu
BEFORE INSERT OR UPDATE ON corpus.professional_coassertion_event
FOR EACH ROW EXECUTE FUNCTION
    corpus.enforce_professional_coassertion_lineage();

CREATE TABLE audit.round3k_acquisition_batch (
    acquisition_batch_id BIGINT GENERATED ALWAYS AS IDENTITY,
    acquisition_batch_key TEXT NOT NULL,
    batch_sequence INTEGER NOT NULL,
    source_family_key TEXT,
    series_id BIGINT,
    adapter_source_kind TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    access_method_code TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    observed_core_record_delta BIGINT NOT NULL,
    model_eligible_record_delta BIGINT NOT NULL,
    descriptor_assertion_delta BIGINT NOT NULL,
    direct_c1_or_source_roast_delta BIGINT NOT NULL,
    new_p1_source_family BOOLEAN NOT NULL,
    new_official_series BOOLEAN NOT NULL,
    material_data_progress BOOLEAN NOT NULL,
    adapter_status_code TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    CONSTRAINT round3k_acquisition_batch_pk PRIMARY KEY (
        acquisition_batch_id
    ),
    CONSTRAINT round3k_acquisition_batch_key_uq UNIQUE (
        acquisition_batch_key
    ),
    CONSTRAINT round3k_acquisition_batch_sequence_uq UNIQUE (batch_sequence),
    CONSTRAINT round3k_acquisition_batch_family_fk FOREIGN KEY (
        source_family_key
    ) REFERENCES evidence.source_family (source_family_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3k_acquisition_batch_series_fk FOREIGN KEY (series_id)
        REFERENCES competition.series (series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3k_acquisition_batch_text_ck CHECK (
        acquisition_batch_key = lower(btrim(acquisition_batch_key))
        AND acquisition_batch_key <> ''
        AND batch_sequence > 0
        AND adapter_source_kind IN (
            'OFFICIAL_HTML_RESULTS', 'OFFICIAL_AUCTION_HTML',
            'OFFICIAL_PDF_CATALOG', 'OFFICIAL_PDF_RESULTS',
            'CSV_EXPORT', 'TSV_EXPORT', 'XLSX_SCORE_EXPORT',
            'JSON_API_PAYLOAD', 'AWARD_FORCE_AUTHORIZED_EXPORT',
            'COMPETITION_PLATFORM_AUTHORIZED_EXPORT',
            'PERMITTED_TRANSCRIPT'
        )
        AND lifecycle_status_code IN (
            'REGISTERED', 'IN_PROGRESS', 'COMPLETE', 'BLOCKED'
        )
        AND access_method_code IN (
            'MANUAL_DOWNLOAD', 'PERMITTED_HTTP', 'OFFICIAL_API',
            'AUTHORIZED_EXPORT', 'LOCAL_USER_SUPPLIED'
        )
        AND (completed_at IS NULL OR completed_at >= started_at)
        AND (lifecycle_status_code IN ('COMPLETE', 'BLOCKED')) =
            (completed_at IS NOT NULL)
        AND observed_core_record_delta >= 0
        AND model_eligible_record_delta >= 0
        AND model_eligible_record_delta <= observed_core_record_delta
        AND descriptor_assertion_delta >= 0
        AND direct_c1_or_source_roast_delta >= 0
        AND material_data_progress = (
            observed_core_record_delta >= 100
            OR descriptor_assertion_delta >= 500
            OR direct_c1_or_source_roast_delta >= 25
            OR new_p1_source_family
            OR new_official_series
        )
        AND adapter_status_code IN (
            'NOT_RUN', 'PASS', 'BLOCKED_QUALITY', 'BLOCKED_RIGHTS',
            'BLOCKED_ACCESS', 'BLOCKED_TERMS', 'STRUCTURAL_TEST_ONLY'
        )
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
    )
);

CREATE TABLE audit.round3k_acquisition_outcome (
    acquisition_outcome_id BIGINT GENERATED ALWAYS AS IDENTITY,
    acquisition_outcome_key TEXT NOT NULL,
    acquisition_batch_id BIGINT NOT NULL,
    official_archive_search_complete BOOLEAN NOT NULL,
    official_items_inspected BIGINT NOT NULL,
    public_yield_pilot_complete BOOLEAN NOT NULL,
    bulk_access_route_examined BOOLEAN NOT NULL,
    rights_state_code TEXT NOT NULL,
    access_state_code TEXT NOT NULL,
    targeted_no_material_gain_attempt_count INTEGER NOT NULL,
    source_saturation_state_code TEXT NOT NULL,
    stop_reason_code TEXT NOT NULL,
    outcome_note TEXT NOT NULL,
    CONSTRAINT round3k_acquisition_outcome_pk PRIMARY KEY (
        acquisition_outcome_id
    ),
    CONSTRAINT round3k_acquisition_outcome_key_uq UNIQUE (
        acquisition_outcome_key
    ),
    CONSTRAINT round3k_acquisition_outcome_batch_uq UNIQUE (
        acquisition_batch_id
    ),
    CONSTRAINT round3k_acquisition_outcome_batch_fk FOREIGN KEY (
        acquisition_batch_id
    ) REFERENCES audit.round3k_acquisition_batch (acquisition_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3k_acquisition_outcome_text_ck CHECK (
        acquisition_outcome_key = lower(btrim(acquisition_outcome_key))
        AND acquisition_outcome_key <> ''
        AND official_items_inspected >= 0
        AND rights_state_code IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND access_state_code IN (
            'PUBLIC', 'AUTHORIZED_PRIVATE', 'REQUEST_REQUIRED',
            'BLOCKED_ACCESS', 'BLOCKED_RIGHTS', 'BLOCKED_TERMS'
        )
        AND targeted_no_material_gain_attempt_count BETWEEN 0 AND 2
        AND source_saturation_state_code IN (
            'NOT_EVALUATED', 'ACTIVE', 'REQUEST_REQUIRED', 'SATURATED'
        )
        AND (
            source_saturation_state_code <> 'SATURATED'
            OR official_archive_search_complete
               AND public_yield_pilot_complete
               AND bulk_access_route_examined
               AND targeted_no_material_gain_attempt_count = 2
        )
        AND stop_reason_code IN (
            'CONTINUE', 'COMPLETE', 'BLOCKED_RIGHTS', 'BLOCKED_ACCESS',
            'BLOCKED_QUALITY', 'REQUEST_REQUIRED', 'SATURATED'
        )
        AND outcome_note = btrim(outcome_note) AND outcome_note <> ''
    )
);

CREATE TABLE audit.professional_duplicate_group (
    professional_duplicate_group_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_duplicate_group_key TEXT NOT NULL,
    duplicate_type_code TEXT NOT NULL,
    decision_basis_code TEXT NOT NULL,
    reviewed BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT professional_duplicate_group_pk PRIMARY KEY (
        professional_duplicate_group_id
    ),
    CONSTRAINT professional_duplicate_group_key_uq UNIQUE (
        professional_duplicate_group_key
    ),
    CONSTRAINT professional_duplicate_group_text_ck CHECK (
        professional_duplicate_group_key =
            lower(btrim(professional_duplicate_group_key))
        AND professional_duplicate_group_key <> ''
        AND duplicate_type_code IN (
            'EXACT_RECORD_DUPLICATE', 'MIRROR_SOURCE',
            'AUCTION_ROASTER_REPUBLICATION', 'CROSS_CATEGORY_SAME_COFFEE',
            'OTHER_REVIEWED'
        )
        AND decision_basis_code IN (
            'SOURCE_IDENTIFIER', 'SOURCE_HASH', 'OFFICIAL_LINK',
            'QUALIFIED_REVIEW', 'DETERMINISTIC_COMPOSITE_KEY'
        )
    )
);

CREATE TABLE audit.professional_duplicate_group_member (
    professional_duplicate_group_id BIGINT NOT NULL,
    member_ordinal INTEGER NOT NULL,
    preparation_service_id BIGINT,
    professional_source_snapshot_id BIGINT,
    member_role_code TEXT NOT NULL,
    CONSTRAINT professional_duplicate_group_member_pk PRIMARY KEY (
        professional_duplicate_group_id, member_ordinal
    ),
    CONSTRAINT professional_duplicate_group_member_service_uq
        UNIQUE NULLS NOT DISTINCT (
        professional_duplicate_group_id, preparation_service_id
    ),
    CONSTRAINT professional_duplicate_group_member_snapshot_uq
        UNIQUE NULLS NOT DISTINCT (
        professional_duplicate_group_id, professional_source_snapshot_id
    ),
    CONSTRAINT professional_duplicate_group_member_group_fk FOREIGN KEY (
        professional_duplicate_group_id
    ) REFERENCES audit.professional_duplicate_group (
        professional_duplicate_group_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_duplicate_group_member_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_duplicate_group_member_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_duplicate_group_member_shape_ck CHECK (
        member_ordinal > 0
        AND num_nonnulls(
            preparation_service_id, professional_source_snapshot_id
        ) = 1
        AND member_role_code IN ('CANONICAL', 'DUPLICATE', 'MIRROR')
    )
);

CREATE FUNCTION audit.validate_professional_duplicate_group()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_professional_duplicate_group$
DECLARE
    affected_group_id BIGINT;
    selected audit.professional_duplicate_group%ROWTYPE;
    member_count BIGINT;
    canonical_count BIGINT;
    service_count BIGINT;
    snapshot_count BIGINT;
BEGIN
    affected_group_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.professional_duplicate_group_id
        ELSE NEW.professional_duplicate_group_id
    END;

    SELECT * INTO selected
    FROM audit.professional_duplicate_group
    WHERE professional_duplicate_group_id = affected_group_id;

    IF selected.professional_duplicate_group_id IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT
        count(*),
        count(*) FILTER (WHERE member_role_code = 'CANONICAL'),
        count(*) FILTER (WHERE preparation_service_id IS NOT NULL),
        count(*) FILTER (
            WHERE professional_source_snapshot_id IS NOT NULL
        )
    INTO member_count, canonical_count, service_count, snapshot_count
    FROM audit.professional_duplicate_group_member
    WHERE professional_duplicate_group_id = affected_group_id;

    IF member_count < 2 OR canonical_count <> 1
       OR selected.duplicate_type_code = 'MIRROR_SOURCE'
          AND snapshot_count <> member_count
       OR selected.duplicate_type_code <> 'MIRROR_SOURCE'
          AND service_count <> member_count THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_duplicate_group_shape_ck',
            MESSAGE = 'duplicate group requires one canonical and at least one same-domain duplicate or mirror';
    END IF;

    RETURN NULL;
END
$validate_professional_duplicate_group$;

CREATE CONSTRAINT TRIGGER professional_duplicate_group_aiu
AFTER INSERT OR UPDATE ON audit.professional_duplicate_group
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_professional_duplicate_group();

CREATE CONSTRAINT TRIGGER professional_duplicate_group_member_aiud
AFTER INSERT OR UPDATE OR DELETE
ON audit.professional_duplicate_group_member
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_professional_duplicate_group();

CREATE TABLE audit.professional_repeat_audit (
    preparation_service_id BIGINT NOT NULL,
    repeats_preparation_service_id BIGINT NOT NULL,
    repeat_relationship_code TEXT NOT NULL,
    relationship_status_code TEXT NOT NULL,
    evidence_basis TEXT NOT NULL,
    CONSTRAINT professional_repeat_audit_pk PRIMARY KEY (
        preparation_service_id
    ),
    CONSTRAINT professional_repeat_audit_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_repeat_audit_parent_fk FOREIGN KEY (
        repeats_preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_repeat_audit_text_ck CHECK (
        repeat_relationship_code IN (
            'LATER_ROUND', 'CROSS_CATEGORY', 'AUCTION_REPUBLICATION',
            'ROASTER_REPUBLICATION', 'OTHER_REVIEWED'
        )
        AND relationship_status_code IN (
            'SOURCE_DECLARED', 'REVIEWED_CONFIRMED', 'REJECTED', 'UNRESOLVED'
        )
        AND evidence_basis = btrim(evidence_basis)
        AND evidence_basis <> ''
    )
);

CREATE FUNCTION audit.enforce_professional_repeat_audit()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_professional_repeat_audit$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM competition.preparation_service AS service
        WHERE service.preparation_service_id = NEW.preparation_service_id
          AND service.repeat_of_preparation_service_id =
              NEW.repeats_preparation_service_id
          AND service.repeat_relationship_code =
              NEW.repeat_relationship_code
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_repeat_audit_lineage_ck',
            MESSAGE = 'repeat audit must reproduce the explicit preparation-service repeat relationship';
    END IF;

    RETURN NEW;
END
$enforce_professional_repeat_audit$;

CREATE TRIGGER professional_repeat_audit_biu
BEFORE INSERT OR UPDATE ON audit.professional_repeat_audit
FOR EACH ROW EXECUTE FUNCTION audit.enforce_professional_repeat_audit();

CREATE TABLE ml.professional_training_candidate (
    professional_training_candidate_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_training_candidate_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    task_code TEXT NOT NULL,
    professional_rights_decision_id BIGINT NOT NULL,
    candidate_status_code TEXT NOT NULL,
    provenance_complete BOOLEAN NOT NULL,
    rights_complete BOOLEAN NOT NULL,
    integrity_complete BOOLEAN NOT NULL,
    included BOOLEAN NOT NULL,
    exclusion_reason_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT professional_training_candidate_pk PRIMARY KEY (
        professional_training_candidate_id
    ),
    CONSTRAINT professional_training_candidate_key_uq UNIQUE (
        professional_training_candidate_key
    ),
    CONSTRAINT professional_training_candidate_service_task_uq UNIQUE (
        preparation_service_id, task_code
    ),
    CONSTRAINT professional_training_candidate_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_training_candidate_rights_fk FOREIGN KEY (
        professional_rights_decision_id
    ) REFERENCES evidence.professional_rights_decision (
        professional_rights_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_training_candidate_text_ck CHECK (
        professional_training_candidate_key =
            lower(btrim(professional_training_candidate_key))
        AND professional_training_candidate_key <> ''
        AND task_code IN (
            'DESCRIPTOR_NORMALIZATION', 'DESCRIPTOR_ASSOCIATION',
            'C0_C1_CONTEXT', 'ADAPTIVE_CANDIDATE_RESEARCH'
        )
        AND candidate_status_code IN (
            'CANDIDATE', 'ELIGIBLE', 'EXCLUDED', 'BLOCKED_RIGHTS',
            'BLOCKED_PROVENANCE', 'BLOCKED_INTEGRITY'
        )
        AND (
            exclusion_reason_code IS NULL
            OR exclusion_reason_code IN (
                'RIGHTS', 'PROVENANCE', 'DUPLICATE', 'MIRROR',
                'LABEL', 'FRESH_PREPARATION', 'AUXILIARY_TIER',
                'MILK_AUXILIARY', 'OTHER_GOVERNED'
            )
        )
        AND included = (
            candidate_status_code = 'ELIGIBLE'
            AND provenance_complete AND rights_complete
            AND integrity_complete
        )
        AND (included = (exclusion_reason_code IS NULL))
    )
);

CREATE FUNCTION ml.validate_professional_training_candidate()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_professional_training_candidate$
DECLARE
    selected_rights evidence.professional_rights_decision%ROWTYPE;
BEGIN
    SELECT * INTO selected_rights
    FROM evidence.professional_rights_decision
    WHERE professional_rights_decision_id =
          NEW.professional_rights_decision_id;

    IF NEW.included AND (
        selected_rights.internal_research_use <> 'ALLOWED'
        OR selected_rights.model_research_use <> 'ALLOWED'
        OR EXISTS (
            SELECT 1
            FROM evidence.professional_rights_decision AS successor
            WHERE successor.supersedes_decision_id =
                  selected_rights.professional_rights_decision_id
        )
        OR NOT EXISTS (
            SELECT 1
            FROM competition.preparation_service_evidence AS service_evidence
            WHERE service_evidence.preparation_service_id =
                  NEW.preparation_service_id
              AND service_evidence.professional_source_snapshot_id =
                  selected_rights.professional_source_snapshot_id
        )
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_training_candidate_rights_ck',
            MESSAGE = 'included training candidate requires current affirmative internal and model-research rights on a linked source snapshot';
    END IF;

    IF NEW.included
       AND NEW.task_code = 'DESCRIPTOR_NORMALIZATION'
       AND NOT EXISTS (
            SELECT 1
            FROM competition.descriptor_assertion AS assertion
            JOIN corpus.professional_expression AS expression
              ON expression.descriptor_assertion_id =
                 assertion.descriptor_assertion_id
            JOIN corpus.professional_label_decision AS decision
              ON decision.professional_expression_id =
                 expression.professional_expression_id
            WHERE assertion.preparation_service_id =
                  NEW.preparation_service_id
              AND decision.decision_status_code = 'FINAL'
              AND NOT decision.candidate_only
              AND NOT EXISTS (
                    SELECT 1
                    FROM corpus.professional_label_decision AS successor
                    WHERE successor.supersedes_decision_id =
                          decision.professional_label_decision_id
              )
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_training_candidate_label_ck',
            MESSAGE = 'descriptor-normalization candidate requires a current governed final professional label';
    END IF;

    RETURN NULL;
END
$validate_professional_training_candidate$;

CREATE CONSTRAINT TRIGGER professional_training_candidate_aiu
AFTER INSERT OR UPDATE ON ml.professional_training_candidate
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    ml.validate_professional_training_candidate();

CREATE TABLE ml.professional_split_plan (
    professional_split_plan_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_split_plan_key TEXT NOT NULL,
    plan_version INTEGER NOT NULL,
    deterministic_rule_version TEXT NOT NULL,
    random_row_split BOOLEAN NOT NULL DEFAULT FALSE,
    lifecycle_status_code TEXT NOT NULL,
    CONSTRAINT professional_split_plan_pk PRIMARY KEY (
        professional_split_plan_id
    ),
    CONSTRAINT professional_split_plan_key_version_uq UNIQUE (
        professional_split_plan_key, plan_version
    ),
    CONSTRAINT professional_split_plan_text_ck CHECK (
        professional_split_plan_key =
            lower(btrim(professional_split_plan_key))
        AND professional_split_plan_key <> ''
        AND plan_version > 0
        AND deterministic_rule_version =
            btrim(deterministic_rule_version)
        AND deterministic_rule_version <> ''
        AND NOT random_row_split
        AND lifecycle_status_code IN ('CANDIDATE', 'FROZEN', 'SUPERSEDED')
    )
);

CREATE TABLE ml.professional_split_group (
    professional_split_group_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_split_plan_id BIGINT NOT NULL,
    split_group_kind_code TEXT NOT NULL,
    split_group_key TEXT NOT NULL,
    source_basis TEXT NOT NULL,
    CONSTRAINT professional_split_group_pk PRIMARY KEY (
        professional_split_group_id
    ),
    CONSTRAINT professional_split_group_plan_kind_key_uq UNIQUE (
        professional_split_plan_id, split_group_kind_code, split_group_key
    ),
    CONSTRAINT professional_split_group_plan_fk FOREIGN KEY (
        professional_split_plan_id
    ) REFERENCES ml.professional_split_plan (professional_split_plan_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_split_group_text_ck CHECK (
        split_group_kind_code IN (
            'COMPETITION_FAMILY', 'COMPETITION_YEAR', 'COFFEE_IDENTITY',
            'LOT', 'ROASTER', 'DUPLICATE_GROUP', 'REPEAT_GROUP',
            'PREPARATION', 'C1'
        )
        AND split_group_key = lower(btrim(split_group_key))
        AND split_group_key <> ''
        AND source_basis = btrim(source_basis) AND source_basis <> ''
    )
);

CREATE TABLE ml.professional_split_group_member (
    professional_split_group_id BIGINT NOT NULL,
    professional_training_candidate_id BIGINT NOT NULL,
    CONSTRAINT professional_split_group_member_pk PRIMARY KEY (
        professional_split_group_id, professional_training_candidate_id
    ),
    CONSTRAINT professional_split_group_member_group_fk FOREIGN KEY (
        professional_split_group_id
    ) REFERENCES ml.professional_split_group (professional_split_group_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_split_group_member_candidate_fk FOREIGN KEY (
        professional_training_candidate_id
    ) REFERENCES ml.professional_training_candidate (
        professional_training_candidate_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE ml.professional_split_assignment (
    professional_split_plan_id BIGINT NOT NULL,
    professional_training_candidate_id BIGINT NOT NULL,
    partition_code TEXT NOT NULL,
    assignment_key TEXT NOT NULL,
    deterministic_assignment_sha256 TEXT NOT NULL,
    CONSTRAINT professional_split_assignment_pk PRIMARY KEY (
        professional_split_plan_id, professional_training_candidate_id
    ),
    CONSTRAINT professional_split_assignment_key_uq UNIQUE (assignment_key),
    CONSTRAINT professional_split_assignment_plan_fk FOREIGN KEY (
        professional_split_plan_id
    ) REFERENCES ml.professional_split_plan (professional_split_plan_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_split_assignment_candidate_fk FOREIGN KEY (
        professional_training_candidate_id
    ) REFERENCES ml.professional_training_candidate (
        professional_training_candidate_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_split_assignment_text_ck CHECK (
        partition_code IN ('TRAIN', 'DEV', 'TEST', 'HELD_OUT')
        AND assignment_key = lower(btrim(assignment_key))
        AND assignment_key <> ''
        AND deterministic_assignment_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE audit.round3k_artifact_registry (
    round3k_artifact_key TEXT NOT NULL,
    artifact_type_code TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    model_weight_artifact BOOLEAN NOT NULL,
    embedding_artifact BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT round3k_artifact_registry_pk PRIMARY KEY (
        round3k_artifact_key
    ),
    CONSTRAINT round3k_artifact_registry_text_ck CHECK (
        round3k_artifact_key = lower(btrim(round3k_artifact_key))
        AND round3k_artifact_key <> ''
        AND artifact_type_code IN (
            'SOURCE_MANIFEST', 'SOURCE_HASHES', 'NORMALIZED_INVENTORY',
            'RIGHTS_INVENTORY', 'DUPLICATE_REPEAT_INVENTORY',
            'LABEL_INVENTORY', 'SPLIT_CANDIDATE',
            'TRAINING_CORPUS_CANDIDATE_MANIFEST'
        )
        AND artifact_path = btrim(artifact_path) AND artifact_path <> ''
        AND artifact_sha256 ~ '^[0-9a-f]{64}$'
        AND NOT model_weight_artifact
        AND NOT embedding_artifact
    )
);

CREATE FUNCTION audit.prevent_round3k_model_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3k_model_run$
BEGIN
    IF upper(COALESCE(NEW.run_configuration ->> 'round', '')) IN (
        '3K', 'ROUND3K'
    ) OR COALESCE(
        (NEW.run_configuration ->> 'professional_competition_corpus')::BOOLEAN,
        FALSE
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3k_model_run_prohibited_ck',
            MESSAGE = 'Round 3K freezes corpus candidates and cannot create model runs';
    END IF;
    RETURN NEW;
END
$prevent_round3k_model_run$;

CREATE TRIGGER round3k_model_run_prohibited_biu
BEFORE INSERT OR UPDATE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3k_model_run();

CREATE INDEX professional_expression_phrase_ix
    ON corpus.professional_expression (language_tag, normalized_phrase);
CREATE INDEX professional_label_decision_disposition_ix
    ON corpus.professional_label_decision (
        decision_status_code, label_disposition_code, candidate_only
    );
CREATE INDEX professional_coassertion_service_ix
    ON corpus.professional_coassertion_event (
        preparation_service_id, coassertion_method_code
    );
CREATE INDEX professional_training_candidate_status_ix
    ON ml.professional_training_candidate (
        task_code, included, candidate_status_code
    );
CREATE INDEX professional_split_group_kind_ix
    ON ml.professional_split_group (
        professional_split_plan_id, split_group_kind_code
    );

COMMENT ON TABLE corpus.professional_label_decision IS
    'Multi-disposition professional mapping decision. Software candidates remain candidate_only until deterministic governed identity or qualified review establishes a final label.';
COMMENT ON TABLE corpus.professional_coassertion_event IS
    'Explicit positive P1/P2 descriptor pairing; descriptor absence is never encoded as a negative association.';
COMMENT ON TABLE ml.professional_training_candidate IS
    'Task-specific, rights-bound corpus candidate metadata only. No model fitting or evaluation occurs in Round 3K.';

COMMIT;
