#!/usr/bin/env python3
"""Round 2 — licence-filtered discovery capture with the R12C defects repaired.

This replaces acquire_license_verified_r10.py as the primary acquisition path.
It does NOT modify that script, which remains registered as defective in
db/data/backend-sequential-model-v2/revisions/r12c/KNOWN_PIPELINE_DEFECTS.json.

REPAIRS RELATIVE TO R10
-----------------------
F1  Pagination. R10 issued exactly one request per API and truncated at its
    page-size literal. This paginates Europe PMC by cursorMark, OpenAlex by
    cursor, and Dryad and Zenodo by page, until the target is met or the
    source is exhausted.

F3  Relevance. R10's relevant() inspected the TITLE only and required both a
    subject token and a topic token, rejecting a measured 79.0% of records
    that had already passed the licence filter and the subject query. This
    inspects title AND abstract, requires a subject token in either, and
    accepts a materially wider topic vocabulary.

UNCHANGED FROM R10
------------------
Licence discipline. The same ALLOWED set, the same ND exclusion, the same
normalisation function. Nothing about rights handling is relaxed.

SCOPE
-----
Discovery only. This script admits no supervision, extracts no table, creates
no rule, concept or relation edge, and runs no fit. Every candidate carries the
disposition it earns and nothing more.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

from license_resolution_r10 import ALLOWED, normalize_license  # noqa: E402

R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
USER_AGENT = "CoffeeFlavorResearch-Round2/1.0 (noncommercial licence-filtered discovery)"

# --- F3 repair: subject and topic vocabulary -------------------------------

SUBJECT_TOKENS = ("coffee", "coffea", "arabica", "robusta", "canephora", "espresso", "cupping")

# R10 accepted nine topic tokens on the title alone. The measured effect was a
# 79% rejection of already-qualified records, discarding papers whose titles use
# quality, volatile, fermentation, processing or protocol vocabulary.
TOPIC_TOKENS = (
    "sensory", "sensorial", "cupping", "flavor", "flavour", "descriptive",
    "descriptor", "cata", "qda", "aroma", "odour", "odor", "taste", "tasting",
    "volatile", "quality", "attribute", "panel", "panellist", "panelist",
    "perception", "profile", "profiling", "roast", "roasting", "ferment",
    "fermentation", "processing", "brew", "brewing", "acidity", "bitterness",
    "sweetness", "body", "mouthfeel", "astringency", "grader", "score",
)

EPMC_LICENCE_FILTER = (
    '(LICENSE:"cc by" OR LICENSE:"cc by-nc" OR LICENSE:"cc by-sa" OR LICENSE:cc0)'
)

EPMC_QUERIES = [
    'coffee AND (sensory OR cupping OR "descriptive analysis" OR CATA OR QDA)',
    '(coffee OR coffea) AND (flavour OR flavor OR aroma OR taste) AND (panel OR descriptor OR profile)',
    '(coffee OR coffea) AND (roast OR roasting OR "roast level") AND (sensory OR quality OR attribute)',
    '(coffee OR coffea) AND (brew OR brewing OR espresso OR "brewing method") AND (sensory OR taste)',
    '(coffee OR coffea) AND (ferment OR fermentation OR processing OR washed OR natural) AND sensory',
    '"Coffea arabica" AND (descriptor OR "sensory profile" OR volatile)',
]

OPENALEX_FILTERS = [
    "title_and_abstract.search:coffee sensory",
    "title_and_abstract.search:coffee flavor",
    "title_and_abstract.search:coffee aroma",
    "title_and_abstract.search:coffee cupping",
    "title_and_abstract.search:coffee roast sensory",
]

DRYAD_QUERIES = [
    "coffee sensory", "coffee cupping", "coffee descriptive analysis",
    "Coffea arabica sensory", "coffee flavor panel", "coffee QDA CATA",
    "coffee roast", "coffee volatile",
]

ZENODO_QUERIES = ["coffee sensory", "coffee flavour", "coffee cupping", "coffee roast"]


def relevant(title: str, abstract: str = "") -> bool:
    """F3 repair: inspect title AND abstract, with a wider topic vocabulary."""
    haystack = f"{title} {abstract}".lower()
    return any(t in haystack for t in SUBJECT_TOKENS) and any(
        t in haystack for t in TOPIC_TOKENS
    )


def fetch(url: str, timeout: float, attempts: int = 4) -> tuple[dict[str, Any], str]:
    """Retry with exponential backoff.

    R10's acquisition caught every exception, returned None, and continued. A
    single transient failure therefore zeroed an entire source with nothing but
    a status line to show for it. Sources here are rate limited and intermittently
    return 400 or 504 under load, so a transient failure must not be mistaken for
    an empty source.
    """
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
            return json.loads(body.decode("utf-8")), hashlib.sha256(body).hexdigest()
        except Exception as exc:  # noqa: BLE001 - re-raised below if all attempts fail
            last = exc
            if attempt < attempts:
                time.sleep(min(2 ** attempt, 12))
    raise last if last else RuntimeError("fetch failed with no exception recorded")


class Collector:
    def __init__(self, target: int, per_source_cap: int | None = None) -> None:
        self.candidates: dict[str, dict[str, Any]] = {}
        self.target = target
        self.per_source_cap = per_source_cap
        self.queries: list[dict[str, Any]] = []
        self.rejected_relevance = 0
        self.rejected_licence = 0
        self.rejected_nd = 0

    @property
    def full(self) -> bool:
        return len(self.candidates) >= self.target

    def source_count(self, source: str) -> int:
        return sum(1 for r in self.candidates.values() if r["source_system"] == source)

    def source_full(self, source: str) -> bool:
        """R11 exit criterion required no family above 35% of the total. Capping
        each source during harvest is how that is achieved rather than hoped for."""
        if self.per_source_cap is None:
            return False
        return self.source_count(source) >= self.per_source_cap

    def add(
        self, source: str, identifier: str, title: str, abstract: str,
        doi: str | None, licence_value: str, source_url: str, query_id: str,
    ) -> None:
        if not relevant(title, abstract):
            self.rejected_relevance += 1
            return
        licence_id = normalize_license(licence_value)
        if licence_id and "ND" in licence_id.upper().split("-"):
            self.rejected_nd += 1
            return
        if licence_id not in ALLOWED:
            self.rejected_licence += 1
            return
        key = doi or f"{source}:{identifier}"
        row = self.candidates.setdefault(key, {
            "candidate_id": key,
            "source_system": source,
            "source_record_id": identifier,
            "doi": doi,
            "title": title,
            "resolved_license": licence_id,
            "license_source_url": source_url,
            "disposition": "DISCOVERY_CANDIDATE_REQUIRES_SAMPLE_DESCRIPTOR_TABLE_ADAPTER",
            "query_ids": [],
        })
        row["query_ids"] = sorted(set(row["query_ids"]) | {query_id})

    def log(self, query_id: str, system: str, url: str, page: int,
            status: str, digest: str | None = None, error: str | None = None) -> None:
        row = {"query_id": query_id, "source_system": system, "url": url,
               "page": page, "status": status}
        if digest:
            row["response_sha256"] = digest
        if error:
            row["error"] = error
        self.queries.append(row)


def harvest_epmc(c: Collector, timeout: float, max_pages: int, page_size: int) -> None:
    for index, subject in enumerate(EPMC_QUERIES, 1):
        if c.full or c.source_full("EUROPE_PMC"):
            return
        query_id = f"EPMC_{index}"
        cursor = "*"
        for page in range(1, max_pages + 1):
            if c.full or c.source_full("EUROPE_PMC"):
                return
            url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
                "query": f"OPEN_ACCESS:Y AND {EPMC_LICENCE_FILTER} AND ({subject})",
                "resultType": "core", "format": "json",
                "pageSize": page_size, "cursorMark": cursor,
            })
            try:
                payload, digest = fetch(url, timeout)
            except Exception as exc:  # noqa: BLE001 - logged, never silent
                c.log(query_id, "EUROPE_PMC", url, page, "ERROR",
                      error=f"{type(exc).__name__}:{exc}")
                break
            c.log(query_id, "EUROPE_PMC", url, page, "COMPLETE", digest)
            results = payload.get("resultList", {}).get("result", [])
            for item in results:
                if item.get("isOpenAccess") != "Y":
                    continue
                pmcid = item.get("pmcid")
                c.add("EUROPE_PMC", pmcid or item.get("id", ""),
                      item.get("title", ""), item.get("abstractText", "") or "",
                      item.get("doi"), item.get("license", "") or "",
                      f"https://www.ebi.ac.uk/europepmc/webservices/rest/PMC/{pmcid}/fullTextXML",
                      query_id)
            nxt = payload.get("nextCursorMark")
            if not results or not nxt or nxt == cursor:
                break
            cursor = nxt
            time.sleep(0.34)


def harvest_openalex(c: Collector, timeout: float, max_pages: int, mailto: str) -> None:
    for licence in ("cc-by", "cc0", "cc-by-sa", "cc-by-nc"):
        for index, base in enumerate(OPENALEX_FILTERS, 1):
            if c.full or c.source_full("OPENALEX"):
                return
            query_id = f"OPENALEX_{licence.upper()}_{index}"
            cursor = "*"
            for page in range(1, max_pages + 1):
                if c.full or c.source_full("OPENALEX"):
                    return
                url = "https://api.openalex.org/works?" + urlencode({
                    "filter": f"{base},best_oa_location.license:{licence}",
                    "per-page": 200, "cursor": cursor, "mailto": mailto,
                })
                try:
                    payload, digest = fetch(url, timeout)
                except Exception as exc:  # noqa: BLE001
                    c.log(query_id, "OPENALEX", url, page, "ERROR",
                          error=f"{type(exc).__name__}:{exc}")
                    break
                c.log(query_id, "OPENALEX", url, page, "COMPLETE", digest)
                results = payload.get("results", [])
                for item in results:
                    loc = item.get("best_oa_location") or {}
                    doi = (item.get("doi") or "").removeprefix("https://doi.org/") or None
                    inv = item.get("abstract_inverted_index") or {}
                    abstract = " ".join(inv.keys()) if inv else ""
                    c.add("OPENALEX", item.get("id", ""), item.get("title") or "",
                          abstract, doi, loc.get("license") or "",
                          loc.get("landing_page_url") or item.get("id", ""), query_id)
                nxt = (payload.get("meta") or {}).get("next_cursor")
                if not results or not nxt:
                    break
                cursor = nxt
                time.sleep(0.15)


def harvest_dryad(c: Collector, timeout: float, max_pages: int) -> None:
    for index, q in enumerate(DRYAD_QUERIES, 1):
        if c.full or c.source_full("DRYAD"):
            return
        query_id = f"DRYAD_{index}"
        for page in range(1, max_pages + 1):
            if c.full or c.source_full("DRYAD"):
                return
            url = "https://datadryad.org/api/v2/search?" + urlencode(
                {"q": q, "per_page": 100, "page": page})
            try:
                payload, digest = fetch(url, timeout)
            except Exception as exc:  # noqa: BLE001
                c.log(query_id, "DRYAD", url, page, "ERROR",
                      error=f"{type(exc).__name__}:{exc}")
                break
            c.log(query_id, "DRYAD", url, page, "COMPLETE", digest)
            items = payload.get("_embedded", {}).get("stash:datasets", [])
            for item in items:
                doi = str(item.get("identifier", "")).removeprefix("doi:") or None
                c.add("DRYAD", str(item.get("id", "")), item.get("title", "") or "",
                      item.get("abstract", "") or "", doi, str(item.get("license", "")),
                      item.get("sharingLink") or url, query_id)
            if not items:
                break
            time.sleep(0.25)


def harvest_zenodo(c: Collector, timeout: float, max_pages: int) -> None:
    for index, q in enumerate(ZENODO_QUERIES, 1):
        if c.full or c.source_full("ZENODO"):
            return
        query_id = f"ZENODO_{index}"
        for page in range(1, max_pages + 1):
            if c.full or c.source_full("ZENODO"):
                return
            url = "https://zenodo.org/api/records?" + urlencode(
                {"q": q, "size": 25, "page": page})
            try:
                payload, digest = fetch(url, timeout)
            except Exception as exc:  # noqa: BLE001
                c.log(query_id, "ZENODO", url, page, "ERROR",
                      error=f"{type(exc).__name__}:{exc}")
                break
            c.log(query_id, "ZENODO", url, page, "COMPLETE", digest)
            hits = payload.get("hits", {}).get("hits", [])
            for item in hits:
                md = item.get("metadata", {})
                lic = md.get("license") or {}
                c.add("ZENODO", str(item.get("id", "")), md.get("title", "") or "",
                      md.get("description", "") or "", item.get("doi"),
                      str(lic.get("id", "")),
                      item.get("links", {}).get("self_html", "") or url, query_id)
            if not hits:
                break
            time.sleep(1.5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--mailto", default="research@example.org")
    parser.add_argument("--per-source-cap", type=int, default=None,
                        help="default: 35%% of target, per R11 concentration criterion")
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    cap = args.per_source_cap or max(1, int(args.target * 0.35))
    c = Collector(args.target, per_source_cap=cap)
    # Pass 1: every source capped, so no family can dominate simply by running first.
    harvest_epmc(c, args.timeout, args.max_pages, args.page_size)
    harvest_openalex(c, args.timeout, args.max_pages, args.mailto)
    harvest_dryad(c, args.timeout, args.max_pages)
    harvest_zenodo(c, args.timeout, args.max_pages)
    capped_total = len(c.candidates)
    capped_distribution = dict(Counter(r["source_system"] for r in c.candidates.values()))
    # Pass 2: only if the capped pass fell short, lift the cap to reach the target.
    if not c.full:
        c.per_source_cap = None
        harvest_epmc(c, args.timeout, args.max_pages, args.page_size)
        harvest_openalex(c, args.timeout, args.max_pages, args.mailto)

    rows = sorted(c.candidates.values(), key=lambda r: r["candidate_id"])
    by_system = Counter(r["source_system"] for r in rows)
    by_licence = Counter(r["resolved_license"] for r in rows)
    errors = sum(1 for q in c.queries if q["status"] != "COMPLETE")
    considered = len(rows) + c.rejected_relevance + c.rejected_licence + c.rejected_nd

    report = {
        "contract_version": "round2.licence-filtered-capture.v1",
        "round": "ROUND2_CAPTURE",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 1),
        "supersedes_for_acquisition": "db/scripts/acquire_license_verified_r10.py",
        "repairs_applied": {
            "F1_pagination": "cursorMark for Europe PMC, cursor for OpenAlex, page for Dryad and Zenodo",
            "F3_relevance": "title AND abstract, wider topic vocabulary",
        },
        "unchanged_from_r10": "Licence discipline: identical ALLOWED set, ND exclusion and normalisation.",
        "target": args.target,
        "captured": len(rows),
        "target_met": len(rows) >= args.target,
        "requests_issued": len(c.queries),
        "request_errors": errors,
        "records_considered": considered,
        "rejected_relevance": c.rejected_relevance,
        "rejected_licence_not_allowed": c.rejected_licence,
        "rejected_no_derivatives": c.rejected_nd,
        "capture_rate_of_considered": (len(rows) / considered) if considered else None,
        "per_source_cap_applied": cap,
        "capped_pass_total": capped_total,
        "capped_pass_distribution": capped_distribution,
        "uncapped_topup_used": capped_total < args.target,
        "max_source_share": (max(by_system.values()) / len(rows)) if rows else None,
        "candidates_per_source_system": dict(by_system.most_common()),
        "candidates_per_licence": dict(by_licence.most_common()),
        "queries": c.queries,
        "discovery_candidates": rows,
        "guards": {
            "records_admitted": 0, "tables_extracted": 0, "r6_rules_created": 0,
            "concepts_created": 0, "formal_relation_edges_created": 0, "fit_count": 0,
            "training_pause": "REMAINS_IN_EFFECT",
            "sealed_artifacts_modified": False,
        },
        "limitations": [
            "Discovery only. A candidate is a licence-verified record that may contain "
            "usable material; it is not supervision and has not been extracted.",
            "The extraction and admission layers remain unrepaired in production. See "
            "KNOWN_PIPELINE_DEFECTS.json before running anything downstream of this.",
        ],
    }
    (args.output_dir / "capture_manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "captured": len(rows), "target": args.target, "target_met": report["target_met"],
        "requests": len(c.queries), "errors": errors,
        "rejected_relevance": c.rejected_relevance,
        "rejected_licence": c.rejected_licence, "rejected_nd": c.rejected_nd,
        "by_system": dict(by_system.most_common()),
        "elapsed_s": report["elapsed_seconds"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
