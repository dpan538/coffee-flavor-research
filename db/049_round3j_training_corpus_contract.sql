\set ON_ERROR_STOP on

-- Round 3J is a corpus-construction and validation round.  The objects below
-- describe candidate data, deterministic splits, and release conditions; they
-- do not authorize model fitting and do not replace any Round 3I current view.
BEGIN;

CREATE TABLE audit.round3j_checkpoint (
    checkpoint_key TEXT NOT NULL,
    baseline_freeze_version TEXT NOT NULL,
    source_sha TEXT NOT NULL,
    expected_state_file TEXT NOT NULL,
    expected_state_commit_sha TEXT NOT NULL,
    expected_state_frozen_before_acquisition BOOLEAN NOT NULL,
    acquisition_started_at TIMESTAMPTZ,
    canonical_concept_count INTEGER NOT NULL,
    active_sensory_attribute_count INTEGER NOT NULL,
    governed_expression_count INTEGER NOT NULL,
    sensory_sample_or_configuration_count INTEGER NOT NULL,
    relationship_evidence_claim_count INTEGER NOT NULL,
    model_count_at_start INTEGER NOT NULL,
    model_run_count_at_start INTEGER NOT NULL,
    model_version_count_at_start INTEGER NOT NULL,
    v0_1_0_mutation_count INTEGER NOT NULL,
    round3_foundation_complete BOOLEAN NOT NULL,
    model_prebuild_data_ready BOOLEAN NOT NULL,
    round3_data_scale_complete BOOLEAN NOT NULL,
    round3_training_corpus_ready BOOLEAN NOT NULL,
    round3_exit_gate_pass BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT round3j_checkpoint_pk PRIMARY KEY (checkpoint_key),
    CONSTRAINT round3j_checkpoint_release_fk FOREIGN KEY (
        baseline_freeze_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3j_checkpoint_baseline_ck CHECK (
        checkpoint_key = 'round3j.training-scale'
        AND baseline_freeze_version =
            'coffee-sensory-research-db-v0.1.0'
        AND source_sha =
            'c3ae9b880d85507a0b8b0298bb94ef013d02f928'
        AND expected_state_file =
            'db/data/round3j/training_scale_expected_state.tsv'
        AND expected_state_commit_sha =
            '2dd6b47f3301b4f705bf6624c69c2832eda17527'
        AND expected_state_frozen_before_acquisition
        AND (acquisition_started_at IS NULL
             OR acquisition_started_at >= created_at)
        AND canonical_concept_count = 130
        AND active_sensory_attribute_count = 92
        AND governed_expression_count = 2996
        AND sensory_sample_or_configuration_count = 230
        AND relationship_evidence_claim_count = 97
        AND model_count_at_start >= 0
        AND model_run_count_at_start >= 0
        AND model_version_count_at_start >= 0
        AND v0_1_0_mutation_count = 0
        AND round3_foundation_complete
        AND model_prebuild_data_ready
        AND NOT round3_data_scale_complete
        AND NOT round3_training_corpus_ready
        AND NOT round3_exit_gate_pass
    )
);

COMMENT ON TABLE audit.round3j_checkpoint IS
    'Immutable pre-acquisition binding to the frozen v0.1.0 release and Round 3J expected-state commit.';

CREATE FUNCTION audit.enforce_round3j_checkpoint_baseline()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3j_checkpoint_baseline$
BEGIN
    IF NEW.model_count_at_start <> (SELECT count(*) FROM ml.model)
       OR NEW.model_version_count_at_start <>
          (SELECT count(*) FROM ml.model_version)
       OR NEW.model_run_count_at_start <>
          (SELECT count(*) FROM ml.model_run) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3j_checkpoint_model_baseline_ck',
            MESSAGE = 'checkpoint model counts must equal the live pre-acquisition tables';
    END IF;
    RETURN NEW;
END;
$enforce_round3j_checkpoint_baseline$;

CREATE TRIGGER round3j_checkpoint_baseline_bi
BEFORE INSERT ON audit.round3j_checkpoint
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3j_checkpoint_baseline();

CREATE FUNCTION audit.prevent_round3j_checkpoint_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3j_checkpoint_mutation$
BEGIN
    RAISE EXCEPTION USING ERRCODE = '23514',
        CONSTRAINT = 'round3j_checkpoint_immutable_ck',
        MESSAGE = 'the Round 3J pre-acquisition checkpoint is immutable';
END;
$prevent_round3j_checkpoint_mutation$;

CREATE TRIGGER round3j_checkpoint_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3j_checkpoint
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3j_checkpoint_mutation();

CREATE TABLE audit.round3j_acquisition_batch (
    batch_key TEXT NOT NULL,
    checkpoint_key TEXT NOT NULL,
    acquisition_lane TEXT NOT NULL,
    batch_sequence INTEGER NOT NULL,
    targeted_training_gap TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    named_source_candidate_count INTEGER NOT NULL,
    acquired_source_count INTEGER NOT NULL,
    admitted_source_count INTEGER NOT NULL,
    raw_row_delta BIGINT NOT NULL,
    effective_unit_delta INTEGER NOT NULL,
    source_family_delta INTEGER NOT NULL,
    coverage_delta INTEGER NOT NULL,
    unique_expression_delta INTEGER NOT NULL,
    zh_hans_expression_delta INTEGER NOT NULL,
    relationship_evidence_delta INTEGER NOT NULL,
    long_tail_target_delta INTEGER NOT NULL,
    held_out_source_feasibility_gain BOOLEAN NOT NULL,
    material_gain BOOLEAN NOT NULL,
    consecutive_no_material_gain_count INTEGER NOT NULL,
    stop_status TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    CONSTRAINT round3j_acquisition_batch_pk PRIMARY KEY (batch_key),
    CONSTRAINT round3j_acquisition_batch_sequence_uq UNIQUE (
        batch_sequence
    ),
    CONSTRAINT round3j_acquisition_batch_checkpoint_fk FOREIGN KEY (
        checkpoint_key
    ) REFERENCES audit.round3j_checkpoint (checkpoint_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3j_acquisition_batch_text_ck CHECK (
        batch_key = lower(btrim(batch_key)) AND batch_key <> ''
        AND acquisition_lane IN ('A', 'B', 'C', 'D', 'E', 'F')
        AND targeted_training_gap = btrim(targeted_training_gap)
        AND targeted_training_gap <> ''
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
        AND lifecycle_status IN (
            'REGISTERED', 'IN_PROGRESS', 'COMPLETE'
        )
        AND stop_status IN (
            'CONTINUE', 'STOP_EXIT_GATE_PASS',
            'STOP_THREE_CONSECUTIVE_NO_MATERIAL_GAIN'
        )
    ),
    CONSTRAINT round3j_acquisition_batch_counts_ck CHECK (
        batch_sequence > 0
        AND named_source_candidate_count >= acquired_source_count
        AND acquired_source_count >= admitted_source_count
        AND admitted_source_count >= 0
        AND raw_row_delta >= 0 AND effective_unit_delta >= 0
        AND source_family_delta >= 0 AND coverage_delta >= 0
        AND unique_expression_delta >= 0
        AND zh_hans_expression_delta >= 0
        AND relationship_evidence_delta >= 0
        AND long_tail_target_delta >= 0
        AND consecutive_no_material_gain_count BETWEEN 0 AND 3
        AND (completed_at IS NULL OR completed_at >= started_at)
        AND ((lifecycle_status = 'COMPLETE') =
             (completed_at IS NOT NULL))
    ),
    CONSTRAINT round3j_acquisition_batch_gain_ck CHECK (
        material_gain = (
            effective_unit_delta > 0 OR source_family_delta > 0
            OR coverage_delta > 0 OR unique_expression_delta > 0
            OR zh_hans_expression_delta > 0
            OR relationship_evidence_delta > 0
            OR long_tail_target_delta > 0
            OR held_out_source_feasibility_gain
        )
        AND (material_gain OR consecutive_no_material_gain_count > 0
             OR lifecycle_status <> 'COMPLETE')
        AND (stop_status <>
                'STOP_THREE_CONSECUTIVE_NO_MATERIAL_GAIN'
             OR (NOT material_gain
                 AND consecutive_no_material_gain_count = 3))
        AND (consecutive_no_material_gain_count < 3
             OR stop_status =
                'STOP_THREE_CONSECUTIVE_NO_MATERIAL_GAIN')
        AND (NOT material_gain
             OR consecutive_no_material_gain_count = 0)
        AND (stop_status = 'CONTINUE'
             OR lifecycle_status = 'COMPLETE')
    )
);

COMMENT ON TABLE audit.round3j_acquisition_batch IS
    'Targeted acquisition result with raw rows and meaningful effective gains reported separately.';

CREATE TABLE audit.round3j_source_identity (
    candidate_key TEXT NOT NULL,
    identity_scope TEXT NOT NULL,
    registered_batch_key TEXT,
    acquisition_lanes TEXT[] NOT NULL,
    targeted_training_gaps TEXT[] NOT NULL,
    title TEXT NOT NULL,
    authors_or_owner TEXT NOT NULL,
    publication_year INTEGER NOT NULL,
    doi_or_stable_url TEXT NOT NULL,
    repository TEXT NOT NULL,
    exact_version TEXT NOT NULL,
    canonical_origin_key TEXT NOT NULL,
    mirror_of_candidate_key TEXT,
    counts_as_independent BOOLEAN NOT NULL,
    independence_basis TEXT NOT NULL,
    expected_contribution TEXT NOT NULL,
    estimated_effective_unit_count INTEGER,
    license_expression TEXT NOT NULL,
    rights_state TEXT NOT NULL,
    access_state TEXT NOT NULL,
    privacy_state TEXT NOT NULL,
    research_use_decision TEXT NOT NULL,
    model_research_use_decision TEXT NOT NULL,
    public_corpus_release_decision TEXT NOT NULL,
    raw_public_release_decision TEXT NOT NULL,
    candidate_decision TEXT NOT NULL,
    raw_acquisition_authorized BOOLEAN NOT NULL,
    registered_on DATE NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT round3j_source_identity_pk PRIMARY KEY (candidate_key),
    CONSTRAINT round3j_source_identity_batch_fk FOREIGN KEY (
        registered_batch_key
    ) REFERENCES audit.round3j_acquisition_batch (batch_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3j_source_identity_mirror_fk FOREIGN KEY (
        mirror_of_candidate_key
    ) REFERENCES audit.round3j_source_identity (candidate_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3j_source_identity_text_ck CHECK (
        candidate_key = lower(btrim(candidate_key)) AND candidate_key <> ''
        AND cardinality(acquisition_lanes) >= 1
        AND acquisition_lanes <@ ARRAY['A', 'B', 'C', 'D', 'E', 'F']::TEXT[]
        AND array_position(acquisition_lanes, NULL) IS NULL
        AND cardinality(targeted_training_gaps) >= 1
        AND array_position(targeted_training_gaps, NULL) IS NULL
        AND title = btrim(title) AND title <> ''
        AND authors_or_owner = btrim(authors_or_owner)
        AND authors_or_owner <> ''
        AND publication_year BETWEEN 1900 AND 2100
        AND doi_or_stable_url ~ '^https?://'
        AND repository = btrim(repository) AND repository <> ''
        AND exact_version = btrim(exact_version) AND exact_version <> ''
        AND canonical_origin_key = lower(btrim(canonical_origin_key))
        AND canonical_origin_key <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
        AND expected_contribution = btrim(expected_contribution)
        AND expected_contribution <> ''
        AND (estimated_effective_unit_count IS NULL
             OR estimated_effective_unit_count >= 0)
        AND license_expression = btrim(license_expression)
        AND license_expression <> ''
        AND limitation = btrim(limitation) AND limitation <> ''
    ),
    CONSTRAINT round3j_source_identity_state_ck CHECK (
        identity_scope IN ('BASELINE_EXISTING', 'ROUND3J_CANDIDATE')
        AND ((identity_scope = 'BASELINE_EXISTING'
              AND registered_batch_key IS NULL
              AND NOT raw_acquisition_authorized)
             OR (identity_scope = 'ROUND3J_CANDIDATE'
                 AND registered_batch_key IS NOT NULL))
        AND rights_state IN (
            'CLEARED', 'RESEARCH_ONLY', 'METADATA_ONLY',
            'BLOCKED_RIGHTS', 'PENDING'
        )
        AND access_state IN (
            'PUBLIC_VERSIONED', 'PUBLIC_UNVERSIONED', 'AUTHOR_REQUEST',
            'PRIVATE_LINK', 'BLOCKED_TERMS', 'UNRESOLVED'
        )
        AND privacy_state IN (
            'NO_PERSONAL_DATA', 'AGGREGATE_ONLY',
            'DEIDENTIFIED_REVIEW_REQUIRED', 'RESTRICTED_PERSONAL_DATA',
            'BLOCKED_PRIVACY', 'PENDING'
        )
        AND research_use_decision IN ('ALLOW', 'DENY', 'UNRESOLVED')
        AND model_research_use_decision IN ('ALLOW', 'DENY', 'UNRESOLVED')
        AND public_corpus_release_decision IN (
            'ALLOW', 'DENY', 'UNRESOLVED'
        )
        AND raw_public_release_decision IN (
            'ALLOW', 'DENY', 'UNRESOLVED'
        )
        AND candidate_decision IN (
            'ACQUIRE_FOR_FILE_AUDIT', 'ACQUIRE_RESEARCH_ONLY',
            'ADMIT_METADATA_ONLY', 'ADMIT_AGGREGATE_ONLY',
            'HOLD_RIGHTS', 'HOLD_PRIVACY', 'HOLD_ACCESS',
            'REJECT_RIGHTS', 'REJECT_PRIVACY',
            'REJECT_ACCESS_TERMS', 'REJECT_OUT_OF_SCOPE', 'MONITOR'
        )
    ),
    CONSTRAINT round3j_source_identity_independence_ck CHECK (
        mirror_of_candidate_key IS DISTINCT FROM candidate_key
        AND (mirror_of_candidate_key IS NULL OR NOT counts_as_independent)
    ),
    CONSTRAINT round3j_source_identity_rights_ck CHECK (
        (raw_public_release_decision <> 'ALLOW'
         OR public_corpus_release_decision = 'ALLOW')
        AND (public_corpus_release_decision <> 'ALLOW'
             OR (rights_state = 'CLEARED'
                 AND privacy_state IN (
                    'NO_PERSONAL_DATA', 'AGGREGATE_ONLY'
                 )))
        AND (model_research_use_decision <> 'ALLOW'
             OR research_use_decision = 'ALLOW')
        AND (NOT raw_acquisition_authorized OR (
            rights_state IN ('CLEARED', 'RESEARCH_ONLY')
            AND access_state IN ('PUBLIC_VERSIONED', 'PUBLIC_UNVERSIONED')
            AND research_use_decision = 'ALLOW'
            AND candidate_decision IN (
                'ACQUIRE_FOR_FILE_AUDIT', 'ACQUIRE_RESEARCH_ONLY'
            )
        ))
    )
);

CREATE UNIQUE INDEX round3j_source_identity_independent_origin_uq
ON audit.round3j_source_identity (canonical_origin_key)
WHERE counts_as_independent;

COMMENT ON TABLE audit.round3j_source_identity IS
    'Canonical named/versioned identity ledger for baseline-existing and pre-acquisition candidate sources; public visibility is not permission.';

CREATE TABLE ml.training_task_candidate (
    task_key TEXT NOT NULL,
    task_type TEXT NOT NULL,
    task_version TEXT NOT NULL,
    effective_unit_definition TEXT NOT NULL,
    candidate_outcomes TEXT[] NOT NULL,
    label_semantics TEXT NOT NULL,
    eligibility_rule TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    model_fitting_authorized BOOLEAN NOT NULL DEFAULT FALSE,
    limitation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT training_task_candidate_pk PRIMARY KEY (task_key),
    CONSTRAINT training_task_candidate_type_uq UNIQUE (
        task_type
    ),
    CONSTRAINT training_task_candidate_contract_ck CHECK (
        task_key = lower(btrim(task_key)) AND task_key <> ''
        AND task_type IN (
            'LEXICAL_NORMALIZATION', 'ASSOCIATION_MODEL',
            'CONTEXT_MODEL', 'QUESTION_MODEL', 'ADAPTIVE_POLICY'
        )
        AND task_version = btrim(task_version) AND task_version <> ''
        AND effective_unit_definition = btrim(effective_unit_definition)
        AND effective_unit_definition <> ''
        AND cardinality(candidate_outcomes) >= 1
        AND array_position(candidate_outcomes, NULL) IS NULL
        AND label_semantics = btrim(label_semantics)
        AND label_semantics <> ''
        AND eligibility_rule = btrim(eligibility_rule)
        AND eligibility_rule <> ''
        AND lifecycle_status IN (
            'DEFINED', 'CORPUS_BUILDING', 'VALIDATED',
            'EVALUATION_ONLY', 'BLOCKED'
        )
        AND NOT model_fitting_authorized
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

COMMENT ON TABLE ml.training_task_candidate IS
    'Task-specific corpus contract only; model fitting remains prohibited in Round 3J.';

CREATE TABLE ml.training_partition_eligibility (
    partition_eligibility_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    partition_key TEXT NOT NULL,
    source_identity_key TEXT NOT NULL,
    source_registry TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_version TEXT NOT NULL,
    snapshot_key TEXT NOT NULL,
    source_locator TEXT NOT NULL,
    source_file_manifest JSONB NOT NULL,
    mirror_of_partition_eligibility_key TEXT,
    counts_as_independent BOOLEAN NOT NULL,
    effective_unit_type TEXT NOT NULL,
    raw_row_count BIGINT NOT NULL,
    effective_unit_count INTEGER NOT NULL,
    sensory_method TEXT NOT NULL,
    outcome_semantics TEXT NOT NULL,
    measurement_scale_semantics TEXT NOT NULL,
    pooling_decision TEXT NOT NULL,
    source_local_semantics_preserved BOOLEAN NOT NULL,
    rights_review_complete BOOLEAN NOT NULL,
    privacy_review_complete BOOLEAN NOT NULL,
    source_file_hash_complete BOOLEAN NOT NULL,
    label_provenance_complete BOOLEAN NOT NULL,
    duplicate_audit_complete BOOLEAN NOT NULL,
    research_use_allowed BOOLEAN NOT NULL,
    model_research_use_allowed BOOLEAN NOT NULL,
    public_corpus_release_allowed BOOLEAN NOT NULL,
    raw_public_release_allowed BOOLEAN NOT NULL,
    eligibility_class TEXT NOT NULL,
    decision_basis TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    reviewed_on DATE NOT NULL,
    CONSTRAINT training_partition_eligibility_pk PRIMARY KEY (
        partition_eligibility_key
    ),
    CONSTRAINT training_partition_eligibility_task_partition_uq UNIQUE (
        task_key, partition_key
    ),
    CONSTRAINT training_partition_eligibility_key_task_uq UNIQUE (
        partition_eligibility_key, task_key
    ),
    CONSTRAINT training_partition_eligibility_task_fk FOREIGN KEY (
        task_key
    ) REFERENCES ml.training_task_candidate (task_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_partition_eligibility_source_identity_fk FOREIGN KEY (
        source_identity_key
    ) REFERENCES audit.round3j_source_identity (candidate_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_partition_eligibility_mirror_fk FOREIGN KEY (
        mirror_of_partition_eligibility_key
    ) REFERENCES ml.training_partition_eligibility (
        partition_eligibility_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_partition_eligibility_text_ck CHECK (
        partition_eligibility_key =
            lower(btrim(partition_eligibility_key))
        AND partition_eligibility_key <> ''
        AND partition_key = lower(btrim(partition_key))
        AND partition_key <> ''
        AND source_registry IN (
            'CURRENT_LANGUAGE_SURFACE', 'CURRENT_SENSORY_SURFACE',
            'CURRENT_CONTEXT_SURFACE', 'CURRENT_RELATIONSHIP_SURFACE',
            'CURRENT_QUESTION_SURFACE', 'EXTERNAL_CANDIDATE'
        )
        AND source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND source_key = lower(btrim(source_key)) AND source_key <> ''
        AND source_version = btrim(source_version) AND source_version <> ''
        AND snapshot_key = lower(btrim(snapshot_key)) AND snapshot_key <> ''
        AND source_locator = btrim(source_locator) AND source_locator <> ''
        AND corpus.language_source_manifest_is_complete(
            source_file_manifest
        )
        AND sensory_method = btrim(sensory_method) AND sensory_method <> ''
        AND outcome_semantics = btrim(outcome_semantics)
        AND outcome_semantics <> ''
        AND measurement_scale_semantics =
            btrim(measurement_scale_semantics)
        AND measurement_scale_semantics <> ''
        AND decision_basis = btrim(decision_basis)
        AND decision_basis <> ''
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
    ),
    CONSTRAINT training_partition_eligibility_state_ck CHECK (
        source_identity_key IS NOT NULL
        AND mirror_of_partition_eligibility_key IS DISTINCT FROM
            partition_eligibility_key
        AND (mirror_of_partition_eligibility_key IS NULL
             OR NOT counts_as_independent)
        AND effective_unit_type IN (
            'UNIQUE_EXPRESSION', 'SOURCE_QUALIFIED_RELATIONSHIP',
            'COFFEE_SAMPLE_CONFIGURATION', 'REAL_USER_RESPONSE',
            'REAL_SEQUENTIAL_RESPONSE'
        )
        AND raw_row_count >= 0 AND effective_unit_count >= 0
        AND effective_unit_count <= raw_row_count
        AND pooling_decision IN (
            'SOURCE_LOCAL_ONLY', 'SEMANTICALLY_COMPATIBLE',
            'PROHIBITED', 'NOT_APPLICABLE'
        )
        AND eligibility_class IN (
            'ELIGIBLE_FOR_LEXICAL_TRAINING',
            'ELIGIBLE_FOR_ASSOCIATION_TRAINING',
            'ELIGIBLE_FOR_CONTEXT_TRAINING',
            'EVALUATION_ONLY', 'RESEARCH_REFERENCE_ONLY',
            'NOT_TRAINING_ELIGIBLE'
        )
        AND source_file_hash_complete =
            corpus.language_source_manifest_is_complete(
                source_file_manifest
            )
        AND (NOT raw_public_release_allowed
             OR public_corpus_release_allowed)
        AND (NOT public_corpus_release_allowed
             OR research_use_allowed)
        AND (NOT model_research_use_allowed OR research_use_allowed)
    ),
    CONSTRAINT training_partition_eligibility_admission_ck CHECK (
        eligibility_class NOT IN (
            'ELIGIBLE_FOR_LEXICAL_TRAINING',
            'ELIGIBLE_FOR_ASSOCIATION_TRAINING',
            'ELIGIBLE_FOR_CONTEXT_TRAINING'
        ) OR (
            counts_as_independent
            AND mirror_of_partition_eligibility_key IS NULL
            AND effective_unit_count > 0
            AND source_local_semantics_preserved
            AND rights_review_complete AND privacy_review_complete
            AND source_file_hash_complete AND label_provenance_complete
            AND duplicate_audit_complete
            AND research_use_allowed AND model_research_use_allowed
        )
    )
);

CREATE FUNCTION ml.enforce_training_partition_task_class()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_training_partition_task_class$
DECLARE
    selected_task_type TEXT;
    expected_class TEXT;
    expected_unit TEXT;
    selected_identity audit.round3j_source_identity%ROWTYPE;
BEGIN
    SELECT task_type INTO selected_task_type
    FROM ml.training_task_candidate
    WHERE task_key = NEW.task_key;

    expected_class := CASE selected_task_type
        WHEN 'LEXICAL_NORMALIZATION' THEN 'ELIGIBLE_FOR_LEXICAL_TRAINING'
        WHEN 'ASSOCIATION_MODEL' THEN 'ELIGIBLE_FOR_ASSOCIATION_TRAINING'
        WHEN 'CONTEXT_MODEL' THEN 'ELIGIBLE_FOR_CONTEXT_TRAINING'
        ELSE NULL END;
    expected_unit := CASE selected_task_type
        WHEN 'LEXICAL_NORMALIZATION' THEN 'UNIQUE_EXPRESSION'
        WHEN 'ASSOCIATION_MODEL' THEN 'SOURCE_QUALIFIED_RELATIONSHIP'
        WHEN 'CONTEXT_MODEL' THEN 'COFFEE_SAMPLE_CONFIGURATION'
        WHEN 'QUESTION_MODEL' THEN 'REAL_USER_RESPONSE'
        WHEN 'ADAPTIVE_POLICY' THEN 'REAL_SEQUENTIAL_RESPONSE' END;

    IF NEW.effective_unit_type <> expected_unit THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_partition_effective_unit_task_ck',
            MESSAGE = 'partition effective-unit semantics do not match its task';
    END IF;
    IF NEW.eligibility_class LIKE 'ELIGIBLE_FOR_%_TRAINING'
       AND (expected_class IS NULL
            OR NEW.eligibility_class <> expected_class) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_partition_eligibility_task_ck',
            MESSAGE = 'partition training eligibility does not match its task';
    END IF;
    IF NEW.source_identity_key IS NOT NULL THEN
        SELECT * INTO selected_identity
        FROM audit.round3j_source_identity
        WHERE candidate_key = NEW.source_identity_key;
        IF NOT FOUND THEN
            RAISE EXCEPTION USING ERRCODE = '23503',
                CONSTRAINT = 'training_partition_source_identity_fk',
                MESSAGE = 'external partition source identity is missing';
        END IF;
        IF (NEW.counts_as_independent
            AND NOT selected_identity.counts_as_independent)
           OR NEW.source_family_key <>
              selected_identity.canonical_origin_key
           OR NEW.source_version <> selected_identity.exact_version
           OR (NEW.rights_review_complete
               AND selected_identity.rights_state NOT IN (
                   'CLEARED', 'RESEARCH_ONLY'
               ))
           OR (NEW.privacy_review_complete
               AND selected_identity.privacy_state NOT IN (
                   'NO_PERSONAL_DATA', 'AGGREGATE_ONLY'
               ))
           OR (NEW.research_use_allowed
               AND selected_identity.research_use_decision <> 'ALLOW')
           OR (NEW.model_research_use_allowed
               AND selected_identity.model_research_use_decision <> 'ALLOW')
           OR (NEW.public_corpus_release_allowed
               AND selected_identity.public_corpus_release_decision <> 'ALLOW')
           OR (NEW.raw_public_release_allowed
               AND selected_identity.raw_public_release_decision <> 'ALLOW') THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_partition_source_rights_bound_ck',
                MESSAGE = 'external partition rights or independence claims exceed its registered source decision';
        END IF;
        IF NEW.eligibility_class LIKE 'ELIGIBLE_FOR_%_TRAINING'
           AND selected_identity.candidate_decision NOT IN (
               'ACQUIRE_RESEARCH_ONLY', 'ADMIT_AGGREGATE_ONLY'
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_partition_source_admission_bound_ck',
                MESSAGE = 'external training eligibility requires an admitted research-use source decision';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_training_partition_task_class$;

CREATE TRIGGER training_partition_task_class_biu
BEFORE INSERT OR UPDATE ON ml.training_partition_eligibility
FOR EACH ROW EXECUTE FUNCTION ml.enforce_training_partition_task_class();

CREATE UNIQUE INDEX training_partition_identity_snapshot_uq
ON ml.training_partition_eligibility (
    task_key, source_identity_key, source_version, snapshot_key
);

CREATE FUNCTION ml.protect_bound_training_task()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_bound_training_task$
BEGIN
    IF TG_OP = 'DELETE' AND EXISTS (
        SELECT 1 FROM ml.training_partition_eligibility
        WHERE task_key = OLD.task_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_task_bound_immutable_ck',
            MESSAGE = 'a task referenced by partitions cannot be deleted';
    END IF;
    IF TG_OP = 'UPDATE' AND EXISTS (
        SELECT 1 FROM ml.training_partition_eligibility
        WHERE task_key = OLD.task_key
    ) AND (
        NEW.task_key IS DISTINCT FROM OLD.task_key
        OR NEW.task_type IS DISTINCT FROM OLD.task_type
        OR NEW.task_version IS DISTINCT FROM OLD.task_version
        OR NEW.effective_unit_definition IS DISTINCT FROM
           OLD.effective_unit_definition
        OR NEW.candidate_outcomes IS DISTINCT FROM OLD.candidate_outcomes
        OR NEW.label_semantics IS DISTINCT FROM OLD.label_semantics
        OR NEW.eligibility_rule IS DISTINCT FROM OLD.eligibility_rule
        OR NEW.model_fitting_authorized IS DISTINCT FROM
           OLD.model_fitting_authorized
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_task_bound_immutable_ck',
            MESSAGE = 'task semantics are immutable after partitions exist';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_bound_training_task$;

CREATE TRIGGER training_task_bound_bud
BEFORE UPDATE OR DELETE ON ml.training_task_candidate
FOR EACH ROW EXECUTE FUNCTION ml.protect_bound_training_task();

CREATE FUNCTION audit.protect_bound_round3j_source_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_bound_round3j_source_identity$
BEGIN
    IF OLD.registered_batch_key IS NULL
       OR EXISTS (
        SELECT 1 FROM audit.round3j_acquisition_batch
        WHERE batch_key = OLD.registered_batch_key
          AND lifecycle_status = 'COMPLETE'
    ) OR EXISTS (
        SELECT 1 FROM ml.training_partition_eligibility
        WHERE source_identity_key = OLD.candidate_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3j_source_identity_bound_immutable_ck',
            MESSAGE = 'a baseline, completed-batch, or partition-bound source identity is immutable; register a new versioned candidate instead';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_bound_round3j_source_identity$;

CREATE TRIGGER round3j_source_identity_bound_bud
BEFORE UPDATE OR DELETE ON audit.round3j_source_identity
FOR EACH ROW EXECUTE FUNCTION audit.protect_bound_round3j_source_identity();

CREATE TABLE audit.training_duplicate_group (
    duplicate_group_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    duplicate_reason TEXT NOT NULL,
    detection_method TEXT NOT NULL,
    deterministic_fingerprint TEXT NOT NULL,
    source_family_keys TEXT[] NOT NULL,
    retained_training_unit_key TEXT,
    resolution_status TEXT NOT NULL,
    audit_complete BOOLEAN NOT NULL,
    evidence_path TEXT NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT training_duplicate_group_pk PRIMARY KEY (
        duplicate_group_key
    ),
    CONSTRAINT training_duplicate_group_key_task_uq UNIQUE (
        duplicate_group_key, task_key
    ),
    CONSTRAINT training_duplicate_group_task_fk FOREIGN KEY (
        task_key
    ) REFERENCES ml.training_task_candidate (task_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_duplicate_group_contract_ck CHECK (
        duplicate_group_key = lower(btrim(duplicate_group_key))
        AND duplicate_group_key <> ''
        AND duplicate_reason IN (
            'EXACT_EXPRESSION', 'SOURCE_MIRROR',
            'REPEATED_PRODUCT_SNAPSHOT', 'TEMPLATE_GENERATED_NOTE',
            'PUNCTUATION_VARIANT', 'MACHINE_GENERATED_VARIANT',
            'TRANSLATION_DUPLICATE', 'DERIVED_RAW_OVERLAP',
            'SAME_SAMPLE_REPLICATE'
        )
        AND detection_method IN (
            'HASH_EXACT', 'NORMALIZED_TEXT_RULE', 'METADATA_IDENTITY',
            'TEMPLATE_FINGERPRINT', 'SOURCE_VERSION_LINEAGE',
            'MANUAL_REVIEWED'
        )
        AND deterministic_fingerprint = btrim(deterministic_fingerprint)
        AND deterministic_fingerprint <> ''
        AND cardinality(source_family_keys) >= 1
        AND array_position(source_family_keys, NULL) IS NULL
        AND resolution_status IN (
            'RETAIN_ONE', 'EXCLUDE_ALL', 'EVALUATION_ONLY', 'PENDING'
        )
        AND (retained_training_unit_key IS NULL OR (
            retained_training_unit_key = btrim(retained_training_unit_key)
            AND retained_training_unit_key <> ''
        ))
        AND ((resolution_status = 'RETAIN_ONE') =
             (retained_training_unit_key IS NOT NULL))
        AND audit_complete = (resolution_status <> 'PENDING')
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE UNIQUE INDEX training_duplicate_group_fingerprint_uq
ON audit.training_duplicate_group (task_key, deterministic_fingerprint);

COMMENT ON TABLE audit.training_duplicate_group IS
    'Deterministic exact/near-duplicate and mirror governance; embedding similarity is intentionally absent.';

CREATE FUNCTION audit.lock_round3j_duplicate_fingerprint(
    selected_task_key TEXT,
    selected_fingerprint TEXT
)
RETURNS VOID
LANGUAGE SQL
VOLATILE
STRICT
SET search_path = pg_catalog
AS $lock_round3j_duplicate_fingerprint$
SELECT pg_advisory_xact_lock(hashtextextended(
    'round3j.duplicate|' || selected_task_key || '|' ||
    selected_fingerprint, 0
))
$lock_round3j_duplicate_fingerprint$;

CREATE FUNCTION audit.enforce_duplicate_group_fingerprint_namespace()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_duplicate_group_fingerprint_namespace$
DECLARE old_lock_key TEXT; new_lock_key TEXT;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        old_lock_key := OLD.task_key || '|' || OLD.deterministic_fingerprint;
    END IF;
    new_lock_key := NEW.task_key || '|' || NEW.deterministic_fingerprint;
    IF old_lock_key IS NOT NULL AND old_lock_key <> new_lock_key THEN
        IF old_lock_key < new_lock_key THEN
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                OLD.task_key, OLD.deterministic_fingerprint
            );
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                NEW.task_key, NEW.deterministic_fingerprint
            );
        ELSE
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                NEW.task_key, NEW.deterministic_fingerprint
            );
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                OLD.task_key, OLD.deterministic_fingerprint
            );
        END IF;
    ELSE
        PERFORM audit.lock_round3j_duplicate_fingerprint(
            NEW.task_key, NEW.deterministic_fingerprint
        );
    END IF;
    IF EXISTS (
        SELECT 1 FROM ml.training_example_candidate
        WHERE task_key = NEW.task_key
          AND deterministic_duplicate_fingerprint =
              NEW.deterministic_fingerprint
          AND duplicate_group_key IS NULL
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23505',
            CONSTRAINT = 'training_duplicate_fingerprint_namespace_uq',
            MESSAGE = 'a duplicate-group fingerprint cannot also be declared UNIQUE';
    END IF;
    RETURN NEW;
END;
$enforce_duplicate_group_fingerprint_namespace$;

CREATE TRIGGER training_duplicate_group_fingerprint_namespace_biu
BEFORE INSERT OR UPDATE ON audit.training_duplicate_group
FOR EACH ROW EXECUTE FUNCTION
    audit.enforce_duplicate_group_fingerprint_namespace();

CREATE TABLE audit.training_label_decision (
    label_decision_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    decision_type TEXT NOT NULL,
    decision_version TEXT NOT NULL,
    target_semantics TEXT NOT NULL,
    decision_specification TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    limitation TEXT NOT NULL,
    CONSTRAINT training_label_decision_pk PRIMARY KEY (
        label_decision_key
    ),
    CONSTRAINT training_label_decision_key_task_uq UNIQUE (
        label_decision_key, task_key
    ),
    CONSTRAINT training_label_decision_task_fk FOREIGN KEY (task_key)
        REFERENCES ml.training_task_candidate (task_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_label_decision_contract_ck CHECK (
        label_decision_key = lower(btrim(label_decision_key))
        AND label_decision_key <> ''
        AND decision_type IN (
            'SOURCE_AUTHORED_DIRECT', 'DETERMINISTIC_RULE',
            'RESEARCH_REVIEW', 'MULTI_SOURCE_REVIEW',
            'REJECTION_REVIEW'
        )
        AND decision_version = btrim(decision_version)
        AND decision_version <> ''
        AND target_semantics = btrim(target_semantics)
        AND target_semantics <> ''
        AND decision_specification = btrim(decision_specification)
        AND decision_specification <> ''
        AND lifecycle_status IN ('DRAFT', 'FINAL')
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
        AND evidence_sha256 ~ '^[0-9a-f]{64}$'
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE FUNCTION ml.training_label_provenance_is_complete(provenance JSONB)
RETURNS BOOLEAN
LANGUAGE SQL
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $training_label_provenance_is_complete$
SELECT jsonb_typeof(provenance) = 'object'
   AND provenance ?& ARRAY[
       'source_key', 'source_version', 'snapshot_key',
       'source_file_sha256', 'source_locator',
       'review_or_rule_key', 'target_semantics'
   ]::TEXT[]
   AND jsonb_typeof(provenance -> 'source_key') = 'string'
   AND jsonb_typeof(provenance -> 'source_version') = 'string'
   AND jsonb_typeof(provenance -> 'snapshot_key') = 'string'
   AND jsonb_typeof(provenance -> 'source_file_sha256') = 'string'
   AND jsonb_typeof(provenance -> 'source_locator') = 'string'
   AND jsonb_typeof(provenance -> 'review_or_rule_key') = 'string'
   AND jsonb_typeof(provenance -> 'target_semantics') = 'string'
   AND btrim(provenance ->> 'source_key') <> ''
   AND btrim(provenance ->> 'source_version') <> ''
   AND btrim(provenance ->> 'snapshot_key') <> ''
   AND provenance ->> 'source_file_sha256' ~ '^[0-9a-f]{64}$'
   AND btrim(provenance ->> 'source_locator') <> ''
   AND btrim(provenance ->> 'review_or_rule_key') <> ''
   AND btrim(provenance ->> 'target_semantics') <> ''
$training_label_provenance_is_complete$;

CREATE FUNCTION ml.training_association_outcome_is_complete(outcome JSONB)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
STRICT
PARALLEL SAFE
SET search_path = pg_catalog
AS $training_association_outcome_is_complete$
BEGIN
    RETURN jsonb_typeof(outcome) = 'object'
       AND outcome ?& ARRAY[
           'support_count', 'document_or_sample_count', 'configuration'
       ]::TEXT[]
       AND jsonb_typeof(outcome -> 'support_count') = 'number'
       AND jsonb_typeof(outcome -> 'document_or_sample_count') = 'number'
       AND (outcome ->> 'support_count')::NUMERIC >= 0
       AND (outcome ->> 'support_count')::NUMERIC = trunc(
           (outcome ->> 'support_count')::NUMERIC
       )
       AND (outcome ->> 'document_or_sample_count')::NUMERIC > 0
       AND (outcome ->> 'document_or_sample_count')::NUMERIC = trunc(
           (outcome ->> 'document_or_sample_count')::NUMERIC
       )
       AND jsonb_typeof(outcome -> 'configuration') = 'object'
       AND outcome -> 'configuration' <> '{}'::JSONB;
EXCEPTION WHEN invalid_text_representation OR numeric_value_out_of_range THEN
    RETURN FALSE;
END;
$training_association_outcome_is_complete$;

CREATE TABLE ml.training_example_candidate (
    training_example_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    partition_eligibility_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_version TEXT NOT NULL,
    snapshot_key TEXT NOT NULL,
    document_key TEXT,
    source_locator TEXT NOT NULL,
    effective_unit_key TEXT NOT NULL,
    effective_unit_type TEXT NOT NULL,
    coffee_identity_key TEXT,
    product_identity_key TEXT,
    participant_group_key TEXT,
    roast_batch_key TEXT,
    preparation_condition_key TEXT,
    origin_sample_family_key TEXT,
    language_code TEXT,
    raw_source_phrase TEXT,
    normalized_expression TEXT,
    lexical_outcome TEXT,
    candidate_target_keys TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    evidence_direction TEXT,
    association_observation_type TEXT,
    measurement_method TEXT,
    measurement_semantics TEXT,
    measurement_scale_key TEXT,
    source_local_outcome JSONB NOT NULL DEFAULT '{}'::JSONB,
    label_lifecycle TEXT NOT NULL,
    label_provenance JSONB NOT NULL,
    review_or_rule_key TEXT NOT NULL,
    rights_path TEXT NOT NULL,
    machine_translated BOOLEAN NOT NULL DEFAULT FALSE,
    project_translation BOOLEAN NOT NULL DEFAULT FALSE,
    artificial_variant BOOLEAN NOT NULL DEFAULT FALSE,
    absence_derived_negative BOOLEAN NOT NULL DEFAULT FALSE,
    false_pooled_scale BOOLEAN NOT NULL DEFAULT FALSE,
    deterministic_duplicate_fingerprint TEXT NOT NULL,
    duplicate_group_key TEXT,
    duplicate_disposition TEXT NOT NULL,
    sampling_eligible BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT training_example_candidate_pk PRIMARY KEY (
        training_example_key
    ),
    CONSTRAINT training_example_candidate_key_task_uq UNIQUE (
        training_example_key, task_key
    ),
    CONSTRAINT training_example_candidate_partition_fk FOREIGN KEY (
        partition_eligibility_key, task_key
    ) REFERENCES ml.training_partition_eligibility (
        partition_eligibility_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_example_candidate_duplicate_fk FOREIGN KEY (
        duplicate_group_key, task_key
    ) REFERENCES audit.training_duplicate_group (
        duplicate_group_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_example_candidate_label_decision_fk FOREIGN KEY (
        review_or_rule_key, task_key
    ) REFERENCES audit.training_label_decision (
        label_decision_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_example_candidate_text_ck CHECK (
        training_example_key = lower(btrim(training_example_key))
        AND training_example_key <> ''
        AND source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND source_key = lower(btrim(source_key)) AND source_key <> ''
        AND source_version = btrim(source_version) AND source_version <> ''
        AND snapshot_key = lower(btrim(snapshot_key)) AND snapshot_key <> ''
        AND (document_key IS NULL
             OR (document_key = lower(btrim(document_key))
                 AND document_key <> ''))
        AND source_locator = btrim(source_locator) AND source_locator <> ''
        AND effective_unit_key = btrim(effective_unit_key)
        AND effective_unit_key <> ''
        AND (coffee_identity_key IS NULL OR (
            coffee_identity_key = btrim(coffee_identity_key)
            AND coffee_identity_key <> ''
        ))
        AND (product_identity_key IS NULL OR (
            product_identity_key = btrim(product_identity_key)
            AND product_identity_key <> ''
        ))
        AND (participant_group_key IS NULL OR (
            participant_group_key = btrim(participant_group_key)
            AND participant_group_key <> ''
        ))
        AND (roast_batch_key IS NULL OR (
            roast_batch_key = btrim(roast_batch_key)
            AND roast_batch_key <> ''
        ))
        AND (preparation_condition_key IS NULL OR (
            preparation_condition_key = btrim(preparation_condition_key)
            AND preparation_condition_key <> ''
        ))
        AND (origin_sample_family_key IS NULL OR (
            origin_sample_family_key = btrim(origin_sample_family_key)
            AND origin_sample_family_key <> ''
        ))
        AND (language_code IS NULL
             OR (language_code = btrim(language_code)
                 AND language_code <> ''))
        AND array_position(candidate_target_keys, NULL) IS NULL
        AND jsonb_typeof(source_local_outcome) = 'object'
        AND jsonb_typeof(label_provenance) = 'object'
        AND evidence.round3e_reject_direct_identifiers(
            source_local_outcome
        )
        AND evidence.round3e_reject_direct_identifiers(label_provenance)
        AND review_or_rule_key = btrim(review_or_rule_key)
        AND review_or_rule_key <> ''
        AND rights_path = btrim(rights_path) AND rights_path <> ''
        AND deterministic_duplicate_fingerprint ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT training_example_candidate_label_ck CHECK (
        label_lifecycle IN (
            'RAW', 'DETERMINISTIC_DERIVED', 'RESEARCH_REVIEWED',
            'MULTI_SOURCE_SUPPORTED', 'TRAINING_ELIGIBLE',
            'EVALUATION_ONLY', 'REJECTED'
        )
        AND (lexical_outcome IS NULL OR lexical_outcome IN (
            'ONE_CANONICAL_TARGET', 'MULTIPLE_PLAUSIBLE_TARGETS',
            'RANGE_LEVEL_TARGET', 'SOURCE_LOCAL_ONLY', 'AMBIGUOUS',
            'UNRESOLVED', 'ABSTAIN', 'OUTSIDE_CURRENT_ONTOLOGY'
        ))
        AND (evidence_direction IS NULL OR evidence_direction IN (
            'SUPPORTS', 'CHALLENGES', 'MIXED',
            'INSUFFICIENT', 'OUT_OF_SCOPE'
        ))
        AND (association_observation_type IS NULL
             OR association_observation_type IN (
                'CO_OCCURRENCE_PAIR', 'CO_SELECTION_PAIR',
                'DESCRIPTOR_PAIR_COUNT', 'RANGE_MEMBERSHIP',
                'EXPLICIT_CONTRAST'
             ))
        AND NOT absence_derived_negative
        AND NOT false_pooled_scale
        AND duplicate_disposition IN (
            'UNIQUE', 'RETAINED', 'EXCLUDED', 'EVALUATION_ONLY'
        )
        AND ((duplicate_group_key IS NULL
              AND duplicate_disposition = 'UNIQUE')
             OR (duplicate_group_key IS NOT NULL
                 AND duplicate_disposition <> 'UNIQUE'))
        AND sampling_eligible = (
            label_lifecycle = 'TRAINING_ELIGIBLE'
            AND duplicate_disposition IN ('UNIQUE', 'RETAINED')
            AND NOT machine_translated
            AND NOT project_translation
            AND NOT artificial_variant
        )
        AND (label_lifecycle = 'RAW'
             OR ml.training_label_provenance_is_complete(
                 label_provenance
             ))
    )
);

CREATE INDEX training_example_candidate_task_unit_ix
ON ml.training_example_candidate (
    task_key, effective_unit_type, effective_unit_key
);

CREATE UNIQUE INDEX training_example_candidate_effective_unit_uq
ON ml.training_example_candidate (
    task_key, source_family_key, effective_unit_key
);

CREATE UNIQUE INDEX training_example_candidate_unique_fingerprint_uq
ON ml.training_example_candidate (
    task_key, deterministic_duplicate_fingerprint
)
WHERE duplicate_group_key IS NULL;

CREATE INDEX training_example_candidate_source_family_ix
ON ml.training_example_candidate (task_key, source_family_key);

CREATE UNIQUE INDEX training_example_candidate_duplicate_retained_uq
ON ml.training_example_candidate (duplicate_group_key)
WHERE duplicate_disposition = 'RETAINED';

CREATE FUNCTION ml.enforce_training_example_contract()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_training_example_contract$
DECLARE
    selected_task_type TEXT;
    selected_partition ml.training_partition_eligibility%ROWTYPE;
    selected_duplicate audit.training_duplicate_group%ROWTYPE;
    selected_label_decision audit.training_label_decision%ROWTYPE;
    target_count INTEGER;
    distinct_target_count INTEGER;
    old_duplicate_lock_key TEXT;
    new_duplicate_lock_key TEXT;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        old_duplicate_lock_key := OLD.task_key || '|' ||
            OLD.deterministic_duplicate_fingerprint;
    END IF;
    new_duplicate_lock_key := NEW.task_key || '|' ||
        NEW.deterministic_duplicate_fingerprint;
    IF old_duplicate_lock_key IS NOT NULL
       AND old_duplicate_lock_key <> new_duplicate_lock_key THEN
        IF old_duplicate_lock_key < new_duplicate_lock_key THEN
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                OLD.task_key, OLD.deterministic_duplicate_fingerprint
            );
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                NEW.task_key, NEW.deterministic_duplicate_fingerprint
            );
        ELSE
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                NEW.task_key, NEW.deterministic_duplicate_fingerprint
            );
            PERFORM audit.lock_round3j_duplicate_fingerprint(
                OLD.task_key, OLD.deterministic_duplicate_fingerprint
            );
        END IF;
    ELSE
        PERFORM audit.lock_round3j_duplicate_fingerprint(
            NEW.task_key, NEW.deterministic_duplicate_fingerprint
        );
    END IF;
    IF NEW.duplicate_group_key IS NULL AND EXISTS (
        SELECT 1 FROM audit.training_duplicate_group
        WHERE task_key = NEW.task_key
          AND deterministic_fingerprint =
              NEW.deterministic_duplicate_fingerprint
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23505',
            CONSTRAINT = 'training_duplicate_fingerprint_namespace_uq',
            MESSAGE = 'a UNIQUE example fingerprint cannot already belong to a duplicate group';
    END IF;
    SELECT * INTO selected_partition
    FROM ml.training_partition_eligibility
    WHERE partition_eligibility_key = NEW.partition_eligibility_key;
    SELECT task_type INTO selected_task_type
    FROM ml.training_task_candidate WHERE task_key = NEW.task_key;
    SELECT * INTO selected_label_decision
    FROM audit.training_label_decision
    WHERE label_decision_key = NEW.review_or_rule_key
      AND task_key = NEW.task_key;

    IF selected_partition.source_family_key <> NEW.source_family_key
       OR selected_partition.source_key <> NEW.source_key
       OR selected_partition.source_version <> NEW.source_version
       OR selected_partition.snapshot_key <> NEW.snapshot_key
       OR selected_partition.effective_unit_type <> NEW.effective_unit_type THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_partition_provenance_ck',
            MESSAGE = 'example provenance or effective-unit type differs from its reviewed partition';
    END IF;

    IF NEW.label_lifecycle <> 'RAW'
       AND (NEW.label_provenance ->> 'source_key' <> NEW.source_key
            OR NEW.label_provenance ->> 'source_version' <>
               NEW.source_version
            OR NEW.label_provenance ->> 'snapshot_key' <>
               NEW.snapshot_key
            OR NEW.label_provenance ->> 'source_locator' <>
               NEW.source_locator
            OR NEW.label_provenance ->> 'review_or_rule_key' <>
               NEW.review_or_rule_key) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_label_provenance_bound_ck',
            MESSAGE = 'label provenance must exactly identify the example source, snapshot, locator, and decision';
    END IF;
    IF NEW.label_lifecycle <> 'RAW'
       AND (selected_label_decision.lifecycle_status <> 'FINAL'
            OR selected_label_decision.target_semantics <>
               NEW.label_provenance ->> 'target_semantics') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_label_decision_final_ck',
            MESSAGE = 'non-raw labels require a final registered decision with matching target semantics';
    END IF;
    IF NEW.label_lifecycle <> 'RAW' AND NOT EXISTS (
        SELECT 1
        FROM jsonb_array_elements(
            selected_partition.source_file_manifest
        ) AS item(value)
        WHERE item.value ->> 'sha256' =
              NEW.label_provenance ->> 'source_file_sha256'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_source_file_hash_bound_ck',
            MESSAGE = 'label source-file hash must occur in the reviewed partition manifest';
    END IF;

    IF NEW.label_lifecycle = 'TRAINING_ELIGIBLE'
       AND selected_partition.eligibility_class <> (CASE selected_task_type
            WHEN 'LEXICAL_NORMALIZATION'
                THEN 'ELIGIBLE_FOR_LEXICAL_TRAINING'
            WHEN 'ASSOCIATION_MODEL'
                THEN 'ELIGIBLE_FOR_ASSOCIATION_TRAINING'
            WHEN 'CONTEXT_MODEL'
                THEN 'ELIGIBLE_FOR_CONTEXT_TRAINING'
            ELSE '__PROHIBITED__' END) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_partition_eligibility_ck',
            MESSAGE = 'a training-eligible example requires matching partition eligibility';
    END IF;

    target_count := cardinality(NEW.candidate_target_keys);
    SELECT count(DISTINCT target_key)::INTEGER
    INTO distinct_target_count
    FROM unnest(NEW.candidate_target_keys) AS target(target_key);
    IF target_count <> distinct_target_count THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_candidate_targets_unique_ck',
            MESSAGE = 'candidate target keys must be unique';
    END IF;
    IF selected_task_type = 'LEXICAL_NORMALIZATION' THEN
        IF NEW.effective_unit_type <> 'UNIQUE_EXPRESSION'
           OR NEW.language_code IS NULL OR NEW.raw_source_phrase IS NULL
           OR btrim(NEW.raw_source_phrase) = ''
           OR NEW.normalized_expression IS NULL
           OR btrim(NEW.normalized_expression) = ''
           OR NEW.lexical_outcome IS NULL
           OR NEW.evidence_direction IS NOT NULL
           OR NEW.association_observation_type IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_lexical_shape_ck',
                MESSAGE = 'lexical examples require expression, language, and explicit disposition';
        END IF;
        IF (NEW.lexical_outcome = 'ONE_CANONICAL_TARGET'
            AND target_count <> 1)
           OR (NEW.lexical_outcome = 'MULTIPLE_PLAUSIBLE_TARGETS'
               AND target_count < 2)
           OR (NEW.lexical_outcome = 'RANGE_LEVEL_TARGET'
               AND target_count < 1)
           OR (NEW.lexical_outcome IN (
                'SOURCE_LOCAL_ONLY', 'UNRESOLVED',
                'ABSTAIN', 'OUTSIDE_CURRENT_ONTOLOGY'
               ) AND target_count <> 0) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_lexical_target_cardinality_ck',
                MESSAGE = 'lexical target count does not match its disposition';
        END IF;
        IF NEW.lexical_outcome IN (
               'ONE_CANONICAL_TARGET', 'MULTIPLE_PLAUSIBLE_TARGETS'
           ) AND EXISTS (
               SELECT 1
               FROM unnest(NEW.candidate_target_keys) AS target(target_key)
               WHERE NOT EXISTS (
                   SELECT 1 FROM kb.concept
                   WHERE concept_key = target.target_key
               )
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23503',
                CONSTRAINT = 'training_example_concept_target_fk',
                MESSAGE = 'canonical lexical targets must exist in kb.concept';
        END IF;
        IF NEW.lexical_outcome = 'RANGE_LEVEL_TARGET'
           AND EXISTS (
               SELECT 1
               FROM unnest(NEW.candidate_target_keys) AS target(target_key)
               WHERE NOT EXISTS (
                   SELECT 1 FROM corpus.association_range
                   WHERE range_key = target.target_key
               )
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23503',
                CONSTRAINT = 'training_example_range_target_fk',
                MESSAGE = 'range-level lexical targets must exist in corpus.association_range';
        END IF;
    ELSIF selected_task_type = 'ASSOCIATION_MODEL' THEN
        IF NEW.effective_unit_type <> 'SOURCE_QUALIFIED_RELATIONSHIP'
           OR NEW.evidence_direction IS NULL
           OR NEW.association_observation_type IS NULL
           OR NEW.measurement_method IS NULL
           OR btrim(NEW.measurement_method) = ''
           OR NEW.measurement_semantics IS NULL
           OR btrim(NEW.measurement_semantics) = ''
           OR NEW.lexical_outcome IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_association_shape_ck',
                MESSAGE = 'association examples require source-local method, semantics, and evidence direction';
        END IF;
        IF NEW.label_lifecycle IN (
               'TRAINING_ELIGIBLE', 'EVALUATION_ONLY'
           ) AND NOT ml.training_association_outcome_is_complete(
               NEW.source_local_outcome
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_association_outcome_ck',
                MESSAGE = 'association candidates require source-local support, document/sample count, and configuration';
        END IF;
        IF NEW.label_lifecycle IN (
               'TRAINING_ELIGIBLE', 'EVALUATION_ONLY'
           ) AND NEW.evidence_direction IN (
               'SUPPORTS', 'CHALLENGES', 'MIXED'
           ) AND (NEW.source_local_outcome ->> 'support_count')::NUMERIC <= 0
        THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_association_explicit_support_ck',
                MESSAGE = 'supporting, challenging, or mixed association evidence requires a positive explicit support count';
        END IF;
        IF NEW.label_lifecycle IN (
               'TRAINING_ELIGIBLE', 'EVALUATION_ONLY'
           ) AND (
               (NEW.association_observation_type IN (
                    'CO_OCCURRENCE_PAIR', 'CO_SELECTION_PAIR',
                    'DESCRIPTOR_PAIR_COUNT'
                ) AND (target_count <> 2 OR EXISTS (
                    SELECT 1
                    FROM unnest(NEW.candidate_target_keys)
                         AS target(target_key)
                    WHERE NOT EXISTS (
                        SELECT 1 FROM kb.concept
                        WHERE concept_key = target.target_key
                    )
                )))
               OR (NEW.association_observation_type = 'RANGE_MEMBERSHIP'
                   AND (target_count <> 2
                        OR (SELECT count(*) FROM unnest(
                              NEW.candidate_target_keys
                            ) AS target(target_key)
                            WHERE EXISTS (
                              SELECT 1 FROM corpus.association_range
                              WHERE range_key = target.target_key
                            )) <> 1
                        OR (SELECT count(*) FROM unnest(
                              NEW.candidate_target_keys
                            ) AS target(target_key)
                            WHERE EXISTS (
                              SELECT 1 FROM kb.concept
                              WHERE concept_key = target.target_key
                            )) <> 1))
               OR (NEW.association_observation_type = 'EXPLICIT_CONTRAST'
                   AND (target_count < 1 OR EXISTS (
                       SELECT 1
                       FROM unnest(NEW.candidate_target_keys)
                            AS target(target_key)
                       WHERE NOT EXISTS (
                           SELECT 1 FROM kb.concept
                           WHERE concept_key = target.target_key
                       ) AND NOT EXISTS (
                           SELECT 1 FROM corpus.association_range
                           WHERE range_key = target.target_key
                       )
                   )))
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_association_target_shape_ck',
                MESSAGE = 'association target keys must match pair, range-membership, or explicit-contrast semantics';
        END IF;
    ELSIF selected_task_type = 'CONTEXT_MODEL' THEN
        IF NEW.effective_unit_type <> 'COFFEE_SAMPLE_CONFIGURATION'
           OR NEW.coffee_identity_key IS NULL
           OR NEW.preparation_condition_key IS NULL
           OR NEW.roast_batch_key IS NULL
           OR NEW.measurement_method IS NULL
           OR btrim(NEW.measurement_method) = ''
           OR NEW.measurement_semantics IS NULL
           OR btrim(NEW.measurement_semantics) = ''
           OR NEW.source_local_outcome = '{}'::JSONB
           OR NEW.lexical_outcome IS NOT NULL
           OR NEW.evidence_direction IS NOT NULL
           OR NEW.association_observation_type IS NOT NULL THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_context_shape_ck',
                MESSAGE = 'context examples require an observed coffee/preparation/roast unit and source-local outcome semantics';
        END IF;
    ELSIF selected_task_type IN ('QUESTION_MODEL', 'ADAPTIVE_POLICY')
          AND NEW.label_lifecycle = 'TRAINING_ELIGIBLE' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_round3j_user_task_prohibited_ck',
            MESSAGE = 'question and adaptive-policy training examples are not eligible in Round 3J';
    END IF;

    IF NEW.duplicate_group_key IS NOT NULL THEN
        SELECT * INTO selected_duplicate
        FROM audit.training_duplicate_group
        WHERE duplicate_group_key = NEW.duplicate_group_key;
        IF NOT selected_duplicate.audit_complete
           AND NEW.label_lifecycle IN (
                'TRAINING_ELIGIBLE', 'EVALUATION_ONLY'
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_duplicate_audit_ck',
                MESSAGE = 'an unresolved duplicate group cannot enter candidate splits';
        END IF;
        IF selected_duplicate.deterministic_fingerprint <>
           NEW.deterministic_duplicate_fingerprint THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_duplicate_fingerprint_bound_ck',
                MESSAGE = 'example duplicate fingerprint must match its governed duplicate group';
        END IF;
        IF NEW.duplicate_disposition = 'RETAINED'
           AND selected_duplicate.retained_training_unit_key <>
               NEW.effective_unit_key THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_example_duplicate_retained_unit_ck',
                MESSAGE = 'retained duplicate does not match the group decision';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_training_example_contract$;

CREATE TRIGGER training_example_contract_biu
BEFORE INSERT OR UPDATE ON ml.training_example_candidate
FOR EACH ROW EXECUTE FUNCTION ml.enforce_training_example_contract();

CREATE FUNCTION ml.protect_bound_training_partition()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_bound_training_partition$
BEGIN
    IF EXISTS (
        SELECT 1 FROM ml.training_example_candidate
        WHERE partition_eligibility_key = OLD.partition_eligibility_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_partition_bound_immutable_ck',
            MESSAGE = 'a partition referenced by training examples is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_bound_training_partition$;

CREATE TRIGGER training_partition_bound_bud
BEFORE UPDATE OR DELETE ON ml.training_partition_eligibility
FOR EACH ROW EXECUTE FUNCTION ml.protect_bound_training_partition();

CREATE FUNCTION audit.protect_bound_training_duplicate_group()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_bound_training_duplicate_group$
BEGIN
    IF EXISTS (
        SELECT 1 FROM ml.training_example_candidate
        WHERE duplicate_group_key = OLD.duplicate_group_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_duplicate_group_bound_immutable_ck',
            MESSAGE = 'a duplicate group referenced by training examples is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_bound_training_duplicate_group$;

CREATE TRIGGER training_duplicate_group_bound_bud
BEFORE UPDATE OR DELETE ON audit.training_duplicate_group
FOR EACH ROW EXECUTE FUNCTION audit.protect_bound_training_duplicate_group();

CREATE FUNCTION audit.protect_bound_training_label_decision()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_bound_training_label_decision$
BEGIN
    IF OLD.lifecycle_status = 'FINAL' OR EXISTS (
        SELECT 1 FROM ml.training_example_candidate
        WHERE review_or_rule_key = OLD.label_decision_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_label_decision_final_immutable_ck',
            MESSAGE = 'a final or referenced label decision is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_bound_training_label_decision$;

CREATE TRIGGER training_label_decision_final_bud
BEFORE UPDATE OR DELETE ON audit.training_label_decision
FOR EACH ROW EXECUTE FUNCTION audit.protect_bound_training_label_decision();

CREATE TABLE ml.training_sampling_policy (
    sampling_policy_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    corpus_scope TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    deterministic_configuration JSONB NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    randomness_used BOOLEAN NOT NULL,
    random_seed BIGINT,
    maximum_source_family_share NUMERIC(9,8) NOT NULL,
    full_governed_corpus_preserved BOOLEAN NOT NULL,
    candidate_manifest_path TEXT,
    candidate_manifest_sha256 TEXT,
    lifecycle_status TEXT NOT NULL,
    limitation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT training_sampling_policy_pk PRIMARY KEY (
        sampling_policy_key
    ),
    CONSTRAINT training_sampling_policy_key_task_uq UNIQUE (
        sampling_policy_key, task_key
    ),
    CONSTRAINT training_sampling_policy_key_hash_uq UNIQUE (
        sampling_policy_key, configuration_sha256
    ),
    CONSTRAINT training_sampling_policy_task_fk FOREIGN KEY (
        task_key
    ) REFERENCES ml.training_task_candidate (task_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_sampling_policy_contract_ck CHECK (
        sampling_policy_key = lower(btrim(sampling_policy_key))
        AND sampling_policy_key <> ''
        AND policy_version = btrim(policy_version) AND policy_version <> ''
        AND corpus_scope = 'FULL_GOVERNED_CORPUS_TO_CANDIDATE'
        AND policy_type IN (
            'FULL_RETENTION', 'SOURCE_FAMILY_CAP',
            'STRATIFIED_SOURCE_FAMILY_CAP', 'REVIEWED_EXCLUSIONS_ONLY'
        )
        AND jsonb_typeof(deterministic_configuration) = 'object'
        AND deterministic_configuration <> '{}'::JSONB
        AND configuration_sha256 = audit.round3i_utf8_sha256(
            deterministic_configuration::TEXT
        )
        AND randomness_used = (random_seed IS NOT NULL)
        AND maximum_source_family_share > 0
        AND maximum_source_family_share <= 0.60000000
        AND full_governed_corpus_preserved
        AND lifecycle_status IN ('DRAFT', 'VALIDATED', 'FROZEN')
        AND (candidate_manifest_path IS NULL OR (
            candidate_manifest_path = btrim(candidate_manifest_path)
            AND candidate_manifest_path <> ''
        ))
        AND (candidate_manifest_sha256 IS NULL
             OR candidate_manifest_sha256 ~ '^[0-9a-f]{64}$')
        AND (lifecycle_status = 'DRAFT' OR (
            candidate_manifest_path IS NOT NULL
            AND candidate_manifest_sha256 IS NOT NULL
        ))
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

COMMENT ON TABLE ml.training_sampling_policy IS
    'A deterministic candidate-manifest policy; it never deletes observations from the full governed corpus.';

CREATE FUNCTION ml.lock_round3j_task_corpus(selected_task_key TEXT)
RETURNS VOID
LANGUAGE SQL
VOLATILE
STRICT
SET search_path = pg_catalog
AS $lock_round3j_task_corpus$
SELECT pg_advisory_xact_lock(hashtextextended(
    'round3j.training-corpus|' || selected_task_key, 0
))
$lock_round3j_task_corpus$;

CREATE FUNCTION ml.protect_frozen_task_example()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_task_example$
DECLARE old_task TEXT; new_task TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN old_task := OLD.task_key; END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN new_task := NEW.task_key; END IF;
    IF old_task IS NOT NULL AND new_task IS NOT NULL
       AND old_task <> new_task THEN
        PERFORM ml.lock_round3j_task_corpus(least(old_task, new_task));
        PERFORM ml.lock_round3j_task_corpus(greatest(old_task, new_task));
    ELSE
        PERFORM ml.lock_round3j_task_corpus(
            coalesce(old_task, new_task)
        );
    END IF;
    IF EXISTS (
        SELECT 1 FROM ml.training_sampling_policy
        WHERE task_key IN (
            coalesce(old_task, '__none__'),
            coalesce(new_task, '__none__')
        )
          AND lifecycle_status = 'FROZEN'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_frozen_policy_immutable_ck',
            MESSAGE = 'no example may be inserted, changed, or deleted after its task sampling policy is frozen';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_frozen_task_example$;

CREATE TRIGGER training_example_frozen_policy_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.training_example_candidate
FOR EACH ROW EXECUTE FUNCTION ml.protect_frozen_task_example();

CREATE FUNCTION ml.protect_frozen_task_partition()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_task_partition$
DECLARE old_task TEXT; new_task TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN old_task := OLD.task_key; END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN new_task := NEW.task_key; END IF;
    IF old_task IS NOT NULL AND new_task IS NOT NULL
       AND old_task <> new_task THEN
        PERFORM ml.lock_round3j_task_corpus(least(old_task, new_task));
        PERFORM ml.lock_round3j_task_corpus(greatest(old_task, new_task));
    ELSE
        PERFORM ml.lock_round3j_task_corpus(
            coalesce(old_task, new_task)
        );
    END IF;
    IF EXISTS (
        SELECT 1 FROM ml.training_sampling_policy
        WHERE task_key IN (
            coalesce(old_task, '__none__'),
            coalesce(new_task, '__none__')
        )
          AND lifecycle_status = 'FROZEN'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_partition_frozen_policy_immutable_ck',
            MESSAGE = 'no partition may be inserted, changed, or deleted after its task sampling policy is frozen';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_frozen_task_partition$;

CREATE TRIGGER training_partition_frozen_policy_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.training_partition_eligibility
FOR EACH ROW EXECUTE FUNCTION ml.protect_frozen_task_partition();

CREATE TABLE ml.training_sampling_allocation (
    sampling_allocation_key TEXT NOT NULL,
    sampling_policy_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    original_count INTEGER NOT NULL,
    retained_count INTEGER NOT NULL,
    duplicate_excluded_count INTEGER NOT NULL,
    rights_excluded_count INTEGER NOT NULL,
    evaluation_reserved_count INTEGER NOT NULL,
    other_reviewed_excluded_count INTEGER NOT NULL,
    sampling_reason TEXT NOT NULL,
    configuration_sha256 TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    CONSTRAINT training_sampling_allocation_pk PRIMARY KEY (
        sampling_allocation_key
    ),
    CONSTRAINT training_sampling_allocation_policy_family_uq UNIQUE (
        sampling_policy_key, source_family_key
    ),
    CONSTRAINT training_sampling_allocation_policy_fk FOREIGN KEY (
        sampling_policy_key, task_key
    ) REFERENCES ml.training_sampling_policy (
        sampling_policy_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_sampling_allocation_policy_hash_fk FOREIGN KEY (
        sampling_policy_key, configuration_sha256
    ) REFERENCES ml.training_sampling_policy (
        sampling_policy_key, configuration_sha256
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_sampling_allocation_contract_ck CHECK (
        sampling_allocation_key = lower(btrim(sampling_allocation_key))
        AND sampling_allocation_key <> ''
        AND source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND original_count >= 0 AND retained_count >= 0
        AND duplicate_excluded_count >= 0
        AND rights_excluded_count >= 0
        AND evaluation_reserved_count >= 0
        AND other_reviewed_excluded_count >= 0
        AND retained_count + duplicate_excluded_count
            + rights_excluded_count + evaluation_reserved_count
            + other_reviewed_excluded_count = original_count
        AND sampling_reason IN (
            'FULL_RETENTION', 'SOURCE_FAMILY_CAP',
            'DUPLICATE_EXCLUSION', 'RIGHTS_EXCLUSION',
            'EVALUATION_RESERVATION', 'MULTIPLE_REVIEWED_REASONS'
        )
        AND (retained_count = original_count
             OR sampling_reason <> 'FULL_RETENTION')
        AND configuration_sha256 ~ '^[0-9a-f]{64}$'
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
    )
);

CREATE TABLE audit.training_source_concentration (
    concentration_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    sampling_policy_key TEXT NOT NULL,
    corpus_scope TEXT NOT NULL,
    total_effective_unit_count INTEGER NOT NULL,
    contributing_source_family_count INTEGER NOT NULL,
    largest_source_family_share NUMERIC(12,10) NOT NULL,
    top_three_source_family_share NUMERIC(12,10) NOT NULL,
    hhi NUMERIC(12,10) NOT NULL,
    effective_source_family_count NUMERIC(14,8) NOT NULL,
    gate_status TEXT NOT NULL,
    calculation_method TEXT NOT NULL,
    calculation_sha256 TEXT NOT NULL,
    calculated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT training_source_concentration_pk PRIMARY KEY (
        concentration_key
    ),
    CONSTRAINT training_source_concentration_scope_uq UNIQUE (
        task_key, sampling_policy_key, corpus_scope
    ),
    CONSTRAINT training_source_concentration_policy_fk FOREIGN KEY (
        sampling_policy_key, task_key
    ) REFERENCES ml.training_sampling_policy (
        sampling_policy_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_source_concentration_contract_ck CHECK (
        concentration_key = lower(btrim(concentration_key))
        AND concentration_key <> ''
        AND corpus_scope IN ('RAW_CORPUS', 'TRAINING_CANDIDATE')
        AND total_effective_unit_count > 0
        AND contributing_source_family_count > 0
        AND largest_source_family_share > 0
        AND largest_source_family_share <= 1
        AND top_three_source_family_share >= largest_source_family_share
        AND top_three_source_family_share <= 1
        AND hhi > 0 AND hhi <= 1
        AND effective_source_family_count >= 1
        AND gate_status IN (
            'NOT_APPLICABLE', 'PASS_MINIMUM',
            'PASS_PREFERRED', 'FAIL'
        )
        AND ((corpus_scope = 'RAW_CORPUS'
              AND gate_status = 'NOT_APPLICABLE')
             OR (corpus_scope = 'TRAINING_CANDIDATE'
                 AND gate_status = CASE
                    WHEN largest_source_family_share <= 0.4500000000
                        THEN 'PASS_PREFERRED'
                    WHEN largest_source_family_share <= 0.6000000000
                        THEN 'PASS_MINIMUM'
                    ELSE 'FAIL' END))
        AND calculation_method = btrim(calculation_method)
        AND calculation_method <> ''
        AND calculation_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE FUNCTION audit.enforce_training_source_concentration()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_training_source_concentration$
DECLARE
    computed_total NUMERIC;
    computed_family_count INTEGER;
    computed_largest NUMERIC;
    computed_top_three NUMERIC;
    computed_hhi NUMERIC;
    computed_effective NUMERIC;
    expected_calculation_hash TEXT;
BEGIN
    PERFORM ml.lock_round3j_task_corpus(NEW.task_key);
    WITH family_counts AS (
        SELECT source_family_key,
               CASE NEW.corpus_scope
                 WHEN 'RAW_CORPUS' THEN original_count
                 ELSE retained_count END::NUMERIC AS unit_count
        FROM ml.training_sampling_allocation
        WHERE sampling_policy_key = NEW.sampling_policy_key
    ), positive AS (
        SELECT source_family_key, unit_count,
               unit_count / sum(unit_count) OVER () AS share
        FROM family_counts WHERE unit_count > 0
    ), ranked AS (
        SELECT *, row_number() OVER (
            ORDER BY share DESC, source_family_key
        ) AS share_rank
        FROM positive
    )
    SELECT sum(unit_count), count(*)::INTEGER, max(share),
           sum(share) FILTER (WHERE share_rank <= 3),
           sum(share * share), 1 / sum(share * share)
    INTO computed_total, computed_family_count, computed_largest,
         computed_top_three, computed_hhi, computed_effective
    FROM ranked;

    expected_calculation_hash := audit.round3i_utf8_sha256(
        jsonb_build_object(
            'task_key', NEW.task_key,
            'sampling_policy_key', NEW.sampling_policy_key,
            'corpus_scope', NEW.corpus_scope,
            'total_effective_unit_count', NEW.total_effective_unit_count,
            'contributing_source_family_count',
                NEW.contributing_source_family_count,
            'largest_source_family_share',
                NEW.largest_source_family_share,
            'top_three_source_family_share',
                NEW.top_three_source_family_share,
            'hhi', NEW.hhi,
            'effective_source_family_count',
                NEW.effective_source_family_count,
            'gate_status', NEW.gate_status,
            'calculation_method', NEW.calculation_method
        )::TEXT
    );

    IF computed_total IS NULL
       OR NEW.total_effective_unit_count <> computed_total
       OR NEW.contributing_source_family_count <> computed_family_count
       OR abs(NEW.largest_source_family_share - computed_largest) > 0.00000001
       OR abs(NEW.top_three_source_family_share - computed_top_three) > 0.00000001
       OR abs(NEW.hhi - computed_hhi) > 0.00000001
       OR abs(NEW.effective_source_family_count - computed_effective) > 0.000001
       OR NEW.calculation_sha256 <> expected_calculation_hash THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_source_concentration_recomputed_ck',
            MESSAGE = 'stored concentration metrics do not match sampling allocations';
    END IF;
    RETURN NEW;
END;
$enforce_training_source_concentration$;

CREATE TRIGGER training_source_concentration_biu
BEFORE INSERT OR UPDATE ON audit.training_source_concentration
FOR EACH ROW EXECUTE FUNCTION audit.enforce_training_source_concentration();

CREATE TABLE ml.training_split_candidate (
    split_candidate_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    sampling_policy_key TEXT NOT NULL,
    split_strategy TEXT NOT NULL,
    grouping_keys TEXT[] NOT NULL,
    prohibited_cross_split_keys TEXT[] NOT NULL,
    deterministic_seed BIGINT NOT NULL,
    readiness_primary BOOLEAN NOT NULL DEFAULT FALSE,
    lifecycle_status TEXT NOT NULL,
    split_feasible BOOLEAN NOT NULL,
    held_out_source_family_count INTEGER NOT NULL,
    train_count INTEGER NOT NULL,
    dev_count INTEGER NOT NULL,
    test_count INTEGER NOT NULL,
    manifest_path TEXT,
    manifest_sha256 TEXT,
    limitation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT training_split_candidate_pk PRIMARY KEY (
        split_candidate_key
    ),
    CONSTRAINT training_split_candidate_key_task_uq UNIQUE (
        split_candidate_key, task_key
    ),
    CONSTRAINT training_split_candidate_task_strategy_uq UNIQUE (
        task_key, split_strategy
    ),
    CONSTRAINT training_split_candidate_policy_fk FOREIGN KEY (
        sampling_policy_key, task_key
    ) REFERENCES ml.training_sampling_policy (
        sampling_policy_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_split_candidate_contract_ck CHECK (
        split_candidate_key = lower(btrim(split_candidate_key))
        AND split_candidate_key <> ''
        AND split_strategy IN (
            'SOURCE_FAMILY_HOLDOUT', 'COFFEE_IDENTITY_HOLDOUT',
            'HYBRID_GROUPED_SPLIT', 'ZH_HANS_STRATIFIED_TEST',
            'AMBIGUOUS_EXPRESSION_TEST', 'ABSTENTION_TEST'
        )
        AND cardinality(grouping_keys) >= 1
        AND cardinality(prohibited_cross_split_keys) >= 1
        AND array_position(grouping_keys, NULL) IS NULL
        AND array_position(prohibited_cross_split_keys, NULL) IS NULL
        AND grouping_keys <@ ARRAY[
            'source_family', 'coffee_identity', 'product_identity',
            'participant', 'roast_batch', 'preparation_condition',
            'origin_sample_family', 'duplicate_group'
        ]::TEXT[]
        AND prohibited_cross_split_keys <@ grouping_keys
        AND grouping_keys @> ARRAY['duplicate_group']::TEXT[]
        AND prohibited_cross_split_keys
            @> ARRAY['duplicate_group']::TEXT[]
        AND (NOT readiness_primary OR split_strategy IN (
            'SOURCE_FAMILY_HOLDOUT', 'COFFEE_IDENTITY_HOLDOUT',
            'HYBRID_GROUPED_SPLIT'
        ))
        AND lifecycle_status IN ('DEFINED', 'ASSIGNED', 'VALIDATED', 'REJECTED')
        AND held_out_source_family_count >= 0
        AND train_count >= 0 AND dev_count >= 0 AND test_count >= 0
        AND (manifest_path IS NULL OR (
            manifest_path = btrim(manifest_path) AND manifest_path <> ''
        ))
        AND (manifest_sha256 IS NULL
             OR manifest_sha256 ~ '^[0-9a-f]{64}$')
        AND (lifecycle_status <> 'VALIDATED' OR (
            split_feasible AND train_count > 0
            AND dev_count > 0 AND test_count > 0
            AND manifest_path IS NOT NULL AND manifest_sha256 IS NOT NULL
        ))
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE UNIQUE INDEX training_split_candidate_primary_task_uq
ON ml.training_split_candidate (task_key)
WHERE readiness_primary;

CREATE FUNCTION ml.enforce_training_split_strategy()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_training_split_strategy$
DECLARE selected_task_type TEXT;
BEGIN
    SELECT task_type INTO selected_task_type
    FROM ml.training_task_candidate WHERE task_key = NEW.task_key;
    IF NEW.split_strategy IN (
        'SOURCE_FAMILY_HOLDOUT', 'ZH_HANS_STRATIFIED_TEST',
        'AMBIGUOUS_EXPRESSION_TEST', 'ABSTENTION_TEST'
       ) AND (
          NOT (NEW.grouping_keys @> ARRAY['source_family']::TEXT[])
          OR NOT (NEW.prohibited_cross_split_keys @>
                  ARRAY['source_family']::TEXT[])
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_source_family_group_ck',
            MESSAGE = 'this split strategy requires source-family grouping';
    END IF;
    IF NEW.split_strategy = 'COFFEE_IDENTITY_HOLDOUT'
       AND (NOT (NEW.grouping_keys @> ARRAY['coffee_identity']::TEXT[])
            OR NOT (NEW.prohibited_cross_split_keys @>
                    ARRAY['coffee_identity']::TEXT[])) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_coffee_identity_group_ck',
            MESSAGE = 'coffee-identity holdout requires coffee grouping';
    END IF;
    IF NEW.split_strategy = 'HYBRID_GROUPED_SPLIT'
       AND (NOT (NEW.grouping_keys @> ARRAY['source_family']::TEXT[])
            OR NOT (NEW.prohibited_cross_split_keys @>
                    ARRAY['source_family']::TEXT[])
            OR NOT (NEW.grouping_keys && ARRAY[
                'coffee_identity', 'product_identity',
                'participant', 'origin_sample_family'
            ]::TEXT[])
            OR NOT EXISTS (
                SELECT 1
                FROM unnest(NEW.grouping_keys) AS item(grouping_key)
                WHERE item.grouping_key = ANY(
                    NEW.prohibited_cross_split_keys
                )
                  AND item.grouping_key = ANY(ARRAY[
                    'coffee_identity', 'product_identity',
                    'participant', 'origin_sample_family'
                  ]::TEXT[])
            )) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_hybrid_group_ck',
            MESSAGE = 'hybrid split requires source family plus an independent identity group';
    END IF;
    IF NEW.readiness_primary AND (
        (selected_task_type IN (
             'LEXICAL_NORMALIZATION', 'ASSOCIATION_MODEL'
         ) AND NEW.split_strategy NOT IN (
             'SOURCE_FAMILY_HOLDOUT', 'HYBRID_GROUPED_SPLIT'
         ))
        OR (selected_task_type = 'CONTEXT_MODEL'
            AND NEW.split_strategy NOT IN (
                'COFFEE_IDENTITY_HOLDOUT', 'HYBRID_GROUPED_SPLIT'
            ))
        OR selected_task_type IN ('QUESTION_MODEL', 'ADAPTIVE_POLICY')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_primary_task_strategy_ck',
            MESSAGE = 'readiness primary strategy does not match task leakage semantics';
    END IF;
    IF NEW.readiness_primary
       AND selected_task_type = 'CONTEXT_MODEL'
       AND (NOT (NEW.grouping_keys @>
                 ARRAY['coffee_identity']::TEXT[])
            OR NOT (NEW.prohibited_cross_split_keys @>
                    ARRAY['coffee_identity']::TEXT[])) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_context_primary_coffee_group_ck',
            MESSAGE = 'context readiness requires coffee identity as a prohibited cross-split group';
    END IF;
    RETURN NEW;
END;
$enforce_training_split_strategy$;

CREATE TRIGGER training_split_strategy_biu
BEFORE INSERT OR UPDATE ON ml.training_split_candidate
FOR EACH ROW EXECUTE FUNCTION ml.enforce_training_split_strategy();

CREATE TABLE ml.training_split_assignment (
    split_assignment_key TEXT NOT NULL,
    split_candidate_key TEXT NOT NULL,
    task_key TEXT NOT NULL,
    training_example_key TEXT NOT NULL,
    split_name TEXT NOT NULL,
    grouping_values JSONB NOT NULL,
    assignment_basis TEXT NOT NULL,
    assignment_sha256 TEXT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT training_split_assignment_pk PRIMARY KEY (
        split_assignment_key
    ),
    CONSTRAINT training_split_assignment_candidate_example_uq UNIQUE (
        split_candidate_key, training_example_key
    ),
    CONSTRAINT training_split_assignment_candidate_fk FOREIGN KEY (
        split_candidate_key, task_key
    ) REFERENCES ml.training_split_candidate (
        split_candidate_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_split_assignment_example_fk FOREIGN KEY (
        training_example_key, task_key
    ) REFERENCES ml.training_example_candidate (
        training_example_key, task_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_split_assignment_contract_ck CHECK (
        split_assignment_key = lower(btrim(split_assignment_key))
        AND split_assignment_key <> ''
        AND split_name IN ('TRAIN', 'DEV', 'TEST')
        AND jsonb_typeof(grouping_values) = 'object'
        AND grouping_values <> '{}'::JSONB
        AND evidence.round3e_reject_direct_identifiers(grouping_values)
        AND assignment_basis = btrim(assignment_basis)
        AND assignment_basis <> ''
        AND assignment_sha256 ~ '^[0-9a-f]{64}$'
    )
);

CREATE INDEX training_split_assignment_split_name_ix
ON ml.training_split_assignment (split_candidate_key, split_name);

CREATE FUNCTION ml.enforce_training_split_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_training_split_assignment$
DECLARE
    selected_split ml.training_split_candidate%ROWTYPE;
    selected_example ml.training_example_candidate%ROWTYPE;
    selected_partition ml.training_partition_eligibility%ROWTYPE;
    grouping_key TEXT;
    grouping_value TEXT;
    expected_value TEXT;
    expected_assignment_hash TEXT;
BEGIN
    SELECT * INTO selected_split FROM ml.training_split_candidate
    WHERE split_candidate_key = NEW.split_candidate_key
    FOR UPDATE;
    SELECT * INTO selected_example FROM ml.training_example_candidate
    WHERE training_example_key = NEW.training_example_key
    FOR UPDATE;
    SELECT * INTO selected_partition
    FROM ml.training_partition_eligibility
    WHERE partition_eligibility_key =
          selected_example.partition_eligibility_key;

    IF selected_split.lifecycle_status IN ('VALIDATED', 'REJECTED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_assignment_closed_ck',
            MESSAGE = 'assignments cannot change after split validation or rejection';
    END IF;
    IF selected_example.duplicate_disposition = 'EXCLUDED'
       OR selected_example.label_lifecycle NOT IN (
           'TRAINING_ELIGIBLE', 'EVALUATION_ONLY'
       )
       OR selected_example.machine_translated
       OR selected_example.project_translation
       OR selected_example.artificial_variant
       OR (NEW.split_name = 'TRAIN'
           AND NOT selected_example.sampling_eligible) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_assignment_example_eligible_ck',
            MESSAGE = 'ineligible, artificial, translated, or duplicate-excluded examples cannot enter this split';
    END IF;
    IF NOT selected_partition.rights_review_complete
       OR NOT selected_partition.privacy_review_complete
       OR NOT selected_partition.source_file_hash_complete
       OR NOT selected_partition.label_provenance_complete
       OR NOT selected_partition.duplicate_audit_complete
       OR NOT selected_partition.research_use_allowed
       OR NOT selected_partition.model_research_use_allowed THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_assignment_partition_rights_ck',
            MESSAGE = 'every train/dev/test assignment requires reviewed model-research rights, privacy, hashes, provenance, and duplicates';
    END IF;

    FOREACH grouping_key IN ARRAY selected_split.grouping_keys LOOP
        IF NOT (NEW.grouping_values ? grouping_key)
           OR jsonb_typeof(NEW.grouping_values -> grouping_key) <> 'string'
           OR btrim(NEW.grouping_values ->> grouping_key) = '' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_assignment_group_values_ck',
                MESSAGE = 'every declared grouping key requires a non-empty string value';
        END IF;
        expected_value := CASE grouping_key
            WHEN 'source_family' THEN selected_example.source_family_key
            WHEN 'coffee_identity' THEN selected_example.coffee_identity_key
            WHEN 'product_identity' THEN selected_example.product_identity_key
            WHEN 'participant' THEN selected_example.participant_group_key
            WHEN 'roast_batch' THEN selected_example.roast_batch_key
            WHEN 'preparation_condition'
                THEN selected_example.preparation_condition_key
            WHEN 'origin_sample_family'
                THEN selected_example.origin_sample_family_key
            WHEN 'duplicate_group' THEN coalesce(
                selected_example.duplicate_group_key,
                'unique.' || selected_example.training_example_key
            ) END;
        IF expected_value IS NULL
           OR NEW.grouping_values ->> grouping_key <> expected_value THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_assignment_group_provenance_ck',
                MESSAGE = 'grouping values must match example provenance';
        END IF;
    END LOOP;

    IF EXISTS (
        SELECT 1 FROM jsonb_object_keys(NEW.grouping_values) AS item(key)
        WHERE NOT (item.key = ANY(selected_split.grouping_keys))
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_assignment_extra_group_key_ck',
            MESSAGE = 'grouping values cannot contain undeclared keys';
    END IF;

    FOREACH grouping_key IN ARRAY selected_split.prohibited_cross_split_keys LOOP
        grouping_value := NEW.grouping_values ->> grouping_key;
        IF EXISTS (
            SELECT 1 FROM ml.training_split_assignment AS existing
            WHERE existing.split_candidate_key = NEW.split_candidate_key
              AND existing.split_assignment_key <> NEW.split_assignment_key
              AND existing.split_name <> NEW.split_name
              AND existing.grouping_values ->> grouping_key = grouping_value
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_assignment_group_leak_ck',
                MESSAGE = 'a prohibited group cannot cross train/dev/test boundaries';
        END IF;
    END LOOP;
    expected_assignment_hash := audit.round3i_utf8_sha256(
        jsonb_build_object(
            'split_assignment_key', NEW.split_assignment_key,
            'split_candidate_key', NEW.split_candidate_key,
            'task_key', NEW.task_key,
            'training_example_key', NEW.training_example_key,
            'split_name', NEW.split_name,
            'grouping_values', NEW.grouping_values,
            'assignment_basis', NEW.assignment_basis
        )::TEXT
    );
    IF NEW.assignment_sha256 <> expected_assignment_hash THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_assignment_hash_ck',
            MESSAGE = 'assignment hash must equal the canonical assignment payload';
    END IF;
    RETURN NEW;
END;
$enforce_training_split_assignment$;

CREATE TRIGGER training_split_assignment_biu
BEFORE INSERT OR UPDATE ON ml.training_split_assignment
FOR EACH ROW EXECUTE FUNCTION ml.enforce_training_split_assignment();

CREATE TABLE audit.training_readiness_assertion (
    assertion_key TEXT NOT NULL,
    task_key TEXT,
    assertion_type TEXT NOT NULL,
    assertion_version INTEGER NOT NULL,
    passed BOOLEAN NOT NULL,
    observed_count NUMERIC,
    observed_state TEXT NOT NULL,
    evidence_path TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    asserted_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT training_readiness_assertion_pk PRIMARY KEY (assertion_key),
    CONSTRAINT training_readiness_assertion_task_fk FOREIGN KEY (task_key)
        REFERENCES ml.training_task_candidate (task_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_readiness_assertion_contract_ck CHECK (
        assertion_key = lower(btrim(assertion_key))
        AND assertion_key <> ''
        AND assertion_type IN (
            'DUPLICATE_DETECTION_COMPLETE',
            'SOURCE_LOCAL_SEMANTICS_PRESERVED',
            'NO_FALSE_POOLED_SCALE',
            'TRAINING_CORPUS_MANIFEST_REPRODUCIBLE',
            'SPLIT_MANIFEST_REPRODUCIBLE',
            'V0_1_0_IMMUTABLE',
            'REMOTE_FRONTEND_CI', 'REMOTE_POSTGRES_CI'
        )
        AND assertion_version > 0
        AND observed_state = btrim(observed_state)
        AND observed_state <> ''
        AND evidence_path = btrim(evidence_path) AND evidence_path <> ''
        AND evidence_sha256 ~ '^[0-9a-f]{64}$'
        AND (assertion_type <> 'V0_1_0_IMMUTABLE'
             OR (passed AND observed_count = 0))
    )
);

CREATE UNIQUE INDEX training_readiness_assertion_version_uq
ON audit.training_readiness_assertion (
    coalesce(task_key, '__global__'), assertion_type, assertion_version
);

CREATE FUNCTION audit.latest_training_readiness_assertion(
    selected_assertion_type TEXT,
    selected_task_key TEXT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $latest_training_readiness_assertion$
SELECT coalesce((
    SELECT assertion.passed
    FROM audit.training_readiness_assertion AS assertion
    WHERE assertion.assertion_type = selected_assertion_type
      AND assertion.task_key IS NOT DISTINCT FROM selected_task_key
    ORDER BY assertion.assertion_version DESC, assertion.asserted_at DESC
    LIMIT 1
), FALSE)
$latest_training_readiness_assertion$;

CREATE TABLE audit.round3j_threshold_revision (
    threshold_revision_key TEXT NOT NULL,
    checkpoint_key TEXT NOT NULL,
    acquisition_batch_key TEXT,
    metric_key TEXT NOT NULL,
    original_threshold TEXT NOT NULL,
    revised_threshold TEXT NOT NULL,
    change_direction TEXT NOT NULL,
    invalid_metric_evidence TEXT NOT NULL,
    methodology_commit_sha TEXT NOT NULL,
    decision_record_path TEXT NOT NULL,
    decision_record_sha256 TEXT NOT NULL,
    approval_status TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT round3j_threshold_revision_pk PRIMARY KEY (
        threshold_revision_key
    ),
    CONSTRAINT round3j_threshold_revision_checkpoint_fk FOREIGN KEY (
        checkpoint_key
    ) REFERENCES audit.round3j_checkpoint (checkpoint_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3j_threshold_revision_batch_fk FOREIGN KEY (
        acquisition_batch_key
    ) REFERENCES audit.round3j_acquisition_batch (batch_key)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3j_threshold_revision_contract_ck CHECK (
        threshold_revision_key = lower(btrim(threshold_revision_key))
        AND threshold_revision_key <> ''
        AND metric_key = lower(btrim(metric_key)) AND metric_key <> ''
        AND original_threshold = btrim(original_threshold)
        AND original_threshold <> ''
        AND revised_threshold = btrim(revised_threshold)
        AND revised_threshold <> ''
        AND original_threshold <> revised_threshold
        AND change_direction IN ('RAISED', 'LOWERED', 'REDEFINED')
        AND invalid_metric_evidence = btrim(invalid_metric_evidence)
        AND invalid_metric_evidence <> ''
        AND methodology_commit_sha ~ '^[0-9a-f]{40}$'
        AND decision_record_path = btrim(decision_record_path)
        AND decision_record_path <> ''
        AND decision_record_sha256 ~ '^[0-9a-f]{64}$'
        AND approval_status IN (
            'EVIDENCE_BACKED_METHODOLOGY_APPROVAL',
            'EXPLICIT_GOVERNANCE_APPROVAL'
        )
        AND (change_direction <> 'LOWERED'
             OR approval_status = 'EXPLICIT_GOVERNANCE_APPROVAL')
    )
);

COMMENT ON TABLE audit.round3j_threshold_revision IS
    'Append-only exceptional record; difficult thresholds cannot be reduced without invalid-metric evidence and explicit governance approval.';

CREATE FUNCTION audit.prevent_round3j_append_only_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3j_append_only_mutation$
BEGIN
    RAISE EXCEPTION USING ERRCODE = '23514',
        CONSTRAINT = 'round3j_append_only_record_immutable_ck',
        MESSAGE = 'Round 3J audit decisions are append-only';
END;
$prevent_round3j_append_only_mutation$;

CREATE TRIGGER round3j_threshold_revision_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3j_threshold_revision
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3j_append_only_mutation();

CREATE TRIGGER training_readiness_assertion_immutable_bud
BEFORE UPDATE OR DELETE ON audit.training_readiness_assertion
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3j_append_only_mutation();

CREATE TABLE audit.training_corpus_release (
    training_corpus_version TEXT NOT NULL,
    database_release_version TEXT NOT NULL,
    candidate_repository_sha TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    payload_frozen BOOLEAN NOT NULL,
    manifest_path TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    artifact_manifest JSONB NOT NULL,
    eligible_task_keys TEXT[] NOT NULL,
    known_exclusions TEXT[] NOT NULL,
    known_leakage_risks TEXT[] NOT NULL,
    training_corpus_reproducible BOOLEAN NOT NULL,
    clean_rebuild_count INTEGER NOT NULL,
    source_hash_pass BOOLEAN NOT NULL,
    split_manifest_reproducible BOOLEAN NOT NULL,
    remote_frontend_ci_pass BOOLEAN NOT NULL,
    remote_postgres_ci_pass BOOLEAN NOT NULL,
    round3_exit_gate_pass BOOLEAN NOT NULL,
    promotion_authorized BOOLEAN NOT NULL,
    new_database_release_tag TEXT,
    force_push_used BOOLEAN NOT NULL DEFAULT FALSE,
    described_as_ground_truth BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payload_frozen_at TIMESTAMPTZ,
    frozen_at TIMESTAMPTZ,
    limitation TEXT NOT NULL,
    CONSTRAINT training_corpus_release_pk PRIMARY KEY (
        training_corpus_version
    ),
    CONSTRAINT training_corpus_release_database_fk FOREIGN KEY (
        database_release_version
    ) REFERENCES audit.research_database_release (freeze_version)
      ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT training_corpus_release_contract_ck CHECK (
        training_corpus_version =
            'coffee-sensory-training-corpus-v0.1.0'
        AND database_release_version =
            'coffee-sensory-research-db-v0.2.0'
        AND candidate_repository_sha ~ '^[0-9a-f]{40}$'
        AND lifecycle_status IN ('DRAFT', 'FREEZE_CANDIDATE', 'FROZEN')
        AND manifest_path = btrim(manifest_path) AND manifest_path <> ''
        AND manifest_sha256 ~ '^[0-9a-f]{64}$'
        AND corpus.language_source_manifest_is_complete(artifact_manifest)
        AND cardinality(eligible_task_keys) >= 1
        AND array_position(eligible_task_keys, NULL) IS NULL
        AND cardinality(known_exclusions) >= 1
        AND array_position(known_exclusions, NULL) IS NULL
        AND cardinality(known_leakage_risks) >= 1
        AND array_position(known_leakage_risks, NULL) IS NULL
        AND clean_rebuild_count BETWEEN 0 AND 2
        AND NOT force_push_used
        AND NOT described_as_ground_truth
        AND limitation = btrim(limitation) AND limitation <> ''
    ),
    CONSTRAINT training_corpus_release_freeze_ck CHECK (
        payload_frozen = (payload_frozen_at IS NOT NULL)
        AND (NOT payload_frozen OR lifecycle_status IN (
            'FREEZE_CANDIDATE', 'FROZEN'
        ))
        AND (NOT payload_frozen OR (
            training_corpus_reproducible
            AND clean_rebuild_count = 2
            AND source_hash_pass
            AND split_manifest_reproducible
        ))
        AND (NOT round3_exit_gate_pass OR payload_frozen)
        AND (NOT promotion_authorized OR (
            round3_exit_gate_pass AND training_corpus_reproducible
            AND clean_rebuild_count = 2 AND source_hash_pass
            AND split_manifest_reproducible
            AND remote_frontend_ci_pass AND remote_postgres_ci_pass
        ))
        AND ((lifecycle_status = 'FROZEN') = (frozen_at IS NOT NULL))
        AND (lifecycle_status <> 'FROZEN' OR promotion_authorized)
        AND (new_database_release_tag IS NULL OR (
            promotion_authorized
            AND new_database_release_tag = database_release_version
        ))
    )
);

COMMENT ON TABLE audit.training_corpus_release IS
    'Conditional manifest metadata for a non-ground-truth corpus freeze derived from a later immutable database release.';

CREATE FUNCTION ml.protect_frozen_sampling_policy()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_sampling_policy$
DECLARE
    checked_key TEXT;
    raw_metric_count INTEGER;
    candidate_metric_count INTEGER;
    old_task TEXT;
    new_task TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN old_task := OLD.task_key; END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN new_task := NEW.task_key; END IF;
    IF old_task IS NOT NULL AND new_task IS NOT NULL
       AND old_task <> new_task THEN
        PERFORM ml.lock_round3j_task_corpus(least(old_task, new_task));
        PERFORM ml.lock_round3j_task_corpus(greatest(old_task, new_task));
    ELSE
        PERFORM ml.lock_round3j_task_corpus(
            coalesce(old_task, new_task)
        );
    END IF;
    IF TG_OP IN ('UPDATE', 'DELETE')
       AND OLD.lifecycle_status = 'FROZEN' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_sampling_policy_frozen_ck',
            MESSAGE = 'a frozen sampling policy is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF NEW.lifecycle_status = 'FROZEN' THEN
        checked_key := NEW.sampling_policy_key;
        IF NOT EXISTS (
            SELECT 1 FROM ml.training_task_candidate
            WHERE task_key = NEW.task_key
              AND lifecycle_status = 'VALIDATED'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_sampling_policy_task_validated_ck',
                MESSAGE = 'freezing a sampling policy requires a validated task contract';
        END IF;
        IF EXISTS (
            WITH expected AS (
                SELECT example.source_family_key,
                       count(*)::INTEGER AS original_count,
                       count(*) FILTER (
                           WHERE example.duplicate_disposition = 'EXCLUDED'
                       )::INTEGER AS duplicate_excluded_count,
                       count(*) FILTER (
                           WHERE example.duplicate_disposition <> 'EXCLUDED'
                             AND (NOT partition.rights_review_complete
                               OR NOT partition.privacy_review_complete
                               OR NOT partition.source_file_hash_complete
                               OR NOT partition.label_provenance_complete
                               OR NOT partition.duplicate_audit_complete
                               OR NOT partition.research_use_allowed
                               OR NOT partition.model_research_use_allowed)
                       )::INTEGER AS rights_excluded_count,
                       count(*) FILTER (
                           WHERE example.duplicate_disposition <> 'EXCLUDED'
                             AND partition.rights_review_complete
                             AND partition.privacy_review_complete
                             AND partition.source_file_hash_complete
                             AND partition.label_provenance_complete
                             AND partition.duplicate_audit_complete
                             AND partition.research_use_allowed
                             AND partition.model_research_use_allowed
                             AND example.label_lifecycle = 'EVALUATION_ONLY'
                       )::INTEGER AS evaluation_reserved_count
                FROM ml.training_example_candidate AS example
                JOIN ml.training_partition_eligibility AS partition
                  ON partition.partition_eligibility_key =
                     example.partition_eligibility_key
                 AND partition.task_key = example.task_key
                WHERE example.task_key = NEW.task_key
                  AND example.label_lifecycle <> 'RAW'
                GROUP BY example.source_family_key
            )
            SELECT 1
            FROM expected
            FULL JOIN (
                SELECT * FROM ml.training_sampling_allocation
                WHERE sampling_policy_key = NEW.sampling_policy_key
            ) AS allocation
              ON allocation.source_family_key = expected.source_family_key
            WHERE coalesce(allocation.original_count, -1) <>
                    coalesce(expected.original_count, -1)
               OR coalesce(allocation.duplicate_excluded_count, -1) <>
                    coalesce(expected.duplicate_excluded_count, -1)
               OR coalesce(allocation.rights_excluded_count, -1) <>
                    coalesce(expected.rights_excluded_count, -1)
               OR coalesce(allocation.evaluation_reserved_count, -1) <>
                    coalesce(expected.evaluation_reserved_count, -1)
               OR allocation.task_key IS DISTINCT FROM NEW.task_key
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_sampling_policy_full_corpus_ck',
                MESSAGE = 'allocations must cover every non-raw example and derive original, duplicate, rights, and evaluation counts';
        END IF;
        IF EXISTS (
            SELECT 1
            FROM ml.training_partition_eligibility AS partition
            LEFT JOIN ml.training_example_candidate AS example
              ON example.partition_eligibility_key =
                 partition.partition_eligibility_key
             AND example.task_key = partition.task_key
            WHERE partition.task_key = NEW.task_key
              AND partition.eligibility_class LIKE
                  'ELIGIBLE_FOR_%_TRAINING'
            GROUP BY partition.partition_eligibility_key,
                     partition.effective_unit_count
            HAVING partition.effective_unit_count <>
                   count(DISTINCT example.effective_unit_key)
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_partition_effective_count_recomputed_ck',
                MESSAGE = 'training-eligible partition effective counts must equal distinct governed example units';
        END IF;
        SELECT count(*) FILTER (WHERE corpus_scope = 'RAW_CORPUS'),
               count(*) FILTER (WHERE corpus_scope = 'TRAINING_CANDIDATE')
        INTO raw_metric_count, candidate_metric_count
        FROM audit.training_source_concentration
        WHERE sampling_policy_key = checked_key;
        IF NOT EXISTS (
            SELECT 1 FROM ml.training_sampling_allocation
            WHERE sampling_policy_key = checked_key
        ) OR raw_metric_count <> 1 OR candidate_metric_count <> 1 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_sampling_policy_freeze_complete_ck',
                MESSAGE = 'freezing requires allocations and recomputed raw/candidate concentration metrics';
        END IF;
    END IF;
    RETURN NEW;
END;
$protect_frozen_sampling_policy$;

CREATE TRIGGER training_sampling_policy_freeze_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.training_sampling_policy
FOR EACH ROW EXECUTE FUNCTION ml.protect_frozen_sampling_policy();

CREATE FUNCTION ml.protect_frozen_sampling_allocation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_frozen_sampling_allocation$
DECLARE
    old_policy TEXT;
    new_policy TEXT;
    old_task TEXT;
    new_task TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        old_policy := OLD.sampling_policy_key;
        old_task := OLD.task_key;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        new_policy := NEW.sampling_policy_key;
        new_task := NEW.task_key;
    END IF;
    IF old_task IS NOT NULL AND new_task IS NOT NULL
       AND old_task <> new_task THEN
        PERFORM ml.lock_round3j_task_corpus(least(old_task, new_task));
        PERFORM ml.lock_round3j_task_corpus(greatest(old_task, new_task));
    ELSE
        PERFORM ml.lock_round3j_task_corpus(
            coalesce(old_task, new_task)
        );
    END IF;
    IF EXISTS (
        SELECT 1 FROM ml.training_sampling_policy
        WHERE sampling_policy_key IN (
            coalesce(old_policy, '__none__'),
            coalesce(new_policy, '__none__')
        )
          AND lifecycle_status = 'FROZEN'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_sampling_allocation_frozen_ck',
            MESSAGE = 'allocations of a frozen sampling policy are immutable';
    END IF;
    IF TG_TABLE_SCHEMA = 'ml'
       AND TG_TABLE_NAME = 'training_sampling_allocation'
       AND EXISTS (
           SELECT 1 FROM audit.training_source_concentration
           WHERE sampling_policy_key IN (
               coalesce(old_policy, '__none__'),
               coalesce(new_policy, '__none__')
           )
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_sampling_allocation_metrics_bound_ck',
            MESSAGE = 'sampling allocations cannot change after concentration metrics are bound';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_frozen_sampling_allocation$;

CREATE TRIGGER training_sampling_allocation_freeze_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.training_sampling_allocation
FOR EACH ROW EXECUTE FUNCTION ml.protect_frozen_sampling_allocation();

CREATE TRIGGER training_source_concentration_freeze_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.training_source_concentration
FOR EACH ROW EXECUTE FUNCTION ml.protect_frozen_sampling_allocation();

CREATE FUNCTION ml.validate_and_protect_training_split()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_and_protect_training_split$
DECLARE
    observed_train INTEGER;
    observed_dev INTEGER;
    observed_test INTEGER;
    observed_held_out_families INTEGER;
    selected_task_type TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE')
       AND OLD.lifecycle_status IN ('VALIDATED', 'REJECTED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_candidate_terminal_ck',
            MESSAGE = 'validated or rejected split candidates are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    IF TG_OP = 'UPDATE' AND EXISTS (
        SELECT 1 FROM ml.training_split_assignment
        WHERE split_candidate_key = OLD.split_candidate_key
    ) AND (
        NEW.split_candidate_key IS DISTINCT FROM OLD.split_candidate_key
        OR NEW.task_key IS DISTINCT FROM OLD.task_key
        OR NEW.sampling_policy_key IS DISTINCT FROM OLD.sampling_policy_key
        OR NEW.split_strategy IS DISTINCT FROM OLD.split_strategy
        OR NEW.grouping_keys IS DISTINCT FROM OLD.grouping_keys
        OR NEW.prohibited_cross_split_keys IS DISTINCT FROM
           OLD.prohibited_cross_split_keys
        OR NEW.deterministic_seed IS DISTINCT FROM OLD.deterministic_seed
        OR NEW.readiness_primary IS DISTINCT FROM OLD.readiness_primary
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_definition_assigned_immutable_ck',
            MESSAGE = 'split policy, strategy, seed, and grouping definition are immutable after assignment begins';
    END IF;
    IF NEW.lifecycle_status = 'VALIDATED' THEN
        SELECT task_type INTO selected_task_type
        FROM ml.training_task_candidate
        WHERE task_key = NEW.task_key;
        IF NEW.readiness_primary AND NOT EXISTS (
            SELECT 1 FROM ml.training_sampling_policy
            WHERE sampling_policy_key = NEW.sampling_policy_key
              AND task_key = NEW.task_key
              AND lifecycle_status = 'FROZEN'
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_primary_policy_frozen_ck',
                MESSAGE = 'a readiness-primary validated split requires its exact frozen sampling policy';
        END IF;
        SELECT count(*) FILTER (WHERE split_name = 'TRAIN'),
               count(*) FILTER (WHERE split_name = 'DEV'),
               count(*) FILTER (WHERE split_name = 'TEST')
        INTO observed_train, observed_dev, observed_test
        FROM ml.training_split_assignment
        WHERE split_candidate_key = NEW.split_candidate_key;
        IF NEW.train_count <> observed_train
           OR NEW.dev_count <> observed_dev
           OR NEW.test_count <> observed_test THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_candidate_counts_ck',
                MESSAGE = 'validated split counts must equal its assignments';
        END IF;
        SELECT count(DISTINCT held_out.source_family_key)::INTEGER
        INTO observed_held_out_families
        FROM (
            SELECT example.source_family_key
            FROM ml.training_split_assignment AS assignment
            JOIN ml.training_example_candidate AS example
              ON example.training_example_key =
                 assignment.training_example_key
            JOIN ml.training_partition_eligibility AS partition
              ON partition.partition_eligibility_key =
                 example.partition_eligibility_key
             AND partition.task_key = example.task_key
            WHERE assignment.split_candidate_key = NEW.split_candidate_key
              AND assignment.split_name IN ('DEV', 'TEST')
              AND example.label_lifecycle = 'TRAINING_ELIGIBLE'
              AND example.sampling_eligible
              AND partition.counts_as_independent
              AND partition.eligibility_class = CASE selected_task_type
                  WHEN 'LEXICAL_NORMALIZATION'
                    THEN 'ELIGIBLE_FOR_LEXICAL_TRAINING'
                  WHEN 'ASSOCIATION_MODEL'
                    THEN 'ELIGIBLE_FOR_ASSOCIATION_TRAINING'
                  WHEN 'CONTEXT_MODEL'
                    THEN 'ELIGIBLE_FOR_CONTEXT_TRAINING'
                  ELSE '__PROHIBITED__' END
              AND NOT EXISTS (
                  SELECT 1
                  FROM ml.training_split_assignment AS train_assignment
                  JOIN ml.training_example_candidate AS train_example
                    ON train_example.training_example_key =
                       train_assignment.training_example_key
                  WHERE train_assignment.split_candidate_key =
                        NEW.split_candidate_key
                    AND train_assignment.split_name = 'TRAIN'
                    AND train_example.source_family_key =
                        example.source_family_key
              )
        ) AS held_out;
        IF NEW.held_out_source_family_count <>
           coalesce(observed_held_out_families, 0) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_candidate_heldout_count_ck',
                MESSAGE = 'held-out source-family count must equal the assignments';
        END IF;
        IF NEW.split_strategy IN (
            'SOURCE_FAMILY_HOLDOUT', 'HYBRID_GROUPED_SPLIT'
        ) AND coalesce(observed_held_out_families, 0) = 0 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_source_family_holdout_nonzero_ck',
                MESSAGE = 'source-family and hybrid holdouts require at least one fully held-out family';
        END IF;
        IF NEW.readiness_primary AND NEW.split_strategy IN (
            'SOURCE_FAMILY_HOLDOUT', 'COFFEE_IDENTITY_HOLDOUT',
            'HYBRID_GROUPED_SPLIT'
        ) AND EXISTS (
            WITH assigned AS (
                SELECT example.source_family_key,
                       count(*) FILTER (
                           WHERE example.label_lifecycle =
                                 'TRAINING_ELIGIBLE'
                       )::INTEGER AS retained_count,
                       count(*) FILTER (
                           WHERE example.label_lifecycle =
                                 'EVALUATION_ONLY'
                       )::INTEGER AS evaluation_reserved_count
                FROM ml.training_split_assignment AS assignment
                JOIN ml.training_example_candidate AS example
                  ON example.training_example_key =
                     assignment.training_example_key
                WHERE assignment.split_candidate_key =
                      NEW.split_candidate_key
                GROUP BY example.source_family_key
            )
            SELECT 1
            FROM (
                SELECT * FROM ml.training_sampling_allocation
                WHERE sampling_policy_key = NEW.sampling_policy_key
            ) AS allocation
            FULL JOIN assigned
              ON assigned.source_family_key = allocation.source_family_key
            WHERE coalesce(allocation.retained_count, 0) <>
                     coalesce(assigned.retained_count, 0)
               OR coalesce(allocation.evaluation_reserved_count, 0) <>
                     coalesce(assigned.evaluation_reserved_count, 0)
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_candidate_sampling_count_ck',
                MESSAGE = 'primary split assignments must equal retained plus evaluation-reserved sampling allocations';
        END IF;
        IF EXISTS (
            SELECT 1
            FROM ml.training_split_assignment AS left_assignment
            JOIN ml.training_split_assignment AS right_assignment
              ON right_assignment.split_candidate_key =
                 left_assignment.split_candidate_key
             AND right_assignment.split_assignment_key >
                 left_assignment.split_assignment_key
             AND right_assignment.split_name <>
                 left_assignment.split_name
            CROSS JOIN LATERAL unnest(
                NEW.prohibited_cross_split_keys
            ) AS prohibited(grouping_key)
            WHERE left_assignment.split_candidate_key =
                  NEW.split_candidate_key
              AND left_assignment.grouping_values ->>
                  prohibited.grouping_key =
                  right_assignment.grouping_values ->>
                  prohibited.grouping_key
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_validation_group_leak_ck',
                MESSAGE = 'validated split contains a prohibited group across boundaries';
        END IF;
        IF NEW.readiness_primary
           AND selected_task_type = 'LEXICAL_NORMALIZATION'
           AND EXISTS (
               SELECT 1
               FROM ml.training_split_assignment AS left_assignment
               JOIN ml.training_example_candidate AS left_example
                 ON left_example.training_example_key =
                    left_assignment.training_example_key
               JOIN ml.training_split_assignment AS right_assignment
                 ON right_assignment.split_candidate_key =
                    left_assignment.split_candidate_key
                AND right_assignment.split_assignment_key >
                    left_assignment.split_assignment_key
                AND right_assignment.split_name <>
                    left_assignment.split_name
               JOIN ml.training_example_candidate AS right_example
                 ON right_example.training_example_key =
                    right_assignment.training_example_key
                AND right_example.product_identity_key =
                    left_example.product_identity_key
               WHERE left_assignment.split_candidate_key =
                     NEW.split_candidate_key
                 AND left_example.product_identity_key IS NOT NULL
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_lexical_product_leak_ck',
                MESSAGE = 'a lexical readiness split cannot place one source product across boundaries';
        END IF;
        IF NEW.split_strategy = 'ZH_HANS_STRATIFIED_TEST'
           AND NOT EXISTS (
               SELECT 1
               FROM ml.training_split_assignment AS assignment
               JOIN ml.training_example_candidate AS example
                 ON example.training_example_key =
                    assignment.training_example_key
               WHERE assignment.split_candidate_key =
                     NEW.split_candidate_key
                 AND assignment.split_name = 'TEST'
                 AND example.language_code = 'zh-Hans'
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_zh_hans_stratum_ck',
                MESSAGE = 'zh-Hans stratified test must contain source-authored zh-Hans examples';
        END IF;
        IF NEW.split_strategy = 'AMBIGUOUS_EXPRESSION_TEST'
           AND NOT EXISTS (
               SELECT 1
               FROM ml.training_split_assignment AS assignment
               JOIN ml.training_example_candidate AS example
                 ON example.training_example_key =
                    assignment.training_example_key
               WHERE assignment.split_candidate_key =
                     NEW.split_candidate_key
                 AND assignment.split_name IN ('DEV', 'TEST')
                 AND example.lexical_outcome = 'AMBIGUOUS'
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_ambiguous_stratum_ck',
                MESSAGE = 'ambiguous-expression split must contain ambiguous held-out examples';
        END IF;
        IF NEW.split_strategy = 'ABSTENTION_TEST'
           AND NOT EXISTS (
               SELECT 1
               FROM ml.training_split_assignment AS assignment
               JOIN ml.training_example_candidate AS example
                 ON example.training_example_key =
                    assignment.training_example_key
               WHERE assignment.split_candidate_key =
                     NEW.split_candidate_key
                 AND assignment.split_name IN ('DEV', 'TEST')
                 AND example.lexical_outcome IN ('UNRESOLVED', 'ABSTAIN')
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_split_abstention_stratum_ck',
                MESSAGE = 'abstention split must contain unresolved or abstain held-out examples';
        END IF;
    END IF;
    RETURN NEW;
END;
$validate_and_protect_training_split$;

CREATE TRIGGER training_split_candidate_terminal_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.training_split_candidate
FOR EACH ROW EXECUTE FUNCTION ml.validate_and_protect_training_split();

CREATE FUNCTION ml.protect_validated_training_assignment()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_validated_training_assignment$
DECLARE old_split TEXT; new_split TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        old_split := OLD.split_candidate_key;
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        new_split := NEW.split_candidate_key;
    END IF;
    IF EXISTS (
        SELECT 1 FROM ml.training_split_candidate
        WHERE split_candidate_key IN (
            coalesce(old_split, '__none__'),
            coalesce(new_split, '__none__')
        )
          AND lifecycle_status IN ('VALIDATED', 'REJECTED')
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_split_assignment_validated_ck',
            MESSAGE = 'assignments of a validated split are immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_validated_training_assignment$;

CREATE TRIGGER training_split_assignment_validated_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.training_split_assignment
FOR EACH ROW EXECUTE FUNCTION ml.protect_validated_training_assignment();

CREATE FUNCTION ml.protect_assigned_training_example()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_assigned_training_example$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM ml.training_split_assignment AS assignment
        WHERE assignment.training_example_key = OLD.training_example_key
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_example_assigned_immutable_ck',
            MESSAGE = 'an assigned example is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$protect_assigned_training_example$;

CREATE TRIGGER training_example_validated_split_bud
BEFORE UPDATE OR DELETE ON ml.training_example_candidate
FOR EACH ROW EXECUTE FUNCTION ml.protect_assigned_training_example();

CREATE FUNCTION audit.run_training_experiment_readiness_gate()
RETURNS TABLE (
    task_type TEXT,
    readiness_key TEXT,
    minimum_required TEXT,
    preferred_required TEXT,
    observed TEXT,
    hard_gate BOOLEAN,
    passed BOOLEAN,
    evidence_path TEXT,
    limitation TEXT
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_training_experiment_readiness_gate$
WITH task_lookup AS (
    SELECT
        max(task_key) FILTER (
            WHERE task_type = 'LEXICAL_NORMALIZATION'
        ) AS lexical_task_key,
        max(task_key) FILTER (
            WHERE task_type = 'ASSOCIATION_MODEL'
        ) AS association_task_key,
        max(task_key) FILTER (
            WHERE task_type = 'CONTEXT_MODEL'
        ) AS context_task_key,
        max(task_key) FILTER (
            WHERE task_type = 'QUESTION_MODEL'
        ) AS question_task_key,
        max(task_key) FILTER (
            WHERE task_type = 'ADAPTIVE_POLICY'
        ) AS adaptive_task_key
    FROM ml.training_task_candidate
), primary_split AS (
    SELECT split.task_key, split.split_candidate_key,
           split.sampling_policy_key, split.split_strategy,
           split.held_out_source_family_count
    FROM ml.training_split_candidate AS split
    JOIN ml.training_sampling_policy AS policy
      ON policy.sampling_policy_key = split.sampling_policy_key
     AND policy.task_key = split.task_key
    JOIN ml.training_task_candidate AS task
      ON task.task_key = split.task_key
    WHERE split.readiness_primary
      AND split.lifecycle_status = 'VALIDATED'
      AND split.split_feasible
      AND policy.lifecycle_status = 'FROZEN'
      AND task.lifecycle_status = 'VALIDATED'
), eligible AS (
    SELECT example.*, task.task_type,
           partition.counts_as_independent,
           partition.source_local_semantics_preserved
    FROM ml.training_example_candidate AS example
    JOIN ml.training_split_assignment AS assignment
      ON assignment.training_example_key = example.training_example_key
     AND assignment.task_key = example.task_key
    JOIN primary_split
      ON primary_split.split_candidate_key =
         assignment.split_candidate_key
     AND primary_split.task_key = assignment.task_key
    JOIN ml.training_task_candidate AS task
      ON task.task_key = example.task_key
    JOIN ml.training_partition_eligibility AS partition
      ON partition.partition_eligibility_key =
         example.partition_eligibility_key
     AND partition.task_key = example.task_key
    WHERE example.label_lifecycle = 'TRAINING_ELIGIBLE'
      AND example.sampling_eligible
), lexical AS (
    SELECT
        count(DISTINCT normalized_expression)::INTEGER AS eligible_expression_count,
        count(DISTINCT source_family_key)::INTEGER AS source_family_count,
        count(DISTINCT normalized_expression) FILTER (
            WHERE language_code = 'zh-Hans'
        )::INTEGER AS zh_hans_count,
        count(training_example_key)::INTEGER AS eligible_row_count,
        count(*) FILTER (
            WHERE ml.training_label_provenance_is_complete(
                label_provenance
            )
        )::INTEGER AS provenance_complete_count,
        (SELECT count(*)::INTEGER
         FROM ml.training_example_candidate AS evaluation
         WHERE evaluation.task_key = task_lookup.lexical_task_key
           AND evaluation.lexical_outcome = 'AMBIGUOUS'
           AND evaluation.label_lifecycle = 'EVALUATION_ONLY'
           AND EXISTS (
              SELECT 1
              FROM ml.training_split_assignment AS assignment
              JOIN primary_split AS split
                ON split.split_candidate_key =
                   assignment.split_candidate_key
              WHERE assignment.training_example_key =
                    evaluation.training_example_key
                AND assignment.split_name IN ('DEV', 'TEST')
                AND split.task_key = evaluation.task_key
           )) AS ambiguous_evaluation_count,
        (SELECT count(*)::INTEGER
         FROM ml.training_example_candidate AS evaluation
         WHERE evaluation.task_key = task_lookup.lexical_task_key
           AND evaluation.lexical_outcome IN ('UNRESOLVED', 'ABSTAIN')
           AND evaluation.label_lifecycle = 'EVALUATION_ONLY'
           AND EXISTS (
              SELECT 1
              FROM ml.training_split_assignment AS assignment
              JOIN primary_split AS split
                ON split.split_candidate_key =
                   assignment.split_candidate_key
              WHERE assignment.training_example_key =
                    evaluation.training_example_key
                AND assignment.split_name IN ('DEV', 'TEST')
                AND split.task_key = evaluation.task_key
           )) AS unresolved_evaluation_count
    FROM task_lookup
    LEFT JOIN eligible
      ON eligible.task_key = task_lookup.lexical_task_key
    GROUP BY task_lookup.lexical_task_key
), association AS (
    SELECT
        count(DISTINCT concat_ws(
            '|', source_family_key, effective_unit_key
        ))::INTEGER AS eligible_example_count,
        count(DISTINCT source_family_key) FILTER (
            WHERE counts_as_independent
        )::INTEGER AS independent_source_family_count,
        count(*) FILTER (
            WHERE evidence_direction = 'SUPPORTS'
        )::INTEGER AS supporting_count,
        count(*) FILTER (
            WHERE evidence_direction IN ('CHALLENGES', 'MIXED')
        )::INTEGER AS challenging_or_mixed_count,
        count(*) FILTER (
            WHERE training_example_key IS NOT NULL
              AND (measurement_method IS NULL
               OR btrim(measurement_method) = ''
               OR measurement_semantics IS NULL
               OR btrim(measurement_semantics) = ''
               OR NOT source_local_semantics_preserved)
        )::INTEGER AS semantics_failure_count,
        count(*) FILTER (
            WHERE absence_derived_negative
        )::INTEGER AS absence_negative_count
    FROM task_lookup
    LEFT JOIN eligible
      ON eligible.task_key = task_lookup.association_task_key
    GROUP BY task_lookup.association_task_key
), context_stats AS (
    SELECT
        count(DISTINCT effective_unit_key)::INTEGER AS effective_sample_count,
        count(DISTINCT source_family_key) FILTER (
            WHERE counts_as_independent
        )::INTEGER AS independent_source_family_count,
        count(DISTINCT concat_ws(
            '|', source_family_key, coffee_identity_key,
            preparation_condition_key, roast_batch_key
        )) FILTER (
            WHERE training_example_key IS NOT NULL
        )::INTEGER AS observed_preparation_roast_cell_count,
        count(DISTINCT concat_ws(
            '|', source_family_key, coffee_identity_key
        )) FILTER (
            WHERE training_example_key IS NOT NULL
        )::INTEGER AS coffee_or_sample_group_count,
        count(*) FILTER (
            WHERE training_example_key IS NOT NULL
              AND (measurement_method IS NULL
               OR btrim(measurement_method) = ''
               OR measurement_semantics IS NULL
               OR btrim(measurement_semantics) = ''
               OR source_local_outcome = '{}'::JSONB
               OR NOT source_local_semantics_preserved)
        )::INTEGER AS semantics_failure_count,
        count(*) FILTER (WHERE false_pooled_scale)::INTEGER
            AS false_pooled_scale_count
    FROM task_lookup
    LEFT JOIN eligible
      ON eligible.task_key = task_lookup.context_task_key
    GROUP BY task_lookup.context_task_key
), split_feasibility AS (
    SELECT task.task_key,
           count(split.split_candidate_key)::INTEGER
               AS feasible_split_count
    FROM ml.training_task_candidate AS task
    LEFT JOIN primary_split AS split
      ON split.task_key = task.task_key
    GROUP BY task.task_key
), held_out_families AS (
    SELECT split.task_key,
           count(DISTINCT example.source_family_key)::INTEGER
               AS held_out_source_family_count
    FROM primary_split AS split
    JOIN ml.training_split_assignment AS assignment
      ON assignment.split_candidate_key = split.split_candidate_key
    JOIN ml.training_example_candidate AS example
      ON example.training_example_key = assignment.training_example_key
    JOIN ml.training_partition_eligibility AS partition
      ON partition.partition_eligibility_key =
         example.partition_eligibility_key
     AND partition.task_key = example.task_key
    JOIN ml.training_task_candidate AS task
      ON task.task_key = split.task_key
    WHERE split.split_strategy IN (
          'SOURCE_FAMILY_HOLDOUT', 'HYBRID_GROUPED_SPLIT',
          'ZH_HANS_STRATIFIED_TEST', 'AMBIGUOUS_EXPRESSION_TEST',
          'ABSTENTION_TEST'
      )
      AND assignment.split_name IN ('DEV', 'TEST')
      AND example.label_lifecycle = 'TRAINING_ELIGIBLE'
      AND example.sampling_eligible
      AND partition.counts_as_independent
      AND partition.eligibility_class = CASE task.task_type
          WHEN 'LEXICAL_NORMALIZATION'
            THEN 'ELIGIBLE_FOR_LEXICAL_TRAINING'
          WHEN 'ASSOCIATION_MODEL'
            THEN 'ELIGIBLE_FOR_ASSOCIATION_TRAINING'
          WHEN 'CONTEXT_MODEL'
            THEN 'ELIGIBLE_FOR_CONTEXT_TRAINING'
          ELSE '__PROHIBITED__' END
      AND NOT EXISTS (
          SELECT 1
          FROM ml.training_split_assignment AS train_assignment
          JOIN ml.training_example_candidate AS train_example
            ON train_example.training_example_key =
               train_assignment.training_example_key
          WHERE train_assignment.split_candidate_key =
                assignment.split_candidate_key
            AND train_assignment.split_name = 'TRAIN'
            AND train_example.source_family_key = example.source_family_key
      )
    GROUP BY split.task_key
), duplicate_leaks AS (
    SELECT split.task_key, count(*)::INTEGER AS leak_count
    FROM primary_split AS split
    JOIN ml.training_split_assignment AS left_assignment
      ON left_assignment.split_candidate_key = split.split_candidate_key
    JOIN ml.training_example_candidate AS left_example
      ON left_example.training_example_key =
         left_assignment.training_example_key
    JOIN ml.training_split_assignment AS right_assignment
      ON right_assignment.split_candidate_key = split.split_candidate_key
     AND right_assignment.split_assignment_key >
         left_assignment.split_assignment_key
     AND right_assignment.split_name <> left_assignment.split_name
    JOIN ml.training_example_candidate AS right_example
      ON right_example.training_example_key =
         right_assignment.training_example_key
     AND right_example.duplicate_group_key = left_example.duplicate_group_key
    WHERE left_example.duplicate_group_key IS NOT NULL
    GROUP BY split.task_key
), concentration AS (
    SELECT metric.task_key,
           count(*) FILTER (
               WHERE corpus_scope = 'RAW_CORPUS'
           )::INTEGER AS raw_metric_count,
           count(*) FILTER (
               WHERE corpus_scope = 'TRAINING_CANDIDATE'
                 AND gate_status IN ('PASS_MINIMUM', 'PASS_PREFERRED')
           )::INTEGER AS passing_candidate_metric_count,
           min(largest_source_family_share) FILTER (
               WHERE corpus_scope = 'TRAINING_CANDIDATE'
           ) AS candidate_largest_share
    FROM audit.training_source_concentration AS metric
    JOIN primary_split AS split
      ON split.sampling_policy_key = metric.sampling_policy_key
     AND split.task_key = metric.task_key
    GROUP BY metric.task_key
), relationship AS (
    SELECT
      (SELECT count(*)::INTEGER
       FROM evidence.v_current_relationship_evidence)
        AS relationship_evidence_claim_count,
      delta.source_local_supported_membership_count,
      delta.cross_source_supported_membership_count,
      delta.range_with_source_local_evidence_count,
      delta.range_with_cross_source_evidence_count,
      delta.total_supported_membership_count,
      delta.limitation
    FROM audit.v_model_prebuild_relationship_delta AS delta
), execution AS (
    SELECT
        EXISTS (SELECT 1 FROM audit.round3j_checkpoint) AS checkpoint_exists,
        coalesce(bool_and(
            (SELECT count(*) FROM ml.model) = model_count_at_start
            AND (SELECT count(*) FROM ml.model_run) = model_run_count_at_start
            AND (SELECT count(*) FROM ml.model_version) =
                model_version_count_at_start
        ), FALSE) AS no_model_delta,
        NOT EXISTS (
            SELECT 1 FROM pg_extension WHERE extname = 'vector'
        ) AS no_pgvector,
        (SELECT count(*) FROM calibration.sensory_observation) = 0
          AND (SELECT count(*) FROM calibration.question_response) = 0
          AS no_real_human_response
    FROM audit.round3j_checkpoint
), criteria(
    task_type, readiness_key, minimum_required, preferred_required,
    observed, hard_gate, passed, evidence_path, limitation
) AS (
    SELECT 'LEXICAL_NORMALIZATION'::TEXT,
      'lexical.eligible_unique_expression_count', '>=5000', '>=8000',
      eligible_expression_count::TEXT, TRUE,
      eligible_expression_count >= 5000,
      'ml.training_example_candidate',
      'Unique reviewed expression units, not raw occurrences.'
    FROM lexical
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.source_family_count', '>=8', '>=12',
      source_family_count::TEXT, TRUE, source_family_count >= 8,
      'ml.training_partition_eligibility',
      'Only training-eligible independent source families count.'
    FROM lexical
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.held_out_source_family_count', '>=2', '>=3',
      coalesce(held_out_source_family_count, 0)::TEXT, TRUE,
      coalesce(held_out_source_family_count, 0) >= 2,
      'ml.training_split_assignment',
      'A held-out family has no training assignment in the same candidate split.'
    FROM task_lookup LEFT JOIN held_out_families
      ON held_out_families.task_key = task_lookup.lexical_task_key
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.zh_hans_training_eligible_count', '>=500', '>=1000',
      zh_hans_count::TEXT, TRUE, zh_hans_count >= 500,
      'ml.training_example_candidate',
      'Machine, project, and artificial translations are ineligible.'
    FROM lexical
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.label_provenance_rate', '=1.0000', '=1.0000',
      coalesce(round(provenance_complete_count::NUMERIC
          / NULLIF(eligible_row_count, 0), 4), 0)::TEXT, TRUE,
      eligible_row_count > 0
        AND provenance_complete_count = eligible_row_count,
      'ml.training_example_candidate.label_provenance',
      'Every eligible label resolves to source version, snapshot, rule/review, and target semantics.'
    FROM lexical
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.duplicate_control', '=complete and 0 leaks',
      '=complete and 0 leaks',
      CASE WHEN audit.latest_training_readiness_assertion(
          'DUPLICATE_DETECTION_COMPLETE', task_lookup.lexical_task_key
      ) THEN 'complete' ELSE 'incomplete' END || '; leaks=' ||
        coalesce(duplicate_leaks.leak_count, 0)::TEXT,
      TRUE,
      audit.latest_training_readiness_assertion(
          'DUPLICATE_DETECTION_COMPLETE', task_lookup.lexical_task_key
      ) AND coalesce(duplicate_leaks.leak_count, 0) = 0,
      'audit.training_duplicate_group + ml.training_split_assignment',
      'Deterministic exact, mirror, template, punctuation, and translation controls; no embeddings.'
    FROM task_lookup LEFT JOIN duplicate_leaks
      ON duplicate_leaks.task_key = task_lookup.lexical_task_key
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.source_concentration', '<=0.60', '<=0.45',
      coalesce(concentration.candidate_largest_share::TEXT, 'UNMEASURED'),
      TRUE,
      coalesce(concentration.raw_metric_count, 0) > 0
        AND coalesce(concentration.passing_candidate_metric_count, 0) > 0,
      'audit.training_source_concentration',
      'Raw and capped candidate concentration are both retained and recomputed from allocations.'
    FROM task_lookup LEFT JOIN concentration
      ON concentration.task_key = task_lookup.lexical_task_key
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.grouped_split_feasible', '=true', '=true',
      (coalesce(feasible_split_count, 0) > 0)::TEXT, TRUE,
      coalesce(feasible_split_count, 0) > 0,
      'ml.training_split_candidate',
      'No naive random row split is an allowed strategy.'
    FROM task_lookup LEFT JOIN split_feasibility
      ON split_feasibility.task_key = task_lookup.lexical_task_key
    UNION ALL SELECT 'LEXICAL_NORMALIZATION',
      'lexical.ambiguous_unresolved_evaluation_strata', '>0 each', '>0 each',
      ambiguous_evaluation_count::TEXT || '/' ||
        unresolved_evaluation_count::TEXT,
      TRUE, ambiguous_evaluation_count > 0
        AND unresolved_evaluation_count > 0,
      'ml.training_example_candidate + ml.training_split_assignment',
      'Hard examples remain in held-out evaluation strata.'
    FROM lexical
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.eligible_source_qualified_example_count',
      '>=150', '>=250',
      eligible_example_count::TEXT, TRUE,
      eligible_example_count >= 150,
      'ml.training_example_candidate + readiness-primary split',
      'Association candidates are source-qualified units and remain separate from the curated claim registry.'
    FROM association
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.independent_source_family_count', '>=2', '>2',
      independent_source_family_count::TEXT, TRUE,
      independent_source_family_count >= 2,
      'ml.training_partition_eligibility',
      'Mirrors and repeated measurements are not independent origins.'
    FROM association
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.source_local_semantics_preserved', '=true', '=true',
      (eligible_example_count > 0
       AND semantics_failure_count = 0)::TEXT, TRUE,
      eligible_example_count > 0 AND semantics_failure_count = 0,
      'ml.training_example_candidate',
      'Co-occurrence, co-selection, CATA, RATA, and intensity semantics remain distinct.'
    FROM association
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.relationship_evidence_claim_count', '>=150', '>=250',
      relationship_evidence_claim_count::TEXT, TRUE,
      relationship_evidence_claim_count >= 150,
      'evidence.v_current_relationship_evidence',
      'Reviewed meaningful claims only; pairs are not generated mechanically.'
    FROM relationship
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.cross_source_supported_memberships', '>=6', '>=8',
      cross_source_supported_membership_count::TEXT, TRUE,
      cross_source_supported_membership_count >= 6,
      'audit.v_model_prebuild_relationship_delta',
      'Independent-origin corroboration is required.'
    FROM relationship
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.ranges_with_cross_source_evidence', '>=5', '>=6',
      range_with_cross_source_evidence_count::TEXT, TRUE,
      range_with_cross_source_evidence_count >= 5,
      'audit.v_model_prebuild_relationship_delta',
      'No range promotion is forced to pass this gate.'
    FROM relationship
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.positive_and_challenging_evidence', '>0 each', '>0 each',
      supporting_count::TEXT || '/' || challenging_or_mixed_count::TEXT,
      TRUE, supporting_count > 0 AND challenging_or_mixed_count > 0,
      'ml.training_example_candidate',
      'Explicit challenge or mixed evidence is required; absence is not negative.'
    FROM association
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.grouped_holdout_feasible', '=true', '=true',
      (coalesce(feasible_split_count, 0) > 0)::TEXT, TRUE,
      coalesce(feasible_split_count, 0) > 0,
      'ml.training_split_candidate',
      'Source-qualified relationship groups must remain intact.'
    FROM task_lookup LEFT JOIN split_feasibility
      ON split_feasibility.task_key = task_lookup.association_task_key
    UNION ALL SELECT 'ASSOCIATION_MODEL',
      'association.absence_derived_negative_count', '=0', '=0',
      absence_negative_count::TEXT, TRUE, absence_negative_count = 0,
      'ml.training_example_candidate',
      'Not co-observed never becomes a negative association label.'
    FROM association
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.effective_sample_count', '>=400', '>=800',
      effective_sample_count::TEXT, TRUE, effective_sample_count >= 400,
      'ml.training_example_candidate',
      'Distinct coffee/sample/configuration units, not raw panel rows.'
    FROM context_stats
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.independent_source_family_count', '>=8', '>=12',
      independent_source_family_count::TEXT, TRUE,
      independent_source_family_count >= 8,
      'ml.training_partition_eligibility',
      'Only independent eligible source families contribute.'
    FROM context_stats
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.observed_preparation_roast_cell_count', '>=250', '>=400',
      observed_preparation_roast_cell_count::TEXT, TRUE,
      observed_preparation_roast_cell_count >= 250,
      'ml.training_example_candidate',
      'Observed source-local preparation by roast cells only; no zero fill.'
    FROM context_stats
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.coffee_or_sample_group_count', '>=300', 'not declared',
      coffee_or_sample_group_count::TEXT, TRUE,
      coffee_or_sample_group_count >= 300,
      'ml.training_example_candidate',
      'Identity groups are retained for leakage control.'
    FROM context_stats
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.grouped_holdout_feasible', '=true', '=true',
      (coalesce(feasible_split_count, 0) > 0)::TEXT, TRUE,
      coalesce(feasible_split_count, 0) > 0,
      'ml.training_split_candidate',
      'Coffee/sample identity must not cross grouped boundaries.'
    FROM task_lookup LEFT JOIN split_feasibility
      ON split_feasibility.task_key = task_lookup.context_task_key
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.source_local_outcome_semantics', '=true', '=true',
      (effective_sample_count > 0
       AND semantics_failure_count = 0)::TEXT, TRUE,
      effective_sample_count > 0 AND semantics_failure_count = 0,
      'ml.training_example_candidate',
      'Incompatible source-local outcomes remain federated.'
    FROM context_stats
    UNION ALL SELECT 'CONTEXT_MODEL',
      'context.false_pooled_sensory_scale_count', '=0', '=0',
      false_pooled_scale_count::TEXT, TRUE,
      false_pooled_scale_count = 0,
      'ml.training_example_candidate',
      'No convenience conversion creates a universal descriptor score.'
    FROM context_stats
    UNION ALL SELECT 'QUESTION_MODEL',
      'question.real_sequential_response_evidence', '>0', '>0',
      '0', TRUE, FALSE,
      'calibration.question_response',
      'No real ordinary-user response, information-gain, or stopping evidence exists.'
    UNION ALL SELECT 'ADAPTIVE_POLICY',
      'adaptive.real_sequential_response_evidence', '>0', '>0',
      '0', TRUE, FALSE,
      'calibration.question_response',
      'Adaptive-policy readiness remains false without real sequential outcomes.'
), task_summary AS (
    SELECT task_type,
           bool_and(passed) FILTER (WHERE hard_gate) AS ready
    FROM criteria GROUP BY task_type
), global_state AS (
    SELECT
      EXISTS (
        SELECT 1 FROM audit.training_corpus_release
        WHERE payload_frozen
      ) AS training_corpus_frozen,
      audit.latest_training_readiness_assertion(
        'TRAINING_CORPUS_MANIFEST_REPRODUCIBLE', NULL
      ) AND audit.latest_training_readiness_assertion(
        'SPLIT_MANIFEST_REPRODUCIBLE', NULL
      ) AS reproducible,
      audit.latest_training_readiness_assertion(
        'V0_1_0_IMMUTABLE', NULL
      ) AND EXISTS (
        SELECT 1 FROM audit.research_database_release AS release
        JOIN audit.research_database_release_attestation AS attestation
          ON attestation.freeze_version = release.freeze_version
        WHERE release.freeze_version =
              'coffee-sensory-research-db-v0.1.0'
          AND release.lifecycle_status = 'FROZEN'
      ) AS v0_1_0_immutable,
      execution.checkpoint_exists AND execution.no_model_delta
        AND execution.no_pgvector AS no_training_execution,
      execution.no_real_human_response,
      coalesce((SELECT ready FROM task_summary
                WHERE task_type = 'LEXICAL_NORMALIZATION'), FALSE)
        AS lexical_ready,
      coalesce((SELECT ready FROM task_summary
                WHERE task_type = 'ASSOCIATION_MODEL'), FALSE)
        AS association_ready,
      coalesce((SELECT ready FROM task_summary
                WHERE task_type = 'CONTEXT_MODEL'), FALSE)
        AS context_ready,
      coalesce((SELECT held_out_source_family_count
                FROM held_out_families, task_lookup
                WHERE held_out_families.task_key =
                      task_lookup.lexical_task_key), 0) >= 2
        AS held_out_source_split_ready,
      lexical.eligible_row_count > 0
        AND lexical.provenance_complete_count = lexical.eligible_row_count
        AS label_provenance_complete,
      coalesce((SELECT passing_candidate_metric_count > 0
                FROM concentration, task_lookup
                WHERE concentration.task_key =
                      task_lookup.lexical_task_key), FALSE)
        AND (NOT coalesce((SELECT ready FROM task_summary
                WHERE task_type = 'ASSOCIATION_MODEL'), FALSE)
             OR coalesce((SELECT passing_candidate_metric_count > 0
                FROM concentration, task_lookup
                WHERE concentration.task_key =
                      task_lookup.association_task_key), FALSE))
        AND (NOT coalesce((SELECT ready FROM task_summary
                WHERE task_type = 'CONTEXT_MODEL'), FALSE)
             OR coalesce((SELECT passing_candidate_metric_count > 0
                FROM concentration, task_lookup
                WHERE concentration.task_key =
                      task_lookup.context_task_key), FALSE))
        AS source_concentration_acceptable
    FROM execution CROSS JOIN lexical
), exit_criteria(
    task_type, readiness_key, minimum_required, preferred_required,
    observed, hard_gate, passed, evidence_path, limitation
) AS (
    SELECT 'ROUND3_EXIT'::TEXT, 'exit.training_corpus_frozen',
      '=true', '=true', training_corpus_frozen::TEXT, TRUE,
      training_corpus_frozen, 'audit.training_corpus_release',
      'The candidate payload is manifest-bound before Round 4 authorization.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT', 'exit.lexical_training_ready',
      '=true', '=true', lexical_ready::TEXT, TRUE, lexical_ready,
      'audit.run_training_experiment_readiness_gate()',
      'Lexical readiness is mandatory.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT',
      'exit.association_or_context_training_ready', '=true', '=true',
      (association_ready OR context_ready)::TEXT, TRUE,
      association_ready OR context_ready,
      'audit.run_training_experiment_readiness_gate()',
      'At least one evidence task beyond lexical normalization must be ready.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT', 'exit.held_out_source_split_ready',
      '=true', '=true', held_out_source_split_ready::TEXT, TRUE,
      held_out_source_split_ready, 'ml.training_split_assignment',
      'At least two lexical source families are fully held out.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT', 'exit.label_provenance_rate',
      '=1.0000', '=1.0000', label_provenance_complete::TEXT, TRUE,
      label_provenance_complete,
      'ml.training_example_candidate.label_provenance',
      'No opaque manually typed eligible label is permitted.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT',
      'exit.training_set_source_concentration_acceptable',
      '=true', '=true', source_concentration_acceptable::TEXT, TRUE,
      source_concentration_acceptable,
      'audit.training_source_concentration',
      'The full corpus remains preserved beside any deterministic cap.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT',
      'exit.training_corpus_reproducible', '=true', '=true',
      reproducible::TEXT, TRUE, reproducible,
      'audit.training_readiness_assertion',
      'Candidate and split manifests must reproduce with fixed configuration.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT', 'exit.v0_1_0_immutable',
      '=true', '=true', v0_1_0_immutable::TEXT, TRUE,
      v0_1_0_immutable, 'audit.research_database_release + freeze hashes',
      'Round 3J is additive and cannot mutate the foundational release.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT', 'exit.no_training_execution',
      '=true', '=true', no_training_execution::TEXT, TRUE,
      no_training_execution, 'ml.model_run + ml.model_version + pg_extension',
      'No model fitting, embedding artifact, or pgvector installation occurred.'
    FROM global_state
    UNION ALL SELECT 'ROUND3_EXIT', 'exit.no_real_human_collection',
      '=true', '=true', no_real_human_response::TEXT, TRUE,
      no_real_human_response,
      'calibration.sensory_observation + calibration.question_response',
      'No real participant collection or synthetic response substitution occurred.'
    FROM global_state
), exit_summary AS (
    SELECT bool_and(passed) AS ready FROM exit_criteria WHERE hard_gate
), summaries AS (
    SELECT task_type,
      CASE task_type
        WHEN 'LEXICAL_NORMALIZATION'
          THEN 'LEXICAL_NORMALIZATION_TRAINING_READY'
        WHEN 'ASSOCIATION_MODEL'
          THEN 'ASSOCIATION_MODEL_TRAINING_READY'
        WHEN 'CONTEXT_MODEL'
          THEN 'CONTEXT_MODEL_TRAINING_READY'
        WHEN 'QUESTION_MODEL'
          THEN 'QUESTION_MODEL_TRAINING_READY'
        WHEN 'ADAPTIVE_POLICY'
          THEN 'ADAPTIVE_POLICY_TRAINING_READY' END AS readiness_key,
      '=true'::TEXT AS minimum_required, '=true'::TEXT AS preferred_required,
      ready::TEXT AS observed, TRUE AS hard_gate, ready AS passed,
      'audit.run_training_experiment_readiness_gate()'::TEXT AS evidence_path,
      'All mandatory task-specific conditions must pass.'::TEXT AS limitation
    FROM task_summary
    UNION ALL
    SELECT 'ROUND3_EXIT', 'ROUND3_EXIT_GATE_PASS', '=true', '=true',
      ready::TEXT, TRUE, ready,
      'audit.run_training_experiment_readiness_gate()',
      'Lexical plus association/context readiness and every exit control are required.'
    FROM exit_summary
)
SELECT * FROM criteria
UNION ALL SELECT * FROM summaries
UNION ALL SELECT * FROM exit_criteria
ORDER BY task_type, readiness_key
$run_training_experiment_readiness_gate$;

COMMENT ON FUNCTION audit.run_training_experiment_readiness_gate() IS
    'Task-specific Round 3J readiness and Round 3 exit gate; it evaluates corpus construction only and never model performance.';

CREATE FUNCTION audit.training_task_is_ready(selected_task_type TEXT)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $training_task_is_ready$
SELECT coalesce((
    SELECT passed
    FROM audit.run_training_experiment_readiness_gate()
    WHERE task_type = selected_task_type
      AND readiness_key = CASE selected_task_type
        WHEN 'LEXICAL_NORMALIZATION'
          THEN 'LEXICAL_NORMALIZATION_TRAINING_READY'
        WHEN 'ASSOCIATION_MODEL'
          THEN 'ASSOCIATION_MODEL_TRAINING_READY'
        WHEN 'CONTEXT_MODEL'
          THEN 'CONTEXT_MODEL_TRAINING_READY'
        WHEN 'QUESTION_MODEL'
          THEN 'QUESTION_MODEL_TRAINING_READY'
        WHEN 'ADAPTIVE_POLICY'
          THEN 'ADAPTIVE_POLICY_TRAINING_READY' END
), FALSE)
$training_task_is_ready$;

CREATE FUNCTION audit.round3_exit_gate_passes()
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $round3_exit_gate_passes$
SELECT coalesce((
    SELECT passed
    FROM audit.run_training_experiment_readiness_gate()
    WHERE task_type = 'ROUND3_EXIT'
      AND readiness_key = 'ROUND3_EXIT_GATE_PASS'
), FALSE)
$round3_exit_gate_passes$;

CREATE FUNCTION audit.enforce_training_corpus_release()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_training_corpus_release$
DECLARE
    selected_task_key TEXT;
    selected_task_type TEXT;
    selected_task_status TEXT;
    selected_policy_manifest_path TEXT;
    selected_policy_manifest_sha TEXT;
    selected_split_manifest_path TEXT;
    selected_split_manifest_sha TEXT;
    lexical_listed BOOLEAN := FALSE;
    association_listed BOOLEAN := FALSE;
    context_listed BOOLEAN := FALSE;
    selected_database_status TEXT;
    selected_database_sha TEXT;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE')
       AND OLD.lifecycle_status = 'FROZEN' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_corpus_release_frozen_immutable_ck',
            MESSAGE = 'a frozen training-corpus release is immutable';
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF OLD.payload_frozen THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_payload_immutable_ck',
                MESSAGE = 'a manifest-bound training-corpus payload cannot be deleted';
        END IF;
        RETURN OLD;
    END IF;

    IF TG_OP = 'UPDATE' AND OLD.payload_frozen AND (
        NEW.training_corpus_version IS DISTINCT FROM
            OLD.training_corpus_version
        OR NEW.database_release_version IS DISTINCT FROM
            OLD.database_release_version
        OR NEW.candidate_repository_sha IS DISTINCT FROM
            OLD.candidate_repository_sha
        OR NEW.manifest_path IS DISTINCT FROM OLD.manifest_path
        OR NEW.manifest_sha256 IS DISTINCT FROM OLD.manifest_sha256
        OR NEW.artifact_manifest IS DISTINCT FROM OLD.artifact_manifest
        OR NEW.eligible_task_keys IS DISTINCT FROM OLD.eligible_task_keys
        OR NEW.known_exclusions IS DISTINCT FROM OLD.known_exclusions
        OR NEW.known_leakage_risks IS DISTINCT FROM OLD.known_leakage_risks
        OR NEW.training_corpus_reproducible IS DISTINCT FROM
           OLD.training_corpus_reproducible
        OR NEW.clean_rebuild_count IS DISTINCT FROM OLD.clean_rebuild_count
        OR NEW.source_hash_pass IS DISTINCT FROM OLD.source_hash_pass
        OR NEW.split_manifest_reproducible IS DISTINCT FROM
           OLD.split_manifest_reproducible
        OR NOT NEW.payload_frozen
        OR NEW.payload_frozen_at IS DISTINCT FROM OLD.payload_frozen_at
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_corpus_payload_immutable_ck',
            MESSAGE = 'manifest-bound training-corpus payload fields are immutable';
    END IF;

    IF NEW.payload_frozen AND (
        TG_OP = 'INSERT' OR NOT OLD.payload_frozen
    ) THEN
        IF NEW.lifecycle_status <> 'FREEZE_CANDIDATE'
           OR NEW.payload_frozen_at IS NULL THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_payload_candidate_ck',
                MESSAGE = 'payload binding requires an explicit freeze-candidate state';
        END IF;
        IF cardinality(NEW.eligible_task_keys) <>
           (SELECT count(DISTINCT task_key)
            FROM unnest(NEW.eligible_task_keys) AS task(task_key)) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_task_unique_ck',
                MESSAGE = 'eligible task keys must be unique';
        END IF;
        IF NOT EXISTS (
            SELECT 1
            FROM jsonb_array_elements(NEW.artifact_manifest) AS item(value)
            WHERE item.value ->> 'path' = NEW.manifest_path
              AND item.value ->> 'sha256' = NEW.manifest_sha256
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_manifest_binding_ck',
                MESSAGE = 'artifact manifest must bind the declared corpus manifest path and hash';
        END IF;
        IF EXISTS (
            WITH required(assertion_type) AS (
                VALUES
                  ('TRAINING_CORPUS_MANIFEST_REPRODUCIBLE'::TEXT),
                  ('SPLIT_MANIFEST_REPRODUCIBLE'::TEXT),
                  ('V0_1_0_IMMUTABLE'::TEXT)
            ), latest AS (
                SELECT required.assertion_type,
                       assertion.passed, assertion.evidence_path,
                       assertion.evidence_sha256
                FROM required
                LEFT JOIN LATERAL (
                    SELECT passed, evidence_path, evidence_sha256
                    FROM audit.training_readiness_assertion
                    WHERE assertion_type = required.assertion_type
                      AND task_key IS NULL
                    ORDER BY assertion_version DESC, asserted_at DESC,
                             assertion_key DESC
                    LIMIT 1
                ) AS assertion ON TRUE
            )
            SELECT 1 FROM latest
            WHERE NOT coalesce(latest.passed, FALSE)
               OR NOT EXISTS (
                   SELECT 1
                   FROM jsonb_array_elements(
                       NEW.artifact_manifest
                   ) AS artifact(value)
                   WHERE coalesce(
                       artifact.value ->> 'path',
                       artifact.value ->> 'url',
                       artifact.value ->> 'canonical_url'
                   ) = latest.evidence_path
                     AND artifact.value ->> 'sha256' =
                         latest.evidence_sha256
               )
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_assertion_manifest_ck',
                MESSAGE = 'payload binding requires manifest-bound passing reproducibility and v0.1 immutability assertions';
        END IF;
        FOREACH selected_task_key IN ARRAY NEW.eligible_task_keys LOOP
            SELECT task_type, lifecycle_status
            INTO selected_task_type, selected_task_status
            FROM ml.training_task_candidate
            WHERE task_key = selected_task_key;
            IF selected_task_type IS NULL
               OR selected_task_status <> 'VALIDATED'
               OR NOT audit.training_task_is_ready(selected_task_type) THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    CONSTRAINT = 'training_corpus_release_task_ready_ck',
                    MESSAGE = 'every listed task must pass its task-specific readiness gate';
            END IF;
            lexical_listed := lexical_listed
                OR selected_task_type = 'LEXICAL_NORMALIZATION';
            association_listed := association_listed
                OR selected_task_type = 'ASSOCIATION_MODEL';
            context_listed := context_listed
                OR selected_task_type = 'CONTEXT_MODEL';
            SELECT policy.candidate_manifest_path,
                   policy.candidate_manifest_sha256,
                   split.manifest_path, split.manifest_sha256
            INTO selected_policy_manifest_path,
                 selected_policy_manifest_sha,
                 selected_split_manifest_path,
                 selected_split_manifest_sha
            FROM ml.training_split_candidate AS split
            JOIN ml.training_sampling_policy AS policy
              ON policy.sampling_policy_key = split.sampling_policy_key
             AND policy.task_key = split.task_key
            WHERE split.task_key = selected_task_key
              AND split.readiness_primary
              AND split.lifecycle_status = 'VALIDATED'
              AND split.split_feasible
              AND policy.lifecycle_status = 'FROZEN';
            IF selected_split_manifest_path IS NULL THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    CONSTRAINT = 'training_corpus_release_manifest_inputs_ck',
                    MESSAGE = 'each frozen task requires its exact readiness-primary split and frozen sampling policy';
            END IF;
            IF NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(NEW.artifact_manifest)
                     AS artifact(value)
                WHERE artifact.value ->> 'path' =
                      selected_policy_manifest_path
                  AND artifact.value ->> 'sha256' =
                      selected_policy_manifest_sha
            ) OR NOT EXISTS (
                SELECT 1
                FROM jsonb_array_elements(NEW.artifact_manifest)
                     AS artifact(value)
                WHERE artifact.value ->> 'path' =
                      selected_split_manifest_path
                  AND artifact.value ->> 'sha256' =
                      selected_split_manifest_sha
            ) THEN
                RAISE EXCEPTION USING ERRCODE = '23514',
                    CONSTRAINT = 'training_corpus_release_task_manifest_binding_ck',
                    MESSAGE = 'artifact manifest must bind each exact primary policy and split manifest';
            END IF;
        END LOOP;
        IF NOT lexical_listed
           OR NOT (association_listed OR context_listed) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_task_set_ck',
                MESSAGE = 'the payload requires lexical plus association or context readiness';
        END IF;
        IF EXISTS (
            SELECT 1
            FROM ml.training_split_candidate AS split
            JOIN ml.training_split_assignment AS assignment
              ON assignment.split_candidate_key =
                 split.split_candidate_key
            JOIN ml.training_example_candidate AS example
              ON example.training_example_key =
                 assignment.training_example_key
            JOIN ml.training_partition_eligibility AS partition
              ON partition.partition_eligibility_key =
                 example.partition_eligibility_key
            CROSS JOIN LATERAL jsonb_array_elements(
                partition.source_file_manifest
            ) AS source_item(value)
            WHERE split.readiness_primary
              AND split.lifecycle_status = 'VALIDATED'
              AND split.task_key = ANY(NEW.eligible_task_keys)
              AND NOT EXISTS (
                  SELECT 1
                  FROM jsonb_array_elements(NEW.artifact_manifest)
                       AS artifact(value)
                  WHERE coalesce(
                      artifact.value ->> 'path',
                      artifact.value ->> 'url',
                      artifact.value ->> 'canonical_url'
                  ) = coalesce(
                      source_item.value ->> 'path',
                      source_item.value ->> 'url',
                      source_item.value ->> 'canonical_url'
                  )
                    AND artifact.value ->> 'sha256' =
                        source_item.value ->> 'sha256'
              )
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_source_manifest_binding_ck',
                MESSAGE = 'artifact manifest must bind every source file or snapshot used by eligible primary splits';
        END IF;
    END IF;

    IF NEW.round3_exit_gate_pass
       AND NOT audit.round3_exit_gate_passes() THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'training_corpus_round3_exit_gate_ck',
            MESSAGE = 'Round 3 exit cannot be asserted while any mandatory gate fails';
    END IF;

    IF NEW.promotion_authorized THEN
        IF NOT audit.latest_training_readiness_assertion(
                'REMOTE_FRONTEND_CI', NULL
           ) OR NOT audit.latest_training_readiness_assertion(
                'REMOTE_POSTGRES_CI', NULL
           ) OR NOT audit.latest_training_readiness_assertion(
                'TRAINING_CORPUS_MANIFEST_REPRODUCIBLE', NULL
           ) OR NOT audit.latest_training_readiness_assertion(
                'SPLIT_MANIFEST_REPRODUCIBLE', NULL
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_external_evidence_ck',
                MESSAGE = 'promotion requires immutable reproducibility and remote-CI assertions';
        END IF;
    END IF;

    IF NEW.lifecycle_status = 'FROZEN' THEN
        SELECT lifecycle_status, final_repository_sha
        INTO selected_database_status, selected_database_sha
        FROM audit.research_database_release
        WHERE freeze_version = NEW.database_release_version;
        IF selected_database_status <> 'FROZEN'
           OR selected_database_sha <> NEW.candidate_repository_sha
           OR NOT NEW.round3_exit_gate_pass
           OR NOT audit.round3_exit_gate_passes()
           OR NOT NEW.promotion_authorized THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'training_corpus_release_database_freeze_ck',
                MESSAGE = 'final corpus freeze requires a later immutable database release and authorized Round 3 exit';
        END IF;
    END IF;
    RETURN NEW;
END;
$enforce_training_corpus_release$;

CREATE TRIGGER training_corpus_release_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.training_corpus_release
FOR EACH ROW EXECUTE FUNCTION audit.enforce_training_corpus_release();

CREATE FUNCTION audit.enforce_round3j_acquisition_stop()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3j_acquisition_stop$
DECLARE
    previous_sequence INTEGER;
    previous_no_gain_count INTEGER;
    previous_stop_status TEXT;
    expected_no_gain_count INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.lifecycle_status = 'COMPLETE' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3j_acquisition_batch_complete_immutable_ck',
                MESSAGE = 'completed acquisition batch receipts are immutable';
        END IF;
        RETURN OLD;
    END IF;
    IF NEW.stop_status = 'STOP_EXIT_GATE_PASS'
       AND NOT audit.round3_exit_gate_passes() THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3j_acquisition_exit_stop_ck',
            MESSAGE = 'acquisition cannot stop for a passing exit gate while the gate fails';
    END IF;
    IF NEW.lifecycle_status = 'COMPLETE' THEN
        SELECT batch_sequence, consecutive_no_material_gain_count,
               stop_status
        INTO previous_sequence, previous_no_gain_count,
             previous_stop_status
        FROM audit.round3j_acquisition_batch
        WHERE lifecycle_status = 'COMPLETE'
          AND batch_key <> NEW.batch_key
          AND batch_sequence < NEW.batch_sequence
        ORDER BY batch_sequence DESC
        LIMIT 1;
        IF NEW.batch_sequence <> 1
           AND previous_sequence IS DISTINCT FROM NEW.batch_sequence - 1 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3j_acquisition_batch_sequence_ck',
                MESSAGE = 'completed acquisition batches require a contiguous prior receipt';
        END IF;
        IF coalesce(previous_no_gain_count, 0) = 3 THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3j_acquisition_stop_after_three_ck',
                MESSAGE = 'no acquisition batch may complete after the three-no-gain stop rule';
        END IF;
        IF previous_stop_status IS NOT NULL
           AND previous_stop_status <> 'CONTINUE' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3j_acquisition_terminal_receipt_ck',
                MESSAGE = 'no acquisition batch may complete after any terminal stop receipt';
        END IF;
        expected_no_gain_count := CASE WHEN NEW.material_gain THEN 0
            ELSE coalesce(previous_no_gain_count, 0) + 1 END;
        IF NEW.consecutive_no_material_gain_count <>
           expected_no_gain_count THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3j_acquisition_no_gain_sequence_ck',
                MESSAGE = 'consecutive no-gain count must follow the prior completed batch';
        END IF;
    END IF;
    IF TG_OP = 'UPDATE' AND OLD.lifecycle_status = 'COMPLETE' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3j_acquisition_batch_complete_immutable_ck',
            MESSAGE = 'completed acquisition batch receipts are immutable';
    END IF;
    RETURN NEW;
END;
$enforce_round3j_acquisition_stop$;

CREATE TRIGGER round3j_acquisition_stop_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.round3j_acquisition_batch
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3j_acquisition_stop();

CREATE FUNCTION audit.prevent_round3j_model_execution()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3j_model_execution$
BEGIN
    IF EXISTS (SELECT 1 FROM audit.round3j_checkpoint) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3j_model_execution_prohibited_ck',
            MESSAGE = 'Round 3J may construct corpora and splits but cannot create or mutate model artifacts';
    END IF;
    IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END;
$prevent_round3j_model_execution$;

CREATE TRIGGER round3j_model_prohibited_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.model
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3j_model_execution();

CREATE TRIGGER round3j_model_run_prohibited_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3j_model_execution();

CREATE TRIGGER round3j_model_version_prohibited_biud
BEFORE INSERT OR UPDATE OR DELETE ON ml.model_version
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3j_model_execution();

COMMIT;
