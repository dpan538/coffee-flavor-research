#!/usr/bin/env python3
"""Write the public-safe SHA256 receipt for CI capability artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / "db" / "data" / "ci"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    CI.mkdir(parents=True, exist_ok=True)
    paths = sorted(path for path in CI.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    (CI / "SHA256SUMS").write_text(
        "".join(f"{sha(path)}  {path.name}\n" for path in paths), encoding="utf-8"
    )
    print(f"CI_ARTIFACT_SHA256_RECEIPT_FILE_COUNT={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
