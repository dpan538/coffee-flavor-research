# CI runtime profile and decomposition

## Measured evidence

The original workflow had a single PostgreSQL job with a 35-minute timeout.
Its commands were sequential, and the final command was:

```text
python3 -B db/scripts/run-with-heartbeat.py --phase postgres-corpus-verification --interval 60 -- bash db/scripts/rebuild-twice.sh
```

The supplied failed remote log reached `CI_HEARTBEAT elapsed=1920s` after the
Round 3M assertions, then the job context was cancelled. This is a measured
lower bound of 32 minutes for the final two-clean-database replay, not an
assertion failure.

The Stage 1 current-artifact profile ran once locally on the selected clean
worktree. It completed in 113 seconds. Measured slower stages were:

| Stage                                | Elapsed seconds | Result |
| ------------------------------------ | --------------: | ------ |
| `CURRENT_DESCRIPTOR_DATA`            |              45 | pass   |
| `BATCH4_CLEANED_30K`                 |              35 | pass   |
| `BATCH6_SEMANTIC_CORPUS`             |              25 | pass   |
| all remaining public artifact stages |               8 | pass   |

The local PostgreSQL parity attempt remained unavailable because the installed
Docker Desktop API did not answer its Unix socket within a bounded five-second
health probe. No local PostgreSQL 16 run is represented as version parity. The
remote `postgres:17-bookworm` historical replay nevertheless passed at
`898586d`. The current-database job passed at both `aaaa615` and `88cd394`; the
latter completed in 18m19s, within its 20-minute budget.

## New execution structure

| Verification job                | Trigger                                              |            Budget | Coverage                                                                                       |
| ------------------------------- | ---------------------------------------------------- | ----------------: | ---------------------------------------------------------------------------------------------- |
| `checks`                        | push/PR                                              |            25 min | unchanged frontend CI                                                                          |
| `database-artifacts`            | push/PR                                              |            15 min | all public corpus, generated-artifact, product-policy, checksum, and public-snapshot contracts |
| `database-current`              | push/PR                                              |            20 min | one clean PostgreSQL 17 migration, Round 3M load, and complete SQL suite                       |
| `historical-replay`             | protected research push + dispatch + weekly schedule |            75 min | original public artifact path plus the two-clean-database byte-reproducibility replay          |
| `ci-verify-restricted-local.sh` | owner local                                          | no remote timeout | required real restricted-input replay, fail-closed when inputs are absent                      |

The 75-minute dedicated replay limit follows the 1,920-second observed lower
bound and reserves more than a full current push budget for the second clean
database build. It is deliberately not applied to the normal push jobs.

The protected research-branch push trigger is required for this checkpoint:
GitHub only registers `workflow_dispatch` workflows from the default branch,
which has not yet been promoted. It remains manually dispatchable after the
validated fast-forward to `main`.

Stage-level markers use `CI_STAGE_START` and `CI_STAGE_END` and emit elapsed
seconds plus the wrapped command's exit status. A failed subcommand returns its
original nonzero status, so timing cannot turn a failure into a pass.

```text
CI_RUNTIME_PROFILE_LOCAL_ARTIFACT_PASS=true
CI_RUNTIME_PROFILE_LOCAL_DATABASE_PASS=NOT_EXECUTED_DOCKER_API_UNRESPONSIVE
CI_HISTORICAL_REPLAY_RUN_33461527537_PASS=true
CI_CURRENT_DATABASE_RUN_33470462970_PASS=true
CI_CURRENT_DATABASE_ELAPSED=18m19s
CI_HISTORICAL_REPLAY_RUN_33470462938_PASS=true
CI_HISTORICAL_REPLAY_ELAPSED=35m01s
CI_RUNTIME_PROFILE_REMOTE_RECOVERY_SHA=88cd394f96df0d409ea2b40b30396b314beecdd8
```
