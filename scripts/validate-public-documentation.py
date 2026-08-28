#!/usr/bin/env python3
"""Validate public Markdown links and documentation-index completeness."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO_REQUIRED = [
    "README.md",
    "CASE_STUDY.md",
    "PROJECT_ONE_PAGER.md",
    "PROJECT_TIMELINE.md",
    "RESEARCH_ITERATION_STORY.md",
    "SKILLS_EVIDENCE_MATRIX.md",
    "DEMO_SCRIPT.md",
    "RECRUITER_READING_PATH.md",
    "PUBLIC_WRITING_AND_CLAIM_STYLE.md",
    "PUBLIC_CLAIMS_REGISTER.tsv",
    "PORTFOLIO_FACTS.json",
    "CONTRIBUTION_SCOPE_REVIEW.md",
    "SCREENSHOT_MANIFEST.md",
]
USER_RESEARCH_REQUIRED = [
    "USER_RESEARCH_OVERVIEW.md",
    "TARGET_USERS_AND_SCENARIOS.md",
    "RESEARCH_QUESTIONS.md",
    "INTERVIEW_AND_USABILITY_GUIDE.md",
    "USER_FEEDBACK_MINING_CONTRACT.md",
    "USER_DATA_COLLECTION_CONTRACT.md",
    "USER_RESEARCH_METRICS.md",
    "USER_INSIGHT_TRACEABILITY.md",
    "PRIVACY_CONSENT_AND_RETENTION.md",
    "FINDINGS_STATUS.md",
]
ML_REQUIRED = [
    "ML_PROBLEM_DEFINITION.md",
    "DATA_ROLE_AND_LABEL_CONTRACT.md",
    "ML_DATA_READINESS_MATRIX.md",
    "BASELINE_TO_DEEP_MODEL_LADDER.md",
    "EVALUATION_AND_SPLIT_PLAN.md",
    "LEARNING_CURVE_AND_SATURATION.md",
    "MODEL_CARD_DRAFT.md",
    "DATASET_CARD_DRAFT.md",
    "EXPERIMENT_REGISTRY.md",
]


def public_markdown_files() -> list[Path]:
    paths = [
        ROOT / "README.md",
        ROOT / "PORTFOLIO.md",
        ROOT / "PROJECT_STATUS.md",
        ROOT / "docs/INDEX.md",
        ROOT / "docs/research/INDEX.md",
        ROOT / "docs/audits/INDEX.md",
    ]
    for directory in ("docs/portfolio", "docs/user-research", "docs/ml"):
        paths.extend((ROOT / directory).glob("*.md"))
    return sorted({path for path in paths if path.is_file()})


def markdown_link_failures(paths: list[Path]) -> list[str]:
    failures: list[str] = []
    pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in pattern.finditer(line):
                raw_target = match.group(1).strip().strip("<>").split(" ", 1)[0]
                if raw_target.startswith(("http://", "https://", "mailto:", "#", "/")):
                    continue
                target_text = unquote(raw_target.split("#", 1)[0])
                if not target_text:
                    continue
                target = (path.parent / target_text).resolve()
                if not target.exists():
                    failures.append(
                        f"{path.relative_to(ROOT)}:{line_number}: missing link target {raw_target}"
                    )
    return failures


def main() -> int:
    missing: list[str] = []
    groups = [
        (ROOT / "docs/portfolio", PORTFOLIO_REQUIRED, ROOT / "docs/portfolio/README.md"),
        (
            ROOT / "docs/user-research",
            USER_RESEARCH_REQUIRED,
            ROOT / "docs/user-research/USER_RESEARCH_OVERVIEW.md",
        ),
        (ROOT / "docs/ml", ML_REQUIRED, ROOT / "docs/ml/README.md"),
    ]
    for directory, names, index in groups:
        index_text = index.read_text(encoding="utf-8") if index.is_file() else ""
        for name in names:
            path = directory / name
            if not path.is_file():
                missing.append(f"missing required document: {path.relative_to(ROOT)}")
            if path != index and name not in index_text:
                missing.append(f"missing from index {index.relative_to(ROOT)}: {name}")

    for required_index in ("docs/INDEX.md", "docs/research/INDEX.md", "docs/audits/INDEX.md"):
        if not (ROOT / required_index).is_file():
            missing.append(f"missing required index: {required_index}")

    link_failures = markdown_link_failures(public_markdown_files())
    for message in missing + link_failures:
        print(message, file=sys.stderr)

    print(f"USER_RESEARCH_DOCUMENT_COUNT={sum((ROOT / 'docs/user-research' / name).is_file() for name in USER_RESEARCH_REQUIRED)}")
    print(f"ML_DOCUMENT_COUNT={sum((ROOT / 'docs/ml' / name).is_file() for name in ML_REQUIRED)}")
    print(f"MARKDOWN_LINK_FAILURE_COUNT={len(link_failures)}")
    print(f"DOCUMENTATION_INDEX_FAILURE_COUNT={len(missing)}")
    print(f"MARKDOWN_LINK_VALIDATION_PASS={'true' if not link_failures else 'false'}")
    print(f"DOCUMENTATION_INDEX_PASS={'true' if not missing else 'false'}")
    return 1 if missing or link_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
