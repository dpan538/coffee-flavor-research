#!/usr/bin/env python3
"""Round 2 — additional source families beyond Europe PMC, OpenAlex, Dryad, Zenodo.

Dryad yields 3 records for this subject and is not a viable ongoing family.
Zenodo is intermittent. Europe PMC and OpenAlex therefore carry ~94% of any
large capture, which cannot satisfy the R11 concentration criterion of no
family above 35%. This module adds three families with populations that do not
substantially overlap the incumbents.

SOURCES ADDED
-------------
DOAJ        Journal-level licences are curated and carry an explicit ND flag.
            A journal whitelist is built first, then articles are accepted only
            when their ISSN appears in it. Licence is therefore known at capture
            time, not resolved afterwards.

OPENALEX    Portuguese and Spanish language filters. Latin American coffee
MULTILINGUAL science is a genuinely different author population from the
            English-language MDPI and PMC results the incumbents return, and it
            needs no new API.

CORE        Aggregates full text from 230+ repositories, reaching institutional
            theses that never enter PMC. CORE returns NO licence field, so
            records are licence-resolved in batches of 50 through OpenAlex
            before admission. A CORE record whose licence cannot be resolved is
            NOT captured. Capturing it as UNKNOWN would recreate the 13,952
            unresolved-rights records that R10 tested and had to exclude.

Licence discipline is identical to R10 and to the round 2 primary capture:
same ALLOWED set, same ND exclusion, same normalisation function. Nothing is
relaxed to reach a number.

Discovery only. No extraction, no admission, no rule or concept, fit count 0.
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
from acquire_round2_capture import relevant  # noqa: E402

R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
USER_AGENT = "CoffeeFlavorResearch-Round2Ext/1.0 (noncommercial licence-filtered discovery)"

DOAJ_QUERIES = [
    "coffee sensory", "coffee flavour", "coffee aroma", "coffee cupping",
    "coffee roasting quality", "Coffea arabica sensory", "coffee fermentation sensory",
]
DOAJ_JOURNAL_QUERIES = [
    "food science", "sensory", "food quality", "beverage", "agriculture food",
    "food research", "coffee",
]
OPENALEX_LANGUAGES = ["pt", "es", "fr", "de", "id", "ja"]
OPENALEX_MULTILINGUAL_FILTERS = [
    "title_and_abstract.search:coffee sensory",
    "title_and_abstract.search:coffee flavor",
    "title_and_abstract.search:coffee quality",
]
CORE_QUERIES = [
    "coffee sensory evaluation", "coffee descriptive analysis", "coffee cupping score",
    "coffee flavour profile", "coffee roasting sensory", "Coffea arabica sensory panel",
]


def fetch(url: str, timeout: float, attempts: int = 4) -> tuple[dict[str, Any], str]:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            with urlopen(request, timeout=timeout) as response:
                body = response.read()
            return json.loads(body.decode("utf-8")), hashlib.sha256(body).hexdigest()
        except Exception as exc:  # noqa: BLE001 - re-raised if all attempts fail
            last = exc
            if attempt < attempts:
                time.sleep(min(2 ** attempt, 12))
    raise last if last else RuntimeError("fetch failed with no exception recorded")


class ExtCollector:
    def __init__(self, target: int, per_source_cap: int) -> None:
        self.candidates: dict[str, dict[str, Any]] = {}
        self.target = target
        self.per_source_cap = per_source_cap
        self.queries: list[dict[str, Any]] = []
        self.rejected_relevance = 0
        self.rejected_licence = 0
        self.rejected_nd = 0
        self.rejected_unresolved_licence = 0

    @property
    def full(self) -> bool:
        return len(self.candidates) >= self.target

    def source_full(self, source: str) -> bool:
        n = sum(1 for r in self.candidates.values() if r["source_system"] == source)
        return n >= self.per_source_cap

    def add(self, source: str, identifier: str, title: str, abstract: str,
            doi: str | None, licence_value: str, source_url: str, query_id: str) -> bool:
        if not relevant(title, abstract):
            self.rejected_relevance += 1
            return False
        licence_id = normalize_license(licence_value)
        if licence_id is None:
            self.rejected_unresolved_licence += 1
            return False
        if "ND" in licence_id.upper().split("-"):
            self.rejected_nd += 1
            return False
        if licence_id not in ALLOWED:
            self.rejected_licence += 1
            return False
        key = doi or f"{source}:{identifier}"
        row = self.candidates.setdefault(key, {
            "candidate_id": key, "source_system": source, "source_record_id": identifier,
            "doi": doi, "title": title, "resolved_license": licence_id,
            "license_source_url": source_url,
            "disposition": "DISCOVERY_CANDIDATE_REQUIRES_SAMPLE_DESCRIPTOR_TABLE_ADAPTER",
            "query_ids": [],
        })
        row["query_ids"] = sorted(set(row["query_ids"]) | {query_id})
        return True

    def log(self, query_id: str, system: str, url: str, page: int, status: str,
            digest: str | None = None, error: str | None = None) -> None:
        row = {"query_id": query_id, "source_system": system, "url": url,
               "page": page, "status": status}
        if digest:
            row["response_sha256"] = digest
        if error:
            row["error"] = error
        self.queries.append(row)


def doaj_journal_whitelist(c: ExtCollector, timeout: float) -> dict[str, str]:
    """Build ISSN -> licence for DOAJ journals whose licence is allowed and non-ND."""
    whitelist: dict[str, str] = {}
    for index, q in enumerate(DOAJ_JOURNAL_QUERIES, 1):
        for page in range(1, 11):
            url = ("https://doaj.org/api/v4/search/journals/"
                   + q.replace(" ", "%20") + "?" + urlencode({"pageSize": 100, "page": page}))
            try:
                payload, digest = fetch(url, timeout)
            except Exception as exc:  # noqa: BLE001
                c.log(f"DOAJ_JOURNALS_{index}", "DOAJ", url, page, "ERROR",
                      error=f"{type(exc).__name__}:{exc}")
                break
            c.log(f"DOAJ_JOURNALS_{index}", "DOAJ", url, page, "COMPLETE", digest)
            results = payload.get("results", [])
            for row in results:
                b = row.get("bibjson", {})
                licences = b.get("license") or []
                chosen = None
                for lic in licences:
                    if lic.get("ND"):
                        continue
                    norm = normalize_license(lic.get("url") or lic.get("type") or "")
                    if norm in ALLOWED:
                        chosen = norm
                        break
                if not chosen:
                    continue
                for issn in b.get("eissn", []) if isinstance(b.get("eissn"), list) else [b.get("eissn")]:
                    if issn:
                        whitelist[str(issn)] = chosen
                for issn in b.get("pissn", []) if isinstance(b.get("pissn"), list) else [b.get("pissn")]:
                    if issn:
                        whitelist[str(issn)] = chosen
            if not results:
                break
            time.sleep(0.3)
    return whitelist


def harvest_doaj(c: ExtCollector, timeout: float, max_pages: int,
                 whitelist: dict[str, str]) -> None:
    for index, q in enumerate(DOAJ_QUERIES, 1):
        if c.full or c.source_full("DOAJ"):
            return
        query_id = f"DOAJ_{index}"
        for page in range(1, max_pages + 1):
            if c.full or c.source_full("DOAJ"):
                return
            url = ("https://doaj.org/api/v4/search/articles/"
                   + q.replace(" ", "%20") + "?" + urlencode({"pageSize": 100, "page": page}))
            try:
                payload, digest = fetch(url, timeout)
            except Exception as exc:  # noqa: BLE001
                c.log(query_id, "DOAJ", url, page, "ERROR", error=f"{type(exc).__name__}:{exc}")
                break
            c.log(query_id, "DOAJ", url, page, "COMPLETE", digest)
            results = payload.get("results", [])
            for row in results:
                b = row.get("bibjson", {})
                ids = {i.get("type"): i.get("id") for i in b.get("identifier", [])}
                issn = ids.get("eissn") or ids.get("pissn")
                licence = whitelist.get(str(issn)) if issn else None
                if not licence:
                    c.rejected_unresolved_licence += 1
                    continue
                c.add("DOAJ", row.get("id", ""), b.get("title", "") or "",
                      b.get("abstract", "") or "", ids.get("doi"), licence,
                      f"https://doaj.org/article/{row.get('id','')}", query_id)
            if not results:
                break
            time.sleep(0.3)


def harvest_openalex_multilingual(c: ExtCollector, timeout: float, max_pages: int,
                                  mailto: str) -> None:
    for lang in OPENALEX_LANGUAGES:
        for index, base in enumerate(OPENALEX_MULTILINGUAL_FILTERS, 1):
            if c.full or c.source_full(f"OPENALEX_{lang.upper()}"):
                break
            query_id = f"OPENALEX_{lang.upper()}_{index}"
            cursor = "*"
            for page in range(1, max_pages + 1):
                if c.full or c.source_full(f"OPENALEX_{lang.upper()}"):
                    break
                url = "https://api.openalex.org/works?" + urlencode({
                    "filter": f"{base},language:{lang},is_oa:true",
                    "per-page": 200, "cursor": cursor, "mailto": mailto})
                try:
                    payload, digest = fetch(url, timeout)
                except Exception as exc:  # noqa: BLE001
                    c.log(query_id, f"OPENALEX_{lang.upper()}", url, page, "ERROR",
                          error=f"{type(exc).__name__}:{exc}")
                    break
                c.log(query_id, f"OPENALEX_{lang.upper()}", url, page, "COMPLETE", digest)
                results = payload.get("results", [])
                for item in results:
                    loc = item.get("best_oa_location") or {}
                    doi = (item.get("doi") or "").removeprefix("https://doi.org/") or None
                    inv = item.get("abstract_inverted_index") or {}
                    c.add(f"OPENALEX_{lang.upper()}", item.get("id", ""),
                          item.get("title") or "", " ".join(inv.keys()) if inv else "",
                          doi, loc.get("license") or "",
                          loc.get("landing_page_url") or item.get("id", ""), query_id)
                nxt = (payload.get("meta") or {}).get("next_cursor")
                if not results or not nxt:
                    break
                cursor = nxt
                time.sleep(0.15)


def resolve_licences_via_openalex(dois: list[str], timeout: float,
                                  mailto: str) -> dict[str, str]:
    """Batch-resolve DOI -> licence, 50 per request. CORE returns no licence."""
    out: dict[str, str] = {}
    for i in range(0, len(dois), 50):
        batch = [d for d in dois[i:i + 50] if d]
        if not batch:
            continue
        url = "https://api.openalex.org/works?" + urlencode({
            "filter": "doi:" + "|".join(batch), "per-page": 50, "mailto": mailto})
        try:
            payload, _ = fetch(url, timeout)
        except Exception:  # noqa: BLE001 - unresolved DOIs simply stay unresolved
            continue
        for w in payload.get("results", []):
            doi = (w.get("doi") or "").removeprefix("https://doi.org/").lower()
            loc = w.get("best_oa_location") or {}
            if doi and loc.get("license"):
                out[doi] = loc["license"]
        time.sleep(0.15)
    return out


def harvest_core(c: ExtCollector, timeout: float, max_pages: int, mailto: str) -> None:
    """CORE has no licence field, so candidates are staged then licence-resolved."""
    staged: list[dict[str, Any]] = []
    for index, q in enumerate(CORE_QUERIES, 1):
        if c.full or c.source_full("CORE"):
            break
        query_id = f"CORE_{index}"
        for page in range(max_pages):
            if c.full or c.source_full("CORE"):
                break
            url = "https://api.core.ac.uk/v3/search/works/?" + urlencode(
                {"q": q, "limit": 100, "offset": page * 100})
            try:
                payload, digest = fetch(url, timeout)
            except Exception as exc:  # noqa: BLE001
                c.log(query_id, "CORE", url, page + 1, "ERROR",
                      error=f"{type(exc).__name__}:{exc}")
                break
            c.log(query_id, "CORE", url, page + 1, "COMPLETE", digest)
            results = payload.get("results", [])
            for item in results:
                doi = (item.get("doi") or "").strip() or None
                if not doi:
                    c.rejected_unresolved_licence += 1
                    continue
                staged.append({
                    "identifier": str(item.get("id", "")), "doi": doi,
                    "title": item.get("title") or "",
                    "abstract": item.get("abstract") or "",
                    "url": item.get("downloadUrl") or "", "query_id": query_id,
                })
            if not results:
                break
            time.sleep(0.4)

    resolved = resolve_licences_via_openalex(
        [s["doi"] for s in staged], timeout, mailto)
    for s in staged:
        if c.full or c.source_full("CORE"):
            break
        licence = resolved.get(s["doi"].lower())
        if not licence:
            c.rejected_unresolved_licence += 1
            continue
        c.add("CORE", s["identifier"], s["title"], s["abstract"], s["doi"],
              licence, s["url"], s["query_id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=3000)
    parser.add_argument("--per-source-cap", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--max-pages", type=int, default=40)
    parser.add_argument("--mailto", default="research@example.org")
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()
    c = ExtCollector(args.target, args.per_source_cap)

    whitelist = doaj_journal_whitelist(c, args.timeout)
    harvest_doaj(c, args.timeout, args.max_pages, whitelist)
    harvest_openalex_multilingual(c, args.timeout, args.max_pages, args.mailto)
    harvest_core(c, args.timeout, args.max_pages, args.mailto)

    rows = sorted(c.candidates.values(), key=lambda r: r["candidate_id"])
    by_system = Counter(r["source_system"] for r in rows)
    errors = sum(1 for q in c.queries if q["status"] != "COMPLETE")

    report = {
        "contract_version": "round2.extended-sources.v1",
        "round": "ROUND2_CAPTURE_EXTENDED_SOURCES",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 1),
        "rationale": (
            "Dryad yields 3 records for this subject and is not a viable family. "
            "Without additional families Europe PMC and OpenAlex carry ~94% of any "
            "large capture, which cannot satisfy the R11 concentration criterion."
        ),
        "sources_added": {
            "DOAJ": "journal-licence whitelist built first; articles accepted only when their ISSN is on it",
            "OPENALEX_MULTILINGUAL": "pt, es, fr, de, id, ja language filters",
            "CORE": "no licence field; DOIs batch-resolved through OpenAlex, 50 per request",
        },
        "licence_discipline": "Identical to R10. Same ALLOWED set, ND exclusion and normalisation. A record whose licence cannot be resolved is not captured.",
        "target": args.target,
        "captured": len(rows),
        "doaj_journal_whitelist_size": len(whitelist),
        "requests_issued": len(c.queries),
        "request_errors": errors,
        "rejected_relevance": c.rejected_relevance,
        "rejected_licence_not_allowed": c.rejected_licence,
        "rejected_no_derivatives": c.rejected_nd,
        "rejected_licence_unresolved": c.rejected_unresolved_licence,
        "candidates_per_source_system": dict(by_system.most_common()),
        "queries": c.queries,
        "discovery_candidates": rows,
        "guards": {
            "records_admitted": 0, "tables_extracted": 0, "r6_rules_created": 0,
            "concepts_created": 0, "formal_relation_edges_created": 0, "fit_count": 0,
            "training_pause": "REMAINS_IN_EFFECT", "sealed_artifacts_modified": False,
        },
    }
    (args.output_dir / "capture_manifest_ext.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "captured": len(rows), "target": args.target,
        "doaj_whitelist": len(whitelist), "requests": len(c.queries), "errors": errors,
        "by_system": dict(by_system.most_common()),
        "rejected_unresolved_licence": c.rejected_unresolved_licence,
        "elapsed_s": report["elapsed_seconds"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
