#!/usr/bin/env python3
"""Round 2 — measure over-normalisation directly instead of arguing about it.

The owner's question is whether a small corpus forces the system to answer
nearly the same thing every time. That is not a matter of opinion: the answer
space is finite and enumerable, so it can be counted.

METHOD
    Walk every reachable answer path. The axis at each step is chosen by the
    product's own strategy (select_next_axis), and every option combination the
    axis permits is expanded, to the absolute five-question limit. Each leaf
    produces one output; distinct outputs are counted.

WHAT IS COMPARED
    shipped     output_generator_round2, the current declared product path
    machine     inference_state_machine_round2, minimal sufficient generalisation
    machine+F   the same, with a proposed dimension-level broad.fruity, which
                today is the only large dimension with no honest middle category

Measurement only. No fitting, no corpus written, nothing admitted.
"""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from evidence_reader_round2 import NON_PARTITION_OPTIONS  # noqa: E402
from output_generator_round2 import load_registry  # noqa: E402
import output_generator_round2 as shipped  # noqa: E402
from proposition_lattice_round2 import (  # noqa: E402
    build_propositions,
    dimension_closure,
    load_declared_extents,
    specific_concepts,
)
import inference_state_machine_round2 as fsm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"

MAX_LEAVES = 200_000


def _dim_status(state: fsm.InferenceState, registry: Mapping[str, Any]) -> dict[str, str]:
    """Dimensions the answers have actually touched, marked supported."""
    status: dict[str, str] = {}
    for branch in state.branches:
        for cid in branch.constraint:
            for dim in registry.get(cid, {}).get("support_dimension_ids") or []:
                status[dim] = fsm.SUPPORTED
    return status


def _option_choices(axis: fsm.Axis) -> list[tuple[str, ...]]:
    """Every selection the axis permits, including abstention."""
    real = [o for o in axis.options if o not in NON_PARTITION_OPTIONS and o in axis.partitions]
    choices: list[tuple[str, ...]] = [("unsure",)]
    for size in range(1, max(1, axis.max_selected) + 1):
        choices.extend(combinations(real, size))
    return choices


def enumerate_leaves(
    registry: Mapping[str, Any],
    axes: Mapping[str, fsm.Axis],
    propositions: Mapping[str, Any],
    require_eligible: bool = False,
) -> list[dict[str, Any]]:
    """All reachable sessions. Eligibility is off by default because all eight
    axes carry product_use_eligible=false, so requiring it yields no sessions
    at all; that fact is reported separately rather than silently emptying the
    measurement."""
    leaves: list[dict[str, Any]] = []
    start = fsm.InferenceState(ground=frozenset(specific_concepts(registry)))

    def walk(state: fsm.InferenceState, previous: fsm.InferenceState | None) -> None:
        if len(leaves) >= MAX_LEAVES:
            return
        state.dim_status = _dim_status(state, registry)
        stop, reason = fsm.should_stop(state, previous, axes, require_eligible)
        if stop:
            leaves.append({"state": state, "stop_reason": reason})
            return
        axis_id = fsm.select_next_axis(state, axes, require_eligible)
        if axis_id is None:
            leaves.append({"state": state, "stop_reason": "NO_ELIGIBLE_AXIS_REMAINS"})
            return
        for selection in _option_choices(axes[axis_id]):
            walk(fsm.apply_answer(state, axis_id, selection, axes), state)

    walk(start, None)
    return leaves


def _shipped_state(state: fsm.InferenceState, registry: Mapping[str, Any]) -> dict[str, Any]:
    """Recast a machine state into the frozen R9 state shape the shipped path reads."""
    options: list[str] = []
    for branch in state.branches:
        options.extend(branch.origins)
    return {
        "qa_pairs": [{"selected_option_ids": options}],
        "k1": {
            "confirmed_concepts": [],
            "dimensions": {d: {"supported": 1.0} for d in state.dim_status},
        },
    }


def _signature(output: Mapping[str, Any]) -> tuple:
    return (
        tuple(r["candidate_id"] for r in output["main"]),
        tuple(r["candidate_id"] for r in output["secondary"]),
        tuple(r["candidate_id"] for r in output["overall_profile"]),
    )


