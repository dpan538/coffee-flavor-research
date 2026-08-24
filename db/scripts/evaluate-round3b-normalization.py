#!/usr/bin/env python3
"""Evaluate the frozen Round 3B C0/C1 lexical contract exactly once."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPOSITORY_ROOT / "db" / "data" / "round3b"
CASE_PATH = DATA_ROOT / "benchmark" / "context_cases_frozen.tsv"
RECORD_PATH = DATA_ROOT / "derived" / "context_records.tsv"
RESULT_PATH = DATA_ROOT / "benchmark" / "normalization_results.tsv"
RULE_PATH = DATA_ROOT / "derived" / "lexical_rules.tsv"
METRIC_PATH = DATA_ROOT / "derived" / "normalization_metrics.json"
STATISTICS_PATH = DATA_ROOT / "derived" / "context_statistics.json"


def normalize(value: str) -> str:
    value = value.strip().casefold().replace("—", "-").replace("–", "-")
    value = value.replace("‑", "-")
    return " ".join(value.split())


def prep_rule(
    family: str, leaf: str = "", grade: str = "reviewed_lexical"
) -> dict[str, str]:
    return {
        "outcome_status": "known",
        "family_key": family,
        "leaf_key": leaf,
        "roast_code": "",
        "mapping_grade": grade,
    }


def roast_rule(code: str, grade: str) -> dict[str, str]:
    return {
        "outcome_status": "known",
        "family_key": "",
        "leaf_key": "",
        "roast_code": code,
        "mapping_grade": grade,
    }


def unresolved_rule(grade: str) -> dict[str, str]:
    return {
        "outcome_status": "reported_unresolved",
        "family_key": "",
        "leaf_key": "",
        "roast_code": "",
        "mapping_grade": grade,
    }


def add_many(
    rules: dict[tuple[str, str, str], dict[str, str]],
    domain: str,
    language: str,
    expressions: list[str],
    rule: dict[str, str],
) -> None:
    for expression in expressions:
        key = (domain, language, normalize(expression))
        if key in rules:
            raise SystemExit(f"duplicate lexical rule: {key}")
        rules[key] = rule


def build_rules() -> dict[tuple[str, str, str], dict[str, str]]:
    rules: dict[tuple[str, str, str], dict[str, str]] = {}
    add_many(
        rules,
        "preparation",
        "en",
        ["V60", "Hario V60", "pour over"],
        prep_rule(
            "preparation.family.filter_percolation",
            "preparation.method.pour_over_cone",
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["hand drip", "manual filter"],
        prep_rule(
            "preparation.family.filter_percolation",
            "preparation.method.manual_filter",
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["Chemex"],
        prep_rule(
            "preparation.family.filter_percolation", "preparation.method.chemex"
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["batch brew"],
        prep_rule(
            "preparation.family.filter_percolation",
            "preparation.method.batch_filter",
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["drip coffee", "filter coffee"],
        prep_rule("preparation.family.filter_percolation"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["French press", "cafetiere", "press pot"],
        prep_rule("preparation.family.immersion", "preparation.method.french_press"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["immersion"],
        prep_rule("preparation.family.immersion"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["Clever Dripper"],
        prep_rule("preparation.family.hybrid"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["AeroPress"],
        prep_rule("preparation.family.hybrid", "preparation.method.aeropress"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["siphon", "vacuum pot"],
        prep_rule("preparation.family.hybrid", "preparation.method.siphon"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["espresso", "short black"],
        prep_rule(
            "preparation.family.espresso_pressure",
            "preparation.method.espresso_standard",
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["ristretto"],
        prep_rule(
            "preparation.family.espresso_pressure", "preparation.beverage.ristretto"
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["lungo"],
        prep_rule("preparation.family.espresso_pressure", "preparation.beverage.lungo"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["Americano"],
        prep_rule(
            "preparation.family.diluted_espresso", "preparation.beverage.americano"
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["long black"],
        prep_rule(
            "preparation.family.diluted_espresso", "preparation.beverage.long_black"
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["moka pot"],
        prep_rule("preparation.family.stovetop_boiled", "preparation.method.moka"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["stovetop coffee"],
        prep_rule("preparation.family.stovetop_boiled"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["Turkish coffee", "cezve"],
        prep_rule("preparation.family.stovetop_boiled", "preparation.method.cezve"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["cold brew"],
        prep_rule(
            "preparation.family.cold_extraction",
            "preparation.method.cold_brew_immersion",
        ),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["cold drip"],
        prep_rule("preparation.family.cold_extraction", "preparation.method.cold_drip"),
    )
    add_many(
        rules,
        "preparation",
        "en",
        ["nitro cold brew"],
        prep_rule(
            "preparation.family.cold_extraction",
            "preparation.beverage.nitro_cold_brew",
        ),
    )
    milk_leaves = {
        "flat white": "flat_white",
        "latte": "latte",
        "cappuccino": "cappuccino",
        "cortado": "cortado",
        "piccolo": "piccolo",
        "macchiato": "macchiato",
        "iced latte": "latte",
    }
    for expression, suffix in milk_leaves.items():
        add_many(
            rules,
            "preparation",
            "en",
            [expression],
            prep_rule(
                "preparation.family.espresso_milk", f"preparation.beverage.{suffix}"
            ),
        )
    add_many(
        rules,
        "preparation",
        "en",
        ["Dutch coffee", "iced coffee", "mocha"],
        unresolved_rule("reviewed_abstention"),
    )

    zh_prep = {
        "手冲": ("preparation.family.filter_percolation", "preparation.method.manual_filter"),
        "V60咖啡": ("preparation.family.filter_percolation", "preparation.method.pour_over_cone"),
        "滴滤咖啡": ("preparation.family.filter_percolation", ""),
        "法压壶": ("preparation.family.immersion", "preparation.method.french_press"),
        "爱乐压": ("preparation.family.hybrid", "preparation.method.aeropress"),
        "虹吸壶": ("preparation.family.hybrid", "preparation.method.siphon"),
        "意式浓缩": ("preparation.family.espresso_pressure", "preparation.method.espresso_standard"),
        "美式咖啡": ("preparation.family.diluted_espresso", "preparation.beverage.americano"),
        "澳白": ("preparation.family.espresso_milk", "preparation.beverage.flat_white"),
        "拿铁": ("preparation.family.espresso_milk", "preparation.beverage.latte"),
        "卡布奇诺": ("preparation.family.espresso_milk", "preparation.beverage.cappuccino"),
        "摩卡壶": ("preparation.family.stovetop_boiled", "preparation.method.moka"),
        "土耳其咖啡": ("preparation.family.stovetop_boiled", "preparation.method.cezve"),
        "冷萃": ("preparation.family.cold_extraction", "preparation.method.cold_brew_immersion"),
        "冰滴": ("preparation.family.cold_extraction", "preparation.method.cold_drip"),
    }
    for expression, (family, leaf) in zh_prep.items():
        add_many(rules, "preparation", "zh-Hans", [expression], prep_rule(family, leaf))
    add_many(
        rules,
        "preparation",
        "zh-Hans",
        ["冰咖啡"],
        unresolved_rule("reviewed_abstention"),
    )

    en_roast = {
        "extremely light": ("extremely_light", "exact_project_label"),
        "light": ("light", "exact_project_label"),
        "medium-light": ("medium_light", "exact_project_label"),
        "medium": ("medium", "exact_project_label"),
        "medium-dark": ("medium_dark", "exact_project_label"),
        "dark": ("dark", "exact_project_label"),
        "extremely dark": ("extremely_dark", "exact_project_label"),
        "extremely-light roast": ("extremely_light", "near_exact"),
        "light roast": ("light", "near_exact"),
        "medium light": ("medium_light", "near_exact"),
        "medium-light roast": ("medium_light", "near_exact"),
        "medium roast": ("medium", "near_exact"),
        "medium dark": ("medium_dark", "near_exact"),
        "medium-dark roast": ("medium_dark", "near_exact"),
        "dark roast": ("dark", "near_exact"),
        "extremely-dark roast": ("extremely_dark", "near_exact"),
        "light-medium": ("medium_light", "supported_ordinal"),
    }
    for expression, (code, grade) in en_roast.items():
        add_many(rules, "roast", "en", [expression], roast_rule(code, grade))
    add_many(
        rules,
        "roast",
        "en",
        [
            "filter roast", "espresso roast", "omniroast", "Nordic roast",
            "City roast", "City+", "Full City", "Vienna roast", "French roast",
            "Italian roast", "very light", "very dark",
        ],
        unresolved_rule("reviewed_abstention"),
    )

    zh_roast_groups = {
        "extremely_light": ["极浅烘", "极浅度烘焙"],
        "light": ["浅烘", "浅度烘焙"],
        "medium_light": ["浅中烘", "浅中烘焙", "中浅烘", "中浅度烘焙"],
        "medium": ["中烘", "中度烘焙"],
        "medium_dark": ["中深烘", "中深度烘焙"],
        "dark": ["深烘", "深度烘焙"],
        "extremely_dark": ["极深烘", "极深度烘焙"],
    }
    for code, expressions in zh_roast_groups.items():
        add_many(
            rules,
            "roast",
            "zh-Hans",
            expressions,
            roast_rule(code, "bilingual_reviewed"),
        )
    add_many(
        rules,
        "roast",
        "zh-Hans",
        ["重烘"],
        unresolved_rule("reviewed_abstention"),
    )
    return rules


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def evaluate(rules: dict[tuple[str, str, str], dict[str, str]]) -> list[dict[str, str]]:
    with CASE_PATH.open("r", encoding="utf-8", newline="") as source:
        cases = list(csv.DictReader(source, delimiter="\t"))
    results: list[dict[str, str]] = []
    for case in cases:
        key = (case["domain"], case["language_tag"], normalize(case["raw_expression"]))
        prediction = rules.get(key, unresolved_rule("no_reviewed_rule"))
        expected_status = case["expected_status"]
        if case["domain"] == "preparation":
            if expected_status == "reported_unresolved" and prediction["outcome_status"] == "reported_unresolved":
                grade = "U"
                gross_error = False
            elif prediction["family_key"] == case["expected_family_key"] and prediction["family_key"]:
                if case["expected_leaf_key"] and prediction["leaf_key"] == case["expected_leaf_key"]:
                    grade = "3"
                else:
                    grade = "2"
                gross_error = False
            elif prediction["family_key"]:
                grade = "0"
                gross_error = True
            else:
                grade = "U"
                gross_error = False
            ordinal_error = ""
        else:
            if expected_status == "reported_unresolved" and prediction["outcome_status"] == "reported_unresolved":
                grade = "U"
                gross_error = False
                ordinal_error = ""
            elif prediction["roast_code"] and case["expected_roast_code"]:
                positions = {
                    "extremely_light": 1, "light": 2, "medium_light": 3,
                    "medium": 4, "medium_dark": 5, "dark": 6,
                    "extremely_dark": 7,
                }
                error = abs(
                    positions[prediction["roast_code"]]
                    - positions[case["expected_roast_code"]]
                )
                ordinal_error = str(error)
                grade = "exact" if error == 0 else "adjacent" if error == 1 else "incorrect"
                gross_error = error > 1
            else:
                grade = "U"
                gross_error = False
                ordinal_error = ""
        results.append(
            {
                "case_key": case["case_key"],
                "domain": case["domain"],
                "split": case["split"],
                "expected_status": expected_status,
                "predicted_status": prediction["outcome_status"],
                "expected_family_key": case["expected_family_key"],
                "predicted_family_key": prediction["family_key"],
                "expected_leaf_key": case["expected_leaf_key"],
                "predicted_leaf_key": prediction["leaf_key"],
                "expected_roast_code": case["expected_roast_code"],
                "predicted_roast_code": prediction["roast_code"],
                "evaluation_grade": grade,
                "ordinal_error": ordinal_error,
                "gross_error": "true" if gross_error else "false",
                "mapping_grade": prediction["mapping_grade"],
            }
        )
    return results


def metrics(results: list[dict[str, str]]) -> dict[str, Any]:
    held = [row for row in results if row["split"] == "held_out"]
    c0 = [row for row in held if row["domain"] == "preparation"]
    c1 = [row for row in held if row["domain"] == "roast"]
    c0_resolved = [row for row in c0 if row["predicted_family_key"]]
    c0_leaf = [row for row in c0 if row["predicted_leaf_key"]]
    c0_ambiguous = [row for row in c0 if row["evaluation_grade"] == "1"]
    c0_gross = [row for row in c0 if row["gross_error"] == "true"]
    c1_expected_known = [row for row in c1 if row["expected_status"] == "known"]
    c1_mapped = [row for row in c1 if row["predicted_roast_code"]]
    c1_exact = [row for row in c1_expected_known if row["ordinal_error"] == "0"]
    c1_adjacent = [
        row for row in c1_expected_known if row["ordinal_error"] in {"0", "1"}
    ]
    c1_gross = [row for row in c1_expected_known if row["gross_error"] == "true"]

    def ratio(numerator: int, denominator: int) -> float:
        return round(numerator / denominator, 4) if denominator else 0.0

    return {
        "metric_semantics": "label-normalization quality; not coffee flavor accuracy",
        "held_out_size": len(held),
        "c0": {
            "held_out_size": len(c0),
            "recall_at_1_leaf": ratio(
                sum(
                    row["expected_leaf_key"] != ""
                    and row["predicted_leaf_key"] == row["expected_leaf_key"]
                    for row in c0
                ),
                sum(row["expected_leaf_key"] != "" for row in c0),
            ),
            "recall_at_1_family": ratio(
                sum(
                    row["expected_family_key"] != ""
                    and row["predicted_family_key"] == row["expected_family_key"]
                    for row in c0
                ),
                sum(row["expected_family_key"] != "" for row in c0),
            ),
            "family_coverage": ratio(len(c0_resolved), len(c0)),
            "leaf_coverage": ratio(len(c0_leaf), len(c0)),
            "unresolved_rate": ratio(len(c0) - len(c0_resolved), len(c0)),
            "ambiguous_rate": ratio(len(c0_ambiguous), len(c0)),
            "gross_family_error_rate": ratio(len(c0_gross), len(c0)),
        },
        "c1": {
            "held_out_size": len(c1),
            "known_expected_size": len(c1_expected_known),
            "exact_category_agreement": ratio(len(c1_exact), len(c1_expected_known)),
            "adjacent_category_agreement": ratio(
                len(c1_adjacent), len(c1_expected_known)
            ),
            "gross_category_error_rate": ratio(len(c1_gross), len(c1_expected_known)),
            "coverage": ratio(len(c1_mapped), len(c1)),
            "unresolved_rate": ratio(len(c1) - len(c1_mapped), len(c1)),
            "mapping_precision": ratio(
                sum(
                    row["predicted_roast_code"] == row["expected_roast_code"]
                    for row in c1_mapped
                ),
                len(c1_mapped),
            ),
            "ordinal_error_summary": {
                "mean_absolute_category_error_on_mapped_known": round(
                    sum(int(row["ordinal_error"]) for row in c1_expected_known if row["ordinal_error"])
                    / max(1, sum(bool(row["ordinal_error"]) for row in c1_expected_known)),
                    4,
                ),
                "equal_physical_distance_assumed": False,
            },
        },
        "sufficiency": {
            "c0_normalization_data_sufficient": False,
            "c1_normalization_data_sufficient": False,
            "reason": "The held-out labels are project-authored contract cases, not an independent ordinary-user sample.",
        },
    }


def context_statistics() -> dict[str, Any]:
    with RECORD_PATH.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    source_counts = Counter(row["source_key"] for row in rows)
    prep_counts = Counter(
        row["normalized_preparation_family_key"] or row["preparation_status_code"]
        for row in rows
    )
    roast_counts = Counter(
        row["normalized_roast_code"] or row["roast_status_code"] for row in rows
    )
    mode_counts = Counter(row["coffee_mode_code"] for row in rows)
    sensory = [row for row in rows if row["has_sensory_outcome"] == "true"]
    sensory_prep = {
        row["normalized_preparation_family_key"] for row in sensory
        if row["normalized_preparation_family_key"]
    }
    sensory_roast = {
        row["normalized_roast_code"] for row in sensory if row["normalized_roast_code"]
    }
    sensory_cells = {
        (row["normalized_preparation_family_key"], row["normalized_roast_code"])
        for row in sensory
        if row["normalized_preparation_family_key"] and row["normalized_roast_code"]
    }
    milk_sensory = [row for row in sensory if row["coffee_mode_code"] == "milk_coffee"]
    return {
        "context_record_count": len(rows),
        "source_distribution": dict(sorted(source_counts.items())),
        "source_concentration_max_share": round(max(source_counts.values()) / len(rows), 4),
        "preparation_distribution": dict(sorted(prep_counts.items())),
        "roast_distribution": dict(sorted(roast_counts.items())),
        "black_milk_distribution": dict(sorted(mode_counts.items())),
        "country_distribution": {
            "united_states_sensory_sessions_honduras_coffee": source_counts[
                "dryad_cotter_black_coffee"
            ],
            "heterogeneous_meta_analysis_not_row_normalized": source_counts[
                "dryad_yeager_acids_meta_analysis"
            ],
        },
        "sensory_context_inventory": {
            "sensory_row_count": len(sensory),
            "preparation_family_count": len(sensory_prep),
            "roast_category_count": len(sensory_roast),
            "preparation_roast_cell_count": len(sensory_cells),
            "milk_sensory_row_count": len(milk_sensory),
        },
        "sufficiency": {
            "preparation_signal_data_sufficient": False,
            "roast_signal_data_sufficient": False,
            "preparation_roast_interaction_data_sufficient": False,
            "milk_mode_data_sufficient": False,
        },
        "results": {
            "preparation_signal": "NOT_ESTIMABLE: sensory rows contain one preparation family.",
            "roast_signal": "NOT_ESTIMABLE: sensory rows contain one roast category.",
            "preparation_roast_interaction": "NOT_ESTIMABLE: sensory rows occupy one preparation-by-roast cell.",
            "milk_mode": "EVIDENCE_INSUFFICIENT: no imported milk-coffee sensory outcomes.",
        },
        "method_audit": {
            "research_question": "Do preparation, roast, or their interaction add information about sensory outcomes?",
            "input_data": "Frozen Round 3B snapshot only.",
            "assumptions": "At least two populated levels per main effect and replicated crossed cells for interaction.",
            "output": "Sufficiency and identifiability gate; no coefficient estimation.",
            "limitations": "The Cotter sensory dataset fixes preparation and roast; the Yeager dataset varies context but reports chemistry, not sensory outcomes.",
        },
    }


def main() -> None:
    rules = build_rules()
    rule_rows: list[dict[str, str]] = []
    for (domain, language, expression), rule in sorted(rules.items()):
        rule_key_material = f"{domain}|{language}|{expression}"
        rule_rows.append(
            {
                "rule_key": "context.rule." + hashlib.sha256(rule_key_material.encode()).hexdigest()[:20],
                "domain": domain,
                "language_tag": language,
                "normalized_expression": expression,
                **rule,
                "review_decision": "approved" if rule["outcome_status"] == "known" else "abstained",
                "evidence_locator": "db/scripts/evaluate-round3b-normalization.py",
            }
        )
    write_tsv(
        RULE_PATH,
        rule_rows,
        [
            "rule_key", "domain", "language_tag", "normalized_expression",
            "outcome_status", "family_key", "leaf_key", "roast_code",
            "mapping_grade", "review_decision", "evidence_locator",
        ],
    )
    results = evaluate(rules)
    write_tsv(RESULT_PATH, results, list(results[0]))
    computed_metrics = metrics(results)
    METRIC_PATH.write_text(
        json.dumps(computed_metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    statistics = context_statistics()
    STATISTICS_PATH.write_text(
        json.dumps(statistics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("HELD_OUT_CONTEXT_EVALUATION_RUN=true")
    print(json.dumps(computed_metrics, ensure_ascii=False, sort_keys=True))
    print(json.dumps(statistics["sufficiency"], sort_keys=True))


if __name__ == "__main__":
    main()
