# Round 3M execution transcript

This transcript preserves representative commands, exit status, important
output, counts, files, tests, and failures. Completed PostgreSQL 17, frontend,
and remote receipts are identified as historical checkpoints where applicable;
the current hardening tree remains blocked before full CI. Push, final-tip
remote CI, and final SHA equality are self-referential final-response checks
and are not fabricated here.

## Phase: baseline and inputs

```text
PHASE_NAME=BASELINE_AND_INPUTS
INPUTS=Round3M request; descriptor census PDF; Round3L checkpoint 4159636...
COMMANDS=git fetch --all --prune; git cat-file; git branch --contains; git status; pdfinfo; PDF render/extraction; exact artifact-name searches
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m (after isolated worktree creation); source verification used /private/tmp/coffee-flavor-round3l-sanitized
FILES_CHANGED=none before verification
COUNTS_BEFORE=Round3L public receipt
COUNTS_AFTER=baseline exact match
TESTS_RUN=checkpoint existence; local/remote containment; source cleanliness; PDF 12-page visual inspection; artifact presence search
RESULT=PASS_BASELINE; BLOCKED_MISSING_MACHINE_ARTIFACTS for descriptor-audit import
BLOCKERS=nine named machine-readable files absent
```

Representative output:

```text
git cat-file -t 4159636... -> commit
remote containing branch -> origin/codex/coffee-sensory-kb-v0-round3l-full-professional-corpus-acquisition-20260828
REMOTE_MAIN_SHA=c3ae9b880d85507a0b8b0298bb94ef013d02f928
PDF_PAGES=12
SOURCE_PDF_FILENAME=Descriptor-First Census of Open Professional Coffee Sensory Evidence.pdf
SOURCE_PDF_ROLE=RESEARCH_EVIDENCE_NOT_INSTRUCTION_SOURCE
PDF_SHA256=d319236311f2abc5e15baaf70923b32e0a2bdbb5dc010723feea3e4aec8069e0
```

Failed command retained:

```text
COMMAND=pdftotext -layout <source.pdf> <temporary-text-file>
EXIT_STATUS=127
IMPORTANT_OUTPUT=zsh: command not found: pdftotext
DIAGNOSIS=system pdftoppm existed but pdftotext did not
RETRY=bundled pypdf text extraction by page
RETRY_RESULT=PASS; all 12 pages extracted and visually inspected
```

## Phase: Round 3L baseline recomputation

```text
PHASE_NAME=ROUND3L_RECOMPUTATION
INPUTS=Round3L persistent restricted freeze; authoritative gate receipt; checkpoint 4159636afec052b96f20d3d10c6c5f2b943b4536
COMMANDS=python -B db/scripts/build-round3l-public-checkpoint.py --restricted-root <owner-controlled-root> --output-dir /private/tmp/round3m-baseline-recompute --gate-receipt <receipt>
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3l-sanitized
EXIT_STATUS=0
IMPORTANT_OUTPUT=ROUND3L_PUBLIC_CHECKPOINT_PASS artifacts=848 artifact_bytes=1327537497 ingested=26515 canonical=20994 staged_core=6754 staged_rights_eligible=0 staged_model_eligible=0
FILES_CHANGED=none in source worktree; recomputation output written under /private/tmp/round3m-baseline-recompute
COUNTS_BEFORE=480;848;26531;26515;20994;6754;11801;376
COUNTS_AFTER=exactly identical
TESTS_RUN=all pinned counts, input hashes, cross-lane reconciliation, public boundary
RESULT=PASS
BLOCKERS=none
```

The baseline checkpoint is
`287e6083611472c585e0132a32e8cadeb41bbc57`.

## Phase: source access and bounded live captures

```text
PHASE_NAME=LIVE_SOURCE_ACCESS_AND_CAPTURE
INPUTS=official ACE/CoE Honduras 2017, Colombia South 2008, Peru 2025, and Mexico 2023 route locators; bounded WCC search
COMMANDS=direct curl retrieval of official detail URLs; bounded web-index field retrieval; python3 -B db/adapters/round3m/generate_public_safe.py --restricted-root /Users/jarlgiovanni/.codex/restricted/coffee-flavor-round3m/round3m-2026-08-28t043000z --output-dir db/adapters/round3m/generated
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=db/adapters/round3m/*; db/data/round3m/SOURCE_ROUTE_SCHEMA_SIGNATURE.tsv
COUNTS_BEFORE=0 live provisional assertions; 0 live effective-record bridges
COUNTS_AFTER=3 bounded captures; 8 effective records; 140 provisional assertions; 73 P2; 67 unresolved
TESTS_RUN=18 test-round3m-live-adapters.py cases with Round3M and Round3L restricted roots
RESULT=PASS_BOUNDED_CAPTURE_PILOT; FULL_PAGE_BODY_ACQUISITION_STATUS=BLOCKED_ENVIRONMENT_POLICY
BLOCKERS=Mexico detail-body drift; no completed filled WCC corpus; official full page bodies unavailable
```

