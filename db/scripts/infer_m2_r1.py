#!/usr/bin/env python3
"""Local JSON inference using the same M2 R1 entry path as evaluation."""

from __future__ import annotations
import argparse, json
from pathlib import Path
import flavor_m2_r1 as backend


def run(payload, bundle):
    backend.check_bundle(bundle)
    if bundle.get("foundation_model"):
        from flavor_foundation_r1 import run as foundation_run

        return foundation_run(payload, bundle, backend)
    return backend.run(payload, bundle)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model-file", type=Path, required=True)
    p.add_argument("--input", type=Path, required=True)
    a = p.parse_args()
    bundle = json.loads(a.model_file.read_text())
    payload = json.loads(a.input.read_text())
    print(
        json.dumps(
            run(payload, bundle), ensure_ascii=False, sort_keys=True, allow_nan=False
        )
    )


if __name__ == "__main__":
    main()
