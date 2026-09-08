#!/usr/bin/env python3
"""R12C — audit the discovery layer that produced the 248 R10 candidates.

R10 through R12B measured extraction and classification. None of them measured
*discovery*: whether the 248-candidate pool is a representative sample of the
license-clear literature or an artefact of a bounded probe.

This script separates two classes of measurement:

  STATIC   deterministic, byte-reproducible; derived from committed source and
           the sealed R10 acquisition manifest. Requires no network.
  PROBE    point-in-time live API observations. NOT byte-reproducible; hit
           counts drift as indexes update. Each probe records its query, the
           retrieval timestamp, and a response digest.

Nothing here acquires supervision, admits records, changes eligibility, or
touches any sealed artefact. Fit count is 0.

Usage:
    python3 audit_discovery_layer_r12c.py --offline   # STATIC only
    python3 audit_discovery_layer_r12c.py             # STATIC + PROBE
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
R12C = ROOT / "db/data/backend-sequential-model-v2/revisions/r12c"
ACQUIRE_SRC = ROOT / "db/scripts/acquire_license_verified_r10.py"
USER_AGENT = "CoffeeFlavorResearch-R12C/1.0 (noncommercial discovery-layer audit)"

# Reproduced verbatim from acquire_license_verified_r10.py at the audited commit.
# Kept as a literal copy so this audit does not import and thereby depend on the
# module under test.
R10_RELEVANT_SUBJECT = ("coffee", "coffea")
R10_RELEVANT_TOPIC = (
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

R10_EPMC_LICENSE_FILTER = (
    '(LICENSE:"cc by" OR LICENSE:"cc by-nc" OR LICENSE:"cc by-sa" OR LICENSE:cc0)'
)
R10_EPMC_QUERY_1 = 'coffee AND (sensory OR cupping OR "descriptive analysis" OR CATA OR QDA)'


def r10_relevant(title: str) -> bool:
    """Verbatim reimplementation of acquire_license_verified_r10.relevant."""
    value = title.lower()
    return any(t in value for t in R10_RELEVANT_SUBJECT) and any(
        t in value for t in R10_RELEVANT_TOPIC
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# STATIC: pagination audit by AST inspection of the acquisition source
# --------------------------------------------------------------------------

PAGINATION_TOKENS = ("cursor", "cursormark", "next_cursor", "page=", "offset", "resumptiontoken")


def audit_pagination() -> dict[str, Any]:
    """Detect whether the R10 acquisition script paginates any API."""
    source = ACQUIRE_SRC.read_text(encoding="utf-8")
    tree = ast.parse(source)

    page_size_literals: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                if key.value.lower() in {"per_page", "pagesize", "per-page", "size"}:
                    if isinstance(value, ast.Constant):
                        page_size_literals.append(
                            {
                                "parameter": key.value,
                                "value": value.value,
                                "lineno": key.lineno,
                            }
                        )

    lowered = source.lower()
    pagination_hits = [token for token in PAGINATION_TOKENS if token in lowered]

    # A loop that re-issues a request while a cursor advances would show a while
    # loop containing a fetch call. Record whether any exists.
    has_while_loop = any(isinstance(node, ast.While) for node in ast.walk(tree))

    return {
        "measurement_class": "STATIC",
        "source_file": str(ACQUIRE_SRC.relative_to(ROOT)),
        "source_sha256": sha256_text(source),
        "page_size_literals": sorted(page_size_literals, key=lambda r: r["lineno"]),
        "pagination_token_hits": pagination_hits,
        "has_while_loop": has_while_loop,
        "paginates": bool(pagination_hits) or has_while_loop,
        "finding": (
            "No pagination construct present. Every API is queried exactly once and "
            "truncated at the page-size literal above."
            if not (pagination_hits or has_while_loop)
            else "Pagination construct detected; re-audit manually."
        ),
    }


# --------------------------------------------------------------------------
# STATIC: what the sealed R10 manifest actually captured, per query
# --------------------------------------------------------------------------


def audit_capture() -> dict[str, Any]:
    manifest_text = (R10 / "acquisition_manifest.json").read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)

    per_query: dict[str, int] = {}
    per_system: dict[str, int] = {}
    for row in manifest["discovery_candidates"]:
        per_system[row["source_system"]] = per_system.get(row["source_system"], 0) + 1
        for query_id in row["query_ids"]:
            per_query[query_id] = per_query.get(query_id, 0) + 1

    return {
        "measurement_class": "STATIC",
        "manifest_sha256": sha256_text(manifest_text),
        "candidate_total": manifest["license_filtered_discovery_candidate_count"],
        "query_count": manifest["query_count"],
        "query_error_count": sum(q["status"] != "COMPLETE" for q in manifest["queries"]),
        "candidates_per_query": dict(sorted(per_query.items(), key=lambda kv: -kv[1])),
        "candidates_per_source_system": dict(sorted(per_system.items(), key=lambda kv: -kv[1])),
        "declared_gate_dependency": manifest.get("gate_dependency"),
        "declared_disposition": (
            manifest["discovery_candidates"][0]["disposition"]
            if manifest["discovery_candidates"]
            else None
        ),
    }


# --------------------------------------------------------------------------
# PROBE: live pool sizes and relevance-filter impact
# --------------------------------------------------------------------------


def fetch_json(url: str, timeout: float) -> tuple[dict[str, Any], str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    return json.loads(body.decode("utf-8")), hashlib.sha256(body).hexdigest()


def epmc_url(query: str, page_size: int, result_type: str = "idlist") -> str:
    return "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode(
        {"query": query, "resultType": result_type, "format": "json", "pageSize": page_size}
    )


def probe_pool_sizes(timeout: float) -> dict[str, Any]:
    """Measure the addressable pool for R10's own queries versus what it captured."""
    probes = []

    definitions = [
        (
            "EPMC_R10_QUERY_1_VERBATIM",
            f"OPEN_ACCESS:Y AND {R10_EPMC_LICENSE_FILTER} AND ({R10_EPMC_QUERY_1})",
            "R10 EUROPE_PMC_1 exactly as issued, licence filter included",
        ),
        (
            "EPMC_R10_QUERY_1_NO_LICENCE_FILTER",
            f"OPEN_ACCESS:Y AND ({R10_EPMC_QUERY_1})",
            "same subject query, licence filter removed, to size the licence-filter cost",
        ),
        (
            "EPMC_BROAD_SUBJECT",
            (
                "OPEN_ACCESS:Y AND (coffee OR coffea) AND "
                "(sensory OR cupping OR flavor OR flavour OR aroma OR taste OR descriptor OR panel)"
            ),
            "broader subject formulation, open access only",
        ),
    ]

    for probe_id, query, rationale in definitions:
        row: dict[str, Any] = {
            "probe_id": probe_id,
            "measurement_class": "PROBE",
            "system": "EUROPE_PMC",
            "query": query,
            "rationale": rationale,
            "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        try:
            payload, digest = fetch_json(epmc_url(query, 1), timeout)
            row["hit_count"] = payload.get("hitCount")
            row["response_sha256"] = digest
            row["status"] = "COMPLETE"
        except Exception as exc:  # noqa: BLE001 - recorded, never swallowed
            row["status"] = "ERROR"
            row["error"] = f"{type(exc).__name__}:{exc}"
        probes.append(row)

    return {"probes": probes}


def probe_relevance_filter(timeout: float, sample_size: int = 200) -> dict[str, Any]:
    """Measure the rejection rate of R10's title-only relevance filter."""
    query = f"OPEN_ACCESS:Y AND {R10_EPMC_LICENSE_FILTER} AND ({R10_EPMC_QUERY_1})"
    row: dict[str, Any] = {
        "probe_id": "R10_RELEVANT_FILTER_REJECTION_RATE",
        "measurement_class": "PROBE",
        "query": query,
        "sample_size_requested": sample_size,
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "filter_under_test": "acquire_license_verified_r10.relevant (title only)",
    }
    try:
        payload, digest = fetch_json(epmc_url(query, sample_size, "core"), timeout)
        results = payload.get("resultList", {}).get("result", [])
        titles = [r.get("title", "") for r in results]
        rejected = [t for t in titles if not r10_relevant(t)]
        row.update(
            {
                "status": "COMPLETE",
                "response_sha256": digest,
                "sample_size_returned": len(titles),
                "passed": len(titles) - len(rejected),
                "rejected": len(rejected),
                "rejection_rate": (len(rejected) / len(titles)) if titles else None,
                "rejected_title_examples": rejected[:15],
                "note": (
                    "Every sampled record already satisfies the licence filter and the "
                    "subject query. Rejections are caused solely by the title-only "
                    "keyword test."
                ),
            }
        )
    except Exception as exc:  # noqa: BLE001
        row.update({"status": "ERROR", "error": f"{type(exc).__name__}:{exc}"})
    return row


def probe_dryad(timeout: float) -> dict[str, Any]:
    """Check whether the low Dryad yield is a licence-parsing defect or real scarcity."""
    url = "https://datadryad.org/api/v2/search?" + urlencode({"q": "coffee sensory", "per_page": 5})
    row: dict[str, Any] = {
        "probe_id": "DRYAD_YIELD_CAUSE",
        "measurement_class": "PROBE",
        "system": "DRYAD",
        "url": url,
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hypothesis_tested": (
            "6 Dryad queries returned 1 candidate from a CC0-only repository; "
            "test whether the licence value fails normalisation."
        ),
    }
    try:
        payload, digest = fetch_json(url, timeout)
        items = payload.get("_embedded", {}).get("stash:datasets", [])
        licence_values = sorted({str(i.get("license", "")) for i in items})
        row.update(
            {
                "status": "COMPLETE",
                "response_sha256": digest,
                "reported_total": payload.get("total"),
                "returned": len(items),
                "distinct_license_values": licence_values,
            }
        )
        try:
            import sys

            sys.path.insert(0, str(ROOT / "db/scripts"))
            from license_resolution_r10 import ALLOWED, normalize_license

            row["normalisation_check"] = {
                value: {
                    "normalised": normalize_license(value),
                    "allowed": normalize_license(value) in ALLOWED,
                }
                for value in licence_values
            }
            row["verdict"] = (
                "LICENCE_PARSING_OK_YIELD_IS_GENUINE_SCARCITY"
                if all(r["allowed"] for r in row["normalisation_check"].values())
                else "LICENCE_PARSING_DEFECT"
            )
        except Exception as exc:  # noqa: BLE001
            row["normalisation_check_error"] = f"{type(exc).__name__}:{exc}"
    except Exception as exc:  # noqa: BLE001
        row.update({"status": "ERROR", "error": f"{type(exc).__name__}:{exc}"})
    return row


