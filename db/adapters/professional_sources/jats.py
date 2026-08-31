"""Small standard-library JATS adapters for governed professional sources.

The adapter returns source-native strings only to the caller operating inside
an owner-controlled restricted root. Public generators hash those values
before writing repository artifacts.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def compact_text(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).replace("\xa0", " ").split())


def article_metadata(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()

    def text_at(query: str) -> str:
        node = root.find(query)
        return compact_text(node) if node is not None else ""

    title = text_at(".//article-title")
    journal = text_at(".//journal-title")
    year = text_at(".//pub-date/year")
    license_text = text_at(".//license")
    return {"title": title, "journal": journal, "year": year, "license": license_text}


def find_table(path: Path, label: str) -> ET.Element:
    root = ET.parse(path).getroot()
    for wrap in root.findall(".//table-wrap"):
        label_node = wrap.find("label")
        if label_node is not None and compact_text(label_node).casefold() == label.casefold():
            table = wrap.find("table")
            if table is None:
                break
            return table
    raise RuntimeError(f"JATS table not found: {path.name} {label}")


def _cells(row: ET.Element) -> list[ET.Element]:
    return [cell for cell in row if cell.tag.rsplit("}", 1)[-1] in {"td", "th"}]


def expanded_rows(section: ET.Element) -> list[list[str]]:
    """Expand HTML/JATS rowspans and colspans to a rectangular text matrix."""

    active: dict[int, tuple[int, str]] = {}
    result: list[list[str]] = []
    for tr in section.findall("tr"):
        output: dict[int, str] = {}
        for column, (remaining, value) in list(active.items()):
            output[column] = value
            if remaining <= 1:
                del active[column]
            else:
                active[column] = (remaining - 1, value)
        column = 0
        for cell in _cells(tr):
            while column in output:
                column += 1
            value = compact_text(cell)
            colspan = int(cell.attrib.get("colspan", "1"))
            rowspan = int(cell.attrib.get("rowspan", "1"))
            for offset in range(colspan):
                output[column + offset] = value
                if rowspan > 1:
                    active[column + offset] = (rowspan - 1, value)
            column += colspan
        if output:
            result.append([output.get(index, "") for index in range(max(output) + 1)])
    return result


def table_body(path: Path, label: str) -> list[list[str]]:
    table = find_table(path, label)
    body = table.find("tbody")
    if body is None:
        raise RuntimeError(f"JATS table has no body: {path.name} {label}")
    return expanded_rows(body)


def table_headers(path: Path, label: str) -> list[list[str]]:
    table = find_table(path, label)
    head = table.find("thead")
    return expanded_rows(head) if head is not None else []


def source_relations(path: Path, pmcid: str) -> list[dict[str, str]]:
    """Extract explicit definition/category relations from five admitted tables."""

    rows: list[dict[str, str]] = []

    def add(term: str, definition: str, locator: str, relation: str = "EXPLICIT_DEFINITION_MATCH") -> None:
        term = term.strip()
        definition = definition.strip()
        if term and definition:
            rows.append({
                "term": term,
                "definition_or_category": definition,
                "relation_type": relation,
                "source_locator": locator,
            })

    if pmcid == "PMC8774372":
        for index, row in enumerate(table_body(path, "Table 3"), start=1):
            if len(row) >= 2:
                add(row[0], row[1], f"PMC8774372#table-3-row-{index}")
    elif pmcid == "PMC13163763":
        for index, row in enumerate(table_body(path, "Table 2"), start=1):
            if len(row) >= 3:
                add(row[1], row[2], f"PMC13163763#table-2-row-{index}")
    elif pmcid == "PMC11675256":
        for index, row in enumerate(table_body(path, "Table 1"), start=1):
            if len(row) >= 2:
                add(row[0], row[1], f"PMC11675256#table-1-row-{index}")
    elif pmcid == "PMC13279845":
        for index, row in enumerate(table_body(path, "TABLE 1"), start=1):
            if len(row) >= 2 and row[1] and row[0] not in {"Appearance", "Aroma", "Flavor", "Texture"}:
                add(row[0], row[1], f"PMC13279845#table-1-row-{index}")
    elif pmcid == "PMC6776322":
        headers = table_headers(path, "Table 2")
        if not headers:
            raise RuntimeError("PMC6776322 Table 2 headers missing")
        descriptor_headers = [
            value for value in headers[-1]
            if value and value.casefold() not in {"sample", "effect", "p-value", "f-value"}
        ]
        for index, term in enumerate(descriptor_headers, start=1):
            add(
                term,
                "retronasal coffee aroma descriptor",
                f"PMC6776322#table-2-column-{index}",
                "EXPLICIT_BROADER_NARROWER",
            )
    else:
        raise RuntimeError(f"no admitted semantic adapter for {pmcid}")
    return rows


def brewed_black_coffee_observations(path: Path) -> list[dict[str, Any]]:
    """Extract positive trained-panel aggregate intensities from PMC8774372."""

    headers = table_headers(path, "Table 4")
    if len(headers) < 2:
        raise RuntimeError("PMC8774372 Table 4 sample headers missing")
    sample_headers = [value for value in headers[-1] if re.fullmatch(r"\d{3} \([lmd]\)", value)]
    if len(sample_headers) != 8:
        raise RuntimeError(f"PMC8774372 sample-header drift: {sample_headers}")
    observations: list[dict[str, Any]] = []
    for row_index, row in enumerate(table_body(path, "Table 4"), start=1):
        if len(row) < 9:
            continue
        attribute = row[0]
        for sample_index, sample in enumerate(sample_headers, start=1):
            match = re.search(r"-?\d+(?:\.\d+)?", row[sample_index])
            if match is None:
                raise RuntimeError(f"PMC8774372 intensity parse drift at row {row_index}, sample {sample}")
            intensity = float(match.group(0))
            if intensity <= 0:
                continue
            observations.append({
                "attribute": attribute,
                "sample": sample,
                "intensity": intensity,
                "roast_class": {"l": "LIGHT", "m": "MEDIUM", "d": "DARK"}[sample[-2]],
                "source_locator": f"PMC8774372#table-4-row-{row_index}-sample-{sample[:3]}",
            })
    return observations
