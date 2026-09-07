#!/usr/bin/env python3
"""Frozen-output co-occurrence and separate-view descriptor similarities for R9."""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
import statistics
from typing import Any

from output_policy_r9 import NAMED_DESCRIPTOR, adapt_output


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def optional_jaccard(left: set[str], right: set[str]) -> float | None:
    union = left | right
    return len(left & right) / len(union) if union else None


def mapping_cosine(left: dict[str, int], right: dict[str, int]) -> float | None:
    keys = set(left) | set(right)
    left_norm = sum(left.get(key, 0) ** 2 for key in keys) ** 0.5
    right_norm = sum(right.get(key, 0) ** 2 for key in keys) ** 0.5
    if not left_norm and not right_norm:
        return None
    if not left_norm or not right_norm:
        return 0.0
    return sum(left.get(key, 0) * right.get(key, 0) for key in keys) / (
        left_norm * right_norm
    )


def cooccurrence_network(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    named_ids = sorted(
        candidate_id
        for candidate_id, entry in registry.items()
        if entry["role"] == NAMED_DESCRIPTOR
    )
    record_extents: dict[str, set[str]] = {
        candidate_id: set() for candidate_id in named_ids
    }
    group_extents: dict[str, set[str]] = {
        candidate_id: set() for candidate_id in named_ids
    }
    main_counts = Counter()
    secondary_counts = Counter()
    edge_record_counts = Counter()
    edge_group_ids: dict[tuple[str, str], set[str]] = defaultdict(set)
    for source in sources:
        output = adapt_output(source["actual_return"], registry, "OUT_SEPARATED")
        main_ids = [row["candidate_id"] for row in output["main"]]
        secondary_ids = [row["candidate_id"] for row in output["secondary"]]
        pool = main_ids + secondary_ids
        if len(pool) != len(set(pool)):
            raise ValueError("DUPLICATE_OUTPUT_ID_IN_COOCCURRENCE_CONTEXT")
        main_counts.update(main_ids)
        secondary_counts.update(secondary_ids)
        for candidate_id in pool:
            record_extents[candidate_id].add(source["record_id"])
            group_extents[candidate_id].add(source["group_id"])
        for left, right in combinations(sorted(pool), 2):
            edge_record_counts[(left, right)] += 1
            edge_group_ids[(left, right)].add(source["group_id"])
    nodes = [
        {
            "descriptor_id": candidate_id,
            "record_occurrences": len(record_extents[candidate_id]),
            "group_occurrences": len(group_extents[candidate_id]),
            "main_occurrences": main_counts[candidate_id],
            "secondary_occurrences": secondary_counts[candidate_id],
        }
        for candidate_id in named_ids
    ]
    edges = [
        {
            "left_descriptor_id": left,
            "right_descriptor_id": right,
            "cooccurrence_record_count": count,
            "cooccurrence_group_count": len(edge_group_ids[(left, right)]),
            "record_extent_jaccard": jaccard(
                record_extents[left], record_extents[right]
            ),
            "semantic_status": "FROZEN_OUTPUT_ASSOCIATION_ONLY_NOT_RELATION_EDGE",
        }
        for (left, right), count in sorted(edge_record_counts.items())
    ]
    neighbors: dict[str, set[str]] = {candidate_id: set() for candidate_id in named_ids}
    cooccurrence_counts: dict[str, dict[str, int]] = {
        candidate_id: {} for candidate_id in named_ids
    }
    for edge in edges:
        left = edge["left_descriptor_id"]
        right = edge["right_descriptor_id"]
        neighbors[left].add(right)
        neighbors[right].add(left)
        count = edge["cooccurrence_record_count"]
        cooccurrence_counts[left][right] = count
        cooccurrence_counts[right][left] = count
    return {
        "nodes": nodes,
        "edges": edges,
        "record_extents": {
            candidate_id: sorted(values)
            for candidate_id, values in record_extents.items()
        },
        "cooccurrence_neighbors": {
            candidate_id: sorted(values) for candidate_id, values in neighbors.items()
        },
        "cooccurrence_record_counts_by_neighbor": cooccurrence_counts,
        "summary": {
            "registered_nodes": len(nodes),
            "nodes_observed_in_output": sum(
                node["record_occurrences"] > 0 for node in nodes
            ),
            "nodes_never_observed_in_output": sum(
                not node["record_occurrences"] for node in nodes
            ),
            "observed_edges": len(edges),
            "edge_record_count_distribution": dict(
                sorted(
                    Counter(edge["cooccurrence_record_count"] for edge in edges).items()
                )
            ),
            "edge_filter": "NONE_ALL_POSITIVE_COOCCURRENCES_RETAINED",
            "semantic_relation_edges_created": 0,
        },
    }


def total_variation_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("MATCHED_DISTRIBUTION_LENGTH_REQUIRED")
    return 1.0 - 0.5 * sum(abs(a - b) for a, b in zip(left, right, strict=True))


def descriptor_similarity_views(
    descriptor_features: dict[str, Any],
    network: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    feature_by_id = {row["descriptor_id"]: row for row in descriptor_features["rows"]}
    extent_by_id = {
        candidate_id: set(record_ids)
        for candidate_id, record_ids in network["record_extents"].items()
    }
    neighbor_by_id = {
        candidate_id: set(neighbors)
        for candidate_id, neighbors in network["cooccurrence_neighbors"].items()
    }
    cooccurrence_by_id = network["cooccurrence_record_counts_by_neighbor"]
    candidate_ids = sorted(feature_by_id)
    rows = []
    for left, right in combinations(candidate_ids, 2):
        left_feature = feature_by_id[left]
        right_feature = feature_by_id[right]
        left_total = left_feature["output_occurrences"]
        right_total = right_feature["output_occurrences"]
        evidence_similarity = None
        position_similarity = None
        if left_total and right_total:
            evidence_similarity = total_variation_similarity(
                [
                    left_feature["evidence_class_fractions"][key]
                    for key in (
                        "EXPLICIT_USER_EXPRESSION",
                        "SUPPORTED_DIRECTION_ONLY",
                        "NO_DIRECT_USER_ANSWER_TRACE",
                    )
                ],
                [
                    right_feature["evidence_class_fractions"][key]
                    for key in (
                        "EXPLICIT_USER_EXPRESSION",
                        "SUPPORTED_DIRECTION_ONLY",
                        "NO_DIRECT_USER_ANSWER_TRACE",
                    )
                ],
            )
            position_similarity = total_variation_similarity(
                [
                    left_feature["main_occurrences"] / left_total,
                    left_feature["secondary_occurrences"] / left_total,
                ],
                [
                    right_feature["main_occurrences"] / right_total,
                    right_feature["secondary_occurrences"] / right_total,
                ],
            )
        rows.append(
            {
                "left_descriptor_id": left,
                "right_descriptor_id": right,
                "observation_stratum": (
                    "BOTH_OBSERVED"
                    if left_total and right_total
                    else (
                        "ONE_OBSERVED"
                        if left_total or right_total
                        else "NEITHER_OBSERVED"
                    )
                ),
                "registered_dimension_jaccard": jaccard(
                    set(registry[left]["support_dimension_ids"]),
                    set(registry[right]["support_dimension_ids"]),
                ),
                "evidence_distribution_similarity": evidence_similarity,
                "position_distribution_similarity": position_similarity,
                "output_frequency_ratio_similarity": (
                    min(left_total, right_total) / max(left_total, right_total)
                    if max(left_total, right_total)
                    else None
                ),
                "output_record_extent_jaccard": optional_jaccard(
                    extent_by_id[left], extent_by_id[right]
                ),
                "cooccurrence_neighbor_jaccard": optional_jaccard(
                    neighbor_by_id[left], neighbor_by_id[right]
                ),
                "cooccurrence_count_cosine": mapping_cosine(
                    cooccurrence_by_id[left], cooccurrence_by_id[right]
                ),
                "composite_similarity": None,
                "semantic_status": "SEPARATE_DIAGNOSTIC_VIEWS_NOT_RELATION_EDGE",
            }
        )

    metrics = (
        "registered_dimension_jaccard",
        "evidence_distribution_similarity",
        "position_distribution_similarity",
        "output_frequency_ratio_similarity",
        "output_record_extent_jaccard",
        "cooccurrence_neighbor_jaccard",
        "cooccurrence_count_cosine",
    )

    def metric_summary(values: list[float]) -> dict[str, Any]:
        return {
            "evaluable_pairs": len(values),
            "mean": statistics.fmean(values) if values else None,
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
        }

    summaries = {}
    for metric in metrics:
        values = [row[metric] for row in rows if row[metric] is not None]
        observed_values = [
            row[metric]
            for row in rows
            if row["observation_stratum"] == "BOTH_OBSERVED" and row[metric] is not None
        ]
        summaries[metric] = {
            "all_evaluable_pairs": metric_summary(values),
            "both_observed_pairs": metric_summary(observed_values),
        }
    return {
        "pairs": rows,
        "summary": {
            "descriptor_pairs": len(rows),
            "pair_observation_strata": dict(
                sorted(Counter(row["observation_stratum"] for row in rows).items())
            ),
            "views": summaries,
            "composite_similarity": "NOT_DEFINED_NO_CROSS_VIEW_WEIGHTS",
            "clustering_or_outlier_detection": "NOT_RUN_R9_CLUSTERING_PROHIBITED",
            "semantic_relation_edges_created": 0,
        },
    }
