# Contributing

Thank you for treating Coffee Flavor Atlas as a research prototype rather than
a finished sensory authority.

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

## Issues

Use issues for focused bug reports, documentation gaps, data questions, and
license review notes. Please include the affected route, descriptor slug, or
file path where possible.

## Descriptor Changes

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

## Pull Requests

- Keep pull requests small and reviewable.
- Use Conventional Commits where practical, such as `fix:`, `docs:`,
  `feat:`, or `test:`.
- Ensure checks pass before requesting review.
- Add tests when changing data validation, search, map, comparison, routing, or
  accessibility behavior.
