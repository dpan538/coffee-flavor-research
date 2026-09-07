#!/usr/bin/env python3
"""Reclassify retrieved R11 tables under the owner-approved T1--T6 contracts.

No model is trained or fitted.  Named-descriptor mapping is exact DIRECT or an
exact lookup in the frozen R6 semantic registry; no new mapping rule is created.
T5/T6 records are ontology-review evidence only and T4 retains source-native
dimension semantics rather than expanding broad terms to named descriptors.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any

from extract_candidates_r11 import (
    C0_PATTERNS,
    C1_PATTERNS,
    aggregation,
    base_sample_key,
    context_value,
    digest,
    find_panel_size,
    find_replicates,
    find_scale,
    norm,
    numeric,
    parse_html,
    parse_xml,
    stable_bytes,
)


ROOT = Path(__file__).resolve().parents[2]
R6 = ROOT / "db/data/backend-sequential-model-v2/revisions/r6"
R9 = ROOT / "db/data/backend-sequential-model-v2/revisions/r9"
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
DEFAULT_RAW = R11 / "extraction_report.json"
DEFAULT_OUTPUT = R11 / "shape_distribution.json"
DEFAULT_CACHE = Path("/private/tmp/coffee-flavor-r11-fulltext-cache")

SHAPES = {
    "T1": "DIRECT_INTENSITY",
    "T2": "DIRECT_FREQUENCY",
    "T3": "DIRECT_PRESENCE",
    "T4": "DIMENSION_ONLY",
    "T5": "ONTOLOGY_REFERENCE",
    "T6": "ONTOLOGY_CHEMICAL",
}

NATIVE_DIMENSIONS = {
    "acidity",
    "acid",
    "sour",
    "sourness",
    "body",
    "bitterness",
    "bitter",
    "sweetness",
    "sweet",
    "aroma",
    "aroma intensity",
    "aromatic intensity",
    "fragrance",
    "flavor",
    "flavour",
    "flavor intensity",
    "flavour intensity",
    "aftertaste",
    "balance",
    "uniformity",
    "clean cup",
    "overall",
    "overall impression",
    "astringency",
    "astringent",
    "fruity",
    "floral",
    "flowery",
    "nutty",
    "roasted",
}

ANALYTIC_NOT_SAMPLE_SUPERVISION = (
    r"analysis of variance|\banova\b",
    r"model performance|model factors|rmsep|rmsev",
    r"descriptive statistics",
    r"correlation coefficients?|principal component|factor loadings?",
    r"variable importance|\bvip\b|regression|prediction errors?",
    r"aroma extract dilution|odor activity|odou?r activity|\boav\b|\broav\b|\baeda\b",
)

INVALID_SAMPLE_LABEL = re.compile(
    r"^(?:p[ -]?values?|lsd|cv|se|sem|sd|error|accuracy|coefficient|vip|rmse|"
    r"model|overall stats?|mean|min|max|m/z|threshold|total number|reference|"
    r"definition|class|preparation)(?:\b|\s*[-:])",
    re.I,
)

TABLE_SUPERVISION_CUE = re.compile(
    r"sensor|cupping|q[ -]?grader|quantitative descriptive|\bqda\b|\bcata\b|"
    r"flavo[u]?r profile|sensory descriptors?",
    re.I,
)


def load_direct_registry() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    registry = json.loads((R9 / "output_policy_contract.json").read_text())[
        "concept_role_registry"
    ]
    direct = {
        norm(candidate_id.removeprefix("sensory.").replace("_", " ")): candidate_id
        for candidate_id, row in registry.items()
        if row["role"] == "NAMED_DESCRIPTOR" and candidate_id.startswith("sensory.")
    }
    rules: dict[str, dict[str, str]] = {}
    with (R6 / "semantic_patch.tsv").open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rules[norm(row["normalized_span"])] = row
    return direct, rules


def resolve_surface(
    surface: str,
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> dict[str, Any]:
    token = norm(surface)
    if token in direct:
        return {
            "mapping_status": "DIRECT",
            "concept_id": direct[token],
            "rule_id": None,
            "mapping_direction": "IDENTITY",
            "specificity_grade": "SPECIFIC",
        }
    rule = rules.get(token)
    if not rule:
        return {
            "mapping_status": "UNMAPPED",
            "concept_id": None,
            "rule_id": None,
            "mapping_direction": "NONE",
            "specificity_grade": (
                "COMPOUND" if len(token.split()) > 1 or "/" in surface else "UNRESOLVED"
            ),
        }
    concept = rule["concepts"]
    specificity = "SPECIFIC" if concept.startswith("sensory.") else "BROAD"
    if rule["relation"] == "SCOPED_MODIFIER_CORE":
        specificity = "COMPOUND"
    return {
        "mapping_status": "MAPPED",
        "concept_id": concept,
        "rule_id": rule["rule_id"],
        "mapping_direction": (
            "GENERALISATION"
            if not concept.startswith("sensory.")
            else "IDENTITY_OR_HEAD_PRESERVING"
        ),
        "specificity_grade": specificity,
        "r6_relation": rule["relation"],
        "r6_human_approval": rule["human_approval"],
    }


def dimension_surface(surface: str) -> str | None:
    token = norm(surface)
    return token if token in NATIVE_DIMENSIONS else None


def table_headers(rows: list[list[str]], limit: int = 5) -> list[tuple[int, list[str]]]:
    return [(index, row) for index, row in enumerate(rows[:limit]) if row]


def table_is_consumer(article_text: str) -> bool:
    consumer = re.search(r"consumer|customer|hedonic|liking|preference", article_text, re.I)
    trained = re.search(
        r"trained (?:sensory )?(?:panel|panelists|assessors)|q[ -]?graders|expert cuppers",
        article_text,
        re.I,
    )
    return bool(consumer and not trained)


def source_family(doi: str) -> str:
    return "family.r11." + digest(doi.lower().encode())[:20]


def group_identity(doi: str, sample: str, article_text: str) -> tuple[str, str]:
    base = base_sample_key(sample, article_text)
    return (
        "r11.group:" + digest(f"{doi.lower()}|{base}".encode())[:24],
        base,
    )


def invalid_sample_label(value: str) -> bool:
    token = norm(value)
    if not token or numeric(value) is not None or INVALID_SAMPLE_LABEL.search(token):
        return True
    return bool(
        re.fullmatch(
            r"(?:attributes?|descriptors?|sensory index|sensory descriptors?|"
            r"extraction conditions?|sample numbers?|temperature|pressure|time)",
            token,
        )
    )


def noncoffee_sample_domain(title: str, caption: str) -> bool:
    text = norm(f"{title} {caption}")
    return bool(
        re.search(
            r"coffee (?:pulp|cascara) wines?|coffee liqueur|coffee flavored|"
            r"green tea|black tea|tea infusion|pure tastant|model solution|"
            r"caffeine solution|sucrose solution",
            text,
        )
    )


def resolved_surface(
    surface: str,
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> tuple[dict[str, Any], str | None] | None:
    mapping = resolve_surface(surface, direct, rules)
    dimension = dimension_surface(surface)
    return (mapping, dimension) if mapping["concept_id"] or dimension else None


def descriptor_axis(
    rows: list[list[str]],
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> tuple[str, Any] | None:
    """Return one unambiguous descriptor-axis orientation for a table.

    A table is never processed in both orientations.  Row-oriented tables need
    at least two descriptor/dimension rows.  Column-oriented tables need at
    least two descriptor/dimension columns and a later row containing numeric
    cells at those columns.  This prevents previous descriptor rows and values
    from leaking into constructed sample labels.
    """
    row_hits: list[tuple[int, int, str, dict[str, Any], str | None]] = []
    for row_index, row in enumerate(rows):
        for column, surface in enumerate(row[:3]):
            resolved = resolved_surface(surface, direct, rules)
            if not resolved:
                continue
            mapping, dimension = resolved
            if any(numeric(cell) is not None or norm(cell) in {"x", "yes", "present", "+", "significant"} for cell in row[column + 1 :]):
                row_hits.append((row_index, column, surface, mapping, dimension))
            break

    column_options = []
    for header_index, header in table_headers(rows):
        resolved_columns = {}
        for column, surface in enumerate(header):
            if column == 0:
                continue
            resolved = resolved_surface(surface, direct, rules)
            if resolved:
                mapping, dimension = resolved
                resolved_columns[column] = (surface, mapping, dimension)
        if len(resolved_columns) < 2:
            continue
        numeric_rows = sum(
            any(column < len(row) and numeric(row[column]) is not None for column in resolved_columns)
            for row in rows[header_index + 1 :]
        )
        if numeric_rows:
            column_options.append((len(resolved_columns), -header_index, header_index, resolved_columns))

    # A strong header axis wins.  Otherwise use the repeated descriptor-row axis.
    if column_options:
        _, _, header_index, resolved_columns = max(column_options)
        return "COLUMN", (header_index, resolved_columns)
    if len(row_hits) >= 2:
        return "ROW", row_hits
    return None


def record_common(
    candidate: dict[str, Any],
    outcome: dict[str, Any],
    table: dict[str, Any],
    shape_id: str,
    sequence: str,
) -> dict[str, Any]:
    retrieval = outcome["retrieval"]
    doi = candidate["doi"]
    return {
        "record_id": "r11.typed:" + digest(
            f"{doi}|{table['table_id']}|{shape_id}|{sequence}".encode()
        )[:24],
        "shape_id": shape_id,
        "evidence_grade": SHAPES[shape_id],
        "source_family_id": source_family(doi),
        "source_system": candidate["source_system"],
        "source_record_id": candidate["source_record_id"],
        "source_doi": doi,
        "source_url": retrieval["final_url"],
        "source_sha256": retrieval["sha256"],
        "resolved_license": outcome.get("source_verified_license"),
        "share_alike_obligation": outcome.get("source_verified_license")
        in {"CC-BY-SA-4.0", "ODbL-1.0"},
        "attribution_string": f"{candidate['title']}. https://doi.org/{doi}",
        "table_id": table["table_id"],
        "table_caption_sha256": digest(table["caption"].encode()),
        "participant_pii_present": False,
        "publication_year": outcome.get("publication_year"),
        "authors": outcome.get("authors", []),
        "institutions": outcome.get("institutions", []),
    }


def ontology_records(
    candidate: dict[str, Any],
    outcome: dict[str, Any],
    table: dict[str, Any],
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows = table["rows"]
    if not rows:
        return []
    caption = norm(table["caption"])
    header_index, header = max(table_headers(rows), key=lambda pair: len(pair[1]))
    normalized = [norm(cell) for cell in header]
    records = []
    if (
        any("definition" in cell or "reference" in cell for cell in normalized)
        and any("attribute" in cell or "descriptor" in cell for cell in normalized)
    ) or re.search(r"guide to sensory attributes|references? for .*training|lexicon", caption):
        descriptor_column = next(
            (
                index
                for index, cell in enumerate(normalized)
                if "attribute" in cell or "descriptor" in cell
            ),
            0,
        )
        reference_column = next(
            (
                index
                for index, cell in enumerate(normalized)
                if "definition" in cell or "reference" in cell
            ),
            None,
        )
        for index, row in enumerate(rows[header_index + 1 :], header_index + 1):
            if descriptor_column >= len(row) or not norm(row[descriptor_column]):
                continue
            surface = row[descriptor_column]
            mapping = resolve_surface(surface, direct, rules)
            reference = row[reference_column] if reference_column is not None and reference_column < len(row) else ""
            records.append(
                record_common(candidate, outcome, table, "T5", f"{index}|{surface}")
                | {
                    "source_surface_form": surface[:240],
                    "reference_value_sha256": digest(reference.encode()) if reference else None,
                    "track": "ONTOLOGY_REVIEW_ONLY",
                    **mapping,
                }
            )
        return records

    compound_column = next(
        (index for index, cell in enumerate(normalized) if "compound" in cell), None
    )
    odor_column = next(
        (
            index
            for index, cell in enumerate(normalized)
            if "odor" in cell or "odour" in cell or "aroma description" in cell
        ),
        None,
    )
    if (compound_column is not None and odor_column is not None) or re.search(
        r"aroma active compounds|key aroma compounds|volatile compounds|\baeda\b|\boav\b",
        caption,
    ):
        if compound_column is None or odor_column is None:
            return []
        for index, row in enumerate(rows[header_index + 1 :], header_index + 1):
            if max(compound_column, odor_column) >= len(row):
                continue
            compound, surface = row[compound_column], row[odor_column]
            if not norm(compound) or not norm(surface):
                continue
            mapping = resolve_surface(surface, direct, rules)
            records.append(
                record_common(candidate, outcome, table, "T6", f"{index}|{compound}|{surface}")
                | {
                    "compound_name": compound[:240],
                    "source_surface_form": surface[:240],
                    "track": "ONTOLOGY_REVIEW_ONLY",
                    **mapping,
                }
            )
        return records
    return []


def sample_axis_records(
    candidate: dict[str, Any],
    outcome: dict[str, Any],
    table: dict[str, Any],
    article_text: str,
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> list[dict[str, Any]]:
    rows = table["rows"]
    caption = f"{table['caption']} {table['label']}"
    if (
        not rows
        or not TABLE_SUPERVISION_CUE.search(caption)
        or any(re.search(pattern, caption, re.I) for pattern in ANALYTIC_NOT_SAMPLE_SUPERVISION)
    ):
        return []
    if re.search(r"guide to sensory|reference standards?|training lexicon", caption, re.I):
        return []
    if re.search(r"compound|\boav\b|\baeda\b|chromatograph|gc[- /]", caption, re.I):
        return []
    if noncoffee_sample_domain(candidate["title"], caption):
        return []
    if table_is_consumer(article_text) or re.search(
        r"consumer|customer|hedonic|liking|preference|pre[ -]?tasting|post[ -]?tasting",
        caption,
        re.I,
    ):
        return []

    records = []
    panel_size = find_panel_size(article_text)
    scale = find_scale(article_text)
    replicates = find_replicates(article_text)
    aggregate = aggregation(f"{caption} {' '.join(sum(rows, []))}")
    frequency = aggregate == "FREQUENCY_OR_PRESENCE" or bool(
        re.search(r"\bcata\b|citation|frequency|proportion|percentage", caption, re.I)
    )

    axis = descriptor_axis(rows, direct, rules)
    if not axis:
        return []

    def append_cell(
        orientation: str,
        row_index: int,
        column: int,
        sample: str,
        surface: str,
        mapping: dict[str, Any],
        dimension: str | None,
        raw_value: str,
    ) -> None:
        value = numeric(raw_value)
        presence = norm(raw_value) in {"x", "yes", "present", "+", "significant"}
        if value is None and not presence:
            return
        mapped_dimension = bool(
            mapping["concept_id"] and not mapping["concept_id"].startswith("sensory.")
        )
        shape = (
            "T4"
            if dimension or mapped_dimension
            else "T3"
            if presence
            else "T2"
            if frequency
            else "T1"
        )
        if shape in {"T1", "T2", "T3"} and not mapping["concept_id"]:
            return
        group_id, base = group_identity(candidate["doi"], sample, article_text)
        context = f"{sample} {caption}"
        c0 = context_value(context, C0_PATTERNS) or context_value(article_text, C0_PATTERNS)
        c1 = context_value(context, C1_PATTERNS) or context_value(article_text, C1_PATTERNS)
        sequence = f"{orientation}|{row_index}|{column}|{sample}|{surface}"
        records.append(
            record_common(candidate, outcome, table, shape, sequence)
            | {
                "coffee_group_id": group_id,
                "canonical_trial_id": "r11.trial:" + digest(candidate["doi"].lower().encode())[:24],
                "base_coffee_identity_normalized": base,
                "sample_condition_id": "r11.condition:" + digest(
                    f"{candidate['doi']}|{table['table_id']}|{norm(sample)}".encode()
                )[:24],
                "sample_label": sample[:240],
                "source_surface_form": surface[:240],
                "reported_value": value if value is not None else 1.0,
                "reported_value_raw": raw_value[:80],
                "panel_size": panel_size,
                "scale": scale,
                "aggregation": aggregate,
                "replicate_structure": replicates,
                "c0_id": c0,
                "c1_id": c1,
                "native_dimension_id": (
                    "native.dimension:"
                    + digest((dimension or mapping["concept_id"]).encode())[:16]
                    if dimension or mapped_dimension
                    else None
                ),
                "native_dimension_label": dimension or (
                    mapping["concept_id"] if mapped_dimension else None
                ),
                "track": "COFFEE_PROFESSIONAL_SUPERVISION",
                **mapping,
            }
        )

    orientation, details = axis
    if orientation == "COLUMN":
        header_index, resolved_columns = details
        first_descriptor_column = min(resolved_columns)
        carried_prefix: list[str] = [""] * first_descriptor_column
        for row_index, row in enumerate(rows[header_index + 1 :], header_index + 1):
            prefix = []
            for column in range(first_descriptor_column):
                cell = row[column].strip() if column < len(row) else ""
                if cell and numeric(cell) is None:
                    carried_prefix[column] = cell
                if carried_prefix[column]:
                    prefix.append(carried_prefix[column])
            sample = " ".join(dict.fromkeys(prefix))
            if invalid_sample_label(sample):
                continue
            for column, (surface, mapping, dimension) in resolved_columns.items():
                if column < len(row):
                    append_cell("col", row_index, column, sample, surface, mapping, dimension, row[column])
    else:
        row_hits = details
        first_descriptor_row = min(row[0] for row in row_hits)
        header_rows = rows[:first_descriptor_row]
        if not header_rows:
            return []
        for row_index, descriptor_column, surface, mapping, dimension in row_hits:
            row = rows[row_index]
            for column in range(descriptor_column + 1, len(row)):
                sample_parts = []
                for header in header_rows:
                    cell = header[column].strip() if column < len(header) else ""
                    if cell and numeric(cell) is None and cell not in sample_parts:
                        sample_parts.append(cell)
                sample = " ".join(sample_parts)
                if invalid_sample_label(sample):
                    continue
                append_cell("row", row_index, column, sample, surface, mapping, dimension, row[column])
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-report", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    raw = json.loads(args.raw_report.read_text())
    candidates = {
        row["candidate_id"]: row
        for row in json.loads((R10 / "acquisition_manifest.json").read_text())[
            "discovery_candidates"
        ]
    }
    direct, rules = load_direct_registry()
    records = []
    candidate_shapes: dict[str, Counter[str]] = defaultdict(Counter)
    table_shapes: dict[str, set[str]] = defaultdict(set)
    retrievable = 0
    for outcome in raw["candidate_outcomes"]:
        retrieval = outcome.get("retrieval")
        if not retrieval or not outcome.get("source_verified_license"):
            continue
        body_path = args.cache_dir / f"{digest(retrieval['requested_url'].encode())}.body"
        if not body_path.exists():
            continue
        body = body_path.read_bytes()
        try:
            if retrieval["content_type"] in {"text/xml", "application/xml"} or body.lstrip().startswith(b"<?xml"):
                tables, metadata = parse_xml(body)
            elif retrieval["content_type"] == "text/html":
                tables, metadata = parse_html(body)
            else:
                continue
        except Exception:
            continue
        retrievable += 1
        candidate = candidates[outcome["candidate_id"]]
        article_text = metadata["plain_text"]
        for table in tables:
            produced = ontology_records(candidate, outcome, table, direct, rules)
            produced.extend(
                sample_axis_records(candidate, outcome, table, article_text, direct, rules)
            )
            unique = {row["record_id"]: row for row in produced}
            for row in unique.values():
                records.append(row)
                candidate_shapes[candidate["candidate_id"]][row["shape_id"]] += 1
                table_shapes[f"{candidate['candidate_id']}|{table['table_id']}"] .add(row["shape_id"])

    records = sorted({row["record_id"]: row for row in records}.values(), key=lambda row: row["record_id"])
    shape_record_counts = Counter(row["shape_id"] for row in records)
    shape_table_counts = Counter(shape for shapes in table_shapes.values() for shape in shapes)
    shape_group_counts = {
        shape: len(
            {
                row["coffee_group_id"]
                for row in records
                if row["shape_id"] == shape and row.get("coffee_group_id")
            }
        )
        for shape in SHAPES
    }
    report = {
        "contract_version": "r11.stratified-shape-distribution.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_extraction_report_sha256": digest(args.raw_report.read_bytes()),
        "r6_mapping_registry": {
            "path": str((R6 / "semantic_patch.tsv").relative_to(ROOT)),
            "sha256": digest((R6 / "semantic_patch.tsv").read_bytes()),
            "rule_count": len(rules),
        },
        "contracts": SHAPES,
        "guards": {
            "fit_count": 0,
            "new_mapping_rules_created": 0,
            "specificity_increasing_mappings": 0,
            "t4_promoted_to_named_supervision": False,
            "t5_t6_promoted_to_sample_supervision": False,
            "consumer_subjective_data_in_supervision": False,
        },
        "summary": {
            "frozen_candidate_count": len(candidates),
            "candidates_with_parseable_retrieval": retrievable,
            "candidates_with_any_typed_record": len(candidate_shapes),
            "typed_table_count": len(table_shapes),
            "shape_table_counts": dict(sorted(shape_table_counts.items())),
            "shape_record_counts": dict(sorted(shape_record_counts.items())),
            "shape_group_counts_pre_dedup": shape_group_counts,
        },
        "candidate_shape_counts": {
            candidate_id: dict(sorted(counts.items()))
            for candidate_id, counts in sorted(candidate_shapes.items())
        },
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(stable_bytes(report))
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
