# Remote CI receipt

The repository workflow supplies two independent required scopes:

- frontend: formatting, TypeScript/schema checks, Vitest, smoke tests, and
  production build;
- PostgreSQL 17: two clean rebuild jobs exercising migrations, validation,
  negative tests, retrieval/query plans, and reproducibility comparison.

The workflow runs for pull requests and direct pushes to `main` or
`codex/**`. This permits feature-branch CI before main promotion even when a PR
cannot be created by the available GitHub integration.

The implementation checkpoint is
`ed5f3889afb0b5d7b7f658ff3c065f405d16e28b`. Remote run identity and the final
feature/main SHAs are recorded in GitHub Actions metadata and the final Codex
receipt after the non-force promotion. This document deliberately does not
attempt to contain the SHA of its own commit.
