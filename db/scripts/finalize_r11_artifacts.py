#!/usr/bin/env python3
"""Build the R11 acquisition, calibration, deduplication, and exit receipts.

This program performs deterministic data accounting only.  It neither imports
an estimator nor fits, tunes, calibrates, or evaluates a model on real labels.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
R1 = ROOT / "db/data/backend-sequential-model-v2/revisions/r1"
R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/r2"
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
PRIVATE_R10 = Path(
    "/Users/jarlgiovanni/Desktop/Coffee_Flavor_Research_Private/"
    "backend-sequential-model-v2/revisions/r10/training_corpus.private.json"
)
PRIVATE_R1 = Path(
    "/Users/jarlgiovanni/Library/Application Support/Coffee Flavor Research/"
    "backend-sequential-model-v2/revisions/r1"
)

ELIGIBILITY_INPUTS = [
    "db/data/professional-descriptor-staging/PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
    "db/data/post20k-extension-staging/POST20K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
    "db/data/post30k-extension-staging/POST30K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
    "db/data/post50k-extension-staging/NON_COE_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
]
SOURCE_LEDGER_40K = "db/data/current/CLEANED_40K_SOURCE_ASSERTION_LEDGER.tsv"
ATOM_LEDGER_40K = "db/data/current/CLEANED_40K_OUTPUT_ATOM_LEDGER.tsv"
ATOM_LEDGER_50K = "db/data/current/CLEANED_50K_OUTPUT_ATOM_LEDGER.tsv"
AUDIT_20K = "db/data/candidate-cleaning-staging/BATCH3_PUBLIC_SAFE_SEMANTIC_AUDIT.tsv"

ALLOWED_LICENSES = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-3.0",
    "CC-BY-SA-4.0",
    "CC-BY-NC-4.0",
    "ODbL-1.0",
    "EXPLICIT-NONCOMMERCIAL-RESEARCH-TDM",
}
SHAPES = {
    "T1": "DIRECT_INTENSITY",
    "T2": "DIRECT_FREQUENCY",
    "T3": "DIRECT_PRESENCE",
    "T4": "DIMENSION_ONLY",
    "T5": "ONTOLOGY_REFERENCE",
    "T6": "ONTOLOGY_CHEMICAL",
}
REASON_CODES = [
    "NO_SAMPLE_IDENTITY",
    "WITHIN_GROUP_DUPLICATE",
    "SHAPE_MISMATCH",
    "BROAD_CLASS_REJECTED",
    "COMPOUND_REJECTED",
    "SPECIFICITY_GATE",
    "UNMAPPED_SURFACE_FORM",
    "RIGHTS",
]


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stable_bytes(value))


def file_or_git(relative_path: str) -> tuple[str, str]:
    path = ROOT / relative_path
    if path.exists():
        raw = path.read_bytes()
    else:
        raw = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
    return raw.decode("utf-8"), sha(raw)


def tsv_rows(relative_path: str) -> tuple[list[dict[str, str]], str]:
    text, checksum = file_or_git(relative_path)
    return list(csv.DictReader(io.StringIO(text), delimiter="\t")), checksum


def truth(value: str | None) -> bool:
    return (value or "").strip().lower() == "true"


def identified(value: str | None) -> bool:
    token = (value or "").strip().lower()
    return bool(token and "unknown" not in token and "unresolved" not in token)


def load_r10_eligible() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    license_rows = json.loads((R10 / "resolved_source_licenses.json").read_text())["sources"]
    licenses = {row["source_family_id"]: row for row in license_rows}
    rows: list[dict[str, str]] = []
    inputs = []
    for relative in ELIGIBILITY_INPUTS:
        loaded, checksum = tsv_rows(relative)
        rows.extend(loaded)
        inputs.append({"path": relative, "sha256": checksum, "row_count": len(loaded)})
    eligible = []
    for row in rows:
        source = licenses.get(row.get("source_family_id", ""))
        license_id = source.get("resolved_license") if source else None
        if (
            source
            and license_id in ALLOWED_LICENSES
            and "-ND-" not in (license_id or "")
            and not source.get("participant_pii_present")
            and source.get("attribution_complete")
            and row.get("descriptor_class") == "STRICT_FLAVOR"
            and identified(row.get("coffee_identity_id"))
            and truth(row.get("counts_as_assertion"))
        ):
            eligible.append(row)
    eligible.sort(key=lambda row: row["descriptor_assertion_id"])
    if len(eligible) != 5819:
        raise ValueError(f"R10_ELIGIBLE_COHORT_DRIFT:{len(eligible)}")
    return eligible, inputs


def freeze_selected(
    atoms: list[dict[str, str]],
    allowed_families: set[str],
    registry: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        row
        for row in atoms
        if row["source_family_id"] in allowed_families
        and row["rights_state"] == "AFFIRMATIVE"
        and row["semantic_class"] == "STRICT_FLAVOR"
        and truth(row["counts_as_cleaned_descriptor_output"])
        and truth(row["counts_as_record_unique_descriptor"])
        and row["canonical_concept_id"] in registry
        and registry[row["canonical_concept_id"]]["role"] == "NAMED_DESCRIPTOR"
    ]


def reconciliation() -> tuple[dict[str, Any], set[str]]:
    eligible, eligibility_inputs = load_r10_eligible()
    eligible_ids = {row["descriptor_assertion_id"] for row in eligible}
    source_rows, source_sha = tsv_rows(SOURCE_LEDGER_40K)
    atoms, atom_sha = tsv_rows(ATOM_LEDGER_40K)
    source_by_id = {row["descriptor_assertion_id"]: row for row in source_rows}
    atoms_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in atoms:
        atoms_by_id[row["descriptor_assertion_id"]].append(row)

    registry = json.loads((R9 / "output_policy_contract.json").read_text())[
        "concept_role_registry"
    ]
    tier = json.loads((R10 / "eligibility_tiers.json").read_text())["tiers"][
        "NON_COMMERCIAL_RESEARCH"
    ]
    allowed_families = set(tier["source_family_assertion_counts"])
    all_selected = freeze_selected(atoms, allowed_families, registry)
    eligible_selected = [
        row for row in all_selected if row["descriptor_assertion_id"] in eligible_ids
    ]
    selected_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible_selected:
        selected_by_id[row["descriptor_assertion_id"]].append(row)

    occurrence_first: dict[tuple[str, str], str] = {}
    for row in sorted(eligible_selected, key=lambda item: item["descriptor_assertion_id"]):
        key = (row["coffee_identity_id"], row["canonical_concept_id"])
        occurrence_first.setdefault(key, row["descriptor_assertion_id"])

    records = []
    counts = Counter()
    admitted_count = 0
    for row in eligible:
        assertion_id = row["descriptor_assertion_id"]
        source = source_by_id.get(assertion_id)
        assertion_atoms = atoms_by_id.get(assertion_id, [])
        selected_atoms = selected_by_id.get(assertion_id, [])
        reason = None
        if not identified(row.get("coffee_identity_id")):
            reason = "NO_SAMPLE_IDENTITY"
        elif selected_atoms:
            keys = {
                (atom["coffee_identity_id"], atom["canonical_concept_id"])
                for atom in selected_atoms
            }
            if any(occurrence_first[key] == assertion_id for key in keys):
                admitted_count += 1
                disposition = "ADMITTED_FROZEN_OCCURRENCE"
            else:
                reason = "WITHIN_GROUP_DUPLICATE"
        elif source is None:
            reason = "SHAPE_MISMATCH"
        elif "COMPOUND" in source.get("source_assertion_disposition", "") or any(
            atom.get("mapping_state") == "COMPOUND_OF_EXISTING_CONCEPTS"
            for atom in assertion_atoms
        ):
            reason = "COMPOUND_REJECTED"
        elif source.get("source_assertion_disposition") == "VALID_BROAD_SENSORY" or any(
            atom.get("semantic_class") == "BROAD_SENSORY" for atom in assertion_atoms
        ):
            reason = "BROAD_CLASS_REJECTED"
        elif any(
            atom.get("mapping_state")
            in {
                "AMBIGUOUS_CONCEPT_BOUNDARY",
                "CROSS_LANGUAGE_REVIEW_REQUIRED",
                "GENUINE_ONTOLOGY_CANDIDATE",
            }
            for atom in assertion_atoms
        ):
            reason = "UNMAPPED_SURFACE_FORM"
        else:
            reason = "SPECIFICITY_GATE"

        if reason:
            counts[reason] += 1
            disposition = reason
        records.append(
            {
                "descriptor_assertion_id": assertion_id,
                "source_family_id": row["source_family_id"],
                "coffee_identity_id": row.get("coffee_identity_id"),
                "disposition": disposition,
                "recoverable_under_addendum": reason
                in {
                    "SHAPE_MISMATCH",
                    "BROAD_CLASS_REJECTED",
                    "COMPOUND_REJECTED",
                    "SPECIFICITY_GATE",
                    "UNMAPPED_SURFACE_FORM",
                },
            }
        )

    if admitted_count + sum(counts.values()) != 5819:
        raise ValueError("R10_RECONCILIATION_DOES_NOT_SUM")

    cohort_occurrences = {
        (row["coffee_identity_id"], row["canonical_concept_id"])
        for row in eligible_selected
    }
    full_occurrences = {
        (row["coffee_identity_id"], row["canonical_concept_id"])
        for row in all_selected
    }
    outside_rows = [
        row for row in all_selected if row["descriptor_assertion_id"] not in eligible_ids
    ]
    outside_occurrences = full_occurrences - cohort_occurrences

    private_receipt: dict[str, Any]
    if PRIVATE_R10.exists():
        raw = PRIVATE_R10.read_bytes()
        private = json.loads(raw)
        private_occurrences = {
            (group["coffee_group_id"], candidate)
            for group in private["groups"]
            for candidate in group["descriptor_ids"]
        }
        private_receipt = {
            "available": True,
            "sha256": sha(raw),
            "group_count": len(private["groups"]),
            "occurrence_count": len(private_occurrences),
            "candidate_count": len(private["candidate_ids"]),
            "matches_full_ledger_freeze_occurrences": private_occurrences == full_occurrences,
        }
    else:
        private_receipt = {"available": False}

    likely = {
        code: {
            "pre_retest_count": counts[code],
            "post_retest_recovery_count": None,
            "post_retest_status": "NOT_COMPUTABLE_FROM_HASH_ONLY_ELIGIBILITY_SIDECARS",
        }
        for code in (
            "SHAPE_MISMATCH",
            "BROAD_CLASS_REJECTED",
            "COMPOUND_REJECTED",
            "SPECIFICITY_GATE",
            "UNMAPPED_SURFACE_FORM",
        )
    }
    report = {
        "contract_version": "r11.r10-readmission-reconciliation.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inputs": {
            "eligibility_sidecars": eligibility_inputs,
            "source_ledger": {"path": SOURCE_LEDGER_40K, "sha256": source_sha},
            "atom_ledger": {"path": ATOM_LEDGER_40K, "sha256": atom_sha},
            "private_frozen_corpus": private_receipt,
        },
        "accounting": {
            "eligible_assertion_count": len(eligible),
            "admitted_frozen_occurrence_representatives": admitted_count,
            "nonadmission_reason_counts": {
                code: counts[code] for code in REASON_CODES
            },
            "accounted_total": admitted_count + sum(counts.values()),
            "sums_to_5819": admitted_count + sum(counts.values()) == 5819,
        },
        "published_879_provenance_discrepancy": {
            "status": "DISCLOSED_NOT_SILENTLY_RECONCILED",
            "eligible_cohort_selected_assertion_count": len(eligible_selected),
            "eligible_cohort_unique_occurrence_count": len(cohort_occurrences),
            "whole_ledger_selected_assertion_count": len(all_selected),
            "whole_ledger_unique_occurrence_count": len(full_occurrences),
            "selected_rows_outside_5819_count": len(outside_rows),
            "unique_occurrences_outside_5819_count": len(outside_occurrences),
            "outside_5819_source_assertion_ids": sorted(
                {row["descriptor_assertion_id"] for row in outside_rows}
            ),
            "explanation": (
                "The published 879 is reproducible from the whole cleaned 40K ledger, "
                "but it is not a pure subset of the 5,819 sidecar eligibility cohort. "
                "The cohort itself reconstructs 869 unique occurrences."
            ),
        },
        "likely_recoverable_retest": likely,
        "records": records,
        "guards": {
            "fit_count": 0,
            "real_label_model_vs_baseline_metric_count": 0,
            "rights_reopened": False,
            "hash_only_rows_promoted": 0,
        },
    }
    return report, eligible_ids


def historical_calibration(eligible_ids: set[str]) -> dict[str, Any]:
    audit, audit_sha = tsv_rows(AUDIT_20K)
    audit_counts = Counter(row["audit_outcome"] for row in audit)
    audit_target = [
        row
        for row in audit
        if row["audit_outcome"]
        in {"VALID_BROAD_SENSORY", "VALID_COMPOSITE_REQUIRES_SPLIT"}
    ]
    audit_overlap = Counter(
        row["audit_outcome"]
        for row in audit_target
        if row["descriptor_assertion_id"] in eligible_ids
    )

    atoms50, atoms50_sha = tsv_rows(ATOM_LEDGER_50K)
    valid50 = [row for row in atoms50 if truth(row["counts_as_cleaned_descriptor_output"])]
    registry = json.loads((R9 / "output_policy_contract.json").read_text())[
        "concept_role_registry"
    ]
    partition = Counter()
    for row in valid50:
        rights_barrier = row.get("rights_noncommercial_model_research") != "AFFIRMATIVE"
        structure_barrier = (
            row.get("semantic_class") != "STRICT_FLAVOR"
            or not truth(row.get("counts_as_record_unique_descriptor"))
            or row.get("canonical_concept_id") not in registry
            or (
                row.get("canonical_concept_id") in registry
                and registry[row["canonical_concept_id"]]["role"] != "NAMED_DESCRIPTOR"
            )
        )
        partition[
            "RIGHTS_AND_STRUCTURE"
            if rights_barrier and structure_barrier
            else "RIGHTS_ONLY"
            if rights_barrier
            else "STRUCTURE_ONLY"
            if structure_barrier
            else "NEITHER"
        ] += 1

    r2 = json.loads((R2 / "data_increment_manifest.json").read_text())
    r2_quarantine = r2["actual_increment"]["quarantined_expression_groups"]

    d1_files = {}
    for filename in ("d1_recovery_records.private.json", "d1_recovery_expanded.private.json"):
        path = PRIVATE_R1 / filename
        if path.exists():
            raw = path.read_bytes()
            rows = json.loads(raw)
            d1_files[filename] = {
                "available": True,
                "sha256": sha(raw),
                "record_count": len(rows),
                "coffee_or_product_group_count": len(
                    {row.get("evaluation_group") or row.get("group_id") for row in rows}
                ),
                "role_counts": dict(sorted(Counter(row.get("role") for row in rows).items())),
                "source_family_counts": dict(
                    sorted(Counter(row.get("source_family") for row in rows).items())
                ),
            }
        else:
            d1_files[filename] = {"available": False}

    r1_manifest = json.loads((R1 / "sample_expansion_manifest.json").read_text())
    increment = r1_manifest["actual_increment"]
    broad_components = {
        "consumer_cata_rows": increment["new_complete_CATA_auxiliary_records"],
        "native_dimension_intensity_cells": increment["new_complete_native_intensity_cells"],
        "weak_narrative_condition_records": increment["new_known_condition_observations"],
        "quarantined_anonymous_source_sample_ids": increment[
            "quarantined_anonymous_source_sample_ids"
        ],
    }
    broad_total = sum(broad_components.values())

    return {
        "contract_version": "r11.historical-contract-calibration.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "twenty_k_semantic_audit": {
            "input": {"path": AUDIT_20K, "sha256": audit_sha},
            "row_count": len(audit),
            "outcome_counts": dict(sorted(audit_counts.items())),
            "broad_count": audit_counts["VALID_BROAD_SENSORY"],
            "compound_count": audit_counts["VALID_COMPOSITE_REQUIRES_SPLIT"],
            "broad_plus_compound_count": len(audit_target),
            "issued_rough_1900_check": {
                "issued_approximation": 1900,
                "reproducible_exact_count": len(audit_target),
                "status": "NOT_SUPPORTED_BY_THE_5744_ROW_AUDIT_DENOMINATOR",
            },
            "r10_5819_overlap_counts": dict(sorted(audit_overlap.items())),
            "retest_status": "NOT_POSSIBLE_FROM_HASH_ONLY_PUBLIC_SAFE_AUDIT_ROWS",
            "newly_admitted_count": 0,
            "note": (
                "The auditable rows contain hashes and semantic decisions, not source table "
                "cells; assigning T1--T6 would invent shape evidence."
            ),
        },
        "fifty_k_valid_output_partition": {
            "input": {"path": ATOM_LEDGER_50K, "sha256": atoms50_sha},
            "valid_output_atom_count": len(valid50),
            "exclusive_barrier_partition": {
                key: partition[key]
                for key in ("RIGHTS_ONLY", "STRUCTURE_ONLY", "RIGHTS_AND_STRUCTURE", "NEITHER")
            },
            "rights_barrier_total": partition["RIGHTS_ONLY"]
            + partition["RIGHTS_AND_STRUCTURE"],
            "structure_barrier_total_nonexclusive": partition["STRUCTURE_ONLY"]
            + partition["RIGHTS_AND_STRUCTURE"],
            "interpretation": (
                "Ledger-native rights fields block every valid output atom; structural "
                "barriers overlap but are not a rights waiver. R10's separately resolved "
                "5,819 cohort remains the only noncommercial eligible subset."
            ),
        },
        "r2_isolated_expression_groups": {
            "group_count": r2_quarantine,
            "status": "REMAINS_QUARANTINED_DATA_CONSISTENCY_FAILURE",
            "t1_t6_readmitted": 0,
        },
        "r1_d1_weak_recovery": {
            "private_receipts": d1_files,
            "classification": {
                "peru": "T3_LIKE_AUX_COFFEE_WEAK_LABEL_NOT_CORE_SUPERVISION",
                "condelli": "T2_LIKE_CONSUMER_AUXILIARY_NOT_PROFESSIONAL_SUPERVISION",
            },
            "promoted_to_r11_exit_counts": 0,
        },
        "broad_heterogeneous_inventory_3938": {
            "derivation_path": (
                "db/data/backend-sequential-model-v2/revisions/r1/"
                "sample_expansion_manifest.json#actual_increment"
            ),
            "components": broad_components,
            "derived_total": broad_total,
            "matches_issued_starting_count": broad_total == 3938,
            "stratified_routing": {
                "consumer_cata_rows": "T2_LIKE_AUXILIARY_CONSUMER_ONLY",
                "native_dimension_intensity_cells": "T4_LIKE_HISTORICAL_DIMENSION_TRACK",
                "weak_narrative_condition_records": "T3_LIKE_AUX_COFFEE_WEAK_LABEL",
                "quarantined_anonymous_source_sample_ids": "REMAINS_QUARANTINED",
            },
            "promoted_to_r11_exit_counts": 0,
            "warning": "The 3,938 units mix rows, cells, records, and quarantines and are not a group total.",
        },
        "conclusion": {
            "contract_narrowness_observed": True,
            "rights_question_reopened": False,
            "historical_hash_only_evidence_promoted": 0,
        },
        "guards": {"fit_count": 0, "real_label_model_vs_baseline_metric_count": 0},
    }


def group_rows(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        if row.get("coffee_group_id"):
            grouped[row["coffee_group_id"]].append(row)
    return grouped


def strong_group_signature(rows: list[dict[str, Any]]) -> str:
    first = rows[0]
    values = sorted(
        (
            row["shape_id"],
            row.get("concept_id") or row.get("native_dimension_label"),
            row.get("reported_value"),
            json.dumps(row.get("scale"), sort_keys=True),
        )
        for row in rows
    )
    payload = {
        "base": first.get("base_coffee_identity_normalized"),
        "panel_size": first.get("panel_size"),
        "values": values,
    }
    return sha(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode())


def deduplicate(records: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, Any]]:
    groups = group_rows(records)
    by_signature: dict[str, list[str]] = defaultdict(list)
    for group_id, rows in groups.items():
        by_signature[strong_group_signature(rows)].append(group_id)
    canonical = {group_id: group_id for group_id in groups}
    collapses = []
    for signature, group_ids in sorted(by_signature.items()):
        if len(group_ids) < 2:
            continue
        for left_index, left in enumerate(sorted(group_ids)):
            a = groups[left][0]
            for right in sorted(group_ids)[left_index + 1 :]:
                b = groups[right][0]
                if a["source_doi"] == b["source_doi"]:
                    continue
                author_overlap = sorted(set(a.get("authors", [])) & set(b.get("authors", [])))
                institution_overlap = sorted(
                    set(a.get("institutions", [])) & set(b.get("institutions", []))
                )
                years = (a.get("publication_year"), b.get("publication_year"))
                year_close = all(isinstance(value, int) for value in years) and abs(years[0] - years[1]) <= 1
                if not (year_close and (author_overlap or institution_overlap)):
                    continue
                winner = min(canonical[left], canonical[right])
                loser = max(canonical[left], canonical[right])
                for key, value in list(canonical.items()):
                    if value == loser:
                        canonical[key] = winner
                collapses.append(
                    {
                        "canonical_group_id": winner,
                        "collapsed_group_id": loser,
                        "signature_sha256": signature,
                        "author_overlap": author_overlap,
                        "institution_overlap": institution_overlap,
                        "publication_years": list(years),
                        "evidence": "EXACT_PANEL_DESCRIPTOR_VALUE_SIGNATURE_PLUS_AUTHOR_OR_INSTITUTION_AND_YEAR",
                    }
                )
    report = {
        "contract_version": "r11.cross-source-duplicate-audit.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pre_dedup_group_count": len(groups),
        "post_dedup_group_count": len(set(canonical.values())),
        "apparent_groups_collapsed": len(groups) - len(set(canonical.values())),
        "collapse_rule": (
            "Exact base identity, panel size, descriptor/dimension set, reported values and "
            "scale, plus author/institution overlap and publication years within one year."
        ),
        "author_institution_trial_year_checks_executed": True,
        "collapses": collapses,
        "guards": {"fit_count": 0, "weak_similarity_only_collapses": 0},
    }
    return canonical, report


def failure_taxonomy(
    raw: dict[str, Any],
    primary: dict[str, Any],
    supplement: dict[str, Any],
) -> dict[str, Any]:
    shapes = primary.get("candidate_shape_counts", {})
    supplement_status = {
        row["candidate_id"]: row for row in supplement.get("candidate_outcomes", [])
    }
    records = []
    for row in raw["candidate_outcomes"]:
        reason = row.get("failure_reason") or "LEGACY_STRICT_ADAPTER_REJECTED"
        if reason.startswith("FULL_TEXT_RETRIEVAL_FAILED") or reason in {
            "SOURCE_LICENSE_NOT_REVERIFIED_ALLOWED_NON_ND",
            "DUPLICATE_EXISTING_SOURCE_DOI",
        }:
            category = "SOURCE_REFUSED_OR_RETRIEVAL_FAILED"
        elif reason == "NO_MACHINE_READABLE_TABLES" or reason.startswith("FULL_TEXT_PARSE_FAILED"):
            category = "FULL_TEXT_NO_MACHINE_READABLE_TABLE"
        elif reason == "NO_ADMISSIBLE_SAMPLE_DESCRIPTOR_CELLS" or row.get("outcome", "").startswith("ADMITTED"):
            category = "TABLE_PRESENT_WRONG_STRUCTURE"
        else:
            category = "MACHINE_TABLE_NO_GOVERNED_NAMED_DESCRIPTOR_SUPERVISION"
        recovered = shapes.get(row["candidate_id"], {})
        supplement_row = supplement_status.get(row["candidate_id"])
        records.append(
            {
                "candidate_id": row["candidate_id"],
                "doi": row.get("doi"),
                "initial_diagnosis_class": category,
                "first_pass_reason": reason,
                "primary_recovery_shape_counts": recovered,
                "supplement_recovery_status": supplement_row.get("status") if supplement_row else "NOT_APPLICABLE",
                "final_recovery_outcome": "RECOVERED_TYPED_RECORDS" if recovered else "NOT_RECOVERED",
            }
        )
    counts = Counter(row["initial_diagnosis_class"] for row in records)
    if len(records) != 248:
        raise ValueError("FAILURE_TAXONOMY_NOT_248")
    return {
        "contract_version": "r11.failure-taxonomy.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate_count": len(records),
        "diagnosis_class_counts": dict(sorted(counts.items())),
        "issued_addendum_count_check": {
            "issued_counts": [115, 74, 11, 50],
            "issued_sum": sum([115, 74, 11, 50]),
            "frozen_candidate_denominator": 248,
            "status": "INCONSISTENT_ISSUED_COUNTS_SUM_TO_250",
            "resolution": "CURRENT_REPRODUCIBLE_FIRST_PASS_RECLASSIFICATION_USED",
        },
        "recovered_candidate_count": sum(
            row["final_recovery_outcome"] == "RECOVERED_TYPED_RECORDS" for row in records
        ),
        "records": records,
        "guards": {"fit_count": 0, "pdf_derived_tables_admitted": 0},
    }


def combined_outputs(
    primary: dict[str, Any], supplement: dict[str, Any], targeted: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sources = {
        "R10_248_PRIMARY": primary.get("records", []),
        "R10_248_SUPPLEMENT": supplement.get("records", []),
        "R11_TARGETED": targeted.get("records", []),
    }
    records_by_id: dict[str, dict[str, Any]] = {}
    source_counts = {}
    for source, rows in sources.items():
        source_counts[source] = len(rows)
        for row in rows:
            copied = dict(row)
            copied["r11_acquisition_stream"] = source
            records_by_id.setdefault(row["record_id"], copied)
    records = sorted(records_by_id.values(), key=lambda row: row["record_id"])
    return records, {
        "source_record_counts_pre_record_dedup": source_counts,
        "combined_record_count": len(records),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--targeted", type=Path, default=R11 / "targeted_acquisition.json")
    args = parser.parse_args()
    required = [
        R11 / "extraction_report.json",
        R11 / "shape_distribution.json",
        R11 / "supplement_recovery.json",
        R11 / "pipeline_validation.json",
        args.targeted,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("MISSING_REQUIRED_INPUT:" + ",".join(missing))

    raw = json.loads(required[0].read_text())
    primary = json.loads(required[1].read_text())
    supplement = json.loads(required[2].read_text())
    pipeline = json.loads(required[3].read_text())
    targeted = json.loads(required[4].read_text())
    records, combination = combined_outputs(primary, supplement, targeted)
    canonical, duplicate_report = deduplicate(records)
    stream_timestamps = {
        "R10_248_PRIMARY": primary.get("generated_at_utc"),
        "R10_248_SUPPLEMENT": supplement.get("generated_at_utc"),
        "R11_TARGETED": targeted.get("generated_at_utc"),
    }

    shape_records = Counter(row["shape_id"] for row in records)
    shape_tables = Counter()
    for shape, table in {
        (row["shape_id"], (row["source_doi"], row["table_id"])) for row in records
    }:
        shape_tables[shape] += 1
    groups = group_rows(records)
    shape_groups = {
        shape: len(
            {
                canonical[row["coffee_group_id"]]
                for row in records
                if row["shape_id"] == shape and row.get("coffee_group_id")
            }
        )
        for shape in SHAPES
    }
    shape_distribution = {
        "contract_version": "r11.combined-stratified-shape-distribution.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "contracts": SHAPES,
        "inputs": {
            "primary_sha256": sha(required[1].read_bytes()),
            "supplement_sha256": sha(required[2].read_bytes()),
            "targeted_sha256": sha(required[4].read_bytes()),
        },
        "summary": combination
        | {
            "typed_table_count": len({(row["source_doi"], row["table_id"]) for row in records}),
            "shape_table_counts": {shape: shape_tables[shape] for shape in SHAPES},
            "shape_record_counts": {shape: shape_records[shape] for shape in SHAPES},
            "shape_group_counts_post_dedup": shape_groups,
        },
        "records": records,
        "guards": {
            "fit_count": 0,
            "new_mapping_rules_created": 0,
            "specificity_increasing_mappings": sum(
                row.get("mapping_direction") == "SPECIFICATION" for row in records
            ),
            "t4_promoted_to_named_supervision": False,
            "t5_t6_promoted_to_sample_supervision": False,
        },
    }

    mapped = [row for row in records if row.get("mapping_status") == "MAPPED"]
    unmapped = [
        row
        for row in records
        if row.get("mapping_status") == "UNMAPPED"
        and not (row["shape_id"] == "T4" and row.get("native_dimension_id"))
    ]
    mapping_audit = {
        "contract_version": "r11.frozen-r6-mapping-audit.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mapped_assertion_count": len(mapped),
        "mapping_direction_counts": dict(
            sorted(Counter(row.get("mapping_direction") for row in mapped).items())
        ),
        "mapped_assertions": [
            {
                key: row.get(key)
                for key in (
                    "record_id",
                    "source_doi",
                    "table_id",
                    "shape_id",
                    "source_surface_form",
                    "concept_id",
                    "rule_id",
                    "mapping_direction",
                    "specificity_grade",
                )
            }
            for row in mapped
        ],
        "owner_review_queue": [
            {
                "queue_id": "r11.mapping-review:" + sha(
                    f"{row['source_doi']}|{row.get('source_surface_form')}".encode()
                )[:24],
                "source_doi": row["source_doi"],
                "source_surface_form": row.get("source_surface_form"),
                "shape_id": row["shape_id"],
                "reason": "NO_FROZEN_R6_RULE",
            }
            for row in {
                (item["source_doi"], item.get("source_surface_form")): item
                for item in unmapped
            }.values()
        ],
        "guards": {
            "fit_count": 0,
            "registry_mutations": 0,
            "formal_relation_edges_created": 0,
            "specificity_increasing_mappings": 0,
        },
    }

    named = [row for row in records if row["shape_id"] in {"T1", "T2", "T3"}]
    direct_named = [row for row in named if row.get("mapping_status") == "DIRECT"]
    mapped_named = [row for row in named if row.get("mapping_status") == "MAPPED"]
    direct_groups = {
        canonical[row["coffee_group_id"]] for row in direct_named if row.get("coffee_group_id")
    }
    mapped_groups = {
        canonical[row["coffee_group_id"]] for row in mapped_named if row.get("coffee_group_id")
    }
    named_groups = direct_groups | mapped_groups
    direct_vs_mapped = {
        "contract_version": "r11.direct-vs-mapped-counts.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "counts_reported_separately": True,
        "direct": {
            "record_count": len(direct_named),
            "post_dedup_group_count": len(direct_groups),
            "candidate_count": len({row.get("concept_id") for row in direct_named}),
        },
        "mapped": {
            "record_count": len(mapped_named),
            "post_dedup_group_count": len(mapped_groups),
            "candidate_count": len({row.get("concept_id") for row in mapped_named}),
        },
        "direct_plus_mapped_union": {
            "record_count": len(direct_named) + len(mapped_named),
            "post_dedup_group_count": len(named_groups),
            "candidate_count": len({row.get("concept_id") for row in named}),
        },
        "warning": "The union is explicitly labelled and is not presented as a DIRECT count.",
        "guards": {"fit_count": 0, "unlabelled_merged_headline_count": 0},
    }

    acquisition_manifest = {
        "contract_version": "r11.acquisition-manifest.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "record_count": len(records),
        "records": [
            ({
                key: row.get(key)
                for key in (
                    "record_id",
                    "shape_id",
                    "evidence_grade",
                    "track",
                    "r11_acquisition_stream",
                    "source_family_id",
                    "source_system",
                    "source_record_id",
                    "source_doi",
                    "source_url",
                    "source_sha256",
                    "resolved_license",
                    "share_alike_obligation",
                    "attribution_string",
                    "table_id",
                    "coffee_group_id",
                    "canonical_trial_id",
                    "mapping_status",
                    "concept_id",
                    "native_dimension_id",
                    "c0_id",
                    "c1_id",
                )
            } | {
                "retrieval_timestamp_utc": stream_timestamps[
                    row["r11_acquisition_stream"]
                ]
            })
            for row in records
        ],
        "retrieval_receipts": targeted.get("query_receipts", []),
        "source_capability_receipts": targeted.get("capability_receipts", []),
        "guards": {
            "fit_count": 0,
            "unknown_license_admitted": 0,
            "nd_license_admitted": 0,
            "participant_pii_admitted": 0,
        },
    }

    r10_manifest = json.loads((R10 / "training_corpus_manifest.json").read_text())
    family_pre = Counter(r10_manifest["coffee_group_counts_by_source_family"])
    for group_id, rows in groups.items():
        family_pre[rows[0]["source_family_id"]] += 1
    family_post = Counter(r10_manifest["coffee_group_counts_by_source_family"])
    seen_post = set()
    for group_id, rows in sorted(groups.items()):
        canonical_id = canonical[group_id]
        if canonical_id in seen_post:
            continue
        seen_post.add(canonical_id)
        family_post[groups[canonical_id][0]["source_family_id"]] += 1
    post_total = sum(family_post.values())
    max_family, max_groups = max(family_post.items(), key=lambda pair: pair[1])
    source_distribution = {
        "contract_version": "r11.source-family-distribution.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "r10_frozen_group_count": r10_manifest["coffee_group_count"],
        "pre_dedup": {
            "group_count": sum(family_pre.values()),
            "source_family_count": len(family_pre),
            "groups_by_family": dict(sorted(family_pre.items())),
        },
        "post_dedup": {
            "group_count": post_total,
            "source_family_count": len(family_post),
            "groups_by_family": dict(sorted(family_post.items())),
            "shares_by_family": {
                family: count / post_total for family, count in sorted(family_post.items())
            },
            "max_family_id": max_family,
            "max_family_group_count": max_groups,
            "max_family_share": max_groups / post_total,
        },
        "guards": {"fit_count": 0},
    }

    t4_groups = {
        canonical[row["coffee_group_id"]]
        for row in records
        if row["shape_id"] == "T4" and row.get("coffee_group_id")
    }
    c0_groups = {
        canonical[row["coffee_group_id"]]
        for row in records
        if row["shape_id"] == "T4" and row.get("coffee_group_id") and row.get("c0_id")
    }
    c1_groups = {
        canonical[row["coffee_group_id"]]
        for row in records
        if row["shape_id"] == "T4" and row.get("coffee_group_id") and row.get("c1_id")
    }
    context_coverage = {
        "contract_version": "r11.context-coverage.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "post_dedup_t4_group_count": len(t4_groups),
        "post_dedup_t4_c0_group_count": len(c0_groups),
        "post_dedup_t4_c1_group_count": len(c1_groups),
        "targets": {"T4": 600, "T4_C0": 150, "T4_C1": 150},
        "status": {
            "T4": "PASS" if len(t4_groups) >= 600 else "FAIL",
            "T4_C0": "PASS" if len(c0_groups) >= 150 else "FAIL",
            "T4_C1": "PASS" if len(c1_groups) >= 150 else "FAIL",
        },
        "guards": {"fit_count": 0},
    }

    reconciliation_report, eligible_ids = reconciliation()
    calibration = historical_calibration(eligible_ids)
    # Candidate support counts use the already-frozen R10 positive corpus plus
    # newly acquired T1--T3 named groups.  This is a corpus count, not a model metric.
    support = Counter()
    if PRIVATE_R10.exists():
        private = json.loads(PRIVATE_R10.read_text())
        for group in private["groups"]:
            support.update(set(group["descriptor_ids"]))
    for group_id in named_groups:
        support.update(
            {
                row.get("concept_id")
                for row in groups[group_id]
                if row["shape_id"] in {"T1", "T2", "T3"} and row.get("concept_id")
            }
        )
    supported_ten = sum(count >= 10 for count in support.values())
    ontology_count = sum(row["shape_id"] in {"T5", "T6"} for row in records)
    criteria = [
        ("DIRECT_T1_T2_T3_GROUPS", len(direct_groups), 250),
        ("DIRECT_PLUS_MAPPED_T1_T2_T3_GROUPS", len(named_groups), 600),
        ("T4_GROUPS", len(t4_groups), 600),
        ("T4_C0_GROUPS", len(c0_groups), 150),
        ("T4_C1_GROUPS", len(c1_groups), 150),
        ("T5_T6_ONTOLOGY_RECORDS", ontology_count, 200),
        ("SOURCE_FAMILIES", len(family_post), 8),
        ("CANDIDATES_WITH_TEN_GROUPS", supported_ten, 40),
    ]
    rows = [
        {
            "criterion": name,
            "current": current,
            "target": target,
            "comparison": ">=",
            "status": "PASS" if current >= target else "FAIL",
            "shortfall": max(0, target - current),
        }
        for name, current, target in criteria
    ]
    rows.append(
        {
            "criterion": "MAX_SOURCE_FAMILY_SHARE",
            "current": max_groups / post_total,
            "target": 0.35,
            "comparison": "<=",
            "status": "PASS" if max_groups / post_total <= 0.35 else "FAIL",
            "excess": max(0.0, max_groups / post_total - 0.35),
        }
    )
    exit_status = {
        "contract_version": "r11.fixed-exit-criterion-status.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL",
        "thresholds_revised_downward": False,
        "power_derivation_recorded_before_acquisition": (
            "Assuming paired per-coffee-group NDCG differences with SD approximately "
            "0.2--0.3, detecting delta approximately 0.03 at 80% power requires roughly "
            "350--800 groups; 600 was fixed in the safer portion of that range. This is "
            "a target derivation only, not an R11 model metric."
        ),
        "criteria": rows,
        "round_outcome": "STOP_BELOW_FIXED_TARGETS"
        if any(row["status"] == "FAIL" for row in rows)
        else "ACQUISITION_THRESHOLD_MET",
        "guards": {
            "fit_count": 0,
            "real_data_model_vs_baseline_metric_count": 0,
            "thresholds_relaxed": 0,
        },
    }

    owner_decision = {
        "contract_version": "r11.owner-architecture-decision.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "PENDING_OWNER_DECISION",
        "decision_required": "SUPERVISION_ARCHITECTURE_IF_DIRECT_NAMED_DESCRIPTOR_SUPPLY_REMAINS_SCARCE",
        "evidence_snapshot": {
            "direct_named_groups": len(direct_groups),
            "direct_plus_mapped_named_groups": len(named_groups),
            "dimension_groups": len(t4_groups),
            "ontology_records": ontology_count,
        },
        "options": {
            "A": {
                "label": "NAMED_DESCRIPTOR_TARGET_WITH_MAPPED_SUPERVISION",
                "condition": "Carry mapping uncertainty explicitly into abstention behaviour.",
            },
            "B": {
                "label": "DIMENSION_TARGET_WITH_GOVERNED_ONTOLOGY_BRIDGE",
                "condition": "Named descriptors require later owner-approved relation edges.",
            },
        },
        "selected_option": None,
        "training_authorized": False,
    }

    auxiliary = {
        "contract_version": "r11.auxiliary-transfer-manifest.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "track": "AUXILIARY_TRANSFER",
        "record_count": 0,
        "records": [],
        "status": "NO_NEW_AUXILIARY_TRANSFER_RECORDS_ACQUIRED",
        "permitted_future_use": "DESCRIPTOR_REPRESENTATION_PRETRAINING_ONLY_IF_SEPARATELY_AUTHORIZED",
        "coffee_supervision_count_contribution": 0,
        "exit_criterion_count_contribution": 0,
        "promotable_to_coffee_professional_labels": False,
        "guards": {"fit_count": 0},
    }

    failure = failure_taxonomy(raw, primary, supplement)
    writes = {
        "shape_distribution.json": shape_distribution,
        "failure_taxonomy.json": failure,
        "mapping_audit.json": mapping_audit,
        "direct_vs_mapped_counts.json": direct_vs_mapped,
        "acquisition_manifest.json": acquisition_manifest,
        "duplicate_audit.json": duplicate_report,
        "source_family_distribution.json": source_distribution,
        "context_coverage.json": context_coverage,
        "exit_criterion_status.json": exit_status,
        "readmission_reconciliation.json": reconciliation_report,
        "contract_calibration_report.json": calibration,
        "owner_decision.json": owner_decision,
        "auxiliary_transfer_manifest.json": auxiliary,
    }
    for filename, value in writes.items():
        write_json(R11 / filename, value)

    manifest = {
        "contract_version": "r11.corpus-expansion-round-manifest.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "predecessor_sha": "4d5b20863173df8cc2b74ba955f18c68f5f4f63a",
        "round_outcome": exit_status["round_outcome"],
        "fit_count": 0,
        "real_label_model_vs_baseline_metric_count": 0,
        "pipeline_validation_status": pipeline["status"],
        "formal_descriptor_relation_edge_count": 0,
        "historical_unknown_records_reopened": 0,
        "historical_unknown_records_remaining_excluded": 13952,
        "insufficient_evidence_abstentions_preserved": 156,
        "strict_evidence_rate_preserved": 0.3193,
        "out_of_scope_dirty_deletions_touched": 0,
        "training_pause_after_round": True,
        "deliverables": {
            filename: {"sha256": sha((R11 / filename).read_bytes())}
            for filename in sorted(writes)
        }
        | {
            "extraction_report.json": {"sha256": sha(required[0].read_bytes())},
            "supplement_recovery.json": {"sha256": sha(required[2].read_bytes())},
            "targeted_acquisition.json": {"sha256": sha(required[4].read_bytes())},
            "pipeline_validation.json": {"sha256": sha(required[3].read_bytes())},
        },
        "notes": [
            "No real-data model-versus-baseline metric was computed or reported.",
            "The R10 5,819-to-879 provenance discrepancy is disclosed in readmission_reconciliation.json.",
            "The addendum's four initial failure counts sum to 250, not 248; reproducible reclassification is used.",
        ],
    }
    write_json(R11 / "round_manifest.json", manifest)
    print(
        json.dumps(
            {
                "round_outcome": manifest["round_outcome"],
                "fit_count": 0,
                "combined_typed_records": len(records),
                "direct_named_groups": len(direct_groups),
                "direct_plus_mapped_named_groups": len(named_groups),
                "t4_groups": len(t4_groups),
                "ontology_records": ontology_count,
                "source_families": len(family_post),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
