# 01 — Discovery and Archive Receipt

- Receipt date: 2026-08-24
- Scope: read-only discovery and archival classification only
- Archive: [`docs/archive/pre-sensory-kb-v0-20260824/`](../../archive/pre-sensory-kb-v0-20260824/)

## Repository facts recorded before KB implementation

```text
SOURCE_REPOSITORY_ROOT=/Users/jarlgiovanni/Desktop/Coffee_Flavor_Research
SOURCE_BRANCH=main
SOURCE_SHA=1755915d3918013c8bd7c5f744e5ce8a0e972167
SOURCE_REMOTE_FETCH=git@github.com:dpan538/coffee-flavor-research.git
SOURCE_REMOTE_PUSH=git@github.com:dpan538/coffee-flavor-research.git
SOURCE_REMOTE_DIVERGENCE=0_ahead_0_behind
SOURCE_WORKTREE_DIRTY=true

ISOLATED_WORKTREE_ROOT=/private/tmp/coffee-sensory-kb-v0-round1-20260824
WORK_BRANCH=codex/coffee-sensory-kb-v0-round1-20260824
WORKTREE_START_SHA=1755915d3918013c8bd7c5f744e5ce8a0e972167
```

The original `main` worktree was dirty and was not modified by this round. Its
observed modified paths were:

```text
AGENTS.md
README.md
app/root.tsx
app/routes/atlas.tsx
app/routes/home.tsx
app/routes/methodology.tsx
app/styles/global.css
docs/ARCHITECTURE.md
docs/FRONTEND-REDESIGN.md
tests/e2e/smoke.spec.ts
```

The dedicated worktree and branch started from the same local/remote commit.
At the archive receipt checkpoint, Git reported all five document operations as
renames (`R`), preserving rename traceability without changing the original
dirty worktree.

## Discovery boundaries

The search was limited to this repository. At the source revision, discovery
found no tracked PostgreSQL migrations, SQL schema, SQLite database, prior
database prototype, ontology database dump, or project-specific generated or
experimental data directory. Existing application code, tests, assets,
licensing metadata, and reusable package plumbing were reviewed but excluded
from legacy counts unless listed below.

In particular, `packages/flavor-data/src/index.ts` and `sort.ts`, the React
application, tests, licensed assets, `docs/ASSET-LICENSES.md`,
`docs/LICENSE-SCOPE.md`, and `docs/RELEASE-CHECKLIST.md` remain current
infrastructure or governance records. They are not archived merely because they
belong to the public baseline.

## Full discovery inventory

