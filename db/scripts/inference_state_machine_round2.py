#!/usr/bin/env python3
"""ARCHIVED 2026-09-12 (owner decision R3-D5): superseded by docs/product/FLAVOR_VECTOR_DESIGN_V1.md; frozen, not extended.
Round 2 — the session as a finite state machine over pure strategies.

Everything here is deterministic: no fitting, no model, no randomness. Given a
state, each strategy is a pure function returning an action.

BRANCHES, NOT ONE REFERENT
--------------------------
A session is not narrowing toward a single answer. A coffee can be fruity and
sweet at once, and the product returns up to three descriptors. So the state
carries a LIST of constraints, one per branch the participant opened.

The question axes are hierarchical, which the data states plainly:
family_direction offers fruit / floral_tea / cocoa_nut_caramel..., and
fruit_region then splits fruit into citrus / berry. So a later answer REFINES
the branch it intersects and OPENS a branch when it intersects none. Refinement
is intersection within a branch; separate branches never intersect each other.

Modelling the whole session as one intersection would be wrong: answering
"fruit" then "nuts" would yield the empty set and the participant would be told
nothing, when they have in fact said two things.

WHAT DECIDES THE NEXT QUESTION
------------------------------
The gap, not a static information-gain table. The coarsest open branch is the
one the output cannot yet describe specifically, so the chosen axis is the one
that splits it best. Ties are broken by declared order, never by spelling.

Standard library only; this module is on the runtime path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from evidence_reader_round2 import (
    NON_PARTITION_OPTIONS,
    load_partitions,
    normalise_k1_dimensions,
)
from proposition_lattice_round2 import (
    DIRECTION,
    NAMED,
    Proposition,
    build_propositions,
    dimension_closure,
    minimal_sufficient_generalisation as msg,
    specific_concepts,
)

ROOT = Path(__file__).resolve().parents[2]
AXIS_TSV = ROOT / "db/data/product-inference-v0/PRODUCT_QUESTION_AXIS.tsv"

SUPPORTED = "SUPPORTED_WITHIN_SCOPE"

# PRODUCT_QUESTION_FLOW.tsv: Q1 mandatory, Q2-Q4 governed, Q5 opt-in behind an
# absolute five-question limit.
ABSOLUTE_QUESTION_LIMIT = 5


@dataclass(frozen=True)
class Axis:
    axis_id: str
    partitions: dict[str, frozenset[str]]
    options: tuple[str, ...]
    max_selected: int
    product_use_eligible: bool
    ineligibility_reason: str


def load_axes(path: Path | None = None) -> dict[str, Axis]:
    path = path or AXIS_TSV
    axes: dict[str, Axis] = {}
    if not path.exists():
        return axes
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            parts = {
                name: frozenset(members)
                for name, members in json.loads(
                    row.get("candidate_partitions_json") or "{}"
                ).items()
            }
            try:
                max_selected = int(row.get("maximum_selected_options") or 1)
            except ValueError:
                max_selected = 1
            axes[row["question_axis_id"]] = Axis(
                axis_id=row["question_axis_id"],
                partitions=parts,
                options=tuple(json.loads(row.get("option_concepts_json") or "[]")),
                max_selected=max_selected,
                product_use_eligible=(row.get("product_use_eligible") == "true"),
                ineligibility_reason=row.get("product_ineligibility_reason", ""),
            )
    return axes


@dataclass
class Branch:
    """One thing the participant has said, progressively narrowed."""

    constraint: frozenset[str]
    origins: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.constraint)


@dataclass
class InferenceState:
    ground: frozenset[str]
    branches: list[Branch] = field(default_factory=list)
    dim_status: dict[str, str] = field(default_factory=dict)
    asked_axes: list[str] = field(default_factory=list)
    abstentions: list[str] = field(default_factory=list)
    max_questions: int = ABSOLUTE_QUESTION_LIMIT

    @property
    def question_count(self) -> int:
        return len(self.asked_axes)

    def snapshot(self) -> tuple:
        """Comparable summary, used by the stop rule to detect a stalled turn."""
        return (
            tuple(sorted(tuple(sorted(b.constraint)) for b in self.branches)),
            tuple(sorted(self.dim_status.items())),
        )


def initial_state(
    registry: Mapping[str, Any], state: Mapping[str, Any] | None = None
) -> InferenceState:
    ground = frozenset(specific_concepts(registry))
    inference = InferenceState(ground=ground)
    if state:
        inference.dim_status = normalise_k1_dimensions(state)
    return inference


def apply_answer(
    state: InferenceState,
    axis_id: str,
    selected_options: Sequence[str],
    axes: Mapping[str, Axis],
    partitions: Mapping[str, frozenset[str]] | None = None,
) -> InferenceState:
    """Refine the branch an answer intersects; open a branch when it intersects none.

    Pure with respect to the caller: a new state is returned and the input is
    left untouched, so a strategy may explore an answer without committing it.
    """
    partitions = partitions or {
        name: frozenset(members) for name, members in load_partitions().items()
    }
    axis = axes.get(axis_id)
    lookup = dict(partitions)
    if axis:
        lookup.update(axis.partitions)

    branches = [Branch(b.constraint, list(b.origins)) for b in state.branches]
    abstentions = list(state.abstentions)

    for option in selected_options:
        if option in NON_PARTITION_OPTIONS:
            abstentions.append(option)
            continue
        members = lookup.get(option)
        if not members:
            continue
        target = None
        for branch in branches:
            if branch.constraint & members:
                target = branch
                break
        if target is None:
            branches.append(Branch(frozenset(members), [option]))
        else:
            refined = target.constraint & members
            if refined:  # an empty refinement would erase what was already said
                target.constraint = refined
                target.origins.append(option)

    return InferenceState(
        ground=state.ground,
        branches=branches,
        dim_status=dict(state.dim_status),
        asked_axes=[*state.asked_axes, axis_id],
        abstentions=abstentions,
        max_questions=state.max_questions,
    )


# ---------------------------------------------------------------- strategies


def split_quality(axis: Axis, constraint: frozenset[str]) -> tuple[int, int]:
    """How well an axis divides one constraint.

    Returns (cells_touched, largest_remaining). A higher first value and a
    lower second value is better; an axis that cannot touch the constraint
    scores (0, len(constraint)).
    """
    touched = [p & constraint for p in axis.partitions.values() if p & constraint]
    if not touched:
        return (0, len(constraint))
    return (len(touched), max(len(t) for t in touched))


def select_next_axis(
    state: InferenceState,
    axes: Mapping[str, Axis],
    require_product_eligible: bool = True,
) -> str | None:
    """The axis that best splits the coarsest branch the output cannot yet name.

    Returns None when nothing is left to ask, which the stop rule reads as
    exhaustion rather than as an error.
    """
    open_branches = [b for b in state.branches if b.size > 1] or state.branches
    available = [
        axis
        for axis_id, axis in axes.items()
        if axis_id not in state.asked_axes
        and (axis.product_use_eligible or not require_product_eligible)
    ]
    if not available:
        return None

    if not open_branches:
        # Nothing said yet: open with the axis touching the most ground.
        best = max(
            available,
            key=lambda a: (len({c for p in a.partitions.values() for c in p}), a.axis_id),
        )
        return best.axis_id

    target = max(open_branches, key=lambda b: (b.size, sorted(b.constraint)[0]))
    scored = []
    for axis in available:
        cells, largest = split_quality(axis, target.constraint)
        if cells > 1:  # an axis that cannot divide the branch teaches nothing
            scored.append((cells, -largest, axis.axis_id, axis))
    if not scored:
        return None
    scored.sort(key=lambda row: (-row[0], -row[1], row[2]))
    return scored[0][3].axis_id


def should_stop(
    state: InferenceState,
    previous: InferenceState | None,
    axes: Mapping[str, Axis],
    require_product_eligible: bool = True,
) -> tuple[bool, str]:
    if state.question_count >= state.max_questions:
        return True, "ABSOLUTE_QUESTION_LIMIT"
    if previous is not None and state.snapshot() == previous.snapshot():
        return True, "NO_NEW_EVIDENCE_FROM_LAST_ANSWER"
    if state.branches and all(b.size == 1 for b in state.branches):
        return True, "ALL_BRANCHES_PINNED"
    if select_next_axis(state, axes, require_product_eligible) is None:
        return True, "NO_ELIGIBLE_AXIS_REMAINS"
    return False, "CONTINUE"


# ------------------------------------------------------------------- output


def build_output(
    state: InferenceState,
    registry: Mapping[str, Any],
    propositions: Mapping[str, Proposition] | None = None,
    main_max: int = 3,
    secondary_max: int = 2,
    profile_max: int = 3,
) -> dict[str, Any]:
    """3 + 2 + 3, filled by minimal sufficient generalisation.

    Ordering is by extent size, so the most specific honest statement is shown
    first, with concept id as a declared tiebreak only. Role separation is
    absolute: main and secondary carry NAMED_DESCRIPTOR, overall_profile
    carries PROFILE_DIRECTION. A direction never occupies a main slot, because
    it would then also appear in overall_profile, which draws from the same
    activated dimensions.
    """
    propositions = propositions or build_propositions(registry)

    # ---- main: the most specific honest statement per branch ---------------
    named_hits: list[tuple[int, str, list[str]]] = []
    unnameable: list[Branch] = []
    for branch in state.branches:
        hit = msg(branch.constraint, propositions, (NAMED,))
        if hit is None:
            unnameable.append(branch)
        else:
            named_hits.append((hit.size, hit.concept_id, branch.origins))

    named_hits.sort(key=lambda row: (row[0], row[1]))
    seen: set[str] = set()
    ordered: list[tuple[int, str, list[str]]] = []
    for row in named_hits:
        if row[1] not in seen:
            seen.add(row[1])
            ordered.append(row)

    main = [cid for _, cid, _ in ordered[:main_max]]
    overflow = [cid for _, cid, _ in ordered[main_max:]]

    # ---- coverage --------------------------------------------------------
    covered: set[str] = set()
    for cid in main:
        covered.update(registry.get(cid, {}).get("support_dimension_ids") or [])
    for branch in state.branches:
        for cid in branch.constraint:
            covered.update(registry.get(cid, {}).get("support_dimension_ids") or [])

    # ---- secondary: stated-but-unshown first, then uncovered dimensions ---
    # D1 stands: something the participant said is never displaced by a
    # representative the system chose.
    secondary: list[str] = overflow[:secondary_max]
    slots = secondary_max - len(secondary)

    uncovered = [d for d in state.dim_status if d not in covered]
    uncovered.sort(key=lambda d: (0 if state.dim_status[d] == SUPPORTED else 1, d))
    for dimension in uncovered:
        if slots <= 0:
            break
        closure = dimension_closure(registry, {dimension})
        hit = msg(closure, propositions, (NAMED,))
        if hit is None or hit.concept_id in main or hit.concept_id in secondary:
            continue
        secondary.append(hit.concept_id)
        slots -= 1

    # ---- overall_profile: directions for activated dimensions ------------
    profile_rows: list[tuple[int, str]] = []
    for dimension, status in state.dim_status.items():
        closure = dimension_closure(registry, {dimension})
        hit = msg(closure, propositions, (DIRECTION,))
        if hit is not None:
            profile_rows.append((0 if status == SUPPORTED else 1, hit.concept_id))
    for branch in state.branches:
        hit = msg(branch.constraint, propositions, (DIRECTION,))
        if hit is not None:
            profile_rows.append((0, hit.concept_id))
    profile_rows.sort(key=lambda row: (row[0], row[1]))
    profile: list[str] = []
    for _, cid in profile_rows:
        if cid not in profile:
            profile.append(cid)
    profile = profile[:profile_max]

    return {
        "main": [{"candidate_id": c} for c in main],
        "secondary": [{"candidate_id": c} for c in secondary],
        "overall_profile": [{"candidate_id": c} for c in profile],
        "_diagnostics": {
            "branches": [
                {"origins": b.origins, "size": b.size, "members": sorted(b.constraint)}
                for b in state.branches
            ],
            "branches_with_no_nameable_generalisation": [
                {"origins": b.origins, "size": b.size} for b in unnameable
            ],
            "questions_asked": list(state.asked_axes),
            "abstentions": list(state.abstentions),
            "covered_dimensions": sorted(covered),
            "uncovered_activated_dimensions": uncovered,
        },
    }


def run_session(
    registry: Mapping[str, Any],
    answers: Sequence[tuple[str, Sequence[str]]],
    state: Mapping[str, Any] | None = None,
    axes: Mapping[str, Axis] | None = None,
) -> dict[str, Any]:
    """Replay a fixed answer sequence through the machine. Used by measurement."""
    axes = axes or load_axes()
    current = initial_state(registry, state)
    for axis_id, selected in answers:
        current = apply_answer(current, axis_id, selected, axes)
    return build_output(current, registry)
