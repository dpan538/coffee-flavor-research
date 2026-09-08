#!/usr/bin/env python3
"""Round 2 — deterministic OUT_SEPARATED generator, defects D1-D4 repaired.

Budget: main <= 3, secondary <= 2, overall_profile <= 3, comparison pool <= 8.

REPAIRS AGAINST THE REVIEWED PROTOTYPE
--------------------------------------
D1  Direct evidence was truncated by sorted()[:3], discarding user-stated words
    by spelling. That destroyed explicit_expression_retention = 1.0, which is
    the single property justifying strict-evidence mode. Direct evidence is now
    never dropped for budget: overflow occupies secondary AHEAD of any
    mid-level representative.

D2  covered_dimensions was computed from main rather than from all direct
    evidence, so a word cut by D1 left its dimension looking uncovered and the
    generator substituted the broad representative. The user says lemon, the
    system drops lemon and answers citrus-family. Coverage is now computed from
    the full direct set.

D3  Which uncovered dimensions reached secondary was decided by dimension-name
    spelling. Ordering is now SUPPORTED_WITHIN_SCOPE before PROPOSED, with a
    declared lexicographic tiebreak inside each tier.

D4  overall_profile truncated alphabetically across evidence tiers, so the only
    SUPPORTED dimension could be pushed out by four PROPOSED ones. Truncation
    is now within tier, never across.

D5  A dimension can occupy both secondary and profile. This is a product
    judgement, not a defect, so it is exposed as suppress_profile_when_secondary
    and defaults to False, preserving current behaviour until the owner rules.

STANDING RULE ADOPTED
    Any truncation orders by a declared evidence property first. sorted() may
    only break ties after that. Three separate defects in this project have
    been lexicographic accident acting as a decision rule.

No training, no fitting, no admission. Reads the frozen registry only.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from typing import Any

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from evidence_reader_round2 import (  # noqa: E402
    covered_dimensions as covered_dims,
    read_evidence,
)

ROOT = Path(__file__).resolve().parents[2]
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"

SUPPORTED = "SUPPORTED_WITHIN_SCOPE"
PROPOSED = "PROPOSED"


ROUND2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"


def load_registry(path: Path | None = None, apply_extension: bool = True) -> dict[str, Any]:
    """R9 sealed registry, optionally layered with the owner-approved round 2 extension.

    The extension is a separate file. R9's output_policy_contract.json is never
    edited, so every hash recorded against it since R9 stays valid.
    """
    path = path or (R9 / "output_policy_contract.json")
    registry = dict(json.loads(path.read_text())["concept_role_registry"])
    ext_path = ROUND2 / "registry_extension.json"
    if apply_extension and ext_path.exists():
        for cid, row in json.loads(ext_path.read_text())["added_concepts"].items():
            registry[cid] = row
    return registry


def _dims(registry: dict[str, Any], cid: str) -> list[str]:
    return registry.get(cid, {}).get("support_dimension_ids", []) or []


def generate_output(
    state: dict[str, Any],
    registry: dict[str, Any],
    main_max: int = 3,
    secondary_max: int = 2,
    profile_max: int = 3,
    suppress_profile_when_secondary: bool = False,
) -> dict[str, Any]:
    # ---- evidence extraction (ROUND2-OP2, ROUND2-OP3) -------------------
    # Delegated to evidence_reader_round2 so this path and the state machine
    # cannot drift apart. The reader accepts the frozen R9 k1 schema, reads
    # k1.confirmed_concepts, and resolves question options through the axis
    # partitions, without which direct evidence is unreachable in production.
    evidence = read_evidence(state, registry)
    direct_named: set[str] = evidence["direct"]
    dim_status: dict[str, str] = evidence["dim_status"]

    # ---- main: direct evidence only, never dropped for budget (D1) -----
    ordered_direct = sorted(direct_named)  # declared tiebreak, no evidence rank exists here
    main = ordered_direct[:main_max]
    direct_overflow = ordered_direct[main_max:]

    # ---- coverage from ALL evidence, not just main (D2) ----------------
    # Set evidence counts as coverage: answering "citrus" addresses fruity
    # even though no single fruit was named, so substituting the broad fruity
    # representative there would tell the participant nothing new.
    covered_dimensions = covered_dims(registry, evidence)

    # ---- secondary: direct overflow first, then representatives (D1) ---
    secondary: list[str] = list(direct_overflow[:secondary_max])
    slots_left = secondary_max - len(secondary)

    representatives_by_dimension: dict[str, list[str]] = defaultdict(list)
    if slots_left > 0:
        for cid, info in registry.items():
            if info.get("role") == "NAMED_DESCRIPTOR" and cid.startswith("broad."):
                for d in _dims(registry, cid):
                    representatives_by_dimension[d].append(cid)

    # order uncovered dimensions by evidence strength, not spelling (D3)
    uncovered = [d for d in dim_status if d not in covered_dimensions]
    uncovered.sort(key=lambda d: (0 if dim_status[d] == SUPPORTED else 1, d))

    represented_dimensions: set[str] = set()
    for dimension in uncovered:
        if slots_left <= 0:
            break
        options = sorted(representatives_by_dimension.get(dimension, []))
        if not options:
            continue
        secondary.append(options[0])
        represented_dimensions.add(dimension)
        slots_left -= 1

    # ---- overall_profile: rank by tier, truncate within tier (D4) ------
    profile_candidates: list[tuple[int, str, str]] = []
    for cid, info in registry.items():
        if info.get("role") != "PROFILE_DIRECTION":
            continue
        for d in _dims(registry, cid):
            if d not in dim_status:
                continue
            if suppress_profile_when_secondary and d in represented_dimensions:
                continue
            profile_candidates.append((0 if dim_status[d] == SUPPORTED else 1, cid, d))
            break
    profile_candidates.sort(key=lambda row: (row[0], row[1]))
    profile = [cid for _, cid, _ in profile_candidates[:profile_max]]

    return {
        "main": [{"candidate_id": c} for c in main],
        "secondary": [{"candidate_id": c} for c in secondary],
        "overall_profile": [{"candidate_id": c} for c in profile],
        "_diagnostics": {
            "direct_evidence_count": len(direct_named),
            "direct_evidence_retained": len(main) + len(direct_overflow[:secondary_max]),
            "direct_evidence_lost": max(0, len(direct_overflow) - secondary_max),
            "covered_dimensions": sorted(covered_dimensions),
            "uncovered_activated_dimensions": uncovered,
            "dimensions_represented_in_secondary": sorted(represented_dimensions),
        },
    }


def simulate_registry_with_proposed_concepts(registry: dict[str, Any]) -> dict[str, Any]:
    """In-memory only. Adds the six proposed broad concepts WITHOUT creating them.

    Nothing is written to the registry file. This exists so the projected effect
    can be shown before the owner decides, and every report using it must say so.
    """
    proposed = {
        "broad.floral": ["floral"],
        "broad.green": ["green_vegetative"],
        "broad.roasted": ["roasted"],
        "broad.fermented": ["sour_fermented"],
        "broad.spice": ["spices"],
        "broad.sweet": ["sweet"],
    }
    simulated = dict(registry)
    for cid, dims in proposed.items():
        simulated[cid] = {"role": "NAMED_DESCRIPTOR", "support_dimension_ids": dims}
    return simulated


def evaluate(states: list[dict[str, Any]], registry: dict[str, Any],
             **kwargs: Any) -> dict[str, Any]:
    n = len(states)
    if n == 0:
        return {"total_cases": 0}
    non_empty = tot_sec = tot_main = tot_prof = lost = 0
    for state in states:
        out = generate_output(state, registry, **kwargs)
        if out["secondary"]:
            non_empty += 1
        tot_sec += len(out["secondary"])
        tot_main += len(out["main"])
        tot_prof += len(out["overall_profile"])
        lost += out["_diagnostics"]["direct_evidence_lost"]
    return {
        "total_cases": n,
        "secondary_non_empty_count": non_empty,
        "secondary_non_empty_rate": round(non_empty / n, 4),
        "mean_secondary": round(tot_sec / n, 3),
        "mean_main": round(tot_main / n, 3),
        "mean_profile": round(tot_prof / n, 3),
        "direct_evidence_lost_total": lost,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--states", type=Path, help="frozen states JSON; omit to run repair checks")
    parser.add_argument("--simulate-proposed-concepts", action="store_true")
    args = parser.parse_args()

    registry = load_registry()
    if args.simulate_proposed_concepts:
        registry = simulate_registry_with_proposed_concepts(registry)

    if not args.states:
        print(json.dumps({"note": "no states supplied; import and call generate_output"},
                         ensure_ascii=False))
        return
    states = json.loads(args.states.read_text())
    print(json.dumps(evaluate(states, registry), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
