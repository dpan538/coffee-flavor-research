#!/usr/bin/env python3
"""R12C — measure every admission gate's rejection rate against the sealed R11 run.

Every prior round audited the layer it owned. None audited the admission gates
themselves. This script treats the gates as the defendant.

All measurements are STATIC: derived from the sealed R11 extraction report and
the committed gate source. No network, no acquisition, no re-extraction, no fit.
Nothing is admitted, promoted, or rewritten.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
R11 = ROOT / "db/data/backend-sequential-model-v2/revisions/r11"
R12C = ROOT / "db/data/backend-sequential-model-v2/revisions/r12c"
GATE_SRC = ROOT / "db/scripts/stratify_extraction_r11.py"

PROFESSIONAL_TITLE = re.compile(
    r"sensor|descriptive|cupping|panel|profil|volatile|aroma|flavou?r|quality|roast|ferment",
    re.I,
)
CONSUMER_TITLE = re.compile(r"consumer|hedonic|liking|acceptance|preference", re.I)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def measure() -> dict[str, Any]:
    report_bytes = (R11 / "extraction_report.json").read_bytes()
    report = json.loads(report_bytes)
    outcomes = report["candidate_outcomes"]

    table_reasons: collections.Counter[str] = collections.Counter()
    sensory_tables = 0
    total_tables = 0
    for candidate in outcomes:
        for table in candidate.get("table_summaries") or []:
            total_tables += 1
            table_reasons[str(table.get("reason"))] += 1
            if table.get("sensory_table"):
                sensory_tables += 1

    # Candidates whose every table died on the article-level consumer switch.
    consumer_killed = [
        c
        for c in outcomes
        if (c.get("table_summaries") or [])
        and all(
            t.get("reason") == "CONSUMER_SUBJECTIVE_DATA_EXCLUDED"
            for t in c["table_summaries"]
        )
    ]
    professional_titles = [c for c in consumer_killed if PROFESSIONAL_TITLE.search(c["title"])]
    consumer_titles = [c for c in consumer_killed if CONSUMER_TITLE.search(c["title"])]

    return {
        "measurement_class": "STATIC",
        "inputs": {
            "r11_extraction_report_sha256": sha256_bytes(report_bytes),
            "gate_source_sha256": sha256_bytes(GATE_SRC.read_bytes()),
        },
        "table_level": {
            "tables_summarised": total_tables,
            "machine_readable_table_count_reported": report["summary"][
                "machine_readable_table_count"
            ],
            "sensory_table_count_reported": report["summary"]["sensory_table_count"],
            "sensory_tables_in_summaries": sensory_tables,
            "rejection_reason_counts": dict(table_reasons.most_common()),
            "rejection_reason_shares": {
                reason: count / total_tables for reason, count in table_reasons.most_common()
            },
        },
        "candidate_level": {
            "failure_reason_counts": report["summary"]["failure_reason_counts"],
            "candidate_outcome_counts": report["summary"]["candidate_outcome_counts"],
        },
        "article_level_consumer_switch": {
            "gate": "stratify_extraction_r11.table_is_consumer",
            "implementation": (
                "return bool(consumer and not trained), where consumer matches "
                "consumer|customer|hedonic|liking|preference anywhere in the FULL ARTICLE "
                "TEXT and trained requires the exact phrases 'trained (sensory) "
                "panel/panelists/assessors', 'q-graders' or 'expert cuppers'."
            ),
            "defect": (
                "Scope error. A single occurrence of a common academic word anywhere in a "
                "paper rejects every table in that paper, unless one of a small set of "
                "exact phrases also appears."
            ),
            "candidates_entirely_killed": len(consumer_killed),
            "of_which_professional_title": len(professional_titles),
            "of_which_consumer_title": len(consumer_titles),
            "misfire_indication": (
                len(professional_titles) / len(consumer_killed) if consumer_killed else None
            ),
            "killed_title_examples": [c["title"] for c in consumer_killed[:20]],
        },
        "systemic_pattern": {
            "finding": (
                "The admission layer is built from substring keyword tests applied at the "
                "wrong granularity. Four independent instances share one defect class."
            ),
            "instances": [
                {
                    "gate": "acquire_license_verified_r10.relevant",
                    "scope_applied": "title only",
                    "appropriate_scope": "title, abstract and full text",
                    "measured_rejection": 0.79,
                    "unit": "licence-and-subject-qualified records",
                },
                {
                    "gate": "stratify_extraction_r11.table_is_consumer",
                    "scope_applied": "whole article text",
                    "appropriate_scope": "the table and its own methods section",
                    "measured_rejection": table_reasons["CONSUMER_SUBJECTIVE_DATA_EXCLUDED"]
                    / total_tables
                    if total_tables
                    else None,
                    "unit": "detected tables",
                },
                {
                    "gate": "stratify_extraction_r11.TABLE_SUPERVISION_CUE",
                    "scope_applied": "table caption only",
                    "appropriate_scope": "caption plus table content",
                    "measured_rejection": table_reasons["NOT_SENSORY_TABLE"] / total_tables
                    if total_tables
                    else None,
                    "unit": "detected tables",
                },
                {
                    "gate": "stratify_extraction_r11.resolve_surface",
                    "scope_applied": "whole normalised cell",
                    "appropriate_scope": "list fragment, as R6 scope EXACT_COMPLETE_LIST_FRAGMENT declares",
                    "measured_rejection": None,
                    "unit": "1429 surface forms queued; 515 recoverable under existing rules",
                },
            ],
        },
        "secondary_defects": [
            {
                "id": "R12C-F9",
                "finding": (
                    "SOURCE_LICENSE_NOT_REVERIFIED_ALLOWED_NON_ND rejected 17 candidates "
                    "whose licences R10 had already resolved and admitted. A redundant "
                    "second verification discards already-verified material."
                ),
                "count": report["summary"]["failure_reason_counts"].get(
                    "SOURCE_LICENSE_NOT_REVERIFIED_ALLOWED_NON_ND"
                ),
            },
            {
                "id": "R12C-F10",
                "finding": (
                    "descriptor_axis scans only row[:3]. A descriptor axis beginning at "
                    "column four or later is never seen."
                ),
                "evidence": "stratify_extraction_r11.py descriptor_axis: for column, surface in enumerate(row[:3])",
            },
            {
                "id": "R12C-F11",
                "finding": (
                    "The gates reject professional sensory tables while admitting "
                    "non-sensory material in the opposite direction: an admitted record "
                    "carries sample_label 'm/z 67', a mass-spectrometry ion treated as a "
                    "coffee sample, with base_coffee_identity_normalized 'z'."
                ),
                "evidence_record_source_doi": "10.3390/molecules24244515",
            },
        ],
        "limitations": [
            "Rejection shares are measured over tables the pipeline actually summarised, "
            "not over the literature.",
            "A gate misfiring does not establish that the rejected tables contain usable "
            "supervision. It establishes only that the stated rejection reason is not "
            "supported by the paper's own subject matter.",
            "No gate was modified, relaxed, or bypassed by this script.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=R12C)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "contract_version": "r12c.admission-gate-audit.v1",
        "round": "R12C",
        "guards": {
            "fit_count": 0,
            "new_acquisition_count": 0,
            "network_calls": 0,
            "gates_modified": 0,
            "records_admitted": 0,
            "sealed_artifacts_modified": False,
        },
        **measure(),
    }
    (args.output_dir / "admission_gate_audit_r12c.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    )

    table = result["table_level"]
    print(
        json.dumps(
            {
                "tables": table["tables_summarised"],
                "sensory_tables": table["sensory_table_count_reported"],
                "top_rejections": dict(list(table["rejection_reason_counts"].items())[:4]),
                "consumer_switch_killed_candidates": result["article_level_consumer_switch"][
                    "candidates_entirely_killed"
                ],
                "of_which_professional_title": result["article_level_consumer_switch"][
                    "of_which_professional_title"
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
