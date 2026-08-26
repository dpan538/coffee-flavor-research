#!/usr/bin/env python3
"""Reproduce the reviewed Cotter citrus/acidity relationship evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

SOURCE_SHA256 = "931aff6185381d5079bf93c4727bbbe65ff58ecfb524d2d3b6046eead2009114"
EXPECTED_ROWS = 3186
EXPECTED_BREWS = 27


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def pearson_r(left: list[float], right: list[float]) -> float:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in left)
        * sum((value - right_mean) ** 2 for value in right)
    )
    return numerator / denominator


def average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(enumerate(values), key=lambda item: (item[1], item[0]))
    ranks = [0.0] * len(values)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and ordered[end][1] == ordered[start][1]:
            end += 1
        average_rank = (start + 1 + end) / 2
        for position in range(start, end):
            ranks[ordered[position][0]] = average_rank
        start = end
    return ranks


def regularized_beta(value: float, left: float, right: float) -> float:
    """Numerically stable regularized incomplete beta for the t-test tail."""

    def continued_fraction(a: float, b: float, x: float) -> float:
        max_iterations = 200
        epsilon = 3.0e-14
        floor = 1.0e-300
        qab = a + b
        qap = a + 1.0
        qam = a - 1.0
        c = 1.0
        d = 1.0 - qab * x / qap
        if abs(d) < floor:
            d = floor
        d = 1.0 / d
        result = d
        for iteration in range(1, max_iterations + 1):
            doubled = 2 * iteration
            coefficient = (
                iteration * (b - iteration) * x
                / ((qam + doubled) * (a + doubled))
            )
            d = 1.0 + coefficient * d
            if abs(d) < floor:
                d = floor
            c = 1.0 + coefficient / c
            if abs(c) < floor:
                c = floor
            d = 1.0 / d
            result *= d * c
            coefficient = -(
                (a + iteration)
                * (qab + iteration)
                * x
                / ((a + doubled) * (qap + doubled))
            )
            d = 1.0 + coefficient * d
            if abs(d) < floor:
                d = floor
            c = 1.0 + coefficient / c
            if abs(c) < floor:
                c = floor
            d = 1.0 / d
            delta = d * c
            result *= delta
            if abs(delta - 1.0) < epsilon:
                return result
        raise RuntimeError("incomplete-beta continued fraction did not converge")

    require(0.0 <= value <= 1.0, "regularized beta input outside [0,1]")
    if value in {0.0, 1.0}:
        return value
    factor = math.exp(
        math.lgamma(left + right)
        - math.lgamma(left)
        - math.lgamma(right)
        + left * math.log(value)
        + right * math.log1p(-value)
    )
    if value < (left + 1.0) / (left + right + 2.0):
        return factor * continued_fraction(left, right, value) / left
    return 1.0 - factor * continued_fraction(right, left, 1.0 - value) / right


def two_sided_correlation_p(correlation: float, sample_count: int) -> float:
    degrees_of_freedom = sample_count - 2
    t_squared = (
        correlation * correlation * degrees_of_freedom
        / (1.0 - correlation * correlation)
    )
    beta_value = degrees_of_freedom / (degrees_of_freedom + t_squared)
    return regularized_beta(beta_value, degrees_of_freedom / 2.0, 0.5)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    source_path = args.source_csv.resolve()
    require(sha256_bytes(source_path.read_bytes()) == SOURCE_SHA256, "source hash changed")
    with source_path.open(encoding="utf-8-sig", newline="") as handle:
        source_rows = list(csv.DictReader(handle))
    require(len(source_rows) == EXPECTED_ROWS, "source row count changed")
    require(
        all(row["Citrus"] in {"0", "1"} and row["Acidity"] for row in source_rows),
        "required source fields changed",
    )

    by_brew: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        by_brew[row["Brew"]].append(row)
    require(len(by_brew) == EXPECTED_BREWS, "brew-condition count changed")
    aggregate_rows: list[dict[str, Any]] = []
    for brew, rows in sorted(by_brew.items()):
        acidity = [float(row["Acidity"]) for row in rows]
        citrus = [int(row["Citrus"]) for row in rows]
        aggregate_rows.append(
            {
                "brew_condition": brew,
                "tasting_row_count": len(rows),
                "mean_acidity_jar_1_to_5": f"{sum(acidity) / len(acidity):.12f}",
                "citrus_selection_count": sum(citrus),
                "citrus_selection_prevalence": f"{sum(citrus) / len(citrus):.12f}",
            }
        )

    citrus_prevalence = [float(row["citrus_selection_prevalence"]) for row in aggregate_rows]
    mean_acidity = [float(row["mean_acidity_jar_1_to_5"]) for row in aggregate_rows]
    pearson_r_value = pearson_r(citrus_prevalence, mean_acidity)
    spearman_rho = pearson_r(
        average_ranks(citrus_prevalence), average_ranks(mean_acidity)
    )
    pearson_p = two_sided_correlation_p(pearson_r_value, len(aggregate_rows))
    spearman_p = two_sided_correlation_p(spearman_rho, len(aggregate_rows))
    selected = [float(row["Acidity"]) for row in source_rows if row["Citrus"] == "1"]
    not_selected = [float(row["Acidity"]) for row in source_rows if row["Citrus"] == "0"]
    require(len(selected) == 577 and len(not_selected) == 2609, "Citrus groups changed")
    require(abs(pearson_r_value - 0.7435702459) < 1e-9, "Pearson r changed")
    require(abs(spearman_rho - 0.6737333531) < 1e-9, "Spearman rho changed")
    require(abs(pearson_p - 8.814419733160027e-06) < 1e-12, "Pearson p changed")
    require(abs(spearman_p - 0.00011700493631573394) < 1e-12, "Spearman p changed")

    output_dir = args.output_dir.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    require(output_dir.is_relative_to(repo_root), "output must be inside repository")
    output_dir.mkdir(parents=True, exist_ok=True)
    aggregate_path = output_dir / "cotter_brew_acidity_citrus_aggregates.tsv"
    write_tsv(aggregate_path, aggregate_rows)

    configuration = {
        "aggregation_unit": "27 controlled brew conditions",
        "acidity_semantics": "1-5 JAR adequacy; not pure intensity",
        "citrus_semantics": "binary CATA selection",
        "citrus_not_selected_mean_acidity": sum(not_selected) / len(not_selected),
        "citrus_not_selected_n": len(not_selected),
        "citrus_selected_mean_acidity": sum(selected) / len(selected),
        "citrus_selected_n": len(selected),
        "mean_delta": (sum(selected) / len(selected))
        - (sum(not_selected) / len(not_selected)),
        "pearson_p": pearson_p,
        "pearson_r": pearson_r_value,
        "pooling": "NONE_SOURCE_LOCAL_REANALYSIS",
        "round": "3I",
        "spearman_p": spearman_p,
        "spearman_rho": spearman_rho,
    }
    claim_rows = [
        {
            "evidence_claim_key": "claim.round3i.cotter.acidity-citrus.correlation",
            "target_entity_type": "MEMBERSHIP",
            "target_entity_key": "membership.acidity-character.citrus",
            "source_family_key": "family.legacy-cotter-consumers",
            "source_key": "dryad.cotter-black-coffee.relationship.v4",
            "snapshot_key": "snapshot.dryad-cotter-relationship.v4",
            "evidence_basis": "OBSERVED_CO_SELECTION",
            "evidence_direction": "SUPPORTS",
            "evidence_scope": "SOURCE_LOCAL_BREW_CONDITION_CORRELATION",
            "evidence_locator": "cotter_dataset.csv grouped by Brew; Citrus and Acidity columns",
            "method": "Project reanalysis: brew-level Pearson and Spearman association between Citrus selection prevalence and mean Acidity JAR response",
            "configuration": canonical_json(configuration),
            "support_count": 27,
            "document_count": 3186,
            "source_diversity": 1,
            "review_status": "REVIEWED",
            "limitation": "Correlational repeated-consumer data from one washed medium-roast Honduras coffee; Citrus and Acidity remain distinct constructs and no causality or general law is claimed.",
            "contradictory_evidence_retained": "true",
        }
    ]
    claim_path = output_dir / "relationship_evidence_claims.tsv"
    write_tsv(claim_path, claim_rows)

    source_annotation = {
        "source_key": "dryad.cotter-black-coffee.relationship.v4",
        "source_family_key": "family.legacy-cotter-consumers",
        "title": "Consumer preference data for black coffee",
        "authors_or_owner": "Ristenpart, Cotter, and Guinard research team",
        "year": 2023,
        "doi_or_stable_url": "https://doi.org/10.25338/B8993H",
        "repository": "Dryad",
        "version": "Version 4 files published 2023-01-16",
        "access_date": "2026-08-26",
        "license": "CC0-1.0",
        "row_count_unit": "source_consumer_evaluation_row",
        "raw_row_count": EXPECTED_ROWS,
        "admitted_row_count": EXPECTED_ROWS,
        "excluded_row_count": 0,
        "rights": {
            "raw_text_internal_use": "ALLOW",
            "raw_text_public_redistribution": "ALLOW",
            "derived_expression_internal_use": "ALLOW",
            "derived_expression_public_release": "ALLOW",
            "derived_counts_internal_use": "ALLOW",
            "derived_counts_public_release": "ALLOW",
            "model_research_use": "ALLOW",
        },
        "privacy_decision": "Source identifiers were removed under IRB #1082568; retain pseudonymous Judge codes only and prohibit reidentification.",
        "files": [
            {
                "path": "db/data/round3b/raw/cotter_2020_black_coffee/cotter_dataset.csv",
                "sha256": SOURCE_SHA256,
                "bytes": 542026,
                "rows": 3186,
                "fields": 48,
            },
            {
                "path": "db/data/round3i/relationship/cotter_brew_acidity_citrus_aggregates.tsv",
                "sha256": sha256_bytes(aggregate_path.read_bytes()),
                "rows": 27,
            },
        ],
        "evidence_role": "Correlational support for an acidity-character/citrus relationship",
        "limitations": claim_rows[0]["limitation"],
    }
    source_path_out = output_dir / "source_annotation.json"
    source_path_out.write_text(
        json.dumps(source_annotation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = {
        "batch_key": "round3i.batch4.relationship-depth",
        "targeted_gap": "RANGE_WITH_CROSS_SOURCE_EVIDENCE_COUNT_PREFERRED",
        "named_sources_reviewed": 1,
        "sources_admitted": 1,
        "source_families_added": 0,
        "rows_added": 1,
        "documents_added": 0,
        "unique_expressions_added": 0,
        "zh_hans_expressions_added": 0,
        "coverage_cells_added": 0,
        "relationship_support_added": 1,
        "rights_blocked_count": 0,
        "access_blocked_count": 0,
        "marginal_coverage_gain": "HIGH",
        "readiness_state_after": "ALL_HARD_GATES_AND_FOURTH_RANGE_PREFERRED_GATE_PASS",
        "range_lifecycle_changed": False,
        "promotion_decision": "CORRELATIONAL_SUPPORT_RETAIN_SOURCE_LOCAL_MEMBERSHIP_LIFECYCLE",
        "file_hashes": {
            aggregate_path.name: sha256_bytes(aggregate_path.read_bytes()),
            claim_path.name: sha256_bytes(claim_path.read_bytes()),
            source_path_out.name: sha256_bytes(source_path_out.read_bytes()),
        },
    }
    result_path = output_dir / "batch_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(canonical_json({"status": "RELATIONSHIP_ARTIFACTS_EMITTED", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
