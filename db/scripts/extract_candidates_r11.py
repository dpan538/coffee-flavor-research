#!/usr/bin/env python3
"""Extract sample x descriptor supervision from the 248 frozen R10 candidates.

This is a fail-closed, deterministic table adapter.  It does not fit a model and
does not interpret prose as supervision.  Only numeric/presence cells in a
machine-readable table with an explicit sample axis and governed descriptor
labels are emitted.  Raw participant identities and author email addresses are
never retained.
"""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
from html.parser import HTMLParser
import io
import json
import math
from pathlib import Path
import re
import threading
import time
from typing import Any
from urllib.parse import quote
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from license_resolution_r10 import ALLOWED, normalize_license


ROOT = Path(__file__).resolve().parents[2]
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
DEFAULT_INPUT = R10 / "acquisition_manifest.json"
DEFAULT_OUTPUT = R11 / "extraction_report.json"
DEFAULT_CACHE = Path("/private/tmp/coffee-flavor-r11-fulltext-cache")
USER_AGENT = "CoffeeFlavorResearch-R11/1.0 (noncommercial evidence-table extraction)"
PRINT_LOCK = threading.Lock()

COMPOUND_ALIASES = {
    "black pepper": "sensory.black_pepper",
    "black tea": "sensory.black_tea",
    "brown sugar": "sensory.brown_sugar",
    "dark chocolate": "sensory.dark_chocolate",
    "fermented character": "sensory.fermented_character",
    "green tea": "sensory.green_tea",
    "orange blossom": "sensory.orange_blossom",
    "wine like character": "sensory.wine_like_character",
    "wine like": "sensory.wine_like_character",
}

C0_PATTERNS = {
    "preparation.family.filter_percolation": (
        r"\bfilter(?:ed)?\b",
        r"\bdrip\b",
        r"pour[ -]?over",
        r"\bv ?60\b",
        r"\bchemex\b",
        r"percolat",
    ),
    "preparation.family.immersion": (r"\bimmersion\b", r"french press", r"\bsteep"),
    "preparation.family.hybrid": (r"\baeropress\b",),
    "preparation.family.espresso_pressure": (r"\bespresso\b",),
    "preparation.family.diluted_espresso": (r"\bamericano\b", r"diluted espresso"),
    "preparation.family.stovetop_boiled": (
        r"\bmoka\b",
        r"\bturkish\b",
        r"\bibrik\b",
        r"stovetop",
        r"boiled coffee",
    ),
    "preparation.family.cold_extraction": (
        r"cold[ -]?brew",
        r"cold[ -]?(?:water )?extract",
    ),
    "preparation.family.espresso_milk": (
        r"\blatte\b",
        r"cappuccino",
        r"flat white",
        r"milk espresso",
    ),
}

C1_PATTERNS = {
    "extremely_light": (r"extremely light(?: roast(?:ed)?)?", r"very light roast"),
    "medium_light": (r"medium[ -]light(?: roast(?:ed)?)?",),
    "medium_dark": (r"medium[ -]dark(?: roast(?:ed)?)?",),
    "extremely_dark": (r"extremely dark(?: roast(?:ed)?)?", r"very dark roast"),
    "light": (r"(?<!medium[ -])(?<!extremely )\blight roast(?:ed)?\b",),
    "medium": (r"(?<!medium[ -])\bmedium roast(?:ed)?\b",),
    "dark": (r"(?<!medium[ -])(?<!extremely )\bdark roast(?:ed)?\b",),
}


