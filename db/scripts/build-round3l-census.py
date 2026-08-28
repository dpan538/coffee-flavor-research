#!/usr/bin/env python3
"""Freeze the reconciled Round 3L professional-source census.

The input HTML is an official, locally cached discovery snapshot.  It is not
copied into the repository; only its hash, canonical URL, and factual edition
links are retained.  The generated census is intentionally immutable during a
Round 3L run.  Acquisition attempts live in separate lane ledgers.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ROUND3K = ROOT / "db" / "data" / "round3k"
ROUND3L = ROOT / "db" / "data" / "round3l"
COE_ARCHIVE_URL = (
    "https://allianceforcoffeeexcellence.org/competition-auction-results/"
)

CENSUS_COLUMNS = (
    "census_item_key",
    "item_kind",
    "parent_key",
    "series_key",
    "source_family_key",
    "edition_label",
    "year",
    "country_or_community",
    "category_or_round",
    "official_url",
    "discovery_basis",
    "source_snapshot_sha256",
    "corpus_state",
    "acquisition_state",
    "rights_state",
    "attempt_status",
    "note",
)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class CoeEdition:
    country: str
    program: str
    label: str
    year: int
    url: str
    pilot: bool


class CoeMenuParser(HTMLParser):
    """Extract the nested official COE country/program/year menu."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_root = False
        self.root_ul_depth = 0
        self.li_stack: list[dict[str, str]] = []
        self.in_anchor = False
        self.anchor_href: str | None = None
        self.anchor_text: list[str] = []
        self.rows: list[CoeEdition] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key: value or "" for key, value in attrs}

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = self._attrs(attrs)
        if tag == "ul" and attributes.get("id") == "menu-coe-country-programs-menu":
            self.in_root = True
            self.root_ul_depth = 1
            return
        if not self.in_root:
            return
        if tag == "ul":
            self.root_ul_depth += 1
        elif tag == "li":
            self.li_stack.append({"label": ""})
        elif tag == "a":
            self.in_anchor = True
            self.anchor_href = attributes.get("href") or None
            self.anchor_text = []

    def handle_data(self, data: str) -> None:
        if self.in_root and self.in_anchor:
            self.anchor_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.in_root:
            return
        if tag == "a":
            text = " ".join("".join(self.anchor_text).split())
            if self.li_stack and not self.anchor_href and text:
                self.li_stack[-1]["label"] = text
            elif self.anchor_href and text:
                match = re.search(r"\b(19|20)\d{2}\b", text)
                labels = [entry["label"] for entry in self.li_stack[:-1]]
                labels = [label for label in labels if label]
                if match and labels:
                    country = labels[0]
                    program = labels[-1]
                    self.rows.append(
                        CoeEdition(
                            country=html.unescape(country),
                            program=html.unescape(program),
                            label=html.unescape(text),
                            year=int(match.group(0)),
                            url=self.anchor_href,
                            pilot="pilot" in text.lower(),
                        )
                    )
            self.anchor_href = None
            self.anchor_text = []
            self.in_anchor = False
        elif tag == "li" and self.li_stack:
            self.li_stack.pop()
        elif tag == "ul":
            self.root_ul_depth -= 1
            if self.root_ul_depth == 0:
                self.in_root = False


def parse_coe_editions(path: Path) -> list[CoeEdition]:
    parser = CoeMenuParser()
    parser.feed(path.read_text(encoding="utf-8"))
    unique: dict[tuple[str, str], CoeEdition] = {}
    for row in parser.rows:
        unique[(row.label, row.url)] = row
    return sorted(
        unique.values(), key=lambda row: (slug(row.country), row.year, row.url)
    )


def empty_row(**values: str) -> dict[str, str]:
    row = {column: "" for column in CENSUS_COLUMNS}
    row.update(values)
    row.setdefault("corpus_state", "DISCOVERED")
    return row


