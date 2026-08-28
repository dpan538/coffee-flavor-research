#!/usr/bin/env python3
"""Generate hash-only Round 3M live assertion and capture receipts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from .live import coassertion_events, deinflate_assertions, extract_candidates
from .model import CountDisposition, DescriptorCandidate, DescriptorClass, SourceRecord
from .restricted import load_bounded_captures, load_capture_manifest
from .signatures import ADAPTER_VERSION, PARSER_VERSION


ASSERTION_COLUMNS = (
    "descriptor_assertion_id",
    "effective_record_id",
    "source_artifact_id",
    "source_route_id",
    "schema_signature_id",
    "publication_layer",
    "source_field_label",
    "source_selector_or_locator",
    "source_page_or_record_locator",
    "raw_field_text_sha256",
    "atomic_source_text_sha256",
    "source_language",
    "descriptor_class",
    "evidence_tier",
    "evidence_origin_type",
    "origin_decision_basis",
    "review_state",
    "review_actor_type",
    "rights_state",
    "within_record_repeat_group",
    "cross_observation_repeat_group",
    "count_disposition",
    "frequency_value",
    "source_retrieved_at",
    "route_index_sha256",
    "source_file_sha256_scope",
    "source_file_nonstorage_reason",
    "parser_version",
    "adapter_version",
    "model_eligible",
)

CAPTURE_COLUMNS = (
    "capture_filename",
    "capture_sha256",
    "byte_count",
    "captured_at",
    "capture_scope",
    "record_count",
    "source_urls_json",
    "full_page_body_stored",
    "public_redistribution",
)

SOURCE_ARTIFACT_COLUMNS = (
    "source_artifact_id",
    "source_route_id",
    "schema_signature_id",
    "governed_locator",
    "source_retrieved_at",
    "source_file_sha256",
    "file_size_bytes",
    "storage_state",
    "non_storage_reason",
    "parser_version",
    "adapter_version",
)

EFFECTIVE_RECORD_COLUMNS = (
    "round3m_effective_record_id",
    "effective_record_key",
    "series_id",
    "edition_id",
    "edition_year",
    "category_id",
    "round_id",
    "subject_kind",
    "entry_or_lot_id",
    "preparation_service_code",
    "preparation_evidence_locator",
    "source_route_id",
    "source_artifact_id",
    "source_record_locator",
    "source_file_sha256",
    "record_identity_sha256",
    "identity_resolution_state",
    "synthetic_generated",
    "preparation_inferred_from_descriptor",
)

_ROUTE_INDEX_SHA256 = {
    "schema.coe.honduras-2017.explicit-top-jury.v1": "453acfc3577f71686783139f9a6dad190ea8edcb188a778e2c8419166593cf95",
    "schema.coe.colombia-south-2008.frequency-coded.v1": "f508ebc481c39b4755250f1422148accae73dc57099ecb164e666e07a12b9bc1",
    "schema.coe.generic-sensory-field.v1": "83b674daf22d57d7d42ea92c30fb3b3b2a7b4927b3da6505022238a26941cc1a",
}


def _text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _public_id(value: str) -> str:
    return "-".join(value.casefold().replace("/", " ").split())


def _edition_year(value: str) -> int:
    for part in reversed(value.split()):
        if len(part) == 4 and part.isascii() and part.isdigit():
            year = int(part)
            if 1900 <= year <= 2100:
                return year
    raise ValueError(f"edition lacks a supported year: {value}")


def _write_tsv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def public_review_candidates(record: SourceRecord) -> tuple[DescriptorCandidate, ...]:
    """Retain every sensory candidate, including non-counting secondary layers."""

    return tuple(
        item
        for item in extract_candidates(record)
        if item.descriptor_class != DescriptorClass.NON_DESCRIPTOR
    )


def generate(restricted_root: Path, output_dir: Path) -> dict[str, object]:
    capture_manifest = load_capture_manifest(restricted_root)
    records, capture_receipts = load_bounded_captures(restricted_root)
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_by_sha256 = {receipt.sha256: receipt for receipt in capture_receipts}
    all_candidates = []
    all_assertion_level = []
    all_record_unique = []
    within_repeat_groups: dict[str, str] = {}
    repeat_groups: dict[str, str] = {}
    for record in records:
        candidates = public_review_candidates(record)
        admitted_candidates = tuple(
            item
            for item in candidates
            if item.count_disposition == CountDisposition.ADMITTED
        )
        result = deinflate_assertions(admitted_candidates)
        all_candidates.extend(candidates)
        all_assertion_level.extend(result.assertion_level)
        all_record_unique.extend(result.record_unique)
        for repeat in result.suppressed:
            group = "repeat:" + hashlib.sha256(
                (repeat.retained_assertion_id + repeat.descriptor_assertion_id).encode(
                    "utf-8"
                )
            ).hexdigest()[:20]
            if repeat.reason == "EXACT_WITHIN_OBSERVATION_REPEAT":
                within_repeat_groups[repeat.retained_assertion_id] = group
                within_repeat_groups[repeat.descriptor_assertion_id] = group
            elif repeat.reason == "CROSS_OBSERVATION_SAME_EFFECTIVE_RECORD":
                repeat_groups[repeat.retained_assertion_id] = group
                repeat_groups[repeat.descriptor_assertion_id] = group

    assertion_rows: list[dict[str, object]] = []
    for item in all_candidates:
        assertion_rows.append(
            {
                "descriptor_assertion_id": item.descriptor_assertion_id,
                "effective_record_id": item.effective_record_id,
                "source_artifact_id": item.source_artifact_id,
                "source_route_id": item.source_route_id,
                "schema_signature_id": item.schema_signature_id,
                "publication_layer": item.publication_layer.value,
                "source_field_label": item.source_field_label,
                "source_selector_or_locator": item.source_selector_or_locator,
                "source_page_or_record_locator": item.source_page_or_record_locator,
                "raw_field_text_sha256": _text_hash(item.raw_field_text),
                "atomic_source_text_sha256": _text_hash(item.atomic_source_text),
                "source_language": item.source_language,
                "descriptor_class": item.descriptor_class.value,
                "evidence_tier": item.evidence_tier.value,
                "evidence_origin_type": item.evidence_origin_type,
                "origin_decision_basis": item.origin_decision_basis,
                "review_state": "PROVISIONAL_MACHINE_CLASSIFIED",
                "review_actor_type": "AUTOMATED_PARSER",
                "rights_state": item.rights_state.value,
                "within_record_repeat_group": within_repeat_groups.get(
                    item.descriptor_assertion_id, ""
                ),
                "cross_observation_repeat_group": repeat_groups.get(
                    item.descriptor_assertion_id, ""
                ),
                "count_disposition": item.count_disposition.value,
                "frequency_value": item.frequency_value or "",
                "source_retrieved_at": item.source_retrieved_at,
                "route_index_sha256": _ROUTE_INDEX_SHA256[item.schema_signature_id],
                "source_file_sha256_scope": (
                    "WEB_INDEX_FIELD_CAPTURE_SHA256:"
                    + item.source_file_sha256
                    + ";NOT_FULL_PAGE_BODY"
                ),
                "source_file_nonstorage_reason": "OFFICIAL_FULL_PAGE_BODY_NOT_STORED_ENVIRONMENT_POLICY",
                "parser_version": item.parser_version,
                "adapter_version": item.adapter_version,
                "model_eligible": "false",
            }
        )
    assertion_rows.sort(
        key=lambda row: (
            str(row["schema_signature_id"]),
            str(row["effective_record_id"]),
            str(row["descriptor_assertion_id"]),
        )
    )
    capture_rows = [
        {
            "capture_filename": receipt.filename,
            "capture_sha256": receipt.sha256,
            "byte_count": receipt.byte_count,
            "captured_at": receipt.captured_at,
            "capture_scope": receipt.capture_scope,
            "record_count": receipt.record_count,
            "source_urls_json": json.dumps(
                receipt.source_urls, ensure_ascii=False, separators=(",", ":")
            ),
            "full_page_body_stored": "false",
            "public_redistribution": "false",
        }
        for receipt in capture_receipts
    ]
    source_artifact_rows: list[dict[str, object]] = []
    effective_record_rows: list[dict[str, object]] = []
    for record in records:
        receipt = receipt_by_sha256[record.source_file_sha256]
        record_index = next(
            index
            for index, source_url in enumerate(receipt.source_urls)
            if source_url == record.source_url
        )
        governed_locator = (
            f"{capture_manifest.root_locator}/web_index_field_capture/"
            f"{receipt.filename}#/records/{record_index}"
        )
        source_artifact_rows.append(
            {
                "source_artifact_id": record.source_artifact_id,
                "source_route_id": record.source_route_id,
                "schema_signature_id": record.schema_signature_id,
                "governed_locator": governed_locator,
                "source_retrieved_at": record.source_retrieved_at,
                "source_file_sha256": record.source_file_sha256,
                "file_size_bytes": receipt.byte_count,
                "storage_state": "HASH_AND_LOCATOR_ONLY",
                "non_storage_reason": "SOURCE_TEXT_RETAINED_ONLY_IN_OWNER_CONTROLLED_RESTRICTED_CAPTURE",
                "parser_version": PARSER_VERSION,
                "adapter_version": ADAPTER_VERSION,
            }
        )
        key = record.effective_record
        series_id = "coe"
        edition_id = _public_id(key.edition)
        edition_year = _edition_year(key.edition)
        category_id = _public_id(key.category)
        round_id = _public_id(key.round_name)
        subject_kind = "LOT"
        entry_or_lot_id = key.entry_or_lot
        preparation_service_code = _public_id(key.preparation_service)
        snapshot_identity = f"file:{record.source_file_sha256}"
        identity_material = "\x1f".join(
            (
                series_id,
                edition_id,
                str(edition_year),
                category_id,
                round_id,
                subject_kind,
                entry_or_lot_id,
                preparation_service_code,
                record.source_route_id,
                snapshot_identity,
                record.source_url,
            )
        )
        effective_record_rows.append(
            {
                "round3m_effective_record_id": key.effective_record_id,
                "effective_record_key": key.effective_record_id,
                "series_id": series_id,
                "edition_id": edition_id,
                "edition_year": edition_year,
                "category_id": category_id,
                "round_id": round_id,
                "subject_kind": subject_kind,
                "entry_or_lot_id": entry_or_lot_id,
                "preparation_service_code": preparation_service_code,
                "preparation_evidence_locator": "source-record:preparation-not-published",
                "source_route_id": record.source_route_id,
                "source_artifact_id": record.source_artifact_id,
                "source_record_locator": record.source_url,
                "source_file_sha256": record.source_file_sha256,
                "record_identity_sha256": hashlib.sha256(
                    identity_material.encode("utf-8")
                ).hexdigest(),
                "identity_resolution_state": "SOURCE_NATIVE_PROVISIONAL",
                "synthetic_generated": "false",
                "preparation_inferred_from_descriptor": "false",
            }
        )
    source_artifact_rows.sort(key=lambda row: str(row["source_artifact_id"]))
    effective_record_rows.sort(
        key=lambda row: str(row["round3m_effective_record_id"])
    )
    _write_tsv(output_dir / "PUBLIC_SAFE_LIVE_ASSERTIONS.tsv", ASSERTION_COLUMNS, assertion_rows)
    _write_tsv(output_dir / "PUBLIC_SAFE_CAPTURE_RECEIPTS.tsv", CAPTURE_COLUMNS, capture_rows)
    _write_tsv(
        output_dir / "PUBLIC_SAFE_SOURCE_ARTIFACTS.tsv",
        SOURCE_ARTIFACT_COLUMNS,
        source_artifact_rows,
    )
    _write_tsv(
        output_dir / "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv",
        EFFECTIVE_RECORD_COLUMNS,
        effective_record_rows,
    )

    admitted_candidates = [
        item
        for item in all_candidates
        if item.count_disposition == CountDisposition.ADMITTED
    ]
    tier_counts = Counter(item.evidence_tier.value for item in admitted_candidates)
    class_counts = Counter(item.descriptor_class.value for item in admitted_candidates)
    rights_counts = Counter(item.rights_state.value for item in admitted_candidates)
    metrics: dict[str, object] = {
        "contract_version": "round3m.live-adapter-public-receipt.v1",
        "capture_scope": "WEB_INDEX_FIELD_CAPTURE_NOT_FULL_PAGE_BODY",
        "live_source_adapter_count": 4,
        "live_source_adapter_validated_count": 3,
        "completed_wcc_scoresheet_live_positive_count": 0,
        "segmented_atomic_candidate_count": len(admitted_candidates),
        "public_review_candidate_count": len(all_candidates),
        "secondary_review_only_candidate_count": sum(
            item.count_disposition == CountDisposition.SECONDARY_REVIEW_ONLY
            for item in all_candidates
        ),
        "assertion_level_deinflated_count": len(all_assertion_level),
        "record_level_unique_count": len(all_record_unique),
        "p1_p2_within_effective_record_coassertion_count": len(
            coassertion_events(all_record_unique)
        ),
        "effective_record_count": len(
            {item.effective_record_id for item in admitted_candidates}
        ),
        "source_artifact_bridge_count": len(source_artifact_rows),
        "effective_record_bridge_count": len(effective_record_rows),
        "tier_counts": dict(sorted(tier_counts.items())),
        "class_counts": dict(sorted(class_counts.items())),
        "rights_counts": dict(sorted(rights_counts.items())),
        "cross_observation_repeat_count": sum(
            1
            for group in set(repeat_groups.values())
            if group
        ),
        "within_observation_repeat_count": sum(
            1
            for group in set(within_repeat_groups.values())
            if group
        ),
        "mexico_2023_export_count": 0,
        "mexico_2023_status": "SOURCE_DRIFT_DETAIL_BODY_UNAVAILABLE",
        "model_eligible_count": 0,
        "raw_source_text_published": False,
        "full_page_body_acquisition_status": "BLOCKED_ENVIRONMENT_POLICY",
        "restricted_capture_manifest_contract": capture_manifest.contract_version,
        "restricted_capture_manifest_sha256": capture_manifest.sha256,
        "restricted_capture_root_locator": capture_manifest.root_locator,
    }
    (output_dir / "LIVE_ADAPTER_METRICS.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--restricted-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    metrics = generate(args.restricted_root.resolve(), args.output_dir.resolve())
    print(json.dumps(metrics, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
