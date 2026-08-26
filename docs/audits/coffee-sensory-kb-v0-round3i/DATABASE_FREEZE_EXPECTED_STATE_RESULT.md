# Database-freeze expected-state result

Pre-import contract:
`db/data/round3i/database_freeze_expected_state.tsv` at commit
`602624143fef8fa4250e5e84f07478101b0846ff`. Threshold revisions: zero.

## Coverage decision

| Freeze dimension                   | Baseline |      Minimum | Preferred | Observed | Result                    |
| ---------------------------------- | -------: | -----------: | --------: | -------: | ------------------------- |
| Canonical concepts                 |      130 |          130 |       130 |      130 | Hard pass                 |
| Active sensory attributes          |       92 |           92 |        92 |       92 | Hard pass                 |
| Contemporary language families     |        0 |            3 |         5 |        3 | Hard pass; preferred miss |
| Contemporary documents             |        0 |          500 |     1,500 |    3,289 | Hard and preferred pass   |
| Governed unique expressions        |    1,777 |        2,500 |     3,500 |    2,996 | Hard pass; preferred miss |
| Source-authored `zh-Hans` families |        0 |            2 |         3 |        2 | Hard pass; preferred miss |
| `zh-Hans` sensory expressions      |        0 | non-blocking |       200 |      249 | Preferred pass            |
| Source-local-supported memberships |        6 |            6 |        10 |        6 | Hard pass                 |
| Cross-source-supported memberships |        4 |            4 |         6 |        4 | Hard pass                 |
| Ranges with source-local evidence  |        6 |            6 |         7 |        6 | Hard pass                 |
| Ranges with cross-source evidence  |        3 | non-blocking |         4 |        4 | Preferred pass            |
| Independent question targets       |       12 |            6 |        10 |       12 | Hard and preferred pass   |
| Feature definitions                |       20 |           20 |        20 |       20 | Hard pass                 |
| Source partitions                  |       12 |           12 |        12 |       12 | Hard pass                 |

All mandatory coverage gates pass. The acquisition stop rule therefore selects
condition A and broad acquisition stops. The evidence-plane decision is:

`DATABASE_FREEZE_EXPECTED_STATE_RESULT=FREEZE_CANDIDATE_WITH_PREFERRED_GAPS`

## Engineering decision

The final release additionally requires complete source/rights/privacy/hash/
relationship provenance, 8 approved current views, 11 verified artifacts, zero
critical quality counts, two matching PostgreSQL 17 rebuilds, green exact-
candidate CI, exact-main promotion, green main CI, and an annotated tag on that
main SHA.

The source/rights/privacy/hash/relationship gates, approved-view count,
artifact count, quality gates, model-prebuild readiness, and two-rebuild
comparison now pass. Until exact-candidate CI, exact-main promotion/main CI,
and annotated-tag outputs exist:

- `MODEL_PREBUILD_DATA_READY=true`
- `RESEARCH_DATABASE_V0_FREEZE_READY=false`
- `RESEARCH_DATABASE_FREEZE_STATE=FREEZE_CANDIDATE_WITH_PREFERRED_GAPS`
- `FREEZE_MANIFEST_SHA256=10ed5e29972082bc5046e6fb9c14be3f24b103a94a79c2482e5cd4819aa3991e`
- `FINAL_REMOTE_SHA=NOT_YET_PROMOTED__EXTERNAL_EXACT_MAIN_BINDING_REQUIRED`

After all hard engineering gates pass and exact-main attestation is written,
the only allowed final state is `RESEARCH_DATABASE_V0_FROZEN`. Preferred misses
remain limitations and are not rewritten as passes.
