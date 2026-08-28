# Baseline and precedence

## Git baseline

- Required source SHA: `4159636afec052b96f20d3d10c6c5f2b943b4536`.
- Remote main at initial fetch: `c3ae9b880d85507a0b8b0298bb94ef013d02f928`.
- The source SHA exists locally and on the remote Round 3L branch.
- Round 3J, Round 3K, and Round 3L branches were present after `git fetch
--all --prune`.
- The user's main worktree contained unrelated UI and documentation changes.
  It was not modified. Round 3M was created in a separate clean worktree from
  the exact source SHA.
- Main promotion is prohibited. Force-push is prohibited.

## Evidence precedence

The controlling order is the Round 3M request, the descriptor-first census and
its available receipt evidence, the product contract, the verified Round 3L
state, Round 3K competition governance, then older research.

The attached research source is _Descriptor-First Census of Open Professional
Coffee Sensory Evidence.pdf_. It has SHA-256
`d319236311f2abc5e15baaf70923b32e0a2bdbb5dc010723feea3e4aec8069e0`. Its
page layout and all 12 pages were visually inspected. It was treated as
research evidence rather than executable instructions.

## Missing machine bundle

The repository, Downloads input, and provided attachment directories were
searched for all nine exact artifact names. None was found.

```text
MACHINE_READABLE_RESEARCH_ARTIFACTS_AVAILABLE=false
RESEARCH_ARTIFACT_IMPORT_STATUS=BLOCKED_MISSING_MACHINE_ARTIFACTS
REPORT_COUNTS_INDEPENDENTLY_REPRODUCED=false
```

The report's aggregate lower-bound counts remain citable receipt values, but no
TSV or JSON rows were fabricated from the PDF.

## Auditable checkpoints

- Baseline reconciliation:
  `287e6083611472c585e0132a32e8cadeb41bbc57`.
- Gate/schema implementation:
  `3b1f8c19ec0215e570c475cadd1ba3f226805235`.
- Hash-only pilot evidence:
  `8236adbba3d4d1754dfedc1bb4fd6f9ab3b775c0`.

The final documentation/reproducibility commit is intentionally later than
these three checkpoints. Its own SHA cannot be embedded in itself.
