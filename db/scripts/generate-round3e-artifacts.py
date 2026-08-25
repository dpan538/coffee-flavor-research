#!/usr/bin/env python3
"""Generate deterministic, source-local Round 3E evidence artifacts.

The generator uses only the Python standard library. It verifies immutable raw
file hashes and declared dimensions before producing any derived record. Raw,
parsed, and normalized values remain separate; no unit conversion is applied.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = ROOT / "db/data/round3e/raw"
SOURCE_ROOT = ROOT / "db/data/round3e/source"
OUTPUT_ROOT = ROOT / "db/data/round3e/generated"
MANIFEST_PATH = RAW_ROOT / "SOURCE_MANIFEST.json"
QUESTION_PATH = SOURCE_ROOT / "question_candidates.json"
PII_HEADER = re.compile(r"^(name|full.?name|email|phone|address|street|postcode|postal.?code)$", re.I)
PII_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
LANGUAGE_ORDER = {"en": 0, "zh-Hans": 1, "zh": 2, "zh-hans": 3, "zh-cn": 4}

WIKIDATA_CONTEXT = {
    "Q180289": ("espresso_pressure", "black"),
    "Q159774": ("espresso_milk", "milk"),
    "Q841774": ("espresso_milk", "milk"),
    "Q1152551": ("diluted_espresso", "black"),
    "Q849290": ("diluted_espresso", "black"),
    "Q5142444": ("cold_extraction", "black"),
    "Q968554": ("unresolved_iced_preparation", "not_reported"),
    "Q1147545": ("immersion", "black"),
    "Q381188": ("hybrid", "black"),
    "Q1155703": ("filter_percolation", "black"),
    "Q43022": ("stovetop_boiled", "black"),
    "Q1054566": ("stovetop_boiled", "black"),
    "Q858049": ("unresolved_instant_product", "not_reported"),
    "Q62449": ("espresso_milk", "milk"),
}


class ContractError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_tsv(path: Path, headers: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in headers})


def normalize_expression(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return re.sub(r"\s+", " ", normalized)


def column_number(reference: str) -> int:
    letters = "".join(char for char in reference if char.isalpha())
    number = 0
    for char in letters:
        number = number * 26 + ord(char.upper()) - 64
    return number


def xlsx_rows(path: Path, sheet_name: str) -> list[list[object | None]]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rel_ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
    office_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", ns):
                shared.append("".join(node.text or "" for node in item.iterfind(".//m:t", ns)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("r:Relationship", rel_ns)}
        target = None
        for sheet in workbook.findall("m:sheets/m:sheet", ns):
            if sheet.attrib["name"] == sheet_name:
                target = targets[sheet.attrib[office_rel]]
                break
        if target is None:
            raise ContractError(f"missing worksheet {sheet_name!r} in {path}")
        sheet_path = target.lstrip("/")
        if not sheet_path.startswith("xl/"):
            sheet_path = "xl/" + sheet_path
        sheet_root = ET.fromstring(archive.read(sheet_path))
        rows: list[list[object | None]] = []
        for row_node in sheet_root.findall("m:sheetData/m:row", ns):
            cells: dict[int, object | None] = {}
            for cell in row_node.findall("m:c", ns):
                index = column_number(cell.attrib["r"])
                cell_type = cell.attrib.get("t")
                value_node = cell.find("m:v", ns)
                if cell_type == "inlineStr":
                    value = "".join(node.text or "" for node in cell.iterfind(".//m:t", ns))
                elif value_node is None:
                    value = None
                elif cell_type == "s":
                    value = shared[int(value_node.text or "0")]
                elif cell_type == "b":
                    value = value_node.text == "1"
                elif cell_type in {"str", "e"}:
                    value = value_node.text
                else:
                    raw = value_node.text or ""
                    try:
                        number = float(raw)
                        value = int(number) if number.is_integer() else number
                    except ValueError:
                        value = raw
                cells[index] = value
            width = max(cells, default=0)
            rows.append([cells.get(index) for index in range(1, width + 1)])
        return rows


def padded(row: list[object | None], width: int) -> list[object | None]:
    return row + [None] * (width - len(row))


def json_record(headers: list[str], values: list[object | None]) -> dict[str, object | None]:
    return {header: values[index] if index < len(values) else None for index, header in enumerate(headers)}


def normalized_record(raw: dict[str, object | None], inherited: dict[str, object] | None = None) -> dict[str, object | None]:
    result: dict[str, object | None] = {}
    for key, value in raw.items():
        result[key] = value.strip() if isinstance(value, str) else value
    if inherited:
        result.update(inherited)
    return result


def verify_manifest(manifest: dict[str, object]) -> None:
    snapshots = manifest.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise ContractError("source manifest must contain snapshots")
    keys = [item.get("dataset_snapshot_key") for item in snapshots if isinstance(item, dict)]
    if len(keys) != len(set(keys)):
        raise ContractError("duplicate external snapshot key")
    expected_dimensions = {
        "mendeley.ftnir-specialty-coffee.v4.selected": (320, 15),
        "mendeley.coffee-taste-sensitivity.v1": (93, 13),
        "wikidata.coffee-preparation-entities.20260825": (14, 6),
        "usda.fdc-coffee-search.fndds-2021-2023.20260825": (50, 18),
    }
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            raise ContractError("snapshot entry must be an object")
        if not snapshot.get("license"):
            raise ContractError(f"missing license decision: {snapshot.get('dataset_snapshot_key')}")
        if not snapshot.get("rights_decision") or not snapshot.get("privacy_decision"):
            raise ContractError(f"missing rights/privacy decision: {snapshot.get('dataset_snapshot_key')}")
        if snapshot.get("public_release_eligible") and str(snapshot.get("rights_decision", "")).startswith("BLOCKED"):
            raise ContractError("public export of blocked raw text")
        snapshot_key = str(snapshot.get("dataset_snapshot_key"))
        if snapshot_key not in expected_dimensions:
            raise ContractError(f"unreviewed external snapshot key: {snapshot_key}")
        expected_rows, expected_fields = expected_dimensions[snapshot_key]
        if snapshot.get("declared_row_count") != expected_rows:
            raise ContractError(f"wrong declared row count: {snapshot_key}")
        if snapshot.get("declared_field_count") != expected_fields:
            raise ContractError(f"wrong declared field count: {snapshot_key}")
        for file_info in snapshot.get("files", []):
            path = RAW_ROOT / str(file_info["path"])
            if not path.is_file():
                raise ContractError(f"missing source file: {path}")
            expected = str(file_info["sha256"])
            if not HASH_RE.fullmatch(expected) or sha256(path) != expected:
                raise ContractError(f"mismatched file hash: {file_info['path']}")


def build_excel_observations() -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    observations: list[dict[str, object]] = []
    fields: list[dict[str, object]] = []
    profile: dict[str, object] = {}

    origin_path = RAW_ROOT / "mendeley_ftnir_v4/Sample_origin_and_sensory_score_Specialty_Coffee.xlsx"
    rows = xlsx_rows(origin_path, "data")
    if len(rows) - 2 != 128:
        raise ContractError("wrong declared row count: Mendeley FT-NIR origin worksheet")
    headers = [
        "sample_no_sensory", "type", "municipality_colombia", "variety", "water_activity",
        "moisture_content_percent_wet_basis", "sensory_score_sca_source_label", "separator",
        "sample_no_geography", "latitude", "longitude", "height_masl", "rainfall_mm",
    ]
    source_headers = [header for header in headers if header != "separator"]
    for position, header in enumerate(headers, start=1):
        if header == "separator":
            continue
        fields.append({
            "dataset_snapshot_key": "mendeley.ftnir-specialty-coffee.v4.selected",
            "source_file": origin_path.name,
            "source_local_column_name": str(padded(rows[1], 13)[position - 1]),
            "project_field_key": header,
            "source_local_unit": {5: "ratio", 6: "percent wet basis", 10: "decimal degrees", 11: "decimal degrees", 12: "metres above sea level", 13: "millimetres"}.get(position, "not_applicable"),
            "normalization_rule": "trim_outer_whitespace_only" if position in {2, 3, 4} else "identity_no_unit_conversion",
        })
    current_sample = None
    for source_row, values in enumerate(rows[2:], start=3):
        values = padded(values, 13)
        raw_full = json_record(headers, values)
        raw = {key: value for key, value in raw_full.items() if key != "separator"}
        if raw["sample_no_sensory"] is not None:
            current_sample = raw["sample_no_sensory"]
        normalized = normalized_record(raw, {"derived_sample_no": current_sample})
        observations.append({
            "dataset_snapshot_key": "mendeley.ftnir-specialty-coffee.v4.selected",
            "source_file": origin_path.name,
            "source_row_identity": f"data!{source_row}",
            "record_type": "sample_origin_and_score",
            "raw_value_json": compact_json(raw),
            "parsed_value_json": compact_json(raw),
            "normalized_value_json": compact_json(normalized),
            "normalization_rule": "outer whitespace trimmed; sample number forward-filled only into derived_sample_no; no unit conversion",
            "exclusion_reason": "",
        })

    score_path = RAW_ROOT / "mendeley_ftnir_v4/SensoryQuality_RoastedCoffee.xlsx"
    rows = xlsx_rows(score_path, "Cup quality_RoastedCoffee")
    if len(rows) - 1 != 192:
        raise ContractError("wrong declared row count: Mendeley FT-NIR sensory worksheet")
    headers = ["sample", "replicates", "cup_quality_points_source_label"]
    for position, header in enumerate(headers):
        fields.append({
            "dataset_snapshot_key": "mendeley.ftnir-specialty-coffee.v4.selected",
            "source_file": score_path.name,
            "source_local_column_name": str(padded(rows[0], 3)[position]),
            "project_field_key": header,
            "source_local_unit": "source-local points" if position == 2 else "not_applicable",
            "normalization_rule": "identity_no_unit_conversion",
        })
    current_sample = None
    for source_row, values in enumerate(rows[1:], start=2):
        raw = json_record(headers, padded(values, 3))
        if raw["sample"] is not None:
            current_sample = raw["sample"]
        normalized = normalized_record(raw, {"derived_sample_no": current_sample})
        observations.append({
            "dataset_snapshot_key": "mendeley.ftnir-specialty-coffee.v4.selected",
            "source_file": score_path.name,
            "source_row_identity": f"Cup quality_RoastedCoffee!{source_row}",
            "record_type": "sensory_score_replicate",
            "raw_value_json": compact_json(raw),
            "parsed_value_json": compact_json(raw),
            "normalized_value_json": compact_json(normalized),
            "normalization_rule": "sample number forward-filled only into derived_sample_no; no score transformation",
            "exclusion_reason": "",
        })

    taste_path = RAW_ROOT / "mendeley_taste_sensitivity_v1/Coffee_sensory_information_data.xlsx"
    rows = xlsx_rows(taste_path, "raw data")
    if len(rows) - 1 != 93:
        raise ContractError("wrong declared row count: Mendeley taste-sensitivity worksheet")
    headers = [str(value).strip() for value in padded(rows[0], 13)]
    for header in headers:
        if PII_HEADER.fullmatch(header):
            raise ContractError(f"import of direct participant identifiers: {header}")
        fields.append({
            "dataset_snapshot_key": "mendeley.coffee-taste-sensitivity.v1",
            "source_file": taste_path.name,
            "source_local_column_name": header,
            "project_field_key": re.sub(r"[^a-z0-9]+", "_", header.casefold()).strip("_"),
            "source_local_unit": "source-local response scale",
            "normalization_rule": "identity_no_unit_conversion",
        })
    unique_ids: set[object] = set()
    missing = Counter()
    exact_rows = Counter()
    for source_row, values in enumerate(rows[1:], start=2):
        raw = json_record(headers, padded(values, 13))
        unique_ids.add(raw["ID"])
        for key, value in raw.items():
            if value is None or value == "":
                missing[key] += 1
            if isinstance(value, str) and PII_EMAIL.search(value):
                raise ContractError("import of direct participant identifiers: email-like value")
        exact_rows[compact_json(raw)] += 1
        observations.append({
            "dataset_snapshot_key": "mendeley.coffee-taste-sensitivity.v1",
            "source_file": taste_path.name,
            "source_row_identity": f"raw data!{source_row}",
            "record_type": "pseudonymous_consumer_response",
            "raw_value_json": compact_json(raw),
            "parsed_value_json": compact_json(raw),
            "normalized_value_json": compact_json(normalized_record(raw)),
            "normalization_rule": "identity; pseudonymous source ID retained; no scale transformation",
            "exclusion_reason": "",
        })
    profile["mendeley.coffee-taste-sensitivity.v1"] = {
        "raw_row_count": 93,
        "imported_record_count": 93,
        "exclusion_count": 0,
        "unique_participant_count": len(unique_ids),
        "duplicate_row_count": sum(count - 1 for count in exact_rows.values() if count > 1),
        "missingness_by_field": dict(sorted(missing.items())),
        "participant_type": "ordinary_user_or_consumer_as_source_described",
        "pii_scan_pass": True,
        "quality_flags": ["source-local numeric codebooks are not fully defined in the workbook", "age and gender are retained as public source demographics; source ID is pseudonymous"],
    }
    profile["mendeley.ftnir-specialty-coffee.v4.selected"] = {
        "raw_row_count": 320,
        "imported_record_count": 320,
        "exclusion_count": 0,
        "unique_sample_count": 64,
        "unique_participant_or_assessor_count": 0,
        "replicate_coverage": "three source-labelled score replicates for each of 64 samples",
        "preparation_coverage": {"not_reported_in_selected_files": 320},
        "roast_coverage": {"green_source_rows": 64, "roasted_source_rows_no_seven_level_mapping": 256},
        "quality_flags": ["source label says SCA score; no project endorsement or conversion", "assessor and preparation metadata are not present in selected files", "geographical columns end before the 128-row green/roasted series"],
        "pii_scan_pass": True,
    }
    return observations, fields, profile


def usda_context(description: str) -> tuple[str, str]:
    lowered = description.casefold()
    if "latte" in lowered or "cafe con leche" in lowered or "macchiato" in lowered or "frozen coffee" in lowered:
        return "espresso_milk_or_mixed_coffee_candidate", "milk"
    if "espresso" in lowered:
        return "espresso_pressure", "black"
    if "turkish" in lowered:
        return "stovetop_boiled", "black"
    if "brewed" in lowered:
        return "filter_percolation_candidate", "black"
    if "cuban" in lowered:
        return "unresolved_cuban_preparation", "not_reported"
    return "unresolved_preparation", "not_reported"


def build_corpus() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    documents: list[dict[str, object]] = []
    expressions: list[dict[str, object]] = []
    mappings: list[dict[str, object]] = []
    profiles: dict[str, object] = {}

    wikidata_path = RAW_ROOT / "wikidata_20260825/entities.json"
    wikidata = json.loads(wikidata_path.read_text(encoding="utf-8"))
    entities = wikidata.get("entities", {})
    if len(entities) != 14:
        raise ContractError("wrong declared row count: Wikidata entities")
    occurrence = 0
    for entity_id in sorted(entities):
        entity = entities[entity_id]
        c0, milk = WIKIDATA_CONTEXT[entity_id]
        documents.append({
            "dataset_snapshot_key": "wikidata.coffee-preparation-entities.20260825",
            "source_document_key": entity_id,
            "source_revision": entity.get("lastrevid"),
            "source_date": str(entity.get("modified", ""))[:10],
            "geography": "global_collaborative_source",
            "language": "multilingual",
            "raw_text": compact_json({"labels": entity.get("labels", {}), "aliases": entity.get("aliases", {})}),
            "raw_text_public_export_allowed": "true",
            "capture_method": "Wikidata Action API wbgetentities",
            "c0_candidate": c0,
            "c1_source_local": "not_applicable_lexical_source",
            "black_milk": milk,
            "sensory_method": "lexical_reference",
            "participant_type": "not_applicable",
        })
        for kind in ("label", "alias"):
            container = entity.get("labels" if kind == "label" else "aliases", {})
            for language in sorted(container, key=lambda item: (LANGUAGE_ORDER.get(item, 99), item)):
                values = [container[language]] if kind == "label" else container[language]
                for item in values:
                    phrase = str(item.get("value", "")).strip()
                    if not phrase:
                        continue
                    occurrence += 1
                    expression_key = f"wikidata.{entity_id}.{kind}.{language}.{occurrence:04d}"
                    expressions.append({
                        "expression_occurrence_key": expression_key,
                        "dataset_snapshot_key": "wikidata.coffee-preparation-entities.20260825",
                        "source_document_key": entity_id,
                        "language": language,
                        "raw_source_phrase": phrase,
                        "normalized_expression": normalize_expression(phrase),
                        "expression_role": "preparation_expression",
                        "candidate_canonical_mappings": compact_json([c0]),
                        "model_or_lexical_candidates": compact_json([{"source_entity": entity_id, "source_role": kind}]),
                        "review_state": "RESEARCH_REVIEWED" if c0.startswith("unresolved_") is False else "CANDIDATE",
                        "automatic_promotion_allowed": "false",
                        "regional_or_register_note": "Wikidata language tag retained; fallback, regional usage, and sensory equivalence require independent review.",
                    })
                    mappings.append({
                        "mapping_key": f"mapping.{expression_key}",
                        "raw_source_phrase": phrase,
                        "normalized_expression": normalize_expression(phrase),
                        "candidate_mapping": c0,
                        "evidence_key": f"wikidata:{entity_id}:{entity.get('lastrevid')}",
                        "lifecycle_status": "RESEARCH_REVIEWED" if not c0.startswith("unresolved_") else "CANDIDATE",
                        "mapping_scope": "preparation_candidate_only",
                        "ambiguity_note": "No automatic canonical promotion; entity membership is lexical evidence, not sensory truth.",
                    })

    usda_path = RAW_ROOT / "usda_fdc_20260825/coffee_search.json"
    usda = json.loads(usda_path.read_text(encoding="utf-8"))
    foods = usda.get("foods", [])
    union_fields = sorted({key for food in foods for key in food})
    if len(foods) != 50 or len(union_fields) != 18:
        raise ContractError("wrong declared row or field count: USDA FDC response")
    included = []
    for food in foods:
        description = str(food.get("description", ""))
        if not (description.startswith("Coffee,") or description.startswith("Frozen coffee drink")):
            continue
        included.append(food)
        fdc_id = str(food["fdcId"])
        c0, milk = usda_context(description)
        documents.append({
            "dataset_snapshot_key": "usda.fdc-coffee-search.fndds-2021-2023.20260825",
            "source_document_key": fdc_id,
            "source_revision": fdc_id,
            "source_date": food.get("publishedDate", ""),
            "geography": "United States",
            "language": "en",
            "raw_text": compact_json({"description": description, "additionalDescriptions": food.get("additionalDescriptions", "")}),
            "raw_text_public_export_allowed": "true",
            "capture_method": "USDA FoodData Central API foods/search; Survey (FNDDS)",
            "c0_candidate": c0,
            "c1_source_local": "not_reported",
            "black_milk": milk,
            "sensory_method": "consumer_food_description_lexical_reference",
            "participant_type": "not_applicable_aggregate_reference",
        })
        phrases = [("description", description)]
        phrases.extend(("additional_description", part.strip()) for part in str(food.get("additionalDescriptions", "")).split(";") if part.strip())
        for phrase_index, (role, phrase) in enumerate(phrases, start=1):
            expression_key = f"usda.{fdc_id}.{phrase_index:02d}"
            expressions.append({
                "expression_occurrence_key": expression_key,
                "dataset_snapshot_key": "usda.fdc-coffee-search.fndds-2021-2023.20260825",
                "source_document_key": fdc_id,
                "language": "en",
                "raw_source_phrase": phrase,
                "normalized_expression": normalize_expression(phrase),
                "expression_role": "preparation_expression" if role == "description" else "modifier_or_alias_expression",
                "candidate_canonical_mappings": compact_json([c0]),
                "model_or_lexical_candidates": compact_json([{"source_field": role}]),
                "review_state": "CANDIDATE",
                "automatic_promotion_allowed": "false",
                "regional_or_register_note": "US FNDDS food-description register; brand-like examples are source-local and not canonical labels.",
            })
    if len(included) != 32:
        raise ContractError("USDA inclusion rule did not yield the declared 32 records")

    profiles["wikidata.coffee-preparation-entities.20260825"] = {
        "raw_row_count": 14,
        "imported_record_count": 14,
        "exclusion_count": 0,
        "language_coverage": dict(sorted(Counter(row["language"] for row in expressions if row["dataset_snapshot_key"].startswith("wikidata")).items())),
        "preparation_coverage": dict(sorted(Counter(WIKIDATA_CONTEXT[key][0] for key in entities).items())),
        "quality_flags": ["community-edited labels and aliases are lexical evidence only", "language fallbacks and regional equivalence are not assumed"],
    }
    profiles["usda.fdc-coffee-search.fndds-2021-2023.20260825"] = {
        "raw_row_count": 50,
        "imported_record_count": 32,
        "exclusion_count": 18,
        "language_coverage": {"en": 32},
        "black_milk_coverage": dict(sorted(Counter(usda_context(str(food["description"]))[1] for food in included).items())),
        "quality_flags": ["search-page snapshot is source-concentrated to the first 50 sorted hits", "food descriptions are not specialty sensory observations", "18 non-beverage hits are retained only in raw source and excluded from derived corpus"],
    }
    return documents, expressions, mappings, profiles


def build_questions() -> list[dict[str, object]]:
    source = json.loads(QUESTION_PATH.read_text(encoding="utf-8"))
    if source.get("ordinary_user_validation_count") != 0 or source.get("information_gain_status") != "NOT_ESTIMABLE":
        raise ContractError("candidate question marked user-validated without evidence or information gain estimated")
    rows: list[dict[str, object]] = []
    logical = source.get("logical_questions", [])
    if len(logical) != 9:
        raise ContractError("Round 3E question source must contain exactly nine logical candidates")
    for question in logical:
        for language, version in question["versions"].items():
            lifecycle = version["lifecycle"]
            if lifecycle in {"COMPREHENSION_READY", "ACTIVE_FOR_CALIBRATION"}:
                raise ContractError("candidate question marked user-validated without evidence")
            rows.append({
                "question_version_key": f"round3e.{question['logical_question_code']}.{language.casefold().replace('-', '_')}",
                "logical_question_code": question["logical_question_code"],
                "language": language,
                "lifecycle_status": lifecycle,
                "target_distinction": question["target_distinction"],
                "eligible_c0_json": compact_json(question["eligible_c0"]),
                "eligible_c1_json": compact_json(question["eligible_c1"]),
                "candidate_region": question["candidate_region"],
                "prompt": version["prompt"],
                "answer_options_json": compact_json(version["options"]),
                "sensory_modality": question["sensory_modality"],
                "evidence_json": compact_json(question["evidence"]),
                "consumer_familiarity_assumptions": question["consumer_familiarity_assumptions"],
                "translation_notes": version["translation_notes"],
                "ambiguity": question["ambiguity"],
                "expected_information_role": question["expected_information_role"],
                "unresolved_concerns": question["unresolved_concerns"],
                "information_gain_status": "NOT_ESTIMABLE",
                "ordinary_user_validation_evidence": "",
            })
    return rows


def build_coverage(observations: list[dict[str, object]], documents: list[dict[str, object]]) -> list[dict[str, object]]:
    cells: Counter[tuple[str, ...]] = Counter()
    cells[("round2b.firstbloom.pinned-a6cb0026", "2383 source product identities", "not_systematically_coded", "not_systematically_coded", "not_systematically_coded", "commercial_tasting_note_corpus_not_controlled_sensory_observations", "not_applicable", "en")] = 2474
    cells[("dryad.cotter-black-coffee.v4", "one Honduras coffee source lot", "filter_percolation", "medium", "black", "consumer_CATA_JAR_liking_and_physical_measurements", "ordinary_user_consumer", "en")] = 3186
    cells[("dryad.yeager-acids-meta-analysis.v5", "heterogeneous literature coffee records", "multiple_source_local_preparations", "multiple_source_local_roasts", "black_and_three_milk_context_records", "chemical_meta_analysis_no_sensory_outcome", "not_applicable", "en")] = 1631
    cells[("mendeley.ftnir-specialty-coffee.v4.selected", "64 source samples", "not_reported", "roasted_source_local_no_level", "not_reported", "source_local_cup_quality_score", "assessor_details_not_reported", "not_applicable")] = 192
    cells[("mendeley.ftnir-specialty-coffee.v4.selected", "64 source samples", "not_reported", "green_and_roasted_source_rows_no_level", "not_reported", "source_local_sample_score_and_metadata", "assessor_details_not_reported", "not_applicable")] = 128
    cells[("mendeley.coffee-taste-sensitivity.v1", "study coffee not identified in workbook", "not_reported", "not_reported", "not_reported", "bitterness_taste_preference_purchase_response", "ordinary_user_or_consumer_as_source_described", "en")] = 93
    for document in documents:
        key = (
            str(document["dataset_snapshot_key"]), str(document["source_document_key"]), str(document["c0_candidate"]),
            str(document["c1_source_local"]), str(document["black_milk"]), str(document["sensory_method"]),
            str(document["participant_type"]), str(document["language"]),
        )
        cells[key] += 1
    rows = []
    for key, count in sorted(cells.items()):
        rows.append({
            "source": key[0], "coffee_identity": key[1], "c0_preparation": key[2], "c1_roast": key[3],
            "black_milk": key[4], "sensory_method": key[5], "participant_type": key[6], "language": key[7],
            "observed_record_count": count, "cell_status": "OBSERVED_SOURCE_LOCAL_EVIDENCE",
            "interpretation_limit": "Presence only; omitted combinations are not inferred empty and sources are not pooled.",
        })
    return rows


def main() -> int:
    global RAW_ROOT, MANIFEST_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()
    MANIFEST_PATH = args.manifest.resolve()
    RAW_ROOT = MANIFEST_PATH.parent

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    verify_manifest(manifest)
    observations, fields, profiles = build_excel_observations()
    documents, expressions, mappings, corpus_profiles = build_corpus()
    profiles.update(corpus_profiles)
    questions = build_questions()
    coverage = build_coverage(observations, documents)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(output_dir / "external_observations.tsv", ["dataset_snapshot_key", "source_file", "source_row_identity", "record_type", "raw_value_json", "parsed_value_json", "normalized_value_json", "normalization_rule", "exclusion_reason"], observations)
    write_tsv(output_dir / "external_field_dictionary.tsv", ["dataset_snapshot_key", "source_file", "source_local_column_name", "project_field_key", "source_local_unit", "normalization_rule"], fields)
    write_tsv(output_dir / "corpus_documents.tsv", ["dataset_snapshot_key", "source_document_key", "source_revision", "source_date", "geography", "language", "raw_text", "raw_text_public_export_allowed", "capture_method", "c0_candidate", "c1_source_local", "black_milk", "sensory_method", "participant_type"], documents)
    write_tsv(output_dir / "corpus_expressions.tsv", ["expression_occurrence_key", "dataset_snapshot_key", "source_document_key", "language", "raw_source_phrase", "normalized_expression", "expression_role", "candidate_canonical_mappings", "model_or_lexical_candidates", "review_state", "automatic_promotion_allowed", "regional_or_register_note"], expressions)
    write_tsv(output_dir / "lexical_mapping_candidates.tsv", ["mapping_key", "raw_source_phrase", "normalized_expression", "candidate_mapping", "evidence_key", "lifecycle_status", "mapping_scope", "ambiguity_note"], mappings)
    write_tsv(output_dir / "question_candidates.tsv", ["question_version_key", "logical_question_code", "language", "lifecycle_status", "target_distinction", "eligible_c0_json", "eligible_c1_json", "candidate_region", "prompt", "answer_options_json", "sensory_modality", "evidence_json", "consumer_familiarity_assumptions", "translation_notes", "ambiguity", "expected_information_role", "unresolved_concerns", "information_gain_status", "ordinary_user_validation_evidence"], questions)
    write_tsv(output_dir / "coverage_cube.tsv", ["source", "coffee_identity", "c0_preparation", "c1_roast", "black_milk", "sensory_method", "participant_type", "language", "observed_record_count", "cell_status", "interpretation_limit"], coverage)
    write_json(output_dir / "data_quality_profiles.json", profiles)

    ci_inventory = {
        "generator": "db/scripts/generate-round3e-artifacts.py",
        "source_manifest": "db/data/round3e/raw/SOURCE_MANIFEST.json",
        "question_source": "db/data/round3e/source/question_candidates.json",
        "generated_paths": sorted(
            f"db/data/round3e/generated/{path.name}"
            for path in output_dir.glob("*")
            if path.name not in {"artifact_manifest.json", "ci_inventory.json"}
        ),
        "required_gates": ["source_hashes", "declared_dimensions", "pii_scan", "rights_decision", "deterministic_generation", "canonical_format", "git_diff_clean"],
        "forbidden_runs": {"deep_learning": False, "embeddings": False, "pgvector": False, "ranking": False, "adaptive_policy": False},
    }
    write_json(output_dir / "ci_inventory.json", ci_inventory)

    generated = sorted(path for path in output_dir.glob("*") if path.name != "artifact_manifest.json")
    artifact_rows = []
    for path in generated:
        row_count = None
        if path.suffix == ".tsv":
            row_count = max(sum(1 for _ in path.open(encoding="utf-8")) - 1, 0)
        artifact_rows.append({"path": f"db/data/round3e/generated/{path.name}", "sha256": sha256(path), "row_count": row_count})
    snapshot_rows = []
    for snapshot in manifest["snapshots"]:
        snapshot_rows.append({
            "dataset_snapshot_key": snapshot["dataset_snapshot_key"],
            "source_version": snapshot["source_version"],
            "file_hashes": {item["path"]: item["sha256"] for item in snapshot["files"]},
            "row_count": snapshot["declared_row_count"],
            "field_count": snapshot["declared_field_count"],
            "import_version": manifest["import_version"],
            "import_code_sha": "RECORDED_BY_FORWARD_MIGRATION",
            "license": snapshot["license"],
            "rights_decision": snapshot["rights_decision"],
            "privacy_decision": snapshot["privacy_decision"],
            "created_at": manifest["capture_date"],
        })
    artifact_manifest = {
        "version": "round3e-artifact-manifest-v1",
        "artifacts": artifact_rows,
        "snapshots": snapshot_rows,
        "counts": {
            "imported_source_count": 4,
            "raw_snapshot_row_count": 477,
            "imported_record_count": len(observations) + len(documents),
            "exclusion_count": 18,
            "external_observation_count": len(observations),
            "corpus_document_count": len(documents),
            "corpus_expression_occurrence_count": len(expressions),
            "unique_normalized_expression_count": len({row["normalized_expression"] for row in expressions}),
            "lexical_mapping_count": len(mappings),
            "question_logical_candidate_count": len({row["logical_question_code"] for row in questions}),
            "question_language_version_count": len(questions),
            "question_user_validated_count": 0,
            "coverage_observed_cell_count": len(coverage),
        },
        "named_hashes": {
            "question_bank_hash": sha256(output_dir / "question_candidates.tsv"),
            "lexical_mapping_hash": sha256(output_dir / "lexical_mapping_candidates.tsv"),
            "coverage_cube_hash": sha256(output_dir / "coverage_cube.tsv"),
            "ci_inventory_hash": sha256(output_dir / "ci_inventory.json"),
            "data_quality_report_hash": sha256(output_dir / "data_quality_profiles.json"),
        },
    }
    write_json(output_dir / "artifact_manifest.json", artifact_manifest)
    print("ROUND3E_ARTIFACT_GENERATION_PASS=true")
    print(f"ROUND3E_IMPORTED_RECORD_COUNT={len(observations) + len(documents)}")
    print(f"ROUND3E_EXPRESSION_OCCURRENCE_COUNT={len(expressions)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as error:
        print(f"ROUND3E_ARTIFACT_GENERATION_PASS=false ERROR={error}", file=sys.stderr)
        raise SystemExit(1)
