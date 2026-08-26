#!/usr/bin/env python3
"""Extract reviewed zh-Hans sensory expressions from frozen guchengf HTML.

The extraction boundary is deliberately narrow and review-driven. Only exact
substrings listed below may be emitted, and each substring must still occur in
the expected author-written ``main > p`` paragraph of an immutable raw HTML
snapshot. No translation, ontology mapping, or model-derived selection occurs.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RAW_RELATIVE = Path(
    "db/data/round3j/raw/"
    "candidate.r3j.guchengf-coffee-reviews-2025/"
    "2025-posts-snapshot-20260826"
)
RAW_DIR = ROOT / RAW_RELATIVE
OUTPUT_RELATIVE = Path(
    "db/data/round3j/derived/"
    "guchengf_2025_zh_hans_sensory_expressions.tsv"
)
OUTPUT_PATH = ROOT / OUTPUT_RELATIVE
MANIFEST_RELATIVE = RAW_RELATIVE / "ACQUISITION_MANIFEST.json"
MANIFEST_PATH = ROOT / MANIFEST_RELATIVE

CANDIDATE_KEY = "candidate.r3j.guchengf-coffee-reviews-2025"
SOURCE_FAMILY_KEY = "family.zh-hans.guchengf-gucheen"
SOURCE_KEY = "guchengf.gucheen.coffee-reviews-2025"
SOURCE_VERSION = "2025-posts-snapshot-20260826"
SNAPSHOT_KEY = "snapshot.round3j.guchengf-2025-posts-20260826"
SOURCE_OWNER = "gucheen"
LICENSE_EXPRESSION = "CC-BY-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
SITE_LICENSE_URL = "https://guchengf.me/#licenses"
REGISTERED_SOURCE_URL = "https://guchengf.me/blog/"
EXPECTED_MANIFEST_SHA256 = (
    "3de9a815409774f815bc0d6dee6255d4e21eebc0b10062634a4b531d3a85302e"
)
EXPECTED_FILE_HASHES = {
    "00_home.html": "822da848a0cb1da0f3454cd0e44f61b2853a3e751c13375fdd55ea465c4c7a8a",
    "01_sangaria-crown-coffee-260ml.html": "56b2fd603f9690c27605ac9183908e46a92da9ae33da12136e9f092442b6b542",
    "02_review-georgia-the-black-coffee-500ml.html": "4d59ea2920dfa7a0e769ae20e0437853ade00ed9f50efc470550fe7b751edc6a",
    "03_review-ucc-shokunin-no-coffee-sugar-free-black-900ml.html": "66903b74256748af4b16f6a0f2d75d01861dd1c08e5875de7b8104bcfbfe113b",
    "04_review-kirin-fire-one-day-black-coffee-600-ml.html": "51abc486d0ba3a446fa1c588474ae89b2479130b6a941a5e968f343ad08de167",
}
EXPECTED_RAW_FILENAMES = set(EXPECTED_FILE_HASHES) | {
    "ACQUISITION_MANIFEST.json",
    "SHA256SUMS",
}
HOME_LICENSE_DECLARATION = (
    "网站内容除单独授权（优先）外，均以 "
    '<a rel="license" href="https://creativecommons.org/licenses/by/4.0/deed.zh-hans">'
    "知识共享署名 4.0 国际许可协议（CC BY 4.0）</a> 发布。"
)
WHITESPACE_RE = re.compile(r"\s+")
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

FIELDS = [
    "training_example_key",
    "effective_unit_key",
    "language_expression_key",
    "language_code",
    "source_family_key",
    "source_key",
    "source_version",
    "snapshot_key",
    "candidate_key",
    "registered_source_url",
    "source_owner",
    "repository",
    "document_key",
    "document_title",
    "document_date",
    "document_url",
    "raw_file_path",
    "raw_file_sha256",
    "acquisition_manifest_path",
    "acquisition_manifest_sha256",
    "source_locator",
    "raw_source_excerpt",
    "raw_source_phrase",
    "normalized_expression",
    "expression_role",
    "source_authored",
    "machine_translated",
    "project_translation",
    "artificial_variant",
    "review_state",
    "label_lifecycle",
    "mapping_disposition",
    "candidate_target_keys",
    "gold_label",
    "sampling_eligible",
    "counts_toward_governed_total",
    "admission_state",
    "duplicate_group_key",
    "duplicate_disposition",
    "expression_occurrence_count",
    "expression_document_count",
    "normalization_rule",
    "dedupe_rule",
    "extraction_method",
    "license_expression",
    "license_url",
    "site_license_url",
    "rights_state",
    "rights_basis_locator",
    "raw_text_public_export_allowed",
    "derived_expression_public_release_allowed",
    "model_research_use_allowed",
    "privacy_state",
    "provenance_json",
    "limitation",
]

DOCUMENT_SPECS: list[dict[str, Any]] = [
    {
        "document_key": "document.zh_hans.guchengf_2025_001",
        "filename": "01_sangaria-crown-coffee-260ml.html",
        "title": "饮料评测：SANGARIA 三佳利皇冠黑咖啡",
        "date": "2025-02-12",
        "url": "https://guchengf.me/blog/sangaria-crown-coffee-260ml/",
        "paragraphs": [
            {
                "text": "属于日本人喜爱的铁皮罐头咖啡。我觉得日式咖啡最大的特点就是烘焙的味道非常重，同时基本都属于是苦味大于酸味的，因为我本人更偏爱苦味的咖啡，所以日式咖啡都比较符合我的口味。",
                "phrases": ["烘焙的味道非常重", "苦味大于酸味"],
            },
            {
                "text": "三佳利的这款皇冠咖啡，在同类的日式铁皮罐头咖啡中，苦味算是轻的，突出烘焙的味道，其他则没有太特殊的，在同类产品中应该算是比较淡的咖啡。",
                "phrases": ["苦味算是轻的", "突出烘焙的味道", "比较淡的咖啡"],
            },
        ],
    },
    {
        "document_key": "document.zh_hans.guchengf_2025_002",
        "filename": "02_review-georgia-the-black-coffee-500ml.html",
        "title": "饮料评测：GEORGIA 乔尼亚 THE BLACK 咖啡 500ml",
        "date": "2025-02-12",
        "url": "https://guchengf.me/blog/review-georgia-the-black-coffee-500ml/",
        "paragraphs": [
            {
                "text": "口感基本符合常见的日式烘焙咖啡口感，但是是属于酸味比较明显的咖啡。含有食用香料。日本的罐装咖啡很多都含有食用香精，让我不得不怀疑所谓的日式烘焙咖啡口感完全来自于香精。",
                "phrases": [
                    "口感基本符合常见的日式烘焙咖啡口感",
                    "酸味比较明显",
                ],
            },
            {
                "text": "总体来说，不能评价它为好喝，缺点在于入口大约2-3秒后那种怪异的很突兀的酸苦感，不知道是否是刻意为之。作为喜欢偏苦和中深烘焙类型的咖啡的人，这款咖啡并不适合我的喜好。",
                "phrases": ["怪异的很突兀的酸苦感", "偏苦"],
            },
        ],
    },
    {
        "document_key": "document.zh_hans.guchengf_2025_003",
        "filename": "03_review-ucc-shokunin-no-coffee-sugar-free-black-900ml.html",
        "title": "饮料评测：UCC 职人咖啡无糖黑标 900ml",
        "date": "2025-02-13",
        "url": "https://guchengf.me/blog/review-ucc-shokunin-no-coffee-sugar-free-black-900ml/",
        "paragraphs": [
            {
                "text": "UCC 职人咖啡无糖黑标是我心目中最好的即饮黑咖啡。我认为这款咖啡可能是即饮黑咖啡的极致，醇厚的日式烹煮黑咖啡口感，除了日式咖啡常见的烘焙、微苦口感，还有轻微的果酸味，让咖啡的整体口感更佳完整、饱满，可以说是很完美。",
                "phrases": [
                    "醇厚的日式烹煮黑咖啡口感",
                    "烘焙、微苦口感",
                    "轻微的果酸味",
                    "整体口感更佳完整、饱满",
                ],
            }
        ],
    },
    {
        "document_key": "document.zh_hans.guchengf_2025_004",
        "filename": "04_review-kirin-fire-one-day-black-coffee-600-ml.html",
        "title": "饮料评测：麒麟直火一日黑咖啡 600ml",
        "date": "2025-03-05",
        "url": "https://guchengf.me/blog/review-kirin-fire-one-day-black-coffee-600-ml/",
        "paragraphs": [
            {
                "text": "麒麟品牌下的直火系列咖啡，比较常见的应该是奶咖那一款。这款黑咖啡相对少见。名字带“直火”，毫无疑问又是以“烘焙口感”为特色的。",
                "phrases": ["以“烘焙口感”为特色"],
            },
            {
                "text": "这款咖啡喝起来几乎没有酸感，只有焦苦味，然后“烘焙”的味道也比较重，但是看到配料表的食用香料，我就知道又是科技的味道。抛开香料不谈，如果喜欢日式咖啡味道的，应该会比价喜欢这款咖啡，确实很还原日式咖啡那种烘焙咖啡豆的味道。",
                "phrases": [
                    "几乎没有酸感",
                    "只有焦苦味",
                    "“烘焙”的味道也比较重",
                    "科技的味道",
                    "日式咖啡那种烘焙咖啡豆的味道",
                ],
            },
            {
                "text": "除此之外，并没有太出彩的地方，烘焙的味道比较突兀，不厚重，很快就消散了，反倒是焦苦味会持续很久，喝完之后嘴巴里一直都是苦的。",
                "phrases": [
                    "烘焙的味道比较突兀，不厚重，很快就消散了",
                    "焦苦味会持续很久",
                    "喝完之后嘴巴里一直都是苦的",
                ],
            },
        ],
    },
]


class ExtractionError(RuntimeError):
    """Raised when an immutable input or reviewed boundary changes."""


class SnapshotParser(HTMLParser):
    """Collect only metadata and decoded paragraphs from a source snapshot."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.language = ""
        self.title_parts: list[str] = []
        self.in_title = False
        self.in_main = False
        self.current_paragraph: dict[str, Any] | None = None
        self.paragraphs: list[dict[str, Any]] = []
        self.canonical_urls: list[str] = []
        self.license_urls: list[str] = []
        self.author_urls: list[str] = []
        self.datetimes: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key: value or "" for key, value in attrs}
        relation = set(attributes.get("rel", "").split())
        if tag == "html":
            self.language = attributes.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "link":
            if "canonical" in relation:
                self.canonical_urls.append(attributes.get("href", ""))
            if "license" in relation:
                self.license_urls.append(attributes.get("href", ""))
            if "author" in relation:
                self.author_urls.append(attributes.get("href", ""))
        elif tag == "time" and attributes.get("datetime"):
            self.datetimes.append(attributes["datetime"])
        elif tag == "main":
            if self.in_main:
                raise ExtractionError("nested main element is not allowed")
            self.in_main = True
        elif tag == "p" and self.in_main:
            if self.current_paragraph is not None:
                raise ExtractionError("nested paragraph is not allowed")
            self.current_paragraph = {
                "line": self.getpos()[0],
                "parts": [],
                "paragraph_index": len(self.paragraphs) + 1,
            }

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.current_paragraph is not None:
            self.current_paragraph["parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "p" and self.current_paragraph is not None:
            text = collapse_source_text(
                "".join(self.current_paragraph.pop("parts"))
            )
            self.current_paragraph["text"] = text
            self.paragraphs.append(self.current_paragraph)
            self.current_paragraph = None
        elif tag == "main":
            if self.current_paragraph is not None:
                raise ExtractionError("main closed inside paragraph")
            self.in_main = False

    @property
    def title(self) -> str:
        return collapse_source_text("".join(self.title_parts))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ExtractionError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def collapse_source_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def normalize_expression(value: str) -> str:
    return WHITESPACE_RE.sub(" ", unicodedata.normalize("NFKC", value)).strip()


def relative_raw_path(filename: str) -> str:
    return (RAW_RELATIVE / filename).as_posix()


def line_containing(text: str, needle: str) -> int:
    matches = [
        index
        for index, line in enumerate(text.splitlines(), start=1)
        if needle in line
    ]
    require(len(matches) == 1, f"expected one line containing {needle!r}")
    return matches[0]


def validate_raw_inventory() -> dict[str, Any]:
    require(RAW_DIR.is_dir(), f"raw snapshot directory is missing: {RAW_DIR}")
    actual_files = {path.name for path in RAW_DIR.iterdir() if path.is_file()}
    require(
        actual_files == EXPECTED_RAW_FILENAMES,
        "raw snapshot file inventory changed: "
        f"missing={sorted(EXPECTED_RAW_FILENAMES - actual_files)}, "
        f"extra={sorted(actual_files - EXPECTED_RAW_FILENAMES)}",
    )
    require(
        sha256_file(MANIFEST_PATH) == EXPECTED_MANIFEST_SHA256,
        "acquisition manifest hash changed",
    )

    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    require(manifest.get("candidate_key") == CANDIDATE_KEY, "candidate key changed")
    require(manifest.get("source_version") == SOURCE_VERSION, "source version changed")
    require(
        manifest.get("acquisition_state") == "ACQUIRED_BYTES_HASHED_NOT_IMPORTED",
        "raw acquisition/import boundary changed",
    )
    register_row = manifest.get("source_candidate_register_row", {})
    require(register_row.get("authors_or_owner") == SOURCE_OWNER, "owner changed")
    require(
        register_row.get("license_or_terms") == "CC BY 4.0",
        "registered license changed",
    )
    require(
        register_row.get("rights_state") == "CLEARED_WITH_TEXT_BOUNDARY_AUDIT",
        "registered rights state changed",
    )
    require(
        register_row.get("doi_or_stable_url") == REGISTERED_SOURCE_URL,
        "registered source URL changed",
    )

    manifest_files = {
        item["path"]: item["sha256"] for item in manifest.get("files", [])
    }
    require(manifest_files == EXPECTED_FILE_HASHES, "manifest raw hashes changed")
    for filename, expected_hash in EXPECTED_FILE_HASHES.items():
        require(
            sha256_file(RAW_DIR / filename) == expected_hash,
            f"raw file hash changed: {filename}",
        )

    checksum_rows: dict[str, str] = {}
    for line in (RAW_DIR / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split("  ", maxsplit=1)
        checksum_rows[filename] = digest
    expected_checksums = {
        **EXPECTED_FILE_HASHES,
        "ACQUISITION_MANIFEST.json": EXPECTED_MANIFEST_SHA256,
    }
    require(checksum_rows == expected_checksums, "SHA256SUMS contract changed")
    return manifest


def validate_site_license() -> str:
    home_path = RAW_DIR / "00_home.html"
    home_text = home_path.read_text(encoding="utf-8")
    require(HOME_LICENSE_DECLARATION in home_text, "site license declaration changed")
    license_line = line_containing(home_text, "网站内容除单独授权（优先）外")
    require(license_line == 158, "site license locator changed")
    return f"{relative_raw_path('00_home.html')}#L156-L159"


def parse_document(spec: dict[str, Any], site_rights_locator: str) -> list[dict[str, Any]]:
    filename = spec["filename"]
    raw_path = RAW_DIR / filename
    raw_text = raw_path.read_text(encoding="utf-8")
    parser = SnapshotParser()
    parser.feed(raw_text)
    parser.close()

    require(parser.language == "zh-Hans", f"language changed: {filename}")
    require(parser.title == spec["title"], f"title changed: {filename}")
    require(parser.canonical_urls == [spec["url"]], f"canonical URL changed: {filename}")
    require(
        len(parser.datetimes) == 1 and parser.datetimes[0][:10] == spec["date"],
        f"publication date changed: {filename}",
    )
    require(
        parser.author_urls == ["mailto:guchengf@gmail.com"],
        f"author locator changed: {filename}",
    )
    require(
        parser.license_urls == [LICENSE_URL],
        f"page license link changed: {filename}",
    )
    head_license_line = line_containing(
        raw_text, '<link href="https://creativecommons.org/licenses/by/4.0/" rel="license">'
    )
    footer_license_line = line_containing(raw_text, "CC-BY-4.0")
    page_rights_locator = (
        f"{relative_raw_path(filename)}#L{head_license_line};"
        f"{relative_raw_path(filename)}#L{footer_license_line}"
    )

    occurrences: list[dict[str, Any]] = []
    for paragraph_spec in spec["paragraphs"]:
        matching_paragraphs = [
            paragraph
            for paragraph in parser.paragraphs
            if paragraph["text"] == paragraph_spec["text"]
        ]
        require(
            len(matching_paragraphs) == 1,
            f"reviewed author paragraph changed or is ambiguous: {filename}",
        )
        paragraph = matching_paragraphs[0]
        for raw_phrase in paragraph_spec["phrases"]:
            require(
                paragraph["text"].count(raw_phrase) == 1,
                f"reviewed phrase changed or is ambiguous: {filename}: {raw_phrase}",
            )
            start = paragraph["text"].index(raw_phrase)
            end = start + len(raw_phrase)
            normalized_expression = normalize_expression(raw_phrase)
            require(
                HAN_RE.search(normalized_expression) is not None,
                f"reviewed expression contains no Han script: {raw_phrase}",
            )
            raw_file_path = relative_raw_path(filename)
            source_locator = (
                f"{raw_file_path}#L{paragraph['line']}:"
                f"main/p[{paragraph['paragraph_index']}]:chars[{start}:{end}]"
            )
            occurrence_hash = sha256_text(
                "|".join(
                    [
                        spec["document_key"],
                        source_locator,
                        raw_phrase,
                        normalized_expression,
                    ]
                )
            )
            occurrences.append(
                {
                    "occurrence_key": (
                        "language.occurrence.round3j.guchengf.sha256_"
                        + occurrence_hash
                    ),
                    "document_key": spec["document_key"],
                    "document_title": spec["title"],
                    "document_date": spec["date"],
                    "document_url": spec["url"],
                    "raw_file_path": raw_file_path,
                    "raw_file_sha256": EXPECTED_FILE_HASHES[filename],
                    "source_locator": source_locator,
                    "raw_source_excerpt": paragraph["text"],
                    "raw_source_phrase": raw_phrase,
                    "normalized_expression": normalized_expression,
                    "page_rights_locator": page_rights_locator,
                    "site_rights_locator": site_rights_locator,
                    "sort_key": (
                        filename,
                        paragraph["paragraph_index"],
                        start,
                        raw_phrase,
                    ),
                }
            )
    return occurrences


def build_rows(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    site_rights_locator = validate_site_license()
    occurrences: list[dict[str, Any]] = []
    for spec in DOCUMENT_SPECS:
        occurrences.extend(parse_document(spec, site_rights_locator))

    occurrence_identities = {
        (
            item["document_key"],
            item["source_locator"],
            item["normalized_expression"],
        )
        for item in occurrences
    }
    require(
        len(occurrence_identities) == len(occurrences),
        "review specification contains a duplicate occurrence",
    )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for occurrence in occurrences:
        grouped[occurrence["normalized_expression"]].append(occurrence)

    register_row = manifest["source_candidate_register_row"]
    rows: list[dict[str, Any]] = []
    duplicate_occurrence_count = 0
    for normalized_expression in sorted(grouped):
        expression_occurrences = sorted(
            grouped[normalized_expression], key=lambda item: item["sort_key"]
        )
        representative = expression_occurrences[0]
        expression_digest = sha256_text("zh-Hans|" + normalized_expression)
        language_expression_key = (
            "language.expression.zh_hans.sha256_" + expression_digest
        )
        effective_unit_key = "effective.lexical.zh_hans.sha256_" + expression_digest
        training_example_key = (
            "training.example.lexical.guchengf.sha256_"
            + sha256_text(
                "|".join(
                    [SOURCE_FAMILY_KEY, "zh-Hans", normalized_expression]
                )
            )
        )
        if len(expression_occurrences) == 1:
            duplicate_group_key = ""
            duplicate_disposition = "UNIQUE"
        else:
            duplicate_group_key = (
                "duplicate.lexical.exact.sha256_" + expression_digest
            )
            duplicate_disposition = "RETAINED"
            duplicate_occurrence_count += len(expression_occurrences) - 1

        provenance_occurrences = []
        for occurrence in expression_occurrences:
            provenance_occurrences.append(
                {
                    key: occurrence[key]
                    for key in [
                        "occurrence_key",
                        "document_key",
                        "document_title",
                        "document_date",
                        "document_url",
                        "raw_file_path",
                        "raw_file_sha256",
                        "source_locator",
                        "raw_source_excerpt",
                        "raw_source_phrase",
                        "page_rights_locator",
                    ]
                }
            )
        rights_basis_locator = (
            f"{site_rights_locator};{representative['page_rights_locator']}"
        )
        rows.append(
            {
                "training_example_key": training_example_key,
                "effective_unit_key": effective_unit_key,
                "language_expression_key": language_expression_key,
                "language_code": "zh-Hans",
                "source_family_key": SOURCE_FAMILY_KEY,
                "source_key": SOURCE_KEY,
                "source_version": SOURCE_VERSION,
                "snapshot_key": SNAPSHOT_KEY,
                "candidate_key": CANDIDATE_KEY,
                "registered_source_url": REGISTERED_SOURCE_URL,
                "source_owner": SOURCE_OWNER,
                "repository": register_row["repository"],
                "document_key": representative["document_key"],
                "document_title": representative["document_title"],
                "document_date": representative["document_date"],
                "document_url": representative["document_url"],
                "raw_file_path": representative["raw_file_path"],
                "raw_file_sha256": representative["raw_file_sha256"],
                "acquisition_manifest_path": MANIFEST_RELATIVE.as_posix(),
                "acquisition_manifest_sha256": EXPECTED_MANIFEST_SHA256,
                "source_locator": representative["source_locator"],
                "raw_source_excerpt": representative["raw_source_excerpt"],
                "raw_source_phrase": representative["raw_source_phrase"],
                "normalized_expression": normalized_expression,
                "expression_role": "UNRESOLVED",
                "source_authored": "true",
                "machine_translated": "false",
                "project_translation": "false",
                "artificial_variant": "false",
                "review_state": "SOURCE_REVIEWED",
                "label_lifecycle": "RESEARCH_REVIEWED",
                "mapping_disposition": "UNRESOLVED",
                "candidate_target_keys": "[]",
                "gold_label": "false",
                "sampling_eligible": "false",
                "counts_toward_governed_total": "false",
                "admission_state": "DERIVED_CANDIDATE_NOT_IMPORTED",
                "duplicate_group_key": duplicate_group_key,
                "duplicate_disposition": duplicate_disposition,
                "expression_occurrence_count": len(expression_occurrences),
                "expression_document_count": len(
                    {item["document_key"] for item in expression_occurrences}
                ),
                "normalization_rule": "NFKC_WHITESPACE_V1",
                "dedupe_rule": (
                    "UNIQUE_BY_LANGUAGE_AND_NORMALIZED_EXPRESSION_V1;"
                    "REPRESENTATIVE_MIN_SOURCE_ORDER;ALL_OCCURRENCES_IN_PROVENANCE_JSON"
                ),
                "extraction_method": (
                    "CURATED_EXACT_SUBSTRING_FROM_AUTHOR_MAIN_PARAGRAPH_V1"
                ),
                "license_expression": LICENSE_EXPRESSION,
                "license_url": LICENSE_URL,
                "site_license_url": SITE_LICENSE_URL,
                "rights_state": register_row["rights_state"],
                "rights_basis_locator": rights_basis_locator,
                "raw_text_public_export_allowed": "true",
                "derived_expression_public_release_allowed": "true",
                "model_research_use_allowed": "true",
                "privacy_state": "PUBLIC_AUTHORSHIP_ONLY_NO_PARTICIPANT_DATA",
                "provenance_json": canonical_json(
                    {
                        "boundary": (
                            "author main prose only; title, date, rating, image, "
                            "figcaption, metadata, footer and site shell excluded"
                        ),
                        "candidate_target_keys": [],
                        "occurrences": provenance_occurrences,
                        "review_or_rule_key": (
                            "review.round3j.guchengf-main-prose-boundary-v1"
                        ),
                    }
                ),
                "limitation": (
                    "Source-authored sensory wording only; expression role and "
                    "canonical target remain unresolved. This derived candidate "
                    "is not imported, gold-labelled, or training-eligible."
                ),
            }
        )
    require(len(occurrences) == 22, "reviewed occurrence count changed")
    require(len(rows) == 22, "reviewed unique-expression count changed")
    return rows, duplicate_occurrence_count


def write_tsv(rows: list[dict[str, Any]]) -> str:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=FIELDS,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="raise",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return sha256_file(OUTPUT_PATH)


def main() -> int:
    manifest = validate_raw_inventory()
    rows, duplicate_occurrence_count = build_rows(manifest)
    output_sha256 = write_tsv(rows)
    print(f"ROUND3J_GUCHENGF_DOCUMENT_COUNT={len(DOCUMENT_SPECS)}")
    print("ROUND3J_GUCHENGF_SOURCE_FAMILY_COUNT=1")
    print("ROUND3J_GUCHENGF_OCCURRENCE_COUNT=22")
    print(f"ROUND3J_GUCHENGF_UNIQUE_EXPRESSION_COUNT={len(rows)}")
    print(
        "ROUND3J_GUCHENGF_DUPLICATE_OCCURRENCE_COUNT="
        f"{duplicate_occurrence_count}"
    )
    print("ROUND3J_GUCHENGF_MACHINE_TRANSLATED_COUNT=0")
    print("ROUND3J_GUCHENGF_GOLD_LABEL_COUNT=0")
    print("ROUND3J_GUCHENGF_IMPORTED_COUNT=0")
    print(f"ROUND3J_GUCHENGF_DERIVED_TSV={OUTPUT_RELATIVE.as_posix()}")
    print(f"ROUND3J_GUCHENGF_DERIVED_TSV_SHA256={output_sha256}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ExtractionError as error:
        print(f"Round 3J guchengf extraction failed: {error}")
        raise SystemExit(1)
