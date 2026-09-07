#!/usr/bin/env python3
"""Resolve licenses for already-admitted descriptor source families.

This is separate from the 13,952-row UNKNOWN pass: these sources already had
affirmative rights labels, but R10 requires a machine-readable license ID and
the source/API URL that supplied it before NON_COMMERCIAL_RESEARCH eligibility
can be computed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from license_resolution_r10 import normalize_license


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT
    / "db/data/backend-sequential-model-v2/revisions/r10/resolved_source_licenses.json"
)
USER_AGENT = "CoffeeFlavorResearch-R10/1.0 (noncommercial provenance audit)"


SOURCES = [
    {
        "source_family_id": "family.zenodo_golovinsky_q_grader_dataset",
        "method": "ZENODO_RECORD_API",
        "url": "https://zenodo.org/api/records/20840464",
        "historical_rights_basis": "CC_BY_NC_4_0_NONCOMMERCIAL_RESEARCH_ONLY",
    },
    {
        "source_family_id": "family.frontiers_inera_robusta_q_grader_panel",
        "method": "FIGSHARE_RECORD_API",
        "url": "https://api.figshare.com/v2/articles/25735122",
        "historical_rights_basis": "CC_BY_4_0_FIGSHARE_DATASET",
    },
    {
        "source_family_id": "family.frontiers_cenicafe_lengupa_trained_cuppers",
        "method": "CROSSREF_WORK_API",
        "url": "https://api.crossref.org/works/10.3389%2Ffsufs.2026.1809471",
        "historical_rights_basis": "CC_BY_FRONTIERS_ARTICLE",
    },
    {
        "source_family_id": "family.mdpi_certified_q_grader_storage_panel",
        "method": "CROSSREF_WORK_API",
        "url": "https://api.crossref.org/works/10.3390%2Ffoods15152756",
        "historical_rights_basis": "CC_BY_4_0_MDPI_ARTICLE_AND_SUPPLEMENT",
    },
    {
        "source_family_id": "family.pmc8774372_brewed_black_coffee",
        "method": "EUROPE_PMC_CORE_API",
        "url": (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            "?query=PMCID:PMC8774372&resultType=core&format=json"
        ),
        "historical_rights_basis": "CC_BY_4_0_ATTRIBUTION_REQUIRED",
    },
]


def fetch(url: str, timeout: float) -> tuple[dict[str, Any], str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    return json.loads(body.decode("utf-8")), hashlib.sha256(body).hexdigest()


def crossref(payload: dict[str, Any]) -> tuple[str | None, str, str, str | None]:
    message = payload["message"]
    raw_license = next(
        (row.get("URL", "") for row in message.get("license", []) if row.get("URL")), ""
    )
    title = next(iter(message.get("title", [])), "")
    authors = ", ".join(
        " ".join(filter(None, [row.get("given"), row.get("family")]))
        for row in message.get("author", [])
    )
    doi = message.get("DOI")
    citation = f"{authors}. {title}. {message.get('publisher', '')}. https://doi.org/{doi}"
    return normalize_license(raw_license), raw_license, citation, doi


def parse(source: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    method = source["method"]
    if method == "ZENODO_RECORD_API":
        raw_license = (payload.get("metadata", {}).get("license") or {}).get("id", "")
        creators = ", ".join(
            row.get("name", "") for row in payload.get("metadata", {}).get("creators", [])
        )
        title = payload.get("metadata", {}).get("title", "")
        doi = payload.get("doi")
        citation = f"{creators}. {title}. Zenodo. https://doi.org/{doi}"
        license_id = normalize_license(raw_license)
    elif method == "FIGSHARE_RECORD_API":
        license_row = payload.get("license") or {}
        raw_license = license_row.get("url") or license_row.get("name", "")
        citation = payload.get("citation", "")
        doi = payload.get("doi")
        license_id = normalize_license(raw_license)
    elif method == "CROSSREF_WORK_API":
        license_id, raw_license, citation, doi = crossref(payload)
    elif method == "EUROPE_PMC_CORE_API":
        results = payload.get("resultList", {}).get("result", [])
        result = results[0] if results else {}
        raw_license = result.get("license", "")
        doi = result.get("doi")
        citation = (
            f"{result.get('authorString', '')} {result.get('title', '')} "
            f"Europe PMC {result.get('pmcid', '')}; https://doi.org/{doi}"
        )
        license_id = normalize_license(raw_license)
    else:
        raise ValueError(f"unknown resolver method {method}")
    return {
        **source,
        "doi": doi,
        "raw_license": raw_license,
        "resolved_license": license_id,
        "attribution_string": citation.strip(),
        "attribution_complete": bool(citation.strip() and doi),
        "participant_pii_present": False,
        "share_alike_obligation": license_id in {"CC-BY-SA-4.0", "ODbL-1.0"},
        "historical_basis_differs_from_live_license": (
            source["source_family_id"] == "family.zenodo_golovinsky_q_grader_dataset"
            and license_id == "CC-BY-4.0"
            and "BY_NC" in source["historical_rights_basis"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    results = []
    for source in SOURCES:
        try:
            payload, response_sha = fetch(source["url"], args.timeout)
            result = parse(source, payload)
            result.update(
                {
                    "resolution_status": "RESOLVED"
                    if result["resolved_license"]
                    else "UNRESOLVED",
                    "response_sha256": response_sha,
                }
            )
        except Exception as exc:  # retained in the receipt; never grants eligibility
            result = {
                **source,
                "resolution_status": "UNRESOLVED",
                "resolved_license": None,
                "resolution_error": f"{type(exc).__name__}:{exc}",
                "attribution_complete": False,
                "participant_pii_present": False,
                "share_alike_obligation": False,
            }
        results.append(result)
    report = {
        "contract_version": "r10.admitted-source-license-resolution.v1",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_count": len(results),
        "resolved_source_count": sum(row["resolution_status"] == "RESOLVED" for row in results),
        "sources": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
