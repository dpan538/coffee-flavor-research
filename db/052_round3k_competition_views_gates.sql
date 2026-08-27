\set ON_ERROR_STOP on

-- Round 3K truthful counting, rights, readiness, leakage, and scale-gate
-- surfaces.  All counts in this migration are derived from the governed facts
-- introduced by migrations 049--051.  No row in this migration is seed data.

BEGIN;

CREATE VIEW evidence.v_current_professional_rights_decision AS
WITH leaf_decision AS (
    SELECT decision.*
    FROM evidence.professional_rights_decision AS decision
    WHERE NOT EXISTS (
        SELECT 1
        FROM evidence.professional_rights_decision AS successor
        WHERE successor.supersedes_decision_id =
              decision.professional_rights_decision_id
    )
)
SELECT
    leaf_decision.*,
    count(*) OVER (
        PARTITION BY professional_source_snapshot_id
    )::INTEGER AS current_decision_count,
    count(*) OVER (
        PARTITION BY professional_source_snapshot_id
    ) = 1 AS unambiguous_current_decision
FROM leaf_decision;

COMMENT ON VIEW evidence.v_current_professional_rights_decision IS
    'Leaf rights decisions without open/closed conflation. More than one leaf for a snapshot is exposed as ambiguity and is never silently resolved.';

CREATE VIEW corpus.v_current_professional_label_decision AS
WITH leaf_decision AS (
    SELECT decision.*
    FROM corpus.professional_label_decision AS decision
    WHERE NOT EXISTS (
        SELECT 1
        FROM corpus.professional_label_decision AS successor
        WHERE successor.supersedes_decision_id =
              decision.professional_label_decision_id
    )
)
SELECT
    leaf_decision.*,
    count(*) OVER (
        PARTITION BY professional_expression_id
    )::INTEGER AS current_decision_count,
    count(*) OVER (
        PARTITION BY professional_expression_id
    ) = 1 AS unambiguous_current_decision
FROM leaf_decision;

COMMENT ON VIEW corpus.v_current_professional_label_decision IS
    'Current governed label disposition per professional expression; candidate decisions remain candidates and do not become reviewed labels.';

CREATE VIEW evidence.v_round3k_governed_professional_snapshot AS
SELECT
    snapshot.professional_source_snapshot_id,
    snapshot.professional_source_snapshot_key,
    snapshot.professional_source_id,
    snapshot.source_family_key,
    source.professional_source_key,
    source.source_type_code,
    family.canonical_origin_key,
    family.counts_as_independent,
    snapshot.snapshot_sha256,
    snapshot.lawfully_acquired_for_internal_research,
    source.admitted AS source_admitted,
    snapshot.admitted AS snapshot_admitted,
    rights.professional_rights_decision_id,
    rights.current_decision_count,
    rights.public_results_use,
    rights.public_descriptor_use,
    rights.internal_research_use,
    rights.public_derived_release,
    rights.model_research_use,
    rights.commercial_model_use,
    privacy.decision_state_code AS privacy_decision_state_code,
    source.admitted
      AND snapshot.admitted
      AND snapshot.lawfully_acquired_for_internal_research
      AND family.admitted
      AND family.counts_as_independent
      AND rights.unambiguous_current_decision
      AND rights.internal_research_use = 'ALLOWED'
      AND NOT EXISTS (
          SELECT 1
          FROM audit.professional_duplicate_group_member AS member
          JOIN audit.professional_duplicate_group AS duplicate_group
            ON duplicate_group.professional_duplicate_group_id =
               member.professional_duplicate_group_id
          WHERE member.professional_source_snapshot_id =
                snapshot.professional_source_snapshot_id
            AND (
                NOT duplicate_group.reviewed
                OR member.member_role_code <> 'CANONICAL'
            )
      ) AS eligible_for_observed_research,
    source.admitted
      AND snapshot.admitted
      AND snapshot.lawfully_acquired_for_internal_research
      AND family.admitted
      AND family.counts_as_independent
      AND rights.unambiguous_current_decision
      AND rights.internal_research_use = 'ALLOWED'
      AND rights.model_research_use = 'ALLOWED'
      AND privacy.decision_state_code = 'ALLOWED'
      AND NOT EXISTS (
          SELECT 1
          FROM audit.professional_duplicate_group_member AS member
          JOIN audit.professional_duplicate_group AS duplicate_group
            ON duplicate_group.professional_duplicate_group_id =
               member.professional_duplicate_group_id
          WHERE member.professional_source_snapshot_id =
                snapshot.professional_source_snapshot_id
            AND (
                NOT duplicate_group.reviewed
                OR member.member_role_code <> 'CANONICAL'
            )
      ) AS eligible_for_model_research
FROM evidence.professional_source_snapshot AS snapshot
JOIN evidence.professional_source AS source
  ON source.professional_source_id = snapshot.professional_source_id
JOIN evidence.source_family AS family
  ON family.source_family_key = snapshot.source_family_key
LEFT JOIN evidence.v_current_professional_rights_decision AS rights
  ON rights.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id
LEFT JOIN evidence.professional_privacy_decision AS privacy
  ON privacy.professional_source_snapshot_id =
     snapshot.professional_source_snapshot_id;

CREATE VIEW competition.v_round3k_countable_descriptor_assertion AS
SELECT
    assertion.descriptor_assertion_id,
    assertion.descriptor_assertion_key,
    assertion.preparation_service_id,
    assertion.judge_observation_id,
    assertion.panel_id,
    assertion.structured_score_id,
    assertion.organizer_published_note_id,
    assertion.assertion_type_code,
    assertion.evidence_tier_code,
    assertion.language_tag,
    assertion.raw_phrase,
    assertion.source_defined_descriptor_key,
    assertion.professional_source_snapshot_id,
    assertion.professional_source_file_id,
    assertion.source_locator,
    assertion.derived_from_judge_observations,
    score.numeric_value AS linked_numeric_score_value,
    score.text_value AS linked_text_score_value
FROM competition.descriptor_assertion AS assertion
LEFT JOIN competition.structured_score AS score
  ON score.structured_score_id = assertion.structured_score_id
WHERE assertion.evidence_tier_code IN ('P1', 'P2')
  AND assertion.assertion_type_code IN (
      'OFFICIAL_JUDGE_DESCRIPTOR',
      'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR',
      'OFFICIAL_AGGREGATED_DESCRIPTOR',
      'OFFICIAL_STRUCTURED_SCORE'
  )
  AND (
      assertion.raw_phrase IS NOT NULL
      OR assertion.source_defined_descriptor_key IS NOT NULL
  )
  AND NOT assertion.semantic_inference_used
  AND NOT (
      assertion.assertion_type_code = 'OFFICIAL_STRUCTURED_SCORE'
      AND score.numeric_value IS NOT NULL
  );

COMMENT ON VIEW competition.v_round3k_countable_descriptor_assertion IS
    'Explicit P1/P2 descriptor text or source-defined descriptor identities. Numeric OFFICIAL_STRUCTURED_SCORE rows are deliberately excluded from descriptor counts.';

CREATE VIEW competition.v_round3k_professional_payload AS
SELECT
    'STRUCTURED_SCORE'::TEXT AS payload_kind_code,
    score.structured_score_id AS payload_id,
    score.preparation_service_id,
    score.professional_source_snapshot_id,
    score.professional_source_file_id,
    score.evidence_tier_code,
    CASE
        WHEN score.evidence_tier_code = 'P1'
            THEN 'P1_JUDGE_STRUCTURED_SCORE'
        ELSE 'P2_AGGREGATED_STRUCTURED_SCORE'
    END::TEXT AS evidence_class_code,
    NULL::BIGINT AS descriptor_assertion_id,
    FALSE AS increments_descriptor_assertion_count,
    score.source_locator
FROM competition.structured_score AS score
UNION ALL
SELECT
    'DESCRIPTOR_ASSERTION',
    assertion.descriptor_assertion_id,
    assertion.preparation_service_id,
    assertion.professional_source_snapshot_id,
    assertion.professional_source_file_id,
    assertion.evidence_tier_code,
    CASE assertion.assertion_type_code
        WHEN 'OFFICIAL_JUDGE_DESCRIPTOR'
            THEN 'P1_JUDGE_DESCRIPTOR'
        WHEN 'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR'
            THEN 'P1_PANEL_CONSENSUS_DESCRIPTOR'
        WHEN 'OFFICIAL_AGGREGATED_DESCRIPTOR'
            THEN 'P2_AGGREGATED_DESCRIPTOR'
        ELSE assertion.evidence_tier_code || '_TEXT_STRUCTURED_SCORE'
    END,
    assertion.descriptor_assertion_id,
    TRUE,
    assertion.source_locator
FROM competition.v_round3k_countable_descriptor_assertion AS assertion;

CREATE VIEW competition.v_round3k_service_coffee_identity AS
WITH service_identity AS (
    SELECT
        service.preparation_service_id,
        lot.coffee_identity_id
    FROM competition.preparation_service AS service
    JOIN competition.lot AS lot
      ON lot.lot_id = service.lot_id
     AND lot.lifecycle_status_code = 'active'
    JOIN competition.coffee_identity AS coffee
      ON coffee.coffee_identity_id = lot.coffee_identity_id
     AND coffee.lifecycle_status_code = 'active'
    WHERE service.lot_id IS NOT NULL
    UNION
    SELECT
        service.preparation_service_id,
        link.coffee_identity_id
    FROM competition.preparation_service AS service
    JOIN competition.entry_coffee_link AS link
      ON link.entry_id = service.entry_id
     AND link.linkage_status_code IN (
         'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
     )
     AND link.link_role_code <> 'REPORTED_UNRESOLVED'
    JOIN competition.coffee_identity AS coffee
      ON coffee.coffee_identity_id = link.coffee_identity_id
     AND coffee.lifecycle_status_code = 'active'
    WHERE service.entry_id IS NOT NULL
)
SELECT
    preparation_service_id,
    array_agg(
        DISTINCT coffee_identity_id ORDER BY coffee_identity_id
    ) AS coffee_identity_ids
FROM service_identity
GROUP BY preparation_service_id;

