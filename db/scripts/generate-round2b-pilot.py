#!/usr/bin/env python3
"""Generate the rights-bounded Firstbloom Round 2B pilot and SQL seed.

This generator is deliberately offline.  It accepts an explicit local source
checkout, verifies its pinned Git commit and every input file hash, and emits
only source-controlled derived data.  It never emits complete tasting-note
strings, roaster descriptions, or consumer reviews.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Iterator, Sequence
from urllib.parse import urlparse


PINNED_SOURCE_SHA = "a6cb0026d1af9642724793c799bbc48dc189ba35"
SOURCE_BASELINE_SHA = "2d864d56496c587cff5b6774e0ea41be8b416e6c"
CORPUS_VERSION = "firstbloom-a6cb002-pilot-v1"
CORPUS_KEY = "corpus.firstbloom_a6cb002_pilot_v1"
SNAPSHOT_KEY = "corpus_snapshot.firstbloom_a6cb002_pilot_v1"
PIPELINE_KEY = "normalization.en_v1"
GENERATOR_VERSION = "round2b-pilot-generator-v2-dual-review"
CHECKED_AT = "2026-08-24"
CAPTURED_AT = "2026-08-24T00:00:00+00:00"
MAX_BATCH = 16
MAX_STORED_PHRASE_CHARACTERS = 80
BOOTSTRAP_REPLICATES = 100
BOOTSTRAP_MIN_DOCUMENT_FREQUENCY = 5
BOOTSTRAP_NEIGHBOUR_K = 5

EXPECTED_ELIGIBLE_RELEASES = 4498
EXPECTED_PUBLISHERS = 215
EXPECTED_DOCUMENTS = 2474
EXPECTED_PRODUCTS = 2383
EXPECTED_RAW_OBSERVATIONS = 6818
EXPECTED_LONG_OBSERVATIONS = 85
EXPECTED_COMPLETE_FIELD_ORIGIN_OCCURRENCES = 311
EXPECTED_SHORT_COMPLETE_FIELDS = 2257
EXPECTED_COMPLETE_FIELD_SURFACE_OCCURRENCES = 502
EXPECTED_COMPLETE_FIELD_UNIQUE_HASHES = 2209
EXPECTED_COMPLETE_FIELD_PARSED_SURFACE_HASHES = 306
EXPECTED_REVIEW_CANDIDATE_UNIQUE_HASHES = 2766
EXPECTED_PRIVATE_REVIEW_CANDIDATE_SHA256 = (
    "6f0af6acfeab8f758ca79e1540d810d57955ab67b81736525db3d8a2b8a3b6a9"
)
SPOT_AUDIT_POLICY_VERSION = "expression-admission-spot-audit-v2"
SPOT_AUDIT_SAMPLING_SALT = "spot-audit-v2"
EXPECTED_PRIVATE_SPOT_AUDIT_ROWS = 271
EXPECTED_PRIVATE_SPOT_AUDIT_ADMITTED_ROWS = 130
EXPECTED_PRIVATE_SPOT_AUDIT_REJECTED_ROWS = 141
EXPECTED_PRIVATE_SPOT_AUDIT_SHA256 = (
    "22094d38c7ac8fe6572953f77edb9ab371be4ec63109bbd87d0f3bd519e217fe"
)
SPOT_AUDIT_REMEDIATED_HASHES = (
    "de03643627d17f2d30664c492279306731a3e5987bb4047a5041470ef2f9661b",
    "80a76bd18b895238c07bb054ebc2e496286768c9edb6504b17e0d68f574a982a",
)
INITIAL_SPOT_AUDIT_PACKET_SHA256 = (
    "860584dc863148211815c6973e87b95dc13e962e788801cc50d39045e358d58f"
)
INITIAL_SPOT_AUDIT_LEDGER_SHA256 = (
    "dc306076ff2d97a25b9f2f8e9c5a503b53808ce74d06a71655dcc3923f0d0c43"
)
FINAL_SPOT_AUDIT_LEDGER_SHA256 = (
    "d3d3945291c9217c1078ef3fb96721c6e18fd147d7a46bf966b5a5757da47152"
)
FINAL_SPOT_AUDIT_RETRIEVAL_LEDGER_SHA256 = (
    "84238908cf0059484882f3e086a66d941121a1695860e951e51af14973fd7053"
)
# Frozen only after dual independent admission review, structural-gate v2, and
# two zero-blocker final spot audits.  These are corpus-language counts, never
# objective coffee-flavor measurements.
EXPECTED_REDACTED_OBSERVATIONS = 1254
EXPECTED_RETAINED_OCCURRENCES = 5564
EXPECTED_UNIQUE_RAW_EXPRESSIONS = 2124
EXPECTED_LEXICAL_FORMS = 1716
EXPECTED_NORMALIZED_EXPRESSIONS = 1713
EXPECTED_COOCCURRENCE_PAIRS = 4600
EXPECTED_FINAL_TOP_25_OVERLAP = 25
EXPECTED_FINAL_TOP_100_OVERLAP = 98
EXPECTED_BOOTSTRAP_PLATEAU_VALUE = 3 / 7
EXPECTED_DUPLICATE_REVIEWS = 129

MANIFEST_RELATIVE_PATH = Path("db/data/round2b/firstbloom_source_manifest.json")
RIGHTS_RELATIVE_PATH = Path("db/data/round2b/source_rights.tsv")
ADMISSION_REVIEW_RELATIVE_PATH = Path(
    "db/data/round2b/expression_admission_review.tsv"
)
ADMISSION_REVIEW_METADATA_RELATIVE_PATH = Path(
    "db/data/round2b/expression_admission_review.json"
)
SQL_RELATIVE_PATH = Path("db/015_round2b_pilot_seed.sql")
DATA_RELATIVE_DIR = Path("db/data/round2b")

PUBLISHER_TSV = "pilot_publishers.tsv"
PRODUCT_TSV = "pilot_products.tsv"
INVENTORY_TSV = "pilot_inventory.tsv"
OBSERVATION_TSV = "pilot_observations.tsv"
EXPRESSION_TSV = "pilot_expressions.tsv"
STATISTIC_TSV = "pilot_expression_statistics.tsv"
COOCCURRENCE_TSV = "pilot_cooccurrence.tsv"
DUPLICATE_TSV = "pilot_duplicate_reviews.tsv"
DIAGNOSTIC_JSON = "pilot_diagnostics.json"
RECEIPT_JSON = "generation_receipt.json"

DELIMITER_RE = re.compile(r"[,;|\r\n\u2022\u2023\u25e6\u2043\u2219]+")
WHITESPACE_RE = re.compile(r"\s+")

PUNCTUATION_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u02bc": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
        "\u2026": "...",
        "\u00a0": " ",
        "\u202f": " ",
    }
)

MISSING_LABELS = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "unknown",
    "unspecified",
    "not specified",
}

WHOLE_PHRASE_RULES = (
    (10, "earl gray", "earl grey"),
    (20, "earl gray tea", "earl grey tea"),
    (30, "black currant", "blackcurrant"),
)

REVIEW_POLICY_VERSION = "expression-admission-dual-review-v1"
STRUCTURAL_GATE_VERSION = "structural-prose-gate-v2"
REVIEW_DECISION_CODES = {
    "ENGLISH_TASTING_LANGUAGE",
    "NARRATIVE_OR_NON_DESCRIPTOR",
    "NON_ENGLISH",
    "UNCERTAIN",
}
REVIEW_PASS_EVIDENCE_CLASS = "CODEX_ASSISTED_PROJECT_CURATION"
EXPECTED_REVIEWER_IDS = (
    "codex_admission_reviewer_a_20260824",
    "codex_admission_reviewer_b_20260824",
)
STRUCTURAL_GATE_CODES = {
    "PASS_CONCISE_FRAGMENT",
    "REJECT_CONTROL_OR_FORMAT_CHARACTER",
    "REJECT_SENTENCE_PUNCTUATION",
    "REJECT_PERSONAL_PRONOUN_OR_FINITE_AUXILIARY",
    "REJECT_REPEATED_CONNECTIVE",
    "REJECT_GT_8_WORD_TOKENS",
}
SENTENCE_PUNCTUATION_RE = re.compile(r"[.!?]")
WORD_TOKEN_RE = re.compile(r"\b[\w'\u2019/-]+\b", re.UNICODE)
PERSONAL_OR_FINITE_AUXILIARY_RE = re.compile(
    r"\b(?:"
    r"i|me|my|mine|myself|we|us|our|ours|ourselves|"
    r"you|your|yours|yourself|yourselves|"
    r"he|him|his|himself|she|her|hers|herself|"
    r"they|them|their|theirs|themselves|it|its|itself|"
    r"am|is|are|was|were|be|been|being|have|has|had|"
    r"do|does|did|can|could|will|would|shall|should|"
    r"may|might|must|"
    r"isn['\u2019]t|aren['\u2019]t|wasn['\u2019]t|weren['\u2019]t|"
    r"haven['\u2019]t|hasn['\u2019]t|hadn['\u2019]t|"
    r"don['\u2019]t|doesn['\u2019]t|didn['\u2019]t|"
    r"can['\u2019]t|couldn['\u2019]t|won['\u2019]t|"
    r"wouldn['\u2019]t|shouldn['\u2019]t|mustn['\u2019]t|"
    r"it['\u2019]s|that['\u2019]s|there['\u2019]s|here['\u2019]s"
    r")\b",
    re.IGNORECASE,
)
REPEATED_CONNECTIVE_RE = re.compile(
    r"\b(?:and|or|with|plus|then|but)\s+"
    r"(?:and|or|with|plus|then|but)\b",
    re.IGNORECASE,
)


class GenerationError(RuntimeError):
    """Raised when a pinned input or deterministic invariant is violated."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationError(message)


def repository_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def load_manifest(repo_root: Path) -> dict[str, Any]:
    path = repo_root / MANIFEST_RELATIVE_PATH
    with path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    require(
        manifest.get("pinned_git_sha") == PINNED_SOURCE_SHA,
        "source manifest pinned Git SHA does not match generator contract",
    )
    require(
        manifest.get("license") == "CC-BY-4.0",
        "source manifest must declare CC-BY-4.0",
    )
    require(
        manifest.get("rights_boundary") == "ALLOW_DERIVED_TERMS",
        "source manifest rights boundary changed",
    )
    require(
        manifest.get("expression_admission_policy")
        == REVIEW_POLICY_VERSION,
        "source manifest expression-admission policy changed",
    )
    return manifest


def verify_source_checkout(source_dir: Path, manifest: dict[str, Any]) -> None:
    require(source_dir.is_dir(), f"source directory does not exist: {source_dir}")
    result = subprocess.run(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    actual_sha = result.stdout.strip()
    require(
        actual_sha == PINNED_SOURCE_SHA,
        f"Firstbloom checkout is {actual_sha}, expected {PINNED_SOURCE_SHA}",
    )

    expected_files = manifest.get("input_files")
    require(isinstance(expected_files, dict), "manifest input_files must be an object")
    for filename, expected_sha in sorted(expected_files.items()):
        path = source_dir / filename
        require(path.is_file(), f"missing pinned source input: {filename}")
        actual_file_sha = sha256_bytes(path.read_bytes())
        require(
            actual_file_sha == expected_sha,
            f"SHA-256 mismatch for {filename}: {actual_file_sha}",
        )

    readme = (source_dir / "README.md").read_text(encoding="utf-8")
    license_text = (source_dir / "LISCENSE").read_text(encoding="utf-8")
    require(
        "CC BY 4.0" in readme
        and "creativecommons.org/licenses/by/4.0" in readme,
        "Firstbloom README no longer contains the pinned CC BY 4.0 grant",
    )
    require(
        "Attribution 4.0 International" in license_text
        and "Creative Commons Attribution 4.0 International Public License"
        in license_text,
        "Firstbloom license text does not match the expected CC BY 4.0 license",
    )


def read_csv(source_dir: Path, filename: str) -> list[dict[str, str]]:
    with (source_dir / filename).open(
        encoding="utf-8-sig", newline=""
    ) as handle:
        return list(csv.DictReader(handle))


def indexed_rows(
    rows: Iterable[dict[str, str]], key: str, label: str
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        require(bool(value), f"{label} has an empty {key}")
        require(value not in result, f"{label} has duplicate {key}={value}")
        result[value] = row
    return result


def clean_label(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = WHITESPACE_RE.sub(" ", value).strip()
    if cleaned.casefold() in MISSING_LABELS:
        return None
    return cleaned or None


def stable_unique(values: Iterable[str | None]) -> list[str]:
    present = {value for value in values if value is not None}
    return sorted(present, key=lambda value: (value.casefold(), value))


def kb_normalize(value: str) -> str:
    """Mirror the Round 1 lower/collapse/trim lexical uniqueness contract."""
    return WHITESPACE_RE.sub(" ", value.lower()).strip()


def normalize_v1(value: str) -> str:
    """Round 2B deterministic Unicode, case, punctuation and whitespace v1."""
    normalized = unicodedata.normalize("NFC", value)
    normalized = normalized.translate(PUNCTUATION_TRANSLATION).lower()
    normalized = WHITESPACE_RE.sub(" ", normalized).strip()
    for _rule_order, source_phrase, replacement_phrase in WHOLE_PHRASE_RULES:
        if normalized == source_phrase:
            normalized = replacement_phrase
    return normalized


def normalization_rules() -> dict[str, Any]:
    return {
        "version": "1",
        "unicode_normalization": "NFC",
        "case_normalization": "Unicode lower-case under the recorded PostgreSQL cluster collation",
        "whitespace": "collapse Unicode whitespace and trim",
        "punctuation": {
            "curly_apostrophes": "ASCII apostrophe",
            "curly_quotes": "ASCII double quote",
            "dash_variants": "ASCII hyphen-minus",
            "Unicode_ellipsis": "three ASCII periods",
        },
        "destructive_stemming": False,
        "slash_is_delimiter": False,
        "word_and_is_delimiter": False,
        "phrase_delimiters": [
            "comma",
            "semicolon",
            "vertical_bar",
            "CR",
            "LF",
            "Unicode_bullet_characters",
        ],
        "ordered_exact_whole_phrase_rules": [
            {
                "order": rule_order,
                "source": source_phrase,
                "replacement": replacement_phrase,
            }
            for rule_order, source_phrase, replacement_phrase in WHOLE_PHRASE_RULES
        ],
        "stored_phrase_max_unicode_characters": MAX_STORED_PHRASE_CHARACTERS,
        "expression_admission": {
            "policy_version": REVIEW_POLICY_VERSION,
            "structural_gate_version": STRUCTURAL_GATE_VERSION,
            "complete_field_surface_policy": (
                "hash_only_when_surface_equals_any_complete_selected_field"
            ),
            "review_pass_count": 2,
            "admit_consensus": "ENGLISH_TASTING_LANGUAGE",
            "disagreement_policy": "hash_only",
            "language_tag_basis": (
                "dual Codex-assisted project curation consensus; not human "
                "review or automated language detection"
            ),
        },
    }


def spot_audit_receipts() -> list[dict[str, Any]]:
    common_reviewer = {
        "reviewer_id": "codex_admission_spot_auditor_schema_20260824",
        "evidence_class": REVIEW_PASS_EVIDENCE_CLASS,
        "human_review": False,
        "automated_language_detection": False,
    }
    receipts = [
        {
            "audit_policy_version": "expression-admission-spot-audit-v1",
            "structural_gate_version": "structural-prose-gate-v1",
            "sampling_salt": "spot-audit-v1",
            "sampling_salt_sha256": sha256_text("spot-audit-v1"),
            "private_packet_sha256": INITIAL_SPOT_AUDIT_PACKET_SHA256,
            "private_ledger_sha256": INITIAL_SPOT_AUDIT_LEDGER_SHA256,
            "sampled_row_count": 268,
            "sampled_admitted_count": 130,
            "sampled_rejected_count": 138,
            "decision_counts": {
                "PASS_ACCEPTED": 128,
                "PASS_REJECTED_CONSERVATIVE": 106,
                "WARN_REJECTED_FALSE_NEGATIVE": 32,
                "FAIL_ACCEPTED_NARRATIVE": 0,
                "FAIL_ACCEPTED_NON_ENGLISH": 0,
                "FAIL_ACCEPTED_UNCLEAR_SCOPE": 0,
                "FAIL_ACCEPTED_STRUCTURAL_LEAK": 2,
            },
            "accepted_blocker_count": 2,
            "changed_hashes": list(SPOT_AUDIT_REMEDIATED_HASHES),
            "result": "FAIL_REMEDIATED_BY_STRUCTURAL_GATE_V2",
            **common_reviewer,
        },
        {
            "audit_policy_version": SPOT_AUDIT_POLICY_VERSION,
            "structural_gate_version": STRUCTURAL_GATE_VERSION,
            "sampling_salt": SPOT_AUDIT_SAMPLING_SALT,
            "sampling_salt_sha256": sha256_text(
                SPOT_AUDIT_SAMPLING_SALT
            ),
            "private_packet_sha256": EXPECTED_PRIVATE_SPOT_AUDIT_SHA256,
            "private_ledger_sha256": FINAL_SPOT_AUDIT_LEDGER_SHA256,
            "sampled_row_count": EXPECTED_PRIVATE_SPOT_AUDIT_ROWS,
            "sampled_admitted_count": (
                EXPECTED_PRIVATE_SPOT_AUDIT_ADMITTED_ROWS
            ),
            "sampled_rejected_count": (
                EXPECTED_PRIVATE_SPOT_AUDIT_REJECTED_ROWS
            ),
            "decision_counts": {
                "PASS_ACCEPTED": 130,
                "PASS_REJECTED_CONSERVATIVE": 114,
                "WARN_REJECTED_FALSE_NEGATIVE": 27,
                "FAIL_ACCEPTED_NARRATIVE": 0,
                "FAIL_ACCEPTED_NON_ENGLISH": 0,
                "FAIL_ACCEPTED_UNCLEAR_SCOPE": 0,
                "FAIL_ACCEPTED_STRUCTURAL_LEAK": 0,
            },
            "accepted_blocker_count": 0,
            "changed_hashes": [],
            "remediated_hashes_verified": list(
                SPOT_AUDIT_REMEDIATED_HASHES
            ),
            "result": "PASS",
            **common_reviewer,
        },
    ]
    retrieval_receipt = {
        **receipts[-1],
        "private_ledger_sha256": (
            FINAL_SPOT_AUDIT_RETRIEVAL_LEDGER_SHA256
        ),
        "decision_counts": {
            "PASS_ACCEPTED": 130,
            "PASS_REJECTED_CONSERVATIVE": 103,
            "WARN_REJECTED_FALSE_NEGATIVE": 38,
            "FAIL_ACCEPTED_NARRATIVE": 0,
            "FAIL_ACCEPTED_NON_ENGLISH": 0,
            "FAIL_ACCEPTED_UNCLEAR_SCOPE": 0,
            "FAIL_ACCEPTED_STRUCTURAL_LEAK": 0,
        },
        "reviewer_id": (
            "codex_admission_spot_auditor_retrieval_20260824"
        ),
    }
    receipts.append(retrieval_receipt)
    return receipts


def selection_digest(release_id: str) -> str:
    return sha256_text(f"{CORPUS_VERSION}:{release_id}")


def select_releases(
    releases: Sequence[dict[str, str]],
    roasters: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, str]]]]:
    by_roaster: dict[str, list[dict[str, str]]] = defaultdict(list)
    for release in releases:
        note = release.get("roaster_tasting_notes_string", "")
        roaster_id = release.get("roaster_id", "")
        if roaster_id in roasters and note.strip():
            by_roaster[roaster_id].append(release)

    eligible_count = sum(len(values) for values in by_roaster.values())
    require(
        eligible_count == EXPECTED_ELIGIBLE_RELEASES,
        f"eligible release count is {eligible_count}, expected {EXPECTED_ELIGIBLE_RELEASES}",
    )
    require(
        len(by_roaster) == EXPECTED_PUBLISHERS,
        f"eligible publisher count is {len(by_roaster)}, expected {EXPECTED_PUBLISHERS}",
    )

    for values in by_roaster.values():
        values.sort(
            key=lambda row: (
                selection_digest(row["product_release_id"]),
                int(row["product_release_id"]),
            )
        )

    selected: list[dict[str, Any]] = []
    for batch_number in range(1, MAX_BATCH + 1):
        for roaster_id in sorted(by_roaster, key=int):
            releases_for_roaster = by_roaster[roaster_id]
            if len(releases_for_roaster) < batch_number:
                continue
            release = dict(releases_for_roaster[batch_number - 1])
            release["batch_number"] = batch_number
            release["selection_sha256"] = selection_digest(
                release["product_release_id"]
            )
            selected.append(release)

    require(
        len(selected) == EXPECTED_DOCUMENTS,
        f"selected document count is {len(selected)}, expected {EXPECTED_DOCUMENTS}",
    )
    return selected, by_roaster


def build_product_metadata(
    selected: Sequence[dict[str, Any]], source_dir: Path
) -> dict[str, dict[str, Any]]:
    selected_ids = {row["product_release_id"] for row in selected}
    relation_rows = [
        row
        for row in read_csv(
            source_dir, "product_release_varieties_202312201400.csv"
        )
        if row["product_release_id"] in selected_ids
    ]
    by_release: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in relation_rows:
        by_release[row["product_release_id"]].append(row)

    cleaning = indexed_rows(
        read_csv(source_dir, "cleaning_processes_202312201327.csv"),
        "id",
        "cleaning processes",
    )
    drying = indexed_rows(
        read_csv(source_dir, "drying_processes_202312201327.csv"),
        "id",
        "drying processes",
    )
    varieties = indexed_rows(
        read_csv(source_dir, "varieties_202312201327.csv"),
        "id",
        "varieties",
    )
    coffee_regions = indexed_rows(
        read_csv(source_dir, "coffee_regions_202312201327.csv"),
        "id",
        "coffee regions",
    )
    countries = indexed_rows(
        read_csv(source_dir, "countries_202312201327.csv"),
        "id",
        "countries",
    )
    regions = indexed_rows(
        read_csv(source_dir, "regions_202312201327.csv"),
        "id",
        "regions",
    )
    producers = indexed_rows(
        read_csv(source_dir, "producers_202312201327.csv"),
        "id",
        "producers",
    )
    farms = indexed_rows(
        read_csv(source_dir, "farms_202312201327.csv"),
        "id",
        "farms",
    )

    def lookup_label(
        table: dict[str, dict[str, str]], row_id: str, *fields: str
    ) -> str | None:
        if not row_id:
            return None
        row = table.get(row_id)
        require(row is not None, f"missing lookup row {row_id} in metadata table")
        for field in fields:
            label = clean_label(row.get(field))
            if label is not None:
                return label
        return None

    output: dict[str, dict[str, Any]] = {}
    for release in selected:
        release_id = release["product_release_id"]
        relations = sorted(by_release.get(release_id, []), key=lambda row: int(row["id"]))

        country_codes: list[str | None] = []
        country_names: list[str | None] = []
        region_names: list[str | None] = []
        producer_names: list[str | None] = []
        farm_names: list[str | None] = []
        variety_names: list[str | None] = []
        cleaning_names: list[str | None] = []
        drying_names: list[str | None] = []

        for relation in relations:
            coffee_region_id = relation.get("coffee_region_id", "")
            if coffee_region_id:
                coffee_region = coffee_regions.get(coffee_region_id)
                require(
                    coffee_region is not None,
                    f"release {release_id} references missing coffee region {coffee_region_id}",
                )
                country_id = coffee_region.get("country_id", "")
                if country_id:
                    country = countries.get(country_id)
                    require(
                        country is not None,
                        f"coffee region {coffee_region_id} references missing country {country_id}",
                    )
                    country_codes.append(clean_label(country.get("short")))
                    country_names.append(clean_label(country.get("name")))
                region_names.append(
                    lookup_label(
                        regions, coffee_region.get("region_id", ""), "name"
                    )
                )

            producer_names.append(
                lookup_label(producers, relation.get("producer_id", ""), "name")
            )
            farm_names.append(
                lookup_label(farms, relation.get("farm_id", ""), "name")
            )
            variety_names.append(
                lookup_label(
                    varieties, relation.get("variety_id", ""), "label", "name"
                )
            )
            cleaning_names.append(
                lookup_label(
                    cleaning, relation.get("cleaning_process_id", ""), "label"
                )
            )
            drying_names.append(
                lookup_label(
                    drying, relation.get("drying_process_id", ""), "label"
                )
            )

        cleaned_country_codes = stable_unique(country_codes)
        output[release_id] = {
            "coffee_origin_country_codes": cleaned_country_codes,
            "coffee_origin_country_names": stable_unique(country_names),
            "coffee_regions": stable_unique(region_names),
            "producer_names": stable_unique(producer_names),
            "farm_names": stable_unique(farm_names),
            "variety_names": stable_unique(variety_names),
            "cleaning_process_names": stable_unique(cleaning_names),
            "drying_process_names": stable_unique(drying_names),
            "process_names": stable_unique(cleaning_names + drying_names),
            "relation_row_count": len(relations),
        }

    require(
        set(output) == selected_ids,
        "product metadata was not built for every selected release",
    )
    return output


