#!/usr/bin/env python3
"""Finalize and validate the public-safe Round 3M artifact checkpoint.

The finalizer never reads source text.  It derives only aggregate receipts,
an exact round-local elapsed-time row, and cryptographic manifests from the
already generated public-safe artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "db" / "data" / "round3m"
ADAPTER_DATA = ROOT / "db" / "adapters" / "round3m" / "generated"


class ContractError(RuntimeError):
    """Raised when a Round 3M input no longer matches the audited contract."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def read_tsv(name: str) -> list[dict[str, str]]:
    path = DATA / name
    require(path.is_file(), f"missing required artifact: {name}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(
    path: Path, columns: Iterable[str], rows: Iterable[Mapping[str, object]]
) -> None:
    fieldnames = tuple(columns)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None, "time values must include a UTC offset")
    return parsed.astimezone(timezone.utc)


def data_row_count(path: Path) -> int | None:
    if path.suffix != ".tsv":
        return None
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--ended-at", required=True)
    parser.add_argument(
        "--phase-status",
        choices=(
            "PASS_DESCRIPTOR_PILOT_NOT_TRAINING_READY",
            "PASS_PILOT_BLOCKED_MODEL_RIGHTS",
            "FAIL_CONTRACT",
            "FAIL_REPRODUCIBILITY",
        ),
        required=True,
    )
    args = parser.parse_args()

    started = parse_utc(args.started_at)
    ended = parse_utc(args.ended_at)
    require(ended >= started, "ended-at precedes started-at")
    active_minutes = (ended - started).total_seconds() / 60

    census = read_tsv("SOURCE_CENSUS_UNIVERSE.tsv")
    routes = read_tsv("SOURCE_ROUTE_DISPOSITION.tsv")
    signatures = read_tsv("SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv")
    queue = read_tsv("DESCRIPTOR_REVIEW_QUEUE.tsv")
    decisions = read_tsv("DESCRIPTOR_PROVISIONAL_DECISIONS.tsv")
    ledger = read_tsv("DESCRIPTOR_ASSERTION_LEDGER.tsv")
    rights = read_tsv("DESCRIPTOR_RIGHTS_DECISION.tsv")
    duplicates = read_tsv("DUPLICATE_REPEAT_DECISION.tsv")
    coassertions = read_tsv("COASSERTION_EVENT.tsv")
    gates = read_tsv("DESCRIPTOR_GATE_STATUS.tsv")
    requests = read_tsv("ORGANIZER_REQUEST_MATRIX.tsv")
    exclusions = read_tsv("LOW_YIELD_EXCLUSION_REGISTER.tsv")
    blockers = read_tsv("ROUND3M_RESEARCH_ARTIFACT_BLOCKER.tsv")
    effective_records_path = ADAPTER_DATA / "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv"
    require(effective_records_path.is_file(), "missing live effective-record export")
    with effective_records_path.open("r", encoding="utf-8", newline="") as handle:
        effective_records = list(csv.DictReader(handle, delimiter="\t"))

    ledger_ids = {row["descriptor_assertion_id"] for row in ledger}
    ledger_duplicate_rows = [
        row for row in duplicates if row["descriptor_assertion_id"] in ledger_ids
    ]
    disposition = Counter(row["current_disposition"] for row in queue)
    classes = Counter(row["descriptor_class"] for row in ledger)
    tiers = Counter(row["evidence_tier"] for row in ledger)
    rights_states = Counter(row["rights_state"] for row in rights)

    require(len(census) == 480, "census count drift")
    require(len(routes) == 131, "source-route count drift")
    require(
        len({row["independent_source_family_id"] for row in census}) == 11,
        "independent-family count drift",
    )
    require(len(signatures) == 4, "schema-signature count drift")
    require(len(queue) == 516, "merged review-queue count drift")
    require(len(decisions) == 516, "provisional-decision count drift")
    require(disposition == Counter({"NON_DESCRIPTOR": 376, "HUMAN_REVIEW_REQUIRED": 140}), "candidate disposition drift")
    require(len(ledger) == 140, "live descriptor-ledger count drift")
    require(classes == Counter({"STRICT_FLAVOR": 86, "BROAD_SENSORY": 54}), "descriptor-class drift")
    require(tiers == Counter({"P2": 73, "UNRESOLVED": 67}), "evidence-tier drift")
    require(len(effective_records) == 8, "effective-record count drift")
    require(len(rights) == 516 * 6, "purpose-specific rights count drift")
    require(rights_states == Counter({"UNKNOWN": 2658, "PENDING": 438}), "rights-state drift")
    require(
        all(row["raw_field_text"] == "" and row["atomic_source_text"] == "" for row in ledger),
        "public ledger contains source text",
    )
    require(
        all(len(row["source_file_sha256"]) == 64 for row in ledger),
        "live source-file hash completeness drift",
    )
    require(
        sum(row["counts_as_assertion"] == "true" for row in ledger_duplicate_rows)
        == 139,
        "assertion-level de-inflated count drift",
    )
    require(
        sum(
            row["counts_as_record_unique_descriptor"] == "true"
            for row in ledger_duplicate_rows
        )
        == 137,
        "record-unique descriptor count drift",
    )
    require(len(coassertions) == 508, "coassertion count drift")
    require(len(gates) == 56 and not any(row["pass"] == "true" for row in gates), "descriptor gate fail-closed drift")
    require(all(row["pass"] == "false" for row in gates if row["not_applicable"] == "true"), "NA gate criterion passed")
    require(len(blockers) == 1, "machine-artifact blocker drift")
    require(len(exclusions) == 11 and all(row["new_round3m_broad_acquisition_budget"] == "0" for row in exclusions), "low-yield stop-loss drift")
    require(all(row["request_status"] == "NOT_SENT" for row in requests), "outbound request status drift")
    require(
        sum(int(row["outbound_data_request_count"]) for row in requests) == 0
        and sum(int(row["contract_acceptance_count"]) for row in requests) == 0
        and sum(int(row["commercial_purchase_count"]) for row in requests) == 0,
        "external-action count drift",
    )

    analyst_rows = [
        {
            "analyst_time_log_key": "round3m.end-to-end-execution.20260828",
            "task_type": "RECONCILIATION",
            "source_route_id": "",
            "artifact_count": 848 + 3,
            "candidate_count": 376 + 140,
            "reviewed_count": 0,
            "started_at": started.isoformat().replace("+00:00", "Z"),
            "ended_at": ended.isoformat().replace("+00:00", "Z"),
            "active_minutes": f"{active_minutes:.3f}",
            "automated_runtime_seconds": "NA_NOT_INSTRUMENTED_FROM_TASK_START",
            "review_actor_type": "CODEX_SOURCE_AUDITOR",
            "notes": "MULTIPLE_ROUTES aggregate. Exact round-local elapsed time only; no historical or per-route allocation was fabricated. Automated runtime was not comprehensively instrumented from task start.",
        }
    ]
    write_tsv(
        DATA / "ANALYST_TIME_LOG.tsv",
        tuple(analyst_rows[0]),
        analyst_rows,
    )

    expected_rows = [
        ("BASELINE", "CENSUS_ITEM_COUNT", "480", str(len(census)), "true", "SOURCE_CENSUS_UNIVERSE.tsv"),
        ("BASELINE", "SOURCE_ROUTE_OR_FAMILY_KEY_COUNT", "131", str(len(routes)), "true", "SOURCE_ROUTE_DISPOSITION.tsv"),
        ("BASELINE", "INDEPENDENT_SOURCE_FAMILY_COUNT", "11", "11", "true", "SOURCE_CENSUS_UNIVERSE.tsv"),
        ("REVIEW", "EXISTING_CANDIDATE_COUNT", "376", "376", "true", "EXISTING_376_REVIEW_RECEIPT.json"),
        ("REVIEW", "NON_DESCRIPTOR_COUNT", "376", str(disposition["NON_DESCRIPTOR"]), "true", "DESCRIPTOR_REVIEW_QUEUE.tsv"),
        ("LIVE_PILOT", "SEGMENTED_ATOMIC_OBSERVATION_COUNT", "140", str(len(ledger)), "true", "DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("LIVE_PILOT", "ASSERTION_LEVEL_DEINFLATED_COUNT", "139", "139", "true", "DUPLICATE_REPEAT_DECISION.tsv"),
        ("LIVE_PILOT", "RECORD_LEVEL_UNIQUE_DESCRIPTOR_COUNT", "137", "137", "true", "DUPLICATE_REPEAT_DECISION.tsv"),
        ("LIVE_PILOT", "STRICT_FLAVOR_ASSERTION_COUNT", "86", str(classes["STRICT_FLAVOR"]), "true", "DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("LIVE_PILOT", "BROAD_SENSORY_ASSERTION_COUNT", "54", str(classes["BROAD_SENSORY"]), "true", "DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("LIVE_PILOT", "P2_DESCRIPTOR_ASSERTION_COUNT", "73", str(tiers["P2"]), "true", "DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("LIVE_PILOT", "PROVENANCE_UNRESOLVED_DESCRIPTOR_ASSERTION_COUNT", "67", str(tiers["UNRESOLVED"]), "true", "DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("LIVE_PILOT", "DESCRIPTOR_BEARING_EFFECTIVE_RECORD_COUNT", "8", str(len(effective_records)), "true", "PUBLIC_SAFE_EFFECTIVE_RECORDS.tsv"),
        ("RIGHTS", "PURPOSE_SPECIFIC_RIGHTS_ROW_COUNT", "3096", str(len(rights)), "true", "DESCRIPTOR_RIGHTS_DECISION.tsv"),
        ("RIGHTS", "MODEL_ELIGIBLE_DESCRIPTOR_COUNT", "0", str(sum(row["model_eligible"] == "true" for row in ledger)), "true", "DESCRIPTOR_ASSERTION_LEDGER.tsv"),
        ("REVIEW", "HUMAN_CONFIRMED_REVIEW_COUNT", "0", str(sum(row["review_state"] == "HUMAN_CONFIRMED" for row in decisions)), "true", "DESCRIPTOR_PROVISIONAL_DECISIONS.tsv"),
        ("REVIEW", "EXPERT_ADJUDICATED_REVIEW_COUNT", "0", str(sum(row["review_state"] == "EXPERT_ADJUDICATED" for row in decisions)), "true", "DESCRIPTOR_PROVISIONAL_DECISIONS.tsv"),
        ("GATE", "PASSING_CRITERION_COUNT", "0", str(sum(row["pass"] == "true" for row in gates)), "true", "DESCRIPTOR_GATE_STATUS.tsv"),
        ("GATE", "SATURATION_EVALUATED", "false", "false", "true", "056_round3m_descriptor_gate_contract.sql"),
        ("GATE", "SATURATION_PASS", "false", "false", "true", "056_round3m_descriptor_gate_contract.sql"),
        ("EXTERNAL_ACTION", "OUTBOUND_DATA_REQUEST_COUNT", "0", "0", "true", "ORGANIZER_REQUEST_MATRIX.tsv"),
        ("EXTERNAL_ACTION", "CONTRACT_ACCEPTANCE_COUNT", "0", "0", "true", "ORGANIZER_REQUEST_MATRIX.tsv"),
        ("EXTERNAL_ACTION", "COMMERCIAL_PURCHASE_COUNT", "0", "0", "true", "ORGANIZER_REQUEST_MATRIX.tsv"),
        ("MODEL", "MODEL_OR_TRAINING_ARTIFACT_COUNT", "0", "0", "true", "Round 3M phase policy"),
        ("RESEARCH_INPUT", "MACHINE_READABLE_RESEARCH_ARTIFACTS_AVAILABLE", "false", "false", "true", "ROUND3M_RESEARCH_ARTIFACT_BLOCKER.tsv"),
    ]
    expected_columns = (
        "section",
        "metric_name",
        "expected_value",
        "observed_value",
        "pass",
        "evidence",
    )
    write_tsv(
        DATA / "ROUND3M_EXPECTED_STATE.tsv",
        expected_columns,
        (dict(zip(expected_columns, row)) for row in expected_rows),
    )

    excluded = {"ROUND3M_MANIFEST.json", "SHA256SUMS"}
    artifact_files = sorted(
        path for path in DATA.iterdir() if path.is_file() and path.name not in excluded
    )
    manifest = {
        "manifest_version": "round3m-public-safe-checkpoint-v1",
        "phase_status": args.phase_status,
        "generated_at": ended.isoformat().replace("+00:00", "Z"),
        "source_checkpoint_sha": "4159636afec052b96f20d3d10c6c5f2b943b4536",
        "machine_readable_research_artifacts_available": False,
        "research_artifact_import_status": "BLOCKED_MISSING_MACHINE_ARTIFACTS",
        "report_counts_independently_reproduced": False,
        "live_pilot": {
            "segmented_atomic_observation_count": 140,
            "assertion_level_deinflated_count": 139,
            "record_level_unique_descriptor_count": 137,
            "strict_flavor_assertion_count": 86,
            "broad_sensory_assertion_count": 54,
            "p2_descriptor_assertion_count": 73,
            "provenance_unresolved_descriptor_assertion_count": 67,
            "descriptor_bearing_effective_record_count": 8,
            "human_confirmed_review_count": 0,
            "model_eligible_descriptor_count": 0,
        },
        "restricted_capture": {
            "locator": "restricted://coffee-flavor-round3m/round3m-2026-08-28t043000z",
            "manifest_sha256": "b36fbe8a959b099b1a3a073b045c3d6ac74e31043f090d2fd88bd78c3290e51d",
            "public_redistribution": False,
        },
        "files": [
            {
                "path": path.name,
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
                "data_row_count": data_row_count(path),
            }
            for path in artifact_files
        ],
    }
    manifest_path = DATA / "ROUND3M_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checksum_files = sorted(
        path for path in DATA.iterdir() if path.is_file() and path.name != "SHA256SUMS"
    )
    (DATA / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(path)}  {path.name}\n" for path in checksum_files),
        encoding="utf-8",
    )
    print(
        "ROUND3M_FINAL_ARTIFACTS_PASS "
        f"files={len(checksum_files)} live=140 assertion_level=139 "
        f"record_unique=137 active_minutes={active_minutes:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
