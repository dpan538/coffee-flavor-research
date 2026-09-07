#!/usr/bin/env python3
"""Typed evidence-dimension-descriptor incidence graph for frozen R9 analysis."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
import math
from typing import Any

from output_policy_r9 import NAMED_DESCRIPTOR
from trajectory_analysis_r9 import ordered_answers


def betweenness_centrality(adjacency: dict[str, set[str]]) -> dict[str, float]:
    """Exact unweighted Brandes centrality for one undirected graph."""

    nodes = sorted(adjacency)
    centrality = dict.fromkeys(nodes, 0.0)
    for source in nodes:
        stack = []
        predecessors = {node: [] for node in nodes}
        path_count = dict.fromkeys(nodes, 0.0)
        path_count[source] = 1.0
        distance = dict.fromkeys(nodes, -1)
        distance[source] = 0
        queue = deque([source])
        while queue:
            vertex = queue.popleft()
            stack.append(vertex)
            for neighbor in sorted(adjacency[vertex]):
                if distance[neighbor] < 0:
                    queue.append(neighbor)
                    distance[neighbor] = distance[vertex] + 1
                if distance[neighbor] == distance[vertex] + 1:
                    path_count[neighbor] += path_count[vertex]
                    predecessors[neighbor].append(vertex)
        dependency = dict.fromkeys(nodes, 0.0)
        while stack:
            vertex = stack.pop()
            if path_count[vertex]:
                coefficient = (1.0 + dependency[vertex]) / path_count[vertex]
                for predecessor in predecessors[vertex]:
                    dependency[predecessor] += path_count[predecessor] * coefficient
            if vertex != source:
                centrality[vertex] += dependency[vertex]
    denominator = math.comb(len(nodes) - 1, 2) if len(nodes) > 2 else 0
    return {
        node: (value / 2.0 / denominator if denominator else 0.0)
        for node, value in centrality.items()
    }


def build_tripartite_graph(
    sources: list[dict[str, Any]], registry: dict[str, Any]
) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edge_counts: Counter[tuple[str, str]] = Counter()
    edge_groups: dict[tuple[str, str], set[str]] = defaultdict(set)

    def add_node(node_id: str, layer: str, concept_id: str) -> None:
        row = {"node_id": node_id, "layer": layer, "concept_id": concept_id}
        if node_id in nodes and nodes[node_id] != row:
            raise ValueError("TRIPARTITE_NODE_COLLISION:" + node_id)
        nodes[node_id] = row

    for source in sources:
        for _, answer in ordered_answers(source["actual_return"]):
            for candidate_id in answer.get("selected_option_ids", []):
                if candidate_id not in registry:
                    raise ValueError("UNREGISTERED_EVIDENCE_CONCEPT:" + candidate_id)
                evidence_node = "EVIDENCE::" + candidate_id
                add_node(evidence_node, "EVIDENCE_CONCEPT", candidate_id)
                for dimension_id in registry[candidate_id]["support_dimension_ids"]:
                    dimension_node = "DIMENSION::" + dimension_id
                    add_node(dimension_node, "REGISTERED_DIMENSION", dimension_id)
                    edge = tuple(sorted((evidence_node, dimension_node)))
                    edge_counts[edge] += 1
                    edge_groups[edge].add(source["group_id"])

    for candidate_id, entry in sorted(registry.items()):
        if entry["role"] != NAMED_DESCRIPTOR:
            continue
        descriptor_node = "DESCRIPTOR::" + candidate_id
        add_node(descriptor_node, "NAMED_DESCRIPTOR", candidate_id)
        for dimension_id in entry["support_dimension_ids"]:
            dimension_node = "DIMENSION::" + dimension_id
            add_node(dimension_node, "REGISTERED_DIMENSION", dimension_id)
            edge = tuple(sorted((descriptor_node, dimension_node)))
            edge_counts.setdefault(edge, 0)

    adjacency: dict[str, set[str]] = {node_id: set() for node_id in nodes}
    for left, right in edge_counts:
        adjacency[left].add(right)
        adjacency[right].add(left)
    centrality = betweenness_centrality(adjacency)
    observed_evidence_occurrences = {
        node_id: sum(
            edge_counts[tuple(sorted((node_id, neighbor)))]
            for neighbor in adjacency[node_id]
            if node_id.startswith("EVIDENCE::") or neighbor.startswith("EVIDENCE::")
        )
        for node_id in nodes
    }
    registered_membership_degree = {
        node_id: sum(
            not (node_id.startswith("EVIDENCE::") or neighbor.startswith("EVIDENCE::"))
            for neighbor in adjacency[node_id]
        )
        for node_id in nodes
    }
    node_rows = [
        {
            **nodes[node_id],
            "degree": len(adjacency[node_id]),
            "observed_evidence_occurrence_count": observed_evidence_occurrences[
                node_id
            ],
            "registered_membership_degree": registered_membership_degree[node_id],
            "betweenness_centrality": centrality[node_id],
        }
        for node_id in sorted(nodes)
    ]
    edge_rows = []
    for left, right in sorted(edge_counts):
        evidence_edge = left.startswith("EVIDENCE::") or right.startswith("EVIDENCE::")
        edge_rows.append(
            {
                "left_node_id": left,
                "right_node_id": right,
                "edge_type": (
                    "OBSERVED_EVIDENCE_TO_REGISTERED_DIMENSION"
                    if evidence_edge
                    else "REGISTERED_DIMENSION_TO_DESCRIPTOR_MEMBERSHIP"
                ),
                "record_occurrence_count": (
                    edge_counts[(left, right)] if evidence_edge else None
                ),
                "group_occurrence_count": (
                    len(edge_groups[(left, right)]) if evidence_edge else None
                ),
                "registry_membership": not evidence_edge,
                "entailment": False,
            }
        )
    top_degree = sorted(
        node_rows,
        key=lambda row: (-row["degree"], row["node_id"]),
    )[:10]
    top_betweenness = sorted(
        node_rows,
        key=lambda row: (-row["betweenness_centrality"], row["node_id"]),
    )[:10]
    top_dimension_evidence_occurrences = sorted(
        (row for row in node_rows if row["layer"] == "REGISTERED_DIMENSION"),
        key=lambda row: (-row["observed_evidence_occurrence_count"], row["node_id"]),
    )
    top_evidence_concept_occurrences = sorted(
        (row for row in node_rows if row["layer"] == "EVIDENCE_CONCEPT"),
        key=lambda row: (-row["observed_evidence_occurrence_count"], row["node_id"]),
    )[:10]
    return {
        "nodes": node_rows,
        "edges": edge_rows,
        "summary": {
            "node_count": len(node_rows),
            "edge_count": len(edge_rows),
            "layer_counts": dict(
                sorted(Counter(row["layer"] for row in node_rows).items())
            ),
            "edge_type_counts": dict(
                sorted(Counter(row["edge_type"] for row in edge_rows).items())
            ),
            "top_degree_nodes": top_degree,
            "top_betweenness_nodes": top_betweenness,
            "dimensions_by_observed_evidence_occurrence": (
                top_dimension_evidence_occurrences
            ),
            "top_evidence_concepts_by_observed_occurrence": (
                top_evidence_concept_occurrences
            ),
            "semantic_relation_edges_created": 0,
            "cross_edge_type_weighted_degree": "NOT_DEFINED",
            "interpretation": (
                "Centrality reflects the topology induced by registered dimension membership "
                "and observed selections. A two-hop evidence-dimension-descriptor path is "
                "compatibility reachability, not descriptor support or semantic entailment."
            ),
        },
    }
