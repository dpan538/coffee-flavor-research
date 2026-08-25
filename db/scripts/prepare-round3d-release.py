#!/usr/bin/env python3
"""Build the deterministic protocol-and-schema release manifest/checksums."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CALIBRATION = ROOT / "data" / "calibration"
RELEASE = CALIBRATION / "releases" / "protocol-and-schema-v0.1.0"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    payload = [
        CALIBRATION / "README.md",
        CALIBRATION / "DATA_DICTIONARY.md",
        CALIBRATION / "DATA_LICENSE.md",
        CALIBRATION / "CITATION.cff",
        CALIBRATION / "schema" / "capture.schema.json",
        *sorted((CALIBRATION / "templates").glob("*")),
        RELEASE / "data" / "README.md",
        RELEASE / "protocol" / "README.md",
        RELEASE / "analysis" / "README.md",
    ]
    payload = [path for path in payload if path.is_file()]
    artifacts = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(payload)
    ]
    manifest = {
        "release_key": "protocol-and-schema-v0.1.0",
        "release_status": "PROTOCOL_AND_SCHEMA_ONLY",
        "is_sensory_dataset_release": False,
        "real_observation_count": 0,
        "dry_run_fixture_count": 5,
        "human_participant_ethics_required": True,
        "institutional_approval_status": "NOT_OBTAINED",
        "public_data_consent_required": True,
        "public_release_rights_ready": False,
        "protocol_sha256": "4c759fcae812203c40394d1f510e93c4a83430a3dfb298e832b5ffc49f5924ad",
        "matrix_sha256": "dbd56b90672e00af5fe17a4d8c2c50b996d020a29e39dce04e9bd752de6d356b",
        "randomization_sha256": "eb7aa3fbfa6daf2d94819c007c42cdb43efcbbe4540335f231907b0b4a6edb4b",
        "question_assignment_sha256": "3e48c83feff27767cf68792f6a9e4c51e80c21aabf0cb419a1cfb02261a528e9",
        "split_inventory_sha256": "fe76dab2f695a0e7a1d23eb0744c97fb7c832e069cd9b060d26da47c3cebe45a",
        "artifacts": artifacts,
    }
    RELEASE.mkdir(parents=True, exist_ok=True)
    manifest_path = RELEASE / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    checksum_paths = [*payload, manifest_path]
    checksum_lines = [
        f"{sha256(path)}  {path.relative_to(ROOT)}"
        for path in sorted(checksum_paths)
    ]
    (RELEASE / "checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8"
    )
    print(f"RELEASE_MANIFEST_SHA256={sha256(manifest_path)}")
    print(f"RELEASE_CHECKSUM_COUNT={len(checksum_lines)}")
    print("PROTOCOL_SCHEMA_RELEASE_PREP_PASS=true")


if __name__ == "__main__":
    main()
