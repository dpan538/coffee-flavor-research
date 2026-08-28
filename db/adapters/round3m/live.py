"""Deterministic source-specific extraction and anti-inflation for Round 3M."""

from __future__ import annotations

import hashlib
import itertools
import re
import unicodedata
from collections import defaultdict
from dataclasses import replace
from typing import Iterable, Sequence

from .model import (
    AdapterViolation,
    CoassertionEvent,
    CountDisposition,
    DeinflationResult,
    DescriptorCandidate,
    DescriptorClass,
    EvidenceTier,
    PublicationLayer,
    RightsState,
    SourceField,
    SourceRecord,
    SuppressedRepeat,
)
from .signatures import (
    ADAPTER_VERSION,
    COE_COLOMBIA_FREQUENCY,
    COE_GENERIC_SENSORY,
    COE_HONDURAS_TOP_JURY,
    PARSER_VERSION,
    SIGNATURES,
    WCC_COMPLETED_SCORESHEET,
)


_SPACE = re.compile(r"\s+")
_DELIMITER = re.compile(r"\s*[,;]\s*")
_FREQUENCY_TERM = re.compile(r"([^,;:]+?)\s*\((\d+)\)")
_COMPOUND_SECTION = re.compile(
    r"(?i)(?:^|\s)(Aroma\s*/?\s*Flavor|Flavor\s*/?\s*Aroma|Aroma|Flavor|"
    r"Acidity|Other\s+Features|Other|Mouthfeel)\s*(?:-|:)\s*"
)

_METADATA_LABELS = {
    "score",
    "score from international judges",
    "taste score",
    "rank",
    "ranking",
    "placement",
    "award",
    "competitor name",
    "judge",
}
_GENERIC_SENSORY_LABELS = {
    "overall",
    "aroma / flavor",
    "aroma/flavor",
    "acidity",
    "mouthfeel / other",
    "mouthfeel/other",
    "other",
}
_BROAD_FIELD_LABELS = {
    "overall",
    "acidity",
    "mouthfeel / other",
    "mouthfeel/other",
    "other",
    "other features",
    "mouthfeel",
}
_BROAD_TERMS = {
    "acidity",
    "aftertaste",
    "balance",
    "balanced",
    "body",
    "bright",
    "clean",
    "cleanliness",
    "complex",
    "crisp",
    "finish",
    "intense",
    "juicy",
    "lingering",
    "mouthfeel",
    "smooth",
    "sweet",
    "sweetness",
    "syrupy",
    "velvety",
}
_STRICT_IN_BROAD_FIELDS = {
    "cream caramel",
    "floral",
    "mandarin orange",
    "passion fruit",
    "red apple",
}


def _label(value: str) -> str:
    return _SPACE.sub(" ", value.strip()).casefold()


