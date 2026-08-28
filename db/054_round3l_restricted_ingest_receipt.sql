-- Immutable receipt for an owner-controlled, row-level Round 3L ingest.
--
-- The actual result and assertion ledgers stay outside the public repository.
-- db/scripts/load-round3l-restricted.sql verifies and loads one restricted
-- freeze, then records only its whole-manifest commitment and aggregate counts.

CREATE TABLE audit.round3l_restricted_ingest_freeze (
    round3l_restricted_ingest_freeze_id BIGINT GENERATED ALWAYS AS IDENTITY,
    freeze_id TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    census_row_count BIGINT NOT NULL,
    attempt_row_count BIGINT NOT NULL,
    professional_record_row_count BIGINT NOT NULL,
    professional_assertion_row_count BIGINT NOT NULL,
    blocker_row_count BIGINT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT transaction_timestamp(),
    CONSTRAINT round3l_restricted_ingest_freeze_pk PRIMARY KEY (
        round3l_restricted_ingest_freeze_id
    ),
    CONSTRAINT round3l_restricted_ingest_freeze_key_uq UNIQUE (freeze_id),
    CONSTRAINT round3l_restricted_ingest_freeze_text_ck CHECK (
        freeze_id = lower(btrim(freeze_id))
        AND freeze_id ~ '^[a-z0-9][a-z0-9._:/-]*$'
        AND manifest_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT round3l_restricted_ingest_freeze_counts_ck CHECK (
        census_row_count > 0
        AND attempt_row_count > 0
        AND professional_record_row_count > 0
        AND professional_assertion_row_count >= 0
        AND blocker_row_count >= 0
    )
);

COMMENT ON TABLE audit.round3l_restricted_ingest_freeze IS
    'Whole-manifest commitment and aggregate receipt for owner-controlled Round 3L row-level data that is intentionally absent from public Git.';
