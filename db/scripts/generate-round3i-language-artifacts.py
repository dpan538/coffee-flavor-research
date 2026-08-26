#!/usr/bin/env python3
"""Generate the governed Round 3I language-corpus artifacts.

The Firstbloom source checkout is supplied explicitly and must resolve to the
pinned CC BY 4.0 commit. Review-candidate text is emitted only under
``/private/tmp``; the repository receives only dual-review decisions and
consensus-admitted expressions.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


PINNED_FIRSTBLOOM_SHA = "a6cb0026d1af9642724793c799bbc48dc189ba35"
FIRSTBLOOM_CSV_SHA256 = (
    "f0b556742dfbb7f4122ae00c9b31051c9a2ff233444771742bb538281cf6a8c0"
)
EXPECTED_ELIGIBLE_DOCUMENTS = 4498
EXPECTED_BASELINE_DOCUMENTS = 2474
EXPECTED_INCREMENTAL_DOCUMENTS = 2024
EXPECTED_CANDIDATE_OCCURRENCES = 4827
EXPECTED_CANDIDATE_NORMALIZED_IDENTITIES = 1515
EXPECTED_NEW_CANDIDATE_IDENTITIES = 1020
EXPECTED_REVIEW_CANDIDATE_SHA256 = (
    "51f65a21fa2e5d29e129d398eec6394541fb8b2b1c058eeaa9a4a6a31365e7a1"
)
EXPECTED_REVIEW_PASS_A_SHA256 = (
    "7e7917abc798ac45ab1ab9e2f610d48ce62bcb897528f916e66c92ab26dcb3dc"
)
EXPECTED_REVIEW_PASS_B_SHA256 = (
    "9a0c53310fc7e89863513b0f06ede91b10d80128dc47eb8c85b97c50ef710642"
)
EXPECTED_CONSENSUS_ADMITTED_IDENTITIES = 953
EXPECTED_GOVERNED_UNIQUE_EXPRESSION_GAIN = 952
MAX_PHRASE_CHARACTERS = 80

# This identity was admitted into the governed Round 3H baseline after the
# Round 2B pilot file used for candidate discovery.  It remains a valid
# dual-reviewed Firstbloom expression, but it is not an incremental identity.
POST_ROUND2B_GOVERNED_BASELINE = {"musty"}

DELIMITER_RE = re.compile(r"[,;|\r\n\u2022\u2023\u25e6\u2043\u2219]+")
WHITESPACE_RE = re.compile(r"\s+")
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
WHOLE_PHRASE_RULES = {
    "earl gray": "earl grey",
    "earl gray tea": "earl grey tea",
    "black currant": "blackcurrant",
}


class GenerationError(RuntimeError):
    """Raised when a frozen input or generated invariant differs."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GenerationError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def write_tsv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def tsv_bytes(rows: Iterable[dict[str, Any]], fields: list[str]) -> bytes:
    from io import StringIO

    output = StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=fields, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    return output.getvalue().encode("utf-8")


