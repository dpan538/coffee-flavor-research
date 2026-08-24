# Dataset import and frozen snapshot

Snapshot `context.snapshot.round3b_v1` contains 4,817 normalized raw-context
records derived without discarding the source payload. Its SHA-256 is
`aca93ed92f0c032f81709bc35d3db102a10bfdddf684c09765228ee1a5481355`.
It records the source versions, six file hashes, normalization version
`context_normalization_v1`, code checkpoint
`6e2aa59d407982e77f05d5df539348719490f179`, creation timestamp, split seed,
case count, held-out count, and stratification description.

The import keeps `raw_preparation_label`, `raw_roast_label`, source file and
row locators, observation state, normalized family/leaf/category references,
black/milk mode, outcome type, addition exclusion, and a JSON source payload.
Normalization never overwrites the raw fields. Triggers require normalized
preparation leaves to descend from their selected family and normalized roast
categories to belong to the current project scheme.

The snapshot and all 4,817 raw rows become immutable when `is_frozen` is set.
The benchmark was deterministically split before the evaluation script read
the held-out labels. The split seed is
`coffee-context-round3b-heldout-v1-20260825`; 17 of 102 cases are held out,
stratified by domain and authored semantic stratum.
