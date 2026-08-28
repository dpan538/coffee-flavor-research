\set ON_ERROR_STOP on

-- Round 3M descriptor-first universes, count surfaces, gates, and saturation
-- instrumentation.  Historical Round 3K record-first gate results remain
-- queryable, but this migration makes their current training authority
-- explicitly false.  No gate in this Round 3M contract authorizes training.

BEGIN;

CREATE VIEW evidence.v_round3m_discovered_source_universe AS
SELECT
    route.source_route_id,
    route.independent_source_family_id,
    route.round3l_source_census_id,
    route.organizer_id,
    route.publication_host,
    route.canonical_url,
    route.route_pattern,
    route.route_disposition,
    route.rights_lineage_id,
    route.mirror_lineage_id,
    route.discovered_at
FROM evidence.round3m_source_route AS route;

CREATE VIEW evidence.v_round3m_rights_assessed_universe AS
SELECT DISTINCT
    route.*
FROM evidence.v_round3m_discovered_source_universe AS route
JOIN evidence.v_round3m_current_descriptor_rights AS rights
  ON rights.source_route_id = route.source_route_id
 AND rights.unambiguous_current_decision;

CREATE VIEW corpus.v_round3m_assertion_level_deinflated AS
SELECT assertion.*
FROM corpus.round3m_descriptor_assertion AS assertion
WHERE assertion.descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
  AND assertion.deduplication_disposition IN (
      'CANONICAL', 'CROSS_OBSERVATION_REPEAT',
      'REPEATED_ROUND', 'REPEATED_PREPARATION_SERVICE'
  );

COMMENT ON VIEW corpus.v_round3m_assertion_level_deinflated IS
    'Atomic observations after exact within-field/within-record and publication/mirror duplicate removal. Cross-observation evidence remains visible at this level.';

CREATE VIEW corpus.v_round3m_record_unique_descriptor AS
WITH ranked AS (
    SELECT
        assertion.*,
        row_number() OVER (
            PARTITION BY
                assertion.effective_record_key,
                coalesce(
                    assertion.normalized_candidate_form,
                    kb.normalize_expression(
                        assertion.source_native_lexical_form
                    ),
                    'sha256:' ||
                        assertion.source_native_lexical_form_sha256
                )
            ORDER BY
                CASE assertion.review_state
                    WHEN 'EXPERT_ADJUDICATED' THEN 1
                    WHEN 'HUMAN_CONFIRMED' THEN 2
                    WHEN 'SOURCE_AUDITED' THEN 3
                    ELSE 4
                END,
                assertion.descriptor_assertion_id
        ) AS record_form_ordinal
    FROM corpus.v_round3m_assertion_level_deinflated AS assertion
)
SELECT *
FROM ranked
WHERE record_form_ordinal = 1;

COMMENT ON VIEW corpus.v_round3m_record_unique_descriptor IS
    'One descriptor form per effective record. Separate observations remain in the assertion-level view but cannot inflate this record-unique surface.';

CREATE VIEW corpus.v_round3m_research_staged_descriptor_universe AS
SELECT
    assertion.*,
    route.independent_source_family_id,
    rights.internal_research_analysis,
    rights.model_research,
    rights.deployment_or_commercial_model
FROM corpus.v_round3m_assertion_level_deinflated AS assertion
JOIN evidence.round3m_source_route AS route
  ON route.source_route_id = assertion.source_route_id
JOIN evidence.v_round3m_current_descriptor_rights AS rights
  ON rights.rights_decision_id = assertion.rights_decision_id
 AND rights.unambiguous_current_decision
WHERE rights.internal_research_analysis = 'AFFIRMATIVE'
  AND NOT assertion.synthetic_generated;

CREATE VIEW corpus.v_round3m_source_audited_descriptor_universe AS
SELECT staged.*
FROM corpus.v_round3m_research_staged_descriptor_universe AS staged
JOIN evidence.round3m_source_schema_signature AS signature
  ON signature.schema_signature_id = staged.schema_signature_id
WHERE staged.review_state IN (
        'SOURCE_AUDITED', 'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
      )
  AND staged.evidence_origin_type NOT IN (
      'GENERIC_ORGANIZER_FIELD_UNKNOWN_AUTHOR',
      'FREQUENCY_CODED_UNKNOWN_ACTOR',
      'FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED',
      'GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED',
      'UNKNOWN_ORIGIN'
  )
  AND signature.validation_status = 'VALIDATED';

CREATE VIEW corpus.v_round3m_human_reviewed_descriptor_universe AS
SELECT audited.*
FROM corpus.v_round3m_source_audited_descriptor_universe AS audited
JOIN audit.round3m_descriptor_review_receipt AS receipt
  ON receipt.review_receipt_id = audited.current_review_receipt_id
 AND receipt.descriptor_assertion_id = audited.descriptor_assertion_id
 AND receipt.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
 AND receipt.receipt_origin_code IN (
     'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
 )
 AND receipt.human_event_evidence_sha256 IS NOT NULL
 AND receipt.decision IN ('CONFIRM_DESCRIPTOR', 'ADJUDICATE_DESCRIPTOR')
WHERE audited.review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED');

CREATE VIEW corpus.v_round3m_model_eligible_descriptor_universe AS
SELECT reviewed.*
FROM corpus.v_round3m_human_reviewed_descriptor_universe AS reviewed
WHERE reviewed.descriptor_class = 'STRICT_FLAVOR'
  AND reviewed.evidence_tier IN ('P1', 'P2')
  AND reviewed.internal_research_analysis = 'AFFIRMATIVE'
  AND reviewed.model_research = 'AFFIRMATIVE'
  AND NOT reviewed.translation_generated
  AND NOT reviewed.synthetic_generated;

CREATE VIEW corpus.v_round3m_deployment_eligible_descriptor_universe AS
SELECT model.*
FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
WHERE model.deployment_or_commercial_model = 'AFFIRMATIVE';

COMMENT ON VIEW corpus.v_round3m_research_staged_descriptor_universe IS
    'Descriptor assertions with affirmative internal-research rights. Rights assessment alone does not place a row here.';
COMMENT ON VIEW corpus.v_round3m_source_audited_descriptor_universe IS
    'Research-staged assertions with a validated schema and resolved source origin. Machine/Codex source audit is not human review.';
COMMENT ON VIEW corpus.v_round3m_human_reviewed_descriptor_universe IS
    'Assertions confirmed by an evidenced actual-human receipt. Machine and Codex provisional decisions cannot enter.';
COMMENT ON VIEW corpus.v_round3m_model_eligible_descriptor_universe IS
    'Human-reviewed, source-native, non-synthetic P1/P2 strict descriptors with affirmative internal and model-research rights.';
