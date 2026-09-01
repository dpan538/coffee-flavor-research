#!/usr/bin/env python3
"""Build Batch 6's public-safe 40k semantic corpus and benchmark candidates.

The generator deliberately consumes source-native text only from the existing
owner-controlled post-30k ledger.  Its committed outputs retain hashes,
stable identifiers and restricted pointers.  It neither changes the V2
cleaner nor trains a model.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import os
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "db" / "data" / "current"
POST30 = ROOT / "db" / "data" / "post30k-extension-staging"
POST40 = ROOT / "db" / "data" / "post40k-extension-staging"
POST30_RESTRICTED = Path(
    os.environ.get(
        "BATCH6_POST30_RESTRICTED_ROOT",
        str(Path(tempfile.gettempdir()) / "coffee-flavor-round3m-post30k" / "post30k_extension"),
    )
)
RESTRICTED_REVIEW = POST30_RESTRICTED / "batch6_semantic_review"
BUILDER_PATH = ROOT / "db" / "scripts" / "build-batch4-cleaning-staging.py"

SNAPSHOT_VERSION = "professional-descriptor-candidate-v2-40k"
CLEANED_VIEW_VERSION = "professional-descriptor-cleaned-v2-40k"
CLEANER_VERSION = "batch4.semantic-cleaner.v2"
GENERATOR_VERSION = "batch6.semantic-corpus-generator.v1"
GENERATED_AT = "2026-08-30T00:00:00+10:00"
PERMITTED = {"AFFIRMATIVE", "AFFIRMATIVE_WITH_CONDITIONS"}
VALID_OUTPUT = {
    "STRICT_FLAVOR", "BROAD_SENSORY", "DEFECT_OR_NEGATIVE_SENSORY",
    "COMPOSITE_DESCRIPTOR",
}
VALID_SOURCE = {
    "VALID_STRICT_FLAVOR", "VALID_BROAD_SENSORY",
    "VALID_DEFECT_OR_NEGATIVE_SENSORY", "VALID_COMPOUND_SPLIT",
    "VALID_COMPOUND_PRESERVED",
}


def load_builder():
    spec = importlib.util.spec_from_file_location("batch6_v2_cleaner", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Batch 4 V2 cleaner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


B = load_builder()


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_id(prefix: str, material: str) -> str:
    return f"{prefix}:{sha_text(material)[:24]}"


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in sorted(value))
    return str(value)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, fields: Iterable[str], rows: Iterable[Mapping[str, Any]]) -> None:
    names = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=names, delimiter="\t", lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({name: scalar(row.get(name, "")) for name in names})


def write_json(path: Path, document: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def data_rows(path: Path) -> int | str:
    if path.suffix != ".tsv":
        return "NA_NOT_TABULAR"
    return max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0)


def split_pipe(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(part) for part in value if part]
    return [part for part in str(value).split("|") if part]


def purpose_rights(source: Mapping[str, str]) -> dict[str, str]:
    basis = source.get("rights_basis", "")
    state = source.get("rights_state", "UNKNOWN")
    if "CC_BY_NC_4_0" in basis:
        return {
            "rights_public_discovery": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_internal_research_analysis": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_noncommercial_model_research": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_commercial_model_training": "PROHIBITED",
            "rights_derived_data_release": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_raw_text_redistribution": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_model_weight_release": "OWNER_POLICY_REQUIRED",
            "rights_product_deployment": "PROHIBITED",
        }
    if "CC_BY_4_0" in basis or "CC_BY_FRONTIERS_ARTICLE" in basis:
        return {
            "rights_public_discovery": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_internal_research_analysis": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_noncommercial_model_research": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_commercial_model_training": "PENDING",
            "rights_derived_data_release": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_raw_text_redistribution": "AFFIRMATIVE_WITH_CONDITIONS",
            "rights_model_weight_release": "OWNER_POLICY_REQUIRED",
            "rights_product_deployment": "OWNER_POLICY_REQUIRED",
        }
    status = "PENDING" if state == "PENDING" else "UNKNOWN"
    return {
        "rights_public_discovery": "AFFIRMATIVE",
        "rights_internal_research_analysis": status,
        "rights_noncommercial_model_research": status,
        "rights_commercial_model_training": "UNKNOWN",
        "rights_derived_data_release": "UNKNOWN",
        "rights_raw_text_redistribution": "UNKNOWN",
        "rights_model_weight_release": "OWNER_POLICY_REQUIRED",
        "rights_product_deployment": "UNKNOWN",
    }


def post30_source(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "corpus_segment": "POST30K_EXTENSION",
        "descriptor_assertion_id": row["descriptor_assertion_id"],
        "source_family_id": row["source_family_id"],
        "publisher_id": stable_id("publisher", row["publisher"]),
        "source_route_id": row["source_route_id"],
        "source_artifact_id": stable_id("source-artifact", row["source_artifact_sha256"]),
        "source_artifact_sha256": row["source_artifact_sha256"],
        "source_locator": row["source_locator"],
        "effective_record_id": row["effective_record_id"],
        "coffee_identity_id": row["coffee_identity_id"],
        "year_id": f"year.{row['edition_year']}" if row["edition_year"] else "year.unreported",
        "preparation_service_id": row["preparation_service"],
        "source_language": row["source_language"],
        "source_field_label_sha256": row["source_field_label"].removeprefix("hash:sha256:"),
        "raw_field_text_sha256": row["raw_field_text_sha256"],
        "atomic_source_text_sha256": row["atomic_source_text_sha256"],
        "source_native_form_id": f"source-form:{row['source_native_form_sha256'][:24]}",
        "restricted_source_pointer": f"restricted://post30k_extension/assertions/{row['descriptor_assertion_id']}",
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


def clean_source(source: Mapping[str, str], raw: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    by_label, _ = B.V1.ontology()
    cleaned, segmentation, basis, confidence = B.V1.clean_atom(raw)
    disposition = B.disposition_for(cleaned, segmentation)
    atom_ids: list[str] = []
    hashes: list[str] = []
    classes: list[str] = []
    mapping_states: list[str] = []
    concept_ids: list[str] = []
    cluster_ids: list[str] = []
    authorities: list[str] = []
    atoms: list[dict[str, Any]] = []
    rights = purpose_rights(source)
    for index, (value, klass) in enumerate(cleaned, start=1):
        lexical_hash = sha_text(value)
        mapping_state, concept_id, authority, mapping_confidence, components = B.v2_mapping(
            value, klass, source["source_language"], by_label
        )
        cluster_id = B.cluster_id_for(lexical_hash, mapping_state, concept_id, components)
        atom_id = stable_id("cleaned-output-atom", source["descriptor_assertion_id"] + f"\x1f{index}\x1f{lexical_hash}")
        modifier_hashes = [sha_text(part) for part in value.split() if part in B.V1.MODIFIERS]
        base = " ".join(part for part in value.split() if part not in B.V1.MODIFIERS) or value
        atom_ids.append(atom_id)
        hashes.append(lexical_hash)
        classes.append(klass)
        mapping_states.append(mapping_state)
        concept_ids.append(concept_id)
        cluster_ids.append(cluster_id)
        authorities.append(authority)
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
            "atom_disposition": B.atom_disposition(klass),
            "counts_as_cleaned_descriptor_output": str(klass in VALID_OUTPUT).lower(),
            "mapping_state": mapping_state,
            "canonical_concept_id": concept_id,
            "concept_cluster_id": cluster_id,
            "normalization_authority": authority,
            "mapping_confidence": mapping_confidence,
            "base_form_sha256": sha_text(base),
            "modifier_form_sha256s": modifier_hashes,
            "component_concept_ids": components,
            "evidence_tier": source["evidence_tier"],
            "collection_tier": source["collection_tier"],
            "rights_state": source["rights_state"],
            "counts_as_record_unique_descriptor": source["counts_as_record_unique_descriptor"],
            "human_reviewed": "false",
            "expert_adjudicated": "false",
            "model_eligible": "false",
            "cleaner_contract_version": CLEANER_VERSION,
            **rights,
        })
    comparable = {
        "STRICT_FLAVOR": "VALID_STRICT_FLAVOR",
        "BROAD_SENSORY": "VALID_BROAD_SENSORY",
        "DEFECT_OR_NEGATIVE_SENSORY": "VALID_DEFECT_OR_NEGATIVE_SENSORY",
    }.get(source["original_descriptor_class"], source["original_descriptor_class"])
    decision = {
        **source,
        "source_assertion_disposition": disposition,
        "segmentation_decision": segmentation,
        "segmentation_confidence": confidence,
        "segmentation_basis": basis,
        "cleaned_output_atom_count": len(cleaned),
        "cleaned_output_atom_ids": atom_ids,
        "cleaned_lexical_form_sha256s": hashes,
        "semantic_classes": classes,
        "mapping_states": mapping_states,
        "canonical_concept_ids": concept_ids,
        "concept_cluster_ids": cluster_ids,
        "normalization_authorities": authorities,
        "machine_first_pass_reclassified": str(
            comparable != disposition and not (
                comparable == "VALID_STRICT_FLAVOR" and disposition in {"VALID_COMPOUND_SPLIT", "VALID_COMPOUND_PRESERVED"}
            )
        ).lower(),
        "human_reviewed": "false",
        "expert_adjudicated": "false",
        "model_eligible": "false",
        "cleaner_contract_version": CLEANER_VERSION,
    }
    return decision, atoms


def combined_cleaned() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    base_decisions = read_tsv(CURRENT / "CLEANED_30K_SOURCE_ASSERTION_LEDGER.tsv")
    base_atoms = read_tsv(CURRENT / "CLEANED_30K_OUTPUT_ATOM_LEDGER.tsv")
    restricted_path = POST30_RESTRICTED / "POST30K_ASSERTIONS_RESTRICTED.tsv"
    if not restricted_path.is_file():
        # CI deliberately does not receive owner-controlled source text.  The
        # checked-in public-safe 40k ledgers are a frozen V2 projection of
        # that text, so they are the only lawful input for an offline public
        # replay.  This preserves the 40k artifact byte-for-byte without
        # widening the public data boundary or trying to recreate raw forms.
        cached_source = CURRENT / "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv"
        cached_atoms = CURRENT / "CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv"
        if not cached_source.is_file() or not cached_atoms.is_file():
            raise RuntimeError(
                "missing owner-controlled post-30k ledger and frozen public-safe 40k replay ledgers"
            )
        decisions = read_tsv(cached_source)
        atoms = read_tsv(cached_atoms)
        if len(decisions) != 40030 or len(atoms) != 42007:
            raise RuntimeError("frozen public-safe 40k replay denominator drift")
        return decisions, atoms, {}
    raw_rows = [row for row in read_tsv(restricted_path) if row["counts_as_assertion"] == "true"]
    if len(base_decisions) != 30010 or len(raw_rows) != 10020:
        raise RuntimeError(f"40k input denominator drift: 30k={len(base_decisions)} post30k={len(raw_rows)}")
    decisions: list[dict[str, Any]] = [dict(row) for row in base_decisions]
    atoms: list[dict[str, Any]] = [dict(row) for row in base_atoms]
    raw_by_id: dict[str, str] = {}
    for raw in raw_rows:
        source = post30_source(raw)
        decision, new_atoms = clean_source(source, raw["atomic_source_text"])
        decisions.append(decision)
        atoms.extend(new_atoms)
        raw_by_id[source["descriptor_assertion_id"]] = raw["atomic_source_text"]
    decisions.sort(key=lambda row: row["descriptor_assertion_id"])
    atoms.sort(key=lambda row: row["cleaned_output_atom_id"])
    # Both the restricted-cleaner path and the public-replay path operate on
    # TSV contracts. Normalize in-memory sequences to that same tabular form
    # before using them to derive IDs, candidates, or packets; otherwise a
    # list's transient order could make a lawful public replay differ from a
    # raw-input run even though the emitted ledger is identical.
    decisions = [{key: scalar(value) for key, value in row.items()} for row in decisions]
    atoms = [{key: scalar(value) for key, value in row.items()} for row in atoms]
    if len(decisions) != 40030 or len({row["descriptor_assertion_id"] for row in decisions}) != 40030:
        raise RuntimeError("combined source assertion identity reconciliation failed")
    if len(atoms) != sum(int(row["cleaned_output_atom_count"]) for row in decisions):
        raise RuntimeError("combined source assertion/output atom reconciliation failed")
    return decisions, atoms, raw_by_id


def node_id(atom: Mapping[str, str]) -> str:
    target = atom["canonical_concept_id"] or atom["concept_cluster_id"]
    return f"semantic-concept:{target}"


def concept_clusters(atoms: list[Mapping[str, str]]) -> list[dict[str, Any]]:
    acc: dict[str, dict[str, Any]] = {}
    for atom in atoms:
        cluster = atom["concept_cluster_id"]
        row = acc.setdefault(cluster, {
            "concept_cluster_id": cluster, "cleaned": set(), "native": set(), "languages": set(),
            "classes": set(), "base": set(), "modifiers": set(), "components": set(),
            "canonical": set(), "states": set(), "authorities": set(), "families": set(),
            "years": set(), "records": set(), "assertions": 0, "gold": 0, "silver": 0,
            "bronze": 0, "rights": Counter(),
        })
        row["cleaned"].add(atom["cleaned_form_id"])
        row["native"].add(atom["source_native_form_id"])
        row["languages"].add(atom.get("source_language", "") or "UNREPORTED")
        row["classes"].add(atom["semantic_class"])
        row["base"].add(atom["base_form_sha256"])
        row["modifiers"].update(split_pipe(atom["modifier_form_sha256s"]))
        row["components"].update(split_pipe(atom["component_concept_ids"]))
        if atom["canonical_concept_id"]:
            row["canonical"].add(atom["canonical_concept_id"])
        row["states"].add(atom["mapping_state"])
        if atom["normalization_authority"] != "NO_GOVERNED_AUTHORITY":
            row["authorities"].add(atom["normalization_authority"])
        row["families"].add(atom["source_family_id"])
        row["years"].add(atom["year_id"])
        row["records"].add(atom["effective_record_id"])
        row["assertions"] += 1
        tier = atom["collection_tier"].casefold()
        if tier in {"gold", "silver", "bronze"}:
            row[tier] += 1
        row["rights"][atom["rights_state"]] += 1
    base_index: dict[str, set[str]] = defaultdict(set)
    for cid, row in acc.items():
        for token in row["base"] | row["modifiers"] | row["components"]:
            base_index[token].add(cid)
    result = []
    for cid, row in sorted(acc.items()):
        neighbours = Counter()
        for token in row["base"] | row["modifiers"] | row["components"]:
            for other in base_index[token]:
                if other != cid:
                    neighbours[other] += 1
        states = sorted(row["states"])
        state = states[0] if len(states) == 1 else (
            "AMBIGUOUS_CONCEPT_BOUNDARY" if "AMBIGUOUS_CONCEPT_BOUNDARY" in states else states[0]
        )
        result.append({
            "concept_cluster_id": cid,
            "cleaned_form_count": len(row["cleaned"]),
            "cleaned_form_ids": row["cleaned"],
            "source_native_form_count": len(row["native"]),
            "source_native_form_ids": row["native"],
            "source_languages": row["languages"],
            "semantic_classes": row["classes"],
            "base_form_sha256s": row["base"],
            "modifier_form_sha256s": row["modifiers"],
            "component_concept_ids": row["components"],
            "existing_canonical_neighbour_cluster_ids": [
                item for item, _ in sorted(
                    neighbours.items(), key=lambda pair: (-pair[1], pair[0])
                )[:5]
            ],
            "canonical_concept_ids": row["canonical"],
            "mapping_state": state,
            "mapping_authorities": row["authorities"],
            "assertion_support": row["assertions"],
            "effective_record_support": len(row["records"]),
            "coffee_sample_support": len(row["records"]),
            "source_family_support": len(row["families"]),
            "source_family_ids": row["families"],
            "publisher_support": len(row["families"]),
            "year_support": len(row["years"]),
            "year_ids": row["years"],
            "gold_support": row["gold"],
            "silver_support": row["silver"],
            "bronze_support": row["bronze"],
            "rights_distribution": [f"{key}:{value}" for key, value in sorted(row["rights"].items())],
            "review_priority": min(row["assertions"], 1000) + 100 * len(row["families"]) + 80 * int(state in {"AMBIGUOUS_CONCEPT_BOUNDARY", "CROSS_LANGUAGE_REVIEW_REQUIRED", "UNRESOLVED"}),
            "human_reviewed": "false",
            "sensory_expert_adjudicated": "false",
            "reversible_to_source_assertions": "true",
        })
    return result


def semantic_graph(atoms: list[Mapping[str, str]], clusters: list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    valid = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    forms: dict[str, dict[str, Any]] = {}
    for atom in valid:
        form = forms.setdefault(atom["cleaned_form_id"], {
            "semantic_form_node_id": f"semantic-form:{atom['cleaned_lexical_form_sha256'][:24]}",
            "cleaned_form_id": atom["cleaned_form_id"],
            "cleaned_lexical_form_sha256": atom["cleaned_lexical_form_sha256"],
            "source_languages": set(), "semantic_classes": set(), "source_native_form_ids": set(),
            "source_families": set(), "records": set(), "assertion_support": 0,
        })
        form["source_languages"].add(atom.get("source_language", "") or "UNREPORTED")
        form["semantic_classes"].add(atom["semantic_class"])
        form["source_native_form_ids"].add(atom["source_native_form_id"])
        form["source_families"].add(atom["source_family_id"])
        form["records"].add(atom["effective_record_id"])
        form["assertion_support"] += 1
    form_rows = [{**row, "source_language_count": len(row["source_languages"]), "source_native_form_count": len(row["source_native_form_ids"]), "source_family_count": len(row["source_families"]), "effective_record_support": len(row["records"])} for _, row in sorted(forms.items())]
    concept_ids = sorted({atom["canonical_concept_id"] for atom in valid if atom["canonical_concept_id"]} | {row["concept_cluster_id"] for row in clusters})
    concept_rows = [{
        "semantic_concept_node_id": f"semantic-concept:{concept}",
        "concept_or_cluster_id": concept,
        "node_kind": "EXISTING_CANONICAL_CONCEPT" if concept.startswith("sensory.") else "CONCEPT_CLUSTER",
        "canonical_ontology_auto_promotion": "false",
    } for concept in concept_ids]
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    evidence: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []

    def add_edge(layer: str, subject: str, relation: str, obj: str, level: str, state: str, atom: Mapping[str, str], basis: str) -> str:
        key = (subject, relation, obj)
        edge = edges.setdefault(key, {
            "semantic_relation_id": stable_id("semantic-relation", "\x1f".join(key)),
            "relation_layer": layer, "subject_node_id": subject, "relation_type": relation,
            "object_node_id": obj, "semantic_evidence_authority": level,
            "governance_state": state, "support_assertion_ids": set(), "records": set(),
            "families": set(), "source_basis": basis,
        })
        edge["support_assertion_ids"].add(atom["descriptor_assertion_id"])
        edge["records"].add(atom["effective_record_id"])
        edge["families"].add(atom["source_family_id"])
        return edge["semantic_relation_id"]

    for atom in valid:
        form = f"semantic-form:{atom['cleaned_lexical_form_sha256'][:24]}"
        concept = node_id(atom)
        state = atom["mapping_state"]
        if state == "EXISTING_CANONICAL_EXACT":
            add_edge("LEXICAL_EQUIVALENCE", form, "EXACT_EQUIVALENT", concept, "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "GOVERNED", atom, "EXISTING_GOVERNED_CANONICAL_MAPPING")
            add_edge("LEXICAL_EQUIVALENCE", concept, "EXACT_EQUIVALENT", form, "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "GOVERNED", atom, "EXISTING_GOVERNED_CANONICAL_MAPPING")
        elif state == "EXISTING_CANONICAL_ALIAS":
            add_edge("LEXICAL_EQUIVALENCE", form, "APPROVED_ALIAS_OF", concept, "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "GOVERNED", atom, "EXISTING_APPROVED_ALIAS")
            add_edge("LEXICAL_EQUIVALENCE", concept, "APPROVED_ALIAS_OF", form, "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "GOVERNED", atom, "EXISTING_APPROVED_ALIAS")
        elif state == "EXISTING_CANONICAL_MORPHOLOGICAL_VARIANT":
            add_edge("LEXICAL_EQUIVALENCE", form, "MORPHOLOGICAL_VARIANT_OF", concept, "S0_DETERMINISTIC_ORTHOGRAPHIC", "GOVERNED", atom, "V2_SAFE_MORPHOLOGICAL_RULE")
            add_edge("LEXICAL_EQUIVALENCE", concept, "MORPHOLOGICAL_VARIANT_OF", form, "S0_DETERMINISTIC_ORTHOGRAPHIC", "GOVERNED", atom, "V2_SAFE_MORPHOLOGICAL_RULE")
        elif state == "EXISTING_CANONICAL_CHILD_OR_SPECIFIC_FORM":
            relation_id = add_edge("CONCEPT_HIERARCHY", form, "INSTANCE_OR_SPECIFIC_FORM_OF", concept, "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "REVIEW_REQUIRED", atom, "V2_CONTAINMENT_CANDIDATE")
            candidates.append({"semantic_relation_candidate_id": stable_id("semantic-candidate", relation_id), "semantic_relation_id": relation_id, "relation_type": "INSTANCE_OR_SPECIFIC_FORM_OF", "candidate_reason": "V2_CONTAINMENT_CANDIDATE_NOT_EQUIVALENCE", "review_required": "true"})
        for modifier_hash in split_pipe(atom["modifier_form_sha256s"]):
            modifier = f"semantic-form:{modifier_hash[:24]}"
            relation_id = add_edge("MODIFIER_COMPOUND", modifier, "MODIFIES", form, "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "REVIEW_REQUIRED", atom, "V2_MODIFIER_PARSE")
            candidates.append({"semantic_relation_candidate_id": stable_id("semantic-candidate", relation_id), "semantic_relation_id": relation_id, "relation_type": "MODIFIES", "candidate_reason": "MODIFIER_PARSE_REQUIRES_REVIEW", "review_required": "true"})
        for component in split_pipe(atom["component_concept_ids"]):
            relation_id = add_edge("MODIFIER_COMPOUND", f"semantic-concept:{component}", "COMPONENT_OF", form, "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "REVIEW_REQUIRED", atom, "V2_COMPOUND_COMPONENT_PARSE")
            candidates.append({"semantic_relation_candidate_id": stable_id("semantic-candidate", relation_id), "semantic_relation_id": relation_id, "relation_type": "COMPONENT_OF", "candidate_reason": "COMPOUND_COMPONENT_PARSE_REQUIRES_REVIEW", "review_required": "true"})

    by_record: dict[str, dict[str, Mapping[str, str]]] = defaultdict(dict)
    for atom in valid:
        by_record[atom["effective_record_id"]][node_id(atom)] = atom
    for record_atoms in by_record.values():
        ids = sorted(record_atoms)
        for index, left in enumerate(ids):
            for right in ids[index + 1:]:
                add_edge("OBSERVATIONAL", left, "COASSERTED_WITH", right, "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "OBSERVATIONAL_ONLY", record_atoms[left], "SAME_EFFECTIVE_RECORD_NO_EQUIVALENCE_INFERENCE")
    for atom in valid:
        subject = node_id(atom)
        prep = atom["preparation_service_id"]
        if prep:
            add_edge("CONTEXT", subject, "OBSERVED_UNDER_PREPARATION", f"semantic-context:preparation:{sha_text(prep)[:24]}", "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "OBSERVATIONAL_ONLY", atom, "SOURCE_REPORTED_PREPARATION")
        roast = atom.get("roast_evidence_sha256_or_state", "")
        if roast:
            add_edge("CONTEXT", subject, "OBSERVED_WITH_ROAST_EVIDENCE", f"semantic-context:roast:{sha_text(roast)[:24]}", "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "OBSERVATIONAL_ONLY", atom, "SOURCE_REPORTED_ROAST_EVIDENCE")
    edge_rows = []
    for _, edge in sorted(edges.items()):
        edge_rows.append({
            **{key: value for key, value in edge.items() if key not in {"support_assertion_ids", "records", "families"}},
            "source_assertion_support": len(edge["support_assertion_ids"]), "effective_record_support": len(edge["records"]),
            "source_family_support": len(edge["families"]), "human_reviewed": "false", "sensory_expert_adjudicated": "false",
        })
    evidence = [
        {
            "semantic_relation_evidence_id": "semantic-evidence-profile:s0",
            "semantic_relation_id": "AUTHORITY_PROFILE:S0_DETERMINISTIC_ORTHOGRAPHIC",
            "source_id": "batch4-v2-deterministic-cleaner",
            "source_locator_or_restricted_pointer": "db/scripts/build-batch4-cleaning-staging.py",
            "term_or_context_hash": "NA_AUTHORITY_PROFILE",
            "relation_supported": "MORPHOLOGICAL_VARIANT_OF",
            "evidence_authority": "S0_DETERMINISTIC_ORTHOGRAPHIC",
            "rights_status": "PROJECT_GOVERNED_CONTENT",
            "raw_definition_published": "false",
        },
        {
            "semantic_relation_evidence_id": "semantic-evidence-profile:s1",
            "semantic_relation_id": "AUTHORITY_PROFILE:S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS",
            "source_id": "semantic-reference.existing-governed-ontology-v1",
            "source_locator_or_restricted_pointer": "restricted://governed-ontology-and-approved-alias-rules",
            "term_or_context_hash": "NA_AUTHORITY_PROFILE",
            "relation_supported": "EXACT_EQUIVALENT|APPROVED_ALIAS_OF",
            "evidence_authority": "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS",
            "rights_status": "PROJECT_GOVERNED_CONTENT",
            "raw_definition_published": "false",
        },
        {
            "semantic_relation_evidence_id": "semantic-evidence-profile:s3",
            "semantic_relation_id": "AUTHORITY_PROFILE:S3_MULTI_SOURCE_MACHINE_CANDIDATE",
            "source_id": "corpus-observation-aggregation",
            "source_locator_or_restricted_pointer": "restricted://semantic-relation-support-by-edge-id",
            "term_or_context_hash": "NA_AUTHORITY_PROFILE",
            "relation_supported": "HIERARCHY|MODIFIER|COMPOUND|OBSERVATIONAL|CONTEXT",
            "evidence_authority": "S3_MULTI_SOURCE_MACHINE_CANDIDATE",
            "rights_status": "MIXED_SOURCE_RIGHTS_NO_PROMOTION",
            "raw_definition_published": "false",
        },
    ]
    return form_rows, concept_rows, edge_rows, evidence, candidates, rejections


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
    def find(self, item: str) -> str:
        self.parent.setdefault(item, item)
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]
    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self.parent[b] = a


def target_id(atom: Mapping[str, str]) -> str:
    return atom["canonical_concept_id"] or atom["concept_cluster_id"]


def benchmark(atoms: list[Mapping[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    valid = [atom for atom in atoms if atom["counts_as_cleaned_descriptor_output"] == "true"]
    governed = [atom for atom in valid if atom["canonical_concept_id"] and atom["normalization_authority"] == "MACHINE_GOVERNED_HIGH_CONFIDENCE"]
    by_target: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    for atom in governed:
        by_target[target_id(atom)].append(atom)
    cases: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    family_cases: list[dict[str, Any]] = []
    open_cases: list[dict[str, Any]] = []
    compound_cases: list[dict[str, Any]] = []
    for target, rows in sorted(by_target.items()):
        forms = defaultdict(list)
        for row in rows:
            forms[row["cleaned_lexical_form_sha256"]].append(row)
        sample_groups = {row["coffee_identity_id"] or row["effective_record_id"] for row in rows}
        if len(forms) >= 2 and len(sample_groups) >= 5:
            held = min(forms, key=lambda form: (len(forms[form]), form))
            test_group_ids = {row["coffee_identity_id"] or row["effective_record_id"] for row in forms[held]}
            training = [row for row in rows if row["cleaned_lexical_form_sha256"] != held and (row["coffee_identity_id"] or row["effective_record_id"]) not in test_group_ids]
            testing = [row for row in forms[held] if (row["coffee_identity_id"] or row["effective_record_id"]) in test_group_ids]
            if training and testing and {row["cleaned_lexical_form_sha256"] for row in training}:
                case_id = stable_id("cross-form-case", target + "\x1f" + held)
                for split, selected in (("TRAIN", training), ("TEST", testing)):
                    for row in selected:
                        cases.append({
                            "benchmark_case_id": case_id, "benchmark_tier": "GOVERNED_CROSS_FORM_BENCHMARK_CANDIDATE",
                            "surface": "UNSEEN_FORM_KNOWN_TARGET", "split": split,
                            "cleaned_output_atom_id": row["cleaned_output_atom_id"], "cleaned_form_hash": row["cleaned_lexical_form_sha256"],
                            "target_concept_or_cluster_id": target, "coffee_sample_group_id": row["coffee_identity_id"] or row["effective_record_id"],
                            "source_family_id": row["source_family_id"], "year_id": row["year_id"],
                            "relation_authority": "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "preferred_requirements_met": str(len({r['source_family_id'] for r in rows}) >= 2 and len({r['year_id'] for r in rows}) >= 2).lower(),
                            "expected_response": "MAP_TO_KNOWN_TARGET", "human_reviewer_decision": "",
                        })
                component_id = stable_id("cross-form-group", target + "\x1f" + held)
                groups.append({"benchmark_case_id": case_id, "benchmark_group_id": component_id, "target_concept_or_cluster_id": target, "held_out_form_hash": held, "train_group_count": len({r['coffee_identity_id'] or r['effective_record_id'] for r in training}), "test_group_count": len(test_group_ids), "form_holdout_feasible": "true", "sample_group_feasible": "true", "component_share": round((len(training) + len(testing)) / len(rows), 6)})
                audits.append({"benchmark_case_id": case_id, "leakage_check": "FORM_HOLDOUT", "leak_count": 0, "status": "PASS", "detail": "HELD_OUT_FORM_ABSENT_FROM_TRAIN"})
                audits.append({"benchmark_case_id": case_id, "leakage_check": "COFFEE_SAMPLE_GROUP", "leak_count": len(({r['coffee_identity_id'] or r['effective_record_id'] for r in training}) & test_group_ids), "status": "PASS", "detail": "GROUPS_ASSIGN_ONE_SPLIT"})
        by_family = defaultdict(list)
        for row in rows:
            by_family[row["source_family_id"]].append(row)
        if len(by_family) >= 2:
            held_family = min(by_family, key=lambda family: (len(by_family[family]), family))
            train = [row for family, family_rows in by_family.items() if family != held_family for row in family_rows]
            test = by_family[held_family]
            case_id = stable_id("held-family-case", target + "\x1f" + held_family)
            for split, selected in (("TRAIN", train), ("TEST", test)):
                for row in selected:
                    family_cases.append({"benchmark_case_id": case_id, "surface": "HELD_OUT_FAMILY_SHARED_TARGET", "split": split, "cleaned_output_atom_id": row["cleaned_output_atom_id"], "target_concept_id": target, "held_out_source_family_id": held_family, "test_form_seen_in_train": str(row["cleaned_lexical_form_sha256"] in {item["cleaned_lexical_form_sha256"] for item in train}).lower() if split == "TEST" else "", "coffee_sample_group_id": row["coffee_identity_id"] or row["effective_record_id"], "expected_response": "MAP_TO_SHARED_TARGET"})
    for atom in valid:
        if not atom["canonical_concept_id"] and atom["mapping_state"] in {"GENUINE_ONTOLOGY_CANDIDATE", "AMBIGUOUS_CONCEPT_BOUNDARY", "CROSS_LANGUAGE_REVIEW_REQUIRED", "UNRESOLVED", "DEFECT_CONCEPT_CANDIDATE"}:
            open_cases.append({"benchmark_case_id": stable_id("open-set-case", atom["cleaned_output_atom_id"]), "surface": "UNSEEN_TARGET_OPEN_SET", "split": "TEST", "cleaned_output_atom_id": atom["cleaned_output_atom_id"], "target_cluster_id": atom["concept_cluster_id"], "target_present_in_training": "false", "expected_response": "ABSTAIN|ONTOLOGY_CANDIDATE|TARGET_NOT_SUPPORTED", "mapping_state": atom["mapping_state"], "coffee_sample_group_id": atom["coffee_identity_id"] or atom["effective_record_id"]})
        if atom["mapping_state"] == "COMPOUND_OF_EXISTING_CONCEPTS" or split_pipe(atom["modifier_form_sha256s"]):
            compound_cases.append({"benchmark_case_id": stable_id("compound-case", atom["cleaned_output_atom_id"]), "surface": "COMPOUND_DECOMPOSITION" if atom["mapping_state"] == "COMPOUND_OF_EXISTING_CONCEPTS" else "MODIFIER_BASE_SEPARATION", "cleaned_output_atom_id": atom["cleaned_output_atom_id"], "base_form_hash": atom["base_form_sha256"], "modifier_form_hashes": atom["modifier_form_sha256s"], "component_concept_ids": atom["component_concept_ids"], "single_label_forced": "false", "expected_response": "STRUCTURED_RELATION_OUTPUT"})
    components = [float(row["component_share"]) for row in groups]
    summary = {"candidate_count": len(cases), "target_count": len({row['target_concept_or_cluster_id'] for row in cases}), "group_count": len(groups), "source_family_count": len({row['source_family_id'] for row in cases}), "largest_component_share": max(components, default=0.0), "leak_count": sum(int(row["leak_count"]) for row in audits), "target_coverage": round(len({row['target_concept_or_cluster_id'] for row in cases}) / max(len(by_target), 1), 6)}
    return cases, groups, audits, family_cases, open_cases, compound_cases, summary


def smoke_addendum() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    smoke = ROOT / "db" / "data" / "normalization-smoke"
    support = {row["target_concept_id"]: row for row in read_tsv(smoke / "SMOKE_TARGET_SUPPORT.tsv")}
    selected = [row for row in read_tsv(smoke / "SMOKE_PREDICTION_RECEIPT.tsv") if row["configuration_id"] == "B2_CHAR_LINEAR" and row["evaluation_id"] == "TEST" and row["split"] == "TEST" and row["prediction_rank"] == "1"]
    categories = Counter()
    corrections: dict[str, dict[str, Any]] = {}
    for row in selected:
        target = row["true_target_concept_id"]
        train_count = int(support[target]["train_output_count"])
        if train_count == 0:
            category = "UNSEEN_TARGET_OPEN_SET"
        elif row["seen_form_status"] == "UNSEEN_CLEANED_LEXICAL_FORM":
            category = "UNSEEN_FORM_KNOWN_TARGET"
        else:
            category = "SEEN_FORM_KNOWN_TARGET"
        categories[category] += 1
        corrections[target] = {"target_concept_id": target, "train_output_count": train_count, "test_output_count": support[target]["test_output_count"], "historical_support_status": support[target]["support_status"], "corrected_status": "TRAIN_UNSUPPORTED_TARGET" if train_count == 0 and int(support[target]["test_output_count"]) else "TRAIN_SUPPORTED_TARGET", "classification_basis": "BATCH6_TARGET_TRAIN_TEST_RECONCILIATION"}
    return {"contract_version": "batch6.smoke-benchmark-interpretation-addendum.v1", "historical_artifacts_modified": False, "SMOKE_FINAL_STATUS": "ENGINEERING_SMOKE_PASS_LEXICAL_MEMORIZATION_ONLY", "SEEN_FORM_KNOWN_TARGET_OUTPUT_COUNT": categories["SEEN_FORM_KNOWN_TARGET"], "UNSEEN_FORM_KNOWN_TARGET_OUTPUT_COUNT": categories["UNSEEN_FORM_KNOWN_TARGET"], "UNSEEN_TARGET_OPEN_SET_OUTPUT_COUNT": categories["UNSEEN_TARGET_OPEN_SET"], "TRAIN_UNSUPPORTED_TARGET_COUNT": sum(row["corrected_status"] == "TRAIN_UNSUPPORTED_TARGET" for row in corrections.values()), "explicit_test_only_targets": "|".join(sorted(row["target_concept_id"] for row in corrections.values() if row["corrected_status"] == "TRAIN_UNSUPPORTED_TARGET")), "interpretation": "The two test unseen forms are unseen targets, not known-target cross-form cases."}, sorted(corrections.values(), key=lambda row: row["target_concept_id"])


def review_packets(clusters: list[Mapping[str, Any]], benchmark_cases: list[Mapping[str, Any]], raw_by_id: Mapping[str, str], atoms: list[Mapping[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    case_clusters = {row["target_concept_or_cluster_id"] for row in benchmark_cases}
    ranked = sorted(clusters, key=lambda row: (-int(row["concept_cluster_id"] in case_clusters), -int(row["review_priority"]), row["concept_cluster_id"]))[:200]
    public = []
    restricted = []
    atom_by_cluster = defaultdict(list)
    for atom in atoms:
        atom_by_cluster[atom["concept_cluster_id"]].append(atom)
    for index, cluster in enumerate(ranked, 1):
        item_id = stable_id("cross-form-review", cluster["concept_cluster_id"])
        action = "DEFER_TO_SENSORY_EXPERT" if cluster["mapping_state"] in {"AMBIGUOUS_CONCEPT_BOUNDARY", "CROSS_LANGUAGE_REVIEW_REQUIRED"} else "MAP_TO_EXISTING"
        public.append({"review_item_id": item_id, "review_rank": index, "concept_cluster_id": cluster["concept_cluster_id"], "mapping_state": cluster["mapping_state"], "assertion_support": cluster["assertion_support"], "effective_record_support": cluster["effective_record_support"], "source_family_ids": cluster["source_family_ids"], "year_ids": cluster["year_ids"], "suggested_action": action, "restricted_pointer": f"restricted://batch6_semantic_review/{item_id}", "project_owner_decision": "", "decision_reason": "", "reviewer_id": "", "reviewed_at": ""})
        representative = sorted(atom_by_cluster[cluster["concept_cluster_id"]], key=lambda row: row["cleaned_output_atom_id"])[0]
        restricted.append({"review_item_id": item_id, "concept_cluster_id": cluster["concept_cluster_id"], "restricted_source_pointer": f"restricted://source-assertion/{representative['descriptor_assertion_id']}", "source_native_form": raw_by_id.get(representative["descriptor_assertion_id"], "NA_RESTRICTED_TEXT_RETAINED_IN_PRIOR_OWNER_STORE"), "candidate_relation_or_mapping_state": cluster["mapping_state"], "candidate_canonical_concepts": cluster["canonical_concept_ids"], "source_family_ids": cluster["source_family_ids"], "publication_context": representative["publication_layer"], "reviewer_decision": ""})
    import_rows = [{"review_item_id": row["review_item_id"], "project_owner_decision": "", "canonical_concept_id": "", "merge_target_cluster_id": "", "split_instruction": "", "decision_reason": "", "reviewer_id": "", "reviewed_at": ""} for row in public]
    return public, import_rows, restricted


def human_packet(cases: list[Mapping[str, Any]], family_cases: list[Mapping[str, Any]], open_cases: list[Mapping[str, Any]], compound_cases: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pool = []
    for row in cases:
        if row["split"] == "TEST":
            pool.append((row["surface"], row.get("source_family_id", ""), row))
    for row in family_cases:
        if row["split"] == "TEST":
            pool.append((row["surface"], row.get("held_out_source_family_id", ""), row))
    pool.extend((row["surface"], "OPEN_SET", row) for row in open_cases)
    pool.extend((row["surface"], "COMPOUND_MODIFIER", row) for row in compound_cases)
    buckets: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for surface, family, row in pool:
        buckets[(surface, family)].append(row)
    for values in buckets.values():
        values.sort(key=lambda row: sha_text(json.dumps(dict(row), sort_keys=True)))
    selected: list[tuple[str, str, Mapping[str, Any]]] = []
    positions = Counter()
    keys = sorted(buckets)
    while len(selected) < 500:
        progressed = False
        for key in keys:
            if positions[key] < len(buckets[key]):
                selected.append((key[0], key[1], buckets[key][positions[key]]))
                positions[key] += 1
                progressed = True
                if len(selected) == 500:
                    break
        if not progressed:
            break
    return [{"human_benchmark_item_id": stable_id("human-cross-form", f"{surface}\x1f{family}\x1f{index}\x1f{json.dumps(dict(row), sort_keys=True)}"), "item_sequence": index, "surface": surface, "source_family_stratum": family, "public_case_pointer": row.get("benchmark_case_id", ""), "cleaned_output_atom_id": row.get("cleaned_output_atom_id", ""), "restricted_context_pointer": f"restricted://batch6_semantic_review/human/{index}", "reviewer_id": "", "reviewer_decision": "", "reviewed_at": "", "review_note": ""} for index, (surface, family, row) in enumerate(selected, 1)]


def init_post40_if_absent() -> None:
    POST40.mkdir(parents=True, exist_ok=True)
    files = {
        "POST40K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv": ["extension_batch_id", "descriptor_assertion_id", "frozen_snapshot_member"],
        "POST40K_PUBLIC_ARTIFACT_RECEIPT.tsv": ["source_route_id", "source_url", "restricted_relative_path"],
        "POST40K_SOURCE_ROUTE_DISCOVERY.tsv": ["source_family_id", "source_route_id", "discovery_lane", "disposition"],
    }
    for name, fields in files.items():
        path = POST40 / name
        if not path.exists():
            write_tsv(path, fields, [])
    manifest = POST40 / "POST40K_EXTENSION_MANIFEST.json"
    if not manifest.exists():
        write_json(manifest, {"contract_version": "post40k-extension-staging.v1", "run": False, "reason": "BATCH6_SEMANTIC_CONSTRUCTION_INITIALIZATION_NO_LIVE_ACQUISITION_YET", "cursor_start": "archive-page=100;detail-index=3;url=https://farmdirectory.cupofexcellence.org/listing/2-la-lucuma-peru-2023/", "extension_isolated_from_frozen_snapshot": True, "total_candidate_count": 40030})


def main() -> int:
    decisions, atoms, raw_by_id = combined_cleaned()
    clusters = concept_clusters(atoms)
    form_nodes, concept_nodes, edges, evidence, relation_candidates, rejections = semantic_graph(atoms, clusters)
    cases, groups, audits, family_cases, open_cases, compound_cases, benchmark_summary = benchmark(atoms)
    addendum, correction = smoke_addendum()
    review, review_import, restricted = review_packets(clusters, cases, raw_by_id, atoms)
    human = human_packet(cases, family_cases, open_cases, compound_cases)
    if len(human) < 500:
        raise RuntimeError(f"human benchmark packet underfilled: {len(human)}")
    init_post40_if_absent()
    post40_manifest = json.loads((POST40 / "POST40K_EXTENSION_MANIFEST.json").read_text())
    if not post40_manifest.get("run", False):
        semantic_yield = [{"route_scope": "POST40K_NOT_YET_ACQUIRED", "new_cleaned_forms": "NA_POST40K_STAGING_EMPTY", "new_known_target_forms": "NA_POST40K_STAGING_EMPTY", "new_cross_family_target_overlaps": "NA_POST40K_STAGING_EMPTY", "assertion_count": 0, "source": "POST40K_EXTENSION"}]
        write_tsv(POST40 / "POST40K_SEMANTIC_YIELD.tsv", list(semantic_yield[0]), semantic_yield)
        post40_files = sorted(path for path in POST40.iterdir() if path.is_file() and path.name != "SHA256SUMS")
        (POST40 / "SHA256SUMS").write_text("".join(f"{sha_file(path)}  {path.name}\n" for path in post40_files), encoding="utf-8")
    source_fields = list(decisions[0])
    atom_fields = list(atoms[0])
    write_tsv(CURRENT / "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv", source_fields, decisions)
    write_tsv(CURRENT / "CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv", atom_fields, atoms)
    snapshot_content = "\n".join("\t".join((row["descriptor_assertion_id"], row["source_artifact_sha256"], row["effective_record_id"], row["coffee_identity_id"], row["atomic_source_text_sha256"])) for row in decisions)
    snapshot = {"contract_version": "candidate-40k-snapshot-manifest.v1", "snapshot_version": SNAPSHOT_VERSION, "immutable": True, "snapshot_role": "ACQUISITION_CHECKPOINT_NOT_TRAINING_CORPUS", "candidate_30k_snapshot_sha256": sha_file(CURRENT / "CANDIDATE_30K_SNAPSHOT_MANIFEST.json"), "post30k_extension_manifest_sha256": sha_file(POST30 / "POST30K_EXTENSION_MANIFEST.json"), "snapshot_content_sha256": sha_text(snapshot_content), "source_assertion_count": len(decisions), "effective_record_count": len({row['effective_record_id'] for row in decisions}), "source_family_count": len({row['source_family_id'] for row in decisions}), "source_ledger": "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv", "source_ledger_sha256": sha_file(CURRENT / "CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv"), "exact_coe_continuation_cursor": json.loads((POST30 / "POST30K_EXTENSION_MANIFEST.json").read_text())["cursor_end"], "restricted_ledger_root_hash": json.loads((POST30 / "POST30K_EXTENSION_MANIFEST.json").read_text())["restricted_assertion_ledger_sha256"], "training_corpus_frozen": False, "model_eligible_corpus_frozen": False, "schema_changed": False, "new_migration_count": 0}
    write_json(CURRENT / "CANDIDATE_40K_SNAPSHOT_MANIFEST.json", snapshot)
    write_json(CURRENT / "CLEANED_40K_MANIFEST.json", {"cleaned_view_version": CLEANED_VIEW_VERSION, "cleaner_version": CLEANER_VERSION, "source_assertion_count": len(decisions), "valid_source_assertion_count": sum(row['source_assertion_disposition'] in VALID_SOURCE for row in decisions), "output_atom_count": len(atoms), "record_unique_output_atom_count": len({(row['effective_record_id'], target_id(row)) for row in atoms if row['counts_as_cleaned_descriptor_output'] == 'true' and row['counts_as_record_unique_descriptor'] == 'true'}), "source_assertion_reconciliation_pass": sum(int(row['cleaned_output_atom_count']) for row in decisions) == len(atoms), "candidate_40k_snapshot_sha256": sha_file(CURRENT / "CANDIDATE_40K_SNAPSHOT_MANIFEST.json")})
    write_tsv(CURRENT / "SEMANTIC_FORM_NODE.tsv", list(form_nodes[0]), form_nodes)
    write_tsv(CURRENT / "SEMANTIC_CONCEPT_NODE.tsv", list(concept_nodes[0]), concept_nodes)
    write_tsv(CURRENT / "SEMANTIC_RELATION_EDGE.tsv", list(edges[0]), edges)
    write_tsv(CURRENT / "SEMANTIC_RELATION_EVIDENCE.tsv", list(evidence[0]), evidence)
    candidate_fields = ["semantic_relation_candidate_id", "semantic_relation_id", "relation_type", "candidate_reason", "review_required"]
    write_tsv(CURRENT / "SEMANTIC_RELATION_CANDIDATE.tsv", candidate_fields, relation_candidates)
    write_tsv(CURRENT / "SEMANTIC_RELATION_REJECTION.tsv", ["semantic_relation_rejection_id", "relation_type", "reason", "source"], rejections)
    relation_counts = Counter(row["relation_type"] for row in edges)
    authority_counts = Counter(row["semantic_evidence_authority"] for row in edges)
    summary_metrics = {
        "semantic_form_node_count": len(form_nodes),
        "semantic_concept_node_count": len(concept_nodes),
        "semantic_relation_edge_count": len(edges),
        "s0_relation_count": authority_counts["S0_DETERMINISTIC_ORTHOGRAPHIC"],
        "s1_relation_count": authority_counts["S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS"],
        "s2_relation_count": 0,
        "s3_relation_candidate_count": len(relation_candidates),
        "s4_project_owner_reviewed_relation_count": 0,
        "s5_sensory_expert_adjudicated_relation_count": 0,
        **{f"{name.lower()}_edge_count": count for name, count in relation_counts.items()},
    }
    summary_rows = [
        {"metric": key, "value": value}
        for key, value in sorted(summary_metrics.items())
    ]
    write_tsv(CURRENT / "SEMANTIC_RELATION_SUMMARY.tsv", ["metric", "value"], summary_rows)
    write_tsv(CURRENT / "CONCEPT_CLUSTER_V2.tsv", list(clusters[0]), clusters)
    consolidation = [{"cleaned_output_atom_id": atom["cleaned_output_atom_id"], "concept_cluster_id": atom["concept_cluster_id"], "cleaned_form_id": atom["cleaned_form_id"], "source_native_form_id": atom["source_native_form_id"], "mapping_state": atom["mapping_state"], "canonical_concept_id": atom["canonical_concept_id"], "mapping_authority": atom["normalization_authority"], "base_form_sha256": atom["base_form_sha256"], "modifier_form_sha256s": atom["modifier_form_sha256s"], "component_concept_ids": atom["component_concept_ids"], "ontology_auto_promotion": "false", "human_reviewed": "false", "sensory_expert_adjudicated": "false"} for atom in atoms]
    write_tsv(CURRENT / "ONTOLOGY_CONSOLIDATION_V2.tsv", list(consolidation[0]), consolidation)
    modifier = [{"cleaned_output_atom_id": atom["cleaned_output_atom_id"], "base_form_sha256": atom["base_form_sha256"], "modifier_form_sha256": value, "relation_type": "MODIFIES", "evidence_authority": "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "review_required": "true"} for atom in atoms for value in split_pipe(atom["modifier_form_sha256s"])]
    compound = [{"cleaned_output_atom_id": atom["cleaned_output_atom_id"], "component_concept_id": value, "relation_type": "COMPONENT_OF", "evidence_authority": "S3_MULTI_SOURCE_MACHINE_CANDIDATE", "review_required": "true"} for atom in atoms for value in split_pipe(atom["component_concept_ids"])]
    write_tsv(CURRENT / "MODIFIER_COMPONENT.tsv", ["cleaned_output_atom_id", "base_form_sha256", "modifier_form_sha256", "relation_type", "evidence_authority", "review_required"], modifier)
    write_tsv(CURRENT / "COMPOUND_COMPONENT.tsv", ["cleaned_output_atom_id", "component_concept_id", "relation_type", "evidence_authority", "review_required"], compound)
    write_tsv(CURRENT / "SEMANTIC_REFERENCE_SOURCE.tsv", ["semantic_reference_source_id", "publisher", "version_or_date", "language", "term_or_term_hash", "definition_or_restricted_pointer", "relation_supported", "evidence_level", "rights_status", "citation_or_locator", "artifact_hash"], [{"semantic_reference_source_id": "semantic-reference.existing-governed-ontology-v1", "publisher": "Coffee Flavor Atlas project", "version_or_date": CLEANER_VERSION, "language": "en", "term_or_term_hash": "NA_GOVERNED_MAPPING_RULE_REFERENCE", "definition_or_restricted_pointer": "restricted://governed-ontology-and-approved-alias-rules", "relation_supported": "EXACT_EQUIVALENT|APPROVED_ALIAS_OF|MORPHOLOGICAL_VARIANT_OF", "evidence_level": "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "rights_status": "PROJECT_GOVERNED_CONTENT", "citation_or_locator": "db/scripts/build-batch4-cleaning-staging.py", "artifact_hash": sha_file(BUILDER_PATH)}])
    write_tsv(CURRENT / "CROSS_FORM_BENCHMARK_CANDIDATE.tsv", list(cases[0]), cases)
    write_tsv(CURRENT / "CROSS_FORM_BENCHMARK_GROUP.tsv", list(groups[0]), groups)
    write_json(CURRENT / "CROSS_FORM_BENCHMARK_SPLIT_MANIFEST.json", {"contract_version": "batch6.cross-form-benchmark-candidate.v1", "model_run": False, "benchmark_tiers": ["GOVERNED_CROSS_FORM_BENCHMARK_CANDIDATE", "REVIEW_REQUIRED_CROSS_FORM_BENCHMARK_CANDIDATE"], "governed_relation_authorities": ["S0_DETERMINISTIC_ORTHOGRAPHIC", "S1_EXISTING_GOVERNED_ONTOLOGY_OR_ALIAS", "S2_EXPLICIT_PROFESSIONAL_LEXICON_OR_GLOSSARY"], "review_required_relation_authority": "S3_MULTI_SOURCE_MACHINE_CANDIDATE", **benchmark_summary})
    write_tsv(CURRENT / "CROSS_FORM_BENCHMARK_LEAKAGE_AUDIT.tsv", list(audits[0]), audits)
    write_tsv(CURRENT / "CROSS_FAMILY_SHARED_TARGET_BENCHMARK.tsv", list(family_cases[0]), family_cases)
    write_tsv(CURRENT / "OPEN_SET_UNSEEN_TARGET_BENCHMARK.tsv", list(open_cases[0]), open_cases)
    write_tsv(CURRENT / "COMPOUND_MODIFIER_BENCHMARK.tsv", list(compound_cases[0]), compound_cases)
    write_json(CURRENT / "SMOKE_BENCHMARK_INTERPRETATION_ADDENDUM.json", addendum)
    write_tsv(CURRENT / "SMOKE_TARGET_SUPPORT_CORRECTION.tsv", list(correction[0]), correction)
    write_tsv(CURRENT / "CROSS_FORM_OWNER_REVIEW_PACKET.tsv", list(review[0]), review)
    write_tsv(CURRENT / "CROSS_FORM_OWNER_REVIEW_IMPORT_TEMPLATE.tsv", list(review_import[0]), review_import)
    write_tsv(CURRENT / "HUMAN_CROSS_FORM_BENCHMARK_TEMPLATE.tsv", list(human[0]), human)
    RESTRICTED_REVIEW.mkdir(parents=True, exist_ok=True)
    write_tsv(RESTRICTED_REVIEW / "RESTRICTED_CROSS_FORM_OWNER_REVIEW_PACKET.tsv", list(restricted[0]), restricted)
    atoms_by_family: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    target_families: dict[str, set[str]] = defaultdict(set)
    for atom in atoms:
        atoms_by_family[atom["source_family_id"]].append(atom)
        if atom["canonical_concept_id"]:
            target_families[target_id(atom)].add(atom["source_family_id"])
    route_yield = []
    for family, rows in sorted(atoms_by_family.items()):
        route_yield.append({"source_family_id": family, "deinflated_source_assertion_count": len({atom['descriptor_assertion_id'] for atom in rows}), "cleaned_lexical_form_count": len({atom['cleaned_form_id'] for atom in rows}), "known_target_form_count": len({atom['cleaned_form_id'] for atom in rows if atom['canonical_concept_id']}), "cross_family_target_overlap_count": len({target_id(atom) for atom in rows if len(target_families[target_id(atom)]) > 1}), "purpose_permitted_assertion_count": sum(atom['rights_noncommercial_model_research'] in PERMITTED for atom in rows), "semantic_novelty_rate": round(len({atom['cleaned_form_id'] for atom in rows}) / max(len({atom['descriptor_assertion_id'] for atom in rows}), 1), 6)})
    write_tsv(CURRENT / "SEMANTIC_SOURCE_ROUTE_YIELD.tsv", list(route_yield[0]), route_yield)
    distribution = [{"metric": "NEW_CLEANED_FORMS_PER_1000_ASSERTIONS", "value": round(len({atom['cleaned_form_id'] for atom in atoms if atom['corpus_segment'] == 'POST30K_EXTENSION'}) / 10020 * 1000, 6)}, {"metric": "NEW_KNOWN_TARGET_FORMS_PER_1000_ASSERTIONS", "value": round(len({atom['cleaned_form_id'] for atom in atoms if atom['corpus_segment'] == 'POST30K_EXTENSION' and atom['canonical_concept_id']}) / 10020 * 1000, 6)}, {"metric": "NEW_CROSS_FAMILY_TARGET_OVERLAPS_PER_1000_ASSERTIONS", "value": "NA_REQUIRES_POST40K_NON_COE_ROUTE_FOR_COMPARABLE_INCREMENT"}]
    write_tsv(CURRENT / "SEMANTIC_NOVELTY_DISTRIBUTION.tsv", ["metric", "value"], distribution)
    existing = json.loads((CURRENT / "CURRENT_DATA_MANIFEST.json").read_text())
    valid_atoms = [atom for atom in atoms if atom['counts_as_cleaned_descriptor_output'] == 'true']
    state_counts = Counter(cluster['mapping_state'] for cluster in clusters)
    existing.update({"generated_date": "2026-08-30", "batch6_generator_version": GENERATOR_VERSION, "phase_status": "CLEANED_40K_SEMANTIC_LAYER_REVIEW_REQUIRED", "final_data_decision": "CLEANED_40K_SEMANTIC_LAYER_AND_CROSS_FORM_BENCHMARK_CANDIDATES_NO_MODEL_RUN", "candidate_40k_snapshot_created": True, "candidate_40k_snapshot_version": SNAPSHOT_VERSION, "cleaned_40k_view_version": CLEANED_VIEW_VERSION, "cleaner_contract_version": CLEANER_VERSION, "training_corpus_frozen": False, "model_training_run": False, "schema_changed": False, "new_migration_count": 0, "batch6_metrics": {"cleaned_40k_valid_source_assertion_count": sum(row['source_assertion_disposition'] in VALID_SOURCE for row in decisions), "cleaned_40k_output_atom_count": len(valid_atoms), "cleaned_40k_lexical_form_count": len({atom['cleaned_form_id'] for atom in valid_atoms}), "concept_cluster_count": len(clusters), "genuine_ontology_candidate_cluster_count": state_counts['GENUINE_ONTOLOGY_CANDIDATE'], "semantic_relation_edge_count": len(edges), "cross_form_benchmark_candidate_count": len(cases), "cross_form_benchmark_ready": len(cases) > 0, "owner_review_packet_count": len(review), "human_benchmark_packet_count": len(human), "smoke_benchmark_addendum_created": True, "post40k_extension_run": post40_manifest.get('run', False), "post40k_net_new_deinflated_assertion_count": post40_manifest.get('net_new_deinflated_assertion_count', 0), "post40k_total_acquired_candidate_count": post40_manifest.get('total_candidate_count', 40030), "candidate_50k_checkpoint_reached": post40_manifest.get('checkpoint_50000_reached', False), "ml_model_run_count": 0}})
    excluded = {"CURRENT_DATA_MANIFEST.json", "SHA256SUMS"}
    existing["files"] = [{"path": path.name, "sha256": sha_file(path), "byte_count": path.stat().st_size, "data_row_count": data_rows(path)} for path in sorted(CURRENT.iterdir()) if path.is_file() and path.name not in excluded]
    write_json(CURRENT / "CURRENT_DATA_MANIFEST.json", existing)
    checksums = sorted(path for path in CURRENT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (CURRENT / "SHA256SUMS").write_text("".join(f"{sha_file(path)}  {path.name}\n" for path in checksums), encoding="utf-8")
    print(f"BATCH6_SEMANTIC_CORPUS_PASS sources={len(decisions)} atoms={len(atoms)} clusters={len(clusters)} relations={len(edges)} benchmark={len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
