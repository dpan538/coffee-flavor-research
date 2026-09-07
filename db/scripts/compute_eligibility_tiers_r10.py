#!/usr/bin/env python3
"""Compute commercial and NON_COMMERCIAL_RESEARCH eligibility independently."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
R10 = ROOT / "db/data/backend-sequential-model-v2/revisions/r10"
DEFAULT_LICENSES = R10 / "resolved_source_licenses.json"
DEFAULT_OUTPUT = R10 / "eligibility_tiers.json"
INPUTS = [
    "db/data/professional-descriptor-staging/PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
    "db/data/post20k-extension-staging/POST20K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
    "db/data/post30k-extension-staging/POST30K_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
    "db/data/post50k-extension-staging/NON_COE_PUBLIC_SAFE_ASSERTION_SIDECAR.tsv",
]
ALLOWED = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-3.0",
    "CC-BY-SA-4.0",
    "CC-BY-NC-4.0",
    "ODbL-1.0",
    "EXPLICIT-NONCOMMERCIAL-RESEARCH-TDM",
}


def git_or_file(relative_path: str) -> tuple[str, str]:
    path = ROOT / relative_path
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    return text, hashlib.sha256(text.encode()).hexdigest()


def is_true(value: str | None) -> bool:
    return (value or "").strip().lower() == "true"


def identified(value: str | None) -> bool:
    token = (value or "").strip().lower()
    return bool(token and "unknown" not in token and "unresolved" not in token)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--licenses", type=Path, default=DEFAULT_LICENSES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    licenses_report = json.loads(args.licenses.read_text(encoding="utf-8"))
    licenses = {row["source_family_id"]: row for row in licenses_report["sources"]}
    all_rows: list[dict[str, str]] = []
    inputs = []
    raw_participant_identity_fields: set[str] = set()
    for relative_path in INPUTS:
        text, sha = git_or_file(relative_path)
        reader = csv.DictReader(io.StringIO(text), delimiter="\t")
        rows = list(reader)
        for field in reader.fieldnames or []:
            lower = field.lower()
            if any(token in lower for token in ("participant", "panelist", "judge")) and not (
                lower.endswith("_sha256") or "_id_sha256" in lower
            ):
                raw_participant_identity_fields.add(field)
        all_rows.extend(rows)
        inputs.append({"path": relative_path, "sha256": sha, "row_count": len(rows)})

    commercial = [row for row in all_rows if is_true(row.get("model_eligible"))]
    eligible: list[dict[str, str]] = []
    excluded_counts: dict[str, int] = {}
    for row in all_rows:
        source = licenses.get(row.get("source_family_id", ""))
        reasons = []
        if not source or source.get("resolved_license") not in ALLOWED:
            reasons.append("LICENSE_NOT_RESOLVED_ALLOWED")
        if source and "-ND-" in (source.get("resolved_license") or ""):
            reasons.append("NO_DERIVATIVES")
        if raw_participant_identity_fields or (
            source and source.get("participant_pii_present")
        ):
            reasons.append("PARTICIPANT_PII")
        if not source or not source.get("attribution_complete"):
            reasons.append("ATTRIBUTION_INCOMPLETE")
        if row.get("descriptor_class") != "STRICT_FLAVOR":
            reasons.append("NOT_STRICT_DESCRIPTOR_LEVEL")
        if not identified(row.get("coffee_identity_id")):
            reasons.append("COFFEE_SAMPLE_NOT_IDENTIFIED")
        if not is_true(row.get("counts_as_assertion")):
            reasons.append("NOT_DEINFLATED_ASSERTION")
        if not reasons:
            eligible.append(row)
        else:
            for reason in set(reasons):
                excluded_counts[reason] = excluded_counts.get(reason, 0) + 1

    by_family: dict[str, int] = {}
    share_alike_count = 0
    for row in eligible:
        family = row["source_family_id"]
        by_family[family] = by_family.get(family, 0) + 1
        if licenses[family].get("share_alike_obligation"):
            share_alike_count += 1

    report: dict[str, Any] = {
        "contract_version": "r10.eligibility-tiers.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inputs": inputs,
        "criteria": {
            "commercial_grade": "UNCHANGED_EXISTING_MODEL_ELIGIBLE_FIELD",
            "non_commercial_research": {
                "license_resolved_from_source": True,
                "allowed_licenses": sorted(ALLOWED),
                "no_derivatives_excluded": True,
                "participant_pii_excluded": True,
                "attribution_required": True,
                "descriptor_level": "STRICT_FLAVOR",
                "identified_coffee_sample_required": True,
                "counts_as_assertion_required": True,
            },
        },
        "pii_schema_check": {
            "raw_participant_identity_fields": sorted(raw_participant_identity_fields),
            "pass": not raw_participant_identity_fields,
            "rule": "participant/panelist/judge fields must be SHA-256-only in admitted public-safe inputs",
        },
        "tiers": {
            "COMMERCIAL_GRADE": {
                "model_eligible_assertion_count": len(commercial),
                "source_family_count": len({row.get("source_family_id") for row in commercial}),
            },
            "NON_COMMERCIAL_RESEARCH": {
                "model_eligible_assertion_count": len(eligible),
                "source_family_count": len(by_family),
                "source_family_assertion_counts": dict(sorted(by_family.items())),
                "share_alike_obligation_assertion_count": share_alike_count,
                "exclusion_reason_counts_nonexclusive": dict(sorted(excluded_counts.items())),
            },
        },
        "resolved_source_licenses": licenses_report["sources"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["tiers"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
