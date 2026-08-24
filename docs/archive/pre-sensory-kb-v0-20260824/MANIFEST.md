# Archive Manifest: Pre-Sensory-KB V0

- Archive key: `pre-sensory-kb-v0-20260824`
- Archive event: 2026-08-24
- Source revision: `1755915d3918013c8bd7c5f744e5ce8a0e972167`
- Work branch: `codex/coffee-sensory-kb-v0-round1-20260824`

The five archived artifacts below all belong to the 2026-06-22 public baseline.
They were moved rather than copied, and Git reports each as a rename. The
current engineering contract is maintained under
[`docs/research/coffee-sensory-kb-v0/`](../../research/coffee-sensory-kb-v0/).

## Archived artifacts

| original_path               | archive_path                                                                             | artifact_type                 | approximate_date_if_known | reason_archived                                                                                                                                                      | superseded_by                                                                           | notes                                                                                                                                 |
| --------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------- | ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                 | `docs/archive/pre-sensory-kb-v0-20260824/product/README-public-baseline-20260622.md`     | Product/public baseline       | 2026-06-22                | Describes the static Coffee Flavor Atlas and its 24-descriptor draft dataset as the project center; it predates the PostgreSQL KB contract.                          | `README.md`; `docs/research/coffee-sensory-kb-v0/`                                      | Git history preserved by rename. No application-runtime dependency; a current replacement README was created at the original path.    |
| `docs/ARCHITECTURE.md`      | `docs/archive/pre-sensory-kb-v0-20260824/architecture/FRONTEND-ARCHITECTURE-20260622.md` | Frontend architecture         | 2026-06-22                | Defines only the static React Router frontend and a speculative future API boundary, not the current knowledge architecture.                                         | `docs/ARCHITECTURE.md`; `docs/research/coffee-sensory-kb-v0/01_V0_ARCHITECTURE.md`      | Git history preserved by rename. No application-runtime dependency; a current architecture document was created at the original path. |
| `docs/FRONTEND-REDESIGN.md` | `docs/archive/pre-sensory-kb-v0-20260824/design/FRONTEND-REDESIGN.md`                    | UI/design direction           | 2026-06-22                | Records an exploratory frontend redesign, while this round explicitly excludes frontend redesign work.                                                               | `docs/research/coffee-sensory-kb-v0/00_RESEARCH_SOURCE.md`                              | Git history preserved by rename. Pure documentation; no runtime reference or replacement at the old path.                             |
| `docs/DATA-METHODOLOGY.md`  | `docs/archive/pre-sensory-kb-v0-20260824/research/DATA-METHODOLOGY.md`                   | Prototype data methodology    | 2026-06-22                | Couples descriptors to project-curated 0–5 association profiles; the current contract instead separates concept identity from sample- or study-specific measurement. | `docs/research/coffee-sensory-kb-v0/01_V0_ARCHITECTURE.md`; `02_DATABASE_INVARIANTS.md` | Git history preserved by rename. Pure documentation; no runtime reference or replacement at the old path.                             |
| `docs/DECISIONS.md`         | `docs/archive/pre-sensory-kb-v0-20260824/decisions/DECISIONS.md`                         | Product/frontend decision log | 2026-06-22                | Bundles decisions from the public frontend baseline and is no longer the governing decision record for KB V0.                                                        | `docs/research/coffee-sensory-kb-v0/03_ENGINEERING_DECISIONS.md`                        | Git history preserved by rename. Pure documentation; no runtime reference or replacement at the old path.                             |

## LEGACY_BUT_RUNTIME_REFERENCED

These five modules are part of the legacy public-baseline data model but remain
live dependencies of the static application. They are not archived artifacts,
are not duplicated in the archive, and must remain in place until a separately
designed frontend integration replaces their runtime role.

| path                                      | current purpose                                                                              | why retained                                                     | current treatment                                                                                      |
| ----------------------------------------- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `packages/flavor-data/src/descriptors.ts` | Supplies 24 pilot descriptors and project-curated draft association ranges.                  | Imported by the public baseline through the flavor-data package. | Leave in place; do not treat its records as PostgreSQL KB canonical knowledge.                         |
| `packages/flavor-data/src/schema.ts`      | Validates the frontend descriptor, category, source, and association-range shapes with Zod.  | Required by runtime data parsing and tests.                      | Leave in place as a compatibility schema; it is not the KB relational schema.                          |
| `packages/flavor-data/src/categories.ts`  | Supplies the frontend's exclusive visual/category registry.                                  | Required by current Atlas filtering and presentation.            | Leave in place; do not promote this exclusive categorization into a universal ontology family.         |
| `packages/flavor-data/src/sources.ts`     | Supplies the public baseline's small source registry and reuse notes.                        | Required by the methodology UI and descriptor validation.        | Leave in place; future canonical provenance belongs in the PostgreSQL `evidence` domain.               |
| `packages/flavor-data/src/comparison.ts`  | Supplies search normalization, display metadata, and comparison utilities for the static UI. | Required by Atlas search and comparison behavior.                | Leave in place as frontend utility code; its dimensions and scoring are not canonical sensory weights. |

## Counts

```text
LEGACY_ARTIFACTS_DISCOVERED=10
LEGACY_ARTIFACTS_ARCHIVED=5
LEGACY_RUNTIME_REFERENCED=5
```

No other current source code, reusable infrastructure, licensing records,
assets, tests, or the external research report were included in the archive.
