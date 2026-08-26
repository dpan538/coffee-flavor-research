#!/usr/bin/env python3
"""Export and verify the deterministic Coffee Sensory Research DB v0 freeze.

The ten TSV inventories are database-derived.  FREEZE_MANIFEST.json records
their paths, row counts, and SHA-256 digests, but deliberately does not contain
its own digest.  The manifest digest is registered externally by migration 048.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT / "db" / "data" / "freeze" / "coffee-sensory-research-db-v0"
)
FREEZE_VERSION = "coffee-sensory-research-db-v0.1.0"
EXPECTED_STATE_COMMIT_SHA = "602624143fef8fa4250e5e84f07478101b0846ff"
SOURCE_SHA = "ccf5769cb5e1f165209e59beaef9fe54017265f5"
MANIFEST_NAME = "FREEZE_MANIFEST.json"


@dataclass(frozen=True)
class Inventory:
    artifact_key: str
    artifact_type: str
    filename: str
    query: str


def json_row_query(relation: str) -> str:
    return f"""
        SELECT to_jsonb(item)::TEXT AS record_json
        FROM {relation} AS item
        ORDER BY to_jsonb(item)::TEXT
    """


INVENTORIES = (
    Inventory(
        "round3i.freeze.canonical-inventory",
        "CANONICAL_INVENTORY",
        "CANONICAL_INVENTORY.tsv",
        json_row_query("kb.v_current_canonical_concept"),
    ),
    Inventory(
        "round3i.freeze.source-inventory",
        "SOURCE_INVENTORY",
        "SOURCE_INVENTORY.tsv",
        """
        SELECT record_type, record_key, record_json
        FROM (
          SELECT 'evidence_source_family'::TEXT AS record_type,
                 source_family_key AS record_key, to_jsonb(item)::TEXT record_json
          FROM evidence.source_family AS item
          UNION ALL
          SELECT 'relationship_source', source_key, to_jsonb(item)::TEXT
          FROM evidence.relationship_source AS item
          UNION ALL
          SELECT 'language_source_family', language_source_family_key,
                 to_jsonb(item)::TEXT
          FROM corpus.language_source_family AS item
          UNION ALL
          SELECT 'language_source', language_source_key, to_jsonb(item)::TEXT
          FROM corpus.language_source AS item
        ) AS inventory
        ORDER BY record_type, record_key, record_json
        """,
    ),
    Inventory(
        "round3i.freeze.raw-file-manifest",
        "RAW_FILE_MANIFEST",
        "RAW_FILE_MANIFEST.tsv",
        """
        SELECT record_type, record_key, record_json
        FROM (
          SELECT 'relationship_source_file'::TEXT AS record_type,
                 file_key AS record_key, to_jsonb(item)::TEXT AS record_json
          FROM evidence.relationship_source_file AS item
          UNION ALL
          SELECT 'external_source_file',
                 dataset_snapshot_key || ':' || source_file_path,
                 to_jsonb(item)::TEXT
          FROM evidence.external_source_file AS item
          UNION ALL
          SELECT 'context_source_file', context_source_file_key,
                 to_jsonb(item)::TEXT
          FROM context.context_source_file AS item
          UNION ALL
          SELECT 'language_source_manifest_item',
                 source.language_source_key || ':' || ordinality::TEXT,
                 jsonb_build_object(
                   'language_source_key', source.language_source_key,
                   'manifest_ordinal', ordinality,
                   'manifest_item', manifest_item
                 )::TEXT
          FROM corpus.language_source AS source
          CROSS JOIN LATERAL jsonb_array_elements(source.source_file_manifest)
               WITH ORDINALITY AS manifest(manifest_item, ordinality)
        ) AS inventory
        ORDER BY record_type, record_key, record_json
        """,
    ),
    Inventory(
        "round3i.freeze.sensory-inventory",
        "SENSORY_INVENTORY",
        "SENSORY_INVENTORY.tsv",
        """
        SELECT record_type, record_key, record_json
        FROM (
          SELECT 'current_sensory_partition'::TEXT AS record_type,
                 partition_key AS record_key, to_jsonb(item)::TEXT record_json
          FROM evidence.v_current_sensory_partition AS item
          UNION ALL
          SELECT 'sensory_concentration', source_family_key,
                 to_jsonb(item)::TEXT
          FROM audit.v_model_prebuild_sensory_concentration AS item
          UNION ALL
          SELECT 'range_evidence_summary', range_key,
                 to_jsonb(item)::TEXT
          FROM audit.model_prebuild_range_evidence_summary AS item
        ) AS inventory
        ORDER BY record_type, record_key, record_json
        """,
    ),
    Inventory(
        "round3i.freeze.context-coverage",
        "CONTEXT_COVERAGE",
        "CONTEXT_COVERAGE.tsv",
        json_row_query("context.v_current_context"),
    ),
    Inventory(
        "round3i.freeze.language-corpus",
        "LANGUAGE_CORPUS",
        "LANGUAGE_CORPUS.tsv",
        json_row_query("corpus.v_current_language_corpus"),
    ),
    Inventory(
        "round3i.freeze.relationship-evidence",
        "RELATIONSHIP_EVIDENCE",
        "RELATIONSHIP_EVIDENCE.tsv",
        json_row_query("evidence.v_current_relationship_evidence"),
    ),
    Inventory(
        "round3i.freeze.question-evidence",
        "QUESTION_EVIDENCE",
        "QUESTION_EVIDENCE.tsv",
        json_row_query("calibration.v_current_question_evidence"),
    ),
    Inventory(
        "round3i.freeze.feature-registry",
        "FEATURE_REGISTRY",
        "FEATURE_REGISTRY.tsv",
        json_row_query("evidence.v_current_model_prebuild_feature"),
    ),
    Inventory(
        "round3i.freeze.source-partition",
        "SOURCE_PARTITION",
        "SOURCE_PARTITION.tsv",
        json_row_query("evidence.v_model_prebuild_source_partitions"),
    ),
)


COVERAGE_QUERY = r"""
WITH language_total AS (
  SELECT count(*)::INTEGER AS n
  FROM (
    SELECT normalized_text AS normalized_expression
    FROM corpus.normalized_expression
    UNION
    SELECT normalized_expression
    FROM corpus.language_expression
    WHERE counts_toward_governed_total
  ) AS governed
), relationship_delta AS (
  SELECT * FROM audit.v_model_prebuild_relationship_delta
), sensory AS (
  SELECT * FROM audit.v_model_prebuild_coverage
)
SELECT jsonb_build_object(
  'canonical_concept_count',
    (SELECT count(*) FROM kb.concept),
  'active_sensory_attribute_count',
    (SELECT count(*) FROM kb.concept
     WHERE concept_type_code = 'sensory_attribute'
       AND lifecycle_status_code = 'active'),
  'current_canonical_view_row_count',
    (SELECT count(*) FROM kb.v_current_canonical_concept),
  'current_canonical_view_distinct_concept_count',
    (SELECT count(DISTINCT concept_key) FROM kb.v_current_canonical_concept),
  'coffee_sensory_source_family_count',
    sensory.coffee_sensory_source_family_count,
  'source_local_sensory_observation_row_count',
    sensory.source_local_sensory_observation_row_count,
  'source_local_sensory_sample_count',
    sensory.source_local_sensory_sample_count,
  'empirical_coverage_cell_count', sensory.empirical_coverage_cell_count,
  'contemporary_language_source_family_count',
    (SELECT count(*) FROM corpus.language_source_family
     WHERE counts_as_new_contemporary_family),
  'new_contemporary_document_count',
    (SELECT count(*) FROM corpus.language_document
     WHERE counts_as_new_contemporary_document),
  'governed_unique_expression_count', (SELECT n FROM language_total),
  'zh_hans_source_family_count',
    (SELECT count(*) FROM corpus.language_source_family
     WHERE counts_as_zh_hans_family),
  'zh_hans_sensory_expression_count',
    (SELECT count(*) FROM corpus.language_expression
     WHERE counts_as_zh_hans_sensory_expression),
  'relationship_evidence_claim_count',
    relationship_delta.relationship_evidence_claim_count,
  'source_local_supported_membership_count',
    relationship_delta.source_local_supported_membership_count,
  'cross_source_supported_membership_count',
    relationship_delta.cross_source_supported_membership_count,
  'range_with_source_local_evidence_count',
    relationship_delta.range_with_source_local_evidence_count,
  'range_with_cross_source_evidence_count',
    relationship_delta.range_with_cross_source_evidence_count,
  'question_target_with_independent_research_support_count',
    (SELECT count(*) FROM calibration.v_current_question_evidence),
  'model_prebuild_feature_count',
    (SELECT count(*) FROM evidence.model_prebuild_feature_definition),
  'source_partition_count',
    (SELECT count(*) FROM evidence.model_prebuild_source_partition),
  'approved_current_surface_count',
    (SELECT count(*) FROM audit.research_database_current_surface
     WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
       AND lifecycle_status = 'CURRENT_APPROVED'
       AND approved_for_future_prebuild),
  'deprecated_research_surface_count',
    (SELECT count(*) FROM audit.research_database_current_surface
     WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'
       AND lifecycle_status = 'DEPRECATED_RESEARCH'),
  'release_member_count',
    (SELECT count(*) FROM audit.research_database_release_member
     WHERE freeze_version = 'coffee-sensory-research-db-v0.1.0'),
  'evidence_source_family_count',
    (SELECT count(*) FROM evidence.source_family),
  'relationship_source_count',
    (SELECT count(*) FROM evidence.relationship_source),
  'language_source_family_count',
    (SELECT count(*) FROM corpus.language_source_family),
  'independent_language_source_family_count',
    (SELECT count(*) FROM corpus.language_source_family
     WHERE counts_as_independent),
  'language_source_count',
    (SELECT count(*) FROM corpus.language_source)
)::TEXT
FROM sensory, relationship_delta
"""


GOVERNANCE_QUERY = r"""
SELECT jsonb_build_object(
  'rights_states', jsonb_build_object(
    'language_source_count', (SELECT count(*) FROM corpus.language_source),
    'language_rights_review_complete_count',
      (SELECT count(*) FROM corpus.language_source WHERE rights_review_complete),
    'source_rights_raw_redistribution_allow_count',
      (SELECT count(*) FROM corpus.language_source
       WHERE raw_text_public_redistribution = 'ALLOW'),
    'source_rights_raw_redistribution_deny_count',
      (SELECT count(*) FROM corpus.language_source
       WHERE raw_text_public_redistribution = 'DENY'),
    'source_rights_derived_expression_release_allow_count',
      (SELECT count(*) FROM corpus.language_source
       WHERE derived_expression_public_release = 'ALLOW'),
    'language_document_public_export_state_counts',
      (SELECT jsonb_object_agg(public_export_state, document_count)
       FROM (
         SELECT public_export_state, count(*) AS document_count
         FROM corpus.language_document
         GROUP BY public_export_state
       ) AS document_states),
    'relationship_rights_cleared_count',
      (SELECT count(*) FROM evidence.relationship_source
       WHERE rights_review_status = 'CLEARED'),
    'relationship_source_count',
      (SELECT count(*) FROM evidence.relationship_source)
  ),
  'privacy_states', jsonb_build_object(
    'language_privacy_review_complete_count',
      (SELECT count(*) FROM corpus.language_source WHERE privacy_review_complete),
    'language_source_count', (SELECT count(*) FROM corpus.language_source),
    'relationship_privacy_reviewed_count',
      (SELECT count(*) FROM evidence.relationship_source
       WHERE privacy_review_status = 'REVIEWED'),
    'relationship_source_count',
      (SELECT count(*) FROM evidence.relationship_source),
    'public_participant_identifier_file_count',
      (SELECT count(*) FROM evidence.relationship_source_file
       WHERE contains_participant_identifiers
         AND public_export_decision <> 'EXTERNAL_ONLY')
  )
)::TEXT
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_psql(database: str, sql: str, *, tuples_only: bool = False) -> bytes:
    command = [
        "psql",
        "-X",
        "--quiet",
        "--set=ON_ERROR_STOP=1",
        f"--dbname={database}",
    ]
    if tuples_only:
        command.extend(("--tuples-only", "--no-align"))
    environment = os.environ.copy()
    environment["PGCLIENTENCODING"] = "UTF8"
    result = subprocess.run(
        command,
        input=sql.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=environment,
    )
    if result.returncode:
        raise SystemExit(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def export_query(database: str, query: str, output_path: Path) -> int:
    copy_sql = (
        "SET enable_nestloop = off;\nSET jit = off;\nCOPY (\n"
        + query.strip()
        + "\n) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, DELIMITER E'\\t', "
        + "ENCODING 'UTF8');\n"
    )
    output_path.write_bytes(run_psql(database, copy_sql))
    with output_path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter="\t"))


