# Coffee Flavor Atlas / Coffee Sensory Knowledge Base

Coffee Flavor Atlas / 咖啡风味图谱 is a research-grounded sensory reference
system for people tasting coffee at home, in a café, or in another ordinary
drinking context. The intended product asks for preparation and roast context,
then asks one mandatory adaptive sensory question and up to four additional
questions only while useful uncertainty remains. It returns five primary and
three secondary flavor references compatible with the user's current
perception.

The system is meant to help someone name, refine, compare, and remember sensory
impressions. It is not a tasting exam, a coffee standard, or a system that
declares a person's perception wrong. Its candidates may help a user compare
their experience with roaster, store, or packaging tasting notes, but those
notes remain industry-language observations rather than objective flavor
labels.

The current repository contains the validated research and database foundation
through Round 3B plus the Round 3C calibration architecture and protocol
contract. The final consumer interaction, calibrated adaptive policy, and
candidate-ranking model have not been implemented or validated.

## Product contract

The current product semantics are frozen in the
[Product Contract V0](./docs/product/PRODUCT_CONTRACT_V0.md). At a conceptual
level, the intended interaction is:

```text
C0 mandatory preparation / beverage context (no unknown choice)
C1 mandatory seven-level roast context
Q1 mandatory context-adaptive question
Q2-Q4 conditional while additional discrimination is useful
Q5 exceptional maximum
↓
5 primary sensory candidates + 3 secondary candidates
```

Round 3B requires one of eight broad C0 preparation families and at least seven
ordered C1 roast categories, including distinct medium-light and medium-dark
positions. Database observations may still be unknown, not reported, not
applicable, or unresolved. These are project interaction constraints, not
universal coffee standards or proof of equal physical roast intervals. The
exact questions, prior strength, stopping thresholds, and consumer-to-sensory
ranking model remain empirical research questions. C0/C1 provide soft context
support; they do not directly generate flavor labels or hard-delete a
descriptor that is strongly supported by the user's answers.

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

## Validated foundation and Round 3C design

The PostgreSQL 17 foundation currently includes:

- 130 ontology concepts, including 92 active canonical sensory attributes;
- source-versioned provenance, rights policy, lifecycle status, and isolated
  source-specific concept schemes;
- 2,474 historical corpus documents and 6,818 parsed observations from a
  rights-reviewed pilot;
- 1,713 unique normalized industry-language expressions;
- deterministic exact, approved-variant, `pg_trgm`, and typed-graph retrieval;
- explicit abstention and `UNRESOLVED` behavior;
- preparation/roast context with source-scheme isolation, observation-level
  unknown states, additions, measured roast methods, conservative unresolved
  labels, and production-safe mandatory C0/seven-level C1 projections; and
- reproducible migrations and two-clean-rebuild validation.

Round 3C freezes the next calibration layer: signal separation, adaptive
question flow, a two-cohort study design, a versioned question bank, grouped
evaluation splits, ethics/privacy gates, and a public protocol-and-schema
release contract. It does not claim that a real Coffee Sensory Context
Calibration Dataset exists.

Round 2B retrieval results are **deterministic language-retrieval metrics**
against graded semantic judgments. They are not coffee flavor accuracy. See
the [Round 2B executive receipt](./docs/audits/coffee-sensory-kb-v0-round2b/00_EXECUTIVE_RECEIPT.md)
for the frozen inventory, metrics, rights decisions, and validation gates.

No `pgvector`, embedding, production LLM, automatic ontology promotion,
consumer ranking model, or database-to-frontend connection is required by the
validated baseline.

## Knowledge architecture

PostgreSQL is the canonical system of record. Its eight logical domains
preserve different kinds of claims:

- `ref`: controlled codes and semantics;
- `kb`: canonical concepts, lexicalizations, and governed relations;
- `evidence`: sources, rights, support, measurements, and projections;
- `corpus`: captured language observations and corpus-derived statistics;
- `context`: preparation, beverage-addition, and roast conditions;
- `calibration`: governed studies, protocols, samples, pseudonymous cohorts,
  question assignments, raw observations, analysis provenance, and releases;
- `ml`: versioned model runs, mapping candidates, and candidate signals; and
- `audit`: review, lifecycle history, validation, and explicit promotion.

The central boundary is:

```text
canonical knowledge
≠ preparation / roast context
≠ raw corpus observation
≠ calibration observation or derived reference distribution
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
- ordinary-user comprehension testing remains outstanding even though a
  held-out lexical normalization audit is now available;
- embeddings have not been benchmarked; and
- no calibrated adaptive-question or stopping policy has been validated;
- no independently collected ordinary-user question-response dataset exists;
- no replicated multi-family preparation-by-seven-level-roast sensory matrix
  exists; and
- no real public Coffee Sensory Context Calibration Dataset has been released.

These limits constrain generalization. They are not hidden by forcing weak
mappings or by describing retrieval scores as sensory probabilities.

## Current research direction

The immediate program is the ethics-gated physical collection handoff for the
selected incomplete-factorial pilot, followed by independent bilingual
ordinary-user comprehension and question-response calibration. Real data must
be lawfully collected before context priors, information gain, stopping, or
candidate ranking are estimated. An embedding benchmark follows only after
those foundations are stronger.

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
  [Round 3A](./docs/audits/coffee-sensory-kb-v0-round3a/00_EXECUTIVE_RECEIPT.md),
  and [Round 3B](./docs/audits/coffee-sensory-kb-v0-round3b/00_EXECUTIVE_RECEIPT.md)
- Adaptive calibration architecture:
  [architecture contract](./docs/architecture/ADAPTIVE_CONTEXT_QUESTION_ARCHITECTURE.md)
  and [Round 3 decision](./docs/decisions/ROUND3_CONTEXT_CALIBRATION_ARCHITECTURE_20260825.md)
- Calibration dataset and protocol contracts:
  [dataset specification](./docs/data/COFFEE_SENSORY_CONTEXT_CALIBRATION_DATASET_SPEC_V0.md)
  and [protocol](./docs/protocols/COFFEE_SENSORY_CONTEXT_CALIBRATION_PROTOCOL_V0.md)
- Current context research:
  [Round 3B synthesis](./docs/research/coffee-sensory-kb-v0-round3b/00_EXECUTIVE_SYNTHESIS.md)
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
