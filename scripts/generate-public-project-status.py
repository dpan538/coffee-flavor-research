#!/usr/bin/env python3
"""Generate public-safe project status from governed repository receipts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "docs/portfolio/PUBLIC_STATUS_SOURCE.json"
BASELINE_PATH = ROOT / "db/data/round3m/BASELINE_RECONCILIATION.json"
ROUND3M_PATH = ROOT / "db/data/round3m/ROUND3M_MANIFEST.json"
LIVE_PATH = ROOT / "db/data/round3m/LIVE_ASSERTION_IMPORT_RECEIPT.json"
FREEZE_PATH = (
    ROOT / "db/data/freeze/coffee-sensory-research-db-v0/FREEZE_MANIFEST.json"
)
EXECUTIVE_PATH = (
    ROOT
    / "docs/audits/coffee-sensory-kb-v0-round3m/00_EXECUTIVE_RECEIPT.md"
)
OUTPUTS = {
    ROOT / "PROJECT_STATUS.md": "markdown",
    ROOT / "docs/portfolio/PORTFOLIO_FACTS.json": "json",
    ROOT / "docs/ml/ML_DATA_READINESS_MATRIX.md": "ml_markdown",
    ROOT / "public/project-status.json": "json",
    ROOT / "app/generated/projectStatus.ts": "typescript",
}


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required receipt is missing: {path.relative_to(ROOT)}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"required receipt must be a JSON object: {path}")
    return value


def read_receipt(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"required receipt is missing: {path.relative_to(ROOT)}")
    fields: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([A-Z][A-Z0-9_]*)=(.*)", line.strip())
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def require_int(receipt: dict[str, str], key: str) -> int:
    try:
        return int(receipt[key])
    except (KeyError, ValueError) as error:
        raise ValueError(f"missing or non-integer receipt field: {key}") from error


def build_facts() -> dict[str, Any]:
    source = read_json(SOURCE_PATH)
    baseline = read_json(BASELINE_PATH)
    round3m = read_json(ROUND3M_PATH)
    live = read_json(LIVE_PATH)
    freeze = read_json(FREEZE_PATH)
    executive = read_receipt(EXECUTIVE_PATH)

    source_sha = source.get("source_sha", "")
    if not re.fullmatch(r"[0-9a-f]{40}", str(source_sha)):
        raise ValueError("current source SHA is absent or invalid")

    live_manifest = round3m.get("live_pilot", {})
    expected_pairs = {
        "segmented_atomic_observation_count": "merged_row_count",
        "assertion_level_deinflated_count": "assertion_level_deinflated_count",
        "record_level_unique_descriptor_count": "record_level_unique_count",
        "descriptor_bearing_effective_record_count": "effective_record_count",
        "human_confirmed_review_count": "human_confirmed_count",
        "model_eligible_descriptor_count": "model_eligible_count",
    }
    conflicts = [
        key
        for key, live_key in expected_pairs.items()
        if live_manifest.get(key) != live.get(live_key)
    ]
    if conflicts:
        raise ValueError(
            "Round 3M governed receipt conflict: " + ", ".join(sorted(conflicts))
        )

    model = source.get("model_receipt", {})
    if model.get("model_status") != "NOT_TRAINED":
        raise ValueError("a model is claimed without a NOT_TRAINED receipt")
    if model.get("model_run_count") != 0 or any(
        model.get(key)
        for key in (
            "ml_baseline_run",
            "embedding_baseline_run",
            "cross_encoder_run",
            "deep_learning_model_run",
            "ranking_model_trained",
            "adaptive_policy_trained",
        )
    ):
        raise ValueError("a model run is claimed but no governed model receipt exists")

    pwa = source.get("pwa_audit", {})
    implemented_requirements = (
        pwa.get("web_app_manifest"),
        pwa.get("installable_icons"),
        pwa.get("service_worker"),
        pwa.get("offline_app_shell"),
    )
    if pwa.get("status") == "IMPLEMENTED" and not all(implemented_requirements):
        raise ValueError("public status says PWA implemented but the PWA audit fails")
    if pwa.get("public_claim_allowed") and pwa.get("status") != "IMPLEMENTED":
        raise ValueError("PWA public claim is allowed without IMPLEMENTED status")

    migration_count = len(list((ROOT / "db").glob("[0-9][0-9][0-9]_*.sql")))
    if migration_count != require_int(executive, "TOTAL_MIGRATION_COUNT"):
        raise ValueError("migration count conflicts with the Round 3M receipt")

    baseline_counts = baseline.get("recomputed", {})
    coverage = freeze.get("coverage_inventory", {})
    research = source.get("first_party_research", {})
    ci = source.get("round3m_remote_ci", {})

    facts = {
        "schema_version": "coffee-flavor-portfolio-facts-v1",
        "status_as_of": source["status_as_of"],
        "source": {
            "branch": source["source_branch"],
            "sha": source_sha,
            "work_branch": source["work_branch"],
            "phase": source["current_phase"],
            "phase_status": source["current_phase_status"],
        },
        "product": {
            "name": "Coffee Flavor Atlas",
            "public_subtitle": (
                "An evidence-grounded mobile-first web prototype for translating "
                "everyday coffee perception into professional sensory references."
            ),
            "interaction_contract": {
                "preparation_context": "C0",
                "roast_context": "C1",
                "mandatory_question_count": 4,
                "conditional_question_count": 0,
                "exceptional_question_count": 1,
                "primary_candidate_count": 5,
                "secondary_candidate_count": 3,
            },
        },
        "database": {
            "engine": "PostgreSQL 17",
            "migration_count": migration_count,
            "canonical_concept_count": coverage["canonical_concept_count"],
            "active_sensory_concept_count": coverage[
                "active_sensory_attribute_count"
            ],
            "focused_invariant_count": require_int(
                executive, "FOCUSED_INVARIANT_COUNT"
            ),
            "clean_rebuild_count": require_int(executive, "CLEAN_REBUILD_COUNT"),
        },
        "acquisition_scale": {
            "universe": "ROUND3L_STAGED_PUBLICATION_AND_ARTIFACT_RECEIPTS",
            "acquired_artifact_count": baseline_counts["artifacts"],
            "parsed_publication_row_count": baseline_counts["parsed_rows"],
            "staged_publication_row_count": baseline_counts["staged_rows"],
            "canonical_publication_row_count": baseline_counts["canonical_rows"],
            "staged_descriptor_assertion_count": baseline_counts[
                "staged_assertions"
            ],
            "independent_source_family_count": baseline[
                "independent_source_family_count"
            ],
        },
        "professional_descriptor_pilot": {
            "universe": "ROUND3M_LIVE_PUBLIC_SAFE_HASH_ONLY_PILOT",
            "admitted_assertion_count": live["merged_row_count"],
            "assertion_level_deinflated_count": live[
                "assertion_level_deinflated_count"
            ],
            "record_level_unique_count": live["record_level_unique_count"],
            "effective_record_count": live["effective_record_count"],
            "source_route_count": live["source_route_count"],
            "p2_assertion_count": live_manifest["p2_descriptor_assertion_count"],
            "provenance_unresolved_assertion_count": live_manifest[
                "provenance_unresolved_descriptor_assertion_count"
            ],
            "within_record_pair_event_count": live["coassertion_event_count"],
            "human_confirmed_count": live["human_confirmed_count"],
            "expert_adjudicated_count": live["expert_adjudicated_count"],
            "reviewed_p1_p2_strict_assertion_count": 0,
            "model_eligible_count": live["model_eligible_count"],
            "rights_cleared_model_count": 0,
        },
        "first_party_user_research": research,
        "ml": model,
        "pwa": pwa,
        "ci": ci,
        "boundaries": {
            "consumer_feedback_used_as_core_professional_label": False,
            "rights_widened": False,
            "evidence_tier_changed": False,
            "descriptor_gate_changed": False,
            "new_database_migration_count": 0,
        },
    }
    return facts


def render_markdown(facts: dict[str, Any]) -> str:
    database = facts["database"]
    acquisition = facts["acquisition_scale"]
    pilot = facts["professional_descriptor_pilot"]
    research = facts["first_party_user_research"]
    ml = facts["ml"]
    pwa = facts["pwa"]
    source = facts["source"]
    return f"""# Project status

