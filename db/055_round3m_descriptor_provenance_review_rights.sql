\set ON_ERROR_STOP on

-- Round 3M descriptor-first provenance, review, rights, de-inflation, and
-- source-schema contract.
--
-- This is a forward-only extension of the Round 3K competition identities
-- and the Round 3L acquisition ledger.  A Round 3M assertion resolves to an
-- existing governed identity when one is available, or to a public-safe
-- source-native identity bridge until restricted identity resolution occurs.
-- The tables below do not turn result rows, scores, rankings, judges, or
-- publication mirrors into coffee records.

BEGIN;

CREATE TABLE evidence.round3m_independent_source_family (
    independent_source_family_id TEXT NOT NULL,
    organizer_id TEXT NOT NULL,
    family_name TEXT NOT NULL,
    independence_basis TEXT NOT NULL,
    rights_lineage_id TEXT NOT NULL,
    admitted_for_descriptor_research BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_independent_source_family_pk PRIMARY KEY (
        independent_source_family_id
    ),
    CONSTRAINT round3m_independent_source_family_text_ck CHECK (
        independent_source_family_id = lower(btrim(
            independent_source_family_id
        ))
        AND independent_source_family_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND organizer_id = lower(btrim(organizer_id))
        AND organizer_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND family_name = btrim(family_name) AND family_name <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
        AND rights_lineage_id = lower(btrim(rights_lineage_id))
        AND rights_lineage_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
    )
);

COMMENT ON TABLE evidence.round3m_independent_source_family IS
    'Organizer/evidence-origin independence unit. Multiple routes, editions, mirrors, and hosts cannot inflate this family count.';

