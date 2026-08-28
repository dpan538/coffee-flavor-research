"""Read owner-controlled bounded field captures without republishing source text."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .model import EffectiveRecordKey, RightsState, SourceField, SourceRecord
from .signatures import (
    COE_COLOMBIA_FREQUENCY,
    COE_GENERIC_SENSORY,
    COE_HONDURAS_TOP_JURY,
    SIGNATURES,
)


@dataclass(frozen=True)
class CaptureReceipt:
    filename: str
    sha256: str
    byte_count: int
    captured_at: str
    capture_scope: str
    record_count: int
    source_urls: tuple[str, ...]


_CAPTURE_CONFIG = {
    "coe_honduras_2017_top_jury.json": {
        "signature": COE_HONDURAS_TOP_JURY,
        "edition": "Honduras 2017",
        "rights": RightsState.PENDING,
        "required": {"Score from International Judges", "Top Jury Descriptions"},
    },
    "coe_colombia_south_2008_frequency.json": {
        "signature": COE_COLOMBIA_FREQUENCY,
        "edition": "Colombia South 2008",
        "rights": RightsState.UNKNOWN,
        "required": {"Aroma/Flavor", "Acidity"},
    },
    "coe_peru_2025_generic.json": {
        "signature": COE_GENERIC_SENSORY,
        "edition": "Peru 2025",
        "rights": RightsState.UNKNOWN,
        "required": {"Overall", "Aroma / Flavor", "Acidity"},
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_bounded_captures(
    restricted_root: Path,
) -> tuple[tuple[SourceRecord, ...], tuple[CaptureReceipt, ...]]:
    """Load exactly the allowlisted captures and bind rows to their file hashes."""

    capture_dir = restricted_root / "web_index_field_capture"
    records: list[SourceRecord] = []
    receipts: list[CaptureReceipt] = []
    for filename, config in _CAPTURE_CONFIG.items():
        path = capture_dir / filename
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"required non-symlink capture is missing: {path}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        document = json.loads(raw)
        if document.get("capture_contract") != "round3m.web-index-field-capture.v1":
            raise ValueError(f"unsupported capture contract: {filename}")
        if document.get("capture_scope") != "NOT_FULL_PAGE_BODY":
            raise ValueError(f"capture scope must remain explicit: {filename}")
        if document.get("capture_method") != "WEB_INDEX_FIELD_CAPTURE":
            raise ValueError(f"capture method differs: {filename}")
        if document.get("public_redistribution") is not False:
            raise ValueError(f"capture cannot authorize redistribution: {filename}")
        source_records = document.get("records")
        if not isinstance(source_records, list) or not source_records:
            raise ValueError(f"capture has no records: {filename}")
        signature_id = str(config["signature"])
        signature = SIGNATURES[signature_id]
        urls: list[str] = []
        for index, item in enumerate(source_records):
            if not isinstance(item, dict):
                raise ValueError(f"capture record is not an object: {filename}:{index}")
            field_values = item.get("fields")
            if not isinstance(field_values, dict) or not set(config["required"]).issubset(
                field_values
            ):
                raise ValueError(f"capture fields are incomplete: {filename}:{index}")
            source_url = str(item.get("source_url", ""))
            if not source_url.startswith("https://"):
                raise ValueError(f"capture URL is not HTTPS: {filename}:{index}")
            publication_host = source_url.split("/", 3)[2]
            if publication_host not in set(signature.host.split("|")):
                raise ValueError(
                    f"capture host is outside the schema signature: {filename}:{index}"
                )
            urls.append(source_url)
            capture_record_id = str(item.get("record_id", ""))
            if not capture_record_id:
                raise ValueError(f"capture record id is empty: {filename}:{index}")
            fields = tuple(
                SourceField(
                    label=str(label),
                    value=str(value),
                    selector_or_locator=(
                        f"restricted:{filename}#/records/{index}/fields/{label}"
                    ),
                )
                for label, value in field_values.items()
            )
            records.append(
                SourceRecord(
                    schema_signature_id=signature_id,
                    source_artifact_id=f"capture:{digest[:16]}:{capture_record_id}",
                    source_route_id=signature.source_route_id,
                    independent_source_family_id="family.coe",
                    source_url=source_url,
                    source_file_sha256=digest,
                    source_retrieved_at=str(document["captured_at"]),
                    effective_record=EffectiveRecordKey(
                        competition_series="Cup of Excellence",
                        edition=str(config["edition"]),
                        category="Cup of Excellence",
                        round_name="Competition final",
                        entry_or_lot=capture_record_id,
                        preparation_service="UNRESOLVED_PREPARATION_SERVICE",
                    ),
                    fields=fields,
                    rights_state=config["rights"],  # type: ignore[arg-type]
                    publication_host=publication_host,
                    publication_instance_id=capture_record_id,
                    roast_code=None,
                    preparation_family_code=None,
                )
            )
        receipts.append(
            CaptureReceipt(
                filename=filename,
                sha256=digest,
                byte_count=len(raw),
                captured_at=str(document["captured_at"]),
                capture_scope=str(document["capture_scope"]),
                record_count=len(source_records),
                source_urls=tuple(urls),
            )
        )
    return tuple(records), tuple(receipts)