CREATE VIEW competition.v_round3k_observed_core_professional_record AS
WITH eligible_payload AS (
    SELECT payload.*, snapshot.source_family_key
    FROM competition.v_round3k_professional_payload AS payload
    JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
      ON snapshot.professional_source_snapshot_id =
         payload.professional_source_snapshot_id
     AND snapshot.eligible_for_observed_research
), payload_by_service AS (
    SELECT
        preparation_service_id,
        array_agg(
            DISTINCT professional_source_snapshot_id
            ORDER BY professional_source_snapshot_id
        ) AS source_snapshot_ids,
        array_agg(
            DISTINCT source_family_key ORDER BY source_family_key
        ) AS source_family_keys,
        array_agg(
            DISTINCT evidence_tier_code ORDER BY evidence_tier_code
        ) AS evidence_tier_codes,
        array_agg(
            DISTINCT evidence_class_code ORDER BY evidence_class_code
        ) AS evidence_class_codes,
        count(*) FILTER (
            WHERE payload_kind_code = 'STRUCTURED_SCORE'
        )::BIGINT AS structured_score_count,
        count(DISTINCT descriptor_assertion_id) FILTER (
            WHERE increments_descriptor_assertion_count
        )::BIGINT AS professional_descriptor_assertion_count,
        bool_or(evidence_tier_code = 'P1') AS has_p1_evidence,
        bool_or(evidence_tier_code = 'P2') AS has_p2_evidence
    FROM eligible_payload
    GROUP BY preparation_service_id
), fresh_provenance AS (
    SELECT
        evidence_record.preparation_service_id,
        array_agg(
            DISTINCT evidence_record.professional_source_snapshot_id
            ORDER BY evidence_record.professional_source_snapshot_id
        ) AS fresh_source_snapshot_ids
    FROM competition.preparation_service_evidence AS evidence_record
    JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
      ON snapshot.professional_source_snapshot_id =
         evidence_record.professional_source_snapshot_id
     AND snapshot.eligible_for_observed_research
    WHERE evidence_record.explicit_fresh_preparation_evidence
    GROUP BY evidence_record.preparation_service_id
)
SELECT
    service.preparation_service_id,
    service.preparation_service_key,
    service.series_id,
    service.edition_id,
    edition.edition_year,
    service.category_id,
    service.round_id,
    service.entry_id,
    service.lot_id,
    CASE WHEN service.entry_id IS NOT NULL THEN 'ENTRY' ELSE 'LOT' END
        AS subject_kind_code,
    coalesce(service.entry_id, service.lot_id) AS subject_id,
    service.entry_service_key,
    concat_ws(
        ':',
        CASE WHEN service.entry_id IS NOT NULL THEN 'entry' ELSE 'lot' END,
        coalesce(service.entry_id, service.lot_id)::TEXT,
        service.entry_service_key
    ) AS distinct_entry_service_key,
    service.repeat_of_preparation_service_id,
    service.repeat_relationship_code,
    service.rule_version_id,
    service.preparation_taxonomy_code,
    service.c0_source_status_code,
    service.c0_preparation_concept_id,
    service.source_native_roast_status_code,
    service.c1_mapping_status_code,
    service.reviewed_c1_roast_category_id,
    service.c1_mapping_basis_code,
    identity_link.coffee_identity_ids,
    payload.source_snapshot_ids,
    fresh.fresh_source_snapshot_ids,
    payload.source_family_keys,
    payload.evidence_tier_codes,
    payload.evidence_class_codes,
    payload.has_p1_evidence,
    payload.has_p2_evidence,
    payload.structured_score_count,
    payload.professional_descriptor_assertion_count,
    service.source_native_roast_status_code IN (
        'REPORTED', 'REPORTED_UNRESOLVED'
    ) OR service.c1_mapping_status_code = 'REVIEWED'
      OR roast_batch.source_native_roast_status_code IN (
          'REPORTED', 'REPORTED_UNRESOLVED'
      )
      OR roast_batch.c1_mapping_status_code = 'REVIEWED'
        AS has_direct_c1_or_source_roast,
    service.c1_mapping_status_code = 'REVIEWED'
      OR roast_batch.c1_mapping_status_code = 'REVIEWED'
        AS has_reviewed_c1_mapping,
    service.c1_mapping_status_code = 'REPORTED_UNRESOLVED'
      OR roast_batch.c1_mapping_status_code = 'REPORTED_UNRESOLVED'
        AS has_unresolved_c1,
    service.preparation_taxonomy_code IN (
        'FILTER', 'POUR_OVER', 'COMPETITION_BATCH_FILTER'
    ) AS is_filter_or_pour_over,
    service.preparation_taxonomy_code IN (
        'ESPRESSO', 'ESPRESSO_PLUS_WATER'
    ) AS is_espresso,
    service.preparation_taxonomy_code IN (
        'STANDARDIZED_CUPPING', 'GREEN_COMPETITION_CUPPING',
        'PRODUCTION_ROAST_CUPPING'
    ) AS is_professional_cupping_or_roasting
FROM competition.preparation_service AS service
JOIN competition.series AS series
  ON series.series_id = service.series_id
JOIN competition.edition AS edition
  ON edition.edition_id = service.edition_id
JOIN competition.category AS category
  ON category.category_id = service.category_id
JOIN competition.round AS round_record
  ON round_record.round_id = service.round_id
JOIN payload_by_service AS payload
  ON payload.preparation_service_id = service.preparation_service_id
JOIN fresh_provenance AS fresh
  ON fresh.preparation_service_id = service.preparation_service_id
JOIN competition.v_round3k_service_coffee_identity AS identity_link
  ON identity_link.preparation_service_id = service.preparation_service_id
LEFT JOIN competition.roast_batch AS roast_batch
  ON roast_batch.roast_batch_id = service.roast_batch_id
WHERE service.lifecycle_status_code = 'active'
  AND series.lifecycle_status_code = 'active'
  AND edition.lifecycle_status_code = 'active'
  AND category.lifecycle_status_code = 'active'
  AND round_record.lifecycle_status_code = 'active'
  AND service.black_coffee_core_candidate
  AND service.fresh_preparation_confirmed
  AND service.fresh_preparation_status_code = 'CONFIRMED_FRESH'
  AND NOT service.milk_auxiliary
  AND (
      service.entry_id IS NULL
      OR EXISTS (
          SELECT 1
          FROM competition.entry AS entry_record
          WHERE entry_record.entry_id = service.entry_id
            AND entry_record.lifecycle_status_code = 'active'
      )
  )
  AND (
      service.lot_id IS NULL
      OR EXISTS (
          SELECT 1
          FROM competition.lot AS lot_record
          WHERE lot_record.lot_id = service.lot_id
            AND lot_record.lifecycle_status_code = 'active'
      )
  )
  AND NOT EXISTS (
      SELECT 1
      FROM audit.professional_duplicate_group_member AS member
      JOIN audit.professional_duplicate_group AS duplicate_group
        ON duplicate_group.professional_duplicate_group_id =
           member.professional_duplicate_group_id
      WHERE member.preparation_service_id = service.preparation_service_id
        AND (
            NOT duplicate_group.reviewed
            OR member.member_role_code <> 'CANONICAL'
        )
  )
  AND (
      service.repeat_of_preparation_service_id IS NULL
      OR service.repeat_relationship_code NOT IN (
          'AUCTION_REPUBLICATION', 'ROASTER_REPUBLICATION'
      )
         AND EXISTS (
             SELECT 1
             FROM audit.professional_repeat_audit AS repeat_audit
             WHERE repeat_audit.preparation_service_id =
                   service.preparation_service_id
               AND repeat_audit.repeats_preparation_service_id =
                   service.repeat_of_preparation_service_id
               AND repeat_audit.repeat_relationship_code =
                   service.repeat_relationship_code
               AND repeat_audit.relationship_status_code IN (
                   'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
               )
         )
  )
  AND lower(coalesce(service.service_metadata ->> 'record_origin', ''))
      NOT IN ('synthetic', 'structural_test_fixture')
  AND lower(coalesce(service.service_metadata ->> 'fixture_class', '')) <>
      'structural_test_fixture'
  AND lower(coalesce(service.service_metadata ->> 'synthetic', 'false'))
      NOT IN ('true', '1', 'yes')
  AND lower(coalesce(
      service.service_metadata ->> 'core_count_eligible', 'true'
  )) NOT IN ('false', '0', 'no');

COMMENT ON VIEW competition.v_round3k_observed_core_professional_record IS
    'One observed-core row per effective preparation service. Judge observations, scores, descriptors, snapshots, mirrors, and unlinked repeats cannot multiply this grain.';

CREATE VIEW competition.v_round3k_model_eligible_core_professional_record AS
SELECT
    observed.*,
    candidate.candidate_ids AS professional_training_candidate_ids,
    candidate.task_codes AS professional_training_task_codes
FROM competition.v_round3k_observed_core_professional_record AS observed
JOIN LATERAL (
    SELECT
        array_agg(
            DISTINCT training_candidate.professional_training_candidate_id
            ORDER BY training_candidate.professional_training_candidate_id
        ) AS candidate_ids,
        array_agg(
            DISTINCT training_candidate.task_code
            ORDER BY training_candidate.task_code
        ) AS task_codes
    FROM ml.professional_training_candidate AS training_candidate
    JOIN evidence.v_current_professional_rights_decision AS rights
      ON rights.professional_rights_decision_id =
         training_candidate.professional_rights_decision_id
     AND rights.unambiguous_current_decision
     AND rights.internal_research_use = 'ALLOWED'
     AND rights.model_research_use = 'ALLOWED'
    JOIN evidence.professional_privacy_decision AS privacy
      ON privacy.professional_source_snapshot_id =
         rights.professional_source_snapshot_id
     AND privacy.decision_state_code = 'ALLOWED'
    WHERE training_candidate.preparation_service_id =
          observed.preparation_service_id
      AND training_candidate.included
      AND training_candidate.candidate_status_code = 'ELIGIBLE'
      AND training_candidate.provenance_complete
      AND training_candidate.rights_complete
      AND training_candidate.integrity_complete
      AND rights.professional_source_snapshot_id =
          ANY(observed.source_snapshot_ids)
    HAVING count(*) > 0
) AS candidate ON TRUE
WHERE NOT EXISTS (
    SELECT 1
    FROM unnest(observed.source_snapshot_ids) AS credited(snapshot_id)
    LEFT JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
      ON snapshot.professional_source_snapshot_id = credited.snapshot_id
     AND snapshot.eligible_for_model_research
    WHERE snapshot.professional_source_snapshot_id IS NULL
);