def stable_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(value: str) -> str:
    value = value.lower().replace("&lt;", " ").replace("&gt;", " ")
    value = value.replace("‐", "-").replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def load_candidates(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    rows = payload["discovery_candidates"]
    if len(rows) != 248 or len({row["candidate_id"] for row in rows}) != 248:
        raise ValueError("R10_248_CANDIDATE_FREEZE_VIOLATION")
    return rows, digest(raw)


def load_candidate_universe() -> set[str]:
    registry = json.loads((R9 / "output_policy_contract.json").read_text())[
        "concept_role_registry"
    ]
    return {
        candidate_id
        for candidate_id, row in registry.items()
        if row["role"] == "NAMED_DESCRIPTOR" and candidate_id.startswith("sensory.")
    }


def descriptor_aliases(universe: set[str]) -> dict[str, str]:
    aliases = {
        candidate_id.removeprefix("sensory.").replace("_", " "): candidate_id
        for candidate_id in universe
    }
    aliases.update({k: v for k, v in COMPOUND_ALIASES.items() if v in universe})
    return aliases


def exact_descriptor(value: str, aliases: dict[str, str]) -> str | None:
    token = norm(value)
    token = re.sub(r"^(?:aroma|flavo[u]?r|taste|attribute|descriptor) (?:of )?", "", token)
    token = re.sub(r" (?:aroma|flavo[u]?r|taste|attribute|descriptor)$", "", token)
    if token in aliases:
        return aliases[token]
    # Parenthetical units and footnote letters may follow a descriptor label.
    token = re.sub(r" (?:intensity|frequency|score|mean)$", "", token)
    return aliases.get(token)


def numeric(value: str) -> float | None:
    token = value.strip().replace(",", ".")
    if not token or token.lower() in {"na", "n/a", "nd", "-", "—", "none"}:
        return None
    match = re.match(r"^\s*([+-]?(?:\d+(?:\.\d+)?|\.\d+))", token)
    if not match:
        return None
    result = float(match.group(1))
    return result if math.isfinite(result) else None


def context_value(text: str, patterns: dict[str, tuple[str, ...]]) -> str | None:
    normalized = norm(text)
    hits = {
        key
        for key, values in patterns.items()
        if any(re.search(pattern, normalized, flags=re.I) for pattern in values)
    }
    return next(iter(hits)) if len(hits) == 1 else None


def find_panel_size(text: str) -> int | None:
    patterns = (
        r"(?:panel (?:consisted|comprised) of|panel of)\s+(\d{1,4})",
        r"(\d{1,4})\s+(?:trained\s+|semi-trained\s+|expert\s+|consumer\s+)?(?:panelists|assessors|judges|q[ -]?graders|consumers)\b",
    )
    values = []
    for pattern in patterns:
        values.extend(int(v) for v in re.findall(pattern, text, flags=re.I))
    values = [value for value in values if 2 <= value <= 2000]
    return min(values) if values else None


def find_scale(text: str) -> dict[str, Any]:
    match = re.search(r"(\d{1,2})[ -]point\s+(?:intensity\s+|hedonic\s+)?scale", text, flags=re.I)
    if match:
        return {"type": "POINT_SCALE", "min": 1, "max": int(match.group(1))}
    match = re.search(r"(?:scale|ranging)\s+(?:from\s+)?(\d+(?:\.\d+)?)\s+(?:to|-)\s+(\d+(?:\.\d+)?)", text, flags=re.I)
    if match:
        return {"type": "EXPLICIT_RANGE", "min": float(match.group(1)), "max": float(match.group(2))}
    if re.search(r"check[ -]?all[ -]?that[ -]?apply|\bcata\b", text, flags=re.I):
        return {"type": "CATA_FREQUENCY_OR_PRESENCE", "min": 0, "max": None}
    return {"type": "REPORTED_NUMERIC_VALUE", "min": None, "max": None}


def find_replicates(text: str) -> dict[str, Any]:
    if re.search(r"\bin triplicate\b", text, flags=re.I):
        return {"reported": True, "count": 3, "basis": "IN_TRIPLICATE"}
    match = re.search(r"(\d{1,3})\s+(?:independent\s+)?replicates", text, flags=re.I)
    if match:
        return {"reported": True, "count": int(match.group(1)), "basis": "EXPLICIT_REPLICATES"}
    return {"reported": False, "count": None, "basis": "NOT_REPORTED"}


def aggregation(text: str) -> str:
    if re.search(r"check[ -]?all|\bcata\b|frequency|count|percentage|%", text, flags=re.I):
        return "FREQUENCY_OR_PRESENCE"
    if re.search(r"\bmeans?\b|average|least square mean", text, flags=re.I):
        return "PANEL_MEAN"
    return "REPORTED_NUMERIC_SUMMARY"


class TableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[dict[str, Any]] = []
        self.table: dict[str, Any] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.caption: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and self.table is None:
            self.table = {"rows": [], "caption": ""}
        elif self.table is not None and tag == "tr":
            self.row = []
        elif self.table is not None and tag in {"td", "th"}:
            self.cell = []
        elif self.table is not None and tag == "caption":
            self.caption = []

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
        if self.caption is not None:
            self.caption.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.table is not None and tag in {"td", "th"} and self.cell is not None:
            if self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif self.table is not None and tag == "tr" and self.row is not None:
            if any(self.row):
                self.table["rows"].append(self.row)
            self.row = None
        elif self.table is not None and tag == "caption" and self.caption is not None:
            self.table["caption"] = " ".join("".join(self.caption).split())
            self.caption = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def element_text(element: ET.Element | None) -> str:
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def parse_xml(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = ET.fromstring(data)
    tables = []
    for index, wrap in enumerate(
        [node for node in root.iter() if local_name(node.tag) == "table-wrap"], 1
    ):
        caption = ""
        label = ""
        rows = []
        for node in wrap:
            if local_name(node.tag) == "caption":
                caption = element_text(node)
            elif local_name(node.tag) == "label":
                label = element_text(node)
        table_nodes = [node for node in wrap.iter() if local_name(node.tag) == "table"]
        if table_nodes:
            spans: dict[int, tuple[str, int]] = {}
            for tr in [node for node in table_nodes[0].iter() if local_name(node.tag) == "tr"]:
                row: dict[int, str] = {}
                for column, (value, remaining) in list(spans.items()):
                    row[column] = value
                    if remaining <= 1:
                        del spans[column]
                    else:
                        spans[column] = (value, remaining - 1)
                column = 0
                for cell in tr:
                    if local_name(cell.tag) not in {"th", "td"}:
                        continue
                    while column in row:
                        column += 1
                    value = element_text(cell)
                    colspan = max(1, int(cell.attrib.get("colspan", "1")))
                    rowspan = max(1, int(cell.attrib.get("rowspan", "1")))
                    for offset in range(colspan):
                        row[column + offset] = value
                        if rowspan > 1:
                            spans[column + offset] = (value, rowspan - 1)
                    column += colspan
                if row:
                    width = max(row) + 1
                    rows.append([row.get(index, "") for index in range(width)])
        tables.append(
            {
                "table_id": wrap.attrib.get("id") or f"table-{index}",
                "label": label or f"Table {index}",
                "caption": caption,
                "rows": rows,
            }
        )
    plain = element_text(root)
    authors = []
    institutions = []
    year = None
    # Restrict bibliographic metadata to the JATS front matter.  Searching the
    # entire tree incorrectly treats every cited author's surname and
    # institution as an author of the source article.
    front = next((node for node in root.iter() if local_name(node.tag) == "front"), None)
    metadata_nodes = front.iter() if front is not None else ()
    for node in metadata_nodes:
        name = local_name(node.tag)
        if name == "contrib" and node.attrib.get("contrib-type") == "author":
            surname = next(
                (child for child in node.iter() if local_name(child.tag) == "surname"),
                None,
            )
            value = element_text(surname) if surname is not None else ""
            if value:
                authors.append(value)
        elif name in {"institution", "institution-wrap"}:
            value = element_text(node)
            if value:
                institutions.append(value)
        elif name == "pub-date" and year is None:
            for child in node:
                if local_name(child.tag) == "year" and element_text(child).isdigit():
                    year = int(element_text(child))
    title_nodes = [node for node in root.iter() if local_name(node.tag) == "article-title"]
    metadata = {
        "plain_text": plain,
        "title": element_text(title_nodes[0]) if title_nodes else "",
        "authors": sorted(set(authors)),
        "institutions": sorted(set(institutions)),
        "year": year,
    }
    return tables, metadata


def parse_html(data: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    text = data.decode("utf-8", errors="replace")
    parser = TableHTMLParser()
    parser.feed(text)
    plain = " ".join(re.sub(r"<[^>]+>", " ", text).split())
    tables = []
    for index, table in enumerate(parser.tables, 1):
        tables.append(
            {
                "table_id": f"html-table-{index}",
                "label": f"HTML table {index}",
                "caption": table["caption"],
                "rows": table["rows"],
            }
        )
    return tables, {
        "plain_text": plain,
        "title": "",
        "authors": [],
        "institutions": [],
        "year": None,
    }


def source_license(data: bytes, content_type: str) -> str | None:
    text = data.decode("utf-8", errors="ignore")[:2_000_000]
    patterns = (
        r"creativecommons\.org/licenses/(by-nc-nd|by-nd|by-nc|by-sa|by)/(3\.0|4\.0)",
        r"creativecommons\.org/publicdomain/zero/1\.0",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        raw = match.group(0)
        value = normalize_license(raw)
        if value:
            return value
    return None


def cache_fetch(url: str, cache_dir: Path, timeout: float) -> dict[str, Any]:
    key = digest(url.encode())
    body_path = cache_dir / f"{key}.body"
    meta_path = cache_dir / f"{key}.json"
    if body_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        meta["body"] = body_path.read_bytes()
        meta["cache_hit"] = True
        return meta
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/xml,text/xml,text/html,application/json,application/pdf,*/*;q=0.2",
        },
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout) as response:
                body = response.read(25_000_000)
                meta = {
                    "requested_url": url,
                    "final_url": response.geturl(),
                    "http_status": response.status,
                    "content_type": response.headers.get_content_type(),
                    "bytes": len(body),
                    "sha256": digest(body),
                    "cache_hit": False,
                }
            break
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
            time.sleep(1.5 * (attempt + 1))
    cache_dir.mkdir(parents=True, exist_ok=True)
    body_path.write_bytes(body)
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    meta["body"] = body
    return meta


def json_fetch(url: str, cache_dir: Path, timeout: float) -> tuple[dict[str, Any], dict[str, Any]]:
    result = cache_fetch(url, cache_dir, timeout)
    return json.loads(result["body"]), result


def epmc_lookup(doi: str, cache_dir: Path, timeout: float) -> str | None:
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:"
        + quote(doi, safe="")
        + "&resultType=core&format=json"
    )
    payload, _ = json_fetch(url, cache_dir, timeout)
    rows = payload.get("resultList", {}).get("result", [])
    return next((row.get("pmcid") for row in rows if row.get("pmcid")), None)


def crossref_license(doi: str, cache_dir: Path, timeout: float) -> tuple[str | None, dict[str, Any], dict[str, Any]]:
    url = "https://api.crossref.org/works/" + quote(doi, safe="")
    payload, retrieval = json_fetch(url, cache_dir, timeout)
    message = payload.get("message", {})
    values = [normalize_license(row.get("URL", "")) for row in message.get("license", [])]
    values = [value for value in values if value]
    license_id = sorted(values)[0] if values and len(set(values)) == 1 else None
    return license_id, message, retrieval


def choose_artifact(candidate: dict[str, Any], cache_dir: Path, timeout: float) -> tuple[dict[str, Any], dict[str, Any]]:
    doi = candidate["doi"]
    metadata: dict[str, Any] = {
        "authors": [],
        "institutions": [],
        "year": None,
        "crossref_license": None,
    }
    if candidate["source_system"] == "EUROPE_PMC":
        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/"
            f"{candidate['source_record_id']}/fullTextXML"
        )
        return cache_fetch(url, cache_dir, timeout), metadata

    if candidate["source_system"] == "ZENODO":
        record_id = str(candidate["source_record_id"])
        api = f"https://zenodo.org/api/records/{record_id}"
        payload, api_retrieval = json_fetch(api, cache_dir, timeout)
        metadata["zenodo_api_sha256"] = api_retrieval["sha256"]
        files = payload.get("files", [])
        priority = {"csv": 0, "xlsx": 1, "xls": 2, "xml": 3, "html": 4, "pdf": 5}
        ranked = []
        for row in files:
            name = (row.get("key") or "").lower()
            suffix = name.rsplit(".", 1)[-1] if "." in name else ""
            url = row.get("links", {}).get("content") or row.get("links", {}).get("self")
            if suffix in priority and url:
                ranked.append((priority[suffix], url))
        if ranked:
            return cache_fetch(sorted(ranked)[0][1], cache_dir, timeout), metadata
        return api_retrieval | {"body": api_retrieval["body"]}, metadata

    if candidate["source_system"] == "DRYAD":
        return cache_fetch(candidate["license_source_url"], cache_dir, timeout), metadata

    pmcid = epmc_lookup(doi, cache_dir, timeout)
    license_id, crossref, crossref_retrieval = crossref_license(doi, cache_dir, timeout)
    metadata["crossref_license"] = license_id
    metadata["crossref_sha256"] = crossref_retrieval["sha256"]
    metadata["authors"] = [
        row.get("family", "") for row in crossref.get("author", []) if row.get("family")
    ]
    metadata["year"] = ((crossref.get("published") or {}).get("date-parts") or [[None]])[0][0]
    if pmcid:
        metadata["pmcid_discovered"] = pmcid
        return cache_fetch(
            f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
            cache_dir,
            timeout,
        ), metadata

    openalex_id = str(candidate["source_record_id"]).rstrip("/").rsplit("/", 1)[-1]
    openalex_url = f"https://api.openalex.org/works/{openalex_id}"
    payload, oa_retrieval = json_fetch(openalex_url, cache_dir, timeout)
    metadata["openalex_sha256"] = oa_retrieval["sha256"]
    metadata["authors"] = metadata["authors"] or [
        row.get("author", {}).get("display_name", "").split()[-1]
        for row in payload.get("authorships", [])
        if row.get("author", {}).get("display_name")
    ]
    metadata["institutions"] = sorted(
        {
            institution.get("display_name", "")
            for row in payload.get("authorships", [])
            for institution in row.get("institutions", [])
            if institution.get("display_name")
        }
    )
    metadata["year"] = metadata["year"] or payload.get("publication_year")
    locations = [payload.get("best_oa_location") or {}] + payload.get("locations", [])
    seen = set()
    for location in locations:
        landing = location.get("landing_page_url")
        if landing and landing not in seen:
            seen.add(landing)
            try:
                result = cache_fetch(landing, cache_dir, timeout)
                if result["content_type"] in {"text/html", "text/xml", "application/xml"}:
                    return result, metadata
            except Exception:
                pass
    for location in locations:  # PDF is explicitly last resort.
        pdf = location.get("pdf_url")
        if pdf and pdf not in seen:
            try:
                return cache_fetch(pdf, cache_dir, timeout), metadata
            except Exception:
                pass
    raise RuntimeError("NO_RETRIEVABLE_FULL_TEXT_ENDPOINT")


def table_records(
    candidate: dict[str, Any],
    table: dict[str, Any],
    aliases: dict[str, str],
    article_text: str,
    metadata: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = table["rows"]
    result: list[dict[str, Any]] = []
    descriptor_rows: list[tuple[int, str]] = []
    descriptor_columns: dict[int, str] = {}
    for index, row in enumerate(rows):
        for cell_index, cell in enumerate(row[:3]):
            value = exact_descriptor(cell, aliases)
            if value:
                descriptor_rows.append((index, value))
                break
    for row in rows[:4]:
        for index, cell in enumerate(row):
            value = exact_descriptor(cell, aliases)
            if value:
                descriptor_columns[index] = value

    sensory_context = " ".join((table["caption"], table["label"])).lower()
    exclusion_patterns = (
        r"references? for (?:panel(?:list)? )?training",
        r"guide to sensory attributes",
        r"analysis of variance|\banova\b",
        r"model performance|model factors|rmsep|rmsev",
        r"descriptive statistics",
        r"aroma-active compounds|key aroma compounds|volatile compounds",
        r"\boav\b|\broav\b|odor threshold",
        r"correlation coefficients?|principal component|factor loadings?",
    )
    if any(re.search(pattern, sensory_context, flags=re.I) for pattern in exclusion_patterns):
        return [], {"sensory_table": False, "reason": "ANALYTIC_OR_REFERENCE_TABLE_NOT_SUPERVISION"}
    article_scope = f"{candidate['title']} {table['caption']}"
    if re.search(r"liqueur|liquor|margarine|shortbread|yogurt", article_scope, flags=re.I):
        return [], {"sensory_table": False, "reason": "COFFEE_FLAVORED_PRODUCT_NOT_COFFEE_SAMPLE"}
    if re.search(
        r"bitter tastant|interactions? between .*caffeine|melanoidin|"
        r"odor descriptor.*compound|aroma-active compound",
        article_scope,
        flags=re.I,
    ):
        return [], {"sensory_table": False, "reason": "CHEMICAL_OR_TASTANT_SYSTEM_NOT_COFFEE_SAMPLE"}
    consumer_terms = re.search(
        r"consumer|customer|hedonic|liking|preference", article_text, flags=re.I
    )
    trained_terms = re.search(
        r"trained (?:sensory )?(?:panel|panelists|assessors)|q[ -]?graders|expert cuppers",
        article_text,
        flags=re.I,
    )
    if consumer_terms and not trained_terms:
        return [], {"sensory_table": False, "reason": "CONSUMER_SUBJECTIVE_DATA_EXCLUDED"}
    sensory_table = bool(
        re.search(r"sensor|descriptor|aroma|flavo[u]?r|taste|cata|panel", sensory_context)
        or len({value for _, value in descriptor_rows}) >= 2
        or len(set(descriptor_columns.values())) >= 2
    )
    if not sensory_table:
        return [], {"sensory_table": False, "reason": "NOT_SENSORY_TABLE"}
    if re.search(r"per[ -]?panelist|participant id|consumer id|judge id", sensory_context, flags=re.I):
        return [], {"sensory_table": True, "reason": "PER_PANELIST_TABLE_NOT_ADMITTED"}

    common_context = " ".join((metadata.get("title") or candidate["title"], table["caption"]))
    article_c0 = context_value(article_text, C0_PATTERNS)
    article_c1 = context_value(article_text, C1_PATTERNS)

    # Row-oriented table: descriptor is a row label, samples are columns.
    if descriptor_rows:
        first_descriptor_index = min(index for index, _ in descriptor_rows)
        header_rows = rows[: max(1, first_descriptor_index)]
        width = max((len(row) for row in header_rows), default=0)
        header = []
        for column in range(width):
            values = []
            for row in header_rows:
                if column < len(row) and row[column] and row[column] not in values:
                    values.append(row[column])
            header.append(" ".join(values))
        for row_index, candidate_id in descriptor_rows:
            row = rows[row_index]
            descriptor_cell = next(
                (i for i, cell in enumerate(row[:3]) if exact_descriptor(cell, aliases)), 0
            )
            for column in range(descriptor_cell + 1, len(row)):
                value = numeric(row[column])
                if value is None:
                    continue
                sample = header[column] if column < len(header) else f"sample-column-{column}"
                if not norm(sample) or numeric(sample) is not None:
                    continue
                sample_context = f"{sample} {common_context}"
                result.append(
                    {
                        "candidate_id": candidate_id,
                        "raw_descriptor": row[descriptor_cell],
                        "reported_value": value,
                        "reported_value_raw": row[column],
                        "sample_label": sample,
                        "c0_id": context_value(sample_context, C0_PATTERNS) or article_c0,
                        "c1_id": context_value(sample_context, C1_PATTERNS) or article_c1,
                    }
                )

    # Column-oriented table: descriptors are headers, samples are rows.
    if descriptor_columns:
        header_index = next(
            (
                i
                for i, row in enumerate(rows[:4])
                if sum(exact_descriptor(cell, aliases) is not None for cell in row) >= 1
            ),
            0,
        )
        carried_condition = ""
        for row_index, row in enumerate(rows[header_index + 1 :], header_index + 1):
            prefix_cells = row[: min(3, min(descriptor_columns, default=len(row)))]
            nonnumeric = next(
                (
                    cell
                    for cell in prefix_cells
                    if cell and numeric(cell) is None and exact_descriptor(cell, aliases) is None
                ),
                "",
            )
            if nonnumeric:
                carried_condition = nonnumeric
            numeric_condition = next(
                (cell for cell in prefix_cells if numeric(cell) is not None), ""
            )
            sample = " ".join(value for value in (carried_condition, numeric_condition) if value)
            if not sample:
                continue
            for column, candidate_id in descriptor_columns.items():
                if column >= len(row):
                    continue
                value = numeric(row[column])
                if value is None:
                    continue
                sample_context = f"{sample} {common_context}"
                result.append(
                    {
                        "candidate_id": candidate_id,
                        "raw_descriptor": rows[header_index][column],
                        "reported_value": value,
                        "reported_value_raw": row[column],
                        "sample_label": sample,
                        "c0_id": context_value(sample_context, C0_PATTERNS) or article_c0,
                        "c1_id": context_value(sample_context, C1_PATTERNS) or article_c1,
                    }
                )

    # De-duplicate cells caught by both orientations.
    unique = {}
    for row in result:
        key = (row["candidate_id"], norm(row["sample_label"]), row["reported_value"])
        unique[key] = row
    result = list(unique.values())
    descriptor_count = len({row["candidate_id"] for row in result})
    if not result:
        return [], {"sensory_table": True, "reason": "NO_SAMPLE_DESCRIPTOR_NUMERIC_CELLS"}
    if descriptor_count < 2 and not re.search(
        r"sensor|descriptor|cata", sensory_context, flags=re.I
    ):
        return [], {"sensory_table": True, "reason": "INSUFFICIENT_DESCRIPTOR_AXIS_EVIDENCE"}

    table_context = f"{article_text} {table['caption']}"
    info = {
        "sensory_table": True,
        "reason": None,
        "panel_size": find_panel_size(table_context),
        "sample_count": len({norm(row["sample_label"]) for row in result}),
        "scale": find_scale(table_context),
        "aggregation": aggregation(f"{table['caption']} {' '.join(sum(rows, []))}"),
        "replicate_structure": find_replicates(table_context),
    }
    return result, info


def base_sample_key(sample_label: str, article_text: str) -> str:
    """Remove experimental condition tokens while retaining a coffee identity.

    The same coffee crossed over brew, roast, storage, pressure, time, or
    temperature conditions must stay in one group for leakage-safe splitting.
    """
    value = norm(sample_label)
    # Explicit species labels are genuine coffee identities, not preparation
    # conditions, and survive the conservative condition collapse below.
    species = re.findall(r"\b(?:arabica|robusta|canephora|liberica|excelsa)\b", value)
    if len(set(species)) == 1:
        return species[0]
    # Preserve the two source-reported regional coffee identities even where
    # the published table truncates the label in a multi-row header.
    if re.search(r"\bhuila\b|\bhui\b", value):
        return "huila"
    if re.search(r"\bnari(?: o)?\b|\bnar\b", value):
        return "narino"
    value = re.sub(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])", " ", value)
    value = re.sub(
        r"\b(?:cold|hot|brew|brewed|espresso|filter|filtered|moka|neapolitan|pot|"
        r"immersion|drip|percolation|french|press|light|medium|dark|roast|roasted|"
        r"freshly|stored|storage|control|group|holding|time|temperature|pressure|"
        r"natural|honey|semiwashed|semi washed|washed|wet|dry|drying|dryer|terrace|"
        r"oven|cast|tape|fixed|bed|rotary|drum|combined|processed|process|method|"
        r"wine|nanoparticles?|regular|coarse|coars|fine|brewing|uhp|cb|h|l|m|d|"
        r"mpa|minutes?|mins?|hours?|hrs?|months?|days?|degrees?|celsius)\b",
        " ",
        value,
    )
    value = re.sub(r"\b\d+(?:\.\d+)?\b", " ", value)
    value = " ".join(value.split())
    if value in {"", "arabica robusta"} or re.fullmatch(
        r"(?:samples?|coffee|beans?|st|co|ctd|fbd|rdd|cd)(?: [a-z0-9]+)?", value
    ):
        return "article-base-coffee"
    return value[:160]


def extract_one(
    candidate: dict[str, Any],
    aliases: dict[str, str],
    existing_dois: set[str],
    cache_dir: Path,
    timeout: float,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    base = {
        "candidate_id": candidate["candidate_id"],
        "source_system": candidate["source_system"],
        "source_record_id": candidate["source_record_id"],
        "doi": candidate["doi"],
        "title": candidate["title"],
        "resolved_license_r10": candidate["resolved_license"],
        "query_ids": candidate["query_ids"],
    }
    if candidate["doi"].lower() in existing_dois:
        return base | {
            "outcome": "NOT_ADMITTED",
            "failure_reason": "DUPLICATE_EXISTING_SOURCE_DOI",
            "tables_scanned": 0,
            "sensory_tables": 0,
            "extracted_group_count": 0,
            "extracted_assertion_count": 0,
        }, []
    try:
        retrieval, external_metadata = choose_artifact(candidate, cache_dir, timeout)
        body = retrieval.pop("body")
    except Exception as exc:
        return base | {
            "outcome": "NOT_ADMITTED",
            "failure_reason": f"FULL_TEXT_RETRIEVAL_FAILED:{type(exc).__name__}",
            "failure_detail": str(exc)[:300],
            "tables_scanned": 0,
            "sensory_tables": 0,
            "extracted_group_count": 0,
            "extracted_assertion_count": 0,
        }, []

    content_type = retrieval["content_type"]
    if content_type == "application/pdf" or retrieval["final_url"].lower().endswith(".pdf"):
        return base | {
            "outcome": "NOT_ADMITTED",
            "failure_reason": "PDF_LAST_RESORT_NOT_MACHINE_READABLE_TABLE",
            "retrieval": retrieval,
            "tables_scanned": 0,
            "sensory_tables": 0,
            "extracted_group_count": 0,
            "extracted_assertion_count": 0,
        }, []

    try:
        if content_type in {"text/xml", "application/xml"} or body.lstrip().startswith(b"<?xml"):
            tables, parsed_metadata = parse_xml(body)
        else:
            tables, parsed_metadata = parse_html(body)
    except Exception as exc:
        return base | {
            "outcome": "NOT_ADMITTED",
            "failure_reason": f"FULL_TEXT_PARSE_FAILED:{type(exc).__name__}",
            "failure_detail": str(exc)[:300],
            "retrieval": retrieval,
            "tables_scanned": 0,
            "sensory_tables": 0,
            "extracted_group_count": 0,
            "extracted_assertion_count": 0,
        }, []

    metadata = dict(external_metadata)
    for key in ("title", "year"):
        metadata[key] = parsed_metadata.get(key) or metadata.get(key)
    for key in ("authors", "institutions"):
        metadata[key] = sorted(set(parsed_metadata.get(key, [])) | set(metadata.get(key, [])))
    article_text = parsed_metadata["plain_text"]
    license_id = source_license(body, content_type) or metadata.get("crossref_license")
    license_ok = license_id in ALLOWED and "-ND-" not in (license_id or "")
    if not license_ok:
        return base | {
            "outcome": "NOT_ADMITTED",
            "failure_reason": "SOURCE_LICENSE_NOT_REVERIFIED_ALLOWED_NON_ND",
            "retrieval": retrieval,
            "source_verified_license": license_id,
            "tables_scanned": len(tables),
            "sensory_tables": 0,
            "extracted_group_count": 0,
            "extracted_assertion_count": 0,
        }, []

    source_family = "family.r11." + digest(candidate["doi"].lower().encode())[:20]
    extracted: list[dict[str, Any]] = []
    table_summaries = []
    for table in tables:
        rows, info = table_records(candidate, table, aliases, article_text, metadata)
        table_id = table["table_id"]
        table_summary = {
            "table_id": table_id,
            "label": table["label"][:120],
            "caption_sha256": digest(table["caption"].encode()),
            "row_count": len(table["rows"]),
            **info,
            "extracted_assertion_count": len(rows),
        }
        table_summaries.append(table_summary)
        for row in rows:
            sample_key = norm(row["sample_label"])
            coffee_key = base_sample_key(row["sample_label"], article_text)
            group_id = "r11.group:" + digest(
                f"{candidate['doi'].lower()}|{coffee_key}".encode()
            )[:24]
            condition_id = "r11.condition:" + digest(
                f"{candidate['doi'].lower()}|{table_id}|{sample_key}".encode()
            )[:24]
            record_id = "r11.assertion:" + digest(
                f"{group_id}|{row['candidate_id']}|{row['reported_value']}".encode()
            )[:24]
            extracted.append(
                {
                    "record_id": record_id,
                    "coffee_group_id": group_id,
                    "canonical_trial_id": "r11.trial:" + digest(candidate["doi"].lower().encode())[:24],
                    "source_family_id": source_family,
                    "source_system": candidate["source_system"],
                    "source_record_id": candidate["source_record_id"],
                    "source_doi": candidate["doi"],
                    "source_url": retrieval["final_url"],
                    "source_sha256": retrieval["sha256"],
                    "resolved_license": license_id,
                    "share_alike_obligation": license_id in {"CC-BY-SA-4.0", "ODbL-1.0"},
                    "attribution_string": f"{metadata.get('title') or candidate['title']}. https://doi.org/{candidate['doi']}",
                    "table_id": table_id,
                    "table_caption_sha256": digest(table["caption"].encode()),
                    "panel_size": info.get("panel_size"),
                    "table_sample_count": info.get("sample_count"),
                    "scale": info.get("scale"),
                    "aggregation": info.get("aggregation"),
                    "replicate_structure": info.get("replicate_structure"),
                    "sample_label": row["sample_label"][:240],
                    "sample_label_normalized": sample_key,
                    "base_coffee_identity_normalized": coffee_key,
                    "sample_condition_id": condition_id,
                    "canonical_candidate_id": row["candidate_id"],
                    "raw_descriptor": row["raw_descriptor"][:160],
                    "reported_value": row["reported_value"],
                    "reported_value_raw": row["reported_value_raw"][:80],
                    "c0_id": row["c0_id"],
                    "c1_id": row["c1_id"],
                    "track": "COFFEE_PROFESSIONAL_SUPERVISION",
                    "participant_pii_present": False,
                    "authors": metadata["authors"],
                    "institutions": metadata["institutions"],
                    "publication_year": metadata["year"],
                }
            )

    # Merge repeated cells within a candidate deterministically.
    unique = {row["record_id"]: row for row in extracted}
    extracted = [unique[key] for key in sorted(unique)]
    groups = {row["coffee_group_id"] for row in extracted}
    sensory_tables = sum(row.get("sensory_table", False) for row in table_summaries)
    if extracted:
        outcome = "ADMITTED_STRUCTURED_SAMPLE_DESCRIPTOR_DATA"
        reason = None
    elif not tables:
        outcome = "NOT_ADMITTED"
        reason = "NO_MACHINE_READABLE_TABLES"
    elif not sensory_tables:
        outcome = "NOT_ADMITTED"
        reason = "NO_SENSORY_DESCRIPTOR_TABLE"
    else:
        outcome = "NOT_ADMITTED"
        reason = "NO_ADMISSIBLE_SAMPLE_DESCRIPTOR_CELLS"
    result = base | {
        "outcome": outcome,
        "failure_reason": reason,
        "retrieval": retrieval,
        "source_verified_license": license_id,
        "source_family_id": source_family,
        "authors": metadata["authors"],
        "institutions": metadata["institutions"],
        "publication_year": metadata["year"],
        "tables_scanned": len(tables),
        "sensory_tables": sensory_tables,
        "extracted_group_count": len(groups),
        "extracted_assertion_count": len(extracted),
        "table_summaries": table_summaries,
    }
    return result, extracted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--timeout", type=float, default=35.0)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    candidates, input_sha = load_candidates(args.input)
    aliases = descriptor_aliases(load_candidate_universe())
    existing = json.loads((R10 / "resolved_source_licenses.json").read_text())
    existing_dois = {row["doi"].lower() for row in existing["sources"] if row.get("doi")}
    outcomes: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(
                extract_one, candidate, aliases, existing_dois, args.cache_dir, args.timeout
            ): candidate["candidate_id"]
            for candidate in candidates
        }
        for index, future in enumerate(as_completed(future_map), 1):
            candidate_id = future_map[future]
            try:
                outcome, extracted = future.result()
            except Exception as exc:
                outcome = {
                    "candidate_id": candidate_id,
                    "outcome": "NOT_ADMITTED",
                    "failure_reason": f"UNHANDLED_EXTRACTION_ERROR:{type(exc).__name__}",
                    "failure_detail": str(exc)[:300],
                    "tables_scanned": 0,
                    "sensory_tables": 0,
                    "extracted_group_count": 0,
                    "extracted_assertion_count": 0,
                }
                extracted = []
            outcomes.append(outcome)
            records.extend(extracted)
            if index % 20 == 0 or index == len(candidates):
                with PRINT_LOCK:
                    print(f"completed {index}/{len(candidates)}")

    outcomes.sort(key=lambda row: row["candidate_id"])
    records.sort(key=lambda row: row["record_id"])
    failure_counts = Counter(
        row.get("failure_reason") or "ADMITTED" for row in outcomes
    )
    report = {
        "contract_version": "r11.frozen-248-table-extraction.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "R10_FROZEN_248_CANDIDATES_NO_NEW_SEARCH",
        "input": {
            "path": str(args.input.relative_to(ROOT)),
            "sha256": input_sha,
            "candidate_count": len(candidates),
        },
        "guards": {
            "training_run_count": 0,
            "fit_count": 0,
            "prose_claims_used_as_supervision": False,
            "participant_pii_retained": False,
            "unresolved_or_nd_license_admitted": False,
            "descriptor_mapping": "EXACT_GOVERNED_IDENTIFIER_LABEL_ONLY_NO_PARENT_EXPANSION",
        },
        "summary": {
            "candidate_count": len(outcomes),
            "candidate_outcome_counts": dict(sorted(Counter(row["outcome"] for row in outcomes).items())),
            "failure_reason_counts": dict(sorted(failure_counts.items())),
            "machine_readable_table_count": sum(row.get("tables_scanned", 0) for row in outcomes),
            "sensory_table_count": sum(row.get("sensory_tables", 0) for row in outcomes),
            "new_assertion_count_pre_dedup": len(records),
            "new_group_count_pre_dedup": len({row["coffee_group_id"] for row in records}),
            "c0_group_count_pre_dedup": len(
                {row["coffee_group_id"] for row in records if row["c0_id"]}
            ),
            "c1_group_count_pre_dedup": len(
                {row["coffee_group_id"] for row in records if row["c1_id"]}
            ),
        },
        "candidate_outcomes": outcomes,
        "extracted_records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(stable_bytes(report))
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
