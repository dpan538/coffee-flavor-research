#!/usr/bin/env python3
"""R12C — diagnose the table-orientation defect F12 at its source.

The repaired-gate shadow run found 95 row labels that are descriptor or
dimension terms rather than coffee samples. This script inspects the actual
table structures behind those cases and determines which branch of
stratify_extraction_r11.descriptor_axis produced the wrong axis.

STATIC only: reads the sealed R11 report and the existing full-text cache.
No network, no acquisition, no admission, no fit, no sealed artefact modified.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "db/scripts"))

import stratify_extraction_r11 as base  # noqa: E402
from extract_candidates_r11 import digest, norm, parse_html, parse_xml  # noqa: E402

R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
R12C = ROOT / "db/data/backend-sequential-model-v2/revisions/r12c"
CACHE = Path("/private/tmp/coffee-flavor-r11-fulltext-cache")


FRAGMENT_SEPARATORS = re.compile(r"[,;/]")
CITATION_MARKER = re.compile(r"\[\s*\d+(?:\s*[,-]\s*\d+)*\s*\]")
PARENTHETICAL = re.compile(r"\([^)]*\)")
TRAILING_FOOTNOTE = re.compile(r"[\s ]*(?:\*+|\d+(?:\s*,\s*\d+)*)\s*$")


def fragments(surface: str) -> list[str]:
    """Same tokenisation as reextract_tokenised_mapping_r12c."""
    cleaned = CITATION_MARKER.sub(" ", surface)
    cleaned = PARENTHETICAL.sub(" ", cleaned)
    out = []
    for part in FRAGMENT_SEPARATORS.split(cleaned):
        part = TRAILING_FOOTNOTE.sub("", part.strip()).strip(" .-")
        if part:
            out.append(part)
    return out


def descriptor_like(surface: str, direct: dict, rules: dict) -> bool:
    """Whole-cell exact match, exactly as the pipeline does it today."""
    token = norm(surface)
    return bool(token) and (
        token in direct or token in rules or token in base.NATIVE_DIMENSIONS
    )


def descriptor_like_tokenised(surface: str, direct: dict, rules: dict) -> bool:
    """Same test after list-fragment tokenisation. Repair candidate only."""
    if descriptor_like(surface, direct, rules):
        return True
    return any(descriptor_like(part, direct, rules) for part in fragments(surface))


def axis_would_resolve_tokenised(
    rows: list[list[str]], direct: dict, rules: dict
) -> dict[str, Any]:
    """Would an axis be found if resolution tokenised list fragments?

    Mirrors descriptor_axis's counting thresholds without calling it, so the
    unmodified function is never affected.
    """
    header = rows[0] if rows else []
    header_hits_now = sum(1 for c in header[1:] if descriptor_like(c, direct, rules))
    header_hits_tok = sum(
        1 for c in header[1:] if descriptor_like_tokenised(c, direct, rules)
    )
    col_hits_now = 0
    col_hits_tok = 0
    for row in rows[1:]:
        if not row:
            continue
        # the pipeline only inspects the first three columns
        window = row[:3]
        if any(descriptor_like(c, direct, rules) for c in window):
            col_hits_now += 1
        if any(descriptor_like_tokenised(c, direct, rules) for c in window):
            col_hits_tok += 1
    return {
        "header_descriptor_hits_wholecell": header_hits_now,
        "header_descriptor_hits_tokenised": header_hits_tok,
        "first_window_descriptor_rows_wholecell": col_hits_now,
        "first_window_descriptor_rows_tokenised": col_hits_tok,
        "would_meet_threshold_wholecell": header_hits_now >= 2 or col_hits_now >= 2,
        "would_meet_threshold_tokenised": header_hits_tok >= 2 or col_hits_tok >= 2,
    }


def profile_table(
    table: dict[str, Any], direct: dict, rules: dict
) -> dict[str, Any]:
    """Describe both axes independently, without deciding."""
    rows = table["rows"]
    if not rows:
        return {"empty": True}

    header = rows[0] if rows else []
    header_descriptor_cells = sum(
        1 for c in header[1:] if descriptor_like(c, direct, rules)
    )
    first_col = [r[0] for r in rows[1:] if r]
    first_col_descriptor_cells = sum(
        1 for c in first_col if descriptor_like(c, direct, rules)
    )

    axis = base.descriptor_axis(rows, direct, rules)
    chosen = axis[0] if axis else None
    tokenised = axis_would_resolve_tokenised(rows, direct, rules)

    # What the chosen orientation implies the sample labels are.
    if chosen == "COLUMN":
        header_index = axis[1][0]
        implied_samples = [r[0] for r in rows[header_index + 1 :] if r and r[0].strip()]
    elif chosen == "ROW":
        implied_samples = [c for c in header[1:] if c.strip()]
    else:
        implied_samples = []

    implied_sample_descriptor_count = sum(
        1 for s in implied_samples if descriptor_like(s, direct, rules)
    )

    return {
        "empty": False,
        "row_count": len(rows),
        "col_count": max((len(r) for r in rows), default=0),
        "header_descriptor_cells": header_descriptor_cells,
        "header_total_cells": max(len(header) - 1, 0),
        "first_column_descriptor_cells": first_col_descriptor_cells,
        "first_column_total_cells": len(first_col),
        "chosen_axis": chosen,
        "implied_sample_count": len(implied_samples),
        "implied_samples_that_are_descriptors": implied_sample_descriptor_count,
        "implied_sample_contamination_rate": (
            implied_sample_descriptor_count / len(implied_samples)
            if implied_samples
            else None
        ),
        "implied_sample_examples": implied_samples[:6],
        "header_examples": [c for c in header[:6]],
        "first_column_examples": first_col[:6],
        "tokenised_axis_test": tokenised,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=CACHE)
    parser.add_argument("--output-dir", type=Path, default=R12C)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw_bytes = (R11 / "extraction_report.json").read_bytes()
    raw = json.loads(raw_bytes)
    direct, rules = base.load_direct_registry()

    profiles: list[dict[str, Any]] = []
    axis_counts: collections.Counter[str] = collections.Counter()
    contaminated = 0
    both_axes_descriptor = 0

    for outcome in raw["candidate_outcomes"]:
        retrieval = outcome.get("retrieval")
        if not retrieval:
            continue
        body_path = args.cache_dir / f"{digest(retrieval['requested_url'].encode())}.body"
        if not body_path.exists():
            continue
        body = body_path.read_bytes()
        try:
            content_type = retrieval.get("content_type") or ""
            if content_type in {"text/xml", "application/xml"} or body.lstrip().startswith(
                b"<?xml"
            ):
                tables, _ = parse_xml(body)
            elif content_type == "text/html":
                tables, _ = parse_html(body)
            else:
                continue
        except Exception:
            continue

        for table in tables:
            profile = profile_table(table, direct, rules)
            if profile.get("empty"):
                continue
            axis_counts[str(profile["chosen_axis"])] += 1
            profile.update(
                {
                    "candidate_id": outcome["candidate_id"],
                    "doi": outcome.get("doi"),
                    "title": (outcome.get("title") or "")[:140],
                    "table_id": table["table_id"],
                }
            )
            profiles.append(profile)
            if profile["chosen_axis"] is None:
                continue
            rate = profile["implied_sample_contamination_rate"]
            if rate:
                contaminated += 1
            if (
                profile["header_descriptor_cells"] >= 2
                and profile["first_column_descriptor_cells"] >= 2
            ):
                both_axes_descriptor += 1

    # Vocabulary-gap measurement: for tables with no axis, how much of their
    # candidate descriptor vocabulary is simply absent from the registry?
    recognisable = set(direct) | set(rules) | set(base.NATIVE_DIMENSIONS)
    unrecognised_terms: collections.Counter[str] = collections.Counter()
    for p_ in profiles:
        if p_["chosen_axis"]:
            continue
        for cell in (p_["first_column_examples"] or []) + (p_["header_examples"] or []):
            for frag in ([cell] + fragments(cell)):
                t = norm(frag)
                if t and t not in recognisable and 2 <= len(t) <= 40 and not t.isdigit():
                    unrecognised_terms[t] += 1

    undecided = [p for p in profiles if not p["chosen_axis"]]
    tokenised_recoverable = [
        p for p in undecided if p["tokenised_axis_test"]["would_meet_threshold_tokenised"]
    ]
    decided = [p for p in profiles if p["chosen_axis"]]
    fully_contaminated = [
        p for p in decided if (p["implied_sample_contamination_rate"] or 0) >= 0.8
    ]

    report = {
        "contract_version": "r12c.orientation-diagnosis.v1",
        "round": "R12C",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "guards": {
            "fit_count": 0,
            "new_acquisition_count": 0,
            "network_calls": 0,
            "records_admitted": 0,
            "sealed_artifacts_modified": False,
            "gates_modified": 0,
        },
        "inputs": {"r11_extraction_report_sha256": hashlib.sha256(raw_bytes).hexdigest()},
        "axis_decision_counts": dict(axis_counts.most_common()),
        "tables_with_a_decided_axis": len(decided),
        "tables_whose_implied_samples_include_descriptors": contaminated,
        "tables_with_descriptor_terms_on_BOTH_axes": both_axes_descriptor,
        "tables_at_least_80pct_contaminated": len(fully_contaminated),
        "tables_with_no_axis_decision": len(undecided),
        "tables_with_no_axis_recoverable_by_tokenisation": len(tokenised_recoverable),
        "tokenisation_axis_recovery_rate": (
            len(tokenised_recoverable) / len(undecided) if undecided else None
        ),
        "vocabulary_gap": {
            "recognisable_vocabulary_size": len(recognisable),
            "registry_concepts": len(direct),
            "frozen_r6_rules": len(rules),
            "native_dimensions": len(base.NATIVE_DIMENSIONS),
            "distinct_unrecognised_terms_on_axisless_tables": len(unrecognised_terms),
            "top_unrecognised_terms": dict(unrecognised_terms.most_common(40)),
            "interpretation": (
                "descriptor_axis needs two or more recognisable terms on one axis. The "
                "recognisable vocabulary is the union of the concept registry, the frozen "
                "R6 rules and NATIVE_DIMENSIONS. Terms outside that union are invisible "
                "to the axis test regardless of tokenisation or gate repair."
            ),
        },
        "tokenisation_recovery_examples": [
            {
                "title": p["title"],
                "table_id": p["table_id"],
                "first_column_examples": p["first_column_examples"],
                "header_examples": p["header_examples"],
                "test": p["tokenised_axis_test"],
            }
            for p in tokenised_recoverable[:15]
        ],
        "defect": {
            "id": "R12C-F12",
            "location": "stratify_extraction_r11.descriptor_axis",
            "rule": (
                "The function returns COLUMN whenever any header row resolves two or "
                "more descriptor columns with numeric rows beneath, and only falls back "
                "to ROW otherwise. The choice is unconditional: it never compares the "
                "two axes against each other."
            ),
            "consequence": (
                "When descriptor terms appear on BOTH axes, COLUMN wins by construction "
                "and the descriptor-bearing first column is then read as the sample "
                "label list, producing sample labels such as Aroma, Bitterness and Umami."
            ),
            "proposed_discriminator": (
                "Compare descriptor density on both axes and select the axis with the "
                "higher density; require the opposite axis to be substantially free of "
                "descriptor terms before accepting the decision. Not implemented here."
            ),
        },
        "worst_cases": sorted(
            fully_contaminated,
            key=lambda p: -(p["implied_sample_count"] or 0),
        )[:25],
        "limitations": [
            "Descriptor-likeness is measured against the existing 56-concept registry, "
            "42 R6 rules and NATIVE_DIMENSIONS. A term outside all three is not counted, "
            "so contamination is a lower bound.",
            "No orientation decision was changed. descriptor_axis was called unmodified.",
            "Contamination indicates a wrong axis, not that the table lacks usable data.",
        ],
    }

    (args.output_dir / "orientation_diagnosis_r12c.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    print(
        json.dumps(
            {
                "axis_decision_counts": report["axis_decision_counts"],
                "decided": len(decided),
                "implied_samples_include_descriptors": contaminated,
                "descriptor_terms_on_both_axes": both_axes_descriptor,
                "at_least_80pct_contaminated": len(fully_contaminated),
                "no_axis_decision": len(undecided),
                "no_axis_recoverable_by_tokenisation": len(tokenised_recoverable),
                "recognisable_vocabulary_size": len(recognisable),
                "distinct_unrecognised_terms": len(unrecognised_terms),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