COMMENT ON VIEW competition.v_round3k_model_eligible_core_professional_record IS
    'Observed core restricted to affirmative, current model-research rights, allowed privacy treatment, and included provenance/rights/integrity-complete training candidates.';

CREATE VIEW competition.v_round3k_auxiliary_professional_record AS
WITH auxiliary_descriptor AS (
    SELECT
        assertion.preparation_service_id,
        assertion.professional_source_snapshot_id,
        assertion.evidence_tier_code,
        assertion.descriptor_assertion_id
    FROM competition.descriptor_assertion AS assertion
    JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
      ON snapshot.professional_source_snapshot_id =
         assertion.professional_source_snapshot_id
     AND snapshot.eligible_for_observed_research
    WHERE assertion.evidence_tier_code IN ('P3', 'P4')
      AND (
          assertion.raw_phrase IS NOT NULL
          OR assertion.source_defined_descriptor_key IS NOT NULL
      )
      AND NOT assertion.semantic_inference_used
    UNION ALL
    SELECT
        payload.preparation_service_id,
        payload.professional_source_snapshot_id,
        payload.evidence_tier_code,
        payload.descriptor_assertion_id
    FROM competition.v_round3k_professional_payload AS payload
    JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
      ON snapshot.professional_source_snapshot_id =
         payload.professional_source_snapshot_id
     AND snapshot.eligible_for_observed_research
    JOIN competition.preparation_service AS service
      ON service.preparation_service_id = payload.preparation_service_id
     AND service.milk_auxiliary
), grouped AS (
    SELECT
        preparation_service_id,
        array_agg(
            DISTINCT professional_source_snapshot_id
            ORDER BY professional_source_snapshot_id
        ) AS source_snapshot_ids,
        array_agg(
            DISTINCT evidence_tier_code ORDER BY evidence_tier_code
        ) AS evidence_tier_codes,
        count(DISTINCT descriptor_assertion_id) FILTER (
            WHERE descriptor_assertion_id IS NOT NULL
        )::BIGINT AS descriptor_assertion_count
    FROM auxiliary_descriptor
    GROUP BY preparation_service_id
)
SELECT
    service.preparation_service_id,
    service.preparation_service_key,
    service.series_id,
    service.edition_id,
    service.category_id,
    service.round_id,
    service.entry_id,
    service.lot_id,
    service.entry_service_key,
    service.preparation_taxonomy_code,
    service.milk_auxiliary,
    grouped.source_snapshot_ids,
    grouped.evidence_tier_codes,
    grouped.descriptor_assertion_count
FROM grouped
JOIN competition.preparation_service AS service
  ON service.preparation_service_id = grouped.preparation_service_id
WHERE service.lifecycle_status_code = 'active'
  AND NOT EXISTS (
      SELECT 1
      FROM competition.v_round3k_observed_core_professional_record AS core
      WHERE core.preparation_service_id = service.preparation_service_id
  );

COMMENT ON VIEW competition.v_round3k_auxiliary_professional_record IS
    'P3/P4 terminology/candidate evidence and milk-coffee auxiliary evidence. These rows never contribute to observed- or model-eligible core gates.';

CREATE VIEW audit.v_round3k_source_concentration AS
WITH observed_credit AS (
    SELECT
        observed.preparation_service_id,
        family.source_family_key,
        1::NUMERIC / cardinality(observed.source_family_keys)::NUMERIC
            AS fractional_credit
    FROM competition.v_round3k_observed_core_professional_record AS observed
    CROSS JOIN LATERAL unnest(
        observed.source_family_keys
    ) AS family(source_family_key)
), model_credit AS (
    SELECT
        model.preparation_service_id,
        family.source_family_key,
        1::NUMERIC / cardinality(model.source_family_keys)::NUMERIC
            AS fractional_credit
    FROM competition.v_round3k_model_eligible_core_professional_record AS model
    CROSS JOIN LATERAL unnest(
        model.source_family_keys
    ) AS family(source_family_key)
), observed_family AS (
    SELECT
        source_family_key,
        count(DISTINCT preparation_service_id)::BIGINT AS record_reach_count,
        sum(fractional_credit) AS credited_record_count
    FROM observed_credit
    GROUP BY source_family_key
), model_family AS (
    SELECT
        source_family_key,
        count(DISTINCT preparation_service_id)::BIGINT AS record_reach_count,
        sum(fractional_credit) AS credited_record_count
    FROM model_credit
    GROUP BY source_family_key
), family_key AS (
    SELECT source_family_key FROM observed_family
    UNION
    SELECT source_family_key FROM model_family
), totals AS (
    SELECT
        (SELECT count(*) FROM
            competition.v_round3k_observed_core_professional_record
        )::NUMERIC AS observed_total,
        (SELECT count(*) FROM
            competition.v_round3k_model_eligible_core_professional_record
        )::NUMERIC AS model_total
)
SELECT
    family_key.source_family_key,
    family.canonical_origin_key,
    family.counts_as_independent,
    coalesce(observed_family.record_reach_count, 0) AS
        observed_record_reach_count,
    coalesce(observed_family.credited_record_count, 0)::NUMERIC AS
        observed_credited_record_count,
    CASE WHEN totals.observed_total = 0 THEN 0::NUMERIC
         ELSE coalesce(
             observed_family.credited_record_count, 0
         ) / totals.observed_total END AS observed_source_family_share,
    coalesce(model_family.record_reach_count, 0) AS
        model_eligible_record_reach_count,
    coalesce(model_family.credited_record_count, 0)::NUMERIC AS
        model_eligible_credited_record_count,
    CASE WHEN totals.model_total = 0 THEN 0::NUMERIC
         ELSE coalesce(
             model_family.credited_record_count, 0
         ) / totals.model_total END AS model_eligible_source_family_share
FROM family_key
JOIN evidence.source_family AS family
  ON family.source_family_key = family_key.source_family_key
LEFT JOIN observed_family
  ON observed_family.source_family_key = family_key.source_family_key
LEFT JOIN model_family
  ON model_family.source_family_key = family_key.source_family_key
CROSS JOIN totals;

CREATE VIEW audit.v_round3k_category_c1_metrics AS
SELECT
    observed.category_id,
    observed.reviewed_c1_roast_category_id,
    count(*)::BIGINT AS observed_core_record_count,
    count(*) FILTER (
        WHERE observed.has_direct_c1_or_source_roast
    )::BIGINT AS direct_c1_or_source_roast_record_count,
    count(*) FILTER (
        WHERE observed.has_reviewed_c1_mapping
    )::BIGINT AS c1_reviewed_mapping_count,
    count(*) FILTER (
        WHERE observed.has_unresolved_c1
    )::BIGINT AS c1_unresolved_count,
    count(*) FILTER (
        WHERE observed.is_filter_or_pour_over
    )::BIGINT AS filter_or_pour_over_record_count,
    count(*) FILTER (
        WHERE observed.is_espresso
    )::BIGINT AS espresso_record_count,
    count(*) FILTER (
        WHERE observed.is_professional_cupping_or_roasting
    )::BIGINT AS professional_cupping_or_roasting_record_count
FROM competition.v_round3k_observed_core_professional_record AS observed
GROUP BY observed.category_id, observed.reviewed_c1_roast_category_id;

COMMENT ON VIEW audit.v_round3k_category_c1_metrics IS
    'Category and C1 inventory. Preparation category never supplies roast depth; C1/source-roast counts use only direct source-native roast or governed C1 facts.';

