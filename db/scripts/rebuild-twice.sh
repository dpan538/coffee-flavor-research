#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
DB_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
MIGRATION_PLAN="$SCRIPT_DIR/migration-plan.sh"

ALLOW_DROP=${COFFEE_KB_ALLOW_DATABASE_DROP:-}
ADMIN_DATABASE=${PGDATABASE:-postgres}
DATABASE_ONE=${COFFEE_KB_REBUILD_DB_ONE:-coffee_sensory_kb_v0_rebuild_one}
DATABASE_TWO=${COFFEE_KB_REBUILD_DB_TWO:-coffee_sensory_kb_v0_rebuild_two}

if [[ "$ALLOW_DROP" != 1 ]]; then
  printf 'ERROR: this script creates and drops databases. Set COFFEE_KB_ALLOW_DATABASE_DROP=1 to continue.\n' >&2
  exit 77
fi

validate_disposable_database_name() {
  local database_name=$1

  if [[ ! "$database_name" =~ ^coffee_sensory_kb_v0_[a-z0-9_]+$ ]]; then
    printf 'ERROR: unsafe disposable database name: %s\n' "$database_name" >&2
    printf 'Names must match ^coffee_sensory_kb_v0_[a-z0-9_]+$.\n' >&2
    exit 64
  fi

  if (( ${#database_name} > 63 )); then
    printf 'ERROR: database name exceeds PostgreSQL\047s 63-byte identifier limit: %s\n' "$database_name" >&2
    exit 64
  fi
}

validate_disposable_database_name "$DATABASE_ONE"
validate_disposable_database_name "$DATABASE_TWO"

if [[ "$DATABASE_ONE" == "$DATABASE_TWO" ]]; then
  printf 'ERROR: the two disposable database names must be distinct.\n' >&2
  exit 64
fi

if [[ "$DATABASE_ONE" == "$ADMIN_DATABASE" || "$DATABASE_TWO" == "$ADMIN_DATABASE" ]]; then
  printf 'ERROR: a disposable database name must not equal the admin database.\n' >&2
  exit 64
fi

required_commands=(psql createdb dropdb pg_dump find sort sed awk cmp mktemp)
for required_command in "${required_commands[@]}"; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    printf 'ERROR: required command is unavailable: %s\n' "$required_command" >&2
    exit 69
  fi
done

if [[ ! -x "$MIGRATION_PLAN" ]]; then
  printf 'ERROR: migration plan helper is missing or not executable: %s\n' \
    "$MIGRATION_PLAN" >&2
  exit 66
fi

"$MIGRATION_PLAN" verify
DISCOVERED_MIGRATION_COUNT=$("$MIGRATION_PLAN" count)

if command -v sha256sum >/dev/null 2>&1; then
  SHA256_COMMAND=sha256sum
elif command -v shasum >/dev/null 2>&1; then
  SHA256_COMMAND=shasum
else
  printf 'ERROR: sha256sum or shasum is required.\n' >&2
  exit 69
fi

sha256_file() {
  local file_path=$1

  if [[ "$SHA256_COMMAND" == sha256sum ]]; then
    sha256sum "$file_path" | awk '{print $1}'
  else
    shasum -a 256 "$file_path" | awk '{print $1}'
  fi
}

psql_admin() {
  psql -X --set=ON_ERROR_STOP=1 --dbname="$ADMIN_DATABASE" "$@"
}

psql_target() {
  local database_name=$1
  shift
  psql -X --set=ON_ERROR_STOP=1 --dbname="$database_name" "$@"
}

database_exists() {
  local database_name=$1
  local exists

  exists=$(psql_admin \
    --tuples-only \
    --no-align \
    --command="SELECT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$database_name');")
  [[ "$exists" == t ]]
}

server_version_num=$(psql_admin --tuples-only --no-align --command='SHOW server_version_num;')
server_version=$(psql_admin --tuples-only --no-align --command='SHOW server_version;')
admin_database_name=$(psql_admin --tuples-only --no-align --command='SELECT current_database();')
if [[ ! "$server_version_num" =~ ^[0-9]+$ ]] || (( server_version_num < 170000 )); then
  printf 'ERROR: PostgreSQL 17 or newer is required; admin server reports %s.\n' "$server_version" >&2
  exit 65
fi

if [[ "$DATABASE_ONE" == "$admin_database_name" || "$DATABASE_TWO" == "$admin_database_name" ]]; then
  printf 'ERROR: a disposable database name must not equal the connected admin database.\n' >&2
  exit 64
fi

if database_exists "$DATABASE_ONE"; then
  printf 'ERROR: refusing to overwrite existing database %s. Choose another disposable name.\n' "$DATABASE_ONE" >&2
  exit 73
fi
if database_exists "$DATABASE_TWO"; then
  printf 'ERROR: refusing to overwrite existing database %s. Choose another disposable name.\n' "$DATABASE_TWO" >&2
  exit 73
fi

ARTIFACT_DIR=$(mktemp -d "${TMPDIR:-/tmp}/coffee-sensory-kb-v0-rebuild.XXXXXX")
DATABASE_ONE_CREATED=false
DATABASE_TWO_CREATED=false

cleanup() {
  local original_status=$?
  local cleanup_status=0

  trap - EXIT INT TERM
  set +e

  if [[ "$DATABASE_TWO_CREATED" == true ]]; then
    dropdb --if-exists --maintenance-db="$ADMIN_DATABASE" "$DATABASE_TWO"
    if (( $? != 0 )); then
      printf 'ERROR: cleanup could not drop %s.\n' "$DATABASE_TWO" >&2
      cleanup_status=1
    fi
  fi

  if [[ "$DATABASE_ONE_CREATED" == true ]]; then
    dropdb --if-exists --maintenance-db="$ADMIN_DATABASE" "$DATABASE_ONE"
    if (( $? != 0 )); then
      printf 'ERROR: cleanup could not drop %s.\n' "$DATABASE_ONE" >&2
      cleanup_status=1
    fi
  fi

  printf 'ARTIFACT_DIR=%s\n' "$ARTIFACT_DIR"

  if (( original_status != 0 )); then
    exit "$original_status"
  fi
  exit "$cleanup_status"
}

trap cleanup EXIT
trap 'exit 130' INT TERM

write_migration_manifest() {
  local output_file=$1
  "$MIGRATION_PLAN" hashes >"$output_file"
}

write_seed_manifest() {
  local output_file=$1
  local seed_file

  : >"$output_file"
  while IFS= read -r seed_file; do
    printf '%s  %s\n' \
      "$(sha256_file "$seed_file")" \
      "$(basename -- "$seed_file")" >>"$output_file"
  done < <(
    find "$DB_DIR" \
      -maxdepth 1 \
      -type f \
      -name '[0-9][0-9][0-9]_*seed*.sql' \
      -print |
      LC_ALL=C sort
  )

  if [[ ! -s "$output_file" ]]; then
    printf 'ERROR: no deterministic seed migrations were discovered.\n' >&2
    return 1
  fi
}

write_stable_key_inventory() {
  local database_name=$1
  local output_file=$2
  local inventory_sql

  # Negative tests may consume identity sequence values even when their
  # transactions roll back. Compare only stable logical candidate values.
  inventory_sql=$(psql_target "$database_name" --tuples-only --no-align <<'SQL'
SELECT
  'SELECT * FROM (' ||
  string_agg(
    format(
      'SELECT %L::text AS table_name, %L::text AS column_name, %I::text AS key_value FROM %I.%I WHERE %I IS NOT NULL',
      c.table_schema || '.' || c.table_name,
      c.column_name,
      c.column_name,
      c.table_schema,
      c.table_name,
      c.column_name
    ),
    ' UNION ALL ' ORDER BY c.table_schema, c.table_name, c.ordinal_position
  ) ||
  ') AS stable_keys ORDER BY table_name, column_name, key_value;'
FROM information_schema.columns AS c
JOIN information_schema.tables AS t
  ON t.table_schema = c.table_schema
 AND t.table_name = c.table_name
WHERE t.table_type = 'BASE TABLE'
  AND c.table_schema IN (
    'ref', 'kb', 'evidence', 'corpus', 'context', 'calibration', 'ml', 'audit'
  )
  AND (
    c.column_name LIKE '%\_key' ESCAPE '\'
    OR c.column_name LIKE '%\_code' ESCAPE '\'
  );
SQL
)

  if [[ -z "$inventory_sql" ]]; then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="$inventory_sql" >"$output_file"
}

write_reference_row_counts() {
  local database_name=$1
  local output_file=$2
  local count_sql

  count_sql=$(psql_target "$database_name" --tuples-only --no-align <<'SQL'
SELECT
  'SELECT * FROM (' ||
  string_agg(
    format(
      'SELECT %L::text AS table_name, count(*)::bigint AS row_count FROM %I.%I',
      t.table_schema || '.' || t.table_name,
      t.table_schema,
      t.table_name
    ),
    ' UNION ALL ' ORDER BY t.table_name
  ) ||
  ') AS reference_counts ORDER BY table_name;'
FROM information_schema.tables AS t
WHERE t.table_schema = 'ref'
  AND t.table_type = 'BASE TABLE';
SQL
)

  if [[ -z "$count_sql" ]]; then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="$count_sql" >"$output_file"
}

write_source_version_inventory() {
  local database_name=$1
  local output_file=$2

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command='SELECT s.source_key, sv.source_version_key, lp.license_policy_key
               FROM evidence.source_version AS sv
               JOIN evidence.source AS s ON s.source_id = sv.source_id
               JOIN evidence.license_policy AS lp ON lp.license_policy_id = sv.license_policy_id
               ORDER BY s.source_key, sv.source_version_key, lp.license_policy_key;' >"$output_file"
}

write_validation_results() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT > 29 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 UNION ALL
                 SELECT 'round3c', check_key, violation_count, passed
                 FROM audit.run_round3c_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 25 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 UNION ALL
                 SELECT 'round3b', check_key, violation_count, passed
                 FROM audit.run_round3b_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 21 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 UNION ALL
                 SELECT 'round3a', check_key, violation_count, passed
                 FROM audit.run_round3a_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 17 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 UNION ALL
                 SELECT 'round2b', check_key, violation_count, passed
                 FROM audit.run_round2b_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  elif (( DISCOVERED_MIGRATION_COUNT > 8 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 UNION ALL
                 SELECT 'round2a', check_key, violation_count, passed
                 FROM audit.run_round2a_validation_queries()
                 ORDER BY 1, 2;" >"$output_file"
  else
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command="SELECT 'round1', check_key, violation_count, passed
                 FROM audit.run_validation_queries()
                 ORDER BY check_key;" >"$output_file"
  fi
}

write_round3a_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 21 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT
                     'coverage', metric_key, metric_value::TEXT
                   FROM context.v_context_coverage

                   UNION ALL

                   SELECT
                     'preparation', preparation_concept_key,
                     concat_ws(',', preparation_concept_type_code,
                       lifecycle_status_code, c0_top_level, c0_second_level,
                       direct_parent_count, direct_child_count,
                       support_count, external_support_count)
                   FROM context.v_preparation_taxonomy

                   UNION ALL

                   SELECT
                     'roast_category', source_roast_category_key,
                     concat_ws(',', source_roast_scheme_key,
                       COALESCE(source_ordinal_position::TEXT, 'none'),
                       COALESCE(context_mapping_certainty_code, 'unresolved'),
                       COALESCE(normalized_roast_category_key, 'unresolved'))
                   FROM context.v_roast_normalization

                   UNION ALL

                   SELECT
                     'unresolved_label', context_domain || '.' || expression_key,
                     concat_ws(',', language_tag_code, normalized_text,
                       lifecycle_status_code)
                   FROM context.v_unresolved_context_labels

                   UNION ALL

                   SELECT
                     'measurement_method', roast_measurement_method_key,
                     concat_ws(',', roast_measurement_basis_code, unit,
                       minimum_value, maximum_value, higher_value_is_lighter)
                   FROM context.roast_measurement_method
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3b_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 25 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'coverage', metric_key, metric_value::TEXT
                   FROM context.v_round3b_context_coverage

                   UNION ALL

                   SELECT 'normalization_metric', metric_key,
                          metric_value::TEXT
                   FROM context.v_held_out_normalization_metrics

                   UNION ALL

                   SELECT 'preparation_choice', preparation_concept_key,
                          concat_ws(',', ordinal_position,
                            candidate_user_label_en,
                            candidate_user_label_zh_hans)
                   FROM context.v_current_user_preparation

                   UNION ALL

                   SELECT 'roast_choice', roast_category_key,
                          concat_ws(',', ordinal_position,
                            interaction_code, scale_semantics)
                   FROM context.v_current_user_roast

                   UNION ALL

                   SELECT 'source', context_source_review_key,
                          concat_ws(',', doi, version_label, license_spdx,
                            context_acquisition_status_code,
                            COALESCE(inspected_row_count::TEXT, 'none'),
                            frozen_file_count)
                   FROM context.v_context_source_inventory

                   UNION ALL

                   SELECT 'snapshot', snapshot_key,
                          concat_ws(',', snapshot_hash,
                            normalization_version, code_commit,
                            case_count, held_out_case_count, is_frozen)
                   FROM context.context_dataset_snapshot
                   WHERE snapshot_key = 'context.snapshot.round3b_v1'
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round3c_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 29 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT 'study', study_key,
                          concat_ws(',', institutional_approval_status,
                            ethics_or_approval_gate, consent_material_ready,
                            public_release_rights_ready,
                            empirical_observation_count)
                   FROM calibration.study

                   UNION ALL

                   SELECT 'design', design_scale_code,
                          concat_ws(',', coffee_lot_count, roast_batch_count,
                            preparation_family_count, roast_category_count,
                            condition_cell_count, beverage_sample_count,
                            includes_milk_mode, calibration_power_status)
                   FROM calibration.study_design_target

                   UNION ALL

                   SELECT 'question', question_key,
                          concat_ws(',', logical_question_code,
                            language_tag_code, option_count,
                            interaction_position_code)
                   FROM calibration.v_question_bank

                   UNION ALL

                   SELECT 'observation_inventory', study_key,
                          concat_ws(',', real_beverage_sample_count,
                            real_sensory_observation_count,
                            dry_run_sensory_observation_count,
                            estimability_status)
                   FROM calibration.v_calibration_observation_inventory
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_round2b_inventory() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT <= 15 )); then
    : >"$output_file"
    return
  fi

  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --field-separator='|' \
    --command="WITH receipt(record_type, record_key, record_value) AS (
                   SELECT
                     'source_policy_decision',
                     review.corpus_source_decision_code,
                     count(*)::TEXT
                   FROM corpus.source_policy_review AS review
                   GROUP BY review.corpus_source_decision_code

                   UNION ALL

                   SELECT
                     'corpus_snapshot',
                     snapshot.corpus_snapshot_key,
                     concat_ws(',',
                       snapshot.expected_document_count,
                       snapshot.expected_observation_count,
                       snapshot.expected_normalized_expression_count,
                       snapshot.source_inventory_sha256,
                       snapshot.document_inventory_sha256,
                       snapshot.code_commit_sha,
                       snapshot.frozen_at IS NOT NULL
                     )
                   FROM corpus.corpus_snapshot AS snapshot

                   UNION ALL

                   SELECT
                     'observation_retention',
                     observation.observation_retention_code,
                     count(*)::TEXT
                   FROM corpus.raw_observation AS observation
                   JOIN corpus.captured_document AS document
                     ON document.captured_document_id = observation.captured_document_id
                   JOIN corpus.corpus AS selected_corpus
                     ON selected_corpus.corpus_id = document.corpus_id
                   WHERE selected_corpus.corpus_key = 'corpus.firstbloom_a6cb002_pilot_v1'
                   GROUP BY observation.observation_retention_code

                   UNION ALL

                   SELECT
                     'normalization_run',
                     inventory.normalization_derivation_run_key,
                     concat_ws(',',
                       inventory.input_observation_count,
                       inventory.output_occurrence_count,
                       inventory.stored_occurrence_count,
                       inventory.unique_normalized_expression_count,
                       inventory.unique_surface_expression_count,
                       inventory.input_inventory_sha256,
                       inventory.output_inventory_sha256,
                       inventory.code_commit_sha,
                       inventory.frozen_at IS NOT NULL
                     )
                   FROM corpus.v_round2b_normalization_inventory AS inventory

                   UNION ALL

                   SELECT
                     'resolution_run',
                     resolution_run.observation_resolution_run_key,
                     concat_ws(',',
                       derivation.normalization_derivation_run_key,
                       resolution_run.policy_version,
                       to_char(
                         resolution_run.resolution_as_of AT TIME ZONE 'UTC',
                         'YYYY-MM-DD HH24:MI:SS.US'
                       ) || 'Z',
                       resolution_run.expected_occurrence_count,
                       resolution_run.resolved_occurrence_count,
                       resolution_run.unresolved_occurrence_count,
                       resolution_run.expected_normalized_identity_count,
                       resolution_run.resolved_only_normalized_identity_count,
                       resolution_run.unresolved_only_normalized_identity_count,
                       resolution_run.mixed_normalized_identity_count,
                       resolution_run.policy_sha256,
                       resolution_run.result_inventory_sha256,
                       resolution_run.source_baseline_sha,
                       resolution_run.frozen_at IS NOT NULL
                     )
                   FROM corpus.observation_resolution_run AS resolution_run
                   JOIN corpus.normalization_derivation_run AS derivation
                     ON derivation.normalization_derivation_run_id =
                        resolution_run.normalization_derivation_run_id

                   UNION ALL

                   SELECT
                     'statistic_run',
                     statistic_run.corpus_statistic_run_key,
                     concat_ws(',',
                       statistic_run.sample_document_count,
                       statistic_run.sample_observation_count,
                       (SELECT count(*) FROM corpus.normalized_expression_frequency AS frequency
                        WHERE frequency.corpus_statistic_run_id = statistic_run.corpus_statistic_run_id),
                       (SELECT count(*) FROM corpus.normalized_expression_pair_measurement AS pair
                        WHERE pair.corpus_statistic_run_id = statistic_run.corpus_statistic_run_id),
                       statistic_run.configuration_sha256,
                       statistic_run.result_inventory_sha256,
                       statistic_run.frozen_at IS NOT NULL
                     )
                   FROM corpus.corpus_statistic_run AS statistic_run

                   UNION ALL

                   SELECT
                     'audit_split',
                     audit_set.retrieval_audit_set_key || '.' || audit_case.audit_split_code,
                     count(*)::TEXT
                   FROM audit.retrieval_audit_set AS audit_set
                   JOIN audit.retrieval_audit_case AS audit_case
                     ON audit_case.retrieval_audit_set_id = audit_set.retrieval_audit_set_id
                   GROUP BY audit_set.retrieval_audit_set_key, audit_case.audit_split_code

                   UNION ALL

                   SELECT
                     'audit_set',
                     audit_set.retrieval_audit_set_key,
                     concat_ws(',',
                       audit_set.version_label,
                       audit_set.inventory_sha256,
                       audit_set.code_commit_sha,
                       (SELECT count(*)
                        FROM audit.retrieval_audit_case AS audit_case
                        WHERE audit_case.retrieval_audit_set_id =
                              audit_set.retrieval_audit_set_id),
                       audit_set.frozen_at IS NOT NULL
                     )
                   FROM audit.retrieval_audit_set AS audit_set

                   UNION ALL

                   SELECT
                     'retrieval_run',
                     model_run.model_run_key,
                     concat_ws(',',
                       deterministic_run.retrieval_baseline_code,
                       model_run.model_run_status_code,
                       deterministic_run.top_k,
                       deterministic_run.trigram_threshold,
                       deterministic_run.configuration_sha256,
                       (SELECT count(*) FROM ml.mapping_inference AS inference
                        WHERE inference.model_run_id = model_run.model_run_id),
                       (SELECT count(*) FROM ml.mapping_candidate AS candidate
                        JOIN ml.mapping_inference AS inference
                          ON inference.mapping_inference_id = candidate.mapping_inference_id
                        WHERE inference.model_run_id = model_run.model_run_id)
                     )
                   FROM ml.model_run AS model_run
                   JOIN ml.deterministic_retrieval_run AS deterministic_run
                     ON deterministic_run.model_run_id = model_run.model_run_id

                   UNION ALL

                   SELECT
                     'retrieval_metric',
                     evaluation.retrieval_evaluation_key || '.' ||
                       metric.retrieval_metric_code || '.' ||
                       COALESCE(metric.cutoff_k::TEXT, 'none'),
                     concat_ws(',',
                       metric.numerator,
                       metric.denominator,
                       metric.metric_value
                     )
                   FROM audit.retrieval_metric_value AS metric
                   JOIN audit.retrieval_evaluation AS evaluation
                     ON evaluation.retrieval_evaluation_id = metric.retrieval_evaluation_id
               )
               SELECT record_type, record_key, record_value
               FROM receipt
               ORDER BY record_type, record_key, record_value;" >"$output_file"
}

