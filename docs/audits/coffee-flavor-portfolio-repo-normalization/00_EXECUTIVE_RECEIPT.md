# Portfolio and repository normalization — executive receipt

This receipt records the portfolio narrative, repository information
architecture, user-research contracts, ML-readiness documentation, generated
public status, public-claim controls, presentation surface, and reproducible
screenshots added on the dedicated normalization branch.

The pass is presentation and documentation work over the validated Round 3M
foundation. It did not acquire external data, collect user data, train a model,
change a database migration, widen rights, change an evidence tier, or alter a
descriptor gate.

## Identity and branch boundary

```text
PHASE_STATUS=PASS_PORTFOLIO_AND_REPOSITORY_NORMALIZATION

SOURCE_BRANCH=codex/coffee-sensory-kb-v0-round3m-descriptor-first-provenance-pilot-20260828
SOURCE_SHA=13b56d2c1d4beec3754ce53edec8954d4e034bce
WORK_BRANCH=codex/coffee-flavor-portfolio-repo-normalization-20260828
FINAL_LOCAL_SHA=SELF_REFERENTIAL_REPORTED_IN_FINAL_RESPONSE
FINAL_REMOTE_SHA=SAME_AS_FINAL_LOCAL_SHA_REPORTED_IN_FINAL_RESPONSE
REMOTE_MAIN_SHA=c3ae9b880d85507a0b8b0298bb94ef013d02f928
WORKTREE_CLEAN=true
```

`FINAL_LOCAL_SHA` cannot literally name the commit containing this receipt
without creating a self-referential hash. The exact final local and remote SHA
is therefore reported in the final execution response after the remote branch
and CI are verified.

## Public product narrative

```text
PUBLIC_PRODUCT_NAME=Coffee Flavor Atlas
PUBLIC_SUBTITLE=An evidence-grounded mobile-first web prototype for translating everyday coffee perception into professional sensory references.
README_REWRITTEN=true
PORTFOLIO_ENTRY_CREATED=true
LONG_FORM_CASE_STUDY_CREATED=true
PROJECT_TIMELINE_CREATED=true
RESEARCH_ITERATION_STORY_CREATED=true
SKILLS_EVIDENCE_MATRIX_CREATED=true
RECRUITER_READING_PATH_CREATED=true
DEMO_SCRIPT_CREATED=true
```

The README contains 1,741 words. The narrative foregrounds the user problem,
current prototype, evidence boundaries, PostgreSQL foundation, negative
research findings, and staged ML path. Round identifiers remain secondary
historical references.

## User research

```text
USER_RESEARCH_DOCUMENT_COUNT=10
USER_FEEDBACK_MINING_CONTRACT_CREATED=true
USER_DATA_COLLECTION_CONTRACT_CREATED=true
USER_INSIGHT_TRACEABILITY_CREATED=true
USER_DATA_COLLECTED=false
INTERVIEW_COUNT=0
USABILITY_SESSION_COUNT=0
SYNTHETIC_USER_QUOTE_COUNT=0
```

The documents define future consent, privacy, retention, withdrawal,
pseudonymization, qualitative coding, feedback mining, interaction events, and
metric interpretation. They do not represent planned fieldwork as completed
research.

## ML and data-role readiness

```text
ML_DOCUMENT_COUNT=9
ML_TASK_COUNT=6
ML_DATA_READINESS_MATRIX_CREATED=true
MODEL_CARD_DRAFT_CREATED=true
DATASET_CARD_DRAFT_CREATED=true
MODEL_RUN_COUNT=0
ML_BASELINE_RUN=false
EMBEDDING_BASELINE_RUN=false
CROSS_ENCODER_RUN=false
DEEP_LEARNING_MODEL_RUN=false
RANKING_MODEL_TRAINED=false
ADAPTIVE_POLICY_TRAINED=false
```

The six task contracts cover descriptor normalization, 5+3 ranking,
co-assertion estimation, question selection, stopping policy, and
consumer-language mapping. The readiness matrix is generated from governed
receipts and keeps acquisition rows separate from reviewed professional and
model-eligible universes.

## Evidence tracks and product presentation

```text
PROFESSIONAL_EVIDENCE_TRACK_DOCUMENTED=true
INDUSTRY_LANGUAGE_TRACK_DOCUMENTED=true
CONSUMER_LANGUAGE_TRACK_DOCUMENTED=true
FIRST_PARTY_USER_DATA_TRACK_DOCUMENTED=true
CONSUMER_FEEDBACK_USED_AS_CORE_PROFESSIONAL_LABEL=false

PWA_STATUS=PLANNED
PWA_PUBLIC_CLAIM_ALLOWED=false
PUBLIC_PROJECT_ROUTE_CREATED_OR_UPDATED=/methodology#project-status
DESKTOP_SCREENSHOT_COUNT=3
MOBILE_SCREENSHOT_COUNT=1
SCREENSHOT_MANIFEST_PASS=true
```

