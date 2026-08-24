# Coffee Flavor Atlas / Coffee Sensory Knowledge Base

Coffee Flavor Atlas / 咖啡风味图谱 is a research-grounded sensory reference
system for people tasting coffee at home, in a café, or in another ordinary
drinking context. The intended product asks for preparation and roast context,
then uses about four low-burden sensory questions to return five primary and
three secondary flavor references compatible with the user's current
perception.

The system is meant to help someone name, refine, compare, and remember sensory
impressions. It is not a tasting exam, a coffee standard, or a system that
declares a person's perception wrong. Its candidates may help a user compare
their experience with roaster, store, or packaging tasting notes, but those
notes remain industry-language observations rather than objective flavor
labels.

The current repository contains the validated research and database foundation
through Round 3A, including governed preparation and roast context. The final
consumer interaction and ranking model have not yet been implemented or
validated.

## Product contract

The current product semantics are frozen in the
[Product Contract V0](./docs/product/PRODUCT_CONTRACT_V0.md). At a conceptual
level, the intended interaction is:

```text
C0 preparation / beverage context
C1 roast context
Q1 + Q2 + Q3 + Q4
optional adaptive Q5
↓
5 primary sensory candidates + 3 secondary candidates
```

Round 3A recommends eight broad C0 preparation families with conditional
subtypes and five coarse C1 roast labels plus explicit unknown. These are
research-backed project representations, not frozen UI controls or universal
coffee standards. The exact questions and consumer-to-sensory ranking model
remain research questions.

## Methodology

Scientific credibility in this project comes from evidence, explicit
semantics, evaluation, uncertainty handling, and reproducibility—not from the
mere use of AI or deep learning.

```text
coffee sensory science
        ↓
canonical sensory knowledge base
        ↓
industry-language observations
        ↓
deterministic normalization
        ↓
NLP / ML candidate retrieval
        ↓
evaluated ranking
        ↓
consumer sensory references
```

The [Methodology Overview](./docs/methodology/METHODOLOGY_OVERVIEW.md) explains
this architecture, its epistemic boundaries, and its present limitations. Any
future embedding or deep-learning layer must demonstrate measurable held-out
benefit over the deterministic baseline. Model output never silently becomes
canonical knowledge, and retrieval may explicitly return `UNRESOLVED`.

## Validated status through Round 3A

The PostgreSQL 17 foundation currently includes:

- 130 ontology concepts, including 92 active canonical sensory attributes;
- source-versioned provenance, rights policy, lifecycle status, and isolated
  source-specific concept schemes;
- 2,474 historical corpus documents and 6,818 parsed observations from a
  rights-reviewed pilot;
- 1,713 unique normalized industry-language expressions;
- deterministic exact, approved-variant, `pg_trgm`, and typed-graph retrieval;
- explicit abstention and `UNRESOLVED` behavior;
- preparation/roast context with source-scheme isolation, explicit unknown,
  additions, measured roast methods, and conservative unresolved labels; and
- reproducible migrations and two-clean-rebuild validation.

Round 2B retrieval results are **deterministic language-retrieval metrics**
against graded semantic judgments. They are not coffee flavor accuracy. See
the [Round 2B executive receipt](./docs/audits/coffee-sensory-kb-v0-round2b/00_EXECUTIVE_RECEIPT.md)
for the frozen inventory, metrics, rights decisions, and validation gates.

No `pgvector`, embedding, production LLM, automatic ontology promotion,
consumer ranking model, or database-to-frontend connection is required by the
validated baseline.

## Knowledge architecture

PostgreSQL is the canonical system of record. Its seven logical domains preserve
different kinds of claims:

- `ref`: controlled codes and semantics;
- `kb`: canonical concepts, lexicalizations, and governed relations;
- `evidence`: sources, rights, support, measurements, and projections;
- `corpus`: captured language observations and corpus-derived statistics;
- `context`: preparation, beverage-addition, and roast conditions;
- `ml`: versioned model runs, mapping candidates, and candidate signals; and
- `audit`: review, lifecycle history, validation, and explicit promotion.

The central boundary is:

```text
canonical knowledge
≠ preparation / roast context
≠ raw corpus observation
≠ model inference
≠ evaluation result
```

