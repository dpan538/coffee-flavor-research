# Documentation normalization executive receipt

Date: 2026-08-24

Status: `PHASE_STATUS=PASS`

## Outcome

This documentation-only round freezes the Coffee Sensory Product Contract V0,
documents the evidence-grounded methodology and staged research roadmap, and
normalizes current repository onboarding through the validated Round 2B
foundation.

The current documents distinguish product intent from implementation status.
They define an ordinary tasting user, low-burden contextual interaction, and
five-primary/three-secondary sensory candidate output while leaving
preparation taxonomies, roast terminology, Q1–Q5, consumer ranking, embeddings,
API design, and frontend integration as explicit research questions.

No frontend, ontology, corpus, model, migration, or database output was
modified. Historical archives and Round 1–2B audit receipts remain unchanged.

## Identity

| Item              | Value                                                    |
| ----------------- | -------------------------------------------------------- |
| Source SHA        | `7243ddb9c1537e3a7096cca652c18c66d18aeb30`               |
| Work branch       | `codex/coffee-sensory-docs-product-contract-v0-20260824` |
| Final checkpoint  | `@self`                                                  |
| Root README       | `README.md`                                              |
| Product contract  | `docs/product/PRODUCT_CONTRACT_V0.md`                    |
| Methodology       | `docs/methodology/METHODOLOGY_OVERVIEW.md`               |
| Research roadmap  | `docs/research/RESEARCH_ROADMAP.md`                      |
| Checkpoint policy | `docs/engineering/GIT_CHECKPOINT_POLICY.md`              |

`@self` means the commit containing this receipt. This avoids placing a Git
commit's cryptographic hash inside its own contents. Resolve it with:

```bash
git log -1 --format=%H -- \
  docs/audits/coffee-sensory-docs-product-contract-v0-20260824/00_EXECUTIVE_RECEIPT.md
```

After remote promotion, that resolved SHA must equal the verified feature
branch and `origin/main` targets.

## Product and methodology normalization

- The Product Contract V0 freezes assistance rather than correction as the
  objective, a four-question default with one optional adaptive discriminator,
  and five primary plus three secondary candidates.
- C0 preparation and C1 roast are documented as contextual research variables,
  not prematurely canonicalized taxonomies or universal standards.
- User-facing output is described as candidates and references rather than
  true flavor probabilities, tasting accuracy, or correct answers.
- Scientific credibility is attributed to sensory research, provenance,
  rights, empirical data, explicit semantics, held-out evaluation,
  uncertainty, abstention, and reproducibility.
- Deep learning and embeddings remain optional future methods that must show
  held-out benefit over the deterministic baseline.
- The README reports 92 active canonical sensory attributes, 130 total
  ontology concepts, 2,474 corpus documents, 6,818 observations, and 1,713
  normalized industry-language expressions with their limitations.
- The current architecture now includes Round 2B corpus and retrieval layers
  while preserving the canonical/corpus/inference/evaluation boundary.

## Validation

The documentation checkpoint passed:

- `git diff --check`;
- `npm run format:check`;
- local internal Markdown link/path validation;
- terminology review of current non-historical documentation;
- `npm run check`;
- `npm run test` with 9 tests passing;
- `npm run build` with all static routes generated; and
- `npm run test:smoke` with 9 Playwright cases passing.

Node 22.21.0 emitted the repository's existing React Router engine advisory
for a required version greater than 22.22.0, but the typecheck and build
commands completed successfully. The database pipeline was not rerun locally
because this round did not modify database inputs, migrations, scripts, or
outputs; the source checkpoint's PostgreSQL 17 gate remains the applicable
validated database evidence.

## Remote CI result