Capture receipts:

```text
HONDURAS_CAPTURE_SHA256=2ecb916106615174a12a05a01589ef2799d168765880a5b83e5416540f562053 records=5
COLOMBIA_CAPTURE_SHA256=717b9e1a3ef6400fa334ddbaf80cb592125ddbdecaf67b0d6271f94bf7878033 records=2
PERU_CAPTURE_SHA256=44b83f0786a9909c3f55fa4ba0f148aee15d75e54ae571918cc4350372b2a0f9 records=1
RESTRICTED_MANIFEST_SHA256=b36fbe8a959b099b1a3a073b045c3d6ac74e31043f090d2fd88bd78c3290e51d
CAPTURE_SCOPE=WEB_INDEX_FIELD_CAPTURE_NOT_FULL_PAGE_BODY
RAW_SOURCE_TEXT_PUBLISHED=false
```

Failed access attempt retained:

```text
COMMAND=direct curl retrieval of official CoE detail pages
EXIT_STATUS=network sandbox blocked; escalated execution rejected
IMPORTANT_OUTPUT=official full page body could not be acquired in the execution environment
DIAGNOSIS=environment policy/access failure, not evidence that the source field is absent
CONTINUATION=preserve bounded field captures, hashes, locators, and explicit non-storage reason; continue other routes
```

One live-test invocation initially used the wrong prior-round restricted root:

```text
COMMAND=env ROUND3M_RESTRICTED_ROOT=<correct> ROUND3L_RESTRICTED_ROOT=/Users/jarlgiovanni/.codex/restricted/coffee-flavor-round3l/round3l-2026-08-27t043000z python3 -B db/scripts/test-round3m-live-adapters.py
EXIT_STATUS=1
DIAGNOSIS=the Round3L timestamp/path was incorrect
RETRY_ROOT=/Users/jarlgiovanni/.codex/restricted/coffee-flavor-round3l/round3l-2026-08-28t040000z
RETRY_RESULT=16 tests passed at that checkpoint; final hardened suite later expanded to 18
```

## Phase: existing candidates and public-safe descriptor artifacts

```text
PHASE_NAME=EXISTING_376_AND_LIVE_LEDGER
INPUTS=Round3L restricted checkpoint; five governed AVPA 2021-2025 artifacts; report PDF; public-safe live export
COMMANDS=python3 -B db/scripts/build-round3m-review-artifacts.py --restricted-root <Round3L restricted root> --report-pdf <descriptor-census PDF> --output-dir db/data/round3m --live-assertion-export db/adapters/round3m/generated/PUBLIC_SAFE_LIVE_ASSERTIONS.tsv --research-artifact-root <searched input root>
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=db/data/round3m review, provenance, rights, repeat, normalization, co-assertion, template, manifest, and checksum artifacts
COUNTS_BEFORE=376 staged gate-type candidates; 0 reviewed; 0 model eligible
COUNTS_AFTER=376 NON_DESCRIPTOR; 140 HUMAN_REVIEW_REQUIRED; 516 complete queue decisions; 140 admitted provisional ledger rows; 0 reviewed; 0 model eligible
TESTS_RUN=artifact schemas; pinned input hashes; exact disposition; source-text exclusion; deterministic generation; intentional contract failures
RESULT=PASS_PUBLIC_SAFE_ARTIFACT_BUILD
BLOCKERS=9 machine-readable report artifacts absent; no human review; no affirmative model rights
```

An independent deterministic-build check ran the same builder twice with the
governed Round 3L root, the descriptor census PDF, and the live export, writing
to separate temporary directories:

```text
COMMANDS=python3 -B db/scripts/build-round3m-review-artifacts.py ... --output-dir <temporary-output-one>; python3 -B db/scripts/build-round3m-review-artifacts.py ... --output-dir <temporary-output-two>; diff -rq <temporary-output-one> <temporary-output-two>
COUNTS_AFTER=22 generated files in each temporary output
DIFF_RESULT=empty
RESULT=ROUND3M_REVIEW_BUILD_DETERMINISM_PASS
FILE_OR_DATA_CHANGES=temporary verification outputs only; governed/public checkpoint unchanged by the comparison
```

Representative exact outputs:

```text
DESCRIPTOR_REVIEW_QUEUE_ROWS=516
DESCRIPTOR_PROVISIONAL_DECISION_ROWS=516
DESCRIPTOR_RIGHTS_DECISION_ROWS=3096
RIGHTS_UNKNOWN_ROWS=2658
RIGHTS_PENDING_ROWS=438
DESCRIPTOR_ASSERTION_LEDGER_ROWS=140
ASSERTION_LEVEL_DEINFLATED_ROWS=139
RECORD_LEVEL_UNIQUE_ROWS=137
COASSERTION_EVENT_ROWS=508
HUMAN_CONFIRMED_ROWS=0
MODEL_ELIGIBLE_ROWS=0
```

Intentional artifact-contract mutations were rejected as designed:

```text
MUTATION=descriptor report hash drift
EXIT_STATUS=65
IMPORTANT_OUTPUT=ROUND3M_REVIEW_ARTIFACT_CONTRACT_ERROR: descriptor-first report hash drift

MUTATION=SOURCE_ROUTE_YIELD.tsv header drift
EXIT_STATUS=65
IMPORTANT_OUTPUT=ROUND3M_REVIEW_ARTIFACT_CONTRACT_ERROR: header mismatch
```

A non-intentional checksum ordering failure also occurred after generated files
changed:

```text
COMMAND=python3 -B db/scripts/test-round3m-artifact-contract.py
EXIT_STATUS=1
DIAGNOSIS=ROUND3M_MANIFEST.json/SHA256SUMS were stale relative to regenerated final artifacts
RETRY=rerun finalize-round3m-artifacts.py, then rerun the validator
RETRY_RESULT=ROUND3M_ARTIFACT_CONTRACT_PASS census_items=480 source_routes=131 review_queue_items=516 rights_decisions=3096 live_assertions=140 coassertion_events=508
```

The pilot checkpoint is
`8236adbba3d4d1754dfedc1bb4fd6f9ab3b775c0`.

## Phase: provenance, rights, repeat, and C0/C1 controls

```text
PHASE_NAME=GOVERNANCE_AND_ANTI_INFLATION_CONTROLS
INPUTS=516 candidate decisions; 140 admitted provisional assertions; Round3L 26515-row staged publication ledger
COMMANDS=build-round3m-review-artifacts.py; test-round3m-artifact-contract.py; test-round3m-live-adapters.py; generate C0_C1_EVIDENCE_RECEIPT.json
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=DESCRIPTOR_PROVENANCE_DECISION.tsv; DESCRIPTOR_RIGHTS_DECISION.tsv; DUPLICATE_REPEAT_DECISION.tsv; PUBLICATION_LAYER_RELATION.tsv; DESCRIPTOR_NORMALIZATION_DECISION.tsv; COASSERTION_EVENT.tsv; C0_C1_EVIDENCE_RECEIPT.json; ORGANIZER_REQUEST_MATRIX.tsv; LOW_YIELD_EXCLUSION_REGISTER.tsv
COUNTS_BEFORE=0 Round3M purpose-rights rows; 0 Round3M repeat decisions; 0 Round3M pair rows
COUNTS_AFTER=3096 purpose-rights rows (2658 UNKNOWN, 438 PENDING); 1 within-field repeat loss; 2 cross-observation repeat losses; 508 within-record P2 pair events; 34 NOT_SENT request rows; 11 zero-budget low-yield route classes
TESTS_RUN=public visibility is not permission; pending/unknown blocks model eligibility; no translation/roast/preparation inference; layer separation; within-record pair boundary; rights completeness
RESULT=PASS_GOVERNANCE_CONTROLS; human=0; expert=0; model_eligible=0
BLOCKERS=ACE field authorship/frequency semantics; affirmative model/deployment rights; human review
```

C0/C1 representative outputs:

```text
ROUND3L_STAGED_PUBLICATION_ROWS=26515
FRESH_PREPARATION_CONFIRMED=13157
FRESH_PREPARATION_PENDING=13085
FRESH_PREPARATION_NOT_APPLICABLE=273
C0_REPORTED=495
C0_REPORTED_UNRESOLVED=39
DIRECT_ROAST_VALUE_AND_SCHEME_PRESENT=7683
C1_REPORTED_UNRESOLVED=7683
REVIEWED_C1_MAPPING_COUNT=0
SEMANTIC_INFERENCE_USED_COUNT=0
```

## Phase: initial descriptor schema and active gates

