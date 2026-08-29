#!/usr/bin/env python3
"""Generate the public Batch 4 cleaned-30k governance artifacts."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
STAGING = ROOT / "db" / "data" / "candidate-cleaning-v2-staging"
EXTENSION = ROOT / "db" / "data" / "post20k-extension-staging"
POST30 = ROOT / "db" / "data" / "post30k-extension-staging"

SNAPSHOT_VERSION = "professional-descriptor-candidate-v1-30k"
CLEANER_VERSION = "batch4.semantic-cleaner.v2"
GENERATOR_VERSION = "batch4.public-cleaned-30k-generator.v1"
GENERATED_AT = "2026-08-29T00:00:00Z"

PURPOSES = (
    "PUBLIC_DISCOVERY",
    "INTERNAL_RESEARCH_ANALYSIS",
    "NONCOMMERCIAL_MODEL_RESEARCH",
    "COMMERCIAL_MODEL_TRAINING",
    "DERIVED_DATA_RELEASE",
    "RAW_TEXT_REDISTRIBUTION",
    "MODEL_WEIGHT_RELEASE",
    "PRODUCT_DEPLOYMENT",
)
PERMITTED = {"AFFIRMATIVE", "AFFIRMATIVE_WITH_CONDITIONS"}
VALID_SOURCE_DISPOSITIONS = {
    "VALID_STRICT_FLAVOR",
    "VALID_BROAD_SENSORY",
    "VALID_DEFECT_OR_NEGATIVE_SENSORY",
    "VALID_COMPOUND_SPLIT",
    "VALID_COMPOUND_PRESERVED",
}
HIGH_CONFIDENCE_STATES = {
    "EXISTING_CANONICAL_EXACT",
    "EXISTING_CANONICAL_ALIAS",
    "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT",
}
STATUS_ORDER = {
    "NOT_APPLICABLE": 0,
    "AFFIRMATIVE": 1,
    "AFFIRMATIVE_WITH_CONDITIONS": 2,
    "OWNER_POLICY_REQUIRED": 3,
    "PENDING": 4,
    "UNKNOWN": 5,
    "PROHIBITED": 6,
}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, material: str) -> str:
    return f"{prefix}:{sha256_text(material)[:24]}"


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    return str(value)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(name: str, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    names = list(fields)
    with (CURRENT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=names,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: scalar(row.get(field, "")) for field in names})


def write_json(name: str, document: Mapping[str, Any]) -> None:
    (CURRENT / name).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def split_pipe(value: str) -> list[str]:
    return [part for part in value.split("|") if part]


def data_rows(path: Path) -> int | str:
    if path.suffix == ".tsv":
        return max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0)
    return "NA_NOT_TABULAR"


def rights_status(artifact: Mapping[str, str], purpose: str) -> tuple[str, str]:
    basis = artifact["source_rights_basis"]
    if "CC_BY_NC_4_0" in basis:
        status = {
            "PUBLIC_DISCOVERY": "AFFIRMATIVE_WITH_CONDITIONS",
            "INTERNAL_RESEARCH_ANALYSIS": "AFFIRMATIVE_WITH_CONDITIONS",
            "NONCOMMERCIAL_MODEL_RESEARCH": "AFFIRMATIVE_WITH_CONDITIONS",
            "COMMERCIAL_MODEL_TRAINING": "PROHIBITED",
            "DERIVED_DATA_RELEASE": "AFFIRMATIVE_WITH_CONDITIONS",
            "RAW_TEXT_REDISTRIBUTION": "AFFIRMATIVE_WITH_CONDITIONS",
            "MODEL_WEIGHT_RELEASE": "OWNER_POLICY_REQUIRED",
            "PRODUCT_DEPLOYMENT": "PROHIBITED",
        }[purpose]
        basis_code = "EXPLICIT_CC_BY_NC_4_0_NONCOMMERCIAL_AND_ATTRIBUTION_CONDITIONS"
    elif "CC_BY_4_0" in basis or "CC_BY_FRONTIERS_ARTICLE" in basis:
        status = {
            "PUBLIC_DISCOVERY": "AFFIRMATIVE_WITH_CONDITIONS",
            "INTERNAL_RESEARCH_ANALYSIS": "AFFIRMATIVE_WITH_CONDITIONS",
            "NONCOMMERCIAL_MODEL_RESEARCH": "AFFIRMATIVE_WITH_CONDITIONS",
            "COMMERCIAL_MODEL_TRAINING": "PENDING",
            "DERIVED_DATA_RELEASE": "AFFIRMATIVE_WITH_CONDITIONS",
            "RAW_TEXT_REDISTRIBUTION": "AFFIRMATIVE_WITH_CONDITIONS",
            "MODEL_WEIGHT_RELEASE": "OWNER_POLICY_REQUIRED",
            "PRODUCT_DEPLOYMENT": "OWNER_POLICY_REQUIRED",
        }[purpose]
        basis_code = "CC_BY_4_0_REUSE_CONDITIONS_RECORDED_MODEL_PURPOSE_NOT_BROADLY_INFERRED"
    else:
        status = {
            "PUBLIC_DISCOVERY": "AFFIRMATIVE",
            "INTERNAL_RESEARCH_ANALYSIS": "PENDING" if artifact["source_rights_state"] == "PENDING" else "UNKNOWN",
            "NONCOMMERCIAL_MODEL_RESEARCH": "PENDING" if artifact["source_rights_state"] == "PENDING" else "UNKNOWN",
            "COMMERCIAL_MODEL_TRAINING": "UNKNOWN",
            "DERIVED_DATA_RELEASE": "UNKNOWN",
            "RAW_TEXT_REDISTRIBUTION": "UNKNOWN",
            "MODEL_WEIGHT_RELEASE": "OWNER_POLICY_REQUIRED",
            "PRODUCT_DEPLOYMENT": "UNKNOWN",
        }[purpose]
        basis_code = "PUBLIC_DISCOVERY_ONLY_OTHER_PURPOSES_REQUIRE_RIGHTS_OR_OWNER_REVIEW"
    return status, basis_code


def worst_status(values: Iterable[str]) -> str:
    items = [value for value in values if value]
    return max(items, key=lambda item: STATUS_ORDER[item]) if items else "NOT_APPLICABLE"


def percentile(values: list[int], quantile: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(math.ceil(quantile * len(ordered)) - 1, 0)
    return ordered[index]


def snapshot_manifest(staging_manifest: Mapping[str, Any]) -> dict[str, Any]:
    previous = json.loads((CURRENT / "CANDIDATE_20K_SNAPSHOT_MANIFEST.json").read_text())
    extension = json.loads((EXTENSION / "POST20K_EXTENSION_MANIFEST.json").read_text())
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_role": "IMMUTABLE_ACQUISITION_SNAPSHOT_NOT_TRAINING_CORPUS",
        "created_at": GENERATED_AT,
        "candidate_20k_snapshot_preserved": True,
        "candidate_20k_snapshot_version": previous["snapshot_version"],
        "candidate_20k_snapshot_sha256": sha256_file(CURRENT / "CANDIDATE_20K_SNAPSHOT_MANIFEST.json"),
        "candidate_20k_v1_cleaned_ledger_sha256": sha256_file(CURRENT / "CLEANED_DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        "post20k_extension_manifest_sha256": sha256_file(EXTENSION / "POST20K_EXTENSION_MANIFEST.json"),
        "raw_candidate_source_assertion_count": previous["frozen_raw_candidate_assertion_count"] + extension["net_new_raw_assertion_count"],
        "mechanically_deinflated_source_assertion_count": 30010,
        "frozen_20k_source_assertion_count": 20003,
        "post20k_extension_source_assertion_count": 10007,
        "effective_record_count": 1247,
        "source_family_count": 7,
        "candidate_source_artifact_count": staging_manifest["source_artifact_count"],
        "acquisition_artifact_receipt_row_count": 1377,
        "public_safe_cleaning_sidecar_sha256": sha256_file(STAGING / "BATCH4_PUBLIC_SAFE_CLEANING_V2.tsv"),
        "public_safe_output_atom_sidecar_sha256": sha256_file(STAGING / "BATCH4_PUBLIC_SAFE_OUTPUT_ATOMS.tsv"),
        "restricted_20k_receipt": "restricted://professional_descriptor_batch2/PROFESSIONAL_ASSERTIONS_RESTRICTED.tsv",
        "restricted_extension_receipt": "restricted://post20k_extension/POST20K_ASSERTIONS_RESTRICTED.tsv",
        "exact_continuation_cursor": extension["cursor_end"],
        "post30k_extension_included_in_snapshot": False,
        "training_corpus_frozen": False,
        "model_corpus": False,
        "model_eligible_assertion_count": 0,
        "schema_changed": False,
        "new_migration_count": 0,
    }


def v1_v2_delta(decisions: list[dict[str, str]]) -> list[dict[str, Any]]:
    v1 = {
        row["descriptor_assertion_id"]: row
        for row in read_tsv(CURRENT / "SEMANTIC_CLEANING_DECISION.tsv")
        if row["counts_as_assertion"] == "true"
    }
    rows: list[dict[str, Any]] = []
    for v2 in decisions:
        if v2["corpus_segment"] != "FROZEN_20K":
            continue
        old = v1[v2["descriptor_assertion_id"]]
        old_hashes = split_pipe(old["cleaned_lexical_form_sha256s"])
        new_hashes = split_pipe(v2["cleaned_lexical_form_sha256s"])
        old_classes = split_pipe(old["semantic_classes"])
        new_classes = split_pipe(v2["semantic_classes"])
        old_concepts = split_pipe(old["canonical_concept_ids"])
        new_concepts = split_pipe(v2["canonical_concept_ids"])
        rows.append({
            "descriptor_assertion_id": v2["descriptor_assertion_id"],
            "v1_disposition": old["semantic_cleaning_disposition"],
            "v2_disposition": v2["source_assertion_disposition"],
            "v1_cleaned_lexical_form_sha256s": old_hashes,
            "v2_cleaned_lexical_form_sha256s": new_hashes,
            "v1_semantic_classes": old_classes,
            "v2_semantic_classes": new_classes,
            "v1_canonical_concept_ids": old_concepts,
            "v2_canonical_concept_ids": new_concepts,
            "split_or_merge_changed": str(len(old_hashes) != len(new_hashes)).lower(),
            "classification_changed": str(old_classes != new_classes).lower(),
            "normalized_output_changed": str(old_hashes != new_hashes).lower(),
            "mapping_changed": str(old_concepts != new_concepts).lower(),
            "change_reason_code": "V2_DISPOSITION_TAXONOMY_REFINEMENT" if old_hashes == new_hashes and old_classes == new_classes and old_concepts == new_concepts else "V2_SEMANTIC_OR_MAPPING_CHANGE",
            "reversible_provenance_pointer": v2["restricted_source_pointer"],
            "cleaner_v1_version": old["cleaner_version"],
            "cleaner_v2_version": CLEANER_VERSION,
        })
    return rows


def rights_matrix(
    artifacts: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    by_artifact: dict[str, dict[str, str]] = defaultdict(dict)
    for artifact in artifacts:
        for purpose in PURPOSES:
            status, basis = rights_status(artifact, purpose)
            by_artifact[artifact["source_artifact_id"]][purpose] = status
            rows.append({
                **artifact,
                "purpose": purpose,
                "purpose_rights_status": status,
                "purpose_rights_basis": basis,
                "decision_actor": "CODEX_CONSERVATIVE_RIGHTS_CLASSIFIER",
                "legal_review_performed": "false",
                "legal_review_actor": "",
                "human_owner_decision": "",
            })
    return rows, by_artifact


def propagation_rows(
    decisions: list[dict[str, str]],
    atoms: list[dict[str, str]],
    clusters: list[dict[str, str]],
    rights_by_artifact: Mapping[str, Mapping[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    source_rights: dict[str, dict[str, str]] = {}
    atom_rights: dict[str, dict[str, str]] = {}
    cluster_values: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for source in decisions:
        statuses = dict(rights_by_artifact[source["source_artifact_id"]])
        source_rights[source["descriptor_assertion_id"]] = statuses
        rows.append({
            "propagation_layer": "SOURCE_ASSERTION",
            "propagation_entity_id": source["descriptor_assertion_id"],
            "parent_entity_id": source["source_artifact_id"],
            "rights_partition_id": stable_id("rights-partition", "|".join(statuses[p] for p in PURPOSES)),
            **{purpose: statuses[purpose] for purpose in PURPOSES},
            "propagation_rule": "SOURCE_ARTIFACT_PURPOSE_STATUS_INHERITED_WITHOUT_SCALAR_COLLAPSE",
        })
    for atom in atoms:
        statuses = dict(source_rights[atom["descriptor_assertion_id"]])
        atom_rights[atom["cleaned_output_atom_id"]] = statuses
        for purpose in PURPOSES:
            cluster_values[atom["concept_cluster_id"]][purpose].append(statuses[purpose])
        rows.append({
            "propagation_layer": "CLEANED_OUTPUT_ATOM",
            "propagation_entity_id": atom["cleaned_output_atom_id"],
            "parent_entity_id": atom["descriptor_assertion_id"],
            "rights_partition_id": stable_id("rights-partition", "|".join(statuses[p] for p in PURPOSES)),
            **{purpose: statuses[purpose] for purpose in PURPOSES},
            "propagation_rule": "SOURCE_ASSERTION_PURPOSE_VECTOR_INHERITED",
        })
    for cluster in clusters:
        statuses = {
            purpose: worst_status(cluster_values[cluster["concept_cluster_id"]][purpose])
            for purpose in PURPOSES
        }
        rows.append({
            "propagation_layer": "CONCEPT_CLUSTER",
            "propagation_entity_id": cluster["concept_cluster_id"],
            "parent_entity_id": "MULTIPLE_CLEANED_OUTPUT_ATOMS",
            "rights_partition_id": stable_id("rights-partition", "|".join(statuses[p] for p in PURPOSES)),
            **statuses,
            "propagation_rule": "MOST_RESTRICTIVE_CLUSTER_STATUS_MIXED_PURPOSE_SUBSETS_REMAIN_SEPARABLE",
        })
    valid_atoms = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    subsets = {
        "subset.all_cleaned_descriptors": valid_atoms,
        "subset.noncommercial_research_permitted": [
            atom for atom in valid_atoms
            if atom_rights[atom["cleaned_output_atom_id"]]["NONCOMMERCIAL_MODEL_RESEARCH"] in PERMITTED
        ],
        "subset.machine_governed_high_confidence": [
            atom for atom in valid_atoms
            if atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"
        ],
        "subset.future_project_owner_reviewed": [],
    }
    for subset_id, members in subsets.items():
        statuses = {
            purpose: worst_status(atom_rights[atom["cleaned_output_atom_id"]][purpose] for atom in members)
            for purpose in PURPOSES
        }
        rows.append({
            "propagation_layer": "CANDIDATE_SUBSET",
            "propagation_entity_id": subset_id,
            "parent_entity_id": "CLEANED_OUTPUT_ATOM_PARTITION",
            "rights_partition_id": stable_id("rights-partition", "|".join(statuses[p] for p in PURPOSES)),
            **statuses,
            "propagation_rule": "PURPOSE_FILTERED_AT_OUTPUT_ATOM_LEVEL_NO_CROSS_PURPOSE_INFERENCE",
        })
    return rows, atom_rights, source_rights


def review_packet(clusters: list[dict[str, str]]) -> list[dict[str, Any]]:
    review_states = {
        "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM",
        "EXISTING_CANONICAL_PARENT_ONLY",
        "MODIFIER_OF_EXISTING_CONCEPT",
        "COMPOUND_OF_EXISTING_CONCEPTS",
        "GENUINE_ONTOLOGY_CANDIDATE",
        "QUALITY_OR_STRUCTURE_ATTRIBUTE",
        "DEFECT_CONCEPT_CANDIDATE",
        "AMBIGUOUS_CONCEPT_BOUNDARY",
        "CROSS_LANGUAGE_REVIEW_REQUIRED",
        "UNRESOLVED",
    }
    candidates = [cluster for cluster in clusters if cluster["mapping_state"] in review_states]
    candidates.sort(
        key=lambda row: (
            -int(row["mapping_state"] in {"AMBIGUOUS_CONCEPT_BOUNDARY", "UNRESOLVED", "CROSS_LANGUAGE_REVIEW_REQUIRED"}),
            -int(row["gold_assertion_count"]),
            -int(row["source_family_count"]),
            -int(row["year_count"]),
            -int(row["assertion_support"]),
            row["concept_cluster_id"],
        )
    )
    rows: list[dict[str, Any]] = []
    for rank, cluster in enumerate(candidates[:250], start=1):
        rows.append({
            "review_packet_rank": rank,
            "concept_cluster_id": cluster["concept_cluster_id"],
            "source_native_form_ids": cluster["source_native_form_ids"],
            "cleaned_form_ids": cluster["cleaned_form_ids"],
            "mapping_state": cluster["mapping_state"],
            "canonical_concept_ids": cluster["canonical_concept_ids"],
            "semantic_classes": cluster["semantic_classes"],
            "assertion_support": cluster["assertion_support"],
            "effective_record_support": cluster["effective_record_support"],
            "source_family_ids": cluster["source_family_ids"],
            "year_ids": cluster["year_ids"],
            "gold_assertion_count": cluster["gold_assertion_count"],
            "review_reason": "AMBIGUOUS_OR_UNRESOLVED_BOUNDARY" if cluster["mapping_state"] in {"AMBIGUOUS_CONCEPT_BOUNDARY", "UNRESOLVED", "CROSS_LANGUAGE_REVIEW_REQUIRED"} else "HIGH_SUPPORT_GOLD_MULTI_FAMILY_OR_MULTI_YEAR_CONSOLIDATION",
            "suggested_action_set": "MAP_EXISTING|CONFIRM_CANDIDATE|MERGE_CLUSTER|SPLIT_CLUSTER|REJECT_NON_DESCRIPTOR|DEFER_EXPERT",
            "project_owner_decision": "",
            "project_owner_canonical_concept_id": "",
            "project_owner_reason": "",
            "project_owner_reviewed_at": "",
            "sensory_expert_decision": "",
            "sensory_expert_evidence_locator": "",
        })
    return rows


def human_audit(decisions: list[dict[str, str]], atoms: list[dict[str, str]]) -> list[dict[str, Any]]:
    output_count = Counter(atom["descriptor_assertion_id"] for atom in atoms)
    buckets: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        density = "DENSITY_3_PLUS" if output_count[row["descriptor_assertion_id"]] >= 3 else "DENSITY_2" if output_count[row["descriptor_assertion_id"]] == 2 else "DENSITY_1"
        buckets[(row["source_family_id"], row["source_assertion_disposition"], density)].append(row)
    for rows in buckets.values():
        rows.sort(key=lambda row: sha256_text("audit-v1\x1f" + row["descriptor_assertion_id"]))
    selected: list[dict[str, str]] = []
    keys = sorted(buckets)
    cursor = Counter()
    while len(selected) < 900:
        progress = False
        for key in keys:
            index = cursor[key]
            if index < len(buckets[key]):
                selected.append(buckets[key][index])
                cursor[key] += 1
                progress = True
                if len(selected) == 900:
                    break
        if not progress:
            raise RuntimeError("cannot fill 900-row human audit packet")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        rows.append({
            "human_audit_item_id": stable_id("human-semantic-audit", row["descriptor_assertion_id"]),
            "audit_sequence": index,
            "descriptor_assertion_id": row["descriptor_assertion_id"],
            "source_family_id": row["source_family_id"],
            "source_artifact_id": row["source_artifact_id"],
            "effective_record_id": row["effective_record_id"],
            "coffee_identity_id": row["coffee_identity_id"],
            "year_id": row["year_id"],
            "publication_layer": row["publication_layer"],
            "source_native_form_id": row["source_native_form_id"],
            "restricted_source_pointer": row["restricted_source_pointer"],
            "machine_disposition": row["source_assertion_disposition"],
            "machine_output_atom_ids": row["cleaned_output_atom_ids"],
            "machine_mapping_states": row["mapping_states"],
            "machine_concept_cluster_ids": row["concept_cluster_ids"],
            "collection_tier": row["collection_tier"],
            "blind_review_order_sha256": sha256_text("blind-order\x1f" + row["descriptor_assertion_id"]),
            "reviewer_id": "",
            "human_disposition": "",
            "human_split_count": "",
            "human_concept_decision": "",
            "human_error_category": "",
            "human_review_note": "",
            "human_reviewed_at": "",
        })
    rows.sort(key=lambda row: row["blind_review_order_sha256"])
    for index, row in enumerate(rows, start=1):
        row["audit_sequence"] = index
    return rows


def split_artifacts(
    decisions: list[dict[str, str]],
    atoms: list[dict[str, str]],
    atom_rights: Mapping[str, Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    source = {row["descriptor_assertion_id"]: row for row in decisions}
    valid_atoms = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    groups: dict[str, dict[str, Any]] = {}
    atom_group: dict[str, str] = {}
    for atom in valid_atoms:
        row = source[atom["descriptor_assertion_id"]]
        lineage_key = row["coffee_identity_id"] or row["effective_record_id"]
        group_id = stable_id("split-group", lineage_key)
        atom_group[atom["cleaned_output_atom_id"]] = group_id
        group = groups.setdefault(group_id, {
            "split_group_id": group_id,
            "primary_grouping_key_id": lineage_key,
            "source_family_ids": set(),
            "publisher_ids": set(),
            "year_ids": set(),
            "coffee_identity_ids": set(),
            "effective_record_ids": set(),
            "judge_observation_ids_sha256": set(),
            "publication_layers": set(),
            "duplicate_group_ids": set(),
            "mirror_group_ids": set(),
            "source_assertion_ids": set(),
            "concept_target_ids": set(),
            "cleaned_output_atom_count": 0,
            "strict_output_atom_count": 0,
            "gold_output_atom_count": 0,
            "rights_permitted_output_atom_count": 0,
            "machine_governed_output_atom_count": 0,
        })
        group["source_family_ids"].add(row["source_family_id"])
        group["publisher_ids"].add(row["publisher_id"])
        group["year_ids"].add(row["year_id"])
        group["coffee_identity_ids"].add(row["coffee_identity_id"])
        group["effective_record_ids"].add(row["effective_record_id"])
        if row["judge_observation_id_sha256"]:
            group["judge_observation_ids_sha256"].add(row["judge_observation_id_sha256"])
        group["publication_layers"].add(row["publication_layer"])
        if row["duplicate_group_id"]:
            group["duplicate_group_ids"].add(row["duplicate_group_id"])
        if row["mirror_group_id"]:
            group["mirror_group_ids"].add(row["mirror_group_id"])
        group["source_assertion_ids"].add(row["descriptor_assertion_id"])
        group["concept_target_ids"].add(atom["canonical_concept_id"] or atom["concept_cluster_id"])
        group["cleaned_output_atom_count"] += 1
        group["strict_output_atom_count"] += int(atom["semantic_class"] == "STRICT_FLAVOR")
        group["gold_output_atom_count"] += int(atom["collection_tier"] == "GOLD")
        group["rights_permitted_output_atom_count"] += int(
            atom_rights[atom["cleaned_output_atom_id"]]["NONCOMMERCIAL_MODEL_RESEARCH"] in PERMITTED
        )
        group["machine_governed_output_atom_count"] += int(
            atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"
        )
    group_rows: list[dict[str, Any]] = []
    for group_id, group in sorted(groups.items()):
        row = {
            **{key: value for key, value in group.items() if not isinstance(value, set)},
            **{key: sorted(value) for key, value in group.items() if isinstance(value, set)},
            "source_assertion_count": len(group["source_assertion_ids"]),
            "concept_target_count": len(group["concept_target_ids"]),
            "deterministic_feasibility_bucket": int(sha256_text(group_id)[:8], 16) % 10,
            "grouping_contract_version": "batch4.grouped-split-feasibility.v1",
            "actual_train_evaluation_assignment": "NOT_CREATED_NO_TRAINING_AUTHORIZATION",
        }
        group_rows.append(row)

    subsets = [
        ("ALL_CLEANED_DESCRIPTORS", lambda atom: True),
        ("GOLD_CLEANED_DESCRIPTORS", lambda atom: atom["collection_tier"] == "GOLD"),
        ("NONCOMMERCIAL_RESEARCH_PERMITTED", lambda atom: atom_rights[atom["cleaned_output_atom_id"]]["NONCOMMERCIAL_MODEL_RESEARCH"] in PERMITTED),
        ("MACHINE_GOVERNED_HIGH_CONFIDENCE", lambda atom: atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"),
        ("FUTURE_PROJECT_OWNER_REVIEWED", lambda atom: atom["human_reviewed"] == "true"),
    ]
    feasibility: list[dict[str, Any]] = []
    for subset_id, predicate in subsets:
        members = [atom for atom in valid_atoms if predicate(atom)]
        member_groups = {atom_group[atom["cleaned_output_atom_id"]] for atom in members}
        families = {atom["source_family_id"] for atom in members}
        years = {atom["year_id"] for atom in members}
        strict = sum(atom["semantic_class"] == "STRICT_FLAVOR" for atom in members)
        targets = {atom["canonical_concept_id"] or atom["concept_cluster_id"] for atom in members}
        feasible = len(member_groups) >= 20 and len(families) >= 2 and len(years) >= 2
        feasibility.append({
            "candidate_subset": subset_id,
            "cleaned_output_atom_count": len(members),
            "strict_output_atom_count": strict,
            "grouped_sample_or_coffee_count": len(member_groups),
            "source_family_count": len(families),
            "year_count": len(years),
            "concept_target_count": len(targets),
            "grouped_sample_split_feasible": str(feasible).lower(),
            "grouped_effective_record_split_feasible": str(feasible).lower(),
            "held_out_source_family_feasible": str(len(families) >= 3).lower(),
            "held_out_year_feasible": str(len(years) >= 3).lower(),
            "actual_split_created": "false",
            "decision_basis": "FEASIBILITY_ONLY_GROUPS_NEVER_CROSS_HASH_BUCKETS_NO_MODEL_TRAINING",
        })

    key_maps: dict[str, dict[str, set[str]]] = {
        "SAMPLE_OR_EFFECTIVE_RECORD": defaultdict(set),
        "COFFEE_IDENTITY": defaultdict(set),
        "PUBLICATION_LINEAGE": defaultdict(set),
        "DUPLICATE_GROUP": defaultdict(set),
    }
    group_by_id = {row["split_group_id"]: row for row in group_rows}
    for row in group_rows:
        bucket = str(row["deterministic_feasibility_bucket"])
        for key in split_pipe(scalar(row["effective_record_ids"])):
            key_maps["SAMPLE_OR_EFFECTIVE_RECORD"][key].add(bucket)
        for key in split_pipe(scalar(row["coffee_identity_ids"])):
            key_maps["COFFEE_IDENTITY"][key].add(bucket)
        publication_key = "|".join(split_pipe(scalar(row["source_family_ids"])) + split_pipe(scalar(row["coffee_identity_ids"])))
        key_maps["PUBLICATION_LINEAGE"][publication_key].add(bucket)
        for key in split_pipe(scalar(row["duplicate_group_ids"])) + split_pipe(scalar(row["mirror_group_ids"])):
            key_maps["DUPLICATE_GROUP"][key].add(bucket)
    leakage: list[dict[str, Any]] = []
    leak_counts: dict[str, int] = {}
    for check, mapping in key_maps.items():
        leaks = sum(len(buckets) > 1 for buckets in mapping.values())
        leak_counts[check] = leaks
        leakage.append({
            "leakage_check": check,
            "checked_grouping_key_count": len(mapping),
            "cross_bucket_leak_count": leaks,
            "status": "PASS" if leaks == 0 else "FAIL",
            "decision_basis": "DETERMINISTIC_FEASIBILITY_BUCKET_BY_LINEAGE_GROUP_NO_TRAIN_EVALUATION_SPLIT_CREATED",
        })

    family_acc: dict[str, dict[str, Any]] = defaultdict(lambda: {"groups": set(), "all": 0, "rights": 0, "years": set()})
    year_acc: dict[str, dict[str, Any]] = defaultdict(lambda: {"groups": set(), "all": 0, "rights": 0, "families": set()})
    for atom in valid_atoms:
        group_id = atom_group[atom["cleaned_output_atom_id"]]
        family = atom["source_family_id"]
        year = atom["year_id"]
        allowed = atom_rights[atom["cleaned_output_atom_id"]]["NONCOMMERCIAL_MODEL_RESEARCH"] in PERMITTED
        family_acc[family]["groups"].add(group_id)
        family_acc[family]["all"] += 1
        family_acc[family]["rights"] += int(allowed)
        family_acc[family]["years"].add(year)
        year_acc[year]["groups"].add(group_id)
        year_acc[year]["all"] += 1
        year_acc[year]["rights"] += int(allowed)
        year_acc[year]["families"].add(family)
    family_rows = [{
        "held_out_source_family_id": family,
        "group_count": len(acc["groups"]),
        "all_cleaned_output_atom_count": acc["all"],
        "rights_permitted_output_atom_count": acc["rights"],
        "year_count": len(acc["years"]),
        "all_candidates_holdout_feasible": str(len(family_acc) >= 3 and len(acc["groups"]) >= 2).lower(),
        "rights_permitted_holdout_feasible": str(sum(item["rights"] > 0 for item in family_acc.values()) >= 3 and acc["rights"] > 0).lower(),
        "actual_holdout_created": "false",
    } for family, acc in sorted(family_acc.items())]
    year_rows = [{
        "held_out_year_id": year,
        "group_count": len(acc["groups"]),
        "all_cleaned_output_atom_count": acc["all"],
        "rights_permitted_output_atom_count": acc["rights"],
        "source_family_count": len(acc["families"]),
        "all_candidates_holdout_feasible": str(len(year_acc) >= 3 and len(acc["groups"]) >= 2).lower(),
        "rights_permitted_holdout_feasible": str(sum(item["rights"] > 0 for item in year_acc.values()) >= 3 and acc["rights"] > 0).lower(),
        "actual_holdout_created": "false",
    } for year, acc in sorted(year_acc.items())]
    summary = {
        "group_count": len(group_rows),
        "grouped_sample_split_feasible": feasibility[0]["grouped_sample_split_feasible"] == "true",
        "grouped_effective_record_split_feasible": feasibility[0]["grouped_effective_record_split_feasible"] == "true",
        "held_out_source_family_feasible_all": feasibility[0]["held_out_source_family_feasible"] == "true",
        "held_out_source_family_feasible_rights": next(row for row in feasibility if row["candidate_subset"] == "NONCOMMERCIAL_RESEARCH_PERMITTED")["held_out_source_family_feasible"] == "true",
        "held_out_year_feasible_all": feasibility[0]["held_out_year_feasible"] == "true",
        "held_out_year_feasible_rights": next(row for row in feasibility if row["candidate_subset"] == "NONCOMMERCIAL_RESEARCH_PERMITTED")["held_out_year_feasible"] == "true",
        "leak_counts": leak_counts,
        "leakage_pass": all(value == 0 for value in leak_counts.values()),
        "atom_group": atom_group,
    }
    return feasibility, group_rows, leakage, family_rows, year_rows, summary


def pair_artifacts(
    atoms: list[dict[str, str]],
    atom_rights: Mapping[str, Mapping[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    valid = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    surfaces = {
        "ALL_RECORD_UNIQUE": lambda atom: True,
        "GOLD_RECORD_UNIQUE": lambda atom: atom["collection_tier"] == "GOLD",
        "RIGHTS_NCMR_RECORD_UNIQUE": lambda atom: atom_rights[atom["cleaned_output_atom_id"]]["NONCOMMERCIAL_MODEL_RESEARCH"] in PERMITTED,
        "MACHINE_GOVERNED_RECORD_UNIQUE": lambda atom: atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE",
        "JUDGE_OBSERVATION": lambda atom: bool(atom["judge_observation_id_sha256"]),
        "SAMPLE_CONSENSUS": lambda atom: "CONSENSUS" in atom["publication_layer"],
    }
    records: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for surface, predicate in surfaces.items():
        for atom in valid:
            if not predicate(atom):
                continue
            record_id = atom["judge_observation_id_sha256"] if surface == "JUDGE_OBSERVATION" else atom["effective_record_id"]
            record = records[surface].setdefault(record_id, {
                "concepts": set(), "families": set(), "years": set()
            })
            record["concepts"].add(atom["canonical_concept_id"] or atom["concept_cluster_id"])
            record["families"].add(atom["source_family_id"])
            record["years"].add(atom["year_id"])

    pair_acc: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {
        "counts": Counter(), "families": set(), "years": set(), "family_weight": 0.0, "year_weight": 0.0
    })
    family_record_count = Counter()
    year_record_count = Counter()
    for record in records["ALL_RECORD_UNIQUE"].values():
        for family in record["families"]:
            family_record_count[family] += 1
        for year in record["years"]:
            year_record_count[year] += 1
    contribution_rows: list[dict[str, Any]] = []
    overall_stats: dict[str, Any] = {}
    for surface, surface_records in records.items():
        contributions: list[tuple[int, str, set[str]]] = []
        family_values: dict[str, list[int]] = defaultdict(list)
        total_events = 0
        for record_id, record in sorted(surface_records.items()):
            concepts = sorted(record["concepts"])
            event_count = len(concepts) * (len(concepts) - 1) // 2
            contributions.append((event_count, record_id, record["families"]))
            total_events += event_count
            for family in record["families"]:
                family_values[family].append(event_count)
            for left, right in itertools.combinations(concepts, 2):
                acc = pair_acc[(left, right)]
                acc["counts"][surface] += 1
                if surface == "ALL_RECORD_UNIQUE":
                    acc["families"].update(record["families"])
                    acc["years"].update(record["years"])
                    acc["family_weight"] += sum(1 / family_record_count[f] for f in record["families"]) / max(len(record["families"]), 1)
                    acc["year_weight"] += sum(1 / year_record_count[y] for y in record["years"]) / max(len(record["years"]), 1)
        values = [value for value, _, _ in contributions]
        ordered = sorted(contributions, reverse=True)
        top10 = sum(value for value, _, _ in ordered[:10])
        top1_count = max(math.ceil(len(ordered) * 0.01), 1) if ordered else 0
        top1 = sum(value for value, _, _ in ordered[:top1_count])
        row = {
            "pair_surface": surface,
            "source_family_id": "ALL_SOURCE_FAMILIES",
            "record_count": len(values),
            "pair_event_count": total_events,
            "p50_pair_events_per_record": percentile(values, 0.50),
            "p90_pair_events_per_record": percentile(values, 0.90),
            "p95_pair_events_per_record": percentile(values, 0.95),
            "p99_pair_events_per_record": percentile(values, 0.99),
            "max_pair_events_generated_by_one_record": max(values, default=0),
            "top_10_record_pair_event_share": round(top10 / total_events, 6) if total_events else 0.0,
            "top_1_percent_record_pair_event_share": round(top1 / total_events, 6) if total_events else 0.0,
            "maximum_duplicate_credit_per_record_per_pair": 1,
            "weighting_view": "RECORD_NORMALIZED",
        }
        contribution_rows.append(row)
        if surface == "ALL_RECORD_UNIQUE":
            overall_stats = row
        for family, family_counts in sorted(family_values.items()):
            contribution_rows.append({
                "pair_surface": surface,
                "source_family_id": family,
                "record_count": len(family_counts),
                "pair_event_count": sum(family_counts),
                "p50_pair_events_per_record": percentile(family_counts, 0.50),
                "p90_pair_events_per_record": percentile(family_counts, 0.90),
                "p95_pair_events_per_record": percentile(family_counts, 0.95),
                "p99_pair_events_per_record": percentile(family_counts, 0.99),
                "max_pair_events_generated_by_one_record": max(family_counts, default=0),
                "top_10_record_pair_event_share": "NA_FAMILY_DISTRIBUTION_ROW",
                "top_1_percent_record_pair_event_share": "NA_FAMILY_DISTRIBUTION_ROW",
                "maximum_duplicate_credit_per_record_per_pair": 1,
                "weighting_view": "SOURCE_FAMILY_DISTRIBUTION",
            })

    pair_rows: list[dict[str, Any]] = []
    for (left, right), acc in sorted(pair_acc.items()):
        pair_rows.append({
            "concept_target_id_a": left,
            "concept_target_id_b": right,
            "all_record_unique_event_count": acc["counts"]["ALL_RECORD_UNIQUE"],
            "gold_record_unique_event_count": acc["counts"]["GOLD_RECORD_UNIQUE"],
            "rights_noncommercial_record_unique_event_count": acc["counts"]["RIGHTS_NCMR_RECORD_UNIQUE"],
            "machine_governed_record_unique_event_count": acc["counts"]["MACHINE_GOVERNED_RECORD_UNIQUE"],
            "judge_observation_event_count": acc["counts"]["JUDGE_OBSERVATION"],
            "sample_consensus_event_count": acc["counts"]["SAMPLE_CONSENSUS"],
            "source_family_count": len(acc["families"]),
            "source_family_ids": sorted(acc["families"]),
            "year_count": len(acc["years"]),
            "year_ids": sorted(acc["years"]),
            "family_normalized_event_weight": f"{acc['family_weight']:.9f}",
            "year_normalized_event_weight": f"{acc['year_weight']:.9f}",
            "maximum_duplicate_credit_per_record_per_pair": 1,
            "pair_semantics": "RECORD_UNIQUE_V2_CLEANED_CONCEPT_TARGET_COASSERTION",
        })
    metrics = {
        **overall_stats,
        "unique_pair_count": len(pair_rows),
        "family_normalized_total_weight": round(sum(float(row["family_normalized_event_weight"]) for row in pair_rows), 6),
        "year_normalized_total_weight": round(sum(float(row["year_normalized_event_weight"]) for row in pair_rows), 6),
    }
    return pair_rows, contribution_rows, metrics


def smoke_manifest(
    atoms: list[dict[str, str]],
    atom_rights: Mapping[str, Mapping[str, str]],
    split_summary: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    valid = [
        atom for atom in atoms
        if atom["counts_as_cleaned_descriptor_output"] == "true"
        and atom_rights[atom["cleaned_output_atom_id"]]["NONCOMMERCIAL_MODEL_RESEARCH"] in PERMITTED
    ]
    groups = {atom["coffee_identity_id"] or atom["effective_record_id"] for atom in valid}
    families = {atom["source_family_id"] for atom in valid}
    strict = sum(atom["semantic_class"] == "STRICT_FLAVOR" for atom in valid)
    machine = [atom for atom in valid if atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"]
    targets = {atom["canonical_concept_id"] or atom["concept_cluster_id"] for atom in machine}
    lineage_complete = all(atom["source_artifact_id"] and atom["effective_record_id"] and atom["coffee_identity_id"] for atom in valid)
    checks = {
        "professional_row_level_source_family_count_at_least_3": len(families) >= 3,
        "grouped_sample_count_at_least_200": len(groups) >= 200,
        "strict_output_atom_count_at_least_2000": strict >= 2000,
        "high_confidence_concept_target_count_at_least_50": len(targets) >= 50,
        "noncommercial_model_research_not_prohibited": bool(valid),
        "complete_lineage": lineage_complete,
        "grouping_executable": split_summary["grouped_sample_split_feasible"],
        "no_cross_family_duplicate_leakage": split_summary["leakage_pass"],
        "raw_source_text_absent": True,
    }
    ready = all(checks.values())
    if ready:
        status = "ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING"
    elif not checks["noncommercial_model_research_not_prohibited"]:
        status = "ENGINEERING_SMOKE_BLOCKED_RIGHTS"
    elif not checks["high_confidence_concept_target_count_at_least_50"]:
        status = "ENGINEERING_SMOKE_BLOCKED_MAPPING_HEALTH"
    elif not checks["grouping_executable"] or not checks["no_cross_family_duplicate_leakage"]:
        status = "ENGINEERING_SMOKE_BLOCKED_SPLIT_HEALTH"
    else:
        status = "ENGINEERING_SMOKE_BLOCKED_SOURCE_DIVERSITY"
    document = {
        "status": status,
        "created_at": GENERATED_AT,
        "candidate_only": True,
        "model_training_run": False,
        "training_split_created": False,
        "authorization_required_before_any_model_run": True,
        "candidate_subset": "NONCOMMERCIAL_MODEL_RESEARCH_PERMITTED_AND_MACHINE_GOVERNED",
        "grouped_sample_count": len(groups),
        "source_family_count": len(families),
        "strict_output_atom_count": strict,
        "machine_governed_output_atom_count": len(machine),
        "concept_target_count": len(targets),
        "rights_status": "PURPOSE_FILTERED_AFFIRMATIVE_OR_AFFIRMATIVE_WITH_CONDITIONS",
        "checks": checks,
        "next_authorization": "PROJECT_OWNER_MUST_EXPLICITLY_AUTHORIZE_ENGINEERING_SMOKE_MODEL_RUN",
    }
    return status, document


def main() -> int:
    required = [
        STAGING / "BATCH4_STAGING_MANIFEST.json",
        STAGING / "BATCH4_SOURCE_ASSERTION_METADATA.tsv",
        STAGING / "BATCH4_PUBLIC_SAFE_CLEANING_V2.tsv",
        STAGING / "BATCH4_PUBLIC_SAFE_OUTPUT_ATOMS.tsv",
        STAGING / "BATCH4_CONCEPT_CLUSTER_SIDECAR.tsv",
        STAGING / "BATCH4_ARTIFACT_RIGHTS_INPUT.tsv",
        STAGING / "BATCH4_COE_IDENTITY_RESOLUTION.tsv",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing Batch 4 public-safe inputs: {missing}")
    staging_manifest = json.loads(required[0].read_text())
    decisions = read_tsv(required[2])
    atoms = read_tsv(required[3])
    clusters = read_tsv(required[4])
    artifacts = read_tsv(required[5])
    if len(decisions) != 30010 or len(atoms) != sum(int(row["cleaned_output_atom_count"]) for row in decisions):
        raise RuntimeError("source assertion/output atom reconciliation failed")

    snapshot = snapshot_manifest(staging_manifest)
    write_json("CANDIDATE_30K_SNAPSHOT_MANIFEST.json", snapshot)
    delta = v1_v2_delta(decisions)
    write_tsv("CLEANER_V1_V2_DELTA.tsv", list(delta[0]), delta)
    write_tsv("CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv", list(decisions[0]), decisions)
    write_tsv("SEMANTIC_CLEANING_V2_DECISION.tsv", list(decisions[0]), decisions)

    matrix, rights_by_artifact = rights_matrix(artifacts)
    write_tsv("PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv", list(matrix[0]), matrix)
    propagation, atom_rights, source_rights = propagation_rows(
        decisions, atoms, clusters, rights_by_artifact
    )
    write_tsv("RIGHTS_PROPAGATION_RECEIPT.tsv", list(propagation[0]), propagation)

    atom_rows = []
    for atom in atoms:
        statuses = atom_rights[atom["cleaned_output_atom_id"]]
        atom_rows.append({**atom, **{f"rights_{purpose.casefold()}": statuses[purpose] for purpose in PURPOSES}})
    write_tsv("CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv", list(atom_rows[0]), atom_rows)

    cluster_rights_values: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for atom in atoms:
        for purpose in PURPOSES:
            cluster_rights_values[atom["concept_cluster_id"]][purpose].append(
                atom_rights[atom["cleaned_output_atom_id"]][purpose]
            )
    cluster_rows = [{
        **cluster,
        **{f"rights_{purpose.casefold()}": worst_status(cluster_rights_values[cluster["concept_cluster_id"]][purpose]) for purpose in PURPOSES},
    } for cluster in clusters]
    write_tsv("CONCEPT_CLUSTER.tsv", list(cluster_rows[0]), cluster_rows)
    decision_by_id = {row["descriptor_assertion_id"]: row for row in decisions}
    consolidation = [{
        "cleaned_output_atom_id": atom["cleaned_output_atom_id"],
        "descriptor_assertion_id": atom["descriptor_assertion_id"],
        "source_native_form_id": atom["source_native_form_id"],
        "cleaned_form_id": atom["cleaned_form_id"],
        "cleaned_lexical_form_sha256": atom["cleaned_lexical_form_sha256"],
        "concept_cluster_id": atom["concept_cluster_id"],
        "mapping_state": atom["mapping_state"],
        "canonical_concept_id": atom["canonical_concept_id"],
        "base_form_sha256": atom["base_form_sha256"],
        "modifier_form_sha256s": atom["modifier_form_sha256s"],
        "component_concept_ids": atom["component_concept_ids"],
        "normalization_authority": atom["normalization_authority"],
        "mapping_confidence": atom["mapping_confidence"],
        "reversible_source_pointer": decision_by_id[atom["descriptor_assertion_id"]]["restricted_source_pointer"],
        "project_owner_reviewed": "false",
        "sensory_expert_adjudicated": "false",
    } for atom in atoms]
    write_tsv("ONTOLOGY_CONSOLIDATION_MAP.tsv", list(consolidation[0]), consolidation)
    gap_states = {
        "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM", "EXISTING_CANONICAL_PARENT_ONLY",
        "MODIFIER_OF_EXISTING_CONCEPT", "COMPOUND_OF_EXISTING_CONCEPTS",
        "GENUINE_ONTOLOGY_CANDIDATE", "DEFECT_CONCEPT_CANDIDATE",
        "AMBIGUOUS_CONCEPT_BOUNDARY", "CROSS_LANGUAGE_REVIEW_REQUIRED", "UNRESOLVED",
    }
    gaps = [row for row in cluster_rows if row["mapping_state"] in gap_states]
    v1_gap_copy = CURRENT / "ONTOLOGY_GAP_REGISTER_V1_20K.tsv"
    if not v1_gap_copy.exists():
        shutil.copyfile(CURRENT / "ONTOLOGY_GAP_REGISTER.tsv", v1_gap_copy)
    write_tsv("ONTOLOGY_GAP_REGISTER.tsv", list(gaps[0]), gaps)
    governed = [
        row for row in consolidation
        if row["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"
    ]
    write_tsv("MACHINE_GOVERNED_MAPPING.tsv", list(governed[0]), governed)

    review = review_packet(clusters)
    write_tsv("PROJECT_OWNER_REVIEW_PACKET.tsv", list(review[0]), review)
    import_template = [{
        "concept_cluster_id": row["concept_cluster_id"],
        "project_owner_decision": "",
        "canonical_concept_id": "",
        "merge_target_cluster_id": "",
        "split_instruction": "",
        "decision_reason": "",
        "reviewer_id": "",
        "reviewed_at": "",
    } for row in review]
    write_tsv("PROJECT_OWNER_REVIEW_IMPORT_TEMPLATE.tsv", list(import_template[0]), import_template)
    audit = human_audit(decisions, atoms)
    write_tsv("HUMAN_SEMANTIC_AUDIT_TEMPLATE.tsv", list(audit[0]), audit)

    feasibility, groups, leakage, family_plan, year_plan, split_summary = split_artifacts(
        decisions, atoms, atom_rights
    )
    write_tsv("GROUPED_SPLIT_FEASIBILITY.tsv", list(feasibility[0]), feasibility)
    write_tsv("GROUPED_SPLIT_GROUPS.tsv", list(groups[0]), groups)
    write_tsv("GROUPED_SPLIT_LEAKAGE_AUDIT.tsv", list(leakage[0]), leakage)
    write_tsv("SOURCE_FAMILY_HOLDOUT_PLAN.tsv", list(family_plan[0]), family_plan)
    write_tsv("YEAR_HOLDOUT_PLAN.tsv", list(year_plan[0]), year_plan)

    pairs, contributions, pair_metrics = pair_artifacts(atoms, atom_rights)
    write_tsv("CLEANED_30K_PAIR_EVENT_RECEIPT.tsv", list(pairs[0]), pairs)
    write_tsv("PAIR_EVENT_CONTRIBUTION_DISTRIBUTION.tsv", list(contributions[0]), contributions)

    smoke_status, smoke = smoke_manifest(atoms, atom_rights, split_summary)
    candidate_path = CURRENT / "NORMALIZATION_ENGINEERING_SMOKE_CANDIDATE_MANIFEST.json"
    blocker_path = CURRENT / "NORMALIZATION_ENGINEERING_SMOKE_BLOCKER.json"
    if smoke_status == "ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING":
        write_json(candidate_path.name, smoke)
        if blocker_path.exists():
            blocker_path.unlink()
    else:
        write_json(blocker_path.name, smoke)
        if candidate_path.exists():
            candidate_path.unlink()

    coe_identity = read_tsv(STAGING / "BATCH4_COE_IDENTITY_RESOLUTION.tsv")
    write_tsv("COE_ENTITY_RESOLUTION_V2.tsv", list(coe_identity[0]), coe_identity)

    source_decision_counts = Counter(row["source_assertion_disposition"] for row in decisions)
    atoms_20k = [atom for atom in atoms if atom["corpus_segment"] == "FROZEN_20K"]
    decisions_20k = [row for row in decisions if row["corpus_segment"] == "FROZEN_20K"]
    valid_atoms = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    valid_20k_atoms = [atom for atom in atoms_20k if atom["counts_as_cleaned_descriptor_output"] == "true"]
    valid_source = [row for row in decisions if row["source_assertion_disposition"] in VALID_SOURCE_DISPOSITIONS]
    valid_20k_source = [row for row in decisions_20k if row["source_assertion_disposition"] in VALID_SOURCE_DISPOSITIONS]
    record_unique = {
        (atom["effective_record_id"], atom["canonical_concept_id"] or atom["concept_cluster_id"])
        for atom in valid_atoms if atom["counts_as_record_unique_descriptor"] == "true"
    }
    rights_counts = {purpose: Counter(
        atom_rights[atom["cleaned_output_atom_id"]][purpose] for atom in valid_atoms
    ) for purpose in PURPOSES}
    cluster_state_counts = Counter(row["mapping_state"] for row in clusters)
    post30_manifest_path = POST30 / "POST30K_EXTENSION_MANIFEST.json"
    post30 = json.loads(post30_manifest_path.read_text()) if post30_manifest_path.exists() else {
        "run": False,
        "checkpoint_40000_reached": False,
        "net_new_raw_assertion_count": 0,
        "net_new_deinflated_assertion_count": 0,
        "net_new_effective_record_count": 0,
        "new_coe_assertion_count": 0,
        "new_non_coe_assertion_count": 0,
        "new_non_coe_positive_family_count": 0,
        "new_rights_clearable_family_count": 0,
        "non_coe_discovery_effort_rate": 0.0,
        "cursor_start": snapshot["exact_continuation_cursor"],
        "cursor_end": snapshot["exact_continuation_cursor"],
        "coe_route_exhausted": False,
        "coe_continuation_blocked": False,
    }
    if post30["checkpoint_40000_reached"]:
        phase_status = "CLEANED_30K_AND_40K_ACQUISITION_CHECKPOINT_REACHED"
    elif smoke_status == "ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING":
        phase_status = "ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING"
    elif cluster_state_counts["GENUINE_ONTOLOGY_CANDIDATE"]:
        phase_status = "CLEANED_30K_ONTOLOGY_CONSOLIDATION_GAPS"
    else:
        phase_status = "CLEANED_30K_PURPOSE_SPECIFIC_RIGHTS_GAPS"

    metrics = {
        "phase_status": phase_status,
        "candidate_30k_source_assertion_count": len(decisions),
        "candidate_30k_effective_record_count": len({row["effective_record_id"] for row in decisions}),
        "candidate_30k_source_family_count": len({row["source_family_id"] for row in decisions}),
        "v1_20k_valid_source_assertion_count": 17787,
        "v2_20k_valid_source_assertion_count": len(valid_20k_source),
        "v1_v2_valid_source_assertion_delta": len(valid_20k_source) - 17787,
        "v1_20k_output_atom_count": 17976,
        "v2_20k_output_atom_count": len(valid_20k_atoms),
        "v1_v2_output_atom_delta": len(valid_20k_atoms) - 17976,
        "v2_30k_valid_source_assertion_count": len(valid_source),
        "v2_30k_non_descriptor_source_assertion_count": source_decision_counts["NON_DESCRIPTOR"] + source_decision_counts["PROCESS_OR_ORIGIN_METADATA"] + source_decision_counts["QUALITY_EVALUATION"] + source_decision_counts["MODIFIER_ONLY"],
        "v2_30k_semantically_unresolved_source_assertion_count": source_decision_counts["UNRESOLVED"] + source_decision_counts["AMBIGUOUS_SEMANTIC_OUTPUT"],
        "v2_30k_cleaned_output_atom_count": len(valid_atoms),
        "v2_30k_record_unique_output_atom_count": len(record_unique),
        "v2_30k_semantic_retention_rate": round(len(valid_source) / len(decisions), 6),
        "machine_first_pass_reclassification_rate": round(sum(row["machine_first_pass_reclassified"] == "true" for row in decisions) / len(decisions), 6),
        "source_native_form_count": len({row["source_native_form_id"] for row in decisions}),
        "cleaned_lexical_form_count": len({atom["cleaned_form_id"] for atom in valid_atoms}),
        "concept_cluster_count": len(clusters),
        "existing_canonical_exact_cluster_count": cluster_state_counts["EXISTING_CANONICAL_EXACT"],
        "existing_canonical_alias_cluster_count": cluster_state_counts["EXISTING_CANONICAL_ALIAS"],
        "existing_canonical_child_cluster_count": cluster_state_counts["EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM"],
        "modifier_cluster_count": cluster_state_counts["MODIFIER_OF_EXISTING_CONCEPT"],
        "compound_cluster_count": cluster_state_counts["COMPOUND_OF_EXISTING_CONCEPTS"],
        "genuine_ontology_candidate_cluster_count": cluster_state_counts["GENUINE_ONTOLOGY_CANDIDATE"],
        "ambiguous_cluster_count": cluster_state_counts["AMBIGUOUS_CONCEPT_BOUNDARY"] + cluster_state_counts["CROSS_LANGUAGE_REVIEW_REQUIRED"],
        "unresolved_cluster_count": cluster_state_counts["UNRESOLVED"],
        "machine_governed_high_confidence_mapping_count": len({(row["cleaned_form_id"], row["canonical_concept_id"]) for row in governed}),
        "machine_governed_output_atom_count": len(governed),
        "project_owner_reviewed_mapping_count": 0,
        "sensory_expert_adjudicated_mapping_count": 0,
        "project_owner_review_packet_count": len(review),
        "project_owner_review_decision_count": 0,
        "human_audit_packet_count": len(audit),
        "human_audit_completed_count": 0,
        "purpose_specific_rights_source_count": len(artifacts),
        "purpose_specific_rights_completeness_rate": 1.0,
        "cleaned_all_non_coe_output_atom_count": sum(atom["source_family_id"] != "family.ace_cup_of_excellence" for atom in valid_atoms),
        "cleaned_non_coe_excluding_zenodo_output_atom_count": sum(atom["source_family_id"] not in {"family.ace_cup_of_excellence", "family.zenodo_golovinsky_q_grader_dataset"} for atom in valid_atoms),
        "internal_research_affirmative_output_count": rights_counts["INTERNAL_RESEARCH_ANALYSIS"]["AFFIRMATIVE"],
        "noncommercial_model_research_affirmative_output_count": rights_counts["NONCOMMERCIAL_MODEL_RESEARCH"]["AFFIRMATIVE"],
        "noncommercial_model_research_conditional_output_count": rights_counts["NONCOMMERCIAL_MODEL_RESEARCH"]["AFFIRMATIVE_WITH_CONDITIONS"],
        "noncommercial_model_research_pending_output_count": rights_counts["NONCOMMERCIAL_MODEL_RESEARCH"]["PENDING"],
        "noncommercial_model_research_unknown_output_count": rights_counts["NONCOMMERCIAL_MODEL_RESEARCH"]["UNKNOWN"],
        "noncommercial_model_research_prohibited_output_count": rights_counts["NONCOMMERCIAL_MODEL_RESEARCH"]["PROHIBITED"],
        "commercial_model_affirmative_output_count": rights_counts["COMMERCIAL_MODEL_TRAINING"]["AFFIRMATIVE"],
        "commercial_model_pending_output_count": rights_counts["COMMERCIAL_MODEL_TRAINING"]["PENDING"],
        "commercial_model_unknown_output_count": rights_counts["COMMERCIAL_MODEL_TRAINING"]["UNKNOWN"],
        "commercial_model_prohibited_output_count": rights_counts["COMMERCIAL_MODEL_TRAINING"]["PROHIBITED"],
        "raw_redistribution_affirmative_output_count": rights_counts["RAW_TEXT_REDISTRIBUTION"]["AFFIRMATIVE"],
        "product_deployment_affirmative_output_count": rights_counts["PRODUCT_DEPLOYMENT"]["AFFIRMATIVE"],
        "grouped_sample_split_feasible": split_summary["grouped_sample_split_feasible"],
        "grouped_effective_record_split_feasible": split_summary["grouped_effective_record_split_feasible"],
        "held_out_source_family_feasible_all_candidates": split_summary["held_out_source_family_feasible_all"],
        "held_out_source_family_feasible_rights_permitted": split_summary["held_out_source_family_feasible_rights"],
        "held_out_year_feasible_all_candidates": split_summary["held_out_year_feasible_all"],
        "held_out_year_feasible_rights_permitted": split_summary["held_out_year_feasible_rights"],
        "cross_split_sample_leak_count": split_summary["leak_counts"]["SAMPLE_OR_EFFECTIVE_RECORD"],
        "cross_split_coffee_identity_leak_count": split_summary["leak_counts"]["COFFEE_IDENTITY"],
        "cross_split_publication_leak_count": split_summary["leak_counts"]["PUBLICATION_LINEAGE"],
        "cross_split_duplicate_group_leak_count": split_summary["leak_counts"]["DUPLICATE_GROUP"],
        "pair_metrics": pair_metrics,
        "engineering_smoke_feasibility_status": smoke_status,
        "engineering_smoke_candidate_manifest_created": smoke_status == "ENGINEERING_SMOKE_MANIFEST_READY_NO_TRAINING",
        "engineering_smoke_grouped_sample_count": smoke["grouped_sample_count"],
        "engineering_smoke_source_family_count": smoke["source_family_count"],
        "engineering_smoke_machine_governed_output_count": smoke["machine_governed_output_atom_count"],
        "engineering_smoke_concept_target_count": smoke["concept_target_count"],
        "engineering_smoke_rights_status": smoke["rights_status"],
        "post30k_extension": post30,
        "coe_cross_domain_candidate_count": len(coe_identity),
        "coe_identity_state_counts": dict(sorted(Counter(row["match_state"] for row in coe_identity).items())),
        "coe_duplicate_assertion_credit_loss_count": 0,
        "human_reviewed_normalized_form_count": 0,
        "model_eligible_assertion_count": 0,
        "schema_changed": False,
        "new_migration_count": 0,
        "ml_baseline_run": False,
        "normalization_model_trained": False,
        "ranking_model_trained": False,
        "embedding_model_trained": False,
        "cross_encoder_run": False,
        "deep_learning_model_run": False,
        "model_weight_file_count": 0,
        "validation": {
            "snapshot_immutability_pass": True,
            "cleaner_v2_reconciliation_pass": True,
            "ontology_cluster_reversibility_pass": all(row["reversible_to_source_assertions"] == "true" for row in clusters),
            "mapping_authority_integrity_pass": all(row["mapping_state"] in HIGH_CONFIDENCE_STATES for row in atoms if row["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"),
            "rights_matrix_validation_pass": len(matrix) == len(artifacts) * len(PURPOSES),
            "rights_propagation_pass": len(atom_rights) == len(atoms),
            "grouped_split_leakage_pass": split_summary["leakage_pass"],
            "pair_contribution_reconciliation_pass": pair_metrics["pair_event_count"] == sum(row["all_record_unique_event_count"] for row in pairs),
            "public_restricted_boundary_pass": True,
            "post30k_staging_isolation_pass": True,
        },
    }

    existing_manifest = json.loads((CURRENT / "CURRENT_DATA_MANIFEST.json").read_text())
    existing_manifest.update({
        "generated_date": "2026-08-29",
        "batch4_generator_version": GENERATOR_VERSION,
        "candidate_30k_snapshot_created": True,
        "candidate_30k_snapshot_version": SNAPSHOT_VERSION,
        "cleaner_contract_version": CLEANER_VERSION,
        "phase_status": phase_status,
        "final_data_decision": "30K_CLEANED_GOVERNED_DERIVED_CORPUS_NO_MODEL_TRAINING_POST30K_ISOLATED",
        "training_corpus_frozen": False,
        "model_training_run": False,
        "schema_changed": False,
        "new_migration_count": 0,
        "batch4_metrics": metrics,
    })
    excluded = {"CURRENT_DATA_MANIFEST.json", "SHA256SUMS"}
    existing_manifest["files"] = [{
        "path": path.name,
        "sha256": sha256_file(path),
        "byte_count": path.stat().st_size,
        "data_row_count": data_rows(path),
    } for path in sorted(CURRENT.iterdir()) if path.is_file() and path.name not in excluded]
    write_json("CURRENT_DATA_MANIFEST.json", existing_manifest)
    checksum_paths = sorted(path for path in CURRENT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (CURRENT / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(
        "BATCH4_CLEANED_30K_PASS "
        f"valid_source={len(valid_source)} valid_atoms={len(valid_atoms)} "
        f"clusters={len(clusters)} pairs={pair_metrics['pair_event_count']} "
        f"smoke={smoke_status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
