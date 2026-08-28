# PWA presentation audit

```text
PWA_STATUS=PLANNED
PWA_PUBLIC_CLAIM_ALLOWED=false
```

| Check                               | Result                 | Evidence / interpretation                                                                                   |
| ----------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------- |
| Web app manifest                    | FAIL                   | no linked web app manifest in the repository                                                                |
| Installable icons                   | FAIL                   | favicon exists; required installable icon set/manifest declarations do not                                  |
| Service worker                      | FAIL                   | no service-worker registration or worker implementation                                                     |
| Secure-context assumption           | NOT_APPLICABLE locally | production installability would require HTTPS or an accepted localhost context; no deployment claim is made |
| Browser installability              | FAIL                   | manifest/service-worker requirements are absent                                                             |
| Offline/app-shell behavior          | FAIL                   | no offline cache or app-shell receipt                                                                       |
| Responsive mobile layout            | PASS                   | mobile Playwright viewport and overflow checks                                                              |
| Keyboard access                     | PASS                   | semantic controls, skip link, and keyboard smoke path                                                       |
| Accessible names                    | PASS                   | primary navigation, search, view, comparison, and status actions have accessible roles/names                |
| Reduced-motion behavior             | PASS                   | media-query CSS and reduced-motion smoke path                                                               |
| Restricted corpus exposed to client | PASS                   | generated status contains aggregate counts only; frontend pilot data is project-curated                     |

## Public wording decision

Use **mobile-first web prototype** and **planned PWA**. Do not use an
unqualified PWA subtitle or imply installability/offline behavior. A minimal PWA
shell may be a separately scoped future frontend phase; this normalization pass
does not add a large offline architecture.
