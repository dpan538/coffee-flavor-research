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

The one requested local PostgreSQL profile was attempted in a disposable
`postgres:17-bookworm` Docker container. Image retrieval did not complete
under the concurrent GitHub DNS failure, so no container was created and no
database command ran. This failed environmental attempt is retained in the
execution transcript; it is not presented as a passing profile.

## New execution structure

| Verification job                | Trigger                    |            Budget | Coverage                                                                              |
| ------------------------------- | -------------------------- | ----------------: | ------------------------------------------------------------------------------------- |
| `checks`                        | push/PR                    |            25 min | unchanged frontend CI                                                                 |
| `database-artifacts`            | push/PR                    |            15 min | all public corpus, generated-artifact, checksum, and public-snapshot contracts        |
| `database-current`              | push/PR                    |            20 min | one clean PostgreSQL 17 migration, Round 3M load, and complete SQL suite              |
| `historical-replay`             | dispatch + weekly schedule |            75 min | original public artifact path plus the two-clean-database byte-reproducibility replay |
| `ci-verify-restricted-local.sh` | owner local                | no remote timeout | required real restricted-input replay, fail-closed when inputs are absent             |

The 75-minute dedicated replay limit follows the 1,920-second observed lower
bound and reserves more than a full current push budget for the second clean
database build. It is deliberately not applied to the normal push jobs.

Stage-level markers use `CI_STAGE_START` and `CI_STAGE_END` and emit elapsed
seconds plus the wrapped command's exit status. A failed subcommand returns its
original nonzero status, so timing cannot turn a failure into a pass.

```text
CI_RUNTIME_PROFILE_LOCAL_ARTIFACT_PASS=true
CI_RUNTIME_PROFILE_LOCAL_DATABASE_PASS=NOT_EXECUTED_DOCKER_IMAGE_RETRIEVAL_UNAVAILABLE
CI_RUNTIME_PROFILE_REMOTE_PASS=AWAITING_POST_PUSH_RUN
```