def complete_field_surface_hashes(
    selected: Sequence[dict[str, Any]],
) -> set[str]:
    """Return every short complete-field surface hash in the pilot.

    A surface that is a complete tasting-note field anywhere in the selected
    snapshot is never emitted as text, even when another document happens to
    use the same surface as one segment of a longer field.  This global rule is
    deliberately more conservative than redacting only the originating row.
    """
    eligible_complete_fields = [
        release["roaster_tasting_notes_string"].strip()
        for release in selected
        if release["roaster_tasting_notes_string"].strip()
        and len(release["roaster_tasting_notes_string"].strip())
        <= MAX_STORED_PHRASE_CHARACTERS
    ]
    hashes = {sha256_text(value) for value in eligible_complete_fields}
    require(
        len(eligible_complete_fields) == EXPECTED_SHORT_COMPLETE_FIELDS,
        "short complete-field count changed",
    )
    require(
        len(hashes) == EXPECTED_COMPLETE_FIELD_UNIQUE_HASHES,
        "short complete-field unique-hash count changed",
    )
    return hashes


def review_exclusion_reason(consensus_decision_code: str) -> str | None:
    return {
        "ENGLISH_TASTING_LANGUAGE": None,
        "NARRATIVE_OR_NON_DESCRIPTOR": (
            "dual_review_narrative_or_non_descriptor"
        ),
        "NON_ENGLISH": "dual_review_non_english",
        "UNCERTAIN": "dual_review_uncertain",
        "DISAGREEMENT": "dual_review_disagreement",
    }[consensus_decision_code]


def expected_consensus_decision(
    reviewer_one_decision_code: str,
    reviewer_two_decision_code: str,
) -> str:
    if reviewer_one_decision_code == reviewer_two_decision_code:
        return reviewer_one_decision_code
    return "DISAGREEMENT"


def structural_prose_gate_v2(value: str) -> str:
    """Reject sentence-like text before any lexical/statistical admission."""
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        return "REJECT_CONTROL_OR_FORMAT_CHARACTER"
    if SENTENCE_PUNCTUATION_RE.search(value):
        return "REJECT_SENTENCE_PUNCTUATION"
    if PERSONAL_OR_FINITE_AUXILIARY_RE.search(value):
        return "REJECT_PERSONAL_PRONOUN_OR_FINITE_AUXILIARY"
    if REPEATED_CONNECTIVE_RE.search(value):
        return "REJECT_REPEATED_CONNECTIVE"
    if len(WORD_TOKEN_RE.findall(value)) > 8:
        return "REJECT_GT_8_WORD_TOKENS"
    return "PASS_CONCISE_FRAGMENT"


def expected_final_admission_code(
    consensus_decision_code: str,
    structural_gate_code: str,
) -> str:
    if (
        consensus_decision_code == "ENGLISH_TASTING_LANGUAGE"
        and structural_gate_code == "PASS_CONCISE_FRAGMENT"
    ):
        return "ADMIT_ENGLISH_TASTING_LANGUAGE"
    if consensus_decision_code != "ENGLISH_TASTING_LANGUAGE":
        return "HASH_ONLY_REVIEW_CONSENSUS"
    return "HASH_ONLY_STRUCTURAL_PROSE_GATE"


def expected_final_exclusion_reason(
    consensus_decision_code: str,
    structural_gate_code: str,
) -> str | None:
    final_admission = expected_final_admission_code(
        consensus_decision_code, structural_gate_code
    )
    if final_admission == "ADMIT_ENGLISH_TASTING_LANGUAGE":
        return None
    if final_admission == "HASH_ONLY_REVIEW_CONSENSUS":
        return review_exclusion_reason(consensus_decision_code)
    return {
        "REJECT_CONTROL_OR_FORMAT_CHARACTER": (
            "structural_gate_control_or_format_character"
        ),
        "REJECT_SENTENCE_PUNCTUATION": (
            "structural_gate_sentence_punctuation"
        ),
        "REJECT_PERSONAL_PRONOUN_OR_FINITE_AUXILIARY": (
            "structural_gate_personal_pronoun_or_finite_auxiliary"
        ),
        "REJECT_REPEATED_CONNECTIVE": (
            "structural_gate_repeated_connective"
        ),
        "REJECT_GT_8_WORD_TOKENS": "structural_gate_gt_8_word_tokens",
    }[structural_gate_code]


