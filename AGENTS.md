# AGENTS.md

## Product

Coffee Flavor Atlas / 咖啡风味图谱 is a research-grounded sensory reference
system for ordinary coffee tasting. The intended product uses low-burden
context and perception questions to return sensory candidates that help users
name, refine, compare, and remember their own impressions. Treat candidates as
references, not correct answers, true flavor probabilities, or a sensory exam.

The current product semantics are governed by
`docs/product/PRODUCT_CONTRACT_V0.md`. Preparation and roast taxonomies,
Q1–Q5, consumer ranking, the API, and the final frontend remain research work.

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

UI redesign, knowledge/research work, and repository metadata work should stay
separate unless a task explicitly asks to combine them.

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

## Done Standard

- `npm run format:check`, `npm run check`, `npm run test`,
  `npm run test:smoke`, and `npm run build` pass for functional changes.
- Database changes remain forward-only and pass the applicable PostgreSQL
  validation and reproducibility gates.
- Home, Atlas, descriptor detail, and methodology routes remain statically
  buildable.
- Atlas search, aliases, category filters, FIELD/INDEX/MAP, detail navigation,
  and comparison remain available.
- 390px, 768px, and 1440px smoke paths avoid horizontal overflow and console
  errors.
- Documentation is updated when architecture, data, motion, licensing, or asset
  policy changes.
- Significant rounds include an executive receipt and follow
  `docs/engineering/GIT_CHECKPOINT_POLICY.md`.
