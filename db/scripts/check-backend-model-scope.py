#!/usr/bin/env python3
"""Reject frontend changes in a staged model commit or a supplied commit range."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
# Exact owner-approved shared backend files only; no blanket package exceptions.
SHARED_BACKEND_FILES = frozenset()
FRONTEND_CONFIG = frozenset({
    "package.json", "package-lock.json", "vite.config.ts", "react-router.config.ts",
    "playwright.config.ts", "tsconfig.json",
})


def forbidden(path):
    p = Path(path)
    if path in SHARED_BACKEND_FILES:
        return False
    return (
        path in FRONTEND_CONFIG
        or path.startswith(("app/", "public/", "tests/e2e/", "packages/flavor-data/"))
        or p.suffix.lower() in {".css", ".scss", ".sass", ".less", ".tsx", ".jsx"}
        or any(part in {"pages", "components", "styles", "service-worker"} for part in p.parts)
        or "service-worker" in p.name
        or "serviceworker" in p.name.lower()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="Compare this revision to the working tree; default checks staged files")
    args = parser.parse_args()
    command = ["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB"]
    command += [args.base] if args.base else ["--cached"]
    paths = subprocess.check_output(command, cwd=ROOT, text=True).splitlines()
    if args.base:
        paths += subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    rejected = sorted({p for p in paths if forbidden(p)})
    if rejected:
        raise SystemExit("BACKEND_SCOPE_REJECTED: " + ", ".join(rejected))
    print("BACKEND_SCOPE_PASS=true; CHECKED_FILE_COUNT=" + str(len(set(paths))))


if __name__ == "__main__":
    main()
