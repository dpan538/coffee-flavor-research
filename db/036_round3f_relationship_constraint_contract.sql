\set ON_ERROR_STOP on

-- Round 3F adds a deliberately small relationship-research layer. It does not
-- change the canonical ontology, normalize text-first candidates, or introduce
-- a generic weighted graph.

BEGIN;

CREATE TABLE corpus.association_range (
    association_range_id BIGINT GENERATED ALWAYS AS IDENTITY,
    range_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    research_definition TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    support_scope TEXT NOT NULL,
    evidence_key TEXT NOT NULL,
    independent_evidence_family_count SMALLINT NOT NULL,
    formal_grouping_key TEXT,
    explicit_review_evidence TEXT,
    canonical_ontology_effect BOOLEAN NOT NULL DEFAULT FALSE,
    exclusive_membership BOOLEAN NOT NULL DEFAULT FALSE,
    transitive_membership BOOLEAN NOT NULL DEFAULT FALSE,
    probability_semantics BOOLEAN NOT NULL DEFAULT FALSE,
    user_visible_final_section BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT association_range_pk PRIMARY KEY (association_range_id),
    CONSTRAINT association_range_key_uq UNIQUE (range_key),
    CONSTRAINT association_range_text_ck CHECK (
        range_key = lower(btrim(range_key)) AND range_key <> ''
        AND display_name = btrim(display_name) AND display_name <> ''
        AND research_definition = btrim(research_definition)
        AND research_definition <> ''
        AND evidence_key = btrim(evidence_key) AND evidence_key <> ''
        AND (formal_grouping_key IS NULL OR (
            formal_grouping_key = btrim(formal_grouping_key)
            AND formal_grouping_key <> ''
        ))
        AND (explicit_review_evidence IS NULL OR (
            explicit_review_evidence = btrim(explicit_review_evidence)
            AND explicit_review_evidence <> ''
        ))
    ),
    CONSTRAINT association_range_lifecycle_ck CHECK (
        lifecycle_status IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED',
            'BILINGUAL_REVIEWED', 'ACTIVE_FOR_CALIBRATION',
            'REJECTED', 'DEPRECATED'
        )
    ),
    CONSTRAINT association_range_support_scope_ck CHECK (
        support_scope IN (
            'GOVERNED_QUESTION_ANCHOR', 'SOURCE_LOCAL',
            'CROSS_SOURCE', 'UNRESOLVED'
        )
        AND independent_evidence_family_count >= 0
    ),
    CONSTRAINT association_range_nonclaim_ck CHECK (
        NOT canonical_ontology_effect
        AND NOT exclusive_membership
        AND NOT transitive_membership
        AND NOT probability_semantics
        AND NOT user_visible_final_section
    )
);

COMMENT ON TABLE corpus.association_range IS
    'Bounded, overlapping research grouping. A row is not an ontology category, universal sensory dimension, latent truth, probability, or final user section.';

