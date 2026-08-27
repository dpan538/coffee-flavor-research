\set ON_ERROR_STOP on

-- Round 3K competition-native identity and effective-record grain.
--
-- This migration is deliberately data-free.  It adds an append-friendly
-- competition domain beside the frozen evidence, corpus, context, ml, and
-- audit domains.  Professional evidence, source snapshots, rights decisions,
-- judge observations, scores, and descriptor assertions are attached by
-- later forward migrations.

BEGIN;

CREATE SCHEMA competition;

COMMENT ON SCHEMA competition IS
    'Versioned professional-competition identities and fresh preparation-service events. Documents and judge rows are evidence about these records, not the effective-record grain.';

CREATE TABLE competition.series (
    series_id BIGINT GENERATED ALWAYS AS IDENTITY,
    series_key TEXT NOT NULL,
    official_name TEXT NOT NULL,
    organizer_name TEXT NOT NULL,
    official_series_identifier TEXT,
    series_scope_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    series_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_series_pk PRIMARY KEY (series_id),
    CONSTRAINT competition_series_key_uq UNIQUE (series_key),
    CONSTRAINT competition_series_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_series_text_ck CHECK (
        series_key = lower(btrim(series_key)) AND series_key <> ''
        AND official_name = btrim(official_name) AND official_name <> ''
        AND organizer_name = btrim(organizer_name) AND organizer_name <> ''
        AND (
            official_series_identifier IS NULL
            OR official_series_identifier = btrim(official_series_identifier)
               AND official_series_identifier <> ''
        )
    ),
    CONSTRAINT competition_series_scope_ck CHECK (
        series_scope_code IN (
            'GLOBAL', 'CONTINENTAL', 'NATIONAL', 'REGIONAL',
            'COUNTRY_PROGRAM', 'COMMERCIAL', 'OTHER_REPORTED'
        )
    ),
    CONSTRAINT competition_series_metadata_object_ck CHECK (
        jsonb_typeof(series_metadata) = 'object'
    )
);

COMMENT ON TABLE competition.series IS
    'Stable official organizer/competition-series identity. Editions, mirrors, pages, categories, and exports do not create new series identities.';