CREATE VIEW audit.v_round3k_label_readiness AS
WITH governed_expression AS (
    SELECT
        expression.professional_expression_id,
        expression.normalized_phrase,
        assertion.preparation_service_id,
        decision.professional_label_decision_id,
        decision.label_disposition_code,
        decision.decision_method_code,
        decision.provenance_complete,
        decision.expert_review_complete
    FROM corpus.professional_expression AS expression
    JOIN competition.v_round3k_countable_descriptor_assertion AS assertion
      ON assertion.descriptor_assertion_id =
         expression.descriptor_assertion_id
    JOIN competition.v_round3k_model_eligible_core_professional_record AS model
      ON model.preparation_service_id = assertion.preparation_service_id
     AND assertion.professional_source_snapshot_id =
         ANY(model.source_snapshot_ids)
    JOIN corpus.v_current_professional_label_decision AS decision
      ON decision.professional_expression_id =
         expression.professional_expression_id
     AND decision.unambiguous_current_decision
     AND decision.decision_status_code = 'FINAL'
     AND NOT decision.candidate_only
), candidate_service AS (
    SELECT DISTINCT candidate.preparation_service_id
    FROM ml.professional_training_candidate AS candidate
    JOIN competition.v_round3k_model_eligible_core_professional_record AS model
      ON model.preparation_service_id = candidate.preparation_service_id
    WHERE candidate.included
      AND candidate.task_code IN (
          'DESCRIPTOR_NORMALIZATION', 'DESCRIPTOR_ASSOCIATION'
      )
), candidate_provenance AS (
    SELECT
        candidate_service.preparation_service_id,
        EXISTS (
            SELECT 1
            FROM governed_expression AS expression
            WHERE expression.preparation_service_id =
                  candidate_service.preparation_service_id
              AND expression.provenance_complete
        )
        AND NOT EXISTS (
            SELECT 1
            FROM competition.v_round3k_countable_descriptor_assertion AS assertion
            JOIN competition.v_round3k_model_eligible_core_professional_record AS model
              ON model.preparation_service_id =
                 candidate_service.preparation_service_id
             AND model.preparation_service_id = assertion.preparation_service_id
             AND assertion.professional_source_snapshot_id =
                 ANY(model.source_snapshot_ids)
            WHERE NOT EXISTS (
                SELECT 1
                FROM corpus.professional_expression AS expression
                JOIN corpus.v_current_professional_label_decision AS decision
                  ON decision.professional_expression_id =
                     expression.professional_expression_id
                 AND decision.unambiguous_current_decision
                 AND decision.decision_status_code = 'FINAL'
                 AND NOT decision.candidate_only
                 AND decision.provenance_complete
                WHERE expression.descriptor_assertion_id =
                      assertion.descriptor_assertion_id
            )
        ) AS provenance_complete
    FROM candidate_service
), coassertion AS (
    SELECT
        count(*)::BIGINT AS event_count,
        count(DISTINCT snapshot.source_family_key)::BIGINT AS family_count
    FROM corpus.professional_coassertion_event AS event
    JOIN competition.v_round3k_model_eligible_core_professional_record AS model
      ON model.preparation_service_id = event.preparation_service_id
    JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
      ON snapshot.professional_source_snapshot_id =
         event.professional_source_snapshot_id
     AND snapshot.eligible_for_model_research
    JOIN competition.v_round3k_countable_descriptor_assertion AS left_assertion
      ON left_assertion.descriptor_assertion_id =
         event.left_descriptor_assertion_id
    JOIN competition.v_round3k_countable_descriptor_assertion AS right_assertion
      ON right_assertion.descriptor_assertion_id =
         event.right_descriptor_assertion_id
    WHERE NOT event.absence_is_negative
)
SELECT
    count(DISTINCT preparation_service_id) FILTER (
        WHERE label_disposition_code IN (
            'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET',
            'RANGE_LEVEL_TARGET'
        ) AND provenance_complete
    )::BIGINT AS reviewed_positive_record_count,
    count(DISTINCT preparation_service_id) FILTER (
        WHERE label_disposition_code = 'MULTI_CANONICAL_TARGET'
          AND provenance_complete
    )::BIGINT AS multi_target_record_count,
    count(DISTINCT preparation_service_id) FILTER (
        WHERE label_disposition_code IN ('ABSTAIN', 'UNRESOLVED')
          AND provenance_complete
    )::BIGINT AS abstention_or_unresolved_record_count,
    count(DISTINCT preparation_service_id) FILTER (
        WHERE label_disposition_code IN (
            'AMBIGUOUS_TARGET', 'CONTRADICTORY_TARGET'
        ) AND provenance_complete
    )::BIGINT AS ambiguous_or_conflicting_record_count,
    count(*) FILTER (
        WHERE label_disposition_code IN (
            'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET',
            'RANGE_LEVEL_TARGET'
        ) AND provenance_complete
    )::BIGINT AS reviewed_positive_professional_expression_instance_count,
    count(DISTINCT normalized_phrase) FILTER (
        WHERE label_disposition_code IN (
            'EXACT_CANONICAL_TARGET', 'MULTI_CANONICAL_TARGET',
            'RANGE_LEVEL_TARGET'
        ) AND provenance_complete
    )::BIGINT AS unique_reviewed_professional_lexical_form_count,
    count(*) FILTER (
        WHERE label_disposition_code = 'MULTI_CANONICAL_TARGET'
          AND provenance_complete
    )::BIGINT AS multi_target_expression_count,
    count(*) FILTER (
        WHERE label_disposition_code IN ('ABSTAIN', 'UNRESOLVED')
          AND provenance_complete
    )::BIGINT AS abstention_or_unresolved_expression_count,
    count(*) FILTER (
        WHERE label_disposition_code IN (
            'AMBIGUOUS_TARGET', 'CONTRADICTORY_TARGET'
        ) AND provenance_complete
    )::BIGINT AS ambiguous_or_conflicting_expression_count,
    CASE
        WHEN (SELECT count(*) FROM candidate_provenance) = 0
            THEN 0::NUMERIC
        ELSE (
            SELECT count(*) FILTER (WHERE provenance_complete)::NUMERIC
            FROM candidate_provenance
        ) / (SELECT count(*)::NUMERIC FROM candidate_provenance)
    END AS training_label_provenance_rate,
    coalesce((SELECT event_count FROM coassertion), 0)::BIGINT AS
        p1_p2_descriptor_coassertion_event_count,
    coalesce((SELECT family_count FROM coassertion), 0)::BIGINT AS
        independent_coassertion_source_family_count,
    coalesce(bool_or(
        decision_method_code = 'QUALIFIED_REVIEW'
        AND expert_review_complete
    ), FALSE) AS expert_review_performed
FROM governed_expression;

CREATE VIEW audit.v_round3k_split_leakage AS
WITH selected_plan AS (
    SELECT plan.*
    FROM ml.professional_split_plan AS plan
    WHERE plan.lifecycle_status_code IN ('FROZEN', 'CANDIDATE')
    ORDER BY
        (plan.lifecycle_status_code = 'FROZEN') DESC,
        plan.plan_version DESC,
        plan.professional_split_plan_id DESC
    LIMIT 1
), assigned AS (
    SELECT
        assignment.professional_training_candidate_id,
        candidate.preparation_service_id,
        assignment.partition_code,
        model.coffee_identity_ids,
        model.source_snapshot_ids
    FROM selected_plan AS plan
    JOIN ml.professional_split_assignment AS assignment
      ON assignment.professional_split_plan_id =
         plan.professional_split_plan_id
    JOIN ml.professional_training_candidate AS candidate
      ON candidate.professional_training_candidate_id =
         assignment.professional_training_candidate_id
     AND candidate.included
    JOIN competition.v_round3k_model_eligible_core_professional_record AS model
      ON model.preparation_service_id = candidate.preparation_service_id
), coffee_leak AS (
    SELECT coffee_identity_id
    FROM assigned
    CROSS JOIN LATERAL unnest(
        assigned.coffee_identity_ids
    ) AS identity_record(coffee_identity_id)
    GROUP BY coffee_identity_id
    HAVING count(DISTINCT partition_code) > 1
), duplicate_assignment AS (
    SELECT DISTINCT
        duplicate_group.professional_duplicate_group_id,
        duplicate_group.duplicate_type_code,
        assigned.partition_code
    FROM audit.professional_duplicate_group AS duplicate_group
    JOIN audit.professional_duplicate_group_member AS member
      ON member.professional_duplicate_group_id =
         duplicate_group.professional_duplicate_group_id
    JOIN assigned
      ON assigned.preparation_service_id = member.preparation_service_id
      OR member.professional_source_snapshot_id =
         ANY(assigned.source_snapshot_ids)
    WHERE duplicate_group.reviewed
), duplicate_leak AS (
    SELECT professional_duplicate_group_id, duplicate_type_code
    FROM duplicate_assignment
    GROUP BY professional_duplicate_group_id, duplicate_type_code
    HAVING count(DISTINCT partition_code) > 1
), held_out_group AS (
    SELECT split_group.split_group_kind_code, split_group.split_group_key
    FROM selected_plan AS plan
    JOIN ml.professional_split_group AS split_group
      ON split_group.professional_split_plan_id =
         plan.professional_split_plan_id
    JOIN ml.professional_split_group_member AS member
      ON member.professional_split_group_id =
         split_group.professional_split_group_id
    JOIN ml.professional_split_assignment AS assignment
      ON assignment.professional_split_plan_id =
         plan.professional_split_plan_id
     AND assignment.professional_training_candidate_id =
         member.professional_training_candidate_id
    GROUP BY split_group.split_group_kind_code, split_group.split_group_key
    HAVING count(*) > 0
       AND bool_and(assignment.partition_code = 'HELD_OUT')
), model_candidate AS (
    SELECT DISTINCT candidate.professional_training_candidate_id
    FROM competition.v_round3k_model_eligible_core_professional_record AS model
    JOIN ml.professional_training_candidate AS candidate
      ON candidate.preparation_service_id = model.preparation_service_id
     AND candidate.included
)
SELECT
    (SELECT professional_split_plan_id FROM selected_plan) AS
        professional_split_plan_id,
    (SELECT professional_split_plan_key FROM selected_plan) AS
        professional_split_plan_key,
    coalesce((SELECT count(*) FROM held_out_group
        WHERE split_group_kind_code = 'COMPETITION_FAMILY'), 0)::BIGINT AS
        held_out_competition_family_count,
    coalesce((SELECT count(*) FROM held_out_group
        WHERE split_group_kind_code = 'COMPETITION_YEAR'), 0)::BIGINT AS
        held_out_competition_year_count,
    coalesce((SELECT count(*) FROM coffee_leak), 0)::BIGINT AS
        cross_split_coffee_identity_leak_count,
    coalesce((SELECT count(*) FROM duplicate_leak
        WHERE duplicate_type_code <> 'MIRROR_SOURCE'), 0)::BIGINT AS
        cross_split_duplicate_leak_count,
    coalesce((SELECT count(*) FROM duplicate_leak
        WHERE duplicate_type_code = 'MIRROR_SOURCE'), 0)::BIGINT AS
        cross_split_mirror_leak_count,
    coalesce((
        SELECT count(*)
        FROM model_candidate AS candidate
        WHERE NOT EXISTS (
            SELECT 1
            FROM selected_plan AS plan
            JOIN ml.professional_split_assignment AS assignment
              ON assignment.professional_split_plan_id =
                 plan.professional_split_plan_id
             AND assignment.professional_training_candidate_id =
                 candidate.professional_training_candidate_id
        )
    ), 0)::BIGINT AS unassigned_model_candidate_count;