def build_rows(
    coe_editions: list[CoeEdition], snapshot_hash: str
) -> tuple[list[dict[str, str]], dict[str, object]]:
    rows: list[dict[str, str]] = []
    series = read_tsv(ROUND3K / "COMPETITION_SERIES.tsv")
    editions = read_tsv(ROUND3K / "COMPETITION_EDITION.tsv")
    access = read_tsv(ROUND3K / "SOURCE_ACCESS_MATRIX.tsv")
    archives = read_tsv(ROUND3K / "RESULT_ARCHIVE_INVENTORY.tsv")
    scoresheets = read_tsv(ROUND3K / "SCORESHEET_INVENTORY.tsv")

    for item in series:
        rows.append(
            empty_row(
                census_item_key=f"series:{item['series_key']}",
                item_kind="COMPETITION_SERIES",
                parent_key="",
                series_key=item["series_key"],
                source_family_key=item["series_key"],
                edition_label=item["series_name"],
                country_or_community=item["competition_level"],
                official_url=item["official_url"],
                discovery_basis="ROUND3K_RECONCILED_SERIES",
                source_snapshot_sha256="",
                corpus_state="DISCOVERED",
                acquisition_state="DISCOVERED_ONLY",
                rights_state="UNKNOWN",
                attempt_status="NOT_ATTEMPTED",
                note=item["limitation"],
            )
        )

    for item in access:
        rights_values = {
            item[field]
            for field in (
                "public_results_use",
                "public_descriptor_use",
                "internal_research_use",
                "public_derived_release",
                "model_research_use",
                "commercial_model_use",
            )
        }
        rows.append(
            empty_row(
                census_item_key=f"source:{item['source_key']}",
                item_kind="SOURCE_ACCESS_ROUTE",
                parent_key=f"series:{item['series_key']}",
                series_key=item["series_key"],
                source_family_key=item["source_family_key"],
                edition_label=item["official_owner"],
                category_or_round=item["source_type"],
                official_url=item["official_url"],
                discovery_basis="ROUND3K_RECONCILED_ACCESS_MATRIX",
                source_snapshot_sha256="",
                corpus_state="DISCOVERED",
                acquisition_state=item["access_state"],
                rights_state=(
                    next(iter(rights_values))
                    if len(rights_values) == 1
                    else "MIXED_OR_DIMENSION_SPECIFIC"
                ),
                attempt_status="NOT_ATTEMPTED",
                note=item["note"],
            )
        )

    live_coe_pairs: set[tuple[str, int]] = set()
    for edition in coe_editions:
        live_coe_pairs.add((slug(edition.country), edition.year))
        url_slug = slug(edition.url.removeprefix("https://").strip("/"))
        item_key = f"edition:coe:{url_slug}:{slug(edition.label)}"
        rows.append(
            empty_row(
                census_item_key=item_key,
                item_kind=("PILOT_EDITION" if edition.pilot else "COMPETITION_EDITION"),
                parent_key="series:coe",
                series_key="coe",
                source_family_key=f"coe_{slug(edition.country)}",
                edition_label=f"{edition.program} {edition.label}",
                year=str(edition.year),
                country_or_community=edition.country,
                category_or_round=edition.program,
                official_url=edition.url,
                discovery_basis="LIVE_OFFICIAL_COE_ARCHIVE_2026_08_28",
                source_snapshot_sha256=snapshot_hash,
                corpus_state="DISCOVERED",
                acquisition_state="PUBLIC_OFFICIAL_EDITION_ROUTE",
                rights_state="UNKNOWN_DIMENSION_SPECIFIC",
                attempt_status="NOT_ATTEMPTED",
                note=(
                    "Official archive labels this as a pilot, retained separately."
                    if edition.pilot
                    else "Official archive country/program edition row."
                ),
            )
        )

    # The live archive is one full edition lower than the Round 2 frozen count.
    # Round 3K had separately verified Taiwan 2026.  Preserve that discovered
    # edition as stale/removed rather than erasing it or fabricating a substitute.
    retained_stale_coe: list[str] = []
    for item in editions:
        if item["series_key"] == "coe":
            pair = (slug(item["country_or_community"]), int(item["year"]))
            if pair in live_coe_pairs:
                continue
            retained_stale_coe.append(item["edition_key"])
        rows.append(
            empty_row(
                census_item_key=f"edition:{item['edition_key']}",
                item_kind="COMPETITION_EDITION",
                parent_key=f"series:{item['series_key']}",
                series_key=item["series_key"],
                source_family_key=item["series_key"],
                edition_label=item["edition_label"],
                year=item["year"],
                country_or_community=item["country_or_community"],
                category_or_round=item["edition_type"],
                official_url=item["official_url"],
                discovery_basis=(
                    "ROUND3K_VERIFIED_STALE_OR_REMOVED_FROM_LIVE_ARCHIVE"
                    if item["series_key"] == "coe"
                    else "ROUND3K_RECONCILED_EDITION"
                ),
                source_snapshot_sha256="",
                corpus_state="DISCOVERED",
                acquisition_state="DISCOVERED_ONLY",
                rights_state="UNKNOWN_DIMENSION_SPECIFIC",
                attempt_status="NOT_ATTEMPTED",
                note=item["note"],
            )
        )

    for item in archives:
        rows.append(
            empty_row(
                census_item_key=f"archive:{item['archive_key']}",
                item_kind="RESULT_ARCHIVE",
                parent_key=f"series:{item['series_key']}",
                series_key=item["series_key"],
                source_family_key=item["series_key"],
                edition_label=item["edition_range"],
                category_or_round=item["archive_type"],
                official_url=item["official_url"],
                discovery_basis="ROUND3K_RECONCILED_RESULT_ARCHIVE",
                source_snapshot_sha256="",
                corpus_state="DISCOVERED",
                acquisition_state=item["access_state"],
                rights_state=item["rights_state"],
                attempt_status="NOT_ATTEMPTED",
                note=item["note"],
            )
        )

    for item in scoresheets:
        rows.append(
            empty_row(
                census_item_key=f"scoresheet:{item['scoresheet_key']}",
                item_kind="SCORESHEET",
                parent_key=f"series:{item['series_key']}",
                series_key=item["series_key"],
                source_family_key=item["series_key"],
                edition_label=f"{item['series_key']} {item['year']}",
                year=item["year"],
                category_or_round=f"{item['category']}|{item['round']}|{item['scoresheet_type']}",
                official_url=item["official_url"],
                discovery_basis="ROUND3K_RECONCILED_SCORESHEET",
                source_snapshot_sha256="",
                corpus_state="DISCOVERED",
                acquisition_state=item["access_state"],
                rights_state="UNKNOWN_DIMENSION_SPECIFIC",
                attempt_status="NOT_ATTEMPTED",
                note=item["note"],
            )
        )

    rows.append(
        empty_row(
            census_item_key="edition_claim:best_of_panama:30th_edition_2026",
            item_kind="EDITION_COUNT_CLAIM",
            parent_key="series:best_of_panama",
            series_key="best_of_panama",
            source_family_key="best_of_panama",
            edition_label="Best of Panama is the 30th edition in 2026",
            year="2026",
            country_or_community="Panama",
            official_url="https://bestofpanama.org/about2026",
            discovery_basis="ROUND2_OFFICIAL_PROGRAM_COUNT_NOT_YEAR_ENUMERATION",
            source_snapshot_sha256="",
            corpus_state="DISCOVERED",
            acquisition_state="HISTORICAL_EDITION_ENUMERATION_REQUIRED",
            rights_state="UNKNOWN_DIMENSION_SPECIFIC",
            attempt_status="NOT_ATTEMPTED",
            note=(
                "Preserves the official ordinal without inventing 29 historical "
                "year rows; exact editions must be enumerated from official evidence."
            ),
        )
    )

    kind_order = {
        "COMPETITION_SERIES": 0,
        "SOURCE_ACCESS_ROUTE": 1,
        "COMPETITION_EDITION": 2,
        "PILOT_EDITION": 3,
        "EDITION_COUNT_CLAIM": 4,
        "RESULT_ARCHIVE": 5,
        "SCORESHEET": 6,
    }
    rows.sort(key=lambda row: (kind_order[row["item_kind"]], row["census_item_key"]))
    keys = [row["census_item_key"] for row in rows]
    if len(keys) != len(set(keys)):
        duplicates = sorted(key for key in set(keys) if keys.count(key) > 1)
        raise ValueError(f"duplicate census keys: {duplicates}")

    edition_rows = [
        row
        for row in rows
        if row["item_kind"] in {"COMPETITION_EDITION", "PILOT_EDITION"}
    ]
    coe_full = [
        row
        for row in edition_rows
        if row["series_key"] == "coe" and row["item_kind"] == "COMPETITION_EDITION"
    ]
    coe_pilots = [
        row
        for row in edition_rows
        if row["series_key"] == "coe" and row["item_kind"] == "PILOT_EDITION"
    ]
    wcc_bodies = [
        row
        for row in rows
        if row["item_kind"] == "SOURCE_ACCESS_ROUTE"
        and row["series_key"] == "wcc_competition_body_registry"
        and row["category_or_round"] == "WCC_COMPETITION_BODY_REGISTRY_RECORD"
    ]
    reconciliation: dict[str, object] = {
        "census_version": "round3l-census-v1-2026-08-28",
        "freeze_rule": (
            "Immutable during this run; acquisition attempts and newly discovered "
            "mirrors are recorded in lane ledgers without rewriting the seed census."
        ),
        "round2_seed_claims": {
            "coe_full_country_editions": 225,
            "coe_pilot_editions": 2,
            "best_of_panama_edition_ordinal_2026": 30,
            "wcc_world_series": 7,
            "wcc_competition_body_lower_bound": 50,
        },
        "live_official_coe_snapshot": {
            "url": COE_ARCHIVE_URL,
            "sha256": snapshot_hash,
            "full_editions": sum(not edition.pilot for edition in coe_editions),
            "pilot_editions": sum(edition.pilot for edition in coe_editions),
        },
        "reconciled_counts": {
            "competition_series": len(series),
            "source_access_routes": len(access),
            "wcc_competition_bodies": len(wcc_bodies),
            "known_edition_rows": len(edition_rows),
            "coe_full_editions": len(coe_full),
            "coe_pilot_editions": len(coe_pilots),
            "result_archives": len(archives),
            "scoresheets": len(scoresheets),
            "total_census_items": len(rows),
        },
        "reconciliation_decisions": {
            "retained_stale_or_removed_coe_editions": retained_stale_coe,
            "live_coe_delta_vs_round2_full_count": len(coe_full)
            - 225,
            "bop_historical_year_rows_invented": 0,
        },
    }
    if len(coe_full) != 225 or len(coe_pilots) != 2:
        raise ValueError(
            "Round 2 CoE reconciliation failed: expected 225 full plus 2 pilots, "
            f"got {len(coe_full)} full plus {len(coe_pilots)} pilots"
        )
    return rows, reconciliation


