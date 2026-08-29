#!/usr/bin/env python3
"""Build the restricted-to-public Batch 4 semantic-cleaning bridge.

The program is the only Batch 4 component that reads source-native text.  Its
outputs contain identifiers, hashes, locators, classifications, rights states,
and restricted pointers only.  The committed sidecars are sufficient for the
public generator and for byte-identical offline reproduction.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
OUT = ROOT / "db" / "data" / "candidate-cleaning-v2-staging"
V1_BUILDER = ROOT / "db" / "scripts" / "build-batch3-cleaning-staging.py"
DEFAULT_BATCH2 = Path("/private/tmp/round3l-acquisition/professional_descriptor_batch2")
DEFAULT_ROUND3M = Path("/private/tmp/coffee-flavor-round3m-restricted")
DEFAULT_EXTENSION = Path(
    "/private/tmp/coffee-flavor-round3m-post20k/post20k_extension"
)

SNAPSHOT_VERSION = "professional-descriptor-candidate-v1-30k"
CLEANER_CONTRACT_VERSION = "batch4.semantic-cleaner.v2"
BUILDER_VERSION = "batch4.restricted-public-bridge.v1"
GENERATED_AT = "2026-08-29T00:00:00Z"

VALID_ATOM_CLASSES = {
    "STRICT_FLAVOR",
    "BROAD_SENSORY",
    "DEFECT_OR_NEGATIVE_SENSORY",
    "COMPOSITE_DESCRIPTOR",
}

MAPPING_STATES = {
    "EXISTING_CANONICAL_EXACT",
    "EXISTING_CANONICAL_ALIAS",
    "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT",
    "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM",
    "EXISTING_CANONICAL_PARENT_ONLY",
    "MODIFIER_OF_EXISTING_CONCEPT",
    "COMPOUND_OF_EXISTING_CONCEPTS",
    "GENUINE_ONTOLOGY_CANDIDATE",
    "QUALITY_OR_STRUCTURE_ATTRIBUTE",
    "DEFECT_CONCEPT_CANDIDATE",
    "AMBIGUOUS_CONCEPT_BOUNDARY",
    "CROSS_LANGUAGE_REVIEW_REQUIRED",
    "NON_DESCRIPTOR",
    "UNRESOLVED",
}


def load_v1():
    spec = importlib.util.spec_from_file_location("batch3_cleaner", V1_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Batch 3 cleaner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V1 = load_v1()


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


def write_tsv(path: Path, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    names = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=names,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: scalar(row.get(name, "")) for name in names})


def disposition_for(cleaned: list[tuple[str, str]], segmentation: str) -> str:
    classes = {klass for _, klass in cleaned}
    if segmentation in {"SAFE_LIST_SPLIT", "HEAD_PLUS_MODIFIER", "MULTIPLE_BROAD_ATTRIBUTES"}:
        return "VALID_COMPOUND_SPLIT"
    if segmentation == "KEEP_AS_ESTABLISHED_COMPOUND":
        return "VALID_COMPOUND_PRESERVED"
    if classes == {"STRICT_FLAVOR"}:
        return "VALID_STRICT_FLAVOR"
    if classes == {"BROAD_SENSORY"}:
        return "VALID_BROAD_SENSORY"
    if classes == {"DEFECT_OR_NEGATIVE_SENSORY"}:
        return "VALID_DEFECT_OR_NEGATIVE_SENSORY"
    if classes == {"QUALITY_EVALUATION"}:
        return "QUALITY_EVALUATION"
    if classes == {"INTENSITY_OR_QUALITY_MODIFIER"}:
        return "MODIFIER_ONLY"
    if classes == {"PROCESS_OR_ORIGIN_METADATA"}:
        return "PROCESS_OR_ORIGIN_METADATA"
    if classes == {"NON_DESCRIPTOR"}:
        return "NON_DESCRIPTOR"
    if "COMPOSITE_DESCRIPTOR" in classes:
        return "AMBIGUOUS_SEMANTIC_OUTPUT"
    if "SEMANTICALLY_UNRESOLVED" in classes:
        return "UNRESOLVED"
    if classes & VALID_ATOM_CLASSES:
        return "VALID_COMPOUND_SPLIT"
    return "UNRESOLVED"


def atom_disposition(klass: str) -> str:
    return {
        "STRICT_FLAVOR": "VALID_STRICT_FLAVOR",
        "BROAD_SENSORY": "VALID_BROAD_SENSORY",
        "DEFECT_OR_NEGATIVE_SENSORY": "VALID_DEFECT_OR_NEGATIVE_SENSORY",
        "QUALITY_EVALUATION": "QUALITY_EVALUATION",
        "INTENSITY_OR_QUALITY_MODIFIER": "MODIFIER_ONLY",
        "PROCESS_OR_ORIGIN_METADATA": "PROCESS_OR_ORIGIN_METADATA",
        "NON_DESCRIPTOR": "NON_DESCRIPTOR",
        "COMPOSITE_DESCRIPTOR": "VALID_COMPOUND_PRESERVED",
        "SEMANTICALLY_UNRESOLVED": "UNRESOLVED",
    }.get(klass, "UNRESOLVED")


def component_concepts(value: str, by_label: Mapping[str, str]) -> list[str]:
    components: set[str] = set()
    for part in value.split():
        if part in by_label:
            components.add(by_label[part])
        elif part in V1.APPROVED_ALIASES:
            components.add(V1.APPROVED_ALIASES[part])
        else:
            for candidate in V1.singular_candidates(part):
                if candidate in by_label:
                    components.add(by_label[candidate])
    return sorted(components)


def v2_mapping(
    value: str,
    klass: str,
    source_language: str,
    by_label: Mapping[str, str],
) -> tuple[str, str, str, str, list[str]]:
    v1_state, concept_id, _, v1_confidence = V1.map_concept(value, klass, by_label)
    components = component_concepts(value, by_label)
    if klass in {"NON_DESCRIPTOR", "PROCESS_OR_ORIGIN_METADATA"}:
        result = ("NON_DESCRIPTOR", "", "NO_GOVERNED_AUTHORITY", "1.000000", components)
    elif klass == "INTENSITY_OR_QUALITY_MODIFIER":
        result = ("MODIFIER_OF_EXISTING_CONCEPT", "", "NO_GOVERNED_AUTHORITY", "0.900000", components)
    elif klass in {"QUALITY_EVALUATION"}:
        result = ("QUALITY_OR_STRUCTURE_ATTRIBUTE", "", "NO_GOVERNED_AUTHORITY", "0.950000", components)
    elif klass == "SEMANTICALLY_UNRESOLVED":
        result = ("UNRESOLVED", "", "NO_GOVERNED_AUTHORITY", "0.000000", components)
    elif source_language and source_language != "en" and not concept_id:
        result = ("CROSS_LANGUAGE_REVIEW_REQUIRED", "", "NO_GOVERNED_AUTHORITY", "0.000000", components)
    elif v1_state == "AUTO_EXACT_CANONICAL":
        result = ("EXISTING_CANONICAL_EXACT", concept_id, "MACHINE_GOVERNED_HIGH_CONFIDENCE", "1.000000", components)
    elif v1_state == "AUTO_APPROVED_ALIAS":
        result = ("EXISTING_CANONICAL_ALIAS", concept_id, "MACHINE_GOVERNED_HIGH_CONFIDENCE", "0.990000", components)
    elif v1_state == "AUTO_MORPHOLOGICAL":
        result = ("EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT", concept_id, "MACHINE_GOVERNED_HIGH_CONFIDENCE", "0.980000", components)
    elif value in V1.AMBIGUOUS:
        result = ("AMBIGUOUS_CONCEPT_BOUNDARY", "", "NO_GOVERNED_AUTHORITY", "0.000000", components)
    elif len(components) >= 2 or klass == "COMPOSITE_DESCRIPTOR":
        result = ("COMPOUND_OF_EXISTING_CONCEPTS", "", "NO_GOVERNED_AUTHORITY", "0.700000", components)
    elif klass == "DEFECT_OR_NEGATIVE_SENSORY":
        result = ("DEFECT_CONCEPT_CANDIDATE", "", "NO_GOVERNED_AUTHORITY", "0.700000", components)
    elif klass == "BROAD_SENSORY":
        result = ("QUALITY_OR_STRUCTURE_ATTRIBUTE", "", "NO_GOVERNED_AUTHORITY", "0.700000", components)
    else:
        containing = [key for label, key in by_label.items() if label in value or value in label]
        if containing:
            result = (
                "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM",
                sorted(containing)[0],
                "NO_GOVERNED_AUTHORITY",
                "0.700000",
                components,
            )
        else:
            result = ("GENUINE_ONTOLOGY_CANDIDATE", "", "NO_GOVERNED_AUTHORITY", v1_confidence, components)
    if result[0] not in MAPPING_STATES:
        raise RuntimeError(f"unapproved V2 mapping state: {result[0]}")
    return result


def cluster_id_for(
    lexical_hash: str,
    mapping_state: str,
    concept_id: str,
    components: list[str],
) -> str:
    if mapping_state in {
        "EXISTING_CANONICAL_EXACT",
        "EXISTING_CANONICAL_ALIAS",
        "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT",
        "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM",
        "EXISTING_CANONICAL_PARENT_ONLY",
    } and concept_id:
        material = "canonical\x1f" + concept_id
    elif mapping_state == "COMPOUND_OF_EXISTING_CONCEPTS" and components:
        material = "compound\x1f" + "\x1f".join(components)
    else:
        material = "form\x1f" + lexical_hash
    return stable_id("concept-cluster", material)


def base_restricted_text(
    batch2_root: Path,
    round3m_root: Path,
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    return V1.restricted_text_by_assertion(batch2_root, round3m_root)


def public_base_row(
    row: Mapping[str, str],
    restricted: Mapping[str, str] | None,
) -> dict[str, str]:
    rights_basis = restricted.get("rights_basis", "") if restricted else ""
    collection = restricted.get("collection_tier", "") if restricted else ""
    if not collection:
        collection = "GOLD" if row["evidence_tier"] in {"P1", "P2"} else "SILVER"
    return {
        "corpus_segment": "FROZEN_20K",
        "descriptor_assertion_id": row["descriptor_assertion_id"],
        "source_family_id": row["source_family_id"],
        "publisher_id": stable_id("publisher", row["source_family_id"]),
        "source_route_id": row["source_route_id"],
        "source_artifact_id": row["source_artifact_id"],
        "source_artifact_sha256": row["source_file_sha256"],
        "source_locator": row["source_locator"],
        "effective_record_id": row["effective_record_id"],
        "coffee_identity_id": row["coffee_identity_id"],
        "year_id": f"year.{row['edition_year']}" if row["edition_year"] else "year.unreported",
        "preparation_service_id": row["preparation_service_id"],
        "source_language": row["source_language"],
        "source_field_label_sha256": sha256_text(row["source_field_label"]),
        "raw_field_text_sha256": row["source_field_text_sha256"],
        "atomic_source_text_sha256": row["atomic_source_text_sha256"],
        "source_native_form_id": f"source-form:{row['atomic_source_text_sha256'][:24]}",
        "restricted_source_pointer": row["raw_source_text_or_restricted_pointer"],
        "original_descriptor_class": row["descriptor_class"],
        "evidence_tier": row["evidence_tier"],
        "collection_tier": collection,
        "provenance_state": row["provenance_state"],
        "rights_state": row["rights_state"],
        "rights_basis": rights_basis or "UNRESOLVED_RIGHTS_BASIS",
        "publication_layer": row["publication_layer"],
        "judge_observation_id_sha256": restricted.get("judge_observation_id_sha256", "") if restricted else "",
        "duplicate_group_id": row["duplicate_group_id"],
        "mirror_group_id": row["mirror_group_id"],
        "counts_as_record_unique_descriptor": row["counts_as_record_unique_descriptor"],
    }


def public_extension_row(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "corpus_segment": "POST20K_EXTENSION",
        "descriptor_assertion_id": row["descriptor_assertion_id"],
        "source_family_id": row["source_family_id"],
        "publisher_id": stable_id("publisher", row["source_family_id"]),
        "source_route_id": row["source_route_id"],
        "source_artifact_id": stable_id("source-artifact", row["source_artifact_sha256"]),
        "source_artifact_sha256": row["source_artifact_sha256"],
        "source_locator": row["source_locator"],
        "effective_record_id": row["effective_record_id"],
        "coffee_identity_id": row["coffee_identity_id"],
        "year_id": f"year.{row['edition_year']}" if row["edition_year"] else "year.unreported",
        "preparation_service_id": row["preparation_service"],
        "source_language": row["source_language"],
        "source_field_label_sha256": sha256_text(row["source_field_label"]),
        "raw_field_text_sha256": row["raw_field_text_sha256"],
        "atomic_source_text_sha256": row["atomic_source_text_sha256"],
        "source_native_form_id": f"source-form:{row['source_native_form_sha256'][:24]}",
        "restricted_source_pointer": f"restricted://post20k_extension/assertions/{row['descriptor_assertion_id']}",
        "original_descriptor_class": row["descriptor_class"],
        "evidence_tier": row["evidence_tier"],
        "collection_tier": row["collection_tier"],
        "provenance_state": row["provenance_state"],
        "rights_state": row["rights_state"],
        "rights_basis": row["rights_basis"],
        "publication_layer": row["publication_layer"],
        "judge_observation_id_sha256": row["judge_observation_id_sha256"],
        "duplicate_group_id": "",
        "mirror_group_id": "",
        "counts_as_record_unique_descriptor": row["counts_as_record_unique_descriptor"],
    }


def rights_terms(row: Mapping[str, str]) -> dict[str, str]:
    basis = row["rights_basis"]
    if "CC_BY_NC_4_0" in basis:
        terms_id = "rights.cc-by-nc-4.0"
        version = "4.0"
        locator = "https://creativecommons.org/licenses/by-nc/4.0/"
        attribution = "REQUIRED"
        noncommercial = "REQUIRED"
    elif "CC_BY_4_0" in basis or "CC_BY_FRONTIERS_ARTICLE" in basis:
        terms_id = "rights.cc-by-4.0"
        version = "4.0"
        locator = "https://creativecommons.org/licenses/by/4.0/"
        attribution = "REQUIRED"
        noncommercial = "NOT_APPLICABLE"
    else:
        terms_id = "rights.unresolved-source-terms"
        version = "UNRESOLVED"
        locator = row["source_locator"]
        attribution = "UNKNOWN"
        noncommercial = "UNKNOWN"
    return {
        "terms_document_id": terms_id,
        "terms_version": version,
        "terms_url_or_locator": locator,
        "terms_retrieved_at": GENERATED_AT,
        "terms_document_sha256_or_state": (
            sha256_text(terms_id + "\x1f" + version + "\x1f" + locator)
            if version != "UNRESOLVED" else "UNRESOLVED"
        ),
        "attribution_requirement": attribution,
        "share_alike_requirement": "NOT_APPLICABLE" if version == "4.0" else "UNKNOWN",
        "noncommercial_restriction": noncommercial,
        "database_rights_note": "NO_SEPARATE_DATABASE_RIGHTS_CONCLUSION",
        "contract_note": "NO_SEPARATE_CONTRACT_REVIEW_PERFORMED",
        "legal_review_performed": "false",
        "legal_review_actor": "",
    }


def identity_rows() -> list[dict[str, str]]:
    prior = read_tsv(CURRENT / "COE_ENTITY_RESOLUTION.tsv")
    result: list[dict[str, str]] = []
    for row in prior:
        year_exact = row["old_domain_year"] == row["new_domain_year"] and bool(row["old_domain_year"])
        descriptor_exact = (
            bool(row["old_domain_descriptor_field_hash_bundle"])
            and row["old_domain_descriptor_field_hash_bundle"]
            == row["new_domain_descriptor_field_hash_bundle"]
        )
        name_score = float(row["match_score"] or 0)
        if year_exact and descriptor_exact and name_score >= 0.95:
            state = "EXACT_SAME_RECORD"
        elif year_exact and descriptor_exact and name_score >= 0.80:
            state = "HIGH_CONFIDENCE_SAME_RECORD"
        elif year_exact and name_score >= 0.65:
            state = "POSSIBLE_SAME_RECORD"
        elif row["new_domain_source_url"] and not year_exact:
            state = "DISTINCT_RECORD"
        elif row["new_domain_source_url"]:
            state = "INSUFFICIENT_EVIDENCE"
        else:
            state = "NO_CANDIDATE"
        result.append({
            "entity_resolution_id": row["entity_resolution_id"],
            "old_domain_source_locator": row["old_domain_source_url"],
            "new_domain_source_locator": row["new_domain_source_url"],
            "old_domain_record_id": row["old_domain_record_id"],
            "new_domain_effective_record_id": row["new_domain_effective_record_id"],
            "old_domain_year_id": f"year.{row['old_domain_year']}" if row["old_domain_year"] else "year.unreported",
            "new_domain_year_id": f"year.{row['new_domain_year']}" if row["new_domain_year"] else "year.unreported",
            "old_domain_name_sha256": row["old_domain_name_sha256"],
            "old_domain_descriptor_bundle_sha256": row["old_domain_descriptor_field_hash_bundle"],
            "new_domain_descriptor_bundle_sha256": row["new_domain_descriptor_field_hash_bundle"],
            "name_year_slug_match_score": row["match_score"],
            "year_exact": str(year_exact).lower(),
            "descriptor_bundle_exact": str(descriptor_exact).lower(),
            "match_state": state,
            "identity_merge_authorized": "false",
            "decision_basis": "NAME_YEAR_SLUG_PLUS_DESCRIPTOR_HASH_BUNDLE_NO_NEAREST_YEAR_MERGE",
            "review_requirement": "PROJECT_OWNER_REVIEW_REQUIRED" if state in {"POSSIBLE_SAME_RECORD", "INSUFFICIENT_EVIDENCE"} else "NONE",
        })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch2-restricted-root", type=Path, default=DEFAULT_BATCH2)
    parser.add_argument("--round3m-restricted-root", type=Path, default=DEFAULT_ROUND3M)
    parser.add_argument("--extension-restricted-root", type=Path, default=DEFAULT_EXTENSION)
    args = parser.parse_args()

    extension_path = args.extension_restricted_root / "POST20K_ASSERTIONS_RESTRICTED.tsv"
    if not extension_path.is_file():
        raise RuntimeError(f"missing post-20k restricted ledger: {extension_path}")
    base_ledger = read_tsv(CURRENT / "CANONICAL_DESCRIPTOR_ASSERTION_LEDGER.tsv")
    batch2_details, baseline_text = base_restricted_text(
        args.batch2_restricted_root, args.round3m_restricted_root
    )
    extension_rows = read_tsv(extension_path)
    extension_by_id = {row["descriptor_assertion_id"]: row for row in extension_rows}
    by_label, _ = V1.ontology()

    source_rows: list[dict[str, str]] = []
    text_by_id: dict[str, str] = {}
    for row in base_ledger:
        if row["counts_as_assertion"] != "true":
            continue
        restricted = batch2_details.get(row["descriptor_assertion_id"])
        source_rows.append(public_base_row(row, restricted))
        text_by_id[row["descriptor_assertion_id"]] = (
            restricted["atomic_source_text"] if restricted
            else baseline_text.get(row["descriptor_assertion_id"], "")
        )
    for row in extension_rows:
        if row["counts_as_assertion"] != "true":
            continue
        source_rows.append(public_extension_row(row))
        text_by_id[row["descriptor_assertion_id"]] = row["atomic_source_text"]

    source_rows.sort(key=lambda item: item["descriptor_assertion_id"])
    ids = [row["descriptor_assertion_id"] for row in source_rows]
    if len(source_rows) != 30010 or len(set(ids)) != 30010:
        raise RuntimeError(
            f"expected 30,010 unique source assertions, found rows={len(source_rows)} unique={len(set(ids))}"
        )

    decisions: list[dict[str, Any]] = []
    atoms: list[dict[str, Any]] = []
    cluster_acc: dict[str, dict[str, Any]] = {}
    for source in source_rows:
        raw = text_by_id[source["descriptor_assertion_id"]]
        if raw:
            cleaned, segmentation, basis, confidence = V1.clean_atom(raw)
        else:
            cleaned = [("", "SEMANTICALLY_UNRESOLVED")]
            segmentation = "SOURCE_TEXT_UNAVAILABLE_IN_GOVERNED_RESTRICTED_CHECKPOINT"
            basis = "HASH_ONLY_RESTRICTED_CAPTURE_NOT_AVAILABLE"
            confidence = "0.000000"
        source_disposition = disposition_for(cleaned, segmentation)
        atom_ids: list[str] = []
        atom_hashes: list[str] = []
        atom_classes: list[str] = []
        mapping_states: list[str] = []
        concept_ids: list[str] = []
        cluster_ids: list[str] = []
        authorities: list[str] = []
        for index, (value, klass) in enumerate(cleaned, start=1):
            lexical_hash = sha256_text(value)
            mapping_state, concept_id, authority, mapping_confidence, components = v2_mapping(
                value, klass, source["source_language"], by_label
            )
            cluster_id = cluster_id_for(lexical_hash, mapping_state, concept_id, components)
            atom_id = stable_id(
                "cleaned-output-atom",
                source["descriptor_assertion_id"] + f"\x1f{index}\x1f" + lexical_hash,
            )
            atom_ids.append(atom_id)
            atom_hashes.append(lexical_hash)
            atom_classes.append(klass)
            mapping_states.append(mapping_state)
            concept_ids.append(concept_id)
            cluster_ids.append(cluster_id)
            authorities.append(authority)
            modifier_hashes = [sha256_text(part) for part in value.split() if part in V1.MODIFIERS]
            base_value = " ".join(part for part in value.split() if part not in V1.MODIFIERS) or value
            atoms.append({
                "cleaned_output_atom_id": atom_id,
                "descriptor_assertion_id": source["descriptor_assertion_id"],
                "corpus_segment": source["corpus_segment"],
                "source_family_id": source["source_family_id"],
                "source_artifact_id": source["source_artifact_id"],
                "source_route_id": source["source_route_id"],
                "effective_record_id": source["effective_record_id"],
                "coffee_identity_id": source["coffee_identity_id"],
                "year_id": source["year_id"],
                "preparation_service_id": source["preparation_service_id"],
                "publication_layer": source["publication_layer"],
                "judge_observation_id_sha256": source["judge_observation_id_sha256"],
                "source_native_form_id": source["source_native_form_id"],
                "cleaned_form_id": f"cleaned-form:{lexical_hash[:24]}",
                "cleaned_lexical_form_sha256": lexical_hash,
                "semantic_class": klass,
                "atom_disposition": atom_disposition(klass),
                "counts_as_cleaned_descriptor_output": str(klass in VALID_ATOM_CLASSES).lower(),
                "mapping_state": mapping_state,
                "canonical_concept_id": concept_id,
                "concept_cluster_id": cluster_id,
                "normalization_authority": authority,
                "mapping_confidence": mapping_confidence,
                "base_form_sha256": sha256_text(base_value),
                "modifier_form_sha256s": modifier_hashes,
                "component_concept_ids": components,
                "evidence_tier": source["evidence_tier"],
                "collection_tier": source["collection_tier"],
                "rights_state": source["rights_state"],
                "counts_as_record_unique_descriptor": source["counts_as_record_unique_descriptor"],
                "human_reviewed": "false",
                "expert_adjudicated": "false",
                "model_eligible": "false",
                "cleaner_contract_version": CLEANER_CONTRACT_VERSION,
            })
            acc = cluster_acc.setdefault(cluster_id, {
                "concept_cluster_id": cluster_id,
                "cleaned_form_ids": set(),
                "cleaned_form_sha256s": set(),
                "source_native_form_ids": set(),
                "source_languages": set(),
                "semantic_classes": set(),
                "base_form_sha256s": set(),
                "modifier_form_sha256s": set(),
                "component_concept_ids": set(),
                "canonical_concept_ids": set(),
                "mapping_states": set(),
                "normalization_authorities": set(),
                "source_families": set(),
                "years": set(),
                "effective_records": set(),
                "assertion_count": 0,
                "gold_assertion_count": 0,
                "silver_assertion_count": 0,
                "bronze_assertion_count": 0,
            })
            acc["cleaned_form_ids"].add(f"cleaned-form:{lexical_hash[:24]}")
            acc["cleaned_form_sha256s"].add(lexical_hash)
            acc["source_native_form_ids"].add(source["source_native_form_id"])
            acc["source_languages"].add(source["source_language"])
            acc["semantic_classes"].add(klass)
            acc["base_form_sha256s"].add(sha256_text(base_value))
            acc["modifier_form_sha256s"].update(modifier_hashes)
            acc["component_concept_ids"].update(components)
            if concept_id:
                acc["canonical_concept_ids"].add(concept_id)
            acc["mapping_states"].add(mapping_state)
            if authority != "NO_GOVERNED_AUTHORITY":
                acc["normalization_authorities"].add(authority)
            acc["source_families"].add(source["source_family_id"])
            acc["years"].add(source["year_id"])
            acc["effective_records"].add(source["effective_record_id"])
            acc["assertion_count"] += 1
            tier_key = source["collection_tier"].casefold() + "_assertion_count"
            if tier_key in acc:
                acc[tier_key] += 1

        original = source["original_descriptor_class"]
        comparable = {
            "STRICT_FLAVOR": "VALID_STRICT_FLAVOR",
            "BROAD_SENSORY": "VALID_BROAD_SENSORY",
            "DEFECT_OR_NEGATIVE_SENSORY": "VALID_DEFECT_OR_NEGATIVE_SENSORY",
        }.get(original, original)
        decisions.append({
            **source,
            "source_assertion_disposition": source_disposition,
            "segmentation_decision": segmentation,
            "segmentation_confidence": confidence,
            "segmentation_basis": basis,
            "cleaned_output_atom_count": len(cleaned),
            "cleaned_output_atom_ids": atom_ids,
            "cleaned_lexical_form_sha256s": atom_hashes,
            "semantic_classes": atom_classes,
            "mapping_states": mapping_states,
            "canonical_concept_ids": concept_ids,
            "concept_cluster_ids": cluster_ids,
            "normalization_authorities": authorities,
            "machine_first_pass_reclassified": str(
                comparable != source_disposition
                and not (
                    comparable == "VALID_STRICT_FLAVOR"
                    and source_disposition in {"VALID_COMPOUND_SPLIT", "VALID_COMPOUND_PRESERVED"}
                )
            ).lower(),
            "human_reviewed": "false",
            "expert_adjudicated": "false",
            "model_eligible": "false",
            "cleaner_contract_version": CLEANER_CONTRACT_VERSION,
        })

    cluster_tokens: dict[str, set[str]] = defaultdict(set)
    for cluster_id, acc in cluster_acc.items():
        cluster_tokens[cluster_id].update(acc["base_form_sha256s"])
        cluster_tokens[cluster_id].update(acc["modifier_form_sha256s"])
        cluster_tokens[cluster_id].update(acc["component_concept_ids"])
    token_index: dict[str, set[str]] = defaultdict(set)
    for cluster_id, tokens in cluster_tokens.items():
        for token in tokens:
            token_index[token].add(cluster_id)

    clusters: list[dict[str, Any]] = []
    for cluster_id, acc in sorted(cluster_acc.items()):
        candidates: Counter[str] = Counter()
        for token in cluster_tokens[cluster_id]:
            for neighbor in token_index[token]:
                if neighbor != cluster_id:
                    candidates[neighbor] += 1
        neighbors = [item for item, _ in candidates.most_common(5)]
        mapping_states = sorted(acc["mapping_states"])
        primary_state = mapping_states[0] if len(mapping_states) == 1 else (
            "AMBIGUOUS_CONCEPT_BOUNDARY" if "AMBIGUOUS_CONCEPT_BOUNDARY" in mapping_states
            else mapping_states[0]
        )
        support = int(acc["assertion_count"])
        clusters.append({
            "concept_cluster_id": cluster_id,
            "cleaned_form_count": len(acc["cleaned_form_ids"]),
            "cleaned_form_ids": sorted(acc["cleaned_form_ids"]),
            "cleaned_form_sha256s": sorted(acc["cleaned_form_sha256s"]),
            "source_native_form_count": len(acc["source_native_form_ids"]),
            "source_native_form_ids": sorted(acc["source_native_form_ids"]),
            "source_languages": sorted(acc["source_languages"]),
            "semantic_classes": sorted(acc["semantic_classes"]),
            "base_form_sha256s": sorted(acc["base_form_sha256s"]),
            "modifier_form_sha256s": sorted(acc["modifier_form_sha256s"]),
            "component_concept_ids": sorted(acc["component_concept_ids"]),
            "neighbor_cluster_ids": neighbors,
            "canonical_concept_ids": sorted(acc["canonical_concept_ids"]),
            "mapping_state": primary_state,
            "normalization_authorities": sorted(acc["normalization_authorities"]),
            "assertion_support": support,
            "effective_record_support": len(acc["effective_records"]),
            "source_family_count": len(acc["source_families"]),
            "source_family_ids": sorted(acc["source_families"]),
            "year_count": len(acc["years"]),
            "year_ids": sorted(acc["years"]),
            "gold_assertion_count": acc["gold_assertion_count"],
            "silver_assertion_count": acc["silver_assertion_count"],
            "bronze_assertion_count": acc["bronze_assertion_count"],
            "support_band": "SUPPORT_100_PLUS" if support >= 100 else "SUPPORT_20_99" if support >= 20 else "SUPPORT_5_19" if support >= 5 else "SUPPORT_1_4",
            "review_priority_score": (
                min(support, 1000)
                + 80 * len(acc["source_families"])
                + 40 * len(acc["years"])
                + 100 * int(primary_state in {"AMBIGUOUS_CONCEPT_BOUNDARY", "CROSS_LANGUAGE_REVIEW_REQUIRED", "UNRESOLVED"})
            ),
            "reversible_to_source_assertions": "true",
            "human_reviewed": "false",
            "expert_adjudicated": "false",
        })

    artifacts: dict[tuple[str, str], dict[str, Any]] = {}
    for row in source_rows:
        key = (row["source_family_id"], row["source_artifact_id"])
        if key not in artifacts:
            artifacts[key] = {
                "source_family_id": row["source_family_id"],
                "source_artifact_id": row["source_artifact_id"],
                "source_artifact_sha256": row["source_artifact_sha256"],
                "source_locator": row["source_locator"],
                "source_rights_state": row["rights_state"],
                "source_rights_basis": row["rights_basis"],
                **rights_terms(row),
                "source_assertion_count": 0,
            }
        artifacts[key]["source_assertion_count"] += 1

    OUT.mkdir(parents=True, exist_ok=True)
    write_tsv(OUT / "BATCH4_SOURCE_ASSERTION_METADATA.tsv", list(source_rows[0]), source_rows)
    write_tsv(OUT / "BATCH4_PUBLIC_SAFE_CLEANING_V2.tsv", list(decisions[0]), decisions)
    write_tsv(OUT / "BATCH4_PUBLIC_SAFE_OUTPUT_ATOMS.tsv", list(atoms[0]), atoms)
    write_tsv(OUT / "BATCH4_CONCEPT_CLUSTER_SIDECAR.tsv", list(clusters[0]), clusters)
    artifact_rows = [artifacts[key] for key in sorted(artifacts)]
    write_tsv(OUT / "BATCH4_ARTIFACT_RIGHTS_INPUT.tsv", list(artifact_rows[0]), artifact_rows)
    coe_rows = identity_rows()
    write_tsv(OUT / "BATCH4_COE_IDENTITY_RESOLUTION.tsv", list(coe_rows[0]), coe_rows)

    manifest = {
        "contract_version": "batch4.public-safe-cleaning-staging.v1",
        "snapshot_version": SNAPSHOT_VERSION,
        "cleaner_contract_version": CLEANER_CONTRACT_VERSION,
        "builder_version": BUILDER_VERSION,
        "generated_at": GENERATED_AT,
        "restricted_input_storage": "OWNER_CONTROLLED_RESTRICTED_NON_GIT",
        "public_source_native_text_included": False,
        "source_assertion_count": len(source_rows),
        "frozen_20k_source_assertion_count": sum(row["corpus_segment"] == "FROZEN_20K" for row in source_rows),
        "extension_source_assertion_count": sum(row["corpus_segment"] == "POST20K_EXTENSION" for row in source_rows),
        "cleaned_output_atom_count": len(atoms),
        "concept_cluster_count": len(clusters),
        "source_artifact_count": len(artifact_rows),
        "normalization_authority_counts": dict(sorted(Counter(atom["normalization_authority"] for atom in atoms).items())),
        "mapping_state_counts": dict(sorted(Counter(atom["mapping_state"] for atom in atoms).items())),
        "source_disposition_counts": dict(sorted(Counter(row["source_assertion_disposition"] for row in decisions).items())),
        "human_reviewed_count": 0,
        "expert_adjudicated_count": 0,
        "model_eligible_count": 0,
        "legal_review_performed": False,
        "files": [],
    }
    for path in sorted(OUT.glob("*.tsv")):
        manifest["files"].append({
            "path": path.name,
            "sha256": sha256_file(path),
            "byte_count": path.stat().st_size,
            "data_row_count": max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0),
        })
    manifest_path = OUT / "BATCH4_STAGING_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_paths = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )
    print(
        "BATCH4_CLEANING_STAGING_PASS "
        f"source_assertions={len(source_rows)} atoms={len(atoms)} "
        f"clusters={len(clusters)} artifacts={len(artifact_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
