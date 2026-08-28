\set ON_ERROR_STOP on

-- Round 3M normalization challenges are governed label decisions, not generic
-- assertion-review markers.  This forward migration adds an actual-human
-- receipt for the existing Round 3K professional-label review chain and
-- replaces only the challenge metric.  It inserts no corpus or review rows.

BEGIN;

DO $round3m_existing_generic_challenge_credit_absent$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM audit.v_round3m_descriptor_gate_metrics
        WHERE reviewed_ambiguous_or_unresolved_challenge_count <> 0
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT =
                'round3m_normalization_challenge_historical_binding_ck',
            MESSAGE = 'pre-059 assertion-review challenge credit lacks a governed professional label-decision binding';
    END IF;
END
$round3m_existing_generic_challenge_credit_absent$;

-- One atomic Round 3K assertion can supply only one Round 3M assertion.  The
-- challenge metric is decision-deinflated as well, but this identity rule also
-- prevents the same bounded source assertion from entering other count
-- surfaces more than once through the compatibility bridge.
DO $round3m_existing_competition_assertion_links_unique$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM corpus.round3m_descriptor_assertion
        WHERE competition_descriptor_assertion_id IS NOT NULL
        GROUP BY competition_descriptor_assertion_id
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23505',
            CONSTRAINT =
                'round3m_competition_descriptor_assertion_link_uq',
            MESSAGE = 'one Round 3K descriptor assertion is linked to multiple Round 3M assertions';
    END IF;
END
$round3m_existing_competition_assertion_links_unique$;

CREATE UNIQUE INDEX round3m_competition_descriptor_assertion_link_uq
    ON corpus.round3m_descriptor_assertion (
        competition_descriptor_assertion_id
    )
    WHERE competition_descriptor_assertion_id IS NOT NULL;

-- The parent marker is written atomically by the first attestation.  Besides
-- making currentness explicit, the parent-row version change closes the
-- child-table phantom visible to a waiting REPEATABLE READ mutator.
ALTER TABLE corpus.professional_label_decision
    ADD COLUMN round3m_attested_review_set_sha256 TEXT,
    ADD CONSTRAINT round3m_attested_review_set_sha256_ck CHECK (
        round3m_attested_review_set_sha256 IS NULL
        OR round3m_attested_review_set_sha256 ~ '^[0-9a-f]{64}$'
    );

-- Migration 051 used UNIQUE NULLS NOT DISTINCT for both polymorphic target
-- columns.  That made a second concept target collide on its NULL range (and
-- vice versa), so the AMBIGUOUS/CONTRADICTORY cardinalities required by the
-- same migration were unrepresentable.  Partial unique indexes preserve the
-- intended per-kind identity without treating the inactive NULL arm as data.
ALTER TABLE corpus.professional_label_target
    DROP CONSTRAINT professional_label_target_decision_concept_uq,
    DROP CONSTRAINT professional_label_target_decision_range_uq;

CREATE UNIQUE INDEX professional_label_target_decision_concept_uq
    ON corpus.professional_label_target (
        professional_label_decision_id, concept_id
    )
    WHERE concept_id IS NOT NULL;

CREATE UNIQUE INDEX professional_label_target_decision_range_uq
    ON corpus.professional_label_target (
        professional_label_decision_id, association_range_id
    )
    WHERE association_range_id IS NOT NULL;

-- The digest uses governed keys rather than generated IDs for rebuild-stable
-- semantics.  It binds the complete expression -> Round 3K assertion ->
-- snapshot/file/rights chain, the final decision lineage and timestamps, and
-- the ordered target mapping (including the empty set for UNRESOLVED).
CREATE FUNCTION audit.round3m_professional_label_decision_payload_sha256(
    professional_label_decision_id_value BIGINT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_label_decision_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    (
    jsonb_build_object(
        'professional_expression_key',
            expression.professional_expression_key,
        'descriptor_assertion_key',
            source_assertion.descriptor_assertion_key,
        'preparation_service_key', preparation_service.preparation_service_key,
        'assertion_type_code', source_assertion.assertion_type_code,
        'evidence_tier_code', source_assertion.evidence_tier_code,
        'raw_phrase_sha256', source_assertion.raw_phrase_sha256,
        'assertion_source_locator', source_assertion.source_locator,
        'judge_observation_key', judge_observation.judge_observation_key,
        'judge_observation_source_key',
            judge_observation.source_observation_key,
        'judge_observation_source_locator', judge_observation.source_locator,
        'panel_key', panel.panel_key,
        'organizer_published_note_key',
            organizer_note.organizer_published_note_key,
        'organizer_note_role_code', organizer_note.note_role_code,
        'organizer_note_raw_text_sha256', organizer_note.raw_text_sha256,
        'organizer_note_source_locator', organizer_note.source_locator,
        'competition_descriptor_assertion_row',
            to_jsonb(source_assertion) - ARRAY[
                'descriptor_assertion_id', 'preparation_service_id',
                'judge_observation_id', 'panel_id', 'structured_score_id',
                'competitor_declared_note_id',
                'organizer_published_note_id',
                'professional_source_snapshot_id',
                'professional_source_file_id'
            ],
        'preparation_service_context', jsonb_build_object(
            'series_key', series.series_key,
            'edition_key', edition.edition_key,
            'edition_year', edition.edition_year,
            'category_key', category.category_key,
            'round_key', round_record.round_key,
            'entry_key', entry_record.entry_key,
            'lot_key', lot.lot_key,
            'rule_version_key', rule_version.rule_version_key,
            'service_row', to_jsonb(preparation_service) - ARRAY[
                'preparation_service_id', 'series_id', 'edition_id',
                'category_id', 'round_id', 'entry_id', 'lot_id',
                'repeat_of_preparation_service_id', 'rule_version_id',
                'scoresheet_version_id', 'roast_batch_id',
                'c0_preparation_concept_id',
                'reviewed_c1_roast_category_id', 'created_at'
            ]
        ),
        'judge_observation_row', CASE
            WHEN judge_observation.judge_observation_id IS NULL THEN NULL
            ELSE (to_jsonb(judge_observation) - ARRAY[
                'judge_observation_id', 'preparation_service_id',
                'panel_id', 'judge_id',
                'professional_source_snapshot_id',
                'professional_source_file_id'
            ]) || jsonb_build_object(
                'judge_key', judge_record.judge_key,
                'panel_key', observation_panel.panel_key,
                'professional_source_file_key',
                    observation_file.professional_source_file_key,
                'professional_source_snapshot_key',
                    observation_snapshot.professional_source_snapshot_key
            )
        END,
        'panel_row', CASE
            WHEN panel.panel_id IS NULL THEN NULL
            ELSE (to_jsonb(panel) - ARRAY[
                'panel_id', 'series_id', 'edition_id', 'category_id',
                'round_id', 'professional_source_snapshot_id'
            ]) || jsonb_build_object(
                'series_key', panel_series.series_key,
                'edition_key', panel_edition.edition_key,
                'category_key', panel_category.category_key,
                'round_key', panel_round.round_key,
                'professional_source_snapshot_key',
                    panel_snapshot.professional_source_snapshot_key
            )
        END,
        'organizer_note_row', CASE
            WHEN organizer_note.organizer_published_note_id IS NULL THEN NULL
            ELSE (to_jsonb(organizer_note) - ARRAY[
                'organizer_published_note_id', 'preparation_service_id',
                'edition_id', 'professional_source_snapshot_id',
                'professional_source_file_id'
            ]) || jsonb_build_object(
                'preparation_service_key',
                    note_service.preparation_service_key,
                'edition_key', note_edition.edition_key,
                'professional_source_snapshot_key',
                    note_snapshot.professional_source_snapshot_key,
                'professional_source_file_key',
                    note_file.professional_source_file_key
            )
        END,
        'descriptor_assertion_judge_lineage', coalesce((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'lineage_role_code', lineage.lineage_role_code,
                    'judge_observation_key',
                        lineage_observation.judge_observation_key,
                    'preparation_service_key',
                        lineage_service.preparation_service_key,
                    'panel_key', lineage_panel.panel_key,
                    'judge_key', lineage_judge.judge_key,
                    'observation_type_code',
                        lineage_observation.observation_type_code,
                    'official_confirmed',
                        lineage_observation.official_confirmed,
                    'professional_source_snapshot_key',
                        lineage_snapshot.professional_source_snapshot_key,
                    'professional_source_file_key',
                        lineage_file.professional_source_file_key,
                    'source_observation_key',
                        lineage_observation.source_observation_key,
                    'source_locator', lineage_observation.source_locator,
                    'observation_metadata',
                        lineage_observation.observation_metadata
                )
                ORDER BY lineage_observation.judge_observation_key,
                         lineage.lineage_role_code
            )
            FROM competition.descriptor_assertion_judge_lineage AS lineage
            JOIN competition.judge_observation AS lineage_observation
              ON lineage_observation.judge_observation_id =
                 lineage.judge_observation_id
            JOIN competition.preparation_service AS lineage_service
              ON lineage_service.preparation_service_id =
                 lineage_observation.preparation_service_id
            JOIN competition.panel AS lineage_panel
              ON lineage_panel.panel_id = lineage_observation.panel_id
            LEFT JOIN competition.judge AS lineage_judge
              ON lineage_judge.judge_id = lineage_observation.judge_id
            JOIN evidence.professional_source_snapshot AS lineage_snapshot
              ON lineage_snapshot.professional_source_snapshot_id =
                 lineage_observation.professional_source_snapshot_id
            LEFT JOIN evidence.professional_source_file AS lineage_file
              ON lineage_file.professional_source_file_id =
                 lineage_observation.professional_source_file_id
            WHERE lineage.descriptor_assertion_id =
                  source_assertion.descriptor_assertion_id
        ), '[]'::jsonb),
        'professional_source_snapshot_key',
            source_snapshot.professional_source_snapshot_key,
        'snapshot_sha256', source_snapshot.snapshot_sha256,
        'snapshot_immutable_locator', source_snapshot.immutable_locator,
        'snapshot_admitted', source_snapshot.admitted,
        'snapshot_lawfully_acquired_for_internal_research',
            source_snapshot.lawfully_acquired_for_internal_research,
        'professional_source_key', source.professional_source_key,
        'professional_source_admitted', source.admitted,
        'source_family_key', source.source_family_key,
        'source_family_canonical_origin_key',
            source_family.canonical_origin_key,
        'source_family_counts_as_independent',
            source_family.counts_as_independent,
        'source_family_admitted', source_family.admitted,
        'source_family_mirror_of_source_family_key',
            source_family.mirror_of_source_family_key,
        'professional_source_file_key', source_file.professional_source_file_key,
        'source_file_verified_sha256', source_file.verified_sha256,
        'source_file_official_locator', source_file.official_locator,
        'source_file_hash_verified', source_file.hash_verified,
        'current_snapshot_rights', coalesce((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'professional_rights_decision_key',
                        rights.professional_rights_decision_key,
                    'public_descriptor_use', rights.public_descriptor_use,
                    'internal_research_use', rights.internal_research_use,
                    'model_research_use', rights.model_research_use,
                    'decision_authority_code', rights.decision_authority_code,
                    'evidence_basis', rights.evidence_basis,
                    'decided_on', rights.decided_on
                )
                ORDER BY rights.professional_rights_decision_key
            )
            FROM evidence.v_current_professional_rights_decision AS rights
            WHERE rights.professional_source_snapshot_id =
                  source_snapshot.professional_source_snapshot_id
        ), '[]'::jsonb)
    ) || jsonb_build_object(
        'snapshot_privacy_decision', coalesce((
            SELECT jsonb_build_object(
                'professional_privacy_decision_key',
                    privacy.professional_privacy_decision_key,
                'personal_data_scope_code', privacy.personal_data_scope_code,
                'direct_identifiers_retained',
                    privacy.direct_identifiers_retained,
                'judge_identity_treatment_code',
                    privacy.judge_identity_treatment_code,
                'processing_basis', privacy.processing_basis,
                'decision_state_code', privacy.decision_state_code,
                'decided_on', privacy.decided_on
            )
            FROM evidence.professional_privacy_decision AS privacy
            WHERE privacy.professional_source_snapshot_id =
                  source_snapshot.professional_source_snapshot_id
        ), 'null'::jsonb),
        'snapshot_duplicate_memberships', coalesce((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'professional_duplicate_group_key',
                        duplicate_group.professional_duplicate_group_key,
                    'duplicate_type_code',
                        duplicate_group.duplicate_type_code,
                    'decision_basis_code',
                        duplicate_group.decision_basis_code,
                    'reviewed', duplicate_group.reviewed,
                    'member_ordinal', member.member_ordinal,
                    'member_role_code', member.member_role_code
                )
                ORDER BY duplicate_group.professional_duplicate_group_key,
                         member.member_ordinal
            )
            FROM audit.professional_duplicate_group_member AS member
            JOIN audit.professional_duplicate_group AS duplicate_group
              ON duplicate_group.professional_duplicate_group_id =
                 member.professional_duplicate_group_id
            WHERE member.professional_source_snapshot_id =
                  source_snapshot.professional_source_snapshot_id
        ), '[]'::jsonb),
        'language_tag', expression.language_tag,
        'normalized_phrase', expression.normalized_phrase,
        'normalization_rule_code', expression.normalization_rule_code,
        'source_span_start', expression.source_span_start,
        'source_span_end', expression.source_span_end,
        'expression_created_at_utc', to_char(
            expression.created_at AT TIME ZONE 'UTC',
            'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
        ),
        'professional_label_decision_key',
            decision.professional_label_decision_key,
        'decision_version', decision.decision_version,
        'supersedes_decision_key', predecessor.professional_label_decision_key,
        'label_disposition_code', decision.label_disposition_code,
        'decision_method_code', decision.decision_method_code,
        'independent_qualified_reviewer_count',
            decision.independent_qualified_reviewer_count,
        'adjudicator_present', decision.adjudicator_present,
        'expert_review_complete', decision.expert_review_complete,
        'candidate_only', decision.candidate_only,
        'decision_status_code', decision.decision_status_code,
        'provenance_complete', decision.provenance_complete,
        'decision_basis', decision.decision_basis,
        'decided_at_utc', to_char(
            decision.decided_at AT TIME ZONE 'UTC',
            'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
        ),
        'predecessor_chain', coalesce((
            WITH RECURSIVE ancestor AS (
                SELECT prior.*
                FROM corpus.professional_label_decision AS prior
                WHERE prior.professional_label_decision_id =
                      decision.supersedes_decision_id
                UNION ALL
                SELECT prior.*
                FROM ancestor AS child
                JOIN corpus.professional_label_decision AS prior
                  ON prior.professional_label_decision_id =
                     child.supersedes_decision_id
            )
            SELECT jsonb_agg(
                (to_jsonb(ancestor) - ARRAY[
                    'professional_label_decision_id',
                    'professional_expression_id', 'supersedes_decision_id',
                    'professional_mapping_rule_id',
                    'round3m_attested_review_set_sha256'
                ]) || jsonb_build_object(
                    'professional_expression_key',
                        ancestor_expression.professional_expression_key,
                    'supersedes_decision_key',
                        ancestor_predecessor.professional_label_decision_key,
                    'targets', coalesce((
                        SELECT jsonb_agg(
                            jsonb_build_object(
                                'target_ordinal', target.target_ordinal,
                                'target_role_code', target.target_role_code,
                                'concept_key', concept.concept_key,
                                'concept_lifecycle_status_code',
                                    concept.lifecycle_status_code,
                                'replacement_concept_key',
                                    replacement.concept_key,
                                'association_range_key', range_record.range_key
                            ) ORDER BY target.target_ordinal
                        )
                        FROM corpus.professional_label_target AS target
                        LEFT JOIN kb.concept AS concept
                          ON concept.concept_id = target.concept_id
                        LEFT JOIN kb.concept AS replacement
                          ON replacement.concept_id =
                             concept.replacement_concept_id
                        LEFT JOIN corpus.association_range AS range_record
                          ON range_record.association_range_id =
                             target.association_range_id
                        WHERE target.professional_label_decision_id =
                              ancestor.professional_label_decision_id
                    ), '[]'::jsonb)
                )
                ORDER BY ancestor.decision_version
            )
            FROM ancestor
            JOIN corpus.professional_expression AS ancestor_expression
              ON ancestor_expression.professional_expression_id =
                 ancestor.professional_expression_id
            LEFT JOIN corpus.professional_label_decision AS
                      ancestor_predecessor
              ON ancestor_predecessor.professional_label_decision_id =
                 ancestor.supersedes_decision_id
        ), '[]'::jsonb),
        'targets', coalesce((
            SELECT jsonb_agg(
                jsonb_build_object(
                    'target_ordinal', target.target_ordinal,
                    'target_role_code', target.target_role_code,
                    'concept_key', concept.concept_key,
                    'concept_lifecycle_status_code',
                        concept.lifecycle_status_code,
                    'replacement_concept_key', replacement.concept_key,
                    'association_range_key', association_range.range_key
                )
                ORDER BY target.target_ordinal
            )
            FROM corpus.professional_label_target AS target
            LEFT JOIN kb.concept AS concept
              ON concept.concept_id = target.concept_id
            LEFT JOIN kb.concept AS replacement
              ON replacement.concept_id = concept.replacement_concept_id
            LEFT JOIN corpus.association_range AS association_range
              ON association_range.association_range_id =
                 target.association_range_id
            WHERE target.professional_label_decision_id =
                  decision.professional_label_decision_id
        ), '[]'::jsonb)
    ))::TEXT
)
FROM corpus.professional_label_decision AS decision
JOIN corpus.professional_expression AS expression
  ON expression.professional_expression_id =
     decision.professional_expression_id
