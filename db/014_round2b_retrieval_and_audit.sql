\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- Round 2B
-- Versioned deterministic retrieval, candidate traceability, and independent
-- graded retrieval evaluation.  This migration deliberately leaves the Round
-- 1/2A kb.retrieve_lexical_candidates function unchanged.  Retrieval tiers are
-- ordinal precedence lanes, never coefficients in an aggregate score.

BEGIN;

CREATE TABLE ref.retrieval_tier (
    retrieval_tier_code TEXT NOT NULL,
    tier_order SMALLINT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_graph_expansion BOOLEAN NOT NULL,
    CONSTRAINT retrieval_tier_pk PRIMARY KEY (retrieval_tier_code),
    CONSTRAINT retrieval_tier_order_uq UNIQUE (tier_order),
    CONSTRAINT retrieval_tier_code_nonempty_ck CHECK (
        retrieval_tier_code = btrim(retrieval_tier_code)
        AND retrieval_tier_code <> ''
    ),
    CONSTRAINT retrieval_tier_order_positive_ck CHECK (tier_order > 0),
    CONSTRAINT retrieval_tier_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT retrieval_tier_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

COMMENT ON TABLE ref.retrieval_tier IS
    'Ordinal deterministic retrieval lanes. Tier order is precedence, not a sensory or calibrated relevance weight.';

CREATE TABLE ref.retrieval_baseline (
    retrieval_baseline_code TEXT NOT NULL,
    maximum_retrieval_tier_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT retrieval_baseline_pk PRIMARY KEY (retrieval_baseline_code),
    CONSTRAINT retrieval_baseline_maximum_tier_uq UNIQUE (
        maximum_retrieval_tier_code
    ),
    CONSTRAINT retrieval_baseline_maximum_tier_fk FOREIGN KEY (
        maximum_retrieval_tier_code
    ) REFERENCES ref.retrieval_tier (retrieval_tier_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_baseline_code_nonempty_ck CHECK (
        retrieval_baseline_code = btrim(retrieval_baseline_code)
        AND retrieval_baseline_code <> ''
    ),
    CONSTRAINT retrieval_baseline_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT retrieval_baseline_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

COMMENT ON TABLE ref.retrieval_baseline IS
    'Named A/B/C/D ablations whose maximum tier is explicit and monotonically additive by retrieval capability.';

CREATE TABLE ref.retrieval_signal (
    retrieval_signal_code TEXT NOT NULL,
    signal_domain_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT retrieval_signal_pk PRIMARY KEY (retrieval_signal_code),
    CONSTRAINT retrieval_signal_domain_fk FOREIGN KEY (signal_domain_code)
        REFERENCES ref.signal_domain (signal_domain_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_signal_code_nonempty_ck CHECK (
        retrieval_signal_code = btrim(retrieval_signal_code)
        AND retrieval_signal_code <> ''
    ),
    CONSTRAINT retrieval_signal_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT retrieval_signal_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

COMMENT ON TABLE ref.retrieval_signal IS
    'Interpretable candidate-generation signals retained separately; values from different signal types must not be summed.';

CREATE TABLE ref.retrieval_metric (
    retrieval_metric_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    requires_cutoff_k BOOLEAN NOT NULL,
    minimum_value NUMERIC,
    maximum_value NUMERIC,
    CONSTRAINT retrieval_metric_pk PRIMARY KEY (retrieval_metric_code),
    CONSTRAINT retrieval_metric_code_nonempty_ck CHECK (
        retrieval_metric_code = btrim(retrieval_metric_code)
        AND retrieval_metric_code <> ''
    ),
    CONSTRAINT retrieval_metric_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT retrieval_metric_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    ),
    CONSTRAINT retrieval_metric_bounds_pair_ck CHECK (
        (minimum_value IS NULL AND maximum_value IS NULL)
        OR (
            minimum_value IS NOT NULL
            AND (maximum_value IS NULL OR minimum_value <= maximum_value)
        )
    )
);

COMMENT ON TABLE ref.retrieval_metric IS
    'Evaluation metric identities and range semantics. They measure language retrieval, never objective coffee flavour.';

CREATE TABLE ref.relevance_grade (
    relevance_grade_code TEXT NOT NULL,
    ordinal_value SMALLINT,
    gain_value NUMERIC,
    is_unresolved BOOLEAN NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT relevance_grade_pk PRIMARY KEY (relevance_grade_code),
    CONSTRAINT relevance_grade_ordinal_uq UNIQUE (ordinal_value),
    CONSTRAINT relevance_grade_code_nonempty_ck CHECK (
        relevance_grade_code = btrim(relevance_grade_code)
        AND relevance_grade_code <> ''
    ),
    CONSTRAINT relevance_grade_semantics_ck CHECK (
        (
            is_unresolved
            AND ordinal_value IS NULL
            AND gain_value IS NULL
        ) OR (
            NOT is_unresolved
            AND ordinal_value BETWEEN 0 AND 3
            AND gain_value >= 0
        )
    ),
    CONSTRAINT relevance_grade_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT relevance_grade_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

COMMENT ON TABLE ref.relevance_grade IS
    'Audit rubric: grades 0--3 are candidate relevance; U is a case-level unresolved expectation and has no ranking gain.';

CREATE TABLE ref.audit_split (
    audit_split_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_held_out BOOLEAN NOT NULL,
    CONSTRAINT audit_split_pk PRIMARY KEY (audit_split_code),
    CONSTRAINT audit_split_held_out_uq UNIQUE (is_held_out),
    CONSTRAINT audit_split_code_nonempty_ck CHECK (
        audit_split_code = btrim(audit_split_code)
        AND audit_split_code <> ''
    ),
    CONSTRAINT audit_split_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT audit_split_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.audit_review_role (
    audit_review_role_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    is_adjudicated BOOLEAN NOT NULL,
    CONSTRAINT audit_review_role_pk PRIMARY KEY (audit_review_role_code),
    CONSTRAINT audit_review_role_adjudicated_uq UNIQUE (is_adjudicated),
    CONSTRAINT audit_review_role_code_nonempty_ck CHECK (
        audit_review_role_code = btrim(audit_review_role_code)
        AND audit_review_role_code <> ''
    ),
    CONSTRAINT audit_review_role_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT audit_review_role_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

CREATE TABLE ref.retrieval_audit_stratum (
    retrieval_audit_stratum_code TEXT NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT retrieval_audit_stratum_pk PRIMARY KEY (
        retrieval_audit_stratum_code
    ),
    CONSTRAINT retrieval_audit_stratum_code_nonempty_ck CHECK (
        retrieval_audit_stratum_code = btrim(retrieval_audit_stratum_code)
        AND retrieval_audit_stratum_code <> ''
    ),
    CONSTRAINT retrieval_audit_stratum_display_name_nonempty_ck CHECK (
        display_name = btrim(display_name) AND display_name <> ''
    ),
    CONSTRAINT retrieval_audit_stratum_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

INSERT INTO ref.retrieval_tier (
    retrieval_tier_code,
    tier_order,
    display_name,
    description,
    is_graph_expansion
)
VALUES
    ('A', 1, 'Approved preferred exact', 'The normalized query exactly matches a current approved preferred lexicalization.', FALSE),
    ('B', 2, 'Approved lexical variant', 'The normalized query exactly matches a current approved variant lexicalization.', FALSE),
    ('C', 3, 'PostgreSQL trigram', 'A canonical-dictionary expression passes the declared pg_trgm threshold; similarity is orthographic only.', FALSE),
    ('D', 4, 'Typed graph expansion', 'A one-hop candidate is exposed through a versioned allowlisted canonical relation and traversal direction.', TRUE);

INSERT INTO ref.retrieval_baseline (
    retrieval_baseline_code,
    maximum_retrieval_tier_code,
    display_name,
    description
)
VALUES
    ('A', 'A', 'Baseline A: exact only', 'Approved preferred exact lexicalization only.'),
    ('B', 'B', 'Baseline B: exact plus variant', 'Baseline A plus approved lexical variants.'),
    ('C', 'C', 'Baseline C: trigram fallback', 'Baseline B plus orthographic pg_trgm candidate generation.'),
    ('D', 'D', 'Baseline D: typed graph expansion', 'Baseline C plus one-hop allowlisted canonical graph expansion.');

INSERT INTO ref.retrieval_signal (
    retrieval_signal_code,
    signal_domain_code,
    display_name,
    description
)
VALUES
    ('raw_surface_exact', 'linguistic_semantic', 'Raw surface exact', 'The query text exactly equals the matched lexical expression text.'),
    ('normalized_phrase_match', 'linguistic_semantic', 'Normalized phrase match', 'The versioned normalization output exactly equals a canonical-dictionary normalized expression.'),
    ('approved_variant_match', 'linguistic_semantic', 'Approved variant match', 'The matched lexicalization is explicitly governed as an approved variant.'),
    ('pg_trgm_similarity', 'linguistic_semantic', 'PostgreSQL trigram similarity', 'Orthographic pg_trgm similarity on version-normalized text; it is not sensory similarity.'),
    ('typed_graph_hop', 'structural', 'Typed graph hop', 'A one-hop allowlisted canonical relation exposed the candidate from a direct seed.');

INSERT INTO ref.retrieval_metric (
    retrieval_metric_code,
    display_name,
    description,
    requires_cutoff_k,
    minimum_value,
    maximum_value
)
VALUES
    ('recall_at_k', 'Recall at K', 'Macro recall of adjudicated grade-2-or-3 concepts among resolvable cases.', TRUE, 0, 1),
    ('mrr', 'Mean reciprocal rank', 'Macro reciprocal rank of the first adjudicated grade-2-or-3 candidate among resolvable cases.', FALSE, 0, 1),
    ('ndcg_at_k', 'Normalized discounted cumulative gain at K', 'Macro graded ranking quality using gains 0, 1, 3, and 7; unresolved cases are excluded.', TRUE, 0, 1),
    ('coverage', 'Coverage', 'Fraction of audit cases returning at least one candidate.', FALSE, 0, 1),
    ('abstention_rate', 'Abstention rate', 'Fraction of audit cases returning no candidate.', FALSE, 0, 1),
    ('abstention_error', 'Abstention error', 'Among abstentions, the fraction adjudicated as resolvable.', FALSE, 0, 1),
    ('median_candidate_set_size', 'Median candidate-set size', 'Median number of candidates per audit case, including zero for abstentions.', FALSE, 0, NULL),
    ('unsafe_nonabstention', 'Unsafe non-abstention', 'Among genuinely unresolved cases, the fraction for which candidates were returned.', FALSE, 0, 1);

INSERT INTO ref.relevance_grade (
    relevance_grade_code,
    ordinal_value,
    gain_value,
    is_unresolved,
    display_name,
    description
)
VALUES
    ('0', 0, 0, FALSE, 'Misleading or unrelated', 'The candidate is misleading or unrelated for language normalization.'),
    ('1', 1, 1, FALSE, 'Useful indirect relation', 'The candidate is useful but only indirectly related.'),
    ('2', 2, 3, FALSE, 'Defensible related mapping', 'The candidate is a defensible broader, narrower, or composite-reference mapping.'),
    ('3', 3, 7, FALSE, 'Same canonical concept', 'The candidate is the same canonical concept or a valid lexicalization.'),
    ('U', NULL, NULL, TRUE, 'Genuinely unresolved', 'No safe canonical mapping is expected; this case-level label has no ranking gain.');

INSERT INTO ref.audit_split (
    audit_split_code,
    display_name,
    description,
    is_held_out
)
VALUES
    ('development', 'Development', 'Cases available for rule and threshold development; never reported as held-out performance.', FALSE),
    ('held_out', 'Held-out', 'Frozen cases excluded from iterative rule and threshold tuning.', TRUE);

INSERT INTO ref.audit_review_role (
    audit_review_role_code,
    display_name,
    description,
    is_adjudicated
)
VALUES
    ('independent', 'Independent review', 'An independent semantic and ontology-rule assessment before adjudication.', FALSE),
    ('adjudicated', 'Adjudicated gold', 'The frozen assessment used for reported evaluation metrics.', TRUE);

INSERT INTO ref.retrieval_audit_stratum (
    retrieval_audit_stratum_code,
    display_name,
    description
)
VALUES
    ('exact', 'Exact lexicalization', 'Approved exact preferred-label cases.'),
    ('variant', 'Approved or orthographic variant', 'Approved variants and safe normalization differences.'),
    ('orthographic_difficulty', 'Orthographic difficulty', 'Misspelling, spacing, punctuation, hyphenation, and difficult short-word cases.'),
    ('graph_reference', 'Hierarchy or composite reference', 'Broader, narrower, composite, and consumer-reference cases.'),
    ('qualifier_polysemy', 'Qualifier or polysemy', 'Context-sensitive qualifier and polysemous expression cases.'),
    ('non_descriptive_language', 'Metaphor, process, or affective language', 'Industry metaphor, process-like language, and affective language.'),
    ('hard_negative', 'Hard negative', 'Plausible lexical false neighbours that should not be forced.'),
    ('unresolved', 'Genuinely unresolved', 'Expressions for which adjudication expects explicit abstention.');

CREATE TABLE ml.retrieval_graph_policy (
    retrieval_graph_policy_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_graph_policy_key TEXT NOT NULL,
    version_label TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    rules_sha256 TEXT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    is_frozen BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    configuration JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT retrieval_graph_policy_pk PRIMARY KEY (
        retrieval_graph_policy_id
    ),
    CONSTRAINT retrieval_graph_policy_key_uq UNIQUE (
        retrieval_graph_policy_key
    ),
    CONSTRAINT retrieval_graph_policy_version_uq UNIQUE (name, version_label),
    CONSTRAINT retrieval_graph_policy_key_nonempty_ck CHECK (
        retrieval_graph_policy_key = btrim(retrieval_graph_policy_key)
        AND retrieval_graph_policy_key <> ''
    ),
    CONSTRAINT retrieval_graph_policy_version_nonempty_ck CHECK (
        version_label = btrim(version_label) AND version_label <> ''
    ),
    CONSTRAINT retrieval_graph_policy_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT retrieval_graph_policy_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    ),
    CONSTRAINT retrieval_graph_policy_rules_sha256_ck CHECK (
        rules_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT retrieval_graph_policy_code_commit_sha_ck CHECK (
        code_commit_sha ~ '^[0-9a-f]{40}$'
    ),
    CONSTRAINT retrieval_graph_policy_configuration_object_ck CHECK (
        jsonb_typeof(configuration) = 'object'
    )
);

COMMENT ON TABLE ml.retrieval_graph_policy IS
    'Frozen, versioned allowlist for typed one-hop canonical graph expansion; source-specific scheme edges are outside its model.';

CREATE TABLE ml.retrieval_graph_policy_rule (
    retrieval_graph_policy_rule_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_graph_policy_rule_key TEXT NOT NULL,
    retrieval_graph_policy_id BIGINT NOT NULL,
    rule_order SMALLINT NOT NULL,
    relation_type_code TEXT NOT NULL,
    traversal_direction TEXT NOT NULL,
    maximum_hops SMALLINT NOT NULL,
    description TEXT NOT NULL,
    CONSTRAINT retrieval_graph_policy_rule_pk PRIMARY KEY (
        retrieval_graph_policy_rule_id
    ),
    CONSTRAINT retrieval_graph_policy_rule_key_uq UNIQUE (
        retrieval_graph_policy_rule_key
    ),
    CONSTRAINT retrieval_graph_policy_rule_order_uq UNIQUE (
        retrieval_graph_policy_id,
        rule_order
    ),
    CONSTRAINT retrieval_graph_policy_rule_semantics_uq UNIQUE (
        retrieval_graph_policy_id,
        relation_type_code,
        traversal_direction
    ),
    CONSTRAINT retrieval_graph_policy_rule_policy_fk FOREIGN KEY (
        retrieval_graph_policy_id
    ) REFERENCES ml.retrieval_graph_policy (retrieval_graph_policy_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_graph_policy_rule_relation_type_fk FOREIGN KEY (
        relation_type_code
    ) REFERENCES ref.relation_type (relation_type_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_graph_policy_rule_key_nonempty_ck CHECK (
        retrieval_graph_policy_rule_key = btrim(retrieval_graph_policy_rule_key)
        AND retrieval_graph_policy_rule_key <> ''
    ),
    CONSTRAINT retrieval_graph_policy_rule_order_positive_ck CHECK (
        rule_order > 0
    ),
    CONSTRAINT retrieval_graph_policy_rule_direction_ck CHECK (
        traversal_direction IN ('OUTGOING', 'INCOMING', 'SYMMETRIC')
    ),
    CONSTRAINT retrieval_graph_policy_rule_one_hop_ck CHECK (
        maximum_hops = 1
    ),
    CONSTRAINT retrieval_graph_policy_rule_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    )
);

CREATE FUNCTION ml.guard_frozen_retrieval_graph_policy()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_retrieval_graph_policy$
DECLARE
    checked_policy_id BIGINT;
    policy_is_frozen BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'retrieval_graph_policy' THEN
        IF OLD.is_frozen THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000',
                CONSTRAINT = 'retrieval_graph_policy_frozen_ck',
                MESSAGE = 'retrieval_graph_policy_frozen_ck: a frozen graph policy cannot be updated or deleted';
        END IF;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    checked_policy_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.retrieval_graph_policy_id
        ELSE NEW.retrieval_graph_policy_id
    END;

    SELECT policy.is_frozen
    INTO policy_is_frozen
    FROM ml.retrieval_graph_policy AS policy
    WHERE policy.retrieval_graph_policy_id = checked_policy_id;

    IF COALESCE(policy_is_frozen, FALSE) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'retrieval_graph_policy_rule_frozen_ck',
            MESSAGE = 'retrieval_graph_policy_rule_frozen_ck: rules of a frozen graph policy cannot be inserted, updated, or deleted';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_retrieval_graph_policy$;

CREATE TRIGGER retrieval_graph_policy_frozen_bud
BEFORE UPDATE OR DELETE
ON ml.retrieval_graph_policy
FOR EACH ROW
EXECUTE FUNCTION ml.guard_frozen_retrieval_graph_policy();

CREATE TRIGGER retrieval_graph_policy_rule_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON ml.retrieval_graph_policy_rule
FOR EACH ROW
EXECUTE FUNCTION ml.guard_frozen_retrieval_graph_policy();

INSERT INTO ml.retrieval_graph_policy (
    retrieval_graph_policy_key,
    version_label,
    name,
    description,
    rules_sha256,
    code_commit_sha,
    is_frozen,
    created_at,
    configuration
)
VALUES (
    'graph_policy.round2b.v1',
    '1.0.0',
    'Round 2B conservative one-hop policy',
    'Allows only explicit canonical hierarchy, composite/reference, and supported sensory-neighbour traversal. It excludes source schemes, contrast, modifier, process inference, and transitive closure.',
    '831811e96925ce8adddbc0f7420a7f2ce7843b28ebee5ca0a9af233f1fbbff17',
    '2d864d56496c587cff5b6774e0ea41be8b416e6c',
    FALSE,
    TIMESTAMPTZ '2026-08-24 00:00:00+00',
    '{"maximum_hops":1,"uses_source_schemes":false,"uses_transitive_closure":false,"weighted_score":false}'::JSONB
);

INSERT INTO ml.retrieval_graph_policy_rule (
    retrieval_graph_policy_rule_key,
    retrieval_graph_policy_id,
    rule_order,
    relation_type_code,
    traversal_direction,
    maximum_hops,
    description
)
SELECT
    seed.rule_key,
    policy.retrieval_graph_policy_id,
    seed.rule_order,
    seed.relation_type_code,
    seed.traversal_direction,
    1,
    seed.description
FROM (
    VALUES
        ('graph_policy_rule.round2b.composite_component.outgoing', 10::SMALLINT, 'composite_has_component', 'OUTGOING', 'Expose a named component from its composite reference.'),
        ('graph_policy_rule.round2b.consumer_reference.outgoing', 20::SMALLINT, 'consumer_reference_for', 'OUTGOING', 'Expose the concept communicated by a consumer reference.'),
        ('graph_policy_rule.round2b.broader.incoming', 30::SMALLINT, 'broader_than', 'INCOMING', 'Expose the directly broader parent of a narrower seed.'),
        ('graph_policy_rule.round2b.broader.outgoing', 40::SMALLINT, 'broader_than', 'OUTGOING', 'Expose a directly narrower child of a broader seed without transitive closure.'),
        ('graph_policy_rule.round2b.sensory_neighbour.symmetric', 50::SMALLINT, 'sensory_neighbour', 'SYMMETRIC', 'Expose only an explicitly supported current symmetric sensory-neighbour assertion.')
) AS seed(
    rule_key,
    rule_order,
    relation_type_code,
    traversal_direction,
    description
)
CROSS JOIN ml.retrieval_graph_policy AS policy
WHERE policy.retrieval_graph_policy_key = 'graph_policy.round2b.v1';

UPDATE ml.retrieval_graph_policy
SET is_frozen = TRUE
WHERE retrieval_graph_policy_key = 'graph_policy.round2b.v1';

-- Normalization-dependent run, trace, retrieval, and audit objects follow
-- after the Round 2B corpus/normalization migrations and are completed below.

CREATE TABLE ml.deterministic_retrieval_run (
    model_run_id BIGINT NOT NULL,
    retrieval_baseline_code TEXT NOT NULL,
    normalization_pipeline_id BIGINT NOT NULL,
    retrieval_graph_policy_id BIGINT,
    top_k INTEGER NOT NULL,
    trigram_threshold REAL NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    CONSTRAINT deterministic_retrieval_run_pk PRIMARY KEY (model_run_id),
    CONSTRAINT deterministic_retrieval_run_model_run_fk FOREIGN KEY (
        model_run_id
    ) REFERENCES ml.model_run (model_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_retrieval_run_baseline_fk FOREIGN KEY (
        retrieval_baseline_code
    ) REFERENCES ref.retrieval_baseline (retrieval_baseline_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_retrieval_run_pipeline_fk FOREIGN KEY (
        normalization_pipeline_id
    ) REFERENCES corpus.normalization_pipeline (normalization_pipeline_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_retrieval_run_graph_policy_fk FOREIGN KEY (
        retrieval_graph_policy_id
    ) REFERENCES ml.retrieval_graph_policy (retrieval_graph_policy_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_retrieval_run_top_k_ck CHECK (
        top_k BETWEEN 1 AND 100
    ),
    CONSTRAINT deterministic_retrieval_run_threshold_ck CHECK (
        trigram_threshold BETWEEN 0::REAL AND 1::REAL
    ),
    CONSTRAINT deterministic_retrieval_run_graph_policy_ck CHECK (
        (retrieval_baseline_code = 'D')
        = (retrieval_graph_policy_id IS NOT NULL)
    ),
    CONSTRAINT deterministic_retrieval_run_configuration_sha256_ck CHECK (
        configuration_sha256 ~ '^[0-9a-f]{64}$'
    )
);

COMMENT ON TABLE ml.deterministic_retrieval_run IS
    'Subtype fixing the baseline, normalizer, optional graph policy, threshold, and top-K for a versioned deterministic model run.';

CREATE TABLE ml.deterministic_candidate_trace (
    mapping_candidate_id BIGINT NOT NULL,
    retrieval_tier_code TEXT NOT NULL,
    matched_expression_id BIGINT,
    seed_mapping_candidate_id BIGINT,
    concept_relation_id BIGINT,
    traversal_direction TEXT,
    graph_hop_count SMALLINT NOT NULL DEFAULT 0,
    raw_surface_exact BOOLEAN NOT NULL DEFAULT FALSE,
    normalized_phrase_match BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT deterministic_candidate_trace_pk PRIMARY KEY (
        mapping_candidate_id
    ),
    CONSTRAINT deterministic_candidate_trace_candidate_fk FOREIGN KEY (
        mapping_candidate_id
    ) REFERENCES ml.mapping_candidate (mapping_candidate_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_trace_tier_fk FOREIGN KEY (
        retrieval_tier_code
    ) REFERENCES ref.retrieval_tier (retrieval_tier_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_trace_expression_fk FOREIGN KEY (
        matched_expression_id
    ) REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_trace_seed_candidate_fk FOREIGN KEY (
        seed_mapping_candidate_id
    ) REFERENCES ml.mapping_candidate (mapping_candidate_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_trace_relation_fk FOREIGN KEY (
        concept_relation_id
    ) REFERENCES kb.concept_relation (concept_relation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_trace_shape_ck CHECK (
        (
            retrieval_tier_code IN ('A', 'B')
            AND matched_expression_id IS NOT NULL
            AND seed_mapping_candidate_id IS NULL
            AND concept_relation_id IS NULL
            AND traversal_direction IS NULL
            AND graph_hop_count = 0
            AND normalized_phrase_match
        ) OR (
            retrieval_tier_code = 'C'
            AND matched_expression_id IS NOT NULL
            AND seed_mapping_candidate_id IS NULL
            AND concept_relation_id IS NULL
            AND traversal_direction IS NULL
            AND graph_hop_count = 0
            AND NOT raw_surface_exact
            AND NOT normalized_phrase_match
        ) OR (
            retrieval_tier_code = 'D'
            AND matched_expression_id IS NULL
            AND seed_mapping_candidate_id IS NOT NULL
            AND concept_relation_id IS NOT NULL
            AND traversal_direction IN ('OUTGOING', 'INCOMING', 'SYMMETRIC')
            AND graph_hop_count = 1
            AND NOT raw_surface_exact
            AND NOT normalized_phrase_match
        )
    )
);

COMMENT ON TABLE ml.deterministic_candidate_trace IS
    'One typed trace per persisted deterministic candidate. Graph candidates point to their same-inference seed and exact canonical relation.';

ALTER TABLE ml.candidate_signal
ADD CONSTRAINT candidate_signal_id_candidate_uq UNIQUE (
    candidate_signal_id,
    mapping_candidate_id
);

CREATE TABLE ml.deterministic_candidate_signal (
    candidate_signal_id BIGINT NOT NULL,
    mapping_candidate_id BIGINT NOT NULL,
    retrieval_signal_code TEXT NOT NULL,
    signal_ordinal SMALLINT NOT NULL,
    CONSTRAINT deterministic_candidate_signal_pk PRIMARY KEY (
        candidate_signal_id
    ),
    CONSTRAINT deterministic_candidate_signal_candidate_ordinal_uq UNIQUE (
        mapping_candidate_id,
        signal_ordinal
    ),
    CONSTRAINT deterministic_candidate_signal_candidate_type_uq UNIQUE (
        mapping_candidate_id,
        retrieval_signal_code
    ),
    CONSTRAINT deterministic_candidate_signal_source_fk FOREIGN KEY (
        candidate_signal_id,
        mapping_candidate_id
    ) REFERENCES ml.candidate_signal (
        candidate_signal_id,
        mapping_candidate_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_signal_trace_fk FOREIGN KEY (
        mapping_candidate_id
    ) REFERENCES ml.deterministic_candidate_trace (mapping_candidate_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_signal_type_fk FOREIGN KEY (
        retrieval_signal_code
    ) REFERENCES ref.retrieval_signal (retrieval_signal_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT deterministic_candidate_signal_ordinal_positive_ck CHECK (
        signal_ordinal > 0
    )
);

COMMENT ON TABLE ml.deterministic_candidate_signal IS
    'Typed subtype of candidate_signal. Heterogeneous values remain separate ledger entries and are never collapsed into one score.';

CREATE FUNCTION ml.enforce_deterministic_candidate_trace()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_deterministic_candidate_trace$
DECLARE
    checked_inference_id BIGINT;
    checked_concept_id BIGINT;
    checked_model_run_id BIGINT;
    selected_baseline_code TEXT;
    selected_policy_id BIGINT;
    maximum_tier_order SMALLINT;
    checked_tier_order SMALLINT;
    seed_inference_id BIGINT;
    seed_concept_id BIGINT;
BEGIN
    SELECT
        candidate.mapping_inference_id,
        candidate.concept_id,
        inference.model_run_id
    INTO
        checked_inference_id,
        checked_concept_id,
        checked_model_run_id
    FROM ml.mapping_candidate AS candidate
    JOIN ml.mapping_inference AS inference
      ON inference.mapping_inference_id = candidate.mapping_inference_id
    WHERE candidate.mapping_candidate_id = NEW.mapping_candidate_id;

    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    SELECT
        run.retrieval_baseline_code,
        run.retrieval_graph_policy_id,
        maximum_tier.tier_order,
        checked_tier.tier_order
    INTO
        selected_baseline_code,
        selected_policy_id,
        maximum_tier_order,
        checked_tier_order
    FROM ml.deterministic_retrieval_run AS run
    JOIN ref.retrieval_baseline AS baseline
      ON baseline.retrieval_baseline_code = run.retrieval_baseline_code
    JOIN ref.retrieval_tier AS maximum_tier
      ON maximum_tier.retrieval_tier_code = baseline.maximum_retrieval_tier_code
    JOIN ref.retrieval_tier AS checked_tier
      ON checked_tier.retrieval_tier_code = NEW.retrieval_tier_code
    WHERE run.model_run_id = checked_model_run_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'deterministic_candidate_trace_run_ck',
            MESSAGE = 'deterministic_candidate_trace_run_ck: a traced candidate requires a deterministic retrieval-run subtype';
    END IF;

    IF checked_tier_order > maximum_tier_order THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'deterministic_candidate_trace_baseline_ck',
            MESSAGE = 'deterministic_candidate_trace_baseline_ck: candidate tier exceeds the run baseline';
    END IF;

    IF NEW.retrieval_tier_code IN ('A', 'B', 'C') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM kb.lexicalization AS lexicalization
            JOIN ref.mapping_type AS mapping_type
              ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
            JOIN kb.concept AS concept
              ON concept.concept_id = lexicalization.concept_id
             AND concept.lifecycle_status_code = 'active'
            WHERE lexicalization.expression_id = NEW.matched_expression_id
              AND lexicalization.concept_id = checked_concept_id
              AND lexicalization.lifecycle_status_code = 'active'
              AND lexicalization.valid_from <= CURRENT_TIMESTAMP
              AND (
                    lexicalization.valid_until IS NULL
                    OR lexicalization.valid_until > CURRENT_TIMESTAMP
                  )
              AND (
                    (NEW.retrieval_tier_code = 'A' AND mapping_type.is_preferred)
                    OR (
                        NEW.retrieval_tier_code = 'B'
                        AND mapping_type.is_approved_variant
                    )
                    OR (
                        NEW.retrieval_tier_code = 'C'
                        AND (
                            mapping_type.is_preferred
                            OR mapping_type.is_approved_variant
                        )
                    )
                  )
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'deterministic_candidate_trace_lexicalization_ck',
                MESSAGE = 'deterministic_candidate_trace_lexicalization_ck: direct trace must identify a current approved lexicalization to the candidate concept';
        END IF;
    ELSE
        SELECT
            seed.mapping_inference_id,
            seed.concept_id
        INTO
            seed_inference_id,
            seed_concept_id
        FROM ml.mapping_candidate AS seed
        JOIN ml.deterministic_candidate_trace AS seed_trace
          ON seed_trace.mapping_candidate_id = seed.mapping_candidate_id
        WHERE seed.mapping_candidate_id = NEW.seed_mapping_candidate_id
          AND seed_trace.retrieval_tier_code IN ('A', 'B', 'C');

        IF NOT FOUND OR seed_inference_id <> checked_inference_id THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'deterministic_candidate_trace_seed_ck',
                MESSAGE = 'deterministic_candidate_trace_seed_ck: graph seed must be a direct candidate from the same inference';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM kb.v_concept_neighbours AS neighbour
            JOIN ml.retrieval_graph_policy_rule AS policy_rule
              ON policy_rule.retrieval_graph_policy_id = selected_policy_id
             AND policy_rule.relation_type_code = neighbour.relation_type_code
             AND policy_rule.traversal_direction = neighbour.traversal_direction
             AND policy_rule.maximum_hops = NEW.graph_hop_count
            WHERE neighbour.concept_id = seed_concept_id
              AND neighbour.neighbour_concept_id = checked_concept_id
              AND neighbour.concept_relation_id = NEW.concept_relation_id
              AND neighbour.traversal_direction = NEW.traversal_direction
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'deterministic_candidate_trace_graph_ck',
                MESSAGE = 'deterministic_candidate_trace_graph_ck: graph trace is not a current one-hop path allowed by the run policy';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_deterministic_candidate_trace$;

CREATE TRIGGER deterministic_candidate_trace_semantics_biu
BEFORE INSERT OR UPDATE
ON ml.deterministic_candidate_trace
FOR EACH ROW
EXECUTE FUNCTION ml.enforce_deterministic_candidate_trace();

CREATE FUNCTION ml.retrieve_deterministic_candidates(
    query_text TEXT,
    language_tag TEXT,
    normalization_pipeline_key TEXT,
    baseline_code TEXT DEFAULT 'D',
    top_k INTEGER DEFAULT 5,
    trigram_threshold REAL DEFAULT 0.35::REAL
)
RETURNS TABLE (
    retrieval_status_code TEXT,
    candidate_rank INTEGER,
    retrieval_tier_code TEXT,
    tier_order INTEGER,
    matched_expression_id BIGINT,
    matched_expression_key TEXT,
    concept_id BIGINT,
    concept_key TEXT,
    concept_type_code TEXT,
    mapping_type_code TEXT,
    trigram_similarity REAL,
    seed_concept_id BIGINT,
    seed_concept_key TEXT,
    concept_relation_id BIGINT,
    relation_type_code TEXT,
    traversal_direction TEXT,
    graph_hop_count SMALLINT,
    raw_surface_exact BOOLEAN,
    normalized_phrase_match BOOLEAN,
    signal_ledger JSONB
)
LANGUAGE plpgsql
STABLE
SET search_path = pg_catalog, public
AS $retrieve_deterministic_candidates$
DECLARE
    selected_pipeline_id BIGINT;
    selected_pipeline_language TEXT;
    selected_baseline_code TEXT;
    selected_maximum_tier_order SMALLINT;
    selected_graph_policy_id BIGINT;
    normalized_query TEXT;
    requested_top_k INTEGER;
    selected_trigram_threshold REAL;
    candidate_expression_limit INTEGER;
BEGIN
    IF NULLIF(btrim($3), '') IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_pipeline_key_ck',
            MESSAGE = 'deterministic_retrieval_pipeline_key_ck: normalization_pipeline_key is required';
    END IF;

    IF NULLIF(btrim(language_tag), '') IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_language_tag_ck',
            MESSAGE = 'deterministic_retrieval_language_tag_ck: language_tag is required';
    END IF;

    selected_baseline_code := COALESCE(
        NULLIF(upper(btrim(baseline_code)), ''),
        'D'
    );
    requested_top_k := COALESCE(top_k, 5);
    selected_trigram_threshold := COALESCE(
        trigram_threshold,
        0.35::REAL
    );

    IF requested_top_k NOT BETWEEN 1 AND 100 THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_top_k_ck',
            MESSAGE = 'deterministic_retrieval_top_k_ck: top_k must be between 1 and 100';
    END IF;

    IF selected_trigram_threshold NOT BETWEEN 0::REAL AND 1::REAL THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_threshold_ck',
            MESSAGE = 'deterministic_retrieval_threshold_ck: trigram_threshold must be between zero and one';
    END IF;

    SELECT
        pipeline.normalization_pipeline_id,
        pipeline.language_tag_code
    INTO
        selected_pipeline_id,
        selected_pipeline_language
    FROM corpus.normalization_pipeline AS pipeline
    WHERE pipeline.normalization_pipeline_key =
          btrim($3)
      AND pipeline.frozen_at IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_pipeline_ck',
            MESSAGE = 'deterministic_retrieval_pipeline_ck: retrieval requires a known frozen normalization pipeline';
    END IF;

    IF selected_pipeline_language <> btrim(language_tag) THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_pipeline_language_ck',
            MESSAGE = 'deterministic_retrieval_pipeline_language_ck: pipeline and query language tags differ';
    END IF;

    SELECT maximum_tier.tier_order
    INTO selected_maximum_tier_order
    FROM ref.retrieval_baseline AS baseline
    JOIN ref.retrieval_tier AS maximum_tier
      ON maximum_tier.retrieval_tier_code =
         baseline.maximum_retrieval_tier_code
    WHERE baseline.retrieval_baseline_code = selected_baseline_code;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'deterministic_retrieval_baseline_ck',
            MESSAGE = 'deterministic_retrieval_baseline_ck: baseline_code must be A, B, C, or D';
    END IF;

    IF selected_maximum_tier_order >= 4 THEN
        SELECT policy.retrieval_graph_policy_id
        INTO selected_graph_policy_id
        FROM ml.retrieval_graph_policy AS policy
        WHERE policy.retrieval_graph_policy_key = 'graph_policy.round2b.v1'
          AND policy.is_frozen;

        IF NOT FOUND THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000',
                CONSTRAINT = 'deterministic_retrieval_graph_policy_ck',
                MESSAGE = 'deterministic_retrieval_graph_policy_ck: baseline D requires the frozen Round 2B graph policy';
        END IF;
    END IF;

    normalized_query := corpus.normalize_expression_v1(
        COALESCE(query_text, ''),
        btrim($3)
    );
    candidate_expression_limit := GREATEST(requested_top_k * 4, 20);

    RETURN QUERY
    WITH canonical_dictionary AS (
        SELECT
            normalized.normalized_expression_id,
            normalized.normalized_text,
            expression.expression_id,
            expression.expression_key,
            expression.expression_text,
            lexicalization.lexicalization_id,
            lexicalization.mapping_type_code,
            mapping_type.retrieval_precedence,
            mapping_type.is_preferred,
            mapping_type.is_approved_variant,
            concept.concept_id,
            concept.concept_key,
            concept.concept_type_code
        FROM corpus.normalized_expression AS normalized
        JOIN corpus.lexical_expression_normalization AS expression_normalization
          ON expression_normalization.normalized_expression_id =
             normalized.normalized_expression_id
         AND expression_normalization.normalization_pipeline_id =
             normalized.normalization_pipeline_id
        JOIN kb.lexical_expression AS expression
          ON expression.expression_id =
             expression_normalization.expression_id
         AND expression.lifecycle_status_code = 'active'
         AND expression.language_tag_code = selected_pipeline_language
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id = expression.expression_id
         AND lexicalization.lifecycle_status_code = 'active'
         AND lexicalization.valid_from <= CURRENT_TIMESTAMP
         AND (
                lexicalization.valid_until IS NULL
                OR lexicalization.valid_until > CURRENT_TIMESTAMP
             )
        JOIN ref.mapping_type AS mapping_type
          ON mapping_type.mapping_type_code = lexicalization.mapping_type_code
         AND (
                mapping_type.is_preferred
                OR mapping_type.is_approved_variant
             )
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
         AND concept.lifecycle_status_code = 'active'
        WHERE normalized.normalization_pipeline_id = selected_pipeline_id
    ),
    exact_ranked AS (
        SELECT
            CASE
                WHEN dictionary.is_preferred THEN 'A'::TEXT
                ELSE 'B'::TEXT
            END AS candidate_tier_code,
            CASE
                WHEN dictionary.is_preferred THEN 1
                ELSE 2
            END::INTEGER AS candidate_tier_order,
            dictionary.expression_id,
            dictionary.expression_key,
            dictionary.expression_text,
            dictionary.concept_id,
            dictionary.concept_key,
            dictionary.concept_type_code,
            dictionary.mapping_type_code,
            dictionary.retrieval_precedence,
            (COALESCE(query_text, '') = dictionary.expression_text)
                AS is_raw_surface_exact,
            ROW_NUMBER() OVER (
                PARTITION BY dictionary.concept_id
                ORDER BY
                    CASE WHEN dictionary.is_preferred THEN 1 ELSE 2 END,
                    dictionary.retrieval_precedence,
                    dictionary.expression_key,
                    dictionary.concept_key
            ) AS concept_match_rank
        FROM canonical_dictionary AS dictionary
        WHERE dictionary.normalized_text = normalized_query
          AND (
                (
                    dictionary.is_preferred
                    AND selected_maximum_tier_order >= 1
                ) OR (
                    dictionary.is_approved_variant
                    AND selected_maximum_tier_order >= 2
                )
              )
    ),
    exact_candidates AS (
        SELECT
            exact.candidate_tier_code,
            exact.candidate_tier_order,
            exact.expression_id,
            exact.expression_key,
            exact.concept_id,
            exact.concept_key,
            exact.concept_type_code,
            exact.mapping_type_code,
            exact.retrieval_precedence,
            NULL::REAL AS candidate_trigram_similarity,
            NULL::BIGINT AS source_concept_id,
            NULL::TEXT AS source_concept_key,
            NULL::BIGINT AS source_relation_id,
            NULL::TEXT AS source_relation_type_code,
            NULL::TEXT AS source_traversal_direction,
            0::SMALLINT AS hop_count,
            exact.is_raw_surface_exact,
            TRUE AS is_normalized_phrase_match,
            NULL::SMALLINT AS graph_rule_order
        FROM exact_ranked AS exact
        WHERE exact.concept_match_rank = 1
    ),
    nearest_expressions AS (
        SELECT
            nearest.normalized_expression_id,
            public.similarity(nearest.normalized_text, normalized_query)
                AS candidate_trigram_similarity
        FROM LATERAL (
            SELECT
                normalized.normalized_expression_id,
                normalized.normalized_text,
                normalized.normalized_expression_key
            FROM corpus.normalized_expression AS normalized
            WHERE normalized.normalization_pipeline_id = selected_pipeline_id
              AND normalized_query <> ''
              AND selected_maximum_tier_order >= 3
              AND NOT EXISTS (SELECT 1 FROM exact_candidates)
              AND EXISTS (
                  SELECT 1
                  FROM corpus.lexical_expression_normalization
                       AS expression_normalization
                  JOIN kb.lexical_expression AS expression
                    ON expression.expression_id =
                       expression_normalization.expression_id
                   AND expression.lifecycle_status_code = 'active'
                   AND expression.language_tag_code =
                       selected_pipeline_language
                  JOIN kb.lexicalization AS lexicalization
                    ON lexicalization.expression_id = expression.expression_id
                  JOIN ref.mapping_type AS mapping_type
                    ON mapping_type.mapping_type_code =
                       lexicalization.mapping_type_code
                  JOIN kb.concept AS concept
                    ON concept.concept_id = lexicalization.concept_id
                   AND concept.lifecycle_status_code = 'active'
                  WHERE expression_normalization.normalized_expression_id =
                        normalized.normalized_expression_id
                    AND expression_normalization.normalization_pipeline_id =
                        selected_pipeline_id
                    AND lexicalization.lifecycle_status_code = 'active'
                    AND lexicalization.valid_from <= CURRENT_TIMESTAMP
                    AND (
                          lexicalization.valid_until IS NULL
                          OR lexicalization.valid_until > CURRENT_TIMESTAMP
                        )
                    AND (
                          mapping_type.is_preferred
                          OR mapping_type.is_approved_variant
                        )
              )
            ORDER BY
                normalized.normalized_text
                    OPERATOR(public.<->) normalized_query,
                normalized.normalized_expression_key
            LIMIT candidate_expression_limit
        ) AS nearest
    ),
    trigram_ranked AS (
        SELECT
            'C'::TEXT AS candidate_tier_code,
            3::INTEGER AS candidate_tier_order,
            dictionary.expression_id,
            dictionary.expression_key,
            dictionary.concept_id,
            dictionary.concept_key,
            dictionary.concept_type_code,
            dictionary.mapping_type_code,
            dictionary.retrieval_precedence,
            nearest.candidate_trigram_similarity,
            ROW_NUMBER() OVER (
                PARTITION BY dictionary.concept_id
                ORDER BY
                    nearest.candidate_trigram_similarity DESC,
                    dictionary.retrieval_precedence,
                    dictionary.expression_key,
                    dictionary.concept_key
            ) AS concept_match_rank
        FROM nearest_expressions AS nearest
        JOIN canonical_dictionary AS dictionary
          ON dictionary.normalized_expression_id =
             nearest.normalized_expression_id
        WHERE nearest.candidate_trigram_similarity >=
              selected_trigram_threshold
    ),
    trigram_candidates AS (
        SELECT
            trigram.candidate_tier_code,
            trigram.candidate_tier_order,
            trigram.expression_id,
            trigram.expression_key,
            trigram.concept_id,
            trigram.concept_key,
            trigram.concept_type_code,
            trigram.mapping_type_code,
            trigram.retrieval_precedence,
            trigram.candidate_trigram_similarity,
            NULL::BIGINT AS source_concept_id,
            NULL::TEXT AS source_concept_key,
            NULL::BIGINT AS source_relation_id,
            NULL::TEXT AS source_relation_type_code,
            NULL::TEXT AS source_traversal_direction,
            0::SMALLINT AS hop_count,
            FALSE AS is_raw_surface_exact,
            FALSE AS is_normalized_phrase_match,
            NULL::SMALLINT AS graph_rule_order
        FROM trigram_ranked AS trigram
        WHERE trigram.concept_match_rank = 1
    ),
    direct_candidates AS (
        SELECT * FROM exact_candidates
        UNION ALL
        SELECT * FROM trigram_candidates
    ),
    graph_ranked AS (
        SELECT
            'D'::TEXT AS candidate_tier_code,
            4::INTEGER AS candidate_tier_order,
            NULL::BIGINT AS expression_id,
            NULL::TEXT AS expression_key,
            neighbour.neighbour_concept_id AS concept_id,
            neighbour.neighbour_concept_key AS concept_key,
            neighbour.neighbour_concept_type_code AS concept_type_code,
            NULL::TEXT AS mapping_type_code,
            NULL::SMALLINT AS retrieval_precedence,
            NULL::REAL AS candidate_trigram_similarity,
            seed.concept_id AS source_concept_id,
            seed.concept_key AS source_concept_key,
            neighbour.concept_relation_id AS source_relation_id,
            neighbour.relation_type_code AS source_relation_type_code,
            neighbour.traversal_direction AS source_traversal_direction,
            1::SMALLINT AS hop_count,
            FALSE AS is_raw_surface_exact,
            FALSE AS is_normalized_phrase_match,
            policy_rule.rule_order AS graph_rule_order,
            ROW_NUMBER() OVER (
                PARTITION BY neighbour.neighbour_concept_id
                ORDER BY
                    seed.candidate_tier_order,
                    seed.candidate_trigram_similarity DESC NULLS LAST,
                    seed.retrieval_precedence,
                    seed.expression_key,
                    policy_rule.rule_order,
                    neighbour.relation_key,
                    neighbour.neighbour_concept_key,
                    seed.concept_key
            ) AS concept_path_rank
        FROM direct_candidates AS seed
        JOIN kb.v_concept_neighbours AS neighbour
          ON neighbour.concept_id = seed.concept_id
        JOIN ml.retrieval_graph_policy_rule AS policy_rule
          ON policy_rule.retrieval_graph_policy_id =
             selected_graph_policy_id
         AND policy_rule.relation_type_code = neighbour.relation_type_code
         AND policy_rule.traversal_direction = neighbour.traversal_direction
         AND policy_rule.maximum_hops = 1
        WHERE selected_maximum_tier_order >= 4
          AND NOT EXISTS (
              SELECT 1
              FROM direct_candidates AS direct
              WHERE direct.concept_id = neighbour.neighbour_concept_id
          )
    ),
    graph_candidates AS (
        SELECT
            graph.candidate_tier_code,
            graph.candidate_tier_order,
            graph.expression_id,
            graph.expression_key,
            graph.concept_id,
            graph.concept_key,
            graph.concept_type_code,
            graph.mapping_type_code,
            graph.retrieval_precedence,
            graph.candidate_trigram_similarity,
            graph.source_concept_id,
            graph.source_concept_key,
            graph.source_relation_id,
            graph.source_relation_type_code,
            graph.source_traversal_direction,
            graph.hop_count,
            graph.is_raw_surface_exact,
            graph.is_normalized_phrase_match,
            graph.graph_rule_order
        FROM graph_ranked AS graph
        WHERE graph.concept_path_rank = 1
    ),
    all_candidates AS (
        SELECT * FROM direct_candidates
        UNION ALL
        SELECT * FROM graph_candidates
    ),
    ranked_candidates AS (
        SELECT
            candidate.*,
            ROW_NUMBER() OVER (
                ORDER BY
                    candidate.candidate_tier_order,
                    candidate.candidate_trigram_similarity DESC NULLS LAST,
                    candidate.retrieval_precedence NULLS LAST,
                    candidate.expression_key NULLS LAST,
                    candidate.graph_rule_order NULLS LAST,
                    candidate.source_concept_key NULLS LAST,
                    candidate.source_relation_id NULLS LAST,
                    candidate.concept_key
            )::INTEGER AS final_candidate_rank
        FROM all_candidates AS candidate
    ),
    limited_candidates AS (
        SELECT *
        FROM ranked_candidates AS ranked
        WHERE ranked.final_candidate_rank <= requested_top_k
    ),
    direct_summary AS (
        SELECT count(*)::BIGINT AS direct_candidate_count
        FROM direct_candidates
    ),
    candidate_results AS (
        SELECT
            CASE
                WHEN candidate.candidate_tier_code IN ('A', 'B')
                 AND summary.direct_candidate_count = 1
                    THEN 'RESOLVED'::TEXT
                ELSE 'CANDIDATE'::TEXT
            END AS result_status_code,
            candidate.final_candidate_rank,
            candidate.candidate_tier_code,
            candidate.candidate_tier_order,
            candidate.expression_id,
            candidate.expression_key,
            candidate.concept_id,
            candidate.concept_key,
            candidate.concept_type_code,
            candidate.mapping_type_code,
            candidate.candidate_trigram_similarity,
            candidate.source_concept_id,
            candidate.source_concept_key,
            candidate.source_relation_id,
            candidate.source_relation_type_code,
            candidate.source_traversal_direction,
            candidate.hop_count,
            candidate.is_raw_surface_exact,
            candidate.is_normalized_phrase_match,
            CASE candidate.candidate_tier_code
                WHEN 'A' THEN
                    jsonb_build_array(
                        jsonb_build_object(
                            'signal_code', 'normalized_phrase_match',
                            'value', TRUE
                        )
                    ) || CASE
                        WHEN candidate.is_raw_surface_exact THEN
                            jsonb_build_array(
                                jsonb_build_object(
                                    'signal_code', 'raw_surface_exact',
                                    'value', TRUE
                                )
                            )
                        ELSE '[]'::JSONB
                    END
                WHEN 'B' THEN
                    jsonb_build_array(
                        jsonb_build_object(
                            'signal_code', 'normalized_phrase_match',
                            'value', TRUE
                        ),
                        jsonb_build_object(
                            'signal_code', 'approved_variant_match',
                            'value', TRUE
                        )
                    ) || CASE
                        WHEN candidate.is_raw_surface_exact THEN
                            jsonb_build_array(
                                jsonb_build_object(
                                    'signal_code', 'raw_surface_exact',
                                    'value', TRUE
                                )
                            )
                        ELSE '[]'::JSONB
                    END
                WHEN 'C' THEN
                    jsonb_build_array(
                        jsonb_build_object(
                            'signal_code', 'pg_trgm_similarity',
                            'value', candidate.candidate_trigram_similarity,
                            'value_semantics', 'orthographic similarity only'
                        )
                    )
                ELSE
                    jsonb_build_array(
                        jsonb_build_object(
                            'signal_code', 'typed_graph_hop',
                            'value', candidate.hop_count,
                            'relation_type_code',
                                candidate.source_relation_type_code,
                            'traversal_direction',
                                candidate.source_traversal_direction,
                            'source_concept_key',
                                candidate.source_concept_key
                        )
                    )
            END AS result_signal_ledger
        FROM limited_candidates AS candidate
        CROSS JOIN direct_summary AS summary
    ),
    unresolved_result AS (
        SELECT
            'UNRESOLVED'::TEXT AS result_status_code,
            NULL::INTEGER AS final_candidate_rank,
            NULL::TEXT AS candidate_tier_code,
            NULL::INTEGER AS candidate_tier_order,
            NULL::BIGINT AS expression_id,
            NULL::TEXT AS expression_key,
            NULL::BIGINT AS concept_id,
            NULL::TEXT AS concept_key,
            NULL::TEXT AS concept_type_code,
            NULL::TEXT AS mapping_type_code,
            NULL::REAL AS candidate_trigram_similarity,
            NULL::BIGINT AS source_concept_id,
            NULL::TEXT AS source_concept_key,
            NULL::BIGINT AS source_relation_id,
            NULL::TEXT AS source_relation_type_code,
            NULL::TEXT AS source_traversal_direction,
            NULL::SMALLINT AS hop_count,
            FALSE AS is_raw_surface_exact,
            FALSE AS is_normalized_phrase_match,
            jsonb_build_array(
                jsonb_build_object(
                    'signal_code', 'unresolved',
                    'value_semantics',
                        'No candidate survived the selected ordinal baseline.'
                )
            ) AS result_signal_ledger
        WHERE NOT EXISTS (SELECT 1 FROM limited_candidates)
    ),
    complete_result AS (
        SELECT * FROM candidate_results
        UNION ALL
        SELECT * FROM unresolved_result
    )
    SELECT
        result.result_status_code,
        result.final_candidate_rank,
        result.candidate_tier_code,
        result.candidate_tier_order,
        result.expression_id,
        result.expression_key,
        result.concept_id,
        result.concept_key,
        result.concept_type_code,
        result.mapping_type_code,
        result.candidate_trigram_similarity,
        result.source_concept_id,
        result.source_concept_key,
        result.source_relation_id,
        result.source_relation_type_code,
        result.source_traversal_direction,
        result.hop_count,
        result.is_raw_surface_exact,
        result.is_normalized_phrase_match,
        result.result_signal_ledger
    FROM complete_result AS result
    ORDER BY result.final_candidate_rank NULLS LAST;
END;
$retrieve_deterministic_candidates$;

COMMENT ON FUNCTION ml.retrieve_deterministic_candidates(
    TEXT,
    TEXT,
    TEXT,
    TEXT,
    INTEGER,
    REAL
) IS
    'Versioned deterministic A/B/C/D retrieval with mandatory normalization, approved exact/variant precedence, canonical-dictionary trigram fallback, one-hop allowlisted graph expansion, an explicit signal ledger, global top-K, and exactly one UNRESOLVED row when empty. No embedding, LLM, weighted aggregate, automatic ontology promotion, or sensory-similarity claim is made.';

CREATE VIEW ml.v_deterministic_candidate_signal_ledger AS
SELECT
    inference.mapping_inference_id,
    inference.mapping_inference_key,
    candidate.mapping_candidate_id,
    candidate.mapping_candidate_key,
    candidate.rank AS candidate_rank,
    concept.concept_id,
    concept.concept_key,
    trace.retrieval_tier_code,
    trace.matched_expression_id,
    trace.seed_mapping_candidate_id,
    trace.concept_relation_id,
    trace.traversal_direction,
    trace.graph_hop_count,
    typed_signal.signal_ordinal,
    typed_signal.retrieval_signal_code,
    signal_type.signal_domain_code,
    candidate_signal.signal_value,
    candidate_signal.value_semantics,
    method.method_key,
    dataset.dataset_key,
    scale.scale_key,
    candidate_signal.context
FROM ml.deterministic_candidate_trace AS trace
JOIN ml.mapping_candidate AS candidate
  ON candidate.mapping_candidate_id = trace.mapping_candidate_id
JOIN ml.mapping_inference AS inference
  ON inference.mapping_inference_id = candidate.mapping_inference_id
JOIN kb.concept AS concept
  ON concept.concept_id = candidate.concept_id
JOIN ml.deterministic_candidate_signal AS typed_signal
  ON typed_signal.mapping_candidate_id = trace.mapping_candidate_id
JOIN ref.retrieval_signal AS signal_type
  ON signal_type.retrieval_signal_code = typed_signal.retrieval_signal_code
JOIN ml.candidate_signal AS candidate_signal
  ON candidate_signal.candidate_signal_id = typed_signal.candidate_signal_id
JOIN evidence.statistical_method AS method
  ON method.statistical_method_id = candidate_signal.statistical_method_id
JOIN evidence.dataset AS dataset
  ON dataset.dataset_id = candidate_signal.dataset_id
JOIN evidence.measurement_scale AS scale
  ON scale.measurement_scale_id = candidate_signal.measurement_scale_id;

COMMENT ON VIEW ml.v_deterministic_candidate_signal_ledger IS
    'Explainable deterministic candidate paths and their separate versioned signals; no aggregate score is calculated.';

CREATE INDEX deterministic_candidate_trace_seed_idx
    ON ml.deterministic_candidate_trace (
        seed_mapping_candidate_id,
        mapping_candidate_id
    )
    WHERE seed_mapping_candidate_id IS NOT NULL;

CREATE INDEX retrieval_graph_policy_rule_lookup_idx
    ON ml.retrieval_graph_policy_rule (
        retrieval_graph_policy_id,
        relation_type_code,
        traversal_direction,
        rule_order
    );

CREATE FUNCTION ml.guard_terminal_deterministic_run_output()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_terminal_deterministic_run_output$
DECLARE
    old_run_id BIGINT;
    new_run_id BIGINT;
    run_is_terminal BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'model_run' THEN
        IF EXISTS (
            SELECT 1
            FROM ml.deterministic_retrieval_run AS deterministic_run
            JOIN ref.model_run_status AS status
              ON status.model_run_status_code = OLD.model_run_status_code
             AND status.is_terminal
            WHERE deterministic_run.model_run_id = OLD.model_run_id
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000',
                CONSTRAINT = 'deterministic_model_run_terminal_ck',
                MESSAGE = 'deterministic_model_run_terminal_ck: a terminal deterministic model run is immutable';
        END IF;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    ELSIF TG_TABLE_NAME = 'deterministic_retrieval_run' THEN
        IF TG_OP <> 'INSERT' THEN old_run_id := OLD.model_run_id; END IF;
        IF TG_OP <> 'DELETE' THEN new_run_id := NEW.model_run_id; END IF;
    ELSIF TG_TABLE_NAME = 'mapping_inference' THEN
        IF TG_OP <> 'INSERT' THEN old_run_id := OLD.model_run_id; END IF;
        IF TG_OP <> 'DELETE' THEN new_run_id := NEW.model_run_id; END IF;
    ELSIF TG_TABLE_NAME = 'mapping_candidate' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT inference.model_run_id INTO old_run_id
            FROM ml.mapping_inference AS inference
            WHERE inference.mapping_inference_id = OLD.mapping_inference_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT inference.model_run_id INTO new_run_id
            FROM ml.mapping_inference AS inference
            WHERE inference.mapping_inference_id = NEW.mapping_inference_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'deterministic_candidate_trace' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT inference.model_run_id INTO old_run_id
            FROM ml.mapping_candidate AS candidate
            JOIN ml.mapping_inference AS inference
              ON inference.mapping_inference_id = candidate.mapping_inference_id
            WHERE candidate.mapping_candidate_id = OLD.mapping_candidate_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT inference.model_run_id INTO new_run_id
            FROM ml.mapping_candidate AS candidate
            JOIN ml.mapping_inference AS inference
              ON inference.mapping_inference_id = candidate.mapping_inference_id
            WHERE candidate.mapping_candidate_id = NEW.mapping_candidate_id;
        END IF;
    ELSE
        IF TG_OP <> 'INSERT' THEN
            SELECT inference.model_run_id INTO old_run_id
            FROM ml.mapping_candidate AS candidate
            JOIN ml.mapping_inference AS inference
              ON inference.mapping_inference_id = candidate.mapping_inference_id
            WHERE candidate.mapping_candidate_id = OLD.mapping_candidate_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT inference.model_run_id INTO new_run_id
            FROM ml.mapping_candidate AS candidate
            JOIN ml.mapping_inference AS inference
              ON inference.mapping_inference_id = candidate.mapping_inference_id
            WHERE candidate.mapping_candidate_id = NEW.mapping_candidate_id;
        END IF;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM ml.model_run AS model_run
        JOIN ref.model_run_status AS status
          ON status.model_run_status_code = model_run.model_run_status_code
         AND status.is_terminal
        WHERE model_run.model_run_id IN (old_run_id, new_run_id)
          AND (
                TG_TABLE_NAME = 'deterministic_retrieval_run'
                OR EXISTS (
                    SELECT 1
                    FROM ml.deterministic_retrieval_run AS deterministic_run
                    WHERE deterministic_run.model_run_id =
                          model_run.model_run_id
                )
              )
    ) INTO run_is_terminal;

    IF COALESCE(run_is_terminal, FALSE) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'deterministic_run_output_terminal_ck',
            MESSAGE = 'deterministic_run_output_terminal_ck: outputs of a terminal deterministic run cannot be inserted, updated, deleted, or moved';
    END IF;

    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$guard_terminal_deterministic_run_output$;

CREATE TRIGGER deterministic_model_run_terminal_bud
BEFORE UPDATE OR DELETE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE TRIGGER deterministic_retrieval_run_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.deterministic_retrieval_run
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE TRIGGER deterministic_mapping_inference_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.mapping_inference
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE TRIGGER deterministic_mapping_candidate_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.mapping_candidate
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE TRIGGER deterministic_candidate_trace_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.deterministic_candidate_trace
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE TRIGGER deterministic_candidate_signal_source_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.candidate_signal
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE TRIGGER deterministic_candidate_signal_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.deterministic_candidate_signal
FOR EACH ROW EXECUTE FUNCTION ml.guard_terminal_deterministic_run_output();

CREATE FUNCTION ml.guard_used_deterministic_model_version()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_used_deterministic_model_version$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM ml.model_run AS model_run
        JOIN ref.model_run_status AS status
          ON status.model_run_status_code = model_run.model_run_status_code
         AND status.is_terminal
        JOIN ml.deterministic_retrieval_run AS deterministic_run
          ON deterministic_run.model_run_id = model_run.model_run_id
        WHERE model_run.model_version_id = OLD.model_version_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'deterministic_model_version_used_ck',
            MESSAGE = 'deterministic_model_version_used_ck: a model version used by a terminal deterministic run is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$guard_used_deterministic_model_version$;

CREATE TRIGGER deterministic_model_version_used_bud
BEFORE UPDATE OR DELETE ON ml.model_version
FOR EACH ROW EXECUTE FUNCTION ml.guard_used_deterministic_model_version();

CREATE TABLE audit.retrieval_audit_set (
    retrieval_audit_set_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_audit_set_key TEXT NOT NULL,
    corpus_snapshot_id BIGINT NOT NULL,
    version_label TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    sampling_configuration JSONB NOT NULL,
    inventory_sha256 TEXT NOT NULL,
    code_commit_sha TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    frozen_at TIMESTAMPTZ,
    CONSTRAINT retrieval_audit_set_pk PRIMARY KEY (retrieval_audit_set_id),
    CONSTRAINT retrieval_audit_set_key_uq UNIQUE (retrieval_audit_set_key),
    CONSTRAINT retrieval_audit_set_name_version_uq UNIQUE (name, version_label),
    CONSTRAINT retrieval_audit_set_snapshot_fk FOREIGN KEY (corpus_snapshot_id)
        REFERENCES corpus.corpus_snapshot (corpus_snapshot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_audit_set_key_nonempty_ck CHECK (
        retrieval_audit_set_key = btrim(retrieval_audit_set_key)
        AND retrieval_audit_set_key <> ''
    ),
    CONSTRAINT retrieval_audit_set_version_nonempty_ck CHECK (
        version_label = btrim(version_label) AND version_label <> ''
    ),
    CONSTRAINT retrieval_audit_set_name_nonempty_ck CHECK (
        name = btrim(name) AND name <> ''
    ),
    CONSTRAINT retrieval_audit_set_description_nonempty_ck CHECK (
        description = btrim(description) AND description <> ''
    ),
    CONSTRAINT retrieval_audit_set_sampling_configuration_object_ck CHECK (
        jsonb_typeof(sampling_configuration) = 'object'
    ),
    CONSTRAINT retrieval_audit_set_inventory_sha256_ck CHECK (
        inventory_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT retrieval_audit_set_code_commit_sha_ck CHECK (
        code_commit_sha ~ '^[0-9a-f]{40}([0-9a-f]{24})?$'
    ),
    CONSTRAINT retrieval_audit_set_freeze_order_ck CHECK (
        frozen_at IS NULL OR frozen_at >= created_at
    )
);

CREATE TABLE audit.retrieval_audit_case (
    retrieval_audit_case_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_audit_case_key TEXT NOT NULL,
    retrieval_audit_set_id BIGINT NOT NULL,
    expression_id BIGINT NOT NULL,
    representative_observation_expression_id BIGINT NOT NULL,
    audit_split_code TEXT NOT NULL,
    case_ordinal INTEGER NOT NULL,
    notes TEXT,
    CONSTRAINT retrieval_audit_case_pk PRIMARY KEY (retrieval_audit_case_id),
    CONSTRAINT retrieval_audit_case_key_uq UNIQUE (retrieval_audit_case_key),
    CONSTRAINT retrieval_audit_case_set_expression_uq UNIQUE (
        retrieval_audit_set_id,
        expression_id
    ),
    CONSTRAINT retrieval_audit_case_set_ordinal_uq UNIQUE (
        retrieval_audit_set_id,
        case_ordinal
    ),
    CONSTRAINT retrieval_audit_case_set_fk FOREIGN KEY (
        retrieval_audit_set_id
    ) REFERENCES audit.retrieval_audit_set (retrieval_audit_set_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_audit_case_expression_fk FOREIGN KEY (expression_id)
        REFERENCES kb.lexical_expression (expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_audit_case_observation_expression_fk FOREIGN KEY (
        representative_observation_expression_id
    ) REFERENCES corpus.observation_expression (observation_expression_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_audit_case_split_fk FOREIGN KEY (audit_split_code)
        REFERENCES ref.audit_split (audit_split_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_audit_case_key_nonempty_ck CHECK (
        retrieval_audit_case_key = btrim(retrieval_audit_case_key)
        AND retrieval_audit_case_key <> ''
    ),
    CONSTRAINT retrieval_audit_case_ordinal_positive_ck CHECK (
        case_ordinal > 0
    ),
    CONSTRAINT retrieval_audit_case_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE audit.retrieval_audit_case_stratum (
    retrieval_audit_case_id BIGINT NOT NULL,
    retrieval_audit_stratum_code TEXT NOT NULL,
    CONSTRAINT retrieval_audit_case_stratum_pk PRIMARY KEY (
        retrieval_audit_case_id,
        retrieval_audit_stratum_code
    ),
    CONSTRAINT retrieval_audit_case_stratum_case_fk FOREIGN KEY (
        retrieval_audit_case_id
    ) REFERENCES audit.retrieval_audit_case (retrieval_audit_case_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_audit_case_stratum_code_fk FOREIGN KEY (
        retrieval_audit_stratum_code
    ) REFERENCES ref.retrieval_audit_stratum (retrieval_audit_stratum_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE audit.retrieval_case_review (
    retrieval_case_review_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_case_review_key TEXT NOT NULL,
    retrieval_audit_case_id BIGINT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    audit_review_role_code TEXT NOT NULL,
    expects_unresolved BOOLEAN NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    CONSTRAINT retrieval_case_review_pk PRIMARY KEY (
        retrieval_case_review_id
    ),
    CONSTRAINT retrieval_case_review_key_uq UNIQUE (
        retrieval_case_review_key
    ),
    CONSTRAINT retrieval_case_review_reviewer_role_uq UNIQUE (
        retrieval_audit_case_id,
        reviewer_id,
        audit_review_role_code
    ),
    CONSTRAINT retrieval_case_review_case_fk FOREIGN KEY (
        retrieval_audit_case_id
    ) REFERENCES audit.retrieval_audit_case (retrieval_audit_case_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_case_review_reviewer_fk FOREIGN KEY (reviewer_id)
        REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_case_review_role_fk FOREIGN KEY (
        audit_review_role_code
    ) REFERENCES ref.audit_review_role (audit_review_role_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_case_review_key_nonempty_ck CHECK (
        retrieval_case_review_key = btrim(retrieval_case_review_key)
        AND retrieval_case_review_key <> ''
    ),
    CONSTRAINT retrieval_case_review_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE UNIQUE INDEX retrieval_case_one_adjudicated_review_idx
    ON audit.retrieval_case_review (retrieval_audit_case_id)
    WHERE audit_review_role_code = 'adjudicated';

CREATE TABLE audit.retrieval_relevance_judgment (
    retrieval_relevance_judgment_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_relevance_judgment_key TEXT NOT NULL,
    retrieval_case_review_id BIGINT NOT NULL,
    concept_id BIGINT NOT NULL,
    relevance_grade_code TEXT NOT NULL,
    rationale TEXT NOT NULL,
    CONSTRAINT retrieval_relevance_judgment_pk PRIMARY KEY (
        retrieval_relevance_judgment_id
    ),
    CONSTRAINT retrieval_relevance_judgment_key_uq UNIQUE (
        retrieval_relevance_judgment_key
    ),
    CONSTRAINT retrieval_relevance_judgment_review_concept_uq UNIQUE (
        retrieval_case_review_id,
        concept_id
    ),
    CONSTRAINT retrieval_relevance_judgment_review_fk FOREIGN KEY (
        retrieval_case_review_id
    ) REFERENCES audit.retrieval_case_review (retrieval_case_review_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_relevance_judgment_concept_fk FOREIGN KEY (concept_id)
        REFERENCES kb.concept (concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_relevance_judgment_grade_fk FOREIGN KEY (
        relevance_grade_code
    ) REFERENCES ref.relevance_grade (relevance_grade_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_relevance_judgment_candidate_grade_ck CHECK (
        relevance_grade_code IN ('0', '1', '2', '3')
    ),
    CONSTRAINT retrieval_relevance_judgment_rationale_nonempty_ck CHECK (
        rationale = btrim(rationale) AND rationale <> ''
    )
);

CREATE INDEX retrieval_audit_case_split_idx
    ON audit.retrieval_audit_case (
        retrieval_audit_set_id,
        audit_split_code,
        case_ordinal
    );

CREATE INDEX retrieval_case_review_case_role_idx
    ON audit.retrieval_case_review (
        retrieval_audit_case_id,
        audit_review_role_code,
        retrieval_case_review_id
    );

CREATE INDEX retrieval_relevance_judgment_review_grade_idx
    ON audit.retrieval_relevance_judgment (
        retrieval_case_review_id,
        relevance_grade_code,
        concept_id
    );

CREATE FUNCTION audit.guard_frozen_retrieval_audit_inventory()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_retrieval_audit_inventory$
DECLARE
    old_set_id BIGINT;
    new_set_id BIGINT;
    old_set_is_frozen BOOLEAN;
    new_set_is_frozen BOOLEAN;
BEGIN
    IF TG_TABLE_NAME = 'retrieval_audit_set' THEN
        IF TG_OP <> 'INSERT' AND OLD.frozen_at IS NOT NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '55000',
                CONSTRAINT = 'retrieval_audit_set_frozen_ck',
                MESSAGE = 'retrieval_audit_set_frozen_ck: a frozen audit-set inventory cannot be updated or deleted';
        END IF;
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;

        IF NEW.frozen_at IS NOT NULL THEN
            IF NOT EXISTS (
                SELECT 1
                FROM corpus.corpus_snapshot AS snapshot
                WHERE snapshot.corpus_snapshot_id = NEW.corpus_snapshot_id
                  AND snapshot.frozen_at IS NOT NULL
            ) THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'retrieval_audit_set_snapshot_frozen_ck',
                    MESSAGE = 'retrieval_audit_set_snapshot_frozen_ck: a frozen audit set requires a frozen corpus snapshot';
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM audit.retrieval_audit_case AS audit_case
                WHERE audit_case.retrieval_audit_set_id =
                      NEW.retrieval_audit_set_id
            ) THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'retrieval_audit_set_nonempty_ck',
                    MESSAGE = 'retrieval_audit_set_nonempty_ck: a frozen audit set requires at least one case';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM audit.retrieval_audit_case AS audit_case
                WHERE audit_case.retrieval_audit_set_id =
                      NEW.retrieval_audit_set_id
                  AND NOT EXISTS (
                      SELECT 1
                      FROM audit.retrieval_audit_case_stratum AS stratum
                      WHERE stratum.retrieval_audit_case_id =
                            audit_case.retrieval_audit_case_id
                  )
            ) THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'retrieval_audit_set_strata_complete_ck',
                    MESSAGE = 'retrieval_audit_set_strata_complete_ck: every frozen audit case requires at least one declared stratum';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM audit.retrieval_audit_case AS audit_case
                WHERE audit_case.retrieval_audit_set_id =
                      NEW.retrieval_audit_set_id
                  AND NOT EXISTS (
                      SELECT 1
                      FROM audit.retrieval_case_review AS review
                      WHERE review.retrieval_audit_case_id =
                            audit_case.retrieval_audit_case_id
                        AND review.audit_review_role_code = 'adjudicated'
                  )
            ) THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'retrieval_audit_set_adjudication_complete_ck',
                    MESSAGE = 'retrieval_audit_set_adjudication_complete_ck: every frozen audit case requires one adjudicated review';
            END IF;

            IF EXISTS (
                SELECT 1
                FROM audit.retrieval_audit_case AS audit_case
                LEFT JOIN audit.retrieval_case_review AS review
                  ON review.retrieval_audit_case_id =
                     audit_case.retrieval_audit_case_id
                 AND review.audit_review_role_code = 'independent'
                WHERE audit_case.retrieval_audit_set_id =
                      NEW.retrieval_audit_set_id
                  AND audit_case.audit_split_code = 'held_out'
                GROUP BY audit_case.retrieval_audit_case_id
                HAVING count(DISTINCT review.reviewer_id) < 2
            ) THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'retrieval_audit_set_heldout_reviewers_ck',
                    MESSAGE = 'retrieval_audit_set_heldout_reviewers_ck: every held-out case requires two independent reviewers before freeze';
            END IF;
        END IF;

        RETURN NEW;
    END IF;

    IF TG_TABLE_NAME = 'retrieval_audit_case' THEN
        IF TG_OP <> 'INSERT' THEN
            old_set_id := OLD.retrieval_audit_set_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_set_id := NEW.retrieval_audit_set_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'retrieval_audit_case_stratum' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT audit_case.retrieval_audit_set_id INTO old_set_id
            FROM audit.retrieval_audit_case AS audit_case
            WHERE audit_case.retrieval_audit_case_id =
                  OLD.retrieval_audit_case_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT audit_case.retrieval_audit_set_id INTO new_set_id
            FROM audit.retrieval_audit_case AS audit_case
            WHERE audit_case.retrieval_audit_case_id =
                  NEW.retrieval_audit_case_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'retrieval_case_review' THEN
        IF TG_OP <> 'INSERT' THEN
            SELECT audit_case.retrieval_audit_set_id INTO old_set_id
            FROM audit.retrieval_audit_case AS audit_case
            WHERE audit_case.retrieval_audit_case_id =
                  OLD.retrieval_audit_case_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT audit_case.retrieval_audit_set_id INTO new_set_id
            FROM audit.retrieval_audit_case AS audit_case
            WHERE audit_case.retrieval_audit_case_id =
                  NEW.retrieval_audit_case_id;
        END IF;
    ELSE
        IF TG_OP <> 'INSERT' THEN
            SELECT audit_case.retrieval_audit_set_id INTO old_set_id
            FROM audit.retrieval_case_review AS review
            JOIN audit.retrieval_audit_case AS audit_case
              ON audit_case.retrieval_audit_case_id =
                 review.retrieval_audit_case_id
            WHERE review.retrieval_case_review_id =
                  OLD.retrieval_case_review_id;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT audit_case.retrieval_audit_set_id INTO new_set_id
            FROM audit.retrieval_case_review AS review
            JOIN audit.retrieval_audit_case AS audit_case
              ON audit_case.retrieval_audit_case_id =
                 review.retrieval_audit_case_id
            WHERE review.retrieval_case_review_id =
                  NEW.retrieval_case_review_id;
        END IF;
    END IF;

    IF old_set_id IS NOT NULL THEN
        SELECT audit_set.frozen_at IS NOT NULL INTO old_set_is_frozen
        FROM audit.retrieval_audit_set AS audit_set
        WHERE audit_set.retrieval_audit_set_id = old_set_id;
    END IF;
    IF new_set_id IS NOT NULL THEN
        SELECT audit_set.frozen_at IS NOT NULL INTO new_set_is_frozen
        FROM audit.retrieval_audit_set AS audit_set
        WHERE audit_set.retrieval_audit_set_id = new_set_id;
    END IF;

    IF COALESCE(old_set_is_frozen, FALSE)
       OR COALESCE(new_set_is_frozen, FALSE) THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'retrieval_audit_inventory_frozen_ck',
            MESSAGE = 'retrieval_audit_inventory_frozen_ck: cases, strata, reviews, and judgments of a frozen audit set cannot change';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$guard_frozen_retrieval_audit_inventory$;

CREATE TRIGGER retrieval_audit_set_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_audit_set
FOR EACH ROW
EXECUTE FUNCTION audit.guard_frozen_retrieval_audit_inventory();

CREATE TRIGGER retrieval_audit_case_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_audit_case
FOR EACH ROW
EXECUTE FUNCTION audit.guard_frozen_retrieval_audit_inventory();

CREATE TRIGGER retrieval_audit_case_stratum_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_audit_case_stratum
FOR EACH ROW
EXECUTE FUNCTION audit.guard_frozen_retrieval_audit_inventory();

CREATE TRIGGER retrieval_case_review_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_case_review
FOR EACH ROW
EXECUTE FUNCTION audit.guard_frozen_retrieval_audit_inventory();

CREATE TRIGGER retrieval_relevance_judgment_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_relevance_judgment
FOR EACH ROW
EXECUTE FUNCTION audit.guard_frozen_retrieval_audit_inventory();

CREATE FUNCTION audit.enforce_retrieval_audit_case_source()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_retrieval_audit_case_source$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM corpus.observation_expression AS occurrence
        JOIN corpus.raw_observation AS observation
          ON observation.raw_observation_id = occurrence.raw_observation_id
        JOIN corpus.captured_document AS document
          ON document.captured_document_id = observation.captured_document_id
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.corpus_id = document.corpus_id
        WHERE occurrence.observation_expression_id =
              NEW.representative_observation_expression_id
          AND occurrence.expression_id = NEW.expression_id
          AND snapshot.corpus_snapshot_id = (
              SELECT audit_set.corpus_snapshot_id
              FROM audit.retrieval_audit_set AS audit_set
              WHERE audit_set.retrieval_audit_set_id =
                    NEW.retrieval_audit_set_id
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_audit_case_source_ck',
            MESSAGE = 'retrieval_audit_case_source_ck: representative occurrence must use the case expression and belong to the audit-set corpus snapshot';
    END IF;

    RETURN NEW;
END;
$enforce_retrieval_audit_case_source$;

CREATE TRIGGER retrieval_audit_case_source_biu
BEFORE INSERT OR UPDATE
ON audit.retrieval_audit_case
FOR EACH ROW
EXECUTE FUNCTION audit.enforce_retrieval_audit_case_source();

CREATE FUNCTION audit.enforce_retrieval_case_review_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_retrieval_case_review_semantics$
DECLARE
    review_ids BIGINT[];
    checked_review_id BIGINT;
    checked_expects_unresolved BOOLEAN;
    positive_grade_count BIGINT;
BEGIN
    IF TG_TABLE_NAME = 'retrieval_case_review' THEN
        review_ids := ARRAY[NEW.retrieval_case_review_id];
    ELSIF TG_OP = 'INSERT' THEN
        review_ids := ARRAY[NEW.retrieval_case_review_id];
    ELSIF TG_OP = 'DELETE' THEN
        review_ids := ARRAY[OLD.retrieval_case_review_id];
    ELSE
        review_ids := ARRAY[
            OLD.retrieval_case_review_id,
            NEW.retrieval_case_review_id
        ];
    END IF;

    FOREACH checked_review_id IN ARRAY review_ids LOOP
        SELECT
            review.expects_unresolved,
            count(judgment.retrieval_relevance_judgment_id) FILTER (
                WHERE grade.ordinal_value >= 2
            )
        INTO
            checked_expects_unresolved,
            positive_grade_count
        FROM audit.retrieval_case_review AS review
        LEFT JOIN audit.retrieval_relevance_judgment AS judgment
          ON judgment.retrieval_case_review_id = review.retrieval_case_review_id
        LEFT JOIN ref.relevance_grade AS grade
          ON grade.relevance_grade_code = judgment.relevance_grade_code
        WHERE review.retrieval_case_review_id = checked_review_id
        GROUP BY review.expects_unresolved;

        IF NOT FOUND THEN
            CONTINUE;
        END IF;

        IF checked_expects_unresolved AND positive_grade_count <> 0 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'retrieval_case_review_unresolved_ck',
                MESSAGE = 'retrieval_case_review_unresolved_ck: an unresolved review cannot assign grade 2 or 3';
        ELSIF NOT checked_expects_unresolved AND positive_grade_count < 1 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'retrieval_case_review_resolvable_ck',
                MESSAGE = 'retrieval_case_review_resolvable_ck: a resolvable review requires at least one grade-2-or-3 concept';
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_retrieval_case_review_semantics$;

CREATE CONSTRAINT TRIGGER retrieval_case_review_semantics_review_ct
AFTER INSERT OR UPDATE
ON audit.retrieval_case_review
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION audit.enforce_retrieval_case_review_semantics();

CREATE CONSTRAINT TRIGGER retrieval_case_review_semantics_judgment_ct
AFTER INSERT OR UPDATE OR DELETE
ON audit.retrieval_relevance_judgment
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION audit.enforce_retrieval_case_review_semantics();

CREATE TABLE audit.retrieval_evaluation (
    retrieval_evaluation_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_evaluation_key TEXT NOT NULL,
    retrieval_audit_set_id BIGINT NOT NULL,
    model_run_id BIGINT NOT NULL,
    audit_split_code TEXT NOT NULL,
    evaluated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    evaluation_configuration JSONB NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    notes TEXT,
    CONSTRAINT retrieval_evaluation_pk PRIMARY KEY (retrieval_evaluation_id),
    CONSTRAINT retrieval_evaluation_key_uq UNIQUE (retrieval_evaluation_key),
    CONSTRAINT retrieval_evaluation_scope_uq UNIQUE (
        retrieval_audit_set_id,
        model_run_id,
        audit_split_code
    ),
    CONSTRAINT retrieval_evaluation_set_fk FOREIGN KEY (
        retrieval_audit_set_id
    ) REFERENCES audit.retrieval_audit_set (retrieval_audit_set_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_evaluation_run_fk FOREIGN KEY (model_run_id)
        REFERENCES ml.deterministic_retrieval_run (model_run_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_evaluation_split_fk FOREIGN KEY (audit_split_code)
        REFERENCES ref.audit_split (audit_split_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_evaluation_key_nonempty_ck CHECK (
        retrieval_evaluation_key = btrim(retrieval_evaluation_key)
        AND retrieval_evaluation_key <> ''
    ),
    CONSTRAINT retrieval_evaluation_configuration_object_ck CHECK (
        jsonb_typeof(evaluation_configuration) = 'object'
    ),
    CONSTRAINT retrieval_evaluation_configuration_sha256_ck CHECK (
        configuration_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT retrieval_evaluation_notes_nonempty_ck CHECK (
        notes IS NULL OR (notes = btrim(notes) AND notes <> '')
    )
);

CREATE TABLE audit.retrieval_metric_value (
    retrieval_metric_value_id BIGINT GENERATED ALWAYS AS IDENTITY,
    retrieval_metric_value_key TEXT NOT NULL,
    retrieval_evaluation_id BIGINT NOT NULL,
    retrieval_metric_code TEXT NOT NULL,
    cutoff_k SMALLINT NOT NULL DEFAULT 0,
    numerator NUMERIC,
    denominator NUMERIC,
    metric_value NUMERIC,
    value_semantics TEXT NOT NULL,
    CONSTRAINT retrieval_metric_value_pk PRIMARY KEY (
        retrieval_metric_value_id
    ),
    CONSTRAINT retrieval_metric_value_key_uq UNIQUE (
        retrieval_metric_value_key
    ),
    CONSTRAINT retrieval_metric_value_scope_uq UNIQUE (
        retrieval_evaluation_id,
        retrieval_metric_code,
        cutoff_k
    ),
    CONSTRAINT retrieval_metric_value_evaluation_fk FOREIGN KEY (
        retrieval_evaluation_id
    ) REFERENCES audit.retrieval_evaluation (retrieval_evaluation_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_metric_value_metric_fk FOREIGN KEY (
        retrieval_metric_code
    ) REFERENCES ref.retrieval_metric (retrieval_metric_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT retrieval_metric_value_key_nonempty_ck CHECK (
        retrieval_metric_value_key = btrim(retrieval_metric_value_key)
        AND retrieval_metric_value_key <> ''
    ),
    CONSTRAINT retrieval_metric_value_cutoff_nonnegative_ck CHECK (
        cutoff_k >= 0
    ),
    CONSTRAINT retrieval_metric_value_denominator_positive_ck CHECK (
        denominator IS NULL OR denominator > 0
    ),
    CONSTRAINT retrieval_metric_value_semantics_nonempty_ck CHECK (
        value_semantics = btrim(value_semantics) AND value_semantics <> ''
    )
);

CREATE FUNCTION audit.enforce_retrieval_evaluation_immutability()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_retrieval_evaluation_immutability$
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'retrieval_evaluation_immutable_ck',
            MESSAGE = 'retrieval_evaluation_immutable_ck: stored retrieval evaluations are immutable';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM audit.retrieval_audit_set AS audit_set
        JOIN audit.retrieval_audit_case AS audit_case
          ON audit_case.retrieval_audit_set_id =
             audit_set.retrieval_audit_set_id
         AND audit_case.audit_split_code = NEW.audit_split_code
        JOIN ml.model_run AS model_run
          ON model_run.model_run_id = NEW.model_run_id
        JOIN ref.model_run_status AS status
          ON status.model_run_status_code = model_run.model_run_status_code
         AND status.is_successful
        JOIN ml.deterministic_retrieval_run AS deterministic_run
          ON deterministic_run.model_run_id = model_run.model_run_id
        JOIN corpus.corpus_snapshot AS snapshot
          ON snapshot.corpus_snapshot_id = audit_set.corpus_snapshot_id
         AND snapshot.corpus_id = model_run.input_corpus_id
         AND snapshot.normalization_pipeline_id =
             deterministic_run.normalization_pipeline_id
        WHERE audit_set.retrieval_audit_set_id =
              NEW.retrieval_audit_set_id
          AND audit_set.frozen_at IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_evaluation_frozen_inputs_ck',
            MESSAGE = 'retrieval_evaluation_frozen_inputs_ck: an evaluation requires a frozen nonempty audit split and a successful deterministic run';
    END IF;

    RETURN NEW;
END;
$enforce_retrieval_evaluation_immutability$;

CREATE TRIGGER retrieval_evaluation_immutable_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_evaluation
FOR EACH ROW
EXECUTE FUNCTION audit.enforce_retrieval_evaluation_immutability();

CREATE FUNCTION audit.guard_retrieval_metric_value_immutability()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_retrieval_metric_value_immutability$
BEGIN
    IF TG_OP <> 'INSERT' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'retrieval_metric_value_immutable_ck',
            MESSAGE = 'retrieval_metric_value_immutable_ck: stored retrieval metric values are immutable';
    END IF;
    RETURN NEW;
END;
$guard_retrieval_metric_value_immutability$;

CREATE TRIGGER retrieval_metric_value_immutable_biud
BEFORE INSERT OR UPDATE OR DELETE
ON audit.retrieval_metric_value
FOR EACH ROW
EXECUTE FUNCTION audit.guard_retrieval_metric_value_immutability();

CREATE FUNCTION audit.enforce_retrieval_metric_value_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_retrieval_metric_value_semantics$
DECLARE
    metric_requires_cutoff BOOLEAN;
    metric_minimum NUMERIC;
    metric_maximum NUMERIC;
BEGIN
    SELECT
        metric.requires_cutoff_k,
        metric.minimum_value,
        metric.maximum_value
    INTO
        metric_requires_cutoff,
        metric_minimum,
        metric_maximum
    FROM ref.retrieval_metric AS metric
    WHERE metric.retrieval_metric_code = NEW.retrieval_metric_code;

    IF NOT FOUND THEN
        RETURN NEW;
    END IF;

    IF metric_requires_cutoff <> (NEW.cutoff_k > 0) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_metric_value_cutoff_ck',
            MESSAGE = 'retrieval_metric_value_cutoff_ck: cutoff presence must match metric semantics';
    END IF;

    IF NEW.metric_value IS NOT NULL
       AND (
            (metric_minimum IS NOT NULL AND NEW.metric_value < metric_minimum)
            OR (metric_maximum IS NOT NULL AND NEW.metric_value > metric_maximum)
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '22003',
            CONSTRAINT = 'retrieval_metric_value_bounds_ck',
            MESSAGE = 'retrieval_metric_value_bounds_ck: metric value is outside its declared range';
    END IF;

    RETURN NEW;
END;
$enforce_retrieval_metric_value_semantics$;

CREATE TRIGGER retrieval_metric_value_semantics_biu
BEFORE INSERT OR UPDATE
ON audit.retrieval_metric_value
FOR EACH ROW
EXECUTE FUNCTION audit.enforce_retrieval_metric_value_semantics();

CREATE FUNCTION audit.calculate_retrieval_metrics(
    audit_set_key TEXT,
    model_run_key TEXT,
    split_code TEXT DEFAULT 'held_out'
)
RETURNS TABLE (
    retrieval_metric_code TEXT,
    cutoff_k SMALLINT,
    numerator NUMERIC,
    denominator NUMERIC,
    metric_value NUMERIC,
    value_semantics TEXT
)
LANGUAGE plpgsql
STABLE
SET search_path = pg_catalog
AS $calculate_retrieval_metrics$
DECLARE
    selected_audit_set_id BIGINT;
    selected_model_run_id BIGINT;
    selected_split_code TEXT;
    selected_case_count BIGINT;
BEGIN
    selected_split_code := COALESCE(
        NULLIF(btrim(split_code), ''),
        'held_out'
    );

    IF NOT EXISTS (
        SELECT 1
        FROM ref.audit_split AS audit_split
        WHERE audit_split.audit_split_code = selected_split_code
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'retrieval_metric_split_ck',
            MESSAGE = 'retrieval_metric_split_ck: unknown audit split';
    END IF;

    SELECT audit_set.retrieval_audit_set_id
    INTO selected_audit_set_id
    FROM audit.retrieval_audit_set AS audit_set
    WHERE audit_set.retrieval_audit_set_key = btrim(audit_set_key)
      AND audit_set.frozen_at IS NOT NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'retrieval_metric_audit_set_ck',
            MESSAGE = 'retrieval_metric_audit_set_ck: evaluation requires a known frozen audit set';
    END IF;

    SELECT model_run.model_run_id
    INTO selected_model_run_id
    FROM ml.model_run AS model_run
    JOIN ref.model_run_status AS run_status
      ON run_status.model_run_status_code = model_run.model_run_status_code
     AND run_status.is_successful
    JOIN ml.deterministic_retrieval_run AS deterministic_run
      ON deterministic_run.model_run_id = model_run.model_run_id
    JOIN audit.retrieval_audit_set AS audit_set
      ON audit_set.retrieval_audit_set_id = selected_audit_set_id
    JOIN corpus.corpus_snapshot AS snapshot
      ON snapshot.corpus_snapshot_id = audit_set.corpus_snapshot_id
     AND snapshot.normalization_pipeline_id =
         deterministic_run.normalization_pipeline_id
     AND snapshot.corpus_id = model_run.input_corpus_id
    WHERE model_run.model_run_key = btrim($2);

    IF NOT FOUND THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'retrieval_metric_model_run_ck',
            MESSAGE = 'retrieval_metric_model_run_ck: evaluation requires a successful deterministic run over the audit-set snapshot and normalizer';
    END IF;

    SELECT count(*)::BIGINT
    INTO selected_case_count
    FROM audit.retrieval_audit_case AS audit_case
    WHERE audit_case.retrieval_audit_set_id = selected_audit_set_id
      AND audit_case.audit_split_code = selected_split_code;

    IF selected_case_count = 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '22023',
            CONSTRAINT = 'retrieval_metric_case_count_ck',
            MESSAGE = 'retrieval_metric_case_count_ck: selected audit split contains no cases';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.retrieval_audit_case AS audit_case
        LEFT JOIN ml.mapping_inference AS inference
          ON inference.model_run_id = selected_model_run_id
         AND inference.observation_expression_id =
             audit_case.representative_observation_expression_id
        WHERE audit_case.retrieval_audit_set_id = selected_audit_set_id
          AND audit_case.audit_split_code = selected_split_code
          AND inference.mapping_inference_id IS NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_metric_inference_completeness_ck',
            MESSAGE = 'retrieval_metric_inference_completeness_ck: every selected audit case requires an inference from the evaluated run';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM audit.retrieval_audit_case AS audit_case
        LEFT JOIN audit.retrieval_case_review AS review
          ON review.retrieval_audit_case_id =
             audit_case.retrieval_audit_case_id
         AND review.audit_review_role_code = 'adjudicated'
        WHERE audit_case.retrieval_audit_set_id = selected_audit_set_id
          AND audit_case.audit_split_code = selected_split_code
          AND review.retrieval_case_review_id IS NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'retrieval_metric_adjudication_completeness_ck',
            MESSAGE = 'retrieval_metric_adjudication_completeness_ck: every selected audit case requires one adjudicated review';
    END IF;

    RETURN QUERY
    WITH selected_cases AS (
        SELECT
            audit_case.retrieval_audit_case_id,
            audit_case.representative_observation_expression_id,
            review.retrieval_case_review_id,
            review.expects_unresolved,
            inference.mapping_inference_id
        FROM audit.retrieval_audit_case AS audit_case
        JOIN audit.retrieval_case_review AS review
          ON review.retrieval_audit_case_id =
             audit_case.retrieval_audit_case_id
         AND review.audit_review_role_code = 'adjudicated'
        JOIN ml.mapping_inference AS inference
          ON inference.model_run_id = selected_model_run_id
         AND inference.observation_expression_id =
             audit_case.representative_observation_expression_id
        WHERE audit_case.retrieval_audit_set_id = selected_audit_set_id
          AND audit_case.audit_split_code = selected_split_code
    ),
    gold_judgments AS (
        SELECT
            selected.retrieval_audit_case_id,
            judgment.concept_id,
            grade.ordinal_value,
            grade.gain_value
        FROM selected_cases AS selected
        JOIN audit.retrieval_relevance_judgment AS judgment
          ON judgment.retrieval_case_review_id =
             selected.retrieval_case_review_id
        JOIN ref.relevance_grade AS grade
          ON grade.relevance_grade_code = judgment.relevance_grade_code
         AND NOT grade.is_unresolved
    ),
    relevant_counts AS (
        SELECT
            selected.retrieval_audit_case_id,
            count(gold.concept_id) FILTER (
                WHERE gold.ordinal_value >= 2
            )::NUMERIC AS relevant_concept_count
        FROM selected_cases AS selected
        LEFT JOIN gold_judgments AS gold
          ON gold.retrieval_audit_case_id =
             selected.retrieval_audit_case_id
        GROUP BY selected.retrieval_audit_case_id
    ),
    retrieved_candidates AS (
        SELECT
            selected.retrieval_audit_case_id,
            candidate.rank,
            candidate.concept_id,
            COALESCE(gold.ordinal_value, 0)::SMALLINT AS ordinal_value,
            COALESCE(gold.gain_value, 0)::NUMERIC AS gain_value
        FROM selected_cases AS selected
        JOIN ml.mapping_candidate AS candidate
          ON candidate.mapping_inference_id = selected.mapping_inference_id
        LEFT JOIN gold_judgments AS gold
          ON gold.retrieval_audit_case_id =
             selected.retrieval_audit_case_id
         AND gold.concept_id = candidate.concept_id
    ),
    candidate_counts AS (
        SELECT
            selected.retrieval_audit_case_id,
            selected.expects_unresolved,
            count(candidate.mapping_candidate_id)::BIGINT AS candidate_count
        FROM selected_cases AS selected
        LEFT JOIN ml.mapping_candidate AS candidate
          ON candidate.mapping_inference_id = selected.mapping_inference_id
        GROUP BY
            selected.retrieval_audit_case_id,
            selected.expects_unresolved
    ),
    ideal_ranked AS (
        SELECT
            gold.retrieval_audit_case_id,
            gold.gain_value,
            ROW_NUMBER() OVER (
                PARTITION BY gold.retrieval_audit_case_id
                ORDER BY
                    gold.ordinal_value DESC,
                    gold.concept_id
            ) AS ideal_rank
        FROM gold_judgments AS gold
        WHERE gold.ordinal_value > 0
    ),
    ideal_dcg AS (
        SELECT
            selected.retrieval_audit_case_id,
            COALESCE(
                sum(
                    ideal.gain_value
                    / (ln((ideal.ideal_rank + 1)::NUMERIC) / ln(2::NUMERIC))
                ) FILTER (WHERE ideal.ideal_rank <= 5),
                0
            )::NUMERIC AS ideal_dcg_at_5
        FROM selected_cases AS selected
        LEFT JOIN ideal_ranked AS ideal
          ON ideal.retrieval_audit_case_id =
             selected.retrieval_audit_case_id
        GROUP BY selected.retrieval_audit_case_id
    ),
    per_case_ranking AS (
        SELECT
            selected.retrieval_audit_case_id,
            selected.expects_unresolved,
            relevant.relevant_concept_count,
            count(retrieved.concept_id) FILTER (
                WHERE retrieved.rank <= 1
                  AND retrieved.ordinal_value >= 2
            )::NUMERIC / NULLIF(relevant.relevant_concept_count, 0)
                AS recall_at_1,
            count(retrieved.concept_id) FILTER (
                WHERE retrieved.rank <= 3
                  AND retrieved.ordinal_value >= 2
            )::NUMERIC / NULLIF(relevant.relevant_concept_count, 0)
                AS recall_at_3,
            count(retrieved.concept_id) FILTER (
                WHERE retrieved.rank <= 5
                  AND retrieved.ordinal_value >= 2
            )::NUMERIC / NULLIF(relevant.relevant_concept_count, 0)
                AS recall_at_5,
            COALESCE(
                1::NUMERIC / NULLIF(
                    min(retrieved.rank) FILTER (
                        WHERE retrieved.ordinal_value >= 2
                    ),
                    0
                ),
                0
            ) AS reciprocal_rank,
            COALESCE(
                sum(
                    retrieved.gain_value
                    / (ln((retrieved.rank + 1)::NUMERIC) / ln(2::NUMERIC))
                ) FILTER (WHERE retrieved.rank <= 5),
                0
            )::NUMERIC AS dcg_at_5,
            ideal.ideal_dcg_at_5
        FROM selected_cases AS selected
        JOIN relevant_counts AS relevant
          ON relevant.retrieval_audit_case_id =
             selected.retrieval_audit_case_id
        JOIN ideal_dcg AS ideal
          ON ideal.retrieval_audit_case_id =
             selected.retrieval_audit_case_id
        LEFT JOIN retrieved_candidates AS retrieved
          ON retrieved.retrieval_audit_case_id =
             selected.retrieval_audit_case_id
        GROUP BY
            selected.retrieval_audit_case_id,
            selected.expects_unresolved,
            relevant.relevant_concept_count,
            ideal.ideal_dcg_at_5
    ),
    ranking_summary AS (
        SELECT
            count(*) FILTER (WHERE NOT ranking.expects_unresolved)::NUMERIC
                AS resolvable_case_count,
            sum(ranking.recall_at_1) FILTER (
                WHERE NOT ranking.expects_unresolved
            )::NUMERIC AS recall_at_1_sum,
            sum(ranking.recall_at_3) FILTER (
                WHERE NOT ranking.expects_unresolved
            )::NUMERIC AS recall_at_3_sum,
            sum(ranking.recall_at_5) FILTER (
                WHERE NOT ranking.expects_unresolved
            )::NUMERIC AS recall_at_5_sum,
            sum(ranking.reciprocal_rank) FILTER (
                WHERE NOT ranking.expects_unresolved
            )::NUMERIC AS reciprocal_rank_sum,
            sum(
                ranking.dcg_at_5 / NULLIF(ranking.ideal_dcg_at_5, 0)
            ) FILTER (
                WHERE NOT ranking.expects_unresolved
            )::NUMERIC AS ndcg_at_5_sum
        FROM per_case_ranking AS ranking
    ),
    candidate_summary AS (
        SELECT
            count(*)::NUMERIC AS all_case_count,
            count(*) FILTER (
                WHERE counts.candidate_count > 0
            )::NUMERIC AS covered_case_count,
            count(*) FILTER (
                WHERE counts.candidate_count = 0
            )::NUMERIC AS abstained_case_count,
            count(*) FILTER (
                WHERE counts.candidate_count = 0
                  AND NOT counts.expects_unresolved
            )::NUMERIC AS erroneous_abstention_count,
            count(*) FILTER (
                WHERE counts.expects_unresolved
            )::NUMERIC AS unresolved_case_count,
            count(*) FILTER (
                WHERE counts.expects_unresolved
                  AND counts.candidate_count > 0
            )::NUMERIC AS unsafe_nonabstention_count,
            percentile_cont(0.5) WITHIN GROUP (
                ORDER BY counts.candidate_count
            )::NUMERIC AS median_candidate_count
        FROM candidate_counts AS counts
    ),
    metric_rows AS (
        SELECT
            'recall_at_k'::TEXT AS metric_code,
            1::SMALLINT AS metric_cutoff,
            ranking.recall_at_1_sum AS metric_numerator,
            NULLIF(ranking.resolvable_case_count, 0) AS metric_denominator,
            ranking.recall_at_1_sum
                / NULLIF(ranking.resolvable_case_count, 0) AS metric_result,
            'Macro recall of adjudicated grade-2-or-3 concepts among resolvable cases; unresolved cases excluded.'::TEXT AS semantics
        FROM ranking_summary AS ranking

        UNION ALL

        SELECT
            'recall_at_k',
            3::SMALLINT,
            ranking.recall_at_3_sum,
            NULLIF(ranking.resolvable_case_count, 0),
            ranking.recall_at_3_sum
                / NULLIF(ranking.resolvable_case_count, 0),
            'Macro recall of adjudicated grade-2-or-3 concepts among resolvable cases; unresolved cases excluded.'
        FROM ranking_summary AS ranking

        UNION ALL

        SELECT
            'recall_at_k',
            5::SMALLINT,
            ranking.recall_at_5_sum,
            NULLIF(ranking.resolvable_case_count, 0),
            ranking.recall_at_5_sum
                / NULLIF(ranking.resolvable_case_count, 0),
            'Macro recall of adjudicated grade-2-or-3 concepts among resolvable cases; unresolved cases excluded.'
        FROM ranking_summary AS ranking

        UNION ALL

        SELECT
            'mrr',
            0::SMALLINT,
            ranking.reciprocal_rank_sum,
            NULLIF(ranking.resolvable_case_count, 0),
            ranking.reciprocal_rank_sum
                / NULLIF(ranking.resolvable_case_count, 0),
            'Mean reciprocal rank of the first adjudicated grade-2-or-3 result; unresolved cases excluded.'
        FROM ranking_summary AS ranking

        UNION ALL

        SELECT
            'ndcg_at_k',
            5::SMALLINT,
            ranking.ndcg_at_5_sum,
            NULLIF(ranking.resolvable_case_count, 0),
            ranking.ndcg_at_5_sum
                / NULLIF(ranking.resolvable_case_count, 0),
            'Macro nDCG with gains 0, 1, 3, and 7; genuinely unresolved cases have undefined IDCG and are excluded.'
        FROM ranking_summary AS ranking

        UNION ALL

        SELECT
            'coverage',
            0::SMALLINT,
            summary.covered_case_count,
            summary.all_case_count,
            summary.covered_case_count / NULLIF(summary.all_case_count, 0),
            'Fraction of all selected cases returning at least one candidate.'
        FROM candidate_summary AS summary

        UNION ALL

        SELECT
            'abstention_rate',
            0::SMALLINT,
            summary.abstained_case_count,
            summary.all_case_count,
            summary.abstained_case_count / NULLIF(summary.all_case_count, 0),
            'Fraction of all selected cases returning no candidate.'
        FROM candidate_summary AS summary

        UNION ALL

        SELECT
            'abstention_error',
            0::SMALLINT,
            summary.erroneous_abstention_count,
            NULLIF(summary.abstained_case_count, 0),
            summary.erroneous_abstention_count
                / NULLIF(summary.abstained_case_count, 0),
            'Conditional false-abstention fraction among abstained cases; NULL when there were no abstentions.'
        FROM candidate_summary AS summary

        UNION ALL

        SELECT
            'median_candidate_set_size',
            0::SMALLINT,
            NULL::NUMERIC,
            summary.all_case_count,
            summary.median_candidate_count,
            'Median candidate count across all selected cases, including zero for abstention.'
        FROM candidate_summary AS summary

        UNION ALL

        SELECT
            'unsafe_nonabstention',
            0::SMALLINT,
            summary.unsafe_nonabstention_count,
            NULLIF(summary.unresolved_case_count, 0),
            summary.unsafe_nonabstention_count
                / NULLIF(summary.unresolved_case_count, 0),
            'Among adjudicated unresolved cases, the fraction for which at least one candidate was returned.'
        FROM candidate_summary AS summary
    )
    SELECT
        metric.metric_code,
        metric.metric_cutoff,
        metric.metric_numerator,
        metric.metric_denominator,
        metric.metric_result,
        metric.semantics
    FROM metric_rows AS metric
    ORDER BY
        CASE metric.metric_code
            WHEN 'recall_at_k' THEN 1
            WHEN 'mrr' THEN 2
            WHEN 'ndcg_at_k' THEN 3
            WHEN 'coverage' THEN 4
            WHEN 'abstention_rate' THEN 5
            WHEN 'abstention_error' THEN 6
            WHEN 'median_candidate_set_size' THEN 7
            ELSE 8
        END,
        metric.metric_cutoff;
END;
$calculate_retrieval_metrics$;

COMMENT ON FUNCTION audit.calculate_retrieval_metrics(TEXT, TEXT, TEXT) IS
    'Calculates held-out or development retrieval metrics from complete stored inferences and one adjudicated review per case. Recall/MRR use relevance >=2; nDCG uses declared graded gains and excludes U cases; abstention remains explicit.';

COMMIT;
