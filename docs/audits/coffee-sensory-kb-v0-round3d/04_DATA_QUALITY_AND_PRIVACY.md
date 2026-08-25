# Data Quality and Privacy

Machine-readable payloads pass the direct-identifier scan. Public assessor
identity is limited to pseudonymous codes and approved categorical metadata.
The database rejects identifier-shaped JSON keys and email-like values.

The study remains in `design` with institutional approval `NOT_OBTAINED`.
Ethics/approval, consent-material, and public-release-rights gates are false.
Consequently, valid-looking real-observation rows are rejected even when they
contain no PII.

```text
PII_SCAN_PASS=true
HUMAN_PARTICIPANT_ETHICS_REQUIRED=true
INSTITUTIONAL_APPROVAL_STATUS=NOT_OBTAINED
PUBLIC_DATA_CONSENT_REQUIRED=true
ETHICS_OR_APPROVAL_GATE=false
CONSENT_MATERIAL_READY=false
PUBLIC_RELEASE_RIGHTS_READY=false
REAL_OBSERVATION_COUNT=0
```
