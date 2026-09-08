#!/usr/bin/env python3
"""Round 2 — propositions, extents, and minimal sufficient generalisation.

THE IDEA THE OWNER PROPOSED, DERIVED RATHER THAN STIPULATED
-----------------------------------------------------------
The owner's design has a three-rung ladder (L1 specific word, L2 middle
category, L3 direction) and a saturation score. Implemented literally, the rung
of each concept is hardcoded and the saturation constants are magic numbers.

The same behaviour falls out of one definition, with no constants and no rungs:

    Every proposition P has an EXTENT: the set of specific concepts it claims.
        sensory.lemon    -> {lemon}
        broad.citrus     -> {lemon, orange}
        attribute.fruity -> all 22 fruity words

    Every answer yields a CONSTRAINT: the set the participant's referent lies
    in.  A singleton partition gives {lemon}. Answering "citrus" gives
    {lemon, orange}. A supported k1 dimension gives that dimension's words.

    P is ENTAILED by constraint S  iff  S subset-of extent(P).

    The MINIMAL SUFFICIENT GENERALISATION of S is the entailed P with the
    smallest extent.

The ladder is then a consequence, not a rule:
    S = {lemon}          -> sensory.lemon            (the specific word)
    S = {lemon, orange}  -> broad.citrus             (the middle category)
    S = all fruity words -> attribute.fruity         (the direction)

WHY THIS MATTERS MORE THAN TIDINESS
-----------------------------------
It makes over-claiming structurally impossible. broad.citrus is NOT entailed by
fruity-level evidence, because {22 fruity words} is not a subset of
{lemon, orange}. The rung-based version had no such guard, and the shipped
generator did exactly this: broad.citrus was the only fruity representative, so
a participant whose evidence supported only "fruity" was told "citrus". Someone
who tasted mango was not being given a vaguer answer, but a wrong one.

Recorded as ROUND2-OP4. The collision was introduced when six dimension-level
broad concepts were layered into a namespace that already held three
sub-dimension ones (broad.chocolate, broad.citrus, broad.nutty from the sealed
R9 contract), and the generator treated all nine as interchangeable
"representative for dimension X".

EXTENTS ARE DECLARED, NEVER GUESSED
-----------------------------------
A concept's extent is a semantic claim and belongs to the owner, so it is read
from a governed file. A broad concept with no declared extent is UNUSABLE
rather than widened to its dimension: widening would keep the narrow label
while silently meaning the whole dimension, which is the same lie in reverse.

Standard library only; this module is on the runtime path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
ROUND2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
EXTENTS_PATH = ROUND2 / "concept_extents.json"

NAMED = "NAMED_DESCRIPTOR"
DIRECTION = "PROFILE_DIRECTION"


@dataclass(frozen=True)
class Proposition:
    concept_id: str
    role: str
    extent: frozenset[str]
    # DIMENSION_CLOSURE covers a whole dimension; SUB_DIMENSION covers part of
    # one. The distinction is what the shipped generator lacked.
    breadth: str
    declared: bool = True
    labels: Mapping[str, str] | None = field(default=None, compare=False)

    @property
    def size(self) -> int:
        return len(self.extent)


def specific_concepts(registry: Mapping[str, Any]) -> set[str]:
    """Named descriptors that are not category concepts. The ground set."""
    return {
        cid
        for cid, info in registry.items()
        if info.get("role") == NAMED and not cid.startswith("broad.")
    }


def dimension_closure(registry: Mapping[str, Any], dimensions: set[str]) -> frozenset[str]:
    """Every specific concept belonging to any of these dimensions."""
    return frozenset(
        cid
        for cid in specific_concepts(registry)
        if set(registry[cid].get("support_dimension_ids") or []) & dimensions
    )


def load_declared_extents(path: Path | None = None) -> dict[str, list[str]]:
    path = path or EXTENTS_PATH
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("declared_extents", {})


def build_propositions(
    registry: Mapping[str, Any],
    declared: Mapping[str, list[str]] | None = None,
) -> dict[str, Proposition]:
    """One proposition per usable concept, keyed by concept id.

    Concepts whose extent cannot be established are omitted. Their absence is
    reported by unusable_concepts() so the gap is visible rather than silently
    filled.
    """
    declared = load_declared_extents() if declared is None else declared
    ground = specific_concepts(registry)
    props: dict[str, Proposition] = {}

    for cid, info in registry.items():
        role = info.get("role")
        dims = set(info.get("support_dimension_ids") or [])
        labels = info.get("labels")

        if role == NAMED and cid in ground:
            props[cid] = Proposition(cid, role, frozenset({cid}), "SPECIFIC", True, labels)
            continue

        closure = dimension_closure(registry, dims)

        if role == NAMED:  # a broad.* category
            if cid in declared:
                extent = frozenset(declared[cid]) & ground
                if not extent:
                    continue
                breadth = "DIMENSION_CLOSURE" if extent == closure else "SUB_DIMENSION"
                props[cid] = Proposition(cid, role, extent, breadth, True, labels)
            # undeclared broad concepts are omitted on purpose
            continue

        if role == DIRECTION and closure:
            props[cid] = Proposition(cid, role, closure, "DIMENSION_CLOSURE", True, labels)

    return props


def unusable_concepts(
    registry: Mapping[str, Any], declared: Mapping[str, list[str]] | None = None
) -> list[str]:
    """Broad concepts that cannot be used because no extent is declared."""
    declared = load_declared_extents() if declared is None else declared
    return sorted(
        cid
        for cid, info in registry.items()
        if info.get("role") == NAMED
        and cid.startswith("broad.")
        and cid not in declared
    )


def entails(prop: Proposition, constraint: frozenset[str]) -> bool:
    """P is entailed by S when everything S allows is something P already claims."""
    return bool(constraint) and constraint <= prop.extent


def minimal_sufficient_generalisation(
    constraint: frozenset[str],
    propositions: Mapping[str, Proposition],
    roles: tuple[str, ...] = (NAMED,),
) -> Proposition | None:
    """The most specific proposition of an allowed role that is entailed by S.

    Ties in extent size are broken by concept id, which is declared here as a
    tiebreak only. Ordering is by extent size first, never by spelling: the
    standing rule adopted after three separate defects in this project turned
    out to be lexicographic accident acting as a decision rule.
    """
    candidates = [
        p for p in propositions.values() if p.role in roles and entails(p, constraint)
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda p: (p.size, p.concept_id))


def constraints_from_evidence(
    evidence: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Turn read_evidence() output into constraint sets, most specific first.

    Each constraint records where it came from, so a later report can say why a
    given word was shown without re-deriving it.
    """
    out: list[dict[str, Any]] = []
    for cid in sorted(evidence.get("direct", ())):
        out.append({"source": "DIRECT", "origin": cid, "constraint": frozenset({cid})})
    for name, members in sorted(evidence.get("set_evidence", {}).items()):
        out.append({"source": "PARTITION", "origin": name, "constraint": frozenset(members)})
    for did, status in sorted(evidence.get("dim_status", {}).items()):
        closure = dimension_closure(registry, {did})
        if closure:
            out.append(
                {
                    "source": "DIMENSION",
                    "origin": did,
                    "status": status,
                    "constraint": closure,
                }
            )
    out.sort(key=lambda row: (len(row["constraint"]), row["origin"]))
    return out
