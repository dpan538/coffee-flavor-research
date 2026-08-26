#!/usr/bin/env python3
"""Generate the source-authored Round 3I Simplified-Chinese corpus artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


EXPECTED_OCCURRENCE_INPUT_SHA256 = (
    "0380b2403589d6e938eed528787977a215aa66bc2137c0d688b427b7db832cbe"
)
EXPECTED_DOCUMENT_INPUT_SHA256 = (
    "2ea841c9a771d4e99e681aba189577a68d1d1007df5ccf5fc70d811364814424"
)
EXPECTED_OCCURRENCES = 253
EXPECTED_EXPRESSIONS = 249
EXPECTED_DOCUMENTS = 8
ALLOWED_ROLES = {
    "SENSORY_ATTRIBUTE",
    "COMPOSITE_REFERENCE",
    "QUALIFIER",
    "TEXTURE",
    "BASIC_TASTE",
    "AROMA_REFERENCE",
    "CONSUMER_METAPHOR",
    "UNRESOLVED",
}
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
WHITESPACE_RE = re.compile(r"\s+")


class GenerationError(RuntimeError):
    """Raised when a reviewed input or generated invariant differs."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalized_zh_hans(value: str) -> str:
    return WHITESPACE_RE.sub(" ", unicodedata.normalize("NFKC", value)).strip()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def source_families() -> list[dict[str, Any]]:
    return [
        {
            "language_source_family_key": "family.zh-hans.zhangdeweb-junru",
            "family_name": "Junru Zhang source-authored coffee tasting notes",
            "canonical_origin_key": "origin.zhangdeweb.junru-zhang",
            "counts_as_independent": "true",
            "mirror_of_language_source_family_key": "",
            "counts_as_new_contemporary_family": "false",
            "counts_as_zh_hans_family": "true",
            "historical_baseline": "false",
            "source_authored": "true",
            "admitted": "true",
            "independence_basis": "Natural-person owner, domain, versioned source repository, and tasting occasions are independent of the other admitted Chinese source.",
            "introduced_round": "3I",
        },
        {
            "language_source_family_key": "family.zh-hans.rinzemoon-lingshiyue",
            "family_name": "Ling Shiyue source-authored cold-brew tasting record",
            "canonical_origin_key": "origin.rinzemoon.lingshiyue",
            "counts_as_independent": "true",
            "mirror_of_language_source_family_key": "",
            "counts_as_new_contemporary_family": "false",
            "counts_as_zh_hans_family": "true",
            "historical_baseline": "false",
            "source_authored": "true",
            "admitted": "true",
            "independence_basis": "Natural-person owner, domain, publishing system, and tasting occasion are independent of the other admitted Chinese source.",
            "introduced_round": "3I",
        },
    ]


