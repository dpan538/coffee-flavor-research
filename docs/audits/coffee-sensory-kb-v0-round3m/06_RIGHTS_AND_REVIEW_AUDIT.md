# Rights and review audit

All six purposes have an explicit decision for every admitted pilot assertion.
`PENDING` and `UNKNOWN` are complete decision states but do not grant model
eligibility. Public visibility is never mapped to `AFFIRMATIVE`.

The merged universe has 3,096 rights decisions: 2,658 `UNKNOWN` and 438
`PENDING`. Every one of the 516 queue rows has all six purposes populated. The
live singular states are 73 pending and 67 unknown; neither state supports
model eligibility.

The 376 AVPA dispositions are Codex machine-assisted source-audit decisions.
They do not count as reviewed descriptors. Human-review and adjudication import
templates are intentionally empty of reviewer decisions.

The 140 live rows are automated-parser provisional decisions with current
disposition `HUMAN_REVIEW_REQUIRED`. They are not included in
`CODEX_PROVISIONAL_REVIEW_COUNT=376`; the actor-specific automated-parser count
is reported separately as 140.

Migration 058 governs reviewer evidence without inventing any. Production
contains zero reviewer artifacts, qualifications, admissions, row-level
decisions, human confirmations, expert adjudications, or qualified-human
challenge credits. The corrected 059 contains no persistent human seed; Codex
source audits remain provisional and test-only synthetic rows roll back. User
migration approval is application authority, not reviewer evidence.

```text
HUMAN_CONFIRMED_REVIEW_COUNT=0
EXPERT_ADJUDICATED_REVIEW_COUNT=0
EXPERT_REVIEW_PERFORMED=false
QUALIFIED_HUMAN_CHALLENGE_CREDIT_COUNT=0
PERSISTED_SYNTHETIC_HUMAN_FIXTURE_COUNT=0
RIGHTS_WIDENED=false
OUTBOUND_DATA_REQUEST_COUNT=0
```

Organizer drafts remain `NOT_SENT`. No contract, credential, or purchase was
accepted.
