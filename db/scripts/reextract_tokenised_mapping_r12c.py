#!/usr/bin/env python3
"""R12C — re-resolve queued surface forms with list-fragment tokenisation.

DEFECT UNDER REPAIR
-------------------
stratify_extraction_r11.resolve_surface() applies norm() to an entire table cell
and then performs an exact dictionary lookup:

    token = norm(surface)
    if token in direct: ...
    rule = rules.get(token)

norm() collapses every non-alphanumeric character to a space, so a multi-term
odour-description cell such as "honey, sweet, floral, green" becomes the single
token "honey sweet floral green", which cannot match any single-term key. The
R6 rules themselves declare scope EXACT_COMPLETE_LIST_FRAGMENT, i.e. they were
authored to match *fragments of a list*, but the caller never splits the list.

The same collapse breaks citation markers: "floral [36]" becomes "floral 36".

WHAT THIS SCRIPT DOES
---------------------
Splits each surface form into list fragments, strips citation and footnote
markers, and resolves every fragment through the SAME concept registry and the
SAME 42 frozen R6 rules used by R11.

WHAT THIS SCRIPT DOES NOT DO
----------------------------
  * creates no R6 rule
  * mutates no registry
  * creates no formal relation edge
  * performs no acquisition and no network access
  * writes no training corpus and runs no fit
  * modifies no sealed artefact

A fragment that resolves does so under a rule that already existed and was
already approved to the same degree. A fragment that does not resolve remains
queued exactly as before. This is a bug fix in the caller, not a policy change.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

from extract_candidates_r11 import norm  # noqa: E402  (path set above)

R6 = ROOT / "db/data/backend-sequential-model-v2/revisions/r6"
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
R12C = ROOT / "db/data/backend-sequential-model-v2/revisions/r12c"

FRAGMENT_SEPARATORS = re.compile(r"[,;/]")
CITATION_MARKER = re.compile(r"\[\s*\d+(?:\s*[,-]\s*\d+)*\s*\]")
PARENTHETICAL = re.compile(r"\([^)]*\)")
TRAILING_FOOTNOTE = re.compile(r"[\s ]*(?:\*+|\d+(?:\s*,\s*\d+)*)\s*$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_registries() -> tuple[dict[str, str], dict[str, dict[str, str]], dict[str, str]]:
    """Load the exact registries R11 used. Digests recorded for provenance."""
    contract_bytes = (R9 / "output_policy_contract.json").read_bytes()
    registry = json.loads(contract_bytes)["concept_role_registry"]
    direct = {
        norm(concept_id.removeprefix("sensory.").replace("_", " ")): concept_id
        for concept_id, row in registry.items()
        if row["role"] == "NAMED_DESCRIPTOR" and concept_id.startswith("sensory.")
    }

    patch_bytes = (R6 / "semantic_patch.tsv").read_bytes()
    rules: dict[str, dict[str, str]] = {}
    with (R6 / "semantic_patch.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rules[norm(row["normalized_span"])] = row

    digests = {
        "r9_output_policy_contract_sha256": sha256_bytes(contract_bytes),
        "r6_semantic_patch_sha256": sha256_bytes(patch_bytes),
    }
    return direct, rules, digests


def fragments(surface: str) -> list[str]:
    """Split a cell into list fragments and strip citation/footnote artefacts."""
    cleaned = CITATION_MARKER.sub(" ", surface)
    cleaned = PARENTHETICAL.sub(" ", cleaned)
    out: list[str] = []
    for part in FRAGMENT_SEPARATORS.split(cleaned):
        part = TRAILING_FOOTNOTE.sub("", part.strip())
        part = part.strip(" .-")
        if part:
            out.append(part)
    return out


def resolve_fragment(
    fragment: str,
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Identical lookup semantics to stratify_extraction_r11.resolve_surface."""
    token = norm(fragment)
    if not token:
        return {"mapping_status": "EMPTY", "concept_id": None, "rule_id": None}
    if token in direct:
        return {
            "mapping_status": "DIRECT",
            "concept_id": direct[token],
            "rule_id": None,
            "mapping_direction": "IDENTITY",
            "specificity_grade": "SPECIFIC",
        }
    rule = rules.get(token)
    if not rule:
        return {
            "mapping_status": "UNMAPPED",
            "concept_id": None,
            "rule_id": None,
            "mapping_direction": "NONE",
            "specificity_grade": "COMPOUND" if len(token.split()) > 1 else "UNRESOLVED",
        }
    concept = rule["concepts"]
    specificity = "SPECIFIC" if concept.startswith("sensory.") else "BROAD"
    if rule["relation"] == "SCOPED_MODIFIER_CORE":
        specificity = "COMPOUND"
    return {
        "mapping_status": "MAPPED",
        "concept_id": concept,
        "rule_id": rule["rule_id"],
        "mapping_direction": (
            "GENERALISATION"
            if not concept.startswith("sensory.")
            else "IDENTITY_OR_HEAD_PRESERVING"
        ),
        "specificity_grade": specificity,
        "r6_relation": rule["relation"],
        "r6_human_approval": rule["human_approval"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=R12C)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    direct, rules, digests = load_registries()

    audit_bytes = (R11 / "mapping_audit.json").read_bytes()
    audit = json.loads(audit_bytes)
    queue = audit["owner_review_queue"]

    results: list[dict[str, Any]] = []
    recovered_forms = 0
    still_unmapped_forms = 0
    concept_hits: dict[str, int] = {}
    unresolved_fragments: dict[str, int] = {}

    for row in queue:
        surface = row["source_surface_form"]
        parts = fragments(surface)
        resolutions = [
            {"fragment": part, **resolve_fragment(part, direct, rules)} for part in parts
        ]
        resolved = [r for r in resolutions if r["mapping_status"] in {"DIRECT", "MAPPED"}]
        if resolved:
            recovered_forms += 1
            for r in resolved:
                concept_hits[r["concept_id"]] = concept_hits.get(r["concept_id"], 0) + 1
        else:
            still_unmapped_forms += 1
            for r in resolutions:
                if r["mapping_status"] == "UNMAPPED":
                    key = norm(r["fragment"])
                    unresolved_fragments[key] = unresolved_fragments.get(key, 0) + 1

        results.append(
            {
                "queue_id": row["queue_id"],
                "shape_id": row["shape_id"],
                "source_doi": row["source_doi"],
                "source_surface_form": surface,
                "fragment_count": len(parts),
                "resolutions": resolutions,
                "recovered": bool(resolved),
                "recovered_concept_ids": sorted({r["concept_id"] for r in resolved}),
            }
        )

    # Marginal value of authoring the next N rules, ranked by fragment frequency.
    # This converts an undifferentiated 1429-item queue into a bounded decision list.
    ranked = [k for k, _ in sorted(unresolved_fragments.items(), key=lambda kv: -kv[1])]
    unresolved_by_form: dict[str, set[str]] = {}
    for record in results:
        if record["recovered"]:
            continue
        unresolved_by_form[record["queue_id"]] = {
            norm(x["fragment"])
            for x in record["resolutions"]
            if x["mapping_status"] == "UNMAPPED"
        }
    prioritisation = []
    for n in (10, 20, 30, 60):
        head = set(ranked[:n])
        gain = sum(1 for forms in unresolved_by_form.values() if forms & head)
        prioritisation.append(
            {
                "rules_authored": n,
                "additional_forms_recovered": gain,
                "cumulative_forms_recovered": recovered_forms + gain,
                "cumulative_recovery_rate": (
                    (recovered_forms + gain) / len(queue) if queue else None
                ),
            }
        )

    total_fragments = sum(r["fragment_count"] for r in results)
    resolved_fragments = sum(
        1
        for r in results
        for x in r["resolutions"]
        if x["mapping_status"] in {"DIRECT", "MAPPED"}
    )

    report = {
        "contract_version": "r12c.tokenised-remapping.v1",
        "round": "R12C",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "defect_repaired": (
            "resolve_surface() performed an exact dictionary lookup on the whole "
            "normalised cell. norm() collapses separators, so multi-term cells and "
            "cells carrying citation markers could never match a single-term key, "
            "despite R6 rules declaring scope EXACT_COMPLETE_LIST_FRAGMENT."
        ),
        "method": (
            "Split on , ; / after removing citation markers and parentheticals; strip "
            "trailing footnote digits and asterisks; resolve each fragment through the "
            "identical concept registry and frozen R6 rule table used by R11."
        ),
        "inputs": {
            "r11_mapping_audit_sha256": sha256_bytes(audit_bytes),
            **digests,
            "concept_registry_size": len(direct),
            "frozen_r6_rule_count": len(rules),
            "queue_size": len(queue),
        },
        "guards": {
            "fit_count": 0,
            "new_acquisition_count": 0,
            "network_calls": 0,
            "r6_rules_created": 0,
            "registry_mutations": 0,
            "formal_relation_edges_created": 0,
            "specificity_increasing_mappings": 0,
            "sealed_artifacts_modified": False,
            "training_corpus_written": False,
        },
        "results_summary": {
            "queued_forms": len(queue),
            "forms_recovered_by_tokenisation": recovered_forms,
            "forms_still_unmapped": still_unmapped_forms,
            "form_recovery_rate": recovered_forms / len(queue) if queue else None,
            "total_fragments": total_fragments,
            "fragments_resolved": resolved_fragments,
            "fragment_resolution_rate": (
                resolved_fragments / total_fragments if total_fragments else None
            ),
            "r11_mapped_assertion_count_before": audit["mapped_assertion_count"],
        },
        "concept_hit_counts": dict(sorted(concept_hits.items(), key=lambda kv: -kv[1])),
        "top_unresolved_fragments": dict(
            sorted(unresolved_fragments.items(), key=lambda kv: -kv[1])[:60]
        ),
        "second_defect_unreachable_concept_prefixes": {
            "finding": (
                "load_direct_registry() admits only concept ids prefixed 'sensory.'. "
                "Concepts prefixed 'attribute.' and 'broad.', which carry the project's "
                "own top-level support dimensions, are reachable only through an explicit "
                "R6 rule, and no rule exists for the bare surface forms."
            ),
            "evidence": {
                "unresolved_floral_occurrences": unresolved_fragments.get("floral", 0),
                "unresolved_fruity_occurrences": unresolved_fragments.get("fruity", 0),
                "unresolved_green_occurrences": unresolved_fragments.get("green", 0),
                "note": (
                    "floral and fruity are among the nine declared support dimensions, "
                    "and attribute.fruity is hit elsewhere via rules, proving the concept "
                    "exists while its bare surface form cannot reach it."
                ),
            },
        },
        "owner_review_prioritisation": prioritisation,
        "limitations": [
            "Recovery counts resolved surface forms, not admitted supervision. Each "
            "recovered concept still faces the downstream extraction gates that R12 and "
            "R12B measured and could not quantify.",
            "No coffee group count is claimed. Group formation was not run.",
            "Fragments resolving only through a BROAD_CATEGORY_ONLY rule remain broad and "
            "are not promoted to specific descriptors.",
            "Unresolved fragments remain queued under existing policy; none were admitted.",
        ],
        "records": results,
    }

    (args.output_dir / "tokenised_remapping_r12c.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    print(
        json.dumps(
            {
                "queued_forms": len(queue),
                "recovered_forms": recovered_forms,
                "form_recovery_rate": round(recovered_forms / len(queue), 4) if queue else None,
                "total_fragments": total_fragments,
                "fragments_resolved": resolved_fragments,
                "distinct_concepts_hit": len(concept_hits),
                "r11_mapped_before": audit["mapped_assertion_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