# --------------------------------------------------------------------------
# STATIC: why the ontology/relational layer admits almost nothing
# --------------------------------------------------------------------------

# Conservative descriptor roots. Deliberately small and drawn from the project's
# own nine support dimensions plus terms already proven to map in R11/R12B.
# A larger list would inflate the recoverable estimate; this one under-counts.
KNOWN_ROOTS = frozenset(
    {
        "floral", "fruity", "green", "vegetative", "nutty", "cocoa", "roasted",
        "sour", "fermented", "spice", "spicy", "sweet", "caramel", "honey",
        "chocolate", "citrus", "berry", "nuts", "nut", "vanilla", "smoky",
        "earthy", "woody", "malty", "toasted", "buttery", "almond",
    }
)

MULTI_TERM_SEPARATORS = (",", ";", "/")


def _strip_markers(form: str) -> str:
    form = re.sub(r"\[\d+\]", "", form)          # citation markers: floral [36]
    form = re.sub(r"\([^)]*\)", "", form)        # parenthetical qualifiers
    form = re.sub(r"[\d\*]+$", "", form.strip())  # trailing footnote digits/asterisks
    return form


def _has_footnote_marker(form: str) -> bool:
    return bool(
        re.search(r"\[\d+\]", form)
        or re.search(r"\s\d+(,\s?\d+)*\s*\*?\s*$", form)
        or form.rstrip().endswith("*")
    )


