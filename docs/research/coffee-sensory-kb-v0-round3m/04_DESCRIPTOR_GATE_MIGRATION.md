# Descriptor gate migration

## Deprecated primary gates

The historical 1,000, 3,000, 7,000, 10,000, and 12,000 record gates and the
60,000-assertion threshold remain in historical Round 3K artifacts. They are
marked `DEPRECATED_RECORD_FIRST_GATE` for current readiness and cannot authorize
training.

Record counts remain denominators and anti-inflation checks. The active
numerator is reviewed P1/P2 strict descriptor evidence with provenance, rights,
diversity, per-label support, record boundaries, and held-out evaluation.

## Versioned gate contract

Round 3M implements executable contracts for:

- 500-assertion deterministic evaluation;
- 2,000-assertion experimental normalization;
- 10,000-assertion research normalization;
- 15,000-assertion association learning;
- 5,000-assertion experimental ranking;
- 20,000-assertion research ranking;
- 40,000-assertion deployment-candidate ranking.

Every metric exposes its gate version, universe, observed and required values,
pass state, NA state, rights blocker, data blocker, review blocker, and note.
An empty database fails. `NA` is never a pass. Pending or unknown rights prevent
model eligibility.

Forward migrations `055_round3m_descriptor_provenance_review_rights.sql`,
`056_round3m_descriptor_gate_contract.sql`, and
`057_round3m_release_contract_hardening.sql` add the ledger/governance model,
the seven-gate contract, and release-audit hardening without rewriting applied
history. The last generated version-one artifact has 56 criteria: 0 pass and 17
explicitly not applicable because a denominator does not exist. Every NA
criterion still has `pass=false`.

Draft `059_round3m_normalization_challenge_contract.sql` extends the contract,
but the migration plan currently fails because 058 is absent. Probe 10 applied
000-057 plus draft 059 and passed 68 of 68 global validations (49 pre-v059 plus
the exact 19-check v059 delta); this is focused evidence only. Final gate counts and
artifact parity remain unclaimed until the contiguous migration sequence,
regeneration, and full CI are complete.

The generated `DESCRIPTOR_GATE_STATUS.tsv` is required to match the
authoritative SQL criterion contract exactly, including gate/metric identifiers,
required value/type, universe, pass/NA states, blockers, and note. Naming or
universe drift fails the artifact contract even if headline counts still match.
Per-label and multi-target metrics count only assertions whose current review
receipt is the leaf of its supersession chain; stale predecessors cannot inflate
support.

The pre-hardening SQL suite exercised a transaction-local 500-assertion fixture
to prove that the evaluation gate can work when actual human receipts,
provenance, labels, and rights exist while still exposing
`training_authorization_pass=false`. Those fixture rows were rolled back and
are not corpus evidence. Current positive, negative, policy, and invariant
totals await final marker-derived reconciliation.

No gate authorizes training during Round 3M.
