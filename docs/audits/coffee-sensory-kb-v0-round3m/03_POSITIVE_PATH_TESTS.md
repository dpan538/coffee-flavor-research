# Positive-path tests

The live adapter suite exercises three source-specific CoE schema classes
against governed bounded field captures. It does not claim full page-body
reproduction:

- explicit Top Jury field to provisional P2;
- frequency-coded field to unresolved P1 candidate;
- generic organizer sensory field to provenance unresolved.

Fixtures preserve source URL, retrieval timestamp, body or governed-snapshot
SHA-256, parser and adapter versions, field selectors, expected class, tier,
publication layer, review actor, and rights state. Public fixtures redact source
text when redistribution rights are not affirmative.

Positive-path tests also preserve producer P3 separation, de-inflated assertion
surfaces, effective-record identity, and within-record pair boundaries. The
18 restricted live-adapter tests passed, including:

- `test_honduras_top_jury_is_p2_and_layers_stay_separate`;
- `test_frequency_is_one_candidate_per_term_not_per_frequency`;
- `test_generic_field_unresolved_and_producer_p3_separate`;
- `test_repeat_levels_and_effective_record_boundaries`;
- `test_judges_do_not_create_records_and_pairs_do_not_cross_records`;
- `test_restricted_bounded_captures_and_public_export`;
- `test_generator_is_deterministic_when_capture_is_available`.

The restricted-root cases also prove that the governed manifest/root and each
capture's hash, size, URL inventory, and timestamp inventory fail closed on
tampering. With both restricted roots, all 18 tests pass. Public CI deliberately
omits those owner-controlled roots, producing 14 passes and 4 explicit skips.

The pre-hardening SQL positives included 17 named paths: versioned gate contract, empty-database
closure, NA closure, legacy-gate deprecation, actual human receipts, model
rights, source provenance, label provenance, the 500 evaluation gate,
higher-gate closure, hash-only bridge/provisional lineage, and the candidate
rights artifact enum, plus current-leaf review successor, current-leaf
validation, stale label-target exclusion, preserved/non-counting secondary
layer, and distinct secondary observation. The explicit regression marker is
`stale_label_targets_excluded`. The 500-gate and secondary-observation fixtures
are transaction-local and rolled back; the live pilot has zero secondary
review-only candidates.

Draft 059 expands this suite. Focused probe 10 ran the full Round 3M gate-schema
test successfully, but 058 is absent and the contiguous full-CI pipeline has
not run. Seventeen is therefore retained only as a historical test inventory,
not a final positive-test count. The final count will be taken from
post-hardening markers.

```text
ROUND3M_LIVE_ADAPTERS_PASS
COE_EXPLICIT_JURY_ADAPTER_PASS=true
COE_FREQUENCY_CODED_ADAPTER_PASS=true
COE_GENERIC_FIELD_ADAPTER_PASS=true
LIVE_PROVISIONAL_ASSERTION_COUNT=140
LIVE_ASSERTION_LEVEL_DEINFLATED_COUNT=139
LIVE_RECORD_LEVEL_UNIQUE_COUNT=137
LIVE_P1_P2_WITHIN_RECORD_COASSERTION_COUNT=508
```
