#!/usr/bin/env python3
"""Resolve the 20k snapshot's UNKNOWN rights records without changing source data.

The resolver works at unique source URL/DOI level, then emits one outcome for
each of the 13,952 historical UNKNOWN assertions.  It accepts only explicit
license metadata returned by the source page or the requested DOI registries.
Public accessibility, site ownership, and hosting-platform defaults are never
treated as a license.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT
    / "db/data/backend-sequential-model-v2/revisions/r10/license_resolution_report.json"
)
DEFAULT_CACHE = Path("/private/tmp/coffee-flavor-r10-license-cache")
LEDGER_PATH = "db/data/current/CLEANED_DESCRIPTOR_ASSERTION_LEDGER.tsv"
SOURCE_PATH = "db/data/professional-descriptor-staging/PUBLIC_SAFE_ASSERTION_SIDECAR.tsv"
EXPECTED_UNKNOWN = 13_952
USER_AGENT = "CoffeeFlavorResearch-R10/1.0 (noncommercial provenance audit)"

ALLOWED = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-3.0",
    "CC-BY-SA-4.0",
    "CC-BY-NC-4.0",
    "ODbL-1.0",
    "EXPLICIT-NONCOMMERCIAL-RESEARCH-TDM",
}
SHARE_ALIKE = {"CC-BY-SA-4.0", "ODbL-1.0"}


def git_or_file_text(relative_path: str) -> str:
    path = ROOT / relative_path
    if path.exists():
        return path.read_text(encoding="utf-8")
    proc = subprocess.run(
        ["git", "show", f"HEAD:{relative_path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def tsv_rows(relative_path: str) -> tuple[list[dict[str, str]], str]:
    text = git_or_file_text(relative_path)
    return list(csv.DictReader(io.StringIO(text), delimiter="\t")), hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


class LicenseHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "link" and "license" in values.get("rel", "").lower():
            if values.get("href"):
                self.candidates.append(
                    {"value": values["href"], "field": "link[rel=license]"}
                )
        if tag.lower() == "meta":
            key = (values.get("name") or values.get("property") or "").lower()
            if "license" in key or key in {"dcterms.rights", "dc.rights"}:
                if values.get("content"):
                    self.candidates.append(
                        {"value": values["content"], "field": f"meta[{key}]"}
                    )


def normalize_license(value: str) -> str | None:
    token = value.strip().lower().replace("_", "-")
    token = re.sub(r"\s+", " ", token)
    if not token:
        return None
    if (
        "creativecommons.org/publicdomain/zero/1.0" in token
        or "spdx.org/licenses/cc0-1.0" in token
        or token in {
        "cc0",
        "cc0-1.0",
        }
    ):
        return "CC0-1.0"
    if "opendatacommons.org/licenses/odbl/1" in token or "odbl-1.0" in token:
        return "ODbL-1.0"
    if "by-nc-nd" in token or "by-nd" in token:
        version = "4.0" if "4.0" in token else "UNSPECIFIED"
        return f"CC-BY-NC-ND-{version}" if "by-nc-nd" in token else f"CC-BY-ND-{version}"
    if "creativecommons.org/licenses/by-nc/4.0" in token or token in {
        "cc-by-nc",
        "cc-by-nc-4.0",
        "cc by-nc",
        "cc by nc",
        "cc by-nc 4.0",
    }:
        return "CC-BY-NC-4.0"
    if "creativecommons.org/licenses/by-sa/4.0" in token or token in {
        "cc-by-sa",
        "cc-by-sa-4.0",
        "cc by-sa",
        "cc by sa",
        "cc by-sa 4.0",
    }:
        return "CC-BY-SA-4.0"
    if "creativecommons.org/licenses/by/4.0" in token or token in {
        "cc-by",
        "cc-by-4.0",
        "cc by",
        "cc by 4.0",
    }:
        return "CC-BY-4.0"
    if "creativecommons.org/licenses/by/3.0" in token or token == "cc-by-3.0":
        return "CC-BY-3.0"
    return None


def request_bytes(url: str, timeout: float) -> tuple[bytes, dict[str, str], str, int]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
        headers = {key.lower(): value for key, value in response.headers.items()}
        return body, headers, response.geturl(), response.status


def cache_path(cache_dir: Path, url: str) -> Path:
    return cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"


def fetch_json(url: str, timeout: float) -> dict[str, Any]:
    body, _, _, _ = request_bytes(url, timeout)
    return json.loads(body.decode("utf-8"))


def resolve_doi(doi: str, timeout: float) -> dict[str, Any]:
    endpoints = {
        "CROSSREF": f"https://api.crossref.org/works/{quote(doi, safe='')}",
        "OPENALEX": f"https://api.openalex.org/works/doi:{quote(doi, safe='')}",
        "EUROPE_PMC": (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            f"?query=DOI:{quote(doi, safe='')}&resultType=core&format=json"
        ),
    }
    evidence: list[dict[str, Any]] = []
    for method, endpoint in endpoints.items():
        try:
            payload = fetch_json(endpoint, timeout)
            values: list[str] = []
            if method == "CROSSREF":
                values = [row.get("URL", "") for row in payload.get("message", {}).get("license", [])]
            elif method == "OPENALEX":
                work = payload
                values = [
                    (work.get("best_oa_location") or {}).get("license") or "",
                    *[(row or {}).get("license") or "" for row in work.get("locations", [])],
                ]
            else:
                results = payload.get("resultList", {}).get("result", [])
                values = [row.get("license", "") for row in results]
            for value in values:
                if value:
                    evidence.append(
                        {
                            "method": method,
                            "resolution_url": endpoint,
                            "raw_license": value,
                            "normalized_license": normalize_license(value),
                        }
                    )
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            evidence.append(
                {"method": method, "resolution_url": endpoint, "error": type(exc).__name__}
            )
    return choose_resolution(evidence, doi=doi)


def license_restrictiveness(license_id: str) -> int:
    if "-ND-" in license_id:
        return 100
    return {
        "CC-BY-NC-4.0": 50,
        "CC-BY-SA-4.0": 40,
        "ODbL-1.0": 40,
        "CC-BY-4.0": 30,
        "CC-BY-3.0": 30,
        "CC0-1.0": 10,
    }.get(license_id, 90)


def choose_resolution(evidence: list[dict[str, Any]], doi: str | None = None) -> dict[str, Any]:
    normalized = sorted(
        {row["normalized_license"] for row in evidence if row.get("normalized_license")},
        key=license_restrictiveness,
        reverse=True,
    )
    chosen = normalized[0] if normalized else None
    chosen_row = next(
        (row for row in evidence if row.get("normalized_license") == chosen), None
    )
    return {
        "doi": doi,
        "resolved_license": chosen,
        "resolution_method": chosen_row.get("method") if chosen_row else "UNRESOLVED",
        "resolution_source_url": chosen_row.get("resolution_url") if chosen_row else None,
        "license_evidence": evidence,
        "resolver_disagreement": len(normalized) > 1,
        "owner_review_required": len(normalized) > 1,
        "noncommercial_research_license_allowed": chosen in ALLOWED,
        "share_alike_obligation": chosen in SHARE_ALIKE,
    }


def resolve_landing_page(
    url: str,
    cache_dir: Path,
    timeout: float,
    retries: int,
    request_delay: float,
) -> dict[str, Any]:
    cached = cache_path(cache_dir, url)
    if cached.exists():
        cached_result = json.loads(cached.read_text(encoding="utf-8"))
        if not cached_result.get("fetch_error"):
            return cached_result
    started = time.time()
    result: dict[str, Any]
    body: bytes | None = None
    headers: dict[str, str] = {}
    final_url: str | None = None
    status: int | None = None
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            body, headers, final_url, status = request_bytes(url, timeout)
            last_error = None
            if request_delay:
                time.sleep(request_delay)
            break
        except HTTPError as exc:
            last_error = exc
            if exc.code != 429 or attempt >= retries:
                break
            retry_after = float(exc.headers.get("Retry-After", "0") or 0)
            time.sleep(max(retry_after, request_delay, 1.0) * (attempt + 1))
        except (URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(max(request_delay, 0.5) * (attempt + 1))
    try:
        if body is None or final_url is None or status is None:
            assert last_error is not None
            raise last_error
        content_type = headers.get("content-type", "")
        evidence: list[dict[str, Any]] = []
        header_link = headers.get("link", "")
        for target in re.findall(r"<([^>]+)>;\s*rel=\"?license\"?", header_link, re.I):
            evidence.append(
                {
                    "method": "HTTP_LINK_LICENSE",
                    "resolution_url": final_url,
                    "raw_license": target,
                    "normalized_license": normalize_license(target),
                }
            )
        if "html" in content_type.lower() or body.lstrip().startswith(b"<"):
            parser = LicenseHTMLParser()
            parser.feed(body.decode("utf-8", errors="replace"))
            for candidate in parser.candidates:
                raw = urljoin(final_url, candidate["value"])
                evidence.append(
                    {
                        "method": "LANDING_PAGE_METADATA",
                        "field": candidate["field"],
                        "resolution_url": final_url,
                        "raw_license": raw,
                        "normalized_license": normalize_license(raw),
                    }
                )
        result = {
            **choose_resolution(evidence),
            "requested_url": url,
            "final_url": final_url,
            "http_status": status,
            "content_type": content_type,
            "response_sha256": hashlib.sha256(body).hexdigest(),
            "response_byte_count": len(body),
            "elapsed_seconds": round(time.time() - started, 3),
        }
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        result = {
            **choose_resolution([]),
            "requested_url": url,
            "final_url": None,
            "http_status": getattr(exc, "code", None),
            "content_type": None,
            "response_sha256": None,
            "response_byte_count": 0,
            "elapsed_seconds": round(time.time() - started, 3),
            "fetch_error": f"{type(exc).__name__}:{exc}",
        }
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return result


def extract_doi(*values: str) -> str | None:
    for value in values:
        match = re.search(r"\b(10\.\d{4,9}/[^\s?#]+)", value or "", re.I)
        if match:
            return match.group(1).rstrip(".,);]").lower()
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--request-delay", type=float, default=0.0)
    args = parser.parse_args()

    ledger, ledger_sha = tsv_rows(LEDGER_PATH)
    source_rows, source_sha = tsv_rows(SOURCE_PATH)
    source_by_id = {row["descriptor_assertion_id"]: row for row in source_rows}
    unknown = [row for row in ledger if row.get("rights_state") == "UNKNOWN"]
    if len(unknown) != EXPECTED_UNKNOWN:
        raise SystemExit(f"expected {EXPECTED_UNKNOWN} UNKNOWN rows, found {len(unknown)}")

    prepared: list[dict[str, Any]] = []
    for row in unknown:
        source = source_by_id.get(row["source_descriptor_assertion_id"], {})
        locator = row.get("source_locator", "")
        source_url = source.get("source_url") or (locator if locator.startswith("http") else "")
        doi = extract_doi(source_url, source.get("edition_or_release", ""), locator)
        prepared.append({"row": row, "source": source, "source_url": source_url, "doi": doi})

    unique_dois = sorted({item["doi"] for item in prepared if item["doi"]})
    doi_results = {doi: resolve_doi(doi, args.timeout) for doi in unique_dois}
    unique_urls = sorted(
        {item["source_url"] for item in prepared if item["source_url"] and not item["doi"]}
    )
    page_results: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(
                resolve_landing_page,
                url,
                args.cache_dir,
                args.timeout,
                args.retries,
                args.request_delay,
            ): url
            for url in unique_urls
        }
        for future in as_completed(futures):
            page_results[futures[future]] = future.result()

    outcomes: list[dict[str, Any]] = []
    for item in prepared:
        row = item["row"]
        source = item["source"]
        resolution = (
            doi_results[item["doi"]]
            if item["doi"]
            else page_results.get(item["source_url"], choose_resolution([]))
        )
        license_id = resolution.get("resolved_license")
        attribution_complete = bool(source.get("publisher") or row.get("source_family_id")) and bool(
            item["source_url"]
        )
        participant_pii_present = False
        eligible = bool(
            license_id in ALLOWED
            and attribution_complete
            and not participant_pii_present
            and not resolution.get("owner_review_required")
        )
        outcomes.append(
            {
                "assertion_id": row["cleaned_descriptor_assertion_id"],
                "source_assertion_id": row["source_descriptor_assertion_id"],
                "source_family_id": row["source_family_id"],
                "source_route_id": row["source_route_id"],
                "source_artifact_id": row["source_artifact_id"],
                "effective_record_id": row["effective_record_id"],
                "coffee_identity_id": row["coffee_identity_id"],
                "semantic_class": row["semantic_class"],
                "original_rights_status": "UNKNOWN",
                "source_url": item["source_url"] or None,
                "doi": item["doi"],
                "resolved_license": license_id,
                "resolution_status": "RESOLVED" if license_id else "UNKNOWN_UNRESOLVED",
                "resolution_method": resolution.get("resolution_method"),
                "resolution_source_url": resolution.get("resolution_source_url"),
                "resolver_disagreement": resolution.get("resolver_disagreement", False),
                "owner_review_required": resolution.get("owner_review_required", False),
                "attribution_complete": attribution_complete,
                "participant_pii_present": participant_pii_present,
                "share_alike_obligation": resolution.get("share_alike_obligation", False),
                "eligible_noncommercial_research": eligible,
            }
        )

    def counts(field: str) -> dict[str, int]:
        values: dict[str, int] = {}
        for row in outcomes:
            key = str(row.get(field) or "UNRESOLVED")
            values[key] = values.get(key, 0) + 1
        return dict(sorted(values.items()))

    report = {
        "contract_version": "r10.license-resolution.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input": {
            "ledger": LEDGER_PATH,
            "ledger_sha256": ledger_sha,
            "source_sidecar": SOURCE_PATH,
            "source_sidecar_sha256": source_sha,
            "expected_unknown_assertion_count": EXPECTED_UNKNOWN,
        },
        "policy": {
            "tier": "NON_COMMERCIAL_RESEARCH",
            "allowed_licenses": sorted(ALLOWED),
            "no_derivatives_excluded": True,
            "public_access_is_not_license": True,
            "unresolved_remains_ineligible": True,
            "most_restrictive_on_disagreement": True,
        },
        "summary": {
            "unknown_assertion_count": len(outcomes),
            "unique_source_url_count": len(unique_urls),
            "unique_doi_count": len(unique_dois),
            "resolved_assertion_count": sum(row["resolved_license"] is not None for row in outcomes),
            "remaining_unknown_assertion_count": sum(row["resolved_license"] is None for row in outcomes),
            "eligible_noncommercial_research_count": sum(
                row["eligible_noncommercial_research"] for row in outcomes
            ),
            "resolution_license_counts": counts("resolved_license"),
            "resolution_method_counts": counts("resolution_method"),
            "source_family_counts": counts("source_family_id"),
        },
        "source_resolutions": {
            "doi": doi_results,
            "landing_page": page_results,
        },
        "records": outcomes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
