\set ON_ERROR_STOP on

-- Coffee Sensory Knowledge Base V0
-- PostgreSQL 17 is a hard compatibility boundary. Keep extension setup in its
-- own transaction so later migrations never run against an unsupported server.

BEGIN;

DO $postgres_version_guard$
BEGIN
    IF current_setting('server_version_num')::integer < 170000 THEN
        RAISE EXCEPTION
            USING
                ERRCODE = 'feature_not_supported',
                MESSAGE = format(
                    'Coffee Sensory KB V0 requires PostgreSQL 17 or newer; server_version_num is %s',
                    current_setting('server_version_num')
                );
    END IF;
END;
$postgres_version_guard$;

-- pg_trgm supports the explicitly bounded lexical-retrieval fallback. V0 does
-- not install pgvector or any external vector-store dependency.
CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMIT;
