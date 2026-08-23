\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- Establish ownership boundaries first, then the controlled vocabularies used
-- by foreign keys in every later migration. No reference values are seeded in
-- this migration.

BEGIN;

CREATE SCHEMA ref;
CREATE SCHEMA kb;
CREATE SCHEMA evidence;
CREATE SCHEMA corpus;
CREATE SCHEMA ml;
CREATE SCHEMA audit;

COMMENT ON SCHEMA ref IS
    'Controlled codes and their database-level semantics.';
COMMENT ON SCHEMA kb IS
    'Canonical, language-neutral coffee sensory knowledge and lexical assertions.';
COMMENT ON SCHEMA evidence IS
    'Versioned sources, rights decisions, datasets, methods, and empirical evidence.';
COMMENT ON SCHEMA corpus IS
    'Raw and derived industry-language observations, kept separate from canonical knowledge.';
COMMENT ON SCHEMA ml IS
    'Regenerable model versions, runs, candidates, and model-derived signals.';
COMMENT ON SCHEMA audit IS
    'Independent reviews and explicit promotion history.';

-- Stable TEXT primary keys are intentional for these small controlled
-- vocabularies. Their codes are public semantic identifiers, not mutable
-- display text; using surrogate identities here would add no independent fact.
-- Each relation is therefore in BCNF: the code is its sole determinant.

