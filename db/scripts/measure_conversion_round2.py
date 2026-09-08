#!/usr/bin/env python3
"""Round 2 — measure the capture-to-supervision conversion rate.

This is the number four rounds never established. R11 converted 248 candidates
into 3 admitted and 10 coffee groups, but that ran through the defective
discovery, gate and mapping layers. Whether the R12C repairs change the
conversion rate has never been measured, and every target discussion so far has
rested on guesses about it.

METHOD
------
A random sample is drawn from the 4019 captured candidates and run through the
full chain with the R12C repairs applied. The conversion rate is reported with
a Wilson interval, and extrapolated to the full capture as a range rather than
a point.

Sampling rather than a full run is deliberate: a full pass over 4019 records
would take hours and produce the same estimate with a narrower interval. The
interval is reported so the precision is visible instead of implied.

REPAIRS APPLIED (none of which are in the production path)
- G1 consumer gate scoped to the table rather than the whole article
- G2 supervision cue accepts table content, not only the caption
- G5 instrumental, chemical, statistics and descriptor-as-sample guards
- F6 list-fragment tokenisation in surface resolution
- F15 resolution consults NATIVE_DIMENSIONS, which resolve_surface never did

Discovery and measurement only. Nothing is admitted, no corpus is written, no
rule or concept is created, fit count 0.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import re
import sys
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import stratify_extraction_r11 as base  # noqa: E402
from extract_candidates_r11 import norm, numeric, parse_xml  # noqa: E402
from repaired_gates_r12c import (  # noqa: E402
    repaired_table_admits,
    sample_label_is_instrumental,
)

R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
CACHE = Path("/private/tmp/coffee-flavor-round2-fulltext-cache")
USER_AGENT = "CoffeeFlavorResearch-Round2Conv/1.0 (noncommercial research measurement)"

FRAGMENT_SEPARATORS = re.compile(r"[,;/]")
CITATION_MARKER = re.compile(r"\[\s*\d+(?:\s*[,-]\s*\d+)*\s*\]")
PARENTHETICAL = re.compile(r"\([^)]*\)")
TRAILING_FOOTNOTE = re.compile(r"[\s ]*(?:\*+|\d+(?:\s*,\s*\d+)*)\s*$")


def fragments(surface: str) -> list[str]:
    cleaned = PARENTHETICAL.sub(" ", CITATION_MARKER.sub(" ", surface))
    out = []
    for part in FRAGMENT_SEPARATORS.split(cleaned):
        part = TRAILING_FOOTNOTE.sub("", part.strip()).strip(" .-")
        if part:
            out.append(part)
    return out


def resolve_repaired(surface: str, direct: dict, rules: dict) -> list[str]:
    """F6 + F15: tokenise list fragments, and consult NATIVE_DIMENSIONS.

    stratify_extraction_r11.resolve_surface does neither. It exact-matches the
    whole normalised cell against direct and rules only, so a multi-term odour
    cell resolves to nothing and the project's own dimension vocabulary is
    invisible to it.
    """
    hits: list[str] = []
    for part in [surface] + fragments(surface):
        token = norm(part)
        if not token:
            continue
        if token in direct:
            hits.append(direct[token])
        elif token in rules:
            hits.append(rules[token]["concepts"])
        elif token in base.NATIVE_DIMENSIONS:
            hits.append(f"dimension.{token.replace(' ', '_')}")
    return sorted(set(hits))


def fetch_bytes(url: str, timeout: float, attempts: int = 3) -> bytes:
    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < attempts:
                time.sleep(min(2 ** attempt, 8))
    raise last if last else RuntimeError("fetch failed")


def epmc_xml_url_for_doi(doi: str, timeout: float) -> str | None:
    """Resolve a DOI to a Europe PMC full-text XML URL.

    Only Europe PMC XML is used. Its <table-wrap> elements are already
    structured, which avoids the PDF table extraction path that R12C found
    scores F1 0.23 and would confound the measurement.
    """
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode(
        {"query": f'DOI:"{doi}"', "resultType": "lite", "format": "json", "pageSize": 1}
    )
    try:
        payload = json.loads(fetch_bytes(url, timeout).decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None
    for item in payload.get("resultList", {}).get("result", []):
        if item.get("isOpenAccess") == "Y" and item.get("pmcid"):
            return (
                "https://www.ebi.ac.uk/europepmc/webservices/rest/"
                f"{item['pmcid']}/fullTextXML"
            )
    return None


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=400)
    parser.add_argument("--source-filter", default=None,
                        help="restrict the population to one source_system, so retrieval "
                             "coverage loss and extraction conversion loss are measured "
                             "separately instead of being conflated")
    parser.add_argument("--seed", type=int, default=20260908)
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--cache-dir", type=Path, default=CACHE)
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((R2 / "capture_manifest.json").read_text())
    population = manifest["discovery_candidates"]
    if args.source_filter:
        population = [r for r in population if r["source_system"] == args.source_filter]
    rng = random.Random(args.seed)
    sample = rng.sample(population, min(args.sample, len(population)))

    direct, rules = base.load_direct_registry()
    started = time.time()

    stage = Counter()
    per_candidate: list[dict[str, Any]] = []
    groups: set[str] = set()
    concept_hits: Counter[str] = Counter()

    for cand in sample:
        stage["sampled"] += 1
        row: dict[str, Any] = {
            "candidate_id": cand["candidate_id"],
            "source_system": cand["source_system"],
            "doi": cand.get("doi"),
        }

        url = cand["license_source_url"]
        # Repair the R10-inherited malformed form PMC/PMCxxxx/fullTextXML.
        url = re.sub(r"/rest/PMC/(PMC\d+)/fullTextXML", r"/rest/\1/fullTextXML", url)
        if "fullTextXML" not in url:
            doi = cand.get("doi")
            url = epmc_xml_url_for_doi(doi, args.timeout) if doi else None
        if not url:
            row["outcome"] = "NO_OPEN_FULL_TEXT_XML"
            stage["no_fulltext_route"] += 1
            per_candidate.append(row)
            continue
        stage["fulltext_route_found"] += 1

        digest = hashlib.sha256(url.encode()).hexdigest()
        cache_path = args.cache_dir / f"{digest}.xml"
        try:
            if cache_path.exists():
                body = cache_path.read_bytes()
            else:
                body = fetch_bytes(url, args.timeout)
                cache_path.write_bytes(body)
        except Exception as exc:  # noqa: BLE001
            row["outcome"] = f"FETCH_FAILED:{type(exc).__name__}"
            stage["fetch_failed"] += 1
            per_candidate.append(row)
            continue
        stage["fetched"] += 1

        try:
            tables, metadata = parse_xml(body)
        except Exception as exc:  # noqa: BLE001
            row["outcome"] = f"PARSE_FAILED:{type(exc).__name__}"
            stage["parse_failed"] += 1
            per_candidate.append(row)
            continue
        if not tables:
            row["outcome"] = "NO_TABLES"
            stage["no_tables"] += 1
            per_candidate.append(row)
            continue
        stage["has_tables"] += 1
        stage["tables_detected"] += len(tables)

        article_text = metadata.get("plain_text", "")
        admitted_tables = 0
        candidate_groups: set[str] = set()

        for table in tables:
            ok, _reason = repaired_table_admits(table, article_text, cand, direct, rules)
            if not ok:
                continue
            admitted_tables += 1
            stage["tables_passing_repaired_gates"] += 1

            rows_ = table["rows"]
            # Descriptor evidence anywhere in the table, under repaired resolution.
            descriptor_concepts: set[str] = set()
            for r in rows_[:60]:
                for cell in r[:14]:
                    for concept in resolve_repaired(cell, direct, rules):
                        descriptor_concepts.add(concept)
            if len(descriptor_concepts) < 2:
                continue
            stage["tables_with_descriptor_evidence"] += 1

            # Sample identities: first-column labels surviving the G5 guards.
            for r in rows_[1:]:
                if not r or not r[0].strip():
                    continue
                label = r[0]
                blocked, _cls = sample_label_is_instrumental(label, direct, rules)
                if blocked:
                    continue
                if numeric(label) is not None:
                    continue
                if base.INVALID_SAMPLE_LABEL.search(norm(label)):
                    continue
                gid = hashlib.sha256(
                    f"{cand.get('doi','')}|{norm(label)}".encode()
                ).hexdigest()[:24]
                candidate_groups.add(gid)
            for concept in descriptor_concepts:
                concept_hits[concept] += 1

        row["tables_detected"] = len(tables)
        row["tables_admitted"] = admitted_tables
        row["groups"] = len(candidate_groups)
        if candidate_groups:
            stage["candidates_yielding_groups"] += 1
            row["outcome"] = "YIELDED_GROUPS"
            groups |= candidate_groups
        elif admitted_tables:
            row["outcome"] = "TABLES_ADMITTED_NO_GROUPS"
            stage["tables_admitted_no_groups"] += 1
        else:
            row["outcome"] = "NO_TABLE_PASSED_GATES"
            stage["no_table_passed_gates"] += 1
        per_candidate.append(row)

    n = stage["sampled"]
    yielded = stage["candidates_yielding_groups"]
    lo, hi = wilson(yielded, n)
    pop = len(population)

    report = {
        "contract_version": "round2.conversion-measurement.v1",
        "round": "ROUND2_CONVERSION",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(time.time() - started, 1),
        "question": "What fraction of captured candidates convert into coffee supervision groups, with the R12C repairs applied?",
        "method": {
            "population": pop,
            "source_filter": args.source_filter,
            "sample": n,
            "seed": args.seed,
            "sampling": "uniform random without replacement",
            "fulltext_source": "Europe PMC full-text XML only; structured table-wrap elements, no PDF extraction",
            "repairs_applied": ["G1", "G2", "G5", "F6", "F15"],
            "not_applied": "Production scripts remain unrepaired; see KNOWN_PIPELINE_DEFECTS.json",
        },
        "funnel": dict(stage.most_common()),
        "conversion": {
            "candidates_yielding_groups": yielded,
            "sample": n,
            "rate": yielded / n if n else None,
            "wilson_95_interval": [round(lo, 4), round(hi, 4)],
            "extrapolated_candidates_yielding_groups": [round(lo * pop), round(hi * pop)],
        },
        "groups": {
            "distinct_groups_in_sample": len(groups),
            "groups_per_sampled_candidate": len(groups) / n if n else None,
            "extrapolated_groups_over_full_capture": [
                round(len(groups) / n * pop * lo / (yielded / n)) if yielded else 0,
                round(len(groups) / n * pop * hi / (yielded / n)) if yielded else 0,
            ] if yielded else [0, 0],
        },
        "top_concepts": dict(concept_hits.most_common(25)),
        "limitations": [
            "A group here is a distinct (DOI, surviving sample label) pair on a table that passed the repaired gates and carried at least two resolvable descriptor concepts. It is a supervision-capable unit, not an admitted assertion.",
            "Only Europe PMC XML is used. Candidates without an open PMC route are counted as non-converting, which understates what a broader retrieval layer might reach.",
            "Extrapolation assumes the sample is representative of the full capture. It is uniform random, but source composition varies.",
            "No record was admitted, no corpus written, no rule or concept created.",
        ],
        "guards": {
            "records_admitted": 0, "corpus_written": False, "r6_rules_created": 0,
            "concepts_created": 0, "fit_count": 0,
            "training_pause": "REMAINS_IN_EFFECT", "sealed_artifacts_modified": False,
        },
        "per_candidate": per_candidate,
    }
    (args.output_dir / "conversion_measurement.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "sample": n,
        "funnel": dict(stage.most_common()),
        "conversion_rate": round(yielded / n, 4) if n else None,
        "wilson_95": [round(lo, 4), round(hi, 4)],
        "groups_in_sample": len(groups),
        "extrapolated_groups": report["groups"]["extrapolated_groups_over_full_capture"],
        "elapsed_s": report["elapsed_seconds"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
