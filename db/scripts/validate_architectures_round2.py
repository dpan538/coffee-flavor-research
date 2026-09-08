#!/usr/bin/env python3
"""Round 2 — build and VALIDATE three post-ANFIS architectures on real data.

ANFIS is out: the measured on-subject supervision is roughly 0.073 groups per
candidate, which extrapolates to a few hundred groups, and the owner is correct
that even 250 is not a safe floor for fitting membership-function and rule
consequent parameters.

The owner asked for at least three alternatives that derive relations from what
already exists, use a topology, decide fuzzily, and are mathematical rather than
fitted — possibly a set of cooperating cluster models. Each must be validated,
not sketched.

WHAT ALREADY EXISTS IN THE PROJECT
  formal_concept_analysis_r9.py     enumerates intent closures, i.e. a concept lattice
  analyze_descriptor_relations_r9.py  co-occurrence network, 134 observed edges
  descriptor_association_analysis_r9.py  1711 descriptor pairs across 7 similarity views
  tripartite_semantic_structure_r9.py  evidence -> dimension -> descriptor, 92 nodes 86 edges
  r9_descriptor_relation_readiness    three graph algorithms specified and GATED on an
                                      approved relation graph: MMR reranking, submodular
                                      selection, weighted evidence propagation

So the substrate is built. What was never done is combining the views
(composite_similarity: NOT_DEFINED_NO_CROSS_VIEW_WEIGHTS) or clustering
(NOT_RUN_R9_CLUSTERING_PROHIBITED). Both were deliberately gated, not missing.

VALIDATION DATA
  Registry topology: 82 concepts, 9 support dimensions, membership edges.
  Observed incidence: rebuilt from the round 2 full-text cache for the papers
  the group-quality audit classified ON_SUBJECT. Real, small, and honest about
  being small.

No fit, no training, no admission, no rule or concept created.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import stratify_extraction_r11 as base  # noqa: E402
from extract_candidates_r11 import norm, numeric, parse_xml  # noqa: E402
from repaired_gates_r12c import repaired_table_admits, sample_label_is_instrumental  # noqa: E402
from measure_conversion_round2 import resolve_repaired  # noqa: E402

R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
CACHE = Path("/private/tmp/coffee-flavor-round2-fulltext-cache")


# ---------------------------------------------------------------- substrate


def load_topology() -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """concept -> dimensions, and dimension -> concepts, from the frozen registry."""
    registry = json.loads((R9 / "output_policy_contract.json").read_text())[
        "concept_role_registry"
    ]
    concept_dims: dict[str, list[str]] = {}
    dim_concepts: dict[str, list[str]] = defaultdict(list)
    for concept, row in registry.items():
        dims = row.get("support_dimension_ids") or []
        concept_dims[concept] = dims
        for d in dims:
            dim_concepts[d].append(concept)
    return concept_dims, dict(dim_concepts)


def build_incidence(direct: dict, rules: dict) -> dict[str, set[str]]:
    """Observed (coffee group -> descriptor concept set) from the round 2 cache."""
    audit_path = R2 / "group_quality_audit.json"
    on_subject = {
        r["doi"] for r in json.loads(audit_path.read_text())["per_candidate"]
        if r["verdict"] == "ON_SUBJECT"
    }
    manifest = json.loads((R2 / "capture_manifest.json").read_text())
    by_doi = {r["doi"]: r for r in manifest["discovery_candidates"] if r.get("doi")}

    incidence: dict[str, set[str]] = {}
    for doi in sorted(on_subject):
        cand = by_doi.get(doi)
        if not cand:
            continue
        url = re.sub(r"/rest/PMC/(PMC\d+)/fullTextXML", r"/rest/\1/fullTextXML",
                     cand["license_source_url"])
        cache = CACHE / f"{hashlib.sha256(url.encode()).hexdigest()}.xml"
        if not cache.exists():
            continue
        try:
            tables, meta = parse_xml(cache.read_bytes())
        except Exception:  # noqa: BLE001
            continue
        for table in tables:
            ok, _ = repaired_table_admits(table, meta.get("plain_text", ""), cand,
                                          direct, rules)
            if not ok:
                continue
            header = table["rows"][0] if table["rows"] else []
            col_concepts: dict[int, list[str]] = {}
            for i, cell in enumerate(header):
                hits = resolve_repaired(cell, direct, rules)
                if hits:
                    col_concepts[i] = hits
            for r_ in table["rows"][1:]:
                if not r_ or not r_[0].strip():
                    continue
                blocked, _ = sample_label_is_instrumental(r_[0], direct, rules)
                if blocked or numeric(r_[0]) is not None:
                    continue
                if base.INVALID_SAMPLE_LABEL.search(norm(r_[0])):
                    continue
                gid = f"{doi}|{norm(r_[0])}"
                present: set[str] = set()
                for i, concepts in col_concepts.items():
                    if i < len(r_) and numeric(r_[i]) is not None:
                        present |= set(concepts)
                # row-oriented tables: descriptor in the label itself
                present |= set(resolve_repaired(r_[0], direct, rules))
                if present:
                    incidence.setdefault(gid, set()).update(present)
    return incidence


# ---------------------------------------------------------------- A1: FCA lattice


def fca(incidence: dict[str, set[str]], max_intents: int = 4000) -> dict[str, Any]:
    """Intent-closure enumeration, the same construction formal_concept_analysis_r9 uses."""
    intents = {frozenset(v) for v in incidence.values() if v}
    closure = set(intents)
    frontier = list(intents)
    while frontier and len(closure) < max_intents:
        a = frontier.pop()
        for b in list(closure):
            inter = a & b
            if inter and inter not in closure:
                closure.add(inter)
                frontier.append(inter)
    # implications A -> B holding over every object whose intent contains A
    support = Counter()
    for v in incidence.values():
        for size in (1, 2):
            for combo in itertools.combinations(sorted(v), size):
                support[frozenset(combo)] += 1
    implications = []
    singles = [k for k in support if len(k) == 1]
    for a in singles:
        for b in singles:
            if a == b:
                continue
            pair = a | b
            if support.get(pair, 0) == 0:
                continue
            conf = support[pair] / support[a]
            if conf >= 0.9 and support[a] >= 2:
                implications.append({
                    "antecedent": sorted(a)[0], "consequent": sorted(b)[0],
                    "support": support[pair], "confidence": round(conf, 3),
                })
    return {
        "objects": len(incidence),
        "distinct_intents": len(intents),
        "closure_size": len(closure),
        "implications_conf_ge_0.9_support_ge_2": len(implications),
        "example_implications": sorted(
            implications, key=lambda r: -r["support"])[:12],
    }


# ---------------------------------------------------------------- A2: spreading activation


def spreading_activation(concept_dims, dim_concepts, seeds: set[str],
                         decay: float = 0.5, hops: int = 2) -> dict[str, float]:
    """Activation from answered concepts through the dimension layer.

    This is the weighted_evidence_propagation the R9 readiness record specifies
    and gates. Decay and hop weight are declared here, not learned.
    """
    act: dict[str, float] = {s: 1.0 for s in seeds}
    frontier = dict(act)
    for hop in range(hops):
        nxt: dict[str, float] = defaultdict(float)
        for node, value in frontier.items():
            for d in concept_dims.get(node, []):
                for peer in dim_concepts.get(d, []):
                    if peer == node:
                        continue
                    nxt[peer] += value * (decay ** (hop + 1)) / max(
                        1, len(dim_concepts.get(d, [])))
        for k, v in nxt.items():
            act[k] = act.get(k, 0.0) + v
        frontier = dict(nxt)
    return act


def validate_a2(concept_dims, dim_concepts, incidence) -> dict[str, Any]:
    """Does activation discriminate? Compare rankings under different seed sets."""
    named = [c for c in concept_dims if c.startswith("sensory.")]
    trials = []
    for dim in list(dim_concepts)[:6]:
        members = [c for c in dim_concepts[dim] if c.startswith("sensory.")]
        if len(members) < 2:
            continue
        seeds = {members[0]}
        act = spreading_activation(concept_dims, dim_concepts, seeds)
        ranked = sorted(act.items(), key=lambda kv: -kv[1])
        top = [c for c, _ in ranked[:5]]
        same_dim = sum(1 for c in top if dim in concept_dims.get(c, []))
        trials.append({
            "seed": members[0], "dimension": dim,
            "activated_nodes": len(act),
            "top5": top,
            "top5_sharing_seed_dimension": same_dim,
        })
    precision = (sum(t["top5_sharing_seed_dimension"] for t in trials)
                 / (5 * len(trials))) if trials else None
    # discrimination: do different seeds give different top sets?
    tops = [tuple(t["top5"]) for t in trials]
    distinct = len(set(tops))
    return {
        "named_concepts": len(named),
        "trials": trials,
        "mean_top5_same_dimension_precision": round(precision, 3) if precision else None,
        "distinct_top5_sets": distinct,
        "trial_count": len(trials),
        "discriminates": distinct == len(trials) if trials else None,
    }


# ---------------------------------------------------------------- A3: peer clusters


def validate_a3(concept_dims, dim_concepts, incidence) -> dict[str, Any]:
    """Each dimension is a peer cluster. Do peers agree or need arbitration?

    A descriptor belonging to several dimensions is a shared member; the
    interesting quantity is how often peers disagree, because that is what an
    arbitration rule would have to resolve.
    """
    multi = {c: d for c, d in concept_dims.items() if len(d) > 1}
    sizes = Counter(len(v) for v in dim_concepts.values())
    # observed co-membership: pairs sharing a dimension
    named = [c for c in concept_dims if c.startswith("sensory.")]
    pairs_sharing = 0
    for a, b in itertools.combinations(named, 2):
        if set(concept_dims[a]) & set(concept_dims[b]):
            pairs_sharing += 1
    # peer disagreement on observed data: for each group, how many distinct
    # dimensions are represented? >1 means peers must be reconciled.
    dim_spread = []
    for gid, concepts in incidence.items():
        dims = set()
        for c in concepts:
            dims |= set(concept_dims.get(c, []))
        dim_spread.append(len(dims))
    return {
        "peer_clusters": len(dim_concepts),
        "cluster_sizes": dict(sorted(sizes.items())),
        "concepts_in_multiple_clusters": len(multi),
        "named_pairs_sharing_a_dimension": pairs_sharing,
        "observed_groups": len(dim_spread),
        "mean_dimensions_per_group": round(sum(dim_spread) / len(dim_spread), 2)
        if dim_spread else None,
        "groups_needing_arbitration_gt1_dimension": sum(1 for x in dim_spread if x > 1),
        "arbitration_share": round(
            sum(1 for x in dim_spread if x > 1) / len(dim_spread), 3) if dim_spread else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()
    started = time.time()

    direct, rules = base.load_direct_registry()
    concept_dims, dim_concepts = load_topology()
    incidence = build_incidence(direct, rules)

    a1 = fca(incidence)
    a2 = validate_a2(concept_dims, dim_concepts, incidence)
    a3 = validate_a3(concept_dims, dim_concepts, incidence)

    report = {
        "contract_version": "round2.architecture-validation.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 1),
        "why_not_anfis": {
            "measured_on_subject_groups_per_candidate": 0.0733,
            "extrapolated_over_capture_ceiling_7000": 510,
            "owner_position": "even 250 is not a safe floor for ANFIS",
            "conclusion": "Parameter fitting is not supported by the measured supervision volume.",
        },
        "substrate_already_in_repo": {
            "formal_concept_analysis_r9.py": "intent closure enumeration, i.e. a concept lattice",
            "descriptor_cooccurrence_network": {"registered_nodes": 59, "observed_edges": 134},
            "descriptor_similarity_views": {"pairs": 1711, "views": 7,
                                            "composite": "NOT_DEFINED_NO_CROSS_VIEW_WEIGHTS",
                                            "clustering": "NOT_RUN_R9_CLUSTERING_PROHIBITED"},
            "tripartite_graph": {"nodes": 92, "edges": 86,
                                 "layers": {"EVIDENCE_CONCEPT": 24, "NAMED_DESCRIPTOR": 59,
                                            "REGISTERED_DIMENSION": 9}},
            "gated_algorithms": ["MMR_reranking", "submodular_selection",
                                 "weighted_evidence_propagation"],
        },
        "validation_data": {
            "topology_concepts": len(concept_dims),
            "dimensions": len(dim_concepts),
            "observed_groups_rebuilt_from_cache": len(incidence),
            "note": "Incidence rebuilt only from papers the group-quality audit classified ON_SUBJECT. Small by design; the off-subject material was excluded rather than counted.",
        },
        "A1_formal_concept_lattice": a1,
        "A2_spreading_activation": a2,
        "A3_peer_dimension_clusters": a3,
        "guards": {"fit_count": 0, "records_admitted": 0, "r6_rules_created": 0,
                   "concepts_created": 0, "relation_edges_created": 0,
                   "training_pause": "REMAINS_IN_EFFECT"},
    }
    (args.output_dir / "architecture_validation.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "observed_groups": len(incidence),
        "A1": {k: v for k, v in a1.items() if k != "example_implications"},
        "A2": {k: v for k, v in a2.items() if k != "trials"},
        "A3": a3,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
