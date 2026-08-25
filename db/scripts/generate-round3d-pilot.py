#!/usr/bin/env python3
"""Generate the deterministic Round 3D engineering pilot package.

The output contains planned material/schedule rows and conspicuous dry-run
fixtures. It contains no collected human or sensory observation.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "db" / "data" / "round3d" / "generated"
SEED = "coffee-context-calibration-minimum-pilot-20260825-v1"
ROASTS = (
    "extremely_light",
    "light",
    "medium_light",
    "medium",
    "medium_dark",
    "dark",
    "extremely_dark",
)
FULL_FAMILIES = ("filter_percolation", "immersion", "espresso_pressure")
ANCHOR_FAMILIES = (
    "hybrid",
    "diluted_espresso",
    "cold_extraction",
    "espresso_milk",
)
ANCHOR_ROASTS = ("light", "medium", "dark")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_tsv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def stable_shuffle(values: list[str], namespace: str) -> list[str]:
    rng = random.Random(f"{SEED}:{namespace}")
    result = values.copy()
    rng.shuffle(result)
    return result


def blinded_codes(session_key: str, count: int) -> list[str]:
    pool = [f"{value:03d}" for value in range(100, 1000)]
    return stable_shuffle(pool, f"blind:{session_key}")[:count]


def build() -> dict[str, object]:
    lots = [
        {
            "coffee_lot_key": f"pilot.round3d.lot_{index:02d}",
            "public_lot_code": f"PILOT-LOT-{index:02d}",
            "record_status": "PLANNED_PHYSICAL_MATERIAL",
        }
        for index in range(1, 3)
    ]

    roast_batches: list[dict[str, object]] = []
    for lot in lots:
        lot_number = lot["public_lot_code"][-2:]
        for roast_position, roast in enumerate(ROASTS, start=1):
            roast_batches.append(
                {
                    "roast_batch_key": f"pilot.round3d.lot_{lot_number}.roast.{roast}",
                    "coffee_lot_key": lot["coffee_lot_key"],
                    "roast_category_key": f"roast.project_v1.{roast}",
                    "batch_code": f"PILOT-L{lot_number}-R{roast_position:02d}",
                    "record_status": "PLANNED_PHYSICAL_MATERIAL",
                }
            )

    recipes = {
        "filter_percolation": {"dose_g": 15, "water_g": 250, "mode": "filter"},
        "immersion": {"dose_g": 15, "water_g": 250, "mode": "immersion"},
        "espresso_pressure": {"dose_g": 18, "beverage_g": 40, "mode": "espresso"},
        "hybrid": {"dose_g": 15, "water_g": 230, "mode": "manual_pressure"},
        "diluted_espresso": {"espresso_g": 40, "water_g": 160, "mode": "espresso_water"},
        "cold_extraction": {"dose_g": 20, "water_g": 240, "mode": "cold_immersion"},
        "espresso_milk": {"espresso_g": 40, "milk_g": 120, "mode": "dairy_milk"},
    }
    preparations: list[dict[str, object]] = []
    for family in (*FULL_FAMILIES, *ANCHOR_FAMILIES):
        preparations.append(
            {
                "preparation_condition_key": f"pilot.round3d.preparation.{family}",
                "preparation_concept_key": f"preparation.family.{family}",
                "condition_code": f"PILOT-{family.upper()}",
                "coffee_mode_code": "milk_coffee"
                if family == "espresso_milk"
                else "black_coffee",
                "paired_black_condition_key": "pilot.round3d.preparation.espresso_pressure"
                if family == "espresso_milk"
                else "",
                "recipe_json": json.dumps(
                    recipes[family], sort_keys=True, separators=(",", ":")
                ),
            }
        )

    cells: list[tuple[dict[str, object], str, str]] = []
    for lot in lots:
        for roast in ROASTS:
            for family in FULL_FAMILIES:
                cells.append((lot, roast, family))
        for roast in ANCHOR_ROASTS:
            for family in ANCHOR_FAMILIES:
                cells.append((lot, roast, family))
    assert len(cells) == 66

    samples: list[dict[str, object]] = []
    for lot, roast, family in cells:
        lot_number = lot["public_lot_code"][-2:]
        for replicate in (1, 2):
            samples.append(
                {
                    "beverage_sample_key": (
                        f"pilot.round3d.sample.lot_{lot_number}.{roast}.{family}.rep_{replicate}"
                    ),
                    "coffee_lot_key": lot["coffee_lot_key"],
                    "roast_batch_key": f"pilot.round3d.lot_{lot_number}.roast.{roast}",
                    "preparation_condition_key": f"pilot.round3d.preparation.{family}",
                    "replicate_number": replicate,
                    "record_origin_code": "planned_real_sample",
                }
            )
    assert len(samples) == 132

    sample_keys = [str(row["beverage_sample_key"]) for row in samples]
    sample_order = stable_shuffle(sample_keys, "sample-order")
    sessions: list[dict[str, object]] = []
    presentations: list[dict[str, object]] = []

    def add_schedule(cohort: str, assessor_count: int, sessions_each: int, burden: int) -> None:
        total_sessions = assessor_count * sessions_each
        total_presentations = total_sessions * burden
        if cohort == "reference":
            scheduled = [
                sample_order[(index % 132 + (index // 132) * 17) % 132]
                for index in range(total_presentations)
            ]
        else:
            scheduled = [
                sample_order[(index % 132 + (index // 132) * 19) % 132]
                for index in range(total_presentations)
            ]
        for assessor in range(1, assessor_count + 1):
            for session_number in range(1, sessions_each + 1):
                session_index = (assessor - 1) * sessions_each + session_number - 1
                session_key = (
                    f"pilot.round3d.session_slot.{cohort}."
                    f"assessor_{assessor:03d}.session_{session_number:02d}"
                )
                sessions.append(
                    {
                        "session_slot_key": session_key,
                        "cohort_code": cohort,
                        "assessor_slot_code": f"{cohort.upper()}_SLOT_{assessor:03d}",
                        "session_number": session_number,
                        "sample_burden": burden,
                    }
                )
                codes = blinded_codes(session_key, burden)
                offset = session_index * burden
                for position in range(1, burden + 1):
                    presentations.append(
                        {
                            "presentation_slot_key": f"{session_key}.position_{position:02d}",
                            "session_slot_key": session_key,
                            "beverage_sample_key": scheduled[offset + position - 1],
                            "sequence_position": position,
                            "blinded_code": codes[position - 1],
                        }
                    )

    add_schedule("reference", 12, 6, 11)
    add_schedule("ordinary_user", 60, 2, 6)
    assert len(sessions) == 192
    assert len(presentations) == 1512

    question_slots: list[dict[str, object]] = []
    later_codes = ("fruit_direction", "sweet_direction", "roast_direction")
    ordinary_presentations = [
        row
        for row in presentations
        if ".ordinary_user." in str(row["presentation_slot_key"])
    ]
    for index, presentation in enumerate(ordinary_presentations):
        plan = (
            "family_direction",
            later_codes[index % len(later_codes)],
            later_codes[(index + 1) % len(later_codes)],
            "bright_acidity",
            "texture_direction",
        )
        for step, logical_code in enumerate(plan, start=1):
            question_slots.append(
                {
                    "question_assignment_slot_key": (
                        f"{presentation['presentation_slot_key']}.question_{step}"
                    ),
                    "presentation_slot_key": presentation["presentation_slot_key"],
                    "step_number": step,
                    "logical_question_code": logical_code,
                    "assignment_status": "mandatory"
                    if step == 1
                    else "conditional",
                }
            )
    assert len(question_slots) == 3600

    dry_runs = [
        {
            "dry_run_case_key": "dry_run.round3d.early_stop_q1",
            "c0_code": "filter_percolation",
            "c1_code": "light",
            "answer_path": "family_direction:fruit_bright",
            "expected_stop_step": 1,
            "explicit_override": "false",
            "fixture_label": "DRY_RUN_FIXTURE",
        },
        {
            "dry_run_case_key": "dry_run.round3d.continue_q2",
            "c0_code": "immersion",
            "c1_code": "medium",
            "answer_path": "family_direction:fruit_bright|fruit_direction:citrus",
            "expected_stop_step": 2,
            "explicit_override": "false",
            "fixture_label": "DRY_RUN_FIXTURE",
        },
        {
            "dry_run_case_key": "dry_run.round3d.refine_q4",
            "c0_code": "espresso_pressure",
            "c1_code": "medium_dark",
            "answer_path": "family_direction:cocoa_roast|roast_direction:cocoa_nut|sweet_direction:caramel|bright_acidity:soft_round",
            "expected_stop_step": 4,
            "explicit_override": "false",
            "fixture_label": "DRY_RUN_FIXTURE",
        },
        {
            "dry_run_case_key": "dry_run.round3d.exceptional_q5",
            "c0_code": "cold_extraction",
            "c1_code": "dark",
            "answer_path": "family_direction:fruit_bright|fruit_direction:dried_tropical|sweet_direction:honey|bright_acidity:juicy|texture_direction:juicy_silky",
            "expected_stop_step": 5,
            "explicit_override": "false",
            "fixture_label": "DRY_RUN_FIXTURE",
        },
        {
            "dry_run_case_key": "dry_run.round3d.user_override_jasmine",
            "c0_code": "filter_percolation",
            "c1_code": "dark",
            "answer_path": "family_direction:floral_tea|fruit_direction:citrus",
            "expected_stop_step": 2,
            "explicit_override": "true",
            "fixture_label": "DRY_RUN_FIXTURE",
        },
    ]

    write_tsv(
        OUTPUT / "coffee_lots.tsv",
        ("coffee_lot_key", "public_lot_code", "record_status"),
        lots,
    )
    write_tsv(
        OUTPUT / "roast_batches.tsv",
        (
            "roast_batch_key",
            "coffee_lot_key",
            "roast_category_key",
            "batch_code",
            "record_status",
        ),
        roast_batches,
    )
    write_tsv(
        OUTPUT / "preparation_conditions.tsv",
        (
            "preparation_condition_key",
            "preparation_concept_key",
            "condition_code",
            "coffee_mode_code",
            "paired_black_condition_key",
            "recipe_json",
        ),
        preparations,
    )
    write_tsv(
        OUTPUT / "beverage_samples.tsv",
        (
            "beverage_sample_key",
            "coffee_lot_key",
            "roast_batch_key",
            "preparation_condition_key",
            "replicate_number",
            "record_origin_code",
        ),
        samples,
    )
    write_tsv(
        OUTPUT / "session_slots.tsv",
        (
            "session_slot_key",
            "cohort_code",
            "assessor_slot_code",
            "session_number",
            "sample_burden",
        ),
        sessions,
    )
    write_tsv(
        OUTPUT / "presentation_slots.tsv",
        (
            "presentation_slot_key",
            "session_slot_key",
            "beverage_sample_key",
            "sequence_position",
            "blinded_code",
        ),
        presentations,
    )
    write_tsv(
        OUTPUT / "question_assignment_slots.tsv",
        (
            "question_assignment_slot_key",
            "presentation_slot_key",
            "step_number",
            "logical_question_code",
            "assignment_status",
        ),
        question_slots,
    )
    write_tsv(
        OUTPUT / "dry_run_cases.tsv",
        (
            "dry_run_case_key",
            "c0_code",
            "c1_code",
            "answer_path",
            "expected_stop_step",
            "explicit_override",
            "fixture_label",
        ),
        dry_runs,
    )

    split_inventory_path = OUTPUT / "split_inventory.json"
    split_inventory_path.write_text(
        json.dumps(
            {
                "status": "NOT_AVAILABLE_MINIMUM_TWO_LOT_FEASIBILITY_PILOT",
                "method": "lot_grouped",
                "development_lots": [],
                "validation_lots": [],
                "held_out_test_lots": [],
                "reason": "Two lots cannot support the frozen three-way performance split.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    baseline_analysis_path = OUTPUT / "baseline_analysis.json"
    baseline_analysis_path.write_text(
        json.dumps(
            {
                "analysis_status": "PASS_WITH_NOT_ESTIMABLE_OUTPUTS",
                "real_observation_count": 0,
                "fixture_observation_count": 5,
                "fixture_exclusion_pass": True,
                "deep_learning_model_run": False,
                "embedding_baseline_run": False,
                "pgvector_required": False,
                "outputs": {
                    key: "NOT_ESTIMABLE"
                    for key in (
                        "context_support_distributions",
                        "question_information_gain",
                        "candidate_ranking_baseline",
                        "average_questions_required",
                        "early_stop_rate",
                        "q2_marginal_value",
                        "q3_marginal_value",
                        "q4_marginal_value",
                        "q5_marginal_value",
                        "context_conflict_rate",
                        "explicit_user_override_rate",
                        "repeat_stability",
                        "assessor_uncertainty",
                    )
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    data_files = sorted(
        [*OUTPUT.glob("*.tsv"), split_inventory_path, baseline_analysis_path]
    )
    receipt = {
        "artifact_status": "ENGINEERING_PILOT_NO_REAL_OBSERVATIONS",
        "generator": "db/scripts/generate-round3d-pilot.py",
        "randomization_seed": SEED,
        "matrix_sha256": digest(OUTPUT / "beverage_samples.tsv"),
        "randomization_sha256": digest(OUTPUT / "presentation_slots.tsv"),
        "question_bank_source_sha256": digest(
            ROOT / "db" / "028_calibration_question_bank_and_plan_seed.sql"
        ),
        "protocol_sha256": digest(
            ROOT
            / "docs"
            / "protocols"
            / "COFFEE_SENSORY_CONTEXT_CALIBRATION_PROTOCOL_V0.md"
        ),
        "split_inventory_sha256": digest(split_inventory_path),
        "counts": {
            "coffee_lots": len(lots),
            "roast_batches": len(roast_batches),
            "preparation_families": len(preparations),
            "roast_categories": len(ROASTS),
            "condition_cells": len(cells),
            "beverage_samples": len(samples),
            "session_slots": len(sessions),
            "reference_presentations": 792,
            "ordinary_user_presentations": 720,
            "presentation_slots": len(presentations),
            "question_assignment_slots": len(question_slots),
            "dry_run_fixtures": len(dry_runs),
            "real_observations": 0,
        },
        "files": {
            path.name: {"sha256": digest(path), "bytes": path.stat().st_size}
            for path in data_files
        },
    }
    receipt_path = OUTPUT / "generation_receipt.json"
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return receipt


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
