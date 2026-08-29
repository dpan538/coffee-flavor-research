#!/usr/bin/env python3
"""Generate deterministic public Batch 3 cleaning products from safe sidecars."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
STAGING = ROOT / "db" / "data" / "candidate-cleaning-staging"
EXTENSION = ROOT / "db" / "data" / "post20k-extension-staging"

SNAPSHOT_VERSION = "professional-descriptor-candidate-v0-20k"
GENERATOR_VERSION = "batch3.public-cleaning-generator.v1"
GENERATED_AT = "2026-08-29T00:00:00Z"
VALID_CLASSES = {
    "STRICT_FLAVOR", "BROAD_SENSORY", "DEFECT_OR_NEGATIVE_SENSORY"
}

DECISION = STAGING / "BATCH3_PUBLIC_SAFE_CLEANING_SIDECAR.tsv"
SEGMENTATION = STAGING / "BATCH3_PUBLIC_SAFE_SEGMENTATION_SIDECAR.tsv"
NORMALIZATION = STAGING / "BATCH3_PUBLIC_SAFE_NORMALIZATION_SIDECAR.tsv"
ENTITY = STAGING / "BATCH3_PUBLIC_SAFE_COE_ENTITY_RESOLUTION.tsv"
DUPLICATE = STAGING / "BATCH3_PUBLIC_SAFE_COE_DUPLICATE_DECISION.tsv"
AUDIT = STAGING / "BATCH3_PUBLIC_SAFE_SEMANTIC_AUDIT.tsv"
STAGING_MANIFEST = STAGING / "BATCH3_STAGING_MANIFEST.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_id(prefix: str, material: str) -> str:
    return f"{prefix}:{hashlib.sha256(material.encode()).hexdigest()[:24]}"


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    return str(value)


def write_tsv(name: str, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    names = list(fields)
    with (CURRENT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=names, delimiter="\t", lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: scalar(row.get(name, "")) for name in names})


def write_json(name: str, value: Any) -> None:
    (CURRENT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def data_rows(path: Path) -> str:
    if path.suffix != ".tsv":
        return "NA_NOT_TABULAR"
    with path.open(encoding="utf-8") as handle:
        return str(max(sum(1 for _ in handle) - 1, 0))


def copy_public_sidecars() -> None:
    translations = {
        DECISION: "SEMANTIC_CLEANING_DECISION.tsv",
        SEGMENTATION: "SEGMENTATION_DECISION.tsv",
        NORMALIZATION: "CANONICAL_NORMALIZATION_MAP.tsv",
        ENTITY: "COE_ENTITY_RESOLUTION.tsv",
        DUPLICATE: "COE_CROSS_DOMAIN_DUPLICATE_DECISION.tsv",
        AUDIT: "SOURCE_STRATIFIED_SEMANTIC_AUDIT.tsv",
    }
    for source, name in translations.items():
        (CURRENT / name).write_bytes(source.read_bytes())


def snapshot_manifest(base_ledger: list[dict[str, str]]) -> dict[str, Any]:
    batch2_manifest = ROOT / "db" / "data" / "professional-descriptor-staging" / "BATCH2_PUBLIC_MANIFEST.json"
    content = {
        "contract_version": "candidate-20k-snapshot-manifest.v1",
        "snapshot_version": SNAPSHOT_VERSION,
        "snapshot_role": "FROZEN_CANDIDATE_ACQUISITION_DENOMINATOR_NOT_TRAINING_OR_REVIEWED_DATA",
        "created_at": GENERATED_AT,
        "immutable": True,
        "frozen_raw_candidate_assertion_count": len(base_ledger),
        "frozen_mechanically_deinflated_assertion_count": sum(row["counts_as_assertion"] == "true" for row in base_ledger),
        "frozen_record_unique_assertion_count": sum(row["counts_as_record_unique_descriptor"] == "true" for row in base_ledger),
        "frozen_effective_record_count": len({row["effective_record_id"] for row in base_ledger if row["counts_as_assertion"] == "true"}),
        "frozen_source_family_count": len({row["source_family_id"] for row in base_ledger if row["counts_as_assertion"] == "true"}),
        "canonical_source_ledger_path": "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv",
        "canonical_source_ledger_sha256": sha256_file(CURRENT / "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        "batch2_manifest_sha256": sha256_file(batch2_manifest),
        "cleaning_staging_manifest_sha256": sha256_file(STAGING_MANIFEST),
        "exact_post20k_continuation_cursor": "archive-page=12;detail-index=10;url=https://farmdirectory.cupofexcellence.org/listing/9-liquidambar-honduras-2026-parainema-catracha/",
        "post20k_extension_included_in_snapshot": False,
        "human_reviewed": False,
        "model_eligible": False,
    }
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
    content["snapshot_content_sha256"] = sha256_bytes(canonical)
    return content


def cleaned_ledger(
    base: list[dict[str, str]], decisions: list[dict[str, str]]
) -> list[dict[str, Any]]:
    by_id = {row["descriptor_assertion_id"]: row for row in base}
    result: list[dict[str, Any]] = []
    seen_record_descriptor: set[tuple[str, str]] = set()
    for decision in decisions:
        if decision["counts_as_assertion"] != "true":
            continue
        source = by_id[decision["descriptor_assertion_id"]]
        hashes = decision["cleaned_lexical_form_sha256s"].split("|")
        classes = decision["semantic_classes"].split("|")
        states = decision["mapping_states"].split("|")
        concepts = decision["canonical_concept_ids"].split("|")
        confidences = decision["mapping_confidences"].split("|")
        if not (len(hashes) == len(classes) == len(states) == len(concepts) == len(confidences)):
            raise RuntimeError("cleaning sidecar parallel-field length mismatch")
        for ordinal, (lexical_hash, klass, state, concept, confidence) in enumerate(
            zip(hashes, classes, states, concepts, confidences), 1
        ):
            if klass not in VALID_CLASSES:
                continue
            descriptor_identity = concept or f"cleaned-form:{lexical_hash[:24]}"
            record_key = (source["effective_record_id"], descriptor_identity)
            record_unique = record_key not in seen_record_descriptor
            seen_record_descriptor.add(record_key)
            result.append({
                "cleaned_descriptor_assertion_id": stable_id(
                    "cleaned-assertion", decision["descriptor_assertion_id"] + f"\x1f{ordinal}\x1f{lexical_hash}"
                ),
                "source_descriptor_assertion_id": decision["descriptor_assertion_id"],
                "snapshot_version": SNAPSHOT_VERSION,
                "source_dataset_id": source["source_dataset_id"],
                "source_family_id": source["source_family_id"],
                "source_route_id": source["source_route_id"],
                "source_artifact_id": source["source_artifact_id"],
                "source_file_sha256": source["source_file_sha256"],
                "source_locator": source["source_locator"],
                "effective_record_id": source["effective_record_id"],
                "coffee_identity_id": source["coffee_identity_id"],
                "edition_year": source["edition_year"],
                "preparation_service_id": source["preparation_service_id"],
                "publication_layer": source["publication_layer"],
                "source_field_label": source["source_field_label"],
                "source_field_text_sha256": source["source_field_text_sha256"],
                "atomic_source_text_sha256": source["atomic_source_text_sha256"],
                "source_native_form_or_restricted_pointer": f"hash:sha256:{decision['source_native_form_sha256']}",
                "cleaned_lexical_form_or_restricted_pointer": f"hash:sha256:{lexical_hash}",
                "cleaned_lexical_form_sha256": lexical_hash,
                "semantic_class": klass,
                "canonical_mapping_state": state,
                "canonical_concept_id": concept,
                "cleaned_descriptor_identity": descriptor_identity,
                "mapping_confidence": confidence,
                "segmentation_decision": decision["segmentation_decision"],
                "evidence_tier": decision["evidence_tier"],
                "rights_state": decision["rights_state"],
                "panelist_identity_sha256": decision["panelist_identity_sha256"],
                "panelist_sample_observation_sha256": decision["panelist_sample_observation_sha256"],
                "roast_evidence_sha256_or_state": decision["roast_evidence_sha256_or_state"],
                "counts_as_cleaned_assertion": "true",
                "counts_as_record_unique_cleaned_descriptor": str(record_unique).lower(),
                "publication_duplicate_suppressed": "false",
                "human_reviewed": "false",
                "expert_adjudicated": "false",
                "model_eligible": "false",
                "cleaner_version": decision["cleaner_version"],
            })
    result.sort(key=lambda row: row["cleaned_descriptor_assertion_id"])
    return result


def descriptor_distributions(cleaned: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    acc: dict[str, dict[str, Any]] = {}
    for row in cleaned:
        identity = row["cleaned_descriptor_identity"]
        item = acc.setdefault(identity, {
            "cleaned_descriptor_identity": identity,
            "canonical_concept_id": row["canonical_concept_id"],
            "semantic_class": row["semantic_class"],
            "mapping_state": row["canonical_mapping_state"],
            "assertions": 0,
            "records": set(),
            "families": set(),
            "years": set(),
            "gold": 0,
            "silver": 0,
            "bronze": 0,
            "rights_affirmative": 0,
            "rights_pending": 0,
            "rights_unknown": 0,
        })
        item["assertions"] += 1
        if row["counts_as_record_unique_cleaned_descriptor"] == "true":
            item["records"].add(row["effective_record_id"])
        item["families"].add(row["source_family_id"])
        if row["edition_year"]:
            item["years"].add(row["edition_year"])
        if row["evidence_tier"] in {"P1", "P2"}:
            item["gold"] += 1
        elif row["evidence_tier"] == "UNRESOLVED":
            item["silver"] += 1
        else:
            item["bronze"] += 1
        key = "rights_" + row["rights_state"].casefold()
        if key in item:
            item[key] += 1
    rows = []
    for identity, item in sorted(acc.items(), key=lambda pair: (-pair[1]["assertions"], pair[0])):
        rows.append({
            "cleaned_descriptor_identity": identity,
            "canonical_concept_id": item["canonical_concept_id"],
            "semantic_class": item["semantic_class"],
            "mapping_state": item["mapping_state"],
            "cleaned_assertion_support": item["assertions"],
            "effective_record_support": len(item["records"]),
            "source_family_support": len(item["families"]),
            "year_support": len(item["years"]),
            "gold_support": item["gold"],
            "silver_support": item["silver"],
            "bronze_support": item["bronze"],
            "rights_affirmative_support": item["rights_affirmative"],
            "rights_pending_support": item["rights_pending"],
            "rights_unknown_support": item["rights_unknown"],
        })
    bands = (
        ("1", 1, 1), ("2_TO_4", 2, 4), ("5_TO_19", 5, 19),
        ("20_TO_49", 20, 49), ("50_TO_99", 50, 99),
        ("100_PLUS", 100, 10**12),
    )
    support_rows = []
    for label, low, high in bands:
        selected = [row for row in rows if low <= int(row["cleaned_assertion_support"]) <= high]
        support_rows.append({
            "support_band": label,
            "minimum_support": low,
            "maximum_support": "UNBOUNDED" if high == 10**12 else high,
            "descriptor_count": len(selected),
            "cleaned_assertion_count": sum(int(row["cleaned_assertion_support"]) for row in selected),
            "record_unique_assertion_count": sum(int(row["effective_record_support"]) for row in selected),
        })
    return rows, support_rows


def pair_receipt(cleaned: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    record_items: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in cleaned:
        if row["counts_as_record_unique_cleaned_descriptor"] != "true":
            continue
        record_items[row["effective_record_id"]][row["cleaned_descriptor_identity"]] = row
    pair_acc: dict[tuple[str, str], dict[str, Any]] = {}
    total_events = 0
    for record_id, item_map in sorted(record_items.items()):
        identities = sorted(item_map)
        for left, right in itertools.combinations(identities, 2):
            total_events += 1
            row = item_map[left]
            item = pair_acc.setdefault((left, right), {
                "records": set(), "families": set(), "years": set(),
                "sample_consensus_records": set(),
            })
            item["records"].add(record_id)
            item["families"].add(row["source_family_id"])
            if row["edition_year"]:
                item["years"].add(row["edition_year"])

    # Consensus requires support from at least two distinct Zenodo panelists.
    zenodo_support: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for row in cleaned:
        if row["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset" and row["panelist_identity_sha256"]:
            zenodo_support[row["effective_record_id"]][row["cleaned_descriptor_identity"]].add(row["panelist_identity_sha256"])
    consensus_events = 0
    consensus_record_count = len(zenodo_support)
    for record_id, descriptor_support in sorted(zenodo_support.items()):
        consensus = sorted(key for key, panelists in descriptor_support.items() if len(panelists) >= 2)
        for left, right in itertools.combinations(consensus, 2):
            consensus_events += 1
            item = pair_acc.setdefault((left, right), {
                "records": set(), "families": set(), "years": set(),
                "sample_consensus_records": set(),
            })
            item["sample_consensus_records"].add(record_id)

    rows = []
    for (left, right), item in sorted(pair_acc.items()):
        rows.append({
            "cleaned_pair_id": stable_id("cleaned-pair", left + "\x1f" + right),
            "left_cleaned_descriptor_identity": left,
            "right_cleaned_descriptor_identity": right,
            "record_unique_pair_event_count": len(item["records"]),
            "effective_record_support": len(item["records"]),
            "year_support": len(item["years"]),
            "source_family_support": len(item["families"]),
            "zenodo_sample_consensus_pair_event_count": len(item["sample_consensus_records"]),
            "maximum_single_record_contribution": 1 if item["records"] else 0,
            "pair_counted_as_source_assertion": "false",
        })
    metrics = {
        "pair_event_count": total_events,
        "unique_pair_count": sum(bool(item["records"]) for item in pair_acc.values()),
        "sample_consensus_pair_event_count": consensus_events,
        "zenodo_sample_consensus_record_count": consensus_record_count,
        "pair_with_multi_record_support_count": sum(len(item["records"]) >= 2 for item in pair_acc.values()),
        "pair_with_multi_year_support_count": sum(len(item["years"]) >= 2 for item in pair_acc.values()),
        "pair_with_multi_family_support_count": sum(len(item["families"]) >= 2 for item in pair_acc.values()),
        "maximum_single_record_pair_contribution": 1 if total_events else 0,
    }
    return rows, metrics


def ontology_gaps(normalization: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for row in normalization:
        if row["mapping_state"] != "ONTOLOGY_CANDIDATE":
            continue
        lexical_hash = row["cleaned_lexical_form_sha256"]
        rows.append({
            "ontology_gap_id": stable_id("ontology-gap", lexical_hash),
            "candidate_preferred_label_or_restricted_pointer": f"hash:sha256:{lexical_hash}",
            "source_native_forms_or_restricted_pointers": f"hash-set:sha256:{lexical_hash}",
            "language": row["source_language"],
            "semantic_class": row["semantic_class"],
            "definition_evidence": "NA_NO_GOVERNED_DEFINITION_EVIDENCE_IN_BATCH3;LEXICAL_SUPPORT_ONLY",
            "source_family_count": row["source_family_count"],
            "source_family_ids": row["source_family_ids"],
            "effective_record_support": row["effective_record_support"],
            "year_count": row["year_count"],
            "years": row["years"],
            "nearest_existing_concepts": "NA_SEMANTIC_SIMILARITY_NOT_RUN_NO_FORCED_MERGE",
            "reason_not_merged": "VALID_PROFESSIONAL_SENSORY_FORM_HAS_NO_EXACT_APPROVED_ALIAS_OR_MORPHOLOGICAL_MATCH",
            "review_requirement": "MACHINE_PROVISIONAL_REVIEW",
            "canonical_ontology_modified": "false",
        })
    rows.sort(key=lambda row: (-int(row["effective_record_support"]), row["ontology_gap_id"]))
    return rows


def review_clusters(
    normalization: list[dict[str, str]], cleaned: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    valid = [row for row in normalization if row["semantic_class"] in VALID_CLASSES]
    valid.sort(key=lambda row: (-int(row["assertion_support"]), row["cleaned_lexical_form_sha256"]))
    total = sum(int(row["assertion_support"]) for row in valid)
    required: dict[str, set[str]] = defaultdict(set)
    running = 0
    for index, row in enumerate(valid):
        lexical_hash = row["cleaned_lexical_form_sha256"]
        support = int(row["assertion_support"])
        if support >= 20:
            required[lexical_hash].add("SUPPORT_AT_LEAST_20")
        if index < 200:
            required[lexical_hash].add("CURRENT_TOP_200")
        if running < total * 0.80:
            required[lexical_hash].add("TOP_COVERAGE_80_PERCENT")
        running += support
        if row["mapping_state"] == "AMBIGUOUS_MAPPING" and int(row["gold_support"]) > 0:
            required[lexical_hash].add("AMBIGUOUS_GOLD")
    if len(required) > 300:
        raise RuntimeError(f"required active cleaning clusters exceed 300: {len(required)}")
    by_hash = {row["cleaned_lexical_form_sha256"]: row for row in normalization}
    result = []
    for lexical_hash, reasons in required.items():
        row = by_hash[lexical_hash]
        result.append({
            "review_cluster_id": stable_id("cleaning-cluster", lexical_hash),
            "cleaned_lexical_form_or_restricted_pointer": f"hash:sha256:{lexical_hash}",
            "source_language": row["source_language"],
            "semantic_class": row["semantic_class"],
            "mapping_state": row["mapping_state"],
            "canonical_concept_id": row["canonical_concept_id"],
            "assertion_support": row["assertion_support"],
            "effective_record_support": row["effective_record_support"],
            "source_family_count": row["source_family_count"],
            "year_count": row["year_count"],
            "gold_support": row["gold_support"],
            "silver_support": row["silver_support"],
            "selection_reasons": sorted(reasons),
            "codex_decision_type": row["decision_method"],
            "review_state": "MACHINE_PROVISIONAL_REVIEW" if row["decision_method"] == "MACHINE_PROVISIONAL_REVIEW" else "AUTOMATED_SAFE_RULE",
            "human_reviewed": "false",
            "expert_adjudicated": "false",
        })
    result.sort(key=lambda row: (-int(row["assertion_support"]), row["review_cluster_id"]))
    return result


def wilson(successes: int, total: int) -> tuple[float, float, float]:
    if total == 0:
        return 0.0, 0.0, 0.0
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return p, max(0.0, center - margin), min(1.0, center + margin)


def audit_metrics(audit: list[dict[str, str]]) -> dict[str, Any]:
    dimensions = {
        "valid_atomic_rate": "valid_atomic",
        "valid_broad_rate": "valid_broad",
        "compound_rate": "compound",
        "over_segmentation_rate": "over_segmentation",
        "under_segmentation_rate": "under_segmentation",
        "non_descriptor_leakage_rate": "non_descriptor_leakage",
        "strict_broad_misclassification_rate": "strict_broad_misclassification",
        "publication_duplicate_rate": "publication_duplicate",
    }
    strata = {"ALL_AUDITED": audit}
    for name in sorted({row["audit_stratum"] for row in audit}):
        strata[name] = [row for row in audit if row["audit_stratum"] == name]
    results = []
    for stratum, rows in strata.items():
        metric = {"audit_stratum": stratum, "sample_count": len(rows), "confidence_method": "WILSON_SCORE_95_PERCENT"}
        for output, field in dimensions.items():
            successes = sum(row[field] == "true" for row in rows)
            estimate, lower, upper = wilson(successes, len(rows))
            metric[output] = round(estimate, 6)
            metric[output + "_ci95_lower"] = round(lower, 6)
            metric[output + "_ci95_upper"] = round(upper, 6)
        results.append(metric)
    return {
        "contract_version": "source-stratified-semantic-audit-metrics.v1",
        "generated_at": GENERATED_AT,
        "audit_is_machine_semantic_qa_not_human_review": True,
        "sample_estimates_not_used_for_destructive_deletion": True,
        "strata": results,
    }


def source_family_balance(
    decisions: list[dict[str, str]], cleaned: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    families = sorted({row["source_family_id"] for row in decisions if row["counts_as_assertion"] == "true"})
    total_cleaned = len(cleaned)
    rows = []
    for family in families:
        source = [row for row in decisions if row["source_family_id"] == family and row["counts_as_assertion"] == "true"]
        family_cleaned = [row for row in cleaned if row["source_family_id"] == family]
        rows.append({
            "corpus_surface": "FROZEN_20K_CLEANED",
            "source_family_id": family,
            "mechanically_deinflated_source_assertion_count": len(source),
            "semantically_valid_source_assertion_count": sum(row["semantic_cleaning_disposition"] == "SEMANTICALLY_VALID" for row in source),
            "cleaned_descriptor_assertion_count": len(family_cleaned),
            "record_unique_cleaned_assertion_count": sum(row["counts_as_record_unique_cleaned_descriptor"] == "true" for row in family_cleaned),
            "cleaned_assertion_share": f"{len(family_cleaned) / total_cleaned:.6f}" if total_cleaned else "0.000000",
            "rights_affirmative_count": sum(row["rights_state"] == "AFFIRMATIVE" for row in family_cleaned),
            "rights_pending_count": sum(row["rights_state"] == "PENDING" for row in family_cleaned),
            "rights_unknown_count": sum(row["rights_state"] == "UNKNOWN" for row in family_cleaned),
        })
    return rows


def extension_progress() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    manifest_path = EXTENSION / "POST20K_EXTENSION_MANIFEST.json"
    default = {
        "run": False,
        "net_new_raw_assertion_count": 0,
        "net_new_deinflated_assertion_count": 0,
        "net_new_record_unique_count": 0,
        "net_new_effective_record_count": 0,
        "total_candidate_count": 20003,
        "checkpoint_30000_reached": False,
        "new_coe_assertion_count": 0,
        "new_non_coe_assertion_count": 0,
        "new_non_coe_positive_family_count": 0,
        "non_coe_discovery_effort_rate": 0.0,
        "cursor_start": "archive-page=12;detail-index=10;url=https://farmdirectory.cupofexcellence.org/listing/9-liquidambar-honduras-2026-parainema-catracha/",
        "cursor_end": "NA_EXTENSION_NOT_RUN",
        "coe_route_exhausted": False,
        "coe_continuation_blocked": False,
        "status": "POST20K_EXTENSION_NOT_RUN",
    }
    if manifest_path.is_file():
        observed = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key in default:
            if key in observed:
                default[key] = observed[key]
    rows = [{"metric": key.upper(), "observed_value": value} for key, value in default.items()]
    return rows, default


def metrics(
    base: list[dict[str, str]], decisions: list[dict[str, str]],
    normalization: list[dict[str, str]], cleaned: list[dict[str, Any]],
    pair_metrics: dict[str, int], audit_document: dict[str, Any],
    review: list[dict[str, Any]], entity: list[dict[str, str]],
    duplicates: list[dict[str, str]], extension: dict[str, Any],
) -> dict[str, Any]:
    deinf = [row for row in decisions if row["counts_as_assertion"] == "true"]
    valid_source = [row for row in deinf if row["semantic_cleaning_disposition"] == "SEMANTICALLY_VALID"]
    unresolved_source = [row for row in deinf if row["semantic_cleaning_disposition"] == "SEMANTICALLY_UNRESOLVED"]
    non_descriptor = [row for row in deinf if row["semantic_cleaning_disposition"] == "NON_DESCRIPTOR"]
    classes = Counter()
    maps = Counter()
    for row in deinf:
        classes.update(row["semantic_classes"].split("|"))
        maps.update(row["mapping_states"].split("|"))
    cleaned_classes = Counter(row["semantic_class"] for row in cleaned)
    all_audit = next(item for item in audit_document["strata"] if item["audit_stratum"] == "ALL_AUDITED")
    source_native_forms = {row["source_native_form_sha256"] for row in deinf}
    valid_forms = {row["cleaned_lexical_form_sha256"] for row in cleaned}
    canonical_concepts = {row["canonical_concept_id"] for row in cleaned if row["canonical_concept_id"]}
    ontology_candidates = {row["cleaned_lexical_form_sha256"] for row in normalization if row["mapping_state"] == "ONTOLOGY_CANDIDATE"}
    unresolved_forms = {row["cleaned_lexical_form_sha256"] for row in normalization if row["mapping_state"] in {"AMBIGUOUS_MAPPING", "COMPOUND_MAPPING_REVIEW_REQUIRED", "UNRESOLVED"}}
    by_family = Counter(row["source_family_id"] for row in cleaned)
    rights = Counter(row["rights_state"] for row in cleaned)
    return {
        "snapshot_raw_candidate_assertion_count": len(base),
        "snapshot_mechanically_deinflated_assertion_count": len(deinf),
        "semantically_valid_candidate_assertion_count": len(valid_source),
        "semantically_unresolved_assertion_count": len(unresolved_source),
        "non_descriptor_removal_count": len(non_descriptor),
        "publication_duplicate_removal_count": sum(int(row["suppressed_assertion_count"]) for row in duplicates),
        "record_unique_cleaned_assertion_count": sum(row["counts_as_record_unique_cleaned_descriptor"] == "true" for row in cleaned),
        "semantic_retention_rate": round(len(valid_source) / len(deinf), 6),
        "source_native_form_count": len(source_native_forms),
        "first_pass_provisional_form_count": len({row["normalized_descriptor_candidate_id"] for row in base if row["counts_as_assertion"] == "true" and row["normalized_descriptor_candidate_id"]}),
        "cleaned_lexical_form_count": len(valid_forms),
        "canonical_mapped_concept_count": len(canonical_concepts),
        "ontology_candidate_count": len(ontology_candidates),
        "unresolved_form_count": len(unresolved_forms),
        "alias_compression_count": maps["AUTO_APPROVED_ALIAS"] + maps["AUTO_MORPHOLOGICAL"],
        "compound_split_count": sum(row["segmentation_decision"] in {"SAFE_LIST_SPLIT", "MULTIPLE_BROAD_ATTRIBUTES", "HEAD_PLUS_MODIFIER"} for row in deinf),
        "compound_preserved_count": sum(row["segmentation_decision"] == "KEEP_AS_ESTABLISHED_COMPOUND" for row in deinf),
        "lexical_compression_ratio": round(len(valid_forms) / len(source_native_forms), 6),
        "auto_exact_canonical_count": maps["AUTO_EXACT_CANONICAL"],
        "auto_approved_alias_count": maps["AUTO_APPROVED_ALIAS"],
        "auto_morphological_count": maps["AUTO_MORPHOLOGICAL"],
        "provisional_semantic_mapping_count": maps["PROVISIONAL_SEMANTIC_MAPPING"],
        "ontology_candidate_mapping_count": maps["ONTOLOGY_CANDIDATE"],
        "ambiguous_mapping_count": maps["AMBIGUOUS_MAPPING"],
        "non_descriptor_mapping_count": maps["NON_DESCRIPTOR"],
        "cleaned_strict_flavor_assertion_count": cleaned_classes["STRICT_FLAVOR"],
        "cleaned_broad_sensory_assertion_count": cleaned_classes["BROAD_SENSORY"],
        "cleaned_defect_assertion_count": cleaned_classes["DEFECT_OR_NEGATIVE_SENSORY"],
        "cleaned_quality_evaluation_count": classes["QUALITY_EVALUATION"],
        "cleaned_modifier_only_count": classes["INTENSITY_OR_QUALITY_MODIFIER"],
        "cleaned_composite_unresolved_count": classes["COMPOSITE_DESCRIPTOR"],
        "coe_cross_domain_match_candidate_count": len(entity),
        "coe_exact_match_count": sum(row["match_state"] == "EXACT_SAME_EFFECTIVE_RECORD" for row in entity),
        "coe_high_confidence_match_count": sum(row["match_state"] == "HIGH_CONFIDENCE_SAME_EFFECTIVE_RECORD" for row in entity),
        "coe_possible_match_review_count": sum(row["match_state"] == "POSSIBLE_SAME_EFFECTIVE_RECORD_REVIEW_REQUIRED" for row in entity),
        "coe_publication_duplicate_assertion_loss_count": sum(int(row["suppressed_assertion_count"]) for row in duplicates),
        "zenodo_panelist_sample_observation_count": len({row["panelist_sample_observation_sha256"] for row in decisions if row["panelist_sample_observation_sha256"]}),
        "zenodo_effective_sample_count": len({row["effective_record_id"] for row in decisions if row["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset" and row["counts_as_assertion"] == "true"}),
        "zenodo_sample_consensus_record_count": pair_metrics["zenodo_sample_consensus_record_count"],
        "semantic_audit_sample_count": all_audit["sample_count"],
        "semantic_audit_valid_atomic_rate": all_audit["valid_atomic_rate"],
        "semantic_audit_valid_broad_rate": all_audit["valid_broad_rate"],
        "semantic_audit_compound_rate": all_audit["compound_rate"],
        "semantic_audit_oversegmentation_rate": all_audit["over_segmentation_rate"],
        "semantic_audit_undersegmentation_rate": all_audit["under_segmentation_rate"],
        "semantic_audit_non_descriptor_leak_rate": all_audit["non_descriptor_leakage_rate"],
        "semantic_audit_classification_error_rate": all_audit["strict_broad_misclassification_rate"],
        "cleaned_source_family_count": len(by_family),
        "cleaned_coe_assertion_count": by_family["family.ace_cup_of_excellence"],
        "cleaned_coe_share": round(by_family["family.ace_cup_of_excellence"] / len(cleaned), 6),
        "cleaned_zenodo_assertion_count": by_family["family.zenodo_golovinsky_q_grader_dataset"],
        "cleaned_non_coe_assertion_count": len(cleaned) - by_family["family.ace_cup_of_excellence"],
        **pair_metrics,
        "post20k_extension": extension,
        "rights_affirmative_cleaned_assertion_count": rights["AFFIRMATIVE"],
        "rights_pending_cleaned_assertion_count": rights["PENDING"],
        "rights_unknown_cleaned_assertion_count": rights["UNKNOWN"],
        "model_eligible_assertion_count": 0,
        "human_reviewed_normalized_form_count": 0,
        "expert_adjudicated_form_count": 0,
        "active_review_cluster_count": len(review),
    }


def update_manifest(batch3_metrics: dict[str, Any], snapshot: dict[str, Any]) -> None:
    manifest_path = CURRENT / "CURRENT_DATA_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    extension = batch3_metrics["post20k_extension"]
    if extension["checkpoint_30000_reached"]:
        status = "CLEANING_PASS_30K_CANDIDATE_CHECKPOINT_REACHED"
    elif extension["run"] and extension["new_non_coe_positive_family_count"] < 3:
        status = "CLEANING_PASS_NON_COE_DIVERSIFICATION_GAPS"
    elif extension["run"]:
        status = "CLEANING_PASS_POST20K_EXTENSION_CHECKPOINT"
    else:
        status = "CLEANING_PARTIAL_SEMANTIC_REVIEW_REQUIRED"
    manifest.update({
        "phase_status": status,
        "candidate_20k_snapshot_version": SNAPSHOT_VERSION,
        "candidate_20k_snapshot_created": True,
        "candidate_20k_snapshot_content_sha256": snapshot["snapshot_content_sha256"],
        "batch3_generator_version": GENERATOR_VERSION,
        "semantic_cleaning_disposition_completeness_rate": 1.0,
        "normalization_disposition_completeness_rate": 1.0,
        "batch3_cleaning_metrics": batch3_metrics,
        "schema_changed": False,
        "new_migration_count": 0,
        "model_training_run": False,
        "model_weight_file_count": 0,
        "ml_baseline_run": False,
        "ranking_model_trained": False,
        "deep_learning_model_run": False,
        "embedding_model_trained": False,
        "cross_encoder_run": False,
        "final_data_decision": "FROZEN_20K_CLEANED_POST20K_EXTENSION_ISOLATED_MODEL_WORK_REMAINS_BLOCKED",
    })
    excluded = {"CURRENT_DATA_MANIFEST.json", "SHA256SUMS"}
    manifest["files"] = []
    for path in sorted(CURRENT.iterdir()):
        if path.is_file() and path.name not in excluded:
            manifest["files"].append({
                "path": path.name,
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
                "data_row_count": data_rows(path),
            })
    write_json("CURRENT_DATA_MANIFEST.json", manifest)
    checksum_paths = sorted(path for path in CURRENT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (CURRENT / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )


def main() -> int:
    required = [DECISION, SEGMENTATION, NORMALIZATION, ENTITY, DUPLICATE, AUDIT, STAGING_MANIFEST]
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing Batch 3 public-safe staging inputs: {missing}")
    base = read_tsv(CURRENT / "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    decisions = read_tsv(DECISION)
    normalization = read_tsv(NORMALIZATION)
    entity = read_tsv(ENTITY)
    duplicates = read_tsv(DUPLICATE)
    audit = read_tsv(AUDIT)
    if len(base) != len(decisions):
        raise RuntimeError("frozen ledger and cleaning decision completeness mismatch")

    copy_public_sidecars()
    snapshot = snapshot_manifest(base)
    write_json("CANDIDATE_20K_SNAPSHOT_MANIFEST.json", snapshot)
    cleaned = cleaned_ledger(base, decisions)
    write_tsv("CLEANED_DESCRIPTOR_ASSERTION_LEDGER.tsv", list(cleaned[0]), cleaned)
    distribution, support = descriptor_distributions(cleaned)
    write_tsv("CLEANED_DESCRIPTOR_DISTRIBUTION.tsv", list(distribution[0]), distribution)
    write_tsv("CLEANED_DESCRIPTOR_SUPPORT_BANDS.tsv", list(support[0]), support)
    pairs, pair_stats = pair_receipt(cleaned)
    write_tsv("CLEANED_PAIR_EVENT_RECEIPT.tsv", list(pairs[0]), pairs)
    gaps = ontology_gaps(normalization)
    write_tsv("ONTOLOGY_GAP_REGISTER.tsv", list(gaps[0]), gaps)
    review = review_clusters(normalization, cleaned)
    write_tsv("REVIEW_CLUSTER_QUEUE.tsv", list(review[0]), review)
    audit_document = audit_metrics(audit)
    write_json("SEMANTIC_AUDIT_METRICS.json", audit_document)
    balance = source_family_balance(decisions, cleaned)
    write_tsv("SOURCE_FAMILY_BALANCE.tsv", list(balance[0]), balance)
    progress_rows, extension = extension_progress()
    write_tsv("POST20K_EXTENSION_PROGRESS.tsv", list(progress_rows[0]), progress_rows)
    batch3_metrics = metrics(
        base, decisions, normalization, cleaned, pair_stats, audit_document,
        review, entity, duplicates, extension,
    )
    update_manifest(batch3_metrics, snapshot)
    print(
        "BATCH3_PUBLIC_CLEANING_PASS "
        f"source_valid={batch3_metrics['semantically_valid_candidate_assertion_count']} "
        f"cleaned={len(cleaned)} forms={batch3_metrics['cleaned_lexical_form_count']} "
        f"pairs={pair_stats['pair_event_count']} clusters={len(review)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
