# Coffee Sensory Knowledge Base V0 database

> **Destructive-operation warning:** never point these scripts at a production
> database, a database containing user data, or any database that is not
> disposable. `apply.sh` changes the selected database. `rebuild-twice.sh`
> creates and then drops two named databases. It refuses to run without an
> explicit destructive-operation opt-in and refuses to replace a database that
> already exists, but the caller remains responsible for selecting the correct
> PostgreSQL server and admin database.

This directory is the directly executable PostgreSQL foundation for Coffee
Sensory Knowledge Base V0. It is a research and interface substrate, not a
coffee standard, a scientific claim about permanent descriptor intensity, or a
copy of a proprietary flavor wheel.

## Requirements

- PostgreSQL server **17 or newer** and matching PostgreSQL client tools.
- `psql`, `createdb`, `dropdb`, and `pg_dump` on `PATH`.
- The PostgreSQL `pg_trgm` extension available to the target server.
- A role allowed to create `pg_trgm` and the seven logical schemas when applying
  migrations. The reproducibility script additionally needs `CREATEDB`.
- `sha256sum` or `shasum` for reproducibility hashes.

`pg_trgm` is required and migration `000` enables it. `pgvector` is not used or
required:

```text
PGVECTOR_REQUIRED=false
```

Use standard libpq connection settings such as `PGHOST`, `PGPORT`, `PGUSER`,
and `PGDATABASE`. The scripts never contain or print a password. Prefer a
properly permissioned `.pgpass`; a CI system may supply its normal libpq secret
environment independently of these scripts.

## Migration and domain layout

Top-level migrations are applied in contiguous numeric order. The first eight
are protected by `db/migration-baselines/round1.sha256`, all twelve Round 1
plus Round 2A migrations are protected by
`db/migration-baselines/round2a.sha256`, and all eighteen migrations through
Round 2B are protected by `db/migration-baselines/round2b.sha256`. The
migration planner refuses to run if any immutable boundary changes:

```text
000_extensions.sql
001_reference_and_schemas.sql
002_core_schema.sql
003_evidence_corpus_ml_audit.sql
004_constraints_and_triggers.sql
005_indexes_and_views.sql
006_reference_seed.sql
007_validation_queries.sql
008_concept_provenance.sql
009_concept_schemes.sql
010_canonical_ontology_seed.sql
011_ontology_validation.sql
012_round2b_corpus_governance.sql
013_round2b_normalization_statistics.sql
014_round2b_retrieval_and_audit.sql
015_round2b_pilot_seed.sql
016_round2b_evaluation_seed.sql
017_round2b_resolution_feedback_validation.sql
018_context_schema.sql
019_context_integrity.sql
020_context_taxonomy_seed.sql
021_context_views_validation.sql
```

`apply.sh` fails unless there is exactly one migration at every contiguous
numeric position. The order separates extension setup, controlled reference
values and namespaces, canonical knowledge, evidence and observation domains,
invariants, retrieval surfaces, the Round 1 smoke seed, baseline validation,
concept provenance, source-local schemes, the curated ontology seed, and
ontology validation.

The Round 2B forward layer adds rights-reviewed source decisions, immutable
corpus snapshots, duplicate and history governance, versioned Unicode phrase
normalization, occurrence/frequency/NPMI statistics, deterministic A--D
retrieval, typed one-hop graph expansion, explicit abstention, and graded
development/held-out audit structures. The final forward migrations persist
the frozen audit, four baseline runs and DB-native metrics, then materialize
the conservative exact-resolution boundary, ontology-feedback queue and
expected-zero validation contract. Historical migrations are never rewritten
to accommodate corpus data.

The Round 3A forward layer adds preparation polyhierarchy, preparation and
roast expressions, source-specific roast schemes, one conservative project
roast projection, explicit unknown/unresolved observation states, beverage
additions, roast measurement methods, context provenance, and context coverage
and validation views. It adds no sensory coefficients and does not modify the
ontology or frozen corpus.

The seven PostgreSQL schemas have deliberately separate responsibilities:

- `ref`: controlled codes and their semantics.
- `kb`: language-neutral canonical concepts, multilingual expressions,
  lexicalizations, typed relations, and sensory measurement constructs.
- `evidence`: sources, rights policy, datasets, support, empirical
  measurements, projections, and reference calibrations.
- `corpus`: captured industry language, raw observations, resolutions, and
  corpus-derived co-occurrence measurements.
- `context`: preparation, serving additions, roast labels/schemes, measured
  roast conditions, and observation context.
- `ml`: versioned models, runs, mapping candidates, and candidate signals.
- `audit`: independent reviews, lifecycle history, explicit promotions, and
  database validation.

