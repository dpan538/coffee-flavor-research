# Decision Log

## 2026-06-22

### Use npm

The repository had no package manager lockfile, so the project uses npm and will keep `package-lock.json` after installation.

### Build a plain Astro app instead of scaffolding an oversized starter

The repository was empty, so the project was initialized manually with Astro, React integration, Zod, Motion for React, Vitest, and Playwright. This keeps the MVP small and avoids unrelated starter code.

### Keep all prototype scores as project-curated drafts

All 24 descriptors use `evidenceStatus: "project_curated_draft"`. Reference frameworks and open data are listed in the source registry for transparency, but no score is presented as coming from WCR, SCA, UC Davis, or any formal sensory study.

### Put Bellflower in the unresolved category

The pilot list groups bellflower with floral terms, but the visual system and methodology need an unresolved master category. Bellflower is therefore kept visible as an unresolved floral candidate with `categoryId: "unresolved"` and `descriptorStatus: "unresolved"`.

### Avoid D3 for the sensory map

The MVP has only 24 nodes and a simple 0-5 coordinate mapping. Plain TypeScript and SVG are easier to maintain than installing a full visualization library.

### Keep comparison as an Atlas drawer

Comparison lives inside `/atlas` and stores selected slugs in the `compare` query parameter. This avoids extra routes and matches the requirement for a panel/drawer/modal-style comparison tool.

### Use original generated SVG motifs

`FlavorGlyph` creates category master shapes with parameterized density, curvature, halo, and motion. The system does not copy external graphics or proprietary flavor-wheel layouts.

### Use system Chrome for local Playwright smoke tests

The first Playwright run reached the dev server but the bundled Chromium binary was not installed. Because this machine has Google Chrome, `playwright.config.ts` uses the Chrome channel for smoke tests instead of requiring a large browser download during this implementation pass.

### Migrate the UI from Astro to React Router Framework Mode

The visual direction changed from a quiet research MVP to an experimental digital publication with richer client-side interaction. The UI layer was rewritten with React Router Framework Mode, Vite, React, and Anime.js while preserving the descriptor data, Zod schema, source registry, validation, search, map, sorting, and comparison logic in `packages/flavor-data`.

### Keep npm and the existing lockfile

The repository already had `package-lock.json`, so the migration stayed on npm instead of switching to Bun. This avoids package-manager churn during a large architecture change.

### Use React Router 8 despite the local Node patch warning

The current stable React Router packages resolve to `8.0.1`, which warns that Node `>=22.22.0` is preferred. The local runtime is `22.21.0`; typegen, tests, smoke, and build still pass, so the warning is documented instead of downgrading.

### Move reusable data to `packages/flavor-data`

The migration is a UI rewrite, not a data rewrite. `packages/flavor-data` is now the single import surface for descriptors, categories, sources, schema validation, search, map, sorting, and comparison utilities.

### Replace the glyph-first image system with a six-asset spike

The old `FlavorGlyph` abstraction was removed as the primary descriptor image language. Six Game-icons.net CC BY 3.0 SVG candidates were added for jasmine, lemon, red berries, dark chocolate, cinnamon, and cheese. The spike is documented in `docs/ASSET-LICENSES.md` and is not treated as a final 24-word visual set.

### Use local Vite preview clean URL middleware

Vite preview serves `/atlas/` correctly but can fall back to `/` for extensionless clean URLs like `/atlas?view=map`. A small preview-only middleware rewrites `/atlas`, `/methodology`, and `/flavor/:slug` to their trailing-slash directory paths so local static smoke tests exercise the prerendered pages.

### Defer Atlas query state until hydration

Static prerendering cannot know browser query parameters. Atlas initially renders the prerendered default state and applies `q`, `category`, `view`, and `compare` parameters after hydration. This avoids React hydration mismatch while preserving refreshable URL state.

### Keep future Elysia work out of this phase

Elysia remains a future optional backend direction. `docs/ARCHITECTURE.md` records how an `apps/api` package could consume `packages/flavor-data` later, but no API server is installed or implemented in this migration.

### Use layered repository licensing for the public baseline

The first public GitHub push separates software licensing from project-authored research and curated descriptor content. Source code stays under MIT. Original methodology prose and curated descriptor records are documented as CC BY 4.0. Third-party assets, fonts, dependencies, source frameworks, and datasets keep their own licenses and are tracked in the asset and third-party notices.

### Use `dpan538` as the confirmed citation identity for now

GitHub CLI was not available locally, and no verified full legal author name was present in project metadata. The only confirmed local author display string is `git config user.name`, which is `dpan538`. The first public baseline therefore uses `dpan538` in `LICENSE` and `CITATION.cff` without inferring a legal name from the username or email.
