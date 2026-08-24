\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- forward provenance refinement
-- Existing concept support already resolves to an immutable source version,
-- directly or through a dataset. This migration makes the semantic role of
-- that support normalized and queryable without inventing a role for legacy
-- rows or storing copied source definitions.

BEGIN;

CREATE TABLE ref.concept_support_role (
    concept_support_role_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT concept_support_role_pk PRIMARY KEY (
        concept_support_role_code
    ),
    CONSTRAINT concept_support_role_code_nonempty_ck CHECK (
        concept_support_role_code = btrim(concept_support_role_code)
        AND concept_support_role_code <> ''
    ),
    CONSTRAINT concept_support_role_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT concept_support_role_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.concept_support_role IS
    'Controlled meaning of a versioned evidence.concept_support assertion; roles describe provenance without copying source definitions.';

INSERT INTO ref.concept_support_role (
    concept_support_role_code,
    display_name,
    description
)
VALUES
    (
        'legacy_unspecified',
        'Legacy unspecified',
        'A support row created before controlled support roles existed; no more specific provenance meaning has been asserted.'
    ),
    (
        'project_authorship',
        'Project authorship',
        'Identifies the fixed project source version in which independently authored concept scope was recorded.'
    ),
    (
        'lexicon_inclusion',
        'Lexicon inclusion',
        'Records that the identified source version includes a corresponding sensory or terminology entry without importing its definition.'
    ),
    (
        'reported_usage',
        'Reported usage',
        'Records source-version evidence that a concept is used in a declared context, without treating frequency as sensory truth.'
    ),
    (
        'empirical_observation',
        'Empirical observation',
        'Connects concept scope to an identified dataset observation while leaving measured values in empirical measurement tables.'
    ),
    (
        'scope_basis',
        'Scope basis',
        'Identifies evidence considered when independently defining the project concept boundary; it does not copy a source definition.'
    ),
    (
        'regional_extension',
        'Regional extension',
        'Records evidence for region- or culture-specific extension of concept coverage without claiming universal equivalence.'
    ),
    (
        'interpretive',
        'Interpretive',
        'Marks a documented project interpretation of versioned source material rather than a direct source assertion.'
    ),
    (
        'corroboration',
        'Corroboration',
        'Identifies independent supporting evidence that corroborates an existing project concept scope.'
    );

ALTER TABLE evidence.concept_support
    ADD COLUMN concept_support_role_code TEXT NOT NULL
        DEFAULT 'legacy_unspecified';

-- No existing free-text note is interpreted automatically. Every pre-role
-- support record is backfilled by ADD COLUMN into the explicit uncertainty
-- bucket. The default is removed immediately so every future support insert
-- must choose its role deliberately.

ALTER TABLE evidence.concept_support
    ALTER COLUMN concept_support_role_code DROP DEFAULT,
    ADD CONSTRAINT concept_support_role_fk
        FOREIGN KEY (concept_support_role_code)
        REFERENCES ref.concept_support_role (concept_support_role_code)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT;

COMMENT ON COLUMN evidence.concept_support.concept_support_role_code IS
    'Controlled provenance role for this exact concept-to-source-version or concept-to-dataset support assertion.';

CREATE INDEX concept_support_concept_role_idx
    ON evidence.concept_support (
        concept_id,
        concept_support_role_code,
        concept_support_id
    );

COMMENT ON INDEX evidence.concept_support_concept_role_idx IS
    'Supports concept-first provenance review grouped by controlled support role.';

CREATE VIEW evidence.v_concept_provenance AS
SELECT
    concept.concept_id,
    concept.concept_key,
    concept.concept_type_code,
    concept.lifecycle_status_code AS concept_lifecycle_status_code,
    concept.provenance_scope_code,
    support.concept_support_id,
    support.concept_support_key,
    support.concept_support_role_code,
    support_role.display_name AS concept_support_role_name,
    support.locator,
    support.notes,
    dataset.dataset_id,
    dataset.dataset_key,
    source_version.source_version_id,
    source_version.source_version_key,
    source.source_id,
    source.source_key,
    source.title AS source_title,
    license_policy.license_policy_id,
    license_policy.license_policy_key,
    license_policy.access_class_code,
    license_policy.rights_status_code,
    rights_status.is_verified AS rights_is_verified,
    license_policy.production_export_allowed
FROM evidence.concept_support AS support
JOIN ref.concept_support_role AS support_role
  ON support_role.concept_support_role_code = support.concept_support_role_code
JOIN kb.concept AS concept
  ON concept.concept_id = support.concept_id
LEFT JOIN evidence.dataset AS dataset
  ON dataset.dataset_id = support.dataset_id
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = COALESCE(
        support.source_version_id,
        dataset.source_version_id
     )
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS license_policy
  ON license_policy.license_policy_id = source_version.license_policy_id
JOIN ref.rights_status AS rights_status
  ON rights_status.rights_status_code = license_policy.rights_status_code;

COMMENT ON VIEW evidence.v_concept_provenance IS
    'Concept support with a controlled provenance role, resolved source version, and rights identifiers; visibility is not redistribution permission and no copied source content is exposed.';

COMMIT;