| path                                      | artifact_type                     | purpose                                                                                             | current_status                                            | legacy_or_current               | reason                                                                                               | recommended_archive_destination                                                          |
| ----------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `README.md`                               | Product/public baseline document  | Described the static Coffee Flavor Atlas, its research caveats, features, and repository operation. | Moved; replacement current README created.                | Legacy archived                 | Product center predates the canonical PostgreSQL KB research contract.                               | `docs/archive/pre-sensory-kb-v0-20260824/product/README-public-baseline-20260622.md`     |
| `docs/ARCHITECTURE.md`                    | Frontend architecture document    | Defined React Router/Vite static routes, motion boundaries, and the package data boundary.          | Moved; replacement current architecture document created. | Legacy archived                 | It is a frontend-only architecture and cannot govern the new knowledge substrate.                    | `docs/archive/pre-sensory-kb-v0-20260824/architecture/FRONTEND-ARCHITECTURE-20260622.md` |
| `docs/FRONTEND-REDESIGN.md`               | UI/design document                | Recorded exploratory visual, interaction, and motion direction.                                     | Moved.                                                    | Legacy archived                 | UI redesign is explicitly out of scope for KB V0 and does not define sensory knowledge.              | `docs/archive/pre-sensory-kb-v0-20260824/design/FRONTEND-REDESIGN.md`                    |
| `docs/DATA-METHODOLOGY.md`                | Prototype research methodology    | Documented the 24-descriptor frontend schema and six project-curated 0–5 ranges.                    | Moved.                                                    | Legacy archived                 | Its descriptor-attached draft profile is superseded by the concept/measurement separation.           | `docs/archive/pre-sensory-kb-v0-20260824/research/DATA-METHODOLOGY.md`                   |
| `docs/DECISIONS.md`                       | Product/frontend decision log     | Recorded package, frontend, data-prototype, asset, and release decisions.                           | Moved.                                                    | Legacy archived                 | It is historical context, not the current KB engineering decision record.                            | `docs/archive/pre-sensory-kb-v0-20260824/decisions/DECISIONS.md`                         |
| `packages/flavor-data/src/descriptors.ts` | Runtime descriptor data           | Supplies 24 bilingual pilot descriptors and draft association profiles.                             | Left in place and still imported.                         | `LEGACY_BUT_RUNTIME_REFERENCED` | Moving it would break the static public baseline; its records are not canonical KB assertions.       | Leave in place until an explicit frontend data-integration phase.                        |
| `packages/flavor-data/src/schema.ts`      | Runtime validation schema         | Validates descriptor, category, source, and range structures.                                       | Left in place and still imported.                         | `LEGACY_BUT_RUNTIME_REFERENCED` | Runtime and tests depend on it; it is distinct from the relational KB schema.                        | Leave in place until an explicit frontend data-integration phase.                        |
| `packages/flavor-data/src/categories.ts`  | Runtime visual/category registry  | Supports Atlas category filtering and presentation.                                                 | Left in place and still imported.                         | `LEGACY_BUT_RUNTIME_REFERENCED` | The app depends on it, while its exclusive categories must not become a universal ontology family.   | Leave in place until an explicit frontend data-integration phase.                        |
| `packages/flavor-data/src/sources.ts`     | Runtime source registry           | Supplies the public methodology UI and validates descriptor source IDs.                             | Left in place and still imported.                         | `LEGACY_BUT_RUNTIME_REFERENCED` | Runtime depends on it; canonical source/version/rights metadata belongs in PostgreSQL.               | Leave in place until an explicit frontend data-integration phase.                        |
| `packages/flavor-data/src/comparison.ts`  | Runtime search/comparison utility | Supplies normalized search, labels, range comparison, and display helpers.                          | Left in place and still imported.                         | `LEGACY_BUT_RUNTIME_REFERENCED` | Atlas behavior depends on it; the draft dimensions must not be treated as universal sensory weights. | Leave in place until an explicit frontend data-integration phase.                        |

## Archive movement receipt

All five archived documents have an approximate/recorded baseline date of
2026-06-22.

| legacy design artifact     | old location                | new archive location                                                                     | git history preserved?     | runtime dependency?                                                                   | archive reason                                                                             |
| -------------------------- | --------------------------- | ---------------------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Public product baseline    | `README.md`                 | `docs/archive/pre-sensory-kb-v0-20260824/product/README-public-baseline-20260622.md`     | Yes; Git reports a rename. | No application-runtime dependency; replacement current README created.                | Preserve the superseded static-product framing.                                            |
| Frontend architecture      | `docs/ARCHITECTURE.md`      | `docs/archive/pre-sensory-kb-v0-20260824/architecture/FRONTEND-ARCHITECTURE-20260622.md` | Yes; Git reports a rename. | No application-runtime dependency; replacement current architecture document created. | Preserve the superseded frontend-only architecture.                                        |
| Frontend redesign          | `docs/FRONTEND-REDESIGN.md` | `docs/archive/pre-sensory-kb-v0-20260824/design/FRONTEND-REDESIGN.md`                    | Yes; Git reports a rename. | None; pure documentation.                                                             | This round is not a frontend redesign round.                                               |
| Prototype data methodology | `docs/DATA-METHODOLOGY.md`  | `docs/archive/pre-sensory-kb-v0-20260824/research/DATA-METHODOLOGY.md`                   | Yes; Git reports a rename. | None; pure documentation.                                                             | Superseded by research-backed separation of identity, evidence, and empirical measurement. |
| Product/frontend decisions | `docs/DECISIONS.md`         | `docs/archive/pre-sensory-kb-v0-20260824/decisions/DECISIONS.md`                         | Yes; Git reports a rename. | None; pure documentation.                                                             | Preserve historical decisions without letting them govern KB V0.                           |

## Archive accounting

```text
LEGACY_ARTIFACTS_DISCOVERED=10
LEGACY_ARTIFACTS_ARCHIVED=5
LEGACY_RUNTIME_REFERENCED=5
ARCHIVE_COMPLETE=true
```

`ARCHIVE_COMPLETE=true` means every legacy artifact found within the agreed
scope is either safely archived with a manifest entry or explicitly classified
in the five-item runtime-referenced set. It does not mean the runtime modules
have been migrated, the PostgreSQL database has been validated, or later audit
receipts have passed.