CREATE TABLE competition.edition (
    edition_id BIGINT GENERATED ALWAYS AS IDENTITY,
    edition_key TEXT NOT NULL,
    series_id BIGINT NOT NULL,
    series_local_edition_key TEXT NOT NULL,
    official_edition_identifier TEXT,
    edition_name TEXT NOT NULL,
    edition_year INTEGER NOT NULL,
    starts_on DATE,
    ends_on DATE,
    lifecycle_status_code TEXT NOT NULL,
    edition_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_edition_pk PRIMARY KEY (edition_id),
    CONSTRAINT competition_edition_key_uq UNIQUE (edition_key),
    CONSTRAINT competition_edition_series_local_uq UNIQUE (
        series_id, series_local_edition_key
    ),
    CONSTRAINT competition_edition_id_series_uq UNIQUE (edition_id, series_id),
    CONSTRAINT competition_edition_series_fk FOREIGN KEY (series_id)
        REFERENCES competition.series (series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_edition_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_edition_text_ck CHECK (
        edition_key = lower(btrim(edition_key)) AND edition_key <> ''
        AND series_local_edition_key = lower(btrim(series_local_edition_key))
        AND series_local_edition_key <> ''
        AND edition_name = btrim(edition_name) AND edition_name <> ''
        AND (
            official_edition_identifier IS NULL
            OR official_edition_identifier = btrim(official_edition_identifier)
               AND official_edition_identifier <> ''
        )
    ),
    CONSTRAINT competition_edition_year_ck CHECK (
        edition_year BETWEEN 1800 AND 2200
    ),
    CONSTRAINT competition_edition_dates_ck CHECK (
        starts_on IS NULL OR ends_on IS NULL OR ends_on >= starts_on
    ),
    CONSTRAINT competition_edition_metadata_object_ck CHECK (
        jsonb_typeof(edition_metadata) = 'object'
    )
);

COMMENT ON TABLE competition.edition IS
    'A series-local official edition with an explicit reported year; retrieval time never supplies edition_year.';

-- Version lineage is shared by rule, scoresheet, category, round, entry,
-- coffee, lot, and roast-batch identities.  Identity-family keys are globally
-- namespaced.  A later version must point to the immediately preceding row in
-- the same family; this makes corrections appendable without silent identity
-- replacement.
CREATE FUNCTION competition.enforce_version_lineage()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_version_lineage$
DECLARE
    group_column TEXT := TG_ARGV[0];
    version_column TEXT := TG_ARGV[1];
    supersedes_column TEXT := TG_ARGV[2];
    id_column TEXT := TG_ARGV[3];
    row_payload JSONB := to_jsonb(NEW);
    old_payload JSONB;
    predecessor_payload JSONB;
    group_value TEXT;
    predecessor_group_value TEXT;
    version_value INTEGER;
    predecessor_version_value INTEGER;
    predecessor_id BIGINT;
    argument_index INTEGER;
    scope_column TEXT;
BEGIN
    group_value := row_payload ->> group_column;
    version_value := (row_payload ->> version_column)::INTEGER;
    predecessor_id := NULLIF(row_payload ->> supersedes_column, '')::BIGINT;

    IF TG_OP = 'UPDATE' THEN
        old_payload := to_jsonb(OLD);
        IF old_payload ->> group_column
               IS DISTINCT FROM row_payload ->> group_column
           OR old_payload ->> version_column
               IS DISTINCT FROM row_payload ->> version_column
           OR old_payload ->> supersedes_column
               IS DISTINCT FROM row_payload ->> supersedes_column THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_identity_version_columns_immutable_ck',
                MESSAGE = 'competition_identity_version_columns_immutable_ck: identity family, version, and predecessor are immutable; append a new version';
        END IF;

        IF TG_NARGS > 4 THEN
            FOR argument_index IN 4..TG_NARGS - 1 LOOP
                scope_column := TG_ARGV[argument_index];
                IF old_payload ->> scope_column
                   IS DISTINCT FROM row_payload ->> scope_column THEN
                    RAISE EXCEPTION USING
                        ERRCODE = '23514',
                        CONSTRAINT = 'competition_identity_version_scope_immutable_ck',
                        MESSAGE = format(
                            'competition_identity_version_scope_immutable_ck: identity scope %s is immutable; append a new version',
                            scope_column
                        );
                END IF;
            END LOOP;
        END IF;
    END IF;

    IF version_value = 1 THEN
        IF predecessor_id IS NOT NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_identity_version_lineage_ck',
                MESSAGE = 'competition_identity_version_lineage_ck: version 1 cannot supersede another identity row';
        END IF;
        RETURN NEW;
    END IF;

    IF predecessor_id IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'competition_identity_version_lineage_ck',
            MESSAGE = 'competition_identity_version_lineage_ck: versions above 1 must identify their immediate predecessor';
    END IF;

    EXECUTE format(
        'SELECT to_jsonb(predecessor) FROM %I.%I AS predecessor WHERE predecessor.%I = $1',
        TG_TABLE_SCHEMA, TG_TABLE_NAME, id_column
    )
    INTO predecessor_payload
    USING predecessor_id;

    IF predecessor_payload IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23503',
            CONSTRAINT = 'competition_identity_version_lineage_fk',
            MESSAGE = 'competition_identity_version_lineage_fk: predecessor identity row does not exist';
    END IF;

    predecessor_group_value := predecessor_payload ->> group_column;
    predecessor_version_value :=
        (predecessor_payload ->> version_column)::INTEGER;

    IF predecessor_group_value IS DISTINCT FROM group_value
       OR predecessor_version_value <> version_value - 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'competition_identity_version_lineage_ck',
            MESSAGE = 'competition_identity_version_lineage_ck: predecessor must be the immediately prior version in the same identity family';
    END IF;

    IF TG_NARGS > 4 THEN
        FOR argument_index IN 4..TG_NARGS - 1 LOOP
            scope_column := TG_ARGV[argument_index];
            IF predecessor_payload ->> scope_column
               IS DISTINCT FROM row_payload ->> scope_column THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'competition_identity_version_scope_ck',
                    MESSAGE = format(
                        'competition_identity_version_scope_ck: version lineage cannot change %s',
                        scope_column
                    );
            END IF;
        END LOOP;
    END IF;

    RETURN NEW;
END;
$enforce_version_lineage$;

CREATE TABLE competition.rule_version (
    rule_version_id BIGINT GENERATED ALWAYS AS IDENTITY,
    rule_version_key TEXT NOT NULL,
    series_id BIGINT NOT NULL,
    rule_family_key TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    supersedes_rule_version_id BIGINT,
    publication_status_code TEXT NOT NULL,
    official_version_label TEXT,
    official_locator TEXT,
    effective_from DATE,
    effective_until DATE,
    status_note TEXT,
    lifecycle_status_code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_rule_version_pk PRIMARY KEY (rule_version_id),
    CONSTRAINT competition_rule_version_key_uq UNIQUE (rule_version_key),
    CONSTRAINT competition_rule_version_family_version_uq UNIQUE (
        rule_family_key, version_number
    ),
    CONSTRAINT competition_rule_version_id_series_uq UNIQUE (
        rule_version_id, series_id
    ),
    CONSTRAINT competition_rule_version_supersedes_uq UNIQUE (
        supersedes_rule_version_id
    ),
    CONSTRAINT competition_rule_version_series_fk FOREIGN KEY (series_id)
        REFERENCES competition.series (series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_rule_version_supersedes_fk FOREIGN KEY (
        supersedes_rule_version_id
    ) REFERENCES competition.rule_version (rule_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_rule_version_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_rule_version_text_ck CHECK (
        rule_version_key = lower(btrim(rule_version_key))
        AND rule_version_key <> ''
        AND rule_family_key = lower(btrim(rule_family_key))
        AND rule_family_key <> ''
        AND (
            official_version_label IS NULL
            OR official_version_label = btrim(official_version_label)
               AND official_version_label <> ''
        )
        AND (
            official_locator IS NULL
            OR official_locator = btrim(official_locator)
               AND official_locator <> ''
        )
        AND (
            status_note IS NULL
            OR status_note = btrim(status_note) AND status_note <> ''
        )
    ),
    CONSTRAINT competition_rule_version_number_ck CHECK (
        version_number > 0
    ),
    CONSTRAINT competition_rule_version_publication_ck CHECK (
        publication_status_code IN ('VERSIONED', 'EXPLICIT_NOT_PUBLISHED')
        AND (
            publication_status_code = 'VERSIONED'
            AND official_version_label IS NOT NULL
            AND official_locator IS NOT NULL
            OR publication_status_code = 'EXPLICIT_NOT_PUBLISHED'
            AND official_version_label IS NULL
            AND official_locator IS NULL
            AND status_note IS NOT NULL
        )
    ),
    CONSTRAINT competition_rule_version_dates_ck CHECK (
        effective_from IS NULL
        OR effective_until IS NULL
        OR effective_until >= effective_from
    )
);

CREATE TRIGGER competition_rule_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.rule_version
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'rule_family_key', 'version_number', 'supersedes_rule_version_id',
    'rule_version_id', 'series_id'
);

COMMENT ON TABLE competition.rule_version IS
    'Versioned official rule/protocol identity. EXPLICIT_NOT_PUBLISHED is a governed decision row, not a missing foreign key.';

CREATE TABLE competition.scoresheet_version (
    scoresheet_version_id BIGINT GENERATED ALWAYS AS IDENTITY,
    scoresheet_version_key TEXT NOT NULL,
    series_id BIGINT NOT NULL,
    rule_version_id BIGINT NOT NULL,
    scoresheet_family_key TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    supersedes_scoresheet_version_id BIGINT,
    publication_status_code TEXT NOT NULL,
    official_version_label TEXT,
    official_locator TEXT,
    status_note TEXT,
    lifecycle_status_code TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_scoresheet_version_pk PRIMARY KEY (scoresheet_version_id),
    CONSTRAINT competition_scoresheet_version_key_uq UNIQUE (scoresheet_version_key),
    CONSTRAINT competition_scoresheet_family_version_uq UNIQUE (
        scoresheet_family_key, version_number
    ),
    CONSTRAINT competition_scoresheet_id_scope_uq UNIQUE (
        scoresheet_version_id, series_id, rule_version_id
    ),
    CONSTRAINT competition_scoresheet_supersedes_uq UNIQUE (
        supersedes_scoresheet_version_id
    ),
    CONSTRAINT competition_scoresheet_rule_scope_fk FOREIGN KEY (
        rule_version_id, series_id
    ) REFERENCES competition.rule_version (rule_version_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_scoresheet_supersedes_fk FOREIGN KEY (
        supersedes_scoresheet_version_id
    ) REFERENCES competition.scoresheet_version (scoresheet_version_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_scoresheet_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_scoresheet_text_ck CHECK (
        scoresheet_version_key = lower(btrim(scoresheet_version_key))
        AND scoresheet_version_key <> ''
        AND scoresheet_family_key = lower(btrim(scoresheet_family_key))
        AND scoresheet_family_key <> ''
        AND (
            official_version_label IS NULL
            OR official_version_label = btrim(official_version_label)
               AND official_version_label <> ''
        )
        AND (
            official_locator IS NULL
            OR official_locator = btrim(official_locator)
               AND official_locator <> ''
        )
        AND (
            status_note IS NULL
            OR status_note = btrim(status_note) AND status_note <> ''
        )
    ),
    CONSTRAINT competition_scoresheet_version_number_ck CHECK (
        version_number > 0
    ),
    CONSTRAINT competition_scoresheet_publication_ck CHECK (
        publication_status_code IN ('VERSIONED', 'NOT_PUBLISHED')
        AND (
            publication_status_code = 'VERSIONED'
            AND official_version_label IS NOT NULL
            AND official_locator IS NOT NULL
            OR publication_status_code = 'NOT_PUBLISHED'
            AND official_version_label IS NULL
            AND official_locator IS NULL
            AND status_note IS NOT NULL
        )
    )
);

CREATE TRIGGER competition_scoresheet_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.scoresheet_version
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'scoresheet_family_key', 'version_number',
    'supersedes_scoresheet_version_id', 'scoresheet_version_id', 'series_id'
);

COMMENT ON TABLE competition.scoresheet_version IS
    'Versioned official scoresheet identity. Service-level status retains NOT_APPLICABLE and uncertain source states without inventing a scoresheet row.';

CREATE TABLE competition.category (
    category_id BIGINT GENERATED ALWAYS AS IDENTITY,
    category_key TEXT NOT NULL,
    category_identity_key TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    supersedes_category_id BIGINT,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    rule_version_id BIGINT NOT NULL,
    source_category_code TEXT NOT NULL,
    category_name TEXT NOT NULL,
    category_kind_code TEXT NOT NULL,
    lifecycle_status_code TEXT NOT NULL,
    category_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_category_pk PRIMARY KEY (category_id),
    CONSTRAINT competition_category_key_uq UNIQUE (category_key),
    CONSTRAINT competition_category_identity_version_uq UNIQUE (
        category_identity_key, identity_version
    ),
    CONSTRAINT competition_category_edition_code_version_uq UNIQUE (
        edition_id, source_category_code, identity_version
    ),
    CONSTRAINT competition_category_scope_uq UNIQUE (
        category_id, series_id, edition_id, rule_version_id
    ),
    CONSTRAINT competition_category_identity_scope_uq UNIQUE (
        category_id, series_id, edition_id
    ),
    CONSTRAINT competition_category_supersedes_uq UNIQUE (supersedes_category_id),
    CONSTRAINT competition_category_edition_scope_fk FOREIGN KEY (
        edition_id, series_id
    ) REFERENCES competition.edition (edition_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_category_rule_scope_fk FOREIGN KEY (
        rule_version_id, series_id
    ) REFERENCES competition.rule_version (rule_version_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_category_supersedes_fk FOREIGN KEY (supersedes_category_id)
        REFERENCES competition.category (category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_category_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_category_text_ck CHECK (
        category_key = lower(btrim(category_key)) AND category_key <> ''
        AND category_identity_key = lower(btrim(category_identity_key))
        AND category_identity_key <> ''
        AND source_category_code = btrim(source_category_code)
        AND source_category_code <> ''
        AND category_name = btrim(category_name) AND category_name <> ''
    ),
    CONSTRAINT competition_category_version_ck CHECK (identity_version > 0),
    CONSTRAINT competition_category_kind_ck CHECK (
        category_kind_code IN (
            'COMPETITION_CLASS', 'SERVICE_CLASS', 'ROAST_LABEL_CLASS',
            'PRODUCT_CLASS', 'OTHER_REPORTED'
        )
    ),
    CONSTRAINT competition_category_metadata_object_ck CHECK (
        jsonb_typeof(category_metadata) = 'object'
    )
);

CREATE TRIGGER competition_category_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.category
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'category_identity_key', 'identity_version', 'supersedes_category_id',
    'category_id', 'series_id'
);

COMMENT ON TABLE competition.category IS
    'Edition-scoped, rule-versioned source category. It contains no C1 mapping; filter, espresso, Nordic, or other category names cannot imply roast depth.';

CREATE TABLE competition.round (
    round_id BIGINT GENERATED ALWAYS AS IDENTITY,
    round_key TEXT NOT NULL,
    round_identity_key TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    supersedes_round_id BIGINT,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    rule_version_id BIGINT NOT NULL,
    source_round_code TEXT NOT NULL,
    round_name TEXT NOT NULL,
    round_kind_code TEXT NOT NULL,
    sequence_number INTEGER,
    lifecycle_status_code TEXT NOT NULL,
    round_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_round_pk PRIMARY KEY (round_id),
    CONSTRAINT competition_round_key_uq UNIQUE (round_key),
    CONSTRAINT competition_round_identity_version_uq UNIQUE (
        round_identity_key, identity_version
    ),
    CONSTRAINT competition_round_edition_code_version_uq UNIQUE (
        edition_id, source_round_code, identity_version
    ),
    CONSTRAINT competition_round_scope_uq UNIQUE (
        round_id, series_id, edition_id, rule_version_id
    ),
    CONSTRAINT competition_round_supersedes_uq UNIQUE (supersedes_round_id),
    CONSTRAINT competition_round_edition_scope_fk FOREIGN KEY (
        edition_id, series_id
    ) REFERENCES competition.edition (edition_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_round_rule_scope_fk FOREIGN KEY (
        rule_version_id, series_id
    ) REFERENCES competition.rule_version (rule_version_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_round_supersedes_fk FOREIGN KEY (supersedes_round_id)
        REFERENCES competition.round (round_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_round_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_round_text_ck CHECK (
        round_key = lower(btrim(round_key)) AND round_key <> ''
        AND round_identity_key = lower(btrim(round_identity_key))
        AND round_identity_key <> ''
        AND source_round_code = btrim(source_round_code)
        AND source_round_code <> ''
        AND round_name = btrim(round_name) AND round_name <> ''
    ),
    CONSTRAINT competition_round_version_ck CHECK (identity_version > 0),
    CONSTRAINT competition_round_kind_ck CHECK (
        round_kind_code IN (
            'PRELIMINARY', 'QUALIFYING', 'SEMIFINAL', 'FINAL',
            'AUCTION', 'PRODUCTION_CUPPING', 'PUBLISHED_AGGREGATE',
            'OTHER_REPORTED'
        )
    ),
    CONSTRAINT competition_round_sequence_ck CHECK (
        sequence_number IS NULL OR sequence_number > 0
    ),
    CONSTRAINT competition_round_metadata_object_ck CHECK (
        jsonb_typeof(round_metadata) = 'object'
    )
);

CREATE TRIGGER competition_round_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.round
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'round_identity_key', 'identity_version', 'supersedes_round_id',
    'round_id', 'series_id'
);

COMMENT ON TABLE competition.round IS
    'Edition-scoped, rule-versioned competition round. A published aggregate is explicit; absent preliminary rounds are never invented.';

CREATE TABLE competition.entry (
    entry_id BIGINT GENERATED ALWAYS AS IDENTITY,
    entry_key TEXT NOT NULL,
    entry_identity_key TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    supersedes_entry_id BIGINT,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    source_entry_identifier TEXT,
    entry_kind_code TEXT NOT NULL,
    display_label TEXT,
    lifecycle_status_code TEXT NOT NULL,
    entry_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_entry_pk PRIMARY KEY (entry_id),
    CONSTRAINT competition_entry_key_uq UNIQUE (entry_key),
    CONSTRAINT competition_entry_identity_version_uq UNIQUE (
        entry_identity_key, identity_version
    ),
    CONSTRAINT competition_entry_scope_uq UNIQUE (
        entry_id, series_id, edition_id, category_id
    ),
    CONSTRAINT competition_entry_supersedes_uq UNIQUE (supersedes_entry_id),
    CONSTRAINT competition_entry_category_scope_fk FOREIGN KEY (
        category_id, series_id, edition_id
    ) REFERENCES competition.category (category_id, series_id, edition_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_entry_supersedes_fk FOREIGN KEY (supersedes_entry_id)
        REFERENCES competition.entry (entry_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_entry_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_entry_text_ck CHECK (
        entry_key = lower(btrim(entry_key)) AND entry_key <> ''
        AND entry_identity_key = lower(btrim(entry_identity_key))
        AND entry_identity_key <> ''
        AND (
            source_entry_identifier IS NULL
            OR source_entry_identifier = btrim(source_entry_identifier)
               AND source_entry_identifier <> ''
        )
        AND (
            display_label IS NULL
            OR display_label = btrim(display_label) AND display_label <> ''
        )
    ),
    CONSTRAINT competition_entry_version_ck CHECK (identity_version > 0),
    CONSTRAINT competition_entry_kind_ck CHECK (
        entry_kind_code IN (
            'COMPETITOR_ENTRY', 'ORGANIZER_ENTRY', 'AUCTION_ENTRY',
            'GOVERNED_PSEUDONYMOUS_ENTRY', 'OTHER_REPORTED'
        )
    ),
    CONSTRAINT competition_entry_identifier_ck CHECK (
        source_entry_identifier IS NOT NULL
        OR entry_kind_code = 'GOVERNED_PSEUDONYMOUS_ENTRY'
    ),
    CONSTRAINT competition_entry_metadata_object_ck CHECK (
        jsonb_typeof(entry_metadata) = 'object'
    )
);

CREATE TRIGGER competition_entry_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.entry
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'entry_identity_key', 'identity_version', 'supersedes_entry_id',
    'entry_id', 'series_id', 'edition_id', 'category_id'
);

COMMENT ON TABLE competition.entry IS
    'One category-scoped official or governed pseudonymous competition entry. Judge rows never become entry rows.';

CREATE TABLE competition.coffee_identity (
    coffee_identity_id BIGINT GENERATED ALWAYS AS IDENTITY,
    coffee_identity_key TEXT NOT NULL,
    coffee_identity_group_key TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    supersedes_coffee_identity_id BIGINT,
    identity_kind_code TEXT NOT NULL,
    source_native_coffee_identifier TEXT,
    display_label TEXT,
    lifecycle_status_code TEXT NOT NULL,
    identity_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_coffee_identity_pk PRIMARY KEY (coffee_identity_id),
    CONSTRAINT competition_coffee_identity_key_uq UNIQUE (coffee_identity_key),
    CONSTRAINT competition_coffee_identity_group_version_uq UNIQUE (
        coffee_identity_group_key, identity_version
    ),
    CONSTRAINT competition_coffee_identity_supersedes_uq UNIQUE (
        supersedes_coffee_identity_id
    ),
    CONSTRAINT competition_coffee_identity_supersedes_fk FOREIGN KEY (
        supersedes_coffee_identity_id
    ) REFERENCES competition.coffee_identity (coffee_identity_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_coffee_identity_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_coffee_identity_text_ck CHECK (
        coffee_identity_key = lower(btrim(coffee_identity_key))
        AND coffee_identity_key <> ''
        AND coffee_identity_group_key = lower(btrim(coffee_identity_group_key))
        AND coffee_identity_group_key <> ''
        AND (
            source_native_coffee_identifier IS NULL
            OR source_native_coffee_identifier = btrim(source_native_coffee_identifier)
               AND source_native_coffee_identifier <> ''
        )
        AND (
            display_label IS NULL
            OR display_label = btrim(display_label) AND display_label <> ''
        )
    ),
    CONSTRAINT competition_coffee_identity_version_ck CHECK (
        identity_version > 0
    ),
    CONSTRAINT competition_coffee_identity_kind_ck CHECK (
        identity_kind_code IN (
            'SOURCE_DECLARED', 'GOVERNED_PSEUDONYMOUS',
            'REVIEWED_LINKED', 'REPORTED_UNRESOLVED', 'WITHHELD'
        )
    ),
    CONSTRAINT competition_coffee_identity_identifier_ck CHECK (
        source_native_coffee_identifier IS NOT NULL
        OR identity_kind_code IN (
            'GOVERNED_PSEUDONYMOUS', 'REPORTED_UNRESOLVED', 'WITHHELD'
        )
    ),
    CONSTRAINT competition_coffee_identity_metadata_object_ck CHECK (
        jsonb_typeof(identity_metadata) = 'object'
    )
);

CREATE TRIGGER competition_coffee_identity_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.coffee_identity
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'coffee_identity_group_key', 'identity_version',
    'supersedes_coffee_identity_id', 'coffee_identity_id'
);

COMMENT ON TABLE competition.coffee_identity IS
    'Versioned source-declared, reviewed, or governed pseudonymous coffee identity shared across legitimate rounds and republications.';

CREATE TABLE competition.lot (
    lot_id BIGINT GENERATED ALWAYS AS IDENTITY,
    lot_key TEXT NOT NULL,
    lot_identity_key TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    supersedes_lot_id BIGINT,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    coffee_identity_id BIGINT NOT NULL,
    source_lot_identifier TEXT,
    lot_kind_code TEXT NOT NULL,
    display_label TEXT,
    lifecycle_status_code TEXT NOT NULL,
    lot_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_lot_pk PRIMARY KEY (lot_id),
    CONSTRAINT competition_lot_key_uq UNIQUE (lot_key),
    CONSTRAINT competition_lot_identity_version_uq UNIQUE (
        lot_identity_key, identity_version
    ),
    CONSTRAINT competition_lot_scope_uq UNIQUE (
        lot_id, series_id, edition_id, category_id
    ),
    CONSTRAINT competition_lot_coffee_uq UNIQUE (
        lot_id, coffee_identity_id
    ),
    CONSTRAINT competition_lot_full_scope_uq UNIQUE (
        lot_id, series_id, edition_id, category_id, coffee_identity_id
    ),
    CONSTRAINT competition_lot_supersedes_uq UNIQUE (supersedes_lot_id),
    CONSTRAINT competition_lot_category_scope_fk FOREIGN KEY (
        category_id, series_id, edition_id
    ) REFERENCES competition.category (category_id, series_id, edition_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_lot_coffee_fk FOREIGN KEY (coffee_identity_id)
        REFERENCES competition.coffee_identity (coffee_identity_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_lot_supersedes_fk FOREIGN KEY (supersedes_lot_id)
        REFERENCES competition.lot (lot_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_lot_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_lot_text_ck CHECK (
        lot_key = lower(btrim(lot_key)) AND lot_key <> ''
        AND lot_identity_key = lower(btrim(lot_identity_key))
        AND lot_identity_key <> ''
        AND (
            source_lot_identifier IS NULL
            OR source_lot_identifier = btrim(source_lot_identifier)
               AND source_lot_identifier <> ''
        )
        AND (
            display_label IS NULL
            OR display_label = btrim(display_label) AND display_label <> ''
        )
    ),
    CONSTRAINT competition_lot_version_ck CHECK (identity_version > 0),
    CONSTRAINT competition_lot_kind_ck CHECK (
        lot_kind_code IN (
            'COMPETITION_LOT', 'AUCTION_LOT', 'GREEN_COFFEE_LOT',
            'ROASTED_COFFEE_LOT', 'GOVERNED_PSEUDONYMOUS_LOT',
            'OTHER_REPORTED'
        )
    ),
    CONSTRAINT competition_lot_identifier_ck CHECK (
        source_lot_identifier IS NOT NULL
        OR lot_kind_code = 'GOVERNED_PSEUDONYMOUS_LOT'
    ),
    CONSTRAINT competition_lot_metadata_object_ck CHECK (
        jsonb_typeof(lot_metadata) = 'object'
    )
);

CREATE TRIGGER competition_lot_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.lot
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'lot_identity_key', 'identity_version', 'supersedes_lot_id',
    'lot_id', 'series_id', 'edition_id', 'category_id'
);

COMMENT ON TABLE competition.lot IS
    'Edition/category lot identity linked directly to one governed coffee identity. Auction and roaster republications reuse or explicitly relate the identity rather than multiplying it.';

CREATE TABLE competition.entry_coffee_link (
    entry_coffee_link_id BIGINT GENERATED ALWAYS AS IDENTITY,
    entry_coffee_link_key TEXT NOT NULL,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    entry_id BIGINT NOT NULL,
    coffee_identity_id BIGINT NOT NULL,
    lot_id BIGINT,
    link_role_code TEXT NOT NULL,
    linkage_status_code TEXT NOT NULL,
    linkage_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_entry_coffee_link_pk PRIMARY KEY (entry_coffee_link_id),
    CONSTRAINT competition_entry_coffee_link_key_uq UNIQUE (entry_coffee_link_key),
    CONSTRAINT competition_entry_coffee_link_fact_uq UNIQUE NULLS NOT DISTINCT (
        entry_id, coffee_identity_id, lot_id, link_role_code
    ),
    CONSTRAINT competition_entry_coffee_link_entry_scope_fk FOREIGN KEY (
        entry_id, series_id, edition_id, category_id
    ) REFERENCES competition.entry (
        entry_id, series_id, edition_id, category_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_entry_coffee_link_coffee_fk FOREIGN KEY (
        coffee_identity_id
    ) REFERENCES competition.coffee_identity (coffee_identity_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_entry_coffee_link_lot_scope_fk FOREIGN KEY (
        lot_id, series_id, edition_id, category_id, coffee_identity_id
    ) REFERENCES competition.lot (
        lot_id, series_id, edition_id, category_id, coffee_identity_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_entry_coffee_link_text_ck CHECK (
        entry_coffee_link_key = lower(btrim(entry_coffee_link_key))
        AND entry_coffee_link_key <> ''
        AND (
            linkage_note IS NULL
            OR linkage_note = btrim(linkage_note) AND linkage_note <> ''
        )
    ),
    CONSTRAINT competition_entry_coffee_link_role_ck CHECK (
        link_role_code IN (
            'PRIMARY', 'COMPONENT', 'ALTERNATE', 'REPEAT_LINK',
            'REPORTED_UNRESOLVED'
        )
    ),
    CONSTRAINT competition_entry_coffee_link_status_ck CHECK (
        linkage_status_code IN (
            'SOURCE_DECLARED', 'REVIEWED_CONFIRMED', 'REVIEW_REQUIRED',
            'REPORTED_UNRESOLVED'
        )
        AND (
            link_role_code = 'REPORTED_UNRESOLVED'
        ) = (
            linkage_status_code = 'REPORTED_UNRESOLVED'
        )
    )
);

CREATE UNIQUE INDEX competition_entry_one_primary_coffee_uq
    ON competition.entry_coffee_link (entry_id)
    WHERE link_role_code = 'PRIMARY'
      AND linkage_status_code IN ('SOURCE_DECLARED', 'REVIEWED_CONFIRMED');

COMMENT ON TABLE competition.entry_coffee_link IS
    'Explicit many-to-many entry-to-coffee lineage. Blends keep component identities; unresolved candidates do not silently become confirmed links.';

CREATE TABLE competition.roast_batch (
    roast_batch_id BIGINT GENERATED ALWAYS AS IDENTITY,
    roast_batch_key TEXT NOT NULL,
    roast_batch_identity_key TEXT NOT NULL,
    identity_version INTEGER NOT NULL,
    supersedes_roast_batch_id BIGINT,
    coffee_identity_id BIGINT NOT NULL,
    lot_id BIGINT,
    source_roast_batch_identifier TEXT,
    roast_batch_kind_code TEXT NOT NULL,
    roasted_on DATE,
    source_native_roast_status_code TEXT NOT NULL,
    source_native_roast_value TEXT,
    source_native_roast_scheme TEXT,
    c1_mapping_status_code TEXT NOT NULL,
    reviewed_c1_roast_category_id BIGINT,
    c1_mapping_basis_code TEXT,
    lifecycle_status_code TEXT NOT NULL,
    roast_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_roast_batch_pk PRIMARY KEY (roast_batch_id),
    CONSTRAINT competition_roast_batch_key_uq UNIQUE (roast_batch_key),
    CONSTRAINT competition_roast_batch_identity_version_uq UNIQUE (
        roast_batch_identity_key, identity_version
    ),
    CONSTRAINT competition_roast_batch_supersedes_uq UNIQUE (
        supersedes_roast_batch_id
    ),
    CONSTRAINT competition_roast_batch_coffee_fk FOREIGN KEY (coffee_identity_id)
        REFERENCES competition.coffee_identity (coffee_identity_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_roast_batch_lot_coffee_fk FOREIGN KEY (
        lot_id, coffee_identity_id
    ) REFERENCES competition.lot (lot_id, coffee_identity_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_roast_batch_supersedes_fk FOREIGN KEY (
        supersedes_roast_batch_id
    ) REFERENCES competition.roast_batch (roast_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_roast_batch_c1_fk FOREIGN KEY (
        reviewed_c1_roast_category_id
    ) REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_roast_batch_lifecycle_fk FOREIGN KEY (lifecycle_status_code)
        REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_roast_batch_text_ck CHECK (
        roast_batch_key = lower(btrim(roast_batch_key))
        AND roast_batch_key <> ''
        AND roast_batch_identity_key = lower(btrim(roast_batch_identity_key))
        AND roast_batch_identity_key <> ''
        AND (
            source_roast_batch_identifier IS NULL
            OR source_roast_batch_identifier = btrim(source_roast_batch_identifier)
               AND source_roast_batch_identifier <> ''
        )
        AND (
            source_native_roast_value IS NULL
            OR source_native_roast_value = btrim(source_native_roast_value)
               AND source_native_roast_value <> ''
        )
        AND (
            source_native_roast_scheme IS NULL
            OR source_native_roast_scheme = btrim(source_native_roast_scheme)
               AND source_native_roast_scheme <> ''
        )
    ),
    CONSTRAINT competition_roast_batch_version_ck CHECK (identity_version > 0),
    CONSTRAINT competition_roast_batch_kind_ck CHECK (
        roast_batch_kind_code IN (
            'COMPETITION_ROAST', 'PRODUCTION_ROAST', 'SAMPLE_ROAST',
            'SOURCE_DECLARED', 'GOVERNED_PSEUDONYMOUS'
        )
    ),
    CONSTRAINT competition_roast_batch_native_status_ck CHECK (
        source_native_roast_status_code IN (
            'REPORTED', 'NOT_REPORTED', 'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND (
            source_native_roast_status_code = 'REPORTED'
            AND source_native_roast_value IS NOT NULL
            AND source_native_roast_scheme IS NOT NULL
            OR source_native_roast_status_code = 'REPORTED_UNRESOLVED'
            AND source_native_roast_value IS NOT NULL
            OR source_native_roast_status_code IN (
                'NOT_REPORTED', 'SOURCE_UNKNOWN', 'NOT_APPLICABLE'
            )
            AND source_native_roast_value IS NULL
            AND source_native_roast_scheme IS NULL
        )
    ),
    CONSTRAINT competition_roast_batch_c1_status_ck CHECK (
        c1_mapping_status_code IN (
            'REVIEWED', 'NOT_REPORTED', 'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND (
            c1_mapping_status_code = 'REVIEWED'
            AND reviewed_c1_roast_category_id IS NOT NULL
            AND c1_mapping_basis_code IN (
                'DIRECT_SOURCE_ROAST', 'DIRECT_ROAST_MEASUREMENT',
                'GOVERNED_REVIEW'
            )
            AND source_native_roast_status_code IN (
                'REPORTED', 'REPORTED_UNRESOLVED'
            )
            OR c1_mapping_status_code = 'REPORTED_UNRESOLVED'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code IN (
                'REPORTED', 'REPORTED_UNRESOLVED'
            )
            OR c1_mapping_status_code = 'NOT_REPORTED'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code = 'NOT_REPORTED'
            OR c1_mapping_status_code = 'SOURCE_UNKNOWN'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code = 'SOURCE_UNKNOWN'
            OR c1_mapping_status_code = 'NOT_APPLICABLE'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code = 'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT competition_roast_batch_metadata_object_ck CHECK (
        jsonb_typeof(roast_metadata) = 'object'
    )
);

CREATE TRIGGER competition_roast_batch_version_lineage_biu
BEFORE INSERT OR UPDATE ON competition.roast_batch
FOR EACH ROW EXECUTE FUNCTION competition.enforce_version_lineage(
    'roast_batch_identity_key', 'identity_version',
    'supersedes_roast_batch_id', 'roast_batch_id', 'coffee_identity_id'
);

COMMENT ON TABLE competition.roast_batch IS
    'Versioned roast-batch identity and direct source-native roast context. It has no competition-category foreign key, preventing category-to-roast inference.';

CREATE TABLE competition.preparation_service (
    preparation_service_id BIGINT GENERATED ALWAYS AS IDENTITY,
    preparation_service_key TEXT NOT NULL,
    series_id BIGINT NOT NULL,
    edition_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    round_id BIGINT NOT NULL,
    entry_id BIGINT,
    lot_id BIGINT,
    entry_service_key TEXT NOT NULL,
    repeat_of_preparation_service_id BIGINT,
    repeat_relationship_code TEXT,
    rule_version_id BIGINT NOT NULL,
    scoresheet_status_code TEXT NOT NULL,
    scoresheet_version_id BIGINT,
    roast_batch_id BIGINT,
    fresh_preparation_confirmed BOOLEAN NOT NULL,
    fresh_preparation_status_code TEXT NOT NULL,
    preparation_taxonomy_code TEXT NOT NULL,
    milk_auxiliary BOOLEAN NOT NULL DEFAULT FALSE,
    black_coffee_core_candidate BOOLEAN NOT NULL DEFAULT FALSE,
    c0_source_status_code TEXT NOT NULL,
    source_native_preparation_value TEXT,
    c0_preparation_concept_id BIGINT,
    c0_assignment_basis_code TEXT,
    source_native_roast_status_code TEXT NOT NULL,
    source_native_roast_value TEXT,
    source_native_roast_scheme TEXT,
    c1_mapping_status_code TEXT NOT NULL,
    reviewed_c1_roast_category_id BIGINT,
    c1_mapping_basis_code TEXT,
    lifecycle_status_code TEXT NOT NULL,
    service_metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT competition_preparation_service_pk PRIMARY KEY (preparation_service_id),
    CONSTRAINT competition_preparation_service_key_uq UNIQUE (preparation_service_key),
    CONSTRAINT competition_preparation_service_series_fk FOREIGN KEY (series_id)
        REFERENCES competition.series (series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_edition_scope_fk FOREIGN KEY (
        edition_id, series_id
    ) REFERENCES competition.edition (edition_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_category_scope_fk FOREIGN KEY (
        category_id, series_id, edition_id, rule_version_id
    ) REFERENCES competition.category (
        category_id, series_id, edition_id, rule_version_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_round_scope_fk FOREIGN KEY (
        round_id, series_id, edition_id, rule_version_id
    ) REFERENCES competition.round (
        round_id, series_id, edition_id, rule_version_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_entry_scope_fk FOREIGN KEY (
        entry_id, series_id, edition_id, category_id
    ) REFERENCES competition.entry (
        entry_id, series_id, edition_id, category_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_lot_scope_fk FOREIGN KEY (
        lot_id, series_id, edition_id, category_id
    ) REFERENCES competition.lot (
        lot_id, series_id, edition_id, category_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_rule_scope_fk FOREIGN KEY (
        rule_version_id, series_id
    ) REFERENCES competition.rule_version (rule_version_id, series_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_scoresheet_scope_fk FOREIGN KEY (
        scoresheet_version_id, series_id, rule_version_id
    ) REFERENCES competition.scoresheet_version (
        scoresheet_version_id, series_id, rule_version_id
    ) ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_roast_batch_fk FOREIGN KEY (
        roast_batch_id
    ) REFERENCES competition.roast_batch (roast_batch_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_repeat_fk FOREIGN KEY (
        repeat_of_preparation_service_id
    ) REFERENCES competition.preparation_service (preparation_service_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_c0_fk FOREIGN KEY (
        c0_preparation_concept_id
    ) REFERENCES context.preparation_concept (preparation_concept_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_c1_fk FOREIGN KEY (
        reviewed_c1_roast_category_id
    ) REFERENCES context.roast_category (roast_category_id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_lifecycle_fk FOREIGN KEY (
        lifecycle_status_code
    ) REFERENCES ref.lifecycle_status (lifecycle_status_code)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    CONSTRAINT competition_preparation_service_text_ck CHECK (
        preparation_service_key = lower(btrim(preparation_service_key))
        AND preparation_service_key <> ''
        AND entry_service_key = lower(btrim(entry_service_key))
        AND entry_service_key <> ''
        AND (
            source_native_preparation_value IS NULL
            OR source_native_preparation_value = btrim(source_native_preparation_value)
               AND source_native_preparation_value <> ''
        )
        AND (
            source_native_roast_value IS NULL
            OR source_native_roast_value = btrim(source_native_roast_value)
               AND source_native_roast_value <> ''
        )
        AND (
            source_native_roast_scheme IS NULL
            OR source_native_roast_scheme = btrim(source_native_roast_scheme)
               AND source_native_roast_scheme <> ''
        )
    ),
    CONSTRAINT competition_preparation_service_subject_ck CHECK (
        (entry_id IS NOT NULL)::INTEGER + (lot_id IS NOT NULL)::INTEGER = 1
    ),
    CONSTRAINT competition_preparation_service_repeat_pair_ck CHECK (
        repeat_of_preparation_service_id IS NULL
        AND repeat_relationship_code IS NULL
        OR repeat_of_preparation_service_id IS NOT NULL
        AND repeat_relationship_code IN (
                'LATER_ROUND', 'CROSS_CATEGORY', 'AUCTION_REPUBLICATION',
                'ROASTER_REPUBLICATION', 'OTHER_REVIEWED'
            )
    ),
    CONSTRAINT competition_preparation_service_no_self_repeat_ck CHECK (
        repeat_of_preparation_service_id IS NULL
        OR repeat_of_preparation_service_id <> preparation_service_id
    ),
    CONSTRAINT competition_preparation_service_scoresheet_status_ck CHECK (
        scoresheet_status_code IN (
            'VERSIONED', 'NOT_PUBLISHED', 'NOT_REPORTED',
            'SOURCE_UNKNOWN', 'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND (scoresheet_status_code = 'VERSIONED') =
            (scoresheet_version_id IS NOT NULL)
    ),
    CONSTRAINT competition_preparation_service_fresh_status_ck CHECK (
        fresh_preparation_status_code IN (
            'CONFIRMED_FRESH', 'CONFIRMED_NOT_FRESH',
            'PENDING_CONFIRMATION', 'NOT_REPORTED', 'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND fresh_preparation_confirmed =
            (fresh_preparation_status_code = 'CONFIRMED_FRESH')
    ),
    CONSTRAINT competition_preparation_service_taxonomy_ck CHECK (
        preparation_taxonomy_code IN (
            'STANDARDIZED_CUPPING', 'GREEN_COMPETITION_CUPPING',
            'PRODUCTION_ROAST_CUPPING', 'FILTER', 'POUR_OVER',
            'COMPETITION_BATCH_FILTER', 'IMMERSION', 'SIPHON',
            'MANUAL_PRESSURE', 'HYBRID', 'ESPRESSO',
            'ESPRESSO_PLUS_WATER', 'FRESH_CEZVE_IBRIK',
            'FRESH_COLD_EXTRACTION', 'FRESH_MILK_ESPRESSO',
            'FRESH_PLANT_MILK_ESPRESSO', 'RTD', 'BOTTLED', 'CANNED',
            'SHELF_STABLE_COLD_BREW', 'INSTANT', 'SOLUBLE',
            'FLAVORED_COFFEE', 'COFFEE_COCKTAIL',
            'NONCOFFEE_SIGNATURE_DRINK', 'OTHER_REPORTED_FRESH',
            'NOT_REPORTED', 'SOURCE_UNKNOWN', 'REPORTED_UNRESOLVED',
            'NOT_APPLICABLE'
        )
        AND (
            preparation_taxonomy_code NOT IN (
                'RTD', 'BOTTLED', 'CANNED', 'SHELF_STABLE_COLD_BREW',
                'INSTANT', 'SOLUBLE'
            )
            OR NOT fresh_preparation_confirmed
        )
        AND (
            preparation_taxonomy_code <> 'NOT_REPORTED'
            OR fresh_preparation_status_code = 'NOT_REPORTED'
        )
        AND (
            preparation_taxonomy_code <> 'SOURCE_UNKNOWN'
            OR fresh_preparation_status_code = 'SOURCE_UNKNOWN'
        )
        AND (
            preparation_taxonomy_code <> 'REPORTED_UNRESOLVED'
            OR fresh_preparation_status_code = 'REPORTED_UNRESOLVED'
        )
        AND (
            preparation_taxonomy_code <> 'NOT_APPLICABLE'
            OR fresh_preparation_status_code = 'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT competition_preparation_service_milk_auxiliary_ck CHECK (
        milk_auxiliary = (preparation_taxonomy_code IN (
            'FRESH_MILK_ESPRESSO', 'FRESH_PLANT_MILK_ESPRESSO'
        ))
        AND (NOT milk_auxiliary OR fresh_preparation_confirmed)
        AND NOT (milk_auxiliary AND black_coffee_core_candidate)
    ),
    CONSTRAINT competition_preparation_service_core_candidate_ck CHECK (
        NOT black_coffee_core_candidate
        OR fresh_preparation_confirmed
           AND NOT milk_auxiliary
           AND preparation_taxonomy_code IN (
               'STANDARDIZED_CUPPING', 'GREEN_COMPETITION_CUPPING',
               'PRODUCTION_ROAST_CUPPING', 'FILTER', 'POUR_OVER',
               'COMPETITION_BATCH_FILTER', 'IMMERSION', 'SIPHON',
               'MANUAL_PRESSURE', 'HYBRID', 'ESPRESSO',
               'ESPRESSO_PLUS_WATER', 'FRESH_CEZVE_IBRIK',
               'FRESH_COLD_EXTRACTION'
           )
    ),
    CONSTRAINT competition_preparation_service_c0_status_ck CHECK (
        c0_source_status_code IN (
            'REPORTED', 'NOT_REPORTED', 'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND (
            c0_source_status_code = 'REPORTED'
            AND c0_preparation_concept_id IS NOT NULL
            AND c0_assignment_basis_code IN (
                'OFFICIAL_CATEGORY', 'OFFICIAL_PROTOCOL',
                'OFFICIAL_SCORESHEET_FIELD', 'OFFICIAL_ENTRY_METADATA'
            )
            OR c0_source_status_code = 'REPORTED_UNRESOLVED'
            AND source_native_preparation_value IS NOT NULL
            AND c0_preparation_concept_id IS NULL
            AND c0_assignment_basis_code IN (
                'OFFICIAL_CATEGORY', 'OFFICIAL_PROTOCOL',
                'OFFICIAL_SCORESHEET_FIELD', 'OFFICIAL_ENTRY_METADATA'
            )
            OR c0_source_status_code IN (
                'NOT_REPORTED', 'SOURCE_UNKNOWN', 'NOT_APPLICABLE'
            )
            AND source_native_preparation_value IS NULL
            AND c0_preparation_concept_id IS NULL
            AND c0_assignment_basis_code IS NULL
        )
    ),
    CONSTRAINT competition_preparation_service_native_roast_status_ck CHECK (
        source_native_roast_status_code IN (
            'REPORTED', 'NOT_REPORTED', 'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND (
            source_native_roast_status_code = 'REPORTED'
            AND source_native_roast_value IS NOT NULL
            AND source_native_roast_scheme IS NOT NULL
            OR source_native_roast_status_code = 'REPORTED_UNRESOLVED'
            AND source_native_roast_value IS NOT NULL
            OR source_native_roast_status_code IN (
                'NOT_REPORTED', 'SOURCE_UNKNOWN', 'NOT_APPLICABLE'
            )
            AND source_native_roast_value IS NULL
            AND source_native_roast_scheme IS NULL
        )
    ),
    CONSTRAINT competition_preparation_service_c1_status_ck CHECK (
        c1_mapping_status_code IN (
            'REVIEWED', 'NOT_REPORTED', 'SOURCE_UNKNOWN',
            'REPORTED_UNRESOLVED', 'NOT_APPLICABLE'
        )
        AND (
            c1_mapping_status_code = 'REVIEWED'
            AND reviewed_c1_roast_category_id IS NOT NULL
            AND c1_mapping_basis_code IN (
                'DIRECT_SOURCE_ROAST', 'DIRECT_ROAST_MEASUREMENT',
                'GOVERNED_REVIEW'
            )
            AND source_native_roast_status_code IN (
                'REPORTED', 'REPORTED_UNRESOLVED'
            )
            OR c1_mapping_status_code = 'REPORTED_UNRESOLVED'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code IN (
                'REPORTED', 'REPORTED_UNRESOLVED'
            )
            OR c1_mapping_status_code = 'NOT_REPORTED'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code = 'NOT_REPORTED'
            OR c1_mapping_status_code = 'SOURCE_UNKNOWN'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code = 'SOURCE_UNKNOWN'
            OR c1_mapping_status_code = 'NOT_APPLICABLE'
            AND reviewed_c1_roast_category_id IS NULL
            AND c1_mapping_basis_code IS NULL
            AND source_native_roast_status_code = 'NOT_APPLICABLE'
        )
    ),
    CONSTRAINT competition_preparation_service_metadata_object_ck CHECK (
        jsonb_typeof(service_metadata) = 'object'
    )
);

-- One active row per effective professional-record grain.  Separate partial
-- indexes avoid NULL equality loopholes while preserving the entry-or-lot XOR.
CREATE UNIQUE INDEX competition_preparation_service_entry_grain_uq
    ON competition.preparation_service (
        series_id, edition_id, category_id, round_id, entry_id,
        entry_service_key
    )
    WHERE entry_id IS NOT NULL AND lifecycle_status_code = 'active';

CREATE UNIQUE INDEX competition_preparation_service_lot_grain_uq
    ON competition.preparation_service (
        series_id, edition_id, category_id, round_id, lot_id,
        entry_service_key
    )
    WHERE lot_id IS NOT NULL AND lifecycle_status_code = 'active';

CREATE INDEX competition_preparation_service_entry_service_idx
    ON competition.preparation_service (
        entry_id, entry_service_key, round_id
    ) WHERE entry_id IS NOT NULL;

CREATE INDEX competition_preparation_service_lot_service_idx
    ON competition.preparation_service (
        lot_id, entry_service_key, round_id
    ) WHERE lot_id IS NOT NULL;

CREATE INDEX competition_preparation_service_context_idx
    ON competition.preparation_service (
        preparation_taxonomy_code, c0_source_status_code,
        c1_mapping_status_code, milk_auxiliary
    );

CREATE UNIQUE INDEX competition_category_active_source_code_uq
    ON competition.category (edition_id, source_category_code)
    WHERE lifecycle_status_code = 'active';

CREATE UNIQUE INDEX competition_round_active_source_code_uq
    ON competition.round (edition_id, source_round_code)
    WHERE lifecycle_status_code = 'active';

CREATE UNIQUE INDEX competition_entry_active_source_identifier_uq
    ON competition.entry (category_id, source_entry_identifier)
    WHERE lifecycle_status_code = 'active'
      AND source_entry_identifier IS NOT NULL;

CREATE UNIQUE INDEX competition_lot_active_source_identifier_uq
    ON competition.lot (category_id, source_lot_identifier)
    WHERE lifecycle_status_code = 'active'
      AND source_lot_identifier IS NOT NULL;

CREATE FUNCTION competition.enforce_current_context_targets()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_current_context_targets$
DECLARE
    c0_is_current BOOLEAN;
    c1_is_current BOOLEAN;
    c0_target_id BIGINT := NULLIF(
        to_jsonb(NEW) ->> 'c0_preparation_concept_id', ''
    )::BIGINT;
    c1_target_id BIGINT := NULLIF(
        to_jsonb(NEW) ->> 'reviewed_c1_roast_category_id', ''
    )::BIGINT;
    old_c0_target_id BIGINT;
    old_c1_target_id BIGINT;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        old_c0_target_id := NULLIF(
            to_jsonb(OLD) ->> 'c0_preparation_concept_id', ''
        )::BIGINT;
        old_c1_target_id := NULLIF(
            to_jsonb(OLD) ->> 'reviewed_c1_roast_category_id', ''
        )::BIGINT;
    END IF;

    IF TG_TABLE_NAME = 'preparation_service'
       AND c0_target_id IS NOT NULL
       AND (
           TG_OP = 'INSERT'
           OR c0_target_id IS DISTINCT FROM old_c0_target_id
       ) THEN
        SELECT
            concept.c0_top_level
            AND concept.preparation_concept_type_code = 'family'
            AND concept.lifecycle_status_code = 'active'
            AND concept.preparation_concept_key IN (
                'preparation.family.filter_percolation',
                'preparation.family.immersion',
                'preparation.family.hybrid',
                'preparation.family.espresso_pressure',
                'preparation.family.diluted_espresso',
                'preparation.family.stovetop_boiled',
                'preparation.family.cold_extraction',
                'preparation.family.espresso_milk'
            )
        INTO c0_is_current
        FROM context.preparation_concept AS concept
        WHERE concept.preparation_concept_id =
              c0_target_id;

        IF c0_is_current IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_preparation_service_current_c0_ck',
                MESSAGE = 'competition_preparation_service_current_c0_ck: C0 target must be an active current top-level preparation family';
        END IF;
    END IF;

    IF c1_target_id IS NOT NULL
       AND (
           TG_OP = 'INSERT'
           OR c1_target_id IS DISTINCT FROM old_c1_target_id
       ) THEN
        SELECT
            scheme.is_project_normalized_target
            AND scheme.lifecycle_status_code = 'active'
            AND category.lifecycle_status_code = 'active'
            AND category.ordinal_position BETWEEN 1 AND 7
            AND (
                SELECT count(*)
                FROM context.roast_category AS scheme_category
                WHERE scheme_category.roast_scheme_id = scheme.roast_scheme_id
                  AND scheme_category.lifecycle_status_code = 'active'
            ) = 7
        INTO c1_is_current
        FROM context.roast_category AS category
        JOIN context.roast_scheme AS scheme
          ON scheme.roast_scheme_id = category.roast_scheme_id
        WHERE category.roast_category_id =
              c1_target_id;

        IF c1_is_current IS NOT TRUE THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_current_c1_target_ck',
                MESSAGE = 'competition_current_c1_target_ck: reviewed C1 must target an active category in the current project seven-level scheme';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_current_context_targets$;

CREATE TRIGGER competition_roast_batch_current_context_biu
BEFORE INSERT OR UPDATE ON competition.roast_batch
FOR EACH ROW EXECUTE FUNCTION competition.enforce_current_context_targets();

CREATE TRIGGER competition_preparation_service_current_context_biu
BEFORE INSERT OR UPDATE ON competition.preparation_service
FOR EACH ROW EXECUTE FUNCTION competition.enforce_current_context_targets();

CREATE FUNCTION competition.enforce_preparation_service_semantics()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_preparation_service_semantics$
DECLARE
    linked_roast competition.roast_batch%ROWTYPE;
    repeated_service competition.preparation_service%ROWTYPE;
    repeat_cycle_exists BOOLEAN;
    unlinked_repeat_exists BOOLEAN;
    shared_coffee_identity_exists BOOLEAN;
    repeated_round_sequence INTEGER;
    new_round_sequence INTEGER;
BEGIN
    IF NEW.roast_batch_id IS NOT NULL THEN
        SELECT * INTO linked_roast
        FROM competition.roast_batch
        WHERE roast_batch_id = NEW.roast_batch_id;

        IF linked_roast.roast_batch_id IS NULL
           OR linked_roast.source_native_roast_status_code
                IS DISTINCT FROM NEW.source_native_roast_status_code
           OR linked_roast.source_native_roast_value
                IS DISTINCT FROM NEW.source_native_roast_value
           OR linked_roast.source_native_roast_scheme
                IS DISTINCT FROM NEW.source_native_roast_scheme
           OR linked_roast.c1_mapping_status_code
                IS DISTINCT FROM NEW.c1_mapping_status_code
           OR linked_roast.reviewed_c1_roast_category_id
                IS DISTINCT FROM NEW.reviewed_c1_roast_category_id
           OR linked_roast.c1_mapping_basis_code
                IS DISTINCT FROM NEW.c1_mapping_basis_code THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_service_roast_batch_context_ck',
                MESSAGE = 'competition_service_roast_batch_context_ck: linked roast-batch context must be preserved exactly on the effective service record';
        END IF;

        IF NEW.lot_id IS NOT NULL AND NOT EXISTS (
            SELECT 1
            FROM competition.lot AS lot
            WHERE lot.lot_id = NEW.lot_id
              AND lot.coffee_identity_id = linked_roast.coffee_identity_id
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_service_roast_batch_coffee_ck',
                MESSAGE = 'competition_service_roast_batch_coffee_ck: lot service and roast batch must identify the same coffee';
        END IF;

        IF NEW.entry_id IS NOT NULL AND NOT EXISTS (
            SELECT 1
            FROM competition.entry_coffee_link AS link
            WHERE link.entry_id = NEW.entry_id
              AND link.coffee_identity_id = linked_roast.coffee_identity_id
              AND link.linkage_status_code IN (
                  'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
              )
        ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_service_roast_batch_coffee_ck',
                MESSAGE = 'competition_service_roast_batch_coffee_ck: entry service roast batch must link to a confirmed entry coffee identity';
        END IF;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM competition.preparation_service AS service
        WHERE service.preparation_service_id <>
              COALESCE(NEW.preparation_service_id, -1)
          AND service.lifecycle_status_code = 'active'
          AND service.entry_service_key = NEW.entry_service_key
          AND (
              NEW.entry_id IS NOT NULL AND service.entry_id = NEW.entry_id
              OR NEW.lot_id IS NOT NULL AND service.lot_id = NEW.lot_id
          )
    ) INTO unlinked_repeat_exists;

    IF NEW.repeat_of_preparation_service_id IS NULL
       AND unlinked_repeat_exists
       AND (
           TG_OP = 'INSERT'
           OR OLD.repeat_of_preparation_service_id IS NOT NULL
           OR OLD.entry_service_key IS DISTINCT FROM NEW.entry_service_key
           OR OLD.entry_id IS DISTINCT FROM NEW.entry_id
           OR OLD.lot_id IS DISTINCT FROM NEW.lot_id
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'competition_preparation_service_repeat_link_ck',
            MESSAGE = 'competition_preparation_service_repeat_link_ck: repeated entry-service observations require an explicit repeat relationship';
    END IF;

    IF NEW.repeat_of_preparation_service_id IS NOT NULL THEN
        SELECT * INTO repeated_service
        FROM competition.preparation_service
        WHERE preparation_service_id =
              NEW.repeat_of_preparation_service_id;

        IF repeated_service.preparation_service_id IS NULL THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_preparation_service_repeat_link_ck',
                MESSAGE = 'competition_preparation_service_repeat_link_ck: referenced preparation service does not exist';
        END IF;

        IF NEW.repeat_relationship_code = 'LATER_ROUND' THEN
            IF repeated_service.entry_service_key <>
                   NEW.entry_service_key
               OR repeated_service.entry_id IS DISTINCT FROM NEW.entry_id
               OR repeated_service.lot_id IS DISTINCT FROM NEW.lot_id
               OR repeated_service.round_id = NEW.round_id THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'competition_preparation_service_repeat_link_ck',
                    MESSAGE = 'competition_preparation_service_repeat_link_ck: later-round repeat must retain subject and entry-service identity while changing round';
            END IF;

            SELECT sequence_number INTO repeated_round_sequence
            FROM competition.round
            WHERE round_id = repeated_service.round_id;

            SELECT sequence_number INTO new_round_sequence
            FROM competition.round
            WHERE round_id = NEW.round_id;

            IF repeated_round_sequence IS NOT NULL
               AND new_round_sequence IS NOT NULL
               AND new_round_sequence <= repeated_round_sequence THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'competition_preparation_service_repeat_order_ck',
                    MESSAGE = 'competition_preparation_service_repeat_order_ck: LATER_ROUND must point from a later sequence to an earlier sequence';
            END IF;
        ELSE
            WITH new_coffee_identity AS (
                SELECT lot.coffee_identity_id
                FROM competition.lot AS lot
                WHERE lot.lot_id = NEW.lot_id
                UNION
                SELECT link.coffee_identity_id
                FROM competition.entry_coffee_link AS link
                WHERE link.entry_id = NEW.entry_id
                  AND link.linkage_status_code IN (
                      'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
                  )
            ),
            repeated_coffee_identity AS (
                SELECT lot.coffee_identity_id
                FROM competition.lot AS lot
                WHERE lot.lot_id = repeated_service.lot_id
                UNION
                SELECT link.coffee_identity_id
                FROM competition.entry_coffee_link AS link
                WHERE link.entry_id = repeated_service.entry_id
                  AND link.linkage_status_code IN (
                      'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
                  )
            )
            SELECT EXISTS (
                SELECT 1
                FROM new_coffee_identity AS new_identity
                JOIN repeated_coffee_identity AS repeated_identity
                  USING (coffee_identity_id)
            ) INTO shared_coffee_identity_exists;

            IF shared_coffee_identity_exists IS NOT TRUE
               OR NEW.repeat_relationship_code = 'CROSS_CATEGORY'
                  AND repeated_service.category_id = NEW.category_id THEN
                RAISE EXCEPTION USING
                    ERRCODE = '23514',
                    CONSTRAINT = 'competition_preparation_service_repeat_link_ck',
                    MESSAGE = 'competition_preparation_service_repeat_link_ck: cross-category and republication repeats require a shared governed coffee identity; CROSS_CATEGORY must change category';
            END IF;
        END IF;

        WITH RECURSIVE ancestry(preparation_service_id) AS (
            SELECT repeated_service.repeat_of_preparation_service_id
            UNION ALL
            SELECT parent.repeat_of_preparation_service_id
            FROM competition.preparation_service AS parent
            JOIN ancestry
              ON parent.preparation_service_id = ancestry.preparation_service_id
            WHERE ancestry.preparation_service_id IS NOT NULL
        )
        SELECT EXISTS (
            SELECT 1
            FROM ancestry
            WHERE preparation_service_id = NEW.preparation_service_id
        ) INTO repeat_cycle_exists;

        IF repeat_cycle_exists THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_preparation_service_repeat_acyclic_ck',
                MESSAGE = 'competition_preparation_service_repeat_acyclic_ck: repeat lineage must remain acyclic';
        END IF;
    END IF;

    RETURN NEW;
END;
$enforce_preparation_service_semantics$;

CREATE TRIGGER competition_preparation_service_semantics_biu
BEFORE INSERT OR UPDATE ON competition.preparation_service
FOR EACH ROW EXECUTE FUNCTION competition.enforce_preparation_service_semantics();

CREATE FUNCTION competition.protect_referenced_roast_batch_context()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $protect_referenced_roast_batch_context$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM competition.preparation_service AS service
        WHERE service.roast_batch_id = OLD.roast_batch_id
    ) AND ROW(
        OLD.coffee_identity_id,
        OLD.lot_id,
        OLD.source_roast_batch_identifier,
        OLD.roast_batch_kind_code,
        OLD.roasted_on,
        OLD.source_native_roast_status_code,
        OLD.source_native_roast_value,
        OLD.source_native_roast_scheme,
        OLD.c1_mapping_status_code,
        OLD.reviewed_c1_roast_category_id,
        OLD.c1_mapping_basis_code
    ) IS DISTINCT FROM ROW(
        NEW.coffee_identity_id,
        NEW.lot_id,
        NEW.source_roast_batch_identifier,
        NEW.roast_batch_kind_code,
        NEW.roasted_on,
        NEW.source_native_roast_status_code,
        NEW.source_native_roast_value,
        NEW.source_native_roast_scheme,
        NEW.c1_mapping_status_code,
        NEW.reviewed_c1_roast_category_id,
        NEW.c1_mapping_basis_code
    ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            CONSTRAINT = 'competition_referenced_roast_batch_immutable_ck',
            MESSAGE = 'competition_referenced_roast_batch_immutable_ck: append a new roast-batch version instead of changing context used by a service';
    END IF;

    RETURN NEW;
END;
$protect_referenced_roast_batch_context$;

CREATE TRIGGER competition_referenced_roast_batch_context_bu
BEFORE UPDATE ON competition.roast_batch
FOR EACH ROW EXECUTE FUNCTION
    competition.protect_referenced_roast_batch_context();

-- Entry subjects must resolve to at least one source-declared or reviewed
-- coffee identity by transaction end.  The deferred constraint permits a
-- loader to insert the service and its link in either order.
CREATE FUNCTION competition.enforce_service_coffee_identity_link()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $enforce_service_coffee_identity_link$
DECLARE
    affected_entry_id BIGINT;
    affected_entry_ids BIGINT[];
BEGIN
    IF TG_TABLE_NAME = 'preparation_service' THEN
        IF TG_OP = 'INSERT' THEN
            affected_entry_ids := ARRAY[NEW.entry_id];
        ELSE
            affected_entry_ids := ARRAY[OLD.entry_id, NEW.entry_id];
        END IF;
    ELSIF TG_OP = 'INSERT' THEN
        affected_entry_ids := ARRAY[NEW.entry_id];
    ELSIF TG_OP = 'DELETE' THEN
        affected_entry_ids := ARRAY[OLD.entry_id];
    ELSE
        affected_entry_ids := ARRAY[OLD.entry_id, NEW.entry_id];
    END IF;

    FOREACH affected_entry_id IN ARRAY affected_entry_ids LOOP
        IF affected_entry_id IS NOT NULL
           AND EXISTS (
                SELECT 1
                FROM competition.preparation_service AS service
                WHERE service.entry_id = affected_entry_id
                  AND service.lifecycle_status_code = 'active'
           )
           AND NOT EXISTS (
                SELECT 1
                FROM competition.entry_coffee_link AS link
                WHERE link.entry_id = affected_entry_id
                  AND link.linkage_status_code IN (
                      'SOURCE_DECLARED', 'REVIEWED_CONFIRMED'
                  )
           ) THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                CONSTRAINT = 'competition_service_coffee_identity_link_ck',
                MESSAGE = 'competition_service_coffee_identity_link_ck: active entry services require at least one source-declared or reviewed coffee link';
        END IF;
    END LOOP;

    RETURN NULL;
END;
$enforce_service_coffee_identity_link$;

CREATE CONSTRAINT TRIGGER competition_service_coffee_identity_link_ct
AFTER INSERT OR UPDATE ON competition.preparation_service
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION competition.enforce_service_coffee_identity_link();

CREATE CONSTRAINT TRIGGER competition_entry_coffee_link_reciprocal_ct
AFTER INSERT OR UPDATE OR DELETE ON competition.entry_coffee_link
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION competition.enforce_service_coffee_identity_link();

COMMENT ON TABLE competition.preparation_service IS
    'Effective professional record grain: series x edition x category x round x entry-or-lot x stable entry-service key. Judge observations and descriptors attach downstream and never multiply this row.';
COMMENT ON COLUMN competition.preparation_service.entry_service_key IS
    'Stable entry/lot-service identity used before legitimate round multiplication; repeated rounds reuse it and point to repeat_of_preparation_service_id.';
COMMENT ON COLUMN competition.preparation_service.black_coffee_core_candidate IS
    'Preparation-only candidate state. Later evidence, provenance, tier, rights, sensory-payload, duplicate, and gate checks are still mandatory before core credit.';
COMMENT ON COLUMN competition.preparation_service.source_native_roast_value IS
    'Explicit source-native roast value only. Category, preparation, origin, variety, and process inference are prohibited.';
COMMENT ON COLUMN competition.preparation_service.reviewed_c1_roast_category_id IS
    'Optional governed mapping to the current seven-level ordinal C1 scheme; the level spacing is not interval-scaled.';

COMMIT;
