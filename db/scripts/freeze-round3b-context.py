#!/usr/bin/env python3
"""Verify Round 3B source bytes and freeze raw context rows and audit split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPOSITORY_ROOT / "db" / "data" / "round3b"
RAW_ROOT = DATA_ROOT / "raw"
BENCHMARK_ROOT = DATA_ROOT / "benchmark"
DERIVED_ROOT = DATA_ROOT / "derived"
SOURCE_MANIFEST_PATH = RAW_ROOT / "SOURCE_MANIFEST.json"
CASE_SOURCE_PATH = BENCHMARK_ROOT / "context_cases_source.tsv"
SPLIT_SEED = "coffee-context-round3b-heldout-v1-20260825"
NORMALIZATION_VERSION = "context_normalization_v1"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_text(value: str) -> str:
    value = value.strip().casefold().replace("—", "-").replace("–", "-")
    return " ".join(value.split())


def read_csv(path: Path, encoding: str = "utf-8-sig") -> tuple[list[str], list[list[str]]]:
    with path.open("r", encoding=encoding, newline="") as source:
        reader = csv.reader(source)
        header = next(reader)
        return header, list(reader)


def compact_payload(header: list[str], row: list[str]) -> dict[str, str]:
    payload: dict[str, str] = {}
    for index, heading in enumerate(header):
        heading = heading.strip()
        if not heading or heading in payload or index >= len(row):
            continue
        value = row[index].strip()
        if value:
            payload[heading] = value
    return payload


def verify_source_manifest(manifest: dict[str, Any]) -> None:
    errors: list[str] = []
    for source in manifest["sources"]:
        for file_record in source["files"]:
            path = RAW_ROOT / file_record["path"]
            if not path.is_file():
                errors.append(f"missing {path}")
                continue
            byte_count = path.stat().st_size
            digest = sha256_path(path)
            if byte_count != file_record["bytes"]:
                errors.append(
                    f"byte mismatch {path}: {byte_count} != {file_record['bytes']}"
                )
            if digest != file_record["sha256"]:
                errors.append(
                    f"hash mismatch {path}: {digest} != {file_record['sha256']}"
                )
    if errors:
        raise SystemExit("\n".join(errors))


def preparation_resolution(raw_label: str) -> tuple[str, str, str]:
    value = normalized_text(raw_label)
    mapped: dict[str, tuple[str, str]] = {
        "filter": ("preparation.family.filter_percolation", ""),
        "drip": ("preparation.family.filter_percolation", ""),
        "immersion": ("preparation.family.immersion", ""),
        "french press": (
            "preparation.family.immersion",
            "preparation.method.french_press",
        ),
        "espresso": (
            "preparation.family.espresso_pressure",
            "preparation.method.espresso_standard",
        ),
        "cold brew": (
            "preparation.family.cold_extraction",
            "preparation.method.cold_brew_immersion",
        ),
        "cappucino": (
            "preparation.family.espresso_milk",
            "preparation.beverage.cappuccino",
        ),
    }
    not_applicable = {
        "solvent",
        "column",
        "pressurized liquid extraction",
    }
    unresolved = {"instant", "mocha", "frech", "french"}
    if not value:
        return "not_reported", "", ""
    if value in mapped:
        family, leaf = mapped[value]
        return "known", family, leaf
    if value in not_applicable:
        return "not_applicable", "", ""
    if value in unresolved:
        return "reported_unresolved", "", ""
    return "reported_unresolved", "", ""


def roast_resolution(raw_label: str) -> tuple[str, str]:
    value = normalized_text(raw_label)
    mapped = {"light": "light", "medium": "medium", "dark": "dark"}
    if value in mapped:
        return "known", mapped[value]
    if value == "green":
        return "not_applicable", ""
    if value in {"", "unspecified"}:
        return "not_reported", ""
    return "reported_unresolved", ""


def cotter_records(path: Path) -> Iterable[dict[str, Any]]:
    header, rows = read_csv(path)
    if len(rows) != 3186 or len(header) != 48:
        raise SystemExit("Cotter row/column inventory differs from reviewed source")
    for row_number, row in enumerate(rows, start=2):
        yield {
            "record_key": f"context.raw.cotter_v4.{row_number - 1:04d}",
            "source_key": "dryad_cotter_black_coffee",
            "file_relative_path": "cotter_2020_black_coffee/cotter_dataset.csv",
            "source_row_number": row_number,
            "raw_preparation_label": "drip-brewed black coffee",
            "raw_roast_label": "medium roast",
            "preparation_status_code": "known",
            "normalized_preparation_family_key": "preparation.family.filter_percolation",
            "normalized_preparation_leaf_key": "preparation.method.batch_filter",
            "roast_status_code": "known",
            "normalized_roast_code": "medium",
            "coffee_mode_code": "black_coffee",
            "has_sensory_outcome": True,
            "has_chemical_outcome": True,
            "has_strong_addition": False,
            "raw_payload": compact_payload(header, row),
        }


def acids_records(path: Path, file_code: str) -> Iterable[dict[str, Any]]:
    header, rows = read_csv(path)
    header_index = {heading.strip(): index for index, heading in enumerate(header)}
    expected_rows = 1344 if file_code == "cga" else 287
    if len(rows) != expected_rows:
        raise SystemExit(f"{path.name} row inventory differs from reviewed source")
    for row_number, row in enumerate(rows, start=2):
        preparation_label = row[header_index["Extraction"]].strip()
        roast_label = row[header_index["Roast"]].strip()
        preparation_status, family_key, leaf_key = preparation_resolution(
            preparation_label
        )
        roast_status, roast_code = roast_resolution(roast_label)
        preparation_value = normalized_text(preparation_label)
        if preparation_value == "cappucino":
            coffee_mode = "milk_coffee"
        elif preparation_status in {"known", "reported_unresolved"}:
            coffee_mode = "black_coffee"
        else:
            coffee_mode = "not_applicable"
        payload = compact_payload(header, row)
        measurement_values = [
            value for key, value in payload.items() if key not in {
                "Source", "Type", "Roast", "Extraction", "Stat", "Stats",
                "Other", "Units", "Notes", "Notes "
            }
        ]
        yield {
            "record_key": f"context.raw.yeager_v5.{file_code}.{row_number - 1:04d}",
            "source_key": "dryad_yeager_acids_meta_analysis",
            "file_relative_path": f"yeager_2021_acids_meta/{path.name}",
            "source_row_number": row_number,
            "raw_preparation_label": preparation_label,
            "raw_roast_label": roast_label,
            "preparation_status_code": preparation_status,
            "normalized_preparation_family_key": family_key,
            "normalized_preparation_leaf_key": leaf_key,
            "roast_status_code": roast_status,
            "normalized_roast_code": roast_code,
            "coffee_mode_code": coffee_mode,
            "has_sensory_outcome": False,
            "has_chemical_outcome": bool(measurement_values),
            "has_strong_addition": False,
            "raw_payload": payload,
        }


def write_tsv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(
            destination,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in rows:
            serializable = dict(row)
            for key, value in serializable.items():
                if isinstance(value, bool):
                    serializable[key] = "true" if value else "false"
                elif isinstance(value, (dict, list)):
                    serializable[key] = json.dumps(
                        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                    )
            writer.writerow(serializable)


def freeze_cases() -> tuple[int, int]:
    with CASE_SOURCE_PATH.open("r", encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    seen: set[str] = set()
    heldout_count = 0
    for row in rows:
        if row["case_key"] in seen:
            raise SystemExit(f"duplicate benchmark case: {row['case_key']}")
        seen.add(row["case_key"])
        split_hash = hashlib.sha256(
            f"{SPLIT_SEED}|{row['domain']}|{row['case_key']}".encode("utf-8")
        ).hexdigest()
        row["split"] = "held_out" if int(split_hash[:8], 16) % 5 == 0 else "development"
        row["split_hash_prefix"] = split_hash[:16]
        heldout_count += row["split"] == "held_out"
    output_fields = list(rows[0])
    write_tsv(BENCHMARK_ROOT / "context_cases_frozen.tsv", output_fields, rows)
    return len(rows), heldout_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.code_commit):
        raise SystemExit("--code-commit must be a full 40-character Git SHA")

    manifest = json.loads(SOURCE_MANIFEST_PATH.read_text(encoding="utf-8"))
    verify_source_manifest(manifest)

    records = list(
        cotter_records(RAW_ROOT / "cotter_2020_black_coffee" / "cotter_dataset.csv")
    )
    records.extend(
        acids_records(
            RAW_ROOT / "yeager_2021_acids_meta" / "Acids_in_Coffee_-CGAs.csv",
            "cga",
        )
    )
    records.extend(
        acids_records(
            RAW_ROOT / "yeager_2021_acids_meta" / "Acids_in_Coffee_-OAs.csv",
            "oa",
        )
    )
    if len(records) != 4817:
        raise SystemExit(f"unexpected imported context record count: {len(records)}")

    record_fields = [
        "record_key",
        "source_key",
        "file_relative_path",
        "source_row_number",
        "raw_preparation_label",
        "raw_roast_label",
        "preparation_status_code",
        "normalized_preparation_family_key",
        "normalized_preparation_leaf_key",
        "roast_status_code",
        "normalized_roast_code",
        "coffee_mode_code",
        "has_sensory_outcome",
        "has_chemical_outcome",
        "has_strong_addition",
        "raw_payload",
    ]
    record_path = DERIVED_ROOT / "context_records.tsv"
    write_tsv(record_path, record_fields, records)
    case_count, heldout_count = freeze_cases()

    source_hashes = sorted(
        file_record["sha256"]
        for source in manifest["sources"]
        if source["acquisition_status"] == "imported"
        for file_record in source["files"]
    )
    snapshot_material = "\n".join(
        source_hashes
        + [
            sha256_path(record_path),
            sha256_path(BENCHMARK_ROOT / "context_cases_frozen.tsv"),
            NORMALIZATION_VERSION,
            args.code_commit,
        ]
    )
    snapshot_hash = hashlib.sha256(snapshot_material.encode("utf-8")).hexdigest()
    snapshot = {
        "snapshot_key": "context.snapshot.round3b_v1",
        "snapshot_hash": snapshot_hash,
        "source_versions": [
            "dryad:B8993H:version_id=215645:version_number=4",
            "dryad:B8C91C:version_id=130006:version_number=5",
        ],
        "source_file_hashes": source_hashes,
        "source_count": 2,
        "context_record_count": len(records),
        "normalization_version": NORMALIZATION_VERSION,
        "code_commit": args.code_commit,
        "created_at": "2026-08-25T00:00:00+10:00",
        "split_seed": SPLIT_SEED,
        "case_count": case_count,
        "held_out_case_count": heldout_count,
        "stratification": "domain and authored semantic stratum; deterministic SHA-256 allocation",
    }
    snapshot_path = DERIVED_ROOT / "snapshot_manifest.json"
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"CONTEXT_SOURCE_HASH_PASS=true")
    print(f"CONTEXT_DATASET_ROW_COUNT={len(records)}")
    print(f"CONTEXT_CASE_COUNT={case_count}")
    print(f"CONTEXT_HELD_OUT_COUNT={heldout_count}")
    print(f"SNAPSHOT_HASH={snapshot_hash}")


if __name__ == "__main__":
    main()
