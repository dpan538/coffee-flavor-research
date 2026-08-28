"""Versioned schema signatures for the Round 3M live-source pilot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


ADAPTER_VERSION = "round3m.live-adapters.v1"
PARSER_VERSION = "round3m.field-parser.v1"

COE_HONDURAS_TOP_JURY = "schema.coe.honduras-2017.explicit-top-jury.v1"
COE_COLOMBIA_FREQUENCY = "schema.coe.colombia-south-2008.frequency-coded.v1"
COE_GENERIC_SENSORY = "schema.coe.generic-sensory-field.v1"
WCC_COMPLETED_SCORESHEET = "schema.wcc.completed-scoresheet.v1"


@dataclass(frozen=True)
class SchemaSignature:
    schema_signature_id: str
    source_route_id: str
    schema_version: str
    host: str
    route_pattern: str
    edition_or_period: str
    field_labels: tuple[str, ...]
    selectors: Mapping[str, str]
    publication_layer_rules: Mapping[str, str]
    field_origin_assumptions: Mapping[str, str]
    known_ambiguity: str
    positive_fixture_locator: str
    negative_fixture_locator: str
    live_positive_fixture_present: bool
    validation_status: str


SIGNATURES = {
    COE_HONDURAS_TOP_JURY: SchemaSignature(
        schema_signature_id=COE_HONDURAS_TOP_JURY,
        source_route_id="route.coe.honduras-2017.explicit-top-jury",
        schema_version="1",
        host="allianceforcoffeeexcellence.org",
        route_pattern="/farm-directory/{score-slug}/ (Honduras 2017 only)",
        edition_or_period="Honduras 2017",
        field_labels=(
            "Score from International Judges",
            "Top Jury Descriptions",
            "Aroma / Flavor",
            "Acidity",
            "Other",
            "Other Features",
            "Producer cup profile",
        ),
        selectors={
            "paired_score": "label:Score from International Judges",
            "primary_jury": "label:Top Jury Descriptions",
            "secondary_table": "table:label(Aroma / Flavor|Acidity|Other)",
            "producer_profile": "label:Producer cup profile",
        },
        publication_layer_rules={
            "Top Jury Descriptions": "PRIMARY_JURY_DESCRIPTION",
            "Aroma / Flavor|Acidity|Other": "SECONDARY_SENSORY_TABLE_WHEN_PRIMARY_PRESENT",
            "Producer cup profile": "PRODUCER_OR_FARM_PROFILE",
        },
        field_origin_assumptions={
            "Top Jury Descriptions": "P2_EXPLICIT_JURY_LABEL_PAIRED_WITH_INTERNATIONAL_JUDGE_SCORE",
            "secondary_table": "UNRESOLVED_RELATION_TO_PRIMARY_NO_DOUBLE_CREDIT",
            "producer_profile": "P3_PRODUCER_OR_FARM",
        },
        known_ambiguity="Secondary sensory table may restate or transform the primary jury description.",
        positive_fixture_locator="fixture://round3m/coe-honduras-2017-la-colmena-live-positive",
        negative_fixture_locator="fixture://round3m/coe-honduras-2017-ranking-score-negative",
        live_positive_fixture_present=True,
        validation_status="VALIDATED",
    ),
    COE_COLOMBIA_FREQUENCY: SchemaSignature(
        schema_signature_id=COE_COLOMBIA_FREQUENCY,
        source_route_id="route.coe.colombia-south-2008.frequency-coded",
        schema_version="1",
        host="allianceforcoffeeexcellence.org|farmdirectory.cupofexcellence.org",
        route_pattern=(
            "/farm-directory/{score-slug}/|"
            "/listing/2008-colombia-south-{score-slug}/"
        ),
        edition_or_period="Colombia South 2008",
        field_labels=("Aroma/Flavor", "Acidity", "Score", "Rank"),
        selectors={
            "frequency_field": "label:Aroma/Flavor|label:Acidity",
            "frequency_term": "bounded-term-followed-by-parenthetical-integer",
        },
        publication_layer_rules={
            "frequency_field": "GENERIC_ORGANIZER_SENSORY_FIELD",
            "score_or_rank": "RESULT_METADATA_ZERO_ASSERTIONS",
        },
        field_origin_assumptions={
            "frequency_field": "UNRESOLVED_P1_CANDIDATE_NOT_VERIFIED_JUDGE_COUNT"
        },
        known_ambiguity=(
            "Official mirror routes preserve the field schema, but the page does not "
            "establish whether frequencies count judges, jury responses, or panel mentions."
        ),
        positive_fixture_locator="fixture://round3m/coe-colombia-south-2008-la-esperanza-live-positive",
        negative_fixture_locator="fixture://round3m/coe-colombia-south-2008-ranking-score-negative",
        live_positive_fixture_present=True,
        validation_status="VALIDATED",
    ),
    COE_GENERIC_SENSORY: SchemaSignature(
        schema_signature_id=COE_GENERIC_SENSORY,
        source_route_id="route.coe.generic-sensory-field",
        schema_version="1",
        host="farmdirectory.cupofexcellence.org",
        route_pattern="/listing/{lot}-{slug}-{country}-{year}/",
        edition_or_period="Peru 2025 and Mexico 2023 pilot strata",
        field_labels=(
            "Overall",
            "Aroma / Flavor",
            "Acidity",
            "Mouthfeel / Other",
            "Other",
            "Producer cup profile",
            "Score",
            "Rank",
        ),
        selectors={
            "sensory_fields": "label:Overall|Aroma / Flavor|Acidity|Mouthfeel / Other|Other",
            "producer_profile": "label:Producer cup profile",
        },
        publication_layer_rules={
            "sensory_fields": "GENERIC_ORGANIZER_SENSORY_FIELD",
            "producer_profile": "PRODUCER_OR_FARM_PROFILE",
            "score_or_rank": "RESULT_METADATA_ZERO_ASSERTIONS",
        },
        field_origin_assumptions={
            "sensory_fields": "UNRESOLVED_ORIGIN_ORGANIZER_HOSTING_IS_NOT_P2",
            "producer_profile": "P3_PRODUCER_OR_FARM",
        },
        known_ambiguity="Filled organizer fields have no explicit judge, jury, or panel author on the audited pages.",
        positive_fixture_locator="fixture://round3m/coe-generic-peru-2025-la-catarata-live-positive",
        negative_fixture_locator="fixture://round3m/coe-generic-ranking-score-negative",
        live_positive_fixture_present=True,
        validation_status="SOURCE_DRIFT",
    ),
    WCC_COMPLETED_SCORESHEET: SchemaSignature(
        schema_signature_id=WCC_COMPLETED_SCORESHEET,
        source_route_id="route.wcc.completed-scoresheet",
        schema_version="1",
        host="wcc.coffee|authorized-institutional-host",
        route_pattern="authoritative completed filled official scoresheet or judge-comment artifact only",
        edition_or_period="open pilot search through 2026-08-28",
        field_labels=(
            "Judge comments",
            "Aroma / Flavor description",
            "Competitor Name",
            "Judge",
            "Taste Score",
            "Rank",
        ),
        selectors={
            "descriptor_field": "filled-label:Judge comments|Aroma / Flavor description",
            "completion_evidence": "filled-judge-and-competitor-identity-on-authoritative-artifact",
        },
        publication_layer_rules={
            "filled_authoritative_comment": "JUDGE_LEVEL_OBSERVATION",
            "blank_form": "PROTOCOL_OR_BLANK_FORM_ZERO_ASSERTIONS",
            "ranking": "RESULT_METADATA_ZERO_ASSERTIONS",
        },
        field_origin_assumptions={
            "filled_authoritative_comment": "P1_ONLY_AFTER_COMPLETION_AND_AUTHORITY_CHECK",
            "blank_form_or_ranking": "P0_OR_METADATA_NOT_AN_OBSERVATION",
        },
        known_ambiguity="No authoritative public completed filled scoresheet corpus was present in the governed audit artifacts.",
        positive_fixture_locator="",
        negative_fixture_locator="fixture://round3m/wcc-blank-form-negative",
        live_positive_fixture_present=False,
        validation_status="BLOCKED_NO_POSITIVE_FIXTURE",
    ),
}
