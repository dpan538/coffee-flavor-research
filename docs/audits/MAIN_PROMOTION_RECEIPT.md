# Main promotion receipt

This receipt records the Batch 6 research checkpoint proposed for an
explicit, fast-forward-only promotion. It is not a claim that restricted source
text was replayed in public CI.

## Pre-promotion ancestry

```text
ACTIVE_RESEARCH_BRANCH=research/coffee-sensory-data-ml-readiness
INITIAL_RESEARCH_SHA=dbe9c07e6c94f7d5e218c2892457976517f4cdce
CI_HARDENING_SHA=7c874f0ab4755b9be2e419490db742a6dccf7187
EXPECTED_REMOTE_MAIN_SHA=21d04f50952ac30ee13010ee26bae8a224ea9f71
PRE_PROMOTION_AHEAD_COUNT=14
PRE_PROMOTION_BEHIND_COUNT=0
MERGE_BASE_EQUALS_REMOTE_MAIN=true
MAIN_PROMOTION_MODE=FAST_FORWARD_ONLY
REBASE_USED=false
SQUASH_USED=false
FORCE_PUSH_USED=false
```

## CI capability boundary

The former public replay path permitted a restricted-input skip to look like a
complete check. The hardened contract instead requires a project-owned
synthetic full-pipeline fixture and independently validates the committed,
public-safe snapshot. Restricted source artifacts and source-native text remain
outside GitHub. A real replay is run only with
`COFFEE_FLAVOR_RESTRICTED_ROOT` in an owner-controlled environment; absent
restricted input in public CI is reported as
`NOT_EXECUTED_PUBLIC_CI_RESTRICTED_INPUT_INTENTIONALLY_UNAVAILABLE`.

The long PostgreSQL verification is wrapped with a 60-second-or-less heartbeat
that preserves the child exit code and CI timeout while publishing phase and
elapsed-time progress only.

## Scientific checkpoint sealed for promotion

```text
FROZEN_40K_SOURCE_ASSERTION_COUNT=40030
ACQUIRED_CANDIDATE_SOURCE_ASSERTION_COUNT=50034
SMOKE_RESULT=SEEN_FORM_LOOKUP_ONLY
MODEL_ELIGIBLE_ASSERTION_COUNT=0
HUMAN_REVIEWED_NORMALIZED_FORM_COUNT=0
TRAINING_CORPUS_FROZEN=false
S2_EXPLICIT_PROFESSIONAL_REFERENCE_RELATION_COUNT=0
BATCH6_SEMANTIC_BENCHMARK_STATUS=REVIEW_REQUIRED
POST40K_NON_COE_DISCOVERY_STATUS=NOT_EXECUTED_DURING_COE_CONTINUATION
SCHEMA_CHANGED=false
NEW_MIGRATION_COUNT=0
PRODUCT_WORK_INCLUDED=false
```

The promotion does not create a training claim, ontology-adjudication claim,
schema migration, or product/PWA change. Historical checkpoints remain
preserved and no history rewrite is part of this promotion.
