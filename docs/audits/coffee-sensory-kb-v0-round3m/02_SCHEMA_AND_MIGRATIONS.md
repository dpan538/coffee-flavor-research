# Schema and migrations audit

Round 3M uses forward-only migrations after the 55-migration Round 3L baseline.
Previously applied migrations are not edited.

The last valid contiguous working-tree sequence before draft 059 comprised:

- `055_round3m_descriptor_provenance_review_rights.sql`;
- `056_round3m_descriptor_gate_contract.sql`;
- `057_round3m_release_contract_hardening.sql`.

The working tree also contains draft
`059_round3m_normalization_challenge_contract.sql`. It is not part of a valid
migration plan while 058 is absent. The plan fails closed before database work,
and no final forward-migration count is claimed pending the explicit 058
decision.

The missing migration is also a semantic P0, not merely a numbering gap. Draft
059 alone permits caller-chosen reviewer identity, human-event/evidence hashes,
and locators without foreign-key and verified-hash binding to an acquired
review artifact. Its transaction-local positive fixture's `+1` is structural
test data, not authoritative human or qualified-human challenge credit.
Approved 058 must provide immutable, dated reviewer qualification/admission and
acquired reviewer-decision evidence binding; 059 must then be wired to those
rows before challenge credit is releasable.

Release audit work initially drafted the last hardening changes by modifying
already-applied migrations 055 and 056. The forward-only fingerprint audit
caught that error before finalization. Both files were restored byte-for-byte
to their checkpoint versions, and the review-supersession, lineage, gate-parity,
and secondary-publication changes were moved into migration 057. No applied
migration history was rewritten.

The new schema supports source routes, source schema signatures, governed
source artifacts, descriptor assertions, publication layers, evidence-origin
decisions, purpose-specific rights, review receipts, candidate dispositions,
repeat/mirror groups, analyst-time logs, versioned descriptor gates, and future
saturation increments.

Natural keys and unique constraints support idempotent artifact import. A
rejected non-descriptor candidate is kept in candidate/review staging and
cannot violate the admitted ledger's exactly-one-effective-record rule or enter
descriptor gate views.

Deferred integrity checks require the current review/rights pointer to be the
leaf of its supersession chain and require assertion artifact hashes,
route-index hash, hash scope, and non-storage reason to match the governed
source artifact. Secondary publication rows remain structurally representable
as review-only evidence but cannot use a canonical counting disposition or
demote primary credit.

Gate artifact validation compares the generated 56-row TSV with the
authoritative SQL contract field by field. Per-label and multi-target views
apply the same current-leaf review-receipt rule as the reviewed descriptor
universe.

The loader validates all machine outputs before import, then imports 11
independent families, 135 route rows (131 census routes plus 4 live schema
routes), 4 schema signatures, 8 source-artifact bridges, 8 effective-record
bridges, 516 queue items, 516 provisional decisions, 3,096 purpose-specific
rights decisions, 140 admitted assertions, 508 co-assertion events, and the
analyst-time row. Repeating the import is idempotent.

Focused PostgreSQL 17 probe 10 compiled migrations 000-057 plus draft 059 and
passed 68 of 68 global validations: 49 pre-v059 plus the exact 19-check v059
delta. Its focused normalization test and full Round 3M gate-schema test both
exited 0. These checks validate the draft's internal structure only; they do not
prove an acquired review event or qualified reviewer. That probe is not a
contiguous current-tree migration/CI run. Final positive, negative, policy,
invariant, and two-clean-rebuild counts remain unclaimed until the approved
evidence-binding migration sequence and full CI are complete.