def load_admission_reviews(
    repo_root: Path,
) -> dict[str, dict[str, str]]:
    """Load the text-free, dual-review admission inventory.

    Review decisions are explicit project curation records.  They are not
    human-review evidence, automatic language detection, or semantic mappings
    to canonical concepts.
    """
    path = repo_root / ADMISSION_REVIEW_RELATIVE_PATH
    metadata_path = repo_root / ADMISSION_REVIEW_METADATA_RELATIVE_PATH
    require(path.is_file(), f"missing admission review inventory: {path}")
    require(
        metadata_path.is_file(),
        f"missing admission review metadata: {metadata_path}",
    )

    with path.open(encoding="utf-8", newline="") as handle:
        physical_rows = list(csv.reader(handle, delimiter="\t"))
    require(bool(physical_rows), "admission review inventory is empty")
    expected_columns = [
        "source_surface_sha256",
        "reviewer_one_decision_code",
        "reviewer_two_decision_code",
        "consensus_decision_code",
        "structural_gate_code",
        "final_admission_code",
        "admitted_language_tag_code",
        "exclusion_reason_code",
    ]
    require(
        physical_rows[0] == expected_columns,
        "admission review inventory columns changed",
    )
    for line_number, row in enumerate(physical_rows[1:], start=2):
        require(
            len(row) == len(expected_columns),
            f"admission review line {line_number} has the wrong field count",
        )

    rows: dict[str, dict[str, str]] = {}
    rows_in_order: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            surface_hash = row["source_surface_sha256"]
            require(
                bool(re.fullmatch(r"[0-9a-f]{64}", surface_hash)),
                "admission review contains an invalid SHA-256",
            )
            require(
                surface_hash not in rows,
                "admission review contains a duplicate surface hash",
            )
            decision_one = row["reviewer_one_decision_code"]
            decision_two = row["reviewer_two_decision_code"]
            require(
                decision_one in REVIEW_DECISION_CODES
                and decision_two in REVIEW_DECISION_CODES,
                "admission review contains an unsupported review decision",
            )
            consensus = expected_consensus_decision(
                decision_one, decision_two
            )
            require(
                row["consensus_decision_code"] == consensus,
                "admission review consensus does not match both passes",
            )
            structural_gate = row["structural_gate_code"]
            require(
                structural_gate in STRUCTURAL_GATE_CODES,
                "admission review contains an unsupported structural gate",
            )
            final_admission = expected_final_admission_code(
                consensus, structural_gate
            )
            require(
                row["final_admission_code"] == final_admission,
                "admission review final gate does not match its inputs",
            )
            admitted = final_admission == "ADMIT_ENGLISH_TASTING_LANGUAGE"
            require(
                row["admitted_language_tag_code"] == ("en" if admitted else ""),
                "admission language tag does not match consensus",
            )
            require(
                row["exclusion_reason_code"]
                == (
                    expected_final_exclusion_reason(
                        consensus, structural_gate
                    )
                    or ""
                ),
                "admission exclusion reason does not match final gate",
            )
            rows[surface_hash] = row
            rows_in_order.append(row)

    require(
        len(rows) == EXPECTED_REVIEW_CANDIDATE_UNIQUE_HASHES,
        "admission review candidate count changed",
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    require(
        metadata.get("review_policy_version") == REVIEW_POLICY_VERSION,
        "admission review policy version changed",
    )
    require(
        metadata.get("structural_gate_version")
        == STRUCTURAL_GATE_VERSION,
        "admission review structural-gate version changed",
    )
    require(
        metadata.get("admission_inventory_sha256")
        == sha256_bytes(path.read_bytes()),
        "admission review metadata does not bind the TSV",
    )
    require(
        metadata.get("private_candidate_review_file_sha256")
        == EXPECTED_PRIVATE_REVIEW_CANDIDATE_SHA256,
        "admission review metadata does not bind the private candidate packet",
    )
    require(
        metadata.get("candidate_hash_inventory_sha256")
        == sha256_text(canonical_json(sorted(rows))),
        "admission review metadata does not bind the candidate hash inventory",
    )
    require(
        metadata.get("pinned_firstbloom_sha") == PINNED_SOURCE_SHA,
        "admission review metadata source SHA changed",
    )
    require(
        metadata.get("decision_codes") == sorted(REVIEW_DECISION_CODES),
        "admission review metadata decision codes changed",
    )
    expected_spot_audits = spot_audit_receipts()
    final_spot_audits = [
        audit
        for audit in expected_spot_audits
        if audit["audit_policy_version"] == SPOT_AUDIT_POLICY_VERSION
    ]
    require(
        metadata.get("spot_audits") == expected_spot_audits
        and len(final_spot_audits) == 2
        and all(
            audit["result"] == "PASS"
            and audit["accepted_blocker_count"] == 0
            for audit in final_spot_audits
        ),
        "admission review spot-audit closure changed",
    )
    passes = metadata.get("review_passes")
    require(
        isinstance(passes, list)
        and len(passes) == 2
        and tuple(item.get("reviewer_id") for item in passes)
        == EXPECTED_REVIEWER_IDS,
        "admission review requires two distinct review passes",
    )
    for review_pass in passes:
        require(
            review_pass.get("evidence_class")
            == REVIEW_PASS_EVIDENCE_CLASS
            and review_pass.get("human_review") is False
            and review_pass.get("automated_language_detection") is False,
            "review provenance must remain explicit and conservative",
        )
        require(
            bool(
                re.fullmatch(
                    r"[0-9a-f]{64}",
                    str(review_pass.get("review_pass_sha256", "")),
                )
            ),
            "review-pass provenance SHA-256 is invalid",
        )

    def reconstructed_review_pass_sha256(decision_column: str) -> str:
        output = io.StringIO(newline="")
        writer = csv.writer(
            output,
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writerow(["source_surface_sha256", "review_decision_code"])
        for row in rows_in_order:
            writer.writerow(
                [row["source_surface_sha256"], row[decision_column]]
            )
        return sha256_text(output.getvalue())

    require(
        passes[0]["review_pass_sha256"]
        == reconstructed_review_pass_sha256("reviewer_one_decision_code")
        and passes[1]["review_pass_sha256"]
        == reconstructed_review_pass_sha256("reviewer_two_decision_code"),
        "public review columns do not reconstruct the frozen private ledgers",
    )

    consensus_counts = Counter(
        row["consensus_decision_code"] for row in rows_in_order
    )
    structural_counts = Counter(
        row["structural_gate_code"] for row in rows_in_order
    )
    final_counts = Counter(
        row["final_admission_code"] for row in rows_in_order
    )
    require(
        metadata.get("consensus_counts")
        == dict(sorted(consensus_counts.items()))
        and metadata.get("structural_gate_counts")
        == dict(sorted(structural_counts.items()))
        and metadata.get("final_admission_counts")
        == dict(sorted(final_counts.items())),
        "admission review metadata aggregate counts changed",
    )
    decision_counts_one = Counter(
        row["reviewer_one_decision_code"] for row in rows_in_order
    )
    decision_counts_two = Counter(
        row["reviewer_two_decision_code"] for row in rows_in_order
    )
    agreement_count = sum(
        row["reviewer_one_decision_code"]
        == row["reviewer_two_decision_code"]
        for row in rows_in_order
    )
    decision_pair_counts = Counter(
        (
            row["reviewer_one_decision_code"],
            row["reviewer_two_decision_code"],
        )
        for row in rows_in_order
    )
    review_count = len(rows_in_order)
    observed_agreement = agreement_count / review_count
    chance_expected_agreement = sum(
        (decision_counts_one[decision] / review_count)
        * (decision_counts_two[decision] / review_count)
        for decision in REVIEW_DECISION_CODES
    )
    cohen_kappa = (
        (observed_agreement - chance_expected_agreement)
        / (1 - chance_expected_agreement)
        if chance_expected_agreement < 1
        else None
    )
    agreement = metadata.get("review_agreement")
    require(
        isinstance(agreement, dict)
        and agreement.get("reviewed_hash_count") == review_count
        and agreement.get("agreement_count") == agreement_count
        and agreement.get("disagreement_count")
        == review_count - agreement_count
        and agreement.get("reviewer_one_decision_counts")
        == dict(sorted(decision_counts_one.items()))
        and agreement.get("reviewer_two_decision_counts")
        == dict(sorted(decision_counts_two.items())),
        "admission review agreement metadata changed",
    )
    require(
        isinstance(agreement.get("raw_agreement"), (int, float))
        and math.isclose(
            agreement["raw_agreement"],
            observed_agreement,
            rel_tol=0,
            abs_tol=1e-15,
        )
        and isinstance(
            agreement.get("chance_expected_agreement"), (int, float)
        )
        and math.isclose(
            agreement["chance_expected_agreement"],
            chance_expected_agreement,
            rel_tol=0,
            abs_tol=1e-15,
        )
        and (
            cohen_kappa is None
            and agreement.get("cohen_kappa") is None
            or isinstance(agreement.get("cohen_kappa"), (int, float))
            and math.isclose(
                agreement["cohen_kappa"],
                cohen_kappa,
                rel_tol=0,
                abs_tol=1e-15,
            )
        )
        and agreement.get("decision_pair_counts")
        == {
            f"{left}|{right}": count
            for (left, right), count in sorted(decision_pair_counts.items())
        },
        "admission review agreement metrics changed",
    )
    return rows


def parse_observations(
    selected: Sequence[dict[str, Any]],
    admission_reviews: dict[str, dict[str, str]] | None = None,
    enforce_frozen_counts: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    observations: list[dict[str, Any]] = []
    lexical_forms: dict[str, dict[str, str]] = {}
    complete_surface_hashes = complete_field_surface_hashes(selected)
    complete_field_hash_by_release = {
        release["product_release_id"]: sha256_text(
            release["roaster_tasting_notes_string"].strip()
        )
        for release in selected
    }
    candidate_hashes: set[str] = set()
    long_count = 0
    complete_origin_count = 0
    complete_surface_count = 0
    parsed_complete_surface_hashes: set[str] = set()

    for release in selected:
        release_id = release["product_release_id"]
        raw_note = release["roaster_tasting_notes_string"]
        ordinal = 0
        segment_spans: list[tuple[int, int]] = []
        segment_start = 0
        for delimiter_match in DELIMITER_RE.finditer(raw_note):
            segment_spans.append((segment_start, delimiter_match.start()))
            segment_start = delimiter_match.end()
        segment_spans.append((segment_start, len(raw_note)))

        for raw_segment_start, raw_segment_end in segment_spans:
            segment = raw_note[raw_segment_start:raw_segment_end]
            raw_phrase = segment.strip()
            if not raw_phrase:
                continue
            leading_whitespace_count = len(segment) - len(segment.lstrip())
            character_start = raw_segment_start + leading_whitespace_count
            character_end = character_start + len(raw_phrase)
            require(
                raw_note[character_start:character_end] == raw_phrase,
                f"source offset reconstruction failed for release {release_id}",
            )
            ordinal += 1
            character_count = len(raw_phrase)
            raw_phrase_sha256 = sha256_text(raw_phrase)
            within_length_boundary = (
                character_count <= MAX_STORED_PHRASE_CHARACTERS
            )
            is_complete_field_surface = (
                within_length_boundary
                and raw_phrase_sha256 in complete_surface_hashes
            )
            is_review_candidate = (
                within_length_boundary and not is_complete_field_surface
            )
            if not within_length_boundary:
                long_count += 1
            if (
                within_length_boundary
                and raw_phrase_sha256
                == complete_field_hash_by_release[release_id]
            ):
                complete_origin_count += 1
            if is_complete_field_surface:
                complete_surface_count += 1
                parsed_complete_surface_hashes.add(raw_phrase_sha256)
            if is_review_candidate:
                candidate_hashes.add(raw_phrase_sha256)

            review = (
                admission_reviews.get(raw_phrase_sha256)
                if admission_reviews is not None and is_review_candidate
                else None
            )
            if admission_reviews is not None and is_review_candidate:
                require(
                    review is not None,
                    "admission review omitted an eligible surface hash",
                )
            consensus = (
                review["consensus_decision_code"] if review is not None else None
            )
            if review is not None:
                structural_gate = structural_prose_gate_v2(raw_phrase)
                require(
                    review["structural_gate_code"] == structural_gate,
                    "source phrase does not match its frozen structural gate",
                )
                require(
                    review["final_admission_code"]
                    == expected_final_admission_code(
                        consensus, structural_gate
                    ),
                    "source phrase does not match its final admission code",
                )
            else:
                structural_gate = None
            retained = (
                review is not None
                and review["final_admission_code"]
                == "ADMIT_ENGLISH_TASTING_LANGUAGE"
            )
            if not within_length_boundary:
                exclusion_reason = (
                    "rights_boundary_gt_80_unicode_characters"
                )
            elif is_complete_field_surface:
                exclusion_reason = "rights_complete_field_surface"
            elif review is None:
                exclusion_reason = "pending_dual_review"
            else:
                exclusion_reason = expected_final_exclusion_reason(
                    consensus, structural_gate
                )

            normalized_text = normalize_v1(raw_phrase) if retained else None
            basic_text = kb_normalize(raw_phrase) if retained else None
            require(
                not retained or bool(normalized_text and basic_text),
                f"retained phrase normalized empty for release {release_id}",
            )
            expression_key = None
            if retained:
                expression_key = (
                    "expression.observed.en.sha256_" + sha256_text(basic_text)
                )
                existing = lexical_forms.get(basic_text)
                if existing is None or raw_phrase.encode("utf-8") < existing[
                    "expression_text"
                ].encode("utf-8"):
                    lexical_forms[basic_text] = {
                        "expression_key": expression_key,
                        "expression_text": raw_phrase,
                        "basic_normalized_text": basic_text,
                        "normalized_text": normalized_text,
                    }
                else:
                    require(
                        existing["normalized_text"] == normalized_text,
                        "one Round 1 lexical identity produced multiple v1 normalizations",
                    )

            observations.append(
                {
                    "observation_key": (
                        f"observation.firstbloom.release_{release_id}.{ordinal:03d}"
                    ),
                    "document_key": f"document.firstbloom.release_{release_id}",
                    "release_id": release_id,
                    "ordinal": ordinal,
                    "observation_text": raw_phrase if retained else None,
                    "raw_phrase_sha256": raw_phrase_sha256,
                    "unicode_character_count": character_count,
                    "source_character_start": character_start,
                    "source_character_end": character_end,
                    "retained": retained,
                    "exclusion_reason": exclusion_reason,
                    "basic_normalized_text": basic_text,
                    "normalized_text": normalized_text,
                    "expression_key": expression_key,
                    # This protected value exists only in memory and in the
                    # explicitly requested private review artifact.  No
                    # repository emitter includes this field.
                    "private_review_candidate_text": (
                        raw_phrase if is_review_candidate else None
                    ),
                }
            )

    redacted_count = sum(not row["retained"] for row in observations)
    retained_count = sum(row["retained"] for row in observations)
    raw_unique = len(
        {
            row["observation_text"]
            for row in observations
            if row["observation_text"] is not None
        }
    )
    require(
        len(observations) == EXPECTED_RAW_OBSERVATIONS,
        f"raw observation count is {len(observations)}, expected {EXPECTED_RAW_OBSERVATIONS}",
    )
    require(
        long_count == EXPECTED_LONG_OBSERVATIONS,
        "long-observation count changed",
    )
    require(
        complete_origin_count == EXPECTED_COMPLETE_FIELD_ORIGIN_OCCURRENCES,
        "complete-field origin occurrence count changed",
    )
    require(
        complete_surface_count == EXPECTED_COMPLETE_FIELD_SURFACE_OCCURRENCES,
        "global complete-field surface occurrence count changed",
    )
    require(
        len(parsed_complete_surface_hashes)
        == EXPECTED_COMPLETE_FIELD_PARSED_SURFACE_HASHES,
        "parsed complete-field surface hash count changed",
    )
    require(
        len(candidate_hashes) == EXPECTED_REVIEW_CANDIDATE_UNIQUE_HASHES,
        "review-candidate surface hash count changed",
    )
    if admission_reviews is None:
        require(
            retained_count == 0 and not lexical_forms,
            "pre-review parsing must not admit lexical text",
        )
        return observations, lexical_forms

    require(
        set(admission_reviews) == candidate_hashes,
        "admission review hash inventory differs from eligible candidates",
    )
    if not enforce_frozen_counts:
        return observations, lexical_forms
    final_expected_counts = [
        EXPECTED_REDACTED_OBSERVATIONS,
        EXPECTED_RETAINED_OCCURRENCES,
        EXPECTED_UNIQUE_RAW_EXPRESSIONS,
        EXPECTED_LEXICAL_FORMS,
        EXPECTED_NORMALIZED_EXPRESSIONS,
        EXPECTED_COOCCURRENCE_PAIRS,
    ]
    require(
        all(value is not None for value in final_expected_counts),
        "dual review counts have not been frozen; final seed generation is disabled",
    )
    require(
        redacted_count == EXPECTED_REDACTED_OBSERVATIONS,
        f"redacted count is {redacted_count}, expected {EXPECTED_REDACTED_OBSERVATIONS}",
    )
    require(
        retained_count == EXPECTED_RETAINED_OCCURRENCES,
        f"retained occurrence count is {retained_count}, expected {EXPECTED_RETAINED_OCCURRENCES}",
    )
    require(
        raw_unique == EXPECTED_UNIQUE_RAW_EXPRESSIONS,
        f"unique retained surface count is {raw_unique}, expected {EXPECTED_UNIQUE_RAW_EXPRESSIONS}",
    )
    require(
        len(lexical_forms) == EXPECTED_LEXICAL_FORMS,
        f"lexical-form identity count is {len(lexical_forms)}, expected {EXPECTED_LEXICAL_FORMS}",
    )
    require(
        len({row["normalized_text"] for row in lexical_forms.values()})
        == EXPECTED_NORMALIZED_EXPRESSIONS,
        "v1 normalized-expression identity count changed",
    )
    return observations, lexical_forms


def document_expression_sets(
    selected: Sequence[dict[str, Any]],
    observations: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_release: dict[str, list[str]] = defaultdict(list)
    for observation in observations:
        if observation["retained"]:
            by_release[observation["release_id"]].append(
                observation["normalized_text"]
            )
    documents = [
        {
            "release_id": release["product_release_id"],
            "publisher_id": release["roaster_id"],
            "batch_number": release["batch_number"],
            "expressions": tuple(by_release[release["product_release_id"]]),
        }
        for release in selected
    ]
    return documents


def pair_counts(documents: Sequence[dict[str, Any]]) -> Counter[tuple[str, str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for document in documents:
        expressions = sorted(set(document["expressions"]))
        for index, subject in enumerate(expressions):
            for object_expression in expressions[index + 1 :]:
                counts[(subject, object_expression)] += 1
    return counts


def neighbour_lists(
    counts: Counter[tuple[str, str]], k: int
) -> dict[str, tuple[str, ...]]:
    neighbours: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for (subject, object_expression), count in counts.items():
        neighbours[subject].append((count, object_expression))
        neighbours[object_expression].append((count, subject))
    return {
        expression: tuple(
            neighbour
            for _count, neighbour in sorted(
                values, key=lambda item: (-item[0], item[1])
            )[:k]
        )
        for expression, values in neighbours.items()
    }


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    return 1.0 if not union else len(left_set & right_set) / len(union)


def sha_counter_bootstrap_indices(
    population_size: int, batch_number: int, replicate_number: int
) -> Iterator[int]:
    seed_material = (
        f"{CORPUS_VERSION}:bootstrap:{batch_number}:{replicate_number}"
    )
    for draw_number in range(population_size):
        digest = hashlib.sha256(
            f"{seed_material}:{draw_number}".encode("utf-8")
        ).digest()
        yield int.from_bytes(digest[:8], byteorder="big") % population_size


def bootstrap_neighbour_diagnostic(
    cumulative_documents: Sequence[dict[str, Any]], batch_number: int
) -> dict[str, Any]:
    full_pair_counts = pair_counts(cumulative_documents)
    full_neighbours = neighbour_lists(full_pair_counts, BOOTSTRAP_NEIGHBOUR_K)
    document_frequency: Counter[str] = Counter()
    for document in cumulative_documents:
        document_frequency.update(set(document["expressions"]))

    eligible = sorted(
        expression
        for expression, frequency in document_frequency.items()
        if frequency >= BOOTSTRAP_MIN_DOCUMENT_FREQUENCY
        and len(full_neighbours.get(expression, ()))
        >= BOOTSTRAP_NEIGHBOUR_K
    )
    jaccards: list[float] = []
    for replicate_number in range(1, BOOTSTRAP_REPLICATES + 1):
        sampled = [
            cumulative_documents[index]
            for index in sha_counter_bootstrap_indices(
                len(cumulative_documents), batch_number, replicate_number
            )
        ]
        sampled_neighbours = neighbour_lists(
            pair_counts(sampled), BOOTSTRAP_NEIGHBOUR_K
        )
        for expression in eligible:
            jaccards.append(
                jaccard(
                    full_neighbours[expression],
                    sampled_neighbours.get(expression, ()),
                )
            )

    return {
        "replicate_count": BOOTSTRAP_REPLICATES,
        "eligible_expression_count": len(eligible),
        "minimum_document_frequency": BOOTSTRAP_MIN_DOCUMENT_FREQUENCY,
        "neighbour_k": BOOTSTRAP_NEIGHBOUR_K,
        "sampling_unit": "captured_document",
        "sample_size_per_replicate": len(cumulative_documents),
        "sampling": "with_replacement",
        "prng": "SHA-256 counter mode; first 64 bits modulo population size",
        "seed_material": (
            f"{CORPUS_VERSION}:bootstrap:{batch_number}:<replicate>:<draw>"
        ),
        "comparison": "replicate top-5 cooccurrence neighbours versus full cumulative-sample top-5",
        "median_jaccard": median(jaccards) if jaccards else None,
        "mean_jaccard": (
            sum(jaccards) / len(jaccards) if jaccards else None
        ),
        "comparison_count": len(jaccards),
    }


def build_expression_statistics(
    documents: Sequence[dict[str, Any]],
    lexical_forms: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    expression_frequency: Counter[str] = Counter()
    document_frequency: Counter[str] = Counter()
    publisher_sets: dict[str, set[str]] = defaultdict(set)

    for document in documents:
        expression_frequency.update(document["expressions"])
        unique_expressions = set(document["expressions"])
        document_frequency.update(unique_expressions)
        for expression in unique_expressions:
            publisher_sets[expression].add(document["publisher_id"])

    normalized_representative: dict[str, dict[str, str]] = {}
    for lexical_form in lexical_forms.values():
        normalized = lexical_form["normalized_text"]
        existing = normalized_representative.get(normalized)
        if existing is None or lexical_form["basic_normalized_text"] < existing[
            "basic_normalized_text"
        ]:
            normalized_representative[normalized] = lexical_form

    representative_keys = {
        normalized: value["expression_key"]
        for normalized, value in normalized_representative.items()
    }
    representative_basic = {
        normalized: value["basic_normalized_text"]
        for normalized, value in normalized_representative.items()
    }
    statistics: list[dict[str, Any]] = []
    total_documents = len(documents)
    total_publishers = len({document["publisher_id"] for document in documents})
    for normalized in sorted(expression_frequency):
        occurrence_count = expression_frequency[normalized]
        doc_count = document_frequency[normalized]
        publisher_count = len(publisher_sets[normalized])
        statistics.append(
            {
                "frequency_key": (
                    f"frequency.{CORPUS_VERSION}.{sha256_text(normalized)}"
                ),
                "representative_expression_key": representative_keys[normalized],
                "representative_basic_normalized_text": representative_basic[
                    normalized
                ],
                "normalized_text": normalized,
                "expression_frequency": occurrence_count,
                "document_frequency": doc_count,
                "publisher_prevalence_count": publisher_count,
                "publisher_sample_count": total_publishers,
                # Firstbloom does not assert roaster country.  Coffee-origin
                # geography is audited separately and must not be substituted.
                "country_prevalence_count": None,
                "country_sample_count": None,
                "value_semantics": (
                    "Retained normalized phrase occurrence, document, and "
                    "publisher counts in the frozen pilot. Country prevalence "
                    "is NULL because roaster country is not source asserted."
                ),
            }
        )

    require(
        len(statistics) == EXPECTED_NORMALIZED_EXPRESSIONS,
        "normalized expression frequency row count changed",
    )

    cooccurrences: list[dict[str, Any]] = []
    all_pair_counts = pair_counts(documents)
    require(
        len(all_pair_counts) == EXPECTED_COOCCURRENCE_PAIRS,
        f"cooccurrence pair count is {len(all_pair_counts)}, expected {EXPECTED_COOCCURRENCE_PAIRS}",
    )
    for (subject, object_expression), count in sorted(all_pair_counts.items()):
        subject_document_count = document_frequency[subject]
        object_document_count = document_frequency[object_expression]
        p_xy = count / total_documents
        p_x = subject_document_count / total_documents
        p_y = object_document_count / total_documents
        pmi = math.log(p_xy / (p_x * p_y))
        npmi = pmi / -math.log(p_xy) if p_xy < 1 else 1.0
        subject_key = representative_keys[subject]
        object_key = representative_keys[object_expression]
        subject_basic = representative_basic[subject]
        object_basic = representative_basic[object_expression]
        pair_hash = sha256_text(f"{subject}\0{object_expression}")
        cooccurrences.append(
            {
                "pair_key": f"cooccurrence.{CORPUS_VERSION}.{pair_hash}",
                "subject_expression_key": subject_key,
                "object_expression_key": object_key,
                "subject_basic_normalized_text": subject_basic,
                "object_basic_normalized_text": object_basic,
                "subject_normalized_text": subject,
                "object_normalized_text": object_expression,
                "document_cooccurrence_count": count,
                "sample_count": total_documents,
                "npmi": min(1.0, max(-1.0, npmi)),
                "subject_given_object_probability": (
                    count / object_document_count
                ),
                "object_given_subject_probability": (
                    count / subject_document_count
                ),
                "subject_document_frequency": subject_document_count,
                "object_document_frequency": object_document_count,
                "value_semantics": "Document-level co-occurrence and NPMI over retained normalized expressions; not perceptual similarity.",
            }
        )

    return statistics, cooccurrences, representative_keys


def build_diagnostics(
    documents: Sequence[dict[str, Any]],
    product_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []
    prior_rank: list[str] | None = None
    prior_neighbours: dict[str, tuple[str, ...]] | None = None
    prior_vocabulary: set[str] = set()

    for batch_number in range(1, MAX_BATCH + 1):
        cumulative = [
            document
            for document in documents
            if document["batch_number"] <= batch_number
        ]
        frequency: Counter[str] = Counter(
            expression
            for document in cumulative
            for expression in document["expressions"]
        )
        rank = [
            expression
            for expression, _count in sorted(
                frequency.items(), key=lambda item: (-item[1], item[0])
            )
        ]
        current_vocabulary = set(frequency)
        neighbours = neighbour_lists(
            pair_counts(cumulative), BOOTSTRAP_NEIGHBOUR_K
        )

        top_25_overlap = None
        top_100_overlap = None
        consecutive_neighbour_jaccard = None
        consecutive_neighbour_eligible_count = 0
        if prior_rank is not None and prior_neighbours is not None:
            top_25_overlap = len(set(prior_rank[:25]) & set(rank[:25]))
            top_100_overlap = len(set(prior_rank[:100]) & set(rank[:100]))
            common = sorted(set(prior_neighbours) & set(neighbours))
            neighbour_values = [
                jaccard(prior_neighbours[expression], neighbours[expression])
                for expression in common
                if len(prior_neighbours[expression]) == BOOTSTRAP_NEIGHBOUR_K
                and len(neighbours[expression]) == BOOTSTRAP_NEIGHBOUR_K
            ]
            consecutive_neighbour_eligible_count = len(neighbour_values)
            consecutive_neighbour_jaccard = (
                median(neighbour_values) if neighbour_values else None
            )

        publisher_counts = Counter(
            document["publisher_id"] for document in cumulative
        )
        publisher_shares = [
            count / len(cumulative) for count in publisher_counts.values()
        ]

        origin_country_counts: Counter[str] = Counter()
        origin_unknown_documents = 0
        for document in cumulative:
            codes = product_metadata[document["release_id"]][
                "coffee_origin_country_codes"
            ]
            if not codes:
                origin_unknown_documents += 1
            else:
                origin_country_counts.update(set(codes))
        max_origin = (
            max(
                origin_country_counts.items(),
                key=lambda item: (item[1], item[0]),
            )
            if origin_country_counts
            else (None, 0)
        )

        stages.append(
            {
                "batch_number": batch_number,
                "cumulative_document_count": len(cumulative),
                "cumulative_publisher_count": len(publisher_counts),
                "cumulative_retained_occurrence_count": sum(frequency.values()),
                "cumulative_unique_normalized_expression_count": len(frequency),
                "new_normalized_expression_count": len(
                    current_vocabulary - prior_vocabulary
                ),
                "hapax_expression_count": sum(
                    count == 1 for count in frequency.values()
                ),
                "top_25_set_overlap_with_previous_batch": top_25_overlap,
                "top_25_denominator": 25 if prior_rank is not None else None,
                "top_100_set_overlap_with_previous_batch": top_100_overlap,
                "top_100_denominator": 100 if prior_rank is not None else None,
                "rank_method": "retained normalized occurrence frequency descending; normalized text ascending tie-break",
                "consecutive_batch_top5_neighbour_median_jaccard": consecutive_neighbour_jaccard,
                "consecutive_batch_neighbour_eligible_expression_count": consecutive_neighbour_eligible_count,
                "bootstrap": bootstrap_neighbour_diagnostic(
                    cumulative, batch_number
                ),
                "publisher_max_document_share": max(publisher_shares),
                "publisher_document_hhi": sum(
                    share * share for share in publisher_shares
                ),
                "roaster_country_concentration": None,
                "roaster_country_concentration_status": "not_assessed_source_country_absent",
                "coffee_origin_country_distinct_source_code_count": len(
                    origin_country_counts
                ),
                "coffee_origin_country_max_source_code": max_origin[0],
                "coffee_origin_country_max_document_share": (
                    max_origin[1] / len(cumulative)
                ),
                "coffee_origin_country_unknown_document_count": origin_unknown_documents,
                "coffee_origin_country_unknown_document_share": (
                    origin_unknown_documents / len(cumulative)
                ),
                "origin_country_semantics": "Firstbloom country short codes for coffee origin; codes are source metadata, not asserted ISO identifiers; multi-country documents count once for each explicit code.",
            }
        )
        prior_rank = rank
        prior_neighbours = neighbours
        prior_vocabulary = current_vocabulary

    final = stages[-1]
    require(
        EXPECTED_FINAL_TOP_25_OVERLAP is not None
        and final["top_25_set_overlap_with_previous_batch"]
        == EXPECTED_FINAL_TOP_25_OVERLAP,
        "batch 15-to-16 top-25 overlap changed",
    )
    require(
        EXPECTED_FINAL_TOP_100_OVERLAP is not None
        and final["top_100_set_overlap_with_previous_batch"]
        == EXPECTED_FINAL_TOP_100_OVERLAP,
        "batch 15-to-16 top-100 overlap changed",
    )
    require(
        final["coffee_origin_country_unknown_document_count"] == 0,
        "expected explicit origin country metadata for every pilot document",
    )
    require(
        final["coffee_origin_country_distinct_source_code_count"] == 36,
        "Firstbloom origin-country source-code coverage changed",
    )
    plateau = [
        stage["bootstrap"]["median_jaccard"] for stage in stages[-3:]
    ]
    require(
        EXPECTED_BOOTSTRAP_PLATEAU_VALUE is not None
        and all(
            value is not None
            and math.isclose(
                value,
                EXPECTED_BOOTSTRAP_PLATEAU_VALUE,
                rel_tol=0,
                abs_tol=1e-15,
            )
            for value in plateau
        ),
        "bootstrap median must match the frozen cumulative-batch 14-16 plateau",
    )

    return {
        "corpus_version": CORPUS_VERSION,
        "generator_version": GENERATOR_VERSION,
        "stages": stages,
        "stop_decision": {
            "stopped_after_batch": MAX_BATCH,
            "vocabulary_convergence_claimed": False,
            "long_tail_discovery_continues": final[
                "new_normalized_expression_count"
            ]
            > 0,
            "bootstrap_median_plateau_batches": [14, 15, 16],
            "bootstrap_median_plateau_value": final["bootstrap"][
                "median_jaccard"
            ],
            "basis": [
                "high but incomplete consecutive-batch high-frequency rank overlap",
                "fixed-seed document bootstrap median plateaued across cumulative batches 14 through 16",
                "very low publisher concentration under the one-release-per-publisher-per-batch frame",
                "bounded moderate-pilot scope rather than a claim of global representativeness",
            ],
        },
    }


def validate_rights_matrix(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / RIGHTS_RELATIVE_PATH
    with path.open(encoding="utf-8", newline="") as handle:
        physical_rows = list(csv.reader(handle, delimiter="\t"))
    require(bool(physical_rows), "source_rights.tsv is empty")
    expected_width = len(physical_rows[0])
    require(expected_width == 20, "source_rights.tsv must have exactly 20 columns")
    for line_number, row in enumerate(physical_rows[1:], start=2):
        require(
            len(row) == expected_width,
            f"source_rights.tsv line {line_number} has {len(row)} fields; expected {expected_width}",
        )

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    required_columns = {
        "policy_key",
        "source_name",
        "country_code",
        "domain",
        "robots_url",
        "robots_status",
        "terms_url",
        "terms_status",
        "access_method",
        "copyright_status",
        "redistribution_status",
        "commercial_use_status",
        "machine_access_status",
        "checked_at",
        "decision",
        "source_blocked",
        "raw_text_allowed",
        "production_export_allowed",
        "evidence_urls",
        "notes",
    }
    require(
        set(reader.fieldnames or []) == required_columns,
        "source_rights.tsv columns changed",
    )
    require(len(rows) == 15, "rights matrix must contain Firstbloom plus 14 live reviews")
    require(
        len({row["policy_key"] for row in rows}) == len(rows),
        "rights matrix policy keys must be unique",
    )
    decisions = Counter(row["decision"] for row in rows)
    require(decisions["ALLOW_DERIVED_TERMS"] == 1, "one derived-terms policy required")
    require(decisions["BLOCKED"] == 8, "eight blocked live-source reviews required")
    require(decisions["MANUAL_ONLY"] == 3, "three manual-only reviews required")
    require(decisions["UNKNOWN"] == 3, "three unknown reviews required")
    allowed_decisions = {
        "ALLOW_DERIVED_TERMS",
        "BLOCKED",
        "MANUAL_ONLY",
        "UNKNOWN",
    }
    allowed_booleans = {"true", "false"}
    for row in rows:
        require(row["checked_at"] == CHECKED_AT, "rights review date changed")
        require(
            row["decision"] in allowed_decisions,
            f"rights review {row['policy_key']} has an unsupported decision",
        )
        require(
            row["source_blocked"] in allowed_booleans
            and row["raw_text_allowed"] in allowed_booleans
            and row["production_export_allowed"] in allowed_booleans,
            f"rights review {row['policy_key']} has a non-boolean gate",
        )
        require(
            not row["country_code"]
            or bool(re.fullmatch(r"[A-Z]{2}", row["country_code"])),
            f"rights review {row['policy_key']} has an invalid review-country code",
        )
        require(
            row["domain"] == row["domain"].lower()
            and bool(re.fullmatch(r"[^/:\s]+", row["domain"])),
            f"rights review {row['policy_key']} has an invalid domain host",
        )
        require(
            all(
                row[column].strip()
                for column in required_columns - {"country_code"}
            ),
            f"rights review {row['policy_key']} has an unexpected empty field",
        )
        evidence_urls = json.loads(row["evidence_urls"])
        require(
            isinstance(evidence_urls, list) and evidence_urls,
            f"rights review {row['policy_key']} requires evidence URLs",
        )
        require(
            all(
                isinstance(url, str)
                and (url.startswith("https://") or url.startswith("http://"))
                for url in evidence_urls
            ),
            f"rights review {row['policy_key']} has a non-HTTP evidence locator",
        )
        if row["decision"] != "ALLOW_DERIVED_TERMS":
            require(
                row["raw_text_allowed"] == "false"
                and row["production_export_allowed"] == "false",
                f"live review {row['policy_key']} must keep raw/export gates closed",
            )
        if row["decision"] == "UNKNOWN":
            require(
                row["source_blocked"] == "true",
                f"unknown review {row['policy_key']} must be effectively blocked",
            )
    return rows


def build_publishers(
    selected: Sequence[dict[str, Any]],
    roasters: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    selected_roaster_ids = sorted(
        {release["roaster_id"] for release in selected}, key=int
    )
    publishers: list[dict[str, Any]] = []
    for roaster_id in selected_roaster_ids:
        roaster = roasters[roaster_id]
        name = clean_label(roaster.get("label")) or clean_label(roaster.get("name"))
        require(name is not None, f"roaster {roaster_id} has no usable name")
        website = clean_label(roaster.get("website"))
        parsed_domain = urlparse(website).hostname if website else None
        require(
            parsed_domain is not None,
            f"roaster {roaster_id} has no explicit website host",
        )
        parsed_domain = parsed_domain.lower()
        publishers.append(
            {
                "publisher_key": f"publisher.firstbloom.{roaster_id}",
                "source_policy_key": "source_policy.firstbloom.a6cb002.derived_terms",
                "external_publisher_key": roaster_id,
                "name": name,
                "domain": parsed_domain,
                "roaster_country_code": None,
                "metadata": {
                    "firstbloom_roaster_id": roaster_id,
                    "source_name": clean_label(roaster.get("name")),
                    "source_label": clean_label(roaster.get("label")),
                    "website": website,
                    "iana_timezone": clean_label(roaster.get("iana_timezone")),
                    "roaster_country_not_inferred": True,
                },
            }
        )
    require(len(publishers) == EXPECTED_PUBLISHERS, "publisher build count changed")
    return publishers


def build_products(
    selected: Sequence[dict[str, Any]],
    product_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for release in selected:
        grouped[(release["roaster_id"], release["product_id"])].append(release)

    products: list[dict[str, Any]] = []
    for (roaster_id, product_id), releases in sorted(
        grouped.items(), key=lambda item: (int(item[0][0]), int(item[0][1]))
    ):
        names = stable_unique(clean_label(row.get("product_name")) for row in releases)
        require(
            len(names) <= 1,
            f"Firstbloom product {product_id} has conflicting selected names",
        )
        release_ids = sorted(
            (row["product_release_id"] for row in releases), key=int
        )

        def union_metadata(field: str) -> list[str]:
            return stable_unique(
                value
                for release_id in release_ids
                for value in product_metadata[release_id][field]
            )

        products.append(
            {
                "product_key": f"product.firstbloom.{product_id}",
                "publisher_key": f"publisher.firstbloom.{roaster_id}",
                "external_product_key": product_id,
                "product_name": names[0] if names else None,
                "coffee_origin_country_codes": union_metadata(
                    "coffee_origin_country_codes"
                ),
                "coffee_regions": union_metadata("coffee_regions"),
                "producer_names": union_metadata("producer_names"),
                "variety_names": union_metadata("variety_names"),
                "process_names": union_metadata("process_names"),
                "notes": {
                    "source": "Firstbloom Data",
                    "firstbloom_product_id": product_id,
                    "firstbloom_roaster_id": roaster_id,
                    "selected_release_ids": release_ids,
                    "selected_release_count": len(release_ids),
                    "farm_names": union_metadata("farm_names"),
                    "cleaning_process_names": union_metadata(
                        "cleaning_process_names"
                    ),
                    "drying_process_names": union_metadata(
                        "drying_process_names"
                    ),
                    "coffee_origin_country_names": union_metadata(
                        "coffee_origin_country_names"
                    ),
                    "metadata_aggregation": "stable union of explicit selected-release values; no missing value inferred",
                },
            }
        )
    require(
        len(products) == EXPECTED_PRODUCTS,
        f"industry product count is {len(products)}, expected {EXPECTED_PRODUCTS}",
    )
    return products


def date_part(timestamp_text: str | None) -> str | None:
    if not timestamp_text:
        return None
    return timestamp_text[:10]


def build_inventory(
    selected: Sequence[dict[str, Any]],
    product_metadata: dict[str, dict[str, Any]],
    observations: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for observation in observations:
        counts[observation["release_id"]]["raw"] += 1
        counts[observation["release_id"]][
            "retained" if observation["retained"] else "redacted"
        ] += 1

    inventory: list[dict[str, Any]] = []
    for release in selected:
        release_id = release["product_release_id"]
        metadata = product_metadata[release_id]
        raw_note_sha256 = sha256_text(release["roaster_tasting_notes_string"])
        product_composite = {
            "firstbloom_product_id": release["product_id"],
            "firstbloom_product_release_id": release_id,
            "firstbloom_roaster_id": release["roaster_id"],
            "product_name": clean_label(release.get("product_name")),
            "product_created_at": clean_label(release.get("product_created_at")),
            "release_created_at": clean_label(release.get("release_created_at")),
            "coffee_origin_country_codes": metadata[
                "coffee_origin_country_codes"
            ],
            "coffee_regions": metadata["coffee_regions"],
            "producer_names": metadata["producer_names"],
            "farm_names": metadata["farm_names"],
            "variety_names": metadata["variety_names"],
            "process_names": metadata["process_names"],
        }
        inventory.append(
            {
                "product_key": f"product.firstbloom.{release['product_id']}",
                "document_key": f"document.firstbloom.release_{release_id}",
                "publisher_key": f"publisher.firstbloom.{release['roaster_id']}",
                "source_policy_key": "source_policy.firstbloom.a6cb002.derived_terms",
                "batch_key": (
                    f"batch.firstbloom_a6cb002_pilot_v1.{release['batch_number']}"
                ),
                "external_product_key": release["product_id"],
                "external_release_key": release_id,
                "product_name": clean_label(release.get("product_name")),
                "listing_date": date_part(release.get("release_created_at")),
                "roast_date": None,
                "captured_at": CAPTURED_AT,
                "canonical_url": None,
                "content_sha256": raw_note_sha256,
                "raw_text_sha256": raw_note_sha256,
                "metadata_composite_sha256": sha256_text(
                    canonical_json(product_composite)
                ),
                "selection_sha256": release["selection_sha256"],
                "batch_number": release["batch_number"],
                "raw_observation_count": counts[release_id]["raw"],
                "retained_observation_count": counts[release_id]["retained"],
                "redacted_observation_count": counts[release_id]["redacted"],
                "coffee_origin_country_codes": metadata[
                    "coffee_origin_country_codes"
                ],
                "coffee_regions": metadata["coffee_regions"],
                "producer_names": metadata["producer_names"],
                "farm_names": metadata["farm_names"],
                "variety_names": metadata["variety_names"],
                "process_names": metadata["process_names"],
                "metadata": {
                    "source": "Firstbloom Data",
                    "source_commit": PINNED_SOURCE_SHA,
                    "source_product_created_at": clean_label(
                        release.get("product_created_at")
                    ),
                    "source_release_created_at": clean_label(
                        release.get("release_created_at")
                    ),
                    "source_relation_row_count": metadata[
                        "relation_row_count"
                    ],
                    "coffee_origin_country_names": metadata[
                        "coffee_origin_country_names"
                    ],
                    "farm_names": metadata["farm_names"],
                    "cleaning_process_names": metadata[
                        "cleaning_process_names"
                    ],
                    "drying_process_names": metadata[
                        "drying_process_names"
                    ],
                    "raw_text_stored": False,
                    "complete_note_string_emitted": False,
                    "roaster_description_emitted": False,
                    "consumer_review_file_read": False,
                },
            }
        )
    require(len(inventory) == EXPECTED_DOCUMENTS, "inventory count changed")
    return inventory


def build_duplicate_reviews(
    inventory: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    document_order = {
        row["document_key"]: index for index, row in enumerate(inventory, start=1)
    }
    candidates: dict[tuple[str, str], tuple[int, str]] = {}

    def add_group(field: str, priority: int, basis: str) -> None:
        groups: dict[str, list[str]] = defaultdict(list)
        for row in inventory:
            value = row.get(field)
            if value:
                groups[str(value)].append(row["document_key"])
        for document_keys in groups.values():
            ordered = sorted(document_keys, key=document_order.__getitem__)
            for left_index, earlier in enumerate(ordered):
                for later in ordered[left_index + 1 :]:
                    pair = (earlier, later)
                    existing = candidates.get(pair)
                    if existing is None or priority < existing[0]:
                        candidates[pair] = (priority, basis)

    add_group("product_key", 3, "publisher_product_key")
    add_group("content_sha256", 4, "content_hash")
    add_group("metadata_composite_sha256", 5, "metadata_composite_hash")

    rationale = {
        "publisher_product_key": "Distinct Firstbloom release identifiers for one stable product are retained as historical release observations.",
        "content_hash": "Distinct Firstbloom release identifiers are retained; matching tasting-note content alone does not establish a duplicate document.",
        "metadata_composite_hash": "Distinct Firstbloom release identifiers are retained; matching structured metadata alone does not establish a duplicate document.",
    }
    reviews = [
        {
            "duplicate_review_key": (
                "duplicate_review."
                + sha256_text(f"{earlier}\0{later}")
            ),
            "earlier_document_key": earlier,
            "later_document_key": later,
            "duplicate_match_basis_code": basis,
            "duplicate_review_decision_code": "distinct",
            "reviewed_at": CAPTURED_AT,
            "rationale": rationale[basis],
        }
        for (earlier, later), (_priority, basis) in sorted(
            candidates.items(),
            key=lambda item: (
                document_order[item[0][0]],
                document_order[item[0][1]],
            ),
        )
    ]
    require(
        len(reviews) == EXPECTED_DUPLICATE_REVIEWS,
        f"duplicate review count is {len(reviews)}, expected {EXPECTED_DUPLICATE_REVIEWS}",
    )
    return reviews


def expression_rows(
    observations: Sequence[dict[str, Any]],
    lexical_forms: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    raw_variants: dict[str, set[str]] = defaultdict(set)
    occurrence_counts: Counter[str] = Counter()
    for observation in observations:
        if not observation["retained"]:
            continue
        basic = observation["basic_normalized_text"]
        raw_variants[basic].add(observation["observation_text"])
        occurrence_counts[basic] += 1
    return [
        {
            **lexical_forms[basic],
            "language_tag_code": "en",
            "raw_variant_count": len(raw_variants[basic]),
            "occurrence_count": occurrence_counts[basic],
        }
        for basic in sorted(lexical_forms)
    ]


def require_private_review_path(path: Path, repo_root: Path) -> Path:
    resolved = path.resolve()
    private_root = Path("/private/tmp").resolve()
    require(
        resolved.is_relative_to(private_root),
        "protected review artifacts must stay under /private/tmp",
    )
    require(
        not resolved.is_relative_to(repo_root.resolve()),
        "protected review artifacts must not be written inside the repository",
    )
    return resolved


def write_private_review_candidates(
    path: Path,
    observations: Sequence[dict[str, Any]],
    repo_root: Path,
) -> dict[str, Any]:
    resolved = require_private_review_path(path, repo_root)
    by_hash: dict[str, dict[str, Any]] = {}
    document_keys: dict[str, set[str]] = defaultdict(set)
    occurrence_counts: Counter[str] = Counter()
    for observation in observations:
        phrase = observation["private_review_candidate_text"]
        if phrase is None:
            continue
        surface_hash = observation["raw_phrase_sha256"]
        existing = by_hash.get(surface_hash)
        if existing is None:
            by_hash[surface_hash] = {
                "source_surface_sha256": surface_hash,
                "candidate_phrase": phrase,
                "unicode_character_count": observation[
                    "unicode_character_count"
                ],
            }
        else:
            require(
                existing["candidate_phrase"] == phrase,
                "SHA-256 collision in review candidates",
            )
        occurrence_counts[surface_hash] += 1
        document_keys[surface_hash].add(observation["document_key"])

    require(
        len(by_hash) == EXPECTED_REVIEW_CANDIDATE_UNIQUE_HASHES,
        "private review candidate count changed",
    )
    rows = []
    for surface_hash in sorted(by_hash):
        rows.append(
            {
                **by_hash[surface_hash],
                "occurrence_count": occurrence_counts[surface_hash],
                "document_count": len(document_keys[surface_hash]),
            }
        )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.touch(mode=0o600, exist_ok=True)
    resolved.chmod(0o600)
    write_tsv(
        resolved,
        rows,
        [
            "source_surface_sha256",
            "candidate_phrase",
            "unicode_character_count",
            "occurrence_count",
            "document_count",
        ],
    )
    resolved.chmod(0o600)
    file_sha256 = sha256_bytes(resolved.read_bytes())
    require(
        file_sha256 == EXPECTED_PRIVATE_REVIEW_CANDIDATE_SHA256,
        "private review candidate artifact hash changed",
    )
    return {
        "path": str(resolved),
        "candidate_rows": len(rows),
        "file_sha256": file_sha256,
        "max_unicode_characters": max(
            row["unicode_character_count"] for row in rows
        ),
    }


def write_private_spot_audit(
    path: Path,
    observations: Sequence[dict[str, Any]],
    admission_reviews: dict[str, dict[str, str]],
    repo_root: Path,
) -> dict[str, Any]:
    resolved = require_private_review_path(path, repo_root)
    candidates: dict[str, dict[str, Any]] = {}
    for observation in observations:
        phrase = observation["private_review_candidate_text"]
        if phrase is None:
            continue
        surface_hash = observation["raw_phrase_sha256"]
        existing = candidates.get(surface_hash)
        if existing is None:
            review = admission_reviews[surface_hash]
            candidates[surface_hash] = {
                **review,
                "candidate_phrase": phrase,
                "unicode_character_count": observation[
                    "unicode_character_count"
                ],
                "word_token_count": len(WORD_TOKEN_RE.findall(phrase)),
            }
        else:
            require(
                existing["candidate_phrase"] == phrase,
                "SHA-256 collision in spot-audit candidates",
            )
    require(
        set(candidates) == set(admission_reviews),
        "spot-audit candidate inventory differs from admission review",
    )

    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def deterministic_order(row: dict[str, Any]) -> str:
        return sha256_text(
            f"{SPOT_AUDIT_SAMPLING_SALT}:{row['source_surface_sha256']}"
        )

    def take(
        stratum: str,
        values: Sequence[dict[str, Any]],
        count: int,
    ) -> None:
        added = 0
        for row in values:
            surface_hash = row["source_surface_sha256"]
            if surface_hash in seen:
                continue
            selected.append({"audit_stratum": stratum, **row})
            seen.add(surface_hash)
            added += 1
            if added >= count:
                break

    take(
        "remediated_v1_accepted_blockers",
        [candidates[surface_hash] for surface_hash in SPOT_AUDIT_REMEDIATED_HASHES],
        len(SPOT_AUDIT_REMEDIATED_HASHES),
    )
    admitted = [
        row
        for row in candidates.values()
        if row["final_admission_code"]
        == "ADMIT_ENGLISH_TASTING_LANGUAGE"
    ]
    take(
        "accepted_deterministic_hash_sample",
        sorted(admitted, key=deterministic_order),
        60,
    )
    take(
        "accepted_longest_remaining",
        sorted(
            admitted,
            key=lambda row: (
                -row["unicode_character_count"],
                row["source_surface_sha256"],
            ),
        ),
        40,
    )
    take(
        "accepted_highest_token_count_remaining",
        sorted(
            admitted,
            key=lambda row: (
                -row["word_token_count"],
                row["source_surface_sha256"],
            ),
        ),
        30,
    )
    for decision, count, stratum in [
        ("DISAGREEMENT", 20, "rejected_review_disagreement"),
        (
            "NARRATIVE_OR_NON_DESCRIPTOR",
            20,
            "rejected_review_narrative",
        ),
        ("NON_ENGLISH", 20, "rejected_review_non_english"),
        ("UNCERTAIN", 20, "rejected_review_uncertain"),
    ]:
        values = [
            row
            for row in candidates.values()
            if row["consensus_decision_code"] == decision
        ]
        take(
            stratum,
            sorted(values, key=deterministic_order),
            min(count, len(values)),
        )
    for gate, count, stratum in [
        (
            "REJECT_SENTENCE_PUNCTUATION",
            30,
            "rejected_structural_sentence_punctuation",
        ),
        (
            "REJECT_PERSONAL_PRONOUN_OR_FINITE_AUXILIARY",
            20,
            "rejected_structural_personal_or_auxiliary",
        ),
        (
            "REJECT_GT_8_WORD_TOKENS",
            20,
            "rejected_structural_gt8_tokens",
        ),
        (
            "REJECT_CONTROL_OR_FORMAT_CHARACTER",
            20,
            "rejected_structural_control_or_format",
        ),
        (
            "REJECT_REPEATED_CONNECTIVE",
            20,
            "rejected_structural_repeated_connective",
        ),
    ]:
        values = [
            row
            for row in candidates.values()
            if row["structural_gate_code"] == gate
        ]
        take(
            stratum,
            sorted(values, key=deterministic_order),
            min(count, len(values)),
        )

    admitted_count = sum(
        row["final_admission_code"]
        == "ADMIT_ENGLISH_TASTING_LANGUAGE"
        for row in selected
    )
    require(
        len(selected) == EXPECTED_PRIVATE_SPOT_AUDIT_ROWS
        and admitted_count == EXPECTED_PRIVATE_SPOT_AUDIT_ADMITTED_ROWS
        and len(selected) - admitted_count
        == EXPECTED_PRIVATE_SPOT_AUDIT_REJECTED_ROWS
        and all(surface_hash in seen for surface_hash in SPOT_AUDIT_REMEDIATED_HASHES),
        "private spot-audit sampling contract changed",
    )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.touch(mode=0o600, exist_ok=True)
    resolved.chmod(0o600)
    write_tsv(
        resolved,
        selected,
        [
            "audit_stratum",
            "source_surface_sha256",
            "candidate_phrase",
            "unicode_character_count",
            "word_token_count",
            "reviewer_one_decision_code",
            "reviewer_two_decision_code",
            "consensus_decision_code",
            "structural_gate_code",
            "final_admission_code",
            "admitted_language_tag_code",
            "exclusion_reason_code",
        ],
    )
    resolved.chmod(0o600)
    file_sha256 = sha256_bytes(resolved.read_bytes())
    require(
        file_sha256 == EXPECTED_PRIVATE_SPOT_AUDIT_SHA256,
        "private spot-audit artifact hash changed",
    )
    return {
        "path": str(resolved),
        "sampled_rows": len(selected),
        "sampled_admitted_rows": admitted_count,
        "sampled_rejected_rows": len(selected) - admitted_count,
        "file_sha256": file_sha256,
    }


def read_private_review_pass(
    path: Path,
    candidate_hashes: set[str],
    repo_root: Path,
    expected_sha256: str,
) -> tuple[dict[str, str], str]:
    resolved = require_private_review_path(path, repo_root)
    require(resolved.is_file(), f"missing private review pass: {resolved}")
    require(
        bool(re.fullmatch(r"[0-9a-f]{64}", expected_sha256)),
        "private review expected SHA-256 is invalid",
    )
    payload = resolved.read_bytes()
    actual_sha256 = sha256_bytes(payload)
    require(
        actual_sha256 == expected_sha256,
        f"private review pass SHA-256 changed: {resolved}",
    )
    decoded = payload.decode("utf-8")
    physical_rows = list(
        csv.reader(io.StringIO(decoded, newline=""), delimiter="\t")
    )
    expected_header = ["source_surface_sha256", "review_decision_code"]
    require(
        bool(physical_rows) and physical_rows[0] == expected_header,
        "private review pass columns changed",
    )
    decisions: dict[str, str] = {}
    for line_number, row in enumerate(physical_rows[1:], start=2):
        require(
            len(row) == 2,
            f"private review pass line {line_number} has extra content",
        )
        surface_hash, decision = row
        require(
            bool(re.fullmatch(r"[0-9a-f]{64}", surface_hash)),
            "private review pass contains an invalid SHA-256",
        )
        require(
            surface_hash not in decisions,
            "private review pass contains a duplicate hash",
        )
        require(
            decision in REVIEW_DECISION_CODES,
            "private review pass contains an unsupported decision",
        )
        decisions[surface_hash] = decision
    require(
        set(decisions) == candidate_hashes,
        "private review pass does not cover the exact candidate inventory",
    )
    return decisions, actual_sha256


def merge_private_review_passes(
    observations: Sequence[dict[str, Any]],
    reviewer_one_path: Path,
    reviewer_two_path: Path,
    reviewer_one_id: str,
    reviewer_two_id: str,
    reviewer_one_expected_sha256: str,
    reviewer_two_expected_sha256: str,
    repo_root: Path,
) -> dict[str, Any]:
    require(
        (reviewer_one_id, reviewer_two_id) == EXPECTED_REVIEWER_IDS,
        "review pass identifiers differ from the frozen independent passes",
    )
    require(
        bool(re.fullmatch(r"[a-z0-9_.-]+", reviewer_one_id))
        and bool(re.fullmatch(r"[a-z0-9_.-]+", reviewer_two_id)),
        "review pass identifiers must be stable lowercase keys",
    )
    candidate_phrase_by_hash: dict[str, str] = {}
    for observation in observations:
        phrase = observation["private_review_candidate_text"]
        if phrase is None:
            continue
        surface_hash = observation["raw_phrase_sha256"]
        existing_phrase = candidate_phrase_by_hash.setdefault(
            surface_hash, phrase
        )
        require(
            existing_phrase == phrase,
            "SHA-256 collision in merge candidate inventory",
        )
    candidate_hashes = set(candidate_phrase_by_hash)
    decisions_one, reviewer_one_sha256 = read_private_review_pass(
        reviewer_one_path,
        candidate_hashes,
        repo_root,
        reviewer_one_expected_sha256,
    )
    decisions_two, reviewer_two_sha256 = read_private_review_pass(
        reviewer_two_path,
        candidate_hashes,
        repo_root,
        reviewer_two_expected_sha256,
    )
    rows: list[dict[str, str]] = []
    consensus_counts: Counter[str] = Counter()
    structural_gate_counts: Counter[str] = Counter()
    final_admission_counts: Counter[str] = Counter()
    decision_counts_one = Counter(decisions_one.values())
    decision_counts_two = Counter(decisions_two.values())
    agreement_count = 0
    agreement_matrix: Counter[tuple[str, str]] = Counter()
    for surface_hash in sorted(candidate_hashes):
        decision_one = decisions_one[surface_hash]
        decision_two = decisions_two[surface_hash]
        agreement_matrix[(decision_one, decision_two)] += 1
        agreement_count += decision_one == decision_two
        consensus = expected_consensus_decision(decision_one, decision_two)
        structural_gate = structural_prose_gate_v2(
            candidate_phrase_by_hash[surface_hash]
        )
        final_admission = expected_final_admission_code(
            consensus, structural_gate
        )
        consensus_counts[consensus] += 1
        structural_gate_counts[structural_gate] += 1
        final_admission_counts[final_admission] += 1
        rows.append(
            {
                "source_surface_sha256": surface_hash,
                "reviewer_one_decision_code": decision_one,
                "reviewer_two_decision_code": decision_two,
                "consensus_decision_code": consensus,
                "structural_gate_code": structural_gate,
                "final_admission_code": final_admission,
                "admitted_language_tag_code": (
                    "en"
                    if final_admission == "ADMIT_ENGLISH_TASTING_LANGUAGE"
                    else ""
                ),
                "exclusion_reason_code": (
                    expected_final_exclusion_reason(
                        consensus, structural_gate
                    )
                    or ""
                ),
            }
        )

    output_path = repo_root / ADMISSION_REVIEW_RELATIVE_PATH
    write_tsv(
        output_path,
        rows,
        [
            "source_surface_sha256",
            "reviewer_one_decision_code",
            "reviewer_two_decision_code",
            "consensus_decision_code",
            "structural_gate_code",
            "final_admission_code",
            "admitted_language_tag_code",
            "exclusion_reason_code",
        ],
    )
    review_count = len(candidate_hashes)
    observed_agreement = agreement_count / review_count
    expected_agreement = sum(
        (decision_counts_one[decision] / review_count)
        * (decision_counts_two[decision] / review_count)
        for decision in REVIEW_DECISION_CODES
    )
    cohen_kappa = (
        (observed_agreement - expected_agreement)
        / (1 - expected_agreement)
        if expected_agreement < 1
        else None
    )
    metadata = {
        "review_policy_version": REVIEW_POLICY_VERSION,
        "structural_gate_version": STRUCTURAL_GATE_VERSION,
        "reviewed_at_contract_date": CHECKED_AT,
        "pinned_firstbloom_sha": PINNED_SOURCE_SHA,
        "candidate_hash_inventory_sha256": sha256_text(
            canonical_json(sorted(candidate_hashes))
        ),
        "private_candidate_review_file_sha256": (
            EXPECTED_PRIVATE_REVIEW_CANDIDATE_SHA256
        ),
        "admission_inventory_sha256": sha256_bytes(output_path.read_bytes()),
        "review_passes": [
            {
                "reviewer_id": reviewer_one_id,
                "review_pass_sha256": reviewer_one_sha256,
                "evidence_class": REVIEW_PASS_EVIDENCE_CLASS,
                "human_review": False,
                "automated_language_detection": False,
            },
            {
                "reviewer_id": reviewer_two_id,
                "review_pass_sha256": reviewer_two_sha256,
                "evidence_class": REVIEW_PASS_EVIDENCE_CLASS,
                "human_review": False,
                "automated_language_detection": False,
            },
        ],
        "decision_codes": sorted(REVIEW_DECISION_CODES),
        "decision_definitions": {
            "ENGLISH_TASTING_LANGUAGE": (
                "Concise English sensory, tactile, qualifier, composite-reference, "
                "or process-like tasting language; admission is lexical only and "
                "does not assert a canonical mapping."
            ),
            "NARRATIVE_OR_NON_DESCRIPTOR": (
                "Sentence-like, promotional, evaluative narrative, or other text "
                "that is not a conservative tasting-expression fragment."
            ),
            "NON_ENGLISH": (
                "The reviewed fragment is not English; no alternative language "
                "tag is inferred in this English-only pilot."
            ),
            "UNCERTAIN": (
                "Language or descriptor scope cannot be established conservatively."
            ),
        },
        "consensus_rule": (
            "Admit as en only when both independent passes select "
            "ENGLISH_TASTING_LANGUAGE; every disagreement and every other "
            "decision remains hash-only."
        ),
        "claims_not_made": [
            "human language review",
            "automatic language detection",
            "canonical concept mapping",
            "objective coffee flavor labels",
        ],
        "consensus_counts": dict(sorted(consensus_counts.items())),
        "structural_gate_counts": dict(
            sorted(structural_gate_counts.items())
        ),
        "final_admission_counts": dict(
            sorted(final_admission_counts.items())
        ),
        "structural_gate_contract": {
            "precedence": [
                "Unicode control or format character",
                "sentence punctuation [.!?]",
                "personal-pronoun or finite-auxiliary token",
                "repeated connective token",
                "more than eight Unicode word tokens",
                "pass concise fragment",
            ],
            "false_negative_policy": (
                "Conservative rejection is preferred to retaining narrative prose."
            ),
            "complete_field_surfaces": (
                "Excluded before review candidates are constructed."
            ),
        },
        "review_agreement": {
            "reviewed_hash_count": review_count,
            "agreement_count": agreement_count,
            "disagreement_count": review_count - agreement_count,
            "raw_agreement": observed_agreement,
            "chance_expected_agreement": expected_agreement,
            "cohen_kappa": cohen_kappa,
            "reviewer_one_decision_counts": dict(
                sorted(decision_counts_one.items())
            ),
            "reviewer_two_decision_counts": dict(
                sorted(decision_counts_two.items())
            ),
            "decision_pair_counts": {
                f"{left}|{right}": count
                for (left, right), count in sorted(
                    agreement_matrix.items()
                )
            },
        },
        "spot_audits": spot_audit_receipts(),
    }
    metadata_path = repo_root / ADMISSION_REVIEW_METADATA_RELATIVE_PATH
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )
    return {
        "admission_inventory_path": str(output_path),
        "admission_inventory_sha256": sha256_bytes(output_path.read_bytes()),
        "metadata_path": str(metadata_path),
        "metadata_sha256": sha256_bytes(metadata_path.read_bytes()),
        "candidate_rows": len(rows),
        "consensus_counts": dict(sorted(consensus_counts.items())),
        "structural_gate_counts": dict(
            sorted(structural_gate_counts.items())
        ),
        "final_admission_counts": dict(
            sorted(final_admission_counts.items())
        ),
    }


def write_tsv(
    path: Path, rows: Sequence[dict[str, Any]], columns: Sequence[str]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writerow(columns)
        for row in rows:
            values: list[Any] = []
            for column in columns:
                value = row.get(column)
                if isinstance(value, (dict, list)):
                    value = canonical_json(value)
                elif isinstance(value, bool):
                    value = "true" if value else "false"
                elif value is None:
                    value = ""
                values.append(value)
            writer.writerow(values)


def emit_machine_readable_data(
    data_dir: Path,
    publishers: Sequence[dict[str, Any]],
    products: Sequence[dict[str, Any]],
    inventory: Sequence[dict[str, Any]],
    observations: Sequence[dict[str, Any]],
    expressions: Sequence[dict[str, Any]],
    statistics: Sequence[dict[str, Any]],
    cooccurrences: Sequence[dict[str, Any]],
    duplicate_reviews: Sequence[dict[str, Any]],
    diagnostics: dict[str, Any],
) -> list[Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    path = data_dir / PUBLISHER_TSV
    write_tsv(
        path,
        publishers,
        [
            "publisher_key",
            "source_policy_key",
            "external_publisher_key",
            "name",
            "domain",
            "roaster_country_code",
            "metadata",
        ],
    )
    paths.append(path)

    path = data_dir / DUPLICATE_TSV
    write_tsv(
        path,
        duplicate_reviews,
        [
            "duplicate_review_key",
            "earlier_document_key",
            "later_document_key",
            "duplicate_match_basis_code",
            "duplicate_review_decision_code",
            "reviewed_at",
            "rationale",
        ],
    )
    paths.append(path)

    path = data_dir / PRODUCT_TSV
    write_tsv(
        path,
        products,
        [
            "product_key",
            "publisher_key",
            "external_product_key",
            "product_name",
            "coffee_origin_country_codes",
            "coffee_regions",
            "producer_names",
            "variety_names",
            "process_names",
            "notes",
        ],
    )
    paths.append(path)

    path = data_dir / INVENTORY_TSV
    write_tsv(
        path,
        inventory,
        [
            "product_key",
            "document_key",
            "publisher_key",
            "source_policy_key",
            "batch_key",
            "external_product_key",
            "external_release_key",
            "product_name",
            "listing_date",
            "roast_date",
            "captured_at",
            "canonical_url",
            "content_sha256",
            "raw_text_sha256",
            "metadata_composite_sha256",
            "selection_sha256",
            "batch_number",
            "raw_observation_count",
            "retained_observation_count",
            "redacted_observation_count",
            "coffee_origin_country_codes",
            "coffee_regions",
            "producer_names",
            "farm_names",
            "variety_names",
            "process_names",
            "metadata",
        ],
    )
    paths.append(path)

    path = data_dir / OBSERVATION_TSV
    write_tsv(
        path,
        observations,
        [
            "observation_key",
            "document_key",
            "ordinal",
            "observation_text",
            "raw_phrase_sha256",
            "unicode_character_count",
            "source_character_start",
            "source_character_end",
            "retained",
            "exclusion_reason",
            "basic_normalized_text",
            "normalized_text",
            "expression_key",
        ],
    )
    paths.append(path)

    path = data_dir / EXPRESSION_TSV
    write_tsv(
        path,
        expressions,
        [
            "expression_key",
            "language_tag_code",
            "expression_text",
            "basic_normalized_text",
            "normalized_text",
            "raw_variant_count",
            "occurrence_count",
        ],
    )
    paths.append(path)

    path = data_dir / STATISTIC_TSV
    write_tsv(
        path,
        statistics,
        [
            "frequency_key",
            "representative_expression_key",
            "representative_basic_normalized_text",
            "normalized_text",
            "expression_frequency",
            "document_frequency",
            "publisher_prevalence_count",
            "publisher_sample_count",
            "country_prevalence_count",
            "country_sample_count",
            "value_semantics",
        ],
    )
    paths.append(path)

    path = data_dir / COOCCURRENCE_TSV
    write_tsv(
        path,
        cooccurrences,
        [
            "pair_key",
            "subject_expression_key",
            "object_expression_key",
            "subject_basic_normalized_text",
            "object_basic_normalized_text",
            "subject_normalized_text",
            "object_normalized_text",
            "document_cooccurrence_count",
            "sample_count",
            "npmi",
            "subject_given_object_probability",
            "object_given_subject_probability",
            "subject_document_frequency",
            "object_document_frequency",
            "value_semantics",
        ],
    )
    paths.append(path)

    path = data_dir / DIAGNOSTIC_JSON
    path.write_text(
        json.dumps(diagnostics, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n",
        encoding="utf-8",
    )
    paths.append(path)
    return paths


def enrich_rights_rows(rows: Sequence[dict[str, str]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        policy_key = row["policy_key"]
        require(
            policy_key.startswith("source_policy."),
            f"rights policy key has an unsupported prefix: {policy_key}",
        )
        suffix = policy_key.removeprefix("source_policy.")
        evidence_urls = json.loads(row["evidence_urls"])
        decision = row["decision"]
        firstbloom = decision == "ALLOW_DERIVED_TERMS"
        unknown = decision == "UNKNOWN"
        manual_only = decision == "MANUAL_ONLY"

        if firstbloom:
            decision_code = "allow_derived_terms"
            robots_code = "not_applicable"
            terms_code = "not_applicable"
            access_method_code = "repository_fixture"
            copyright_code = "explicit_permission"
        elif decision == "BLOCKED":
            decision_code = "blocked"
            robots_code = (
                "allows"
                if "crawlable" in row["robots_status"].lower()
                or "accessible" in row["robots_status"].lower()
                else "unknown"
            )
            terms_code = "prohibits_automation"
            access_method_code = "manual_browser"
            copyright_code = "copyright_restricted"
        elif manual_only:
            decision_code = "manual_only"
            robots_code = (
                "allows"
                if "crawlable" in row["robots_status"].lower()
                or "accessible" in row["robots_status"].lower()
                else "unknown"
            )
            terms_code = "prohibits_reuse"
            access_method_code = "manual_browser"
            copyright_code = "copyright_restricted"
        else:
            decision_code = "unknown"
            robots_code = (
                "allows"
                if "crawlable" in row["robots_status"].lower()
                else "unknown"
            )
            terms_code = "unknown"
            access_method_code = "manual_browser"
            copyright_code = "unknown"

        review_context = {
            "review_country_code": row["country_code"] or None,
            "robots_status_observation": row["robots_status"],
            "terms_status_observation": row["terms_status"],
            "access_method_observation": row["access_method"],
            "copyright_status_observation": row["copyright_status"],
            "redistribution_status_observation": row[
                "redistribution_status"
            ],
            "commercial_use_status_observation": row[
                "commercial_use_status"
            ],
            "machine_access_status_observation": row[
                "machine_access_status"
            ],
            "matrix_source_blocked": row["source_blocked"] == "true",
            "matrix_raw_text_allowed": row["raw_text_allowed"] == "true",
            "matrix_production_export_allowed": (
                row["production_export_allowed"] == "true"
            ),
            "evidence_urls": evidence_urls,
            "review_note": row["notes"],
            "live_content_acquired": False,
        }
        enriched.append(
            {
                "policy_key": policy_key,
                "license_policy_key": f"license_policy.{suffix}",
                "source_key": f"source.corpus_rights.{suffix}",
                "source_version_key": f"source_version.corpus_rights.{suffix}",
                "source_name": row["source_name"],
                "creator": "Alex Caza" if firstbloom else None,
                "country_code": row["country_code"] or None,
                "domain": row["domain"],
                "source_url": evidence_urls[0],
                "version_locator": (
                    "https://github.com/alexcaza/firstbloom-data/tree/"
                    + PINNED_SOURCE_SHA
                    if firstbloom
                    else row["terms_url"]
                ),
                "version_label": (
                    PINNED_SOURCE_SHA
                    if firstbloom
                    else "rights-review-2026-08-24"
                ),
                "checked_on": CHECKED_AT,
                "evidence_urls": evidence_urls,
                "review_context": review_context,
                "license_access_class_code": "metadata_only",
                "license_rights_status_code": (
                    "unknown" if unknown else "verified"
                ),
                "license_redistributable": firstbloom,
                "license_derivative_work_allowed": firstbloom,
                "license_commercial_use_allowed": firstbloom,
                "license_machine_use_allowed": firstbloom,
                # The older licence-policy export flag implies raw-text
                # access.  Firstbloom's scoped grant is instead represented
                # by the 012 derived-terms redistribution permission.
                "license_production_export_allowed": False,
                "decision_code": decision_code,
                "robots_code": robots_code,
                "robots_locator": row["robots_url"],
                "terms_code": terms_code,
                "terms_locator": row["terms_url"],
                "access_method_code": access_method_code,
                "copyright_code": copyright_code,
                "document_metadata_allowed": firstbloom or manual_only,
                "raw_retention_allowed": False,
                "derived_terms_allowed": firstbloom,
                "derived_terms_redistribution_allowed": firstbloom,
                "raw_redistribution_allowed": False,
                "automated_acquisition_allowed": False,
                "commercial_use_implications": row[
                    "commercial_use_status"
                ],
                "review_notes": canonical_json(review_context),
            }
        )
    return enriched


def build_batch_rows(inventory: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_batch: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in inventory:
        by_batch[row["batch_number"]].append(row)
    batches: list[dict[str, Any]] = []
    for batch_number in range(1, MAX_BATCH + 1):
        rows = by_batch[batch_number]
        batch_receipt = [
            {
                "document_key": row["document_key"],
                "selection_sha256": row["selection_sha256"],
                "content_sha256": row["content_sha256"],
            }
            for row in rows
        ]
        batches.append(
            {
                "batch_key": (
                    f"batch.firstbloom_a6cb002_pilot_v1.{batch_number}"
                ),
                "batch_number": batch_number,
                "captured_from": CAPTURED_AT,
                "captured_until": CAPTURED_AT,
                "batch_inventory_sha256": sha256_text(
                    canonical_json(batch_receipt)
                ),
                "expected_document_count": len(rows),
                "notes": (
                    f"Cumulative staged sampling batch {batch_number}: select "
                    f"the {batch_number}th SHA-256-ranked eligible release for "
                    "each publisher with that many releases."
                ),
            }
        )
    require(sum(row["expected_document_count"] for row in batches) == EXPECTED_DOCUMENTS,
            "acquisition batch document counts changed")
    return batches


def build_diagnostic_rows(diagnostics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage in diagnostics["stages"]:
        batch_number = stage["batch_number"]
        prefix = f"diagnostic.{CORPUS_VERSION}.batch_{batch_number:02d}"
        cumulative_vocabulary = stage[
            "cumulative_unique_normalized_expression_count"
        ]
        rows.append(
            {
                "diagnostic_key": f"{prefix}.vocabulary_discovery_rate",
                "batch_key": f"batch.firstbloom_a6cb002_pilot_v1.{batch_number}",
                "diagnostic_code": "VOCABULARY_DISCOVERY_RATE",
                "measured_value": (
                    stage["new_normalized_expression_count"]
                    / cumulative_vocabulary
                ),
                "sample_count": stage["cumulative_retained_occurrence_count"],
                "value_semantics": (
                    "New retained normalized expressions in this batch divided "
                    "by cumulative retained normalized vocabulary size."
                ),
                "bootstrap_configuration": None,
                "context": {
                    "new_normalized_expression_count": stage[
                        "new_normalized_expression_count"
                    ],
                    "cumulative_unique_normalized_expression_count": cumulative_vocabulary,
                    "hapax_expression_count": stage["hapax_expression_count"],
                    "long_tail_discovery_complete": False,
                },
            }
        )

        baseline = batch_number == 1
        top_100_overlap = (
            100
            if baseline
            else stage["top_100_set_overlap_with_previous_batch"]
        )
        rows.append(
            {
                "diagnostic_key": f"{prefix}.high_frequency_rank_stability",
                "batch_key": f"batch.firstbloom_a6cb002_pilot_v1.{batch_number}",
                "diagnostic_code": "HIGH_FREQUENCY_RANK_STABILITY",
                "measured_value": top_100_overlap / 100,
                "sample_count": stage["cumulative_document_count"],
                "value_semantics": (
                    "Top-100 retained normalized-expression set overlap with "
                    "the previous cumulative batch; batch 1 is an explicit "
                    "self-baseline."
                ),
                "bootstrap_configuration": None,
                "context": {
                    "comparison_status": (
                        "baseline_self_reference"
                        if baseline
                        else "previous_cumulative_batch"
                    ),
                    "top_25_overlap": (
                        25
                        if baseline
                        else stage[
                            "top_25_set_overlap_with_previous_batch"
                        ]
                    ),
                    "top_25_denominator": 25,
                    "top_100_overlap": top_100_overlap,
                    "top_100_denominator": 100,
                    "rank_method": stage["rank_method"],
                },
            }
        )

        bootstrap = stage["bootstrap"]
        bootstrap_configuration = {
            key: value
            for key, value in bootstrap.items()
            if key
            not in {
                "median_jaccard",
                "mean_jaccard",
                "comparison_count",
            }
        }
        rows.append(
            {
                "diagnostic_key": f"{prefix}.cooccurrence_neighbour_stability",
                "batch_key": f"batch.firstbloom_a6cb002_pilot_v1.{batch_number}",
                "diagnostic_code": "COOCCURRENCE_NEIGHBOUR_STABILITY",
                "measured_value": bootstrap["median_jaccard"],
                "sample_count": bootstrap["comparison_count"],
                "value_semantics": (
                    "Median top-5 co-occurrence-neighbour Jaccard across "
                    "eligible expressions and 100 fixed-seed document "
                    "bootstrap replicates, compared with the full cumulative batch."
                ),
                "bootstrap_configuration": bootstrap_configuration,
                "context": {
                    "bootstrap_mean_jaccard": bootstrap["mean_jaccard"],
                    "bootstrap_median_jaccard": bootstrap["median_jaccard"],
                    "eligible_expression_count": bootstrap[
                        "eligible_expression_count"
                    ],
                    "consecutive_batch_top5_neighbour_median_jaccard": stage[
                        "consecutive_batch_top5_neighbour_median_jaccard"
                    ],
                    "consecutive_batch_neighbour_eligible_expression_count": stage[
                        "consecutive_batch_neighbour_eligible_expression_count"
                    ],
                    "consecutive_batch_metric_is_not_bootstrap": True,
                },
            }
        )

        rows.append(
            {
                "diagnostic_key": f"{prefix}.publisher_concentration",
                "batch_key": f"batch.firstbloom_a6cb002_pilot_v1.{batch_number}",
                "diagnostic_code": "PUBLISHER_CONCENTRATION",
                "measured_value": stage["publisher_document_hhi"],
                "sample_count": stage["cumulative_document_count"],
                "value_semantics": (
                    "Herfindahl-Hirschman index of captured-document share by "
                    "Firstbloom publisher in the cumulative batch."
                ),
                "bootstrap_configuration": None,
                "context": {
                    "publisher_max_document_share": stage[
                        "publisher_max_document_share"
                    ],
                    "cumulative_publisher_count": stage[
                        "cumulative_publisher_count"
                    ],
                },
            }
        )

        rows.append(
            {
                "diagnostic_key": f"{prefix}.geographic_concentration",
                "batch_key": f"batch.firstbloom_a6cb002_pilot_v1.{batch_number}",
                "diagnostic_code": "GEOGRAPHIC_CONCENTRATION",
                "measured_value": stage[
                    "coffee_origin_country_max_document_share"
                ],
                "sample_count": stage["cumulative_document_count"],
                "value_semantics": (
                    "Maximum cumulative document share for an explicit "
                    "Firstbloom coffee-origin country source code. This is not "
                    "roaster-country concentration."
                ),
                "bootstrap_configuration": None,
                "context": {
                    "coffee_origin_country_max_source_code": stage[
                        "coffee_origin_country_max_source_code"
                    ],
                    "coffee_origin_country_distinct_source_code_count": stage[
                        "coffee_origin_country_distinct_source_code_count"
                    ],
                    "coffee_origin_country_unknown_document_count": stage[
                        "coffee_origin_country_unknown_document_count"
                    ],
                    "coffee_origin_country_unknown_document_share": stage[
                        "coffee_origin_country_unknown_document_share"
                    ],
                    "roaster_country_concentration": None,
                    "roaster_country_concentration_status": stage[
                        "roaster_country_concentration_status"
                    ],
                    "origin_country_semantics": stage[
                        "origin_country_semantics"
                    ],
                },
            }
        )
    require(len(rows) == MAX_BATCH * 5, "diagnostic row count changed")
    return rows


def copy_text_value(value: Any) -> str:
    if value is None:
        return r"\N"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        value = canonical_json(value)
    elif isinstance(value, float):
        value = format(value, ".17g")
    else:
        value = str(value)
    return (
        value.replace("\\", "\\\\")
        .replace("\t", "\\t")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def copy_block(
    table_name: str,
    columns: Sequence[str],
    rows: Sequence[dict[str, Any]],
) -> str:
    lines = [
        f"COPY {table_name} ({', '.join(columns)}) FROM STDIN;"
    ]
    for row in rows:
        lines.append(
            "\t".join(copy_text_value(row.get(column)) for column in columns)
        )
    lines.append(r"\.")
    return "\n".join(lines)


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def statistic_configuration_contract() -> dict[str, Any]:
    return {
        "corpus_version": CORPUS_VERSION,
        "frequency_unit": "retained normalized phrase occurrence",
        "document_frequency_window": "captured_document",
        "publisher_prevalence_unit": "distinct Firstbloom publisher",
        "roaster_country_prevalence": "not_assessed_source_country_absent",
        "coffee_origin_country": "diagnostic_only_not_roaster_geography",
        "pair_window": "unique normalized expressions within captured_document",
        "pmi_logarithm": "natural",
        "npmi_formula": "PMI(x,y) / -ln(P(x,y))",
        "conditional_probability_orientation": (
            "subject_given_object=count(subject,object)/document_frequency(object)"
        ),
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_prng": "SHA-256 counter mode",
        "bootstrap_minimum_document_frequency": BOOTSTRAP_MIN_DOCUMENT_FREQUENCY,
        "bootstrap_neighbour_k": BOOTSTRAP_NEIGHBOUR_K,
        "interpretation": "language observation; not sensory similarity",
    }


def render_sql(
    *,
    rights_rows: Sequence[dict[str, Any]],
    publishers: Sequence[dict[str, Any]],
    products: Sequence[dict[str, Any]],
    batches: Sequence[dict[str, Any]],
    inventory: Sequence[dict[str, Any]],
    observations: Sequence[dict[str, Any]],
    expressions: Sequence[dict[str, Any]],
    statistics: Sequence[dict[str, Any]],
    cooccurrences: Sequence[dict[str, Any]],
    duplicate_reviews: Sequence[dict[str, Any]],
    diagnostic_rows: Sequence[dict[str, Any]],
    manifest: dict[str, Any],
    code_commit_sha: str,
    receipts: dict[str, str],
) -> str:
    firstbloom_right = next(
        row
        for row in rights_rows
        if row["policy_key"]
        == "source_policy.firstbloom.a6cb002.derived_terms"
    )
    inventory_sql_rows = [
        {**row, "document_ordinal": ordinal}
        for ordinal, row in enumerate(inventory, start=1)
    ]
    rules_sha256 = receipts["normalization_rules_sha256"]
    frame_sha256 = receipts["sampling_frame_sha256"]
    source_inventory_sha256 = receipts["source_inventory_sha256"]
    document_inventory_sha256 = receipts["document_inventory_sha256"]
    normalization_input_sha256 = receipts[
        "normalization_input_inventory_sha256"
    ]
    normalization_output_sha256 = receipts[
        "normalization_output_inventory_sha256"
    ]
    statistic_configuration_sha256 = receipts[
        "statistic_configuration_sha256"
    ]
    statistic_result_sha256 = receipts["statistic_result_inventory_sha256"]

    statistic_configuration = statistic_configuration_contract()
    require(
        sha256_text(canonical_json(statistic_configuration))
        == statistic_configuration_sha256,
        "statistic configuration hash changed during SQL rendering",
    )

    parts: list[str] = [
        "\\set ON_ERROR_STOP on",
        "",
        "-- Coffee Sensory Knowledge Base V0 -- Round 2B pilot seed.",
        "-- GENERATED by db/scripts/generate-round2b-pilot.py from the pinned",
        "-- Firstbloom checkout. Complete tasting-note strings, descriptions,",
        "-- consumer reviews, parsed fragments over 80 Unicode characters,",
        "-- and non-consensus review candidates are deliberately absent.",
        "-- Industry language is observational and not canonical truth.",
        "",
        "BEGIN;",
        "",
        "CREATE TEMP TABLE _r2b_rights_seed (",
        "    policy_key TEXT, license_policy_key TEXT, source_key TEXT,",
        "    source_version_key TEXT, source_name TEXT, creator TEXT,",
        "    country_code TEXT, domain TEXT, source_url TEXT,",
        "    version_locator TEXT, version_label TEXT, checked_on DATE,",
        "    evidence_urls JSONB, review_context JSONB,",
        "    license_access_class_code TEXT, license_rights_status_code TEXT,",
        "    license_redistributable BOOLEAN,",
        "    license_derivative_work_allowed BOOLEAN,",
        "    license_commercial_use_allowed BOOLEAN,",
        "    license_machine_use_allowed BOOLEAN,",
        "    license_production_export_allowed BOOLEAN,",
        "    decision_code TEXT, robots_code TEXT, robots_locator TEXT,",
        "    terms_code TEXT, terms_locator TEXT, access_method_code TEXT,",
        "    copyright_code TEXT, document_metadata_allowed BOOLEAN,",
        "    raw_retention_allowed BOOLEAN, derived_terms_allowed BOOLEAN,",
        "    derived_terms_redistribution_allowed BOOLEAN,",
        "    raw_redistribution_allowed BOOLEAN,",
        "    automated_acquisition_allowed BOOLEAN,",
        "    commercial_use_implications TEXT, review_notes TEXT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_rights_seed",
            [
                "policy_key", "license_policy_key", "source_key",
                "source_version_key", "source_name", "creator",
                "country_code", "domain", "source_url", "version_locator",
                "version_label", "checked_on", "evidence_urls",
                "review_context", "license_access_class_code",
                "license_rights_status_code", "license_redistributable",
                "license_derivative_work_allowed",
                "license_commercial_use_allowed",
                "license_machine_use_allowed",
                "license_production_export_allowed", "decision_code",
                "robots_code", "robots_locator", "terms_code",
                "terms_locator", "access_method_code", "copyright_code",
                "document_metadata_allowed", "raw_retention_allowed",
                "derived_terms_allowed",
                "derived_terms_redistribution_allowed",
                "raw_redistribution_allowed", "automated_acquisition_allowed",
                "commercial_use_implications", "review_notes",
            ],
            rights_rows,
        ),
        "",
        "CREATE TEMP TABLE _r2b_publisher_seed (",
        "    publisher_key TEXT, source_policy_key TEXT,",
        "    external_publisher_key TEXT, name TEXT, domain TEXT,",
        "    roaster_country_code TEXT, metadata JSONB",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_publisher_seed",
            [
                "publisher_key", "source_policy_key",
                "external_publisher_key", "name", "domain",
                "roaster_country_code", "metadata",
            ],
            publishers,
        ),
        "",
        "CREATE TEMP TABLE _r2b_product_seed (",
        "    product_key TEXT, publisher_key TEXT, external_product_key TEXT,",
        "    product_name TEXT, coffee_origin_country_codes JSONB,",
        "    coffee_regions JSONB, producer_names JSONB, variety_names JSONB,",
        "    process_names JSONB, notes JSONB",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_product_seed",
            [
                "product_key", "publisher_key", "external_product_key",
                "product_name", "coffee_origin_country_codes",
                "coffee_regions", "producer_names", "variety_names",
                "process_names", "notes",
            ],
            products,
        ),
        "",
        "CREATE TEMP TABLE _r2b_batch_seed (",
        "    batch_key TEXT, batch_number INTEGER, captured_from TIMESTAMPTZ,",
        "    captured_until TIMESTAMPTZ, batch_inventory_sha256 TEXT,",
        "    expected_document_count BIGINT, notes TEXT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_batch_seed",
            [
                "batch_key", "batch_number", "captured_from",
                "captured_until", "batch_inventory_sha256",
                "expected_document_count", "notes",
            ],
            batches,
        ),
        "",
        "CREATE TEMP TABLE _r2b_document_seed (",
        "    document_ordinal INTEGER, product_key TEXT, document_key TEXT,",
        "    publisher_key TEXT, source_policy_key TEXT, batch_key TEXT,",
        "    external_product_key TEXT, external_release_key TEXT,",
        "    product_name TEXT, listing_date DATE, roast_date DATE,",
        "    captured_at TIMESTAMPTZ, canonical_url TEXT, content_sha256 TEXT,",
        "    raw_text_sha256 TEXT, metadata_composite_sha256 TEXT,",
        "    selection_sha256 TEXT, batch_number INTEGER,",
        "    raw_observation_count INTEGER, retained_observation_count INTEGER,",
        "    redacted_observation_count INTEGER,",
        "    coffee_origin_country_codes JSONB, coffee_regions JSONB,",
        "    producer_names JSONB, farm_names JSONB, variety_names JSONB,",
        "    process_names JSONB, metadata JSONB",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_document_seed",
            [
                "document_ordinal", "product_key", "document_key",
                "publisher_key", "source_policy_key", "batch_key",
                "external_product_key", "external_release_key", "product_name",
                "listing_date", "roast_date", "captured_at", "canonical_url",
                "content_sha256", "raw_text_sha256",
                "metadata_composite_sha256", "selection_sha256",
                "batch_number", "raw_observation_count",
                "retained_observation_count", "redacted_observation_count",
                "coffee_origin_country_codes", "coffee_regions",
                "producer_names", "farm_names", "variety_names",
                "process_names", "metadata",
            ],
            inventory_sql_rows,
        ),
        "",
        "CREATE TEMP TABLE _r2b_observation_seed (",
        "    observation_key TEXT, document_key TEXT, ordinal INTEGER,",
        "    observation_text TEXT, raw_phrase_sha256 TEXT,",
        "    unicode_character_count INTEGER, source_character_start INTEGER,",
        "    source_character_end INTEGER, retained BOOLEAN,",
        "    exclusion_reason TEXT, basic_normalized_text TEXT,",
        "    normalized_text TEXT, expression_key TEXT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_observation_seed",
            [
                "observation_key", "document_key", "ordinal",
                "observation_text", "raw_phrase_sha256",
                "unicode_character_count", "source_character_start",
                "source_character_end", "retained", "exclusion_reason",
                "basic_normalized_text", "normalized_text", "expression_key",
            ],
            observations,
        ),
        "",
        "CREATE TEMP TABLE _r2b_expression_seed (",
        "    expression_key TEXT, language_tag_code TEXT, expression_text TEXT,",
        "    basic_normalized_text TEXT, normalized_text TEXT,",
        "    raw_variant_count INTEGER, occurrence_count BIGINT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_expression_seed",
            [
                "expression_key", "language_tag_code", "expression_text",
                "basic_normalized_text", "normalized_text",
                "raw_variant_count", "occurrence_count",
            ],
            expressions,
        ),
        "",
        "CREATE TEMP TABLE _r2b_frequency_seed (",
        "    frequency_key TEXT, representative_expression_key TEXT,",
        "    representative_basic_normalized_text TEXT, normalized_text TEXT,",
        "    expression_frequency BIGINT, document_frequency BIGINT,",
        "    publisher_prevalence_count BIGINT, publisher_sample_count BIGINT,",
        "    country_prevalence_count BIGINT, country_sample_count BIGINT,",
        "    value_semantics TEXT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_frequency_seed",
            [
                "frequency_key", "representative_expression_key",
                "representative_basic_normalized_text", "normalized_text",
                "expression_frequency", "document_frequency",
                "publisher_prevalence_count", "publisher_sample_count",
                "country_prevalence_count", "country_sample_count",
                "value_semantics",
            ],
            statistics,
        ),
        "",
        "CREATE TEMP TABLE _r2b_pair_seed (",
        "    pair_key TEXT, subject_expression_key TEXT,",
        "    object_expression_key TEXT, subject_basic_normalized_text TEXT,",
        "    object_basic_normalized_text TEXT, subject_normalized_text TEXT,",
        "    object_normalized_text TEXT, document_cooccurrence_count BIGINT,",
        "    sample_count BIGINT, npmi NUMERIC,",
        "    subject_given_object_probability NUMERIC,",
        "    object_given_subject_probability NUMERIC,",
        "    subject_document_frequency BIGINT,",
        "    object_document_frequency BIGINT, value_semantics TEXT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_pair_seed",
            [
                "pair_key", "subject_expression_key", "object_expression_key",
                "subject_basic_normalized_text",
                "object_basic_normalized_text", "subject_normalized_text",
                "object_normalized_text", "document_cooccurrence_count",
                "sample_count", "npmi", "subject_given_object_probability",
                "object_given_subject_probability",
                "subject_document_frequency", "object_document_frequency",
                "value_semantics",
            ],
            cooccurrences,
        ),
        "",
        "CREATE TEMP TABLE _r2b_duplicate_seed (",
        "    duplicate_review_key TEXT, earlier_document_key TEXT,",
        "    later_document_key TEXT, duplicate_match_basis_code TEXT,",
        "    duplicate_review_decision_code TEXT, reviewed_at TIMESTAMPTZ,",
        "    rationale TEXT",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_duplicate_seed",
            [
                "duplicate_review_key", "earlier_document_key",
                "later_document_key", "duplicate_match_basis_code",
                "duplicate_review_decision_code", "reviewed_at", "rationale",
            ],
            duplicate_reviews,
        ),
        "",
        "CREATE TEMP TABLE _r2b_diagnostic_seed (",
        "    diagnostic_key TEXT, batch_key TEXT, diagnostic_code TEXT,",
        "    measured_value NUMERIC, sample_count BIGINT, value_semantics TEXT,",
        "    bootstrap_configuration JSONB, context JSONB",
        ") ON COMMIT DROP;",
        copy_block(
            "_r2b_diagnostic_seed",
            [
                "diagnostic_key", "batch_key", "diagnostic_code",
                "measured_value", "sample_count", "value_semantics",
                "bootstrap_configuration", "context",
            ],
            diagnostic_rows,
        ),
        "",
    ]

    manifest_metadata = {
        "source": manifest["source"],
        "source_url": manifest["source_url"],
        "pinned_git_sha": manifest["pinned_git_sha"],
        "input_files": manifest["input_files"],
        "rights_boundary": manifest["rights_boundary"],
        "source_baseline_sha": SOURCE_BASELINE_SHA,
        "code_commit_sha": code_commit_sha,
        "generator_sha256": receipts["generator_sha256"],
        "expression_admission_review": {
            "policy_version": REVIEW_POLICY_VERSION,
            "inventory_sha256": receipts["admission_review_sha256"],
            "metadata_sha256": receipts[
                "admission_review_metadata_sha256"
            ],
            "human_review": False,
            "automated_language_detection": False,
        },
    }
    parts.extend(
        [
            "INSERT INTO evidence.license_policy (",
            "    license_policy_key, access_class_code, rights_status_code,",
            "    redistributable, derivative_work_allowed, commercial_use_allowed,",
            "    machine_use_allowed, production_export_allowed, checked_on, notes",
            ")",
            "SELECT license_policy_key, license_access_class_code,",
            "       license_rights_status_code, license_redistributable,",
            "       license_derivative_work_allowed,",
            "       license_commercial_use_allowed, license_machine_use_allowed,",
            "       license_production_export_allowed, checked_on, review_notes",
            "FROM _r2b_rights_seed ORDER BY policy_key;",
            "",
            "INSERT INTO evidence.source (",
            "    source_key, title, creator, publisher, citation, doi,",
            "    source_url, external_metadata",
            ")",
            "SELECT source_key, source_name, creator, NULL,",
            "       source_name || ' rights and access review checked ' || checked_on::TEXT || '.',",
            "       NULL, source_url, review_context",
            "FROM _r2b_rights_seed ORDER BY policy_key;",
            "",
            "INSERT INTO evidence.source_version (",
            "    source_version_key, source_id, license_policy_id, version_label,",
            "    published_on, retrieved_on, version_locator, external_metadata",
            ")",
            "SELECT seed.source_version_key, source.source_id, policy.license_policy_id,",
            "       seed.version_label, NULL, seed.checked_on, seed.version_locator,",
            "       seed.review_context",
            "FROM _r2b_rights_seed AS seed",
            "JOIN evidence.source AS source ON source.source_key = seed.source_key",
            "JOIN evidence.license_policy AS policy",
            "  ON policy.license_policy_key = seed.license_policy_key",
            "ORDER BY seed.policy_key;",
            "",
            "INSERT INTO corpus.source_policy_review (",
            "    source_policy_review_key, source_version_id, license_policy_id,",
            "    domain, corpus_source_decision_code, robots_status_code,",
            "    robots_locator, terms_status_code, terms_locator,",
            "    corpus_access_method_code, copyright_status_code,",
            "    document_metadata_allowed, raw_retention_allowed,",
            "    derived_terms_allowed, derived_terms_redistribution_allowed,",
            "    raw_redistribution_allowed, automated_acquisition_allowed,",
            "    commercial_use_implications, checked_at, notes",
            ")",
            "SELECT seed.policy_key, version.source_version_id, policy.license_policy_id,",
            "       seed.domain, seed.decision_code, seed.robots_code,",
            "       seed.robots_locator, seed.terms_code, seed.terms_locator,",
            "       seed.access_method_code, seed.copyright_code,",
            "       seed.document_metadata_allowed, seed.raw_retention_allowed,",
            "       seed.derived_terms_allowed,",
            "       seed.derived_terms_redistribution_allowed,",
            "       seed.raw_redistribution_allowed,",
            "       seed.automated_acquisition_allowed,",
            "       seed.commercial_use_implications,",
            "       seed.checked_on::TIMESTAMP AT TIME ZONE 'UTC', seed.review_notes",
            "FROM _r2b_rights_seed AS seed",
            "JOIN evidence.source_version AS version",
            "  ON version.source_version_key = seed.source_version_key",
            "JOIN evidence.license_policy AS policy",
            "  ON policy.license_policy_key = seed.license_policy_key",
            "ORDER BY seed.policy_key;",
            "",
            "INSERT INTO evidence.dataset (",
            "    dataset_key, source_version_id, name, description, external_metadata",
            ")",
            "SELECT 'dataset.firstbloom_a6cb002_pilot_v1',",
            "       version.source_version_id,",
            "       'Firstbloom rights-bounded industry-language pilot v1',",
            "       'Deterministic derived-term pilot: full tasting notes, long descriptions, and consumer reviews are absent.',",
            f"       {sql_literal(canonical_json(manifest_metadata))}::JSONB",
            "FROM evidence.source_version AS version",
            f"WHERE version.source_version_key = {sql_literal(firstbloom_right['source_version_key'])};",
            "",
            "INSERT INTO evidence.statistical_method (method_key, name, description)",
            "VALUES (",
            "    'method.round2b.document_language_observation_v1',",
            "    'Round 2B document language-observation statistics v1',",
            "    'Occurrence/document/publisher frequencies, document-window co-occurrence, natural-log NPMI, conditional co-occurrence, and fixed-seed document bootstrap diagnostics; no statistic asserts sensory validity or similarity.'",
            ");",
            "",
            "INSERT INTO corpus.industry_publisher (",
            "    industry_publisher_key, source_policy_review_id,",
            "    external_publisher_key, publisher_name, domain,",
            "    roaster_country_code, notes",
            ")",
            "SELECT seed.publisher_key, policy.source_policy_review_id,",
            "       seed.external_publisher_key, seed.name, seed.domain,",
            "       seed.roaster_country_code, seed.metadata::TEXT",
            "FROM _r2b_publisher_seed AS seed",
            "JOIN corpus.source_policy_review AS policy",
            "  ON policy.source_policy_review_key = seed.source_policy_key",
            "ORDER BY seed.external_publisher_key::BIGINT;",
            "",
            "INSERT INTO corpus.industry_product (",
            "    industry_product_key, industry_publisher_id, external_product_key,",
            "    product_name, coffee_origin_countries, coffee_regions,",
            "    producer_names, variety_names, process_names, notes",
            ")",
            "SELECT seed.product_key, publisher.industry_publisher_id,",
            "       seed.external_product_key, seed.product_name,",
            "       seed.coffee_origin_country_codes, seed.coffee_regions,",
            "       seed.producer_names, seed.variety_names, seed.process_names,",
            "       seed.notes::TEXT",
            "FROM _r2b_product_seed AS seed",
            "JOIN corpus.industry_publisher AS publisher",
            "  ON publisher.industry_publisher_key = seed.publisher_key",
            "ORDER BY seed.external_product_key::BIGINT;",
            "",
            "INSERT INTO corpus.sampling_frame (",
            "    sampling_frame_key, name, language_tag_code, frame_sha256,",
            "    created_at, description, representativeness_note",
            ") VALUES (",
            "    'sampling_frame.firstbloom_a6cb002_pilot_v1',",
            "    'Firstbloom deterministic publisher-balanced pilot frame v1',",
            "    'en',",
            f"    {sql_literal(frame_sha256)},",
            f"    {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ,",
            "    'All Firstbloom publishers with at least one nonempty roaster tasting-note release; each batch selects the next deterministic SHA-256-ranked release per publisher.',",
            "    'Historical English-language repository pilot. It is broad across publishers and coffee origins but is not a globally representative live-roaster sample; roaster country and size are not source asserted.'",
            ");",
            "",
            "INSERT INTO corpus.sampling_frame_member (",
            "    sampling_frame_id, industry_publisher_id, source_policy_review_id,",
            "    selected, roaster_size_stratum, process_focus_stratum,",
            "    offering_period_stratum, selection_rationale",
            ")",
            "SELECT frame.sampling_frame_id, publisher.industry_publisher_id,",
            "       policy.source_policy_review_id, TRUE, NULL, NULL,",
            "       'historical_repository_snapshot',",
            "       'Eligible publisher with at least one explicit nonempty Firstbloom roaster tasting-note release; no country, size, or process stratum was inferred.'",
            "FROM _r2b_publisher_seed AS seed",
            "JOIN corpus.industry_publisher AS publisher",
            "  ON publisher.industry_publisher_key = seed.publisher_key",
            "JOIN corpus.source_policy_review AS policy",
            "  ON policy.source_policy_review_key = seed.source_policy_key",
            "CROSS JOIN corpus.sampling_frame AS frame",
            "WHERE frame.sampling_frame_key = 'sampling_frame.firstbloom_a6cb002_pilot_v1'",
            "ORDER BY seed.external_publisher_key::BIGINT;",
            "",
            "INSERT INTO corpus.normalization_pipeline (",
            "    normalization_pipeline_key, version_label, language_tag_code,",
            "    unicode_form, rules_sha256, code_commit_sha, parser_version,",
            "    description, created_at, frozen_at",
            ") VALUES (",
            f"    {sql_literal(PIPELINE_KEY)}, '1', 'en', 'NFC',",
            f"    {sql_literal(rules_sha256)}, {sql_literal(code_commit_sha)},",
            f"    {sql_literal(GENERATOR_VERSION)},",
            "    'NFC, explicit conservative punctuation translation, Unicode lower-case under the recorded PostgreSQL cluster collation, whitespace collapse, and three ordered whole-phrase orthographic rules. No stemming or semantic collapse.',",
            f"    {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ, NULL",
            ");",
            "",
            "INSERT INTO corpus.normalization_rule (",
            "    normalization_rule_key, normalization_pipeline_id, rule_order,",
            "    rule_kind, input_normalized_text, output_normalized_text, description",
            ")",
            "SELECT 'normalization_rule.en_v1.' || rule.rule_order::TEXT,",
            "       pipeline.normalization_pipeline_id, rule.rule_order,",
            "       'WHOLE_PHRASE', rule.input_text, rule.output_text,",
            "       'Curated exact whole-phrase orthographic variant; no substring replacement.'",
            "FROM (VALUES",
            "    (10::SMALLINT, 'earl gray'::TEXT, 'earl grey'::TEXT),",
            "    (20::SMALLINT, 'earl gray tea'::TEXT, 'earl grey tea'::TEXT),",
            "    (30::SMALLINT, 'black currant'::TEXT, 'blackcurrant'::TEXT)",
            ") AS rule(rule_order, input_text, output_text)",
            "CROSS JOIN corpus.normalization_pipeline AS pipeline",
            f"WHERE pipeline.normalization_pipeline_key = {sql_literal(PIPELINE_KEY)}",
            "ORDER BY rule.rule_order;",
            "",
            "UPDATE corpus.normalization_pipeline",
            f"SET frozen_at = {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ",
            f"WHERE normalization_pipeline_key = {sql_literal(PIPELINE_KEY)};",
            "",
            "INSERT INTO corpus.corpus (",
            "    corpus_key, name, language_tag_code, description, capture_metadata",
            ") VALUES (",
            f"    {sql_literal(CORPUS_KEY)},",
            "    'Firstbloom specialty-coffee industry-language pilot v1',",
            "    'en',",
            "    'Rights-reviewed historical industry tasting-language observations. Roaster language is observational and is not canonical sensory truth.',",
            f"    {sql_literal(canonical_json({'corpus_version': CORPUS_VERSION, 'raw_text_stored': False, 'source_baseline_sha': SOURCE_BASELINE_SHA, 'code_commit_sha': code_commit_sha, 'rights_boundary': 'ALLOW_DERIVED_TERMS', 'expression_admission_policy': REVIEW_POLICY_VERSION, 'expression_admission_review_sha256': receipts['admission_review_sha256'], 'human_review': False, 'automated_language_detection': False}))}::JSONB",
            ");",
            "",
            "INSERT INTO corpus.corpus_snapshot (",
            "    corpus_snapshot_key, corpus_id, corpus_version, manifest_dataset_id,",
            "    sampling_frame_id, normalization_pipeline_id,",
            "    capture_window_start, capture_window_end,",
            "    source_inventory_sha256, document_inventory_sha256,",
            "    code_commit_sha, expected_document_count,",
            "    expected_observation_count, expected_normalized_expression_count,",
            "    raw_public_reproducibility_complete, reproducibility_boundary, frozen_at",
            ")",
            f"SELECT {sql_literal(SNAPSHOT_KEY)}, corpus.corpus_id,",
            f"       {sql_literal(CORPUS_VERSION)}, dataset.dataset_id,",
            "       frame.sampling_frame_id, pipeline.normalization_pipeline_id,",
            f"       {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ,",
            f"       {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ,",
            f"       {sql_literal(source_inventory_sha256)},",
            f"       {sql_literal(document_inventory_sha256)},",
            f"       {sql_literal(code_commit_sha)},",
            f"       {EXPECTED_DOCUMENTS}, {EXPECTED_RAW_OBSERVATIONS},",
            f"       {EXPECTED_NORMALIZED_EXPRESSIONS}, FALSE,",
            "       'Public rebuild requires the separately obtained pinned CC BY 4.0 Firstbloom checkout. The repository stores source hashes, explicit metadata, and only short partial phrases admitted by two independent Codex-assisted project-curation passes; every other fragment is hash-only. Complete tasting notes, descriptions, and consumer reviews are excluded.',",
            "       NULL",
            "FROM corpus.corpus AS corpus",
            "CROSS JOIN evidence.dataset AS dataset",
            "CROSS JOIN corpus.sampling_frame AS frame",
            "CROSS JOIN corpus.normalization_pipeline AS pipeline",
            f"WHERE corpus.corpus_key = {sql_literal(CORPUS_KEY)}",
            "  AND dataset.dataset_key = 'dataset.firstbloom_a6cb002_pilot_v1'",
            "  AND frame.sampling_frame_key = 'sampling_frame.firstbloom_a6cb002_pilot_v1'",
            f"  AND pipeline.normalization_pipeline_key = {sql_literal(PIPELINE_KEY)};",
            "",
        ]
    )
    normalization_configuration = {
        "pipeline_key": PIPELINE_KEY,
        "normalization_rules_sha256": rules_sha256,
        "input_retention_codes": ["derived_phrase"],
        "excluded_retention_codes": ["hash_only"],
        "source_offset_unit": "UNICODE_CODE_POINT",
        "source_offsets": "0-based half-open in hashed complete source field",
        "raw_document_text_stored": False,
    }
    parts.extend(
        [
            "INSERT INTO corpus.corpus_snapshot_source (",
            "    corpus_snapshot_id, industry_publisher_id,",
            "    source_policy_review_id, source_ordinal, sampling_stratum,",
            "    inclusion_note",
            ")",
            "SELECT snapshot.corpus_snapshot_id, publisher.industry_publisher_id,",
            "       policy.source_policy_review_id,",
            "       row_number() OVER (ORDER BY seed.external_publisher_key::BIGINT)::INTEGER,",
            "       'publisher_balanced_historical_repository_pilot',",
            "       'Firstbloom publisher selected under one shared pinned-repository CC BY 4.0 policy; roaster country and size were not inferred.'",
            "FROM _r2b_publisher_seed AS seed",
            "JOIN corpus.industry_publisher AS publisher",
            "  ON publisher.industry_publisher_key = seed.publisher_key",
            "JOIN corpus.source_policy_review AS policy",
            "  ON policy.source_policy_review_key = seed.source_policy_key",
            "CROSS JOIN corpus.corpus_snapshot AS snapshot",
            f"WHERE snapshot.corpus_snapshot_key = {sql_literal(SNAPSHOT_KEY)}",
            "ORDER BY seed.external_publisher_key::BIGINT;",
            "",
            "INSERT INTO corpus.acquisition_batch (",
            "    acquisition_batch_key, corpus_snapshot_id, batch_ordinal,",
            "    captured_from, captured_until, batch_inventory_sha256,",
            "    expected_document_count, notes",
            ")",
            "SELECT seed.batch_key, snapshot.corpus_snapshot_id,",
            "       seed.batch_number, seed.captured_from, seed.captured_until,",
            "       seed.batch_inventory_sha256, seed.expected_document_count,",
            "       seed.notes",
            "FROM _r2b_batch_seed AS seed",
            "CROSS JOIN corpus.corpus_snapshot AS snapshot",
            f"WHERE snapshot.corpus_snapshot_key = {sql_literal(SNAPSHOT_KEY)}",
            "ORDER BY seed.batch_number;",
            "",
            "INSERT INTO corpus.captured_document (",
            "    captured_document_key, corpus_id, source_version_id,",
            "    external_document_key, captured_at, raw_text, capture_metadata,",
            "    industry_product_id, source_policy_review_id,",
            "    acquisition_batch_id, canonical_url, content_sha256,",
            "    raw_text_sha256, metadata_composite_sha256,",
            "    listing_observed_on, roast_date",
            ")",
            "SELECT seed.document_key, corpus.corpus_id, version.source_version_id,",
            "       seed.external_release_key, seed.captured_at, NULL,",
            "       seed.metadata || jsonb_build_object(",
            "           'selection_sha256', seed.selection_sha256,",
            "           'source_external_product_key', seed.external_product_key,",
            "           'raw_observation_count', seed.raw_observation_count,",
            "           'retained_observation_count', seed.retained_observation_count,",
            "           'redacted_observation_count', seed.redacted_observation_count",
            "       ),",
            "       product.industry_product_id, policy.source_policy_review_id,",
            "       batch.acquisition_batch_id, seed.canonical_url,",
            "       seed.content_sha256, seed.raw_text_sha256,",
            "       seed.metadata_composite_sha256, seed.listing_date, seed.roast_date",
            "FROM _r2b_document_seed AS seed",
            "JOIN corpus.corpus AS corpus",
            f"  ON corpus.corpus_key = {sql_literal(CORPUS_KEY)}",
            "JOIN corpus.industry_product AS product",
            "  ON product.industry_product_key = seed.product_key",
            "JOIN corpus.source_policy_review AS policy",
            "  ON policy.source_policy_review_key = seed.source_policy_key",
            "JOIN evidence.source_version AS version",
            "  ON version.source_version_id = policy.source_version_id",
            "JOIN corpus.acquisition_batch AS batch",
            "  ON batch.acquisition_batch_key = seed.batch_key",
            "ORDER BY seed.document_ordinal;",
            "",
            "INSERT INTO corpus.raw_observation (",
            "    raw_observation_key, captured_document_id, observation_text,",
            "    character_start, character_end, observation_metadata,",
            "    observation_sha256, character_count, observation_retention_code",
            ")",
            "SELECT seed.observation_key, document.captured_document_id,",
            "       seed.observation_text, seed.source_character_start,",
            "       seed.source_character_end, jsonb_build_object(",
            "           'parser_version', 'round2b-delimiter-parser-v1',",
            "           'source_phrase_ordinal', seed.ordinal,",
            "           'source_offset_unit', 'UNICODE_CODE_POINT',",
            "           'source_offset_semantics', '0-based half-open in hashed complete source field',",
            "           'exclusion_reason', seed.exclusion_reason,",
            "           'complete_note_string_stored', FALSE",
            "       ), seed.raw_phrase_sha256, seed.unicode_character_count,",
            "       CASE WHEN seed.retained THEN 'derived_phrase' ELSE 'hash_only' END",
            "FROM _r2b_observation_seed AS seed",
            "JOIN corpus.captured_document AS document",
            "  ON document.captured_document_key = seed.document_key",
            "ORDER BY document.captured_document_id, seed.ordinal;",
            "",
            "INSERT INTO kb.lexical_expression (",
            "    expression_key, language_tag_code, expression_text,",
            "    lifecycle_status_code",
            ")",
            "SELECT seed.expression_key, seed.language_tag_code,",
            "       seed.expression_text, 'candidate'",
            "FROM _r2b_expression_seed AS seed",
            "ORDER BY seed.basic_normalized_text",
            "ON CONFLICT (language_tag_code, normalized_text) DO NOTHING;",
            "",
            "INSERT INTO corpus.observation_expression (",
            "    observation_expression_key, raw_observation_id, expression_id,",
            "    occurrence_ordinal",
            ")",
            "SELECT 'observation_expression.' || seed.observation_key,",
            "       observation.raw_observation_id, expression.expression_id, 1",
            "FROM _r2b_observation_seed AS seed",
            "JOIN corpus.raw_observation AS observation",
            "  ON observation.raw_observation_key = seed.observation_key",
            "JOIN kb.lexical_expression AS expression",
            "  ON expression.language_tag_code = 'en'",
            " AND expression.normalized_text = seed.basic_normalized_text",
            "WHERE seed.retained",
            "ORDER BY observation.raw_observation_id;",
            "",
            "-- Populate one v1 identity and deterministic mapping for every",
            "-- English lexical expression available to retrieval, canonical or",
            "-- observed, before the snapshot closes the dictionary.",
            "WITH normalized_surface AS (",
            "    SELECT DISTINCT corpus.normalize_expression_v1(",
            f"               expression.expression_text, {sql_literal(PIPELINE_KEY)}",
            "           ) AS normalized_text",
            "    FROM kb.lexical_expression AS expression",
            "    WHERE expression.language_tag_code = 'en'",
            ")",
            "INSERT INTO corpus.normalized_expression (",
            "    normalized_expression_key, normalization_pipeline_id,",
            "    normalized_text, created_at",
            ")",
            "SELECT 'normalized_expression.en_v1.sha256_' ||",
            "       encode(sha256(convert_to(surface.normalized_text, 'UTF8')), 'hex'),",
            "       pipeline.normalization_pipeline_id, surface.normalized_text,",
            f"       {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ",
            "FROM normalized_surface AS surface",
            "CROSS JOIN corpus.normalization_pipeline AS pipeline",
            f"WHERE pipeline.normalization_pipeline_key = {sql_literal(PIPELINE_KEY)}",
            "ORDER BY surface.normalized_text;",
            "",
            "INSERT INTO corpus.lexical_expression_normalization (",
            "    lexical_expression_normalization_key, expression_id,",
            "    normalization_pipeline_id, normalized_expression_id,",
            "    surface_sha256, derived_at",
            ")",
            "SELECT 'lexical_expression_normalization.en_v1.sha256_' ||",
            "       encode(sha256(convert_to(expression.expression_key, 'UTF8')), 'hex'),",
            "       expression.expression_id, pipeline.normalization_pipeline_id,",
            "       normalized.normalized_expression_id,",
            "       encode(sha256(convert_to(expression.expression_text, 'UTF8')), 'hex'),",
            f"       {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ",
            "FROM kb.lexical_expression AS expression",
            "CROSS JOIN corpus.normalization_pipeline AS pipeline",
            "JOIN corpus.normalized_expression AS normalized",
            "  ON normalized.normalization_pipeline_id = pipeline.normalization_pipeline_id",
            " AND normalized.normalized_text = corpus.normalize_expression_v1(",
            f"         expression.expression_text, {sql_literal(PIPELINE_KEY)}",
            "     )",
            "WHERE expression.language_tag_code = 'en'",
            f"  AND pipeline.normalization_pipeline_key = {sql_literal(PIPELINE_KEY)}",
            "ORDER BY expression.expression_id;",
            "",
            "INSERT INTO corpus.document_duplicate_review (",
            "    document_duplicate_review_key, earlier_document_id,",
            "    later_document_id, duplicate_match_basis_code,",
            "    duplicate_review_decision_code, reviewed_at, rationale",
            ")",
            "SELECT seed.duplicate_review_key,",
            "       least(left_document.captured_document_id, right_document.captured_document_id),",
            "       greatest(left_document.captured_document_id, right_document.captured_document_id),",
            "       seed.duplicate_match_basis_code,",
            "       seed.duplicate_review_decision_code, seed.reviewed_at,",
            "       seed.rationale",
            "FROM _r2b_duplicate_seed AS seed",
            "JOIN corpus.captured_document AS left_document",
            "  ON left_document.captured_document_key = seed.earlier_document_key",
            "JOIN corpus.captured_document AS right_document",
            "  ON right_document.captured_document_key = seed.later_document_key",
            "ORDER BY least(left_document.captured_document_id, right_document.captured_document_id),",
            "         greatest(left_document.captured_document_id, right_document.captured_document_id);",
            "",
            "UPDATE corpus.corpus_snapshot",
            f"SET frozen_at = {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ",
            f"WHERE corpus_snapshot_key = {sql_literal(SNAPSHOT_KEY)};",
            "",
            "INSERT INTO corpus.normalization_derivation_run (",
            "    normalization_derivation_run_key, corpus_snapshot_id,",
            "    normalization_pipeline_id, version_label, code_commit_sha,",
            "    input_inventory_sha256, output_inventory_sha256, started_at,",
            "    completed_at, frozen_at, input_observation_count,",
            "    output_occurrence_count, configuration, notes",
            ")",
            "SELECT 'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1',",
            "       snapshot.corpus_snapshot_id, pipeline.normalization_pipeline_id,",
            f"       '1', {sql_literal(code_commit_sha)},",
            f"       {sql_literal(normalization_input_sha256)}, NULL,",
            f"       {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ, NULL, NULL,",
            f"       {EXPECTED_RAW_OBSERVATIONS}, NULL,",
            f"       {sql_literal(canonical_json(normalization_configuration))}::JSONB,",
            "       'Hash-only fragments remain part of the input receipt but cannot produce a normalized occurrence.'",
            "FROM corpus.corpus_snapshot AS snapshot",
            "JOIN corpus.normalization_pipeline AS pipeline",
            "  ON pipeline.normalization_pipeline_id = snapshot.normalization_pipeline_id",
            f"WHERE snapshot.corpus_snapshot_key = {sql_literal(SNAPSHOT_KEY)};",
            "",
            "INSERT INTO corpus.normalized_expression_occurrence (",
            "    normalized_expression_occurrence_key,",
            "    normalization_derivation_run_id, normalization_pipeline_id,",
            "    observation_expression_id, normalized_expression_id,",
            "    source_observation_sha256, source_surface_sha256,",
            "    source_character_start, source_character_end, source_offset_unit",
            ")",
            "SELECT 'normalized_occurrence.' || seed.observation_key,",
            "       run.normalization_derivation_run_id,",
            "       pipeline.normalization_pipeline_id,",
            "       occurrence.observation_expression_id,",
            "       normalized.normalized_expression_id, seed.raw_phrase_sha256,",
            "       seed.raw_phrase_sha256, seed.source_character_start,",
            "       seed.source_character_end, 'UNICODE_CODE_POINT'",
            "FROM _r2b_observation_seed AS seed",
            "JOIN corpus.observation_expression AS occurrence",
            "  ON occurrence.observation_expression_key =",
            "     'observation_expression.' || seed.observation_key",
            "CROSS JOIN corpus.normalization_derivation_run AS run",
            "JOIN corpus.normalization_pipeline AS pipeline",
            "  ON pipeline.normalization_pipeline_id = run.normalization_pipeline_id",
            "JOIN corpus.normalized_expression AS normalized",
            "  ON normalized.normalization_pipeline_id = pipeline.normalization_pipeline_id",
            " AND normalized.normalized_text = seed.normalized_text",
            "WHERE seed.retained",
            "  AND run.normalization_derivation_run_key =",
            "      'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'",
            "ORDER BY occurrence.observation_expression_id;",
            "",
            "UPDATE corpus.normalization_derivation_run",
            f"SET output_inventory_sha256 = {sql_literal(normalization_output_sha256)},",
            f"    completed_at = {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ,",
            f"    output_occurrence_count = {EXPECTED_RETAINED_OCCURRENCES},",
            f"    frozen_at = {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ",
            "WHERE normalization_derivation_run_key =",
            "      'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1';",
            "",
            "INSERT INTO corpus.corpus_statistic_run (",
            "    corpus_statistic_run_key, normalization_derivation_run_id,",
            "    statistical_method_id, dataset_id, version_label, code_commit_sha,",
            "    configuration_sha256, configuration, sample_document_count,",
            "    sample_observation_count, sample_occurrence_count, started_at,",
            "    completed_at, frozen_at, result_inventory_sha256, value_semantics",
            ")",
            "SELECT 'statistic_run.firstbloom_a6cb002_pilot_v1.v1',",
            "       run.normalization_derivation_run_id, method.statistical_method_id,",
            "       dataset.dataset_id, '1',",
            f"       {sql_literal(code_commit_sha)},",
            f"       {sql_literal(statistic_configuration_sha256)},",
            f"       {sql_literal(canonical_json(statistic_configuration))}::JSONB,",
            f"       {EXPECTED_DOCUMENTS}, {EXPECTED_RAW_OBSERVATIONS},",
            f"       {EXPECTED_RETAINED_OCCURRENCES},",
            f"       {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ, NULL, NULL, NULL,",
            "       'Corpus frequencies and co-occurrences describe published language observations, not objective coffee flavor, perceptual similarity, or canonical ontology assertions.'",
            "FROM corpus.normalization_derivation_run AS run",
            "CROSS JOIN evidence.statistical_method AS method",
            "CROSS JOIN evidence.dataset AS dataset",
            "WHERE run.normalization_derivation_run_key =",
            "      'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'",
            "  AND method.method_key = 'method.round2b.document_language_observation_v1'",
            "  AND dataset.dataset_key = 'dataset.firstbloom_a6cb002_pilot_v1';",
            "",
            "WITH occurrence_classification AS (",
            "    SELECT normalized_occurrence.normalized_expression_id,",
            "           count(*)::BIGINT AS occurrence_count,",
            "           count(*) FILTER (WHERE EXISTS (",
            "               SELECT 1 FROM kb.lexicalization AS lexicalization",
            "               JOIN kb.concept AS concept",
            "                 ON concept.concept_id = lexicalization.concept_id",
            "               WHERE lexicalization.expression_id = occurrence.expression_id",
            "                 AND lexicalization.lifecycle_status_code = 'active'",
            "                 AND concept.lifecycle_status_code = 'active'",
            "                 AND concept.concept_type_code = 'composite_reference'",
            "           ))::BIGINT AS composite_count,",
            "           count(*) FILTER (WHERE EXISTS (",
            "               SELECT 1 FROM kb.lexicalization AS lexicalization",
            "               JOIN kb.concept AS concept",
            "                 ON concept.concept_id = lexicalization.concept_id",
            "               WHERE lexicalization.expression_id = occurrence.expression_id",
            "                 AND lexicalization.lifecycle_status_code = 'active'",
            "                 AND concept.lifecycle_status_code = 'active'",
            "                 AND concept.concept_type_code = 'qualifier'",
            "           ))::BIGINT AS qualifier_count,",
            "           count(*) FILTER (WHERE NOT EXISTS (",
            "               SELECT 1 FROM kb.lexicalization AS lexicalization",
            "               JOIN kb.concept AS concept",
            "                 ON concept.concept_id = lexicalization.concept_id",
            "               WHERE lexicalization.expression_id = occurrence.expression_id",
            "                 AND lexicalization.lifecycle_status_code = 'active'",
            "                 AND concept.lifecycle_status_code = 'active'",
            "           ))::BIGINT AS unresolved_count",
            "    FROM corpus.normalized_expression_occurrence AS normalized_occurrence",
            "    JOIN corpus.observation_expression AS occurrence",
            "      ON occurrence.observation_expression_id =",
            "         normalized_occurrence.observation_expression_id",
            "    JOIN corpus.normalization_derivation_run AS run",
            "      ON run.normalization_derivation_run_id =",
            "         normalized_occurrence.normalization_derivation_run_id",
            "    WHERE run.normalization_derivation_run_key =",
            "          'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1'",
            "    GROUP BY normalized_occurrence.normalized_expression_id",
            ")",
            "INSERT INTO corpus.normalized_expression_frequency (",
            "    normalized_expression_frequency_key, corpus_statistic_run_id,",
            "    normalized_expression_id, expression_frequency, document_frequency,",
            "    publisher_prevalence_count, publisher_sample_count,",
            "    country_prevalence_count, country_sample_count,",
            "    composite_reference_occurrence_count, qualifier_occurrence_count,",
            "    unresolved_occurrence_count, value_semantics",
            ")",
            "SELECT seed.frequency_key, statistic_run.corpus_statistic_run_id,",
            "       normalized.normalized_expression_id, seed.expression_frequency,",
            "       seed.document_frequency, seed.publisher_prevalence_count,",
            "       seed.publisher_sample_count, seed.country_prevalence_count,",
            "       seed.country_sample_count, classification.composite_count,",
            "       classification.qualifier_count, classification.unresolved_count,",
            "       seed.value_semantics",
            "FROM _r2b_frequency_seed AS seed",
            "JOIN corpus.normalized_expression AS normalized",
            "  ON normalized.normalized_text = seed.normalized_text",
            "JOIN corpus.normalization_pipeline AS pipeline",
            "  ON pipeline.normalization_pipeline_id = normalized.normalization_pipeline_id",
            "JOIN occurrence_classification AS classification",
            "  ON classification.normalized_expression_id = normalized.normalized_expression_id",
            "CROSS JOIN corpus.corpus_statistic_run AS statistic_run",
            f"WHERE pipeline.normalization_pipeline_key = {sql_literal(PIPELINE_KEY)}",
            "  AND statistic_run.corpus_statistic_run_key =",
            "      'statistic_run.firstbloom_a6cb002_pilot_v1.v1'",
            "  AND classification.occurrence_count = seed.expression_frequency",
            "ORDER BY normalized.normalized_expression_id;",
            "",
            "INSERT INTO corpus.normalized_expression_pair_measurement (",
            "    normalized_expression_pair_measurement_key, corpus_statistic_run_id,",
            "    subject_normalized_expression_id, object_normalized_expression_id,",
            "    cooccurrence_document_count, normalized_pmi,",
            "    subject_given_object_probability,",
            "    object_given_subject_probability, value_semantics, context",
            ")",
            "SELECT seed.pair_key, statistic_run.corpus_statistic_run_id,",
            "       least(subject.normalized_expression_id, object_expression.normalized_expression_id),",
            "       greatest(subject.normalized_expression_id, object_expression.normalized_expression_id),",
            "       seed.document_cooccurrence_count, seed.npmi,",
            "       CASE WHEN subject.normalized_expression_id < object_expression.normalized_expression_id",
            "            THEN seed.subject_given_object_probability",
            "            ELSE seed.object_given_subject_probability END,",
            "       CASE WHEN subject.normalized_expression_id < object_expression.normalized_expression_id",
            "            THEN seed.object_given_subject_probability",
            "            ELSE seed.subject_given_object_probability END,",
            "       seed.value_semantics, jsonb_build_object(",
            "           'window', 'captured_document',",
            "           'sample_document_count', seed.sample_count,",
            "           'staged_subject_normalized_text', seed.subject_normalized_text,",
            "           'staged_object_normalized_text', seed.object_normalized_text,",
            "           'staged_subject_document_frequency', seed.subject_document_frequency,",
            "           'staged_object_document_frequency', seed.object_document_frequency,",
            "           'endpoint_order', 'database identity ascending',",
            "           'sensory_similarity_asserted', FALSE",
            "       )",
            "FROM _r2b_pair_seed AS seed",
            "JOIN corpus.normalized_expression AS subject",
            "  ON subject.normalized_text = seed.subject_normalized_text",
            "JOIN corpus.normalized_expression AS object_expression",
            "  ON object_expression.normalized_text = seed.object_normalized_text",
            "JOIN corpus.normalization_pipeline AS pipeline",
            "  ON pipeline.normalization_pipeline_id = subject.normalization_pipeline_id",
            " AND pipeline.normalization_pipeline_id = object_expression.normalization_pipeline_id",
            "CROSS JOIN corpus.corpus_statistic_run AS statistic_run",
            f"WHERE pipeline.normalization_pipeline_key = {sql_literal(PIPELINE_KEY)}",
            "  AND statistic_run.corpus_statistic_run_key =",
            "      'statistic_run.firstbloom_a6cb002_pilot_v1.v1'",
            "ORDER BY least(subject.normalized_expression_id, object_expression.normalized_expression_id),",
            "         greatest(subject.normalized_expression_id, object_expression.normalized_expression_id);",
            "",
            "INSERT INTO corpus.acquisition_batch_diagnostic (",
            "    acquisition_batch_diagnostic_key, acquisition_batch_id,",
            "    corpus_statistic_run_id, diagnostic_code, measured_value,",
            "    sample_count, value_semantics, bootstrap_configuration, context",
            ")",
            "SELECT seed.diagnostic_key, batch.acquisition_batch_id,",
            "       statistic_run.corpus_statistic_run_id, seed.diagnostic_code,",
            "       seed.measured_value, seed.sample_count, seed.value_semantics,",
            "       seed.bootstrap_configuration, seed.context",
            "FROM _r2b_diagnostic_seed AS seed",
            "JOIN corpus.acquisition_batch AS batch",
            "  ON batch.acquisition_batch_key = seed.batch_key",
            "CROSS JOIN corpus.corpus_statistic_run AS statistic_run",
            "WHERE statistic_run.corpus_statistic_run_key =",
            "      'statistic_run.firstbloom_a6cb002_pilot_v1.v1'",
            "ORDER BY batch.batch_ordinal, seed.diagnostic_code;",
            "",
            "UPDATE corpus.corpus_statistic_run",
            f"SET completed_at = {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ,",
            f"    frozen_at = {sql_literal(CAPTURED_AT)}::TIMESTAMPTZ,",
            f"    result_inventory_sha256 = {sql_literal(statistic_result_sha256)}",
            "WHERE corpus_statistic_run_key =",
            "      'statistic_run.firstbloom_a6cb002_pilot_v1.v1';",
            "",
            "DO $round2b_pilot_assertions$",
            "DECLARE",
            "    selected_corpus_id BIGINT;",
            "    selected_pipeline_id BIGINT;",
            "    selected_run_id BIGINT;",
            "    selected_statistic_run_id BIGINT;",
            "BEGIN",
            f"    SELECT corpus_id INTO STRICT selected_corpus_id FROM corpus.corpus WHERE corpus_key = {sql_literal(CORPUS_KEY)};",
            f"    SELECT normalization_pipeline_id INTO STRICT selected_pipeline_id FROM corpus.normalization_pipeline WHERE normalization_pipeline_key = {sql_literal(PIPELINE_KEY)};",
            "    SELECT normalization_derivation_run_id INTO STRICT selected_run_id",
            "    FROM corpus.normalization_derivation_run",
            "    WHERE normalization_derivation_run_key =",
            "          'normalization_run.firstbloom_a6cb002_pilot_v1.en_v1';",
            "    SELECT corpus_statistic_run_id INTO STRICT selected_statistic_run_id",
            "    FROM corpus.corpus_statistic_run",
            "    WHERE corpus_statistic_run_key =",
            "          'statistic_run.firstbloom_a6cb002_pilot_v1.v1';",
            "",
            f"    IF (SELECT count(*) FROM corpus.industry_publisher WHERE source_policy_review_id = (SELECT source_policy_review_id FROM corpus.source_policy_review WHERE source_policy_review_key = 'source_policy.firstbloom.a6cb002.derived_terms')) <> {EXPECTED_PUBLISHERS} THEN RAISE EXCEPTION 'round2b publisher inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.industry_product AS product JOIN corpus.industry_publisher AS publisher USING (industry_publisher_id) WHERE publisher.source_policy_review_id = (SELECT source_policy_review_id FROM corpus.source_policy_review WHERE source_policy_review_key = 'source_policy.firstbloom.a6cb002.derived_terms')) <> {EXPECTED_PRODUCTS} THEN RAISE EXCEPTION 'round2b product inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.captured_document WHERE corpus_id = selected_corpus_id) <> {EXPECTED_DOCUMENTS} THEN RAISE EXCEPTION 'round2b document inventory mismatch'; END IF;",
            "    IF EXISTS (SELECT 1 FROM corpus.captured_document WHERE corpus_id = selected_corpus_id AND raw_text IS NOT NULL) THEN RAISE EXCEPTION 'round2b complete raw text leaked'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.raw_observation AS observation JOIN corpus.captured_document AS document USING (captured_document_id) WHERE document.corpus_id = selected_corpus_id) <> {EXPECTED_RAW_OBSERVATIONS} THEN RAISE EXCEPTION 'round2b observation inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.raw_observation AS observation JOIN corpus.captured_document AS document USING (captured_document_id) WHERE document.corpus_id = selected_corpus_id AND observation.observation_retention_code = 'hash_only' AND observation.observation_text IS NULL) <> {EXPECTED_REDACTED_OBSERVATIONS} THEN RAISE EXCEPTION 'round2b hash-only boundary mismatch'; END IF;",
            "    IF EXISTS (SELECT 1 FROM corpus.raw_observation AS observation JOIN corpus.captured_document AS document USING (captured_document_id) WHERE document.corpus_id = selected_corpus_id AND observation.observation_text IS NOT NULL AND char_length(observation.observation_text) > 80) THEN RAISE EXCEPTION 'round2b retained phrase exceeds rights boundary'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.normalized_expression_occurrence WHERE normalization_derivation_run_id = selected_run_id) <> {EXPECTED_RETAINED_OCCURRENCES} THEN RAISE EXCEPTION 'round2b normalized occurrence inventory mismatch'; END IF;",
            f"    IF (SELECT count(DISTINCT normalized_expression_id) FROM corpus.normalized_expression_occurrence WHERE normalization_derivation_run_id = selected_run_id) <> {EXPECTED_NORMALIZED_EXPRESSIONS} THEN RAISE EXCEPTION 'round2b normalized identity inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.normalized_expression_frequency WHERE corpus_statistic_run_id = selected_statistic_run_id) <> {EXPECTED_NORMALIZED_EXPRESSIONS} THEN RAISE EXCEPTION 'round2b frequency inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.normalized_expression_pair_measurement WHERE corpus_statistic_run_id = selected_statistic_run_id) <> {EXPECTED_COOCCURRENCE_PAIRS} THEN RAISE EXCEPTION 'round2b pair inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.acquisition_batch_diagnostic WHERE corpus_statistic_run_id = selected_statistic_run_id) <> {MAX_BATCH * 5} THEN RAISE EXCEPTION 'round2b diagnostic inventory mismatch'; END IF;",
            f"    IF (SELECT count(*) FROM corpus.document_duplicate_review AS review JOIN corpus.captured_document AS document ON document.captured_document_id = review.earlier_document_id WHERE document.corpus_id = selected_corpus_id) <> {EXPECTED_DUPLICATE_REVIEWS} THEN RAISE EXCEPTION 'round2b duplicate-review inventory mismatch'; END IF;",
            "    IF EXISTS (",
            "        SELECT 1 FROM kb.lexical_expression AS expression",
            "        WHERE expression.language_tag_code = 'en'",
            "          AND NOT EXISTS (",
            "              SELECT 1 FROM corpus.lexical_expression_normalization AS mapping",
            "              WHERE mapping.expression_id = expression.expression_id",
            "                AND mapping.normalization_pipeline_id = selected_pipeline_id",
            "          )",
            "    ) THEN RAISE EXCEPTION 'round2b English normalization dictionary closure mismatch'; END IF;",
            "    IF NOT EXISTS (SELECT 1 FROM corpus.corpus_snapshot WHERE corpus_snapshot_key =",
            f"        {sql_literal(SNAPSHOT_KEY)} AND frozen_at IS NOT NULL) THEN RAISE EXCEPTION 'round2b snapshot not frozen'; END IF;",
            "    IF NOT EXISTS (SELECT 1 FROM corpus.normalization_derivation_run WHERE normalization_derivation_run_id = selected_run_id AND frozen_at IS NOT NULL) THEN RAISE EXCEPTION 'round2b normalization run not frozen'; END IF;",
            "    IF NOT EXISTS (SELECT 1 FROM corpus.corpus_statistic_run WHERE corpus_statistic_run_id = selected_statistic_run_id AND frozen_at IS NOT NULL) THEN RAISE EXCEPTION 'round2b statistic run not frozen'; END IF;",
            "END;",
            "$round2b_pilot_assertions$;",
            "",
            "COMMIT;",
            "",
        ]
    )
    return "\n".join(parts)


def artifact_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate the deterministic, rights-bounded Round 2B Firstbloom "
            "pilot without network access."
        )
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Explicit local checkout of the pinned Firstbloom source",
    )
    parser.add_argument(
        "--code-commit-sha",
        help=(
            "40-hex commit containing the frozen Round 2B generator and "
            "normalization/schema code; this avoids claiming the Round 2A "
            "baseline as the implementation commit; required only for final "
            "seed generation"
        ),
    )
    parser.add_argument(
        "--emit-private-review-candidates",
        type=Path,
        help=(
            "Write the protected phrase-review TSV under /private/tmp and "
            "exit without generating repository artifacts"
        ),
    )
    parser.add_argument(
        "--emit-private-spot-audit",
        type=Path,
        help=(
            "Write the protected deterministic final-admission spot-audit "
            "packet under /private/tmp and exit"
        ),
    )
    parser.add_argument("--merge-private-review-passes", action="store_true")
    parser.add_argument("--reviewer-one-decisions", type=Path)
    parser.add_argument("--reviewer-two-decisions", type=Path)
    parser.add_argument("--reviewer-one-id")
    parser.add_argument("--reviewer-two-id")
    parser.add_argument("--reviewer-one-sha256")
    parser.add_argument("--reviewer-two-sha256")
    args = parser.parse_args()
    review_merge_arguments = [
        args.reviewer_one_decisions,
        args.reviewer_two_decisions,
        args.reviewer_one_id,
        args.reviewer_two_id,
        args.reviewer_one_sha256,
        args.reviewer_two_sha256,
    ]
    mode_count = sum(
        bool(value)
        for value in [
            args.emit_private_review_candidates,
            args.emit_private_spot_audit,
            args.merge_private_review_passes,
        ]
    )
    require(mode_count <= 1, "review preparation modes are mutually exclusive")
    require(
        args.merge_private_review_passes
        == all(value is not None for value in review_merge_arguments),
        "review merge requires both decision files and both reviewer IDs",
    )
    if not (
        args.emit_private_review_candidates
        or args.emit_private_spot_audit
        or args.merge_private_review_passes
    ):
        require(
            bool(
                args.code_commit_sha
                and re.fullmatch(r"[0-9a-f]{40}", args.code_commit_sha)
            ),
            "--code-commit-sha must be exactly 40 lowercase hexadecimal characters",
        )

    repo_root = repository_root_from_script()
    source_dir = args.source_dir.resolve()
    manifest = load_manifest(repo_root)
    verify_source_checkout(source_dir, manifest)
    rights_rows = enrich_rights_rows(validate_rights_matrix(repo_root))

    releases = read_csv(source_dir, "product_releases.csv")
    roasters = indexed_rows(
        read_csv(source_dir, "roasters_202312201330.csv"),
        "id",
        "roasters",
    )
    selected, _eligible_by_roaster = select_releases(releases, roasters)
    if args.emit_private_review_candidates:
        observations, _lexical_forms = parse_observations(selected)
        summary = write_private_review_candidates(
            args.emit_private_review_candidates, observations, repo_root
        )
        print(json.dumps({"status": "review_candidates_emitted", **summary}, sort_keys=True))
        return 0

    if args.merge_private_review_passes:
        observations, _lexical_forms = parse_observations(selected)
        summary = merge_private_review_passes(
            observations=observations,
            reviewer_one_path=args.reviewer_one_decisions,
            reviewer_two_path=args.reviewer_two_decisions,
            reviewer_one_id=args.reviewer_one_id,
            reviewer_two_id=args.reviewer_two_id,
            reviewer_one_expected_sha256=args.reviewer_one_sha256,
            reviewer_two_expected_sha256=args.reviewer_two_sha256,
            repo_root=repo_root,
        )
        print(json.dumps({"status": "review_passes_merged", **summary}, sort_keys=True))
        return 0

    if args.emit_private_spot_audit:
        admission_reviews = load_admission_reviews(repo_root)
        observations, _lexical_forms = parse_observations(
            selected,
            admission_reviews,
            enforce_frozen_counts=False,
        )
        summary = write_private_spot_audit(
            args.emit_private_spot_audit,
            observations,
            admission_reviews,
            repo_root,
        )
        print(
            json.dumps(
                {"status": "private_spot_audit_emitted", **summary},
                sort_keys=True,
            )
        )
        return 0

    admission_reviews = load_admission_reviews(repo_root)
    product_metadata = build_product_metadata(selected, source_dir)
    observations, lexical_forms = parse_observations(
        selected, admission_reviews
    )
    documents = document_expression_sets(selected, observations)
    statistics, cooccurrences, _representative_keys = (
        build_expression_statistics(documents, lexical_forms)
    )
    diagnostics = build_diagnostics(documents, product_metadata)
    publishers = build_publishers(selected, roasters)
    products = build_products(selected, product_metadata)
    inventory = build_inventory(selected, product_metadata, observations)
    duplicate_reviews = build_duplicate_reviews(inventory)
    expressions = expression_rows(observations, lexical_forms)
    batches = build_batch_rows(inventory)
    diagnostic_rows = build_diagnostic_rows(diagnostics)

    data_dir = repo_root / DATA_RELATIVE_DIR
    generated_data_paths = emit_machine_readable_data(
        data_dir,
        publishers,
        products,
        inventory,
        observations,
        expressions,
        statistics,
        cooccurrences,
        duplicate_reviews,
        diagnostics,
    )

    data_path_by_name = {path.name: path for path in generated_data_paths}
    required_generated_names = {
        PUBLISHER_TSV,
        PRODUCT_TSV,
        INVENTORY_TSV,
        OBSERVATION_TSV,
        EXPRESSION_TSV,
        STATISTIC_TSV,
        COOCCURRENCE_TSV,
        DUPLICATE_TSV,
        DIAGNOSTIC_JSON,
    }
    require(
        set(data_path_by_name) == required_generated_names,
        "machine-readable artifact set changed",
    )

    generator_path = Path(__file__).resolve()
    manifest_path = repo_root / MANIFEST_RELATIVE_PATH
    rights_path = repo_root / RIGHTS_RELATIVE_PATH
    admission_review_path = repo_root / ADMISSION_REVIEW_RELATIVE_PATH
    admission_review_metadata_path = (
        repo_root / ADMISSION_REVIEW_METADATA_RELATIVE_PATH
    )
    attribution_path = data_dir / "FIRSTBLOOM_ATTRIBUTION.md"
    require(attribution_path.is_file(), "Firstbloom attribution file is missing")
    require(
        admission_review_path.is_file()
        and admission_review_metadata_path.is_file(),
        "dual-review admission artifacts are missing",
    )
    admission_review_metadata = json.loads(
        admission_review_metadata_path.read_text(encoding="utf-8")
    )

    generated_data_hashes = {
        name: artifact_sha256(path)
        for name, path in sorted(data_path_by_name.items())
    }
    frame_receipt = [
        {
            "publisher_key": row["publisher_key"],
            "external_publisher_key": row["external_publisher_key"],
            "source_policy_key": row["source_policy_key"],
            "selected": True,
        }
        for row in publishers
    ]
    normalization_output_receipt = [
        {
            "observation_key": row["observation_key"],
            "source_observation_sha256": row["raw_phrase_sha256"],
            "source_surface_sha256": row["raw_phrase_sha256"],
            "source_character_start": row["source_character_start"],
            "source_character_end": row["source_character_end"],
            "normalized_text": row["normalized_text"],
        }
        for row in observations
        if row["retained"]
    ]
    statistic_configuration = statistic_configuration_contract()
    receipts = {
        "generator_sha256": artifact_sha256(generator_path),
        "source_manifest_sha256": artifact_sha256(manifest_path),
        "source_rights_sha256": artifact_sha256(rights_path),
        "admission_review_sha256": artifact_sha256(admission_review_path),
        "admission_review_metadata_sha256": artifact_sha256(
            admission_review_metadata_path
        ),
        "attribution_sha256": artifact_sha256(attribution_path),
        "normalization_rules_sha256": sha256_text(
            canonical_json(normalization_rules())
        ),
        "sampling_frame_sha256": sha256_text(canonical_json(frame_receipt)),
        "source_inventory_sha256": sha256_text(
            canonical_json(
                {
                    "pinned_source_sha": PINNED_SOURCE_SHA,
                    "source_manifest_sha256": artifact_sha256(manifest_path),
                    "source_rights_sha256": artifact_sha256(rights_path),
                    "admission_review_sha256": artifact_sha256(
                        admission_review_path
                    ),
                    "admission_review_metadata_sha256": artifact_sha256(
                        admission_review_metadata_path
                    ),
                    "pilot_publishers_sha256": generated_data_hashes[
                        PUBLISHER_TSV
                    ],
                }
            )
        ),
        "document_inventory_sha256": generated_data_hashes[INVENTORY_TSV],
        "normalization_input_inventory_sha256": generated_data_hashes[
            OBSERVATION_TSV
        ],
        "normalization_output_inventory_sha256": sha256_text(
            canonical_json(normalization_output_receipt)
        ),
        "statistic_configuration_sha256": sha256_text(
            canonical_json(statistic_configuration)
        ),
        "statistic_result_inventory_sha256": sha256_text(
            canonical_json(
                {
                    "frequency_sha256": generated_data_hashes[STATISTIC_TSV],
                    "cooccurrence_sha256": generated_data_hashes[
                        COOCCURRENCE_TSV
                    ],
                    "diagnostic_sha256": generated_data_hashes[
                        DIAGNOSTIC_JSON
                    ],
                }
            )
        ),
    }

    sql_text = render_sql(
        rights_rows=rights_rows,
        publishers=publishers,
        products=products,
        batches=batches,
        inventory=inventory,
        observations=observations,
        expressions=expressions,
        statistics=statistics,
        cooccurrences=cooccurrences,
        duplicate_reviews=duplicate_reviews,
        diagnostic_rows=diagnostic_rows,
        manifest=manifest,
        code_commit_sha=args.code_commit_sha,
        receipts=receipts,
    )
    sql_path = repo_root / SQL_RELATIVE_PATH
    sql_path.write_text(sql_text, encoding="utf-8")

    all_artifact_paths = [*generated_data_paths, sql_path]
    all_artifact_hashes = {
        str(path.relative_to(repo_root)): artifact_sha256(path)
        for path in sorted(all_artifact_paths)
    }
    process_document_counts: Counter[str] = Counter()
    origin_source_codes: set[str] = set()
    for row in inventory:
        process_document_counts.update(set(row["process_names"]))
        origin_source_codes.update(row["coffee_origin_country_codes"])
    decision_counts = Counter(row["decision_code"] for row in rights_rows)
    duplicate_basis_counts = Counter(
        row["duplicate_match_basis_code"] for row in duplicate_reviews
    )
    exclusion_reason_counts = Counter(
        row["exclusion_reason"]
        for row in observations
        if not row["retained"]
    )
    batch_document_counts = [
        row["expected_document_count"] for row in batches
    ]
    final_stage = diagnostics["stages"][-1]
    receipt = {
        "corpus_version": CORPUS_VERSION,
        "generated_at_contract_date": CHECKED_AT,
        "source_baseline_sha": SOURCE_BASELINE_SHA,
        "code_commit_sha": args.code_commit_sha,
        "pinned_firstbloom_sha": PINNED_SOURCE_SHA,
        "pinned_source_input_sha256": manifest["input_files"],
        "rights_boundary": {
            "decision": "ALLOW_DERIVED_TERMS",
            "complete_tasting_notes_stored": False,
            "long_descriptions_stored": False,
            "consumer_reviews_read": False,
            "max_stored_phrase_unicode_characters": MAX_STORED_PHRASE_CHARACTERS,
            "complete_field_surfaces": "hash_only_globally",
            "non_consensus_review_candidates": "hash_only",
            "long_fragments": "hash_only",
            "expression_admission_policy": REVIEW_POLICY_VERSION,
            "human_review": False,
            "automated_language_detection": False,
        },
        "counts": {
            "reviewed_source_policies": len(rights_rows),
            "source_decisions": dict(sorted(decision_counts.items())),
            "industry_publishers": len(publishers),
            "industry_products": len(products),
            "captured_documents": len(inventory),
            "batch_document_counts": batch_document_counts,
            "raw_observations": len(observations),
            "retained_short_observations": sum(
                row["retained"] for row in observations
            ),
            "hash_only_observations": sum(
                not row["retained"] for row in observations
            ),
            "hash_only_exclusion_reason_counts": dict(
                sorted(exclusion_reason_counts.items())
            ),
            "review_candidate_unique_hashes": (
                EXPECTED_REVIEW_CANDIDATE_UNIQUE_HASHES
            ),
            "review_consensus_counts": admission_review_metadata[
                "consensus_counts"
            ],
            "unique_retained_raw_expressions": len(
                {
                    row["observation_text"]
                    for row in observations
                    if row["retained"]
                }
            ),
            "observed_lexical_identities": len(expressions),
            "observed_normalized_identities": len(statistics),
            "frequency_rows": len(statistics),
            "cooccurrence_pairs": len(cooccurrences),
            "duplicate_reviews": len(duplicate_reviews),
            "duplicate_review_basis_counts": dict(
                sorted(duplicate_basis_counts.items())
            ),
            "acquisition_batch_diagnostics": len(diagnostic_rows),
            "explicit_origin_source_code_count": len(origin_source_codes),
            "documents_with_explicit_process": sum(
                bool(row["process_names"]) for row in inventory
            ),
        },
        "key_process_document_counts": {
            key: process_document_counts.get(key, 0)
            for key in [
                "Wet/Washed",
                "Dry/Natural",
                "Honey",
                "Anaerobic Fermentation",
            ]
        },
        "sampling_stop": diagnostics["stop_decision"],
        "final_batch_diagnostics": {
            "top_25_set_overlap": final_stage[
                "top_25_set_overlap_with_previous_batch"
            ],
            "top_100_set_overlap": final_stage[
                "top_100_set_overlap_with_previous_batch"
            ],
            "bootstrap_top5_neighbour_median_jaccard": final_stage[
                "bootstrap"
            ]["median_jaccard"],
            "bootstrap_top5_neighbour_mean_jaccard": final_stage[
                "bootstrap"
            ]["mean_jaccard"],
            "publisher_max_document_share": final_stage[
                "publisher_max_document_share"
            ],
            "publisher_document_hhi": final_stage[
                "publisher_document_hhi"
            ],
            "coffee_origin_country_max_source_code": final_stage[
                "coffee_origin_country_max_source_code"
            ],
            "coffee_origin_country_max_document_share": final_stage[
                "coffee_origin_country_max_document_share"
            ],
            "roaster_country_concentration": None,
            "roaster_country_concentration_status": (
                "not_assessed_source_country_absent"
            ),
        },
        "normalization_contract": normalization_rules(),
        "receipt_sha256": receipts,
        "artifact_sha256": all_artifact_hashes,
        "reproducibility_boundary": (
            "Schema, derived data, and statistics are reproducible from the "
            "pinned separately obtained CC BY 4.0 checkout, this generator, "
            "and the source-controlled hash-only dual-review inventory. The "
            "repository intentionally does not vendor complete tasting-note "
            "strings, rejected review phrases, long descriptions, or consumer "
            "reviews."
        ),
    }
    receipt_path = data_dir / RECEIPT_JSON
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    safe_summary = {
        "status": "generated",
        "corpus_version": CORPUS_VERSION,
        "code_commit_sha": args.code_commit_sha,
        "documents": len(inventory),
        "raw_observations": len(observations),
        "hash_only_observations": sum(
            not row["retained"] for row in observations
        ),
        "normalized_expressions": len(statistics),
        "cooccurrence_pairs": len(cooccurrences),
        "duplicate_reviews": len(duplicate_reviews),
        "sql_sha256": artifact_sha256(sql_path),
        "receipt_sha256": artifact_sha256(receipt_path),
    }
    print(json.dumps(safe_summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as error:
        print(f"generation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