This page is generated from governed repository receipts. Run
`npm run public:status` after changing a source receipt; do not edit the values
below by hand.

## Current product state

<!-- prettier-ignore -->
| Surface | Status | Evidence-backed interpretation |
| --- | --- | --- |
| Mobile web prototype | IMPLEMENTED | Responsive React Router interface with keyboard and reduced-motion checks. |
| Installable PWA | {pwa['status']} | Project-owned icons, a web app manifest, service worker, public app-shell cache, and offline fallback are present; restricted corpus files are excluded. |
| PostgreSQL knowledge base | VALIDATED | Provenance, evidence, review, rights, duplicate, and gate contracts are executable. |
| First-party user research | NOT_STARTED | Protocols exist; no user data was collected in this pass. |
| Ranking or adaptive model | NOT_STARTED | `MODEL_STATUS={ml['model_status']}`; deterministic retrieval remains the baseline. |

## Governed counts

Counts are separated by universe so acquisition volume is never presented as
reviewed or model-ready evidence.

<!-- prettier-ignore -->
| Universe | Measure | Current value |
| --- | --- | ---: |
| Canonical knowledge | Canonical concepts | {database['canonical_concept_count']} | <!-- claim: DATABASE_CANONICAL_CONCEPTS -->
| Canonical knowledge | Active sensory attributes | {database['active_sensory_concept_count']} | <!-- claim: DATABASE_ACTIVE_SENSORY -->
| Database governance | Forward migrations | {database['migration_count']} | <!-- claim: DATABASE_MIGRATIONS -->
| Acquisition | Acquired artifacts | {acquisition['acquired_artifact_count']} | <!-- claim: ACQUISITION_ARTIFACTS -->
| Acquisition | Staged publication rows | {acquisition['staged_publication_row_count']} | <!-- claim: ACQUISITION_STAGED_ROWS -->
| Descriptor pilot | Admitted hash-only assertions | {pilot['admitted_assertion_count']} | <!-- claim: PILOT_ADMITTED_ASSERTIONS -->
| Descriptor pilot | De-inflated assertion observations | {pilot['assertion_level_deinflated_count']} | <!-- claim: PILOT_DEINFLATED_ASSERTIONS -->
| Descriptor pilot | Record-level unique observations | {pilot['record_level_unique_count']} | <!-- claim: PILOT_RECORD_UNIQUE -->
| Descriptor pilot | Within-record P2 pair events | {pilot['within_record_pair_event_count']} | <!-- claim: PILOT_PAIR_EVENTS -->
| Reviewed professional universe | Reviewed P1/P2 strict assertions | {pilot['reviewed_p1_p2_strict_assertion_count']} | <!-- claim: REVIEWED_PROFESSIONAL_ASSERTIONS -->
| Human review | Human-confirmed assertions | {pilot['human_confirmed_count']} | <!-- claim: HUMAN_CONFIRMED_ASSERTIONS -->
| Model eligibility | Rights-cleared model-eligible assertions | {pilot['model_eligible_count']} | <!-- claim: MODEL_ELIGIBLE_ASSERTIONS -->
| First-party research | Interview sessions | {research['interview_count']} | <!-- claim: USER_INTERVIEW_COUNT -->
| First-party research | Usability sessions | {research['usability_session_count']} | <!-- claim: USER_USABILITY_COUNT -->
| Model work | Model runs | {ml['model_run_count']} | <!-- claim: MODEL_RUN_COUNT -->

