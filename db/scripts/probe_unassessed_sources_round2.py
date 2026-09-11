#!/usr/bin/env python3
"""Round 2 — G1-4. Assess the four discovery sources the project never touched.

R11 recorded capability receipts for SciELO, CORE, Unpaywall, J-Stage and
Redalyc, each saying why the source was or was not usable. Four sources have no
receipt and no reference anywhere in the project:

    BASE              Bielefeld Academic Search Engine, ~300M documents
    OpenAIRE          EU aggregator over repositories and journals
    Semantic Scholar  S2 corpus, ~200M papers, open API
    PubAg             USDA National Agricultural Library

An exhaustion claim that does not mention them is incomplete, so each is either
measured or given a receipt in the same shape R11 used.

WHAT IS MEASURED PER SOURCE
    reachable          did the endpoint answer at all
    auth               does it demand a key or registration
    pool               how many records it claims for the subject
    licence_exposed    does the record carry a licence field usable at capture
    novelty            of the DOIs sampled, how many are absent from the 4,031
                       already held

Discovery assessment only. Nothing captured, nothing admitted, fit count 0.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import time
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
USER_AGENT = "CoffeeFlavorResearch-Round2/1.0 (noncommercial licence-filtered discovery)"

TERMS = ("coffee sensory", "coffee flavour descriptive", "coffee cupping quality")


def fetch(url: str, timeout: float, attempts: int = 3) -> tuple[bytes | None, str | None]:
    """Returns (body, error). A failure is always reported, never returned as emptiness."""
    last = "unknown"
    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT,
                                            "Accept": "application/json, application/xml"})
            with urlopen(request, timeout=timeout) as response:
                return response.read(), None
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}:{str(exc)[:110]}"
            if attempt == attempts:
                return None, last
            time.sleep(min(2 ** attempt, 20))
    return None, last


def normalise(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = str(doi).strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi if doi.startswith("10.") else None


# --------------------------------------------------------------- per source


def probe_openaire(timeout: float, pause: float) -> dict:
    pool = 0
    dois: set[str] = set()
    licences: set[str] = set()
    errors: list[str] = []
    for term in TERMS:
        url = ("https://api.openaire.eu/search/publications?"
               + urlencode({"keywords": term, "size": 50, "format": "json"}))
        body, error = fetch(url, timeout)
        if error:
            errors.append(f"{term}:{error}")
            time.sleep(pause)
            continue
        try:
            payload = json.loads(body.decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}:parse:{type(exc).__name__}")
            time.sleep(pause)
            continue
        response = (payload.get("response") or {})
        header = response.get("header") or {}
        pool = max(pool, int((header.get("total") or {}).get("$", 0) or 0))
        results = ((response.get("results") or {}).get("result") or [])
        for item in results if isinstance(results, list) else [results]:
            blob = json.dumps(item)
            for token in ("CC-BY", "cc-by", "OPEN", "CLOSED", "EMBARGO", "RESTRICTED"):
                if token in blob:
                    licences.add(token)
            # Only the record's OWN doi pid. An earlier version of this probe
            # scanned the whole record for any "10.*" string, which also caught
            # the DOIs of references and related works: 186 strings for 50
            # records, inflating the sample and the novelty rate by about 3.7x.
            match = re.search(r'"@classid":\s*"doi"[^}]*?"\$":\s*"(10\.[^"]+)"', blob)
            if match:
                d = normalise(match.group(1))
                if d:
                    dois.add(d)
        time.sleep(pause)
    return {"pool": pool, "dois": dois, "licence_tokens": sorted(licences), "errors": errors}


def probe_semantic_scholar(timeout: float, pause: float) -> dict:
    pause = max(pause, 4.0)  # S2 429s aggressively without an API key
    pool = 0
    dois: set[str] = set()
    oa_flagged = 0
    errors: list[str] = []
    for term in TERMS:
        url = ("https://api.semanticscholar.org/graph/v1/paper/search?"
               + urlencode({"query": term, "limit": 100,
                            "fields": "externalIds,openAccessPdf,title,year"}))
        body, error = fetch(url, timeout)
        if error:
            errors.append(f"{term}:{error}")
            time.sleep(pause)
            continue
        try:
            payload = json.loads(body.decode("utf-8", "replace"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{term}:parse:{type(exc).__name__}")
            time.sleep(pause)
            continue
        pool = max(pool, int(payload.get("total") or 0))
        for item in payload.get("data") or []:
            d = normalise((item.get("externalIds") or {}).get("DOI"))
            if d:
                dois.add(d)
            if item.get("openAccessPdf"):
                oa_flagged += 1
        time.sleep(pause)
    return {"pool": pool, "dois": dois, "open_access_flagged": oa_flagged, "errors": errors}


def probe_base(timeout: float, pause: float) -> dict:
    """BASE requires IP registration. The probe records the refusal rather than
    assuming it."""
    url = ("https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi?"
           + urlencode({"func": "PerformSearch", "query": "coffee sensory",
                        "format": "json", "hits": 20}))
    body, error = fetch(url, timeout, attempts=2)
    time.sleep(pause)
    if error:
        return {"pool": 0, "dois": set(), "errors": [error],
                "auth": "REGISTRATION_REQUIRED_ENDPOINT_REFUSED"}
    text = body.decode("utf-8", "replace")[:400]
    # BASE answers with HTTP 200 and an error object rather than an HTTP error,
    # so a naive probe records it as reachable with an empty pool.
    if '"error"' in text and "Access denied" in text:
        return {"pool": 0, "dois": set(), "errors": [],
                "auth": "REGISTRATION_REQUIRED_IP_AND_USER_AGENT_MUST_BE_WHITELISTED",
                "verbatim_refusal": text.strip()[:200]}
    return {"pool": 0, "dois": set(), "errors": [], "auth": "ANSWERED",
            "sample_response_head": text}


def probe_pubag(timeout: float, pause: float) -> dict:
    """PubAg's documented API is api.nal.usda.gov and needs a key. The public
    site search is HTML, not a licence-bearing record API."""
    url = "https://api.nal.usda.gov/pubag/rest/search/?query=" + quote("coffee sensory")
    body, error = fetch(url, timeout, attempts=2)
    time.sleep(pause)
    if error:
        # Checked separately: the public site at pubag.nal.usda.gov answers, but
        # serves an Ex Libris Primo HTML interface, not a record API. There is
        # no licence-bearing JSON route to capture from.
        return {"pool": 0, "dois": set(), "errors": [error],
                "auth": "NO_RECORD_API_DOCUMENTED_REST_PATH_RETURNS_404_SITE_SERVES_PRIMO_HTML"}
    return {"pool": 0, "dois": set(), "errors": [], "auth": "ANSWERED",
            "sample_response_head": body.decode("utf-8", "replace")[:400]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--pause", type=float, default=1.5)
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()

    held: set[str] = set()
    for name in ("capture_manifest.json", "capture_manifest_ext.json"):
        path = R2 / name
        if path.exists():
            held |= {
                normalise(row.get("doi"))
                for row in json.loads(path.read_text())["discovery_candidates"]
            }
    held.discard(None)

    receipts = []
    for name, fn, note in (
        ("OPENAIRE", probe_openaire,
         "EU aggregator. Open API, no key. Rights appear as access-level tokens rather than a licence identifier, so per-item licence would still need resolving."),
        ("SEMANTIC_SCHOLAR", probe_semantic_scholar,
         "Open API, rate limited without a key. Exposes openAccessPdf but no licence field, so licence would have to be resolved elsewhere for every record."),
        ("BASE", probe_base,
         "Requires IP registration for API access."),
        ("PUBAG", probe_pubag,
         "USDA NAL. Documented API requires a data.gov key."),
    ):
        result = fn(args.timeout, args.pause)
        dois = result.get("dois") or set()
        new = dois - held
        receipts.append({
            "source_system": name,
            "reachable": not result.get("errors"),
            "auth": result.get("auth", "NONE_REQUIRED"),
            "claimed_pool_for_subject": result.get("pool", 0),
            "dois_sampled": len(dois),
            "dois_not_already_held": len(new),
            "novelty_rate": round(len(new) / len(dois), 4) if dois else None,
            "licence_exposed_at_discovery": result.get("licence_tokens")
            or ("open_access_flag_only" if result.get("open_access_flagged") is not None else None),
            "errors": result.get("errors", []),
            "assessment_note": note,
        })
        print(json.dumps(receipts[-1], ensure_ascii=False), flush=True)

    report = {
        "contract_version": "round2.unassessed-source-probe.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gate_item": "G1-4",
        "question": "Four discovery sources have no capability receipt anywhere in the project. Do they contain acquisition space the ceiling estimate has missed?",
        "held_doi_count": len(held),
        "receipts": receipts,
        "guards": {"records_captured": 0, "records_admitted": 0, "corpus_written": False,
                   "fit_count": 0},
        "limitations": [
            "One page per term per source. Novelty is measured on a sample, not on a pool.",
            "A DOI absent from the held set is new to the corpus. It is not thereby relevant, openly licensed, extractable, or of the granularity option A needs.",
            "Sources demanding a key or registration are recorded as refused rather than assessed. That is a capability receipt, not a measurement of their contents.",
        ],
    }
    (args.output_dir / "unassessed_source_probe.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps([{k: r[k] for k in
                       ("source_system", "reachable", "auth", "claimed_pool_for_subject",
                        "dois_sampled", "dois_not_already_held")} for r in receipts],
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
