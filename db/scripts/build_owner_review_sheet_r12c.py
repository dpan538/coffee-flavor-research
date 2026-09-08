#!/usr/bin/env python3
"""R12C — build a categorised owner review sheet for the queued surface forms.

The R12C remapping showed that approving roughly 60 additional mappings would
lift recovery from 515 to 1047 of 1429 queued forms. Those 60 are NOT 60
equivalent decisions. They fall into four categories with very different risk
and very different required judgement, and batching them as one list would
produce wrong approvals.

This script categorises them from data. It PROPOSES nothing as approved:
every row is a candidate for owner decision, and no rule, concept or relation
edge is created.

STATIC only. No network, no acquisition, no fit, no sealed artefact modified.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import stratify_extraction_r11 as base  # noqa: E402
from extract_candidates_r11 import norm  # noqa: E402

R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
R12C = ROOT / "db/data/backend-sequential-model-v2/revisions/r12c"

# Morphological suffix pairs that make two surface forms the same lexical item.
SUFFIX_VARIANTS = (
    ("y", ""), ("", "y"), ("ic", ""), ("", "ic"), ("s", ""), ("", "s"),
    ("like", ""), ("", "like"), ("ish", ""), ("", "ish"),
    ("iness", "y"), ("ness", ""), ("ed", ""), ("", "ed"),
)

# Terms that describe study design, chemistry, quality judgement or the subject
# itself rather than a flavour percept. Kept explicit so the owner can contest it.
NOT_A_FLAVOUR_DESCRIPTOR = {
    "coffee", "clean", "fresh", "mild", "no", "yes", "sample", "samples",
    "control", "total", "intensity", "overall", "quality", "score", "scores",
    "strong", "weak", "heavy", "light", "high", "low", "age", "gender", "male",
    "female", "method", "content", "concentration", "compound", "compounds",
    "formulation", "moisture", "descriptors", "descriptor", "attribute",
    "attributes", "appearance", "colour", "color", "texture", "temperature",
}


def variants(token: str) -> set[str]:
    out = {token}
    for old, new in SUFFIX_VARIANTS:
        if old and token.endswith(old):
            out.add(token[: -len(old)] + new)
        elif not old:
            out.add(token + new)
    return {v for v in out if v}


def categorise(
    token: str,
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> dict[str, Any]:
    """Assign one of four decision categories, with the reason."""
    if token in base.NATIVE_DIMENSIONS:
        return {
            "category": "A_CODE_FIX_NOT_A_DECISION",
            "reason": (
                "Already present in NATIVE_DIMENSIONS. It appears unresolved only "
                "because resolve_surface does not consult NATIVE_DIMENSIONS, unlike "
                "dimension_surface. No owner decision is required; this is a code fix."
            ),
            "existing_target": "NATIVE_DIMENSIONS",
            "owner_decision_needed": False,
        }

    for v in variants(token):
        if v == token:
            continue
        if v in direct:
            return {
                "category": "B_MORPHOLOGICAL_VARIANT",
                "reason": f"Suffix variant of existing concept surface '{v}'.",
                "existing_target": direct[v],
                "proposed_direction": "IDENTITY_OR_HEAD_PRESERVING",
                "owner_decision_needed": True,
                "risk": "LOW - same lexical item, no specificity change.",
            }
        if v in rules:
            return {
                "category": "B_MORPHOLOGICAL_VARIANT",
                "reason": f"Suffix variant of existing R6 span '{v}'.",
                "existing_target": rules[v]["concepts"],
                "existing_rule_id": rules[v]["rule_id"],
                "proposed_direction": rules[v].get("relation"),
                "owner_decision_needed": True,
                "risk": "LOW - inherits an already-authored rule's target.",
            }
        if v in base.NATIVE_DIMENSIONS:
            return {
                "category": "B_MORPHOLOGICAL_VARIANT",
                "reason": f"Suffix variant of dimension '{v}'.",
                "existing_target": "NATIVE_DIMENSIONS",
                "owner_decision_needed": True,
                "risk": "LOW",
            }

    if token in NOT_A_FLAVOUR_DESCRIPTOR:
        return {
            "category": "D_NOT_A_FLAVOUR_DESCRIPTOR",
            "reason": (
                "Study design, chemistry, quality judgement, or the subject itself. "
                "Admitting it would put non-percept vocabulary into the descriptor space."
            ),
            "owner_decision_needed": True,
            "recommended": "REJECT",
            "risk": "Admitting these pollutes the concept space and is hard to undo.",
        }

    return {
        "category": "C_NEW_DESCRIPTOR_REQUIRES_JUDGEMENT",
        "reason": (
            "No existing concept, rule or dimension covers this term or a variant of it. "
            "Approving it means deciding whether it is a coffee flavour percept at all, "
            "and if so whether it needs a new concept rather than only a rule."
        ),
        "owner_decision_needed": True,
        "risk": "HIGH - this is a concept-space decision, not a mapping decision.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=60)
    parser.add_argument("--output-dir", type=Path, default=R12C)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    remap_path = R12C / "tokenised_remapping_r12c.json"
    remap_bytes = remap_path.read_bytes()
    remap = json.loads(remap_bytes)

    audit = json.loads((R11 / "mapping_audit.json").read_text())
    dois_by_form: dict[str, set[str]] = collections.defaultdict(set)
    for row in audit["owner_review_queue"]:
        dois_by_form[norm(row["source_surface_form"])].add(row["source_doi"])

    direct, rules = base.load_direct_registry()

    ranked = list(remap["top_unresolved_fragments"].items())[: args.top]

    entries = []
    for rank, (token, frequency) in enumerate(ranked, 1):
        info = categorise(token, direct, rules)
        supporting = sorted(
            {doi for form, dset in dois_by_form.items() if token in form for doi in dset}
        )
        entries.append(
            {
                "rank": rank,
                "surface_form": token,
                "fragment_frequency": frequency,
                "supporting_source_doi_count": len(supporting),
                "supporting_source_dois": supporting[:6],
                **info,
            }
        )

    by_category = collections.Counter(e["category"] for e in entries)
    freq_by_category: collections.Counter[str] = collections.Counter()
    for e in entries:
        freq_by_category[e["category"]] += e["fragment_frequency"]

    report = {
        "contract_version": "r12c.owner-review-sheet.v1",
        "round": "R12C",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "CANDIDATES_FOR_OWNER_DECISION_NOTHING_APPROVED",
        "guards": {
            "fit_count": 0,
            "r6_rules_created": 0,
            "concepts_created": 0,
            "formal_relation_edges_created": 0,
            "registry_mutations": 0,
            "records_admitted": 0,
            "sealed_artifacts_modified": False,
            "network_calls": 0,
        },
        "inputs": {
            "tokenised_remapping_sha256": hashlib.sha256(remap_bytes).hexdigest(),
            "concept_registry_size": len(direct),
            "frozen_r6_rule_count": len(rules),
            "native_dimension_count": len(base.NATIVE_DIMENSIONS),
        },
        "framing_correction": (
            "The earlier statement that 60 rule approvals lift recovery to 73.3% treated "
            "these as 60 equivalent decisions. They are not. Category A needs no owner "
            "decision at all, category D should mostly be rejected, and only category C "
            "is a genuine concept-space judgement."
        ),
        "category_definitions": {
            "A_CODE_FIX_NOT_A_DECISION": "Already in NATIVE_DIMENSIONS; unresolved only because resolve_surface never consults that set. Fix the code, approve nothing.",
            "B_MORPHOLOGICAL_VARIANT": "Suffix variant of an existing concept, rule or dimension. Low risk, no specificity change.",
            "C_NEW_DESCRIPTOR_REQUIRES_JUDGEMENT": "No existing coverage. Deciding this is a concept-space decision, not a mapping decision.",
            "D_NOT_A_FLAVOUR_DESCRIPTOR": "Study design, chemistry, quality judgement or the subject itself. Recommended reject.",
        },
        "category_counts": dict(by_category.most_common()),
        "category_fragment_frequency": dict(freq_by_category.most_common()),
        "entries": entries,
        "limitations": [
            "Frequency counts fragments on the queued forms, not admitted supervision.",
            "The NOT_A_FLAVOUR_DESCRIPTOR list is an explicit editorial judgement by the "
            "audit author and is stated so the owner can contest any member of it.",
            "Category B proposes inheriting an existing target; it does not verify that "
            "the inherited target is itself correct.",
            "Nothing here is approved. No rule, concept or edge was created.",
        ],
    }

    (args.output_dir / "owner_review_sheet_r12c.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    print(json.dumps({
        "top_n": args.top,
        "category_counts": report["category_counts"],
        "category_fragment_frequency": report["category_fragment_frequency"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
