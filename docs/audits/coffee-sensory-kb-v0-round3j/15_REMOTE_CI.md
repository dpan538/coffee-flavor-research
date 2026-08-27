# Remote CI

Remote frontend and PostgreSQL CI receipts must be bound to the exact final
branch SHA after the global corpus commits are pushed. Until those checks are
observed green, `REMOTE_FRONTEND_CI_PASS` and `REMOTE_POSTGRES_CI_PASS` remain
false and cannot be inferred from local success.