def measure(
    registry: Mapping[str, Any],
    propositions: Mapping[str, Any],
    leaves: list[dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    signatures: Counter = Counter()
    main_signatures: Counter = Counter()
    empty_main = specific_main = 0
    concept_use: Counter = Counter()

    for leaf in leaves:
        output = fsm.build_output(leaf["state"], registry, propositions)
        sig = _signature(output)
        signatures[sig] += 1
        main_signatures[sig[0]] += 1
        if not sig[0]:
            empty_main += 1
        elif any(not c.startswith("broad.") for c in sig[0]):
            specific_main += 1
        for cid in sig[0] + sig[1]:
            concept_use[cid] += 1

    total = len(leaves) or 1
    top_share = signatures.most_common(1)[0][1] / total if signatures else 0.0
    return {
        "variant": label,
        "sessions_enumerated": len(leaves),
        "distinct_outputs": len(signatures),
        "distinct_main_sets": len(main_signatures),
        "most_common_output_share": round(top_share, 4),
        "sessions_with_empty_main": empty_main,
        "sessions_naming_a_specific_word": specific_main,
        "specific_word_rate": round(specific_main / total, 4),
        "distinct_concepts_ever_shown": len(concept_use),
        "most_shown_concepts": concept_use.most_common(8),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()

    registry = dict(load_registry())
    axes = fsm.load_axes()
    declared = dict(load_declared_extents())

    leaves = enumerate_leaves(registry, axes, build_propositions(registry, declared))

    results = [measure(registry, build_propositions(registry, declared), leaves, "machine")]

    # Variant: give fruity an honest dimension-level category.
    with_fruity_registry = dict(registry)
    with_fruity_registry["broad.fruity"] = {
        "role": "NAMED_DESCRIPTOR",
        "support_dimension_ids": ["fruity"],
        "labels": {"en": "Fruity", "zhHans": "水果类"},
    }
    declared_plus = dict(declared)
    declared_plus["broad.fruity"] = sorted(dimension_closure(with_fruity_registry, {"fruity"}))
    results.append(
        measure(
            with_fruity_registry,
            build_propositions(with_fruity_registry, declared_plus),
            leaves,
            "machine+broad.fruity",
        )
    )

    # The shipped path, over the same sessions.
    shipped_sigs: Counter = Counter()
    shipped_specific = 0
    shipped_failures = 0
    for leaf in leaves:
        try:
            output = shipped.generate_output(_shipped_state(leaf["state"], registry), registry)
        except Exception:  # noqa: BLE001 - a crash is a result, not an abort
            shipped_failures += 1
            continue
        sig = _signature(output)
        shipped_sigs[sig] += 1
        if sig[0] and any(not c.startswith("broad.") for c in sig[0]):
            shipped_specific += 1
    total = len(leaves) or 1
    results.insert(
        0,
        {
            "variant": "shipped (output_generator_round2)",
            "sessions_enumerated": len(leaves),
            "distinct_outputs": len(shipped_sigs),
            "most_common_output_share": round(
                shipped_sigs.most_common(1)[0][1] / total, 4
            )
            if shipped_sigs
            else None,
            "sessions_naming_a_specific_word": shipped_specific,
            "specific_word_rate": round(shipped_specific / total, 4),
            "crashes": shipped_failures,
        },
    )

    report = {
        "contract_version": "round2.output-diversity.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "Does the small corpus force the system to answer nearly the same thing every time?",
        "method": {
            "enumeration": "every reachable answer path, axis chosen by the product's own select_next_axis, to the five-question limit",
            "abstention": "each axis expansion includes an 'unsure' branch",
            "eligibility_note": "all 8 axes carry product_use_eligible=false with reason INFORMATION_GAIN_AND_USER_COMPREHENSION_NOT_VALIDATED; enumeration ignores that flag, so these figures describe the mechanism, not a shippable question set",
        },
        "resolution_limit": {
            "specific_concepts": len(specific_concepts(registry)),
            "cells_from_dimensions_alone": None,
            "note": "see partition_resolution below",
        },
        "variants": results,
        "guards": {"records_admitted": 0, "corpus_written": False, "fit_count": 0},
    }
    (args.output_dir / "output_diversity_measurement.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