The seed in `006_reference_seed.sql` is independently authored, lawful, and
test-only. It exists to exercise semantic distinctions such as pink grapefruit,
Earl Grey, bright, fermented, and the intentionally unresolved “meteor fruit.”
The forward seed in `010_canonical_ontology_seed.sql` populates the reviewed V0
ontology without copying WCR, SCA, ISO, journal definitions, reference
preparations, intensities, Flavor Wheel placement, or commercial source text.

## Apply and test one disposable database

Create the empty database yourself, verify the server target, and then run:

```bash
PGHOST=localhost \
PGPORT=5432 \
PGUSER=coffee_kb_dev \
PGDATABASE=coffee_sensory_kb_v0_manual \
./db/scripts/apply.sh

PGHOST=localhost \
PGPORT=5432 \
PGUSER=coffee_kb_dev \
PGDATABASE=coffee_sensory_kb_v0_manual \
./db/scripts/test.sh
```

A database name can instead be passed as the sole positional argument. Both
scripts require either that explicit argument or `PGDATABASE`; they refuse
libpq's implicit database-name default. All `psql` calls use `-X` and
`ON_ERROR_STOP`, so user startup files cannot alter behavior and SQL errors stop
the run.

`test.sh` executes, in order:

1. the `audit.run_validation_queries()` contract created by migration `007`,
   failing if any check reports a violation;
2. the Round 1 negative, semantic, retrieval, and query-plan suites;
3. when Round 2A migrations are present, the
   `audit.run_round2a_validation_queries()` contract; and
4. the Round 2A negative, semantic, retrieval, and query-plan suites;
5. when Round 2B migrations are present, the Round 2B negative, semantic,
   retrieval, and query-plan suites; and
6. after the final Round 2B validation migration, the
   `audit.run_round2b_validation_queries()` expected-zero contract;
7. when Round 3A is present, the
   `audit.run_round3a_validation_queries()` expected-zero contract and Round
   3A negative, semantic, context-retrieval, and query-plan suites.

## Two clean rebuilds

The reproducibility runner uses `PGDATABASE` as the optional **admin
connection database**, defaulting to `postgres`. Its two target databases come
from `COFFEE_KB_REBUILD_DB_ONE` and `COFFEE_KB_REBUILD_DB_TWO`, with safe
defaults. Target names must be distinct, at most 63 bytes, and match exactly:

```text
^coffee_sensory_kb_v0_[a-z0-9_]+$
```

The runner refuses to overwrite either target if it already exists. It also
refuses to start unless the destructive-operation flag is exactly `1`:

```bash
COFFEE_KB_ALLOW_DATABASE_DROP=1 \
PGHOST=localhost \
PGPORT=5432 \
PGUSER=coffee_kb_admin \
PGDATABASE=postgres \
COFFEE_KB_REBUILD_DB_ONE=coffee_sensory_kb_v0_check_one \
COFFEE_KB_REBUILD_DB_TWO=coffee_sensory_kb_v0_check_two \
./db/scripts/rebuild-twice.sh
```

On both fresh databases it applies all migrations, runs the complete test
suite, and captures artifacts in a directory created by `mktemp`. It prints the
artifact directory, PostgreSQL and `pg_trgm` versions, hashes, inventories,
reference row counts, source-version inventory, and validation counts. It then
compares:

- the per-file migration hash manifest;
- the ordered hash manifest for every migration whose name contains `seed`;
- a normalized schema-only dump hash (PostgreSQL 17's randomized `\\restrict`
  and `\\unrestrict` lines are removed);
- all stable `*_key` and controlled `*_code` values;
- every `ref` table's row count;
- source-version and license-policy keys;
- ordered Round 1, Round 2A, Round 2B, and Round 3A validation result counts;
- the ordered ontology coverage metrics;
- source-policy, snapshot, retention, normalization, and statistic-run
  receipts; and
- frozen audit-split, deterministic A--D run, candidate-count, and retrieval
  metric values when Round 2B is present; and
- preparation, roast, unresolved-context, coverage, and measurement-method
  inventory when Round 3A is present.

Only stable logical values are inventoried. Identity IDs and sequence state
advanced by deliberately failing negative tests are excluded. Both databases
that this invocation created are dropped by the exit cleanup, including after
a test or comparison failure. Temporary artifacts remain at the printed path
for audit inspection.

## Frontend isolation

These scripts use only PostgreSQL command-line tools and SQL files under `db/`.
They do not invoke npm, TypeScript, Vite, React, or application code, and no
application package is a hidden migration dependency. The current static
TypeScript frontend continues to import its public descriptor data from
`packages/flavor-data`; this V0 database is not silently wired into frontend
runtime behavior in this round.
