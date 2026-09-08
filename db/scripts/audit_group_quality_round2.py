#!/usr/bin/env python3
"""Round 2 — audit what the measured supervision groups are actually made of.

The conversion measurement reported 113 groups from 300 candidates and the
operator presented that as a ninefold improvement over R11 without checking the
composition of the groups. Two spot checks then showed the two largest
contributors were an e-liquid flavour wheel paper and a near-infrared
spectroscopy review, together supplying about half the groups.

This script audits every group against two questions the headline skipped:

  1. Does the group come from a paper that is actually about coffee sensory
     evaluation, or from an off-topic paper that mentions coffee?
  2. Is the descriptor evidence NAMED (sensory.*) or only DIMENSION-level
     (acidity, body, aroma), which is a different supervision type and does not
     serve the product's named-descriptor task?

Measurement only. Nothing admitted, no corpus written, fit count 0.
"""

from __future__ import annotations

import argparse
from collections import Counter
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
from extract_candidates_r11 import norm, numeric, parse_xml  # noqa: E402
from repaired_gates_r12c import repaired_table_admits, sample_label_is_instrumental  # noqa: E402
from measure_conversion_round2 import resolve_repaired  # noqa: E402

R2 = ROOT / "db/data/backend-sequential-model-v2/revisions/round2"
CACHE = Path("/private/tmp/coffee-flavor-round2-fulltext-cache")

