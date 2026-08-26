# Post-freeze versioning policy

## Immutable baseline

`coffee-sensory-research-db-v0.1.0` identifies one exact research database
state. Once its exact-main attestation and annotated tag exist, the following
must not change in place:

- frozen source snapshots and their file hashes;
- release-member rows and member hashes;
- the canonical inventory used by the release;
- the 11 inventory and manifest hashes;
- the freeze manifest;
- the eight approved v0.1.0 current-view definitions; and
- the release attestation, tag target, and tag object.

The tag is never moved or reused. The main branch is never force-pushed to
rewrite the release. `FROZEN` and `SUPERSEDED` release rows are terminal audit
records.

## Forward-change rule

Any future evidence, correction, rights-state change, schema extension, or
view-definition change requires all of the following:

1. a new forward migration; historical migrations remain byte-for-byte intact;
2. a new immutable source snapshot or a new derived artifact, with provenance
   back to its predecessor when applicable;
3. a new semantic release version and release-member inventory;
4. regenerated current-view definition hashes and all affected inventories;
5. a new freeze manifest whose limitations and exclusions describe the delta;
6. the full integrity, negative-test, two-rebuild, and remote-CI sequence; and
7. a new annotated tag on the exact promoted main SHA.

The earlier release remains queryable and reproducible after supersession.
Consumers must pin a release tag or exact SHA rather than treating unversioned
main as a stable dataset identity.

## Version meanings

| Version change                         | Appropriate use                                                                                                 | Examples                                                                                                                                           |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| New v0 minor release, such as `v0.2.0` | Additive evidence or governance-compatible schema/read-surface evolution before a declared stable 1.0 contract. | New rights-cleared corpora, a new relationship claim, additional source-authored languages, new context cells, or an additive current-view column. |
| New v0 patch release, such as `v0.1.1` | A narrowly scoped correction that still produces a complete new snapshot and does not silently mutate v0.1.0.   | Corrected provenance spelling, a fixed derived count, or removal of a row that was admitted in error.                                              |
| New major release, such as `v1.0.0`    | A breaking evidence contract or a separately authorized architecture/ontology decision.                         | Changed normalized-identity semantics, incompatible partition contracts, or an explicitly approved canonical redesign.                             |

A version label never converts the research database into ground truth. Model
training, adaptive-policy work, embeddings, human collection, or a canonical
redesign each requires its own authorized phase and cannot be smuggled into a
data-release patch.

## Corrections, contradictions, and rights changes

Errors are corrected prospectively. The new release records why the earlier
row is deprecated, quarantined, or superseded; it does not erase the historical
receipt. Contradictory relationship claims remain preserved with their original
direction and provenance rather than being overwritten by a later consensus.

If a source's rights or privacy status changes, public distribution follows the
new restriction immediately. A new release records the changed state and
excludes content as required, while the internal historical audit retains only
what continued legal and privacy obligations permit. Rights revocation is not
handled by pretending the earlier file never existed.

## Current-view evolution

The word `current` is release-scoped. A future release may approve new current
views and mark the v0.1.0 surfaces historical for new consumers, but it cannot
alter the definitions attested for v0.1.0. Compatibility views may be added by
forward migration when they preserve semantics; otherwise the new release must
document the breaking change explicitly.
