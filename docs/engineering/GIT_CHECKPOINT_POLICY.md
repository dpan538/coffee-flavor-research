# Git checkpoint and remote backup policy

This policy applies to all future Codex research and engineering rounds in this
repository. It exists because the validated Coffee Sensory KB Rounds 1, 2A,
and 2B accumulated as local-only commits before a remote backup checkpoint was
created.

## Descriptive commits are mandatory

Use small, logical commits with descriptive Conventional-Commit-style messages
where practical. Good examples include:

```text
db: add concept provenance enforcement
data: curate canonical coffee sensory core
corpus: import firstbloom pilot snapshot
nlp: add deterministic trigram candidate retrieval
test: add semantic abstention audit cases
docs: add round3 embedding benchmark receipt
```

Avoid vague messages such as `update`, `fix`, `changes`, `work`, `final`, or
`misc`.

## Commit descriptions must explain why

For substantive changes, include a commit body that records:

```text
What changed
Why it changed
Research/governance implication
Validation performed
```

For example:

```text
nlp: add graph-expanded lexical candidates

Add typed graph expansion after deterministic lexical and trigram
candidate generation.

This preserves the Round 1–2B distinction between lexical similarity
and canonical ontology relations while improving candidate coverage
without introducing embeddings.

Validation:
- SQL retrieval suite
- semantic smoke tests
- held-out baseline unchanged until next benchmark
```

## Regular remote backup is mandatory

During active Codex work, commit and push the current feature branch after every
meaningful coherent checkpoint. Do not leave multiple hours or multiple major
phases of validated work only in a local or `/private/tmp` worktree.

The practical default is:

> Push after every completed phase or every 1–3 substantive logical commits,
> whichever occurs first.

Do not create artificial empty commits merely to satisfy this cadence.

## Feature branch first, main after gates

Experimental work belongs on `codex/<descriptive-round-name>` or the
repository's established feature-branch convention. During a round, use:

```text
feature branch
→ descriptive commits
→ regular remote pushes
```

Do not continuously push experimental or partial states directly to `main`.

## Main represents validated checkpoints

Promote a round to `main` only when it reports:

```text
PHASE_STATUS=PASS
WORKTREE_CLEAN=true
required validation gates=true
reproducibility gate=true where applicable
KNOWN_BLOCKERS=none
```

Immediately before promotion:

```text
fetch origin
verify no divergence
promote the validated SHA to main
push main
```

Prefer fast-forward integration when history is already linear. Never force
push `main`.

## Preserve round receipts

Every significant research or engineering round must commit an audit receipt
before promotion to `main` at:

```text
docs/audits/<round-name>/00_EXECUTIVE_RECEIPT.md
```

The receipt should record:

```text
SOURCE_SHA
FINAL_LOCAL_SHA
FINAL_REMOTE_SHA
branch
database/tool versions where relevant
validation gates
known blockers
next phase
```

## Tags for major milestones

Use annotated milestone tags for major stable checkpoints, not every commit.
Examples include:

```text
coffee-sensory-kb-v0-round2b
coffee-sensory-kb-v0-nlp-baseline
coffee-sensory-kb-v0-embedding-benchmark
coffee-sensory-kb-v1-data-freeze
```

Do not move an existing milestone tag. If a tag name already resolves to a
different object, stop and investigate.

## Temporary paths are never the only evidence location

Paths such as `/private/tmp/...` are working locations only. Every final audit
receipt, source matrix, migration, seed, benchmark result, and governance
document must exist in committed repository history.

## Dirty-worktree protection

Never reset, clean, stash, overwrite, or commit another user's dirty worktree
as part of a checkpoint operation. Use a separate clean worktree based on the
latest intended source commit. After remote `main` advances, future work must
start from a clean worktree based on the latest `origin/main`, not a stale dirty
checkout.
