#!/usr/bin/env python3
"""Build deterministic, public-safe Round 3M baseline artifacts.

This script consumes only the public Round 3L aggregate checkpoint and census.
It never reads or republishes row-level result, score, OCR, participant, or
descriptor text.  The Round 3 descriptor-census machine bundle is deliberately
not reconstructed from the PDF: when those exact files are unavailable, the
script emits an explicit blocker and leaves direct-audit row counts unimported.
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
ROUND3L = ROOT / "db" / "data" / "round3l"
PUBLIC3L = ROUND3L / "public"
OUTPUT = ROOT / "db" / "data" / "round3m"

CURRENT_GATE_VERSION = "round3m-descriptor-gates-v2"
NORMALIZATION_CHALLENGE_UNIVERSE = (
    "HUMAN_REVIEWED_NORMALIZATION_CHALLENGE_UNIVERSE"
)
NORMALIZATION_CHALLENGE_NOTE = (
    "Leaf final all-ACCEPT qualified-human ambiguous, contradictory, or "
    "unresolved normalization-label decisions with exact Round 3M/Round 3K "
    "source binding; ABSTAIN, REVISE, REJECT, CONFLICT, and generic assertion "
    "MARK_* receipts do not count."
)

EXPECTED_RESEARCH_ARTIFACTS = (
    "OPEN_DESCRIPTOR_SOURCE_CENSUS.tsv",
    "DESCRIPTOR_YIELD_AUDIT.tsv",
    "DESCRIPTOR_COUNT_RECEIPT.json",
    "DESCRIPTOR_PROVENANCE_MATRIX.tsv",
    "OPEN_DESCRIPTOR_CEILING.md",
    "DESCRIPTOR_TRAINING_GATES.md",
    "SOURCE_PRIORITY_BY_DESCRIPTOR_YIELD.tsv",
    "LOW_YIELD_AND_FALSE_SCALE_REGISTER.tsv",
    "CODEX_RESUMPTION_DECISION.md",
)

EXPECTED_BASELINE = {
    "census_items": 480,
    "source_route_or_family_keys": 131,
    "editions": 267,
    "artifacts": 848,
    "parsed_rows": 26_531,
    "staged_rows": 26_515,
    "canonical_rows": 20_994,
    "staged_core_candidates": 6_754,
    "staged_assertions": 11_801,
    "staged_gate_descriptors": 376,
    "reviewed_descriptors": 0,
    "model_eligible_descriptors": 0,
}

# This is a conservative publication-origin grouping, not an assertion that
# every national organizer, edition, or host is statistically independent.
# In particular, all WCC routes remain one family until independence evidence
# is reviewed.  Multiple CoE country/edition routes remain one ACE/CoE family.
SERIES_FAMILY = {
    "avpa_coffees_roasted_at_origin": "family.avpa",
    "best_of_panama": "family.scap_best_of_panama",
    "coe": "family.ace_cup_of_excellence",
    "global_coffee_awards": "family.global_coffee_awards",
    "golden_bean_americas": "family.golden_bean",
    "golden_bean_australasia": "family.golden_bean",
    "golden_bean_world_series": "family.golden_bean",
    "iiac_ict": "family.iiac",
    "melbourne_royal_aica": "family.melbourne_royal",
    "royal_adelaide_coffee_show": "family.royal_adelaide",
    "scaj_jbrc": "family.scaj",
    "scaj_jcrc": "family.scaj",
    "scaj_jhdc": "family.scaj",
    "scaj_jsc": "family.scaj",
    "scaj_wsc": "family.scaj",
    "taste_of_harvest": "family.afca_taste_of_harvest",
    "wcc_cic": "family.world_coffee_events",
    "wcc_competition_body_registry": "family.world_coffee_events",
    "wcc_wbc": "family.world_coffee_events",
    "wcc_wbrc": "family.world_coffee_events",
    "wcc_wcigs": "family.world_coffee_events",
    "wcc_wcrc": "family.world_coffee_events",
    "wcc_wctc": "family.world_coffee_events",
    "wcc_wlac": "family.world_coffee_events",
}

FAMILY_ORGANIZER = {
    "family.avpa": "organizer.avpa",
    "family.scap_best_of_panama": "organizer.scap",
    "family.ace_cup_of_excellence": "organizer.ace",
    "family.global_coffee_awards": "organizer.global_coffee_awards",
    "family.golden_bean": "organizer.golden_bean",
    "family.iiac": "organizer.iiac",
    "family.melbourne_royal": "organizer.melbourne_royal",
    "family.royal_adelaide": "organizer.royal_adelaide",
    "family.scaj": "organizer.scaj",
    "family.afca_taste_of_harvest": "organizer.afca",
    "family.world_coffee_events": "organizer.world_coffee_events",
}

ZERO_BUDGET_SERIES = {
    "avpa_coffees_roasted_at_origin",
    "best_of_panama",
    "global_coffee_awards",
    "golden_bean_americas",
    "golden_bean_australasia",
    "golden_bean_world_series",
    "melbourne_royal_aica",
    "royal_adelaide_coffee_show",
    "scaj_jbrc",
    "scaj_jcrc",
    "scaj_jhdc",
    "scaj_jsc",
    "scaj_wsc",
    "taste_of_harvest",
}

CENSUS_COLUMNS = (
    "census_item_key", "item_kind", "parent_key", "series_key",
    "source_family_key", "edition_label", "year", "country_or_community",
    "category_or_round", "official_url", "discovery_basis",
    "source_snapshot_sha256", "corpus_state", "acquisition_state",
    "rights_state", "attempt_status", "note",
)

ATTEMPT_COLUMNS = (
    "attempt_key", "census_item_key", "lane_key", "attempt_sequence",
    "attempted_at", "acquisition_method", "outcome", "canonical_url",
    "final_url", "http_status", "source_snapshot_sha256",
    "artifact_byte_count", "parsed_row_count", "normalized_record_count",
    "descriptor_assertion_count", "external_action_type", "next_cursor",
)

ARTIFACT_COLUMNS = (
    "artifact_receipt_key", "lane_key", "census_item_key", "canonical_url",
    "retrieval_url", "http_status", "media_type", "sha256", "byte_count",
    "inventory_basis",
)


class ContractError(ValueError):
    pass


def read_tsv(path: Path, columns: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != tuple(columns):
            raise ContractError(f"header mismatch: {path}")
        rows = list(reader)
    if any(None in row for row in rows):
        raise ContractError(f"extra TSV field: {path}")
    return rows


def write_tsv(
    path: Path, columns: Sequence[str], rows: Iterable[Mapping[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=columns,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        writer.writerows(rows)


def integer(row: Mapping[str, str], key: str) -> int:
    return int(row[key] or "0")


def schema_signature(row: Mapping[str, str]) -> str:
    key = row["census_item_key"]
    if "honduras_2017" in key:
        return "schema.coe.honduras-2017.explicit-top-jury.v1"
    if "colombia_south_2008" in key:
        return "schema.coe.colombia-south-2008.frequency-coded.v1"
    if "mexico_2023" in key or "peru_2025" in key:
        return "schema.coe.generic-sensory-field.v1"
    if row["item_kind"] == "SCORESHEET":
        return "schema.protocol-or-blank-form.v1"
    if row["item_kind"] == "RESULT_ARCHIVE":
        return "schema.result-metadata.v1"
    return "schema.unresolved.v1"


def disposition(row: Mapping[str, str], descriptor_candidates: int) -> str:
    key = row["census_item_key"]
    series = row["series_key"]
    if "honduras_2017" in key:
        return "PRIORITY_DESCRIPTOR_ROUTE"
    if "colombia_south_2008" in key:
        return "PROVENANCE_PILOT_ONLY"
    if "mexico_2023" in key or "peru_2025" in key:
        return "PROVENANCE_PILOT_ONLY"
    if descriptor_candidates > 0:
        return "REVIEW_EXISTING_CANDIDATES"
    if series == "iiac_ict":
        return "PARTNERSHIP_ONLY"
    if series in ZERO_BUDGET_SERIES:
        return "EXCLUDED_LOW_YIELD"
    if series.startswith("wcc_"):
        return (
            "PROVENANCE_PILOT_ONLY"
            if row["item_kind"] == "SCORESHEET"
            else "EXCLUDED_LOW_YIELD"
        )
    return "UNRESOLVED_ROUTE"


GATE_CONTRACT = (
    (
        "GATE_500_EVALUATION",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "500", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT", ">=", "75", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Distinct conservative normalized forms."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "3", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Routes and editions sharing an origin remain one family."),
            ("SOURCE_AND_LABEL_PROVENANCE_COMPLETENESS", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA_AND_REVIEW", "Every reviewed assertion has both complete source provenance and receipt-backed label provenance."),
        ),
    ),
    (
        "GATE_2000_EXPERIMENTAL_NORMALIZATION",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "2000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT", ">=", "500", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Descriptor-bearing effective records."),
            ("REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT", ">=", "100", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Conservative normalized forms."),
            ("MINIMUM_RECORDS_PER_OUTPUT_LABEL", ">=", "20", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Minimum effective-record support per output label."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "3", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Independent families."),
            ("REVIEWED_LARGEST_FAMILY_SHARE", "<=", "0.70", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Largest-family concentration."),
            ("REVIEWED_AMBIGUOUS_OR_UNRESOLVED_CHALLENGE_COUNT", ">=", "100", NORMALIZATION_CHALLENGE_UNIVERSE, "REVIEW", NORMALIZATION_CHALLENGE_NOTE),
            ("MODEL_RESEARCH_RIGHTS_RATE", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "RIGHTS", "All counted assertions have affirmative model-research rights."),
        ),
    ),
    (
        "GATE_5000_EXPERIMENTAL_RANKING",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "5000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT", ">=", "1000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Descriptor-bearing effective records."),
            ("REVIEWED_MULTI_TARGET_RECORD_COUNT", ">=", "500", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Receipt-backed multi-target records."),
            ("SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT", ">=", "2500", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Governed within-record pair events."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "4", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Independent families."),
            ("REVIEWED_LARGEST_FAMILY_SHARE", "<=", "0.60", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Largest-family concentration."),
            ("HELD_OUT_EDITION_YEAR_COUNT", ">=", "1", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out edition years."),
            ("MODEL_RESEARCH_RIGHTS_RATE", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "RIGHTS", "Affirmative model-research rights."),
        ),
    ),
    (
        "GATE_10000_RESEARCH_NORMALIZATION",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "10000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT", ">=", "2500", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Descriptor-bearing effective records."),
            ("REVIEWED_UNIQUE_NORMALIZED_FORM_COUNT", ">=", "200", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Conservative normalized forms."),
            ("MINIMUM_RECORDS_PER_OUTPUT_LABEL", ">=", "50", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Minimum effective-record support per output label."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "5", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Independent families."),
            ("REVIEWED_LARGEST_FAMILY_SHARE", "<=", "0.45", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Largest-family concentration."),
            ("HELD_OUT_INDEPENDENT_FAMILY_COUNT", ">=", "2", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out families."),
            ("HELD_OUT_EDITION_YEAR_COUNT", ">=", "2", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out years."),
            ("MODEL_RESEARCH_RIGHTS_RATE", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "RIGHTS", "Affirmative model-research rights."),
        ),
    ),
    (
        "GATE_15000_ASSOCIATION",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "15000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT", ">=", "3000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Descriptor-bearing effective records."),
            ("SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT", ">=", "10000", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Governed within-record pair events."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "5", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Independent families."),
            ("RECORD_BOUNDARIES_PRESERVED", "=", "true", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "No cross-record or unrelated-observation pair."),
            ("MODEL_RESEARCH_RIGHTS_RATE", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "RIGHTS", "Affirmative model-research rights."),
        ),
    ),
    (
        "GATE_20000_RESEARCH_RANKING",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "20000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT", ">=", "4000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Descriptor-bearing effective records."),
            ("REVIEWED_MULTI_TARGET_RECORD_COUNT", ">=", "2000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Receipt-backed multi-target records."),
            ("SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT", ">=", "15000", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Governed within-record pair events."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "6", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Independent families."),
            ("REVIEWED_LARGEST_FAMILY_SHARE", "<=", "0.35", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Largest-family concentration."),
            ("HELD_OUT_INDEPENDENT_FAMILY_COUNT", ">=", "2", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out families."),
            ("HELD_OUT_EDITION_YEAR_COUNT", ">=", "2", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out years."),
            ("MODEL_RESEARCH_RIGHTS_RATE", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "RIGHTS", "Affirmative model-research rights."),
        ),
    ),
    (
        "GATE_40000_DEPLOYMENT_CANDIDATE",
        (
            ("REVIEWED_P1_P2_STRICT_ASSERTION_COUNT", ">=", "40000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Actual-human reviewed P1/P2 strict assertions."),
            ("REVIEWED_DESCRIPTOR_BEARING_RECORD_COUNT", ">=", "8000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Descriptor-bearing effective records."),
            ("REVIEWED_MULTI_TARGET_RECORD_COUNT", ">=", "5000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Receipt-backed multi-target records."),
            ("SUPPORTED_WITHIN_RECORD_PAIR_EVENT_COUNT", ">=", "40000", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Governed within-record pair events."),
            ("REVIEWED_INDEPENDENT_SOURCE_FAMILY_COUNT", ">=", "8", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Independent families."),
            ("REVIEWED_LARGEST_FAMILY_SHARE", "<=", "0.25", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Largest-family concentration."),
            ("HELD_OUT_INDEPENDENT_FAMILY_COUNT", ">=", "3", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out families."),
            ("HELD_OUT_EDITION_YEAR_COUNT", ">=", "3", "MODEL_ELIGIBLE_DESCRIPTOR_UNIVERSE", "DATA", "Predeclared held-out years."),
            ("MINIMUM_RECORDS_PER_OUTPUT_LABEL", ">=", "100", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Minimum production support per output label."),
            ("SOURCE_PROVENANCE_COMPLETENESS", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "DATA", "Complete source provenance."),
            ("LABEL_PROVENANCE_COMPLETENESS", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "REVIEW", "Complete label provenance."),
            ("DEPLOYMENT_RIGHTS_RATE", "=", "1.0000", "HUMAN_REVIEWED_DESCRIPTOR_UNIVERSE", "RIGHTS", "Affirmative deployment/commercial-model rights."),
        ),
    ),
)

GATE_NULL_METRICS = {
    "MINIMUM_RECORDS_PER_OUTPUT_LABEL",
    "REVIEWED_LARGEST_FAMILY_SHARE",
    "SOURCE_PROVENANCE_COMPLETENESS",
    "LABEL_PROVENANCE_COMPLETENESS",
    "SOURCE_AND_LABEL_PROVENANCE_COMPLETENESS",
    "MODEL_RESEARCH_RIGHTS_RATE",
    "DEPLOYMENT_RIGHTS_RATE",
}


def gate_rows() -> list[dict[str, object]]:
    if len(GATE_CONTRACT) != 7 or sum(len(criteria) for _, criteria in GATE_CONTRACT) != 56:
        raise ContractError("current descriptor-gate contract must contain exactly 7 definitions and 56 criteria")
    rows: list[dict[str, object]] = []
    for gate_name, criteria in GATE_CONTRACT:
        for ordinal, criterion in enumerate(criteria, start=1):
            metric_name, operator, required_value, universe, blocker_class, note = criterion
            not_applicable = metric_name in GATE_NULL_METRICS
            observed_value = (
                "NA"
                if not_applicable
                else "false"
                if metric_name == "RECORD_BOUNDARIES_PRESERVED"
                else "0"
            )
            rows.append(
                {
                    "gate_version": CURRENT_GATE_VERSION,
                    "gate_name": gate_name,
                    "criterion_ordinal": ordinal,
                    "metric_name": metric_name,
                    "operator": operator,
                    "observed_value": observed_value,
                    "required_value": required_value,
                    "universe": universe,
                    "pass": "false",
                    "not_applicable": str(not_applicable).lower(),
                    "rights_blocker": str(blocker_class == "RIGHTS").lower(),
                    "data_blocker": str(
                        blocker_class in {"DATA", "DATA_AND_REVIEW"}
                    ).lower(),
                    "review_blocker": str(
                        blocker_class in {"REVIEW", "DATA_AND_REVIEW"}
                    ).lower(),
                    "explanatory_note": (
                        note + " Observed value is unavailable; NA never passes."
                        if not_applicable
                        else note
                    ),
                }
            )
    return rows


def main() -> None:
    census = read_tsv(ROUND3L / "SOURCE_UNIVERSE.tsv", CENSUS_COLUMNS)
    attempts = read_tsv(PUBLIC3L / "SOURCE_ATTEMPTS_PUBLIC.tsv", ATTEMPT_COLUMNS)
    artifacts = read_tsv(PUBLIC3L / "ARTIFACT_MANIFEST.tsv", ARTIFACT_COLUMNS)
    checkpoint = json.loads((PUBLIC3L / "PUBLIC_CHECKPOINT.json").read_text())

    actual = {
        "census_items": len(census),
        "source_route_or_family_keys": len({r["source_family_key"] for r in census}),
        "editions": sum(r["item_kind"] in {"COMPETITION_EDITION", "PILOT_EDITION"} for r in census),
        "artifacts": checkpoint["acquisition"]["artifact_count"],
        "parsed_rows": checkpoint["acquisition"]["parsed_rows"],
        "staged_rows": checkpoint["acquisition"]["ingested_rows"],
        "canonical_rows": checkpoint["acquisition"]["canonical_rows"],
        "staged_core_candidates": checkpoint["staging_inventory"]["staged_core_candidates"],
        "staged_assertions": checkpoint["staging_inventory"]["total_assertions"],
        "staged_gate_descriptors": checkpoint["staging_inventory"]["staged_gate_type_descriptor_assertions"],
        "reviewed_descriptors": 0,
        "model_eligible_descriptors": checkpoint["staging_inventory"]["staged_model_eligible_records"],
    }
    if actual != EXPECTED_BASELINE:
        raise ContractError(f"Round 3L baseline drift: {actual!r}")

    attempts_by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    artifacts_by_item: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in attempts:
        attempts_by_item[row["census_item_key"]].append(row)
    for row in artifacts:
        artifacts_by_item[row["census_item_key"]].append(row)

    census_rows = []
    for row in census:
        item_attempts = attempts_by_item[row["census_item_key"]]
        family = SERIES_FAMILY[row["series_key"]]
        descriptor_candidates = sum(integer(a, "descriptor_assertion_count") for a in item_attempts)
        artifact_count = len(artifacts_by_item[row["census_item_key"]])
        publication_rows = sum(integer(a, "parsed_row_count") for a in item_attempts)
        effective_candidates = sum(integer(a, "normalized_record_count") for a in item_attempts)
        census_rows.append(
            {
                "census_item_key": row["census_item_key"],
                "item_kind": row["item_kind"],
                "source_family_id": family,
                "source_route_id": "route." + row["source_family_key"],
                "organizer_id": FAMILY_ORGANIZER[family],
                "edition_id": row["census_item_key"] if "EDITION" in row["item_kind"] else "",
                "schema_signature_id": schema_signature(row),
                "publication_host": urlsplit(row["official_url"]).netloc.lower(),
                "independent_source_family_id": family,
                "independence_state": "CONSERVATIVE_PUBLICATION_ORIGIN_GROUP",
                "rights_lineage_id": "rights." + family.removeprefix("family."),
                "mirror_lineage_id": "UNRESOLVED",
                "route_disposition": disposition(row, descriptor_candidates),
                "artifact_count": artifact_count,
                "publication_row_count": publication_rows,
                "effective_record_candidate_count": effective_candidates,
                "gate_descriptor_candidate_count": descriptor_candidates,
                "reviewed_strict_count": 0,
                "reviewed_broad_count": 0,
                "p1_count": 0,
                "p2_count": 0,
                "p3_count": 0,
                "unresolved_count": descriptor_candidates,
                "rights_affirmative_model_count": 0,
                "analyst_minutes": "NA",
                "descriptor_yield_per_artifact": (
                    f"{descriptor_candidates / artifact_count:.6f}" if artifact_count else "NA"
                ),
                "descriptor_yield_per_analyst_hour": "NA",
                "corpus_universe": row["corpus_state"],
                "official_url": row["official_url"],
            }
        )

    census_columns = tuple(census_rows[0])
    write_tsv(OUTPUT / "SOURCE_CENSUS_UNIVERSE.tsv", census_columns, census_rows)

    route_rows = []
    for route_id in sorted({r["source_route_id"] for r in census_rows}):
        grouped = [r for r in census_rows if r["source_route_id"] == route_id]
        dispositions = Counter(r["route_disposition"] for r in grouped)
        chosen = sorted(dispositions, key=lambda d: (-dispositions[d], d))[0]
        route_rows.append(
            {
                "source_route_id": route_id,
                "source_family_id": grouped[0]["source_family_id"],
                "organizer_id": grouped[0]["organizer_id"],
                "independent_source_family_id": grouped[0]["independent_source_family_id"],
                "route_disposition": chosen,
                "census_item_count": len(grouped),
                "artifact_count": sum(int(r["artifact_count"]) for r in grouped),
                "publication_row_count": sum(int(r["publication_row_count"]) for r in grouped),
                "effective_record_candidate_count": sum(int(r["effective_record_candidate_count"]) for r in grouped),
                "gate_descriptor_candidate_count": sum(int(r["gate_descriptor_candidate_count"]) for r in grouped),
                "disposition_basis": "Round 3M descriptor-first stop-loss policy; edition-level exceptions remain in SOURCE_CENSUS_UNIVERSE.tsv.",
            }
        )
    write_tsv(OUTPUT / "SOURCE_ROUTE_DISPOSITION.tsv", tuple(route_rows[0]), route_rows)

    yield_rows = []
    for route in route_rows:
        artifacts_n = int(route["artifact_count"])
        descriptors_n = int(route["gate_descriptor_candidate_count"])
        yield_rows.append(
            {
                "source_route_id": route["source_route_id"],
                "source_family_id": route["source_family_id"],
                "artifact_count": artifacts_n,
                "candidate_count": descriptors_n,
                "reviewed_count": 0,
                "analyst_minutes": "NA",
                "descriptor_yield_per_artifact": f"{descriptors_n / artifacts_n:.6f}" if artifacts_n else "NA",
                "descriptor_yield_per_analyst_hour": "NA",
                "yield_scope": "ROUND3L_STAGED_CANDIDATES_NOT_HUMAN_REVIEWED",
            }
        )
    write_tsv(OUTPUT / "SOURCE_ROUTE_YIELD.tsv", tuple(yield_rows[0]), yield_rows)

    low_yield_groups = (
        ("BOP_RESULT_TABLES", "family.scap_best_of_panama", "EXCLUDED_LOW_YIELD"),
        ("GOLDEN_BEAN_PUBLIC_RESULTS", "family.golden_bean", "EXCLUDED_LOW_YIELD"),
        ("WCC_BLANK_FORMS", "family.world_coffee_events", "P0_PROTOCOL"),
        ("WCC_RANKING_METADATA", "family.world_coffee_events", "RESULT_METADATA"),
        ("SCAJ_RESULTS", "family.scaj", "EXCLUDED_LOW_YIELD"),
        ("AFCA_SCORE_TABLES", "family.afca_taste_of_harvest", "EXCLUDED_LOW_YIELD"),
        ("ROYAL_ADELAIDE_RESULTS", "family.royal_adelaide", "EXCLUDED_LOW_YIELD"),
        ("MELBOURNE_ROYAL_RESULTS", "family.melbourne_royal", "EXCLUDED_LOW_YIELD"),
        ("AVPA_PALMARES", "family.avpa", "EXCLUDED_LOW_YIELD"),
        ("IIAC_PUBLIC_MEDAL_LISTS", "family.iiac", "PARTNERSHIP_ONLY"),
        ("GLOBAL_COFFEE_AWARDS_PUBLIC_AWARD_LISTS", "family.global_coffee_awards", "EXCLUDED_LOW_YIELD"),
    )
    low_rows = []
    for route_key, family, route_disposition in low_yield_groups:
        grouped = [r for r in census_rows if r["source_family_id"] == family]
        low_rows.append(
            {
                "route_key": route_key,
                "independent_source_family_id": family,
                "disposition": route_disposition,
                "artifact_count": sum(int(r["artifact_count"]) for r in grouped),
                "publication_row_count": sum(int(r["publication_row_count"]) for r in grouped),
                "verified_descriptor_count": 0,
                "new_round3m_broad_acquisition_budget": 0,
                "reason": "Public audited surface is protocol, ranking, score, medal, award, or result metadata rather than a filled coffee-specific professional descriptor observation.",
            }
        )
    write_tsv(OUTPUT / "LOW_YIELD_EXCLUSION_REGISTER.tsv", tuple(low_rows[0]), low_rows)

    request_topics = {
        "ACE_COE": (
            "AUTHORSHIP_GENERIC_SENSORY_FIELDS", "LEGACY_FREQUENCY_COUNT_ORIGIN",
            "TOP_JURY_DERIVED_ASSERTION_STORAGE", "INTERNAL_RESEARCH_USE",
            "MODEL_RESEARCH_USE", "DEPLOYMENT_COMMERCIAL_MODEL_USE",
            "DERIVED_NORMALIZED_DATA_REDISTRIBUTION", "HISTORICAL_JURY_EXPORT_ACCESS",
        ),
        "IIAC": (
            "PRODUCT_LEVEL_PROFILE_ACCESS", "THIRTEEN_DIMENSION_VALUES",
            "RAW_JUDGE_VS_MEDIAN_RETENTION", "ARCHIVE_SIZE_AND_COVERAGE",
            "INTERNAL_RESEARCH_USE", "MODEL_RESEARCH_USE", "DEPLOYMENT_USE",
            "DERIVED_DATA_PUBLICATION",
        ),
        "WCC_AND_NATIONAL_BODIES": (
            "COMPLETED_FILLED_SCORESHEETS", "JUDGE_COMMENTS",
            "SENSORY_DESCRIPTION_FIELDS", "EFFECTIVE_RECORD_IDENTITY",
            "PREPARATION_SERVICE", "EDITION_AND_ROUND",
            "JUDGE_LEVEL_VS_CONSENSUS", "RESEARCH_AND_MODEL_RIGHTS",
        ),
        "GOLDEN_BEAN": (
            "NON_PUBLIC_FILLED_JUDGE_COMMENTS", "SENSORY_FEEDBACK",
            "COMPLETED_SCORESHEETS", "PRODUCT_LEVEL_ASSESSMENT_EXPORTS",
            "RESEARCH_AND_MODEL_RIGHTS",
        ),
        "GLOBAL_COFFEE_AWARDS": (
            "NON_PUBLIC_FILLED_JUDGE_COMMENTS", "SENSORY_FEEDBACK",
            "COMPLETED_SCORESHEETS", "PRODUCT_LEVEL_ASSESSMENT_EXPORTS",
            "RESEARCH_AND_MODEL_RIGHTS",
        ),
    }
    request_rows = []
    for organizer, topics in request_topics.items():
        for sequence, topic in enumerate(topics, start=1):
            request_rows.append(
                {
                    "request_key": f"round3m.{organizer.lower()}.{sequence:02d}",
                    "organizer": organizer,
                    "request_topic": topic,
                    "request_draft": "Please clarify the specified field provenance, retained observation level, permitted research/model purpose, and derived-data redistribution boundary.",
                    "request_status": "NOT_SENT",
                    "outbound_data_request_count": 0,
                    "contract_acceptance_count": 0,
                    "commercial_purchase_count": 0,
                }
            )
    write_tsv(OUTPUT / "ORGANIZER_REQUEST_MATRIX.tsv", tuple(request_rows[0]), request_rows)

    gates = gate_rows()
    write_tsv(OUTPUT / "DESCRIPTOR_GATE_STATUS.tsv", tuple(gates[0]), gates)

    independent_count = len(set(SERIES_FAMILY.values()))
    if independent_count != 11 or len(route_rows) != 131:
        raise ContractError("route/family separation drift")
    reconciliation = {
        "receipt_schema": "round3m-baseline-reconciliation-v1",
        "source_checkpoint_sha": "4159636afec052b96f20d3d10c6c5f2b943b4536",
        "expected": EXPECTED_BASELINE,
        "recomputed": actual,
        "exact_match": True,
        "source_route_or_family_key_count": len(route_rows),
        "independent_source_family_count": independent_count,
        "independence_semantics": "Conservative publication-origin grouping; route, edition, host, rights lineage, mirror lineage, and family are separate columns.",
        "round3l_public_regeneration": "PASS",
        "machine_readable_research_artifacts_available": False,
        "research_artifact_import_status": "BLOCKED_MISSING_MACHINE_ARTIFACTS",
        "missing_research_artifacts": list(EXPECTED_RESEARCH_ARTIFACTS),
        "report_counts_independently_reproduced": False,
        "report_counts_usage": "Methodological and expected-count receipt only; no 303-row ledger reconstructed from PDF.",
    }
    (OUTPUT / "BASELINE_RECONCILIATION.json").write_text(
        json.dumps(reconciliation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "ROUND3M_BASELINE_ARTIFACTS_PASS "
        f"census={len(census_rows)} routes={len(route_rows)} "
        f"independent_families={independent_count} gates={len(gates)}"
    )


if __name__ == "__main__":
    main()