CREATE VIEW audit.v_round3k_professional_corpus_metrics AS
WITH observed AS (
    SELECT *
    FROM competition.v_round3k_observed_core_professional_record
), model AS (
    SELECT *
    FROM competition.v_round3k_model_eligible_core_professional_record
), auxiliary AS (
    SELECT *
    FROM competition.v_round3k_auxiliary_professional_record
), record_snapshot AS (
    SELECT
        observed.preparation_service_id,
        snapshot_id
    FROM observed
    CROSS JOIN LATERAL unnest(
        observed.source_snapshot_ids || observed.fresh_source_snapshot_ids
    ) AS snapshot(snapshot_id)
    UNION
    SELECT
        observed.preparation_service_id,
        payload.professional_source_snapshot_id
    FROM observed
    JOIN competition.v_round3k_professional_payload AS payload
      ON payload.preparation_service_id = observed.preparation_service_id
    UNION
    SELECT
        observed.preparation_service_id,
        source_evidence.professional_source_snapshot_id
    FROM observed
    JOIN competition.preparation_service_evidence AS source_evidence
      ON source_evidence.preparation_service_id =
         observed.preparation_service_id
), provenance_by_record AS (
    SELECT
        observed.preparation_service_id,
        cardinality(observed.fresh_source_snapshot_ids) > 0 AS fresh_complete,
        NOT EXISTS (
            SELECT 1
            FROM competition.v_round3k_professional_payload AS payload
            LEFT JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
              ON snapshot.professional_source_snapshot_id =
                 payload.professional_source_snapshot_id
             AND snapshot.eligible_for_observed_research
            WHERE payload.preparation_service_id =
                  observed.preparation_service_id
              AND snapshot.professional_source_snapshot_id IS NULL
        ) AS source_complete,
        NOT EXISTS (
            SELECT 1
            FROM record_snapshot AS credited
            LEFT JOIN evidence.v_current_professional_rights_decision AS rights
              ON rights.professional_source_snapshot_id = credited.snapshot_id
             AND rights.unambiguous_current_decision
            WHERE credited.preparation_service_id =
                  observed.preparation_service_id
              AND rights.professional_rights_decision_id IS NULL
        ) AS rights_complete,
        NOT EXISTS (
            SELECT 1
            FROM record_snapshot AS credited
            JOIN evidence.professional_source_file AS source_file
              ON source_file.professional_source_snapshot_id =
                 credited.snapshot_id
             AND source_file.retention_state_code = 'LOCAL_RETAINED'
            WHERE credited.preparation_service_id =
                  observed.preparation_service_id
              AND (
                  NOT source_file.hash_verified
                  OR source_file.declared_sha256 <>
                     source_file.verified_sha256
              )
        ) AS source_file_hash_complete,
        NOT EXISTS (
            SELECT 1
            FROM competition.v_round3k_countable_descriptor_assertion AS assertion
            WHERE assertion.preparation_service_id =
                  observed.preparation_service_id
              AND assertion.professional_source_snapshot_id =
                  ANY(observed.source_snapshot_ids)
              AND (
                  assertion.source_locator = ''
                  OR assertion.assertion_type_code =
                     'OFFICIAL_JUDGE_DESCRIPTOR'
                     AND assertion.judge_observation_id IS NULL
                  OR assertion.assertion_type_code =
                     'OFFICIAL_PANEL_CONSENSUS_DESCRIPTOR'
                     AND assertion.panel_id IS NULL
                  OR assertion.assertion_type_code =
                     'OFFICIAL_AGGREGATED_DESCRIPTOR'
                     AND assertion.organizer_published_note_id IS NULL
              )
        ) AS descriptor_lineage_complete
    FROM observed
), provenance AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (WHERE fresh_complete)::BIGINT AS fresh_numerator,
        count(*) FILTER (WHERE source_complete)::BIGINT AS source_numerator,
        count(*) FILTER (WHERE rights_complete)::BIGINT AS rights_numerator,
        count(*) FILTER (WHERE source_file_hash_complete)::BIGINT AS
            hash_numerator,
        count(*) FILTER (WHERE descriptor_lineage_complete)::BIGINT AS
            descriptor_lineage_numerator
    FROM provenance_by_record
), descriptor_count AS (
    SELECT count(DISTINCT assertion.descriptor_assertion_id)::BIGINT AS value
    FROM observed
    JOIN competition.v_round3k_countable_descriptor_assertion AS assertion
      ON assertion.preparation_service_id = observed.preparation_service_id
     AND assertion.professional_source_snapshot_id =
         ANY(observed.source_snapshot_ids)
), judge_count AS (
    SELECT count(DISTINCT observation.judge_observation_id)::BIGINT AS value
    FROM observed
    JOIN competition.judge_observation AS observation
      ON observation.preparation_service_id = observed.preparation_service_id
), coffee_count AS (
    SELECT count(DISTINCT identity_record.coffee_identity_id)::BIGINT AS value
    FROM observed
    CROSS JOIN LATERAL unnest(
        observed.coffee_identity_ids
    ) AS identity_record(coffee_identity_id)
), evidence_class_count AS (
    SELECT count(DISTINCT class.evidence_class_code)::BIGINT AS value
    FROM observed
    CROSS JOIN LATERAL unnest(
        observed.evidence_class_codes
    ) AS class(evidence_class_code)
), independent_family_count AS (
    SELECT count(DISTINCT family.source_family_key)::BIGINT AS value
    FROM observed
    CROSS JOIN LATERAL unnest(
        observed.source_family_keys
    ) AS family(source_family_key)
), rebuild AS (
    SELECT coalesce(max(attestation.clean_rebuild_count), 0)::BIGINT AS value
    FROM audit.round3k_checkpoint AS checkpoint
    JOIN audit.research_database_reproducibility_attestation AS attestation
      ON attestation.freeze_version = checkpoint.frozen_release_version
     AND attestation.hashes_match_across_rebuilds
     AND attestation.committed_artifacts_match
-- Gate 4 needs a separate forensic act, not merely the ordinary Gate 3
-- inventories.  A forensic duplicate/repeat inventory is therefore required
-- to use the explicit round3k.forensic.* registry-key namespace.
), artifact AS (
    SELECT
        count(DISTINCT artifact_type_code) FILTER (
            WHERE artifact_type_code IN (
                'SOURCE_MANIFEST', 'SOURCE_HASHES',
                'NORMALIZED_INVENTORY', 'RIGHTS_INVENTORY',
                'DUPLICATE_REPEAT_INVENTORY', 'LABEL_INVENTORY',
                'SPLIT_CANDIDATE',
                'TRAINING_CORPUS_CANDIDATE_MANIFEST'
            )
        ) = 8 AS training_inventory_complete,
        count(DISTINCT artifact_type_code) FILTER (
            WHERE artifact_type_code IN (
                'SOURCE_MANIFEST', 'SOURCE_HASHES',
                'NORMALIZED_INVENTORY', 'RIGHTS_INVENTORY',
                'DUPLICATE_REPEAT_INVENTORY', 'LABEL_INVENTORY',
                'SPLIT_CANDIDATE'
            )
        ) = 7
        AND count(*) FILTER (
            WHERE artifact_type_code = 'DUPLICATE_REPEAT_INVENTORY'
              AND round3k_artifact_key LIKE 'round3k.forensic.%'
        ) > 0 AS forensic_audit_evidence_present
    FROM audit.round3k_artifact_registry
), synthetic AS (
    SELECT count(*)::BIGINT AS value
    FROM competition.preparation_service AS service
    WHERE service.lifecycle_status_code = 'active'
      AND service.black_coffee_core_candidate
      AND (
          lower(coalesce(service.service_metadata ->> 'record_origin', ''))
              IN ('synthetic', 'structural_test_fixture')
          OR lower(coalesce(service.service_metadata ->> 'fixture_class', ''))
              = 'structural_test_fixture'
          OR lower(coalesce(
              service.service_metadata ->> 'synthetic', 'false'
          )) IN ('true', '1', 'yes')
          OR lower(coalesce(
              service.service_metadata ->> 'core_count_eligible', 'true'
          )) IN ('false', '0', 'no')
      )
), inferred_descriptor AS (
    SELECT count(*)::BIGINT AS value
    FROM competition.descriptor_assertion AS assertion
    WHERE assertion.evidence_tier_code IN ('P1', 'P2')
      AND (
          assertion.semantic_inference_used
          OR lower(coalesce(
              assertion.assertion_metadata ->> 'machine_generated', 'false'
          )) IN ('true', '1', 'yes')
          OR lower(coalesce(
              assertion.assertion_metadata ->> 'llm_generated', 'false'
          )) IN ('true', '1', 'yes')
          OR lower(coalesce(
              assertion.assertion_metadata ->> 'project_inferred', 'false'
          )) IN ('true', '1', 'yes')
      )
), unlinked_repeat AS (
    SELECT count(*)::BIGINT AS value
    FROM competition.preparation_service AS service
    WHERE service.lifecycle_status_code = 'active'
      AND service.black_coffee_core_candidate
      AND service.repeat_of_preparation_service_id IS NOT NULL
      AND (
          service.repeat_relationship_code IN (
              'AUCTION_REPUBLICATION', 'ROASTER_REPUBLICATION'
          )
          OR NOT EXISTS (
              SELECT 1
              FROM audit.professional_repeat_audit AS repeat_audit
              WHERE repeat_audit.preparation_service_id =
                    service.preparation_service_id
                AND repeat_audit.repeats_preparation_service_id =
                    service.repeat_of_preparation_service_id
                AND repeat_audit.repeat_relationship_code =
                    service.repeat_relationship_code
                AND repeat_audit.relationship_status_code IN (
                    'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
                )
          )
      )
), base AS (
    SELECT
        (SELECT count(*) FROM observed)::BIGINT AS observed_count,
        (SELECT count(*) FROM model)::BIGINT AS model_count,
        (SELECT count(*) FROM auxiliary)::BIGINT AS auxiliary_count
)
SELECT
    (SELECT count(DISTINCT series_id) FROM observed)::BIGINT AS
        competition_series_count,
    (SELECT count(DISTINCT edition_id) FROM observed)::BIGINT AS
        competition_edition_count,
    independent_family_count.value AS
        independent_professional_source_family_count,
    base.observed_count AS observed_core_professional_record_count,
    base.model_count AS model_eligible_core_professional_record_count,
    base.auxiliary_count AS auxiliary_professional_record_count,
    coffee_count.value AS unique_coffee_identity_count,
    (SELECT count(DISTINCT distinct_entry_service_key) FROM observed)::BIGINT
        AS unique_entry_service_count,
    base.observed_count AS effective_round_service_record_count,
    CASE WHEN base.observed_count = 0 THEN 0::NUMERIC
         ELSE (SELECT count(DISTINCT distinct_entry_service_key)::NUMERIC
               FROM observed) / base.observed_count::NUMERIC END AS
        distinct_entry_service_ratio,
    (SELECT count(*) FROM observed WHERE has_p1_evidence)::BIGINT AS
        p1_record_count,
    (SELECT count(*) FROM observed WHERE has_p2_evidence)::BIGINT AS
        p2_record_count,
    (SELECT count(*) FROM auxiliary
     WHERE 'P3' = ANY(evidence_tier_codes))::BIGINT AS p3_record_count,
    (SELECT count(*) FROM auxiliary
     WHERE 'P4' = ANY(evidence_tier_codes))::BIGINT AS p4_record_count,
    judge_count.value AS judge_observation_count,
    descriptor_count.value AS professional_descriptor_assertion_count,
    audit.v_round3k_label_readiness.p1_p2_descriptor_coassertion_event_count,
    (SELECT count(*) FROM observed WHERE is_filter_or_pour_over)::BIGINT AS
        filter_or_pour_over_record_count,
    (SELECT count(*) FROM observed WHERE is_espresso)::BIGINT AS
        espresso_record_count,
    (SELECT count(*) FROM observed
     WHERE is_professional_cupping_or_roasting)::BIGINT AS
        professional_cupping_or_roasting_record_count,
    (SELECT count(*) FROM auxiliary WHERE milk_auxiliary)::BIGINT AS
        milk_auxiliary_record_count,
    (SELECT count(*) FROM observed
     WHERE has_direct_c1_or_source_roast)::BIGINT AS
        direct_c1_or_source_roast_record_count,
    (SELECT count(*) FROM observed WHERE has_reviewed_c1_mapping)::BIGINT AS
        c1_reviewed_mapping_count,
    (SELECT count(*) FROM observed WHERE has_unresolved_c1)::BIGINT AS
        c1_unresolved_count,
    evidence_class_count.value AS evidence_class_count,
    audit.v_round3k_label_readiness.reviewed_positive_record_count,
    audit.v_round3k_label_readiness.multi_target_record_count,
    audit.v_round3k_label_readiness.abstention_or_unresolved_record_count,
    audit.v_round3k_label_readiness.ambiguous_or_conflicting_record_count,
    audit.v_round3k_label_readiness.
        reviewed_positive_professional_expression_instance_count,
    audit.v_round3k_label_readiness.
        unique_reviewed_professional_lexical_form_count,
    audit.v_round3k_label_readiness.multi_target_expression_count,
    audit.v_round3k_label_readiness.
        abstention_or_unresolved_expression_count,
    audit.v_round3k_label_readiness.
        ambiguous_or_conflicting_expression_count,
    audit.v_round3k_label_readiness.
        independent_coassertion_source_family_count,
    coalesce((SELECT max(observed_source_family_share)
              FROM audit.v_round3k_source_concentration), 0)::NUMERIC AS
        largest_observed_source_family_share,
    coalesce((SELECT max(model_eligible_source_family_share)
              FROM audit.v_round3k_source_concentration), 0)::NUMERIC AS
        largest_model_eligible_source_family_share,
    audit.v_round3k_split_leakage.held_out_competition_family_count,
    audit.v_round3k_split_leakage.held_out_competition_year_count,
    audit.v_round3k_split_leakage.cross_split_coffee_identity_leak_count,
    audit.v_round3k_split_leakage.cross_split_duplicate_leak_count,
    audit.v_round3k_split_leakage.cross_split_mirror_leak_count,
    audit.v_round3k_split_leakage.unassigned_model_candidate_count,
    CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
         ELSE provenance.fresh_numerator::NUMERIC /
              provenance.denominator::NUMERIC END AS
        fresh_preparation_provenance_rate,
    CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
         ELSE provenance.source_numerator::NUMERIC /
              provenance.denominator::NUMERIC END AS source_provenance_rate,
    CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
         ELSE provenance.hash_numerator::NUMERIC /
              provenance.denominator::NUMERIC END AS
        source_file_hash_completeness,
    CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
         ELSE provenance.rights_numerator::NUMERIC /
              provenance.denominator::NUMERIC END AS
        rights_decision_completeness,
    CASE WHEN base.model_count = 0 THEN 0::NUMERIC
         ELSE (
             SELECT count(*)::NUMERIC
             FROM model
             WHERE NOT EXISTS (
                 SELECT 1
                 FROM unnest(model.source_snapshot_ids) AS credited(snapshot_id)
                 LEFT JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
                   ON snapshot.professional_source_snapshot_id =
                      credited.snapshot_id
                  AND snapshot.eligible_for_model_research
                 WHERE snapshot.professional_source_snapshot_id IS NULL
             )
         ) / base.model_count::NUMERIC END AS model_research_rights_rate,
    audit.v_round3k_label_readiness.training_label_provenance_rate,
    CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
         ELSE provenance.descriptor_lineage_numerator::NUMERIC /
              provenance.denominator::NUMERIC END AS
        descriptor_assertion_lineage_rate,
    (SELECT count(DISTINCT adapter_source_kind)
     FROM audit.round3k_acquisition_batch
     WHERE lifecycle_status_code = 'COMPLETE'
       AND adapter_status_code = 'PASS')::BIGINT AS generic_adapter_count,
    TRUE AS deduplication_implemented,
    base.observed_count > 0
      AND provenance.fresh_numerator = provenance.denominator AS
        fresh_preparation_linkage_complete,
    base.observed_count > 0
      AND provenance.descriptor_lineage_numerator = provenance.denominator AS
        descriptor_assertion_lineage_complete,
    rebuild.value AS clean_postgres_rebuild_count,
    artifact.training_inventory_complete
      AND rebuild.value >= 2 AS training_corpus_reproducible,
    artifact.forensic_audit_evidence_present,
    synthetic.value AS synthetic_core_record_count,
    inferred_descriptor.value AS inferred_professional_descriptor_count,
    unlinked_repeat.value AS unlinked_repeat_count,
    least(
        CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
             ELSE provenance.fresh_numerator::NUMERIC /
                  provenance.denominator::NUMERIC END,
        CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
             ELSE provenance.source_numerator::NUMERIC /
                  provenance.denominator::NUMERIC END,
        CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
             ELSE provenance.hash_numerator::NUMERIC /
                  provenance.denominator::NUMERIC END,
        CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
             ELSE provenance.rights_numerator::NUMERIC /
                  provenance.denominator::NUMERIC END,
        CASE WHEN provenance.denominator = 0 THEN 0::NUMERIC
             ELSE provenance.descriptor_lineage_numerator::NUMERIC /
                  provenance.denominator::NUMERIC END
    ) AS provenance_rate,
    audit.v_round3k_label_readiness.expert_review_performed
