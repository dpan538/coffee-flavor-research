# Remote CI

The exact implementation checkpoint
`f077b840213c7ade540ae94ad3c4570b24ad632e` was pushed to the Round 3C feature
branch and inspected in GitHub Actions run `32804422644`.

```text
REMOTE_FRONTEND_CI_PASS=true
REMOTE_POSTGRES_CI_PASS=true
```

The frontend job ran format, typecheck, unit, build, browser install, and smoke
steps. The PostgreSQL job ran two clean PostgreSQL 17 rebuilds. The later audit
receipt commit must also receive a green exact-SHA run before non-force main
promotion; that final SHA is recorded externally to avoid self-reference.
