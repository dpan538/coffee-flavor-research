\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0 -- Round 2B resolution closure,
-- governance projections, ontology-feedback queue, and validation contract.
--
-- Resolution is intentionally narrower than retrieval.  An occurrence is
-- resolved only through a current active preferred/approved lexicalization of
-- its exact preserved expression identity.  Normalized phrases, trigrams,
-- graph expansion, and polysemous_usage mappings remain candidate signals and
-- cannot satisfy this materialized-resolution boundary.

BEGIN;

CREATE TABLE corpus.observation_resolution_run (
    observation_resolution_run_id BIGINT GENERATED ALWAYS AS IDENTITY,
    observation_resolution_run_key TEXT NOT NULL,
    normalization_derivation_run_id BIGINT NOT NULL,
    policy_version TEXT NOT NULL,
    resolution_as_of TIMESTAMPTZ NOT NULL,
    allowed_mapping_types JSONB NOT NULL,
    policy_sha256 TEXT NOT NULL,
    source_baseline_sha TEXT NOT NULL,
    expected_occurrence_count BIGINT NOT NULL,
    resolved_occurrence_count BIGINT NOT NULL,
    unresolved_occurrence_count BIGINT NOT NULL,
    expected_normalized_identity_count BIGINT NOT NULL,
    resolved_only_normalized_identity_count BIGINT NOT NULL,
    unresolved_only_normalized_identity_count BIGINT NOT NULL,
    mixed_normalized_identity_count BIGINT NOT NULL,
    result_inventory_sha256 TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    frozen_at TIMESTAMPTZ,
    notes TEXT NOT NULL,
    CONSTRAINT observation_resolution_run_pk PRIMARY KEY (
        observation_resolution_run_id
    ),
    CONSTRAINT observation_resolution_run_key_uq UNIQUE (
        observation_resolution_run_key
    ),
    CONSTRAINT observation_resolution_run_derivation_policy_uq UNIQUE (
        normalization_derivation_run_id,
        policy_version
    ),
    CONSTRAINT observation_resolution_run_derivation_fk FOREIGN KEY (
        normalization_derivation_run_id
    ) REFERENCES corpus.normalization_derivation_run (
        normalization_derivation_run_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_run_key_nonempty_ck CHECK (
        observation_resolution_run_key = btrim(observation_resolution_run_key)
        AND observation_resolution_run_key <> ''
        AND policy_version = btrim(policy_version)
        AND policy_version <> ''
        AND notes = btrim(notes)
        AND notes <> ''
    ),
    CONSTRAINT observation_resolution_run_mapping_types_ck CHECK (
        allowed_mapping_types =
            '["preferred_label", "approved_variant"]'::JSONB
    ),
    CONSTRAINT observation_resolution_run_hashes_ck CHECK (
        policy_sha256 ~ '^[0-9a-f]{64}$'
        AND source_baseline_sha ~ '^[0-9a-f]{40}$'
        AND (
            result_inventory_sha256 IS NULL
            OR result_inventory_sha256 ~ '^[0-9a-f]{64}$'
        )
    ),
    CONSTRAINT observation_resolution_run_counts_ck CHECK (
        expected_occurrence_count > 0
        AND resolved_occurrence_count >= 0
        AND unresolved_occurrence_count >= 0
        AND resolved_occurrence_count + unresolved_occurrence_count =
            expected_occurrence_count
        AND expected_normalized_identity_count > 0
        AND resolved_only_normalized_identity_count >= 0
        AND unresolved_only_normalized_identity_count >= 0
        AND mixed_normalized_identity_count >= 0
        AND resolved_only_normalized_identity_count
            + unresolved_only_normalized_identity_count
            + mixed_normalized_identity_count =
              expected_normalized_identity_count
    ),
    CONSTRAINT observation_resolution_run_time_ck CHECK (
        resolution_as_of <= created_at
        AND (frozen_at IS NULL OR frozen_at >= created_at)
    ),
    CONSTRAINT observation_resolution_run_completion_shape_ck CHECK (
        (frozen_at IS NULL AND result_inventory_sha256 IS NULL)
        OR (frozen_at IS NOT NULL AND result_inventory_sha256 IS NOT NULL)
    )
);

COMMENT ON TABLE corpus.observation_resolution_run IS
    'Versioned receipt for conservative exact-expression materialization, including its deterministic as-of boundary. A run is populated while unfrozen and becomes immutable with its result inventory.';

CREATE TABLE corpus.observation_resolution_run_result (
    observation_resolution_run_id BIGINT NOT NULL,
    observation_expression_id BIGINT NOT NULL,
    resolution_status_code TEXT NOT NULL,
    lexicalization_id BIGINT,
    resolution_note TEXT NOT NULL,
    CONSTRAINT observation_resolution_run_result_pk PRIMARY KEY (
        observation_resolution_run_id,
        observation_expression_id
    ),
    CONSTRAINT observation_resolution_run_result_run_fk FOREIGN KEY (
        observation_resolution_run_id
    ) REFERENCES corpus.observation_resolution_run (
        observation_resolution_run_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_run_result_expression_fk FOREIGN KEY (
        observation_expression_id
    ) REFERENCES corpus.observation_expression (
        observation_expression_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_run_result_status_fk FOREIGN KEY (
        resolution_status_code
    ) REFERENCES ref.resolution_status (resolution_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_run_result_lexicalization_fk FOREIGN KEY (
        lexicalization_id
    ) REFERENCES kb.lexicalization (lexicalization_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT observation_resolution_run_result_shape_ck CHECK (
        (resolution_status_code = 'resolved' AND lexicalization_id IS NOT NULL)
        OR (
            resolution_status_code = 'unresolved'
            AND lexicalization_id IS NULL
        )
    ),
    CONSTRAINT observation_resolution_run_result_note_nonempty_ck CHECK (
        resolution_note = btrim(resolution_note)
        AND resolution_note <> ''
    )
);

COMMENT ON TABLE corpus.observation_resolution_run_result IS
    'Immutable-after-freeze historical result rows for one exact-expression resolution policy run. These rows do not reference the mutable current observation_resolution materialization.';

CREATE FUNCTION corpus.guard_frozen_observation_resolution_run()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_observation_resolution_run$
DECLARE
    actual_result_count BIGINT;
    derivation_occurrence_count BIGINT;
    off_scope_result_count BIGINT;
    actual_resolved_count BIGINT;
    actual_unresolved_count BIGINT;
    actual_normalized_identity_count BIGINT;
    actual_resolved_only_identity_count BIGINT;
    actual_unresolved_only_identity_count BIGINT;
    actual_mixed_identity_count BIGINT;
    actual_inventory_sha256 TEXT;
    policy_mismatch_count BIGINT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NEW.frozen_at IS NOT NULL
           OR NEW.result_inventory_sha256 IS NOT NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'observation_resolution_run_insert_unfrozen_ck',
                MESSAGE = 'observation_resolution_run_insert_unfrozen_ck: a resolution run must be inserted unfrozen, populated, and then frozen through validated update';
        END IF;
        RETURN NEW;
    END IF;

    IF OLD.frozen_at IS NOT NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'observation_resolution_run_frozen_ck',
            MESSAGE = 'observation_resolution_run_frozen_ck: a frozen resolution run cannot be updated or deleted';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    IF NEW.frozen_at IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT count(*)
    INTO actual_result_count
    FROM corpus.observation_resolution_run_result AS result
    WHERE result.observation_resolution_run_id =
          NEW.observation_resolution_run_id;

    SELECT count(*)
    INTO derivation_occurrence_count
    FROM corpus.normalized_expression_occurrence AS occurrence
    WHERE occurrence.normalization_derivation_run_id =
          NEW.normalization_derivation_run_id;

    SELECT count(*)
    INTO off_scope_result_count
    FROM corpus.observation_resolution_run_result AS result
    LEFT JOIN corpus.normalized_expression_occurrence AS occurrence
      ON occurrence.observation_expression_id =
         result.observation_expression_id
     AND occurrence.normalization_derivation_run_id =
         NEW.normalization_derivation_run_id
    WHERE result.observation_resolution_run_id =
          NEW.observation_resolution_run_id
      AND occurrence.observation_expression_id IS NULL;

    SELECT
        count(*) FILTER (
            WHERE result.resolution_status_code = 'resolved'
        ),
        count(*) FILTER (
            WHERE result.resolution_status_code = 'unresolved'
        ),
        count(DISTINCT occurrence.normalized_expression_id)
    INTO
        actual_resolved_count,
        actual_unresolved_count,
        actual_normalized_identity_count
    FROM corpus.observation_resolution_run_result AS result
    JOIN corpus.normalized_expression_occurrence AS occurrence
      ON occurrence.observation_expression_id =
         result.observation_expression_id
     AND occurrence.normalization_derivation_run_id =
         NEW.normalization_derivation_run_id
    WHERE result.observation_resolution_run_id =
          NEW.observation_resolution_run_id;

    SELECT
        count(*) FILTER (
            WHERE identity_status.has_resolved
              AND NOT identity_status.has_unresolved
        ),
        count(*) FILTER (
            WHERE identity_status.has_unresolved
              AND NOT identity_status.has_resolved
        ),
        count(*) FILTER (
            WHERE identity_status.has_resolved
              AND identity_status.has_unresolved
        )
    INTO
        actual_resolved_only_identity_count,
        actual_unresolved_only_identity_count,
        actual_mixed_identity_count
    FROM (
        SELECT
            occurrence.normalized_expression_id,
            bool_or(result.resolution_status_code = 'resolved')
                AS has_resolved,
            bool_or(result.resolution_status_code = 'unresolved')
                AS has_unresolved
        FROM corpus.observation_resolution_run_result AS result
        JOIN corpus.normalized_expression_occurrence AS occurrence
          ON occurrence.observation_expression_id =
             result.observation_expression_id
         AND occurrence.normalization_derivation_run_id =
             NEW.normalization_derivation_run_id
        WHERE result.observation_resolution_run_id =
              NEW.observation_resolution_run_id
        GROUP BY occurrence.normalized_expression_id
    ) AS identity_status;

    SELECT encode(
        sha256(convert_to(
            string_agg(
                observation_expression.observation_expression_key || '|' ||
                result.resolution_status_code || '|' ||
                COALESCE(lexicalization.lexicalization_key, ''),
                E'\n' ORDER BY
                    observation_expression.observation_expression_key
            ),
            'UTF8'
        )),
        'hex'
    )
    INTO actual_inventory_sha256
    FROM corpus.observation_resolution_run_result AS result
    JOIN corpus.observation_expression AS observation_expression
      ON observation_expression.observation_expression_id =
         result.observation_expression_id
    LEFT JOIN kb.lexicalization AS lexicalization
      ON lexicalization.lexicalization_id = result.lexicalization_id
    WHERE result.observation_resolution_run_id =
          NEW.observation_resolution_run_id;

    WITH eligible_lexicalizations AS (
        SELECT
            result.observation_expression_id,
            lexicalization.concept_id,
            lexicalization.lexicalization_id,
            CASE lexicalization.mapping_type_code
                WHEN 'preferred_label' THEN 1
                WHEN 'approved_variant' THEN 2
                ELSE 99
            END AS mapping_precedence,
            lexicalization.lexicalization_key
        FROM corpus.observation_resolution_run_result AS result
        JOIN corpus.observation_expression AS observation_expression
          ON observation_expression.observation_expression_id =
             result.observation_expression_id
        JOIN kb.lexicalization AS lexicalization
          ON lexicalization.expression_id =
             observation_expression.expression_id
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
         AND concept.lifecycle_status_code = 'active'
        WHERE result.observation_resolution_run_id =
              NEW.observation_resolution_run_id
          AND lexicalization.lifecycle_status_code = 'active'
          AND NEW.allowed_mapping_types ?
              lexicalization.mapping_type_code
          AND lexicalization.valid_from <= NEW.resolution_as_of
          AND (
              lexicalization.valid_until IS NULL
              OR lexicalization.valid_until > NEW.resolution_as_of
          )
    ),
    eligible_concepts AS (
        SELECT
            eligible_lexicalizations.observation_expression_id,
            eligible_lexicalizations.concept_id,
            (array_agg(
                eligible_lexicalizations.lexicalization_id
                ORDER BY
                    eligible_lexicalizations.mapping_precedence,
                    eligible_lexicalizations.lexicalization_key,
                    eligible_lexicalizations.lexicalization_id
            ))[1] AS selected_lexicalization_id
        FROM eligible_lexicalizations
        GROUP BY
            eligible_lexicalizations.observation_expression_id,
            eligible_lexicalizations.concept_id
    ),
    expected_result AS (
        SELECT
            result.observation_expression_id,
            count(eligible_concepts.concept_id) AS eligible_concept_count,
            min(eligible_concepts.selected_lexicalization_id)
                AS selected_lexicalization_id
        FROM corpus.observation_resolution_run_result AS result
        LEFT JOIN eligible_concepts
          ON eligible_concepts.observation_expression_id =
             result.observation_expression_id
        WHERE result.observation_resolution_run_id =
              NEW.observation_resolution_run_id
        GROUP BY result.observation_expression_id
    )
    SELECT count(*)
    INTO policy_mismatch_count
    FROM corpus.observation_resolution_run_result AS result
    JOIN expected_result
      ON expected_result.observation_expression_id =
         result.observation_expression_id
    WHERE result.observation_resolution_run_id =
          NEW.observation_resolution_run_id
      AND (
          result.resolution_status_code IS DISTINCT FROM
              CASE
                  WHEN expected_result.eligible_concept_count = 1
                  THEN 'resolved'
                  ELSE 'unresolved'
              END
          OR result.lexicalization_id IS DISTINCT FROM
              CASE
                  WHEN expected_result.eligible_concept_count = 1
                  THEN expected_result.selected_lexicalization_id
              END
      );

    IF policy_mismatch_count IS DISTINCT FROM 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'observation_resolution_run_policy_result_ck',
            MESSAGE = 'observation_resolution_run_policy_result_ck: result rows do not exactly implement the run mapping-type, lifecycle, validity, active-concept, and ambiguity policy';
    END IF;

    IF actual_result_count IS DISTINCT FROM NEW.expected_occurrence_count
       OR derivation_occurrence_count IS DISTINCT FROM
          NEW.expected_occurrence_count
       OR off_scope_result_count IS DISTINCT FROM 0
       OR actual_resolved_count IS DISTINCT FROM
          NEW.resolved_occurrence_count
       OR actual_unresolved_count IS DISTINCT FROM
          NEW.unresolved_occurrence_count
       OR actual_normalized_identity_count IS DISTINCT FROM
          NEW.expected_normalized_identity_count
       OR actual_resolved_only_identity_count IS DISTINCT FROM
          NEW.resolved_only_normalized_identity_count
       OR actual_unresolved_only_identity_count IS DISTINCT FROM
          NEW.unresolved_only_normalized_identity_count
       OR actual_mixed_identity_count IS DISTINCT FROM
          NEW.mixed_normalized_identity_count
       OR actual_inventory_sha256 IS DISTINCT FROM
          NEW.result_inventory_sha256 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'observation_resolution_run_freeze_inventory_ck',
            MESSAGE = 'observation_resolution_run_freeze_inventory_ck: child results do not match the proposed frozen receipt';
    END IF;

    RETURN NEW;
END;
$guard_frozen_observation_resolution_run$;

CREATE TRIGGER observation_resolution_run_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE ON corpus.observation_resolution_run
FOR EACH ROW EXECUTE FUNCTION
    corpus.guard_frozen_observation_resolution_run();

CREATE FUNCTION corpus.guard_frozen_observation_resolution_run_result()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $guard_frozen_observation_resolution_run_result$
DECLARE
    old_run_frozen_at TIMESTAMPTZ;
    new_run_frozen_at TIMESTAMPTZ;
BEGIN
    IF TG_OP <> 'INSERT' THEN
        SELECT run.frozen_at
        INTO old_run_frozen_at
        FROM corpus.observation_resolution_run AS run
        WHERE run.observation_resolution_run_id =
              OLD.observation_resolution_run_id;
    END IF;

    IF TG_OP <> 'DELETE' THEN
        SELECT run.frozen_at
        INTO new_run_frozen_at
        FROM corpus.observation_resolution_run AS run
        WHERE run.observation_resolution_run_id =
              NEW.observation_resolution_run_id;
    END IF;

    IF old_run_frozen_at IS NOT NULL OR new_run_frozen_at IS NOT NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            CONSTRAINT = 'observation_resolution_run_result_frozen_ck',
            MESSAGE = 'observation_resolution_run_result_frozen_ck: results belonging to a frozen resolution run cannot be inserted, updated, or deleted';
    END IF;

    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$guard_frozen_observation_resolution_run_result$;

CREATE TRIGGER observation_resolution_run_result_frozen_biud
BEFORE INSERT OR UPDATE OR DELETE
ON corpus.observation_resolution_run_result
FOR EACH ROW EXECUTE FUNCTION
    corpus.guard_frozen_observation_resolution_run_result();

CREATE TRIGGER observation_resolution_run_result_semantics_biu
BEFORE INSERT OR UPDATE OF
    observation_expression_id,
    resolution_status_code,
    lexicalization_id
ON corpus.observation_resolution_run_result
FOR EACH ROW EXECUTE FUNCTION
    corpus.enforce_observation_resolution_semantics();

COMMENT ON TRIGGER observation_resolution_run_result_semantics_biu
ON corpus.observation_resolution_run_result IS
    'Rejects cross-expression historical resolutions and preserves status-to-lexicalization shape before a run can be frozen.';

WITH pilot_run AS (
    SELECT run.normalization_derivation_run_id
    FROM corpus.normalization_derivation_run AS run
    WHERE run.normalization_derivation_run_key =
          'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
),
eligible_lexicalizations AS (
    SELECT
        lexicalization.expression_id,
        lexicalization.concept_id,
        lexicalization.lexicalization_id,
        CASE lexicalization.mapping_type_code
            WHEN 'preferred_label' THEN 1
            WHEN 'approved_variant' THEN 2
        END AS mapping_precedence,
        lexicalization.lexicalization_key
    FROM kb.lexicalization AS lexicalization
    JOIN kb.concept AS concept
      ON concept.concept_id = lexicalization.concept_id
     AND concept.lifecycle_status_code = 'active'
    WHERE lexicalization.lifecycle_status_code = 'active'
      AND lexicalization.mapping_type_code IN (
          'preferred_label',
          'approved_variant'
      )
      AND lexicalization.valid_from <=
          TIMESTAMPTZ '2026-08-24 08:31:00+00'
      AND (
          lexicalization.valid_until IS NULL
          OR lexicalization.valid_until >
             TIMESTAMPTZ '2026-08-24 08:31:00+00'
      )
),
eligible_concepts AS (
    SELECT
        eligible_lexicalizations.expression_id,
        eligible_lexicalizations.concept_id,
        (array_agg(
            eligible_lexicalizations.lexicalization_id
            ORDER BY
                eligible_lexicalizations.mapping_precedence,
                eligible_lexicalizations.lexicalization_key,
                eligible_lexicalizations.lexicalization_id
        ))[1] AS lexicalization_id
    FROM eligible_lexicalizations
    GROUP BY
        eligible_lexicalizations.expression_id,
        eligible_lexicalizations.concept_id
),
eligible AS (
    SELECT
        eligible_concepts.expression_id,
        eligible_concepts.lexicalization_id,
        row_number() OVER (
            PARTITION BY eligible_concepts.expression_id
            ORDER BY eligible_concepts.concept_id
        ) AS eligibility_rank,
        count(*) OVER (
            PARTITION BY eligible_concepts.expression_id
        ) AS eligibility_count
    FROM eligible_concepts
),
pilot_occurrences AS (
    SELECT occurrence.observation_expression_id,
           observation_expression.observation_expression_key,
           observation_expression.expression_id
    FROM corpus.normalized_expression_occurrence AS occurrence
    JOIN pilot_run
      ON pilot_run.normalization_derivation_run_id =
         occurrence.normalization_derivation_run_id
    JOIN corpus.observation_expression AS observation_expression
      ON observation_expression.observation_expression_id =
         occurrence.observation_expression_id
),
resolution_rows AS (
    SELECT
        pilot_occurrences.observation_expression_id,
        pilot_occurrences.observation_expression_key,
        CASE
            WHEN eligible.eligibility_count = 1 THEN 'resolved'
            ELSE 'unresolved'
        END AS resolution_status_code,
        CASE
            WHEN eligible.eligibility_count = 1
            THEN eligible.lexicalization_id
        END AS lexicalization_id
    FROM pilot_occurrences
    LEFT JOIN eligible AS eligible
      ON eligible.expression_id = pilot_occurrences.expression_id
     AND eligible.eligibility_rank = 1
)
INSERT INTO corpus.observation_resolution (
    observation_resolution_key,
    observation_expression_id,
    resolution_status_code,
    lexicalization_id,
    resolution_note
)
SELECT
    'observation_resolution.round2b.' ||
        encode(
            sha256(convert_to(resolution_rows.observation_expression_key, 'UTF8')),
            'hex'
        ),
    resolution_rows.observation_expression_id,
    resolution_rows.resolution_status_code,
    resolution_rows.lexicalization_id,
    CASE resolution_rows.resolution_status_code
        WHEN 'resolved' THEN
            'Exact current active preferred/approved lexicalization; no normalized, trigram, graph, or polysemous inference.'
        ELSE
            'Explicitly unresolved under the exact current active preferred/approved boundary; retrieval candidates remain noncanonical suggestions.'
    END
FROM resolution_rows;

DO $resolution_inventory_gate$
DECLARE
    total_count BIGINT;
    resolved_count BIGINT;
    unresolved_count BIGINT;
    resolved_normalized_count BIGINT;
    unresolved_normalized_count BIGINT;
BEGIN
    SELECT
        count(*),
        count(*) FILTER (WHERE resolution.resolution_status_code = 'resolved'),
        count(*) FILTER (WHERE resolution.resolution_status_code = 'unresolved'),
        count(DISTINCT occurrence.normalized_expression_id) FILTER (
            WHERE resolution.resolution_status_code = 'resolved'
        ),
        count(DISTINCT occurrence.normalized_expression_id) FILTER (
            WHERE resolution.resolution_status_code = 'unresolved'
        )
    INTO
        total_count,
        resolved_count,
        unresolved_count,
        resolved_normalized_count,
        unresolved_normalized_count
    FROM corpus.normalized_expression_occurrence AS occurrence
    JOIN corpus.normalization_derivation_run AS run
      ON run.normalization_derivation_run_id =
         occurrence.normalization_derivation_run_id
     AND run.normalization_derivation_run_key =
         'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
    JOIN corpus.observation_resolution AS resolution
      ON resolution.observation_expression_id =
         occurrence.observation_expression_id;

    IF (total_count, resolved_count, unresolved_count,
        resolved_normalized_count, unresolved_normalized_count)
       IS DISTINCT FROM (5564::BIGINT, 1866::BIGINT, 3698::BIGINT,
                         57::BIGINT, 1656::BIGINT) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_exact_resolution_inventory_ck',
            MESSAGE = format(
                'round2b_exact_resolution_inventory_ck: expected 5564/1866/3698 occurrences and 57/1656 normalized identities; found %s/%s/%s and %s/%s',
                total_count, resolved_count, unresolved_count,
                resolved_normalized_count, unresolved_normalized_count
            );
    END IF;
END;
$resolution_inventory_gate$;

WITH pilot_run AS (
    SELECT run.normalization_derivation_run_id
    FROM corpus.normalization_derivation_run AS run
    WHERE run.normalization_derivation_run_key =
          'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
),
policy(configuration) AS (
    VALUES (
        '{
          "allowed_mapping_types":["preferred_label","approved_variant"],
          "concept_status":"active",
          "expression_identity":"exact_observation_expression_id",
          "multiple_concepts":"unresolved",
          "normalized_phrase_allowed":false,
          "polysemous_usage_allowed":false,
          "resolution_as_of":"2026-08-24T08:31:00Z",
          "retrieval_candidates_allowed":false,
          "version":"round2b-exact-preferred-approved-v1"
        }'::JSONB
    )
)
INSERT INTO corpus.observation_resolution_run (
    observation_resolution_run_key,
    normalization_derivation_run_id,
    policy_version,
    resolution_as_of,
    allowed_mapping_types,
    policy_sha256,
    source_baseline_sha,
    expected_occurrence_count,
    resolved_occurrence_count,
    unresolved_occurrence_count,
    expected_normalized_identity_count,
    resolved_only_normalized_identity_count,
    unresolved_only_normalized_identity_count,
    mixed_normalized_identity_count,
    result_inventory_sha256,
    created_at,
    frozen_at,
    notes
)
SELECT
    'resolution_run.firstbloom_a6cb002_pilot_v1.exact_v1',
    pilot_run.normalization_derivation_run_id,
    'round2b-exact-preferred-approved-v1',
    TIMESTAMPTZ '2026-08-24 08:31:00+00',
    '["preferred_label", "approved_variant"]'::JSONB,
    encode(sha256(convert_to(policy.configuration::TEXT, 'UTF8')), 'hex'),
    'a6abb4112cff3fc436b1613c37f9b40f51e65144',
    5564,
    1866,
    3698,
    1713,
    57,
    1656,
    0,
    NULL,
    TIMESTAMPTZ '2026-08-24 08:31:00+00',
    NULL,
    'Versioned exact-expression receipt. The five winey occurrences remain unresolved because polysemous_usage is outside the allowed mapping types.'
FROM pilot_run
CROSS JOIN policy;

INSERT INTO corpus.observation_resolution_run_result (
    observation_resolution_run_id,
    observation_expression_id,
    resolution_status_code,
    lexicalization_id,
    resolution_note
)
SELECT
    resolution_run.observation_resolution_run_id,
    occurrence.observation_expression_id,
    resolution.resolution_status_code,
    resolution.lexicalization_id,
    resolution.resolution_note
FROM corpus.observation_resolution_run AS resolution_run
JOIN corpus.normalized_expression_occurrence AS occurrence
  ON occurrence.normalization_derivation_run_id =
     resolution_run.normalization_derivation_run_id
JOIN corpus.observation_resolution AS resolution
  ON resolution.observation_expression_id =
     occurrence.observation_expression_id
WHERE resolution_run.observation_resolution_run_key =
      'resolution_run.firstbloom_a6cb002_pilot_v1.exact_v1';

WITH result_inventory AS (
    SELECT
        resolution_run.observation_resolution_run_id,
        encode(
            sha256(convert_to(
                string_agg(
                    observation_expression.observation_expression_key || '|' ||
                    result.resolution_status_code || '|' ||
                    COALESCE(lexicalization.lexicalization_key, ''),
                    E'\n' ORDER BY
                        observation_expression.observation_expression_key
                ),
                'UTF8'
            )),
            'hex'
        ) AS result_inventory_sha256
    FROM corpus.observation_resolution_run AS resolution_run
    JOIN corpus.observation_resolution_run_result AS result
      ON result.observation_resolution_run_id =
         resolution_run.observation_resolution_run_id
    JOIN corpus.observation_expression AS observation_expression
      ON observation_expression.observation_expression_id =
         result.observation_expression_id
    LEFT JOIN kb.lexicalization AS lexicalization
      ON lexicalization.lexicalization_id = result.lexicalization_id
    WHERE resolution_run.observation_resolution_run_key =
          'resolution_run.firstbloom_a6cb002_pilot_v1.exact_v1'
    GROUP BY resolution_run.observation_resolution_run_id
)
UPDATE corpus.observation_resolution_run AS resolution_run
SET result_inventory_sha256 = result_inventory.result_inventory_sha256,
    frozen_at = TIMESTAMPTZ '2026-08-24 08:31:00+00'
FROM result_inventory
WHERE resolution_run.observation_resolution_run_id =
      result_inventory.observation_resolution_run_id;

CREATE VIEW corpus.v_source_policy_matrix AS
SELECT
    policy.source_policy_review_key,
    source.source_key,
    source.title AS source_title,
    NULLIF(source.external_metadata ->> 'review_country_code', '')
        AS review_country_code,
    source_version.source_version_key,
    source_version.version_label AS source_version,
    license.license_policy_key,
    license.rights_status_code,
    license.production_export_allowed,
    policy.domain,
    policy.corpus_source_decision_code,
    policy.robots_status_code,
    policy.robots_locator,
    policy.terms_status_code,
    policy.terms_locator,
    policy.corpus_access_method_code,
    policy.copyright_status_code,
    policy.document_metadata_allowed,
    policy.raw_retention_allowed,
    policy.derived_terms_allowed,
    policy.derived_terms_redistribution_allowed,
    policy.raw_redistribution_allowed,
    policy.automated_acquisition_allowed,
    policy.commercial_use_implications,
    policy.checked_at,
    policy.notes
FROM corpus.source_policy_review AS policy
JOIN evidence.source_version AS source_version
  ON source_version.source_version_id = policy.source_version_id
JOIN evidence.source AS source
  ON source.source_id = source_version.source_id
JOIN evidence.license_policy AS license
  ON license.license_policy_id = policy.license_policy_id;

COMMENT ON VIEW corpus.v_source_policy_matrix IS
    'Auditable source/version/licence/access matrix. Unknown and blocked decisions remain visible rather than disappearing from allowed-source totals.';

CREATE VIEW corpus.v_corpus_inventory AS
SELECT
    snapshot.corpus_snapshot_key,
    snapshot.corpus_version,
    snapshot.capture_window_start,
    snapshot.capture_window_end,
    snapshot.source_inventory_sha256,
    snapshot.document_inventory_sha256,
    snapshot.code_commit_sha,
    snapshot.frozen_at,
    snapshot.raw_public_reproducibility_complete,
    snapshot.reproducibility_boundary,
    (SELECT count(DISTINCT source_member.source_policy_review_id)
       FROM corpus.corpus_snapshot_source AS source_member
      WHERE source_member.corpus_snapshot_id = snapshot.corpus_snapshot_id)
        AS source_policy_count,
    (SELECT count(DISTINCT source_member.industry_publisher_id)
       FROM corpus.corpus_snapshot_source AS source_member
      WHERE source_member.corpus_snapshot_id = snapshot.corpus_snapshot_id)
        AS publisher_count,
    (SELECT count(*) FROM corpus.acquisition_batch AS batch
      WHERE batch.corpus_snapshot_id = snapshot.corpus_snapshot_id)
        AS acquisition_batch_count,
    (SELECT count(*) FROM corpus.captured_document AS document
      WHERE document.corpus_id = snapshot.corpus_id) AS document_count,
    (SELECT count(DISTINCT document.industry_product_id)
       FROM corpus.captured_document AS document
      WHERE document.corpus_id = snapshot.corpus_id) AS product_count,
    (SELECT count(*)
       FROM corpus.raw_observation AS observation
       JOIN corpus.captured_document AS document
         ON document.captured_document_id = observation.captured_document_id
      WHERE document.corpus_id = snapshot.corpus_id) AS raw_observation_count,
    (SELECT count(*)
       FROM corpus.raw_observation AS observation
       JOIN corpus.captured_document AS document
         ON document.captured_document_id = observation.captured_document_id
      WHERE document.corpus_id = snapshot.corpus_id
        AND observation.observation_retention_code = 'derived_phrase')
        AS retained_phrase_count,
    (SELECT count(*)
       FROM corpus.raw_observation AS observation
       JOIN corpus.captured_document AS document
         ON document.captured_document_id = observation.captured_document_id
      WHERE document.corpus_id = snapshot.corpus_id
        AND observation.observation_retention_code = 'hash_only')
        AS hash_only_observation_count,
    (SELECT count(DISTINCT occurrence.observation_expression_id)
       FROM corpus.normalized_expression_occurrence AS occurrence
       JOIN corpus.normalization_derivation_run AS run
         ON run.normalization_derivation_run_id =
            occurrence.normalization_derivation_run_id
      WHERE run.corpus_snapshot_id = snapshot.corpus_snapshot_id
        AND run.frozen_at IS NOT NULL) AS normalized_occurrence_count,
    (SELECT count(DISTINCT occurrence.normalized_expression_id)
       FROM corpus.normalized_expression_occurrence AS occurrence
       JOIN corpus.normalization_derivation_run AS run
         ON run.normalization_derivation_run_id =
            occurrence.normalization_derivation_run_id
      WHERE run.corpus_snapshot_id = snapshot.corpus_snapshot_id
        AND run.frozen_at IS NOT NULL)
        AS unique_normalized_expression_count
FROM corpus.corpus_snapshot AS snapshot;

COMMENT ON VIEW corpus.v_corpus_inventory IS
    'One nonmultiplying inventory row per frozen or in-progress corpus snapshot, including the protected-raw reproducibility boundary.';

CREATE VIEW corpus.v_resolution_coverage AS
WITH occurrence_scope AS (
    SELECT
        resolution_run.observation_resolution_run_id,
        occurrence.normalization_derivation_run_id,
        occurrence.normalized_expression_id,
        result.resolution_status_code
    FROM corpus.observation_resolution_run AS resolution_run
    JOIN corpus.normalized_expression_occurrence AS occurrence
      ON occurrence.normalization_derivation_run_id =
         resolution_run.normalization_derivation_run_id
    LEFT JOIN corpus.observation_resolution_run_result AS result
      ON result.observation_resolution_run_id =
         resolution_run.observation_resolution_run_id
     AND result.observation_expression_id =
         occurrence.observation_expression_id
),
occurrence_counts AS (
    SELECT
        occurrence_scope.observation_resolution_run_id,
        occurrence_scope.normalization_derivation_run_id,
        count(*) AS total_occurrence_count,
        count(*) FILTER (
            WHERE occurrence_scope.resolution_status_code = 'resolved'
        ) AS resolved_occurrence_count,
        count(*) FILTER (
            WHERE occurrence_scope.resolution_status_code = 'unresolved'
        ) AS unresolved_occurrence_count,
        count(*) FILTER (
            WHERE occurrence_scope.resolution_status_code IS NULL
        ) AS missing_resolution_count
    FROM occurrence_scope
    GROUP BY
        occurrence_scope.observation_resolution_run_id,
        occurrence_scope.normalization_derivation_run_id
),
identity_status AS (
    SELECT
        occurrence_scope.observation_resolution_run_id,
        occurrence_scope.normalization_derivation_run_id,
        occurrence_scope.normalized_expression_id,
        bool_or(occurrence_scope.resolution_status_code = 'resolved')
            AS has_resolved,
        bool_or(occurrence_scope.resolution_status_code = 'unresolved')
            AS has_unresolved,
        bool_or(occurrence_scope.resolution_status_code IS NULL)
            AS has_missing
    FROM occurrence_scope
    GROUP BY
        occurrence_scope.observation_resolution_run_id,
        occurrence_scope.normalization_derivation_run_id,
        occurrence_scope.normalized_expression_id
),
identity_counts AS (
    SELECT
        identity_status.observation_resolution_run_id,
        identity_status.normalization_derivation_run_id,
        count(*) AS normalized_identity_count,
        count(*) FILTER (
            WHERE identity_status.has_resolved
              AND NOT identity_status.has_unresolved
              AND NOT identity_status.has_missing
        ) AS resolved_only_normalized_identity_count,
        count(*) FILTER (
            WHERE identity_status.has_unresolved
              AND NOT identity_status.has_resolved
              AND NOT identity_status.has_missing
        ) AS unresolved_only_normalized_identity_count,
        count(*) FILTER (
            WHERE identity_status.has_resolved
              AND identity_status.has_unresolved
              AND NOT identity_status.has_missing
        ) AS mixed_normalized_identity_count,
        count(*) FILTER (WHERE identity_status.has_missing)
            AS incomplete_normalized_identity_count
    FROM identity_status
    GROUP BY
        identity_status.observation_resolution_run_id,
        identity_status.normalization_derivation_run_id
)
SELECT
    resolution_run.observation_resolution_run_key,
    resolution_run.policy_version,
    resolution_run.resolution_as_of,
    resolution_run.frozen_at AS resolution_run_frozen_at,
    run.normalization_derivation_run_key,
    snapshot.corpus_snapshot_key,
    pipeline.normalization_pipeline_key,
    occurrence_counts.total_occurrence_count,
    occurrence_counts.resolved_occurrence_count,
    occurrence_counts.unresolved_occurrence_count,
    occurrence_counts.missing_resolution_count,
    identity_counts.normalized_identity_count,
    identity_counts.resolved_only_normalized_identity_count,
    identity_counts.unresolved_only_normalized_identity_count,
    identity_counts.mixed_normalized_identity_count,
    identity_counts.incomplete_normalized_identity_count,
    round(
        occurrence_counts.resolved_occurrence_count::NUMERIC
        / NULLIF(occurrence_counts.total_occurrence_count, 0),
        8
    ) AS resolution_coverage,
    round(
        occurrence_counts.unresolved_occurrence_count::NUMERIC
        / NULLIF(occurrence_counts.total_occurrence_count, 0),
        8
    ) AS abstention_rate
FROM occurrence_counts
JOIN identity_counts
  ON identity_counts.observation_resolution_run_id =
     occurrence_counts.observation_resolution_run_id
 AND identity_counts.normalization_derivation_run_id =
     occurrence_counts.normalization_derivation_run_id
JOIN corpus.observation_resolution_run AS resolution_run
  ON resolution_run.observation_resolution_run_id =
     occurrence_counts.observation_resolution_run_id
JOIN corpus.normalization_derivation_run AS run
  ON run.normalization_derivation_run_id =
     occurrence_counts.normalization_derivation_run_id
JOIN corpus.corpus_snapshot AS snapshot
  ON snapshot.corpus_snapshot_id = run.corpus_snapshot_id
JOIN corpus.normalization_pipeline AS pipeline
  ON pipeline.normalization_pipeline_id = run.normalization_pipeline_id;

COMMENT ON VIEW corpus.v_resolution_coverage IS
    'Run-scoped conservative exact-expression resolution coverage. Historical frozen policies remain separately visible and exclude normalized-phrase, trigram, graph, and polysemous suggestions.';

CREATE VIEW audit.v_retrieval_ablation AS
SELECT
    audit_set.retrieval_audit_set_key,
    evaluation.audit_split_code,
    baseline.retrieval_baseline_code,
    baseline.maximum_retrieval_tier_code,
    model_run.model_run_key,
    deterministic.top_k,
    deterministic.trigram_threshold,
    evaluation.retrieval_evaluation_key,
    evaluation.evaluated_at,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'recall_at_k'
          AND metric.cutoff_k = 1
    ) AS recall_at_1,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'recall_at_k'
          AND metric.cutoff_k = 3
    ) AS recall_at_3,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'recall_at_k'
          AND metric.cutoff_k = 5
    ) AS recall_at_5,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'mrr'
    ) AS mrr,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'ndcg_at_k'
          AND metric.cutoff_k = 5
    ) AS ndcg_at_5,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'coverage'
    ) AS coverage,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'abstention_rate'
    ) AS abstention_rate,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'abstention_error'
    ) AS abstention_error,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'median_candidate_set_size'
    ) AS median_candidate_set_size,
    max(metric.metric_value) FILTER (
        WHERE metric.retrieval_metric_code = 'unsafe_nonabstention'
    ) AS unsafe_nonabstention
