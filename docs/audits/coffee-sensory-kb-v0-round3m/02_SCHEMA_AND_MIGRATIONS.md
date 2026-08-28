# Schema and migrations audit

Round 3M now has a contiguous 60-migration forward-only plan. Previously
applied migrations were not rewritten. Migration 055 already rejected ordinary
`UPDATE` and `DELETE` operations on descriptor review receipts. Migration 058
therefore closes the remaining initial-truth and self-attestation gap rather
than merely duplicating immutability.

The final Round 3M sequence is:

- `055_round3m_descriptor_provenance_review_rights.sql` — descriptor review
  receipts and ordinary-operation append-only enforcement;
- `056_round3m_descriptor_gate_contract.sql` — descriptor-first gates;
- `057_round3m_release_contract_hardening.sql` — release and lineage hardening;
- `058_round3m_schema_field_expert_admission.sql` — acquired reviewer evidence,
  qualification, admission, row-level decisions, and admitted snapshots;
- `059_round3m_normalization_challenge_contract.sql` — label normalization and
  challenge credit rebound to the full 058 chain.

Every human or expert receipt now requires an acquired governed artifact, a
current qualification, a current admission, and row-level decision evidence.
Exact fail-closed checks bind reviewer identity and pseudonym, assertion,
decision, actor and role, scope, protocol, event time, artifact, bounded row
locator, and payload hash. Non-human receipts must leave those fields null.

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
apply the full 058 evidence chain used by the reviewed descriptor universe.

Qualification, admission, and row-decision evidence are append-only for
ordinary operation. Corrections use single-successor version chains with exact
version increments, stable governed identity, one current leaf, and revocation
semantics. Admitted assertion snapshots lock only review/gate identity,
evidence, rights, and payload fields; provisional queues and new successor
evidence remain writable.

```text
IMMUTABILITY_SCOPE=DATABASE_ENFORCED_APPEND_ONLY_FOR_ORDINARY_OPERATION
SUPERUSER_OR_DDL_OWNER_CAN_BYPASS=true
TAMPER_EVIDENCE_PROVIDED_BY=ROW_HASHES_AND_MANIFESTS
```

The loader validates all machine outputs before import, then imports 11
independent families, 135 route rows (131 census routes plus 4 live schema
routes), 4 schema signatures, 8 source-artifact bridges, 8 effective-record
bridges, 516 queue items, 516 provisional decisions, 3,096 purpose-specific
rights decisions, 140 admitted assertions, 508 co-assertion events, and the
analyst-time row. Repeating the import is idempotent.

The contiguous PostgreSQL 17 plan compiles migrations 000-059. The authoritative
validator returns 84 checks with zero failures. Current human-reviewed, expert,
model/deployment, normalization-target, multi-target, challenge, and gate
surfaces all consume the complete 058 chain:

```text
OLD_SELF_ATTESTING_GATE_PATH_COUNT=0
CURRENT_GATE_REQUIRES_QUALIFICATION=true
CURRENT_GATE_REQUIRES_ADMISSION=true
CURRENT_GATE_REQUIRES_ROW_DECISION_EVIDENCE=true
```

Migration 059 contains no persistent reviewer-attestation seed. Codex source
audits remain provisional, and synthetic human/expert positives exist only in
transaction-rollback suites. Human review does not modify P1/P2 evidence or any
rights decision.