write_ontology_coverage() {
  local database_name=$1
  local output_file=$2

  if (( DISCOVERED_MIGRATION_COUNT > 8 )); then
    psql_target "$database_name" \
      --tuples-only \
      --no-align \
      --field-separator='|' \
      --command='SELECT metric_key, metric_value
                 FROM kb.v_ontology_coverage
                 ORDER BY metric_key;' >"$output_file"
  else
    : >"$output_file"
  fi
}

normalize_schema_dump() {
  local database_name=$1
  local output_file=$2

  pg_dump \
    --schema-only \
    --no-owner \
    --no-privileges \
    --dbname="$database_name" |
    sed \
      -e '/^\\restrict /d' \
      -e '/^\\unrestrict /d' >"$output_file"
}

run_build() {
  local database_name=$1
  local build_label=$2
  local build_dir="$ARTIFACT_DIR/$build_label"

  mkdir -p "$build_dir"
  write_migration_manifest "$build_dir/migration-files.txt"
  write_seed_manifest "$build_dir/seed-files.txt"

  printf 'CREATE_DATABASE=%s\n' "$database_name"
  createdb \
    --maintenance-db="$ADMIN_DATABASE" \
    --template=template0 \
    --encoding=UTF8 \
    "$database_name"

  if [[ "$build_label" == build-one ]]; then
    DATABASE_ONE_CREATED=true
  else
    DATABASE_TWO_CREATED=true
  fi

  "$SCRIPT_DIR/apply.sh" "$database_name"
  "$SCRIPT_DIR/test.sh" "$database_name"

  normalize_schema_dump "$database_name" "$build_dir/schema.sql"
  write_stable_key_inventory "$database_name" "$build_dir/stable-key-inventory.txt"
  write_reference_row_counts "$database_name" "$build_dir/reference-row-counts.txt"
  write_source_version_inventory "$database_name" "$build_dir/source-version-inventory.txt"
  write_validation_results "$database_name" "$build_dir/validation-results.txt"
  write_ontology_coverage "$database_name" "$build_dir/ontology-coverage.txt"
  write_round2b_inventory "$database_name" "$build_dir/round2b-inventory.txt"
  write_round3a_inventory "$database_name" "$build_dir/round3a-inventory.txt"
  write_round3b_inventory "$database_name" "$build_dir/round3b-inventory.txt"
  write_round3c_inventory "$database_name" "$build_dir/round3c-inventory.txt"
  psql_target "$database_name" \
    --tuples-only \
    --no-align \
    --command="SELECT extversion FROM pg_extension WHERE extname = 'pg_trgm';" \
    >"$build_dir/pg-trgm-version.txt"
}

