#!/usr/bin/env python3
"""Seal or verify Round 3O public package checksums; never touches v0.1."""
import argparse
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FOLDERS=("user-research-round1","product-inference-v0.2","product-benchmark-v0.2","product-gap-mining-v0.2")
parser=argparse.ArgumentParser(); parser.add_argument("--check",action="store_true"); args=parser.parse_args()
for name in FOLDERS:
    folder=ROOT/"db/data"/name
    expected="".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in sorted(folder.iterdir()) if p.is_file() and p.name!="SHA256SUMS")
    if args.check:
        if (folder/"SHA256SUMS").read_text()!=expected: raise SystemExit("Checksum drift: "+name)
    else: (folder/"SHA256SUMS").write_text(expected)
print("ROUND3O_CHECKSUM_PASS=true")