FROM base
CROSS JOIN coffee_count
CROSS JOIN judge_count
CROSS JOIN descriptor_count
CROSS JOIN evidence_class_count
CROSS JOIN independent_family_count
CROSS JOIN provenance
CROSS JOIN rebuild
CROSS JOIN artifact
CROSS JOIN synthetic
CROSS JOIN inferred_descriptor
CROSS JOIN unlinked_repeat
CROSS JOIN audit.v_round3k_label_readiness
CROSS JOIN audit.v_round3k_split_leakage;

COMMENT ON VIEW audit.v_round3k_professional_corpus_metrics IS
    'Single-row Round 3K metric surface. Empty denominators produce zero, never a vacuous 1.0, so every scale gate fails at zero.';

CREATE VIEW audit.v_round3k_scale_gate_criteria AS
WITH metric AS (
    SELECT * FROM audit.v_round3k_professional_corpus_metrics
), criterion AS (
    SELECT row_value.*
    FROM metric
    CROSS JOIN LATERAL (VALUES
        ('GATE_0_1000', 'OBSERVED_CORE_PROFESSIONAL_RECORD_COUNT', '>=',
         1000::NUMERIC, NULL::BOOLEAN, '1000', 'effective_round_service_records', TRUE,
         metric.observed_core_professional_record_count::NUMERIC, NULL::BOOLEAN),
        ('GATE_0_1000', 'INDEPENDENT_PROFESSIONAL_SOURCE_FAMILY_COUNT', '>=',
         3, NULL, '3', 'source_families', TRUE,
         metric.independent_professional_source_family_count::NUMERIC, NULL),
        ('GATE_0_1000', 'GENERIC_ADAPTER_COUNT', '>=',
         2, NULL, '2', 'adapters', TRUE,
         metric.generic_adapter_count::NUMERIC, NULL),
        ('GATE_0_1000', 'DEDUPLICATION_IMPLEMENTED', '=',
         NULL, TRUE, 'true', 'boolean', TRUE,
         NULL, metric.deduplication_implemented),
        ('GATE_0_1000', 'FRESH_PREPARATION_LINKAGE_COMPLETE', '=',
         NULL, TRUE, 'true', 'boolean', TRUE,
         NULL, metric.fresh_preparation_linkage_complete),
        ('GATE_0_1000', 'DESCRIPTOR_ASSERTION_LINEAGE_COMPLETE', '=',
         NULL, TRUE, 'true', 'boolean', TRUE,
         NULL, metric.descriptor_assertion_lineage_complete),
        ('GATE_0_1000', 'CLEAN_POSTGRES_REBUILD_COUNT', '>=',
         2, NULL, '2', 'rebuilds', TRUE,
         metric.clean_postgres_rebuild_count::NUMERIC, NULL),

        ('GATE_1_3000', 'OBSERVED_CORE_PROFESSIONAL_RECORD_COUNT', '>=',
         3000, NULL, '3000', 'effective_round_service_records', TRUE,
         metric.observed_core_professional_record_count::NUMERIC, NULL),
        ('GATE_1_3000', 'INDEPENDENT_PROFESSIONAL_SOURCE_FAMILY_COUNT', '>=',
         6, NULL, '6', 'source_families', TRUE,
         metric.independent_professional_source_family_count::NUMERIC, NULL),
        ('GATE_1_3000', 'LARGEST_SOURCE_FAMILY_SHARE', '<=',
         0.50, NULL, '0.50', 'ratio', TRUE,
         metric.largest_observed_source_family_share, NULL),
        ('GATE_1_3000', 'PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT', '>=',
         15000, NULL, '15000', 'assertions', TRUE,
         metric.professional_descriptor_assertion_count::NUMERIC, NULL),

        ('GATE_2_7000', 'OBSERVED_CORE_PROFESSIONAL_RECORD_COUNT', '>=',
         7000, NULL, '7000', 'effective_round_service_records', TRUE,
         metric.observed_core_professional_record_count::NUMERIC, NULL),
        ('GATE_2_7000', 'PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT', '>=',
         40000, NULL, '40000', 'assertions', TRUE,
         metric.professional_descriptor_assertion_count::NUMERIC, NULL),
        ('GATE_2_7000', 'INDEPENDENT_PROFESSIONAL_SOURCE_FAMILY_COUNT', '>=',
         12, NULL, '12', 'source_families', TRUE,
         metric.independent_professional_source_family_count::NUMERIC, NULL),
        ('GATE_2_7000', 'COMPETITION_EDITION_COUNT', '>=',
         30, NULL, '30', 'editions', TRUE,
         metric.competition_edition_count::NUMERIC, NULL),
        ('GATE_2_7000', 'EVIDENCE_CLASS_COUNT', '>=',
         3, NULL, '3', 'evidence_classes', TRUE,
         metric.evidence_class_count::NUMERIC, NULL),
        ('GATE_2_7000', 'LARGEST_SOURCE_FAMILY_SHARE', '<=',
         0.35, NULL, '0.35', 'ratio', TRUE,
         metric.largest_observed_source_family_share, NULL),
        ('GATE_2_7000', 'FRESH_PREPARATION_PROVENANCE_RATE', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.fresh_preparation_provenance_rate, NULL),
        ('GATE_2_7000', 'SOURCE_PROVENANCE_RATE', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.source_provenance_rate, NULL),
        ('GATE_2_7000', 'SOURCE_FILE_HASH_COMPLETENESS', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.source_file_hash_completeness, NULL),
        ('GATE_2_7000', 'RIGHTS_DECISION_COMPLETENESS', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.rights_decision_completeness, NULL),
        ('GATE_2_7000', 'DISTINCT_ENTRY_SERVICE_RATIO', '>=',
         0.60, NULL, '0.60', 'ratio', TRUE,
         metric.distinct_entry_service_ratio, NULL),
        ('GATE_2_7000', 'HELD_OUT_COMPETITION_FAMILY_COUNT', '>=',
         2, NULL, '2', 'families', TRUE,
         metric.held_out_competition_family_count::NUMERIC, NULL),
        ('GATE_2_7000', 'DIRECT_C1_OR_SOURCE_ROAST_RECORD_COUNT', '>=',
         2000, NULL, '2000', 'records', TRUE,
         metric.direct_c1_or_source_roast_record_count::NUMERIC, NULL),
        ('GATE_2_7000', 'FILTER_OR_POUR_OVER_RECORD_COUNT', '>=',
         1500, NULL, '1500', 'records', TRUE,
         metric.filter_or_pour_over_record_count::NUMERIC, NULL),
        ('GATE_2_7000', 'ESPRESSO_RECORD_COUNT', '>=',
         1500, NULL, '1500', 'records', TRUE,
         metric.espresso_record_count::NUMERIC, NULL),
        ('GATE_2_7000', 'PROFESSIONAL_CUPPING_OR_ROASTING_RECORD_COUNT', '>=',
         1500, NULL, '1500', 'records', TRUE,
         metric.professional_cupping_or_roasting_record_count::NUMERIC, NULL),

        ('GATE_3_10000', 'MODEL_ELIGIBLE_CORE_PROFESSIONAL_RECORD_COUNT', '>=',
         10000, NULL, '10000', 'effective_round_service_records', TRUE,
         metric.model_eligible_core_professional_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'PROFESSIONAL_DESCRIPTOR_ASSERTION_COUNT', '>=',
         60000, NULL, '60000', 'assertions', TRUE,
         metric.professional_descriptor_assertion_count::NUMERIC, NULL),
        ('GATE_3_10000', 'INDEPENDENT_PROFESSIONAL_SOURCE_FAMILY_COUNT', '>=',
         15, NULL, '15', 'source_families', TRUE,
         metric.independent_professional_source_family_count::NUMERIC, NULL),
        ('GATE_3_10000', 'COMPETITION_EDITION_COUNT', '>=',
         50, NULL, '50', 'editions', TRUE,
         metric.competition_edition_count::NUMERIC, NULL),
        ('GATE_3_10000', 'LARGEST_SOURCE_FAMILY_SHARE', '<=',
         0.30, NULL, '0.30', 'ratio', TRUE,
         metric.largest_model_eligible_source_family_share, NULL),
        ('GATE_3_10000', 'DISTINCT_ENTRY_SERVICE_RATIO', '>=',
         0.60, NULL, '0.60', 'ratio', TRUE,
         metric.distinct_entry_service_ratio, NULL),
        ('GATE_3_10000', 'DISTINCT_ENTRY_SERVICE_RATIO_PREFERRED', '>=',
         0.65, NULL, '0.65', 'ratio', FALSE,
         metric.distinct_entry_service_ratio, NULL),
        ('GATE_3_10000', 'HELD_OUT_COMPETITION_FAMILY_COUNT', '>=',
         3, NULL, '3', 'families', TRUE,
         metric.held_out_competition_family_count::NUMERIC, NULL),
        ('GATE_3_10000', 'HELD_OUT_COMPETITION_YEAR_COUNT', '>=',
         1, NULL, '1', 'years', TRUE,
         metric.held_out_competition_year_count::NUMERIC, NULL),
        ('GATE_3_10000', 'DIRECT_C1_OR_SOURCE_ROAST_RECORD_COUNT', '>=',
         4000, NULL, '4000', 'records', TRUE,
         metric.direct_c1_or_source_roast_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'FILTER_OR_POUR_OVER_RECORD_COUNT', '>=',
         2000, NULL, '2000', 'records', TRUE,
         metric.filter_or_pour_over_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'ESPRESSO_RECORD_COUNT', '>=',
         2000, NULL, '2000', 'records', TRUE,
         metric.espresso_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'PROFESSIONAL_CUPPING_OR_ROASTING_RECORD_COUNT', '>=',
         2000, NULL, '2000', 'records', TRUE,
         metric.professional_cupping_or_roasting_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'REVIEWED_POSITIVE_RECORD_COUNT', '>=',
         7000, NULL, '7000', 'records', TRUE,
         metric.reviewed_positive_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'MULTI_TARGET_RECORD_COUNT', '>=',
         1200, NULL, '1200', 'records', TRUE,
         metric.multi_target_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'ABSTENTION_OR_UNRESOLVED_RECORD_COUNT', '>=',
         1000, NULL, '1000', 'records', TRUE,
         metric.abstention_or_unresolved_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'AMBIGUOUS_OR_CONFLICTING_RECORD_COUNT', '>=',
         500, NULL, '500', 'records', TRUE,
         metric.ambiguous_or_conflicting_record_count::NUMERIC, NULL),
        ('GATE_3_10000', 'TRAINING_LABEL_PROVENANCE_RATE', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.training_label_provenance_rate, NULL),
        ('GATE_3_10000', 'MODEL_RESEARCH_RIGHTS_RATE', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.model_research_rights_rate, NULL),
        ('GATE_3_10000', 'CROSS_SPLIT_COFFEE_IDENTITY_LEAK_COUNT', '=',
         0, NULL, '0', 'leaks', TRUE,
         metric.cross_split_coffee_identity_leak_count::NUMERIC, NULL),
        ('GATE_3_10000', 'CROSS_SPLIT_DUPLICATE_LEAK_COUNT', '=',
         0, NULL, '0', 'leaks', TRUE,
         metric.cross_split_duplicate_leak_count::NUMERIC, NULL),
        ('GATE_3_10000', 'CROSS_SPLIT_MIRROR_LEAK_COUNT', '=',
         0, NULL, '0', 'leaks', TRUE,
         metric.cross_split_mirror_leak_count::NUMERIC, NULL),
        ('GATE_3_10000', 'TRAINING_CORPUS_REPRODUCIBLE', '=',
         NULL, TRUE, 'true', 'boolean', TRUE,
         NULL, metric.training_corpus_reproducible),

        ('GATE_3_NORMALIZATION',
         'REVIEWED_POSITIVE_PROFESSIONAL_EXPRESSION_INSTANCE_COUNT', '>=',
         3000, NULL, '3000', 'expression_instances', TRUE,
         metric.reviewed_positive_professional_expression_instance_count::NUMERIC,
         NULL),
        ('GATE_3_NORMALIZATION',
         'UNIQUE_REVIEWED_PROFESSIONAL_LEXICAL_FORM_COUNT', '>=',
         1500, NULL, '1500', 'lexical_forms', TRUE,
         metric.unique_reviewed_professional_lexical_form_count::NUMERIC, NULL),
        ('GATE_3_NORMALIZATION', 'MULTI_TARGET_EXPRESSION_COUNT', '>=',
         500, NULL, '500', 'expressions', TRUE,
         metric.multi_target_expression_count::NUMERIC, NULL),
        ('GATE_3_NORMALIZATION',
         'ABSTENTION_OR_UNRESOLVED_EXPRESSION_COUNT', '>=',
         500, NULL, '500', 'expressions', TRUE,
         metric.abstention_or_unresolved_expression_count::NUMERIC, NULL),
        ('GATE_3_NORMALIZATION',
         'AMBIGUOUS_OR_CONFLICTING_EXPRESSION_COUNT', '>=',
         300, NULL, '300', 'expressions', TRUE,
         metric.ambiguous_or_conflicting_expression_count::NUMERIC, NULL),

        ('GATE_3_ASSOCIATION', 'P1_P2_DESCRIPTOR_COASSERTION_EVENT_COUNT', '>=',
         10000, NULL, '10000', 'coassertion_events', TRUE,
         metric.p1_p2_descriptor_coassertion_event_count::NUMERIC, NULL),
        ('GATE_3_ASSOCIATION',
         'INDEPENDENT_COASSERTION_SOURCE_FAMILY_COUNT', '>=',
         5, NULL, '5', 'source_families', TRUE,
         metric.independent_coassertion_source_family_count::NUMERIC, NULL),

        ('GATE_4_12000', 'OBSERVED_CORE_PROFESSIONAL_RECORD_COUNT', '>=',
         12000, NULL, '12000', 'effective_round_service_records', FALSE,
         metric.observed_core_professional_record_count::NUMERIC, NULL),
        ('GATE_4_12000', 'SYNTHETIC_CORE_RECORD_COUNT', '=',
         0, NULL, '0', 'records', TRUE,
         metric.synthetic_core_record_count::NUMERIC, NULL),
        ('GATE_4_12000', 'INFERRED_PROFESSIONAL_DESCRIPTOR_COUNT', '=',
         0, NULL, '0', 'assertions', TRUE,
         metric.inferred_professional_descriptor_count::NUMERIC, NULL),
        ('GATE_4_12000', 'UNLINKED_REPEAT_COUNT', '=',
         0, NULL, '0', 'repeats', TRUE,
         metric.unlinked_repeat_count::NUMERIC, NULL),
        ('GATE_4_12000', 'PROVENANCE_RATE', '=',
         1.0000, NULL, '1.0000', 'ratio', TRUE,
         metric.provenance_rate, NULL)
    ) AS row_value(
        gate_key, metric_key, operator, required_numeric,
        required_boolean, required_value, unit, hard_gate,
        observed_numeric, observed_boolean
    )
)
SELECT
    gate_key,
    metric_key,
    operator,
    required_value,
    unit,
    hard_gate,
    observed_numeric,
    observed_boolean,
    CASE operator
        WHEN '>=' THEN observed_numeric >= required_numeric
        WHEN '<=' THEN observed_numeric <= required_numeric
        WHEN '=' THEN CASE
            WHEN required_boolean IS NOT NULL
                THEN observed_boolean IS NOT DISTINCT FROM required_boolean
            ELSE observed_numeric = required_numeric
        END
        ELSE FALSE
    END AS criterion_pass