print_result_file() {
  local label=$1
  local file_path=$2

  printf '%s_BEGIN\n' "$label"
  sed 's/^/  /' "$file_path"
  printf '%s_END\n' "$label"
}

compare_artifact() {
  local label=$1
  local relative_path=$2
  local first_file="$ARTIFACT_DIR/build-one/$relative_path"
  local second_file="$ARTIFACT_DIR/build-two/$relative_path"
  local first_hash
  local second_hash

  first_hash=$(sha256_file "$first_file")
  second_hash=$(sha256_file "$second_file")
  printf '%s_BUILD_ONE_SHA256=%s\n' "$label" "$first_hash"
  printf '%s_BUILD_TWO_SHA256=%s\n' "$label" "$second_hash"

  if ! cmp -s "$first_file" "$second_file"; then
    printf 'ERROR: reproducibility mismatch for %s.\n' "$label" >&2
    if command -v diff >/dev/null 2>&1; then
      diff -u "$first_file" "$second_file" >&2 || true
    fi
    return 1
  fi
}

printf 'POSTGRES_VERSION=%s\n' "$server_version"
printf 'ADMIN_DATABASE=%s\n' "$admin_database_name"
printf 'DISPOSABLE_DATABASE_ONE=%s\n' "$DATABASE_ONE"
printf 'DISPOSABLE_DATABASE_TWO=%s\n' "$DATABASE_TWO"