COMMENT ON VIEW corpus.v_round3m_deployment_eligible_descriptor_universe IS
    'Model-eligible descriptors with additional affirmative deployment/commercial-model rights.';

CREATE VIEW audit.v_round3m_descriptor_count_surfaces AS
WITH segmented AS (
    SELECT *
    FROM corpus.round3m_descriptor_assertion
    WHERE descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
), assertion_level AS (
    SELECT * FROM corpus.v_round3m_assertion_level_deinflated
), record_level AS (
    SELECT * FROM corpus.v_round3m_record_unique_descriptor
)
SELECT
    (SELECT count(*) FROM segmented)::BIGINT AS
        segmented_atomic_observation_count,
    (SELECT count(*) FROM assertion_level)::BIGINT AS
        assertion_level_deinflated_count,
    (SELECT count(*) FROM record_level)::BIGINT AS
        record_level_unique_descriptor_count,
    (SELECT count(*) FROM assertion_level
     WHERE descriptor_class = 'STRICT_FLAVOR')::BIGINT AS
        strict_flavor_assertion_count,
    (SELECT count(*) FROM assertion_level
     WHERE descriptor_class = 'BROAD_SENSORY')::BIGINT AS
        broad_sensory_assertion_count,
    (SELECT count(DISTINCT effective_record_key)
     FROM assertion_level)::BIGINT AS descriptor_bearing_effective_record_count,
    (SELECT count(*) FROM assertion_level
     WHERE evidence_tier = 'P1')::BIGINT AS p1_descriptor_assertion_count,
    (SELECT count(*) FROM assertion_level
     WHERE evidence_tier = 'P2')::BIGINT AS p2_descriptor_assertion_count,
    (SELECT count(*) FROM assertion_level
     WHERE evidence_tier = 'P3')::BIGINT AS p3_descriptor_assertion_count,
    (SELECT count(*) FROM assertion_level
     WHERE evidence_tier = 'P4')::BIGINT AS p4_descriptor_assertion_count,
    (SELECT count(*) FROM assertion_level
     WHERE evidence_tier = 'UNRESOLVED')::BIGINT AS
        provenance_unresolved_descriptor_assertion_count,
    (SELECT count(DISTINCT source_native_lexical_form_sha256)
     FROM assertion_level
     WHERE NOT translation_generated)::BIGINT AS
        unique_source_native_lexical_form_count,
    (SELECT count(DISTINCT normalized_candidate_form)
     FROM assertion_level
     WHERE normalized_candidate_form IS NOT NULL)::BIGINT AS
        unique_normalized_descriptor_form_count;

