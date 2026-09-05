# AGENTS.md

## [CODEX EXECUTION SCOPE — BACKEND MODEL ONLY]

Effective 2026-09-05. This section governs active execution and supersedes older
research-front-end, novice-study, C1-unsure and no-training authorizations in
historical contracts and receipts. Preserve those receipts as historical facts.

Target users are coffee enthusiasts interested in flavor exploration. Complete
coffee beginners are outside the product scope. Do not optimize around novice
onboarding or novice completion.

Authorized work: professional sensory data engineering; semantic analysis and
governed normalization; question/option semantic models; sequential answer-effect
algorithms; candidate retrieval and flavor ranking; question-selection and
stopping models; backend information architecture and executable contracts;
training, evaluation, error analysis and reproducibility.

Forbidden work: frontend, UI/UX layouts or page structure; participant-facing
research harnesses; hidden/test/demo routes; React components, CSS, visual assets
or result-page design; PWA/service workers; new onboarding, novice studies or
presentation variants. Research-only, temporary, unlinked and feature-flagged
status do not exempt frontend work. Even successful model validation does not
authorize building a frontend or PWA; a separate explicit owner assignment is
required. One owner-authorized corrective commit may remove verified agent-added
frontend changes after an external recoverable patch is saved.

C0 is required and must be exactly one existing eight-family ID. C1 is required
and must be exactly one of `extremely_light`, `light`, `medium_light`, `medium`,
`medium_dark`, `dark`, `extremely_dark`. No unknown, unsure, null, skip, eighth
class or automatic default is allowed. Missing/invalid C1 is an input-validation
error. Source-side missing roast metadata must not be fabricated.

Backend model fitting and bounded comparative experiments are authorized.
Training-data rights, satisfied source-specific permission conditions, provenance
and split isolation remain mandatory. Split coffee/sample/lot and duplicate
source groups before estimating features, priors, co-occurrences or weights.
Questionnaire preferences are not sensory truth or training labels. Positive-only
records must not turn all unmentioned descriptors into sensory negatives.
Historical no-training receipts do not block this explicitly authorized work.

The primary task is `(C0, C1, question/option answer sets)` to candidate ranking,
next valuable question or stop, and structured `main <= 5`, `secondary <= 3`.
Lexical normalization is auxiliary. A task is complete only with executable
backend behavior and measured comparative results, not categories or fixtures.

Write only necessary execution constraints, processing provenance, experiment
configuration, training records, evaluation and error analysis. Use one current
experiment directory and the existing experiment register; no new design-document
hierarchy. Retain reloadable models in owner-controlled storage outside public
Git and CI attachments. Use the existing long-lived research branch; do not
rewrite history, merge main, or touch another dirty checkout.

Subsequent model commits must pass `db/scripts/check-backend-model-scope.py`.
No app/public/style/page/component/service-worker or frontend dependency changes
are permitted. Any required shared-module exception must list exact files, never
an entire frontend package. There are currently no shared frontend exceptions.

## Product

Current project purpose is `PERSONAL_NONCOMMERCIAL_COFFEE_RESEARCH`;
monetization, commercial training and commercial deployment are not required.
Resume discussion of the research does not authorize portfolio or PWA work.
Admit source material for `NONCOMMERCIAL_RESEARCH_USE` under its actual applicable
license and satisfied conditions; commercial use, raw-data release and weight
release are separate decisions. Standard licenses need not explicitly name ML.
Do not grant permission to unknown, unlicensed, training-prohibited or approval-
required sources. Keep original machine-license fields and author notices;
enforce their shared permitted noncommercial scope without rewriting either.

Keep data roles explicit: `CORE_PROFESSIONAL`, `AUX_COFFEE_WEAK_LABEL`,
`AUX_SEMANTIC`, `AUX_CONTEXT`, `AUX_USER_RESEARCH`. Auxiliary data must not enter
the core evaluation or acquire a higher evidence grade by association. Compound
source categories remain compound. Other-food semantics do not become coffee
observations. Source-native roast terms do not automatically establish calibrated
seven-level C1 mappings. Freeze the core split/configuration before at most two
additional balanced/auxiliary comparisons; use DEV decisions and the unchanged
locked TEST scope, never TEST-driven iteration. Cache sources and models in
persistent owner-controlled storage. Do not create additional design/license
report hierarchies or broaden source discovery beyond eight targeted routes and
90 minutes for the current experiment.

Coffee Flavor Atlas / 咖啡风味图谱 is a research-grounded sensory reference
system for ordinary coffee tasting. The intended product uses low-burden
context and perception questions to return sensory candidates that help users
name, refine, compare, and remember their own impressions. Treat candidates as
references, not correct answers, true flavor probabilities, or a sensory exam.

Historical semantics and evidence lineage are recorded in
`docs/product/PRODUCT_CONTRACT_V0.md`. Active execution follows the backend-only
scope above and the current experiment's machine-readable backend contract.

## Repository Purpose

This repository preserves two deliberately separate layers:

- the validated PostgreSQL sensory knowledge base, canonical ontology,
  rights-reviewed pilot corpus, deterministic retrieval baseline, evidence,
  and audit receipts through Round 2B; and
- a static React Router + Vite public-baseline interface with
  schema-validated project-curated pilot descriptors.

PostgreSQL is the canonical architecture for future knowledge, corpus, NLP/ML,
and evaluation work. The static TypeScript data remains a compatibility
dependency of the existing interface and is not canonical KB knowledge.

The public-baseline interface is preserved as a historical compatibility layer;
its existence does not authorize frontend modifications in a model task.

## Current Architecture

Knowledge and research substrate:

- PostgreSQL 17+ with `pg_trgm` and no required `pgvector` dependency.
- Six schemas: `ref`, `kb`, `evidence`, `corpus`, `ml`, and `audit`.
- Forward-only migrations under `db/`; migrations `000` through `007` are the
  immutable Round 1 baseline, and `008` through `011` are the immutable Round
  2A baseline.
- Source-controlled ontology and corpus inputs, SQL validation, negative and
  semantic tests, query-plan review, and reproducibility scripts.
- Canonical knowledge, corpus observations, model inference, and evaluation
  results remain separate.

Static application compatibility layer:

- React Router Framework Mode with `ssr: false`.
- Vite for build and preview.
- React for UI.
- Anime.js for scoped animation.
- TypeScript strict mode.
- Zod for data validation.
- Vitest for data and utility tests.
- Playwright for smoke tests.
- Native CSS custom properties in `app/styles/global.css`.

Astro has been removed. Do not reintroduce Astro, Next.js, Tailwind, Framer
Motion, GSAP, Lenis, Three.js, WebGL, Canvas as primary rendering, UI component
frameworks, CMS, a second database architecture, login, API server, or large
global state libraries without an explicit architecture task. Do not connect
the static frontend to PostgreSQL without a dedicated API/data-integration
contract.

## Common Commands

```bash
npm ci
npm run dev
npm run build
npm run preview
npm run check
npm run test
npm run test:smoke
npm run format:check
```

Database commands require a disposable PostgreSQL 17+ environment and the
destructive-operation safeguards documented in `db/README.md`:

```bash
npm run db:migrate
npm run test:db
npm run test:db:repro
```

Use npm because `package-lock.json` is the active lockfile.

## Data Location

- `db/`: canonical PostgreSQL migrations, source-controlled inputs, scripts,
  and executable database tests.
- `docs/audits/`: frozen implementation and validation receipts.
- `docs/methodology/METHODOLOGY_OVERVIEW.md`: current scientific architecture.
- `docs/research/RESEARCH_ROADMAP.md`: ordered research program.
- `packages/flavor-data/src/descriptors.ts`: 24 pilot descriptors.
- `packages/flavor-data/src/categories.ts`: category registry.
- `packages/flavor-data/src/sources.ts`: source registry.
- `packages/flavor-data/src/schema.ts`: Zod schema and validation.
- `packages/flavor-data/src/comparison.ts`: comparison utilities.
- `packages/flavor-data/src/sort.ts`: search, map, and related sorting tools.

React UI must import descriptor/category/source data from `packages/flavor-data`.
Do not copy or fork descriptor data inside `app/`, and do not promote the
static pilot descriptor scores into PostgreSQL as canonical knowledge.

## Schema Rules

- All descriptor data must pass Zod validation.
- `id` and `slug` must be unique.
- `categoryId` must point to an existing category.
- Every `sourceIds` entry must point to an existing source.
- English and Simplified Chinese labels must not be empty.
- Every sensory range must stay within 0 to 5.
- Every range must satisfy `min <= typical <= max`.
- Boundary, compound, unresolved, broad, culturally sensitive, or
  translation-sensitive terms need `editorialNote`.

## Research Disclaimer

The current sensory association profiles are project-curated drafts. They are
not chemical measurements, official cupping scores, WCR values, SCA values,
expert panel findings, or fixed scores for any coffee.

Do not modify descriptor scores unless the task explicitly asks for data work
and the change includes provenance. Do not describe draft profiles as scientific
facts.

## License Layers

- Root `LICENSE`: MIT for source code, schemas, utilities, tests,
  configuration, build scripts, and software components.
- `LICENSES/CC-BY-4.0.txt`: CC BY 4.0 for project-authored research prose and
  curated descriptor content.
- `docs/LICENSE-SCOPE.md`: authoritative scope explanation.
- `THIRD_PARTY_NOTICES.md` and `docs/ASSET-LICENSES.md`: third-party materials,
  attributions, and unconfirmed assets.

TypeScript files that contain both wrapper code and descriptor content have
split treatment: wrapper code is MIT; original curated content is CC BY 4.0;
third-party-derived material remains under its source terms.

## External Asset Requirements

Do not add fonts, icons, SVGs, datasets, images, DOCX/PDF content, or visual
references unless their source, author/project, URL, license, attribution
requirement, and modification status are documented.

Do not use Google Images, Pinterest, Dribbble, Behance, unclear SVG Repo
entries, or "free download" assets with unverified licenses.

## Prohibited Research Claims

- Do not copy the SCA Coffee Taster's Flavor Wheel design, colors, layout, full
  vocabulary, definitions, or proprietary forms.
- Do not republish WCR, SCA, Cup of Excellence, or commercial source materials
  as this project's dataset.
- Do not claim public web access equals reuse permission.
- Do not invent papers, studies, sample counts, institutions, DOI values, ORCID
  IDs, author names, licenses, or attributions.

## Done Standard for Current Backend Model Work

- Run corresponding backend unit/data tests after local changes, then current
  backend validation after reproducibility. Do not repeatedly run all historical
  corpus generators for pure model changes.
- Database changes remain forward-only and pass the applicable PostgreSQL
  validation and reproducibility gates.
- Report B0/B1/B2/M1 results on the same locked scope and input budget, with
  coffee/sample-level paired uncertainty, coverage, errors and question deltas.
- Real independent evaluations and record-recovery proxy results remain distinct.
  No agent opinion, generated rule target or questionnaire preference is sensory
  ground truth. No fabricated human review decisions.
- Rights, leakage or evaluation contamination block the affected result. Remote
  infrastructure failures remain explicitly unpassed but need not block isolated
  locally verified research. Never claim an unobserved CI outcome.
- Follow the incremental commit and dirty-worktree protections in
  `docs/engineering/GIT_CHECKPOINT_POLICY.md`; the experiment run receipt replaces
  a new audit/design-document hierarchy for this model round.
