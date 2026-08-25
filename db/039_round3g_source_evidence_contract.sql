\set ON_ERROR_STOP on

BEGIN;

CREATE TABLE evidence.source_family (
    source_family_key TEXT NOT NULL,
    family_name TEXT NOT NULL,
    family_type TEXT NOT NULL,
    canonical_origin_key TEXT NOT NULL,
    counts_as_independent BOOLEAN NOT NULL,
    mirror_of_source_family_key TEXT,
    independence_basis TEXT NOT NULL,
    admitted BOOLEAN NOT NULL,
    introduced_round TEXT NOT NULL DEFAULT '3G',
    CONSTRAINT source_family_pk PRIMARY KEY (source_family_key),
    CONSTRAINT source_family_mirror_fk FOREIGN KEY (
        mirror_of_source_family_key
    ) REFERENCES evidence.source_family (source_family_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT source_family_text_ck CHECK (
        source_family_key = lower(btrim(source_family_key))
        AND source_family_key <> ''
        AND family_name = btrim(family_name) AND family_name <> ''
        AND canonical_origin_key = lower(btrim(canonical_origin_key))
        AND canonical_origin_key <> ''
        AND independence_basis = btrim(independence_basis)
        AND independence_basis <> ''
        AND introduced_round = '3G'
    ),
    CONSTRAINT source_family_type_ck CHECK (
        family_type IN (
            'COFFEE_SENSORY', 'CONSUMER_STUDY',
            'BILINGUAL_LEXICAL', 'CONTEMPORARY_LANGUAGE',
            'FORMAL_STANDARD', 'OTHER_RESEARCH'
        )
    ),
    CONSTRAINT source_family_mirror_independence_ck CHECK (
        mirror_of_source_family_key IS DISTINCT FROM source_family_key
        AND (mirror_of_source_family_key IS NULL OR NOT counts_as_independent)
    ),
    CONSTRAINT source_family_admission_ck CHECK (
        NOT admitted OR counts_as_independent
    )
);

CREATE UNIQUE INDEX source_family_independent_origin_uq
ON evidence.source_family (canonical_origin_key)
WHERE counts_as_independent;

CREATE TABLE evidence.relationship_source (
    source_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    title TEXT NOT NULL,
    authors_or_owner TEXT NOT NULL,
    publication_year SMALLINT NOT NULL,
    doi_or_stable_url TEXT NOT NULL,
    repository TEXT NOT NULL,
    exact_version TEXT NOT NULL,
    access_date DATE NOT NULL,
    source_type TEXT NOT NULL,
    geography TEXT NOT NULL,
    language TEXT NOT NULL,
    population_or_panel TEXT NOT NULL,
    sensory_method TEXT NOT NULL,
    preparation_coverage TEXT NOT NULL,
    roast_coverage TEXT NOT NULL,
    milk_coverage TEXT NOT NULL,
    license TEXT NOT NULL,
    commercial_use_allowed BOOLEAN NOT NULL,
    derivative_use_allowed BOOLEAN NOT NULL,
    redistribution_allowed BOOLEAN NOT NULL,
    machine_use_allowed BOOLEAN NOT NULL,
    rights_review_status TEXT NOT NULL,
    privacy_review_status TEXT NOT NULL,
    privacy_decision TEXT NOT NULL,
    public_export_decision TEXT NOT NULL,
    file_list JSONB NOT NULL,
    row_count INTEGER NOT NULL,
    field_count INTEGER NOT NULL,
    evidence_role TEXT NOT NULL,
    supported_relationship_keys TEXT[] NOT NULL,
    challenged_relationship_keys TEXT[] NOT NULL,
    evidence_locator TEXT NOT NULL,
    limitations TEXT NOT NULL,
    independence_note TEXT NOT NULL,
    admitted BOOLEAN NOT NULL,
    CONSTRAINT relationship_source_pk PRIMARY KEY (source_key),
    CONSTRAINT relationship_source_family_fk FOREIGN KEY (
        source_family_key
    ) REFERENCES evidence.source_family (source_family_key)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relationship_source_key_family_uq UNIQUE (
        source_key, source_family_key
    ),
    CONSTRAINT relationship_source_text_ck CHECK (
        source_key = lower(btrim(source_key)) AND source_key <> ''
        AND title = btrim(title) AND title <> ''
        AND authors_or_owner = btrim(authors_or_owner)
        AND authors_or_owner <> ''
        AND doi_or_stable_url = btrim(doi_or_stable_url)
        AND doi_or_stable_url <> ''
        AND repository = btrim(repository) AND repository <> ''
        AND exact_version = btrim(exact_version) AND exact_version <> ''
        AND geography = btrim(geography) AND geography <> ''
        AND language = btrim(language) AND language <> ''
        AND population_or_panel = btrim(population_or_panel)
        AND population_or_panel <> ''
        AND sensory_method = btrim(sensory_method)
        AND sensory_method <> ''
        AND preparation_coverage = btrim(preparation_coverage)
        AND preparation_coverage <> ''
        AND roast_coverage = btrim(roast_coverage)
        AND roast_coverage <> ''
        AND milk_coverage = btrim(milk_coverage)
        AND milk_coverage <> ''
        AND license = btrim(license) AND license <> ''
        AND evidence_role = btrim(evidence_role) AND evidence_role <> ''
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
        AND limitations = btrim(limitations) AND limitations <> ''
        AND independence_note = btrim(independence_note)
        AND independence_note <> ''
    ),
    CONSTRAINT relationship_source_shape_ck CHECK (
        publication_year BETWEEN 1900 AND 2100
        AND row_count >= 0 AND field_count >= 0
        AND jsonb_typeof(file_list) = 'array'
        AND jsonb_array_length(file_list) > 0
    ),
    CONSTRAINT relationship_source_review_ck CHECK (
        rights_review_status IN ('CLEARED', 'REJECTED', 'PENDING')
        AND privacy_review_status IN ('REVIEWED', 'REJECTED', 'PENDING')
        AND privacy_decision IN (
            'NO_PERSONAL_DATA', 'PUBLIC_AGGREGATE_ONLY',
            'PUBLIC_SOURCE_NO_LOCAL_DATA', 'REJECTED_PRIVACY'
        )
        AND public_export_decision IN (
            'PUBLIC_AGGREGATE', 'PUBLIC_METADATA',
            'MIXED_EXTERNAL_RAW_PUBLIC_DERIVED', 'BLOCKED'
        )
    ),
    CONSTRAINT relationship_source_admission_ck CHECK (
        NOT admitted OR (
            commercial_use_allowed
            AND derivative_use_allowed
            AND redistribution_allowed
            AND machine_use_allowed
            AND rights_review_status = 'CLEARED'
            AND privacy_review_status = 'REVIEWED'
            AND privacy_decision <> 'REJECTED_PRIVACY'
            AND public_export_decision <> 'BLOCKED'
        )
    )
);

CREATE TABLE evidence.source_candidate_register (
    candidate_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    targeted_range_or_gap TEXT NOT NULL,
    reason_for_search TEXT NOT NULL,
    access_result TEXT NOT NULL,
    rights_result TEXT NOT NULL,
    decision TEXT NOT NULL,
    next_action TEXT NOT NULL,
    stop_status TEXT NOT NULL,
    reviewed_on DATE NOT NULL,
    CONSTRAINT source_candidate_register_pk PRIMARY KEY (candidate_key),
    CONSTRAINT source_candidate_register_source_uq UNIQUE (source_key),
    CONSTRAINT source_candidate_register_text_ck CHECK (
        candidate_key = lower(btrim(candidate_key))
        AND candidate_key <> ''
        AND source_key = lower(btrim(source_key)) AND source_key <> ''
        AND targeted_range_or_gap = btrim(targeted_range_or_gap)
        AND targeted_range_or_gap <> ''
        AND reason_for_search = btrim(reason_for_search)
        AND reason_for_search <> ''
        AND access_result = btrim(access_result) AND access_result <> ''
        AND rights_result = btrim(rights_result) AND rights_result <> ''
        AND next_action = btrim(next_action) AND next_action <> ''
    ),
    CONSTRAINT source_candidate_register_decision_ck CHECK (
        decision IN (
            'ADMIT_AGGREGATE_ONLY', 'ADMIT_METADATA_ONLY',
            'REJECT_OUT_OF_SCOPE', 'REJECT_RIGHTS',
            'REJECT_PRIVACY', 'REJECT_ACCESS_TERMS'
        )
        AND stop_status LIKE 'STOP_%'
    )
);

CREATE TABLE evidence.relationship_source_snapshot (
    snapshot_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    exact_version TEXT NOT NULL,
    acquired_at TIMESTAMPTZ NOT NULL,
    immutable_locator TEXT NOT NULL,
    snapshot_sha256 TEXT NOT NULL,
    source_record_count INTEGER NOT NULL,
    admitted BOOLEAN NOT NULL,
    CONSTRAINT relationship_source_snapshot_pk PRIMARY KEY (snapshot_key),
    CONSTRAINT relationship_source_snapshot_source_fk FOREIGN KEY (
        source_key, source_family_key
    ) REFERENCES evidence.relationship_source (
        source_key, source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relationship_source_snapshot_composite_uq UNIQUE (
        snapshot_key, source_key, source_family_key
    ),
    CONSTRAINT relationship_source_snapshot_text_ck CHECK (
        snapshot_key = lower(btrim(snapshot_key)) AND snapshot_key <> ''
        AND exact_version = btrim(exact_version) AND exact_version <> ''
        AND immutable_locator = btrim(immutable_locator)
        AND immutable_locator <> ''
        AND snapshot_sha256 ~ '^[0-9a-f]{64}$'
        AND source_record_count >= 0
    )
);

CREATE TABLE evidence.relationship_source_file (
    file_key TEXT NOT NULL,
    snapshot_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_role TEXT NOT NULL,
    locator TEXT NOT NULL,
    license TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    declared_sha256 TEXT NOT NULL,
    verified_sha256 TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    field_count INTEGER NOT NULL,
    hash_verified BOOLEAN NOT NULL,
    contains_participant_identifiers BOOLEAN NOT NULL,
    public_export_decision TEXT NOT NULL,
    local_path TEXT,
    CONSTRAINT relationship_source_file_pk PRIMARY KEY (file_key),
    CONSTRAINT relationship_source_file_snapshot_fk FOREIGN KEY (
        snapshot_key, source_key, source_family_key
    ) REFERENCES evidence.relationship_source_snapshot (
        snapshot_key, source_key, source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relationship_source_file_text_ck CHECK (
        file_key = lower(btrim(file_key)) AND file_key <> ''
        AND filename = btrim(filename) AND filename <> ''
        AND locator = btrim(locator) AND locator <> ''
        AND license = btrim(license) AND license <> ''
        AND declared_sha256 ~ '^[0-9a-f]{64}$'
        AND verified_sha256 ~ '^[0-9a-f]{64}$'
        AND (local_path IS NULL OR (
            local_path = btrim(local_path) AND local_path <> ''
        ))
    ),
    CONSTRAINT relationship_source_file_shape_ck CHECK (
        file_role IN (
            'RAW_EXTERNAL', 'DERIVED_AGGREGATE', 'REVISION_METADATA'
        )
        AND file_size_bytes >= 0 AND row_count >= 0 AND field_count >= 0
        AND public_export_decision IN (
            'EXTERNAL_ONLY', 'PUBLIC_AGGREGATE', 'PUBLIC_METADATA'
        )
    ),
    CONSTRAINT relationship_source_file_hash_match_ck CHECK (
        NOT hash_verified OR declared_sha256 = verified_sha256
    ),
    CONSTRAINT relationship_source_file_privacy_export_ck CHECK (
        NOT contains_participant_identifiers
        OR public_export_decision = 'EXTERNAL_ONLY'
    ),
    CONSTRAINT relationship_source_file_local_export_ck CHECK (
        (public_export_decision = 'EXTERNAL_ONLY' AND local_path IS NULL)
        OR (public_export_decision <> 'EXTERNAL_ONLY' AND local_path IS NOT NULL)
    )
);

CREATE TABLE evidence.relationship_evidence_claim (
    evidence_claim_key TEXT NOT NULL,
    target_entity_type TEXT NOT NULL,
    target_entity_key TEXT NOT NULL,
    source_family_key TEXT NOT NULL,
    source_key TEXT NOT NULL,
    snapshot_key TEXT NOT NULL,
    evidence_basis TEXT NOT NULL,
    evidence_direction TEXT NOT NULL,
    evidence_scope TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    method TEXT NOT NULL,
    configuration JSONB NOT NULL,
    support_count INTEGER NOT NULL,
    document_count INTEGER NOT NULL,
    source_diversity INTEGER NOT NULL,
    review_status TEXT NOT NULL,
    limitation TEXT NOT NULL,
    contradictory_evidence_retained BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT relationship_evidence_claim_pk PRIMARY KEY (
        evidence_claim_key
    ),
    CONSTRAINT relationship_evidence_claim_source_fk FOREIGN KEY (
        source_key, source_family_key
    ) REFERENCES evidence.relationship_source (
        source_key, source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relationship_evidence_claim_snapshot_fk FOREIGN KEY (
        snapshot_key, source_key, source_family_key
    ) REFERENCES evidence.relationship_source_snapshot (
        snapshot_key, source_key, source_family_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relationship_evidence_claim_target_ck CHECK (
        target_entity_type IN (
            'ASSOCIATION_RANGE', 'MEMBERSHIP', 'QUESTION_TARGET'
        )
    ),
    CONSTRAINT relationship_evidence_claim_basis_ck CHECK (
        evidence_basis IN (
            'SOURCE_DEFINED_GROUPING', 'OBSERVED_CO_OCCURRENCE',
            'OBSERVED_CO_SELECTION', 'LEXICAL_ATTESTATION',
            'QUESTION_WORDING_EVIDENCE', 'COFFEE_SENSORY_STUDY',
            'FORMAL_STANDARD', 'INDEPENDENT_BILINGUAL_REVIEW',
            'CURATED_REVIEW'
        )
    ),
    CONSTRAINT relationship_evidence_claim_direction_ck CHECK (
        evidence_direction IN (
            'SUPPORTS', 'CHALLENGES', 'MIXED',
            'INSUFFICIENT', 'OUT_OF_SCOPE'
        )
    ),
    CONSTRAINT relationship_evidence_claim_counts_ck CHECK (
        support_count >= 0 AND document_count >= 0
        AND source_diversity >= 1
        AND jsonb_typeof(configuration) = 'object'
        AND configuration <> '{}'::JSONB
    ),
    CONSTRAINT relationship_evidence_claim_text_ck CHECK (
        evidence_claim_key = lower(btrim(evidence_claim_key))
        AND evidence_claim_key <> ''
        AND target_entity_key = lower(btrim(target_entity_key))
        AND target_entity_key <> ''
        AND evidence_scope = btrim(evidence_scope) AND evidence_scope <> ''
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
        AND method = btrim(method) AND method <> ''
        AND review_status IN ('REVIEWED', 'PENDING')
        AND limitation = btrim(limitation) AND limitation <> ''
    )
);

CREATE INDEX relationship_evidence_claim_target_ix
ON evidence.relationship_evidence_claim (
    target_entity_type, target_entity_key, evidence_direction
);

CREATE INDEX relationship_evidence_claim_source_family_ix
ON evidence.relationship_evidence_claim (
    source_family_key, source_key, snapshot_key
);

CREATE FUNCTION evidence.validate_relationship_evidence_target()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_relationship_evidence_target$
BEGIN
    IF NEW.target_entity_type = 'ASSOCIATION_RANGE'
       AND NOT EXISTS (
           SELECT 1 FROM corpus.association_range
           WHERE range_key = NEW.target_entity_key
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503',
            CONSTRAINT = 'relationship_evidence_claim_range_target_fk',
            MESSAGE = 'relationship evidence range target does not exist';
    ELSIF NEW.target_entity_type = 'MEMBERSHIP'
       AND NOT EXISTS (
           SELECT 1 FROM corpus.association_range_membership
           WHERE membership_key = NEW.target_entity_key
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503',
            CONSTRAINT = 'relationship_evidence_claim_membership_target_fk',
            MESSAGE = 'relationship evidence membership target does not exist';
    ELSIF NEW.target_entity_type = 'QUESTION_TARGET'
       AND NOT EXISTS (
           SELECT 1 FROM calibration.question_range_target
           WHERE question_range_target_key = NEW.target_entity_key
       ) THEN
        RAISE EXCEPTION USING ERRCODE = '23503',
            CONSTRAINT = 'relationship_evidence_claim_question_target_fk',
            MESSAGE = 'relationship evidence question target does not exist';
    END IF;
    RETURN NEW;
END
$validate_relationship_evidence_target$;

CREATE TRIGGER relationship_evidence_claim_target_biu
BEFORE INSERT OR UPDATE ON evidence.relationship_evidence_claim
FOR EACH ROW EXECUTE FUNCTION evidence.validate_relationship_evidence_target();

CREATE FUNCTION evidence.retain_round3g_contradictory_evidence()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $retain_round3g_contradictory_evidence$
BEGIN
    IF OLD.evidence_direction IN ('CHALLENGES', 'MIXED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_contradictory_evidence_retained_ck',
            MESSAGE = 'challenging or mixed Round 3G evidence cannot be silently deleted';
    END IF;
    RETURN OLD;
END
$retain_round3g_contradictory_evidence$;

CREATE TRIGGER relationship_evidence_claim_retain_bd
BEFORE DELETE ON evidence.relationship_evidence_claim
FOR EACH ROW EXECUTE FUNCTION evidence.retain_round3g_contradictory_evidence();

CREATE TABLE kb.relationship_review_decision (
    review_key TEXT NOT NULL,
    association_range_membership_id BIGINT NOT NULL,
    disposition TEXT NOT NULL,
    prior_lifecycle TEXT NOT NULL,
    new_lifecycle TEXT NOT NULL,
    supporting_source_families TEXT[] NOT NULL,
    challenging_source_families TEXT[] NOT NULL,
    decision_reason TEXT NOT NULL,
    remaining_uncertainty TEXT NOT NULL,
    review_protocol TEXT NOT NULL,
    reviewed_round TEXT NOT NULL DEFAULT '3G',
    CONSTRAINT relationship_review_decision_pk PRIMARY KEY (review_key),
    CONSTRAINT relationship_review_decision_membership_fk FOREIGN KEY (
        association_range_membership_id
    ) REFERENCES corpus.association_range_membership (
        association_range_membership_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT relationship_review_decision_membership_round_uq UNIQUE (
        association_range_membership_id, reviewed_round
    ),
    CONSTRAINT relationship_review_decision_disposition_ck CHECK (
        disposition IN (
            'PROMOTE_SOURCE_LOCAL', 'PROMOTE_CROSS_SOURCE',
            'RETAIN_CANDIDATE', 'REJECT', 'RETURN_TO_UNRESOLVED'
        )
        AND prior_lifecycle IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED',
            'BILINGUAL_REVIEWED', 'REJECTED', 'DEPRECATED'
        )
        AND new_lifecycle IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED',
            'REJECTED', 'DEPRECATED'
        )
        AND reviewed_round = '3G'
    ),
    CONSTRAINT relationship_review_decision_consistency_ck CHECK (
        (disposition = 'PROMOTE_SOURCE_LOCAL'
            AND new_lifecycle = 'SOURCE_LOCAL_SUPPORTED'
            AND cardinality(supporting_source_families) >= 1)
        OR (disposition = 'PROMOTE_CROSS_SOURCE'
            AND new_lifecycle = 'CROSS_SOURCE_SUPPORTED'
            AND cardinality(supporting_source_families) >= 2)
        OR (disposition = 'RETAIN_CANDIDATE'
            AND new_lifecycle = 'CANDIDATE')
        OR (disposition = 'REJECT' AND new_lifecycle = 'REJECTED')
        OR (disposition = 'RETURN_TO_UNRESOLVED'
            AND new_lifecycle = 'CANDIDATE')
    ),
    CONSTRAINT relationship_review_decision_text_ck CHECK (
        review_key = lower(btrim(review_key)) AND review_key <> ''
        AND decision_reason = btrim(decision_reason)
        AND decision_reason <> ''
        AND remaining_uncertainty = btrim(remaining_uncertainty)
        AND remaining_uncertainty <> ''
        AND review_protocol = btrim(review_protocol)
        AND review_protocol <> ''
    )
);

CREATE TABLE calibration.question_target_review_decision (
    review_key TEXT NOT NULL,
    question_range_target_id BIGINT NOT NULL,
    disposition TEXT NOT NULL,
    supporting_source_families TEXT[] NOT NULL,
    challenging_source_families TEXT[] NOT NULL,
    decision_reason TEXT NOT NULL,
    remaining_uncertainty TEXT NOT NULL,
    review_protocol TEXT NOT NULL,
    reviewed_round TEXT NOT NULL DEFAULT '3G',
    CONSTRAINT question_target_review_decision_pk PRIMARY KEY (review_key),
    CONSTRAINT question_target_review_decision_target_fk FOREIGN KEY (
        question_range_target_id
    ) REFERENCES calibration.question_range_target (
        question_range_target_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT question_target_review_decision_target_round_uq UNIQUE (
        question_range_target_id, reviewed_round
    ),
    CONSTRAINT question_target_review_decision_disposition_ck CHECK (
        disposition IN (
            'RETAIN_HYPOTHESIS', 'RESEARCH_SUPPORT_ADDED',
            'BILINGUAL_REVIEW_REQUIRED', 'REJECT_TARGET',
            'RETURN_TO_UNRESOLVED'
        )
        AND reviewed_round = '3G'
    ),
    CONSTRAINT question_target_review_decision_text_ck CHECK (
        review_key = lower(btrim(review_key)) AND review_key <> ''
        AND decision_reason = btrim(decision_reason)
        AND decision_reason <> ''
        AND remaining_uncertainty = btrim(remaining_uncertainty)
        AND remaining_uncertainty <> ''
        AND review_protocol = btrim(review_protocol)
        AND review_protocol <> ''
    )
);

CREATE TABLE audit.range_review_decision (
    review_key TEXT NOT NULL,
    association_range_id BIGINT NOT NULL,
    disposition TEXT NOT NULL,
    prior_lifecycle TEXT NOT NULL,
    new_lifecycle TEXT NOT NULL,
    supporting_source_families TEXT[] NOT NULL,
    challenging_source_families TEXT[] NOT NULL,
    decision_reason TEXT NOT NULL,
    remaining_uncertainty TEXT NOT NULL,
    review_protocol TEXT NOT NULL,
    reviewed_round TEXT NOT NULL DEFAULT '3G',
    CONSTRAINT range_review_decision_pk PRIMARY KEY (review_key),
    CONSTRAINT range_review_decision_range_fk FOREIGN KEY (
        association_range_id
    ) REFERENCES corpus.association_range (association_range_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT range_review_decision_range_round_uq UNIQUE (
        association_range_id, reviewed_round
    ),
    CONSTRAINT range_review_decision_disposition_ck CHECK (
        disposition IN (
            'REVIEWED_RETAIN_CANDIDATE', 'PROMOTE_SOURCE_LOCAL',
            'PROMOTE_CROSS_SOURCE', 'RESEARCH_REVIEWED',
            'REJECT', 'RETURN_TO_UNRESOLVED'
        )
        AND prior_lifecycle = 'CANDIDATE'
        AND new_lifecycle IN (
            'CANDIDATE', 'SOURCE_LOCAL_SUPPORTED',
            'CROSS_SOURCE_SUPPORTED', 'RESEARCH_REVIEWED', 'REJECTED'
        )
        AND reviewed_round = '3G'
    ),
    CONSTRAINT range_review_decision_text_ck CHECK (
        review_key = lower(btrim(review_key)) AND review_key <> ''
        AND decision_reason = btrim(decision_reason)
        AND decision_reason <> ''
        AND remaining_uncertainty = btrim(remaining_uncertainty)
        AND remaining_uncertainty <> ''
        AND review_protocol = btrim(review_protocol)
        AND review_protocol <> ''
    )
);

CREATE TABLE audit.round3g_threshold_revision (
    revision_key TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    original_value TEXT NOT NULL,
    revised_value TEXT NOT NULL,
    written_reason TEXT NOT NULL,
    epistemic_impact TEXT NOT NULL,
    invalidity_evidence TEXT NOT NULL,
    decision_record_key TEXT NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT round3g_threshold_revision_pk PRIMARY KEY (revision_key),
    CONSTRAINT round3g_threshold_revision_decision_ck CHECK (
        revision_key = lower(btrim(revision_key)) AND revision_key <> ''
        AND metric_key = upper(btrim(metric_key)) AND metric_key <> ''
        AND original_value <> revised_value
        AND written_reason = btrim(written_reason) AND written_reason <> ''
        AND epistemic_impact = btrim(epistemic_impact)
        AND epistemic_impact <> ''
        AND invalidity_evidence = btrim(invalidity_evidence)
        AND invalidity_evidence <> ''
        AND decision_record_key = btrim(decision_record_key)
        AND decision_record_key <> ''
    )
);

CREATE TABLE audit.data_access_request_update (
    request_key TEXT NOT NULL,
    source_doi TEXT NOT NULL,
    contact_verification TEXT NOT NULL,
    requested_fields TEXT NOT NULL,
    desired_license_and_release_rights TEXT NOT NULL,
    prepared_request_text_path TEXT NOT NULL,
    request_sent BOOLEAN NOT NULL,
    reviewed_round TEXT NOT NULL DEFAULT '3G',
    CONSTRAINT data_access_request_update_pk PRIMARY KEY (request_key),
    CONSTRAINT data_access_request_update_unsent_ck CHECK (
        NOT request_sent AND reviewed_round = '3G'
    ),
    CONSTRAINT data_access_request_update_text_ck CHECK (
        request_key = lower(btrim(request_key)) AND request_key <> ''
        AND source_doi = btrim(source_doi) AND source_doi <> ''
        AND contact_verification = btrim(contact_verification)
        AND contact_verification <> ''
        AND requested_fields = btrim(requested_fields)
        AND requested_fields <> ''
        AND desired_license_and_release_rights =
            btrim(desired_license_and_release_rights)
        AND desired_license_and_release_rights <> ''
        AND prepared_request_text_path = btrim(prepared_request_text_path)
        AND prepared_request_text_path <> ''
    )
);

CREATE TABLE audit.round3g_checkpoint (
    checkpoint_key TEXT NOT NULL,
    source_sha TEXT NOT NULL,
    expected_state_commit_sha TEXT NOT NULL,
    expected_state_frozen_before_import BOOLEAN NOT NULL,
    threshold_revision_count INTEGER NOT NULL,
    canonical_concept_count_before INTEGER NOT NULL,
    active_sensory_attribute_count_before INTEGER NOT NULL,
    association_range_count_before INTEGER NOT NULL,
    association_membership_count_before INTEGER NOT NULL,
    question_target_count_before INTEGER NOT NULL,
    new_active_association_range_count INTEGER NOT NULL,
    automatic_promotion_path_count INTEGER NOT NULL,
    real_human_collection_performed BOOLEAN NOT NULL,
    real_observation_count INTEGER NOT NULL,
    question_user_validated_count INTEGER NOT NULL,
    question_information_gain_estimated_count INTEGER NOT NULL,
    model_or_embedding_run_count INTEGER NOT NULL,
    product_frontend_modified BOOLEAN NOT NULL,
    CONSTRAINT round3g_checkpoint_pk PRIMARY KEY (checkpoint_key),
    CONSTRAINT round3g_checkpoint_sha_ck CHECK (
        source_sha ~ '^[0-9a-f]{40}$'
        AND expected_state_commit_sha ~ '^[0-9a-f]{40}$'
    ),
    CONSTRAINT round3g_checkpoint_baseline_ck CHECK (
        expected_state_frozen_before_import
        AND threshold_revision_count = 0
        AND canonical_concept_count_before = 130
        AND active_sensory_attribute_count_before = 92
        AND association_range_count_before = 7
        AND association_membership_count_before = 18
        AND question_target_count_before = 18
    ),
    CONSTRAINT round3g_checkpoint_prohibition_ck CHECK (
        new_active_association_range_count = 0
        AND automatic_promotion_path_count = 0
        AND NOT real_human_collection_performed
        AND real_observation_count = 0
        AND question_user_validated_count = 0
        AND question_information_gain_estimated_count = 0
        AND model_or_embedding_run_count = 0
        AND NOT product_frontend_modified
    )
);

CREATE TABLE audit.round3g_constraint_registry (
    constraint_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    rule TEXT NOT NULL,
    enforcement_layer TEXT NOT NULL,
    negative_test TEXT NOT NULL,
    CONSTRAINT round3g_constraint_registry_pk PRIMARY KEY (constraint_key),
    CONSTRAINT round3g_constraint_registry_text_ck CHECK (
        constraint_key = lower(btrim(constraint_key))
        AND constraint_key <> ''
        AND scope = btrim(scope) AND scope <> ''
        AND rule = btrim(rule) AND rule <> ''
        AND enforcement_layer IN (
            'POSTGRESQL_CONSTRAINT', 'POSTGRESQL_TRIGGER',
            'AUDIT_QUERY', 'CI_GATE', 'CURATION_POLICY'
        )
        AND negative_test = btrim(negative_test)
        AND negative_test <> ''
    )
);

CREATE FUNCTION audit.enforce_round3g_membership_promotion()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3g_membership_promotion$
DECLARE
    independent_origin_count INTEGER;
BEGIN
    IF NEW.lifecycle_status = 'BILINGUAL_REVIEWED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_bilingual_review_prohibited_ck',
            MESSAGE = 'Round 3G has no independent bilingual reviewer record';
    END IF;

    IF NEW.lifecycle_status = 'ACTIVE_FOR_CALIBRATION' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_membership_calibration_prohibited_ck',
            MESSAGE = 'Round 3G cannot activate a membership for calibration';
    END IF;

    IF NEW.lifecycle_status IN (
        'SOURCE_LOCAL_SUPPORTED', 'CROSS_SOURCE_SUPPORTED'
    ) AND NEW.lifecycle_status IS DISTINCT FROM OLD.lifecycle_status THEN
        IF NOT EXISTS (
            SELECT 1
            FROM kb.relationship_review_decision AS decision
            WHERE decision.association_range_membership_id =
                NEW.association_range_membership_id
              AND decision.reviewed_round = '3G'
              AND decision.new_lifecycle = NEW.lifecycle_status
              AND decision.disposition = CASE NEW.lifecycle_status
                  WHEN 'SOURCE_LOCAL_SUPPORTED' THEN 'PROMOTE_SOURCE_LOCAL'
                  ELSE 'PROMOTE_CROSS_SOURCE'
              END
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3g_membership_promotion_review_ck',
                MESSAGE = 'membership promotion requires a matching Round 3G review decision';
        END IF;

        SELECT count(DISTINCT family.canonical_origin_key)
        INTO independent_origin_count
        FROM evidence.relationship_evidence_claim AS claim
        JOIN evidence.source_family AS family
          ON family.source_family_key = claim.source_family_key
        WHERE claim.target_entity_type = 'MEMBERSHIP'
          AND claim.target_entity_key = NEW.membership_key
          AND claim.evidence_direction = 'SUPPORTS'
          AND claim.review_status = 'REVIEWED'
          AND claim.support_count >= 3
          AND claim.document_count >= 2
          AND family.counts_as_independent
          AND family.admitted;

        IF independent_origin_count < (CASE NEW.lifecycle_status
            WHEN 'SOURCE_LOCAL_SUPPORTED' THEN 1 ELSE 2 END) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                CONSTRAINT = 'round3g_membership_promotion_evidence_ck',
                MESSAGE = 'membership promotion does not meet frozen source/support thresholds';
        END IF;
    END IF;
    RETURN NEW;
END
$enforce_round3g_membership_promotion$;

CREATE TRIGGER association_range_membership_round3g_promotion_bu
BEFORE UPDATE ON corpus.association_range_membership
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3g_membership_promotion();

CREATE FUNCTION audit.enforce_round3g_range_boundary()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_round3g_range_boundary$
BEGIN
    IF NEW.lifecycle_status IN (
        'BILINGUAL_REVIEWED', 'ACTIVE_FOR_CALIBRATION'
    ) THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = CASE NEW.lifecycle_status
                WHEN 'BILINGUAL_REVIEWED'
                    THEN 'round3g_bilingual_review_prohibited_ck'
                ELSE 'round3g_active_range_prohibited_ck'
            END,
            MESSAGE = 'Round 3G cannot establish this range lifecycle';
    END IF;
    IF TG_OP = 'INSERT' AND NEW.lifecycle_status <> 'REJECTED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_new_range_prohibited_ck',
            MESSAGE = 'Round 3G cannot add an association range';
    END IF;
    RETURN NEW;
END
$enforce_round3g_range_boundary$;

CREATE TRIGGER association_range_round3g_boundary_biu
BEFORE INSERT OR UPDATE ON corpus.association_range
FOR EACH ROW EXECUTE FUNCTION audit.enforce_round3g_range_boundary();

CREATE FUNCTION audit.prevent_round3g_model_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $prevent_round3g_model_run$
BEGIN
    IF lower(COALESCE(NEW.run_configuration ->> 'round', '')) IN (
        '3g', 'round3g'
    ) OR NEW.run_configuration ? 'round3g_evidence_snapshot'
      OR NEW.run_configuration ->> 'uses_round3g_evidence' = 'true' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            CONSTRAINT = 'round3g_model_run_prohibited_ck',
            MESSAGE = 'Round 3G evidence cannot be used in a model run';
    END IF;
    RETURN NEW;
END
$prevent_round3g_model_run$;

CREATE TRIGGER model_run_round3g_prohibited_biu
BEFORE INSERT OR UPDATE ON ml.model_run
FOR EACH ROW EXECUTE FUNCTION audit.prevent_round3g_model_run();

COMMIT;
