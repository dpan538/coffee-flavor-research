# Repository Architecture

## Canonical knowledge boundary

The current research architecture is the PostgreSQL 17+ Coffee Sensory
Knowledge Base V0. It is implemented as an isolated migration and test
substrate under `db/`; the frontend does not connect to it in Round 1.

The database uses six logical schemas:

- `ref`: controlled semantics;
- `kb`: language-neutral canonical knowledge and lexicalization;
- `evidence`: sources, rights, datasets, support, measurements, projections,
  and reference calibration;
- `corpus`: captured documents, raw observations, and co-occurrence measures;
- `ml`: versioned models, runs, mapping candidates, and candidate signals; and
- `audit`: independent reviews, lifecycle history, and explicit promotion.

The governing specification is
[`docs/research/coffee-sensory-kb-v0/`](./research/coffee-sensory-kb-v0/).
Executable pass/fail evidence belongs in
[`docs/audits/coffee-sensory-kb-v0-round1/`](./audits/coffee-sensory-kb-v0-round1/).

## PostgreSQL boundary

`db/000_extensions.sql` through `db/007_validation_queries.sql` form the
dependency-ordered baseline. PostgreSQL is the system of record and `pg_trgm`
is required. `pgvector`, embeddings, an application API, and frontend data
integration are deliberately outside V0.

Canonical concepts never store display labels, permanent descriptor intensity,
universal similarity, or projection coordinates. Source-specific structures,
empirical measurements, raw observations, model output, and promotion decisions
remain in separate normalized relations.

## Static application compatibility boundary

The public baseline remains a static React Router Framework Mode application:

- React Router with `ssr: false` and prerendered `/`, `/atlas`,
  `/methodology`, and `/flavor/:slug` routes;
- Vite, React, TypeScript strict mode, Anime.js, Zod, Vitest, and Playwright;
- deployable output in `build/client`; and
- no runtime database connection or API server.

The UI imports its current data only from `packages/flavor-data/src/index.ts`.
That package's 24 descriptors, exclusive presentation categories, draft 0–5
association ranges, comparison distance, and map coordinates are
`LEGACY_BUT_RUNTIME_REFERENCED`. They remain to keep the public baseline
buildable, but they are not canonical KB entities or measurements and must not
be copied into PostgreSQL.

Future frontend integration requires its own architecture round and a
rights-filtered export or API contract. It must not silently replace the static
dataset or make PostgreSQL a hidden build dependency.

## Current routes and motion

- `/`: editorial descriptor field and publication-style scroll scenes.
- `/atlas`: field, index, map, search, filters, URL state, and comparison.
- `/flavor/:slug`: statically prerendered descriptor specimen pages.
- `/methodology`: public-baseline methodology and provenance display.

Motion remains scoped to `app/motion/`, supports reduced motion, and does not
affect the database substrate. UI redesign is out of scope for KB V0.

## Rights boundary

Software, project-authored research/content, and third-party material retain
their documented license layers. Database rights decisions are represented in
machine-readable source-version policy, and production-facing corpus views may
expose raw text only when `production_export_allowed` is affirmatively true.
The active repository policies remain in `docs/LICENSE-SCOPE.md`,
`docs/ASSET-LICENSES.md`, and `THIRD_PARTY_NOTICES.md`.

## Historical architecture

The pre-KB product, frontend architecture, data methodology, redesign, and
decision log are frozen under
[`docs/archive/pre-sensory-kb-v0-20260824/`](./archive/pre-sensory-kb-v0-20260824/).