FROM audit.retrieval_evaluation AS evaluation
JOIN audit.retrieval_audit_set AS audit_set
  ON audit_set.retrieval_audit_set_id = evaluation.retrieval_audit_set_id
JOIN ml.model_run AS model_run
  ON model_run.model_run_id = evaluation.model_run_id
JOIN ml.deterministic_retrieval_run AS deterministic
  ON deterministic.model_run_id = model_run.model_run_id
JOIN ref.retrieval_baseline AS baseline
  ON baseline.retrieval_baseline_code = deterministic.retrieval_baseline_code
LEFT JOIN audit.retrieval_metric_value AS metric
  ON metric.retrieval_evaluation_id = evaluation.retrieval_evaluation_id
GROUP BY
    audit_set.retrieval_audit_set_key,
    evaluation.audit_split_code,
    baseline.retrieval_baseline_code,
    baseline.maximum_retrieval_tier_code,
    model_run.model_run_key,
    deterministic.top_k,
    deterministic.trigram_threshold,
    evaluation.retrieval_evaluation_key,
    evaluation.evaluated_at;

COMMENT ON VIEW audit.v_retrieval_ablation IS
    'A/B/C/D language-retrieval metrics by split. These values are not coffee-flavour accuracy.';

ALTER TABLE corpus.ontology_extension_candidate
    ADD COLUMN retrieval_audit_case_id BIGINT NOT NULL,
    ADD CONSTRAINT ontology_extension_candidate_audit_case_fk FOREIGN KEY (
        retrieval_audit_case_id
    ) REFERENCES audit.retrieval_audit_case (retrieval_audit_case_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE corpus.ontology_extension_candidate_nearest_concept
    ADD COLUMN adjudicated_relevance_judgment_id BIGINT NOT NULL,
    ADD CONSTRAINT ontology_extension_nearest_adjudicated_judgment_fk FOREIGN KEY (
        adjudicated_relevance_judgment_id
    ) REFERENCES audit.retrieval_relevance_judgment (
        retrieval_relevance_judgment_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT;

CREATE FUNCTION corpus.enforce_ontology_extension_candidate_audit_context()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_ontology_extension_candidate_audit_context$
DECLARE
    valid_context_count BIGINT;
BEGIN
    SELECT count(*)
    INTO valid_context_count
    FROM corpus.corpus_statistic_run AS statistic_run
    JOIN corpus.normalization_derivation_run AS derivation
      ON derivation.normalization_derivation_run_id =
         statistic_run.normalization_derivation_run_id
    JOIN audit.retrieval_audit_case AS audit_case
      ON audit_case.retrieval_audit_case_id =
         NEW.retrieval_audit_case_id
    JOIN audit.retrieval_audit_set AS audit_set
      ON audit_set.retrieval_audit_set_id =
         audit_case.retrieval_audit_set_id
     AND audit_set.corpus_snapshot_id = derivation.corpus_snapshot_id
     AND audit_set.frozen_at IS NOT NULL
    JOIN corpus.lexical_expression_normalization AS normalization
      ON normalization.expression_id = audit_case.expression_id
     AND normalization.normalization_pipeline_id =
         derivation.normalization_pipeline_id
     AND normalization.normalized_expression_id =
         NEW.normalized_expression_id
    JOIN audit.retrieval_case_review AS adjudicated_review
      ON adjudicated_review.retrieval_audit_case_id =
         audit_case.retrieval_audit_case_id
     AND adjudicated_review.audit_review_role_code = 'adjudicated'
    WHERE statistic_run.corpus_statistic_run_id =
          NEW.corpus_statistic_run_id;

    IF valid_context_count IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'ontology_extension_candidate_audit_context_ck',
            MESSAGE = 'ontology_extension_candidate_audit_context_ck: candidate expression must match one adjudicated case in a frozen audit set for the statistic run pipeline and snapshot';
    END IF;

    RETURN NEW;
END;
$enforce_ontology_extension_candidate_audit_context$;

CREATE TRIGGER ontology_extension_candidate_audit_context_biu
BEFORE INSERT OR UPDATE
ON corpus.ontology_extension_candidate
FOR EACH ROW EXECUTE FUNCTION
    corpus.enforce_ontology_extension_candidate_audit_context();

CREATE FUNCTION corpus.enforce_ontology_extension_nearest_adjudication()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_ontology_extension_nearest_adjudication$
DECLARE
    valid_judgment_count BIGINT;
BEGIN
    SELECT count(*)
    INTO valid_judgment_count
    FROM corpus.ontology_extension_candidate AS candidate
    JOIN audit.retrieval_audit_case AS audit_case
      ON audit_case.retrieval_audit_case_id =
         candidate.retrieval_audit_case_id
    JOIN audit.retrieval_audit_set AS audit_set
      ON audit_set.retrieval_audit_set_id =
         audit_case.retrieval_audit_set_id
     AND audit_set.frozen_at IS NOT NULL
    JOIN audit.retrieval_relevance_judgment AS judgment
      ON judgment.retrieval_relevance_judgment_id =
         NEW.adjudicated_relevance_judgment_id
     AND judgment.concept_id = NEW.concept_id
    JOIN audit.retrieval_case_review AS adjudicated_review
      ON adjudicated_review.retrieval_case_review_id =
         judgment.retrieval_case_review_id
     AND adjudicated_review.retrieval_audit_case_id =
         candidate.retrieval_audit_case_id
     AND adjudicated_review.audit_review_role_code = 'adjudicated'
    WHERE candidate.ontology_extension_candidate_id =
          NEW.ontology_extension_candidate_id;

    IF valid_judgment_count IS DISTINCT FROM 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'ontology_extension_nearest_adjudication_ck',
            MESSAGE = 'ontology_extension_nearest_adjudication_ck: nearest concept must equal a judgment from the candidate case adjudicated review in its frozen audit set';
    END IF;

    RETURN NEW;
END;
$enforce_ontology_extension_nearest_adjudication$;

CREATE TRIGGER ontology_extension_nearest_adjudication_biu
BEFORE INSERT OR UPDATE
ON corpus.ontology_extension_candidate_nearest_concept
FOR EACH ROW EXECUTE FUNCTION
    corpus.enforce_ontology_extension_nearest_adjudication();

CREATE VIEW corpus.v_ontology_extension_feedback AS
SELECT
    candidate.ontology_extension_candidate_key,
    run.corpus_statistic_run_key,
    normalized.normalized_text,
    candidate.expression_frequency,
    candidate.publisher_diversity_count,
    candidate.information_lost,
    candidate.recommended_action,
    candidate.evidence_status,
    candidate.curation_status,
    audit_case.retrieval_audit_case_key,
    audit_case.audit_split_code,
    candidate.created_at,
    COALESCE(
        jsonb_agg(
            jsonb_build_object(
                'rank', nearest.candidate_rank,
                'concept_key', concept.concept_key,
                'comparison_basis', nearest.comparison_basis,
                'orthographic_similarity', nearest.orthographic_similarity,
                'information_preserved', nearest.information_preserved,
                'adjudicated_judgment_key',
                    judgment.retrieval_relevance_judgment_key,
                'adjudicated_relevance_grade',
                    judgment.relevance_grade_code
            ) ORDER BY nearest.candidate_rank
        ) FILTER (WHERE nearest.ontology_extension_candidate_nearest_concept_id IS NOT NULL),
        '[]'::JSONB
    ) AS nearest_concepts
FROM corpus.ontology_extension_candidate AS candidate
JOIN corpus.corpus_statistic_run AS run
  ON run.corpus_statistic_run_id = candidate.corpus_statistic_run_id
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalized_expression_id = candidate.normalized_expression_id
JOIN audit.retrieval_audit_case AS audit_case
  ON audit_case.retrieval_audit_case_id =
     candidate.retrieval_audit_case_id
LEFT JOIN corpus.ontology_extension_candidate_nearest_concept AS nearest
  ON nearest.ontology_extension_candidate_id =
     candidate.ontology_extension_candidate_id
LEFT JOIN kb.concept AS concept
  ON concept.concept_id = nearest.concept_id
LEFT JOIN audit.retrieval_relevance_judgment AS judgment
  ON judgment.retrieval_relevance_judgment_id =
     nearest.adjudicated_relevance_judgment_id
GROUP BY
    candidate.ontology_extension_candidate_id,
    candidate.ontology_extension_candidate_key,
    run.corpus_statistic_run_key,
    normalized.normalized_text,
    audit_case.retrieval_audit_case_key,
    audit_case.audit_split_code;

COMMENT ON VIEW corpus.v_ontology_extension_feedback IS
    'Corpus-observation feedback queue with explicit nearest canonical concepts. It cannot promote or alter canonical ontology rows.';

-- ONTOLOGY EXTENSION CANDIDATE INSERTION BOUNDARY
-- Candidate rows and nearest-concept comparisons may be added here only after
-- the independent held-out adjudication is frozen.  Corpus frequency alone is
-- insufficient evidence.  The following small queue contains only repeated,
-- publisher-diverse information-loss cases from the frozen 300-case audit.  It
-- creates no kb concept, lexicalization, relation, scheme membership, or
-- promotion event.

WITH configuration(value) AS (
    VALUES (
        '{
          "adjudication_sha256":"7e9b4ce21697ffd614cc11e89632394411d1bf1813bc331f0cc66a1b506ef6e8",
          "candidate_policy":"repeated publisher-diverse adjudicated information loss; no auto-promotion",
          "minimum_expression_frequency":2,
          "minimum_publisher_diversity_count":2,
          "reviewer_evidence_class":"CODEX_ASSISTED_PROJECT_ADJUDICATION",
          "source_statistic_run_key":"statistic_run.firstbloom_a6cb002_pilot_v1.v1",
          "shortlist_version":"round2b-adjudicated-information-loss-v1"
        }'::JSONB
    )
)
INSERT INTO corpus.corpus_statistic_run (
    corpus_statistic_run_key,
    normalization_derivation_run_id,
    statistical_method_id,
    dataset_id,
    version_label,
    code_commit_sha,
    configuration_sha256,
    configuration,
    sample_document_count,
    sample_observation_count,
    sample_occurrence_count,
    started_at,
    completed_at,
    frozen_at,
    result_inventory_sha256,
    value_semantics
)
SELECT
    'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1',
    source_run.normalization_derivation_run_id,
    source_run.statistical_method_id,
    source_run.dataset_id,
    'ontology-feedback-1',
    'a6abb4112cff3fc436b1613c37f9b40f51e65144',
    encode(sha256(convert_to(configuration.value::TEXT, 'UTF8')), 'hex'),
    configuration.value,
    source_run.sample_document_count,
    source_run.sample_observation_count,
    source_run.sample_occurrence_count,
    TIMESTAMPTZ '2026-08-24 08:31:00+00',
    NULL,
    NULL,
    NULL,
    'Governed ontology-feedback queue from adjudicated language observations; not sensory validity, similarity, or automatic ontology evidence.'
FROM corpus.corpus_statistic_run AS source_run
CROSS JOIN configuration
WHERE source_run.corpus_statistic_run_key =
      'statistic_run.firstbloom_a6cb002_pilot_v1.v1'
  AND source_run.frozen_at IS NOT NULL;

WITH selected_expression(normalized_text) AS (
    VALUES
        ('stone fruit'),
        ('watermelon'),
        ('clementine'),
        ('pecan'),
        ('passion fruit'),
        ('cashew'),
        ('gooseberry'),
        ('lilac'),
        ('macadamia'),
        ('honey melon'),
        ('rosemary')
)
INSERT INTO corpus.normalized_expression_frequency (
    normalized_expression_frequency_key,
    corpus_statistic_run_id,
    normalized_expression_id,
    expression_frequency,
    document_frequency,
    publisher_prevalence_count,
    publisher_sample_count,
    country_prevalence_count,
    country_sample_count,
    composite_reference_occurrence_count,
    qualifier_occurrence_count,
    unresolved_occurrence_count,
    value_semantics
)
SELECT
    'frequency.round2b.ontology_feedback.' ||
        encode(sha256(convert_to(normalized.normalized_text, 'UTF8')), 'hex'),
    feedback_run.corpus_statistic_run_id,
    source_frequency.normalized_expression_id,
    source_frequency.expression_frequency,
    source_frequency.document_frequency,
    source_frequency.publisher_prevalence_count,
    source_frequency.publisher_sample_count,
    source_frequency.country_prevalence_count,
    source_frequency.country_sample_count,
    source_frequency.composite_reference_occurrence_count,
    source_frequency.qualifier_occurrence_count,
    source_frequency.unresolved_occurrence_count,
    'Exact copied frequency receipt from the frozen pilot statistic run for a governed ontology-feedback expression; no sensory validity is implied.'
FROM selected_expression
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalized_text = selected_expression.normalized_text
JOIN corpus.normalized_expression_frequency AS source_frequency
  ON source_frequency.normalized_expression_id =
     normalized.normalized_expression_id
JOIN corpus.corpus_statistic_run AS source_run
  ON source_run.corpus_statistic_run_id =
     source_frequency.corpus_statistic_run_id
 AND source_run.corpus_statistic_run_key =
     'statistic_run.firstbloom_a6cb002_pilot_v1.v1'
CROSS JOIN corpus.corpus_statistic_run AS feedback_run
WHERE feedback_run.corpus_statistic_run_key =
      'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1';

WITH candidate_seed (
    normalized_text,
    information_lost,
    recommended_action,
    curation_status
) AS (
    VALUES
        ('stone fruit',
         'The orchard-fruit grouping does not preserve the repeatedly observed stone-fruit grouping as its own language abstraction.',
         'Evaluate a category or controlled lexical abstraction; do not model it as a universal sensory axis.',
         'OPEN'),
        ('watermelon',
         'The generic fruit category loses the explicit watermelon reference.',
         'Review as a candidate sensory attribute against coffee-specific sensory evidence.',
         'OPEN'),
        ('clementine',
         'Orange and citrus preserve the family but not the clementine-specific reference.',
         'Review whether a narrower attribute is independently supported or should remain a lexical normalization to orange.',
         'OPEN'),
        ('pecan',
         'The nut/seed category loses the explicit pecan reference.',
         'Review as a candidate sensory attribute against coffee-specific sensory evidence.',
         'OPEN'),
        ('passion fruit',
         'The tropical-fruit grouping loses the explicit passion-fruit reference.',
         'Review as a candidate sensory attribute against coffee-specific sensory evidence.',
         'OPEN'),
        ('cashew',
         'The nut/seed category loses the explicit cashew reference.',
         'Review as a candidate sensory attribute while keeping the limited pilot diversity explicit.',
         'OPEN'),
        ('gooseberry',
         'Broad berry and fruit categories lose the explicit gooseberry reference.',
         'Review as a candidate sensory attribute and adjudicate canonical grouping separately from source schemes.',
         'OPEN'),
        ('lilac',
         'The floral grouping loses the explicit lilac reference.',
         'Review as a candidate sensory attribute against coffee-specific sensory evidence.',
         'OPEN'),
        ('macadamia',
         'The nut/seed category loses the explicit macadamia reference; a separate macadamia-nut surface is also observed.',
         'Review one concept with governed lexical variants rather than create duplicate concepts from two surfaces.',
         'OPEN'),
        ('honey melon',
         'The fruit category loses the melon reference, while the surface may be read as a compound rather than a honey component.',
         'Defer pending semantic review of melon versus honeydew-like usage and external coffee evidence.',
         'DEFERRED'),
        ('rosemary',
         'The green/herbal category loses the explicit rosemary reference.',
         'Review as a candidate sensory attribute and avoid confusion with rose.',
         'OPEN')
),
adjudicated_cases AS (
    SELECT
        normalization.normalized_expression_id,
        audit_case.retrieval_audit_case_id
    FROM audit.retrieval_audit_set AS audit_set
    JOIN audit.retrieval_audit_case AS audit_case
      ON audit_case.retrieval_audit_set_id =
         audit_set.retrieval_audit_set_id
    JOIN corpus.lexical_expression_normalization AS normalization
      ON normalization.expression_id = audit_case.expression_id
    JOIN audit.retrieval_case_review AS adjudicated_review
      ON adjudicated_review.retrieval_audit_case_id =
         audit_case.retrieval_audit_case_id
     AND adjudicated_review.audit_review_role_code = 'adjudicated'
    WHERE audit_set.retrieval_audit_set_key =
          'audit_set.round2b.firstbloom_pilot_v1'
      AND audit_set.frozen_at IS NOT NULL
)
INSERT INTO corpus.ontology_extension_candidate (
    ontology_extension_candidate_key,
    corpus_statistic_run_id,
    normalized_expression_id,
    retrieval_audit_case_id,
    expression_frequency,
    publisher_diversity_count,
    information_lost,
    recommended_action,
    evidence_status,
    curation_status,
    created_at
)
SELECT
    'ontology_extension_candidate.round2b.' ||
        encode(sha256(convert_to(candidate_seed.normalized_text, 'UTF8')), 'hex'),
    feedback_run.corpus_statistic_run_id,
    normalized.normalized_expression_id,
    adjudicated_cases.retrieval_audit_case_id,
    frequency.expression_frequency,
    frequency.publisher_prevalence_count,
    candidate_seed.information_lost,
    candidate_seed.recommended_action,
    'REQUIRES_COFFEE_SENSORY_EVIDENCE',
    candidate_seed.curation_status,
    TIMESTAMPTZ '2026-08-24 08:31:00+00'
FROM candidate_seed
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalized_text = candidate_seed.normalized_text
JOIN adjudicated_cases
  ON adjudicated_cases.normalized_expression_id =
     normalized.normalized_expression_id
CROSS JOIN corpus.corpus_statistic_run AS feedback_run
JOIN corpus.normalized_expression_frequency AS frequency
  ON frequency.corpus_statistic_run_id =
     feedback_run.corpus_statistic_run_id
 AND frequency.normalized_expression_id = normalized.normalized_expression_id
WHERE feedback_run.corpus_statistic_run_key =
      'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1';

WITH nearest_seed (
    normalized_text,
    candidate_rank,
    concept_key,
    information_preserved
) AS (
    VALUES
        ('stone fruit', 1, 'category.orchard_fruit', 'Preserves a broad orchard-fruit grouping but not the stone-fruit abstraction.'),
        ('watermelon', 1, 'category.fruit', 'Preserves only the generic fruit grouping.'),
        ('clementine', 1, 'sensory.orange', 'Preserves a close citrus-fruit reference but not clementine specificity.'),
        ('clementine', 2, 'category.citrus', 'Preserves only the broad citrus grouping.'),
        ('pecan', 1, 'category.nut_seed', 'Preserves only the broad nut/seed grouping.'),
        ('passion fruit', 1, 'category.tropical_fruit', 'Preserves the tropical-fruit grouping.'),
        ('passion fruit', 2, 'category.fruit', 'Preserves only the generic fruit grouping.'),
        ('cashew', 1, 'category.nut_seed', 'Preserves only the broad nut/seed grouping.'),
        ('gooseberry', 1, 'category.berry', 'Preserves a defensible berry grouping without the explicit reference.'),
        ('gooseberry', 2, 'category.fruit', 'Preserves only the generic fruit grouping.'),
        ('lilac', 1, 'category.floral', 'Preserves only the broad floral grouping.'),
        ('macadamia', 1, 'category.nut_seed', 'Preserves only the broad nut/seed grouping.'),
        ('honey melon', 1, 'category.fruit', 'Preserves only the generic fruit grouping and not the compound interpretation.'),
        ('rosemary', 1, 'category.green_herbal', 'Preserves only the broad green/herbal grouping.')
)
INSERT INTO corpus.ontology_extension_candidate_nearest_concept (
    ontology_extension_candidate_nearest_concept_key,
    ontology_extension_candidate_id,
    concept_id,
    adjudicated_relevance_judgment_id,
    candidate_rank,
    comparison_basis,
    orthographic_similarity,
    information_preserved
)
SELECT
    'ontology_extension_nearest.round2b.' ||
        encode(
            sha256(convert_to(
                nearest_seed.normalized_text || E'\x1f' ||
                nearest_seed.concept_key,
                'UTF8'
            )),
            'hex'
        ),
    candidate.ontology_extension_candidate_id,
    concept.concept_id,
    judgment.retrieval_relevance_judgment_id,
    nearest_seed.candidate_rank,
    'Independent Round 2B graded semantic adjudication; not corpus co-occurrence or sensory similarity.',
    NULL,
    nearest_seed.information_preserved
FROM nearest_seed
JOIN corpus.normalized_expression AS normalized
  ON normalized.normalized_text = nearest_seed.normalized_text
JOIN corpus.ontology_extension_candidate AS candidate
  ON candidate.normalized_expression_id = normalized.normalized_expression_id
JOIN corpus.corpus_statistic_run AS feedback_run
  ON feedback_run.corpus_statistic_run_id =
     candidate.corpus_statistic_run_id
 AND feedback_run.corpus_statistic_run_key =
     'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
JOIN kb.concept AS concept
  ON concept.concept_key = nearest_seed.concept_key
JOIN audit.retrieval_case_review AS adjudicated_review
  ON adjudicated_review.retrieval_audit_case_id =
     candidate.retrieval_audit_case_id
 AND adjudicated_review.audit_review_role_code = 'adjudicated'
JOIN audit.retrieval_relevance_judgment AS judgment
  ON judgment.retrieval_case_review_id =
     adjudicated_review.retrieval_case_review_id
 AND judgment.concept_id = concept.concept_id;

WITH result_receipt AS (
    SELECT string_agg(receipt_line, E'\n' ORDER BY receipt_line) AS inventory
    FROM (
        SELECT
            'F|' || normalized.normalized_text || '|' ||
            frequency.expression_frequency || '|' ||
            frequency.document_frequency || '|' ||
            frequency.publisher_prevalence_count AS receipt_line
        FROM corpus.normalized_expression_frequency AS frequency
        JOIN corpus.normalized_expression AS normalized
          ON normalized.normalized_expression_id =
             frequency.normalized_expression_id
        JOIN corpus.corpus_statistic_run AS run
          ON run.corpus_statistic_run_id = frequency.corpus_statistic_run_id
        WHERE run.corpus_statistic_run_key =
              'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
        UNION ALL
        SELECT
            'C|' || normalized.normalized_text || '|' ||
            candidate.expression_frequency || '|' ||
            candidate.publisher_diversity_count || '|' ||
            candidate.curation_status || '|' ||
            audit_case.retrieval_audit_case_key
        FROM corpus.ontology_extension_candidate AS candidate
        JOIN corpus.normalized_expression AS normalized
          ON normalized.normalized_expression_id =
             candidate.normalized_expression_id
        JOIN corpus.corpus_statistic_run AS run
          ON run.corpus_statistic_run_id = candidate.corpus_statistic_run_id
        JOIN audit.retrieval_audit_case AS audit_case
          ON audit_case.retrieval_audit_case_id =
             candidate.retrieval_audit_case_id
        WHERE run.corpus_statistic_run_key =
              'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
        UNION ALL
        SELECT
            'N|' || normalized.normalized_text || '|' ||
            nearest.candidate_rank || '|' || concept.concept_key || '|' ||
            judgment.retrieval_relevance_judgment_key || '|' ||
            judgment.relevance_grade_code
        FROM corpus.ontology_extension_candidate_nearest_concept AS nearest
        JOIN corpus.ontology_extension_candidate AS candidate
          ON candidate.ontology_extension_candidate_id =
             nearest.ontology_extension_candidate_id
        JOIN corpus.normalized_expression AS normalized
          ON normalized.normalized_expression_id =
             candidate.normalized_expression_id
        JOIN kb.concept AS concept
          ON concept.concept_id = nearest.concept_id
        JOIN audit.retrieval_relevance_judgment AS judgment
          ON judgment.retrieval_relevance_judgment_id =
             nearest.adjudicated_relevance_judgment_id
        JOIN corpus.corpus_statistic_run AS run
          ON run.corpus_statistic_run_id = candidate.corpus_statistic_run_id
        WHERE run.corpus_statistic_run_key =
              'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
    ) AS receipt_lines
)
UPDATE corpus.corpus_statistic_run AS run
SET completed_at = TIMESTAMPTZ '2026-08-24 08:31:00+00',
    frozen_at = TIMESTAMPTZ '2026-08-24 08:31:00+00',
    result_inventory_sha256 = encode(
        sha256(convert_to(result_receipt.inventory, 'UTF8')),
        'hex'
    )
FROM result_receipt
WHERE run.corpus_statistic_run_key =
      'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1';

CREATE FUNCTION audit.run_round2b_validation_queries()
RETURNS TABLE (
    check_key TEXT,
    violation_count BIGINT,
    passed BOOLEAN
)
LANGUAGE SQL
STABLE
SET search_path = pg_catalog
AS $run_round2b_validation_queries$
    WITH pilot_snapshot AS (
        SELECT snapshot.*
        FROM corpus.corpus_snapshot AS snapshot
        WHERE snapshot.corpus_snapshot_key =
              'corpus_snapshot.firstbloom_a6cb002_pilot_v1'
    ),
    pilot_observations AS (
        SELECT observation.*, document.raw_text_sha256
        FROM corpus.raw_observation AS observation
        JOIN corpus.captured_document AS document
          ON document.captured_document_id =
             observation.captured_document_id
        JOIN pilot_snapshot
          ON pilot_snapshot.corpus_id = document.corpus_id
    ),
    pilot_occurrences AS (
        SELECT
            occurrence.*,
            observation_expression.expression_id,
            observation_expression.observation_expression_key
        FROM corpus.normalized_expression_occurrence AS occurrence
        JOIN corpus.normalization_derivation_run AS derivation
          ON derivation.normalization_derivation_run_id =
             occurrence.normalization_derivation_run_id
         AND derivation.normalization_derivation_run_key =
             'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
        JOIN corpus.observation_expression AS observation_expression
          ON observation_expression.observation_expression_id =
             occurrence.observation_expression_id
    ),
    eligible_lexicalizations AS (
        SELECT
            lexicalization.expression_id,
            lexicalization.concept_id,
            lexicalization.lexicalization_id,
            CASE lexicalization.mapping_type_code
                WHEN 'preferred_label' THEN 1
                WHEN 'approved_variant' THEN 2
            END AS mapping_precedence,
            lexicalization.lexicalization_key
        FROM kb.lexicalization AS lexicalization
        JOIN kb.concept AS concept
          ON concept.concept_id = lexicalization.concept_id
         AND concept.lifecycle_status_code = 'active'
        WHERE lexicalization.lifecycle_status_code = 'active'
          AND lexicalization.mapping_type_code IN (
              'preferred_label', 'approved_variant'
          )
          AND lexicalization.valid_from <=
              TIMESTAMPTZ '2026-08-24 08:31:00+00'
          AND (
              lexicalization.valid_until IS NULL
              OR lexicalization.valid_until >
                 TIMESTAMPTZ '2026-08-24 08:31:00+00'
          )
    ),
    eligible_concepts AS (
        SELECT
            eligible_lexicalizations.expression_id,
            eligible_lexicalizations.concept_id,
            (array_agg(
                eligible_lexicalizations.lexicalization_id
                ORDER BY
                    eligible_lexicalizations.mapping_precedence,
                    eligible_lexicalizations.lexicalization_key,
                    eligible_lexicalizations.lexicalization_id
            ))[1] AS lexicalization_id
        FROM eligible_lexicalizations
        GROUP BY
            eligible_lexicalizations.expression_id,
            eligible_lexicalizations.concept_id
    ),
    eligible_summary AS (
        SELECT
            eligible_concepts.expression_id,
            count(*) AS concept_count,
            min(eligible_concepts.lexicalization_id) AS lexicalization_id
        FROM eligible_concepts
        GROUP BY eligible_concepts.expression_id
    ),
    selected_resolution_run AS (
        SELECT resolution_run.*
        FROM corpus.observation_resolution_run AS resolution_run
        WHERE resolution_run.observation_resolution_run_key =
              'resolution_run.firstbloom_a6cb002_pilot_v1.exact_v1'
          AND resolution_run.frozen_at IS NOT NULL
    ),
    selected_resolution_results AS (
        SELECT result.*
        FROM corpus.observation_resolution_run_result AS result
        JOIN selected_resolution_run
          ON selected_resolution_run.observation_resolution_run_id =
             result.observation_resolution_run_id
    ),
    latest_frozen_resolution_run AS (
        SELECT resolution_run.*
        FROM corpus.observation_resolution_run AS resolution_run
        JOIN corpus.normalization_derivation_run AS derivation
          ON derivation.normalization_derivation_run_id =
             resolution_run.normalization_derivation_run_id
        WHERE derivation.normalization_derivation_run_key =
              'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'
          AND resolution_run.frozen_at IS NOT NULL
        ORDER BY
            resolution_run.resolution_as_of DESC,
            resolution_run.observation_resolution_run_id DESC
        LIMIT 1
    ),
    latest_frozen_resolution_results AS (
        SELECT result.*
        FROM corpus.observation_resolution_run_result AS result
        JOIN latest_frozen_resolution_run
          ON latest_frozen_resolution_run.observation_resolution_run_id =
             result.observation_resolution_run_id
    ),
    selected_audit_set AS (
        SELECT audit_set.*
        FROM audit.retrieval_audit_set AS audit_set
        WHERE audit_set.retrieval_audit_set_key =
              'audit_set.round2b.firstbloom_pilot_v1'
    ),
    selected_audit_cases AS (
        SELECT audit_case.*
        FROM audit.retrieval_audit_case AS audit_case
        JOIN selected_audit_set
          ON selected_audit_set.retrieval_audit_set_id =
             audit_case.retrieval_audit_set_id
    ),
    selected_model_runs AS (
        SELECT
            model_run.*,
            deterministic.retrieval_baseline_code,
            deterministic.normalization_pipeline_id,
            deterministic.retrieval_graph_policy_id,
            deterministic.top_k,
            deterministic.trigram_threshold
        FROM ml.model_run AS model_run
        JOIN ml.deterministic_retrieval_run AS deterministic
          ON deterministic.model_run_id = model_run.model_run_id
        WHERE model_run.model_run_key ~
              '^model_run[.]round2b[.]deterministic_retrieval_v1[.][ABCD]$'
    ),
    recomputed_metrics AS (
        SELECT
            evaluation.retrieval_evaluation_id,
            calculated.retrieval_metric_code,
            calculated.cutoff_k,
            calculated.numerator,
            calculated.denominator,
            calculated.metric_value,
            calculated.value_semantics
        FROM audit.retrieval_evaluation AS evaluation
        JOIN selected_audit_set
          ON selected_audit_set.retrieval_audit_set_id =
             evaluation.retrieval_audit_set_id
        JOIN selected_model_runs
          ON selected_model_runs.model_run_id = evaluation.model_run_id
        CROSS JOIN LATERAL audit.calculate_retrieval_metrics(
            'audit_set.round2b.firstbloom_pilot_v1',
            selected_model_runs.model_run_key,
            evaluation.audit_split_code
        ) AS calculated
    ),
    frozen_resolution_inventory AS (
        SELECT encode(
            sha256(convert_to(
                string_agg(
                    pilot_occurrences.observation_expression_key || '|' ||
                    result.resolution_status_code || '|' ||
                    COALESCE(lexicalization.lexicalization_key, ''),
                    E'\n' ORDER BY
                        pilot_occurrences.observation_expression_key
                ),
                'UTF8'
            )),
            'hex'
        ) AS inventory_sha256
        FROM pilot_occurrences
        JOIN selected_resolution_results AS result
          ON result.observation_expression_id =
             pilot_occurrences.observation_expression_id
        LEFT JOIN kb.lexicalization AS lexicalization
          ON lexicalization.lexicalization_id =
             result.lexicalization_id
    ),
    violations AS (
        SELECT 'canonical_concept_snapshot'::TEXT AS check_key,
               (
                   abs(count(*) - 130)
                   + abs(count(*) FILTER (
                       WHERE lifecycle_status_code = 'active'
                     ) - 114)
                   + abs(count(*) FILTER (
                       WHERE lifecycle_status_code = 'active'
                         AND concept_type_code = 'sensory_attribute'
                     ) - 92)
                   + abs(count(*) FILTER (
                       WHERE lifecycle_status_code = 'candidate'
                         AND concept_type_code = 'sensory_attribute'
                     ) - 8)
                   + abs(count(*) FILTER (
                       WHERE lifecycle_status_code = 'active'
                         AND concept_type_code = 'category'
                     ) - 20)
               )::BIGINT AS violation_count
        FROM kb.concept

        UNION ALL
        SELECT 'canonical_relation_and_scheme_snapshot',
               (
                   (SELECT abs(count(*) - 110) FROM kb.concept_relation)
                   + (SELECT abs(count(*) - 100)
                      FROM kb.concept_relation AS relation
                      WHERE relation.lifecycle_status_code = 'active'
                        AND relation.valid_from <=
                            TIMESTAMPTZ '2026-08-24 08:31:00+00'
                        AND (
                            relation.valid_until IS NULL
                            OR relation.valid_until >
                               TIMESTAMPTZ '2026-08-24 08:31:00+00'
                        ))
                   + (SELECT abs(count(*) - 6)
                      FROM kb.concept_dimension_link)
                   + (SELECT abs(count(*) - 2)
                      FROM evidence.concept_scheme)
                   + (SELECT abs(count(*) - 106)
                      FROM evidence.concept_scheme_edge)
                   + (SELECT abs(count(*) - 145)
                      FROM evidence.concept_scheme_mapping)
               )::BIGINT

        UNION ALL
        SELECT 'lexical_dictionary_snapshot',
               (
                   (SELECT abs(count(*) - 1780)
                    FROM kb.lexical_expression)
                   + (SELECT abs(count(*) - 134)
                      FROM kb.lexicalization)
                   + (SELECT abs(count(*) - 134)
                      FROM kb.lexicalization AS lexicalization
                      WHERE lexicalization.lifecycle_status_code = 'active'
                        AND lexicalization.valid_from <=
                            TIMESTAMPTZ '2026-08-24 08:31:00+00'
                        AND (
                            lexicalization.valid_until IS NULL
                            OR lexicalization.valid_until >
                               TIMESTAMPTZ '2026-08-24 08:31:00+00'
                        ))
                   + (SELECT abs(count(*) - 1780)
                      FROM corpus.lexical_expression_normalization)
                   + (SELECT abs(count(*) - 1777)
                      FROM corpus.normalized_expression)
               )::BIGINT

        UNION ALL
        SELECT 'observed_expression_governance',
               (
                   abs(count(*) - 1646)
                   + count(*) FILTER (
                       WHERE expression.lifecycle_status_code <> 'candidate'
                          OR expression.language_tag_code <> 'en'
                          OR EXISTS (
                              SELECT 1
                              FROM kb.lexicalization AS lexicalization
                              WHERE lexicalization.expression_id =
                                    expression.expression_id
                          )
                     )
               )::BIGINT
        FROM kb.lexical_expression AS expression
        WHERE expression.expression_key LIKE 'expression.observed.%'

        UNION ALL
        SELECT 'source_policy_inventory',
               (
                   abs(count(*) - 15)
                   + abs(count(*) FILTER (
                       WHERE corpus_source_decision_code =
                             'allow_derived_terms'
                     ) - 1)
                   + abs(count(*) FILTER (
                       WHERE corpus_source_decision_code = 'blocked'
                     ) - 8)
                   + abs(count(*) FILTER (
                       WHERE corpus_source_decision_code = 'manual_only'
                     ) - 3)
                   + abs(count(*) FILTER (
                       WHERE corpus_source_decision_code = 'unknown'
                     ) - 3)
               )::BIGINT
        FROM corpus.source_policy_review

        UNION ALL
        SELECT 'source_policy_blocking_permissions', count(*)
        FROM corpus.source_policy_review AS policy
        WHERE policy.corpus_source_decision_code IN ('blocked', 'unknown')
          AND (
              policy.document_metadata_allowed
              OR policy.raw_retention_allowed
              OR policy.derived_terms_allowed
              OR policy.derived_terms_redistribution_allowed
              OR policy.raw_redistribution_allowed
              OR policy.automated_acquisition_allowed
          )

        UNION ALL
        SELECT 'firstbloom_rights_boundary',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE policy.domain <> 'github.com'
                      OR policy.corpus_source_decision_code <>
                         'allow_derived_terms'
                      OR NOT policy.document_metadata_allowed
                      OR policy.raw_retention_allowed
                      OR NOT policy.derived_terms_allowed
                      OR NOT policy.derived_terms_redistribution_allowed
                      OR policy.raw_redistribution_allowed
                      OR policy.automated_acquisition_allowed
               )
        FROM corpus.source_policy_review AS policy
        WHERE policy.source_policy_review_key =
              'source_policy.firstbloom.a6cb002.derived_terms'

        UNION ALL
        SELECT 'source_policy_matrix_projection',
               abs(count(*) - 15)
               + abs(count(*) FILTER (
                   WHERE review_country_code IS NOT NULL
                 ) - 14)
        FROM corpus.v_source_policy_matrix

        UNION ALL
        SELECT 'pilot_snapshot_identity',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE snapshot.expected_document_count <> 2474
                      OR snapshot.expected_observation_count <> 6818
                      OR snapshot.expected_normalized_expression_count <> 1713
                      OR snapshot.source_inventory_sha256 <>
                         'ce659e34c1f96b457789f720692e214b0ad5b021bf409c769cfc0df874036bda'
                      OR snapshot.document_inventory_sha256 <>
                         '75132e0bda01641cef8a1ad042ac1d5d313df894383617822c557c32578e2c53'
                      OR snapshot.code_commit_sha <>
                         'd90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0'
                      OR snapshot.frozen_at IS NULL
                      OR snapshot.raw_public_reproducibility_complete
               )
        FROM pilot_snapshot AS snapshot

        UNION ALL
        SELECT 'pilot_sampling_frame_identity',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE frame.language_tag_code <> 'en'
                      OR frame.frame_sha256 <>
                         '3da254bf0ab64e73e532aad31125ab51050b0f56556eb6e6a0025377db25d7cf'
               )
        FROM corpus.sampling_frame AS frame
        WHERE frame.sampling_frame_key =
              'sampling_frame.firstbloom_a6cb002_pilot_v1'

        UNION ALL
        SELECT 'pilot_inventory_projection',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE inventory.source_policy_count <> 1
                      OR inventory.publisher_count <> 215
                      OR inventory.acquisition_batch_count <> 16
                      OR inventory.document_count <> 2474
                      OR inventory.product_count <> 2383
                      OR inventory.raw_observation_count <> 6818
                      OR inventory.retained_phrase_count <> 5564
                      OR inventory.hash_only_observation_count <> 1254
                      OR inventory.normalized_occurrence_count <> 5564
                      OR inventory.unique_normalized_expression_count <> 1713
               )
        FROM corpus.v_corpus_inventory AS inventory
        WHERE inventory.corpus_snapshot_key =
              'corpus_snapshot.firstbloom_a6cb002_pilot_v1'

        UNION ALL
        SELECT 'pilot_source_and_entity_inventory',
               (
                   (SELECT abs(count(*) - 215)
                    FROM corpus.corpus_snapshot_source AS source_member
                    JOIN pilot_snapshot
                      ON pilot_snapshot.corpus_snapshot_id =
                         source_member.corpus_snapshot_id)
                   + (SELECT abs(count(DISTINCT source_member.source_policy_review_id) - 1)
                      FROM corpus.corpus_snapshot_source AS source_member
                      JOIN pilot_snapshot
                        ON pilot_snapshot.corpus_snapshot_id =
                           source_member.corpus_snapshot_id)
                   + (SELECT abs(count(*) - 215)
                      FROM corpus.industry_publisher)
                   + (SELECT abs(count(*) - 215)
                      FROM corpus.industry_publisher
                      WHERE roaster_country_code IS NULL)
                   + (SELECT abs(count(*) - 2383)
                      FROM corpus.industry_product)
                   + (SELECT abs(count(*) - 16)
                      FROM corpus.acquisition_batch AS batch
                      JOIN pilot_snapshot
                        ON pilot_snapshot.corpus_snapshot_id =
                           batch.corpus_snapshot_id)
               )::BIGINT

        UNION ALL
        SELECT 'pilot_document_rights_boundary',
               abs(count(*) - 2474)
               + count(*) FILTER (
                   WHERE document.raw_text IS NOT NULL
                      OR document.raw_text_sha256 IS NULL
                      OR document.content_sha256 IS NULL
                      OR document.metadata_composite_sha256 IS NULL
                      OR document.source_policy_review_id IS NULL
                      OR document.industry_product_id IS NULL
                      OR document.acquisition_batch_id IS NULL
               )
        FROM corpus.captured_document AS document
        JOIN pilot_snapshot
          ON pilot_snapshot.corpus_id = document.corpus_id

        UNION ALL
        SELECT 'pilot_observation_retention_inventory',
               abs(count(*) - 6818)
               + abs(count(*) FILTER (
                   WHERE observation_retention_code = 'derived_phrase'
                 ) - 5564)
               + abs(count(*) FILTER (
                   WHERE observation_retention_code = 'hash_only'
                 ) - 1254)
               + count(*) FILTER (
                   WHERE observation_sha256 IS NULL
                      OR character_count IS NULL
                      OR observation_metadata ->> 'parser_version' <>
                         'round2b-delimiter-parser-v1'
                      OR observation_metadata ->>
                         'complete_note_string_stored' <> 'false'
                      OR observation_retention_code = 'derived_phrase'
                         AND (
                             observation_text IS NULL
                             OR character_count > 80
                             OR character_count <>
                                char_length(observation_text)
                         )
                      OR observation_retention_code = 'hash_only'
                         AND observation_text IS NOT NULL
               )
        FROM pilot_observations

        UNION ALL
        SELECT 'pilot_hash_only_reason_inventory',
               abs(count(*) - 1254)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' = 'dual_review_disagreement') - 176)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'dual_review_narrative_or_non_descriptor') - 75)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' = 'dual_review_non_english') - 111)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' = 'dual_review_uncertain') - 9)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'rights_boundary_gt_80_unicode_characters') - 85)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'rights_complete_field_surface') - 502)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'structural_gate_control_or_format_character') - 2)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'structural_gate_gt_8_word_tokens') - 11)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'structural_gate_repeated_connective') - 1)
               + abs(count(*) FILTER (WHERE observation_metadata ->>
                   'exclusion_reason' =
                   'structural_gate_sentence_punctuation') - 282)
        FROM pilot_observations
        WHERE observation_retention_code = 'hash_only'

        UNION ALL
        SELECT 'complete_source_fields_not_admitted_globally', count(*)
        FROM corpus.raw_observation AS observation
        JOIN corpus.captured_document AS document
          ON document.raw_text_sha256 = observation.observation_sha256
        WHERE observation.observation_retention_code = 'derived_phrase'

        UNION ALL
        SELECT 'pilot_observation_expression_boundary', count(*)
        FROM pilot_observations AS observation
        WHERE (
            observation.observation_retention_code = 'derived_phrase'
            AND (
                SELECT count(*)
                FROM corpus.observation_expression AS occurrence
                JOIN kb.lexical_expression AS expression
                  ON expression.expression_id = occurrence.expression_id
                WHERE occurrence.raw_observation_id =
                      observation.raw_observation_id
                  AND expression.language_tag_code = 'en'
            ) <> 1
        ) OR (
            observation.observation_retention_code = 'hash_only'
            AND EXISTS (
                SELECT 1
                FROM corpus.observation_expression AS occurrence
                WHERE occurrence.raw_observation_id =
                      observation.raw_observation_id
            )
        )

        UNION ALL
        SELECT 'pilot_duplicate_review_closure',
               (SELECT abs(count(*) - 129)
                FROM corpus.v_document_duplicate_candidates)
               + abs(count(*) - 129)
               + abs(count(*) FILTER (
                   WHERE review.duplicate_match_basis_code = 'content_hash'
                     AND review.duplicate_review_decision_code = 'distinct'
                 ) - 33)
               + abs(count(*) FILTER (
                   WHERE review.duplicate_match_basis_code =
                         'publisher_product_key'
                     AND review.duplicate_review_decision_code = 'distinct'
                 ) - 96)
        FROM corpus.document_duplicate_review AS review

        UNION ALL
        SELECT 'normalization_pipeline_identity',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE pipeline.version_label <> '1'
                      OR pipeline.language_tag_code <> 'en'
                      OR pipeline.unicode_form <> 'NFC'
                      OR pipeline.rules_sha256 <>
                         'b32e4aec8b6ceacd067c5dd920996d4d71603647b49bbc910cd7ebcc32922824'
                      OR pipeline.code_commit_sha <>
                         'd90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0'
                      OR pipeline.parser_version <>
                         'round2b-pilot-generator-v2-dual-review'
                      OR pipeline.frozen_at IS NULL
               )
        FROM corpus.normalization_pipeline AS pipeline
        WHERE pipeline.normalization_pipeline_key = 'normalization.en_v1'

        UNION ALL
        SELECT 'normalization_rule_and_identity_inventory',
               (SELECT abs(count(*) - 3)
                FROM corpus.normalization_rule AS rule
                JOIN corpus.normalization_pipeline AS pipeline
                  ON pipeline.normalization_pipeline_id =
                     rule.normalization_pipeline_id
                WHERE pipeline.normalization_pipeline_key =
                      'normalization.en_v1')
               + (SELECT abs(count(*) - 1780)
                  FROM corpus.lexical_expression_normalization)
               + (SELECT abs(count(*) - 1777)
                  FROM corpus.normalized_expression)

        UNION ALL
        SELECT 'normalization_derivation_receipt',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE derivation.code_commit_sha <>
                         'd90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0'
                      OR derivation.input_inventory_sha256 <>
                         '792ed3e77f7975c92b6feb8de0124cc047245c2d2640280913a8a94ef16e18c7'
                      OR derivation.output_inventory_sha256 <>
                         '301c45168413d1cf281f7c5a927bbc0e8ce57910dc68bf0cb07ec5ef8a845d76'
                      OR derivation.input_observation_count <> 6818
                      OR derivation.output_occurrence_count <> 5564
                      OR derivation.frozen_at IS NULL
               )
        FROM corpus.normalization_derivation_run AS derivation
        WHERE derivation.normalization_derivation_run_key =
              'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'

        UNION ALL
        SELECT 'normalization_occurrence_integrity',
               abs(count(*) - 5564)
               + abs(count(DISTINCT normalized_expression_id) - 1713)
               + count(*) FILTER (
                   WHERE source_offset_unit <> 'UNICODE_CODE_POINT'
                      OR source_character_start < 0
                      OR source_character_end <= source_character_start
               )
        FROM pilot_occurrences

        UNION ALL
        SELECT 'main_statistic_run_receipt',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE run.code_commit_sha <>
                         'd90b0bd3ee52b449fa1cebf7fca64e6f05ce8aa0'
                      OR run.configuration_sha256 <>
                         'a21af2ec3f055ee23b0286290d51dea86cdbf1617a5ded9a55841c2245457254'
                      OR run.result_inventory_sha256 <>
                         '4c785a338f5b61b703dd253d98beda92d86635db8f0ceac290f81a70eaac7092'
                      OR run.sample_document_count <> 2474
                      OR run.sample_observation_count <> 6818
                      OR run.sample_occurrence_count <> 5564
                      OR run.frozen_at IS NULL
               )
        FROM corpus.corpus_statistic_run AS run
        WHERE run.corpus_statistic_run_key =
              'statistic_run.firstbloom_a6cb002_pilot_v1.v1'

        UNION ALL
        SELECT 'main_statistic_artifact_inventory',
               (SELECT abs(count(*) - 1713)
                       + abs(
                           COALESCE(sum(frequency.expression_frequency), 0)
                           - 5564
                       )
                FROM corpus.normalized_expression_frequency AS frequency
                JOIN corpus.corpus_statistic_run AS run
                  ON run.corpus_statistic_run_id =
                     frequency.corpus_statistic_run_id
                WHERE run.corpus_statistic_run_key =
                      'statistic_run.firstbloom_a6cb002_pilot_v1.v1')
               + (SELECT abs(count(*) - 4600)
                  FROM corpus.normalized_expression_pair_measurement AS pair
                  JOIN corpus.corpus_statistic_run AS run
                    ON run.corpus_statistic_run_id =
                       pair.corpus_statistic_run_id
                  WHERE run.corpus_statistic_run_key =
                        'statistic_run.firstbloom_a6cb002_pilot_v1.v1')
               + (SELECT abs(count(*) - 80)
                  FROM corpus.acquisition_batch_diagnostic AS diagnostic
                  JOIN corpus.corpus_statistic_run AS run
                    ON run.corpus_statistic_run_id =
                       diagnostic.corpus_statistic_run_id
                  WHERE run.corpus_statistic_run_key =
                        'statistic_run.firstbloom_a6cb002_pilot_v1.v1')

        UNION ALL
        SELECT 'resolution_run_receipt_identity',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE receipt.policy_version <>
                         'round2b-exact-preferred-approved-v1'
                      OR receipt.resolution_as_of <>
                         TIMESTAMPTZ '2026-08-24 08:31:00+00'
                      OR receipt.allowed_mapping_types <>
                         '["preferred_label", "approved_variant"]'::JSONB
                      OR receipt.policy_sha256 <>
                         encode(sha256(convert_to(
                             '{
                               "allowed_mapping_types":["preferred_label","approved_variant"],
                               "concept_status":"active",
                               "expression_identity":"exact_observation_expression_id",
                               "multiple_concepts":"unresolved",
                               "normalized_phrase_allowed":false,
                               "polysemous_usage_allowed":false,
                               "resolution_as_of":"2026-08-24T08:31:00Z",
                               "retrieval_candidates_allowed":false,
                               "version":"round2b-exact-preferred-approved-v1"
                             }'::JSONB::TEXT,
                             'UTF8'
                         )), 'hex')
                      OR receipt.source_baseline_sha <>
                         'a6abb4112cff3fc436b1613c37f9b40f51e65144'
                      OR receipt.expected_occurrence_count <> 5564
                      OR receipt.resolved_occurrence_count <> 1866
                      OR receipt.unresolved_occurrence_count <> 3698
                      OR receipt.expected_normalized_identity_count <> 1713
                      OR receipt.resolved_only_normalized_identity_count <> 57
                      OR receipt.unresolved_only_normalized_identity_count <> 1656
                      OR receipt.mixed_normalized_identity_count <> 0
                      OR receipt.frozen_at IS NULL
                      OR receipt.result_inventory_sha256 IS DISTINCT FROM
                         frozen_resolution_inventory.inventory_sha256
               )
        FROM selected_resolution_run AS receipt
        CROSS JOIN frozen_resolution_inventory

        UNION ALL
        SELECT 'strict_exact_resolution_run_result', count(*)
        FROM pilot_occurrences
        LEFT JOIN eligible_summary
          ON eligible_summary.expression_id = pilot_occurrences.expression_id
        LEFT JOIN selected_resolution_results AS result
          ON result.observation_expression_id =
             pilot_occurrences.observation_expression_id
        WHERE result.resolution_status_code IS DISTINCT FROM
              CASE WHEN eligible_summary.concept_count = 1
                   THEN 'resolved' ELSE 'unresolved' END
           OR result.lexicalization_id IS DISTINCT FROM
              CASE WHEN eligible_summary.concept_count = 1
                   THEN eligible_summary.lexicalization_id END

        UNION ALL
        SELECT 'pilot_resolution_inventory',
               abs(count(*) - 5564)
               + abs(count(*) FILTER (
                   WHERE result.resolution_status_code = 'resolved'
                 ) - 1866)
               + abs(count(*) FILTER (
                   WHERE result.resolution_status_code = 'unresolved'
                 ) - 3698)
        FROM pilot_occurrences
        LEFT JOIN selected_resolution_results AS result
          ON result.observation_expression_id =
             pilot_occurrences.observation_expression_id

        UNION ALL
        SELECT 'current_resolution_matches_latest_frozen_run', count(*)
        FROM (
            SELECT
                COALESCE(
                    result.observation_expression_id,
                    current_resolution.observation_expression_id
                ) AS observation_expression_id
            FROM latest_frozen_resolution_results AS result
            FULL JOIN (
                SELECT current_resolution.*
                FROM corpus.observation_resolution AS current_resolution
                JOIN pilot_occurrences
                  ON pilot_occurrences.observation_expression_id =
                     current_resolution.observation_expression_id
            ) AS current_resolution
              ON current_resolution.observation_expression_id =
                 result.observation_expression_id
            WHERE current_resolution.resolution_status_code IS DISTINCT FROM
                  result.resolution_status_code
               OR current_resolution.lexicalization_id IS DISTINCT FROM
                  result.lexicalization_id
               OR current_resolution.resolution_note IS DISTINCT FROM
                  result.resolution_note
        ) AS materialization_difference

        UNION ALL
        SELECT 'resolution_coverage_projection',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE coverage.total_occurrence_count <> 5564
                      OR coverage.resolved_occurrence_count <> 1866
                      OR coverage.unresolved_occurrence_count <> 3698
                      OR coverage.missing_resolution_count <> 0
                      OR coverage.normalized_identity_count <> 1713
                      OR coverage.resolved_only_normalized_identity_count <> 57
                      OR coverage.unresolved_only_normalized_identity_count <> 1656
                      OR coverage.mixed_normalized_identity_count <> 0
                      OR coverage.incomplete_normalized_identity_count <> 0
               )
        FROM corpus.v_resolution_coverage AS coverage
        WHERE coverage.observation_resolution_run_key =
              'resolution_run.firstbloom_a6cb002_pilot_v1.exact_v1'

        UNION ALL
        SELECT 'winey_polysemous_usage_remains_unresolved',
               abs(count(*) - 5)
               + count(*) FILTER (
                   WHERE result.resolution_status_code <> 'unresolved'
                      OR result.lexicalization_id IS NOT NULL
               )
        FROM pilot_occurrences
        JOIN kb.lexical_expression AS expression
          ON expression.expression_id = pilot_occurrences.expression_id
        LEFT JOIN selected_resolution_results AS result
          ON result.observation_expression_id =
             pilot_occurrences.observation_expression_id
        WHERE expression.normalized_text = 'winey'

        UNION ALL
        SELECT 'retrieval_audit_set_identity',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE audit_set.inventory_sha256 <>
                         'f23fe402b542a482532149dd41de14ef04d95c34226e5d7de13ffc4cd036208b'
                      OR audit_set.code_commit_sha <>
                         'a6abb4112cff3fc436b1613c37f9b40f51e65144'
                      OR audit_set.frozen_at IS NULL
                      OR audit_set.sampling_configuration ->>
                         'case_count' <> '300'
                      OR audit_set.sampling_configuration ->>
                         'development_count' <> '75'
                      OR audit_set.sampling_configuration ->>
                         'held_out_count' <> '225'
                      OR audit_set.sampling_configuration ->>
                         'held_out_tuning_eligible' <> 'false'
                      OR audit_set.sampling_configuration ->>
                         'synthetic_padding' <> 'false'
                      OR audit_set.sampling_configuration #>>
                         '{input_hashes,audit_cases.tsv}' <>
                         '0401ae2c3759044d4b9f5ab16ea1f374e27399080fc14717e27f79d0d96f1609'
                      OR audit_set.sampling_configuration #>>
                         '{input_hashes,audit_candidate_pool.tsv}' <>
                         '00b087cabd36d1b50a258624e79e14ea10b3c135969143ca56c967e29c95cd45'
                      OR audit_set.sampling_configuration #>>
                         '{input_hashes,adjudication.tsv}' <>
                         '7e9b4ce21697ffd614cc11e89632394411d1bf1813bc331f0cc66a1b506ef6e8'
               )
        FROM selected_audit_set AS audit_set

        UNION ALL
        SELECT 'retrieval_audit_case_inventory',
               abs(count(*) - 300)
               + abs(count(*) FILTER (
                   WHERE audit_split_code = 'development'
                 ) - 75)
               + abs(count(*) FILTER (
                   WHERE audit_split_code = 'held_out'
                 ) - 225)
               + count(*) FILTER (
                   WHERE NOT EXISTS (
                       SELECT 1
                       FROM pilot_occurrences
                       WHERE pilot_occurrences.observation_expression_id =
                             selected_audit_cases.representative_observation_expression_id
                         AND pilot_occurrences.expression_id =
                             selected_audit_cases.expression_id
                   )
               )
        FROM selected_audit_cases

        UNION ALL
        SELECT 'retrieval_audit_stratum_inventory',
               abs(count(*) - 469)
               + (SELECT count(*)
                  FROM selected_audit_cases AS audit_case
                  WHERE NOT EXISTS (
                      SELECT 1
                      FROM audit.retrieval_audit_case_stratum AS stratum
                      WHERE stratum.retrieval_audit_case_id =
                            audit_case.retrieval_audit_case_id
                  ))
        FROM audit.retrieval_audit_case_stratum AS stratum
        JOIN selected_audit_cases AS audit_case
          ON audit_case.retrieval_audit_case_id =
             stratum.retrieval_audit_case_id

        UNION ALL
        SELECT 'retrieval_review_closure',
               (SELECT abs(count(*) - 900)
                       + abs(count(*) FILTER (
                           WHERE audit_review_role_code = 'independent'
                         ) - 600)
                       + abs(count(*) FILTER (
                           WHERE audit_review_role_code = 'adjudicated'
                         ) - 300)
                       + abs(count(*) FILTER (
                           WHERE audit_review_role_code = 'adjudicated'
                             AND expects_unresolved
                         ) - 19)
                FROM audit.retrieval_case_review AS review
                JOIN selected_audit_cases AS audit_case
                  ON audit_case.retrieval_audit_case_id =
                     review.retrieval_audit_case_id)
               + (SELECT count(*)
                  FROM (
                      SELECT audit_case.retrieval_audit_case_id
                      FROM selected_audit_cases AS audit_case
                      LEFT JOIN audit.retrieval_case_review AS review
                        ON review.retrieval_audit_case_id =
                           audit_case.retrieval_audit_case_id
                      GROUP BY audit_case.retrieval_audit_case_id
                      HAVING count(*) FILTER (
                          WHERE review.audit_review_role_code = 'independent'
                        ) <> 2
                          OR count(*) FILTER (
                              WHERE review.audit_review_role_code = 'adjudicated'
                          ) <> 1
                  ) AS incomplete_review)

        UNION ALL
        SELECT 'retrieval_judgment_inventory',
               abs(count(*) - 1844)
               + abs(count(*) FILTER (
                   WHERE review.audit_review_role_code = 'adjudicated'
                 ) - 646)
        FROM audit.retrieval_relevance_judgment AS judgment
        JOIN audit.retrieval_case_review AS review
          ON review.retrieval_case_review_id =
             judgment.retrieval_case_review_id
        JOIN selected_audit_cases AS audit_case
          ON audit_case.retrieval_audit_case_id =
             review.retrieval_audit_case_id

        UNION ALL
        SELECT 'retrieval_model_run_contract',
               abs(count(*) - 4)
               + abs(count(DISTINCT retrieval_baseline_code) - 4)
               + count(*) FILTER (
                   WHERE model_run_status_code <> 'completed'
                      OR completed_at IS NULL
                      OR top_k <> 5
                      OR trigram_threshold <> 0.35::REAL
                      OR run_configuration ->>
                         'weighted_composite_score' <> 'false'
                      OR run_configuration ->>
                         'code_commit_sha' <>
                         'a6abb4112cff3fc436b1613c37f9b40f51e65144'
                      OR result_metadata ->>
                         'automatic_ontology_promotion' <> 'false'
                      OR (retrieval_baseline_code = 'D') <>
                         (retrieval_graph_policy_id IS NOT NULL)
               )
        FROM selected_model_runs

        UNION ALL
        SELECT 'retrieval_model_no_embedding_or_llm',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE version.configuration ->> 'embeddings' <> 'false'
                      OR version.configuration ->> 'llm' <> 'false'
                      OR version.configuration ->>
                         'weighted_composite_score' <> 'false'
               )
        FROM ml.model_version AS version
        WHERE version.model_version_key =
              'model_version.round2b.deterministic_retrieval_v1.a6abb411'

        UNION ALL
        SELECT 'graph_policy_whitelist',
               abs(count(*) - 5)
               + count(*) FILTER (
                   WHERE (rule.relation_type_code, rule.traversal_direction)
                         NOT IN (
                             ('composite_has_component', 'OUTGOING'),
                             ('consumer_reference_for', 'OUTGOING'),
                             ('broader_than', 'INCOMING'),
                             ('broader_than', 'OUTGOING'),
                             ('sensory_neighbour', 'SYMMETRIC')
                         )
                      OR rule.maximum_hops <> 1
                      OR NOT policy.is_frozen
                      OR policy.rules_sha256 <>
                         '831811e96925ce8adddbc0f7420a7f2ce7843b28ebee5ca0a9af233f1fbbff17'
                      OR policy.configuration ->>
                         'uses_source_schemes' <> 'false'
                      OR policy.configuration ->>
                         'uses_transitive_closure' <> 'false'
                      OR policy.configuration ->>
                         'weighted_score' <> 'false'
               )
        FROM ml.retrieval_graph_policy AS policy
        JOIN ml.retrieval_graph_policy_rule AS rule
          ON rule.retrieval_graph_policy_id =
             policy.retrieval_graph_policy_id
        WHERE policy.retrieval_graph_policy_key = 'graph_policy.round2b.v1'

        UNION ALL
        SELECT 'retrieval_inference_candidate_inventory',
               abs(count(DISTINCT inference.mapping_inference_id) - 1200)
               + abs(count(DISTINCT candidate.mapping_candidate_id) - 610)
               + abs(count(DISTINCT candidate.mapping_candidate_id) FILTER (
                   WHERE selected_model_runs.retrieval_baseline_code = 'A'
                 ) - 45)
               + abs(count(DISTINCT candidate.mapping_candidate_id) FILTER (
                   WHERE selected_model_runs.retrieval_baseline_code = 'B'
                 ) - 46)
               + abs(count(DISTINCT candidate.mapping_candidate_id) FILTER (
                   WHERE selected_model_runs.retrieval_baseline_code = 'C'
                 ) - 171)
               + abs(count(DISTINCT candidate.mapping_candidate_id) FILTER (
                   WHERE selected_model_runs.retrieval_baseline_code = 'D'
                 ) - 348)
        FROM selected_model_runs
        LEFT JOIN ml.mapping_inference AS inference
          ON inference.model_run_id = selected_model_runs.model_run_id
        LEFT JOIN ml.mapping_candidate AS candidate
          ON candidate.mapping_inference_id = inference.mapping_inference_id

        UNION ALL
        SELECT 'retrieval_trace_and_signal_inventory',
               (SELECT abs(count(*) - 610)
                FROM ml.deterministic_candidate_trace AS trace
                JOIN ml.mapping_candidate AS candidate
                  ON candidate.mapping_candidate_id = trace.mapping_candidate_id
                JOIN ml.mapping_inference AS inference
                  ON inference.mapping_inference_id =
                     candidate.mapping_inference_id
                JOIN selected_model_runs
                  ON selected_model_runs.model_run_id = inference.model_run_id)
               + (SELECT abs(count(*) - 796)
                  FROM ml.deterministic_candidate_signal AS signal
                  JOIN ml.mapping_candidate AS candidate
                    ON candidate.mapping_candidate_id =
                       signal.mapping_candidate_id
                  JOIN ml.mapping_inference AS inference
                    ON inference.mapping_inference_id =
                       candidate.mapping_inference_id
                  JOIN selected_model_runs
                    ON selected_model_runs.model_run_id =
                       inference.model_run_id)

        UNION ALL
        SELECT 'retrieved_candidates_active_only', count(*)
        FROM ml.mapping_candidate AS candidate
        JOIN ml.mapping_inference AS inference
          ON inference.mapping_inference_id = candidate.mapping_inference_id
        JOIN selected_model_runs
          ON selected_model_runs.model_run_id = inference.model_run_id
        JOIN kb.concept AS concept
          ON concept.concept_id = candidate.concept_id
        WHERE concept.lifecycle_status_code <> 'active'
           OR candidate.rank > selected_model_runs.top_k

        UNION ALL
        SELECT 'typed_graph_trace_whitelist', count(*)
        FROM ml.deterministic_candidate_trace AS trace
        JOIN ml.mapping_candidate AS candidate
          ON candidate.mapping_candidate_id = trace.mapping_candidate_id
        JOIN ml.mapping_inference AS inference
          ON inference.mapping_inference_id = candidate.mapping_inference_id
        JOIN selected_model_runs
          ON selected_model_runs.model_run_id = inference.model_run_id
        LEFT JOIN kb.concept_relation AS relation
          ON relation.concept_relation_id = trace.concept_relation_id
        LEFT JOIN ml.retrieval_graph_policy_rule AS rule
          ON rule.retrieval_graph_policy_id =
             selected_model_runs.retrieval_graph_policy_id
         AND rule.relation_type_code = relation.relation_type_code
         AND rule.traversal_direction = trace.traversal_direction
        WHERE trace.retrieval_tier_code = 'D'
          AND (
              selected_model_runs.retrieval_baseline_code <> 'D'
              OR trace.graph_hop_count <> 1
              OR relation.concept_relation_id IS NULL
              OR relation.lifecycle_status_code <> 'active'
              OR relation.valid_from >
                 TIMESTAMPTZ '2026-08-24 08:31:00+00'
              OR relation.valid_until IS NOT NULL
                 AND relation.valid_until <=
                     TIMESTAMPTZ '2026-08-24 08:31:00+00'
              OR rule.retrieval_graph_policy_rule_id IS NULL
          )

        UNION ALL
        SELECT 'retrieval_evaluation_inventory',
               abs(count(*) - 8)
               + abs(count(*) FILTER (
                   WHERE evaluation.audit_split_code = 'development'
                 ) - 4)
               + abs(count(*) FILTER (
                   WHERE evaluation.audit_split_code = 'held_out'
                 ) - 4)
               + count(*) FILTER (
                   WHERE evaluation.evaluation_configuration ->>
                         'metric_policy_version' <>
                         'round2b-retrieval-metrics-v1'
               )
        FROM audit.retrieval_evaluation AS evaluation
        JOIN selected_audit_set
          ON selected_audit_set.retrieval_audit_set_id =
             evaluation.retrieval_audit_set_id

        UNION ALL
        SELECT 'retrieval_metric_inventory',
               abs(count(*) - 80)
               + (SELECT count(*)
                  FROM (
                      SELECT evaluation.retrieval_evaluation_id
                      FROM audit.retrieval_evaluation AS evaluation
                      JOIN selected_audit_set
                        ON selected_audit_set.retrieval_audit_set_id =
                           evaluation.retrieval_audit_set_id
                      LEFT JOIN audit.retrieval_metric_value AS metric
                        ON metric.retrieval_evaluation_id =
                           evaluation.retrieval_evaluation_id
                      GROUP BY evaluation.retrieval_evaluation_id
                      HAVING count(metric.retrieval_metric_value_id) <> 10
                  ) AS incomplete_metric_set)
        FROM audit.retrieval_metric_value AS metric
        JOIN audit.retrieval_evaluation AS evaluation
          ON evaluation.retrieval_evaluation_id =
             metric.retrieval_evaluation_id
        JOIN selected_audit_set
          ON selected_audit_set.retrieval_audit_set_id =
             evaluation.retrieval_audit_set_id

        UNION ALL
        SELECT 'retrieval_metric_recomputation', count(*)
        FROM (
            SELECT *
            FROM (
                SELECT
                    stored.retrieval_evaluation_id,
                    stored.retrieval_metric_code,
                    stored.cutoff_k,
                    stored.numerator,
                    stored.denominator,
                    stored.metric_value,
                    stored.value_semantics
                FROM audit.retrieval_metric_value AS stored
                JOIN audit.retrieval_evaluation AS evaluation
                  ON evaluation.retrieval_evaluation_id =
                     stored.retrieval_evaluation_id
                JOIN selected_audit_set
                  ON selected_audit_set.retrieval_audit_set_id =
                     evaluation.retrieval_audit_set_id
                EXCEPT ALL
                SELECT * FROM recomputed_metrics
            ) AS stored_only
            UNION ALL
            SELECT *
            FROM (
                SELECT * FROM recomputed_metrics
                EXCEPT ALL
                SELECT
                    stored.retrieval_evaluation_id,
                    stored.retrieval_metric_code,
                    stored.cutoff_k,
                    stored.numerator,
                    stored.denominator,
                    stored.metric_value,
                    stored.value_semantics
                FROM audit.retrieval_metric_value AS stored
                JOIN audit.retrieval_evaluation AS evaluation
                  ON evaluation.retrieval_evaluation_id =
                     stored.retrieval_evaluation_id
                JOIN selected_audit_set
                  ON selected_audit_set.retrieval_audit_set_id =
                     evaluation.retrieval_audit_set_id
            ) AS recomputed_only
        ) AS metric_difference

        UNION ALL
        SELECT 'retrieval_ablation_projection',
               abs(count(*) - 8)
               + count(*) FILTER (
                   WHERE recall_at_1 IS NULL
                      OR recall_at_3 IS NULL
                      OR recall_at_5 IS NULL
                      OR mrr IS NULL
                      OR ndcg_at_5 IS NULL
                      OR coverage IS NULL
                      OR abstention_rate IS NULL
                      OR abstention_error IS NULL
                      OR median_candidate_set_size IS NULL
                      OR unsafe_nonabstention IS NULL
               )
        FROM audit.v_retrieval_ablation AS ablation
        WHERE ablation.retrieval_audit_set_key =
              'audit_set.round2b.firstbloom_pilot_v1'

        UNION ALL
        SELECT 'heldout_baseline_d_metric_receipt',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE recall_at_1 <>
                         0.27910685805422647528::NUMERIC
                      OR recall_at_3 <>
                         0.43620414673046251994::NUMERIC
                      OR recall_at_5 <>
                         0.44098883572567783094::NUMERIC
                      OR mrr <> 0.48803827751196172249::NUMERIC
                      OR ndcg_at_5 <>
                         0.45481865642031275923::NUMERIC
                      OR coverage <>
                         0.49333333333333333333::NUMERIC
                      OR abstention_rate <>
                         0.50666666666666666667::NUMERIC
                      OR abstention_error <>
                         0.86842105263157894737::NUMERIC
                      OR median_candidate_set_size <> 0::NUMERIC
                      OR unsafe_nonabstention <> 0.0625::NUMERIC
               )
        FROM audit.v_retrieval_ablation AS ablation
        WHERE ablation.retrieval_audit_set_key =
              'audit_set.round2b.firstbloom_pilot_v1'
          AND ablation.audit_split_code = 'held_out'
          AND ablation.retrieval_baseline_code = 'D'

        UNION ALL
        SELECT 'ontology_feedback_run_receipt',
               abs(count(*) - 1)
               + count(*) FILTER (
                   WHERE run.code_commit_sha <>
                         'a6abb4112cff3fc436b1613c37f9b40f51e65144'
                      OR run.configuration_sha256 <>
                         '05360e75114668068eaa6160e8eb32ce37301afaf36818b37c02e71b439b463b'
                      OR run.result_inventory_sha256 <>
                         '2260b78550da2dfa40d0670fc7111e07cd4a2c7514894bd0781d27e38c9216ec'
                      OR run.sample_document_count <> 2474
                      OR run.sample_observation_count <> 6818
                      OR run.sample_occurrence_count <> 5564
                      OR run.frozen_at IS NULL
               )
        FROM corpus.corpus_statistic_run AS run
        WHERE run.corpus_statistic_run_key =
              'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'

        UNION ALL
        SELECT 'ontology_feedback_inventory',
               (SELECT abs(count(*) - 11)
                FROM corpus.normalized_expression_frequency AS frequency
                JOIN corpus.corpus_statistic_run AS run
                  ON run.corpus_statistic_run_id =
                     frequency.corpus_statistic_run_id
                WHERE run.corpus_statistic_run_key =
                      'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1')
               + (SELECT abs(count(*) - 11)
                         + abs(count(*) FILTER (
                             WHERE candidate.curation_status = 'OPEN'
                           ) - 10)
                         + abs(count(*) FILTER (
                             WHERE candidate.curation_status = 'DEFERRED'
                           ) - 1)
                  FROM corpus.ontology_extension_candidate AS candidate
                  JOIN corpus.corpus_statistic_run AS run
                    ON run.corpus_statistic_run_id =
                       candidate.corpus_statistic_run_id
                  WHERE run.corpus_statistic_run_key =
                        'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1')
               + (SELECT abs(count(*) - 14)
                  FROM corpus.ontology_extension_candidate_nearest_concept AS nearest
                  JOIN corpus.ontology_extension_candidate AS candidate
                    ON candidate.ontology_extension_candidate_id =
                       nearest.ontology_extension_candidate_id
                  JOIN corpus.corpus_statistic_run AS run
                    ON run.corpus_statistic_run_id =
                       candidate.corpus_statistic_run_id
                  WHERE run.corpus_statistic_run_key =
                        'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1')

        UNION ALL
        SELECT 'ontology_feedback_adjudication_qrel_closure',
               (SELECT count(*)
                FROM corpus.ontology_extension_candidate AS candidate
                JOIN corpus.corpus_statistic_run AS feedback_run
                  ON feedback_run.corpus_statistic_run_id =
                     candidate.corpus_statistic_run_id
                LEFT JOIN audit.retrieval_audit_case AS audit_case
                  ON audit_case.retrieval_audit_case_id =
                     candidate.retrieval_audit_case_id
                LEFT JOIN audit.retrieval_audit_set AS audit_set
                  ON audit_set.retrieval_audit_set_id =
                     audit_case.retrieval_audit_set_id
                LEFT JOIN corpus.lexical_expression_normalization AS normalization
                  ON normalization.expression_id = audit_case.expression_id
                 AND normalization.normalized_expression_id =
                     candidate.normalized_expression_id
                LEFT JOIN audit.retrieval_case_review AS adjudicated_review
                  ON adjudicated_review.retrieval_audit_case_id =
                     audit_case.retrieval_audit_case_id
                 AND adjudicated_review.audit_review_role_code = 'adjudicated'
                WHERE feedback_run.corpus_statistic_run_key =
                      'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
                  AND (
                      audit_set.retrieval_audit_set_key IS DISTINCT FROM
                          'audit_set.round2b.firstbloom_pilot_v1'
                      OR audit_set.frozen_at IS NULL
                      OR normalization.lexical_expression_normalization_id IS NULL
                      OR adjudicated_review.retrieval_case_review_id IS NULL
                  ))
               + (SELECT count(*)
                  FROM corpus.ontology_extension_candidate_nearest_concept AS nearest
                  JOIN corpus.ontology_extension_candidate AS candidate
                    ON candidate.ontology_extension_candidate_id =
                       nearest.ontology_extension_candidate_id
                  JOIN corpus.corpus_statistic_run AS feedback_run
                    ON feedback_run.corpus_statistic_run_id =
                       candidate.corpus_statistic_run_id
                  LEFT JOIN audit.retrieval_relevance_judgment AS judgment
                    ON judgment.retrieval_relevance_judgment_id =
                       nearest.adjudicated_relevance_judgment_id
                  LEFT JOIN audit.retrieval_case_review AS adjudicated_review
                    ON adjudicated_review.retrieval_case_review_id =
                       judgment.retrieval_case_review_id
                  WHERE feedback_run.corpus_statistic_run_key =
                        'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
                    AND (
                        judgment.concept_id IS DISTINCT FROM nearest.concept_id
                        OR adjudicated_review.retrieval_audit_case_id
                           IS DISTINCT FROM candidate.retrieval_audit_case_id
                        OR adjudicated_review.audit_review_role_code
                           IS DISTINCT FROM 'adjudicated'
                    ))

        UNION ALL
        SELECT 'ontology_feedback_frequency_and_rank_closure', count(*)
        FROM corpus.ontology_extension_candidate AS candidate
        JOIN corpus.corpus_statistic_run AS feedback_run
          ON feedback_run.corpus_statistic_run_id =
             candidate.corpus_statistic_run_id
        LEFT JOIN corpus.normalized_expression_frequency AS feedback_frequency
          ON feedback_frequency.corpus_statistic_run_id =
             candidate.corpus_statistic_run_id
         AND feedback_frequency.normalized_expression_id =
             candidate.normalized_expression_id
        LEFT JOIN corpus.corpus_statistic_run AS main_run
          ON main_run.corpus_statistic_run_key =
             'statistic_run.firstbloom_a6cb002_pilot_v1.v1'
        LEFT JOIN corpus.normalized_expression_frequency AS main_frequency
          ON main_frequency.corpus_statistic_run_id =
             main_run.corpus_statistic_run_id
         AND main_frequency.normalized_expression_id =
             candidate.normalized_expression_id
        WHERE feedback_run.corpus_statistic_run_key =
              'statistic_run.firstbloom_a6cb002_pilot_v1.ontology_feedback_v1'
          AND (
              feedback_frequency.expression_frequency IS DISTINCT FROM
                  candidate.expression_frequency
              OR feedback_frequency.publisher_prevalence_count IS DISTINCT FROM
                 candidate.publisher_diversity_count
              OR feedback_frequency.expression_frequency IS DISTINCT FROM
                 main_frequency.expression_frequency
              OR feedback_frequency.publisher_prevalence_count IS DISTINCT FROM
                 main_frequency.publisher_prevalence_count
              OR NOT EXISTS (
                  SELECT 1
                  FROM corpus.ontology_extension_candidate_nearest_concept AS nearest
                  WHERE nearest.ontology_extension_candidate_id =
                        candidate.ontology_extension_candidate_id
                  GROUP BY nearest.ontology_extension_candidate_id
                  HAVING min(nearest.candidate_rank) = 1
                     AND max(nearest.candidate_rank) = count(*)
              )
          )

        UNION ALL
        SELECT 'no_corpus_to_canonical_promotion',
               (SELECT count(*) FROM audit.promotion_event)
               + (SELECT count(*)
                  FROM kb.lexical_expression AS expression
                  WHERE expression.expression_key LIKE 'expression.observed.%'
                    AND EXISTS (
                        SELECT 1
                        FROM kb.lexicalization AS lexicalization
                        WHERE lexicalization.expression_id =
                              expression.expression_id
                    ))
               + abs((SELECT count(*) FROM kb.concept) - 130)

        UNION ALL
        SELECT 'pgvector_remains_absent', count(*)
        FROM pg_catalog.pg_extension AS extension
        WHERE extension.extname = 'vector'
    )
    SELECT
        violations.check_key,
        COALESCE(violations.violation_count, 1::BIGINT)
            AS violation_count,
        COALESCE(violations.violation_count, 1::BIGINT) = 0
            AS passed
    FROM violations
    ORDER BY violations.check_key;
$run_round2b_validation_queries$;

COMMENT ON FUNCTION audit.run_round2b_validation_queries() IS
    'Expected-zero Round 2B closure: rights, frozen corpus receipts, exact resolution, required A-D evaluation, metric recomputation, graph isolation, and governed ontology feedback.';

DO $round2b_validation_gate$
DECLARE
    failure_count BIGINT;
BEGIN
    SELECT count(*) INTO failure_count
    FROM audit.run_round2b_validation_queries() AS check_result
    WHERE check_result.passed IS NOT TRUE
       OR check_result.violation_count IS DISTINCT FROM 0;

    IF failure_count <> 0 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'round2b_validation_gate_ck',
            MESSAGE = format(
                'round2b_validation_gate_ck: %s expected-zero checks failed',
                failure_count
            );
    END IF;
END;
$round2b_validation_gate$;

COMMIT;
