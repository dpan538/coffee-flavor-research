#!/usr/bin/env python3
"""Exact native-cell admission from two CC BY study supplements/tables.

No figure digitization, chemical-to-sensory truth conversion, or fabricated
individual records. Raw studies stay in owner storage outside public Git.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from external_construct_r3 import save, sha

VERSION = "m2-r3-castillo-commercial-native-admission.v1"
RAW_HASHES = {
    "PMC12817937.xml": "fa1cffb1cf5bf9ed2de44ffc43aa46e94ea00f98dd29a104ae8c8b2745abc57c",
    "PMC12817937.supplementary.zip": "74782f7d8aa9cf2625d4a998472e9ba3efb62c2912660232166413b839af1d98",
    "PMC12469716.xml": "c50109405a74e89caacfb0939851f76d95e43a28a0c54bcec1e16598782861ad",
    "PMC12469716.supplementary.zip": "493ccd677e265d5428c62f78eee5fd37e0e2e8355c5fa9553c328e9ef6eccbe2",
}
CASTILLO_FIELDS = ["aroma", "flavor", "residual_flavor", "acidity", "body", "uniformity", "balance", "clean_cup", "sweetness", "general"]
CASTILLO_TARGETS = CASTILLO_FIELDS[:5]
COFFEE_KEYS = ["GL", "MJ", "XF", "BS"]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


def text(element):
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def metadata(root, pmc):
    permissions = text(root.find(".//permissions"))
    if "Creative Commons Attribution" not in permissions or not ("4.0" in permissions):
        raise ValueError("EXPLICIT_CC_BY_4_LICENSE_REQUIRED")
    authors = [text(c.find("name")) for c in root.findall(".//article-meta/contrib-group/contrib") if c.attrib.get("contrib-type") == "author"]
    doi = next(a.text for a in root.findall(".//article-id") if a.attrib.get("pub-id-type") == "doi")
    return {"title": text(root.find(".//article-title")), "authors": authors, "doi": doi, "pmcid": pmc,
            "article_url": "https://pmc.ncbi.nlm.nih.gov/articles/" + pmc + "/", "license": "CC-BY-4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/", "source_permissions_text": permissions,
            "publication_dates_as_source": [text(x) for x in root.findall(".//article-meta/pub-date")],
            "attribution_required": True, "modification": "EXACT_TABLE_CELL_EXTRACTION_WITH_NAMESPACED_FIELDS_AND_EXPLICIT_MASKS",
            "raw_redistribution": "NOT_PERFORMED_PRIVATE_OWNER_STORAGE_ONLY"}


def parse_castillo(root, archive):
    with zipfile.ZipFile(archive) as z:
        docx_name = "msystems.01364-25-s0001.docx"
        with zipfile.ZipFile(io.BytesIO(z.read(docx_name))) as docx:
            document = ET.fromstring(docx.read("word/document.xml"))
    tables = document.findall(".//w:tbl", NS)
    records = []
    for table_index, condition in enumerate(["SW", "IW"]):
        table = [[text(cell) for cell in row.findall("w:tc", NS)] for row in tables[table_index].findall("w:tr", NS)]
        expected = ["Q-grader", "Aroma", "Flavor", "Residual flavor", "Acidity", "Body", "Uniformity", "Balance", "Clean cup", "Sweetness", "General"]
        if table[0] != expected or len(table) != 4:
            raise ValueError("EXACT_THREE_GRADER_TEN_SCORE_TABLE_REQUIRED")
        for row_index, row in enumerate(table[1:], 2):
            grader = row[0]
            if grader not in ("1", "2", "3") or len(row) != 11:
                raise ValueError("PUBLISHED_GRADER_ROW_REQUIRED")
            values = {field: float(value) for field, value in zip(CASTILLO_FIELDS, row[1:])}
            if any(not 1 <= v <= 10 for v in values.values()):
                raise ValueError("SOURCE_ONE_TO_TEN_CODE_RANGE")
            records.append({"record_id": f"castillo2025:grader:{grader}|{condition}", "grader_id": f"castillo2025:grader:{grader}",
                            "source_grader_code": grader, "condition_id": condition, "coffee_group_id": "castillo2025:single_farm_source_material",
                            "role": "AUX_COFFEE_WEAK_LABEL", "source_family": "madrid_restrepo_castillo_2025",
                            "source_native_scores": values, "score_masks": dict.fromkeys(CASTILLO_FIELDS, True),
                            "score_states": dict.fromkeys(CASTILLO_FIELDS, "OBSERVED"),
                            "model_target_mask": {f: f in CASTILLO_TARGETS for f in CASTILLO_FIELDS},
                            "source_cells": {field: {"archive_member": docx_name, "native_xml": "word/document.xml", "table_index_zero_based": table_index,
                                                     "row_one_based": row_index, "column_one_based": j + 2, "original_text": row[j + 1]}
                                             for j, field in enumerate(CASTILLO_FIELDS)},
                            "source_C0": "preparation.family.immersion", "source_C1": None,
                            "intensity_truth_mask": False, "quality_score_mask": True, "production_runtime_feature": False})
    if len(records) != 6 or len({r["record_id"] for r in records}) != 6:
        raise ValueError("THREE_BY_TWO_SOURCE_SHAPE_REQUIRED")
    return {"contract": {"version": VERSION, "source_id": "MADRID_RESTREPO_CASTILLO_2025", **metadata(root, "PMC12817937"),
                         "source_material_groups": 1, "fermentation_conditions": 2, "named_cupped_profiles": 2,
                         "certified_q_graders": 3, "individual_score_rows": 6, "individual_score_cells": 60,
                         "source_scale": "SOURCE_FEATURE_SCORES_1_TO_10_WITH_QUARTER_POINT_ENTRIES",
                         "scale_interpretation": "MIXED_SCA_STYLE_QUALITY_FEATURE_CODES;ARTICLE_ALSO_SAYS_INTENSITY;NO_CALIBRATED_INTENSITY_CLAIM",
                         "selected_task_fields": CASTILLO_TARGETS, "excluded_from_model_fields": CASTILLO_FIELDS[5:],
                         "material_identity": "SAME_FARM_VARIETY_CASTILLO;ONE_CONSERVATIVE_MATERIAL_GROUP;RAW_LOT_IDENTIFIER_NOT_PROVIDED",
                         "biological_tank_replicates": "ARTICLE_REPORTS_INDEPENDENT_TANKS_FOR_OMICS;NO_INDIVIDUAL_SENSORY_TANK_LINKS_OR_EXTRA_COFFEE_IDS_IN_SCORE_TABLE",
                         "chemistry_join": "SUPPLEMENT_HAS_GROUP_DIFFERENTIAL_FOLD_CHANGES_ONLY;NO_SAMPLE_MATCHED_ABUNDANCE_MATRIX;NO_FABRICATED_JOIN",
                         "descriptors": "NARRATIVE_NOT_CONVERTED_TO_SIGNED_TARGETS",
                         "coffee_holdout": "NOT_ESTIMABLE_ONE_MATERIAL", "real_user_alignment": "NOT_EVALUATED",
                         "main_M2_scoring_eligible": False}, "records": records}


def table_rows(root, table_id):
    wrapper = root.find('.//table-wrap[@id="' + table_id + '"]')
    table = wrapper.find("table")
    rows = []
    for row in table.findall(".//tr"):
        cells = [text(c) for c in row if c.tag in ("td", "th")]
        if cells:
            rows.append(cells)
    return rows, text(wrapper.find("table-wrap-foot"))


def mean_sd_cell(raw):
    if raw.startswith("ND"):
        return {"mean": None, "sd": None, "mask": False, "state": "NOT_DETECTED_UNQUANTIFIED_NOT_ZERO", "raw": raw}
    if raw == "-":
        return {"mean": None, "sd": None, "mask": False, "state": "SOURCE_DASH_UNREPORTED_NOT_ZERO", "raw": raw}
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*±\s*([0-9]+(?:\.[0-9]+)?)(?:\s*[a-z]+)?", raw)
    if match:
        return {"mean": float(match[1]), "sd": float(match[2]), "mask": True, "state": "OBSERVED_PUBLISHED_MEAN_SD", "raw": raw}
    if raw == "0":
        return {"mean": 0.0, "sd": None, "mask": True, "state": "SOURCE_ROUNDED_ZERO_NO_ABSENCE_CLAIM", "raw": raw}
    raise ValueError("UNRECOGNIZED_NATIVE_MEAN_SD:" + raw)


def parse_commercial(root):
    products = [{"coffee_id": code, "record_id": "chen2025:coffee:" + code, "source_family": "chen_commercial_aroma_2025",
                 "source_product_name": name, "role": "AUX_COFFEE_WEAK_LABEL", "QDA_values": None, "QDA_mask": False,
                 "chemical_cells": {}, "AEDA_FD_cells": {}, "source_C0": None, "source_C1": None}
                for code, name in zip(COFFEE_KEYS, ["Colombia", "Bench Maji", "Yirgacheffe", "Baoshan"])]
    chemistry_long, fd_long, issues = [], [], []
    for table_id, unit, first_column, expected_cols in [("foods-14-03192-t001", "CIELAB_NATIVE_COORDINATE", 1, 5),
                                                       ("foods-14-03192-t002", "mg/g", 1, 5),
                                                       ("foods-14-03192-t004", "microgram/g", 2, 11)]:
        rows, foot = table_rows(root, table_id)
        for row_index, row in enumerate(rows, 1):
            if len(row) != expected_cols or "GL" in row or row[0] in ("Compounds", "CIELAB Color Space"):
                continue
            for j, product in enumerate(products):
                value = mean_sd_cell(row[first_column + j])
                key = table_id + "|" + row[0]
                cell = {**value, "compound_or_measurement": row[0], "unit": unit, "source_table": table_id,
                        "source_row_one_based": row_index, "source_column_one_based": first_column + j + 1}
                product["chemical_cells"][key] = cell
                chemistry_long.append({"coffee_id": product["coffee_id"], **cell})
                if table_id.endswith("t004") and value["state"] == "SOURCE_ROUNDED_ZERO_NO_ABSENCE_CLAIM":
                    issues.append({"coffee_id": product["coffee_id"], "compound": row[0], "issue": "SOURCE_CONCENTRATION_PRINTED_ZERO_WITH_POSITIVE_REPORTED_OAV;RETAIN_LITERAL_VALUE_DO_NOT_INFER_ABSENCE"})
    rows, foot = table_rows(root, "foods-14-03192-t003")
    for row_index, row in enumerate(rows, 1):
        if len(row) != 9 or row[0] == "Compounds":
            continue
        for j, product in enumerate(products):
            raw = row[4 + j]
            if raw != "-" and (not raw.isdigit() or int(raw) not in [3 ** k for k in range(8)]):
                raise ValueError("SOURCE_SERIAL_THREE_DILUTION_CODE_REQUIRED:" + raw)
            cell = {"compound": row[0], "source_odor_description": row[1], "FD": int(raw) if raw != "-" else None,
                    "mask": raw != "-", "state": "OBSERVED_GC_O_DILUTION_ENDPOINT" if raw != "-" else "SOURCE_DASH_UNREPORTED_NOT_ZERO",
                    "raw": raw, "source_table": "foods-14-03192-t003", "source_row_one_based": row_index, "source_column_one_based": 5 + j,
                    "not_cup_sensory_intensity": True, "identification_methods_as_source": row[-1]}
            if row[0] in product["AEDA_FD_cells"]:
                raise ValueError("DUPLICATE_NATIVE_COMPOUND_NAME")
            product["AEDA_FD_cells"][row[0]] = cell
            fd_long.append({"coffee_id": product["coffee_id"], **cell})
    return {"contract": {"version": VERSION, "source_id": "CHEN_COMMERCIAL_COFFEE_AROMA_2025", **metadata(root, "PMC12469716"),
                         "published_products": 4, "individual_sensory_records_obtained": 0,
                         "source_reported_QDA_panel_size": 18, "QDA_target_fields": ["roasted", "fruity", "caramel", "smoky", "woody", "chocolate", "nutty", "floral"],
                         "QDA_source_scale": "0_NOT_PERCEIVABLE_TO_10_STRONGLY_PERCEIVABLE", "QDA_numeric_cells_obtained": 0,
                         "QDA_status": "FIGURE_ONLY_NOT_DIGITIZED;ALL_EIGHT_SUPPLEMENT_PAGES_INSPECTED_NO_QDA_TABLE",
                         "source_reporting_issue": "METHOD_SAYS_SEVEN_ATTRIBUTES_BUT_NAMES_EIGHT;PRESERVE_EIGHT_NAMES_NO_INVENTED_COLUMN",
                         "aggregate_unit": "FOUR_SOURCE_PRODUCTS;MEAN_SD_TECHNICAL_EXPERIMENTS_ARE_NOT_EXTRA_COFFEES_OR_PEOPLE",
                         "chemistry_AEDA_pair_key": "NATIVE_GL_MJ_XF_BS_PRODUCT_CODES_ONLY;COMPOUND_NAMES_NOT_FORCED_NORMALIZED",
                         "AEDA_endpoint": "HIGHEST_REPORTED_THREEFOLD_DILUTION_GC_O_DETECTION;NO_CUP_INTENSITY_OR_HUMAN_RESPONSE_MATRIX",
                         "AEDA_dash": "UNREPORTED_OR_UNDETECTED_AMBIGUOUS;MASK_FALSE_NOT_ZERO",
                         "chemical_ND": "NOT_DETECTED_NO_QUANTIFIED_ZERO", "OAV": "DERIVED_CONCENTRATION_OVER_EXTERNAL_ODOR_THRESHOLD_NOT_INDEPENDENT_TARGET",
                         "main_M2_scoring_eligible": False, "professional_profile_alignment_eligible": False,
                         "admission_role": "AUX_LAB_CHEMISTRY_AND_GC_O_RECORDED_ENDPOINTS_ONLY_NO_CUP_PROFILE_FIT"},
            "records": products, "chemical_observations": chemistry_long, "AEDA_observations": fd_long, "source_issues": issues}


def run(owner):
    private = Path(owner) / "revisions/r3"
    source = private / "sources"
    for name, expected in RAW_HASHES.items():
        if sha(source / name) != expected:
            raise ValueError("ASSIGNED_SOURCE_HASH_MISMATCH:" + name)
    castillo = parse_castillo(ET.parse(source / "PMC12817937.xml").getroot(), source / "PMC12817937.supplementary.zip")
    commercial = parse_commercial(ET.parse(source / "PMC12469716.xml").getroot())
    manifest = {"version": VERSION, "source_files": [{"owner_relative_path": "revisions/r3/sources/" + name, "sha256": value,
                "download_url": "https://www.ebi.ac.uk/europepmc/webservices/rest/" + name.split(".")[0] + ("/fullTextXML" if name.endswith(".xml") else "/supplementaryFiles")} for name, value in RAW_HASHES.items()]}
    for name, package in [("castillo_grader_scores.private.json", castillo), ("commercial_aroma_native_records.private.json", commercial)]:
        package["source_manifest"] = manifest
        path = private / name
        if path.exists() and json.loads(path.read_text()) != package:
            raise ValueError("PRESERVE_EXISTING_ADMISSION_PAYLOAD")
        if not path.exists():
            save(path, package)
    summary = {"version": VERSION, "raw_files_downloaded": 4, "all_source_licenses": "CC-BY-4.0", "castillo": {"role": "AUX_RECORDED_MIXED_QUALITY_GRADER_SCORES",
               "material_groups": 1, "conditions": 2, "actual_people": 3, "individual_rows": 6, "native_cells": 60, "eligible_proxy_fields": CASTILLO_TARGETS,
               "profile_intensity_eligible": False, "owner_relative_path": "revisions/r3/castillo_grader_scores.private.json", "sha256": sha(private / "castillo_grader_scores.private.json")},
               "commercial": {"role": "AUX_LAB_CHEMISTRY_AND_GC_O_ENDPOINTS", "products": 4, "individual_sensory_records": 0,
               "exact_QDA_cells": 0, "analytical_cells_total_including_color": len(commercial["chemical_observations"]),
               "analytical_cells_observed_including_color": sum(r["mask"] for r in commercial["chemical_observations"]),
               "color_cells_total": sum(r["source_table"].endswith("t001") for r in commercial["chemical_observations"]),
               "chemical_cells_total": sum(not r["source_table"].endswith("t001") for r in commercial["chemical_observations"]),
               "chemical_cells_observed": sum(r["mask"] and not r["source_table"].endswith("t001") for r in commercial["chemical_observations"]),
               "AEDA_cells_total": len(commercial["AEDA_observations"]), "AEDA_cells_observed": sum(r["mask"] for r in commercial["AEDA_observations"]),
               "source_issue_count": len(commercial["source_issues"]), "owner_relative_path": "revisions/r3/commercial_aroma_native_records.private.json", "sha256": sha(private / "commercial_aroma_native_records.private.json")},
               "new_cup_intensity_sources_admitted": 0, "new_auxiliary_recorded_score_sources": 1, "new_auxiliary_lab_sources": 1, "main_M2_scoring_changed": False}
    save(private / "admitted_multiview_sources_public_summary.private.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.owner_dir), indent=2, sort_keys=True))
