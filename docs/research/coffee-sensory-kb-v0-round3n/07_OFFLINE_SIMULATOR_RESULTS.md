# Offline simulator results

The committed package contains 120 deterministic policy cases: 56 context
only, 24 answer updates, eight answer-overrides-context, eight missing context,
eight conflicts, eight open-set expressions, and eight rights-blocked cases.

Observed aggregate behavior is:

```text
MAIN_OUTPUT_FILL_RATE=0.253333
SECONDARY_OUTPUT_FILL_RATE=0.050000
COMPLETE_5_PLUS_3_CASE_COUNT=6
COMPLETE_ABSTENTION_CASE_COUNT=24
ALIAS_DUPLICATE_OUTPUT_COUNT=0
NEAR_DUPLICATE_OUTPUT_COUNT=0
RIGHTS_LEAK_COUNT=0
EXPLANATION_MISSING_COUNT=0
QUESTION_AXIS_ELIGIBILITY_RATE=0.875000
ABSTENTION_RATE=0.200000
UNRESOLVED_RATE=0.750000
RIGHTS_BLOCKED_RATE=0.066667
```

Low fill is not treated as a defect. The fixture bank intentionally exercises
partial and abstained paths, and it is not an accuracy benchmark or a source of
fabricated gold labels. Source-family concentration is not estimable from the
public aggregates because output-level source-family identities are not
published; source-family count is retained as a bounded component and is not
misrepresented as evidence independence.

The generator recomputes all 120 cases under 12 deterministic variants. C0
removal changes output order in three cases without changing fill or state; C1
removal changes zero because every C1 prior is neutral. Removing direct,
effective-record, source-diversity, or structured-contrast components changes
12, 9, 6, and 12 output signatures respectively without changing aggregate
fill. Governed-normalization and governed-semantic removal each change zero in
this bounded fixture bank. Review-required exploration changes zero by
contract. Removing redundancy changes 26 cases, exposes 32 duplicate-group
placements, and raises fill; that higher fill is not interpreted as better.
Removing positive-answer weights changes 48 states and collapses output fill
to zero. Removing contradiction weights changes zero because current explicit
negative fixtures terminate through conflict handling rather than ranking.
