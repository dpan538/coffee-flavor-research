# Relationship constraint delta

Evidence decision: `PASS`.

Round 3I adds one evidence-specific `SUPPORTS` claim from the independent Dryad
Cotter origin. The claim resolves to an admitted source, immutable version-4
snapshot, verified raw file, verified 27-row aggregate, exact target membership,
review status, method/configuration, and explicit non-causal limitation.

The resulting evidence counts are 97 total claims: 48 `SUPPORTS`, 18
`CHALLENGES`, 14 `MIXED`, and 17 `INSUFFICIENT`. The preferred count of ranges
with cross-source evidence increases from three to four.

No promotion is applied:

- source-local-supported memberships remain 6;
- cross-source-supported memberships remain 4;
- ranges with source-local evidence remain 6;
- the acidity--citrus membership stays `SOURCE_LOCAL_SUPPORTED`;
- the acidity-character range stays `CANDIDATE`;
- all seven association ranges stay `CANDIDATE`; and
- canonical concept counts remain 130/92.

This distinguishes evidence breadth from lifecycle status. Correlation does not
create synonymy, causality, scale compatibility, or a universal coffee rule.
Contradictory directions remain retained in the underlying claim registry.

Database validation must confirm the new claim has complete provenance and that
unsupported promotion, stale review, single-origin cross-source status,
manifest mismatch, and frozen-data mutation are rejected. The current receipt
is:

- `RELATIONSHIP_EVIDENCE_CLAIM_COUNT=97`
- `RANGE_WITH_CROSS_SOURCE_EVIDENCE_COUNT=4`
- `RANGE_LIFECYCLE_CHANGED=false`
- `MEMBERSHIP_LIFECYCLE_CHANGED=false`
- `RELATIONSHIP_CONSTRAINT_TEST_PASS=true`

The last complete local PostgreSQL 17 suite passes the relationship-provenance
gate, the orphan-evidence rejection, the artifact-hash and current-surface
guards, and the no-promotion invariants. The two later additions to the final
35-test source are language-only countability fixtures and do not alter this
relationship-specific result; the exact candidate still requires remote
PostgreSQL 17 confirmation of the full suite.
