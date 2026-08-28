#!/usr/bin/env python3
"""Fail when current public surfaces overstate project evidence."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / "docs/portfolio/PORTFOLIO_FACTS.json"
EXCLUDED = {
    ROOT / "docs/portfolio/PUBLIC_WRITING_AND_CLAIM_STYLE.md",
    ROOT / "docs/portfolio/PUBLIC_CLAIMS_REGISTER.tsv",
}


def public_files() -> list[Path]:
    paths = [ROOT / "README.md", ROOT / "PORTFOLIO.md", ROOT / "PROJECT_STATUS.md"]
    for directory in ("docs/portfolio", "docs/user-research", "docs/ml"):
        paths.extend((ROOT / directory).glob("*.md"))
    paths.extend((ROOT / "app/routes").glob("*.tsx"))
    return sorted({path for path in paths if path.is_file() and path not in EXCLUDED})


def qualified_negative(context: str) -> bool:
    qualifiers = (
        "not ",
        "no ",
        "never ",
        "without ",
        "future ",
        "planned",
        "blocked",
        "prohibited",
        "requires",
        "until ",
        "cannot ",
        "do not ",
        "has not",
        "have not",
        "isn't",
        "untrained",
        "not_trained",
    )
    lowered = context.lower()
    return any(token in lowered for token in qualifiers)


def main() -> int:
    if not FACTS_PATH.is_file():
        print(f"PUBLIC_CLAIM_LINT_ERROR=missing {FACTS_PATH.relative_to(ROOT)}", file=sys.stderr)
        return 1
    facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
    pwa_allowed = facts["pwa"]["public_claim_allowed"]
    model_count = facts["ml"]["model_run_count"]
    model_eligible = facts["professional_descriptor_pilot"]["model_eligible_count"]

    explicit_patterns = {
        "UNSUPPORTED": [
            r"\bai tastes coffee\b",
            r"\bdetects? the (?:coffee['’]s )?true flavo[u]?r\b",
            r"\bpredicts? exact tasting notes\b",
            r"\bexpert[- ]level accuracy\b",
            r"\btrained on 26,?000 professional coffees\b",
            r"\b26,?000 professional labels\b",
            r"\bfully verified global sensory dataset\b",
            r"\bconsumer reviews prove (?:the )?coffee tastes like\b",
            r"\breal[- ]time personalization\b",
        ],
        "STALE_CURRENT_PHASE": [
            r"\bcurrent (?:phase|foundation|repository|work|state).{0,80}\bround 3[bc]\b",
            r"\bcurrent.{0,60}\bthrough round 3[bc]\b",
            r"\bthrough round 3[bc].{0,60}\bcurrent\b",
        ],
    }
    category_counts = {
        "UNSUPPORTED": 0,
        "STALE_CURRENT_PHASE": 0,
        "RAW_ROW_AS_TRAINING_LABEL": 0,
        "FALSE_MODEL": 0,
        "FALSE_PWA": 0,
    }
    failures: list[tuple[str, int, str, str]] = []

    for path in public_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            context = " ".join(lines[max(0, index - 1) : min(len(lines), index + 2)])
            for category, patterns in explicit_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, lowered, re.IGNORECASE)
                    if match:
                        failures.append(
                            (str(path.relative_to(ROOT)), index + 1, match.group(0), category)
                        )
                        category_counts[category] += 1

            raw_match = re.search(
                r"\b(?:raw|parsed|staged|publication)[ -]?rows?.{0,60}"
                r"(?:training (?:labels?|samples?)|professional labels?|model[- ]ready records?)",
                lowered,
            )
            if raw_match and not qualified_negative(context):
                failures.append(
                    (
                        str(path.relative_to(ROOT)),
                        index + 1,
                        raw_match.group(0),
                        "RAW_ROW_AS_TRAINING_LABEL",
                    )
                )
                category_counts["RAW_ROW_AS_TRAINING_LABEL"] += 1

            if not pwa_allowed:
                pwa_match = re.search(
                    r"\b(?:is|as|an?|the)\s+(?:evidence[- ]grounded\s+)?"
                    r"(?:adaptive\s+)?pwa\b|\bpwa\s+(?:implemented|available|installable)\b",
                    lowered,
                )
                if pwa_match and not qualified_negative(context):
                    failures.append(
                        (
                            str(path.relative_to(ROOT)),
                            index + 1,
                            pwa_match.group(0),
                            "FALSE_PWA",
                        )
                    )
                    category_counts["FALSE_PWA"] += 1

            if model_count == 0:
                model_match = re.search(
                    r"\b(?:trained (?:model|ranker|classifier|embedding|neural|deep[- ]learning)|"
                    r"model (?:achieves?|reaches?|predicts?|accuracy|probability)|"
                    r"accuracy\s*[:=]\s*\d)",
                    lowered,
                )
                if model_match and not qualified_negative(context):
                    failures.append(
                        (
                            str(path.relative_to(ROOT)),
                            index + 1,
                            model_match.group(0),
                            "FALSE_MODEL",
                        )
                    )
                    category_counts["FALSE_MODEL"] += 1

            if model_eligible == 0:
                ready_match = re.search(
                    r"\b(?:model[- ]ready|training[- ]ready|production[- ]ready ml)\b",
                    lowered,
                )
                if ready_match and not qualified_negative(context):
                    failures.append(
                        (
                            str(path.relative_to(ROOT)),
                            index + 1,
                            ready_match.group(0),
                            "FALSE_MODEL",
                        )
                    )
                    category_counts["FALSE_MODEL"] += 1

    for path, line, phrase, category in failures:
        print(
            f"{path}:{line}: {category}: {phrase!r}",
            file=sys.stderr,
        )

    print(f"UNSUPPORTED_PUBLIC_CLAIM_COUNT={len(failures)}")
    print(f"STALE_CURRENT_PHASE_REFERENCE_COUNT={category_counts['STALE_CURRENT_PHASE']}")
    print(f"RAW_ROW_AS_TRAINING_LABEL_CLAIM_COUNT={category_counts['RAW_ROW_AS_TRAINING_LABEL']}")
    print(f"FALSE_MODEL_CLAIM_COUNT={category_counts['FALSE_MODEL']}")
    print(f"FALSE_PWA_CLAIM_COUNT={category_counts['FALSE_PWA']}")
    print(f"PUBLIC_CLAIM_LINT_PASS={'true' if not failures else 'false'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
