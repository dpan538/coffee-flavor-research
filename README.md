# Coffee Flavor Atlas / Coffee Sensory Knowledge Base

Coffee Flavor Atlas / 咖啡风味图谱 is a research project about coffee sensory
language. The repository now has two deliberately separate layers:

- a static React Router + Vite public-baseline interface with 24 project-curated
  pilot descriptors; and
- the current PostgreSQL-backed Coffee Sensory Knowledge Base V0 research
  substrate under [`db/`](./db/).

The PostgreSQL model is the canonical architecture for future knowledge, NLP,
corpus, and evaluation work. The existing TypeScript descriptor data remains a
compatibility dependency of the static interface only. Its draft association
ranges are not scientific measurements, official cupping values, or canonical
KB assertions.

## Current research architecture

KB V0 separates language-neutral concepts, multilingual lexical expressions,
typed polyhierarchical relations, source and rights evidence, raw corpus
observations, model inference, independent review, and explicit promotion.
PostgreSQL 17+ is the system of record, `pg_trgm` is the only required
extension, and `pgvector` is not a V0 dependency.

Start with:

- [`docs/research/coffee-sensory-kb-v0/00_RESEARCH_SOURCE.md`](./docs/research/coffee-sensory-kb-v0/00_RESEARCH_SOURCE.md)
- [`docs/research/coffee-sensory-kb-v0/01_V0_ARCHITECTURE.md`](./docs/research/coffee-sensory-kb-v0/01_V0_ARCHITECTURE.md)
- [`docs/research/coffee-sensory-kb-v0/02_DATABASE_INVARIANTS.md`](./docs/research/coffee-sensory-kb-v0/02_DATABASE_INVARIANTS.md)
- [`docs/research/coffee-sensory-kb-v0/03_ENGINEERING_DECISIONS.md`](./docs/research/coffee-sensory-kb-v0/03_ENGINEERING_DECISIONS.md)
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)

The external Deep Research PDF named by the engineering brief was not present
in the workspace and has not been fabricated or copied. The supplied Round 1
brief is recorded as the engineering contract. Test results, rather than these
documents, determine whether an implementation gate passes.

## Database workflow

The migrations are ordered, directly executable through `psql`, and isolated
from the frontend runtime:

```text
db/000_extensions.sql
db/001_reference_and_schemas.sql
db/002_core_schema.sql
db/003_evidence_corpus_ml_audit.sql
db/004_constraints_and_triggers.sql
db/005_indexes_and_views.sql
db/006_reference_seed.sql
db/007_validation_queries.sql
db/008_concept_provenance.sql
db/009_concept_schemes.sql
db/010_canonical_ontology_seed.sql
db/011_ontology_validation.sql
```

Migrations `000` through `007` are the immutable Round 1 baseline. Round 2A is
forward-only: it adds controlled concept-provenance roles, isolated
source-specific schemes, the curated canonical ontology, and ontology-specific
views and validation.

Use only a disposable PostgreSQL 17+ database. The database README documents
the required environment and destructive-test safeguards:
[`db/README.md`](./db/README.md).

```bash
npm run db:migrate
npm run test:db
npm run test:db:repro
```

Round 1 evidence is recorded under
[`docs/audits/coffee-sensory-kb-v0-round1/`](./docs/audits/coffee-sensory-kb-v0-round1/).
Round 2A ontology, provenance, rights, query-plan, and reproducibility evidence
is recorded under
[`docs/audits/coffee-sensory-kb-v0-round2a/`](./docs/audits/coffee-sensory-kb-v0-round2a/).

## Static public baseline

The frontend remains a vocabulary and interface prototype, not a coffee
standard, ecommerce site, formal cupping system, or sample database. It keeps
search, category filtering, Atlas views, descriptor details, comparison,
methodology, and bilingual pilot labels available while later data integration
is designed separately.

```bash
npm ci
npm run dev
```

Other frontend checks:

```bash
npm run format:check
npm run check
npm run test
npm run build
npm run test:smoke
```

Application code imports descriptor/category/source data only from
`packages/flavor-data`. Do not copy that pilot dataset into `app/` or promote it
into PostgreSQL as canonical knowledge.

## Repository map

```text
app/                         Static React Router application
packages/flavor-data/src/    Runtime-referenced pilot descriptor model
db/                          PostgreSQL KB migrations and executable tests
docs/research/               Current KB V0 research architecture
docs/audits/                 Evidence-backed implementation receipts
docs/archive/                Frozen pre-KB product and design material
tests/                       Vitest and Playwright frontend tests
```

The archived 2026-06-22 product baseline remains available at
[`docs/archive/pre-sensory-kb-v0-20260824/`](./docs/archive/pre-sensory-kb-v0-20260824/).
Archival status preserves traceability; it does not imply every earlier idea
was wrong.

## Scientific and rights boundaries

- Concepts are language-neutral; display labels are lexical records, not IDs.
- A concept is not restricted to one universal Flavor Wheel family.
- Descriptor identity has no intrinsic permanent intensity or universal
  coordinate.
- Perceptual, linguistic, corpus, structural, model, and governance signals
  remain distinct.
- Retrieval may return `UNRESOLVED`; nearest-neighbour classification is never
  forced.
- Model output never silently becomes canonical knowledge.
- Restricted raw text is excluded from production-export views unless rights
  metadata affirmatively permits export.
- The project does not reproduce protected SCA, WCR, ISO, Cup of Excellence,
  or commercial source content as its dataset.

See [`docs/LICENSE-SCOPE.md`](./docs/LICENSE-SCOPE.md),
[`THIRD_PARTY_NOTICES.md`](./THIRD_PARTY_NOTICES.md), and
[`docs/ASSET-LICENSES.md`](./docs/ASSET-LICENSES.md) for the layered rights
policy.

## Citation and contribution

[`CITATION.cff`](./CITATION.cff) is the repository citation metadata. Cite the
exact commit used until a formal version and release exist. Contributions must
follow [`CONTRIBUTING.md`](./CONTRIBUTING.md) and include provenance for any
sensory, translation, source, or rights claim.
