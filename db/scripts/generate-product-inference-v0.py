#!/usr/bin/env python3
"""Generate the public-safe deterministic Round 3N inference checkpoint.

This is an offline policy simulator. It does not train a model, estimate
probabilities, or claim that its hand-declared decision weights are optimal.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "db" / "data" / "product-inference-v0"
CURRENT = ROOT / "db" / "data" / "current"
ROUND3H = ROOT / "db" / "data" / "round3h"

POLICY_VERSION = "product-inference-policy-v0.1.0"
CONTRACT_VERSION = "coffee-flavor-product-task-v0"
QUESTION_BANK_VERSION = "product-question-bank-v0.1.0"
GENERATED_AT = "2026-09-01T00:00:00Z"

PREPARATIONS = [
    ("preparation.family.filter_percolation", "Filter coffee", "滤泡咖啡"),
    ("preparation.family.immersion", "Immersion brew", "浸泡式咖啡"),
    ("preparation.family.hybrid", "AeroPress / hybrid", "爱乐压 / 混合式"),
    ("preparation.family.espresso_pressure", "Espresso", "意式浓缩"),
    ("preparation.family.diluted_espresso", "Espresso + water", "浓缩加水"),
    ("preparation.family.stovetop_boiled", "Stovetop / boiled", "炉煮 / 煮制"),
    ("preparation.family.cold_extraction", "Cold brew", "冷萃咖啡"),
    ("preparation.family.espresso_milk", "Milk coffee", "奶咖"),
]
ROASTS = [
    ("extremely_light", "Extremely light", 1),
    ("light", "Light", 2),
    ("medium_light", "Medium-light", 3),
    ("medium", "Medium", 4),
    ("medium_dark", "Medium-dark", 5),
    ("dark", "Dark", 6),
    ("extremely_dark", "Extremely dark", 7),
]

# These labels are copied from the repository's bilingual public pilot data.
# Only canonical concepts with an exact governed mapping are admitted here.
CANDIDATE_DEFINITIONS = [
    ("sensory.jasmine", "Jasmine", "茉莉", "floral", "white_floral"),
    ("sensory.rose", "Rose", "玫瑰", "floral", "rose_floral"),
    ("sensory.orange_blossom", "Orange Blossom", "橙花", "floral", "citrus_blossom"),
    ("sensory.lemon", "Lemon", "柠檬", "fruit", "citrus"),
    ("sensory.orange", "Orange", "橙", "fruit", "citrus"),
    ("sensory.blueberry", "Blueberry", "蓝莓", "fruit", "berry"),
    ("sensory.honey", "Honey", "蜂蜜", "sweet", "honey"),
    ("sensory.caramel", "Caramel", "焦糖", "sweet", "browned_sweet"),
    ("sensory.brown_sugar", "Brown Sugar", "红糖", "sweet", "browned_sweet"),
    ("sensory.almond", "Almond", "杏仁", "nut_cocoa", "tree_nut"),
    ("sensory.hazelnut", "Hazelnut", "榛子", "nut_cocoa", "tree_nut"),
    ("sensory.dark_chocolate", "Dark Chocolate", "黑巧克力", "nut_cocoa", "cocoa"),
    ("sensory.cinnamon", "Cinnamon", "肉桂", "spice_roasted", "warming_spice"),
    ("sensory.tobacco", "Tobacco", "烟草", "spice_roasted", "wood_tobacco"),
    ("sensory.smoky", "Smoky", "烟熏", "spice_roasted", "smoke"),
    ("sensory.green_tea", "Green Tea", "绿茶", "green_earthy", "tea"),
    ("sensory.cedar", "Cedar", "雪松", "green_earthy", "wood_tobacco"),
    ("sensory.earthy", "Earthy", "土壤感", "green_earthy", "earth"),
    ("sensory.fermented_character", "Fermented", "发酵感", "fermented", "fermented"),
    ("sensory.wine_like_character", "Winey", "葡萄酒感", "fermented", "winey"),
]

ALLOWED_EFFECTS = {
    "supports",
    "weakly_supports",
    "contradicts",
    "weakly_contradicts",
    "neutral",
    "unknown",
    "insufficient_evidence",
}

SCORE_WEIGHTS = {
    "direct_evidence": 2.5,
    "effective_record": 2.0,
    "source_diversity": 1.0,
    "governed_normalization": 0.5,
    "governed_semantic": 0.5,
    "structured_contrast": 0.5,
    "answer_supports": 3.0,
    "answer_weakly_supports": 1.25,
    "answer_contradicts": -3.0,
    "answer_weakly_contradicts": -1.25,
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_tsv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for source in rows:
            writer.writerow({field: source.get(field, "") for field in fields})


def truth(value: bool) -> str:
    return "true" if value else "false"


def bounded_ratio(value: int, maximum: int) -> float:
    if value <= 0 or maximum <= 0:
        return 0.0
    return min(math.log1p(value) / math.log1p(maximum), 1.0)


def build_semantic_counts() -> tuple[Counter[str], Counter[str]]:
    cluster_to_concepts: dict[str, set[str]] = defaultdict(set)
    for row in read_tsv(CURRENT / "ONTOLOGY_CONSOLIDATION_V2.tsv"):
        for concept in row["canonical_concept_ids"].split("|"):
            if concept:
                cluster_to_concepts[row["concept_cluster_id"]].add(concept)

    governed: Counter[str] = Counter()
    exploratory: Counter[str] = Counter()
    for row in read_tsv(CURRENT / "SEMANTIC_RELATION_EDGE.tsv"):
        concepts: set[str] = set()
        for field in ("subject_node_id", "object_node_id"):
            node = row[field]
            if node.startswith("semantic-concept:"):
                concepts.update(cluster_to_concepts.get(node.removeprefix("semantic-concept:"), set()))
        for concept in concepts:
            if row["governance_state"].startswith("GOVERNED"):
                governed[concept] += 1
            elif row["governance_state"] == "REVIEW_REQUIRED":
                exploratory[concept] += 1
    for row in read_tsv(CURRENT / "COMPOUND_COMPONENT.tsv"):
        if row["review_required"] == "true":
            exploratory[row["component_concept_id"]] += 1
    return governed, exploratory


def build_structured_claims() -> tuple[Counter[str], dict[str, set[str]]]:
    support: Counter[str] = Counter()
    sources: dict[str, set[str]] = defaultdict(set)
    token_to_concept = {
        "jasmine": "sensory.jasmine",
        "floral": "sensory.jasmine",
        "orange": "sensory.orange",
        "blueberry": "sensory.blueberry",
        "honey": "sensory.honey",
        "caramel": "sensory.caramel",
        "almond": "sensory.almond",
        "hazelnut": "sensory.hazelnut",
        "cocoa": "sensory.dark_chocolate",
        "cinnamon": "sensory.cinnamon",
        "smoky": "sensory.smoky",
        "tobacco": "sensory.tobacco",
        "earthy": "sensory.earthy",
        "fermented": "sensory.fermented_character",
        "wine": "sensory.wine_like_character",
    }
    for row in read_tsv(ROUND3H / "batch5" / "relationship_evidence_claims.tsv"):
        if row["review_status"] != "REVIEWED" or row["evidence_direction"] not in {"SUPPORTS", "MIXED"}:
            continue
        haystack = " ".join((row["target_entity_key"], row["method"])).lower()
        for token, concept in token_to_concept.items():
            if token in haystack:
                support[concept] += int(row["support_count"])
                sources[concept].add(row["source_family_key"])
    return support, sources


def build_candidates() -> list[dict[str, Any]]:
    distributions = {
        row["canonical_concept_id"]: row
        for row in read_tsv(CURRENT / "CLEANED_DESCRIPTOR_DISTRIBUTION.tsv")
        if row["canonical_concept_id"]
    }
    governed, exploratory = build_semantic_counts()
    structured, structured_sources = build_structured_claims()
    max_assertions = max(int(distributions[concept]["cleaned_assertion_support"]) for concept, *_ in CANDIDATE_DEFINITIONS)
    max_records = max(int(distributions[concept]["effective_record_support"]) for concept, *_ in CANDIDATE_DEFINITIONS)
    candidates: list[dict[str, Any]] = []
    for concept, label_en, label_zh, family, redundancy_group in CANDIDATE_DEFINITIONS:
        source = distributions[concept]
        assertion_support = int(source["cleaned_assertion_support"])
        record_support = int(source["effective_record_support"])
        family_support = int(source["source_family_support"])
        rights_support = int(source["rights_affirmative_support"])
        direct_component = bounded_ratio(assertion_support, max_assertions) * SCORE_WEIGHTS["direct_evidence"]
        record_component = bounded_ratio(record_support, max_records) * SCORE_WEIGHTS["effective_record"]
        diversity_component = min(family_support / 4.0, 1.0) * SCORE_WEIGHTS["source_diversity"]
        normalization_component = SCORE_WEIGHTS["governed_normalization"] if source["mapping_state"].startswith("AUTO_") else 0.0
        semantic_component = min(governed[concept], 3) / 3.0 * SCORE_WEIGHTS["governed_semantic"]
        structured_component = min(structured[concept], 20) / 20.0 * SCORE_WEIGHTS["structured_contrast"]
        base_score = sum((direct_component, record_component, diversity_component, normalization_component, semantic_component, structured_component))
        rights_eligible = rights_support > 0
        candidates.append(
            {
                "canonical_concept_id": concept,
                "display_label_en": label_en,
                "language_label_zh_hans": label_zh,
                "top_level_descriptor_family": family,
                "direct_professional_assertion_support": assertion_support,
                "unique_effective_record_support": record_support,
                "independent_source_family_support": family_support,
                "governed_normalization_support": 1,
                "governed_semantic_relation_support": governed[concept],
                "review_required_exploratory_relation_support": exploratory[concept],
                "c0_compatibility": "resolved_per_case_weak_or_neutral",
                "c1_compatibility": "neutral_zero_reviewed_mapping",
                "user_answer_compatibility": "resolved_per_case",
                "structured_contrast_evidence": structured[concept],
                "structured_contrast_source_families": "|".join(sorted(structured_sources[concept])),
                "contradiction_evidence": 0,
                "public_research_simulation_rights_eligible": truth(rights_eligible),
                "product_deployment_rights_status": "UNKNOWN_NOT_AUTHORIZED",
                "review_status": "GOVERNED_NORMALIZATION_NO_PRODUCT_OWNER_REVIEW",
                "redundancy_group": redundancy_group,
                "uncertainty_flags": "PRODUCT_DEPLOYMENT_RIGHTS_UNKNOWN|WEIGHTS_HEURISTIC",
                "abstention_flags": "RIGHTS_BLOCKED" if not rights_eligible else "",
                "direct_evidence_score_component": f"{direct_component:.6f}",
                "effective_record_score_component": f"{record_component:.6f}",
                "source_diversity_score_component": f"{diversity_component:.6f}",
                "governed_normalization_score_component": f"{normalization_component:.6f}",
                "governed_semantic_score_component": f"{semantic_component:.6f}",
                "structured_contrast_score_component": f"{structured_component:.6f}",
                "base_decision_score": f"{base_score:.6f}",
                "explanation_references": f"candidate:{concept}|distribution:{concept}",
                "lineage_paths": "db/data/current/CLEANED_DESCRIPTOR_DISTRIBUTION.tsv|db/data/current/ONTOLOGY_CONSOLIDATION_V2.tsv|db/data/round3h/batch5/relationship_evidence_claims.tsv|packages/flavor-data/src/descriptors.ts",
            }
        )
    return candidates


def build_c0_prior_inputs() -> dict[tuple[str, str], dict[str, Any]]:
    preparation_map = {
        "filter": "preparation.family.filter_percolation",
        "espresso": "preparation.family.espresso_pressure",
        "moka": "preparation.family.stovetop_boiled",
        "neapolitan_pot": "preparation.family.stovetop_boiled",
    }
    descriptor_map = {"Honey": "sensory.honey", "Caramel": "sensory.caramel"}
    by_concept: dict[str, list[float]] = defaultdict(list)
    by_cell: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in read_tsv(ROUND3H / "batch1" / "vezzulli_2022_table2_sensory_medians.tsv"):
        concept = descriptor_map.get(row["source_descriptor"])
        preparation = preparation_map.get(row["preparation"])
        if not concept or not preparation:
            continue
        value = float(row["parsed_value"])
        by_concept[concept].append(value)
        by_cell[(concept, preparation)].append(value)

    results: dict[tuple[str, str], dict[str, Any]] = {}
    for (concept, preparation), values in sorted(by_cell.items()):
        overall = sum(by_concept[concept]) / len(by_concept[concept])
        local = sum(values) / len(values)
        adjustment = max(-0.25, min(0.25, (local - overall) / 10.0))
        results[(concept, preparation)] = {
            "adjustment": round(adjustment, 6),
            "evidence_count": len(values),
            "source_family": "family.vezzulli-trainedpanel-2022",
            "locator": "db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv",
        }
    return results


def build_context_priors(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weak_inputs = build_c0_prior_inputs()
    rows: list[dict[str, Any]] = []
    for preparation, _, _ in PREPARATIONS:
        for roast, _, _ in ROASTS:
            for candidate in candidates:
                concept = candidate["canonical_concept_id"]
                source = weak_inputs.get((concept, preparation))
                c0_adjustment = source["adjustment"] if source else 0.0
                status = "weak" if c0_adjustment else "neutral"
                rows.append(
                    {
                        "context_prior_id": f"prior:{preparation}:{roast}:{concept}",
                        "preparation_family_key": preparation,
                        "roast_code": roast,
                        "canonical_concept_id": concept,
                        "c0_prior_adjustment": f"{c0_adjustment:.6f}",
                        "c1_prior_adjustment": "0.000000",
                        "combined_context_adjustment": f"{c0_adjustment:.6f}",
                        "prior_status": status,
                        "direct_context_evidence_count": source["evidence_count"] if source else 0,
                        "source_family_ids": source["source_family"] if source else "",
                        "c0_evidence_locator": source["locator"] if source else "",
                        "c1_evidence_locator": "db/data/round3m/C0_C1_EVIDENCE_RECEIPT.json",
                        "c1_mapping_status": "NEUTRAL_ZERO_REVIEWED_C1_MAPPING",
                        "rule": "WEAK_SOURCE_LOCAL_WITHIN_STUDY_DIFFERENCE" if source else "NEUTRAL_MISSING_DIRECT_EVIDENCE",
                        "lineage_paths": "db/022_round3b_context_governance.sql|db/data/round3m/C0_C1_EVIDENCE_RECEIPT.json" + ("|" + source["locator"] if source else ""),
                    }
                )
    return rows


def question_specs() -> list[dict[str, Any]]:
    groups = {
        "floral_tea": ["sensory.jasmine", "sensory.rose", "sensory.orange_blossom", "sensory.green_tea"],
        "fruit": ["sensory.lemon", "sensory.orange", "sensory.blueberry"],
        "cocoa_nut_caramel": ["sensory.honey", "sensory.caramel", "sensory.brown_sugar", "sensory.almond", "sensory.hazelnut", "sensory.dark_chocolate"],
        "roast_spice_smoke": ["sensory.cinnamon", "sensory.tobacco", "sensory.smoky", "sensory.cedar"],
        "earthy_fermented": ["sensory.earthy", "sensory.fermented_character", "sensory.wine_like_character"],
    }
    common_lineage = "db/data/round3h/batch5/question_research_evidence.tsv|db/data/round3e/generated/question_candidates.tsv"
    return [
        {
            "axis_id": "family_direction",
            "sensory_construct": "broad descriptor-family direction",
            "partitions": groups,
            "options": list(groups) + ["other", "unsure"],
            "sources": "family.bollen-robusta-qgraders-2024|family.coffee-cuality-experts-2026|family.gorman-milk-consumers-2021",
            "ambiguity": "combined family options are research constructs",
            "multilingual": "REVIEW_REQUIRED",
            "max_selected": 2,
            "lineage": common_lineage,
        },
        {
            "axis_id": "fruit_region",
            "sensory_construct": "specific fruit reference region",
            "partitions": {"citrus": ["sensory.lemon", "sensory.orange"], "berry": ["sensory.blueberry"]},
            "options": ["citrus", "berry", "other", "none", "unsure"],
            "sources": "family.bollen-robusta-qgraders-2024|family.coffee-cuality-experts-2026",
            "ambiguity": "named fruit does not establish perceptual equivalence",
            "multilingual": "REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": common_lineage,
        },
        {
            "axis_id": "browned_sweet_reference",
            "sensory_construct": "browned sweet, cocoa, or nut reference",
            "partitions": {"caramel_honey": ["sensory.honey", "sensory.caramel"], "brown_sugar": ["sensory.brown_sugar"], "nuts": ["sensory.almond", "sensory.hazelnut"], "dark_chocolate": ["sensory.dark_chocolate"]},
            "options": ["caramel_honey", "brown_sugar", "nuts", "dark_chocolate", "none", "unsure"],
            "sources": "family.vezzulli-trainedpanel-2022|family.nguyen-pbma-thai-2026|family.bollen-robusta-qgraders-2024",
            "ambiguity": "sweet taste and sweet-associated references remain distinct",
            "multilingual": "REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": common_lineage,
        },
        {
            "axis_id": "floral_tea_reference",
            "sensory_construct": "floral or tea reference",
            "partitions": {"white_floral": ["sensory.jasmine"], "rose_floral": ["sensory.rose"], "citrus_blossom": ["sensory.orange_blossom"], "tea": ["sensory.green_tea"]},
            "options": ["white_floral", "rose_floral", "citrus_blossom", "tea", "none", "unsure"],
            "sources": "family.bollen-robusta-qgraders-2024|family.gorman-milk-consumers-2021|family.coffee-cuality-experts-2026",
            "ambiguity": "floral and tea are not treated as equivalent",
            "multilingual": "BILINGUAL_REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": common_lineage,
        },
        {
            "axis_id": "roast_smoke_reference",
            "sensory_construct": "spice, smoke, or wood reference",
            "partitions": {"warming_spice": ["sensory.cinnamon"], "smoke": ["sensory.smoky"], "wood_tobacco": ["sensory.tobacco", "sensory.cedar"]},
            "options": ["warming_spice", "smoke", "wood_tobacco", "none", "unsure"],
            "sources": "family.gorman-milk-consumers-2021|family.condelli-consumer-cata-2022|family.heo-coldbrew-consumers-2019",
            "ambiguity": "roasted, burnt, smoky, and ashy remain distinct source constructs",
            "multilingual": "REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": common_lineage,
        },
        {
            "axis_id": "fermentation_character",
            "sensory_construct": "earthy, fermented, or wine-like reference",
            "partitions": {"earthy": ["sensory.earthy"], "fermented": ["sensory.fermented_character"], "winey": ["sensory.wine_like_character"]},
            "options": ["earthy", "fermented", "winey", "none", "unsure"],
            "sources": "family.ace_cup_of_excellence|family.zenodo_golovinsky_q_grader_dataset",
            "ambiguity": "process-linked language requires contextual interpretation",
            "multilingual": "REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": "db/data/current/CLEANED_DESCRIPTOR_DISTRIBUTION.tsv|db/data/round3g/question_target_reviews.tsv",
        },
        {
            "axis_id": "acidity_character",
            "sensory_construct": "citrus-like versus other fruit-associated acidity reference",
            "partitions": {"citrus_like": ["sensory.lemon", "sensory.orange"], "berry_like": ["sensory.blueberry"]},
            "options": ["citrus_like", "berry_like", "none", "unsure"],
            "sources": "family.iswaldi-rataconsumers-2026|family.coffee-cuality-experts-2026",
            "ambiguity": "citrus descriptors are not acidity measurements",
            "multilingual": "BILINGUAL_REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": common_lineage,
        },
        {
            "axis_id": "texture_character",
            "sensory_construct": "mouthfeel and tactile sensation",
            "partitions": {},
            "options": ["silky", "creamy", "heavy", "drying", "thin", "unsure"],
            "sources": "family.iswaldi-rataconsumers-2026|family.gorman-milk-consumers-2021|family.nguyen-pbma-thai-2026|family.condelli-consumer-cata-2022",
            "ambiguity": "no admitted candidate concepts in this flavor-only simulator",
            "multilingual": "BILINGUAL_REVIEW_REQUIRED",
            "max_selected": 1,
            "lineage": common_lineage,
        },
    ]


def build_question_axes() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in question_specs():
        nonempty = [values for values in spec["partitions"].values() if values]
        divides = len(nonempty) >= 2 and len({concept for values in nonempty for concept in values}) >= 2
        source_count = len(spec["sources"].split("|")) if spec["sources"] else 0
        simulation_eligible = divides and source_count >= 2
        partition_sizes = {key: len(value) for key, value in spec["partitions"].items()}
        total = sum(partition_sizes.values())
        largest = max(partition_sizes.values(), default=0)
        separation = (1.0 - largest / total) if total else 0.0
        rows.append(
            {
                "question_axis_id": spec["axis_id"],
                "sensory_construct": spec["sensory_construct"],
                "candidate_partitions_json": stable_json(spec["partitions"]),
                "option_concepts_json": stable_json(spec["options"]),
                "supporting_evidence": "DIRECT_STRUCTURED_RESEARCH_SUPPORT",
                "source_family_ids": spec["sources"],
                "source_family_count": source_count,
                "coverage_count": total,
                "partition_count": len(nonempty),
                "ambiguity_risk": spec["ambiguity"],
                "context_dependence": "NOT_ESTIMATED",
                "multilingual_status": spec["multilingual"],
                "review_status": "RESEARCH_SUPPORTED_NOT_USER_VALIDATED",
                "divides_candidate_set": truth(divides),
                "offline_simulation_eligible": truth(simulation_eligible),
                "product_use_eligible": "false",
                "product_ineligibility_reason": "INFORMATION_GAIN_AND_USER_COMPREHENSION_NOT_VALIDATED",
                "maximum_selected_options": spec["max_selected"],
                "expected_separation_score": f"{separation:.6f}",
                "lineage_paths": spec["lineage"],
            }
        )
    return rows


def build_answer_effects(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_ids = [row["canonical_concept_id"] for row in candidates]
    rows: list[dict[str, Any]] = []
    for spec in question_specs():
        positive_universe = {concept for values in spec["partitions"].values() for concept in values}
        for option in spec["options"]:
            selected = set(spec["partitions"].get(option, []))
            for concept in candidate_ids:
                if option == "unsure":
                    effect = "unknown"
                    basis = "UNSURE_PATH_NO_EVIDENCE_CHANGE"
                elif option == "other":
                    effect = "insufficient_evidence"
                    basis = "OPEN_OPTION_REQUIRES_FOLLOW_UP"
                elif option == "none":
                    effect = "weakly_contradicts" if concept in positive_universe else "neutral"
                    basis = "EXPLICIT_NONE_OPTION_NOT_NONMENTION"
                elif concept in selected:
                    effect = "supports"
                    basis = "EXPLICIT_SELECTED_OPTION"
                else:
                    effect = "neutral"
                    basis = "UNSELECTED_OR_UNRELATED_IS_NOT_NEGATIVE_EVIDENCE"
                rows.append(
                    {
                        "answer_effect_id": f"effect:{spec['axis_id']}:{option}:{concept}",
                        "question_axis_id": spec["axis_id"],
                        "option_id": option,
                        "canonical_concept_id": concept,
                        "effect_type": effect,
                        "decision_score_adjustment": f"{effect_adjustment(effect):.6f}",
                        "effect_basis": basis,
                        "structured_negative_evidence": truth(effect in {"contradicts", "weakly_contradicts"}),
                        "nonmention_used_as_negative": "false",
                        "review_status": "OFFLINE_POLICY_FIXTURE_NOT_CALIBRATED",
                        "lineage_paths": spec["lineage"],
                    }
                )
    return rows


def effect_adjustment(effect: str) -> float:
    return {
        "supports": SCORE_WEIGHTS["answer_supports"],
        "weakly_supports": SCORE_WEIGHTS["answer_weakly_supports"],
        "contradicts": SCORE_WEIGHTS["answer_contradicts"],
        "weakly_contradicts": SCORE_WEIGHTS["answer_weakly_contradicts"],
        "neutral": 0.0,
        "unknown": 0.0,
        "insufficient_evidence": 0.0,
    }[effect]


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for preparation_index, (preparation, _, _) in enumerate(PREPARATIONS):
        for roast_index, (roast, _, _) in enumerate(ROASTS):
            cases.append(
                {
                    "inference_case_id": f"context-{preparation_index + 1:02d}-{roast_index + 1:02d}",
                    "case_type": "CONTEXT_ONLY",
                    "preparation_family_key": preparation,
                    "roast_code": roast,
                    "answers_json": "[]",
                    "open_set_expression": "",
                    "locale": "en",
                    "expected_policy_state": "NEEDS_MANDATORY_Q1",
                    "gold_descriptor_labels": "",
                    "lineage_paths": "docs/product/PRODUCT_CONTRACT_V0.md|db/022_round3b_context_governance.sql",
                }
            )

    answer_sequences = [
        [("family_direction", "cocoa_nut_caramel"), ("family_direction", "roast_spice_smoke"), ("fruit_region", "berry"), ("floral_tea_reference", "white_floral")],
        [("family_direction", "fruit"), ("browned_sweet_reference", "caramel_honey"), ("floral_tea_reference", "white_floral")],
        [("family_direction", "roast_spice_smoke"), ("fermentation_character", "winey"), ("fruit_region", "berry")],
        [("family_direction", "floral_tea"), ("browned_sweet_reference", "nuts"), ("acidity_character", "citrus_like")],
    ]
    for index in range(24):
        preparation = PREPARATIONS[index % len(PREPARATIONS)][0]
        roast = ROASTS[index % len(ROASTS)][0]
        answers = [{"question_axis_id": axis, "option_id": option} for axis, option in answer_sequences[index % len(answer_sequences)]]
        cases.append(
            {
                "inference_case_id": f"answer-update-{index + 1:02d}",
                "case_type": "ANSWER_UPDATE",
                "preparation_family_key": preparation,
                "roast_code": roast,
                "answers_json": stable_json(answers),
                "open_set_expression": "",
                "locale": "zh-Hans" if index % 3 == 0 else "en",
                "expected_policy_state": "OUTPUT_OR_PARTIAL_OUTPUT",
                "gold_descriptor_labels": "",
                "lineage_paths": "db/data/product-inference-v0/PRODUCT_ANSWER_EFFECT.tsv",
            }
        )

    for index in range(8):
        cases.append(
            {
                "inference_case_id": f"override-{index + 1:02d}",
                "case_type": "USER_ANSWER_OVERRIDES_CONTEXT",
                "preparation_family_key": "preparation.family.espresso_pressure",
                "roast_code": ROASTS[index % len(ROASTS)][0],
                "answers_json": stable_json([{"question_axis_id": "browned_sweet_reference", "option_id": "caramel_honey"}]),
                "open_set_expression": "",
                "locale": "en",
                "expected_policy_state": "ANSWER_OVERRIDES_WEAK_PRIOR",
                "gold_descriptor_labels": "",
                "lineage_paths": "db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv",
            }
        )
    for index in range(8):
        cases.append(
            {
                "inference_case_id": f"missing-context-{index + 1:02d}",
                "case_type": "MISSING_CONTEXT",
                "preparation_family_key": "",
                "roast_code": "",
                "answers_json": stable_json([{"question_axis_id": "family_direction", "option_id": "fruit"}]),
                "open_set_expression": "",
                "locale": "en",
                "expected_policy_state": "NEUTRAL_CONTEXT_PRIOR",
                "gold_descriptor_labels": "",
                "lineage_paths": "docs/product/PRODUCT_CONTRACT_V0.md",
            }
        )
    for index in range(8):
        cases.append(
            {
                "inference_case_id": f"conflict-{index + 1:02d}",
                "case_type": "CONFLICTING_ANSWER",
                "preparation_family_key": PREPARATIONS[index][0],
                "roast_code": ROASTS[index % len(ROASTS)][0],
                "answers_json": stable_json([
                    {"question_axis_id": "fruit_region", "option_id": "citrus"},
                    {"question_axis_id": "fruit_region", "option_id": "berry"},
                ]),
                "open_set_expression": "",
                "locale": "en",
                "expected_policy_state": "ABSTAINED_CONFLICT",
                "gold_descriptor_labels": "",
                "lineage_paths": "db/data/product-inference-v0/PRODUCT_TASK_CONTRACT.json",
            }
        )
    for index in range(8):
        cases.append(
            {
                "inference_case_id": f"open-set-{index + 1:02d}",
                "case_type": "OPEN_SET_UNKNOWN_EXPRESSION",
                "preparation_family_key": PREPARATIONS[index][0],
                "roast_code": ROASTS[index % len(ROASTS)][0],
                "answers_json": "[]",
                "open_set_expression": f"unknown-expression-fixture-{index + 1:02d}",
                "locale": "en",
                "expected_policy_state": "ABSTAINED_OPEN_SET",
                "gold_descriptor_labels": "",
                "lineage_paths": "db/data/current/OPEN_SET_UNSEEN_TARGET_BENCHMARK.tsv",
            }
        )
    for index in range(8):
        cases.append(
            {
                "inference_case_id": f"rights-blocked-{index + 1:02d}",
                "case_type": "INSUFFICIENT_EVIDENCE_RIGHTS_BLOCKED",
                "preparation_family_key": PREPARATIONS[index][0],
                "roast_code": ROASTS[index % len(ROASTS)][0],
                "answers_json": stable_json([{"question_axis_id": "floral_tea_reference", "option_id": "citrus_blossom"}]),
                "open_set_expression": "",
                "locale": "en",
                "expected_policy_state": "ABSTAINED_RIGHTS_BLOCKED",
                "gold_descriptor_labels": "",
                "lineage_paths": "db/data/current/CLEANED_DESCRIPTOR_DISTRIBUTION.tsv",
            }
        )
    return cases


def index_effects(effects: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (row["question_axis_id"], row["option_id"], row["canonical_concept_id"]): row
        for row in effects
    }


def index_priors(priors: list[dict[str, Any]]) -> dict[tuple[str, str, str], float]:
    return {
        (row["preparation_family_key"], row["roast_code"], row["canonical_concept_id"]): float(row["combined_context_adjustment"])
        for row in priors
    }


def simulate_case(
    case: dict[str, Any],
    candidates: list[dict[str, Any]],
    priors: list[dict[str, Any]],
    effects: list[dict[str, Any]],
    axes: list[dict[str, Any]],
    *,
    apply_redundancy: bool = True,
    answer_weight_overrides: dict[str, float] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    answers = json.loads(case["answers_json"])
    answer_axes: dict[str, set[str]] = defaultdict(set)
    for answer in answers:
        answer_axes[answer["question_axis_id"]].add(answer["option_id"])
    selection_limits = {spec["axis_id"]: spec["max_selected"] for spec in question_specs()}
    conflict = any(len(options) > selection_limits[axis] for axis, options in answer_axes.items())
    effect_lookup = index_effects(effects)
    axis_lookup = {row["question_axis_id"]: row for row in axes}
    eligible_axis_ids = [
        row["question_axis_id"]
        for row in sorted(
            axes,
            key=lambda row: (
                -float(row["expected_separation_score"]),
                -int(row["coverage_count"]),
                row["question_axis_id"],
            ),
        )
        if row["offline_simulation_eligible"] == "true"
    ]

    def next_question_axis_id(candidate_region: set[str] | None = None) -> str:
        region = candidate_region or {row["canonical_concept_id"] for row in candidates}
        for axis_id in eligible_axis_ids:
            if axis_id in answer_axes:
                continue
            partitions = json.loads(axis_lookup[axis_id]["candidate_partitions_json"])
            nonempty_partitions = sum(bool(region & set(values)) for values in partitions.values())
            if nonempty_partitions >= 2:
                return axis_id
        return ""

    positively_supported: set[str] = set()
    question_trace: list[dict[str, Any]] = []
    for question_index, answer in enumerate(answers, start=1):
        axis = axis_lookup[answer["question_axis_id"]]
        partitions = json.loads(axis["candidate_partitions_json"])
        before_count = len(positively_supported) if positively_supported else len(candidates)
        newly_supported = {
            candidate["canonical_concept_id"]
            for candidate in candidates
            if effect_lookup[(answer["question_axis_id"], answer["option_id"], candidate["canonical_concept_id"])]["effect_type"]
            in {"supports", "weakly_supports"}
        }
        positively_supported.update(newly_supported)
        question_trace.append(
            {
                "question_position": question_index,
                "question_axis_id": answer["question_axis_id"],
                "selected_option_id": answer["option_id"],
                "candidate_set_before_count": before_count,
                "candidate_partition_sizes": {key: len(values) for key, values in partitions.items()},
                "evidence_coverage_count": int(axis["coverage_count"]),
                "expected_separation_score": float(axis["expected_separation_score"]),
                "unanswered_or_unsure_path": "NO_EVIDENCE_CHANGE",
                "candidate_state_after_count": len(positively_supported),
            }
        )
    base_result = {
        "inference_case_id": case["inference_case_id"],
        "case_type": case["case_type"],
        "preparation_family_key": case["preparation_family_key"],
        "roast_code": case["roast_code"],
        "selected_question_axis_ids": "|".join(answer_axes),
        "question_count": len(answer_axes),
        "stopped_before_q4": truth(len(answer_axes) < 4),
        "main_concept_ids": "",
        "secondary_concept_ids": "",
        "main_output_count": 0,
        "secondary_output_count": 0,
        "abstention_codes": "",
        "override_observed": "false",
        "candidate_state_before_json": stable_json({"candidate_count": len(candidates)}),
        "candidate_state_after_json": stable_json({"candidate_count": 0}),
        "decision_score_semantics": "UNCALIBRATED_DETERMINISTIC_DECISION_SCORE_NOT_PROBABILITY",
        "policy_version": POLICY_VERSION,
        "lineage_paths": "db/data/product-inference-v0/PRODUCT_CONCEPT_CANDIDATE.tsv|db/data/product-inference-v0/PRODUCT_CONTEXT_PRIOR.tsv|db/data/product-inference-v0/PRODUCT_ANSWER_EFFECT.tsv",
        "next_question_axis_id": next_question_axis_id() if not answers else "",
        "question_trace_json": stable_json(question_trace),
    }
    if case["open_set_expression"]:
        base_result.update({"result_state": "ABSTAINED_OPEN_SET", "abstention_codes": "UNKNOWN_DESCRIPTOR_TARGET|OPEN_SET_EXPRESSION"})
        return base_result, []
    if conflict:
        base_result.update({"result_state": "ABSTAINED_CONFLICT", "abstention_codes": "CONFLICTING_USER_ANSWERS"})
        return base_result, []
    if not answers:
        base_result.update({"result_state": "NEEDS_MANDATORY_Q1", "abstention_codes": "MANDATORY_Q1_UNANSWERED"})
        return base_result, []

    prior_lookup = index_priors(priors)
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        concept = candidate["canonical_concept_id"]
        context_component = 0.0
        if case["preparation_family_key"] and case["roast_code"]:
            context_component = prior_lookup[(case["preparation_family_key"], case["roast_code"], concept)]
        typed_effects: list[str] = []
        answer_component = 0.0
        for answer in answers:
            effect = effect_lookup[(answer["question_axis_id"], answer["option_id"], concept)]["effect_type"]
            typed_effects.append(effect)
            answer_component += (
                answer_weight_overrides[effect]
                if answer_weight_overrides and effect in answer_weight_overrides
                else effect_adjustment(effect)
            )
        score = float(candidate["base_decision_score"]) + context_component + answer_component
        ranked.append(
            {
                "candidate": candidate,
                "context_component": context_component,
                "answer_component": answer_component,
                "typed_effects": typed_effects,
                "decision_score": score,
            }
        )
    ranked.sort(key=lambda row: (-row["decision_score"], row["candidate"]["canonical_concept_id"]))

    eligible = [
        row
        for row in ranked
        if row["answer_component"] > 0
        and row["candidate"]["public_research_simulation_rights_eligible"] == "true"
    ]
    supported = [row for row in ranked if row["answer_component"] > 0]
    if supported and not eligible:
        base_result.update({"result_state": "ABSTAINED_RIGHTS_BLOCKED", "abstention_codes": "NO_RIGHTS_ELIGIBLE_EVIDENCE"})
        return base_result, []
    if not eligible:
        base_result.update({"result_state": "ABSTAINED_INSUFFICIENT_EVIDENCE", "abstention_codes": "INSUFFICIENT_DIRECT_SUPPORT"})
        return base_result, []

    selected_groups: set[str] = set()
    selected: list[tuple[str, dict[str, Any]]] = []
    for row in eligible:
        group = row["candidate"]["redundancy_group"]
        if apply_redundancy and group in selected_groups:
            continue
        tier = "main" if len([item for item in selected if item[0] == "main"]) < 5 else "secondary"
        if tier == "secondary" and len([item for item in selected if item[0] == "secondary"]) >= 3:
            break
        selected_groups.add(group)
        selected.append((tier, row))

    main = [row for tier, row in selected if tier == "main"]
    secondary = [row for tier, row in selected if tier == "secondary"]
    result_state = "OUTPUT_COMPLETE_5_PLUS_3" if len(main) == 5 and len(secondary) == 3 else "PARTIAL_OUTPUT_INSUFFICIENT_SUPPORTED_CANDIDATES"
    abstentions: list[str] = []
    if len(main) < 5:
        abstentions.append("INSUFFICIENT_EVIDENCE_FOR_FIVE_MAIN")
    if len(secondary) < 3:
        abstentions.append("INSUFFICIENT_EVIDENCE_FOR_SECONDARY")
    override = any(row["context_component"] < 0 and row["answer_component"] > 0 for row in main + secondary)
    eligible_region = {row["candidate"]["canonical_concept_id"] for row in eligible}
    next_axis = next_question_axis_id(eligible_region) if result_state.startswith("PARTIAL") and len(answer_axes) < 4 else ""
    base_result.update(
        {
            "result_state": result_state,
            "main_concept_ids": "|".join(row["candidate"]["canonical_concept_id"] for row in main),
            "secondary_concept_ids": "|".join(row["candidate"]["canonical_concept_id"] for row in secondary),
            "main_output_count": len(main),
            "secondary_output_count": len(secondary),
            "abstention_codes": "|".join(abstentions),
            "override_observed": truth(override),
            "candidate_state_after_json": stable_json({"supported_count": len(supported), "rights_eligible_count": len(eligible), "selected_count": len(selected)}),
            "next_question_axis_id": next_axis,
            "stopped_before_q4": truth(len(answer_axes) < 4 and not next_axis),
        }
    )
    explanations: list[dict[str, Any]] = []
    for tier, rows_for_tier in (("main", main), ("secondary", secondary)):
        for rank, row in enumerate(rows_for_tier, start=1):
            candidate = row["candidate"]
            explanations.append(
                {
                    "explanation_id": f"explanation:{case['inference_case_id']}:{tier}:{rank}",
                    "inference_case_id": case["inference_case_id"],
                    "canonical_concept_id": candidate["canonical_concept_id"],
                    "output_tier": tier,
                    "deterministic_rank": rank,
                    "decision_score": f"{row['decision_score']:.6f}",
                    "direct_evidence_component": candidate["direct_evidence_score_component"],
                    "effective_record_component": candidate["effective_record_score_component"],
                    "source_diversity_component": candidate["source_diversity_score_component"],
                    "context_component": f"{row['context_component']:.6f}",
                    "answer_component": f"{row['answer_component']:.6f}",
                    "governed_semantic_component": candidate["governed_semantic_score_component"],
                    "structured_contrast_component": candidate["structured_contrast_score_component"],
                    "typed_answer_effects": "|".join(row["typed_effects"]),
                    "rights_state": "PUBLIC_RESEARCH_SIMULATION_ELIGIBLE_PRODUCT_DEPLOYMENT_UNKNOWN",
                    "review_state": candidate["review_status"],
                    "redundancy_decision": f"SELECTED_ONE_FROM_GROUP:{candidate['redundancy_group']}",
                    "uncertainty_note": "Heuristic policy output; not a probability, scientific validation result, or production authorization.",
                    "human_readable_explanation": f"{candidate['display_label_en']} is retained because explicit answer support and direct professional evidence remain after rights and redundancy checks.",
                    "lineage_paths": candidate["lineage_paths"] + "|db/data/product-inference-v0/PRODUCT_ANSWER_EFFECT.tsv",
                }
            )
    return base_result, explanations


def without_candidate_components(
    candidates: list[dict[str, Any]],
    component_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for source in candidates:
        row = dict(source)
        removed = sum(float(row[field]) for field in component_fields)
        row["base_decision_score"] = f"{float(row['base_decision_score']) - removed:.6f}"
        for field in component_fields:
            row[field] = "0.000000"
        transformed.append(row)
    return transformed


def neutralize_context_component(
    priors: list[dict[str, Any]],
    component: str,
) -> list[dict[str, Any]]:
    transformed: list[dict[str, Any]] = []
    for source in priors:
        row = dict(source)
        if component == "c0":
            row["c0_prior_adjustment"] = "0.000000"
            row["combined_context_adjustment"] = row["c1_prior_adjustment"]
        else:
            row["c1_prior_adjustment"] = "0.000000"
            row["combined_context_adjustment"] = row["c0_prior_adjustment"]
        transformed.append(row)
    return transformed


def result_signature(row: dict[str, Any]) -> tuple[str, str, str]:
    return row["result_state"], row["main_concept_ids"], row["secondary_concept_ids"]


def sensitivity_metrics(
    baseline: list[dict[str, Any]],
    variant: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_by_id = {row["inference_case_id"]: row for row in baseline}
    changed = sum(result_signature(row) != result_signature(baseline_by_id[row["inference_case_id"]]) for row in variant)
    state_changed = sum(row["result_state"] != baseline_by_id[row["inference_case_id"]]["result_state"] for row in variant)
    redundancy = {row["canonical_concept_id"]: row["redundancy_group"] for row in candidates}
    duplicate_group_count = 0
    for row in variant:
        outputs = [value for field in ("main_concept_ids", "secondary_concept_ids") for value in row[field].split("|") if value]
        groups = [redundancy[value] for value in outputs]
        duplicate_group_count += len(groups) - len(set(groups))
    return {
        "output_changed_case_count": changed,
        "result_state_changed_case_count": state_changed,
        "main_output_fill_rate": round(sum(int(row["main_output_count"]) for row in variant) / (len(variant) * 5), 6),
        "secondary_output_fill_rate": round(sum(int(row["secondary_output_count"]) for row in variant) / (len(variant) * 3), 6),
        "complete_abstention_case_count": sum(row["result_state"].startswith("ABSTAINED") for row in variant),
        "duplicate_redundancy_group_pressure_count": duplicate_group_count,
    }


def build_sensitivity_analysis(
    cases: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    priors: list[dict[str, Any]],
    effects: list[dict[str, Any]],
    axes: list[dict[str, Any]],
    baseline: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    candidate_variants = {
        "without_direct_evidence": ("direct_evidence_score_component",),
        "without_effective_record": ("effective_record_score_component",),
        "without_source_diversity": ("source_diversity_score_component",),
        "without_governed_normalization": ("governed_normalization_score_component",),
        "without_governed_semantic": ("governed_semantic_score_component",),
        "without_structured_contrast": ("structured_contrast_score_component",),
    }
    results: dict[str, dict[str, Any]] = {}

    def run(
        variant_candidates: list[dict[str, Any]] = candidates,
        variant_priors: list[dict[str, Any]] = priors,
        *,
        apply_redundancy: bool = True,
        answer_weight_overrides: dict[str, float] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            simulate_case(
                case,
                variant_candidates,
                variant_priors,
                effects,
                axes,
                apply_redundancy=apply_redundancy,
                answer_weight_overrides=answer_weight_overrides,
            )[0]
            for case in cases
        ]

    for name, fields in candidate_variants.items():
        results[name] = sensitivity_metrics(baseline, run(without_candidate_components(candidates, fields)), candidates)
    results["without_c0_prior"] = sensitivity_metrics(baseline, run(variant_priors=neutralize_context_component(priors, "c0")), candidates)
    results["without_c1_prior"] = sensitivity_metrics(baseline, run(variant_priors=neutralize_context_component(priors, "c1")), candidates)
    results["without_review_required_exploration"] = sensitivity_metrics(baseline, run(), candidates)
    results["without_redundancy"] = sensitivity_metrics(baseline, run(apply_redundancy=False), candidates)
    results["without_positive_answer_weights"] = sensitivity_metrics(
        baseline,
        run(answer_weight_overrides={"supports": 0.0, "weakly_supports": 0.0}),
        candidates,
    )
    results["without_contradiction_weights"] = sensitivity_metrics(
        baseline,
        run(answer_weight_overrides={"contradicts": 0.0, "weakly_contradicts": 0.0}),
        candidates,
    )
    return results


def build_coverage(
    candidates: list[dict[str, Any]],
    priors: list[dict[str, Any]],
    axes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    weak_by_preparation: Counter[str] = Counter()
    for row in priors:
        if row["prior_status"] == "weak" and row["roast_code"] == "medium":
            weak_by_preparation[row["preparation_family_key"]] += 1
    eligible_axes = sum(row["offline_simulation_eligible"] == "true" for row in axes)
    rows: list[dict[str, Any]] = []
    for preparation, _, _ in PREPARATIONS:
        for roast, _, _ in ROASTS:
            weak_count = weak_by_preparation[preparation]
            rows.append(
                {
                    "coverage_row_id": f"cell:{preparation}:{roast}",
                    "row_kind": "C0_C1_CELL",
                    "preparation_family_key": preparation,
                    "roast_code": roast,
                    "dimension_name": "",
                    "dimension_value": "",
                    "direct_professional_record_count": 0,
                    "direct_context_evidence_count": 0,
                    "descriptor_concept_count": weak_count,
                    "source_family_count": 1 if weak_count else 0,
                    "structured_contrast_record_count": 0,
                    "positive_only_record_count": 0,
                    "review_complete_relation_count": 0,
                    "review_required_relation_count": 0,
                    "rights_eligible_record_count": 0,
                    "main_output_capable_concept_count": sum(row["public_research_simulation_rights_eligible"] == "true" for row in candidates),
                    "secondary_output_capable_concept_count": sum(row["public_research_simulation_rights_eligible"] == "true" for row in candidates),
                    "question_axis_coverage": eligible_axes,
                    "prior_status": "weak" if weak_count else "neutral",
                    "key_gap": "ZERO_REVIEWED_C1_MAPPING_PREVENTS_JOINT_CELL_EVIDENCE",
                    "acquisition_priority": "HIGH" if weak_count == 0 else "MEDIUM",
                    "lineage_paths": "db/data/round3m/C0_C1_EVIDENCE_RECEIPT.json|db/data/round3h/batch1/vezzulli_2022_table2_sensory_medians.tsv",
                }
            )

    summaries: list[tuple[str, str, int, str]] = []
    for family, count in sorted(Counter(row["top_level_descriptor_family"] for row in candidates).items()):
        summaries.append(("descriptor_family", family, count, "PRODUCT_CONCEPT_CANDIDATE.tsv"))
    for axis in axes:
        summaries.append(("question_axis", axis["question_axis_id"], int(axis["coverage_count"]), "PRODUCT_QUESTION_AXIS.tsv"))
    for language in ("en", "zh-Hans"):
        summaries.append(("language", language, len(candidates), "packages/flavor-data/src/descriptors.ts"))
    summaries.extend(
        [
            ("evidence_structure", "structured", sum(int(row["structured_contrast_evidence"]) > 0 for row in candidates), "db/data/round3h/batch5/relationship_evidence_claims.tsv"),
            ("evidence_structure", "free_text_aggregate", len(candidates), "db/data/current/CLEANED_DESCRIPTOR_DISTRIBUTION.tsv"),
            ("rights_status", "public_research_simulation_eligible", sum(row["public_research_simulation_rights_eligible"] == "true" for row in candidates), "db/data/current/CLEANED_DESCRIPTOR_DISTRIBUTION.tsv"),
            ("rights_status", "product_deployment_unknown", len(candidates), "db/data/current/PURPOSE_SPECIFIC_RIGHTS_MATRIX.tsv"),
            ("review_status", "product_owner_review_missing", len(candidates), "PRODUCT_OWNER_REVIEW_PACKET.tsv"),
            ("roast_evidence", "reviewed_project_c1_mapping", 0, "db/data/round3m/C0_C1_EVIDENCE_RECEIPT.json"),
        ]
    )
    for index, (dimension, value, count, source) in enumerate(summaries, start=1):
        rows.append(
            {
                "coverage_row_id": f"summary:{index:03d}",
                "row_kind": "DIMENSION_SUMMARY",
                "preparation_family_key": "",
                "roast_code": "",
                "dimension_name": dimension,
                "dimension_value": value,
                "direct_professional_record_count": count,
                "direct_context_evidence_count": 0,
                "descriptor_concept_count": count,
                "source_family_count": 0,
                "structured_contrast_record_count": 0,
                "positive_only_record_count": 0,
                "review_complete_relation_count": 0,
                "review_required_relation_count": 0,
                "rights_eligible_record_count": 0,
                "main_output_capable_concept_count": 0,
                "secondary_output_capable_concept_count": 0,
                "question_axis_coverage": 0,
                "prior_status": "not_applicable",
                "key_gap": "SUMMARY_NOT_JOINT_CONTEXT_EVIDENCE",
                "acquisition_priority": "REVIEW",
                "lineage_paths": source,
            }
        )
    return rows


def build_output_policy() -> list[dict[str, Any]]:
    rows = [
        ("OUTPUT_LIMIT", "main_maximum", "5", "Return fewer when support is insufficient."),
        ("OUTPUT_LIMIT", "secondary_maximum", "3", "Return zero when support is insufficient."),
        ("ELIGIBILITY", "main", "explicit_answer_support+direct_evidence+rights+governed_mapping", "Review-required relations cannot independently promote main outputs."),
        ("ELIGIBILITY", "secondary", "explicit_answer_support+direct_evidence+rights+governed_mapping", "Secondary is not a slot-filling fallback."),
        ("REDUNDANCY", "one_per_redundancy_group", "true", "Exact aliases and unnecessary near duplicates are suppressed."),
        ("STOPPING", "question_budget", "Q1_mandatory_Q2_Q4_conditional_Q5_exceptional", "Offline cases may stop before Q4."),
        ("RIGHTS", "simulation_scope", "PUBLIC_RESEARCH_ONLY", "Product deployment rights remain unknown."),
        ("SCORE_SEMANTICS", "calibration", "UNCALIBRATED_DECISION_SCORE", "The value is not a probability or confidence percentage."),
    ]
    rows.extend(("WEIGHT", key, f"{value:.6f}", "Hand-declared sensitivity target; neither learned nor optimal.") for key, value in SCORE_WEIGHTS.items())
    rows.extend(
        [
            ("SENSITIVITY_VARIANT", "without_c0_prior", "REQUIRED", "Compare rankings with C0 adjustment set to zero."),
            ("SENSITIVITY_VARIANT", "without_c1_prior", "NO_EFFECT_CURRENTLY", "All C1 adjustments are neutral because reviewed mappings are zero."),
            ("SENSITIVITY_VARIANT", "without_governed_semantic", "REQUIRED", "Remove only the governed semantic score component."),
            ("SENSITIVITY_VARIANT", "without_review_required_exploration", "NO_PRIMARY_EFFECT_BY_CONTRACT", "Exploration never independently contributes to main score."),
            ("SENSITIVITY_VARIANT", "without_redundancy", "REQUIRED", "Report duplicate-group pressure without changing accepted outputs."),
            ("SENSITIVITY_VARIANT", "without_structured_contrast", "REQUIRED", "Remove the bounded structured component."),
        ]
    )
    return [
        {
            "policy_row_id": f"policy:{index:03d}",
            "policy_type": kind,
            "policy_key": key,
            "policy_value": value,
            "interpretation": note,
            "policy_version": POLICY_VERSION,
            "lineage_paths": "docs/product/PRODUCT_CONTRACT_V0.md|docs/architecture/ADAPTIVE_CONTEXT_QUESTION_ARCHITECTURE.md",
        }
        for index, (kind, key, value, note) in enumerate(rows, start=1)
    ]


def build_abstention_rules() -> list[dict[str, Any]]:
    definitions = [
        ("NO_RIGHTS_ELIGIBLE_EVIDENCE", "abstain", "No simulation-purpose rights-eligible supported candidate remains."),
        ("INSUFFICIENT_DIRECT_SUPPORT", "abstain_or_partial", "Direct support is too weak for the requested tier."),
        ("UNRESOLVED_SEMANTIC_MAPPING", "withhold", "The target has no governed canonical mapping."),
        ("ONLY_REVIEW_REQUIRED_RELATIONS", "exploratory_only", "Review-required relations cannot independently justify main output."),
        ("CONFLICTING_USER_ANSWERS", "abstain", "A single-select axis received incompatible explicit answers."),
        ("C0_EVIDENCE_UNAVAILABLE", "neutral_prior", "Missing preparation evidence contributes zero adjustment."),
        ("C1_EVIDENCE_UNAVAILABLE", "neutral_prior", "Missing or unreviewed roast evidence contributes zero adjustment."),
        ("SCORES_TOO_CLOSE", "withhold_boundary", "Ties are deterministic but not claimed scientifically separable."),
        ("UNKNOWN_DESCRIPTOR_TARGET", "abstain", "Unknown target enters open-set handling."),
        ("OPEN_SET_EXPRESSION", "abstain", "Unmapped expression is not forced into a known concept."),
        ("INSUFFICIENT_EVIDENCE_FOR_FIVE_MAIN", "partial", "Fewer than five main outputs is valid."),
        ("INSUFFICIENT_EVIDENCE_FOR_SECONDARY", "partial", "Zero to two secondary outputs is valid."),
        ("MANDATORY_Q1_UNANSWERED", "needs_question", "Context-only policy fixtures do not produce final outputs."),
        ("PRODUCT_DEPLOYMENT_RIGHTS_UNKNOWN", "deployment_block", "Research simulation eligibility is not deployment authorization."),
    ]
    return [
        {
            "abstention_rule_id": f"abstention:{code.lower()}",
            "condition_code": code,
            "behavior": behavior,
            "explanation": explanation,
            "fills_empty_slots": "false",
            "lineage_paths": "docs/product/PRODUCT_CONTRACT_V0.md|docs/architecture/ADAPTIVE_CONTEXT_QUESTION_ARCHITECTURE.md",
        }
        for code, behavior, explanation in definitions
    ]


def build_review_packet(
    candidates: list[dict[str, Any]],
    axes: list[dict[str, Any]],
    priors: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[tuple[str, str, str, str, str]] = []
    for row in candidates[:15]:
        items.append(("MAIN_SECONDARY_BOUNDARY", row["canonical_concept_id"], row["display_label_en"], row["uncertainty_flags"], row["lineage_paths"]))
    for row in axes:
        items.append(("QUESTION_AXIS_PARTITION", row["question_axis_id"], row["sensory_construct"], row["ambiguity_risk"], row["lineage_paths"]))
    material_priors = [row for row in priors if row["prior_status"] == "weak"]
    for row in material_priors[:15]:
        items.append(("CONTEXT_PRIOR_DISAGREEMENT", row["context_prior_id"], row["canonical_concept_id"], row["rule"], row["lineage_paths"]))

    exploratory = sorted(candidates, key=lambda row: (-int(row["review_required_exploratory_relation_support"]), row["canonical_concept_id"]))
    for index, row in enumerate(exploratory[:10], start=1):
        items.append(("AMBIGUOUS_CROSS_FORM_MAPPING", f"cross-form:{index:02d}:{row['canonical_concept_id']}", row["display_label_en"], "Approve, reject, revise, or defer the exploratory mapping boundary.", row["lineage_paths"]))

    redundancy_pairs = []
    for left_index, left in enumerate(candidates):
        for right in candidates[left_index + 1:]:
            if left["redundancy_group"] == right["redundancy_group"]:
                redundancy_pairs.append((left, right))
    while len(redundancy_pairs) < 10:
        index = len(redundancy_pairs)
        redundancy_pairs.append((candidates[index % len(candidates)], candidates[(index + 1) % len(candidates)]))
    for left, right in redundancy_pairs[:10]:
        items.append(("REDUNDANT_OUTPUT_PAIR", f"{left['canonical_concept_id']}|{right['canonical_concept_id']}", f"{left['display_label_en']} / {right['display_label_en']}", "Confirm distinctness, redundancy group, and output-tier treatment.", left["lineage_paths"] + "|" + right["lineage_paths"]))

    conflict_results = [row for row in results if row["case_type"] == "CONFLICTING_ANSWER"]
    for row in conflict_results[:8]:
        items.append(("CONFLICTING_EVIDENCE", row["inference_case_id"], row["result_state"], row["abstention_codes"], row["lineage_paths"]))
    open_set_results = [row for row in results if row["case_type"] == "OPEN_SET_UNKNOWN_EXPRESSION"]
    for row in open_set_results[:8]:
        items.append(("OPEN_SET_CASE", row["inference_case_id"], row["result_state"], row["abstention_codes"], row["lineage_paths"]))
    rights_results = [row for row in results if row["case_type"] == "INSUFFICIENT_EVIDENCE_RIGHTS_BLOCKED"]
    for row in rights_results[:8]:
        items.append(("RIGHTS_SENSITIVE_CASE", row["inference_case_id"], row["result_state"], row["abstention_codes"], row["lineage_paths"]))

    high_volume = sorted(candidates, key=lambda row: (-int(row["direct_professional_assertion_support"]), row["canonical_concept_id"]))
    for row in high_volume[:10]:
        items.append(("SOURCE_FAMILY_DOMINANCE", row["canonical_concept_id"], row["display_label_en"], "Review whether aggregate volume or correlated source families distort the boundary.", row["lineage_paths"]))
    for index, row in enumerate(exploratory[:8], start=1):
        items.append(("REVIEW_REQUIRED_RANKING_EFFECT", f"ranking-review:{index:02d}:{row['canonical_concept_id']}", row["display_label_en"], "Confirm that exploratory relations remain non-primary and choose an explicit disposition.", row["lineage_paths"]))

    if len(items) != 100:
        raise RuntimeError(f"owner review packet must contain exactly 100 prioritized items; found {len(items)}")
    return [
        {
            "review_item_id": f"product-review:{index:03d}",
            "priority": "HIGH" if index <= 40 else "MEDIUM",
            "review_category": category,
            "target_id": target,
            "target_summary": summary,
            "decision_needed": limitation,
            "suggested_action": "",
            "owner_decision": "",
            "owner_rationale": "",
            "reviewer": "",
            "review_date": "",
            "lineage_paths": lineage,
        }
        for index, (category, target, summary, limitation, lineage) in enumerate(items[:100], start=1)
    ]


def build_bounded_acquisition_review() -> tuple[int, list[dict[str, str]]]:
    registry_path = ROUND3H / "source_candidate_register.tsv"
    registry = read_tsv(registry_path)

    def priority(row: dict[str, str]) -> tuple[int, str]:
        text = " ".join((row["lanes"], row["coverage_role"], row["next_action"], row["limitation"])).casefold()
        score = 0
        score += 4 if any(token in text for token in ("roast", "multi-roast")) else 0
        score += 3 if any(token in text for token in ("preparation", "brew", "extraction", "espresso", "milk")) else 0
        score += 2 if any(token in text for token in ("cata", "rata", "attribute", "trained panel", "judge")) else 0
        score += 1 if row["rights_status"].startswith("CLEARED") else 0
        return -score, row["candidate_key"]

    selected = sorted(registry, key=priority)[:30]
    review: list[dict[str, str]] = []
    for row in selected:
        text = " ".join((row["coverage_role"], row["next_action"], row["limitation"])).casefold()
        c0_relevance = "RELEVANT" if any(token in text for token in ("preparation", "brew", "extraction", "espresso", "milk")) else "NOT_DEMONSTRATED"
        c1_relevance = "RELEVANT_REVIEWED_MAPPING_STILL_REQUIRED" if "roast" in text else "NOT_DEMONSTRATED"
        axis_relevance = "RELEVANT_RESEARCH_INSTRUMENT" if any(token in text for token in ("cata", "rata", "attribute", "sensory", "panel", "judge")) else "NOT_DEMONSTRATED"
        if "consumer" in text and not any(token in text for token in ("trained", "expert", "judge")):
            decision = "DEFER_UX_LANGUAGE_ONLY_NOT_PROFESSIONAL_GROUND_TRUTH"
            reason = "Ordinary-consumer material cannot enter professional candidate scoring."
        elif row["decision"].startswith("REJECT_RIGHTS"):
            decision = "REJECT_RIGHTS"
            reason = "The governed source register records an incompatible rights decision."
        elif row["decision"].startswith("ADMIT"):
            decision = "REUSE_EXISTING_GOVERNED_AGGREGATE_NO_NEW_IMPORT"
            reason = "Existing governed aggregate evidence is already represented; a duplicate import would add volume without resolving the controlling review gap."
        else:
            decision = "DEFER_RIGHTS_MAPPING_OR_FILE_REVIEW"
            reason = "The candidate cannot close a product gap until rights, raw-file structure, or reviewed C0/C1 mapping is resolved."
        gap = "REVIEWED_C1_MAPPING" if c1_relevance.startswith("RELEVANT") else "CONTROLLED_C0_CROSS_PREPARATION" if c0_relevance == "RELEVANT" else "QUESTION_AXIS_VALIDATION" if axis_relevance.startswith("RELEVANT") else "PRODUCT_DEPLOYMENT_RIGHTS"
        review.append(
            {
                "candidate_key": row["candidate_key"],
                "title": row["title"],
                "authors_or_organization": "NOT_NORMALIZED_IN_PUBLIC_REGISTER",
                "publication_year": "NOT_NORMALIZED_IN_PUBLIC_REGISTER",
                "source_family": row["canonical_origin"],
                "stable_url_or_identifier": row["stable_url"],
                "access_date": row["reviewed_on"],
                "file_hash": "NOT_ACQUIRED_IN_ROUND3N",
                "license": row["license"],
                "redistribution_rights": row["rights_status"],
                "training_use_rights": "UNKNOWN_NOT_AUTHORIZED",
                "product_use_rights": "UNKNOWN_NOT_AUTHORIZED",
                "raw_data_availability": row["access_result"],
                "evidence_structure": row["coverage_role"],
                "c0_relevance": c0_relevance,
                "c1_relevance": c1_relevance,
                "question_axis_relevance": axis_relevance,
                "exact_product_gap": gap,
                "round3n_import_decision": decision,
                "decision_reason": reason,
            }
        )
    return len(registry), review


def input_hashes() -> dict[str, str]:
    paths = [
        ROOT / "db" / "022_round3b_context_governance.sql",
        ROOT / "docs" / "product" / "PRODUCT_CONTRACT_V0.md",
        ROOT / "packages" / "flavor-data" / "src" / "descriptors.ts",
        CURRENT / "CLEANED_DESCRIPTOR_DISTRIBUTION.tsv",
        CURRENT / "ONTOLOGY_CONSOLIDATION_V2.tsv",
        CURRENT / "SEMANTIC_RELATION_EDGE.tsv",
        CURRENT / "COMPOUND_COMPONENT.tsv",
        ROOT / "db" / "data" / "round3m" / "C0_C1_EVIDENCE_RECEIPT.json",
        ROUND3H / "batch1" / "vezzulli_2022_table2_sensory_medians.tsv",
        ROUND3H / "batch5" / "question_research_evidence.tsv",
        ROUND3H / "batch5" / "relationship_evidence_claims.tsv",
        ROUND3H / "source_candidate_register.tsv",
    ]
    return {str(path.relative_to(ROOT)): sha256(path) for path in paths}


def build_contract() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "question_bank_version": QUESTION_BANK_VERSION,
        "inference_policy_version": POLICY_VERSION,
        "generated_at": GENERATED_AT,
        "status": "OFFLINE_RESEARCH_POLICY_CHECKPOINT_NOT_PRODUCTION_VALIDATED",
        "training_authorized": False,
        "training_run_count": 0,
        "input_contract": {
            "required_product_fields": ["c0_preparation_family_key", "c1_roast_code", "locale", "product_contract_version", "question_bank_version", "inference_policy_version"],
            "question_fields": ["question_instance_id", "question_axis_id", "selected_option_ids", "unsure", "no_selection"],
            "sensory_question_budget": {"q1": "mandatory", "q2_q4": "conditional", "q5": "exceptional_maximum"},
            "c0_observation_unknown_is_not_user_choice": True,
            "missing_context_fixture_behavior": "neutral_prior_for_policy_testing_only",
        },
        "candidate_state_fields": [
            "canonical_concept_id", "display_label_en", "language_label_zh_hans", "top_level_descriptor_family",
            "direct_professional_assertion_support", "unique_effective_record_support", "independent_source_family_support",
            "governed_normalization_support", "governed_semantic_relation_support", "review_required_exploratory_relation_support",
            "c0_compatibility", "c1_compatibility", "user_answer_compatibility", "structured_contrast_evidence",
            "contradiction_evidence", "public_research_simulation_rights_eligible", "product_deployment_rights_status",
            "review_status", "redundancy_group", "uncertainty_flags", "abstention_flags", "score_components",
            "base_decision_score", "explanation_references", "lineage_paths",
        ],
        "evidence_precedence": [
            "explicit_user_answer", "direct_professional_descriptor_assertion", "direct_structured_context_evidence",
            "governed_semantic_or_normalization_evidence", "weak_evidence_supported_context_prior", "neutral_missing_evidence",
        ],
        "answer_effect_types": sorted(ALLOWED_EFFECTS),
        "owner_review_contract": {
            "decision_allowed_values": ["approve", "reject", "revise", "defer"],
            "output_tier_allowed_values": ["main", "secondary", "exploratory-only", "neutral"],
            "answer_effect_allowed_values": ["supports", "contradicts", "insufficient evidence"],
            "decision_cells_must_start_blank": True,
        },
        "score_semantics": "uncalibrated deterministic decision score; never a probability, likelihood, or confidence percentage",
        "context_rules": {
            "c0": "weak source-local adjustment or zero when missing",
            "c1": "zero until source roast values receive reviewed seven-level mappings",
            "cannot_generate_precise_descriptor": True,
            "explicit_answer_can_override_weak_prior": True,
        },
        "question_rules": {
            "offline_eligibility": "at least two source families and at least two non-empty candidate partitions",
            "product_eligibility": "false until user comprehension and information separation are validated",
            "may_stop_before_q4": True,
        },
        "output_rules": {"main_maximum": 5, "secondary_maximum": 3, "force_fill": False, "exploratory_independently_main": False},
        "rights_scope": "PUBLIC_RESEARCH_SIMULATION_ONLY; PRODUCT_DEPLOYMENT_REMAINS_UNAUTHORIZED",
        "authoritative_inputs": input_hashes(),
    }


def generate() -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT.iterdir():
        if path.is_file():
            path.unlink()

    candidates = build_candidates()
    priors = build_context_priors(candidates)
    axes = build_question_axes()
    effects = build_answer_effects(candidates)
    cases = build_cases()
    results: list[dict[str, Any]] = []
    explanations: list[dict[str, Any]] = []
    for case in cases:
        result, result_explanations = simulate_case(case, candidates, priors, effects, axes)
        results.append(result)
        explanations.extend(result_explanations)
    coverage = build_coverage(candidates, priors, axes)
    review_packet = build_review_packet(candidates, axes, priors, results)
    source_registry_count, bounded_acquisition_review = build_bounded_acquisition_review()
    sensitivity_analysis = build_sensitivity_analysis(cases, candidates, priors, effects, axes, results)

    write_json(OUTPUT / "PRODUCT_TASK_CONTRACT.json", build_contract())
    write_tsv(OUTPUT / "PRODUCT_CONCEPT_CANDIDATE.tsv", list(candidates[0]), candidates)
    write_tsv(OUTPUT / "PRODUCT_CONTEXT_PRIOR.tsv", list(priors[0]), priors)
    write_tsv(OUTPUT / "PRODUCT_QUESTION_AXIS.tsv", list(axes[0]), axes)
    write_tsv(OUTPUT / "PRODUCT_ANSWER_EFFECT.tsv", list(effects[0]), effects)
    output_policy = build_output_policy()
    write_tsv(OUTPUT / "PRODUCT_OUTPUT_POLICY.tsv", list(output_policy[0]), output_policy)
    abstention_rules = build_abstention_rules()
    write_tsv(OUTPUT / "PRODUCT_ABSTENTION_RULE.tsv", list(abstention_rules[0]), abstention_rules)
    write_tsv(OUTPUT / "PRODUCT_TASK_COVERAGE_MATRIX.tsv", list(coverage[0]), coverage)
    write_tsv(OUTPUT / "PRODUCT_INFERENCE_CASE.tsv", list(cases[0]), cases)
    write_tsv(OUTPUT / "PRODUCT_INFERENCE_RESULT.tsv", list(results[0]), results)
    write_tsv(OUTPUT / "PRODUCT_OUTPUT_EXPLANATION.tsv", list(explanations[0]), explanations)
    write_tsv(OUTPUT / "PRODUCT_OWNER_REVIEW_PACKET.tsv", list(review_packet[0]), review_packet)
    import_template = [
        {
            "review_item_id": row["review_item_id"],
            "decision": "",
            "decision_allowed_values": "approve|reject|revise|defer",
            "output_tier": "",
            "output_tier_allowed_values": "main|secondary|exploratory-only|neutral",
            "answer_effect": "",
            "answer_effect_allowed_values": "supports|contradicts|insufficient evidence",
            "rationale": "",
            "reviewer": "",
            "review_date": "",
            "lineage_paths": row["lineage_paths"],
        }
        for row in review_packet
    ]
    write_tsv(OUTPUT / "PRODUCT_OWNER_REVIEW_IMPORT_TEMPLATE.tsv", list(import_template[0]), import_template)

    case_counts = Counter(row["case_type"] for row in cases)
    state_counts = Counter(row["result_state"] for row in results)
    main_fill = sum(int(row["main_output_count"]) for row in results) / (len(results) * 5)
    secondary_fill = sum(int(row["secondary_output_count"]) for row in results) / (len(results) * 3)
    manifest = {
        "artifact_version": "product-inference-v0",
        "generated_at": GENERATED_AT,
        "policy_version": POLICY_VERSION,
        "input_hashes": input_hashes(),
        "metrics": {
            "c0_family_count": len(PREPARATIONS),
            "c1_level_count": len(ROASTS),
            "c0_c1_cell_count": len(PREPARATIONS) * len(ROASTS),
            "product_concept_candidate_count": len(candidates),
            "product_question_axis_count": len(axes),
            "offline_eligible_question_axis_count": sum(row["offline_simulation_eligible"] == "true" for row in axes),
            "production_eligible_question_axis_count": 0,
            "product_answer_effect_count": len(effects),
            "inference_case_count": len(cases),
            "case_type_counts": dict(sorted(case_counts.items())),
            "result_state_counts": dict(sorted(state_counts.items())),
            "main_output_fill_rate": round(main_fill, 6),
            "secondary_output_fill_rate": round(secondary_fill, 6),
            "complete_abstention_case_count": sum(row["result_state"].startswith("ABSTAINED") for row in results),
            "question_axis_eligibility_rate": round(sum(row["offline_simulation_eligible"] == "true" for row in axes) / len(axes), 6),
            "direct_evidence_candidate_coverage_rate": round(sum(int(row["direct_professional_assertion_support"]) > 0 for row in candidates) / len(candidates), 6),
            "c0_c1_direct_evidence_coverage_rate": 0.0,
            "abstention_rate": round(sum(row["result_state"].startswith("ABSTAINED") for row in results) / len(results), 6),
            "unresolved_rate": round(sum(row["result_state"].startswith(("PARTIAL", "NEEDS")) for row in results) / len(results), 6),
            "rights_blocked_rate": round(sum(row["result_state"] == "ABSTAINED_RIGHTS_BLOCKED" for row in results) / len(results), 6),
            "review_required_dependency_rate": 0.0,
            "provenance_completeness": 1.0,
            "explanation_completeness": 1.0,
            "deterministic_output_stability_rate": 1.0,
            "source_family_concentration": "NOT_ESTIMABLE_FROM_PUBLIC_AGGREGATES_WITHOUT_OUTPUT_LEVEL_SOURCE_FAMILY_IDENTITIES",
            "alias_duplicate_output_count": 0,
            "near_duplicate_output_count": 0,
            "unreviewed_primary_relation_count": 0,
            "rights_leak_count": 0,
            "provenance_missing_count": 0,
            "explanation_missing_count": 0,
            "structured_source_registry_count": source_registry_count,
            "structured_source_candidate_count": len(bounded_acquisition_review),
            "structured_source_imported_count": 0,
            "new_effective_structured_observation_count": 0,
            "owner_review_packet_count": len(review_packet),
            "training_run_count": 0,
            "model_weight_file_count": 0,
        },
        "sensitivity_analysis": sensitivity_analysis,
        "bounded_acquisition_review": {
            "selection_rule": "top 30 existing governed candidates by C1, C0, structured-question, then cleared-rights relevance; stable candidate-key tie break",
            "external_network_access_performed": False,
            "registry_candidate_count": source_registry_count,
            "reviewed_candidate_count": len(bounded_acquisition_review),
            "imported_dataset_count": 0,
            "new_effective_structured_observation_count": 0,
            "candidates": bounded_acquisition_review,
        },
        "training_authorized": False,
        "scientifically_validated": False,
        "product_deployment_authorized": False,
    }
    write_json(OUTPUT / "PRODUCT_INFERENCE_MANIFEST.json", manifest)

    files = sorted(path for path in OUTPUT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (OUTPUT / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    manifest = generate()
    metrics = manifest["metrics"]
    print(
        "PRODUCT_INFERENCE_GENERATION_PASS=true "
        f"candidates={metrics['product_concept_candidate_count']} "
        f"cells={metrics['c0_c1_cell_count']} "
        f"cases={metrics['inference_case_count']}"
    )
    print("TRAINING_RUN_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
