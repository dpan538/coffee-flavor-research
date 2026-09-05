#!/usr/bin/env python3
"""Non-destructive attribution correction for the two acquired R3 studies.

Europe PMC carries author/editor roles on contrib-group content-type. This
addendum corrects derived metadata while preserving all frozen rows and fits.
"""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from admit_multiview_sources_r3 import RAW_HASHES
from external_construct_r3 import digest, save, sha


def attribution(root):
    authors, editors = [], []
    for group in root.findall(".//article-meta/contrib-group"):
        for person in group.findall("contrib"):
            role = person.attrib.get("contrib-type", group.attrib.get("content-type"))
            name = person.find("name")
            if name is None:
                continue
            parts = [name.findtext("given-names", ""), name.findtext("surname", "")]
            full = " ".join(p.strip() for p in parts if p.strip())
            if role == "author":
                authors.append(full)
            elif role == "editor":
                editors.append(full)
    dates = []
    for date in root.findall(".//article-meta/pub-date"):
        year, month, day = (date.findtext(k) for k in ("year", "month", "day"))
        dates.append({"date_type_as_source": dict(date.attrib), "year": int(year) if year else None,
                      "month": int(month) if month else None, "day": int(day) if day else None,
                      "iso_date": f"{int(year):04d}-{int(month):02d}-{int(day):02d}" if year and month and day else None})
    if not authors:
        raise ValueError("ACTUAL_SOURCE_AUTHOR_GROUP_REQUIRED")
    return {"authors": authors, "editors_not_authors": editors, "publication_dates": dates,
            "title": "".join(root.find(".//article-title").itertext()),
            "doi": next(e.text for e in root.findall(".//article-id") if e.attrib.get("pub-id-type") == "doi"),
            "license": "CC-BY-4.0", "license_url": "https://creativecommons.org/licenses/by/4.0/",
            "attribution_required": True, "modification": "EXACT_NATIVE_CELL_EXTRACTION_WITH_EXPLICIT_MASKS_AND_NAMESPACED_KEYS"}


def run(owner):
    private = Path(owner) / "revisions/r3"
    studies = {}
    for pmc, payload in [("PMC12817937", "castillo_grader_scores.private.json"), ("PMC12469716", "commercial_aroma_native_records.private.json")]:
        xml = private / "sources" / (pmc + ".xml")
        if sha(xml) != RAW_HASHES[xml.name]:
            raise ValueError("SOURCE_XML_HASH_CHANGED")
        package = json.loads((private / payload).read_text())
        studies[pmc] = {**attribution(ET.parse(xml).getroot()),
                        "article_url": "https://pmc.ncbi.nlm.nih.gov/articles/" + pmc + "/",
                        "applies_to_owner_relative_path": "revisions/r3/" + payload,
                        "preserved_payload_sha256": sha(private / payload), "preserved_records_sha256": digest(package["records"]),
                        "source_files": [r for r in package["source_manifest"]["source_files"] if pmc in r["owner_relative_path"]]}
    result = {"version": "m2-r3-native-source-attribution-addendum.v1", "studies": studies,
              "corrects": "EMPTY_DERIVED_AUTHOR_LIST_AND_CONCATENATED_DATE_STRING_FROM_CONTRIB_TYPE_ONLY_ADAPTER;READ_PARENT_GROUP_CONTENT_TYPE_AND_DATE_CHILDREN",
              "preservation": "NO_NATIVE_ROW_MASK_SCORE_SOURCE_FILE_PROTOCOL_MODEL_OR_EVALUATION_CHANGED",
              "model_refits": 0, "evaluation_reruns": 0, "code_sha256": sha(__file__)}
    path = private / "native_source_attribution_addendum.private.json"
    if path.exists():
        if json.loads(path.read_text()) != result:
            raise ValueError("PRESERVE_EXISTING_ATTRIBUTION_ADDENDUM")
    else:
        save(path, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-dir", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.owner_dir), ensure_ascii=False, indent=2, sort_keys=True))