run_build "$DATABASE_ONE" build-one
run_build "$DATABASE_TWO" build-two

compare_artifact MIGRATION_HASH migration-files.txt
compare_artifact SEED_FILE_HASHES seed-files.txt
compare_artifact SCHEMA_ONLY_DUMP_HASH schema.sql
compare_artifact STABLE_KEY_INVENTORY stable-key-inventory.txt
compare_artifact REFERENCE_TABLE_ROW_COUNTS reference-row-counts.txt
compare_artifact SOURCE_VERSION_INVENTORY source-version-inventory.txt
compare_artifact VALIDATION_RESULT_COUNTS validation-results.txt
compare_artifact ONTOLOGY_COVERAGE ontology-coverage.txt
compare_artifact ROUND2B_INVENTORY round2b-inventory.txt
compare_artifact ROUND3A_INVENTORY round3a-inventory.txt
compare_artifact ROUND3B_INVENTORY round3b-inventory.txt
compare_artifact ROUND3C_INVENTORY round3c-inventory.txt
compare_artifact PG_TRGM_VERSION pg-trgm-version.txt

seed_hash_one=$(sha256_file "$ARTIFACT_DIR/build-one/seed-files.txt")
seed_hash_two=$(sha256_file "$ARTIFACT_DIR/build-two/seed-files.txt")
printf 'SEED_HASH_BUILD_ONE_SHA256=%s\n' "$seed_hash_one"
printf 'SEED_HASH_BUILD_TWO_SHA256=%s\n' "$seed_hash_two"
if [[ "$seed_hash_one" != "$seed_hash_two" ]]; then
  printf 'ERROR: reproducibility mismatch for SEED_HASH.\n' >&2
  exit 1
