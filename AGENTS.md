# AGENTS.md

## Product

Coffee Flavor Atlas / 咖啡风味图谱 is an interactive, research-driven atlas of
coffee flavor language. Treat it as a vocabulary and interface prototype, not a
coffee standard, ecommerce site, dashboard, or sample database.

## Repository Purpose

This repository preserves the Coffee Flavor Atlas public baseline: a static
React Router + Vite application, schema-validated flavor descriptor data,
methodology documentation, tests, and layered licensing metadata.

UI redesign work and repository metadata work should stay separate unless a
task explicitly asks to combine them.

## Current Architecture

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
frameworks, CMS, databases, login, API server, or large global state libraries
without an explicit architecture task.

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

Use npm because `package-lock.json` is the active lockfile.

## Data Location

- `packages/flavor-data/src/descriptors.ts`: 24 pilot descriptors.
- `packages/flavor-data/src/categories.ts`: category registry.
- `packages/flavor-data/src/sources.ts`: source registry.
- `packages/flavor-data/src/schema.ts`: Zod schema and validation.
- `packages/flavor-data/src/comparison.ts`: comparison utilities.
- `packages/flavor-data/src/sort.ts`: search, map, and related sorting tools.

React UI must import descriptor/category/source data from `packages/flavor-data`.
Do not copy or fork descriptor data inside `app/`.

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
- Home, Atlas, descriptor detail, and methodology routes remain statically
  buildable.
- Atlas search, aliases, category filters, FIELD/INDEX/MAP, detail navigation,
  and comparison remain available.
- 390px, 768px, and 1440px smoke paths avoid horizontal overflow and console
  errors.
- Documentation is updated when architecture, data, motion, licensing, or asset
  policy changes.
