# Remote CI receipt

Status before final promotion: `FEATURE_CHECKPOINT_GREEN`.

The verified source-main run was `32807372976` at
`52c29e53a8f3d3ab60b72f2a6e5f60419b6173e5`; both frontend and PostgreSQL 17
jobs passed.

Feature run `32818720429` tested implementation checkpoint
`2d465e7b2c22ee7e49c8f038abc12c5730b746ac`:

- `Format, typecheck, test, and build` job `97712203338`: success;
- `PostgreSQL 17 ontology and corpus gates` job `97712203501`: success.

The two jobs used `npm run ci:verify:web` and
`bash db/scripts/ci-verify.sh`, respectively. GitHub emitted an actions-runtime
Node deprecation annotation, but no repository gate failed.

The receipt-finalization commit and promoted-main SHA are verified after their
pushes and reported in the terminal handoff. This avoids falsely claiming a
self-referential future run ID inside the commit that triggers it.
