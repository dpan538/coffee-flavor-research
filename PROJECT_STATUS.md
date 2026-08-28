# Project status

This page is generated from governed repository receipts. Run
`npm run public:status` after changing a source receipt; do not edit the values
below by hand.

## Current product state

<!-- prettier-ignore -->
| Surface | Status | Evidence-backed interpretation |
| --- | --- | --- |
| Mobile web prototype | IMPLEMENTED | Responsive React Router interface with keyboard and reduced-motion checks. |
| Installable PWA | PLANNED | No manifest, service worker, installability receipt, or offline app shell is present. |
| PostgreSQL knowledge base | VALIDATED | Provenance, evidence, review, rights, duplicate, and gate contracts are executable. |
| First-party user research | NOT_STARTED | Protocols exist; no user data was collected in this pass. |
| Ranking or adaptive model | NOT_STARTED | `MODEL_STATUS=NOT_TRAINED`; deterministic retrieval remains the baseline. |

## Governed counts

Counts are separated by universe so acquisition volume is never presented as
reviewed or model-ready evidence.

<!-- prettier-ignore -->
| Universe | Measure | Current value |
| --- | --- | ---: |
| Canonical knowledge | Canonical concepts | 130 | <!-- claim: DATABASE_CANONICAL_CONCEPTS -->
| Canonical knowledge | Active sensory attributes | 92 | <!-- claim: DATABASE_ACTIVE_SENSORY -->
| Database governance | Forward migrations | 60 | <!-- claim: DATABASE_MIGRATIONS -->
| Acquisition | Acquired artifacts | 848 | <!-- claim: ACQUISITION_ARTIFACTS -->
| Acquisition | Staged publication rows | 26515 | <!-- claim: ACQUISITION_STAGED_ROWS -->
| Descriptor pilot | Admitted hash-only assertions | 140 | <!-- claim: PILOT_ADMITTED_ASSERTIONS -->
| Descriptor pilot | De-inflated assertion observations | 139 | <!-- claim: PILOT_DEINFLATED_ASSERTIONS -->
| Descriptor pilot | Record-level unique observations | 137 | <!-- claim: PILOT_RECORD_UNIQUE -->
| Descriptor pilot | Within-record P2 pair events | 508 | <!-- claim: PILOT_PAIR_EVENTS -->
| Reviewed professional universe | Reviewed P1/P2 strict assertions | 0 | <!-- claim: REVIEWED_PROFESSIONAL_ASSERTIONS -->
| Human review | Human-confirmed assertions | 0 | <!-- claim: HUMAN_CONFIRMED_ASSERTIONS -->
| Model eligibility | Rights-cleared model-eligible assertions | 0 | <!-- claim: MODEL_ELIGIBLE_ASSERTIONS -->
| First-party research | Interview sessions | 0 | <!-- claim: USER_INTERVIEW_COUNT -->
| First-party research | Usability sessions | 0 | <!-- claim: USER_USABILITY_COUNT -->
| Model work | Model runs | 0 | <!-- claim: MODEL_RUN_COUNT -->

## Readiness gates

The descriptor gates apply to reviewed P1/P2 strict assertions with companion
provenance, rights, diversity, and held-out evaluation requirements. They are
not raw-row targets.

<!-- prettier-ignore -->
| Gate | Purpose | Current status |
| ---: | --- | --- |
| 500 | Deterministic evaluation checkpoint | BLOCKED |
| 2,000 | Experimental normalization | BLOCKED |
| 5,000 | Experimental candidate ranking | BLOCKED |
| 10,000 | Research-grade normalization | BLOCKED |
| 15,000 | Association/co-assertion learning | BLOCKED |
| 20,000 | Research-grade candidate ranking | BLOCKED |
| 40,000 | Deployment-candidate ranking | BLOCKED |

## Current boundaries

- Consumer and industry language may support vocabulary and UX research, but
  cannot silently become professional label truth.
- Public availability does not grant model, deployment, or redistribution
  rights.
- No interviews, usability sessions, first-party interaction events, model
  runs, embeddings, cross-encoders, or deep-learning experiments are claimed.
- PWA implementation remains planned; the current product is a mobile-first web
  prototype.

## Provenance

```text
SOURCE_BRANCH=codex/coffee-sensory-kb-v0-round3m-descriptor-first-provenance-pilot-20260828
SOURCE_SHA=13b56d2c1d4beec3754ce53edec8954d4e034bce
WORK_BRANCH=codex/coffee-flavor-portfolio-repo-normalization-20260828
STATUS_AS_OF=2026-08-29
```

See [PORTFOLIO.md](./PORTFOLIO.md),
[the long-form case study](./docs/portfolio/CASE_STUDY.md), and
[the ML readiness matrix](./docs/ml/ML_DATA_READINESS_MATRIX.md).
