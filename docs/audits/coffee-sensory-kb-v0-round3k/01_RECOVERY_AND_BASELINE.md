# Recovery and baseline audit

## Frozen references

- frozen `origin/main`: `c3ae9b880d85507a0b8b0298bb94ef013d02f928`;
- failed Round 3J branch: `a92b448043e8dad468339b3ca2cdfd2b7f6aa772`;
- Round 3K work branch:
  `codex/coffee-sensory-kb-v0-round3k-professional-competition-corpus-20260827`.

The branch was created in an isolated worktree. The user's original dirty main
worktree is outside the Round 3K edit path and must remain untouched. The failed
branch is preserved as failure evidence and is not merged.

## Round 3J diagnosis

Round 3J used the wrong population and grain: four ready-to-drink reviews and
two consumer sensory studies produced 37 occurrences constrained to unresolved.
Those documents are not professional competition records and do not enter the
Round 3K corpus.

The db/049 dependency audit retained its useful semantics—source-family
identity, rights and privacy decisions, acquisition audit, duplicate/repeat
governance, grouped splits, readiness gates, and model-run prohibition—but not
its exact code. Exact reuse would retain failed-branch checkpoints, obsolete
scale lanes, deprecated views, missing competition grain, and incomplete rights
dimensions. Round 3K therefore uses forward migrations 049-052.

The Round 3J db/050 active role is superseded. Its forced-unresolved mapping
contract is not reused, and the failed-branch file remains available as history.

## Checkpoint controls

The 000-048 migration baseline is fingerprinted before forward migration. Phase
A governance checkpoint `6e0279e75622f59341cef5464940c385381c82c7` was pushed,
and remote CI run
[33070396341](https://github.com/dpan538/coffee-flavor-research/actions/runs/33070396341)
was green before Phase B began. Phase B implementation checkpoint
`f48fde33128dc90c46ef18f08a46702163afc98f` and validated source-audit checkpoint
`ab7c886f0ea3d3a59709a618c148f82fe892d927` remain on the feature branch; main
is unchanged at the frozen source SHA.