```text
PHASE_NAME=INITIAL_SCHEMA_AND_GATE_REMEDIATION
INPUTS=55 immutable Round3L migrations; active readiness SQL; Round3M descriptor gate requirements
COMMANDS=inspect executable readiness views/functions/tests; add db/055_round3m_descriptor_provenance_review_rights.sql; add db/056_round3m_descriptor_gate_contract.sql; psql -X --set=ON_ERROR_STOP=1 --file=db/tests/round3m_gate_schema.sql
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=db/055_round3m_descriptor_provenance_review_rights.sql; db/056_round3m_descriptor_gate_contract.sql; db/tests/round3m_gate_schema.sql
COUNTS_BEFORE=55 migrations; deprecated record-first gates could still be confused with active readiness
COUNTS_AFTER=57 migrations at reproducibility checkpoint bdc9bca15dad58a910a943ab5fed41176cc77af8
TESTS_RUN=initial gate/schema suite at the reproducibility checkpoint; superseded by the release-contract audit below
RESULT=ROUND3M_GATE_SCHEMA_PASS; legacy training authority false
BLOCKERS=human-reviewed universe empty; rights not affirmative
```

## Phase: release-contract audit and forward-only recovery

```text
PHASE_NAME=RELEASE_CONTRACT_AUDIT
INPUTS=bdc9bca15dad58a910a943ab5fed41176cc77af8 reproducibility checkpoint; applied migration fingerprints; generated DESCRIPTOR_GATE_STATUS.tsv; authoritative SQL gate contract; review-supersession and publication-layer views
COMMANDS=compare migrations 055/056 with checkpoint fingerprints; compare generated gate rows field-by-field with SQL; inspect current-review-receipt filters; add forward migration db/057_round3m_release_contract_hardening.sql; extend round3m_gate_schema.sql
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=db/057_round3m_release_contract_hardening.sql; db/tests/round3m_gate_schema.sql; db/data/round3m/DESCRIPTOR_GATE_STATUS.tsv; gate generator/validator and restricted-capture validation code
COUNTS_BEFORE=57 migrations; generated gate naming/universe drift; 15 generated NA rows; stale review targets could remain in per-label/multi-target metrics
COUNTS_AFTER=intermediate checkpoint only: 58 migrations; migrations 055/056 byte-identical to bdc9bca15dad58a910a943ab5fed41176cc77af8; 7 gates; 56 exact SQL-parity criteria; 0 pass; 17 NA and non-passing; blockers data=38/review=13/rights=6 (non-exclusive); current leaf targets only
TESTS_RUN=intermediate checkpoint only: 17 named positive paths; 13 named negative checks; 3 policy/constraint assertions; 20 invariant queries; 18 restricted live-adapter tests
RESULT=SUPERSEDED_INTERMEDIATE_RELEASE_CONTRACT_CHECKPOINT; later 059 hardening and final marker-derived counts remain pending
BLOCKERS=human-reviewed universe empty; rights not affirmative
```

The audit first found that release hardening had been drafted by editing the
already-applied migrations 055 and 056:

```text
FAILED_ATTEMPT=direct modifications to migrations 055 and 056 during release hardening
RESULT=FAIL_FORWARD_ONLY_MIGRATION_AUDIT
DIAGNOSIS=applied migration fingerprints must remain immutable
RECOVERY=restore 055/056 byte-for-byte from bdc9bca15dad58a910a943ab5fed41176cc77af8; move all new hardening into forward migration 057
RECOVERY_RESULT=055/056 have zero diff from the checkpoint; migration count advanced from 57 to 58; no applied history rewritten
```

The same audit found semantically stale gate and review surfaces:

```text
FAILED_ATTEMPT=generated gate artifact matched headline row counts but not authoritative SQL gate/metric identifiers and universes
RESULT=FAIL_GATE_ARTIFACT_PARITY_AUDIT
RECOVERY=generate and validate all 56 fields against the SQL contract; resulting surface is 7 gates / 56 criteria / 0 pass / 17 NA

FAILED_ATTEMPT=per-label and multi-target metrics did not uniformly require a current leaf review receipt
RESULT=FAIL_REVIEW_SUPERSESSION_AUDIT
RECOVERY=exclude stale label targets and prohibit assertions from restoring a superseded review pointer; add positive stale_label_targets_excluded and negative assertion_cannot_restore_superseded_review_pointer
```

Two read-only release diagnostics also failed without changing files or data:

```text
COMMAND=rg inspection containing the unmatched zsh glob db/057*
EXIT_STATUS=1 before rg executed
DIAGNOSIS=zsh nomatch expansion only; not a repository or database failure
RETRY=repeat the inspection with explicit db/057_round3m_release_contract_hardening.sql and related filenames
RETRY_RESULT=inspection completed

COMMAND=ps -ax -o pid=,etime=,command= filtered for the PostgreSQL verification process
EXIT_STATUS=1
IMPORTANT_OUTPUT=operation not permitted
DIAGNOSIS=sandbox process-list restriction only
RECOVERY=use agent-status coordination to confirm the PostgreSQL run remained active; no escalation required
FILE_OR_DATA_CHANGES=none
```