## Readiness gates

The descriptor gates apply to reviewed P1/P2 strict assertions with companion
provenance, rights, diversity, and held-out evaluation requirements. They are
not raw-row targets.

<!-- prettier-ignore -->
| Gate | Purpose | Current status |
| ---: | --- | --- |
| 500 | Deterministic evaluation checkpoint | BLOCKED |
| 2,000 | Experimental normalization | BLOCKED |
| 5,000 | Experimental candidate ranking | BLOCKED |
| 10,000 | Research-grade normalization | BLOCKED |
| 15,000 | Association/co-assertion learning | BLOCKED |
| 20,000 | Research-grade candidate ranking | BLOCKED |
| 40,000 | Deployment-candidate ranking | BLOCKED |

## Current boundaries

- Consumer and industry language may support vocabulary and UX research, but
  cannot silently become professional label truth.
- Public availability does not grant model, deployment, or redistribution
  rights.
- No interviews, usability sessions, first-party interaction events, model
  runs, embeddings, cross-encoders, or deep-learning experiments are claimed.
- PWA implementation remains planned; the current product is a mobile-first web
  prototype.

## Provenance

```text
SOURCE_BRANCH={source['branch']}
SOURCE_SHA={source['sha']}
WORK_BRANCH={source['work_branch']}
STATUS_AS_OF={facts['status_as_of']}
```

