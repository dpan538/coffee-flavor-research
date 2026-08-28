# Descriptor assertion contract

## Observation identity

An effective professional coffee record remains one competition series x
edition x category x round x entry or lot x preparation service. Judges,
scores, descriptor rows, frequency values, and publication layers are
observations below that identity. They cannot create additional coffee records.

## Atomic assertion

A descriptor assertion is one source-supported sensory statement attached to
one effective record, artifact, bounded source field or passage, publication
layer, evidence-origin decision, rights decision, and review state. Raw field
text and atomic text may remain redacted from the public repository when reuse
rights are pending; their hashes and governed locators remain auditable.

The live public ledger uses this redacted path for all 140 assertions. Each row
has a 64-character source capture hash, a bounded record locator, a route-index
hash, and an explicit non-storage reason. `raw_field_text`,
`atomic_source_text`, source-native text, and normalized text remain absent from
the public ledger. The capture scope is
`WEB_INDEX_FIELD_CAPTURE_NOT_FULL_PAGE_BODY`.

Capture provenance is pinned to governed root
`restricted://coffee-flavor-round3m/round3m-2026-08-28t043000z` and manifest
SHA-256
`b36fbe8a959b099b1a3a073b045c3d6ac74e31043f090d2fd88bd78c3290e51d`.
Manifest identity and every capture's hash, byte size, URL inventory, and
timestamp inventory fail closed on drift. The governed locator is derived from
the validated manifest rather than accepted as a free-form caller claim.
Assertion route-index hash, hash scope, and non-storage reason must match the
governed artifact row.

The public contract distinguishes `STRICT_FLAVOR`, `BROAD_SENSORY`, and
`NON_DESCRIPTOR`. Rankings, scores without sensory text, awards, category
names, identities, bids, blank form labels, criteria, rules, and empty fields
are `NON_DESCRIPTOR`.

## Evidence and publication layers

Evidence tiers remain P0-P5 plus `UNRESOLVED`. Organizer hosting alone does not
make a field P2. Frequency-coded source terms remain unresolved P1 candidates
until their observer semantics are established.

Primary jury descriptions, generic organizer sensory fields, producer/farm
profiles, secondary sensory tables, judge-level observations, result metadata,
and protocols or blank forms remain separate publication layers. A secondary
table cannot silently double-credit a primary jury field.

## Review boundary

Codex decisions use machine-assisted or source-audited provisional actor types.
`HUMAN_CONFIRMED` and `EXPERT_ADJUDICATED` require an actual review receipt.
Round 3M does not impersonate a reviewer.

When review or rights receipts are superseded, the current pointer must name
the leaf receipt. A stale predecessor is excluded from the promoted universe
and fails deferred integrity validation.

The current queue contains 516 decisions: 376 Codex source-audit rejections of
non-descriptor AVPA category cells and 140 automated-parser assertions requiring
human review. The admitted ledger contains only the latter 140; none counts as
a reviewed descriptor or model-eligible assertion.
