# Round 2A executive receipt

Date: 2026-08-24

Status: `PASS`

This receipt records the frozen, source-controlled ontology contract and the
observed results from two clean PostgreSQL 17 rebuilds.

## Scope outcome

Round 2A adds concept-level provenance, source-version-specific concept
schemes, a conservative canonical ontology seed, governed query views, and
semantic validation as forward migrations `008` through `011`. Migrations
`000` through `007` remain the immutable Round 1 history.

The frozen seed contains 130 concepts: 92 active sensory attributes, eight
candidate sensory attributes, 20 active project categories, one active
composite reference, six candidate qualifiers, one active and one candidate
process entity, and one candidate affective term. The 92 active sensory
attributes fall within the expected 90--120 range without promoting the eight
evidence-limited candidates.

All descriptions, canonical lexical mappings, canonical relations, and the
project V0 organizational projection are independently authored. No protected
source definition, reference preparation, intensity, score, full vocabulary,
or source hierarchy is included.

## Receipt

```text
PHASE_STATUS=PASS

SOURCE_SHA=26b014bd6fc4f87880e6e8f6a939a25cbbedb874
WORK_BRANCH=codex/coffee-sensory-kb-v0-round2a-ontology-20260824
FINAL_LOCAL_SHA=RECORDED_BY_FINAL_GIT_RECEIPT
FINAL_REMOTE_SHA=NOT_PUSHED
REMOTE_DIVERGENCE=RECORDED_BY_FINAL_GIT_RECEIPT
WORKTREE_CLEAN=RECORDED_BY_FINAL_GIT_RECEIPT

ROUND1_MIGRATIONS_MODIFIED=false
FORWARD_MIGRATION_COUNT=4
MIGRATION_PASS=true
CLEAN_REBUILD_COUNT=2
REPRODUCIBILITY_PASS=true

TOTAL_CONCEPTS=130
ACTIVE_SENSORY_ATTRIBUTES=92
CANDIDATE_SENSORY_ATTRIBUTES=8
ACTIVE_COMPOSITE_REFERENCES=1
CANDIDATE_COMPOSITE_REFERENCES=0
ACTIVE_QUALIFIERS=0
CANDIDATE_QUALIFIERS=6
ACTIVE_CATEGORIES=20

LEXICAL_EXPRESSION_COUNT=134
CANONICAL_RELATION_COUNT=100
SOURCE_SCHEME_COUNT=2

ACTIVE_EXTERNAL_CONCEPTS_WITHOUT_PROVENANCE=0
ACTIVE_EXTERNAL_RELATIONS_WITHOUT_PROVENANCE=0
ACTIVE_EXTERNAL_LEXICALIZATIONS_WITHOUT_PROVENANCE=0

ONTOLOGY_VALIDATION_PASS=true
SEMANTIC_VALIDATION_PASS=true
RIGHTS_REVIEW_PASS=true
QUERY_PLAN_PASS=true
REPOSITORY_TESTS_PASS=true

AUDIT_RECEIPT=docs/audits/coffee-sensory-kb-v0-round2a/00_EXECUTIVE_RECEIPT.md
KNOWN_BLOCKERS=none
ROUND2B_READY=true
NEXT_RECOMMENDED_PHASE=Round 2B rights-governed industry-language acquisition and unresolved-expression curation.
```

## Gate interpretation

The inventory values above were enforced by the seed transaction and repeated
in the Round 2A semantic contract. Both clean rebuilds produced the same
coverage and stable-key inventory. Repository type checks, nine Vitest tests,
the production build, nine Playwright smoke tests, harness syntax review, and
immutable-manifest checks passed. The 100 current canonical relations comprise
98 active `broader_than` relations, one active composite-component relation,
and one active consumer-reference relation. The database also retains eight
candidate and two deprecated historical relations, for 110 stored relation
rows. `ROUND2B_READY=true`; the final response supplies the commit SHA,
remote-divergence, and clean-worktree facts that cannot be embedded in the
commit that creates them.
