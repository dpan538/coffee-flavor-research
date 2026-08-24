# 07 — Known Gaps and Phase Boundary

Receipt date: 2026-08-24

## Intentionally unresolved research questions

Round 1 does not invent answers for:

- universal coffee perceptual distance or stable cross-cultural sensory
  geometry;
- numeric decompositions of `bright`, `clean`, or `juicy`;
- a universal similarity threshold or embedding/rule fusion coefficient;
- the final four or five consumer questions;
- a consumer-to-region ranking or personalization model;
- roaster-note “accuracy”;
- embedding model selection, fine-tuning, vector storage, or `pgvector`;
- large-scale corpus acquisition or LLM normalization.

The schema can retain later, source-identified evidence for these questions,
but neither the seed nor the retrieval prototype represents a scientific
answer.

## Deliberate product boundary

The PostgreSQL KB is not wired into the static React application in this
round. `packages/flavor-data` remains runtime-referenced compatibility data and
is explicitly non-canonical. A later integration must define a stable,
rights-filtered export or service contract before replacing those imports.

No questionnaire UI, frontend redesign, scraper, embedding pipeline, model
training, login, API server, recommendation engine, or personalization work was
started.

## Seed and evidence limitations

- The 19-concept seed is a semantic fixture, not the target ontology.
- Chinese is supported through the `zh-Hans` language registry but no Chinese
  lexical data is asserted yet.
- Seed relations are independently authored test assertions and are not
  presented as universal perceptual findings.
- No empirical sample, panel, laboratory, or population dataset is included.
- The external Deep Research PDF referenced by the request was not physically
  attached, so it was recorded as absent rather than copied or reconstructed.
- `pgvector` is intentionally absent and not required.

## Engineering caveats recorded, not hidden

- The host has PostgreSQL 16.13, not the required baseline. Validation used an
  isolated official PostgreSQL 17.11 container; the host cluster was left
  untouched.
- The available Node runtime was 22.21.0 while React Router printed a
  recommendation for 22.22.0 or newer. Typecheck, unit tests, production build,
  and all nine Playwright smoke tests still passed; this warning is not a
  database blocker, but CI/toolchain maintenance should update Node.
- Lifecycle-active hierarchy and support obligations are conservative: they do
  not reinterpret relation validity timestamps. An expired relation that still
  has lifecycle `active` retains provenance and acyclicity obligations until a
  governed lifecycle change.
- Promotion eligibility checks lifecycle-active status at event write. Later
  target lifecycle changes do not invalidate historical promotion records.
- Not every boolean property in every controlled-code registry is frozen by a
  reciprocal trigger. Administrative semantic changes must be migration-
  reviewed; the rights-filtered view re-evaluates current access/rights flags,
  and the expected-zero suite detects resulting invariant violations.
- The branch was not pushed. Remote CI has therefore not run these commits;
  local PostgreSQL 17 and repository gates are the recorded evidence.

## Next phase gate

The recommended next phase is rights-reviewed corpus/NLP acquisition and
ontology curation: expand toward the planned 90–120 active concepts, add
reviewed multilingual expressions, preserve unresolved terms, and attach every
external assertion to a licensed source version. Embeddings, consumer scoring,
and frontend integration remain later decisions.