CREATE VIEW audit.v_round3m_descriptor_gate_metrics AS
WITH reviewed AS (
    SELECT *
    FROM corpus.v_round3m_human_reviewed_descriptor_universe
    WHERE descriptor_class = 'STRICT_FLAVOR'
      AND evidence_tier IN ('P1', 'P2')
), reviewed_descriptor_record AS (
    SELECT DISTINCT effective_record_key
    FROM corpus.v_round3m_human_reviewed_descriptor_universe
    WHERE evidence_tier IN ('P1', 'P2')
      AND descriptor_class IN ('STRICT_FLAVOR', 'BROAD_SENSORY')
), reviewed_by_family AS (
    SELECT independent_source_family_id, count(*)::BIGINT AS assertion_count
    FROM reviewed
    GROUP BY independent_source_family_id
), rights_rate AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (
            WHERE internal_research_analysis = 'AFFIRMATIVE'
        )::BIGINT AS internal_affirmative_count,
        count(*) FILTER (
            WHERE model_research = 'AFFIRMATIVE'
        )::BIGINT AS model_affirmative_count,
        count(*) FILTER (
            WHERE deployment_or_commercial_model = 'AFFIRMATIVE'
        )::BIGINT AS deployment_affirmative_count
    FROM reviewed
), source_provenance AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (
            WHERE artifact.source_file_sha256 = reviewed.source_file_sha256
              AND artifact.route_index_sha256 =
                  reviewed.route_index_sha256
              AND artifact.source_file_sha256_scope =
                  reviewed.source_file_sha256_scope
              AND artifact.source_file_nonstorage_reason =
                  reviewed.source_file_nonstorage_reason
              AND artifact.source_retrieved_at =
                  reviewed.source_retrieved_at
              AND artifact.source_route_id = reviewed.source_route_id
              AND artifact.schema_signature_id =
                  reviewed.schema_signature_id
              AND signature.validation_status = 'VALIDATED'
              AND reviewed.source_selector_or_locator <> ''
              AND reviewed.source_page_or_record_locator <> ''
              AND reviewed.origin_evidence_locator <> ''
              AND reviewed.source_field_label_sha256 =
                  audit.round3i_utf8_sha256(reviewed.source_field_label)
              AND reviewed.atomic_source_text_sha256 ~ '^[0-9a-f]{64}$'
        )::BIGINT AS complete_count
    FROM reviewed
    JOIN evidence.round3m_source_artifact AS artifact
      ON artifact.source_artifact_id = reviewed.source_artifact_id
    JOIN evidence.round3m_source_schema_signature AS signature
      ON signature.schema_signature_id = reviewed.schema_signature_id
), label_provenance AS (
    SELECT
        count(*)::BIGINT AS denominator,
        count(*) FILTER (
            WHERE reviewed.normalized_candidate_form IS NOT NULL
              AND EXISTS (
                  SELECT 1
                  FROM corpus.round3m_descriptor_label_target AS target
                  WHERE target.descriptor_assertion_id =
                        reviewed.descriptor_assertion_id
                    AND target.review_receipt_id =
                        reviewed.current_review_receipt_id
              )
        )::BIGINT AS complete_count
    FROM reviewed
), label_record_count AS (
    SELECT
        target.output_label_key,
        count(DISTINCT reviewed.effective_record_key)::BIGINT AS record_count
    FROM reviewed
    JOIN corpus.round3m_descriptor_label_target AS target
      ON target.descriptor_assertion_id = reviewed.descriptor_assertion_id
    GROUP BY target.output_label_key
), target_by_record AS (
    SELECT
        reviewed.effective_record_key,
        count(DISTINCT target.output_label_key)::BIGINT AS target_count
    FROM reviewed
    JOIN corpus.round3m_descriptor_label_target AS target
      ON target.descriptor_assertion_id = reviewed.descriptor_assertion_id
    GROUP BY reviewed.effective_record_key
), human_challenge AS (
    SELECT count(DISTINCT assertion.descriptor_assertion_id)::BIGINT AS value
    FROM corpus.round3m_descriptor_assertion AS assertion
    JOIN audit.round3m_descriptor_review_receipt AS receipt
      ON receipt.review_receipt_id = assertion.current_review_receipt_id
     AND receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
    WHERE receipt.review_actor_type IN (
            'HUMAN_REVIEWER', 'EXPERT_REVIEWER'
          )
      AND receipt.receipt_origin_code IN (
            'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
          )
      AND receipt.decision IN ('MARK_AMBIGUOUS', 'MARK_UNRESOLVED', 'ABSTAIN')
), model_pair AS (
    SELECT event.*
    FROM corpus.round3m_coassertion_event AS event
    JOIN corpus.v_round3m_model_eligible_descriptor_universe AS left_assertion
      ON left_assertion.descriptor_assertion_id =
         event.left_descriptor_assertion_id
    JOIN corpus.v_round3m_model_eligible_descriptor_universe AS right_assertion
      ON right_assertion.descriptor_assertion_id =
         event.right_descriptor_assertion_id
), heldout AS (
    SELECT
        count(*) FILTER (
            WHERE holdout.holdout_kind = 'INDEPENDENT_SOURCE_FAMILY'
              AND EXISTS (
                  SELECT 1
                  FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
                  WHERE model.independent_source_family_id =
                        holdout.holdout_value
              )
        )::BIGINT AS family_count,
        count(*) FILTER (
            WHERE holdout.holdout_kind = 'EDITION_YEAR'
              AND EXISTS (
                  SELECT 1
                  FROM corpus.v_round3m_model_eligible_descriptor_universe AS model
                  WHERE model.edition_year::TEXT = holdout.holdout_value
              )
        )::BIGINT AS year_count
    FROM audit.round3m_descriptor_holdout AS holdout
    WHERE holdout.active
), review_blocker AS (
    SELECT count(*)::BIGINT AS value
    FROM corpus.v_round3m_source_audited_descriptor_universe AS audited
    WHERE audited.descriptor_class = 'STRICT_FLAVOR'
      AND audited.evidence_tier IN ('P1', 'P2')
      AND audited.review_state NOT IN (
          'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
      )
), base AS (
    SELECT count(*)::BIGINT AS reviewed_count
    FROM reviewed
)
SELECT
    (SELECT segmented_atomic_observation_count
     FROM audit.v_round3m_descriptor_count_surfaces) AS
        segmented_atomic_observation_count,
    base.reviewed_count AS reviewed_p1_p2_strict_assertion_count,
    (SELECT count(*) FROM reviewed_descriptor_record)::BIGINT AS
        reviewed_descriptor_bearing_record_count,
    (SELECT count(DISTINCT normalized_candidate_form)
     FROM reviewed
     WHERE normalized_candidate_form IS NOT NULL)::BIGINT AS
        reviewed_unique_normalized_form_count,
    (SELECT count(*) FROM reviewed_by_family)::BIGINT AS
        reviewed_independent_source_family_count,
    CASE
        WHEN base.reviewed_count = 0 THEN NULL::NUMERIC
        ELSE coalesce((
            SELECT max(assertion_count)::NUMERIC
            FROM reviewed_by_family
        ), 0) / base.reviewed_count::NUMERIC
    END AS reviewed_largest_family_share,
    (SELECT min(record_count) FROM label_record_count)::NUMERIC AS
        minimum_records_per_output_label,
    (SELECT count(*) FROM target_by_record
     WHERE target_count >= 2)::BIGINT AS reviewed_multi_target_record_count,
    human_challenge.value AS reviewed_ambiguous_or_unresolved_challenge_count,
    (SELECT count(*) FROM model_pair)::BIGINT AS
        supported_within_record_pair_event_count,
    (SELECT count(DISTINCT coassertion_set_key)
     FROM model_pair)::BIGINT AS supported_coassertion_set_count,
    heldout.family_count AS held_out_independent_family_count,
    heldout.year_count AS held_out_edition_year_count,
    CASE WHEN source_provenance.denominator = 0 THEN NULL::NUMERIC
         ELSE source_provenance.complete_count::NUMERIC /
              source_provenance.denominator::NUMERIC END AS
        source_provenance_completeness,
    CASE WHEN label_provenance.denominator = 0 THEN NULL::NUMERIC
         ELSE label_provenance.complete_count::NUMERIC /
              label_provenance.denominator::NUMERIC END AS
        label_provenance_completeness,
    CASE
        WHEN source_provenance.denominator = 0
          OR label_provenance.denominator = 0 THEN NULL::NUMERIC
        ELSE least(
            source_provenance.complete_count::NUMERIC /
                source_provenance.denominator::NUMERIC,
            label_provenance.complete_count::NUMERIC /
                label_provenance.denominator::NUMERIC
        )
    END AS source_and_label_provenance_completeness,
    CASE WHEN rights_rate.denominator = 0 THEN NULL::NUMERIC
         ELSE rights_rate.internal_affirmative_count::NUMERIC /
              rights_rate.denominator::NUMERIC END AS
        internal_research_rights_rate,
    CASE WHEN rights_rate.denominator = 0 THEN NULL::NUMERIC
         ELSE rights_rate.model_affirmative_count::NUMERIC /
              rights_rate.denominator::NUMERIC END AS
        model_research_rights_rate,
    CASE WHEN rights_rate.denominator = 0 THEN NULL::NUMERIC
         ELSE rights_rate.deployment_affirmative_count::NUMERIC /
              rights_rate.denominator::NUMERIC END AS
        deployment_rights_rate,
    (rights_rate.denominator -
     rights_rate.internal_affirmative_count)::BIGINT AS
        internal_research_rights_blocker_count,
    (rights_rate.denominator -
     rights_rate.model_affirmative_count)::BIGINT AS
        model_research_rights_blocker_count,
    (rights_rate.denominator -
     rights_rate.deployment_affirmative_count)::BIGINT AS
        deployment_rights_blocker_count,
    review_blocker.value AS human_review_blocker_count,
    base.reviewed_count > 0
      AND NOT EXISTS (
          SELECT 1
          FROM corpus.round3m_coassertion_event AS event
          JOIN corpus.round3m_descriptor_assertion AS left_assertion
            ON left_assertion.descriptor_assertion_id =
               event.left_descriptor_assertion_id
          JOIN corpus.round3m_descriptor_assertion AS right_assertion
            ON right_assertion.descriptor_assertion_id =
               event.right_descriptor_assertion_id
          WHERE left_assertion.effective_record_key IS DISTINCT FROM
                    right_assertion.effective_record_key
             OR left_assertion.source_observation_key IS DISTINCT FROM
                    right_assertion.source_observation_key
      ) AS record_boundaries_preserved
FROM base
CROSS JOIN rights_rate
CROSS JOIN source_provenance
CROSS JOIN label_provenance
CROSS JOIN human_challenge
CROSS JOIN heldout
CROSS JOIN review_blocker;

