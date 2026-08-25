# Reproducibility receipt

The artifact contract rehashes all committed local source artifacts without
network access. The migration planner verifies frozen historical fingerprints
and finds 42 contiguous migrations. Database semantic, negative, retrieval and
query-plan suites pass on PostgreSQL 17.11.

`npm run ci:verify` passed on implementation checkpoint
`452b439eadfee682fedf8c1788a101420e15dbcf`. It also passed formatting,
generated-artifact cleanliness, typecheck, 9 unit tests, production build and
12 Playwright smoke paths.

Two clean disposable databases were created from `template0`, migrated, tested,
inventoried, compared and dropped. Key matched hashes were:

| Compared artifact                 | Build one / build two SHA-256                                      |
| --------------------------------- | ------------------------------------------------------------------ |
| migration manifest                | `bdcee0913543e0f2a1858ec279c77ec59056bcac09b31b2c64b8e9c4c36ec057` |
| seed manifest                     | `daaf6af829b6691ad9143755fe37d5667205a473fabb76f4a00ea5f3f2dc2ff4` |
| normalized schema                 | `1ddeb8955967152324f7951e2d0625f1b55b3502ae7d88bccf5b436300956354` |
| stable key inventory              | `8873006326ab48e0813114d357d4fafcff6d4c0d6ff1d05090f1d3f32aacdc11` |
| all-round validation results      | `1e8e1dc246ea47b759ce409598450d43e6153b20170d95c3daed8c215128ca8e` |
| Round 3F relationship delta       | `0010364372c6c47f520767f11bdb2a22c59ddd89b6231db6d11e1edf29215820` |
| Round 3G expected state and delta | `1dea4b034e077c3477b382f42fb4cec9a0fcf74c507dff7b8aa5053406f6ade8` |

`CLEAN_REBUILD_COUNT=2` and `REPRODUCIBILITY_PASS=true`. The local runner
reported `CI_VERIFY_WEB_PASS=true`, `CI_VERIFY_DATABASE_PASS=true` and
`CI_VERIFY_PASS=true`.
