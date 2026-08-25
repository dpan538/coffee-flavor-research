# Capture Pipeline

`data/calibration/` contains the data dictionary, license, citation metadata,
JSON schema, zero-row example bundle, and twelve CSV templates for material,
execution, observations, questions, judgments, and deviations.

The capture validator checks exact headers, record origins, direct identifiers,
and the three real-data governance flags. The staging script emits a governed
manifest without silently promoting rows. Migrations `030`–`032` add capture
batches/rows, reject direct identifiers, and reject real-observation writes or
promotion while approval, consent-material, or release-rights gates are closed.

```text
CAPTURE_TEMPLATE_PASS=true
CAPTURE_ROW_COUNT=0
REAL_CAPTURE_ROW_COUNT=0
IMPORT_PIPELINE_PASS=true
RELEASE_MANIFEST_SHA256=062198d21cf56d3ac1f1bf9faea30169ca89efb12cbbabc0190178b4dfb8d063
```