See [PORTFOLIO.md](./PORTFOLIO.md),
[the long-form case study](./docs/portfolio/CASE_STUDY.md), and
[the ML readiness matrix](./docs/ml/ML_DATA_READINESS_MATRIX.md).
"""


def render_ml_markdown(facts: dict[str, Any]) -> str:
    acquisition = facts["acquisition_scale"]
    pilot = facts["professional_descriptor_pilot"]
    model = facts["ml"]
    rights_rate = "0%" if pilot["model_eligible_count"] == 0 else "REQUIRES_LIVE_QUERY"
    tasks = [
        (
            "Professional descriptor normalization",
            "500 / 2,000 / 10,000",
            "Qualified descriptor review and model-use rights",
            "Continue rights-cleared professional descriptor review",
        ),
        (
            "5+3 sensory candidate ranking",
            "5,000 / 20,000 / 40,000",
            "Reviewed multi-target relevance and grouped evaluation data",
            "Build eligible multi-target records after review",
        ),
        (
            "Co-assertion / association estimation",
            "15,000",
            "Observed pairs are not reviewed or model-rights eligible",
            "Review source assertions before association learning",
        ),
        (
            "Adaptive question selection",
            "Task-specific first-party gate",
            "No consented interaction events",
            "Run a separately authorized interaction pilot",
        ),
        (
            "Stopping policy",
            "Task-specific first-party gate",
            "No consented burden or outcome labels",
            "Collect consented completion and abstention evidence",
        ),
        (
            "Consumer-language comprehension mapping",
            "Task-specific rights/review gate",
            "No rights-approved task dataset",
            "Review purpose and rights before language mining",
        ),
    ]
    task_lines: list[str] = []
    for name, gate, blocker, next_step in tasks:
        professional_task = name.startswith(("Professional", "5+3", "Co-"))
        pair_events = (
            pilot["within_record_pair_event_count"] if name.startswith("Co-") else 0
        )
        effective_records = pilot["effective_record_count"] if professional_task else 0
        source_routes = pilot["source_route_count"] if professional_task else 0
        task_lines.append(
            f"| {name} | 0 | {effective_records} | {source_routes} | 0 | 0 | "
            f"{pair_events} | 0 | {rights_rate} | {gate} | BLOCKED | "
            f"{blocker} | {next_step} |"
        )

    return f"""# ML data-readiness matrix

This file is generated by `scripts/generate-public-project-status.py` from
governed Round 3L/3M machine receipts. Do not edit its counts by hand.

`MODEL_STATUS={model['model_status']}`

## Acquisition scale — not model data

<!-- prettier-ignore -->
| Measure | Current value | Universe |
| --- | ---: | --- |
| Acquired artifacts | {acquisition['acquired_artifact_count']} | Round 3L staged publication/artifact receipts |
| Parsed publication rows | {acquisition['parsed_publication_row_count']} | acquisition parsing |
| Staged publication rows | {acquisition['staged_publication_row_count']} | acquisition staging |
| Staged descriptor assertions | {acquisition['staged_descriptor_assertion_count']} | provisional acquisition census |
| Independent source families | {acquisition['independent_source_family_count']} | conservative acquisition-family grouping |

