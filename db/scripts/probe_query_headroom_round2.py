#!/usr/bin/env python3
"""Round 2 — is the capture ceiling a ceiling on the literature, or on the query set?

capture_ceiling_finding.json reports the incumbent families exhausting at 4,019
records and concludes the binding constraint is licence. The capture manifest
does not support that reading:

    records_considered              55,574
    rejected_relevance              51,515   (92.7%)
    rejected_licence_not_allowed        37
    rejected_no_derivatives              3

Licence rejected 37 records. It was not the binding constraint at capture time,
because licence filtering happens IN THE QUERY -- Europe PMC carries a LICENSE:
clause and OpenAlex a best_oa_location.license filter -- so non-open literature
was never returned and cannot be counted from this manifest either way.

What the incumbents actually exhausted was a narrow query set: five OpenAlex
topic searches and six Europe PMC queries. This probe asks whether widening the
query set reaches records the capture never saw.

METHOD
    One request per probe query against OpenAlex with the same licence filter.
    Read meta.count for the pool size, take the first page of DOIs, and measure
    how many are absent from the 3,943 DOIs already captured.

Counts and DOIs only. Nothing captured, nothing admitted, fit count 0.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
USER_AGENT = "CoffeeFlavorResearch-Round2/1.0 (noncommercial licence-filtered discovery)"

LICENCES = ("cc-by", "cc-by-nc", "cc-by-sa", "cc0")

# The five the capture already used, kept so their counts anchor the comparison.
INCUMBENT_QUERIES = (
    "coffee sensory",
    "coffee flavor",
    "coffee aroma",
    "coffee cupping",
    "coffee roast sensory",
)

# Vocabulary the capture never queried. Every term appears in TOPIC_TOKENS of
# acquire_round2_capture.relevant(), so a record matching one of these would
# have passed the relevance filter had it ever been returned.
PROBE_QUERIES = (
    "coffee descriptive analysis",
    "coffee CATA",
    "coffee QDA",
    "coffee descriptor panel",
    "coffee volatile compounds",
    "coffee fermentation sensory",
    "coffee processing sensory",
    "coffee brewing sensory",
    "coffee acidity perception",
    "coffee bitterness",
    "coffee sweetness",
    "coffee mouthfeel body",
    "coffee astringency",
    "coffee Q grader score",
    "espresso sensory",
    "cold brew sensory",
    "Coffea arabica quality attributes",
    "Coffea canephora sensory",
    "coffee consumer preference",
    "coffee trained panel",
)


def fetch(url: str, timeout: float, attempts: int = 5) -> tuple[dict | None, str | None]:
    """Returns (payload, error). A failure is reported, never returned as emptiness.

    The first version of this probe swallowed every exception and returned None,
    so a run in which OpenAlex 429'd every single request reported pool 0 and
    novelty 0 for all 25 terms -- including the five incumbent controls known to
    have yielded 2,612 records. A silent zero is indistinguishable from a genuinely
    empty pool, and this is the same defect the capture script's own docstring
    criticises in R10's acquisition.
    """
    last = "unknown"
    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT,
                                            "Accept": "application/json"})
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8")), None
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}:{str(exc)[:90]}"
            if attempt == attempts:
                return None, last
            time.sleep(min(2 ** attempt, 30))
    return None, last


def normalise(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi or None


# The multilingual harvest in acquire_round2_sources_ext.py was wiped out by
# HTTP 429 -- 18 of 18 requests failed -- because the operator ran this probe
# concurrently against the same API. Its yield has never been measured, so it is
# re-measured here rather than left as a hole in the ceiling estimate.
MULTILINGUAL_LANGUAGES = ("pt", "es", "fr", "de", "id", "ja")
MULTILINGUAL_TERMS = ("coffee sensory", "coffee flavor", "coffee quality")


def probe(term: str, timeout: float, mailto: str, pause: float,
          language: str | None = None) -> dict:
    """Pool size and first-page DOIs for one term, summed over the licence set.

    With a language, the filter mirrors the ext harvest exactly: language plus
    is_oa, with the licence read from best_oa_location afterwards rather than
    filtered in the query.
    """
    total = 0
    dois: set[str] = set()
    errors: list[str] = []
    variants = ([f"title_and_abstract.search:{term},language:{language},is_oa:true"]
                if language else
                [f"title_and_abstract.search:{term},best_oa_location.license:{lic}"
                 for lic in LICENCES])
    for variant in variants:
        url = "https://api.openalex.org/works?" + urlencode({
            "filter": variant,
            "per-page": 200,
            "cursor": "*",
            "mailto": mailto,
        })
        payload, error = fetch(url, timeout)
        if error:
            errors.append(error)
            continue
        total += int((payload.get("meta") or {}).get("count") or 0)
        for item in payload.get("results") or []:
            d = normalise(item.get("doi"))
            if d:
                dois.add(d)
        time.sleep(pause)
    return {"term": term, "pool": total, "sampled_dois": dois, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--mailto", default="research@example.org")
    parser.add_argument("--pause", type=float, default=1.5,
                        help="seconds between requests; OpenAlex 429s under concurrent load")
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()

    # Everything already held: the incumbent capture plus the extended-source run.
    captured: set[str] = set()
    for name in ("capture_manifest.json", "capture_manifest_ext.json"):
        path = R2 / name
        if path.exists():
            captured |= {
                normalise(row.get("doi"))
                for row in json.loads(path.read_text())["discovery_candidates"]
            }
    captured.discard(None)

    rows = []
    seen_new: set[str] = set()
    multilingual = tuple(
        (f"{term} [{lang}]", term, lang)
        for lang in MULTILINGUAL_LANGUAGES
        for term in MULTILINGUAL_TERMS
    )
    for group, terms in (("INCUMBENT", INCUMBENT_QUERIES), ("PROBE", PROBE_QUERIES)):
        for term in terms:
            result = probe(term, args.timeout, args.mailto, args.pause)
            sampled = result["sampled_dois"]
            new = sampled - captured
            if group == "PROBE":
                seen_new |= new
            rows.append({
                "group": group,
                "term": term,
                "pool_across_licences": result["pool"],
                "sampled": len(sampled),
                "sampled_not_already_captured": len(new),
                "novelty_rate": round(len(new) / len(sampled), 4) if sampled else None,
                "request_errors": result["errors"],
            })
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)

    multilingual_new: set[str] = set()
    for label, term, lang in multilingual:
        result = probe(term, args.timeout, args.mailto, args.pause, language=lang)
        sampled = result["sampled_dois"]
        new = sampled - captured
        multilingual_new |= new
        rows.append({
            "group": "MULTILINGUAL",
            "term": label,
            "pool_across_licences": result["pool"],
            "sampled": len(sampled),
            "sampled_not_already_captured": len(new),
            "novelty_rate": round(len(new) / len(sampled), 4) if sampled else None,
            "request_errors": result["errors"],
        })
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)

    # Control check: the five incumbent terms returned 2,612 records during the
    # capture. If they come back empty here, the instrument failed and no
    # conclusion about headroom may be drawn from this run.
    control = [r for r in rows if r["group"] == "INCUMBENT"]
    control_ok = any(r["pool_across_licences"] > 0 for r in control)
    control_errors = sum(len(r["request_errors"]) for r in control)

    probe_rows = [r for r in rows if r["group"] == "PROBE"]
    sampled_total = sum(r["sampled"] for r in probe_rows)
    new_total = sum(r["sampled_not_already_captured"] for r in probe_rows)

    report = {
        "contract_version": "round2.query-headroom-probe.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "Is the 4,019 ceiling a limit of the literature or of the query set?",
        "why": {
            "capture_manifest_says": {
                "records_considered": 55574,
                "rejected_relevance": 51515,
                "rejected_licence_not_allowed": 37,
                "rejected_no_derivatives": 3,
            },
            "reading": "Licence rejected 37 records at capture time, so it was not the binding constraint there. capture_ceiling_finding.json attributes the ceiling to licence; that claim cannot be evaluated from this manifest, because licence filtering happens inside the query and non-open records were never returned.",
        },
        "method": "One OpenAlex request per term per licence, same filter set as the capture. meta.count for pool size, first page for DOIs, compared against the 3,943 DOIs already captured.",
        "captured_doi_count": len(captured),
        "control_check": {
            "purpose": "The five incumbent terms yielded 2,612 records during the capture. Non-zero here means the instrument works; zero means it does not, and nothing in this run may be read as evidence of an empty pool.",
            "passed": control_ok,
            "request_errors_on_controls": control_errors,
            "verdict": "INSTRUMENT_OK" if control_ok else "INSTRUMENT_FAILED_RESULTS_UNUSABLE",
        },
        "rows": rows,
        "probe_summary": {
            "valid_only_if_control_passed": control_ok,
            "terms": len(probe_rows),
            "sampled": sampled_total,
            "not_already_captured": new_total,
            "distinct_new_dois": len(seen_new),
            "novelty_rate": round(new_total / sampled_total, 4) if sampled_total else None,
            "terms_with_request_errors": sum(1 for r in probe_rows if r["request_errors"]),
        },
        "multilingual_summary": {
            "why_remeasured": "All 18 OpenAlex multilingual requests in the extended-source capture failed with HTTP 429 because the operator ran an earlier version of this probe concurrently against the same API. That harvest produced 0 records and its yield had never been measured.",
            "languages": list(MULTILINGUAL_LANGUAGES),
            "distinct_new_dois": len(multilingual_new),
            "terms_with_request_errors": sum(
                1 for r in rows if r["group"] == "MULTILINGUAL" and r["request_errors"]),
        },
        "guards": {"records_captured": 0, "records_admitted": 0, "corpus_written": False,
                   "fit_count": 0},
        "limitations": [
            "First page per licence only, so novelty is measured on a sample and not on the whole pool.",
            "pool_across_licences sums four licence-filtered counts and will double count a record carrying more than one licence label.",
            "Novelty here means a DOI the capture does not hold. It does not mean the record is relevant, extractable, or of the granularity the selected architecture needs.",
        ],
    }
    (args.output_dir / "query_headroom_probe.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report["probe_summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