JOIN competition.descriptor_assertion AS source_assertion
  ON source_assertion.descriptor_assertion_id =
     expression.descriptor_assertion_id
JOIN competition.preparation_service AS preparation_service
  ON preparation_service.preparation_service_id =
     source_assertion.preparation_service_id
JOIN competition.series AS series
  ON series.series_id = preparation_service.series_id
JOIN competition.edition AS edition
  ON edition.edition_id = preparation_service.edition_id
JOIN competition.category AS category
  ON category.category_id = preparation_service.category_id
JOIN competition.round AS round_record
  ON round_record.round_id = preparation_service.round_id
LEFT JOIN competition.entry AS entry_record
  ON entry_record.entry_id = preparation_service.entry_id
LEFT JOIN competition.lot AS lot
  ON lot.lot_id = preparation_service.lot_id
JOIN competition.rule_version AS rule_version
  ON rule_version.rule_version_id = preparation_service.rule_version_id
LEFT JOIN competition.judge_observation AS judge_observation
  ON judge_observation.judge_observation_id =
     source_assertion.judge_observation_id
LEFT JOIN competition.panel AS panel
  ON panel.panel_id = source_assertion.panel_id
LEFT JOIN competition.judge AS judge_record
  ON judge_record.judge_id = judge_observation.judge_id
LEFT JOIN competition.panel AS observation_panel
  ON observation_panel.panel_id = judge_observation.panel_id
LEFT JOIN evidence.professional_source_snapshot AS observation_snapshot
  ON observation_snapshot.professional_source_snapshot_id =
     judge_observation.professional_source_snapshot_id
LEFT JOIN evidence.professional_source_file AS observation_file
  ON observation_file.professional_source_file_id =
     judge_observation.professional_source_file_id
LEFT JOIN competition.series AS panel_series
  ON panel_series.series_id = panel.series_id
LEFT JOIN competition.edition AS panel_edition
  ON panel_edition.edition_id = panel.edition_id
LEFT JOIN competition.category AS panel_category
  ON panel_category.category_id = panel.category_id
LEFT JOIN competition.round AS panel_round
  ON panel_round.round_id = panel.round_id
LEFT JOIN evidence.professional_source_snapshot AS panel_snapshot
  ON panel_snapshot.professional_source_snapshot_id =
     panel.professional_source_snapshot_id
LEFT JOIN competition.organizer_published_note AS organizer_note
  ON organizer_note.organizer_published_note_id =
     source_assertion.organizer_published_note_id
LEFT JOIN competition.preparation_service AS note_service
  ON note_service.preparation_service_id =
     organizer_note.preparation_service_id
LEFT JOIN competition.edition AS note_edition
  ON note_edition.edition_id = organizer_note.edition_id
LEFT JOIN evidence.professional_source_snapshot AS note_snapshot
  ON note_snapshot.professional_source_snapshot_id =
     organizer_note.professional_source_snapshot_id
LEFT JOIN evidence.professional_source_file AS note_file
  ON note_file.professional_source_file_id =
     organizer_note.professional_source_file_id
JOIN evidence.professional_source_snapshot AS source_snapshot
  ON source_snapshot.professional_source_snapshot_id =
     source_assertion.professional_source_snapshot_id
JOIN evidence.professional_source AS source
  ON source.professional_source_id = source_snapshot.professional_source_id
JOIN evidence.source_family AS source_family
  ON source_family.source_family_key = source_snapshot.source_family_key
LEFT JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_file_id =
     source_assertion.professional_source_file_id
 AND source_file.professional_source_snapshot_id =
     source_assertion.professional_source_snapshot_id
LEFT JOIN corpus.professional_label_decision AS predecessor
  ON predecessor.professional_label_decision_id =
     decision.supersedes_decision_id
WHERE decision.professional_label_decision_id =
      professional_label_decision_id_value
$round3m_professional_label_decision_payload_sha256$;

CREATE FUNCTION audit.round3m_professional_label_review_payload_sha256(
    professional_label_review_id_value BIGINT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_label_review_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    jsonb_build_object(
        'decision_payload_sha256',
            audit.round3m_professional_label_decision_payload_sha256(
                review.professional_label_decision_id
            ),
        'reviewer_key', reviewer.reviewer_key,
        'reviewer_role_code', review.reviewer_role_code,
        'review_outcome_code', review.review_outcome_code,
        'review_evidence', review.review_evidence,
        'reviewed_at_utc', to_char(
            review.reviewed_at AT TIME ZONE 'UTC',
            'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
        )
    )::TEXT
)
FROM audit.professional_label_review AS review
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_id = review.reviewer_id
WHERE review.professional_label_review_id =
      professional_label_review_id_value
$round3m_professional_label_review_payload_sha256$;

