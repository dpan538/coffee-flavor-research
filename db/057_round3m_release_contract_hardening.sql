BEGIN;

-- Forward-only release hardening for the already-applied Round 3M migrations.
-- Migration 055/056 remain immutable; this migration tightens their final
-- catalog contract without rewriting historical migration text.

-- The public checkpoint contained no actual-human reviewed assertions.  A
-- database that does contain one must not silently acquire new semantic
-- rules whose earlier human evidence did not bind.
DO $round3m_no_prehardening_human_rows$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion
        WHERE review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
    ) OR EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt
        WHERE review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewed_semantics_historical_binding_ck',
            MESSAGE = 'Round 3M release hardening requires zero pre-hardening human/expert assertions';
    END IF;
END
$round3m_no_prehardening_human_rows$;

-- One governed organizer/rights origin is one independent family.  Routes
-- cannot be reassigned later to manufacture diversity.
DO $round3m_existing_family_origin_unique$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM evidence.round3m_independent_source_family
        GROUP BY organizer_id, rights_lineage_id
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_independent_source_family_origin_uq',
            MESSAGE = 'one organizer and rights lineage cannot be split across independent-family identifiers';
    END IF;
END
$round3m_existing_family_origin_unique$;

ALTER TABLE evidence.round3m_independent_source_family
    ADD CONSTRAINT round3m_independent_source_family_origin_uq UNIQUE (
        organizer_id, rights_lineage_id
    );

CREATE FUNCTION evidence.validate_round3m_source_route_family_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_source_route_family_scope$
DECLARE
    family evidence.round3m_independent_source_family%ROWTYPE;
BEGIN
    SELECT * INTO STRICT family
    FROM evidence.round3m_independent_source_family
    WHERE independent_source_family_id = NEW.independent_source_family_id;

    IF family.organizer_id IS DISTINCT FROM NEW.organizer_id
       OR family.rights_lineage_id IS DISTINCT FROM
          NEW.rights_lineage_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_source_route_family_scope_ck',
            MESSAGE = 'source route organizer and rights lineage must match its independent family';
    END IF;

    RETURN NEW;
END
$validate_round3m_source_route_family_scope$;

CREATE TRIGGER round3m_source_route_family_scope_biu
BEFORE INSERT OR UPDATE ON evidence.round3m_source_route
FOR EACH ROW EXECUTE FUNCTION
    evidence.validate_round3m_source_route_family_scope();