These values measure acquisition and staging. They are not training samples,
professional labels, reviewed targets, or model-eligible records.

## Current public-safe descriptor pilot

<!-- prettier-ignore -->
| Measure | Current value | Qualification |
| --- | ---: | --- |
| Admitted assertions | {pilot['admitted_assertion_count']} | hash/route-index pilot; machine provisional |
| Effective descriptor-bearing records | {pilot['effective_record_count']} | observed pilot records, not eligible model rows |
| Source routes | {pilot['source_route_count']} | routes, not claimed independent families |
| Within-record P2 pair events | {pilot['within_record_pair_event_count']} | co-assertions, not independent coffees |
| Human-confirmed assertions | {pilot['human_confirmed_count']} | full qualification/admission/decision chain required |
| Model-eligible assertions | {pilot['model_eligible_count']} | rights and review fail closed |

## Task readiness

“Current” columns use the public-safe pilot where applicable. A nonzero observed
count still contributes no model credit until task-specific review, rights,
diversity, and grouped-split gates pass.

<!-- prettier-ignore -->
| Task | Current reviewed assertions | Current effective records | Current source routes | Current reviewed normalized forms | Current reviewed multi-target records | Current observed pair events | Current qualified challenge cases | Current model-rights rate | Minimum gate | Status | Principal blocker | Next acquisition or review step |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
{chr(10).join(task_lines)}

## Descriptor gate ladder

<!-- prettier-ignore -->
| Reviewed P1/P2 strict assertion gate | Purpose | Current status |
| ---: | --- | --- |
| 500 | deterministic evaluation checkpoint | BLOCKED |
| 2,000 | experimental normalization | BLOCKED |
| 5,000 | experimental 5+3 ranking | BLOCKED |
| 10,000 | research-grade normalization | BLOCKED |
| 15,000 | association/co-assertion learning | BLOCKED |
| 20,000 | research-grade 5+3 ranking | BLOCKED |
| 40,000 | deployment-candidate ranking | BLOCKED |

The gates require reviewed P1/P2 strict assertions plus companion provenance,
rights, diversity, and held-out evaluation conditions. Raw publication rows,
rankings, scores, consumer reviews, unresolved fields, duplicate publications,
or synthetic fixtures cannot satisfy them.
"""


def render_outputs(facts: dict[str, Any]) -> dict[Path, str]:
    json_text = json.dumps(facts, indent=2, sort_keys=True) + "\n"
    ts_text = (
        "// Generated by scripts/generate-public-project-status.py.\n"
        "// Do not edit by hand.\n\n"
        "// prettier-ignore\n"
        f"export const projectStatus = {json_text.rstrip()} as const;\n"
    )
    return {
        ROOT / "PROJECT_STATUS.md": render_markdown(facts),
        ROOT / "docs/portfolio/PORTFOLIO_FACTS.json": json_text,
        ROOT / "docs/ml/ML_DATA_READINESS_MATRIX.md": render_ml_markdown(facts),
        ROOT / "public/project-status.json": json_text,
        ROOT / "app/generated/projectStatus.ts": ts_text,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if generated files drift"
    )
    args = parser.parse_args()

    try:
        outputs = render_outputs(build_facts())
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"PUBLIC_STATUS_GENERATION_ERROR={error}", file=sys.stderr)
        return 1

    drift: list[str] = []
    for path, content in outputs.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    if drift:
        print("PUBLIC_STATUS_GENERATION_DRIFT=" + ";".join(drift), file=sys.stderr)
        return 1

    print("PUBLIC_STATUS_GENERATOR_CREATED=true")
    print("PUBLIC_STATUS_JSON_CREATED=true")
    print("STATUS_GENERATION_DETERMINISTIC_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