CREATE TABLE audit.round3m_descriptor_gate_definition (
    gate_version TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    gate_order INTEGER NOT NULL,
    gate_purpose TEXT NOT NULL,
    default_universe TEXT NOT NULL,
    authorizes_training BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    explanatory_note TEXT NOT NULL,
    CONSTRAINT round3m_descriptor_gate_definition_pk PRIMARY KEY (
        gate_version, gate_name
    ),
    CONSTRAINT round3m_descriptor_gate_definition_order_uq UNIQUE (
        gate_version, gate_order
    ),
    CONSTRAINT round3m_descriptor_gate_definition_text_ck CHECK (
        gate_version = lower(btrim(gate_version))
        AND gate_version ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND gate_name = upper(btrim(gate_name))
        AND gate_name <> ''
        AND gate_order > 0
        AND gate_purpose = btrim(gate_purpose) AND gate_purpose <> ''
        AND default_universe IN (
            'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE',
            'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
            'DEPLOYMENT_ELIGIBLE_DESCRIPTOR_UNIVERSE'
        )
        AND authorizes_training IS FALSE
        AND explanatory_note = btrim(explanatory_note)
        AND explanatory_note <> ''
    )
);

CREATE TABLE audit.round3m_descriptor_gate_criterion (
    gate_version TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    criterion_ordinal INTEGER NOT NULL,
    metric_name TEXT NOT NULL,
    operator TEXT NOT NULL,
    required_numeric NUMERIC,
    required_boolean BOOLEAN,
    required_value TEXT NOT NULL,
    universe TEXT NOT NULL,
    blocker_class TEXT NOT NULL,
    explanatory_note TEXT NOT NULL,
    CONSTRAINT round3m_descriptor_gate_criterion_pk PRIMARY KEY (
        gate_version, gate_name, criterion_ordinal
    ),
    CONSTRAINT round3m_descriptor_gate_criterion_metric_uq UNIQUE (
        gate_version, gate_name, metric_name
    ),
    CONSTRAINT round3m_descriptor_gate_criterion_definition_fk FOREIGN KEY (
        gate_version, gate_name
    ) REFERENCES audit.round3m_descriptor_gate_definition (
        gate_version, gate_name
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT round3m_descriptor_gate_criterion_text_ck CHECK (
        metric_name = upper(btrim(metric_name)) AND metric_name <> ''
        AND operator IN ('>=', '<=', '=')
        AND num_nonnulls(required_numeric, required_boolean) = 1
        AND required_value = btrim(required_value)
        AND required_value <> ''
        AND universe IN (
            'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE',
            'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
            'DEPLOYMENT_ELIGIBLE_DESCRIPTOR_UNIVERSE'
        )
        AND blocker_class IN (
            'DATA', 'RIGHTS', 'REVIEW', 'DATA_AND_REVIEW'
        )
        AND explanatory_note = btrim(explanatory_note)
        AND explanatory_note <> ''
    )
);

INSERT INTO audit.round3m_descriptor_gate_definition (
    gate_version, gate_name, gate_order, gate_purpose, default_universe,
    explanatory_note
) VALUES
('round3m-descriptor-gates-v1', 'GATE_500_EVALUATION', 1,
 'Deterministic lexicon or retrieval evaluation checkpoint',
 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE',
 'Evaluation-only checkpoint; it does not authorize model training.'),
('round3m-descriptor-gates-v1',
 'GATE_2000_EXPERIMENTAL_NORMALIZATION', 2,
 'Experimental descriptor normalization readiness',
 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
 'Future threshold only; separate authorization is required.'),
('round3m-descriptor-gates-v1',
 'GATE_5000_EXPERIMENTAL_RANKING', 3,
 'Experimental 5+3 ranking readiness',
 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
 'Future threshold only; separate authorization is required.'),
('round3m-descriptor-gates-v1',
 'GATE_10000_RESEARCH_NORMALIZATION', 4,
 'Research-grade descriptor normalization readiness',
 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
 'Future threshold only; separate authorization is required.'),
('round3m-descriptor-gates-v1', 'GATE_15000_ASSOCIATION', 5,
 'Association and within-record co-assertion readiness',
 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
 'Future threshold only; separate authorization is required.'),
('round3m-descriptor-gates-v1',
 'GATE_20000_RESEARCH_RANKING', 6,
 'Research-grade 5+3 ranking readiness',
 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE',
 'Future threshold only; separate authorization is required.'),
('round3m-descriptor-gates-v1',
 'GATE_40000_DEPLOYMENT_CANDIDATE', 7,
 'Deployment-candidate ranking readiness',
 'DEPLOYMENT_ELIGIBLE_DESCRIPTOR_UNIVERSE',
 'Future threshold only; separate authorization is required.');

-- Criterion rows are the exact 56 requirements listed in Round 3M sections
-- 9.1 through 9.7. Structural ledger protections remain global constraints;
-- they are not silently added as extra numerical gate criteria.
INSERT INTO audit.round3m_descriptor_gate_criterion (
    gate_version, gate_name, criterion_ordinal, metric_name, operator,
    required_numeric, required_boolean, required_value, universe,
    blocker_class, explanatory_note
)
SELECT
    'round3m-descriptor-gates-v1', values_row.*
FROM (VALUES
('GATE_500_EVALUATION', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 500::NUMERIC, NULL::BOOLEAN, '500', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_500_EVALUATION', 2, 'REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT', '>=', 75, NULL, '75', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Distinct conservative normalized forms.'),
('GATE_500_EVALUATION', 3, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 3, NULL, '3', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Routes and editions sharing an origin remain one family.'),
('GATE_500_EVALUATION', 4, 'SOURCE_AND_LABEL_PROVENANCE_COMPLETENESS', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA_AND_REVIEW', 'Every reviewed assertion has both complete source provenance and receipt-backed label provenance.'),

('GATE_2000_EXPERIMENTAL_NORMALIZATION', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 2000, NULL, '2000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 2, 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT', '>=', 500, NULL, '500', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Descriptor-bearing effective records.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 3, 'REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT', '>=', 100, NULL, '100', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Conservative normalized forms.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 4, 'MINIMUM_RECORDS_PER_OUTPUT_LABEL', '>=', 20, NULL, '20', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Minimum effective-record support per output label.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 5, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 3, NULL, '3', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Independent families.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 6, 'REVIEWED_LARGEST_FAMILY_SHARE', '<=', 0.70, NULL, '0.70', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Largest-family concentration.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 7, 'REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT', '>=', 100, NULL, '100', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human challenge cases.'),
('GATE_2000_EXPERIMENTAL_NORMALIZATION', 8, 'MODEL_RESEARCH_RIGHTS_RATE', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'RIGHTS', 'All counted assertions have affirmative model-research rights.'),

('GATE_5000_EXPERIMENTAL_RANKING', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 5000, NULL, '5000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_5000_EXPERIMENTAL_RANKING', 2, 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT', '>=', 1000, NULL, '1000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Descriptor-bearing effective records.'),
('GATE_5000_EXPERIMENTAL_RANKING', 3, 'REVIEWED_MULTI_TARGET_RECORD_COUNT', '>=', 500, NULL, '500', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Receipt-backed multi-target records.'),
('GATE_5000_EXPERIMENTAL_RANKING', 4, 'SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT', '>=', 2500, NULL, '2500', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Governed within-record pair events.'),
('GATE_5000_EXPERIMENTAL_RANKING', 5, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 4, NULL, '4', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Independent families.'),
('GATE_5000_EXPERIMENTAL_RANKING', 6, 'REVIEWED_LARGEST_FAMILY_SHARE', '<=', 0.60, NULL, '0.60', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Largest-family concentration.'),
('GATE_5000_EXPERIMENTAL_RANKING', 7, 'HELD_OUT_EDITION_YEAR_COUNT', '>=', 1, NULL, '1', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out edition years.'),
('GATE_5000_EXPERIMENTAL_RANKING', 8, 'MODEL_RESEARCH_RIGHTS_RATE', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'RIGHTS', 'Affirmative model-research rights.'),

('GATE_10000_RESEARCH_NORMALIZATION', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 10000, NULL, '10000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_10000_RESEARCH_NORMALIZATION', 2, 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT', '>=', 2500, NULL, '2500', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Descriptor-bearing effective records.'),
('GATE_10000_RESEARCH_NORMALIZATION', 3, 'REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT', '>=', 200, NULL, '200', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Conservative normalized forms.'),
('GATE_10000_RESEARCH_NORMALIZATION', 4, 'MINIMUM_RECORDS_PER_OUTPUT_LABEL', '>=', 50, NULL, '50', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Minimum effective-record support per output label.'),
('GATE_10000_RESEARCH_NORMALIZATION', 5, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 5, NULL, '5', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Independent families.'),
('GATE_10000_RESEARCH_NORMALIZATION', 6, 'REVIEWED_LARGEST_FAMILY_SHARE', '<=', 0.45, NULL, '0.45', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Largest-family concentration.'),
('GATE_10000_RESEARCH_NORMALIZATION', 7, 'HELD_OUT_INDEPENDENT_FAMILY_COUNT', '>=', 2, NULL, '2', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out families.'),
('GATE_10000_RESEARCH_NORMALIZATION', 8, 'HELD_OUT_EDITION_YEAR_COUNT', '>=', 2, NULL, '2', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out years.'),
('GATE_10000_RESEARCH_NORMALIZATION', 9, 'MODEL_RESEARCH_RIGHTS_RATE', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'RIGHTS', 'Affirmative model-research rights.'),

('GATE_15000_ASSOCIATION', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 15000, NULL, '15000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_15000_ASSOCIATION', 2, 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT', '>=', 3000, NULL, '3000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Descriptor-bearing effective records.'),
('GATE_15000_ASSOCIATION', 3, 'SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT', '>=', 10000, NULL, '10000', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Governed within-record pair events.'),
('GATE_15000_ASSOCIATION', 4, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 5, NULL, '5', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Independent families.'),
('GATE_15000_ASSOCIATION', 5, 'RECORD_BOUNDARIES_PRESERVED', '=', NULL, TRUE, 'true', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'No cross-record or unrelated-observation pair.'),
('GATE_15000_ASSOCIATION', 6, 'MODEL_RESEARCH_RIGHTS_RATE', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'RIGHTS', 'Affirmative model-research rights.'),

('GATE_20000_RESEARCH_RANKING', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 20000, NULL, '20000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_20000_RESEARCH_RANKING', 2, 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT', '>=', 4000, NULL, '4000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Descriptor-bearing effective records.'),
('GATE_20000_RESEARCH_RANKING', 3, 'REVIEWED_MULTI_TARGET_RECORD_COUNT', '>=', 2000, NULL, '2000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Receipt-backed multi-target records.'),
('GATE_20000_RESEARCH_RANKING', 4, 'SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT', '>=', 15000, NULL, '15000', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Governed within-record pair events.'),
('GATE_20000_RESEARCH_RANKING', 5, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 6, NULL, '6', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Independent families.'),
('GATE_20000_RESEARCH_RANKING', 6, 'REVIEWED_LARGEST_FAMILY_SHARE', '<=', 0.35, NULL, '0.35', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Largest-family concentration.'),
('GATE_20000_RESEARCH_RANKING', 7, 'HELD_OUT_INDEPENDENT_FAMILY_COUNT', '>=', 2, NULL, '2', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out families.'),
('GATE_20000_RESEARCH_RANKING', 8, 'HELD_OUT_EDITION_YEAR_COUNT', '>=', 2, NULL, '2', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out years.'),
('GATE_20000_RESEARCH_RANKING', 9, 'MODEL_RESEARCH_RIGHTS_RATE', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'RIGHTS', 'Affirmative model-research rights.'),

('GATE_40000_DEPLOYMENT_CANDIDATE', 1, 'REVIEWED_P1_P2_STRICT_ASSERTION_COUNT', '>=', 40000, NULL, '40000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Actual-human reviewed P1/P2 strict assertions.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 2, 'REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT', '>=', 8000, NULL, '8000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Descriptor-bearing effective records.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 3, 'REVIEWED_MULTI_TARGET_RECORD_COUNT', '>=', 5000, NULL, '5000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Receipt-backed multi-target records.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 4, 'SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT', '>=', 40000, NULL, '40000', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Governed within-record pair events.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 5, 'REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT', '>=', 8, NULL, '8', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Independent families.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 6, 'REVIEWED_LARGEST_FAMILY_SHARE', '<=', 0.25, NULL, '0.25', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Largest-family concentration.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 7, 'HELD_OUT_INDEPENDENT_FAMILY_COUNT', '>=', 3, NULL, '3', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out families.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 8, 'HELD_OUT_EDITION_YEAR_COUNT', '>=', 3, NULL, '3', 'MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE', 'DATA', 'Predeclared held-out years.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 9, 'MINIMUM_RECORDS_PER_OUTPUT_LABEL', '>=', 100, NULL, '100', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Minimum production support per output label.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 10, 'SOURCE_PROVENANCE_COMPLETENESS', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'DATA', 'Complete source provenance.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 11, 'LABEL_PROVENANCE_COMPLETENESS', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'REVIEW', 'Complete label provenance.'),
('GATE_40000_DEPLOYMENT_CANDIDATE', 12, 'DEPLOYMENT_RIGHTS_RATE', '=', 1, NULL, '1.0000', 'HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE', 'RIGHTS', 'Affirmative deployment/commercial-model rights.')
) AS values_row(
    gate_name, criterion_ordinal, metric_name, operator,
    required_numeric, required_boolean, required_value, universe,
    blocker_class, explanatory_note
);

CREATE VIEW audit.v_round3m_descriptor_gate_status AS
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
            WHEN required_boolean IS NOT NULL AND observed_boolean IS NULL
                THEN FALSE
            WHEN required_numeric IS NOT NULL AND observed_numeric IS NULL
                THEN FALSE
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
         THEN explanatory_note || ' Observed value is unavailable; NA never passes.'
         ELSE explanatory_note END AS explanatory_note,
    criterion_ordinal,
    operator,
    observed_numeric,
    observed_boolean
FROM evaluated;

CREATE VIEW audit.v_round3m_descriptor_gate AS
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

CREATE TABLE audit.round3m_legacy_gate_deprecation (
    legacy_gate_key TEXT NOT NULL,
    legacy_gate_family TEXT NOT NULL,
    deprecation_status TEXT NOT NULL,
    current_training_authority BOOLEAN NOT NULL DEFAULT FALSE,
    replacement_gate_version TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3m_legacy_gate_deprecation_pk PRIMARY KEY (
        legacy_gate_key
    ),
    CONSTRAINT round3m_legacy_gate_deprecation_ck CHECK (
        legacy_gate_key = upper(btrim(legacy_gate_key))
        AND legacy_gate_key <> ''
        AND legacy_gate_family = 'ROUND3K_RECORD_FIRST'
        AND deprecation_status = 'DEPRECATED_RECORD_FIRST_GATE'
        AND current_training_authority IS FALSE
        AND replacement_gate_version = 'round3m-descriptor-gates-v1'
        AND reason = btrim(reason) AND reason <> ''
    )
);

INSERT INTO audit.round3m_legacy_gate_deprecation (
    legacy_gate_key, legacy_gate_family, deprecation_status,
    replacement_gate_version, reason
) VALUES
('GATE_0_1000', 'ROUND3K_RECORD_FIRST', 'DEPRECATED_RECORD_FIRST_GATE',
 'round3m-descriptor-gates-v1',
 'Record count remains an anti-inflation denominator, not current readiness authority.'),
('GATE_1_3000', 'ROUND3K_RECORD_FIRST', 'DEPRECATED_RECORD_FIRST_GATE',
 'round3m-descriptor-gates-v1',
 'Record count remains an anti-inflation denominator, not current readiness authority.'),
('GATE_2_7000', 'ROUND3K_RECORD_FIRST', 'DEPRECATED_RECORD_FIRST_GATE',
 'round3m-descriptor-gates-v1',
 'The former 7000-record gate cannot authorize current training.'),
('GATE_3_10000', 'ROUND3K_RECORD_FIRST', 'DEPRECATED_RECORD_FIRST_GATE',
 'round3m-descriptor-gates-v1',
 'The former 10000-record gate cannot authorize current training.'),
('GATE_4_12000', 'ROUND3K_RECORD_FIRST', 'DEPRECATED_RECORD_FIRST_GATE',
 'round3m-descriptor-gates-v1',
 'The former 12000-record forensic trigger is replaced by saturation instrumentation.'),
('60000_ASSERTION_GATE', 'ROUND3K_RECORD_FIRST',
 'DEPRECATED_RECORD_FIRST_GATE', 'round3m-descriptor-gates-v1',
 'Undifferentiated assertion volume cannot replace reviewed, tiered, rights-cleared strict descriptors.');

CREATE TABLE audit.round3m_phase_policy (
    policy_version TEXT NOT NULL,
    model_training_allowed BOOLEAN NOT NULL,
    training_corpus_freeze_allowed BOOLEAN NOT NULL,
    record_first_training_authority_allowed BOOLEAN NOT NULL,
    saturation_evaluated BOOLEAN NOT NULL,
    saturation_pass BOOLEAN NOT NULL,
    effective_at TIMESTAMPTZ NOT NULL,
    explanatory_note TEXT NOT NULL,
    CONSTRAINT round3m_phase_policy_pk PRIMARY KEY (policy_version),
    CONSTRAINT round3m_phase_policy_ck CHECK (
        policy_version = 'round3m-policy-v1'
        AND model_training_allowed IS FALSE
        AND training_corpus_freeze_allowed IS FALSE
        AND record_first_training_authority_allowed IS FALSE
        AND saturation_evaluated IS FALSE
        AND saturation_pass IS FALSE
        AND explanatory_note = btrim(explanatory_note)
        AND explanatory_note <> ''
    )
);

INSERT INTO audit.round3m_phase_policy (
    policy_version, model_training_allowed,
    training_corpus_freeze_allowed,
    record_first_training_authority_allowed,
    saturation_evaluated, saturation_pass,
    effective_at, explanatory_note
) VALUES (
    'round3m-policy-v1', FALSE, FALSE, FALSE, FALSE, FALSE,
    '2026-08-28T00:00:00Z',
    'Round 3M validates descriptor infrastructure and a positive evidence pilot; it cannot train a model or freeze a training corpus.'
);

CREATE VIEW audit.v_round3m_legacy_gate_status AS
SELECT
    deprecation.legacy_gate_key,
    deprecation.deprecation_status,
    legacy.gate_pass AS historical_gate_pass,
    deprecation.current_training_authority,
    FALSE AS current_training_authorization_pass,
    deprecation.replacement_gate_version,
    deprecation.reason
FROM audit.round3m_legacy_gate_deprecation AS deprecation
LEFT JOIN audit.v_round3k_scale_gate AS legacy
  ON legacy.gate_key = deprecation.legacy_gate_key;

CREATE VIEW audit.v_current_professional_training_readiness AS
SELECT
    gate.gate_version,
    gate.gate_name,
    gate.universe,
    gate.gate_pass AS descriptor_requirement_pass,
    gate.rights_blocker,
    gate.data_blocker,
    gate.review_blocker,
    gate.has_not_applicable,
    policy.model_training_allowed,
    gate.authorizes_training,
    FALSE AS current_training_authorization_pass
FROM audit.v_round3m_descriptor_gate AS gate
CROSS JOIN audit.round3m_phase_policy AS policy
WHERE policy.policy_version = 'round3m-policy-v1';

COMMENT ON VIEW audit.v_current_professional_training_readiness IS
    'Canonical current readiness surface. Only descriptor-first gates appear; legacy record-first results have no current authority, and Round 3M policy forbids training.';

CREATE TABLE audit.round3m_saturation_increment (
    saturation_increment_id BIGINT GENERATED ALWAYS AS IDENTITY,
    increment_key TEXT NOT NULL,
    increment_sequence INTEGER NOT NULL,
    reviewed_strict_assertion_increment BIGINT NOT NULL,
    new_normalized_forms_per_1000 NUMERIC,
    new_normalized_forms_upper_bound_per_1000 NUMERIC,
    canonical_mapping_rate NUMERIC,
    new_supported_edge_rate NUMERIC,
    weighted_jaccard_graph_stability NUMERIC,
    same_population_duplicate_rate NUMERIC,
    held_out_normalization_delta_percentage_points NUMERIC,
    held_out_family_ndcg8_delta NUMERIC,
    worst_held_out_family_delta NUMERIC,
    preparation_service_coverage_status TEXT NOT NULL,
    source_family_coverage_status TEXT NOT NULL,
    measurement_complete BOOLEAN NOT NULL DEFAULT FALSE,
    measured_at TIMESTAMPTZ NOT NULL,
    measurement_receipt_sha256 TEXT NOT NULL,
    CONSTRAINT round3m_saturation_increment_pk PRIMARY KEY (
        saturation_increment_id
    ),
    CONSTRAINT round3m_saturation_increment_key_uq UNIQUE (increment_key),
    CONSTRAINT round3m_saturation_increment_sequence_uq UNIQUE (
        increment_sequence
    ),
    CONSTRAINT round3m_saturation_increment_text_ck CHECK (
        increment_key = lower(btrim(increment_key))
        AND increment_key ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND increment_sequence > 0
        AND reviewed_strict_assertion_increment > 0
        AND preparation_service_coverage_status IN (
            'NOT_EVALUATED', 'UNDER_COVERED', 'COVERAGE_SUFFICIENT'
        )
        AND source_family_coverage_status IN (
            'NOT_EVALUATED', 'UNDER_COVERED', 'COVERAGE_SUFFICIENT'
        )
        AND measurement_receipt_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3m_saturation_increment_rates_ck CHECK (
        (new_normalized_forms_per_1000 IS NULL
         OR new_normalized_forms_per_1000 >= 0)
        AND (new_normalized_forms_upper_bound_per_1000 IS NULL
             OR new_normalized_forms_upper_bound_per_1000 >= 0)
        AND (canonical_mapping_rate IS NULL
             OR canonical_mapping_rate BETWEEN 0 AND 1)
        AND (new_supported_edge_rate IS NULL
             OR new_supported_edge_rate BETWEEN 0 AND 1)
        AND (weighted_jaccard_graph_stability IS NULL
             OR weighted_jaccard_graph_stability BETWEEN 0 AND 1)
        AND (same_population_duplicate_rate IS NULL
             OR same_population_duplicate_rate BETWEEN 0 AND 1)
    ),
    CONSTRAINT round3m_saturation_measurement_complete_ck CHECK (
        NOT measurement_complete
        OR num_nonnulls(
            new_normalized_forms_per_1000,
            new_normalized_forms_upper_bound_per_1000,
            canonical_mapping_rate,
            new_supported_edge_rate,
            weighted_jaccard_graph_stability,
            same_population_duplicate_rate,
            held_out_normalization_delta_percentage_points,
            held_out_family_ndcg8_delta,
            worst_held_out_family_delta
        ) = 9
        AND preparation_service_coverage_status <> 'NOT_EVALUATED'
        AND source_family_coverage_status <> 'NOT_EVALUATED'
    )
);

CREATE VIEW audit.v_round3m_saturation_status AS
WITH recent AS (
    SELECT *
    FROM audit.round3m_saturation_increment
    WHERE measurement_complete
    ORDER BY increment_sequence DESC
    LIMIT 3
), future_condition AS (
    SELECT
        count(*) = 3
        AND bool_and(new_normalized_forms_per_1000 < 0.5)
        AND bool_and(new_normalized_forms_upper_bound_per_1000 < 1.0)
        AND bool_and(canonical_mapping_rate >= 0.97)
        AND bool_and(new_supported_edge_rate < 0.01)
        AND bool_and(weighted_jaccard_graph_stability > 0.98)
        AND bool_and(same_population_duplicate_rate > 0.80)
        AND bool_and(
            held_out_normalization_delta_percentage_points < 0.5
        )
        AND bool_and(held_out_family_ndcg8_delta < 0.005)
        AND bool_and(
            preparation_service_coverage_status = 'COVERAGE_SUFFICIENT'
            AND source_family_coverage_status = 'COVERAGE_SUFFICIENT'
        ) AS raw_future_condition
    FROM recent
)
SELECT
    policy.policy_version,
    policy.saturation_evaluated,
    policy.saturation_pass,
    future_condition.raw_future_condition,
    (SELECT count(*) FROM recent)::INTEGER AS complete_increment_count,
    'Round 3M cannot evaluate saturation: three reviewed increments and trained held-out evaluations do not exist.'::TEXT AS explanatory_note
FROM audit.round3m_phase_policy AS policy
CROSS JOIN future_condition
WHERE policy.policy_version = 'round3m-policy-v1';

CREATE TRIGGER round3m_gate_definition_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_gate_definition
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_gate_criterion_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_descriptor_gate_criterion
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_legacy_deprecation_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_legacy_gate_deprecation
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

CREATE TRIGGER round3m_phase_policy_immutable_bud
BEFORE UPDATE OR DELETE ON audit.round3m_phase_policy
FOR EACH ROW EXECUTE FUNCTION audit.reject_round3m_immutable_mutation();

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
WITH checks AS (
    SELECT
        'round3m.empty_database_never_passes_descriptor_gate'::TEXT AS
            check_key,
        count(*) FILTER (WHERE gate.gate_pass)::BIGINT AS violation_count
    FROM audit.v_round3m_descriptor_gate AS gate
    CROSS JOIN audit.v_round3m_descriptor_gate_metrics AS metric
    WHERE metric.segmented_atomic_observation_count = 0
    UNION ALL
    SELECT 'round3m.na_never_passes', count(*)::BIGINT
    FROM audit.v_round3m_descriptor_gate_status
    WHERE not_applicable AND pass
    UNION ALL
    SELECT 'round3m.rights_blocker_never_passes_gate', count(*)::BIGINT
    FROM audit.v_round3m_descriptor_gate
    WHERE rights_blocker AND gate_pass
    UNION ALL
    SELECT 'round3m.legacy_record_first_gate_has_no_authority', count(*)::BIGINT
    FROM audit.v_round3m_legacy_gate_status
    WHERE current_training_authority
       OR current_training_authorization_pass
    UNION ALL
    SELECT 'round3m.current_policy_forbids_training', count(*)::BIGINT
    FROM audit.v_current_professional_training_readiness
    WHERE model_training_allowed
       OR authorizes_training
       OR current_training_authorization_pass
    UNION ALL
    SELECT 'round3m.human_state_requires_actual_human_receipt', count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion AS assertion
    LEFT JOIN audit.round3m_descriptor_review_receipt AS receipt
      ON receipt.review_receipt_id = assertion.current_review_receipt_id
     AND receipt.descriptor_assertion_id = assertion.descriptor_assertion_id
     AND receipt.review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
     AND receipt.receipt_origin_code IN (
         'HUMAN_REVIEW_IMPORT', 'DOCUMENTED_HUMAN_EVENT'
     )
     AND receipt.human_event_evidence_sha256 IS NOT NULL
    WHERE assertion.review_state IN (
            'HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED'
          )
      AND receipt.review_receipt_id IS NULL
    UNION ALL
    SELECT 'round3m.expert_state_requires_final_adjudication', count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion AS assertion
    JOIN audit.round3m_descriptor_review_receipt AS receipt
      ON receipt.review_receipt_id = assertion.current_review_receipt_id
    WHERE assertion.review_state = 'EXPERT_ADJUDICATED'
      AND (
          receipt.review_actor_type <> 'EXPERT_REVIEWER'
          OR receipt.reviewer_role <> 'ADJUDICATOR'
          OR receipt.adjudication_status <> 'FINAL'
          OR receipt.decision <> 'ADJUDICATE_DESCRIPTOR'
      )
    UNION ALL
    SELECT 'round3m.current_rights_pointer_is_leaf', count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion AS assertion
    LEFT JOIN evidence.v_round3m_current_descriptor_rights AS rights
      ON rights.rights_decision_id = assertion.rights_decision_id
     AND rights.unambiguous_current_decision
    WHERE rights.rights_decision_id IS NULL
    UNION ALL
    SELECT 'round3m.model_universe_has_affirmative_rights', count(*)::BIGINT
    FROM corpus.v_round3m_model_eligible_descriptor_universe
    WHERE internal_research_analysis <> 'AFFIRMATIVE'
       OR model_research <> 'AFFIRMATIVE'
    UNION ALL
    SELECT 'round3m.deployment_universe_has_affirmative_rights', count(*)::BIGINT
    FROM corpus.v_round3m_deployment_eligible_descriptor_universe
    WHERE internal_research_analysis <> 'AFFIRMATIVE'
       OR model_research <> 'AFFIRMATIVE'
       OR deployment_or_commercial_model <> 'AFFIRMATIVE'
    UNION ALL
    SELECT 'round3m.non_descriptors_never_enter_descriptor_universes', count(*)::BIGINT
    FROM corpus.v_round3m_human_reviewed_descriptor_universe
    WHERE descriptor_class = 'NON_DESCRIPTOR'
    UNION ALL
    SELECT 'round3m.assertion_deinflation_excludes_publication_duplicates',
           count(*)::BIGINT
    FROM corpus.v_round3m_assertion_level_deinflated
    WHERE deduplication_disposition IN (
        'EXACT_WITHIN_FIELD_REPEAT', 'WITHIN_RECORD_REPEAT',
        'MIRROR_PUBLICATION', 'SUMMARY_DETAIL_DUPLICATE',
        'TRUE_DUPLICATE_ARTIFACT', 'UNRESOLVED'
    )
    UNION ALL
    SELECT 'round3m.record_unique_surface_is_unique',
           coalesce(sum(row_count - 1), 0)::BIGINT
    FROM (
        SELECT effective_record_key,
               coalesce(
                   normalized_candidate_form,
                   kb.normalize_expression(source_native_lexical_form),
                   'sha256:' || source_native_lexical_form_sha256
               ) AS descriptor_form,
               count(*) AS row_count
        FROM corpus.v_round3m_record_unique_descriptor
        GROUP BY effective_record_key,
                 coalesce(
                     normalized_candidate_form,
                     kb.normalize_expression(source_native_lexical_form),
                     'sha256:' || source_native_lexical_form_sha256
                 )
        HAVING count(*) > 1
    ) AS duplicate
    UNION ALL
    SELECT 'round3m.coassertion_boundaries_preserved', count(*)::BIGINT
    FROM corpus.round3m_coassertion_event AS event
    JOIN corpus.round3m_descriptor_assertion AS left_assertion
      ON left_assertion.descriptor_assertion_id =
         event.left_descriptor_assertion_id
    JOIN corpus.round3m_descriptor_assertion AS right_assertion
      ON right_assertion.descriptor_assertion_id =
         event.right_descriptor_assertion_id
    WHERE left_assertion.effective_record_key IS DISTINCT FROM
              right_assertion.effective_record_key
       OR left_assertion.source_observation_key IS DISTINCT FROM
              right_assertion.source_observation_key
       OR event.effective_record_key IS DISTINCT FROM
              left_assertion.effective_record_key
       OR event.source_observation_key IS DISTINCT FROM
              left_assertion.source_observation_key
    UNION ALL
    SELECT 'round3m.no_descriptor_inferred_context', count(*)::BIGINT
    FROM corpus.round3m_descriptor_assertion
    WHERE roast_inferred_from_descriptor
       OR preparation_inferred_from_descriptor
    UNION ALL
    SELECT 'round3m.machine_queue_cannot_claim_human_review', count(*)::BIGINT
    FROM audit.round3m_descriptor_provisional_decision
    WHERE human_confirmed
       OR expert_adjudicated
       OR counts_as_reviewed_descriptor
       OR model_eligible
       OR review_state IN ('HUMAN_CONFIRMED', 'EXPERT_ADJUDICATED')
       OR review_actor_type IN ('HUMAN_REVIEWER', 'EXPERT_REVIEWER')
    UNION ALL
    SELECT 'round3m.saturation_not_evaluated_or_passed', count(*)::BIGINT
    FROM audit.v_round3m_saturation_status
    WHERE saturation_evaluated OR saturation_pass
)
SELECT
    check_key,
    violation_count,
    violation_count = 0 AS passed
FROM checks
ORDER BY check_key
$run_round3m_gate_validation_queries$;

COMMENT ON VIEW audit.v_round3m_descriptor_gate_status IS
    'Executable criterion surface with required Round 3M columns. NULL observations render as NA and always fail.';
COMMENT ON VIEW audit.v_round3m_descriptor_gate IS
    'Aggregate descriptor-first gates. Empty data, NA criteria, and rights blockers cannot pass; a pass never authorizes Round 3M training.';
COMMENT ON TABLE audit.round3m_legacy_gate_deprecation IS
    'Executable deprecation registry for the former record-first gates and undifferentiated 60000-assertion threshold.';

COMMIT;