Named SQL negative mutations:

```text
human_state_without_receipt
codex_cannot_create_human_receipt
public_visibility_not_model_permission
descriptor_route_index_must_match_source_artifact
descriptor_hash_scope_must_match_source_artifact
descriptor_nonstorage_reason_must_match_source_artifact
secondary_layer_cannot_become_canonical_counting_assertion
cross_record_coassertion_rejected
not_applicable_model_rights_never_supports_eligibility
stale_review_receipt_pointer_after_supersession
superseded_receipt_excluded_from_human_universe
superseded_receipt_validation
assertion_cannot_restore_superseded_review_pointer
```

The gate/schema checkpoint is
`3b1f8c19ec0215e570c475cadd1ba3f226805235`.

## Phase: database loader and reproducibility

```text
PHASE_NAME=ARTIFACT_IMPORT_AND_TWO_CLEAN_REBUILDS
INPUTS=57 migrations; finalized Round3M machine artifacts; PostgreSQL 17.11 disposable server
COMMANDS=PGHOST=127.0.0.1 PGPORT=55437 PGUSER=postgres PGDATABASE=postgres COFFEE_KB_ALLOW_DATABASE_DROP=1 COFFEE_KB_REBUILD_DB_ONE=coffee_sensory_kb_v0_round3m_c COFFEE_KB_REBUILD_DB_TWO=coffee_sensory_kb_v0_round3m_d COFFEE_KB_PG_DUMP_CONTAINER=coffee-round3m-pg17 bash db/scripts/ci-verify.sh
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=db/scripts/load-round3m-artifacts.{sh,sql}; db/scripts/test-round3m-artifact-contract.py; db/scripts/{test,ci-verify,rebuild-twice}.sh; package.json; finalized manifest/time/checksum artifacts
COUNTS_BEFORE=0 rows in each separate disposable database
COUNTS_AFTER=each historical rebuild: 11 families; 135 route rows; 4 schemas; 8 source artifacts; 8 effective records; 516 queue/decisions; 3096 rights; 140 assertions; 139 assertion-level; 137 record-unique; 508 pairs; 0 human; 0 model eligible
TESTS_RUN=artifact contract; live adapters; all database tests; Round3M gate schema; deterministic inventory comparison across two empty databases
RESULT=CLEAN_REBUILD_COUNT=2; REPRODUCIBILITY_PASS=true; CI_VERIFY_DATABASE_PASS=true
BLOCKERS=none for local PostgreSQL verification
```

Earlier PostgreSQL attempts and diagnoses are retained:

```text
COMMAND=initdb for local PostgreSQL 16 cluster under /tmp/round3m_pg16.*
EXIT_STATUS=failed during bootstrap
IMPORTANT_OUTPUT=dynamic shared memory selected sysv; bootstrap did not complete
DIAGNOSIS=local PostgreSQL 16 shared-memory/environment failure

COMMAND=db/scripts/migration-plan.sh list
EXIT_STATUS=64
DIAGNOSIS=list is not a supported helper operation
RETRY=db/scripts/migration-plan.sh paths
RETRY_RESULT=57 migration paths discovered

COMMAND=bash db/scripts/rebuild-twice.sh against available PostgreSQL 16 server
EXIT_STATUS=65
IMPORTANT_OUTPUT=PostgreSQL 17 or newer is required
DIAGNOSIS=expected version guard; no migration/data failure
```

Docker recovery was required before the PostgreSQL 17 run:

```text
COMMAND=docker run / docker builder prune checks
EXIT_STATUS=daemon internal filesystem read-only; initial prune failed
DIAGNOSIS=Docker VM storage pressure/read-only state; host had 5.9 GB free and 7.376 GB reclaimable build cache
RECOVERY=restart Docker Desktop via osascript; terminate only Docker host processes; reopen; prune stale build cache older than 24 hours
RECOVERY_RESULT=2.871 GB build cache reclaimed; no images, containers, or volumes deleted
SERVER=docker postgres:17-bookworm PostgreSQL 17.11; container coffee-round3m-pg17; tmpfs data; localhost port 55437
```

The first full PostgreSQL 17 run completed migrations, artifact loads, and the
database tests in both databases, then failed during deterministic inventory
generation:

