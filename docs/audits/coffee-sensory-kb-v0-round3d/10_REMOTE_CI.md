# Remote CI

- Implementation checkpoint: `183ae279563a9763372fa50d26303d9c547317ec`
- Workflow run: `32806848705`
- Frontend job: pass, including formatting, typecheck, unit tests, production
  build, and Playwright smoke tests.
- PostgreSQL 17 job: pass, including two complete clean rebuilds.

```text
REMOTE_FRONTEND_CI_PASS=true
REMOTE_POSTGRES_CI_PASS=true
```

The receipt commit will not be promoted until both jobs are green. Its own CI
run will also be checked before non-force promotion.