fi

print_result_file MIGRATION_FILE_HASHES "$ARTIFACT_DIR/build-one/migration-files.txt"
print_result_file SEED_FILE_HASHES "$ARTIFACT_DIR/build-one/seed-files.txt"
print_result_file STABLE_KEY_INVENTORY "$ARTIFACT_DIR/build-one/stable-key-inventory.txt"
print_result_file REFERENCE_TABLE_ROW_COUNTS "$ARTIFACT_DIR/build-one/reference-row-counts.txt"
print_result_file SOURCE_VERSION_INVENTORY "$ARTIFACT_DIR/build-one/source-version-inventory.txt"
print_result_file VALIDATION_RESULT_COUNTS "$ARTIFACT_DIR/build-one/validation-results.txt"
print_result_file ONTOLOGY_COVERAGE "$ARTIFACT_DIR/build-one/ontology-coverage.txt"
print_result_file ROUND2B_INVENTORY "$ARTIFACT_DIR/build-one/round2b-inventory.txt"
print_result_file ROUND3A_INVENTORY "$ARTIFACT_DIR/build-one/round3a-inventory.txt"
print_result_file ROUND3B_INVENTORY "$ARTIFACT_DIR/build-one/round3b-inventory.txt"
print_result_file ROUND3C_INVENTORY "$ARTIFACT_DIR/build-one/round3c-inventory.txt"
printf 'PG_TRGM_VERSION=%s\n' "$(sed -n '1p' "$ARTIFACT_DIR/build-one/pg-trgm-version.txt")"

printf 'CLEAN_REBUILD_COUNT=2\n'
printf 'REPRODUCIBILITY_PASS=true\n'