CREATE TABLE ref.lifecycle_status (
    lifecycle_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT lifecycle_status_pk PRIMARY KEY (lifecycle_status_code),
    CONSTRAINT lifecycle_status_code_nonempty_ck CHECK (
        lifecycle_status_code = btrim(lifecycle_status_code)
        AND lifecycle_status_code <> ''
    ),
    CONSTRAINT lifecycle_status_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT lifecycle_status_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.lifecycle_status IS
    'Lifecycle codes shared by canonical assertions; history is retained by status rather than deletion.';

CREATE TABLE ref.concept_type (
    concept_type_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT concept_type_pk PRIMARY KEY (concept_type_code),
    CONSTRAINT concept_type_code_nonempty_ck CHECK (
        concept_type_code = btrim(concept_type_code)
        AND concept_type_code <> ''
    ),
    CONSTRAINT concept_type_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT concept_type_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.concept_type IS
    'Language-neutral concept kinds; sensory, composite, qualifier, affective, process, and category concepts remain distinguishable.';

CREATE TABLE ref.relation_type (
    relation_type_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_directional BOOLEAN NOT NULL,
    is_symmetric BOOLEAN NOT NULL,
    is_hierarchical BOOLEAN NOT NULL,
    closure_is_transitive BOOLEAN NOT NULL,
    allows_self BOOLEAN NOT NULL,
    evidence_required BOOLEAN NOT NULL,
    CONSTRAINT relation_type_pk PRIMARY KEY (relation_type_code),
    CONSTRAINT relation_type_code_nonempty_ck CHECK (
        relation_type_code = btrim(relation_type_code)
        AND relation_type_code <> ''
    ),
    CONSTRAINT relation_type_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT relation_type_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT relation_type_direction_symmetry_ck CHECK (
        NOT (is_directional AND is_symmetric)
    ),
    CONSTRAINT relation_type_hierarchy_direction_ck CHECK (
        NOT is_hierarchical OR is_directional
    ),
    CONSTRAINT relation_type_transitive_hierarchy_ck CHECK (
        NOT closure_is_transitive OR is_hierarchical
    )
);

COMMENT ON TABLE ref.relation_type IS
    'Typed graph predicates and enforceable semantic properties. Direction always reads subject predicate object.';
COMMENT ON COLUMN ref.relation_type.is_directional IS
    'True when subject and object roles are semantically ordered.';
COMMENT ON COLUMN ref.relation_type.is_symmetric IS
    'True when the unordered pair has one canonical stored endpoint order.';
COMMENT ON COLUMN ref.relation_type.closure_is_transitive IS
    'True only for a hierarchy whose transitive closure has predicate meaning.';

CREATE TABLE ref.mapping_type (
    mapping_type_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_preferred BOOLEAN NOT NULL,
    is_approved_variant BOOLEAN NOT NULL,
    allows_polysemy BOOLEAN NOT NULL,
    retrieval_precedence SMALLINT NOT NULL,
    CONSTRAINT mapping_type_pk PRIMARY KEY (mapping_type_code),
    CONSTRAINT mapping_type_retrieval_precedence_uq UNIQUE (retrieval_precedence),
    CONSTRAINT mapping_type_code_nonempty_ck CHECK (
        mapping_type_code = btrim(mapping_type_code)
        AND mapping_type_code <> ''
    ),
    CONSTRAINT mapping_type_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT mapping_type_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT mapping_type_preferred_variant_ck CHECK (
        NOT (is_preferred AND is_approved_variant)
    ),
    CONSTRAINT mapping_type_retrieval_precedence_positive_ck CHECK (
        retrieval_precedence > 0
    )
);

COMMENT ON TABLE ref.mapping_type IS
    'Lexical mapping semantics, including preferred forms, approved variants, polysemy permission, and deterministic retrieval precedence.';
COMMENT ON COLUMN ref.mapping_type.retrieval_precedence IS
    'Positive rank used for approved lexical retrieval; lower values are considered first.';

CREATE TABLE ref.language_tag (
    language_tag_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT language_tag_pk PRIMARY KEY (language_tag_code),
    CONSTRAINT language_tag_code_nonempty_ck CHECK (
        language_tag_code = btrim(language_tag_code)
        AND language_tag_code <> ''
    ),
    CONSTRAINT language_tag_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT language_tag_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.language_tag IS
    'Controlled BCP 47-style language tags for lexical expressions, including future multilingual forms such as zh-Hans.';

CREATE TABLE ref.signal_domain (
    signal_domain_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT signal_domain_pk PRIMARY KEY (signal_domain_code),
    CONSTRAINT signal_domain_code_nonempty_ck CHECK (
        signal_domain_code = btrim(signal_domain_code)
        AND signal_domain_code <> ''
    ),
    CONSTRAINT signal_domain_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT signal_domain_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.signal_domain IS
    'Non-interchangeable perceptual, linguistic, corpus, structural, model, and governance signal domains.';

CREATE TABLE ref.review_decision (
    review_decision_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    permits_promotion BOOLEAN NOT NULL,
    CONSTRAINT review_decision_pk PRIMARY KEY (review_decision_code),
    CONSTRAINT review_decision_code_nonempty_ck CHECK (
        review_decision_code = btrim(review_decision_code)
        AND review_decision_code <> ''
    ),
    CONSTRAINT review_decision_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT review_decision_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.review_decision IS
    'Independent review outcomes; permits_promotion is governance metadata and never performs promotion automatically.';

CREATE TABLE ref.provenance_scope (
    provenance_scope_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    requires_source_support BOOLEAN NOT NULL,
    CONSTRAINT provenance_scope_pk PRIMARY KEY (provenance_scope_code),
    CONSTRAINT provenance_scope_code_nonempty_ck CHECK (
        provenance_scope_code = btrim(provenance_scope_code)
        AND provenance_scope_code <> ''
    ),
    CONSTRAINT provenance_scope_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT provenance_scope_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.provenance_scope IS
    'Assertion provenance classes; externally sourced active assertions can be marked as requiring versioned source support.';

CREATE TABLE ref.resolution_status (
    resolution_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL,
    CONSTRAINT resolution_status_pk PRIMARY KEY (resolution_status_code),
    CONSTRAINT resolution_status_code_nonempty_ck CHECK (
        resolution_status_code = btrim(resolution_status_code)
        AND resolution_status_code <> ''
    ),
    CONSTRAINT resolution_status_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT resolution_status_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.resolution_status IS
    'Resolution outcomes, including an explicit unresolved state rather than forced nearest-neighbour classification.';

CREATE TABLE ref.model_run_status (
    model_run_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_terminal BOOLEAN NOT NULL,
    is_successful BOOLEAN NOT NULL,
    CONSTRAINT model_run_status_pk PRIMARY KEY (model_run_status_code),
    CONSTRAINT model_run_status_code_nonempty_ck CHECK (
        model_run_status_code = btrim(model_run_status_code)
        AND model_run_status_code <> ''
    ),
    CONSTRAINT model_run_status_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT model_run_status_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    ),
    CONSTRAINT model_run_status_success_terminal_ck CHECK (
        NOT is_successful OR is_terminal
    )
);

COMMENT ON TABLE ref.model_run_status IS
    'Model-run execution states; successful completion has no canonical promotion side effect.';

CREATE TABLE ref.candidate_status (
    candidate_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_reviewable BOOLEAN NOT NULL,
    is_terminal BOOLEAN NOT NULL,
    CONSTRAINT candidate_status_pk PRIMARY KEY (candidate_status_code),
    CONSTRAINT candidate_status_code_nonempty_ck CHECK (
        candidate_status_code = btrim(candidate_status_code)
        AND candidate_status_code <> ''
    ),
    CONSTRAINT candidate_status_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT candidate_status_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.candidate_status IS
    'Lifecycle semantics for inferred mapping candidates, independent from canonical assertion lifecycle.';

CREATE TABLE ref.access_class (
    access_class_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    permits_raw_text BOOLEAN NOT NULL,
    CONSTRAINT access_class_pk PRIMARY KEY (access_class_code),
    CONSTRAINT access_class_code_nonempty_ck CHECK (
        access_class_code = btrim(access_class_code)
        AND access_class_code <> ''
    ),
    CONSTRAINT access_class_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT access_class_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.access_class IS
    'Controlled access boundaries for source and corpus material; access alone does not grant production export.';

CREATE TABLE ref.rights_status (
    rights_status_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_verified BOOLEAN NOT NULL,
    CONSTRAINT rights_status_pk PRIMARY KEY (rights_status_code),
    CONSTRAINT rights_status_code_nonempty_ck CHECK (
        rights_status_code = btrim(rights_status_code)
        AND rights_status_code <> ''
    ),
    CONSTRAINT rights_status_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name)
        AND display_name <> ''
    ),
    CONSTRAINT rights_status_description_nonempty_ck CHECK (
        description = btrim(description)
        AND description <> ''
    )
);

COMMENT ON TABLE ref.rights_status IS
    'Machine-readable rights-review state; unknown or restricted facts remain explicit rather than inferred.';

COMMIT;
