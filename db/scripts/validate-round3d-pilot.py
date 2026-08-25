#!/usr/bin/env python3
"""Validate Round 3D matrix, schedules, fixtures, privacy, and determinism."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "db" / "data" / "round3d" / "generated"
GENERATOR = ROOT / "db" / "scripts" / "generate-round3d-pilot.py"
DIRECT_IDENTIFIER = re.compile(
    r"(^|[^a-z])(name|email|phone|street|address|postcode|postal_code)([^a-z]|$)|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)
ROASTS = {
    "extremely_light",
    "light",
    "medium_light",
    "medium",
    "medium_dark",
    "dark",
    "extremely_dark",
}
FULL = {"filter_percolation", "immersion", "espresso_pressure"}
ANCHOR = {"hybrid", "diluted_espresso", "cold_extraction", "espresso_milk"}
ANCHOR_ROASTS = {"light", "medium", "dark"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(name: str) -> list[dict[str, str]]:
    with (GENERATED / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"ROUND3D_VALIDATION_ERROR={message}")


def main() -> None:
    tracked = sorted(path for path in GENERATED.iterdir() if path.is_file())
    before = {path.name: sha256(path) for path in tracked}
    subprocess.run(["python3", str(GENERATOR)], cwd=ROOT, check=True, capture_output=True)
    after = {
        path.name: sha256(path)
        for path in sorted(GENERATED.iterdir())
        if path.is_file()
    }
    require(before == after, "deterministic_generator_hash_mismatch")

    lots = read_tsv("coffee_lots.tsv")
    roasts = read_tsv("roast_batches.tsv")
    preparations = read_tsv("preparation_conditions.tsv")
    samples = read_tsv("beverage_samples.tsv")
    sessions = read_tsv("session_slots.tsv")
    presentations = read_tsv("presentation_slots.tsv")
    questions = read_tsv("question_assignment_slots.tsv")
    fixtures = read_tsv("dry_run_cases.tsv")

    require(len(lots) == 2, "coffee_lot_count")
    require(len(roasts) == 14, "roast_batch_count")
    require(
        {row["roast_category_key"].rsplit(".", 1)[-1] for row in roasts}
        == ROASTS,
        "seven_roast_coverage",
    )
    require(len(preparations) == 7, "preparation_family_count")
    require(
        sum(row["coffee_mode_code"] == "milk_coffee" for row in preparations) == 1,
        "separate_milk_condition",
    )
    milk = next(row for row in preparations if row["coffee_mode_code"] == "milk_coffee")
    require(
        milk["paired_black_condition_key"]
        == "pilot.round3d.preparation.espresso_pressure",
        "milk_pairing",
    )

    require(len(samples) == 132, "beverage_sample_count")
    require(len({row["beverage_sample_key"] for row in samples}) == 132, "sample_key_unique")
    cell_counts: Counter[tuple[str, str, str]] = Counter()
    for row in samples:
        roast = row["roast_batch_key"].rsplit(".", 1)[-1]
        family = row["preparation_condition_key"].rsplit(".", 1)[-1]
        lot = row["coffee_lot_key"]
        cell_counts[(lot, roast, family)] += 1
        require(row["record_origin_code"] == "planned_real_sample", "sample_origin")
        require(
            family in FULL or (family in ANCHOR and roast in ANCHOR_ROASTS),
            "impossible_condition",
        )
    require(len(cell_counts) == 66, "condition_cell_count")
    require(set(cell_counts.values()) == {2}, "independent_replicate_count")
    require(
        all(
            any(key[0] == lot and key[2] == family for key in cell_counts)
            for lot in {row["coffee_lot_key"] for row in lots}
            for family in FULL | ANCHOR
        ),
        "same_coffee_cross_condition_coverage",
    )

    require(len(sessions) == 192, "session_slot_count")
    require(len(presentations) == 1512, "presentation_slot_count")
    by_session: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    by_cohort_sample: defaultdict[str, Counter[str]] = defaultdict(Counter)
    session_cohort = {row["session_slot_key"]: row["cohort_code"] for row in sessions}
    for row in presentations:
        by_session[row["session_slot_key"]].append(row)
        by_cohort_sample[session_cohort[row["session_slot_key"]]][
            row["beverage_sample_key"]
        ] += 1
    for session in sessions:
        rows = by_session[session["session_slot_key"]]
        burden = int(session["sample_burden"])
        require(len(rows) == burden, "session_burden")
        require(len({row["beverage_sample_key"] for row in rows}) == burden, "session_duplicate")
        require(
            {int(row["sequence_position"]) for row in rows}
            == set(range(1, burden + 1)),
            "session_sequence",
        )
        require(len({row["blinded_code"] for row in rows}) == burden, "blinded_code_unique")
    require(
        set(by_cohort_sample["reference"].values()) == {6},
        "reference_schedule_balance",
    )
    require(
        set(by_cohort_sample["ordinary_user"].values()) == {5, 6},
        "ordinary_schedule_balance",
    )

    require(len(questions) == 3600, "question_assignment_slot_count")
    by_presentation: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in questions:
        by_presentation[row["presentation_slot_key"]].append(row)
    require(len(by_presentation) == 720, "ordinary_question_presentation_count")
    for rows in by_presentation.values():
        ordered = sorted(rows, key=lambda row: int(row["step_number"]))
        require([int(row["step_number"]) for row in ordered] == [1, 2, 3, 4, 5], "question_steps")
        require(ordered[0]["assignment_status"] == "mandatory", "q1_mandatory")
        require(
            all(row["assignment_status"] == "conditional" for row in ordered[1:]),
            "q2_q5_conditional",
        )

    require(len(fixtures) == 5, "dry_run_fixture_count")
    require({int(row["expected_stop_step"]) for row in fixtures} == {1, 2, 4, 5}, "dry_run_paths")
    require(all(row["fixture_label"] == "DRY_RUN_FIXTURE" for row in fixtures), "fixture_label")
    require(
        any(row["explicit_override"] == "true" for row in fixtures),
        "explicit_user_override_path",
    )

    receipt = json.loads((GENERATED / "generation_receipt.json").read_text())
    analysis = json.loads((GENERATED / "baseline_analysis.json").read_text())
    split = json.loads((GENERATED / "split_inventory.json").read_text())
    require(receipt["counts"]["real_observations"] == 0, "receipt_real_observation_count")
    require(analysis["real_observation_count"] == 0, "analysis_real_observation_count")
    require(
        set(analysis["outputs"].values()) == {"NOT_ESTIMABLE"},
        "baseline_abstention",
    )
    require(
        split["status"] == "NOT_AVAILABLE_MINIMUM_TWO_LOT_FEASIBILITY_PILOT",
        "split_abstention",
    )

    public_paths = [ROOT / "data" / "calibration", GENERATED]
    for root in public_paths:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="ignore")
                require(not DIRECT_IDENTIFIER.search(text), f"pii_scan:{path.relative_to(ROOT)}")

    print("PILOT_MATRIX_VALIDATION_PASS=true")
    print("RANDOMIZATION_VALIDATION_PASS=true")
    print("QUESTION_POLICY_DRY_RUN_PASS=true")
    print("PII_SCAN_PASS=true")
    print("REAL_OBSERVATION_COUNT=0")
    print("BASELINE_ANALYSIS_PASS=true")
    print("ROUND3D_PILOT_VALIDATION_PASS=true")


if __name__ == "__main__":
    main()
