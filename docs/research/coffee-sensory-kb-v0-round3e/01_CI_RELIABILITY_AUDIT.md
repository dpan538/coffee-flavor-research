# CI reliability audit

Audit date: 2026-08-25. Evidence came from actual GitHub Actions job metadata
and failed logs, plus commit contents—not commit titles or screenshots.

## Current truth

`CURRENT_MAIN_CI_STATUS=GREEN`

Run [32807372976](https://github.com/dpan538/coffee-flavor-research/actions/runs/32807372976)
tested exact main SHA `52c29e53a8f3d3ab60b72f2a6e5f60419b6173e5`.
Both `Format, typecheck, test, and build` and
`PostgreSQL 17 ontology and corpus gates` succeeded. Therefore
`ACTIVE_MAIN_CI_FAILURE=false`.

## Historical intermediate failures

| Run         | Commit     | Exact failed step(s)                                  | Root cause and later disposition                                                                      |
| ----------- | ---------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 32803214645 | `57f4eee…` | `Check formatting`                                    | formatting drift in newly added adaptive-architecture/methodology documents; later formatted          |
| 32804187304 | `f27c17f…` | `Check formatting`                                    | formatting drift in protocol/question research documents; later formatted                             |
| 32805467260 | `0ba15df…` | `Check formatting`                                    | generated/calibration dictionary formatting drift; later repaired by formatting commits               |
| 32806374327 | `0b0e035…` | `Check formatting`; `Run two clean database rebuilds` | same dictionary drift plus Round 3C negative-test setup ordering; database helper fixed in `f6f1b60…` |
| 32806658880 | `f6f1b60…` | `Check formatting`                                    | database repair passed; dictionary formatting still failed                                            |
| 32806742340 | `d3b7561…` | `Check formatting`                                    | dictionary formatting still failed; later closed by `f077b84…` / `183ae279…`                          |

`HISTORICAL_FAILURE_COUNT_REVIEWED=6`

`HISTORICAL_FAILURE_ROOT_CAUSES=2`

There was no typecheck, unit-test, build, Playwright, race, timeout, missing
committed output or environment-mismatch root cause in those six runs. The red
icons remain valid historical records and were not rewritten.

## Round 3E reliability closure

- `npm run ci:verify:web` runs artifact contract tests, formatting, generated
  artifact cleanliness, typecheck, unit tests, build and Playwright in explicit
  fail-fast order.
- `bash db/scripts/ci-verify.sh` verifies the migration plan and performs two
  clean PostgreSQL rebuilds with test suites and inventory comparison.
- `npm run ci:verify` runs both surfaces and cannot return success after an
  internal failed step.
- The artifact gate regenerates active Round 3D/3E outputs twice, compares
  hashes, verifies formatting and requires a clean Git diff. Frozen external raw
  snapshots are hash-validated but never regenerated or reformatted.
- Regression tests cover generator nondeterminism, stale output, unformatted
  output and fail-fast orchestration.

The repository reports `main` as unprotected through the available GitHub API.
No setting was changed. Exact recommended manual settings are in
`docs/engineering/BRANCH_PROTECTION_RECOMMENDATION.md`.