def _tokenise(form: str) -> list[str]:
    cleaned = _strip_markers(form)
    parts = re.split(r"[,;/]", cleaned)
    return [p.strip().lower().rstrip(".") for p in parts if p.strip()]


def audit_mapping_layer() -> dict[str, Any]:
    """Determine why 1429 ontology mappings were queued rather than admitted."""
    audit_path = ROOT / "db/data/backend-sequential-model-v2/revisions/r11/mapping_audit.json"
    text = audit_path.read_text(encoding="utf-8")
    audit = json.loads(text)

    queue = audit["owner_review_queue"]
    reasons: dict[str, int] = {}
    shapes: dict[str, int] = {}
    for row in queue:
        reasons[row["reason"]] = reasons.get(row["reason"], 0) + 1
        shapes[row["shape_id"]] = shapes.get(row["shape_id"], 0) + 1

    forms = sorted({row["source_surface_form"] for row in queue})
    total = len(forms)

    multi = [f for f in forms if any(s in f for s in MULTI_TERM_SEPARATORS)]
    footnoted = [f for f in forms if _has_footnote_marker(f)]
    parenthetical = [f for f in forms if "(" in f]
    clean_single = [
        f
        for f in forms
        if not any(s in f for s in MULTI_TERM_SEPARATORS)
        and not _has_footnote_marker(f)
        and "(" not in f
    ]

    def contains_known_root(form: str) -> bool:
        for token in _tokenise(form):
            if token in KNOWN_ROOTS:
                return True
            if any(word in KNOWN_ROOTS for word in token.split()):
                return True
        return False

    recoverable = [f for f in forms if contains_known_root(f)]

    return {
        "measurement_class": "STATIC",
        "source_artifact": str(audit_path.relative_to(ROOT)),
        "source_sha256": sha256_text(text),
        "mapped_assertion_count": audit["mapped_assertion_count"],
        "mapping_direction_counts": audit["mapping_direction_counts"],
        "formal_relation_edges_created": audit["guards"]["formal_relation_edges_created"],
        "owner_review_queue_size": len(queue),
        "queue_reason_counts": reasons,
        "queue_shape_counts": shapes,
        "distinct_surface_forms": total,
        "distinct_source_dois": len({row["source_doi"] for row in queue}),
        "surface_form_structure": {
            "multi_term_separator": {
                "count": len(multi),
                "share": len(multi) / total if total else None,
            },
            "footnote_or_citation_marker": {
                "count": len(footnoted),
                "share": len(footnoted) / total if total else None,
            },
            "parenthetical_qualifier": {
                "count": len(parenthetical),
                "share": len(parenthetical) / total if total else None,
            },
            "clean_single_entry": {
                "count": len(clean_single),
                "share": len(clean_single) / total if total else None,
            },
        },
        "tokenisation_recoverable": {
            "count": len(recoverable),
            "share": len(recoverable) / total if total else None,
            "known_root_vocabulary_size": len(KNOWN_ROOTS),
            "method": (
                "Split on , ; / after stripping citation markers, footnote digits and "
                "parentheticals, then test each token against a deliberately small "
                "root vocabulary drawn from the project's own nine support dimensions "
                "and terms already proven to map."
            ),
            "caveat": (
                "This is a lower bound on tokenisation-recoverable forms, not a promise "
                "of admission. Each token would still require a frozen R6 rule and "
                "owner approval under existing policy. No mapping was created."
            ),
            "examples": recoverable[:15],
        },
        "finding": (
            "The mapper receives each table cell as one atomic surface form. Multi-term "
            "odour-description cells, which are the standard reporting format for GC-O "
            "and sensory tables, therefore never match a single-term rule and are queued "
            "wholesale as NO_FROZEN_R6_RULE. This is a missing cell-tokenisation step, "
            "not a vocabulary coverage gap."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="STATIC measurements only")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--output-dir", type=Path, default=R12C)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    pagination = audit_pagination()
    capture = audit_capture()
    mapping = audit_mapping_layer()

    defects = {
        "contract_version": "r12c.discovery-layer-audit.v1",
        "round": "R12C",
        "scope": "Discovery layer only. No acquisition, no admission, no eligibility change.",
        "fit_count": 0,
        "new_acquisition_count": 0,
        "sealed_artifacts_modified": False,
        "pagination_audit": pagination,
        "capture_audit": capture,
        "mapping_layer_audit": mapping,
    }
    (args.output_dir / "discovery_layer_defects.json").write_text(
        json.dumps(defects, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    if args.offline:
        print(json.dumps({
            "mode": "STATIC_ONLY",
            "paginates": pagination["paginates"],
            "owner_review_queue_size": mapping["owner_review_queue_size"],
            "mapped_assertion_count": mapping["mapped_assertion_count"],
            "multi_term_share": mapping["surface_form_structure"]["multi_term_separator"]["share"],
            "tokenisation_recoverable_share": mapping["tokenisation_recoverable"]["share"],
        }, indent=2))
        return

    pool = probe_pool_sizes(args.timeout)
    relevance = probe_relevance_filter(args.timeout)
    dryad = probe_dryad(args.timeout)

    captured_epmc_1 = capture["candidates_per_query"].get("EUROPE_PMC_1")
    verbatim = next(
        (p for p in pool["probes"] if p["probe_id"] == "EPMC_R10_QUERY_1_VERBATIM"), {}
    )
    hit_count = verbatim.get("hit_count")
    capture_ratio = (
        (captured_epmc_1 / hit_count) if (hit_count and captured_epmc_1 is not None) else None
    )

    probe_report = {
        "contract_version": "r12c.discovery-pool-probe.v1",
        "round": "R12C",
        "reproducibility": (
            "PROBE values are point-in-time live API observations and are NOT "
            "byte-reproducible. Index contents drift. STATIC findings in "
            "discovery_layer_defects.json are reproducible."
        ),
        "fit_count": 0,
        "new_acquisition_count": 0,
        "pool_probes": pool["probes"],
        "relevance_filter_probe": relevance,
        "dryad_probe": dryad,
        "headline_capture_ratio": {
            "query_id": "EUROPE_PMC_1",
            "addressable_hit_count": hit_count,
            "captured_candidates": captured_epmc_1,
            "capture_ratio": capture_ratio,
            "interpretation": (
                "Share of the licence-filtered addressable pool that reached the "
                "candidate set for R10's single largest query."
            ),
        },
    }
    (args.output_dir / "pool_size_probe.json").write_text(
        json.dumps(probe_report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    print(
        json.dumps(
            {
                "paginates": pagination["paginates"],
                "candidate_total": capture["candidate_total"],
                "epmc_1_addressable": hit_count,
                "epmc_1_captured": captured_epmc_1,
                "capture_ratio": capture_ratio,
                "relevance_rejection_rate": relevance.get("rejection_rate"),
                "dryad_verdict": dryad.get("verdict"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
