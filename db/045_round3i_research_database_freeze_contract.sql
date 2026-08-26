\set ON_ERROR_STOP on

-- Round 3I governed language corpus and non-self-referential release contract.
BEGIN;

CREATE FUNCTION audit.round3i_utf8_sha256(value TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $round3i_utf8_sha256$
SELECT encode(sha256(convert_to(value, 'UTF8')), 'hex')
$round3i_utf8_sha256$;

CREATE FUNCTION corpus.language_source_manifest_is_complete(manifest JSONB)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
SET search_path = pg_catalog
AS $language_source_manifest_is_complete$
BEGIN
    IF jsonb_typeof(manifest) <> 'array'
       OR jsonb_array_length(manifest) = 0 THEN
        RETURN FALSE;
    END IF;
    RETURN NOT EXISTS (
        SELECT 1
        FROM jsonb_array_elements(manifest) AS item(value)
        WHERE jsonb_typeof(value) <> 'object'
           OR coalesce(
               value ->> 'path',
               value ->> 'url',
               value ->> 'canonical_url',
               ''
           ) = ''
           OR coalesce(value ->> 'sha256', '') !~ '^[0-9a-f]{64}$'
    ) AND (
        SELECT count(*) = count(DISTINCT coalesce(
            value ->> 'path',
            value ->> 'url',
            value ->> 'canonical_url'
        ))
        FROM jsonb_array_elements(manifest) AS item(value)
    );
END;
$language_source_manifest_is_complete$;

CREATE TABLE corpus.language_source_family (
    language_source_family_key TEXT NOT NULL,
    family_name TEXT NOT NULL,
    canonical_origin_key TEXT NOT NULL,
    counts_as_independent BOOLEAN NOT NULL,
    mirror_of_language_source_family_key TEXT,
    counts_as_new_contemporary_family BOOLEAN NOT NULL,
    counts_as_zh_hans_family BOOLEAN NOT NULL,
    historical_baseline BOOLEAN NOT NULL,
    source_authored BOOLEAN NOT NULL,
    admitted BOOLEAN NOT NULL,
    independence_basis TEXT NOT NULL,
    introduced_round TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'ADMITTED',
    CONSTRAINT language_source_family_pk PRIMARY KEY (language_source_family_key),
    CONSTRAINT language_source_family_mirror_fk FOREIGN KEY (
        mirror_of_language_source_family_key
    ) REFERENCES corpus.language_source_family (language_source_family_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT language_source_family_key_ck CHECK (
        language_source_family_key = lower(btrim(language_source_family_key))
        AND language_source_family_key <> ''
        AND canonical_origin_key = lower(btrim(canonical_origin_key))
        AND canonical_origin_key <> ''
        AND family_name = btrim(family_name) AND family_name <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
        AND introduced_round = '3I'
        AND lifecycle_status IN (
            'CANDIDATE', 'ADMITTED', 'REJECTED', 'QUARANTINED', 'DEPRECATED'
        )
        AND admitted = (lifecycle_status = 'ADMITTED')
    ),
    CONSTRAINT language_source_family_independence_ck CHECK (
        (mirror_of_language_source_family_key IS NULL
         OR (mirror_of_language_source_family_key <> language_source_family_key
             AND NOT counts_as_independent
             AND NOT counts_as_new_contemporary_family
             AND NOT counts_as_zh_hans_family))
        AND (NOT counts_as_new_contemporary_family OR (
            counts_as_independent AND source_authored AND admitted
            AND NOT historical_baseline
            AND mirror_of_language_source_family_key IS NULL
        ))
        AND (NOT counts_as_zh_hans_family OR (
            counts_as_independent AND source_authored AND admitted
            AND mirror_of_language_source_family_key IS NULL
        ))
    )
);

CREATE UNIQUE INDEX language_source_family_independent_origin_uq
ON corpus.language_source_family (canonical_origin_key)
WHERE counts_as_independent;

CREATE FUNCTION corpus.enforce_language_source_family_origin()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_language_source_family_origin$
DECLARE target_origin TEXT; target_independent BOOLEAN; target_admitted BOOLEAN;
BEGIN
    IF NEW.mirror_of_language_source_family_key IS NOT NULL THEN
        SELECT canonical_origin_key, counts_as_independent, admitted
        INTO target_origin, target_independent, target_admitted
        FROM corpus.language_source_family
        WHERE language_source_family_key = NEW.mirror_of_language_source_family_key;
        IF target_origin IS NULL OR target_origin <> NEW.canonical_origin_key
           OR NOT target_independent OR NOT target_admitted THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'language_source_family_mirror_origin_ck',
                MESSAGE = 'mirrors must name the same admitted independent origin';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_language_source_family_origin$;

CREATE TRIGGER language_source_family_origin_biu
BEFORE INSERT OR UPDATE ON corpus.language_source_family
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_language_source_family_origin();

CREATE TABLE corpus.language_source (
    language_source_key TEXT NOT NULL,
    language_source_family_key TEXT NOT NULL,
    title TEXT NOT NULL,
    authors_or_owner TEXT NOT NULL,
    publication_year INTEGER NOT NULL,
    doi_or_stable_url TEXT NOT NULL,
    repository TEXT NOT NULL,
    exact_version TEXT NOT NULL,
    access_date DATE NOT NULL,
    license_expression TEXT NOT NULL,
    license_url TEXT NOT NULL,
    raw_text_internal_use TEXT NOT NULL,
    raw_text_public_redistribution TEXT NOT NULL,
    derived_expression_internal_use TEXT NOT NULL,
    derived_expression_public_release TEXT NOT NULL,
    derived_counts_internal_use TEXT NOT NULL,
    derived_counts_public_release TEXT NOT NULL,
    model_research_use TEXT NOT NULL,
    rights_basis TEXT NOT NULL,
    rights_review_complete BOOLEAN NOT NULL,
    privacy_decision TEXT NOT NULL,
    privacy_review_complete BOOLEAN NOT NULL,
    source_file_manifest JSONB NOT NULL,
    source_file_hash_complete BOOLEAN NOT NULL,
    language_codes TEXT[] NOT NULL,
    geography TEXT NOT NULL,
    data_type TEXT NOT NULL,
    evidence_role TEXT NOT NULL,
    limitations TEXT NOT NULL,
    annotation_complete BOOLEAN NOT NULL,
    admitted BOOLEAN NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'ADMITTED',
    qualifies_as_observed_tasting_language BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT language_source_pk PRIMARY KEY (language_source_key),
    CONSTRAINT language_source_family_uq UNIQUE (
        language_source_key, language_source_family_key
    ),
    CONSTRAINT language_source_family_fk FOREIGN KEY (
        language_source_family_key
    ) REFERENCES corpus.language_source_family (language_source_family_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT language_source_key_ck CHECK (
        language_source_key = lower(btrim(language_source_key))
        AND language_source_key <> ''
        AND publication_year BETWEEN 1900 AND 2100
        AND title = btrim(title) AND title <> ''
        AND authors_or_owner = btrim(authors_or_owner) AND authors_or_owner <> ''
        AND doi_or_stable_url ~ '^https?://'
        AND repository = btrim(repository) AND repository <> ''
        AND exact_version = btrim(exact_version) AND exact_version <> ''
        AND license_expression = btrim(license_expression)
        AND license_expression <> '' AND license_url ~ '^https?://'
        AND rights_basis = btrim(rights_basis) AND rights_basis <> ''
        AND privacy_decision = btrim(privacy_decision) AND privacy_decision <> ''
        AND geography = btrim(geography) AND geography <> ''
        AND data_type = btrim(data_type) AND data_type <> ''
        AND evidence_role = btrim(evidence_role) AND evidence_role <> ''
        AND limitations = btrim(limitations) AND limitations <> ''
        AND cardinality(language_codes) >= 1
        AND array_position(language_codes, NULL) IS NULL
        AND language_codes <@ ARRAY['en', 'zh-Hans', 'und']::TEXT[]
        AND lifecycle_status IN (
            'CANDIDATE', 'ADMITTED', 'REJECTED', 'QUARANTINED', 'DEPRECATED'
        )
        AND admitted = (lifecycle_status = 'ADMITTED')
    ),
    CONSTRAINT language_source_rights_state_ck CHECK (
        raw_text_internal_use IN ('ALLOW', 'DENY', 'QUARANTINE')
        AND raw_text_public_redistribution IN ('ALLOW', 'DENY', 'QUARANTINE')
        AND derived_expression_internal_use IN ('ALLOW', 'DENY')
        AND derived_expression_public_release IN ('ALLOW', 'DENY')
        AND derived_counts_internal_use IN ('ALLOW', 'DENY')
        AND derived_counts_public_release IN ('ALLOW', 'DENY')
        AND model_research_use IN ('ALLOW', 'DENY')
        AND (raw_text_public_redistribution <> 'ALLOW'
             OR raw_text_internal_use = 'ALLOW')
        AND (derived_expression_public_release <> 'ALLOW'
             OR derived_expression_internal_use = 'ALLOW')
        AND (derived_counts_public_release <> 'ALLOW'
             OR derived_counts_internal_use = 'ALLOW')
    ),
    CONSTRAINT language_source_file_manifest_ck CHECK (
        corpus.language_source_manifest_is_complete(source_file_manifest)
    ),
    CONSTRAINT language_source_admission_ck CHECK (
        NOT admitted OR (
            annotation_complete AND rights_review_complete
            AND privacy_review_complete AND source_file_hash_complete
            AND derived_expression_internal_use = 'ALLOW'
            AND derived_counts_internal_use = 'ALLOW'
            AND model_research_use = 'ALLOW'
        )
    )
);

CREATE FUNCTION corpus.enforce_language_source_admitted_family()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_language_source_admitted_family$
BEGIN
    IF NEW.admitted AND NOT EXISTS (
        SELECT 1 FROM corpus.language_source_family
        WHERE language_source_family_key = NEW.language_source_family_key
          AND admitted
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_source_admitted_family_ck',
            MESSAGE = 'an admitted source requires an admitted family';
    END IF;
    RETURN NEW;
END;
$enforce_language_source_admitted_family$;

CREATE TRIGGER language_source_admitted_family_biu
BEFORE INSERT OR UPDATE ON corpus.language_source
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_language_source_admitted_family();

CREATE TABLE corpus.language_document (
    language_document_key TEXT NOT NULL,
    language_source_key TEXT NOT NULL,
    language_source_family_key TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    source_date DATE NOT NULL,
    source_row_locator TEXT NOT NULL,
    language_code TEXT NOT NULL,
    document_type TEXT NOT NULL,
    source_content_sha256 TEXT NOT NULL,
    content JSONB NOT NULL,
    raw_text_public_export_allowed BOOLEAN NOT NULL,
    counts_as_new_contemporary_document BOOLEAN NOT NULL,
    counts_as_zh_hans_document BOOLEAN NOT NULL,
    source_authored BOOLEAN NOT NULL,
    machine_translated BOOLEAN NOT NULL DEFAULT FALSE,
    artificial_variant BOOLEAN NOT NULL DEFAULT FALSE,
    privacy_state TEXT NOT NULL,
    public_export_state TEXT NOT NULL,
    frozen_snapshot BOOLEAN NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'ADMITTED',
    sensory_language_verified BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT language_document_pk PRIMARY KEY (language_document_key),
    CONSTRAINT language_document_source_fk FOREIGN KEY (
        language_source_key, language_source_family_key
    ) REFERENCES corpus.language_source (
        language_source_key, language_source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT language_document_identity_uq UNIQUE (
        language_source_key, source_row_locator
    ),
    CONSTRAINT language_document_text_ck CHECK (
        language_document_key = lower(btrim(language_document_key))
        AND language_document_key <> ''
        AND source_revision = btrim(source_revision) AND source_revision <> ''
        AND source_row_locator = btrim(source_row_locator)
        AND source_row_locator <> ''
        AND language_code IN ('en', 'zh-Hans', 'und')
        AND document_type IN (
            'TASTING_NOTE', 'CONSUMER_EVALUATION',
            'TRAINED_PANEL_PROFILE', 'EXPERT_PANEL_PROFILE',
            'SOURCE_AUTHORED_ARTICLE', 'SOURCE_AUTHORED_BLOG'
        )
        AND source_content_sha256 ~ '^[0-9a-f]{64}$'
        AND jsonb_typeof(content) = 'object'
        AND privacy_state IN (
            'NO_PERSONAL_DATA', 'DEIDENTIFIED_SOURCE_ROW',
            'PUBLIC_AUTHORSHIP_ONLY', 'QUARANTINED'
        )
        AND public_export_state IN (
            'PUBLIC_RAW', 'PUBLIC_DERIVED_ONLY', 'HASH_ONLY', 'QUARANTINED'
        )
        AND lifecycle_status IN (
            'CANDIDATE', 'ADMITTED', 'REJECTED', 'QUARANTINED', 'DEPRECATED'
        )
    ),
    CONSTRAINT language_document_countability_ck CHECK (
        NOT (counts_as_new_contemporary_document OR counts_as_zh_hans_document)
        OR (
            lifecycle_status = 'ADMITTED' AND source_authored
            AND NOT machine_translated AND NOT artificial_variant
            AND sensory_language_verified AND frozen_snapshot
            AND privacy_state <> 'QUARANTINED'
            AND public_export_state IN ('PUBLIC_RAW', 'PUBLIC_DERIVED_ONLY')
        )
    ),
    CONSTRAINT language_document_contemporary_ck CHECK (
        NOT counts_as_new_contemporary_document
        OR source_date BETWEEN DATE '2018-01-01' AND DATE '2026-12-31'
    ),
    CONSTRAINT language_document_zh_hans_ck CHECK (
        NOT counts_as_zh_hans_document OR language_code = 'zh-Hans'
    ),
    CONSTRAINT language_document_export_ck CHECK (
        NOT raw_text_public_export_allowed
        OR public_export_state = 'PUBLIC_RAW'
    )
);

CREATE FUNCTION corpus.enforce_language_document_source()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_language_document_source$
DECLARE src corpus.language_source%ROWTYPE; fam corpus.language_source_family%ROWTYPE;
BEGIN
    SELECT * INTO src FROM corpus.language_source
    WHERE language_source_key = NEW.language_source_key
      AND language_source_family_key = NEW.language_source_family_key;
    IF NOT FOUND THEN RETURN NEW; END IF;
    SELECT * INTO fam FROM corpus.language_source_family
    WHERE language_source_family_key = NEW.language_source_family_key;
    IF NEW.raw_text_public_export_allowed
       AND src.raw_text_public_redistribution <> 'ALLOW' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_document_raw_redistribution_ck',
            MESSAGE = 'raw export cannot exceed source rights';
    END IF;
    IF NEW.public_export_state IN ('PUBLIC_RAW', 'PUBLIC_DERIVED_ONLY')
       AND src.derived_expression_public_release <> 'ALLOW' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_document_derived_redistribution_ck',
            MESSAGE = 'derived export cannot exceed source rights';
    END IF;
    IF NEW.counts_as_new_contemporary_document AND NOT (
        src.admitted AND src.qualifies_as_observed_tasting_language
        AND src.derived_counts_public_release = 'ALLOW'
        AND fam.counts_as_new_contemporary_family
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_document_contemporary_source_ck',
            MESSAGE = 'contemporary counts require a qualifying admitted family';
    END IF;
    IF NEW.counts_as_zh_hans_document AND NOT (
        src.admitted AND src.qualifies_as_observed_tasting_language
        AND src.derived_counts_public_release = 'ALLOW'
        AND fam.counts_as_zh_hans_family
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_document_zh_hans_source_ck',
            MESSAGE = 'zh-Hans counts require a qualifying admitted zh-Hans family';
    END IF;
    RETURN NEW;
END;
$enforce_language_document_source$;

CREATE TRIGGER language_document_source_biu
BEFORE INSERT OR UPDATE ON corpus.language_document
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_language_document_source();

CREATE TABLE corpus.language_review_candidate (
    candidate_key TEXT NOT NULL,
    candidate_inventory_sha256 TEXT NOT NULL,
    normalized_expression_sha256 TEXT NOT NULL,
    raw_variant_count INTEGER NOT NULL,
    occurrence_count INTEGER NOT NULL,
    document_count INTEGER NOT NULL,
    raw_surface_hash_inventory_sha256 TEXT NOT NULL,
    source_document_inventory_sha256 TEXT NOT NULL,
    candidate_text_retained BOOLEAN NOT NULL,
    CONSTRAINT language_review_candidate_pk PRIMARY KEY (candidate_key),
    CONSTRAINT language_review_candidate_inventory_uq UNIQUE (
        candidate_key, candidate_inventory_sha256
    ),
    CONSTRAINT language_review_candidate_normalized_uq UNIQUE (
        normalized_expression_sha256
    ),
    CONSTRAINT language_review_candidate_key_ck CHECK (
        candidate_key = lower(btrim(candidate_key))
        AND candidate_key ~ '^round3i\.[a-z0-9][a-z0-9._-]*\.sha256_[0-9a-f]{64}$'
        AND right(candidate_key, 64) = normalized_expression_sha256
        AND candidate_inventory_sha256 ~ '^[0-9a-f]{64}$'
        AND normalized_expression_sha256 ~ '^[0-9a-f]{64}$'
        AND raw_surface_hash_inventory_sha256 ~ '^[0-9a-f]{64}$'
        AND source_document_inventory_sha256 ~ '^[0-9a-f]{64}$'
        AND raw_variant_count > 0 AND occurrence_count > 0
        AND document_count > 0
        AND raw_variant_count <= occurrence_count
        AND document_count <= occurrence_count
        AND NOT candidate_text_retained
    )
);

CREATE TABLE corpus.language_candidate_review_decision (
    candidate_review_key TEXT NOT NULL,
    candidate_key TEXT NOT NULL,
    reviewer_key TEXT NOT NULL,
    review_pass TEXT NOT NULL,
    candidate_inventory_sha256 TEXT NOT NULL,
    decision_code TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    reviewed_on DATE NOT NULL,
    human_review BOOLEAN NOT NULL,
    automatic_language_detection BOOLEAN NOT NULL,
    CONSTRAINT language_candidate_review_decision_pk PRIMARY KEY (candidate_review_key),
    CONSTRAINT language_candidate_review_decision_uq UNIQUE (
        candidate_key, review_pass
    ),
    CONSTRAINT language_candidate_review_candidate_fk FOREIGN KEY (
        candidate_key, candidate_inventory_sha256
    ) REFERENCES corpus.language_review_candidate (
        candidate_key, candidate_inventory_sha256
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT language_candidate_review_key_ck CHECK (
        candidate_review_key = lower(btrim(candidate_review_key))
        AND candidate_review_key <> ''
        AND reviewer_key = lower(btrim(reviewer_key)) AND reviewer_key <> ''
        AND review_pass IN ('A', 'B')
        AND candidate_inventory_sha256 ~ '^[0-9a-f]{64}$'
        AND decision_code IN (
            'ADMIT_SENSORY_LANGUAGE', 'REJECT_NON_SENSORY', 'REJECT_UNCERTAIN'
        )
        AND reason_code ~ '^[a-z0-9_]+$'
        AND reviewed_on BETWEEN DATE '2026-01-01' AND DATE '2026-12-31'
        AND NOT human_review AND NOT automatic_language_detection
    )
);

CREATE FUNCTION corpus.enforce_independent_candidate_reviewer()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_independent_candidate_reviewer$
BEGIN
    IF EXISTS (
        SELECT 1 FROM corpus.language_candidate_review_decision
        WHERE candidate_key = NEW.candidate_key
          AND review_pass <> NEW.review_pass
          AND reviewer_key = NEW.reviewer_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_candidate_review_independent_reviewer_ck',
            MESSAGE = 'review passes require different reviewers';
    END IF;
    RETURN NEW;
END;
$enforce_independent_candidate_reviewer$;

CREATE TRIGGER language_candidate_review_reviewer_biu
BEFORE INSERT OR UPDATE ON corpus.language_candidate_review_decision
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_independent_candidate_reviewer();

CREATE TABLE corpus.language_expression (
    language_expression_key TEXT NOT NULL,
    language_code TEXT NOT NULL,
    representative_source_phrase TEXT NOT NULL,
    normalized_expression TEXT NOT NULL,
    normalized_expression_sha256 TEXT GENERATED ALWAYS AS (
        audit.round3i_utf8_sha256(normalized_expression)
    ) STORED,
    expression_role TEXT NOT NULL,
    source_authored BOOLEAN NOT NULL,
    machine_translated BOOLEAN NOT NULL DEFAULT FALSE,
    artificial_variant BOOLEAN NOT NULL DEFAULT FALSE,
    review_state TEXT NOT NULL,
    counts_toward_governed_total BOOLEAN NOT NULL,
    counts_as_zh_hans_sensory_expression BOOLEAN NOT NULL,
    public_export_allowed BOOLEAN NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT language_expression_pk PRIMARY KEY (language_expression_key),
    CONSTRAINT language_expression_normalized_uq UNIQUE (
        language_code, normalized_expression
    ),
    CONSTRAINT language_expression_key_ck CHECK (
        language_expression_key = lower(btrim(language_expression_key))
        AND language_expression_key <> ''
        AND language_code IN ('en', 'zh-Hans', 'und')
        AND representative_source_phrase = btrim(representative_source_phrase)
        AND representative_source_phrase <> ''
        AND normalized_expression = btrim(normalized_expression)
        AND normalized_expression <> ''
        AND expression_role IN (
            'PREPARATION', 'ROAST', 'SENSORY_ATTRIBUTE',
            'COMPOSITE_REFERENCE', 'QUALIFIER', 'TEXTURE',
            'BASIC_TASTE', 'AROMA_REFERENCE', 'CONSUMER_METAPHOR', 'UNRESOLVED'
        )
        AND review_state IN (
            'SOURCE_REVIEWED', 'DUAL_CODEX_REVIEWED',
            'REJECTED', 'QUARANTINED', 'DEPRECATED'
        )
        AND limitation = btrim(limitation) AND limitation <> ''
    ),
    CONSTRAINT language_expression_countability_ck CHECK (
        NOT counts_toward_governed_total OR (
            source_authored AND NOT machine_translated AND NOT artificial_variant
            AND review_state IN ('SOURCE_REVIEWED', 'DUAL_CODEX_REVIEWED')
            AND expression_role NOT IN ('PREPARATION', 'ROAST')
            AND public_export_allowed
        )
    ),
    CONSTRAINT language_expression_zh_hans_ck CHECK (
        NOT counts_as_zh_hans_sensory_expression OR (
            counts_toward_governed_total AND language_code = 'zh-Hans'
            AND expression_role NOT IN ('PREPARATION', 'ROAST')
        )
    ),
    CONSTRAINT language_expression_public_ck CHECK (
        NOT public_export_allowed
        OR review_state IN ('SOURCE_REVIEWED', 'DUAL_CODEX_REVIEWED')
    )
);

CREATE FUNCTION corpus.enforce_language_expression_review()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_language_expression_review$
DECLARE matching_candidate TEXT;
BEGIN
    IF NEW.review_state = 'DUAL_CODEX_REVIEWED' THEN
        SELECT candidate_key INTO matching_candidate
        FROM corpus.language_review_candidate
        WHERE normalized_expression_sha256 = NEW.normalized_expression_sha256;
        IF matching_candidate IS NULL OR (
            SELECT count(*) FROM corpus.language_candidate_review_decision
            WHERE candidate_key = matching_candidate
              AND decision_code = 'ADMIT_SENSORY_LANGUAGE'
        ) <> 2 OR (
            SELECT count(DISTINCT reviewer_key)
            FROM corpus.language_candidate_review_decision
            WHERE candidate_key = matching_candidate
              AND decision_code = 'ADMIT_SENSORY_LANGUAGE'
        ) <> 2 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'language_expression_dual_review_consensus_ck',
                MESSAGE = 'dual-reviewed expressions require two independent admits';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_language_expression_review$;

CREATE CONSTRAINT TRIGGER language_expression_review_aiu
AFTER INSERT OR UPDATE ON corpus.language_expression
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_language_expression_review();

CREATE TABLE corpus.language_expression_occurrence (
    language_occurrence_key TEXT NOT NULL,
    language_document_key TEXT NOT NULL,
    language_expression_key TEXT NOT NULL,
    raw_source_phrase TEXT NOT NULL,
    raw_source_phrase_sha256 TEXT GENERATED ALWAYS AS (
        audit.round3i_utf8_sha256(raw_source_phrase)
    ) STORED,
    source_locator TEXT NOT NULL,
    observed_value JSONB NOT NULL,
    lifecycle_status TEXT NOT NULL DEFAULT 'ADMITTED',
    CONSTRAINT language_expression_occurrence_pk PRIMARY KEY (language_occurrence_key),
    CONSTRAINT language_expression_occurrence_uq UNIQUE (
        language_document_key, language_expression_key, source_locator
    ),
    CONSTRAINT language_expression_occurrence_document_fk FOREIGN KEY (
        language_document_key
    ) REFERENCES corpus.language_document (language_document_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT language_expression_occurrence_expression_fk FOREIGN KEY (
        language_expression_key
    ) REFERENCES corpus.language_expression (language_expression_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT language_expression_occurrence_text_ck CHECK (
        language_occurrence_key = lower(btrim(language_occurrence_key))
        AND language_occurrence_key <> ''
        AND raw_source_phrase = btrim(raw_source_phrase)
        AND raw_source_phrase <> ''
        AND source_locator = btrim(source_locator) AND source_locator <> ''
        AND jsonb_typeof(observed_value) = 'object'
        AND lifecycle_status IN (
            'ADMITTED', 'REJECTED', 'QUARANTINED', 'DEPRECATED'
        )
    )
);

CREATE INDEX language_expression_occurrence_expression_ix
ON corpus.language_expression_occurrence (language_expression_key);

CREATE FUNCTION corpus.enforce_language_occurrence_source()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_language_occurrence_source$
DECLARE doc corpus.language_document%ROWTYPE; expr corpus.language_expression%ROWTYPE;
        raw_internal TEXT; src_admitted BOOLEAN;
BEGIN
    SELECT * INTO doc FROM corpus.language_document
    WHERE language_document_key = NEW.language_document_key;
    SELECT * INTO expr FROM corpus.language_expression
    WHERE language_expression_key = NEW.language_expression_key;
    IF doc.language_document_key IS NULL OR expr.language_expression_key IS NULL THEN
        RETURN NEW;
    END IF;
    SELECT raw_text_internal_use, admitted INTO raw_internal, src_admitted
    FROM corpus.language_source
    WHERE language_source_key = doc.language_source_key;
    IF raw_internal = 'DENY' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_occurrence_raw_retention_ck',
            MESSAGE = 'raw phrases cannot be retained when source rights deny it';
    END IF;
    IF NEW.lifecycle_status = 'ADMITTED' AND NOT (
        doc.lifecycle_status = 'ADMITTED' AND src_admitted
        AND expr.review_state IN ('SOURCE_REVIEWED', 'DUAL_CODEX_REVIEWED')
        AND doc.language_code = expr.language_code
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_occurrence_admission_ck',
            MESSAGE = 'admitted occurrences require aligned admitted evidence';
    END IF;
    RETURN NEW;
END;
$enforce_language_occurrence_source$;

CREATE TRIGGER language_occurrence_source_biu
BEFORE INSERT OR UPDATE ON corpus.language_expression_occurrence
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_language_occurrence_source();

CREATE FUNCTION corpus.validate_language_expression_evidence()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $validate_language_expression_evidence$
DECLARE checked_key TEXT; checked corpus.language_expression%ROWTYPE;
BEGIN
    checked_key := CASE WHEN TG_OP = 'DELETE'
        THEN OLD.language_expression_key ELSE NEW.language_expression_key END;
    SELECT * INTO checked FROM corpus.language_expression
    WHERE language_expression_key = checked_key;
    IF NOT FOUND OR NOT checked.counts_toward_governed_total THEN
        RETURN NULL;
    END IF;
    IF NOT EXISTS (
        SELECT 1
        FROM corpus.language_expression_occurrence AS occurrence
        JOIN corpus.language_document AS document
          ON document.language_document_key = occurrence.language_document_key
        JOIN corpus.language_source AS source
          ON source.language_source_key = document.language_source_key
        JOIN corpus.language_source_family AS family
          ON family.language_source_family_key = document.language_source_family_key
        WHERE occurrence.language_expression_key = checked_key
          AND occurrence.lifecycle_status = 'ADMITTED'
          AND document.lifecycle_status = 'ADMITTED'
          AND document.source_authored AND NOT document.machine_translated
          AND NOT document.artificial_variant AND document.sensory_language_verified
          AND source.admitted AND source.qualifies_as_observed_tasting_language
          AND source.derived_expression_public_release = 'ALLOW'
          AND family.admitted
          AND (NOT checked.counts_as_zh_hans_sensory_expression
               OR (document.counts_as_zh_hans_document
                   AND family.counts_as_zh_hans_family))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_expression_observed_evidence_ck',
            MESSAGE = 'countable expressions require admitted observed evidence';
    END IF;
    RETURN NULL;
END;
$validate_language_expression_evidence$;

CREATE CONSTRAINT TRIGGER language_expression_evidence_aiu
AFTER INSERT OR UPDATE ON corpus.language_expression
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION corpus.validate_language_expression_evidence();

CREATE CONSTRAINT TRIGGER language_occurrence_evidence_aud
AFTER UPDATE OR DELETE ON corpus.language_expression_occurrence
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION corpus.validate_language_expression_evidence();

CREATE TABLE audit.round3i_acquisition_batch (
    batch_key TEXT NOT NULL PRIMARY KEY,
    targeted_gap TEXT NOT NULL,
    named_sources_reviewed INTEGER NOT NULL,
    sources_admitted INTEGER NOT NULL,
    source_families_added INTEGER NOT NULL,
    rows_added INTEGER NOT NULL,
    documents_added INTEGER NOT NULL,
    unique_expressions_added INTEGER NOT NULL,
    zh_hans_expressions_added INTEGER NOT NULL,
    coverage_cells_added INTEGER NOT NULL,
    relationship_support_added INTEGER NOT NULL,
    rights_blocked_count INTEGER NOT NULL,
    access_blocked_count INTEGER NOT NULL,
    marginal_coverage_gain TEXT NOT NULL,
    readiness_state_after TEXT NOT NULL,
    result_path TEXT NOT NULL,
    completed_on DATE NOT NULL,
    CONSTRAINT round3i_acquisition_batch_ck CHECK (
        batch_key = lower(btrim(batch_key)) AND batch_key <> ''
        AND targeted_gap = btrim(targeted_gap) AND targeted_gap <> ''
        AND named_sources_reviewed >= sources_admitted AND sources_admitted >= 0
        AND source_families_added >= 0 AND rows_added >= 0
        AND documents_added >= 0 AND unique_expressions_added >= 0
        AND zh_hans_expressions_added >= 0 AND coverage_cells_added >= 0
        AND relationship_support_added >= 0 AND rights_blocked_count >= 0
        AND access_blocked_count >= 0
        AND marginal_coverage_gain IN ('HIGH', 'MEDIUM', 'LOW', 'NONE')
        AND readiness_state_after = btrim(readiness_state_after)
        AND readiness_state_after <> ''
        AND result_path = btrim(result_path) AND result_path <> ''
    )
);

CREATE TABLE audit.research_database_release (
    freeze_version TEXT NOT NULL PRIMARY KEY,
    lifecycle_status TEXT NOT NULL,
    source_checkpoint_sha TEXT NOT NULL UNIQUE,
    final_repository_sha TEXT,
    final_repository_ref TEXT,
    release_tag_target_sha TEXT,
    release_tag_object_sha TEXT,
    manifest_path TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    expected_state_commit_sha TEXT NOT NULL,
    release_tag TEXT NOT NULL,
    supersedes_freeze_version TEXT,
    created_on DATE NOT NULL,
    frozen_on DATE,
    limitation TEXT NOT NULL,
    CONSTRAINT research_database_release_supersedes_fk FOREIGN KEY (
        supersedes_freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_release_key_ck CHECK (
        freeze_version ~ '^coffee-sensory-research-db-v[0-9]+\.[0-9]+\.[0-9]+$'
        AND lifecycle_status IN (
            'DRAFT', 'FREEZE_CANDIDATE', 'FROZEN', 'SUPERSEDED'
        )
        AND source_checkpoint_sha ~ '^[0-9a-f]{40}$'
        AND (final_repository_sha IS NULL
             OR final_repository_sha ~ '^[0-9a-f]{40}$')
        AND (final_repository_ref IS NULL
             OR final_repository_ref = 'refs/heads/main')
        AND (release_tag_target_sha IS NULL
             OR release_tag_target_sha ~ '^[0-9a-f]{40}$')
        AND (release_tag_object_sha IS NULL
             OR release_tag_object_sha ~ '^[0-9a-f]{40}$')
        AND manifest_path = btrim(manifest_path) AND manifest_path <> ''
        AND manifest_sha256 ~ '^[0-9a-f]{64}$'
        AND expected_state_commit_sha ~ '^[0-9a-f]{40}$'
        AND release_tag = btrim(release_tag) AND release_tag <> ''
        AND limitation = btrim(limitation) AND limitation <> ''
        AND (supersedes_freeze_version IS NULL
             OR supersedes_freeze_version <> freeze_version)
    ),
    CONSTRAINT research_database_release_frozen_ck CHECK (
        (lifecycle_status = 'FROZEN' AND final_repository_sha IS NOT NULL
         AND final_repository_ref = 'refs/heads/main'
         AND release_tag_target_sha = final_repository_sha
         AND release_tag_object_sha IS NOT NULL
         AND release_tag_object_sha <> release_tag_target_sha
         AND frozen_on IS NOT NULL)
        OR (lifecycle_status <> 'FROZEN' AND final_repository_sha IS NULL
            AND final_repository_ref IS NULL
            AND release_tag_target_sha IS NULL
            AND release_tag_object_sha IS NULL
            AND frozen_on IS NULL)
    )
);

CREATE TABLE audit.research_database_artifact_hash (
    freeze_version TEXT NOT NULL,
    artifact_key TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    verified_sha256 TEXT NOT NULL,
    hash_verified BOOLEAN NOT NULL,
    database_derived BOOLEAN NOT NULL,
    required_for_freeze BOOLEAN NOT NULL,
    hash_semantics TEXT NOT NULL,
    CONSTRAINT research_database_artifact_hash_pk PRIMARY KEY (
        freeze_version, artifact_key
    ),
    CONSTRAINT research_database_artifact_hash_path_uq UNIQUE (
        freeze_version, artifact_path
    ),
    CONSTRAINT research_database_artifact_hash_type_uq UNIQUE (
        freeze_version, artifact_type
    ),
    CONSTRAINT research_database_artifact_hash_release_fk FOREIGN KEY (
        freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_artifact_hash_ck CHECK (
        artifact_key = lower(btrim(artifact_key)) AND artifact_key <> ''
        AND artifact_type IN (
            'CANONICAL_INVENTORY', 'SOURCE_INVENTORY', 'RAW_FILE_MANIFEST',
            'SENSORY_INVENTORY', 'CONTEXT_COVERAGE', 'LANGUAGE_CORPUS',
            'RELATIONSHIP_EVIDENCE', 'QUESTION_EVIDENCE',
            'FEATURE_REGISTRY', 'SOURCE_PARTITION', 'FREEZE_MANIFEST'
        )
        AND artifact_path = btrim(artifact_path) AND artifact_path <> ''
        AND sha256 ~ '^[0-9a-f]{64}$'
        AND verified_sha256 ~ '^[0-9a-f]{64}$'
        AND (NOT hash_verified OR sha256 = verified_sha256)
        AND (NOT required_for_freeze OR hash_verified)
        AND hash_semantics = btrim(hash_semantics) AND hash_semantics <> ''
    )
);

CREATE TABLE audit.research_database_current_surface (
    freeze_version TEXT NOT NULL,
    surface_key TEXT NOT NULL,
    surface_role TEXT,
    database_object_name TEXT NOT NULL,
    object_definition_sha256 TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    approved_for_future_prebuild BOOLEAN NOT NULL,
    required_for_freeze BOOLEAN NOT NULL,
    supersedes_object_name TEXT,
    contract_note TEXT NOT NULL,
    CONSTRAINT research_database_current_surface_pk PRIMARY KEY (
        freeze_version, surface_key
    ),
    CONSTRAINT research_database_current_surface_object_uq UNIQUE (
        freeze_version, database_object_name
    ),
    CONSTRAINT research_database_current_surface_role_uq UNIQUE (
        freeze_version, surface_role
    ),
    CONSTRAINT research_database_current_surface_release_fk FOREIGN KEY (
        freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_current_surface_ck CHECK (
        surface_key = lower(btrim(surface_key)) AND surface_key <> ''
        AND database_object_name ~ '^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$'
        AND object_definition_sha256 ~ '^[0-9a-f]{64}$'
        AND lifecycle_status IN (
            'CURRENT_APPROVED', 'DEPRECATED_RESEARCH',
            'HISTORICAL', 'RESEARCH_ONLY'
        )
        AND ((lifecycle_status = 'CURRENT_APPROVED'
              AND surface_role IS NOT NULL
              AND approved_for_future_prebuild AND required_for_freeze
              AND supersedes_object_name IS NOT NULL)
             OR (lifecycle_status <> 'CURRENT_APPROVED'
                 AND surface_role IS NULL
                 AND NOT approved_for_future_prebuild
                 AND NOT required_for_freeze))
        AND (supersedes_object_name IS NULL OR supersedes_object_name
             ~ '^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$')
        AND contract_note = btrim(contract_note) AND contract_note <> ''
    ),
    CONSTRAINT research_database_current_surface_role_ck CHECK (
        surface_role IS NULL OR database_object_name = CASE surface_role
            WHEN 'CANONICAL_CONCEPT' THEN 'kb.v_current_canonical_concept'
            WHEN 'LEXICAL_EVIDENCE' THEN 'kb.v_current_lexical_evidence'
            WHEN 'CONTEXT' THEN 'context.v_current_context'
            WHEN 'SENSORY_PARTITION' THEN 'evidence.v_current_sensory_partition'
            WHEN 'LANGUAGE_CORPUS' THEN 'corpus.v_current_language_corpus'
            WHEN 'RELATIONSHIP_EVIDENCE' THEN 'evidence.v_current_relationship_evidence'
            WHEN 'QUESTION_EVIDENCE' THEN 'calibration.v_current_question_evidence'
            WHEN 'MODEL_PREBUILD_FEATURE' THEN 'evidence.v_current_model_prebuild_feature'
            ELSE NULL END
    )
);

CREATE TABLE audit.research_database_threshold_revision (
    threshold_revision_key TEXT NOT NULL PRIMARY KEY,
    freeze_version TEXT NOT NULL,
    readiness_key TEXT NOT NULL,
    prior_threshold TEXT NOT NULL,
    revised_threshold TEXT NOT NULL,
    change_direction TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    decision_record_path TEXT NOT NULL,
    decision_record_sha256 TEXT NOT NULL,
    CONSTRAINT research_database_threshold_revision_release_fk FOREIGN KEY (
        freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_threshold_revision_ck CHECK (
        threshold_revision_key = lower(btrim(threshold_revision_key))
        AND threshold_revision_key <> ''
        AND readiness_key = btrim(readiness_key) AND readiness_key <> ''
        AND prior_threshold = btrim(prior_threshold) AND prior_threshold <> ''
        AND revised_threshold = btrim(revised_threshold) AND revised_threshold <> ''
        AND change_direction IN ('RAISED', 'UNCHANGED', 'LOWERED')
        AND (change_direction <> 'LOWERED'
             OR approval_status = 'EXPLICIT_GOVERNANCE_APPROVAL')
        AND approval_status IN (
            'NOT_REQUIRED', 'EXPLICIT_GOVERNANCE_APPROVAL'
        )
        AND decision_record_path = btrim(decision_record_path)
        AND decision_record_path <> ''
        AND decision_record_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE audit.research_database_release_member (
    freeze_version TEXT NOT NULL,
    member_table TEXT NOT NULL,
    member_key TEXT NOT NULL,
    member_row_sha256 TEXT NOT NULL,
    CONSTRAINT research_database_release_member_pk PRIMARY KEY (
        freeze_version, member_table, member_key
    ),
    CONSTRAINT research_database_release_member_release_fk FOREIGN KEY (
        freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_release_member_ck CHECK (
        member_table IN (
            'corpus.language_source_family', 'corpus.language_source',
            'corpus.language_document', 'corpus.language_review_candidate',
            'corpus.language_candidate_review_decision',
            'corpus.language_expression',
            'corpus.language_expression_occurrence'
        )
        AND member_key = btrim(member_key) AND member_key <> ''
        AND member_row_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE TABLE audit.research_database_release_attestation (
    freeze_version TEXT NOT NULL PRIMARY KEY,
    final_repository_sha TEXT NOT NULL,
    final_repository_ref TEXT NOT NULL,
    release_tag TEXT NOT NULL,
    release_tag_target_sha TEXT NOT NULL,
    release_tag_object_sha TEXT NOT NULL,
    attested_at TIMESTAMPTZ NOT NULL,
    attested_by TEXT NOT NULL,
    attestation_basis TEXT NOT NULL,
    CONSTRAINT research_database_release_attestation_release_fk FOREIGN KEY (
        freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT research_database_release_attestation_ck CHECK (
        final_repository_sha ~ '^[0-9a-f]{40}$'
        AND final_repository_ref = 'refs/heads/main'
        AND release_tag = btrim(release_tag) AND release_tag <> ''
        AND release_tag_target_sha = final_repository_sha
        AND release_tag_object_sha ~ '^[0-9a-f]{40}$'
        AND release_tag_object_sha <> release_tag_target_sha
        AND attested_by = btrim(attested_by) AND attested_by <> ''
        AND attestation_basis = btrim(attestation_basis)
        AND attestation_basis <> ''
    )
);

CREATE FUNCTION audit.research_database_member_row_sha256(
    checked_table TEXT, checked_key TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
STABLE
SET search_path = pg_catalog
AS $research_database_member_row_sha256$
DECLARE row_value JSONB;
BEGIN
    CASE checked_table
      WHEN 'corpus.language_source_family' THEN
        SELECT to_jsonb(t) INTO row_value FROM corpus.language_source_family t
        WHERE language_source_family_key = checked_key;
      WHEN 'corpus.language_source' THEN
        SELECT to_jsonb(t) INTO row_value FROM corpus.language_source t
        WHERE language_source_key = checked_key;
      WHEN 'corpus.language_document' THEN
        SELECT to_jsonb(t) INTO row_value FROM corpus.language_document t
        WHERE language_document_key = checked_key;
      WHEN 'corpus.language_review_candidate' THEN
        SELECT to_jsonb(t) INTO row_value FROM corpus.language_review_candidate t
        WHERE candidate_key = checked_key;
      WHEN 'corpus.language_candidate_review_decision' THEN
        SELECT to_jsonb(t) INTO row_value
        FROM corpus.language_candidate_review_decision t
        WHERE candidate_review_key = checked_key;
      WHEN 'corpus.language_expression' THEN
        SELECT to_jsonb(t) INTO row_value FROM corpus.language_expression t
        WHERE language_expression_key = checked_key;
      WHEN 'corpus.language_expression_occurrence' THEN
        SELECT to_jsonb(t) INTO row_value
        FROM corpus.language_expression_occurrence t
        WHERE language_occurrence_key = checked_key;
      ELSE
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_release_member_table_ck',
            MESSAGE = 'unsupported release-member table';
    END CASE;
    IF row_value IS NULL THEN RETURN NULL; END IF;
    RETURN encode(sha256(convert_to(row_value::TEXT, 'UTF8')), 'hex');
END;
$research_database_member_row_sha256$;

CREATE FUNCTION audit.enforce_research_database_release_member()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_research_database_release_member$
DECLARE actual_sha TEXT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit.research_database_release_attestation
        WHERE freeze_version = NEW.freeze_version
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_frozen_membership_immutable_ck',
            MESSAGE = 'frozen membership is immutable';
    END IF;
    actual_sha := audit.research_database_member_row_sha256(
        NEW.member_table, NEW.member_key
    );
    IF actual_sha IS NULL OR actual_sha <> NEW.member_row_sha256 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_release_member_hash_ck',
            MESSAGE = 'release member must exist and match its row hash';
    END IF;
    RETURN NEW;
END;
$enforce_research_database_release_member$;

CREATE TRIGGER research_database_release_member_biu
BEFORE INSERT OR UPDATE ON audit.research_database_release_member
FOR EACH ROW EXECUTE FUNCTION audit.enforce_research_database_release_member();

CREATE FUNCTION audit.refresh_research_database_release_members(
    selected_freeze_version TEXT
)
RETURNS VOID
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $refresh_research_database_release_members$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM audit.research_database_release
        WHERE freeze_version = selected_freeze_version
          AND lifecycle_status IN ('DRAFT', 'FREEZE_CANDIDATE')
    ) OR EXISTS (
        SELECT 1 FROM audit.research_database_release_attestation
        WHERE freeze_version = selected_freeze_version
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_release_member_refresh_state_ck',
            MESSAGE = 'membership can only be refreshed for an unfrozen candidate';
    END IF;
    DELETE FROM audit.research_database_release_member
    WHERE freeze_version = selected_freeze_version;
    INSERT INTO audit.research_database_release_member
        (freeze_version, member_table, member_key, member_row_sha256)
    SELECT selected_freeze_version, member_table, member_key,
           audit.research_database_member_row_sha256(member_table, member_key)
    FROM (
        SELECT 'corpus.language_source_family'::TEXT member_table,
               language_source_family_key member_key
        FROM corpus.language_source_family
        UNION ALL SELECT 'corpus.language_source', language_source_key
        FROM corpus.language_source
        UNION ALL SELECT 'corpus.language_document', language_document_key
        FROM corpus.language_document
        UNION ALL SELECT 'corpus.language_review_candidate', candidate_key
        FROM corpus.language_review_candidate
        UNION ALL SELECT 'corpus.language_candidate_review_decision',
                         candidate_review_key
        FROM corpus.language_candidate_review_decision
        UNION ALL SELECT 'corpus.language_expression', language_expression_key
        FROM corpus.language_expression
        UNION ALL SELECT 'corpus.language_expression_occurrence',
                         language_occurrence_key
        FROM corpus.language_expression_occurrence
    ) AS members;
END;
$refresh_research_database_release_members$;

CREATE FUNCTION audit.research_database_release_members_complete(
    selected_freeze_version TEXT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $research_database_release_members_complete$
WITH expected AS (
    SELECT sum(n)::BIGINT AS n FROM (
        SELECT count(*) n FROM corpus.language_source_family
        UNION ALL SELECT count(*) FROM corpus.language_source
        UNION ALL SELECT count(*) FROM corpus.language_document
        UNION ALL SELECT count(*) FROM corpus.language_review_candidate
        UNION ALL SELECT count(*) FROM corpus.language_candidate_review_decision
        UNION ALL SELECT count(*) FROM corpus.language_expression
        UNION ALL SELECT count(*) FROM corpus.language_expression_occurrence
    ) counts
), actual AS (
    SELECT count(*)::BIGINT n,
           bool_and(member_row_sha256 =
               audit.research_database_member_row_sha256(
                   member_table, member_key)) hashes_match
    FROM audit.research_database_release_member
    WHERE freeze_version = selected_freeze_version
)
SELECT expected.n = actual.n AND coalesce(actual.hashes_match, FALSE)
FROM expected, actual
$research_database_release_members_complete$;

CREATE FUNCTION audit.current_research_database_release_version()
RETURNS TEXT
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $current_research_database_release_version$
SELECT freeze_version
FROM audit.research_database_release
WHERE lifecycle_status IN ('FROZEN', 'FREEZE_CANDIDATE')
ORDER BY (lifecycle_status = 'FROZEN') DESC, frozen_on DESC NULLS LAST,
         created_on DESC, freeze_version DESC
LIMIT 1
$current_research_database_release_version$;

CREATE FUNCTION audit.prevent_frozen_release_payload_mutation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $prevent_frozen_release_payload_mutation$
DECLARE checked_version TEXT;
BEGIN
    checked_version := CASE WHEN TG_OP = 'DELETE'
        THEN OLD.freeze_version ELSE NEW.freeze_version END;
    IF EXISTS (
        SELECT 1 FROM audit.research_database_release_attestation
        WHERE freeze_version = checked_version
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_frozen_release_payload_immutable_ck',
            MESSAGE = 'frozen release payload is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$prevent_frozen_release_payload_mutation$;

CREATE TRIGGER research_database_artifact_hash_immutable_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.research_database_artifact_hash
FOR EACH ROW EXECUTE FUNCTION audit.prevent_frozen_release_payload_mutation();
CREATE TRIGGER research_database_current_surface_immutable_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.research_database_current_surface
FOR EACH ROW EXECUTE FUNCTION audit.prevent_frozen_release_payload_mutation();
CREATE TRIGGER research_database_threshold_revision_immutable_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.research_database_threshold_revision
FOR EACH ROW EXECUTE FUNCTION audit.prevent_frozen_release_payload_mutation();
CREATE TRIGGER research_database_release_member_immutable_bd
BEFORE DELETE ON audit.research_database_release_member
FOR EACH ROW EXECUTE FUNCTION audit.prevent_frozen_release_payload_mutation();

CREATE FUNCTION audit.prevent_frozen_language_member_mutation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $prevent_frozen_language_member_mutation$
DECLARE checked_key TEXT;
BEGIN
    checked_key := to_jsonb(OLD) ->> TG_ARGV[0];
    IF EXISTS (
        SELECT 1
        FROM audit.research_database_release_member member
        JOIN audit.research_database_release_attestation attestation
          ON attestation.freeze_version = member.freeze_version
        WHERE member.member_table = TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME
          AND member.member_key = checked_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_frozen_member_immutable_ck',
            MESSAGE = 'a row included in a frozen release is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$prevent_frozen_language_member_mutation$;

CREATE TRIGGER language_source_family_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_source_family FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('language_source_family_key');
CREATE TRIGGER language_source_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_source FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('language_source_key');
CREATE TRIGGER language_document_release_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_document FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('language_document_key');
CREATE TRIGGER language_review_candidate_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_review_candidate FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('candidate_key');
CREATE TRIGGER language_candidate_decision_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_candidate_review_decision FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('candidate_review_key');
CREATE TRIGGER language_expression_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_expression FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('language_expression_key');
CREATE TRIGGER language_occurrence_frozen_bud BEFORE UPDATE OR DELETE
ON corpus.language_expression_occurrence FOR EACH ROW EXECUTE FUNCTION
audit.prevent_frozen_language_member_mutation('language_occurrence_key');

CREATE FUNCTION corpus.prevent_frozen_language_document_mutation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $prevent_frozen_language_document_mutation$
BEGIN
    IF OLD.frozen_snapshot THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'language_document_frozen_immutable_ck',
            MESSAGE = 'a frozen language document is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$prevent_frozen_language_document_mutation$;

CREATE TRIGGER language_document_snapshot_immutable_bud
BEFORE UPDATE OR DELETE ON corpus.language_document
FOR EACH ROW EXECUTE FUNCTION corpus.prevent_frozen_language_document_mutation();

CREATE FUNCTION audit.prevent_frozen_release_mutation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $prevent_frozen_release_mutation$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.lifecycle_status = 'FROZEN' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'research_database_freeze_attestation_required_ck',
                MESSAGE = 'a frozen release requires a post-commit attestation';
        END IF;
        RETURN NEW;
    END IF;
    IF OLD.lifecycle_status IN ('FROZEN', 'SUPERSEDED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_frozen_immutable_ck',
            MESSAGE = 'terminal release rows are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF NEW.lifecycle_status = 'FROZEN' AND NOT EXISTS (
        SELECT 1 FROM audit.research_database_release_attestation
        WHERE freeze_version = NEW.freeze_version
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_freeze_attestation_required_ck',
            MESSAGE = 'a frozen release requires a post-commit attestation';
    END IF;
    RETURN NEW;
END;
$prevent_frozen_release_mutation$;

CREATE TRIGGER research_database_release_guard_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.research_database_release
FOR EACH ROW EXECUTE FUNCTION audit.prevent_frozen_release_mutation();

CREATE FUNCTION audit.validate_research_database_release_attestation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $validate_research_database_release_attestation$
DECLARE selected audit.research_database_release%ROWTYPE;
BEGIN
    SELECT * INTO selected FROM audit.research_database_release
    WHERE freeze_version = NEW.freeze_version;
    IF selected.lifecycle_status <> 'FREEZE_CANDIDATE'
       OR selected.release_tag <> NEW.release_tag THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_attestation_candidate_ck',
            MESSAGE = 'attestation must match a freeze candidate and its tag';
    END IF;
    IF NOT audit.research_database_release_members_complete(NEW.freeze_version)
       OR (SELECT count(*) FROM audit.research_database_artifact_hash
           WHERE freeze_version = NEW.freeze_version
             AND required_for_freeze AND hash_verified
             AND sha256 = verified_sha256) <> 11
       OR NOT EXISTS (
           SELECT 1 FROM audit.research_database_artifact_hash
           WHERE freeze_version = NEW.freeze_version
             AND artifact_type = 'FREEZE_MANIFEST'
             AND sha256 = selected.manifest_sha256
       )
       OR (SELECT count(*) FROM audit.research_database_current_surface
           WHERE freeze_version = NEW.freeze_version
             AND lifecycle_status = 'CURRENT_APPROVED'
             AND required_for_freeze
             AND approved_for_future_prebuild) <> 8 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_attestation_integrity_gate_ck',
            MESSAGE = 'membership, artifacts, or current surfaces are incomplete';
    END IF;
    IF EXISTS (
        SELECT 1 FROM audit.run_model_prebuild_readiness_gate()
        WHERE hard_gate AND NOT passed
          AND readiness_key NOT LIKE 'language.%'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_attestation_readiness_gate_ck',
            MESSAGE = 'a non-language hard readiness gate is failing';
    END IF;
    IF (SELECT count(*) FROM corpus.language_source_family f
        JOIN audit.research_database_release_member m
          ON m.freeze_version = NEW.freeze_version
         AND m.member_table = 'corpus.language_source_family'
         AND m.member_key = f.language_source_family_key
        WHERE f.counts_as_new_contemporary_family) < 3
       OR (SELECT count(*) FROM corpus.language_document d
           JOIN audit.research_database_release_member m
             ON m.freeze_version = NEW.freeze_version
            AND m.member_table = 'corpus.language_document'
            AND m.member_key = d.language_document_key
           WHERE d.counts_as_new_contemporary_document) < 500
       OR (SELECT count(*) FROM (
              SELECT normalized_text FROM corpus.normalized_expression
              UNION
              SELECT e.normalized_expression
              FROM corpus.language_expression e
              JOIN audit.research_database_release_member m
                ON m.freeze_version = NEW.freeze_version
               AND m.member_table = 'corpus.language_expression'
               AND m.member_key = e.language_expression_key
              WHERE e.counts_toward_governed_total
           ) governed) < 2500
       OR (SELECT count(*) FROM corpus.language_source_family f
           JOIN audit.research_database_release_member m
             ON m.freeze_version = NEW.freeze_version
            AND m.member_table = 'corpus.language_source_family'
            AND m.member_key = f.language_source_family_key
           WHERE f.counts_as_zh_hans_family) < 2 THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'research_database_attestation_language_gate_ck',
            MESSAGE = 'a mandatory Round 3I language gate is failing';
    END IF;
    RETURN NEW;
END;
$validate_research_database_release_attestation$;

CREATE TRIGGER research_database_release_attestation_bi
BEFORE INSERT ON audit.research_database_release_attestation
FOR EACH ROW EXECUTE FUNCTION audit.validate_research_database_release_attestation();

CREATE FUNCTION audit.complete_research_database_release_attestation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $complete_research_database_release_attestation$
BEGIN
    UPDATE audit.research_database_release
    SET lifecycle_status = 'FROZEN',
        final_repository_sha = NEW.final_repository_sha,
        final_repository_ref = NEW.final_repository_ref,
        release_tag_target_sha = NEW.release_tag_target_sha,
        release_tag_object_sha = NEW.release_tag_object_sha,
        frozen_on = NEW.attested_at::DATE
    WHERE freeze_version = NEW.freeze_version;
    RETURN NEW;
END;
$complete_research_database_release_attestation$;

CREATE TRIGGER research_database_release_attestation_ai
AFTER INSERT ON audit.research_database_release_attestation
FOR EACH ROW EXECUTE FUNCTION audit.complete_research_database_release_attestation();

CREATE FUNCTION audit.prevent_release_attestation_mutation()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $prevent_release_attestation_mutation$
BEGIN
    RAISE EXCEPTION USING ERRCODE = '23514',
        CONSTRAINT = 'research_database_release_attestation_immutable_ck',
        MESSAGE = 'release attestations are immutable';
END;
$prevent_release_attestation_mutation$;

CREATE TRIGGER research_database_release_attestation_bud
BEFORE UPDATE OR DELETE ON audit.research_database_release_attestation
FOR EACH ROW EXECUTE FUNCTION audit.prevent_release_attestation_mutation();

CREATE FUNCTION audit.finalize_research_database_release(
    selected_freeze_version TEXT,
    selected_final_repository_sha TEXT,
    selected_release_tag TEXT,
    selected_release_tag_object_sha TEXT,
    selected_attested_by TEXT,
    selected_attestation_basis TEXT
)
RETURNS VOID LANGUAGE SQL SET search_path = pg_catalog
AS $finalize_research_database_release$
INSERT INTO audit.research_database_release_attestation (
    freeze_version, final_repository_sha, final_repository_ref,
    release_tag, release_tag_target_sha, release_tag_object_sha,
    attested_at, attested_by, attestation_basis
) VALUES (
    selected_freeze_version, selected_final_repository_sha,
    'refs/heads/main', selected_release_tag, selected_final_repository_sha,
    selected_release_tag_object_sha, CURRENT_TIMESTAMP,
    selected_attested_by, selected_attestation_basis
)
$finalize_research_database_release$;

COMMIT;