def verify_firstbloom_checkout(source_dir: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    require(
        result.stdout.strip() == PINNED_FIRSTBLOOM_SHA,
        "Firstbloom checkout does not match the pinned commit",
    )
    source_file = source_dir / "product_releases.csv"
    require(source_file.is_file(), "Firstbloom product_releases.csv is missing")
    require(
        sha256_bytes(source_file.read_bytes()) == FIRSTBLOOM_CSV_SHA256,
        "Firstbloom product_releases.csv hash differs from the frozen source",
    )


def structural_gate(value: str) -> str:
    if len(value) > MAX_PHRASE_CHARACTERS:
        return "REJECT_GT_80_UNICODE_CHARACTERS"
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        return "REJECT_CONTROL_OR_FORMAT_CHARACTER"
    if SENTENCE_PUNCTUATION_RE.search(value):
        return "REJECT_SENTENCE_PUNCTUATION"
    if PERSONAL_OR_FINITE_AUXILIARY_RE.search(value):
        return "REJECT_PERSONAL_OR_FINITE_AUXILIARY"
    if REPEATED_CONNECTIVE_RE.search(value):
        return "REJECT_REPEATED_CONNECTIVE"
    if len(WORD_TOKEN_RE.findall(value)) > 8:
        return "REJECT_GT_8_WORD_TOKENS"
    return "PASS_CONCISE_FRAGMENT"


def normalize_round2b_v1(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value)
    normalized = normalized.translate(PUNCTUATION_TRANSLATION)
    normalized = WHITESPACE_RE.sub(" ", normalized.lower()).strip()
    return WHOLE_PHRASE_RULES.get(normalized, normalized)


def firstbloom_review_candidates(
    repo_root: Path, source_dir: Path
) -> tuple[
    list[dict[str, Any]],
    dict[str, int],
    dict[str, list[dict[str, str]]],
    dict[str, dict[str, str]],
]:
    verify_firstbloom_checkout(source_dir)
    releases = read_csv(source_dir / "product_releases.csv")
    eligible = [
        row
        for row in releases
        if row.get("roaster_tasting_notes_string", "").strip()
    ]
    require(
        len(eligible) == EXPECTED_ELIGIBLE_DOCUMENTS,
        f"eligible Firstbloom document count is {len(eligible)}",
    )

    baseline_inventory = read_csv(
        repo_root / "db/data/round2b/pilot_inventory.tsv", delimiter="\t"
    )
    baseline_release_ids = {row["external_release_key"] for row in baseline_inventory}
    require(
        len(baseline_release_ids) == EXPECTED_BASELINE_DOCUMENTS,
        "Round 2B baseline document inventory changed",
    )
    incremental = [
        row
        for row in eligible
        if row["product_release_id"] not in baseline_release_ids
    ]
    require(
        len(incremental) == EXPECTED_INCREMENTAL_DOCUMENTS,
        f"incremental Firstbloom document count is {len(incremental)}",
    )

    complete_surfaces = {
        row["roaster_tasting_notes_string"].strip()
        for row in eligible
        if len(row["roaster_tasting_notes_string"].strip())
        <= MAX_PHRASE_CHARACTERS
    }
    baseline_expressions = {
        row["normalized_text"]
        for row in read_csv(
            repo_root / "db/data/round2b/pilot_expressions.tsv", delimiter="\t"
        )
    }

    occurrences: list[dict[str, str]] = []
    gate_counts: Counter[str] = Counter()
    incremental_by_id = {
        release["product_release_id"]: release for release in incremental
    }
    for release in incremental:
        raw_note = release["roaster_tasting_notes_string"]
        for fragment_index, raw_fragment in enumerate(DELIMITER_RE.split(raw_note), 1):
            phrase = raw_fragment.strip()
            if not phrase:
                continue
            if phrase in complete_surfaces:
                gate_counts["REJECT_COMPLETE_FIELD_SURFACE"] += 1
                continue
            gate = structural_gate(phrase)
            gate_counts[gate] += 1
            if gate != "PASS_CONCISE_FRAGMENT":
                continue
            normalized = normalize_round2b_v1(phrase)
            occurrences.append(
                {
                    "source_document_key": (
                        "document.firstbloom.release_"
                        + release["product_release_id"]
                    ),
                    "raw_phrase": phrase,
                    "raw_phrase_sha256": sha256_text(phrase),
                    "normalized_expression": normalized,
                    "fragment_index": str(fragment_index),
                }
            )

    require(
        len(occurrences) == EXPECTED_CANDIDATE_OCCURRENCES,
        f"Firstbloom candidate occurrence count is {len(occurrences)}",
    )
    require(
        len({row["normalized_expression"] for row in occurrences})
        == EXPECTED_CANDIDATE_NORMALIZED_IDENTITIES,
        "Firstbloom candidate normalized-identity inventory changed",
    )

    by_normalized: dict[str, list[dict[str, str]]] = defaultdict(list)
    for occurrence in occurrences:
        if occurrence["normalized_expression"] not in baseline_expressions:
            by_normalized[occurrence["normalized_expression"]].append(occurrence)
    require(
        len(by_normalized) == EXPECTED_NEW_CANDIDATE_IDENTITIES,
        f"new Firstbloom candidate identity count is {len(by_normalized)}",
    )

    candidates: list[dict[str, Any]] = []
    for normalized, grouped in sorted(by_normalized.items()):
        phrases = sorted(
            {row["raw_phrase"] for row in grouped},
            key=lambda value: (value.casefold(), value),
        )
        documents = sorted({row["source_document_key"] for row in grouped})
        surface_hashes = sorted({row["raw_phrase_sha256"] for row in grouped})
        candidates.append(
            {
                "candidate_key": "round3i.firstbloom.sha256_"
                + sha256_text(normalized),
                "normalized_expression": normalized,
                "representative_phrase": phrases[0],
                "raw_variant_count": len(phrases),
                "occurrence_count": len(grouped),
                "document_count": len(documents),
                "raw_surface_sha256": canonical_json(surface_hashes),
                "source_document_keys": canonical_json(documents),
                "review_state": "PENDING_DUAL_REVIEW",
            }
        )

    summary = {
        "eligible_document_count": len(eligible),
        "baseline_document_count": len(baseline_release_ids),
        "incremental_document_count": len(incremental),
        "candidate_occurrence_count": len(occurrences),
        "candidate_normalized_identity_count": len(
            {row["normalized_expression"] for row in occurrences}
        ),
        "new_candidate_identity_count": len(candidates),
        **{f"gate_{key.lower()}": value for key, value in sorted(gate_counts.items())},
    }
    return candidates, summary, by_normalized, incremental_by_id


REVIEW_CANDIDATE_FIELDS = [
    "candidate_key",
    "normalized_expression",
    "representative_phrase",
    "raw_variant_count",
    "occurrence_count",
    "document_count",
    "raw_surface_sha256",
    "source_document_keys",
    "review_state",
]


def load_review_pass(
    path: Path, expected_sha256: str, candidate_keys: set[str], review_pass: str
) -> dict[str, dict[str, str]]:
    require(path.is_file(), f"review pass {review_pass} is missing")
    require(
        sha256_bytes(path.read_bytes()) == expected_sha256,
        f"review pass {review_pass} hash differs from the reviewed artifact",
    )
    rows = read_csv(path, delimiter="\t")
    require(len(rows) == EXPECTED_NEW_CANDIDATE_IDENTITIES, "review row count changed")
    require(
        set(rows[0]) == {"candidate_key", "decision_code", "reason_code"},
        f"review pass {review_pass} schema changed",
    )
    by_key = {row["candidate_key"]: row for row in rows}
    require(len(by_key) == len(rows), f"review pass {review_pass} has duplicate keys")
    require(set(by_key) == candidate_keys, f"review pass {review_pass} candidate set changed")
    for row in rows:
        require(
            row["decision_code"]
            in {
                "ADMIT_SENSORY_LANGUAGE",
                "REJECT_NON_SENSORY",
                "REJECT_UNCERTAIN",
            },
            f"review pass {review_pass} has an invalid decision",
        )
        require(
            re.fullmatch(r"[a-z0-9_]+", row["reason_code"]) is not None,
            f"review pass {review_pass} has an invalid reason code",
        )
    return by_key


def firstbloom_repository_artifacts(
    repo_root: Path,
    candidates: list[dict[str, Any]],
    by_normalized: dict[str, list[dict[str, str]]],
    incremental_by_id: dict[str, dict[str, str]],
    review_pass_a: Path,
    review_pass_b: Path,
    output_dir: Path,
) -> dict[str, Any]:
    candidate_bytes = tsv_bytes(candidates, REVIEW_CANDIDATE_FIELDS)
    require(
        sha256_bytes(candidate_bytes) == EXPECTED_REVIEW_CANDIDATE_SHA256,
        "review-candidate inventory no longer matches the independently reviewed file",
    )
    candidates_by_key = {row["candidate_key"]: row for row in candidates}
    candidate_keys = set(candidates_by_key)
    pass_a = load_review_pass(
        review_pass_a, EXPECTED_REVIEW_PASS_A_SHA256, candidate_keys, "A"
    )
    pass_b = load_review_pass(
        review_pass_b, EXPECTED_REVIEW_PASS_B_SHA256, candidate_keys, "B"
    )
    consensus_keys = {
        key
        for key in candidate_keys
        if pass_a[key]["decision_code"] == "ADMIT_SENSORY_LANGUAGE"
        and pass_b[key]["decision_code"] == "ADMIT_SENSORY_LANGUAGE"
    }
    require(
        len(consensus_keys) == EXPECTED_CONSENSUS_ADMITTED_IDENTITIES,
        "dual-review consensus count changed",
    )

    decision_rows: list[dict[str, Any]] = []
    consensus_rows: list[dict[str, Any]] = []
    candidate_inventory_rows: list[dict[str, Any]] = []
    for candidate_key in sorted(candidate_keys):
        candidate = candidates_by_key[candidate_key]
        candidate_inventory_rows.append(
            {
                "candidate_key": candidate_key,
                "candidate_inventory_sha256": EXPECTED_REVIEW_CANDIDATE_SHA256,
                "normalized_expression_sha256": candidate_key.rsplit("_", 1)[-1],
                "raw_variant_count": candidate["raw_variant_count"],
                "occurrence_count": candidate["occurrence_count"],
                "document_count": candidate["document_count"],
                "raw_surface_hash_inventory_sha256": sha256_text(
                    candidate["raw_surface_sha256"]
                ),
                "source_document_inventory_sha256": sha256_text(
                    candidate["source_document_keys"]
                ),
                "candidate_text_retained": "false",
            }
        )
        for review_pass, reviewer_key, decision in (
            ("A", "codex.round3i.review.pass_a", pass_a[candidate_key]),
            ("B", "codex.round3i.review.pass_b", pass_b[candidate_key]),
        ):
            decision_rows.append(
                {
                    "candidate_review_key": (
                        f"review.round3i.firstbloom.{review_pass.lower()}."
                        + candidate_key.rsplit("_", 1)[-1]
                    ),
                    "candidate_key": candidate_key,
                    "reviewer_key": reviewer_key,
                    "review_pass": review_pass,
                    "candidate_inventory_sha256": EXPECTED_REVIEW_CANDIDATE_SHA256,
                    "decision_code": decision["decision_code"],
                    "reason_code": decision["reason_code"],
                    "reviewed_on": "2026-08-26",
                    "human_review": "false",
                    "automatic_language_detection": "false",
                }
            )
        consensus_rows.append(
            {
                "candidate_key": candidate_key,
                "pass_a_decision": pass_a[candidate_key]["decision_code"],
                "pass_a_reason": pass_a[candidate_key]["reason_code"],
                "pass_b_decision": pass_b[candidate_key]["decision_code"],
                "pass_b_reason": pass_b[candidate_key]["reason_code"],
                "consensus_admitted": str(candidate_key in consensus_keys).lower(),
            }
        )

    normalized_by_candidate = {
        row["candidate_key"]: row["normalized_expression"] for row in candidates
    }
    admitted_normalized = {
        normalized_by_candidate[key] for key in consensus_keys
    }
    admitted_occurrences = [
        occurrence
        for normalized in admitted_normalized
        for occurrence in by_normalized[normalized]
    ]
    admitted_occurrences.sort(
        key=lambda row: (
            row["source_document_key"],
            int(row["fragment_index"]),
            row["normalized_expression"],
            row["raw_phrase"],
        )
    )
    document_keys = {
        row["source_document_key"] for row in admitted_occurrences
    }

    family_rows = [
        {
            "language_source_family_key": "family.baseline.firstbloom-industry",
            "family_name": "Firstbloom licensed industry tasting notes",
            "canonical_origin_key": "origin.github.alexcaza.firstbloom-data",
            "counts_as_independent": "true",
            "mirror_of_language_source_family_key": "",
            "counts_as_new_contemporary_family": "false",
            "counts_as_zh_hans_family": "false",
            "historical_baseline": "true",
            "source_authored": "true",
            "admitted": "true",
            "independence_basis": "One pinned upstream aggregation already governed as the Round 2B historical language baseline; this increment is not a new independent family.",
            "introduced_round": "3I",
        }
    ]
    source_rows = [
        {
            "language_source_key": "github.firstbloom-data.a6cb0026",
            "language_source_family_key": "family.baseline.firstbloom-industry",
            "title": "Firstbloom Data",
            "authors_or_owner": "Alex Caza",
            "publication_year": "2023",
            "doi_or_stable_url": "https://github.com/alexcaza/firstbloom-data",
            "repository": "GitHub",
            "exact_version": PINNED_FIRSTBLOOM_SHA,
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
            "rights_basis": "Pinned repository license file and README declare CC BY 4.0; project export remains limited to dual-reviewed short phrases with attribution and change indication.",
            "rights_review_complete": "true",
            "privacy_decision": "No consumer reviews or personal data are imported; only product-release tasting-note fragments and non-personal row keys are retained.",
            "privacy_review_complete": "true",
            "source_file_manifest": canonical_json(
                [
                    {
                        "path": "product_releases.csv",
                        "sha256": FIRSTBLOOM_CSV_SHA256,
                    }
                ]
            ),
            "source_file_hash_complete": "true",
            "language_codes": canonical_json(["en"]),
            "geography": "Multi-origin industry aggregation",
            "data_type": "Licensed specialty-coffee product-release tasting-note records",
            "evidence_role": "Observed industry tasting language only",
            "limitations": "Secondary aggregation; not objective sensory truth; complete fields, disagreements, descriptions, and consumer reviews remain excluded.",
            "annotation_complete": "true",
            "admitted": "true",
        }
    ]

    documents: list[dict[str, Any]] = []
    for document_key in sorted(document_keys):
        release_id = document_key.rsplit("_", 1)[-1]
        release = incremental_by_id[release_id]
        raw_note = release["roaster_tasting_notes_string"]
        documents.append(
            {
                "language_document_key": document_key,
                "language_source_key": "github.firstbloom-data.a6cb0026",
                "language_source_family_key": "family.baseline.firstbloom-industry",
                "source_revision": PINNED_FIRSTBLOOM_SHA,
                "source_date": release["release_created_at"][:10],
                "source_row_locator": f"product_release_id={release_id}",
                "language_code": "en",
                "document_type": "TASTING_NOTE",
                "source_content_sha256": sha256_text(raw_note),
                "content": canonical_json(
                    {
                        "external_release_key": release_id,
                        "product_id": release["product_id"],
                        "raw_field_sha256": sha256_text(raw_note),
                        "retention": "dual-reviewed-short-phrases-only",
                    }
                ),
                "raw_text_public_export_allowed": "false",
                "counts_as_new_contemporary_document": "false",
                "counts_as_zh_hans_document": "false",
                "source_authored": "true",
                "machine_translated": "false",
                "artificial_variant": "false",
                "privacy_state": "NO_PERSONAL_DATA",
                "public_export_state": "PUBLIC_DERIVED_ONLY",
                "frozen_snapshot": "true",
            }
        )

    expressions: list[dict[str, Any]] = []
    for candidate_key in sorted(consensus_keys):
        candidate = candidates_by_key[candidate_key]
        expression_hash = candidate_key.rsplit("_", 1)[-1]
        expressions.append(
            {
                "language_expression_key": f"language.expression.en.sha256_{expression_hash}",
                "language_code": "en",
                "representative_source_phrase": candidate["representative_phrase"],
                "normalized_expression": candidate["normalized_expression"],
                "expression_role": "UNRESOLVED",
                "source_authored": "true",
                "machine_translated": "false",
                "artificial_variant": "false",
                "review_state": "DUAL_CODEX_REVIEWED",
                "counts_toward_governed_total": str(
                    candidate["normalized_expression"]
                    not in POST_ROUND2B_GOVERNED_BASELINE
                ).lower(),
                "counts_as_zh_hans_sensory_expression": "false",
                "public_export_allowed": "true",
                "limitation": "Observed licensed industry phrase; not a canonical concept or scientific sensory fact.",
            }
        )

    occurrences: list[dict[str, Any]] = []
    duplicate_counter: Counter[tuple[str, str, str]] = Counter()
    for occurrence in admitted_occurrences:
        expression_hash = sha256_text(occurrence["normalized_expression"])
        identity = (
            occurrence["source_document_key"],
            expression_hash,
            occurrence["fragment_index"],
        )
        duplicate_counter[identity] += 1
        locator = (
            f"tasting_note.fragment.{int(occurrence['fragment_index']):03d}."
            f"occurrence.{duplicate_counter[identity]:03d}"
        )
        occurrence_hash = sha256_text(
            "|".join(
                [
                    occurrence["source_document_key"],
                    expression_hash,
                    locator,
                    occurrence["raw_phrase"],
                ]
            )
        )
        occurrences.append(
            {
                "language_occurrence_key": f"language.occurrence.firstbloom.sha256_{occurrence_hash}",
                "language_document_key": occurrence["source_document_key"],
                "language_expression_key": f"language.expression.en.sha256_{expression_hash}",
                "raw_source_phrase": occurrence["raw_phrase"],
                "source_locator": locator,
                "observed_value": canonical_json(
                    {
                        "admission": "dual-review-consensus",
                        "normalization": "round2b-v1",
                    }
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[tuple[str, list[dict[str, Any]], list[str]]] = [
        (
            "language_source_families.tsv",
            family_rows,
            list(family_rows[0]),
        ),
        ("language_sources.tsv", source_rows, list(source_rows[0])),
        ("language_documents.tsv", documents, list(documents[0])),
        ("language_expressions.tsv", expressions, list(expressions[0])),
        ("language_occurrences.tsv", occurrences, list(occurrences[0])),
        (
            "firstbloom_review_candidates_text_free.tsv",
            candidate_inventory_rows,
            list(candidate_inventory_rows[0]),
        ),
        (
            "firstbloom_review_decisions.tsv",
            decision_rows,
            list(decision_rows[0]),
        ),
        (
            "firstbloom_review_consensus.tsv",
            consensus_rows,
            list(consensus_rows[0]),
        ),
    ]
    file_hashes: dict[str, str] = {}
    for filename, rows, fields in outputs:
        path = output_dir / filename
        write_tsv(path, rows, fields)
        file_hashes[filename] = sha256_bytes(path.read_bytes())

    result = {
        "batch_key": "round3i.batch2.firstbloom-language-expansion",
        "targeted_gap": "TOTAL_GOVERNED_UNIQUE_NORMALIZED_EXPRESSION_COUNT",
        "named_sources_reviewed": 1,
        "sources_admitted": 1,
        "source_families_added": 0,
        "rows_added": len(occurrences),
        "documents_added": len(documents),
        "governed_baseline_expression_overlap_count": sum(
            row["counts_toward_governed_total"] == "false"
            for row in expressions
        ),
        "unique_expression_inventory_count": len(expressions),
        "unique_expressions_added": sum(
            row["counts_toward_governed_total"] == "true"
            for row in expressions
        ),
        "zh_hans_expressions_added": 0,
        "coverage_cells_added": 0,
        "relationship_support_added": 0,
        "rights_blocked_count": 0,
        "access_blocked_count": 0,
        "marginal_coverage_gain": "HIGH",
        "readiness_state_after": "LANGUAGE_EXPRESSION_GATE_PENDING_ZH_HANS",
        "candidate_inventory_sha256": EXPECTED_REVIEW_CANDIDATE_SHA256,
        "review_pass_a_sha256": EXPECTED_REVIEW_PASS_A_SHA256,
        "review_pass_b_sha256": EXPECTED_REVIEW_PASS_B_SHA256,
        "consensus_admitted_identity_count": len(expressions),
        "file_hashes": file_hashes,
    }
    result_path = output_dir / "batch_result.json"
    require(
        result["unique_expressions_added"]
        == EXPECTED_GOVERNED_UNIQUE_EXPRESSION_GAIN,
        "governed Firstbloom expression gain differs",
    )
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result["batch_result_sha256"] = sha256_bytes(result_path.read_bytes())
    return result


def require_private_path(path: Path, repo_root: Path) -> Path:
    resolved = path.resolve()
    require(
        resolved.is_relative_to(Path("/private/tmp").resolve()),
        "review candidates must stay under /private/tmp",
    )
    require(
        not resolved.is_relative_to(repo_root.resolve()),
        "review candidates must not be written into the repository",
    )
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--emit-private-review-candidates", type=Path)
    parser.add_argument("--review-pass-a", type=Path)
    parser.add_argument("--review-pass-b", type=Path)
    parser.add_argument("--emit-repository-artifacts", type=Path)
    args = parser.parse_args()
    repo_root = repository_root()
    candidates, summary, by_normalized, incremental_by_id = firstbloom_review_candidates(
        repo_root, args.source_dir.resolve()
    )
    if args.emit_private_review_candidates:
        output = require_private_path(
            args.emit_private_review_candidates, repo_root
        )
        write_tsv(
            output,
            candidates,
            REVIEW_CANDIDATE_FIELDS,
        )
        output.chmod(0o600)
        print(
            canonical_json(
                {
                    "status": "PRIVATE_REVIEW_CANDIDATES_EMITTED",
                    "output": str(output),
                    "output_sha256": sha256_bytes(output.read_bytes()),
                    **summary,
                }
            )
        )
        return 0
    if args.emit_repository_artifacts:
        require(
            args.review_pass_a is not None and args.review_pass_b is not None,
            "both independent review-pass files are required",
        )
        output_dir = args.emit_repository_artifacts.resolve()
        require(
            output_dir.is_relative_to(repo_root.resolve()),
            "repository artifacts must be written inside the repository",
        )
        result = firstbloom_repository_artifacts(
            repo_root,
            candidates,
            by_normalized,
            incremental_by_id,
            args.review_pass_a.resolve(),
            args.review_pass_b.resolve(),
            output_dir,
        )
        print(canonical_json({"status": "REPOSITORY_ARTIFACTS_EMITTED", **summary, **result}))
        return 0
    print(canonical_json({"status": "AUDIT_ONLY", **summary}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GenerationError as error:
        print(f"Round 3I language generation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