```text
COMMAND=same ci-verify.sh flow with disposable databases coffee_sensory_kb_v0_round3m_a and coffee_sensory_kb_v0_round3m_b
EXIT_STATUS=1
IMPORTANT_OUTPUT=second macOS mktemp call reused the literal stable-key-query.XXXXXX.sql filename
DIAGNOSIS=macOS mktemp expands a trailing X template only; the .sql suffix prevented randomization
FIX=use suffix-free stable-key-query.XXXXXX template
RETRY_RESULT=both clean rebuilds and all reproducibility comparisons passed
```

Release hardening later required a fresh full run over all 58 migrations. Its
first connection attempt failed before any database work:

```text
COMMAND=db/scripts/ci-verify.sh against the earlier PostgreSQL 17 container on localhost port 55437
EXIT_STATUS=1
IMPORTANT_OUTPUT=fe_sendauth: no password supplied
DIAGNOSIS=stale container authentication state; no migration, artifact, or test failure
FILE_OR_DATA_CHANGES=none
RECOVERY=start a new isolated PostgreSQL 17 container with trust authentication on localhost port 55438
```

The first full run on that isolated server was then deliberately stopped when
an independent release audit exposed an additional anti-inflation gap:

```text
COMMAND=db/scripts/ci-verify.sh against isolated trust-auth PostgreSQL 17 on localhost port 55438
EXIT_STATUS=130 (intentional cancellation during Round3M tests)
FINDING=the same descriptor pair could inflate co-assertion count by using alternate coassertion_set_key values
DIAGNOSIS=pair uniqueness was not yet enforced across alternate set keys for the same effective record/source observation
ACTION=cancel the obsolete run; add an invariant and negative regression; rerun from fresh empty databases after the forward fix
RESULT=NO_FINAL_REPRODUCIBILITY_RESULT_CLAIMED_FROM_CANCELLED_RUN
```

Later normalization/challenge hardening used isolated compile probes before a
full migration-plan run. Probe 6 exposed a PostgreSQL function-arity limit:

```text
FAILED_ATTEMPT=the first draft-059 gate test fixture omitted two newly required NOT NULL digest columns
EXIT_STATUS=1
DIAGNOSIS=test-fixture/schema drift during active forward-migration development; not a corpus-data failure
RECOVERY=update the fixture to provide the governed digest bindings before the next focused probe
LIMITATION=subsequent focused results were superseded by further 059 edits and are not current-tree full-CI evidence
```

```text
PROBE_NAME=ROUND3M_059_COMPILE_PROBE_6
COMMAND=clean PostgreSQL 17 compile/validation probe through db/059_round3m_normalization_challenge_contract.sql
EXIT_STATUS=1
IMPORTANT_OUTPUT=jsonb_build_object cannot take more than 100 arguments
DIAGNOSIS=the canonical semantic payload attempted to construct one JSON object beyond PostgreSQL's function-argument limit
RECOVERY=split the canonical payload construction into bounded JSONB components
FILE_OR_DATA_CHANGES=no corpus rows; forward migration source corrected before finalization
```

The next isolated probe compiled the corrected payload and closed every
validation available in that probe, but it is not a substitute for the pending
contiguous migration plan or full two-rebuild CI:

```text
PROBE_NAME=ROUND3M_059_COMPILE_PROBE_7
RESULT=PASS_FOCUSED_COMPILE_AND_VALIDATION
VALIDATION_RESULT=64/64 passed
LIMITATION=focused clean compile probe only; not final current-tree reproducibility evidence
```

Chronology hardening then advanced the focused result without closing the
migration-sequence or full-CI blockers:

```text
PROBE_NAME=ROUND3M_059_CHRONOLOGY_PROBE_10
INPUTS=fresh PostgreSQL 17 database; migrations 000-057; draft 059; focused normalization and full Round3M gate-schema tests
COMMANDS=apply migrations 000-057 explicitly; apply db/059_round3m_normalization_challenge_contract.sql explicitly; query audit.run_round3m_gate_validation_queries(); run db/tests/round3m_normalization_challenge_contract.sql; run db/tests/round3m_gate_schema.sql
EXIT_STATUS=0
RESULT=PASS_FOCUSED_COMPILE_AND_VALIDATION
GLOBAL_VALIDATION_RESULT=68/68 passed
PRE_V059_VALIDATION_COUNT=49
V059_VALIDATION_DELTA=19
NORMALIZATION_CHALLENGE_TEST_EXIT_STATUS=0
ROUND3M_GATE_SCHEMA_TEST_EXIT_STATUS=0
IMPORTANT_OUTPUT=ROUND3M_GATE_SCHEMA_PASS
LIMITATION=focused structural PostgreSQL 17 probe only; it does not prove an acquired human review event, qualified reviewer, or releasable challenge credit; contiguous migration plan, artifact regeneration, and two-clean-rebuild CI remain pending
```

