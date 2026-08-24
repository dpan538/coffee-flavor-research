\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- Round 2B corpus acquisition governance.
-- Industry pages are language observations, never canonical sensory evidence.
-- This migration stores policy decisions and immutable snapshot identities;
-- protected raw text remains optional and production export remains opt-in.

BEGIN;

INSERT INTO ref.language_tag (
    language_tag_code,
    display_name,
    description
)
VALUES (
    'und',
    'Undetermined language',
    'BCP 47 und for an observation whose language was not asserted by its source or established by review.'
);

CREATE TABLE ref.corpus_source_decision (
    corpus_source_decision_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    permits_document_metadata BOOLEAN NOT NULL,
    permits_raw_retention BOOLEAN NOT NULL,
    permits_derived_terms BOOLEAN NOT NULL,
    permits_derived_redistribution BOOLEAN NOT NULL,
    permits_raw_redistribution BOOLEAN NOT NULL,
    requires_manual_access BOOLEAN NOT NULL,
    is_blocking BOOLEAN NOT NULL,
    CONSTRAINT corpus_source_decision_pk PRIMARY KEY (
        corpus_source_decision_code
    ),
    CONSTRAINT corpus_source_decision_code_nonempty_ck CHECK (
        corpus_source_decision_code = btrim(corpus_source_decision_code)
        AND corpus_source_decision_code <> ''
    ),
    CONSTRAINT corpus_source_decision_text_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT corpus_source_decision_permission_order_ck CHECK (
        (NOT permits_raw_retention OR permits_document_metadata)
        AND (NOT permits_derived_terms OR permits_document_metadata)
        AND (NOT permits_derived_redistribution OR permits_derived_terms)
        AND (NOT permits_raw_redistribution OR permits_raw_retention)
    ),
    CONSTRAINT corpus_source_decision_blocking_ck CHECK (
        NOT is_blocking
        OR NOT (
            permits_document_metadata
            OR permits_raw_retention
            OR permits_derived_terms
            OR permits_derived_redistribution
            OR permits_raw_redistribution
        )
    )
);

INSERT INTO ref.corpus_source_decision VALUES
    ('allow_private_analysis', 'Allow private analysis', 'Metadata, retained raw text, and derived terms may be used in the governed private analysis boundary.', TRUE, TRUE, TRUE, FALSE, FALSE, FALSE, FALSE),
    ('allow_metadata_only', 'Allow metadata only', 'Only document metadata and non-content hashes may be retained.', TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE),
    ('allow_derived_terms', 'Allow derived terms', 'Metadata and short derived expression observations may be retained without retaining source prose.', TRUE, FALSE, TRUE, TRUE, FALSE, FALSE, FALSE),
    ('allow_redistribution', 'Allow redistribution', 'The reviewed policy permits governed retention and redistribution, subject to the linked licence policy.', TRUE, TRUE, TRUE, TRUE, TRUE, FALSE, FALSE),
    ('manual_only', 'Manual only', 'Acquisition may proceed only through a reviewed non-automated access method.', TRUE, TRUE, TRUE, TRUE, FALSE, TRUE, FALSE),
    ('blocked', 'Blocked', 'The source is excluded from acquisition.', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE),
    ('unknown', 'Unknown', 'The source remains excluded until its acquisition and reuse status is sufficiently resolved.', FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, TRUE);

CREATE TABLE ref.robots_status (
    robots_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    automation_not_prohibited BOOLEAN NOT NULL,
    CONSTRAINT robots_status_pk PRIMARY KEY (robots_status_code),
    CONSTRAINT robots_status_nonempty_ck CHECK (
        robots_status_code = btrim(robots_status_code)
        AND robots_status_code <> ''
        AND display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
    )
);

INSERT INTO ref.robots_status VALUES
    ('allows', 'Allows', 'The reviewed target path is not disallowed by the current robots policy.', TRUE),
    ('partial_allow', 'Partial allow', 'The reviewed target path is allowed although other paths are restricted.', TRUE),
    ('absent', 'Absent', 'No robots policy was found at the checked location.', TRUE),
    ('disallows', 'Disallows', 'The reviewed target path is disallowed.', FALSE),
    ('unavailable', 'Unavailable', 'The robots policy could not be retrieved reliably.', FALSE),
    ('unknown', 'Unknown', 'Robots status has not been established.', FALSE),
    ('not_applicable', 'Not applicable', 'The reviewed access method does not make an automated web request.', TRUE);

CREATE TABLE ref.terms_status (
    terms_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    machine_access_not_prohibited BOOLEAN NOT NULL,
    CONSTRAINT terms_status_pk PRIMARY KEY (terms_status_code),
    CONSTRAINT terms_status_nonempty_ck CHECK (
        terms_status_code = btrim(terms_status_code)
        AND terms_status_code <> ''
        AND display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
    )
);

INSERT INTO ref.terms_status VALUES
    ('permits_machine_analysis', 'Permits machine analysis', 'Terms or direct permission allow the reviewed machine-analysis use.', TRUE),
    ('silent', 'Silent', 'Reviewed terms do not expressly address the scoped machine access; other rights checks still apply.', TRUE),
    ('prohibits_automation', 'Prohibits automation', 'Reviewed terms prohibit automated access.', FALSE),
    ('prohibits_reuse', 'Prohibits reuse', 'Reviewed terms prohibit the intended reuse.', FALSE),
    ('unavailable', 'Unavailable', 'Applicable terms could not be retrieved reliably.', FALSE),
    ('unknown', 'Unknown', 'Terms status has not been established.', FALSE),
    ('not_applicable', 'Not applicable', 'The reviewed source was supplied without site access.', TRUE);

CREATE TABLE ref.corpus_access_method (
    corpus_access_method_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_automated BOOLEAN NOT NULL,
    CONSTRAINT corpus_access_method_pk PRIMARY KEY (
        corpus_access_method_code
    ),
    CONSTRAINT corpus_access_method_nonempty_ck CHECK (
        corpus_access_method_code = btrim(corpus_access_method_code)
        AND corpus_access_method_code <> ''
        AND display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
    )
);

INSERT INTO ref.corpus_access_method VALUES
    ('automated_http', 'Automated HTTP', 'Rate-limited automated retrieval of a reviewed public endpoint.', TRUE),
    ('manual_browser', 'Manual browser', 'Manual review and capture without automated crawling.', FALSE),
    ('provided_snapshot', 'Provided snapshot', 'A source snapshot supplied directly for the scoped analysis.', FALSE),
    ('direct_permission', 'Direct permission', 'Material accessed under direct permission from the rights holder.', FALSE),
    ('repository_fixture', 'Repository fixture', 'Project-authored or explicitly redistributable fixture data.', FALSE);

CREATE TABLE ref.copyright_status (
    copyright_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT copyright_status_pk PRIMARY KEY (copyright_status_code),
    CONSTRAINT copyright_status_nonempty_ck CHECK (
        copyright_status_code = btrim(copyright_status_code)
        AND copyright_status_code <> ''
        AND display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
    )
);

