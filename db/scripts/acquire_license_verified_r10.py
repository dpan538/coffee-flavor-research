#!/usr/bin/env python3
"""Run the bounded, license-filtered R10 discovery enhancement.

The GO gate is already evaluated from admitted sources.  This script records
metadata-only candidates from the required APIs and admits no supervision unless
a later source-specific table adapter can prove sample × descriptor structure.
Author emails and participant data are not retained.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from license_resolution_r10 import ALLOWED, normalize_license


ROOT = Path(__file__).resolve().parents[2]
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
DEFAULT_OUTPUT = R10 / "acquisition_manifest.json"
USER_AGENT = "CoffeeFlavorResearch-R10/1.0 (noncommercial license-filtered discovery)"

DRYAD_QUERIES = [
    "coffee sensory",
    "coffee cupping",
    "coffee descriptive analysis",
    "Coffea arabica sensory",
    "coffee flavor panel",
    "coffee QDA CATA",
]
EPMC_QUERIES = [
    'coffee AND (sensory OR cupping OR "descriptive analysis" OR CATA OR QDA)',
    '"Coffea arabica" AND descriptor',
    'coffee AND "flavor profile" AND panel',
]


def relevant(title: str) -> bool:
    value = title.lower()
    return any(token in value for token in ("coffee", "coffea")) and any(
        token in value
        for token in (
            "sensory",
            "cupping",
            "flavor",
            "flavour",
            "descriptive",
            "cata",
            "qda",
            "aroma",
            "taste",
        )
    )


def fetch(url: str, timeout: float) -> tuple[dict[str, Any], str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    return json.loads(body.decode("utf-8")), hashlib.sha256(body).hexdigest()


def add_candidate(
    candidates: dict[str, dict[str, Any]],
    source: str,
    identifier: str,
    title: str,
    doi: str | None,
    license_value: str,
    source_url: str,
    query_id: str,
) -> None:
    if not relevant(title):
        return
    license_id = normalize_license(license_value)
    if license_id not in ALLOWED or "-ND-" in (license_id or ""):
        return
    key = doi or f"{source}:{identifier}"
    row = candidates.setdefault(
        key,
        {
            "candidate_id": key,
            "source_system": source,
            "source_record_id": identifier,
            "doi": doi,
            "title": title,
            "resolved_license": license_id,
            "license_source_url": source_url,
            "disposition": "DISCOVERY_CANDIDATE_REQUIRES_SAMPLE_DESCRIPTOR_TABLE_ADAPTER",
            "query_ids": [],
        },
    )
    row["query_ids"] = sorted(set(row["query_ids"]) | {query_id})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()
    queries = []
    candidates: dict[str, dict[str, Any]] = {}

    def execute(query_id: str, system: str, url: str) -> dict[str, Any] | None:
        row = {"query_id": query_id, "source_system": system, "url": url}
        try:
            payload, digest = fetch(url, args.timeout)
            row.update({"status": "COMPLETE", "response_sha256": digest})
            queries.append(row)
            return payload
        except Exception as exc:
            row.update({"status": "ERROR", "error": f"{type(exc).__name__}:{exc}"})
            queries.append(row)
            return None

    for index, value in enumerate(DRYAD_QUERIES, 1):
        query_id = f"DRYAD_{index}"
        url = f"https://datadryad.org/api/v2/search?{urlencode({'q': value, 'per_page': 100})}"
        payload = execute(query_id, "DRYAD", url)
        if not payload:
            continue
        for item in payload.get("_embedded", {}).get("stash:datasets", []):
            doi = item.get("identifier", "").removeprefix("doi:") or None
            add_candidate(
                candidates,
                "DRYAD",
                str(item.get("id", "")),
                item.get("title", ""),
                doi,
                item.get("license", ""),
                item.get("sharingLink") or url,
                query_id,
            )

    license_filter = '(LICENSE:"cc by" OR LICENSE:"cc by-nc" OR LICENSE:"cc by-sa" OR LICENSE:cc0)'
    for index, value in enumerate(EPMC_QUERIES, 1):
        query_id = f"EUROPE_PMC_{index}"
        query = f"OPEN_ACCESS:Y AND {license_filter} AND ({value})"
        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
            + urlencode({"query": query, "resultType": "core", "format": "json", "pageSize": 1000})
        )
        payload = execute(query_id, "EUROPE_PMC", url)
        if not payload:
            continue
        for item in payload.get("resultList", {}).get("result", []):
            if item.get("isOpenAccess") != "Y":
                continue
            identifier = item.get("pmcid") or item.get("id") or ""
            source_url = (
                "https://www.ebi.ac.uk/europepmc/webservices/rest/"
                f"PMC/{item.get('pmcid')}/fullTextXML"
            )
            add_candidate(
                candidates,
                "EUROPE_PMC",
                identifier,
                item.get("title", ""),
                item.get("doi"),
                item.get("license", ""),
                source_url,
                query_id,
            )

    for license_value in ("cc-by", "cc0"):
        query_id = f"OPENALEX_{license_value.upper()}"
        filter_value = (
            "title_and_abstract.search:coffee sensory,"
            f"best_oa_location.license:{license_value}"
        )
        url = "https://api.openalex.org/works?" + urlencode(
            {"filter": filter_value, "per-page": 200}
        )
        payload = execute(query_id, "OPENALEX", url)
        if not payload:
            continue
        for item in payload.get("results", []):
            location = item.get("best_oa_location") or {}
            doi = (item.get("doi") or "").removeprefix("https://doi.org/") or None
            add_candidate(
                candidates,
                "OPENALEX",
                item.get("id", ""),
                item.get("title", ""),
                doi,
                location.get("license") or "",
                location.get("landing_page_url") or item.get("id", ""),
                query_id,
            )

    query_id = "ZENODO_1"
    url = "https://zenodo.org/api/records?" + urlencode(
        {"q": "coffee sensory AND access_right:open", "size": 25}
    )
    payload = execute(query_id, "ZENODO", url)
    if payload:
        for item in payload.get("hits", {}).get("hits", []):
            metadata = item.get("metadata", {})
            license_row = metadata.get("license") or {}
            add_candidate(
                candidates,
                "ZENODO",
                str(item.get("id", "")),
                metadata.get("title", ""),
                item.get("doi"),
                license_row.get("id", ""),
                item.get("links", {}).get("self_html") or item.get("links", {}).get("self", ""),
                query_id,
            )

    result_rows = sorted(candidates.values(), key=lambda row: row["candidate_id"])
    report = {
        "contract_version": "r10.license-filtered-acquisition-manifest.v1",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gate_dependency": "ENHANCEMENT_NOT_PREREQUISITE_GATE_ALREADY_GO",
        "queries": queries,
        "query_count": len(queries),
        "license_filtered_discovery_candidate_count": len(result_rows),
        "discovery_candidates": result_rows,
        "new_records": [],
        "new_record_count": 0,
        "reason_no_new_records": (
            "Metadata discovery cannot establish sample-by-descriptor supervision; "
            "no record is admitted without a source-specific table adapter and duplicate audit."
        ),
        "excluded_source_classes_unchanged": [
            "SCA_WCR_ND_OR_PERSONAL_DOWNLOAD",
            "COFFEE_REVIEW_DERIVED",
            "FIRSTBLOOM",
            "GREAT_AMERICAN_COFFEE_TEST",
            "COMMERCIAL_ROASTER_TASTING_NOTES",
        ],
        "participant_or_subjective_training_data_acquired": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "query_count": len(queries),
                "query_errors": sum(row["status"] != "COMPLETE" for row in queries),
                "license_filtered_discovery_candidate_count": len(result_rows),
                "new_record_count": 0,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
