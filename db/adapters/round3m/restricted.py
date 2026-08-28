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


@dataclass(frozen=True)
class ManifestArtifactReceipt:
    relative_path: str
    sha256: str
    byte_count: int
    retrieved_at: str
    capture_scope: str
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class CaptureManifestReceipt:
    contract_version: str
    sha256: str
    root_locator: str
    generated_at: str
    artifacts: tuple[ManifestArtifactReceipt, ...]


EXPECTED_CAPTURE_MANIFEST_SHA256 = (
    "b36fbe8a959b099b1a3a073b045c3d6ac74e31043f090d2fd88bd78c3290e51d"
)
EXPECTED_CAPTURE_ROOT_LOCATOR = (
    "restricted://coffee-flavor-round3m/round3m-2026-08-28t043000z"
)


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


def load_capture_manifest(restricted_root: Path) -> CaptureManifestReceipt:
    """Verify the exact governed checkpoint before any capture is trusted.

    The path supplied by a caller is never authority by itself.  The manifest
    hash, governed locator, artifact inventory, sizes, and hashes are pinned to
    the audited owner-controlled checkpoint.
    """

    manifest_path = restricted_root / "CAPTURE_MANIFEST.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise ValueError(f"required non-symlink capture manifest is missing: {manifest_path}")
    raw = manifest_path.read_bytes()
    manifest_sha256 = hashlib.sha256(raw).hexdigest()
    if manifest_sha256 != EXPECTED_CAPTURE_MANIFEST_SHA256:
        raise ValueError(
            "capture manifest hash differs from governed checkpoint: "
            f"{manifest_sha256}"
        )
    document = json.loads(raw)
    if not isinstance(document, dict):
        raise ValueError("capture manifest must be a JSON object")
    if document.get("contract_version") != "round3m.restricted-capture-manifest.v1":
        raise ValueError("unsupported capture manifest contract")
    if document.get("root") != EXPECTED_CAPTURE_ROOT_LOCATOR:
        raise ValueError("capture manifest governed root locator drift")
    if document.get("storage_class") != "OWNER_CONTROLLED_RESTRICTED_NON_GIT":
        raise ValueError("capture manifest storage class drift")
    if document.get("public_redistribution") is not False:
        raise ValueError("capture manifest cannot authorize public redistribution")
    raw_artifacts = document.get("artifacts")
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ValueError("capture manifest has no artifact inventory")

    artifacts: list[ManifestArtifactReceipt] = []
    seen_paths: set[str] = set()
    for index, item in enumerate(raw_artifacts):
        if not isinstance(item, dict):
            raise ValueError(f"capture manifest artifact is not an object: {index}")
        relative_path = str(item.get("path", ""))
        candidate = Path(relative_path)
        if (
            not relative_path
            or candidate.is_absolute()
            or ".." in candidate.parts
            or relative_path in seen_paths
        ):
            raise ValueError(f"unsafe or duplicate capture manifest path: {relative_path}")
        seen_paths.add(relative_path)
        artifact_path = restricted_root / candidate
        if not artifact_path.is_file() or artifact_path.is_symlink():
            raise ValueError(f"manifest artifact is missing or a symlink: {relative_path}")
        expected_sha256 = str(item.get("sha256", ""))
        expected_bytes = item.get("bytes")
        if len(expected_sha256) != 64 or any(
            character not in "0123456789abcdef" for character in expected_sha256
        ):
            raise ValueError(f"invalid artifact SHA-256 in manifest: {relative_path}")
        if not isinstance(expected_bytes, int) or expected_bytes < 0:
            raise ValueError(f"invalid artifact byte count in manifest: {relative_path}")
        if _sha256(artifact_path) != expected_sha256:
            raise ValueError(f"manifest artifact hash mismatch: {relative_path}")
        if artifact_path.stat().st_size != expected_bytes:
            raise ValueError(f"manifest artifact size mismatch: {relative_path}")
        source_urls = item.get("source_urls")
        if not isinstance(source_urls, list) or not all(
            isinstance(url, str) and url.startswith("https://") for url in source_urls
        ):
            raise ValueError(f"invalid source URL inventory: {relative_path}")
        artifacts.append(
            ManifestArtifactReceipt(
                relative_path=relative_path,
                sha256=expected_sha256,
                byte_count=expected_bytes,
                retrieved_at=str(item.get("retrieved_at", "")),
                capture_scope=str(item.get("capture_scope", "")),
                source_urls=tuple(source_urls),
            )
        )

    expected_paths = {
        *(f"web_index_field_capture/{filename}" for filename in _CAPTURE_CONFIG),
        "web_index_field_capture/FULL_BODY_ACQUISITION_BLOCKER.json",
    }
    if seen_paths != expected_paths:
        raise ValueError("capture manifest artifact inventory differs from governed checkpoint")
    if document.get("bounded_field_capture_count") != len(_CAPTURE_CONFIG):
        raise ValueError("bounded field capture count drift")
    if document.get("official_full_page_body_count") != 0:
        raise ValueError("unexpected official full-page body in restricted checkpoint")
    return CaptureManifestReceipt(
        contract_version=str(document["contract_version"]),
        sha256=manifest_sha256,
        root_locator=str(document["root"]),
        generated_at=str(document.get("generated_at", "")),
        artifacts=tuple(artifacts),
    )


def load_bounded_captures(
    restricted_root: Path,
) -> tuple[tuple[SourceRecord, ...], tuple[CaptureReceipt, ...]]:
    """Load exactly the allowlisted captures and bind rows to their file hashes."""

    manifest = load_capture_manifest(restricted_root)
    artifact_by_path = {artifact.relative_path: artifact for artifact in manifest.artifacts}
    capture_dir = restricted_root / "web_index_field_capture"
    records: list[SourceRecord] = []
    receipts: list[CaptureReceipt] = []
    for filename, config in _CAPTURE_CONFIG.items():
        path = capture_dir / filename
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"required non-symlink capture is missing: {path}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        manifest_artifact = artifact_by_path[f"web_index_field_capture/{filename}"]
        if digest != manifest_artifact.sha256 or len(raw) != manifest_artifact.byte_count:
            raise ValueError(f"capture differs from governed manifest: {filename}")
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
        if tuple(urls) != manifest_artifact.source_urls:
            raise ValueError(f"capture source URL inventory differs from manifest: {filename}")
        if str(document.get("captured_at", "")) != manifest_artifact.retrieved_at:
            raise ValueError(f"capture timestamp differs from manifest: {filename}")
        if manifest_artifact.capture_scope != "WEB_INDEX_FIELD_CAPTURE_NOT_FULL_PAGE_BODY":
            raise ValueError(f"capture scope differs from manifest: {filename}")
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