def registered_hashes(database: str) -> dict[str, str]:
    sql = f"""
    SELECT artifact_path || E'\\t' || sha256
    FROM audit.research_database_artifact_hash
    WHERE freeze_version = '{FREEZE_VERSION}'
    ORDER BY artifact_path;
    """
    output = run_psql(database, sql, tuples_only=True).decode("utf-8")
    result: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        artifact_path, digest = line.split("\t", 1)
        result[artifact_path] = digest
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-database-registration-check",
        action="store_true",
        help="Bootstrap only: export before migration 048 has final digests.",
    )
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory_items: list[dict[str, object]] = []
    for inventory in INVENTORIES:
        output_path = output_dir / inventory.filename
        row_count = export_query(args.database, inventory.query, output_path)
        inventory_items.append(
            {
                "artifact_key": inventory.artifact_key,
                "artifact_type": inventory.artifact_type,
                "path": (
                    "db/data/freeze/coffee-sensory-research-db-v0/"
                    + inventory.filename
                ),
                "row_count": row_count,
                "sha256": sha256(output_path),
            }
        )

    coverage_text = run_psql(
        args.database, COVERAGE_QUERY, tuples_only=True
    ).decode("utf-8").strip()
    coverage = json.loads(coverage_text)
    governance_text = run_psql(
        args.database, GOVERNANCE_QUERY, tuples_only=True
    ).decode("utf-8").strip()
    governance = json.loads(governance_text)
    inventory_index = {
        str(item["artifact_type"]): {
            "path": item["path"],
            "row_count": item["row_count"],
            "sha256": item["sha256"],
        }
        for item in inventory_items
    }
    manifest = {
        "format_version": "1.0",
        "freeze_version": FREEZE_VERSION,
        "release_tag": FREEZE_VERSION,
        "expected_state_commit_sha": EXPECTED_STATE_COMMIT_SHA,
        "implementation_expected_state_checkpoint_sha": EXPECTED_STATE_COMMIT_SHA,
        "repository_sha": SOURCE_SHA,
        "repository_sha_role": "VERIFIED_STARTING_SOURCE_SHA",
        "final_repository_sha_binding": (
            "POST_COMMIT_ATTESTATION_REQUIRED_NON_SELF_REFERENTIAL"
        ),
        "migration_count": 49,
        "database_engine": "PostgreSQL 17",
        "inventory_hashes": inventory_items,
        "inventory_index": inventory_index,
        "canonical_inventory": inventory_index["CANONICAL_INVENTORY"],
        "source_inventory": inventory_index["SOURCE_INVENTORY"],
        "source_family_inventory": {
            "evidence_source_family_count": coverage[
                "evidence_source_family_count"
            ],
            "language_source_family_count": coverage[
                "language_source_family_count"
            ],
            "independent_language_source_family_count": coverage[
                "independent_language_source_family_count"
            ],
        },
        "file_inventory": inventory_index["RAW_FILE_MANIFEST"],
        "file_hashes": {
            item["path"]: item["sha256"] for item in inventory_items
        },
        "row_inventories": {
            item["artifact_type"]: item["row_count"] for item in inventory_items
        },
        "sensory_inventory": inventory_index["SENSORY_INVENTORY"],
        "context_inventory": inventory_index["CONTEXT_COVERAGE"],
        "language_inventory": inventory_index["LANGUAGE_CORPUS"],
        "relationship_inventory": inventory_index["RELATIONSHIP_EVIDENCE"],
        "question_inventory": inventory_index["QUESTION_EVIDENCE"],
        "feature_definitions": inventory_index["FEATURE_REGISTRY"],
        "source_partitions": inventory_index["SOURCE_PARTITION"],
        "current_approved_views": [
            "calibration.v_current_question_evidence",
            "context.v_current_context",
            "corpus.v_current_language_corpus",
            "evidence.v_current_model_prebuild_feature",
            "evidence.v_current_relationship_evidence",
            "evidence.v_current_sensory_partition",
            "kb.v_current_canonical_concept",
            "kb.v_current_lexical_evidence",
        ],
        "deprecated_research_views": [
            "audit.v_model_prebuild_context_coverage",
            "audit.v_model_prebuild_relationship_delta",
            "calibration.v_model_prebuild_question_evidence",
            "corpus.v_model_prebuild_language_inventory",
            "evidence.v_model_prebuild_feature_availability",
            "evidence.v_model_prebuild_source_partitions",
            "kb.v_current_canonical_ontology",
            "kb.v_lexical_resolution",
        ],
        "rights_states": governance["rights_states"],
        "privacy_states": governance["privacy_states"],
        "coverage_inventory": coverage,
        "research_database_freeze_state": "READY_TO_FREEZE",
        "model_prebuild_data_ready": True,
        "contains_model_weights": False,
        "contains_embeddings": False,
        "training_or_evaluation_executed": False,
        "known_gaps": [
            "Contemporary tasting-language families: 3 observed, 5 preferred.",
            "Governed unique normalized expressions: 2996 observed, 3500 preferred.",
            "Simplified-Chinese source families: 2 observed, 3 preferred.",
            "Milk-mode sensory outcome coverage remains a preferred future gap.",
        ],
        "known_exclusions": [
            "No model weights, embeddings, or model training/evaluation outputs.",
            "No real-human study, question validation, or information-gain estimate.",
            "No frontend or canonical ontology change.",
            "No machine translation or artificial lexical variants count toward gates.",
            "Rights-blocked raw text is excluded from public inventories.",
        ],
        "manifest_hash_semantics": (
            "SHA-256 of exact UTF-8 bytes. This manifest lists the ten "
            "inventory digests and intentionally excludes its own digest."
        ),
    }
    manifest_path = output_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not args.skip_database_registration_check:
        registered = registered_hashes(args.database)
        expected = {
            str(item["path"]): str(item["sha256"]) for item in inventory_items
        }
        manifest_relative = (
            "db/data/freeze/coffee-sensory-research-db-v0/" + MANIFEST_NAME
        )
        expected[manifest_relative] = sha256(manifest_path)
        if registered != expected:
            missing = sorted(set(expected) - set(registered))
            extra = sorted(set(registered) - set(expected))
            mismatched = sorted(
                key
                for key in set(expected) & set(registered)
                if expected[key] != registered[key]
            )
            raise SystemExit(
                "Round 3I registered artifact hashes differ from export: "
                f"missing={missing}, extra={extra}, mismatched={mismatched}"
            )

    print("ROUND3I_FREEZE_INVENTORY_COUNT=10")
    print(f"ROUND3I_FREEZE_MANIFEST_SHA256={sha256(manifest_path)}")
    print("ROUND3I_FREEZE_EXPORT_PASS=true")


if __name__ == "__main__":
    main()
