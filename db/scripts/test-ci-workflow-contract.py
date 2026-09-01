#!/usr/bin/env python3
"""Fail closed if CI decomposition removes or misclassifies a test contract."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLASSIFICATION = ROOT / "db" / "data" / "ci" / "CI_TEST_CLASSIFICATION_AND_EQUIVALENCE.json"
CURRENT = ROOT / "db" / "scripts" / "ci-verify-current-artifacts.sh"
HISTORICAL = ROOT / "db" / "scripts" / "ci-verify.sh"
CURRENT_DATABASE = ROOT / "db" / "scripts" / "ci-verify-current-database.sh"
RESTRICTED = ROOT / "db" / "scripts" / "ci-verify-restricted-local.sh"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
HISTORICAL_WORKFLOW = ROOT / ".github" / "workflows" / "historical-replay.yml"

ALLOWED_CLASSES = {
    "PUSH_REQUIRED_CURRENT",
    "RELEASE_REQUIRED_HISTORICAL",
    "SCHEDULED_HISTORICAL",
    "RESTRICTED_LOCAL_REQUIRED",
    "OPTIONAL_DIAGNOSTIC",
}
REQUIRED_IDS = {
    "web-verification",
    "public-fixture-replay",
    "round3m-artifact-contract",
    "current-descriptor-data",
    "batch3-cleaning",
    "post20k-public-extension",
    "batch4-cleaned-30k",
    "post30k-public-extension",
    "batch6-semantic-corpus",
    "batch7-pipeline",
    "post40k-public-extension",
    "normalization-smoke",
    "round3m-live-adapters-public",
    "public-snapshot-contract",
    "current-database-contract",
    "restricted-real-replay",
    "two-clean-database-historical-replay",
}
CURRENT_TOKENS = {
    "test-round3m-artifact-contract.py",
    "test-current-descriptor-data.py",
    "test-batch3-candidate-cleaning.py",
    "test-post20k-extension.py",
    "test-batch4-cleaned-30k.py",
    "test-post30k-extension.py",
    "test-batch6-semantic-corpus.py",
    "test-batch7-pipeline.py",
    "test-post40k-extension.py",
    "test-normalization-smoke.py",
    "test-round3m-live-adapters.py",
    "--public-fixture",
    "--public-snapshot",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    payload = json.loads(CLASSIFICATION.read_text(encoding="utf-8"))
    tests = payload.get("tests")
    require(payload.get("mandatory_test_skip_count") == 0, "mandatory test skip count must be zero")
    require(isinstance(tests, list), "classification tests must be a list")
    ids = {row.get("id") for row in tests}
    require(ids == REQUIRED_IDS, "classification must enumerate every required CI contract exactly once")
    require(len(ids) == len(tests), "classification ids must be unique")
    for row in tests:
        require(row.get("classification") in ALLOWED_CLASSES, f"invalid class for {row.get('id')}")
        for key in ("old_command", "new_command", "expected_inputs", "expected_outputs", "coverage"):
            require(bool(row.get(key)), f"missing {key} for {row.get('id')}")
        require(isinstance(row.get("push_required"), bool), f"missing push flag for {row.get('id')}")
        require(isinstance(row.get("release_required"), bool), f"missing release flag for {row.get('id')}")

    current = CURRENT.read_text(encoding="utf-8")
    historical = HISTORICAL.read_text(encoding="utf-8")
    current_database = CURRENT_DATABASE.read_text(encoding="utf-8")
    restricted = RESTRICTED.read_text(encoding="utf-8")
    ci_workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    historical_workflow = HISTORICAL_WORKFLOW.read_text(encoding="utf-8")
    require(all(token in current for token in CURRENT_TOKENS), "current artifact entrypoint omits a public test")
    require("ci-verify-current-artifacts.sh" in historical, "historical entrypoint omits current artifact contracts")
    require("rebuild-twice.sh" in historical, "historical entrypoint omits two-build replay")
    require("--restricted-real" in historical, "historical entrypoint omits restricted replay declaration")
    require("--require-restricted-real" in restricted, "restricted replay must fail closed without owner inputs")
    require("apply.sh" in current_database and "load-round3m-artifacts.sh" in current_database and "test.sh" in current_database, "current database entrypoint omits a required database stage")
    require("database-artifacts:" in ci_workflow and "database-current:" in ci_workflow, "push workflow lacks decomposed database jobs")
    require("timeout-minutes: 15" in ci_workflow and "timeout-minutes: 20" in ci_workflow, "push database budgets changed")
    require("actions/setup-python@v5" in ci_workflow and 'python-version: "3.12"' in ci_workflow, "public artifact job must pin Python 3.12")
    require("PYTHON_COMMAND: python" in ci_workflow, "public artifact job must select one canonical interpreter")
    require("python -X dev -B db/scripts/generate-batch6-semantic-corpus.py" in ci_workflow, "public artifact workflow omits direct Batch 6 diagnostic")
    require("python -X dev -B db/scripts/test-current-descriptor-data.py" in ci_workflow, "public artifact workflow omits current descriptor diagnostic")
    require("apt-get install --yes --no-install-recommends python3 ca-certificates" in ci_workflow, "current database job must install its Python runtime explicitly")
    require(all(token in current_database for token in ("python3", "psql", "createdb", "dropdb")), "current database preflight omits a required command")
    require("workflow_dispatch:" in historical_workflow and "schedule:" in historical_workflow, "historical workflow must be dispatchable and scheduled")
    require("push:" in historical_workflow and "research/coffee-sensory-data-ml-readiness" in historical_workflow, "historical workflow must validate the protected research branch before main promotion")
    require("timeout-minutes: 75" in historical_workflow and "ci-verify.sh" in historical_workflow, "historical replay command or budget changed")
    print(f"CI_TEST_CLASSIFICATION_COUNT={len(tests)}")
    print("MANDATORY_TEST_SKIP_COUNT=0")
    print("CI_TEST_CLASSIFICATION_PASS=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
