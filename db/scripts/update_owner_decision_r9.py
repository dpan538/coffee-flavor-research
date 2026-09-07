#!/usr/bin/env python3
"""Record the owner's OUT_SEPARATED R9 output-role decision.

The update is idempotent for the same approved policy.  It changes no default,
model, question-selection parameter or training authorization.
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DECISION_FILE = (
    ROOT / "db/data/backend-sequential-model-v2/revisions/r9/decision_record.json"
)
POLICY = "OUT_SEPARATED"


def now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def update(path: Path, approved_utc: str) -> tuple[dict[str, Any], bool]:
    data = json.loads(path.read_text())
    owner = data.get("owner_decision")
    if not isinstance(owner, dict):
        raise ValueError("OWNER_DECISION_OBJECT_REQUIRED")
    status = owner.get("status")
    if status == "OWNER_APPROVED":
        if owner.get("approved_policy") != POLICY:
            raise ValueError("CONFLICTING_EXISTING_OWNER_APPROVAL")
        return data, False
    if status != "PENDING_OWNER_DECISION":
        raise ValueError("OWNER_DECISION_MUST_BE_PENDING")

    owner.update(
        status="OWNER_APPROVED",
        approved_policy=POLICY,
        approved_utc=approved_utc,
        approval_scope=(
            "Backend output-role contract only. This approval does not claim "
            "empirical superiority, change the default finalizer, authorize a "
            "frontend, or resume training."
        ),
        approval_note=(
            "Owner approved named descriptors in main/secondary and already-supported "
            "directions in overall_profile, with no invented child descriptors."
        ),
    )
    owner.pop("only_product_decision_to_approve", None)
    owner["approved_product_decision"] = (
        "Use OUT_SEPARATED as the backend output-role contract: named descriptors "
        "in main/secondary and supported directions in overall_profile."
    )
    data["recorded_utc"] = approved_utc
    data["recommendation"]["status"] = "OWNER_APPROVED_OUTPUT_ROLE_CONTRACT"
    data["recommendation"]["policy_id"] = POLICY
    data["default_adoption"] = "NOT_APPLIED_B2_AND_DEFAULT_FINALIZER_UNCHANGED"
    data["empirical_superiority_claim"] = "NOT_CLAIMED"
    data["training_after_R9"] = "PAUSED_REQUIRES_SEPARATE_FUTURE_OWNER_AUTHORIZATION"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return data, True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-file", type=Path, default=DECISION_FILE)
    parser.add_argument(
        "--approved-utc",
        help="Explicit ISO-8601 approval time; default is the actual current UTC time.",
    )
    args = parser.parse_args()
    approved_utc = args.approved_utc or now()
    try:
        datetime.datetime.fromisoformat(approved_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("ISO8601_APPROVAL_TIME_REQUIRED") from exc
    data, changed = update(args.decision_file, approved_utc)
    print(
        json.dumps(
            {
                "status": data["owner_decision"]["status"],
                "approved_policy": data["owner_decision"]["approved_policy"],
                "changed": changed,
                "training_after_R9": data["training_after_R9"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