FROM criterion;

CREATE VIEW audit.v_round3k_scale_gate AS
WITH gate_criterion AS (
    SELECT
        gate_key,
        bool_and(criterion_pass) FILTER (WHERE hard_gate) AS
            hard_criteria_pass,
        bool_and(criterion_pass) AS all_listed_criteria_pass
    FROM audit.v_round3k_scale_gate_criteria
    GROUP BY gate_key
), dependency AS (
    SELECT
        coalesce(bool_and(criterion_pass) FILTER (
            WHERE gate_key = 'GATE_3_NORMALIZATION' AND hard_gate
        ), FALSE) AS normalization_pass,
        coalesce(bool_and(criterion_pass) FILTER (
            WHERE gate_key = 'GATE_3_ASSOCIATION' AND hard_gate
        ), FALSE) AS association_pass
    FROM audit.v_round3k_scale_gate_criteria
), metric AS (
    SELECT * FROM audit.v_round3k_professional_corpus_metrics
)
SELECT
    gate_criterion.gate_key,
    gate_criterion.hard_criteria_pass,
    gate_criterion.all_listed_criteria_pass,
    CASE gate_criterion.gate_key
        WHEN 'GATE_3_10000'
            THEN dependency.normalization_pass AND dependency.association_pass
        WHEN 'GATE_4_12000'
            THEN metric.forensic_audit_evidence_present
        ELSE TRUE
    END AS dependency_pass,
    gate_criterion.gate_key = 'GATE_4_12000'
      AND metric.observed_core_professional_record_count >= 12000 AS
        forensic_audit_required,
    CASE gate_criterion.gate_key
        WHEN 'GATE_0_1000' THEN
            metric.observed_core_professional_record_count > 0
            AND gate_criterion.hard_criteria_pass
        WHEN 'GATE_1_3000' THEN
            metric.observed_core_professional_record_count > 0
            AND gate_criterion.hard_criteria_pass
        WHEN 'GATE_2_7000' THEN
            metric.observed_core_professional_record_count > 0
            AND gate_criterion.hard_criteria_pass
        WHEN 'GATE_3_10000' THEN
            metric.model_eligible_core_professional_record_count > 0
            AND gate_criterion.hard_criteria_pass
            AND dependency.normalization_pass
            AND dependency.association_pass
        WHEN 'GATE_3_NORMALIZATION' THEN
            metric.reviewed_positive_professional_expression_instance_count > 0
            AND gate_criterion.hard_criteria_pass
        WHEN 'GATE_3_ASSOCIATION' THEN
            metric.p1_p2_descriptor_coassertion_event_count > 0
            AND gate_criterion.hard_criteria_pass
        WHEN 'GATE_4_12000' THEN
            metric.observed_core_professional_record_count >= 12000
            AND gate_criterion.hard_criteria_pass
            AND metric.forensic_audit_evidence_present
        ELSE FALSE
    END AS gate_pass
