#!/usr/bin/env python3
"""Run the fixed R11 C0/C1 and multilingual OA acquisition queries.

Only source records carrying an allowed, non-ND licence are retrieved.  The
script extracts T1--T6 records with the frozen R6 mapping registry; it never
trains, fits, tunes, or evaluates a model.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import time
from urllib.parse import quote

from extract_candidates_r11 import (
    cache_fetch,
    digest,
    epmc_lookup,
    normalize_license,
    parse_html,
    parse_xml,
    source_license,
    stable_bytes,
)
from stratify_extraction_r11 import (
    R10,
    R11,
    load_direct_registry,
    ontology_records,
    sample_axis_records,
)


ALLOWED = {"CC0-1.0", "CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0", "CC-BY-NC-4.0"}
EPMC_LICENSE_QUERY = '(LICENSE:"cc by" OR LICENSE:"cc by-nc" OR LICENSE:"cc by-sa" OR LICENSE:cc0)'
EPMC_QUERIES = {
    "R11_C0_BREW": 'coffee AND (brew* OR "brewing method" OR espresso OR filter OR "French press" OR "cold brew" OR immersion OR percolation) AND (sensory OR descriptive OR panel OR CATA)',
    "R11_C1_ROAST": 'coffee AND (roast* OR "roast level" OR "roast degree" OR light OR medium OR dark) AND (sensory OR descriptive OR panel)',
    "R11_C0_EXTRACTION": 'coffee AND (grind OR "extraction yield" OR TDS OR "brew ratio") AND sensory',
}
DOAJ_QUERIES = {
    "DOAJ_C0_BREW": "coffee brewing sensory",
    "DOAJ_C1_ROAST": "coffee roast sensory",
    "DOAJ_EXTRACTION": "coffee extraction sensory",
    "DOAJ_PT_SENSORIAL": "café sensorial",
    "DOAJ_PT_ANALISE": "análise sensorial café",
    "DOAJ_PT_PERFIL": "perfil sensorial café",
    "DOAJ_ES_CATACION": "catación café",
    "DOAJ_ES_TORREFACCION": "torrefacción café",
}

NON_COFFEE_PRODUCT_TITLE = re.compile(
    r"spent coffee grounds|coffee leaf tea|cell culture[- ]based coffee|coffee[- ]flavou?red|"
    r"coffee flavored|coffee husk|coffee pulp|cascara|skin care|skincare|cosmetic|"
    r"bread|ice cream|gelati|hemp seed oil|medical purposes|beer|liqueur",
    re.I,
)


def coffee_is_study_subject(title: str) -> bool:
    """Require coffee in the title and reject adjacent-product studies."""
    return bool(
        re.search(r"\bcoffee\b|\bcoffea\b|\bcafé\b", title, re.I)
        and not NON_COFFEE_PRODUCT_TITLE.search(title)
    )


def epmc_license(value: str | None) -> str | None:
    token = (value or "").strip().lower().replace("_", "-")
    if "nd" in token:
        return None
    if "cc0" in token:
        return "CC0-1.0"
    if "by-nc" in token or "by nc" in token:
        return "CC-BY-NC-4.0"
    if "by-sa" in token or "by sa" in token:
        return "CC-BY-SA-4.0"
    if "cc by" in token or "cc-by" in token:
        return "CC-BY-4.0"
    return None


def doaj_journal_license(payload: dict) -> str | None:
    values = []
    for result in payload.get("results", []):
        for row in result.get("bibjson", {}).get("license", []):
            if row.get("ND"):
                continue
            value = normalize_license(row.get("url", "")) or normalize_license(row.get("type", ""))
            if value in ALLOWED:
                values.append(value)
    return sorted(values)[0] if values else None


def relevant_article(row: dict) -> bool:
    bib = row.get("bibjson", {})
    title = bib.get("title", "")
    text = f"{title} {bib.get('abstract', '')}".lower()
    return bool(
        coffee_is_study_subject(title)
        and re.search(r"sensor|cupping|descript|cata|flavo[u]?r|aroma", text)
        and not re.search(r"craft beer|coffee grounds beer|coffee pulp wine|liqueur|consumer preference|consumer acceptance", text)
    )


def relevant_epmc_article(row: dict) -> bool:
    """Apply a bounded bibliographic relevance gate before full-text retrieval.

    EPMC's broad `light OR medium OR dark` and brewing queries legitimately
    return thousands of OA records where coffee is only incidental.  Downloading
    those records is neither useful acquisition nor respectful endpoint use.
    """
    title = row.get("title", "")
    text = f"{title} {row.get('abstractText', '')}".lower()
    return bool(
        coffee_is_study_subject(title)
        and re.search(r"sensor|cupping|descript|\bcata\b|\bqda\b|flavo[u]?r|aroma", text)
        and not re.search(
            r"consumer liking|consumer acceptance|machine learning|deep learning|"
            r"blood glucose|cancer|disease|antioxidant|antimicrobial|bibliometric",
            text,
        )
    )


def doi_from_bib(bib: dict) -> str | None:
    return next((row.get("id", "").lower() for row in bib.get("identifier", []) if row.get("type") == "doi" and row.get("id")), None)


def retrieve_candidate(candidate: dict, cache_dir: Path, timeout: float) -> tuple[dict, bytes]:
    pmcid = candidate.get("pmcid") or epmc_lookup(candidate["doi"], cache_dir, timeout)
    if pmcid:
        url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
        result = cache_fetch(url, cache_dir, timeout)
        return result, result.pop("body")
    for link in candidate.get("links", []):
        if link.get("content_type") == "text/html" and link.get("url"):
            result = cache_fetch(link["url"], cache_dir, timeout)
            return result, result.pop("body")
    raise RuntimeError("NO_STRUCTURED_FULL_TEXT_ENDPOINT")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=Path("/private/tmp/coffee-flavor-r11-targeted-cache"))
    parser.add_argument("--output", type=Path, default=R11 / "targeted_acquisition.json")
    parser.add_argument("--timeout", type=float, default=25.0)
    args = parser.parse_args()

    r10_dois = {row["doi"].lower() for row in json.loads((R10 / "acquisition_manifest.json").read_text())["discovery_candidates"]}
    r10_source_dois = {
        row.get("doi", "").lower()
        for row in json.loads((R10 / "resolved_source_licenses.json").read_text())["sources"]
        if row.get("doi")
    }
    existing = r10_dois | r10_source_dois
    query_receipts = []
    candidates: dict[str, dict] = {}

    for query_id, terms in EPMC_QUERIES.items():
        query = f"OPEN_ACCESS:Y AND {EPMC_LICENSE_QUERY} AND ({terms})"
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=" + quote(query, safe="") + "&resultType=core&format=json&pageSize=1000"
        try:
            response = cache_fetch(url, args.cache_dir, args.timeout)
            body = response.pop("body")
            payload = json.loads(body)
            results = payload.get("resultList", {}).get("result", [])
            query_receipts.append({"query_id": query_id, "source_system": "EUROPE_PMC", "url": url, "status": "COMPLETE", "result_count": len(results), "response_sha256": digest(body)})
            for row in results:
                doi = (row.get("doi") or "").lower()
                license_id = epmc_license(row.get("license"))
                if (
                    not doi
                    or doi in existing
                    or license_id not in ALLOWED
                    or not row.get("pmcid")
                    or not relevant_epmc_article(row)
                ):
                    continue
                candidate = candidates.setdefault(
                    doi,
                    {
                        "candidate_id": "r11.target:" + digest(doi.encode())[:24],
                        "source_system": "EUROPE_PMC",
                        "source_record_id": row["pmcid"],
                        "pmcid": row["pmcid"],
                        "doi": doi,
                        "title": row.get("title", ""),
                        "resolved_license": license_id,
                        "links": [],
                        "query_ids": [],
                    },
                )
                candidate["query_ids"].append(query_id)
        except Exception as exc:
            query_receipts.append({"query_id": query_id, "source_system": "EUROPE_PMC", "url": url, "status": "FAILED", "detail": f"{type(exc).__name__}:{str(exc)[:180]}"})

    doaj_rows: dict[str, dict] = {}
    for query_id, terms in DOAJ_QUERIES.items():
        url = "https://doaj.org/api/search/articles/" + quote(terms, safe="") + "?pageSize=100"
        try:
            response = cache_fetch(url, args.cache_dir, args.timeout)
            body = response.pop("body")
            payload = json.loads(body)
            results = payload.get("results", [])
            query_receipts.append({"query_id": query_id, "source_system": "DOAJ", "url": url, "status": "COMPLETE", "result_count": len(results), "total_available": payload.get("total"), "response_sha256": digest(body)})
            for row in results:
                if not relevant_article(row):
                    continue
                doi = doi_from_bib(row.get("bibjson", {}))
                if doi and doi not in existing:
                    saved = doaj_rows.setdefault(doi, row | {"query_ids": []})
                    saved["query_ids"].append(query_id)
        except Exception as exc:
            query_receipts.append({"query_id": query_id, "source_system": "DOAJ", "url": url, "status": "FAILED", "detail": f"{type(exc).__name__}:{str(exc)[:180]}"})

    journal_licenses: dict[str, str | None] = {}
    for row in doaj_rows.values():
        bib = row["bibjson"]
        issns = bib.get("journal", {}).get("issns", [])
        for issn in issns:
            if issn in journal_licenses:
                continue
            url = "https://doaj.org/api/search/journals/" + quote(issn, safe="") + "?pageSize=5"
            try:
                response = cache_fetch(url, args.cache_dir, args.timeout)
                body = response.pop("body")
                journal_licenses[issn] = doaj_journal_license(json.loads(body))
            except Exception:
                journal_licenses[issn] = None
    for doi, row in doaj_rows.items():
        if doi in candidates:
            candidates[doi]["query_ids"] = sorted(set(candidates[doi]["query_ids"] + row["query_ids"]))
            continue
        bib = row["bibjson"]
        licenses = [journal_licenses.get(issn) for issn in bib.get("journal", {}).get("issns", [])]
        licenses = [value for value in licenses if value in ALLOWED]
        if not licenses:
            continue
        candidates[doi] = {
            "candidate_id": "r11.target:" + digest(doi.encode())[:24],
            "source_system": "DOAJ",
            "source_record_id": row.get("id"),
            "doi": doi,
            "title": bib.get("title", ""),
            "resolved_license": sorted(licenses)[0],
            "links": bib.get("link", []),
            "query_ids": sorted(set(row["query_ids"])),
        }

    # Bounded capability receipts for required families that cannot be queried
    # license-cleanly in this environment are explicit rather than silently omitted.
    capability_receipts = [
        {"source_system": "SCIELO_OAI_PMH", "endpoint": "https://www.scielo.br/oai/scielo-oai.php", "status": "METADATA_ENDPOINT_NO_BOUNDED_KEYWORD_QUERY", "multilingual_terms_covered_in_doaj": True},
        {"source_system": "CORE", "endpoint": "https://api.core.ac.uk/", "status": "BLOCKED_API_KEY_REQUIRED"},
        {"source_system": "UNPAYWALL", "endpoint": "https://api.unpaywall.org/v2/", "status": "NOT_CALLED_CONTACT_EMAIL_NOT_PROVIDED"},
        {"source_system": "J_STAGE", "endpoint": "https://www.jstage.jst.go.jp/pub/html/AY04S210_en.html", "status": "METADATA_ONLY_NO_PER_ITEM_LICENSE_CLEAN_FULLTEXT_ROUTE"},
        {"source_system": "REDALYC_AJOL_INSTITUTES", "status": "COVERED_BY_DOAJ_KEYWORD_DISCOVERY_ONLY_PER_ITEM_LICENSE_STILL_REQUIRED"},
    ]

    direct, rules = load_direct_registry()
    outcomes = []
    records = []
    for candidate in sorted(candidates.values(), key=lambda row: row["doi"]):
        try:
            retrieval, body = retrieve_candidate(candidate, args.cache_dir, args.timeout)
            embedded_license = source_license(body, retrieval.get("content_type", ""))
            verified = embedded_license or candidate["resolved_license"]
            if verified not in ALLOWED:
                raise RuntimeError("SOURCE_LICENSE_NOT_ALLOWED")
            if retrieval.get("content_type") in {"text/xml", "application/xml"} or body.lstrip().startswith(b"<?xml"):
                tables, metadata = parse_xml(body)
            elif retrieval.get("content_type") == "text/html":
                tables, metadata = parse_html(body)
            else:
                raise RuntimeError("NO_MACHINE_READABLE_TABLE_FORMAT")
            outcome = {
                "candidate_id": candidate["candidate_id"],
                "doi": candidate["doi"],
                "title": candidate["title"],
                "source_system": candidate["source_system"],
                "source_record_id": candidate["source_record_id"],
                "source_verified_license": verified,
                "retrieval": retrieval,
                "publication_year": metadata.get("year"),
                "authors": metadata.get("authors", []),
                "institutions": metadata.get("institutions", []),
            }
            produced = []
            for table in tables:
                produced.extend(ontology_records(candidate, outcome, table, direct, rules))
                produced.extend(sample_axis_records(candidate, outcome, table, metadata["plain_text"], direct, rules))
            produced = list({row["record_id"]: row for row in produced}.values())
            records.extend(produced)
            outcomes.append({"candidate_id": candidate["candidate_id"], "doi": candidate["doi"], "status": "ADMITTED_TYPED_RECORDS" if produced else "NO_GOVERNED_TABLE", "typed_record_count": len(produced), "retrieval": retrieval})
        except Exception as exc:
            outcomes.append({"candidate_id": candidate["candidate_id"], "doi": candidate["doi"], "status": "RETRIEVAL_OR_PARSE_FAILED", "detail": f"{type(exc).__name__}:{str(exc)[:180]}"})

    records = sorted({row["record_id"]: row for row in records}.values(), key=lambda row: row["record_id"])
    report = {
        "contract_version": "r11.targeted-license-filtered-acquisition.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query_receipts": query_receipts,
        "capability_receipts": capability_receipts,
        "guards": {"fit_count": 0, "real_label_metric_count": 0, "unknown_license_admitted": 0, "nd_license_admitted": 0, "new_mapping_rules_created": 0},
        "summary": {
            "unique_license_clean_candidates": len(candidates),
            "retrieval_outcome_counts": dict(sorted(Counter(row["status"] for row in outcomes).items())),
            "typed_record_count": len(records),
            "shape_record_counts": dict(sorted(Counter(row["shape_id"] for row in records).items())),
            "coffee_group_count": len({row.get("coffee_group_id") for row in records if row.get("coffee_group_id")}),
        },
        "candidates": sorted(candidates.values(), key=lambda row: row["doi"]),
        "candidate_outcomes": outcomes,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(stable_bytes(report))
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