Remote main and the feature branch were both verified at the documentation
checkpoint. GitHub Actions run
[`32725576893`](https://github.com/dpan538/coffee-flavor-research/actions/runs/32725576893)
then produced a split result:

- formatting, typecheck, unit tests, and production build passed;
- the PostgreSQL 17 ontology and corpus job passed two clean rebuilds;
- the Playwright smoke step failed; and
- one failed-job rerun also failed.

The initial attempt could not find the comparison overlay in all three
viewports. The rerun passed seven of nine cases but reproduced the existing
viewport-sensitive comparison flow: the desktop comparison overlay intercepted
the Lemon detail link, while the mobile comparison heading did not appear.
The same nine smoke cases passed locally in this clean worktree.

No application or test file changed in the documentation round itself. Its
aggregate remote repository gate therefore remained red pending a separate,
narrowly scoped repair.

## CI repair and closure

Repair commit
[`1848b643a701a0913915405cedd897b75093305d`](https://github.com/dpan538/coffee-flavor-research/commit/1848b643a701a0913915405cedd897b75093305d)
resolved the blocker on branch
`fix/coffee-sensory-playwright-comparison-ci-20260824`.

The root cause was a real application race combined with inadequate test
synchronization. React Router's `setSearchParams` updater closes over the
current render's search parameters rather than queueing updates like React
state. Rapid compare, query, close, and view changes could therefore replace a
newer parameter with stale URL state. The repair merges every change from a
synchronously maintained latest-requested parameter snapshot.

The Playwright flow now waits for observable URL and comparison-queue
transitions without sleeps, timeout inflation, retries, skipped viewports, or
weakened assertions. A focused regression immediately changes the query after
selecting Jasmine, verifies that `compare=jasmine` survives, adds Dark
Chocolate, and verifies `compare=jasmine,dark-chocolate` before opening the
two-item comparison.

Local CI-Chromium validation passed:

- desktop comparison flow: 4 of 4 tests;
- mobile comparison flow: 4 of 4 tests;
- focused desktop repeat: 10 of 10 without retries;
- focused mobile repeat: 10 of 10 without retries; and
- complete desktop, tablet, and mobile suite: 12 of 12 tests.

GitHub Actions pull-request run
[`32728230235`](https://github.com/dpan538/coffee-flavor-research/actions/runs/32728230235)
then passed both required jobs:

- Format, typecheck, test, and build, including Playwright smoke tests; and
- PostgreSQL 17 ontology and corpus gates, including two clean rebuilds.

This green remote evidence closes the documentation-round CI blocker. The
repair changed no PostgreSQL schema, migration, corpus, ontology, product
contract, methodology, roadmap, archive, or product semantics.

## Safety

Work was performed in the isolated clean worktree at
`/private/tmp/coffee-sensory-docs-product-contract-v0-20260824`. The user's
original dirty local `main` was not checked out, reset, stashed, cleaned,
committed, merged, rebased, or written by this round.

Its pre-existing status and binary-diff fingerprints remained the safety gate:

```text
STATUS_SHA256=77b1f7111a6b4ad6bc233cf8f0d9075fad72996d36bc0506a3ad418b8b131de1
DIFF_SHA256=2c4eec84cd822846900bf6915a2b103c8cac08f04d8243ff7440cea4e21932df
```

## Receipt

```text
PHASE_STATUS=PASS

SOURCE_SHA=7243ddb9c1537e3a7096cca652c18c66d18aeb30
WORK_BRANCH=codex/coffee-sensory-docs-product-contract-v0-20260824
FINAL_LOCAL_SHA=@self
FINAL_REMOTE_SHA=@self
REMOTE_MAIN_SHA=@self
WORKTREE_CLEAN=true

README_NORMALIZED=true
PRODUCT_CONTRACT_CREATED=true
METHODOLOGY_DOC_CREATED=true
RESEARCH_ROADMAP_CREATED=true
LEGACY_DOCS_MODIFIED=false

PRODUCT_TERMINOLOGY_PASS=true
DOCUMENT_LINK_PASS=true
REPOSITORY_CHECKS_PASS=true

REMOTE_BACKUP_PASS=true
MAIN_PROMOTION_PASS=true
FORCE_PUSH_USED=false
ORIGINAL_DIRTY_MAIN_TOUCHED=false

AUDIT_RECEIPT=docs/audits/coffee-sensory-docs-product-contract-v0-20260824/00_EXECUTIVE_RECEIPT.md
CI_REPAIR_BRANCH=fix/coffee-sensory-playwright-comparison-ci-20260824
CI_REPAIR_SHA=1848b643a701a0913915405cedd897b75093305d
CI_REPAIR_ACTIONS_RUN=32728230235
REMOTE_FRONTEND_CI_PASS=true
REMOTE_POSTGRES_CI_PASS=true
KNOWN_BLOCKERS=none
ROUND3A_READY=true
```

The documentation contract is committed and remotely backed up, and its
mandatory repository gate is green. Round 3A readiness does not mean the C0/C1
taxonomies, sensory questions, consumer ranking model, or final interaction
have already been validated.
