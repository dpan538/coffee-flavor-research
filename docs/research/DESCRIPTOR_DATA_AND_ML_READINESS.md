# Descriptor Data and ML Readiness

Last updated: 29 August 2026  
Active branch: `research/coffee-sensory-data-ml-readiness`  
Current decision: `MERGE_COMPLETE_STRICTNESS_POLICY_REVIEW_REQUIRED`

## Current position

The available row-level professional descriptor evidence has been merged into
one deterministic, public-safe current view. The current view is derived from
the governed Round 3M ledger, its effective-record, provenance, rights, review,
duplicate and pair-event relations, plus one bounded hash-only acquisition from
an official 2009 Cup of Excellence listing.

The external Descriptor-First Census remains an aggregate receipt only. Its
required nine-file machine-readable bundle and the named report PDF were not
present in the verified repository or supplied attachment directory. The
external 305/303/302 counts were not reconstructed, added to the live-pilot
counts, or converted into synthetic rows.

Round 4A remains preserved and unmerged. Its 140 assertions, 8 records and 508
pair events are an exact derived view of Round 3M, not new evidence. Seven useful
data-health semantics were regenerated in the rolling package; four redundant
or unusable reports were rejected. No product, PWA, recommendation, event,
service-worker or frontend file was imported.

## Current corpus counts

| Surface                              | Count | Meaning                                                      |
| ------------------------------------ | ----: | ------------------------------------------------------------ |
| Raw segmented assertion rows         |   158 | 140 Round 3M rows plus 18 new hash-only source atoms         |
| Assertion-level de-inflated          |   157 | One Round 3M exact within-field repeat removed               |
| Effective-record-level unique        |   155 | Two additional cross-observation repeats excluded            |
| Descriptor-bearing effective records |     9 | Eight Round 3M records plus one 2009 official-field record   |
| Strict flavor assertions             |    96 | Assertion-level de-inflated                                  |
| Broad sensory assertions             |    61 | Assertion-level de-inflated                                  |
| P2 assertions                        |    73 | Machine-audited explicit jury fields; not human reviewed     |
| Provenance-unresolved assertions     |    84 | Kept in the official-field quarantine stratum                |
| Source-native hash identities        |   130 | Restricted lexical forms counted by SHA-256 identity         |
| Reviewed normalized forms            |     0 | No human-reviewed canonical mapping exists                   |
| Unmapped assertions                  |   157 | 100% of the de-inflated current ledger                       |
| Candidate pair events                |   661 | 508 Round 3M P2 events plus 153 unresolved candidate events  |
| Unique source-atom hash pairs        |   659 | Not canonical normalized descriptor pairs                    |
| Multi-target records                 |     0 | Coassertion is not treated as reviewed multi-target labeling |
| Model-eligible assertions            |     0 | Review, rights, normalization and distribution gates fail    |

The Round 3M headline class totals remain historically preserved as 86 strict
and 54 broad across 140 segmented rows. The current strict/broad surface uses
the assertion-level de-inflated denominator, so the Round 3M contribution is 85
strict plus 54 broad before the 11 strict and 7 broad new candidates are added.

## Distribution diagnosis

The current corpus has four edition years (2008, 2009, 2017 and 2025) but only
one independent professional source family. The largest-family share is 1.0 and
source-family HHI is 1.0. All nine records have unresolved preparation service,
no direct source roast value, and no reviewed C1 mapping. A held-out year or
source-family evaluation is therefore not feasible for an eligible corpus.

No descriptor support band is populated because source-native hashes have not
been human-normalized. Singleton and tail rates are `NA_NO_NORMALIZED_LABELS`,
not zero-evidence claims. The unmapped assertion rate is 1.0.

The master corpus remains complete: common observations were not deleted,
downsampled or relabeled to improve the distribution. Distribution correction
is represented as an acquisition and review queue.

## Bounded targeted acquisition

Batch `descriptor-data-integration-batch-1-20260829` was preregistered with a
maximum of six artifacts, 45 analyst-equivalent minutes, two target cells and
the mandated stop rules. Four artifacts across three route strata were
inspected.

- An official Brazil Pulped Naturals 2009 CoE detail route yielded one new
  coffee-specific record with 18 de-inflated descriptor candidates: 11 strict
  and 7 broad. The field author is not explicit and model-use rights are
  unknown, so every assertion remains hash-only in
  `C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED`.
- A public CQI sample-grade route exposed professional grading context but no
  visible filled descriptor values.
- A 2026 Alishan government competition results release documented professional
  blind evaluation and winners but no filled coffee-specific descriptor
  passage.

The batch stopped at two consecutive zero-yield target route strata. Analyst
minutes are `NA_NOT_INSTRUMENTED_DURING_INTERACTIVE_BROWSER_PASS`; no estimate
was invented.

## Acquisition priorities

The rolling queue prioritizes:

1. a filled explicit judge or panel route from an independent non-CoE family;
2. explicit CoE Top Jury fields in additional years;
3. organizer provenance resolution for the generic and frequency-coded CoE
   fields;
4. owner-controlled normalization review of the 157 current hash-only atoms;
5. filled Brewers Cup judge feedback for filter/pour-over coverage;
6. filled roasting-production cupping evidence with direct roast and C1 context;
7. a genuinely filled CQI sample-grade surface, without rescanning the current
   empty route.

Expected yield is `UNKNOWN` unless measured history exists. The only measured
estimate retained is the prior governed Top Jury capture: 73 P2 assertions per
governed capture in the Round 3M pilot.

## Review and rights

The rolling review packet contains all 157 de-inflated current assertions and
stays under `MAX_REVIEW_PACKET_SIZE=200`. The 18 newly acquired unresolved
official-field rows are first, followed by the 73 P2 rows and the remaining
unresolved rows. Reviewer decision and reason columns are empty.

Current model-research rights are:

- affirmative: 0 assertions;
- pending: 73 assertions;
- unknown: 84 assertions;
- prohibited: 0 assertions.

All 157 assertions are source-audited candidates requiring human review. None is
human confirmed, expert adjudicated, core eligible or model eligible.

## Strictness impact

`SI-001-OFFICIAL-FIELD-ORIGIN-UNRESOLVED` is triggered because 100% of each
affected official-field route is quarantined for the same unresolved-origin
reason. The constraint affects four effective records and 84 de-inflated
assertions (55 strict and 29 broad).

The safe interim state is
`C_OFFICIAL_FIELD_PROVENANCE_UNRESOLVED`; the recommended action is
`REQUEST_ORGANIZER_PROVENANCE`. Relaxing the evidence tier is not authorized.
The data remain retained, reviewable and model-ineligible while the policy or
source-provenance decision is outstanding.

## Training gates

All five operational gates fail. Observed reviewed P1/P2 strict assertions,
reviewed normalized forms, eligible records, eligible families, eligible pair
events and multi-target records are all zero. The 84 unresolved current
challenge cases are retained but do not satisfy a reviewed challenge-case gate.

No classical model, ranking model, deep model, embedding baseline,
cross-encoder, adaptive policy or model weight was created. No training corpus
was frozen.

## Next batch decision

Continue with organizer provenance resolution and the 157-row review packet,
while seeking one bounded independent filled judge/panel route and one explicit
preparation or roast-context route. A user policy decision is required before
any official-field-origin rule is relaxed; until then the current quarantine
state remains mandatory.

Machine-readable evidence is in `db/data/current/`. The deterministic generator
and fail-closed contract test are
`db/scripts/generate-current-descriptor-data.py` and
`db/scripts/test-current-descriptor-data.py`.
