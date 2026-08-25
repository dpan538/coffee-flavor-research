# Coffee Sensory Context Calibration engineering package

Status: `PROTOCOL_AND_SCHEMA_ONLY`. This directory is not a sensory dataset
release and contains no collected human observation.

The package provides machine-readable capture schemas, empty CSV templates,
an example JSON envelope without participant data, and the deterministic
`protocol-and-schema-v0.1.0` release skeleton. Planned matrix/schedule artifacts
live under `db/data/round3d/generated/` and are imported by forward migrations.

Real capture is blocked until institutional approval, final bilingual consent,
and public-release rights gates are all true. Identity-to-pseudonym lookup,
recruitment records, and direct identifiers must remain outside this repository
and any public release.

Validate with:

```bash
python3 db/scripts/validate-round3d-capture.py data/calibration/templates
python3 db/scripts/prepare-round3d-release.py
```
