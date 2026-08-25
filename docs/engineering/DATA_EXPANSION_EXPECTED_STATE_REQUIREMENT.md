# Data-expansion expected-state requirement

From Round 3G onward, every substantive data-expansion round must freeze an
expected-state contract before acquisition or import begins. The contract is a
governance control, not a quota for creating concepts, relationships or
promotions.

## Required sections

The human-readable and deterministic machine-readable forms must contain:

- `BASELINE`: verified semantic and data counts at the source checkpoint;
- `MINIMUM_EXPECTED`: the smallest evidentiary expansion needed to describe the
  round as successful expansion;
- `PREFERRED_EXPECTED`: soft goals that may fail without blocking closure;
- `OBSERVED`: the result measured from the completed implementation; and
- `DELTA`: the difference between the frozen baseline and observed result.

The baseline and minimum/preferred thresholds must be committed before the
first new source import. `OBSERVED` and `DELTA` may be filled later from
deterministic database or artifact validation.

## Revision rule

A threshold may not be revised after acquisition merely because it is hard to
reach. A valid revision requires a separate descriptive commit that records:

- the original and revised value;
- why the original threshold was invalid;
- the evidence establishing that invalidity; and
- the epistemic impact of the change.

The round must count threshold revisions. Unrecorded or post-hoc revisions are
integrity failures.

## Gate classes

Hard gates cover baseline preservation, rights, privacy, immutable file hashes,
source annotation, relationship provenance, review dispositions and prohibited
inferences. Any failed hard gate blocks promotion.

Minimum gates describe whether the declared acquisition and review scope was
actually completed. Preferred gates are non-binding. Promotion-count targets
must never be hard-coded: a defensible rejection or unresolved result is valid
research evidence.

Every round must return one explicit classification:

- `PASS`;
- `COMPLETE_WITH_EVIDENCE_GAP`;
- `BLOCKED_INTEGRITY`;
- `BLOCKED_RIGHTS`;
- `BLOCKED_PRIVACY`;
- `BLOCKED_REPRODUCIBILITY`; or
- `BLOCKED_REMOTE_CI`.

Final row count alone is never a success criterion. A gate must not pressure
reviewers to invent mappings, memberships, equivalences or promotions.

## Required evidence trail

Each round must preserve:

1. the pre-acquisition expected-state commit;
2. the source-candidate and rights/privacy review;
3. immutable snapshot and file hashes;
4. provenance-complete evidence and review decisions;
5. the generated expected-state result and delta;
6. negative tests for the round's prohibited shortcuts; and
7. local reproducibility plus remote CI receipts.

Round 3G's first implementation is
[`docs/research/coffee-sensory-kb-v0-round3g/01_DATA_EXPANSION_EXPECTED_STATE.md`](../research/coffee-sensory-kb-v0-round3g/01_DATA_EXPANSION_EXPECTED_STATE.md),
with the machine-readable contract in
[`db/data/round3g/expected_state.tsv`](../../db/data/round3g/expected_state.tsv).