The application is accurately presented as a mobile-first web prototype or a
planned PWA. It has responsive layouts, keyboard access, accessible names, and
reduced-motion behavior, but no web app manifest, installable icons, service
worker, or offline app shell.

## Generated public status and claim controls

```text
PUBLIC_STATUS_GENERATOR_CREATED=true
PUBLIC_STATUS_JSON_CREATED=true
PUBLIC_CLAIMS_REGISTER_CREATED=true
PUBLIC_QUANTITATIVE_CLAIM_COUNT=16
UNSUPPORTED_PUBLIC_CLAIM_COUNT=0
STALE_CURRENT_PHASE_REFERENCE_COUNT=0
RAW_ROW_AS_TRAINING_LABEL_CLAIM_COUNT=0
FALSE_MODEL_CLAIM_COUNT=0
FALSE_PWA_CLAIM_COUNT=0
```

The deterministic generator emits `PROJECT_STATUS.md`, the portfolio facts
JSON, the ML readiness matrix, a public JSON aggregate, and the frontend
TypeScript aggregate. The public-claim linter excludes immutable historical
audit material from current-claim enforcement.

## Preservation boundaries

```text
HISTORICAL_RESEARCH_FILES_MOVED=false
HISTORICAL_AUDIT_FILES_REWRITTEN=false
APPLIED_MIGRATION_FILES_CHANGED=false
NEW_DATABASE_MIGRATION_COUNT=0
RIGHTS_WIDENED=false
EVIDENCE_TIER_CHANGED=false
DESCRIPTOR_GATE_CHANGED=false
```

## Verification

```text
PUBLIC_CLAIM_LINT_PASS=true
MARKDOWN_LINK_VALIDATION_PASS=true
DOCUMENTATION_INDEX_PASS=true
STATUS_GENERATION_DETERMINISTIC_PASS=true
FRONTEND_ACCESSIBILITY_SMOKE_PASS=true
LOCAL_FRONTEND_CI_PASS=true
LOCAL_POSTGRES_CI_PASS=true
REMOTE_FRONTEND_CI_PASS=true
REMOTE_POSTGRES_CI_PASS=true

MAIN_PROMOTION_ALLOWED=false
MAIN_PROMOTION_PASS=false
FORCE_PUSH_USED=false
REMOTE_BACKUP_PASS=true
```

Local web verification included generated-artifact drift checks, public
contracts, formatting, typecheck, 9 unit tests, a production prerender build,
and 15 Playwright checks across desktop, tablet, and mobile profiles. The
accessibility smoke covers keyboard navigation, accessible project-status
links, and reduced-motion behavior.

Local PostgreSQL verification used PostgreSQL 17.11 and two separately named
empty disposable databases. Both applied all 60 migrations, loaded the same
governed artifacts, passed the full database harness, and produced matching
migration, seed, schema, stable-key inventory, validation, ontology, and
historical checkpoint hashes.

The first remote run exposed a CI-only provenance issue: the default
single-commit checkout could not resolve the earlier implementation commit
recorded by the screenshot manifest. The run was cancelled after the frontend
failure, the frontend checkout was changed to retain Git history, and the
replacement run passed without weakening or rewriting screenshot provenance.

```text
REMOTE_CI_RUN_ID=33199679962
REMOTE_FRONTEND_JOB_ID=98945699505
REMOTE_POSTGRES_JOB_ID=98945699685
REMOTE_FRONTEND_DURATION=1m16s
REMOTE_POSTGRES_DURATION=32m39s
```

```text
CLEAN_REBUILD_COUNT=2
MIGRATION_COUNT=60
FOCUSED_ROUND3M_INVARIANT_COUNT=84
NEW_058_POSITIVE_TEST_COUNT=3
NEW_058_NEGATIVE_TEST_COUNT=32
OLD_SELF_ATTESTING_GATE_PATH_COUNT=0
PERSISTED_SYNTHETIC_HUMAN_FIXTURE_COUNT=0
REPRODUCIBILITY_PASS=true
```

## Current limitations and next phase

```text
CURRENT_PROJECT_LIMITATIONS=The current interface is a research-grounded mobile web prototype, not an installable PWA or deployed adaptive model.
CURRENT_DATA_GAPS=The descriptor pilot has 140 admitted assertions, 139 assertion-level de-inflated assertions, 137 record-unique assertions, 8 effective records, 0 reviewed P1/P2 strict assertions, and 0 model-eligible assertions.
CURRENT_USER_RESEARCH_GAPS=No interviews, usability sessions, first-party interaction sessions, or behavioral relevance labels have been collected.
CURRENT_ML_GAPS=No deterministic ML baseline, embedding model, cross-encoder, ranking model, deep model, or adaptive policy has been trained; professional review and model-use rights gates remain closed.
NEXT_RECOMMENDED_PHASE=RUN_SEPARATELY_AUTHORIZED_USER_RESEARCH_PILOT
```

The zero states are deliberate evidence boundaries, not missing receipt data.
The next phase requires separate authorization and must preserve consent,
privacy, rights, review, and evaluation gates.