def write_tsv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=CENSUS_COLUMNS, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coe-html", type=Path, required=True)
    parser.add_argument("--retrieved-at", required=True)
    args = parser.parse_args()
    if not args.coe_html.is_file():
        parser.error(f"missing official COE snapshot: {args.coe_html}")

    snapshot_hash = sha256(args.coe_html)
    coe_editions = parse_coe_editions(args.coe_html)
    rows, reconciliation = build_rows(coe_editions, snapshot_hash)
    reconciliation["live_official_coe_snapshot"]["retrieved_at"] = args.retrieved_at
    reconciliation["live_official_coe_snapshot"]["byte_count"] = (
        args.coe_html.stat().st_size
    )

    ROUND3L.mkdir(parents=True, exist_ok=True)
    write_tsv(ROUND3L / "SOURCE_UNIVERSE.tsv", rows)
    (ROUND3L / "CENSUS_RECONCILIATION.json").write_text(
        json.dumps(reconciliation, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    print(f"CENSUS_ITEM_COUNT={len(rows)}")
    print(
        "KNOWN_EDITION_COUNT="
        + str(
            sum(
                row["item_kind"] in {"COMPETITION_EDITION", "PILOT_EDITION"}
                for row in rows
            )
        )
    )
    print("COE_RECONCILIATION=225_FULL_PLUS_2_PILOTS")


if __name__ == "__main__":
    main()