The final adversarial audit found that the missing 058 contract is also the
required external-evidence bridge, not merely a migration-number gap:

```text
ADVERSARIAL_AUDIT_RESULT=P0_DRAFT_059_SELF_ATTESTING_WITHOUT_058
FINDING=draft 059 accepts caller-chosen reviewer identity, human-event/evidence hashes, and locators without foreign-key and verified-hash binding to an acquired review artifact
FIXTURE_EFFECT=transaction-local structural +1 only
AUTHORITATIVE_QUALIFIED_HUMAN_CHALLENGE_CREDIT_COUNT=0
FOCUSED_PROBE_SCOPE=STRUCTURAL_ONLY
REQUIRED_058=immutable dated reviewer qualification/admission plus acquired reviewer-decision evidence artifact, foreign-key, and verified-hash binding
REQUIRED_059_CHANGE=wire every reviewer identity, event/evidence hash, decision, and locator used for challenge credit to the approved 058 contract
RELEASE_RULE=no qualified-human challenge credit is releasable before both migrations and their full validation pass
```

The release migration inventory still had a blocking sequence gap at this
checkpoint:

```text
COMMAND=bash db/scripts/migration-plan.sh count
EXIT_STATUS=65
IMPORTANT_OUTPUT=migration position 58 must start with 058_; found 059_round3m_normalization_challenge_contract.sql.
DIAGNOSIS=db/059 exists while db/058 is absent; the migration plan fails closed before database work, and 059 lacks authoritative acquired-review-artifact binding without 058
STATUS=P0_MISSING_058_PENDING_EXPLICIT_USER_APPROVAL
RESULT=NO_FINAL_MIGRATION_OR_CI_RESULT_CLAIMED
```

Representative markers from the completed 57-migration reproducibility
checkpoint (before release hardening):

```text
ROUND3M_ARTIFACT_LOAD_PASS=true
ROUND3M_VALIDATION_PASS=true
ROUND3M_GATE_SCHEMA_PASS
DATABASE_TEST_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true
CI_VERIFY_DATABASE_PASS=true
```

The reproducibility checkpoint is
`bdc9bca15dad58a910a943ab5fed41176cc77af8`.

Its remote baseline workflow also passed:

```text
REMOTE_BASELINE_WORKFLOW_RUN_ID=33151084412
REMOTE_BASELINE_HEAD_SHA=bdc9bca15dad58a910a943ab5fed41176cc77af8
REMOTE_BASELINE_FRONTEND_JOB_ID=98782973168
REMOTE_BASELINE_FRONTEND_JOB_RESULT=success
REMOTE_BASELINE_POSTGRES17_JOB_ID=98782973442
REMOTE_BASELINE_POSTGRES17_JOB_RESULT=success
LIMITATION=run predates the audit documentation checkpoint and does not verify the final branch tip
```

## Phase: intermediate public artifact checkpoint

```text
PHASE_NAME=INTERMEDIATE_PUBLIC_ARTIFACT_CHECKPOINT
INPUTS=validated public-safe Round3M artifacts and generated live adapter receipts
COMMANDS=python3 -B db/scripts/finalize-round3m-artifacts.py --started-at 2026-08-28T04:56:44Z --ended-at 2026-08-28T08:09:06Z --phase-status PASS_DESCRIPTOR_PILOT_NOT_TRAINING_READY
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=db/data/round3m/ANALYST_TIME_LOG.tsv; ROUND3M_EXPECTED_STATE.tsv; ROUND3M_MANIFEST.json; SHA256SUMS
COUNTS_BEFORE=no finalized analyst-time/expected-state checkpoint
COUNTS_AFTER=34 public artifact files; 1 analyst-time row; 192.367 elapsed analyst-equivalent minutes; automated runtime NA_NOT_INSTRUMENTED_FROM_TASK_START
TESTS_RUN=finalizer pinned counts and policy invariants; SHA256 manifest; python3 -B db/scripts/test-round3m-artifact-contract.py
RESULT=script emitted ROUND3M_FINAL_ARTIFACTS_PASS and ROUND3M_ARTIFACT_CONTRACT_PASS for this intermediate checkpoint
BLOCKERS=final current-tree regeneration pending; automated runtime was not comprehensively instrumented from task start; no zero substituted
```

This timestamp belongs to the current generated artifact receipt but is not a
final release timestamp. When the finalizer is rerun after the hardening audit,
its end time, elapsed minutes, manifest, and checksums must advance together;
the earlier value must not be relabeled as the later total.

## Phase: historical frontend checkpoint and remote pending state

