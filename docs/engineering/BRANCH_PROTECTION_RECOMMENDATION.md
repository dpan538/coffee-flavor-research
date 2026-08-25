# Branch protection recommendation

Review date: 2026-08-25

The read-only GitHub API check returned `404 Branch not protected` for `main`.
Round 3E does not silently change repository settings. A repository
administrator should configure a branch ruleset with:

- target branch `main`;
- force pushes disabled;
- deletion disabled;
- pull request or equivalent reviewed merge required;
- branch required to be up to date before merge;
- required check `Format, typecheck, test, and build` (or its renamed unified
  web-verification successor);
- required check `PostgreSQL 17 ontology and corpus gates`;
- administrator bypass limited to documented recovery work.

Historical failed checks on intermediate commits should remain visible. Branch
protection should evaluate the current proposed head, not rewrite or conceal
earlier results.
