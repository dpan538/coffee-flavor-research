\set ON_ERROR_STOP on
\pset pager off

-- Focused Round 3K core failure paths.  All fixtures are transaction-local;
-- evidence, rights, and professional sensory rows belong to later migrations.

BEGIN;

CREATE FUNCTION pg_temp.expect_round3k_core_failure(
    test_key TEXT,
    statement_text TEXT,
    expected_state TEXT,
    expected_constraint TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $expect_round3k_core_failure$
DECLARE
    actual_state TEXT;
    actual_constraint TEXT;
BEGIN
    BEGIN
        EXECUTE statement_text;
        RAISE EXCEPTION
            'Round 3K core negative statement unexpectedly succeeded: %',
            test_key;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS
            actual_state = RETURNED_SQLSTATE,
            actual_constraint = CONSTRAINT_NAME;
        IF actual_state <> expected_state
           OR actual_constraint IS DISTINCT FROM expected_constraint THEN
            RAISE;
        END IF;
        RAISE NOTICE
            'ROUND3K_CORE_NEGATIVE=% SQLSTATE=% CONSTRAINT=% PASS',
            test_key, actual_state, actual_constraint;
    END;
END;
$expect_round3k_core_failure$;

INSERT INTO competition.series (
    series_key, official_name, organizer_name, series_scope_code,
    lifecycle_status_code
) VALUES (
    'negative.round3k.series', 'Round 3K negative series',
    'Round 3K fixture organizer', 'GLOBAL', 'active'
);

INSERT INTO competition.edition (
    edition_key, series_id, series_local_edition_key, edition_name,
    edition_year, lifecycle_status_code
)
SELECT
    'negative.round3k.edition.2026', series_id, '2026',
    'Round 3K negative edition 2026', 2026, 'active'
FROM competition.series
WHERE series_key = 'negative.round3k.series';

INSERT INTO competition.rule_version (
    rule_version_key, series_id, rule_family_key, version_number,
    publication_status_code, official_version_label, official_locator,
    lifecycle_status_code
)
SELECT
    'negative.round3k.rules.v1', series_id, 'negative.round3k.rules', 1,
    'VERSIONED', 'Fixture rules v1', 'db/tests/round3k_core_negative.sql',
    'active'
FROM competition.series
WHERE series_key = 'negative.round3k.series';

INSERT INTO competition.scoresheet_version (
    scoresheet_version_key, series_id, rule_version_id,
    scoresheet_family_key, version_number, publication_status_code,
    official_version_label, official_locator, lifecycle_status_code
)
SELECT
    'negative.round3k.scoresheet.v1', series.series_id,
    rule_version.rule_version_id, 'negative.round3k.scoresheet', 1,
    'VERSIONED', 'Fixture scoresheet v1',
    'db/tests/round3k_core_negative.sql', 'active'
FROM competition.series AS series
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = series.series_id
WHERE series.series_key = 'negative.round3k.series'
  AND rule_version.rule_version_key = 'negative.round3k.rules.v1';

INSERT INTO competition.category (
    category_key, category_identity_key, identity_version, series_id,
    edition_id, rule_version_id, source_category_code, category_name,
    category_kind_code, lifecycle_status_code
)
SELECT
    'negative.round3k.category.filter.v1',
    'negative.round3k.category.filter', 1, series.series_id,
    edition.edition_id, rule_version.rule_version_id, 'FILTER',
    'Fixture filter category', 'SERVICE_CLASS', 'active'
FROM competition.series AS series
JOIN competition.edition AS edition ON edition.series_id = series.series_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = series.series_id
WHERE series.series_key = 'negative.round3k.series'
  AND edition.edition_key = 'negative.round3k.edition.2026'
  AND rule_version.rule_version_key = 'negative.round3k.rules.v1';

INSERT INTO competition.round (
    round_key, round_identity_key, identity_version, series_id, edition_id,
    rule_version_id, source_round_code, round_name, round_kind_code,
    sequence_number, lifecycle_status_code
)
SELECT
    round_seed.round_key, round_seed.round_identity_key, 1,
    series.series_id, edition.edition_id, rule_version.rule_version_id,
    round_seed.source_round_code, round_seed.round_name,
    round_seed.round_kind_code, round_seed.sequence_number, 'active'
FROM (VALUES
    (
        'negative.round3k.round.semifinal.v1',
        'negative.round3k.round.semifinal', 'SEMIFINAL',
        'Fixture semifinal', 'SEMIFINAL', 1
    ),
    (
        'negative.round3k.round.final.v1',
        'negative.round3k.round.final', 'FINAL',
        'Fixture final', 'FINAL', 2
    )
) AS round_seed(
    round_key, round_identity_key, source_round_code, round_name,
    round_kind_code, sequence_number
)
CROSS JOIN competition.series AS series
JOIN competition.edition AS edition ON edition.series_id = series.series_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = series.series_id
WHERE series.series_key = 'negative.round3k.series'
  AND edition.edition_key = 'negative.round3k.edition.2026'
  AND rule_version.rule_version_key = 'negative.round3k.rules.v1';

INSERT INTO competition.entry (
    entry_key, entry_identity_key, identity_version, series_id, edition_id,
    category_id, source_entry_identifier, entry_kind_code,
    lifecycle_status_code
)
SELECT
    'negative.round3k.entry.v1', 'negative.round3k.entry', 1,
    category.series_id, category.edition_id, category.category_id,
    'ENTRY-1', 'COMPETITOR_ENTRY', 'active'
FROM competition.category AS category
WHERE category.category_key = 'negative.round3k.category.filter.v1';

INSERT INTO competition.coffee_identity (
    coffee_identity_key, coffee_identity_group_key, identity_version,
    identity_kind_code, source_native_coffee_identifier,
    lifecycle_status_code
) VALUES (
    'negative.round3k.coffee.v1', 'negative.round3k.coffee', 1,
    'SOURCE_DECLARED', 'COFFEE-1', 'active'
);

INSERT INTO competition.lot (
    lot_key, lot_identity_key, identity_version, series_id, edition_id,
    category_id, coffee_identity_id, source_lot_identifier, lot_kind_code,
    lifecycle_status_code
)
SELECT
    'negative.round3k.lot.v1', 'negative.round3k.lot', 1,
    category.series_id, category.edition_id, category.category_id,
    coffee.coffee_identity_id, 'LOT-1', 'COMPETITION_LOT', 'active'
FROM competition.category AS category
CROSS JOIN competition.coffee_identity AS coffee
WHERE category.category_key = 'negative.round3k.category.filter.v1'
  AND coffee.coffee_identity_key = 'negative.round3k.coffee.v1';

INSERT INTO competition.entry_coffee_link (
    entry_coffee_link_key, series_id, edition_id, category_id, entry_id,
    coffee_identity_id, lot_id, link_role_code, linkage_status_code
)
SELECT
    'negative.round3k.entry_coffee.primary', entry.series_id,
    entry.edition_id, entry.category_id, entry.entry_id,
    lot.coffee_identity_id, lot.lot_id, 'PRIMARY', 'SOURCE_DECLARED'
FROM competition.entry AS entry
JOIN competition.lot AS lot
  ON lot.series_id = entry.series_id
 AND lot.edition_id = entry.edition_id
 AND lot.category_id = entry.category_id
WHERE entry.entry_key = 'negative.round3k.entry.v1'
  AND lot.lot_key = 'negative.round3k.lot.v1';

INSERT INTO competition.roast_batch (
    roast_batch_key, roast_batch_identity_key, identity_version,
    coffee_identity_id, lot_id, source_roast_batch_identifier,
    roast_batch_kind_code, source_native_roast_status_code,
    c1_mapping_status_code, lifecycle_status_code
)
SELECT
    'negative.round3k.roast_batch.v1', 'negative.round3k.roast_batch', 1,
    lot.coffee_identity_id, lot.lot_id, 'ROAST-1', 'COMPETITION_ROAST',
    'NOT_REPORTED', 'NOT_REPORTED', 'active'
FROM competition.lot AS lot
WHERE lot.lot_key = 'negative.round3k.lot.v1';

INSERT INTO competition.preparation_service (
    preparation_service_key, series_id, edition_id, category_id, round_id,
    entry_id, entry_service_key, rule_version_id, scoresheet_status_code,
    scoresheet_version_id, fresh_preparation_confirmed,
    fresh_preparation_status_code, preparation_taxonomy_code,
    milk_auxiliary, black_coffee_core_candidate, c0_source_status_code,
    c0_preparation_concept_id, c0_assignment_basis_code,
    source_native_roast_status_code, c1_mapping_status_code,
    lifecycle_status_code
)
SELECT
    'negative.round3k.service.filter.semifinal', entry.series_id,
    entry.edition_id, entry.category_id, round_record.round_id,
    entry.entry_id, 'negative.round3k.entry.filter_service',
    rule_version.rule_version_id, 'VERSIONED',
    scoresheet.scoresheet_version_id, TRUE, 'CONFIRMED_FRESH', 'FILTER',
    FALSE, TRUE, 'REPORTED', preparation.preparation_concept_id,
    'OFFICIAL_PROTOCOL', 'NOT_REPORTED', 'NOT_REPORTED', 'active'
FROM competition.entry AS entry
JOIN competition.round AS round_record
  ON round_record.series_id = entry.series_id
 AND round_record.edition_id = entry.edition_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = entry.series_id
JOIN competition.scoresheet_version AS scoresheet
  ON scoresheet.rule_version_id = rule_version.rule_version_id
CROSS JOIN context.preparation_concept AS preparation
WHERE entry.entry_key = 'negative.round3k.entry.v1'
  AND round_record.round_key = 'negative.round3k.round.semifinal.v1'
  AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
  AND scoresheet.scoresheet_version_key =
      'negative.round3k.scoresheet.v1'
  AND preparation.preparation_concept_key =
      'preparation.family.filter_percolation';

CREATE FUNCTION pg_temp.attempt_remove_only_entry_coffee_link()
RETURNS VOID
LANGUAGE plpgsql
AS $attempt_remove_only_entry_coffee_link$
BEGIN
    DELETE FROM competition.entry_coffee_link
    WHERE entry_coffee_link_key =
          'negative.round3k.entry_coffee.primary';
    SET CONSTRAINTS ALL IMMEDIATE;
END;
$attempt_remove_only_entry_coffee_link$;

SELECT pg_temp.expect_round3k_core_failure(
    'active_entry_service_orphaned_from_coffee',
    'SELECT pg_temp.attempt_remove_only_entry_coffee_link()',
    '23514',
    'competition_service_coffee_identity_link_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'version_lineage_skips_immediate_predecessor',
    $sql$
        INSERT INTO competition.rule_version (
            rule_version_key, series_id, rule_family_key, version_number,
            supersedes_rule_version_id, publication_status_code,
            official_version_label, official_locator,
            lifecycle_status_code
        )
        SELECT
            'negative.round3k.rules.v3', series_id,
            'negative.round3k.rules', 3, rule_version_id,
            'VERSIONED', 'Fixture rules v3',
            'db/tests/round3k_core_negative.sql', 'active'
        FROM competition.rule_version
        WHERE rule_version_key = 'negative.round3k.rules.v1'
    $sql$,
    '23514',
    'competition_identity_version_lineage_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'entry_and_lot_subject_both_set',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, lot_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.two_subjects', entry.series_id,
            entry.edition_id, entry.category_id, round_record.round_id,
            entry.entry_id, lot.lot_id, 'negative.round3k.two_subjects',
            rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FILTER', FALSE, FALSE, 'NOT_APPLICABLE',
            'NOT_REPORTED', 'NOT_REPORTED', 'active'
        FROM competition.entry AS entry
        JOIN competition.lot AS lot
          ON lot.series_id = entry.series_id
         AND lot.edition_id = entry.edition_id
         AND lot.category_id = entry.category_id
        JOIN competition.round AS round_record
          ON round_record.series_id = entry.series_id
         AND round_record.edition_id = entry.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = entry.series_id
        WHERE entry.entry_key = 'negative.round3k.entry.v1'
          AND lot.lot_key = 'negative.round3k.lot.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
    $sql$,
    '23514',
    'competition_preparation_service_subject_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'rtd_marked_fresh',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, lot_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.rtd', lot.series_id, lot.edition_id,
            lot.category_id, round_record.round_id, lot.lot_id,
            'negative.round3k.lot.rtd', rule_version.rule_version_id,
            'NOT_APPLICABLE', TRUE, 'CONFIRMED_FRESH', 'RTD', FALSE,
            FALSE, 'NOT_APPLICABLE', 'NOT_APPLICABLE',
            'NOT_APPLICABLE', 'active'
        FROM competition.lot AS lot
        JOIN competition.round AS round_record
          ON round_record.series_id = lot.series_id
         AND round_record.edition_id = lot.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = lot.series_id
        WHERE lot.lot_key = 'negative.round3k.lot.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
    $sql$,
    '23514',
    'competition_preparation_service_taxonomy_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'milk_service_marked_black_core',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, lot_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.milk_core', lot.series_id,
            lot.edition_id, lot.category_id, round_record.round_id,
            lot.lot_id, 'negative.round3k.lot.milk',
            rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FRESH_MILK_ESPRESSO', TRUE, TRUE,
            'NOT_APPLICABLE', 'NOT_REPORTED', 'NOT_REPORTED', 'active'
        FROM competition.lot AS lot
        JOIN competition.round AS round_record
          ON round_record.series_id = lot.series_id
         AND round_record.edition_id = lot.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = lot.series_id
        WHERE lot.lot_key = 'negative.round3k.lot.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
    $sql$,
    '23514',
    'competition_preparation_service_core_candidate_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'filter_category_inferred_as_light_roast',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, lot_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, reviewed_c1_roast_category_id,
            c1_mapping_basis_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.filter_implies_light', lot.series_id,
            lot.edition_id, lot.category_id, round_record.round_id,
            lot.lot_id, 'negative.round3k.lot.filter_inference',
            rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'NOT_APPLICABLE',
            'NOT_REPORTED', 'REVIEWED', roast_category.roast_category_id,
            'GOVERNED_REVIEW', 'active'
        FROM competition.lot AS lot
        JOIN competition.round AS round_record
          ON round_record.series_id = lot.series_id
         AND round_record.edition_id = lot.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = lot.series_id
        CROSS JOIN context.roast_category AS roast_category
        WHERE lot.lot_key = 'negative.round3k.lot.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
          AND roast_category.roast_category_key = 'roast.project_v1.light'
    $sql$,
    '23514',
    'competition_preparation_service_c1_status_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'superseded_five_level_c1_target',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, lot_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            source_native_roast_value, source_native_roast_scheme,
            c1_mapping_status_code, reviewed_c1_roast_category_id,
            c1_mapping_basis_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.old_c1', lot.series_id,
            lot.edition_id, lot.category_id, round_record.round_id,
            lot.lot_id, 'negative.round3k.lot.old_c1',
            rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'NOT_APPLICABLE',
            'REPORTED', 'light', 'source-native label', 'REVIEWED',
            roast_category.roast_category_id, 'GOVERNED_REVIEW', 'active'
        FROM competition.lot AS lot
        JOIN competition.round AS round_record
          ON round_record.series_id = lot.series_id
         AND round_record.edition_id = lot.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = lot.series_id
        CROSS JOIN context.roast_category AS roast_category
        WHERE lot.lot_key = 'negative.round3k.lot.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
          AND roast_category.roast_category_key = 'roast.project.light'
    $sql$,
    '23514',
    'competition_current_c1_target_ck'
);

SELECT pg_temp.expect_round3k_core_failure(
    'unlinked_repeated_round_service',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, entry_id, entry_service_key, rule_version_id,
            scoresheet_status_code, fresh_preparation_confirmed,
            fresh_preparation_status_code, preparation_taxonomy_code,
            milk_auxiliary, black_coffee_core_candidate,
            c0_source_status_code, source_native_roast_status_code,
            c1_mapping_status_code, lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.filter.final_unlinked',
            entry.series_id, entry.edition_id, entry.category_id,
            round_record.round_id, entry.entry_id,
            'negative.round3k.entry.filter_service',
            rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
            'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'NOT_APPLICABLE',
            'NOT_REPORTED', 'NOT_REPORTED', 'active'
        FROM competition.entry AS entry
        JOIN competition.round AS round_record
          ON round_record.series_id = entry.series_id
         AND round_record.edition_id = entry.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = entry.series_id
        WHERE entry.entry_key = 'negative.round3k.entry.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
    $sql$,
    '23514',
    'competition_preparation_service_repeat_link_ck'
);

-- A legitimate later-round observation is a second effective record but keeps
-- the same entry-service identity and an explicit predecessor link.
INSERT INTO competition.preparation_service (
    preparation_service_key, series_id, edition_id, category_id, round_id,
    entry_id, entry_service_key, repeat_of_preparation_service_id,
    repeat_relationship_code, rule_version_id, scoresheet_status_code,
    fresh_preparation_confirmed, fresh_preparation_status_code,
    preparation_taxonomy_code, milk_auxiliary,
    black_coffee_core_candidate, c0_source_status_code,
    c0_preparation_concept_id, c0_assignment_basis_code,
    source_native_roast_status_code, c1_mapping_status_code,
    lifecycle_status_code
)
SELECT
    'negative.round3k.service.filter.final_linked', entry.series_id,
    entry.edition_id, entry.category_id, final_round.round_id,
    entry.entry_id, earlier_service.entry_service_key,
    earlier_service.preparation_service_id, 'LATER_ROUND',
    rule_version.rule_version_id, 'NOT_APPLICABLE', TRUE,
    'CONFIRMED_FRESH', 'FILTER', FALSE, TRUE, 'REPORTED',
    preparation.preparation_concept_id, 'OFFICIAL_PROTOCOL',
    'NOT_REPORTED', 'NOT_REPORTED', 'active'
FROM competition.entry AS entry
JOIN competition.round AS final_round
  ON final_round.series_id = entry.series_id
 AND final_round.edition_id = entry.edition_id
JOIN competition.rule_version AS rule_version
  ON rule_version.series_id = entry.series_id
JOIN competition.preparation_service AS earlier_service
  ON earlier_service.entry_id = entry.entry_id
CROSS JOIN context.preparation_concept AS preparation
WHERE entry.entry_key = 'negative.round3k.entry.v1'
  AND final_round.round_key = 'negative.round3k.round.final.v1'
  AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
  AND earlier_service.preparation_service_key =
      'negative.round3k.service.filter.semifinal'
  AND preparation.preparation_concept_key =
      'preparation.family.filter_percolation';

SELECT pg_temp.expect_round3k_core_failure(
    'linked_roast_batch_context_changed_on_service',
    $sql$
        INSERT INTO competition.preparation_service (
            preparation_service_key, series_id, edition_id, category_id,
            round_id, lot_id, entry_service_key, rule_version_id,
            scoresheet_status_code, roast_batch_id,
            fresh_preparation_confirmed, fresh_preparation_status_code,
            preparation_taxonomy_code, milk_auxiliary,
            black_coffee_core_candidate, c0_source_status_code,
            source_native_roast_status_code, c1_mapping_status_code,
            lifecycle_status_code
        )
        SELECT
            'negative.round3k.service.roast_context_changed', lot.series_id,
            lot.edition_id, lot.category_id, round_record.round_id,
            lot.lot_id, 'negative.round3k.lot.roast_context_changed',
            rule_version.rule_version_id, 'NOT_APPLICABLE',
            roast_batch.roast_batch_id, TRUE, 'CONFIRMED_FRESH',
            'PRODUCTION_ROAST_CUPPING', FALSE, TRUE, 'NOT_APPLICABLE',
            'SOURCE_UNKNOWN', 'SOURCE_UNKNOWN', 'active'
        FROM competition.lot AS lot
        JOIN competition.round AS round_record
          ON round_record.series_id = lot.series_id
         AND round_record.edition_id = lot.edition_id
        JOIN competition.rule_version AS rule_version
          ON rule_version.series_id = lot.series_id
        JOIN competition.roast_batch AS roast_batch
          ON roast_batch.lot_id = lot.lot_id
        WHERE lot.lot_key = 'negative.round3k.lot.v1'
          AND round_record.round_key = 'negative.round3k.round.final.v1'
          AND rule_version.rule_version_key = 'negative.round3k.rules.v1'
    $sql$,
    '23514',
    'competition_service_roast_batch_context_ck'
);

ROLLBACK;

\echo ROUND3K_CORE_NEGATIVE_PASS=true