```text
PHASE_NAME=HISTORICAL_FRONTEND_CHECKPOINT_AND_REMOTE_PENDING
INPUTS=Round3M branch after local database reproducibility checkpoint
COMMANDS=COFFEE_CI_NPM_BIN=/private/tmp/round3m-npm bash scripts/ci-verify-web.sh
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=none by the check
COUNTS_BEFORE=3 unformatted new Markdown files
COUNTS_AFTER=documentation formatting remediated in this audit documentation checkpoint
TESTS_RUN=fail-fast CI contract; Prettier; TypeScript check; 9 Vitest tests; production prerender; 12 Playwright smoke paths
RESULT=historical checkpoint emitted CI_VERIFY_WEB_PASS=true after documentation and sandbox-loopback retries
BLOCKERS=final current-tree local web CI and remote final-tip post-commit checks are not yet represented in this commit
```

Failed frontend attempt retained:

```text
EXIT_STATUS=1
IMPORTANT_OUTPUT=prettier --check reported docs/research/.../01_BASELINE_AND_PRECEDENCE.md, docs/research/.../03_SOURCE_CENSUS_RECONCILIATION.md, and docs/audits/.../08_KNOWN_BLOCKERS.md
DIAGNOSIS=documentation formatting only; no application/test/database failure
```

The corrected in-sandbox retry exposed an environment-only browser-server
failure before the authorized successful retry:

```text
COMMAND=COFFEE_CI_NPM_BIN=/private/tmp/round3m-npm bash scripts/ci-verify-web.sh
EXIT_STATUS=1
IMPORTANT_OUTPUT=listen EPERM: operation not permitted ::1
DIAGNOSIS=sandbox loopback-bind restriction, not application or test failure
RETRY=run the same bounded CI command outside the sandbox
RETRY_RESULT=format pass; fail-fast contract pass; typecheck pass; 9 Vitest tests pass; production prerender pass; 12 Playwright smoke paths pass; CI_VERIFY_WEB_PASS=true
```

## Phase: current local frontend CI

```text
PHASE_NAME=CURRENT_LOCAL_FRONTEND_CI
INPUTS=current Round3M working tree after documentation and release-hardening edits
COMMANDS=npm run ci:verify:web inside sandbox; retry the same command outside sandbox after the loopback-bind failure
WORKING_DIRECTORY=/private/tmp/coffee-flavor-round3m
FILES_CHANGED=none by the verification commands
COUNTS_BEFORE=current generated artifacts and current frontend/test tree
COUNTS_AFTER=generated drift pass; 2 Vitest files / 9 tests pass; 12 of 12 Playwright smoke paths pass
TESTS_RUN=generated-drift contract; format; fail-fast contract; TypeScript; Vitest; production prerender; Playwright smoke suite
RESULT=LOCAL_FRONTEND_CI_PASS=true; CI_VERIFY_WEB_PASS=true
BLOCKERS=remote frontend CI pending; current PostgreSQL/full reproducibility CI blocked by missing 058
```

The first current-tree attempt failed only at the sandbox network boundary and
was retried unchanged outside the sandbox:

```text
COMMAND=npm run ci:verify:web
EXIT_STATUS=1
IMPORTANT_OUTPUT=production prerender failed with listen EPERM ::1
DIAGNOSIS=sandbox loopback-bind restriction; generated drift, format, fail-fast, typecheck, and unit tests had already passed
RETRY=run npm run ci:verify:web outside the sandbox
RETRY_EXIT_STATUS=0
RETRY_RESULT=generated drift pass; format pass; fail-fast pass; typecheck pass; 2 Vitest files / 9 tests pass; production prerender pass; Playwright 12/12 pass; CI_VERIFY_WEB_PASS=true
LIMITATION=local frontend verification only; no remote-CI or PostgreSQL result inferred
```

Remote and final self-referential fields remain:

```text
FINAL_LOCAL_SHA=NA_SELF_REFERENTIAL_REPORTED_IN_FINAL_RESPONSE
FINAL_REMOTE_SHA=NA_SELF_REFERENTIAL_REPORTED_IN_FINAL_RESPONSE
WORKTREE_CLEAN=NA_POST_COMMIT_VERIFICATION_REPORTED_IN_FINAL_RESPONSE
REMOTE_FRONTEND_CI_PASS=NA_POST_COMMIT_VERIFICATION_REPORTED_IN_FINAL_RESPONSE
REMOTE_POSTGRES_CI_PASS=NA_POST_COMMIT_VERIFICATION_REPORTED_IN_FINAL_RESPONSE
REMOTE_BACKUP_PASS=NA_POST_COMMIT_VERIFICATION_REPORTED_IN_FINAL_RESPONSE
```
