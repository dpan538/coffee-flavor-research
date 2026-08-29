#!/usr/bin/env python3
"""Generate the deterministic Round 4A audit and research data package.

This generator is intentionally read-only with respect to migrations and live
database state. It reconciles frozen/public artifacts already governed by the
repository. Empty eligible manifests are evidence-bearing outcomes, not errors.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "db" / "data" / "round4a"
PRIMARY_START = 1996
PRIMARY_END = 2025
SUPPLEMENT_YEAR = 2026


# Scope starts are conservative project archive boundaries. They are not claims
# about legal continuity, and the basis is retained in every expectation row.
SERIES_STARTS = {
    "wcc_wbc": (2000, "EARLIEST_OFFICIAL_RANKING_IN_ACQUIRED_WCC_ARCHIVE"),
    "wcc_wbrc": (2011, "KNOWN_SERIES_START_REQUIRES_EDITION_LEVEL_COMPLETION"),
    "wcc_wlac": (2005, "EARLIEST_OFFICIAL_RANKING_IN_ACQUIRED_WCC_ARCHIVE"),
    "wcc_wcigs": (2005, "KNOWN_SERIES_START_REQUIRES_EDITION_LEVEL_COMPLETION"),
    "wcc_wctc": (2005, "KNOWN_SERIES_START_REQUIRES_EDITION_LEVEL_COMPLETION"),
    "wcc_wcrc": (2013, "KNOWN_SERIES_START_REQUIRES_EDITION_LEVEL_COMPLETION"),
    "wcc_cic": (2011, "KNOWN_SERIES_START_REQUIRES_EDITION_LEVEL_COMPLETION"),
    "coe": (1999, "EARLIEST_OFFICIAL_EDITION_IN_RECONCILED_CENSUS"),
    "best_of_panama": (1996, "THIRTY_YEAR_PROJECT_SCOPE_START"),
    "golden_bean_americas": (2015, "PROVISIONAL_SERIES_SCOPE_START"),
    "golden_bean_australasia": (2005, "PROVISIONAL_SERIES_SCOPE_START"),
    "golden_bean_world_series": (2022, "PROVISIONAL_SERIES_SCOPE_START"),
    "iiac_ict": (2006, "PROVISIONAL_SERIES_SCOPE_START"),
    "global_coffee_awards": (2024, "PROVISIONAL_SERIES_SCOPE_START"),
    "taste_of_harvest": (2000, "PROVISIONAL_SERIES_SCOPE_START"),
    "scaj_jhdc": (2012, "EARLIEST_YEAR_IN_VERIFIED_RESULT_ARCHIVE_RANGE"),
    "scaj_jbrc": (2014, "EARLIEST_YEAR_IN_VERIFIED_RESULT_ARCHIVE_RANGE"),
    "scaj_jcrc": (2012, "EARLIEST_YEAR_IN_VERIFIED_RESULT_ARCHIVE_RANGE"),
    "scaj_jsc": (2003, "EARLIEST_YEAR_IN_VERIFIED_RESULT_ARCHIVE_RANGE"),
    "scaj_wsc": (2009, "PROVISIONAL_SERIES_SCOPE_START"),
    "royal_adelaide_coffee_show": (2014, "PROVISIONAL_SERIES_SCOPE_START"),
    "melbourne_royal_aica": (2013, "PROVISIONAL_SERIES_SCOPE_START"),
    "avpa_coffees_roasted_at_origin": (2015, "PROVISIONAL_SERIES_SCOPE_START"),
}

TERMINAL_STATUSES = {
    "ACQUIRED_DESCRIPTOR_BEARING",
    "ACQUIRED_SCORE_ONLY",
    "ACQUIRED_RANKING_ONLY",
    "ACQUIRED_METADATA_ONLY",
    "ACQUIRED_PROTOCOL_ONLY",
    "NOT_PUBLISHED",
    "NOT_FOUND",
    "ACCESS_BLOCKED",
    "SOURCE_LOST",
    "SERIES_NOT_HELD",
    "CURRENT_YEAR_INCOMPLETE",
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(name: str, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: scalar(row.get(field, "")) for field in fields})


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def scalar(value: Any) -> Any:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return "|".join(str(item) for item in value)
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_rows(path: Path) -> int | None:
    if path.suffix != ".tsv":
        return None
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def classify_series_from_text(text: str, census_lookup: dict[str, str]) -> str | None:
    for key, series in census_lookup.items():
        if key and key in text:
            return series
    aliases = {
        "wbc": "wcc_wbc",
        "wbrc": "wcc_wbrc",
        "wlac": "wcc_wlac",
        "wcigs": "wcc_wcigs",
        "wctc": "wcc_wctc",
        "wcrc": "wcc_wcrc",
        "cic": "wcc_cic",
        "golden-bean-americas": "golden_bean_americas",
        "golden_bean_americas": "golden_bean_americas",
        "golden-bean-australasia": "golden_bean_australasia",
        "golden_bean_australasia": "golden_bean_australasia",
        "golden-bean-world": "golden_bean_world_series",
        "best-of-panama": "best_of_panama",
        "bop-": "best_of_panama",
        "coe": "coe",
        "avpa": "avpa_coffees_roasted_at_origin",
    }
    lowered = text.lower()
    for token, series in aliases.items():
        if token in lowered:
            return series
    return None


def archive_rows(series: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    universe = read_tsv(ROOT / "db/data/round3l/SOURCE_UNIVERSE.tsv")
    attempts = read_tsv(ROOT / "db/data/round3l/public/SOURCE_ATTEMPTS_PUBLIC.tsv")
    census_lookup = {row["census_item_key"]: row["series_key"] for row in universe if row["series_key"]}
    acquired: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    blocked: set[tuple[str, int]] = set()

    for attempt in attempts:
        # Only identity/locator fields may contribute an edition year. The
        # attempt timestamp and continuation cursor are operational metadata;
        # treating either as edition evidence would inflate archive coverage.
        text = " ".join(
            attempt.get(field, "")
            for field in (
                "attempt_key",
                "census_item_key",
                "lane_key",
                "canonical_url",
                "final_url",
            )
        )
        series_key = classify_series_from_text(text, census_lookup)
        if not series_key:
            continue
        years = {int(year) for year in re.findall(r"\b(?:19|20)\d{2}\b", text)}
        years = {year for year in years if PRIMARY_START <= year <= SUPPLEMENT_YEAR}
        for year in years:
            outcome = attempt.get("outcome", "")
            if outcome in {"COMPLETED", "PARTIAL", "NO_RECORD_PAYLOAD"}:
                acquired[(series_key, year)].append(attempt)
            elif outcome:
                blocked.add((series_key, year))

    # The row-boundary-governed Round 3M descriptor ledger establishes only
    # these professional descriptor-bearing edition years.
    descriptor_years = {("coe", 2008), ("coe", 2017), ("coe", 2025)}
    names = {row["series_key"]: row["series_name"] for row in series}
    expectation: list[dict[str, Any]] = []
    completeness: list[dict[str, Any]] = []

    for series_key, (raw_start, start_basis) in sorted(SERIES_STARTS.items()):
        start = max(raw_start, PRIMARY_START)
        for year in range(start, SUPPLEMENT_YEAR + 1):
            in_primary = year <= PRIMARY_END
            if year == SUPPLEMENT_YEAR:
                status = "CURRENT_YEAR_INCOMPLETE"
                evidence = "Round 4A treats 2026 as a separately labelled current-year supplement."
            elif (series_key, year) in descriptor_years:
                status = "ACQUIRED_DESCRIPTOR_BEARING"
                evidence = "Round 3M governed descriptor assertion ledger contains bounded coffee-record observations."
            elif (series_key, year) in acquired:
                if series_key.startswith("wcc_") or series_key.startswith("scaj_"):
                    status = "ACQUIRED_RANKING_ONLY"
                elif series_key in {"best_of_panama", "golden_bean_americas", "golden_bean_australasia"}:
                    status = "ACQUIRED_RANKING_ONLY"
                else:
                    status = "ACQUIRED_METADATA_ONLY"
                evidence = f"{len(acquired[(series_key, year)])} public acquisition attempt(s) retained in Round 3L."
            elif (series_key, year) in blocked:
                status = "ACCESS_BLOCKED"
                evidence = "Round 3L acquisition attempt did not yield a lawful accessible payload."
            else:
                status = "NOT_FOUND"
                evidence = "No acquired edition payload is present in the reconciled repository artifacts."
            row = {
                "expectation_key": f"archive:{series_key}:{year}",
                "series_key": series_key,
                "series_name": names.get(series_key, series_key),
                "year": year,
                "expected_start_year": start,
                "start_basis": start_basis,
                "primary_denominator": in_primary,
                "data_role": "LONGITUDINAL_ARCHIVE_ROW",
                "terminal_status": status,
                "status_evidence": evidence,
                "archive_rows_count_as_model_labels": False,
            }
            expectation.append(row)
            completeness.append(row.copy())

    assert all(row["terminal_status"] in TERMINAL_STATUSES for row in completeness)
    return expectation, completeness


def pair_outputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    events = read_tsv(ROOT / "db/data/round3m/COASSERTION_EVENT.tsv")
    assertions = {
        row["descriptor_assertion_id"]: row
        for row in read_tsv(ROOT / "db/data/round3m/DESCRIPTOR_ASSERTION_LEDGER.tsv")
    }
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for event in events:
        pair = tuple(sorted((event["left_atomic_source_text_sha256"], event["right_atomic_source_text_sha256"])))
        grouped[pair].append(event)

    edges: list[dict[str, Any]] = []
    adjacency: dict[str, set[str]] = defaultdict(set)
    for (left, right), rows in sorted(grouped.items()):
        record_ids = {row["effective_record_id"] for row in rows}
        years: set[str] = set()
        source_families: set[str] = set()
        for row in rows:
            assertion = assertions[row["left_descriptor_assertion_id"]]
            route = assertion["source_route_id"]
            match = re.search(r"(20\d{2}|19\d{2})", route)
            if match:
                years.add(match.group(1))
            source_families.add("coe")
        edge_id = "professional-pair:" + hashlib.sha256(f"{left}|{right}".encode()).hexdigest()[:24]
        edges.append(
            {
                "edge_id": edge_id,
                "graph_layer": "G_professional",
                "edge_type": "PROFESSIONAL_COASSERTION_EDGE",
                "left_descriptor_hash": left,
                "right_descriptor_hash": right,
                "raw_pair_support": len(rows),
                "distinct_effective_record_support": len(record_ids),
                "distinct_source_family_support": len(source_families),
                "distinct_year_support": len(years),
                "context_specific_support": "CUPPING_PREPARATION_UNRESOLVED",
                "source_family": sorted(source_families),
                "edition_year": sorted(years),
                "preparation_scope": "PROFESSIONAL_CUPPING_PREPARATION_UNRESOLVED",
                "roast_scope": "UNKNOWN_NO_INFERENCE",
                "publication_layer": "PRIMARY_JURY_DESCRIPTION",
                "evidence_tier": "P2",
                "rights_regime": "REFERENCE_ONLY",
                "review_state": "PROVISIONAL_MACHINE_CLASSIFIED",
                "normalized_candidate_edge_eligible": False,
                "limitation": "Hash-bound source atoms are not yet human-normalized descriptor targets.",
            }
        )
        adjacency[left].add(right)
        adjacency[right].add(left)

    support_counts = Counter(edge["distinct_effective_record_support"] for edge in edges)
    support_distribution = [
        {
            "distinct_effective_record_support": support,
            "unique_pair_count": count,
            "metric_status": "REFERENCE_ONLY_NOT_MODEL_ELIGIBLE",
        }
        for support, count in sorted(support_counts.items())
    ]

    seen: set[str] = set()
    components: list[dict[str, Any]] = []
    for node in sorted(adjacency):
        if node in seen:
            continue
        queue = deque([node])
        component: set[str] = set()
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            seen.add(current)
            queue.extend(adjacency[current] - component)
        edge_count = sum(1 for edge in edges if edge["left_descriptor_hash"] in component and edge["right_descriptor_hash"] in component)
        components.append(
            {
                "component_id": f"professional-component-{len(components) + 1:03d}",
                "graph_layer": "G_professional",
                "node_count": len(component),
                "edge_count": edge_count,
                "descriptor_hashes": sorted(component),
                "candidate_level_usable": False,
                "limitation": "Source-text hashes cannot be presented as canonical descriptor identities.",
            }
        )
    return edges, support_distribution, components


def write_regime_and_health(expected_count: int) -> None:
    regimes = [
        ("REFERENCE_ONLY", "Display, audit, source-frequency statistics, and candidate generation without gradient updates.", False),
        ("PROJECT_EXPERIMENT_ALLOWED", "Task-specific fitting only with complete rights, row/label provenance, project review, and grouped splits.", True),
        ("FIRST_PARTY_BEHAVIORAL_ALLOWED", "Consented pseudonymous behavioral fitting with withdrawal and participant grouping.", True),
        ("DEPLOYMENT_ALLOWED", "Deployment fitting only with commercial/model rights, privacy controls, model card, monitoring, and rollback.", True),
        ("PROHIBITED", "No model fitting, redistribution, or automated promotion.", False),
    ]
    write_tsv(
        "DATA_USE_REGIME.tsv",
        ["regime", "allowed_use", "empirical_model_fitting_possible", "automatic_widening_allowed"],
        [
            {
                "regime": name,
                "allowed_use": use,
                "empirical_model_fitting_possible": possible,
                "automatic_widening_allowed": False,
            }
            for name, use, possible in regimes
        ],
    )

    datasets = [
        ("LONGITUDINAL_ARCHIVE", 26531, 26531, "mixed publication metadata/ranking/descriptor", 11, "UNKNOWN", "REFERENCE_ONLY", "PROVISIONAL_SOURCE_AUDIT"),
        ("SOURCE_LOCAL_SENSORY", 4344, 230, "incompatible RATA/CATA/intensity/hedonic/source-local", 9, "0.7334254143", "REFERENCE_ONLY", "SOURCE_GOVERNED"),
        ("GOVERNED_NORMALIZED_LANGUAGE", 2996, 2996, "normalized expression", 3, "UNKNOWN", "REFERENCE_ONLY", "HISTORICAL_FROZEN"),
        ("CONTEMPORARY_LANGUAGE", 3289, 3289, "language document", 3, "0.96868349", "REFERENCE_ONLY", "SOURCE_GOVERNED"),
        ("ROUND3M_PROFESSIONAL_ASSERTION", 140, 8, "provisional professional descriptor assertion", 1, "1.0", "REFERENCE_ONLY", "PROVISIONAL_MACHINE_CLASSIFIED"),
        ("PROFESSIONAL_PAIR_EVENT", 508, 5, "hash-bound co-assertion event", 1, "1.0", "REFERENCE_ONLY", "PROVISIONAL_MACHINE_CLASSIFIED"),
        ("PROJECT_REVIEWED_EXPERIMENT", 0, 0, "PROJECT_REVIEWED_PROVISIONAL", 0, "NOT_APPLICABLE", "PROJECT_EXPERIMENT_ALLOWED", "EMPTY"),
        ("FIRST_PARTY_BEHAVIORAL", 0, 0, "consented relevance event", 0, "NOT_APPLICABLE", "FIRST_PARTY_BEHAVIORAL_ALLOWED", "EMPTY"),
    ]
    tasks = [
        "professional descriptor normalization",
        "source-local descriptor classification",
        "consumer-language mapping",
        "context-conditioned candidate retrieval",
        "5+3 candidate ranking",
        "co-assertion estimation",
        "adaptive question selection",
        "stopping policy",
    ]
    compatibility: list[dict[str, Any]] = []
    for dataset, rows, units, label, families, share, rights, review in datasets:
        for task in tasks:
            reference_ok = (
                task in {"consumer-language mapping", "context-conditioned candidate retrieval"}
                and dataset in {"GOVERNED_NORMALIZED_LANGUAGE", "CONTEMPORARY_LANGUAGE"}
            ) or (task == "co-assertion estimation" and dataset == "PROFESSIONAL_PAIR_EVENT")
            compatibility.append(
                {
                    "dataset": dataset,
                    "task": task,
                    "unit_of_observation": "source-defined; see label_type",
                    "row_count": rows,
                    "effective_independent_unit_count": units,
                    "label_type": label,
                    "label_source": dataset,
                    "source_families": families,
                    "largest_family_share": share,
                    "languages": "en|zh-Hans" if "LANGUAGE" in dataset else "en|unknown",
                    "preparation_coverage": "SOURCE_LOCAL_OR_UNRESOLVED",
                    "roast_coverage": "PARTIAL_NO_DESCRIPTOR_INFERENCE",
                    "missingness": "TASK_SPECIFIC_AUDIT_REQUIRED",
                    "duplicate_rate": "NOT_POOLABLE_ACROSS_INCOMPATIBLE_SURFACES",
                    "rights_regime": rights,
                    "review_regime": review,
                    "split_feasibility": "FAIL_GROUPED_HOLDOUT" if families < 3 else "REFERENCE_ONLY_NOT_FITTING_ELIGIBLE",
                    "eligible": False,
                    "reason": "REFERENCE_SUPPORT_ONLY" if reference_ok else "NO_TASK_SPECIFIC_RIGHTS_REVIEW_AND_GROUPED_LABEL_MANIFEST",
                }
            )
    fields = list(compatibility[0])
    write_tsv("DATASET_COMPATIBILITY_MATRIX.tsv", fields, compatibility)

    health = []
    for task in tasks:
        health.append(
            {
                "task": task,
                "raw_rows": 140 if "professional" in task else 0,
                "deduplicated_rows": 137 if "professional" in task else 0,
                "effective_records": 8 if task in {"professional descriptor normalization", "5+3 candidate ranking", "co-assertion estimation"} else 0,
                "independent_source_families": 1 if task in {"professional descriptor normalization", "5+3 candidate ranking", "co-assertion estimation"} else 0,
                "distinct_participants": 0,
                "distinct_coffee_identities": 8 if "professional" in task or task in {"5+3 candidate ranking", "co-assertion estimation"} else 0,
                "distinct_labels": 0,
                "minimum_support_per_label": 0,
                "median_support_per_label": 0,
                "tail_labels_lt_5": "NOT_COMPUTABLE_UNNORMALIZED",
                "tail_labels_lt_10": "NOT_COMPUTABLE_UNNORMALIZED",
                "tail_labels_lt_20": "NOT_COMPUTABLE_UNNORMALIZED",
                "multi_target_records": 5 if task in {"5+3 candidate ranking", "co-assertion estimation"} else 0,
                "ambiguous_unresolved_cases": 67 if "professional" in task or task in {"5+3 candidate ranking", "co-assertion estimation"} else 0,
                "largest_source_family_share": 1 if task in {"professional descriptor normalization", "5+3 candidate ranking", "co-assertion estimation"} else "NOT_APPLICABLE",
                "grouped_train_validation_test_feasibility": "FAIL",
                "eligible": False,
                "reason": "ZERO_MODEL_ELIGIBLE_LABELS_AND_INSUFFICIENT_INDEPENDENT_FAMILIES",
            }
        )
    write_tsv("TASK_DATA_HEALTH.tsv", list(health[0]), health)
    write_tsv(
        "LABEL_SUPPORT_DISTRIBUTION.tsv",
        ["task", "label_state", "label_count", "support_bin", "eligible", "reason"],
        [{"task": task, "label_state": "NO_ELIGIBLE_NORMALIZED_LABELS", "label_count": 0, "support_bin": "0", "eligible": False, "reason": "STRICT_REVIEW_AND_RIGHTS_GATES_FAIL"} for task in tasks],
    )
    write_tsv(
        "SOURCE_FAMILY_CONCENTRATION.tsv",
        ["dataset", "source_family_count", "largest_family_share", "grouped_holdout_feasible", "status"],
        [
            {"dataset": dataset, "source_family_count": families, "largest_family_share": share, "grouped_holdout_feasible": False, "status": "REFERENCE_ONLY_OR_INSUFFICIENT"}
            for dataset, _, _, _, families, share, _, _ in datasets
        ],
    )
    write_tsv(
        "SPLIT_FEASIBILITY.tsv",
        ["task", "coffee_identity_grouping", "participant_grouping", "source_family_grouping", "year_holdout", "feasible", "reason"],
        [{"task": task, "coffee_identity_grouping": True, "participant_grouping": "REQUIRED_WHERE_APPLICABLE", "source_family_grouping": True, "year_holdout": True, "feasible": False, "reason": "NO_ELIGIBLE_TASK_MANIFEST"} for task in tasks],
    )
    protocol = [
        ("SOURCE_TEXT_IDENTITY", "VERIFY", "Source text and bounded locator match."),
        ("FIELD_SEGMENTATION", "VERIFY|CORRECT|ABSTAIN", "Atomic field segmentation only."),
        ("SPELLING_PLURAL", "NORMALIZE|ABSTAIN", "Obvious spelling or plural normalization."),
        ("CANONICAL_CANDIDATE", "MAP|MULTI_TARGET|UNRESOLVED|ABSTAIN", "Provisional project mapping; not expert truth."),
        ("PUBLICATION_LAYER", "PRIMARY|MIRROR|REPEAT|UNRESOLVED", "De-inflation disposition."),
        ("TASK_RELEVANCE", "IN_SCOPE|OUT_OF_SCOPE|ABSTAIN", "Task relevance only."),
    ]
    write_tsv(
        "PROJECT_REVIEW_PROTOCOL.tsv",
        ["scope", "allowed_decisions", "boundary"],
        [{"scope": scope, "allowed_decisions": decision, "boundary": boundary} for scope, decision, boundary in protocol],
    )


def write_manifests(expected_count: int, terminal_count: int, edges: list[dict[str, Any]]) -> None:
    event_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "coffee-flavor-atlas:first-party-behavioral-event:v1",
        "title": "Consent-gated local-first candidate interaction event",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "pseudonymous_participant_id", "pseudonymous_session_id", "consent_version",
            "model_use_consent", "C0", "C1", "question_id", "question_version",
            "question_order", "answer", "answer_latency_ms", "candidate_set_version",
            "candidate_rank", "candidate_selected", "candidate_rejected",
            "none_of_these_selected", "confidence", "completion_state", "withdrawal_state"
        ],
        "properties": {
            "pseudonymous_participant_id": {"type": "string", "minLength": 1},
            "pseudonymous_session_id": {"type": "string", "minLength": 1},
            "consent_version": {"type": "string", "minLength": 1},
            "model_use_consent": {"type": "boolean"},
            "C0": {"type": "string"}, "C1": {"type": "integer", "minimum": 1, "maximum": 7},
            "question_id": {"type": "string"}, "question_version": {"type": "string"},
            "question_order": {"type": "integer", "minimum": 1, "maximum": 5},
            "answer": {"type": ["string", "null"]}, "answer_latency_ms": {"type": "integer", "minimum": 0},
            "candidate_set_version": {"type": "string"}, "candidate_rank": {"type": ["integer", "null"], "minimum": 1, "maximum": 8},
            "candidate_selected": {"type": "boolean"}, "candidate_rejected": {"type": "boolean"},
            "none_of_these_selected": {"type": "boolean"}, "confidence": {"type": ["string", "null"]},
            "completion_state": {"enum": ["STARTED", "COMPLETED", "ABANDONED"]},
            "withdrawal_state": {"enum": ["ACTIVE", "WITHDRAWN", "DELETED"]}
        },
        "collection_default": "NO_REMOTE_COLLECTION",
        "storage_default": "LOCAL_ONLY_OR_NO_OP",
        "first_party_behavioral_ranking_phase": "POST_INITIAL_MODEL",
    }
    write_json("FIRST_PARTY_BEHAVIORAL_SCHEMA.json", event_schema)
    write_json(
        "PROJECT_EXPERIMENT_MANIFEST.json",
        {
            "manifest_version": "round4a-project-experiment-v1",
            "eligible": False,
            "row_count": 0,
            "review_regime": "PROJECT_REVIEWED_PROVISIONAL",
            "rights_regime": "PROJECT_EXPERIMENT_ALLOWED",
            "exclusion_reason": "No rows satisfy task-specific rights, review, provenance, and grouped-split gates.",
            "professional_ground_truth": False,
        },
    )
    write_json(
        "PROFESSIONAL_REFERENCE_MANIFEST.json",
        {
            "manifest_version": "round4a-professional-reference-v1",
            "data_role": "REFERENCE_ONLY",
            "descriptor_assertion_count": 140,
            "effective_record_count": 8,
            "professional_pair_event_count": 508,
            "unique_pair_count": len(edges),
            "professional_reviewed_count": 0,
            "model_eligible_count": 0,
            "empirical_fitting_allowed": False,
        },
    )
    write_json(
        "TRAINING_FEASIBILITY_DECISION.json",
        {
            "decision": "CONTINUE_TASK_TARGETED_DATA_REVIEW",
            "empirical_classical_model_run": False,
            "deep_learning_entry_ready": False,
            "deterministic_baseline_allowed": True,
            "professional_gate": {"eligible_strict_assertions": 0, "required": 2000, "pass": False},
            "ranking_gate": {"eligible_strict_assertions": 0, "required": 5000, "pass": False},
            "first_party_required_for_initial_professional_model": False,
            "first_party_required_for_later_personalization": True,
            "next_required_data_cell": "RIGHTS_CLEARED_PROJECT_OR_PROFESSIONALLY_REVIEWED_NORMALIZATION_TARGETS_WITH_GROUPED_SOURCE_FAMILY_AND_YEAR_KEYS",
        },
    )
    write_json(
        "ROUND4A_MANIFEST.json",
        {
            "schema": "coffee-flavor-round4a-manifest-v1",
            "source_sha": "21d04f50952ac30ee13010ee26bae8a224ea9f71",
            "archive_primary_start_year": PRIMARY_START,
            "archive_primary_end_year": PRIMARY_END,
            "expected_series_year_count": expected_count,
            "terminally_classified_series_year_count": terminal_count,
            "archive_rows_counted_as_model_labels": False,
            "migrations_000_059_modified": False,
            "first_party_behavioral_ranking_phase": "POST_INITIAL_MODEL",
            "first_party_data_required_for_initial_professional_model": False,
            "first_party_data_required_for_later_personalization": True,
            "model_training_run": False,
            "deep_learning_run": False,
            "training_corpus_frozen": False,
        },
    )


def write_candidate_data() -> None:
    fixtures = [
        ("floral_citrus_tea", "filter", 3, "floral|citrus|tea", "floral|citrus|tea|honey|sweet", "stone-fruit|cocoa|spice", "SUPPORTED_SINGLE_CLUSTER"),
        ("fruit_chocolate_spice", "espresso", 5, "fruit|chocolate|spice", "dark-chocolate|red-berry|baking-spice|caramel|roasted", "citrus|tea|honey", "SUPPORTED_MULTI_CLUSTER"),
        ("rare_direct_answer", "immersion", 4, "tropical-fruit", "tropical-fruit|citrus|honey|tea|floral", "stone-fruit|sweet|spice", "DIRECT_Q_OVERRIDE"),
        ("insufficient_evidence", "unknown", 4, "", "", "", "ABSTAIN_INSTEAD_OF_FILLER"),
    ]
    write_tsv(
        "CANDIDATE_SET_FIXTURE.tsv",
        ["fixture_id", "C0", "C1", "q_answers", "expected_primary", "expected_secondary", "expected_behavior"],
        [{"fixture_id": a, "C0": b, "C1": c, "q_answers": d, "expected_primary": e, "expected_secondary": f, "expected_behavior": g} for a, b, c, d, e, f, g in fixtures],
    )
    ablations = [
        ("A", "global descriptor frequency", "PLANNED_REFERENCE"),
        ("B", "C0/C1 context-only prior", "DETERMINISTIC_FIXTURE_AVAILABLE"),
        ("C", "deterministic C0/C1 + Q mapping", "IMPLEMENTED"),
        ("D", "independent-label ranker", "BLOCKED_NO_ELIGIBLE_TRAINING_MANIFEST"),
        ("E", "D + professional coherence", "BLOCKED_NO_ELIGIBLE_NORMALIZED_GRAPH"),
        ("F", "E + ontology connectivity", "BLOCKED_EMPIRICAL_EVALUATION"),
        ("G", "F + auxiliary community-language bridge", "BLOCKED_ZERO_COMMUNITY_EDGES"),
        ("H", "embedding or fine-tuned reranker", "PROHIBITED_ROUND4A"),
    ]
    write_tsv("COHERENCE_ABLATION_PLAN.tsv", ["stage", "system", "status"], [{"stage": a, "system": b, "status": c} for a, b, c in ablations])
    metrics = ["Reference Coverage@8", "nDCG@8", "Reference Supported Candidate Rate@8", "Unsupported Candidate Rate@8", "Isolated Outlier Rate@8", "Candidate-Set Coherence@8", "Redundancy Rate@8", "Worst Held-Out Family nDCG@8"]
    write_tsv(
        "COHERENCE_METRIC_STATUS.tsv",
        ["metric", "value", "status", "split_scope", "reason"],
        [{"metric": metric, "value": "NOT_EVALUATED", "status": "BLOCKED_LABEL_HEALTH", "split_scope": "coffee_identity|edition_year|source_family", "reason": "No model-eligible normalized professional reference holdout exists."} for metric in metrics],
    )
    write_tsv(
        "COMMUNITY_LANGUAGE_EDGE.tsv",
        ["edge_id", "graph_layer", "edge_type", "left_term", "right_term", "source_family", "effective_record_count", "assertion_count", "year_count", "preparation_scope", "roast_scope", "evidence_tier", "rights_regime", "review_state", "counts_as_professional_pair"],
        [],
    )


def write_descriptor_corpus_health(edges: list[dict[str, Any]]) -> None:
    write_tsv(
        "DESCRIPTOR_CORPUS_HEALTH.tsv",
        [
            "descriptor_bearing_effective_record_count",
            "strict_descriptor_assertion_count",
            "strict_p2_descriptor_assertion_count",
            "model_eligible_strict_descriptor_assertion_count",
            "multi_descriptor_record_count",
            "multi_target_record_count",
            "professional_pair_event_count",
            "unique_professional_pair_count",
            "pair_support_distribution",
            "descriptor_degree_distribution",
            "isolated_descriptor_count",
            "source_family_pair_coverage",
            "year_pair_coverage",
            "preparation_specific_pair_coverage",
            "roast_specific_pair_coverage",
            "status",
        ],
        [
            {
                "descriptor_bearing_effective_record_count": 8,
                "strict_descriptor_assertion_count": 140,
                "strict_p2_descriptor_assertion_count": 73,
                "model_eligible_strict_descriptor_assertion_count": 0,
                "multi_descriptor_record_count": 5,
                "multi_target_record_count": 5,
                "professional_pair_event_count": 508,
                "unique_professional_pair_count": len(edges),
                "pair_support_distribution": "support_1:504|support_2:2",
                "descriptor_degree_distribution": "NOT_COMPUTABLE_UNNORMALIZED_HASH_IDENTITIES",
                "isolated_descriptor_count": "NOT_COMPUTABLE_UNNORMALIZED_HASH_IDENTITIES",
                "source_family_pair_coverage": 1,
                "year_pair_coverage": 1,
                "preparation_specific_pair_coverage": 0,
                "roast_specific_pair_coverage": 0,
                "status": "REFERENCE_ONLY_NOT_CANDIDATE_LEVEL_MODEL_READY",
            }
        ],
    )


def main() -> None:
    series = read_tsv(ROOT / "db/data/round3k/COMPETITION_SERIES.tsv")
    expectation, completeness = archive_rows(series)
    archive_fields = [
        "expectation_key", "series_key", "series_name", "year", "expected_start_year",
        "start_basis", "primary_denominator", "data_role", "terminal_status",
        "status_evidence", "archive_rows_count_as_model_labels",
    ]
    write_tsv("LONGITUDINAL_ARCHIVE_EXPECTATION.tsv", archive_fields, expectation)
    write_tsv("LONGITUDINAL_ARCHIVE_COMPLETENESS.tsv", archive_fields, completeness)
    primary = [row for row in completeness if row["primary_denominator"]]
    terminal = [row for row in primary if row["terminal_status"] in TERMINAL_STATUSES]

    edges, distribution, components = pair_outputs()
    edge_fields = list(edges[0])
    write_tsv("DESCRIPTOR_PAIR_EDGE.tsv", edge_fields, edges)
    write_tsv("DESCRIPTOR_PAIR_SUPPORT_DISTRIBUTION.tsv", list(distribution[0]), distribution)
    write_tsv("DESCRIPTOR_GRAPH_COMPONENTS.tsv", list(components[0]), components)
    write_descriptor_corpus_health(edges)
    write_regime_and_health(len(primary))
    write_candidate_data()
    write_manifests(len(primary), len(terminal), edges)

    files = sorted(path for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in files), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
