"""Typed, source-preserving records for the Round 3M live adapters.

The types intentionally keep a judge observation below an effective coffee
record and keep publication layers separate.  They do not contain ontology or
translation fields: adapters emit source-native review candidates only.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum


class AdapterViolation(ValueError):
    """A stable, machine-testable live-adapter contract failure."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


class DescriptorClass(str, Enum):
    STRICT_FLAVOR = "STRICT_FLAVOR"
    BROAD_SENSORY = "BROAD_SENSORY"
    NON_DESCRIPTOR = "NON_DESCRIPTOR"


class EvidenceTier(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
    P5 = "P5"
    UNRESOLVED = "UNRESOLVED"


class PublicationLayer(str, Enum):
    PRIMARY_JURY_DESCRIPTION = "PRIMARY_JURY_DESCRIPTION"
    GENERIC_ORGANIZER_SENSORY_FIELD = "GENERIC_ORGANIZER_SENSORY_FIELD"
    PRODUCER_OR_FARM_PROFILE = "PRODUCER_OR_FARM_PROFILE"
    SECONDARY_SENSORY_TABLE = "SECONDARY_SENSORY_TABLE"
    JUDGE_LEVEL_OBSERVATION = "JUDGE_LEVEL_OBSERVATION"
    RESULT_METADATA = "RESULT_METADATA"
    PROTOCOL_OR_BLANK_FORM = "PROTOCOL_OR_BLANK_FORM"


class RightsState(str, Enum):
    AFFIRMATIVE = "AFFIRMATIVE"
    PENDING = "PENDING"
    UNKNOWN = "UNKNOWN"
    PROHIBITED = "PROHIBITED"


class CountDisposition(str, Enum):
    ADMITTED = "ADMITTED"
    SECONDARY_REVIEW_ONLY = "SECONDARY_REVIEW_ONLY"


@dataclass(frozen=True)
class EffectiveRecordKey:
    """The only identity grain that can increment a professional record count."""

    competition_series: str
    edition: str
    category: str
    round_name: str
    entry_or_lot: str
    preparation_service: str

    def __post_init__(self) -> None:
        values = (
            self.competition_series,
            self.edition,
            self.category,
            self.round_name,
            self.entry_or_lot,
            self.preparation_service,
        )
        if any(not value.strip() for value in values):
            raise AdapterViolation(
                "INCOMPLETE_EFFECTIVE_RECORD",
                "series, edition, category, round, entry/lot, and explicit "
                "preparation service are required",
            )

    @property
    def effective_record_id(self) -> str:
        material = "\x1f".join(
            (
                self.competition_series,
                self.edition,
                self.category,
                self.round_name,
                self.entry_or_lot,
                self.preparation_service,
            )
        )
        return "effective:" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


@dataclass(frozen=True)
class SourceField:
    label: str
    value: str
    selector_or_locator: str
    judge_observation_id: str = ""


@dataclass(frozen=True)
class SourceRecord:
    schema_signature_id: str
    source_artifact_id: str
    source_route_id: str
    independent_source_family_id: str
    source_url: str
    source_file_sha256: str
    source_retrieved_at: str
    effective_record: EffectiveRecordKey
    fields: tuple[SourceField, ...]
    rights_state: RightsState
    source_language: str = "en"
    publication_host: str = ""
    publication_instance_id: str = ""
    roast_code: str | None = None
    preparation_family_code: str | None = None
    completed_filled_authoritative_scoresheet: bool = False
    authoritative_completion_evidence_locator: str = ""

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.source_file_sha256):
            raise AdapterViolation(
                "INVALID_SOURCE_SHA256", "source_file_sha256 must be lowercase SHA-256"
            )
        if not self.source_url.startswith("https://"):
            raise AdapterViolation("INVALID_SOURCE_URL", "source_url must use HTTPS")
        if not self.source_artifact_id or not self.source_route_id:
            raise AdapterViolation(
                "MISSING_SOURCE_IDENTITY", "artifact and route identifiers are required"
            )


@dataclass(frozen=True)
class DescriptorCandidate:
    descriptor_assertion_id: str
    effective_record_id: str
    source_artifact_id: str
    source_route_id: str
    schema_signature_id: str
    publication_layer: PublicationLayer
    source_field_label: str
    source_selector_or_locator: str
    source_page_or_record_locator: str
    raw_field_text: str
    atomic_source_text: str
    source_language: str
    descriptor_class: DescriptorClass
    source_native_lexical_form: str
    normalized_candidate_form: str
    evidence_tier: EvidenceTier
    evidence_origin_type: str
    origin_decision_basis: str
    origin_evidence_locator: str
    review_state: str
    rights_state: RightsState
    count_disposition: CountDisposition
    judge_observation_id: str
    frequency_value: int | None
    source_retrieved_at: str
    source_file_sha256: str
    parser_version: str
    adapter_version: str
    roast_code: str | None
    preparation_family_code: str | None
    model_eligible: bool = False


@dataclass(frozen=True)
class SuppressedRepeat:
    descriptor_assertion_id: str
    retained_assertion_id: str
    reason: str


@dataclass(frozen=True)
class DeinflationResult:
    extracted_candidates: tuple[DescriptorCandidate, ...]
    assertion_level: tuple[DescriptorCandidate, ...]
    record_unique: tuple[DescriptorCandidate, ...]
    suppressed: tuple[SuppressedRepeat, ...]


@dataclass(frozen=True)
class CoassertionEvent:
    effective_record_id: str
    left_normalized_form: str
    right_normalized_form: str
    evidence_scope: str = "P1_P2_WITHIN_EFFECTIVE_RECORD"
