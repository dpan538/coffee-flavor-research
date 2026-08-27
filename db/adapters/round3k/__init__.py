"""Round 3K source-neutral professional competition adapter contract."""

from .contract import (
    CONTRACT_VERSION,
    QUALITY_THRESHOLDS,
    REQUIRED_FILES,
    REQUIRED_TABLE_FILES,
    RIGHTS_DIMENSIONS,
    SOURCE_PROFILES,
    SUPPORTED_SOURCE_KINDS,
    TABLE_SCHEMAS,
    AdapterProfile,
    ContractViolation,
    ExplicitRecordAdapter,
    ValidationSummary,
    emit_bundle,
    read_table,
    validate_bundle,
)

__all__ = [
    "CONTRACT_VERSION",
    "QUALITY_THRESHOLDS",
    "REQUIRED_FILES",
    "REQUIRED_TABLE_FILES",
    "RIGHTS_DIMENSIONS",
    "SOURCE_PROFILES",
    "SUPPORTED_SOURCE_KINDS",
    "TABLE_SCHEMAS",
    "AdapterProfile",
    "ContractViolation",
    "ExplicitRecordAdapter",
    "ValidationSummary",
    "emit_bundle",
    "read_table",
    "validate_bundle",
]