CREATE TABLE evidence.round3m_source_route (
    source_route_id TEXT NOT NULL,
    independent_source_family_id TEXT NOT NULL,
    round3l_source_census_id BIGINT,
    organizer_id TEXT NOT NULL,
    publication_host TEXT NOT NULL,
    canonical_url TEXT NOT NULL,
    route_pattern TEXT NOT NULL,
    route_disposition TEXT NOT NULL,
    rights_lineage_id TEXT NOT NULL,
    mirror_lineage_id TEXT NOT NULL,
    discovered_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_source_route_pk PRIMARY KEY (source_route_id),
    CONSTRAINT round3m_source_route_family_fk FOREIGN KEY (
        independent_source_family_id
    ) REFERENCES evidence.round3m_independent_source_family (
        independent_source_family_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_route_census_fk FOREIGN KEY (
        round3l_source_census_id
    ) REFERENCES audit.round3l_source_census (round3l_source_census_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_route_text_ck CHECK (
        source_route_id = lower(btrim(source_route_id))
        AND source_route_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND organizer_id = lower(btrim(organizer_id))
        AND organizer_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND publication_host = lower(btrim(publication_host))
        AND publication_host <> ''
        AND canonical_url = btrim(canonical_url) AND canonical_url <> ''
        AND route_pattern = btrim(route_pattern) AND route_pattern <> ''
        AND rights_lineage_id = lower(btrim(rights_lineage_id))
        AND rights_lineage_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND mirror_lineage_id = lower(btrim(mirror_lineage_id))
        AND mirror_lineage_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
    ),
    CONSTRAINT round3m_source_route_disposition_ck CHECK (
        route_disposition IN (
            'PRIORITY_DESCRIPTOR_ROUTE',
            'PROVENANCE_PILOT_ONLY',
            'REVIEW_EXISTING_CANDIDATES',
            'PARTNERSHIP_ONLY',
            'EXCLUDED_LOW_YIELD',
            'UNRESOLVED_ROUTE'
        )
    )
);

CREATE INDEX round3m_source_route_family_idx
    ON evidence.round3m_source_route (independent_source_family_id);

COMMENT ON TABLE evidence.round3m_source_route IS
    'A retrieval route, not an independent source family. Host, mirror, rights-lineage, and organizer identities remain explicit.';

-- Column names deliberately mirror SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv so a
-- validated artifact can be imported with an explicit-column COPY.
CREATE TABLE evidence.round3m_source_schema_signature (
    schema_signature_id TEXT NOT NULL,
    source_route_id TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    host TEXT NOT NULL,
    route_pattern TEXT NOT NULL,
    edition_or_period TEXT NOT NULL,
    field_labels_json JSONB NOT NULL,
    selectors_json JSONB NOT NULL,
    publication_layer_rules_json JSONB NOT NULL,
    field_origin_assumptions_json JSONB NOT NULL,
    known_ambiguity TEXT NOT NULL,
    positive_fixture_locator TEXT NOT NULL,
    negative_fixture_locator TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    live_positive_fixture_present BOOLEAN NOT NULL,
    validation_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_source_schema_signature_pk PRIMARY KEY (
        schema_signature_id
    ),
    CONSTRAINT round3m_source_schema_signature_route_version_uq UNIQUE (
        source_route_id, schema_version
    ),
    CONSTRAINT round3m_source_schema_signature_route_fk FOREIGN KEY (
        source_route_id
    ) REFERENCES evidence.round3m_source_route (source_route_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_schema_signature_text_ck CHECK (
        schema_signature_id = lower(btrim(schema_signature_id))
        AND schema_signature_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND schema_version > 0
        AND host = lower(btrim(host)) AND host <> ''
        AND route_pattern = btrim(route_pattern) AND route_pattern <> ''
        AND edition_or_period = btrim(edition_or_period)
        AND edition_or_period <> ''
        AND known_ambiguity = btrim(known_ambiguity)
        AND known_ambiguity <> ''
        AND positive_fixture_locator = btrim(positive_fixture_locator)
        AND (
            positive_fixture_locator <> ''
            OR validation_status = 'BLOCKED_NO_POSITIVE_FIXTURE'
        )
        AND negative_fixture_locator = btrim(negative_fixture_locator)
        AND negative_fixture_locator <> ''
        AND adapter_version = btrim(adapter_version)
        AND adapter_version <> ''
    ),
    CONSTRAINT round3m_source_schema_signature_json_ck CHECK (
        jsonb_typeof(field_labels_json) = 'array'
        AND jsonb_array_length(field_labels_json) > 0
        AND jsonb_typeof(selectors_json) = 'object'
        AND jsonb_typeof(publication_layer_rules_json) = 'object'
        AND jsonb_typeof(field_origin_assumptions_json) = 'object'
    ),
    CONSTRAINT round3m_source_schema_signature_status_ck CHECK (
        validation_status IN (
            'VALIDATED', 'PROVISIONAL',
            'BLOCKED_NO_POSITIVE_FIXTURE', 'SOURCE_DRIFT'
        )
        AND (
            validation_status <> 'VALIDATED'
            OR live_positive_fixture_present
        )
        AND (
            validation_status <> 'BLOCKED_NO_POSITIVE_FIXTURE'
            OR live_positive_fixture_present IS FALSE
               AND positive_fixture_locator = ''
        )
    )
);

COMMENT ON TABLE evidence.round3m_source_schema_signature IS
    'Versioned field/schema/edition extraction contract. A family-wide parser assumption is not a schema signature.';

CREATE TABLE evidence.round3m_source_artifact (
    source_artifact_id TEXT NOT NULL,
    source_route_id TEXT NOT NULL,
    schema_signature_id TEXT NOT NULL,
    round3l_source_attempt_id BIGINT,
    professional_source_file_id BIGINT,
    governed_locator TEXT NOT NULL,
    source_retrieved_at TIMESTAMPTZ NOT NULL,
    source_file_sha256 TEXT NOT NULL,
    route_index_sha256 TEXT NOT NULL,
    source_file_sha256_scope TEXT NOT NULL,
    source_file_nonstorage_reason TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    storage_state TEXT NOT NULL,
    non_storage_reason TEXT,
    parser_version TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_source_artifact_pk PRIMARY KEY (source_artifact_id),
    CONSTRAINT round3m_source_artifact_route_fk FOREIGN KEY (
        source_route_id
    ) REFERENCES evidence.round3m_source_route (source_route_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_artifact_schema_fk FOREIGN KEY (
        schema_signature_id
    ) REFERENCES evidence.round3m_source_schema_signature (
        schema_signature_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_artifact_attempt_fk FOREIGN KEY (
        round3l_source_attempt_id
    ) REFERENCES audit.round3l_source_attempt (round3l_source_attempt_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_artifact_file_fk FOREIGN KEY (
        professional_source_file_id
    ) REFERENCES evidence.professional_source_file (
        professional_source_file_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_source_artifact_text_ck CHECK (
        source_artifact_id = lower(btrim(source_artifact_id))
        AND source_artifact_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND governed_locator = btrim(governed_locator)
        AND governed_locator <> ''
        AND (
            source_file_sha256 = ''
            OR source_file_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND (
            route_index_sha256 = ''
            OR route_index_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND num_nonnulls(
            NULLIF(source_file_sha256, ''),
            NULLIF(route_index_sha256, '')
        ) >= 1
        AND source_file_sha256_scope =
            btrim(source_file_sha256_scope)
        AND source_file_sha256_scope <> ''
        AND source_file_nonstorage_reason =
            btrim(source_file_nonstorage_reason)
        AND (
            source_file_sha256 <> ''
            OR source_file_nonstorage_reason <> ''
        )
        AND parser_version = btrim(parser_version) AND parser_version <> ''
        AND adapter_version = btrim(adapter_version)
        AND adapter_version <> ''
    ),
    CONSTRAINT round3m_source_artifact_storage_ck CHECK (
        file_size_bytes >= 0
        AND storage_state IN (
            'RESTRICTED_RETAINED', 'PUBLIC_RETAINED',
            'HASH_AND_LOCATOR_ONLY', 'EXTERNAL_OWNER_CONTROLLED'
        )
        AND (
            storage_state IN ('RESTRICTED_RETAINED', 'PUBLIC_RETAINED')
            AND non_storage_reason IS NULL
            OR storage_state IN (
                'HASH_AND_LOCATOR_ONLY', 'EXTERNAL_OWNER_CONTROLLED'
            )
            AND non_storage_reason IS NOT NULL
            AND btrim(non_storage_reason) <> ''
        )
    )
);

CREATE FUNCTION evidence.validate_round3m_source_artifact()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_source_artifact$
DECLARE
    signature_route_id TEXT;
    signature_adapter_version TEXT;
    attempt_hash TEXT;
BEGIN
    SELECT signature.source_route_id, signature.adapter_version
    INTO STRICT signature_route_id, signature_adapter_version
    FROM evidence.round3m_source_schema_signature AS signature
    WHERE signature.schema_signature_id = NEW.schema_signature_id;

    IF signature_route_id IS DISTINCT FROM NEW.source_route_id
       OR signature_adapter_version IS DISTINCT FROM NEW.adapter_version THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_source_artifact_schema_scope_ck',
            MESSAGE = 'source artifact must use a schema signature from the same route and adapter version';
    END IF;

    IF NEW.round3l_source_attempt_id IS NOT NULL THEN
        SELECT attempt.source_snapshot_sha256
        INTO attempt_hash
        FROM audit.round3l_source_attempt AS attempt
        WHERE attempt.round3l_source_attempt_id =
              NEW.round3l_source_attempt_id;

        IF attempt_hash IS NULL
           OR attempt_hash IS DISTINCT FROM NEW.source_file_sha256 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_source_artifact_attempt_hash_ck',
                MESSAGE = 'Round 3M artifact hash must equal its Round 3L acquisition snapshot hash';
        END IF;
    END IF;

    RETURN NEW;
END
$validate_round3m_source_artifact$;

CREATE TRIGGER round3m_source_artifact_validate_biu
BEFORE INSERT OR UPDATE ON evidence.round3m_source_artifact
FOR EACH ROW EXECUTE FUNCTION evidence.validate_round3m_source_artifact();

CREATE TABLE evidence.round3m_descriptor_rights_decision (
    rights_decision_id TEXT NOT NULL,
    rights_scope_id TEXT NOT NULL,
    decision_version INTEGER NOT NULL,
    supersedes_rights_decision_id TEXT,
    source_route_id TEXT NOT NULL,
    publication_layer TEXT NOT NULL,
    source_field_label TEXT NOT NULL,
    public_discovery TEXT NOT NULL,
    internal_research_analysis TEXT NOT NULL,
    derived_research_data TEXT NOT NULL,
    model_research TEXT NOT NULL,
    deployment_or_commercial_model TEXT NOT NULL,
    raw_redistribution TEXT NOT NULL,
    decision_authority_code TEXT NOT NULL,
    decision_actor_type TEXT NOT NULL,
    decision_basis TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_descriptor_rights_decision_pk PRIMARY KEY (
        rights_decision_id
    ),
    CONSTRAINT round3m_descriptor_rights_scope_version_uq UNIQUE (
        source_route_id, rights_scope_id, decision_version
    ),
    CONSTRAINT round3m_descriptor_rights_successor_uq UNIQUE (
        supersedes_rights_decision_id
    ),
    CONSTRAINT round3m_descriptor_rights_route_fk FOREIGN KEY (
        source_route_id
    ) REFERENCES evidence.round3m_source_route (source_route_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_rights_supersedes_fk FOREIGN KEY (
        supersedes_rights_decision_id
    ) REFERENCES evidence.round3m_descriptor_rights_decision (
        rights_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_rights_text_ck CHECK (
        rights_decision_id = lower(btrim(rights_decision_id))
        AND rights_decision_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND rights_scope_id = lower(btrim(rights_scope_id))
        AND rights_scope_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND decision_version > 0
        AND (decision_version = 1) =
            (supersedes_rights_decision_id IS NULL)
        AND source_field_label = btrim(source_field_label)
        AND source_field_label <> ''
        AND decision_basis = btrim(decision_basis)
        AND decision_basis <> ''
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
    ),
    CONSTRAINT round3m_descriptor_rights_publication_layer_ck CHECK (
        publication_layer IN (
            'PRIMARY_JURY_DESCRIPTION',
            'GENERIC_ORGANIZER_SENSORY_FIELD',
            'PRODUCER_OR_FARM_PROFILE',
            'SECONDARY_SENSORY_TABLE',
            'JUDGE_LEVEL_OBSERVATION',
            'RESULT_METADATA',
            'PROTOCOL_OR_BLANK_FORM'
        )
    ),
    CONSTRAINT round3m_descriptor_rights_states_ck CHECK (
        public_discovery IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND internal_research_analysis IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND derived_research_data IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND model_research IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND deployment_or_commercial_model IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND raw_redistribution IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT round3m_descriptor_rights_authority_ck CHECK (
        decision_authority_code IN (
            'RIGHTS_HOLDER', 'ORGANIZER_TERMS', 'PUBLIC_LICENSE',
            'PROJECT_RIGHTS_AUDIT', 'LEGAL_REVIEW', 'UNKNOWN'
        )
        AND decision_actor_type IN (
            'CODEX_SOURCE_AUDITOR', 'HUMAN_RIGHTS_REVIEWER',
            'LEGAL_REVIEWER', 'RIGHTS_HOLDER', 'AUTOMATED_PARSER'
        )
    ),
    CONSTRAINT round3m_public_visibility_not_model_permission_ck CHECK (
        NOT (
            decision_authority_code IN ('PROJECT_RIGHTS_AUDIT', 'UNKNOWN')
            AND (
                model_research = 'AFFIRMATIVE'
                OR deployment_or_commercial_model = 'AFFIRMATIVE'
            )
        )
        AND NOT (
            lower(decision_basis) LIKE '%public visibility%'
            AND (
                model_research = 'AFFIRMATIVE'
                OR deployment_or_commercial_model = 'AFFIRMATIVE'
            )
        )
    )
);

CREATE FUNCTION evidence.validate_round3m_rights_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_rights_lineage$
DECLARE
    predecessor evidence.round3m_descriptor_rights_decision%ROWTYPE;
BEGIN
    IF NEW.supersedes_rights_decision_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO STRICT predecessor
    FROM evidence.round3m_descriptor_rights_decision
    WHERE rights_decision_id = NEW.supersedes_rights_decision_id;

    IF predecessor.source_route_id IS DISTINCT FROM NEW.source_route_id
       OR predecessor.rights_scope_id IS DISTINCT FROM NEW.rights_scope_id
       OR predecessor.decision_version <> NEW.decision_version - 1
       OR predecessor.decided_at > NEW.decided_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_rights_lineage_ck',
            MESSAGE = 'rights supersession must use the immediately prior decision for the same route and field scope';
    END IF;

    RETURN NEW;
END
$validate_round3m_rights_lineage$;

CREATE TRIGGER round3m_descriptor_rights_lineage_bi
BEFORE INSERT ON evidence.round3m_descriptor_rights_decision
FOR EACH ROW EXECUTE FUNCTION evidence.validate_round3m_rights_lineage();

CREATE VIEW evidence.v_round3m_current_descriptor_rights AS
WITH leaf AS (
    SELECT decision.*
    FROM evidence.round3m_descriptor_rights_decision AS decision
    WHERE NOT EXISTS (
        SELECT 1
        FROM evidence.round3m_descriptor_rights_decision AS successor
        WHERE successor.supersedes_rights_decision_id =
              decision.rights_decision_id
    )
)
SELECT
    leaf.*,
    count(*) OVER (
        PARTITION BY source_route_id, rights_scope_id
    )::INTEGER AS current_decision_count,
    count(*) OVER (
        PARTITION BY source_route_id, rights_scope_id
    ) = 1 AS unambiguous_current_decision
FROM leaf;

-- Public-safe Round 3M artifacts can identify a real effective record even
-- when the owner-controlled Round 3L row is intentionally absent from the
-- public database.  This is an identity bridge, not a second record corpus:
-- it stores the competition-native tuple, its source hash, and an optional
-- later resolution to exactly one existing Round 3K or Round 3L identity.
CREATE TABLE competition.round3m_effective_record_bridge (
    round3m_effective_record_id TEXT NOT NULL,
    effective_record_key TEXT NOT NULL,
    series_id TEXT NOT NULL,
    edition_id TEXT NOT NULL,
    edition_year INTEGER NOT NULL,
    category_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    entry_or_lot_id TEXT NOT NULL,
    preparation_service_code TEXT NOT NULL,
    preparation_evidence_locator TEXT NOT NULL,
    source_route_id TEXT NOT NULL,
    source_artifact_id TEXT NOT NULL,
    source_record_locator TEXT NOT NULL,
    source_file_sha256 TEXT NOT NULL,
    route_index_sha256 TEXT NOT NULL,
    source_file_sha256_scope TEXT NOT NULL,
    source_file_nonstorage_reason TEXT NOT NULL,
    record_identity_sha256 TEXT NOT NULL,
    preparation_service_id BIGINT,
    professional_acquisition_record_id BIGINT,
    identity_resolution_state TEXT NOT NULL,
    synthetic_generated BOOLEAN NOT NULL DEFAULT FALSE,
    preparation_inferred_from_descriptor BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_effective_record_bridge_pk PRIMARY KEY (
        round3m_effective_record_id
    ),
    CONSTRAINT round3m_effective_record_bridge_key_uq UNIQUE (
        effective_record_key
    ),
    CONSTRAINT round3m_effective_record_bridge_tuple_uq UNIQUE (
        series_id, edition_id, category_id, round_id,
        subject_kind, entry_or_lot_id, preparation_service_code
    ),
    CONSTRAINT round3m_effective_record_bridge_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_effective_record_bridge_acquisition_fk FOREIGN KEY (
        professional_acquisition_record_id
    ) REFERENCES corpus.professional_acquisition_record (
        professional_acquisition_record_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_effective_record_bridge_route_fk FOREIGN KEY (
        source_route_id
    ) REFERENCES evidence.round3m_source_route (source_route_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_effective_record_bridge_artifact_fk FOREIGN KEY (
        source_artifact_id
    ) REFERENCES evidence.round3m_source_artifact (source_artifact_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_effective_record_bridge_text_ck CHECK (
        round3m_effective_record_id =
            lower(btrim(round3m_effective_record_id))
        AND round3m_effective_record_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND effective_record_key = lower(btrim(effective_record_key))
        AND effective_record_key <> ''
        AND series_id = lower(btrim(series_id)) AND series_id <> ''
        AND edition_id = lower(btrim(edition_id)) AND edition_id <> ''
        AND edition_year BETWEEN 1900 AND 2100
        AND category_id = lower(btrim(category_id)) AND category_id <> ''
        AND round_id = lower(btrim(round_id)) AND round_id <> ''
        AND subject_kind IN ('ENTRY', 'LOT')
        AND entry_or_lot_id = btrim(entry_or_lot_id)
        AND entry_or_lot_id <> ''
        AND preparation_service_code =
            lower(btrim(preparation_service_code))
        AND preparation_service_code <> ''
        AND preparation_evidence_locator =
            btrim(preparation_evidence_locator)
        AND preparation_evidence_locator <> ''
        AND source_record_locator = btrim(source_record_locator)
        AND source_record_locator <> ''
        AND (
            source_file_sha256 = ''
            OR source_file_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND (
            route_index_sha256 = ''
            OR route_index_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND num_nonnulls(
            NULLIF(source_file_sha256, ''),
            NULLIF(route_index_sha256, '')
        ) >= 1
        AND source_file_sha256_scope =
            btrim(source_file_sha256_scope)
        AND source_file_sha256_scope <> ''
        AND source_file_nonstorage_reason =
            btrim(source_file_nonstorage_reason)
        AND (
            source_file_sha256 <> ''
            OR source_file_nonstorage_reason <> ''
        )
        AND record_identity_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_effective_record_bridge_resolution_ck CHECK (
        identity_resolution_state IN (
            'SOURCE_NATIVE_PROVISIONAL', 'ROUND3K_LINKED',
            'ROUND3L_RESTRICTED_LINKED'
        )
        AND (
            identity_resolution_state = 'SOURCE_NATIVE_PROVISIONAL'
            AND num_nonnulls(
                preparation_service_id,
                professional_acquisition_record_id
            ) = 0
            OR identity_resolution_state = 'ROUND3K_LINKED'
            AND preparation_service_id IS NOT NULL
            AND professional_acquisition_record_id IS NULL
            OR identity_resolution_state = 'ROUND3L_RESTRICTED_LINKED'
            AND professional_acquisition_record_id IS NOT NULL
            AND preparation_service_id IS NULL
        )
        AND synthetic_generated IS FALSE
        AND preparation_inferred_from_descriptor IS FALSE
    )
);

CREATE FUNCTION competition.validate_round3m_effective_record_bridge()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_effective_record_bridge$
DECLARE
    artifact evidence.round3m_source_artifact%ROWTYPE;
    linked_key TEXT;
    linked_year INTEGER;
BEGIN
    SELECT * INTO STRICT artifact
    FROM evidence.round3m_source_artifact
    WHERE source_artifact_id = NEW.source_artifact_id;

    IF artifact.source_route_id IS DISTINCT FROM NEW.source_route_id
       OR artifact.source_file_sha256 IS DISTINCT FROM
          NEW.source_file_sha256
       OR artifact.route_index_sha256 IS DISTINCT FROM
          NEW.route_index_sha256
       OR artifact.source_file_sha256_scope IS DISTINCT FROM
          NEW.source_file_sha256_scope
       OR artifact.source_file_nonstorage_reason IS DISTINCT FROM
          NEW.source_file_nonstorage_reason
       OR artifact.route_index_sha256 IS DISTINCT FROM
          NEW.route_index_sha256
       OR artifact.source_file_sha256_scope IS DISTINCT FROM
          NEW.source_file_sha256_scope
       OR artifact.source_file_nonstorage_reason IS DISTINCT FROM
          NEW.source_file_nonstorage_reason THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_effective_record_artifact_scope_ck',
            MESSAGE = 'effective-record bridge must retain its source route and file hash';
    END IF;

    IF NEW.preparation_service_id IS NOT NULL THEN
        SELECT service.preparation_service_key, edition.edition_year
        INTO STRICT linked_key, linked_year
        FROM competition.preparation_service AS service
        JOIN competition.edition AS edition
          ON edition.edition_id = service.edition_id
        WHERE service.preparation_service_id = NEW.preparation_service_id;
    ELSIF NEW.professional_acquisition_record_id IS NOT NULL THEN
        SELECT record.effective_record_key, record.edition_year
        INTO STRICT linked_key, linked_year
        FROM corpus.professional_acquisition_record AS record
        WHERE record.professional_acquisition_record_id =
              NEW.professional_acquisition_record_id;
    END IF;

    IF linked_key IS NOT NULL
       AND (
           linked_key IS DISTINCT FROM NEW.effective_record_key
           OR linked_year IS DISTINCT FROM NEW.edition_year
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_effective_record_existing_identity_ck',
            MESSAGE = 'resolved bridge key and year must match the existing governed effective record';
    END IF;

    RETURN NEW;
END
$validate_round3m_effective_record_bridge$;

CREATE TRIGGER round3m_effective_record_bridge_biu
BEFORE INSERT OR UPDATE ON competition.round3m_effective_record_bridge
FOR EACH ROW EXECUTE FUNCTION
    competition.validate_round3m_effective_record_bridge();

CREATE TABLE corpus.round3m_descriptor_assertion (
    descriptor_assertion_id BIGINT GENERATED ALWAYS AS IDENTITY,
    descriptor_assertion_key TEXT NOT NULL,
    competition_descriptor_assertion_id BIGINT,
    professional_acquisition_assertion_id BIGINT,
    preparation_service_id BIGINT,
    professional_acquisition_record_id BIGINT,
    round3m_effective_record_id TEXT,
    effective_record_key TEXT NOT NULL,
    edition_year INTEGER NOT NULL,
    source_artifact_id TEXT NOT NULL,
    source_route_id TEXT NOT NULL,
    schema_signature_id TEXT NOT NULL,
    publication_layer TEXT NOT NULL,
    source_field_label TEXT NOT NULL,
    source_field_label_sha256 TEXT NOT NULL,
    source_selector_or_locator TEXT NOT NULL,
    source_page_or_record_locator TEXT NOT NULL,
    source_observation_key TEXT NOT NULL,
    raw_field_text TEXT,
    raw_field_text_sha256 TEXT NOT NULL,
    atomic_source_text TEXT,
    atomic_source_text_sha256 TEXT NOT NULL,
    text_storage_state TEXT NOT NULL,
    source_text_non_storage_reason TEXT NOT NULL,
    source_language TEXT NOT NULL,
    descriptor_class TEXT NOT NULL,
    source_native_lexical_form TEXT,
    source_native_lexical_form_sha256 TEXT NOT NULL,
    normalized_candidate_form TEXT,
    normalized_candidate_form_sha256 TEXT NOT NULL,
    normalization_method_code TEXT NOT NULL,
    evidence_tier TEXT NOT NULL,
    evidence_origin_type TEXT NOT NULL,
    origin_decision_basis TEXT NOT NULL,
    origin_evidence_locator TEXT NOT NULL,
    review_state TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    current_review_receipt_id BIGINT,
    rights_decision_id TEXT NOT NULL,
    deduplication_disposition TEXT NOT NULL DEFAULT 'CANONICAL',
    within_record_repeat_group TEXT,
    cross_observation_repeat_group TEXT,
    mirror_group TEXT,
    translation_generated BOOLEAN NOT NULL DEFAULT FALSE,
    synthetic_generated BOOLEAN NOT NULL DEFAULT FALSE,
    roast_inferred_from_descriptor BOOLEAN NOT NULL DEFAULT FALSE,
    preparation_inferred_from_descriptor BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    source_retrieved_at TIMESTAMPTZ NOT NULL,
    source_file_sha256 TEXT NOT NULL,
    route_index_sha256 TEXT NOT NULL,
    source_file_sha256_scope TEXT NOT NULL,
    source_file_nonstorage_reason TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    CONSTRAINT round3m_descriptor_assertion_pk PRIMARY KEY (
        descriptor_assertion_id
    ),
    CONSTRAINT round3m_descriptor_assertion_key_uq UNIQUE (
        descriptor_assertion_key
    ),
    CONSTRAINT round3m_descriptor_assertion_competition_fk FOREIGN KEY (
        competition_descriptor_assertion_id
    ) REFERENCES competition.descriptor_assertion (descriptor_assertion_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_acquisition_assertion_fk
        FOREIGN KEY (professional_acquisition_assertion_id)
        REFERENCES corpus.professional_acquisition_assertion (
            professional_acquisition_assertion_id
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_service_fk FOREIGN KEY (
        preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_acquisition_record_fk
        FOREIGN KEY (professional_acquisition_record_id)
        REFERENCES corpus.professional_acquisition_record (
            professional_acquisition_record_id
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_round3m_record_fk FOREIGN KEY (
        round3m_effective_record_id
    ) REFERENCES competition.round3m_effective_record_bridge (
        round3m_effective_record_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_artifact_fk FOREIGN KEY (
        source_artifact_id
    ) REFERENCES evidence.round3m_source_artifact (source_artifact_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_route_fk FOREIGN KEY (
        source_route_id
    ) REFERENCES evidence.round3m_source_route (source_route_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_schema_fk FOREIGN KEY (
        schema_signature_id
    ) REFERENCES evidence.round3m_source_schema_signature (
        schema_signature_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_rights_fk FOREIGN KEY (
        rights_decision_id
    ) REFERENCES evidence.round3m_descriptor_rights_decision (
        rights_decision_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_assertion_text_ck CHECK (
        descriptor_assertion_key = lower(btrim(descriptor_assertion_key))
        AND descriptor_assertion_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND effective_record_key = lower(btrim(effective_record_key))
        AND effective_record_key <> ''
        AND edition_year BETWEEN 1900 AND 2100
        AND source_field_label = btrim(source_field_label)
        AND source_field_label <> ''
        AND source_field_label_sha256 =
            audit.round3i_utf8_sha256(source_field_label)
        AND source_selector_or_locator = btrim(source_selector_or_locator)
        AND source_selector_or_locator <> ''
        AND source_page_or_record_locator =
            btrim(source_page_or_record_locator)
        AND source_page_or_record_locator <> ''
        AND source_observation_key = lower(btrim(source_observation_key))
        AND source_observation_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND raw_field_text_sha256 ~ '^[0-9a-f]{64}$'
        AND atomic_source_text_sha256 ~ '^[0-9a-f]{64}$'
        AND source_language = btrim(source_language)
        AND source_language <> ''
        AND source_native_lexical_form_sha256 ~ '^[0-9a-f]{64}$'
        AND origin_decision_basis = btrim(origin_decision_basis)
        AND origin_decision_basis <> ''
        AND origin_evidence_locator = btrim(origin_evidence_locator)
        AND origin_evidence_locator <> ''
        AND (
            source_file_sha256 = ''
            OR source_file_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND (
            route_index_sha256 = ''
            OR route_index_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND num_nonnulls(
            NULLIF(source_file_sha256, ''),
            NULLIF(route_index_sha256, '')
        ) >= 1
        AND source_file_sha256_scope =
            btrim(source_file_sha256_scope)
        AND source_file_sha256_scope <> ''
        AND source_file_nonstorage_reason =
            btrim(source_file_nonstorage_reason)
        AND (
            source_file_sha256 <> ''
            OR source_file_nonstorage_reason <> ''
        )
        AND parser_version = btrim(parser_version) AND parser_version <> ''
        AND adapter_version = btrim(adapter_version)
        AND adapter_version <> ''
    ),
    CONSTRAINT round3m_descriptor_assertion_effective_record_ck CHECK (
        num_nonnulls(
            preparation_service_id, professional_acquisition_record_id,
            round3m_effective_record_id
        ) = 1
        AND num_nonnulls(
            competition_descriptor_assertion_id,
            professional_acquisition_assertion_id
        ) <= 1
    ),
    CONSTRAINT round3m_descriptor_assertion_storage_ck CHECK (
        text_storage_state IN (
            'RESTRICTED_RETAINED', 'REVIEWED_EXCERPT', 'HASH_ONLY'
        )
        AND (
            text_storage_state = 'HASH_ONLY'
            AND raw_field_text IS NULL
            AND atomic_source_text IS NULL
            AND source_text_non_storage_reason =
                btrim(source_text_non_storage_reason)
            AND source_text_non_storage_reason <> ''
            OR text_storage_state <> 'HASH_ONLY'
            AND raw_field_text IS NOT NULL
            AND btrim(raw_field_text) <> ''
            AND atomic_source_text IS NOT NULL
            AND btrim(atomic_source_text) <> ''
            AND raw_field_text_sha256 =
                audit.round3i_utf8_sha256(raw_field_text)
            AND atomic_source_text_sha256 =
                audit.round3i_utf8_sha256(atomic_source_text)
            AND source_text_non_storage_reason = ''
        )
    ),
    CONSTRAINT round3m_descriptor_assertion_class_ck CHECK (
        descriptor_class IN (
            'STRICT_FLAVOR', 'BROAD_SENSORY', 'NON_DESCRIPTOR'
        )
        AND (
            descriptor_class = 'NON_DESCRIPTOR'
            OR source_native_lexical_form IS NOT NULL
               AND btrim(source_native_lexical_form) <> ''
               AND atomic_source_text IS NOT NULL
            OR text_storage_state = 'HASH_ONLY'
               AND source_native_lexical_form IS NULL
               AND atomic_source_text IS NULL
        )
        AND (
            source_native_lexical_form IS NULL
            OR source_native_lexical_form_sha256 =
                audit.round3i_utf8_sha256(source_native_lexical_form)
        )
        AND (
            normalized_candidate_form IS NULL
            AND normalized_candidate_form_sha256 = ''
            OR normalized_candidate_form =
                kb.normalize_expression(normalized_candidate_form)
               AND normalized_candidate_form <> ''
               AND normalized_candidate_form_sha256 =
                   audit.round3i_utf8_sha256(normalized_candidate_form)
        )
        AND normalization_method_code IN (
            'NONE', 'UNICODE_NFC_WHITESPACE_CASE',
            'OBVIOUS_PLURAL_OR_SPELLING',
            'EXPLICIT_HUMAN_REVIEWED_CROSS_LANGUAGE_EQUIVALENCE'
        )
        AND (
            normalized_candidate_form IS NULL
            AND normalization_method_code = 'NONE'
            OR normalized_candidate_form IS NOT NULL
               AND normalization_method_code <> 'NONE'
        )
    ),
    CONSTRAINT round3m_descriptor_assertion_publication_layer_ck CHECK (
        publication_layer IN (
            'PRIMARY_JURY_DESCRIPTION',
            'GENERIC_ORGANIZER_SENSORY_FIELD',
            'PRODUCER_OR_FARM_PROFILE',
            'SECONDARY_SENSORY_TABLE',
            'JUDGE_LEVEL_OBSERVATION',
            'RESULT_METADATA',
            'PROTOCOL_OR_BLANK_FORM'
        )
    ),
    CONSTRAINT round3m_descriptor_assertion_tier_origin_ck CHECK (
        evidence_tier IN (
            'P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'UNRESOLVED'
        )
        AND evidence_origin_type IN (
            'EXPLICIT_IDENTIFIED_JUDGE',
            'EXPLICIT_IDENTIFIED_PANEL',
            'EXPLICIT_TOP_JURY_FIELD',
            'ORGANIZER_PUBLISHED_EXPLICIT_JURY',
            'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION',
            'PRODUCER_OR_FARM_DECLARED',
            'ROASTER_OR_COMMERCIAL_DECLARED',
            'GENERIC_ORGANIZER_FIELD_UNKNOWN_AUTHOR',
            'FREQUENCY_CODED_UNKNOWN_ACTOR',
            'FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED',
            'GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED',
            'PROTOCOL_RULE_OR_BLANK_FORM',
            'CONSUMER_OR_SYNTHETIC',
            'UNKNOWN_ORIGIN'
        )
        AND (
            evidence_tier = 'P1'
            AND evidence_origin_type IN (
                'EXPLICIT_IDENTIFIED_JUDGE',
                'EXPLICIT_IDENTIFIED_PANEL'
            )
            OR evidence_tier = 'P2'
            AND evidence_origin_type IN (
                'EXPLICIT_TOP_JURY_FIELD',
                'ORGANIZER_PUBLISHED_EXPLICIT_JURY',
                'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION'
            )
            OR evidence_tier = 'P3'
            AND evidence_origin_type = 'PRODUCER_OR_FARM_DECLARED'
            OR evidence_tier = 'P4'
            AND evidence_origin_type = 'ROASTER_OR_COMMERCIAL_DECLARED'
            OR evidence_tier = 'P5'
            AND evidence_origin_type = 'CONSUMER_OR_SYNTHETIC'
            OR evidence_tier = 'P0'
            AND evidence_origin_type = 'PROTOCOL_RULE_OR_BLANK_FORM'
            OR evidence_tier = 'UNRESOLVED'
            AND evidence_origin_type IN (
                'GENERIC_ORGANIZER_FIELD_UNKNOWN_AUTHOR',
                'FREQUENCY_CODED_UNKNOWN_ACTOR',
                'FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED',
                'GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED',
                'UNKNOWN_ORIGIN'
            )
        )
        AND (
            evidence_origin_type NOT IN (
                'GENERIC_ORGANIZER_FIELD_UNKNOWN_AUTHOR',
                'GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED',
                'FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED'
            )
            OR publication_layer = 'GENERIC_ORGANIZER_SENSORY_FIELD'
        )
        AND (
            evidence_origin_type <> 'PRODUCER_OR_FARM_DECLARED'
            OR publication_layer = 'PRODUCER_OR_FARM_PROFILE'
        )
        AND (
            evidence_origin_type <> 'PROTOCOL_RULE_OR_BLANK_FORM'
            OR publication_layer = 'PROTOCOL_OR_BLANK_FORM'
               AND descriptor_class = 'NON_DESCRIPTOR'
        )
    ),
    CONSTRAINT round3m_descriptor_assertion_review_shape_ck CHECK (
        review_state IN (
            'AUTO_EXTRACTED', 'PROVISIONAL_MACHINE_CLASSIFIED',
            'SOURCE_AUDITED', 'HUMAN_CONFIRMED',
            'EXPERT_ADJUDICATED', 'REJECTED_NON_DESCRIPTOR',
            'REJECTED_DUPLICATE', 'SOURCE_UNAVAILABLE',
            'PROVENANCE_UNRESOLVED', 'RIGHTS_BLOCKED'
        )
        AND review_actor_type IN (
            'AUTOMATED_PARSER', 'MACHINE_CLASSIFIER',
            'CODEX_SOURCE_AUDITOR', 'HUMAN_REVIEWER',
            'EXPERT_REVIEWER'
        )
        AND (
            review_state = 'AUTO_EXTRACTED'
            AND review_actor_type = 'AUTOMATED_PARSER'
            AND current_review_receipt_id IS NULL
            OR review_state = 'PROVISIONAL_MACHINE_CLASSIFIED'
            AND review_actor_type IN (
                'AUTOMATED_PARSER', 'MACHINE_CLASSIFIER',
                'CODEX_SOURCE_AUDITOR'
            )
            AND current_review_receipt_id IS NULL
            OR review_state NOT IN (
                'AUTO_EXTRACTED', 'PROVISIONAL_MACHINE_CLASSIFIED'
            )
            AND current_review_receipt_id IS NOT NULL
        )
        AND (
            review_state <> 'HUMAN_CONFIRMED'
            OR review_actor_type = 'HUMAN_REVIEWER'
        )
        AND (
            review_state <> 'EXPERT_ADJUDICATED'
            OR review_actor_type = 'EXPERT_REVIEWER'
        )
        AND (
            review_state <> 'REJECTED_NON_DESCRIPTOR'
            OR descriptor_class = 'NON_DESCRIPTOR'
        )
    ),
    CONSTRAINT round3m_descriptor_assertion_dedup_ck CHECK (
        deduplication_disposition IN (
            'CANONICAL', 'EXACT_WITHIN_FIELD_REPEAT',
            'WITHIN_RECORD_REPEAT', 'CROSS_OBSERVATION_REPEAT',
            'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE',
            'MIRROR_PUBLICATION', 'SUMMARY_DETAIL_DUPLICATE',
            'TRUE_DUPLICATE_ARTIFACT', 'UNRESOLVED'
        )
        AND (
            deduplication_disposition NOT IN (
                'EXACT_WITHIN_FIELD_REPEAT', 'WITHIN_RECORD_REPEAT'
            )
            OR within_record_repeat_group IS NOT NULL
               AND btrim(within_record_repeat_group) <> ''
        )
        AND (
            deduplication_disposition <> 'CROSS_OBSERVATION_REPEAT'
            OR cross_observation_repeat_group IS NOT NULL
               AND btrim(cross_observation_repeat_group) <> ''
        )
        AND (
            deduplication_disposition NOT IN (
                'MIRROR_PUBLICATION', 'SUMMARY_DETAIL_DUPLICATE',
                'TRUE_DUPLICATE_ARTIFACT'
            )
            OR mirror_group IS NOT NULL AND btrim(mirror_group) <> ''
        )
    ),
    CONSTRAINT round3m_descriptor_assertion_no_inferred_context_ck CHECK (
        roast_inferred_from_descriptor IS FALSE
        AND preparation_inferred_from_descriptor IS FALSE
    )
);

CREATE UNIQUE INDEX round3m_descriptor_observation_canonical_uq
    ON corpus.round3m_descriptor_assertion (
        effective_record_key,
        source_observation_key,
        coalesce(
            normalized_candidate_form,
            source_native_lexical_form,
            'sha256:' || source_native_lexical_form_sha256
        )
    )
    WHERE descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
      AND deduplication_disposition IN (
          'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
          'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
      );

CREATE INDEX round3m_descriptor_gate_idx
    ON corpus.round3m_descriptor_assertion (
        review_state, evidence_tier, descriptor_class
    );

CREATE INDEX round3m_descriptor_effective_record_idx
    ON corpus.round3m_descriptor_assertion (
        effective_record_key, source_observation_key
    );

CREATE FUNCTION corpus.validate_round3m_descriptor_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_lineage$
DECLARE
    artifact evidence.round3m_source_artifact%ROWTYPE;
    rights evidence.round3m_descriptor_rights_decision%ROWTYPE;
    service_key TEXT;
    service_year INTEGER;
    acquisition_key TEXT;
    acquisition_year INTEGER;
    acquisition_hash TEXT;
    bridge competition.round3m_effective_record_bridge%ROWTYPE;
BEGIN
    SELECT * INTO STRICT artifact
    FROM evidence.round3m_source_artifact
    WHERE source_artifact_id = NEW.source_artifact_id;

    SELECT * INTO STRICT rights
    FROM evidence.round3m_descriptor_rights_decision
    WHERE rights_decision_id = NEW.rights_decision_id;

    IF artifact.source_route_id IS DISTINCT FROM NEW.source_route_id
       OR artifact.schema_signature_id IS DISTINCT FROM
          NEW.schema_signature_id
       OR artifact.source_file_sha256 IS DISTINCT FROM
          NEW.source_file_sha256
       OR artifact.source_retrieved_at IS DISTINCT FROM
          NEW.source_retrieved_at
       OR artifact.parser_version IS DISTINCT FROM NEW.parser_version
       OR artifact.adapter_version IS DISTINCT FROM NEW.adapter_version THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_artifact_lineage_ck',
            MESSAGE = 'descriptor assertion must retain exact artifact, route, schema, hash, retrieval, parser, and adapter lineage';
    END IF;

    IF rights.source_route_id IS DISTINCT FROM NEW.source_route_id
       OR rights.publication_layer IS DISTINCT FROM NEW.publication_layer
       OR rights.source_field_label IS DISTINCT FROM NEW.source_field_label THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_rights_scope_ck',
            MESSAGE = 'descriptor assertion rights decision must cover its route, publication layer, and source field';
    END IF;

    IF NEW.preparation_service_id IS NOT NULL THEN
        SELECT service.preparation_service_key, edition.edition_year
        INTO STRICT service_key, service_year
        FROM competition.preparation_service AS service
        JOIN competition.edition AS edition
          ON edition.edition_id = service.edition_id
        WHERE service.preparation_service_id = NEW.preparation_service_id;

        IF service_key IS DISTINCT FROM NEW.effective_record_key
           OR service_year IS DISTINCT FROM NEW.edition_year THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_descriptor_effective_record_lineage_ck',
                MESSAGE = 'competition descriptor effective-record key and edition year must match the preparation service';
        END IF;
    ELSIF NEW.professional_acquisition_record_id IS NOT NULL THEN
        SELECT record.effective_record_key, record.edition_year,
               record.source_snapshot_sha256
        INTO STRICT acquisition_key, acquisition_year, acquisition_hash
        FROM corpus.professional_acquisition_record AS record
        WHERE record.professional_acquisition_record_id =
              NEW.professional_acquisition_record_id;

        IF acquisition_key IS NULL
           OR acquisition_key IS DISTINCT FROM NEW.effective_record_key
           OR acquisition_year IS DISTINCT FROM NEW.edition_year
           OR acquisition_hash IS DISTINCT FROM NEW.source_file_sha256 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_descriptor_effective_record_lineage_ck',
                MESSAGE = 'staged descriptor effective-record key, year, and source hash must match its canonical acquisition record';
        END IF;
    ELSE
        SELECT * INTO STRICT bridge
        FROM competition.round3m_effective_record_bridge
        WHERE round3m_effective_record_id =
              NEW.round3m_effective_record_id;

        IF bridge.effective_record_key IS DISTINCT FROM
              NEW.effective_record_key
           OR bridge.edition_year IS DISTINCT FROM NEW.edition_year
           OR bridge.source_route_id IS DISTINCT FROM NEW.source_route_id
           OR bridge.source_artifact_id IS DISTINCT FROM
              NEW.source_artifact_id
           OR bridge.source_file_sha256 IS DISTINCT FROM
              NEW.source_file_sha256
           OR bridge.route_index_sha256 IS DISTINCT FROM
              NEW.route_index_sha256
           OR bridge.source_file_sha256_scope IS DISTINCT FROM
              NEW.source_file_sha256_scope
           OR bridge.source_file_nonstorage_reason IS DISTINCT FROM
              NEW.source_file_nonstorage_reason THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_descriptor_effective_record_lineage_ck',
                MESSAGE = 'descriptor bridge identity, year, route, artifact, and source hash must match';
        END IF;
    END IF;

    IF NEW.competition_descriptor_assertion_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
            FROM competition.descriptor_assertion AS assertion
            WHERE assertion.descriptor_assertion_id =
                  NEW.competition_descriptor_assertion_id
              AND assertion.preparation_service_id =
                  NEW.preparation_service_id
              AND assertion.raw_phrase_sha256 =
                  NEW.atomic_source_text_sha256
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_prior_assertion_lineage_ck',
            MESSAGE = 'linked Round 3K assertion must match service and atomic source-text hash';
    END IF;

    IF NEW.professional_acquisition_assertion_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
            FROM corpus.professional_acquisition_assertion AS assertion
            WHERE assertion.professional_acquisition_assertion_id =
                  NEW.professional_acquisition_assertion_id
              AND assertion.professional_acquisition_record_id =
                  NEW.professional_acquisition_record_id
              AND assertion.assertion_text_sha256 =
                  NEW.atomic_source_text_sha256
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_prior_assertion_lineage_ck',
            MESSAGE = 'linked Round 3L assertion must match record and atomic source-text hash';
    END IF;

    RETURN NEW;
END
$validate_round3m_descriptor_lineage$;

CREATE TRIGGER round3m_descriptor_lineage_biu
BEFORE INSERT OR UPDATE ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION corpus.validate_round3m_descriptor_lineage();

CREATE TABLE audit.round3m_descriptor_review_receipt (
    review_receipt_id BIGINT GENERATED ALWAYS AS IDENTITY,
    review_receipt_key TEXT NOT NULL,
    descriptor_assertion_id BIGINT NOT NULL,
    receipt_version INTEGER NOT NULL,
    supersedes_review_receipt_id BIGINT,
    reviewer_id BIGINT,
    reviewer_id_or_pseudonymous_code TEXT NOT NULL,
    reviewer_role TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    receipt_origin_code TEXT NOT NULL,
    human_event_evidence_sha256 TEXT,
    review_protocol_version TEXT NOT NULL,
    decision TEXT NOT NULL,
    decision_reason TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    adjudication_status TEXT NOT NULL,
    previous_decision TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_descriptor_review_receipt_pk PRIMARY KEY (
        review_receipt_id
    ),
    CONSTRAINT round3m_descriptor_review_receipt_key_uq UNIQUE (
        review_receipt_key
    ),
    CONSTRAINT round3m_descriptor_review_receipt_version_uq UNIQUE (
        descriptor_assertion_id, receipt_version
    ),
    CONSTRAINT round3m_descriptor_review_receipt_successor_uq UNIQUE (
        supersedes_review_receipt_id
    ),
    CONSTRAINT round3m_descriptor_review_receipt_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_review_receipt_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_review_receipt_supersedes_fk FOREIGN KEY (
        supersedes_review_receipt_id
    ) REFERENCES audit.round3m_descriptor_review_receipt (
        review_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_review_receipt_text_ck CHECK (
        review_receipt_key = lower(btrim(review_receipt_key))
        AND review_receipt_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND receipt_version > 0
        AND (receipt_version = 1) =
            (supersedes_review_receipt_id IS NULL)
        AND reviewer_id_or_pseudonymous_code =
            btrim(reviewer_id_or_pseudonymous_code)
        AND reviewer_id_or_pseudonymous_code <> ''
        AND review_protocol_version = btrim(review_protocol_version)
        AND review_protocol_version <> ''
        AND decision_reason = btrim(decision_reason)
        AND decision_reason <> ''
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
        AND previous_decision = btrim(previous_decision)
        AND previous_decision <> ''
        AND (
            human_event_evidence_sha256 IS NULL
            OR human_event_evidence_sha256 ~ '^[0-9a-f]{64}$'
        )
    ),
    CONSTRAINT round3m_descriptor_review_receipt_values_ck CHECK (
        reviewer_role IN (
            'SOURCE_AUDITOR', 'PROFESSIONAL_SENSORY_REVIEWER',
            'INDEPENDENT_REVIEWER', 'ADJUDICATOR',
            'RIGHTS_REVIEWER'
        )
        AND review_actor_type IN (
            'AUTOMATED_PARSER', 'MACHINE_CLASSIFIER',
            'CODEX_SOURCE_AUDITOR', 'HUMAN_REVIEWER',
            'EXPERT_REVIEWER'
        )
        AND receipt_origin_code IN (
            'AUTOMATED_EXTRACTION', 'CODEX_SOURCE_AUDIT',
            'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
        )
        AND decision IN (
            'SOURCE_AUDIT_COMPLETE', 'CONFIRM_DESCRIPTOR',
            'ADJUDICATE_DESCRIPTOR', 'REJECT_NON_DESCRIPTOR',
            'REJECT_DUPLICATE', 'MARK_SOURCE_UNAVAILABLE',
            'MARK_AMBIGUOUS', 'MARK_UNRESOLVED', 'ABSTAIN',
            'RIGHTS_BLOCK'
        )
        AND adjudication_status IN (
            'NOT_REQUIRED', 'PENDING', 'FINAL', 'SUPERSEDED'
        )
    ),
    CONSTRAINT round3m_human_review_receipt_origin_ck CHECK (
        (
            review_actor_type NOT IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
            AND receipt_origin_code IN (
                'AUTOMATED_EXTRACTION', 'CODEX_SOURCE_AUDIT'
            )
            AND human_event_evidence_sha256 IS NULL
        )
        OR (
            review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
            AND receipt_origin_code IN (
                'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
            )
            AND human_event_evidence_sha256 IS NOT NULL
            AND lower(reviewer_id_or_pseudonymous_code)
                !~ '(^|[._ -])codex($|[._ -])'
        )
        AND (
            review_actor_type <> 'EXPERT_REVIEWER'
            OR reviewer_role = 'ADJUDICATOR'
               AND decision = 'ADJUDICATE_DESCRIPTOR'
               AND adjudication_status = 'FINAL'
        )
    )
);

ALTER TABLE corpus.round3m_descriptor_assertion
    ADD CONSTRAINT round3m_descriptor_assertion_current_review_fk
    FOREIGN KEY (current_review_receipt_id)
    REFERENCES audit.round3m_descriptor_review_receipt (review_receipt_id)
    DEFERRABLE INITIALLY IMMEDIATE;

CREATE FUNCTION audit.validate_round3m_review_receipt_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_review_receipt_lineage$
DECLARE
    predecessor audit.round3m_descriptor_review_receipt%ROWTYPE;
BEGIN
    IF NEW.supersedes_review_receipt_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO STRICT predecessor
    FROM audit.round3m_descriptor_review_receipt
    WHERE review_receipt_id = NEW.supersedes_review_receipt_id;

    IF predecessor.descriptor_assertion_id IS DISTINCT FROM
          NEW.descriptor_assertion_id
       OR predecessor.receipt_version <> NEW.receipt_version - 1
       OR predecessor.reviewed_at > NEW.reviewed_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_receipt_lineage_ck',
            MESSAGE = 'review receipt supersession must use the immediately prior receipt for the same assertion';
    END IF;

    RETURN NEW;
END
$validate_round3m_review_receipt_lineage$;

CREATE TRIGGER round3m_review_receipt_lineage_bi
BEFORE INSERT ON audit.round3m_descriptor_review_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_review_receipt_lineage();

CREATE FUNCTION corpus.validate_round3m_review_state()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_review_state$
DECLARE
    receipt audit.round3m_descriptor_review_receipt%ROWTYPE;
    expected_decision TEXT;
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

    expected_decision := CASE NEW.review_state
        WHEN 'SOURCE_AUDITED' THEN 'SOURCE_AUDIT_COMPLETE'
        WHEN 'HUMAN_CONFIRMED' THEN 'CONFIRM_DESCRIPTOR'
        WHEN 'EXPERT_ADJUDICATED' THEN 'ADJUDICATE_DESCRIPTOR'
        WHEN 'REJECTED_NON_DESCRIPTOR' THEN 'REJECT_NON_DESCRIPTOR'
        WHEN 'REJECTED_DUPLICATE' THEN 'REJECT_DUPLICATE'
        WHEN 'SOURCE_UNAVAILABLE' THEN 'MARK_SOURCE_UNAVAILABLE'
        WHEN 'PROVENANCE_UNRESOLVED' THEN 'MARK_UNRESOLVED'
        WHEN 'RIGHTS_BLOCKED' THEN 'RIGHTS_BLOCK'
    END;

    IF expected_decision IS NULL
       OR receipt.decision IS DISTINCT FROM expected_decision THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_state_receipt_ck',
            MESSAGE = 'review state must match the current receipt decision';
    END IF;

    IF NEW.review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
       AND (
            receipt.receipt_origin_code NOT IN (
                'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
            )
            OR receipt.human_event_evidence_sha256 IS NULL
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_human_receipt_ck',
            MESSAGE = 'human and expert review states require an evidenced actual-human receipt';
    END IF;

    RETURN NEW;
END
$validate_round3m_review_state$;

CREATE TRIGGER round3m_descriptor_review_state_biu
BEFORE INSERT OR UPDATE OF review_state, review_actor_type,
    current_review_receipt_id
ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION corpus.validate_round3m_review_state();

CREATE TABLE corpus.round3m_descriptor_label_target (
    descriptor_assertion_id BIGINT NOT NULL,
    target_ordinal INTEGER NOT NULL,
    output_label_key TEXT NOT NULL,
    normalization_decision TEXT NOT NULL,
    review_receipt_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_descriptor_label_target_pk PRIMARY KEY (
        descriptor_assertion_id, target_ordinal
    ),
    CONSTRAINT round3m_descriptor_label_target_uq UNIQUE (
        descriptor_assertion_id, output_label_key
    ),
    CONSTRAINT round3m_descriptor_label_target_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_label_target_receipt_fk FOREIGN KEY (
        review_receipt_id
    ) REFERENCES audit.round3m_descriptor_review_receipt (
        review_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_label_target_text_ck CHECK (
        target_ordinal > 0
        AND output_label_key = lower(btrim(output_label_key))
        AND output_label_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND normalization_decision IN (
            'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET',
            'RANGE_LEVEL_TARGET', 'SOURCE_LOCAL_TARGET'
        )
    )
);

CREATE FUNCTION corpus.validate_round3m_label_target()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_label_target$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion AS assertion
        JOIN audit.round3m_descriptor_review_receipt AS receipt
          ON receipt.review_receipt_id = NEW.review_receipt_id
         AND receipt.descriptor_assertion_id =
             assertion.descriptor_assertion_id
        WHERE assertion.descriptor_assertion_id =
              NEW.descriptor_assertion_id
          AND assertion.current_review_receipt_id = NEW.review_receipt_id
          AND assertion.review_state IN (
              'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
          )
          AND receipt.review_actor_type IN (
              'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
          AND receipt.decision IN (
              'CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR'
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_label_human_provenance_ck',
            MESSAGE = 'output labels require the assertion current actual-human review receipt';
    END IF;

    RETURN NEW;
END
$validate_round3m_label_target$;

CREATE TRIGGER round3m_descriptor_label_target_biu
BEFORE INSERT OR UPDATE ON corpus.round3m_descriptor_label_target
FOR EACH ROW EXECUTE FUNCTION corpus.validate_round3m_label_target();

CREATE TABLE corpus.round3m_coassertion_event (
    coassertion_event_id BIGINT GENERATED ALWAYS AS IDENTITY,
    coassertion_event_key TEXT NOT NULL,
    coassertion_set_key TEXT NOT NULL,
    effective_record_key TEXT NOT NULL,
    source_observation_key TEXT NOT NULL,
    left_descriptor_assertion_id BIGINT NOT NULL,
    right_descriptor_assertion_id BIGINT NOT NULL,
    generated_by_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_coassertion_event_pk PRIMARY KEY (
        coassertion_event_id
    ),
    CONSTRAINT round3m_coassertion_event_key_uq UNIQUE (
        coassertion_event_key
    ),
    CONSTRAINT round3m_coassertion_event_pair_uq UNIQUE (
        coassertion_set_key,
        left_descriptor_assertion_id,
        right_descriptor_assertion_id
    ),
    CONSTRAINT round3m_coassertion_event_left_fk FOREIGN KEY (
        left_descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_coassertion_event_right_fk FOREIGN KEY (
        right_descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_coassertion_event_text_ck CHECK (
        coassertion_event_key = lower(btrim(coassertion_event_key))
        AND coassertion_event_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND coassertion_set_key = lower(btrim(coassertion_set_key))
        AND coassertion_set_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND effective_record_key = lower(btrim(effective_record_key))
        AND effective_record_key <> ''
        AND source_observation_key = lower(btrim(source_observation_key))
        AND source_observation_key <> ''
        AND generated_by_version = btrim(generated_by_version)
        AND generated_by_version <> ''
        AND left_descriptor_assertion_id < right_descriptor_assertion_id
    )
);

CREATE FUNCTION corpus.validate_round3m_coassertion_boundary()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_coassertion_boundary$
DECLARE
    left_assertion corpus.round3m_descriptor_assertion%ROWTYPE;
    right_assertion corpus.round3m_descriptor_assertion%ROWTYPE;
BEGIN
    SELECT * INTO STRICT left_assertion
    FROM corpus.round3m_descriptor_assertion
    WHERE descriptor_assertion_id = NEW.left_descriptor_assertion_id;

    SELECT * INTO STRICT right_assertion
    FROM corpus.round3m_descriptor_assertion
    WHERE descriptor_assertion_id = NEW.right_descriptor_assertion_id;

    IF left_assertion.effective_record_key IS DISTINCT FROM
          right_assertion.effective_record_key
       OR left_assertion.effective_record_key IS DISTINCT FROM
          NEW.effective_record_key
       OR left_assertion.source_observation_key IS DISTINCT FROM
          right_assertion.source_observation_key
       OR left_assertion.source_observation_key IS DISTINCT FROM
          NEW.source_observation_key
       OR left_assertion.evidence_tier NOT IN ('P1', 'P2')
       OR right_assertion.evidence_tier NOT IN ('P1', 'P2')
       OR left_assertion.descriptor_class NOT IN (
            'STRICT_FLAVOR', 'BROAD_SENSORY'
       )
       OR right_assertion.descriptor_class NOT IN (
            'STRICT_FLAVOR', 'BROAD_SENSORY'
       )
       OR left_assertion.deduplication_disposition NOT IN (
            'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
            'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
       )
       OR right_assertion.deduplication_disposition NOT IN (
            'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
            'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_effective_record_boundary_ck',
            MESSAGE = 'co-assertion pairs require two countable P1/P2 descriptors from one governed effective record and one observation';
    END IF;

    RETURN NEW;
END
$validate_round3m_coassertion_boundary$;

CREATE TRIGGER round3m_coassertion_boundary_biu
BEFORE INSERT OR UPDATE ON corpus.round3m_coassertion_event
FOR EACH ROW EXECUTE FUNCTION corpus.validate_round3m_coassertion_boundary();

CREATE TABLE audit.round3m_descriptor_holdout (
    descriptor_holdout_id BIGINT GENERATED ALWAYS AS IDENTITY,
    holdout_key TEXT NOT NULL,
    holdout_kind TEXT NOT NULL,
    holdout_value TEXT NOT NULL,
    declared_at TIMESTAMPTZ NOT NULL,
    declaration_receipt_sha256 TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT round3m_descriptor_holdout_pk PRIMARY KEY (
        descriptor_holdout_id
    ),
    CONSTRAINT round3m_descriptor_holdout_key_uq UNIQUE (holdout_key),
    CONSTRAINT round3m_descriptor_holdout_value_uq UNIQUE (
        holdout_kind, holdout_value
    ),
    CONSTRAINT round3m_descriptor_holdout_text_ck CHECK (
        holdout_key = lower(btrim(holdout_key))
        AND holdout_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND holdout_kind IN ('INDEPENDENT_SOURCE_FAMILY', 'EDITION_YEAR')
        AND holdout_value = lower(btrim(holdout_value))
        AND holdout_value <> ''
        AND declaration_receipt_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_descriptor_holdout_year_ck CHECK (
        holdout_kind <> 'EDITION_YEAR'
        OR holdout_value ~ '^[0-9]{4}$'
           AND holdout_value::INTEGER BETWEEN 1900 AND 2100
    )
);

CREATE TABLE audit.round3m_analyst_time_log (
    analyst_time_log_id BIGINT GENERATED ALWAYS AS IDENTITY,
    analyst_time_log_key TEXT NOT NULL,
    task_type TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    source_route_id TEXT,
    artifact_count BIGINT NOT NULL,
    candidate_count BIGINT NOT NULL,
    reviewed_count BIGINT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NOT NULL,
    active_minutes NUMERIC(12, 3) NOT NULL,
    automated_runtime_seconds NUMERIC(16, 3),
    review_actor_type TEXT NOT NULL,
    notes TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_analyst_time_log_pk PRIMARY KEY (
        analyst_time_log_id
    ),
    CONSTRAINT round3m_analyst_time_log_key_uq UNIQUE (
        analyst_time_log_key
    ),
    CONSTRAINT round3m_analyst_time_log_route_fk FOREIGN KEY (
        source_route_id
    ) REFERENCES evidence.round3m_source_route (source_route_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_analyst_time_log_text_ck CHECK (
        analyst_time_log_key = lower(btrim(analyst_time_log_key))
        AND analyst_time_log_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND task_type IN (
            'SOURCE_DISCOVERY', 'SOURCE_RETRIEVAL', 'SCHEMA_AUDIT',
            'ADAPTER_VALIDATION', 'DESCRIPTOR_SEGMENTATION',
            'PROVISIONAL_SOURCE_AUDIT', 'HUMAN_REVIEW',
            'EXPERT_ADJUDICATION', 'RIGHTS_REVIEW',
            'DUPLICATE_REVIEW', 'RECONCILIATION'
        )
        AND scope_type IN ('SOURCE_ROUTE', 'MULTIPLE_ROUTES')
        AND (
            scope_type = 'SOURCE_ROUTE'
            AND source_route_id IS NOT NULL
            OR scope_type = 'MULTIPLE_ROUTES'
            AND source_route_id IS NULL
        )
        AND artifact_count >= 0
        AND candidate_count >= 0
        AND reviewed_count >= 0
        AND ended_at >= started_at
        AND active_minutes >= 0
        AND (
            automated_runtime_seconds IS NULL
            OR automated_runtime_seconds >= 0
        )
        AND review_actor_type IN (
            'AUTOMATED_PARSER', 'MACHINE_CLASSIFIER',
            'CODEX_SOURCE_AUDITOR', 'HUMAN_REVIEWER',
            'EXPERT_REVIEWER'
        )
        AND notes = btrim(notes) AND notes <> ''
    )
);

-- Existing Round 3L gate-shaped candidates and new live hash-only candidates
-- enter a public-safe review queue before any descriptor row is admitted to
-- the atomic ledger above. These rows deliberately have text natural IDs:
-- they are dispositions of candidates, not asserted coffee observations.
CREATE TABLE audit.round3m_descriptor_review_queue_item (
    review_queue_id TEXT NOT NULL,
    descriptor_assertion_id TEXT NOT NULL,
    professional_record_id TEXT NOT NULL,
    source_family_id TEXT NOT NULL,
    source_route_id TEXT NOT NULL,
    edition_id TEXT,
    edition_year INTEGER,
    source_artifact_id TEXT NOT NULL,
    source_file_sha256 TEXT NOT NULL,
    route_index_sha256 TEXT NOT NULL,
    source_file_sha256_scope TEXT NOT NULL,
    source_file_nonstorage_reason TEXT NOT NULL,
    raw_record_sha256 TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    source_language TEXT NOT NULL,
    source_text_sha256 TEXT NOT NULL,
    source_text_storage_state TEXT NOT NULL,
    source_text_non_storage_reason TEXT NOT NULL,
    source_field_contract TEXT NOT NULL,
    publication_layer TEXT NOT NULL,
    descriptor_class TEXT NOT NULL,
    evidence_tier TEXT NOT NULL,
    review_state TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    current_disposition TEXT NOT NULL,
    disposition_reason_code TEXT NOT NULL,
    human_review_required BOOLEAN NOT NULL,
    model_eligible BOOLEAN NOT NULL,
    decision_effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_descriptor_review_queue_item_pk PRIMARY KEY (
        review_queue_id
    ),
    CONSTRAINT round3m_descriptor_review_queue_assertion_uq UNIQUE (
        descriptor_assertion_id
    ),
    CONSTRAINT round3m_descriptor_review_queue_assertion_artifact_uq UNIQUE (
        descriptor_assertion_id, source_artifact_id
    ),
    CONSTRAINT round3m_descriptor_review_queue_text_ck CHECK (
        review_queue_id = lower(btrim(review_queue_id))
        AND review_queue_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND descriptor_assertion_id = lower(btrim(descriptor_assertion_id))
        AND descriptor_assertion_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND professional_record_id = btrim(professional_record_id)
        AND professional_record_id <> ''
        AND source_family_id = lower(btrim(source_family_id))
        AND source_family_id <> ''
        AND source_artifact_id = lower(btrim(source_artifact_id))
        AND source_artifact_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND source_route_id = lower(btrim(source_route_id))
        AND source_route_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND (
            edition_id IS NULL AND edition_year IS NULL
            OR edition_id = btrim(edition_id) AND edition_id <> ''
               AND edition_year BETWEEN 1900 AND 2100
        )
        AND source_locator = btrim(source_locator)
        AND source_locator <> ''
        AND (
            source_file_sha256 = ''
            OR source_file_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND (
            route_index_sha256 = ''
            OR route_index_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND num_nonnulls(
            NULLIF(source_file_sha256, ''),
            NULLIF(route_index_sha256, '')
        ) >= 1
        AND source_file_sha256_scope = btrim(source_file_sha256_scope)
        AND source_file_sha256_scope <> ''
        AND source_file_nonstorage_reason =
            btrim(source_file_nonstorage_reason)
        AND (
            source_file_sha256 <> ''
            OR source_file_nonstorage_reason <> ''
        )
        AND (
            raw_record_sha256 = ''
            OR raw_record_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND source_language = btrim(source_language)
        AND source_language <> ''
        AND source_text_sha256 ~ '^[0-9a-f]{64}$'
        AND source_text_storage_state IN (
            'HASH_ONLY', 'CAPTURED_RESTRICTED', 'REVIEWED_TEXT'
        )
        AND source_text_non_storage_reason =
            btrim(source_text_non_storage_reason)
        AND source_text_non_storage_reason <> ''
        AND source_field_contract = btrim(source_field_contract)
        AND source_field_contract <> ''
        AND publication_layer IN (
            'PRIMARY_JURY_DESCRIPTION',
            'GENERIC_ORGANIZER_SENSORY_FIELD',
            'PRODUCER_OR_FARM_PROFILE',
            'SECONDARY_SENSORY_TABLE',
            'JUDGE_LEVEL_OBSERVATION',
            'RESULT_METADATA',
            'PROTOCOL_OR_BLANK_FORM'
        )
        AND descriptor_class IN (
            'STRICT_FLAVOR', 'BROAD_SENSORY', 'NON_DESCRIPTOR'
        )
        AND evidence_tier IN (
            'P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'UNRESOLVED'
        )
        AND review_state IN (
            'AUTO_EXTRACTED', 'PROVISIONAL_MACHINE_CLASSIFIED',
            'SOURCE_AUDITED', 'HUMAN_CONFIRMED',
            'EXPERT_ADJUDICATED', 'REJECTED_NON_DESCRIPTOR',
            'REJECTED_DUPLICATE', 'SOURCE_UNAVAILABLE',
            'PROVENANCE_UNRESOLVED', 'RIGHTS_BLOCKED'
        )
        AND review_actor_type IN (
            'AUTOMATED_PARSER', 'MACHINE_CLASSIFIER',
            'CODEX_SOURCE_AUDITOR', 'HUMAN_REVIEWER',
            'EXPERT_REVIEWER'
        )
        AND current_disposition IN (
            'SOURCE_AUDIT_COMPLETE', 'HUMAN_REVIEW_REQUIRED',
            'SOURCE_UNAVAILABLE', 'NON_DESCRIPTOR',
            'DUPLICATE_OR_REPEAT', 'PUBLICATION_LAYER_CONFLICT',
            'PROVENANCE_UNRESOLVED', 'RIGHTS_BLOCKED',
            'OUT_OF_CORE_TIER'
        )
        AND disposition_reason_code =
            upper(btrim(disposition_reason_code))
        AND disposition_reason_code <> ''
    ),
    CONSTRAINT round3m_descriptor_review_queue_provisional_ck CHECK (
        review_actor_type NOT IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
        AND review_state NOT IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
        AND model_eligible IS FALSE
    )
);

CREATE TABLE audit.round3m_descriptor_provisional_decision (
    decision_id TEXT NOT NULL,
    review_queue_id TEXT NOT NULL,
    descriptor_assertion_id TEXT NOT NULL,
    current_disposition TEXT NOT NULL,
    descriptor_class TEXT NOT NULL,
    review_state TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    review_protocol_version TEXT NOT NULL,
    decision_reason_code TEXT NOT NULL,
    decision_basis TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    source_file_sha256 TEXT NOT NULL,
    route_index_sha256 TEXT NOT NULL,
    source_file_sha256_scope TEXT NOT NULL,
    source_file_nonstorage_reason TEXT NOT NULL,
    source_text_sha256 TEXT NOT NULL,
    human_confirmed BOOLEAN NOT NULL,
    expert_adjudicated BOOLEAN NOT NULL,
    counts_as_reviewed_descriptor BOOLEAN NOT NULL,
    model_eligible BOOLEAN NOT NULL,
    decision_effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_descriptor_provisional_decision_pk PRIMARY KEY (
        decision_id
    ),
    CONSTRAINT round3m_descriptor_provisional_queue_uq UNIQUE (
        review_queue_id
    ),
    CONSTRAINT round3m_descriptor_provisional_assertion_uq UNIQUE (
        descriptor_assertion_id
    ),
    CONSTRAINT round3m_descriptor_provisional_queue_fk FOREIGN KEY (
        review_queue_id
    ) REFERENCES audit.round3m_descriptor_review_queue_item (
        review_queue_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_provisional_text_ck CHECK (
        decision_id = lower(btrim(decision_id))
        AND decision_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND descriptor_assertion_id = lower(btrim(descriptor_assertion_id))
        AND descriptor_assertion_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND current_disposition IN (
            'SOURCE_AUDIT_COMPLETE', 'HUMAN_REVIEW_REQUIRED',
            'SOURCE_UNAVAILABLE', 'NON_DESCRIPTOR',
            'DUPLICATE_OR_REPEAT', 'PUBLICATION_LAYER_CONFLICT',
            'PROVENANCE_UNRESOLVED', 'RIGHTS_BLOCKED',
            'OUT_OF_CORE_TIER'
        )
        AND descriptor_class IN (
            'STRICT_FLAVOR', 'BROAD_SENSORY', 'NON_DESCRIPTOR'
        )
        AND review_state IN (
            'AUTO_EXTRACTED', 'PROVISIONAL_MACHINE_CLASSIFIED',
            'SOURCE_AUDITED', 'HUMAN_CONFIRMED',
            'EXPERT_ADJUDICATED', 'REJECTED_NON_DESCRIPTOR',
            'REJECTED_DUPLICATE', 'SOURCE_UNAVAILABLE',
            'PROVENANCE_UNRESOLVED', 'RIGHTS_BLOCKED'
        )
        AND review_actor_type IN (
            'AUTOMATED_PARSER', 'MACHINE_CLASSIFIER',
            'CODEX_SOURCE_AUDITOR', 'HUMAN_REVIEWER',
            'EXPERT_REVIEWER'
        )
        AND review_protocol_version = btrim(review_protocol_version)
        AND review_protocol_version <> ''
        AND decision_reason_code = upper(btrim(decision_reason_code))
        AND decision_reason_code <> ''
        AND decision_basis = btrim(decision_basis)
        AND decision_basis <> ''
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
        AND (
            source_file_sha256 = ''
            OR source_file_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND (
            route_index_sha256 = ''
            OR route_index_sha256 ~ '^[0-9a-f]{64}$'
        )
        AND num_nonnulls(
            NULLIF(source_file_sha256, ''),
            NULLIF(route_index_sha256, '')
        ) >= 1
        AND source_file_sha256_scope = btrim(source_file_sha256_scope)
        AND source_file_sha256_scope <> ''
        AND source_file_nonstorage_reason =
            btrim(source_file_nonstorage_reason)
        AND (
            source_file_sha256 <> ''
            OR source_file_nonstorage_reason <> ''
        )
        AND source_text_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_descriptor_provisional_no_human_impersonation_ck CHECK (
        (
            human_confirmed
            OR expert_adjudicated
            OR counts_as_reviewed_descriptor
            OR model_eligible
        ) IS FALSE
        AND review_actor_type NOT IN (
            'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
        )
        AND review_state NOT IN (
            'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
        )
    ),
    CONSTRAINT round3m_descriptor_provisional_queue_identity_ck CHECK (
        descriptor_assertion_id <> ''
    )
);

CREATE FUNCTION audit.validate_round3m_provisional_queue_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_provisional_queue_identity$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_queue_item AS queue_item
        WHERE queue_item.review_queue_id = NEW.review_queue_id
          AND queue_item.descriptor_assertion_id =
              NEW.descriptor_assertion_id
          AND queue_item.current_disposition = NEW.current_disposition
          AND queue_item.descriptor_class = NEW.descriptor_class
          AND queue_item.review_state = NEW.review_state
          AND queue_item.review_actor_type = NEW.review_actor_type
          AND queue_item.decision_effective_date =
              NEW.decision_effective_date
          AND queue_item.source_file_sha256 = NEW.source_file_sha256
          AND queue_item.route_index_sha256 = NEW.route_index_sha256
          AND queue_item.source_file_sha256_scope =
              NEW.source_file_sha256_scope
          AND queue_item.source_file_nonstorage_reason =
              NEW.source_file_nonstorage_reason
          AND queue_item.source_text_sha256 = NEW.source_text_sha256
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_provisional_queue_identity_ck',
            MESSAGE = 'provisional decision must preserve queue assertion, disposition, and hashes';
    END IF;

    RETURN NEW;
END
$validate_round3m_provisional_queue_identity$;

CREATE TRIGGER round3m_descriptor_provisional_queue_biu
BEFORE INSERT OR UPDATE ON audit.round3m_descriptor_provisional_decision
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_provisional_queue_identity();

-- The public live-ledger `review_receipt_id` values are machine provisional
-- decision identifiers, not human receipts.  Preserve that lineage in a
-- separately typed pointer so a machine decision can never impersonate the
-- BIGINT actual-human receipt used by reviewed/model-eligible universes.
ALTER TABLE corpus.round3m_descriptor_assertion
    ADD COLUMN provisional_decision_id TEXT,
    ADD CONSTRAINT round3m_descriptor_provisional_decision_uq UNIQUE (
        provisional_decision_id
    ),
    ADD CONSTRAINT round3m_descriptor_provisional_decision_fk FOREIGN KEY (
        provisional_decision_id
    ) REFERENCES audit.round3m_descriptor_provisional_decision (decision_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT;

CREATE FUNCTION corpus.validate_round3m_provisional_decision_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_provisional_decision_lineage$
BEGIN
    IF NEW.provisional_decision_id IS NULL THEN
        RETURN NEW;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_provisional_decision AS decision
        JOIN audit.round3m_descriptor_review_queue_item AS queue_item
          ON queue_item.review_queue_id = decision.review_queue_id
        WHERE decision.decision_id = NEW.provisional_decision_id
          AND decision.descriptor_assertion_id =
              NEW.descriptor_assertion_key
          AND decision.descriptor_class = NEW.descriptor_class
          AND queue_item.source_artifact_id = NEW.source_artifact_id
          AND decision.source_file_sha256 = NEW.source_file_sha256
          AND decision.route_index_sha256 = NEW.route_index_sha256
          AND decision.source_file_sha256_scope =
              NEW.source_file_sha256_scope
          AND decision.source_file_nonstorage_reason =
              NEW.source_file_nonstorage_reason
          AND decision.source_text_sha256 = NEW.atomic_source_text_sha256
          AND decision.human_confirmed IS FALSE
          AND decision.expert_adjudicated IS FALSE
          AND decision.counts_as_reviewed_descriptor IS FALSE
          AND decision.model_eligible IS FALSE
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_provisional_lineage_ck',
            MESSAGE = 'provisional pointer must preserve the same machine decision, artifact, descriptor class, and source hashes';
    END IF;

    RETURN NEW;
END
$validate_round3m_provisional_decision_lineage$;

CREATE TRIGGER round3m_descriptor_provisional_decision_biu
BEFORE INSERT OR UPDATE OF provisional_decision_id,
    descriptor_assertion_key, descriptor_class, source_artifact_id,
    source_file_sha256, route_index_sha256, source_file_sha256_scope,
    source_file_nonstorage_reason, atomic_source_text_sha256
ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_round3m_provisional_decision_lineage();

CREATE TABLE evidence.round3m_candidate_rights_decision (
    rights_decision_id TEXT NOT NULL,
    descriptor_assertion_id TEXT NOT NULL,
    source_artifact_id TEXT NOT NULL,
    purpose TEXT NOT NULL,
    rights_state TEXT NOT NULL,
    decision_basis TEXT NOT NULL,
    rights_evidence_locator TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    model_eligibility_effect TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_candidate_rights_decision_pk PRIMARY KEY (
        rights_decision_id
    ),
    CONSTRAINT round3m_candidate_rights_assertion_purpose_uq UNIQUE (
        descriptor_assertion_id, purpose
    ),
    CONSTRAINT round3m_candidate_rights_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES audit.round3m_descriptor_review_queue_item (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_candidate_rights_artifact_scope_fk FOREIGN KEY (
        descriptor_assertion_id, source_artifact_id
    ) REFERENCES audit.round3m_descriptor_review_queue_item (
        descriptor_assertion_id, source_artifact_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_candidate_rights_text_ck CHECK (
        rights_decision_id = lower(btrim(rights_decision_id))
        AND rights_decision_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND descriptor_assertion_id = lower(btrim(descriptor_assertion_id))
        AND descriptor_assertion_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND source_artifact_id = lower(btrim(source_artifact_id))
        AND source_artifact_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND purpose IN (
            'PUBLIC_DISCOVERY', 'INTERNAL_RESEARCH_ANALYSIS',
            'DERIVED_RESEARCH_DATA', 'MODEL_RESEARCH',
            'DEPLOYMENT_OR_COMMERCIAL_MODEL', 'RAW_REDISTRIBUTION'
        )
        AND rights_state IN (
            'AFFIRMATIVE', 'PENDING', 'UNKNOWN',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND decision_basis = btrim(decision_basis)
        AND decision_basis <> ''
        AND rights_evidence_locator = btrim(rights_evidence_locator)
        AND rights_evidence_locator <> ''
        AND review_actor_type IN (
            'CODEX_SOURCE_AUDITOR', 'HUMAN_RIGHTS_REVIEWER',
            'LEGAL_REVIEWER', 'RIGHTS_HOLDER', 'AUTOMATED_PARSER'
        )
        AND model_eligibility_effect IN (
            'NO_EFFECT', 'BLOCKS_MODEL_ELIGIBILITY',
            'SUPPORTS_MODEL_ELIGIBILITY', 'BLOCKS_DEPLOYMENT_ELIGIBILITY',
            'SUPPORTS_DEPLOYMENT_ELIGIBILITY',
            'INELIGIBLE_NON_DESCRIPTOR_AND_NO_AFFIRMATIVE_RIGHTS',
            'INELIGIBLE_PENDING_OR_UNKNOWN_RIGHTS_AND_NO_HUMAN_REVIEW'
        )
    ),
    CONSTRAINT round3m_candidate_public_visibility_not_permission_ck CHECK (
        NOT (
            purpose IN (
                'MODEL_RESEARCH', 'DEPLOYMENT_OR_COMMERCIAL_MODEL'
            )
            AND rights_state = 'AFFIRMATIVE'
            AND review_actor_type IN (
                'CODEX_SOURCE_AUDITOR', 'AUTOMATED_PARSER'
            )
        )
        AND (
            purpose <> 'MODEL_RESEARCH'
            OR (
                rights_state = 'AFFIRMATIVE'
                AND model_eligibility_effect =
                    'SUPPORTS_MODEL_ELIGIBILITY'
                OR rights_state <> 'AFFIRMATIVE'
                   AND model_eligibility_effect IN (
                       'BLOCKS_MODEL_ELIGIBILITY',
                       'INELIGIBLE_NON_DESCRIPTOR_AND_NO_AFFIRMATIVE_RIGHTS',
                       'INELIGIBLE_PENDING_OR_UNKNOWN_RIGHTS_AND_NO_HUMAN_REVIEW'
                   )
            )
        )
        AND (
            purpose <> 'DEPLOYMENT_OR_COMMERCIAL_MODEL'
            OR (
                rights_state = 'AFFIRMATIVE'
                AND model_eligibility_effect =
                    'SUPPORTS_DEPLOYMENT_ELIGIBILITY'
                OR rights_state <> 'AFFIRMATIVE'
                   AND model_eligibility_effect IN (
                       'BLOCKS_DEPLOYMENT_ELIGIBILITY',
                       'INELIGIBLE_NON_DESCRIPTOR_AND_NO_AFFIRMATIVE_RIGHTS',
                       'INELIGIBLE_PENDING_OR_UNKNOWN_RIGHTS_AND_NO_HUMAN_REVIEW'
                   )
            )
        )
        AND (
            rights_state = 'AFFIRMATIVE'
            OR model_eligibility_effect NOT IN (
                'SUPPORTS_MODEL_ELIGIBILITY',
                'SUPPORTS_DEPLOYMENT_ELIGIBILITY'
            )
        )
    )
);

COMMENT ON TABLE audit.round3m_descriptor_review_queue_item IS
    'Public-safe hash/locator queue for pre-admission candidates. Queue completion is not human review and never contributes descriptor gate counts.';
COMMENT ON TABLE audit.round3m_descriptor_provisional_decision IS
    'One current machine/source-audit disposition per queued candidate. Human/expert and reviewed/model flags are structurally forbidden here.';
COMMENT ON TABLE evidence.round3m_candidate_rights_decision IS
    'Six purpose-specific rights rows per queued candidate. These assessed states do not admit a candidate to the descriptor ledger.';

-- Versioned decisions and source artifacts are append-only. Corrections use
-- explicit supersession or a new schema/artifact version.
CREATE FUNCTION audit.reject_round3m_immutable_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $reject_round3m_immutable_mutation$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '23514',
        CONSTRAINT = 'round3m_immutable_evidence_ck',
        MESSAGE = format('%I.%I rows are immutable; append a versioned successor',
                         TG_TABLE_SCHEMA, TG_TABLE_NAME);
END
$reject_round3m_immutable_mutation$;

CREATE TRIGGER round3m_source_schema_signature_immutable_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_source_schema_signature
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_source_artifact_immutable_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_source_artifact
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_descriptor_rights_immutable_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_descriptor_rights_decision
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_descriptor_review_receipt_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_review_receipt
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_descriptor_review_queue_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_review_queue_item
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_descriptor_provisional_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_provisional_decision
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_candidate_rights_immutable_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_candidate_rights_decision
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

COMMENT ON TABLE corpus.round3m_descriptor_assertion IS
    'Atomic descriptor-first ledger. Each row has one effective record, artifact, route/schema, bounded source location, origin decision, rights decision, review state, and de-inflation disposition.';
COMMENT ON TABLE audit.round3m_descriptor_review_receipt IS
    'Append-only review evidence. HUMAN_CONFIRMED and EXPERT_ADJUDICATED are impossible without a documented actual-human receipt; Codex actor rows remain provisional/source-audit decisions.';
COMMENT ON TABLE evidence.round3m_descriptor_rights_decision IS
    'Field-, publication-layer-, route-, and purpose-specific rights decision. Public visibility alone cannot confer model or deployment permission.';
COMMENT ON TABLE corpus.round3m_coassertion_event IS
    'Unordered descriptor pair inside one governed effective record and one source observation; cross-record and unrelated-judge pairs are rejected.';
COMMENT ON TABLE audit.round3m_analyst_time_log IS
    'Round-local analyst-equivalent timing only. Historical hours must not be reconstructed or fabricated.';

COMMIT;