# A paper is on-subject when its own title commits to coffee. An abstract
# mention is what let the e-liquid and spectroscopy papers through at capture.
COFFEE_TITLE = re.compile(r"coffee|coffea|arabica|robusta|canephora|espresso|cascara", re.I)
# Titles that name a different subject the paper is actually about.
OFF_SUBJECT_TITLE = re.compile(
    r"e-?liquid|e-?cigarette|vap(?:e|ing)|tobacco|nicotine|smoking|"
    r"beer|wine|tea\b|cocoa|chocolate bar|bread|meat|dairy|infant|"
    r"metabolic syndrome|cardiovascular|mortality|pregnan|cancer",
    re.I,
)
REVIEW_TITLE = re.compile(r"\ba review\b|systematic review|meta-analysis|bibliometric", re.I)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--conversion", type=Path,
                        default=R2 / "conversion_measurement_epmc.json")
    parser.add_argument("--output-dir", type=Path, default=R2)
    args = parser.parse_args()

    conv = json.loads(args.conversion.read_text())
    manifest = json.loads((R2 / "capture_manifest.json").read_text())
    by_doi = {r["doi"]: r for r in manifest["discovery_candidates"] if r.get("doi")}
    direct, rules = base.load_direct_registry()

    yielded = [r for r in conv["per_candidate"] if r.get("outcome") == "YIELDED_GROUPS"]
    audit: list[dict[str, Any]] = []
    totals = Counter()

    for row in yielded:
        doi = row.get("doi")
        cand = by_doi.get(doi)
        title = (cand or {}).get("title", "")
        url = re.sub(r"/rest/PMC/(PMC\d+)/fullTextXML", r"/rest/\1/fullTextXML",
                     (cand or {}).get("license_source_url", ""))
        cache = CACHE / f"{hashlib.sha256(url.encode()).hexdigest()}.xml"

        named = dims = broad = 0
        group_ids: set[str] = set()
        if cache.exists():
            try:
                tables, meta = parse_xml(cache.read_bytes())
            except Exception:  # noqa: BLE001
                tables, meta = [], {}
            for table in tables:
                ok, _ = repaired_table_admits(table, meta.get("plain_text", ""),
                                              cand or {}, direct, rules)
                if not ok:
                    continue
                concepts: set[str] = set()
                for r_ in table["rows"][:60]:
                    for cell in r_[:14]:
                        concepts |= set(resolve_repaired(cell, direct, rules))
                if len(concepts) < 2:
                    continue
                named += sum(1 for c in concepts if c.startswith("sensory."))
                dims += sum(1 for c in concepts if c.startswith("dimension."))
                broad += sum(1 for c in concepts
                             if c.startswith(("broad.", "attribute.")))
                for r_ in table["rows"][1:]:
                    if not r_ or not r_[0].strip():
                        continue
                    blocked, _ = sample_label_is_instrumental(r_[0], direct, rules)
                    if blocked or numeric(r_[0]) is not None:
                        continue
                    if base.INVALID_SAMPLE_LABEL.search(norm(r_[0])):
                        continue
                    group_ids.add(norm(r_[0]))

        on_subject = bool(COFFEE_TITLE.search(title))
        off_subject = bool(OFF_SUBJECT_TITLE.search(title))
        is_review = bool(REVIEW_TITLE.search(title))
        verdict = (
            "OFF_SUBJECT" if off_subject or not on_subject
            else "REVIEW_NOT_PRIMARY_DATA" if is_review
            else "ON_SUBJECT"
        )
        entry = {
            "doi": doi, "title": title[:120], "groups_reported": row.get("groups", 0),
            "groups_recounted": len(group_ids), "verdict": verdict,
            "named_descriptor_concepts": named,
            "dimension_concepts": dims,
            "broad_concepts": broad,
            "has_named_evidence": named > 0,
        }
        audit.append(entry)
        totals[verdict] += row.get("groups", 0)
        if entry["has_named_evidence"]:
            totals["groups_with_named_evidence"] += row.get("groups", 0)

    total_groups = sum(r.get("groups", 0) for r in yielded)
    on_subject_groups = totals["ON_SUBJECT"]
    sample_n = conv["method"]["sample"]

    report = {
        "contract_version": "round2.group-quality-audit.v1",
        "round": "ROUND2_CONVERSION",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "What are the 113 reported supervision groups actually made of?",
        "headline_being_audited": "The operator reported 113 groups from 300 candidates as a ninefold improvement over R11 without auditing group composition.",
        "totals": {
            "groups_reported": total_groups,
            "by_verdict": dict(totals.most_common()),
            "on_subject_groups": on_subject_groups,
            "off_subject_share": (total_groups - on_subject_groups) / total_groups if total_groups else None,
        },
        "corrected_rates": {
            "sample": sample_n,
            "groups_per_candidate_as_reported": total_groups / sample_n,
            "groups_per_candidate_on_subject_only": on_subject_groups / sample_n,
            "r11_groups_per_candidate": 10 / 248,
            "improvement_as_reported": (total_groups / sample_n) / (10 / 248),
            "improvement_on_subject_only": (on_subject_groups / sample_n) / (10 / 248),
        },
        "evidence_type": {
            "note": "The product task is named descriptors. Dimension-level evidence is a different supervision type and does not serve it.",
            "named_share_of_concept_hits": 0.27,
            "source": "conversion_measurement top_concepts: dimension 67, sensory 27, broad/attribute 6",
        },
        "per_candidate": sorted(audit, key=lambda r: -r["groups_reported"]),
        "limitations": [
            "Subject classification is by title regex and is an approximation. A paper may be on-subject with an ambiguous title, or off-subject with a coffee-bearing title.",
            "Group recount uses first-column labels only and will differ from the conversion script's count, which is reported alongside rather than replacing it.",
            "This audits composition, not admissibility. Evidence-trace, rights and governed-mapping admission were not run.",
        ],
        "guards": {"records_admitted": 0, "corpus_written": False, "fit_count": 0,
                   "training_pause": "REMAINS_IN_EFFECT"},
    }
    (args.output_dir / "group_quality_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    print(json.dumps({
        "groups_reported": total_groups,
        "by_verdict": dict(totals.most_common()),
        "on_subject_groups": on_subject_groups,
        "off_subject_share": round(report["totals"]["off_subject_share"], 4) if total_groups else None,
        "improvement_as_reported": round(report["corrected_rates"]["improvement_as_reported"], 2),
        "improvement_on_subject_only": round(report["corrected_rates"]["improvement_on_subject_only"], 2),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
