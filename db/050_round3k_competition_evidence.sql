\set ON_ERROR_STOP on

-- Round 3K professional source, rights, panel, observation, score, and
-- descriptor evidence. Competition identities and preparation services live in
-- migration 049; this layer keeps every sensory claim attached to a governed
-- source snapshot and never treats public visibility as model-use permission.

BEGIN;

ALTER TABLE evidence.source_family
    DROP CONSTRAINT source_family_text_ck,
    DROP CONSTRAINT source_family_type_ck;

ALTER TABLE evidence.source_family
    ADD CONSTRAINT source_family_text_ck CHECK (
        source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND family_name = btrim(family_name) AND family_name <> ''
        AND canonical_origin_key = lower(btrim(canonical_origin_key))
        AND canonical_origin_key <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
        AND introduced_round IN ('3G', '3H', '3K')
    ),
    ADD CONSTRAINT source_family_type_ck CHECK (
        family_type IN (
            'COFFEE_SENSORY', 'CONSUMER_STUDY',
            'BILINGUAL_LEXICAL', 'CONTEMPORARY_LANGUAGE',
            'FORMAL_STANDARD', 'OTHER_RESEARCH',
            'PROFESSIONAL_COMPETITION'
        )
    );

CREATE TABLE evidence.professional_source (
    professional_source_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_source_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    title TEXT NOT NULL,
    official_owner TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    source_type_code TEXT NOT NULL,
    evidence_tier_scope TEXT[] NOT NULL,
    access_state_code TEXT NOT NULL,
    automation_permission_state_code TEXT NOT NULL,
    data_custodian TEXT NOT NULL,
    independence_basis TEXT NOT NULL,
    admitted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT professional_source_pk PRIMARY KEY (professional_source_id),
    CONSTRAINT professional_source_key_uq UNIQUE (professional_source_key),
    CONSTRAINT professional_source_key_family_uq UNIQUE (
        professional_source_id, source_family_key
    ),
    CONSTRAINT professional_source_family_fk FOREIGN KEY (source_family_key)
        REFERENCES evidence.source_family (source_family_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_source_text_ck CHECK (
        professional_source_key = lower(btrim(professional_source_key))
        AND professional_source_key <> ''
        AND title = btrim(title) AND title <> ''
        AND official_owner = btrim(official_owner) AND official_owner <> ''
        AND canonical_url = btrim(canonical_url) AND canonical_url <> ''
        AND data_custodian = btrim(data_custodian) AND data_custodian <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
    ),
    CONSTRAINT professional_source_type_ck CHECK (
        source_type_code IN (
            'OFFICIAL_HTML_RESULTS', 'OFFICIAL_AUCTION_LOTS',
            'OFFICIAL_PDF_CATALOG', 'OFFICIAL_PDF_RESULTS',
            'OFFICIAL_CSV_EXPORT', 'OFFICIAL_TSV_EXPORT',
            'OFFICIAL_XLSX_EXPORT', 'OFFICIAL_JSON_API',
            'AUTHORIZED_AWARD_FORCE_EXPORT',
            'AUTHORIZED_COMPETITION_PLATFORM_EXPORT',
            'PERMITTED_TRANSCRIPT', 'PROTOCOL_OR_SCORESHEET'
        )
    ),
    CONSTRAINT professional_source_evidence_tier_ck CHECK (
        cardinality(evidence_tier_scope) > 0
        AND evidence_tier_scope <@ ARRAY['P0', 'P1', 'P2', 'P3', 'P4']::TEXT[]
    ),
    CONSTRAINT professional_source_access_ck CHECK (
        access_state_code IN (
            'PUBLIC', 'AUTHORIZED_PRIVATE', 'REQUEST_REQUIRED',
            'BLOCKED_ACCESS', 'BLOCKED_RIGHTS', 'BLOCKED_TERMS'
        )
        AND automation_permission_state_code IN (
            'PERMITTED', 'MANUAL_ONLY', 'NOT_APPLICABLE',
            'NOT_REVIEWED', 'PROHIBITED'
        )
        AND (
            NOT admitted
            OR access_state_code IN ('PUBLIC', 'AUTHORIZED_PRIVATE')
               AND automation_permission_state_code <> 'PROHIBITED'
        )
    )
);

CREATE TABLE evidence.professional_source_series (
    professional_source_id BIGINT NOT NULL,
    series_id BIGINT NOT NULL,
    source_role_code TEXT NOT NULL,
    CONSTRAINT professional_source_series_pk PRIMARY KEY (
        professional_source_id, series_id
    ),
    CONSTRAINT professional_source_series_source_fk FOREIGN KEY (
        professional_source_id
    ) REFERENCES evidence.professional_source (professional_source_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_source_series_series_fk FOREIGN KEY (series_id)
        REFERENCES competition.series (series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_source_series_role_ck CHECK (
        source_role_code IN (
            'PRIMARY_RESULTS', 'AUCTION_LOTS', 'RULES', 'SCORESHEET',
            'ORGANIZER_EXPORT', 'MIRROR_DISCOVERY_ONLY'
        )
    )
);

CREATE TABLE evidence.professional_source_snapshot (
    professional_source_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_source_snapshot_key TEXT NOT NULL,
    professional_source_id BIGINT NOT NULL,
    source_family_key TEXT NOT NULL,
    exact_version TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    immutable_locator TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL,
    access_method_code TEXT NOT NULL,
    automated_access_compliance_code TEXT NOT NULL,
    lawfully_acquired_for_internal_research BOOLEAN NOT NULL,
    source_record_count BIGINT NOT NULL,
    admitted BOOLEAN NOT NULL DEFAULT FALSE,
    snapshot_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT professional_source_snapshot_pk PRIMARY KEY (
        professional_source_snapshot_id
    ),
    CONSTRAINT professional_source_snapshot_key_uq UNIQUE (
        professional_source_snapshot_key
    ),
    CONSTRAINT professional_source_snapshot_source_fk FOREIGN KEY (
        professional_source_id, source_family_key
    ) REFERENCES evidence.professional_source (
        professional_source_id, source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_source_snapshot_text_ck CHECK (
        professional_source_snapshot_key =
            lower(btrim(professional_source_snapshot_key))
        AND professional_source_snapshot_key <> ''
        AND exact_version = btrim(exact_version) AND exact_version <> ''
        AND immutable_locator = btrim(immutable_locator)
        AND immutable_locator <> ''
        AND snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND source_record_count >= 0
        AND jsonb_typeof(snapshot_metadata) = 'object'
    ),
    CONSTRAINT professional_source_snapshot_access_ck CHECK (
        access_method_code IN (
            'MANUAL_DOWNLOAD', 'PERMITTED_HTTP', 'OFFICIAL_API',
            'AUTHORIZED_EXPORT', 'LOCAL_USER_SUPPLIED'
        )
        AND automated_access_compliance_code IN (
            'PERMITTED', 'MANUAL_ONLY', 'NOT_APPLICABLE', 'UNKNOWN'
        )
        AND (
            NOT admitted
            OR lawfully_acquired_for_internal_research
               AND automated_access_compliance_code <> 'UNKNOWN'
        )
    )
);

CREATE TABLE evidence.professional_source_file (
    professional_source_file_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_source_file_key TEXT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    filename TEXT NOT NULL,
    file_role_code TEXT NOT NULL,
    official_locator TEXT NOT NULL,
    local_path TEXT,
    declared_sha256 TEXT NOT NULL,
    verified_sha256 TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    row_count BIGINT NOT NULL,
    field_count INTEGER NOT NULL,
    hash_verified BOOLEAN NOT NULL,
    retention_state_code TEXT NOT NULL,
    public_redistribution_allowed BOOLEAN NOT NULL,
    source_owner TEXT NOT NULL,
    source_url TEXT NOT NULL,
    license_or_terms TEXT NOT NULL,
    attribution_requirement TEXT NOT NULL,
    modification_status TEXT NOT NULL,
    CONSTRAINT professional_source_file_pk PRIMARY KEY (
        professional_source_file_id
    ),
    CONSTRAINT professional_source_file_key_uq UNIQUE (
        professional_source_file_key
    ),
    CONSTRAINT professional_source_file_snapshot_uq UNIQUE (
        professional_source_file_id, professional_source_snapshot_id
    ),
    CONSTRAINT professional_source_file_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_source_file_text_ck CHECK (
        professional_source_file_key =
            lower(btrim(professional_source_file_key))
        AND professional_source_file_key <> ''
        AND filename = btrim(filename) AND filename <> ''
        AND official_locator = btrim(official_locator)
        AND official_locator <> ''
        AND (local_path IS NULL OR (
            local_path = btrim(local_path) AND local_path <> ''
        ))
        AND declared_sha256 ~ '^[0-9a-f]{64}$'
        AND verified_sha256 ~ '^[0-9a-f]{64}$'
        AND source_owner = btrim(source_owner) AND source_owner <> ''
        AND source_url = btrim(source_url) AND source_url <> ''
        AND license_or_terms = btrim(license_or_terms)
        AND license_or_terms <> ''
        AND attribution_requirement = btrim(attribution_requirement)
        AND attribution_requirement <> ''
        AND modification_status = btrim(modification_status)
        AND modification_status <> ''
    ),
    CONSTRAINT professional_source_file_shape_ck CHECK (
        file_role_code IN (
            'RAW_OFFICIAL', 'SOURCE_MANIFEST', 'HASH_MANIFEST',
            'GOVERNED_DERIVED', 'REVISION_METADATA'
        )
        AND retention_state_code IN (
            'LOCAL_RETAINED', 'HASH_AND_LOCATOR_ONLY', 'EXTERNAL_ONLY'
        )
        AND file_size_bytes >= 0 AND row_count >= 0 AND field_count >= 0
        AND (NOT hash_verified OR declared_sha256 = verified_sha256)
        AND (retention_state_code = 'LOCAL_RETAINED') = (local_path IS NOT NULL)
    )
);

CREATE TABLE evidence.professional_rights_decision (
    professional_rights_decision_id BIGINT GENERATED ALWAYS AS IDENTITY,
    professional_rights_decision_key TEXT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    public_results_use TEXT NOT NULL,
    public_descriptor_use TEXT NOT NULL,
    internal_research_use TEXT NOT NULL,
    public_derived_release TEXT NOT NULL,
    model_research_use TEXT NOT NULL,
    commercial_model_use TEXT NOT NULL,
    decision_authority_code TEXT NOT NULL,
    evidence_basis TEXT NOT NULL,
    decided_on DATE NOT NULL,
    supersedes_decision_id BIGINT,
    CONSTRAINT professional_rights_decision_pk PRIMARY KEY (
        professional_rights_decision_id
    ),
    CONSTRAINT professional_rights_decision_key_uq UNIQUE (
        professional_rights_decision_key
    ),
    CONSTRAINT professional_rights_decision_successor_uq UNIQUE (
        supersedes_decision_id
    ),
    CONSTRAINT professional_rights_decision_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_rights_decision_supersedes_fk FOREIGN KEY (
        supersedes_decision_id
    ) REFERENCES evidence.professional_rights_decision (
        professional_rights_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT professional_rights_decision_text_ck CHECK (
        professional_rights_decision_key =
            lower(btrim(professional_rights_decision_key))
        AND professional_rights_decision_key <> ''
        AND evidence_basis = btrim(evidence_basis) AND evidence_basis <> ''
        AND supersedes_decision_id IS DISTINCT FROM
            professional_rights_decision_id
    ),
    CONSTRAINT professional_rights_decision_states_ck CHECK (
        public_results_use IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND public_descriptor_use IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND internal_research_use IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND public_derived_release IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND model_research_use IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND commercial_model_use IN (
            'ALLOWED', 'DENIED', 'PENDING', 'NOT_APPLICABLE'
        )
        AND decision_authority_code IN (
            'RIGHTS_HOLDER', 'ORGANIZER_TERMS', 'PUBLIC_LICENSE',
            'PROJECT_RIGHTS_REVIEW', 'LEGAL_REVIEW'
        )
    )
);

CREATE FUNCTION evidence.enforce_professional_rights_supersession()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_professional_rights_supersession$
DECLARE
    predecessor evidence.professional_rights_decision%ROWTYPE;
BEGIN
    IF NEW.supersedes_decision_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO predecessor
    FROM evidence.professional_rights_decision
    WHERE professional_rights_decision_id = NEW.supersedes_decision_id;

    IF predecessor.professional_rights_decision_id IS NULL
       OR predecessor.professional_source_snapshot_id IS DISTINCT FROM
          NEW.professional_source_snapshot_id
       OR predecessor.decided_on > NEW.decided_on THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'professional_rights_supersession_ck',
            MESSAGE = 'rights supersession must retain the source snapshot and cannot predate its predecessor';
    END IF;

    RETURN NEW;
END
$enforce_professional_rights_supersession$;

CREATE TRIGGER professional_rights_supersession_biu
BEFORE INSERT OR UPDATE ON evidence.professional_rights_decision
FOR EACH ROW EXECUTE FUNCTION
    evidence.enforce_professional_rights_supersession();

CREATE TABLE competition.preparation_service_evidence (
    preparation_service_evidence_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_service_evidence_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    professional_source_file_id BIGINT,
    evidence_role_code TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    explicit_fresh_preparation_evidence BOOLEAN NOT NULL,
    CONSTRAINT preparation_service_evidence_pk PRIMARY KEY (
        preparation_service_evidence_id
    ),
    CONSTRAINT preparation_service_evidence_key_uq UNIQUE (
        preparation_service_evidence_key
    ),
    CONSTRAINT preparation_service_evidence_fact_uq UNIQUE (
        preparation_service_id, professional_source_snapshot_id,
        evidence_role_code, source_locator
    ),
    CONSTRAINT preparation_service_evidence_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_service_evidence_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_service_evidence_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_service_evidence_file_snapshot_fk FOREIGN KEY (
        professional_source_file_id, professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id, professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT preparation_service_evidence_text_ck CHECK (
        preparation_service_evidence_key =
            lower(btrim(preparation_service_evidence_key))
        AND preparation_service_evidence_key <> ''
        AND source_locator = btrim(source_locator)
        AND source_locator <> ''
        AND evidence_role_code IN (
            'PREPARATION_PROTOCOL', 'RULE_VERSION', 'SCORESHEET_VERSION',
            'ENTRY_METADATA', 'OFFICIAL_RESULT', 'ORGANIZER_EXPORT'
        )
    )
);

CREATE TABLE competition.panel (
    panel_id BIGINT GENERATED ALWAYS AS IDENTITY,
    panel_key TEXT NOT NULL,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    round_id BIGINT NOT NULL,
    panel_type_code TEXT NOT NULL,
    official_panel_key TEXT,
    professional_source_snapshot_id BIGINT NOT NULL,
    CONSTRAINT panel_pk PRIMARY KEY (panel_id),
    CONSTRAINT panel_key_uq UNIQUE (panel_key),
    CONSTRAINT panel_round_uq UNIQUE (panel_id, round_id),
    CONSTRAINT panel_series_fk FOREIGN KEY (series_id)
        REFERENCES competition.series (series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_edition_fk FOREIGN KEY (edition_id)
        REFERENCES competition.edition (edition_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_category_fk FOREIGN KEY (category_id)
        REFERENCES competition.category (category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_round_fk FOREIGN KEY (round_id)
        REFERENCES competition.round (round_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_text_ck CHECK (
        panel_key = lower(btrim(panel_key)) AND panel_key <> ''
        AND (official_panel_key IS NULL OR (
            official_panel_key = btrim(official_panel_key)
            AND official_panel_key <> ''
        ))
        AND panel_type_code IN (
            'SENSORY_JURY', 'HEAD_JUDGE_PANEL', 'PRODUCTION_CUPPING_PANEL',
            'ORGANIZER_AGGREGATE_PANEL'
        )
    )
);

CREATE TABLE competition.judge (
    judge_id BIGINT GENERATED ALWAYS AS IDENTITY,
    judge_key TEXT NOT NULL,
    pseudonymous_label TEXT NOT NULL,
    identity_scope_code TEXT NOT NULL,
    certification_state_code TEXT NOT NULL,
    certification_version TEXT,
    judge_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT judge_pk PRIMARY KEY (judge_id),
    CONSTRAINT judge_key_uq UNIQUE (judge_key),
    CONSTRAINT judge_text_ck CHECK (
        judge_key = lower(btrim(judge_key)) AND judge_key <> ''
        AND pseudonymous_label = btrim(pseudonymous_label)
        AND pseudonymous_label <> ''
        AND pseudonymous_label !~ '@'
        AND (certification_version IS NULL OR (
            certification_version = btrim(certification_version)
            AND certification_version <> ''
        ))
        AND jsonb_typeof(judge_metadata) = 'object'
    ),
    CONSTRAINT judge_state_ck CHECK (
        identity_scope_code IN ('PSEUDONYMOUS', 'ANONYMOUS')
        AND certification_state_code IN (
            'CURRENT', 'EXPIRED', 'NOT_REPORTED', 'NOT_APPLICABLE'
        )
    )
);

CREATE TABLE competition.panel_membership (
    panel_membership_id BIGINT GENERATED ALWAYS AS IDENTITY,
    panel_membership_key TEXT NOT NULL,
    panel_id BIGINT NOT NULL,
    judge_id BIGINT NOT NULL,
    judge_role_code TEXT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    CONSTRAINT panel_membership_pk PRIMARY KEY (panel_membership_id),
    CONSTRAINT panel_membership_key_uq UNIQUE (panel_membership_key),
    CONSTRAINT panel_membership_fact_uq UNIQUE (panel_id, judge_id),
    CONSTRAINT panel_membership_panel_fk FOREIGN KEY (panel_id)
        REFERENCES competition.panel (panel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_membership_judge_fk FOREIGN KEY (judge_id)
        REFERENCES competition.judge (judge_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_membership_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT panel_membership_text_ck CHECK (
        panel_membership_key = lower(btrim(panel_membership_key))
        AND panel_membership_key <> ''
        AND judge_role_code IN (
            'SENSORY_JUDGE', 'HEAD_JUDGE', 'SHADOW_JUDGE',
            'PRODUCTION_CUPPING_JUDGE'
        )
    )
);

CREATE TABLE competition.judge_observation (
    judge_observation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    judge_observation_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    panel_id BIGINT NOT NULL,
    judge_id BIGINT,
    observation_type_code TEXT NOT NULL,
    official_confirmed BOOLEAN NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    professional_source_file_id BIGINT,
    source_observation_key TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    observation_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT judge_observation_pk PRIMARY KEY (judge_observation_id),
    CONSTRAINT judge_observation_key_uq UNIQUE (judge_observation_key),
    CONSTRAINT judge_observation_fact_uq UNIQUE NULLS NOT DISTINCT (
        preparation_service_id, panel_id, judge_id, source_observation_key
    ),
    CONSTRAINT judge_observation_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT judge_observation_panel_fk FOREIGN KEY (panel_id)
        REFERENCES competition.panel (panel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT judge_observation_judge_fk FOREIGN KEY (judge_id)
        REFERENCES competition.judge (judge_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT judge_observation_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT judge_observation_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT judge_observation_file_snapshot_fk FOREIGN KEY (
        professional_source_file_id, professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id, professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT judge_observation_text_ck CHECK (
        judge_observation_key = lower(btrim(judge_observation_key))
        AND judge_observation_key <> ''
        AND source_observation_key = btrim(source_observation_key)
        AND source_observation_key <> ''
        AND source_locator = btrim(source_locator) AND source_locator <> ''
        AND jsonb_typeof(observation_metadata) = 'object'
    ),
    CONSTRAINT judge_observation_type_ck CHECK (
        observation_type_code IN (
            'JUDGE', 'HEAD_JUDGE', 'PANEL_CONSENSUS_SOURCE',
            'PRODUCTION_CUPPING'
        )
        AND official_confirmed
        AND (
            observation_type_code = 'PANEL_CONSENSUS_SOURCE'
            AND judge_id IS NULL
            OR observation_type_code <> 'PANEL_CONSENSUS_SOURCE'
               AND judge_id IS NOT NULL
        )
    )
);

CREATE TABLE competition.structured_score (
    structured_score_id BIGINT GENERATED ALWAYS AS IDENTITY,
    structured_score_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    judge_observation_id BIGINT,
    panel_id BIGINT,
    evidence_tier_code TEXT NOT NULL,
    score_dimension_key TEXT NOT NULL,
    source_native_field_label TEXT NOT NULL,
    numeric_value NUMERIC,
    text_value TEXT,
    scale_min NUMERIC,
    scale_max NUMERIC,
    professional_source_snapshot_id BIGINT NOT NULL,
    professional_source_file_id BIGINT,
    source_locator TEXT NOT NULL,
    CONSTRAINT structured_score_pk PRIMARY KEY (structured_score_id),
    CONSTRAINT structured_score_key_uq UNIQUE (structured_score_key),
    CONSTRAINT structured_score_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT structured_score_observation_fk FOREIGN KEY (
        judge_observation_id
    ) REFERENCES competition.judge_observation (judge_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT structured_score_panel_fk FOREIGN KEY (panel_id)
        REFERENCES competition.panel (panel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT structured_score_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT structured_score_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT structured_score_file_snapshot_fk FOREIGN KEY (
        professional_source_file_id, professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id, professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT structured_score_text_ck CHECK (
        structured_score_key = lower(btrim(structured_score_key))
        AND structured_score_key <> ''
        AND score_dimension_key = lower(btrim(score_dimension_key))
        AND score_dimension_key <> ''
        AND source_native_field_label = btrim(source_native_field_label)
        AND source_native_field_label <> ''
        AND (text_value IS NULL OR (
            text_value = btrim(text_value) AND text_value <> ''
        ))
        AND source_locator = btrim(source_locator) AND source_locator <> ''
    ),
    CONSTRAINT structured_score_shape_ck CHECK (
        evidence_tier_code IN ('P1', 'P2')
        AND num_nonnulls(numeric_value, text_value) = 1
        AND (
            numeric_value IS NULL
            AND scale_min IS NULL AND scale_max IS NULL
            OR numeric_value IS NOT NULL
               AND scale_min IS NOT NULL AND scale_max IS NOT NULL
               AND scale_min <= numeric_value
               AND numeric_value <= scale_max
        )
        AND (
            evidence_tier_code = 'P1' AND judge_observation_id IS NOT NULL
            OR evidence_tier_code = 'P2' AND judge_observation_id IS NULL
        )
    )
);

CREATE TABLE competition.competitor_declared_note (
    competitor_declared_note_id BIGINT GENERATED ALWAYS AS IDENTITY,
    competitor_declared_note_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    professional_source_file_id BIGINT,
    language_tag TEXT NOT NULL,
    raw_text TEXT,
    raw_text_sha256 TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    CONSTRAINT competitor_declared_note_pk PRIMARY KEY (
        competitor_declared_note_id
    ),
    CONSTRAINT competitor_declared_note_key_uq UNIQUE (
        competitor_declared_note_key
    ),
    CONSTRAINT competitor_declared_note_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competitor_declared_note_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competitor_declared_note_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competitor_declared_note_file_snapshot_fk FOREIGN KEY (
        professional_source_file_id, professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id, professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competitor_declared_note_text_ck CHECK (
        competitor_declared_note_key =
            lower(btrim(competitor_declared_note_key))
        AND competitor_declared_note_key <> ''
        AND language_tag = btrim(language_tag) AND language_tag <> ''
        AND (raw_text IS NULL OR (raw_text = btrim(raw_text) AND raw_text <> ''))
        AND raw_text_sha256 ~ '^[0-9a-f]{64}$'
        AND (
            raw_text IS NULL
            OR raw_text_sha256 = audit.round3i_utf8_sha256(raw_text)
        )
        AND source_locator = btrim(source_locator) AND source_locator <> ''
    )
);

CREATE TABLE competition.organizer_published_note (
    organizer_published_note_id BIGINT GENERATED ALWAYS AS IDENTITY,
    organizer_published_note_key TEXT NOT NULL,
    preparation_service_id BIGINT,
    edition_id BIGINT NOT NULL,
    evidence_tier_code TEXT NOT NULL,
    note_role_code TEXT NOT NULL,
    professional_source_snapshot_id BIGINT NOT NULL,
    professional_source_file_id BIGINT,
    language_tag TEXT NOT NULL,
    raw_text TEXT,
    raw_text_sha256 TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    CONSTRAINT organizer_published_note_pk PRIMARY KEY (
        organizer_published_note_id
    ),
    CONSTRAINT organizer_published_note_key_uq UNIQUE (
        organizer_published_note_key
    ),
    CONSTRAINT organizer_published_note_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT organizer_published_note_edition_fk FOREIGN KEY (edition_id)
        REFERENCES competition.edition (edition_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT organizer_published_note_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT organizer_published_note_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT organizer_published_note_file_snapshot_fk FOREIGN KEY (
        professional_source_file_id, professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id, professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT organizer_published_note_text_ck CHECK (
        organizer_published_note_key =
            lower(btrim(organizer_published_note_key))
        AND organizer_published_note_key <> ''
        AND language_tag = btrim(language_tag) AND language_tag <> ''
        AND (raw_text IS NULL OR (raw_text = btrim(raw_text) AND raw_text <> ''))
        AND raw_text_sha256 ~ '^[0-9a-f]{64}$'
        AND (
            raw_text IS NULL
            OR raw_text_sha256 = audit.round3i_utf8_sha256(raw_text)
        )
        AND source_locator = btrim(source_locator) AND source_locator <> ''
    ),
    CONSTRAINT organizer_published_note_role_ck CHECK (
        evidence_tier_code IN ('P2', 'P4')
        AND note_role_code IN (
            'JURY_NOTE', 'OFFICIAL_LOT_DESCRIPTION',
            'OFFICIAL_AGGREGATE_PROFILE', 'ORGANIZER_MARKETING'
        )
        AND (
            evidence_tier_code = 'P2'
            AND note_role_code <> 'ORGANIZER_MARKETING'
            OR evidence_tier_code = 'P4'
               AND note_role_code = 'ORGANIZER_MARKETING'
        )
    )
);

CREATE TABLE competition.descriptor_assertion (
    descriptor_assertion_id BIGINT GENERATED ALWAYS AS IDENTITY,
    descriptor_assertion_key TEXT NOT NULL,
    preparation_service_id BIGINT NOT NULL,
    judge_observation_id BIGINT,
    panel_id BIGINT,
    structured_score_id BIGINT,
    competitor_declared_note_id BIGINT,
    organizer_published_note_id BIGINT,
    assertion_type_code TEXT NOT NULL,
    evidence_tier_code TEXT NOT NULL,
    language_tag TEXT NOT NULL,
    raw_phrase TEXT,
    raw_phrase_sha256 TEXT NOT NULL,
    source_defined_descriptor_key TEXT,
    professional_source_snapshot_id BIGINT NOT NULL,
    professional_source_file_id BIGINT,
    source_locator TEXT NOT NULL,
    derived_from_judge_observations BOOLEAN NOT NULL DEFAULT FALSE,
    semantic_inference_used BOOLEAN NOT NULL DEFAULT FALSE,
    assertion_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT descriptor_assertion_pk PRIMARY KEY (descriptor_assertion_id),
    CONSTRAINT descriptor_assertion_key_uq UNIQUE (descriptor_assertion_key),
    CONSTRAINT descriptor_assertion_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_observation_fk FOREIGN KEY (
        judge_observation_id
    ) REFERENCES competition.judge_observation (judge_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_panel_fk FOREIGN KEY (panel_id)
        REFERENCES competition.panel (panel_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_score_fk FOREIGN KEY (structured_score_id)
        REFERENCES competition.structured_score (structured_score_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_competitor_note_fk FOREIGN KEY (
        competitor_declared_note_id
    ) REFERENCES competition.competitor_declared_note (
        competitor_declared_note_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_organizer_note_fk FOREIGN KEY (
        organizer_published_note_id
    ) REFERENCES competition.organizer_published_note (
        organizer_published_note_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_snapshot_fk FOREIGN KEY (
        professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_snapshot (
        professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_file_snapshot_fk FOREIGN KEY (
        professional_source_file_id, professional_source_snapshot_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id, professional_source_snapshot_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_text_ck CHECK (
        descriptor_assertion_key = lower(btrim(descriptor_assertion_key))
        AND descriptor_assertion_key <> ''
        AND language_tag = btrim(language_tag) AND language_tag <> ''
        AND (raw_phrase IS NULL OR (
            raw_phrase = btrim(raw_phrase) AND raw_phrase <> ''
        ))
        AND raw_phrase_sha256 ~ '^[0-9a-f]{64}$'
        AND (
            raw_phrase IS NULL
            OR raw_phrase_sha256 = audit.round3i_utf8_sha256(raw_phrase)
        )
        AND (source_defined_descriptor_key IS NULL OR (
            source_defined_descriptor_key =
                btrim(source_defined_descriptor_key)
            AND source_defined_descriptor_key <> ''
        ))
        AND source_locator = btrim(source_locator) AND source_locator <> ''
        AND jsonb_typeof(assertion_metadata) = 'object'
    ),
    CONSTRAINT descriptor_assertion_type_ck CHECK (
        assertion_type_code IN (
            'OFFICIAL_JUDGE_DESCRIPTOR',
            'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR',
            'OFFICIAL_AGGREGATED_DESCRIPTOR',
            'OFFICIAL_STRUCTURED_SCORE',
            'COMPETITOR_DECLARED_DESCRIPTOR',
            'ROASTER_SUBMITTED_DESCRIPTOR',
            'ORGANIZER_MARKETING_DESCRIPTION'
        )
        AND evidence_tier_code IN ('P1', 'P2', 'P3', 'P4')
        AND NOT semantic_inference_used
    ),
    CONSTRAINT descriptor_assertion_lineage_shape_ck CHECK (
        assertion_type_code = 'OFFICIAL_JUDGE_DESCRIPTOR'
        AND evidence_tier_code = 'P1'
        AND judge_observation_id IS NOT NULL
        AND NOT derived_from_judge_observations
        AND num_nonnulls(
            structured_score_id, competitor_declared_note_id,
            organizer_published_note_id
        ) = 0
        OR assertion_type_code = 'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR'
        AND evidence_tier_code = 'P1'
        AND panel_id IS NOT NULL
        AND judge_observation_id IS NULL
        AND derived_from_judge_observations
        AND num_nonnulls(
            structured_score_id, competitor_declared_note_id,
            organizer_published_note_id
        ) = 0
        OR assertion_type_code = 'OFFICIAL_AGGREGATED_DESCRIPTOR'
        AND evidence_tier_code = 'P2'
        AND organizer_published_note_id IS NOT NULL
        AND judge_observation_id IS NULL
        AND NOT derived_from_judge_observations
        OR assertion_type_code = 'OFFICIAL_STRUCTURED_SCORE'
        AND evidence_tier_code IN ('P1', 'P2')
        AND structured_score_id IS NOT NULL
        AND num_nonnulls(
            competitor_declared_note_id, organizer_published_note_id
        ) = 0
        OR assertion_type_code = 'COMPETITOR_DECLARED_DESCRIPTOR'
        AND evidence_tier_code = 'P3'
        AND competitor_declared_note_id IS NOT NULL
        AND num_nonnulls(
            judge_observation_id, structured_score_id,
            organizer_published_note_id
        ) = 0
        OR assertion_type_code = 'ROASTER_SUBMITTED_DESCRIPTOR'
        AND evidence_tier_code = 'P4'
        AND num_nonnulls(
            judge_observation_id, structured_score_id,
            competitor_declared_note_id, organizer_published_note_id
        ) = 0
        OR assertion_type_code = 'ORGANIZER_MARKETING_DESCRIPTION'
        AND evidence_tier_code = 'P4'
        AND organizer_published_note_id IS NOT NULL
        AND num_nonnulls(
            judge_observation_id, structured_score_id,
            competitor_declared_note_id
        ) = 0
    )
);

CREATE FUNCTION competition.enforce_panel_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_panel_scope$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM competition.category AS category
        JOIN competition.round AS round_record
          ON round_record.series_id = category.series_id
         AND round_record.edition_id = category.edition_id
         AND round_record.rule_version_id = category.rule_version_id
        WHERE category.category_id = NEW.category_id
          AND round_record.round_id = NEW.round_id
          AND category.series_id = NEW.series_id
          AND category.edition_id = NEW.edition_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'competition_panel_scope_ck',
            MESSAGE = 'panel category and round must share the declared series, edition, and rule version';
    END IF;

    RETURN NEW;
END
$enforce_panel_scope$;

CREATE TRIGGER competition_panel_scope_biu
BEFORE INSERT OR UPDATE ON competition.panel
FOR EACH ROW EXECUTE FUNCTION competition.enforce_panel_scope();

CREATE FUNCTION competition.enforce_professional_fact_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_professional_fact_lineage$
DECLARE
    selected_service competition.preparation_service%ROWTYPE;
    selected_panel competition.panel%ROWTYPE;
    selected_observation competition.judge_observation%ROWTYPE;
BEGIN
    IF TG_TABLE_NAME = 'judge_observation' THEN
        SELECT * INTO selected_service
        FROM competition.preparation_service
        WHERE preparation_service_id = NEW.preparation_service_id;
        SELECT * INTO selected_panel
        FROM competition.panel
        WHERE panel_id = NEW.panel_id;

        IF selected_service.preparation_service_id IS NULL
           OR selected_panel.panel_id IS NULL
           OR selected_panel.series_id IS DISTINCT FROM selected_service.series_id
           OR selected_panel.edition_id IS DISTINCT FROM selected_service.edition_id
           OR selected_panel.category_id IS DISTINCT FROM selected_service.category_id
           OR selected_panel.round_id IS DISTINCT FROM selected_service.round_id
           OR NEW.judge_id IS NOT NULL AND NOT EXISTS (
                SELECT 1
                FROM competition.panel_membership AS membership
                WHERE membership.panel_id = NEW.panel_id
                  AND membership.judge_id = NEW.judge_id
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'competition_judge_observation_lineage_ck',
                MESSAGE = 'judge observation must use the service panel and a recorded panel member';
        END IF;
    ELSIF TG_TABLE_NAME = 'structured_score' THEN
        IF NEW.judge_observation_id IS NOT NULL THEN
            SELECT * INTO selected_observation
            FROM competition.judge_observation
            WHERE judge_observation_id = NEW.judge_observation_id;

            IF selected_observation.preparation_service_id IS DISTINCT FROM
                  NEW.preparation_service_id
               OR selected_observation.professional_source_snapshot_id
                  IS DISTINCT FROM NEW.professional_source_snapshot_id
               OR NEW.panel_id IS NOT NULL
                  AND NEW.panel_id IS DISTINCT FROM selected_observation.panel_id THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    CONSTRAINT = 'competition_structured_score_lineage_ck',
                    MESSAGE = 'P1 structured score must retain its observation service, panel, and snapshot';
            END IF;
        ELSIF NEW.panel_id IS NOT NULL AND NOT EXISTS (
            SELECT 1
            FROM competition.preparation_service AS service
            JOIN competition.panel AS panel_record
              ON panel_record.series_id = service.series_id
             AND panel_record.edition_id = service.edition_id
             AND panel_record.category_id = service.category_id
             AND panel_record.round_id = service.round_id
            WHERE service.preparation_service_id = NEW.preparation_service_id
              AND panel_record.panel_id = NEW.panel_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'competition_structured_score_lineage_ck',
                MESSAGE = 'aggregate structured score panel must match its preparation service';
        END IF;
    ELSIF TG_TABLE_NAME = 'organizer_published_note' THEN
        IF NEW.preparation_service_id IS NOT NULL
           AND NOT EXISTS (
                SELECT 1
                FROM competition.preparation_service AS service
                WHERE service.preparation_service_id = NEW.preparation_service_id
                  AND service.edition_id = NEW.edition_id
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'competition_organizer_note_service_ck',
                MESSAGE = 'organizer note edition must match its linked preparation service';
        END IF;
    END IF;

    RETURN NEW;
END
$enforce_professional_fact_lineage$;

CREATE TRIGGER competition_judge_observation_lineage_biu
BEFORE INSERT OR UPDATE ON competition.judge_observation
FOR EACH ROW EXECUTE FUNCTION competition.enforce_professional_fact_lineage();

CREATE TRIGGER competition_structured_score_lineage_biu
BEFORE INSERT OR UPDATE ON competition.structured_score
FOR EACH ROW EXECUTE FUNCTION competition.enforce_professional_fact_lineage();

CREATE TRIGGER competition_organizer_note_service_biu
BEFORE INSERT OR UPDATE ON competition.organizer_published_note
FOR EACH ROW EXECUTE FUNCTION competition.enforce_professional_fact_lineage();

CREATE FUNCTION competition.enforce_descriptor_assertion_source_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_descriptor_assertion_source_lineage$
BEGIN
    IF NEW.judge_observation_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM competition.judge_observation AS observation
        WHERE observation.judge_observation_id = NEW.judge_observation_id
          AND observation.preparation_service_id = NEW.preparation_service_id
          AND observation.professional_source_snapshot_id =
              NEW.professional_source_snapshot_id
          AND (
              NEW.panel_id IS NULL
              OR observation.panel_id = NEW.panel_id
          )
    ) OR NEW.panel_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM competition.preparation_service AS service
        JOIN competition.panel AS panel_record
          ON panel_record.series_id = service.series_id
         AND panel_record.edition_id = service.edition_id
         AND panel_record.category_id = service.category_id
         AND panel_record.round_id = service.round_id
        WHERE service.preparation_service_id = NEW.preparation_service_id
          AND panel_record.panel_id = NEW.panel_id
    ) OR NEW.structured_score_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM competition.structured_score AS score
        WHERE score.structured_score_id = NEW.structured_score_id
          AND score.preparation_service_id = NEW.preparation_service_id
          AND score.professional_source_snapshot_id =
              NEW.professional_source_snapshot_id
    ) OR NEW.competitor_declared_note_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM competition.competitor_declared_note AS note
        WHERE note.competitor_declared_note_id =
              NEW.competitor_declared_note_id
          AND note.preparation_service_id = NEW.preparation_service_id
          AND note.professional_source_snapshot_id =
              NEW.professional_source_snapshot_id
    ) OR NEW.organizer_published_note_id IS NOT NULL AND NOT EXISTS (
        SELECT 1
        FROM competition.organizer_published_note AS note
        WHERE note.organizer_published_note_id =
              NEW.organizer_published_note_id
          AND note.preparation_service_id = NEW.preparation_service_id
          AND note.professional_source_snapshot_id =
              NEW.professional_source_snapshot_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'competition_descriptor_assertion_source_lineage_ck',
            MESSAGE = 'descriptor assertion must retain service, panel, snapshot, and source-record lineage';
    END IF;

    RETURN NEW;
END
$enforce_descriptor_assertion_source_lineage$;

CREATE TRIGGER competition_descriptor_assertion_source_lineage_biu
BEFORE INSERT OR UPDATE ON competition.descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    competition.enforce_descriptor_assertion_source_lineage();

CREATE TABLE competition.descriptor_assertion_judge_lineage (
    descriptor_assertion_id BIGINT NOT NULL,
    judge_observation_id BIGINT NOT NULL,
    lineage_role_code TEXT NOT NULL,
    CONSTRAINT descriptor_assertion_judge_lineage_pk PRIMARY KEY (
        descriptor_assertion_id, judge_observation_id
    ),
    CONSTRAINT descriptor_assertion_judge_lineage_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES competition.descriptor_assertion (descriptor_assertion_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_judge_lineage_observation_fk FOREIGN KEY (
        judge_observation_id
    ) REFERENCES competition.judge_observation (judge_observation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT descriptor_assertion_judge_lineage_role_ck CHECK (
        lineage_role_code IN ('SUPPORTING_JUDGE', 'HEAD_JUDGE_ADJUDICATION')
    )
);

CREATE FUNCTION competition.validate_descriptor_assertion_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_descriptor_assertion_lineage$
DECLARE
    selected competition.descriptor_assertion%ROWTYPE;
    invalid_count BIGINT;
    lineage_count BIGINT;
BEGIN
    SELECT * INTO selected
    FROM competition.descriptor_assertion
    WHERE descriptor_assertion_id = COALESCE(
        NEW.descriptor_assertion_id, OLD.descriptor_assertion_id
    );

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    SELECT count(*), count(*) FILTER (
        WHERE observation.preparation_service_id IS DISTINCT FROM
                  selected.preparation_service_id
           OR observation.panel_id IS DISTINCT FROM selected.panel_id
    )
    INTO lineage_count, invalid_count
    FROM competition.descriptor_assertion_judge_lineage AS lineage
    JOIN competition.judge_observation AS observation
      ON observation.judge_observation_id = lineage.judge_observation_id
    WHERE lineage.descriptor_assertion_id = selected.descriptor_assertion_id;

    IF selected.assertion_type_code =
       'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR' THEN
        IF lineage_count = 0 OR invalid_count > 0 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'descriptor_assertion_consensus_lineage_ck',
                MESSAGE = 'panel consensus requires same-service, same-panel judge-observation lineage';
        END IF;
    ELSIF lineage_count <> 0 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'descriptor_assertion_nonconsensus_lineage_ck',
            MESSAGE = 'only panel-consensus assertions may have judge lineage rows';
    END IF;

    RETURN NULL;
END
$validate_descriptor_assertion_lineage$;

CREATE CONSTRAINT TRIGGER descriptor_assertion_lineage_assertion_aiu
AFTER INSERT OR UPDATE ON competition.descriptor_assertion
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    competition.validate_descriptor_assertion_lineage();

CREATE CONSTRAINT TRIGGER descriptor_assertion_lineage_member_aiud
AFTER INSERT OR UPDATE OR DELETE
ON competition.descriptor_assertion_judge_lineage
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    competition.validate_descriptor_assertion_lineage();

CREATE INDEX professional_source_family_ix
    ON evidence.professional_source (source_family_key, admitted);
CREATE INDEX professional_snapshot_source_ix
    ON evidence.professional_source_snapshot (
        professional_source_id, admitted, retrieved_at
    );
CREATE INDEX professional_rights_model_ix
    ON evidence.professional_rights_decision (
        internal_research_use, model_research_use
    );
CREATE INDEX preparation_service_evidence_service_ix
    ON competition.preparation_service_evidence (
        preparation_service_id, explicit_fresh_preparation_evidence
    );
CREATE INDEX judge_observation_service_ix
    ON competition.judge_observation (
        preparation_service_id, panel_id, judge_id
    );
CREATE INDEX structured_score_service_ix
    ON competition.structured_score (
        preparation_service_id, evidence_tier_code, score_dimension_key
    );
CREATE INDEX descriptor_assertion_service_ix
    ON competition.descriptor_assertion (
        preparation_service_id, evidence_tier_code, assertion_type_code
    );
CREATE INDEX descriptor_assertion_source_ix
    ON competition.descriptor_assertion (
        professional_source_snapshot_id, professional_source_file_id
    );

COMMENT ON TABLE evidence.professional_rights_decision IS
    'Six independent source-snapshot rights decisions; public access never implies model-research permission.';
COMMENT ON TABLE competition.structured_score IS
    'Explicit source-native score values. Numeric score rows are reported separately and do not inflate professional descriptor-assertion counts.';
COMMENT ON TABLE competition.descriptor_assertion IS
    'Explicit professional descriptor evidence with controlled P1-P4 assertion types, raw-source lineage, and no semantic inference.';
COMMENT ON TABLE competition.organizer_published_note IS
    'P2 notes without a complete round-service identity remain governed evidence but are not effective professional coffee records.';

COMMIT;
