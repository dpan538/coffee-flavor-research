"""Zero-fit comparison of R9 policies on sealed R8 actual returns.

The policy adapter never receives T.  This evaluator applies the already-created
outputs first, then separately scores their actual returned positions against the
unchanged archived proxy target.  Raw case rows remain in owner-controlled storage;
only aggregates are written to the public R9 directory.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

from acquire_supervision_r5 import save
from output_alignment_r8 import measure
from output_policy_r9 import (
    NAMED_DESCRIPTOR,
    POLICIES,
    PROFILE_DIRECTION,
    adapt_output,
    digest,
    equivalence,
    role_registry_from_contract,
)

ROOT = Path(__file__).resolve().parents[2]
R8_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r8"
R9_PUBLIC = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
VERSION = "m2-r9.zero-fit-policy-comparison.v1"


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ids(rows: list[dict[str, Any]]) -> list[str]:
    return [row["candidate_id"] for row in rows]


def group_macro(rows: list[dict[str, Any]], field: str, metric: str) -> float | None:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        value = row[field][metric]
        if value is not None:
            groups[row["group_id"]].append(float(value))
    if not groups:
        return None
    return statistics.fmean(statistics.fmean(values) for values in groups.values())


def role_counts(
    candidate_ids: list[str], registry: dict[str, dict[str, Any]]
) -> Counter[str]:
    return Counter(registry[candidate_id]["role"] for candidate_id in candidate_ids)


def supported_dimensions(
    candidate_id: str, registry: dict[str, dict[str, Any]]
) -> set[str]:
    return set(registry[candidate_id].get("support_dimension_ids", []))


def detail(
    source: dict[str, Any],
    policy_id: str,
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    final = source["actual_return"]
    output = adapt_output(final, registry, policy_id)
    main_ids = ids(output["main"])
    secondary_ids = ids(output["secondary"])
    pool = output["comparison_pool_candidate_ids"]
    profile_ids = ids(output["overall_profile"])
    ranking_ids = ids(final["state"]["candidate_scores"])
    if not set(pool + profile_ids) <= set(ranking_ids):
        raise ValueError("POLICY_INVENTED_CANDIDATE")
    main_metric = measure(main_ids, source["full_T"], 5)
    pool_metric = measure(pool, source["full_T"], 8)
    combined_metric = measure(main_ids + secondary_ids, source["full_T"], 8)
    if pool_metric != combined_metric:
        raise ValueError("COMPARISON_POOL_AND_MAIN_SECONDARY_METRIC_MISMATCH")

    confirmed = set(final["state"]["k1"]["confirmed_concepts"])
    eligible_explicit = confirmed & set(ranking_ids)
    returned = set(pool + profile_ids)
    output_named = [
        candidate_id
        for candidate_id in pool
        if registry[candidate_id]["role"] == NAMED_DESCRIPTOR
    ]
    explicit_named = {
        row["candidate_id"]
        for row in final["state"]["candidate_scores"]
        if bool(row.get("explicit"))
        and registry[row["candidate_id"]]["role"] == NAMED_DESCRIPTOR
    }
    profile_in_pool = [
        candidate_id
        for candidate_id in pool
        if registry[candidate_id]["role"] == PROFILE_DIRECTION
    ]
    overlaps = [
        [profile, named]
        for profile in profile_in_pool + profile_ids
        for named in output_named
        if supported_dimensions(profile, registry)
        & supported_dimensions(named, registry)
    ]
    return {
        "record_id": source["record_id"],
        "group_id": source["group_id"],
        "generator": source["policy"],
        "output_policy": policy_id,
        "outer_fold": source.get("outer_fold"),
        "model_sha256": source.get("model_sha256"),
        "model_bundle_id": source.get("bundle_id"),
        "answer_state_hash": (
            final.get("exposure", {}).get("state_hash")
            if isinstance(final.get("exposure"), dict)
            else None
        ),
        "source_return_sha256": output["source_return_sha256"],
        "output_hash": output["output_hash"],
        "main_ids": main_ids,
        "secondary_ids": secondary_ids,
        "profile_ids": profile_ids,
        "pool_ids": pool,
        "main_metric": main_metric,
        "pool_metric": pool_metric,
        "main_roles": dict(role_counts(main_ids, registry)),
        "pool_roles": dict(role_counts(pool, registry)),
        "profile_count": len(profile_ids),
        "named_available": sum(
            registry[candidate_id]["role"] == NAMED_DESCRIPTOR
            for candidate_id in ranking_ids
        ),
        "comparison_executable": output["final_comparison_status"] == "ELIGIBLE",
        "explicit_eligible_count": len(eligible_explicit),
        "explicit_retained_count": len(eligible_explicit & returned),
        "explicit_named_retained_count": len(explicit_named & returned),
        "named_without_explicit_selection_count": len(
            set(output_named) - explicit_named
        ),
        "profile_named_shared_dimension_pairs": len(overlaps),
        "duplicate_ids": len(pool) - len(set(pool)),
    }


def summarize_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for generator in ("C00", "C01"):
        generated = [row for row in cells if row["generator"] == generator]
        result[generator] = {}
        for policy_id in POLICIES:
            rows = [row for row in generated if row["output_policy"] == policy_id]
            explicit_total = sum(row["explicit_eligible_count"] for row in rows)
            result[generator][policy_id] = {
                "records": len(rows),
                "coffee_groups": len({row["group_id"] for row in rows}),
                "actual_main_metrics_coffee_macro": {
                    metric: group_macro(rows, "main_metric", metric)
                    for metric in ("raw_gap", "recall", "ndcg_actual_positions")
                },
                "actual_main_secondary_comparison_pool_metrics_coffee_macro": {
                    metric: group_macro(rows, "pool_metric", metric)
                    for metric in ("raw_gap", "recall", "ndcg_actual_positions")
                },
                "mean_counts_per_return": {
                    "main_named": statistics.fmean(
                        row["main_roles"].get(NAMED_DESCRIPTOR, 0) for row in rows
                    ),
                    "main_profile_direction": statistics.fmean(
                        row["main_roles"].get(PROFILE_DIRECTION, 0) for row in rows
                    ),
                    "secondary_named": statistics.fmean(
                        row["pool_roles"].get(NAMED_DESCRIPTOR, 0)
                        - row["main_roles"].get(NAMED_DESCRIPTOR, 0)
                        for row in rows
                    ),
                    "secondary_profile_direction": statistics.fmean(
                        row["pool_roles"].get(PROFILE_DIRECTION, 0)
                        - row["main_roles"].get(PROFILE_DIRECTION, 0)
                        for row in rows
                    ),
                    "pool_named": statistics.fmean(
                        row["pool_roles"].get(NAMED_DESCRIPTOR, 0) for row in rows
                    ),
                    "pool_profile_direction": statistics.fmean(
                        row["pool_roles"].get(PROFILE_DIRECTION, 0) for row in rows
                    ),
                    "overall_profile": statistics.fmean(
                        row["profile_count"] for row in rows
                    ),
                },
                "explicit_expression_retention": {
                    "eligible_occurrences": explicit_total,
                    "retained_occurrences": sum(
                        row["explicit_retained_count"] for row in rows
                    ),
                    "rate": (
                        sum(row["explicit_retained_count"] for row in rows)
                        / explicit_total
                        if explicit_total
                        else None
                    ),
                },
                "output_insufficiency": {
                    "comparison_not_executable_records": sum(
                        not row["comparison_executable"] for row in rows
                    ),
                    "fewer_than_five_main_records": sum(
                        len(row["main_ids"]) < 5 for row in rows
                    ),
                },
                "mechanism_diagnostics": {
                    "duplicate_records": sum(
                        bool(row["duplicate_ids"]) for row in rows
                    ),
                    "named_without_explicit_selection_occurrences": sum(
                        row["named_without_explicit_selection_count"] for row in rows
                    ),
                    "profile_named_shared_dimension_pair_occurrences": sum(
                        row["profile_named_shared_dimension_pairs"] for row in rows
                    ),
                    "interpretation": "Review flags only. They are neither over-specificity errors nor user-effect findings without real judgments.",
                },
            }
    return result


def difference_summary(
    sources: list[dict[str, Any]], cells: list[dict[str, Any]]
) -> dict[str, Any]:
    by_key = {
        (row["generator"], row["record_id"], row["output_policy"]): row for row in cells
    }
    counts: dict[str, Counter[str]] = {
        generator: Counter() for generator in ("C00", "C01")
    }
    pairwise: dict[str, dict[str, Counter[str]]] = {
        generator: {
            "OUT_MIXED__OUT_SPECIFIC_FIRST": Counter(),
            "OUT_MIXED__OUT_SEPARATED": Counter(),
            "OUT_SPECIFIC_FIRST__OUT_SEPARATED": Counter(),
        }
        for generator in ("C00", "C01")
    }
    for source in sources:
        generator = source["policy"]
        rows = {
            policy_id: by_key[(generator, source["record_id"], policy_id)]
            for policy_id in POLICIES
        }
        mains = {tuple(row["main_ids"]) for row in rows.values()}
        full = {tuple(row["pool_ids"]) for row in rows.values()}
        profiles = {tuple(row["profile_ids"]) for row in rows.values()}
        counts[generator]["cases"] += 1
        counts[generator]["main_identical_all_three"] += len(mains) == 1
        counts[generator]["full_return_identical_all_three"] += len(full) == 1
        counts[generator]["only_profile_different"] += (
            len(mains) == 1 and len(full) == 1 and len(profiles) > 1
        )
        counts[generator]["equivalent_all_fields_all_three"] += (
            len(mains) == 1 and len(full) == 1 and len(profiles) == 1
        )
        shortage = rows["OUT_SEPARATED"]["named_available"] < 8
        specific_separated_content_differs = (
            rows["OUT_SPECIFIC_FIRST"]["main_ids"] != rows["OUT_SEPARATED"]["main_ids"]
            or rows["OUT_SPECIFIC_FIRST"]["pool_ids"]
            != rows["OUT_SEPARATED"]["pool_ids"]
        )
        counts[generator]["named_descriptor_shortage_cases"] += shortage
        counts[generator]["specific_vs_separated_content_differs_only_on_shortage"] += (
            shortage and specific_separated_content_differs
        )
        counts[generator][
            "specific_vs_separated_content_difference_without_shortage"
        ] += (not shortage and specific_separated_content_differs)
        for left, right in (
            ("OUT_MIXED", "OUT_SPECIFIC_FIRST"),
            ("OUT_MIXED", "OUT_SEPARATED"),
            ("OUT_SPECIFIC_FIRST", "OUT_SEPARATED"),
        ):
            left_output = {
                "main": [{"candidate_id": value} for value in rows[left]["main_ids"]],
                "comparison_pool_candidate_ids": rows[left]["pool_ids"],
                "overall_profile": [
                    {"candidate_id": value} for value in rows[left]["profile_ids"]
                ],
            }
            right_output = {
                "main": [{"candidate_id": value} for value in rows[right]["main_ids"]],
                "comparison_pool_candidate_ids": rows[right]["pool_ids"],
                "overall_profile": [
                    {"candidate_id": value} for value in rows[right]["profile_ids"]
                ],
            }
            status = equivalence(left_output, right_output)["status"]
            values = pairwise[generator][left + "__" + right]
            values[status] += 1
            main_equal = rows[left]["main_ids"] == rows[right]["main_ids"]
            full_equal = rows[left]["pool_ids"] == rows[right]["pool_ids"]
            profile_equal = rows[left]["profile_ids"] == rows[right]["profile_ids"]
            values["MAIN_IDENTICAL"] += main_equal
            values["FULL_RETURN_IDENTICAL"] += full_equal
            values["ONLY_PROFILE_DIFFERENT"] += (
                main_equal and full_equal and not profile_equal
            )
    return {
        "case_level_counts": {
            generator: dict(value) for generator, value in counts.items()
        },
        "pairwise_equivalence": {
            generator: {pair: dict(value) for pair, value in pairs.items()}
            for generator, pairs in pairwise.items()
        },
    }


def descriptive_deltas(policy_results: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for generator, policies in policy_results.items():
        mixed = policies["OUT_MIXED"]
        result[generator] = {}
        for policy_id in ("OUT_SPECIFIC_FIRST", "OUT_SEPARATED"):
            result[generator][policy_id] = {}
            for field in (
                "actual_main_metrics_coffee_macro",
                "actual_main_secondary_comparison_pool_metrics_coffee_macro",
            ):
                result[generator][policy_id][field] = {
                    metric: policies[policy_id][field][metric] - mixed[field][metric]
                    for metric in (
                        "raw_gap",
                        "recall",
                        "ndcg_actual_positions",
                    )
                }
    return result


def compare(
    source_path: Path,
    contract_path: Path,
    output_path: Path,
    private_detail_path: Path | None = None,
) -> dict[str, Any]:
    r8_results = read(R8_PUBLIC / "output_alignment_results.json")
    expected = r8_results["private_artifact_hashes"]["actual_returns.private.json"]
    if sha256(source_path) != expected:
        raise ValueError("R8_ACTUAL_RETURNS_HASH_MISMATCH")
    contract = read(contract_path)
    registry = role_registry_from_contract(contract)
    sources = read(source_path)
    if not isinstance(sources, list) or not sources:
        raise ValueError("NONEMPTY_R8_ACTUAL_RETURN_ROWS_REQUIRED")
    expected_model_hashes = set(
        read(R8_PUBLIC / "evaluation_contract.json")["input_hashes"].values()
    )
    if any(source["model_sha256"] not in expected_model_hashes for source in sources):
        raise ValueError("UNFROZEN_OUTER_EXPERT_HASH")
    cells = [
        detail(source, policy_id, registry)
        for source in sources
        for policy_id in POLICIES
    ]
    for source in sources:
        mixed = next(
            row
            for row in cells
            if row["record_id"] == source["record_id"]
            and row["generator"] == source["policy"]
            and row["output_policy"] == "OUT_MIXED"
        )
        if (
            mixed["main_ids"] != source["ids"]["M"]
            or mixed["pool_ids"] != source["ids"]["P"]
        ):
            raise ValueError("OUT_MIXED_NOT_EXACT_R8_RETURN")

    policy_results = summarize_cells(cells)
    private_artifact = None
    if private_detail_path is not None:
        private_artifact = save(
            private_detail_path,
            {
                "version": VERSION,
                "scope": "PRIVATE_ACTUAL_POLICY_OUTPUT_IDS_AND_CASE_METRICS",
                "fit_count": 0,
                "source_actual_returns_sha256": expected,
                "cells": cells,
            },
        )
    report = {
        "version": VERSION,
        "status": "ACTUAL_R8_RETURNS_COMPARED",
        "checkpoint": "FIRST_R9_THREE_POLICY_ACTUAL_OUTPUTS_AND_DIFFERENCES",
        "baseline_sha": contract["baseline_sha"],
        "fit_count": 0,
        "question_reselection_count": 0,
        "default_finalizer_changed": False,
        "primary_research_generator": "C01",
        "historical_generator": "C00",
        "source": {
            "scope": "R8 repeatedly viewed development outer-held states; not independent confirmation or real user evidence",
            "actual_returns_sha256": expected,
            "records": len(sources),
            "coffee_groups": len({source["group_id"] for source in sources}),
            "outer_expert_hashes": sorted(
                {source["model_sha256"] for source in sources}
            ),
        },
        "policy_results": policy_results,
        "descriptive_delta_vs_OUT_MIXED": descriptive_deltas(policy_results),
        "actual_output_differences": difference_summary(sources, cells),
        "guards": {
            "mixed_exact_r8_returns": True,
            "duplicate_policy_output_records": sum(
                bool(row["duplicate_ids"]) for row in cells
            ),
            "invented_candidate_records": 0,
            "comparison_pool_equals_main_plus_secondary": True,
            "policy_adapter_received_T": False,
            "synthetic_cases_in_effect_statistics": 0,
            "model_weights_or_question_parameters_changed": False,
        },
        "real_user_feedback": "NOT_EVALUATED",
        "private_actual_policy_outputs": (
            None
            if private_artifact is None
            else {
                "status": "WRITTEN_TO_OWNER_CONTROLLED_STORAGE",
                "sha256": private_artifact["sha256"],
                "records": len(cells),
            }
        ),
        "interpretation_limits": [
            "Specific-first may improve fine-reference metrics mechanically; that alone is not evidence of better user outcomes.",
            "No parent partial-credit, metric-weight, threshold or confidence rule changed.",
            "Named-without-explicit-selection and shared-dimension counts are mechanism review flags, not demonstrated over-specificity or redundancy.",
            "Rows repeat coffee groups and are summarized at coffee-group level; no ordinary independent-row ANOVA is reported.",
        ],
    }
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r8-actual-returns", type=Path, required=True)
    parser.add_argument(
        "--contract",
        type=Path,
        default=R9_PUBLIC / "output_policy_contract.json",
    )
    parser.add_argument(
        "--output", type=Path, default=R9_PUBLIC / "policy_comparison.json"
    )
    parser.add_argument(
        "--private-detail-output",
        type=Path,
        help="Optional owner-controlled path for the 3 outputs per actual R8 row.",
    )
    args = parser.parse_args()
    report = compare(
        args.r8_actual_returns,
        args.contract,
        args.output,
        args.private_detail_output,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "fit_count": report["fit_count"],
                "records": report["source"]["records"],
                "output_sha256": sha256(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