def _normalize_candidate(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = _SPACE.sub(" ", value.strip(" .,:;\t\n")).casefold()
    return value


def _split_atomic(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in _DELIMITER.split(value) if part.strip())


def _classify(value: str, *, default_broad: bool) -> DescriptorClass:
    normalized = _normalize_candidate(value)
    if not normalized:
        return DescriptorClass.NON_DESCRIPTOR
    if normalized in _STRICT_IN_BROAD_FIELDS:
        return DescriptorClass.STRICT_FLAVOR
    if default_broad or normalized in _BROAD_TERMS:
        return DescriptorClass.BROAD_SENSORY
    return DescriptorClass.STRICT_FLAVOR


def _candidate(
    record: SourceRecord,
    field: SourceField,
    atomic_text: str,
    *,
    descriptor_class: DescriptorClass,
    evidence_tier: EvidenceTier,
    evidence_origin_type: str,
    origin_decision_basis: str,
    publication_layer: PublicationLayer,
    count_disposition: CountDisposition = CountDisposition.ADMITTED,
    frequency_value: int | None = None,
    occurrence_index: int = 0,
) -> DescriptorCandidate:
    normalized = _normalize_candidate(atomic_text)
    material = "\x1f".join(
        (
            record.source_artifact_id,
            record.effective_record.effective_record_id,
            publication_layer.value,
            field.selector_or_locator,
            field.judge_observation_id,
            normalized,
            str(frequency_value or ""),
            str(occurrence_index),
        )
    )
    assertion_id = "assertion:" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    # AUTO_EXTRACTED candidates are never model eligible.  Rights approval alone
    # would still require human/expert review downstream.
    return DescriptorCandidate(
        descriptor_assertion_id=assertion_id,
        effective_record_id=record.effective_record.effective_record_id,
        source_artifact_id=record.source_artifact_id,
        source_route_id=record.source_route_id,
        schema_signature_id=record.schema_signature_id,
        publication_layer=publication_layer,
        source_field_label=field.label,
        source_selector_or_locator=field.selector_or_locator,
        source_page_or_record_locator=record.source_url,
        raw_field_text=field.value,
        atomic_source_text=atomic_text,
        source_language=record.source_language,
        descriptor_class=descriptor_class,
        source_native_lexical_form=atomic_text,
        normalized_candidate_form=normalized,
        evidence_tier=evidence_tier,
        evidence_origin_type=evidence_origin_type,
        origin_decision_basis=origin_decision_basis,
        origin_evidence_locator=field.selector_or_locator,
        review_state="AUTO_EXTRACTED",
        rights_state=record.rights_state,
        count_disposition=count_disposition,
        judge_observation_id=field.judge_observation_id,
        frequency_value=frequency_value,
        source_retrieved_at=record.source_retrieved_at,
        source_file_sha256=record.source_file_sha256,
        parser_version=PARSER_VERSION,
        adapter_version=ADAPTER_VERSION,
        roast_code=record.roast_code,
        preparation_family_code=record.preparation_family_code,
        model_eligible=False,
    )


def _compound_sections(value: str) -> tuple[tuple[str, str], ...]:
    matches = list(_COMPOUND_SECTION.finditer(value))
    if not matches:
        return ()
    result: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(value)
        result.append((match.group(1), value[match.end() : end].strip()))
    return tuple(result)


def _extract_honduras_top_jury(record: SourceRecord) -> tuple[DescriptorCandidate, ...]:
    fields = {_label(field.label): field for field in record.fields}
    primary = fields.get("top jury descriptions")
    score = fields.get("score from international judges")
    candidates: list[DescriptorCandidate] = []
    if primary is not None and primary.value.strip() and score is not None and score.value.strip():
        sections = _compound_sections(primary.value)
        if not sections:
            raise AdapterViolation(
                "TOP_JURY_SECTION_STRUCTURE",
                "Top Jury Descriptions must expose a bounded sensory subfield",
            )
        for section_label, section_value in sections:
            broad = _label(section_label) in _BROAD_FIELD_LABELS
            for atomic in _split_atomic(section_value):
                candidates.append(
                    _candidate(
                        record,
                        primary,
                        atomic,
                        descriptor_class=_classify(atomic, default_broad=broad),
                        evidence_tier=EvidenceTier.P2,
                        evidence_origin_type="ORGANIZER_PUBLISHED_EXPLICIT_JURY_DESCRIPTION",
                        origin_decision_basis="EXPLICIT_TOP_JURY_LABEL_PAIRED_WITH_INTERNATIONAL_JUDGE_SCORE",
                        publication_layer=PublicationLayer.PRIMARY_JURY_DESCRIPTION,
                        occurrence_index=len(candidates),
                    )
                )

    # The generic table is preserved for review, but is never silently added to
    # the primary jury count on these pages.
    for field in record.fields:
        normalized_label = _label(field.label)
        if normalized_label in _GENERIC_SENSORY_LABELS and field.value.strip():
            for atomic in _split_atomic(field.value):
                candidates.append(
                    _candidate(
                        record,
                        field,
                        atomic,
                        descriptor_class=_classify(
                            atomic, default_broad=normalized_label in _BROAD_FIELD_LABELS
                        ),
                        evidence_tier=EvidenceTier.UNRESOLVED,
                        evidence_origin_type="SECONDARY_FIELD_ORIGIN_UNRESOLVED",
                        origin_decision_basis="PRIMARY_JURY_FIELD_PRESENT_NO_DOUBLE_CREDIT",
                        publication_layer=PublicationLayer.SECONDARY_SENSORY_TABLE,
                        count_disposition=CountDisposition.SECONDARY_REVIEW_ONLY,
                        occurrence_index=len(candidates),
                    )
                )

    producer = fields.get("producer cup profile")
    if producer is not None and producer.value.strip():
        for atomic in _split_atomic(producer.value):
            candidates.append(
                _candidate(
                    record,
                    producer,
                    atomic,
                    descriptor_class=_classify(atomic, default_broad=False),
                    evidence_tier=EvidenceTier.P3,
                    evidence_origin_type="PRODUCER_OR_FARM_DECLARED",
                    origin_decision_basis="EXPLICIT_PRODUCER_PROFILE_FIELD",
                    publication_layer=PublicationLayer.PRODUCER_OR_FARM_PROFILE,
                    occurrence_index=len(candidates),
                )
            )
    return tuple(candidates)


def _frequency_sections(field: SourceField) -> tuple[tuple[str, str, int], ...]:
    sections = _compound_sections(field.value)
    if not sections:
        sections = ((field.label, field.value),)
    result: list[tuple[str, str, int]] = []
    for section_label, text in sections:
        for match in _FREQUENCY_TERM.finditer(text):
            result.append((section_label, match.group(1).strip(), int(match.group(2))))
    return tuple(result)


def _extract_colombia_frequency(record: SourceRecord) -> tuple[DescriptorCandidate, ...]:
    candidates: list[DescriptorCandidate] = []
    for field in record.fields:
        normalized_label = _label(field.label)
        if normalized_label in _METADATA_LABELS:
            continue
        if normalized_label not in {"aroma / flavor", "aroma/flavor", "acidity"}:
            continue
        for section_label, atomic, frequency in _frequency_sections(field):
            broad = (
                normalized_label == "acidity"
                or _label(section_label) in _BROAD_FIELD_LABELS
            )
            candidates.append(
                _candidate(
                    record,
                    field,
                    atomic,
                    descriptor_class=_classify(atomic, default_broad=broad),
                    evidence_tier=EvidenceTier.UNRESOLVED,
                    evidence_origin_type="FREQUENCY_CODED_P1_CANDIDATE_ORIGIN_UNRESOLVED",
                    origin_decision_basis="FREQUENCY_SEMANTICS_DO_NOT_IDENTIFY_JUDGE_JURY_OR_PANEL_RESPONSES",
                    publication_layer=PublicationLayer.GENERIC_ORGANIZER_SENSORY_FIELD,
                    frequency_value=frequency,
                    occurrence_index=len(candidates),
                )
            )
    return tuple(candidates)


def _extract_generic(record: SourceRecord) -> tuple[DescriptorCandidate, ...]:
    candidates: list[DescriptorCandidate] = []
    for field in record.fields:
        normalized_label = _label(field.label)
        if normalized_label in _METADATA_LABELS or not field.value.strip():
            continue
        if normalized_label in _GENERIC_SENSORY_LABELS:
            for atomic in _split_atomic(field.value):
                candidates.append(
                    _candidate(
                        record,
                        field,
                        atomic,
                        descriptor_class=_classify(
                            atomic, default_broad=normalized_label in _BROAD_FIELD_LABELS
                        ),
                        evidence_tier=EvidenceTier.UNRESOLVED,
                        evidence_origin_type="GENERIC_ORGANIZER_FIELD_ORIGIN_UNRESOLVED",
                        origin_decision_basis="ORGANIZER_HOSTING_DOES_NOT_IDENTIFY_FIELD_AUTHOR",
                        publication_layer=PublicationLayer.GENERIC_ORGANIZER_SENSORY_FIELD,
                        occurrence_index=len(candidates),
                    )
                )
        elif normalized_label == "producer cup profile":
            for atomic in _split_atomic(field.value):
                candidates.append(
                    _candidate(
                        record,
                        field,
                        atomic,
                        descriptor_class=_classify(atomic, default_broad=False),
                        evidence_tier=EvidenceTier.P3,
                        evidence_origin_type="PRODUCER_OR_FARM_DECLARED",
                        origin_decision_basis="EXPLICIT_PRODUCER_PROFILE_FIELD",
                        publication_layer=PublicationLayer.PRODUCER_OR_FARM_PROFILE,
                        occurrence_index=len(candidates),
                    )
                )
    return tuple(candidates)


def _extract_wcc_completed(record: SourceRecord) -> tuple[DescriptorCandidate, ...]:
    if not record.completed_filled_authoritative_scoresheet:
        return ()
    if not record.authoritative_completion_evidence_locator:
        raise AdapterViolation(
            "MISSING_COMPLETION_EVIDENCE",
            "a completed WCC scoresheet needs an authoritative completion locator",
        )
    candidates: list[DescriptorCandidate] = []
    accepted_labels = {"judge comments", "aroma / flavor description"}
    for field in record.fields:
        if _label(field.label) not in accepted_labels or not field.value.strip():
            continue
        if not field.judge_observation_id:
            raise AdapterViolation(
                "MISSING_JUDGE_OBSERVATION",
                "filled authoritative judge comments need a judge observation id",
            )
        for atomic in _split_atomic(field.value):
            candidates.append(
                _candidate(
                    record,
                    field,
                    atomic,
                    descriptor_class=_classify(atomic, default_broad=False),
                    evidence_tier=EvidenceTier.P1,
                    evidence_origin_type="EXPLICIT_OFFICIAL_JUDGE_OBSERVATION",
                    origin_decision_basis="AUTHORITATIVE_COMPLETED_FILLED_SCORESHEET",
                    publication_layer=PublicationLayer.JUDGE_LEVEL_OBSERVATION,
                    occurrence_index=len(candidates),
                )
            )
    return tuple(candidates)


def extract_candidates(record: SourceRecord) -> tuple[DescriptorCandidate, ...]:
    """Extract field-level candidates without semantic or rights promotion."""

    signature = SIGNATURES.get(record.schema_signature_id)
    if signature is None:
        raise AdapterViolation(
            "UNKNOWN_SCHEMA_SIGNATURE", record.schema_signature_id
        )
    if record.source_route_id != signature.source_route_id:
        raise AdapterViolation(
            "ROUTE_SIGNATURE_MISMATCH",
            f"{record.source_route_id} does not match {record.schema_signature_id}",
        )
    if record.schema_signature_id == COE_HONDURAS_TOP_JURY:
        return _extract_honduras_top_jury(record)
    if record.schema_signature_id == COE_COLOMBIA_FREQUENCY:
        return _extract_colombia_frequency(record)
    if record.schema_signature_id == COE_GENERIC_SENSORY:
        return _extract_generic(record)
    if record.schema_signature_id == WCC_COMPLETED_SCORESHEET:
        return _extract_wcc_completed(record)
    raise AssertionError("signature registry and dispatcher diverged")


def deinflate_assertions(
    candidates: Sequence[DescriptorCandidate],
) -> DeinflationResult:
    """Keep publication/observation counts distinct from record-unique counts."""

    admitted = [
        item
        for item in candidates
        if item.count_disposition == CountDisposition.ADMITTED
        and item.descriptor_class != DescriptorClass.NON_DESCRIPTOR
    ]
    assertion_level: list[DescriptorCandidate] = []
    record_unique: list[DescriptorCandidate] = []
    suppressed: list[SuppressedRepeat] = []
    observation_seen: dict[tuple[str, ...], DescriptorCandidate] = {}
    for item in admitted:
        key = (
            item.effective_record_id,
            item.source_artifact_id,
            item.publication_layer.value,
            item.judge_observation_id,
            item.source_selector_or_locator,
            item.normalized_candidate_form,
        )
        retained = observation_seen.get(key)
        if retained is not None:
            suppressed.append(
                SuppressedRepeat(
                    item.descriptor_assertion_id,
                    retained.descriptor_assertion_id,
                    "EXACT_WITHIN_OBSERVATION_REPEAT",
                )
            )
            continue
        observation_seen[key] = item
        assertion_level.append(item)

    record_seen: dict[tuple[str, str], DescriptorCandidate] = {}
    for item in assertion_level:
        # Record-level uniqueness follows the authoritative gate contract:
        # one normalized lexical form per effective record.  Descriptor class
        # remains on the retained assertion for review but cannot create a
        # second record-level observation of the same source-native form.
        key = (
            item.effective_record_id,
            item.normalized_candidate_form,
        )
        retained = record_seen.get(key)
        if retained is not None:
            suppressed.append(
                SuppressedRepeat(
                    item.descriptor_assertion_id,
                    retained.descriptor_assertion_id,
                    "CROSS_OBSERVATION_SAME_EFFECTIVE_RECORD",
                )
            )
            continue
        record_seen[key] = item
        record_unique.append(item)
    return DeinflationResult(
        extracted_candidates=tuple(candidates),
        assertion_level=tuple(assertion_level),
        record_unique=tuple(record_unique),
        suppressed=tuple(suppressed),
    )


def coassertion_events(
    record_unique: Iterable[DescriptorCandidate],
) -> tuple[CoassertionEvent, ...]:
    """Generate unordered P1/P2 pairs within, never across, effective records."""

    grouped: dict[str, set[str]] = defaultdict(set)
    for item in record_unique:
        if item.evidence_tier not in {EvidenceTier.P1, EvidenceTier.P2}:
            continue
        grouped[item.effective_record_id].add(item.normalized_candidate_form)
    events: list[CoassertionEvent] = []
    for effective_record_id, forms in sorted(grouped.items()):
        for left, right in itertools.combinations(sorted(forms), 2):
            events.append(CoassertionEvent(effective_record_id, left, right))
    return tuple(events)


def effective_record_count(records: Iterable[SourceRecord]) -> int:
    """Deduplicate publications/judges while retaining different services."""

    return len({record.effective_record.effective_record_id for record in records})


def independent_source_family_count(records: Iterable[SourceRecord]) -> int:
    return len({record.independent_source_family_id for record in records})


def assert_no_inferred_service_or_roast(
    source: SourceRecord, candidates: Sequence[DescriptorCandidate]
) -> None:
    """Guard against later code deriving roast or service from descriptor text."""

    for candidate in candidates:
        if candidate.roast_code != source.roast_code:
            raise AdapterViolation("ROAST_INFERENCE", "adapter changed explicit roast state")
        if candidate.preparation_family_code != source.preparation_family_code:
            raise AdapterViolation(
                "PREPARATION_INFERENCE", "adapter changed explicit preparation state"
            )


def with_rights(candidate: DescriptorCandidate, state: RightsState) -> DescriptorCandidate:
    """Test/support helper; review is still required so eligibility stays false."""

    return replace(candidate, rights_state=state, model_eligible=False)
