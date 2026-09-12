#!/usr/bin/env python3
"""ARCHIVED 2026-09-12 (owner decision R3-D5): superseded by docs/product/FLAVOR_VECTOR_DESIGN_V1.md; frozen, not extended.
Round 2 — the single reader for what a session state actually says.

WHY THIS MODULE EXISTS
----------------------
Two defects motivated it, both found by feeding a real R9 state to the code
that claimed to be the product path.

ROUND2-OP2  output_generator_round2 read state["k1"]["dimensions"] as a list of
    {dimension_id, status} rows. The frozen R9 schema, enforced by
    output_policy_r9._supported_profile_rows and exercised in
    test_output_policy_r9, is a Mapping {dimension_id: {"supported": float}}.
    Iterating a Mapping yields strings, so the generator raised
    AttributeError on every real state. It had only ever been run on states
    the operator invented to match his own misreading.

ROUND2-OP3  The same reader took direct evidence only from
    qa_pairs[].selected_option_ids, requiring each option id to be a
    NAMED_DESCRIPTOR in the registry. No option id in the product ever is: all
    28 options across the 8 question axes are partition names ("citrus",
    "nuts", "white_floral"), none of which are registry concepts. Direct
    evidence was therefore structurally unreachable, every session fell
    through to dimension-level output, and that -- not the inference rule --
    is the origin of the over-normalisation the owner asked about.
    state["k1"]["confirmed_concepts"] was also ignored.

THE PARTITION RULE
------------------
A question option names a partition, and a partition names a SET of concepts.
Set size is what evidence strength means here:

    |partition| == 1   the answer pins exactly one concept. This is direct
                       evidence about that concept and is treated as such.
    |partition| > 1    the answer constrains the candidate set but names no
                       single concept. It is set evidence: it covers the
                       dimension and narrows candidates, and it must NOT be
                       promoted into a claim about any one member.

13 of the 23 partitions are singletons, so this rule is what makes direct
evidence reachable at all. Promoting a multi-member partition to its members
would be the system inventing a specificity the participant never expressed.

Standard library only; this module is on the runtime path.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
AXIS_TSV = ROOT / "db/data/product-inference-v0/PRODUCT_QUESTION_AXIS.tsv"

SUPPORTED = "SUPPORTED_WITHIN_SCOPE"
PROPOSED = "PROPOSED"

# Option tokens that carry no partition. "none" and "unsure" are abstention.
NON_PARTITION_OPTIONS = frozenset({"other", "none", "unsure"})


def load_partitions(path: Path | None = None) -> dict[str, set[str]]:
    """partition name -> concept ids, unioned across every axis that defines it.

    Several axes define the same partition name (citrus and citrus_like both
    resolve to lemon+orange). Union is safe because the definitions agree; a
    disagreement would widen the set, which errs toward less specificity
    rather than more.
    """
    path = path or AXIS_TSV
    partitions: dict[str, set[str]] = {}
    if not path.exists():
        return partitions
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            raw = row.get("candidate_partitions_json") or "{}"
            for name, members in json.loads(raw).items():
                partitions.setdefault(name, set()).update(members)
    return partitions


def normalise_k1_dimensions(state: Mapping[str, Any]) -> dict[str, str]:
    """dimension id -> SUPPORTED_WITHIN_SCOPE | PROPOSED, from either schema.

    Canonical (frozen R9): {"fruity": {"supported": 1.0}, "sweet": {"supported": 0.0}}
        supported > 0 is SUPPORTED; presence with 0 is PROPOSED, matching
        output_policy_r9, which admits a direction only when supported > 0.
    Legacy: [{"dimension_id": ..., "status": ...}] -- the operator's own shape,
        accepted so existing round 2 fixtures keep working.
    """
    k1 = state.get("k1") or {}
    dimensions = k1.get("dimensions")
    status: dict[str, str] = {}

    if isinstance(dimensions, Mapping):
        for did, entry in dimensions.items():
            if isinstance(entry, Mapping):
                try:
                    value = float(entry.get("supported", 0))
                except (TypeError, ValueError):
                    value = 0.0
            else:
                try:
                    value = float(entry)
                except (TypeError, ValueError):
                    value = 0.0
            status[did] = SUPPORTED if value > 0 else PROPOSED
    elif isinstance(dimensions, list):
        for row in dimensions:
            if not isinstance(row, Mapping):
                continue
            did, raw = row.get("dimension_id"), row.get("status")
            if did and raw in (SUPPORTED, PROPOSED):
                # SUPPORTED wins if a dimension appears twice
                if status.get(did) != SUPPORTED:
                    status[did] = raw
    return status


def read_evidence(
    state: Mapping[str, Any],
    registry: Mapping[str, Any],
    partitions: Mapping[str, set[str]] | None = None,
) -> dict[str, Any]:
    """Everything the state says, separated by what kind of claim it supports.

    direct        concepts the participant pinned: a registry concept chosen
                  outright, a singleton partition, or a k1 confirmed concept.
    set_evidence  partition name -> members, for multi-member answers. Narrows
                  candidates and covers dimensions; names no single concept.
    dim_status    dimension id -> SUPPORTED_WITHIN_SCOPE | PROPOSED.
    abstentions   options carrying no partition, kept so a later stop rule can
                  tell "no answer" from "answered nothing useful".
    """
    partitions = load_partitions() if partitions is None else partitions

    direct: set[str] = set()
    set_evidence: dict[str, set[str]] = {}
    abstentions: list[str] = []

    def named(cid: str) -> bool:
        return registry.get(cid, {}).get("role") == "NAMED_DESCRIPTOR"

    for qa in state.get("qa_pairs", []) or []:
        for option in qa.get("selected_option_ids", []) or []:
            if option in NON_PARTITION_OPTIONS:
                abstentions.append(option)
                continue
            if named(option):  # an option that is itself a registry concept
                direct.add(option)
                continue
            members = partitions.get(option)
            if not members:
                continue
            usable = {m for m in members if named(m)}
            if len(usable) == 1:
                direct |= usable  # singleton partition pins one concept
            elif usable:
                set_evidence[option] = usable

    # k1 confirmed concepts are settled evidence, not a proposal.
    for cid in (state.get("k1") or {}).get("confirmed_concepts", []) or []:
        if named(cid):
            direct.add(cid)

    return {
        "direct": direct,
        "set_evidence": set_evidence,
        "dim_status": normalise_k1_dimensions(state),
        "abstentions": abstentions,
    }


def dimensions_of(registry: Mapping[str, Any], cid: str) -> list[str]:
    return registry.get(cid, {}).get("support_dimension_ids", []) or []


def covered_dimensions(
    registry: Mapping[str, Any], evidence: Mapping[str, Any]
) -> set[str]:
    """Dimensions spoken for by direct OR set evidence.

    Set evidence covers a dimension: answering "citrus" means the fruity
    dimension has been addressed, even though no single fruit was named.
    """
    covered: set[str] = set()
    for cid in evidence["direct"]:
        covered.update(dimensions_of(registry, cid))
    for members in evidence["set_evidence"].values():
        for cid in members:
            covered.update(dimensions_of(registry, cid))
    return covered
