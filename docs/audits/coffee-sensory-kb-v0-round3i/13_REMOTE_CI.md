# Remote CI

GitHub Actions run `32920566208` passed both repository jobs at commit
`c5059a6e6f457cf8e8ad3a429dbd099b2e64a713`: the web job completed in 1 minute
12 seconds and the PostgreSQL 17 job completed in 3 minutes 17 seconds. That run
verified the earlier formatting repair; it is not the final freeze-candidate CI
receipt because the branch subsequently added schema and freeze work.

Final promotion requires:

1. `Format, typecheck, test, and build` green on the exact candidate SHA;
2. `PostgreSQL 17 ontology and corpus gates` green on the same SHA;
3. exact candidate SHA verification before promotion;
4. a non-force, history-preserving promotion to `main`;
5. both jobs green again on the exact remote-main SHA; and
6. annotated-tag verification against that exact main commit.

| CI/promotion receipt            | State                                                                 |
| ------------------------------- | --------------------------------------------------------------------- |
| Earlier branch CI at `c5059a6…` | both jobs pass                                                        |
| Final candidate SHA             | Not yet created; post-commit external binding required                |
| Final candidate web CI          | Not yet run on the exact candidate SHA                                |
| Final candidate PostgreSQL CI   | Not yet run on the exact candidate SHA                                |
| Remote main SHA                 | Not yet promoted; exact external remote-main binding required         |
| Main web/PostgreSQL CI          | Not yet run on the exact remote-main SHA                              |
| Annotated freeze tag            | Not yet created; external tag-object and target verification required |
| Force push used                 | false                                                                 |

The release stays a candidate while any final field is pending.