FROM gate_criterion
CROSS JOIN dependency
CROSS JOIN metric;

COMMENT ON VIEW audit.v_round3k_scale_gate IS
    'All scale gates fail at zero. At 12,000 observed records forensic_audit_required becomes true and the gate cannot pass without the forensic artifact set plus all four authenticity requirements.';

CREATE FUNCTION audit.run_round3k_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round3k_validation_queries$
WITH checks AS (
    SELECT
        'round3k.current_rights_unambiguous'::TEXT AS check_key,
        count(*)::BIGINT AS violation_count
    FROM evidence.v_current_professional_rights_decision
    WHERE NOT unambiguous_current_decision
    UNION ALL
    SELECT 'round3k.current_labels_unambiguous', count(*)::BIGINT
    FROM corpus.v_current_professional_label_decision
    WHERE NOT unambiguous_current_decision
    UNION ALL
    SELECT 'round3k.numeric_scores_do_not_increment_descriptors',
           count(*)::BIGINT
    FROM competition.v_round3k_countable_descriptor_assertion AS assertion
    WHERE assertion.assertion_type_code = 'OFFICIAL_STRUCTURED_SCORE'
      AND assertion.linked_numeric_score_value IS NOT NULL
    UNION ALL
    SELECT 'round3k.observed_core_effective_service_grain',
           coalesce(sum(duplicate_count - 1), 0)::BIGINT
    FROM (
        SELECT preparation_service_id, count(*) AS duplicate_count
        FROM competition.v_round3k_observed_core_professional_record
        GROUP BY preparation_service_id
        HAVING count(*) > 1
    ) AS duplicate
    UNION ALL
    SELECT 'round3k.observed_core_fresh_black_only', count(*)::BIGINT
    FROM competition.v_round3k_observed_core_professional_record AS observed
    JOIN competition.preparation_service AS service
      ON service.preparation_service_id = observed.preparation_service_id
    WHERE NOT service.fresh_preparation_confirmed
       OR service.milk_auxiliary
       OR NOT service.black_coffee_core_candidate
    UNION ALL
    SELECT 'round3k.observed_and_auxiliary_disjoint', count(*)::BIGINT
    FROM competition.v_round3k_observed_core_professional_record AS observed
    JOIN competition.v_round3k_auxiliary_professional_record AS auxiliary
      ON auxiliary.preparation_service_id = observed.preparation_service_id
    UNION ALL
    SELECT 'round3k.model_eligible_is_observed_subset', count(*)::BIGINT
    FROM competition.v_round3k_model_eligible_core_professional_record AS model
    LEFT JOIN competition.v_round3k_observed_core_professional_record AS observed
      ON observed.preparation_service_id = model.preparation_service_id
    WHERE observed.preparation_service_id IS NULL
    UNION ALL
    SELECT 'round3k.model_eligible_current_model_rights', count(*)::BIGINT
    FROM competition.v_round3k_model_eligible_core_professional_record AS model
    WHERE EXISTS (
        SELECT 1
        FROM unnest(model.source_snapshot_ids) AS credited(snapshot_id)
        LEFT JOIN evidence.v_round3k_governed_professional_snapshot AS snapshot
          ON snapshot.professional_source_snapshot_id = credited.snapshot_id
         AND snapshot.eligible_for_model_research
        WHERE snapshot.professional_source_snapshot_id IS NULL
    )
    UNION ALL
    SELECT 'round3k.no_synthetic_observed_core', count(*)::BIGINT
    FROM competition.v_round3k_observed_core_professional_record AS observed
    JOIN competition.preparation_service AS service
      ON service.preparation_service_id = observed.preparation_service_id
    WHERE lower(coalesce(service.service_metadata ->> 'record_origin', ''))
              IN ('synthetic', 'structural_test_fixture')
       OR lower(coalesce(service.service_metadata ->> 'fixture_class', ''))
              = 'structural_test_fixture'
       OR lower(coalesce(
              service.service_metadata ->> 'synthetic', 'false'
          )) IN ('true', '1', 'yes')
       OR lower(coalesce(
              service.service_metadata ->> 'core_count_eligible', 'true'
          )) IN ('false', '0', 'no')
    UNION ALL
    SELECT 'round3k.no_inferred_professional_descriptors',
           inferred_professional_descriptor_count
    FROM audit.v_round3k_professional_corpus_metrics
    UNION ALL
    SELECT 'round3k.no_unlinked_repeats', unlinked_repeat_count
    FROM audit.v_round3k_professional_corpus_metrics
    UNION ALL
    SELECT 'round3k.no_category_to_roast_shortcut', count(*)::BIGINT
    FROM competition.preparation_service AS service
    WHERE service.c1_mapping_status_code = 'REVIEWED'
      AND service.c1_mapping_basis_code NOT IN (
          'DIRECT_SOURCE_ROAST', 'DIRECT_ROAST_MEASUREMENT',
          'GOVERNED_REVIEW'
      )
    UNION ALL
    SELECT 'round3k.cross_split_coffee_identity_leaks',
           cross_split_coffee_identity_leak_count
    FROM audit.v_round3k_split_leakage
    UNION ALL
    SELECT 'round3k.cross_split_duplicate_leaks',
           cross_split_duplicate_leak_count
    FROM audit.v_round3k_split_leakage
    UNION ALL
    SELECT 'round3k.cross_split_mirror_leaks',
           cross_split_mirror_leak_count
    FROM audit.v_round3k_split_leakage
    UNION ALL
    SELECT 'round3k.zero_population_cannot_pass_scale_gate',
           count(*)::BIGINT
    FROM audit.v_round3k_scale_gate AS gate
    CROSS JOIN audit.v_round3k_professional_corpus_metrics AS metric
    WHERE metric.observed_core_professional_record_count = 0
      AND gate.gate_pass
    UNION ALL
    SELECT 'round3k.12000_requires_forensic_audit',
           CASE
               WHEN metric.observed_core_professional_record_count >= 12000
                AND NOT coalesce(gate.gate_pass, FALSE)
                   THEN 1 ELSE 0
           END::BIGINT
    FROM audit.v_round3k_professional_corpus_metrics AS metric
    LEFT JOIN audit.v_round3k_scale_gate AS gate
      ON gate.gate_key = 'GATE_4_12000'
    UNION ALL
    SELECT 'round3k.no_round3k_model_runs',
           greatest(
               (SELECT count(*) FROM ml.model_run) -
               checkpoint.model_run_count_at_start,
               0
           )::BIGINT
    FROM audit.round3k_checkpoint AS checkpoint
    WHERE checkpoint.checkpoint_key =
          'round3k.professional-competition-corpus'
    UNION ALL
    SELECT 'round3k.no_model_or_embedding_artifacts', count(*)::BIGINT
    FROM audit.round3k_artifact_registry
    WHERE model_weight_artifact OR embedding_artifact
)
SELECT
    checks.check_key,
    checks.violation_count,
    checks.violation_count = 0 AS passed
FROM checks
$run_round3k_validation_queries$;

COMMIT;
