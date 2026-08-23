# Architecture

## Current Stack

Coffee Flavor Atlas now uses React Router Framework Mode, Vite, React, TypeScript strict mode, Anime.js, Zod, Vitest, and Playwright.

Configuration:

- `ssr: false` in `react-router.config.ts`.
- Static prerender paths include `/`, `/atlas`, `/methodology`, and all `/flavor/:slug` pages.
- `npm run build` outputs the deployable static client to `build/client`.
- `npm run preview` serves `build/client` through Vite preview.

Astro was removed after React parity, tests, smoke, and build passed.

## Data Boundary

The UI layer imports data only from `packages/flavor-data/src/index.ts`. This package contains descriptor data, categories, sources, Zod schemas, validation, search helpers, map point calculation, sorting, and comparison logic.

React routes must not create a second descriptor dataset.

## Route Model

- `/`: editorial descriptor field and publication-style scroll scenes.
- `/atlas`: FIELD, INDEX, MAP, search, filters, URL query state, and comparison overlay.
- `/flavor/:slug`: statically prerendered descriptor specimen pages.
- `/methodology`: appendix-style method index, source matrix, evidence legend, and asset spike.

Vite preview has a small clean URL middleware for local static preview so `/atlas`, `/methodology`, and `/flavor/:slug` resolve to their prerendered directory HTML instead of the SPA fallback.

## Motion Boundary

Motion lives under `app/motion/`:

- `animeScope.ts`: scoped Anime.js lifecycle.
- `cursorEffects.ts`: fine-pointer cursor mode and requestAnimationFrame follower.
- `scrollObservers.ts`: route-scoped scroll progress observer.
- `textEffects.ts`: limited split-text reveal.
- `routeTransitions.ts`: simple route crossfade layer.
- `reducedMotion.ts`: shared reduced-motion hook.
- `presets.ts`: reusable representational motion families.

The debug panel appears only in development and reports active Anime scopes, scroll observers, reduced motion, pointer capability, and cursor mode.

## Future API Extension

Elysia is intentionally not installed in this phase. If a backend becomes necessary, add it as a separate app:

```text
apps/
  api/
    src/
      index.ts
packages/
  flavor-data/
```

The API should consume `packages/flavor-data` rather than duplicating descriptor data. Keep the frontend statically deployable unless a documented product requirement needs runtime data.
