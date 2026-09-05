#!/usr/bin/env python3
"""Regenerate only Round 3O twice and compare all public bytes, without training."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
FOLDERS=("user-research-round1","product-inference-v0.2","product-benchmark-v0.2","product-gap-mining-v0.2")
def snapshot():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for f in FOLDERS for p in (ROOT/"db/data"/f).iterdir() if p.is_file()}
def run(*args): subprocess.run(args,cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
before=snapshot()
for _ in range(2):
    if os.environ.get("COFFEE_FLAVOR_USER_RESEARCH_ROOT"):
        run(sys.executable,"db/scripts/ingest-user-research-round1.py")
    run(sys.executable,"db/scripts/generate-product-inference-v02.py")
    run(os.environ.get("COFFEE_RESEARCH_NODE","node"),"scripts/generate-product-benchmark.mjs")
    run(sys.executable,"scripts/seal-round3o.py")
    after=snapshot()
    if before!=after:
        changed=sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))
        raise SystemExit("Generation drift: "+", ".join(changed))
print(f"BYTE_REPRODUCIBILITY_PASS=true; PUBLIC_ARTIFACT_FILE_COUNT={len(before)}; TRAINING_RUN_COUNT=0")