See the [Repository Architecture](./docs/ARCHITECTURE.md),
[database guide](./db/README.md), and
[database research architecture](./docs/research/coffee-sensory-kb-v0/01_V0_ARCHITECTURE.md)
for implementation details.

## Known limitations

The current foundation is deliberately incomplete:

- the Round 2B corpus is primarily one historical secondary source;
- the governed lexical bridge remains sparse and deterministic retrieval
  coverage is low;
- consumer-to-sensory-region ranking is not calibrated;
- the Round 2B corpus has zero structured preparation and roast coverage;
- the eight-family C0 and five-level C1 interaction have not yet been tested
  with ordinary users;
- embeddings have not been benchmarked; and
- no final four-to-five-question interaction has been validated.

These limits constrain generalization. They are not hidden by forcing weak
mappings or by describing retrieval scores as sensory probabilities.

## Current research direction

The next phase should freeze and import a rights-cleared context dataset,
validate C0/C1 comprehension and context-conditioned evaluation slices, and
continue multi-source corpus and lexical normalization work. An embedding
benchmark follows only after those foundations are stronger.

See the [Research Roadmap](./docs/research/RESEARCH_ROADMAP.md) for the ordered
program. No dates are implied by that sequence.

## Repository boundaries and local workflow

The repository still includes a static React Router + Vite public-baseline
interface backed by 24 project-curated TypeScript pilot descriptors. That UI
is a compatibility and interface prototype; its draft association ranges are
not canonical KB assertions or scientific measurements. It is not yet
connected to PostgreSQL.

```bash
npm ci
npm run format:check
npm run check
npm run test
npm run build
npm run test:smoke
```

Database migrations and destructive-test safeguards are documented in
[`db/README.md`](./db/README.md). Use only a disposable PostgreSQL 17+
database.

```bash
npm run db:migrate
npm run test:db
npm run test:db:repro
```

## Documentation map

- Current product semantics:
  [Product Contract V0](./docs/product/PRODUCT_CONTRACT_V0.md)
- Scientific and evaluation boundaries:
  [Methodology Overview](./docs/methodology/METHODOLOGY_OVERVIEW.md)
- Ordered research program:
  [Research Roadmap](./docs/research/RESEARCH_ROADMAP.md)
- Database structure:
  [Repository Architecture](./docs/ARCHITECTURE.md) and
  [KB V0 research documents](./docs/research/coffee-sensory-kb-v0/)
- Validated implementation evidence:
  [Round 1](./docs/audits/coffee-sensory-kb-v0-round1/00_EXECUTIVE_RECEIPT.md),
  [Round 2A](./docs/audits/coffee-sensory-kb-v0-round2a/00_EXECUTIVE_RECEIPT.md),
  [Round 2B](./docs/audits/coffee-sensory-kb-v0-round2b/00_EXECUTIVE_RECEIPT.md),
  and [Round 3A](./docs/audits/coffee-sensory-kb-v0-round3a/00_EXECUTIVE_RECEIPT.md)
- Current context research:
  [Round 3A synthesis](./docs/research/coffee-sensory-kb-v0-round3a/00_EXECUTIVE_SYNTHESIS.md)
- Frozen pre-V0 material:
  [legacy archive](./docs/archive/pre-sensory-kb-v0-20260824/README.md) and
  [archive manifest](./docs/archive/pre-sensory-kb-v0-20260824/MANIFEST.md)

Historical documents and audit receipts preserve the terminology and claims
that applied when they were written. Current product interpretation should
start with the Product Contract V0.

## Scientific, rights, and contribution boundaries

The project does not reproduce protected SCA, WCR, ISO, Cup of Excellence, or
commercial source content as its dataset. Public web access is not treated as
reuse permission. Restricted raw text is excluded from production-export
surfaces unless rights metadata affirmatively permit export.

See [License Scope](./docs/LICENSE-SCOPE.md),
[Third-Party Notices](./THIRD_PARTY_NOTICES.md), and
[Asset Licenses](./docs/ASSET-LICENSES.md). Cite the exact repository commit
used until a formal release exists. Contributions must follow
[CONTRIBUTING.md](./CONTRIBUTING.md) and include provenance for sensory,
translation, source, or rights claims.
