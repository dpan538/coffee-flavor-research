#!/usr/bin/env python3
"""R12C — repaired admission gates, run as a shadow against the sealed 248.

Repairs five defects located by the R12C audit. Runs over the SAME frozen 248
candidates and the SAME cached full text as R11. Writes a delta report only.
The sealed R11 artefacts are never modified and no record is promoted into any
training corpus.

REPAIRS
-------
G1  table_is_consumer scope error (44.6% of table rejections)
    Old: any of consumer|customer|hedonic|liking|preference ANYWHERE in the full
    article text rejects EVERY table in that article, unless one of a small set
    of exact phrases also appears.
    New: the consumer signal must appear in the table's own caption, or the
    article must lack any professional-panel signal under a materially widened
    professional vocabulary.

G2  TABLE_SUPERVISION_CUE caption-only gate (27.3% of table rejections)
    Old: caption must match a keyword list.
    New: caption match OR the table's own axis carries at least two resolvable
    descriptor/dimension terms. Content is stronger evidence than a caption.

G3  Redundant licence re-verification (17 candidates)
    Old: a candidate is skipped unless source_verified_license is truthy, even
    when R10 already resolved and admitted an allowed non-ND licence.
    New: trust R10's resolution when it is present and allowed non-ND.

G4  descriptor_axis column window (unmeasured)
    Old: enumerate(row[:3]) - a descriptor axis starting at column four is never
    seen.
    New: widened window.

G5  NEW GUARD, tightening not loosening (defect F11)
    R11 admitted sample_label 'm/z 67' as a coffee sample. Loosening G1-G4
    without this would admit more instrumental rows. Adds rejection of mass
    spectrometry, chromatography and spectroscopy identifiers used as samples.

Guards: no fit, no acquisition, no network, no sealed artefact modified, no
training corpus written, no R6 rule created, no relation edge created.
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

# ---------------------------------------------------------------- G1

CONSUMER_CAPTION = re.compile(
    r"consumer|hedonic|liking|acceptab|acceptance|preference|purchase intent|"
    r"just[- ]about[- ]right|\bjar\b|emotion",
    re.I,
)

# Widened professional-panel vocabulary. The original required one of four exact
# phrases; real papers describe professional panels in many more ways.
PROFESSIONAL_PANEL = re.compile(
    r"trained\s+(?:sensory\s+)?(?:panel|panelist|panellist|assessor|judge)|"
    r"experienced\s+(?:sensory\s+)?(?:panel|panelist|panellist|assessor|judge|taster|cupper)|"
    r"expert\s+(?:panel|panelist|panellist|assessor|judge|taster|cupper)|"
    r"q[\s-]?graders?|certified\s+cupper|professional\s+cupper|"
    r"quantitative\s+descriptive\s+analysis|\bqda\b|descriptive\s+panel|"
    r"iso\s*8586|iso\s*13299|sca\s+(?:cupping\s+)?protocol|"
    r"specialty\s+coffee\s+association\s+(?:cupping|protocol)|"
    r"cupping\s+(?:protocol|form|score|session)|panel\s+training|trained\s+for",
    re.I,
)


def table_is_consumer_repaired(caption: str, article_text: str) -> bool:
    """G1: judge the table, not the article."""
    if CONSUMER_CAPTION.search(caption):
        return True
    if PROFESSIONAL_PANEL.search(article_text):
        return False
    consumer = re.search(r"consumer|customer|hedonic|liking|preference", article_text, re.I)
    return bool(consumer)


# ---------------------------------------------------------------- G2


def table_has_descriptor_content(
    rows: list[list[str]],
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
    minimum: int = 2,
) -> bool:
    """G2: content evidence that this is a sensory table."""
    hits = 0
    for row in rows[:40]:
        for surface in row[:12]:
            token = norm(surface)
            if not token:
                continue
            if token in direct or token in rules or token in base.NATIVE_DIMENSIONS:
                hits += 1
                if hits >= minimum:
                    return True
    return False


# ---------------------------------------------------------------- G5

INSTRUMENTAL_SAMPLE_LABEL = re.compile(
    r"^\s*(?:"
    r"m\s*/\s*z|mz\s*\d|"
    r"(?:l?ri|kovats?|retention\s*(?:index|time)|rt)\b|"
    r"cas(?:\s*(?:no|number|rn))?\b|"
    r"peak\s*(?:no|number|#)?\s*\d|"
    r"wavelength|\d+\s*nm\b|"
    r"\bpc\s*\d|\bpls\b|\blv\s*\d|"
    r"fragment\s*ion|ion\s*\d|"
    r"compound\s*\d+$"
    r")",
    re.I,
)


CHEMICAL_SOLUTION_LABEL = re.compile(
    r"\d\s*(?:mmol|mol|mg|µg|ug|ng|ppm|ppb|g)\s*/\s*(?:l|ml|kg|g)\b|"
    r"\bmmol\b|\bkda\b|\bcqa\b|\bhmw\b|\blmw\b|"
    r"\b(?:caffeine|trigonelline|chlorogenic|quinic|melanoidin)\b.*\d|"
    r"^\d[-,\d]*\s*-\s*[a-z]{2,4}\*?$",
    re.I,
)

STATISTICS_LABEL = re.compile(
    r"^\s*(?:#|no\.?|number)\s*(?:of\s+)?samples?\b|"
    r"^\s*(?:range|mean|median|average|total|sum|std|sd|sem|se|cv|min|max|"
    r"minimum|maximum|overall\s+stats?)\b|"
    r"mean\s*[±+]|±\s*sd",
    re.I,
)


def sample_label_is_instrumental(
    label: str,
    direct: dict[str, str] | None = None,
    rules: dict[str, dict[str, str]] | None = None,
) -> tuple[bool, str]:
    """G5: reject non-coffee-sample labels. Returns (blocked, class)."""
    if INSTRUMENTAL_SAMPLE_LABEL.search(label):
        return True, "INSTRUMENTAL_IDENTIFIER"
    if CHEMICAL_SOLUTION_LABEL.search(label):
        return True, "CHEMICAL_SOLUTION"
    if STATISTICS_LABEL.search(label):
        return True, "STATISTICS_ROW"

    token = norm(label)
    if not token:
        return False, "OK"

    # Orientation error: a descriptor or dimension term is not a coffee sample.
    if token in base.NATIVE_DIMENSIONS:
        return True, "DESCRIPTOR_AS_SAMPLE"
    if direct is not None and token in direct:
        return True, "DESCRIPTOR_AS_SAMPLE"
    if rules is not None and token in rules:
        return True, "DESCRIPTOR_AS_SAMPLE"
    if token in {"descriptor", "descriptors", "attribute", "attributes", "sensory attribute"}:
        return True, "AXIS_HEADER_AS_SAMPLE"

    if token.isdigit() or len(token) <= 1:
        return True, "NO_COFFEE_IDENTITY"
    return False, "OK"


# ---------------------------------------------------------------- shadow run


def repaired_table_admits(
    table: dict[str, Any],
    article_text: str,
    candidate: dict[str, Any],
    direct: dict[str, str],
    rules: dict[str, dict[str, str]],
) -> tuple[bool, str]:
    """Apply the repaired gate stack. Returns (admitted, reason)."""
    rows = table["rows"]
    caption = f"{table['caption']} {table['label']}"
    if not rows:
        return False, "EMPTY_TABLE"

    cue = bool(base.TABLE_SUPERVISION_CUE.search(caption))
    content = table_has_descriptor_content(rows, direct, rules)
    if not cue and not content:
        return False, "NOT_SENSORY_TABLE_CAPTION_AND_CONTENT"

    if any(
        re.search(pattern, caption, re.I) for pattern in base.ANALYTIC_NOT_SAMPLE_SUPERVISION
    ):
        return False, "ANALYTIC_OR_REFERENCE_TABLE_NOT_SUPERVISION"
    if re.search(r"guide to sensory|reference standards?|training lexicon", caption, re.I):
        return False, "REFERENCE_LEXICON_TABLE"
    if re.search(r"compound|\boav\b|\baeda\b|chromatograph|gc[- /]", caption, re.I):
        return False, "CHEMICAL_TABLE"
    if base.noncoffee_sample_domain(candidate["title"], caption):
        return False, "NONCOFFEE_DOMAIN"
    if table_is_consumer_repaired(caption, article_text):
        return False, "CONSUMER_SUBJECTIVE_DATA_EXCLUDED"

    return True, "ADMITTED_BY_REPAIRED_GATES"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=CACHE)
    parser.add_argument("--output-dir", type=Path, default=R12C)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw_bytes = (R11 / "extraction_report.json").read_bytes()
    raw = json.loads(raw_bytes)
    manifest = json.loads((R10 / "acquisition_manifest.json").read_text())
    candidates = {row["candidate_id"]: row for row in manifest["discovery_candidates"]}
    direct, rules = base.load_direct_registry()

    old_reason_by_table: dict[str, str] = {}
    for outcome in raw["candidate_outcomes"]:
        for summary in outcome.get("table_summaries") or []:
            key = f"{outcome['candidate_id']}|{summary['table_id']}"
            old_reason_by_table[key] = str(summary.get("reason"))

    g3_recovered: list[str] = []
    new_reasons: collections.Counter[str] = collections.Counter()
    delta_admitted: list[dict[str, Any]] = []
    instrumental_blocked: list[dict[str, Any]] = []
    tables_seen = 0
    candidates_processed = 0

    for outcome in raw["candidate_outcomes"]:
        retrieval = outcome.get("retrieval")
        if not retrieval:
            continue

        # G3: trust R10's resolution rather than demanding re-verification.
        verified = outcome.get("source_verified_license")
        r10_license = outcome.get("resolved_license_r10")
        trusted = bool(verified) or (
            bool(r10_license) and "ND" not in str(r10_license).upper().split("-")
        )
        if not trusted:
            continue
        if not verified and r10_license:
            g3_recovered.append(outcome["candidate_id"])

        body_path = args.cache_dir / f"{digest(retrieval['requested_url'].encode())}.body"
        if not body_path.exists():
            continue
        body = body_path.read_bytes()
        try:
            content_type = retrieval.get("content_type") or ""
            if content_type in {"text/xml", "application/xml"} or body.lstrip().startswith(
                b"<?xml"
            ):
                tables, metadata = parse_xml(body)
            elif content_type == "text/html":
                tables, metadata = parse_html(body)
            else:
                continue
        except Exception as exc:  # noqa: BLE001 - recorded, never silent
            new_reasons[f"PARSE_FAILED:{type(exc).__name__}"] += 1
            continue

        candidates_processed += 1
        candidate = candidates[outcome["candidate_id"]]
        article_text = metadata["plain_text"]

        for table in tables:
            tables_seen += 1
            admitted, reason = repaired_table_admits(
                table, article_text, candidate, direct, rules
            )
            new_reasons[reason] += 1
            key = f"{outcome['candidate_id']}|{table['table_id']}"
            old_reason = old_reason_by_table.get(key)

            if admitted and old_reason and old_reason != "None":
                # G5 applies at row level: would the repaired stack admit rows whose
                # sample labels are instrumental identifiers?
                labels = [r[0] for r in table["rows"][1:] if r and r[0].strip()]
                blocked = [
                    (lab, cls)
                    for lab in labels
                    for ok, cls in [sample_label_is_instrumental(lab, direct, rules)]
                    if ok
                ]
                block_classes = collections.Counter(cls for _, cls in blocked)
                clean = len(labels) - len(blocked)
                entry = {
                    "candidate_id": outcome["candidate_id"],
                    "doi": outcome.get("doi"),
                    "title": outcome.get("title", "")[:160],
                    "table_id": table["table_id"],
                    "old_reason": old_reason,
                    "sample_label_sample": labels[:6],
                    "row_label_total": len(labels),
                    "row_labels_blocked_by_g5": len(blocked),
                    "row_labels_surviving": clean,
                    "g5_block_classes": dict(block_classes),
                    "table_fully_blocked_by_g5": clean == 0 and len(labels) > 0,
                }
                delta_admitted.append(entry)
                if blocked:
                    instrumental_blocked.append(entry)

    report = {
        "contract_version": "r12c.repaired-gate-shadow.v1",
        "round": "R12C",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "SHADOW_MEASUREMENT_ONLY",
        "guards": {
            "fit_count": 0,
            "new_acquisition_count": 0,
            "network_calls": 0,
            "sealed_artifacts_modified": False,
            "training_corpus_written": False,
            "r6_rules_created": 0,
            "formal_relation_edges_created": 0,
            "records_promoted": 0,
        },
        "inputs": {
            "r11_extraction_report_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "candidates_processed": candidates_processed,
            "tables_seen": tables_seen,
        },
        "repairs": {
            "G1_consumer_scope": "table caption, or absence of any professional-panel signal under a widened vocabulary",
            "G2_supervision_cue": "caption match OR >=2 resolvable descriptor/dimension terms in the table itself",
            "G3_licence_trust": "trust R10 resolved non-ND licence instead of demanding re-verification",
            "G4_descriptor_axis_window": "widened from row[:3] (applied in G2 content scan as row[:12])",
            "G5_instrumental_sample_guard": "NEW rejection of m/z, RI/RT, CAS, peak, wavelength, PC/LV identifiers used as samples",
        },
        "results": {
            "old_table_rejection_counts": dict(
                collections.Counter(old_reason_by_table.values()).most_common()
            ),
            "new_table_reason_counts": dict(new_reasons.most_common()),
            "g3_candidates_recovered": len(g3_recovered),
            "g3_candidate_ids": sorted(g3_recovered),
            "tables_newly_admitted": len(delta_admitted),
            "tables_newly_admitted_containing_blocked_labels": len(instrumental_blocked),
            "tables_newly_admitted_fully_blocked_by_g5": sum(
                1 for e in delta_admitted if e["table_fully_blocked_by_g5"]
            ),
            "tables_newly_admitted_with_surviving_rows": sum(
                1 for e in delta_admitted if not e["table_fully_blocked_by_g5"]
            ),
            "g5_block_class_totals": dict(
                collections.Counter(
                    cls
                    for e in delta_admitted
                    for cls, n in e["g5_block_classes"].items()
                    for _ in range(n)
                ).most_common()
            ),
        },
        "newly_admitted_tables": sorted(
            delta_admitted, key=lambda r: (r["candidate_id"], r["table_id"])
        )[:120],
        "limitations": [
            "Shadow measurement of gate behaviour only. No record was extracted, mapped, "
            "grouped, admitted, or written to any corpus.",
            "A table passing the repaired gates is not established supervision. Downstream "
            "descriptor-axis resolution, sample identity and grouping still apply.",
            "G5 is reported as a row-level count on newly admitted tables; it was not used "
            "to retroactively re-audit the sealed R11 admissions.",
            "Widening the professional-panel vocabulary is a judgement about sensory "
            "methods reporting. It should be reviewed before any of this is promoted.",
        ],
    }

    (args.output_dir / "repaired_gate_shadow_r12c.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    print(
        json.dumps(
            {
                "candidates_processed": candidates_processed,
                "tables_seen": tables_seen,
                "g3_candidates_recovered": len(g3_recovered),
                "tables_newly_admitted": len(delta_admitted),
                "newly_admitted_with_blocked_labels": len(instrumental_blocked),
                "fully_blocked_by_g5": sum(1 for e in delta_admitted if e["table_fully_blocked_by_g5"]),
                "with_surviving_rows": sum(1 for e in delta_admitted if not e["table_fully_blocked_by_g5"]),
                "new_reason_top": dict(new_reasons.most_common(5)),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
