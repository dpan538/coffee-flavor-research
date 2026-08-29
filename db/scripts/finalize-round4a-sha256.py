#!/usr/bin/env python3
"""Finalize non-self-referential Round 4A file hashes."""

from __future__ import annotations

import hashlib
from pathlib import Path


root = Path(__file__).resolve().parents[2] / "db/data/round4a"
files = sorted(path for path in root.iterdir() if path.is_file() and path.name != "SHA256SUMS")
(root / "SHA256SUMS").write_text(
    "".join(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in files),
    encoding="utf-8",
)