-- A resolved mirror lineage is a single publication-equivalence identity.
-- Normalize that identity into a parent row so concurrent route inserts
-- cannot assign one resolved mirror lineage to multiple independent families.
-- ``unresolved`` is an explicit absence-of-resolution sentinel, not an
-- equivalence identity, and therefore remains scoped to each family.
CREATE TABLE evidence.round3m_mirror_lineage_family (
    mirror_lineage_id TEXT NOT NULL,
    independent_source_family_id TEXT NOT NULL,
    CONSTRAINT round3m_mirror_lineage_family_pk PRIMARY KEY (
        mirror_lineage_id, independent_source_family_id
    ),
    CONSTRAINT round3m_mirror_lineage_family_family_fk FOREIGN KEY (
        independent_source_family_id
    ) REFERENCES evidence.round3m_independent_source_family (
        independent_source_family_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_mirror_lineage_family_text_ck CHECK (
        mirror_lineage_id = lower(btrim(mirror_lineage_id))
        AND mirror_lineage_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
    )
);

CREATE UNIQUE INDEX round3m_resolved_mirror_lineage_family_uq
    ON evidence.round3m_mirror_lineage_family (mirror_lineage_id)
    WHERE mirror_lineage_id <> 'unresolved';

INSERT INTO evidence.round3m_mirror_lineage_family (
    mirror_lineage_id, independent_source_family_id
)
SELECT DISTINCT mirror_lineage_id, independent_source_family_id
FROM evidence.round3m_source_route;

ALTER TABLE evidence.round3m_source_route
    ADD CONSTRAINT round3m_source_route_mirror_family_fk FOREIGN KEY (
        mirror_lineage_id, independent_source_family_id
    ) REFERENCES evidence.round3m_mirror_lineage_family (
        mirror_lineage_id, independent_source_family_id
    ) DEFERRABLE INITIALLY IMMEDIATE;

CREATE FUNCTION evidence.register_round3m_mirror_lineage_family()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $register_round3m_mirror_lineage_family$
BEGIN
    INSERT INTO evidence.round3m_mirror_lineage_family (
        mirror_lineage_id, independent_source_family_id
    ) VALUES (
        NEW.mirror_lineage_id, NEW.independent_source_family_id
    ) ON CONFLICT DO NOTHING;

    IF NEW.mirror_lineage_id <> 'unresolved'
       AND NOT EXISTS (
        SELECT 1
        FROM evidence.round3m_mirror_lineage_family AS mapping
        WHERE mapping.mirror_lineage_id = NEW.mirror_lineage_id
          AND mapping.independent_source_family_id =
              NEW.independent_source_family_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_mirror_lineage_one_family_ck',
            MESSAGE = 'one mirror lineage cannot be assigned to multiple independent source families';
    END IF;

    RETURN NEW;
END
$register_round3m_mirror_lineage_family$;

CREATE TRIGGER round3m_source_route_mirror_family_biu
BEFORE INSERT OR UPDATE ON evidence.round3m_source_route
FOR EACH ROW EXECUTE FUNCTION
    evidence.register_round3m_mirror_lineage_family();

CREATE TRIGGER round3m_mirror_lineage_family_immutable_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_mirror_lineage_family
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

-- A resolved lineage with more than one route needs one explicit canonical
-- publication route before another mirror can be registered.  This makes
-- publication credit a governed decision rather than an insertion-order or
-- host-name heuristic.
ALTER TABLE evidence.round3m_source_route
    ADD CONSTRAINT round3m_source_route_mirror_credit_fk_uq UNIQUE (
        source_route_id, mirror_lineage_id, independent_source_family_id
    );

CREATE TABLE evidence.round3m_mirror_lineage_credit_route (
    mirror_lineage_id TEXT NOT NULL,
    independent_source_family_id TEXT NOT NULL,
    canonical_source_route_id TEXT NOT NULL,
    decision_basis TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_mirror_lineage_credit_route_pk PRIMARY KEY (
        mirror_lineage_id
    ),
    CONSTRAINT round3m_mirror_lineage_credit_family_fk FOREIGN KEY (
        mirror_lineage_id, independent_source_family_id
    ) REFERENCES evidence.round3m_mirror_lineage_family (
        mirror_lineage_id, independent_source_family_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_mirror_lineage_credit_route_fk FOREIGN KEY (
        canonical_source_route_id, mirror_lineage_id,
        independent_source_family_id
    ) REFERENCES evidence.round3m_source_route (
        source_route_id, mirror_lineage_id, independent_source_family_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_mirror_lineage_credit_resolved_ck CHECK (
        mirror_lineage_id <> 'unresolved'
        AND decision_basis = btrim(decision_basis)
        AND decision_basis <> ''
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
        AND decided_at <= created_at
    )
);

COMMENT ON TABLE evidence.round3m_mirror_lineage_credit_route IS
    'Immutable explicit canonical route for a resolved multi-route publication lineage; all other routes are preserved as mirror publications but cannot receive descriptor credit.';

CREATE TRIGGER round3m_mirror_lineage_credit_route_immutable_bud
BEFORE UPDATE OR DELETE ON evidence.round3m_mirror_lineage_credit_route
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE OR REPLACE FUNCTION evidence.register_round3m_mirror_lineage_family()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $register_round3m_mirror_lineage_family$
BEGIN
    INSERT INTO evidence.round3m_mirror_lineage_family (
        mirror_lineage_id, independent_source_family_id
    ) VALUES (
        NEW.mirror_lineage_id, NEW.independent_source_family_id
    ) ON CONFLICT DO NOTHING;

    IF NEW.mirror_lineage_id <> 'unresolved'
       AND NOT EXISTS (
        SELECT 1
        FROM evidence.round3m_mirror_lineage_family AS mapping
        WHERE mapping.mirror_lineage_id = NEW.mirror_lineage_id
          AND mapping.independent_source_family_id =
              NEW.independent_source_family_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_mirror_lineage_one_family_ck',
            MESSAGE = 'one mirror lineage cannot be assigned to multiple independent source families';
    END IF;

    IF NEW.mirror_lineage_id <> 'unresolved' THEN
        -- Serialize route expansion through the normalized lineage parent.
        PERFORM mapping.mirror_lineage_id
        FROM evidence.round3m_mirror_lineage_family AS mapping
        WHERE mapping.mirror_lineage_id = NEW.mirror_lineage_id
          AND mapping.independent_source_family_id =
              NEW.independent_source_family_id
        FOR UPDATE;

        IF EXISTS (
            SELECT 1
            FROM evidence.round3m_source_route AS route
            WHERE route.mirror_lineage_id = NEW.mirror_lineage_id
              AND route.source_route_id <> NEW.source_route_id
        ) AND NOT EXISTS (
            SELECT 1
            FROM evidence.round3m_mirror_lineage_credit_route AS credit
            WHERE credit.mirror_lineage_id = NEW.mirror_lineage_id
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_mirror_credit_required_before_additional_route_ck',
                MESSAGE = 'select an immutable canonical credit route before registering another route in a resolved mirror lineage';
        END IF;
    END IF;

    RETURN NEW;
END
$register_round3m_mirror_lineage_family$;

DO $round3m_existing_resolved_mirror_credit_is_unambiguous$
BEGIN
    IF EXISTS (
        SELECT route.mirror_lineage_id
        FROM evidence.round3m_source_route AS route
        WHERE route.mirror_lineage_id <> 'unresolved'
        GROUP BY route.mirror_lineage_id
        HAVING count(*) > 1
           AND NOT EXISTS (
               SELECT 1
               FROM evidence.round3m_mirror_lineage_credit_route AS credit
               WHERE credit.mirror_lineage_id = route.mirror_lineage_id
           )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_existing_mirror_credit_route_ck',
            MESSAGE = 'pre-hardening multi-route mirror lineages require an explicit canonical credit route';
    END IF;
END
$round3m_existing_resolved_mirror_credit_is_unambiguous$;

DO $round3m_existing_route_family_scope$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM evidence.round3m_source_route AS route
        JOIN evidence.round3m_independent_source_family AS family
          ON family.independent_source_family_id =
             route.independent_source_family_id
        WHERE route.organizer_id IS DISTINCT FROM family.organizer_id
           OR route.rights_lineage_id IS DISTINCT FROM
              family.rights_lineage_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_source_route_family_scope_ck',
            MESSAGE = 'existing source routes must match their family organizer and rights lineage';
    END IF;
END
$round3m_existing_route_family_scope$;

CREATE FUNCTION evidence.protect_round3m_source_family_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_source_family_identity$
BEGIN
    IF OLD.organizer_id IS DISTINCT FROM NEW.organizer_id
       OR OLD.rights_lineage_id IS DISTINCT FROM
          NEW.rights_lineage_id
       OR OLD.admitted_for_descriptor_research IS DISTINCT FROM
          NEW.admitted_for_descriptor_research THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_source_family_identity_immutable_ck',
            MESSAGE = 'independent-family organizer, rights identity, and descriptor-research admission are immutable';
    END IF;
    RETURN NEW;
END
$protect_round3m_source_family_identity$;

CREATE TRIGGER round3m_source_family_identity_bu
BEFORE UPDATE ON evidence.round3m_independent_source_family
FOR EACH ROW EXECUTE FUNCTION
    evidence.protect_round3m_source_family_identity();

CREATE FUNCTION evidence.protect_round3m_source_route_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_source_route_identity$
BEGIN
    IF OLD.source_route_id IS DISTINCT FROM NEW.source_route_id
       OR OLD.independent_source_family_id IS DISTINCT FROM
          NEW.independent_source_family_id
       OR OLD.organizer_id IS DISTINCT FROM NEW.organizer_id
       OR OLD.publication_host IS DISTINCT FROM NEW.publication_host
       OR OLD.canonical_url IS DISTINCT FROM NEW.canonical_url
       OR OLD.route_pattern IS DISTINCT FROM NEW.route_pattern
       OR OLD.rights_lineage_id IS DISTINCT FROM NEW.rights_lineage_id
       OR OLD.mirror_lineage_id IS DISTINCT FROM NEW.mirror_lineage_id
       OR OLD.discovered_at IS DISTINCT FROM NEW.discovered_at
       OR OLD.created_at IS DISTINCT FROM NEW.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_source_route_identity_immutable_ck',
            MESSAGE = 'source-route family, host, rights, mirror, and discovery identity are immutable';
    END IF;
    RETURN NEW;
END
$protect_round3m_source_route_identity$;

CREATE TRIGGER round3m_source_route_identity_bu
BEFORE UPDATE ON evidence.round3m_source_route
FOR EACH ROW EXECUTE FUNCTION
    evidence.protect_round3m_source_route_identity();

CREATE FUNCTION corpus.validate_round3m_resolved_mirror_credit()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_resolved_mirror_credit$
DECLARE
    route evidence.round3m_source_route%ROWTYPE;
    route_count BIGINT;
    canonical_route_id TEXT;
BEGIN
    SELECT * INTO STRICT route
    FROM evidence.round3m_source_route
    WHERE source_route_id = NEW.source_route_id;

    IF route.mirror_lineage_id = 'unresolved'
       OR NEW.descriptor_class NOT IN (
           'STRICT_FLAVOR', 'BROAD_SENSORY'
       ) THEN
        RETURN NEW;
    END IF;

    SELECT count(*) INTO route_count
    FROM evidence.round3m_source_route AS peer
    WHERE peer.mirror_lineage_id = route.mirror_lineage_id;

    IF route_count <= 1 THEN
        RETURN NEW;
    END IF;

    SELECT credit.canonical_source_route_id INTO canonical_route_id
    FROM evidence.round3m_mirror_lineage_credit_route AS credit
    WHERE credit.mirror_lineage_id = route.mirror_lineage_id
    FOR KEY SHARE;

    IF canonical_route_id IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_resolved_mirror_credit_route_ck',
            MESSAGE = 'a multi-route resolved mirror lineage requires one explicit canonical credit route';
    END IF;

    IF NEW.source_route_id <> canonical_route_id
       AND (
           NEW.deduplication_disposition <> 'MIRROR_PUBLICATION'
           OR NEW.mirror_group IS DISTINCT FROM route.mirror_lineage_id
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_resolved_mirror_noncanonical_ck',
            MESSAGE = 'descriptor assertions from a noncanonical mirror route must remain preserved as noncounting MIRROR_PUBLICATION rows bound to the resolved lineage';
    END IF;

    RETURN NEW;
END
$validate_round3m_resolved_mirror_credit$;

CREATE TRIGGER round3m_resolved_mirror_credit_biu
BEFORE INSERT OR UPDATE ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_round3m_resolved_mirror_credit();

-- Event time and database-import time are separate. Historical rights and
-- reviews may be imported now, but neither a future event nor a caller-chosen
-- future import timestamp may become current before it exists.
DO $round3m_existing_evidence_chronology_is_nonfuture$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM evidence.round3m_descriptor_rights_decision
        WHERE decided_at > created_at
           OR created_at > transaction_timestamp()
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_rights_chronology_ck',
            MESSAGE = 'existing descriptor-rights decisions must have a historical event time no later than their database import time';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt
        WHERE reviewed_at > created_at
           OR created_at > transaction_timestamp()
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_receipt_chronology_ck',
            MESSAGE = 'existing descriptor-review receipts must have a historical event time no later than their database import time';
    END IF;
END
$round3m_existing_evidence_chronology_is_nonfuture$;

ALTER TABLE evidence.round3m_descriptor_rights_decision
    ADD CONSTRAINT round3m_descriptor_rights_chronology_ck CHECK (
        decided_at <= created_at
    );

ALTER TABLE audit.round3m_descriptor_review_receipt
    ADD CONSTRAINT round3m_descriptor_review_receipt_chronology_ck CHECK (
        reviewed_at <= created_at
    );

CREATE FUNCTION evidence.validate_round3m_descriptor_rights_chronology()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_rights_chronology$
BEGIN
    IF NEW.decided_at > NEW.created_at
       OR NEW.created_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_rights_chronology_ck',
            MESSAGE = 'descriptor-rights decided_at may be historical, but created_at must be the current database transaction import time';
    END IF;
    RETURN NEW;
END
$validate_round3m_descriptor_rights_chronology$;

CREATE TRIGGER round3m_descriptor_rights_chronology_bi
BEFORE INSERT ON evidence.round3m_descriptor_rights_decision
FOR EACH ROW EXECUTE FUNCTION
    evidence.validate_round3m_descriptor_rights_chronology();

CREATE FUNCTION audit.validate_round3m_descriptor_review_receipt_chronology()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_review_receipt_chronology$
BEGIN
    IF NEW.reviewed_at > NEW.created_at
       OR NEW.created_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_review_receipt_chronology_ck',
            MESSAGE = 'descriptor-review reviewed_at may be historical, but created_at must be the current database transaction import time';
    END IF;
    RETURN NEW;
END
$validate_round3m_descriptor_review_receipt_chronology$;

CREATE TRIGGER round3m_descriptor_review_receipt_chronology_bi
BEFORE INSERT ON audit.round3m_descriptor_review_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_descriptor_review_receipt_chronology();

-- Rights currentness is governed by the actual route/layer/field scope, not
-- by a caller-chosen scope label.  Multiple current leaves are safe only when
-- all six purpose decisions agree.
ALTER TABLE evidence.round3m_descriptor_rights_decision
    ADD CONSTRAINT round3m_deployment_requires_model_rights_ck CHECK (
        deployment_or_commercial_model <> 'AFFIRMATIVE'
        OR internal_research_analysis = 'AFFIRMATIVE'
           AND model_research = 'AFFIRMATIVE'
    );

CREATE OR REPLACE FUNCTION evidence.validate_round3m_rights_lineage()
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
       OR predecessor.publication_layer IS DISTINCT FROM
          NEW.publication_layer
       OR predecessor.source_field_label IS DISTINCT FROM
          NEW.source_field_label
       OR predecessor.decision_version <> NEW.decision_version - 1
       OR predecessor.decided_at > NEW.decided_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_rights_lineage_ck',
            MESSAGE = 'rights supersession must use the immediately prior decision for the exact route, publication layer, and source field';
    END IF;

    RETURN NEW;
END
$validate_round3m_rights_lineage$;

CREATE OR REPLACE VIEW evidence.v_round3m_current_descriptor_rights AS
WITH leaf AS (
    SELECT decision.*
    FROM evidence.round3m_descriptor_rights_decision AS decision
    WHERE NOT EXISTS (
        SELECT 1
        FROM evidence.round3m_descriptor_rights_decision AS successor
        WHERE successor.supersedes_rights_decision_id =
              decision.rights_decision_id
    )
      AND decision.decided_at <= decision.created_at
      AND decision.created_at <= transaction_timestamp()
), natural_scope AS (
    SELECT
        source_route_id, publication_layer, source_field_label,
        count(*)::INTEGER AS current_decision_count,
        count(DISTINCT (
            public_discovery, internal_research_analysis,
            derived_research_data, model_research,
            deployment_or_commercial_model, raw_redistribution
        )) = 1 AS unambiguous_current_decision
    FROM leaf
    GROUP BY source_route_id, publication_layer, source_field_label
)
SELECT leaf.*, natural_scope.current_decision_count,
       natural_scope.unambiguous_current_decision
FROM leaf
JOIN natural_scope
  USING (source_route_id, publication_layer, source_field_label);

-- Bind every bridge to a deterministic governed source identity.  The source
-- snapshot identity is included so merely minting a new artifact ID cannot
-- create another effective coffee record.
CREATE FUNCTION competition.round3m_effective_record_identity_sha256(
    series_id_value TEXT,
    edition_id_value TEXT,
    edition_year_value INTEGER,
    category_id_value TEXT,
    round_id_value TEXT,
    subject_kind_value TEXT,
    entry_or_lot_id_value TEXT,
    preparation_service_code_value TEXT,
    source_route_id_value TEXT,
    source_file_sha256_value TEXT,
    route_index_sha256_value TEXT,
    source_record_locator_value TEXT
)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
SET search_path = pg_catalog
AS $round3m_effective_record_identity_sha256$
SELECT audit.round3i_utf8_sha256(
    series_id_value || chr(31) ||
    edition_id_value || chr(31) ||
    edition_year_value::TEXT || chr(31) ||
    category_id_value || chr(31) ||
    round_id_value || chr(31) ||
    subject_kind_value || chr(31) ||
    entry_or_lot_id_value || chr(31) ||
    preparation_service_code_value || chr(31) ||
    source_route_id_value || chr(31) ||
    CASE WHEN source_file_sha256_value <> ''
         THEN 'file:' || source_file_sha256_value
         ELSE 'route-index:' || route_index_sha256_value END || chr(31) ||
    source_record_locator_value
)
$round3m_effective_record_identity_sha256$;

-- Upgrade already-loaded pre-hardening rows before making the binding
-- declarative.  This is a deterministic data migration, not a new identity.
UPDATE competition.round3m_effective_record_bridge
SET record_identity_sha256 =
    competition.round3m_effective_record_identity_sha256(
        series_id, edition_id, edition_year, category_id, round_id,
        subject_kind, entry_or_lot_id, preparation_service_code,
        source_route_id, source_file_sha256, route_index_sha256,
        source_record_locator
    );

ALTER TABLE competition.round3m_effective_record_bridge
    ADD CONSTRAINT round3m_effective_record_identity_hash_ck CHECK (
        record_identity_sha256 =
            competition.round3m_effective_record_identity_sha256(
                series_id, edition_id, edition_year, category_id, round_id,
                subject_kind, entry_or_lot_id, preparation_service_code,
                source_route_id, source_file_sha256, route_index_sha256,
                source_record_locator
            )
    );

DO $round3m_existing_effective_source_identity_unique$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM competition.round3m_effective_record_bridge
        GROUP BY
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END,
            source_record_locator,
            preparation_service_code
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_effective_record_source_identity_uq',
            MESSAGE = 'one governed snapshot record and preparation cannot mint multiple effective records';
    END IF;
END
$round3m_existing_effective_source_identity_unique$;

CREATE UNIQUE INDEX round3m_effective_record_source_identity_uq
    ON competition.round3m_effective_record_bridge (
        (CASE WHEN source_file_sha256 <> ''
              THEN 'file:' || source_file_sha256
              ELSE 'route-index:' || route_index_sha256 END),
        source_record_locator,
        preparation_service_code
    );

CREATE FUNCTION competition.protect_round3m_effective_record_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_effective_record_identity$
BEGIN
    IF (to_jsonb(OLD) - ARRAY[
            'preparation_service_id',
            'professional_acquisition_record_id',
            'identity_resolution_state'
        ]) IS DISTINCT FROM
       (to_jsonb(NEW) - ARRAY[
            'preparation_service_id',
            'professional_acquisition_record_id',
            'identity_resolution_state'
        ]) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_effective_record_identity_immutable_ck',
            MESSAGE = 'effective-record governed identity is immutable; only existing-identity resolution may advance';
    END IF;
    RETURN NEW;
END
$protect_round3m_effective_record_identity$;

CREATE TRIGGER round3m_effective_record_identity_bu
BEFORE UPDATE ON competition.round3m_effective_record_bridge
FOR EACH ROW EXECUTE FUNCTION
    competition.protect_round3m_effective_record_identity();

-- Artifact IDs are citations, not source identities.  Re-registering the
-- same governed snapshot locator under another ID cannot create new credit.
DO $round3m_existing_source_artifact_natural_unique$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM evidence.round3m_source_artifact
        GROUP BY
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END,
            governed_locator
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_source_artifact_natural_uq',
            MESSAGE = 'one governed snapshot locator cannot be re-registered under multiple artifact IDs';
    END IF;
END
$round3m_existing_source_artifact_natural_unique$;

CREATE UNIQUE INDEX round3m_source_artifact_natural_uq
    ON evidence.round3m_source_artifact (
        (CASE WHEN source_file_sha256 <> ''
              THEN 'file:' || source_file_sha256
              ELSE 'route-index:' || route_index_sha256 END),
        governed_locator
    );

-- Reverse publication-layer semantics prevent metadata, producer copy, and
-- generic organizer fields from being promoted through a P1/P2 label alone.
ALTER TABLE corpus.round3m_descriptor_assertion
    ADD CONSTRAINT round3m_publication_layer_semantics_ck CHECK (
        publication_layer = 'PRIMARY_JURY_DESCRIPTION'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'P2'
        AND evidence_origin_type IN (
            'EXPLICIT_TOP_JURY_FIELD',
            'ORGANIZER_PUBLISHED_EXPLICIT_JURY',
            'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION'
        )
        OR publication_layer = 'JUDGE_LEVEL_OBSERVATION'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'P1'
        AND evidence_origin_type IN (
            'EXPLICIT_IDENTIFIED_JUDGE', 'EXPLICIT_IDENTIFIED_PANEL'
        )
        OR publication_layer = 'PRODUCER_OR_FARM_PROFILE'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'P3'
        AND evidence_origin_type = 'PRODUCER_OR_FARM_DECLARED'
        OR publication_layer = 'GENERIC_ORGANIZER_SENSORY_FIELD'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'UNRESOLVED'
        AND evidence_origin_type IN (
            'GENERIC_ORGANIZER_FIELD_UNKNOWN_AUTHOR',
            'FREQUENCY_CODED_UNKNOWN_ACTOR',
            'FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED',
            'GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED'
        )
        OR publication_layer = 'SECONDARY_SENSORY_TABLE'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier <> 'P0'
        OR publication_layer = 'RESULT_METADATA'
        AND descriptor_class = 'NON_DESCRIPTOR'
        OR publication_layer = 'PROTOCOL_OR_BLANK_FORM'
        AND descriptor_class = 'NON_DESCRIPTOR'
        AND evidence_tier = 'P0'
        AND evidence_origin_type = 'PROTOCOL_RULE_OR_BLANK_FORM'
    );

ALTER TABLE corpus.round3m_descriptor_assertion
    ADD CONSTRAINT round3m_secondary_publication_layer_noncounting_ck CHECK (
        publication_layer <> 'SECONDARY_SENSORY_TABLE'
        OR deduplication_disposition NOT IN (
            'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
            'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
        )
    );

-- Exact source repeats cannot become countable merely by renaming an
-- observation or re-registering the same source snapshot under a new artifact
-- ID.  Row-specific selectors are the bounded occurrence identity.
DO $round3m_existing_countable_source_assertion_unique$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
          AND publication_layer <> 'SECONDARY_SENSORY_TABLE'
          AND deduplication_disposition IN (
              'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
              'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
          )
        GROUP BY
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END,
            source_page_or_record_locator,
            source_field_label_sha256,
            source_selector_or_locator,
            atomic_source_text_sha256
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_countable_source_assertion_natural_uq',
            MESSAGE = 'one bounded atomic source assertion cannot receive countable credit more than once';
    END IF;
END
$round3m_existing_countable_source_assertion_unique$;

CREATE UNIQUE INDEX round3m_countable_source_assertion_natural_uq
    ON corpus.round3m_descriptor_assertion (
        (CASE WHEN source_file_sha256 <> ''
              THEN 'file:' || source_file_sha256
              ELSE 'route-index:' || route_index_sha256 END),
        source_page_or_record_locator,
        source_field_label_sha256,
        source_selector_or_locator,
        atomic_source_text_sha256
    )
    WHERE descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
      AND publication_layer <> 'SECONDARY_SENSORY_TABLE'
      AND deduplication_disposition IN (
          'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
          'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
      );

DO $round3m_existing_coassertion_endpoint_pair_unique$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_coassertion_event AS left_event
        JOIN corpus.round3m_coassertion_event AS right_event
          ON left_event.coassertion_event_id < right_event.coassertion_event_id
         AND left_event.left_descriptor_assertion_id =
             right_event.left_descriptor_assertion_id
         AND left_event.right_descriptor_assertion_id =
             right_event.right_descriptor_assertion_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_endpoint_pair_uq',
            MESSAGE = 'existing co-assertion rows cannot repeat one assertion endpoint pair under another set key';
    END IF;
END
$round3m_existing_coassertion_endpoint_pair_unique$;

ALTER TABLE corpus.round3m_coassertion_event
    ADD CONSTRAINT round3m_coassertion_endpoint_pair_uq UNIQUE (
        left_descriptor_assertion_id,
        right_descriptor_assertion_id
    );

DO $round3m_existing_coassertion_set_identity$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_coassertion_event AS left_event
        JOIN corpus.round3m_coassertion_event AS right_event
          ON left_event.coassertion_event_id < right_event.coassertion_event_id
         AND (
              (
                  left_event.effective_record_key =
                      right_event.effective_record_key
                  AND left_event.source_observation_key =
                      right_event.source_observation_key
                  AND left_event.coassertion_set_key IS DISTINCT FROM
                      right_event.coassertion_set_key
              )
              OR (
                  left_event.coassertion_set_key =
                      right_event.coassertion_set_key
                  AND (
                      left_event.effective_record_key IS DISTINCT FROM
                          right_event.effective_record_key
                      OR left_event.source_observation_key IS DISTINCT FROM
                          right_event.source_observation_key
                  )
              )
         )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_set_identity_ck',
            MESSAGE = 'existing co-assertion set keys and governed record-observation identities must map one-to-one';
    END IF;
END
$round3m_existing_coassertion_set_identity$;

CREATE TABLE corpus.round3m_coassertion_set_identity (
    coassertion_set_key TEXT NOT NULL,
    effective_record_key TEXT NOT NULL,
    source_observation_key TEXT NOT NULL,
    CONSTRAINT round3m_coassertion_set_identity_pk PRIMARY KEY (
        coassertion_set_key
    ),
    CONSTRAINT round3m_coassertion_set_identity_observation_uq UNIQUE (
        effective_record_key, source_observation_key
    ),
    CONSTRAINT round3m_coassertion_set_identity_full_uq UNIQUE (
        coassertion_set_key, effective_record_key,
        source_observation_key
    ),
    CONSTRAINT round3m_coassertion_set_identity_text_ck CHECK (
        coassertion_set_key = lower(btrim(coassertion_set_key))
        AND coassertion_set_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND effective_record_key = lower(btrim(effective_record_key))
        AND effective_record_key <> ''
        AND source_observation_key = lower(btrim(source_observation_key))
        AND source_observation_key <> ''
    )
);

INSERT INTO corpus.round3m_coassertion_set_identity (
    coassertion_set_key, effective_record_key, source_observation_key
)
SELECT DISTINCT coassertion_set_key, effective_record_key,
       source_observation_key
FROM corpus.round3m_coassertion_event;

ALTER TABLE corpus.round3m_coassertion_event
    ADD CONSTRAINT round3m_coassertion_event_set_identity_fk FOREIGN KEY (
        coassertion_set_key, effective_record_key,
        source_observation_key
    ) REFERENCES corpus.round3m_coassertion_set_identity (
        coassertion_set_key, effective_record_key,
        source_observation_key
    ) DEFERRABLE INITIALLY IMMEDIATE;

CREATE FUNCTION corpus.register_round3m_coassertion_set_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $register_round3m_coassertion_set_identity$
BEGIN
    INSERT INTO corpus.round3m_coassertion_set_identity (
        coassertion_set_key, effective_record_key,
        source_observation_key
    ) VALUES (
        NEW.coassertion_set_key, NEW.effective_record_key,
        NEW.source_observation_key
    ) ON CONFLICT DO NOTHING;

    IF NOT EXISTS (
        SELECT 1
        FROM corpus.round3m_coassertion_set_identity AS identity
        WHERE identity.coassertion_set_key = NEW.coassertion_set_key
          AND identity.effective_record_key = NEW.effective_record_key
          AND identity.source_observation_key =
              NEW.source_observation_key
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_set_identity_ck',
            MESSAGE = 'one co-assertion set key must map to exactly one governed record-observation identity and vice versa';
    END IF;

    RETURN NEW;
END
$register_round3m_coassertion_set_identity$;

CREATE TRIGGER round3m_coassertion_set_identity_biu
BEFORE INSERT OR UPDATE ON corpus.round3m_coassertion_event
FOR EACH ROW EXECUTE FUNCTION
    corpus.register_round3m_coassertion_set_identity();

CREATE TRIGGER round3m_coassertion_set_identity_immutable_bud
BEFORE UPDATE OR DELETE ON corpus.round3m_coassertion_set_identity
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE FUNCTION corpus.validate_round3m_coassertion_set_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_coassertion_set_identity$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_coassertion_event AS event
        WHERE event.coassertion_event_id <> NEW.coassertion_event_id
          AND (
              (
                  event.effective_record_key = NEW.effective_record_key
                  AND event.source_observation_key =
                      NEW.source_observation_key
                  AND event.coassertion_set_key IS DISTINCT FROM
                      NEW.coassertion_set_key
              )
              OR (
                  event.coassertion_set_key = NEW.coassertion_set_key
                  AND (
                      event.effective_record_key IS DISTINCT FROM
                          NEW.effective_record_key
                      OR event.source_observation_key IS DISTINCT FROM
                          NEW.source_observation_key
                  )
              )
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_set_identity_ck',
            MESSAGE = 'one co-assertion set key must map to exactly one governed record-observation identity and vice versa';
    END IF;

    RETURN NEW;
END
$validate_round3m_coassertion_set_identity$;

CREATE CONSTRAINT TRIGGER round3m_coassertion_set_identity_ci
AFTER INSERT OR UPDATE ON corpus.round3m_coassertion_event
DEFERRABLE INITIALLY IMMEDIATE
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_round3m_coassertion_set_identity();

CREATE OR REPLACE FUNCTION corpus.validate_round3m_coassertion_boundary()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_coassertion_boundary$
DECLARE
    left_assertion corpus.round3m_descriptor_assertion%ROWTYPE;
    right_assertion corpus.round3m_descriptor_assertion%ROWTYPE;
BEGIN
    -- Serialize endpoint validation with any concurrent semantic/provenance
    -- mutation.  Lock in primary-key order so two reversed endpoint pairs
    -- cannot deadlock each other.
    PERFORM assertion.descriptor_assertion_id
    FROM corpus.round3m_descriptor_assertion AS assertion
    WHERE assertion.descriptor_assertion_id IN (
        NEW.left_descriptor_assertion_id,
        NEW.right_descriptor_assertion_id
    )
    ORDER BY assertion.descriptor_assertion_id
    FOR NO KEY UPDATE;

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
            MESSAGE = 'co-assertion pairs require two countable P1/P2 descriptors from one governed effective record and observation';
    END IF;

    IF left_assertion.source_artifact_id IS DISTINCT FROM
          right_assertion.source_artifact_id
       OR left_assertion.source_route_id IS DISTINCT FROM
          right_assertion.source_route_id
       OR left_assertion.schema_signature_id IS DISTINCT FROM
          right_assertion.schema_signature_id
       OR left_assertion.publication_layer IS DISTINCT FROM
          right_assertion.publication_layer
       OR left_assertion.publication_layer NOT IN (
            'PRIMARY_JURY_DESCRIPTION', 'JUDGE_LEVEL_OBSERVATION'
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_publication_boundary_ck',
            MESSAGE = 'co-assertion endpoints must share one primary artifact, route, schema, and publication layer';
    END IF;

    RETURN NEW;
END
$validate_round3m_coassertion_boundary$;

DO $round3m_existing_coassertion_full_boundary$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_coassertion_event AS event
        JOIN corpus.round3m_descriptor_assertion AS left_assertion
          ON left_assertion.descriptor_assertion_id =
             event.left_descriptor_assertion_id
        JOIN corpus.round3m_descriptor_assertion AS right_assertion
          ON right_assertion.descriptor_assertion_id =
             event.right_descriptor_assertion_id
        WHERE event.effective_record_key IS DISTINCT FROM
                  left_assertion.effective_record_key
           OR event.source_observation_key IS DISTINCT FROM
                  left_assertion.source_observation_key
           OR left_assertion.effective_record_key IS DISTINCT FROM
                  right_assertion.effective_record_key
           OR left_assertion.source_observation_key IS DISTINCT FROM
                  right_assertion.source_observation_key
           OR left_assertion.source_artifact_id IS DISTINCT FROM
                  right_assertion.source_artifact_id
           OR left_assertion.source_route_id IS DISTINCT FROM
                  right_assertion.source_route_id
           OR left_assertion.schema_signature_id IS DISTINCT FROM
                  right_assertion.schema_signature_id
           OR left_assertion.publication_layer IS DISTINCT FROM
                  right_assertion.publication_layer
           OR left_assertion.publication_layer NOT IN (
                  'PRIMARY_JURY_DESCRIPTION', 'JUDGE_LEVEL_OBSERVATION'
              )
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
              )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_publication_boundary_ck',
            MESSAGE = 'existing co-assertion rows must satisfy full record, observation, artifact, route, schema, and publication boundaries';
    END IF;
END
$round3m_existing_coassertion_full_boundary$;

CREATE FUNCTION corpus.protect_round3m_coassertion_endpoint_governance()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_coassertion_endpoint_governance$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_coassertion_event AS event
        WHERE event.left_descriptor_assertion_id = OLD.descriptor_assertion_id
           OR event.right_descriptor_assertion_id = OLD.descriptor_assertion_id
    )
       AND (to_jsonb(OLD) - ARRAY[
                'review_state', 'review_actor_type',
                'current_review_receipt_id', 'rights_decision_id'
           ]) IS DISTINCT FROM
           (to_jsonb(NEW) - ARRAY[
                'review_state', 'review_actor_type',
                'current_review_receipt_id', 'rights_decision_id'
           ]) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_coassertion_endpoint_governance_immutable_ck',
            MESSAGE = 'remove and regenerate co-assertion events before changing endpoint semantics or provenance';
    END IF;
    RETURN NEW;
END
$protect_round3m_coassertion_endpoint_governance$;

CREATE TRIGGER round3m_coassertion_endpoint_governance_bu
BEFORE UPDATE ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    corpus.protect_round3m_coassertion_endpoint_governance();

CREATE FUNCTION corpus.validate_round3m_descriptor_artifact_hash_scope()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_artifact_hash_scope$
DECLARE
    artifact evidence.round3m_source_artifact%ROWTYPE;
BEGIN
    SELECT * INTO STRICT artifact
    FROM evidence.round3m_source_artifact
    WHERE source_artifact_id = NEW.source_artifact_id;

    IF artifact.route_index_sha256 IS DISTINCT FROM
          NEW.route_index_sha256
       OR artifact.source_file_sha256_scope IS DISTINCT FROM
          NEW.source_file_sha256_scope
       OR artifact.source_file_nonstorage_reason IS DISTINCT FROM
          NEW.source_file_nonstorage_reason THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_artifact_lineage_ck',
            MESSAGE = 'descriptor assertion must retain exact artifact route-index hash, source-file hash scope, and non-storage reason';
    END IF;

    RETURN NEW;
END
$validate_round3m_descriptor_artifact_hash_scope$;

CREATE TRIGGER round3m_descriptor_artifact_hash_scope_biu
BEFORE INSERT OR UPDATE ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    corpus.validate_round3m_descriptor_artifact_hash_scope();

DO $round3m_existing_descriptor_artifact_hash_scope$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion AS assertion
        JOIN evidence.round3m_source_artifact AS artifact
          ON artifact.source_artifact_id = assertion.source_artifact_id
        WHERE artifact.route_index_sha256 IS DISTINCT FROM
                  assertion.route_index_sha256
           OR artifact.source_file_sha256_scope IS DISTINCT FROM
                  assertion.source_file_sha256_scope
           OR artifact.source_file_nonstorage_reason IS DISTINCT FROM
                  assertion.source_file_nonstorage_reason
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_artifact_lineage_ck',
            MESSAGE = 'existing descriptor assertions must match artifact route-index hash, source-file hash scope, and non-storage reason';
    END IF;
END
$round3m_existing_descriptor_artifact_hash_scope$;

CREATE FUNCTION audit.validate_round3m_current_review_receipt_leaf()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_current_review_receipt_leaf$
BEGIN
    IF NEW.supersedes_review_receipt_id IS NOT NULL
       AND EXISTS (
            SELECT 1
            FROM corpus.round3m_descriptor_assertion AS assertion
            WHERE assertion.current_review_receipt_id =
                  NEW.supersedes_review_receipt_id
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_current_review_receipt_leaf_ck',
            MESSAGE = 'a superseded review receipt cannot remain the current assertion receipt';
    END IF;

    RETURN NEW;
END
$validate_round3m_current_review_receipt_leaf$;

-- A successor and the assertion pointer may be written in either order inside
-- one transaction, but the predecessor cannot remain current at commit.
CREATE CONSTRAINT TRIGGER round3m_current_review_receipt_leaf_ci
AFTER INSERT ON audit.round3m_descriptor_review_receipt
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_current_review_receipt_leaf();

DO $round3m_existing_review_pointer_leaf$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion AS assertion
        JOIN audit.round3m_descriptor_review_receipt AS receipt
          ON receipt.review_receipt_id = assertion.current_review_receipt_id
        WHERE EXISTS (
            SELECT 1
            FROM audit.round3m_descriptor_review_receipt AS successor
            WHERE successor.supersedes_review_receipt_id =
                  receipt.review_receipt_id
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_current_review_pointer_leaf_ck',
            MESSAGE = 'existing assertion current-review pointers must reference leaf receipts';
    END IF;
END
$round3m_existing_review_pointer_leaf$;

CREATE OR REPLACE FUNCTION audit.validate_round3m_review_receipt_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_review_receipt_lineage$
DECLARE
    predecessor audit.round3m_descriptor_review_receipt%ROWTYPE;
BEGIN
    -- A successor insertion and an assertion-pointer update must observe one
    -- another.  Without this incompatible row lock, two transactions can
    -- each validate against the old leaf and commit a stale current pointer.
    PERFORM assertion.descriptor_assertion_id
    FROM corpus.round3m_descriptor_assertion AS assertion
    WHERE assertion.descriptor_assertion_id =
          NEW.descriptor_assertion_id
    FOR NO KEY UPDATE;

    IF NEW.supersedes_review_receipt_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO STRICT predecessor
    FROM audit.round3m_descriptor_review_receipt
    WHERE review_receipt_id = NEW.supersedes_review_receipt_id;

    IF predecessor.descriptor_assertion_id IS DISTINCT FROM
          NEW.descriptor_assertion_id
       OR predecessor.receipt_version <> NEW.receipt_version - 1
       OR predecessor.reviewed_at > NEW.reviewed_at
       OR predecessor.decision IS DISTINCT FROM NEW.previous_decision THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_review_receipt_previous_decision_ck',
            MESSAGE = 'review successor must name the immediately prior receipt and its exact decision';
    END IF;

    RETURN NEW;
END
$validate_round3m_review_receipt_lineage$;

DO $round3m_existing_review_previous_decision$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt AS successor
        JOIN audit.round3m_descriptor_review_receipt AS predecessor
          ON predecessor.review_receipt_id =
             successor.supersedes_review_receipt_id
        WHERE successor.descriptor_assertion_id IS DISTINCT FROM
                  predecessor.descriptor_assertion_id
           OR successor.receipt_version <> predecessor.receipt_version + 1
           OR successor.reviewed_at < predecessor.reviewed_at
           OR successor.previous_decision IS DISTINCT FROM
                  predecessor.decision
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_review_receipt_previous_decision_ck',
            MESSAGE = 'existing successor receipts must name their predecessor decision exactly';
    END IF;
END
$round3m_existing_review_previous_decision$;

CREATE FUNCTION corpus.protect_round3m_reviewed_assertion_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_reviewed_assertion_semantics$
DECLARE
    semantic_changed BOOLEAN;
    has_human_history BOOLEAN;
BEGIN
    semantic_changed := (to_jsonb(OLD) - ARRAY[
        'rights_decision_id', 'review_state',
        'review_actor_type', 'current_review_receipt_id'
    ]) IS DISTINCT FROM (to_jsonb(NEW) - ARRAY[
        'rights_decision_id', 'review_state',
        'review_actor_type', 'current_review_receipt_id'
    ]);

    SELECT EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt AS historical
        WHERE historical.descriptor_assertion_id =
              OLD.descriptor_assertion_id
          AND historical.review_actor_type IN (
              'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
          AND historical.receipt_origin_code IN (
              'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
          )
          AND historical.human_event_evidence_sha256 IS NOT NULL
    ) INTO has_human_history;

    IF semantic_changed AND has_human_history
       AND NEW.current_review_receipt_id IS NOT DISTINCT FROM
           OLD.current_review_receipt_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewed_semantics_receipt_binding_ck',
            MESSAGE = 'each reviewed semantic change requires a new direct human/expert successor receipt';
    END IF;

    IF semantic_changed AND has_human_history
       AND NOT EXISTS (
            SELECT 1
            FROM audit.round3m_descriptor_review_receipt AS successor
            JOIN audit.round3m_descriptor_review_receipt AS predecessor
              ON predecessor.review_receipt_id =
                 successor.supersedes_review_receipt_id
            WHERE successor.review_receipt_id =
                  NEW.current_review_receipt_id
              AND predecessor.review_receipt_id =
                  OLD.current_review_receipt_id
              AND successor.descriptor_assertion_id =
                  OLD.descriptor_assertion_id
              AND successor.review_actor_type IN (
                  'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
              )
              AND successor.receipt_origin_code IN (
                  'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
              )
              AND successor.human_event_evidence_sha256 IS NOT NULL
              AND successor.decision IN (
                  'CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR'
              )
              AND successor.previous_decision = predecessor.decision
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_reviewed_semantics_receipt_binding_ck',
            MESSAGE = 'reviewed assertion semantics require the exact new direct evidenced human/expert successor';
    END IF;

    RETURN NEW;
END
$protect_round3m_reviewed_assertion_semantics$;

CREATE TRIGGER round3m_reviewed_assertion_semantics_bu
BEFORE UPDATE ON corpus.round3m_descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    corpus.protect_round3m_reviewed_assertion_semantics();

-- Expert adjudication is a qualification claim, not merely an actor label.
-- Pseudonymous human review remains supported, while EXPERT_REVIEWER requires
-- a governed reviewer identity with current eligible adjudication and coffee-
-- sensory or competition-judging qualifications.
CREATE FUNCTION audit.validate_round3m_expert_review_qualification()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_expert_review_qualification$
BEGIN
    IF NEW.review_actor_type = 'EXPERT_REVIEWER'
       AND (
            NEW.reviewer_id IS NULL
            OR NOT EXISTS (
                SELECT 1
                FROM audit.professional_reviewer_qualification AS qualification
                WHERE qualification.reviewer_id = NEW.reviewer_id
                  AND qualification.qualification_scope_code = 'ADJUDICATION'
                  AND qualification.eligible
            )
            OR NOT EXISTS (
                SELECT 1
                FROM audit.professional_reviewer_qualification AS qualification
                WHERE qualification.reviewer_id = NEW.reviewer_id
                  AND qualification.qualification_scope_code IN (
                      'PROFESSIONAL_COFFEE_SENSORY',
                      'COMPETITION_JUDGING'
                  )
                  AND qualification.eligible
            )
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_expert_review_qualification_ck',
            MESSAGE = 'expert adjudication requires a governed eligible adjudicator with coffee-sensory or competition-judging qualification';
    END IF;

    RETURN NEW;
END
$validate_round3m_expert_review_qualification$;

CREATE TRIGGER round3m_expert_review_qualification_bi
BEFORE INSERT ON audit.round3m_descriptor_review_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_expert_review_qualification();

-- Ambiguous and unresolved are distinct evidenced human challenge outcomes.
-- Both map to the non-promoting PROVENANCE_UNRESOLVED assertion state.
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

-- Output labels are a separate actual-human decision.  A mapping receipt and
-- all of its targets must be created in the same transaction as the immutable
-- human review receipt, and its digest binds the complete ordered label set.
CREATE TABLE audit.round3m_descriptor_label_mapping_receipt (
    label_mapping_receipt_id TEXT NOT NULL,
    descriptor_assertion_id BIGINT NOT NULL,
    review_receipt_id BIGINT NOT NULL,
    label_set_sha256 TEXT NOT NULL,
    mapping_evidence_sha256 TEXT NOT NULL,
    mapping_evidence_locator TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_descriptor_label_mapping_receipt_pk PRIMARY KEY (
        label_mapping_receipt_id
    ),
    CONSTRAINT round3m_label_mapping_assertion_receipt_uq UNIQUE (
        descriptor_assertion_id, review_receipt_id
    ),
    CONSTRAINT round3m_label_mapping_full_scope_uq UNIQUE (
        label_mapping_receipt_id, descriptor_assertion_id,
        review_receipt_id
    ),
    CONSTRAINT round3m_label_mapping_assertion_fk FOREIGN KEY (
        descriptor_assertion_id
    ) REFERENCES corpus.round3m_descriptor_assertion (
        descriptor_assertion_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_label_mapping_review_fk FOREIGN KEY (
        review_receipt_id
    ) REFERENCES audit.round3m_descriptor_review_receipt (
        review_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_label_mapping_text_ck CHECK (
        label_mapping_receipt_id = lower(btrim(label_mapping_receipt_id))
        AND label_mapping_receipt_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND label_set_sha256 ~ '^[0-9a-f]{64}$'
        AND mapping_evidence_sha256 ~ '^[0-9a-f]{64}$'
        AND mapping_evidence_locator = btrim(mapping_evidence_locator)
        AND mapping_evidence_locator <> ''
    )
);

CREATE FUNCTION audit.validate_round3m_label_mapping_receipt()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_label_mapping_receipt$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt AS receipt
        JOIN corpus.round3m_descriptor_assertion AS assertion
          ON assertion.descriptor_assertion_id =
             receipt.descriptor_assertion_id
        WHERE receipt.review_receipt_id = NEW.review_receipt_id
          AND receipt.descriptor_assertion_id =
              NEW.descriptor_assertion_id
          AND assertion.current_review_receipt_id =
              receipt.review_receipt_id
          AND assertion.review_state IN (
              'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
          )
          AND receipt.review_actor_type IN (
              'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
          AND receipt.receipt_origin_code IN (
              'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
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
            MESSAGE = 'label mapping must be bound in the same transaction to the assertion current actual-human receipt and evidence';
    END IF;

    RETURN NEW;
END
$validate_round3m_label_mapping_receipt$;

CREATE TRIGGER round3m_label_mapping_receipt_bi
BEFORE INSERT ON audit.round3m_descriptor_label_mapping_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_label_mapping_receipt();

DO $round3m_existing_label_targets_absent$
BEGIN
    IF EXISTS (
        SELECT 1 FROM corpus.round3m_descriptor_label_target
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_label_mapping_historical_binding_ck',
            MESSAGE = 'pre-hardening label targets lack exact actual-human mapping-set evidence';
    END IF;
END
$round3m_existing_label_targets_absent$;

ALTER TABLE corpus.round3m_descriptor_label_target
    DROP CONSTRAINT round3m_descriptor_label_target_pk,
    DROP CONSTRAINT round3m_descriptor_label_target_uq;

ALTER TABLE corpus.round3m_descriptor_label_target
    ADD CONSTRAINT round3m_descriptor_label_target_pk PRIMARY KEY (
        descriptor_assertion_id, review_receipt_id, target_ordinal
    );

ALTER TABLE corpus.round3m_descriptor_label_target
    ADD CONSTRAINT round3m_descriptor_label_target_receipt_uq UNIQUE (
        descriptor_assertion_id, review_receipt_id, output_label_key
    );

ALTER TABLE corpus.round3m_descriptor_label_target
    ADD COLUMN label_mapping_receipt_id TEXT;

ALTER TABLE corpus.round3m_descriptor_label_target
    ADD COLUMN concept_id BIGINT,
    ADD COLUMN association_range_id BIGINT;

ALTER TABLE corpus.round3m_descriptor_label_target
    ADD CONSTRAINT round3m_label_target_concept_fk FOREIGN KEY (
        concept_id
    ) REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_label_target_range_fk FOREIGN KEY (
        association_range_id
    ) REFERENCES corpus.association_range (association_range_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_label_target_governed_shape_ck CHECK (
        normalization_decision IN (
            'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET'
        )
        AND concept_id IS NOT NULL
        AND association_range_id IS NULL
        OR normalization_decision = 'RANGE_LEVEL_TARGET'
        AND concept_id IS NULL
        AND association_range_id IS NOT NULL
        OR normalization_decision = 'SOURCE_LOCAL_TARGET'
        AND concept_id IS NULL
        AND association_range_id IS NULL
    );

ALTER TABLE corpus.round3m_descriptor_label_target
    ADD CONSTRAINT round3m_label_target_mapping_receipt_fk FOREIGN KEY (
        label_mapping_receipt_id, descriptor_assertion_id,
        review_receipt_id
    ) REFERENCES audit.round3m_descriptor_label_mapping_receipt (
        label_mapping_receipt_id, descriptor_assertion_id,
        review_receipt_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE corpus.round3m_descriptor_label_target
    ALTER COLUMN label_mapping_receipt_id SET NOT NULL;

CREATE OR REPLACE FUNCTION corpus.validate_round3m_label_target()
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
          AND receipt.receipt_origin_code IN (
              'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
          )
          AND receipt.human_event_evidence_sha256 IS NOT NULL
          AND receipt.decision IN (
              'CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR'
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_label_human_provenance_ck',
            MESSAGE = 'output labels require the assertion current evidenced actual-human review receipt';
    END IF;

    IF NEW.concept_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
            FROM kb.concept AS concept
            WHERE concept.concept_id = NEW.concept_id
              AND concept.concept_key = NEW.output_label_key
              AND concept.lifecycle_status_code = 'active'
              AND concept.replacement_concept_id IS NULL
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_label_target_canonical_key_ck',
            MESSAGE = 'canonical label target must name the exact active unreplaced concept key';
    END IF;

    IF NEW.association_range_id IS NOT NULL
       AND NOT EXISTS (
            SELECT 1
            FROM corpus.association_range AS association_range
            WHERE association_range.association_range_id =
                  NEW.association_range_id
              AND association_range.range_key = NEW.output_label_key
              AND association_range.lifecycle_status NOT IN (
                  'REJECTED', 'DEPRECATED'
              )
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_label_target_canonical_key_ck',
            MESSAGE = 'range label target must name the exact governed non-rejected range key';
    END IF;

    RETURN NEW;
END
$validate_round3m_label_target$;

CREATE FUNCTION audit.round3m_descriptor_label_set_sha256(
    mapping_receipt_id_value TEXT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_descriptor_label_set_sha256$
SELECT audit.round3i_utf8_sha256(
    coalesce(
        string_agg(
            target.target_ordinal::TEXT || chr(31) ||
            target.output_label_key || chr(31) ||
            target.normalization_decision || chr(31) ||
            CASE
                WHEN target.concept_id IS NOT NULL
                    THEN 'concept:' || target.concept_id::TEXT
                WHEN target.association_range_id IS NOT NULL
                    THEN 'range:' || target.association_range_id::TEXT
                ELSE 'source-local'
            END,
            chr(30)
            ORDER BY target.target_ordinal, target.output_label_key,
                     target.normalization_decision,
                     target.concept_id, target.association_range_id
        ),
        ''
    )
)
FROM corpus.round3m_descriptor_label_target AS target
WHERE target.label_mapping_receipt_id = mapping_receipt_id_value
$round3m_descriptor_label_set_sha256$;

CREATE FUNCTION audit.validate_round3m_label_mapping_set()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_label_mapping_set$
DECLARE
    mapping_receipt_id_value TEXT;
    expected_sha256 TEXT;
    target_count BIGINT;
    decision_count BIGINT;
    decision_value TEXT;
    minimum_ordinal INTEGER;
    maximum_ordinal INTEGER;
    distinct_ordinal_count BIGINT;
BEGIN
    mapping_receipt_id_value := CASE TG_TABLE_NAME
        WHEN 'round3m_descriptor_label_mapping_receipt'
            THEN NEW.label_mapping_receipt_id
        ELSE NEW.label_mapping_receipt_id
    END;

    SELECT mapping.label_set_sha256
    INTO STRICT expected_sha256
    FROM audit.round3m_descriptor_label_mapping_receipt AS mapping
    WHERE mapping.label_mapping_receipt_id = mapping_receipt_id_value;

    IF expected_sha256 IS DISTINCT FROM
       audit.round3m_descriptor_label_set_sha256(
           mapping_receipt_id_value
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_label_mapping_set_digest_ck',
            MESSAGE = 'label targets must exactly match the immutable human mapping-set digest';
    END IF;

    SELECT count(*), count(DISTINCT normalization_decision),
           min(normalization_decision), min(target_ordinal),
           max(target_ordinal), count(DISTINCT target_ordinal)
    INTO target_count, decision_count, decision_value,
         minimum_ordinal, maximum_ordinal, distinct_ordinal_count
    FROM corpus.round3m_descriptor_label_target
    WHERE label_mapping_receipt_id = mapping_receipt_id_value;

    IF target_count = 0
       OR decision_count <> 1
       OR minimum_ordinal <> 1
       OR maximum_ordinal <> target_count
       OR distinct_ordinal_count <> target_count
       OR decision_value = 'EXACT_CANONICAL_TARGET'
          AND target_count <> 1
       OR decision_value = 'MULTI_CANONICAL_TARGET'
          AND target_count < 2
       OR decision_value = 'SOURCE_LOCAL_TARGET'
          AND target_count <> 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_label_mapping_cardinality_ck',
            MESSAGE = 'label mapping requires one decision kind, contiguous ordinals, and exact decision-specific target cardinality';
    END IF;

    RETURN NEW;
END
$validate_round3m_label_mapping_set$;

CREATE CONSTRAINT TRIGGER round3m_label_mapping_set_receipt_ci
AFTER INSERT ON audit.round3m_descriptor_label_mapping_receipt
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_label_mapping_set();

CREATE CONSTRAINT TRIGGER round3m_label_mapping_set_target_ci
AFTER INSERT ON corpus.round3m_descriptor_label_target
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_label_mapping_set();

CREATE FUNCTION audit.reject_round3m_label_mapping_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $reject_round3m_label_mapping_mutation$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '23514',
        CONSTRAINT = 'round3m_label_target_immutable_ck',
        MESSAGE = 'label mapping receipts and targets are immutable; append a new human review successor mapping';
END
$reject_round3m_label_mapping_mutation$;

CREATE TRIGGER round3m_label_mapping_receipt_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_label_mapping_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.reject_round3m_label_mapping_mutation();

CREATE TRIGGER round3m_label_target_immutable_bud
BEFORE UPDATE OR DELETE ON corpus.round3m_descriptor_label_target
FOR EACH ROW EXECUTE FUNCTION
    audit.reject_round3m_label_mapping_mutation();

CREATE VIEW corpus.v_round3m_verified_descriptor_label_target AS
SELECT target.*
FROM corpus.round3m_descriptor_label_target AS target
JOIN audit.round3m_descriptor_label_mapping_receipt AS mapping
  ON mapping.label_mapping_receipt_id =
     target.label_mapping_receipt_id
 AND mapping.descriptor_assertion_id = target.descriptor_assertion_id
 AND mapping.review_receipt_id = target.review_receipt_id
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = mapping.review_receipt_id
 AND receipt.descriptor_assertion_id = mapping.descriptor_assertion_id
 AND receipt.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
 AND receipt.receipt_origin_code IN (
     'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
 )
 AND receipt.human_event_evidence_sha256 =
     mapping.mapping_evidence_sha256
WHERE mapping.label_set_sha256 =
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

CREATE OR REPLACE VIEW corpus.v_round3m_assertion_level_deinflated AS
SELECT assertion.*
FROM corpus.round3m_descriptor_assertion AS assertion
WHERE assertion.descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
  AND assertion.publication_layer <> 'SECONDARY_SENSORY_TABLE'
  AND assertion.deduplication_disposition IN (
      'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
      'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
  );

COMMENT ON VIEW corpus.v_round3m_assertion_level_deinflated IS
    'Atomic primary observations after exact within-field/within-record and publication/mirror duplicate removal. Secondary sensory publication layers remain preserved in the base ledger but never count here.';

CREATE OR REPLACE VIEW corpus.v_round3m_research_staged_descriptor_universe AS
SELECT
    assertion.*,
    route.independent_source_family_id,
    rights.internal_research_analysis,
    rights.model_research,
    rights.deployment_or_commercial_model
FROM corpus.v_round3m_assertion_level_deinflated AS assertion
JOIN evidence.round3m_source_route AS route
  ON route.source_route_id = assertion.source_route_id
JOIN evidence.round3m_independent_source_family AS family
  ON family.independent_source_family_id =
     route.independent_source_family_id
JOIN evidence.v_round3m_current_descriptor_rights AS rights
  ON rights.rights_decision_id = assertion.rights_decision_id
 AND rights.unambiguous_current_decision
WHERE rights.internal_research_analysis = 'AFFIRMATIVE'
  AND family.admitted_for_descriptor_research
  AND NOT assertion.synthetic_generated;

COMMENT ON VIEW corpus.v_round3m_research_staged_descriptor_universe IS
    'De-inflated descriptor assertions from explicitly admitted independent families with unanimous current natural-scope rights and affirmative internal-research permission.';

CREATE OR REPLACE VIEW corpus.v_round3m_human_reviewed_descriptor_universe AS
SELECT audited.*
FROM corpus.v_round3m_source_audited_descriptor_universe AS audited
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = audited.current_review_receipt_id
 AND receipt.descriptor_assertion_id = audited.descriptor_assertion_id
 AND receipt.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
 AND receipt.receipt_origin_code IN (
     'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
 )
 AND receipt.human_event_evidence_sha256 IS NOT NULL
 AND receipt.decision IN ('CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR')
 AND receipt.reviewed_at <= receipt.created_at
 AND receipt.created_at <= transaction_timestamp()
WHERE audited.review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
  AND NOT EXISTS (
      SELECT 1
      FROM audit.round3m_descriptor_review_receipt AS successor
      WHERE successor.supersedes_review_receipt_id =
            receipt.review_receipt_id
  );

CREATE OR REPLACE VIEW corpus.v_round3m_deployment_eligible_descriptor_universe AS
SELECT model.*
FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
WHERE model.internal_research_analysis = 'AFFIRMATIVE'
  AND model.model_research = 'AFFIRMATIVE'
  AND model.deployment_or_commercial_model = 'AFFIRMATIVE';

-- Round 3M holdout declarations reuse the governed professional split model.
-- No split is frozen by this migration.  A future split can count only after
-- a transaction-timestamped freeze with immutable members and assignments.
DO $round3m_existing_frozen_split_absent$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM ml.professional_split_plan
        WHERE professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND lifecycle_status_code IN ('FROZEN', 'SUPERSEDED')
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_split_freeze_historical_evidence_ck',
            MESSAGE = 'pre-hardening frozen split plans lack a timestamped freeze receipt';
    END IF;
END
$round3m_existing_frozen_split_absent$;

ALTER TABLE ml.professional_split_plan
    ADD COLUMN frozen_at TIMESTAMPTZ,
    ADD COLUMN freeze_receipt_sha256 TEXT,
    ADD CONSTRAINT round3m_professional_split_freeze_shape_ck CHECK (
        professional_split_plan_key <>
            'round3m.descriptor-gate-holdout'
        OR lifecycle_status_code IN ('FROZEN', 'SUPERSEDED')
           AND frozen_at IS NOT NULL
           AND freeze_receipt_sha256 ~ '^[0-9a-f]{64}$'
        OR lifecycle_status_code = 'CANDIDATE'
           AND frozen_at IS NULL
           AND freeze_receipt_sha256 IS NULL
    );

CREATE FUNCTION ml.round3m_professional_split_assignment_sha256(
    split_plan_id_value BIGINT,
    training_candidate_id_value BIGINT,
    partition_code_value TEXT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_split_assignment_sha256$
SELECT audit.round3i_utf8_sha256(
    plan.professional_split_plan_key || chr(31) ||
    plan.plan_version::TEXT || chr(31) ||
    plan.deterministic_rule_version || chr(31) ||
    candidate.professional_training_candidate_key || chr(31) ||
    service.preparation_service_key || chr(31) ||
    candidate.task_code || chr(31) ||
    rights.professional_rights_decision_key || chr(31) ||
    candidate.candidate_status_code || chr(31) ||
    candidate.provenance_complete::TEXT || chr(31) ||
    candidate.rights_complete::TEXT || chr(31) ||
    candidate.integrity_complete::TEXT || chr(31) ||
    candidate.included::TEXT || chr(31) ||
    coalesce(candidate.exclusion_reason_code, '<NULL>') || chr(31) ||
    to_char(
        candidate.created_at AT TIME ZONE 'UTC',
        'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
    ) || chr(31) ||
    partition_code_value
)
FROM ml.professional_split_plan AS plan
CROSS JOIN ml.professional_training_candidate AS candidate
JOIN competition.preparation_service AS service
  ON service.preparation_service_id = candidate.preparation_service_id
JOIN evidence.professional_rights_decision AS rights
  ON rights.professional_rights_decision_id =
     candidate.professional_rights_decision_id
WHERE plan.professional_split_plan_id = split_plan_id_value
  AND candidate.professional_training_candidate_id =
      training_candidate_id_value
$round3m_professional_split_assignment_sha256$;

-- Bind/unbind operations take an incompatible candidate-row lock before any
-- digest validation or plan lock.  A concurrent candidate UPDATE therefore
-- completes first (and the new digest is observed) or waits until the split
-- binding exists (and is rejected by the candidate protection trigger).
CREATE FUNCTION ml.lock_round3m_professional_split_candidate()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $lock_round3m_professional_split_candidate$
DECLARE
    old_candidate_id BIGINT;
    new_candidate_id BIGINT;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        old_candidate_id := OLD.professional_training_candidate_id;
    END IF;
    IF TG_OP <> 'DELETE' THEN
        new_candidate_id := NEW.professional_training_candidate_id;
    END IF;

    PERFORM candidate.professional_training_candidate_id
    FROM ml.professional_training_candidate AS candidate
    WHERE candidate.professional_training_candidate_id IN (
        old_candidate_id, new_candidate_id
    )
    ORDER BY candidate.professional_training_candidate_id
    FOR UPDATE;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$lock_round3m_professional_split_candidate$;

CREATE TRIGGER round3m_split_assignment_candidate_lock_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.professional_split_assignment
FOR EACH ROW EXECUTE FUNCTION
    ml.lock_round3m_professional_split_candidate();

CREATE TRIGGER round3m_split_group_member_candidate_lock_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.professional_split_group_member
FOR EACH ROW EXECUTE FUNCTION
    ml.lock_round3m_professional_split_candidate();

CREATE FUNCTION ml.validate_round3m_professional_split_assignment_hash()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_professional_split_assignment_hash$
DECLARE
    split_plan_key TEXT;
BEGIN
    SELECT plan.professional_split_plan_key INTO STRICT split_plan_key
    FROM ml.professional_split_plan AS plan
    WHERE plan.professional_split_plan_id =
          NEW.professional_split_plan_id;

    -- Round 3K permits any governed 64-hex deterministic receipt.  The
    -- content-derived digest below is a forward Round 3M contract for the
    -- descriptor-gate holdout plan, not a retroactive reinterpretation of
    -- every historical split fixture.
    IF split_plan_key <> 'round3m.descriptor-gate-holdout' THEN
        RETURN NEW;
    END IF;

    IF NEW.deterministic_assignment_sha256 IS DISTINCT FROM
       ml.round3m_professional_split_assignment_sha256(
           NEW.professional_split_plan_id,
           NEW.professional_training_candidate_id,
           NEW.partition_code
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_split_assignment_digest_ck',
            MESSAGE = 'split assignment digest must bind the plan rule, candidate identity, and partition';
    END IF;
    RETURN NEW;
END
$validate_round3m_professional_split_assignment_hash$;

CREATE TRIGGER round3m_split_assignment_hash_biu
BEFORE INSERT OR UPDATE ON ml.professional_split_assignment
FOR EACH ROW EXECUTE FUNCTION
    ml.validate_round3m_professional_split_assignment_hash();

CREATE FUNCTION ml.protect_round3m_professional_split_children()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_professional_split_children$
DECLARE
    old_plan_id BIGINT;
    new_plan_id BIGINT;
BEGIN
    IF TG_TABLE_NAME = 'professional_split_group' THEN
        IF TG_OP = 'UPDATE'
           AND OLD.professional_split_plan_id IS DISTINCT FROM
               NEW.professional_split_plan_id
           AND EXISTS (
               SELECT 1
               FROM ml.professional_split_plan AS identity_plan
               WHERE identity_plan.professional_split_plan_id IN (
                   OLD.professional_split_plan_id,
                   NEW.professional_split_plan_id
               )
                 AND identity_plan.professional_split_plan_key =
                     'round3m.descriptor-gate-holdout'
           ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_split_group_plan_immutable_ck',
                MESSAGE = 'a split group cannot be reassigned into or out of a Round 3M descriptor holdout plan';
        END IF;
    END IF;

    IF TG_TABLE_NAME = 'professional_split_group' THEN
        IF TG_OP <> 'INSERT' THEN
            old_plan_id := OLD.professional_split_plan_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_plan_id := NEW.professional_split_plan_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'professional_split_group_member' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT professional_split_plan_id INTO old_plan_id
            FROM ml.professional_split_group
            WHERE professional_split_group_id =
                  OLD.professional_split_group_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT professional_split_plan_id INTO new_plan_id
            FROM ml.professional_split_group
            WHERE professional_split_group_id =
                  NEW.professional_split_group_id;
        END IF;
    ELSE
        IF TG_OP <> 'INSERT' THEN
            old_plan_id := OLD.professional_split_plan_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_plan_id := NEW.professional_split_plan_id;
        END IF;
    END IF;

    -- A foreign-key KEY SHARE lock is compatible with the lifecycle UPDATE's
    -- NO KEY UPDATE lock.  Take an explicit incompatible lock so a child
    -- insert/update/delete cannot write-skew against a concurrent freeze.
    PERFORM plan.professional_split_plan_id
    FROM ml.professional_split_plan AS plan
    WHERE plan.professional_split_plan_id IN (
              old_plan_id, new_plan_id
          )
      AND plan.professional_split_plan_key =
          'round3m.descriptor-gate-holdout'
    ORDER BY plan.professional_split_plan_id
    FOR NO KEY UPDATE;

    IF EXISTS (
        SELECT 1
        FROM ml.professional_split_plan AS plan
        WHERE plan.professional_split_plan_id IN (
            old_plan_id, new_plan_id
        )
          AND plan.professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND plan.lifecycle_status_code <> 'CANDIDATE'
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_frozen_split_children_immutable_ck',
            MESSAGE = 'split groups, members, and assignments are mutable only while the plan is a candidate';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_professional_split_children$;

CREATE TRIGGER round3m_split_group_mutability_bud
BEFORE INSERT OR UPDATE OR DELETE ON ml.professional_split_group
FOR EACH ROW EXECUTE FUNCTION
    ml.protect_round3m_professional_split_children();

CREATE TRIGGER round3m_split_group_member_mutability_bud
BEFORE INSERT OR UPDATE OR DELETE ON ml.professional_split_group_member
FOR EACH ROW EXECUTE FUNCTION
    ml.protect_round3m_professional_split_children();

CREATE TRIGGER round3m_split_assignment_mutability_bud
BEFORE INSERT OR UPDATE OR DELETE ON ml.professional_split_assignment
FOR EACH ROW EXECUTE FUNCTION
    ml.protect_round3m_professional_split_children();

CREATE FUNCTION ml.protect_round3m_frozen_training_candidate()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_frozen_training_candidate$
BEGIN
    -- Lock every target plan referencing the candidate in deterministic order.
    -- This serializes candidate mutation against the plan's freeze transition.
    PERFORM plan.professional_split_plan_id
    FROM ml.professional_split_plan AS plan
    WHERE plan.professional_split_plan_key =
          'round3m.descriptor-gate-holdout'
      AND plan.professional_split_plan_id IN (
          SELECT assignment.professional_split_plan_id
          FROM ml.professional_split_assignment AS assignment
          WHERE assignment.professional_training_candidate_id =
                OLD.professional_training_candidate_id
          UNION
          SELECT split_group.professional_split_plan_id
          FROM ml.professional_split_group_member AS member
          JOIN ml.professional_split_group AS split_group
            ON split_group.professional_split_group_id =
               member.professional_split_group_id
          WHERE member.professional_training_candidate_id =
                OLD.professional_training_candidate_id
      )
    ORDER BY plan.professional_split_plan_id
    FOR NO KEY UPDATE;

    IF EXISTS (
        SELECT 1
        FROM ml.professional_split_plan AS plan
        WHERE plan.professional_split_plan_key =
              'round3m.descriptor-gate-holdout'
          AND plan.professional_split_plan_id IN (
              SELECT assignment.professional_split_plan_id
              FROM ml.professional_split_assignment AS assignment
              WHERE assignment.professional_training_candidate_id =
                    OLD.professional_training_candidate_id
              UNION
              SELECT split_group.professional_split_plan_id
              FROM ml.professional_split_group_member AS member
              JOIN ml.professional_split_group AS split_group
                ON split_group.professional_split_group_id =
                   member.professional_split_group_id
              WHERE member.professional_training_candidate_id =
                    OLD.professional_training_candidate_id
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_bound_split_candidate_immutable_ck',
            MESSAGE = 'a training candidate is immutable once bound to a Round 3M descriptor holdout; remove candidate-plan bindings before correction';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_frozen_training_candidate$;

CREATE TRIGGER round3m_frozen_training_candidate_bud
BEFORE UPDATE OR DELETE ON ml.professional_training_candidate
FOR EACH ROW EXECUTE FUNCTION
    ml.protect_round3m_frozen_training_candidate();

CREATE FUNCTION ml.protect_round3m_professional_split_plan()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_professional_split_plan$
BEGIN
    -- This forward contract governs only the Round 3M descriptor-gate
    -- holdout.  It must not retroactively reinterpret earlier split plans.
    IF TG_OP = 'INSERT'
       AND NEW.professional_split_plan_key <>
           'round3m.descriptor-gate-holdout' THEN
        RETURN NEW;
    ELSIF TG_OP = 'DELETE'
       AND OLD.professional_split_plan_key <>
           'round3m.descriptor-gate-holdout' THEN
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE'
       AND OLD.professional_split_plan_key <>
           'round3m.descriptor-gate-holdout'
       AND NEW.professional_split_plan_key <>
           'round3m.descriptor-gate-holdout' THEN
        RETURN NEW;
    END IF;

    IF TG_OP = 'UPDATE'
       AND OLD.professional_split_plan_key IS DISTINCT FROM
           NEW.professional_split_plan_key THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_split_plan_identity_immutable_ck',
            MESSAGE = 'a plan cannot be renamed into or out of the Round 3M descriptor-gate holdout contract';
    END IF;

    IF TG_OP = 'INSERT'
       AND NEW.lifecycle_status_code IN ('FROZEN', 'SUPERSEDED') THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_split_freeze_transition_ck',
            MESSAGE = 'a split plan must be assembled as CANDIDATE before it is frozen';
    END IF;

    IF TG_OP = 'DELETE' THEN
        IF OLD.lifecycle_status_code <> 'CANDIDATE' THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_frozen_split_plan_immutable_ck',
                MESSAGE = 'frozen and superseded split plans are immutable';
        END IF;
        RETURN OLD;
    END IF;

    IF TG_OP = 'UPDATE'
       AND OLD.lifecycle_status_code <> 'CANDIDATE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_frozen_split_plan_immutable_ck',
            MESSAGE = 'frozen and superseded split plans are immutable';
    END IF;

    IF TG_OP = 'UPDATE'
       AND NEW.lifecycle_status_code NOT IN ('CANDIDATE', 'FROZEN') THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_split_freeze_transition_ck',
            MESSAGE = 'a Round 3M candidate split can transition only to FROZEN';
    END IF;

    IF TG_OP = 'UPDATE'
       AND NEW.lifecycle_status_code = 'FROZEN' THEN
        IF OLD.professional_split_plan_key IS DISTINCT FROM
              NEW.professional_split_plan_key
           OR OLD.plan_version IS DISTINCT FROM NEW.plan_version
           OR OLD.deterministic_rule_version IS DISTINCT FROM
              NEW.deterministic_rule_version
           OR OLD.random_row_split IS DISTINCT FROM NEW.random_row_split
           OR NEW.frozen_at IS DISTINCT FROM transaction_timestamp()
           OR NEW.freeze_receipt_sha256 IS NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_split_freeze_transition_ck',
                MESSAGE = 'split freeze time must be the current transaction and must carry a receipt hash';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM ml.professional_split_group_member AS member
            JOIN ml.professional_split_group AS split_group
              ON split_group.professional_split_group_id =
                 member.professional_split_group_id
            WHERE split_group.professional_split_plan_id =
                  NEW.professional_split_plan_id
              AND NOT EXISTS (
                  SELECT 1
                  FROM ml.professional_split_assignment AS assignment
                  WHERE assignment.professional_split_plan_id =
                        NEW.professional_split_plan_id
                    AND assignment.professional_training_candidate_id =
                        member.professional_training_candidate_id
              )
        ) OR EXISTS (
            SELECT 1
            FROM ml.professional_split_group AS split_group
            JOIN ml.professional_split_group_member AS member
              ON member.professional_split_group_id =
                 split_group.professional_split_group_id
            JOIN ml.professional_split_assignment AS assignment
              ON assignment.professional_split_plan_id =
                 NEW.professional_split_plan_id
             AND assignment.professional_training_candidate_id =
                 member.professional_training_candidate_id
            WHERE split_group.professional_split_plan_id =
                  NEW.professional_split_plan_id
            GROUP BY split_group.professional_split_group_id
            HAVING count(DISTINCT assignment.partition_code) <> 1
        ) OR EXISTS (
            SELECT 1
            FROM ml.professional_split_assignment AS assignment
            WHERE assignment.professional_split_plan_id =
                  NEW.professional_split_plan_id
              AND assignment.deterministic_assignment_sha256 IS DISTINCT FROM
                  ml.round3m_professional_split_assignment_sha256(
                      assignment.professional_split_plan_id,
                      assignment.professional_training_candidate_id,
                      assignment.partition_code
                  )
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_split_freeze_completeness_ck',
                MESSAGE = 'a frozen split requires complete deterministic assignments and one partition per governed group';
        END IF;
    END IF;

    RETURN NEW;
END
$protect_round3m_professional_split_plan$;

CREATE TRIGGER round3m_split_plan_freeze_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.professional_split_plan
FOR EACH ROW EXECUTE FUNCTION
    ml.protect_round3m_professional_split_plan();

ALTER TABLE ml.professional_split_group
    ADD CONSTRAINT round3m_split_group_plan_identity_uq UNIQUE (
        professional_split_group_id, professional_split_plan_id
    );

DO $round3m_existing_holdouts_absent$
BEGIN
    IF EXISTS (SELECT 1 FROM audit.round3m_descriptor_holdout) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_holdout_historical_split_binding_ck',
            MESSAGE = 'pre-hardening holdouts lack a frozen governed split binding';
    END IF;
END
$round3m_existing_holdouts_absent$;

ALTER TABLE audit.round3m_descriptor_holdout
    DROP CONSTRAINT round3m_descriptor_holdout_value_uq,
    ADD COLUMN professional_split_plan_id BIGINT,
    ADD COLUMN professional_split_group_id BIGINT;

ALTER TABLE audit.round3m_descriptor_holdout
    ALTER COLUMN professional_split_plan_id SET NOT NULL,
    ALTER COLUMN professional_split_group_id SET NOT NULL,
    ADD CONSTRAINT round3m_descriptor_holdout_plan_fk FOREIGN KEY (
        professional_split_plan_id
    ) REFERENCES ml.professional_split_plan (
        professional_split_plan_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_descriptor_holdout_group_plan_fk FOREIGN KEY (
        professional_split_group_id, professional_split_plan_id
    ) REFERENCES ml.professional_split_group (
        professional_split_group_id, professional_split_plan_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT round3m_descriptor_holdout_plan_value_uq UNIQUE (
        professional_split_plan_id, holdout_kind, holdout_value
    ),
    ADD CONSTRAINT round3m_descriptor_holdout_active_ck CHECK (active);

CREATE FUNCTION audit.validate_round3m_descriptor_holdout()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_holdout$
DECLARE
    split_plan ml.professional_split_plan%ROWTYPE;
    split_group ml.professional_split_group%ROWTYPE;
BEGIN
    SELECT * INTO STRICT split_plan
    FROM ml.professional_split_plan
    WHERE professional_split_plan_id = NEW.professional_split_plan_id;

    SELECT * INTO STRICT split_group
    FROM ml.professional_split_group
    WHERE professional_split_group_id =
          NEW.professional_split_group_id;

    IF split_plan.professional_split_plan_key <>
          'round3m.descriptor-gate-holdout'
       OR split_plan.lifecycle_status_code <> 'FROZEN'
       OR split_plan.frozen_at IS NULL
       OR split_plan.freeze_receipt_sha256 IS NULL
       OR split_group.professional_split_plan_id IS DISTINCT FROM
          split_plan.professional_split_plan_id
       OR split_group.split_group_key IS DISTINCT FROM NEW.holdout_value
       OR NEW.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
          AND split_group.split_group_kind_code <>
              'COMPETITION_FAMILY'
       OR NEW.holdout_kind = 'EDITION_YEAR'
          AND split_group.split_group_kind_code <> 'COMPETITION_YEAR'
       OR NEW.declared_at IS DISTINCT FROM split_plan.frozen_at
       OR NEW.declaration_receipt_sha256 IS DISTINCT FROM
          split_plan.freeze_receipt_sha256 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_holdout_frozen_split_binding_ck',
            MESSAGE = 'holdout must exactly bind a predeclared group in the timestamped frozen Round 3M split plan';
    END IF;

    IF NEW.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
       AND NOT EXISTS (
            SELECT 1
            FROM evidence.round3m_independent_source_family AS family
            WHERE family.independent_source_family_id = NEW.holdout_value
              AND family.admitted_for_descriptor_research
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_holdout_admitted_family_ck',
            MESSAGE = 'family holdout must name an admitted governed independent source family';
    END IF;

    RETURN NEW;
END
$validate_round3m_descriptor_holdout$;

CREATE TRIGGER round3m_descriptor_holdout_bi
BEFORE INSERT ON audit.round3m_descriptor_holdout
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_descriptor_holdout();

CREATE TRIGGER round3m_descriptor_holdout_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_holdout
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE OR REPLACE VIEW audit.v_round3m_descriptor_gate_metrics AS
WITH reviewed AS (
    SELECT *
    FROM corpus.v_round3m_human_reviewed_descriptor_universe
    WHERE descriptor_class = 'STRICT_FLAVOR'
      AND evidence_tier IN ('P1', 'P2')
), reviewed_descriptor_record AS (
    SELECT DISTINCT effective_record_key
    FROM corpus.v_round3m_human_reviewed_descriptor_universe
    WHERE evidence_tier IN ('P1', 'P2')
      AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
), reviewed_by_family AS (
    SELECT independent_source_family_id, count(*)::BIGINT AS assertion_count
    FROM reviewed
    GROUP BY independent_source_family_id
), rights_rate AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (
            WHERE internal_research_analysis = 'AFFIRMATIVE'
        )::BIGINT AS internal_affirmative_count,
        count(*) FILTER (
            WHERE model_research = 'AFFIRMATIVE'
        )::BIGINT AS model_affirmative_count,
        count(*) FILTER (
            WHERE internal_research_analysis = 'AFFIRMATIVE'
              AND model_research = 'AFFIRMATIVE'
              AND deployment_or_commercial_model = 'AFFIRMATIVE'
        )::BIGINT AS deployment_affirmative_count
    FROM reviewed
), source_provenance AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (
            WHERE artifact.source_file_sha256 = reviewed.source_file_sha256
              AND artifact.route_index_sha256 =
                  reviewed.route_index_sha256
              AND artifact.source_file_sha256_scope =
                  reviewed.source_file_sha256_scope
              AND artifact.source_file_nonstorage_reason =
                  reviewed.source_file_nonstorage_reason
              AND artifact.source_retrieved_at =
                  reviewed.source_retrieved_at
              AND artifact.source_route_id = reviewed.source_route_id
              AND artifact.schema_signature_id =
                  reviewed.schema_signature_id
              AND signature.validation_status = 'VALIDATED'
              AND reviewed.source_selector_or_locator <> ''
              AND reviewed.source_page_or_record_locator <> ''
              AND reviewed.origin_evidence_locator <> ''
              AND reviewed.source_field_label_sha256 =
                  audit.round3i_utf8_sha256(reviewed.source_field_label)
              AND reviewed.atomic_source_text_sha256 ~ '^[0-9a-f]{64}$'
        )::BIGINT AS complete_count
    FROM reviewed
    JOIN evidence.round3m_source_artifact AS artifact
      ON artifact.source_artifact_id = reviewed.source_artifact_id
    JOIN evidence.round3m_source_schema_signature AS signature
      ON signature.schema_signature_id = reviewed.schema_signature_id
), label_provenance AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (
            WHERE reviewed.normalized_candidate_form IS NOT NULL
              AND EXISTS (
                  SELECT 1
                  FROM corpus.v_round3m_verified_descriptor_label_target AS target
                  WHERE target.descriptor_assertion_id =
                        reviewed.descriptor_assertion_id
                    AND target.review_receipt_id =
                        reviewed.current_review_receipt_id
              )
        )::BIGINT AS complete_count
    FROM reviewed
), label_record_count AS (
    SELECT
        target.output_label_key,
        count(DISTINCT reviewed.effective_record_key)::BIGINT AS record_count
    FROM reviewed
    JOIN corpus.v_round3m_verified_descriptor_label_target AS target
      ON target.descriptor_assertion_id = reviewed.descriptor_assertion_id
     AND target.review_receipt_id = reviewed.current_review_receipt_id
    GROUP BY target.output_label_key
), target_by_record AS (
    SELECT
        reviewed.effective_record_key,
        count(DISTINCT target.output_label_key)::BIGINT AS target_count
    FROM reviewed
    JOIN corpus.v_round3m_verified_descriptor_label_target AS target
      ON target.descriptor_assertion_id = reviewed.descriptor_assertion_id
     AND target.review_receipt_id = reviewed.current_review_receipt_id
    GROUP BY reviewed.effective_record_key
), human_challenge AS (
    SELECT count(DISTINCT assertion.descriptor_assertion_id)::BIGINT AS value
    FROM corpus.v_round3m_research_staged_descriptor_universe AS assertion
    JOIN evidence.round3m_source_schema_signature AS signature
      ON signature.schema_signature_id = assertion.schema_signature_id
    JOIN audit.round3m_descriptor_review_receipt AS receipt
      ON receipt.review_receipt_id = assertion.current_review_receipt_id
     AND receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
    WHERE assertion.descriptor_class = 'STRICT_FLAVOR'
      AND assertion.evidence_tier IN ('P1', 'P2')
      AND assertion.model_research = 'AFFIRMATIVE'
      AND assertion.review_state = 'PROVENANCE_UNRESOLVED'
      AND NOT assertion.translation_generated
      AND NOT assertion.synthetic_generated
      AND signature.validation_status = 'VALIDATED'
      AND receipt.review_actor_type IN (
            'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
      AND receipt.receipt_origin_code IN (
            'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
          )
      AND receipt.human_event_evidence_sha256 IS NOT NULL
      AND receipt.decision IN ('MARK_AMBIGUOUS', 'MARK_UNRESOLVED')
      AND NOT EXISTS (
          SELECT 1
          FROM audit.round3m_descriptor_review_receipt AS successor
          WHERE successor.supersedes_review_receipt_id =
                receipt.review_receipt_id
      )
), model_pair AS (
    SELECT event.*
    FROM corpus.round3m_coassertion_event AS event
    JOIN corpus.v_round3m_model_eligible_descriptor_universe AS left_assertion
      ON left_assertion.descriptor_assertion_id =
         event.left_descriptor_assertion_id
     AND event.effective_record_key = left_assertion.effective_record_key
     AND event.source_observation_key =
         left_assertion.source_observation_key
    JOIN corpus.v_round3m_model_eligible_descriptor_universe AS right_assertion
      ON right_assertion.descriptor_assertion_id =
         event.right_descriptor_assertion_id
     AND event.effective_record_key = right_assertion.effective_record_key
     AND event.source_observation_key =
         right_assertion.source_observation_key
     AND right_assertion.source_artifact_id =
         left_assertion.source_artifact_id
     AND right_assertion.source_route_id = left_assertion.source_route_id
     AND right_assertion.schema_signature_id =
         left_assertion.schema_signature_id
     AND right_assertion.publication_layer =
         left_assertion.publication_layer
     AND left_assertion.publication_layer IN (
         'PRIMARY_JURY_DESCRIPTION', 'JUDGE_LEVEL_OBSERVATION'
     )
), selected_split_plan AS (
    SELECT plan.*
    FROM ml.professional_split_plan AS plan
    WHERE plan.professional_split_plan_key =
          'round3m.descriptor-gate-holdout'
      AND plan.lifecycle_status_code = 'FROZEN'
      AND plan.frozen_at IS NOT NULL
      AND plan.freeze_receipt_sha256 IS NOT NULL
    ORDER BY plan.plan_version DESC,
             plan.professional_split_plan_id DESC
    LIMIT 1
), qualified_holdout AS (
    SELECT holdout.*
    FROM selected_split_plan AS plan
    JOIN audit.round3m_descriptor_holdout AS holdout
      ON holdout.professional_split_plan_id =
         plan.professional_split_plan_id
     AND holdout.active
     AND holdout.declared_at = plan.frozen_at
     AND holdout.declaration_receipt_sha256 =
         plan.freeze_receipt_sha256
    JOIN ml.professional_split_group AS split_group
      ON split_group.professional_split_group_id =
         holdout.professional_split_group_id
     AND split_group.professional_split_plan_id =
         plan.professional_split_plan_id
     AND split_group.split_group_key = holdout.holdout_value
    WHERE EXISTS (
        SELECT 1
        FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
        JOIN ml.professional_training_candidate AS candidate
          ON candidate.preparation_service_id = model.preparation_service_id
         AND candidate.task_code = 'DESCRIPTOR_NORMALIZATION'
         AND candidate.included
        JOIN ml.professional_split_group_member AS member
          ON member.professional_split_group_id =
             split_group.professional_split_group_id
         AND member.professional_training_candidate_id =
             candidate.professional_training_candidate_id
        JOIN ml.professional_split_assignment AS assignment
          ON assignment.professional_split_plan_id =
             plan.professional_split_plan_id
         AND assignment.professional_training_candidate_id =
             candidate.professional_training_candidate_id
         AND assignment.partition_code = 'HELD_OUT'
        WHERE holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
              AND model.independent_source_family_id =
                  holdout.holdout_value
           OR holdout.holdout_kind = 'EDITION_YEAR'
              AND model.edition_year::TEXT = holdout.holdout_value
    )
      AND NOT EXISTS (
        SELECT 1
        FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
        WHERE (
                holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
                AND model.independent_source_family_id =
                    holdout.holdout_value
              OR holdout.holdout_kind = 'EDITION_YEAR'
                AND model.edition_year::TEXT = holdout.holdout_value
              )
          AND NOT EXISTS (
              SELECT 1
              FROM ml.professional_training_candidate AS candidate
              JOIN ml.professional_split_group_member AS member
                ON member.professional_split_group_id =
                   split_group.professional_split_group_id
               AND member.professional_training_candidate_id =
                   candidate.professional_training_candidate_id
              JOIN ml.professional_split_assignment AS assignment
                ON assignment.professional_split_plan_id =
                   plan.professional_split_plan_id
               AND assignment.professional_training_candidate_id =
                   candidate.professional_training_candidate_id
               AND assignment.partition_code = 'HELD_OUT'
              WHERE candidate.preparation_service_id =
                    model.preparation_service_id
                AND candidate.task_code = 'DESCRIPTOR_NORMALIZATION'
                AND candidate.included
          )
      )
      AND NOT EXISTS (
        SELECT 1
        FROM ml.professional_split_group_member AS member
        JOIN ml.professional_training_candidate AS candidate
          ON candidate.professional_training_candidate_id =
             member.professional_training_candidate_id
        WHERE member.professional_split_group_id =
              split_group.professional_split_group_id
          AND NOT EXISTS (
              SELECT 1
              FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
              WHERE model.preparation_service_id =
                    candidate.preparation_service_id
                AND (
                    holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
                    AND model.independent_source_family_id =
                        holdout.holdout_value
                    OR holdout.holdout_kind = 'EDITION_YEAR'
                    AND model.edition_year::TEXT = holdout.holdout_value
                )
          )
      )
      AND NOT EXISTS (
        SELECT 1
        FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
        JOIN audit.round3m_descriptor_review_receipt AS receipt
          ON receipt.review_receipt_id = model.current_review_receipt_id
        WHERE (
                holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
                AND model.independent_source_family_id =
                    holdout.holdout_value
              OR holdout.holdout_kind = 'EDITION_YEAR'
                AND model.edition_year::TEXT = holdout.holdout_value
              )
          AND receipt.created_at < plan.frozen_at
      )
), heldout AS (
    SELECT
        count(*) FILTER (
            WHERE holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
        )::BIGINT AS family_count,
        count(*) FILTER (
            WHERE holdout_kind = 'EDITION_YEAR'
        )::BIGINT AS year_count
    FROM qualified_holdout
), review_blocker AS (
    SELECT count(*)::BIGINT AS value
    FROM corpus.v_round3m_source_audited_descriptor_universe AS audited
    WHERE audited.descriptor_class = 'STRICT_FLAVOR'
      AND audited.evidence_tier IN ('P1', 'P2')
      AND audited.review_state NOT IN (
          'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
      )
), base AS (
    SELECT count(*)::BIGINT AS reviewed_count
    FROM reviewed
)
SELECT
    (SELECT segmented_atomic_observation_count
     FROM audit.v_round3m_descriptor_count_surfaces) AS
        segmented_atomic_observation_count,
    base.reviewed_count AS reviewed_p1_p2_strict_assertion_count,
    (SELECT count(*) FROM reviewed_descriptor_record)::BIGINT AS
        reviewed_descriptor_bearing_record_count,
    (SELECT count(DISTINCT normalized_candidate_form)
     FROM reviewed
     WHERE normalized_candidate_form IS NOT NULL
       AND NOT translation_generated
       AND NOT synthetic_generated)::BIGINT AS
        reviewed_unique_normalized_form_count,
    (SELECT count(*) FROM reviewed_by_family)::BIGINT AS
        reviewed_independent_source_family_count,
    CASE
        WHEN base.reviewed_count = 0 THEN NULL::NUMERIC
        ELSE coalesce((
            SELECT max(assertion_count)::NUMERIC
            FROM reviewed_by_family
        ), 0) / base.reviewed_count::NUMERIC
    END AS reviewed_largest_family_share,
    (SELECT min(record_count) FROM label_record_count)::NUMERIC AS
        minimum_records_per_output_label,
    (SELECT count(*) FROM target_by_record
     WHERE target_count >= 2)::BIGINT AS reviewed_multi_target_record_count,
    human_challenge.value AS reviewed_ambiguous_or_unresolved_challenge_count,
    (SELECT count(DISTINCT (
         left_descriptor_assertion_id, right_descriptor_assertion_id
     )) FROM model_pair)::BIGINT AS
        supported_within_record_pair_event_count,
    (SELECT count(DISTINCT (
         effective_record_key, source_observation_key
     ))
     FROM model_pair)::BIGINT AS supported_coassertion_set_count,
    heldout.family_count AS held_out_independent_family_count,
    heldout.year_count AS held_out_edition_year_count,
    CASE WHEN source_provenance.denominator = 0 THEN NULL::NUMERIC
         ELSE source_provenance.complete_count::NUMERIC /
              source_provenance.denominator::NUMERIC END AS
        source_provenance_completeness,
    CASE WHEN label_provenance.denominator = 0 THEN NULL::NUMERIC
         ELSE label_provenance.complete_count::NUMERIC /
              label_provenance.denominator::NUMERIC END AS
        label_provenance_completeness,
    CASE
        WHEN source_provenance.denominator = 0
          OR label_provenance.denominator = 0 THEN NULL::NUMERIC
        ELSE least(
            source_provenance.complete_count::NUMERIC /
                source_provenance.denominator::NUMERIC,
            label_provenance.complete_count::NUMERIC /
                label_provenance.denominator::NUMERIC
        )
    END AS source_and_label_provenance_completeness,
    CASE WHEN rights_rate.denominator = 0 THEN NULL::NUMERIC
         ELSE rights_rate.internal_affirmative_count::NUMERIC /
              rights_rate.denominator::NUMERIC END AS
        internal_research_rights_rate,
    CASE WHEN rights_rate.denominator = 0 THEN NULL::NUMERIC
         ELSE rights_rate.model_affirmative_count::NUMERIC /
              rights_rate.denominator::NUMERIC END AS
        model_research_rights_rate,
    CASE WHEN rights_rate.denominator = 0 THEN NULL::NUMERIC
         ELSE rights_rate.deployment_affirmative_count::NUMERIC /
              rights_rate.denominator::NUMERIC END AS
        deployment_rights_rate,
    (rights_rate.denominator -
     rights_rate.internal_affirmative_count)::BIGINT AS
        internal_research_rights_blocker_count,
    (rights_rate.denominator -
     rights_rate.model_affirmative_count)::BIGINT AS
        model_research_rights_blocker_count,
    (rights_rate.denominator -
     rights_rate.deployment_affirmative_count)::BIGINT AS
        deployment_rights_blocker_count,
    review_blocker.value AS human_review_blocker_count,
    base.reviewed_count > 0
      AND NOT EXISTS (
          SELECT 1
          FROM corpus.round3m_coassertion_event AS event
          JOIN corpus.round3m_descriptor_assertion AS left_assertion
            ON left_assertion.descriptor_assertion_id =
               event.left_descriptor_assertion_id
          JOIN corpus.round3m_descriptor_assertion AS right_assertion
            ON right_assertion.descriptor_assertion_id =
               event.right_descriptor_assertion_id
          WHERE left_assertion.effective_record_key IS DISTINCT FROM
                    right_assertion.effective_record_key
             OR left_assertion.source_observation_key IS DISTINCT FROM
                    right_assertion.source_observation_key
             OR event.effective_record_key IS DISTINCT FROM
                    left_assertion.effective_record_key
             OR event.source_observation_key IS DISTINCT FROM
                    left_assertion.source_observation_key
             OR left_assertion.source_artifact_id IS DISTINCT FROM
                    right_assertion.source_artifact_id
             OR left_assertion.source_route_id IS DISTINCT FROM
                    right_assertion.source_route_id
             OR left_assertion.schema_signature_id IS DISTINCT FROM
                    right_assertion.schema_signature_id
             OR left_assertion.publication_layer IS DISTINCT FROM
                    right_assertion.publication_layer
             OR left_assertion.publication_layer NOT IN (
                    'PRIMARY_JURY_DESCRIPTION',
                    'JUDGE_LEVEL_OBSERVATION'
                )
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
                )
      )
      AND NOT EXISTS (
          SELECT 1
          FROM corpus.round3m_coassertion_event AS left_event
          JOIN corpus.round3m_coassertion_event AS right_event
            ON left_event.coassertion_event_id <
               right_event.coassertion_event_id
           AND (
                (
                    left_event.effective_record_key =
                        right_event.effective_record_key
                    AND left_event.source_observation_key =
                        right_event.source_observation_key
                    AND left_event.coassertion_set_key IS DISTINCT FROM
                        right_event.coassertion_set_key
                )
                OR (
                    left_event.coassertion_set_key =
                        right_event.coassertion_set_key
                    AND (
                        left_event.effective_record_key IS DISTINCT FROM
                            right_event.effective_record_key
                        OR left_event.source_observation_key IS DISTINCT FROM
                            right_event.source_observation_key
                    )
                )
           )
      ) AS record_boundaries_preserved
FROM base
CROSS JOIN rights_rate
CROSS JOIN source_provenance
CROSS JOIN label_provenance
CROSS JOIN human_challenge
CROSS JOIN heldout
CROSS JOIN review_blocker;

ALTER FUNCTION audit.run_round3m_gate_validation_queries()
    RENAME TO run_round3m_gate_validation_queries_v056;

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
WITH hardening_checks AS (
    SELECT 'round3m.current_review_pointer_is_leaf'::TEXT AS check_key,
           count(*)::BIGINT AS violation_count
    FROM corpus.round3m_descriptor_assertion AS assertion
    JOIN audit.round3m_descriptor_review_receipt AS receipt
      ON receipt.review_receipt_id = assertion.current_review_receipt_id
    WHERE EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_review_receipt AS successor
        WHERE successor.supersedes_review_receipt_id =
              receipt.review_receipt_id
    )
    UNION ALL
    SELECT 'round3m.secondary_publication_layer_never_counts',
           count(*)::BIGINT
    FROM corpus.v_round3m_assertion_level_deinflated
    WHERE publication_layer = 'SECONDARY_SENSORY_TABLE'
    UNION ALL
    SELECT 'round3m.secondary_publication_layer_has_noncounting_disposition',
           count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion
    WHERE publication_layer = 'SECONDARY_SENSORY_TABLE'
      AND deduplication_disposition IN (
          'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
          'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
      )
    UNION ALL
    SELECT 'round3m.publication_layer_semantics_are_exact',
           count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion
    WHERE NOT (
        publication_layer = 'PRIMARY_JURY_DESCRIPTION'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'P2'
        AND evidence_origin_type IN (
            'EXPLICIT_TOP_JURY_FIELD',
            'ORGANIZER_PUBLISHED_EXPLICIT_JURY',
            'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION'
        )
        OR publication_layer = 'JUDGE_LEVEL_OBSERVATION'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'P1'
        AND evidence_origin_type IN (
            'EXPLICIT_IDENTIFIED_JUDGE', 'EXPLICIT_IDENTIFIED_PANEL'
        )
        OR publication_layer = 'PRODUCER_OR_FARM_PROFILE'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'P3'
        AND evidence_origin_type = 'PRODUCER_OR_FARM_DECLARED'
        OR publication_layer = 'GENERIC_ORGANIZER_SENSORY_FIELD'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier = 'UNRESOLVED'
        AND evidence_origin_type IN (
            'GENERIC_ORGANIZER_FIELD_UNKNOWN_AUTHOR',
            'FREQUENCY_CODED_UNKNOWN_ACTOR',
            'FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED',
            'GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED'
        )
        OR publication_layer = 'SECONDARY_SENSORY_TABLE'
        AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
        AND evidence_tier <> 'P0'
        OR publication_layer = 'RESULT_METADATA'
        AND descriptor_class = 'NON_DESCRIPTOR'
        OR publication_layer = 'PROTOCOL_OR_BLANK_FORM'
        AND descriptor_class = 'NON_DESCRIPTOR'
        AND evidence_tier = 'P0'
        AND evidence_origin_type = 'PROTOCOL_RULE_OR_BLANK_FORM'
    )
    UNION ALL
    SELECT 'round3m.coassertion_endpoint_pairs_are_unique',
           count(*)::BIGINT
    FROM (
        SELECT left_descriptor_assertion_id,
               right_descriptor_assertion_id
        FROM corpus.round3m_coassertion_event
        GROUP BY left_descriptor_assertion_id,
                 right_descriptor_assertion_id
        HAVING count(*) > 1
    ) AS duplicate_endpoint
    UNION ALL
    SELECT 'round3m.coassertion_observation_has_one_set_key',
           count(*)::BIGINT
    FROM (
        SELECT effective_record_key, source_observation_key
        FROM corpus.round3m_coassertion_event
        GROUP BY effective_record_key, source_observation_key
        HAVING count(DISTINCT coassertion_set_key) > 1
    ) AS duplicate_observation_set
    UNION ALL
    SELECT 'round3m.coassertion_set_key_has_one_observation',
           count(*)::BIGINT
    FROM (
        SELECT coassertion_set_key
        FROM corpus.round3m_coassertion_event
        GROUP BY coassertion_set_key
        HAVING count(DISTINCT (
            effective_record_key, source_observation_key
        )) > 1
    ) AS duplicate_set_observation
    UNION ALL
    SELECT 'round3m.review_successor_names_previous_decision',
           count(*)::BIGINT
    FROM audit.round3m_descriptor_review_receipt AS successor
    JOIN audit.round3m_descriptor_review_receipt AS predecessor
      ON predecessor.review_receipt_id =
         successor.supersedes_review_receipt_id
    WHERE successor.previous_decision IS DISTINCT FROM
          predecessor.decision
    UNION ALL
    SELECT 'round3m.source_family_origin_is_canonical',
           count(*)::BIGINT
    FROM (
        SELECT organizer_id, rights_lineage_id
        FROM evidence.round3m_independent_source_family
        GROUP BY organizer_id, rights_lineage_id
        HAVING count(*) > 1
    ) AS duplicate_family_origin
    UNION ALL
    SELECT 'round3m.source_route_matches_family_scope',
           count(*)::BIGINT
    FROM evidence.round3m_source_route AS route
    JOIN evidence.round3m_independent_source_family AS family
      ON family.independent_source_family_id =
         route.independent_source_family_id
    WHERE route.organizer_id IS DISTINCT FROM family.organizer_id
       OR route.rights_lineage_id IS DISTINCT FROM family.rights_lineage_id
    UNION ALL
    SELECT 'round3m.effective_record_identity_hash_is_bound',
           count(*)::BIGINT
    FROM competition.round3m_effective_record_bridge AS bridge
    WHERE bridge.record_identity_sha256 IS DISTINCT FROM
          competition.round3m_effective_record_identity_sha256(
              bridge.series_id, bridge.edition_id, bridge.edition_year,
              bridge.category_id, bridge.round_id, bridge.subject_kind,
              bridge.entry_or_lot_id, bridge.preparation_service_code,
              bridge.source_route_id, bridge.source_file_sha256,
              bridge.route_index_sha256,
              bridge.source_record_locator
          )
    UNION ALL
    SELECT 'round3m.effective_source_record_has_one_identity',
           count(*)::BIGINT
    FROM (
        SELECT
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END AS
                     snapshot_identity,
            source_record_locator, preparation_service_code
        FROM competition.round3m_effective_record_bridge
        GROUP BY
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END,
            source_record_locator, preparation_service_code
        HAVING count(*) > 1
    ) AS duplicate_effective_source
    UNION ALL
    SELECT 'round3m.countable_source_assertion_is_natural_unique',
           count(*)::BIGINT
    FROM (
        SELECT
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END AS
                     snapshot_identity,
            source_page_or_record_locator,
            source_field_label_sha256, source_selector_or_locator,
            atomic_source_text_sha256
        FROM corpus.round3m_descriptor_assertion
        WHERE descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
          AND publication_layer <> 'SECONDARY_SENSORY_TABLE'
          AND deduplication_disposition IN (
              'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
              'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
          )
        GROUP BY
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END,
            source_page_or_record_locator,
            source_field_label_sha256, source_selector_or_locator,
            atomic_source_text_sha256
        HAVING count(*) > 1
    ) AS duplicate_source_assertion
    UNION ALL
    SELECT 'round3m.coassertion_full_publication_boundary',
           count(*)::BIGINT
    FROM corpus.round3m_coassertion_event AS event
    JOIN corpus.round3m_descriptor_assertion AS left_assertion
      ON left_assertion.descriptor_assertion_id =
         event.left_descriptor_assertion_id
    JOIN corpus.round3m_descriptor_assertion AS right_assertion
      ON right_assertion.descriptor_assertion_id =
         event.right_descriptor_assertion_id
    WHERE event.effective_record_key IS DISTINCT FROM
              left_assertion.effective_record_key
       OR event.source_observation_key IS DISTINCT FROM
              left_assertion.source_observation_key
       OR left_assertion.effective_record_key IS DISTINCT FROM
              right_assertion.effective_record_key
       OR left_assertion.source_observation_key IS DISTINCT FROM
              right_assertion.source_observation_key
       OR left_assertion.source_artifact_id IS DISTINCT FROM
              right_assertion.source_artifact_id
       OR left_assertion.source_route_id IS DISTINCT FROM
              right_assertion.source_route_id
       OR left_assertion.schema_signature_id IS DISTINCT FROM
              right_assertion.schema_signature_id
       OR left_assertion.publication_layer IS DISTINCT FROM
              right_assertion.publication_layer
       OR left_assertion.publication_layer NOT IN (
              'PRIMARY_JURY_DESCRIPTION', 'JUDGE_LEVEL_OBSERVATION'
          )
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
          )
    UNION ALL
    SELECT 'round3m.label_mapping_sets_are_exact',
           count(*)::BIGINT
    FROM audit.round3m_descriptor_label_mapping_receipt AS mapping
    JOIN audit.round3m_descriptor_review_receipt AS receipt
      ON receipt.review_receipt_id = mapping.review_receipt_id
    WHERE mapping.descriptor_assertion_id IS DISTINCT FROM
              receipt.descriptor_assertion_id
       OR mapping.mapping_evidence_sha256 IS DISTINCT FROM
              receipt.human_event_evidence_sha256
       OR mapping.created_at IS DISTINCT FROM receipt.created_at
       OR mapping.label_set_sha256 IS DISTINCT FROM
              audit.round3m_descriptor_label_set_sha256(
                  mapping.label_mapping_receipt_id
              )
    UNION ALL
    SELECT 'round3m.mirror_lineage_has_one_family', count(*)::BIGINT
    FROM (
        SELECT mirror_lineage_id
        FROM evidence.round3m_source_route
        WHERE mirror_lineage_id <> 'unresolved'
        GROUP BY mirror_lineage_id
        HAVING count(DISTINCT independent_source_family_id) > 1
    ) AS cross_family_mirror
    UNION ALL
    SELECT 'round3m.mirror_lineage_parent_matches_routes', count(*)::BIGINT
    FROM evidence.round3m_source_route AS route
    LEFT JOIN evidence.round3m_mirror_lineage_family AS mapping
      ON mapping.mirror_lineage_id = route.mirror_lineage_id
     AND mapping.independent_source_family_id =
         route.independent_source_family_id
    WHERE mapping.mirror_lineage_id IS NULL
    UNION ALL
    SELECT 'round3m.resolved_mirror_lineages_have_canonical_credit',
           count(*)::BIGINT
    FROM (
        SELECT route.mirror_lineage_id
        FROM evidence.round3m_source_route AS route
        LEFT JOIN evidence.round3m_mirror_lineage_credit_route AS credit
          ON credit.mirror_lineage_id = route.mirror_lineage_id
        WHERE route.mirror_lineage_id <> 'unresolved'
        GROUP BY route.mirror_lineage_id
        HAVING count(*) > 1
           AND count(credit.mirror_lineage_id) = 0
    ) AS unresolved_credit
    UNION ALL
    SELECT 'round3m.noncanonical_mirror_assertions_are_noncounting',
           count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion AS assertion
    JOIN evidence.round3m_source_route AS route
      ON route.source_route_id = assertion.source_route_id
    LEFT JOIN evidence.round3m_mirror_lineage_credit_route AS credit
      ON credit.mirror_lineage_id = route.mirror_lineage_id
    WHERE route.mirror_lineage_id <> 'unresolved'
      AND assertion.descriptor_class IN (
          'STRICT_FLAVOR', 'BROAD_SENSORY'
      )
      AND 1 < (
          SELECT count(*)
          FROM evidence.round3m_source_route AS peer
          WHERE peer.mirror_lineage_id = route.mirror_lineage_id
      )
      AND (
          credit.canonical_source_route_id IS NULL
          OR credit.canonical_source_route_id IS DISTINCT FROM
                 assertion.source_route_id
             AND (
                 assertion.deduplication_disposition <>
                     'MIRROR_PUBLICATION'
                 OR assertion.mirror_group IS DISTINCT FROM
                     route.mirror_lineage_id
             )
      )
    UNION ALL
    SELECT 'round3m.research_staged_family_is_admitted', count(*)::BIGINT
    FROM corpus.v_round3m_research_staged_descriptor_universe AS staged
    JOIN evidence.round3m_independent_source_family AS family
      ON family.independent_source_family_id =
         staged.independent_source_family_id
    WHERE NOT family.admitted_for_descriptor_research
    UNION ALL
    SELECT 'round3m.source_artifact_identity_is_natural_unique',
           count(*)::BIGINT
    FROM (
        SELECT
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END AS
                     snapshot_identity,
            governed_locator
        FROM evidence.round3m_source_artifact
        GROUP BY
            CASE WHEN source_file_sha256 <> ''
                 THEN 'file:' || source_file_sha256
                 ELSE 'route-index:' || route_index_sha256 END,
            governed_locator
        HAVING count(*) > 1
    ) AS duplicate_artifact
    UNION ALL
    SELECT 'round3m.current_natural_rights_scope_is_unanimous',
           count(*)::BIGINT
    FROM evidence.v_round3m_current_descriptor_rights
    WHERE NOT unambiguous_current_decision
    UNION ALL
    SELECT 'round3m.descriptor_rights_chronology_is_nonfuture',
           count(*)::BIGINT
    FROM evidence.round3m_descriptor_rights_decision
    WHERE decided_at > created_at
       OR created_at > transaction_timestamp()
    UNION ALL
    SELECT 'round3m.descriptor_review_receipt_chronology_is_nonfuture',
           count(*)::BIGINT
    FROM audit.round3m_descriptor_review_receipt
    WHERE reviewed_at > created_at
       OR created_at > transaction_timestamp()
    UNION ALL
    SELECT 'round3m.deployment_rights_follow_permission_chain',
           count(*)::BIGINT
    FROM evidence.round3m_descriptor_rights_decision
    WHERE deployment_or_commercial_model = 'AFFIRMATIVE'
      AND (
          internal_research_analysis <> 'AFFIRMATIVE'
          OR model_research <> 'AFFIRMATIVE'
      )
    UNION ALL
    SELECT 'round3m.expert_reviewers_are_qualified', count(*)::BIGINT
    FROM audit.round3m_descriptor_review_receipt AS receipt
    WHERE receipt.review_actor_type = 'EXPERT_REVIEWER'
      AND (
          receipt.reviewer_id IS NULL
          OR NOT EXISTS (
              SELECT 1
              FROM audit.professional_reviewer_qualification AS qualification
              WHERE qualification.reviewer_id = receipt.reviewer_id
                AND qualification.qualification_scope_code = 'ADJUDICATION'
                AND qualification.eligible
          )
          OR NOT EXISTS (
              SELECT 1
              FROM audit.professional_reviewer_qualification AS qualification
              WHERE qualification.reviewer_id = receipt.reviewer_id
                AND qualification.qualification_scope_code IN (
                    'PROFESSIONAL_COFFEE_SENSORY',
                    'COMPETITION_JUDGING'
                )
                AND qualification.eligible
          )
      )
    UNION ALL
    SELECT 'round3m.label_targets_are_governed', count(*)::BIGINT
    FROM corpus.round3m_descriptor_label_target AS target
    LEFT JOIN kb.concept AS concept
      ON concept.concept_id = target.concept_id
    LEFT JOIN corpus.association_range AS association_range
      ON association_range.association_range_id =
         target.association_range_id
    WHERE target.normalization_decision IN (
              'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET'
          )
          AND (
              concept.concept_id IS NULL
              OR concept.concept_key IS DISTINCT FROM
                 target.output_label_key
              OR concept.lifecycle_status_code <> 'active'
              OR concept.replacement_concept_id IS NOT NULL
          )
       OR target.normalization_decision = 'RANGE_LEVEL_TARGET'
          AND (
              association_range.association_range_id IS NULL
              OR association_range.range_key IS DISTINCT FROM
                 target.output_label_key
              OR association_range.lifecycle_status IN (
                  'REJECTED', 'DEPRECATED'
              )
          )
       OR target.normalization_decision = 'SOURCE_LOCAL_TARGET'
          AND (
              target.concept_id IS NOT NULL
              OR target.association_range_id IS NOT NULL
          )
    UNION ALL
    SELECT 'round3m.label_mapping_cardinality_is_exact', count(*)::BIGINT
    FROM (
        SELECT mapping.label_mapping_receipt_id,
               count(target.descriptor_assertion_id)::BIGINT AS target_count,
               count(DISTINCT target.normalization_decision)::BIGINT AS
                   decision_count,
               min(target.normalization_decision) AS decision_value,
               min(target.target_ordinal) AS minimum_ordinal,
               max(target.target_ordinal) AS maximum_ordinal,
               count(DISTINCT target.target_ordinal)::BIGINT AS
                   distinct_ordinal_count
        FROM audit.round3m_descriptor_label_mapping_receipt AS mapping
        LEFT JOIN corpus.round3m_descriptor_label_target AS target
          ON target.label_mapping_receipt_id =
             mapping.label_mapping_receipt_id
        GROUP BY mapping.label_mapping_receipt_id
    ) AS cardinality
    WHERE target_count = 0
       OR decision_count <> 1
       OR minimum_ordinal <> 1
       OR maximum_ordinal <> target_count
       OR distinct_ordinal_count <> target_count
       OR decision_value = 'EXACT_CANONICAL_TARGET'
          AND target_count <> 1
       OR decision_value = 'MULTI_CANONICAL_TARGET'
          AND target_count < 2
       OR decision_value = 'SOURCE_LOCAL_TARGET'
          AND target_count <> 1
    UNION ALL
    SELECT 'round3m.coassertion_parent_identity_matches_events',
           count(*)::BIGINT
    FROM corpus.round3m_coassertion_event AS event
    LEFT JOIN corpus.round3m_coassertion_set_identity AS identity
      ON identity.coassertion_set_key = event.coassertion_set_key
     AND identity.effective_record_key = event.effective_record_key
     AND identity.source_observation_key = event.source_observation_key
    WHERE identity.coassertion_set_key IS NULL
    UNION ALL
    SELECT 'round3m.split_assignments_bind_deterministic_digest',
           count(*)::BIGINT
    FROM ml.professional_split_assignment AS assignment
    JOIN ml.professional_split_plan AS plan
      ON plan.professional_split_plan_id =
         assignment.professional_split_plan_id
     AND plan.professional_split_plan_key =
         'round3m.descriptor-gate-holdout'
    WHERE assignment.deterministic_assignment_sha256 IS DISTINCT FROM
          ml.round3m_professional_split_assignment_sha256(
              assignment.professional_split_plan_id,
              assignment.professional_training_candidate_id,
              assignment.partition_code
          )
    UNION ALL
    SELECT 'round3m.frozen_split_groups_have_one_complete_partition',
           count(*)::BIGINT
    FROM (
        SELECT split_group.professional_split_group_id
        FROM ml.professional_split_plan AS plan
        JOIN ml.professional_split_group AS split_group
          ON split_group.professional_split_plan_id =
             plan.professional_split_plan_id
        LEFT JOIN ml.professional_split_group_member AS member
          ON member.professional_split_group_id =
             split_group.professional_split_group_id
        LEFT JOIN ml.professional_split_assignment AS assignment
          ON assignment.professional_split_plan_id =
             plan.professional_split_plan_id
         AND assignment.professional_training_candidate_id =
             member.professional_training_candidate_id
        WHERE plan.professional_split_plan_key =
                  'round3m.descriptor-gate-holdout'
          AND plan.lifecycle_status_code = 'FROZEN'
        GROUP BY split_group.professional_split_group_id
        HAVING count(member.professional_training_candidate_id) > 0
           AND (
               count(assignment.professional_training_candidate_id) <>
                   count(member.professional_training_candidate_id)
               OR count(DISTINCT assignment.partition_code) <> 1
           )
    ) AS incomplete_group
    UNION ALL
    SELECT 'round3m.holdouts_bind_frozen_governed_split', count(*)::BIGINT
    FROM audit.round3m_descriptor_holdout AS holdout
    LEFT JOIN ml.professional_split_plan AS plan
      ON plan.professional_split_plan_id =
         holdout.professional_split_plan_id
    LEFT JOIN ml.professional_split_group AS split_group
      ON split_group.professional_split_group_id =
         holdout.professional_split_group_id
     AND split_group.professional_split_plan_id =
         holdout.professional_split_plan_id
    LEFT JOIN evidence.round3m_independent_source_family AS family
      ON holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
     AND family.independent_source_family_id = holdout.holdout_value
    WHERE plan.professional_split_plan_key IS DISTINCT FROM
              'round3m.descriptor-gate-holdout'
       OR plan.lifecycle_status_code IS DISTINCT FROM 'FROZEN'
       OR holdout.declared_at IS DISTINCT FROM plan.frozen_at
       OR holdout.declaration_receipt_sha256 IS DISTINCT FROM
          plan.freeze_receipt_sha256
       OR split_group.split_group_key IS DISTINCT FROM
          holdout.holdout_value
       OR holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
          AND (
              split_group.split_group_kind_code IS DISTINCT FROM
                  'COMPETITION_FAMILY'
              OR family.independent_source_family_id IS NULL
              OR NOT family.admitted_for_descriptor_research
          )
       OR holdout.holdout_kind = 'EDITION_YEAR'
          AND split_group.split_group_kind_code IS DISTINCT FROM
              'COMPETITION_YEAR'
)
SELECT prior.check_key, prior.violation_count, prior.passed
FROM audit.run_round3m_gate_validation_queries_v056() AS prior
UNION ALL
SELECT hardening.check_key,
       hardening.violation_count,
       hardening.violation_count = 0 AS passed
FROM hardening_checks AS hardening
ORDER BY check_key
$run_round3m_gate_validation_queries$;

COMMENT ON FUNCTION audit.run_round3m_gate_validation_queries() IS
    'Round 3M descriptor gate invariants, including current review-receipt leaf, secondary-publication non-counting, unique co-assertion endpoints, and bidirectional set/observation identity hardening.';

COMMIT;
