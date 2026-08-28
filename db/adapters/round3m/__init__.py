"""Round 3M source-specific professional descriptor adapters."""

from .live import (
    assert_no_inferred_service_or_roast,
    coassertion_events,
    deinflate_assertions,
    effective_record_count,
    extract_candidates,
    independent_source_family_count,
)
from .model import (
    AdapterViolation,
    CountDisposition,
    DescriptorCandidate,
    DescriptorClass,
    EffectiveRecordKey,
    EvidenceTier,
    PublicationLayer,
    RightsState,
    SourceField,
    SourceRecord,
)
from .signatures import SIGNATURES

__all__ = [
    "AdapterViolation",
    "CountDisposition",
    "DescriptorCandidate",
    "DescriptorClass",
    "EffectiveRecordKey",
    "EvidenceTier",
    "PublicationLayer",
    "RightsState",
    "SIGNATURES",
    "SourceField",
    "SourceRecord",
    "assert_no_inferred_service_or_roast",
    "coassertion_events",
    "deinflate_assertions",
    "effective_record_count",
    "extract_candidates",
    "independent_source_family_count",
]