def sources() -> list[dict[str, Any]]:
    common = {
        "access_date": "2026-08-26",
        "license_expression": "CC-BY-4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "raw_text_internal_use": "ALLOW",
        "raw_text_public_redistribution": "ALLOW",
        "derived_expression_internal_use": "ALLOW",
        "derived_expression_public_release": "ALLOW",
        "derived_counts_internal_use": "ALLOW",
        "derived_counts_public_release": "ALLOW",
        "model_research_use": "ALLOW",
        "rights_review_complete": "true",
        "privacy_review_complete": "true",
        "source_file_hash_complete": "true",
        "language_codes": canonical_json(["zh-Hans"]),
        "geography": "Source-authored Simplified Chinese web publication",
        "data_type": "Source-authored coffee tasting records",
        "evidence_role": "Observed Simplified-Chinese coffee sensory language",
        "annotation_complete": "true",
        "admitted": "true",
    }
    return [
        {
            **common,
            "language_source_key": "zhangdeweb_junru_zhang_tasting_notes",
            "language_source_family_key": "family.zh-hans.zhangdeweb-junru",
            "title": "Tasting Notes",
            "authors_or_owner": "Junru Zhang",
            "publication_year": "2025",
            "doi_or_stable_url": "https://zhangdeweb.site/2025/03/06/coffee/index.html",
            "repository": "https://github.com/curiosusJR/curiosusJR.github.io",
            "exact_version": "git dc5d02885c599df207f6bbd8c2bbc4009a4303e8; blob f757d6f40372e33b4d7edb96ec4af69fed237f02",
            "rights_basis": "Page footer states all posts unless otherwise noted use CC BY 4.0 and links the Chinese CC BY 4.0 deed; attribution, license link, change indication, and no endorsement apply.",
            "privacy_decision": "Public author identity only; reference-flavor copy, alcohol blocks, images, theme, and UI are excluded.",
            "source_file_manifest": canonical_json(
                [
                    {
                        "path": "2025/03/06/coffee/index.html",
                        "bytes": 45613,
                        "git_commit": "dc5d02885c599df207f6bbd8c2bbc4009a4303e8",
                        "git_blob": "f757d6f40372e33b4d7edb96ec4af69fed237f02",
                        "sha256": "19c8cce17bf4f97f8354d29a79e7e1e860be4ef8422a8ce65d479e91545dc3c4",
                    }
                ]
            ),
            "limitations": "Only the author overview and personal-feeling sections for seven coffee blocks are admitted; source reference-flavor package copy is excluded.",
        },
        {
            **common,
            "language_source_key": "rinzemoon_lengcui_lingshiyue",
            "language_source_family_key": "family.zh-hans.rinzemoon-lingshiyue",
            "title": "首次冷萃记录",
            "authors_or_owner": "泠時月",
            "publication_year": "2026",
            "doi_or_stable_url": "https://rinzemoon.top/article/articles/LengCui",
            "repository": "rinzemoon.top",
            "exact_version": "2026-04-25 page; W/\"66db-zkjFNR3Mqp1vGFeK5G55s3we/4U\"; SHA-256 bfefe1bba5efbeb508e87f4ea4a45d77adf49683e0b0fb606ee208f0e12a2f7f",
            "rights_basis": "Page footer states CC BY 4.0, requests retained attribution, and links the Chinese CC BY 4.0 deed; attribution, license link, change indication, and no endorsement apply.",
            "privacy_decision": "Public author identity only; AI advice, comments, contact/security metadata, avatars, images, friend remark, and non-article shell are excluded.",
            "source_file_manifest": canonical_json(
                [
                    {
                        "url": "https://rinzemoon.top/article/articles/LengCui",
                        "bytes": 26331,
                        "etag": "W/\"66db-zkjFNR3Mqp1vGFeK5G55s3we/4U\"",
                        "sha256": "bfefe1bba5efbeb508e87f4ea4a45d77adf49683e0b0fb606ee208f0e12a2f7f",
                    }
                ]
            ),
            "limitations": "One personal cold-brew record; appearance, AI-advice, milk-preparation context, comments, and site metadata are excluded.",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--occurrence-input", type=Path, required=True)
    parser.add_argument("--document-input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    require(
        sha256_bytes(args.occurrence_input.read_bytes())
        == EXPECTED_OCCURRENCE_INPUT_SHA256,
        "reviewed occurrence input hash changed",
    )
    require(
        sha256_bytes(args.document_input.read_bytes())
        == EXPECTED_DOCUMENT_INPUT_SHA256,
        "reviewed document input hash changed",
    )
    occurrence_input = read_tsv(args.occurrence_input)
    document_input = read_tsv(args.document_input)
    require(len(occurrence_input) == EXPECTED_OCCURRENCES, "occurrence count changed")
    require(len(document_input) == EXPECTED_DOCUMENTS, "document count changed")
    require(
        {row["document_key"] for row in occurrence_input}
        == {row["document_key"] for row in document_input},
        "occurrence/document join changed",
    )
    for row in occurrence_input:
        require(row["expression_role"] in ALLOWED_ROLES, "non-sensory role admitted")
        require(HAN_RE.search(row["normalized_expression"]) is not None, "Han script missing")
        require(
            normalized_zh_hans(row["raw_source_phrase"])
            == row["normalized_expression"],
            "governed NFKC normalization changed",
        )

    source_by_key = {row["language_source_key"]: row for row in sources()}
    family_by_source = {
        key: value["language_source_family_key"] for key, value in source_by_key.items()
    }
    documents: list[dict[str, Any]] = []
    document_key_map: dict[str, str] = {}
    for row in document_input:
        document_key = "document.zh_hans." + row["document_key"].replace("-", "_")
        document_key_map[row["document_key"]] = document_key
        documents.append(
            {
                "language_document_key": document_key,
                "language_source_key": row["source_key"],
                "language_source_family_key": family_by_source[row["source_key"]],
                "source_revision": source_by_key[row["source_key"]]["exact_version"],
                "source_date": row["source_date"],
                "source_row_locator": row["source_row_locator"],
                "language_code": "zh-Hans",
                "document_type": "SOURCE_AUTHORED_BLOG",
                "source_content_sha256": row["source_content_sha256"],
                "content": canonical_json(
                    {
                        "admitted_block_locator": row["source_row_locator"],
                        "raw_source_snapshot_sha256": row["source_content_sha256"],
                        "retention": "reviewed-sensory-expressions-and-provenance",
                    }
                ),
                "raw_text_public_export_allowed": "true",
                "counts_as_new_contemporary_document": "false",
                "counts_as_zh_hans_document": "true",
                "source_authored": "true",
                "machine_translated": "false",
                "artificial_variant": "false",
                "privacy_state": "PUBLIC_AUTHORSHIP_ONLY",
                "public_export_state": "PUBLIC_RAW",
                "frozen_snapshot": "true",
            }
        )

    by_expression: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in occurrence_input:
        by_expression[row["normalized_expression"]].append(row)
    require(len(by_expression) == EXPECTED_EXPRESSIONS, "expression count changed")
    expressions: list[dict[str, Any]] = []
    expression_key_map: dict[str, str] = {}
    for normalized_expression, rows in sorted(by_expression.items()):
        roles = {row["expression_role"] for row in rows}
        require(len(roles) == 1, "one normalized expression has conflicting roles")
        expression_hash = sha256_text("zh-Hans|" + normalized_expression)
        expression_key = f"language.expression.zh_hans.sha256_{expression_hash}"
        expression_key_map[normalized_expression] = expression_key
        expressions.append(
            {
                "language_expression_key": expression_key,
                "language_code": "zh-Hans",
                "representative_source_phrase": rows[0]["raw_source_phrase"],
                "normalized_expression": normalized_expression,
                "expression_role": next(iter(roles)),
                "source_authored": "true",
                "machine_translated": "false",
                "artificial_variant": "false",
                "review_state": "SOURCE_REVIEWED",
                "counts_toward_governed_total": "true",
                "counts_as_zh_hans_sensory_expression": "true",
                "public_export_allowed": "true",
                "limitation": "Observed source-authored Simplified-Chinese sensory expression; no forced canonical mapping or translation equivalence.",
            }
        )

    occurrences: list[dict[str, Any]] = []
    identity_counts: Counter[tuple[str, str, str, str]] = Counter()
    for row in occurrence_input:
        identity = (
            row["document_key"],
            row["normalized_expression"],
            row["source_locator"],
            row["raw_source_phrase"],
        )
        identity_counts[identity] += 1
        ordinal = identity_counts[identity]
        occurrence_hash = sha256_text("|".join(identity + (str(ordinal),)))
        occurrences.append(
            {
                "language_occurrence_key": f"language.occurrence.zh_hans.sha256_{occurrence_hash}",
                "language_document_key": document_key_map[row["document_key"]],
                "language_expression_key": expression_key_map[row["normalized_expression"]],
                "raw_source_phrase": row["raw_source_phrase"],
                "source_locator": f"{row['source_locator']}#sensory-occurrence-{ordinal:03d}-{occurrence_hash[:12]}",
                "observed_value": canonical_json(
                    {
                        "admission": "source-reviewed-observed-zh-hans",
                        "normalization": "NFKC-whitespace-v1",
                    }
                ),
            }
        )

    output_dir = args.output_dir.resolve()
    repo_root = Path(__file__).resolve().parents[2]
    require(output_dir.is_relative_to(repo_root), "output must be inside repository")
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = [
        ("language_source_families.tsv", source_families()),
        ("language_sources.tsv", list(source_by_key.values())),
        ("language_documents.tsv", documents),
        ("language_expressions.tsv", expressions),
        ("language_occurrences.tsv", occurrences),
    ]
    file_hashes: dict[str, str] = {}
    for filename, rows in generated:
        path = output_dir / filename
        write_tsv(path, rows, list(rows[0]))
        file_hashes[filename] = sha256_bytes(path.read_bytes())

    result = {
        "batch_key": "round3i.batch3.zh-hans-language-closure",
        "targeted_gap": "SIMPLIFIED_CHINESE_LANGUAGE_FAMILY_AND_DEPTH_GATES",
        "named_sources_reviewed": 2,
        "sources_admitted": 2,
        "source_families_added": 2,
        "rows_added": len(occurrences),
        "documents_added": len(documents),
        "unique_expressions_added": len(expressions),
        "zh_hans_expressions_added": len(expressions),
        "coverage_cells_added": 0,
        "relationship_support_added": 0,
        "rights_blocked_count": 0,
        "access_blocked_count": 0,
        "marginal_coverage_gain": "HIGH",
        "readiness_state_after": "ALL_MANDATORY_LANGUAGE_GATES_PASS",
        "reviewed_occurrence_input_sha256": EXPECTED_OCCURRENCE_INPUT_SHA256,
        "reviewed_document_input_sha256": EXPECTED_DOCUMENT_INPUT_SHA256,
        "role_counts": dict(sorted(Counter(row["expression_role"] for row in occurrence_input).items())),
        "file_hashes": file_hashes,
    }
    result_path = output_dir / "batch_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        canonical_json(
            {
                "status": "ZH_HANS_REPOSITORY_ARTIFACTS_EMITTED",
                "batch_result_sha256": sha256_bytes(result_path.read_bytes()),
                **result,
            }
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as error:
        print(f"Round 3I zh-Hans generation failed: {error}")
        raise SystemExit(1)
