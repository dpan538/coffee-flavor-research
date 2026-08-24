# Contributing

Thank you for treating Coffee Flavor Atlas as a research-grounded sensory
reference system under development rather than a finished sensory authority.

Before proposing product or research changes, read the
[Product Contract V0](docs/product/PRODUCT_CONTRACT_V0.md),
[Methodology Overview](docs/methodology/METHODOLOGY_OVERVIEW.md), and
[Research Roadmap](docs/research/RESEARCH_ROADMAP.md). They distinguish current
product semantics from open research questions.

## Local Setup

```bash
npm ci
npm run dev
```

Before opening a pull request, run:

```bash
npm run format:check
npm run check
npm run test
npm run build
```

Run `npm run test:smoke` when changing routes, interaction, layout, or
accessibility-sensitive UI.

Database changes require a disposable PostgreSQL 17+ environment and the
applicable commands documented in [`db/README.md`](db/README.md). Never point
the migration or reproducibility scripts at a production database or a
database containing user data.

## Issues

Use issues for focused bug reports, documentation gaps, data questions, and
license review notes. Please include the affected route, descriptor slug, or
file path where possible.

## Static pilot descriptor changes

Descriptor edits live in `packages/flavor-data/src/descriptors.ts`.

Every substantive descriptor change must explain its source or provenance. This
includes translation changes, aliases, category changes, editorial notes,
confidence, evidence status, and sensory association ranges.

Do not submit:

- scraped commercial coffee data;
- images, SVGs, or datasets with unclear licensing;
- protected flavor wheel graphics or copied definitions;
- sensory score changes without evidence;
- wording that presents project-curated draft profiles as scientific facts.

Translation changes should explain the intended sensory nuance and any regional
or cultural assumptions.

The TypeScript pilot descriptors support the existing static interface. They
are not canonical knowledge and must not be copied into PostgreSQL or presented
as validated sensory measurements.

## Knowledge base, corpus, and model changes

- Keep historical migrations immutable and make database changes through
  forward migrations.
- Preserve the separation between canonical knowledge, evidence, corpus
  observations, model inference, and evaluation results.
- Include source/version provenance and rights decisions for sensory, lexical,
  corpus, or translation claims.
- Do not auto-promote corpus terms or model candidates into the canonical
  ontology.
- Preserve explicit uncertainty and `UNRESOLVED` behavior.
- Add or update the applicable validation and audit receipt.

## Pull Requests

- Keep pull requests small and reviewable.
- Use Conventional Commits where practical, such as `fix:`, `docs:`,
  `feat:`, or `test:`.
- Follow the
  [Git checkpoint and remote backup policy](docs/engineering/GIT_CHECKPOINT_POLICY.md).
- Ensure checks pass before requesting review.
- Add tests when changing data validation, search, map, comparison, routing, or
  accessibility behavior.
