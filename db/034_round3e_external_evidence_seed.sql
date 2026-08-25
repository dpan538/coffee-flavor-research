\set ON_ERROR_STOP on

-- The included seed is generator-owned, hash-gated, and contains only
-- source-local records plus research candidates. It creates no model output.

BEGIN;

\ir data/round3e/generated/seed_round3e.sql

COMMIT;