INSERT INTO ref.copyright_status VALUES
    ('explicit_permission', 'Explicit permission', 'The intended use is covered by explicit permission or an applicable licence.'),
    ('copyright_restricted', 'Copyright restricted', 'Commercial source prose is treated as protected and non-redistributable.'),
    ('public_domain', 'Public domain', 'The reviewed material is established as public-domain material.'),
    ('project_authored', 'Project authored', 'The material is independently authored by this project.'),
    ('unknown', 'Unknown', 'Copyright status is unresolved and no reuse permission is inferred.');

CREATE TABLE ref.observation_retention (
    observation_retention_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    retains_text BOOLEAN NOT NULL,
    requires_raw_permission BOOLEAN NOT NULL,
    requires_derived_permission BOOLEAN NOT NULL,
    CONSTRAINT observation_retention_pk PRIMARY KEY (
        observation_retention_code
    ),
    CONSTRAINT observation_retention_nonempty_ck CHECK (
        observation_retention_code = btrim(observation_retention_code)
        AND observation_retention_code <> ''
        AND display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT observation_retention_permission_ck CHECK (
        NOT (requires_raw_permission AND requires_derived_permission)
    )
);

INSERT INTO ref.observation_retention VALUES
    ('full_text', 'Full text retained', 'The exact scoped observation text is retained inside its rights boundary.', TRUE, TRUE, FALSE),
    ('derived_phrase', 'Derived short phrase', 'Only a short, conservatively parsed expression phrase is retained.', TRUE, FALSE, TRUE),
    ('hash_only', 'Hash only', 'The text is redacted; only its hash, length, and non-content metadata remain.', FALSE, FALSE, FALSE);

CREATE TABLE ref.duplicate_match_basis (
    duplicate_match_basis_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    priority SMALLINT NOT NULL,
    CONSTRAINT duplicate_match_basis_pk PRIMARY KEY (
        duplicate_match_basis_code
    ),
    CONSTRAINT duplicate_match_basis_priority_uq UNIQUE (priority),
    CONSTRAINT duplicate_match_basis_nonempty_ck CHECK (
        duplicate_match_basis_code = btrim(duplicate_match_basis_code)
        AND duplicate_match_basis_code <> ''
        AND display_name = btrim(display_name)
        AND display_name <> ''
        AND description = btrim(description)
        AND description <> ''
        AND priority > 0
    )
);

INSERT INTO ref.duplicate_match_basis VALUES
    ('external_document_id', 'External document identifier', 'Stable source release identifier.', 1),
    ('canonical_url', 'Canonical URL', 'Canonical product-release URL within a frozen corpus snapshot.', 2),
    ('publisher_product_key', 'Publisher and product key', 'Same publisher product identity; this is only a candidate because historical releases remain distinct.', 3),
    ('content_hash', 'Content hash', 'Exact source-content hash.', 4),
    ('metadata_composite_hash', 'Metadata composite hash', 'Deterministic normalized product-metadata composite hash.', 5);

CREATE TABLE ref.duplicate_review_decision (
    duplicate_review_decision_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT duplicate_review_decision_pk PRIMARY KEY (
        duplicate_review_decision_code
    )
);

INSERT INTO ref.duplicate_review_decision VALUES
    ('duplicate', 'Duplicate', 'The later record duplicates the retained snapshot document.'),
    ('distinct', 'Distinct', 'The records are intentionally distinct, including a legitimate historical release.');

CREATE FUNCTION corpus.jsonb_is_string_array(input_value JSONB)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $jsonb_is_string_array$
    SELECT jsonb_typeof(input_value) = 'array'
       AND NOT EXISTS (
            SELECT 1
            FROM jsonb_array_elements(input_value) AS element(value)
            WHERE jsonb_typeof(element.value) <> 'string'
       );
$jsonb_is_string_array$;

CREATE TABLE corpus.source_policy_review (
    source_policy_review_id BIGINT GENERATED ALWAYS AS IDENTITY,
    source_policy_review_key TEXT NOT NULL,
    source_version_id BIGINT NOT NULL,
    license_policy_id BIGINT NOT NULL,
    domain TEXT NOT NULL,
    corpus_source_decision_code TEXT NOT NULL,
    robots_status_code TEXT NOT NULL,
    robots_locator TEXT,
    terms_status_code TEXT NOT NULL,
    terms_locator TEXT,
    corpus_access_method_code TEXT NOT NULL,
    copyright_status_code TEXT NOT NULL,
    document_metadata_allowed BOOLEAN NOT NULL,
    raw_retention_allowed BOOLEAN NOT NULL,
    derived_terms_allowed BOOLEAN NOT NULL,
    derived_terms_redistribution_allowed BOOLEAN NOT NULL,
    raw_redistribution_allowed BOOLEAN NOT NULL,
    automated_acquisition_allowed BOOLEAN NOT NULL,
    commercial_use_implications TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL,
    notes TEXT NOT NULL,
    CONSTRAINT source_policy_review_pk PRIMARY KEY (source_policy_review_id),
    CONSTRAINT source_policy_review_key_uq UNIQUE (source_policy_review_key),
    CONSTRAINT source_policy_review_version_fk FOREIGN KEY (source_version_id)
        REFERENCES evidence.source_version (source_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_license_fk FOREIGN KEY (license_policy_id)
        REFERENCES evidence.license_policy (license_policy_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_decision_fk FOREIGN KEY (
        corpus_source_decision_code
    ) REFERENCES ref.corpus_source_decision (corpus_source_decision_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_robots_fk FOREIGN KEY (robots_status_code)
        REFERENCES ref.robots_status (robots_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_terms_fk FOREIGN KEY (terms_status_code)
        REFERENCES ref.terms_status (terms_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_access_method_fk FOREIGN KEY (
        corpus_access_method_code
    ) REFERENCES ref.corpus_access_method (corpus_access_method_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_copyright_fk FOREIGN KEY (
        copyright_status_code
    ) REFERENCES ref.copyright_status (copyright_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_policy_review_version_domain_checked_uq UNIQUE (
        source_version_id,
        domain,
        checked_at
    ),
    CONSTRAINT source_policy_review_key_nonempty_ck CHECK (
        source_policy_review_key = btrim(source_policy_review_key)
        AND source_policy_review_key <> ''
    ),
    CONSTRAINT source_policy_review_domain_ck CHECK (
        domain = lower(btrim(domain))
        AND domain <> ''
        AND domain !~ '[/:[:space:]]'
    ),
    CONSTRAINT source_policy_review_text_nonempty_ck CHECK (
        commercial_use_implications = btrim(commercial_use_implications)
        AND commercial_use_implications <> ''
        AND notes = btrim(notes)
        AND notes <> ''
    )
);

CREATE FUNCTION corpus.enforce_source_policy_review_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_source_policy_review_semantics$
DECLARE
    decision ref.corpus_source_decision%ROWTYPE;
    robots_allows BOOLEAN;
    terms_allow BOOLEAN;
    method_is_automated BOOLEAN;
    version_license_id BIGINT;
    access_permits_raw BOOLEAN;
    policy_redistributable BOOLEAN;
    policy_derivatives BOOLEAN;
    policy_machine BOOLEAN;
    policy_export BOOLEAN;
BEGIN
    SELECT * INTO decision
    FROM ref.corpus_source_decision
    WHERE corpus_source_decision_code = NEW.corpus_source_decision_code;

    SELECT automation_not_prohibited INTO robots_allows
    FROM ref.robots_status WHERE robots_status_code = NEW.robots_status_code;
    SELECT machine_access_not_prohibited INTO terms_allow
    FROM ref.terms_status WHERE terms_status_code = NEW.terms_status_code;
    SELECT is_automated INTO method_is_automated
    FROM ref.corpus_access_method
    WHERE corpus_access_method_code = NEW.corpus_access_method_code;

    SELECT
        source_version.license_policy_id,
        access_class.permits_raw_text,
        policy.redistributable,
        policy.derivative_work_allowed,
        policy.machine_use_allowed,
        policy.production_export_allowed
    INTO
        version_license_id,
        access_permits_raw,
        policy_redistributable,
        policy_derivatives,
        policy_machine,
        policy_export
    FROM evidence.source_version AS source_version
    JOIN evidence.license_policy AS policy
      ON policy.license_policy_id = NEW.license_policy_id
    JOIN ref.access_class AS access_class
      ON access_class.access_class_code = policy.access_class_code
    WHERE source_version.source_version_id = NEW.source_version_id;

    IF version_license_id IS DISTINCT FROM NEW.license_policy_id THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_version_license_ck',
            MESSAGE = 'source_policy_review_version_license_ck: review licence must be the licence attached to its source version';
    END IF;

    IF NEW.document_metadata_allowed AND NOT decision.permits_document_metadata
       OR NEW.raw_retention_allowed AND NOT decision.permits_raw_retention
       OR NEW.derived_terms_allowed AND NOT decision.permits_derived_terms
       OR NEW.derived_terms_redistribution_allowed AND NOT decision.permits_derived_redistribution
       OR NEW.raw_redistribution_allowed AND NOT decision.permits_raw_redistribution THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_decision_ceiling_ck',
            MESSAGE = 'source_policy_review_decision_ceiling_ck: permissions exceed the controlled acquisition decision';
    END IF;

    IF NEW.raw_retention_allowed AND NOT access_permits_raw THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_raw_access_ck',
            MESSAGE = 'source_policy_review_raw_access_ck: raw retention requires an access class that permits raw text';
    END IF;
    IF NEW.derived_terms_allowed AND NOT policy_machine THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_machine_use_ck',
            MESSAGE = 'source_policy_review_machine_use_ck: derived-term analysis requires machine-use permission';
    END IF;
    IF NEW.derived_terms_redistribution_allowed
       AND NOT (NEW.derived_terms_allowed AND policy_redistributable AND policy_derivatives) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_derived_export_ck',
            MESSAGE = 'source_policy_review_derived_export_ck: derived-term redistribution requires explicit derivative and redistribution permissions';
    END IF;
    IF NEW.raw_redistribution_allowed AND NOT policy_export THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_raw_export_ck',
            MESSAGE = 'source_policy_review_raw_export_ck: raw redistribution requires production export permission';
    END IF;
    IF NEW.automated_acquisition_allowed
       AND NOT (method_is_automated AND robots_allows AND terms_allow AND policy_machine)
       OR NEW.automated_acquisition_allowed AND decision.requires_manual_access THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_automation_ck',
            MESSAGE = 'source_policy_review_automation_ck: automation requires a defensible automated method, robots/terms status, and machine-use permission';
    END IF;
    IF decision.is_blocking AND (
        NEW.document_metadata_allowed OR NEW.raw_retention_allowed
        OR NEW.derived_terms_allowed OR NEW.derived_terms_redistribution_allowed
        OR NEW.raw_redistribution_allowed OR NEW.automated_acquisition_allowed
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'source_policy_review_blocked_ck',
            MESSAGE = 'source_policy_review_blocked_ck: blocked and unknown decisions cannot grant acquisition permissions';
    END IF;
    RETURN NEW;
END;
$enforce_source_policy_review_semantics$;

CREATE TRIGGER source_policy_review_semantics_biu
BEFORE INSERT OR UPDATE ON corpus.source_policy_review
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_source_policy_review_semantics();

CREATE TABLE corpus.industry_publisher (
    industry_publisher_id BIGINT GENERATED ALWAYS AS IDENTITY,
    industry_publisher_key TEXT NOT NULL,
    source_policy_review_id BIGINT,
    external_publisher_key TEXT,
    publisher_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    roaster_country_code TEXT,
    notes TEXT,
    CONSTRAINT industry_publisher_pk PRIMARY KEY (industry_publisher_id),
    CONSTRAINT industry_publisher_key_uq UNIQUE (industry_publisher_key),
    CONSTRAINT industry_publisher_policy_fk FOREIGN KEY (source_policy_review_id)
        REFERENCES corpus.source_policy_review (source_policy_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT industry_publisher_domain_external_uq UNIQUE (
        domain,
        external_publisher_key
    ),
    CONSTRAINT industry_publisher_key_name_ck CHECK (
        industry_publisher_key = btrim(industry_publisher_key)
        AND industry_publisher_key <> ''
        AND publisher_name = btrim(publisher_name)
        AND publisher_name <> ''
    ),
    CONSTRAINT industry_publisher_domain_ck CHECK (
        domain = lower(btrim(domain)) AND domain <> ''
        AND domain !~ '[/:[:space:]]'
    ),
    CONSTRAINT industry_publisher_country_ck CHECK (
        roaster_country_code IS NULL
        OR roaster_country_code ~ '^[A-Z]{2}$'
    )
);

CREATE TABLE corpus.industry_product (
    industry_product_id BIGINT GENERATED ALWAYS AS IDENTITY,
    industry_product_key TEXT NOT NULL,
    industry_publisher_id BIGINT NOT NULL,
    external_product_key TEXT,
    product_name TEXT,
    coffee_origin_countries JSONB NOT NULL DEFAULT '[]'::JSONB,
    coffee_regions JSONB NOT NULL DEFAULT '[]'::JSONB,
    producer_names JSONB NOT NULL DEFAULT '[]'::JSONB,
    variety_names JSONB NOT NULL DEFAULT '[]'::JSONB,
    process_names JSONB NOT NULL DEFAULT '[]'::JSONB,
    notes TEXT,
    CONSTRAINT industry_product_pk PRIMARY KEY (industry_product_id),
    CONSTRAINT industry_product_key_uq UNIQUE (industry_product_key),
    CONSTRAINT industry_product_publisher_external_uq UNIQUE (
        industry_publisher_id,
        external_product_key
    ),
    CONSTRAINT industry_product_publisher_fk FOREIGN KEY (industry_publisher_id)
        REFERENCES corpus.industry_publisher (industry_publisher_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT industry_product_key_ck CHECK (
        industry_product_key = btrim(industry_product_key)
        AND industry_product_key <> ''
    ),
    CONSTRAINT industry_product_name_ck CHECK (
        product_name IS NULL OR (product_name = btrim(product_name) AND product_name <> '')
    ),
    CONSTRAINT industry_product_arrays_ck CHECK (
        corpus.jsonb_is_string_array(coffee_origin_countries)
        AND corpus.jsonb_is_string_array(coffee_regions)
        AND corpus.jsonb_is_string_array(producer_names)
        AND corpus.jsonb_is_string_array(variety_names)
        AND corpus.jsonb_is_string_array(process_names)
    )
);

COMMENT ON COLUMN corpus.industry_product.coffee_origin_countries IS
    'Explicit source assertions preserved as strings; no ISO code or geographic fact is inferred.';

CREATE TABLE corpus.sampling_frame (
    sampling_frame_id BIGINT GENERATED ALWAYS AS IDENTITY,
    sampling_frame_key TEXT NOT NULL,
    name TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    frame_sha256 TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    description TEXT NOT NULL,
    representativeness_note TEXT NOT NULL,
    CONSTRAINT sampling_frame_pk PRIMARY KEY (sampling_frame_id),
    CONSTRAINT sampling_frame_key_uq UNIQUE (sampling_frame_key),
    CONSTRAINT sampling_frame_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sampling_frame_hash_ck CHECK (frame_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT sampling_frame_text_ck CHECK (
        sampling_frame_key = btrim(sampling_frame_key) AND sampling_frame_key <> ''
        AND name = btrim(name) AND name <> ''
        AND description = btrim(description) AND description <> ''
        AND representativeness_note = btrim(representativeness_note)
        AND representativeness_note <> ''
    )
);

CREATE TABLE corpus.sampling_frame_member (
    sampling_frame_id BIGINT NOT NULL,
    industry_publisher_id BIGINT NOT NULL,
    source_policy_review_id BIGINT NOT NULL,
    selected BOOLEAN NOT NULL,
    roaster_size_stratum TEXT,
    process_focus_stratum TEXT,
    offering_period_stratum TEXT,
    selection_rationale TEXT NOT NULL,
    CONSTRAINT sampling_frame_member_pk PRIMARY KEY (
        sampling_frame_id,
        industry_publisher_id
    ),
    CONSTRAINT sampling_frame_member_frame_fk FOREIGN KEY (sampling_frame_id)
        REFERENCES corpus.sampling_frame (sampling_frame_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sampling_frame_member_publisher_fk FOREIGN KEY (industry_publisher_id)
        REFERENCES corpus.industry_publisher (industry_publisher_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sampling_frame_member_policy_fk FOREIGN KEY (source_policy_review_id)
        REFERENCES corpus.source_policy_review (source_policy_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT sampling_frame_member_rationale_ck CHECK (
        selection_rationale = btrim(selection_rationale)
        AND selection_rationale <> ''
    )
);

CREATE TABLE corpus.normalization_pipeline (
    normalization_pipeline_id BIGINT GENERATED ALWAYS AS IDENTITY,
    normalization_pipeline_key TEXT NOT NULL,
    version_label TEXT NOT NULL,
    language_tag_code TEXT NOT NULL,
    unicode_form TEXT NOT NULL DEFAULT 'NFC',
    rules_sha256 TEXT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    frozen_at TIMESTAMPTZ,
    CONSTRAINT normalization_pipeline_pk PRIMARY KEY (normalization_pipeline_id),
    CONSTRAINT normalization_pipeline_key_uq UNIQUE (normalization_pipeline_key),
    CONSTRAINT normalization_pipeline_version_uq UNIQUE (
        version_label,
        language_tag_code
    ),
    CONSTRAINT normalization_pipeline_language_fk FOREIGN KEY (language_tag_code)
        REFERENCES ref.language_tag (language_tag_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT normalization_pipeline_key_ck CHECK (
        normalization_pipeline_key = btrim(normalization_pipeline_key)
        AND normalization_pipeline_key <> ''
        AND version_label = btrim(version_label) AND version_label <> ''
        AND parser_version = btrim(parser_version) AND parser_version <> ''
        AND description = btrim(description) AND description <> ''
    ),
    CONSTRAINT normalization_pipeline_unicode_ck CHECK (unicode_form = 'NFC'),
    CONSTRAINT normalization_pipeline_rules_hash_ck CHECK (
        rules_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT normalization_pipeline_commit_ck CHECK (
        code_commit_sha ~ '^[0-9a-f]{40}$' OR code_commit_sha ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT normalization_pipeline_time_ck CHECK (
        frozen_at IS NULL OR frozen_at >= created_at
    )
);

CREATE TABLE corpus.corpus_snapshot (
    corpus_snapshot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    corpus_snapshot_key TEXT NOT NULL,
    corpus_id BIGINT NOT NULL,
    corpus_version TEXT NOT NULL,
    manifest_dataset_id BIGINT NOT NULL,
    sampling_frame_id BIGINT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    capture_window_start TIMESTAMPTZ NOT NULL,
    capture_window_end TIMESTAMPTZ NOT NULL,
    source_inventory_sha256 TEXT NOT NULL,
    document_inventory_sha256 TEXT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    expected_document_count BIGINT NOT NULL,
    expected_observation_count BIGINT NOT NULL,
    expected_normalized_expression_count BIGINT NOT NULL,
    raw_public_reproducibility_complete BOOLEAN NOT NULL,
    reproducibility_boundary TEXT NOT NULL,
    frozen_at TIMESTAMPTZ,
    CONSTRAINT corpus_snapshot_pk PRIMARY KEY (corpus_snapshot_id),
    CONSTRAINT corpus_snapshot_key_uq UNIQUE (corpus_snapshot_key),
    CONSTRAINT corpus_snapshot_corpus_uq UNIQUE (corpus_id),
    CONSTRAINT corpus_snapshot_version_uq UNIQUE (corpus_version),
    CONSTRAINT corpus_snapshot_corpus_fk FOREIGN KEY (corpus_id)
        REFERENCES corpus.corpus (corpus_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_dataset_fk FOREIGN KEY (manifest_dataset_id)
        REFERENCES evidence.dataset (dataset_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_frame_fk FOREIGN KEY (sampling_frame_id)
        REFERENCES corpus.sampling_frame (sampling_frame_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_pipeline_fk FOREIGN KEY (normalization_pipeline_id)
        REFERENCES corpus.normalization_pipeline (normalization_pipeline_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_window_ck CHECK (
        capture_window_end >= capture_window_start
    ),
    CONSTRAINT corpus_snapshot_hashes_ck CHECK (
        source_inventory_sha256 ~ '^[0-9a-f]{64}$'
        AND document_inventory_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT corpus_snapshot_commit_ck CHECK (
        code_commit_sha ~ '^[0-9a-f]{40}$' OR code_commit_sha ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT corpus_snapshot_counts_ck CHECK (
        expected_document_count >= 0
        AND expected_observation_count >= 0
        AND expected_normalized_expression_count >= 0
    ),
    CONSTRAINT corpus_snapshot_boundary_ck CHECK (
        reproducibility_boundary = btrim(reproducibility_boundary)
        AND reproducibility_boundary <> ''
    )
);

CREATE TABLE corpus.corpus_snapshot_source (
    corpus_snapshot_id BIGINT NOT NULL,
    industry_publisher_id BIGINT NOT NULL,
    source_policy_review_id BIGINT NOT NULL,
    source_ordinal INTEGER NOT NULL,
    sampling_stratum TEXT NOT NULL,
    inclusion_note TEXT NOT NULL,
    CONSTRAINT corpus_snapshot_source_pk PRIMARY KEY (
        corpus_snapshot_id,
        industry_publisher_id
    ),
    CONSTRAINT corpus_snapshot_source_ordinal_uq UNIQUE (
        corpus_snapshot_id,
        source_ordinal
    ),
    CONSTRAINT corpus_snapshot_source_snapshot_fk FOREIGN KEY (corpus_snapshot_id)
        REFERENCES corpus.corpus_snapshot (corpus_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_source_publisher_fk FOREIGN KEY (industry_publisher_id)
        REFERENCES corpus.industry_publisher (industry_publisher_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_source_policy_fk FOREIGN KEY (source_policy_review_id)
        REFERENCES corpus.source_policy_review (source_policy_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT corpus_snapshot_source_text_ck CHECK (
        source_ordinal > 0
        AND sampling_stratum = btrim(sampling_stratum) AND sampling_stratum <> ''
        AND inclusion_note = btrim(inclusion_note) AND inclusion_note <> ''
    )
);

CREATE TABLE corpus.acquisition_batch (
    acquisition_batch_id BIGINT GENERATED ALWAYS AS IDENTITY,
    acquisition_batch_key TEXT NOT NULL,
    corpus_snapshot_id BIGINT NOT NULL,
    batch_ordinal INTEGER NOT NULL,
    captured_from TIMESTAMPTZ NOT NULL,
    captured_until TIMESTAMPTZ NOT NULL,
    batch_inventory_sha256 TEXT NOT NULL,
    expected_document_count BIGINT NOT NULL,
    notes TEXT NOT NULL,
    CONSTRAINT acquisition_batch_pk PRIMARY KEY (acquisition_batch_id),
    CONSTRAINT acquisition_batch_key_uq UNIQUE (acquisition_batch_key),
    CONSTRAINT acquisition_batch_snapshot_ordinal_uq UNIQUE (
        corpus_snapshot_id,
        batch_ordinal
    ),
    CONSTRAINT acquisition_batch_snapshot_fk FOREIGN KEY (corpus_snapshot_id)
        REFERENCES corpus.corpus_snapshot (corpus_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT acquisition_batch_window_ck CHECK (captured_until >= captured_from),
    CONSTRAINT acquisition_batch_hash_ck CHECK (
        batch_inventory_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT acquisition_batch_values_ck CHECK (
        batch_ordinal > 0 AND expected_document_count >= 0
        AND acquisition_batch_key = btrim(acquisition_batch_key)
        AND acquisition_batch_key <> ''
        AND notes = btrim(notes) AND notes <> ''
    )
);

ALTER TABLE corpus.captured_document
    ALTER COLUMN raw_text DROP NOT NULL,
    ADD COLUMN industry_product_id BIGINT,
    ADD COLUMN source_policy_review_id BIGINT,
    ADD COLUMN acquisition_batch_id BIGINT,
    ADD COLUMN canonical_url TEXT,
    ADD COLUMN content_sha256 TEXT,
    ADD COLUMN raw_text_sha256 TEXT,
    ADD COLUMN metadata_composite_sha256 TEXT,
    ADD COLUMN listing_observed_on DATE,
    ADD COLUMN roast_date DATE,
    ADD CONSTRAINT captured_document_product_fk FOREIGN KEY (industry_product_id)
        REFERENCES corpus.industry_product (industry_product_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT captured_document_policy_review_fk FOREIGN KEY (source_policy_review_id)
        REFERENCES corpus.source_policy_review (source_policy_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT captured_document_batch_fk FOREIGN KEY (acquisition_batch_id)
        REFERENCES corpus.acquisition_batch (acquisition_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT captured_document_url_ck CHECK (
        canonical_url IS NULL OR (canonical_url = btrim(canonical_url) AND canonical_url <> '')
    ),
    ADD CONSTRAINT captured_document_hashes_ck CHECK (
        (content_sha256 IS NULL OR content_sha256 ~ '^[0-9a-f]{64}$')
        AND (raw_text_sha256 IS NULL OR raw_text_sha256 ~ '^[0-9a-f]{64}$')
        AND (metadata_composite_sha256 IS NULL OR metadata_composite_sha256 ~ '^[0-9a-f]{64}$')
    );

UPDATE corpus.captured_document
SET raw_text_sha256 = encode(sha256(convert_to(raw_text, 'UTF8')), 'hex')
WHERE raw_text IS NOT NULL
  AND raw_text_sha256 IS NULL;

ALTER TABLE corpus.captured_document
    ADD CONSTRAINT captured_document_raw_text_receipt_ck CHECK (
        raw_text IS NULL OR raw_text_sha256 IS NOT NULL
    );

ALTER TABLE corpus.raw_observation
    ALTER COLUMN observation_text DROP NOT NULL,
    ADD COLUMN observation_sha256 TEXT,
    ADD COLUMN character_count INTEGER,
    ADD COLUMN observation_retention_code TEXT,
    ADD CONSTRAINT raw_observation_retention_fk FOREIGN KEY (observation_retention_code)
        REFERENCES ref.observation_retention (observation_retention_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ADD CONSTRAINT raw_observation_hash_ck CHECK (
        observation_sha256 IS NULL OR observation_sha256 ~ '^[0-9a-f]{64}$'
    ),
    ADD CONSTRAINT raw_observation_character_count_ck CHECK (
        character_count IS NULL OR character_count > 0
    );

UPDATE corpus.raw_observation
SET
    observation_sha256 = encode(
        sha256(convert_to(observation_text, 'UTF8')),
        'hex'
    ),
    character_count = char_length(observation_text),
    observation_retention_code = 'full_text'
WHERE observation_text IS NOT NULL
  AND observation_retention_code IS NULL;

ALTER TABLE corpus.raw_observation
    ADD CONSTRAINT raw_observation_text_retention_ck CHECK (
        observation_retention_code IS NULL
        OR observation_retention_code = 'hash_only' AND observation_text IS NULL
        OR observation_retention_code IN ('full_text', 'derived_phrase')
           AND observation_text IS NOT NULL
    ),
    ADD CONSTRAINT raw_observation_text_length_ck CHECK (
        observation_retention_code IS NULL
        OR observation_text IS NULL
        OR character_count = char_length(observation_text)
    ),
    ADD CONSTRAINT raw_observation_derived_phrase_length_ck CHECK (
        observation_retention_code <> 'derived_phrase'
        OR character_count <= 80
    );

CREATE FUNCTION corpus.enforce_snapshot_document_policy()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_snapshot_document_policy$
DECLARE
    snapshot_id BIGINT;
    snapshot_start TIMESTAMPTZ;
    snapshot_end TIMESTAMPTZ;
    batch_snapshot_id BIGINT;
    review_source_version_id BIGINT;
    metadata_allowed BOOLEAN;
    raw_allowed BOOLEAN;
    publisher_id BIGINT;
    inherited_review_id BIGINT;
BEGIN
    SELECT corpus_snapshot_id, capture_window_start, capture_window_end
    INTO snapshot_id, snapshot_start, snapshot_end
    FROM corpus.corpus_snapshot WHERE corpus_id = NEW.corpus_id;
    IF NOT FOUND THEN RETURN NEW; END IF;

    IF num_nonnulls(NEW.industry_product_id, NEW.source_policy_review_id,
                    NEW.acquisition_batch_id, NEW.content_sha256,
                    NEW.raw_text_sha256) <> 5 THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_snapshot_metadata_ck',
            MESSAGE = 'captured_document_snapshot_metadata_ck: snapshot documents require product, policy, batch, content hash, and raw-source hash; URL remains nullable when absent';
    END IF;
    IF NEW.external_document_key IS NULL AND NEW.canonical_url IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_stable_identity_ck',
            MESSAGE = 'captured_document_stable_identity_ck: snapshot documents require an external release identifier or canonical URL';
    END IF;

    SELECT source_version_id, document_metadata_allowed, raw_retention_allowed
    INTO review_source_version_id, metadata_allowed, raw_allowed
    FROM corpus.source_policy_review
    WHERE source_policy_review_id = NEW.source_policy_review_id;
    IF review_source_version_id IS DISTINCT FROM NEW.source_version_id OR NOT metadata_allowed THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_source_policy_ck',
            MESSAGE = 'captured_document_source_policy_ck: document source version must match a metadata-permitting policy review';
    END IF;
    IF NEW.raw_text IS NOT NULL AND NOT raw_allowed THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_raw_retention_ck',
            MESSAGE = 'captured_document_raw_retention_ck: source policy forbids retaining raw document text';
    END IF;

    SELECT batch.corpus_snapshot_id INTO batch_snapshot_id
    FROM corpus.acquisition_batch AS batch
    WHERE batch.acquisition_batch_id = NEW.acquisition_batch_id;
    IF batch_snapshot_id IS DISTINCT FROM snapshot_id
       OR NEW.captured_at < snapshot_start OR NEW.captured_at > snapshot_end THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_snapshot_batch_ck',
            MESSAGE = 'captured_document_snapshot_batch_ck: acquisition batch and capture time must belong to the document snapshot';
    END IF;

    SELECT product.industry_publisher_id, publisher.source_policy_review_id
    INTO publisher_id, inherited_review_id
    FROM corpus.industry_product AS product
    JOIN corpus.industry_publisher AS publisher
      ON publisher.industry_publisher_id = product.industry_publisher_id
    WHERE product.industry_product_id = NEW.industry_product_id;
    IF inherited_review_id IS NOT NULL
       AND inherited_review_id <> NEW.source_policy_review_id THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_inherited_policy_ck',
            MESSAGE = 'captured_document_inherited_policy_ck: document policy must equal the publisher inherited policy';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM corpus.corpus_snapshot_source AS member
        WHERE member.corpus_snapshot_id = snapshot_id
          AND member.industry_publisher_id = publisher_id
          AND member.source_policy_review_id = NEW.source_policy_review_id
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'captured_document_snapshot_source_ck',
            MESSAGE = 'captured_document_snapshot_source_ck: publisher and policy must be declared snapshot sources';
    END IF;
    RETURN NEW;
END;
$enforce_snapshot_document_policy$;

CREATE TRIGGER captured_document_snapshot_policy_biu
BEFORE INSERT OR UPDATE ON corpus.captured_document
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_snapshot_document_policy();

CREATE FUNCTION corpus.enforce_snapshot_observation_policy()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_snapshot_observation_policy$
DECLARE
    snapshot_id BIGINT;
    raw_allowed BOOLEAN;
    derived_allowed BOOLEAN;
BEGIN
    SELECT snapshot.corpus_snapshot_id, policy.raw_retention_allowed,
           policy.derived_terms_allowed
    INTO snapshot_id, raw_allowed, derived_allowed
    FROM corpus.captured_document AS document
    JOIN corpus.corpus_snapshot AS snapshot ON snapshot.corpus_id = document.corpus_id
    JOIN corpus.source_policy_review AS policy
      ON policy.source_policy_review_id = document.source_policy_review_id
    WHERE document.captured_document_id = NEW.captured_document_id;
    IF NOT FOUND THEN RETURN NEW; END IF;

    IF num_nonnulls(NEW.observation_sha256, NEW.character_count,
                    NEW.observation_retention_code) <> 3 THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'raw_observation_snapshot_receipt_ck',
            MESSAGE = 'raw_observation_snapshot_receipt_ck: snapshot observations require hash, original character count, and retention disposition';
    END IF;
    IF NEW.observation_retention_code = 'full_text' AND NOT raw_allowed
       OR NEW.observation_retention_code = 'derived_phrase' AND NOT derived_allowed THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'raw_observation_policy_ck',
            MESSAGE = 'raw_observation_policy_ck: observation retention exceeds the source policy';
    END IF;
    RETURN NEW;
END;
$enforce_snapshot_observation_policy$;

CREATE TRIGGER raw_observation_snapshot_policy_biu
BEFORE INSERT OR UPDATE ON corpus.raw_observation
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_snapshot_observation_policy();

CREATE FUNCTION corpus.enforce_snapshot_expression_policy()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_snapshot_expression_policy$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.raw_observation AS observation
        JOIN corpus.captured_document AS document
          ON document.captured_document_id = observation.captured_document_id
        JOIN corpus.corpus_snapshot AS snapshot ON snapshot.corpus_id = document.corpus_id
        JOIN corpus.source_policy_review AS policy
          ON policy.source_policy_review_id = document.source_policy_review_id
        WHERE observation.raw_observation_id = NEW.raw_observation_id
          AND NOT policy.derived_terms_allowed
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'observation_expression_derived_terms_ck',
            MESSAGE = 'observation_expression_derived_terms_ck: source policy forbids retaining derived expressions';
    END IF;
    RETURN NEW;
END;
$enforce_snapshot_expression_policy$;

CREATE TRIGGER observation_expression_snapshot_policy_biu
BEFORE INSERT OR UPDATE ON corpus.observation_expression
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_snapshot_expression_policy();

CREATE UNIQUE INDEX captured_document_external_release_uq
    ON corpus.captured_document (corpus_id, source_version_id, external_document_key)
    WHERE external_document_key IS NOT NULL;
CREATE UNIQUE INDEX captured_document_canonical_url_uq
    ON corpus.captured_document (corpus_id, canonical_url)
    WHERE canonical_url IS NOT NULL;
CREATE INDEX captured_document_product_history_idx
    ON corpus.captured_document (industry_product_id, captured_at, captured_document_id)
    WHERE industry_product_id IS NOT NULL;
CREATE INDEX captured_document_content_hash_idx
    ON corpus.captured_document (corpus_id, content_sha256)
    WHERE content_sha256 IS NOT NULL;
CREATE INDEX captured_document_metadata_hash_idx
    ON corpus.captured_document (corpus_id, metadata_composite_sha256)
    WHERE metadata_composite_sha256 IS NOT NULL;

CREATE VIEW corpus.v_document_duplicate_candidates AS
WITH candidate_pairs AS (
    SELECT
        left_document.captured_document_id AS earlier_document_id,
        right_document.captured_document_id AS later_document_id,
        'publisher_product_key'::TEXT AS duplicate_match_basis_code
    FROM corpus.captured_document AS left_document
    JOIN corpus.captured_document AS right_document
      ON right_document.corpus_id = left_document.corpus_id
     AND right_document.industry_product_id = left_document.industry_product_id
     AND right_document.captured_document_id > left_document.captured_document_id
    WHERE left_document.industry_product_id IS NOT NULL
    UNION ALL
    SELECT left_document.captured_document_id, right_document.captured_document_id,
           'content_hash'::TEXT
    FROM corpus.captured_document AS left_document
    JOIN corpus.captured_document AS right_document
      ON right_document.corpus_id = left_document.corpus_id
     AND right_document.content_sha256 = left_document.content_sha256
     AND right_document.captured_document_id > left_document.captured_document_id
    WHERE left_document.content_sha256 IS NOT NULL
    UNION ALL
    SELECT left_document.captured_document_id, right_document.captured_document_id,
           'metadata_composite_hash'::TEXT
    FROM corpus.captured_document AS left_document
    JOIN corpus.captured_document AS right_document
      ON right_document.corpus_id = left_document.corpus_id
     AND right_document.metadata_composite_sha256 = left_document.metadata_composite_sha256
     AND right_document.captured_document_id > left_document.captured_document_id
    WHERE left_document.metadata_composite_sha256 IS NOT NULL
), ranked AS (
    SELECT candidate_pairs.*,
           row_number() OVER (
               PARTITION BY earlier_document_id, later_document_id
               ORDER BY basis.priority
           ) AS basis_rank
    FROM candidate_pairs
    JOIN ref.duplicate_match_basis AS basis
      ON basis.duplicate_match_basis_code = candidate_pairs.duplicate_match_basis_code
)
SELECT earlier_document_id, later_document_id, duplicate_match_basis_code
FROM ranked WHERE basis_rank = 1;

COMMENT ON VIEW corpus.v_document_duplicate_candidates IS
    'Ordered duplicate candidates within one snapshot corpus. A shared product identity is reviewable because historical releases must remain distinct.';

CREATE TABLE corpus.document_duplicate_review (
    document_duplicate_review_id BIGINT GENERATED ALWAYS AS IDENTITY,
    document_duplicate_review_key TEXT NOT NULL,
    earlier_document_id BIGINT NOT NULL,
    later_document_id BIGINT NOT NULL,
    duplicate_match_basis_code TEXT NOT NULL,
    duplicate_review_decision_code TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL,
    rationale TEXT NOT NULL,
    CONSTRAINT document_duplicate_review_pk PRIMARY KEY (
        document_duplicate_review_id
    ),
    CONSTRAINT document_duplicate_review_key_uq UNIQUE (
        document_duplicate_review_key
    ),
    CONSTRAINT document_duplicate_review_pair_uq UNIQUE (
        earlier_document_id,
        later_document_id
    ),
    CONSTRAINT document_duplicate_review_earlier_fk FOREIGN KEY (earlier_document_id)
        REFERENCES corpus.captured_document (captured_document_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT document_duplicate_review_later_fk FOREIGN KEY (later_document_id)
        REFERENCES corpus.captured_document (captured_document_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT document_duplicate_review_basis_fk FOREIGN KEY (
        duplicate_match_basis_code
    ) REFERENCES ref.duplicate_match_basis (duplicate_match_basis_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT document_duplicate_review_decision_fk FOREIGN KEY (
        duplicate_review_decision_code
    ) REFERENCES ref.duplicate_review_decision (duplicate_review_decision_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT document_duplicate_review_order_ck CHECK (
        earlier_document_id < later_document_id
    ),
    CONSTRAINT document_duplicate_review_text_ck CHECK (
        document_duplicate_review_key = btrim(document_duplicate_review_key)
        AND document_duplicate_review_key <> ''
        AND rationale = btrim(rationale) AND rationale <> ''
    )
);

CREATE FUNCTION corpus.enforce_duplicate_review_semantics()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $enforce_duplicate_review_semantics$
DECLARE earlier_corpus BIGINT; later_corpus BIGINT;
BEGIN
    SELECT corpus_id INTO earlier_corpus FROM corpus.captured_document
    WHERE captured_document_id = NEW.earlier_document_id;
    SELECT corpus_id INTO later_corpus FROM corpus.captured_document
    WHERE captured_document_id = NEW.later_document_id;
    IF earlier_corpus IS DISTINCT FROM later_corpus THEN
        RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'document_duplicate_review_same_snapshot_ck',
            MESSAGE = 'document_duplicate_review_same_snapshot_ck: duplicate review endpoints must belong to the same corpus snapshot';
    END IF;
    RETURN NEW;
END;
$enforce_duplicate_review_semantics$;

CREATE TRIGGER document_duplicate_review_semantics_biu
BEFORE INSERT OR UPDATE ON corpus.document_duplicate_review
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_duplicate_review_semantics();

CREATE FUNCTION corpus.guard_frozen_snapshot()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $guard_frozen_snapshot$
BEGIN
    IF TG_OP <> 'INSERT' AND OLD.frozen_at IS NOT NULL THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'frozen corpus snapshots are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF NEW.frozen_at IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM corpus.normalization_pipeline AS pipeline
            WHERE pipeline.normalization_pipeline_id = NEW.normalization_pipeline_id
              AND pipeline.frozen_at IS NOT NULL
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'corpus_snapshot_frozen_pipeline_ck',
                MESSAGE = 'corpus_snapshot_frozen_pipeline_ck: a snapshot requires a frozen normalization pipeline';
        END IF;
        IF NEW.expected_document_count <> (
            SELECT count(*) FROM corpus.captured_document
            WHERE corpus_id = NEW.corpus_id
        ) OR NEW.expected_observation_count <> (
            SELECT count(*) FROM corpus.raw_observation AS observation
            JOIN corpus.captured_document AS document
              ON document.captured_document_id = observation.captured_document_id
            WHERE document.corpus_id = NEW.corpus_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'corpus_snapshot_frozen_counts_ck',
                MESSAGE = 'corpus_snapshot_frozen_counts_ck: declared document or observation count does not match stored rows';
        END IF;
        IF EXISTS (
            SELECT 1 FROM corpus.v_document_duplicate_candidates AS candidate
            JOIN corpus.captured_document AS document
              ON document.captured_document_id = candidate.earlier_document_id
            WHERE document.corpus_id = NEW.corpus_id
              AND NOT EXISTS (
                  SELECT 1 FROM corpus.document_duplicate_review AS review
                  WHERE review.earlier_document_id = candidate.earlier_document_id
                    AND review.later_document_id = candidate.later_document_id
              )
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514', CONSTRAINT = 'corpus_snapshot_duplicate_review_ck',
                MESSAGE = 'corpus_snapshot_duplicate_review_ck: every duplicate candidate must be reviewed before snapshot freeze';
        END IF;
    END IF;
    RETURN NEW;
END;
$guard_frozen_snapshot$;

CREATE TRIGGER corpus_snapshot_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.corpus_snapshot
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot();

CREATE FUNCTION corpus.guard_frozen_pipeline()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $guard_frozen_pipeline$
BEGIN
    IF OLD.frozen_at IS NOT NULL THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'frozen normalization pipelines are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$guard_frozen_pipeline$;

CREATE TRIGGER normalization_pipeline_immutable_bud
BEFORE UPDATE OR DELETE ON corpus.normalization_pipeline
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_pipeline();

CREATE FUNCTION corpus.guard_frozen_snapshot_member()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $guard_frozen_snapshot_member$
DECLARE
    old_snapshot_id BIGINT;
    new_snapshot_id BIGINT;
    is_frozen BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'corpus_snapshot_source' THEN
        IF TG_OP <> 'INSERT' THEN
            old_snapshot_id := OLD.corpus_snapshot_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_snapshot_id := NEW.corpus_snapshot_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'acquisition_batch' THEN
        IF TG_OP <> 'INSERT' THEN
            old_snapshot_id := OLD.corpus_snapshot_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_snapshot_id := NEW.corpus_snapshot_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'captured_document' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT corpus_snapshot_id INTO old_snapshot_id
            FROM corpus.corpus_snapshot
            WHERE corpus_id = OLD.corpus_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT corpus_snapshot_id INTO new_snapshot_id
            FROM corpus.corpus_snapshot
            WHERE corpus_id = NEW.corpus_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'raw_observation' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT snapshot.corpus_snapshot_id INTO old_snapshot_id
            FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE document.captured_document_id = OLD.captured_document_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT snapshot.corpus_snapshot_id INTO new_snapshot_id
            FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE document.captured_document_id = NEW.captured_document_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'observation_expression' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT snapshot.corpus_snapshot_id INTO old_snapshot_id
            FROM corpus.raw_observation AS observation
            JOIN corpus.captured_document AS document
              ON document.captured_document_id = observation.captured_document_id
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE observation.raw_observation_id = OLD.raw_observation_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT snapshot.corpus_snapshot_id INTO new_snapshot_id
            FROM corpus.raw_observation AS observation
            JOIN corpus.captured_document AS document
              ON document.captured_document_id = observation.captured_document_id
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE observation.raw_observation_id = NEW.raw_observation_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'document_duplicate_review' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT snapshot.corpus_snapshot_id INTO old_snapshot_id
            FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE document.captured_document_id = OLD.earlier_document_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT snapshot.corpus_snapshot_id INTO new_snapshot_id
            FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_id = document.corpus_id
            WHERE document.captured_document_id = NEW.earlier_document_id;
        END IF;
    END IF;
    SELECT EXISTS (
        SELECT 1
        FROM corpus.corpus_snapshot AS snapshot
        WHERE snapshot.frozen_at IS NOT NULL
          AND snapshot.corpus_snapshot_id IN (
              old_snapshot_id,
              new_snapshot_id
          )
    ) INTO is_frozen;
    IF COALESCE(is_frozen, FALSE) THEN
        RAISE EXCEPTION USING ERRCODE = '55000', MESSAGE = 'members of a frozen corpus snapshot are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$guard_frozen_snapshot_member$;

CREATE TRIGGER corpus_snapshot_source_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.corpus_snapshot_source
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot_member();
CREATE TRIGGER acquisition_batch_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.acquisition_batch
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot_member();
CREATE TRIGGER captured_document_snapshot_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.captured_document
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot_member();
CREATE TRIGGER raw_observation_snapshot_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.raw_observation
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot_member();
CREATE TRIGGER observation_expression_snapshot_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.observation_expression
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot_member();
CREATE TRIGGER document_duplicate_review_immutable_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.document_duplicate_review
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_snapshot_member();

CREATE FUNCTION corpus.guard_frozen_governance_row()
RETURNS TRIGGER LANGUAGE plpgsql SET search_path = pg_catalog
AS $guard_frozen_governance_row$
DECLARE
    row_is_referenced BOOLEAN := FALSE;
    new_row_is_referenced BOOLEAN := FALSE;
BEGIN
    IF TG_TABLE_NAME = 'source_policy_review' THEN
        SELECT EXISTS (
            SELECT 1 FROM corpus.corpus_snapshot_source AS member
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_snapshot_id = member.corpus_snapshot_id
            WHERE member.source_policy_review_id = OLD.source_policy_review_id
              AND snapshot.frozen_at IS NOT NULL
        ) INTO row_is_referenced;
    ELSIF TG_TABLE_NAME = 'industry_publisher' THEN
        SELECT EXISTS (
            SELECT 1 FROM corpus.corpus_snapshot_source AS member
            JOIN corpus.corpus_snapshot AS snapshot
              ON snapshot.corpus_snapshot_id = member.corpus_snapshot_id
            WHERE member.industry_publisher_id = OLD.industry_publisher_id
              AND snapshot.frozen_at IS NOT NULL
        ) INTO row_is_referenced;
    ELSIF TG_TABLE_NAME = 'industry_product' THEN
        SELECT EXISTS (
            SELECT 1 FROM corpus.captured_document AS document
            JOIN corpus.corpus_snapshot AS snapshot ON snapshot.corpus_id = document.corpus_id
            WHERE document.industry_product_id = OLD.industry_product_id
              AND snapshot.frozen_at IS NOT NULL
        ) INTO row_is_referenced;
    ELSIF TG_TABLE_NAME = 'sampling_frame' THEN
        SELECT EXISTS (
            SELECT 1 FROM corpus.corpus_snapshot AS snapshot
            WHERE snapshot.sampling_frame_id = OLD.sampling_frame_id
              AND snapshot.frozen_at IS NOT NULL
        ) INTO row_is_referenced;
    ELSIF TG_TABLE_NAME = 'sampling_frame_member' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT EXISTS (
                SELECT 1 FROM corpus.corpus_snapshot AS snapshot
                WHERE snapshot.sampling_frame_id = OLD.sampling_frame_id
                  AND snapshot.frozen_at IS NOT NULL
            ) INTO row_is_referenced;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT EXISTS (
                SELECT 1 FROM corpus.corpus_snapshot AS snapshot
                WHERE snapshot.sampling_frame_id = NEW.sampling_frame_id
                  AND snapshot.frozen_at IS NOT NULL
            ) INTO new_row_is_referenced;
        END IF;
    END IF;
    IF row_is_referenced OR new_row_is_referenced THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'governance rows referenced by a frozen corpus snapshot are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$guard_frozen_governance_row$;

CREATE TRIGGER source_policy_review_frozen_guard_bud
BEFORE UPDATE OR DELETE ON corpus.source_policy_review
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_governance_row();
CREATE TRIGGER industry_publisher_frozen_guard_bud
BEFORE UPDATE OR DELETE ON corpus.industry_publisher
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_governance_row();
CREATE TRIGGER industry_product_frozen_guard_bud
BEFORE UPDATE OR DELETE ON corpus.industry_product
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_governance_row();
CREATE TRIGGER sampling_frame_frozen_guard_bud
BEFORE UPDATE OR DELETE ON corpus.sampling_frame
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_governance_row();
CREATE TRIGGER sampling_frame_member_frozen_guard_bud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.sampling_frame_member
FOR EACH ROW EXECUTE FUNCTION corpus.guard_frozen_governance_row();

COMMENT ON TABLE corpus.source_policy_review IS
    'Immutable-at-snapshot acquisition decision distinct from publisher identity; one domain review may govern many publishers.';
COMMENT ON TABLE corpus.corpus_snapshot IS
    'Frozen version identity for a corpus capture. It is never a mutable corpus named current.';
COMMENT ON TABLE corpus.industry_product IS
    'Stable industry product identity; multiple captured releases may reference one product and remain historical.';
COMMENT ON COLUMN corpus.captured_document.raw_text IS
    'Optional restricted raw text. NULL plus hashes is the default repository-safe representation.';
COMMENT ON COLUMN corpus.raw_observation.observation_text IS
    'Optional source observation or short derived phrase; hash-only redaction retains no protected prose.';

COMMIT;