-- Pseudonymous reviewer rows are not themselves evidence that distinct humans
-- participated.  This imported identity receipt binds exactly one reviewer to
-- one canonical, non-PII identity digest and the hash/locator of the source
-- evidence used to establish that identity.
CREATE TABLE audit.round3m_human_reviewer_identity_receipt (
    reviewer_identity_receipt_key TEXT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    canonical_human_identity_sha256 TEXT NOT NULL,
    identity_evidence_sha256 TEXT NOT NULL,
    receipt_origin_code TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_human_reviewer_identity_receipt_pk PRIMARY KEY (
        reviewer_identity_receipt_key
    ),
    CONSTRAINT round3m_human_reviewer_identity_reviewer_uq UNIQUE (
        reviewer_id
    ),
    CONSTRAINT round3m_human_reviewer_identity_digest_uq UNIQUE (
        canonical_human_identity_sha256
    ),
    CONSTRAINT round3m_human_reviewer_identity_reviewer_fk FOREIGN KEY (
        reviewer_id
    ) REFERENCES audit.reviewer (reviewer_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_human_reviewer_identity_receipt_text_ck CHECK (
        reviewer_identity_receipt_key =
            lower(btrim(reviewer_identity_receipt_key))
        AND reviewer_identity_receipt_key ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND canonical_human_identity_sha256 ~ '^[0-9a-f]{64}$'
        AND identity_evidence_sha256 ~ '^[0-9a-f]{64}$'
        AND receipt_origin_code IN (
            'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
        )
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
    )
);

CREATE FUNCTION audit.validate_round3m_human_reviewer_identity_receipt()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_human_reviewer_identity_receipt$
BEGIN
    IF NEW.created_at IS DISTINCT FROM transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_human_reviewer_identity_import_time_ck',
            MESSAGE = 'reviewer identity receipt created_at is the immutable database import time';
    END IF;

    RETURN NEW;
END
$validate_round3m_human_reviewer_identity_receipt$;

CREATE TRIGGER round3m_human_reviewer_identity_receipt_bi
BEFORE INSERT ON audit.round3m_human_reviewer_identity_receipt
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_human_reviewer_identity_receipt();

CREATE TRIGGER round3m_human_reviewer_identity_receipt_bud
BEFORE UPDATE OR DELETE
ON audit.round3m_human_reviewer_identity_receipt
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE FUNCTION audit.round3m_human_review_event_member_sha256(
    professional_label_review_id_value BIGINT,
    human_event_evidence_sha256_value TEXT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_human_review_event_member_sha256$
SELECT audit.round3i_utf8_sha256(
    jsonb_build_object(
        'reviewer_identity_receipt_key',
            identity.reviewer_identity_receipt_key,
        'canonical_human_identity_sha256',
            identity.canonical_human_identity_sha256,
        'identity_evidence_sha256', identity.identity_evidence_sha256,
        'human_event_evidence_sha256',
            human_event_evidence_sha256_value,
        'review_payload_sha256',
            audit.round3m_professional_label_review_payload_sha256(
                review.professional_label_review_id
            )
    )::TEXT
)
FROM audit.professional_label_review AS review
JOIN audit.round3m_human_reviewer_identity_receipt AS identity
  ON identity.reviewer_id = review.reviewer_id
WHERE review.professional_label_review_id =
      professional_label_review_id_value
$round3m_human_review_event_member_sha256$;

-- One digest freezes the complete decision-level reviewer set.  A separate
-- identity/qualification digest makes reviewer independence and the exact
-- qualifications consulted by this migration auditable.  Migration 058, if
-- separately authorized, adds the stronger dated qualification-receipt and
-- admission contract; these digests never manufacture historical evidence.
CREATE FUNCTION audit.round3m_professional_label_review_set_sha256(
    professional_label_decision_id_value BIGINT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_label_review_set_sha256$
SELECT audit.round3i_utf8_sha256(
    jsonb_build_object(
        'decision_payload_sha256',
            audit.round3m_professional_label_decision_payload_sha256(
                professional_label_decision_id_value
            ),
        'reviews', coalesce((
            SELECT jsonb_agg(
                audit.round3m_professional_label_review_payload_sha256(
                    review.professional_label_review_id
                )
                ORDER BY reviewer.reviewer_key
            )
            FROM audit.professional_label_review AS review
            JOIN audit.reviewer AS reviewer
              ON reviewer.reviewer_id = review.reviewer_id
            WHERE review.professional_label_decision_id =
                  professional_label_decision_id_value
        ), '[]'::jsonb)
    )::TEXT
)
$round3m_professional_label_review_set_sha256$;

CREATE FUNCTION audit.round3m_professional_reviewer_independence_set_sha256(
    professional_label_decision_id_value BIGINT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_reviewer_independence_set_sha256$
SELECT audit.round3i_utf8_sha256(
    coalesce(jsonb_agg(
        jsonb_build_object(
            'reviewer_key', reviewer.reviewer_key,
            'display_name', reviewer.display_name,
            'affiliation', reviewer.affiliation,
            'reviewer_role_code', review.reviewer_role_code,
            'reviewer_identity_receipt', CASE
                WHEN identity.reviewer_id IS NULL THEN NULL
                ELSE jsonb_build_object(
                    'reviewer_identity_receipt_key',
                        identity.reviewer_identity_receipt_key,
                    'canonical_human_identity_sha256',
                        identity.canonical_human_identity_sha256,
                    'identity_evidence_sha256',
                        identity.identity_evidence_sha256,
                    'receipt_origin_code', identity.receipt_origin_code,
                    'evidence_locator', identity.evidence_locator,
                    'created_at_utc', to_char(
                        identity.created_at AT TIME ZONE 'UTC',
                        'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
                    )
                )
            END,
            'qualifications', coalesce((
                SELECT jsonb_agg(
                    jsonb_build_object(
                        'qualification_scope_code',
                            qualification.qualification_scope_code,
                        'source_language_tag',
                            qualification.source_language_tag,
                        'qualification_evidence',
                            qualification.qualification_evidence,
                        'verified_on', qualification.verified_on,
                        'eligible', qualification.eligible
                    )
                    ORDER BY qualification.qualification_scope_code,
                             qualification.source_language_tag NULLS FIRST
                )
                FROM audit.professional_reviewer_qualification AS qualification
                WHERE qualification.reviewer_id = reviewer.reviewer_id
            ), '[]'::jsonb)
        )
        ORDER BY reviewer.reviewer_key
    ), '[]'::jsonb)::TEXT
)
FROM audit.professional_label_review AS review
JOIN audit.reviewer AS reviewer
  ON reviewer.reviewer_id = review.reviewer_id
LEFT JOIN audit.round3m_human_reviewer_identity_receipt AS identity
  ON identity.reviewer_id = reviewer.reviewer_id
WHERE review.professional_label_decision_id =
      professional_label_decision_id_value
$round3m_professional_reviewer_independence_set_sha256$;

CREATE FUNCTION audit.round3m_professional_label_lineage_is_valid(
    professional_label_decision_id_value BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_label_lineage_is_valid$
WITH RECURSIVE ancestry AS (
    SELECT
        decision.professional_label_decision_id,
        decision.professional_expression_id,
        decision.decision_version,
        decision.supersedes_decision_id,
        decision.decided_at
    FROM corpus.professional_label_decision AS decision
    WHERE decision.professional_label_decision_id =
          professional_label_decision_id_value
    UNION
    SELECT
        predecessor.professional_label_decision_id,
        predecessor.professional_expression_id,
        predecessor.decision_version,
        predecessor.supersedes_decision_id,
        predecessor.decided_at
    FROM ancestry AS child
    JOIN corpus.professional_label_decision AS predecessor
      ON predecessor.professional_label_decision_id =
         child.supersedes_decision_id
), stats AS (
    SELECT
        count(*)::BIGINT AS chain_length,
        min(decision_version) AS minimum_version,
        max(decision_version) AS maximum_version,
        count(*) FILTER (
            WHERE supersedes_decision_id IS NULL
        )::BIGINT AS root_count,
        count(DISTINCT professional_expression_id)::BIGINT AS expression_count
    FROM ancestry
), broken_link AS (
    SELECT count(*)::BIGINT AS value
    FROM ancestry AS child
    LEFT JOIN ancestry AS predecessor
      ON predecessor.professional_label_decision_id =
         child.supersedes_decision_id
    WHERE child.supersedes_decision_id IS NOT NULL
      AND (
          predecessor.professional_label_decision_id IS NULL
          OR predecessor.professional_expression_id IS DISTINCT FROM
             child.professional_expression_id
          OR predecessor.decision_version <> child.decision_version - 1
          OR predecessor.decided_at > child.decided_at
      )
)
SELECT stats.chain_length > 0
   AND stats.minimum_version = 1
   AND stats.maximum_version = stats.chain_length
   AND stats.root_count = 1
   AND stats.expression_count = 1
   AND broken_link.value = 0
FROM stats
CROSS JOIN broken_link
$round3m_professional_label_lineage_is_valid$;

CREATE TABLE audit.round3m_professional_label_review_attestation (
    professional_label_review_id BIGINT NOT NULL,
    attestation_key TEXT NOT NULL,
    review_actor_type TEXT NOT NULL,
    receipt_origin_code TEXT NOT NULL,
    reviewer_id_or_pseudonymous_code TEXT NOT NULL,
    reviewer_identity_receipt_key TEXT NOT NULL,
    human_event_evidence_sha256 TEXT NOT NULL,
    human_event_member_sha256 TEXT NOT NULL,
    review_payload_sha256 TEXT NOT NULL,
    decision_review_set_sha256 TEXT NOT NULL,
    reviewer_independence_set_sha256 TEXT NOT NULL,
    evidence_locator TEXT NOT NULL,
    independence_evidence_locator TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_prof_label_review_attestation_pk PRIMARY KEY (
        professional_label_review_id
    ),
    CONSTRAINT round3m_prof_label_review_attestation_key_uq UNIQUE (
        attestation_key
    ),
    CONSTRAINT round3m_prof_label_review_attestation_member_uq UNIQUE (
        human_event_member_sha256
    ),
    CONSTRAINT round3m_prof_label_review_attestation_review_fk FOREIGN KEY (
        professional_label_review_id
    ) REFERENCES audit.professional_label_review (
        professional_label_review_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_prof_label_review_attestation_identity_fk FOREIGN KEY (
        reviewer_identity_receipt_key
    ) REFERENCES audit.round3m_human_reviewer_identity_receipt (
        reviewer_identity_receipt_key
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_prof_label_review_attestation_text_ck CHECK (
        attestation_key = lower(btrim(attestation_key))
        AND attestation_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND reviewer_id_or_pseudonymous_code =
            btrim(reviewer_id_or_pseudonymous_code)
        AND reviewer_id_or_pseudonymous_code <> ''
        AND lower(reviewer_id_or_pseudonymous_code)
            !~ '(^|[._ -])codex($|[._ -])'
        AND reviewer_identity_receipt_key =
            lower(btrim(reviewer_identity_receipt_key))
        AND reviewer_identity_receipt_key ~
            '^[a-z0-9][a-z0-9._:/-]*$'
        AND human_event_evidence_sha256 ~ '^[0-9a-f]{64}$'
        AND human_event_member_sha256 ~ '^[0-9a-f]{64}$'
        AND review_payload_sha256 ~ '^[0-9a-f]{64}$'
        AND decision_review_set_sha256 ~ '^[0-9a-f]{64}$'
        AND reviewer_independence_set_sha256 ~ '^[0-9a-f]{64}$'
        AND evidence_locator = btrim(evidence_locator)
        AND evidence_locator <> ''
        AND independence_evidence_locator =
            btrim(independence_evidence_locator)
        AND independence_evidence_locator <> ''
    ),
    CONSTRAINT round3m_prof_label_review_attestation_values_ck CHECK (
        review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
        AND receipt_origin_code IN (
            'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
        )
    )
);

CREATE FUNCTION audit.validate_round3m_prof_label_review_attestation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_prof_label_review_attestation$
DECLARE
    selected_decision_id BIGINT;
    selected_review audit.professional_label_review%ROWTYPE;
    selected_decision corpus.professional_label_decision%ROWTYPE;
    selected_reviewer audit.reviewer%ROWTYPE;
    selected_identity audit.round3m_human_reviewer_identity_receipt%ROWTYPE;
    selected_expression corpus.professional_expression%ROWTYPE;
BEGIN
    SELECT professional_label_decision_id INTO STRICT selected_decision_id
    FROM audit.professional_label_review
    WHERE professional_label_review_id =
          NEW.professional_label_review_id;

    SELECT * INTO STRICT selected_decision
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id =
          selected_decision_id
    FOR UPDATE;

    SELECT * INTO STRICT selected_review
    FROM audit.professional_label_review
    WHERE professional_label_review_id =
          NEW.professional_label_review_id
    FOR UPDATE;

    IF selected_review.professional_label_decision_id IS DISTINCT FROM
       selected_decision.professional_label_decision_id THEN
        RAISE EXCEPTION USING
            ERRCODE = '40001',
            MESSAGE = 'professional label review changed decisions while its attestation was being created';
    END IF;

    SELECT * INTO STRICT selected_expression
    FROM corpus.professional_expression
    WHERE professional_expression_id =
          selected_decision.professional_expression_id
    FOR UPDATE;

    SELECT * INTO STRICT selected_reviewer
    FROM audit.reviewer
    WHERE reviewer_id = selected_review.reviewer_id
    FOR UPDATE;

    SELECT * INTO STRICT selected_identity
    FROM audit.round3m_human_reviewer_identity_receipt
    WHERE reviewer_identity_receipt_key =
          NEW.reviewer_identity_receipt_key
    FOR UPDATE;

    IF selected_review.review_outcome_code <> 'ACCEPT'
       OR selected_review.reviewed_at > selected_decision.decided_at
       OR selected_review.reviewed_at > transaction_timestamp()
       OR selected_decision.decided_at > transaction_timestamp()
       OR NEW.created_at < selected_decision.decided_at
       OR NEW.created_at IS DISTINCT FROM transaction_timestamp()
       OR selected_decision.decision_method_code <> 'QUALIFIED_REVIEW'
       OR selected_decision.decision_status_code <> 'FINAL'
       OR selected_decision.candidate_only
       OR NOT selected_decision.provenance_complete
       OR NOT audit.round3m_professional_label_lineage_is_valid(
              selected_decision.professional_label_decision_id
          )
       OR NEW.reviewer_id_or_pseudonymous_code IS DISTINCT FROM
          selected_reviewer.reviewer_key
       OR selected_identity.reviewer_id IS DISTINCT FROM
          selected_reviewer.reviewer_id
       OR selected_identity.created_at > NEW.created_at
       OR NEW.human_event_member_sha256 IS DISTINCT FROM
          audit.round3m_human_review_event_member_sha256(
              NEW.professional_label_review_id,
              NEW.human_event_evidence_sha256
          )
       OR selected_review.reviewer_role_code = 'ADJUDICATOR'
          AND NEW.review_actor_type <> 'EXPERT_REVIEWER'
       OR NEW.review_payload_sha256 IS DISTINCT FROM
          audit.round3m_professional_label_review_payload_sha256(
              NEW.professional_label_review_id
          )
       OR NEW.decision_review_set_sha256 IS DISTINCT FROM
          audit.round3m_professional_label_review_set_sha256(
              selected_decision.professional_label_decision_id
          )
       OR NEW.reviewer_independence_set_sha256 IS DISTINCT FROM
          audit.round3m_professional_reviewer_independence_set_sha256(
              selected_decision.professional_label_decision_id
          )
       OR selected_decision.round3m_attested_review_set_sha256 IS NOT NULL
          AND selected_decision.round3m_attested_review_set_sha256 IS DISTINCT
              FROM NEW.decision_review_set_sha256 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT =
                'round3m_prof_label_review_human_attestation_ck',
            MESSAGE = 'professional label attestation must bind the exact canonical human identity/event member, all-ACCEPT review set, nonfuture chronology, independence set, and final qualified-review payload',
            DETAIL = format(
                'outcome=%s reviewer_identity_match=%s review_payload_match=%s review_set_match=%s independence_set_match=%s review_at=%s decision_at=%s receipt_at=%s transaction_at=%s',
                selected_review.review_outcome_code,
                NEW.reviewer_id_or_pseudonymous_code IS NOT DISTINCT FROM
                    selected_reviewer.reviewer_key,
                NEW.review_payload_sha256 IS NOT DISTINCT FROM
                    audit.round3m_professional_label_review_payload_sha256(
                        NEW.professional_label_review_id
                    ),
                NEW.decision_review_set_sha256 IS NOT DISTINCT FROM
                    audit.round3m_professional_label_review_set_sha256(
                        selected_decision.professional_label_decision_id
                    ),
                NEW.reviewer_independence_set_sha256 IS NOT DISTINCT FROM
                    audit.round3m_professional_reviewer_independence_set_sha256(
                        selected_decision.professional_label_decision_id
                    ),
                selected_review.reviewed_at,
                selected_decision.decided_at,
                NEW.created_at,
                transaction_timestamp()
            );
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM audit.professional_label_review AS review
        JOIN audit.round3m_professional_label_review_attestation AS attestation
          ON attestation.professional_label_review_id =
             review.professional_label_review_id
        WHERE review.reviewer_id = selected_reviewer.reviewer_id
    ) THEN
        UPDATE audit.reviewer
        SET display_name = display_name
        WHERE reviewer_id = selected_reviewer.reviewer_id;
    END IF;

    RETURN NEW;
END
$validate_round3m_prof_label_review_attestation$;

CREATE TRIGGER round3m_prof_label_review_attestation_bi
BEFORE INSERT ON audit.round3m_professional_label_review_attestation
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_prof_label_review_attestation();

CREATE FUNCTION audit.seal_round3m_prof_label_review_set()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $seal_round3m_prof_label_review_set$
DECLARE
    selected_decision_id BIGINT;
BEGIN
    SELECT professional_label_decision_id INTO STRICT selected_decision_id
    FROM audit.professional_label_review
    WHERE professional_label_review_id =
          NEW.professional_label_review_id;

    UPDATE corpus.professional_label_decision
    SET round3m_attested_review_set_sha256 =
            NEW.decision_review_set_sha256
    WHERE professional_label_decision_id = selected_decision_id
      AND round3m_attested_review_set_sha256 IS NULL;

    RETURN NEW;
END
$seal_round3m_prof_label_review_set$;

CREATE TRIGGER round3m_prof_label_review_attestation_ai
AFTER INSERT ON audit.round3m_professional_label_review_attestation
FOR EACH ROW EXECUTE FUNCTION
    audit.seal_round3m_prof_label_review_set();

CREATE TRIGGER round3m_prof_label_review_attestation_bud
BEFORE UPDATE OR DELETE
ON audit.round3m_professional_label_review_attestation
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

-- Freeze the complete review/decision/target/expression surface once its first
-- human attestation exists.  Corrections append a successor decision.
CREATE FUNCTION audit.protect_round3m_attested_prof_label_review_set()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_prof_label_review_set$
DECLARE
    affected_decision_id BIGINT;
    prior_decision_id BIGINT;
BEGIN
    affected_decision_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.professional_label_decision_id
        ELSE NEW.professional_label_decision_id
    END;
    prior_decision_id := CASE
        WHEN TG_OP = 'UPDATE' THEN OLD.professional_label_decision_id
        ELSE affected_decision_id
    END;

    PERFORM 1
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id IN (
        affected_decision_id, prior_decision_id
    )
    ORDER BY professional_label_decision_id
    FOR UPDATE;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS decision
        WHERE decision.professional_label_decision_id IN (
            affected_decision_id, prior_decision_id
        )
          AND decision.round3m_attested_review_set_sha256 IS NOT NULL
    ) OR EXISTS (
        SELECT 1
        FROM audit.professional_label_review AS locked_review
        JOIN audit.round3m_professional_label_review_attestation AS attestation
          ON attestation.professional_label_review_id =
             locked_review.professional_label_review_id
        WHERE locked_review.professional_label_decision_id IN (
            affected_decision_id, prior_decision_id
        )
    ) OR EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS successor
        WHERE successor.supersedes_decision_id IN (
            affected_decision_id, prior_decision_id
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_prof_label_review_set_immutable_ck',
            MESSAGE = 'an attested professional label review set is immutable; append a successor decision';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_prof_label_review_set$;

CREATE TRIGGER round3m_attested_prof_label_review_biud
BEFORE INSERT OR UPDATE OR DELETE ON audit.professional_label_review
FOR EACH ROW EXECUTE FUNCTION
    audit.protect_round3m_attested_prof_label_review_set();

CREATE FUNCTION audit.protect_round3m_attested_reviewer_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_reviewer_identity$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM audit.professional_label_review AS review
        JOIN audit.round3m_professional_label_review_attestation AS attestation
          ON attestation.professional_label_review_id =
             review.professional_label_review_id
        WHERE review.reviewer_id = OLD.reviewer_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_reviewer_identity_immutable_ck',
            MESSAGE = 'a reviewer identity used by an attested professional label decision is immutable';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_reviewer_identity$;

CREATE TRIGGER round3m_attested_reviewer_identity_bud
BEFORE UPDATE OR DELETE ON audit.reviewer
FOR EACH ROW EXECUTE FUNCTION
    audit.protect_round3m_attested_reviewer_identity();

-- Serialize successor creation with predecessor mutation and revalidate the
-- lineage after acquiring the predecessor row lock.  Once the successor is
-- visible, the mutation guard below closes the predecessor permanently.
CREATE FUNCTION corpus.lock_validate_round3m_prof_label_predecessor()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $lock_validate_round3m_prof_label_predecessor$
DECLARE
    predecessor corpus.professional_label_decision%ROWTYPE;
BEGIN
    IF NEW.supersedes_decision_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO STRICT predecessor
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id = NEW.supersedes_decision_id
    FOR UPDATE;

    IF predecessor.professional_expression_id IS DISTINCT FROM
       NEW.professional_expression_id
       OR predecessor.decision_version <> NEW.decision_version - 1
       OR predecessor.decided_at > NEW.decided_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_prof_label_decision_locked_lineage_ck',
            MESSAGE = 'a successor must retain the locked prior version, expression, and chronology';
    END IF;

    RETURN NEW;
END
$lock_validate_round3m_prof_label_predecessor$;

CREATE TRIGGER round3m_prof_label_predecessor_lock_biu
BEFORE INSERT OR UPDATE ON corpus.professional_label_decision
FOR EACH ROW EXECUTE FUNCTION
    corpus.lock_validate_round3m_prof_label_predecessor();

CREATE FUNCTION corpus.protect_round3m_attested_prof_label_decision()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_prof_label_decision$
BEGIN
    IF TG_OP = 'UPDATE'
       AND OLD.round3m_attested_review_set_sha256 IS NULL
       AND NEW.round3m_attested_review_set_sha256 IS NOT NULL
       AND (to_jsonb(NEW) - 'round3m_attested_review_set_sha256')
           IS NOT DISTINCT FROM
           (to_jsonb(OLD) - 'round3m_attested_review_set_sha256')
       AND NEW.round3m_attested_review_set_sha256 IS NOT DISTINCT FROM
           audit.round3m_professional_label_review_set_sha256(
               OLD.professional_label_decision_id
           )
       AND EXISTS (
            SELECT 1
            FROM audit.professional_label_review AS review
            JOIN audit.round3m_professional_label_review_attestation AS attestation
              ON attestation.professional_label_review_id =
                 review.professional_label_review_id
             AND attestation.decision_review_set_sha256 =
                 NEW.round3m_attested_review_set_sha256
            WHERE review.professional_label_decision_id =
                  OLD.professional_label_decision_id
       ) THEN
        RETURN NEW;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS successor
        WHERE successor.supersedes_decision_id =
              OLD.professional_label_decision_id
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_superseded_prof_label_decision_immutable_ck',
            MESSAGE = 'a superseded professional label decision is immutable';
    END IF;

    IF EXISTS (
        WITH RECURSIVE decision_chain AS (
            SELECT OLD.professional_label_decision_id AS
                       professional_label_decision_id,
                   OLD.supersedes_decision_id
            UNION
            SELECT neighbor.professional_label_decision_id,
                   neighbor.supersedes_decision_id
            FROM decision_chain AS chain
            CROSS JOIN LATERAL (
                SELECT predecessor.professional_label_decision_id,
                       predecessor.supersedes_decision_id
                FROM corpus.professional_label_decision AS predecessor
                WHERE predecessor.professional_label_decision_id =
                      chain.supersedes_decision_id
                UNION
                SELECT successor.professional_label_decision_id,
                       successor.supersedes_decision_id
                FROM corpus.professional_label_decision AS successor
                WHERE successor.supersedes_decision_id =
                      chain.professional_label_decision_id
            ) AS neighbor
        )
        SELECT chain.professional_label_decision_id
        FROM decision_chain AS chain
        LEFT JOIN corpus.professional_label_decision AS chain_decision
          ON chain_decision.professional_label_decision_id =
             chain.professional_label_decision_id
        LEFT JOIN audit.professional_label_review AS review
          ON review.professional_label_decision_id =
             chain.professional_label_decision_id
        LEFT JOIN audit.round3m_professional_label_review_attestation AS attestation
          ON attestation.professional_label_review_id =
             review.professional_label_review_id
        WHERE chain_decision.round3m_attested_review_set_sha256 IS NOT NULL
           OR attestation.professional_label_review_id IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_prof_label_decision_immutable_ck',
            MESSAGE = 'an attested professional label decision is immutable; append a successor decision';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_prof_label_decision$;

CREATE TRIGGER round3m_attested_prof_label_decision_bud
BEFORE UPDATE OR DELETE ON corpus.professional_label_decision
FOR EACH ROW EXECUTE FUNCTION
    corpus.protect_round3m_attested_prof_label_decision();

CREATE FUNCTION corpus.protect_round3m_attested_prof_label_target()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_prof_label_target$
DECLARE
    affected_decision_id BIGINT;
    prior_decision_id BIGINT;
BEGIN
    affected_decision_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.professional_label_decision_id
        ELSE NEW.professional_label_decision_id
    END;
    prior_decision_id := CASE
        WHEN TG_OP = 'UPDATE' THEN OLD.professional_label_decision_id
        ELSE affected_decision_id
    END;

    PERFORM 1
    FROM corpus.professional_label_decision
    WHERE professional_label_decision_id IN (
        affected_decision_id, prior_decision_id
    )
    ORDER BY professional_label_decision_id
    FOR UPDATE;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS decision
        WHERE decision.professional_label_decision_id IN (
            affected_decision_id, prior_decision_id
        )
          AND decision.round3m_attested_review_set_sha256 IS NOT NULL
    ) OR EXISTS (
        SELECT 1
        FROM audit.professional_label_review AS review
        JOIN audit.round3m_professional_label_review_attestation AS attestation
          ON attestation.professional_label_review_id =
             review.professional_label_review_id
        WHERE review.professional_label_decision_id IN (
            affected_decision_id, prior_decision_id
        )
    ) OR EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS successor
        WHERE successor.supersedes_decision_id IN (
            affected_decision_id, prior_decision_id
        )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_prof_label_target_immutable_ck',
            MESSAGE = 'targets of an attested professional label decision are immutable';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_prof_label_target$;

CREATE TRIGGER round3m_attested_prof_label_target_biud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.professional_label_target
FOR EACH ROW EXECUTE FUNCTION
    corpus.protect_round3m_attested_prof_label_target();

CREATE FUNCTION corpus.protect_round3m_attested_prof_expression()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_prof_expression$
BEGIN
    PERFORM 1
    FROM corpus.professional_label_decision
    WHERE professional_expression_id = OLD.professional_expression_id
    ORDER BY professional_label_decision_id
    FOR UPDATE;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS decision
        LEFT JOIN audit.professional_label_review AS review
          ON review.professional_label_decision_id =
             decision.professional_label_decision_id
        LEFT JOIN audit.round3m_professional_label_review_attestation AS attestation
          ON attestation.professional_label_review_id =
             review.professional_label_review_id
        WHERE decision.professional_expression_id =
              OLD.professional_expression_id
          AND (
              decision.round3m_attested_review_set_sha256 IS NOT NULL
              OR attestation.professional_label_review_id IS NOT NULL
          )
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_prof_expression_immutable_ck',
            MESSAGE = 'an expression used by an attested label decision is immutable';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_prof_expression$;

CREATE TRIGGER round3m_attested_prof_expression_bud
BEFORE UPDATE OR DELETE ON corpus.professional_expression
FOR EACH ROW EXECUTE FUNCTION
    corpus.protect_round3m_attested_prof_expression();

-- Challenge credit requires a byte-identical Round 3M artifact and Round 3K
-- source file, the same snapshot and record locator, and affirmative current
-- Round 3K research rights.  A shared phrase/service alone is insufficient.
CREATE VIEW corpus.v_round3m_round3k_exact_descriptor_source_binding AS
SELECT
    assertion.descriptor_assertion_id,
    assertion.competition_descriptor_assertion_id,
    assertion.source_artifact_id,
    artifact.professional_source_file_id,
    source_file.professional_source_snapshot_id,
    governed_snapshot.professional_rights_decision_id,
    source_file.verified_sha256 AS exact_source_file_sha256,
    source_file.official_locator AS exact_source_file_locator
FROM corpus.round3m_descriptor_assertion AS assertion
JOIN evidence.round3m_source_artifact AS artifact
  ON artifact.source_artifact_id = assertion.source_artifact_id
JOIN audit.round3m_descriptor_review_receipt AS descriptor_review_receipt
  ON descriptor_review_receipt.review_receipt_id =
     assertion.current_review_receipt_id
 AND descriptor_review_receipt.descriptor_assertion_id =
     assertion.descriptor_assertion_id
 AND descriptor_review_receipt.reviewed_at <= transaction_timestamp()
JOIN evidence.v_round3m_current_descriptor_rights AS round3m_rights
  ON round3m_rights.rights_decision_id = assertion.rights_decision_id
 AND round3m_rights.unambiguous_current_decision
 AND round3m_rights.decided_at <= transaction_timestamp()
JOIN competition.descriptor_assertion AS legacy_assertion
  ON legacy_assertion.descriptor_assertion_id =
     assertion.competition_descriptor_assertion_id
 AND legacy_assertion.preparation_service_id = assertion.preparation_service_id
 AND legacy_assertion.raw_phrase_sha256 = assertion.atomic_source_text_sha256
 AND legacy_assertion.raw_phrase_sha256 =
     assertion.source_native_lexical_form_sha256
 AND legacy_assertion.language_tag = assertion.source_language
 AND legacy_assertion.evidence_tier_code = assertion.evidence_tier
 AND legacy_assertion.professional_source_file_id =
     artifact.professional_source_file_id
 AND legacy_assertion.source_locator =
     assertion.source_page_or_record_locator
JOIN competition.preparation_service AS service
  ON service.preparation_service_id =
     legacy_assertion.preparation_service_id
 AND service.preparation_service_key = assertion.effective_record_key
JOIN competition.edition AS edition
  ON edition.edition_id = service.edition_id
 AND edition.edition_year = assertion.edition_year
LEFT JOIN competition.judge_observation AS observation
  ON observation.judge_observation_id = legacy_assertion.judge_observation_id
LEFT JOIN competition.panel AS assertion_panel
  ON assertion_panel.panel_id = legacy_assertion.panel_id
LEFT JOIN competition.organizer_published_note AS organizer_note
  ON organizer_note.organizer_published_note_id =
     legacy_assertion.organizer_published_note_id
JOIN evidence.professional_source_file AS source_file
  ON source_file.professional_source_file_id =
     artifact.professional_source_file_id
 AND source_file.professional_source_snapshot_id =
     legacy_assertion.professional_source_snapshot_id
 AND source_file.hash_verified
 AND source_file.verified_sha256 = artifact.source_file_sha256
 AND source_file.verified_sha256 = assertion.source_file_sha256
 AND source_file.official_locator = artifact.governed_locator
JOIN evidence.v_round3k_governed_professional_snapshot AS governed_snapshot
  ON governed_snapshot.professional_source_snapshot_id =
     source_file.professional_source_snapshot_id
 AND governed_snapshot.eligible_for_model_research
JOIN evidence.professional_source_snapshot AS exact_snapshot
  ON exact_snapshot.professional_source_snapshot_id =
     source_file.professional_source_snapshot_id
 AND exact_snapshot.retrieved_at <= transaction_timestamp()
JOIN evidence.v_current_professional_rights_decision AS current_rights
  ON current_rights.professional_rights_decision_id =
     governed_snapshot.professional_rights_decision_id
 AND current_rights.unambiguous_current_decision
 AND current_rights.decided_on <= current_date
JOIN evidence.professional_privacy_decision AS current_privacy
  ON current_privacy.professional_source_snapshot_id =
     source_file.professional_source_snapshot_id
 AND current_privacy.decision_state_code = 'ALLOWED'
 AND current_privacy.decided_on <= current_date
WHERE artifact.professional_source_file_id IS NOT NULL
  AND artifact.source_retrieved_at <= transaction_timestamp()
  AND assertion.source_retrieved_at <= transaction_timestamp()
  AND assertion.source_file_sha256_scope = 'FULL_SOURCE_FILE_SHA256'
  AND assertion.source_file_nonstorage_reason = ''
  AND (
      assertion.evidence_tier = 'P1'
      AND (
          legacy_assertion.assertion_type_code =
              'OFFICIAL_JUDGE_DESCRIPTOR'
          AND assertion.evidence_origin_type =
              'EXPLICIT_IDENTIFIED_JUDGE'
          AND observation.judge_observation_id IS NOT NULL
          AND observation.preparation_service_id =
              legacy_assertion.preparation_service_id
          AND observation.judge_id IS NOT NULL
          AND observation.observation_type_code IN ('JUDGE', 'HEAD_JUDGE')
          AND observation.official_confirmed
          AND legacy_assertion.panel_id = observation.panel_id
          AND observation.professional_source_snapshot_id =
              legacy_assertion.professional_source_snapshot_id
          AND observation.professional_source_file_id IS NOT DISTINCT FROM
              legacy_assertion.professional_source_file_id
          AND left(
              legacy_assertion.source_locator,
              length(observation.source_locator)
          ) = observation.source_locator
          OR legacy_assertion.assertion_type_code =
              'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR'
          AND assertion.evidence_origin_type =
              'EXPLICIT_IDENTIFIED_PANEL'
          AND assertion_panel.panel_id IS NOT NULL
          AND assertion_panel.series_id = service.series_id
          AND assertion_panel.edition_id = service.edition_id
          AND assertion_panel.category_id = service.category_id
          AND assertion_panel.round_id = service.round_id
          AND assertion_panel.professional_source_snapshot_id =
              legacy_assertion.professional_source_snapshot_id
          AND EXISTS (
              SELECT 1
              FROM competition.descriptor_assertion_judge_lineage AS lineage
              JOIN competition.judge_observation AS supporting_observation
                ON supporting_observation.judge_observation_id =
                   lineage.judge_observation_id
              WHERE lineage.descriptor_assertion_id =
                    legacy_assertion.descriptor_assertion_id
                AND supporting_observation.preparation_service_id =
                    legacy_assertion.preparation_service_id
                AND supporting_observation.panel_id =
                    legacy_assertion.panel_id
                AND supporting_observation.judge_id IS NOT NULL
                AND supporting_observation.observation_type_code IN (
                    'JUDGE', 'HEAD_JUDGE'
                )
                AND supporting_observation.official_confirmed
                AND supporting_observation.professional_source_snapshot_id =
                    legacy_assertion.professional_source_snapshot_id
                AND supporting_observation.professional_source_file_id
                    IS NOT DISTINCT FROM
                    legacy_assertion.professional_source_file_id
          )
          AND NOT EXISTS (
              SELECT 1
              FROM competition.descriptor_assertion_judge_lineage AS lineage
              JOIN competition.judge_observation AS supporting_observation
                ON supporting_observation.judge_observation_id =
                   lineage.judge_observation_id
              WHERE lineage.descriptor_assertion_id =
                    legacy_assertion.descriptor_assertion_id
                AND (
                    supporting_observation.preparation_service_id IS DISTINCT
                        FROM legacy_assertion.preparation_service_id
                    OR supporting_observation.panel_id IS DISTINCT FROM
                        legacy_assertion.panel_id
                    OR supporting_observation.judge_id IS NULL
                    OR supporting_observation.observation_type_code NOT IN (
                        'JUDGE', 'HEAD_JUDGE'
                    )
                    OR NOT supporting_observation.official_confirmed
                    OR supporting_observation.professional_source_snapshot_id
                        IS DISTINCT FROM
                        legacy_assertion.professional_source_snapshot_id
                    OR supporting_observation.professional_source_file_id
                        IS DISTINCT FROM
                        legacy_assertion.professional_source_file_id
                )
          )
      )
      OR assertion.evidence_tier = 'P2'
      AND legacy_assertion.assertion_type_code =
          'OFFICIAL_AGGREGATED_DESCRIPTOR'
      AND assertion.evidence_origin_type IN (
          'EXPLICIT_TOP_JURY_FIELD',
          'ORGANIZER_PUBLISHED_EXPLICIT_JURY',
          'ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION'
      )
      AND organizer_note.organizer_published_note_id IS NOT NULL
      AND organizer_note.preparation_service_id =
          legacy_assertion.preparation_service_id
      AND organizer_note.edition_id = service.edition_id
      AND organizer_note.evidence_tier_code = legacy_assertion.evidence_tier_code
      AND organizer_note.note_role_code IN (
          'JURY_NOTE', 'OFFICIAL_AGGREGATE_PROFILE'
      )
      AND organizer_note.professional_source_snapshot_id =
          legacy_assertion.professional_source_snapshot_id
      AND organizer_note.professional_source_file_id IS NOT DISTINCT FROM
          legacy_assertion.professional_source_file_id
      AND organizer_note.language_tag = legacy_assertion.language_tag
      AND organizer_note.raw_text IS NOT NULL
      AND legacy_assertion.raw_phrase IS NOT NULL
      AND position(
          legacy_assertion.raw_phrase IN organizer_note.raw_text
      ) > 0
      AND left(
          legacy_assertion.source_locator,
          length(organizer_note.source_locator)
      ) = organizer_note.source_locator
  );

COMMENT ON VIEW corpus.v_round3m_round3k_exact_descriptor_source_binding IS
    'Exact byte/file/snapshot/locator and affirmative-current-rights bridge for Round 3M assertions that reuse a Round 3K professional label decision.';

-- Ambiguous targets count only when they name one current PRIMARY root plus
-- current ADDITIONAL roots.  Contradictory targets require one current PRIMARY
-- root plus current CONFLICTING_ALTERNATIVE roots.  Aliases, candidates,
-- deprecated/replaced concepts, ranges, and duplicate roots add no credit.
CREATE FUNCTION audit.round3m_professional_label_target_set_is_countable(
    professional_label_decision_id_value BIGINT
)
RETURNS BOOLEAN
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_professional_label_target_set_is_countable$
WITH target_stats AS (
    SELECT
        count(*)::BIGINT AS target_count,
        count(*) FILTER (
            WHERE target.concept_id IS NOT NULL
        )::BIGINT AS concept_target_count,
        count(DISTINCT target.concept_id) FILTER (
            WHERE concept.lifecycle_status_code = 'active'
              AND concept.replacement_concept_id IS NULL
        )::BIGINT AS current_root_count,
        count(*) FILTER (
            WHERE target.target_role_code = 'PRIMARY'
        )::BIGINT AS primary_count,
        count(*) FILTER (
            WHERE target.target_role_code = 'ADDITIONAL'
        )::BIGINT AS additional_count,
        count(*) FILTER (
            WHERE target.target_role_code = 'CONFLICTING_ALTERNATIVE'
        )::BIGINT AS conflicting_count,
        count(*) FILTER (
            WHERE target.association_range_id IS NOT NULL
               OR concept.concept_id IS NULL
               OR concept.lifecycle_status_code <> 'active'
               OR concept.replacement_concept_id IS NOT NULL
               OR target.target_role_code = 'RANGE'
        )::BIGINT AS invalid_target_count
    FROM corpus.professional_label_target AS target
    LEFT JOIN kb.concept AS concept
      ON concept.concept_id = target.concept_id
    WHERE target.professional_label_decision_id =
          professional_label_decision_id_value
)
SELECT CASE decision.label_disposition_code
    WHEN 'UNRESOLVED' THEN stats.target_count = 0
    WHEN 'AMBIGUOUS_TARGET' THEN
        stats.target_count >= 2
        AND stats.target_count = stats.concept_target_count
        AND stats.current_root_count = stats.target_count
        AND stats.invalid_target_count = 0
        AND stats.primary_count = 1
        AND stats.additional_count = stats.target_count - 1
    WHEN 'CONTRADICTORY_TARGET' THEN
        stats.target_count >= 2
        AND stats.target_count = stats.concept_target_count
        AND stats.current_root_count = stats.target_count
        AND stats.invalid_target_count = 0
        AND stats.primary_count = 1
        AND stats.conflicting_count = stats.target_count - 1
    ELSE FALSE
END
FROM corpus.professional_label_decision AS decision
CROSS JOIN target_stats AS stats
WHERE decision.professional_label_decision_id =
      professional_label_decision_id_value
$round3m_professional_label_target_set_is_countable$;

-- Reverse-protect the Round 3K source identity after it contributes an
-- attested decision.  Rights corrections remain possible only by INSERTing a
-- successor; existing decisions and source identities are append-only.
CREATE FUNCTION competition.protect_round3m_attested_descriptor_source()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_descriptor_source$
BEGIN
    PERFORM 1
    FROM corpus.professional_expression AS expression
    JOIN corpus.professional_label_decision AS decision
      ON decision.professional_expression_id =
         expression.professional_expression_id
    WHERE expression.descriptor_assertion_id = OLD.descriptor_assertion_id
    ORDER BY decision.professional_label_decision_id
    FOR UPDATE OF decision;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_expression AS expression
        JOIN corpus.professional_label_decision AS decision
          ON decision.professional_expression_id =
             expression.professional_expression_id
        WHERE expression.descriptor_assertion_id = OLD.descriptor_assertion_id
          AND decision.round3m_attested_review_set_sha256 IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_descriptor_source_immutable_ck',
            MESSAGE = 'a Round 3K descriptor source used by an attested normalization decision is immutable';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_descriptor_source$;

CREATE TRIGGER round3m_attested_descriptor_source_bud
BEFORE UPDATE OR DELETE ON competition.descriptor_assertion
FOR EACH ROW EXECUTE FUNCTION
    competition.protect_round3m_attested_descriptor_source();

CREATE FUNCTION competition.protect_round3m_attested_descriptor_judge_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_descriptor_judge_lineage$
DECLARE
    affected_descriptor_assertion_id BIGINT;
    prior_descriptor_assertion_id BIGINT;
BEGIN
    affected_descriptor_assertion_id := CASE
        WHEN TG_OP = 'DELETE' THEN OLD.descriptor_assertion_id
        ELSE NEW.descriptor_assertion_id
    END;
    prior_descriptor_assertion_id := CASE
        WHEN TG_OP = 'UPDATE' THEN OLD.descriptor_assertion_id
        ELSE affected_descriptor_assertion_id
    END;

    PERFORM 1
    FROM corpus.professional_expression AS expression
    JOIN corpus.professional_label_decision AS decision
      ON decision.professional_expression_id =
         expression.professional_expression_id
    WHERE expression.descriptor_assertion_id IN (
        affected_descriptor_assertion_id, prior_descriptor_assertion_id
    )
    ORDER BY decision.professional_label_decision_id
    FOR UPDATE OF decision;

    IF EXISTS (
        SELECT 1
        FROM corpus.professional_expression AS expression
        JOIN corpus.professional_label_decision AS decision
          ON decision.professional_expression_id =
             expression.professional_expression_id
        WHERE expression.descriptor_assertion_id IN (
            affected_descriptor_assertion_id,
            prior_descriptor_assertion_id
        )
          AND decision.round3m_attested_review_set_sha256 IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT =
                'round3m_attested_descriptor_judge_lineage_immutable_ck',
            MESSAGE = 'judge-observation lineage used by an attested normalization decision is immutable';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_descriptor_judge_lineage$;

CREATE TRIGGER round3m_attested_descriptor_judge_lineage_biud
BEFORE INSERT OR UPDATE OR DELETE
ON competition.descriptor_assertion_judge_lineage
FOR EACH ROW EXECUTE FUNCTION
    competition.protect_round3m_attested_descriptor_judge_lineage();

CREATE FUNCTION evidence.protect_round3m_attested_source_identity()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_round3m_attested_source_identity$
DECLARE
    affected_file_id BIGINT;
    affected_snapshot_id BIGINT;
BEGIN
    IF TG_TABLE_NAME = 'professional_source_file' THEN
        affected_file_id := OLD.professional_source_file_id;
    ELSIF TG_TABLE_NAME IN (
        'professional_source_snapshot', 'professional_rights_decision'
    ) THEN
        affected_snapshot_id := OLD.professional_source_snapshot_id;
    ELSE
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'unexpected source-identity trigger table';
    END IF;

    PERFORM 1
    FROM competition.descriptor_assertion AS assertion
    JOIN corpus.professional_expression AS expression
      ON expression.descriptor_assertion_id = assertion.descriptor_assertion_id
    JOIN corpus.professional_label_decision AS decision
      ON decision.professional_expression_id =
         expression.professional_expression_id
    WHERE affected_file_id IS NOT NULL
          AND assertion.professional_source_file_id = affected_file_id
       OR affected_snapshot_id IS NOT NULL
          AND assertion.professional_source_snapshot_id = affected_snapshot_id
    ORDER BY decision.professional_label_decision_id
    FOR UPDATE OF decision;

    IF EXISTS (
        SELECT 1
        FROM competition.descriptor_assertion AS assertion
        JOIN corpus.professional_expression AS expression
          ON expression.descriptor_assertion_id =
             assertion.descriptor_assertion_id
        JOIN corpus.professional_label_decision AS decision
          ON decision.professional_expression_id =
             expression.professional_expression_id
        WHERE (
            affected_file_id IS NOT NULL
            AND assertion.professional_source_file_id = affected_file_id
            OR affected_snapshot_id IS NOT NULL
            AND assertion.professional_source_snapshot_id =
                affected_snapshot_id
        )
          AND decision.round3m_attested_review_set_sha256 IS NOT NULL
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_attested_source_identity_immutable_ck',
            MESSAGE = 'Round 3K source identity and rights rows used by an attested normalization decision are immutable; append a rights successor';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END
$protect_round3m_attested_source_identity$;

CREATE TRIGGER round3m_attested_source_file_bud
BEFORE UPDATE OR DELETE ON evidence.professional_source_file
FOR EACH ROW EXECUTE FUNCTION
    evidence.protect_round3m_attested_source_identity();

CREATE TRIGGER round3m_attested_source_snapshot_bud
BEFORE UPDATE OR DELETE ON evidence.professional_source_snapshot
FOR EACH ROW EXECUTE FUNCTION
    evidence.protect_round3m_attested_source_identity();

CREATE TRIGGER round3m_attested_source_rights_bud
BEFORE UPDATE OR DELETE ON evidence.professional_rights_decision
FOR EACH ROW EXECUTE FUNCTION
    evidence.protect_round3m_attested_source_identity();

CREATE VIEW corpus.v_round3m_human_reviewed_normalization_challenge_universe AS
SELECT
    model.descriptor_assertion_id,
    model.descriptor_assertion_key,
    model.effective_record_key,
    model.edition_year,
    model.independent_source_family_id,
    model.source_language,
    model.source_native_lexical_form,
    model.normalized_candidate_form,
    legacy_assertion.descriptor_assertion_id AS
        competition_descriptor_assertion_id,
    expression.professional_expression_id,
    expression.professional_expression_key,
    expression.normalized_phrase AS professional_normalized_phrase,
    decision.professional_label_decision_id,
    decision.professional_label_decision_key,
    decision.label_disposition_code,
    decision.decision_version,
    decision.decided_at
FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
JOIN corpus.v_round3m_round3k_exact_descriptor_source_binding AS
     exact_source
  ON exact_source.descriptor_assertion_id = model.descriptor_assertion_id
 AND exact_source.competition_descriptor_assertion_id =
     model.competition_descriptor_assertion_id
JOIN competition.descriptor_assertion AS legacy_assertion
  ON legacy_assertion.descriptor_assertion_id =
     model.competition_descriptor_assertion_id
 AND legacy_assertion.preparation_service_id = model.preparation_service_id
 AND legacy_assertion.raw_phrase_sha256 = model.atomic_source_text_sha256
 AND legacy_assertion.raw_phrase_sha256 =
     model.source_native_lexical_form_sha256
 AND legacy_assertion.language_tag = model.source_language
 AND legacy_assertion.assertion_type_code <> 'OFFICIAL_STRUCTURED_SCORE'
 AND legacy_assertion.raw_phrase IS NOT NULL
JOIN corpus.professional_expression AS expression
  ON expression.descriptor_assertion_id =
     legacy_assertion.descriptor_assertion_id
 AND expression.language_tag = model.source_language
 AND expression.normalized_phrase =
     kb.normalize_expression(legacy_assertion.raw_phrase)
 AND expression.normalized_phrase = model.normalized_candidate_form
 AND NOT expression.project_authored
 AND NOT expression.machine_generated
 AND NOT expression.semantic_inference_used
JOIN corpus.v_current_professional_label_decision AS decision
  ON decision.professional_expression_id =
     expression.professional_expression_id
 AND decision.unambiguous_current_decision
 AND decision.decision_status_code = 'FINAL'
 AND NOT decision.candidate_only
 AND decision.provenance_complete
 AND decision.decision_method_code = 'QUALIFIED_REVIEW'
 AND decision.expert_review_complete
 AND decision.adjudicator_present
 AND decision.independent_qualified_reviewer_count >= 2
 AND decision.label_disposition_code IN (
     'AMBIGUOUS_TARGET', 'CONTRADICTORY_TARGET', 'UNRESOLVED'
 )
JOIN corpus.professional_label_decision AS sealed_decision
  ON sealed_decision.professional_label_decision_id =
     decision.professional_label_decision_id
 AND sealed_decision.round3m_attested_review_set_sha256 IS NOT NULL
 AND sealed_decision.round3m_attested_review_set_sha256 IS NOT DISTINCT FROM
     audit.round3m_professional_label_review_set_sha256(
         decision.professional_label_decision_id
     )
WHERE model.source_native_lexical_form IS NOT NULL
  AND kb.normalize_expression(model.source_native_lexical_form) =
      expression.normalized_phrase
  AND decision.decided_at <= transaction_timestamp()
  AND audit.round3m_professional_label_lineage_is_valid(
          decision.professional_label_decision_id
      )
  AND (
      SELECT count(DISTINCT identity.canonical_human_identity_sha256)
      FROM audit.professional_label_review AS review
      JOIN audit.round3m_professional_label_review_attestation AS attestation
        ON attestation.professional_label_review_id =
           review.professional_label_review_id
      JOIN audit.round3m_human_reviewer_identity_receipt AS identity
        ON identity.reviewer_identity_receipt_key =
           attestation.reviewer_identity_receipt_key
       AND identity.reviewer_id = review.reviewer_id
      WHERE review.professional_label_decision_id =
            decision.professional_label_decision_id
        AND review.reviewer_role_code = 'INDEPENDENT_REVIEWER'
        AND review.review_outcome_code = 'ACCEPT'
  ) = decision.independent_qualified_reviewer_count
  AND (
      SELECT count(DISTINCT identity.canonical_human_identity_sha256)
      FROM audit.professional_label_review AS review
      JOIN audit.round3m_professional_label_review_attestation AS attestation
        ON attestation.professional_label_review_id =
           review.professional_label_review_id
      JOIN audit.round3m_human_reviewer_identity_receipt AS identity
        ON identity.reviewer_identity_receipt_key =
           attestation.reviewer_identity_receipt_key
       AND identity.reviewer_id = review.reviewer_id
      WHERE review.professional_label_decision_id =
            decision.professional_label_decision_id
        AND review.reviewer_role_code = 'ADJUDICATOR'
        AND review.review_outcome_code = 'ACCEPT'
  ) = 1
  AND (
      SELECT count(*) =
             count(DISTINCT identity.canonical_human_identity_sha256)
      FROM audit.professional_label_review AS review
      JOIN audit.round3m_professional_label_review_attestation AS attestation
        ON attestation.professional_label_review_id =
           review.professional_label_review_id
      JOIN audit.round3m_human_reviewer_identity_receipt AS identity
        ON identity.reviewer_identity_receipt_key =
           attestation.reviewer_identity_receipt_key
       AND identity.reviewer_id = review.reviewer_id
      WHERE review.professional_label_decision_id =
            decision.professional_label_decision_id
        AND review.review_outcome_code = 'ACCEPT'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM audit.professional_label_review AS review
      JOIN audit.reviewer AS reviewer
        ON reviewer.reviewer_id = review.reviewer_id
      LEFT JOIN audit.round3m_professional_label_review_attestation AS attestation
        ON attestation.professional_label_review_id =
           review.professional_label_review_id
      LEFT JOIN audit.round3m_human_reviewer_identity_receipt AS identity
        ON identity.reviewer_identity_receipt_key =
           attestation.reviewer_identity_receipt_key
      WHERE review.professional_label_decision_id =
            decision.professional_label_decision_id
        AND (
            review.review_outcome_code <> 'ACCEPT'
            OR review.reviewed_at > decision.decided_at
            OR review.reviewed_at > transaction_timestamp()
            OR attestation.professional_label_review_id IS NULL
            OR attestation.review_actor_type NOT IN (
                'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
            )
            OR attestation.receipt_origin_code NOT IN (
                'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
            )
            OR attestation.human_event_evidence_sha256 !~
                '^[0-9a-f]{64}$'
            OR attestation.created_at < decision.decided_at
            OR attestation.created_at > transaction_timestamp()
            OR attestation.reviewer_id_or_pseudonymous_code IS DISTINCT FROM
               reviewer.reviewer_key
            OR identity.reviewer_id IS NULL
            OR identity.reviewer_id IS DISTINCT FROM review.reviewer_id
            OR identity.created_at > attestation.created_at
            OR attestation.human_event_member_sha256 IS DISTINCT FROM
               audit.round3m_human_review_event_member_sha256(
                   review.professional_label_review_id,
                   attestation.human_event_evidence_sha256
               )
            OR review.reviewer_role_code = 'ADJUDICATOR'
               AND attestation.review_actor_type <> 'EXPERT_REVIEWER'
            OR attestation.review_payload_sha256 IS DISTINCT FROM
               audit.round3m_professional_label_review_payload_sha256(
                   review.professional_label_review_id
               )
            OR attestation.decision_review_set_sha256 IS DISTINCT FROM
               audit.round3m_professional_label_review_set_sha256(
                   decision.professional_label_decision_id
               )
            OR attestation.reviewer_independence_set_sha256 IS DISTINCT FROM
               audit.round3m_professional_reviewer_independence_set_sha256(
                   decision.professional_label_decision_id
               )
            OR review.reviewer_role_code = 'INDEPENDENT_REVIEWER'
               AND NOT EXISTS (
                    SELECT 1
                    FROM audit.professional_reviewer_qualification AS qualification
                    WHERE qualification.reviewer_id = review.reviewer_id
                      AND qualification.eligible
                      AND qualification.verified_on <=
                          (review.reviewed_at AT TIME ZONE 'UTC')::DATE
                      AND qualification.qualification_scope_code IN (
                          'PROFESSIONAL_COFFEE_SENSORY',
                          'COMPETITION_JUDGING'
                      )
               )
            OR review.reviewer_role_code = 'ADJUDICATOR'
               AND (
                    NOT EXISTS (
                        SELECT 1
                        FROM audit.professional_reviewer_qualification AS qualification
                        WHERE qualification.reviewer_id = review.reviewer_id
                          AND qualification.eligible
                          AND qualification.verified_on <=
                              (review.reviewed_at AT TIME ZONE 'UTC')::DATE
                          AND qualification.qualification_scope_code =
                              'ADJUDICATION'
                    )
                    OR NOT EXISTS (
                        SELECT 1
                        FROM audit.professional_reviewer_qualification AS qualification
                        WHERE qualification.reviewer_id = review.reviewer_id
                          AND qualification.eligible
                          AND qualification.verified_on <=
                              (review.reviewed_at AT TIME ZONE 'UTC')::DATE
                          AND qualification.qualification_scope_code IN (
                              'PROFESSIONAL_COFFEE_SENSORY',
                              'COMPETITION_JUDGING'
                          )
                    )
               )
            OR lower(split_part(expression.language_tag, '-', 1)) <> 'en'
               AND NOT EXISTS (
                    SELECT 1
                    FROM audit.professional_reviewer_qualification AS qualification
                    WHERE qualification.reviewer_id = review.reviewer_id
                      AND qualification.eligible
                      AND qualification.verified_on <=
                          (review.reviewed_at AT TIME ZONE 'UTC')::DATE
                      AND qualification.qualification_scope_code =
                          'SOURCE_LANGUAGE'
                      AND lower(split_part(
                          qualification.source_language_tag, '-', 1
                      )) = lower(split_part(
                          expression.language_tag, '-', 1
                      ))
               )
        )
  )
  AND audit.round3m_professional_label_target_set_is_countable(
          decision.professional_label_decision_id
      );

COMMENT ON VIEW
    corpus.v_round3m_human_reviewed_normalization_challenge_universe
IS 'Model-rights-eligible P1/P2 strict assertions with byte-identical Round 3M/Round 3K file, snapshot, locator, and rights lineage plus one sealed leaf FINAL all-ACCEPT qualified-human current-root AMBIGUOUS_TARGET, CONTRADICTORY_TARGET, or UNRESOLVED label decision. ABSTAIN, REVISE, REJECT, CONFLICT, and generic Round 3M assertion MARK_* receipts do not count.';

ALTER VIEW audit.v_round3m_descriptor_gate_metrics
    RENAME TO v_round3m_descriptor_gate_metrics_pre_v059;

CREATE VIEW audit.v_round3m_descriptor_gate_metrics AS
WITH challenge AS (
    SELECT count(DISTINCT professional_label_decision_id)::BIGINT AS value
    FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
)
SELECT
    prior.segmented_atomic_observation_count,
    prior.reviewed_p1_p2_strict_assertion_count,
    prior.reviewed_descriptor_bearing_record_count,
    prior.reviewed_unique_normalized_form_count,
    prior.reviewed_independent_source_family_count,
    prior.reviewed_largest_family_share,
    prior.minimum_records_per_output_label,
    prior.reviewed_multi_target_record_count,
    challenge.value AS reviewed_ambiguous_or_unresolved_challenge_count,
    prior.supported_within_record_pair_event_count,
    prior.supported_coassertion_set_count,
    prior.held_out_independent_family_count,
    prior.held_out_edition_year_count,
    prior.source_provenance_completeness,
    prior.label_provenance_completeness,
    prior.source_and_label_provenance_completeness,
    prior.internal_research_rights_rate,
    prior.model_research_rights_rate,
    prior.deployment_rights_rate,
    prior.internal_research_rights_blocker_count,
    prior.model_research_rights_blocker_count,
    prior.deployment_rights_blocker_count,
    prior.human_review_blocker_count,
    prior.record_boundaries_preserved
FROM audit.v_round3m_descriptor_gate_metrics_pre_v059 AS prior
CROSS JOIN challenge;

-- Gate rows are immutable by design.  Append a complete successor contract;
-- do not rewrite the v1 historical checkpoint.  Only the challenge criterion
-- changes universe and explanation.
ALTER TABLE audit.round3m_descriptor_gate_criterion
    DROP CONSTRAINT round3m_descriptor_gate_criterion_text_ck,
    ADD CONSTRAINT round3m_descriptor_gate_criterion_text_ck CHECK (
        metric_name = upper(btrim(metric_name)) AND metric_name <> ''
        AND operator IN ('>=', '<=', '=')
        AND num_nonnulls(required_numeric, required_boolean) = 1
        AND required_value = btrim(required_value)
        AND required_value <> ''
        AND universe IN (
            'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE',
            'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
            'DEPLOYMENT_ELIGIBLE_DESCRIPTOR_UNIVERSE',
            'HUMAN_REVIEWED_NORMALIZATION_CHALLENGE_UNIVERSE'
        )
        AND blocker_class IN (
            'DATA', 'RIGHTS', 'REVIEW', 'DATA_AND_REVIEW'
        )
        AND explanatory_note = btrim(explanatory_note)
        AND explanatory_note <> ''
    );

INSERT INTO audit.round3m_descriptor_gate_definition (
    gate_version, gate_name, gate_order, gate_purpose, default_universe,
    authorizes_training, active, explanatory_note
)
SELECT
    'round3m-descriptor-gates-v2', gate_name, gate_order, gate_purpose,
    default_universe, authorizes_training, active,
    CASE
        WHEN gate_name = 'GATE_2000_EXPERIMENTAL_NORMALIZATION'
            THEN explanatory_note ||
                 ' Normalization challenge credit follows the qualified-human label-decision contract introduced by migration 059.'
        ELSE explanatory_note
    END
FROM audit.round3m_descriptor_gate_definition
WHERE gate_version = 'round3m-descriptor-gates-v1';

INSERT INTO audit.round3m_descriptor_gate_criterion (
    gate_version, gate_name, criterion_ordinal, metric_name, operator,
    required_numeric, required_boolean, required_value, universe,
    blocker_class, explanatory_note
)
SELECT
    'round3m-descriptor-gates-v2', gate_name, criterion_ordinal,
    metric_name, operator, required_numeric, required_boolean,
    required_value,
    CASE
        WHEN gate_name = 'GATE_2000_EXPERIMENTAL_NORMALIZATION'
         AND metric_name =
             'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT'
            THEN 'HUMAN_REVIEWED_NORMALIZATION_CHALLENGE_UNIVERSE'
        ELSE universe
    END,
    blocker_class,
    CASE
        WHEN gate_name = 'GATE_2000_EXPERIMENTAL_NORMALIZATION'
         AND metric_name =
             'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT'
            THEN 'Leaf final all-ACCEPT qualified-human ambiguous, contradictory, or unresolved normalization-label decisions with exact Round 3M/Round 3K source binding; ABSTAIN, REVISE, REJECT, CONFLICT, and generic assertion MARK_* receipts do not count.'
        ELSE explanatory_note
    END
FROM audit.round3m_descriptor_gate_criterion
WHERE gate_version = 'round3m-descriptor-gates-v1';

CREATE FUNCTION audit.round3m_descriptor_gate_contract_payload_sha256(
    gate_version_value TEXT
)
RETURNS TEXT
LANGUAGE SQL
STABLE
STRICT
SET search_path = pg_catalog
AS $round3m_descriptor_gate_contract_payload_sha256$
SELECT audit.round3i_utf8_sha256(
    jsonb_build_object(
        'gate_version', gate_version_value,
        'definitions', coalesce((
            SELECT jsonb_agg(
                to_jsonb(definition)
                ORDER BY definition.gate_order, definition.gate_name
            )
            FROM audit.round3m_descriptor_gate_definition AS definition
            WHERE definition.gate_version = gate_version_value
        ), '[]'::jsonb),
        'criteria', coalesce((
            SELECT jsonb_agg(
                to_jsonb(criterion)
                ORDER BY criterion.gate_name, criterion.criterion_ordinal
            )
            FROM audit.round3m_descriptor_gate_criterion AS criterion
            WHERE criterion.gate_version = gate_version_value
        ), '[]'::jsonb)
    )::TEXT
)
$round3m_descriptor_gate_contract_payload_sha256$;

CREATE TABLE audit.round3m_descriptor_gate_contract_release (
    gate_version TEXT NOT NULL,
    contract_ordinal INTEGER NOT NULL,
    supersedes_gate_version TEXT,
    released_at TIMESTAMPTZ NOT NULL,
    contract_payload_sha256 TEXT NOT NULL,
    release_basis TEXT NOT NULL,
    CONSTRAINT round3m_descriptor_gate_contract_release_pk PRIMARY KEY (
        gate_version
    ),
    CONSTRAINT round3m_descriptor_gate_contract_release_ordinal_uq UNIQUE (
        contract_ordinal
    ),
    CONSTRAINT round3m_descriptor_gate_contract_release_successor_uq UNIQUE (
        supersedes_gate_version
    ),
    CONSTRAINT round3m_descriptor_gate_contract_release_predecessor_fk
        FOREIGN KEY (supersedes_gate_version)
        REFERENCES audit.round3m_descriptor_gate_contract_release (
            gate_version
        ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_gate_contract_release_text_ck CHECK (
        gate_version = lower(btrim(gate_version))
        AND gate_version <> ''
        AND contract_ordinal > 0
        AND (contract_ordinal = 1) = (supersedes_gate_version IS NULL)
        AND contract_payload_sha256 ~ '^[0-9a-f]{64}$'
        AND release_basis = btrim(release_basis)
        AND release_basis <> ''
    )
);

-- Definitions and criteria may be assembled before their release row exists,
-- but a released version is closed to every later INSERT as well as the
-- UPDATE/DELETE operations already rejected by migration 056.
CREATE FUNCTION audit.reject_round3m_released_gate_contract_insert()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $reject_round3m_released_gate_contract_insert$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM audit.round3m_descriptor_gate_contract_release AS release
        WHERE release.gate_version = NEW.gate_version
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_released_gate_contract_immutable_ck',
            MESSAGE = 'a released descriptor gate contract is closed to new definitions and criteria';
    END IF;

    RETURN NEW;
END
$reject_round3m_released_gate_contract_insert$;

CREATE TRIGGER round3m_gate_definition_released_bi
BEFORE INSERT ON audit.round3m_descriptor_gate_definition
FOR EACH ROW EXECUTE FUNCTION
    audit.reject_round3m_released_gate_contract_insert();

CREATE TRIGGER round3m_gate_criterion_released_bi
BEFORE INSERT ON audit.round3m_descriptor_gate_criterion
FOR EACH ROW EXECUTE FUNCTION
    audit.reject_round3m_released_gate_contract_insert();

CREATE FUNCTION audit.validate_round3m_descriptor_gate_contract_release()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $validate_round3m_descriptor_gate_contract_release$
DECLARE
    predecessor audit.round3m_descriptor_gate_contract_release%ROWTYPE;
    definition_count BIGINT;
    criterion_count BIGINT;
BEGIN
    IF NEW.released_at > transaction_timestamp() THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_gate_contract_nonfuture_ck',
            MESSAGE = 'a descriptor gate contract cannot become current before its release timestamp';
    END IF;

    SELECT count(*) INTO definition_count
    FROM audit.round3m_descriptor_gate_definition
    WHERE gate_version = NEW.gate_version;

    SELECT count(*) INTO criterion_count
    FROM audit.round3m_descriptor_gate_criterion
    WHERE gate_version = NEW.gate_version;

    IF definition_count <> 7 OR criterion_count <> 56 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_gate_contract_shape_ck',
            MESSAGE = 'a descriptor gate contract release requires the complete seven-definition, 56-criterion authoritative gate surface',
            DETAIL = format(
                'gate_version=%s definitions=%s criteria=%s',
                NEW.gate_version, definition_count, criterion_count
            );
    END IF;

    IF NEW.contract_payload_sha256 IS DISTINCT FROM
       audit.round3m_descriptor_gate_contract_payload_sha256(
           NEW.gate_version
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round3m_descriptor_gate_contract_payload_ck',
            MESSAGE = 'gate contract release must bind the exact immutable definition and criterion payload';
    END IF;

    IF NEW.supersedes_gate_version IS NOT NULL THEN
        SELECT * INTO STRICT predecessor
        FROM audit.round3m_descriptor_gate_contract_release
        WHERE gate_version = NEW.supersedes_gate_version;

        IF predecessor.contract_ordinal <> NEW.contract_ordinal - 1
           OR predecessor.released_at > NEW.released_at THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'round3m_descriptor_gate_contract_lineage_ck',
                MESSAGE = 'gate contract release must supersede the immediately prior chronological version';
        END IF;
    END IF;

    RETURN NEW;
END
$validate_round3m_descriptor_gate_contract_release$;

CREATE TRIGGER round3m_descriptor_gate_contract_release_bi
BEFORE INSERT ON audit.round3m_descriptor_gate_contract_release
FOR EACH ROW EXECUTE FUNCTION
    audit.validate_round3m_descriptor_gate_contract_release();

CREATE TRIGGER round3m_descriptor_gate_contract_release_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_gate_contract_release
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

INSERT INTO audit.round3m_descriptor_gate_contract_release (
    gate_version, contract_ordinal, supersedes_gate_version, released_at,
    contract_payload_sha256, release_basis
) VALUES (
    'round3m-descriptor-gates-v1', 1, NULL,
    TIMESTAMPTZ '2026-08-28T00:00:00Z',
    audit.round3m_descriptor_gate_contract_payload_sha256(
        'round3m-descriptor-gates-v1'
    ),
    'Historical descriptor-first gate contract introduced by migration 056.'
);

INSERT INTO audit.round3m_descriptor_gate_contract_release (
    gate_version, contract_ordinal, supersedes_gate_version, released_at,
    contract_payload_sha256, release_basis
) VALUES (
    'round3m-descriptor-gates-v2', 2,
    'round3m-descriptor-gates-v1',
    TIMESTAMPTZ '2026-08-28T06:00:00Z',
    audit.round3m_descriptor_gate_contract_payload_sha256(
        'round3m-descriptor-gates-v2'
    ),
    'Normalization challenge credit corrected to exact-source sealed qualified-human label decisions by migration 059.'
);

CREATE VIEW audit.v_round3m_current_descriptor_gate_contract AS
SELECT release.*
FROM audit.round3m_descriptor_gate_contract_release AS release
WHERE NOT EXISTS (
    SELECT 1
    FROM audit.round3m_descriptor_gate_contract_release AS successor
    WHERE successor.supersedes_gate_version = release.gate_version
)
  AND release.released_at <= transaction_timestamp()
  AND release.contract_payload_sha256 IS NOT DISTINCT FROM
      audit.round3m_descriptor_gate_contract_payload_sha256(
          release.gate_version
      );

COMMENT ON VIEW audit.v_round3m_current_descriptor_gate_contract IS
    'Exactly one append-only leaf gate contract; historical release rows remain auditable but cannot authorize current status.';

DO $round3m_normalization_challenge_criterion_exact$
BEGIN
    IF (
        SELECT count(*)
        FROM audit.round3m_descriptor_gate_criterion
        WHERE gate_version = 'round3m-descriptor-gates-v2'
          AND gate_name = 'GATE_2000_EXPERIMENTAL_NORMALIZATION'
          AND metric_name =
              'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT'
          AND universe =
              'HUMAN_REVIEWED_NORMALIZATION_CHALLENGE_UNIVERSE'
    ) <> 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT =
                'round3m_normalization_challenge_criterion_universe_ck',
            MESSAGE = 'the normalization challenge criterion must use exactly the qualified-human normalization-challenge universe';
    END IF;
END
$round3m_normalization_challenge_criterion_exact$;

-- Renaming the old metric view preserves it for audit.  Recreate the two
-- direct consumers so their dependencies bind to the corrected metric view.
CREATE OR REPLACE VIEW audit.v_round3m_descriptor_gate_status AS
WITH observed AS (
    SELECT
        criterion.*,
        CASE criterion.metric_name
            WHEN 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT'
                THEN metric.reviewed_p1_p2_strict_assertion_count::NUMERIC
            WHEN 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT'
                THEN metric.reviewed_descriptor_bearing_record_count::NUMERIC
            WHEN 'REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT'
                THEN metric.reviewed_unique_normalized_form_count::NUMERIC
            WHEN 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT'
                THEN metric.reviewed_independent_source_family_count::NUMERIC
            WHEN 'REVIEWED_LARGEST_FAMILY_SHARE'
                THEN metric.reviewed_largest_family_share
            WHEN 'MINIMUM_RECORDS_PER_OUTPUT_LABEL'
                THEN metric.minimum_records_per_output_label
            WHEN 'REVIEWED_MULTI_TARGET_RECORD_COUNT'
                THEN metric.reviewed_multi_target_record_count::NUMERIC
            WHEN 'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT'
                THEN metric.reviewed_ambiguous_or_unresolved_challenge_count::NUMERIC
            WHEN 'SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT'
                THEN metric.supported_within_record_pair_event_count::NUMERIC
            WHEN 'HELD_OUT_INDEPENDENT_FAMILY_COUNT'
                THEN metric.held_out_independent_family_count::NUMERIC
            WHEN 'HELD_OUT_EDITION_YEAR_COUNT'
                THEN metric.held_out_edition_year_count::NUMERIC
            WHEN 'SOURCE_PROVENANCE_COMPLETENESS'
                THEN metric.source_provenance_completeness
            WHEN 'LABEL_PROVENANCE_COMPLETENESS'
                THEN metric.label_provenance_completeness
            WHEN 'SOURCE_AND_LABEL_PROVENANCE_COMPLETENESS'
                THEN metric.source_and_label_provenance_completeness
            WHEN 'INTERNAL_RESEARCH_RIGHTS_RATE'
                THEN metric.internal_research_rights_rate
            WHEN 'MODEL_RESEARCH_RIGHTS_RATE'
                THEN metric.model_research_rights_rate
            WHEN 'DEPLOYMENT_RIGHTS_RATE'
                THEN metric.deployment_rights_rate
            ELSE NULL::NUMERIC
        END AS observed_numeric,
        CASE criterion.metric_name
            WHEN 'RECORD_BOUNDARIES_PRESERVED'
                THEN metric.record_boundaries_preserved
            ELSE NULL::BOOLEAN
        END AS observed_boolean
    FROM audit.round3m_descriptor_gate_criterion AS criterion
    JOIN audit.v_round3m_current_descriptor_gate_contract AS current_contract
      ON current_contract.gate_version = criterion.gate_version
    CROSS JOIN audit.v_round3m_descriptor_gate_metrics AS metric
), evaluated AS (
    SELECT
        observed.*,
        CASE
            WHEN required_boolean IS NOT NULL
                THEN observed_boolean IS NULL
            ELSE observed_numeric IS NULL
        END AS not_applicable,
        CASE
            WHEN required_boolean IS NOT NULL
              AND observed_boolean IS NULL THEN FALSE
            WHEN required_numeric IS NOT NULL
              AND observed_numeric IS NULL THEN FALSE
            WHEN operator = '>=' THEN observed_numeric >= required_numeric
            WHEN operator = '<=' THEN observed_numeric <= required_numeric
            WHEN operator = '=' AND required_boolean IS NOT NULL
                THEN observed_boolean IS NOT DISTINCT FROM required_boolean
            WHEN operator = '=' THEN observed_numeric = required_numeric
            ELSE FALSE
        END AS criterion_pass
    FROM observed
)
SELECT
    gate_version,
    gate_name,
    metric_name,
    CASE
        WHEN not_applicable THEN 'NA'
        WHEN required_boolean IS NOT NULL THEN observed_boolean::TEXT
        ELSE observed_numeric::TEXT
    END AS observed_value,
    required_value,
    universe,
    criterion_pass AS pass,
    not_applicable,
    blocker_class = 'RIGHTS' AND NOT criterion_pass AS rights_blocker,
    blocker_class IN ('DATA', 'DATA_AND_REVIEW')
      AND NOT criterion_pass AS data_blocker,
    blocker_class IN ('REVIEW', 'DATA_AND_REVIEW')
      AND NOT criterion_pass AS review_blocker,
    CASE WHEN not_applicable
         THEN explanatory_note ||
              ' Observed value is unavailable; NA never passes.'
         ELSE explanatory_note END AS explanatory_note,
    criterion_ordinal,
    operator,
    observed_numeric,
    observed_boolean
FROM evaluated;

CREATE OR REPLACE VIEW audit.v_round3m_descriptor_gate AS
SELECT
    definition.gate_version,
    definition.gate_name,
    definition.gate_purpose,
    definition.default_universe AS universe,
    count(status.metric_name)::INTEGER AS criterion_count,
    bool_and(status.pass) AS criteria_pass,
    bool_or(status.not_applicable) AS has_not_applicable,
    bool_or(status.rights_blocker) AS rights_blocker,
    bool_or(status.data_blocker) AS data_blocker,
    bool_or(status.review_blocker) AS review_blocker,
    count(status.metric_name) > 0
      AND metric.segmented_atomic_observation_count > 0
      AND bool_and(status.pass)
      AND NOT bool_or(status.not_applicable) AS gate_pass,
    definition.authorizes_training,
    FALSE AS training_authorization_pass,
    definition.explanatory_note
FROM audit.round3m_descriptor_gate_definition AS definition
JOIN audit.v_round3m_current_descriptor_gate_contract AS current_contract
  ON current_contract.gate_version = definition.gate_version
JOIN audit.v_round3m_descriptor_gate_status AS status
  ON status.gate_version = definition.gate_version
 AND status.gate_name = definition.gate_name
CROSS JOIN audit.v_round3m_descriptor_gate_metrics AS metric
WHERE definition.active
GROUP BY
    definition.gate_version, definition.gate_name,
    definition.gate_order, definition.gate_purpose,
    definition.default_universe, definition.authorizes_training,
    definition.explanatory_note,
    metric.segmented_atomic_observation_count
ORDER BY definition.gate_order;

ALTER FUNCTION audit.run_round3m_gate_validation_queries()
    RENAME TO run_round3m_gate_validation_queries_pre_v059;

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
WITH challenge_rows AS (
    SELECT *
    FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
), attested_review AS (
    SELECT
        attestation.*,
        review.professional_label_decision_id,
        review.reviewer_id,
        review.reviewer_role_code,
        review.review_outcome_code,
        review.reviewed_at,
        reviewer.reviewer_key,
        identity.reviewer_id AS identity_reviewer_id,
        identity.created_at AS identity_created_at,
        decision.decided_at,
        decision.round3m_attested_review_set_sha256
    FROM audit.round3m_professional_label_review_attestation AS attestation
    JOIN audit.professional_label_review AS review
      ON review.professional_label_review_id =
         attestation.professional_label_review_id
    JOIN audit.reviewer AS reviewer
      ON reviewer.reviewer_id = review.reviewer_id
    JOIN audit.round3m_human_reviewer_identity_receipt AS identity
      ON identity.reviewer_identity_receipt_key =
         attestation.reviewer_identity_receipt_key
    JOIN corpus.professional_label_decision AS decision
      ON decision.professional_label_decision_id =
         review.professional_label_decision_id
), definition_parity AS (
    SELECT
        count(*) FILTER (
            WHERE v2.gate_name <>
                      'GATE_2000_EXPERIMENTAL_NORMALIZATION'
              AND (to_jsonb(v2) - 'gate_version') IS NOT DISTINCT FROM
                  (to_jsonb(v1) - 'gate_version')
        )::BIGINT AS unchanged_count,
        count(*) FILTER (
            WHERE v2.gate_name =
                      'GATE_2000_EXPERIMENTAL_NORMALIZATION'
              AND v2.explanatory_note = v1.explanatory_note ||
                  ' Normalization challenge credit follows the qualified-human label-decision contract introduced by migration 059.'
              AND (to_jsonb(v2) - ARRAY[
                      'gate_version', 'explanatory_note'
                  ]) IS NOT DISTINCT FROM
                  (to_jsonb(v1) - ARRAY[
                      'gate_version', 'explanatory_note'
                  ])
        )::BIGINT AS exact_changed_count,
        count(*) FILTER (
            WHERE NOT v2.authorizes_training
        )::BIGINT AS nontraining_count,
        count(*)::BIGINT AS paired_count
    FROM audit.round3m_descriptor_gate_definition AS v2
    JOIN audit.round3m_descriptor_gate_definition AS v1
      ON v1.gate_version = 'round3m-descriptor-gates-v1'
     AND v1.gate_name = v2.gate_name
    WHERE v2.gate_version = 'round3m-descriptor-gates-v2'
), criterion_parity AS (
    SELECT
        count(*) FILTER (
            WHERE (to_jsonb(v2) - 'gate_version') IS NOT DISTINCT FROM
                  (to_jsonb(v1) - 'gate_version')
        )::BIGINT AS unchanged_count,
        count(*) FILTER (
            WHERE v2.gate_name =
                      'GATE_2000_EXPERIMENTAL_NORMALIZATION'
              AND v2.metric_name =
                      'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT'
              AND v2.universe =
                      'HUMAN_REVIEWED_NORMALIZATION_CHALLENGE_UNIVERSE'
              AND v2.explanatory_note =
                      'Leaf final all-ACCEPT qualified-human ambiguous, contradictory, or unresolved normalization-label decisions with exact Round 3M/Round 3K source binding; ABSTAIN, REVISE, REJECT, CONFLICT, and generic assertion MARK_* receipts do not count.'
              AND (to_jsonb(v2) - ARRAY[
                      'gate_version', 'universe', 'explanatory_note'
                  ]) IS NOT DISTINCT FROM
                  (to_jsonb(v1) - ARRAY[
                      'gate_version', 'universe', 'explanatory_note'
                  ])
        )::BIGINT AS exact_changed_count,
        count(*)::BIGINT AS paired_count
    FROM audit.round3m_descriptor_gate_criterion AS v2
    JOIN audit.round3m_descriptor_gate_criterion AS v1
      ON v1.gate_version = 'round3m-descriptor-gates-v1'
     AND v1.gate_name = v2.gate_name
     AND v1.criterion_ordinal = v2.criterion_ordinal
    WHERE v2.gate_version = 'round3m-descriptor-gates-v2'
), challenge_checks AS (
    SELECT
        'round3m.normalization_challenge_metric_matches_governed_universe'::TEXT
            AS check_key,
        count(*)::BIGINT AS violation_count
    FROM audit.v_round3m_descriptor_gate_metrics AS metric
    CROSS JOIN LATERAL (
        SELECT count(DISTINCT professional_label_decision_id)::BIGINT AS value
        FROM corpus.v_round3m_human_reviewed_normalization_challenge_universe
    ) AS expected
    WHERE metric.reviewed_ambiguous_or_unresolved_challenge_count IS DISTINCT
          FROM expected.value
    UNION ALL
    SELECT
        'round3m.normalization_challenge_criterion_universe_is_exact',
        CASE WHEN count(*) = 1 THEN 0 ELSE 1 END::BIGINT
    FROM audit.round3m_descriptor_gate_criterion AS criterion
    WHERE criterion.gate_version = 'round3m-descriptor-gates-v2'
      AND criterion.gate_name = 'GATE_2000_EXPERIMENTAL_NORMALIZATION'
      AND criterion.metric_name =
          'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT'
      AND criterion.universe =
          'HUMAN_REVIEWED_NORMALIZATION_CHALLENGE_UNIVERSE'
    UNION ALL
    SELECT
        'round3m.professional_label_attestation_payload_is_exact',
        count(*)::BIGINT
    FROM audit.round3m_professional_label_review_attestation AS attestation
    WHERE attestation.review_payload_sha256 IS DISTINCT FROM
          audit.round3m_professional_label_review_payload_sha256(
              attestation.professional_label_review_id
          )
    UNION ALL
    SELECT
        'round3m.professional_label_attestation_sets_are_exact',
        count(*)::BIGINT
    FROM attested_review AS attested
    WHERE attested.decision_review_set_sha256 IS DISTINCT FROM
          audit.round3m_professional_label_review_set_sha256(
              attested.professional_label_decision_id
          )
       OR attested.reviewer_independence_set_sha256 IS DISTINCT FROM
          audit.round3m_professional_reviewer_independence_set_sha256(
              attested.professional_label_decision_id
          )
    UNION ALL
    SELECT
        'round3m.professional_label_attestation_human_identity_is_exact',
        count(*)::BIGINT
    FROM attested_review AS attested
    WHERE attested.identity_reviewer_id IS DISTINCT FROM attested.reviewer_id
       OR attested.identity_created_at > attested.created_at
       OR attested.human_event_member_sha256 IS DISTINCT FROM
          audit.round3m_human_review_event_member_sha256(
              attested.professional_label_review_id,
              attested.human_event_evidence_sha256
          )
    UNION ALL
    SELECT
        'round3m.professional_label_attested_parent_marker_is_exact',
        count(DISTINCT attested.professional_label_decision_id)::BIGINT
    FROM attested_review AS attested
    WHERE attested.round3m_attested_review_set_sha256 IS NULL
       OR attested.round3m_attested_review_set_sha256 IS DISTINCT FROM
          audit.round3m_professional_label_review_set_sha256(
              attested.professional_label_decision_id
          )
       OR attested.round3m_attested_review_set_sha256 IS DISTINCT FROM
          attested.decision_review_set_sha256
    UNION ALL
    SELECT
        'round3m.professional_label_attested_lineage_is_valid',
        count(DISTINCT attested.professional_label_decision_id)::BIGINT
    FROM attested_review AS attested
    WHERE NOT audit.round3m_professional_label_lineage_is_valid(
        attested.professional_label_decision_id
    )
    UNION ALL
    SELECT
        'round3m.professional_label_attestation_identity_outcome_chronology_is_exact',
        count(*)::BIGINT
    FROM attested_review AS attested
    WHERE attested.reviewer_id_or_pseudonymous_code IS DISTINCT FROM
          attested.reviewer_key
       OR attested.review_outcome_code <> 'ACCEPT'
       OR attested.reviewed_at > attested.decided_at
       OR attested.reviewed_at > transaction_timestamp()
       OR attested.decided_at > attested.created_at
       OR attested.created_at > transaction_timestamp()
       OR attested.reviewer_role_code = 'ADJUDICATOR'
          AND attested.review_actor_type <> 'EXPERT_REVIEWER'
    UNION ALL
    SELECT
        'round3m.normalization_challenge_exact_source_binding_is_unique',
        count(*)::BIGINT
    FROM challenge_rows AS challenge
    WHERE (
        SELECT count(*)
        FROM corpus.v_round3m_round3k_exact_descriptor_source_binding AS exact
        WHERE exact.descriptor_assertion_id =
              challenge.descriptor_assertion_id
          AND exact.competition_descriptor_assertion_id =
              challenge.competition_descriptor_assertion_id
    ) <> 1
    UNION ALL
    SELECT
        'round3m.normalization_challenge_target_set_is_countable',
        count(*)::BIGINT
    FROM challenge_rows AS challenge
    WHERE NOT audit.round3m_professional_label_target_set_is_countable(
        challenge.professional_label_decision_id
    )
    UNION ALL
    SELECT
        'round3m.exact_source_binding_identity_is_unique',
        count(*)::BIGINT
    FROM (
        SELECT descriptor_assertion_id, competition_descriptor_assertion_id
        FROM corpus.v_round3m_round3k_exact_descriptor_source_binding
        GROUP BY descriptor_assertion_id,
                 competition_descriptor_assertion_id
        HAVING count(*) > 1
    ) AS duplicate_binding
    UNION ALL
    SELECT
        'round3m.competition_descriptor_assertion_link_is_unique',
        count(*)::BIGINT
    FROM (
        SELECT competition_descriptor_assertion_id
        FROM corpus.round3m_descriptor_assertion
        WHERE competition_descriptor_assertion_id IS NOT NULL
        GROUP BY competition_descriptor_assertion_id
        HAVING count(*) > 1
    ) AS duplicate_link
    UNION ALL
    SELECT
        'round3m.descriptor_gate_release_payloads_are_exact',
        count(*)::BIGINT
    FROM audit.round3m_descriptor_gate_contract_release AS release
    WHERE release.contract_payload_sha256 IS DISTINCT FROM
          audit.round3m_descriptor_gate_contract_payload_sha256(
              release.gate_version
          )
    UNION ALL
    SELECT
        'round3m.current_descriptor_gate_release_is_exact_v2',
        CASE WHEN count(*) = 1
                   AND bool_and(
                       gate_version = 'round3m-descriptor-gates-v2'
                       AND contract_ordinal = 2
                       AND supersedes_gate_version =
                           'round3m-descriptor-gates-v1'
                   )
             THEN 0 ELSE 1 END::BIGINT
    FROM audit.v_round3m_current_descriptor_gate_contract
    UNION ALL
    SELECT
        'round3m.descriptor_gate_release_shapes_are_exact',
        count(*)::BIGINT
    FROM audit.round3m_descriptor_gate_contract_release AS release
    CROSS JOIN LATERAL (
        SELECT
            count(*) FILTER (WHERE object_type = 'definition') AS definitions,
            count(*) FILTER (WHERE object_type = 'criterion') AS criteria
        FROM (
            SELECT 'definition'::TEXT AS object_type
            FROM audit.round3m_descriptor_gate_definition AS definition
            WHERE definition.gate_version = release.gate_version
            UNION ALL
            SELECT 'criterion'::TEXT
            FROM audit.round3m_descriptor_gate_criterion AS criterion
            WHERE criterion.gate_version = release.gate_version
        ) AS object
    ) AS shape
    WHERE shape.definitions <> 7 OR shape.criteria <> 56
    UNION ALL
    SELECT
        'round3m.descriptor_gate_v2_definition_parity_is_6_plus_1_nontraining',
        CASE WHEN unchanged_count = 6
                   AND exact_changed_count = 1
                   AND nontraining_count = 7
                   AND paired_count = 7
             THEN 0 ELSE 1 END::BIGINT
    FROM definition_parity
    UNION ALL
    SELECT
        'round3m.descriptor_gate_v2_criterion_parity_is_55_plus_1',
        CASE WHEN unchanged_count = 55
                   AND exact_changed_count = 1
                   AND paired_count = 56
             THEN 0 ELSE 1 END::BIGINT
    FROM criterion_parity
    UNION ALL
    SELECT
        'round3m.descriptor_gate_status_is_exact_v2_surface',
        CASE WHEN count(*) = 56
                   AND bool_and(
                       gate_version = 'round3m-descriptor-gates-v2'
                   )
             THEN 0 ELSE 1 END::BIGINT
    FROM audit.v_round3m_descriptor_gate_status
    UNION ALL
    SELECT
        'round3m.descriptor_gate_summary_is_exact_v2_surface',
        CASE WHEN count(*) = 7
                   AND bool_and(
                       gate_version = 'round3m-descriptor-gates-v2'
                   )
             THEN 0 ELSE 1 END::BIGINT
    FROM audit.v_round3m_descriptor_gate
)
SELECT prior.check_key, prior.violation_count, prior.passed
FROM audit.run_round3m_gate_validation_queries_pre_v059() AS prior
UNION ALL
SELECT challenge.check_key,
       challenge.violation_count,
       challenge.violation_count = 0 AS passed
FROM challenge_checks AS challenge
ORDER BY check_key
$run_round3m_gate_validation_queries$;

COMMENT ON FUNCTION audit.run_round3m_gate_validation_queries() IS
    'Round 3M gate invariants including qualified-human normalization challenge identity, immutable payload evidence, and metric/criterion parity.';

COMMIT;