CREATE TABLE corpus.association_range_membership (
    association_range_membership_id BIGINT GENERATED ALWAYS AS IDENTITY,
    membership_key TEXT NOT NULL,
    association_range_id BIGINT NOT NULL,
    normalized_expression_id BIGINT,
    lexical_mapping_key TEXT,
    concept_id BIGINT,
    member_text TEXT,
    member_language_code TEXT,
    membership_role TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    evidence_basis TEXT NOT NULL,
    evidence_key TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    membership_semantics TEXT NOT NULL DEFAULT 'NON_PROBABILISTIC',
    is_exclusive BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT association_range_membership_pk PRIMARY KEY (
        association_range_membership_id
    ),
    CONSTRAINT association_range_membership_key_uq UNIQUE (membership_key),
    CONSTRAINT association_range_membership_range_fk FOREIGN KEY (
        association_range_id
    ) REFERENCES corpus.association_range (association_range_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT association_range_membership_normalized_expression_fk
        FOREIGN KEY (normalized_expression_id)
        REFERENCES corpus.normalized_expression (normalized_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT association_range_membership_lexical_candidate_fk
        FOREIGN KEY (lexical_mapping_key)
        REFERENCES corpus.lexical_mapping_candidate (mapping_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT association_range_membership_concept_fk
        FOREIGN KEY (concept_id) REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT association_range_membership_subject_xor_ck CHECK (
        num_nonnulls(
            normalized_expression_id, lexical_mapping_key,
            concept_id, member_text
        ) = 1
        AND (
            (member_text IS NULL AND member_language_code IS NULL)
            OR (
                member_text = btrim(member_text) AND member_text <> ''
                AND member_language_code = btrim(member_language_code)
                AND member_language_code <> ''
            )
        )
    ),
    CONSTRAINT association_range_membership_role_ck CHECK (
        membership_role IN (
            'ANCHOR', 'FREQUENT_ASSOCIATE', 'CONTEXTUAL_ASSOCIATE',
            'PERIPHERAL_CANDIDATE', 'AMBIGUOUS'
        )
    ),
    CONSTRAINT association_range_membership_lifecycle_ck CHECK (
        lifecycle_status IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED',
            'BILINGUAL_REVIEWED', 'ACTIVE_FOR_CALIBRATION',
            'REJECTED', 'DEPRECATED'
        )
    ),
    CONSTRAINT association_range_membership_evidence_basis_ck CHECK (
        evidence_basis IN (
            'EXISTING_CANONICAL_RELATION', 'SOURCE_DEFINED_GROUPING',
            'EXISTING_GOVERNED_QUESTION_REGION',
            'OBSERVED_SOURCE_LOCAL_COOCCURRENCE',
            'REPRODUCIBLE_CORPUS_STATISTIC',
            'PEER_REVIEWED_SENSORY_EVIDENCE',
            'EXPLICIT_CURATED_REVIEW_DECISION'
        )
    ),
    CONSTRAINT association_range_membership_nonprobability_ck CHECK (
        membership_semantics = 'NON_PROBABILISTIC'
        AND NOT is_exclusive
    ),
    CONSTRAINT association_range_membership_text_ck CHECK (
        membership_key = lower(btrim(membership_key))
        AND membership_key <> ''
        AND evidence_key = btrim(evidence_key) AND evidence_key <> ''
        AND provenance_path = btrim(provenance_path)
        AND provenance_path <> ''
    )
);

COMMENT ON TABLE corpus.association_range_membership IS
    'Evidence-bounded, non-exclusive, non-transitive and non-probabilistic range membership. Exactly one preserved subject representation is used; no canonical resolution is required.';

CREATE TABLE corpus.association_measurement (
    association_measurement_id BIGINT GENERATED ALWAYS AS IDENTITY,
    measurement_key TEXT NOT NULL,
    association_range_membership_id BIGINT NOT NULL,
    method_key TEXT NOT NULL,
    method_version TEXT NOT NULL,
    source_snapshot_key TEXT NOT NULL,
    support_count INTEGER,
    document_count INTEGER,
    independent_source_count INTEGER,
    source_diversity INTEGER,
    observed_value NUMERIC,
    value_semantics TEXT NOT NULL,
    configuration JSONB NOT NULL,
    CONSTRAINT association_measurement_pk PRIMARY KEY (
        association_measurement_id
    ),
    CONSTRAINT association_measurement_key_uq UNIQUE (measurement_key),
    CONSTRAINT association_measurement_membership_fk FOREIGN KEY (
        association_range_membership_id
    ) REFERENCES corpus.association_range_membership (
        association_range_membership_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT association_measurement_method_ck CHECK (
        method_key IN (
            'SOURCE_DEFINED_GROUPING', 'RAW_COOCCURRENCE',
            'DOCUMENT_FREQUENCY', 'JACCARD',
            'CONDITIONAL_COOCCURRENCE', 'PMI', 'PPMI',
            'SOURCE_DIVERSITY_WEIGHTED', 'OVERLAPPING_COMMUNITY',
            'FUZZY_MEMBERSHIP', 'GRAPH_NEIGHBOUR',
            'SOURCE_HOLDOUT_STABILITY', 'BOOTSTRAP_STABILITY'
        )
    ),
    CONSTRAINT association_measurement_support_ck CHECK (
        (support_count IS NULL OR support_count >= 0)
        AND (document_count IS NULL OR document_count >= 0)
        AND (independent_source_count IS NULL OR independent_source_count >= 0)
        AND (source_diversity IS NULL OR source_diversity >= 0)
        AND num_nonnulls(
            support_count, document_count, independent_source_count,
            source_diversity, observed_value
        ) >= 1
    ),
    CONSTRAINT association_measurement_configuration_ck CHECK (
        jsonb_typeof(configuration) = 'object'
        AND configuration <> '{}'::JSONB
    ),
    CONSTRAINT association_measurement_text_ck CHECK (
        measurement_key = lower(btrim(measurement_key))
        AND measurement_key <> ''
        AND method_version = btrim(method_version) AND method_version <> ''
        AND source_snapshot_key = btrim(source_snapshot_key)
        AND source_snapshot_key <> ''
        AND value_semantics = btrim(value_semantics)
        AND value_semantics <> ''
    )
);

COMMENT ON TABLE corpus.association_measurement IS
    'Method-specific quantitative observation ledger. Values retain method, snapshot, counts, semantics and configuration; they are never a universal membership score.';

CREATE TABLE calibration.question_range_target (
    question_range_target_id BIGINT GENERATED ALWAYS AS IDENTITY,
    question_range_target_key TEXT NOT NULL,
    logical_question_code TEXT NOT NULL,
    question_source TEXT NOT NULL,
    association_range_id BIGINT NOT NULL,
    relationship_role TEXT NOT NULL,
    direction_kind TEXT NOT NULL,
    option_scope TEXT,
    evidence_key TEXT NOT NULL,
    context_eligibility_status TEXT NOT NULL,
    user_validation_status TEXT NOT NULL,
    information_gain_status TEXT NOT NULL,
    CONSTRAINT question_range_target_pk PRIMARY KEY (
        question_range_target_id
    ),
    CONSTRAINT question_range_target_key_uq UNIQUE (
        question_range_target_key
    ),
    CONSTRAINT question_range_target_fact_uq UNIQUE (
        logical_question_code, association_range_id, relationship_role
    ),
    CONSTRAINT question_range_target_range_fk FOREIGN KEY (
        association_range_id
    ) REFERENCES corpus.association_range (association_range_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_range_target_source_ck CHECK (
        question_source IN (
            'ROUND3C_QUESTION_BANK', 'ROUND3E_RESEARCH_CANDIDATE'
        )
        AND relationship_role IN (
            'QUESTION_TARGETS_RANGE', 'OPTION_INDICATES_RANGE',
            'QUESTION_DISTINGUISHES_RANGES'
        )
        AND direction_kind IN (
            'BROAD_DIRECTION', 'WITHIN_RANGE', 'CROSS_RANGE'
        )
    ),
    CONSTRAINT question_range_target_nonvalidation_ck CHECK (
        context_eligibility_status = 'HYPOTHESIZED'
        AND user_validation_status = 'NOT_USER_VALIDATED'
        AND information_gain_status = 'NOT_ESTIMABLE'
    ),
    CONSTRAINT question_range_target_text_ck CHECK (
        question_range_target_key = lower(btrim(question_range_target_key))
        AND question_range_target_key <> ''
        AND logical_question_code = lower(btrim(logical_question_code))
        AND logical_question_code <> ''
        AND evidence_key = btrim(evidence_key) AND evidence_key <> ''
        AND (option_scope IS NULL OR (
            option_scope = btrim(option_scope) AND option_scope <> ''
        ))
    )
);

COMMENT ON TABLE calibration.question_range_target IS
    'Logical-question research targeting. A target is a hypothesis, not user validation, information gain, or a measured context effect.';

CREATE TABLE audit.relationship_semantic_rule (
    relationship_key TEXT NOT NULL,
    relationship_domain TEXT NOT NULL,
    subject_entity_type TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_entity_type TEXT NOT NULL,
    cardinality TEXT NOT NULL,
    directionality TEXT NOT NULL,
    symmetry TEXT NOT NULL,
    transitivity TEXT NOT NULL,
    exclusivity TEXT NOT NULL,
    evidence_requirement TEXT NOT NULL,
    provenance_path TEXT NOT NULL,
    lifecycle TEXT NOT NULL,
    computational_role TEXT NOT NULL,
    allowed_inference TEXT NOT NULL,
    forbidden_inference TEXT NOT NULL,
    database_representation TEXT NOT NULL,
    validation_method TEXT NOT NULL,
    negative_test TEXT NOT NULL,
    current_status TEXT NOT NULL,
    CONSTRAINT relationship_semantic_rule_pk PRIMARY KEY (relationship_key),
    CONSTRAINT relationship_semantic_rule_domain_ck CHECK (
        relationship_domain IN (
            'LEXICAL', 'CANONICAL_ONTOLOGY', 'SOURCE_LOCAL_EMPIRICAL',
            'ASSOCIATION_RANGE', 'QUESTION', 'EVIDENCE', 'GOVERNANCE'
        )
    ),
    CONSTRAINT relationship_semantic_rule_status_ck CHECK (
        current_status IN (
            'ENFORCED', 'AUDITED', 'DOCUMENTED_BOUNDARY', 'UNRESOLVED'
        )
    ),
    CONSTRAINT relationship_semantic_rule_nonempty_ck CHECK (
        relationship_key = lower(btrim(relationship_key))
        AND relationship_key <> ''
        AND predicate = btrim(predicate) AND predicate <> ''
        AND forbidden_inference = btrim(forbidden_inference)
        AND forbidden_inference <> ''
    )
);

CREATE TABLE audit.constraint_registry_entry (
    constraint_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    constraint_category TEXT NOT NULL,
    rule TEXT NOT NULL,
    rationale TEXT NOT NULL,
    enforcement_layer TEXT NOT NULL,
    failure_behavior TEXT NOT NULL,
    override_policy TEXT NOT NULL,
    promotion_requirement TEXT NOT NULL,
    negative_test TEXT NOT NULL,
    current_status TEXT NOT NULL,
    introduced_round TEXT NOT NULL,
    CONSTRAINT constraint_registry_entry_pk PRIMARY KEY (constraint_key),
    CONSTRAINT constraint_registry_enforcement_layer_ck CHECK (
        enforcement_layer IN (
            'POSTGRESQL_CONSTRAINT', 'POSTGRESQL_TRIGGER', 'AUDIT_QUERY',
            'CI_GATE', 'CURATION_POLICY', 'DOCUMENTED_BOUNDARY'
        )
    ),
    CONSTRAINT constraint_registry_status_ck CHECK (
        current_status IN (
            'ENFORCED', 'DOCUMENTED_ONLY',
            'MISSING_BUT_ENFORCEABLE', 'INTENTIONALLY_NOT_ENFORCEABLE',
            'UNRESOLVED'
        )
    ),
    CONSTRAINT constraint_registry_entry_nonempty_ck CHECK (
        constraint_key = lower(btrim(constraint_key))
        AND constraint_key <> ''
        AND rule = btrim(rule) AND rule <> ''
        AND negative_test = btrim(negative_test) AND negative_test <> ''
    )
);

CREATE TABLE audit.forbidden_inference_rule (
    forbidden_inference_key TEXT NOT NULL,
    source_fact TEXT NOT NULL,
    forbidden_claim TEXT NOT NULL,
    rule_text TEXT NOT NULL,
    enforcement_layer TEXT NOT NULL,
    constraint_name TEXT NOT NULL,
    negative_test TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT forbidden_inference_rule_pk PRIMARY KEY (
        forbidden_inference_key
    ),
    CONSTRAINT forbidden_inference_fact_uq UNIQUE (
        source_fact, forbidden_claim
    ),
    CONSTRAINT forbidden_inference_layer_ck CHECK (
        enforcement_layer IN (
            'POSTGRESQL_CONSTRAINT', 'POSTGRESQL_TRIGGER', 'AUDIT_QUERY',
            'CI_GATE', 'CURATION_POLICY', 'DOCUMENTED_BOUNDARY'
        )
    ),
    CONSTRAINT forbidden_inference_nonempty_ck CHECK (
        forbidden_inference_key = lower(btrim(forbidden_inference_key))
        AND forbidden_inference_key <> ''
        AND source_fact = upper(btrim(source_fact)) AND source_fact <> ''
        AND forbidden_claim = upper(btrim(forbidden_claim))
        AND forbidden_claim <> ''
        AND rule_text = btrim(rule_text) AND rule_text <> ''
        AND constraint_name = lower(btrim(constraint_name))
        AND constraint_name <> ''
        AND negative_test = btrim(negative_test) AND negative_test <> ''
    )
);

CREATE TABLE audit.round3f_checkpoint (
    checkpoint_key TEXT NOT NULL,
    source_sha TEXT NOT NULL,
    expected_canonical_concept_count INTEGER NOT NULL,
    expected_active_sensory_attribute_count INTEGER NOT NULL,
    text_first_lexical_candidate_intentional BOOLEAN NOT NULL,
    canonical_ontology_frozen BOOLEAN NOT NULL,
    ranking_model_trained BOOLEAN NOT NULL,
    adaptive_policy_trained BOOLEAN NOT NULL,
    deep_learning_model_run BOOLEAN NOT NULL,
    embedding_baseline_run BOOLEAN NOT NULL,
    pgvector_required BOOLEAN NOT NULL,
    real_human_collection_performed BOOLEAN NOT NULL,
    real_observation_count INTEGER NOT NULL,
    question_user_validated_count INTEGER NOT NULL,
    question_information_gain_estimated_count INTEGER NOT NULL,
    product_frontend_modified BOOLEAN NOT NULL,
    CONSTRAINT round3f_checkpoint_pk PRIMARY KEY (checkpoint_key),
    CONSTRAINT round3f_checkpoint_source_sha_ck CHECK (
        source_sha ~ '^[0-9a-f]{40}$'
    ),
    CONSTRAINT round3f_checkpoint_inventory_ck CHECK (
        expected_canonical_concept_count = 130
        AND expected_active_sensory_attribute_count = 92
        AND text_first_lexical_candidate_intentional
        AND canonical_ontology_frozen
    ),
    CONSTRAINT round3f_checkpoint_prohibition_ck CHECK (
        NOT ranking_model_trained AND NOT adaptive_policy_trained
        AND NOT deep_learning_model_run AND NOT embedding_baseline_run
        AND NOT pgvector_required AND NOT real_human_collection_performed
        AND real_observation_count = 0
        AND question_user_validated_count = 0
        AND question_information_gain_estimated_count = 0
        AND NOT product_frontend_modified
    )
);

CREATE FUNCTION corpus.enforce_association_range_lifecycle()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_association_range_lifecycle$
BEGIN
    IF NEW.lifecycle_status = 'SOURCE_LOCAL_SUPPORTED'
       AND (
           NEW.support_scope <> 'SOURCE_LOCAL'
           OR NEW.independent_evidence_family_count < 1
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'association_range_source_local_support_ck',
            MESSAGE = 'SOURCE_LOCAL_SUPPORTED requires one identified source-local evidence family';
    END IF;

    IF (
        NEW.lifecycle_status = 'CROSS_SOURCE_SUPPORTED'
        OR NEW.support_scope = 'CROSS_SOURCE'
    ) AND NEW.independent_evidence_family_count < 2
      AND NEW.formal_grouping_key IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'association_range_cross_source_support_ck',
            MESSAGE = 'cross-source support requires two independent evidence families or an explicit formal grouping';
    END IF;

    IF NEW.lifecycle_status = 'ACTIVE_FOR_CALIBRATION'
       AND NEW.explicit_review_evidence IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'association_range_calibration_review_ck',
            MESSAGE = 'ACTIVE_FOR_CALIBRATION requires explicit review evidence';
    END IF;

    RETURN NEW;
END
$enforce_association_range_lifecycle$;

CREATE TRIGGER association_range_lifecycle_biu
BEFORE INSERT OR UPDATE ON corpus.association_range
FOR EACH ROW EXECUTE FUNCTION corpus.enforce_association_range_lifecycle();

CREATE FUNCTION audit.reject_forbidden_round3f_inference(
    asserted_source_fact TEXT,
    asserted_claim TEXT
)
RETURNS VOID
LANGUAGE plpgsql
STABLE
SET search_path = pg_catalog
AS $reject_forbidden_round3f_inference$
DECLARE
    prohibited audit.forbidden_inference_rule%ROWTYPE;
BEGIN
    SELECT * INTO prohibited
    FROM audit.forbidden_inference_rule AS rule
    WHERE rule.source_fact = upper(btrim(asserted_source_fact))
      AND rule.forbidden_claim = upper(btrim(asserted_claim))
      AND rule.active;

    IF FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = prohibited.constraint_name,
            MESSAGE = prohibited.rule_text;
    END IF;
END
$reject_forbidden_round3f_inference$;

CREATE FUNCTION audit.enforce_round3f_canonical_freeze()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3f_canonical_freeze$
BEGIN
    IF EXISTS (
        SELECT 1 FROM audit.round3f_checkpoint AS checkpoint
        WHERE checkpoint.canonical_ontology_frozen
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3f_canonical_ontology_frozen_ck',
            MESSAGE = 'Round 3F canonical ontology is frozen; record a future ontology change candidate instead';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END
$enforce_round3f_canonical_freeze$;

CREATE TRIGGER concept_round3f_frozen_aiud
AFTER INSERT OR UPDATE OR DELETE ON kb.concept
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3f_canonical_freeze();

CREATE TRIGGER relation_type_round3f_frozen_aiud
AFTER INSERT OR UPDATE OR DELETE ON ref.relation_type
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3f_canonical_freeze();

CREATE FUNCTION audit.prevent_round3f_model_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3f_model_run$
BEGIN
    IF NEW.run_configuration ->> 'round' IN ('3F', 'round3f')
       OR NEW.run_configuration ->> 'uses_association_range' = 'true'
       OR NEW.run_configuration ? 'association_range_snapshot' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3f_model_run_prohibited_ck',
            MESSAGE = 'Round 3F relationship and association-range data cannot be used for a model run';
    END IF;
    RETURN NEW;
END
$prevent_round3f_model_run$;

CREATE TRIGGER model_run_round3f_prohibited_biu
BEFORE INSERT OR UPDATE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3f_model_run();

COMMIT;
