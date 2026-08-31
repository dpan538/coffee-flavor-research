# Corpus artifact retention policy

This policy governs descriptor-corpus artifacts created after the accepted
20K, 30K, 40K, and 50K research checkpoints. It is a forward-looking storage
and reproducibility policy; it does not rewrite Git history or alter the
scientific status of an accepted snapshot.

## Historical checkpoints

The accepted 20K, 30K, 40K, and 50K manifests, public receipts, checksum
inventories, and restricted-ledger hashes are permanent reproducibility
records. Historical per-checkpoint scripts remain available when an accepted
snapshot depends on them, but they are legacy entry points rather than the
system used for new acquisition.

## Canonical current surfaces

At any time the public research package has one canonical current
source-assertion ledger and one canonical current cleaned-output-atom ledger.
Earlier full ledgers are immutable historical checkpoints, not competing
current surfaces. A current manifest names the active pair and records their
hashes, denominators, cleaner contract, and lineage.

Between accepted major snapshots, acquisition is stored as an isolated delta.
A delta contains public-safe IDs, hashes, cursors, state transitions, and
rights/evidence metadata; source-native text remains in the configured
owner-controlled restricted root. A new complete duplicate ledger is not
created merely because another 10,000-candidate boundary was crossed.

Full immutable snapshots are created only at an explicitly accepted major
milestone. Derived artifacts must be reproducible from the canonical ledgers,
the route manifests, and committed generators. Public Git artifacts contain
hashes, stable IDs, citations, and restricted pointers only, never restricted
source-native descriptor text.

## Acquisition implementation

New mining uses `db/scripts/descriptor-pipeline.py` and the source-route
manifests. Route state, adapter identity, exact cursor, retries, access and
robots decisions, failure taxonomy, artifact hashes, and route/semantic yield
are recorded in `db/data/acquisition-state/`. Historical acquisition programs
are retained only as `LEGACY_REPRODUCIBILITY_ENTRYPOINT` wrappers.

## Repository boundaries

Prior history is not rewritten. `git filter-repo`, rebases used to discard
accepted checkpoint history, and history squashing are prohibited for artifact
retention work. Git LFS is not introduced without separate owner
authorization. Model files are not corpus artifacts and remain prohibited in
this checkpoint because no model run is authorized.
